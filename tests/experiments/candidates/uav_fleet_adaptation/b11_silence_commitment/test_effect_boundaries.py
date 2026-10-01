"""Focused output/admission/assets/integrity fixtures; no episode execution."""
import os
import numpy as np
import pytest
import torch
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import checked_path
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment import assets,run,study
from experiments.candidates.uav_local_history.b01.study import file_identity


def test_launcher_owned_directory_reaches_checked_asset_load(tmp_path,monkeypatch):
    out=tmp_path/"admitted"
    out.mkdir()
    names=("launch-status.json","launch-manifest.json","admission-preflight.json","stdout.log","stderr.log")
    for name in names:
        (out/name).write_text("launcher fixture")
    seen=[]
    monkeypatch.setattr(study,"source_identities",lambda repo:{})
    def reject(paths):
        seen.append(paths)
        raise ValueError("mock asset reached; no env/scientific effects")
    monkeypatch.setattr(study,"load_assets",reject)
    with pytest.raises(ValueError,match="mock asset reached"):
        study.run_batch(out,"fake-sha",admission={"sha":"fake-sha"},asset_paths={"P0":tmp_path/"unused.pt"})
    assert seen==[{"P0":tmp_path/"unused.pt"}]
    assert list((out/"raw").iterdir())==[]
    assert all((out/name).read_text()=="launcher fixture" for name in names)


@pytest.mark.parametrize("existing",("raw","summary.json","episodes.jsonl","reading.json","stdout.log"))
def test_previous_scientific_payload_rejected_before_assets(tmp_path,monkeypatch,existing):
    out=tmp_path/"previous"
    out.mkdir()
    if existing in ("raw","stdout.log"):
        (out/existing).mkdir() # A name in the allowlist must also be an actual file.
    else:
        (out/existing).write_text("existing evidence")
    def forbidden(*args,**kwargs):
        raise AssertionError("touched source/assets after existing output")
    monkeypatch.setattr(study,"source_identities",forbidden)
    monkeypatch.setattr(study,"load_assets",forbidden)
    with pytest.raises(FileExistsError,match="scientific output exists"):
        study.run_batch(out,"fake",admission={"sha":"fake"},asset_paths={})
    assert set(path.name for path in out.iterdir())=={existing}


def test_entry_admission_precedes_output_runtime_assets(tmp_path,monkeypatch):
    from scripts import hmasd_admission
    prior=dict(os.environ)
    def rejected(*args,**kwargs):
        raise ValueError("fixture admission denied")
    monkeypatch.setattr(hmasd_admission,"require_admission",rejected)
    def forbidden(*args,**kwargs):
        raise AssertionError("runtime/worker touched before admission")
    monkeypatch.setattr(torch,"set_num_threads",forbidden)
    monkeypatch.setattr(study,"run_batch",forbidden)
    with pytest.raises(ValueError,match="fixture admission denied"):
        run.main(["--out",str(tmp_path/"absent"),"--launch-sha","fake","--seed","30022000","--p0",str(tmp_path/"absent.pt")])
    assert dict(os.environ)==prior and not (tmp_path/"absent").exists()


def test_p0_hash_is_checked_before_student_construction(tmp_path,monkeypatch):
    path=tmp_path/"fabricated_not_production.pt"
    path.write_bytes(b"invalid P0 fixture")
    def forbidden(*args,**kwargs):
        raise AssertionError("constructed/loaded before artifact hash")
    monkeypatch.setattr(assets,"make_student",forbidden)
    monkeypatch.setattr(torch,"load",forbidden)
    with pytest.raises(ValueError,match="artifact identity"):
        assets.load_assets({"P0":path})
    with pytest.raises(ValueError,match="P0 only"):
        assets.load_assets({"P0":path,"HIDDEN":path})


def test_raw_hash_and_path_corruption(tmp_path):
    out=tmp_path/"out"
    out.mkdir()
    path=out/"fixture.npz"
    np.savez_compressed(path,fixture=np.zeros(1))
    identity=file_identity(path)
    assert checked_path(out,"fixture.npz",identity)==path
    path.write_bytes(path.read_bytes()+b"corruption")
    with pytest.raises((ValueError,AssertionError),match="identity|sha|bytes|digest|artifact"):
        checked_path(out,"fixture.npz",identity)
    with pytest.raises((ValueError,AssertionError),match="path|escap|artifact"):
        checked_path(out,"../outside.npz",identity)
