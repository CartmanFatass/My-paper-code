from __future__ import annotations

import copy
import json

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from experiments.candidates.eociv_lite import actor_anchored_critic_clip_root_cross as b6
from experiments.candidates.eociv_lite import actor_anchored_gradient_geometry as geom
from experiments.candidates.eociv_lite import payload_content_learnability as b2
from experiments.candidates.eociv_lite import sibling_env as sib


def test_plan_counts_ids_and_rosters_are_exact() -> None:
    assert (b6.FULL_PLAN.training_episodes, b6.FULL_PLAN.diagnostic_episodes, b6.FULL_PLAN.evaluation_episodes) == (576, 324, 243)
    assert (b6.FULL_PLAN.total_episodes, b6.FULL_PLAN.total_transitions, b6.FULL_PLAN.optimizer_updates) == (1_143, 54_864, 144)
    assert (b6.SMOKE_PLAN.training_episodes, b6.SMOKE_PLAN.diagnostic_episodes, b6.SMOKE_PLAN.evaluation_episodes) == (8, 12, 9)
    assert (b6.SMOKE_PLAN.total_episodes, b6.SMOKE_PLAN.total_transitions, b6.SMOKE_PLAN.optimizer_updates) == (29, 1_392, 2)
    assert b6.training_episode_id(2, 1, 7) == 18_210_007
    assert b6.heldout_episode_id(2, 2) == 19_020_002
    assert b6.diagnostic_tape_identity(2) == 19_900_002
    assert set(b6.training_episode_id(s,p,r) for s in range(3) for p in range(3) for r in range(8)).isdisjoint(
        {b6.heldout_episode_id(p,r) for p in range(3) for r in range(3)}
    )
    assert b6.CRITICAL_TUPLES == ((sib.SHOCK_A,sib.SHOCK_A),(sib.SHOCK_A,sib.SHOCK_B),(sib.SHOCK_B,sib.SHOCK_A),(sib.SHOCK_B,sib.SHOCK_B))


def test_parameter_layout_groups_and_structural_zeros_are_exact() -> None:
    actor = b6._new_actor(87031)
    layout = geom.ordered_layout(actor)
    assert [row["name"] for row in layout["parameters"]] == list(geom.EXPECTED_PARAMETER_NAMES)
    assert layout["total_numel"] == 1061
    assert {key: len(value) for key,value in layout["group_indices"].items()} == {"shared_trunk":1008,"policy_head":36,"value_head":17}
    actor.set_capture(True)
    runner = b6._runner(actor,b6.PROFILES[0],b6.training_episode_id(0,0,0),b2._correct_body,shock_tuple=b6.CRITICAL_TUPLES[0],noise=None)
    from experiments.candidates.eociv_lite import host_reward_snr_discrimination as b5
    aloss,closs,_=b5._episode_loss_tensors(actor,runner.env.reward_trace)
    a,v=geom.actor_critic_vectors(aloss,closs,actor)
    assert torch.count_nonzero(a[layout["group_indices"]["value_head"]]).item()==0
    assert torch.count_nonzero(v[layout["group_indices"]["policy_head"]]).item()==0


def test_projection_alpha_zero_and_nonfinite_fail_closed() -> None:
    a=torch.tensor([3.0,4.0],dtype=torch.float64)
    v=torch.tensor([0.0,10.0],dtype=torch.float64)
    result=geom.intervention_vectors(a,v)
    assert result["alpha"]==pytest.approx(0.05)
    assert geom.l2_norm(result["alpha"]*v)<=0.5
    assert geom.l2_norm(result["baseline"])==pytest.approx(0.5)
    assert geom.intervention_vectors(a,torch.zeros_like(a))["alpha"]==1.0
    with pytest.raises(geom.GeometryError,match="zero actor"):
        geom.intervention_vectors(torch.zeros_like(a),v)
    with pytest.raises(geom.GeometryError,match="nonfinite"):
        geom.intervention_vectors(torch.tensor([float("nan"),1.0]),v)


def test_exact_assignment_and_copied_adam_match_actual_cloned_step_without_mutation() -> None:
    actor=b6._new_actor(87031); optimizer=b6._new_optimizer(actor)
    gradient=torch.linspace(-0.25,0.25,1061,dtype=torch.float64)
    before=[p.detach().clone() for p in actor.parameters()]
    before_mom=copy.deepcopy(optimizer.state_dict())
    predicted=geom.copied_adam_next_delta(actor,optimizer,gradient)
    assert all(torch.equal(p,q) for p,q in zip(actor.parameters(),before))
    for key in before_mom["state"]:
        assert all(torch.equal(optimizer.state_dict()["state"][key][field],before_mom["state"][key][field]) for field in ("step","exp_avg","exp_avg_sq"))
    geom.assign_gradient_vector(actor,gradient); optimizer.step()
    actual=torch.cat([(p.detach()-q).reshape(-1).double() for p,q in zip(actor.parameters(),before)])
    assert torch.equal(predicted,actual)


def test_parameter_and_optimizer_base64_roundtrip_is_bit_exact() -> None:
    actor=b6._new_actor(87032); optimizer=b6._new_optimizer(actor)
    parameters=geom.serialize_parameter_state(actor); moments=geom.serialize_optimizer_state(actor,optimizer)
    assert len(parameters["tensors"])==10 and len(moments["states"])==10
    assert all(torch.equal(parameter.detach().cpu(),geom.tensor_from_record(record)) for parameter,record in zip(actor.parameters(),parameters["tensors"]))
    assert all(float(geom.tensor_from_record(row["state"][0]))==0.0 for row in moments["states"])


def test_four_strata_share_root_lifecycle_and_tape() -> None:
    actor=b6._new_actor(87031)
    a,v,rows=b6._four_episode_gradients(actor,b6.PROFILES[0],b6.training_episode_id(0,0,0))
    assert a.shape==v.shape==(1061,)
    assert [row["critical_shock_tuple"] for row in rows]==[list(value) for value in b6.CRITICAL_TUPLES]
    assert len({row["public_world_digest"] for row in rows})==len({row["lifecycle_digest"] for row in rows})==len({row["action_noise_tape_digest"] for row in rows})==1
    assert all(row["accepted_boundary_ticks"]==list(sib.EVENT_TIMES) for row in rows)


def test_energy_identity_and_synthetic_balanced_factorial_reconstruct() -> None:
    actor=b6._new_actor(87031); layout=geom.ordered_layout(actor)
    a=torch.arange(1061,dtype=torch.float64)/1000
    v=torch.flip(a,[0])-0.2
    identity=geom.energy_identity(a,v,layout)
    assert all(abs(row["identity_residual"])<1e-8 for row in identity.values())
    assert all(-1.0 <= row["bounded_overlap"] <= 1.0 for row in identity.values())
    zero_identity=geom.energy_identity(torch.zeros_like(a),v,layout)
    assert all(row["bounded_overlap"] == 0.0 for row in zero_identity.values())
    acells={}; ccells={}
    for si,state in enumerate(b6.STATE_LEVELS):
        for root in range(3):
            for shock in range(4):
                acells[(state,root,shock)]=torch.full((1061,),float(si+2*root+3*shock))
                ccells[(state,root,shock)]=torch.full((1061,),float(5*si-root+shock))
    result=geom.balanced_factorial(acells,ccells,layout)
    assert result["reconstruction_max"]<1e-10
    for term in ("state","root","shock","state_x_root","state_x_shock","root_x_shock","state_x_root_x_shock"):
        assert abs(result[term]["identity_residual"])<1e-8
        assert set(result["groups"])==set(geom.GROUPS)


@pytest.fixture(scope="module")
def smoke_pair():
    kwargs={"source_commit":"33ffb79a0655b0a3b4415be2203c35cf077f6570","run_id":"eociv_b6_focused_smoke"}
    return b6.run_train("smoke",**kwargs),b6.run_train("smoke",**kwargs)


def test_smoke_is_deterministic_matched_complete_and_technical_only(smoke_pair) -> None:
    first,second=smoke_pair
    assert json.dumps(first,sort_keys=True)==json.dumps(second,sort_keys=True)
    assert first["counts"]=={"training_episodes":8,"diagnostic_episodes":12,"evaluation_episodes":9,"total_episodes":29,"environment_transitions":1392,"policy_calls":1392,"optimizer_updates":2,"trained_actors":2,"retained_states":3,"hypothetical_transitions":0,"coefficient_searches":0,"rescue_arms":0}
    assert len(first["training_updates"])==2 and len(first["diagnostic_cells"])==12 and len(first["evaluation_rows"])==3
    assert all(all(value for key,value in row.items() if key!="actor_seed") for row in first["training_matching"])
    assert len({row["action_noise_tape_digest"] for row in first["diagnostic_cells"]})==1
    assert all(row["state_identity_before"]==row["state_identity_after"] for row in first["copied_adam_rows"])
    retained={(row["actor_seed"],row["state_level"]):row["identity"] for row in first["retained_states"]}
    for condition,final_level in ((b6.CONDITIONS[0],"BASELINE_FINAL"),(b6.CONDITIONS[1],"TREATMENT_FINAL")):
        row=next(row for row in first["training_updates"] if row["condition"]==condition)
        assert row["pre_step_state_identity"]==retained[(87031,"INIT")]
        assert row["post_step_state_identity"]==retained[(87031,final_level)]
    receipt=b6.evaluate_raw(first); analysis=b6.analyze_evaluation(receipt)
    assert receipt["technical_only"] and not receipt["scientific_terminal_admitted"]
    assert analysis["technical_only"] and analysis["terminal_label"] is None
    assert all(receipt["fidelity"].values())


def test_full_admission_rejects_count_and_shape_drift(smoke_pair) -> None:
    raw=copy.deepcopy(smoke_pair[0]); raw["counts"]["total_episodes"]+=1
    with pytest.raises(RuntimeError,match="count admission"):
        b6.evaluate_raw(raw)
    raw=copy.deepcopy(smoke_pair[0]); raw["diagnostic_cells"].pop()
    with pytest.raises(RuntimeError,match="shape admission"):
        b6.evaluate_raw(raw)


def test_update_identity_chain_rejects_broken_middle_link() -> None:
    init={"parameter_state_sha256":"init","optimizer_state_sha256":"zero","layout_sha256":"layout"}
    middle={"parameter_state_sha256":"middle","optimizer_state_sha256":"one","layout_sha256":"layout"}
    final={"parameter_state_sha256":"final","optimizer_state_sha256":"two","layout_sha256":"layout"}
    rows=[{"pre_step_state_identity":copy.deepcopy(init),"post_step_state_identity":copy.deepcopy(middle)},{"pre_step_state_identity":copy.deepcopy(middle),"post_step_state_identity":copy.deepcopy(final)}]
    b6._validate_update_identity_chain(rows,init,final)
    broken=copy.deepcopy(rows); broken[1]["pre_step_state_identity"]["parameter_state_sha256"]="broken"
    with pytest.raises(RuntimeError,match="chain continuity"):
        b6._validate_update_identity_chain(broken,init,final)
