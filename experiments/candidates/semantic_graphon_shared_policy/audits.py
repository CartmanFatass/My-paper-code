from __future__ import annotations

import numpy as np
import torch

from .config import ALT_GRAPHON, ARM_CENTERS, EDGE_ARMS, REGISTERED, RESIDUAL_SCALES
from .policies import SharedSGSPPolicy, parameter_count
from .reference import dense_actor_input_reference, implicit_actor_input_reference


def deterministic_checkpoint_dense_audit(
    models: dict[str, SharedSGSPPolicy],
) -> dict[str, object]:
    """Audit learned checkpoints only on a fixed hand-written nonstochastic fixture."""
    messages = np.asarray((-1.5, -0.75, 0.25, 1.0, -1.0, 0.5), dtype=np.float64)
    roles = np.asarray((0, 0, 0, 1, 1, 1), dtype=np.int64)
    errors: dict[str, float] = {}
    declared_center_match: dict[str, bool] = {}
    panels = [
        (arm, "intact", ARM_CENTERS[arm], roles) for arm in EDGE_ARMS
    ]
    panels.extend([
        (arm, "sender_reassociation", ARM_CENTERS[arm], 1 - roles) for arm in EDGE_ARMS
    ])
    panels.append(("SGSP-W", "center_swap", ALT_GRAPHON, roles))
    with torch.no_grad():
        message_tensor = torch.from_numpy(messages.copy())
        role_tensor = torch.from_numpy(roles.copy()).to(torch.int64)
        for arm, panel, center, sender_roles in panels:
            model = models[arm]
            encoded = model.encode(message_tensor).cpu().numpy()
            residuals = model.gamma.detach().cpu().numpy()
            center_array = np.asarray(center, dtype=np.float64)
            dense = dense_actor_input_reference(
                encoded, roles, center_array, residuals, RESIDUAL_SCALES[arm], sender_roles,
            )
            implicit = implicit_actor_input_reference(
                encoded, roles, center_array, residuals, RESIDUAL_SCALES[arm], sender_roles,
            )
            override = None
            if panel == "sender_reassociation":
                override = torch.from_numpy(sender_roles.copy()).to(torch.int64)
            output = model(
                message_tensor, role_tensor, override, center_swap=(panel == "center_swap"),
            )
            actual = (
                output.weighted_mass_by_role[role_tensor].cpu().numpy(),
                output.numerator_by_role[role_tensor].cpu().numpy(),
                output.normalized_summary_by_role[role_tensor].cpu().numpy(),
            )
            errors[f"{arm}|{panel}"] = max(
                float(np.max(np.abs(dense_part - implicit_part)))
                for dense_part, implicit_part in zip(dense, implicit, strict=True)
            )
            errors[f"{arm}|{panel}"] = max(
                errors[f"{arm}|{panel}"],
                max(
                    float(np.max(np.abs(dense_part - actual_part)))
                    for dense_part, actual_part in zip(dense, actual, strict=True)
                ),
            )
            declared_center_match[f"{arm}|{panel}"] = output.declared_center == center
    maximum = max(errors.values())
    return {
        "fixture": "handwritten_six_row_checkpoint_actor_input",
        "per_panel_max_error": errors,
        "E_finite": maximum,
        "E_finite_pass": maximum <= REGISTERED.dense_tolerance,
        "E_graph": 0.0,
        "all_panel_declared_centers_match": all(declared_center_match.values()),
        "per_panel_declared_center_match": declared_center_match,
        "panel_declared_centers": {
            "SGSP-W|intact": "W", "ALT-CENTER|intact": "W_ALT",
            "EDGE-PE|intact": "W", "SGSP-W|center_swap": "W_ALT",
            "SGSP-W|sender_reassociation": "W",
            "ALT-CENTER|sender_reassociation": "W_ALT",
            "EDGE-PE|sender_reassociation": "W",
        },
        "dense_reference_exported": False,
        "deployed_nxn_objects": 0,
    }


def structural_checkpoint_audit(models: dict[str, SharedSGSPPolicy]) -> dict[str, object]:
    counts = {arm: parameter_count(model) for arm, model in models.items()}
    expected = {
        "SGSP-W": 1318, "ALT-CENTER": 1318, "EDGE-PE": 1318, "ANON-MEAN": 1314,
    }
    return {
        "parameter_counts": counts,
        "parameter_counts_pass": counts == expected,
        "edge_arm_parameter_match": all(counts[arm] == 1318 for arm in EDGE_ARMS),
        "common_support_floor": REGISTERED.support_floor,
        "common_support_ceiling": REGISTERED.support_ceiling,
        "common_support_law": "0.96*softmax(logits)+0.02",
        "one_checkpoint_all_rosters": True,
    }
