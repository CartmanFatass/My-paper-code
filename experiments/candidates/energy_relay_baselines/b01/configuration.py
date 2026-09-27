"""Independent-seed SET replication: B02's exact recipe with new seed ownership."""

from experiments.candidates.energy_relay_benchmark.b02.configuration import (
    B02Spec, CHECKPOINT_RULE, PROGRAMME, RECIPE_NOTES, assert_production,
    checkpoint_rollouts, config_dict, make_b02_config, spec_record,
)

OBJECT_ID = "ENERGY-RELAY-BASELINES-B01"
DIRECTION = "energy_relay_baselines"
TRAINING_SEEDS = (26092711, 26092731)
DEVELOPMENT_WORLDS = tuple(range(955001, 955033))
EVALUATED_CHECKPOINTS = ("c00", "c06")
MODES = ("deterministic", "stochastic")


def production_spec(seed: int) -> B02Spec:
    if int(seed) not in TRAINING_SEEDS:
        raise ValueError(f"unplanned training seed {seed}; declared {TRAINING_SEEDS}")
    spec = B02Spec(seed=int(seed))
    assert_production(spec)
    if checkpoint_rollouts(spec) != (34, 67, 100, 134, 167, 200):
        raise ValueError("the six B02 checkpoint positions changed")
    return spec
