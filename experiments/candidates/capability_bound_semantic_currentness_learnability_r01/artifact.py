"""Atomic create-only publication seam for a future complete CBSC-LR01 result."""

from __future__ import annotations

import json
import math
import os
from dataclasses import fields, is_dataclass
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping

from .contract import PRODUCTION_BLOCKER, READY_FOR_PRODUCTION, SCHEMA_ID


_TOGGLE_CELL_PAIRS = {
    "neutral_active": (3, 5),
    "persist_refresh": (3, 15),
    "correct_swapped": (3, 4),
    "open_gated": (6, 9),
    "owner_live_broken": (3, 27),
    "authentic_reassociated": (3, 9),
}


def _toggle_counts_from_correct_by_cell(values: Any) -> dict[str, list[int]]:
    if (
        not isinstance(values, list) or len(values) != 48
        or any(type(count) is not int or not 0 <= count <= 16 for count in values)
    ):
        raise ValueError("CBSC-LR01 STRUCT U64 correct-by-cell support mismatch")
    return {
        name: [values[left], values[right]]
        for name, (left, right) in _TOGGLE_CELL_PAIRS.items()
    }


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        to_jsonable(value), ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"),
    ).encode("ascii")


def validate_complete_result(result: Mapping[str, Any]) -> None:
    if not READY_FOR_PRODUCTION:
        raise RuntimeError(f"CBSC-LR01 result publication is fenced: {PRODUCTION_BLOCKER}")
    if not isinstance(result, Mapping):
        raise TypeError("CBSC-LR01 result must be a mapping")
    if result.get("schema") != SCHEMA_ID or result.get("complete") is not True:
        raise ValueError("CBSC-LR01 publication requires its complete registered schema")
    required = {"schema", "complete", "protocol_id", "codec_schedules", "branch", "audits", "first_failing_witness", "preflight", "competence", "main", "decision", "work", "resource"}
    if set(result) != required or result.get("protocol_id") != "CBSC-LR01":
        raise ValueError("CBSC-LR01 complete result key/identity mismatch")
    if result["branch"] not in {
        "INVALID", "RAW_INCOMPETENT", "NO_RESOLVABLE_HEADROOM",
        "VALID_NARROW_CBSC_INDUCTIVE_BIAS", "GENERIC_FACTORIZATION_OR_CONDITIONING",
        "NO_CAPABILITY_SPECIFIC_ATTRIBUTION", "PRACTICAL_EQUIVALENCE",
        "RAW_OR_SHAM_MATERIALLY_SUPERIOR", "UNRESOLVED",
    }:
        raise ValueError("CBSC-LR01 branch mismatch")
    from .codecs import CODEC_SCHEDULES, CodecArm
    expected_schedules = {
        arm.value: [list(pair) for pair in CODEC_SCHEDULES[arm]] for arm in CodecArm
    }
    if result.get("codec_schedules") != expected_schedules or result["preflight"].get("codec_schedules") != expected_schedules:
        raise ValueError("CBSC-LR01 literal codec schedule mismatch")
    preflight = result["preflight"]
    if not isinstance(preflight, Mapping) or preflight.get("valid") is not True or preflight.get("ready_for_production") is not True:
        raise ValueError("CBSC-LR01 complete result requires a valid ready preflight")
    audit_order = (
        "preflight_valid", "complete_competence_panel", "competence_numeric_health",
        "complete_main_panel", "main_numeric_health", "update_zero_common",
        "direct_pair_parity", "paired_work_parity",
    )
    audits = result["audits"]
    if not isinstance(audits, Mapping) or set(audits) != set(audit_order) or any(
        value not in (True, False, None) for value in audits.values()
    ):
        raise ValueError("CBSC-LR01 audit map mismatch")
    competence = result["competence"]
    if not isinstance(competence, list) or len(competence) != 4:
        raise ValueError("CBSC-LR01 requires four competence blocks")
    for block, item in enumerate(competence):
        if not isinstance(item, Mapping) or (item.get("block"), item.get("arm"), item.get("updates")) != (block, "RAW_FLEX", 512):
            raise ValueError("CBSC-LR01 competence identity/order mismatch")
        checkpoints = item.get("checkpoints")
        if not isinstance(checkpoints, list) or len(checkpoints) != 1 or checkpoints[0].get("update") != 512:
            raise ValueError("CBSC-LR01 competence checkpoint mismatch")
        receipt = item.get("work_receipt", {})
        if (
            receipt.get("digest_role") != "NON_AUTH_INFORMATIONAL_RECEIPT"
            or receipt.get("codec_context_materializations") != 1536
            or receipt.get("codec_xor_operations") != 75264
            or receipt.get("active_parameters") != 43395
            or receipt.get("parameter_bytes") != 173580
            or receipt.get("dense_macs_per_context") != 43056
            or receipt.get("training_forward_contexts") != 49152
            or receipt.get("backward_calls") != 512
            or receipt.get("adam_calls") != 512
            or receipt.get("scalar_target_exposures") != 147456
            or receipt.get("checkpoint_evaluations") != 1
            or receipt.get("evaluation_contexts") != 768
        ):
            raise ValueError("CBSC-LR01 competence work receipt mismatch")
    raw_competent = all(
        item["finite_losses"] is True
        and item["checkpoints"][0].get("finite") is True
        and item["checkpoints"][0].get("state_unchanged") is True
        and item["checkpoints"][0].get("correct") == 768
        and item["checkpoints"][0].get("strict") == 768
        and item["checkpoints"][0].get("zero_regret") == 768
        for item in competence
    )
    competence_numeric_health = all(
        item["finite_losses"] is True
        and item["checkpoints"][0].get("finite") is True
        and item["checkpoints"][0].get("state_unchanged") is True
        for item in competence
    )
    main = result["main"]
    if main == []:
        expected_audits = {
            "preflight_valid": True, "complete_competence_panel": True,
            "competence_numeric_health": competence_numeric_health,
            "complete_main_panel": None, "main_numeric_health": None,
            "update_zero_common": None, "direct_pair_parity": None,
            "paired_work_parity": None,
        }
        if dict(audits) != expected_audits or result["decision"] is not None:
            raise ValueError("CBSC-LR01 competence-first audit projection mismatch")
        expected_branch = "INVALID" if not competence_numeric_health else "RAW_INCOMPETENT"
        if raw_competent or result["branch"] != expected_branch:
            raise ValueError("competence-first result is not branch coherent")
    else:
        if not raw_competent or not isinstance(main, list) or len(main) != 24:
            raise ValueError("complete main result requires competent RAW and 24 blocks")
        from .analysis import reduce_finite_panel, select_branch
        from .codecs import CodecArm
        vectors = []
        no_headroom = True
        endpoint = True
        parity_keys = {
            "initial_logits_zero", "codec_context_materializations",
            "codec_xor_operations", "active_parameters", "parameter_bytes",
            "dense_macs_per_context", "training_forward_contexts", "backward_calls",
            "adam_calls", "scalar_target_exposures", "checkpoint_evaluations",
            "evaluation_contexts", "workers", "threads", "dtype",
        }
        direct_parity_all = True
        paired_work_all = True
        update_zero_all = True
        main_numeric_health = True
        for block, item in enumerate(main):
            if item.get("block") != block or len(item.get("arms", [])) != 3:
                raise ValueError("CBSC-LR01 main block/arm support mismatch")
            if type(item.get("direct_pair_parity")) is not bool:
                raise ValueError("CBSC-LR01 direct paired byte/value parity receipt mismatch")
            direct_parity_all = direct_parity_all and item["direct_pair_parity"]
            arms = item["arms"]
            if [arm.get("arm") for arm in arms] != [member.value for member in CodecArm]:
                raise ValueError("CBSC-LR01 main arm order mismatch")
            baseline = {key: arms[0]["work_receipt"].get(key) for key in parity_keys}
            for arm in arms:
                if arm.get("updates") != 64 or [point.get("update") for point in arm.get("checkpoints", [])] != [0, 8, 16, 32, 64]:
                    raise ValueError("CBSC-LR01 main checkpoint schedule mismatch")
                if type(arm.get("finite_losses")) is not bool:
                    raise ValueError("CBSC-LR01 finite-loss health must be boolean")
                main_numeric_health = main_numeric_health and arm["finite_losses"]
                receipt = arm.get("work_receipt", {})
                if receipt.get("digest_role") != "NON_AUTH_INFORMATIONAL_RECEIPT":
                    raise ValueError("CBSC-LR01 digest receipt role mismatch")
                paired_work_all = paired_work_all and (
                    {key: receipt.get(key) for key in parity_keys} == baseline
                )
                if (
                    receipt.get("codec_context_materializations") != 1536
                    or receipt.get("codec_xor_operations") != 75264
                    or receipt.get("active_parameters") != 43395
                    or receipt.get("parameter_bytes") != 173580
                    or receipt.get("dense_macs_per_context") != 43056
                    or receipt.get("training_forward_contexts") != 6144
                    or receipt.get("backward_calls") != 64
                    or receipt.get("adam_calls") != 64
                    or receipt.get("scalar_target_exposures") != 18432
                    or receipt.get("checkpoint_evaluations") != 5
                    or receipt.get("evaluation_contexts") != 3840
                    or receipt.get("initial_logits_zero") is not True
                ):
                    raise ValueError("CBSC-LR01 work receipt mismatch")
                for point in arm["checkpoints"]:
                    if type(point.get("finite")) is not bool or type(point.get("state_unchanged")) is not bool:
                        raise ValueError("CBSC-LR01 evaluation health must be boolean")
                    main_numeric_health = (
                        main_numeric_health and point["finite"] and point["state_unchanged"]
                    )
                    for name in ("mean_regret", "gated_regret", "open_regret"):
                        value = point.get(name)
                        if type(value) is not float or not math.isfinite(value) or value < 0:
                            raise ValueError("CBSC-LR01 checkpoint regret mismatch")
                    if point["mean_regret"] > 11.0 / 8.0 or point["gated_regret"] > 1.0 or point["open_regret"] > 1.0:
                        raise ValueError("CBSC-LR01 checkpoint regret outside exact bound")
                    for name in ("correct", "strict", "zero_regret"):
                        value = point.get(name)
                        if type(value) is not int or not 0 <= value <= 768:
                            raise ValueError("CBSC-LR01 checkpoint count mismatch")
                no_headroom = no_headroom and arm["checkpoints"][1].get("zero_regret") == 768
            u0_fields = ("mean_regret", "gated_regret", "open_regret", "correct", "strict", "zero_regret")
            computed_u0_common = all(
                tuple(arm["checkpoints"][0][name] for name in u0_fields)
                == tuple(arms[0]["checkpoints"][0][name] for name in u0_fields)
                for arm in arms
            ) and all(arm["work_receipt"].get("initial_logits_zero") is True for arm in arms)
            if item.get("update_zero_common") is not computed_u0_common:
                raise ValueError("CBSC-LR01 update-zero common receipt mismatch")
            update_zero_all = update_zero_all and computed_u0_common
            if item.get("paired_work_parity") is not (
                all({key: arm["work_receipt"].get(key) for key in parity_keys} == baseline for arm in arms)
            ):
                raise ValueError("CBSC-LR01 paired work parity receipt mismatch")
            weights = (1.0 / 16.0, 1.0 / 8.0, 3.0 / 16.0, 3.0 / 8.0, 1.0 / 4.0)
            def auc(arm_index: int, surface: str) -> float:
                return float(sum(
                    weight * float(point[surface])
                    for weight, point in zip(weights, arms[arm_index]["checkpoints"])
                ))
            structured_e, sham_e, raw_e = auc(0, "mean_regret"), auc(1, "mean_regret"), auc(2, "mean_regret")
            expected_vector = [
                raw_e - structured_e,
                sham_e - structured_e,
                (auc(1, "gated_regret") - auc(0, "gated_regret"))
                - (auc(1, "open_regret") - auc(0, "open_regret")),
            ]
            vector = item.get("estimand")
            if not isinstance(vector, list) or len(vector) != 3 or any(type(value) is not float or not math.isfinite(value) for value in vector):
                raise ValueError("CBSC-LR01 estimand vector mismatch")
            if vector != expected_vector:
                raise ValueError("CBSC-LR01 estimand does not reconstruct from checkpoints")
            vectors.append(tuple(vector))
            toggle = item.get("structured_toggle_counts")
            reconstructed_toggle = _toggle_counts_from_correct_by_cell(
                item.get("structured_u64_correct_by_cell")
            )
            if sum(item["structured_u64_correct_by_cell"]) != arms[0]["checkpoints"][-1]["correct"]:
                raise ValueError("CBSC-LR01 STRUCT U64 cell counts do not sum to checkpoint total")
            if toggle != reconstructed_toggle:
                raise ValueError("CBSC-LR01 structured toggle map does not reconstruct from 48 cells")
            computed_endpoint = (
                arms[0]["checkpoints"][-1]["mean_regret"] < arms[0]["checkpoints"][0]["mean_regret"]
                and all(count >= 15 for pair in reconstructed_toggle.values() for count in pair)
            )
            if item.get("structured_endpoint_gate") is not computed_endpoint:
                raise ValueError("CBSC-LR01 structured endpoint gate mismatch")
            endpoint = endpoint and computed_endpoint
        decision = reduce_finite_panel(vectors)
        if result["decision"] != to_jsonable(decision):
            raise ValueError("CBSC-LR01 decision descriptors do not reconstruct")
        expected_audits = {
            "preflight_valid": True, "complete_competence_panel": True,
            "competence_numeric_health": competence_numeric_health,
            "complete_main_panel": True, "main_numeric_health": main_numeric_health,
            "update_zero_common": update_zero_all,
            "direct_pair_parity": direct_parity_all,
            "paired_work_parity": paired_work_all,
        }
        if dict(audits) != expected_audits:
            raise ValueError("CBSC-LR01 complete audit map does not reconstruct")
        valid = all(value is True for value in expected_audits.values())
        expected_branch = select_branch(
            decision, valid=valid, raw_competent=True, no_resolvable_headroom=no_headroom,
            structured_endpoint_gate=endpoint,
        )
        if result["branch"] != expected_branch:
            raise ValueError("CBSC-LR01 branch does not reconstruct")
    expected_witness = next((name for name in audit_order if audits[name] is False), None)
    if result["first_failing_witness"] != expected_witness:
        raise ValueError("CBSC-LR01 first failing witness mismatch")
    work = result["work"]
    if not isinstance(work, Mapping) or work.get("competence_optimizer_steps") != 2048 or work.get("threads") != 1:
        raise ValueError("CBSC-LR01 work totals mismatch")
    expected_main_steps = 0 if main == [] else 4608
    if work.get("main_optimizer_steps") != expected_main_steps:
        raise ValueError("CBSC-LR01 main work total mismatch")
    resource = result["resource"]
    if (
        not isinstance(resource, Mapping)
        or type(resource.get("wall_seconds")) is not float
        or not math.isfinite(resource["wall_seconds"])
        or not 0 <= resource["wall_seconds"] <= 1800
        or type(resource.get("peak_rss_bytes")) is not int
        or not 0 < resource["peak_rss_bytes"] <= 4 * 1024**3
    ):
        raise ValueError("CBSC-LR01 resource receipt mismatch")
    text = canonical_bytes(dict(result)).lower()
    for forbidden in (b"resampling", b"population_inference", b"model_state", b"optimizer_state"):
        if forbidden in text:
            raise ValueError(f"forbidden CBSC-LR01 result field: {forbidden.decode()}")
    try:
        import jsonschema
        schema_path = Path(__file__).with_name("schemas") / "cbsc_lr01_complete_result_v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(to_jsonable(result))
    except ImportError as error:
        raise RuntimeError("jsonschema is required for complete-result validation") from error


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported CBSC-LR01 serialization type: {type(value).__name__}")


def _atomic_create_only_bytes(target: Path, payload: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"CBSC-LR01 publication is create-only: {target}")
    temporary: Path | None = None
    for counter in range(1024):
        candidate = target.with_name(f".{target.name}.cbsc-lr01-tmp-{os.getpid()}-{counter}")
        try:
            descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        temporary = candidate
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            candidate.unlink(missing_ok=True)
            raise
        break
    if temporary is None:
        raise FileExistsError("could not allocate bounded CBSC-LR01 publication temporary")
    try:
        os.link(temporary, target)
    except FileExistsError as error:
        raise FileExistsError(f"CBSC-LR01 publication is create-only: {target}") from error
    finally:
        temporary.unlink(missing_ok=True)
    return target


def publish_complete_result(path: str | os.PathLike[str], result: Mapping[str, Any]) -> Path:
    validate_complete_result(result)
    payload = canonical_bytes(result) + b"\n"
    if len(payload) > 128 * 1024**2:
        raise ValueError("CBSC-LR01 durable output exceeds 128 MiB")
    return _atomic_create_only_bytes(Path(path), payload)


__all__ = ["canonical_bytes", "publish_complete_result", "to_jsonable", "validate_complete_result"]
