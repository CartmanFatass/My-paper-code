from __future__ import annotations

import pytest
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    C1P1,
    FLEX,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    HELDOUT_CELLS,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    TBCFVModel,
    apply_affine_fixture_uniforms,
    required_affine_fixture_uniforms,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b01.study import (
    IDENTITY as B01_IDENTITY,
    SEED_KEY_ASCII as B01_SEED_KEY_ASCII,
    block_digest_hex,
    seed_root_key,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b02.study import (
    IDENTITY,
    INIT_SOURCE,
    OBJECT_ID,
    REFERENCE_SOURCE,
    SEED,
    SEED_KEY_ASCII,
    STEP_LAW,
    SELECTION_HISTORY,
    apply_b02_block_update,
    b02_allocations,
    b02_configuration,
    execute_b02_training_update,
    fixed_norm_sgd_step,
    flat_parameters,
    initialize_b01_models,
    load_and_validate_b02_control_summary,
    make_b02_semantic_rng,
    native_available,
    publish_b02_primary,
    publish_b02_primary_or_error,
    se_of_mean_of_independent_ses,
    validate_control_summary,
)


ROOT_KEY_HEX = "fd3cd5cf0f085e880a424f7a546017a62d300676e385e1174676b9f4c14e5093"
BLOCK_DIGEST_HEX = "82593ad701533212112f1e29d22f3d0b701fd8360b88d9bfcb61ac565f6b2210"
B01_ROOT_KEY_HEX = "fb5f7dce9ab4cff9cc898c91aa49721936b84a16f202e51bc705504dd1d94c34"
B01_BLOCK_DIGEST_HEX = "a67b014451fa8d614c191e82f2e20ded2d8f77f21098dcb52d2744e64d596048"


def test_seed_and_block_digest_are_reproducible_and_distinct_from_b01() -> None:
    root = seed_root_key(SEED_KEY_ASCII)
    assert root.hex() == ROOT_KEY_HEX
    assert IDENTITY == "RCLE-TBCFV-B02-NORM-0p02"
    assert OBJECT_ID == IDENTITY
    assert SEED == 18
    assert SEED_KEY_ASCII == "RCLE-TBCFV-B02-NORM-0p02/seed/18"
    assert block_digest_hex(root, IDENTITY, 0) == BLOCK_DIGEST_HEX
    assert seed_root_key(SEED_KEY_ASCII) == root
    b01_root = seed_root_key(B01_SEED_KEY_ASCII)
    assert b01_root.hex() == B01_ROOT_KEY_HEX
    assert block_digest_hex(b01_root, B01_IDENTITY, 0) == B01_BLOCK_DIGEST_HEX
    assert root.hex() != b01_root.hex()
    assert BLOCK_DIGEST_HEX != B01_BLOCK_DIGEST_HEX


def test_fixed_norm_sgd_step_prescribed_and_measured_norms() -> None:
    model = TBCFVModel()
    first = next(model.parameters())
    first.grad = torch.arange(
        1, first.numel() + 1, dtype=torch.float64
    ).reshape_as(first)
    before = flat_parameters(model).clone()
    step = fixed_norm_sgd_step(model, 0.02)
    delta = flat_parameters(model) - before
    applied = float(torch.linalg.vector_norm(delta).item())
    assert applied == pytest.approx(0.02, abs=1.0e-9)
    assert step.audit.parameter_delta_norm == 0.02
    assert step.audit.nonzero is True
    assert step.measured_parameter_delta_norm == pytest.approx(0.02, abs=1.0e-9)

    zero_model = TBCFVModel()
    zero_before = flat_parameters(zero_model).clone()
    zero_step = fixed_norm_sgd_step(zero_model, 0.02)
    assert zero_step.audit.nonzero is False
    assert zero_step.audit.parameter_delta_norm == 0.0
    assert zero_step.measured_parameter_delta_norm == 0.0
    assert torch.equal(flat_parameters(zero_model), zero_before)

    other = TBCFVModel()
    first_other = next(other.parameters())
    first_other.grad = torch.arange(
        1, first_other.numel() + 1, dtype=torch.float64
    ).reshape_as(first_other)
    other_before = flat_parameters(other).clone()
    other_step = fixed_norm_sgd_step(other, 0.0005)
    other_delta = float(
        torch.linalg.vector_norm(flat_parameters(other) - other_before).item()
    )
    assert other_delta == pytest.approx(0.0005, abs=1.0e-9)
    assert other_step.audit.parameter_delta_norm == 0.0005
    assert other_step.measured_parameter_delta_norm == pytest.approx(0.0005, abs=1.0e-9)


def test_apply_b02_block_update_parameters_then_baselines() -> None:
    model = TBCFVModel()
    first_parameter = next(model.parameters())
    first_parameter.grad = torch.arange(
        1, first_parameter.numel() + 1, dtype=torch.float64
    ).reshape_as(first_parameter)
    before = flat_parameters(model).clone()
    cells = torch.arange(8, dtype=torch.int64).repeat_interleave(8)
    returns = cells.to(torch.float64) + 2.0
    start_baselines = torch.arange(8, dtype=torch.float64)
    block = apply_b02_block_update(model, start_baselines, returns, cells, 0.02)
    delta = flat_parameters(model) - before
    assert block.block.event_order == ("parameter_update", "baseline_update")
    assert block.block.parameter_update.nonzero
    assert block.block.parameter_update.parameter_delta_norm == 0.02
    assert float(torch.linalg.vector_norm(delta)) == pytest.approx(0.02, abs=1.0e-9)
    assert block.measured_parameter_delta_norm == pytest.approx(0.02, abs=1.0e-9)
    expected_baselines = 0.95 * start_baselines + 0.05 * returns[::8]
    assert torch.allclose(
        block.block.updated_baselines, expected_baselines, atol=1.0e-15, rtol=0.0
    )
    assert not block.block.updated_baselines.requires_grad
    assert torch.equal(start_baselines, torch.arange(8, dtype=torch.float64))


def test_both_arms_start_identical_and_flex_finals_are_zero_trainable() -> None:
    reference = TBCFVModel()
    uniforms = {
        name: torch.full(shape, 0.5, dtype=torch.float64)
        for name, shape in required_affine_fixture_uniforms(reference).items()
    }
    apply_affine_fixture_uniforms(reference, uniforms)
    models = {}
    for arm in (C1P1, FLEX):
        model = TBCFVModel()
        model.load_state_dict(reference.state_dict())
        models[arm] = model
    assert torch.equal(flat_parameters(models[C1P1]), flat_parameters(models[FLEX]))
    for name in ("common_update_final", "agent_update_final"):
        layer = getattr(models[FLEX], name)
        assert torch.count_nonzero(layer.weight) == 0
        assert torch.count_nonzero(layer.bias) == 0
        assert layer.weight.requires_grad is True
        assert layer.bias.requires_grad is True
    base = torch.tensor(
        [[0.25, 0.0, 0.0, 0.0], [0.25, 0.0, 0.0, 0.0]], dtype=torch.float64
    )
    event = torch.zeros((2, 68), dtype=torch.float64)
    event[:, 0] = 0.5
    physical = torch.tensor(
        [[0.8, 0.2, 0.0, 0.0, 0.0], [-0.7, 0.6, 1.0, 0.0, 1.0]],
        dtype=torch.float64,
    )
    noise = torch.tensor(
        [[0.1, 0.2, 0.3, 0.4], [-0.1, -0.2, -0.3, -0.4]], dtype=torch.float64
    )
    treatment_plan, treatment_common, treatment_agent = models[C1P1].event_plan(
        C1P1, base, event, physical, noise
    )
    flex_plan, flex_common, flex_agent = models[FLEX].event_plan(
        FLEX, base, event, physical, noise
    )
    assert treatment_common is None and treatment_agent is None
    assert flex_common is not None and flex_agent is not None
    assert torch.equal(treatment_plan, flex_plan)
    with torch.no_grad():
        models[FLEX].common_update_final.weight.fill_(0.65)
        models[FLEX].agent_update_final.weight.fill_(0.45)
    unchanged_treatment, still_common, still_agent = models[C1P1].event_plan(
        C1P1, base, event, physical, noise
    )
    assert still_common is None and still_agent is None
    assert torch.equal(unchanged_treatment, treatment_plan)
    for name in ("common_update_final", "agent_update_final"):
        layer = getattr(models[C1P1], name)
        assert torch.count_nonzero(layer.weight) == 0
        assert layer.weight.requires_grad is True


def _row(
    cell: str, index: int, arm: str, tau: float, u: float, y: float
) -> dict[str, object]:
    return {
        "cell": cell,
        "index": index,
        "arm": arm,
        "tau": tau,
        "U": u,
        "F": 0.0,
        "Y": y,
    }


def test_publish_b02_primary_on_handwritten_tables() -> None:
    init_rows = []
    treatment = []
    flex = []
    primary = {
        "8_to_12.ACTIVE_CONTINUATION": (
            (10.0, 12.0),
            (14.0, 16.0),
            (0.20, 0.20),
            (0.10, 0.10),
            (0.12, 0.12),
        ),
        "12_to_8.ACTIVE_CONTINUATION": (
            (20.0, 22.0),
            (24.0, 26.0),
            (0.30, 0.30),
            (0.20, 0.20),
            (0.22, 0.22),
        ),
    }
    for cell in HELDOUT_CELLS:
        if cell in primary:
            t_tau, f_tau, i_u, t_u, f_u = primary[cell]
            for index in range(2):
                init_rows.append(_row(cell, index, "C1P1-INIT", 8.0, i_u[index], 0.9))
                treatment.append(_row(cell, index, C1P1, t_tau[index], t_u[index], 0.8))
                flex.append(_row(cell, index, FLEX, f_tau[index], f_u[index], 0.7))
        else:
            for index in range(2):
                init_rows.append(_row(cell, index, "C1P1-INIT", 28.0, 0.28, 0.6))
                treatment.append(_row(cell, index, C1P1, 30.0, 0.25, 0.5))
                flex.append(_row(cell, index, FLEX, 32.0, 0.27, 0.4))
    published = publish_b02_primary(init_rows, treatment, flex)
    paths = {row["path"]: row for row in published["active_paths"]}
    assert paths["8_to_12"]["init_U_mean"] == pytest.approx(0.20)
    assert paths["8_to_12"]["c1p1_U_mean"] == pytest.approx(0.10)
    assert paths["8_to_12"]["flex_U_mean"] == pytest.approx(0.12)
    assert paths["8_to_12"]["difference_U_flex_minus_c1p1"] == pytest.approx(0.02)
    assert paths["8_to_12"]["G_U_c1p1"] == pytest.approx(0.10)
    assert paths["8_to_12"]["G_U_flex"] == pytest.approx(0.08)
    assert paths["12_to_8"]["init_U_mean"] == pytest.approx(0.30)
    assert paths["12_to_8"]["G_U_c1p1"] == pytest.approx(0.10)
    assert paths["12_to_8"]["G_U_flex"] == pytest.approx(0.08)
    assert published["delta_U_b02"] == pytest.approx(0.02)
    assert published["G_U_c1p1"] == pytest.approx(0.10)
    assert published["G_U_flex"] == pytest.approx(0.08)
    assert published["delta_tau_b02"] == 4.0
    assert published["delta_U_b02_se"] == pytest.approx(0.0)
    assert published["delta_tau_b02_se"] == pytest.approx(0.0)
    assert published["MEI_U"] == 0.05
    assert published["MEI_tau_ticks"] == 4
    assert published["sources"] == {
        "init": INIT_SOURCE,
        "C1P1": "new:C1P1-COMMON-PERSISTENT:update200",
        "FLEX": "new:FLEX-REKEY:update200",
        "reference": REFERENCE_SOURCE,
    }
    mismatched = [dict(row) for row in init_rows]
    for row in mismatched:
        if row["cell"] == "8_to_12.ACTIVE_CONTINUATION":
            row["index"] = 99
            break
    with pytest.raises(ValueError, match="init scenario indices differ"):
        publish_b02_primary(mismatched, treatment, flex)


def test_publish_b02_standard_error_combination_on_handwritten_table() -> None:
    init_rows = []
    treatment = []
    flex = []
    path_a = "8_to_12.ACTIVE_CONTINUATION"
    path_b = "12_to_8.ACTIVE_CONTINUATION"
    for index, (t_tau, f_tau, t_u, f_u, i_u) in enumerate(
        (
            (10.0, 12.0, 0.10, 0.20, 0.30),
            (12.0, 16.0, 0.20, 0.30, 0.40),
            (14.0, 20.0, 0.30, 0.40, 0.50),
        )
    ):
        init_rows.append(_row(path_a, index, "C1P1-INIT", 8.0, i_u, 0.9))
        treatment.append(_row(path_a, index, C1P1, t_tau, t_u, 0.8))
        flex.append(_row(path_a, index, FLEX, f_tau, f_u, 0.7))
    for index, (t_tau, f_tau, t_u, f_u, i_u) in enumerate(
        ((20.0, 20.0, 0.20, 0.22, 0.30), (24.0, 26.0, 0.24, 0.28, 0.34))
    ):
        init_rows.append(_row(path_b, index, "C1P1-INIT", 8.0, i_u, 0.9))
        treatment.append(_row(path_b, index, C1P1, t_tau, t_u, 0.8))
        flex.append(_row(path_b, index, FLEX, f_tau, f_u, 0.7))
    for cell in HELDOUT_CELLS:
        if cell in (path_a, path_b):
            continue
        for index in range(2):
            init_rows.append(_row(cell, index, "C1P1-INIT", 28.0, 0.28, 0.6))
            treatment.append(_row(cell, index, C1P1, 30.0, 0.25, 0.5))
            flex.append(_row(cell, index, FLEX, 32.0, 0.27, 0.4))
    published = publish_b02_primary(init_rows, treatment, flex)
    paths = {row["path"]: row for row in published["active_paths"]}
    assert paths["8_to_12"]["difference_U_flex_minus_c1p1"] == pytest.approx(0.10)
    assert paths["8_to_12"]["paired_U_se"] == pytest.approx(0.0)
    assert paths["12_to_8"]["difference_U_flex_minus_c1p1"] == pytest.approx(0.03)
    assert paths["12_to_8"]["paired_U_se"] == pytest.approx(0.01)
    assert published["delta_U_b02"] == pytest.approx(0.065)
    expected = se_of_mean_of_independent_ses([0.0, 0.01])
    assert published["delta_U_b02_se"] == pytest.approx(expected)
    assert paths["8_to_12"]["G_U_c1p1"] == pytest.approx(0.20)
    assert paths["8_to_12"]["G_U_flex"] == pytest.approx(0.10)
    paired, error = publish_b02_primary_or_error([], treatment, flex)
    assert paired is None
    assert error is not None
    assert "init scenarios are empty" in error


def test_configuration_literal_fields() -> None:
    body = b02_configuration(
        updates=200, updates_completed=200, eval_episodes=256, wall_cap=580.0
    )
    assert body["nonzero_update_norm"] == 0.02
    assert body["previous_nonzero_update_norm"] == 0.0005
    assert body["step_law"] == STEP_LAW
    assert body["step_law"] == (
        "theta <- theta - 0.02 * g / ||g||_2 if g != 0 else no update"
    )
    assert body["selection_history"] == SELECTION_HISTORY
    assert body["initial_parameter_norm_reference_b01"] == 21.186038495201018
    assert body["path_bound"] == 4.0
    allocations = b02_allocations()
    assert allocations["package_models_allocated_count"] == 5
    assert allocations["training_instances_count"] == 2


def test_control_summary_requires_b02_identity_and_initialization_panel(
    tmp_path,
) -> None:
    payload = {
        "object": OBJECT_ID,
        "status": "COMPLETE",
        "arm": C1P1,
        "seed": SEED,
        "block_digest_hex": BLOCK_DIGEST_HEX,
        "configuration": {"eval_episodes_per_cell": 256},
        "counts": {"completed_updates": 200},
        "scenarios": [_row("8_to_12.ACTIVE_CONTINUATION", 0, C1P1, 12.0, 0.1, 0.8)],
        "initialization_panel": {
            "arm": "C1P1-INIT",
            "source": INIT_SOURCE,
            "scenarios": [_row("8_to_12.ACTIVE_CONTINUATION", 0, "C1P1-INIT", 8.0, 0.2, 0.9)],
        },
    }
    identity = validate_control_summary(
        payload,
        updates=200,
        eval_episodes=256,
        block_digest=BLOCK_DIGEST_HEX,
        object_id=OBJECT_ID,
        seed=SEED,
    )
    assert identity["control_arm"] == C1P1
    path = tmp_path / "summary.json"
    path.write_text(__import__("json").dumps(payload), encoding="ascii")
    control, loaded = load_and_validate_b02_control_summary(
        path, updates=200, eval_episodes=256, block_digest=BLOCK_DIGEST_HEX
    )
    assert loaded["control_block_digest_hex"] == BLOCK_DIGEST_HEX
    assert isinstance(control["initialization_panel"], dict)

    missing = dict(payload)
    missing.pop("initialization_panel")
    missing_path = tmp_path / "missing.json"
    missing_path.write_text(__import__("json").dumps(missing), encoding="ascii")
    with pytest.raises(ValueError, match="initialization_panel is required"):
        load_and_validate_b02_control_summary(
            missing_path,
            updates=200,
            eval_episodes=256,
            block_digest=BLOCK_DIGEST_HEX,
        )


def test_two_update_if_native_builds() -> None:
    available, reason = native_available()
    if not available:
        pytest.skip(reason)
    _, rng = make_b02_semantic_rng()
    models = initialize_b01_models(rng)
    assert torch.equal(flat_parameters(models[C1P1]), flat_parameters(models[FLEX]))
    model = models[C1P1]
    baselines = torch.zeros(8, dtype=torch.float64)
    before = flat_parameters(model).clone()
    baselines, _counts, curve0, nonzero0 = execute_b02_training_update(
        model, C1P1, rng, 0, baselines
    )
    after_first = flat_parameters(model)
    delta0 = float(torch.linalg.vector_norm(after_first - before).item())
    if nonzero0:
        assert delta0 == pytest.approx(0.02, abs=1.0e-9)
        assert curve0["parameter_delta_norm"] == 0.02
        assert curve0["measured_parameter_delta_norm"] == pytest.approx(0.02, abs=1.0e-9)
    else:
        assert delta0 == pytest.approx(0.0, abs=1.0e-9)
        assert curve0["parameter_delta_norm"] == 0.0
        assert curve0["measured_parameter_delta_norm"] == pytest.approx(0.0, abs=1.0e-9)
    assert tuple(baselines.shape) == (8,)
    assert curve0["event_order"] == ["parameter_update", "baseline_update"]
    first_baselines = baselines.detach().clone()
    baselines, _counts, curve1, nonzero1 = execute_b02_training_update(
        model, C1P1, rng, 1, baselines
    )
    delta1 = float(torch.linalg.vector_norm(flat_parameters(model) - after_first).item())
    if nonzero1:
        assert delta1 == pytest.approx(0.02, abs=1.0e-9)
        assert curve1["parameter_delta_norm"] == 0.02
        assert curve1["measured_parameter_delta_norm"] == pytest.approx(0.02, abs=1.0e-9)
    else:
        assert delta1 == pytest.approx(0.0, abs=1.0e-9)
        assert curve1["parameter_delta_norm"] == 0.0
        assert curve1["measured_parameter_delta_norm"] == pytest.approx(0.0, abs=1.0e-9)
    assert curve1["event_order"] == ["parameter_update", "baseline_update"]
    assert tuple(baselines.shape) == (8,)
    assert baselines is not first_baselines
