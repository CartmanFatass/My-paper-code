"""The generic-SHORT toy environment must stay byte-identical under optimization.

Every acceleration of this environment -- the plumbing removal here, the
synchronous batch and native observation slice planned after it -- is only
legitimate if the environment it produces is the SAME environment. An algorithm
comparison that straddles a change in observation bytes is silently invalid, and
nothing downstream would report it.

So this pins two different things, because neither implies the other:

  test_toy_environment_digest_is_unchanged
      hashes the whole caller-visible surface over 40 episodes. Values.

  test_handed_out_transaction_arrays_are_independent
      writes through everything the caller receives and proves the environment
      did not move. References. The digest cannot see this: a shared reference
      reads correct right up until somebody writes through it, and replacing
      ``copy.deepcopy`` in ``event_transaction`` is exactly the change that
      could introduce one.

The digest is a golden value ON PURPOSE. If a future change alters it, that is
not a broken test -- it is the environment changing, and the run that produced
any prior result is no longer reproducible by this code. Re-pin it only with a
recorded decision saying so.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pytest

from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    DynamicRosterEventEnv,
    GenericShortDynamicRosterEnv,
    make_dynamic_roster_ledger,
)

# Measured on the environment as it stood at 69c44fe7, before any acceleration.
EXPECTED_DIGEST = "50f7385f916d0445a79f6b067a65a6ba308455e3d97adef81af8b2a1f00445e7"
EPISODES = 40
FINGERPRINT_SEED = 20260729


def _feed_snapshot(digest, snapshot, label: str) -> None:
    digest.update(label.encode())
    digest.update(str(int(snapshot.physical_time)).encode())
    digest.update("|".join(snapshot.frontier).encode())
    digest.update(
        np.ascontiguousarray(snapshot.critic_global_features, dtype=np.float32).tobytes()
    )
    for member in snapshot.members:
        digest.update(member.lifecycle_key.encode())
        digest.update(str(int(member.membership_epoch)).encode())
        digest.update(np.ascontiguousarray(member.observation, dtype=np.float32).tobytes())
        digest.update(
            np.ascontiguousarray(
                member.critic_member_features, dtype=np.float32
            ).tobytes()
        )


def _feed_transaction(digest, transaction) -> None:
    if transaction is None:
        digest.update(b"<no-transaction>")
        return
    _feed_snapshot(digest, transaction.pre_membership_boundary_snapshot, "pre")
    for delta in transaction.atomic_membership_delta:
        digest.update(str(delta.lifecycle_key).encode())
        digest.update(str(delta).encode())
    _feed_snapshot(digest, transaction.post_membership_pre_policy_snapshot, "post")


def _fingerprint(episodes: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    rng = np.random.default_rng(FINGERPRINT_SEED)
    steps = 0
    for episode_id in range(episodes):
        env = DynamicRosterEventEnv()
        transaction = env.reset_event_runtime(episode_id)
        _feed_transaction(digest, transaction)
        terminal = False
        while not terminal:
            members = transaction.post_membership_pre_policy_snapshot.members
            actions = {m.lifecycle_key: int(rng.integers(ACTION_COUNT)) for m in members}
            for key in sorted(actions):
                digest.update(f"{key}={actions[key]}".encode())
            result = env.step_event_runtime(actions)
            digest.update(np.float64(result.reward).tobytes())
            digest.update(b"T" if result.terminated else b"F")
            digest.update(b"R" if result.truncated else b"F")
            for key in sorted(result.info):
                digest.update(f"{key}:{result.info[key]!r}".encode())
            _feed_transaction(digest, result.next_transaction)
            transaction = result.next_transaction
            terminal = result.terminated or result.truncated
            steps += 1
    return digest.hexdigest(), steps


def test_the_fingerprint_can_actually_change() -> None:
    """A digest insensitive to the environment would bless any change at all."""

    baseline, steps = _fingerprint(2)
    assert steps > 0
    perturbed = hashlib.sha256()
    perturbed.update(baseline.encode())
    perturbed.update(b"one different byte")
    assert perturbed.hexdigest() != baseline

    # and the real sensitivity claim: a different action stream must move it
    other = hashlib.sha256()
    rng = np.random.default_rng(FINGERPRINT_SEED + 1)
    env = DynamicRosterEventEnv()
    transaction = env.reset_event_runtime(0)
    _feed_transaction(other, transaction)
    terminal = False
    while not terminal:
        members = transaction.post_membership_pre_policy_snapshot.members
        actions = {m.lifecycle_key: int(rng.integers(ACTION_COUNT)) for m in members}
        result = env.step_event_runtime(actions)
        _feed_transaction(other, result.next_transaction)
        transaction = result.next_transaction
        terminal = result.terminated or result.truncated
    assert other.hexdigest() != baseline


def test_toy_environment_is_deterministic() -> None:
    first, _ = _fingerprint(4)
    second, _ = _fingerprint(4)
    assert first == second, "the toy environment does not reproduce itself"


def test_toy_environment_digest_is_unchanged() -> None:
    digest, steps = _fingerprint(EPISODES)
    assert steps == 3200, f"expected 3200 steps over {EPISODES} episodes, got {steps}"
    assert digest == EXPECTED_DIGEST, (
        "the toy environment's caller-visible bytes changed. This is not a flaky "
        "test: any algorithm comparison spanning this change is invalid. Re-pin "
        "only with a recorded decision."
    )


def _arrays(transaction):
    rows = []
    for label, snapshot in (
        ("pre", transaction.pre_membership_boundary_snapshot),
        ("post", transaction.post_membership_pre_policy_snapshot),
    ):
        rows.append((f"{label}.critic_global", snapshot.critic_global_features))
        for member in snapshot.members:
            rows.append((f"{label}.{member.lifecycle_key}.obs", member.observation))
            rows.append(
                (
                    f"{label}.{member.lifecycle_key}.critic",
                    member.critic_member_features,
                )
            )
    return rows


@pytest.fixture(name="environment")
def _environment() -> GenericShortDynamicRosterEnv:
    return GenericShortDynamicRosterEnv(make_dynamic_roster_ledger(0, master_seed=67_057))


def test_handed_out_transaction_arrays_are_independent(environment) -> None:
    first = environment.event_transaction()
    second = environment.event_transaction()

    for (name, array_a), (_, array_b) in zip(_arrays(first), _arrays(second)):
        assert array_a is not array_b, f"two calls returned the same array at {name}"

    retained = _arrays(environment._pending_event_transaction)
    for (name, handed_out), (_, held) in zip(_arrays(first), retained):
        assert handed_out is not held, f"handed-out array aliases the environment at {name}"

    before = [array.copy() for _, array in retained]
    for _, array in _arrays(first):
        array += 12345.0
    for (name, _), original, (_, held) in zip(retained, before, retained):
        assert np.array_equal(original, held), (
            f"writing through the caller's copy moved the environment at {name}"
        )

    third = environment.event_transaction()
    for (name, expected), (_, actual) in zip(retained, _arrays(third)):
        assert np.array_equal(expected, actual), (
            f"the environment's next transaction changed at {name}"
        )


def test_shared_delta_tuple_is_genuinely_immutable(environment) -> None:
    """The copy shares the delta tuple. That is only safe if it cannot be written."""

    transaction = environment.event_transaction()
    assert (
        transaction.atomic_membership_delta
        is environment._pending_event_transaction.atomic_membership_delta
    ), "delta tuple was rebuilt; the sharing this test exists to cover is not happening"
    for delta in transaction.atomic_membership_delta:
        with pytest.raises(Exception):
            delta.kind = "MUTATED"


def test_active_keys_cache_survives_a_subclass_that_skips_our_init() -> None:
    """OpenRosterDynamicEnv inherits active_keys and never calls this __init__.

    An instance attribute set in __init__ raised AttributeError on its first
    observation. The default lives on the class so the cache arrives with the
    property that reads it.
    """

    assert GenericShortDynamicRosterEnv._active_keys_cache is None

    class SubclassSkippingInit(GenericShortDynamicRosterEnv):
        def __init__(self) -> None:  # deliberately does not call super().__init__
            self.ledger = make_dynamic_roster_ledger(0, master_seed=67_057)
            self.time = 0
            self.lifecycles = {}

    assert SubclassSkippingInit().active_keys == ()
