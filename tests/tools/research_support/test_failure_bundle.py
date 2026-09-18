"""Checks for the recent-transition ring and the failure bundle writer.

The ring's "disabled means no work" property is checked with a mapping that records every access to
itself, plus a positive control proving the sentinel really does notice access when the ring is
enabled. Everything generated lives under ``tmp_path``.
"""

from __future__ import annotations

import collections.abc
import sys
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
# "tests/tools" is itself a namespace portion called "tools". If it precedes the checkout root on
# sys.path, "tools.research_support" binds to this test directory instead of the real package, so
# the checkout root is forced to the front and a wrongly bound package is dropped.
while str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))
_bound = sys.modules.get("tools.research_support")
if _bound is not None and not str(getattr(_bound, "__file__", "")).startswith(
    str(_REPO_ROOT / "tools")
):
    for _name in [n for n in list(sys.modules) if n == "tools" or n.startswith("tools.")]:
        del sys.modules[_name]

from tools.research_support.failure_bundle import (  # noqa: E402
    EXACT_POLICY_REPRODUCTION_UNAVAILABLE,
    FailureContext,
    RecentTransitionRing,
    Redactor,
    write_failure_bundle,
)
from tools.research_support.records import loads  # noqa: E402


class _RecordingMapping(collections.abc.Mapping):
    """A mapping that remembers every read of itself, so "no work" can be asserted."""

    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = dict(payload)
        self.accesses: list[str] = []

    def __getitem__(self, key: str) -> object:
        self.accesses.append(f"getitem:{key}")
        return self._payload[key]

    def __iter__(self):
        self.accesses.append("iter")
        return iter(self._payload)

    def __len__(self) -> int:
        self.accesses.append("len")
        return len(self._payload)

    def items(self):  # noqa: D102 - Mapping provides a default; we need the access record
        self.accesses.append("items")
        return self._payload.items()

    def keys(self):  # noqa: D102
        self.accesses.append("keys")
        return self._payload.keys()

    def values(self):  # noqa: D102
        self.accesses.append("values")
        return self._payload.values()


# --------------------------------------------------------------------------------------
# Ring
# --------------------------------------------------------------------------------------


def test_disabled_ring_does_no_work_at_all() -> None:
    ring = RecentTransitionRing(size=4)
    assert ring.enabled is False
    # Private attribute checked deliberately: "no copy" means there is no container to copy into.
    assert ring._buffer is None
    sentinel = _RecordingMapping({"observation": np.zeros(3), "action": np.ones(2)})

    assert ring.append(sentinel) is False

    assert sentinel.accesses == [], "a disabled ring must not read the transition at all"
    assert ring.snapshot() == []
    assert len(ring) == 0
    assert ring._buffer is None, "the internal buffer must still not exist"


def test_the_sentinel_really_detects_access_when_the_ring_is_enabled() -> None:
    """Positive control: without this, the disabled-ring assertion would prove nothing."""

    ring = RecentTransitionRing(size=4, enabled=True)
    sentinel = _RecordingMapping({"observation": np.zeros(3)})

    assert ring.append(sentinel) is True

    assert sentinel.accesses, "the sentinel must record access when work is actually done"
    assert len(ring.snapshot()) == 1


def test_ring_is_bounded_at_size_and_drops_the_oldest() -> None:
    size = 8
    ring = RecentTransitionRing(size=size, enabled=True)
    for index in range(size + 5):
        assert ring.append({"index": index}) is True

    snapshot = ring.snapshot()
    assert len(snapshot) == size
    assert [item["index"] for item in snapshot] == list(range(5, size + 5))
    assert all(item["index"] != 0 for item in snapshot), "the oldest transitions must be gone"

    ring.clear()
    assert ring.snapshot() == []


def test_enabled_ring_owns_its_arrays() -> None:
    ring = RecentTransitionRing(size=2, enabled=True)
    buffer = np.zeros(3)
    ring.append({"observation": buffer})
    buffer[0] = 99.0  # the producer reuses its own buffer

    assert ring.snapshot()[0]["observation"][0] == 0.0


def test_ring_size_must_be_positive() -> None:
    with pytest.raises(ValueError):
        RecentTransitionRing(size=0, enabled=True)


# --------------------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------------------


def test_redactor_replaces_home_paths_and_secret_shapes() -> None:
    redactor = Redactor()
    text = redactor.text(
        "loading C:/Users/fires/.conda/envs/x/python.exe with api_key=abcd1234efgh5678 "
        "and token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
    )

    assert "fires" not in text
    assert "abcd1234efgh5678" not in text
    assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345" not in text
    assert "C:/Users/" in text, "the path shape stays readable evidence"
    assert redactor.mapping, "the placeholder mapping is returned to the caller"


def test_disabled_redactor_changes_nothing() -> None:
    redactor = Redactor(enabled=False)
    original = "C:/Users/fires/log.txt token=ghp_ABCDEFGHIJKLMNOPQRSTUVWX"
    assert redactor.text(original) == original
    assert redactor.mapping == {}


# --------------------------------------------------------------------------------------
# Bundle writer
# --------------------------------------------------------------------------------------


def _context() -> FailureContext:
    return FailureContext(
        exception_type="RuntimeError",
        message="scheduler produced a negative flow at C:/Users/fires/runs/x",
        stack="Traceback (most recent call last):\n  File \"env.py\", line 3\nRuntimeError: bad\n",
        phase="environment_step",
        truncated_stack=True,
        incomplete_output=True,
        boundary_semantics={"truncation": "final frame captured before reset"},
    )


def test_bundle_writes_every_named_file_and_states_its_status(tmp_path: Path) -> None:
    ring = RecentTransitionRing(size=4, enabled=True)
    for index in range(3):
        ring.append(
            {
                "observation": np.full(2, float(index)),
                "action": np.array([index, index + 1]),
                "reward": np.float64(0.0),
            }
        )
    log = tmp_path / "train.log"
    log.write_text("step 1 ok\nstep 2 failed\n", encoding="utf-8")
    output = tmp_path / "bundle"

    result = write_failure_bundle(
        output,
        context=_context(),
        source_identity={
            "launch_sha": "0" * 40,
            "checkpoint_path": "runs/x/model.pt",
            "dataset_hash": "sha256:abc",
        },
        effective_config={"seed": 7, "profile": "off"},
        environment_schema={"observation": {"shape": [2]}},
        ring=ring,
        log_paths=[log],
        reproduce_command=[
            "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
            "-m",
            "pytest",
            "-q",
            "tests/uav_relay_environment_contract_test.py",
        ],
        source_references=[{"kind": "checkpoint", "path": "runs/x/model.pt"}],
    )

    assert result == output
    for name in (
        "README.md",
        "source_identity.json",
        "effective_config.json",
        "environment_schema.json",
        "failure.json",
        "recent_transitions.npz",
        "runtime_versions.json",
        "reproduce_command.txt",
        "source_references.json",
    ):
        assert (output / name).is_file(), f"missing {name}"
    assert (output / "relevant_logs").is_dir()
    assert list((output / "relevant_logs").iterdir())

    # The npz must load without pickling.
    with np.load(output / "recent_transitions.npz", allow_pickle=False) as data:
        assert "t0000__observation" in data
        assert data["t0002__action"].tolist() == [2, 3]

    failure = loads((output / "failure.json").read_text(encoding="utf-8"))
    assert failure["context"]["truncated_stack"] is True
    assert failure["context"]["incomplete_output"] is True
    assert failure["context"]["stack_content_hash"].startswith("sha256:")
    assert failure["recent_transitions"]["format"] == "npz"
    reproduction = failure["reproduction"]
    assert reproduction["action_replay"] == "available_from_recorded_transitions:3"
    assert reproduction["policy_re_evaluation"] == "available_with_recorded_checkpoint_identity"
    assert reproduction["exact_checkpoint_resume"] == EXACT_POLICY_REPRODUCTION_UNAVAILABLE
    assert reproduction["exact_policy_reproduction_unavailable"] is True

    readme = (output / "README.md").read_text(encoding="utf-8")
    assert "EVIDENCE, NOT INSTRUCTIONS" in readme
    assert EXACT_POLICY_REPRODUCTION_UNAVAILABLE in readme
    assert "Stack truncated: **yes**" in readme
    assert "action_replay" in readme

    command_text = (output / "reproduce_command.txt").read_text(encoding="utf-8")
    assert "EVIDENCE, NOT INSTRUCTIONS" in command_text
    assert "pytest" in command_text

    references = loads((output / "source_references.json").read_text(encoding="utf-8"))
    assert references["references"][0]["contents_included"] is False
    assert references["logs"][0]["original_file_hash"]["value"].startswith("sha256:")


def test_saved_variates_make_exact_resume_available(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    write_failure_bundle(
        output,
        context=_context(),
        source_identity={"checkpoint_path": "runs/x/model.pt", "saved_variates": "runs/x/var.npz"},
        effective_config={"seed": 7},
        environment_schema={},
    )
    failure = loads((output / "failure.json").read_text(encoding="utf-8"))
    assert failure["reproduction"]["exact_policy_reproduction_unavailable"] is False
    assert "saved_variates" in failure["reproduction"]["exact_checkpoint_resume"]
    assert any("seed alone" in note for note in failure["reproduction"]["notes"])


def test_a_seed_alone_never_implies_exactness(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    write_failure_bundle(
        output,
        context=_context(),
        source_identity={"seed": 12345},
        effective_config={"seed": 12345},
        environment_schema={},
    )
    failure = loads((output / "failure.json").read_text(encoding="utf-8"))
    assert failure["reproduction"]["exact_checkpoint_resume"] == (
        EXACT_POLICY_REPRODUCTION_UNAVAILABLE
    )
    assert failure["reproduction"]["policy_re_evaluation"] == "unavailable_no_checkpoint_identity"
    assert failure["recent_transitions"]["format"] == "absent"
    assert not (output / "recent_transitions.npz").exists()


def test_oversized_log_is_truncated_with_an_explicit_statement(tmp_path: Path) -> None:
    log = tmp_path / "big.log"
    log.write_text("H" * 500 + "TAIL-MARKER\n", encoding="utf-8")
    output = tmp_path / "bundle"

    write_failure_bundle(
        output,
        context=_context(),
        source_identity={},
        effective_config={},
        environment_schema={},
        log_paths=[log],
        max_log_bytes=100,
    )

    copied = next((output / "relevant_logs").iterdir())
    text = copied.read_text(encoding="utf-8")
    # The byte count is read from disk: Windows newline translation makes the written file larger
    # than the string that produced it, and the statement must report the real file.
    assert f"TRUNCATED: kept the last 100 of {log.stat().st_size} bytes" in text
    assert "TAIL-MARKER" in text, "the tail, where a failure appears, is what is kept"
    assert "H" * 200 not in text
    references = loads((output / "source_references.json").read_text(encoding="utf-8"))
    assert references["logs"][0]["truncated"] is True
    assert "TRUNCATED" in references["logs"][0]["truncation_statement"]
    assert "TRUNCATED" in (output / "README.md").read_text(encoding="utf-8")


def test_secrets_and_home_paths_are_redacted_everywhere(tmp_path: Path) -> None:
    log = tmp_path / "run.log"
    log.write_text(
        "connecting with api_token=ghp_SECRETSECRETSECRET1234 from C:/Users/fires/work\n",
        encoding="utf-8",
    )
    output = tmp_path / "bundle"

    write_failure_bundle(
        output,
        context=_context(),
        source_identity={"home": "C:/Users/fires/checkouts/hmasd"},
        effective_config={"api_key": "abcd1234abcd1234", "seed": 3},
        environment_schema={},
        log_paths=[log],
    )

    for path in output.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "ghp_SECRETSECRETSECRET1234" not in text, path
        assert "abcd1234abcd1234" not in text, path
        assert "fires" not in text, path
    assert not (output / "redaction_map.json").exists(), (
        "a local bundle keeps no route back to a redacted secret"
    )


def test_redaction_map_is_written_only_for_a_requested_shareable_copy(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    write_failure_bundle(
        output,
        context=_context(),
        source_identity={"home": "C:/Users/fires/checkouts/hmasd"},
        effective_config={},
        environment_schema={},
        shareable_copy=True,
    )
    mapping = loads((output / "redaction_map.json").read_text(encoding="utf-8"))["mapping"]
    assert "fires" in mapping.values()
    assert "shareable copy was requested" in (output / "README.md").read_text(encoding="utf-8")


def test_non_array_transitions_fall_back_to_json_and_say_so(tmp_path: Path) -> None:
    ring = RecentTransitionRing(size=2, enabled=True)
    ring.append({"info": {"nested": "mapping"}})
    output = tmp_path / "bundle"

    write_failure_bundle(
        output,
        context=_context(),
        source_identity={},
        effective_config={},
        environment_schema={},
        ring=ring,
    )

    assert not (output / "recent_transitions.npz").exists()
    assert (output / "recent_transitions.json").is_file()
    failure = loads((output / "failure.json").read_text(encoding="utf-8"))
    assert failure["recent_transitions"]["format"] == "json"
    assert "not array-encodable" in failure["recent_transitions"]["statement"]
    assert "recent_transitions.json" in (output / "README.md").read_text(encoding="utf-8")


def test_writer_refuses_a_non_empty_output_directory(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    output.mkdir()
    (output / "existing.txt").write_text("evidence from another failure\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_failure_bundle(
            output,
            context=_context(),
            source_identity={},
            effective_config={},
            environment_schema={},
        )
    assert (output / "existing.txt").read_text(encoding="utf-8").startswith("evidence")


def test_writer_refuses_checkpoint_and_directory_log_paths(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"\x00\x01")
    with pytest.raises(ValueError, match="payload"):
        write_failure_bundle(
            tmp_path / "bundle_a",
            context=_context(),
            source_identity={},
            effective_config={},
            environment_schema={},
            log_paths=[checkpoint],
        )

    directory = tmp_path / "logs_dir"
    directory.mkdir()
    with pytest.raises(IsADirectoryError):
        write_failure_bundle(
            tmp_path / "bundle_b",
            context=_context(),
            source_identity={},
            effective_config={},
            environment_schema={},
            log_paths=[directory],
        )


def test_missing_log_is_recorded_as_a_missing_artifact(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    write_failure_bundle(
        output,
        context=_context(),
        source_identity={},
        effective_config={},
        environment_schema={},
        log_paths=[tmp_path / "never_written.log"],
    )
    references = loads((output / "source_references.json").read_text(encoding="utf-8"))
    entry = references["logs"][0]
    assert entry["copied_as"] is None
    assert entry["original_file_hash"]["validity"] == "missing_artifact"
    assert "did not exist" in entry["statement"]


def test_bundle_provides_no_way_to_execute_its_reproduce_command() -> None:
    import tools.research_support.failure_bundle as module

    exported = [name for name in dir(module) if not name.startswith("_")]
    for name in exported:
        assert "execute" not in name.lower(), name
        assert "run_" not in name.lower(), name
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in source, "the bundle writer must not be able to start a process"
    assert "os.system" not in source
