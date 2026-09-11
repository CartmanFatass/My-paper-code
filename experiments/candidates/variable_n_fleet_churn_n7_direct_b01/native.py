"""Linux loading adapter; all environment/controller computation remains R09."""

import ctypes as ct
import os
from pathlib import Path
import subprocess

from ..variable_n_fleet_churn_bpcr_r09 import native_backend as original


def build(out):
    candidates = Path(__file__).resolve().parents[1]
    source = candidates / "variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp"
    include = candidates / "variable_n_fleet_churn_headroom/native"
    binary = out / "b01_native.so"
    subprocess.run([os.environ.get("CXX", "c++"), "-std=c++20", "-O2", "-fPIC", "-shared",
                    "-fno-fast-math", "-ffp-contract=off", f"-I{include}",
                    str(source), "-o", str(binary)], check=True)
    library = ct.CDLL(str(binary))
    handle = ct.POINTER(ct.c_void_p)
    signatures = {
        "reset": [ct.POINTER(original._EpisodeInput), ct.c_int32, handle, ct.POINTER(original._InteractiveOutput)],
        "step": [handle, ct.POINTER(ct.c_int32), ct.c_int32, ct.POINTER(original._InteractiveOutput)],
        "bcrh": [handle, ct.c_int32, ct.POINTER(original._BCRHOutput)],
        "close": [handle, ct.c_int32],
    }
    for operation, arguments in signatures.items():
        function = getattr(library, f"vnfc_bpcr_r09_interactive_{operation}_batch")
        function.argtypes, function.restype = arguments, ct.c_int32
    return library


class Batch(original.NativeInteractiveBatch):
    """Inject only the selected Linux library into the unchanged step/BCRH API."""

    def __init__(self, library, fixtures):
        self._width, self._library = len(fixtures), library
        inputs = (original._EpisodeInput * self._width)(*(original._episode_input(x) for x in fixtures))
        self._handles = (ct.c_void_p * self._width)()
        outputs = (original._InteractiveOutput * self._width)()
        status = library.vnfc_bpcr_r09_interactive_reset_batch(inputs, self._width, self._handles, outputs)
        if status:
            raise RuntimeError(f"N7 native reset status {status}")
        self._open = True
        self.initial = tuple(original._interactive_dict(item) for item in outputs)
