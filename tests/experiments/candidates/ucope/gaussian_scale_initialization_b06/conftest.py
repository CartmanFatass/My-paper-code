import pytest


@pytest.fixture
def admission():
    return {
        "schema_version": 1,
        "direction": "ucope",
        "sha": "admitted-b06-sha",
        "command_sha256": "command-digest",
        "parent_pid": 41,
        "child_pid": 42,
        "accepted_at_epoch": 123.5,
    }
