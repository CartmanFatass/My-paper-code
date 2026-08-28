from scripts import hmasd_host_compat


def test_default_prefixes_use_only_current_state_fixtures() -> None:
    assert "tests/fixtures/hmasd_state/" in hmasd_host_compat.DEFAULT_PREFIXES
    assert all("phase0" not in prefix for prefix in hmasd_host_compat.DEFAULT_PREFIXES)
