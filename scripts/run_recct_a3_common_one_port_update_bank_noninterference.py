"""One-shot runner for RECCT-A3 common one-port bank noninterference."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import ha_ctse_process.continuous_roster_native_six_credit_reduction_g40 as g40
from experiments.candidates.recct_lite import directed_edge_masked_update as a1
from experiments.candidates.recct_lite import (
    common_one_port_update_bank_noninterference as a3,
)
from scripts import run_recct_a1_directed_edge_masked_update_binding as a1_runner


MINUS_INITIALIZATION_SEED = 20_260_810


def _config(optimizer: torch.optim.Adam) -> a1.LearnerConfig:
    group = optimizer.param_groups[0]
    return a1.LearnerConfig(
        learning_rate=float(group["lr"]),
        betas=tuple(float(row) for row in group["betas"]),
        eps=float(group["eps"]),
        weight_decay=float(group["weight_decay"]),
        amsgrad=bool(group["amsgrad"]),
        maximize=bool(group.get("maximize", False)),
    )


def _build_orientation_capsule(
    *,
    initialization_seed: int,
    learner_instance: str,
    policy_generation: str,
    parent_label: bytes,
    predictor_label: bytes,
    roster_names: tuple[str, str, str],
    reverse_handles: bool,
) -> tuple[
    a1.DirectedEdgeMaskedLearner,
    a1.SealedLearnerCapsule,
    tuple[a1.OpaqueDirectedHandle, a1.OpaqueDirectedHandle],
]:
    model = g40.make_model(3, initialization_seed=initialization_seed)
    optimizer = torch.optim.Adam(
        model.actor_credit_parameters(), lr=g40.LEARNING_RATE
    )
    trajectory = a1_runner._sealed_n3_pretreatment_batch(model)
    learner = a1.DirectedEdgeMaskedLearner(learner_instance)
    ancestry = a1.RosterEpochAncestry(
        roster_epoch=1,
        policy_generation=policy_generation,
        learner_checkpoint_digest=a1.model_digest(model),
        optimizer_checkpoint_digest=a1.optimizer_digest(model, optimizer),
        pretreatment_batch_digest=a1.trajectory_digest(trajectory),
        parent_epoch_digest=hashlib.sha256(parent_label).hexdigest(),
    )
    capsule = learner.seal_capsule(
        model=model,
        optimizer=optimizer,
        trajectory=trajectory,
        roster=(
            a1.AgentInstance(roster_names[0], 0),
            a1.AgentInstance(roster_names[1], 1),
            a1.AgentInstance(roster_names[2], 2),
        ),
        ancestry=ancestry,
        frozen_selection=a1.FrozenSelectionState(
            support=(True, True),
            rho=(0.6, 0.6),
            predictor_digest=hashlib.sha256(predictor_label).hexdigest(),
            selected_mask="10",
        ),
        rng_plan=a1.SiteKeyedRNGPlan(
            (("learner/replay", 0), ("optimizer/adam", 0))
        ),
        learner_config=_config(optimizer),
        scheduler_state=a1.DisabledUpdateState("scheduler"),
        scaler_state=a1.DisabledUpdateState("scaler"),
        clipping_state=a1.DisabledUpdateState("gradient_clipping"),
        accumulation_state=a1.DisabledUpdateState("gradient_accumulation"),
    )
    left, right = roster_names[:2]
    handles = (
        learner.handle(capsule, right, left),
        learner.handle(capsule, left, right),
    ) if reverse_handles else (
        learner.handle(capsule, left, right),
        learner.handle(capsule, right, left),
    )
    return learner, capsule, handles


def _credit_rows(orientation: str) -> tuple[a3.CreditObservation, ...]:
    if orientation not in a3.ORIENTATIONS:
        raise ValueError("unknown orientation")
    # Detached proposal predictions and already-observed binary four-step team
    # rewards are fixture data, never inferred from A1 private capsule bytes.
    targets = {
        "A": (0.0, 1.0, 0.0, 1.0),
        "B": (1.0, 0.0, 1.0, 0.0),
    }
    base = {
        "A": {
            "00": (0.44, 0.54, 0.39, 0.59),
            "10": (0.35, 0.66, 0.31, 0.70),
            "01": (0.40, 0.62, 0.34, 0.65),
            "11": (0.29, 0.75, 0.25, 0.78),
        },
        "B": {
            "00": (0.55, 0.45, 0.60, 0.40),
            "10": (0.67, 0.34, 0.72, 0.30),
            "01": (0.63, 0.38, 0.68, 0.33),
            "11": (0.76, 0.25, 0.80, 0.22),
        },
    }
    shift = 0.0 if orientation == "PLUS" else -0.015
    rows = []
    for half in ("A", "B"):
        for state in a3.SHADOW_STATES:
            predictions = tuple(
                min(0.98, max(0.02, value + shift))
                for value in base[half][state]
            )
            rows.append(a3.CreditObservation(half, state, predictions, targets[half]))
    return tuple(rows)


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_registered_credit_sources(
    path: Path,
    capsule_digests: dict[str, str],
) -> dict[str, a3.SealedCreditSource]:
    resolved_path = path.resolve()
    forbidden_root = (REPOSITORY_ROOT / "local_research").resolve()
    try:
        resolved_path.relative_to(forbidden_root)
    except ValueError:
        pass
    else:
        raise ValueError("registered credit source DTO may not come from local_research")
    first = path.read_bytes()
    second = path.read_bytes()
    if first != second:
        raise ValueError("registered credit source DTO changed while being frozen")
    payload = json.loads(first.decode("utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("document_kind") != "recct_a3_immutable_credit_source_dto"
        or payload.get("treatment_id") != a3.TREATMENT_ID
    ):
        raise ValueError("registered credit source DTO identity/schema failed")
    lineage = payload.get("lineage")
    if not isinstance(lineage, dict):
        raise ValueError("registered credit source DTO lineage is absent")
    source_commit = str(lineage.get("source_commit", ""))
    source_git_path = str(lineage.get("source_git_path", ""))
    normalized_git_path = source_git_path.replace("\\", "/").lstrip("./")
    source_blob = (
        _git_value("rev-parse", f"{source_commit}:{source_git_path}")
        if source_commit and source_git_path
        else ""
    )
    if (
        not bool(lineage.get("immutable_before_audit"))
        or not source_commit
        or not source_git_path
        or normalized_git_path.startswith("local_research/")
        or resolved_path != (REPOSITORY_ROOT / source_git_path).resolve()
        or not source_blob
        or _git_value("hash-object", str(path)) != source_blob
    ):
        raise ValueError("registered credit source DTO Git lineage is not immutable")
    dto_sha256 = hashlib.sha256(first).hexdigest()
    source_lineage = a3.CreditSourceLineage(
        source_kind="REGISTERED_IMMUTABLE_DTO",
        source_record_id=str(lineage.get("source_record_id", "")),
        source_commit=source_commit,
        source_blob=source_blob,
        source_dto_sha256=dto_sha256,
        immutable_before_audit=True,
    )
    orientations = payload.get("orientations")
    if not isinstance(orientations, dict) or set(orientations) != set(a3.ORIENTATIONS):
        raise ValueError("registered credit source DTO orientation set failed")
    sources: dict[str, a3.SealedCreditSource] = {}
    for orientation in a3.ORIENTATIONS:
        row = orientations[orientation]
        if (
            not isinstance(row, dict)
            or row.get("capsule_digest") != capsule_digests[orientation]
            or not isinstance(row.get("encoded_content_base64"), str)
            or not isinstance(row.get("opaque_content_digest"), str)
            or row.get("observation_count") != 8
            or row.get("ordered_key_digest")
            != a3.credit_observation_order_digest()
            or "observations" in row
        ):
            raise ValueError("registered credit source DTO capsule binding failed")
        try:
            encoded_content = base64.b64decode(
                row["encoded_content_base64"], validate=True
            )
        except Exception as exc:
            raise ValueError("registered credit source opaque encoding failed") from exc
        sources[orientation] = a3.SealedCreditSource(
            capsule_digests[orientation],
            encoded_content,
            str(row["opaque_content_digest"]),
            int(row["observation_count"]),
            str(row["ordered_key_digest"]),
            source_lineage,
        )
    return sources


def build_registered_pair(source_dto_path: Path) -> a3.ProspectiveOrientationPair:
    plus_learner, plus_capsule, plus_handles = a1_runner.build_registered_capsule()
    minus_learner, minus_capsule, minus_handles = _build_orientation_capsule(
        initialization_seed=MINUS_INITIALIZATION_SEED,
        learner_instance="recct-a3-g40-learner-minus",
        policy_generation="g40-recct-a3-minus-generation-0",
        parent_label=b"recct-a3-minus-pretreatment-parent-epoch-v1",
        predictor_label=b"recct-a3-minus-frozen-pretreatment-predictor-v1",
        roster_names=(
            "minus-member-left",
            "minus-member-right",
            "minus-member-companion",
        ),
        reverse_handles=True,
    )
    sources = _load_registered_credit_sources(
        source_dto_path,
        {"PLUS": plus_capsule.digest, "MINUS": minus_capsule.digest},
    )
    plus = a3.OrientationCapsule(
        orientation="PLUS",
        member_id="orientation-member-plus",
        capsule_id="recct-a3-capsule-plus",
        learner=plus_learner,
        capsule=plus_capsule,
        lr_handle=plus_handles[0],
        rl_handle=plus_handles[1],
        lr_role=("LEFT", "RIGHT"),
        rl_role=("RIGHT", "LEFT"),
        role_instances=(("LEFT", "agent-instance-a"), ("RIGHT", "agent-instance-b")),
        credit_source=sources["PLUS"],
    )
    minus = a3.OrientationCapsule(
        orientation="MINUS",
        member_id="orientation-member-minus",
        capsule_id="recct-a3-capsule-minus",
        learner=minus_learner,
        capsule=minus_capsule,
        lr_handle=minus_handles[0],
        rl_handle=minus_handles[1],
        lr_role=("RIGHT", "LEFT"),
        rl_role=("LEFT", "RIGHT"),
        role_instances=(("LEFT", "minus-member-left"), ("RIGHT", "minus-member-right")),
        credit_source=sources["MINUS"],
    )
    return a3.ProspectiveOrientationPair("recct-a3-frame-0001", plus, minus)


def build_technical_pair() -> a3.ProspectiveOrientationPair:
    """Disjoint technical-only pair; never the registered A3 scientific object."""

    plus_learner, plus_capsule, plus_handles = _build_orientation_capsule(
        initialization_seed=20_260_811,
        learner_instance="recct-a3-technical-learner-plus",
        policy_generation="recct-a3-technical-plus-generation",
        parent_label=b"recct-a3-technical-plus-parent",
        predictor_label=b"recct-a3-technical-plus-predictor",
        roster_names=("technical-plus-left", "technical-plus-right", "technical-plus-companion"),
        reverse_handles=False,
    )
    minus_learner, minus_capsule, minus_handles = _build_orientation_capsule(
        initialization_seed=20_260_812,
        learner_instance="recct-a3-technical-learner-minus",
        policy_generation="recct-a3-technical-minus-generation",
        parent_label=b"recct-a3-technical-minus-parent",
        predictor_label=b"recct-a3-technical-minus-predictor",
        roster_names=("technical-minus-left", "technical-minus-right", "technical-minus-companion"),
        reverse_handles=True,
    )
    technical_lineage = a3.CreditSourceLineage(
        source_kind="TECHNICAL_SYNTHETIC",
        source_record_id="recct-a3-disjoint-technical-fixture-v1",
        source_commit="technical-only-not-a-git-result",
        source_blob="technical-only-not-a-git-blob",
        source_dto_sha256=hashlib.sha256(b"recct-a3-disjoint-technical-credit-fixture-v1").hexdigest(),
        immutable_before_audit=True,
    )
    plus = a3.OrientationCapsule(
        "PLUS",
        "technical-orientation-plus",
        "recct-a3-technical-capsule-plus",
        plus_learner,
        plus_capsule,
        plus_handles[0],
        plus_handles[1],
        ("LEFT", "RIGHT"),
        ("RIGHT", "LEFT"),
        (("LEFT", "technical-plus-left"), ("RIGHT", "technical-plus-right")),
        a3.SealedCreditSource.from_technical_observations(
            plus_capsule.digest, _credit_rows("PLUS"), technical_lineage
        ),
    )
    minus = a3.OrientationCapsule(
        "MINUS",
        "technical-orientation-minus",
        "recct-a3-technical-capsule-minus",
        minus_learner,
        minus_capsule,
        minus_handles[0],
        minus_handles[1],
        ("RIGHT", "LEFT"),
        ("LEFT", "RIGHT"),
        (("LEFT", "technical-minus-left"), ("RIGHT", "technical-minus-right")),
        a3.SealedCreditSource.from_technical_observations(
            minus_capsule.digest, _credit_rows("MINUS"), technical_lineage
        ),
    )
    return a3.ProspectiveOrientationPair("recct-a3-technical-frame", plus, minus)


def _validate_public_a1_result() -> None:
    path = (
        REPOSITORY_ROOT
        / "docs/research/candidates/recct_lite/RECCT_A1_DIRECTED_EDGE_MASKED_UPDATE_BINDING_RESULT.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("branch") != a3.A1_ACCEPTED_BRANCH
        or payload.get("raw_output_binding") != a3.A1_RAW_OUTPUT_BINDING
    ):
        raise ValueError("public accepted RECCT-A1 result binding failed")
    source_relative = "experiments/candidates/recct_lite/directed_edge_masked_update.py"
    result_relative = "docs/research/candidates/recct_lite/RECCT_A1_DIRECTED_EDGE_MASKED_UPDATE_BINDING_RESULT.json"

    bindings = (
        (
            _git_value("rev-parse", f"{a3.A1_SOURCE_COMMIT}:{source_relative}"),
            _git_value("hash-object", source_relative),
            a3.A1_SOURCE_BLOB,
        ),
        (
            _git_value("rev-parse", f"{a3.A1_RESULT_COMMIT}:{result_relative}"),
            _git_value("hash-object", result_relative),
            a3.A1_RESULT_BLOB,
        ),
    )
    if any(accepted != current or current != expected for accepted, current, expected in bindings):
        raise ValueError("current RECCT-A1 source/result bytes differ from frozen Git blobs")


def _technical_fixture_receipt(pair: a3.ProspectiveOrientationPair) -> dict[str, object]:
    binding = a3.A1Binding()
    binding.validate()
    _validate_public_a1_result()
    selected, receipt = a3.select_first_structural_pair((pair,))
    return {
        "technical_fixture_only": True,
        "claim_bearing_calls": 0,
        "a1_binding": a3._jsonable(binding),
        "selected_key": receipt.selected_key,
        "selection_prohibited_value_reads": receipt.prohibited_value_reads,
        "capsule_digests": (
            selected.plus.capsule.digest,
            selected.minus.capsule.digest,
        ),
        "credit_open_calls": (
            selected.plus.credit_source.content_open_count
            + selected.minus.credit_source.content_open_count
        ),
        "credit_content_decode_calls": (
            selected.plus.credit_source.content_decode_count
            + selected.minus.credit_source.content_decode_count
        ),
        "manifest_access_calls": (
            selected.plus.credit_source.manifest_access_count
            + selected.minus.credit_source.manifest_access_count
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the unique RECCT-A3 deterministic common one-port bank audit."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--technical-fixture",
        action="store_true",
        help="Validate bindings and structural selection with zero claim-bearing calls.",
    )
    mode.add_argument(
        "--output",
        type=Path,
        help="Write the unique claim-bearing audit result to a new file.",
    )
    parser.add_argument(
        "--source-dto",
        type=Path,
        help=(
            "Pre-existing immutable Git-bound credit-source DTO. Required for "
            "registered construction; absence selects the frozen provenance failure."
        ),
    )
    args = parser.parse_args(argv)

    if args.technical_fixture:
        if args.source_dto is not None:
            parser.error("--source-dto is reserved for the registered --output path")
        pair = build_technical_pair()
        print(json.dumps(_technical_fixture_receipt(pair), separators=(",", ":"), sort_keys=True))
        return 0

    assert args.output is not None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        if args.source_dto is None:
            result = a3.make_failure_result(
                a3.A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE,
                "no pre-existing immutable registered credit-source DTO was supplied",
            )
        else:
            try:
                pair = build_registered_pair(args.source_dto)
            except Exception as exc:
                result = a3.make_failure_result(
                    a3.A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE,
                    str(exc),
                )
            else:
                try:
                    _validate_public_a1_result()
                except Exception as exc:
                    result = a3.make_failure_result(
                        a3.A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE,
                        str(exc),
                    )
                else:
                    result = a3.run_common_bank_audit((pair,))
        a3.validate_a3_result(result)
        stream.write(result.to_bytes())
        stream.write(b"\n")
    print(json.dumps(result.to_dict(), separators=(",", ":"), sort_keys=True))
    return 0 if result.branch == a3.A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
