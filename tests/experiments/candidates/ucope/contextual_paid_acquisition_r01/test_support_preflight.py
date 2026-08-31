from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
import gzip
import json

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01 import contract
from experiments.candidates.ucope.contextual_paid_acquisition_r01.schema import canonical_bytes
from experiments.candidates.ucope.contextual_paid_acquisition_r01.support import (
    SupportError,
    build_fixed_behavior_plan,
    materialize_fixed_behavior_plan,
    preflight_support,
    validate_support,
)


def _context(link="LINKED"):
    return {"link": link, "reliability": Fraction(17, 20), "total_cost": Fraction(9, 100)}


def test_production_behavior_plan_is_exact_and_schedule_is_context_independent():
    manifest = contract.default_manifest()
    plans = [build_fixed_behavior_plan(contract.SEED_SLOTS[0], cell, manifest) for cell in contract.contexts()]
    entries = plans[0].entries
    assert len(entries) == 20_480
    assert sum(item.root_action == "PROBE" for item in entries) == 10_240
    assert Counter(item.period for item in entries if item.root_action == "PROBE") == {k: 2_048 for k in contract.K_TRAIN}
    assert Counter(item.period for item in entries if item.root_action == "IMMEDIATE") == {k: 2_048 for k in contract.K_TRAIN}
    reference = canonical_bytes([asdict(item) for item in entries])
    assert all(canonical_bytes([asdict(item) for item in plan.entries]) == reference for plan in plans)
    assert {plan.context_id for plan in plans} == set(contract.default_manifest()["context_ids"])


@pytest.mark.parametrize("link", ["LINKED", "SEVERED"])
def test_test_only_materialization_preserves_balanced_action_strata(link):
    manifest = contract.default_manifest(contract.TEST_ONLY_MODE, 640)
    plan = build_fixed_behavior_plan(contract.SEED_SLOTS[0], _context(link), manifest)
    records = materialize_fixed_behavior_plan(plan, _context(link))
    assert len(records) == 640
    for action in ("PROBE", "IMMEDIATE"):
        for period in contract.K_TRAIN:
            selected = [r for r in records if r.root_action == action and r.period == period]
            assert len(selected) == 64
            assert Counter(r.regime for r in selected) == {"SHORT": 32, "LONG": 32}
            if link == "SEVERED":
                assert Counter((r.regime, r.displayed_regime) for r in selected) == {
                    ("SHORT", "SHORT"): 16, ("SHORT", "LONG"): 16,
                    ("LONG", "SHORT"): 16, ("LONG", "LONG"): 16,
                }
    probe_counts = Counter(r.displayed_short_count for r in records if r.root_action == "PROBE")
    assert set(probe_counts) == set(range(7))
    assert min(probe_counts.values()) >= 8


def test_test_only_preflight_is_complete_bound_strict_and_nonresult(tmp_path):
    manifest = contract.default_manifest(contract.TEST_ONLY_MODE, 640)
    artifact_path = preflight_support(manifest, tmp_path / "preflight")
    value = validate_support(artifact_path, manifest)
    expected = {f"{seed}|{cell}" for seed in contract.SEED_SLOTS for cell in manifest["context_ids"]}
    assert value["mode"] == "TEST_ONLY"
    assert value["episodes_per_context"] == 640
    assert value["optimizer_updates"] == 0
    assert value["complete"] is True
    assert value["contract_spec"]["support"]["displayed_count_floor"] == 1
    assert set(value["materialized_files"]) == set(value["seed_context_counts"]) == expected
    observed_manifest = {name: value[name] for name in (
        "schema_version", "contract_id", "mode", "seed_slots", "episodes_per_context", "context_ids", "contract_spec",
    )}
    assert observed_manifest == manifest
    records = list(value["materialized_files"].values())
    assert all(set(record) == {"filename", "rows"} and record["rows"] == 640 for record in records)
    assert sorted(record["filename"] for record in records) == [
        f"cell-{seed_index:02d}-{cell_index:02d}.jsonl.gz" for seed_index in range(10) for cell_index in range(8)
    ]
    forbidden = {
        "value", "values", "contrast", "contrasts", "conclusion", "acquisition_pass", "competence_pass",
        "contract_spec_digest", "manifest_digest", "tape_digest", "dataset_digest", "support_digest",
        "artifact_digest", "state_digest", "checkpoint_digests", "rng_contract_digest",
    }
    assert forbidden.isdisjoint(value)

    missing = deepcopy(value)
    missing["materialized_files"].pop(next(iter(expected)))
    with pytest.raises(SupportError):
        validate_support(missing, manifest)
    extra = deepcopy(value)
    extra["seed_context_counts"]["forged"] = next(iter(extra["seed_context_counts"].values()))
    with pytest.raises(SupportError):
        validate_support(extra, manifest)

    extra_top = deepcopy(value)
    extra_top["unexpected"] = None
    with pytest.raises(SupportError):
        validate_support(extra_top, manifest)

    materialized = artifact_path.parent / "materialized"
    extra_file = materialized / "unregistered.jsonl.gz"
    extra_file.write_bytes(b"unregistered")
    with pytest.raises(SupportError):
        validate_support(artifact_path, manifest)
    extra_file.unlink()

    swapped = json.loads(artifact_path.read_text(encoding="utf-8"))
    keys = sorted(swapped["materialized_files"])
    swapped["materialized_files"][keys[0]], swapped["materialized_files"][keys[1]] = swapped["materialized_files"][keys[1]], swapped["materialized_files"][keys[0]]
    forged_path = artifact_path.parent / "forged-support.json"
    forged_path.write_bytes(canonical_bytes(swapped))
    with pytest.raises(SupportError):
        validate_support(forged_path, manifest)

    file_record = next(iter(value["materialized_files"].values()))
    bound_file = materialized / file_record["filename"]
    with gzip.open(bound_file, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    rows[0]["period"] = 2
    with gzip.open(bound_file, "wt", encoding="utf-8") as stream:
        for row in rows:
            stream.write(canonical_bytes(row).decode("ascii") + "\n")
    with pytest.raises(SupportError):
        validate_support(artifact_path, manifest)
