"""Source-keyed ctypes loader for the BPCR revision-09 batched C++ host.

Compilation and loading fail closed.  There is no Python implementation
fallback and no build-root override because the artifact identity is derived
from the frozen candidate-local source set and toolchain.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

from .contracts import (
    FIXTURE_MAGIC,
    MSVC_COMPILE_FLAGS,
    NATIVE_ABI_VERSION,
    contract_sha256,
    verify_immutable_inputs,
)


_SOURCE = Path(__file__).with_name("native") / "bpcr_backend.cpp"
_GENERAL_SOURCE = Path(__file__).with_name("native") / "bpcr_general.hpp"
_CHECKER_SOURCE = Path(__file__).with_name("native") / "bpcr_checker.hpp"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class NativeBackendError(RuntimeError):
    """The exact native source/toolchain/ABI boundary is unavailable."""


class _FixtureInput(ctypes.Structure):
    _fields_ = [
        ("fixture_magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_int32),
        ("failed_zone", ctypes.c_int32),
        ("demand_1", ctypes.c_int32),
        ("demand_2", ctypes.c_int32),
        ("blocked_1", ctypes.c_int32),
        ("blocked_2", ctypes.c_int32),
        ("failed_relay_present", ctypes.c_int32),
    ]


class _FixtureOutput(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int32),
        ("candidate_count", ctypes.c_int32),
        ("scorer_command", ctypes.c_int32 * 4),
        ("checker_command", ctypes.c_int32 * 4),
        ("scorer_checker_equal", ctypes.c_int32),
        ("independent_enumerator_equal", ctypes.c_int32),
        ("witness_present", ctypes.c_int32),
        ("earliest_safe_executor_rank", ctypes.c_int32),
        ("needed_relay_rank", ctypes.c_int32),
        ("selected_floor_num", ctypes.c_int32),
        ("selected_floor_den", ctypes.c_int32),
        ("selected_event_count", ctypes.c_int32),
        ("selected_reward_record_count", ctypes.c_int32),
        ("post60_reduced_verified", ctypes.c_int32),
    ]


class _HostInput(ctypes.Structure):
    _fields_ = [
        ("fixture_magic", ctypes.c_uint64), ("abi_version", ctypes.c_int32),
        ("selected_mask", ctypes.c_uint8), ("failed_zone", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 6),
        ("demand_1", ctypes.c_int32 * 12), ("demand_2", ctypes.c_int32 * 12),
        ("blocked_1", ctypes.c_int32 * 12), ("blocked_2", ctypes.c_int32 * 12),
        ("commands", ctypes.c_int32 * 48),
    ]


class _HostOutput(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int32), ("integrated_ticks", ctypes.c_int32),
        ("decision_count", ctypes.c_int32), ("failed_rank", ctypes.c_int32),
        ("fail_delivered", ctypes.c_int64), ("fail_demand", ctypes.c_int64),
        ("total_delivered", ctypes.c_int64), ("total_demand", ctypes.c_int64),
        ("intact_delivered", ctypes.c_int64), ("intact_demand", ctypes.c_int64),
        ("final_token_state", ctypes.c_int32 * 4),
        ("final_acquisition_elapsed", ctypes.c_int32 * 4),
        ("safety_violation", ctypes.c_int32),
        ("exclusivity_violation", ctypes.c_int32), ("event_count", ctypes.c_int32),
    ]


class _GeneralAgentInput(ctypes.Structure):
    _fields_=[(name,ctypes.c_int32) for name in ("rank","opaque_rank","fast","radio","node","edge_from","edge_to","edge_remaining","destination_node","token","token_state","acquisition_elapsed","energy_fifths")]


class _EpisodeInput(ctypes.Structure):
    _fields_=[("magic",ctypes.c_uint64),("abi",ctypes.c_int32),("failed_zone",ctypes.c_int32),("active_count",ctypes.c_int32),("agents",_GeneralAgentInput*8),("demand_1",ctypes.c_int32*12),("demand_2",ctypes.c_int32*12),("blocked_1",ctypes.c_int32*12),("blocked_2",ctypes.c_int32*12),("post_commands",ctypes.c_int32*24),("post_presentation",ctypes.c_int32*48)]


class _DecisionTrace(ctypes.Structure):
    _fields_=[("active_count",ctypes.c_int32),("epoch",ctypes.c_int32),("command",ctypes.c_int32*4),("token_state",ctypes.c_int32*4),("token_elapsed",ctypes.c_int32*4),("legality",ctypes.c_int32*32),("eta",ctypes.c_int32*32),("margin_fifths",ctypes.c_int32*32),("agent_rows",ctypes.c_double*304),("zone_rows",ctypes.c_double*30),("globals",ctypes.c_double*4)]


class _EpisodeOutput(ctypes.Structure):
    _fields_=[("status",ctypes.c_int32),("failed_rank",ctypes.c_int32),("integrated_ticks",ctypes.c_int32),("prehistory_decisions",ctypes.c_int32),("post_decisions",ctypes.c_int32),("safety_violation",ctypes.c_int32),("exclusivity_violation",ctypes.c_int32),("event_count",ctypes.c_int32),("fail_delivered",ctypes.c_int64),("fail_demand",ctypes.c_int64),("total_delivered",ctypes.c_int64),("total_demand",ctypes.c_int64),("intact_delivered",ctypes.c_int64),("intact_demand",ctypes.c_int64),("prehistory_commands",ctypes.c_int32*24),("traces",_DecisionTrace*6)]


class _BCRHInput(ctypes.Structure):
    _fields_=[("magic",ctypes.c_uint64),("abi",ctypes.c_int32),("epoch",ctypes.c_int32),("failed_zone",ctypes.c_int32),("active_count",ctypes.c_int32),("agents",_GeneralAgentInput*8),("clearance",ctypes.c_int32*4),("accrued_fail_delivered",ctypes.c_int64),("accrued_fail_demand",ctypes.c_int64),("accrued_total_delivered",ctypes.c_int64),("accrued_total_demand",ctypes.c_int64),("demand_1",ctypes.c_int32),("demand_2",ctypes.c_int32),("blocked_1",ctypes.c_int32),("blocked_2",ctypes.c_int32)]


class _BCRHCandidateRecord(ctypes.Structure):
    _fields_=[("command",ctypes.c_int32*4),("floor_num",ctypes.c_int32),("floor_den",ctypes.c_int32),("releases",ctypes.c_int32),("objective_limbs",ctypes.c_uint64*4),("checker_floor_num",ctypes.c_int32),("checker_floor_den",ctypes.c_int32),("checker_releases",ctypes.c_int32),("checker_objective_limbs",ctypes.c_uint64*4),("exact_match",ctypes.c_int32)]


class _BCRHOutput(ctypes.Structure):
    _fields_=[("status",ctypes.c_int32),("candidate_count",ctypes.c_int32),("scorer_command",ctypes.c_int32*4),("checker_command",ctypes.c_int32*4),("scorer_checker_equal",ctypes.c_int32),("independent_enumerator_equal",ctypes.c_int32),("post60_reduced",ctypes.c_int32),("floor_num",ctypes.c_int32),("floor_den",ctypes.c_int32),("releases",ctypes.c_int32),("event_records",ctypes.c_int32),("reward_records",ctypes.c_int32),("objective_limbs",ctypes.c_uint64*4),("checker_objective_limbs",ctypes.c_uint64*4),("candidate_digest",ctypes.c_uint64),("checker_digest",ctypes.c_uint64),("records",_BCRHCandidateRecord*1961)]


class _SensitivityInput(ctypes.Structure):
    _fields_=[("current",_BCRHInput),("demand_1",ctypes.c_int32*3),("demand_2",ctypes.c_int32*3),("blocked_1",ctypes.c_int32*3),("blocked_2",ctypes.c_int32*3)]


class _SensitivityOutput(ctypes.Structure):
    _fields_=[("status",ctypes.c_int32),("candidate_count",ctypes.c_int32),("min_c60",ctypes.c_int32),("max_c60",ctypes.c_int32),("sensitive",ctypes.c_int32),("min_command",ctypes.c_int32*4),("max_command",ctypes.c_int32*4)]


class _InteractiveOutput(ctypes.Structure):
    _fields_=[("status",ctypes.c_int32),("terminal",ctypes.c_int32),("epoch",ctypes.c_int32),("failed_rank",ctypes.c_int32),("integrated_ticks",ctypes.c_int32),("safety_violation",ctypes.c_int32),("exclusivity_violation",ctypes.c_int32),("event_count",ctypes.c_int32),("fail_delivered",ctypes.c_int64),("fail_demand",ctypes.c_int64),("total_delivered",ctypes.c_int64),("total_demand",ctypes.c_int64),("intact_delivered",ctypes.c_int64),("intact_demand",ctypes.c_int64),("prehistory_commands",ctypes.c_int32*24),("applied_decision",_DecisionTrace),("next_observation",_DecisionTrace)]


class _ClearanceInput(ctypes.Structure):
    _fields_=[("magic",ctypes.c_uint64),("abi",ctypes.c_int32),("holder_state",ctypes.c_int32)]


class _ClearanceOutput(ctypes.Structure):
    _fields_=[("status",ctypes.c_int32),("clearance_after_relinquish",ctypes.c_int32)]


class _PrehistoryOutput(ctypes.Structure):
    _fields_=[("status",ctypes.c_int32),("command",ctypes.c_int32*4)]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    result = subprocess.run(
        [
            str(locator), "-latest", "-products", "*", "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
            "installationPath",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    installation = Path(result.stdout.strip())
    if not installation.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return installation


def _compiler_path() -> Path:
    candidates = tuple(
        path
        for path in (_vs_installation() / "VC/Tools/MSVC").glob("*/bin/Hostx64/x64/cl.exe")
        if path.is_file()
    )
    if not candidates:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")
    def version(path: Path) -> tuple[int, ...]:
        try:
            return tuple(int(part) for part in path.parents[3].name.split("."))
        except ValueError:
            return (0,)
    return max(candidates, key=version)


@functools.lru_cache(maxsize=1)
def native_toolchain_identity() -> dict[str, object]:
    compiler = _compiler_path().resolve()
    probe = subprocess.run([str(compiler)], capture_output=True, text=True, check=False)
    output = "\n".join(
        line.strip()
        for line in (probe.stdout + "\n" + probe.stderr).splitlines()
        if line.strip()
    )
    if "Microsoft" not in output or "C/C++" not in output:
        raise NativeBackendError("MSVC compiler identity could not be read")
    return {
        "compiler_path": str(compiler),
        "compiler_sha256": _sha256_file(compiler),
        "compiler_version_output": output,
        "compile_flags": list(MSVC_COMPILE_FLAGS),
        "abi_version": NATIVE_ABI_VERSION,
    }


def native_source_sha256() -> str:
    digest=hashlib.sha256(b"VNFC-BPCR-R09-NATIVE-SOURCE-SET-v1\0")
    for path in (_SOURCE,_GENERAL_SOURCE,_CHECKER_SOURCE):
        payload=path.read_bytes();name=path.name.encode("ascii")
        digest.update(len(name).to_bytes(4,"big"));digest.update(name)
        digest.update(len(payload).to_bytes(8,"big"));digest.update(payload)
    return digest.hexdigest()


@functools.lru_cache(maxsize=1)
def native_build_key() -> str:
    toolchain = native_toolchain_identity()
    frozen = verify_immutable_inputs(_REPOSITORY_ROOT)
    digest = hashlib.sha256(b"VNFC-BPCR-R09-NATIVE-BUILD-v1\0")
    for item in (
        native_source_sha256(),
        contract_sha256(),
        str(frozen["science_card_sha256"]),
        str(frozen["public_law_sha256"]),
        str(toolchain["compiler_sha256"]),
    ):
        digest.update(item.encode("ascii"))
    for flag in MSVC_COMPILE_FLAGS:
        digest.update(len(flag).to_bytes(4, "big")); digest.update(flag.encode("ascii"))
    digest.update(NATIVE_ABI_VERSION.to_bytes(4, "big"))
    return digest.hexdigest()


def _compiled_path() -> Path:
    cache = Path(tempfile.gettempdir()) / "hmasd_vnfc_bpcr_r09_native" / native_build_key()
    dll = cache / "bpcr_backend.dll"
    if dll.is_file():
        return dll
    cache.mkdir(parents=True, exist_ok=True)
    vcvars = _vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    obj = cache / "bpcr_backend.obj"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'"{_SOURCE}" /Fo:"{obj}" /link /OUT:"{dll}"'
    )
    result = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=cache,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not dll.is_file():
        raise NativeBackendError(
            f"native BPCR compilation failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    return dll


@functools.lru_cache(maxsize=1)
def require_cpp_batched_backend(*, build_root: str | Path | None = None) -> ctypes.CDLL:
    """Compile/load the exact native DLL; reject overrides and never fall back."""
    if build_root is not None:
        raise ValueError("source-keyed BPCR loader does not accept build_root override")
    library = ctypes.CDLL(str(_compiled_path()))
    library.vnfc_bpcr_r09_abi_version.argtypes = []
    library.vnfc_bpcr_r09_abi_version.restype = ctypes.c_int32
    library.vnfc_bpcr_r09_fixture_magic.argtypes = []
    library.vnfc_bpcr_r09_fixture_magic.restype = ctypes.c_uint64
    if library.vnfc_bpcr_r09_abi_version() != NATIVE_ABI_VERSION:
        raise NativeBackendError("BPCR native ABI version mismatch")
    if library.vnfc_bpcr_r09_fixture_magic() != FIXTURE_MAGIC:
        raise NativeBackendError("BPCR native fixture magic mismatch")
    sizes = {
        "vnfc_bpcr_r09_sizeof_fixture_input": _FixtureInput,
        "vnfc_bpcr_r09_sizeof_fixture_output": _FixtureOutput,
        "vnfc_bpcr_r09_sizeof_host_input": _HostInput,
        "vnfc_bpcr_r09_sizeof_host_output": _HostOutput,
        "vnfc_bpcr_r09_sizeof_general_agent_input": _GeneralAgentInput,
        "vnfc_bpcr_r09_sizeof_episode_input": _EpisodeInput,
        "vnfc_bpcr_r09_sizeof_decision_trace": _DecisionTrace,
        "vnfc_bpcr_r09_sizeof_episode_output": _EpisodeOutput,
        "vnfc_bpcr_r09_sizeof_bcrh_input": _BCRHInput,
        "vnfc_bpcr_r09_sizeof_bcrh_candidate_record": _BCRHCandidateRecord,
        "vnfc_bpcr_r09_sizeof_bcrh_output": _BCRHOutput,
        "vnfc_bpcr_r09_sizeof_sensitivity_input": _SensitivityInput,
        "vnfc_bpcr_r09_sizeof_sensitivity_output": _SensitivityOutput,
        "vnfc_bpcr_r09_sizeof_interactive_output": _InteractiveOutput,
        "vnfc_bpcr_r09_sizeof_clearance_input": _ClearanceInput,
        "vnfc_bpcr_r09_sizeof_clearance_output": _ClearanceOutput,
        "vnfc_bpcr_r09_sizeof_prehistory_output": _PrehistoryOutput,
    }
    for symbol, structure in sizes.items():
        function = getattr(library, symbol)
        function.argtypes = []
        function.restype = ctypes.c_size_t
        if int(function()) != ctypes.sizeof(structure):
            raise NativeBackendError(f"BPCR native ABI size mismatch for {symbol}")
    library.vnfc_bpcr_r09_run_fixture_batch.argtypes = [
        ctypes.POINTER(_FixtureInput), ctypes.c_int32, ctypes.POINTER(_FixtureOutput)
    ]
    library.vnfc_bpcr_r09_run_fixture_batch.restype = ctypes.c_int32
    library.vnfc_bpcr_r09_run_host_batch.argtypes = [
        ctypes.POINTER(_HostInput), ctypes.c_int32, ctypes.POINTER(_HostOutput)
    ]
    library.vnfc_bpcr_r09_run_host_batch.restype = ctypes.c_int32
    library.vnfc_bpcr_r09_run_episode_batch.argtypes=[ctypes.POINTER(_EpisodeInput),ctypes.c_int32,ctypes.POINTER(_EpisodeOutput)]
    library.vnfc_bpcr_r09_run_episode_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_run_bcrh_batch.argtypes=[ctypes.POINTER(_BCRHInput),ctypes.c_int32,ctypes.POINTER(_BCRHOutput)]
    library.vnfc_bpcr_r09_run_bcrh_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_checker_detects_perturbation.argtypes=[ctypes.POINTER(_BCRHInput),ctypes.c_int32,ctypes.POINTER(ctypes.c_int32)]
    library.vnfc_bpcr_r09_checker_detects_perturbation.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_run_sensitivity_batch.argtypes=[ctypes.POINTER(_SensitivityInput),ctypes.c_int32,ctypes.POINTER(_SensitivityOutput)]
    library.vnfc_bpcr_r09_run_sensitivity_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_interactive_reset_batch.argtypes=[ctypes.POINTER(_EpisodeInput),ctypes.c_int32,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(_InteractiveOutput)]
    library.vnfc_bpcr_r09_interactive_reset_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_interactive_step_batch.argtypes=[ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_int32),ctypes.c_int32,ctypes.POINTER(_InteractiveOutput)]
    library.vnfc_bpcr_r09_interactive_step_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_interactive_bcrh_batch.argtypes=[ctypes.POINTER(ctypes.c_void_p),ctypes.c_int32,ctypes.POINTER(_BCRHOutput)]
    library.vnfc_bpcr_r09_interactive_bcrh_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_interactive_sensitivity_batch.argtypes=[ctypes.POINTER(ctypes.c_void_p),ctypes.c_int32,ctypes.POINTER(_SensitivityOutput)]
    library.vnfc_bpcr_r09_interactive_sensitivity_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_interactive_close_batch.argtypes=[ctypes.POINTER(ctypes.c_void_p),ctypes.c_int32]
    library.vnfc_bpcr_r09_interactive_close_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_run_clearance_batch.argtypes=[ctypes.POINTER(_ClearanceInput),ctypes.c_int32,ctypes.POINTER(_ClearanceOutput)]
    library.vnfc_bpcr_r09_run_clearance_batch.restype=ctypes.c_int32
    library.vnfc_bpcr_r09_run_first_prehistory_batch.argtypes=[ctypes.POINTER(_EpisodeInput),ctypes.c_int32,ctypes.POINTER(_PrehistoryOutput)]
    library.vnfc_bpcr_r09_run_first_prehistory_batch.restype=ctypes.c_int32
    return library


def run_native_fixture_batch(fixtures: object) -> tuple[dict[str, object], ...]:
    """Run a nonempty deterministic fixture batch through the native boundary."""
    materialized = tuple(fixtures)  # type: ignore[arg-type]
    if not materialized:
        raise ValueError("native BPCR fixture batch must be nonempty")
    native_inputs = (_FixtureInput * len(materialized))()
    for index, fixture in enumerate(materialized):
        values = (
            int(fixture.failed_zone), int(fixture.demand_1), int(fixture.demand_2),
            int(fixture.blocked_1), int(fixture.blocked_2),
            int(fixture.failed_relay_present),
        )
        native_inputs[index] = _FixtureInput(
            FIXTURE_MAGIC, NATIVE_ABI_VERSION, *values
        )
    outputs = (_FixtureOutput * len(materialized))()
    status = require_cpp_batched_backend().vnfc_bpcr_r09_run_fixture_batch(
        native_inputs, len(materialized), outputs
    )
    if status != 0:
        raise NativeBackendError(f"native BPCR fixture batch failed with status {status}")
    converted = []
    for output in outputs:
        if output.status != 0:
            raise NativeBackendError(f"native BPCR fixture status was {output.status}")
        converted.append({
            "candidate_count": int(output.candidate_count),
            "scorer_command": tuple(int(x) for x in output.scorer_command),
            "checker_command": tuple(int(x) for x in output.checker_command),
            "scorer_checker_equal": bool(output.scorer_checker_equal),
            "independent_enumerator_equal": bool(output.independent_enumerator_equal),
            "witness_present": bool(output.witness_present),
            "earliest_safe_executor_rank": int(output.earliest_safe_executor_rank),
            "needed_relay_rank": int(output.needed_relay_rank),
            "selected_floor": (
                int(output.selected_floor_num), int(output.selected_floor_den)
            ),
            "selected_event_count": int(output.selected_event_count),
            "selected_reward_record_count": int(output.selected_reward_record_count),
            "post60_reduced_verified": bool(output.post60_reduced_verified),
        })
    return tuple(converted)


def run_native_host_batch(fixtures: object) -> tuple[dict[str, object], ...]:
    """Execute nonempty reset-to-terminal public-law command tapes in C++."""
    materialized=tuple(fixtures)  # type: ignore[arg-type]
    if not materialized:raise ValueError("native BPCR host batch must be nonempty")
    inputs=(_HostInput*len(materialized))()
    for index,fixture in enumerate(materialized):
        fixture.validate();item=_HostInput();item.fixture_magic=FIXTURE_MAGIC;item.abi_version=NATIVE_ABI_VERSION;item.selected_mask=fixture.selected_mask;item.failed_zone=fixture.failed_zone
        for j in range(12):
            item.demand_1[j]=fixture.demand_1[j];item.demand_2[j]=fixture.demand_2[j];item.blocked_1[j]=fixture.blocked_1[j];item.blocked_2[j]=fixture.blocked_2[j]
            for token,value in enumerate(fixture.commands[j]):item.commands[4*j+token]=255 if value is None else value
        inputs[index]=item
    outputs=(_HostOutput*len(materialized))();status=require_cpp_batched_backend().vnfc_bpcr_r09_run_host_batch(inputs,len(materialized),outputs)
    if status!=0:raise NativeBackendError(f"native BPCR host batch failed with status {status}")
    result=[]
    for output in outputs:
        if output.status!=0:raise NativeBackendError(f"native BPCR host item status was {output.status}")
        result.append({"integrated_ticks":int(output.integrated_ticks),"decision_count":int(output.decision_count),"failed_rank":int(output.failed_rank),"fail_endpoint":(int(output.fail_delivered),int(output.fail_demand)),"total_endpoint":(int(output.total_delivered),int(output.total_demand)),"intact_endpoint":(int(output.intact_delivered),int(output.intact_demand)),"final_token_state":tuple(int(x) for x in output.final_token_state),"final_acquisition_elapsed":tuple(int(x) for x in output.final_acquisition_elapsed),"safety_violation":bool(output.safety_violation),"exclusivity_violation":bool(output.exclusivity_violation),"event_count":int(output.event_count)})
    return tuple(result)


def _agent_input(agent: object) -> _GeneralAgentInput:
    return _GeneralAgentInput(*(int(getattr(agent,name)) for name,_ in _GeneralAgentInput._fields_))


def _episode_input(fixture: object) -> _EpisodeInput:
    fixture.validate();item=_EpisodeInput();item.magic=FIXTURE_MAGIC;item.abi=NATIVE_ABI_VERSION;item.failed_zone=fixture.failed_zone;item.active_count=len(fixture.agents)
    for j,agent in enumerate(fixture.agents):item.agents[j]=_agent_input(agent)
    for j in range(12):item.demand_1[j]=fixture.demand_1[j];item.demand_2[j]=fixture.demand_2[j];item.blocked_1[j]=fixture.blocked_1[j];item.blocked_2[j]=fixture.blocked_2[j]
    for e in range(6):
        for t,value in enumerate(fixture.post_commands[e]):item.post_commands[4*e+t]=255 if value is None else value
        for j,rank in enumerate(fixture.post_presentations[e]):item.post_presentation[8*e+j]=rank
    return item


def _trace_dict(trace: _DecisionTrace) -> dict[str, object]:
    active=int(trace.active_count)
    return {"epoch":int(trace.epoch),"active_count":active,"command":tuple(None if int(x)==255 else int(x) for x in trace.command),"token_state":tuple(int(x) for x in trace.token_state),"token_elapsed":tuple(int(x) for x in trace.token_elapsed),"legality":tuple(int(x) for x in trace.legality[:active*4]),"eta":tuple(int(x) for x in trace.eta[:active*4]),"margin_fifths":tuple(int(x) for x in trace.margin_fifths[:active*4]),"agent_rows":tuple(float(x) for x in trace.agent_rows[:active*38]),"zone_rows":tuple(float(x) for x in trace.zone_rows),"globals":tuple(float(x) for x in trace.globals)}


def _interactive_dict(output: _InteractiveOutput) -> dict[str, object]:
    return {"terminal":bool(output.terminal),"epoch":int(output.epoch),"failed_rank":int(output.failed_rank),"integrated_ticks":int(output.integrated_ticks),"safety_violation":bool(output.safety_violation),"exclusivity_violation":bool(output.exclusivity_violation),"event_count":int(output.event_count),"fail_endpoint":(int(output.fail_delivered),int(output.fail_demand)),"total_endpoint":(int(output.total_delivered),int(output.total_demand)),"intact_endpoint":(int(output.intact_delivered),int(output.intact_demand)),"prehistory_commands":tuple(tuple(None if int(output.prehistory_commands[4*e+t])==255 else int(output.prehistory_commands[4*e+t]) for t in range(4)) for e in range(6)),"applied_decision":_trace_dict(output.applied_decision),"next_observation":None if output.terminal else _trace_dict(output.next_observation)}


class NativeInteractiveBatch:
    """Opaque C++-owned batch of revision-09 public-law episode states."""
    def __init__(self,fixtures:object):
        materialized=tuple(fixtures)  # type: ignore[arg-type]
        if not materialized:raise ValueError("native interactive batch must be nonempty")
        self._width=len(materialized);self._library=require_cpp_batched_backend();inputs=(_EpisodeInput*self._width)(*(_episode_input(x) for x in materialized));self._handles=(ctypes.c_void_p*self._width)();outputs=(_InteractiveOutput*self._width)()
        status=self._library.vnfc_bpcr_r09_interactive_reset_batch(inputs,self._width,self._handles,outputs)
        if status!=0:raise NativeBackendError(f"native interactive reset failed with status {status}")
        self._open=True;self.initial=tuple(_interactive_dict(x) for x in outputs)
    def step(self,commands:object)->tuple[dict[str,object],...]:
        if not self._open:raise NativeBackendError("native interactive batch is closed")
        rows=tuple(commands)  # type: ignore[arg-type]
        if len(rows)!=self._width or any(len(tuple(row))!=4 for row in rows):raise ValueError("one width-four command is required per native session")
        packed=(ctypes.c_int32*(4*self._width))()
        for i,row in enumerate(rows):
            for t,value in enumerate(row):packed[4*i+t]=255 if value is None else int(value)
        outputs=(_InteractiveOutput*self._width)();status=self._library.vnfc_bpcr_r09_interactive_step_batch(self._handles,packed,self._width,outputs)
        if status!=0:raise NativeBackendError(f"native interactive step failed with status {status}")
        return tuple(_interactive_dict(x) for x in outputs)
    def bcrh(self,*,include_candidate_records:bool=False)->tuple[dict[str,object],...]:
        if not self._open:raise NativeBackendError("native interactive batch is closed")
        outputs=(_BCRHOutput*self._width)();status=self._library.vnfc_bpcr_r09_interactive_bcrh_batch(self._handles,self._width,outputs)
        if status!=0:raise NativeBackendError(f"native interactive BCRH failed with status {status}")
        rows=[]
        for o in outputs:
            row={"candidate_count":int(o.candidate_count),"scorer_command":tuple(None if int(x)==255 else int(x) for x in o.scorer_command),"checker_command":tuple(None if int(x)==255 else int(x) for x in o.checker_command),"scorer_checker_equal":bool(o.scorer_checker_equal),"independent_enumerator_equal":bool(o.independent_enumerator_equal),"post60_reduced":bool(o.post60_reduced),"floor":(int(o.floor_num),int(o.floor_den)),"releases":int(o.releases),"objective_limbs":tuple(int(x) for x in o.objective_limbs),"checker_objective_limbs":tuple(int(x) for x in o.checker_objective_limbs),"candidate_digest":int(o.candidate_digest),"checker_digest":int(o.checker_digest)}
            if include_candidate_records:row["candidate_records"]=tuple({"command":tuple(None if int(x)==255 else int(x) for x in record.command),"exact_match":bool(record.exact_match)} for record in o.records[:o.candidate_count])
            rows.append(row)
        return tuple(rows)
    def sensitivity(self)->tuple[dict[str,object],...]:
        if not self._open:raise NativeBackendError("native interactive batch is closed")
        outputs=(_SensitivityOutput*self._width)();status=self._library.vnfc_bpcr_r09_interactive_sensitivity_batch(self._handles,self._width,outputs)
        if status!=0:raise NativeBackendError(f"native interactive sensitivity failed with status {status}")
        return tuple({"candidate_count":int(o.candidate_count),"min_c60":int(o.min_c60),"max_c60":int(o.max_c60),"sensitive":bool(o.sensitive)} for o in outputs)
    def close(self)->None:
        if not self._open:return
        status=self._library.vnfc_bpcr_r09_interactive_close_batch(self._handles,self._width)
        if status!=0:raise NativeBackendError(f"native interactive close failed with status {status}")
        self._open=False
    def __enter__(self)->"NativeInteractiveBatch":return self
    def __exit__(self,*_:object)->None:self.close()


def run_native_clearance_batch(holder_states:object)->tuple[int,...]:
    materialized=tuple(int(x) for x in holder_states)  # type: ignore[arg-type]
    if not materialized:raise ValueError("native clearance probe batch must be nonempty")
    inputs=(_ClearanceInput*len(materialized))(*(_ClearanceInput(FIXTURE_MAGIC,NATIVE_ABI_VERSION,x) for x in materialized));outputs=(_ClearanceOutput*len(materialized))()
    status=require_cpp_batched_backend().vnfc_bpcr_r09_run_clearance_batch(inputs,len(materialized),outputs)
    if status!=0:raise NativeBackendError(f"native clearance probe failed with status {status}")
    return tuple(int(x.clearance_after_relinquish) for x in outputs)


def run_native_first_prehistory_batch(fixtures:object)->tuple[tuple[int|None,...],...]:
    materialized=tuple(fixtures)  # type: ignore[arg-type]
    if not materialized:raise ValueError("native prehistory batch must be nonempty")
    inputs=(_EpisodeInput*len(materialized))(*(_episode_input(x) for x in materialized));outputs=(_PrehistoryOutput*len(materialized))()
    status=require_cpp_batched_backend().vnfc_bpcr_r09_run_first_prehistory_batch(inputs,len(materialized),outputs)
    if status!=0:raise NativeBackendError(f"native prehistory probe failed with status {status}")
    return tuple(tuple(None if int(v)==255 else int(v) for v in x.command) for x in outputs)


def run_native_episode_batch(fixtures: object) -> tuple[dict[str, object], ...]:
    """Run internal-prehistory, observable, reset-to-terminal native episodes."""
    materialized=tuple(fixtures)  # type: ignore[arg-type]
    if not materialized:raise ValueError("native general episode batch must be nonempty")
    inputs=(_EpisodeInput*len(materialized))()
    for index,fixture in enumerate(materialized):
        inputs[index]=_episode_input(fixture)
    outputs=(_EpisodeOutput*len(materialized))();status=require_cpp_batched_backend().vnfc_bpcr_r09_run_episode_batch(inputs,len(materialized),outputs)
    if status!=0:raise NativeBackendError(f"native general episode batch failed with status {status}")
    rows=[]
    for output in outputs:
        traces=[]
        for trace in output.traces:
            traces.append(_trace_dict(trace))
        rows.append({"failed_rank":int(output.failed_rank),"integrated_ticks":int(output.integrated_ticks),"prehistory_decisions":int(output.prehistory_decisions),"post_decisions":int(output.post_decisions),"safety_violation":bool(output.safety_violation),"exclusivity_violation":bool(output.exclusivity_violation),"event_count":int(output.event_count),"fail_endpoint":(int(output.fail_delivered),int(output.fail_demand)),"total_endpoint":(int(output.total_delivered),int(output.total_demand)),"intact_endpoint":(int(output.intact_delivered),int(output.intact_demand)),"prehistory_commands":tuple(tuple(None if int(output.prehistory_commands[4*e+t])==255 else int(output.prehistory_commands[4*e+t]) for t in range(4)) for e in range(6)),"traces":tuple(traces)})
    return tuple(rows)


def run_native_bcrh_batch(
    fixtures: object, *, include_candidate_records: bool = False
) -> tuple[dict[str, object], ...]:
    """Run arbitrary-current-state k=0..5 BCRH scorer and independent checker."""
    materialized=tuple(fixtures)  # type: ignore[arg-type]
    if not materialized:raise ValueError("native general BCRH batch must be nonempty")
    inputs=(_BCRHInput*len(materialized))()
    for index,fixture in enumerate(materialized):
        inputs[index]=_bcrh_input(fixture)
    outputs=(_BCRHOutput*len(materialized))();status=require_cpp_batched_backend().vnfc_bpcr_r09_run_bcrh_batch(inputs,len(materialized),outputs)
    if status!=0:raise NativeBackendError(f"native general BCRH batch failed with status {status}")
    rows=[]
    for o in outputs:
        fixture=materialized[len(rows)]
        row={"candidate_count":int(o.candidate_count),"scorer_command":tuple(None if int(x)==255 else int(x) for x in o.scorer_command),"checker_command":tuple(None if int(x)==255 else int(x) for x in o.checker_command),"scorer_checker_equal":bool(o.scorer_checker_equal),"independent_enumerator_equal":bool(o.independent_enumerator_equal),"post60_reduced":bool(o.post60_reduced),"floor":(int(o.floor_num),int(o.floor_den)),"releases":int(o.releases),"event_records":int(o.event_records),"reward_records":int(o.reward_records),"objective_limbs":tuple(int(x) for x in o.objective_limbs),"checker_objective_limbs":tuple(int(x) for x in o.checker_objective_limbs),"objective_denominator_factors":(2,20,5_354_228_880,2500,5-int(fixture.epoch)),"candidate_digest":int(o.candidate_digest),"checker_digest":int(o.checker_digest)}
        if include_candidate_records:
            row["candidate_records"]=tuple({"command":tuple(None if int(x)==255 else int(x) for x in record.command),"floor":(int(record.floor_num),int(record.floor_den)),"releases":int(record.releases),"objective_limbs":tuple(int(x) for x in record.objective_limbs),"checker_floor":(int(record.checker_floor_num),int(record.checker_floor_den)),"checker_releases":int(record.checker_releases),"checker_objective_limbs":tuple(int(x) for x in record.checker_objective_limbs),"exact_match":bool(record.exact_match)} for record in o.records[:o.candidate_count])
        rows.append(row)
    return tuple(rows)


def checker_detects_scorer_perturbation(fixtures: object)->tuple[bool,...]:
    materialized=tuple(fixtures)  # type: ignore[arg-type]
    if not materialized:raise ValueError("checker perturbation batch must be nonempty")
    inputs=(_BCRHInput*len(materialized))(*(_bcrh_input(x) for x in materialized));detected=(ctypes.c_int32*len(materialized))()
    status=require_cpp_batched_backend().vnfc_bpcr_r09_checker_detects_perturbation(inputs,len(materialized),detected)
    if status!=0:raise NativeBackendError(f"native checker perturbation probe failed with status {status}")
    return tuple(bool(x) for x in detected)


def probe_bcrh_over_cap_rejection()->dict[str,object]:
    """Construction-only direct ABI canary for the forbidden active-N=8 boundary."""
    item=_BCRHInput();item.magic=FIXTURE_MAGIC;item.abi=NATIVE_ABI_VERSION;item.epoch=5;item.failed_zone=1;item.active_count=8
    for index in range(8):
        agent=_GeneralAgentInput();agent.rank=index+1;agent.opaque_rank=index+1;agent.fast=index%2;agent.radio=1+(index%2);agent.node=0;agent.edge_from=-1;agent.edge_to=-1;agent.edge_remaining=0;agent.destination_node=0;agent.token=-1;agent.token_state=0;agent.acquisition_elapsed=0;agent.energy_fifths=800;item.agents[index]=agent
    item.accrued_fail_delivered=200;item.accrued_fail_demand=240;item.accrued_total_delivered=400;item.accrued_total_demand=480;item.demand_1=2;item.demand_2=2;item.blocked_1=1;item.blocked_2=1
    output=_BCRHOutput();ctypes.memset(ctypes.byref(output),0xA5,ctypes.sizeof(output));before=ctypes.string_at(ctypes.byref(output),ctypes.sizeof(output))
    status=require_cpp_batched_backend().vnfc_bpcr_r09_run_bcrh_batch(ctypes.byref(item),1,ctypes.byref(output));after=ctypes.string_at(ctypes.byref(output),ctypes.sizeof(output))
    return {"active_count":8,"unconstrained_command_count":3393,"candidate_cap":1961,"status":int(status),"output_unchanged":before==after}


def _bcrh_input(fixture: object) -> _BCRHInput:
    fixture.validate();item=_BCRHInput();item.magic=FIXTURE_MAGIC;item.abi=NATIVE_ABI_VERSION;item.epoch=fixture.epoch;item.failed_zone=fixture.failed_zone;item.active_count=len(fixture.agents)
    for j,agent in enumerate(fixture.agents):item.agents[j]=_agent_input(agent)
    for t,value in enumerate(fixture.clearance):item.clearance[t]=value
    for name in ("accrued_fail_delivered","accrued_fail_demand","accrued_total_delivered","accrued_total_demand","demand_1","demand_2","blocked_1","blocked_2"):setattr(item,name,int(getattr(fixture,name)))
    return item


def run_native_sensitivity_batch(fixtures: object) -> tuple[dict[str,object],...]:
    materialized=tuple(fixtures)  # type: ignore[arg-type]
    if not materialized:raise ValueError("native sensitivity batch must be nonempty")
    inputs=(_SensitivityInput*len(materialized))()
    for index,fixture in enumerate(materialized):
        fixture.validate();item=_SensitivityInput();item.current=_bcrh_input(fixture.current)
        for j in range(3):item.demand_1[j]=fixture.demand_1[j];item.demand_2[j]=fixture.demand_2[j];item.blocked_1[j]=fixture.blocked_1[j];item.blocked_2[j]=fixture.blocked_2[j]
        inputs[index]=item
    outputs=(_SensitivityOutput*len(materialized))();status=require_cpp_batched_backend().vnfc_bpcr_r09_run_sensitivity_batch(inputs,len(materialized),outputs)
    if status!=0:raise NativeBackendError(f"native action-sensitivity batch failed with status {status}")
    return tuple({"candidate_count":int(o.candidate_count),"min_c60":int(o.min_c60),"max_c60":int(o.max_c60),"sensitive":bool(o.sensitive),"min_command":tuple(None if int(x)==255 else int(x) for x in o.min_command),"max_command":tuple(None if int(x)==255 else int(x) for x in o.max_command)} for o in outputs)


def native_artifact_identity() -> dict[str, object]:
    """Build/load and return the frozen result-blind artifact identity schema."""
    library = require_cpp_batched_backend()
    path = Path(vars(library)["_name"]).resolve()
    frozen = verify_immutable_inputs(_REPOSITORY_ROOT)
    from .fixtures import (
        BCRHFixture,
        deterministic_general_bcrh,
        deterministic_general_episode,
        deterministic_host_fixture,
        deterministic_sensitivity_fixture,
    )
    smoke = run_native_fixture_batch((BCRHFixture(1, 1, 1, 0, 0, 0),))[0]
    host_smoke = run_native_host_batch((deterministic_host_fixture(1),))[0]
    episode_smokes = tuple(
        run_native_episode_batch(tuple(deterministic_general_episode(1 + i % 2) for i in range(width)))
        for width in (1, 8, 32)
    )
    interactive_smokes=[]
    for width,oracle in zip((1,8,32),episode_smokes):
        fixtures=tuple(deterministic_general_episode(1+i%2) for i in range(width));batch=NativeInteractiveBatch(fixtures)
        try:
            observations=tuple(row["next_observation"] for row in batch.initial)
            initial_ok=all(row is not None and row["epoch"]==0 for row in observations)
            for _ in range(6):
                commands=tuple(fixture.post_commands[int(observation["epoch"])] for fixture,observation in zip(fixtures,observations))
                terminal=batch.step(commands);observations=tuple(row["next_observation"] for row in terminal)
            interactive_smokes.append((initial_ok,terminal,oracle))
        finally:batch.close()
    general_bcrh_smokes = tuple(
        run_native_bcrh_batch(tuple(deterministic_general_bcrh(i % 6) for i in range(width)))
        for width in (1, 8, 32)
    )
    record_smoke=run_native_bcrh_batch((deterministic_general_bcrh(0),),include_candidate_records=True)[0]
    sensitivity_smoke=run_native_sensitivity_batch((deterministic_sensitivity_fixture(),))[0]
    bcrh_ok = (
        smoke["scorer_checker_equal"]
        and smoke["independent_enumerator_equal"]
        and smoke["witness_present"]
        and smoke["post60_reduced_verified"]
    )
    host_ok = all(initial_ok and all(row["terminal"] and row["integrated_ticks"]==240 and row["next_observation"] is None and not row["safety_violation"] and not row["exclusivity_violation"] and row["fail_endpoint"]==expected["fail_endpoint"] and row["total_endpoint"]==expected["total_endpoint"] and row["intact_endpoint"]==expected["intact_endpoint"] for row,expected in zip(terminal,oracle)) for initial_ok,terminal,oracle in interactive_smokes)
    general_bcrh_ok = all(
        row["scorer_checker_equal"]
        and row["independent_enumerator_equal"]
        and row["post60_reduced"] == (fixture.epoch >= 3)
        and row["objective_limbs"] == row["checker_objective_limbs"]
        and row["candidate_digest"] == row["checker_digest"]
        for width, batch in zip((1, 8, 32), general_bcrh_smokes)
        for fixture, row in zip(
            tuple(deterministic_general_bcrh(i % 6) for i in range(width)), batch
        )
    )
    sensitivity_ok=(sensitivity_smoke["candidate_count"]>1 and sensitivity_smoke["sensitive"]==(sensitivity_smoke["max_c60"]-sensitivity_smoke["min_c60"]>=6))
    every_record_ok=all(record["exact_match"] and record["floor"]==record["checker_floor"] and record["releases"]==record["checker_releases"] and record["objective_limbs"]==record["checker_objective_limbs"] for record in record_smoke["candidate_records"])
    if not bcrh_ok or not host_ok or not general_bcrh_ok or not sensitivity_ok or not every_record_ok:
        raise NativeBackendError("native BPCR smoke conformance failed")
    return {
        "schema": "VNFC-BPCR-R09-NATIVE-ARTIFACT-IDENTITY-v1",
        "artifact_path": str(path),
        "artifact_sha256": _sha256_file(path),
        "artifact_size": path.stat().st_size,
        "build_key": native_build_key(),
        "native_source_path": str(_SOURCE.resolve()),
        "native_source_paths": [str(_SOURCE.resolve()), str(_GENERAL_SOURCE.resolve()),str(_CHECKER_SOURCE.resolve())],
        "native_source_sha256": native_source_sha256(),
        "contract_sha256": contract_sha256(),
        "toolchain": native_toolchain_identity(),
        "immutable_inputs": frozen,
        "abi_version": NATIVE_ABI_VERSION,
        "abi_version_function": "vnfc_bpcr_r09_abi_version",
        "exports": [
            "vnfc_bpcr_r09_abi_version",
            "vnfc_bpcr_r09_fixture_magic",
            "vnfc_bpcr_r09_sizeof_fixture_input",
            "vnfc_bpcr_r09_sizeof_fixture_output",
            "vnfc_bpcr_r09_run_fixture_batch",
            "vnfc_bpcr_r09_sizeof_host_input",
            "vnfc_bpcr_r09_sizeof_host_output",
            "vnfc_bpcr_r09_run_host_batch",
            "vnfc_bpcr_r09_sizeof_general_agent_input",
            "vnfc_bpcr_r09_sizeof_episode_input",
            "vnfc_bpcr_r09_sizeof_decision_trace",
            "vnfc_bpcr_r09_sizeof_episode_output",
            "vnfc_bpcr_r09_sizeof_bcrh_input",
            "vnfc_bpcr_r09_sizeof_bcrh_candidate_record",
            "vnfc_bpcr_r09_sizeof_bcrh_output",
            "vnfc_bpcr_r09_sizeof_sensitivity_input",
            "vnfc_bpcr_r09_sizeof_sensitivity_output",
            "vnfc_bpcr_r09_sizeof_interactive_output",
            "vnfc_bpcr_r09_sizeof_clearance_input",
            "vnfc_bpcr_r09_sizeof_clearance_output",
            "vnfc_bpcr_r09_sizeof_prehistory_output",
            "vnfc_bpcr_r09_run_episode_batch",
            "vnfc_bpcr_r09_run_bcrh_batch",
            "vnfc_bpcr_r09_checker_detects_perturbation",
            "vnfc_bpcr_r09_run_sensitivity_batch",
            "vnfc_bpcr_r09_interactive_reset_batch",
            "vnfc_bpcr_r09_interactive_step_batch",
            "vnfc_bpcr_r09_interactive_bcrh_batch",
            "vnfc_bpcr_r09_interactive_sensitivity_batch",
            "vnfc_bpcr_r09_interactive_close_batch",
            "vnfc_bpcr_r09_run_clearance_batch",
            "vnfc_bpcr_r09_run_first_prehistory_batch",
        ],
        "abi_sizes": {
            "fixture_input": ctypes.sizeof(_FixtureInput),
            "fixture_output": ctypes.sizeof(_FixtureOutput),
            "host_input": ctypes.sizeof(_HostInput),
            "host_output": ctypes.sizeof(_HostOutput),
            "general_agent_input": ctypes.sizeof(_GeneralAgentInput),
            "episode_input": ctypes.sizeof(_EpisodeInput),
            "decision_trace": ctypes.sizeof(_DecisionTrace),
            "episode_output": ctypes.sizeof(_EpisodeOutput),
            "bcrh_input": ctypes.sizeof(_BCRHInput),
            "bcrh_output": ctypes.sizeof(_BCRHOutput),
            "bcrh_candidate_record": ctypes.sizeof(_BCRHCandidateRecord),
            "sensitivity_input": ctypes.sizeof(_SensitivityInput),
            "sensitivity_output": ctypes.sizeof(_SensitivityOutput),
            "interactive_output": ctypes.sizeof(_InteractiveOutput),
            "clearance_input": ctypes.sizeof(_ClearanceInput),
            "clearance_output": ctypes.sizeof(_ClearanceOutput),
            "prehistory_output": ctypes.sizeof(_PrehistoryOutput),
        },
        "binding_kind": "ctypes_cdll",
        "batch_api": True,
        "full_reset_step_cpp": host_ok,
        "bcrh_scorer_checker_cpp": bcrh_ok and general_bcrh_ok and every_record_ok,
        "action_sensitivity_cpp": sensitivity_ok,
        "deterministic_smoke_conformance": bcrh_ok and host_ok and general_bcrh_ok and sensitivity_ok,
        "interactive_conformance_widths": [1,8,32],
        "python_environment_loop": False,
        "python_action_loop": False,
        "legacy_materialized_host_fixture_only": False,
        "legacy_tape_conformance_only": True,
        "python_fallback": False,
        "build_root_override_accepted": False,
    }
