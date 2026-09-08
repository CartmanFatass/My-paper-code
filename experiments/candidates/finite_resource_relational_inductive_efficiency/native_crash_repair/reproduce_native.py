"""Non-learning, fixed-input allocation-boundary check of a retained native ABI."""

import ctypes as c
import json
import sys

from ..native import native_abi as abi


def guarded(element, count):
    class Buffer(c.Structure):
        _pack_ = 1
        _fields_ = [("before", c.c_ubyte * 64), ("rows", element * count),
                    ("after", c.c_ubyte * 64)]
    value = Buffer()
    value.before[:] = value.after[:] = [0xA5] * 64
    return value


def main():
    library = abi.bind_native_abi(c.CDLL(sys.argv[1]), native_width=32).library
    buffers = [guarded(kind, 32) for kind in
               (abi.NativeStateV1, abi.ResetInputV1, abi.ObservationOutputV1,
                abi.StepInputV1, abi.StepOutputV1)]
    states, resets, observations, actions, outputs = [b.rows for b in buffers]
    snapshot = guarded(c.c_ubyte, abi.STATE_SIZE * 32)
    buffers.append(snapshot)
    calls = 0

    def call(function, *args):
        nonlocal calls
        assert function(*args, 32, 32) == 0
        calls += 1
        for buffer in buffers:
            assert bytes(buffer.before) == bytes([0xA5]) * 64
            assert bytes(buffer.after) == bytes([0xA5]) * 64

    for roster in (6, 9, 15, 21):
        for row in resets:
            row.abi_version, row.state_version, row.roster = 2, 1, roster
            for basin in range(2):
                row.event_times[basin][:] = (basin, basin + 3, basin + 6)
        for repeat in range(8):
            call(library.frrie_reset_batch_v1, states, resets)
            for slot in range(12):
                call(library.frrie_observe_batch_v1, states, observations)
                call(library.frrie_snapshot_batch_v1, states, snapshot.rows,
                     abi.STATE_SIZE * 32)
                original = bytes(states)
                call(library.frrie_restore_batch_v1, states, snapshot.rows,
                     abi.STATE_SIZE * 32)
                assert bytes(states) == original
                for lane, row in enumerate(actions):
                    row.abi_version = 2
                    for agent in range(roster):
                        role = agent // (roster // 3)
                        legal = ((0, 1, 5), (0, 1, 5), (2, 3, 4, 5))[role]
                        row.actions[agent] = legal[(slot + lane + agent + repeat) % len(legal)]
                call(library.frrie_step_batch_v1, states, actions, outputs)
            assert all(row.slot == 12 and row.terminal for row in states)
    print(json.dumps({"native_calls": calls, "fixed_input_transitions": 12288,
                      "guard_bytes_unchanged": True, "learning_steps": 0,
                      "snapshot_restores_equal": True}), flush=True)


if __name__ == "__main__":
    main()
