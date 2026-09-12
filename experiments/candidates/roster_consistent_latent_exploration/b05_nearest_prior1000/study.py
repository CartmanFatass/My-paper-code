"""Fresh final1000 binding; the B04 defaults and master24 command stay at200."""
from experiments.candidates.roster_consistent_latent_exploration.b04_nearest_prior import study as b04

host = b04.host
OBJECT_ID = "RCLE-TBCFV-B05-NEAREST-PRIOR1000"
SEED = 25
UPDATES = 1000


def run(arm, out, launch_sha, admission_receipt, started, wall_cap, learned_summary=None, seed=SEED):
    return b04.run(arm, out, launch_sha, admission_receipt, started, wall_cap,
                   learned_summary, seed, updates=UPDATES, object_id=OBJECT_ID, panel_label="B05")
