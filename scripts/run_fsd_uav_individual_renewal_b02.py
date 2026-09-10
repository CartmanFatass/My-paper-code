"""B02 independent UAV pair through the unchanged shared learning path."""
import run_fsd_uav_individual_renewal_b01 as shared

TRAINING_SEED = 770603
EVALUATION_SEED = 780603
OBJECT_ID = "FSD_UAV_INDIVIDUAL_RENEWAL_B02"
CARD = "docs/research/candidates/flexible_skill_duration/" + OBJECT_ID + "_SCIENCE_CARD_20260908.md"


def main(argv=None):
    return shared.main(argv, training_seed=TRAINING_SEED, evaluation_seed=EVALUATION_SEED,
                       object_id=OBJECT_ID, card=CARD)


if __name__ == "__main__":
    raise SystemExit(main())
