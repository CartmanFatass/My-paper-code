"""New factories and the thin adaptation this package needs.

``make_parallel_env`` returns the native PettingZoo environment.  ``make_array_env`` wraps
it in the **existing, unmodified** ``envs.pettingzoo.env_adapter.ParallelToArrayAdapter``.

Nothing here touches ``ha_ctse_process.env_factory``: no scenario alias is added, no
default route is changed, and the legacy factory keeps producing exactly what it produced
before.  These factories are constructed explicitly by this package's own CLIs.

Checked properties of the shared adapter, read from its implementation rather than from
its docstring:

* ``reset(seed, options)`` returns ``(observations_array, info)`` with the global state
  under ``info["state"]``, and ``step`` returns
  ``(obs, scalar_reward, terminated, truncated, info)`` with ``info["next_state"]``.
* the scalar reward is the **mean** of the per-agent rewards
  (``env_adapter.py:254``).  This environment returns the same team reward ``r`` to every
  UAV, so the adapted scalar is ``r`` - it must not be divided by the UAV count again.
* observations must match the declared Box ``shape`` **and** ``dtype`` exactly and must be
  finite (``env_adapter.py:403-414``); this environment emits finite float32.
* the state comes from ``_get_state()`` or ``state()`` and is flattened to float32.
* ``get_current_state()`` is called on every ``reset`` and ``step`` and its mapping is
  placed in ``info["state_info"]``, which the process-core trainer forwards into its
  segment ledger.  That is why this environment's ``get_current_state()`` carries only
  permitted centralized telemetry, and why privileged diagnostics live behind a separate
  method.

``ServiceRestorationArrayAdapter`` is a subclass that adds read-only passthroughs for this
package's episode summary and privileged diagnostics.  It adds no behaviour to ``reset``
or ``step``.
"""

from __future__ import annotations

from typing import Any

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter

from .config import EnvConfig, load_config
from .env import UAVServiceRestorationEnv


class ServiceRestorationArrayAdapter(ParallelToArrayAdapter):
    """Array-interface adapter with this package's metrics exposed.

    Pure addition: ``reset`` and ``step`` are inherited unchanged, so the array contract
    is byte-for-byte the shared adapter's.
    """

    def episode_summary(self) -> dict[str, Any]:
        return self.env.episode_summary()

    def get_privileged_diagnostics(self) -> dict[str, Any]:
        """Evaluator-only view.  Never routed into ``info`` by ``reset`` or ``step``."""

        return self.env.get_privileged_diagnostics()

    def schema(self) -> dict[str, Any]:
        return self.env.schema()

    @property
    def native_env(self) -> UAVServiceRestorationEnv:
        return self.env


def make_parallel_env(
    config: EnvConfig | str,
    *,
    demand_source: Any | None = None,
    dataset_root: str | None = None,
    seed: int | None = None,
    render_mode: str | None = None,
) -> UAVServiceRestorationEnv:
    """Construct the native Parallel API environment.

    ``config`` may be an :class:`EnvConfig` or a path to a configuration document.  There
    is no implicit default: a real-data configuration whose dataset is missing raises.
    """

    resolved = load_config(config) if isinstance(config, str) else config
    return UAVServiceRestorationEnv(
        resolved,
        demand_source=demand_source,
        dataset_root=dataset_root,
        seed=seed,
        render_mode=render_mode,
    )


def make_array_env(
    config: EnvConfig | str,
    *,
    demand_source: Any | None = None,
    dataset_root: str | None = None,
    seed: int | None = None,
    render_mode: str | None = None,
    wrap_metrics: bool = True,
) -> ParallelToArrayAdapter:
    """Construct the array-interface environment through the shared adapter.

    With ``wrap_metrics=False`` the shared ``ParallelToArrayAdapter`` is used directly, so
    the contract can be tested against the unmodified class.
    """

    parallel = make_parallel_env(
        config,
        demand_source=demand_source,
        dataset_root=dataset_root,
        seed=seed,
        render_mode=render_mode,
    )
    adapter_class = ServiceRestorationArrayAdapter if wrap_metrics else ParallelToArrayAdapter
    return adapter_class(parallel, seed=seed)
