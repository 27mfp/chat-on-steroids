"""Lead-only AdaL orchestration tools; implementation belongs to workers."""
import json
import os
import urllib.request


def _call(path, body=None):
    headers = {'Authorization': 'Bearer ' + os.environ['PORT_ORCHESTRATOR_TOKEN'],
               'Content-Type': 'application/json'}
    request = urllib.request.Request(os.environ['PORT_ORCHESTRATOR_URL'] + path,
                                    data=None if body is None else json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def start_worker(task_id: str, title: str, task: str, allowed_files: list[str],
                 checks: list[str], role: str = 'implementation', verifies_worker: str = ''):
    """Dispatch a detailed, bounded GLM task on PR #4's source lineage.

    Args:
        task_id: Exact card ID from task-cards.md, e.g. R00 or R01.
        title: Short assignment name.
        task: Detailed brief with Context:, Steps:, Acceptance:, Negative cases:,
            Documentation:, and Handoff: sections. Explain actual source and APIs.
        allowed_files: Exact repository-relative files; no globs/directories.
            Task report and worklog paths are added automatically. Implementation
            and verification also update task-cards.md. No orchestration edits.
        checks: Exact commands with working directories and expected outcomes.
        role: implementation, verification (no code changes), or audit (docs only).
        verifies_worker: Implementation worker ID being independently verified;
            mandatory for verification. Its integrated commit must be in this base.
    """
    return _call('/api/worker', dict(task_id=task_id, title=title, task=task,
                                   allowed_files=allowed_files, checks=checks,
                                   role=role, verifies_worker=verifies_worker))


def orchestration_status():
    """Read task states, completion reports, PR publication and account usage."""
    return _call('/api/state')


def review_worker(worker_id: str):
    """Read the worker's evidence and complete patch; never implement it yourself."""
    return _call('/api/review', {'worker_id': worker_id})


def integrate_worker(worker_id: str):
    """Integrate a reviewed worker patch into the PR-lineage staging workspace.

    Implementation must receive a separate verification worker before publication.
    Verification integration records which implementation it independently checked.
    """
    return _call('/api/integrate', {'worker_id': worker_id})


def reject_worker(worker_id: str):
    """Reject terminal work; dispatch a detailed correction instead of fixing it yourself."""
    return _call('/api/reject', {'worker_id': worker_id})


def cancel_worker(worker_id: str):
    """Cancel obsolete active work; its final state is delivered automatically."""
    return _call('/api/cancel-worker', {'worker_id': worker_id})


def publish_progress(summary: str):
    """Commit and push reviewed, independently verified progress to PR #4 only.

    The controller checks branch, source epoch, docs and remote lineage. It never
    force-pushes, merges the PR, or publishes a release. No manual patch application.
    """
    return _call('/api/publish', {'summary': summary})


def finish_run(summary: str, outcome: str = 'completed'):
    """Publish verified progress and finish with actual evidence or an external gate.

    outcome is completed or blocked. Never finish while workers/results/review
    remain. Exhaust independent work before reporting unavailable platform gates.
    """
    return _call('/api/finish', {'summary': summary, 'outcome': outcome})


CUSTOM_TOOLS = [start_worker, orchestration_status, review_worker, integrate_worker,
                reject_worker, cancel_worker, publish_progress, finish_run]
