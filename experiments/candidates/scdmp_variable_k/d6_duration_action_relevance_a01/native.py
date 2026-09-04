"""Direct native boundary for the A01 TAU_LEAK=.92 host."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import struct
import subprocess
from typing import Callable

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
SOURCE_STREAMS = ((9011, 7), (9013, 13))
TARGET_TICKS = (64, 160, 256)
EVALUATION_DOMAIN = 9029


def compile_host(build_root: Path) -> ctypes.CDLL:
    """Build the card's host from the canonical source with its sole edit."""

    build_root.mkdir(parents=True, exist_ok=True)
    canonical = Path(abi.__file__).with_name("native") / "mf_rs_native.cpp"
    source = build_root / "d6_a01_native.cpp"
    source.write_text(
        canonical.read_text(encoding="utf-8").replace(
            "tau[i] - 0.88", "tau[i] - 0.92",
        ),
        encoding="utf-8",
    )
    compiler = abi._compiler_path()
    vcvars = abi._vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    obj = build_root / "d6_a01_native.obj"
    dll = build_root / "d6_a01_native.dll"
    command = (
        f'call "{vcvars}" >nul && "{compiler}" /nologo /std:c++20 /O2 /EHsc /LD /W4 '
        f'"{source}" /Fo:"{obj}" /Fe:"{dll}"'
    )
    completed = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=build_root,
        capture_output=True,
        text=True,
    )
    obj.unlink(missing_ok=True)
    if completed.returncode != 0:
        raise RuntimeError(f"native compilation failed: {completed.stdout}\n{completed.stderr}")
    return abi._configure(ctypes.CDLL(str(dll)))


class Host:
    def __init__(self, build_root: Path) -> None:
        self.library = compile_host(build_root)

    def __enter__(self) -> "Host":
        self._previous = abi.require_native_backend
        abi.require_native_backend = lambda: self.library
        return self

    def __exit__(self, *_args: object) -> None:
        abi.require_native_backend = self._previous
        handle, self.library._handle = self.library._handle, 0
        ctypes.windll.kernel32.FreeLibrary(ctypes.c_void_p(handle))

    @staticmethod
    def _duration_clone(payload: bytes, k: int) -> bytes:
        state = abi._state_from_bytes(payload)
        state.current_k = k
        state.cached.next_k = k
        state.cached.hold_k = 0
        state.cached.observation[16] = k / 13.0
        return abi._state_bytes(state)

    def source_population(
        self,
        *,
        streams: tuple[tuple[int, int], ...] = SOURCE_STREAMS,
        targets: tuple[int, ...] = TARGET_TICKS,
        deadline: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        states: list[dict[str, object]] = []
        transitions = 0
        renewals = 0
        trajectories = 0
        issues: list[str] = []
        for source_seed, source_k in streams:
            trajectories += 1
            session = abi.NativeSession.reset(
                width=1,
                k=source_k,
                pre_event_q=0,
                initial_v=0.015,
                initial_y=0.0,
                initial_phi=0.0,
            )
            reset = session.states()[0]
            if reset.latent_assignment != (1, 2, 3, 4) or reset.latent_q != 0:
                raise RuntimeError("native reset did not preserve literal p identity and q=0")
            target_index = 0
            renewal_index = 0
            while target_index < len(targets):
                output = session.outputs[0]
                if output.terminal:
                    issues.append(
                        f"source {source_seed} terminated before target {targets[target_index]}"
                    )
                    break
                if output.tick >= targets[target_index]:
                    source_bytes = session.state_bytes()[0]
                    twins = abi.NativeSession.from_state_bytes((source_bytes, source_bytes))
                    twin_outputs = twins.apply_orders(GRAPHS)
                    hr_public = struct.pack("<18d", *twin_outputs[0].observation)
                    rh_public = struct.pack("<18d", *twin_outputs[1].observation)
                    if hr_public != rh_public:
                        issues.append(
                            f"source {source_seed} target {targets[target_index]} "
                            "HR/RH public observations differ after LEVEL_RELEASE"
                        )
                    else:
                        states.append({
                            "state_id": f"source-{source_seed}-target-{targets[target_index]:03d}",
                            "source_seed": source_seed,
                            "source_k": source_k,
                            "target_tick": targets[target_index],
                            "boundary_tick": output.tick,
                            "hr_state": twins.state_bytes()[0],
                            "rh_state": twins.state_bytes()[1],
                        })
                    target_index += 1
                    continue
                row = disturbance_tape(
                    source_seed,
                    "source-disturbance",
                    (renewal_index,),
                    holds=1,
                )[0]
                output = session.step((0,), (row,))[0]
                transitions += output.ticks_advanced
                renewals += 1
                renewal_index += 1
                if deadline is not None and clock is not None and clock() >= deadline:
                    return states, {
                        "established": False,
                        "reason": "1,800 second cap crossed at a source-renewal boundary",
                        "cap_crossed": True,
                        "source_trajectories": trajectories,
                        "source_transitions": transitions,
                        "source_renewals": renewals,
                    }
        established = not issues and len(states) == len(streams) * len(targets)
        return states, {
            "established": established,
            "reason": None if established else "; ".join(issues),
            "cap_crossed": False,
            "source_trajectories": trajectories,
            "source_transitions": transitions,
            "source_renewals": renewals,
        }

    def materialize_evaluation_tapes(
        self,
        states: list[dict[str, object]],
        *,
        tape_count: int = 16,
        seed: int = EVALUATION_DOMAIN,
    ) -> dict[tuple[int, int], tuple[DisturbanceHold, ...]]:
        return {
            (state_index, tape_index): disturbance_tape(
                seed,
                "evaluation-disturbance",
                (states[state_index]["state_id"], tape_index),
            )
            for state_index in range(len(states))
            for tape_index in range(tape_count)
        }

    def mission(
        self,
        state: dict[str, object],
        graph: str,
        action: tuple[int, int],
        tape: tuple[DisturbanceHold, ...],
    ) -> dict[str, object]:
        key = "hr_state" if graph == "HR" else "rh_state"
        payload = self._duration_clone(state[key], action[1])
        session = abi.NativeSession.from_state_bytes((payload,))
        renewal = 0
        transitions = 0
        output = session.outputs[0]
        while not output.terminal:
            held_action = action[0] if renewal == 0 else 0
            output = session.step((held_action,), (tape[renewal],))[0]
            transitions += output.ticks_advanced
            renewal += 1
        y = HORIZON - output.dock_tick if output.safe_dock else 0
        return {
            "Y": y,
            "transitions": transitions,
            "safe_dock": int(output.safe_dock),
            "timeout": int(output.timeout),
            "failure": int(output.failure),
            "cable_overload": int(output.cable_overload),
            "gantry_contact": int(output.gantry_contact),
            "attitude_loss": int(output.attitude_loss),
            "formation_loss": int(output.formation_loss),
        }


__all__ = [
    "ACTIONS",
    "EVALUATION_DOMAIN",
    "GRAPHS",
    "HORIZON",
    "Host",
    "SOURCE_STREAMS",
    "TARGET_TICKS",
]
