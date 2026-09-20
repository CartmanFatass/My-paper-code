"""The optional state-block affine of the CF central input (`central_snapshot_state_affine`).

The field is introduced for FSD_FLAT_INPUT_SCALE_B05 and lives in the shared learner
(`hmasd/networks.py` `SkillDiscoverer`), at the same single application point
`_apply_central_input` that this directory's CF pathway tests already cover, so its contract is
checked here beside them:

  * with the field absent or None the path is the one that ran before the field existed - same
    `state_dict` keys, same parameter list, the same RNG consumed at construction and bit-identical
    forward outputs;
  * with the field set the module's output equals the unconfigured module's output on a manually
    pre-transformed central input;
  * acting and replay still read the identical actor input for the same stored snapshot;
  * a malformed field, or the field without the CF flag, raises at construction.

Technical checks of the changed contract, never a scientific result.
"""
import importlib.util
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402
from hmasd.networks import SkillDiscoverer  # noqa: E402

_SPEC = importlib.util.spec_from_file_location(
    "fsd_cf_pathway_helpers", Path(__file__).with_name("test_cf_pathway.py"))
cf = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cf)

shared = b01.shared
tiny = cf.tiny  # the two-lane, twenty-step CF host of the pathway tests
LANES, HORIZON, N_UAVS, K, SEED = cf.LANES, cf.HORIZON, cf.N_UAVS, cf.K, cf.SEED
AFFINE_FIELD = scale.AFFINE_FIELD
STATE_DIM, OBS_DIM = 119, 104


def discoverer_config(**overrides):
    """A minimal CF configuration of the real shapes; no environment and no agent."""
    config = SimpleNamespace(
        state_dim=STATE_DIM, obs_dim=OBS_DIM, n_agents=N_UAVS, action_dim=3, action_bound=1.,
        action_space_type="continuous", hidden_size=64, gru_hidden_size=64, n_z=1, n_Z=1,
        use_central_snapshot_in_flat_actor=True)
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


def affine_pair():
    offset, scale_values = scale.state_affine_from_bounds(N_UAVS, 50, 1000, (50, 150), STATE_DIM)
    return offset, scale_values


def build(config, seed=20260919):
    """Construct under a pinned RNG and return the module with the RNG state it left behind."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    module = SkillDiscoverer(config, device=torch.device("cpu"))
    return module, torch.get_rng_state().clone()


def fixed_inputs(batch=5, seed=11):
    generator = torch.Generator().manual_seed(seed)
    observation = torch.randn(batch, OBS_DIM, generator=generator)
    # Raw-metre magnitudes: this is the input the unscaled construction actually reads.
    central = torch.rand(batch, STATE_DIM + N_UAVS * OBS_DIM + N_UAVS, generator=generator)
    central[:, :STATE_DIM] *= 1000.
    hidden = torch.randn(batch, 64, generator=generator)
    skill = torch.zeros(batch, dtype=torch.long)
    return observation, central, hidden, skill


def transformed(central, offset, scale_values):
    values = central.clone()
    values[:, :STATE_DIM] = (values[:, :STATE_DIM] - torch.tensor(offset)) / torch.tensor(scale_values)
    return values


def test_absent_and_none_are_the_same_module_and_the_same_rng_as_the_field_being_set():
    """Flag absent: same keys, same parameters, same RNG draws, bit-identical forward."""
    offset, scale_values = affine_pair()
    absent, rng_absent = build(discoverer_config())
    explicit_none, rng_none = build(discoverer_config(**{AFFINE_FIELD: None}))
    configured, rng_configured = build(discoverer_config(**{AFFINE_FIELD: (offset, scale_values)}))

    assert list(absent.state_dict()) == list(explicit_none.state_dict()) == list(configured.state_dict())
    assert not any(name.startswith("central_state_") for name in configured.state_dict())
    counts = [sum(p.numel() for p in module.parameters())
              for module in (absent, explicit_none, configured)]
    assert counts[0] == counts[1] == counts[2]
    assert len(list(absent.parameters())) == len(list(configured.parameters()))
    # Construction consumes the identical RNG stream with and without the field.
    assert torch.equal(rng_absent, rng_none) and torch.equal(rng_absent, rng_configured)
    assert absent.use_central_state_affine is False and explicit_none.use_central_state_affine is False
    assert configured.use_central_state_affine is True
    assert [name for name, _ in configured.named_buffers()] == ["central_state_offset",
                                                                "central_state_scale"]
    assert [name for name, _ in absent.named_buffers()] == []

    observation, central, hidden, skill = fixed_inputs()
    with torch.no_grad():
        left = absent.forward(observation, skill, hidden, deterministic=True, central_input=central)
        right = explicit_none.forward(observation, skill, hidden, deterministic=True, central_input=central)
    assert torch.equal(left[0], right[0]) and torch.equal(left[1], right[1])
    assert torch.equal(left[3], right[3])
    assert torch.equal(absent._apply_central_input(observation, central),
                       torch.cat([observation, central], dim=-1))


def test_the_configured_module_equals_the_unconfigured_one_on_a_pre_transformed_input():
    offset, scale_values = affine_pair()
    absent, _ = build(discoverer_config())
    configured, _ = build(discoverer_config(**{AFFINE_FIELD: (offset, scale_values)}))
    for left, right in zip(absent.parameters(), configured.parameters()):
        assert torch.equal(left, right)  # the same initialisation, so only the input differs

    observation, central, hidden, skill = fixed_inputs()
    pre = transformed(central, offset, scale_values)
    assert torch.equal(configured._apply_central_input(observation, central),
                       absent._apply_central_input(observation, pre))
    with torch.no_grad():
        scaled_out = configured.forward(observation, skill, hidden, deterministic=True,
                                        central_input=central)
        manual_out = absent.forward(observation, skill, hidden, deterministic=True,
                                    central_input=pre)
        unscaled_out = absent.forward(observation, skill, hidden, deterministic=True,
                                      central_input=central)
    assert torch.equal(scaled_out[0], manual_out[0]) and torch.equal(scaled_out[1], manual_out[1])
    assert torch.equal(scaled_out[3], manual_out[3])
    assert not torch.equal(scaled_out[0], unscaled_out[0])  # the transform does reach the output
    # The sequence path of the update uses the same application point.
    sequence_observation = observation.unsqueeze(0).repeat(2, 1, 1)
    sequence_central = central.unsqueeze(0).repeat(2, 1, 1)
    assert torch.equal(
        configured._apply_central_input(sequence_observation, sequence_central),
        absent._apply_central_input(sequence_observation, transformed(
            sequence_central.reshape(-1, sequence_central.shape[-1]), offset, scale_values
        ).reshape(sequence_central.shape)))


def test_collection_and_replay_read_the_identical_scaled_actor_input(tmp_path, tiny):
    """The acting and replay paths of a real CF learner, with the field set."""
    offset, scale_values = affine_pair()
    envs, config, agent = cf.build(tmp_path, arm="CF", **{AFFINE_FIELD: (offset, scale_values)})
    agent.train(True)
    assert config.use_obsnorm is False and config.use_statenorm is False
    assert agent.skill_discoverer.use_central_state_affine is True
    offset_tensor = torch.tensor(offset, dtype=torch.float32)
    scale_tensor = torch.tensor(scale_values, dtype=torch.float32)

    collected, record = [], []
    cf.capture_actor_inputs(agent, collected)
    states, observations, dones = cf.collect(agent, envs, HORIZON, record=record)
    collected = np.stack(collected)

    # Acting: the state block the actor reads is the held snapshot on the environment's own scale.
    for step, row in enumerate(record):
        actor_input = collected[step].reshape(LANES, N_UAVS, -1)
        expected = ((torch.tensor(row["snapshot_states"], dtype=torch.float32) - offset_tensor)
                    / scale_tensor).numpy()
        for lane in range(LANES):
            for index in range(N_UAVS):
                block = actor_input[lane, index][config.obs_dim:config.obs_dim + config.state_dim]
                np.testing.assert_array_equal(block, expected[lane])
        assert abs(expected).max() <= 10.  # the raw metres are gone; nothing else is touched
    offsets = config.obs_dim + config.state_dim
    np.testing.assert_array_equal(
        collected[0, 0, offsets:offsets + N_UAVS * config.obs_dim],
        record[0]["snapshot_obs"][0].reshape(-1))

    class _NoShuffle:
        def shuffle(self, array):
            return None

    agent.rollout_buffer._sampler_rng = _NoShuffle()
    agent.config.ppo_epochs = 1
    agent.config.sequence_batch_size = 10 ** 6
    replayed = []
    original = agent.skill_discoverer.actor.evaluate_actions

    def spy(observations_seq, *args, **kwargs):
        replayed.append(np.array(observations_seq.detach().cpu().numpy(), copy=True))
        return original(observations_seq, *args, **kwargs)

    agent.skill_discoverer.actor.evaluate_actions = spy
    agent.update(last_values=np.zeros((LANES, N_UAVS), dtype=np.float32), dones=dones.copy(),
                 steps_in_buffer=HORIZON, last_state=states.copy(), last_observations=observations.copy())
    assert len(replayed) == 1
    sequence = replayed[0]
    assert sequence.shape == (K, (HORIZON // K) * LANES * N_UAVS,
                              config.obs_dim + agent.skill_discoverer.central_input_dim)
    for index in range(sequence.shape[1]):
        chunk, remainder = divmod(index, LANES * N_UAVS)
        lane, agent_index = divmod(remainder, N_UAVS)
        for local in range(K):
            np.testing.assert_array_equal(
                sequence[local, index], collected[chunk * K + local, lane * N_UAVS + agent_index])


@pytest.mark.parametrize("affine,message", [
    ((list(range(STATE_DIM - 1)), [1.] * (STATE_DIM - 1)), "must have length"),
    (([0.] * STATE_DIM, [1.] * (STATE_DIM - 1)), "must have length"),
    (([0.] * STATE_DIM, [1.] * (STATE_DIM - 1) + [0.]), "strictly positive"),
    (([0.] * STATE_DIM, [1.] * (STATE_DIM - 1) + [-2.]), "strictly positive"),
    (([0.] * STATE_DIM, [1.] * (STATE_DIM - 1) + [float("inf")]), "non-finite"),
    (([float("nan")] * STATE_DIM, [1.] * STATE_DIM), "non-finite"),
    (([0.] * STATE_DIM,), "pair"),  # not a pair at all
    ((0., 1.), "must have length"),  # a pair of scalars is not a pair of length-119 sequences
])
def test_a_malformed_affine_raises_at_construction(affine, message):
    with pytest.raises(ValueError, match=message):
        build(discoverer_config(**{AFFINE_FIELD: affine}))


def test_the_affine_requires_the_central_input_flag():
    offset, scale_values = affine_pair()
    with pytest.raises(ValueError, match="use_central_snapshot_in_flat_actor=True"):
        build(discoverer_config(use_central_snapshot_in_flat_actor=False,
                                **{AFFINE_FIELD: (offset, scale_values)}))
    # And the agent refuses it on any route where CF itself is refused.
    envs = [SimpleNamespace(state_dim=STATE_DIM, obs_dim=OBS_DIM) for _ in range(2)]
    matched.bind()
    config = matched.make_config("D1280", envs, SEED)
    setattr(config, AFFINE_FIELD, (offset, scale_values))
    with pytest.raises(ValueError):
        SkillDiscoverer(config, device=torch.device("cpu"))
