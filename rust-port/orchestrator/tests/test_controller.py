import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('controller', Path(__file__).resolve().parents[1] / 'server.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def wait_for(predicate, timeout=5):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError('Condition timed out')


class Controlled(module.Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = []
        self.release_lead = threading.Event()
        self.release_worker = threading.Event()
        self.worker_success = True
        self.out_of_scope = False

    def validate_source(self):
        if module.git(self.source_fixture, 'branch', '--show-current') != module.BRANCH:
            raise ValueError('wrong branch')

    def preflight(self):
        return {'ok': True}

    def execute(self, identity, workspace, model, prompt_file, prompt, log_path, session=None, lead=False):
        self.calls.append({'id': identity, 'session': session, 'lead': lead, 'prompt': prompt})
        Path(log_path).write_text('test log\n')
        (self.release_lead if lead else self.release_worker).wait(5)
        if not lead:
            worker = self.find_worker(identity)
            for doc in worker['required_docs']:
                target = Path(workspace) / doc
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('a') as stream:
                    stream.write(f'\n{identity}: exact test command passed; native evidence not run.\n')
            file = Path(workspace) / ('rust-port/b.txt' if self.out_of_scope else 'rust-port/a.txt')
            if worker['role'] == 'implementation':
                file.write_text('worker changed\n')
        return {'success': True if lead else self.worker_success, 'session_id': 'lead-session' if lead else 'worker-session',
                'answer': 'validated report' + ('\nVERIFICATION: PASS' if not lead and self.find_worker(identity)['role'] == 'verification' else ''), 'complete': True, 'exit_code': 0}


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        (self.source / 'rust-port/docs').mkdir(parents=True)
        (self.source / 'rust-port/scripts').mkdir()
        (self.source / 'rust-port/docs/task-cards.md').write_text('## R00: Fixture baseline\n## R01: Fixture next task\n')
        (self.source / 'rust-port/scripts/verify-docs.py').write_text('print("Fixture docs passed")\n')
        (self.source / 'AGENTS.md').write_text('Fixture instructions\n')
        (self.source / 'rust-port/a.txt').write_text('original\n')
        (self.source / 'rust-port/b.txt').write_text('other\n')
        module.git(self.source, 'init', '-q')
        module.git(self.source, 'config', 'user.name', 'Test')
        module.git(self.source, 'config', 'user.email', 'test@localhost')
        module.git(self.source, 'config', 'commit.gpgsign', 'false')
        module.git(self.source, 'add', '--all')
        module.git(self.source, 'commit', '-qm', 'baseline')
        module.git(self.source, 'branch', '-m', module.BRANCH)
        self.remote = self.root / 'remote.git'
        module.git(self.source, 'clone', '--bare', str(self.source), str(self.remote))
        module.git(self.source, 'remote', 'add', 'fork', str(self.remote))
        self.repo_patch = patch.object(module, 'REPO', self.source)
        self.repo_patch.start()
        self.controller = Controlled(self.root / 'state', '/fake/adal')
        self.controller.source_fixture = self.source

    def tearDown(self):
        self.controller.shutdown()
        self.controller.release_worker.set()
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        self.controller.instance_lock.close()
        self.repo_patch.stop()
        self.temp.cleanup()

    def start(self):
        self.controller.start('Implement only the synthetic test objective')
        wait_for(lambda: len(self.controller.calls) == 1)

    def worker(self, path='rust-port/a.txt', role='implementation', verifies_worker=''):
        task = ('Context: This fixture tests the exact original source owner and required docs. '
                'Steps: Implement the small assigned change and preserve all neighboring behavior. '
                'Acceptance: The deterministic fixture produces the expected changed bytes and evidence. '
                'Negative cases: Do not change unrelated files, do not claim native checks ran. '
                'Documentation: Update the task card, task report and dated worklog with exact commands. '
                'Handoff: Report actual tests, failures, source bounds and the next eligible task.')
        return self.controller.add_worker('task', task, [path], ['test command'], role=role, verifies_worker=verifies_worker)

    def test_completion_resumes_same_lead_session_once(self):
        self.start()
        worker = self.worker()
        self.controller.release_lead.set()
        wait_for(lambda: self.controller.state['lead']['status'] == 'completed')
        self.controller.release_worker.set()
        wait_for(lambda: len([x for x in self.controller.calls if x['lead']]) == 2)
        second = [x for x in self.controller.calls if x['lead']][1]
        self.assertEqual(second['session'], 'lead-session')
        self.assertIn(worker['id'], second['prompt'])
        self.assertIn('validated report', second['prompt'])
        wait_for(lambda: not self.controller.jobs)
        self.assertEqual(self.controller.state['run']['turns'], 2)

    def test_completion_during_lead_is_delivered_after_turn(self):
        self.start()
        self.worker()
        self.controller.release_worker.set()
        wait_for(lambda: self.controller.state['workers'][0]['status'] == 'completed')
        self.assertEqual(len([x for x in self.controller.calls if x['lead']]), 1)
        self.assertEqual(len(self.controller.state['inbox']), 1)
        self.controller.release_lead.set()
        wait_for(lambda: len([x for x in self.controller.calls if x['lead']]) == 2)

    def test_pause_retains_result_until_resume(self):
        self.start()
        self.worker()
        self.controller.control('pause')
        self.controller.release_worker.set()
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        self.assertEqual(self.controller.state['run']['status'], 'paused')
        self.assertEqual(len(self.controller.state['inbox']), 1)
        self.controller.control('resume')
        wait_for(lambda: self.controller.state['run']['turns'] == 2)

    def test_overlap_and_concurrency_refused(self):
        self.start()
        self.worker()
        with self.assertRaisesRegex(ValueError, 'overlap'):
            self.worker()
        self.worker('rust-port/docs/b.txt', role='audit')
        with self.assertRaisesRegex(ValueError, 'Two workers'):
            self.worker('rust-port/c.txt')

    def test_out_of_scope_changes_fail_and_notify_lead(self):
        self.start()
        self.controller.out_of_scope = True
        self.worker()
        self.controller.release_worker.set()
        wait_for(lambda: self.controller.state['workers'][0]['status'] == 'failed')
        self.assertIn('Out-of-scope', self.controller.state['workers'][0]['result']['error'])
        self.assertEqual(self.controller.state['inbox'][0]['kind'], 'worker')

    def test_review_gate_integration_and_shared_source_untouched(self):
        self.start()
        worker = self.worker()
        self.controller.control('pause')
        self.controller.release_worker.set()
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        with self.assertRaisesRegex(ValueError, 'Read the completed'):
            self.controller.integrate(worker['id'])
        self.assertIn('worker changed', self.controller.review(worker['id'])['patch'])
        self.controller.integrate(worker['id'])
        self.assertEqual((Path(self.controller.state['run']['workspace']) / 'rust-port/a.txt').read_text(), 'worker changed\n')
        self.assertEqual((self.source / 'rust-port/a.txt').read_text(), 'original\n')
        self.assertIn('worker changed', module.git(Path(self.controller.state['run']['workspace']), 'diff', self.controller.state['run']['baseline']))
        self.assertTrue(self.controller.integrate(worker['id'])['already_integrated'])

    def test_conflicting_patch_refused_without_partial_mutation(self):
        self.start()
        worker = self.worker()
        self.controller.control('pause')
        self.controller.release_worker.set()
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        workspace = Path(self.controller.state['run']['workspace'])
        (workspace / 'rust-port/a.txt').write_text('lead different\n')
        module.git(workspace, 'add', '--all')
        module.git(workspace, 'commit', '-qm', 'lead edit')
        self.controller.review(worker['id'])
        with self.assertRaises(Exception):
            self.controller.integrate(worker['id'])
        self.assertEqual((workspace / 'rust-port/a.txt').read_text(), 'lead different\n')
        self.assertFalse(module.git(workspace, 'status', '--porcelain'))

    def test_finish_cannot_skip_active_or_unreviewed_workers(self):
        self.start()
        worker = self.worker()
        with self.assertRaisesRegex(ValueError, 'Workers must finish'):
            self.controller.finish('done', 'completed')
        self.controller.control('pause')
        self.controller.release_worker.set()
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        with self.assertRaisesRegex(ValueError, 'Workers must finish'):
            self.controller.finish('done', 'completed')
        self.controller.reject(worker['id'])
        with self.assertRaisesRegex(ValueError, 'inbox'):
            self.controller.finish('done', 'completed')

    def test_dirty_snapshot_bytes_preserved_but_shared_run_refuses_dirty_source(self):
        (self.source / 'rust-port/a.txt').write_text('dirty baseline\n')
        (self.source / 'rust-port/new.txt').write_text('untracked baseline\n')
        workspace = self.root / 'snapshot-check'
        module.snapshot(self.source, workspace)
        self.assertEqual((workspace / 'rust-port/a.txt').read_text(), 'dirty baseline\n')
        self.assertTrue((workspace / 'rust-port/new.txt').exists())
        with self.assertRaisesRegex(ValueError, 'uncommitted changes'):
            self.start()
        self.assertEqual((self.source / 'rust-port/a.txt').read_text(), 'dirty baseline\n')

    def test_only_one_controller_can_own_state(self):
        with self.assertRaisesRegex(ValueError, 'already owns'):
            module.Controller(self.root / 'state', '/fake/adal')

    def test_invalid_paths(self):
        for name in ['/tmp/x', '../x', 'rust-port/../x', 'rust-port/*.rs', 'rust-port/orchestrator/server.py', 'rust-port/target/x', '.env', 'rust-port/.env.local']:
            self.assertFalse(module.valid_file(name), name)
        self.assertTrue(module.valid_file('rust-port/gpui-prototype/src/main.rs'))

    def test_cancel_cannot_become_success_and_keeps_slot_until_exit(self):
        self.start()
        worker = self.worker()
        self.worker('rust-port/docs/b.txt', role='audit')
        self.controller.cancel_worker(worker['id'])
        with self.assertRaisesRegex(ValueError, 'Two workers'):
            self.worker('rust-port/c.txt')
        self.controller.release_worker.set()
        wait_for(lambda: self.controller.state['workers'][0].get('finished_at'))
        self.assertEqual(self.controller.state['workers'][0]['status'], 'cancelled')
        self.assertIn(worker['id'], json.dumps(self.controller.state['inbox']))

    def test_stop_prevents_followup_turns(self):
        self.start()
        self.worker()
        self.controller.control('stop')
        self.controller.release_worker.set()
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        self.assertEqual(self.controller.state['run']['status'], 'stopped')
        self.assertEqual(self.controller.state['run']['turns'], 1)
        self.assertEqual(self.controller.state['workers'][0]['status'], 'cancelled')

    def test_restart_marks_interrupted_and_retains_mailbox(self):
        self.start()
        self.worker()
        state = self.controller.view()
        recovery = self.root / 'recovery'
        recovery.mkdir()
        (recovery / 'state.json').write_text(json.dumps(state))
        restored = module.Controller(recovery, '/fake/adal')
        try:
            self.assertEqual(restored.state['run']['status'], 'paused')
            self.assertEqual(restored.state['lead']['status'], 'interrupted')
            self.assertEqual(restored.state['workers'][0]['status'], 'interrupted')
            self.assertEqual(len(restored.state['inbox']), 2)
            self.assertFalse(restored.processes)
            self.assertFalse(restored.jobs)
        finally:
            restored.shutdown()
            restored.instance_lock.close()

    def test_http_auth_host_and_origin_boundaries(self):
        server = module.ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
        server.controller = self.controller
        self.controller.url = f'http://127.0.0.1:{server.server_port}'
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = self.controller.url + '/api/state'
        try:
            with self.assertRaises(urllib.error.HTTPError) as denied:
                urllib.request.urlopen(url)
            self.assertEqual(denied.exception.code, 403)
            denied.exception.close()
            token = {'Authorization': 'Bearer ' + self.controller.token}
            with urllib.request.urlopen(urllib.request.Request(url, headers=token)) as response:
                self.assertIsNone(json.load(response)['run'])
            for extra in ({'Origin': 'http://evil.test'}, {'Host': 'evil.test'}):
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    urllib.request.urlopen(urllib.request.Request(url, headers={**token, **extra}))
                self.assertEqual(denied.exception.code, 403)
                denied.exception.close()
            req = urllib.request.Request(self.controller.url + '/api/control', data=b'{}',
                                         headers={**token, 'Origin': 'http://evil.test'})
            with self.assertRaises(urllib.error.HTTPError) as denied:
                urllib.request.urlopen(req)
            self.assertEqual(denied.exception.code, 403)
            denied.exception.close()
        finally:
            server.shutdown()
            server.server_close()

    def test_detailed_brief_and_doc_updates_required(self):
        self.start()
        with self.assertRaisesRegex(ValueError, 'detailed brief'):
            self.controller.add_worker('vague', 'Implement R00', ['rust-port/a.txt'], [])
        with self.assertRaisesRegex(ValueError, 'documentation only'):
            self.worker(role='audit')
        with self.assertRaisesRegex(ValueError, 'Unknown worker'):
            self.worker('rust-port/docs/check.md', role='verification', verifies_worker='missing')

    def test_verification_required_and_publication_pushes_only_pr_branch(self):
        self.start()
        worker = self.worker()
        self.controller.control('pause')
        self.controller.release_lead.set()
        self.controller.release_worker.set()
        wait_for(lambda: not self.controller.jobs)
        self.controller.review(worker['id'])
        self.controller.integrate(worker['id'])
        with self.assertRaisesRegex(ValueError, 'independent verification'):
            self.controller.publish('Task implementation')
        self.controller.state['run']['status'] = 'running'
        verification = self.worker('rust-port/docs/verification.md', role='verification', verifies_worker=worker['id'])
        self.controller.control('pause')
        wait_for(lambda: not self.controller.jobs)
        self.controller.review(verification['id'])
        self.controller.integrate(verification['id'])
        result = self.controller.publish('R00 independently verified with updated docs')
        self.assertEqual(result['branch'], module.BRANCH)
        self.assertEqual((self.source / 'rust-port/a.txt').read_text(), 'worker changed\n')
        remote_head = module.git(self.source, 'ls-remote', 'fork', 'refs/heads/' + module.BRANCH).split()[0]
        self.assertEqual(remote_head, result['commit'])
        self.assertFalse(module.git(self.source, 'status', '--porcelain'))
        self.assertFalse(self.controller.state['run']['pending_push'])

    def test_publication_refuses_external_source_changes(self):
        self.start()
        self.controller.control('pause')
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        (self.source / 'rust-port/a.txt').write_text('external changes\n')
        with self.assertRaisesRegex(ValueError, 'changed outside'):
            self.controller.publish('No work')
        self.assertEqual((self.source / 'rust-port/a.txt').read_text(), 'external changes\n')

    def test_failed_push_retains_one_commit_and_retries_without_duplication(self):
        self.start()
        worker = self.worker('rust-port/docs/audit.md', role='audit')
        self.controller.control('pause')
        self.controller.release_worker.set()
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        self.controller.review(worker['id'])
        self.controller.integrate(worker['id'])
        original_git = module.git
        def fail_push(cwd, *args, **kwargs):
            if args and args[0] == 'push':
                raise module.subprocess.CalledProcessError(1, ['git', 'push'])
            return original_git(cwd, *args, **kwargs)
        with patch.object(module, 'git', side_effect=fail_push):
            with self.assertRaisesRegex(ValueError, 'push failed'):
                self.controller.publish('Audited documentation')
        head = original_git(self.source, 'rev-parse', 'HEAD')
        self.assertTrue(self.controller.state['run']['pending_push'])
        self.controller.publish('Retry same publication')
        self.assertEqual(original_git(self.source, 'rev-parse', 'HEAD'), head)
        self.assertFalse(self.controller.state['run']['pending_push'])
        self.assertEqual(original_git(self.source, 'ls-remote', 'fork', 'refs/heads/' + module.BRANCH).split()[0], head)

    def test_dispatcher_cannot_get_edit_or_shell_tools(self):
        fake = self.root / 'inspect-adal'
        fake.write_text('#!/usr/bin/env python3\nimport sys,json\nprint(json.dumps({"type":"answer","content":sys.argv[sys.argv.index("--enabled-default-tools")+1]}))\nprint(json.dumps({"type":"complete","exit_code":0,"session_id":"fake"}))\n')
        fake.chmod(0o700)
        self.controller.adal = str(fake)
        self.controller.state['run'] = {'id': 'fake', 'status': 'running'}
        self.controller.state['lead'] = {'id': 'lead-test', 'status': 'running'}
        result = module.Controller.execute(self.controller, 'lead-test', self.source, module.LEAD_MODEL,
            module.HERE / 'prompts/lead.md', 'test', self.root / 'lead-tools.log', lead=True)
        self.assertEqual(result['answer'], 'Read,Search')
        self.controller.state['run'] = None

    def test_start_renews_exhausted_turn_and_worker_allowances(self):
        self.start()
        self.controller.control('pause')
        self.controller.release_lead.set()
        wait_for(lambda: not self.controller.jobs)
        run = self.controller.state['run']
        run['turns'] = run['turn_limit']
        run['worker_limit'] = 0
        self.controller.control('resume')
        self.assertEqual(run['turn_limit'], 60)
        self.assertEqual(run['worker_limit'], 60)
        wait_for(lambda: not self.controller.jobs)

    def test_real_process_protocol_and_timeout(self):
        fake = self.root / 'fake-adal'
        fake.write_text('#!/usr/bin/env python3\nimport json\nprint(json.dumps({"type":"answer","content":"OK"}))\nprint(json.dumps({"type":"complete","exit_code":0,"session_id":"fake"}))\n')
        fake.chmod(0o700)
        self.controller.adal = str(fake)
        self.controller.state['run'] = {'id': 'fake-run', 'status': 'running'}
        result = module.Controller.execute(self.controller, 'process-test', self.source, module.WORKER_MODEL,
                                            module.HERE / 'prompts/worker.md', 'test', self.root / 'process.log')
        self.assertTrue(result['success'])
        self.assertEqual(result['session_id'], 'fake')
        fake.write_text('#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n')
        self.controller.timeout = .1
        result = module.Controller.execute(self.controller, 'timeout-test', self.source, module.WORKER_MODEL,
                                            module.HERE / 'prompts/worker.md', 'test', self.root / 'timeout.log')
        self.assertFalse(result['success'])
        self.assertIn('timed out', result['error'])
        self.controller.state['run'] = None


if __name__ == '__main__':
    unittest.main()
