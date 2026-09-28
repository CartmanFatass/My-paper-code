"""CPU crash harness: resumes c03 and runs the real collector for a bounded number of steps."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.candidates.energy_relay_benchmark.diagnostics import crash_harness as ch

C03 = ch.DEFAULT_CHECKPOINT


def test_arguments():
    args = ch.parse_args(["--out", "x", "--steps", "5"])
    assert (args.collector, args.malloc, args.threads, args.audit) == ("b05", "inherit", 4, False)
    with pytest.raises(SystemExit):
        ch.parse_args(["--out", "x", "--steps", "0"])
    with pytest.raises(SystemExit):
        ch.parse_args(["--out", "x", "--steps", "5", "--malloc", "tcmalloc"])


@pytest.mark.skipif(not (C03 / "agent.pt").exists(), reason="local B02 c03 checkpoint absent")
@pytest.mark.parametrize("collector", ["b05", "b02"])
def test_bounded_resume_run_writes_summary(tmp_path, monkeypatch, collector):
    import os

    monkeypatch.setenv("HMASD_UAV_CPP_BUILD_ROOT",
                       os.environ.get("HMASD_UAV_CPP_BUILD_ROOT", str(tmp_path / "build")))
    args = ch.parse_args(["--out", str(tmp_path / "run"), "--steps", "3", "--sample-every", "2",
                          "--collector", collector, "--threads", "1", "--allow-core",
                          "--launch-sha", "test"])
    summary = ch.run(args)
    saved = json.loads((tmp_path / "run" / "summary.json").read_text(encoding="utf-8"))
    for record in (summary, saved):
        assert record["status"] == "STOPPED" and record["ending"] == {"kind": "steps"}
        assert record["steps_completed"] == 3 and record["env_steps"] == 4
        assert record["seed"] == 925131 and record["checkpoint_rollout"] == 100
        assert record["collector"] == collector and record["launch_sha"] == "test"
    with pytest.raises(FileExistsError):
        ch.run(args)
