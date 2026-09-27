"""Opt-in B01 evaluator observation, with no actor replay or RNG draw.

Rows use transition index ``t``: ``observations_t`` are the eight legal per-UAV inputs and
``state_t`` is the privileged central state before proposal/shield. ``proposal_t`` is the
controller command before the shield; ``submitted_t`` is the command sent to ``env.step``.
``observations_t1`` and ``state_t1`` are read after that step. The state is never labelled
as a legal actor observation. Held snapshots, when present, are raw central state plus raw
joint legal observations captured at ``held_source_t`` and used at step ``t``. The actor
internally normalizes these before use. ``held_age`` is ``t - held_source_t``.
``own_xyz_t`` and ``own_xyz_t1`` are compact positions decoded from the respective legal
observations for every transition, even when full inputs are disabled.

The actor fields are from hooks on the action head's *actual* forward pass. ``actor_mean_raw``
is the Gaussian mean before a possible tanh, and ``actor_scale_raw`` is exp(effective logstd),
after the tanh Gaussian's logstd clamp when configured. Neither field is the statistical mean
or scale of a tanh transformed random variable. For Gaussian, they are the direct action
distribution parameters. Heuristic controllers have no actor fields.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import own_positions
from hmasd.r_mappo_utils import DiagGaussian, TanhDiagGaussian


class ActionInputRecorder:
    """One-world recorder used as ``evaluate_world(observer=...)``.

    ``capture_inputs`` separately enables full decision and post-step legal observations
    and privileged states. ``capture_held_snapshot`` separately enables raw held inputs;
    action and snapshot-age fields remain compact when both are false. ``as_arrays`` returns
    independent copies for storage or a heuristic-teacher collector.
    """

    def __init__(self, *, capture_inputs: bool = False,
                 capture_held_snapshot: bool = False):
        self.capture_inputs = bool(capture_inputs)
        self.capture_held_snapshot = bool(capture_held_snapshot)
        self._rows: dict[str, list[np.ndarray | int]] = {}
        self._distribution: str | None = None
        self._head_calls = 0
        self._mean: np.ndarray | None = None
        self._logstd: np.ndarray | None = None
        self._held_source_t: int | None = None

    def _append(self, name: str, value) -> None:
        self._rows.setdefault(name, []).append(np.array(value, copy=True))

    def _identity(self, name, *values):
        """Small per-transition identities retain first-divergence evidence without full inputs."""
        digest = hashlib.sha256()
        for value in values:
            array = np.ascontiguousarray(value)
            digest.update(str((array.dtype.str, array.shape)).encode())
            digest.update(array.tobytes())
        self._append(name, np.frombuffer(digest.digest(), dtype=np.uint8))

    @contextmanager
    def attach(self, controller):
        """Install head hooks for learned policies; always remove them on exit."""
        handles = []
        self._held_source_t = None
        self._head_calls = 0
        self._mean = self._logstd = None
        evaluator = getattr(controller, "evaluator", None)
        if evaluator is not None:
            head = evaluator.skill_discoverer.actor.act.action_out
            if isinstance(head, TanhDiagGaussian):
                self._distribution = "tanh_gaussian"
            elif isinstance(head, DiagGaussian):
                self._distribution = "gaussian"
            else:
                raise TypeError(f"unsupported actor action head: {type(head).__name__}")

            def mean_hook(_module, _inputs, output):
                self._head_calls += 1
                self._mean = output.detach().cpu().numpy().copy()

            def logstd_hook(_module, _inputs, output):
                self._logstd = output.detach().cpu().numpy().copy()

            try:
                handles.append(head.fc_mean.register_forward_hook(mean_hook))
                handles.append(head.logstd.register_forward_hook(logstd_hook))
            except BaseException:
                for handle in handles:
                    handle.remove()
                raise
        try:
            yield self
        finally:
            for handle in handles:
                handle.remove()

    def on_step(self, *, t: int, observations_t, state_t, proposal_t, submitted_t,
                observations_t1, state_t1, controller) -> None:
        """Read one completed transition. All retained arrays are copied at this boundary."""
        self._append("t", int(t))
        self._append("proposal_t", proposal_t)
        self._append("submitted_t", submitted_t)
        self._identity("input_digest_t", observations_t, state_t)
        self._append("own_xyz_t", own_positions(observations_t))
        self._append("own_xyz_t1", own_positions(observations_t1))
        if self.capture_inputs:
            self._append("observations_t", observations_t)
            self._append("state_t", state_t)
            self._append("observations_t1", observations_t1)
            self._append("state_t1", state_t1)
        evaluator = getattr(controller, "evaluator", None)
        if evaluator is None:
            return
        if self._head_calls != 1 or self._mean is None or self._logstd is None:
            raise RuntimeError("actor head did not expose exactly one action-producing forward")
        head = evaluator.skill_discoverer.actor.act.action_out
        logstd = self._logstd
        if self._distribution == "tanh_gaussian":
            logstd = np.clip(logstd, head.logstd_min, head.logstd_max)
        self._append("actor_mean_raw", self._mean.reshape(proposal_t.shape))
        self._append("actor_scale_raw", np.exp(logstd).reshape(proposal_t.shape))
        self._head_calls = 0
        self._mean = self._logstd = None
        if getattr(evaluator, "use_central_snapshot", False):
            if not bool(evaluator._central_snapshot_valid[0]):
                raise RuntimeError("actor used an invalid held central snapshot")
            if self._held_source_t is None or int(evaluator.env_timers[0]) == 0:
                self._held_source_t = int(t)
            self._append("held_source_t", self._held_source_t)
            self._append("held_age", int(t) - self._held_source_t)
            self._identity("held_digest_t", evaluator._central_snapshot_states[0],
                           evaluator._central_snapshot_obs[0])
            if self.capture_held_snapshot:
                self._append("held_state", evaluator._central_snapshot_states[0])
                self._append("held_observations", evaluator._central_snapshot_obs[0])

    def as_arrays(self) -> dict[str, np.ndarray | str]:
        """Copy-owned trace arrays, plus ``actor_distribution`` for learned policies."""
        arrays: dict[str, np.ndarray | str] = {
            name: np.asarray(values).copy() for name, values in self._rows.items()
        }
        if self._distribution is not None:
            arrays["actor_distribution"] = self._distribution
        return arrays
