"""Fixed prospective B01 identities and exposure."""

HORIZON = 3000
MACRO_STEPS = 30
POLICY_SEED = 5292801
TRAIN_SEEDS = tuple(range(52092801, 52092865))
EVAL_SEEDS = tuple(range(52192801, 52192817))
N_ENVS = 4
N_ACTIONS = 25
ARMS = ("L", "O", "P")
ROLLOUTS = 16
ROLLOUT_STEPS = 100
OPTIMIZER_STEPS = 640
DIRECTION = "uav_persistent_service"
BATCH = "b01_commitment_a01"


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in EVAL_SEEDS for arm in ARMS]


def lane_seeds(lane):
    if lane not in range(N_ENVS):
        raise ValueError("lane outside the fixed four-lane schedule")
    return TRAIN_SEEDS[lane::N_ENVS]
