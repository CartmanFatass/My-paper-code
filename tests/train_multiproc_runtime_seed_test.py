from __future__ import annotations

from types import SimpleNamespace

import pytest

from hmasd.agent import _rollout_sampler_seed_from_config
from train_multiproc_config_1 import bind_runtime_seed


def _named_rollout_seed(cli_seed: int) -> int:
    config = SimpleNamespace()
    bind_runtime_seed(config, cli_seed)
    return _rollout_sampler_seed_from_config(config, stream=0)


def test_cli_seed_binds_reproducible_distinct_named_rollout_streams() -> None:
    assert _named_rollout_seed(41) == _named_rollout_seed(41)
    assert _named_rollout_seed(41) != _named_rollout_seed(42)


def test_missing_or_invalid_runtime_seed_fails_closed() -> None:
    with pytest.raises(ValueError, match="requires config.runtime_seed"):
        _rollout_sampler_seed_from_config(SimpleNamespace(), stream=0)
    with pytest.raises(ValueError, match="runtime seed"):
        bind_runtime_seed(SimpleNamespace(), -1)
