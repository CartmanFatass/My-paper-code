"""Exclusive local stores and sole-parent immutable manifest aggregation."""
from __future__ import annotations
import gzip
import os
from pathlib import Path
from experiments.candidates.typed_joint_skill_decision.b04 import evidence as old
from . import contract as c


def durable(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def allowed(job, name):
    stage = job["stage"]
    if name.startswith("children/" + job["id"] + "/"):
        return True
    if stage == "fit":
        fit = job["fit"]
        return (name.startswith("raw/fit/" + fit["id"] + "/")
                or name.startswith("raw/endpoints/" + fit["id"] + "/train.")
                or name == "endpoints/" + fit["id"] + "/train-summary.json"
                or name == "assets/" + fit["id"] + ".json"
                or (job.get("new_stream", False) and name == "raw/initial/stream" + str(fit["stream"]) + ".pt")
                or (job["engineering"] and name == "raw/engineering/scorers.json.gz"))
    if stage == "endpoint":
        return (name.startswith("commitments/")
                or any(name == "raw/endpoints/" + fit["id"] + "/fresh.npz"
                       or name == "endpoints/" + fit["id"] + "/fresh-summary.json" for fit in c.FITS))
    if stage == "cold":
        return (name.startswith("raw/main/" + str(job["world"]) + "/" + job["arm"] + "/")
                and not name.endswith(("/decision.json", "/matched-endpoint.json")))
    if stage == "reader":
        return name.startswith(("raw/reader/", "raw/native-reader/", "raw/audit/", "raw/functional/", "reading/"))
    return False


class ChildStore(old.Store):
    # Keep original exclusive serializers; only replace unsafe whole-root initialization/register.
    def __init__(self, root, bill, job, inherited=None):
        self.root, self.bill, self.job = Path(root), bill, dict(job)
        self.files = dict(inherited or {})
        self.local = {}

    def writable(self, relative):
        c.relative(self.root, relative)
        if not allowed(self.job, relative) or relative in self.files:
            raise ValueError("child refused write ownership: " + relative)

    def write(self, relative, value):
        self.writable(relative)
        return super().write(relative, value)

    def write_gzip(self, relative, value):
        self.writable(relative)
        return super().write_gzip(relative, value)

    def register(self, relative, **metadata):
        c.relative(self.root, relative)
        if not allowed(self.job, relative) or relative in self.files and relative not in self.local:
            raise ValueError("child output ownership/refused overwrite: " + relative)
        path = c.relative(self.root, relative)
        value = {"sha256": c.sha(path), "bytes": path.stat().st_size, **metadata}
        if relative in self.local and self.local[relative] != value:
            raise ValueError("registered immutable child artifact changed: " + relative)
        self.local[relative] = value
        self.files[relative] = value

    def progress(self, phase, **fields):
        # Per-child progress is append-only; no root progress/manifest overwrite.
        self.bill.check()

    def finish(self):
        name = "children/" + self.job["id"] + "/artifacts.json"
        durable(c.relative(self.root, name), c.encoded({"schema": 1, "job": self.job, "files": self.local}))
        return name


class ParentStore:
    def __init__(self, root):
        self.root, self.files = Path(root), {}
        self.root.mkdir(parents=True, exist_ok=True)
        unknown = [p.name for p in self.root.iterdir() if p.name not in old.LAUNCH_FILES
                   and not p.name.startswith(".hmasd-launch-")]
        if unknown:
            raise ValueError("no retry/resume or preexisting consumer evidence: " + str(unknown))

    def write(self, name, value):
        durable(c.relative(self.root, name), c.encoded(value))
        self.register(name)

    def gzip(self, name, value):
        durable(c.relative(self.root, name), gzip.compress(c.encoded(value), compresslevel=1, mtime=0))
        self.register(name)

    def register(self, name, **metadata):
        if name in self.files:
            raise ValueError("parent refused duplicate ownership: " + name)
        path = c.relative(self.root, name)
        self.files[name] = {"sha256": c.sha(path), "bytes": path.stat().st_size, **metadata}

    def merge(self, job, manifest):
        if manifest["job"] != job or manifest["schema"] != 1:
            raise ValueError("child manifest identity mismatch")
        checked = {}
        for name, value in manifest["files"].items():
            if name in self.files or not allowed(job, name):
                raise ValueError("child merge refused overwrite/ownership: " + name)
            c.verify(self.root, name, value)
            checked[name] = value
        self.files.update(checked)

    def check(self, name, digest=None):
        path = c.verify(self.root, name, self.files[name])
        if digest is not None and self.files[name]["sha256"] != digest:
            raise ValueError("artifact digest mismatch: " + name)
        return path

    def load(self, name):
        import json
        return json.loads(self.check(name).read_bytes())

    def selection(self, name, digest):
        return c.bound_json(c.relative(self.root, name), digest)

    def seal(self, name="artifact-manifest.json"):
        # Immutable snapshots instead of repeatedly overwriting the sole root manifest.
        for relative, value in self.files.items():
            c.verify(self.root, relative, value)
        self.write(name, {"schema": 1, "files": dict(self.files)})
        return self.files[name]["sha256"]

    def failure_prefix(self, job):
        # Preserve actual bytes, including incomplete gz streams; never parse/recompute science.
        roots = [self.root / "children" / job["id"]]
        if job["stage"] == "cold":
            roots.append(self.root / "raw/main" / str(job["world"]) / job["arm"])
        elif job["stage"] == "fit":
            roots.extend((self.root / "raw/fit" / job["fit"]["id"],
                          self.root / "raw/endpoints" / job["fit"]["id"],
                          self.root / "endpoints" / job["fit"]["id"],
                          self.root / "assets" / (job["fit"]["id"] + ".json")))
            if job.get("new_stream"):
                roots.append(self.root / "raw/initial" / ("stream" + str(job["fit"]["stream"]) + ".pt"))
            if job.get("engineering"):
                roots.append(self.root / "raw/engineering")
        elif job["stage"] == "endpoint":
            roots.append(self.root / "commitments")
            for fit in c.FITS:
                roots.extend((self.root / "raw/endpoints" / fit["id"], self.root / "endpoints" / fit["id"]))
        elif job["stage"] == "reader":
            roots.extend(self.root / name for name in ("raw/reader", "raw/native-reader", "raw/audit", "raw/functional", "reading"))
        for root in roots:
            for path in ([root] if root.is_file() else root.rglob("*") if root.exists() else []):
                if path.is_file():
                    name = str(path.relative_to(self.root))
                    if name not in self.files and allowed(job, name):
                        self.register(name, failed_prefix=True)
