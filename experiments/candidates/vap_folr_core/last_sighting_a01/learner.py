"""Actor selection with the unchanged native double-Q learner contract."""

import copy

from torch.optim import RMSprop

from ..entity_history_b01.model import Actor as GenericActor
from ..public_lifecycle_b01.flex_qmix import FlexQMixer
from ..public_lifecycle_b01.learner import Learner as EpisodicLearner
from .model import Actor as LastSightingActor


ARMS = ("GENERIC_RETAIN", "LAST_SIGHTING")


class Learner(EpisodicLearner):
    """Construct one selected actor; inherit native update and save verbatim."""

    def __init__(self, arm):
        if arm == "GENERIC_RETAIN":
            self.actor = GenericActor(arm)
        elif arm == "LAST_SIGHTING":
            self.actor = LastSightingActor()
        else:
            raise ValueError(arm)
        self.mixer = FlexQMixer()
        self.target_mixer = copy.deepcopy(self.mixer)
        self.params = list(self.actor.parameters()) + list(self.mixer.parameters())
        self.optimiser = RMSprop(
            self.params, lr=0.0005, alpha=0.99, eps=0.00001
        )
        self.target_actor = copy.deepcopy(self.actor)
        self.last_target_update_episode = 0
        self.updates = 0

