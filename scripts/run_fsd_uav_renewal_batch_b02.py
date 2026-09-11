"""Fresh allocated I1280/D0 pair; CLI/summary arm I means I1280.

Fresh allocation at Portfolio response6c32ade; old770803 allocation stays ended. Complete command
caps are D0 900s and I1280 1800s, including the sole final endpoint/publication.
"""
import run_fsd_uav_individual_renewal_b01 as shared

TRAINING_SEED, EVALUATION_SEED = 770903, 780903
OBJECT_ID = "FSD_UAV_RENEWAL_BATCH_B02_770903"
CARD = "docs/research/candidates/flexible_skill_duration/FSD_UAV_RENEWAL_BATCH_B02_SCIENCE_CARD_20260911.md"
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
