from __future__ import annotations

import numpy as np

def dense_actor_input_reference(
    encoded: np.ndarray, receiver_roles: np.ndarray, center: np.ndarray,
    residuals: np.ndarray, scale: float, sender_roles: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fixed-small deterministic audit only; this is never a deployed forward path."""
    n, width = encoded.shape
    sender_roles = receiver_roles if sender_roles is None else sender_roles
    if (
        n not in (6, 8, 12, 16) or width != 33
        or receiver_roles.shape != (n,) or sender_roles.shape != (n,)
    ):
        raise ValueError("dense audit reference accepts only registered fixed-small fixtures")
    omega = np.asarray(center, dtype=np.float64) * np.exp(scale * np.tanh(residuals))
    dense_weights = np.empty((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            dense_weights[i, j] = omega[int(receiver_roles[i]), int(sender_roles[j])]
    d = dense_weights.sum(axis=1) / float(n)
    m = dense_weights @ encoded / float(n)
    z = m / (d[:, None] + 1e-12)
    return d, m, z


def implicit_actor_input_reference(
    encoded: np.ndarray, receiver_roles: np.ndarray, center: np.ndarray,
    residuals: np.ndarray, scale: float, sender_roles: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = int(encoded.shape[0])
    sender_roles = receiver_roles if sender_roles is None else sender_roles
    omega = np.asarray(center, dtype=np.float64) * np.exp(scale * np.tanh(residuals))
    block_sums = np.stack([
        encoded[sender_roles == sender].sum(axis=0) / float(n) for sender in (0, 1)
    ])
    block_mass = np.asarray([
        (sender_roles == sender).sum() / float(n) for sender in (0, 1)
    ])
    d_by_role = omega @ block_mass
    m_by_role = omega @ block_sums
    z_by_role = m_by_role / (d_by_role[:, None] + 1e-12)
    return (
        d_by_role[receiver_roles], m_by_role[receiver_roles], z_by_role[receiver_roles],
    )
