"""B03 authentic fair-D0 comparison through the shared native-renewal learning path."""
import run_fsd_native_renewal_learning_b01 as shared

TRAINING_SEED = 770403
EVALUATION_MASTER = 770404
OBJECT_ID = "FSD_NATIVE_RENEWAL_LEARNING_B03"
CARD = "docs/research/candidates/flexible_skill_duration/" + OBJECT_ID + "_SCIENCE_CARD_20260908.md"


def main(argv=None):
    return shared.main(argv, training_seed=TRAINING_SEED, evaluation_master=EVALUATION_MASTER,
                       object_id=OBJECT_ID, card=CARD, control_policy="D0")


if __name__ == "__main__":
    raise SystemExit(main())
