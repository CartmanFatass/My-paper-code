"""EOCIV Stage 0 deterministic no-update preflight.

Executes the licensed Stage 0 scope end to end: environment/identity
manifest, source digests, world/noise/ancestry manifest, model instantiation
(forward only), bound execution of sample D_fit episodes through the accepted
binding path, and the thirteen registered abort predicates (registration
``ABORT_PREDICATES``) — each terminal, none advisory.

NO parameter update happens here.  The optimizers are constructed so their
classes and constants are executable registration facts and are then
discarded without a single ``step()``.

The preflight's terminal is
``EOCIV_STAGE0_PREFLIGHT_COMPLETE`` or ``EOCIV_STAGE0_PREFLIGHT_ABORT``.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import platform
import sys

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate as gate_mod
from experiments.candidates.eociv_lite import outcome_harness as harness
from experiments.candidates.eociv_lite import sibling_env as sib
from experiments.candidates.eociv_lite import stage0_registration as reg
from experiments.candidates.eociv_lite import trainable_policy as tp

RAW_OUTPUT_BINDING = "eociv_lite.stage0_preflight.v1"

#: The D_fit-namespace sample the preflight drives (forward-only).  These
#: are fit-pool episodes, never focal roots: no focal-arm return is read.
PREFLIGHT_EPISODES = (0, 1)
PREFLIGHT_PROFILE_INDEX = 0

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)


def environment_manifest() -> dict[str, object]:
    torch_config = tp.configure_torch()
    try:
        blas = str(np.show_config(mode="dicts"))
    except TypeError:
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            np.show_config()
        blas = buffer.getvalue()
    return {
        "experiment_identity": reg.STAGE0_IDENTITY,
        "parent_capability_commit": reg.PARENT_CAPABILITY_COMMIT,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "backend": "cpu",
        "blas_config": blas,
        "torch_config": torch_config,
        "env_vars": {
            name: os.environ.get(name) for name in reg.MANIFEST_ENV_VARS
        },
    }


def source_digests() -> dict[str, str]:
    digests: dict[str, str] = {}
    for relative in reg.DIGEST_FILES:
        path = os.path.join(_REPO_ROOT, *relative.split("/"))
        with open(path, "rb") as handle:
            digests[relative] = hashlib.sha256(handle.read()).hexdigest()
    return digests


def _shock_source_receiver_digest(profile, local_episode_id: int) -> str:
    """Digest of the block's shock states and per-event source/receiver
    draws (ruling 6.7: include these, not only world/noise digests).

    This drives the sampled episode's WORLD forward with constructive
    actions to reach the boundaries — including, for the d_focal pool,
    focal-namespace worlds.  That is manifest evidence within the Stage 0
    license ("generate Stage 0 manifests and raw evidence"): no arm is
    instantiated, no policy runs, and no return, reward statistic or
    contrast is read or stored."""
    env = harness.block_environment(profile, local_episode_id)
    record: list[object] = [env._shock_states]
    for event_index in range(len(sib.EVENT_TIMES)):
        gate_mod._drive_to(env, sib.EVENT_TIMES[event_index])
        opportunity = env.opportunity(event_index)
        record.append(
            (event_index, opportunity.identity.source_member_key,
             opportunity.identity.receiver_member_key)
        )
    return hashlib.sha256(repr(record).encode("ascii")).hexdigest()


def world_noise_ancestry_manifest(samples_per_pool: int = 2) -> dict[str, object]:
    pools: dict[str, object] = {}
    for pool in harness.POOLS:
        namespace = harness.pool_episode_ids(pool)
        per_profile = {}
        for profile in roster_env.TRAIN_PROFILES:
            sample_ids = tuple(
                namespace[i] for i in range(min(samples_per_pool, len(namespace)))
            )
            rows = []
            for episode_id in sample_ids:
                ledger = roster_env.make_ledger(
                    episode_id,
                    master_seed=harness.outcome_world_seed(profile.name),
                    profile=profile,
                )
                rows.append(
                    {
                        "local_episode_id": episode_id,
                        "ancestry_root": harness.episode_uid(
                            profile.name, pool, episode_id
                        ),
                        "world_digest": gate_mod._world_digest(ledger),
                        "noise_digest": gate_mod._noise_digest(profile, episode_id),
                        "shock_source_receiver_digest": (
                            _shock_source_receiver_digest(profile, episode_id)
                        ),
                    }
                )
            per_profile[profile.name] = {
                "world_seed": harness.outcome_world_seed(profile.name),
                "noise_seed": harness.outcome_noise_seed(profile.name),
                "namespace": [namespace.start, namespace.stop - 1],
                "samples": rows,
            }
        pools[pool] = per_profile
    return pools


def _run_preflight_episode(
    profile, actor: tp.EocivActor, valve: tp.EocivValve, arm: str,
    local_episode_id: int,
) -> art.ArmEpisodeRunner:
    runner = harness.build_arm_runner(
        profile,
        pool="d_fit",
        actor_training_seed=actor.actor_training_seed,
        local_episode_id=local_episode_id,
        arm=arm,
        actor=actor,
        valve=valve,
    )
    runner.run_episode()
    return runner


def preflight() -> dict[str, object]:
    """Run the Stage 0 preflight and the thirteen abort predicates."""
    aborts: dict[str, bool] = {name: False for name in reg.ABORT_PREDICATES}
    detail: dict[str, object] = {}
    profile = roster_env.TRAIN_PROFILES[PREFLIGHT_PROFILE_INDEX]

    manifest = environment_manifest()
    # A torch thread policy differing from the REGISTERED constants is a
    # registration mismatch (the registered constant is not honored by the
    # process), routed under predicate 2 by that reading.
    if (
        manifest["torch_config"]["intra_op_threads"] != reg.TORCH_INTRA_OP_THREADS
        or manifest["torch_config"]["inter_op_threads"] != reg.TORCH_INTER_OP_THREADS
    ):
        aborts["source_or_registration_digest_mismatch"] = True
        detail["registered_torch_policy_not_honored"] = manifest["torch_config"]

    # 1. Gate v2.1 must be green.
    gate_report = gate_mod.gate()
    detail["gate_terminal"] = gate_report["terminal"]
    if gate_report["terminal"] != "EOCIV_SIBLING_CAPABILITY_PRESENT":
        aborts["gate_v21_not_green"] = True

    # 2. Source digests against the FROZEN registered baselines: an altered
    # source or registration file aborts locally (ruling 6.10) — the
    # recompute-twice form could never fire and was replaced after review.
    # The registration module itself cannot contain its own digest; it is
    # emitted here and pinned externally (commit + dispatch archive).
    digests = source_digests()
    detail["source_digests"] = digests
    mismatched = [
        path
        for path, expected in reg.EXPECTED_SOURCE_DIGESTS.items()
        if digests.get(path) != expected
    ]
    if mismatched:
        aborts["source_or_registration_digest_mismatch"] = True
        detail["digest_mismatches"] = mismatched

    # 3. Profile-qualified seeds: ONE authoritative implementation, by
    # function identity, and derived values equal to the accepted gate's
    # check-11 report.
    identity_ok = (
        harness.profile_qualified_seed is gate_mod.profile_qualified_seed
        and harness.outcome_world_seed is gate_mod.outcome_world_seed
        and harness.outcome_noise_seed is gate_mod.outcome_noise_seed
    )
    eleven = gate_report["checks"][
        "11_profile_qualified_outcome_world_noise_manifest"
    ]
    seeds_ok = all(
        eleven["world_seeds"][p.name] == harness.outcome_world_seed(p.name)
        and eleven["noise_seeds"][p.name] == harness.outcome_noise_seed(p.name)
        for p in roster_env.TRAIN_PROFILES
    )
    detail["authoritative_seed_functions"] = identity_ok
    if not (identity_ok and seeds_ok):
        aborts["profile_qualified_seed_mismatch"] = True

    # 4. Ancestry: namespaces disjoint and sampled ancestry roots unique.
    ancestry = world_noise_ancestry_manifest()
    roots = [
        row["ancestry_root"]
        for pool in ancestry.values()
        for entry in pool.values()
        for row in entry["samples"]
    ]
    if len(set(roots)) != len(roots) or not eleven["namespaces_disjoint"]:
        aborts["ancestry_overlap"] = True

    # 5. Token-support assignment: deterministic and at the registered rates
    # over the FULL d_fit namespace x 3 events.
    counts: dict[str, int] = {}
    for episode_id in harness.pool_episode_ids("d_fit"):
        for event_index in range(3):
            route = harness.fit_support_route(
                "d_fit", profile.name, episode_id, event_index
            )
            counts[route] = counts.get(route, 0) + 1
    total = sum(counts.values())
    frequencies = {route: counts[route] / total for route in sorted(counts)}
    detail["fit_support_frequencies"] = frequencies
    targets = {"REAL": 0.5, "NATIVE_NEUTRAL": 0.25,
               "PATTERN_ONLY": 0.125, "PAYLOAD_KNOCKOUT": 0.125}
    # Determinism half: recompute the ENTIRE assignment census and require
    # equality (a per-call self-comparison would be vacuous — review F7).
    counts_replay: dict[str, int] = {}
    for episode_id in harness.pool_episode_ids("d_fit"):
        for event_index in range(3):
            route = harness.fit_support_route(
                "d_fit", profile.name, episode_id, event_index
            )
            counts_replay[route] = counts_replay.get(route, 0) + 1
    if counts_replay != counts:
        aborts["token_support_assignment_drift"] = True
    if any(abs(frequencies.get(k, 0.0) - v) > 0.02 for k, v in targets.items()):
        aborts["token_support_assignment_drift"] = True

    # 6. Read-set contracts, structurally.
    actor_params = tuple(
        inspect.signature(tp.EocivActor.forward_step).parameters
    )
    valve_params = tuple(inspect.signature(tp.valve_features).parameters)
    read_set_ok = (
        actor_params == ("self", "observations", "active_mask", "slot_block",
                         "hidden", "noise")
        and valve_params == ("w_minus_bytes", "member_capacity")
    )
    # The Bernoulli-0.5 gate probe must be mechanically unreachable from the
    # outcome harness: no call site may exist.  (The harness docstrings name
    # the forbidden probe without parentheses; a call requires them.)
    harness_source = inspect.getsource(harness)
    probe_unreachable = "control_tape_open(" not in harness_source
    detail["gate_probe_unreachable_from_harness"] = probe_unreachable
    if not (read_set_ok and probe_unreachable):
        aborts["actor_or_valve_read_set_violation"] = True

    # 8. The accepted runner routes every boundary action through bound_step.
    runner_source = inspect.getsource(art.ArmEpisodeRunner.run_episode)
    if "bound_step(env, actions, action_receipt)" not in runner_source:
        aborts["direct_boundary_env_step_bypass"] = True

    # Build the three registered actor seeds; record parameter digests and
    # construct (never step) the registered optimizers.
    model_digests = {}
    for seed in reg.ACTOR_TRAINING_SEEDS:
        actor_s, critic_s, valve_s = tp.build_models(seed)
        tp.build_optimizers(actor_s, critic_s, valve_s)
        model_digests[seed] = tp.parameter_digest(actor_s, critic_s, valve_s)
    detail["model_parameter_digests"] = model_digests
    detail["optimizer_steps_taken"] = 0

    # 7/9/10/11/12/13: bound forward-only execution on D_fit samples.
    actor, critic, valve = tp.build_models(reg.ACTOR_TRAINING_SEEDS[0])
    runs: dict[str, art.ArmEpisodeRunner] = {}
    try:
        for arm in ("LR", "CR", "LS"):
            runs[arm] = _run_preflight_episode(
                profile, actor, valve, arm, PREFLIGHT_EPISODES[0]
            )
        runs["LR2"] = _run_preflight_episode(
            profile, actor, valve, "LR", PREFLIGHT_EPISODES[1]
        )
    except art.ReceiptError as error:
        aborts["receipt_action_binding_violation"] = True
        detail["binding_error"] = str(error)
    except ValueError as error:
        aborts["action_support_violation"] = True
        detail["support_error"] = str(error)

    if not aborts["receipt_action_binding_violation"] and not aborts[
        "action_support_violation"
    ]:
        if runs["LR"].step_traces != runs["CR"].step_traces:
            aborts["lr_cr_presampling_or_trajectory_mismatch"] = True
        totals = {name: sum(r.env.reward_trace) for name, r in runs.items()}
        detail["preflight_reward_totals_d_fit_pool"] = {
            # D_fit diagnostics, not focal outcomes: these episodes are from
            # the fit namespace and carry no arm contrast.
            name: float(value) for name, value in totals.items()
        }
        if not all(np.isfinite(v) for v in totals.values()):
            aborts["nonfinite_forward_value"] = True
        # 12. Nondeterministic replay: fresh models from the same seed must
        # reproduce the episode byte-for-byte.
        actor_r, _, valve_r = tp.build_models(reg.ACTOR_TRAINING_SEEDS[0])
        replay_runner = _run_preflight_episode(
            profile, actor_r, valve_r, "LR", PREFLIGHT_EPISODES[0]
        )
        if replay_runner.step_traces != runs["LR"].step_traces:
            aborts["nondeterministic_replay"] = True
        if tp.parameter_digest(actor_r) != tp.parameter_digest(actor):
            aborts["nondeterministic_replay"] = True
        # 13. Artifact lifecycle completeness.
        lifecycle_ok = all(
            len(r.step_traces) == roster_env.HORIZON
            and len(r.boundary_records) == 3
            and len(r.action_receipts) == 3
            for r in runs.values()
        )
        if not lifecycle_ok:
            aborts["incomplete_artifact_lifecycle"] = True

    aborted = any(aborts.values())
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "stage0_identity": reg.STAGE0_IDENTITY,
        "environment": manifest,
        "world_noise_ancestry": ancestry,
        "abort_predicates": aborts,
        "detail": detail,
        "binding_failure_rule": reg.BINDING_FAILURE_RULE,
        "terminal": (
            "EOCIV_STAGE0_PREFLIGHT_ABORT" if aborted
            else "EOCIV_STAGE0_PREFLIGHT_COMPLETE"
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(preflight(), indent=2, default=str))
