"""Source-only EOCIV-A8 exact-ledger constructibility audit.

The module never imports or calls the EOCIV runtime.  It binds a Git source
snapshot, parses the two registered host surfaces as text/AST, and evaluates a
literal interface manifest when (and only when) that manifest is present in
the accepted source.  Missing seams therefore fail closed instead of being
filled by an execution probe or by retrospective evidence.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


TREATMENT_ID = "EOCIV-A8-EXACT-DYADIC-LEDGER-IDENTIFIABILITY-PROOF"
DESIGN_ID = "DESIGN-2026-08-10-EOCIV-A8-EXACT-DYADIC-LEDGER-IDENTIFIABILITY-V1"
TARGET_VERSION_ID = "CAND-VAP-EOCIV-LITE@adversarial-revision-v8"
MANIFEST_SYMBOL = "A8_EXACT_DYADIC_INTERFACE_MANIFEST"
EXPECTED_PAYLOAD_SHA256 = "9b04f7fac747a23c0985c940138386d2eba46d60d25e72ec4b2eea70f03b2409"

HOST_SOURCE_PATHS = (
    "experiments/candidates/eociv_lite/sibling_env.py",
    "experiments/candidates/eociv_lite/actuation_runtime.py",
)

BRANCH_PRECEDENCE = (
    "A8_INVALID_SOURCE_OR_ACTIVITY_CONTRACT",
    "A8_REWARD_INTERFACE_OR_EXACT_DECODER_UNIDENTIFIED",
    "A8_FORK_TAPE_OR_MASK_IDENTITY_UNIDENTIFIED",
    "A8_PHASE_ENDPOINT_OR_FIREWALL_UNIDENTIFIED",
    "A8_FRESHNESS_OR_IDENTITY_FAILURE",
    "A8_EXACT_DYADIC_LEDGER_AND_CAUSAL_PANEL_CONSTRUCTIBLE",
)

CERTIFICATE_ORDER = (
    "reward_interface_manifest",
    "capture_site_census",
    "dtype_decoder",
    "fork_tape_dependency",
    "mask_raw_bit_identity",
    "phase_count_oracle",
    "endpoint_context_no_target_outcome_firewall",
    "b6_b7_freshness",
)

ZERO_ACTIVITY_LEDGER = {
    "registered_audits": 1,
    "environment_episodes": 0,
    "environment_transitions": 0,
    "policy_calls": 0,
    "learner_calls": 0,
    "trainer_calls": 0,
    "optimizer_calls": 0,
    "evaluations": 0,
    "model_fits": 0,
    "checkpoint_reconstructions": 0,
    "rng_draws": 0,
    "retries_rescues_sweeps": 0,
    "pool_units": 0,
}

HISTORIES = {
    "H8A": {"history_index": 0, "initialization_seed": 180001, "trainer_seed": 180011},
    "H8B": {"history_index": 1, "initialization_seed": 180002, "trainer_seed": 180012},
}
PROFILES = ("train_4_3_6_5", "train_5_3_7_6", "train_6_4_8_6")
TRAINING_ROOTS = {
    "H8A/P0": (181001, 181002, 181003),
    "H8A/P1": (181011, 181012, 181013),
    "H8A/P2": (181021, 181022, 181023),
    "H8B/P0": (182001, 182002, 182003),
    "H8B/P1": (182011, 182012, 182013),
    "H8B/P2": (182021, 182022, 182023),
}
HELDOUT_ROOTS = {
    "H8A/P0": (183001, 183002),
    "H8A/P1": (183011, 183012),
    "H8A/P2": (183021, 183022),
    "H8B/P0": (184001, 184002),
    "H8B/P1": (184011, 184012),
    "H8B/P2": (184021, 184022),
}
SHOCK_ORDER = (("A", "A"), ("A", "B"), ("B", "A"), ("B", "B"))
TAPE_ADDRESS_FIELDS = (
    "family",
    "history",
    "profile",
    "root_id",
    "shock_index",
    "timestep",
    "agent_id",
    "draw_kind",
    "draw_index",
)
DEEP_STATE_FIELDS = (
    "environment",
    "wrapper",
    "lifecycle",
    "roster",
    "actor",
    "value",
    "native_gate",
    "recurrent",
    "counter",
    "termination",
    "rng",
)
MASK_TRACE_CHANNELS = (
    "tape_addresses",
    "observations",
    "recurrent_inputs",
    "actions",
    "environment_state",
    "wrapper_state",
    "rewards",
    "done_flags",
)
CONTEXT_FIELDS = ("profile_id", "lifecycle_class", "eligible")
CONTEXT_EXCLUSIONS = ("root", "shock", "arm", "reward", "future_state")
SUPPORTED_DTYPES = ("binary16", "bfloat16", "binary32", "binary64", "integer")
FLOAT_FORMATS = {
    "binary16": (10, 15, 31),
    "bfloat16": (7, 127, 255),
    "binary32": (23, 127, 255),
    "binary64": (52, 1023, 2047),
}
PREDECESSOR_ANCHORS = {
    "b7_source_commit": "8f3bba4a8e86a4706bd7510f070f97377ff873ec",
    "b7_publication_commit": "c95772c842175ca8c8b14db2815414aaa09bf8c8",
}
FORBIDDEN_PREDECESSOR_TOKENS = (
    "actor_anchored_critic_clip_root_cross",
    "one_step_root_partition_frozen_history",
    "EOCIV_B7_ONE_STEP_ROOT_PARTITION_FROZEN_HISTORY_RESULT",
    "B6_ARTIFACT",
    "B7_ARTIFACT",
)


class ContractError(ValueError):
    """A frozen A8 contract value is invalid."""


@dataclass(frozen=True)
class Certificate:
    name: str
    passed: bool
    source_digest: str
    witnesses: tuple[str, ...]
    failures: tuple[str, ...]


@dataclass(frozen=True)
class SourceBinding:
    passed: bool
    source_root: str
    expected_commit: str
    actual_commit: str | None
    cwd: str
    runtime_core_file: str
    runtime_runner_file: str
    audited_paths: tuple[str, ...]
    file_sha256: Mapping[str, str]
    failures: tuple[str, ...]


@dataclass(frozen=True)
class SourceSnapshot:
    root: Path
    texts: Mapping[str, str]
    raw_bytes: Mapping[str, bytes]
    digest: str
    manifest: Mapping[str, Any] | None
    manifest_locator: str | None
    manifest_failures: tuple[str, ...]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _normal(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def verify_source_binding(
    *,
    source_root: Path,
    expected_commit: str,
    cwd: Path,
    audited_paths: Sequence[str],
    runtime_core_file: Path,
    runtime_runner_file: Path,
    core_relative_path: str,
    runner_relative_path: str,
) -> SourceBinding:
    root = source_root.resolve()
    failures: list[str] = []
    actual_commit: str | None = None
    file_hashes: dict[str, str] = {}

    top = _git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        failures.append("source_root_is_not_a_git_worktree")
    else:
        observed_top = Path(top.stdout.decode("utf-8").strip()).resolve()
        if _normal(observed_top) != _normal(root):
            failures.append("source_root_does_not_equal_git_toplevel")

    head = _git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        failures.append("source_head_unavailable")
    else:
        actual_commit = head.stdout.decode("ascii").strip().lower()
        if actual_commit != expected_commit.lower():
            failures.append("source_head_mismatch")

    if _normal(cwd) != _normal(root):
        failures.append("cwd_not_bound_to_source_root")
    if _normal(runtime_core_file) != _normal(root / core_relative_path):
        failures.append("runtime_core_file_not_bound_to_source_root")
    if _normal(runtime_runner_file) != _normal(root / runner_relative_path):
        failures.append("runtime_runner_file_not_bound_to_source_root")

    for relative in audited_paths:
        path = (root / relative).resolve()
        if not _normal(path).startswith(_normal(root) + os.sep):
            failures.append(f"path_escape:{relative}")
            continue
        if not path.is_file():
            failures.append(f"missing_source_path:{relative}")
            continue
        raw = path.read_bytes()
        file_hashes[relative] = sha256_bytes(raw)
        tracked = _git(root, "ls-files", "--error-unmatch", "--", relative)
        if tracked.returncode != 0:
            failures.append(f"untracked_source_path:{relative}")
            continue
        index_blob = _git(root, "rev-parse", f"HEAD:{relative}")
        working_blob = _git(root, "hash-object", "--path", relative, relative)
        if index_blob.returncode != 0 or working_blob.returncode != 0:
            failures.append(f"git_blob_binding_unavailable:{relative}")
        elif index_blob.stdout.strip() != working_blob.stdout.strip():
            failures.append(f"working_bytes_not_bound_to_head:{relative}")

    return SourceBinding(
        passed=not failures,
        source_root=str(root),
        expected_commit=expected_commit.lower(),
        actual_commit=actual_commit,
        cwd=str(cwd.resolve()),
        runtime_core_file=str(runtime_core_file.resolve()),
        runtime_runner_file=str(runtime_runner_file.resolve()),
        audited_paths=tuple(audited_paths),
        file_sha256=file_hashes,
        failures=tuple(failures),
    )


def _literal_manifest(tree: ast.AST) -> Mapping[str, Any] | None:
    found: list[Mapping[str, Any]] = []
    for node in getattr(tree, "body", ()):
        names: tuple[str, ...] = ()
        value: ast.AST | None = None
        if isinstance(node, ast.Assign):
            names = tuple(t.id for t in node.targets if isinstance(t, ast.Name))
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = (node.target.id,)
            value = node.value
        if MANIFEST_SYMBOL in names and value is not None:
            literal = ast.literal_eval(value)
            if not isinstance(literal, dict):
                raise ContractError(f"{MANIFEST_SYMBOL} must be a literal dict")
            found.append(literal)
    if len(found) > 1:
        raise ContractError(f"duplicate {MANIFEST_SYMBOL} assignments")
    return found[0] if found else None


def read_source_snapshot(root: Path, source_paths: Sequence[str]) -> SourceSnapshot:
    texts: dict[str, str] = {}
    raw_bytes: dict[str, bytes] = {}
    manifests: list[tuple[str, Mapping[str, Any]]] = []
    failures: list[str] = []
    for relative in source_paths:
        path = root / relative
        if not path.is_file():
            failures.append(f"missing_source:{relative}")
            continue
        raw = path.read_bytes()
        raw_bytes[relative] = raw
        try:
            text = raw.decode("utf-8")
            tree = ast.parse(text, filename=relative)
            manifest = _literal_manifest(tree)
        except (UnicodeDecodeError, SyntaxError, ValueError, TypeError) as exc:
            failures.append(f"unparseable_source:{relative}:{type(exc).__name__}")
            continue
        texts[relative] = text
        if manifest is not None:
            manifests.append((relative, manifest))
    if len(manifests) > 1:
        failures.append("multiple_interface_manifests")
    manifest = manifests[0][1] if len(manifests) == 1 else None
    locator = manifests[0][0] if len(manifests) == 1 else None
    digest_material = b"".join(
        relative.encode("utf-8") + b"\0" + raw_bytes[relative] + b"\0"
        for relative in sorted(raw_bytes)
    )
    return SourceSnapshot(
        root=root.resolve(),
        texts=texts,
        raw_bytes=raw_bytes,
        digest=sha256_bytes(digest_material),
        manifest=manifest,
        manifest_locator=locator,
        manifest_failures=tuple(failures),
    )


def decode_float_bits(format_name: str, raw_bits: int) -> dict[str, Any]:
    """Decode one finite IEEE-style bit pattern as N * 2^-1074 exactly."""
    if format_name not in FLOAT_FORMATS:
        raise ContractError(f"unsupported float format: {format_name}")
    p, bias, e_max = FLOAT_FORMATS[format_name]
    exponent_bits = int(math.log2(e_max + 1))
    width = 1 + exponent_bits + p
    if not isinstance(raw_bits, int) or isinstance(raw_bits, bool):
        raise ContractError("raw bits must be an integer")
    if not 0 <= raw_bits < (1 << width):
        raise ContractError("raw bits outside declared format width")
    sign = (raw_bits >> (exponent_bits + p)) & 1
    exponent = (raw_bits >> p) & e_max
    fraction = raw_bits & ((1 << p) - 1)
    if exponent == e_max:
        raise ContractError("nonfinite float representation")
    signed = -1 if sign else 1
    if exponent == 0:
        n = signed * fraction * (1 << (1075 - bias - p))
    else:
        n = signed * ((1 << p) + fraction) * (1 << (1074 + exponent - bias - p))
    return {
        "format": format_name,
        "raw_bits": raw_bits,
        "sign": sign,
        "exponent": exponent,
        "fraction": fraction,
        "integer_n": n,
        "scale_power": -1074,
        "signed_zero": bool(exponent == 0 and fraction == 0 and sign == 1),
    }


def decode_integer(value: int) -> dict[str, Any]:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ContractError("integer decoder rejects non-integers and booleans")
    return {"integer_n": value * (1 << 1074), "scale_power": -1074}


def _source_line_hash(snapshot: SourceSnapshot, locator: str) -> tuple[bool, str]:
    try:
        relative, line_text, expected = locator.split("|", 2)
        line_number = int(line_text)
        line = snapshot.texts[relative].splitlines()[line_number - 1]
    except (ValueError, KeyError, IndexError):
        return False, f"invalid_source_witness:{locator}"
    observed = sha256_bytes(line.encode("utf-8"))
    if observed != expected:
        return False, f"source_witness_hash_mismatch:{relative}:{line_number}"
    return True, f"source_witness:{relative}:{line_number}:{observed}"


def _require_witnesses(
    snapshot: SourceSnapshot, manifest: Mapping[str, Any], section: str
) -> tuple[list[str], list[str]]:
    witnesses: list[str] = []
    failures: list[str] = []
    raw = manifest.get("source_witnesses", {}).get(section, ())
    if not isinstance(raw, list) or not raw:
        return witnesses, [f"missing_source_witnesses:{section}"]
    for locator in raw:
        if not isinstance(locator, str):
            failures.append(f"non_string_source_witness:{section}")
            continue
        passed, detail = _source_line_hash(snapshot, locator)
        (witnesses if passed else failures).append(detail)
    return witnesses, failures


def _certificate(
    name: str, snapshot: SourceSnapshot, witnesses: Iterable[str], failures: Iterable[str]
) -> Certificate:
    failures_tuple = tuple(failures)
    return Certificate(
        name=name,
        passed=not failures_tuple,
        source_digest=snapshot.digest,
        witnesses=tuple(witnesses),
        failures=failures_tuple,
    )


def _manifest_section(manifest: Mapping[str, Any] | None, name: str) -> tuple[Mapping[str, Any], list[str]]:
    if manifest is None:
        return {}, ["accepted_source_has_no_literal_a8_interface_manifest"]
    section = manifest.get(name)
    if not isinstance(section, dict):
        return {}, [f"missing_or_nonobject_manifest_section:{name}"]
    return section, []


def certify_reward_interface(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "reward_interface")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "reward_interface")
        witnesses += w
        failures += f
    if section:
        if section.get("primary_key") != ["episode_key", "timestep", "reward_slot"]:
            failures.append("primary_key_is_not_value_free_exact_tuple")
        payload_fields = section.get("payload_fields")
        if not isinstance(payload_fields, list) or not {"source_dtype", "value_encoding"}.issubset(payload_fields):
            failures.append("dtype_or_value_encoding_not_payload")
        if not bool(section.get("closed_manifest")):
            failures.append("reward_leaf_manifest_not_closed")
        leaves = section.get("leaves")
        if not isinstance(leaves, list) or not leaves:
            failures.append("reachable_reward_leaf_census_empty")
            leaves = []
        slots: list[str] = []
        dtypes: set[str] = set()
        for index, leaf in enumerate(leaves):
            if not isinstance(leaf, dict):
                failures.append(f"leaf_not_object:{index}")
                continue
            slot = leaf.get("reward_slot")
            dtype = leaf.get("source_dtype")
            if not isinstance(slot, str) or not slot:
                failures.append(f"missing_reward_slot:{index}")
            else:
                slots.append(slot)
            if dtype not in SUPPORTED_DTYPES:
                failures.append(f"unsupported_reachable_dtype:{dtype}")
            else:
                dtypes.add(dtype)
        if len(slots) != len(set(slots)):
            failures.append("duplicate_reward_slot_in_manifest")
        reachable = section.get("reachable_dtypes")
        if not isinstance(reachable, list) or set(reachable) != dtypes:
            failures.append("reachable_dtype_census_not_exact")
        if section.get("downstream_reward_shaping") not in ([], None):
            failures.append("downstream_reward_shaping_outside_manifest")
        witnesses.extend((f"reward_leaf_count:{len(leaves)}", f"reachable_dtypes:{sorted(dtypes)}"))
    failures.extend(snapshot.manifest_failures)
    return _certificate("reward_interface_manifest", snapshot, witnesses, failures)


def certify_capture_sites(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "reward_interface")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "capture_sites")
        witnesses += w
        failures += f
    leaves = section.get("leaves", []) if section else []
    if not isinstance(leaves, list) or not leaves:
        failures.append("no_capture_site_census")
        leaves = []
    capture_ids: list[str] = []
    for index, leaf in enumerate(leaves):
        if not isinstance(leaf, dict):
            continue
        capture_id = leaf.get("capture_site")
        if not isinstance(capture_id, str) or not capture_id:
            failures.append(f"missing_capture_site:{index}")
        else:
            capture_ids.append(capture_id)
        for field in ("after_final_wrapper", "before_cast", "before_reduction", "exactly_once", "raw_bits_available", "native_nonmutation"):
            if leaf.get(field) is not True:
                failures.append(f"capture_boundary_false:{index}:{field}")
    if len(capture_ids) != len(set(capture_ids)):
        failures.append("duplicate_capture_site")
    if section and section.get("primary_key_cardinality") != "one_per_emitted_scalar":
        failures.append("primary_key_uniqueness_not_proved")
    witnesses.append(f"capture_site_count:{len(capture_ids)}")
    return _certificate("capture_site_census", snapshot, witnesses, failures)


def certify_dtype_decoder(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "reward_interface")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "dtype_decoder")
        witnesses += w
        failures += f
    if section:
        if section.get("decoder") != "exact_integer_n_times_2^-1074":
            failures.append("exact_dyadic_decoder_not_selected")
        aggregation = section.get("aggregation")
        if not isinstance(aggregation, dict):
            failures.append("aggregation_metadata_missing")
        else:
            required = {
                "claim_values": "integer_ledger_only",
                "means": "numerator_count_pairs",
                "comparisons": "cross_multiplication",
                "squared_scale_power": -2148,
                "float_aggregation": False,
                "tolerance": False,
            }
            for key, expected in required.items():
                if aggregation.get(key) != expected:
                    failures.append(f"aggregation_contract_mismatch:{key}")
        reachable = section.get("reachable_dtypes", [])
        if not isinstance(reachable, list):
            failures.append("reachable_dtypes_not_list")
        else:
            for dtype in reachable:
                if dtype not in SUPPORTED_DTYPES:
                    failures.append(f"decoder_does_not_cover:{dtype}")
    try:
        one_patterns = {
            "binary16": 0x3C00,
            "bfloat16": 0x3F80,
            "binary32": 0x3F800000,
            "binary64": 0x3FF0000000000000,
        }
        for dtype, bits in one_patterns.items():
            decoded = decode_float_bits(dtype, bits)
            if decoded["integer_n"] != 1 << 1074:
                failures.append(f"decoder_internal_one_failure:{dtype}")
        if decode_float_bits("binary16", 1)["integer_n"] != 1 << 1050:
            failures.append("decoder_internal_binary16_subnormal_failure")
        negative_zero = decode_float_bits("binary32", 0x80000000)
        if negative_zero["integer_n"] != 0 or not negative_zero["signed_zero"]:
            failures.append("decoder_internal_signed_zero_failure")
        if decode_integer(-3)["integer_n"] != -3 * (1 << 1074):
            failures.append("decoder_internal_integer_failure")
        for dtype, bits in (("binary16", 0x7C00), ("binary32", 0x7FC00000), ("binary64", 0x7FF0000000000000)):
            try:
                decode_float_bits(dtype, bits)
            except ContractError:
                continue
            failures.append(f"decoder_internal_nonfinite_accepted:{dtype}")
    except (ContractError, OverflowError) as exc:
        failures.append(f"decoder_internal_exception:{type(exc).__name__}")
    witnesses.append("decoder_self_test:finite_normals_subnormal_signed_zero_integer_nonfinite")
    return _certificate("dtype_decoder", snapshot, witnesses, failures)


def certify_fork_tape(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "fork_tape_mask")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "fork_tape")
        witnesses += w
        failures += f
    if section:
        if section.get("deep_state_fields") != list(DEEP_STATE_FIELDS):
            failures.append("deep_state_schema_incomplete_or_reordered")
        if section.get("deep_non_aliased") is not True or section.get("cross_arm_aliases") != []:
            failures.append("deep_fork_nonaliasing_unproved")
        tape = section.get("tape")
        if not isinstance(tape, dict):
            failures.append("tape_manifest_missing")
        else:
            if tape.get("address_fields") != list(TAPE_ADDRESS_FIELDS):
                failures.append("tape_address_not_exact")
            if tape.get("random_access") is not True:
                failures.append("tape_not_random_access")
            if tape.get("cursor_based") is not False:
                failures.append("cursor_or_consumption_dependent_tape")
            if tape.get("unlisted_stochastic_sources") != []:
                failures.append("unlisted_stochastic_source")
            if tape.get("global_or_unkeyed_draws") is not False:
                failures.append("global_or_unkeyed_draw")
        pipeline = section.get("semantic_pipeline")
        if not isinstance(pipeline, dict):
            failures.append("semantic_pipeline_missing")
        else:
            exact = {
                "correct": "CORRECT(payload)",
                "swapped": "SWAPPED(payload)",
                "reveal": "payload_s",
                "mask": "canonical_mask_token_independent_of_semantic",
                "other_semantic_sinks": [],
            }
            for key, expected in exact.items():
                if pipeline.get(key) != expected:
                    failures.append(f"semantic_pipeline_mismatch:{key}")
        witnesses.append("fork_fields_and_tape_address_exact")
    return _certificate("fork_tape_dependency", snapshot, witnesses, failures)


def certify_mask_identity(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "fork_tape_mask")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "mask_identity")
        witnesses += w
        failures += f
    mask = section.get("mask_identity") if section else None
    if not isinstance(mask, dict):
        failures.append("mask_identity_manifest_missing")
    else:
        if mask.get("trace_channels") != list(MASK_TRACE_CHANNELS):
            failures.append("mask_trace_channel_census_incomplete_or_reordered")
        if mask.get("raw_bit_equal_correct_swapped") is not True:
            failures.append("mask_raw_bit_identity_unproved")
        if mask.get("signed_zero_bits_diagnostic") is not True:
            failures.append("signed_zero_identity_not_diagnostic")
        if mask.get("fork_through_termination") is not True:
            failures.append("mask_identity_not_end_to_end")
        if mask.get("semantic_value_downstream_sinks") != []:
            failures.append("masked_semantic_value_leaks_downstream")
    witnesses.append("mask_trace_identity_channels_checked")
    return _certificate("mask_raw_bit_identity", snapshot, witnesses, failures)


def canonical_roster() -> dict[str, Any]:
    return {
        "histories": HISTORIES,
        "profiles": list(PROFILES),
        "training_roots": {key: list(value) for key, value in TRAINING_ROOTS.items()},
        "heldout_roots": {key: list(value) for key, value in HELDOUT_ROOTS.items()},
        "shock_order": [list(pair) for pair in SHOCK_ORDER],
        "shock_indexing": "zero-based 0,1,2,3 in published shock_order",
        "natural_shock_tape_seed": "3000000+10*root_id+shock_index",
        "action_noise_tape_seed": "5000000+10*root_id+shock_index",
        "natural_seed_span": "4810010..4840123",
        "action_seed_span": "6810010..6840123",
        "data_order": "lexicographic(history,profile,root,shock,gate,semantic)",
        "episode_horizon": 48,
        "root_overlap": "All 18 training roots and 12 held-out roots are distinct; any collision or post-freeze substitution fails.",
    }


def _root_seed_witnesses() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    roots = [root for values in (*TRAINING_ROOTS.values(), *HELDOUT_ROOTS.values()) for root in values]
    if len(roots) != 30 or len(roots) != len(set(roots)):
        failures.append("root_roster_collision_or_wrong_count")
    natural = [3_000_000 + 10 * root + shock for root in roots for shock in range(4)]
    action = [5_000_000 + 10 * root + shock for root in roots for shock in range(4)]
    if len(set(natural + action)) != 240:
        failures.append("derived_tape_seed_collision")
    if (min(natural), max(natural)) != (4_810_010, 4_840_123):
        failures.append("natural_seed_span_mismatch")
    if (min(action), max(action)) != (6_810_010, 6_840_123):
        failures.append("action_seed_span_mismatch")
    return [
        "roots:18_training_12_heldout_distinct",
        "derived_tapes:240_unique",
        f"observed_natural_seed_span:{min(natural)}..{max(natural)}",
        f"observed_action_seed_span:{min(action)}..{max(action)}",
    ], failures


def certify_phase_counts(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "phase_count_oracle")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "phase_count_oracle")
        witnesses += w
        failures += f
    roster_witnesses, roster_failures = _root_seed_witnesses()
    witnesses += roster_witnesses
    failures += roster_failures
    expected = {
        "roster": canonical_roster(),
        "training_units": 72,
        "training_native_natural_episodes": 72,
        "training_complementary_episodes": 72,
        "training_episodes": 144,
        "heldout_units": 48,
        "heldout_episodes": 192,
        "complete_episodes": 336,
        "transition_policy_call_ceiling": 16128,
        "native_learner_calls": 18,
        "native_optimizer_updates": 18,
        "exact_shadow_updates": 72,
        "sign_control_updates": 72,
        "native_anchors": 2,
        "training_semantic": "CORRECT_only",
        "evaluation_arms": ["REVEAL_CORRECT", "MASK_CORRECT", "REVEAL_SWAPPED", "MASK_SWAPPED"],
    }
    if section:
        for key, value in expected.items():
            if section.get(key) != value:
                failures.append(f"phase_count_literal_mismatch:{key}")
    witnesses.append("phase_counts:144_training_192_heldout_336_total")
    return _certificate("phase_count_oracle", snapshot, witnesses, failures)


def certify_endpoint_firewall(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "endpoint_firewall")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "endpoint_firewall")
        witnesses += w
        failures += f
    expected = {
        "native_endpoint_per_history": True,
        "history_specific_exact_accumulator": True,
        "history_specific_sign_control_accumulator": True,
        "context_fields": list(CONTEXT_FIELDS),
        "context_exclusions": list(CONTEXT_EXCLUSIONS),
        "finite_context_vocabulary_enumerated_before_outcomes": True,
        "native_gate_before_reward_or_future": True,
        "native_natural_only_updates_native": True,
        "complementary_ledger_only": True,
        "no_learning_between_pair_branches": True,
        "freeze_hash_endpoints_and_tables_before_heldout_rewards": True,
        "heldout_updates_endpoints": False,
        "missing_target_maps_all_endpoints_to_mask": True,
        "missing_target_retained_as_same_noop_episode": True,
        "missing_target_excluded": False,
        "endpoint_specific_evaluation_episode": False,
    }
    if section:
        for key, value in expected.items():
            if section.get(key) != value:
                failures.append(f"endpoint_firewall_literal_mismatch:{key}")
    witnesses.append("endpoint_context_no_target_and_outcome_firewall_checked")
    return _certificate("endpoint_context_no_target_outcome_firewall", snapshot, witnesses, failures)


def certify_freshness(snapshot: SourceSnapshot) -> Certificate:
    section, failures = _manifest_section(snapshot.manifest, "freshness")
    witnesses: list[str] = []
    if snapshot.manifest is not None:
        w, f = _require_witnesses(snapshot, snapshot.manifest, "freshness")
        witnesses += w
        failures += f
    if section:
        if section.get("treatment_id") != TREATMENT_ID:
            failures.append("treatment_identity_not_fresh_a8")
        if section.get("imports_predecessor_scientific_objects") != []:
            failures.append("predecessor_scientific_object_import_declared")
        if section.get("reconstructs_or_redecodes_predecessor") is not False:
            failures.append("predecessor_reconstruction_not_rejected")
        if section.get("artifact_identity_collision") is not False:
            failures.append("artifact_identity_collision")
        if section.get("predecessor_anchors") != PREDECESSOR_ANCHORS:
            failures.append("predecessor_anchor_census_mismatch")
    joined = "\n".join(snapshot.texts.values())
    for token in FORBIDDEN_PREDECESSOR_TOKENS:
        if token in joined:
            failures.append(f"forbidden_predecessor_source_dependency:{token}")
    witnesses.extend((f"source_files_scanned:{len(snapshot.texts)}", "a8_roster_and_tape_ids_are_fresh"))
    return _certificate("b6_b7_freshness", snapshot, witnesses, failures)


def evaluate_certificates(snapshot: SourceSnapshot) -> tuple[Certificate, ...]:
    certificates = (
        certify_reward_interface(snapshot),
        certify_capture_sites(snapshot),
        certify_dtype_decoder(snapshot),
        certify_fork_tape(snapshot),
        certify_mask_identity(snapshot),
        certify_phase_counts(snapshot),
        certify_endpoint_firewall(snapshot),
        certify_freshness(snapshot),
    )
    if tuple(c.name for c in certificates) != CERTIFICATE_ORDER:
        raise AssertionError("certificate implementation order drift")
    return certificates


def select_terminal_branch(
    *, source_binding_passed: bool, activity_ledger: Mapping[str, int], certificates: Sequence[Certificate]
) -> str:
    if not source_binding_passed or dict(activity_ledger) != ZERO_ACTIVITY_LEDGER:
        return BRANCH_PRECEDENCE[0]
    by_name = {certificate.name: certificate for certificate in certificates}
    if not all(by_name[name].passed for name in CERTIFICATE_ORDER[:3]):
        return BRANCH_PRECEDENCE[1]
    if not all(by_name[name].passed for name in CERTIFICATE_ORDER[3:5]):
        return BRANCH_PRECEDENCE[2]
    if not all(by_name[name].passed for name in CERTIFICATE_ORDER[5:7]):
        return BRANCH_PRECEDENCE[3]
    if not by_name[CERTIFICATE_ORDER[7]].passed:
        return BRANCH_PRECEDENCE[4]
    return BRANCH_PRECEDENCE[5]


def build_result(
    *,
    binding: SourceBinding,
    snapshot: SourceSnapshot | None,
    payload_sha256: str,
    payload_valid: bool,
    payload_failures: Sequence[str],
) -> dict[str, Any]:
    activity = dict(ZERO_ACTIVITY_LEDGER)
    if binding.passed and payload_valid and snapshot is not None:
        certificates = evaluate_certificates(snapshot)
        source_contract_passed = True
    else:
        source_digest = snapshot.digest if snapshot is not None else ""
        reasons = tuple(binding.failures) + tuple(payload_failures)
        certificates = tuple(
            Certificate(name, False, source_digest, (), ("not_evaluated_due_source_or_payload_binding", *reasons))
            for name in CERTIFICATE_ORDER
        )
        source_contract_passed = False
    branch = select_terminal_branch(
        source_binding_passed=source_contract_passed,
        activity_ledger=activity,
        certificates=certificates,
    )
    return {
        "schema_version": 1,
        "document_kind": "eociv_a8_exact_dyadic_ledger_identifiability_result",
        "treatment_id": TREATMENT_ID,
        "design_id": DESIGN_ID,
        "target_version_id": TARGET_VERSION_ID,
        "conclusion": branch,
        "terminal_branch": branch,
        "source_binding": asdict(binding),
        "payload_sha256": payload_sha256,
        "payload_valid": payload_valid,
        "payload_failures": list(payload_failures),
        "source_snapshot": {
            "digest": snapshot.digest if snapshot is not None else None,
            "manifest_locator": snapshot.manifest_locator if snapshot is not None else None,
            "manifest_present": bool(snapshot is not None and snapshot.manifest is not None),
        },
        "certificates": [asdict(certificate) for certificate in certificates],
        "activity_ledger": activity,
        "branch_precedence": list(BRANCH_PRECEDENCE),
        "roster_digest": sha256_bytes(canonical_json_bytes(canonical_roster())),
        "predecessor_anchors": PREDECESSOR_ANCHORS,
        "b8_authorized": False,
        "scientific_effect_claimed": False,
    }


def validate_payload(payload: Any) -> tuple[bool, tuple[str, ...]]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return False, ("payload_not_object",)
    for key in ("design_id", "treatment_id", "target_version_id"):
        expected = {
            "design_id": DESIGN_ID,
            "treatment_id": TREATMENT_ID,
            "target_version_id": TARGET_VERSION_ID,
        }[key]
        if payload.get(key) != expected:
            failures.append(f"payload_identity_mismatch:{key}")
    branches = payload.get("branch_precedence")
    if not isinstance(branches, list) or [item.get("branch") for item in branches if isinstance(item, dict)] != list(BRANCH_PRECEDENCE):
        failures.append("payload_branch_precedence_mismatch")
    if payload.get("hard_caps") != ZERO_ACTIVITY_LEDGER:
        failures.append("payload_hard_caps_mismatch")
    roster = payload.get("fixed_roster")
    if not isinstance(roster, dict):
        failures.append("payload_fixed_roster_missing")
    else:
        expected_roster = canonical_roster()
        for key, expected in expected_roster.items():
            if roster.get(key) != expected:
                failures.append(f"payload_roster_mismatch:{key}")
        _, derived_failures = _root_seed_witnesses()
        failures.extend(f"payload_internal:{failure}" for failure in derived_failures)
    required = payload.get("required_certificates")
    if not isinstance(required, list) or len(required) != 8:
        failures.append("payload_required_certificate_count_mismatch")
    return not failures, tuple(failures)


def validate_result(result: Mapping[str, Any]) -> None:
    failures: list[str] = []
    if result.get("treatment_id") != TREATMENT_ID or result.get("design_id") != DESIGN_ID:
        failures.append("result_identity_mismatch")
    if result.get("branch_precedence") != list(BRANCH_PRECEDENCE):
        failures.append("result_branch_precedence_mismatch")
    if result.get("activity_ledger") != ZERO_ACTIVITY_LEDGER:
        failures.append("result_activity_ledger_mismatch")
    if result.get("roster_digest") != sha256_bytes(canonical_json_bytes(canonical_roster())):
        failures.append("result_roster_digest_mismatch")
    if result.get("payload_valid") is True and result.get("payload_sha256") != EXPECTED_PAYLOAD_SHA256:
        failures.append("result_payload_hash_mismatch")
    raw_certificates = result.get("certificates")
    if not isinstance(raw_certificates, list) or [item.get("name") for item in raw_certificates if isinstance(item, dict)] != list(CERTIFICATE_ORDER):
        failures.append("result_certificate_order_mismatch")
        certificates: tuple[Certificate, ...] = ()
    else:
        if any(type(item.get("passed")) is not bool for item in raw_certificates):
            failures.append("result_certificate_passed_not_boolean")
        certificates = tuple(
            Certificate(
                name=item["name"],
                passed=bool(item["passed"]),
                source_digest=str(item["source_digest"]),
                witnesses=tuple(item["witnesses"]),
                failures=tuple(item["failures"]),
            )
            for item in raw_certificates
        )
    binding = result.get("source_binding")
    if isinstance(binding, dict) and binding.get("passed") is True:
        if binding.get("failures") not in ([], ()):
            failures.append("result_source_binding_pass_has_failures")
        if binding.get("expected_commit") != binding.get("actual_commit"):
            failures.append("result_source_binding_commit_mismatch")
    snapshot_digest = result.get("source_snapshot", {}).get("digest") if isinstance(result.get("source_snapshot"), dict) else None
    if certificates:
        if snapshot_digest is None:
            if any(certificate.source_digest != "" for certificate in certificates):
                failures.append("result_certificate_source_digest_mismatch")
        elif any(certificate.source_digest != snapshot_digest for certificate in certificates):
            failures.append("result_certificate_source_digest_mismatch")
    source_valid = bool(
        isinstance(binding, dict)
        and binding.get("passed") is True
        and result.get("payload_valid") is True
    )
    expected_branch = select_terminal_branch(
        source_binding_passed=source_valid,
        activity_ledger=result.get("activity_ledger", {}),
        certificates=certificates,
    ) if certificates else None
    if expected_branch != result.get("terminal_branch") or result.get("conclusion") != result.get("terminal_branch"):
        failures.append("result_terminal_branch_not_rederived")
    if result.get("b8_authorized") is not False or result.get("scientific_effect_claimed") is not False:
        failures.append("result_exceeds_constructibility_boundary")
    if failures:
        raise ContractError(";".join(failures))


def load_and_validate_payload(path: Path) -> tuple[Any, str, bool, tuple[str, ...]]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, "", False, (f"payload_unreadable:{type(exc).__name__}",)
    observed_hash = sha256_bytes(raw)
    valid, failures = validate_payload(payload)
    if observed_hash != EXPECTED_PAYLOAD_SHA256:
        failures = (*failures, "payload_bytes_not_exact_frozen_payload")
        valid = False
    return payload, observed_hash, valid, failures


def write_result_once(path: Path, result: Mapping[str, Any]) -> None:
    validate_result(result)
    payload = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def run_audit(
    *,
    source_root: Path,
    expected_commit: str,
    payload_path: Path,
    output_path: Path,
    cwd: Path,
    core_relative_path: str,
    runner_relative_path: str,
    runtime_runner_file: Path,
) -> dict[str, Any]:
    audited_paths = (*HOST_SOURCE_PATHS, core_relative_path, runner_relative_path)
    binding = verify_source_binding(
        source_root=source_root,
        expected_commit=expected_commit,
        cwd=cwd,
        audited_paths=audited_paths,
        runtime_core_file=Path(__file__),
        runtime_runner_file=runtime_runner_file,
        core_relative_path=core_relative_path,
        runner_relative_path=runner_relative_path,
    )
    _, payload_hash, payload_valid, payload_failures = load_and_validate_payload(payload_path)
    snapshot = read_source_snapshot(source_root.resolve(), HOST_SOURCE_PATHS) if binding.passed else None
    result = build_result(
        binding=binding,
        snapshot=snapshot,
        payload_sha256=payload_hash,
        payload_valid=payload_valid,
        payload_failures=payload_failures,
    )
    write_result_once(output_path, result)
    return result
