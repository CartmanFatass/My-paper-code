"""CPU-only fixed-budget PPO/GAE/AdamW execution surfaces."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping,Sequence
from datetime import datetime
from pathlib import Path
import hashlib,io,json,re
import numpy as np
import torch
from torch import nn

from .training import adamw_decay_groups,frozen_minibatches,gae_terminal,normalize_advantages,ppo_loss
from .torch_models import MAPR4,DirectSetAR,mapr_parameter_shapes,direct_parameter_shapes,materialize_external_initialization
from .rng import EmpiricalRNG,address
from .services import build_world,_shuffle
from .native_backend import NativeInteractiveBatch
from .frontier import AtomicFrontier
from .lifecycle import write_once
from .contracts import canonical_json_bytes

@dataclass(frozen=True)
class TrainerConfig:
    updates:int=256;episodes_per_update:int=16;decisions_per_episode:int=6;epochs:int=4;minibatch_size:int=24;learning_rate:float=3e-4;betas:tuple[float,float]=(0.9,0.999);epsilon:float=1e-8;weight_decay:float=1e-4;max_grad_norm:float=0.5

def make_optimizer(model:nn.Module)->torch.optim.AdamW:
    named=dict(model.named_parameters());groups=adamw_decay_groups(named);decay=[named[n] for n in groups["decay_1e-4"]];plain=[named[n] for n in groups["decay_zero"]]
    return torch.optim.AdamW([{"params":decay,"weight_decay":1e-4},{"params":plain,"weight_decay":0.0}],lr=3e-4,betas=(0.9,0.999),eps=1e-8)

def _state_equal(left:object,right:object)->bool:
    if isinstance(left,torch.Tensor) and isinstance(right,torch.Tensor):return left.dtype==right.dtype and left.device==right.device and torch.equal(left,right)
    if isinstance(left,Mapping) and isinstance(right,Mapping):return set(left)==set(right) and all(_state_equal(left[key],right[key]) for key in left)
    if isinstance(left,(list,tuple)) and isinstance(right,(list,tuple)):return len(left)==len(right) and all(_state_equal(a,b) for a,b in zip(left,right))
    return left==right

def _resume_state_pair(model:nn.Module,optimizer:torch.optim.AdamW,checkpoint_path:Path,optimizer_path:Path,kind:str)->tuple[str,str]|None:
    present=(checkpoint_path.is_file(),optimizer_path.is_file())
    if present==(False,False):return None
    if present!=(True,True):raise RuntimeError(f"partial {kind} checkpoint/optimizer pair")
    checkpoint=torch.load(checkpoint_path,map_location="cpu",weights_only=True);optimizer_state=torch.load(optimizer_path,map_location="cpu",weights_only=True)
    if not isinstance(checkpoint,Mapping) or not _state_equal(checkpoint,model.state_dict()):raise RuntimeError(f"existing {kind} checkpoint differs from expected same-coordinate state")
    if not isinstance(optimizer_state,Mapping) or not _state_equal(optimizer_state,optimizer.state_dict()):raise RuntimeError(f"existing {kind} optimizer differs from expected same-coordinate state")
    model.load_state_dict(checkpoint);optimizer.load_state_dict(optimizer_state)
    return hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),hashlib.sha256(optimizer_path.read_bytes()).hexdigest()

def _resume_initial_pair(model:nn.Module,optimizer:torch.optim.AdamW,checkpoint_path:Path,optimizer_path:Path)->tuple[str,str]|None:return _resume_state_pair(model,optimizer,checkpoint_path,optimizer_path,"initial")

def _validate_generation_chain(frontier_root:Path,slot:str)->tuple[dict[str,object],Path,str]|None:
    root=Path(frontier_root);paths=sorted(root.glob(f"{slot}.g*.json"))
    if not paths:return None
    pattern=re.compile(rf"^{re.escape(slot)}\.g([0-9]{{4}})\.json$");addressed=[]
    for path in paths:
        match=pattern.fullmatch(path.name)
        if match is None:raise RuntimeError("generation filename/address inventory differs")
        addressed.append((int(match.group(1)),path))
    numbers=[number for number,_ in addressed];last_number=max(numbers)
    if last_number<1 or last_number>256 or numbers!=list(range(1,last_number+1)):raise RuntimeError("generation filename/address inventory has gaps or extras")
    bindings_path=root/"bindings.json"
    if not bindings_path.is_file():raise RuntimeError("generation origin bindings are absent")
    bindings_sha=hashlib.sha256(bindings_path.read_bytes()).hexdigest();previous=None;last_value:dict[str,object]|None=None;last_state:Path|None=None;last_digest=""
    required={"schema","slot","generation","previous_generation_sha256","bindings_sha256","state_path","state_sha256","optimizer_step","training_episodes_completed","joint_decisions_completed","scientific_values_exposed","partial_inspection_permitted"}
    for generation,path in addressed:
        try:raw=path.read_bytes();value=json.loads(raw.decode("ascii"))
        except (OSError,UnicodeError,json.JSONDecodeError) as error:raise RuntimeError("generation record cannot be read") from error
        if not isinstance(value,dict) or set(value)!=required or raw!=canonical_json_bytes(value):raise RuntimeError("generation schema/field inventory differs")
        expected={"schema":"VNFC_BPCR_R09_BLINDED_GENERATION_V1","slot":slot,"generation":generation,"previous_generation_sha256":previous,"bindings_sha256":bindings_sha,"state_path":f"{slot}.state.g{generation:04d}.pt","optimizer_step":generation*16,"training_episodes_completed":generation*16,"joint_decisions_completed":generation*96,"scientific_values_exposed":False,"partial_inspection_permitted":False}
        if any(value.get(key)!=expected_value for key,expected_value in expected.items()):raise RuntimeError("generation address/count/predecessor binding differs")
        state_path=root/str(value["state_path"])
        try:state_path.resolve().relative_to(root.resolve())
        except ValueError as error:raise RuntimeError("generation state path escapes frontier") from error
        state_sha=value.get("state_sha256")
        if not isinstance(state_sha,str) or len(state_sha)!=64 or not state_path.is_file() or hashlib.sha256(state_path.read_bytes()).hexdigest()!=state_sha:raise RuntimeError("generation state path/hash differs")
        last_digest=hashlib.sha256(raw).hexdigest();previous=last_digest;last_value=value;last_state=state_path
    assert last_value is not None and last_state is not None
    return last_value,last_state,last_digest

def train_update(model:nn.Module,optimizer:torch.optim.AdamW,batch:Mapping[str,torch.Tensor],permutations:Sequence[Sequence[int]])->dict[str,int]:
    if any(parameter.device.type!="cpu" for parameter in model.parameters()):raise RuntimeError("revision-09 trainer is CPU-only")
    if len(permutations)!=4:raise ValueError("one permutation is required per PPO epoch")
    torch.set_num_threads(1);advantages,returns=gae_terminal(batch["old_values"].reshape(16,6),batch["terminal_objective"]);advantages=normalize_advantages(advantages).reshape(96);returns=returns.reshape(96);steps=0
    for permutation in permutations:
        for indices in frozen_minibatches(permutation):
            ix=torch.tensor(indices,dtype=torch.int64);output=model(*[batch[name][ix] for name in ("agents","zones","globals","legal_masks","fixed_occupants","opaque_ranks","uniforms")]);loss=ppo_loss(output["log_probability"],batch["old_log_probability"][ix],advantages[ix],output["value"],returns[ix],output["token_entropies"],batch["token_is_variable"][ix]);optimizer.zero_grad(set_to_none=True);loss["total"].backward();torch.nn.utils.clip_grad_norm_(model.parameters(),0.5);optimizer.step();steps+=1
    return {"episodes":16,"joint_decisions":96,"optimizer_steps":steps}

def _normal_source_shape(shape:tuple[int,int])->tuple[int,int]:return (shape[1],shape[0]) if shape[0]<=shape[1] else shape

def _model_inputs(trace:Mapping[str,object],fixture:object,failed_rank:int)->tuple[torch.Tensor,...]:
    active=int(trace["active_count"]);agents=np.asarray(trace["agent_rows"],dtype=np.float64).reshape(active,38);zones=np.asarray(trace["zone_rows"],dtype=np.float64).reshape(2,15);globals_=np.asarray(trace["globals"],dtype=np.float64);legal=np.asarray(trace["legality"],dtype=np.float64).reshape(active,4);epoch=int(trace["epoch"]);presented=tuple(rank for rank in fixture.post_presentations[epoch] if rank!=failed_rank);order=(0,1,2,3) if fixture.failed_zone==1 else (2,3,0,1);fixed=np.full(4,-1,dtype=np.int64)
    for row,data in enumerate(agents):
        if np.any(data[8:18]==1):
            token=int(np.argmax(data[20:25]));
            if token<4:fixed[order.index(token)]=row
    opaque_by_rank={a.rank:a.opaque_rank for a in fixture.agents};opaque=np.asarray([opaque_by_rank[r] for r in presented],dtype=np.int64)
    return (torch.from_numpy(agents)[None],torch.from_numpy(zones)[None],torch.from_numpy(globals_)[None],torch.from_numpy(legal[:,order])[None],torch.from_numpy(fixed)[None],torch.from_numpy(opaque)[None])

class ConcreteTrainSlotService:
    """Exact future slot executor; constructor performs no initialization or activity."""
    def __init__(self,frontier:AtomicFrontier):self.frontier=frontier
    def _initial_parameters(self,rng:EmpiricalRNG,role:str,now:datetime)->tuple[dict[str,torch.Tensor],dict[str,torch.Tensor]]:
        base={};residual={}
        for name,shape in mapr_parameter_shapes().items():
            if len(shape)!=2:continue
            source_shape=_normal_source_shape(shape);builder=lambda draw,n=name:address(replicate_role=role,domain="model-initialization/base",purpose=n,roster_size=3,failed_zone=1,update_or_panel_row=0,episode_row=0,physical_time=0,draw=draw);base[name]=("model-initialization/base",rng.normal_array(source_shape,builder,now=now))
        for name in ("residual.0.weight","residual.1.weight"):
            shape=direct_parameter_shapes()[name];builder=lambda draw,n=name:address(replicate_role=role,domain="model-initialization/direct-residual",purpose=n,roster_size=3,failed_zone=1,update_or_panel_row=0,episode_row=0,physical_time=0,draw=draw);residual[name]=("model-initialization/direct-residual",rng.normal_array(_normal_source_shape(shape),builder,now=now))
        return materialize_external_initialization(base,residual)
    def _save(self,path:Path,value:object)->str:
        buffer=io.BytesIO();torch.save(value,buffer);return write_once(path,buffer.getvalue())
    @staticmethod
    def _receipt(permit:object,rng:EmpiricalRNG,replicate_role:str,arm:str,initial_checkpoint:Path,initial_checkpoint_sha:str,final_checkpoint:Path,final_checkpoint_sha:str,initial_optimizer:Path,initial_optimizer_sha:str,final_optimizer:Path,final_optimizer_sha:str)->dict[str,object]:
        return {"replicate_role":replicate_role,"arm":arm,"initial_checkpoint_path":str(initial_checkpoint.resolve()),"initial_checkpoint_sha256":initial_checkpoint_sha,"final_checkpoint_path":str(final_checkpoint.resolve()),"final_checkpoint_sha256":final_checkpoint_sha,"initial_optimizer_path":str(initial_optimizer.resolve()),"initial_optimizer_sha256":initial_optimizer_sha,"final_optimizer_path":str(final_optimizer.resolve()),"final_optimizer_sha256":final_optimizer_sha,"update":256,"source_manifest_sha256":permit.source_manifest_sha256,"coordinate_digest":permit.coordinate_digest,"master_digest":rng.master_digest,"origin_lease_id":permit.origin_lease_id,"externally_accepted":False}
    def train_slot(self,authority:object,rng:EmpiricalRNG,replicate_role:str,arm:str,*,now:datetime)->dict[str,object]:
        permit=authority.permit;permit.require_active(now=now)
        rng.require_frontier_binding(self.frontier.bindings)
        if permit.phase!="TRAIN" or replicate_role not in __import__("experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_contract",fromlist=["REPLICATE_ROLES"]).REPLICATE_ROLES or arm not in ("MAPR","DIRECT"):raise RuntimeError("training slot authority/address differs")
        mapr,direct=self._initial_parameters(rng,replicate_role,now);model=MAPR4(mapr) if arm=="MAPR" else DirectSetAR(direct);optimizer=make_optimizer(model);slot=f"{replicate_role}.{arm}";initial_checkpoint=self.frontier.root/f"{slot}.initial.checkpoint.pt";initial_optimizer=self.frontier.root/f"{slot}.initial.optimizer.pt";final_checkpoint=self.frontier.root/f"{slot}.final.checkpoint.pt";final_optimizer=self.frontier.root/f"{slot}.final.optimizer.pt";chain=_validate_generation_chain(self.frontier.root,slot);previous=None;start_update=0;initial_pair=_resume_initial_pair(model,optimizer,initial_checkpoint,initial_optimizer)
        if chain is not None:
            last,state_path,previous=chain
            if initial_pair is None:raise RuntimeError("generation exists without initial checkpoint/optimizer pair")
            state=torch.load(state_path,map_location="cpu",weights_only=True)
            if not isinstance(state,Mapping) or set(state)!={"model","optimizer","update"} or int(state["update"])!=last["generation"]:raise RuntimeError("resume state payload differs from generation")
            model.load_state_dict(state["model"]);optimizer.load_state_dict(state["optimizer"]);start_update=int(state["update"]);initial_checkpoint_sha,initial_optimizer_sha=initial_pair
        elif initial_pair is not None:initial_checkpoint_sha,initial_optimizer_sha=initial_pair
        else:initial_checkpoint_sha=self._save(initial_checkpoint,model.state_dict());initial_optimizer_sha=self._save(initial_optimizer,optimizer.state_dict())
        final_present=final_checkpoint.is_file() or final_optimizer.is_file()
        if start_update==256:
            final_pair=_resume_state_pair(model,optimizer,final_checkpoint,final_optimizer,"final")
            if final_pair is None:raise RuntimeError("completed generation lacks final checkpoint/optimizer pair")
            final_checkpoint_sha,final_optimizer_sha=final_pair
            return self._receipt(permit,rng,replicate_role,arm,initial_checkpoint,initial_checkpoint_sha,final_checkpoint,final_checkpoint_sha,initial_optimizer,initial_optimizer_sha,final_optimizer,final_optimizer_sha)
        if start_update<0 or start_update>256 or final_present:raise RuntimeError("incomplete slot has mismatched final checkpoint/optimizer pair")
        for update in range(start_update,256):
            fixtures=tuple(build_world(rng,replicate_role=replicate_role,purpose="training",roster_size=n,failed_zone=z,panel_row=update*16+(n_index*8+(z-1)*4+row),now=now) for n_index,n in enumerate((3,5)) for z in (1,2) for row in range(4));records=[];terminals=[]
            for n in (3,5):
                group=tuple(f for f in fixtures if len(f.agents)==n+1);batch=NativeInteractiveBatch(group)
                try:
                    observations=tuple(x["next_observation"] for x in batch.initial);failed=tuple(x["failed_rank"] for x in batch.initial)
                    group_records=[[] for _ in group]
                    for epoch in range(6):
                        inputs=[_model_inputs(obs,fixture,fr) for obs,fixture,fr in zip(observations,group,failed)];stacked=tuple(torch.cat([row[j] for row in inputs],0) for j in range(6));uniform_values=[]
                        for fixture_index,fixture in enumerate(group):uniform_values.append([((rng.word(address(replicate_role=replicate_role,domain="training/action",purpose=arm,roster_size=n,failed_zone=fixture.failed_zone,update_or_panel_row=update,episode_row=fixture_index,physical_time=20*epoch,draw=t),now=now)+0.5)/float(1<<64)) for t in range(4)])
                        uniforms=torch.tensor(uniform_values,dtype=torch.float64);out=model(*stacked,uniforms);relative=out["command"].detach();commands=[]
                        for i,(fixture,fr) in enumerate(zip(group,failed)):
                            presented=tuple(rank for rank in fixture.post_presentations[epoch] if rank!=fr);rel=tuple(None if int(x)==n else presented[int(x)] for x in relative[i]);commands.append(rel if fixture.failed_zone==1 else (rel[2],rel[3],rel[0],rel[1]));group_records[i].append({"inputs":tuple(x[i:i+1] for x in stacked),"command":relative[i:i+1],"old_logp":out["log_probability"][i].detach(),"old_value":out["value"][i].detach(),"variable":torch.tensor([int(v<0) for v in stacked[4][i]],dtype=torch.float64)})
                        rows=batch.step(commands);observations=tuple(x["next_observation"] for x in rows)
                    terminals.extend(rows);records.extend(item for episode in group_records for item in episode)
                finally:batch.close()
            objectives=torch.tensor([0.5*(row["fail_endpoint"][0]/row["fail_endpoint"][1])+0.5*(row["total_endpoint"][0]/row["total_endpoint"][1]) for row in terminals],dtype=torch.float64);old_values=torch.stack([r["old_value"] for r in records]).reshape(16,6);advantages,returns=gae_terminal(old_values,objectives);advantages=normalize_advantages(advantages).reshape(96);returns=returns.reshape(96);old_logp=torch.stack([r["old_logp"] for r in records]);permutations=[]
            for epoch in range(4):permutations.append(_shuffle(tuple(range(96)),rng,{"replicate_role":replicate_role,"domain":"training/minibatch-permutation","purpose":arm,"roster_size":3,"failed_zone":1,"update_or_panel_row":update,"episode_row":epoch,"physical_time":0},now))
            for permutation in permutations:
                for minibatch in frozen_minibatches(permutation):
                    outputs=[model(*records[i]["inputs"],None,records[i]["command"]) for i in minibatch];logpi=torch.cat([x["log_probability"] for x in outputs]);values=torch.cat([x["value"] for x in outputs]);entropy=torch.cat([x["token_entropies"] for x in outputs]);variable=torch.stack([records[i]["variable"] for i in minibatch]);ix=torch.tensor(minibatch);loss=ppo_loss(logpi,old_logp[ix],advantages[ix],values,returns[ix],entropy,variable);optimizer.zero_grad(set_to_none=True);loss["total"].backward();torch.nn.utils.clip_grad_norm_(model.parameters(),0.5);optimizer.step()
            state_path=self.frontier.root/f"{slot}.state.g{update+1:04d}.pt";state_sha=self._save(state_path,{"model":model.state_dict(),"optimizer":optimizer.state_dict(),"update":update+1});previous=self.frontier.append_generation(slot,update+1,previous_generation_sha256=previous,state_path=state_path.name,state_sha256=state_sha,optimizer_step=(update+1)*16,training_episodes_completed=(update+1)*16,joint_decisions_completed=(update+1)*96)
        final_checkpoint_sha=self._save(final_checkpoint,model.state_dict());final_optimizer_sha=self._save(final_optimizer,optimizer.state_dict());return self._receipt(permit,rng,replicate_role,arm,initial_checkpoint,initial_checkpoint_sha,final_checkpoint,final_checkpoint_sha,initial_optimizer,initial_optimizer_sha,final_optimizer,final_optimizer_sha)
