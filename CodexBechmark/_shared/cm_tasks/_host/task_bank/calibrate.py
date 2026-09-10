"""Bounded host calibration; never launch candidate/model benchmarking here."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from task_bank import TASKS, install, apply_reference, grade
from task_bank.catalog import SOURCES, WRONG


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch-parent", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    parent = args.scratch_parent.resolve()
    repo = Path(__file__).resolve().parents[5]
    if parent != (repo / "temp" / "tests").resolve():
        raise ValueError("scratch-parent must be this checkout's temp/tests")
    parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="cm-bank-", dir=parent)).resolve()
    report = dict(passed=False, python=sys.executable, tasks={}, scratch=str(scratch))
    started = time.monotonic()
    try:
        for task, metadata in TASKS.items():
            workspace = scratch / task
            install(workspace, task)
            files = sorted(str(p.relative_to(workspace)).replace('\\','/')
                           for p in workspace.rglob('*') if p.is_file())
            assert files == sorted(SOURCES[task]), (task, files)
            baseline = grade(workspace, task)
            public_baseline = subprocess.run([sys.executable, *metadata['public_command']],
                                            cwd=workspace, capture_output=True, text=True, timeout=30)
            apply_reference(workspace, task)
            reference = grade(workspace, task)
            public = subprocess.run([sys.executable, *metadata['public_command']], cwd=workspace,
                                    capture_output=True, text=True, timeout=30)
            for relative, content in WRONG[task].items():
                (workspace / relative).write_text(content, encoding='utf-8')
            wrong = grade(workspace, task)
            row = dict(baseline=baseline, reference=reference, wrong=wrong,
                       public_baseline_returncode=public_baseline.returncode,
                       public_reference_returncode=public.returncode,
                       public_reference_stderr=public.stderr)
            row['passed'] = (not baseline['passed'] and reference['passed'] and
                             not wrong['passed'] and public.returncode == 0 and
                             public_baseline.returncode != 0)
            report['tasks'][task] = row
            print(task, 'PASS' if row['passed'] else 'FAIL', flush=True)
        # A round installs exactly two disjoint tasks; installing the second preserves the first.
        pair = scratch / 'pair'
        install(pair,'timeout_bootstrap')
        before={p.relative_to(pair):p.read_bytes() for p in pair.rglob('*') if p.is_file()}
        install(pair,'paired_tape')
        assert all((pair/p).read_bytes()==data for p,data in before.items())
        assert {p.name for p in pair.iterdir()} == {'cm_timeout_bootstrap','cm_paired_tape'}
        report['two_task_isolation'] = True
        report['passed'] = all(row['passed'] for row in report['tasks'].values())
    finally:
        report['seconds'] = time.monotonic() - started
        # Retain checks/diagnostics before removing exactly our own scratch.
        args.out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        assert scratch.parent == parent and scratch.name.startswith('cm-bank-')
        shutil.rmtree(scratch)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
