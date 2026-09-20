"""B/G construction, private-state and ordinary-feedback semantic checks."""

import torch

from experiments.candidates.ucope.reactive_rate_b03.scalar import ScalarGate
from experiments.candidates.ucope.scalar_feedback_b04 import study
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, templates
from experiments.candidates.ucope.uav_motion_prefix_b01.study import new_counts


def test_b_g_share_common_bytes_but_have_private_models_and_only_b_has_gate():
    master = 8931
    common = templates(master)
    rng_before = torch.random.get_rng_state().clone()
    b_actor, b_critic = study.make_arm(common, "B", master * 100000)
    g_actor, g_critic = study.make_arm(common, "G", master * 100000)
    assert torch.equal(rng_before, torch.random.get_rng_state())

    for module_b, module_g in (
        (b_actor.encoder, g_actor.encoder),
        (b_actor.gru, g_actor.gru),
        (b_actor.mean, g_actor.mean),
        (b_critic, g_critic),
    ):
        for name, value in module_b.state_dict().items():
            torch.testing.assert_close(value, module_g.state_dict()[name], rtol=0, atol=0)
        assert next(module_b.parameters()).data_ptr() != next(module_g.parameters()).data_ptr()
    torch.testing.assert_close(b_actor.log_std, g_actor.log_std, rtol=0, atol=0)
    assert b_actor.log_std.data_ptr() != g_actor.log_std.data_ptr()

    assert isinstance(b_actor.duration, ScalarGate)
    assert b_actor.duration_conditioned
    torch.testing.assert_close(
        b_actor.duration(torch.randn(5, 67)).softmax(-1),
        torch.full((5, 2), 0.5),
        rtol=0,
        atol=0,
    )
    assert g_actor.duration is None
    assert not g_actor.duration_conditioned


def test_g_snapshot_and_endpoint_explicitly_have_no_gate():
    actor, critic = study.make_arm(templates(8931), "G", 893100000)
    groups = study.snapshot(actor, critic)
    assert set(groups) == {"common_actor", "critic", "total"}
    endpoint = study._endpoint_gate("G", actor)
    assert endpoint == {
        "present": False,
        "parameters": 0,
        "raw_logits": None,
        "probabilities": None,
        "qualification": "Ordinary G has no duration head or gate probabilities.",
    }


def test_g_uses_ordinary_fresh_each_tick_semantics_and_update():
    actor, critic = study.make_arm(templates(9931), "G", 993100000)
    counts = new_counts(renewal=True, short=True)
    emitted = []
    episodes = []
    for episode_index in range(2):
        episodes.append(
            learner.collect_episode(
                SyntheticAdapter(19, 8),
                actor,
                critic,
                8,
                90 + episode_index,
                generator(21 + episode_index),
                generator(31 + episode_index),
                {"arm": "G", "phase": "train", "episode": episode_index},
                lambda: None,
                counts,
                emitted.append,
                lambda row: None,
                [],
                ratio_grouping="agent_compound",
                value_moments=None,
                renewal=True,
                duration_support=(1, 2),
            )
        )
    rollout = {
        key: torch.stack([episode[key] for episode in episodes])
        for key in episodes[0]
    }
    assert rollout["velocity_mask"].all()
    assert not rollout["duration_mask"].any()
    assert not rollout["durations"].any()
    assert not rollout["obs"][..., -1].any()
    assert [row["velocity_decisions"] for row in emitted] == [40, 40]
    assert [row["duration_decisions"] for row in emitted] == [0, 0]

    initial = study.snapshot(actor, critic)
    records = learner.update(
        actor,
        critic,
        learner.optimizer_for(actor, critic),
        episodes,
        4,
        lambda: None,
        counts,
        ratio_grouping="agent_compound",
        entropy_coef=0.0,
        value_moments=None,
    )
    movement = study.exposure(initial, actor, critic)
    assert len(records) == counts["optimizer_steps"] == 4
    assert all("entropy" in record for record in records)
    assert movement["common_actor"]["displacement"] > 0
    assert movement["critic"]["displacement"] > 0
    assert "duration" not in movement
