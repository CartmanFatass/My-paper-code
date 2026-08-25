"""Exact CRTO-B1 seed-phase coordinator.

The concrete bridges own physical trajectories and panel records.  This
coordinator owns immutable phase ordering, the predictor/probe-before-activity
gate, paired learner updates, checkpoint binding, and the raw-to-aggregate
reporting boundary.  An incomplete bridge is an engineering failure, never a
substitute DGP.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
from typing import Mapping, Sequence

from .config import (
    ALGORITHM_SEEDS, HORIZON, LEARNED_ARMS, PREDICTOR_DATA_EPISODES,
    TRAINING_EPISODES_PER_ARM,
)
from .models import assert_paired_architecture, build_paired_models
from .predictor import (
    FrozenPredictor, fit_calibration_table, fit_frozen_predictor,
    save_predictor_checkpoint,
)
from .training import RecurrentPPOTrainer, fit_decodability_probe


class HostInterfaceError(RuntimeError):
    """A concrete CRTO execution bridge did not meet its frozen contract."""


PANEL_NAMESPACE = 2_026_081_203
FROZEN_REVISION = "CRTO-B1-SCIENCE-20260812-04"


@dataclass(frozen=True)
class PreparedSeed:
    """One probe-cleared seed retained only until learned execution finishes."""

    seed: int
    config: object
    data: object
    evaluation: object
    predictor_data: Mapping[str, object]
    predictor: FrozenPredictor
    calibration: object
    predictor_report: object
    probe_report: object
    predictor_path: object
    panel_identities: Mapping[str, object]
    data_panel_identity_receipt: Mapping[str, object]


def _require_mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise HostInterfaceError(f"bridge {name} must return a mapping")
    return value


def _required(source: Mapping[str, object], keys: Sequence[str], *, name: str) -> None:
    absent = [key for key in keys if key not in source]
    if absent:
        raise HostInterfaceError(f"bridge {name} is missing required fields: {', '.join(absent)}")


def _load_bridges(*, seed: int, config: object) -> tuple[object, object]:
    """Bind the concrete data and evaluation bridges for one algorithm seed.

    The bridges intentionally divide trajectory construction from frozen-policy
    evaluation.  Their module-level phase functions are the only concrete DGP
    access allowed to this coordinator.
    """
    try:
        data_module = importlib.import_module(".data_bridge", __package__)
    except ImportError as error:
        raise HostInterfaceError("CRTO data_bridge module is unavailable") from error
    try:
        evaluation_module = importlib.import_module(".evaluation_bridge", __package__)
    except ImportError as error:
        raise HostInterfaceError("CRTO evaluation_bridge module is unavailable") from error
    return data_module, evaluation_module


def _phase(bridge: object, name: str, /, **kwargs: object) -> Mapping[str, object]:
    call = getattr(bridge, name, None)
    if not callable(call):
        raise HostInterfaceError(f"CRTO execution bridge lacks required phase method {name}()")
    return _require_mapping(call(**kwargs), name=name)


def _panel_identities(evaluation: object, *, seed: int) -> Mapping[str, object]:
    """Obtain the immutable namespace-qualified evaluation panel identities."""
    namespace = getattr(evaluation, "PANEL_ROOT_NAMESPACE", None)
    ordinals = getattr(evaluation, "PANEL_ORDINALS", None)
    root = getattr(evaluation, "panel_root", None)
    if namespace != PANEL_NAMESPACE or not isinstance(ordinals, Mapping) or not callable(root):
        raise HostInterfaceError("CRTO evaluation panel namespace drifted from 2026081203")
    return {
        "namespace": PANEL_NAMESPACE,
        "algorithm_seed": seed,
        "panels": {
            str(name): {"ordinal": int(ordinal), "root": int(root(seed, int(ordinal)))}
            for name, ordinal in ordinals.items()
        },
    }


def _phase_steps(phase: Mapping[str, object], *, name: str, expected: int) -> Mapping[str, object]:
    _required(phase, ("steps",), name=name)
    steps = phase["steps"]
    if isinstance(steps, bool) or not isinstance(steps, int) or steps != expected:
        raise HostInterfaceError(f"bridge {name} must report exactly {expected} completed steps")
    return phase


def _phase_summary(phase: Mapping[str, object]) -> dict[str, object]:
    """Produce a JSON-safe receipt while retaining the full raw phase in memory."""
    summary: dict[str, object] = {"steps": phase["steps"]}
    for name in ("episodes", "states", "assignments", "feature_rows"):
        value = phase.get(name)
        if value is not None:
            try:
                summary[f"{name}_count"] = len(value)  # type: ignore[arg-type]
            except TypeError as error:
                raise HostInterfaceError(f"bridge phase {name} must have a finite record count") from error
    return summary


def _require_authoritative_hazard_encoding(evaluation: object) -> str:
    """Refuse the hazard fit until its frozen switch encoding is installed."""
    encoding_id = getattr(evaluation, "HAZARD_SWITCH_FEATURE_ENCODING_ID", None)
    if not isinstance(encoding_id, str) or not encoding_id.strip():
        raise HostInterfaceError(
            "hazard development is withheld: no authoritative switch-direction/phase encoding ID"
        )
    return encoding_id


def finalize(
    per_seed_raw: Mapping[int, Mapping[str, object]], resources: Mapping[str, object],
) -> Mapping[str, object]:
    """Pool the complete registered seed set through the evaluation analysis API.

    Seed-local phase outputs are intentionally not interpreted by this
    coordinator.  The evaluation bridge converts their registered records into
    the exact analysis inputs and applies the package-level analysis routines.
    """
    expected_seeds = tuple(ALGORITHM_SEEDS)
    observed_seeds = tuple(sorted(per_seed_raw))
    if observed_seeds != expected_seeds:
        raise HostInterfaceError(
            f"aggregate finalization requires exactly the registered eight seeds; got {observed_seeds}"
        )
    if not isinstance(resources, Mapping):
        raise TypeError("aggregate finalization requires the completed resource ledger mapping")
    for seed in expected_seeds:
        row = _require_mapping(per_seed_raw[seed], name=f"per_seed_raw[{seed}]")
        if row.get("seed") != seed:
            raise HostInterfaceError(f"aggregate finalization received a mismatched seed row for {seed}")
        panel_bundle = _require_mapping(row.get("panel_identities"), name=f"seed {seed} panel_identities")
        if panel_bundle.get("namespace") != PANEL_NAMESPACE:
            raise HostInterfaceError(f"seed {seed} top-level panel namespace drifted from 2026081203")
        evaluation_panels = _require_mapping(
            panel_bundle.get("evaluation"), name=f"seed {seed} evaluation panel identities",
        )
        data_panels = _require_mapping(panel_bundle.get("data"), name=f"seed {seed} data panel identities")
        if evaluation_panels.get("namespace") != PANEL_NAMESPACE or data_panels.get("namespace") != PANEL_NAMESPACE:
            raise HostInterfaceError(f"seed {seed} panel namespace drifted from 2026081203")
    try:
        evaluation_module = importlib.import_module(".evaluation_bridge", __package__)
    except ImportError as error:
        raise HostInterfaceError("CRTO evaluation_bridge module is unavailable for finalization") from error
    bridge_finalizer = getattr(evaluation_module, "finalize", None)
    if not callable(bridge_finalizer):
        raise HostInterfaceError("CRTO evaluation_bridge must export finalize(per_seed_raw, resources)")
    aggregate = _require_mapping(
        bridge_finalizer(per_seed_raw=per_seed_raw, resources=resources), name="evaluation_bridge.finalize",
    )
    packet = _require_mapping(aggregate.get("result_packet"), name="aggregate.result_packet")
    if not bool(packet.get("required_sections_complete", False)):
        raise HostInterfaceError("aggregate result packet omitted a required analysis section")
    return aggregate


def prepare_seed(*, seed: int, config: object, ledger: object, writer: object) -> PreparedSeed:
    """Complete one seed's predictor/probe gate without any learned update.

    The runner invokes this for every registered algorithm seed and requires
    all returned probes to pass before it calls :func:`run_prepared_seed` for
    any seed.  This function contains no learned-policy optimizer operation.
    """
    # Delayed imports avoid constructing Torch/host state for --help or source-check.
    from .run import ResourceLedger, SeedWriter

    if not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if not isinstance(ledger, ResourceLedger):
        raise TypeError("CRTO preparation requires the runner's ResourceLedger")
    if not isinstance(writer, SeedWriter):
        raise TypeError("CRTO execution requires the runner's seed-local atomic writer")
    if getattr(config, "horizon", None) != HORIZON or tuple(getattr(config, "algorithm_seeds", ())) == ():
        raise HostInterfaceError("execution received a nonregistered CRTO configuration")
    if getattr(config, "revision", None) != FROZEN_REVISION:
        raise HostInterfaceError(f"execution is bound to {FROZEN_REVISION}")

    data, evaluation = _load_bridges(seed=seed, config=config)
    panel_identities = _panel_identities(evaluation, seed=seed)

    # Scripted arm-independent data, predictor fit/calibration, and the
    # decodability probe all complete before any learned policy update.
    collect_scripted = getattr(data, "collect_scripted_predictor_panel", None)
    materialize_probe = getattr(data, "materialize_probe_splits", None)
    collect_training = getattr(data, "collect_paired_training_batch", None)
    if not all(callable(call) for call in (collect_scripted, materialize_probe, collect_training)):
        raise HostInterfaceError(
            "CRTO data_bridge must export collect_scripted_predictor_panel, "
            "materialize_probe_splits, and collect_paired_training_batch"
        )
    scripted_panel = collect_scripted(seed)
    scripted = _require_mapping({
        "steps": getattr(scripted_panel, "steps", None),
        "observation_dim": getattr(scripted_panel, "observation_dim", None),
        "centralized_state_dim": getattr(scripted_panel, "centralized_state_dim", None),
        "predictor_fit": getattr(scripted_panel, "predictor_fit", None),
        "calibration": getattr(scripted_panel, "calibration", None),
        "development": getattr(scripted_panel, "development", None),
    }, name="scripted_predictor_data")
    _required(
        scripted,
        ("steps", "observation_dim", "centralized_state_dim", "predictor_fit", "calibration", "development"),
        name="scripted_predictor_data",
    )
    _phase_steps(scripted, name="scripted_predictor_data", expected=PREDICTOR_DATA_EPISODES * HORIZON)
    # The complete scripted panel has already consumed its registered
    # environment population at this boundary.  Account it independently of
    # the downstream scientific support gate so a failing probe cannot erase
    # completed work or bypass the post-collection resource check.
    ledger.add(
        "predictor_data", int(scripted["steps"]), completed_rows=PREDICTOR_DATA_EPISODES,
    )
    predictor = FrozenPredictor(int(scripted["observation_dim"]), seed)
    predictor_report = fit_frozen_predictor(predictor, scripted["predictor_fit"])  # type: ignore[arg-type]
    ledger.facts()
    calibration = fit_calibration_table(predictor, scripted["calibration"])  # type: ignore[arg-type]
    probe_splits = materialize_probe(predictor, calibration, scripted_panel)
    ledger.facts()
    _probe, probe_report = fit_decodability_probe(
        seed, probe_splits.predictor_fit, probe_splits.calibration, probe_splits.development,
    )
    probe_inputs = {
        "predictor_fit_examples": len(probe_splits.predictor_fit),
        "calibration_examples": len(probe_splits.calibration),
        "combined_fit_examples": (
            len(probe_splits.predictor_fit) + len(probe_splits.calibration)
        ),
        "development_examples": len(probe_splits.development),
    }
    probe_gate = {
        "normalized_mse_maximum": 0.01,
        "sign_accuracy_minimum": 0.95,
    }
    # Persist the exact observed gate inputs and outputs before applying the
    # pass/fail branch.  This packet contains no learned-policy activity and is
    # intentionally durable even when the registered support gate fails.
    writer.write_json("preactivity.json", {
        "revision": FROZEN_REVISION,
        "seed": seed,
        "predictor": asdict(predictor_report),
        "probe": asdict(probe_report),
        "probe_inputs": probe_inputs,
        "probe_gate": probe_gate,
        "learned_activity_started": False,
    })
    ledger.facts()
    if not probe_report.passed:
        raise HostInterfaceError("registered preactivity decodability probe failed")
    predictor_path = writer.artifact_path("checkpoints/predictor.pt")
    save_predictor_checkpoint(predictor, calibration, predictor_report, predictor_path)
    writer.write_json("preactivity.json", {
        "revision": FROZEN_REVISION, "seed": seed,
        "predictor": asdict(predictor_report), "probe": asdict(probe_report),
        "probe_inputs": probe_inputs, "probe_gate": probe_gate,
        "predictor_checkpoint": str(predictor_path), "learned_activity_started": False,
    })

    panel_manifest = getattr(data, "panel_manifest", None)
    panel_ordinal = getattr(data, "PanelOrdinal", None)
    if not callable(panel_manifest) or panel_ordinal is None:
        raise HostInterfaceError("CRTO data_bridge must export panel_manifest and PanelOrdinal")
    training_manifest = panel_manifest(seed, panel_ordinal.LEARNED_TRAINING)
    persisted_data_panel_identities = {
        "namespace": PANEL_NAMESPACE,
        "scripted_predictor": list(scripted_panel.persisted_identities()),
        "learned_training": [identity.persisted() for identity in training_manifest],
    }
    panel_identity_path = writer.write_json("panel_identities.json", {
        "evaluation": panel_identities, "data": persisted_data_panel_identities,
    })
    predictor_data = {
        "steps": int(scripted["steps"]),
        "observation_dim": int(scripted["observation_dim"]),
        "centralized_state_dim": int(scripted["centralized_state_dim"]),
    }
    data_panel_identity_receipt = {
        "namespace": PANEL_NAMESPACE, "artifact": str(panel_identity_path),
    }
    return PreparedSeed(
        seed=seed, config=config, data=data, evaluation=evaluation, predictor_data=predictor_data,
        predictor=predictor, calibration=calibration, predictor_report=predictor_report,
        probe_report=probe_report, predictor_path=predictor_path,
        panel_identities=panel_identities, data_panel_identity_receipt=data_panel_identity_receipt,
    )


def run_prepared_seed(
    *, prepared: PreparedSeed, ledger: object, activity: object, writer: object,
) -> Mapping[str, object]:
    """Train and evaluate one seed after the runner has closed every probe gate."""
    from .run import ActivityMarker, ResourceLedger, SeedWriter

    if not isinstance(prepared, PreparedSeed):
        raise TypeError("CRTO learned execution requires a PreparedSeed")
    if not isinstance(ledger, ResourceLedger) or not isinstance(activity, ActivityMarker):
        raise TypeError("CRTO learned execution requires the runner's ResourceLedger and ActivityMarker")
    if not isinstance(writer, SeedWriter) or writer.seed != prepared.seed:
        raise TypeError("CRTO learned execution requires its matching seed-local writer")
    seed, config = prepared.seed, prepared.config
    data, evaluation = prepared.data, prepared.evaluation
    predictor_data, predictor, calibration = prepared.predictor_data, prepared.predictor, prepared.calibration
    predictor_report, probe_report = prepared.predictor_report, prepared.probe_report
    predictor_path = prepared.predictor_path
    panel_identities, data_panel_identities = prepared.panel_identities, prepared.data_panel_identity_receipt
    if not bool(getattr(probe_report, "passed", False)):
        raise HostInterfaceError("learned execution received a seed without a passing preactivity probe")
    collect_training = getattr(data, "collect_paired_training_batch", None)
    if not callable(collect_training):
        raise HostInterfaceError("CRTO data_bridge must export collect_paired_training_batch")

    # 2. Paired learned-arm training.  The first trainer invokes the activity
    # marker from inside its first optimizer.step(), not after the batch/seed.
    crto, full = build_paired_models(
        int(predictor_data["observation_dim"]), int(predictor_data["centralized_state_dim"]), seed,
    )
    assert_paired_architecture(crto, full)

    def mark_first_update(witness: Mapping[str, object]) -> None:
        if not activity.facts()["started"]:
            activity.mark_first_learned_optimizer_update(
                seed=seed, arm=str(witness["arm"]), update_index=0,
                trajectory_count=32,
            )

    trainers = {
        "CRTO": RecurrentPPOTrainer(crto, seed, on_first_optimizer_step=mark_first_update),
        "FULL-HISTORY-AUX-TERM": RecurrentPPOTrainer(full, seed),
    }
    reports: dict[str, list[dict[str, object]]] = {arm: [] for arm in LEARNED_ARMS}
    for update_index in range(TRAINING_EPISODES_PER_ARM // 32):
        batch_object = collect_training(
            seed, update_index, {"CRTO": crto, "FULL-HISTORY-AUX-TERM": full}, predictor, calibration,
        )
        as_training_mapping = getattr(batch_object, "as_training_mapping", None)
        if not callable(as_training_mapping):
            raise HostInterfaceError("CRTO paired training batch lacks as_training_mapping()")
        batch = _require_mapping(as_training_mapping(), name="training_batch")
        _required(batch, ("CRTO", "FULL-HISTORY-AUX-TERM", "steps"), name="training_batch")
        _phase_steps(batch, name="training_batch", expected=2 * 32 * HORIZON)
        identities = batch.get("panel_identities")
        if not isinstance(identities, Sequence) or isinstance(identities, (str, bytes)):
            raise HostInterfaceError("CRTO paired training batch omitted its persisted panel identities")
        for arm in LEARNED_ARMS:
            reports[arm].append(asdict(trainers[arm].update(batch[arm])))  # type: ignore[arg-type]
        ledger.add("learned_arm_training", int(batch["steps"]), completed_rows=64)

    checkpoints: dict[str, str] = {"predictor": str(predictor_path)}
    for arm, trainer in trainers.items():
        path = writer.artifact_path(f"checkpoints/{arm}.pt")
        trainer.save_final_checkpoint(path, str(predictor_path))
        checkpoints[arm] = str(path)
    writer.write_json("training.json", {"updates": reports, "checkpoints": checkpoints})

    # 3--8. The bridges receive frozen checkpoints/objects; they cannot retrain
    # or alter predictor/calibration.  Each exact panel is accounted immediately.
    frozen = {"CRTO": crto, "FULL-HISTORY-AUX-TERM": full}
    hazard_encoding_id = _require_authoritative_hazard_encoding(evaluation)
    hazard = _phase(
        evaluation, "hazard_development", seed=seed, model=crto, predictor=predictor,
        calibration=calibration,
    )
    _phase_steps(hazard, name="hazard_development", expected=4 * 64 * HORIZON)
    ledger.add("hazard_development", int(hazard["steps"]), completed_rows=256)

    scored = _phase(
        evaluation, "scored_evaluation", seed=seed, models=frozen, predictor=predictor,
        calibration=calibration, hazard=hazard,
    )
    _phase_steps(scored, name="scored_evaluation", expected=2 * 4 * 64 * HORIZON)
    ledger.add("main_evaluation", int(scored["steps"]), completed_rows=512)

    cuts = _phase(
        evaluation, "complete_rollout_cuts", seed=seed, model=crto, predictor=predictor,
        calibration=calibration, hazard=hazard,
    )
    _phase_steps(cuts, name="complete_rollout_cuts", expected=3 * 4 * 64 * HORIZON)
    ledger.add("complete_rollout_cuts", int(cuts["steps"]), completed_rows=768)

    donor = _phase(
        evaluation, "donor_panel", seed=seed, model=crto, predictor=predictor,
        calibration=calibration,
    )
    _phase_steps(donor, name="donor_panel", expected=4 * 256 * HORIZON)
    ledger.add("donor_only", int(donor["steps"]), completed_rows=1024)

    def persist_derangement_plan(plan_payload: Mapping[str, object]) -> Mapping[str, object]:
        """Durably persist the frozen canonical plan before any replay branch."""
        payload = _require_mapping(plan_payload, name="derangement plan payload")
        if payload.get("seed") != seed or payload.get("panel_namespace") != PANEL_NAMESPACE:
            raise HostInterfaceError("derangement plan persistence received an unregistered seed or namespace")
        artifact = writer.write_json("derangement_plan.json", dict(payload))
        return {"durable": True, "artifact": str(artifact)}

    deranged = _phase(
        evaluation, "deranged_replays", seed=seed, model=crto, predictor=predictor,
        calibration=calibration, scored=scored, donor=donor, persist_plan=persist_derangement_plan,
    )
    _phase_steps(deranged, name="deranged_replays", expected=4 * 64 * HORIZON)
    ledger.add("deranged_replays", int(deranged["steps"]), completed_rows=256)

    audit = _phase(
        evaluation, "audit_enumeration", seed=seed, models=frozen, predictor=predictor,
        calibration=calibration, scored=scored, deranged=deranged,
    )
    _required(audit, ("steps",), name="audit_enumeration")
    audit_steps = audit["steps"]
    if isinstance(audit_steps, bool) or not isinstance(audit_steps, int) or not 0 <= audit_steps <= 4 * 64 * 7 * 16:
        raise HostInterfaceError("audit_enumeration steps must reflect legal actions and remain under its cap")
    ledger.add("audit_action_enumeration", audit_steps, completed_rows=256)

    phase_rows = (predictor_data, hazard, scored, cuts, donor, deranged, audit)
    anomalies: list[str] = []
    for phase in phase_rows:
        phase_anomalies = phase.get("anomalies", ())
        if not isinstance(phase_anomalies, Sequence) or isinstance(phase_anomalies, (str, bytes)):
            raise HostInterfaceError("bridge phase anomalies must be a sequence of strings")
        if any(not isinstance(anomaly, str) for anomaly in phase_anomalies):
            raise HostInterfaceError("bridge phase anomalies must contain only strings")
        anomalies.extend(phase_anomalies)
    raw_panels_complete = all(
        isinstance(phase.get("steps"), int) and not isinstance(phase["steps"], bool)
        for phase in phase_rows
    )
    raw = {
        "seed": seed,
        "panel_identities": {
            "namespace": PANEL_NAMESPACE,
            "evaluation": dict(panel_identities), "data": data_panel_identities,
        },
        "predictor": {"fit": asdict(predictor_report), "probe": asdict(probe_report)},
        "training": {"updates": reports, "checkpoints": checkpoints},
        "hazard_encoding_id": hazard_encoding_id,
        "hazard_development": hazard, "scored_evaluation": scored,
        "mechanism_cuts": {"complete_rollout": cuts, "deranged": deranged},
        "donor_only": donor, "audit": audit,
        "anomalies": tuple(anomalies),
    }
    writer.write_pickle("seed_raw.pkl", raw)
    result = {
        "seed": seed, "predictor": {"fit": asdict(predictor_report), "probe": asdict(probe_report)},
        "training": {"updates": reports}, "hazard_development": _phase_summary(hazard),
        "scored_evaluation": _phase_summary(scored), "donor_only": _phase_summary(donor),
        "mechanism_cuts": {
            "complete_rollout": _phase_summary(cuts), "deranged": _phase_summary(deranged),
        },
        "audit": _phase_summary(audit), "checkpoints": checkpoints,
        "panel_identities": {
            "namespace": PANEL_NAMESPACE,
            "evaluation": dict(panel_identities), "data": data_panel_identities,
        },
        "raw_output_exists": raw_panels_complete,
        # This establishes only that every registered raw panel exists.  The
        # cross-seed aggregate alone decides scientific relevance.
        "question_relevant_output_exists": raw_panels_complete,
        "anomalies": anomalies,
        "_raw": raw,
    }
    writer.write_json("seed_raw.json", {key: value for key, value in result.items() if key != "_raw"})
    return result
