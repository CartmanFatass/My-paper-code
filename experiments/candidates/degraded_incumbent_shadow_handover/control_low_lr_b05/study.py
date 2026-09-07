"""Seed-101 B05 binding; B04 remains the frozen RNG family and shared algorithm."""
from functools import partial

from experiments.candidates.degraded_incumbent_shadow_handover.control_low_lr_b04 import study as b04

OBJECT = "DISH-CONTROL-LOW-LR-B05"
SEED = 101
master = partial(b04.master, seed=SEED)
configuration = partial(b04.configuration, seed=SEED, object_name=OBJECT)
prepare_shared = partial(b04.prepare_shared, seed=SEED, object_name=OBJECT)
run_arm = partial(b04.run_arm, seed=SEED, object_name=OBJECT)
paired_result = partial(b04.paired_result, seed=SEED, object_name=OBJECT)
