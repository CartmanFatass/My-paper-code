"""Own one fresh scratch directory per pytest invocation, including failed runs."""
from pathlib import Path
import os
import shutil
import stat
import tempfile
import warnings

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    root = Path(__file__).resolve().parents[1] / "temp"
    root.mkdir(exist_ok=True)
    # Refuse redirected scratch roots: cleanup must stay in this checkout.
    if root.resolve() != root:
        raise pytest.UsageError("Checkout temp/ must not be a symlink or junction")
    requested = config.option.basetemp
    if requested:
        target = Path(requested).absolute()
        resolved = target.resolve()
        if not resolved.is_relative_to(root) or resolved == root or resolved != target:
            raise pytest.UsageError("--basetemp must be a fresh directory inside checkout temp/")
        if target.exists():
            raise pytest.UsageError("--basetemp already exists; choose a new tag (existing data is preserved)")
        target.mkdir(parents=True)
    else:
        parent = root / "tests"
        if parent.resolve() != parent:
            raise pytest.UsageError("temp/tests must not be a symlink or junction")
        parent.mkdir(exist_ok=True)
        target = Path(tempfile.mkdtemp(prefix="pytest-", dir=parent))
    config.option.basetemp = str(target)
    config._hmasd_owned_scratch = target


def pytest_unconfigure(config):
    target = getattr(config, "_hmasd_owned_scratch", None)
    if target is None:
        return
    try:
        if target.resolve() != target:
            raise OSError("scratch directory was redirected during the test")
        def clear_copied_readonly(function, path, error):
            # copytree copies Windows read-only directory attributes as well as files.
            # Only repair this invocation's copies, never source ACLs or old scratch.
            failed = Path(path)
            if (not isinstance(error[1], PermissionError)
                    or not failed.resolve().is_relative_to(target)
                    or not getattr(failed.stat(), "st_file_attributes", 0)
                    & stat.FILE_ATTRIBUTE_READONLY):
                raise error[1]
            os.chmod(failed, stat.S_IWRITE | stat.S_IREAD)
            function(path)

        shutil.rmtree(target, onerror=clear_copied_readonly)
    except OSError as exc:
        warnings.warn(pytest.PytestWarning(f"Test scratch cleanup failed at {target}: {exc}"))
