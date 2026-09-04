"""A02-local native host with one scheduled-event composite hold export."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import subprocess
from typing import Callable

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    native_backend as abi,
)

from .rng import PrimitiveTape, materialize_tape


A02_ROOT_SEED = 9173
SOURCE_DOMAINS = (("SCDMP-D6-A02/SOURCE/K7", 7), ("SCDMP-D6-A02/SOURCE/K13", 13))
SOURCE_TICKS = (91, 182, 273)
EVALUATION_DOMAIN = "SCDMP-D6-A02/EVALUATION"
COUNTDOWNS = (7, 78)
CLOCKS = (7, 13)
GRAPHS = ("HR", "RH")
HORIZON = 364
ORDER_ACTION = {"HR": 10, "RH": 12}


_COMPOSITE_EXPORT = r'''

// A02-local scheduled-event hold.  It preserves primitive(), the existing
// mf_rs_apply_order_batch event/LEVEL_RELEASE path, and snapshot().
MF_EXPORT std::int32_t mf_rs_step_event_batch(
        NativeStateV1* states, const StepInput* inputs,
        const std::int32_t* event_offsets, const std::int32_t* orders,
        std::int32_t width, HostOutput* outputs, std::int32_t* event_applied) {
    if (!states || !inputs || !event_offsets || !orders || !outputs || !event_applied
        || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) {
        event_applied[i] = 0;
        if (!valid_state(states[i]) || !valid_step(inputs[i]) || inputs[i].active != 1
            || !states[i].enabled || states[i].terminal || states[i].event_phase != 0
            || event_offsets[i] < 1 || event_offsets[i] > states[i].current_k
            || (orders[i] != kOrderHR && orders[i] != kOrderRH)) return 2;
    }
    for (std::int32_t i = 0; i < width; ++i) {
        auto& state = states[i];
        const auto held_k = state.current_k;
        const auto planned = std::min(held_k, kHorizon - state.n);
        std::array<double, kMaxHold> rewards{};
        std::int32_t advanced = 0;
        for (std::int32_t tick = 0; tick < planned; ++tick) {
            rewards[advanced] = primitive(state, inputs[i].action, inputs[i].eta_v[tick],
                                          inputs[i].eta_y[tick], inputs[i].eta_omega[tick]);
            ++advanced;
            if (state.terminal) break;
            if (advanced == event_offsets[i]) {
                state.cached = snapshot(state, advanced, held_k, rewards.data());
                HostOutput event_output{};
                const auto status = mf_rs_apply_order_batch(
                    &state, &orders[i], 1, &event_output);
                if (status != 0) return 3;
                event_applied[i] = 1;
            }
        }
        state.cached = snapshot(state, advanced, held_k, rewards.data());
        outputs[i] = state.cached;
    }
    return 0;
}
'''


def compile_host(build_root: Path) -> ctypes.CDLL:
    build_root.mkdir(parents=True, exist_ok=True)
    canonical = Path(abi.__file__).with_name("native") / "mf_rs_native.cpp"
    source = build_root / "d6_a02_native.cpp"
    derived = canonical.read_text(encoding="utf-8").replace(
        "tau[i] - 0.88", "tau[i] - 0.92",
    ) + _COMPOSITE_EXPORT
    source.write_text(derived, encoding="utf-8")
    compiler = abi._compiler_path()
    vcvars = abi._vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    obj = build_root / "d6_a02_native.obj"
    dll = build_root / "d6_a02_native.dll"
    command = (
        f'call "{vcvars}" >nul && "{compiler}" /nologo /std:c++20 /O2 /EHsc /LD /W4 '
        f'"{source}" /Fo:"{obj}" /Fe:"{dll}"'
    )
    completed = subprocess.run(
        command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=build_root, capture_output=True, text=True,
    )
    obj.unlink(missing_ok=True)
    if completed.returncode != 0:
        raise RuntimeError(f"native compilation failed: {completed.stdout}\n{completed.stderr}")
    library = abi._configure(ctypes.CDLL(str(dll)))
    library.mf_rs_step_event_batch.argtypes = [
        ctypes.POINTER(abi._NativeState), ctypes.POINTER(abi._StepInput),
        ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
        ctypes.POINTER(abi._HostOutput), ctypes.POINTER(ctypes.c_int32),
    ]
    library.mf_rs_step_event_batch.restype = ctypes.c_int32
    return library


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
    def _clock_clone(payload: bytes, clock_k: int) -> bytes:
        state = abi._state_from_bytes(payload)
        state.current_k = clock_k
        state.cached.next_k = clock_k
        state.cached.hold_k = 0
        state.cached.observation[16] = clock_k / 13.0
        return abi._state_bytes(state)

    def _event_step(
        self,
        session: abi.NativeSession,
        *,
        action: int,
        row: object,
        event_offset: int,
        graph: str,
    ) -> tuple[object, bool]:
        step = (abi._StepInput * 1)(abi._step_input(action, row, True))
        offsets = (ctypes.c_int32 * 1)(event_offset)
        orders = (ctypes.c_int32 * 1)(1 if graph == "HR" else 2)
        outputs = (abi._HostOutput * 1)()
        applied = (ctypes.c_int32 * 1)()
        status = int(self.library.mf_rs_step_event_batch(
            session._states, step, offsets, orders, 1, outputs, applied,
        ))
        if status != 0:
            raise RuntimeError(f"A02 composite event hold failed with status {status}")
        session._outputs = (abi._host_output(outputs[0]),)
        return session.outputs[0], bool(applied[0])

    def source_population(
        self,
        *,
        seed: int = A02_ROOT_SEED,
        domains: tuple[tuple[str, int], ...] = SOURCE_DOMAINS,
        targets: tuple[int, ...] = SOURCE_TICKS,
        deadline: float | None = None,
        clock: Callable[[], float] | None = None,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        states: list[dict[str, object]] = []
        transitions = renewals = trajectories = 0
        issues: list[str] = []
        try:
            for domain, source_k in domains:
                tape = materialize_tape(seed, domain, ())
                session = abi.NativeSession.reset(
                    width=1, k=source_k, pre_event_q=0,
                    initial_v=0.015, initial_y=0.0, initial_phi=0.0,
                )
                trajectories += 1
                target_index = 0
                while target_index < len(targets):
                    if deadline is not None and clock is not None and clock() >= deadline:
                        return states, {
                            "established": False,
                            "reason": "1,800 second cap crossed at a source-renewal boundary",
                            "cap_crossed": True,
                            "execution_error": False,
                            "source_trajectories": trajectories,
                            "source_renewals": renewals,
                            "source_transitions": transitions,
                        }
                    output = session.outputs[0]
                    target = targets[target_index]
                    if output.terminal:
                        issues.append(f"{domain} terminated before exact renewal {target}")
                        break
                    if output.tick == target:
                        state = session.states()[0]
                        states.append({
                            "base_state": f"{domain.rsplit('/', 1)[-1]}-tick-{target:03d}",
                            "source_domain": domain,
                            "source_k": source_k,
                            "tick": target,
                            "state_bytes": state.state_bytes,
                            "public_observation": list(state.output.observation),
                        })
                        target_index += 1
                        continue
                    if output.tick > target:
                        issues.append(f"{domain} skipped exact renewal {target}")
                        break
                    output = session.step((0,), (tape.hold(output.tick),))[0]
                    transitions += output.ticks_advanced
                    renewals += 1
        except Exception as error:
            return states, {
                "established": False,
                "reason": f"source execution failed: {error}",
                "cap_crossed": False,
                "execution_error": True,
                "source_trajectories": trajectories,
                "source_renewals": renewals,
                "source_transitions": transitions,
            }
        established = not issues and len(states) == len(domains) * len(targets)
        return states, {
            "established": established,
            "reason": None if established else "; ".join(issues),
            "cap_crossed": False,
            "execution_error": False,
            "source_trajectories": trajectories,
            "source_renewals": renewals,
            "source_transitions": transitions,
        }

    @staticmethod
    def materialize_evaluation_tapes(
        states: list[dict[str, object]],
        *,
        seed: int = A02_ROOT_SEED,
        domain: str = EVALUATION_DOMAIN,
        tape_count: int = 16,
    ) -> dict[tuple[int, int], PrimitiveTape]:
        return {
            (state_index, tape_index): materialize_tape(
                seed, domain, (state["base_state"], tape_index),
            )
            for state_index, state in enumerate(states)
            for tape_index in range(tape_count)
        }

    def mission(
        self,
        state: dict[str, object],
        *,
        countdown: int,
        clock_k: int,
        graph: str,
        tape: PrimitiveTape,
    ) -> dict[str, object]:
        payload = self._clock_clone(state["state_bytes"], clock_k)
        session = abi.NativeSession.from_state_bytes((payload,))
        event_tick = int(state["tick"]) + countdown
        event_applied = False
        first_matched_tick: int | None = None
        transitions = renewals = 0
        output = session.outputs[0]
        while not output.terminal:
            start_tick = output.tick
            action = 0
            if event_applied:
                action = ORDER_ACTION[graph]
                if first_matched_tick is None:
                    first_matched_tick = start_tick
            row = tape.hold(start_tick)
            if not event_applied and start_tick < event_tick <= start_tick + clock_k:
                output, applied = self._event_step(
                    session, action=action, row=row,
                    event_offset=event_tick - start_tick, graph=graph,
                )
                event_applied = event_applied or applied
            else:
                output = session.step((action,), (row,))[0]
            transitions += output.ticks_advanced
            renewals += 1
        visible = session.states()[0]
        y = HORIZON - output.dock_tick if output.safe_dock else 0
        return {
            "Y": y,
            "transitions": transitions,
            "renewals": renewals,
            "event_tick": event_tick,
            "event_applied": event_applied,
            "visible_order": visible.event_order,
            "latency": None if first_matched_tick is None else first_matched_tick - event_tick,
            "safe_dock": int(output.safe_dock),
            "timeout": int(output.timeout),
            "failure": int(output.failure),
            "cable_overload": int(output.cable_overload),
            "gantry_contact": int(output.gantry_contact),
            "attitude_loss": int(output.attitude_loss),
            "formation_loss": int(output.formation_loss),
        }


__all__ = [
    "A02_ROOT_SEED", "CLOCKS", "COUNTDOWNS", "EVALUATION_DOMAIN", "GRAPHS",
    "HORIZON", "Host", "ORDER_ACTION", "SOURCE_DOMAINS", "SOURCE_TICKS",
]
