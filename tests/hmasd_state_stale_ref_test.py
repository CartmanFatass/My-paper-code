from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/hmasd_phase0/research_state.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_replace_rebinds_a_stale_research_direction_ref_with_revision_cas(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/hmasd_state.py", scripts / "hmasd_state.py")
    shutil.copy2(ROOT / "scripts/hmasd_platform.py", scripts / "hmasd_platform.py")
    shutil.copy2(ROOT / "scripts/hmasd_path_policy.py", scripts / "hmasd_path_policy.py")
    shutil.copytree(ROOT / "scripts/schemas", scripts / "schemas")

    direction_id = "alpha"
    direction_root = repo / "docs/research/candidates" / direction_id
    state_path = direction_root / "workflow/research/state.json"
    direction_path = direction_root / "DIRECTION.md"
    state_path.parent.mkdir(parents=True)
    direction_path.write_text("# Alpha revision 1\n", encoding="utf-8")

    registry_path = repo / "docs/research/portfolio/workflow/registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "directions": [
                    {
                        "id": direction_id,
                        "path": f"docs/research/candidates/{direction_id}",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    current = json.loads(FIXTURE.read_text(encoding="utf-8"))
    current.update(
        {
            "direction_id": direction_id,
            "writer": f"EM-{direction_id}",
            "revision": 1,
        }
    )
    current["direction_ref"] = {
        "path": f"docs/research/candidates/{direction_id}/DIRECTION.md",
        "sha256": sha256(direction_path),
    }
    state_path.write_text(json.dumps(current), encoding="utf-8")

    direction_path.write_text("# Alpha revision 2\n", encoding="utf-8")
    replacement = copy.deepcopy(current)
    replacement["revision"] = 2
    replacement["updated_at"] = "2026-08-27T00:00:00Z"
    replacement["direction_ref"]["sha256"] = sha256(direction_path)
    replacement_path = repo / "replacement.json"
    replacement_path.write_text(json.dumps(replacement), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(scripts / "hmasd_state.py"),
            "replace",
            "--kind",
            "research_state",
            "--path",
            str(state_path),
            "--writer",
            f"EM-{direction_id}",
            "--expected-revision",
            "1",
            "--input",
            str(replacement_path),
        ],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(state_path.read_text(encoding="utf-8")) == replacement
