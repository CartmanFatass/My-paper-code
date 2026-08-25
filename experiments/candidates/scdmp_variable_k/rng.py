from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from .config import NUMPY_VERSION

TWO_NEG_53 = np.float64(2.0 ** -53)
TWO_64 = 1 << 64
PI64 = np.float64(float.fromhex("0x1.921fb54442d18p+1"))


def require_numpy_version() -> None:
    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(f"SCDMP requires NumPy {NUMPY_VERSION}, found {np.__version__}")


def raw_word(bit_generator: np.random.PCG64) -> int:
    return int(bit_generator.random_raw())


def u0(raw: int) -> np.float64:
    return np.float64(raw >> 11) * TWO_NEG_53


def umid(raw: int) -> np.float64:
    return (np.float64(raw >> 11) + np.float64(0.5)) * TWO_NEG_53


def box_muller_pair(bit_generator: np.random.PCG64) -> tuple[np.float64, np.float64]:
    x = raw_word(bit_generator)
    y = raw_word(bit_generator)
    radius = np.sqrt(np.float64(-2.0) * np.log(umid(x)))
    angle = np.float64(2.0) * PI64 * umid(y)
    return radius * np.cos(angle), radius * np.sin(angle)


def xavier_array(
    bit_generator: np.random.PCG64, rows: int, columns: int,
) -> np.ndarray:
    bound = (np.float64(5.0) / np.float64(3.0)) * np.sqrt(
        np.float64(6.0) / np.float64(columns + rows)
    )
    out = np.empty((rows, columns), dtype=np.float64)
    for row in range(rows):
        for column in range(columns):
            uniform = u0(raw_word(bit_generator))
            out[row, column] = -bound + np.float64(2.0) * bound * uniform
    return out.astype(np.float32)


def orthogonal_gate(bit_generator: np.random.PCG64, width: int = 32) -> np.ndarray:
    matrix = np.empty((width, width), dtype=np.float64)
    flat = matrix.reshape(-1)
    for offset in range(0, flat.size, 2):
        z0, z1 = box_muller_pair(bit_generator)
        flat[offset] = z0
        flat[offset + 1] = z1
    q_matrix, r_matrix = np.linalg.qr(matrix, mode="reduced")
    signs = np.asarray(
        [np.float64(1.0) if r_matrix[j, j] >= 0.0 else np.float64(-1.0) for j in range(width)],
        dtype=np.float64,
    )
    return (q_matrix * signs[None, :]).astype(np.float32)


def fisher_yates(bit_generator: np.random.PCG64, values: Iterable[int]) -> list[int]:
    result = list(values)
    for j in range(len(result) - 1, 0, -1):
        modulus = j + 1
        rejection_limit = TWO_64 - (TWO_64 % modulus)
        raw = raw_word(bit_generator)
        while raw >= rejection_limit:
            raw = raw_word(bit_generator)
        h = raw % modulus
        result[j], result[h] = result[h], result[j]
    return result
