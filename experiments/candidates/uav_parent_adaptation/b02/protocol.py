"""Frozen B02 full-continuation exposure and the deliberately reused train streams."""

from experiments.candidates.uav_parent_adaptation.b01 import protocol as b01

HORIZON, TRAIN, EVAL = 256, 512, 32
LINEAGES = (1, 2, 3)
PROGRAMS = ("P", "U", "K", "D")
FIRST_MASTER = 29813
PARENT_SOURCE = "930a0789dad4adbba67592c5fff07802a3dd40c2"
PARENT_SUMMARY_SHA256 = "02ad55031ca64e58ea03582ba7bcb18825f01568dc8f1cb8613ede793240948b"
PARENT_ROOT = "/home/wu/projects/HMASD/runs/uav_parent_adaptation/b01_unscreened_a01"
WITNESS_FIELDS = ("initial_scene_sha256", "channel_sequence_sha256", "motion_rng_start_sha256",
                  "motion_rng_end_sha256", "innovation_sha256", "innovation_vectors")


def masters(lineage):
    if type(lineage) is not int or lineage not in LINEAGES:
        raise ValueError("B02 has exactly three retained lineages")
    return dict(U=29803 + 10 * lineage, evaluation=29805 + 10 * lineage)


def addresses(lineage, phase, *, train=TRAIN, evaluation=EVAL):
    if phase == "U":
        return b01.addresses(lineage, "K", train=train)
    if phase != "evaluation":
        raise ValueError("B02 has U training and final evaluation only")
    base = 100000 * masters(lineage)["evaluation"]
    return dict(master=base // 100000, scene_start=base + 2000,
                scene_end=base + 2000 + evaluation - 1, channel_start=base + 7000,
                channel_end=base + 7000 + evaluation - 1, motion_start=base + 3000,
                motion_end=base + 3000 + evaluation - 1, motion_mode="fresh_per_episode")


def rng_table():
    return {str(lineage): {phase: addresses(lineage, phase) for phase in ("U", "evaluation")}
            for lineage in LINEAGES}


def rotating_order(world):
    offset = world % len(PROGRAMS)
    return PROGRAMS[offset:] + PROGRAMS[:offset]


def expected_training_counts(horizon=HORIZON, train=TRAIN):
    return b01.expected_training_counts("B", horizon, train)


def expected_evaluation_counts(horizon=HORIZON, evaluation=EVAL):
    return b01.expected_evaluation_counts(horizon, evaluation)
