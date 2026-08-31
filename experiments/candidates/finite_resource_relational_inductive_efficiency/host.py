"""Fresh native host contract and factual/shadow trajectory boundary."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from .contracts.core import ContractError, HOST_ID, NATIVE_ABI, NATIVE_COMPONENT, SOURCE_ID

HORIZON = 12
PUBLIC_ROLES = ("WEST_SURVEYOR", "EAST_SURVEYOR", "RIDGE_RELAY")
LEGAL_ACTIONS_BY_ROLE = {
    "WEST_SURVEYOR": (0, 1, 5),
    "EAST_SURVEYOR": (0, 1, 5),
    "RIDGE_RELAY": (2, 3, 4, 5),
}
LEGAL_MASK_BY_ROLE = {
    role: [action in legal for action in range(6)]
    for role, legal in LEGAL_ACTIONS_BY_ROLE.items()
}


class NativeBackendUnavailable(RuntimeError):
    pass


class NativePreflightFailed(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class NativeContract:
    host_id: str
    source_id: str
    component: str
    abi: str
    binding_kind: str
    native_width: int
    workers: int
    threads: int
    dtype: str = "float32"
    reduction_dtype: str = "float64"
    device: str = "cpu"
    python_fallback: bool = False
    test_only: bool = False

    def validate(self, *, production: bool) -> "NativeContract":
        if self.host_id != HOST_ID or self.source_id != SOURCE_ID:
            raise NativeBackendUnavailable("backend host/source differs from the fresh FRRIE contract")
        if self.component != NATIVE_COMPONENT or self.abi != NATIVE_ABI:
            raise NativeBackendUnavailable("backend component/ABI differs from the fresh FRRIE contract")
        if self.python_fallback:
            raise NativeBackendUnavailable("Python fallback is forbidden")
        if production and self.test_only:
            raise NativeBackendUnavailable("TEST_ONLY backends are categorically forbidden in production")
        if self.device != "cpu" or self.dtype != "float32" or self.reduction_dtype != "float64":
            raise NativeBackendUnavailable("native CPU/FP32/float64 reduction contract mismatch")
        for field in ("native_width", "workers", "threads"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise NativeBackendUnavailable(f"native {field} must be positive")
        if self.binding_kind != "FRRIE_NATIVE_CTYPES_V1" and not self.test_only:
            raise NativeBackendUnavailable("native binding kind is not the direct FRRIE ctypes seam")
        return self


@runtime_checkable
class NativeBackend(Protocol):
    contract: NativeContract

    def preflight(self, resource_ceiling: Mapping[str, int]) -> Mapping[str, Any]: ...
    def rollout(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...


def admit_native_backend(backend: Any, *, production: bool = True) -> NativeBackend:
    if backend is None or not isinstance(getattr(backend, "contract", None), NativeContract):
        raise NativeBackendUnavailable("a caller-supplied native backend is required")
    backend.contract.validate(production=production)
    if production:
        raise NativeBackendUnavailable("fresh package-owned production native adapter is not bundled")
    if not callable(getattr(backend, "preflight", None)) or not callable(getattr(backend, "rollout", None)):
        raise NativeBackendUnavailable("native backend protocol is incomplete")
    return backend


def preflight_native_backend(backend: NativeBackend, resource_ceiling: Mapping[str, int]) -> Mapping[str, Any]:
    receipt = backend.preflight(resource_ceiling)
    required = {
        "schema", "ok", "fresh", "complete",
        "native_contract", "resource_ceiling",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != required:
        raise NativePreflightFailed("native preflight receipt fields are not exact")
    if (
        receipt.get("schema") != "FRRIE_NATIVE_PREFLIGHT_V1"
        or receipt.get("ok") is not True
        or receipt.get("fresh") is not True
        or receipt.get("complete") is not True
    ):
        raise NativePreflightFailed("native resource preflight did not pass")
    if receipt["native_contract"] != asdict(backend.contract):
        raise NativePreflightFailed("preflight native contract mismatch")
    if receipt["resource_ceiling"] != dict(resource_ceiling):
        raise NativePreflightFailed("preflight resource contract mismatch")
    return dict(receipt)


@dataclass(frozen=True, slots=True)
class Trajectory:
    kind: str
    observations: tuple[Any, ...]
    actions: tuple[Any, ...]
    rewards: tuple[Any, ...]
    terminal: bool
    tape_contract: dict[str, Any]
    side_effect_count: int
    state_before: dict[str, Any]
    state_after: dict[str, Any]

    @classmethod
    def from_backend(cls, value: Mapping[str, Any], expected_kind: str, request: Mapping[str, Any]) -> "Trajectory":
        expected_fields = {
            "schema", "kind", "purpose", "intervention", "roster", "observations", "roles", "legal_role_masks",
            "actions", "rewards", "terminal", "complete", "tape_contract", "side_effect_count",
            "state_before", "state_after",
        }
        if set(value) != expected_fields or value.get("schema") != "FRRIE_NATIVE_TRAJECTORY_V1":
            raise ContractError("native trajectory fields/schema must be exact")
        if value.get("kind") != expected_kind:
            raise ContractError("native trajectory kind mismatch")
        for field in ("purpose", "intervention", "roster", "tape_contract"):
            if value.get(field) != request.get(field):
                raise ContractError(f"native trajectory {field} does not bind its request")
        if expected_kind == "SHADOW" and value.get("side_effect_count") != 0:
            raise ContractError("shadow trajectory attempted a side effect")
        if not isinstance(value["state_before"], Mapping) or not isinstance(value["state_after"], Mapping):
            raise ContractError("native state contracts must be direct mappings")
        if expected_kind == "SHADOW" and value["state_before"] != value["state_after"]:
            raise ContractError("shadow/evaluation trajectory changed native state")
        if value.get("terminal") is not True or value.get("complete") is not True:
            raise ContractError("native trajectory must be terminal and complete")
        roster = value.get("roster")
        if isinstance(roster, bool) or not isinstance(roster, int) or roster <= 0:
            raise ContractError("native trajectory roster is invalid")
        observations, roles, masks, actions, rewards = (
            value["observations"], value["roles"], value["legal_role_masks"],
            value["actions"], value["rewards"],
        )
        if not all(
            isinstance(series, list)
            and all(isinstance(step_row, list) and len(step_row) == roster for step_row in series)
            for series in (observations, roles, masks, actions)
        ):
            raise ContractError("trajectory entity axes must equal the fixed roster")
        steps = len(observations)
        if steps != HORIZON or not (len(roles) == len(masks) == len(actions) == len(rewards) == steps):
            raise ContractError("trajectory step axes are empty or unaligned")
        for step in range(steps):
            if any(not isinstance(obs, list) or len(obs) != 22 or any(isinstance(x, bool) or not isinstance(x, float) or not math.isfinite(x) for x in obs) for obs in observations[step]):
                raise ContractError("observations must be finite FP32-shaped 22-field rows")
            role_masks = LEGAL_MASK_BY_ROLE
            if any(role not in role_masks for role in roles[step]):
                raise ContractError("public role is outside the frozen three-role set")
            for entity in range(roster):
                mask = masks[step][entity]
                action = actions[step][entity]
                if mask != role_masks[roles[step][entity]]:
                    raise ContractError("legal role masks must be six literal booleans with support")
                if isinstance(action, bool) or not isinstance(action, int) or not 0 <= action < 6 or not mask[action]:
                    raise ContractError("native categorical action is illegal under its role mask")
        expected_role_count = roster // 3
        if roster % 3 or any(roles[0].count(role) != expected_role_count for role in PUBLIC_ROLES):
            raise ContractError("roster must contain exactly N/3 of each frozen role")
        if any(step_roles != roles[0] for step_roles in roles[1:]):
            raise ContractError("roles must remain stable for the fixed-roster episode")
        if any(isinstance(reward, bool) or not isinstance(reward, (int, float)) or not math.isfinite(float(reward)) for reward in rewards):
            raise ContractError("native rewards must be finite scalars")
        if isinstance(value["side_effect_count"], bool) or not isinstance(value["side_effect_count"], int) or value["side_effect_count"] < 0:
            raise ContractError("side_effect_count must be a nonnegative literal integer")
        tape = value["tape_contract"]
        _validate_tape_contract(tape, request)
        return cls(
            expected_kind, tuple(value["observations"]), tuple(value["actions"]),
            tuple(value["rewards"]), value["terminal"], dict(tape),
            int(value["side_effect_count"]), dict(value["state_before"]), dict(value["state_after"]),
        )


class FRRIEHost:
    def __init__(self, backend: NativeBackend):
        self.backend = admit_native_backend(backend, production=True)

    def factual(self, request: Mapping[str, Any]) -> Trajectory:
        payload = _validate_rollout_request(request)
        payload["trajectory_kind"] = "FACTUAL"
        payload["allow_side_effects"] = True
        return Trajectory.from_backend(self.backend.rollout(payload), "FACTUAL", payload)

    def shadow(self, request: Mapping[str, Any]) -> Trajectory:
        payload = _validate_rollout_request(request)
        payload["trajectory_kind"] = "SHADOW"
        payload["allow_side_effects"] = False
        payload["evaluation_accounting"] = False
        return Trajectory.from_backend(self.backend.rollout(payload), "SHADOW", payload)


def native_endpoint(dw: int, de: int, waste: float) -> float:
    """Strict-support float64 reduction for the frozen higher-better endpoint."""
    if type(dw) is not int or type(de) is not int:
        raise ContractError("endpoint deliveries must be literal integer counts")
    values = (dw, de, waste)
    if isinstance(waste, bool) or not isinstance(waste, (int, float)) or not math.isfinite(float(waste)):
        raise ContractError("endpoint inputs must be finite real scalars")
    dw64, de64, waste64 = map(float, values)
    if not (0.0 <= dw64 <= 3.0 and 0.0 <= de64 <= 3.0 and 0.0 <= waste64 <= 1.0):
        raise ContractError("endpoint inputs are outside native support")
    return 0.65 * (dw64 + de64) / 6.0 + 0.25 * min(dw64, de64) / 3.0 + 0.10 * (1.0 - waste64)


class TestOnlyNativeBackend:
    """Tiny explicit double; impossible to admit through the production path."""

    TEST_ONLY = True
    __test__ = False

    def __init__(self) -> None:
        self.contract = NativeContract(
            HOST_ID, SOURCE_ID, NATIVE_COMPONENT, NATIVE_ABI,
            "TEST_ONLY", 1, 1, 1, test_only=True,
        )

    def preflight(self, resource_ceiling: Mapping[str, int]) -> Mapping[str, Any]:
        return {
            "schema": "FRRIE_NATIVE_PREFLIGHT_V1",
            "ok": True,
            "fresh": True,
            "complete": True,
            "native_contract": asdict(self.contract),
            "resource_ceiling": dict(resource_ceiling),
        }

    def rollout(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        if request.get("trajectory_kind") not in {"FACTUAL", "SHADOW"}:
            raise ContractError("TEST_ONLY trajectory kind required")
        shadow = request["trajectory_kind"] == "SHADOW"
        return {
            "schema": "FRRIE_NATIVE_TRAJECTORY_V1", "kind": request["trajectory_kind"],
            "purpose": request.get("purpose", "TEST_ONLY"), "intervention": request.get("intervention", "TEST_ONLY"),
            "roster": 3, "observations": [[[0.0] * 22 for _ in range(3)] for _ in range(HORIZON)],
            "roles": [["WEST_SURVEYOR", "EAST_SURVEYOR", "RIDGE_RELAY"] for _ in range(HORIZON)],
            "legal_role_masks": [[
                [True, True, False, False, False, True],
                [True, True, False, False, False, True],
                [False, False, True, True, True, True],
            ] for _ in range(HORIZON)],
            "actions": [[0, 5, 4] for _ in range(HORIZON)], "rewards": [0.0] * HORIZON,
            "terminal": True, "complete": True,
            "tape_contract": request.get("tape_contract", {
                "schema": "FRRIE_ADDRESSED_TAPE_V1", "seed_block": "TEST_ONLY",
                "purpose": "TEST_ONLY", "roster": 3, "update": 0, "episode": 0,
            }),
            "side_effect_count": 0 if shadow else 1,
            "state_before": {"schema": "TEST_ONLY_NATIVE_STATE_V1", "step": request.get("step", 0)},
            "state_after": (
                {"schema": "TEST_ONLY_NATIVE_STATE_V1", "step": request.get("step", 0)}
                if shadow else {"schema": "TEST_ONLY_NATIVE_STATE_V1", "step": request.get("step", 0) + 1}
            ),
        }


def _validate_rollout_request(request: Mapping[str, Any]) -> dict[str, Any]:
    required = {"schema", "seed_block", "purpose", "intervention", "roster", "update", "episode", "tape_contract"}
    if set(request) != required or request.get("schema") != "FRRIE_NATIVE_ROLLOUT_REQUEST_V1":
        raise ContractError("native rollout request fields/schema must be exact")
    if request["purpose"] not in {"TRAIN", "EVALUATE"} or request["intervention"] not in {"INTACT", "SEMANTIC_COLUMN_ROTATE"}:
        raise ContractError("native rollout purpose/roster is outside the frozen panel")
    if request["purpose"] == "TRAIN" and (request["roster"] not in {9, 15} or request["intervention"] != "INTACT"):
        raise ContractError("training rollout must be INTACT at N=9 or N=15")
    if request["purpose"] == "EVALUATE" and request["roster"] not in {6, 9, 15, 21}:
        raise ContractError("evaluation roster is outside the frozen complete panel")
    if not isinstance(request["seed_block"], str) or not request["seed_block"].startswith("FRRIE-"):
        raise ContractError("rollout seed block lacks a fresh FRRIE label")
    if type(request["update"]) is not int or not 1 <= request["update"] <= 512:
        raise ContractError("rollout update is outside [1,512]")
    episode_limit = 64 if request["purpose"] == "TRAIN" else 256
    if type(request["episode"]) is not int or not 0 <= request["episode"] < episode_limit:
        raise ContractError("rollout episode coordinate is outside its purpose range")
    _validate_tape_contract(request["tape_contract"], request)
    return dict(request)


def _validate_tape_contract(tape: Any, request: Mapping[str, Any]) -> None:
    fields = {"schema", "seed_block", "purpose", "roster", "update", "episode"}
    if not isinstance(tape, Mapping) or set(tape) != fields:
        raise ContractError("addressed tape contract fields must be exact")
    expected = {
        "schema": "FRRIE_ADDRESSED_TAPE_V1",
        "seed_block": request.get("seed_block"),
        "purpose": request.get("purpose"),
        "roster": request.get("roster"),
        "update": request.get("update"),
        "episode": request.get("episode"),
    }
    if dict(tape) != expected:
        raise ContractError("addressed tape contract does not bind rollout coordinates")
