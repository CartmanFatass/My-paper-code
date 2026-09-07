"""B05 uses the B04 execution path with explicit seed and result identity."""
from scripts.run_dish_control_low_lr_b04 import main
from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b05.study import OBJECT, SEED


if __name__ == "__main__":
    raise SystemExit(main(seed=SEED, object_name=OBJECT))
