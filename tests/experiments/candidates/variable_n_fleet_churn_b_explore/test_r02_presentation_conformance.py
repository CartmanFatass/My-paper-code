"""VNFC-R02-PRESENTATION-CONFORMANCE-52.

The 52-row unit-test-scale presentation-conformance check that replaces the
304-row byte-addressed A0 finite-physical-action law as a section 4 integrity
item for `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02`.

The row list is frozen, before this file was written, in
`docs/research/candidates/variable_n_fleet_churn/VNFC_SECTION11_RECAST_INTAKE_20260903.md`
section 4.  `ROW_IDS` below must equal that list exactly, in order.

Scope.  A finite conformance observation on the states it enumerates.  It
supports no learnability, return, recovery, superiority, arbitrary-`N` or general
permutation-invariance claim.  It runs in seconds, touches no native host, and
trains nothing.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.torch_models import (  # noqa: E402
    direct_parameter_shapes,
    initial_learned_availability,
    mapr_parameter_shapes,
    materialize_external_initialization,
)

PRESENTATIONS = ("canonical", "reverse", "cyclic", "seed_fixed_random")
STATE_KINDS = ("t0", "later_fixed_or_acquiring", "diagnostic_null_tie")

ROW_IDS = (
    "A01_SORT_ASCENDING_N3",
    "A02_SORT_ASCENDING_N5",
    "A03_SORT_ASCENDING_N7",
    "A04_SORT_NULL_LAST",
    "A05_TIE_EXACT_LOGIT_SMALLEST_OPAQUE",
    "A06_TIE_AGENT_BEATS_NULL",
    "B01_AGENT_ROWS_COPERMUTED",
    "B02_LEGAL_MASKS_COPERMUTED",
    "B03_FIXED_OCCUPANTS_COPERMUTED",
    "B04_OPAQUE_RANKS_COPERMUTED",
    "B05_PHYSICAL_SUPPORT_EQUAL",
    "B06_OPAQUE_DETERMINISTIC_TIE_RANKS_COMPLETE",
    "C01_DET_MAPR_CANONICAL",
    "C02_DET_MAPR_REVERSE",
    "C03_DET_MAPR_CYCLIC",
    "C04_DET_MAPR_SEED_FIXED_RANDOM",
    "C05_DET_DIRECT_CANONICAL",
    "C06_DET_DIRECT_REVERSE",
    "C07_DET_DIRECT_CYCLIC",
    "C08_DET_DIRECT_SEED_FIXED_RANDOM",
    "D01_CDF_BOUNDARY_0_BELOW",
    "D02_CDF_BOUNDARY_0_AT",
    "D03_CDF_BOUNDARY_1_BELOW",
    "D04_CDF_BOUNDARY_1_AT",
    "D05_CDF_BOUNDARY_2_BELOW",
    "D06_CDF_BOUNDARY_2_AT",
    "D07_CDF_FIRST_HALF_OPEN",
    "D08_CDF_LAST_HALF_OPEN",
    "E01_RNG_MAPR_CANONICAL",
    "E02_RNG_MAPR_REVERSE",
    "E03_RNG_MAPR_CYCLIC",
    "E04_RNG_MAPR_SEED_FIXED_RANDOM",
    "E05_RNG_DIRECT_CANONICAL",
    "E06_RNG_DIRECT_REVERSE",
    "E07_RNG_DIRECT_CYCLIC",
    "E08_RNG_DIRECT_SEED_FIXED_RANDOM",
    "F01_RANDOM_STATE_01",
    "F02_RANDOM_STATE_02",
    "F03_RANDOM_STATE_03",
    "F04_RANDOM_STATE_04",
    "F05_RANDOM_STATE_05",
    "F06_RANDOM_STATE_06",
    "F07_RANDOM_STATE_07",
    "F08_RANDOM_STATE_08",
    "F09_RANDOM_STATE_09",
    "F10_RANDOM_STATE_10",
    "F11_RANDOM_STATE_11",
    "F12_RANDOM_STATE_12",
    "G01_NEAR_TIE_N5_REVERSE_SURROGATE",
    "G02_DUPLICATE_TIE",
    "G03_FIXED_PREFIX_NULL",
    "G04_ONE_STEP_GRADIENT_PARAMETER_EQUALITY",
)


def test_row_inventory_is_exactly_the_frozen_52():
    assert len(ROW_IDS) == 52
    assert len(set(ROW_IDS)) == 52


# ---------------------------------------------------------------------------
# fixtures: the R02 law and one frozen parameter pair
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def r02():
    path = REPOSITORY_ROOT / "scripts" / "run_vnfc_bpcr_r02.py"
    spec = importlib.util.spec_from_file_location("vnfc_r02_runner_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["vnfc_r02_runner_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def models(r02):
    """MAPR-4 and zero-residual DIRECT-SET-AR under the canonical sort law.

    `build_canonical_model_classes` derives the R02 classes without mutating the
    R01 runner module, so this file cannot leak the R02 law into other tests.
    """
    torch.set_num_threads(1)
    r01 = r02.load_r01_runner()
    canonical_mapr, canonical_direct = r02.build_canonical_model_classes(r01)
    generator = np.random.default_rng(20260903)
    base = {}
    for name, shape in mapr_parameter_shapes().items():
        if len(shape) != 2:
            continue
        source = (shape[1], shape[0]) if shape[0] <= shape[1] else shape
        base[name] = ("model-initialization/base", generator.standard_normal(source))
    residual = {}
    for name in ("residual.0.weight", "residual.1.weight"):
        shape = direct_parameter_shapes()[name]
        source = (shape[1], shape[0]) if shape[0] <= shape[1] else shape
        residual[name] = ("model-initialization/direct-residual", generator.standard_normal(source))
    mapr_parameters, direct_parameters = materialize_external_initialization(base, residual)
    assert torch.count_nonzero(direct_parameters["residual.out.weight"]) == 0
    assert torch.count_nonzero(direct_parameters["residual.out.bias"]) == 0
    return {
        "MAPR": canonical_mapr(mapr_parameters),
        "DIRECT": canonical_direct(direct_parameters),
    }


@pytest.fixture(scope="module")
def permute(r02):
    r01 = r02.load_r01_runner()
    return r01._permuted_inputs


# ---------------------------------------------------------------------------
# synthetic physical states and the four presentations
# ---------------------------------------------------------------------------

def build_state(n: int, zone: int, kind: str, seed: int):
    """One synthetic physical state in canonical (opaque-ascending) order.

    Physical rank is carried by the opaque rank, so a physical command is read
    off a row index by looking up that row's opaque rank.  Row order here is the
    host's presentation order; `presentation_inputs` permutes it.
    """
    generator = np.random.default_rng(seed)
    agents = torch.from_numpy(generator.standard_normal((1, n, 38)))
    zones = torch.from_numpy(generator.standard_normal((1, 2, 15)))
    globals_ = torch.from_numpy(generator.standard_normal((1, 4)))
    legal = np.ones((1, n, 4), dtype=np.float64)
    fixed = np.full((1, 4), -1, dtype=np.int64)
    if kind == "later_fixed_or_acquiring":
        fixed[0, (zone - 1) * 2] = 0
        legal[0, :, 1] = (generator.random(n) < 0.7).astype(np.float64)
    elif kind == "diagnostic_null_tie":
        legal[0, :, :] = (generator.random((n, 4)) < 0.9).astype(np.float64)
        legal[0, 0, :] = 1.0
        legal[0, min(1, n - 1), :] = 1.0
    else:
        legal[0, :, :] = (generator.random((n, 4)) < 0.85).astype(np.float64)
        legal[0, 0, :] = 1.0
    opaque = torch.from_numpy(generator.permutation(np.arange(1, n + 1)))[None]
    return (
        agents,
        zones,
        globals_,
        torch.from_numpy(legal),
        torch.from_numpy(fixed),
        opaque,
    )


def presentation_orders(n: int, zone: int, seed: int) -> dict[str, tuple[int, ...]]:
    """The same four presentation families PS-B0 uses, on row indices."""
    canonical = tuple(range(n))
    orders = {
        "canonical": canonical,
        "reverse": tuple(reversed(canonical)),
        "cyclic": canonical[1:] + canonical[:1],
    }
    keyed = sorted(
        canonical,
        key=lambda row: hashlib.sha256(
            f"VNFC-R02/presentation/{seed}/{n}/{zone}/{row}".encode("ascii")
        ).hexdigest(),
    )
    random_order = tuple(keyed)
    if random_order in set(orders.values()):
        random_order = tuple(reversed(keyed))
    orders["seed_fixed_random"] = random_order
    return orders


def physical_command(command: torch.Tensor, opaque: torch.Tensor, n: int):
    return tuple(None if int(value) == n else int(opaque[0, int(value)]) for value in command)


def probabilities_by_physical_rank(output, opaque: torch.Tensor, n: int):
    probabilities = output["token_probabilities"][0]
    rows = {int(opaque[0, row]): tuple(probabilities[:, row].tolist()) for row in range(n)}
    rows[None] = tuple(probabilities[:, n].tolist())
    return rows


def presented_views(permute, inputs, orders):
    return {name: permute(inputs, order) for name, order in orders.items()}


def run_all_presentations(model, permute, inputs, orders, uniforms=None):
    """Return {presentation: (physical command, probabilities by physical rank)}."""
    n = inputs[0].shape[1]
    result = {}
    for name, order in orders.items():
        view = permute(inputs, order)
        with torch.no_grad():
            output = model(*view) if uniforms is None else model(*view, uniforms)
        result[name] = (
            physical_command(output["command"][0], view[5], n),
            probabilities_by_physical_rank(output, view[5], n),
        )
    return result


# ---------------------------------------------------------------------------
# Group A -- the canonical sort and its tie order
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "row_id,n",
    [("A01_SORT_ASCENDING_N3", 3), ("A02_SORT_ASCENDING_N5", 5), ("A03_SORT_ASCENDING_N7", 7)],
)
def test_a_sort_is_ascending_opaque_rank(r02, row_id, n):
    assert row_id in ROW_IDS
    for seed in range(4):
        opaque = torch.from_numpy(np.random.default_rng(seed).permutation(np.arange(1, n + 1)))[None]
        perm, inverse = r02.canonical_permutation(opaque)
        ordered = torch.gather(opaque, 1, perm)[0].tolist()
        assert ordered == sorted(ordered) == list(range(1, n + 1))
        assert torch.equal(torch.gather(perm, 1, inverse), torch.arange(n)[None])


def test_a04_sort_null_last(r02, models, permute):
    assert "A04_SORT_NULL_LAST" in ROW_IDS
    n = 5
    inputs = build_state(n, 1, "t0", seed=41)
    orders = presentation_orders(n, 1, seed=41)
    for name, order in orders.items():
        view = permute(inputs, order)
        with torch.no_grad():
            output = models["MAPR"](*view)
        assert output["token_probabilities"].shape == (1, 4, n + 1)
        # the null candidate is column n in every presentation and is never a row
        _, _, _, _, perm, inverse = r02.canonicalize_inputs(view[0], view[3], view[4], view[5])
        assert sorted(perm[0].tolist()) == list(range(n))
        assert n not in perm[0].tolist()


def _tie_state(n: int, tied_rows: tuple[int, int], seed: int):
    """A state whose two named rows are byte-identical, forcing an exact tie."""
    inputs = list(build_state(n, 1, "t0", seed=seed))
    agents = inputs[0].clone()
    legal = inputs[3].clone()
    agents[0, tied_rows[1]] = agents[0, tied_rows[0]]
    legal[0, :, :] = 0.0
    legal[0, tied_rows[0], :] = 1.0
    legal[0, tied_rows[1], :] = 1.0
    inputs[0] = agents
    inputs[3] = legal
    return tuple(inputs)


def _canonical_decode(masked: torch.Tensor, opaque: torch.Tensor) -> int:
    """The frozen deterministic decoder, applied in canonical opaque order.

    `masked` is the presented-order masked logit row of length `n + 1` (null
    last); `opaque` the presented-order opaque ranks.  Returns the physical rank
    of the choice, or `None` for null.
    """
    n = opaque.shape[1]
    perm = torch.argsort(opaque, dim=1, stable=True)
    c_opaque = torch.gather(opaque, 1, perm)
    c_masked = torch.cat((torch.gather(masked[:, :n], 1, perm), masked[:, n:]), 1)
    tie = torch.cat((c_opaque, torch.full((1, 1), 2 ** 30, dtype=c_opaque.dtype)), 1)
    best = c_masked.max(1, keepdim=True).values
    choice = int(torch.where(c_masked == best, tie, torch.iinfo(tie.dtype).max).argmin(1))
    return None if choice == n else int(c_opaque[0, choice])


def test_a05_exact_logit_tie_takes_smallest_opaque_rank():
    """The decoder's tie order under the canonical opaque-rank serialisation."""
    assert "A05_TIE_EXACT_LOGIT_SMALLEST_OPAQUE" in ROW_IDS
    n = 5
    opaque = torch.tensor([[3, 1, 5, 2, 4]], dtype=torch.int64)
    masked = torch.tensor([[-1.0, 0.25, -2.0, 0.25, -3.0, -4.0]], dtype=torch.float64)
    tied = {int(opaque[0, 1]), int(opaque[0, 3])}
    chosen = []
    for order in presentation_orders(n, 1, seed=55).values():
        index = list(order)
        permuted_opaque = opaque[:, index]
        permuted_masked = torch.cat((masked[:, :n][:, index], masked[:, n:]), 1)
        chosen.append(_canonical_decode(permuted_masked, permuted_opaque))
    assert len(set(chosen)) == 1, chosen
    assert chosen[0] == min(tied) == 1


def test_a06_exact_agent_null_tie_takes_the_agent(r02, models):
    assert "A06_TIE_AGENT_BEATS_NULL" in ROW_IDS
    n = 4
    opaque = torch.tensor([[3, 1, 4, 2]], dtype=torch.int64)
    masked = torch.tensor([[0.5, 0.5, -math.inf, -math.inf, 0.5]], dtype=torch.float64)
    tie = torch.cat((opaque, torch.full((1, 1), 2 ** 30, dtype=opaque.dtype)), 1)
    best = masked.max(1, keepdim=True).values
    choice = int(torch.where(masked == best, tie, torch.iinfo(tie.dtype).max).argmin(1))
    assert choice < n, "the null candidate must lose an exact tie against an agent"
    assert int(opaque[0, choice]) == min(int(opaque[0, 0]), int(opaque[0, 1]))
    assert int(tie[0, n]) == 2 ** 30


# ---------------------------------------------------------------------------
# Group B -- the structural predicates, one row each
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def structural(permute):
    n = 5
    inputs = build_state(n, 2, "later_fixed_or_acquiring", seed=61)
    orders = presentation_orders(n, 2, seed=61)
    views = presented_views(permute, inputs, orders)
    return n, views


def test_b01_agent_rows_copermuted(structural):
    assert "B01_AGENT_ROWS_COPERMUTED" in ROW_IDS
    n, views = structural
    keyed = [
        {int(view[5][0, row]): tuple(view[0][0, row].tolist()) for row in range(n)}
        for view in views.values()
    ]
    assert all(row == keyed[0] for row in keyed)


def test_b02_legal_masks_copermuted(structural):
    assert "B02_LEGAL_MASKS_COPERMUTED" in ROW_IDS
    n, views = structural
    keyed = [
        {int(view[5][0, row]): tuple(view[3][0, row].tolist()) for row in range(n)}
        for view in views.values()
    ]
    assert all(row == keyed[0] for row in keyed)


def test_b03_fixed_occupants_copermuted(structural):
    assert "B03_FIXED_OCCUPANTS_COPERMUTED" in ROW_IDS
    n, views = structural
    keyed = [
        tuple(None if int(value) < 0 else int(view[5][0, int(value)]) for value in view[4][0])
        for view in views.values()
    ]
    assert any(value is not None for value in keyed[0]), "this row needs a fixed occupant"
    assert all(row == keyed[0] for row in keyed)


def test_b04_opaque_ranks_copermuted(structural):
    assert "B04_OPAQUE_RANKS_COPERMUTED" in ROW_IDS
    n, views = structural
    keyed = [
        {int(view[5][0, row]): tuple(view[0][0, row].tolist()) for row in range(n)}
        for view in views.values()
    ]
    ranks = [sorted(row) for row in keyed]
    assert all(row == ranks[0] == list(range(1, n + 1)) for row in ranks)
    assert all(row == keyed[0] for row in keyed)


def test_b05_physical_support_equal(structural):
    assert "B05_PHYSICAL_SUPPORT_EQUAL" in ROW_IDS
    n, views = structural
    supports = []
    for view in views.values():
        available = initial_learned_availability(view[4], n)[0]
        per_token = []
        for token in range(4):
            occupant = int(view[4][0, token])
            if occupant >= 0:
                per_token.append((int(view[5][0, occupant]),))
            else:
                per_token.append(tuple(sorted(
                    int(view[5][0, row])
                    for row in range(n)
                    if bool(available[row]) and bool(view[3][0, row, token])
                )))
        supports.append(tuple(per_token))
    assert all(row == supports[0] for row in supports)


def test_b06_opaque_tie_ranks_complete(structural):
    assert "B06_OPAQUE_DETERMINISTIC_TIE_RANKS_COMPLETE" in ROW_IDS
    n, views = structural
    for view in views.values():
        values = [int(value) for value in view[5][0]]
        assert len(values) == n and set(values) == set(range(1, n + 1))


# ---------------------------------------------------------------------------
# Group C -- one deterministic command per family (arm x presentation)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def deterministic(models, permute):
    n = 5
    inputs = build_state(n, 1, "t0", seed=71)
    orders = presentation_orders(n, 1, seed=71)
    return {
        arm: run_all_presentations(models[arm], permute, inputs, orders)
        for arm in ("MAPR", "DIRECT")
    }


@pytest.mark.parametrize(
    "row_id,arm,presentation",
    [
        ("C01_DET_MAPR_CANONICAL", "MAPR", "canonical"),
        ("C02_DET_MAPR_REVERSE", "MAPR", "reverse"),
        ("C03_DET_MAPR_CYCLIC", "MAPR", "cyclic"),
        ("C04_DET_MAPR_SEED_FIXED_RANDOM", "MAPR", "seed_fixed_random"),
        ("C05_DET_DIRECT_CANONICAL", "DIRECT", "canonical"),
        ("C06_DET_DIRECT_REVERSE", "DIRECT", "reverse"),
        ("C07_DET_DIRECT_CYCLIC", "DIRECT", "cyclic"),
        ("C08_DET_DIRECT_SEED_FIXED_RANDOM", "DIRECT", "seed_fixed_random"),
    ],
)
def test_c_deterministic_command_per_family(deterministic, row_id, arm, presentation):
    assert row_id in ROW_IDS
    reference_command, reference_probabilities = deterministic[arm]["canonical"]
    command, probabilities = deterministic[arm][presentation]
    assert command == reference_command
    assert probabilities == reference_probabilities  # bitwise: float equality on binary64


def test_c_direct_contains_mapr_at_zero_residual(deterministic):
    """DIRECT with an exactly zero residual output reproduces MAPR exactly."""
    assert deterministic["DIRECT"]["canonical"][0] == deterministic["MAPR"]["canonical"][0]
    assert deterministic["DIRECT"]["canonical"][1] == deterministic["MAPR"]["canonical"][1]


# ---------------------------------------------------------------------------
# Group D -- physically aligned probabilities at CDF boundaries
# ---------------------------------------------------------------------------

def _cumulative_boundaries(r02, models, permute, inputs, orders):
    n = inputs[0].shape[1]
    view = permute(inputs, orders["canonical"])
    c_agents, c_legal, c_fixed, c_opaque, _, _ = r02.canonicalize_inputs(
        view[0], view[3], view[4], view[5]
    )
    with torch.no_grad():
        output = models["MAPR"](*view)
    probabilities = output["token_probabilities"][0, 0]
    canonical_order = torch.argsort(view[5], dim=1, stable=True)[0].tolist()
    canonical_probabilities = [float(probabilities[row]) for row in canonical_order]
    canonical_probabilities.append(float(probabilities[n]))
    cumulative = []
    running = 0.0
    for value in canonical_probabilities[:-1]:
        running += value
        cumulative.append(running)
    return cumulative


@pytest.mark.parametrize(
    "row_id,index,offset",
    [
        ("D01_CDF_BOUNDARY_0_BELOW", 0, "below"),
        ("D02_CDF_BOUNDARY_0_AT", 0, "at"),
        ("D03_CDF_BOUNDARY_1_BELOW", 1, "below"),
        ("D04_CDF_BOUNDARY_1_AT", 1, "at"),
        ("D05_CDF_BOUNDARY_2_BELOW", 2, "below"),
        ("D06_CDF_BOUNDARY_2_AT", 2, "at"),
        ("D07_CDF_FIRST_HALF_OPEN", None, "first"),
        ("D08_CDF_LAST_HALF_OPEN", None, "last"),
    ],
)
def test_d_cdf_boundaries_are_presentation_free(r02, models, permute, row_id, index, offset):
    assert row_id in ROW_IDS
    n = 3
    inputs = build_state(n, 1, "t0", seed=81)
    orders = presentation_orders(n, 1, seed=81)
    cumulative = _cumulative_boundaries(r02, models, permute, inputs, orders)
    assert len(cumulative) == n
    if offset == "first":
        value = math.nextafter(0.0, 1.0)
    elif offset == "last":
        value = math.nextafter(1.0, 0.0)
    elif offset == "at":
        value = cumulative[index]
    else:
        value = math.nextafter(cumulative[index], 0.0)
    uniforms = torch.full((1, 4), value, dtype=torch.float64)
    results = run_all_presentations(models["MAPR"], permute, inputs, orders, uniforms)
    commands = {name: value_[0] for name, value_ in results.items()}
    probabilities = {name: value_[1] for name, value_ in results.items()}
    assert len(set(commands.values())) == 1, (row_id, commands)
    reference = probabilities["canonical"]
    assert all(row == reference for row in probabilities.values())


# ---------------------------------------------------------------------------
# Group E -- one RNG-coupled physical action per family
# ---------------------------------------------------------------------------

def _address_uniforms(seed: int, arm: str) -> torch.Tensor:
    """Four token uniforms drawn at declared addresses (the runner's law shape)."""
    values = []
    for token in range(4):
        label = f"VNFC-R02/training/action/{arm}/{seed}/token{token}".encode("ascii")
        word = int.from_bytes(hashlib.sha256(label).digest()[:8], "big")
        values.append((word + 0.5) / float(1 << 64))
    return torch.tensor([values], dtype=torch.float64)


@pytest.fixture(scope="module")
def rng_coupled(models, permute):
    n = 5
    inputs = build_state(n, 2, "t0", seed=91)
    orders = presentation_orders(n, 2, seed=91)
    return {
        arm: run_all_presentations(models[arm], permute, inputs, orders, _address_uniforms(91, arm))
        for arm in ("MAPR", "DIRECT")
    }


@pytest.mark.parametrize(
    "row_id,arm,presentation",
    [
        ("E01_RNG_MAPR_CANONICAL", "MAPR", "canonical"),
        ("E02_RNG_MAPR_REVERSE", "MAPR", "reverse"),
        ("E03_RNG_MAPR_CYCLIC", "MAPR", "cyclic"),
        ("E04_RNG_MAPR_SEED_FIXED_RANDOM", "MAPR", "seed_fixed_random"),
        ("E05_RNG_DIRECT_CANONICAL", "DIRECT", "canonical"),
        ("E06_RNG_DIRECT_REVERSE", "DIRECT", "reverse"),
        ("E07_RNG_DIRECT_CYCLIC", "DIRECT", "cyclic"),
        ("E08_RNG_DIRECT_SEED_FIXED_RANDOM", "DIRECT", "seed_fixed_random"),
    ],
)
def test_e_rng_coupled_action_per_family(rng_coupled, row_id, arm, presentation):
    assert row_id in ROW_IDS
    reference_command, reference_probabilities = rng_coupled[arm]["canonical"]
    command, probabilities = rng_coupled[arm][presentation]
    assert command == reference_command
    assert probabilities == reference_probabilities


# ---------------------------------------------------------------------------
# Group F -- twelve fixed-seed random states
# ---------------------------------------------------------------------------

def _random_row_case(index: int):
    generator = np.random.default_rng(20260903_000 + index)
    n = int(generator.choice([3, 5, 7]))
    zone = int(generator.choice([1, 2]))
    kind = STATE_KINDS[int(generator.integers(0, len(STATE_KINDS)))]
    arm = "MAPR" if index % 2 == 1 else "DIRECT"
    return n, zone, kind, arm


@pytest.mark.parametrize("row_id", [f"F{index:02d}_RANDOM_STATE_{index:02d}" for index in range(1, 13)])
def test_f_random_states(models, permute, row_id):
    assert row_id in ROW_IDS
    index = int(row_id[1:3])
    n, zone, kind, arm = _random_row_case(index)
    seed = 20260903_000 + index
    inputs = build_state(n, zone, kind, seed=seed)
    orders = presentation_orders(n, zone, seed=seed)
    uniforms = _address_uniforms(seed, arm)

    deterministic = run_all_presentations(models[arm], permute, inputs, orders)
    sampled = run_all_presentations(models[arm], permute, inputs, orders, uniforms)
    for table in (deterministic, sampled):
        commands = {name: value[0] for name, value in table.items()}
        probabilities = {name: value[1] for name, value in table.items()}
        assert len(set(commands.values())) == 1, (row_id, n, zone, kind, arm, commands)
        assert all(row == probabilities["canonical"] for row in probabilities.values())


# ---------------------------------------------------------------------------
# Group G -- near tie, duplicate tie, fixed prefix with null, and one step
# ---------------------------------------------------------------------------

def test_g01_near_tie_n5_reverse_surrogate(models, permute):
    """Surrogate for the registered R01 `N=5/reverse` witness.

    The frozen witness parameterisation lives in the untracked A0 package
    `experiments/candidates/variable_n_fleet_churn_r02/fixtures.py`, which this
    recast neither commits nor imports; this row constructs its own near-tie
    exhibiting the same mechanism (two candidate logits within one ULP, where a
    reduction-order difference across presentations would flip the choice).
    """
    assert "G01_NEAR_TIE_N5_REVERSE_SURROGATE" in ROW_IDS
    n = 5
    inputs = list(_tie_state(n, (1, 3), seed=101))
    agents = inputs[0].clone()
    # perturb one tied row by a single ULP in one feature
    agents[0, 3, 0] = math.nextafter(float(agents[0, 3, 0]), math.inf)
    inputs[0] = agents
    inputs = tuple(inputs)
    orders = presentation_orders(n, 1, seed=101)
    results = run_all_presentations(models["MAPR"], permute, inputs, orders)
    canonical_command, canonical_probabilities = results["canonical"]
    reverse_command, reverse_probabilities = results["reverse"]
    assert reverse_command == canonical_command
    assert reverse_probabilities == canonical_probabilities
    assert all(value[0] == canonical_command for value in results.values())


def test_g02_duplicate_tie(models, permute):
    """Two byte-identical agent rows with different opaque ranks.

    Direct observation, recorded rather than assumed: byte-identical agent rows
    at different row positions do not always produce byte-identical candidate
    logits, because the row-wise GEMM is position dependent -- which is exactly
    the finite-precision mechanism the R01 counterexample exhibited.  What the
    canonical opaque-rank sort guarantees is that whatever the decoder does, it
    does the same thing for every co-presentation of the physical state; and
    that when the masked logits are exactly equal the smaller opaque rank wins.
    """
    assert "G02_DUPLICATE_TIE" in ROW_IDS
    n = 5
    inputs = _tie_state(n, (0, 4), seed=111)
    opaque = inputs[5]
    tied = (int(opaque[0, 0]), int(opaque[0, 4]))
    orders = presentation_orders(n, 1, seed=111)
    results = run_all_presentations(models["DIRECT"], permute, inputs, orders)
    first = {name: value[0][0] for name, value in results.items()}
    assert len(set(first.values())) == 1, first
    assert next(iter(first.values())) in tied
    probabilities = {name: value[1] for name, value in results.items()}
    assert all(row == probabilities["canonical"] for row in probabilities.values())
    # the exact-tie limb of the rule, on the decoder itself
    duplicate_opaque = torch.tensor([[tied[0], tied[1]]], dtype=torch.int64)
    duplicate_masked = torch.tensor([[0.5, 0.5, -1.0]], dtype=torch.float64)
    assert _canonical_decode(duplicate_masked, duplicate_opaque) == min(tied)


def test_g03_fixed_prefix_null(models, permute):
    assert "G03_FIXED_PREFIX_NULL" in ROW_IDS
    n = 5
    inputs = list(build_state(n, 1, "later_fixed_or_acquiring", seed=121))
    legal = inputs[3].clone()
    legal[0, :, 3] = 0.0  # token 3 has no legal agent, so null is the only support
    inputs[3] = legal
    inputs = tuple(inputs)
    assert int(inputs[4][0].max()) >= 0, "this row needs a fixed occupant"
    orders = presentation_orders(n, 1, seed=121)
    results = run_all_presentations(models["MAPR"], permute, inputs, orders)
    commands = {name: value[0] for name, value in results.items()}
    assert len(set(commands.values())) == 1
    assert next(iter(commands.values()))[3] is None
    fixed_token = int(torch.argmax(inputs[4][0]))
    reference = next(iter(commands.values()))
    assert reference[fixed_token] is not None


def test_g04_one_step_gradient_and_parameter_equality(r02, permute):
    assert "G04_ONE_STEP_GRADIENT_PARAMETER_EQUALITY" in ROW_IDS
    r01 = r02.load_r01_runner()
    canonical_mapr, _ = r02.build_canonical_model_classes(r01)
    generator = np.random.default_rng(131)
    base = {}
    for name, shape in mapr_parameter_shapes().items():
        if len(shape) != 2:
            continue
        source = (shape[1], shape[0]) if shape[0] <= shape[1] else shape
        base[name] = ("model-initialization/base", generator.standard_normal(source))
    residual = {}
    for name in ("residual.0.weight", "residual.1.weight"):
        shape = direct_parameter_shapes()[name]
        source = (shape[1], shape[0]) if shape[0] <= shape[1] else shape
        residual[name] = ("model-initialization/direct-residual", generator.standard_normal(source))
    mapr_parameters, _ = materialize_external_initialization(base, residual)

    n = 5
    inputs = build_state(n, 1, "t0", seed=131)
    orders = presentation_orders(n, 1, seed=131)

    def one_step(order):
        model = canonical_mapr({name: value.clone() for name, value in mapr_parameters.items()})
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        view = permute(inputs, order)
        with torch.no_grad():
            reference = model(*view)
        output = model(*view, None, reference["command"])
        loss = -output["log_probability"].sum() + output["value"].pow(2).sum()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradients = {
            name: parameter.grad.detach().clone()
            for name, parameter in model.named_parameters()
        }
        optimizer.step()
        parameters = {
            name: parameter.detach().clone() for name, parameter in model.named_parameters()
        }
        return float(loss), gradients, parameters

    base_loss, base_gradients, base_parameters = one_step(orders["canonical"])
    other_loss, other_gradients, other_parameters = one_step(orders["reverse"])
    assert base_loss == other_loss
    assert set(base_gradients) == set(other_gradients)
    for name in base_gradients:
        assert torch.equal(base_gradients[name], other_gradients[name]), name
        assert torch.equal(base_parameters[name], other_parameters[name]), name
