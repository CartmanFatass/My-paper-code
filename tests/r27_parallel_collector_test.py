from __future__ import annotations

import pytest

from ha_ctse_process.collectors import EnvStep, SubprocEnvCollector


class FakeRemote:
    def __init__(
        self,
        env_id: int,
        *,
        fail_send: bool = False,
        fail_recv: bool = False,
    ) -> None:
        self.env_id = int(env_id)
        self.fail_send = bool(fail_send)
        self.fail_recv = bool(fail_recv)
        self.sent: list[tuple[str, object]] = []
        self.closed = False

    def send(self, payload: tuple[str, object]) -> None:
        if self.fail_send:
            raise BrokenPipeError(f"worker {self.env_id} send failed")
        self.sent.append(payload)

    def recv(self):
        if self.fail_recv:
            raise RuntimeError(f"worker {self.env_id} failed")
        return (
            "ok",
            EnvStep(
                obs=f"obs-{self.env_id}",
                reward=float(self.env_id),
                terminated=False,
                truncated=False,
                info={"env_id": self.env_id},
            ),
        )

    def close(self) -> None:
        self.closed = True


class FakeProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.joined = False

    def is_alive(self) -> bool:
        return not self.terminated

    def terminate(self) -> None:
        self.terminated = True

    def join(self, timeout: float) -> None:
        del timeout
        self.joined = True


def make_fake_collector(num_envs: int) -> SubprocEnvCollector:
    collector = SubprocEnvCollector.__new__(SubprocEnvCollector)
    collector.num_envs = int(num_envs)
    collector.remotes = tuple(FakeRemote(env_id) for env_id in range(num_envs))
    return collector


def test_step_selected_only_touches_requested_workers():
    collector = make_fake_collector(4)

    result = collector.step_selected([(3, "a3"), (1, "a1")])

    assert list(result) == [3, 1]
    assert result[3].info == {"env_id": 3}
    assert result[1].info == {"env_id": 1}
    assert collector.remotes[0].sent == []
    assert collector.remotes[2].sent == []
    assert collector.remotes[3].sent == [("step", "a3")]
    assert collector.remotes[1].sent == [("step", "a1")]


@pytest.mark.parametrize(
    ("indexed_actions", "message"),
    [
        ([(1, "a"), (1, "b")], "duplicate env_id"),
        ([(-1, "a")], "out of range"),
        ([(4, "a")], "out of range"),
    ],
)
def test_step_selected_rejects_invalid_ids(indexed_actions, message):
    collector = make_fake_collector(4)

    with pytest.raises(ValueError, match=message):
        collector.step_selected(indexed_actions)

    assert all(remote.sent == [] for remote in collector.remotes)


def test_existing_step_contract_remains_all_env_list():
    collector = make_fake_collector(3)

    result = collector.step(["a0", "a1", "a2"])

    assert isinstance(result, list)
    assert [step.info["env_id"] for step in result] == [0, 1, 2]
    assert [remote.sent for remote in collector.remotes] == [
        [("step", "a0")],
        [("step", "a1")],
        [("step", "a2")],
    ]


def test_partial_selected_receive_failure_breaks_and_terminates_collector():
    collector = make_fake_collector(3)
    collector.remotes = (
        FakeRemote(0),
        FakeRemote(1, fail_recv=True),
        FakeRemote(2),
    )
    collector.processes = [FakeProcess() for _ in range(3)]

    with pytest.raises(RuntimeError, match="worker 1 failed"):
        collector.step_selected([(0, "a0"), (1, "a1"), (2, "a2")])

    with pytest.raises(RuntimeError, match="broken"):
        collector.step_selected([(0, "next")])
    collector.close()
    assert all(remote.closed for remote in collector.remotes)
    assert all(process.terminated for process in collector.processes)
    assert all(process.joined for process in collector.processes)


def test_partial_selected_send_failure_breaks_collector_before_reuse():
    collector = make_fake_collector(3)
    collector.remotes = (
        FakeRemote(0),
        FakeRemote(1, fail_send=True),
        FakeRemote(2),
    )
    collector.processes = [FakeProcess() for _ in range(3)]

    with pytest.raises(BrokenPipeError, match="worker 1 send failed"):
        collector.step_selected([(0, "a0"), (1, "a1"), (2, "a2")])

    assert collector.remotes[0].sent == [("step", "a0")]
    assert collector.remotes[2].sent == []
    with pytest.raises(RuntimeError, match="broken"):
        collector.step_selected([(2, "next")])
    collector.close()
    assert all(process.terminated for process in collector.processes)
