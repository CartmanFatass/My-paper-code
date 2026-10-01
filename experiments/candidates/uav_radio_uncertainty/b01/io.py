"""Compact identities and atomic, pickle-free direction-owned evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource

import numpy as np


def identity(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return dict(path=str(path.resolve()), bytes=path.stat().st_size, sha256=digest.hexdigest())


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, default=_json, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    os.replace(temporary, path)


def write_npz(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, **values)
    os.replace(temporary, path)
    return identity(path)


def save_evidence(path,values,ledger,binding):
    """Register intent before persistence; retain paid evidence on IO failure."""
    path=Path(path).resolve()
    binding.update(path=str(path),write_status="writing")
    ledger.append(binding)
    try:
        binding.update(write_npz(path,values))
        binding["write_status"]="complete"
    except Exception as exc:
        binding.update(write_status="failed",write_error=dict(type=type(exc).__name__,message=str(exc)),
                       final_exists=path.exists(),partial_exists=path.with_name(path.name+".partial").exists())
        for key,candidate in (("final",path),("partial",path.with_name(path.name+".partial"))):
            if candidate.exists():
                try:
                    binding[key+"_bytes"]=candidate.stat().st_size
                    if key=="final":
                        binding.update(identity(candidate))
                    else:
                        binding["partial_identity"]=identity(candidate)
                except Exception as identity_error:
                    binding[key+"_identity_error"]=dict(type=type(identity_error).__name__,message=str(identity_error))
        raise
    return binding


def artifact_bytes(ledger):
    return sum(item.get("bytes",item.get("final_bytes",0))+item.get("partial_bytes",0) for item in ledger)


def resources():
    own, child = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_seconds=own.ru_utime + own.ru_stime,
                waited_child_cpu_seconds=child.ru_utime + child.ru_stime,
                peak_rss_kib=own.ru_maxrss, peak_rss_scope="this Linux process")


def read_npz(binding, root=None):
    path = Path(binding["path"]) if root is None else Path(root) / Path(binding["path"]).name
    actual = identity(path)
    if any(actual[key] != binding[key] for key in ("bytes", "sha256")):
        raise ValueError("raw identity mismatch: " + str(path))
    with np.load(path, allow_pickle=False) as value:
        return {key: value[key] for key in value.files}
