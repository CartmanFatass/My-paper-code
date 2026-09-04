"""Small counter-addressed RNG used by every arm and evaluator."""

from __future__ import annotations

MASK64 = (1 << 64) - 1


def _mix64(value: int) -> int:
    value = (value + 0x9E3779B97F4A7C15) & MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
    return (value ^ (value >> 31)) & MASK64


def counter_u64(seed: int, namespace: int, *coordinates: int) -> int:
    """Map an integer coordinate tuple to one stable unsigned 64-bit value."""

    value = _mix64(seed & MASK64) ^ _mix64(namespace & MASK64)
    for ordinal, coordinate in enumerate(coordinates):
        value = _mix64(value ^ _mix64((coordinate + ordinal * 0x9E3779B9) & MASK64))
    return value


def uniform01(seed: int, namespace: int, *coordinates: int) -> float:
    return ((counter_u64(seed, namespace, *coordinates) >> 11) + 0.5) / float(1 << 53)


def categorical(seed: int, namespace: int, size: int, *coordinates: int) -> int:
    return min(int(uniform01(seed, namespace, *coordinates) * size), size - 1)


def counter_permutation(seed: int, namespace: int, size: int) -> list[int]:
    return sorted(range(size), key=lambda index: (counter_u64(seed, namespace, index), index))


def cyclic_minibatches(
    seed: int,
    namespace: int,
    row_count: int,
    updates: int,
    batch_size: int,
) -> list[list[int]]:
    permutation = counter_permutation(seed, namespace, row_count)
    return [
        [permutation[(update * batch_size + offset) % row_count] for offset in range(batch_size)]
        for update in range(updates)
    ]
