"""Direct stdlib-only A05 acceptance; two inert pdb children, never pytest."""

import dataclasses
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


REPO = Path(__file__).resolve().parents[5]
DIRECTION = "finite_resource_relational_inductive_efficiency"
HELPER = REPO / "experiments/candidates" / DIRECTION / "r09_first_exception_a05/capture.py"
INPUT = REPO / "docs/research/candidates" / DIRECTION / "FRRIE_R09_FIRST_EXCEPTION_A05_PDB_COMMANDS_20260907.txt"


def main():
    started = time.monotonic()
    spec = importlib.util.spec_from_file_location("a05_inert_capture", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    calls = []

    class Untouchable:
        def __iter__(self):
            calls.append("iter")
            raise AssertionError("unexpected container iterated")

        def __next__(self):
            calls.append("next")
            raise AssertionError("existing iterator advanced")

        def __repr__(self):
            calls.append("repr")
            raise AssertionError("unexpected object rendered")

        __str__ = __repr__

    unusual = Untouchable()
    record, ordinary = helper.field_table(unusual)
    assert ordinary is False and record["status"] == "unexpected_container_not_iterated"
    assert helper.reference(unusual)["id"] == id(unusual)
    assert helper.primitive(unusual)["status"] == "unexpected_type_not_rendered"
    assert calls == []
    assert helper.primitive("x" * 300)["value"] == "x" * 256
    assert helper.primitive("x" * 300)["truncated"] is True
    assert helper.primitive(1 << 10000)["truncated"] is True
    oversized, ordinary = helper.field_table({str(i): unusual for i in range(20)})
    assert ordinary is False and oversized["truncated"] is True
    assert len(oversized["entries"]) == 14 and calls == []
    existing = iter({"one": 1}.values())
    helper.reference(existing)
    assert next(existing) == 1

    def deep_error(depth):
        if depth:
            return deep_error(depth - 1)
        raise ValueError("bounded traceback fixture")

    try:
        deep_error(35)
    except ValueError as error:
        bounded = helper.observe(error)
    assert len(bounded["frames"]) == 32 and bounded["frames_truncated"] is True
    assert bounded["capture_complete"] is False

    # Compile synthetic frame identities without importing a research package.
    # The inner generator raises the same builtin TypeError on an ordinary Field.
    dataclass_source = '''
def fields(class_or_instance):
    fields = class_or_instance.__dataclass_fields__
    return tuple(f for f in fields.values() for unused in f)
def asdict(obj):
    return bridge_one(obj)
def bridge_one(obj):
    return bridge_two(obj)
def bridge_two(obj):
    return fields(obj)
'''
    address_source = '''
@dataclass(frozen=True, slots=True)
class SemanticRNGAddress:
    seed_block: str
    purpose: str
    roster: int
    update: int
    episode: int
    basin: object
    event_ordinal: object
    slot: int
    public_role: int
    role_local_index: int
    sender: int
    receiver: int
    kind: str
    draw: int
    def canonical_bytes(self):
        return asdict(self)
'''
    execute_source = '''
def execute():
    number, update, paired_updates = 7, 6, 6
    adam = {"PHY_TRUST": 6, "EDGE_FLEX": 6}
    backward = {"PHY_TRUST": 6, "EDGE_FLEX": 6}
    training_slots = {"PHY_TRUST": 29568, "EDGE_FLEX": 29568}
    address = SemanticRNGAddress(
        "FRRIE-B09-CONTACT-BLOCK-003", "TRAIN", 15, 7, 2,
        None, None, 3, 1, 0, 5, 7, "uplink_uniform", 0,
    )
    return address.canonical_bytes()
'''
    prefix = "experiments.candidates." + DIRECTION
    target = (
        "__import__('pathlib').Path(__import__('os').environ['A05_VISITS']).open('a').write('body\\n')\n"
        "import dataclasses, sys, types\n"
        "dc = {'__name__': 'dataclasses'}\n"
        f"exec(compile({dataclass_source!r}, dataclasses.__file__, 'exec'), dc)\n"
        f"address = types.ModuleType({prefix + '.rng'!r})\n"
        "sys.modules[address.__name__] = address\n"
        "address.__dict__.update(dataclass=dataclasses.dataclass, asdict=dc['asdict'])\n"
        f"exec(compile({address_source!r}, '/inert/experiments/candidates/{DIRECTION}/rng.py', 'exec'), address.__dict__)\n"
        f"run = {{'__name__': {prefix + '.b01_contact_r02.experiment'!r}, 'SemanticRNGAddress': address.SemanticRNGAddress}}\n"
        f"exec(compile({execute_source!r}, '/inert/experiments/candidates/{DIRECTION}/b01_contact_r02/experiment.py', 'exec'), run)\n"
        "run['execute']()\n"
    )
    normal = (
        "__import__('pathlib').Path(__import__('os').environ['A05_VISITS']).open('a').write('body\\n')\n"
        "raise SystemExit(0)\n"
    )
    parent = REPO / "temp/directions" / DIRECTION / "test"
    parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="a05-inert-", dir=parent))
    receipts = []
    for name, program in (("target", target), ("normal", normal)):
        case = root / name
        case.mkdir()
        (case / "fixture_target.py").write_text(program, encoding="utf-8")
        environment = dict(os.environ)
        environment.update(
            FRRIE_A05_HELPER=str(HELPER), FRRIE_A05_OUTPUT=str(case / "out"),
            A05_VISITS=str(case / "visits.txt"),
        )
        command = [sys.executable, "-m", "pdb", "-c", "continue", "-m", "fixture_target"]
        remaining = 25 - (time.monotonic() - started)
        assert remaining > 0, "whole fixture budget exhausted"
        child_started = time.monotonic()
        run = subprocess.run(
            command, cwd=case, env=environment, input=INPUT.read_bytes(),
            capture_output=True, timeout=min(10, remaining),
        )
        elapsed = time.monotonic() - child_started
        (case / "stdout.txt").write_bytes(run.stdout)
        (case / "stderr.txt").write_bytes(run.stderr)
        assert run.returncode == 0, run.stderr.decode()
        assert (case / "visits.txt").read_text() == "body\n", "second module-body traversal"
        assert run.stdout.count(b"A05_SUMMARY_WRITTEN") == 1
        value = json.loads((case / "out/summary.json").read_text())
        if name == "target":
            assert b"TypeError: 'Field' object is not iterable" in run.stderr
            assert b"Post mortem debugger finished" in run.stdout
            assert value["observation"] == "post_mortem"
            assert value["original_exception"]["message"]["value"] == "'Field' object is not iterable"
            assert value["capture_complete"] is True, value
            assert all(value["structure_checks"].values()), value["structure_checks"]
            assert value["components"]["execute"]["number"]["value"] == 7
            assert value["components"]["execute"]["paired_updates"]["value"] == 6
            assert len(value["components"]["address"]["coordinates"]) == 14
            assert value["components"]["address"]["coordinates"]["receiver"]["value"] == 7
            assert value["components"]["generator"]["iterator"]["type_name"]["value"] == "dict_valueiterator"
        else:
            assert b"Exit status: 0" in run.stdout
            assert value["observation"] == "no_active_exception_at_entry_prompt"
            assert value["original_exception"] is None
        receipts.append({
            "case": name, "argv": command, "cwd": str(case), "returncode": run.returncode,
            "wall_seconds": elapsed, "body_traversals": 1, "summary_writes": 1,
            "capture_complete": value["capture_complete"],
        })
    elapsed = time.monotonic() - started
    assert elapsed <= 25
    receipt = {
        "passed": True, "python": sys.version, "executable": sys.executable,
        "wall_seconds": elapsed, "program_subprocesses": 2,
        "unexpected_object_operations": calls, "cases": receipts,
    }
    (root / "acceptance.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "receipt": str(root / 'acceptance.json'), **receipt}, indent=2))


if __name__ == "__main__":
    main()
