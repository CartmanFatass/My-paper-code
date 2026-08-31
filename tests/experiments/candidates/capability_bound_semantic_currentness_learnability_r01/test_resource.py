from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.resource import peak_rss_bytes


def test_dependency_free_peak_rss_is_positive_and_nondecreasing() -> None:
    before = peak_rss_bytes()
    material = bytearray(1024 * 1024)
    material[0] = 1
    after = peak_rss_bytes()
    assert before > 0
    assert after >= before
