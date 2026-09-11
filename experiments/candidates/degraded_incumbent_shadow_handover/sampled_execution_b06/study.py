"""One LOW_LR learner; modal and two sampled executions of the same final bytes."""
from functools import partial
import hashlib
import json
import math

from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04 import study as b04
from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02 import study as b02

OBJECT = "DISH-SAMPLED-EXECUTION-B06"
SEED = 113
SAMPLES = (0, 1)
MOTION_FIELDS = ("MOTION_OWNER_X", "MOTION_OWNER_Y", "MOTION_STANDBY_X", "MOTION_STANDBY_Y")
ROLE_SWAP = dict(zip(MOTION_FIELDS, MOTION_FIELDS[2:] + MOTION_FIELDS[:2]))
NATIVE_METRICS = ("energy", "completed_ticks", "unstepped_zero_service_ticks", "legal_transfers",
                  "service_before_transfer", "service_at_or_after_transfer")


def master():
    return b04.master(SEED, family=OBJECT)


def evaluation_policy_master():
    return hashlib.sha256(f"{OBJECT}/EVAL_POLICY/seed/{SEED}".encode("ascii")).digest()


class EvaluationPolicySampler:
    """Width1 policy draws; the physical pre-step tick is passed by the evaluator."""

    def __init__(self, *, master_digest, canonical_key, sample):
        self.master_digest = master_digest
        self.canonical_key = canonical_key
        self.sample = sample
        self.owner = 0
        self.counts = {"renewals": 0, "normal_draws": 0, "bernoulli_draws": 0, "uniform_draws": 0}

    def begin_tick(self, *, owner, tick, renew):
        self.owner = owner
        self.words = {}
        if renew:
            fields = [ROLE_SWAP[field] if owner == 1 else field for field in MOTION_FIELDS]
            keys = [(tick, field, draw) for field in fields for draw in (0, 1)]
            keys += [(tick, field, 0) for field in ("PREPARE_BERNOULLI", "COMMIT_BERNOULLI")]
            addresses = tuple(
                f"DISH/RBHR/R06/{OBJECT}/EVAL_POLICY/{self.canonical_key}"
                f"/sample/{self.sample}/tick/{t}/field/{field}/draw/{draw}"
                for t, field, draw in keys)
            words = b04.backend.rng_words_native(self.master_digest, addresses)
            self.words = dict(zip(keys, words))
            self.counts["uniform_draws"] += len(words)
            self.counts["renewals"] += 1

    def _uniform(self, *, tick, field, draw):
        word = self.words[tick, field, draw]
        return ((word >> 11) + 0.5) / 2**53

    def normal(self, *, lane, tick, field):
        del lane  # There is exactly one physical evaluation lane; it is not a TRAIN address.
        # step_rows names its four requests in physical-component order. Bind RNG roles only;
        # inherited means, learned log_std and native raw_action ordering do not move.
        if self.owner == 1:
            field = ROLE_SWAP[field]
        u0 = self._uniform(tick=tick, field=field, draw=0)
        u1 = self._uniform(tick=tick, field=field, draw=1)
        value = math.sqrt(-2.0 * math.log(u0)) * math.cos(2.0 * math.pi * u1)
        self.counts["normal_draws"] += 1
        return value

    def bernoulli(self, *, lane, tick, field, probability):
        del lane
        value = int(self._uniform(tick=tick, field=field, draw=0) < probability)
        self.counts["bernoulli_draws"] += 1
        return value


class SampledEvaluationPolicy(b04.BatchedRecurrentPolicy):
    """Bind public current owner before using the unchanged width1 policy forward."""

    def step_rows(self, observation, *, sampler, global_tick, deterministic):
        sampler.begin_tick(owner=int(observation["owner"][0]), tick=global_tick,
                           renew=bool(observation["renew"][0]))
        return super().step_rows(observation, sampler=sampler, global_tick=global_tick,
                                 deterministic=deterministic)


evaluate_modal = partial(b02.evaluate_episode, record_first_transfer=True)


def planned_cost():
    return {
        "ordinary_transitions": 16 * 32 * 128, "optimizer_steps": 16 * 4 * 8,
        "initial_modal_episodes": 4, "final_modal_episodes": 4, "final_sampled_episodes": 8,
        "evaluation_ticks_upper": 16 * 1200,
        "native_training_call_law": "2N+2E+H; 0<=E<=N, 0<=H<=20E",
        "native_training_calls_upper": (2 + 2 + 20) * 65536,
        "sampled_policy_draw_law": "4R normals, 2R Bernoullis, 10R uniforms in R native RNG batches; R<=9600",
        "sampled_uniform_draws_upper": 8 * 1200 * 10,
        "complete_cap_seconds": 1800,
        "planning_anchors_seconds": {"B05_low_lr_complete": 212.86, "B05_shared_reference": 7.11},
        "projection": "Conditional hundreds-of-seconds anchor; added sampling/checks and new E/H/R unknown. No cost experiment.",
    }


def _native_values(row):
    return {**{name: row[name] for name in NATIVE_METRICS},
            "hard_events": {name: row["hard_events"][name] for name in b04.HARD_EVENTS}}


def paired_result(reference, learner, sampled):
    if any(panel.get("status") != "COMPLETE" for panel in (reference, learner, sampled)):
        raise ValueError("B06 primary requires complete reference, learner and sampled panels")
    reference_rows = reference["reference_rows"]
    modal_rows = learner["evaluation_rows"]
    sampled_rows = sampled["evaluation_rows"]
    if (len(reference_rows), len(modal_rows), len(sampled_rows)) != (4, 4, 8):
        raise ValueError("B06 primary requires four reference, four modal and eight sampled rows")
    zero = {r["coordinate"]: r for r in reference_rows}
    modal = {r["coordinate"]: r for r in modal_rows}
    samples = {(r["coordinate"], r["sample"]): r for r in sampled_rows}
    rows = []
    for coordinate in b04.coordinates():
        key = coordinate.canonical_key()
        initial, mode = zero[key], modal[key]
        draws = [samples[key, j] for j in SAMPLES]
        if not all(r["complete"] for r in (initial, mode, *draws)):
            raise ValueError("B06 primary contains an incomplete episode")
        sampled_mean = sum(r["service_ticks"] for r in draws) / 2
        rows.append({
            "coordinate": key, "initial_modal_service": initial["service_ticks"],
            "final_modal_service": mode["service_ticks"],
            "final_sampled_services": [r["service_ticks"] for r in draws],
            "final_sampled_mean": sampled_mean,
            "sampled_minus_modal": sampled_mean - mode["service_ticks"],
            "modal_minus_initial": mode["service_ticks"] - initial["service_ticks"],
            "sampled_minus_initial": sampled_mean - initial["service_ticks"],
            "initial_modal_native": _native_values(initial), "final_modal_native": _native_values(mode),
            "sampled_native_mean": {
                **{name: sum(r[name] for r in draws) / 2 for name in NATIVE_METRICS},
                "hard_events": {name: sum(r["hard_events"][name] for r in draws) / 2
                                for name in b04.HARD_EVENTS}},
            "first_legal_transfer_ticks": {
                "initial_modal": initial["first_legal_transfer_tick"],
                "final_modal": mode["first_legal_transfer_tick"],
                "final_sampled": [r["first_legal_transfer_tick"] for r in draws]},
        })
    return {
        "object": OBJECT, "seed": SEED, "status": "COMPLETE", "independent_training_instances": 1,
        "reference_mean": sum(r["initial_modal_service"] for r in rows) / 4,
        "modal_mean": sum(r["final_modal_service"] for r in rows) / 4,
        "sampled_mean": sum(r["final_sampled_mean"] for r in rows) / 4,
        "delta_exec": sum(r["sampled_minus_modal"] for r in rows) / 4,
        "d_modal": sum(r["modal_minus_initial"] for r in rows) / 4,
        "g_sampled_vs_init": sum(r["sampled_minus_initial"] for r in rows) / 4,
        "sampled_vs_init_scope": "Learning plus execution-law change; not same-interface learning gain",
        "scale_ticks": 24, "rows": rows,
    }


def actual_exposure(result):
    reference = result.get("reference", {})
    learner = result.get("learner", {})
    sampled = result.get("sampled", {})
    rows = (reference.get("reference_rows", []) + learner.get("evaluation_rows", [])
            + sampled.get("evaluation_rows", []))
    draws = sampled.get("evaluation_rows", [])
    return {
        "initializer_calls": reference.get("initializer_calls", 0),
        "learner": b04.exposure(learner) if "ordinary_training_transitions" in learner else None,
        "evaluation_rows_started": len(rows),
        "evaluation_rows_complete": sum(bool(r.get("complete")) for r in rows),
        "executed_evaluation_ticks": sum(r.get("completed_ticks", 0) for r in rows),
        "unstepped_zero_service_ticks": sum(r.get("unstepped_zero_service_ticks", 0) for r in rows),
        "sampled_policy": {name: sum(r["policy_sampling"][name] for r in draws)
                           for name in ("renewals", "normal_draws", "bernoulli_draws", "uniform_draws")},
        "source_forks": 0, "selected_checkpoint_update": 16,
    }


def run_study(output, deadline, result):
    """One invocation, one learner, one fixed endpoint; all partial panels remain in result."""
    b04.torch.set_num_threads(1)
    result.update(object=OBJECT, seed=SEED, master_hex=master().hex(),
                  evaluation_policy_master_hex=evaluation_policy_master().hex(), status="INCOMPLETE")
    reference = result["reference"] = b04.new_progress()
    shared = output / "shared"
    shared.mkdir()
    b04.prepare_shared(shared, deadline, reference, seed=SEED, object_name=OBJECT,
                       master_family=OBJECT, episode_evaluator=evaluate_modal)
    for row in reference["reference_rows"]:
        row.update(execution_mode="MODAL", checkpoint_update=0, sample=None)
    learner = result["learner"] = b04.new_progress()
    trained = output / "learner"
    trained.mkdir()
    b04.run_arm("LOW_LR", trained, deadline, learner, shared, seed=SEED,
                object_name=OBJECT, master_family=OBJECT, episode_evaluator=evaluate_modal)
    for row in learner["evaluation_rows"]:
        row.update(execution_mode="MODAL", checkpoint_update=16, sample=None)
    final = (trained / "checkpoint_update16.pt").read_bytes()
    resets = json.loads((shared / "resets.json").read_text(encoding="utf8"))
    library = b04.load_host(b04.HOST)
    sampled = result["sampled"] = b04.new_progress()
    for coordinate in b04.coordinates():
        key = coordinate.canonical_key()
        for sample in SAMPLES:
            b04.check_time(deadline)
            reset = resets[key]
            native = b04.backend.native_batch_from_rows((reset,), library=library)
            state = b04.RecurrentRolloutState.fresh("STRUCTURED", width=1)
            policy = SampledEvaluationPolicy(arm="STRUCTURED", checkpoint_bytes=final,
                                              state=state, forecast_package=False)
            sampler = EvaluationPolicySampler(master_digest=evaluation_policy_master(),
                                               canonical_key=key, sample=sample)
            record = {"coordinate": key, "regime": coordinate.regime, "schedule": coordinate.schedule,
                      "speed": 4, "slot": 0, "block": 0, "reset": reset, "execution_mode": "SAMPLED",
                      "sample": sample, "checkpoint_update": 16, "source": f"new:LOW_LR:update16:SAMPLED:{sample}",
                      "policy_sampling": sampler.counts}
            sampled["evaluation_rows"].append(record)
            b02.evaluate_episode(native, policy, deadline, sampled, record, sampler=sampler,
                                 deterministic=False, record_first_transfer=True)
    sampled["status"] = "COMPLETE"
    result["primary"] = paired_result(reference, learner, sampled)
    result["status"] = "COMPLETE"
