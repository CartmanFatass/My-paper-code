from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.tapes import (
    production_training_inputs,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.tape_isolation_a03 import (
    tape_digest,
    training_inputs_no_torch,
)

REPO = Path(__file__).resolve().parents[4]
ROOT = bytes.fromhex("00" * 31 + "01")
LABEL = "FRRIE-B09-CONTACT-BLOCK-003"
ARRAYS = (
    "event_times",
    "detection_uniform",
    "uplink_uniform",
    "base_uniform",
    "action_uniform",
)
SCALARS = ("seed_block", "purpose", "roster", "update", "episode")


def test_training_inputs_no_torch_match_production_and_omit_torch():
    probe = (
        "import sys\n"
        "from experiments.candidates.finite_resource_relational_inductive_efficiency"
        ".tape_isolation_a03 import training_inputs_no_torch\n"
        "root = bytes.fromhex('00' * 31 + '01')\n"
        "tapes = training_inputs_no_torch(root, 'FRRIE-B09-CONTACT-BLOCK-003', 1)\n"
        "assert len(tapes) == 64\n"
        "print('torch' in sys.modules)\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip().splitlines()[-1] == "False"

    ours = training_inputs_no_torch(ROOT, LABEL, 1)
    theirs, _origins = production_training_inputs(ROOT, LABEL, 1)
    assert len(ours) == len(theirs) == 64
    for left, right in zip(ours, theirs):
        for name in SCALARS:
            assert getattr(left, name) == getattr(right, name)
        for name in ARRAYS:
            np.testing.assert_array_equal(getattr(left, name), getattr(right, name))
            assert getattr(left, name).dtype == getattr(right, name).dtype
    assert tape_digest(ours) == tape_digest(ours)
    assert tape_digest(ours) == tape_digest(theirs)
