"""RECCT dependency mask bound to the real roster PPO learner update.

Sequence 05 algorithm implementation.  The accepted certificate at
``820d4d1c`` established signed-credit feasible sets, complete/transitive
ancestry, protected declarations and multi-leader hysteresis inside a fixed
zero-return rational unit.  This module moves that mechanism onto the actual
Adam update used by the continuous-roster workstream.

WHAT IS AND IS NOT CLAIMED
--------------------------
External ruling ``ENV_CAPABILITY_EXTENSION_REQUIRED`` (archived under
``local_research/pro_reviews/env_capability_v1_continuous_roster_toy/``) placed
RECCT differently from the other three mechanisms.  It is *not* eliminated by an
interface impossibility -- the policy still has to be learned from a coupled
team reward, so different update masks can genuinely alter gradient variance,
optimisation speed and stability.  But the ruling was equally explicit that the
task does not identify the intended mechanism:

    "all relevant variants share an extremely low-complexity representational
     solution; the optimum is highly non-unique; there is no pre-established
     state or coalition condition in which one update dependency is necessary
     and another is wrong; a performance difference can therefore arise from
     generic optimizer regularization rather than the proposed dependency
     semantics."

    "RECCT can be run here as an optimization smoke test or negative control.
     It should not be treated as a decisive positive or negative scientific
     discriminator without an added condition that forces the relevant update
     dependencies to disagree."

This module therefore supports an EXPLORATORY OPTIMISATION PROBE only.  Results
may not promote or eliminate the candidate.

ADMISSIBLE INPUTS
-----------------
The mask is computed strictly from pre-update state: the gradient about to be
applied, the Adam moments as they stand *before* the step, and the declared
buffer ancestry.  It never reads the audit outcome, future state, return, raw
owner key, global RNG or any post-treatment quantity -- the prohibitions the
accepted RECCT certificate registered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import torch

RAW_OUTPUT_BINDING = "recct_lite.roster_learner_mask.v1"

#: The three registered arms.
CANDIDATE = "RECCT_DEPENDENCY_MASK"
UNCHANGED = "UNCHANGED_LEARNER"
SIGN_DESTROYED = "SIGN_DESTROYED_MATCHED"
ARMS = (CANDIDATE, UNCHANGED, SIGN_DESTROYED)


@dataclass(frozen=True)
class MaskDecision:
    """What the mask did on one update, in checkable form."""

    arm: str
    total_parameters: int
    retained_parameters: int
    zeroed_parameters: int
    sign_flipped_parameters: int

    @property
    def retained_fraction(self) -> float:
        if self.total_parameters == 0:
            return 0.0
        return self.retained_parameters / self.total_parameters


def _pre_update_second_moment(
    optimizer: torch.optim.Optimizer, parameter: torch.Tensor
) -> torch.Tensor | None:
    """Adam's ``exp_avg_sq`` as it stands BEFORE this step, or None on step 0."""
    state = optimizer.state.get(parameter)
    if not state:
        return None
    moment = state.get("exp_avg_sq")
    if moment is None:
        return None
    return moment


def recct_feasible_mask(
    parameter: torch.Tensor,
    gradient: torch.Tensor,
    *,
    optimizer: torch.optim.Optimizer,
    ancestry_admits: bool,
) -> torch.Tensor:
    """Signed-credit feasible set for one parameter tensor.

    A coordinate is retained when the ancestry admits it AND the gradient
    carries credit that the accumulated second moment does not already explain.
    On the very first step no moment exists, so everything is feasible -- which
    is the hysteresis-free boundary the accepted certificate registered.
    """
    if not ancestry_admits:
        return torch.zeros_like(gradient, dtype=torch.bool)
    moment = _pre_update_second_moment(optimizer, parameter)
    if moment is None:
        return torch.ones_like(gradient, dtype=torch.bool)
    scale = moment.sqrt()
    threshold = scale.mean()
    return gradient.abs() > threshold


def apply_arm(
    parameters: Sequence[torch.Tensor],
    *,
    arm: str,
    optimizer: torch.optim.Optimizer,
    ancestry_admits: Mapping[int, bool] | None = None,
    generator: torch.Generator | None = None,
) -> MaskDecision:
    """Mutate ``.grad`` in place according to ``arm``; return what was done.

    ``UNCHANGED`` leaves every gradient alone.  ``CANDIDATE`` zeroes the
    infeasible coordinates.  ``SIGN_DESTROYED`` retains exactly the same
    coordinates as ``CANDIDATE`` -- so the two are matched on how much signal
    survives -- but destroys the credit direction on them, which is the
    objective-matched control the task list requires.
    """
    if arm not in ARMS:
        raise ValueError(f"unregistered arm {arm!r}")

    total = retained = zeroed = flipped = 0
    for index, parameter in enumerate(parameters):
        gradient = parameter.grad
        if gradient is None:
            continue
        total += gradient.numel()
        if arm == UNCHANGED:
            retained += gradient.numel()
            continue

        admits = True if ancestry_admits is None else bool(ancestry_admits.get(index, True))
        keep = recct_feasible_mask(
            parameter, gradient, optimizer=optimizer, ancestry_admits=admits
        )
        kept = int(keep.sum().item())
        retained += kept
        zeroed += gradient.numel() - kept

        if arm == CANDIDATE:
            gradient.mul_(keep)
        else:  # SIGN_DESTROYED
            bits = torch.randint(
                0,
                2,
                gradient.shape,
                generator=generator,
                device=gradient.device,
                dtype=torch.int64,
            )
            signs = bits.to(gradient.dtype).mul_(2).sub_(1)
            gradient.mul_(keep)
            gradient.mul_(signs)
            flipped += kept

    return MaskDecision(
        arm=arm,
        total_parameters=total,
        retained_parameters=retained,
        zeroed_parameters=zeroed,
        sign_flipped_parameters=flipped,
    )
