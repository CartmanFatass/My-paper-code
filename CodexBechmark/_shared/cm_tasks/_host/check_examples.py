"""Focused behavior checks for illustrative snippets; creates no files."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np
import torch

BASE = Path(__file__).resolve().parents[1] / "patterns/examples"


def example(name):
    spec = importlib.util.spec_from_file_location(name, BASE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExampleChecks(unittest.TestCase):
    def test_full_row_denominator_and_gradient(self):
        terms = torch.tensor([[2., 90.], [80., 70.]], requires_grad=True)
        mask = torch.tensor([[True, False], [False, False]])
        value = example("masked_reduction").row_mean_of_agent_sum(terms, mask)
        self.assertEqual(value.item(), 1.)  # eligible-only mean would be 2.
        value.backward()
        torch.testing.assert_close(terms.grad, torch.tensor([[.5, 0.], [0., 0.]]))

    def test_all_held_rows_are_zero_without_dividing_by_decision_count(self):
        terms = torch.tensor([[4., 7.]], requires_grad=True)
        value = example("masked_reduction").row_mean_of_agent_sum(
            terms, torch.zeros_like(terms, dtype=torch.bool))
        self.assertEqual(value.item(), 0.)
        value.backward()
        torch.testing.assert_close(terms.grad, torch.zeros_like(terms))

    def test_terminal_and_external_truncation_are_different(self):
        terminal = torch.tensor([False, True, False, True])
        truncated = torch.tensor([False, False, True, True])
        bootstrap, trace = example("transition_masks").continuing_task_masks(
            terminal, truncated)
        self.assertEqual(bootstrap.tolist(), [True, False, True, False])
        self.assertEqual(trace.tolist(), [True, False, False, False])

    def test_evaluation_does_not_advance_training_generator(self):
        make = example("evaluation_streams").make_sampling_streams
        train, evaluation = make(41, 91)
        control, _ = make(41, 91)
        np.testing.assert_array_equal(train.normal(size=3), control.normal(size=3))
        evaluation.normal(size=17)
        np.testing.assert_array_equal(train.normal(size=9), control.normal(size=9))
        self.assertIsNot(train, evaluation)


if __name__ == "__main__":
    unittest.main()
