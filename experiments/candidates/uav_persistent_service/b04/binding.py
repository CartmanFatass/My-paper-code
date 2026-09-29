"""Read-only source and original B02 evidence binding for B04."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np


OLD_SOURCE = "e905d8842a6ad6006b2b6d82237e98f4a5dbb2d2"
R_SOURCE = "a4bd3b5eccef6e83a71c00fdbb8eccd6ecaf5c67"
ORIGINAL_ROOT = Path("/home/wu/projects/HMASD/runs/uav_persistent_service/b02_long_mission_a01")
ORIGINAL_MANIFEST_SHA256 = "5741dc165d5213345020f17378bc1088cf2efb6f7571731b071639eee5cd85d2"
HORIZON = 12000
SEEDS = tuple(range(52292801, 52292809))
OLD_ARMS = ("O_H", "P")
SOURCE_PREFIXES = (
    "configs", "hmasd", "envs", "ha_ctse_process",
    "experiments/candidates/energy_relay_availability",
    "experiments/candidates/energy_relay_benchmark",
    "experiments/candidates/uav_information_value",
    "experiments/candidates/uav_service_auxiliary",
)
OLD_ROOT_PATHS = tuple(
    f"experiments/candidates/uav_persistent_service/{name}.py"
    for name in ("constants", "controllers", "mechanisms", "policy", "readout")
)
R_PATHS = (
    "experiments/candidates/uav_persistent_service/macro_env.py",
    "experiments/candidates/uav_persistent_service/b03/__init__.py",
    "experiments/candidates/uav_persistent_service/b03/controller.py",
    "experiments/candidates/uav_persistent_service/b03/episode.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def git_tree(repo: Path, revision: str, paths: tuple[str, ...]) -> dict[str, str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", revision, "--", *paths],
        check=True, capture_output=True)
    found = {}
    for item in result.stdout.split(b"\0"):
        if not item:
            continue
        head, path = item.split(b"\t", 1)
        mode, kind, blob = head.decode("ascii").split()
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError(f"unexpected tracked source type: {path!r}")
        found[path.decode("utf-8")] = blob
    return found


def verify_blob_map(repo: Path, expected: dict[str, str]) -> dict:
    if not expected:
        raise ValueError("empty source binding")
    records = {}
    root = repo.resolve()
    for name, blob in sorted(expected.items()):
        path = root/name
        if (not path.is_file() or path.is_symlink()
                or not path.resolve().is_relative_to(root)):
            raise ValueError(f"source file missing or linked: {name}")
        actual = git_blob_id(path.read_bytes())
        if actual != blob:
            raise ValueError(f"source blob differs: {name}")
        records[name] = blob
    identity = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return {"file_count": len(records), "source_map_sha256": identity, "git_blobs": records}


def bind_source(repo: Path) -> dict:
    old = git_tree(repo, OLD_SOURCE, SOURCE_PREFIXES + OLD_ROOT_PATHS)
    retained = git_tree(repo, R_SOURCE, R_PATHS)
    if not old or set(retained) != set(R_PATHS) or not set(OLD_ROOT_PATHS) <= set(old):
        raise ValueError("source revision lacks a declared dependency path")
    overlap = set(old) & set(retained)
    if overlap:
        raise ValueError(f"duplicate source binding paths: {sorted(overlap)}")
    report = verify_blob_map(repo, old | retained)
    report.update(original_source=OLD_SOURCE, retained_r_source=R_SOURCE,
                  original_file_count=len(old), retained_file_count=len(retained))
    return report


def old_plan() -> list[dict]:
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in SEEDS for arm in OLD_ARMS]


def verified_path(root: Path, name: str, digest: str, size: int | None = None) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"invalid artifact path: {name}")
    path = root/name
    if (path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve())
            or (size is not None and path.stat().st_size != size)
            or sha256_file(path) != digest):
        raise ValueError(f"artifact missing or changed: {name}")
    return path


def verify_manifest(root: Path) -> tuple[dict, dict]:
    root = Path(root)
    manifest_path = root/"manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("original manifest missing or linked")
    if sha256_file(manifest_path) != ORIGINAL_MANIFEST_SHA256:
        raise ValueError("original manifest identity differs")
    manifest = json.loads(manifest_path.read_text())
    artifacts = manifest.get("artifacts")
    expected = {"config.json", "perworld.json", "summary.json"}
    for job in old_plan():
        stem = job["job_key"].replace("/", "_")
        expected.update({f"raw/{stem}.npz", f"raw/{stem}.decisions.json",
                         f"raw/{stem}.progress.json"})
    if not isinstance(artifacts, dict) or set(artifacts) != expected or len(artifacts) != 51:
        raise ValueError("original manifest has an incomplete or unexpected file set")
    for name, item in artifacts.items():
        if (not isinstance(item, dict) or not isinstance(item.get("sha256"), str)
                or not isinstance(item.get("bytes"), int)):
            raise ValueError(f"invalid original manifest entry: {name}")
        verified_path(root, name, item["sha256"], item["bytes"])
    if manifest.get("storage_bytes") != sum(item["bytes"] for item in artifacts.values()):
        raise ValueError("original manifest byte total differs")
    if manifest.get("launch_sha") != OLD_SOURCE:
        raise ValueError("original manifest source differs")
    return manifest, {"root": str(root), "manifest_sha256": ORIGINAL_MANIFEST_SHA256,
                      "verified_artifacts": len(artifacts),
                      "verified_bytes": sum(item["bytes"] for item in artifacts.values())}


def verify_old_config(config: dict, rows: list[dict], summary: dict) -> dict:
    if (config.get("launch_sha") != OLD_SOURCE
            or config.get("batch") != "b02_long_mission_a01"
            or config.get("direction") != "uav_persistent_service"
            or config.get("jobs") != old_plan()
            or config.get("arms") != list(OLD_ARMS)
            or config.get("seeds") != list(SEEDS)
            or config.get("horizon") != HORIZON
            or config.get("evaluation_workers") != 4
            or config.get("numeric_threads_per_worker") != 1
            or config.get("fits") != 0 or config.get("optimizer_updates") != 0
            or config.get("max_native_transitions") != 192000
            or config.get("mission_service_denominator") != HORIZON
            or config.get("late_window") != [6000, 12000]
            or config.get("fixed_bins") != 3000
            or config.get("final_reserve_window") != [11700, 12000]
            or config.get("shield") != {"enter_margin": 0.0, "exit_margin": 0.05}):
        raise ValueError("original fixed configuration differs")
    expected = {job["job_key"]: job for job in old_plan()}
    indexed = {row.get("job_key"): row for row in rows}
    if len(rows) != 16 or len(indexed) != 16 or set(indexed) != set(expected):
        raise ValueError("original control rows differ from fixed plan")
    effective = None
    for key, row in indexed.items():
        if (row.get("arm") != expected[key]["arm"] or row.get("seed") != expected[key]["seed"]
                or row.get("status") != "completed" or row.get("actual_length") != HORIZON):
            raise ValueError(f"original control identity incomplete: {key}")
        current = row.get("effective_config")
        if not isinstance(current, dict) or current.get("max_steps") != HORIZON or current.get("n_uavs") != 8 \
                or current.get("n_users") != 30 or current.get("n_charging_stations") != 2 \
                or current.get("charging_station_capacity") != [1, 1]:
            raise ValueError(f"original effective configuration differs: {key}")
        if effective is None:
            effective = current
        elif current != effective:
            raise ValueError(f"original effective configurations disagree: {key}")
    if (summary.get("status") != "complete" or summary.get("planned_jobs") != 16
            or summary.get("completed_jobs") != 16 or summary.get("launch_sha") != OLD_SOURCE
            or any(summary.get("pairing", {}).get(str(seed), {}).get("status") != "verified"
                   for seed in SEEDS)):
        raise ValueError("original summary does not certify all fixed controls")
    return effective


def verify_raw_identity(raw, row: dict) -> tuple[np.ndarray, np.ndarray]:
    length = int(row["actual_length"])
    users = raw["user_xy_m"]
    rng = raw["rng_state_sha256_by_step"]
    ends = raw["ends"]
    if (users.shape != (length+1, 30, 2) or not np.isfinite(users).all()
            or rng.shape != (length+1,) or rng.dtype.kind != "U"
            or not np.all(np.char.str_len(rng) == 64)
            or raw["reward"].shape != (length,)
            or ends.shape != (length, 2) or not ends[-1].any()):
        raise ValueError(f"raw exogenous or terminal structure differs: {row['job_key']}")
    return users.copy(), rng.copy()


def verify_old_pairs(root: Path, rows: list[dict], artifacts: dict) -> None:
    indexed = {row["job_key"]: row for row in rows}
    for seed in SEEDS:
        pair = {}
        for arm in OLD_ARMS:
            row = indexed[f"{arm}/{seed}"]
            stem = f"{arm}_{seed}"
            for field, name in (("raw", f"raw/{stem}.npz"),
                                ("decisions", f"raw/{stem}.decisions.json")):
                if (row.get(f"{field}_path") != name
                        or row.get(f"{field}_sha256") != artifacts[name]["sha256"]
                        or (field == "raw" and row.get("raw_bytes") != artifacts[name]["bytes"])):
                    raise ValueError(f"original row artifact identity differs: {arm}/{seed}")
            with np.load(root/row["raw_path"], allow_pickle=False) as raw:
                pair[arm] = verify_raw_identity(raw, row)
        left, right = (indexed[f"{arm}/{seed}"] for arm in OLD_ARMS)
        if (left.get("initial_state_sha256") != right.get("initial_state_sha256")
                or left.get("ground_bs_sha256") != right.get("ground_bs_sha256")
                or any(left.get(field) != right.get(field) for field in
                       ("user_xy_trace_sha256", "rng_state_stream_sha256"))
                or not np.array_equal(pair["O_H"][0], pair["P"][0])
                or not np.array_equal(pair["O_H"][1], pair["P"][1])):
            raise ValueError(f"original control exogenous pair differs: {seed}")


def bind_original(root: Path) -> dict:
    manifest, evidence = verify_manifest(root)
    config = json.loads((root/"config.json").read_text())
    rows = json.loads((root/"perworld.json").read_text())
    summary = json.loads((root/"summary.json").read_text())
    effective = verify_old_config(config, rows, summary)
    verify_old_pairs(root, rows, manifest["artifacts"])
    evidence.update(source_sha=OLD_SOURCE, effective_config=effective,
                    rows={row["job_key"]: row for row in rows},
                    artifacts=manifest["artifacts"])
    return evidence
