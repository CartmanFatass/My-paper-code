"""Selected B01 scientific inputs; no runtime sweep dimensions."""

DIRECTION = "uav_joint_transition"
HORIZON = 3000
CLOCK = 30
N_ENVS = 2
POLICY_SEED = 62092871
TRAIN_SEEDS = tuple(range(62092801, 62092865))
EVAL_SEEDS = tuple(range(62102801, 62102809))
ARMS = ("L", "O", "R", "P")
ROLLOUT_STEPS = 100
ROLLOUTS = 32
TOTAL_MACRO_STEPS = 6400
OPTIMIZER_STEPS = 256
MAX_RADIO_QUERIES = 1312000
MAX_PREDICTION_TEAM_TICKS = 9864000


def lane_seeds(lane):
    if lane not in range(N_ENVS):
        raise ValueError("invalid training lane")
    return TRAIN_SEEDS[lane::N_ENVS]


def evaluation_plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for arm in ARMS for seed in EVAL_SEEDS]
