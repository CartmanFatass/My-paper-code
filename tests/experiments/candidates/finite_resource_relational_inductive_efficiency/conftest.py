from __future__ import annotations

from copy import deepcopy

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core
from experiments.candidates.finite_resource_relational_inductive_efficiency.work import planned_work

@pytest.fixture
def manifest_factory(tmp_path):
    def make():
        compute = {"device": "cpu", "gpu": False, "model_dtype": "float32", "reduction_dtype": "float64", "native_width": 8, "workers": 1, "threads": 1, "network": False}
        return {
            "schema": core.FRRIE_MANIFEST_V2,
            "direction_id": core.DIRECTION_ID,
            "experiment_id": core.EXPERIMENT_ID,
            "host": {
                "id": core.HOST_ID, "source_id": core.SOURCE_ID,
                "component": core.NATIVE_COMPONENT, "abi": core.NATIVE_ABI,
                "binding_kind": core.NATIVE_BINDING_KIND,
                "native_required": True, "python_fallback": False,
            },
            "arms": [
                {"id": "PHY_TRUST", "learned": True, "evaluation_only": False, "beta_projection": [-0.15, 0.15], "parameter_count": 35_513},
                {"id": "EDGE_FLEX", "learned": True, "evaluation_only": False, "beta_projection": [-1.5, 1.5], "parameter_count": 35_513},
                {"id": "UNIFORM_LEGAL", "learned": False, "evaluation_only": True, "beta_projection": None, "parameter_count": 0},
            ],
            "cells": [
                *[{"purpose": "TRAIN", "roster": n, "intervention": "INTACT", "episodes": 32} for n in (9, 15)],
                *[{"purpose": "EVALUATE", "roster": n, "intervention": cut, "episodes": 256} for n in (9, 15, 6, 21) for cut in core.INTERVENTIONS],
            ],
            "compute": compute,
            "training": {
                "updates": 512,
                "episodes_per_update": 64,
                "rosters": [9, 15],
                "episodes_by_roster": {"9": 32, "15": 32},
                "episode_roster_order": [9, 15] * 32,
                "checkpoints": [512],
            },
            "evaluation": {"episodes_per_cell": 256, "adaptation": False, "seen_rosters": [9, 15], "heldout_rosters": [6, 21], "interventions": list(core.INTERVENTIONS)},
            "seed_blocks": list(core.REQUIRED_SEED_BLOCKS),
            "sealed_seed_packet": {"path": str(tmp_path / "packet.json")},
            "preflight_receipt": {"path": str(tmp_path / "preflight.json")},
            "thresholds": deepcopy(core.THRESHOLDS),
            "inference": deepcopy(core.INFERENCE_CONTRACT),
            "implementation_contract": deepcopy(core.IMPLEMENTATION_CONTRACT),
            "roots": {"output": str(tmp_path / "run" / "output"), "checkpoint": str(tmp_path / "run" / "checkpoint")},
            "fixture_contracts": deepcopy(core.FIXTURE_CONTRACTS),
            "planned_work": planned_work(compute),
            "resource_ceiling": {"wall_seconds": 1, "cpu_core_hours": 1, "rss_bytes": 1, "scratch_bytes": 1, "durable_bytes": 1},
        }
    return make
