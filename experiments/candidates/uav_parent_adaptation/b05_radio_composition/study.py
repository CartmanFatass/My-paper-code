"""One fixed, admitted motion/radio composition panel with partial-work retention."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import make_bundle
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.study import load_asset
from .collection import collect_episode
from .contract import (ASSET, ASSET_ORIGIN_PATH, ASSET_PATH, FROZEN, OBJECT, PINS, WORKER_CPU_SECONDS,
                       CpuBudget, arm_parts, new_counts, source_identities, validate_counts)
from .reading import cost_totals, read_comparisons

ROOT = Path(__file__).resolve().parents[4]


def run_batch(out, launch_sha, *, protocol=FROZEN, asset_path=ASSET_PATH,
              admission=None, scientific_invocation=False, factory=None, fixture_binding=None,
              entry_wall=None, entry_cpu=None):
    protocol.validate()
    if factory is None:
        if (not scientific_invocation or not admission or admission.get("sha") != launch_sha
                or protocol != FROZEN or fixture_binding is not None or Path(asset_path) != ASSET_PATH):
            raise ValueError("native work requires the admitted fixed production contract")
        from experiments.candidates.uav_radio_activation.b01.study import factory
    elif scientific_invocation or protocol == FROZEN or fixture_binding is None:
        raise ValueError("injected fixtures must be nonproduction and explicitly bound")
    elif (Path(asset_path).resolve() == ASSET_PATH.resolve()
          or fixture_binding.get("sha256") == ASSET["sha256"]
          or fixture_binding.get("state_sha256") == ASSET["state_sha256"]):
        raise ValueError("a synthetic fixture must not load the production asset or its tensors")
    start_wall = time.perf_counter() if entry_wall is None else entry_wall
    start_cpu = time.process_time() if entry_cpu is None else entry_cpu
    budget = CpuBudget(WORKER_CPU_SECONDS, started=start_cpu)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(p.name not in allowed for p in out.iterdir()):
        raise FileExistsError("existing scientific output; no automatic repeat/resume")
    batch = dict(object=OBJECT, status="INCOMPLETE", launch_sha=launch_sha,
                 scientific_invocation=scientific_invocation, protocol=protocol.to_dict(), expected=protocol.expected(),
                 actual=new_counts(), rows=[], costs={}, admission=dict(admission or {}),
                 start_utc=datetime.now(timezone.utc).isoformat(),
                 environment=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                                  host=platform.node(), device="cpu", actor_dtype="float32", probability_dtype="float64",
                                  torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                                  thread_environment={n: os.environ.get(n) for n in
                                                      ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 worker_cpu_envelope_seconds=WORKER_CPU_SECONDS,
                 worker_timing_scope="entry through final summary preparation; imports when run.py is used, "
                 "binding/load, construction/resets, tapes, local/helper/coordinator queries, decoding, native "
                 "steps/mask refresh, diagnostics, compression and previous writes included; final self-write/close "
                 "and separately metered reader excluded; budget checked between bounded calls")
    env, inflight = None, {}

    def publish():
        batch["worker_wall_seconds"] = time.perf_counter() - start_wall
        batch["worker_cpu_seconds"] = time.process_time() - start_cpu
        batch["worker_process_peak_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(out / "summary.json", batch)

    try:
        budget.check()
        batch["source_sha256"] = source_identities(ROOT)
        actor, batch["asset"] = load_asset(asset_path, ASSET if scientific_invocation else fixture_binding)
        batch["asset"]["original_canonical_path"] = str(ASSET_ORIGIN_PATH) if scientific_invocation else None
        if not scientific_invocation:
            batch["asset"]["source_launch_sha"] = "synthetic-fixture"
        if scientific_invocation and (torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1):
            raise ValueError("production CPU thread contract changed")
        config = {k: batch[k] for k in ("object", "launch_sha", "scientific_invocation", "protocol", "expected",
                                       "source_sha256", "asset", "environment")}
        write_json(out / "config.json", config)
        (out / "raw").mkdir()
        publish()
        bundles = {(world, tape): make_bundle(world, tape, horizon=protocol.horizon,
                                             public_root=protocol.public_root, departure_root=protocol.departure_root,
                                             tail_root=protocol.tail_root)
                   for world in protocol.worlds for tape in protocol.tapes}
        batch["tape_provision"] = dict(unique_bundles=len(bundles),
                                       unique_bytes=sum(a.nbytes for b in bundles.values() for a in b.values()),
                                       unique_integers=sum(a.size for b in bundles.values() for a in b.values()),
                                       ranks=[0, 1, 2, 3, 4], online_payload_bytes=0, public_stream_used=False,
                                       future_entries_and_roots_are_policy_inputs=False)
        budget.check()
        inflight["phase"] = "constructor"
        batch["actual"]["constructor_calls"] += 1
        env = factory(protocol.worlds[0])
        batch["actual"]["constructors"] += 1
        batch["actual"]["constructor_resets"] += 1
        for index, (arm, world, tape) in enumerate(protocol.schedule()):
            budget.check()
            policy_sha = (batch["asset"]["state_sha256"] if arm_parts(arm)[0] == "S_I"
                          else PINS["experiments/candidates/uav_local_history/b01/controller.py"])
            row = collect_episode(env, arm=arm, world=world, tape=tape, bundle=bundles.get((world, tape)),
                                  out=out, protocol=protocol, counts=batch["actual"], actor=actor,
                                  policy_sha=policy_sha, inflight=inflight, check=budget.check)
            batch["rows"].append(row)
            batch["costs"] = cost_totals(batch["rows"])
            batch["progress"] = dict(completed=index + 1, total=batch["expected"]["complete_episodes"],
                                     arm=arm, world=world, tape=tape)
            publish()
            if (index + 1) % 16 == 0:
                print(batch["progress"], flush=True)
        budget.check()
        batch["asset_after_state_sha256"] = state_digest(actor.state_dict())
        if batch["asset_after_state_sha256"] != batch["asset"]["state_sha256"]:
            raise AssertionError("fixed learned asset changed")
        if any(file_identity(asset_path)[key] != batch["asset"][key] for key in ("sha256", "bytes")):
            raise AssertionError("asset file changed during the panel")
        if source_identities(ROOT) != batch["source_sha256"]:
            raise AssertionError("source changed during the panel")
        validate_counts(batch)
        batch["comparisons"] = read_comparisons(batch["rows"], protocol)
        batch["bulk"] = dict(canonical_root=str(out), raw_files=len(batch["rows"]),
                             raw_bytes=sum(r["raw"]["bytes"] for r in batch["rows"]),
                             identity_scope="per-file size/SHA256 in rows; one canonical evidence copy")
        budget.check()
        batch["status"] = "COMPLETE"
        publish()
        return batch
    except Exception:
        batch["status"] = "INCOMPLETE"
        batch["error"] = traceback.format_exc()
        batch["inflight"] = copy.deepcopy(inflight)
        batch["costs"] = cost_totals(batch["rows"])
        publish()
        raise
    finally:
        if env is not None and hasattr(env, "close"):
            env.close()
