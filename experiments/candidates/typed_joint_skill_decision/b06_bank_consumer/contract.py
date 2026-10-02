"""Effect-free consumer boundaries. A directory or mock is never certification."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from experiments.candidates.typed_joint_skill_decision.b04.contract import FITS, ARMS

SCIENCE_SHA = "b19508a5c2825359e66a36b4fdc1db68b60cc809"
SCIENCE_INPUT = "000588aa756405e25e9e3dbebec99b95927277b6a85ee38275947f322f4a12a3"
B05_INPUT = "dd2bf2e7f54b0070587529559a1963438fa62fb8fb9bfe7db46202932e303394"
DIRECTION = "typed_joint_skill_decision"
THREADS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")
SCIENCE_FILES = tuple("experiments/candidates/typed_joint_skill_decision/b04/" + name + ".py"
                      for name in ("__init__", "bank", "contract", "evidence", "functional", "model",
                                   "native", "online", "planner_reader", "reader", "run", "shortlist", "training"))


FROZEN_DIGESTS = {'experiments/candidates/typed_joint_skill_decision/b04/__init__.py': 'f160546e36507cbb6da4357825a99298431ec6b487248409380b63007a6599df', 'experiments/candidates/typed_joint_skill_decision/b04/bank.py': '45cd06e8538b011a62fcdcaca8cea8416fa4a06ef78435f0d7513214ed65b173', 'experiments/candidates/typed_joint_skill_decision/b04/contract.py': 'd555883a25030a6a1bcb89150b3823d0dc843d96f33085a6dba6329e364b5c7a', 'experiments/candidates/typed_joint_skill_decision/b04/evidence.py': '74c197cf2ab1db82e8899ba9ad4c7c04d0decc93476731eefb4161bc21f10583', 'experiments/candidates/typed_joint_skill_decision/b04/functional.py': 'ff2ae5d5f27260be266ac9959bd6180f892076b9ca7f9f74965df0d7af9803d1', 'experiments/candidates/typed_joint_skill_decision/b04/model.py': 'cf59f16f79f6cc7f37ba18936d89816f6eff90da61d291c63273f8601965f5ac', 'experiments/candidates/typed_joint_skill_decision/b04/native.py': '43c78e5f0da727e0e529ca0a9583352a9c98d63cfcd6ad01e7a62fd4f824e3f8', 'experiments/candidates/typed_joint_skill_decision/b04/online.py': '441ddbfb88a4a4c2d992ad4c99a7225dd52214876664c542e957fd94a5afb18e', 'experiments/candidates/typed_joint_skill_decision/b04/planner_reader.py': '0f20e3a98d908d72e6a2b2f509e5e151e030a40415e736205b43a54d876ce76b', 'experiments/candidates/typed_joint_skill_decision/b04/reader.py': '49ae4474572971bdbaeaecbcb8d2a2470178d8a0c7b1fd1e1678b0e91c7f9bcc', 'experiments/candidates/typed_joint_skill_decision/b04/run.py': 'dfb43f931798073f8af553b8d235ec428be0b0166a6901b3f5e3ea6fadabaae0', 'experiments/candidates/typed_joint_skill_decision/b04/shortlist.py': '0404065d3c7c3b454e9d157bf5cf3d80e80bee25db5f37ccb94982bb09e12f28', 'experiments/candidates/typed_joint_skill_decision/b04/training.py': 'dd59cdd48787ee3e9684b38735d2b4b11af8875996777ba94b0c87dbae46857b'}


class PendingCertification(RuntimeError):
    pass


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 ** 2), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(root, name):
    p = Path(name)
    if not isinstance(name, str) or not name or p.is_absolute() or ".." in p.parts or str(p) != name:
        raise ValueError("canonical contained relative artifact required")
    base = Path(root).resolve()
    current = Path(root).absolute()
    if current.is_symlink():
        raise ValueError("artifact root symlink refused")
    for part in p.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("artifact symlink alias refused")
    result = (base / p).resolve()
    if base not in result.parents:
        raise ValueError("artifact path escape")
    return result


def verify(root, name, entry):
    path = relative(root, name)
    if path.is_symlink() or path.stat().st_size != entry["bytes"] or sha(path) != entry["sha256"]:
        raise ValueError("immutable artifact changed: " + name)
    return path


def bound_json(path, digest):
    if sha(path) != digest:
        raise ValueError("input digest changed")
    return json.loads(Path(path).read_bytes())


@dataclass(frozen=True)
class CertifiedBank:
    # Internal handoff type for a future real validator, not a certificate schema.
    root: str
    files: dict
    producer_source_sha: str
    producer_input_sha256: str
    manifest_sha256: str
    prior_cost: dict
    certification: dict


def certify_bank(binding):
    """Pending real B05 config/summary/witness/258+258 reader/2501 compatibility binding.

    Intentionally no success branch and no injectable CLI validator. Do not turn arbitrary
    fields or the internal CertifiedBank test type into a production passing certificate.
    """
    if not isinstance(binding, dict) or binding.get("status") in (None, "pending", "partial", "unknown"):
        raise PendingCertification("B05 complete producer certification is missing/pending/partial/unknown")
    # Future narrow binding: published B05 read.read(root, actual_manifest_digest), then
    # require complete_compatible_bank and extract actual config.launch_sha/input_sha256.
    # That reader source publication + real digest + deployment are not yet supplied.
    raise PendingCertification("B05 read.read terminal interface has no bound published source/actual artifact digest")


def investment(value):
    if not isinstance(value, dict) or value.get("selected") is not True:
        raise PendingCertification("B06 result execution has not been selected")
    keys = {"cpu_seconds", "gpu_child_seconds", "wall_seconds", "disk_bytes"}
    if set(value.get("limits", {})) != keys:
        raise PendingCertification("explicit deployed CPU/GPU-child/wall/disk bounds required; no forecast defaults")
    limits = value["limits"]
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in limits.values()):
        raise ValueError("positive finite actual investment bounds required")
    if type(limits["disk_bytes"]) is not int:
        raise ValueError("integer disk bound required")
    return dict(limits)


def preparation_cost(value, source=None):
    """Explicit paid preparation and its selected CPU-cap scope; never default to zero."""
    required = {"known_cpu_seconds", "cpu_limit_scope", "evidence", "unmetered_support"}
    if not isinstance(value, dict) or set(value) != required:
        raise PendingCertification("actual preparation evidence/known CPU and chosen cap scope required")
    paid = value["known_cpu_seconds"]
    if type(paid) not in (int, float) or not math.isfinite(paid) or paid <= 0:
        raise ValueError("positive finite already-paid preparation CPU required")
    if value["cpu_limit_scope"] not in ("inside_consumer_cpu_limit", "separate_from_consumer_cpu_limit"):
        raise ValueError("explicit preparation-versus-deployment CPU cap scope required")
    if value["unmetered_support"] != "unknown_not_zero" or not isinstance(value["evidence"], list) or not value["evidence"]:
        raise ValueError("bound preparation evidence and honest unknown support required")
    for entry in value["evidence"]:
        if set(entry) != {"path", "sha256", "bytes"} or type(entry["bytes"]) is not int or entry["bytes"] < 0:
            raise ValueError("exact preparation artifact identity required")
        digest = entry["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(x not in "0123456789abcdef" for x in digest):
            raise ValueError("preparation artifact SHA256 required")
        relative(Path("/"), entry["path"])
        if source is not None:
            verify(source, entry["path"], entry)
    return value


def process_identity(pid):
    """Linux process identity for a child bound to its one actual parent."""
    if type(pid) is not int or pid <= 0:
        raise ValueError("positive actual parent PID required")
    fields = Path("/proc/" + str(pid) + "/stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "start_ticks": int(fields[19])}


def scientific_binding(binding, source):
    if binding["scientific_source_sha"] != SCIENCE_SHA or binding["scientific_input_sha256"] != SCIENCE_INPUT:
        raise ValueError("frozen B04 scientific identity changed")
    expected = binding["frozen_sources"]
    if expected != FROZEN_DIGESTS:
        raise ValueError("full B04 scientific source set required")
    for name, digest in expected.items():
        if sha(relative(source, name)) != digest:
            raise ValueError("frozen scientific source bytes changed: " + name)
    path = relative(source, "docs/research/candidates/typed_joint_skill_decision/B04_INPUT.json")
    original = bound_json(path, SCIENCE_INPUT)
    for name, digest in original["pinned_upstream_sources"].items():
        if sha(relative(source, name)) != digest:
            raise ValueError("frozen native upstream changed: " + name)
    return original


def guard_parent():
    forbidden = ("numpy", "torch", "envs", "jax", "cupy",
                 "experiments.candidates.typed_joint_skill_decision.b04.model",
                 "experiments.candidates.typed_joint_skill_decision.b04.reader",
                 "experiments.candidates.typed_joint_skill_decision.b04.functional")
    bad = [name for name in sys.modules if any(name == p or name.startswith(p + ".") for p in forbidden)]
    if bad:
        raise RuntimeError("stdlib parent imported scientific modules: " + ",".join(bad))


def threads():
    os.environ.update({key: "1" for key in THREADS})
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True


def jobs():
    for index, fit in enumerate(FITS):
        yield {"id": "fit-" + fit["id"], "stage": "fit", "fit": dict(fit), "engineering": index == 0, "gpu": True}
    yield {"id": "endpoint", "stage": "endpoint", "gpu": True}
    for offset, world in enumerate(range(109420000, 109420128)):
        order = list(ARMS)
        order = order[offset % 9:] + order[:offset % 9]
        for arm in order:
            yield {"id": str(world) + "-" + arm, "stage": "cold", "world": world, "arm": arm,
                   "gpu": arm not in ("Raw8J", "RawJ", "P")}
    yield {"id": "reader", "stage": "reader", "gpu": False}
