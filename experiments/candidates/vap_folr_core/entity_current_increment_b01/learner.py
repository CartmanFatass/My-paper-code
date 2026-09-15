"""Separate complete-episode learners for the unchanged selected G and Z actors."""

import copy

from torch.optim import RMSprop

from ..entity_history_augmentation_b01.model import AugmentedActor
from ..entity_history_b01.model import Actor
from ..public_lifecycle_b01.flex_qmix import FlexQMixer
from ..public_lifecycle_b01.learner import Learner as EpisodicLearner


class Learner(EpisodicLearner):
    def __init__(self, arm):
        if arm == "GENERIC_RETAIN":
            self.actor = Actor(arm)
        elif arm == "AUGMENTED_CURRENT_ONLY":
            self.actor = AugmentedActor(arm)
        else:
            raise ValueError(arm)
        self.mixer = FlexQMixer()
        self.target_mixer = copy.deepcopy(self.mixer)
        self.params = list(self.actor.parameters()) + list(self.mixer.parameters())
        self.optimiser = RMSprop(self.params, lr=0.0005, alpha=0.99, eps=0.00001)
        self.target_actor = copy.deepcopy(self.actor)
        self.last_target_update_episode = 0
        self.updates = 0
