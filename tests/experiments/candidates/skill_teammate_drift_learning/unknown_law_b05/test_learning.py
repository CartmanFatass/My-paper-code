from dataclasses import asdict

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05 import learning


def test_development_bank_is_exact_and_ids_are_stable():
    specs = learning.development_specs()
    assert len(specs) == 20
    assert len({spec.id for spec in specs}) == 20
    assert [sum(spec.family == family for spec in specs) for family in learning.FAMILIES] == [2, 6, 12]
    assert all(asdict(spec)["prior_strength"] in (2.0, 16.0) for spec in specs)
    assert learning.Spec("fingerprint_recent", "law", 2, 64).id == (
        "fingerprint_recent__law__prior2__window64"
    )


def test_shared_law_excludes_safe_and_resets_on_public_version():
    learner = learning.SharedLawLearner(contexts=4)
    initial = learner.predict(version=0, context=2)
    np.testing.assert_array_equal(initial, np.full(4, 0.25))
    assert not learner.observe(action=learning.SAFE, version=0, context=2, outcome=0)
    np.testing.assert_array_equal(learner.predict(version=0, context=2), initial)
    assert learner.count(version=0, context=2) == 0

    assert learner.observe(action=learning.COOPERATIVE, version=0, context=2, outcome=3)
    np.testing.assert_allclose(
        learner.predict(version=0, context=2), [1 / 6, 1 / 6, 1 / 6, 1 / 2]
    )
    np.testing.assert_array_equal(
        learner.predict(version=0, context=1), np.full(4, 0.25)
    )
    center = learner.activate_version(1)
    expected_center = np.mean(
        [[0.25] * 4, [0.25] * 4, [1 / 6, 1 / 6, 1 / 6, 1 / 2], [0.25] * 4],
        axis=0,
    )
    np.testing.assert_allclose(center, expected_center)
    np.testing.assert_allclose(learner.predict(version=1, context=2), expected_center)
    assert learner.updates == 1


def test_new_version_center_is_frozen_before_current_feedback():
    learner = learning.SharedLawLearner(contexts=4)
    for context, outcome in enumerate((0, 1, 2, 3)):
        for _ in range(context + 1):
            learner.observe(
                action=learning.COOPERATIVE,
                version=0,
                context=context,
                outcome=outcome,
            )
    expected = np.stack(
        [learner.predict(version=0, context=context) for context in range(4)]
    ).mean(axis=0)
    center = learner.activate_version(1)
    np.testing.assert_allclose(center, expected)
    learner.observe(
        action=learning.COOPERATIVE, version=1, context=0, outcome=3
    )
    np.testing.assert_allclose(learner.prior_center(1), expected)
    np.testing.assert_allclose(learner.predict(version=1, context=1), expected)


def test_regression_permanently_stores_pre_outcome_law_feature():
    spec = learning.Spec("fingerprint_recent", "law", 2, 64)
    learner = learning.DecisionLearner(spec, contexts=4)
    law_before = np.array([0.25, 0.25, 0.25, 0.25])
    learner.observe(
        macro_index=0,
        action=learning.COOPERATIVE,
        version=0,
        context=0,
        estimated_law=law_before,
        outcome=3,
        reward=1,
    )
    law_before[:] = [0.1, 0.1, 0.1, 0.7]
    state = learner.export_state()
    np.testing.assert_array_equal(state["window_features"], [[0.25] * 4])
    np.testing.assert_array_equal(state["xtx"], np.full((4, 4), 0.25**2))


@pytest.mark.parametrize("representation", ["law", "cell", "hybrid"])
def test_recent_forgetting_uses_absolute_macro_time_and_expires_before_predict(
    representation,
):
    spec = learning.Spec("fingerprint_recent", representation, 2, 2)
    learner = learning.DecisionLearner(spec, contexts=4)
    law = np.full(4, 0.25)
    learner.observe(
        macro_index=0,
        action=learning.COOPERATIVE,
        version=0,
        context=0,
        estimated_law=law,
        outcome=0,
        reward=1,
    )
    # SAFE steps still advance absolute time, but never enter the cooperative window.
    learner.observe(
        macro_index=1,
        action=learning.SAFE,
        version=0,
        context=1,
        estimated_law=law,
        outcome=0,
        reward=0,
    )
    assert learner.expire_before(2) == 0  # retain indices t-window .. t-1
    assert learner.export_state()["window_macro_index"].tolist() == [0]
    assert learner.expire_before(3) == 1
    state = learner.export_state()
    assert state["window_macro_index"].size == 0
    if representation == "cell":
        assert state["cell_counts"].sum() == 0
        assert learner.expiration_recomputations == 0
    else:
        np.testing.assert_allclose(state["xtx"], 0.0, atol=1e-15)
        np.testing.assert_allclose(state["xty"], 0.0, atol=1e-15)
        assert learner.expiration_recomputations == 1


def test_safe_beta_is_identical_across_every_setting_and_has_mass_two():
    estimates = []
    law = np.full(4, 0.25)
    for spec in learning.development_specs():
        learner = learning.DecisionLearner(spec, contexts=4)
        for index, reward in enumerate((1, 0, 1)):
            learner.observe(
                macro_index=index,
                action=learning.SAFE,
                version=0,
                context=index % 4,
                estimated_law=law,
                outcome=0,
                reward=reward,
            )
        estimates.append(learner.predict(version=0, context=0, estimated_law=law)[0])
    np.testing.assert_array_equal(estimates, np.full(20, 3 / 5))


def test_only_cooperative_regression_block_is_solved():
    learner = learning.DecisionLearner(
        learning.Spec("fingerprint_full", "hybrid", 2), contexts=4
    )
    law = np.full(4, 0.25)
    learner.observe(
        macro_index=0,
        action=learning.SAFE,
        version=0,
        context=0,
        estimated_law=law,
        outcome=0,
        reward=1,
    )
    assert learner.solve_calls == 0
    learner.observe(
        macro_index=1,
        action=learning.COOPERATIVE,
        version=0,
        context=0,
        estimated_law=law,
        outcome=3,
        reward=1,
    )
    assert learner.solve_calls == 1
    assert learner.safe_updates == learner.cooperative_updates == 1
