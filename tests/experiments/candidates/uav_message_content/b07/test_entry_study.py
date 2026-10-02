import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.uav_message_content.b07 import run, study
from experiments.candidates.uav_message_content.b07.contract import EXPECTED, B_SHA, D_SHA


def argv(tmp_path):
    return ["--out", str(tmp_path / "out"), "--launch-sha", "a" * 40, "--seed", "19811",
            "--input-manifest", str(tmp_path / "inputs.json"), "--input-manifest-sha256", "b" * 64,
            "--d-checkpoint", str(tmp_path / "D.pt"), "--d-checkpoint-sha256", D_SHA,
            "--b-checkpoint", str(tmp_path / "B.pt"), "--b-checkpoint-sha256", B_SHA]


def test_parser_and_admission_before_effects(tmp_path, monkeypatch):
    import scripts.hmasd_admission as admission
    effects = []
    def denied(*args, **kwargs):
        effects.append("admission")
        raise RuntimeError("synthetic admission refusal")
    monkeypatch.setattr(admission, "require_admission", denied)
    monkeypatch.setattr(study, "run_batch", lambda *a, **k: effects.append("study"))
    with pytest.raises(RuntimeError, match="refusal"):
        run.main(argv(tmp_path))
    assert effects == ["admission"] and not (tmp_path / "out").exists()
    with pytest.raises(SystemExit):
        run.main(argv(tmp_path) + ["--horizon", "8"])
    with pytest.raises(SystemExit):
        run.main(["--seed", "1"])


def test_mocked_admitted_complete_wiring_with_launcher_owned_output(tmp_path, monkeypatch):
    import scripts.hmasd_admission as admission
    out = tmp_path / "out"
    out.mkdir()
    (out / "launch-manifest.json").write_text('{"launcher":"synthetic"}')
    (tmp_path / "inputs.json").write_text('{}')
    calls = dict(O=0, L=0, dev=0, native=0, reader=0)
    actor = torch.nn.Linear(1, 1).requires_grad_(False)
    monkeypatch.setattr(admission, "require_admission", lambda *a, **k: {"sha": "a" * 40})
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: None)
    ep = {"packet": __import__('numpy').zeros((256, 10), dtype='float32')}
    monkeypatch.setattr(study, "load_inputs", lambda *a: ({"synthetic": True}, [ep] * 32))
    monkeypatch.setattr(study, "load_receiver", lambda *a: actor)
    monkeypatch.setattr(study, "binding_replay", lambda *a: {"synthetic": True})
    def ordinary(*a):
        calls["O"] += 1
        a[4]({"iteration": 0}, torch.zeros(256, 6))
        return torch.zeros(256, 6), torch.zeros(256, 6), [], 0.
    def learned(*a):
        calls["L"] += 1
        a[6]({"epoch": 0, "batch": 0}, torch.zeros(256, 6))
        return torch.zeros(256, 6), []
    def score(*a):
        calls["dev"] += 1
        return 0.
    class Environment:
        def close(self):
            pass
    monkeypatch.setattr(study, "fit_ordinary", ordinary)
    monkeypatch.setattr(study, "fit_learned", learned)
    monkeypatch.setattr(study, "score", score)
    monkeypatch.setattr(study, "make_real", lambda *a: Environment())
    def collect(env, actor, kind, codec, world, path, counts, progress):
        calls["native"] += 1
        return {"world": world}
    monkeypatch.setattr(study, "collect_episode", collect)
    def reader(rows, actors, selected, counts, progress):
        calls["reader"] += 1
        assert len(rows) == 8 and all(len(panel) == 32 for panel in rows.values())
        assert len(selected) == 6
        counts.update(EXPECTED)
        return {"synthetic_mock": True}
    monkeypatch.setattr(study, "full_read", reader)
    result = run.main(argv(tmp_path))
    assert result["status"] == "COMPLETE", result["limits"]
    assert calls == {"O": 6, "L": 6, "dev": 12, "native": 256, "reader": 1}
    assert result["total_actor_rows"] == 4505600
    assert json.loads((out / "launch-manifest.json").read_text()) == {"launcher": "synthetic"}
    assert all(c["metric"] == "unit" for c in result["selection"].values())
    with pytest.raises(ValueError, match="already exists"):
        study.run_batch(SimpleNamespace(out=out), start_wall=time.monotonic(), start_cpu=time.process_time())


def test_failure_manifest_identity_preserves_summary(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{}')
    args = SimpleNamespace(out=tmp_path / "out", input_manifest=manifest, input_manifest_sha256="wrong",
                           d_checkpoint=tmp_path / "D.pt", d_checkpoint_sha256=D_SHA,
                           b_checkpoint=tmp_path / "B.pt", b_checkpoint_sha256=B_SHA, launch_sha="a" * 40)
    result = study.run_batch(args, start_wall=time.monotonic(), start_cpu=time.process_time())
    assert result["status"] == "INCOMPLETE" and result["counts"]["fits_started"] == 0
    assert "manifest digest" in result["limits"][0]
    assert result["failure_frontier"] == {"phase": "inputs"}
    assert (args.out / "summary.json").exists() and (args.out / "progress.json").exists()
