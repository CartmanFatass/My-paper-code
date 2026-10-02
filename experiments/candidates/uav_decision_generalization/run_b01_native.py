"""Admitted fresh collection after six frozen fits; original native semantics."""
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

from experiments.candidates.uav_decision_generalization import contract as c
from experiments.candidates.uav_decision_generalization.data import Bill, Store, Trace, hash_file


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
        if address["world"] in (c.BASES[0]+30000, c.BASES[0]+30001):
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
        if address["split"] == "fresh":
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
                f"raw/b{address['block']}/fresh/{address['world']}/full_planner.jsonl.gz", "planner")
            output["full_planner"] = {"menu": menu, "result": result, "logical_sha256": logical,
                                      "static_evaluation_calls": calls, "compute_menu_wall_seconds": planner_seconds}
        self.store.write_json(f"{prefix}/labels.json", output, kind="world_labels", **address)
        self.bill.complete("worlds_completed")
        self.store.status("collecting")

def verify_frozen_fits(fit_root,files,summary):
    import torch
    from experiments.candidates.uav_decision_generalization import phases,models
    if summary.get('weights_frozen_before_fresh') is not True or summary['bill']['delta_counters']['fits_completed']!=6:
        raise ValueError('fresh collection requires all six frozen fits')
    identities={}
    for block in (1,2,3):
        for arm in ('A','R'):
            prefix=f'fits/b{block}/{arm}'
            for name in ('initial.pt','final.pt','config.json','summary.json','optimizer.pt','updates.jsonl','initial-train.json','final-train.json'):
                phases.require_file(files,prefix+'/'+name)
            config=json.loads((fit_root/(prefix+'/config.json')).read_bytes())
            fit_summary=json.loads((fit_root/(prefix+'/summary.json')).read_bytes())
            if (config['model_seed']!=c.BASES[block-1]+(41001 if arm=='A' else 42001)
                    or config['order_seed']!=c.BASES[block-1]+20002 or config['arm']!=arm
                    or config['parameters']!=c.PARAMETERS[arm] or fit_summary['updates']!=512):
                raise ValueError('frozen fit recipe mismatch')
            for stage in ('initial','final'):
                state=torch.load(fit_root/(prefix+'/'+stage+'.pt'),map_location='cpu',weights_only=True)
                digest=models.parameter_digest(state)
                if digest!=fit_summary[stage+'_sha256']:
                    raise ValueError('frozen fit checkpoint mismatch')
                identities[f'b{block}/{arm}/{stage}']=digest
    return identities


def fresh_endpoints(store,records,fit_root,old_root,old_files):
    import torch
    from experiments.candidates.uav_decision_generalization import models,phases
    from experiments.candidates.uav_decision_generalization.run_b01_learning import endpoint
    for block in (1,2,3):
        subset=[r for r in records if r['address']['block']==block]
        for arm in ('A','R','N'):
            for stage in (('final',) if arm=='N' else ('initial','final')):
                model=models.make_model(arm)
                state=(phases.load_old_n(old_root,old_files,block) if arm=='N' else
                       torch.load(fit_root/f'fits/b{block}/{arm}/{stage}.pt',map_location='cpu',weights_only=True))
                model.load_state_dict(state,strict=True)
                endpoint(store,model,subset,arm,stage,block,'fresh')
                del model,state


def main(argv=None):
    from experiments.candidates.uav_decision_generalization import phases,models
    args=phases.parser(__doc__,('fit-input','dataset-input','learning-input')).parse_args(argv)
    from scripts.hmasd_admission import ENVIRONMENT_KEY,require_admission
    import os
    paths=json.loads(os.environ.get(ENVIRONMENT_KEY,'{}'))
    admission=require_admission(__file__,direction='uav_decision_generalization')
    store,admission,prior,root=phases.accepted_store(__file__,args,admission,paths)
    try:
        threads=models.cpu_thread_environment()
        phases.verify_sources(root)
        versions=phases.verify_numerical_versions()
        fit_root,fit_locator,fit_files,fit_summary,fit_config=phases.phase_input(args.fit_input,args.fit_input_sha256,prior)
        phases.verify_phase_source(fit_config,root)
        native_root,native_locator=phases.dataset_locator(args.dataset_input,args.dataset_input_sha256)
        if fit_config['dataset_locator']!=native_locator:
            raise ValueError('fit/native training input mismatch')
        old_root,old_locator,old_files=phases.verify_old_learning(args.learning_input,args.learning_input_sha256,native_locator)
        phases.register_external_roots(store,native_root,old_root)
        phases.register_external_roots(store,fit_root,category="sequential_study_evidence")
        identities=verify_frozen_fits(fit_root,fit_files,fit_summary)
        for block in (1,2,3):
            phases.load_old_n(old_root,old_files,block)
        store.write_json('config.json',{'admission':admission,'contract':c.frozen_contract(),'direction_source_sha256':phases.source_identity(root),'fit_locator':fit_locator,
            'dataset_locator':native_locator,'learning_locator':old_locator,'frozen_fit_digests':identities,'versions':versions,
            'cpu_thread_environment':threads,'prior_bill_sha256':args.budget_ledger_sha256},kind='native_config')
        # Verify original source bytes before importing the pinned native modules.
        from experiments.candidates.coupled_host_joint_skills_stage1 import host,planner,menus
        runtime=NativeRuntime(store,host,planner,menus)
        records=[]
        with runtime.instrument():
            for a in c.worlds():
                prepared=runtime.prepare_world(a)
                prefix=f"prepared/b{a['block']}/fresh/{a['world']}"
                store.write_json(prefix+'/features.json',prepared['features'],kind='features',**a)
                store.write_json(prefix+'/provenance.json',{k:v for k,v in prepared.items() if k!='features'},kind='preparation',**a)
                c.validate_features(prepared['features'])
                store.status('preparing')
            # GPU endpoint decisions are made without any fresh outcome access.
            for a in c.worlds():
                prefix=store.output/f"prepared/b{a['block']}/fresh/{a['world']}"
                records.append({'address':a,'features':json.loads((prefix/'features.json').read_bytes())})
            store.bill.start_gpu();models.configure_float32()
            import torch
            import numpy as np
            if torch.__version__!='2.7.0+cu118' or np.__version__!='1.26.3':
                raise RuntimeError('frozen numerical dependency versions unavailable')
            torch.cuda.reset_peak_memory_stats()
            fresh_endpoints(store,records,fit_root,old_root,old_files)
            torch.cuda.synchronize();store.bill.stop_gpu()
            gpu_peak={'allocated_bytes':torch.cuda.max_memory_allocated(),'reserved_bytes':torch.cuda.max_memory_reserved()}
            for a in c.worlds():
                prefix=store.output/f"prepared/b{a['block']}/fresh/{a['world']}"
                prepared=json.loads((prefix/'provenance.json').read_bytes())
                prepared['features']=json.loads((prefix/'features.json').read_bytes())
                runtime.collect_world(prepared)
        if store.bill.delta['worlds_completed']!=384:
            raise AssertionError('incomplete fresh worlds')
        total=sum(store.bill.total('endpoint_'+arm+'_contexts') for arm in ('A','R','N'))
        if total!=4992:
            raise AssertionError('endpoint budget mismatch')
        status=store.status('complete',timings=runtime.timings)
        store.write_json('summary.json',{**status,'launch_sha':args.launch_sha,'source_sha256':c.SOURCE_SHA256,
            'contract_sha256':c.digest(c.frozen_contract()),'fit_manifest_sha256':fit_locator['manifest_sha256'],
            'endpoint_contexts':total,'gpu_peak':gpu_peak,'timings':runtime.timings,'learning_updates':0},kind='native_summary')
        return 0
    except BaseException as exc:
        store.bill.stop_gpu();phases.failure(store,exc);raise
    finally:
        store.close()


if __name__=='__main__':
    raise SystemExit(main())
