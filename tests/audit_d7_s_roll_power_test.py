"""The roll-power counters must survive the worker-process boundary.

Step H returned 8/8 shards, passed every mechanical gate, and still could not
say whether the source-assignment defect fired during it -- because nothing
recorded rejoins. `roll_power` closes that: rejoin events, leave events, and the
number of partial-injection checks actually performed.

The counter is a module global, and episode work runs under
`ProcessPoolExecutor` whenever `--workers` > 1. A parent-side read would report
ZERO checks on a run that performed thousands, which in the artifact is
indistinguishable from a guard that never ran -- the exact failure this counter
exists to make visible, reintroduced one level up.

`test_the_process_boundary_really_does_lose_the_counter` proves the trap is real
rather than hypothetical. Without it, the payload plumbing looks like
superstition and the next person "simplifies" it away.
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import audit_d7_s_event_aligned as audit  # noqa: E402


def _count_in_child(n: int) -> tuple[int, int]:
    """Run checks in THIS process and report (pid, local count)."""
    audit.reset_injectivity_check_count()
    for i in range(n):
        audit.assert_partial_injection({0: i})
    return os.getpid(), audit.injectivity_check_count()


def test_counter_increments_once_per_check() -> None:
    audit.reset_injectivity_check_count()
    for i in range(7):
        audit.assert_partial_injection({0: i, 1: i + 100})
    assert audit.injectivity_check_count() == 7


def test_counter_counts_a_refusal_too() -> None:
    """A refused map was still a check. If refusals were not counted, a run that
    refused on its first boundary would report zero checks performed."""

    audit.reset_injectivity_check_count()
    with pytest.raises(audit.SourceAssignmentInvariantError):
        audit.assert_partial_injection({0: 5, 1: 5})
    assert audit.injectivity_check_count() == 1


def test_the_process_boundary_really_does_lose_the_counter() -> None:
    """The trap, demonstrated. This is why roll_power rides the return payload."""

    audit.reset_injectivity_check_count()
    parent_pid = os.getpid()
    with ProcessPoolExecutor(max_workers=2) as pool:
        child_pid, child_count = pool.submit(_count_in_child, 25).result()

    if child_pid == parent_pid:
        pytest.skip("executor did not actually fork a separate process")

    assert child_count == 25, "the child did perform the checks"
    assert audit.injectivity_check_count() == 0, (
        "the parent's global saw the child's checks, so this platform shares the "
        "counter and the premise of the payload plumbing would need rechecking"
    )


def test_accumulator_sums_roll_power_across_episodes() -> None:
    report = audit._new_episode_block_report()
    for rejoins, leaves, checks, steps in ((2, 3, 40, 100), (0, 1, 17, 50)):
        audit._accumulate_episode_leave_stats(
            report,
            leave_diagnostics=[],
            rejected_counts={},
            roll_power={"rejoin_events": rejoins, "leave_events": leaves,
                        "injectivity_checks": checks, "steps_rolled": steps},
        )
    assert report["roll_power"] == {
        "rejoin_events": 2, "leave_events": 4,
        "injectivity_checks": 57, "steps_rolled": 150,
    }


def test_accumulator_tolerates_a_missing_roll_power() -> None:
    """Older callers and the sequential path must not crash the accumulator."""

    report = audit._new_episode_block_report()
    audit._accumulate_episode_leave_stats(
        report, leave_diagnostics=[], rejected_counts={})
    assert report["roll_power"]["rejoin_events"] == 0
