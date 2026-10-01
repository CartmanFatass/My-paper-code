"""Content guard of both original transitive local kernel closures.

The versioned manifest includes package initializers and recursively resolved local
Python imports at each original commit. External library versions are separate
runtime evidence. No frozen code is rewritten or loaded from a scratch copy.
"""

import hashlib
import json
from pathlib import Path

from .config import SOURCES

ROOT = Path(__file__).resolve().parents[4]
MANIFEST = Path(__file__).with_name("source_manifest.json")


def verify_sources(root=ROOT, manifest_path=MANIFEST):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if set(manifest) != set(SOURCES):
        raise ValueError("source program set differs")
    for program, commit in SOURCES.items():
        closure = manifest[program]
        if closure["commit"] != commit or not closure["files"]:
            raise ValueError("original source binding differs")
        for relative, digest in closure["files"].items():
            path = Path(root) / relative
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ValueError("invalid source path")
            if path.is_symlink() or not path.is_file():
                raise ValueError("missing or aliased source: " + relative)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("inherited source drift: " + relative)
    return manifest
