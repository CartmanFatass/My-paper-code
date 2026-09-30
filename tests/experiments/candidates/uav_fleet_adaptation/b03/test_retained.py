"""Metadata-only retained-control fixtures; no native episode or teacher work."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.uav_fleet_adaptation.b02 import contract
from experiments.candidates.uav_fleet_adaptation.b03 import retained

REPO = Path(__file__).resolve().parents[5]


def file_record(path):
    content = path.read_bytes()
    return dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())


class Fixture:
    def __init__(self, root):
        self.root = root
        root.mkdir()
        (root / "raw").mkdir()
        self.old = contract.Protocol(training_worlds=((101,), (102,), (103,)),
                                     evaluation_worlds=(201,), init_seed=301, shuffle_root=302,
                                     sampling_root=303, horizon=4, epochs=(1, 1, 1), batch_size=5).validate()
        self.new = replace(self.old, training_worlds=((111,), (112,), (113,)),
                           init_seed=311, shuffle_root=312).validate()
        expected = self.old.expected()
        source = contract.source_identities(REPO)
        controller = source["experiments/candidates/uav_fleet_adaptation/b02/controllers.py"]
        rows = []
        entries = [(arm, world, "training", phase)
                   for phase, (arm, worlds) in enumerate(zip(contract.PHASES, self.old.training_worlds))
                   for world in worlds]
        entries += [(arm, world, "evaluation", None)
                    for arm in contract.ARMS for world in self.old.evaluation_worlds]
        for arm, world, kind, phase in entries:
            relative = f"raw/{arm}_{world}.npz"
            path = root / relative
            # Opaque synthetic bytes deliberately need no array/model loading.
            path.write_bytes(f"synthetic:{arm}:{world}".encode())
            rows.append(dict(arm=arm, world=world, kind=kind, phase=phase, steps=self.old.horizon,
                             policy_sha256=controller if arm in retained.CONTROLS else "synthetic-neural",
                             raw=dict(path=relative, **file_record(path)), metric=world / 1000))
        actual = {key: expected[key] for key in (
            "native_steps", "training_native_steps", "evaluation_native_steps", "complete_episodes",
            "training_episodes", "evaluation_episodes", "sample_presentations", "expert_label_requests")}
        actual.update(fit_started=1, constructors=1, constructor_resets=1,
                      explicit_resets=expected["complete_episodes"], native_step_calls=expected["native_steps"],
                      optimizer_steps=expected["optimizer_updates"])
        costs = dict(full_C=dict(requests=expected["full_C_requests"]),
                     C7=dict(requests=expected["C7_requests"]), helper=dict(helper_calls=0),
                     neural=dict(neural_rows=0, sampled_draws=expected["sampled_draws"]))
        sha = "synthetic-retained-lineage"
        environment = retained._runtime()
        admission = dict(schema_version=1, sha=sha, direction="uav_fleet_adaptation",
                         command_sha256="f" * 64, parent_pid=11, child_pid=12)
        parent, child = dict(kind="synthetic", pid=11), dict(kind="synthetic", pid=12)
        self.docs = {
            "summary.json": dict(object="UAV-LOCAL-C-INHERITANCE-B02", status="COMPLETE", launch_sha=sha,
                                 scientific_invocation=False, protocol=self.old.to_dict(), expected=expected,
                                 actual=actual, source_sha256=source, environment=environment, admission=admission,
                                 rows=rows, costs=costs, assets={"synthetic": {"optimizer_steps": 6}},
                                 reading={"synthetic_comparison": 0.125}),
            "reading.json": dict(object="UAV-LOCAL-C-INHERITANCE-B02", status="VERIFIED", launch_sha=sha,
                                 expected=deepcopy(expected), actual=deepcopy(actual), costs=deepcopy(costs),
                                 assets={"synthetic": {"optimizer_steps": 6}}, reading={"synthetic_comparison": 0.125},
                                 raw_files=len(rows), raw_bytes=sum(row["raw"]["bytes"] for row in rows),
                                 native_ticks_verified=actual["native_steps"],
                                 decisions_verified=expected["expert_label_requests"]
                                 + expected["evaluation_native_steps"] // self.old.period * self.old.n_agents,
                                 reader_calls=dict(native=0, expert_queries=0, radio_power_model=0,
                                                   actor_forward=0, optimizer=0),
                                 per_row=[dict(arm=row["arm"], world=row["world"], kind=row["kind"],
                                               verified=True, raw_sha256=row["raw"]["sha256"]) for row in rows]),
            "launch-manifest.json": dict(schema_version=1, acceptance="accepted", sha=sha,
                                         direction="uav_fleet_adaptation", command_sha256="f" * 64,
                                         node="fixture", host_identity=environment["host"], output_root=str(root),
                                         process=dict(pid=11, identity=parent), runner_process=dict(pid=12, identity=child)),
            "process-exit.json": dict(schema_version=1, status="exited", termination="process_exit", exit_code=0,
                                      pid=12, process_identity=child, supervisor_identity=parent),
        }
        self.rebind()

    @property
    def batch(self):
        return self.docs["summary.json"]

    def rebind(self):
        self.docs["config.json"] = {key: deepcopy(self.batch[key]) for key in (
            "object", "launch_sha", "scientific_invocation", "protocol", "expected", "source_sha256", "environment")}
        summary = self.root / "summary.json"
        summary.write_text(json.dumps(self.batch))
        self.docs["reading.json"]["summary"] = dict(path=str(summary), **file_record(summary))
        for name, document in self.docs.items():
            (self.root / name).write_text(json.dumps(document))
        self.binding = dict(launch_sha=self.batch["launch_sha"], files={
            name: file_record(self.root / name) for name in retained.BINDING["files"]})

    def load(self, **kwargs):
        return retained.load_retained(self.root, kwargs.pop("protocol", self.new), repo=REPO,
                                      permit_fixture=kwargs.pop("permit_fixture", True),
                                      binding=kwargs.pop("binding", self.binding), **kwargs)


@pytest.fixture
def fixture(tmp_path):
    return Fixture(tmp_path / "retained")


def test_returns_unchanged_rows_and_facts_without_work_or_writes(fixture, monkeypatch):
    from experiments.candidates.uav_fleet_adaptation.b02 import read, study
    from experiments.candidates.uav_local_history.b01 import controller

    def forbidden(*args, **kwargs):
        pytest.fail("retained loading must not perform model/native/replay work")

    monkeypatch.setattr(retained.np, "load", forbidden)
    monkeypatch.setattr(study, "run_batch", forbidden)
    monkeypatch.setattr(read, "check_episode", forbidden)
    monkeypatch.setattr(controller.LocalController, "act", forbidden)
    monkeypatch.setattr(controller, "_power", forbidden)
    before = {path.relative_to(fixture.root): path.read_bytes() for path in fixture.root.rglob("*") if path.is_file()}
    result = fixture.load()
    controls = [row for row in fixture.batch["rows"] if row["kind"] == "evaluation" and row["arm"] in retained.CONTROLS]
    assert result["rows"] == controls
    assert result["original_protocol"] == fixture.old.to_dict()
    assert result["old_reading"] == fixture.batch["reading"]
    assert result["old_assets"] == fixture.batch["assets"]
    assert result["source_sha256"] == fixture.batch["source_sha256"]
    assert result["binding"] == fixture.binding
    assert result["raw_verification"] == dict(files=2, bytes=sum(row["raw"]["bytes"] for row in controls))
    after = {path.relative_to(fixture.root): path.read_bytes() for path in fixture.root.rglob("*") if path.is_file()}
    assert before == after


@pytest.mark.parametrize("name", tuple(retained.BINDING["files"]))
def test_metadata_tamper_is_rejected(fixture, name):
    with (fixture.root / name).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(AssertionError, match="artifact identity mismatch"):
        fixture.load()


@pytest.mark.parametrize("arm", retained.CONTROLS)
def test_raw_tamper_is_rejected(fixture, arm):
    row = next(row for row in fixture.batch["rows"] if row["arm"] == arm and row["kind"] == "evaluation")
    (fixture.root / row["raw"]["path"]).write_bytes(b"tampered")
    with pytest.raises(AssertionError, match="artifact identity mismatch"):
        fixture.load()


def test_raw_escape_is_rejected_even_with_matching_bytes(fixture):
    row = next(row for row in fixture.batch["rows"] if row["arm"] == "C7_memo")
    outside = fixture.root.parent / "outside.npz"
    outside.write_bytes((fixture.root / row["raw"]["path"]).read_bytes())
    row["raw"]["path"] = "../outside.npz"
    fixture.rebind()
    with pytest.raises(AssertionError, match="artifact escapes"):
        fixture.load()


@pytest.mark.parametrize("protocol_change", [
    {"training_worlds": ((101,), (112,), (113,))},
    {"training_worlds": ((201,), (112,), (113,))},
    {"init_seed": 301}, {"shuffle_root": 302}, {"init_seed": 302},
])
def test_new_lineage_identities_must_be_fresh(fixture, protocol_change):
    with pytest.raises(ValueError, match="reuse original|training/evaluation worlds overlap"):
        fixture.load(protocol=replace(fixture.new, **protocol_change))


@pytest.mark.parametrize("protocol_change", [
    {"learning_rate": 1e-3}, {"horizon": 8}, {"epochs": (2, 1, 1)},
    {"sampling_root": 304}, {"evaluation_worlds": (202,)},
    {"training_worlds": ((111, 114), (112,), (113,))},
])
def test_recipe_evaluation_and_sampling_must_match(fixture, protocol_change):
    with pytest.raises(ValueError, match="recipe/evaluation/sampling changed|phase sizes changed"):
        fixture.load(protocol=replace(fixture.new, **protocol_change))


def test_changed_source_inventory_is_rejected(fixture, monkeypatch):
    source = deepcopy(fixture.batch["source_sha256"])
    source["experiments/candidates/uav_fleet_adaptation/b02/controllers.py"] = "0" * 64
    monkeypatch.setattr(contract, "source_identities", lambda repo: source)
    with pytest.raises(ValueError, match="source identities changed"):
        fixture.load()


@pytest.mark.parametrize("field", ["python", "numpy", "torch", "device", "dtype", "host",
                                  "torch_threads", "torch_interop_threads", "thread_environment"])
def test_runtime_changes_are_rejected(fixture, field):
    fixture.batch["environment"][field] = "different"
    fixture.rebind()
    with pytest.raises(ValueError, match="runtime/host/thread"):
        fixture.load()


@pytest.mark.parametrize("which", ["duplicate", "missing", "wrong_world", "wrong_arm"])
def test_control_identity_must_be_complete_and_unique(fixture, which):
    index = next(i for i, row in enumerate(fixture.batch["rows"]) if row["arm"] == "C7_memo")
    if which == "duplicate":
        fixture.batch["rows"][index] = deepcopy(fixture.batch["rows"][index - 1])
    elif which == "missing":
        fixture.batch["rows"].pop(index)
    elif which == "wrong_world":
        fixture.batch["rows"][index]["world"] = 999
    else:
        fixture.batch["rows"][index]["arm"] = "S0"
    fixture.rebind()
    with pytest.raises(ValueError, match="control arms or worlds|coverage/call count"):
        fixture.load()


@pytest.mark.parametrize("document,field,value,message", [
    ("summary.json", "status", "FAILED", "incomplete or unverified"),
    ("reading.json", "status", "FAILED", "incomplete or unverified"),
    ("process-exit.json", "exit_code", 1, "zero process exit"),
    ("process-exit.json", "exit_code", False, "zero process exit"),
    ("launch-manifest.json", "acceptance", "rejected", "accepted source/direction"),
    ("launch-manifest.json", "command_sha256", "0" * 64, "command binding differs"),
])
def test_completion_and_accepted_zero_exit_required(fixture, document, field, value, message):
    fixture.docs[document][field] = value
    fixture.rebind()
    with pytest.raises(ValueError, match=message):
        fixture.load()


def test_reader_hash_and_counts_are_independently_bound(fixture):
    fixture.docs["reading.json"]["actual"]["native_steps"] += 1
    fixture.rebind()
    with pytest.raises(ValueError, match="reader count binding"):
        fixture.load()
    fixture.docs["reading.json"]["actual"]["native_steps"] -= 1
    fixture.rebind()
    fixture.docs["reading.json"]["summary"]["sha256"] = "0" * 64
    path = fixture.root / "reading.json"
    path.write_text(json.dumps(fixture.docs["reading.json"]))
    fixture.binding["files"]["reading.json"] = file_record(path)
    with pytest.raises(ValueError, match="reader summary hash/path"):
        fixture.load()


def test_fixture_permission_cannot_bypass_production_binding(fixture):
    with pytest.raises(ValueError, match="override forbidden"):
        fixture.load(permit_fixture=False)
    fixture.binding["launch_sha"] = retained.BINDING["launch_sha"]
    with pytest.raises(ValueError, match="override forbidden"):
        fixture.load()


@pytest.mark.parametrize("production_input", ["scientific", "old_frozen", "new_frozen"])
def test_fixture_permission_rejects_production_inputs(fixture, production_input):
    protocol = fixture.new
    if production_input == "scientific":
        fixture.batch["scientific_invocation"] = True
    elif production_input == "old_frozen":
        fixture.batch["protocol"] = contract.FROZEN.to_dict()
    else:
        protocol = contract.FROZEN
    fixture.rebind()
    with pytest.raises(ValueError, match="cannot reuse production/scientific inputs"):
        fixture.load(protocol=protocol)
