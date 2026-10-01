"""Admitted, fixed B01 native collector; no native import/effect at module import.

Run as this explicit file with --seed 0 --launch-sha SHA --out-dir PATH
--budget-ledger JSON --asset-manifest JSON. Science is not configurable. DM owns
codec.py: its mandatory validator runs on every prepared world before any labels.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from typing import Any

# Support the direct-file invocation used by hmasd_launch (and ordinary -m import).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from experiments.candidates.typed_joint_skill_decision import contract as c
from experiments.candidates.typed_joint_skill_decision.data import Bill, Store, Trace, hash_file


def builtin(value):
    """Native NumPy scalar/array payload -> finite lossless JSON values."""
    if isinstance(value, dict):
        return {str(k): builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [builtin(v) for v in value]
    if hasattr(value, "tolist"):
        return builtin(value.tolist())
    return value


def rng_identity(env):
    return builtin(env.np_random.get_state())


def rng_key(env):
    state = env.np_random.get_state()
    return (state[0], state[1].tobytes(), *state[2:])


def reset_identity(env):
    # Native reset methods own cache rebuilding and all mutable state, including RNG.
    # Preserve the consequential reset fields, not stale pre-reset reward_info diagnostics.
    fields = ("uav_positions", "user_positions", "ground_bs_positions", "connections",
              "sinr_matrix", "uav_connections", "uav_bs_connections", "routing_paths",
              "uav_sinr_matrix", "current_step", "agents", "_transmitter_mask",
              "action_clip_events_episode", "channel_backend", "_path_loss_cache_context",
              "_path_loss_cache_hits", "_path_loss_cache_misses")
    return {"fields": {key: builtin(getattr(env, key)) for key in fields},
            "native_rng_state": rng_identity(env)}


class NativeRuntime:
    """Process-local instrumentation of pinned imports, never substitute native science.

    The original executor owns reset, live feedback, termination and assignment latch.
    Wrappers count and stream each call, then restore every module/class attribute.
    Tests can inject pure modules/hosts without importing the native environment.
    """
    def __init__(self, store: Store, host, planner, menus):
        self.store, self.bill = store, store.bill
        self.host, self.planner, self.menus = host, planner, menus
        self.active_trace = None
        self.expected_reset = None
        self.timings = {}

    @contextmanager
    def instrument(self):
        originals = []
        def patch(obj, name, replacement):
            originals.append((obj, name, getattr(obj, name)))
            setattr(obj, name, replacement)
        def counted(name, function, extra=None):
            def wrapper(*args, **kwargs):
                self.bill.enter(name + "_calls")
                started = time.perf_counter()
                try:
                    result = function(*args, **kwargs)
                    self.bill.complete({"host_construction": "hosts_constructed", "reset": "resets_completed",
                                        "candidate_build": "candidate_builds_completed", "matching": "matchings_completed",
                                        "static_evaluation": "static_evaluations_completed"}[name])
                    if extra:
                        extra(args, result)
                    return result
                finally:
                    self.timings[name + "_wall_seconds"] = self.timings.get(name + "_wall_seconds", 0) + time.perf_counter() - started
            return wrapper
        original_reset = self.host.CoupledRelayHost.reset
        original_step = self.host.CoupledRelayHost.step
        def after_reset(args, result):
            env = args[0]
            if self.active_trace is not None:
                identity = reset_identity(env)
                self.active_trace.write({"kind": "reset", "identity": identity})
                if identity != self.expected_reset:
                    raise AssertionError("executor reset identity differs from saved preparation")
        def step(env, actions):
            self.bill.enter("native_step_calls")
            started = time.perf_counter()
            rng = rng_key(env)
            if self.active_trace is not None:
                self.active_trace.write({"kind": "step_request", "step": int(env.current_step),
                                         "positions_xyz": builtin(env.uav_positions),
                                         "actions": [builtin(actions[a]) for a in env.agents]})
            try:
                result = original_step(env, actions)
                self.bill.complete("native_steps_completed")
                if self.active_trace is not None:
                    self.active_trace.write({"kind": "step", "step": int(env.current_step),
                        "positions_xyz": builtin(env.uav_positions), "reward_info": builtin(env.reward_info),
                        "rewards": builtin(result[1]), "terminations": builtin(result[2]),
                        "truncations": builtin(result[3]),
                        "user_association": builtin(self.planner.user_association(env)),
                        "backhauled_users_mask": builtin(self.planner.backhauled_users_mask(env)),
                        "routing_paths": builtin(env.routing_paths)})
                if rng_key(env) != rng:
                    raise AssertionError("after-reset native exogenous RNG draw contradicts frozen contract")
                return result
            finally:
                self.timings["native_step_wall_seconds"] = self.timings.get("native_step_wall_seconds", 0) + time.perf_counter() - started
        original_static = self.host.static_evaluate
        def static(*args, **kwargs):
            env = args[0]
            before = rng_key(env)
            result = original_static(*args, **kwargs)
            if rng_key(env) != before:
                raise AssertionError("static evaluator consumed native RNG")
            return result
        try:
            patch(self.host.CoupledRelayHost, "reset", counted("reset", original_reset, after_reset))
            patch(self.host.CoupledRelayHost, "step", step)
            patch(self.host, "make_host", counted("host_construction", self.host.make_host))
            static_wrapper = counted("static_evaluation", static)
            patch(self.host, "static_evaluate", static_wrapper)
            # planner imports the alias at module load; menus imports host functions per call.
            patch(self.planner, "static_evaluate", static_wrapper)
            patch(self.planner, "assign_targets", counted("matching", self.planner.assign_targets))
            patch(self.planner, "build_candidates", counted("candidate_build", self.planner.build_candidates))
            yield self
        finally:
            for obj, name, original in reversed(originals):
                setattr(obj, name, original)

    def prepare_world(self, address):
        """Outcome-free native reset -> shadow constructor -> canonical assigned plans."""
        import numpy as np
        env = self.host.make_host(address["world"], area_size=c.AREA)
        # scenario2.__init__ replaces routing/link arrays after its constructor reset;
        # the episode baseline is the full native explicit reset, not that transient state.
        env.reset(seed=address["world"])
        identity = reset_identity(env)
        started = time.perf_counter()
        shadow = copy.deepcopy(env)
        rng = np.random.Generator(np.random.PCG64(0))
        before_rng = builtin(rng.bit_generator.state)
        report = {}
        raw = self.planner.build_candidates(shadow, rng, allow_a2a=True, report=report)
        menu, selection = c.select_menu(raw)
        construction_seconds = time.perf_counter() - started
        matching_started = time.perf_counter()
        initial = np.asarray(env.uav_positions, dtype=float)
        for plan in menu:
            targets = np.asarray(plan["positions_xyz"], dtype=float)
            perm = self.planner.assign_targets(initial, targets)
            plan["target_permutation"] = perm.tolist()
            plan["assigned_targets_xyz"] = targets[perm].tolist()
            distances = np.linalg.norm(initial - targets[perm], axis=1)
            plan["max_travel_distance_m"] = float(distances.max())
            plan["total_travel_distance_m"] = float(distances.sum())
        if reset_identity(env) != identity:
            raise AssertionError("shadow construction mutated the live reset branch")
        features = c.make_features(initial, env.user_positions[:, :2], env.ground_bs_positions[0], menu)
        return {"schema": c.SCHEMA, "address": address, "features": features,
                "feature_sha256": c.digest(features), "reset_identity": identity,
                "menu_provenance": menu, "source_generator_report": builtin(report),
                "selection_report": selection,
                "constructor_rng": {"initial": before_rng, "final": builtin(rng.bit_generator.state)},
                "construction_and_shadow_wall_seconds": construction_seconds,
                "matching_wall_seconds": time.perf_counter() - matching_started}

    def execute(self, env, assigned, expected_reset, relative, episode_kind, *, compare=None):
        """One exact identity-assigned source executor episode, partial trace on errors."""
        self.bill.enter(episode_kind + "_episode_calls")
        trace = Trace(self.store, relative, {"kind": "assigned_targets", "assigned_targets_xyz": assigned})
        self.active_trace, self.expected_reset = trace, expected_reset
        status = "partial"
        try:
            result = self.planner.closed_loop_execute(env, assigned, max_steps=c.HORIZON,
                                                     allow_a2a=True, assignment="identity")
            if result["steps"] != c.HORIZON or trace.steps != c.HORIZON:
                raise AssertionError("native episode terminated before full H500")
            if result["target_permutation"] != list(range(6)) or result["targets_xyz"] != assigned:
                raise AssertionError("native executor target identity changed")
            if result["initial_positions_xyz"] != expected_reset["fields"]["uav_positions"]:
                raise AssertionError("native initial positions changed")
            if result["final_max_distance_to_target_m"] > self.planner.ARRIVAL_TOL_M:
                raise AssertionError("executor failed to land and hold at assigned targets")
            # Every native series is streamed; scalar result records carry no duplicate bulk.
            compact = {key: builtin(value) for key, value in result.items()
                       if key not in ("series", "association_changes_per_step", "backhaul_losses_per_step")}
            compact["Q"] = float(result["coverage_backhauled_mean_all"])
            if compare is not None:
                if trace.logical.hexdigest() != compare["logical_sha256"] or c.digest(compact) != compare["result_sha256"]:
                    # Reconstructing comparison from the paid original stream provides the
                    # concrete mismatch; it does not rerun any native transition.
                    raise AssertionError("reversed-order audit changed full native trace/result")
                status = "identical_audit"
            else:
                status = "complete"
            self.bill.complete(episode_kind + "_episodes_completed")
            return compact, trace.logical.hexdigest()
        finally:
            self.active_trace, self.expected_reset = None, None
            record = trace.close(status)
            if status == "identical_audit":
                # Retain exactly one necessary native evidence copy. The append-only
                # manifest explicitly marks the deleted byte object as an alias.
                trace.path.unlink()
                self.bill.observe_file(trace.path)
                self.store.append_manifest({"kind": "audit_trace_alias", "discarded_path": record["path"],
                    "retained_path": compare["path"], "sha256": record["sha256"],
                    "logical_sha256": record["logical_sha256"], "reason": "full paid repeat exactly equal"})
            self.store.status("collecting")

    def collect_world(self, prepared):
        import numpy as np
        address = prepared["address"]
        prefix = f"worlds/b{address['block']}/{address['split']}/{address['world']}"
        self.store.current = {**address, "phase": "labels"}
        env = self.host.make_host(address["world"], area_size=c.AREA)
        env.reset(seed=address["world"])
        if reset_identity(env) != prepared["reset_identity"]:
            raise AssertionError("label branch differs from prepared full reset identity")
        features = prepared["features"]
        if c.digest(features) != prepared["feature_sha256"]:
            raise AssertionError("prepared feature bytes changed")
        c.validate_features(features)
        plans = prepared["menu_provenance"]
        by_slot = {p["construction_slot"]: p for p in features["plans"]}
        for plan in plans:
            if plan["assigned_targets_xyz"] != by_slot[plan["construction_slot"]]["assigned_targets_xyz"]:
                raise AssertionError("provenance/feature target mismatch")
        static_started = time.perf_counter()
        static_before = self.timings.get("static_evaluation_wall_seconds",0)
        static_shadow = copy.deepcopy(env)
        initial_info = self.host.static_evaluate(static_shadow, env.uav_positions.copy(), allow_a2a=True)
        static_initial = float(initial_info["coverage_backhauled"])
        static = {}
        for plan in plans:
            slot = plan["construction_slot"]
            info = self.host.static_evaluate(static_shadow, plan["assigned_targets_xyz"], allow_a2a=True)
            static[slot] = {"coverage_backhauled": float(info["coverage_backhauled"]),
                            "native_static_info": builtin(info)}
        static_package_seconds = time.perf_counter()-static_started
        static_query_seconds = self.timings.get("static_evaluation_wall_seconds",0)-static_before
        results, traces = {}, {}
        for plan in plans:
            slot = plan["construction_slot"]
            self.store.current = {**address, "phase": "candidate", "construction_slot": slot}
            relative = f"raw/b{address['block']}/{address['split']}/{address['world']}/slot{slot}.jsonl.gz"
            result, logical = self.execute(env, plan["assigned_targets_xyz"], prepared["reset_identity"],
                                           relative, "candidate")
            results[slot] = result
            traces[slot] = {"path": relative, "logical_sha256": logical, "result_sha256": c.digest(result)}
            self.store.write_json(f"{prefix}/slot{slot}.json", {"result": result, "trace": traces[slot]}, kind="native_candidate", **address)
        audit = []
        if address["world"] in (c.BASES[0], c.BASES[0] + 1):
            for plan in reversed(plans):
                slot = plan["construction_slot"]
                self.store.current = {**address, "phase": "correctness", "construction_slot": slot}
                relative = f"raw/audit/{address['world']}/slot{slot}.jsonl.gz"
                result, logical = self.execute(env, plan["assigned_targets_xyz"], prepared["reset_identity"],
                                               relative, "correctness", compare=traces[slot])
                audit.append({"construction_slot": slot, "identical": True,
                              "logical_sha256": logical, "retained_trace": traces[slot]["path"]})
        slots = [plan["construction_slot"] for plan in plans]
        q = [results[slot]["Q"] for slot in slots]
        rank_started = time.perf_counter()
        ordinary = c.ordinary_choices(plans, {slot: static[slot]["coverage_backhauled"] for slot in slots}, static_initial)
        rank_seconds = time.perf_counter()-rank_started
        output = {"schema": c.SCHEMA, "address": address, "feature_sha256": prepared["feature_sha256"],
                  "slot_order": slots, "Q": q, "soft_targets": c.soft_targets(q),
                  "candidate_results": results, "traces": traces,
                  "ordinary": {"initial_native_static_info": builtin(initial_info), "static_by_slot": static,
                               "selected_slots": ordinary,
                               "ordinary_static_package_wall_seconds":static_package_seconds,
                               "ordinary_static_query_wall_seconds":static_query_seconds,
                               "ordinary_ranking_wall_seconds":rank_seconds,
                               "fixed_policy_executed_slots": {str(s): c.fallback_slot(s, slots) for s in range(8)}},
                  "correctness_audit": audit}
        if address["split"] == "test":
            self.store.current = {**address, "phase": "full_planner"}
            self.bill.enter("planner_menu_calls")
            before = self.bill.delta["static_evaluation_calls"]
            started = time.perf_counter()
            menu = self.menus.compute_menu(address["world"], area_size=c.AREA, budget=3000)
            self.bill.complete("planner_menus_completed")
            calls = self.bill.delta["static_evaluation_calls"] - before
            if calls != sum(menu["static"]["evaluations"]) + 1 or calls > 6001:
                raise AssertionError("compute_menu static count disagrees with paid searches + metadata query")
            if menu["initial_positions_xyz"] != prepared["reset_identity"]["fields"]["uav_positions"]:
                raise AssertionError("full planner reset identity differs")
            planner_seconds = time.perf_counter() - started
            # compute_menu already assigned the returned relay; do not match a second time.
            assigned = np.asarray(menu["positions_xyz"], dtype=float)[menu["m_permutation"]].tolist()
            result, logical = self.execute(env, assigned, prepared["reset_identity"],
                f"raw/b{address['block']}/test/{address['world']}/full_planner.jsonl.gz", "planner")
            output["full_planner"] = {"menu": menu, "result": result, "logical_sha256": logical,
                                      "static_evaluation_calls": calls, "compute_menu_wall_seconds": planner_seconds}
        self.store.write_json(f"{prefix}/labels.json", output, kind="world_labels", **address)
        self.bill.complete("worlds_completed")
        self.store.status("collecting")


def verify_sources(root: Path):
    for relative, expected in c.SOURCE_SHA256.items():
        if hash_file(root / relative) != expected:
            raise ValueError(f"pinned native source drift: {relative}")


def load_bound_json(path: Path, expected_sha256: str):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError(f"admitted external input changed: {path}")
    return json.loads(payload)


def verify_assets(path: Path, expected_sha256: str):
    manifest = load_bound_json(path, expected_sha256)
    if (manifest.get("schema") != 1 or manifest.get("repository") != c.ASSET_REPOSITORY
            or manifest.get("revision") != c.ASSET_REVISION):
        raise ValueError("asset manifest differs from fixed Laya repository/revision")
    for name, (sha, size) in c.ASSET_FILES.items():
        if manifest.get("files", {}).get(name) != {"sha256": sha, "bytes": size}:
            raise ValueError(f"asset manifest omits or changes pinned object: {name}")
    model_root = Path(manifest["model_root"])
    if not model_root.is_absolute() or model_root.resolve() != model_root or not model_root.is_dir():
        raise ValueError("asset model_root must be canonical existing absolute directory")
    if not manifest.get("files"):
        raise ValueError("asset manifest has no bound files")
    for relative, identity in manifest["files"].items():
        file = model_root / relative
        if file.resolve() != file or not file.is_relative_to(model_root):
            raise ValueError("asset path escapes pinned model_root")
        if file.stat().st_size != identity["bytes"] or hash_file(file) != identity["sha256"]:
            raise ValueError(f"pinned asset drift: {relative}")
    return model_root, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True, choices=(0,), help="fixed constructor seed")
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", "--out-dir", dest="out_dir", type=Path, required=True)
    parser.add_argument("--budget-ledger", type=Path, required=True)
    parser.add_argument("--budget-ledger-sha256", required=True)
    parser.add_argument("--asset-manifest", type=Path, required=True)
    parser.add_argument("--asset-manifest-sha256", required=True)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import ENVIRONMENT_KEY, require_admission
    # require_admission consumes this environment value and returns a compact
    # receipt without output/source roots. Capture only their path bindings first;
    # trust them only after the handshake has verified the same full specification.
    spec_paths = json.loads(os.environ.get(ENVIRONMENT_KEY, "{}"))
    admission = require_admission(__file__, direction="typed_joint_skill_decision")
    if args.launch_sha != admission["sha"]:
        raise ValueError("--launch-sha differs from admitted published source")
    root = Path(__file__).resolve().parents[3]
    output = args.out_dir.absolute()
    if (output.resolve() != output or str(output) != spec_paths.get("output_root")
            or str(root) != spec_paths.get("source_root")):
        raise ValueError("output/source root differs from admitted launcher path binding")
    launch = json.loads((output / "launch-manifest.json").read_bytes())
    if any(launch.get(key) != value for key, value in {
            "output_root": str(output), "source_root": str(root), "direction": c.DIRECTION,
            "sha": args.launch_sha, "command_sha256": admission["command_sha256"]}.items()):
        raise ValueError("launcher manifest differs from admitted invocation")
    prior_bill = load_bound_json(args.budget_ledger, args.budget_ledger_sha256)
    bill = Bill(prior_bill, output, source_root=root)
    store = Store(output, bill)
    try:
        threads = {}
        for key in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS"):
            os.environ[key] = "1"
            threads[key] = "1"
        verify_sources(root)
        tokenizer_dir, assets = verify_assets(args.asset_manifest, args.asset_manifest_sha256)
        if not any(tokenizer_dir.is_relative_to(p) for p in bill.roots):
            raise ValueError("model object missing from global disk bill")
        from experiments.candidates.typed_joint_skill_decision.codec import validate_native_features
        # All native imports follow published-source admission and global billing.
        from experiments.candidates.coupled_host_joint_skills_stage1 import host, planner, menus
        import numpy as np
        runtime = NativeRuntime(store, host, planner, menus)
        store.write_json("config.json", {"contract": c.frozen_contract(), "contract_sha256": c.digest(c.frozen_contract()),
            "admission": dict(admission), "seed": args.seed, "asset_manifest": assets,
            "asset_manifest_sha256": args.asset_manifest_sha256, "budget_ledger": prior_bill,
            "budget_ledger_sha256": args.budget_ledger_sha256, "interpreter": sys.executable,
            "numpy_version": np.__version__,
            "cpu_thread_environment": threads,
            "timing_scope": "nested helper wall timings overlap; process CPU bill is authoritative"}, kind="config")
        with runtime.instrument():
            # No outcome queries/steps until *all* 1152 menus pass pinned tokenization.
            for address in c.worlds():
                store.current = {**address, "phase": "prepare_and_validate"}
                prepared = runtime.prepare_world(address)
                prefix = f"prepared/b{address['block']}/{address['split']}/{address['world']}"
                store.write_json(f"{prefix}/features.json", prepared["features"], kind="features", **address)
                # Save the exact refused input before validation can fail. No filtering,
                # omission or new preparation occurs on refusal.
                provenance = {key: value for key, value in prepared.items() if key != "features"}
                store.write_json(f"{prefix}/provenance.json", provenance, kind="preparation", **address)
                try:
                    codec = validate_native_features(prepared["features"], tokenizer_dir)
                except Exception as exc:
                    store.write_json(f"{prefix}/codec_refusal.json", {
                        "feature_sha256": prepared["feature_sha256"],
                        "exception_type": type(exc).__name__, "exception": str(exc)},
                        kind="codec_refusal", **address)
                    raise
                store.write_json(f"{prefix}/codec.json", codec, kind="codec_validation", **address)
                store.status("preparing")
            store.status("all_features_validated")
            for address in c.worlds():
                prefix = output / f"prepared/b{address['block']}/{address['split']}/{address['world']}"
                prepared = json.loads((prefix / "provenance.json").read_bytes())
                prepared["features"] = json.loads((prefix / "features.json").read_bytes())
                runtime.collect_world(prepared)
        bill.check(disk=True)
        status = store.status("complete", timings=runtime.timings)
        store.write_json("summary.json", {**status, "contract_sha256": c.digest(c.frozen_contract()),
                    "source_sha256": c.SOURCE_SHA256, "launch_sha": args.launch_sha,
                    "learning": {"fits": 0, "optimizer_updates": 0, "model_forwards": 0},
                    "manifest_sha256_before_summary": hash_file(output / "manifest.jsonl")}, kind="summary")
        return 0
    except BaseException as exc:
        # Failure preserves all already-written streams, exact counts and the active identity.
        status = store.status("failed_partial", exception_type=type(exc).__name__, exception=str(exc))
        # Do not hide evidence if CPU/disk exhaustion itself caused the failure: use only
        # compact reserved status space, with no native retry or new label generation.
        (output / "failure.json").write_bytes(c.encode_json({**status, "traceback": traceback.format_exc()}))
        raise
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
