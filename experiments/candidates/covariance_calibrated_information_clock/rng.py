"""Counter-addressed Philox4x32-10 required by revision 06."""

from __future__ import annotations

from statistics import NormalDist

MASK32 = 0xFFFFFFFF
M0 = 0xD2511F53
M1 = 0xCD9E8D57
W0 = 0x9E3779B9
W1 = 0xBB67AE85
NORMAL = NormalDist()


def _mulhilo(a: int, b: int) -> tuple[int, int]:
    product = (a & MASK32) * (b & MASK32)
    return (product >> 32) & MASK32, product & MASK32


def philox4x32_10(seed: int, phase: int, stream: int, item: int, address: int) -> tuple[int, int, int, int]:
    """Return all four words; revision 06 ordinarily consumes lane zero."""
    c0, c1, c2, c3 = phase & MASK32, stream & MASK32, item & MASK32, address & MASK32
    k0, k1 = seed & MASK32, (seed >> 32) & MASK32
    for round_index in range(10):
        hi0, lo0 = _mulhilo(M0, c0)
        hi1, lo1 = _mulhilo(M1, c2)
        c0, c1, c2, c3 = (hi1 ^ c1 ^ k0) & MASK32, lo1, (hi0 ^ c3 ^ k1) & MASK32, lo0
        if round_index != 9:
            k0 = (k0 + W0) & MASK32
            k1 = (k1 + W1) & MASK32
    return c0, c1, c2, c3


def uniform(seed: int, phase: int, stream: int, item: int, address: int, lane: int = 0) -> float:
    word = philox4x32_10(seed, phase, stream, item, address)[lane]
    return (word + 0.5) / 4294967296.0


def standard_normal(seed: int, phase: int, stream: int, item: int, address: int, lane: int = 0) -> float:
    return NORMAL.inv_cdf(uniform(seed, phase, stream, item, address, lane))
