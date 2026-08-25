from __future__ import annotations

import numpy as np

from ..model import SCDMPModel as B1Model
from .config import INITIALIZATION_NAMESPACE_BASE


class SCDMPModel(B1Model):
    """Inherited 26,148-parameter architecture with the fresh B3 namespace."""

    def _exact_initialize(self) -> None:
        bit_generator = np.random.PCG64(INITIALIZATION_NAMESPACE_BASE + self.algorithm_seed)
        for layer in (self.node_1, self.node_2, self.action_embedding):
            layer.initialize(bit_generator)
        self.word_gru.initialize(bit_generator)
        for layer in (
            self.f_1, self.f_2, self.f_3, self.gn_1, self.gn_2, self.ge_1, self.ge_2,
        ):
            layer.initialize(bit_generator)
