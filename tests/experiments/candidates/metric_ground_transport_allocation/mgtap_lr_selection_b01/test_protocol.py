"""Synthetic-only contract tests. No model, native environment or trajectory runs."""

import copy
import unittest

from experiments.candidates.metric_ground_transport_allocation.mgtap_lr_selection_b01 import protocol as p


def panel(stage, arm, lr_key, score):
    master = p.SELECTION_MASTER if stage == "selection" else p.HOLDOUT_MASTER
    return [dict(stage=stage, phase="eval", pair_master=master, arm=arm,
                 lr_key=lr_key, learning_rate=p.LEARNING_RATES[lr_key], episode=e,
                 J=score, steps=p.HORIZON, **p.randomization(master, "eval", e))
            for e in range(p.EVAL_EPISODES)]


def selection_rows(tie=False):
    values = {"COND": {"base": .03, "slow": .07, "fast": .02},
              "DENSE": {"base": .20, "slow": .15, "fast": .25}}
    return [row for arm in p.ARMS for key in p.LEARNING_RATES
            for row in panel("selection", arm, key, .1 if tie else values[arm][key])]


class ProtocolTests(unittest.TestCase):
    def test_each_arm_maximizes_its_own_validation_score(self):
        result = p.select_learning_rates(selection_rows())
        self.assertEqual(result["selected_lr_key"], {"COND": "slow", "DENSE": "fast"})
        self.assertFalse(result["holdout_used_for_selection"])

    def test_exact_tie_prefers_inherited_rate_independent_of_row_order(self):
        result = p.select_learning_rates(list(reversed(selection_rows(tie=True))))
        self.assertEqual(result["selected_lr_key"], dict.fromkeys(p.ARMS, "base"))

    def test_no_replacement_of_missing_candidate_or_episode(self):
        rows = selection_rows()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            p.select_learning_rates(rows[:-1])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            p.select_learning_rates([row for row in rows if row["lr_key"] != "slow"])

    def test_duplicate_episode_rejected(self):
        rows = selection_rows()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            p.select_learning_rates(rows + [rows[0]])

    def test_holdout_cannot_enter_selection(self):
        rows = selection_rows()
        rows[0] = panel("holdout", "COND", "base", 999)[0]
        with self.assertRaisesRegex(ValueError, "role or master"):
            p.select_learning_rates(rows)

    def test_nonfinite_bool_and_missing_scores_rejected(self):
        for bad in (float("nan"), float("inf"), True, None, "0.1"):
            with self.subTest(bad=bad):
                rows = selection_rows()
                rows[0]["J"] = bad
                with self.assertRaises(ValueError):
                    p.select_learning_rates(rows)

    def test_randomization_endpoint_and_rate_bindings(self):
        for key, bad in (("reset_seed", 1), ("velocity_seed", 1), ("duration_seed", 1),
                         ("steps", 255), ("learning_rate", .3), ("pair_master", 8241)):
            with self.subTest(key=key):
                rows = selection_rows()
                rows[0][key] = bad
                with self.assertRaises(ValueError):
                    p.select_learning_rates(rows)

    def test_fresh_holdout_and_carded_readings(self):
        selected = p.select_learning_rates(selection_rows())
        for delta, expected in ((.03, "COND_ABOVE_MEI"), (-.03, "COND_ADVERSE"),
                                (.005, "INSIDE_MEI"), (.01, "INSIDE_MEI"), (-.01, "INSIDE_MEI")):
            with self.subTest(delta=delta):
                rows = panel("holdout", "COND", "slow", delta) + panel("holdout", "DENSE", "fast", 0.)
                result = p.holdout_primary(rows, selected)
                self.assertAlmostEqual(result["delta_J"], delta)
                self.assertEqual(result["reading"], expected)
                self.assertEqual(result["independent_final_training_pairs"], 1)
                self.assertEqual(result["conditional_panel_se"], 0.)

    def test_final_rows_must_use_selected_rates(self):
        selected = p.select_learning_rates(selection_rows())
        rows = panel("holdout", "COND", "base", .5) + panel("holdout", "DENSE", "fast", .1)
        with self.assertRaisesRegex(ValueError, "unexpected arm"):
            p.holdout_primary(rows, selected)

    def test_selection_provenance_must_remain_separate(self):
        selected = p.select_learning_rates(selection_rows())
        rows = panel("holdout", "COND", "slow", .5) + panel("holdout", "DENSE", "fast", .1)
        contaminated = copy.deepcopy(selected)
        contaminated["holdout_used_for_selection"] = True
        with self.assertRaisesRegex(ValueError, "provenance"):
            p.holdout_primary(rows, contaminated)

    def test_addresses_disjoint_across_stages(self):
        addresses = []
        for master in (p.SELECTION_MASTER, p.HOLDOUT_MASTER):
            addresses.append({value for phase, size in (("train", 256), ("eval", 32))
                              for e in range(size) for value in p.randomization(master, phase, e).values()})
        self.assertFalse(addresses[0] & addresses[1])

    def test_retuning_selection_record_without_validation_support_rejected(self):
        selected = p.select_learning_rates(selection_rows())
        selected["selected_lr_key"]["COND"] = "base"
        selected["selected_learning_rate"]["COND"] = p.LEARNING_RATES["base"]
        rows = panel("holdout", "COND", "base", .5) + panel("holdout", "DENSE", "fast", .1)
        with self.assertRaisesRegex(ValueError, "frozen validation rule"):
            p.holdout_primary(rows, selected)

    def test_counts_are_work_not_new_experiment_results(self):
        plan = p.planned_exposure()
        self.assertEqual(plan["status"], "PLANNED_NOT_EXECUTED")
        self.assertEqual(plan["stages"]["selection"]["fits"], 6)
        self.assertEqual(plan["stages"]["holdout"]["fits"], 2)
        self.assertEqual(plan["total"]["fits"], 8)
        self.assertEqual(plan["total"]["total_team_ticks"], 589824)
        self.assertEqual(plan["total"]["adam_calls"], 4096)
        self.assertEqual(plan["total"]["actor_row_uses_collection_evaluation_replay"], 13434880)
        self.assertEqual(plan["actual_new_native_exposure_at_protocol_preparation"], 0)


if __name__ == "__main__":
    unittest.main()
