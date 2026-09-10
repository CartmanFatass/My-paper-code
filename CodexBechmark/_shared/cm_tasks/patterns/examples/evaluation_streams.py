"""Example only: independent mutable Generator objects, not a new seed law.

The caller supplies scalar seeds using its already chosen experiment rules.
Production code should retain its existing RNG factory and namespaces. This
does not handle Torch/native/environment RNG or mutable policy state.
"""
import numpy as np


def make_sampling_streams(train_seed, evaluation_seed):
    return (np.random.default_rng(train_seed),
            np.random.default_rng(evaluation_seed))
