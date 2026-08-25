"""Durable, strict-finite retained-artifact helpers."""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np


def json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        scalar = value.item()
        if isinstance(scalar, float) and not math.isfinite(scalar):
            raise ValueError("nonfinite numeric value is forbidden in retained JSON")
        return scalar
    raise TypeError(type(value).__name__)


def fsync_directory(path: Path) -> None:
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return
    # Windows has no supported directory-fsync equivalent. Durability is
    # supplied by the MOVEFILE_WRITE_THROUGH rename below; never call
    # FlushFileBuffers on a read-only directory handle.
    return


def atomic_replace(source: Path, destination: Path) -> None:
    if os.name != "nt":
        os.replace(source, destination)
        fsync_directory(destination.parent)
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    move_file_ex = kernel32.MoveFileExW
    move_file_ex.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
    move_file_ex.restype = ctypes.c_int
    MOVEFILE_REPLACE_EXISTING = 0x1
    MOVEFILE_WRITE_THROUGH = 0x8
    if not move_file_ex(str(source), str(destination), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH):
        raise OSError(ctypes.get_last_error(), f"write-through atomic move failed: {source} -> {destination}")


def write_json_atomic(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    encoded = json.dumps(
        value,
        indent=2,
        sort_keys=True,
        default=json_default,
        allow_nan=False,
    ).encode("utf-8")
    with temporary.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    atomic_replace(temporary, path)


def fsync_file(path: Path) -> None:
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()
