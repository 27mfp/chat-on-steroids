#!/usr/bin/env python3
"""Local AdaL controller. Python stdlib only; no production app dependencies."""
import argparse
import copy
import fcntl
import json
import os
import re
from pathlib import Path, PurePosixPath
import secrets
import shutil
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
LEAD_MODEL = 'openai-gpt-6-sol'
WORKER_MODEL = 'zai-glm-5.3-flash'
BRANCH = 'feat/gpui-frontend-port'
PR_URL = 'https://github.com/27mfp/chat-on-steroids/pull/4'
DEFAULT_OBJECTIVE = ('Autonomously execute the next eligible tasks in rust-port/docs/task-cards.md, '
    'starting with R00 if its actual evidence is not recorded, on PR #4 and feat/gpui-frontend-port. '
    'Dispatch all implementation, verification, documentation and worklogs to GLM workers; '
    'the GPT-6 Sol lead only plans, dispatches and reviews. Keep docs current after each task. '
    'Publish reviewed independently verified progress to that PR branch. Continue automatically '
    'through all eligible work, preserving M0–M4 gates; exhaust independent work before reporting '
    'external/native/platform gates blocked. The user only starts, stops and checks status.')
MAX_OUTPUT = 8 * 1024 * 1024


def git(cwd, *args, timeout=60):
    return subprocess.check_output(['git', '-C', str(cwd), *args], stderr=subprocess.STDOUT,
                                   timeout=timeout).decode('utf-8', 'replace').strip()


def valid_file(name):
    if not isinstance(name, str) or not name or len(name) > 500:
        return False
    p = PurePosixPath(name)
    return (not p.is_absolute() and '..' not in p.parts
            and not name.startswith('rust-port/orchestrator/')
            and not any(c in name for c in ('*', '?', '[', '\\', '\x00', '\n'))
            and not any(part in p.parts for part in ('target', '.git', '.adal', 'node_modules'))
            and not any(part.startswith('.env') for part in p.parts)
            and not name.endswith('/'))


def snapshot(source, destination):
    """Copy versioned sources plus nonignored rust-port sources, including dirty bytes.

    No commit/index mutation in source. A local private repository owns run commits.
    """
    destination.mkdir(parents=True)
    paths = set(subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z']).split(b'\0'))
    paths.update(subprocess.check_output(['git', '-C', str(source), 'ls-files', '--others',
                                        '--exclude-standard', '-z', '--', 'rust-port']).split(b'\0'))
    copied = 0
    for raw in sorted(paths):
        if not raw:
            continue
        name = os.fsdecode(raw)
        relative = PurePosixPath(name)
        if (relative.is_absolute() or '..' in relative.parts or
                any(part in relative.parts for part in ('.git', '.adal', 'target', 'node_modules', '__pycache__'))):
            continue
        src, dst = source / name, destination / name
        if not src.exists() and not src.is_symlink():
            continue  # preserve local deletions
        if src.is_symlink():
            raise ValueError(f'Snapshot refuses symlink: {name}; review its target first')
        if not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    git(destination, 'init', '-q')
    git(destination, 'config', 'user.name', 'Local AdaL controller')
    git(destination, 'config', 'user.email', 'local-controller@localhost')
    # Hooks/signing are never borrowed from the shared repository.
    git(destination, 'config', 'core.hooksPath', '/dev/null')
    git(destination, 'config', 'commit.gpgsign', 'false')
    git(destination, 'add', '--all')
    git(destination, 'commit', '-qm', 'Isolated source snapshot')
    git(destination, 'branch', '-m', BRANCH)
    return git(destination, 'rev-parse', 'HEAD'), copied


class Controller:
    def __init__(self, state_dir, adal, timeout=1800, max_turns=30):
        self.root = Path(state_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.instance_lock = (self.root / 'controller.lock').open('a')
        try:
            fcntl.flock(self.instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.instance_lock.close()
            raise ValueError('A controller already owns this state directory')
        self.adal, self.timeout, self.max_turns = adal, timeout, max_turns
        self.lock = threading.RLock()
        self.processes = {}
        self.jobs = set()
        self.closed = False
        self.usage_process = None
        self.usage = {'status': 'loading'}
        self.url = ''
        self.token = secrets.token_urlsafe(32)
        self.file = self.root / 'state.json'
        self.state = json.loads(self.file.read_text()) if self.file.exists() else {
            'run': None, 'workers': [], 'events': [], 'inbox': [], 'lead': None}
        if self.state['run'] and self.state['run']['status'] in ('running', 'paused'):
            self.state['run']['status'] = 'paused'
            for worker in self.state['workers']:
                if worker['status'] == 'running':
                    worker['status'] = 'interrupted'
                    self.state['inbox'].append({'kind': 'worker', 'worker_id': worker['id'],
                                               'text': 'Controller restarted; worker interrupted. Do not replay silently.'})
            if self.state['lead'] and self.state['lead']['status'] == 'running':
                self.state['lead']['status'] = 'interrupted'
                self.state['inbox'].append({'kind': 'notice', 'text': 'Lead interrupted by controller restart. Inspect work before continuing.'})
        self.save()

    def save(self):
        temp = self.file.with_suffix('.tmp')
        with temp.open('w') as stream:
            json.dump(self.state, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.file)

    def event(self, text):
        self.state['events'].append({'time': time.time(), 'text': text})
        self.state['events'] = self.state['events'][-300:]

    def view(self):
        with self.lock:
            result = copy.deepcopy(self.state)
            result['usage'] = copy.deepcopy(self.usage)
            result['pr_url'] = PR_URL
            result['branch'] = BRANCH
            result['active_jobs'] = len(self.jobs)
            return result

    def validate_source(self):
        if git(REPO, 'branch', '--show-current') != BRANCH:
            raise ValueError(f'Controller must run from {BRANCH} worktree for PR #4')
        remote = git(REPO, 'remote', 'get-url', 'fork').removesuffix('.git').rstrip('/')
        if remote not in ('https://github.com/27mfp/chat-on-steroids',
                          'git@github.com:27mfp/chat-on-steroids'):
            raise ValueError('fork remote must be 27mfp/chat-on-steroids; publication refused')

    def start_usage(self):
        def collect():
            try:
                install = Path(self.adal).resolve().parent
                bun = install / 'runtime/bun'
                work = self.root / 'usage-workspace'
                work.mkdir(exist_ok=True)
                process = subprocess.Popen([str(bun), str(HERE / 'usage.js'), str(install), str(work)],
                                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                           start_new_session=True)
                with self.lock:
                    self.usage_process = process
                    if self.closed:
                        self.kill(process)
                for raw in iter(process.stdout.readline, b''):
                    if len(raw) > 16000:
                        continue
                    try:
                        data = json.loads(raw)
                        if data.get('status') not in ('available', 'unavailable'):
                            continue
                        with self.lock:
                            self.usage = {k: data[k] for k in ('status', 'updated_at', 'plan',
                                'wallet_balance', 'weekly', 'error') if k in data}
                    except (ValueError, AttributeError):
                        continue
                process.stdout.close()
                process.wait()
                with self.lock:
                    if not self.closed:
                        self.usage = {'status': 'unavailable', 'error': 'AdaL usage connection ended'}
            except Exception:
                with self.lock:
                    self.usage = {'status': 'unavailable', 'error': 'Installed AdaL usage adapter unavailable'}
        threading.Thread(target=collect, daemon=True).start()

    def preflight(self):
        if any(os.environ.get(name) for name in ('OPENAI_API_KEY', 'ZAI_API_KEY')):
            raise ValueError('Provider API key environment detected. Launch without OPENAI_API_KEY/ZAI_API_KEY to use AdaL credits.')
        if not Path(self.adal).is_file():
            raise ValueError('AdaL executable not found')
        self.validate_source()
        # Read only routing flags, never return settings or keys to the UI.
        settings = Path.home() / '.adal/settings.json'
        if settings.exists():
            data = json.loads(settings.read_text())
            def walk(value):
                if isinstance(value, dict):
                    for key, val in value.items():
                        if 'byoak' in key.lower() and val:
                            raise ValueError('BYOAK configuration detected. Disable OpenAI/Z.ai BYOAK in AdaL before using subscription credits.')
                        if key.lower() in ('api_key', 'apikey', 'api_keys', 'provider_keys') and val:
                            raise ValueError('Provider API key configuration detected; inspect AdaL billing routing before starting.')
                        walk(val)
                elif isinstance(value, list):
                    for item in value:
                        walk(item)
            walk(data)
        return {'adal': self.adal, 'lead_model': LEAD_MODEL, 'worker_model': WORKER_MODEL,
                'billing': 'AdaL credits; no ChatGPT OAuth model slugs or BYOAK configured by this controller',
                'provider_verified': False}

    def start(self, objective=DEFAULT_OBJECTIVE):
        with self.lock:
            if not isinstance(objective, str) or not objective.strip() or len(objective) > 20000:
                raise ValueError('Enter an objective of 1–20,000 characters')
            if self.state['run'] and self.state['run']['status'] in ('running', 'paused'):
                raise ValueError('Finish/stop the current run before starting another')
            if self.jobs or self.processes:
                raise ValueError('Previous jobs are still stopping')
            self.preflight()
            if git(REPO, 'status', '--porcelain'):
                raise ValueError('PR worktree has unrelated uncommitted changes; refusing to overwrite them')
            source_head = git(REPO, 'rev-parse', 'HEAD')
            remote_head = git(REPO, 'ls-remote', 'fork', f'refs/heads/{BRANCH}').split()[0]
            run_id = secrets.token_hex(6)
            directory = self.root / 'runs' / run_id
            workspace = directory / 'lead'
            baseline, count = snapshot(REPO, workspace)
            (workspace / '.adal').mkdir()
            shutil.copy2(HERE / 'tools.py', workspace / '.adal/tools.py')
            # Ignore generated custom tools in the isolated snapshot only.
            with (workspace / '.git/info/exclude').open('a') as stream:
                stream.write('\n.adal/\n')
            run = {'id': run_id, 'status': 'running', 'objective': objective,
                   'workspace': str(workspace), 'baseline': baseline, 'created_at': time.time(),
                   'lead_model': LEAD_MODEL, 'worker_model': WORKER_MODEL, 'turns': 0,
                   'summary': '', 'source_files': count, 'branch': BRANCH, 'pr_url': PR_URL,
                   'source_head': source_head, 'remote_head': remote_head,
                   'published_snapshot': baseline, 'pending_push': False, 'turn_limit': self.max_turns}
            self.state = {'run': run, 'workers': [], 'events': [], 'inbox': [
                {'kind': 'objective', 'text': objective}], 'lead': None}
            self.event(f'Created isolated snapshot ({count} files); shared checkout unchanged')
            self.save()
            self.schedule()
            return self.view()

    def schedule(self):
        """Single lead owns inbox batches. Completion during a turn waits for next turn."""
        with self.lock:
            run = self.state['run']
            if self.closed or not run or run['status'] != 'running' or not self.state['inbox']:
                return
            if self.state['lead'] and self.state['lead']['status'] == 'running':
                return
            if run['turns'] >= run.get('turn_limit', self.max_turns):
                run['status'] = 'paused'
                self.event('Lead turn limit reached. Review before resuming with a larger limit.')
                self.save()
                return
            batch = self.state['inbox']
            self.state['inbox'] = []
            run['turns'] += 1
            previous = self.state['lead'] or {}
            lead = {'id': f'lead-{run["turns"]}', 'status': 'running', 'batch': batch,
                    'session_id': previous.get('session_id'), 'started_at': time.time(),
                    'log': str(self.root / 'runs' / run['id'] / f'lead-{run["turns"]}.ndjson')}
            self.state['lead'] = lead
            self.event(f'Starting lead turn {run["turns"]} with {len(batch)} inbox item(s)')
            self.save()
            self.launch(self.run_lead, run['id'], lead)

    def launch(self, target, run_id, entry):
        self.jobs.add(entry['id'])
        def job():
            try:
                target(run_id, entry)
            finally:
                with self.lock:
                    self.jobs.discard(entry['id'])
                self.schedule()
        threading.Thread(target=job, daemon=True).start()

    def add_worker(self, title, task, allowed_files, checks, task_id='R00', role='implementation', verifies_worker=''):
        with self.lock:
            run = self.state['run']
            if not run or run['status'] != 'running':
                raise ValueError('Run is not running')
            if len(self.state['workers']) >= 60:
                raise ValueError('Run worker limit reached (60); review the scope before starting another run')
            if sum(w['id'] in self.jobs for w in self.state['workers']) >= 2:
                raise ValueError('Two workers are already running')
            if not isinstance(allowed_files, list) or len(allowed_files) > 50 or not all(
                    isinstance(p, str) and valid_file(p) for p in allowed_files):
                raise ValueError('Allowed files must be exact source paths outside orchestration, secrets and build outputs')
            if not isinstance(title, str) or not isinstance(task, str) or not title.strip() or len(title) > 200 or not task.strip() or len(task) > 30000:
                raise ValueError('A title and bounded task are required')
            if not isinstance(checks, list) or len(checks) > 30 or not all(isinstance(c, str) and len(c) <= 5000 for c in checks):
                raise ValueError('Checks must be a list of commands')
            if not re.fullmatch(r'R\d{2}', task_id) or role not in ('implementation', 'verification', 'audit'):
                raise ValueError('Use an exact task-card ID and implementation/verification/audit role')
            cards = (Path(run['workspace']) / 'rust-port/docs/task-cards.md').read_text()
            if f'## {task_id}:' not in cards:
                raise ValueError('Task card does not exist')
            sections = ('Context:', 'Steps:', 'Acceptance:', 'Negative cases:', 'Documentation:', 'Handoff:')
            if len(task) < 400 or any(section.lower() not in task.lower() for section in sections):
                raise ValueError('A detailed brief with Context, Steps, Acceptance, Negative cases, Documentation and Handoff sections is required')
            if role in ('verification', 'audit') and any(not p.startswith('rust-port/docs/') for p in allowed_files):
                raise ValueError('Verification/audit workers may write documentation only')
            if role == 'verification':
                target = self.find_worker(verifies_worker)
                if target['role'] != 'implementation' or not target['integrated'] or not checks:
                    raise ValueError('Verification requires an integrated implementation and explicit independent checks')
            worker_id = 'worker-' + secrets.token_hex(4)
            date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            report_doc = f'rust-port/docs/tasks/{task_id}-{worker_id}.md'
            worklog = f'rust-port/docs/worklog-{date}-{task_id}-{worker_id}.md'
            required_docs = [report_doc, worklog]
            if role != 'audit':
                required_docs.append('rust-port/docs/task-cards.md')
            allowed_files = sorted(set(allowed_files + required_docs))
            occupied = {p for w in self.state['workers'] if (w['id'] in self.jobs or w['status'] in ('running', 'completed'))
                        and not w.get('integrated') and not w.get('rejected') for p in w['allowed_files']}
            if occupied.intersection(allowed_files):
                raise ValueError('Files overlap an active or unreviewed worker')
            workspace = Path(run['workspace'])
            if git(workspace, 'status', '--porcelain'):
                raise ValueError('Lead tree has uncommitted changes; review and commit them in the isolated tree before delegation')
            worker_dir = self.root / 'runs' / run['id'] / worker_id
            base = git(workspace, 'rev-parse', 'HEAD')
            if role == 'verification':
                git(workspace, 'merge-base', '--is-ancestor', target['integration_commit'], base)
            git(workspace, 'worktree', 'add', '-b', worker_id, str(worker_dir), base)
            worker = {'id': worker_id, 'title': title, 'task': task, 'checks': checks,
                      'allowed_files': sorted(set(allowed_files)), 'status': 'running',
                      'workspace': str(worker_dir), 'base': base, 'started_at': time.time(),
                      'log': str(worker_dir.parent / f'{worker_id}.ndjson'),
                      'integrated': False, 'rejected': False, 'report': '', 'task_id': task_id,
                      'role': role, 'verifies_worker': verifies_worker, 'verified': False,
                      'required_docs': required_docs}
            self.state['workers'].append(worker)
            self.event(f'Started {worker_id}: {title}')
            self.save()
            self.launch(self.run_worker, run['id'], worker)
            return copy.deepcopy(worker)

    def execute(self, identity, workspace, model, prompt_file, prompt, log_path, session=None, lead=False):
        args = [self.adal, '-q', prompt, '-m', model, '-o', 'stream-json',
                '--permission-mode', 'yolo', '--prompt-file', str(prompt_file),
                '--enabled-default-tools', 'Read,Search' if lead else 'Read,Search,Edit,Bash']
        if session:
            args += ['-r', session]
        env = os.environ.copy()
        # Prevent workers inheriting controller tool credentials.
        env.pop('PORT_ORCHESTRATOR_URL', None)
        env.pop('PORT_ORCHESTRATOR_TOKEN', None)
        if lead:
            env['PORT_ORCHESTRATOR_URL'] = self.url
            env['PORT_ORCHESTRATOR_TOKEN'] = self.token
        result = {'answer': '', 'session_id': session, 'complete': False, 'exit_code': None}
        log_path = Path(log_path)
        with self.lock:
            run = self.state['run']
            entry = self.state['lead'] if lead else self.find_worker(identity) if identity.startswith('worker-') else None
            if entry and entry['status'] != 'running':
                return {**result, 'error': 'Job cancelled before process launch'}
            if self.closed or not run or run['status'] not in ('running', 'paused'):
                return {**result, 'error': 'Run stopped before process launch'}
            process = subprocess.Popen(args, cwd=workspace, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            self.processes[identity] = process
        timed_out = threading.Event()
        def expire():
            timed_out.set()
            self.kill(process)
        timer = threading.Timer(self.timeout, expire)
        timer.start()
        total = 0
        overflow = False
        try:
            with log_path.open('wb') as log:
                while True:
                    raw = process.stdout.readline(MAX_OUTPUT + 1)
                    if not raw:
                        break
                    total += len(raw)
                    if total > MAX_OUTPUT:
                        overflow = True
                        self.kill(process)
                        break
                    log.write(raw)
                    log.flush()
                    try:
                        event = json.loads(raw)
                    except (ValueError, UnicodeDecodeError):
                        continue
                    if not isinstance(event, dict):
                        continue
                    kind = event.get('type')
                    if kind == 'answer':
                        result['answer'] = event.get('content', '')
                    elif kind == 'complete':
                        result['complete'] = True
                        result['exit_code'] = event.get('exit_code')
                        result['session_id'] = event.get('session_id') or session
                    elif kind == 'error' or kind == 'permission_denied':
                        result['error'] = event.get('message') or event.get('reason') or str(event)
            result['process_exit'] = process.wait(timeout=10)
        finally:
            timer.cancel()
            process.stdout.close()
            if process.poll() is None:
                self.kill(process)
            with self.lock:
                self.processes.pop(identity, None)
        if not result['complete'] and not result.get('error'):
            result['error'] = 'CLI ended without a completion event; inspect log before retrying'
        if result.get('process_exit') not in (0, None) and not result.get('error'):
            result['error'] = f'CLI process exited with code {result["process_exit"]}'
        if timed_out.is_set():
            result['error'] = 'Process timed out; no automatic retry'
        if overflow:
            result['error'] = 'Output limit exceeded; process stopped'
        result['success'] = (result.get('process_exit') == 0 and result['complete']
                             and result['exit_code'] == 0 and not result.get('error'))
        return result

    @staticmethod
    def kill(process):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            def force():
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            killer = threading.Timer(2, force)
            killer.daemon = True
            killer.start()

    def run_worker(self, run_id, worker):
        try:
            brief = json.dumps({k: worker[k] for k in ('task_id', 'title', 'task', 'role', 'verifies_worker',
                'allowed_files', 'checks', 'required_docs')}, indent=2)
            result = self.execute(worker['id'], worker['workspace'], WORKER_MODEL,
                                  HERE / 'prompts/worker.md', brief, worker['log'])
            if worker['role'] == 'verification' and result.get('success') and 'VERIFICATION: PASS' not in result.get('answer', ''):
                result['success'] = False
                result['error'] = 'Verification must explicitly report VERIFICATION: PASS after successful independent checks'
            workspace = Path(worker['workspace'])
            changes = subprocess.check_output(['git', '-C', str(workspace), 'diff', '--name-only',
                                                '-z', worker['base']]).split(b'\0')
            changes += subprocess.check_output(['git', '-C', str(workspace), 'ls-files', '--others',
                                                '--exclude-standard', '-z']).split(b'\0')
            names = {os.fsdecode(p) for p in changes if p}
            forbidden = names.difference(worker['allowed_files'])
            missing_docs = set(worker['required_docs']).difference(names)
            if result.get('success') and missing_docs:
                result['success'] = False
                result['error'] = 'Required documentation/worklog not updated: ' + ', '.join(sorted(missing_docs))
            if any((workspace / p).is_symlink() for p in names):
                result['success'] = False
                result['error'] = 'Worker added a symlink; patch rejected'
            if forbidden:
                result['success'] = False
                result['error'] = 'Out-of-scope changes: ' + ', '.join(sorted(forbidden))
            patch_path = workspace.parent / f'{worker["id"]}.patch'
            if not forbidden and not any((workspace / p).is_symlink() for p in names):
                if names:
                    git(workspace, 'add', '--', *sorted(names))
                patch = subprocess.check_output(['git', '-C', str(workspace), 'diff', '--cached',
                                                 '--binary', worker['base']])
                if len(patch) > MAX_OUTPUT:
                    raise ValueError('Patch exceeds 8 MiB review limit')
                patch_path.write_bytes(patch)
            with self.lock:
                if self.state['run']['id'] != run_id:
                    return
                # Never convert an explicit cancellation into success.
                cancelled = worker['status'] == 'cancelled'
                worker.update({'status': 'cancelled' if cancelled else 'completed' if result.get('success') else 'failed',
                               'result': result, 'report': result.get('answer', ''),
                               'patch': str(patch_path) if patch_path.exists() else None,
                               'finished_at': time.time()})
                self.state['inbox'].append({'kind': 'worker', 'worker_id': worker['id'],
                                           'text': f'{worker["title"]}: {worker["status"]}',
                                           'report': worker['report'], 'error': result.get('error')})
                self.event(f'{worker["id"]} {worker["status"]}; result queued for lead')
                self.save()
        except Exception as error:
            with self.lock:
                if self.state['run']['id'] != run_id:
                    return
                worker.update(status='cancelled' if worker['status'] == 'cancelled' else 'failed', report=str(error), finished_at=time.time())
                self.state['inbox'].append({'kind': 'worker', 'worker_id': worker['id'], 'text': str(error)})
                self.event(f'{worker["id"]} failed; lead notified')
                self.save()
        self.schedule()

    def run_lead(self, run_id, lead):
        try:
            run = self.state['run']
            prompt = ('Continue the complete objective below. Inbox messages are new evidence, not a scope replacement.\n'
                      + run['objective'] + '\n\nCONTROLLER INBOX:\n' + json.dumps(lead['batch'], indent=2)
                      + '\nUse orchestration_status to read all tasks. Continue ready work or finish explicitly.')
            result = self.execute(lead['id'], run['workspace'], LEAD_MODEL,
                                  HERE / 'prompts/lead.md', prompt, lead['log'],
                                  session=lead.get('session_id'), lead=True)
            with self.lock:
                if self.state['run']['id'] != run_id:
                    return
                lead.update(status='completed' if result.get('success') else 'failed', result=result,
                            session_id=result.get('session_id'), finished_at=time.time())
                self.event(f'{lead["id"]} {lead["status"]}')
                if not result.get('success') and run['status'] == 'running':
                    run['status'] = 'paused'
                    self.state['inbox'] = lead['batch'] + self.state['inbox']
                    self.event('Lead failed; paused with its inbox retained. Inspect logs before resuming.')
                elif run['status'] == 'running' and not self.state['inbox'] and not any(
                        w['status'] == 'running' for w in self.state['workers']):
                    run['status'] = 'paused'
                    self.event('Lead ended without finishing or delegating; paused for review instead of a paid polling loop')
                self.save()
        except Exception as error:
            with self.lock:
                if self.state['run']['id'] != run_id:
                    return
                lead.update(status='failed', result={'error': str(error)})
                if self.state['run']['status'] == 'running':
                    self.state['run']['status'] = 'paused'
                self.state['inbox'] = lead['batch'] + self.state['inbox']
                self.event(f'Lead failed: {error}')
                self.save()
        self.schedule()

    def find_worker(self, worker_id):
        for worker in self.state['workers']:
            if worker['id'] == worker_id:
                return worker
        raise ValueError('Unknown worker')

    def review(self, worker_id):
        with self.lock:
            worker = self.find_worker(worker_id)
            patch = Path(worker['patch']).read_text(errors='replace') if worker.get('patch') else ''
            worker['reviewed'] = True
            self.save()
            return {'worker': copy.deepcopy(worker), 'patch': patch}

    def integrate(self, worker_id):
        with self.lock:
            worker = self.find_worker(worker_id)
            if worker['status'] != 'completed' or worker.get('rejected') or not worker.get('reviewed'):
                raise ValueError('Read the completed worker report and patch before integrating')
            if worker['integrated']:
                return {'already_integrated': True}
            workspace = Path(self.state['run']['workspace'])
            if git(workspace, 'status', '--porcelain'):
                raise ValueError('Lead tree has uncommitted changes; review them before integration')
            patch = Path(worker['patch'])
            if patch.stat().st_size:
                git(workspace, 'apply', '--check', '--index', str(patch))
                git(workspace, 'apply', '--index', str(patch))
                git(workspace, 'commit', '-qm', f'Reviewed {worker_id}: {worker["title"]}')
            worker['integrated'] = True
            worker['integration_commit'] = git(workspace, 'rev-parse', 'HEAD')
            if worker['role'] == 'verification':
                for candidate in self.state['workers']:
                    if candidate['role'] == 'implementation' and candidate['integrated'] and candidate['task_id'] == worker['task_id']:
                        git(workspace, 'merge-base', '--is-ancestor', candidate['integration_commit'], worker['base'])
                        candidate['verified'] = True
                        candidate['verification_worker'] = worker_id
            self.event(f'Integrated {worker_id} into isolated lead tree')
            self.save()
            return {'commit': worker['integration_commit']}

    def publish(self, summary):
        """Deterministic Git publication, with source and remote epoch checks."""
        with self.lock:
            run = self.state['run']
            if not run or not isinstance(summary, str) or not summary.strip():
                raise ValueError('Publication needs a run and evidence summary')
            self.validate_source()
            if any(w['integrated'] and w['role'] == 'implementation' and not w['verified']
                   for w in self.state['workers']):
                raise ValueError('Every integrated implementation needs independent verification before PR publication')
            workspace = Path(run['workspace'])
            if git(workspace, 'status', '--porcelain'):
                raise ValueError('Dispatcher workspace has unexpected direct edits; delegate a correction')
            if git(REPO, 'status', '--porcelain') or git(REPO, 'rev-parse', 'HEAD') != run['source_head']:
                raise ValueError('PR worktree changed outside this run; publication refused without overwriting it')
            remote_head = git(REPO, 'ls-remote', 'fork', f'refs/heads/{BRANCH}').split()[0]
            if remote_head != run['remote_head']:
                if run.get('pending_push') and remote_head == run['source_head']:
                    run.update(remote_head=remote_head, pending_push=False)
                    self.save()
                else:
                    raise ValueError('PR branch advanced remotely; publication refused without force-pushing')
            current = git(workspace, 'rev-parse', 'HEAD')
            if current != run['published_snapshot']:
                verifier = workspace / 'rust-port/scripts/verify-docs.py'
                check = subprocess.run(['python3', str(verifier)], cwd=workspace,
                                       capture_output=True, text=True, timeout=60)
                if check.returncode:
                    raise ValueError('Documentation verification failed: ' + (check.stderr or check.stdout)[-4000:])
                diff = subprocess.check_output(['git', '-C', str(workspace), 'diff', '--binary',
                                                run['published_snapshot'], current])
                patch = self.root / 'runs' / run['id'] / 'publication.patch'
                patch.write_bytes(diff)
                if diff:
                    git(REPO, 'apply', '--check', '--index', str(patch))
                    git(REPO, 'apply', '--index', str(patch))
                    try:
                        git(REPO, '-c', 'commit.gpgsign=false', 'commit', '-m',
                            'rust-port: ' + summary.strip().splitlines()[0][:160])
                    except subprocess.SubprocessError:
                        run['status'] = 'paused'
                        self.event('Git commit failed; source retains only the controller-staged patch for inspection')
                        self.save()
                        raise
                    run['source_head'] = git(REPO, 'rev-parse', 'HEAD')
                    run['pending_push'] = True
                run['published_snapshot'] = current
                self.save()
            if run.get('pending_push'):
                try:
                    git(REPO, 'push', 'fork', f'HEAD:refs/heads/{BRANCH}', timeout=120)
                except subprocess.SubprocessError:
                    actual = git(REPO, 'ls-remote', 'fork', f'refs/heads/{BRANCH}').split()[0]
                    if actual != run['source_head']:
                        run['status'] = 'paused'
                        self.event('Push failed; local reviewed commit retained, no force push or duplicate commit')
                        self.save()
                        raise ValueError('PR push failed; reviewed local commit retained')
                run.update(remote_head=run['source_head'], pending_push=False)
                self.event(f'Published reviewed progress to PR #4: {run["source_head"][:12]}')
                self.save()
            return {'pr_url': PR_URL, 'branch': BRANCH, 'commit': run['source_head']}

    def finish(self, summary, outcome):
        with self.lock:
            if outcome not in ('completed', 'blocked') or not isinstance(summary, str) or not summary.strip():
                raise ValueError('Supply a summary and completed/blocked outcome')
            if any(w['status'] == 'running' or (w['status'] == 'completed' and not w['integrated']
                   and not w['rejected']) for w in self.state['workers']):
                raise ValueError('Workers must finish and successful patches must be integrated or rejected first')
            if self.state['inbox']:
                raise ValueError('Unprocessed inbox messages remain; end this turn so they can be delivered')
            self.publish(summary)
            self.state['run'].update(status=outcome, summary=summary)
            self.event(f'Run {outcome}: {summary}')
            self.save()
            return {'status': outcome}

    def control(self, action, text=''):
        with self.lock:
            run = self.state['run']
            if not run:
                raise ValueError('No run exists')
            if action == 'pause':
                if run['status'] != 'running':
                    raise ValueError('Only a running run can be paused')
                run['status'] = 'paused'
                self.event('Paused: current turns finish; no new turns or workers start')
            elif action == 'resume':
                if run['status'] not in ('paused', 'blocked', 'stopped'):
                    raise ValueError('Only a paused or blocked run can resume')
                if run['turns'] >= run.get('turn_limit', self.max_turns):
                    run['turn_limit'] = run['turns'] + self.max_turns
                    self.event('Start renewed the lead turn allowance')
                self.preflight()
                run['status'] = 'running'
                if not self.state['inbox']:
                    self.state['inbox'].append({'kind': 'user', 'text': text or 'Continue the scoped objective; inspect prior work before retrying.'})
                self.event('Resumed')
            elif action == 'steer':
                if not text.strip() or len(text) > 20000 or run['status'] not in ('running', 'paused', 'blocked'):
                    raise ValueError('A bounded instruction and active run are required')
                self.state['inbox'].append({'kind': 'user', 'text': text})
                self.event('User instruction queued for next lead turn')
            elif action == 'stop':
                run['status'] = 'stopped'
                for worker in self.state['workers']:
                    if worker['status'] == 'running':
                        worker['status'] = 'cancelled'
                for process in list(self.processes.values()):
                    self.kill(process)
                self.event('Stopped all owned process groups; no automatic retry')
            else:
                raise ValueError('Unknown action')
            self.save()
        self.schedule()
        return self.view()

    def cancel_worker(self, worker_id):
        with self.lock:
            worker = self.find_worker(worker_id)
            if worker['status'] != 'running':
                raise ValueError('Worker is not running')
            worker['status'] = 'cancelled'
            process = self.processes.get(worker_id)
            if process:
                self.kill(process)
            self.event(f'Cancellation requested for {worker_id}; its terminal report will notify the lead')
            self.save()
            return self.view()

    def reject(self, worker_id):
        with self.lock:
            worker = self.find_worker(worker_id)
            if worker['status'] == 'running' or worker['integrated']:
                raise ValueError('Cannot reject running or integrated work')
            worker['rejected'] = True
            self.state['inbox'].append({'kind': 'user', 'text': f'Worker {worker_id} rejected; revise assignment if still needed.'})
            self.event(f'Rejected {worker_id}')
            self.save()
        self.schedule()
        return self.view()

    def export(self):
        with self.lock:
            run = self.state['run']
            if not run:
                raise ValueError('No run')
            if self.jobs or self.processes:
                raise ValueError('Wait for jobs to finish (or stop them) before exporting')
            workspace = run['workspace']
            # Includes committed integration and lead modifications; never custom tools.
            patch = subprocess.check_output(['git', '-C', workspace, 'diff', '--binary', run['baseline'], '--', 'rust-port',
                                             ':(exclude)rust-port/orchestrator'])
            untracked = git(workspace, 'ls-files', '--others', '--exclude-standard', '--', 'rust-port')
            if untracked:
                raise ValueError('Untracked lead files remain. Ask the lead to review and commit them in the isolated tree before exporting.')
            return patch

    def shutdown(self):
        with self.lock:
            self.closed = True
            if self.state['run'] and self.state['run']['status'] == 'running':
                self.state['run']['status'] = 'paused'
            for process in list(self.processes.values()):
                self.kill(process)
            if self.usage_process:
                self.kill(self.usage_process)
            self.save()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, data, content_type='application/json'):
        body = json.dumps(data).encode() if content_type == 'application/json' else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        # Reject DNS rebinding and cross-origin writes; no CORS support.
        if self.headers.get('Host') != urllib.parse.urlsplit(self.server.controller.url).netloc:
            return False
        origin = self.headers.get('Origin')
        if origin and origin != self.server.controller.url:
            return False
        supplied = self.headers.get('Authorization', '')
        if supplied.startswith('Bearer '):
            return secrets.compare_digest(supplied[7:], self.server.controller.token)
        cookies = self.headers.get('Cookie', '').split(';')
        return any(secrets.compare_digest(c.strip(), 'port_token=' + self.server.controller.token) for c in cookies)

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path)
        if path.path == '/':
            token = urllib.parse.parse_qs(path.query).get('token', [''])[0]
            if token and secrets.compare_digest(token, self.server.controller.token) and self.headers.get('Host') == urllib.parse.urlsplit(self.server.controller.url).netloc:
                self.send_response(303)
                self.send_header('Set-Cookie', f'port_token={token}; HttpOnly; SameSite=Strict; Path=/')
                self.send_header('Location', '/')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Referrer-Policy', 'no-referrer')
                self.end_headers()
                return
        if not self.authorized():
            self.send(403, {'error': 'Open the dashboard URL printed by the controller'})
            return
        controller = self.server.controller
        try:
            if path.path in ('/', '/app.js', '/style.css'):
                name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[path.path]
                content_type = {'/': 'text/html; charset=utf-8', '/app.js': 'text/javascript; charset=utf-8', '/style.css': 'text/css; charset=utf-8'}[path.path]
                self.send(200, (HERE / name).read_bytes(), content_type)
            elif path.path == '/api/state':
                self.send(200, controller.view())
            elif path.path == '/api/preflight':
                self.send(200, controller.preflight())
            elif path.path == '/api/log':
                identity = urllib.parse.parse_qs(path.query).get('id', [''])[0]
                state = controller.view()
                entries = state['workers'] + ([state['lead']] if state['lead'] else [])
                entry = next((e for e in entries if e['id'] == identity), None)
                if not entry:
                    raise ValueError('Unknown log')
                file = Path(entry['log'])
                with file.open('rb') as stream:
                    stream.seek(max(0, file.stat().st_size - 64000))
                    log = stream.read(64000).decode('utf-8', 'replace')
                self.send(200, {'text': log})
            elif path.path == '/api/export':
                self.send(200, controller.export(), 'text/plain; charset=utf-8')
            else:
                self.send(404, {'error': 'Not found'})
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            self.send(400, {'error': str(error)})

    def do_POST(self):
        if not self.authorized():
            self.send(403, {'error': 'Unauthorized origin or token'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 0 or size > 64000:
                raise ValueError('Request too large')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('Expected JSON object')
            controller = self.server.controller
            path = urllib.parse.urlsplit(self.path).path
            if path == '/api/start':
                run = controller.state['run']
                if run and run['status'] in ('paused', 'blocked', 'stopped'):
                    if controller.jobs:
                        raise ValueError('Previous jobs are still stopping')
                    result = controller.control('resume')
                else:
                    result = controller.start(body.get('objective', DEFAULT_OBJECTIVE))
            elif path == '/api/worker':
                result = controller.add_worker(body['title'], body['task'], body['allowed_files'], body['checks'],
                    body['task_id'], body.get('role', 'implementation'), body.get('verifies_worker', ''))
            elif path == '/api/control':
                result = controller.control(body['action'], body.get('text', ''))
            elif path == '/api/review':
                result = controller.review(body['worker_id'])
            elif path == '/api/integrate':
                result = controller.integrate(body['worker_id'])
            elif path == '/api/cancel-worker':
                result = controller.cancel_worker(body['worker_id'])
            elif path == '/api/reject':
                result = controller.reject(body['worker_id'])
            elif path == '/api/publish':
                result = controller.publish(body['summary'])
            elif path == '/api/finish':
                result = controller.finish(body['summary'], body.get('outcome', 'completed'))
            else:
                self.send(404, {'error': 'Not found'})
                return
            self.send(200, result)
        except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
            self.send(400, {'error': str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--state-dir', default=str(Path.home() / '.local/state/chat-on-steroids-adal'))
    parser.add_argument('--adal', default=str(Path.home() / '.adal/bin/adal'))
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--max-turns', type=int, default=30)
    args = parser.parse_args()
    os.umask(0o077)
    if args.timeout < 1 or args.max_turns < 1:
        parser.error('timeout and max-turns must be positive')
    controller = Controller(args.state_dir, args.adal, args.timeout, args.max_turns)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.controller = controller
    controller.url = f'http://127.0.0.1:{server.server_port}'
    controller.start_usage()
    print(f'Dashboard: {controller.url}/?token={controller.token}', flush=True)
    print('Idle: no model requests until Start/Resume. Billing: AdaL credits.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
