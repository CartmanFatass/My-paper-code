"""Two directly selected libraries; each native state retains its own explicit handle."""

import ctypes
import hashlib

import numpy as np

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_backend as backend

HOSTS = ("LITERAL", "GROUND-TERMINAL-LINEAR-CLEARANCE-A03")


def load_host(host):
    if host == HOSTS[0]:
        return backend.require_cpp_batched_production_backend()
    if host != HOSTS[1]:
        raise ValueError(host)
    key, source = backend._build_material()
    variant = b"#define DISH_GROUND_ENDPOINT_A03 1\n" + source
    key = hashlib.sha256(key.encode("ascii") + variant).hexdigest()
    return backend._configure(ctypes.CDLL(str(backend._compile(key, variant))))


class PointBatch:
    """The three width-one operations needed by this paired ordinary episode."""

    def __init__(self, library, row):
        self.library = library
        self.width = 1
        self.states = (backend._State * 1)()
        self.outputs = (backend._StepOutput * 1)()
        names = [name for name, _ in backend._ResetInput._fields_ if name != "master"]
        reset = backend._ResetInput(**{name: row[name] for name in names},
                                   master=(ctypes.c_uint8 * 32).from_buffer_copy(bytes.fromhex(row["master"])))
        code = library.dish_rbhr_r06_prod_reset_batch(ctypes.byref(reset), 1, self.states, self.outputs)
        if code:
            raise RuntimeError(f"A03 native reset failed: {code}")

    def state_copy(self):
        return backend._State.from_buffer_copy(bytes(self.states))

    def prepare_b01_tick(self):
        values = (backend._B01PreparedTick * 1)()
        code = self.library.dish_rbhr_r06_prod_b01_prepare_batch(self.states, 1, values)
        if code:
            raise RuntimeError(f"A03 native preparation failed: {code}")
        return backend.B01PreparedBatch(values, 1)

    def complete_b01_tick(self, prepared, rows):
        values = np.ascontiguousarray(rows, dtype=np.dtype(backend._StepInput))
        code = self.library.dish_rbhr_r06_prod_b01_complete_batch(
            prepared._values, values.ctypes.data_as(ctypes.POINTER(backend._StepInput)),
            1, self.states, self.outputs,
        )
        if code:
            raise RuntimeError(f"A03 native completion failed: {code}")
        return backend._decode_step_outputs(self.outputs, 1)
