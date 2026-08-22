"""Create-only atomic construction-evidence lifecycle."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Callable, Mapping
import zlib

from .contracts import canonical_json_bytes


class EvidenceLifecycleError(RuntimeError):
    pass


def _publish_no_overwrite(temp: Path, final: Path) -> None:
    if os.name == "nt":
        import ctypes
        kernel32=ctypes.WinDLL("kernel32",use_last_error=True)
        move=kernel32.MoveFileExW
        move.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32]
        move.restype=ctypes.c_int
        if not move(str(temp),str(final),0x8):  # MOVEFILE_WRITE_THROUGH, no replace
            error=ctypes.get_last_error()
            if final.exists():raise FileExistsError(str(final))
            raise OSError(error,"MoveFileExW create-only publication failed",str(final))
    else:
        os.link(temp,final)
        descriptor=os.open(final.parent,os.O_RDONLY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
        temp.unlink()


def write_once(
    path: Path,
    payload: bytes,
    *,
    failure_hook: Callable[[str],None] | None = None,
) -> str:
    """Fsync a hidden same-directory temp, then atomically publish without replace."""
    hook=failure_hook or (lambda _:None)
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,temp_name=tempfile.mkstemp(prefix=f".{path.name}.",suffix=".tmp",dir=path.parent)
    temp=Path(temp_name)
    try:
        with os.fdopen(descriptor,"wb") as stream:
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        hook("temp_fsynced")
        try:_publish_no_overwrite(temp,path)
        except FileExistsError as error:raise EvidenceLifecycleError(f"create-only path already exists: {path}") from error
        hook("published")
    finally:
        if temp.exists():temp.unlink()
    return hashlib.sha256(payload).hexdigest()


class ConstructionEvidence:
    """Atomic construction records; deliberately not an activity/result manifest."""
    def __init__(self,root:Path,*,failure_hook:Callable[[str],None]|None=None)->None:
        self.root=Path(root);self.failure_hook=failure_hook or (lambda _:None);self.records=[];self.sealed=False
        self.root.mkdir(parents=True,exist_ok=False)

    def add_record(self,name:str,value:Mapping[str,object],*,writer:str)->dict[str,object]:
        if self.sealed:raise EvidenceLifecycleError("sealed evidence cannot be changed")
        if not name or "/" in name or "\\" in name:raise ValueError("record name must be one path component")
        self.failure_hook(f"before:{name}");raw=canonical_json_bytes(value);compressed=zlib.compress(raw,level=9)
        path=self.root/f"{name}.json.zlib";compressed_sha=write_once(path,compressed,failure_hook=lambda phase:self.failure_hook(f"write_once:{phase}:{name}"));self.failure_hook(f"after:{name}")
        record={"name":name,"writer":writer,"path":path.name,"uncompressed_sha256":hashlib.sha256(raw).hexdigest(),"compressed_sha256":compressed_sha,"uncompressed_bytes":len(raw),"compressed_bytes":len(compressed)}
        self.records.append(record);return record

    def seal(self,dependencies:Mapping[str,str])->Path:
        if self.sealed:raise EvidenceLifecycleError("evidence already sealed")
        self.failure_hook("before:manifest")
        manifest={"schema":"VNFC-BPCR-R09-CONSTRUCTION-EVIDENCE-v1","activity":False,"result":False,"records":self.records,"dependencies":dict(sorted(dependencies.items()))}
        path=self.root/"manifest.json";write_once(path,canonical_json_bytes(manifest),failure_hook=lambda phase:self.failure_hook(f"write_once:{phase}:manifest"));self.sealed=True;self.failure_hook("after:manifest");return path
