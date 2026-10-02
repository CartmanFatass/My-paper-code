import os
from pathlib import Path
import subprocess

import pytest

from scripts import hmasd_source_snapshot


def test_snapshot_uses_committed_bytes_and_shared_git_store(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()

    def git(source, *args, timeout=30):
        return subprocess.run(
            ['git', '-C', str(source), *args], check=True,
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

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


@pytest.mark.parametrize('worktree_config', [False, True])
def test_snapshot_materializes_sparse_inputs_without_changing_other_worktrees(
    tmp_path, worktree_config,
):
    root = tmp_path / 'repo'
    root.mkdir()

    def git(source, *args, timeout=30):
        return subprocess.run(
            ['git', '-C', str(source), *args], check=True,
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )

    git(root, 'init')
    git(root, 'config', 'user.name', 'Fixture')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    (root / 'code').mkdir()
    (root / 'code' / 'input.py').write_text('published')
    excluded = Path('runs/direction/checks.json')
    (root / excluded).parent.mkdir(parents=True)
    (root / excluded).write_text('{"cpu_seconds": 7.4}\n')
    git(root, 'add', 'code/input.py', str(excluded))
    git(root, 'commit', '-m', 'published inputs')
    sha = git(root, 'rev-parse', 'HEAD').stdout.strip()
    if worktree_config:
        git(root, 'config', 'extensions.worktreeConfig', 'true')
        git(root, 'config', '--worktree', 'core.sparseCheckout', 'true')
    else:
        git(root, 'config', 'core.sparseCheckout', 'true')
    patterns = root / '.git' / 'info' / 'sparse-checkout'
    patterns.parent.mkdir(exist_ok=True)
    patterns.write_text('/code/\n')
    git(root, 'read-tree', '-mu', 'HEAD')
    assert not (root / excluded).exists()
    (root / 'code' / 'input.py').write_text('author editing')

    sibling = tmp_path / 'accepted-sibling'
    git(root, 'worktree', 'add', '--detach', '--lock', str(sibling), sha)
    assert not (sibling / excluded).exists()
    (sibling / 'keep.txt').write_text('existing operation')
    configs = [root / '.git' / 'config', root / '.git' / 'config.worktree']
    before = {path: path.read_bytes() if path.exists() else None for path in configs}
    old_patterns = patterns.read_bytes()

    snapshot = hmasd_source_snapshot.prepare(root, root / '.git', sha, git)

    assert (snapshot / excluded).read_text() == '{"cpu_seconds": 7.4}\n'
    assert (snapshot / 'code' / 'input.py').read_text() == 'published'
    assert git(snapshot, 'rev-parse', 'HEAD').stdout.strip() == sha
    assert not any(line.startswith('S ') for line in git(snapshot, 'ls-files', '-t').stdout.splitlines())
    assert git(snapshot, 'status', '--porcelain').stdout == ''
    from scripts import hmasd_launch
    hmasd_launch._validate_source_local(snapshot, sha)
    assert (root / 'code' / 'input.py').read_text() == 'author editing'
    assert not (root / excluded).exists()
    assert not (sibling / excluded).exists()
    assert (sibling / 'keep.txt').read_text() == 'existing operation'
    assert patterns.read_bytes() == old_patterns
    assert {path: path.read_bytes() if path.exists() else None for path in configs} == before
