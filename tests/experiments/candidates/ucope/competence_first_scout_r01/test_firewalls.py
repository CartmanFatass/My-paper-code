from pathlib import Path

import pytest

from experiments.candidates.ucope.competence_first_scout_r01.artifact import atomic_create_json
from experiments.candidates.ucope.competence_first_scout_r01.workflow import validate_scratch_fence


def test_consumed_artifact_path_fence_and_create_once(tmp_path):
    with pytest.raises(ValueError):
        validate_scratch_fence(tmp_path / "contextual_paid_acquisition_r01" / "result")
    path = tmp_path / "artifact.json"
    atomic_create_json(path, {"complete": False})
    with pytest.raises(FileExistsError):
        atomic_create_json(path, {"complete": True})


def test_new_package_has_no_consumed_package_imports():
    root = Path("experiments/candidates/ucope/competence_first_scout_r01")
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "from experiments.candidates.ucope.contextual_paid_acquisition_r01" not in source
    assert "from ..contextual_paid_acquisition_r01" not in source
