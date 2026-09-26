"""Prospectively fixed B03 addresses and cell order."""

OBJECT = "controller_composition_b03"
TAG = "b03_partner_replication_20260925"
BLOCKS = {
    "B1": {"learner_seed": 92561001, "assignment_seed": 92561002,
           "train_world_base": 92570000},
    "B2": {"learner_seed": 92562001, "assignment_seed": 92562002,
           "train_world_base": 92580000},
}
EVAL_WORLD_BASE = 92590000
BOOTSTRAP_SEED = 92569999
BOOTSTRAP_DRAWS = 10000
ARMS = ("F2", "M")
PARTNERS = (1, 2, 3)
EVAL_CELLS = tuple((block, learner, partner) for block in BLOCKS
                   for learner in ("I", *ARMS) for partner in PARTNERS) + (("shared", "OLD3", 3),)
