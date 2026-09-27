"""B01 chain_bandit host, exact quantities and estimators (sequential_coordinator_credit)."""

from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.sequential_coordinator_credit.b01 import chain_bandit as cb
from experiments.candidates.sequential_coordinator_credit.b01 import estimators as est
from experiments.candidates.sequential_coordinator_credit.b01 import learner as ln
from experiments.candidates.sequential_coordinator_credit.b01 import readings as rd

I, RL, S1, S2 = cb.IDLE, cb.RELAY, cb.SERVE_1, cb.SERVE_2
D_HAND = np.array([0.6, 0.5])
Q_HAND = np.array([[0.3, 0.4], [0.5, 0.35], [0.45, 0.6], [0.4, 0.3]])


def _contexts(beta, s, sigma=0.0, d=None, q=None, n=4, seed=0):
    rng = np.random.default_rng(seed)
    config = cb.Configuration(beta, s, sigma)
    d = rng.uniform(0.3, 1.0, (n, cb.C)) if d is None else np.broadcast_to(d, (n, cb.C)).copy()
    q = rng.uniform(0.3, 1.0, (n, cb.K, cb.C)) if q is None else \
        np.broadcast_to(q, (n, cb.K, cb.C)).copy()
    return cb.Contexts(config=config, d=d, q=q, xi_eval=rng.standard_normal((n, 32, cb.C)),
                       mask=cb.capability_mask(s))


def _random_policy(mask, n, seed, scale=1.5):
    theta = np.random.default_rng(seed).normal(scale=scale, size=(n, cb.N_PREFIXES, cb.N_LABELS))
    return cb.masked_softmax(theta, cb.prefix_mask(mask)), theta


def _rtab(ctx):
    return cb.reward_table(ctx.eval_demands(), ctx.q, ctx.mask, ctx.b0)


def test_constants_grid_and_masks():
    assert cb.K == 4 and cb.N_JOINTS == 256 and cb.N_PREFIXES == 85 and cb.C == 2
    assert len(cb.CONFIGURATIONS) == 12
    assert cb.config_index(cb.BINDING_CORNER) == 9
    assert cb.CONFIGURATIONS[9].b0 == pytest.approx(0.1)
    with pytest.raises(ValueError):
        cb.config_index((0.7, 1, 0.2))
    m1, m2 = cb.capability_mask(1), cb.capability_mask(2)
    assert m1[:, I].all() and m2[:, I].all()
    assert [set(np.flatnonzero(row)) for row in m1] == [{I, RL}, {I, S1}, {I, S2}, {I, S1, S2}]
    assert [set(np.flatnonzero(row)) for row in m2] == [{I, RL, S1}, {I, RL, S2}, {I, S1, S2},
                                                        {I, S1, S2}]
    assert cb.joint_index([1, 2, 3, 0]) == 1 * 64 + 2 * 16 + 3 * 4
    assert (cb.JOINT_PREFIX[cb.joint_index([1, 2, 3, 0])] == [0, 1 + 1, 5 + 6, 21 + 27]).all()


@pytest.mark.parametrize("beta, s, z, expected", [
    # binding (b0 = .1): relay lifts both clusters to B; without relay both capped at .1
    (0.9, 1, (RL, S1, S2, S1), 0.6 + 0.5),
    (0.9, 1, (I, S1, S2, S1), 0.1 + 0.1),
    (0.9, 1, (I, S1, I, I), 0.1),
    # non-binding (b0 = B): demand/access only
    (0.0, 1, (I, S1, S2, S2), 0.5 + 0.5),
    (0.0, 1, (RL, S1, I, I), 0.5),
    (0.0, 1, (I, I, S2, I), 0.5),
    # masked labels count as IDLE: agent 0 cannot serve, agent 1 cannot relay (s = 1)
    (0.9, 1, (S1, RL, S2, I), 0.1),
    (0.0, 1, (S1, S1, I, I), 0.5),
    (0.9, 2, (S1, S2, I, I), 0.1 + 0.1),
])
def test_hand_computed_reward(beta, s, z, expected):
    mask = cb.capability_mask(s)
    b0 = (1 - beta) * cb.B_RELAYED
    assert cb.reward(D_HAND, Q_HAND, np.array(z), mask, b0) == pytest.approx(expected)
    table = cb.reward_table(D_HAND[None, None], Q_HAND[None], mask, b0)
    assert table[0, 0, cb.joint_index(z)] == pytest.approx(expected)


def test_reward_table_matches_pointwise_reward():
    ctx = _contexts(0.5, 2, 0.2)
    table = _rtab(ctx)
    d = ctx.eval_demands()
    pointwise = cb.reward(d[:, :, None, :], ctx.q[:, None, None], cb.JOINTS[None, None],
                          ctx.mask, ctx.b0)
    np.testing.assert_allclose(table, pointwise, rtol=0, atol=1e-15)


def test_noise_enters_inside_the_min():
    mask = cb.capability_mask(1)
    ctx = _contexts(0.9, 1, d=np.array([0.9, 0.9]), q=Q_HAND, n=1)
    xi = np.linspace(-3.0, 3.0, 41)[:, None] * np.ones((1, cb.C))
    d_noisy = cb.noisy_demands(ctx.d[:, None, :], xi[None], 0.2)
    base = cb.reward_table(ctx.d[:, None, :], ctx.q, mask, ctx.b0)[0, 0]
    noisy = cb.reward_table(d_noisy, ctx.q, mask, ctx.b0)[0]
    access = cb.access_table(ctx.q, mask)[0]                                  # (256, C)
    backhaul = cb.backhaul_table(mask, ctx.b0)
    cap = np.minimum(access, backhaul[:, None])
    not_binding = (cap <= d_noisy.min(axis=1)[0][None, :]).all(axis=1) & \
        (cap <= ctx.d[0][None, :]).all(axis=1)
    assert not_binding.sum() > 0 and (~not_binding).sum() > 0
    np.testing.assert_array_equal(noisy[:, not_binding], np.broadcast_to(base[not_binding],
                                                                           noisy[:, not_binding].shape))
    assert np.ptp(noisy[:, ~not_binding], axis=0).max() > 0
    # never additive team noise: sigma = 0 recovers R exactly
    assert np.array_equal(cb.noisy_demands(ctx.d, np.ones_like(ctx.d), 0.0), ctx.d)


def test_masked_softmax_and_joint_probabilities():
    ctx = _contexts(0.9, 1)
    P, _ = _random_policy(ctx.mask, ctx.n, 1)
    pmask = cb.prefix_mask(ctx.mask)
    assert (P[:, ~pmask] == 0).all()
    np.testing.assert_allclose(P.sum(-1), 1.0)
    pj = cb.joint_probs(P)
    np.testing.assert_allclose(pj.sum(-1), 1.0)
    masked = ~ctx.mask[np.arange(cb.K), cb.JOINTS].all(axis=1)
    assert (pj[:, masked] == 0).all()
    rng = np.random.default_rng(3)
    z = cb.sample_joints(P, 20000, rng)
    assert ctx.mask[np.arange(cb.K), z].all()
    freq = np.bincount(cb.joint_index(z[0]), minlength=256) / 20000
    assert np.abs(freq - pj[0]).max() < 0.02


def test_telescoping_prefix_values():
    """sum_i [Q(x, z_<=i) - Q(x, z_<i)] = R(x, z) - J(x) for a random policy (E3* sums)."""
    ctx = _contexts(0.9, 2, 0.2)
    P, _ = _random_policy(ctx.mask, ctx.n, 2)
    rtab = _rtab(ctx)
    jidx = est.all_joints(ctx.n, rtab.shape[1])
    A = est.seqau_exact(P, rtab, jidx)
    J = (cb.joint_probs(P)[:, None, :] * rtab).sum(-1)
    np.testing.assert_allclose(A.sum(-1), rtab - J[..., None], atol=1e-12)
    levels = cb.prefix_values(cb.suffix_products(P), rtab)
    np.testing.assert_allclose(levels[0][..., 0], J, atol=1e-12)
    np.testing.assert_array_equal(levels[cb.K], rtab)


def test_shapley_efficiency_and_removal():
    ctx = _contexts(0.5, 2, 0.2)
    rtab = _rtab(ctx)
    jidx = est.all_joints(ctx.n, rtab.shape[1])
    assert (rtab[..., 0] == 0).all()                                          # R(all IDLE) = 0
    phi = est.shapley_values(rtab, jidx)
    np.testing.assert_allclose(phi.sum(-1), rtab, atol=1e-12)
    D = est.removal_difference(rtab, jidx)
    idle = cb.JOINTS == cb.IDLE
    assert (D[..., idle] == 0).all() and (phi[..., idle] == 0).all()


def test_suffix_shapley_sums_to_e4_minus_e4_star():
    ctx = _contexts(0.9, 2, 0.2)
    P, _ = _random_policy(ctx.mask, ctx.n, 4)
    rtab = _rtab(ctx)
    jidx = est.all_joints(ctx.n, rtab.shape[1])
    attribution = est.suffix_shapley(P, rtab, jidx)
    gap = est.removal_difference(rtab, jidx) - est.removal_resampled(P, rtab, jidx)
    np.testing.assert_allclose(attribution.sum(-1), gap, atol=1e-12)
    assert (attribution[..., np.tril_indices(cb.K)[0], np.tril_indices(cb.K)[1]] == 0).all()


def test_e4_equals_e4_star_under_deterministic_downstream():
    ctx = _contexts(0.9, 2, 0.2)
    P, _ = _random_policy(ctx.mask, ctx.n, 5)
    fixed = {1: cb.SERVE_2, 2: cb.SERVE_1, 3: cb.SERVE_2}
    for agent, label in fixed.items():
        rows = cb.PREFIX_AGENT == agent
        P[:, rows] = 0.0
        P[:, rows, label] = 1.0
    rtab = _rtab(ctx)
    jidx = est.all_joints(ctx.n, rtab.shape[1])
    support = cb.joint_probs(P) > 0
    e4 = est.removal_difference(rtab, jidx)
    e4s = est.removal_resampled(P, rtab, jidx)
    diff = np.abs(e4 - e4s).max(axis=(1, 3))                                  # (n, 256)
    assert support.sum() > 0 and diff[support].max() < 1e-12


def test_e3_converges_to_e3_star_on_an_additive_configuration():
    """beta = 0, sigma = 0, d = 1 and q <= .5 with s = 1: no min binds, R is additive."""
    rng = np.random.default_rng(6)
    q = rng.uniform(0.3, 0.5, (2, cb.K, cb.C))
    ctx = _contexts(0.0, 1, 0.0, d=np.array([1.0, 1.0]), q=q, n=2)
    P, _ = _random_policy(ctx.mask, ctx.n, 7, scale=0.7)

    def error(M, L, seed):
        stream = np.random.default_rng(seed)
        z = cb.sample_joints(P, M, stream)
        R = cb.reward(ctx.d[:, None], ctx.q[:, None], z, ctx.mask, ctx.b0)
        rtab = cb.reward_table(ctx.d[:, None], ctx.q, ctx.mask, ctx.b0)
        exact = est.seqau_exact(P, rtab, cb.joint_index(z)[:, None, :])[:, 0]
        estimate = est.seqau_ridge(P, z, R, stream, n_continuations=L)
        return np.abs(estimate - exact).mean()

    small, large = error(64, 8, 8), error(1024, 128, 9)
    assert large < 0.015 and large < 0.3 * small
    # without continuation noise (deterministic downstream) only the ridge fit remains
    for agent, label in {1: cb.SERVE_1, 2: cb.SERVE_2, 3: cb.SERVE_2}.items():
        rows = cb.PREFIX_AGENT == agent
        P[:, rows] = 0.0
        P[:, rows, label] = 1.0
    assert error(4096, 8, 10) < 1e-3


def test_blas_free_solver_matches_lapack():
    rng = np.random.default_rng(14)
    X = rng.normal(size=(5, 40, 17))
    lhs = np.einsum("nmf,nmg->nfg", X, X) + 0.01 * np.eye(17)
    rhs = rng.normal(size=(5, 17))
    np.testing.assert_allclose(est.solve_spd(lhs, rhs),
                               np.linalg.solve(lhs, rhs[..., None])[..., 0], rtol=1e-10)


def test_exact_gradient_matches_finite_differences():
    ctx = _contexts(0.9, 2, 0.2)
    _, theta = _random_policy(ctx.mask, ctx.n, 10, scale=1.0)
    pmask = cb.prefix_mask(ctx.mask)
    r_bar = cb.mean_reward_table(ctx)
    grad = cb.exact_grad_J(cb.masked_softmax(theta, pmask), r_bar)
    rng = np.random.default_rng(11)
    allowed = np.argwhere(np.broadcast_to(pmask, theta.shape))
    for x, row, label in allowed[rng.choice(len(allowed), 40, replace=False)]:
        h = 1e-6
        plus, minus = theta.copy(), theta.copy()
        plus[x, row, label] += h
        minus[x, row, label] -= h
        fd = (cb.exact_J(cb.masked_softmax(plus, pmask), r_bar)
              - cb.exact_J(cb.masked_softmax(minus, pmask), r_bar)) / (2 * h)
        assert grad[x, row, label] == pytest.approx(fd, abs=1e-8)
    assert (grad[:, ~pmask] == 0).all()


def test_exact_readings_are_unbiased_for_the_exact_seqau_and_shared_return():
    ctx = _contexts(0.9, 1, 0.2)
    _, theta = _random_policy(ctx.mask, ctx.n, 12, scale=1.0)
    out = rd.snapshot_readings(theta, ctx, np.random.default_rng(13), e3_draws=4)
    for arm in ("E1", "E3*", "E4*"):
        assert out["arms"][arm]["raw"]["cosine"] == pytest.approx(1.0, abs=1e-9)
        assert out["arms"][arm]["raw"]["projection"] == pytest.approx(1.0, abs=1e-9)
        assert out["arms"][arm]["native"]["cosine"] == pytest.approx(1.0, abs=1e-9)
    for arm in est.ARMS:
        for which in rd.CALIBRATIONS:
            assert out["arms"][arm][which]["variance"] >= -1e-12
    assert out["arms"]["E3"]["raw"]["draws"] == 4 and "cosine_se" in out["arms"]["E3"]["raw"]
    assert out["shapley"]["shapley_efficiency_max_abs_error"] < 1e-12


def test_random_streams_do_not_collide():
    """SeedSequence zero-pads short keys; seeds start at 1 so no policy key equals a context key."""
    from experiments.candidates.sequential_coordinator_credit.b01.first_cell import SEED_BASE

    first = {}
    seeds = range(SEED_BASE, SEED_BASE + 6)
    for ci in (9, 11):
        for seed in seeds:
            first[("ctx", ci, seed)] = cb.context_stream(ci, seed).random()
            for arm in range(5):
                for ent in range(2):
                    first[("pol", ci, arm, ent, seed)] = ln.policy_stream(ci, arm, ent,
                                                                          seed).random()
            for snap in rd.READING_SNAPSHOTS:
                first[("read", ci, seed, snap)] = rd.reading_stream(ci, 0, seed, snap).random()
    assert len(set(first.values())) == len(first)
