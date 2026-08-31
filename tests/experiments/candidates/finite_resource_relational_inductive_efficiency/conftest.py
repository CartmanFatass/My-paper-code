from __future__ import annotations

from copy import deepcopy

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core

@pytest.fixture
def manifest_factory(tmp_path):
    def make(*, blocks=("FRRIE-FRESH-BLOCK-001",), checkpoints=(512,)):
        work = {
            "environment_slots": 1, "learned_decisions": 1, "backward_calls": 512,
            "adam_steps": 512, "parameter_bytes": 35_513 * 4, "flops": 1,
            "workers": 1, "threads": 1, "native_width": 8, "dtype": "float32",
            "checkpoint_io": len(checkpoints), "evaluation_opportunities": len(checkpoints) * 8 * 256,
        }
        return {
            "schema": core.FRRIE_MANIFEST_V1,
            "direction_id": core.DIRECTION_ID,
            "experiment_id": core.EXPERIMENT_ID,
            "host": {
                "id": core.HOST_ID, "source_id": core.SOURCE_ID,
                "component": core.NATIVE_COMPONENT, "abi": core.NATIVE_ABI,
                "binding_kind": "FRRIE_NATIVE_CTYPES_V1",
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
            "compute": {"device": "cpu", "gpu": False, "model_dtype": "float32", "reduction_dtype": "float64", "native_width": 8, "workers": 1, "threads": 1, "network": False},
            "training": {"updates": 512, "episodes_per_update": 64, "rosters": [9, 15], "episodes_by_roster": {"9": 32, "15": 32}, "checkpoints": list(checkpoints)},
            "evaluation": {"episodes_per_cell": 256, "adaptation": False, "seen_rosters": [9, 15], "heldout_rosters": [6, 21], "interventions": list(core.INTERVENTIONS)},
            "seed_blocks": list(blocks),
            "sealed_seed_packet": {"path": str(tmp_path / "packet.json")},
            "preflight_receipt": {"path": str(tmp_path / "preflight.json")},
            "thresholds": {field: 0.0 for field in core.THRESHOLD_FIELDS},
            "generic_competence": {"heldout_direct_return_lower": 0.0, "seen_direct_return_lower": 0.0, "worst_basin_delivery_lower": 0.0, "legal_action_validity_lower": 0.0},
            "work_to_threshold": {"metric": "native_endpoint_J", "thresholds_by_roster": {"9": 0.1, "15": 0.1, "6": 0.1, "21": 0.1}, "checkpoints": list(checkpoints), "crossing_rule": "FIRST_PROSPECTIVE_CHECKPOINT_GE_THRESHOLD"},
            "roots": {"output": str(tmp_path / "out"), "checkpoint": str(tmp_path / "ckpt")},
            "fixture_contracts": deepcopy(core.FIXTURE_CONTRACTS),
            "work_parity": {"PHY_TRUST": dict(work), "EDGE_FLEX": dict(work)},
            "resource_ceiling": {"wall_seconds": 1, "cpu_core_hours": 1, "rss_bytes": 1, "scratch_bytes": 1, "durable_bytes": 1},
        }
    return make
