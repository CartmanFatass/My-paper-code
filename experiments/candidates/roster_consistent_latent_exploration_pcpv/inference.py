"""Registered 70-tail inference, gates, and literal first-match map."""

from __future__ import annotations

import math
from typing import Callable, Mapping, Sequence

from .config import CHURN_CELLS, EVAL_CELLS, REGISTERED_TAILS, T_CRITICAL, cell_name


def interval(values: Sequence[float]) -> dict[str, float]:
    if len(values) != 16 or not all(math.isfinite(float(x)) for x in values):
        raise ValueError("each registered root quantity must contain 16 finite values")
    mean = sum(float(x) for x in values) / 16.0
    variance = sum((float(x) - mean) ** 2 for x in values) / 15.0
    spread = T_CRITICAL * math.sqrt(variance) / 4.0
    return {"mean": mean, "lower": mean - spread, "upper": mean + spread}


def _values(panel: Mapping, package: str, cell: tuple[int, int], endpoint: str):
    name = cell_name(cell)
    return [panel[root][package][name][endpoint] for root in sorted(panel)]


def _contrast(panel: Mapping, left: str, right: str, cell: tuple[int, int],
              endpoint: str, offset: float = 0.0):
    a = _values(panel, left, cell, endpoint)
    b = _values(panel, right, cell, endpoint)
    return [x - y - offset for x, y in zip(a, b)]


def stage_a_inference(panel: Mapping) -> dict[str, object]:
    tails: dict[str, dict[str, float]] = {}
    for cell in CHURN_CELLS:
        name = cell_name(cell)
        tails[f"assay/{name}/time"] = interval(
            _contrast(panel, "FRAGMENTED", "CARRY", cell, "tau", 3.0))
        tails[f"assay/{name}/loss"] = interval(
            _contrast(panel, "FRAGMENTED", "CARRY", cell, "U", 0.03))
    for cell in EVAL_CELLS:
        name = cell_name(cell)
        transforms = {
            "carry_time": [12.0 - x for x in _values(panel, "CARRY", cell, "tau")],
            "carry_loss": [0.08 - x for x in _values(panel, "CARRY", cell, "U")],
            "replan_time": [12.0 - x for x in _values(panel, "REPLAN", cell, "tau")],
            "replan_loss": [0.08 - x for x in _values(panel, "REPLAN", cell, "U")],
            "carry_vs_nearest_time": _contrast(panel, "NEAREST", "CARRY", cell, "tau", 2.0),
            "carry_vs_nearest_loss": _contrast(panel, "NEAREST", "CARRY", cell, "U", 0.02),
        }
        for key, values in transforms.items():
            tails[f"scaffold/{name}/{key}"] = interval(values)
    for cell in CHURN_CELLS:
        name = cell_name(cell)
        tails[f"physical/{name}/time"] = interval(
            _contrast(panel, "REPLAN", "CARRY", cell, "tau"))
        tails[f"physical/{name}/loss"] = interval(
            _contrast(panel, "REPLAN", "CARRY", cell, "U"))
    assay = all(value["lower"] > 0.0 for key, value in tails.items()
                if key.startswith("assay/"))
    scaffold = all(value["lower"] > 0.0 for key, value in tails.items()
                   if key.startswith("scaffold/"))
    physical_paths = []
    for winner in CHURN_CELLS:
        other = CHURN_CELLS[1] if winner == CHURN_CELLS[0] else CHURN_CELLS[0]
        if (tails[f"physical/{cell_name(winner)}/time"]["lower"] > 1.5 and
            tails[f"physical/{cell_name(other)}/time"]["lower"] > -0.5 and
            all(tails[f"physical/{cell_name(c)}/loss"]["lower"] > -0.005
                for c in CHURN_CELLS)):
            physical_paths.append(cell_name(winner))
    physical = bool(physical_paths)
    if len(tails) != 32:
        raise AssertionError("Stage-A must register exactly 32 tails")
    branch = ("ASSAY_SENSITIVITY_NOT_ESTABLISHED" if not assay else
              "PUBLIC_SCAFFOLD_NOT_ESTABLISHED" if not scaffold else
              "PHYSICAL_PERSISTENCE_OPPORTUNITY_NOT_ESTABLISHED"
              if not physical else "STAGE_B_REQUIRED")
    return {"tails": tails, "assay_sensitivity": assay,
            "public_scaffold": scaffold,
            "physical_persistence_opportunity": physical,
            "physical_winning_paths": physical_paths, "branch": branch}


def complete_inference(stage_a_panel: Mapping, learned_panel: Mapping,
                       physical_paths: Sequence[str], valid: bool = True) -> dict[str, object]:
    if not valid:
        return {"branch": "INVALID_OR_INCOMPLETE", "tails": {}}
    stage_a = stage_a_inference(stage_a_panel)
    tails = dict(stage_a["tails"])
    if stage_a["branch"] != "STAGE_B_REQUIRED":
        return {"branch": stage_a["branch"], "tails": tails,
                "flex_competence": False}
    for cell in EVAL_CELLS:
        name = cell_name(cell)
        transforms = {
            "absolute_time": [16.0 - x for x in _values(learned_panel, "FLEX", cell, "tau")],
            "absolute_loss": [0.12 - x for x in _values(learned_panel, "FLEX", cell, "U")],
            "vs_nearest_time": _contrast_mixed(stage_a_panel, "NEAREST", learned_panel, "FLEX", cell, "tau", 2.0),
            "vs_nearest_loss": _contrast_mixed(stage_a_panel, "NEAREST", learned_panel, "FLEX", cell, "U", 0.02),
        }
        for key, values in transforms.items():
            tails[f"flex/{name}/{key}"] = interval(values)
    for cell in CHURN_CELLS:
        name = cell_name(cell)
        for endpoint, label in (("tau", "time"), ("U", "loss")):
            values = _contrast(learned_panel, "FLEX", "KEEP", cell, endpoint)
            tails[f"direct/{name}/{label}/lower"] = interval(values)
            tails[f"direct/{name}/{label}/upper"] = tails[f"direct/{name}/{label}/lower"]
        tails[f"fragmentation/{name}"] = interval(
            _contrast(learned_panel, "FLEX", "KEEP", cell, "F"))
        for left, right, prefix in (("FLEX", "CLAMP", "rekey"),
                                    ("CLAMP", "KEEP", "backbone")):
            for endpoint, label in (("tau", "time"), ("U", "loss")):
                values = _contrast(learned_panel, left, right, cell, endpoint)
                stats = interval(values)
                if prefix == "rekey":
                    tails[f"clamp/{name}/{prefix}_{label}/lower"] = stats
                else:
                    tails[f"clamp/{name}/{prefix}_{label}/lower"] = stats
                    tails[f"clamp/{name}/{prefix}_{label}/upper"] = stats
    if len(tails) != REGISTERED_TAILS:
        raise AssertionError(f"expected 70 registered tails, got {len(tails)}")
    competence = all(value["lower"] > 0.0 for key, value in tails.items()
                     if key.startswith("flex/"))
    if not competence:
        return {"branch": "FLEX_COMPETENCE_NOT_ESTABLISHED", "tails": tails,
                "flex_competence": False}
    keep_paths = _directional_paths(tails, "direct", lower=True)
    flex_win = _mirror_win(tails)
    no_material = _inside_direct(tails, "direct")
    backbone_keep = bool(_directional_paths(tails, "clamp", lower=True,
                                            stem="backbone"))
    rekey = False
    for path in set(keep_paths).intersection(physical_paths):
        if (tails[f"clamp/{path}/rekey_time/lower"]["lower"] > 1.0 and
            tails[f"clamp/{path}/rekey_loss/lower"]["lower"] > -0.01 and
            tails[f"fragmentation/{path}"]["lower"] > 0.03 and
            _inside_direct(tails, "clamp", stem="backbone")):
            rekey = True
    branch = ("KEEP_TARGET_ALIGNED_REKEY_VALUE" if keep_paths and rekey else
              "KEEP_TRAINING_GEOMETRY_VALUE" if keep_paths and backbone_keep else
              "KEEP_PACKAGE_ONLY" if keep_paths else
              "FLEX_CONTAINING_SUPERIOR" if flex_win else
              "FRAGMENTATION_WITHOUT_DIRECT_VALUE" if no_material and any(
                  tails[f"fragmentation/{cell_name(c)}"]["lower"] > 0.03
                  for c in CHURN_CELLS) else
              "TARGET_SPECIFIC_NO_MATERIAL" if no_material else
              "TARGET_UNRESOLVED")
    return {"branch": branch, "tails": tails, "flex_competence": competence,
            "keep_winning_paths": keep_paths, "rekey_application_localized": rekey,
            "training_geometry_persists": backbone_keep}


def _contrast_mixed(left_panel, left, right_panel, right, cell, endpoint, offset):
    a = _values(left_panel, left, cell, endpoint)
    b = _values(right_panel, right, cell, endpoint)
    return [x - y - offset for x, y in zip(a, b)]


def _directional_paths(tails, prefix, lower=True, stem=None):
    paths = [cell_name(c) for c in CHURN_CELLS]
    out = []
    for winner in paths:
        other = paths[1] if winner == paths[0] else paths[0]
        key = (lambda p, e: f"{prefix}/{p}/{stem}_{e}/lower" if stem else
               f"{prefix}/{p}/{e}/lower")
        if (tails[key(winner, "time")]["lower"] > 2.0 and
            tails[key(other, "time")]["lower"] > -1.0 and
            all(tails[key(p, "loss")]["lower"] > -0.01 for p in paths)):
            out.append(winner)
    return out


def _mirror_win(tails):
    paths = [cell_name(c) for c in CHURN_CELLS]
    for winner in paths:
        other = paths[1] if winner == paths[0] else paths[0]
        if (tails[f"direct/{winner}/time/upper"]["upper"] < -2.0 and
            tails[f"direct/{other}/time/upper"]["upper"] < 1.0 and
            all(tails[f"direct/{p}/loss/upper"]["upper"] < 0.01 for p in paths)):
            return True
    return False


def _inside_direct(tails, prefix, stem=None):
    for path in (cell_name(c) for c in CHURN_CELLS):
        for endpoint, bound in (("time", 1.0), ("loss", 0.01)):
            base = f"{prefix}/{path}/{stem}_{endpoint}" if stem else f"{prefix}/{path}/{endpoint}"
            if not (tails[f"{base}/lower"]["lower"] >= -bound and
                    tails[f"{base}/upper"]["upper"] <= bound):
                return False
    return True
