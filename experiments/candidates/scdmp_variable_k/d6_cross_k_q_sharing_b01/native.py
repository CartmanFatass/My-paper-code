"""Direct loader and rollout seam for the owned TAU_LEAK=.92 native host."""

from __future__ import annotations

import base64
import ctypes
import os
from pathlib import Path
import struct
import subprocess

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    native_backend as abi,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_state import (
    DisturbanceHold,
)

from .rng import disturbance_tape


ACTIONS = ((0, 7), (0, 13), (10, 7), (10, 13), (12, 7), (12, 13))
GRAPHS = ("HR", "RH")
HORIZON = 364
PRE_EVENT_Q = 0
SOURCE_STREAMS = ((9011, 7), (9013, 13))
TARGET_TICKS = (64, 160, 256)
EVALUATION_DOMAIN = 9029


def compile_host(build_root: Path) -> ctypes.CDLL:
    """Derive and compile the .92 host without a cache or receipt."""

    build_root.mkdir(parents=True, exist_ok=True)
    canonical = Path(abi.__file__).with_name("native") / "mf_rs_native.cpp"
    source = build_root / "d6_native.cpp"
    source.write_text(
        canonical.read_text(encoding="utf-8").replace(
            "tau[i] - 0.88", "tau[i] - 0.92",
        ),
        encoding="utf-8",
    )
    compiler = abi._compiler_path()
    vcvars = abi._vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    obj = build_root / "d6_native.obj"
    dll = build_root / "d6_native.dll"
    command = (
        f'call "{vcvars}" >nul && "{compiler}" /nologo /std:c++20 /O2 /EHsc /LD /W4 '
        f'"{source}" /Fo:"{obj}" /Fe:"{dll}"'
    )
    completed = subprocess.run(
        command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=build_root, capture_output=True, text=True,
    )
    if completed.returncode != 0 or not dll.is_file():
        raise RuntimeError(f"native compilation failed: {completed.stdout}\n{completed.stderr}")
    obj.unlink(missing_ok=True)
    return abi._configure(ctypes.CDLL(str(dll)))


class Host:
    def __init__(self, build_root: Path) -> None:
        self.library = compile_host(build_root)
        self._previous = None

    def __enter__(self) -> "Host":
        self._previous = abi.require_native_backend
        abi.require_native_backend = lambda: self.library
        return self

    def __exit__(self, *_args: object) -> None:
        abi.require_native_backend = self._previous

    def source_states(
        self, targets: tuple[int, ...] = TARGET_TICKS,
    ) -> tuple[list[dict[str, object]], int]:
        states: list[dict[str, object]] = []
        transitions = 0
        for seed, source_k in SOURCE_STREAMS:
            session = abi.NativeSession.reset(
                width=1, k=source_k, pre_event_q=PRE_EVENT_Q,
                initial_v=0.015, initial_y=0.0, initial_phi=0.0,
            )
            target_index = 0
            renewal = 0
            while target_index < len(targets):
                output = session.outputs[0]
                if output.terminal:
                    raise RuntimeError(f"source stream {seed} terminated before target {targets[target_index]}")
                if output.tick >= targets[target_index]:
                    source = session.state_bytes()[0]
                    twins = abi.NativeSession.from_state_bytes((source, source))
                    twin_outputs = twins.apply_orders(GRAPHS)
                    public = tuple(twin_outputs[0].observation)
                    if struct.pack("<18d", *public) != struct.pack("<18d", *twin_outputs[1].observation):
                        raise RuntimeError("HR/RH actor-visible observations differ")
                    states.append({
                        "state_id": f"source-{seed}-target-{targets[target_index]:03d}",
                        "source_seed": seed, "source_k": source_k,
                        "target_tick": targets[target_index], "boundary_tick": output.tick,
                        "observation": list(public),
                        "hr_state_b64": base64.b64encode(twins.state_bytes()[0]).decode("ascii"),
                        "rh_state_b64": base64.b64encode(twins.state_bytes()[1]).decode("ascii"),
                    })
                    target_index += 1
                    continue
                tape = disturbance_tape(seed, "source-disturbance", (renewal,), holds=1)
                output = session.step((0,), tape)[0]
                transitions += output.ticks_advanced
                renewal += 1
        return states, transitions

    @staticmethod
    def _duration_clone(payload: bytes, k: int) -> bytes:
        state = abi._state_from_bytes(payload)
        state.current_k = k
        state.cached.next_k = k
        state.cached.hold_k = 0
        state.cached.observation[16] = k / 13.0
        return abi._state_bytes(state)

    def mission(
        self, state: dict[str, object], graph: str, action: tuple[int, int],
        tape: tuple[DisturbanceHold, ...],
    ) -> tuple[float, int]:
        key = "hr_state_b64" if graph == "HR" else "rh_state_b64"
        payload = base64.b64decode(str(state[key]))
        z, k = action
        session = abi.NativeSession.from_state_bytes((self._duration_clone(payload, k),))
        renewal = 0
        output = session.outputs[0]
        transitions = 0
        while not output.terminal:
            if renewal >= len(tape):
                raise RuntimeError("disturbance tape exhausted")
            held_action = z if renewal == 0 else 0
            output = session.step((held_action,), (tape[renewal],))[0]
            transitions += output.ticks_advanced
            renewal += 1
        return output.completion_value, transitions

    def evaluation_tape(self, state_id: str, tape: int) -> tuple[DisturbanceHold, ...]:
        return disturbance_tape(EVALUATION_DOMAIN, "evaluation-disturbance", (state_id, tape))

    def training_tape(
        self, learner_seed: int, update: int, record: int, state_id: str,
        graph: str, action_index: int,
    ) -> tuple[DisturbanceHold, ...]:
        return disturbance_tape(
            learner_seed, "training-disturbance",
            (update, record, state_id, graph, action_index),
        )


__all__ = [
    "ACTIONS", "EVALUATION_DOMAIN", "GRAPHS", "HORIZON", "Host", "PRE_EVENT_Q",
    "SOURCE_STREAMS", "TARGET_TICKS",
]
