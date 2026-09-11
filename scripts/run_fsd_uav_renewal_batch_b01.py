"""I1280/D0 binding; real execution requires a separate allocation.

The retained CLI/summary arm ``I`` means I1280 only under this new object ID.
Prospective whole-command caps are D0 900s and I1280 1800s; they are unallocated.
"""
import run_fsd_uav_individual_renewal_b01 as shared

TRAINING_SEED, EVALUATION_SEED = 770703, 780703
OBJECT_ID = "FSD_UAV_RENEWAL_BATCH_B01"
CARD = "docs/research/candidates/flexible_skill_duration/" + OBJECT_ID + "_DESIGN_CARD_20260910.md"
CAPS = {"D0": 900., "I": 1800.}


def make_config(arm, envs, seed):
    return shared.make_config(arm, envs, seed, renewal_batch=True)


def assemble_pair(treatment, control):
    return shared.assemble_pair(treatment, control, training_seed=TRAINING_SEED,
        evaluation_seed=EVALUATION_SEED, object_id=OBJECT_ID, card=CARD, renewal_batch=True)


def main(argv=None):
    return shared.main(argv, training_seed=TRAINING_SEED, evaluation_seed=EVALUATION_SEED,
                       object_id=OBJECT_ID, card=CARD, renewal_batch=True, caps=CAPS)


if __name__ == "__main__":
    raise SystemExit(main())
