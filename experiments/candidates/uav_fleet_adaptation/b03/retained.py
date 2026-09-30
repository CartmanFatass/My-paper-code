"""Read-only, source-bound reuse of B02's already-paid ordinary controls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import platform

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import contract as original
from experiments.candidates.uav_fleet_adaptation.b02.read import identity
from experiments.candidates.uav_fleet_adaptation.b02.study import validate_counts

BINDING = {
    "launch_sha": "e945483b85c7f8ddfc315c57f36938d6c14201c7",
    "files": {
        "summary.json": {"bytes": 1615407, "sha256": "2e9e5d83f6b7d1cdff0a947a361fe1e1493046cd7c8b25aee068ed9eb7fc6e8c"},
        "reading.json": {"bytes": 265626, "sha256": "a3f76992ccb01aa90138eec2272dc2667b7283d32e86742e87bf77e43bd613e9"},
        "config.json": {"bytes": 8685, "sha256": "821ba7697c3f184dfbe6d4337bd8b8ad396193bf83db34dc7e22b9c7404dd733"},
        "launch-manifest.json": {"bytes": 3840, "sha256": "73403021d3b71abf66c6d8f0b3a33bce627d56949d1fdf8f6e5d806bb95ef0a1"},
        "process-exit.json": {"bytes": 556, "sha256": "95b5e1918dce9dd122d985e60983763381f52b6cc3ce18b3db862bb29f60d1fc"},
    },
}
CONTROLS = ("C_memo", "C7_memo")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _runtime():
    return dict(python=platform.python_version(), numpy=np.__version__, torch=str(torch.__version__),
                device="cpu", dtype="float32", host=platform.node(),
                torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                thread_environment={name: os.environ.get(name) for name in
                                    ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})


def _protocol(value):
    fields = deepcopy(value)
    fields["training_worlds"] = tuple(tuple(phase) for phase in fields["training_worlds"])
    fields["evaluation_worlds"] = tuple(fields["evaluation_worlds"])
    fields["epochs"] = tuple(fields["epochs"])
    return original.Protocol(**fields).validate()


def _check_protocol(old, new):
    before, after = old.to_dict(), new.to_dict()
    exceptions = {"training_worlds", "init_seed", "shuffle_root"}
    _require(set(before) == set(after), "protocol fields changed")
    _require(all(before[key] == after[key] for key in before if key not in exceptions),
             "retained protocol recipe/evaluation/sampling changed")
    _require(tuple(map(len, old.training_worlds)) == tuple(map(len, new.training_worlds)),
             "training recipe phase sizes changed")
    old_worlds = {w for phase in old.training_worlds for w in phase} | set(old.evaluation_worlds)
    new_worlds = {w for phase in new.training_worlds for w in phase}
    _require(not old_worlds.intersection(new_worlds), "new training worlds reuse original training/evaluation identities")
    old_roots = {old.init_seed, old.shuffle_root, old.sampling_root}
    _require(new.init_seed not in old_roots and new.shuffle_root not in old_roots,
             "new initialization/shuffle roots reuse original randomness identities")


def _check_acceptance(batch, manifest, exit_record, binding, root, production):
    admission = batch["admission"]
    sha = binding["launch_sha"]
    _require(manifest["acceptance"] == "accepted" and manifest["schema_version"] == 1
             and manifest["sha"] == sha and manifest["direction"] == "uav_fleet_adaptation",
             "original manifest is not the accepted source/direction")
    _require(admission["sha"] == sha and admission["direction"] == manifest["direction"]
             and admission["schema_version"] == 1
             and admission["command_sha256"] == manifest["command_sha256"],
             "original admission/source/command binding differs")
    _require(manifest["host_identity"] == batch["environment"]["host"], "original accepted host differs")
    _require(manifest["process"]["pid"] == admission["parent_pid"]
             and manifest["runner_process"]["pid"] == admission["child_pid"],
             "original admitted process identities differ")
    _require(exit_record["status"] == "exited" and exit_record["termination"] == "process_exit"
             and type(exit_record["exit_code"]) is int and exit_record["exit_code"] == 0
             and exit_record["schema_version"] == 1 and exit_record["pid"] == admission["child_pid"]
             and exit_record["process_identity"] == manifest["runner_process"]["identity"]
             and exit_record["supervisor_identity"] == manifest["process"]["identity"],
             "original worker lacks its matching zero process exit")
    if production:
        _require(manifest["node"] == "wsl_4070" and Path(manifest["output_root"]).resolve() == root,
                 "production retained controls require the canonical original node/output")


def load_retained(root, protocol, *, repo, permit_fixture=False, binding=None):
    """Validate metadata and all control raw bytes, without loading/replaying arrays.

    Fixture overrides accept only an explicitly nonscientific, nonproduction
    lineage. Production hashes and all15 unchanged source identities are binding.
    Returned rows are unmodified original dictionaries, in their recorded order.
    """
    root, repo = Path(root).resolve(), Path(repo).resolve()
    chosen = deepcopy(BINDING if binding is None else binding)
    production = chosen == BINDING
    if not production:
        _require(permit_fixture is True and chosen.get("launch_sha") != BINDING["launch_sha"],
                 "production binding override forbidden; synthetic fixtures require explicit permission")
    _require(set(chosen) == {"launch_sha", "files"} and set(chosen["files"]) == set(BINDING["files"]),
             "retained metadata binding schema differs")
    documents = {}
    for name, record in chosen["files"].items():
        path = identity(root, {**record, "path": name})
        documents[name] = json.loads(path.read_text())
    batch, reading, config = (documents[name] for name in ("summary.json", "reading.json", "config.json"))
    manifest, exit_record = documents["launch-manifest.json"], documents["process-exit.json"]
    old = _protocol(batch["protocol"])
    new = _protocol(protocol.to_dict())
    if production:
        _require(old == original.FROZEN and batch["scientific_invocation"] is True,
                 "production retained source is not the original scientific FROZEN protocol")
    else:
        _require(batch["scientific_invocation"] is False and old != original.FROZEN and new != original.FROZEN,
                 "fixture override cannot reuse production/scientific inputs")
    _check_protocol(old, new)
    _require(batch["status"] == "COMPLETE" and reading["status"] == "VERIFIED",
             "original worker/reader is incomplete or unverified")
    _require(batch["object"] == reading["object"] == "UAV-LOCAL-C-INHERITANCE-B02"
             and batch["launch_sha"] == reading["launch_sha"] == chosen["launch_sha"],
             "original result object/source identity differs")
    expected_config = {key: batch[key] for key in (
        "object", "launch_sha", "scientific_invocation", "protocol", "expected", "source_sha256", "environment")}
    _require(config == expected_config, "original config and summary binding differs")
    current_sources = original.source_identities(repo)
    _require(len(current_sources) == 15 and batch["source_sha256"] == current_sources,
             "original source identities changed or inventory differs")
    _require(batch["environment"] == _runtime(), "runtime/host/thread settings differ from original controls")
    _check_acceptance(batch, manifest, exit_record, chosen, root, production)
    summary_binding = chosen["files"]["summary.json"]
    _require(all(reading["summary"][key] == summary_binding[key] for key in ("bytes", "sha256"))
             and Path(reading["summary"]["path"]) == Path(manifest["output_root"]) / "summary.json",
             "original reader summary hash/path binding differs")
    _require(batch["expected"] == old.expected() and reading["expected"] == batch["expected"]
             and reading["actual"] == batch["actual"], "original reader count binding differs")
    validate_counts(batch)
    _require(reading["assets"] == batch["assets"] and reading["reading"] == batch["reading"]
             and reading["costs"] == batch["costs"], "original reader assets/reductions/costs differ")
    all_rows = batch["rows"]
    _require(len(all_rows) == old.expected()["complete_episodes"]
             and reading["raw_files"] == len(all_rows)
             and reading["raw_bytes"] == sum(row["raw"]["bytes"] for row in all_rows)
             and reading["native_ticks_verified"] == batch["actual"]["native_steps"]
             and reading["decisions_verified"] == (old.expected()["expert_label_requests"]
                                                    + old.expected()["evaluation_native_steps"] // old.period * old.n_agents)
             and reading["reader_calls"] == dict(native=0, expert_queries=0, radio_power_model=0, actor_forward=0, optimizer=0),
             "original reader coverage/call count binding differs")
    controls = [row for row in all_rows if row["arm"] in CONTROLS]
    expected_controls = {(arm, world) for world in old.evaluation_worlds for arm in CONTROLS}
    _require(len(controls) == len(expected_controls)
             and {(row["arm"], row["world"]) for row in controls} == expected_controls,
             "duplicate/missing/wrong retained control arms or worlds")
    verified = reading["per_row"]
    _require(len(verified) == len(all_rows), "original reader row coverage differs")
    reader_index = {(row["arm"], row["world"], row["kind"]): row for row in verified}
    _require(len(reader_index) == len(verified), "duplicate original reader row identity")
    raw_paths, total_bytes = set(), 0
    controller_sha = current_sources["experiments/candidates/uav_fleet_adaptation/b02/controllers.py"]
    for row in controls:
        _require(row["kind"] == "evaluation" and row["phase"] is None and row["steps"] == old.horizon
                 and row["policy_sha256"] == controller_sha, "retained control row policy/episode identity differs")
        proof = reader_index.get((row["arm"], row["world"], row["kind"]))
        _require(proof is not None and proof["verified"] is True and proof["raw_sha256"] == row["raw"]["sha256"],
                 "retained control row lacks matching original reader verification")
        path = identity(root, row["raw"])
        _require(path not in raw_paths, "retained controls reuse a raw path")
        raw_paths.add(path)
        total_bytes += row["raw"]["bytes"]
    return dict(root=str(root), binding=chosen, original_protocol=deepcopy(batch["protocol"]),
                rows=controls, old_reading=batch["reading"], old_assets=batch["assets"],
                source_sha256=current_sources, environment=deepcopy(batch["environment"]),
                raw_verification=dict(files=len(controls), bytes=total_bytes))
