from tools.hmasd_control_plane.runtime_plausibility import EstimateBasis, RuntimeDisposition, RuntimeSample, assess_runtime


def sample(profile, wall_seconds, basis=EstimateBasis.MEASURED):
    return RuntimeSample(profile, basis, 500, 1, 1, wall_seconds, "cpp", True, 2, 1, 500)


def test_speculative_is_unvalidated_e0():
    result = assess_runtime(sample("TOY_SMOKE", 1, EstimateBasis.SPECULATIVE))
    assert result.disposition is RuntimeDisposition.UNVALIDATED_ESTIMATE
    assert result.incident_level == "E0_OBSERVATION"


def test_toy_multiday_estimate_routes_to_cm():
    result = assess_runtime(sample("TOY_SMOKE", 30 * 86400 / 500))
    assert result.disposition is RuntimeDisposition.PERFORMANCE_IMPLEMENTATION_ANOMALY
    assert result.incident_level == "E2_ASSIGNMENT_RECOVERY"
    assert result.route_to == "CM"
    assert not result.user_authority_required


def test_formal_long_runtime_is_review_not_scientific_stop():
    result = assess_runtime(sample("FORMAL_ITERATION", 9 * 3600))
    assert result.disposition is RuntimeDisposition.OPTIMIZATION_REVIEW
    assert result.route_to == "CM"
