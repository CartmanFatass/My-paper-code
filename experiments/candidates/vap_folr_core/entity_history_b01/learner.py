"""New actor constructor; unchanged native double-Q update/checkpoint contract."""
import copy

from torch.optim import RMSprop

from ..public_lifecycle_b01.flex_qmix import FlexQMixer
from ..public_lifecycle_b01.learner import Learner as EpisodicLearner
from .model import Actor


class Learner(EpisodicLearner):
    def __init__(self, arm):
        self.actor = Actor(arm)
        self.mixer = FlexQMixer()
        self.target_mixer = copy.deepcopy(self.mixer)
        self.params = list(self.actor.parameters()) + list(self.mixer.parameters())
        self.optimiser = RMSprop(self.params, lr=0.0005, alpha=0.99, eps=0.00001)
        self.target_actor = copy.deepcopy(self.actor)
        self.last_target_update_episode = 0
        self.updates = 0
