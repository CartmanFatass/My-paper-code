"""Tests for the ``UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01`` runner.

They pin the runner to the frozen package: the canonical row order, the cyclic batch windows,
the FP32 feature and basis constructions, the FP32 root-target arithmetic, the whitening
contract and its recovery identity, the reading rule's branch order, and one end-to-end
miniature run whose update counts are the only thing reduced.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

numpy = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")

from experiments.candidates.ucope.competence_first_scout_r01 import training  # noqa: E402
from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    BATCH_SIZE,
    CONTEXTS,
    K_TRAIN,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    BellmanScorer,
    tensors_for_record,
    x_features,
)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load("ucope_competence_whitened_r01", "run_ucope_competence_whitened_r01.py")
SELECTION = _load("ucope_competence_n_selection", "run_ucope_competence_whitened_n_selection.py")

SMALL_EPISODES = 320


@pytest.fixture(scope="module")
def small_columns():
    raw = SELECTION.generate_columns(B1_SEEDS[0], SMALL_EPISODES)
    ordered, labels = RUNNER.canonical_order(raw)
    return raw, ordered, labels


# --------------------------------------------------------------------------- frozen constants


def test_the_carded_constants_are_the_frozen_ones():
    assert RUNNER.TAIL_ROWS_PER_POLICY == 81_920
    assert RUNNER.EPISODES_PER_CONTEXT == 40_960
    assert (RUNNER.TAIL_UPDATES, RUNNER.ROOT_UPDATES) == (1_600, 3_200)
    assert RUNNER.LEARNING_RATE == 3e-3
    assert RUNNER.BATCH_SIZE == BATCH_SIZE == 256
    assert RUNNER.ARM_ID == "FT-XF-BC"
    assert RUNNER.EPS_L == 0.10
    assert RUNNER.MAJORITY == 4
    assert RUNNER.BETA_STAR == (0.31, 0.60, 1.35, -1.08, -0.891)
    assert (RUNNER.CHOLESKY_TOLERANCE, RUNNER.MINIMUM_GRAM_EIGENVALUE) == (1e-10, 1e-6)


def test_the_index_law_is_the_one_the_n_selection_fixed():
    assert SELECTION.OFFSET == 1_000_000
    assert SELECTION.OFFSET % 20 == 0
    assert SELECTION.OFFSET > 5_119
    # The runner has exactly one generation path: the n selection's.
    assert RUNNER.N_SELECTION_SCRIPT.name == "run_ucope_competence_whitened_n_selection.py"


# --------------------------------------------------------------------------- canonical order


def test_canonical_order_is_the_frozen_episode_index_context_id_order(small_columns):
    _raw, ordered, labels = small_columns
    assert labels == sorted(context_id(context) for context in CONTEXTS)
    assert labels != [context_id(context) for context in CONTEXTS]
    width = len(CONTEXTS)
    rebuilt = [
        f"{'LINKED' if ordered['linked'][index] else 'SEVERED'}"
        f"-p{round(ordered['reliability'][index] * 20)}_20"
        f"-c{round(ordered['cost'][index] * 100)}_100"
        for index in range(width)
    ]
    # Costs 9/100 and 7/50 print as 9_100 and 14_100 here; only the ordering is under test.
    assert rebuilt == sorted(rebuilt)
    assert (ordered["episode_order"][:width] == 0).all()


def test_canonical_order_is_a_permutation_that_preserves_every_episode(small_columns):
    raw, ordered, _labels = small_columns
    for name in raw:
        assert sorted(raw[name].tolist()) == sorted(ordered[name].tolist())
        width = len(CONTEXTS)
        assert sorted(raw[name][:width].tolist()) == sorted(ordered[name][:width].tolist())


# --------------------------------------------------------------------------- batch windows


@pytest.mark.parametrize("count", (640, 1_280, 999))
@pytest.mark.parametrize("update", (0, 1, 7, 63))
def test_cyclic_indices_reproduce_the_frozen_cyclic_batch(count, update):
    rows = tuple(range(count))
    assert tuple(RUNNER._cyclic_indices(count, update, BATCH_SIZE)) == training._cyclic_batch(
        rows, update, BATCH_SIZE)


# --------------------------------------------------------------------------- designs


def test_stage_designs_reproduce_the_n_selection_designs(small_columns):
    _raw, ordered, _labels = small_columns
    for fold in (0, 1):
        blocks = RUNNER.stage_designs(ordered, fold)
        tail_mask = (ordered["fold"] == (1 - fold)) & ordered["probe"]
        root_mask = ordered["fold"] == fold
        design, targets = SELECTION._tail_design(ordered, tail_mask)
        assert numpy.array_equal(blocks["tail"]["design64"], design)
        assert numpy.array_equal(blocks["tail"]["targets64"], targets)
        assert numpy.array_equal(
            blocks["root"]["design64"], SELECTION._root_design(ordered, root_mask))
        assert blocks["tail"]["design64"].shape == (2 * SMALL_EPISODES, 5)
        assert blocks["root"]["design64"].shape == (4 * SMALL_EPISODES, 7)


def test_x_features_match_the_frozen_nine_dimensional_construction(small_columns):
    _raw, ordered, _labels = small_columns
    blocks = RUNNER.stage_designs(ordered, 0)
    tail_mask = (ordered["fold"] == 1) & ordered["probe"]
    root_mask = ordered["fold"] == 0
    for offset in (0, 1, 17, 129):
        index = numpy.flatnonzero(tail_mask)[offset]
        expected = x_features(
            phase_tail=True, action_probe=False, period=int(ordered["period"][index]),
            belief=float(ordered["belief"][index]), cost=float(ordered["cost"][index]),
            linked=bool(ordered["linked"][index]), reliability=float(ordered["reliability"][index]))
        assert blocks["tail"]["x"][offset].tolist() == pytest.approx(list(expected), abs=1e-7)

        index = numpy.flatnonzero(root_mask)[offset]
        probe = bool(ordered["probe"][index])
        expected = x_features(
            phase_tail=False, action_probe=probe,
            period=0 if probe else int(ordered["period"][index]), belief=0.5,
            cost=float(ordered["cost"][index]), linked=bool(ordered["linked"][index]),
            reliability=float(ordered["reliability"][index]))
        assert blocks["root"]["x"][offset].tolist() == pytest.approx(list(expected), abs=1e-7)


# --------------------------------------------------------------------------- root targets


def test_root_targets_fp64_match_the_n_selection_package(small_columns):
    _raw, ordered, _labels = small_columns
    blocks = RUNNER.stage_designs(ordered, 0)
    beta = numpy.array([0.31, 0.60, 1.35, -1.08, -0.891])
    root_mask = ordered["fold"] == 0
    assert numpy.array_equal(
        RUNNER.root_targets_fp64(blocks["root"], beta),
        SELECTION._root_targets(ordered, root_mask, beta),
    )


def test_root_targets_fp32_match_the_frozen_scorer_arithmetic(small_columns):
    _raw, ordered, _labels = small_columns
    blocks = RUNNER.stage_designs(ordered, 0)
    beta = numpy.array([0.31, 0.60, 1.35, -1.08, -0.891])
    scorer = BellmanScorer.build("tail", False, "probe|fold-0|BC")
    with torch.no_grad():
        scorer.beta.copy_(torch.tensor(beta.astype(numpy.float32), dtype=torch.float32))
    produced = RUNNER.root_targets_fp32(blocks["root"], list(beta))
    indices = numpy.flatnonzero(blocks["root"]["probe"])[:32]
    for index in indices:
        record = SimpleNamespace(
            link="LINKED" if blocks["root"]["design64"][index][5] else "SEVERED",
            reliability=float(ordered["reliability"][ordered["fold"] == 0][index]),
            total_cost=float(ordered["cost"][ordered["fold"] == 0][index]),
        )
        belief = float(blocks["root"]["belief"][index])
        pairs = [tensors_for_record(record, stage="tail", action_probe=False, period=period,
                                    belief=belief) for period in K_TRAIN]
        with torch.no_grad():
            values = scorer(torch.stack([p[0] for p in pairs]), torch.stack([p[1] for p in pairs]))
        expected = float(blocks["root"]["probe_primitive"][index]) + float(values.max())
        assert produced[index] == pytest.approx(expected, abs=1e-6)


# --------------------------------------------------------------------------- whitening


def test_whitening_records_the_contract_and_recovers_the_raw_solution(small_columns):
    _raw, ordered, _labels = small_columns
    blocks = RUNNER.stage_designs(ordered, 0)
    for stage in ("tail", "root"):
        design = blocks[stage]["design64"]
        record = RUNNER.whitening(design, stage=stage)
        assert record["stage"] == stage
        assert record["source"] == "training_rows_only"
        assert record["cholesky_reconstruction_max_abs"] <= RUNNER.CHOLESKY_TOLERANCE
        assert record["gram_smallest_eigenvalue"] > RUNNER.MINIMUM_GRAM_EIGENVALUE
        assert record["gram_condition_number"] > 1.0
        factor = record["_factor"]
        assert numpy.abs(factor @ factor.T - design.T @ design / design.shape[0]).max() <= 1e-10
        assert numpy.abs(record["_inverse"] @ factor - numpy.eye(design.shape[1])).max() < 1e-9

    design = blocks["tail"]["design64"]
    targets = blocks["tail"]["targets64"]
    record = RUNNER.whitening(design, stage="tail")
    whitened = design @ record["_inverse"].T
    beta_tilde, *_ = numpy.linalg.lstsq(whitened, targets, rcond=None)
    recovered = numpy.linalg.solve(record["_factor"].T, beta_tilde)
    assert recovered == pytest.approx(RUNNER.exact_solve(design, targets), abs=1e-9)


def test_whitening_refuses_a_rank_deficient_design():
    design = numpy.tile(numpy.array([[1.0, 2.0, 3.0]]), (64, 1))
    with pytest.raises(RUNNER.LaunchRefusal, match="lambda_min"):
        RUNNER.whitening(design, stage="tail")


def test_gradient_infinity_norm_vanishes_at_the_exact_solution(small_columns):
    _raw, ordered, _labels = small_columns
    blocks = RUNNER.stage_designs(ordered, 0)
    design, targets = blocks["tail"]["design64"], blocks["tail"]["targets64"]
    beta = RUNNER.exact_solve(design, targets)
    assert RUNNER.gradient_infinity_norm(design, targets, beta) < 1e-10
    assert RUNNER.gradient_infinity_norm(design, targets, RUNNER.BETA_STAR) > 0.0


# --------------------------------------------------------------------------- the reading rule


def _policies(whitened, raw, exact):
    return [
        {"arms": {
            "WHITENED-10X": {"competence": {"competence_pass": w}},
            "RAW-10X": {"competence": {"competence_pass": r}},
            "EXACT-SOLVE": {"competence": {"competence_pass": e}},
        }}
        for w, r, e in zip(whitened, raw, exact)
    ]


def test_rule_c_a_when_the_whitened_arm_is_competent_in_all_six():
    reading = RUNNER.apply_reading_rule(_policies([True] * 6, [False] * 6, [False] * 6))
    assert reading["branch"] == "C-A"
    assert reading["numbers"]["whitened_competent"] == 6


def test_rule_c_b_needs_a_majority_and_a_clean_ceiling():
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 4 + [False] * 2, [False] * 6, [True] * 6))
    assert reading["branch"] == "C-B"
    assert reading["numbers"]["whitened_competent"] == 4


def test_rule_c_c_when_the_ceiling_is_clean_and_the_learner_is_not():
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 3 + [False] * 3, [False] * 6, [True] * 6))
    assert reading["branch"] == "C-C"


def test_rule_c_d_when_the_ceiling_itself_falls_short():
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 5 + [False], [False] * 6, [True] * 5 + [False]))
    assert reading["branch"] == "C-D"


def test_rule_c_e_is_reachable_only_after_the_four_named_branches():
    # Ceiling clean in all six and whitened at exactly the majority is C-B, not C-E; C-E needs a
    # combination none of the four describe, which the ordered rule leaves as a residue only.
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 4 + [False] * 2, [False] * 6, [True] * 6))
    assert reading["branch"] == "C-B"
    assert RUNNER.apply_reading_rule(
        _policies([False] * 6, [False] * 6, [True] * 6))["branch"] == "C-C"


def test_the_branch_order_is_the_carded_order():
    source = (PROJECT_ROOT / "scripts/run_ucope_competence_whitened_r01.py").read_text(
        encoding="utf-8")
    positions = [source.index(f'"branch": "{name}"') for name in ("C-A", "C-B", "C-C", "C-D", "C-E")]
    assert positions == sorted(positions)


# --------------------------------------------------------------------------- end to end


def test_a_miniature_run_produces_a_complete_record(tmp_path, monkeypatch):
    monkeypatch.setattr(RUNNER, "TAIL_UPDATES", 4)
    monkeypatch.setattr(RUNNER, "ROOT_UPDATES", 8)
    path = RUNNER.run_object(tmp_path / "mini", thread_cap=2,
                             episodes_per_context=SMALL_EPISODES)
    record = json.loads(Path(path).read_text(encoding="utf-8"))

    assert record["complete"] is True
    assert record["object_id"] == "UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01"
    assert record["evidence_class"] == "B/EXPLORE"
    assert len(record["policies"]) == 6
    assert record["counts"]["environment_episodes"] == 3 * SMALL_EPISODES * len(CONTEXTS)
    assert record["counts"]["tail_rows"] == 6 * 2 * SMALL_EPISODES
    assert record["counts"]["root_rows"] == 6 * 4 * SMALL_EPISODES
    assert record["counts"]["exact_solves"] == 12
    for name, value in record["counts"].items():
        if name not in {"nonfinite_events", "clipping_events"}:
            assert value > 0, name
    assert record["counts"]["nonfinite_events"] == 0

    assert record["admission"]["passed"] is True
    assert record["execution_topology"]["torch_intraop_threads"] <= 2
    assert record["reading_rule"]["branch"] in {"C-A", "C-B", "C-C", "C-D", "C-E"}

    for policy in record["policies"]:
        assert set(policy["arms"]) == {"WHITENED-10X", "RAW-10X", "EXACT-SOLVE"}
        for stage in ("tail", "root"):
            check = policy["whitening"][stage]
            assert check["cholesky_reconstruction_max_abs"] <= 1e-10
            assert check["gram_smallest_eigenvalue"] > 1e-6
        assert policy["arms"]["EXACT-SOLVE"]["d_learned_tail"] == 0.0
        for arm in ("WHITENED-10X", "RAW-10X"):
            competence = policy["arms"][arm]["competence"]
            assert set(competence) >= {
                "all_finite", "all_unique", "oracle_root_match", "max_regret",
                "minimum_tail_agreement", "competence_pass"}

    exposure = record["exposure_line"]
    assert {row["arm"] for row in exposure["rows"]} == {"WHITENED-10X", "RAW-10X"}
    assert len(exposure["rows"]) == 6 * 2 * 2
    assert exposure["learner_can_move_in_its_budget"] is True


def test_the_output_root_is_create_once(tmp_path):
    (tmp_path / "taken").mkdir()
    with pytest.raises(RUNNER.LaunchRefusal, match="create-once"):
        RUNNER.run_object(tmp_path / "taken")


def test_the_interop_thread_knob_fails_soft_and_is_only_recorded(monkeypatch):
    """Topology is recorded-not-gating (spec 11.4), so a refused knob must not stop a run."""
    import torch as _torch_module

    def refuse(_value):
        raise RuntimeError(
            "Error: cannot set number of interop threads after parallel work has started")

    monkeypatch.setattr(_torch_module, "set_num_interop_threads", refuse)
    RUNNER._configure_topology(2)          # must not raise
    record = RUNNER.topology_record(2)
    assert record["gating"] is False
    assert record["torch_interop_threads_observed"] == _torch_module.get_num_interop_threads()
    assert "cannot set number of interop threads" in record["torch_interop_threads_set_error"]

    # With the real torch restored the call still must not raise; in a shared pytest process the
    # genuine knob refuses too, and that refusal is recorded rather than asserted.
    monkeypatch.undo()
    RUNNER._configure_topology(2)
    assert RUNNER.topology_record(2)["torch_intraop_threads"] == 2
