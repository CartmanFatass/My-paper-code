"""One fresh .99-nearest-prior final1000 binding; earlier laws stay unchanged."""
from experiments.candidates.roster_consistent_latent_exploration.b04_nearest_prior import study as b04

host = b04.host
OBJECT_ID = "RCLE-TBCFV-B06-NEAREST99-PRIOR1000"
SEED = 26
UPDATES = 1000
LAW = {"nearest_probability": .99, "other_probability": .002,
       "distance_field": 76, "tie": "first candidate", "pointer_output_initially_zero": True}


def run(arm, out, launch_sha, admission_receipt, started, wall_cap, learned_summary=None, seed=SEED):
    return b04.run(arm, out, launch_sha, admission_receipt, started, wall_cap,
                   learned_summary, seed, updates=UPDATES, object_id=OBJECT_ID,
                   panel_label="B06", action_law=LAW)
