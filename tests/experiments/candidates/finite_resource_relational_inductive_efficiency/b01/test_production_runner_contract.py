from __future__ import annotations

import inspect
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract as contract_module
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.constants import ROOT_LABELS
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError, manifest_template,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.production_runner import (
    construct_formal_production_plan,
)


def _git(monkeypatch, *, head: str, dirty: str = "") -> None:
    def fake_run(argv, *, cwd, check, capture_output, text, timeout):
        assert argv[0] == "git" and check is False and capture_output and text and timeout == 30
        assert Path(cwd).is_absolute()
        if argv[1:3] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(returncode=0, stdout=head + "\n", stderr="")
        assert argv[1:4] == ["status", "--porcelain=v1", "--untracked-files=all"]
        return SimpleNamespace(returncode=0, stdout=dirty, stderr="")

    monkeypatch.setattr(contract_module.subprocess, "run", fake_run)


def _extension(tmp_path: Path, initial: dict) -> dict:
    parent = (tmp_path / "initial-manifest.json").resolve()
    parent.write_text(json.dumps(initial), encoding="utf-8")
    return manifest_template(
        seed_packet_path=initial["seed_packet"]["path"], phase="EXTENSION_004_005",
        roots={
            name: str((tmp_path / "extension-run" / name).resolve())
            for name in ("output", "checkpoint", "scratch")
        },
        compute=initial["compute"], code_revision=initial["code_revision"],
        parent_initial={"locator": str(parent), "manifest_contract": initial},
    )


def test_public_seam_has_one_manifest_argument_and_initial_plan_is_pure(
    monkeypatch, tmp_path, b01_manifest,
):
    assert list(inspect.signature(construct_formal_production_plan).parameters) == ["manifest"]
    _git(monkeypatch, head=b01_manifest["code_revision"])
    manifest_before = deepcopy(b01_manifest)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    plan = construct_formal_production_plan(b01_manifest)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert before == after
    assert b01_manifest == manifest_before
    assert plan["schema"] == "FRRIE_B01_FORMAL_PRODUCTION_PLAN_V1"
    assert plan["phase"] == "INITIAL_001_003"
    assert plan["seed_order"] == list(ROOT_LABELS[:3])
    assert plan["capacity"] == 4 and plan["planned_worker_count"] == 3
    assert plan["launch_capable"] is False
    assert plan["production_token_minted"] is False
    assert plan["result_bearing"] is False and plan["effect_count"] == 0
    assert plan["source_gate"]["actual_head"] == b01_manifest["code_revision"]
    assert plan["residual_downstream_blockers"]

    all_locators = []
    roots = {name: Path(value).resolve() for name, value in b01_manifest["roots"].items()}
    run_parent = roots["output"].parent
    admission_namespace = run_parent.with_name(run_parent.name + ".FRRIE_B01_ADMISSION")
    assert plan["admission_namespace"] == {
        "path": str(admission_namespace),
        "created_by_plan": False,
        "later_lifecycle_owns_cleanup_or_archive": True,
        "ownership_scope": "ONLY_THIS_EXACT_ADMISSION_NAMESPACE",
    }
    assert admission_namespace.parent == run_parent.parent
    assert not admission_namespace.is_relative_to(run_parent)
    assert not admission_namespace.exists()
    for seed, task in zip(plan["seed_order"], plan["workers"]):
        assert task["seed_label"] == seed
        assert task["planned_identity"] == {
            "label": f"FRRIE-B01-FORMAL-{b01_manifest['phase']}-{seed}",
            "authoritative": False, "actual_invocation_id": None,
            "future_worker_must_mint_and_bind_actual_id": True,
        }
        assert task["worker_local_fresh_admission_required"] is True
        assert task["fresh_admission_order_contract"] == {
            "sequence": [
                "WORKER_START", "FRESH_ADMIT_MEMORY_RECEIPT",
                "NO_INTERVENING_EFFECT", "FIRST_FUTURE_RUNTIME_OR_EFFECT",
            ],
            "precedes": [
                "NATIVE_BUILD_LOAD", "RNG_MASTER_CREATE",
                "PAIRED_MODEL_OPTIMIZER_CREATE_OR_RESTORE", "ROOT_OR_RESULT_CREATE",
                "CHECKPOINT_WRITE_OR_RESTORE",
            ],
        }
        locators = task["locators"]
        assert Path(locators["output"]).is_relative_to(roots["output"])
        assert Path(locators["checkpoint"]).is_relative_to(roots["checkpoint"])
        assert Path(locators["scratch"]).is_relative_to(roots["scratch"])
        admission = Path(locators["planned_future_admission_receipt"])
        assert admission == admission_namespace / f"{seed}.json"
        assert not admission.is_relative_to(run_parent)
        assert all(not admission.is_relative_to(root) for root in roots.values())
        assert Path(locators["creating"]).is_relative_to(roots["output"])
        assert Path(locators["incomplete"]).is_relative_to(roots["output"])
        assert Path(locators["quarantine"]).is_relative_to(roots["output"])
        assert all(not Path(value).exists() for value in locators.values())
        all_locators.extend(Path(value) for value in locators.values())
    assert len(all_locators) == len(set(all_locators))


def test_extension_plan_is_exact_004_005_in_manifest_order(monkeypatch, tmp_path, b01_manifest):
    extension = _extension(tmp_path, b01_manifest)
    _git(monkeypatch, head=extension["code_revision"])
    plan = construct_formal_production_plan(extension)
    assert plan["phase"] == "EXTENSION_004_005"
    assert plan["seed_order"] == list(ROOT_LABELS[3:])
    assert [row["seed_label"] for row in plan["workers"]] == list(ROOT_LABELS[3:])
    assert plan["capacity"] == 4 and plan["planned_worker_count"] == 2


def test_admission_argv_is_five_literal_tokens_even_with_spaces_and_ampersand(
    monkeypatch, tmp_path, b01_manifest,
):
    manifest = deepcopy(b01_manifest)
    run_parent = (tmp_path / "formal run & literal spaces").resolve()
    manifest["roots"] = {
        name: str((run_parent / name).resolve())
        for name in ("output", "checkpoint", "scratch")
    }
    _git(monkeypatch, head=manifest["code_revision"])
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    plan = construct_formal_production_plan(manifest)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert before == after
    repository = Path(plan["source_gate"]["repository"])
    for worker in plan["workers"]:
        assert "fresh_admission_command" not in worker
        argv = worker["fresh_admission_argv"]
        assert len(argv) == 5
        assert argv == [
            str(Path(sys.executable).resolve()),
            str((repository / "scripts" / "hmasd_resource_preflight.py").resolve()),
            "admit-memory", "--out",
            worker["locators"]["planned_future_admission_receipt"],
        ]
        assert argv[-1].count("&") == 1 and " " in argv[-1]
        assert worker["future_execution_requires_shell_false"] is True


@pytest.mark.parametrize("failure", ["wrong_head", "dirty"])
def test_actual_source_gate_rejects_wrong_head_or_scoped_dirty(
    monkeypatch, b01_manifest, failure,
):
    _git(
        monkeypatch,
        head=("2" * 40 if failure == "wrong_head" else b01_manifest["code_revision"]),
        dirty=("?? experiments/candidates/finite_resource_relational_inductive_efficiency/x\n"
               if failure == "dirty" else ""),
    )
    with pytest.raises(B01ContractError, match=(
        "BLOCKED_SOURCE_REVISION" if failure == "wrong_head" else "BLOCKED_UNCOMMITTED"
    )):
        construct_formal_production_plan(b01_manifest)


def test_manifest_mutation_and_preexisting_derived_locator_reject(
    monkeypatch, b01_manifest,
):
    _git(monkeypatch, head=b01_manifest["code_revision"])
    changed = deepcopy(b01_manifest)
    changed["execution_labels"] = list(reversed(changed["execution_labels"]))
    with pytest.raises(B01ContractError):
        construct_formal_production_plan(changed)

    occupied = Path(b01_manifest["roots"]["output"]) / b01_manifest["execution_labels"][0]
    occupied.mkdir(parents=True)
    with pytest.raises(B01ContractError, match="not fresh"):
        construct_formal_production_plan(b01_manifest)


def test_preexisting_admission_namespace_or_exact_receipt_rejects(
    monkeypatch, tmp_path, b01_manifest,
):
    _git(monkeypatch, head=b01_manifest["code_revision"])
    run_parent = Path(b01_manifest["roots"]["output"]).parent
    namespace = run_parent.with_name(run_parent.name + ".FRRIE_B01_ADMISSION")
    namespace.mkdir()
    with pytest.raises(B01ContractError, match="admission namespace"):
        construct_formal_production_plan(b01_manifest)
    namespace.rmdir()

    namespace.mkdir()
    receipt = namespace / f"{b01_manifest['execution_labels'][0]}.json"
    receipt.write_text("occupied", encoding="utf-8")
    with pytest.raises(B01ContractError, match="admission receipt"):
        construct_formal_production_plan(b01_manifest)


@pytest.mark.parametrize("scope", ["anchor", "repository", "repository_ancestor"])
def test_unsafe_broad_run_parent_rejects(monkeypatch, b01_manifest, scope):
    _git(monkeypatch, head=b01_manifest["code_revision"])
    repository = Path(contract_module.__file__).resolve().parents[4]
    run_parent = {
        "anchor": Path(repository.anchor),
        "repository": repository,
        "repository_ancestor": repository.parent,
    }[scope]
    manifest = deepcopy(b01_manifest)
    manifest["roots"] = {
        name: str((run_parent / name).resolve())
        for name in ("output", "checkpoint", "scratch")
    }
    with pytest.raises(B01ContractError, match="unsafe broad run parent"):
        construct_formal_production_plan(manifest)
