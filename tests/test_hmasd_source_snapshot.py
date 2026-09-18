import os
from pathlib import Path
import subprocess

from scripts import hmasd_source_snapshot


def test_snapshot_uses_committed_bytes_and_shared_git_store(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()

    def git(source, *args, timeout=30):
        return subprocess.run(['git', '-C', str(source), *args], check=True,
                              capture_output=True, text=True, timeout=timeout)

    git(root, 'init')
    git(root, 'config', 'user.name', 'Fixture')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    (root / 'input.py').write_text('published')
    git(root, 'add', 'input.py')
    git(root, 'commit', '-m', 'fixture')
    sha = git(root, 'rev-parse', 'HEAD').stdout.strip()
    (root / 'input.py').write_text('author editing')
    (root / 'untracked.py').write_text('not an input')
    snapshot = hmasd_source_snapshot.prepare(root, root / '.git', sha, git)
    assert (snapshot / 'input.py').read_text() == 'published'
    assert not (snapshot / 'untracked.py').exists()
    common = Path(git(snapshot, 'rev-parse', '--git-common-dir').stdout.strip())
    if not common.is_absolute():
        common = snapshot / common
    assert common.resolve() == (root / '.git').resolve()
    assert (root / 'input.py').read_text() == 'author editing'
    assert 'locked' in git(root, 'worktree', 'list', '--porcelain').stdout


def test_snapshot_environment_does_not_import_author_python_paths(monkeypatch):
    for key in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONUSERBASE'):
        monkeypatch.setenv(key, 'author-specific')
    environment = hmasd_source_snapshot.environment()
    assert all(key not in environment for key in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONUSERBASE'))
    assert environment['PYTHONNOUSERSITE'] == '1'
    assert environment['PYTHONDONTWRITEBYTECODE'] == '1'
    assert os.environ['PYTHONPATH'] == 'author-specific'
