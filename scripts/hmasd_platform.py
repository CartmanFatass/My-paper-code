"""Small native-host adapters shared by HMASD workflow helpers.

The workflow uses cooperative exclusive locks and best-effort directory
durability on both POSIX and native Windows. This module exposes only those
mechanics; state ownership and CAS remain in their existing helpers.
"""

from __future__ import annotations

import contextlib
import errno
import os
from pathlib import Path
import stat
import time
from typing import Iterator


IS_WINDOWS = os.name == "nt"
_FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


@contextlib.contextmanager
def exclusive_file_lock(descriptor: int) -> Iterator[None]:
    """Hold one cooperative exclusive byte-range/file lock until exit."""

    if IS_WINDOWS:
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b"\0")
            os.fsync(descriptor)
        while True:
            os.lseek(descriptor, 0, os.SEEK_SET)
            try:
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
                break
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                time.sleep(0.05)
        try:
            yield
        finally:
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)


def fsync_directory(path: str | os.PathLike[str]) -> None:
    """Persist a directory entry where the native runtime supports it."""

    if IS_WINDOWS:
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(os.fspath(path), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def apply_fd_mode(descriptor: int, mode: int) -> None:
    """Apply a POSIX mode when available; Windows ACLs remain unchanged."""

    if hasattr(os, "fchmod"):
        os.fchmod(descriptor, mode)


def is_reparse_or_symlink(path: Path, info: os.stat_result | None = None) -> bool:
    """Recognize POSIX symlinks and Windows reparse-point aliases."""

    try:
        observed = os.lstat(path) if info is None else info
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(observed.st_mode):
        return True
    attributes = getattr(observed, "st_file_attributes", 0)
    return bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT)
