"""V-K0D reference-arm digest report producer (A-VD-7, amendment frozen by
external ruling -- see `docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md`).

Produces the per-seed `reference_digest_report_path` witness
`scripts/analyze_vk0d_result.py` consumes for the REFERENCE arm: this module
is developed against that analyzer's ACTUAL, on-disk schema
(`validate_reference_digest_report_shape` / `compute_reference_conforms`),
not a paraphrase of it -- the analyzer is the frozen consumer, and every
field name and type below is copied from its validator rather than invented.

A-VD-7 REFERENCE_CONFORMS requires, per seed:

1. canonical SHA-256 of the final high-actor state_dict equals the valid
   V-K0B digest;
2. canonical SHA-256 of the final high-value state_dict equals the valid
   V-K0B digest;
3. canonical SHA-256 of the shared high-optimizer state equals the valid
   V-K0B digest;
4. resolved training semantics and actual exposure match, and the canonical
   path consumes no order-stream draw;
5. the frozen evaluation reaches its competence floors (evaluated once at
   the arm level, outside this module's scope).

This module realizes conditions 1-4 for one seed. The three digests (1-3)
are computed by ONE shared canonical procedure -- name/shape/dtype/exact
bytes for the state_dicts, plus the parameter-name mapping, per-parameter-
group hyperparameters and per-parameter optimizer state for the optimizer --
applied identically to the V-K0D reference checkpoint and the corresponding
V-K0B checkpoint. There is NO tolerance and NO fallback: bytes equal or they
do not. `semantics_match` and `exposure_match` (condition 4) are computed by
re-running the exact frozen validators the V-K0D launcher itself uses
(`scripts/run_vk0d_training.validate_resolved`,
`scripts/run_vk0b_training.validate_identical_contract_identities`) against
the run's resolved manifest and actual-exposure block; any validator
exception counts as a non-match, never a silently-assumed pass.
`order_stream_draws_consumed` is read from the run's durable A-VD-4
order-exposure block: zero when `order_stream_version` is the frozen
"no draw" identity and no reversed sequence was realized, otherwise the
block's own completed-sequence total. A missing or structurally malformed
input (checkpoint, exposure block, manifest) is always a hard refusal --
never a silently-assumed value.

The output report carries the analyzer's own required flat field set
(`actor_state_dict_sha256`, `value_state_dict_sha256`,
`optimizer_state_sha256`, `vk0b_actor_state_dict_sha256`,
`vk0b_value_state_dict_sha256`, `vk0b_optimizer_state_sha256`,
`semantics_match`, `exposure_match`, `order_stream_draws_consumed`,
`checkpoint_hash`) plus informational extras the analyzer's validator does
not enforce a closed key set against (verified directly against
`validate_reference_digest_report_shape`, which only ever reads named
fields via `.get`, never checks `set(report.keys())`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch

from ha_ctse_process.standalone_agent import (
    VK0D_ORDER_STREAM_NONE,
    VK0D_ORDER_STREAM_VERSION,
)
from scripts.run_vk0b_training import validate_identical_contract_identities
from scripts.run_vk0d_training import validate_resolved as validate_vk0d_resolved


class Vk0dReferenceDigestRefusalError(Exception):
    """A required input file is missing, unreadable, or structurally
    malformed. Raised before any report is written -- never silently
    defaulted."""


# =============================================================================
# Hash helpers
# =============================================================================


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path, tag: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Vk0dReferenceDigestRefusalError(f"{tag}_UNREADABLE: {path}: {exc}") from exc


# =============================================================================
# Canonical state/optimizer digest -- byte-for-byte the same procedure as the
# recipe that produced the recorded witness digests on the truncated run
# (name|shape|dtype|exact-bytes, sorted names, optimizer state resolved to
# parameter names via the actor-then-value registration order). Parity with
# that recipe is proven directly in the test suite, never merely asserted.
# =============================================================================


def canonical_state_dict_digest(state_dict) -> str:
    h = hashlib.sha256()
    for name in sorted(state_dict.keys()):
        t = state_dict[name]
        h.update(name.encode("utf-8"))
        h.update(b"|")
        h.update(str(tuple(t.shape)).encode("utf-8"))
        h.update(b"|")
        h.update(str(t.dtype).encode("utf-8"))
        h.update(b"|")
        h.update(t.detach().cpu().contiguous().numpy().tobytes())
        h.update(b"\n")
    return h.hexdigest()


def canonical_optimizer_digest(opt_state_dict, param_names: list[str]) -> str:
    """`opt_state_dict` is an Adam-shaped state_dict: {"state": {idx:
    {...}}, "param_groups": [{"params": [idx...], hyperparams...}]}. Index
    resolves to a parameter name via `param_names` (the actor-then-value
    parameter order the checkpoint's own key layout registers), never a
    transient Python object identity."""
    h = hashlib.sha256()
    for gi, group in enumerate(opt_state_dict["param_groups"]):
        h.update(f"group{gi}".encode("utf-8"))
        for key in sorted(group.keys()):
            if key == "params":
                names = [param_names[int(i)] for i in group["params"]]
                h.update(b"params=" + "|".join(names).encode("utf-8"))
            else:
                h.update(f"{key}={group[key]!r}".encode("utf-8"))
            h.update(b";")
        h.update(b"\n")
    for idx in sorted(opt_state_dict["state"].keys()):
        h.update(param_names[int(idx)].encode("utf-8"))
        entry = opt_state_dict["state"][idx]
        for key in sorted(entry.keys()):
            value = entry[key]
            h.update(f"|{key}=".encode("utf-8"))
            if torch.is_tensor(value):
                h.update(str(tuple(value.shape)).encode("utf-8"))
                h.update(str(value.dtype).encode("utf-8"))
                h.update(value.detach().cpu().contiguous().numpy().tobytes())
            else:
                h.update(repr(value).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def load_checkpoint_components(path: Path) -> tuple[Any, Any, Any, list[str]]:
    """The A-VD-7 extraction -- high-actor, high-value, and shared
    high-optimizer state, plus the actor-then-value parameter-name order the
    optimizer's index-keyed state resolves against -- applied identically
    whichever side (V-K0D reference or V-K0B) the checkpoint came from, per
    A-VD-7's "ONE shared procedure applied to both sides." Mirrors
    `ha_ctse_process/train.py`'s own `weights_only=False` convention for
    project-owned local checkpoint artifacts (registered runtime ledger and
    NumPy RNG state cannot decode under the PyTorch 2.6 `weights_only=True`
    default)."""
    if not path.is_file():
        raise Vk0dReferenceDigestRefusalError(f"CHECKPOINT_FILE_MISSING: {path}")
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if (
        not isinstance(checkpoint, dict)
        or "high" not in checkpoint
        or checkpoint.get("r30_high_value") is None
        or "high_opt" not in checkpoint
    ):
        raise Vk0dReferenceDigestRefusalError(
            f"CHECKPOINT_MISSING_R30_COMPONENTS: {path} lacks high/r30_high_value/high_opt"
        )
    actor = checkpoint["high"]
    value = checkpoint["r30_high_value"]
    high_opt = checkpoint["high_opt"]
    param_names = [f"actor.{n}" for n in actor.keys()] + [f"value.{n}" for n in value.keys()]
    return actor, value, high_opt, param_names


def digest_checkpoint(path: Path) -> dict[str, str]:
    actor, value, high_opt, param_names = load_checkpoint_components(path)
    return {
        "actor": canonical_state_dict_digest(actor),
        "value": canonical_state_dict_digest(value),
        "optimizer": canonical_optimizer_digest(high_opt, param_names),
    }


# =============================================================================
# order_stream_draws_consumed -- the run's durable A-VD-4 order-exposure
# block (the `actual_exposure` object `ha_ctse_process/train.py`'s
# `run_manifest.json` writes, echoed verbatim by
# `scripts/run_vk0d_training.py`'s `order_exposure` launcher field). Exactly
# two stream identities are admissible in this frozen contract
# (`VK0D_ORDER_STREAM_NONE` / `VK0D_ORDER_STREAM_VERSION`); anything else, or
# a structurally incomplete block, is a hard refusal -- never a silently
# defaulted zero.
# =============================================================================


def compute_order_stream_draws_consumed(block: Any) -> int:
    if not isinstance(block, dict):
        raise Vk0dReferenceDigestRefusalError(f"EXPOSURE_BLOCK_MALFORMED: not an object ({block!r})")
    stream_version = block.get("order_stream_version")
    if not isinstance(stream_version, str) or stream_version not in (
        VK0D_ORDER_STREAM_NONE,
        VK0D_ORDER_STREAM_VERSION,
    ):
        raise Vk0dReferenceDigestRefusalError(
            "EXPOSURE_BLOCK_MALFORMED: order_stream_version must be one of "
            f"{(VK0D_ORDER_STREAM_NONE, VK0D_ORDER_STREAM_VERSION)!r}, got {stream_version!r}"
        )

    def _int_entry(key: str) -> int:
        entry = block.get(key)
        value = entry.get("value") if isinstance(entry, dict) else None
        if not isinstance(value, int) or isinstance(value, bool):
            raise Vk0dReferenceDigestRefusalError(
                f"EXPOSURE_BLOCK_MALFORMED: {key} missing or not a {{value, source}} int entry ({entry!r})"
            )
        return int(value)

    reversed_count = _int_entry("completed_reversed_sequences")
    total = _int_entry("completed_sequence_total")

    if stream_version == VK0D_ORDER_STREAM_NONE:
        if reversed_count != 0:
            raise Vk0dReferenceDigestRefusalError(
                f"EXPOSURE_BLOCK_INCONSISTENT: order_stream_version={VK0D_ORDER_STREAM_NONE!r} "
                f"but completed_reversed_sequences={reversed_count} != 0"
            )
        return 0
    return total


# =============================================================================
# semantics_match / exposure_match (A-VD-7 condition 4) -- re-run the exact
# frozen launcher validators rather than reimplementing their checks.
# =============================================================================


def _extract_manifest_identity(manifest: dict) -> tuple[dict, str, bool, int]:
    resolved = manifest.get("resolved")
    arm = manifest.get("arm")
    nonscientific = manifest.get("nonscientific")
    if not isinstance(resolved, dict):
        raise Vk0dReferenceDigestRefusalError("MANIFEST_MALFORMED: resolved must be an object")
    if not isinstance(arm, str) or not arm:
        raise Vk0dReferenceDigestRefusalError("MANIFEST_MALFORMED: arm must be a non-empty str")
    if not isinstance(nonscientific, bool):
        raise Vk0dReferenceDigestRefusalError("MANIFEST_MALFORMED: nonscientific must be a bool")
    seed = resolved.get("training_seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise Vk0dReferenceDigestRefusalError("MANIFEST_MALFORMED: resolved.training_seed must be an int")
    return resolved, arm, nonscientific, int(seed)


def compute_semantics_match(resolved: dict, seed: int, nonscientific: bool, arm: str) -> tuple[bool, list[str]]:
    try:
        violations = validate_vk0d_resolved(resolved, seed, nonscientific, arm)
    except Exception as exc:  # noqa: BLE001 -- any validator exception is a non-match, per PM ruling.
        return False, [f"VALIDATE_RESOLVED_RAISED: {exc!r}"]
    return (len(violations) == 0), list(violations)


def compute_exposure_match(block: Any, nonscientific: bool) -> tuple[bool, list[str]]:
    if nonscientific:
        # `validate_identical_contract_identities` is scoped to scientific
        # runs (its own docstring: "not the frozen contract" otherwise); a
        # V-K0D reference run is always scientific in practice, but this
        # mirrors the launcher's own `scientific and isinstance(block, dict)`
        # gate rather than asserting a check that does not apply.
        return True, []
    try:
        violations = validate_identical_contract_identities(block)
    except Exception as exc:  # noqa: BLE001 -- any validator exception is a non-match, per PM ruling.
        return False, [f"VALIDATE_IDENTICAL_CONTRACT_RAISED: {exc!r}"]
    return (len(violations) == 0), list(violations)


# =============================================================================
# Report assembly
# =============================================================================


def build_report(
    *,
    vk0d_checkpoint: Path,
    vk0b_checkpoint: Path,
    exposure_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    vk0d_digests = digest_checkpoint(vk0d_checkpoint)
    vk0b_digests = digest_checkpoint(vk0b_checkpoint)

    if not exposure_path.is_file():
        raise Vk0dReferenceDigestRefusalError(f"EXPOSURE_FILE_MISSING: {exposure_path}")
    exposure_block = _read_json(exposure_path, "EXPOSURE_FILE")

    if not manifest_path.is_file():
        raise Vk0dReferenceDigestRefusalError(f"MANIFEST_FILE_MISSING: {manifest_path}")
    manifest = _read_json(manifest_path, "MANIFEST_FILE")

    order_stream_draws_consumed = compute_order_stream_draws_consumed(exposure_block)
    resolved, arm, nonscientific, seed = _extract_manifest_identity(manifest)
    semantics_match, semantics_violations = compute_semantics_match(resolved, seed, nonscientific, arm)
    exposure_match, exposure_violations = compute_exposure_match(exposure_block, nonscientific)

    checkpoint_hash = _sha256_file(vk0d_checkpoint)
    vk0b_checkpoint_hash = _sha256_file(vk0b_checkpoint)

    actor_equal = vk0d_digests["actor"] == vk0b_digests["actor"]
    value_equal = vk0d_digests["value"] == vk0b_digests["value"]
    optimizer_equal = vk0d_digests["optimizer"] == vk0b_digests["optimizer"]

    return {
        # Frozen fields `scripts/analyze_vk0d_result.py`'s
        # `validate_reference_digest_report_shape` requires verbatim.
        "actor_state_dict_sha256": vk0d_digests["actor"],
        "value_state_dict_sha256": vk0d_digests["value"],
        "optimizer_state_sha256": vk0d_digests["optimizer"],
        "vk0b_actor_state_dict_sha256": vk0b_digests["actor"],
        "vk0b_value_state_dict_sha256": vk0b_digests["value"],
        "vk0b_optimizer_state_sha256": vk0b_digests["optimizer"],
        "semantics_match": semantics_match,
        "exposure_match": exposure_match,
        "order_stream_draws_consumed": order_stream_draws_consumed,
        "checkpoint_hash": checkpoint_hash,
        # Informational extras -- inert to the frozen consumer (verified:
        # `validate_reference_digest_report_shape` never checks
        # `set(report.keys())`).
        "seed": seed,
        "arm": arm,
        "vk0d_checkpoint_path": str(vk0d_checkpoint),
        "vk0b_checkpoint_path": str(vk0b_checkpoint),
        "vk0b_checkpoint_sha256": vk0b_checkpoint_hash,
        "components_equal": {
            "high_actor": actor_equal,
            "high_value": value_equal,
            "high_optimizer": optimizer_equal,
        },
        "all_digests_equal": bool(actor_equal and value_equal and optimizer_equal),
        "semantics_violations": semantics_violations,
        "exposure_violations": exposure_violations,
    }


def write_report_once(out_path: Path, report: dict[str, Any]) -> None:
    if out_path.exists():
        raise Vk0dReferenceDigestRefusalError(f"OUTPUT_ALREADY_EXISTS: {out_path} (write-once)")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(out_path)


# =============================================================================
# CLI
# =============================================================================


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vk0d-checkpoint", dest="vk0d_checkpoint", required=True)
    parser.add_argument("--vk0b-checkpoint", dest="vk0b_checkpoint", required=True)
    parser.add_argument(
        "--exposure",
        dest="exposure",
        required=True,
        help="Path to the run's actual_exposure JSON block (A-VD-4 durable order-exposure record).",
    )
    parser.add_argument(
        "--manifest",
        dest="manifest",
        required=True,
        help="Path to the V-K0D launcher's resolved preflight manifest (vk0d_preflight_manifest.json).",
    )
    parser.add_argument("--out", dest="out", required=True)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    try:
        report = build_report(
            vk0d_checkpoint=Path(args.vk0d_checkpoint),
            vk0b_checkpoint=Path(args.vk0b_checkpoint),
            exposure_path=Path(args.exposure),
            manifest_path=Path(args.manifest),
        )
        write_report_once(Path(args.out), report)
    except Vk0dReferenceDigestRefusalError as exc:
        print(f"VK0D_REFERENCE_DIGEST_REFUSED={exc}")
        raise SystemExit(1) from exc

    print(f"VK0D_REFERENCE_DIGEST_OUT={args.out}")
    print(f"VK0D_REFERENCE_DIGEST_ALL_EQUAL={report['all_digests_equal']}")
    print(f"VK0D_REFERENCE_DIGEST_SEMANTICS_MATCH={report['semantics_match']}")
    print(f"VK0D_REFERENCE_DIGEST_EXPOSURE_MATCH={report['exposure_match']}")
    print(f"VK0D_REFERENCE_DIGEST_ORDER_STREAM_DRAWS_CONSUMED={report['order_stream_draws_consumed']}")


if __name__ == "__main__":
    main()
