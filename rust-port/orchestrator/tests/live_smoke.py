"""Opt-in live handoff test, using AdaL credits and a tiny synthetic repository."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import time

spec = importlib.util.spec_from_file_location('controller', Path(__file__).resolve().parents[1] / 'server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Authorize the small paid model smoke test')
    args = parser.parse_args()
    if not args.live:
        parser.error('Requires --live; this uses AdaL credits')
    with tempfile.TemporaryDirectory(prefix='adal-live-handoff-') as temp:
        root = Path(temp)
        source = root / 'source'
        (source / 'rust-port/docs').mkdir(parents=True)
        (source / 'AGENTS.md').write_text('Synthetic connectivity fixture. Only the assigned smoke task is in scope. No nested delegation.\n')
        (source / 'rust-port/docs/implementation-start-plan-2026-10-01.md').write_text('Synthetic M0 smoke fixture. Read only. No application port work.\n')
        (source / 'rust-port/smoke.txt').write_text('HANDOFF_OK\n')
        (source / 'rust-port/docs/task-cards.md').write_text('## R00: Synthetic audit fixture\n')
        (source / 'rust-port/scripts').mkdir()
        (source / 'rust-port/scripts/verify-docs.py').write_text('print("Synthetic docs verified")\n')
        module.git(source, 'init', '-q')
        module.git(source, 'config', 'user.name', 'Smoke fixture')
        module.git(source, 'config', 'user.email', 'smoke@localhost')
        module.git(source, 'config', 'commit.gpgsign', 'false')
        module.git(source, 'add', '--all')
        module.git(source, 'commit', '-qm', 'fixture')
        module.git(source, 'branch', '-m', module.BRANCH)
        remote = root / 'remote.git'
        module.git(source, 'clone', '--bare', str(source), str(remote))
        module.git(source, 'remote', 'add', 'fork', str(remote))
        module.REPO = source
        class SmokeController(module.Controller):
            def validate_source(self):
                assert module.git(source, 'branch', '--show-current') == module.BRANCH
                assert module.git(source, 'remote', 'get-url', 'fork') == str(remote)
        controller = SmokeController(root / 'state', str(Path.home() / '.adal/bin/adal'), timeout=120, max_turns=3)
        server = module.ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
        server.controller = controller
        controller.url = f'http://127.0.0.1:{server.server_port}'
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            brief = ('Context: Only a synthetic fixture is in scope. Read rust-port/smoke.txt, '
                'whose canonical contents are HANDOFF_OK; this is not GPUI implementation. '
                'Steps: Read the fixture, create the controller-assigned task report and dated '
                'worklog, then run the assigned documentation checks. Do not modify the fixture. '
                'Acceptance: Report HANDOFF_OK exactly and record true doc check evidence. '
                'Negative cases: No code edits, no nested workers, no platform acceptance claims. '
                'Documentation: Write BOTH required_docs paths given by the controller. Include '
                'the fixture contents, checks, actual exit outcomes and synthetic scope. '
                'Handoff: Report HANDOFF_OK and name the docs written plus checks passed.')
            controller.start('ONLY a synthetic orchestration smoke test, not port implementation. '
                'Use start_worker exactly once: task_id R00, role audit, title Read handoff fixture, '
                'allowed_files [], checks ["python3 rust-port/scripts/verify-docs.py", "git diff --check"], '
                'verifies_worker empty, and this exact detailed task brief: ' + brief +
                ' Then end your first turn immediately saying you are waiting. Do not poll or '
                'finish in that turn. When the controller resumes you with completion, use '
                'review_worker, integrate_worker, then finish_run with completed and summary '
                '"Synthetic worker returned HANDOFF_OK; handoff, docs and local fixture publication succeeded". '
                'Role audit does not certify implementation or need a verification worker. '
                'The controller in this synthetic test publishes ONLY to a temporary local bare '
                'Git repository, never GitHub. Do not start more workers or other work.')
            end = time.monotonic() + 180
            seen = 0
            while time.monotonic() < end:
                state = controller.view()
                for event in state['events'][seen:]:
                    print(event['text'], flush=True)
                seen = len(state['events'])
                if state['run']['status'] not in ('running',):
                    if not controller.jobs:
                        break
                time.sleep(.5)
            state = controller.view()
            assert state['run']['status'] == 'completed', json.dumps(state, indent=2)
            assert state['run']['turns'] == 2, state['run']
            assert len(state['workers']) == 1, state['workers']
            assert state['workers'][0]['integrated']
            assert 'HANDOFF_OK' in state['workers'][0]['report']
            first = [json.loads(line) for line in (root / 'state/runs' / state['run']['id'] / 'lead-1.ndjson').read_text().splitlines() if line.startswith('{')]
            original_session = next(e['session_id'] for e in first if e.get('type') == 'complete')
            assert state['lead']['session_id'] == original_session, 'Lead session changed during handoff'
            assert (source / 'rust-port/smoke.txt').read_text() == 'HANDOFF_OK\n'
            forbidden = {'bash', 'edit_file', 'write_file', 'apply_patch', 'Bash', 'Edit', 'Write'}
            for turn in ('lead-1.ndjson', 'lead-2.ndjson'):
                for line in (root / 'state/runs' / state['run']['id'] / turn).read_text().splitlines():
                    if line.startswith('{'):
                        event = json.loads(line)
                        assert not (event.get('type') == 'tool_call' and event.get('name') in forbidden)
            assert module.git(source, 'ls-remote', 'fork', 'refs/heads/' + module.BRANCH).split()[0] == state['run']['source_head']
            print('PASS: real GLM docs task → same read-only Sol dispatcher → review → integration → automatic local fixture publication', flush=True)
        finally:
            controller.shutdown()
            server.shutdown()
            server.server_close()
            deadline = time.monotonic() + 5
            while controller.jobs and time.monotonic() < deadline:
                time.sleep(.05)
            controller.instance_lock.close()


if __name__ == '__main__':
    main()
