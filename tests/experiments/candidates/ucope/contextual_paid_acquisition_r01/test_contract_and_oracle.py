from dataclasses import replace
from fractions import Fraction

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01 import contract, oracle


def test_frozen_contract_population_and_manifest_are_exact():
    cells = contract.contexts()
    assert len(cells) == 8
    assert {cell["link"] for cell in cells} == {"LINKED", "SEVERED"}
    assert {cell["reliability"] for cell in cells} == {Fraction(13, 20), Fraction(17, 20)}
    assert {cell["total_cost"] for cell in cells} == {Fraction(9, 100), Fraction(14, 100)}
    assert contract.HORIZON == 12
    assert contract.MARK_COUNT == 6
    assert contract.K_TRAIN == (1, 3, 5, 7, 9)
    assert contract.K_TEST == (2, 4, 6, 8)
    assert contract.EPISODES_PER_CONTEXT == 20_480
    assert contract.PROBE_EPISODES == 10_240
    assert contract.ROOT_ACTION_FLOOR == 2_048
    assert contract.DISPLAYED_COUNT_FLOOR == 256
    assert len(contract.SEED_SLOTS) == len(set(contract.SEED_SLOTS)) == 10
    assert all("r03" not in seed.lower() for seed in contract.SEED_SLOTS)
    assert contract.SCHEMA_VERSION == 2
    assert contract.INFERENCE_READINESS == {
        "ready": True,
        "status": "READY",
        "rule": "ALL_TEN_ALL_EIGHT_STRICT_POSITIVE_V1",
        "strict_threshold": {"numerator": 0, "denominator": 1},
        "fixed_seed_slots": 10,
        "seed_superpopulation_claim": False,
    }
    assert contract.RESOURCE_CEILING == {
        "workers": 1,
        "torch_intraop_threads": 1,
        "torch_interop_threads": 1,
        "batch_size": 256,
        "model_checkpoints_per_seed": 1,
        "checkpoint_cadence_batches": 1,
        "estimated_peak_memory_bytes": 2 * 1024**3,
        "minimum_live_available_memory_bytes": 4 * 1024**3,
        "minimum_free_disk_bytes": 4 * 1024**3,
        "projected_scratch_bytes": 64 * 1024**2,
        "projected_durable_bytes": 64 * 1024**2,
        "scratch_ceiling_bytes": 256 * 1024**2,
        "durable_ceiling_bytes": 256 * 1024**2,
        "maximum_result_wall_seconds": 3_600,
    }
    assert contract.validate_contract() == contract.default_manifest()


@pytest.mark.parametrize("field,bad", [
    ("schema_version", True),
    ("contract_id", "drift"),
    ("mode", "PRODUCTION-ish"),
    ("seed_slots", []),
    ("episodes_per_context", 20_479),
    ("context_ids", []),
    ("inference_readiness", {"ready": False, "status": "UNRESOLVED"}),
])
def test_manifest_drift_fails_closed(field, bad):
    manifest = contract.default_manifest()
    manifest[field] = bad
    with pytest.raises(contract.ContractError):
        contract.validate_contract(manifest)
    manifest = contract.default_manifest()
    manifest["extra"] = 1
    with pytest.raises(contract.ContractError):
        contract.validate_contract(manifest)


def test_test_only_manifest_is_explicit_and_bounded():
    value = contract.validate_contract(contract.default_manifest(contract.TEST_ONLY_MODE, 640))
    assert value["mode"] == "TEST_ONLY"
    assert value["episodes_per_context"] == 640
    for size in (0, 39, 41, 641, 20_520, True, "640"):
        manifest = contract.default_manifest(contract.TEST_ONLY_MODE, 640)
        manifest["episodes_per_context"] = size
        with pytest.raises(contract.ContractError):
            contract.validate_contract(manifest)


def test_exact_tail_law_and_fraction_oracle():
    for regime, center in (("SHORT", 2), ("LONG", 8)):
        for period in range(1, 10):
            q = Fraction(95, 100) - Fraction((period - center) ** 2, 100)
            assert oracle.tail_q(regime, period) == q
            assert oracle.tail_time(period) == -Fraction(period, 100)
            assert oracle.tail_energy(period) == -Fraction(period * period, 1000)
            assert oracle.tail_return(regime, period) == q - Fraction(period, 100) - Fraction(period * period, 1000)


def test_flip_certificate_has_exact_decomposition_vectors_and_single_flip():
    cert = oracle.construct_flip_certificate()
    assert (cert.baseline_train_period, cert.baseline_train_value) == (5, Fraction(785, 1000))
    assert (cert.baseline_test_period, cert.baseline_test_value) == (4, Fraction(794, 1000))
    assert cert.information == {
        "13/20": {"train": Fraction(57309249, 1600000000), "test": Fraction(23936761, 800000000)},
        "17/20": {"train": Fraction(26928171, 320000000), "test": Fraction(57149681, 800000000)},
    }
    positives_train = []
    positives_test = []
    for cell, context in zip(cert.cells, contract.contexts()):
        expected_d = Fraction(1, 25) - context["total_cost"]
        expected_i_train = oracle.information_gain(context["reliability"], contract.K_TRAIN) if context["link"] == "LINKED" else Fraction(0)
        expected_i_test = oracle.information_gain(context["reliability"], contract.K_TEST) if context["link"] == "LINKED" else Fraction(0)
        assert (cell.B_train, cell.B_test) == (Fraction(785, 1000), Fraction(794, 1000))
        assert cell.D == expected_d < 0
        assert (cell.I_train, cell.I_test) == (expected_i_train, expected_i_test)
        assert (cell.A0_train, cell.A0_test) == (cell.B_train + expected_d, cell.B_test + expected_d)
        assert (cell.A_train, cell.A_test) == (cell.A0_train + expected_i_train, cell.A0_test + expected_i_test)
        assert (cell.train_gamma, cell.test_gamma) == (expected_i_train + expected_d, expected_i_test + expected_d)
        for periods, values, optima in ((contract.K_TRAIN, cell.train_tail_values, cell.train_tail_optima), (contract.K_TEST, cell.test_tail_values, cell.test_tail_optima)):
            for count in range(7):
                belief = oracle.posterior_short(context["reliability"], count) if context["link"] == "LINKED" else Fraction(1, 2)
                expected = {str(k): oracle.expected_tail_value(k, belief) for k in periods}
                assert values[str(count)] == expected
                ranking = sorted((value, -int(k), int(k)) for k, value in expected.items())
                assert ranking[-1][0] != ranking[-2][0]
                assert optima[str(count)] == ranking[-1][2]
        positives_train += [cell.context_id] if cell.train_action == "PROBE" else []
        positives_test += [cell.context_id] if cell.test_action == "PROBE" else []
    assert positives_train == positives_test == ["LINKED-p17_20-c9_100"]
    target = next(cell for cell in cert.cells if cell.context_id == positives_test[0])
    assert [target.test_tail_optima[str(n)] for n in range(7)] == [6, 6, 6, 4, 2, 2, 2]


def test_flip_certificate_validation_rejects_sign_tie_and_vector_drift():
    cert = oracle.construct_flip_certificate()
    with pytest.raises(ValueError):
        replace(cert, baseline_train_value=cert.baseline_train_value + Fraction(1, 1000)).validate()
    cell = cert.cells[0]
    with pytest.raises(ValueError):
        replace(cert, cells=(replace(cell, D=Fraction(0)), *cert.cells[1:])).validate()


@pytest.mark.parametrize("call", [
    lambda: oracle.tail_q("UNKNOWN", 2),
    lambda: oracle.tail_q("SHORT", True),
    lambda: oracle.tail_time(0),
    lambda: oracle.tail_energy(10),
    lambda: oracle.joint_count_probability("SHORT", Fraction(1, 2), 3),
    lambda: oracle.joint_count_probability("SHORT", Fraction(13, 20), True),
    lambda: oracle.direct_probe_value(Fraction(1, 10)),
    lambda: oracle.gamma("UNKNOWN", Fraction(13, 20), Fraction(9, 100), (1,)),
])
def test_oracle_invalid_inputs_fail_closed(call):
    with pytest.raises(ValueError):
        call()
