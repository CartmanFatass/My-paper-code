from copy import deepcopy

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01 import contract
from experiments.candidates.ucope.contextual_paid_acquisition_r01.checkpoint import (
    checkpoint_payload,
    load_checkpoint,
    save_checkpoint,
    validate_checkpoint_payload,
    validate_cold_resume,
)
from experiments.candidates.ucope.contextual_paid_acquisition_r01.model import build_shared_model
from experiments.candidates.ucope.contextual_paid_acquisition_r01.rng import uint64


torch = pytest.importorskip("torch")

FORBIDDEN_FIELDS = {
    "contract_spec_digest", "manifest_digest", "tape_digest", "dataset_digest", "support_digest",
    "artifact_digest", "state_digest", "checkpoint_digests", "rng_contract_digest",
}


def _optimizer(parameters):
    return torch.optim.AdamW(parameters, lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-4)


def _support_record(manifest):
    size = manifest["episodes_per_context"]
    unit = size // 10
    strata = [f"{action}:{period}" for action in ("PROBE", "IMMEDIATE") for period in contract.K_TRAIN]
    base, remainder = divmod(5 * unit, 7)
    materialized_files = {}
    seed_context_counts = {}
    for seed_index, seed in enumerate(contract.SEED_SLOTS):
        for cell_index, cell in enumerate(manifest["context_ids"]):
            key = f"{seed}|{cell}"
            linked = cell.startswith("LINKED-")
            materialized_files[key] = {"filename": f"cell-{seed_index:02d}-{cell_index:02d}.jsonl.gz", "rows": size}
            seed_context_counts[key] = {
                "episodes": size,
                "root": {"PROBE": 5 * unit, **{f"IMMEDIATE:{k}": unit for k in contract.K_TRAIN}},
                "tail_conditional_probe": {str(k): unit for k in contract.K_TRAIN},
                "regimes": {"LONG": size // 2, "SHORT": size // 2},
                "displayed_short_count": {str(n): base + (n < remainder) for n in range(7)},
                "action_stratified_regimes": {name: {"LONG": unit // 2, "SHORT": unit // 2} for name in strata},
                "actual_display_joint": {
                    name: ({"LONG|LONG": unit // 2, "SHORT|SHORT": unit // 2} if linked else {
                        "LONG|LONG": unit // 4, "LONG|SHORT": unit // 4,
                        "SHORT|LONG": unit // 4, "SHORT|SHORT": unit // 4,
                    }) for name in strata
                },
            }
    return {
        "schema_version": manifest["schema_version"], "contract_id": manifest["contract_id"],
        "mode": manifest["mode"], "episodes_per_context": manifest["episodes_per_context"],
        "seed_slots": list(manifest["seed_slots"]), "context_ids": list(manifest["context_ids"]),
        "contract_spec": deepcopy(manifest["contract_spec"]), "materialized_files": materialized_files,
        "seed_context_counts": seed_context_counts, "complete": True, "optimizer_updates": 0,
    }


def _untrained_payload(seed=None):
    seed = seed or contract.SEED_SLOTS[0]
    manifest = contract.default_manifest(contract.TEST_ONLY_MODE, 640)
    model = build_shared_model(seed)
    optimizer = _optimizer(model.parameters())
    payload = checkpoint_payload(
        model, optimizer, seed_slot=seed, completed_batches=0, optimizer_updates=0, total_batches=20,
        mode=contract.TEST_ONLY_MODE, contract_spec=manifest["contract_spec"], support_record=_support_record(manifest),
    )
    return model, optimizer, payload


def _assert_recursive_equal(left, right):
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor) and torch.equal(left, right)
    elif isinstance(left, dict):
        assert isinstance(right, dict) and set(left) == set(right)
        for key in left:
            _assert_recursive_equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert type(left) is type(right) and len(left) == len(right)
        for first, second in zip(left, right):
            _assert_recursive_equal(first, second)
    else:
        assert left == right


def test_zero_step_checkpoint_atomic_roundtrip_and_cold_resume(tmp_path):
    _, _, payload = _untrained_payload()
    assert set(payload) == {
        "format", "schema_version", "contract_id", "seed_slot", "feature_names", "train_periods",
        "model_spec", "optimizer_spec", "completed_batches", "total_batches", "optimizer_updates", "mode",
        "contract_spec", "support_record", "rng_contract", "model_state", "optimizer_state",
    }
    assert FORBIDDEN_FIELDS.isdisjoint(payload)
    assert payload["completed_batches"] == payload["optimizer_updates"] == 0
    assert payload["total_batches"] == 20
    assert payload["mode"] == payload["contract_spec"]["mode"] == payload["support_record"]["mode"] == "TEST_ONLY"
    path = save_checkpoint(tmp_path / "checkpoint.pt", payload)
    assert path.is_file() and not list(tmp_path.glob("*.tmp"))
    restored = load_checkpoint(path)
    _assert_recursive_equal(restored, payload)
    resumed = validate_cold_resume(path, build_shared_model, _optimizer)
    _assert_recursive_equal(resumed["model_state"], payload["model_state"])
    _assert_recursive_equal(resumed["optimizer_state"], payload["optimizer_state"])


def test_checkpoint_rejects_extra_or_context_specific_model_state():
    _, _, payload = _untrained_payload()
    extra = deepcopy(payload)
    extra["unexpected"] = None
    with pytest.raises(ValueError):
        validate_checkpoint_payload(extra)
    context_state = deepcopy(payload)
    context_state["model_state"]["context.0.weight"] = torch.zeros((1, 1), dtype=torch.float32)
    with pytest.raises(ValueError):
        validate_checkpoint_payload(context_state)


@pytest.mark.parametrize("mutation", [
    lambda value: value.update(completed_batches=True), lambda value: value.update(optimizer_updates=0.0),
    lambda value: value.update(total_batches=-1), lambda value: value.update(mode="PRODUCTION-ish"),
    lambda value: value["contract_spec"].update(mode="PRODUCTION"),
    lambda value: value["support_record"].update(mode="PRODUCTION"),
    lambda value: value["support_record"].update(complete=False),
    lambda value: value["support_record"].update(optimizer_updates=1),
])
def test_checkpoint_structure_and_progress_fail_closed(mutation):
    _, _, payload = _untrained_payload()
    mutation(payload)
    with pytest.raises(ValueError):
        validate_checkpoint_payload(payload)


@pytest.mark.parametrize("kind", ["shape", "dtype", "nonfinite"])
def test_checkpoint_model_tensors_are_strict_fp32_finite_and_exact_shape(kind):
    _, _, payload = _untrained_payload()
    name = "root.layers.0.weight"
    if kind == "shape":
        payload["model_state"][name] = torch.zeros((1, 1), dtype=torch.float32)
    elif kind == "dtype":
        payload["model_state"][name] = payload["model_state"][name].to(torch.float64)
    else:
        payload["model_state"][name][0, 0] = float("nan")
    with pytest.raises(ValueError):
        validate_checkpoint_payload(payload)


def test_fixed_counter_and_global_torch_rng_are_unchanged_by_model_checkpoint_construction():
    counter_before = uint64("glorot", "sentinel", counter=7)
    torch.manual_seed(123456)
    state_before = torch.random.get_rng_state().clone()
    _untrained_payload()
    assert torch.equal(torch.random.get_rng_state(), state_before)
    assert uint64("glorot", "sentinel", counter=7) == counter_before


def test_checkpoint_payload_rejects_coercible_counters_before_serialization():
    manifest = contract.default_manifest(contract.TEST_ONLY_MODE, 640)
    model = build_shared_model(contract.SEED_SLOTS[0])
    optimizer = _optimizer(model.parameters())
    for bad in (True, 0.0, "0", -1):
        with pytest.raises(ValueError):
            checkpoint_payload(
                model, optimizer, seed_slot=contract.SEED_SLOTS[0], completed_batches=bad,
                optimizer_updates=0, total_batches=20, mode=contract.TEST_ONLY_MODE,
                contract_spec=manifest["contract_spec"], support_record=_support_record(manifest),
            )


@pytest.mark.parametrize("field,bad", [
    ("maximize", True), ("foreach", False), ("fused", False),
    ("capturable", True), ("differentiable", True), ("decoupled_weight_decay", False),
])
def test_checkpoint_freezes_all_algorithmic_adamw_group_settings(field, bad):
    _, _, payload = _untrained_payload()
    payload["optimizer_state"]["param_groups"][0][field] = bad
    with pytest.raises(ValueError):
        validate_checkpoint_payload(payload)


def _synthetic_updated_payload():
    _, _, payload = _untrained_payload()
    payload["completed_batches"] = payload["optimizer_updates"] = 1
    states = {}
    for index, tensor in enumerate(payload["model_state"].values()):
        states[index] = {
            "step": torch.tensor(1.0, dtype=torch.float32),
            "exp_avg": torch.zeros_like(tensor),
            "exp_avg_sq": torch.zeros_like(tensor),
        }
    payload["optimizer_state"]["state"] = states
    return payload


def test_checkpoint_optimizer_steps_and_moments_match_progress_and_parameter_order():
    payload = _synthetic_updated_payload()
    validate_checkpoint_payload(payload)
    for mutation in ("wrong_step", "nonfinite_step", "wrong_shape", "duplicate_param"):
        changed = deepcopy(payload)
        if mutation == "wrong_step":
            changed["optimizer_state"]["state"][0]["step"] = torch.tensor(0.0)
        elif mutation == "nonfinite_step":
            changed["optimizer_state"]["state"][0]["step"] = torch.tensor(float("nan"))
        elif mutation == "wrong_shape":
            changed["optimizer_state"]["state"][0]["exp_avg"] = torch.zeros((1,), dtype=torch.float32)
        else:
            changed["optimizer_state"]["param_groups"][0]["params"][-1] = 0
        with pytest.raises(ValueError):
            validate_checkpoint_payload(changed)
