"""Fresh fixed confirmation; scientific per-block work is inherited unchanged."""

import json
import time
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t
import torch

from experiments.candidates.vsp_03.opportunity_b08.study import (
    ARMS, CONTRASTS, EVAL_EPISODES, TRAIN_BATCH, UPDATES, train_and_evaluate,
)
from experiments.candidates.vsp_03.vsp03_b01.b01 import peak_rss, write_json


SEEDS = (21901, 21902, 21903, 21904, 21905)


def aggregate(blocks):
    if [b["seed"] for b in blocks] != list(SEEDS) or any(b["status"] != "complete" for b in blocks):
        raise ValueError("confirmation requires all five fixed complete blocks in order")
    result = {}
    for left, right in (("O", "G"), *CONTRASTS):
        key = left + "-" + right
        source = "G-O" if key == "O-G" else key
        sign = -1 if key == "O-G" else 1
        values = np.array([sign * b["comparisons"][source]["mean"] for b in blocks])
        mean, sd = float(values.mean()), float(values.std(ddof=1))
        half = float(student_t.ppf(.975, 4)) * sd / np.sqrt(5)
        result[key] = {"per_block": values.tolist(), "mean": mean, "between_block_sd": sd,
                       "independent_blocks": 5, "t95": [mean - half, mean + half], "df": 4,
                       "scope": "primary" if key == "O-G" else "descriptive_secondary"}
    lower, upper = result["O-G"]["t95"]
    reading = "O_SUPERIOR" if lower > 0 else "G_SUPERIOR" if upper < 0 else "INCONCLUSIVE"
    return result, {"label": reading, "primary": "O-G", "practical_reference_J": .02,
                    "lower_bound_above_practical_reference": bool(lower > .02),
                    "no_equivalence_claim": True,
                    "assumption": "independent approximately normal block contrasts; five fresh blocks"}


def run(out, launch_sha, seeds=SEEDS):
    if tuple(seeds) != SEEDS:
        raise ValueError("B09 fixes five new seeds 21901 through 21905")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    config = {"object": "VSP03_FITTED_OPPORTUNITY_CONFIRMATION_B09", "seeds": list(SEEDS),
              "launch_sha": launch_sha, "arms": list(ARMS), "training_updates": UPDATES,
              "episodes_per_update": TRAIN_BATCH, "evaluation_episodes_per_arm_per_block": EVAL_EPISODES,
              "planned_fits": 10, "G_fits": 5, "O_transition_model_fits": 5,
              "planned_unique_training_episodes": 5 * UPDATES * TRAIN_BATCH,
              "planned_evaluation_episodes": 5 * len(ARMS) * EVAL_EPISODES,
              "planned_team_ticks": 5 * (UPDATES * TRAIN_BATCH + len(ARMS) * EVAL_EPISODES) * 40,
              "scientific_block_implementation": "opportunity_b08.study.train_and_evaluate (unchanged)",
              "primary": "final512:O-G", "selection": "none after B08; no development blocks pooled",
              "claim": "docs/research/candidates/vsp_03/CLAIM_fitted_opportunity_b09.md",
              "threads": 1, "device": "cpu", "G_dtype": "float32", "O_dtype": "float64"}
    write_json(out / "config.json", config)
    summary = {**config, "status": "incomplete", "blocks": [], "technical_failures": []}
    start = time.perf_counter()
    try:
        for seed in seeds:
            try:
                block = train_and_evaluate(seed, out / str(seed), launch_sha)
                summary["blocks"].append(block)
                print(json.dumps({"seed": seed, "status": "complete",
                                  "O-G": -block["comparisons"]["G-O"]["mean"]}), flush=True)
            except Exception as exc:
                summary["technical_failures"].append({"seed": seed, "error": repr(exc)})
                raise
        summary["comparisons"], summary["reading"] = aggregate(summary["blocks"])
        summary["status"] = "complete"
    finally:
        summary["study_wall_s_through_publication_start"] = time.perf_counter() - start
        summary["peak_rss_bytes"] = peak_rss()
        summary["peak_rss_scope"] = "single research process lifetime maximum"
        retained = [json.loads((out / str(seed) / "summary.json").read_text())
                    for seed in seeds if (out / str(seed) / "summary.json").exists()]
        summary["fits_started"] = {a: sum(b["fits_started"][a] for b in retained) for a in ("G", "O")}
        summary["fits_completed"] = {a: sum(b["fits_completed"][a] for b in retained) for a in ("G", "O")}
        write_json(out / "summary.json", summary)
    return summary
