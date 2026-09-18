"""The capture seams in the shared environment must cost nothing when capture is off.

`envs/uav_service_restoration/env.py` is the one file in this suite that edits shared
scientific code. Four observer hooks were added to `step()` and `reset()`. Every existing
training and evaluation path leaves `capture_observer` as `None`, and this module is the
evidence that such a path is unchanged: not "close enough", but the same trajectory, the
same random stream, the same episode boundaries and the same number of scheduler solves as
the committed version of the file that predates the edit.

The baseline is not a stored golden file - it is the previous revision of `env.py` read out
of git and executed inside the real package, so the comparison keeps working as the rest of
the environment evolves and cannot silently rot into comparing the new code with itself.
"""

from __future__ import annotations

import hashlib
import importlib
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_RELPATH = "envs/uav_service_restoration/env.py"
CONFIG_PATH = REPO_ROOT / "configs" / "uav_service_restoration" / "smoke_fixture.json"

#: The exact revision the capture seams were added on top of. Pinned to a commit, not to
#: HEAD: once this work is committed, HEAD holds the edited file and the comparison would
#: quietly become "the new code equals itself". `_load_baseline_env_module` additionally
#: refuses a baseline that already contains the seam, so a wrong pin fails loudly.
BASELINE_REV = "ef6cb091a621bf04a734878346dbd8860a1ebe59"

#: A token that exists only in the edited file. Its ABSENCE is what makes the baseline a
#: baseline.
SEAM_MARKER = "_capture_observer"

#: The whole episode. An earlier value of 40 stopped short of the horizon, which left the
#: terminal transition - the truncation flag, and the ordering the seam exists to protect -
#: outside the compared trajectory entirely.
DECISION_STEPS = 80
SEED = 17


def _git_show(rev: str, relpath: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "show", f"{rev}:{relpath}"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.decode("utf-8")


def _load_baseline_env_module() -> types.ModuleType | None:
    """Execute the committed `env.py` as a sibling module of the real package.

    The file uses relative imports (`from .config import ...`), so it is given a `__name__`
    and `__package__` inside `envs.uav_service_restoration`. Nothing is written to disk and
    the real module is left untouched.
    """

    source = _git_show(BASELINE_REV, ENV_RELPATH)
    if source is None:
        return None
    if SEAM_MARKER in source:
        raise AssertionError(
            f"{ENV_RELPATH} at {BASELINE_REV} already contains {SEAM_MARKER!r}: the pinned "
            "baseline is not the revision that predates the capture seams, so this test "
            "would be comparing the edited environment against itself"
        )
    package = importlib.import_module("envs.uav_service_restoration")
    name = "envs.uav_service_restoration._env_offpath_baseline"
    module = types.ModuleType(name)
    module.__package__ = "envs.uav_service_restoration"
    module.__file__ = str(REPO_ROOT / ENV_RELPATH)
    module.__dict__["__builtins__"] = __builtins__
    sys.modules[name] = module
    try:
        exec(compile(source, module.__file__, "exec"), module.__dict__)
    except Exception:  # pragma: no cover - a broken baseline is a skip, not a failure
        sys.modules.pop(name, None)
        return None
    assert package is not None
    return module


def _digest(value: Any, hasher: "hashlib._Hash") -> None:
    """Fold a step result into a hash without tolerating a float difference anywhere."""

    if isinstance(value, np.ndarray):
        hasher.update(b"ndarray")
        hasher.update(str(value.dtype).encode())
        hasher.update(str(value.shape).encode())
        hasher.update(np.ascontiguousarray(value).tobytes())
    elif isinstance(value, dict):
        hasher.update(b"dict")
        for key in sorted(value, key=repr):
            hasher.update(repr(key).encode())
            _digest(value[key], hasher)
    elif isinstance(value, (list, tuple)):
        hasher.update(b"seq")
        for item in value:
            _digest(item, hasher)
    elif isinstance(value, float):
        # Bit pattern, not repr: a one-ulp difference must fail this test.
        hasher.update(b"f")
        hasher.update(np.float64(value).tobytes())
    else:
        hasher.update(repr(value).encode())


def _rollout(env_module: types.ModuleType) -> dict[str, Any]:
    """One fully deterministic rollout with capture off, reduced to comparable facts."""

    from envs.uav_service_restoration.baselines import build_controller
    from envs.uav_service_restoration.config import load_config

    config = load_config(str(CONFIG_PATH))
    env = env_module.UAVServiceRestorationEnv(config)

    # Count scheduler solves: the capture seam sits right beside `_evaluate_service`, so an
    # accidental extra solve for display purposes would show up here even if the numbers
    # happened to match.
    solves = {"n": 0}
    original = type(env)._evaluate_service

    def counting(self, *args, **kwargs):
        solves["n"] += 1
        return original(self, *args, **kwargs)

    type(env)._evaluate_service = counting
    try:
        controller = build_controller("backhaul_aware_greedy", config, seed=SEED)
        hasher = hashlib.sha256()
        controller.reset()
        env.reset(seed=SEED)
        _digest(env.get_current_state(), hasher)

        boundaries: list[int] = []
        steps = 0
        while env.agents and steps < DECISION_STEPS:
            view = env.get_current_state()
            result = env.step(controller.act(view, list(env.agents)))
            _digest(result, hasher)
            _digest(env.get_current_state(), hasher)
            steps += 1
            if not env.agents:
                boundaries.append(steps)

        summary = env.episode_summary()
        _digest(summary, hasher)
        return {
            "trajectory_sha256": hasher.hexdigest(),
            "steps": steps,
            "episode_boundaries": boundaries,
            "solver_calls": solves["n"],
            "rng_state": _rng_fingerprint(env),
            "rng_streams": _rng_stream_count(env),
        }
    finally:
        type(env)._evaluate_service = original
        env.close()


def _rng_fingerprint(env: Any) -> str:
    """Hash the state of every named generator the environment draws from.

    The environment keeps its streams in `_rngs`, spawned per episode from a `SeedSequence`
    over (base seed, episode index); there is no generator sitting directly on the instance,
    so a naive scan of `vars(env)` would hash nothing and silently pass. The count is folded
    into the digest, and `_assert_rng_surface_is_real` fails the suite if it is ever zero.
    """

    hasher = hashlib.sha256()
    streams: dict[str, Any] = {}
    for container_name in ("_rngs",):
        container = getattr(env, container_name, None)
        if isinstance(container, dict):
            for name, generator in container.items():
                if isinstance(generator, np.random.Generator):
                    streams[f"{container_name}.{name}"] = generator.bit_generator.state
                elif isinstance(generator, np.random.RandomState):
                    streams[f"{container_name}.{name}"] = generator.get_state()
    for name in sorted(vars(env)):
        value = getattr(env, name, None)
        if isinstance(value, np.random.Generator):
            streams[name] = value.bit_generator.state
        elif isinstance(value, np.random.RandomState):
            streams[name] = value.get_state()
    for name in sorted(streams):
        hasher.update(name.encode())
        _digest(streams[name], hasher)
    hasher.update(f"generators={len(streams)}".encode())
    hasher.update(repr(getattr(env, "_base_seed", None)).encode())
    return hasher.hexdigest()


def _rng_stream_count(env: Any) -> int:
    container = getattr(env, "_rngs", None)
    return len(container) if isinstance(container, dict) else 0


@pytest.fixture(scope="module")
def current_rollout() -> dict[str, Any]:
    env_module = importlib.import_module("envs.uav_service_restoration.env")
    return _rollout(env_module)


def test_the_rollout_reaches_the_end_of_the_episode(current_rollout: dict[str, Any]) -> None:
    """The comparison must include the terminal transition, not stop short of it.

    ``on_decision_complete`` runs before ``self.agents`` is emptied specifically so a
    terminal frame describes the episode that just ended. A rollout that never reaches the
    horizon compares none of that, and `episode_boundaries` would be an empty list on both
    sides - equal, and meaningless.
    """

    assert current_rollout["episode_boundaries"], (
        "the rollout never reached a terminal step, so the terminal ordering this seam "
        "exists to protect is not covered by the comparison"
    )


def test_the_rng_comparison_is_not_vacuous(current_rollout: dict[str, Any]) -> None:
    """Guard the guard: an empty generator set would make every RNG assertion trivially true."""

    assert current_rollout["rng_streams"] > 0, (
        "no named random stream was found on the environment, so `rng_state` compares "
        "nothing; update `_rng_fingerprint` to follow where the streams actually live"
    )


def test_capture_observer_defaults_to_absent() -> None:
    """Nothing in the shared environment turns capture on by itself."""

    from envs.uav_service_restoration.config import load_config
    from envs.uav_service_restoration.env import UAVServiceRestorationEnv

    env = UAVServiceRestorationEnv(load_config(str(CONFIG_PATH)))
    try:
        assert env.capture_observer is None
        env.reset(seed=SEED)
        assert env.capture_observer is None, "reset must not attach an observer"
    finally:
        env.close()


def test_off_path_matches_the_revision_before_the_capture_seams(
    current_rollout: dict[str, Any],
) -> None:
    """With ``capture_observer`` unset, the edited env reproduces the previous revision.

    Compared: the full step-by-step trajectory (observations, rewards, termination and
    truncation flags, info payloads and the episode summary, hashed over raw float bits),
    the episode boundaries, the number of scheduler solves, and the environment's random
    state at the end.
    """

    baseline_module = _load_baseline_env_module()
    if baseline_module is None:
        # Only a genuinely unavailable history may skip. Where git works, silently skipping
        # would report green having compared nothing at all.
        if _git_show("HEAD", ENV_RELPATH) is not None:
            raise AssertionError(
                f"git is available but {ENV_RELPATH} could not be loaded at {BASELINE_REV}; "
                "the off-path comparison did not run and must not be reported as passing"
            )
        pytest.skip(f"no usable git history for {ENV_RELPATH}; cannot compare revisions")
    baseline = _rollout(baseline_module)

    assert baseline["steps"] == current_rollout["steps"]
    assert baseline["episode_boundaries"] == current_rollout["episode_boundaries"]
    assert baseline["solver_calls"] == current_rollout["solver_calls"], (
        "the capture seam changed how many times the scheduler was solved; a display path "
        "must never add a solve"
    )
    assert baseline["rng_streams"] == current_rollout["rng_streams"]
    assert baseline["rng_state"] == current_rollout["rng_state"], (
        "the random stream diverged from the pre-change revision"
    )
    assert baseline["trajectory_sha256"] == current_rollout["trajectory_sha256"], (
        "the off-path trajectory is not identical to the revision before the capture seams"
    )


def test_off_path_is_reproducible_within_the_current_revision(
    current_rollout: dict[str, Any],
) -> None:
    """The rollout used for the comparison is itself deterministic.

    Without this, an equality above could be produced by two runs that are each unstable in
    the same way, and a failure could not be attributed to the edit.
    """

    again = _rollout(importlib.import_module("envs.uav_service_restoration.env"))
    assert again["trajectory_sha256"] == current_rollout["trajectory_sha256"]
    assert again["solver_calls"] == current_rollout["solver_calls"]
    assert again["rng_state"] == current_rollout["rng_state"]


def test_attaching_and_detaching_an_observer_leaves_the_trajectory_unchanged(
    current_rollout: dict[str, Any],
) -> None:
    """A gate that admits nothing must be indistinguishable from no observer at all.

    This is the case that matters operationally: an operator arms a preview, no viewer ever
    connects, and the run must still be the run that would have happened.
    """

    from envs.uav_service_restoration.config import load_config
    from envs.uav_service_restoration.env import UAVServiceRestorationEnv

    from tools.research_support.capture.profiles import (
        CaptureConfig,
        CaptureGate,
        Profile,
    )
    from tools.research_support.capture.service_restoration import ServiceRestorationObserver
    from tools.research_support.capture.transport import NullSink
    from tools.research_support.records import PolicyKind, SourceKind

    from envs.uav_service_restoration.baselines import build_controller

    config = load_config(str(CONFIG_PATH))
    env = UAVServiceRestorationEnv(config)
    # Profile OFF: the gate refuses before it reads a clock, so nothing is ever captured.
    gate = CaptureGate(CaptureConfig(profile=Profile.OFF))
    observer = ServiceRestorationObserver(
        gate=gate,
        sink=NullSink(),
        run_id="off-path-check",
        trace_id="off-path-check",
        policy_kind=PolicyKind.RULE_CONTROLLER,
        source_kind=SourceKind.RULE_CONTROLLER_ROLLOUT,
        policy_label="backhaul_aware_greedy",
    )
    env.set_capture_observer(observer)
    try:
        controller = build_controller("backhaul_aware_greedy", config, seed=SEED)
        hasher = hashlib.sha256()
        controller.reset()
        env.reset(seed=SEED)
        _digest(env.get_current_state(), hasher)
        steps = 0
        while env.agents and steps < DECISION_STEPS:
            view = env.get_current_state()
            _digest(env.step(controller.act(view, list(env.agents))), hasher)
            _digest(env.get_current_state(), hasher)
            steps += 1
        _digest(env.episode_summary(), hasher)

        assert observer.emitted == 0, "profile OFF emitted a frame"
        assert gate.counters.admitted == 0
        assert hasher.hexdigest() == current_rollout["trajectory_sha256"], (
            "attaching an observer changed the trajectory even though it captured nothing"
        )
        assert _rng_fingerprint(env) == current_rollout["rng_state"]
    finally:
        env.set_capture_observer(None)
        env.close()
