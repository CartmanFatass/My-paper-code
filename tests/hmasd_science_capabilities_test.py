from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import hmasd_science_capabilities as capabilities


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_is_minimal_and_unique() -> None:
    catalog = capabilities.load_catalog(ROOT / "configs/scientific-capabilities-v1.toml")
    identifiers = [item["capability"] for item in catalog["capability"]]
    assert len(identifiers) == len(set(identifiers))
    assert {item["status"] for item in catalog["capability"]} == {"active", "unavailable"}
    assert all(set(item) == capabilities.FIELDS for item in catalog["capability"])



def test_paper_lookup_distinguishes_repository_tool_from_installed_adapter() -> None:
    catalog = capabilities.load_catalog(ROOT / "configs/scientific-capabilities-v1.toml")
    paper_lookup = next(
        item for item in catalog["capability"] if item["capability"] == "paper-lookup"
    )
    assert paper_lookup["status"] == "unavailable"
    assert paper_lookup["entrypoint"] == ""
    assert paper_lookup["environment"] == ""
    assert "Repository-local hmasd-paper-lookup skill/tool surface" in paper_lookup["purpose"]
    assert "no dedicated installed" in paper_lookup["purpose"]


def test_cli_list_show_and_doctor_are_observation_only() -> None:
    list_result = subprocess.run(
        [sys.executable, "scripts/hmasd_science_capabilities.py", "list"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert list_result.returncode == 0, list_result.stderr
    assert json.loads(list_result.stdout)["capabilities"]
    show = subprocess.run(
        [sys.executable, "scripts/hmasd_science_capabilities.py", "show", "--id", "networkx"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert json.loads(show.stdout)["status"] == "active"
    doctor = subprocess.run(
        [sys.executable, "scripts/hmasd_science_capabilities.py", "doctor", "--id", "wolfram"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert json.loads(doctor.stdout)["observed"]["available"] is False
    active_doctor = subprocess.run(
        [sys.executable, "scripts/hmasd_science_capabilities.py", "doctor", "--id", "networkx"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    observed = json.loads(active_doctor.stdout)["observed"]
    assert active_doctor.returncode == 0
    assert observed["available"] is True
    assert observed["version"].startswith("Python ")
