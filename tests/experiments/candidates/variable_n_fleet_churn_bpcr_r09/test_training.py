import math
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_training import ConcreteTrainSlotService,_model_inputs,_resume_initial_pair,_resume_state_pair,_validate_generation_chain,make_optimizer
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.contracts import canonical_json_bytes
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import deterministic_general_episode
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.models import direct_parameter_shapes,mapr_parameter_shapes
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import NativeInteractiveBatch
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.torch_models import DirectSetAR,MAPR4

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.training import (
    adamw_decay_groups,
    explicit_stiefel_fixture,
    frozen_minibatches,
    gae_terminal,
    normalize_advantages,
    ppo_loss,
    work_count_contract,
)


def test_identity_free_gae_normalization_and_minibatches() -> None:
    values=torch.zeros((16,6),dtype=torch.float64);objective=torch.ones(16,dtype=torch.float64)
    advantages,returns=gae_terminal(values,objective)
    assert torch.allclose(advantages[0],torch.tensor([0.95**5,0.95**4,0.95**3,0.95**2,0.95,1.0],dtype=torch.float64))
    assert torch.isfinite(normalize_advantages(advantages)).all()
    assert torch.equal(normalize_advantages(torch.ones(96)),torch.zeros(96))
    blocks=frozen_minibatches(tuple(reversed(range(96))))
    assert len(blocks)==4 and all(len(block)==24 for block in blocks)


def test_exact_ppo_loss_decay_and_work_counts() -> None:
    shape=(24,);zeros=torch.zeros(shape,dtype=torch.float64);ones=torch.ones(shape,dtype=torch.float64)
    losses=ppo_loss(zeros,zeros,ones,zeros,ones,torch.ones((24,4),dtype=torch.float64),torch.tensor([[1,1,0,0]]*24,dtype=torch.float64))
    assert torch.isclose(losses["actor"],torch.tensor(-1.0,dtype=torch.float64))
    assert torch.isclose(losses["value"],torch.tensor(1.0,dtype=torch.float64))
    assert torch.isclose(losses["entropy"],torch.tensor(0.5,dtype=torch.float64))
    assert torch.isclose(losses["total"],torch.tensor(-0.505,dtype=torch.float64))
    groups=adamw_decay_groups({"weight":torch.zeros((2,2)),"embedding":torch.zeros((4,16)),"bias":torch.zeros(2)})
    assert groups=={"decay_1e-4":("embedding","weight"),"decay_zero":("bias",)}
    assert work_count_contract()["learned_joint_decisions"]==786432


def test_canonical_stiefel_fixture_has_frozen_orientation() -> None:
    x=np.arange(1,7,dtype=np.float64)
    source=np.stack((np.ones(6),x,x*x,x*x*x),axis=1)
    q=explicit_stiefel_fixture(source,(4,6),math.sqrt(2.0))
    assert q.shape==(4,6)
    assert np.allclose(q@q.T,2.0*np.eye(4),rtol=0,atol=2e-14)
    assert np.array_equal(q,explicit_stiefel_fixture(source,(4,6),math.sqrt(2.0)))


def test_first_train_optimizer_step_keeps_masked_entropy_gradient_finite() -> None:
    parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in mapr_parameter_shapes().items()};model=MAPR4(parameters);optimizer=make_optimizer(model)
    fixtures=tuple(deterministic_general_episode(1+index%2) for index in range(8));batch=NativeInteractiveBatch(fixtures)
    try:
        observations=tuple(row["next_observation"] for row in batch.initial);failed=tuple(row["failed_rank"] for row in batch.initial)
        inputs=[_model_inputs(observation,fixture,failed_rank) for observation,fixture,failed_rank in zip(observations,fixtures,failed)];stacked=tuple(torch.cat([row[index] for row in inputs],0) for index in range(6));uniforms=torch.full((8,4),0.5,dtype=torch.float64)
        output=model(*stacked,uniforms);loss=ppo_loss(output["log_probability"],output["log_probability"].detach(),torch.ones(8,dtype=torch.float64),output["value"],torch.ones(8,dtype=torch.float64),output["token_entropies"],(stacked[4]<0).to(torch.float64));optimizer.zero_grad(set_to_none=True);loss["total"].backward();optimizer.step()
        assert all(torch.isfinite(parameter).all() for parameter in model.parameters())
        second=model(*stacked,uniforms);assert torch.isfinite(second["value"]).all() and torch.isfinite(second["token_entropies"]).all()
    finally:batch.close()


def test_same_coordinate_resume_reuses_complete_initial_pair_without_overwrite(tmp_path) -> None:
    parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in mapr_parameter_shapes().items()};original=MAPR4(parameters);original_optimizer=make_optimizer(original);checkpoint=tmp_path/"initial.checkpoint.pt";optimizer_path=tmp_path/"initial.optimizer.pt";torch.save(original.state_dict(),checkpoint);torch.save(original_optimizer.state_dict(),optimizer_path)
    before=(checkpoint.read_bytes(),optimizer_path.read_bytes());resumed=MAPR4(parameters);resumed_optimizer=make_optimizer(resumed);digests=_resume_initial_pair(resumed,resumed_optimizer,checkpoint,optimizer_path)
    assert digests==(hashlib.sha256(before[0]).hexdigest(),hashlib.sha256(before[1]).hexdigest()) and (checkpoint.read_bytes(),optimizer_path.read_bytes())==before
    changed=original.state_dict();changed[next(iter(changed))]=changed[next(iter(changed))].clone()+1;torch.save(changed,checkpoint)
    with pytest.raises(RuntimeError,match="same-coordinate"):_resume_initial_pair(MAPR4(parameters),make_optimizer(MAPR4(parameters)),checkpoint,optimizer_path)
    direct_parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in direct_parameter_shapes().items()};direct=DirectSetAR(direct_parameters);direct_optimizer=make_optimizer(direct);direct_checkpoint=tmp_path/"DIRECT.initial.checkpoint.pt";direct_optimizer_path=tmp_path/"DIRECT.initial.optimizer.pt";torch.save(direct.state_dict(),direct_checkpoint);torch.save(direct_optimizer.state_dict(),direct_optimizer_path);direct_before=(direct_checkpoint.read_bytes(),direct_optimizer_path.read_bytes());resumed_direct=DirectSetAR(direct_parameters)
    assert _resume_initial_pair(resumed_direct,make_optimizer(resumed_direct),direct_checkpoint,direct_optimizer_path)==(hashlib.sha256(direct_before[0]).hexdigest(),hashlib.sha256(direct_before[1]).hexdigest()) and (direct_checkpoint.read_bytes(),direct_optimizer_path.read_bytes())==direct_before


def test_direct_first_step_anomaly_detection_preserves_containment_and_gradients() -> None:
    mapr_parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in mapr_parameter_shapes().items()};direct_parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in direct_parameter_shapes().items()};mapr=MAPR4(mapr_parameters);direct=DirectSetAR(direct_parameters);optimizer=make_optimizer(direct)
    fixtures=tuple(deterministic_general_episode(1+index%2) for index in range(8));batch=NativeInteractiveBatch(fixtures)
    try:
        observations=tuple(row["next_observation"] for row in batch.initial);failed=tuple(row["failed_rank"] for row in batch.initial);inputs=[_model_inputs(observation,fixture,failed_rank) for observation,fixture,failed_rank in zip(observations,fixtures,failed)];stacked=tuple(torch.cat([row[index] for row in inputs],0) for index in range(6));uniforms=torch.full((8,4),0.5,dtype=torch.float64)
        mapr_output=mapr(*stacked,uniforms);direct_output=direct(*stacked,uniforms);assert torch.equal(direct_output["command"],mapr_output["command"]) and torch.equal(direct_output["token_probabilities"],mapr_output["token_probabilities"])
        loss=ppo_loss(direct_output["log_probability"],direct_output["log_probability"].detach(),torch.ones(8,dtype=torch.float64),direct_output["value"],torch.ones(8,dtype=torch.float64),direct_output["token_entropies"],(stacked[4]<0).to(torch.float64));optimizer.zero_grad(set_to_none=True)
        with torch.autograd.detect_anomaly(check_nan=True):loss["total"].backward()
        optimizer.step();assert all(torch.isfinite(parameter).all() for parameter in direct.parameters())
    finally:batch.close()


def _write_exact_generation_chain(root,slot,count,final_state=None) -> None:
    bindings=root/"bindings.json"
    if not bindings.exists():bindings.write_bytes(canonical_json_bytes({"construction":"origin-bindings"}))
    bindings_sha=hashlib.sha256(bindings.read_bytes()).hexdigest();previous=None
    for generation in range(1,count+1):
        state_path=root/f"{slot}.state.g{generation:04d}.pt"
        if generation==count and final_state is not None:torch.save(final_state,state_path)
        else:state_path.write_bytes(f"construction-state-{generation}".encode("ascii"))
        value={"schema":"VNFC_BPCR_R09_BLINDED_GENERATION_V1","slot":slot,"generation":generation,"previous_generation_sha256":previous,"bindings_sha256":bindings_sha,"state_path":state_path.name,"state_sha256":hashlib.sha256(state_path.read_bytes()).hexdigest(),"optimizer_step":generation*16,"training_episodes_completed":generation*16,"joint_decisions_completed":generation*96,"scientific_values_exposed":False,"partial_inspection_permitted":False};raw=canonical_json_bytes(value);(root/f"{slot}.g{generation:04d}.json").write_bytes(raw);previous=hashlib.sha256(raw).hexdigest()


def test_completed_slot_returns_receipt_without_rewrite_or_rerun(monkeypatch:pytest.MonkeyPatch,tmp_path) -> None:
    role="BPCR-REP-00";arm="MAPR";slot=f"{role}.{arm}";mapr_parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in mapr_parameter_shapes().items()};direct_parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in direct_parameter_shapes().items()};model=MAPR4(mapr_parameters);optimizer=make_optimizer(model)
    initial_checkpoint=tmp_path/f"{slot}.initial.checkpoint.pt";initial_optimizer=tmp_path/f"{slot}.initial.optimizer.pt";final_checkpoint=tmp_path/f"{slot}.final.checkpoint.pt";final_optimizer=tmp_path/f"{slot}.final.optimizer.pt";state_path=tmp_path/f"{slot}.state.g0256.pt"
    for path,value in ((initial_checkpoint,model.state_dict()),(initial_optimizer,optimizer.state_dict()),(final_checkpoint,model.state_dict()),(final_optimizer,optimizer.state_dict()),(state_path,{"model":model.state_dict(),"optimizer":optimizer.state_dict(),"update":256})):torch.save(value,path)
    state_path.unlink();_write_exact_generation_chain(tmp_path,slot,256,{"model":model.state_dict(),"optimizer":optimizer.state_dict(),"update":256})
    frontier=SimpleNamespace(root=tmp_path,bindings=SimpleNamespace(),append_generation=lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError("completed slot reran")));service=ConcreteTrainSlotService(frontier);monkeypatch.setattr(service,"_initial_parameters",lambda *args,**kwargs:(mapr_parameters,direct_parameters))
    permit=SimpleNamespace(phase="TRAIN",source_manifest_sha256="1"*64,coordinate_digest="2"*64,origin_lease_id="construction-origin",require_active=lambda **kwargs:None);authority=SimpleNamespace(permit=permit);rng=SimpleNamespace(master_digest="3"*64,require_frontier_binding=lambda bindings:None)
    before={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir() if path.is_file()};receipt=service.train_slot(authority,rng,role,arm,now=SimpleNamespace());after={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir() if path.is_file()}
    assert before==after and receipt["update"]==256 and receipt["final_checkpoint_sha256"]==before[final_checkpoint.name] and receipt["final_optimizer_sha256"]==before[final_optimizer.name]


@pytest.mark.parametrize("mutation",["missing_middle","wrong_predecessor","wrong_state_hash","wrong_state_path","wrong_count"])
def test_generation_chain_rejects_every_address_predecessor_state_and_count_mutation(tmp_path,mutation) -> None:
    slot="BPCR-REP-00.MAPR";_write_exact_generation_chain(tmp_path,slot,3);valid=_validate_generation_chain(tmp_path,slot);assert valid is not None and valid[0]["generation"]==3
    target=tmp_path/f"{slot}.g0002.json"
    if mutation=="missing_middle":target.unlink()
    else:
        value=json.loads(target.read_text("ascii"))
        if mutation=="wrong_predecessor":value["previous_generation_sha256"]="0"*64
        elif mutation=="wrong_state_hash":value["state_sha256"]="0"*64
        elif mutation=="wrong_state_path":value["state_path"]="../escape.pt"
        else:value["optimizer_step"]+=1
        target.write_bytes(canonical_json_bytes(value))
    with pytest.raises(RuntimeError,match="generation"):_validate_generation_chain(tmp_path,slot)


def test_final_pair_rejects_partial_and_mismatched_state(tmp_path) -> None:
    parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in mapr_parameter_shapes().items()};model=MAPR4(parameters);optimizer=make_optimizer(model);checkpoint=tmp_path/"final.pt";optimizer_path=tmp_path/"final.optimizer.pt";torch.save(model.state_dict(),checkpoint)
    with pytest.raises(RuntimeError,match="partial final"):_resume_state_pair(model,optimizer,checkpoint,optimizer_path,"final")
    torch.save(optimizer.state_dict(),optimizer_path);changed=model.state_dict();key=next(iter(changed));changed[key]=changed[key].clone()+1;torch.save(changed,checkpoint)
    with pytest.raises(RuntimeError,match="expected same-coordinate"):_resume_state_pair(model,optimizer,checkpoint,optimizer_path,"final")
