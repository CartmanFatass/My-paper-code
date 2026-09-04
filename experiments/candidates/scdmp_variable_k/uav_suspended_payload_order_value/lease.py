"""Identity-free coordinate proposal and exact future empirical lease gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
from collections.abc import Callable
from typing import Final, Mapping

from .config import CARD_REVISION, COMPONENT, CONSTRUCTION_OBJECT, HOST_ID
from .native_backend import NATIVE_ABI_VERSION, SCIENCE_CARD_SHA256


EMPIRICAL_STAGE: Final[str] = "SCDMP-UAV-SP-R02-FULL-EMPIRICAL-PANEL"
TRAIN_PHASE: Final[str] = "TRAIN"
EVALUATE_PHASE: Final[str] = "EVALUATE"
EXECUTION_MODULE: Final[str] = (
    "experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value"
)
PYTHON_EXECUTABLE: Final[str] = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
BOUND_PATH_FIELDS: Final[tuple[str, ...]] = (
    "result_path",
    "train_terminal_path",
    "evaluation_terminal_path",
    "run_identity_path",
    "completion_inventory_path",
    "cm_acceptance_path",
)
PROPOSAL_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_COORDINATE_PROPOSAL_V1"
LEASE_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_ROOT_EMPIRICAL_LEASE_V1"
PROHIBITIONS: Final[tuple[str, ...]] = (
    "stage_b",
    "relation_assay",
    "second_surface",
    "deployment",
    "flight",
)
_PERMIT_SEAL: Final[object] = object()
EMPIRICAL_SOURCE_MANIFEST_NAME: Final[str] = "empirical_source_manifest.json"
_CANDIDATE_SOURCE_PREFIX: Final[str] = (
    "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value/"
)


def _source_digest(path: Path) -> str:
    content = path.read_bytes()
    if path.suffix.lower() in {".cpp", ".hpp", ".json", ".md", ".py"}:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


EMPIRICAL_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "envs/native/production_backend.py",
    *(
        _CANDIDATE_SOURCE_PREFIX + relative
        for relative in (
            "__init__.py",
            "config.py",
            "controllers.py",
            "evaluation.py",
            "frontier.py",
            "host_types.py",
            "inference.py",
            "lease.py",
            "lifecycle.py",
            "model.py",
            "native/uav_sp_order_value_backend.cpp",
            "native_backend.py",
            "oracle.py",
            "preactivity.py",
            "rng.py",
            "runner.py",
            "support.py",
            "training.py",
            "production_training.py",
            "production_evaluation.py",
            "production.py",
            "__main__.py",
        )
    ),
)

# Exact implementation identity accepted by the construction-stage CM.  It is
# deliberately limited to the already accepted host package, excluding this
# empirical contract and the separately assigned model/training package.
ACCEPTED_CONSTRUCTION_SOURCE_MAP: Final[dict[str, str]] = {
    "__init__.py": "79248ca69c583c16c4ef97a691f4cb22184666bdedb0e2926cb79bbcdf7453d3",
    "config.py": "2c8c1d6a796e4b4d8978dc91760a4be2e3c6f7defcb7bc88fdc5da80fb00547b",
    "controllers.py": "7d4c3f25ab19f615a3fe99aa6d58c569fbc929d711f0d89f9b7bcb2fa1d6aa20",
    "host_types.py": "45a0ee95232ccb9e0345fd2cfcf39c67386012724659f531f99a916dd18fe952",
    "lifecycle.py": "9b60cbec31f22ba56b81b43b55cf13fddad1e944e434dbd596e8e18c9b174f72",
    "native/uav_sp_order_value_backend.cpp": "a4965d8558ac1921c4c00e43726996ac60d4a6a794811b03860a34c394887cea",
    "native_backend.py": "26e82f5609bad314c4d01fd0a124accaa6e0de930fed5c96d8a00afdca79fde9",
    "oracle.py": "72e0cc6555eb21a35af6896c8a650359feed20b4da5f2be983dd87be9c133dda",
    "preactivity.py": "63e56acb8781ddcb3cf6f09eef2205289cb686096ed5ec0f043a37122c7aad5a",
}
ACCEPTED_CONSTRUCTION_SOURCE_MAP_DIGEST: Final[str] = (
    "2ea216e143e222303c2a170e0c2fe3ce65a4ff994209c3e62a27021c60a748ad"
)
ACCEPTED_NATIVE_SOURCE_SHA256: Final[str] = (
    "a4965d8558ac1921c4c00e43726996ac60d4a6a794811b03860a34c394887cea"
)
ACCEPTED_SOURCE_SHA256: Final[str] = (
    "f0bf4f6ee42bc13b4bca4edad4125df4190ae22d8dcd33d1f55e2867c62dea35"
)
ACCEPTED_BUILD_KEY: Final[str] = (
    "7a70cf5b9bc769739e8c0afb7124dbaaca6cb55dc4831645c5020e4eccaa56d7"
)
ACCEPTED_ARTIFACT_SHA256: Final[str] = (
    "9ec8e6fb25cf60fa7525a0e1af2bb2244edf2119ad13068a3b24edab77a7add9"
)
ACCEPTED_ARTIFACT_SIZE: Final[int] = 123_904
ACCEPTED_ABI_SIZES: Final[dict[str, int]] = {
    "reset_input": 6_760,
    "full_input": 7_184,
    "tick": 152,
    "renewal_output": 352,
    "full_output": 64_152,
}


class LeaseValidationError(RuntimeError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def construction_source_map_digest(source_map: Mapping[str, str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(source_map):
        encoded = relative.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        try:
            digest.update(bytes.fromhex(str(source_map[relative])))
        except ValueError as error:
            raise LeaseValidationError("construction source map contains a non-hex digest") from error
    return digest.hexdigest()


def canonical_absolute_path_key(path: str | Path) -> str:
    """Normalize ordinary and Windows extended-length absolute paths equally."""

    raw = str(Path(path).resolve())
    if raw.startswith("\\\\?\\UNC\\"):
        raw = "\\\\" + raw[8:]
    elif raw.startswith("\\\\?\\"):
        raw = raw[4:]
    return os.path.normcase(os.path.normpath(raw))


def path_is_within_root(path: str | Path, root: str | Path, *, allow_equal: bool = False) -> bool:
    child_key = canonical_absolute_path_key(path)
    root_key = canonical_absolute_path_key(root)
    if child_key == root_key:
        return allow_equal
    try:
        return os.path.commonpath((child_key, root_key)) == root_key
    except ValueError:
        # Different Windows drives or incompatible absolute path kinds.
        return False


def empirical_source_manifest_identity(
    package_root: Path,
    *,
    manifest_path: Path | None = None,
    require_final: bool,
) -> dict[str, object]:
    """Validate canonical manifest bytes and every bound production source."""

    package = package_root.resolve()
    repository = package.parents[3]
    path = (
        package / EMPIRICAL_SOURCE_MANIFEST_NAME
        if manifest_path is None
        else manifest_path.resolve()
    )
    if not path.is_file():
        raise LeaseValidationError("empirical source manifest is missing")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LeaseValidationError("empirical source manifest is not ASCII JSON") from error
    if not isinstance(value, Mapping) or set(value) != {"schema", "status", "files"}:
        raise LeaseValidationError("empirical source manifest schema differs")
    if value.get("schema") != "SCDMP_UAV_SP_R02_EMPIRICAL_SOURCE_MANIFEST_V1":
        raise LeaseValidationError("empirical source manifest identity differs")
    status = value.get("status")
    if status not in ("PROVISIONAL", "FINAL"):
        raise LeaseValidationError("empirical source manifest status is invalid")
    if require_final and status != "FINAL":
        raise LeaseValidationError("empirical source manifest is not final")
    canonical = canonical_json_bytes(dict(value)) + b"\n"
    if raw.replace(b"\r\n", b"\n") != canonical:
        raise LeaseValidationError("empirical source manifest bytes are not canonical")
    manifest_sha256 = hashlib.sha256(canonical).hexdigest()
    files = value.get("files")
    if not isinstance(files, list) or len(files) != len(EMPIRICAL_SOURCE_PATHS):
        raise LeaseValidationError("empirical source manifest inventory count differs")
    observed: dict[str, str] = {}
    for row in files:
        if not isinstance(row, Mapping) or set(row) != {"path", "sha256"}:
            raise LeaseValidationError("empirical source manifest row schema differs")
        relative = row.get("path")
        expected = row.get("sha256")
        if not isinstance(relative, str) or relative in observed:
            raise LeaseValidationError("empirical source path is invalid or duplicated")
        if not isinstance(expected, str) or len(expected) != 64:
            raise LeaseValidationError("empirical source digest is invalid")
        try:
            int(expected, 16)
        except ValueError as error:
            raise LeaseValidationError("empirical source digest is invalid") from error
        if require_final:
            source = (repository / relative).resolve()
            try:
                source.relative_to(repository)
            except ValueError as error:
                raise LeaseValidationError("empirical source path escapes repository root") from error
            if not source.is_file():
                raise LeaseValidationError(f"empirical production source is missing: {relative}")
            actual = _source_digest(source)
            if actual != expected:
                raise LeaseValidationError(f"empirical production source digest changed: {relative}")
        observed[relative] = expected
    if tuple(observed) != EMPIRICAL_SOURCE_PATHS:
        raise LeaseValidationError("empirical source manifest path/order inventory differs")
    return {
        "path": EMPIRICAL_SOURCE_MANIFEST_NAME,
        "sha256": manifest_sha256,
        "status": status,
        "file_count": len(observed),
    }


def current_empirical_source_manifest_identity(*, require_final: bool) -> dict[str, object]:
    return empirical_source_manifest_identity(
        Path(__file__).resolve().parent,
        require_final=require_final,
    )


def accepted_construction_binding() -> dict[str, object]:
    return {
        "construction_object": CONSTRUCTION_OBJECT,
        "component": COMPONENT,
        "host": HOST_ID,
        "card_revision": CARD_REVISION,
        "card_sha256": SCIENCE_CARD_SHA256,
        "abi_version": 2,
        "source_map": dict(ACCEPTED_CONSTRUCTION_SOURCE_MAP),
        "source_map_digest": ACCEPTED_CONSTRUCTION_SOURCE_MAP_DIGEST,
        "native_source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
        "source_sha256": ACCEPTED_SOURCE_SHA256,
        "build_key": ACCEPTED_BUILD_KEY,
        "artifact_sha256": ACCEPTED_ARTIFACT_SHA256,
        "artifact_size": ACCEPTED_ARTIFACT_SIZE,
        "abi_sizes": dict(ACCEPTED_ABI_SIZES),
        "binding_kind": "ctypes_cdll",
        "python_fallback": False,
        "full_reset_step_cpp": True,
    }


def coordinate_proposal() -> dict[str, object]:
    empirical_manifest = current_empirical_source_manifest_identity(require_final=False)
    checkpoint_slots = [
        {"replicate": replicate, "arm": arm, "eligible_update": 144}
        for replicate in range(18)
        for arm in ("TREAT", "FREE", "SET")
    ]
    return {
        "schema": PROPOSAL_SCHEMA,
        "materialized": False,
        "stage": EMPIRICAL_STAGE,
        "card_revision": CARD_REVISION,
        "card_sha256": SCIENCE_CARD_SHA256,
        "host": HOST_ID,
        "construction_binding": accepted_construction_binding(),
        "empirical_source_manifest": empirical_manifest,
        "two_phase_contract": {
            "phases": [TRAIN_PHASE, EVALUATE_PHASE],
            "module": EXECUTION_MODULE,
            "python_executable": PYTHON_EXECUTABLE,
            "commands": {
                TRAIN_PHASE: [PYTHON_EXECUTABLE, "-m", EXECUTION_MODULE, "--phase", TRAIN_PHASE],
                EVALUATE_PHASE: [PYTHON_EXECUTABLE, "-m", EXECUTION_MODULE, "--phase", EVALUATE_PHASE],
            },
            "bound_paths": ["result_root", *BOUND_PATH_FIELDS],
            "training_stops_before_evaluation": True,
            "cm_acceptance_required": True,
            "torch_threads": 1,
        },
        "rng": {
            "derivation": "HMAC-SHA256",
            "master_bits": 256,
            "replicate_namespace": "SCDMP-UAV-SP-ORDER-VALUE-r02/replicate/<uint32_be(s)>",
            "replicates": list(range(18)),
            "domains": [
                "initialization",
                "training-initial-state",
                "training-setup-event-order",
                "training-disturbances",
                "training-action-uniforms",
                "training-minibatch-order",
                "evaluation-state",
                "evaluation-setup-event-order",
                "evaluation-switch-time",
                "evaluation-disturbances",
                "support-states",
                "support-disturbances",
            ],
            "master": None,
            "master_digest": None,
            "replicate_key_digests": [],
            "domain_key_digests": [],
        },
        "training": {
            "replicates": 18,
            "learned_arms": ["TREAT", "FREE", "SET"],
            "updates_per_arm": 144,
            "epochs_per_update": 4,
            "minibatches_per_epoch": 4,
            "adamw_steps_per_arm": 2_304,
            "checkpoint_slots": checkpoint_slots,
            "checkpoint_count": 54,
            "only_update_144_eligible": True,
        },
        "evaluation": {
            "controllers": ["TREAT", "FREE", "REVERSED", "SET"],
            "regimes": ["fixed-4", "fixed-10", "fixed-6", "fixed-14", "6-to-14", "14-to-6"],
            "episodes_per_replicate_controller_regime": 120,
            "episode_count": 51_840,
            "deterministic_lexicographic_argmax": True,
        },
        "support": {
            "shape": [18, 2, 72, 2, 27],
            "fixed_k": [6, 14],
            "states_per_k": 72,
            "histories": ["RG", "GR"],
            "actions": 27,
            "registered_expanded_action_intervals": 139_968,
            "lossless_carrier_permutation_quotient": {
                "representatives": 10,
                "representative_simulations": 51_840,
                "maximum_transitions_per_support_boundary": 140,
                "complexity": "O(k*10)",
                "nested_replanning": False,
                "expanded_exact_max_set_actions": 27,
            },
        },
        "lifecycle": {
            "frontiers": "create_only_blinded_per_replicate_arm",
            "checkpoint_barrier": "all_54_technically_accepted_before_any_evaluation",
            "result_boundary": "complete_atomic_result_blind",
            "partial_inspection_permitted": False,
            "same_coordinate_resume": True,
        },
        "lease_request": {
            "cpu_only": True,
            "gpu_count": 0,
            "max_independent_workers": 4,
            "ram_gib": 12,
            "scratch_gib": 6,
            "durable_artifacts_gib": 2,
            "validity_hours": 36,
            "complete_panel_only": True,
            "stage": EMPIRICAL_STAGE,
        },
        "prohibitions": list(PROHIBITIONS),
    }


COORDINATE_PLAN_DIGEST: Final[str] = canonical_digest(coordinate_proposal())


def validate_coordinate_proposal(value: Mapping[str, object]) -> None:
    try:
        candidate = dict(value)
        digest = canonical_digest(candidate)
    except (TypeError, ValueError) as error:
        raise LeaseValidationError("coordinate proposal is not canonical JSON") from error
    if candidate != coordinate_proposal() or digest != COORDINATE_PLAN_DIGEST:
        raise LeaseValidationError("coordinate proposal differs from the identity-free freeze")


def _parse_time(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise LeaseValidationError(f"{field} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise LeaseValidationError(f"{field} is not valid ISO-8601") from error
    if parsed.tzinfo is None:
        raise LeaseValidationError(f"{field} must include an offset")
    return parsed


def _bound_paths(lease: Mapping[str, object]) -> dict[str, Path]:
    paths = lease.get("paths")
    if not isinstance(paths, Mapping) or set(paths) != {"result_root", *BOUND_PATH_FIELDS}:
        raise LeaseValidationError("lease path field inventory differs")
    resolved: dict[str, Path] = {}
    for field in ("result_root", *BOUND_PATH_FIELDS):
        raw = paths.get(field)
        if not isinstance(raw, str) or not Path(raw).is_absolute():
            raise LeaseValidationError(f"lease path {field} must be absolute")
        resolved[field] = Path(raw).resolve()
    root = resolved["result_root"]
    targets = [resolved[field] for field in BOUND_PATH_FIELDS]
    if len({canonical_absolute_path_key(target) for target in targets}) != len(targets):
        raise LeaseValidationError("lease output/control paths must be distinct")
    for field in BOUND_PATH_FIELDS:
        target = resolved[field]
        if not path_is_within_root(target, root, allow_equal=False):
            raise LeaseValidationError(f"lease path {field} escapes or equals result_root")
    return resolved


def validate_lease_envelope(lease: Mapping[str, object], *, now: datetime) -> None:
    """Validate every non-native field before any guard or identity call."""

    if not isinstance(lease, Mapping):
        raise LeaseValidationError("an exact Root lease mapping is required")
    required_keys = {
        "schema", "lease_id", "activity_authorized", "stage", "card_revision",
        "card_sha256", "component", "abi_version", "coordinate_plan_digest",
        "construction_binding", "complete_panel_only", "prohibitions", "issued_at",
        "expires_at", "resources", "empirical_source_manifest_sha256", "phase",
        "paths", "execution", "occupied_digest_registry",
    }
    if set(lease) != required_keys:
        raise LeaseValidationError("lease field inventory differs from the exact empirical schema")
    if lease.get("schema") != LEASE_SCHEMA or lease.get("activity_authorized") is not True:
        raise LeaseValidationError("future exact empirical activity lease is absent")
    if not isinstance(lease.get("lease_id"), str) or not str(lease["lease_id"]).strip():
        raise LeaseValidationError("lease_id is absent")
    exact = {
        "stage": EMPIRICAL_STAGE,
        "card_revision": CARD_REVISION,
        "card_sha256": SCIENCE_CARD_SHA256,
        "component": COMPONENT,
        "abi_version": 2,
        "coordinate_plan_digest": COORDINATE_PLAN_DIGEST,
        "complete_panel_only": True,
        "prohibitions": list(PROHIBITIONS),
        "empirical_source_manifest_sha256": str(
            coordinate_proposal()["empirical_source_manifest"]["sha256"]
        ),
    }
    for key, expected in exact.items():
        if lease.get(key) != expected:
            raise LeaseValidationError(f"lease field {key!r} differs from exact empirical freeze")
    if lease.get("construction_binding") != accepted_construction_binding():
        raise LeaseValidationError("lease construction source/build/artifact binding differs")
    phase = lease.get("phase")
    if phase not in (TRAIN_PHASE, EVALUATE_PHASE):
        raise LeaseValidationError("lease phase must be TRAIN or EVALUATE")
    expected_execution = {
        "module": EXECUTION_MODULE,
        "phase": phase,
        "command": [PYTHON_EXECUTABLE, "-m", EXECUTION_MODULE, "--phase", phase],
    }
    if lease.get("execution") != expected_execution:
        raise LeaseValidationError("lease command/module/phase contract differs")
    _bound_paths(lease)
    registry = lease.get("occupied_digest_registry")
    if registry is not None:
        if not isinstance(registry, Mapping) or set(registry) != {"path", "sha256"}:
            raise LeaseValidationError("occupied digest registry binding differs")
        registry_path = registry.get("path")
        registry_sha = registry.get("sha256")
        if not isinstance(registry_path, str) or not Path(registry_path).is_absolute():
            raise LeaseValidationError("occupied digest registry path must be absolute")
        if not isinstance(registry_sha, str) or len(registry_sha) != 64:
            raise LeaseValidationError("occupied digest registry SHA must be a hex digest")
        try:
            int(registry_sha, 16)
        except ValueError as error:
            raise LeaseValidationError("occupied digest registry SHA must be a hex digest") from error
    resources = lease.get("resources")
    if not isinstance(resources, Mapping):
        raise LeaseValidationError("lease resource declaration is absent")
    if set(resources) != {
        "cpu_only", "gpu_count", "independent_workers", "ram_gib", "scratch_gib",
        "durable_artifacts_gib", "torch_threads",
    }:
        raise LeaseValidationError("lease resource field inventory differs")
    if resources.get("cpu_only") is not True or resources.get("gpu_count") != 0:
        raise LeaseValidationError("SCDMP UAV r02 production is CPU-only")
    if resources.get("torch_threads") != 1:
        raise LeaseValidationError("SCDMP UAV r02 production requires torch_threads=1")
    workers = resources.get("independent_workers")
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 4:
        raise LeaseValidationError("lease permits one to four independent workers")
    ram = resources.get("ram_gib")
    if isinstance(ram, bool) or not isinstance(ram, (int, float)) or not 8 <= ram <= 12:
        raise LeaseValidationError("lease ram_gib must lie in the accepted [8,12] interval")
    caps = (("scratch_gib", 6), ("durable_artifacts_gib", 2))
    for field, cap in caps:
        value = resources.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0 or value > cap:
            raise LeaseValidationError(f"lease resource {field} exceeds or omits its cap")
    issued = _parse_time(lease.get("issued_at"), "issued_at")
    expires = _parse_time(lease.get("expires_at"), "expires_at")
    if now.tzinfo is None:
        raise LeaseValidationError("validation time must include an offset")
    if not issued <= now < expires:
        raise LeaseValidationError("lease is not currently active")
    if (expires - issued).total_seconds() > 36 * 3600:
        raise LeaseValidationError("lease validity exceeds the 36-hour proposal")


def validate_current_construction_sources(package_root: Path) -> None:
    package_root = package_root.resolve()
    actual: dict[str, str] = {}
    for relative in ACCEPTED_CONSTRUCTION_SOURCE_MAP:
        path = package_root / relative
        if not path.is_file():
            raise LeaseValidationError(f"accepted construction source is missing: {relative}")
        actual[relative] = _source_digest(path)
    if actual != ACCEPTED_CONSTRUCTION_SOURCE_MAP:
        raise LeaseValidationError("accepted construction source map changed")
    if construction_source_map_digest(actual) != ACCEPTED_CONSTRUCTION_SOURCE_MAP_DIGEST:
        raise LeaseValidationError("accepted construction source-map digest changed")


def construction_binding_from_guard(receipt: Mapping[str, object]) -> dict[str, object]:
    native = receipt.get("direction_native")
    science_card = receipt.get("science_card")
    if not isinstance(native, Mapping) or not isinstance(science_card, Mapping):
        raise LeaseValidationError("native preactivity receipt lacks exact identity fields")
    return {
        "construction_object": receipt.get("construction_object"),
        "component": receipt.get("component"),
        "host": receipt.get("host"),
        "card_revision": receipt.get("card_revision"),
        "card_sha256": science_card.get("sha256"),
        "abi_version": native.get("abi_version"),
        "source_map": dict(ACCEPTED_CONSTRUCTION_SOURCE_MAP),
        "source_map_digest": ACCEPTED_CONSTRUCTION_SOURCE_MAP_DIGEST,
        "native_source_sha256": native.get("native_source_sha256"),
        "source_sha256": native.get("source_sha256"),
        "build_key": native.get("build_key"),
        "artifact_sha256": native.get("artifact_sha256"),
        "artifact_size": native.get("artifact_size"),
        "abi_sizes": native.get("abi_sizes"),
        "binding_kind": native.get("binding_kind"),
        "python_fallback": native.get("python_fallback"),
        "full_reset_step_cpp": receipt.get("full_reset_step_cpp"),
    }


@dataclass(frozen=True, repr=False)
class ActivityPermit:
    lease_id: str
    coordinate_plan_digest: str
    workers: int
    expires_at: datetime
    activity_authorized: bool = True
    phase: str | None = None
    paths: Mapping[str, str] | None = None
    source_manifest_sha256: str | None = None
    native_binding_digest: str | None = None
    card_sha256: str | None = None
    lease_issued_at: str | None = None
    _validation_seal: object | None = None

    def require_active(self, *, now: datetime | None = None) -> None:
        if self._validation_seal is not _PERMIT_SEAL or self.activity_authorized is not True:
            raise LeaseValidationError("activity permit is not authorized")
        checked_at = now if now is not None else datetime.now(self.expires_at.tzinfo)
        if checked_at >= self.expires_at:
            raise LeaseValidationError("activity permit expired")

    def require_phase(self, phase: str) -> None:
        self.require_active()
        if self.phase != phase:
            raise LeaseValidationError(f"activity permit does not authorize {phase} phase")


def validate_lease(
    lease: Mapping[str, object],
    *,
    now: datetime,
    package_root: Path,
    native_guard: Callable[..., Mapping[str, object]],
    manifest_path: Path | None = None,
) -> ActivityPermit:
    validate_lease_envelope(lease, now=now)
    # Full source inventory and the manifest's own lease-bound SHA are checked
    # before native loading and before any identity source is reachable.
    empirical_manifest = empirical_source_manifest_identity(
        package_root,
        manifest_path=manifest_path,
        require_final=True,
    )
    if empirical_manifest["sha256"] != lease["empirical_source_manifest_sha256"]:
        raise LeaseValidationError("empirical source manifest SHA differs from the exact lease")
    registry = lease.get("occupied_digest_registry")
    if isinstance(registry, Mapping):
        registry_path = Path(str(registry["path"])).resolve()
        if not registry_path.is_file():
            raise LeaseValidationError("occupied digest registry file is missing")
        if hashlib.sha256(registry_path.read_bytes()).hexdigest() != registry["sha256"]:
            raise LeaseValidationError("occupied digest registry SHA differs from the exact lease")
    if NATIVE_ABI_VERSION != 2:
        raise LeaseValidationError("candidate native ABI is not revision 2")
    resources = lease["resources"]
    assert isinstance(resources, Mapping)
    native_guard_receipt = native_guard(batch_width=int(resources["independent_workers"]))
    actual = construction_binding_from_guard(native_guard_receipt)
    if actual != accepted_construction_binding():
        raise LeaseValidationError("live native guard differs from accepted construction binding")
    paths = _bound_paths(lease)
    return ActivityPermit(
        lease_id=str(lease["lease_id"]),
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=int(resources["independent_workers"]),
        expires_at=_parse_time(lease["expires_at"], "expires_at"),
        phase=str(lease["phase"]),
        paths={key: str(value) for key, value in paths.items()},
        source_manifest_sha256=str(empirical_manifest["sha256"]),
        native_binding_digest=canonical_digest(actual),
        card_sha256=SCIENCE_CARD_SHA256,
        lease_issued_at=str(lease["issued_at"]),
        _validation_seal=_PERMIT_SEAL,
    )
