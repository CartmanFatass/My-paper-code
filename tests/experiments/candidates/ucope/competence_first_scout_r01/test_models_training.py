from pathlib import Path

import torch

from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import load_checkpoint
from experiments.candidates.ucope.competence_first_scout_r01.contract import RunBinding, ScoutConfig
from experiments.candidates.ucope.competence_first_scout_r01.host import generate_population
from experiments.candidates.ucope.competence_first_scout_r01.model import build_arm
from experiments.candidates.ucope.competence_first_scout_r01.training import train_policy


def _equal(left, right):
    if isinstance(left, torch.Tensor):
        return isinstance(right, torch.Tensor) and torch.equal(left, right)
    if isinstance(left, dict):
        return isinstance(right, dict) and set(left) == set(right) and all(_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)):
        return type(left) is type(right) and len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


def test_flex_initialization_is_paired_and_bc_has_no_residual():
    mt_root, mt_tail = build_arm("MT-XF-FLEX", "seed", 0)
    ft_root, ft_tail = build_arm("FT-XF-FLEX", "seed", 0)
    assert _equal(mt_root.state_dict(), ft_root.state_dict())
    assert _equal(mt_tail.state_dict(), ft_tail.state_dict())
    bc_root, bc_tail = build_arm("FT-XF-BC", "seed", 0)
    assert set(dict(bc_root.named_parameters())) == {"beta"}
    assert set(dict(bc_tail.named_parameters())) == {"beta"}


def test_target_clocks_and_real_gradient_updates(tmp_path):
    config = ScoutConfig.assess()
    seed = config.seed_ids[0]
    population = generate_population(config, seed)
    binding = RunBinding.assess("a" * 64)
    mt = train_policy(config, population, arm_id="MT-XF-FLEX", seed_id=seed, fold_id=0, run_binding=binding, checkpoint_root=tmp_path / "mt")
    assert mt.activity["tail_optimizer_updates"] == 8
    assert mt.activity["root_optimizer_updates"] == 16
    assert mt.activity["target_refresh_events"] == 16
    assert mt.activity["target_materialization_events"] == 0
    assert mt.activity["root_example_exposures"] == 16 * 256
    assert mt.activity["tail_example_exposures"] == 8 * 256
    for arm in ("FT-XF-FLEX", "FT-XF-BC"):
        run = train_policy(config, population, arm_id=arm, seed_id=seed, fold_id=0, run_binding=binding, checkpoint_root=tmp_path / arm)
        assert run.activity["target_refresh_events"] == 0
        assert run.activity["target_materialization_events"] == 1
        assert run.activity["target_materialization_rows"] == 320 * 4
        assert run.activity["nonfinite_events"] == 0


def test_cold_resume_is_bit_equal_to_uninterrupted(tmp_path):
    config = ScoutConfig.assess()
    seed = config.seed_ids[0]
    population = generate_population(config, seed)
    binding = RunBinding.assess("b" * 64)
    interrupted_root = tmp_path / "interrupted"
    first = train_policy(
        config, population, arm_id="FT-XF-FLEX", seed_id=seed, fold_id=1,
        run_binding=binding, checkpoint_root=interrupted_root, stop_after_root_updates=8,
    )
    assert first.activity["root_optimizer_updates"] == 8
    resumed = train_policy(config, population, arm_id="FT-XF-FLEX", seed_id=seed, fold_id=1, run_binding=binding, checkpoint_root=interrupted_root)
    uninterrupted = train_policy(config, population, arm_id="FT-XF-FLEX", seed_id=seed, fold_id=1, run_binding=binding, checkpoint_root=tmp_path / "uninterrupted")
    resumed_payload = load_checkpoint(interrupted_root / "root-0016.pt")
    full_payload = load_checkpoint(tmp_path / "uninterrupted" / "root-0016.pt")
    for field in ("root_state", "tail_state", "root_optimizer_state", "tail_optimizer_state", "frozen_root_targets", "activity", "run_binding"):
        assert _equal(resumed_payload[field], full_payload[field])
    assert resumed.activity == uninterrupted.activity
