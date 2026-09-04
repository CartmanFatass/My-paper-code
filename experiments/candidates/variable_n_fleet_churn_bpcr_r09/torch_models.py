"""Concrete explicit-parameter CPU PyTorch MAPR-4 and DIRECT-SET-AR modules."""
from __future__ import annotations

from collections.abc import Mapping
import math
import torch
from torch import nn

from .models import direct_parameter_shapes,mapr_parameter_shapes
from .models import exact_binary64_mean
from .numeric import canonical_stiefel
from .empirical_contract import DOMAIN_LABELS

class ModelContractError(RuntimeError):pass

class _ExactRosterMean(torch.autograd.Function):
    @staticmethod
    def forward(ctx:object,rows:torch.Tensor)->torch.Tensor:
        ctx.n=rows.shape[1]  # type: ignore[attr-defined]
        values=[torch.from_numpy(exact_binary64_mean(batch.detach().numpy())) for batch in rows]
        return torch.stack(values)
    @staticmethod
    def backward(ctx:object,gradient:torch.Tensor)->tuple[torch.Tensor]:
        return (gradient[:,None,:].expand(-1,ctx.n,-1)/ctx.n,)  # type: ignore[attr-defined]

def initial_learned_availability(fixed_occupants:torch.Tensor,n:int)->torch.Tensor:
    if fixed_occupants.ndim!=2 or fixed_occupants.shape[1]!=4:raise ModelContractError("fixed occupant tensor shape differs")
    available=torch.ones((fixed_occupants.shape[0],n),dtype=torch.bool)
    for row in range(fixed_occupants.shape[0]):
        fixed=fixed_occupants[row][fixed_occupants[row]>=0]
        if len(torch.unique(fixed))!=len(fixed) or bool((fixed>=n).any()):raise ModelContractError("fixed occupants are not unique active rows")
        available[row,fixed]=False
    return available

def variable_prefix_mask(fixed_occupants:torch.Tensor,token:int,choice:torch.Tensor,n:int)->torch.Tensor:return (choice<n)&(fixed_occupants[:,token]<0)

def model_structure_contract()->dict[str,object]:
    return {"schema":"VNFC_BPCR_R09_TORCH_MODEL_STRUCTURE_V1","dtype":"torch.float64","device":"cpu","mapr_shapes":mapr_parameter_shapes(),"direct_shapes":direct_parameter_shapes(),"shared_base":"bitwise_copy","direct_residual_hidden":"independent_registered_domain","direct_residual_output":"exact_zero","random_default_initializer":False,"model_factory_requires_external_parameters":True}

def materialize_external_initialization(base_normals:Mapping[str,tuple[str,object]],residual_normals:Mapping[str,tuple[str,object]])->tuple[dict[str,torch.Tensor],dict[str,torch.Tensor]]:
    """Materialize only externally supplied counter-normal matrices; never draw."""
    import numpy as np
    base_shapes=mapr_parameter_shapes();base_matrix={name for name,shape in base_shapes.items() if len(shape)==2 and name!="null.embedding"}
    if set(base_normals)!=base_matrix:raise ModelContractError("external MAPR normal-input inventory differs")
    base:dict[str,torch.Tensor]={}
    for name,shape in base_shapes.items():
        if name=="null.embedding" or len(shape)==1:array=np.zeros(shape,dtype=np.float64)
        else:
            domain,source=base_normals[name]
            if domain!="model-initialization/base":raise ModelContractError("MAPR matrix uses wrong HMAC domain")
            gain=1.0 if name=="token.embedding" else (0.01 if name.endswith("out.weight") else math.sqrt(2.0));array=canonical_stiefel(np.asarray(source,dtype=np.float64),shape)*gain
        base[name]=torch.from_numpy(array.copy())
    residual_shapes={name:shape for name,shape in direct_parameter_shapes().items() if name.startswith("residual.")};required={"residual.0.weight","residual.1.weight"}
    if set(residual_normals)!=required:raise ModelContractError("external DIRECT residual normal-input inventory differs")
    residual:dict[str,torch.Tensor]={}
    for name,shape in residual_shapes.items():
        if name in required:
            domain,source=residual_normals[name]
            if domain!="model-initialization/direct-residual":raise ModelContractError("DIRECT residual uses wrong HMAC domain")
            array=canonical_stiefel(np.asarray(source,dtype=np.float64),shape)*math.sqrt(2.0)
        else:array=np.zeros(shape,dtype=np.float64)
        residual[name]=torch.from_numpy(array.copy())
    return shared_initial_parameter_sets(base,residual)

def _key(name:str)->str:return name.replace(".","__")

class _ExplicitModule(nn.Module):
    SHAPES:dict[str,tuple[int,...]]={}
    def __init__(self,parameters:Mapping[str,torch.Tensor]):
        super().__init__()
        if set(parameters)!=set(self.SHAPES):raise ModelContractError("explicit parameter inventory differs")
        values={}
        for name,shape in self.SHAPES.items():
            value=parameters[name]
            if value.device.type!="cpu" or value.dtype!=torch.float64 or tuple(value.shape)!=shape or not bool(torch.isfinite(value).all()):raise ModelContractError(f"invalid CPU binary64 tensor: {name}")
            values[_key(name)]=nn.Parameter(value.detach().clone())
        self.parameters_by_name=nn.ParameterDict(values)
    def p(self,name:str)->torch.Tensor:return self.parameters_by_name[_key(name)]
    def linear(self,x:torch.Tensor,prefix:str,activate:bool=True)->torch.Tensor:
        y=torch.nn.functional.linear(x,self.p(prefix+".weight"),self.p(prefix+".bias"));return torch.nn.functional.silu(y) if activate else y
    def encoder(self,x:torch.Tensor,prefix:str)->torch.Tensor:return self.linear(self.linear(x,prefix+".0"),prefix+".1")

class MAPR4(_ExplicitModule):
    SHAPES=mapr_parameter_shapes()
    def encode(self,agents:torch.Tensor,zones:torch.Tensor,globals_:torch.Tensor)->tuple[torch.Tensor,torch.Tensor]:
        if agents.ndim!=3 or agents.shape[2]!=38 or zones.shape!=(agents.shape[0],2,15) or globals_.shape!=(agents.shape[0],4):raise ModelContractError("public tensor shape differs")
        encoded=self.encoder(agents,"agent");summary=torch.cat((_ExactRosterMean.apply(encoded),encoded.max(1).values,self.encoder(zones[:,0],"zone"),self.encoder(zones[:,1],"zone"),self.encoder(globals_,"global")),1);return encoded,summary
    def score(self,encoded:torch.Tensor,summary:torch.Tensor,candidate:int|None,token:int)->tuple[torch.Tensor,torch.Tensor]:
        feature=self.p("null.embedding").expand(encoded.shape[0],-1) if candidate is None else encoded[:,candidate];te=self.p("token.embedding")[token].expand(encoded.shape[0],-1);x=torch.cat((feature,summary,te),1);hidden=self.linear(self.linear(x,"score.0"),"score.1");return self.linear(hidden,"score.out",False).squeeze(1),hidden
    def candidate_logits(self,encoded:torch.Tensor,summary:torch.Tensor,token:int)->tuple[torch.Tensor,torch.Tensor]:
        pairs=[self.score(encoded,summary,i,token) for i in range(encoded.shape[1])]+[self.score(encoded,summary,None,token)];return torch.stack([x[0] for x in pairs],1),torch.stack([x[1] for x in pairs],1)
    def score_table(self,agents:torch.Tensor,zones:torch.Tensor,globals_:torch.Tensor)->tuple[torch.Tensor,torch.Tensor]:
        encoded,summary=self.encode(agents,zones,globals_);tables=[self.candidate_logits(encoded,summary,t)[0] for t in range(4)];stacked=torch.stack(tables,2);return stacked[:,:-1,:],stacked[:,-1,:]
    def prefix_adjustment(self,summary:torch.Tensor,hidden:torch.Tensor,prefix_sum:torch.Tensor,prefix_max:torch.Tensor)->torch.Tensor:return torch.zeros(hidden.shape[:2],dtype=torch.float64)
    def forward(self,agents:torch.Tensor,zones:torch.Tensor,globals_:torch.Tensor,legal_masks:torch.Tensor,fixed_occupants:torch.Tensor,opaque_ranks:torch.Tensor,uniforms:torch.Tensor|None=None,forced_commands:torch.Tensor|None=None,_evaluation_support_valid_forcing:bool=False)->dict[str,torch.Tensor]:
        if any(x.device.type!="cpu" for x in (agents,zones,globals_,legal_masks,fixed_occupants,opaque_ranks)):raise ModelContractError("CPU-only module")
        if _evaluation_support_valid_forcing and forced_commands is None:raise ModelContractError("evaluation support-valid forcing requires teacher commands")
        encoded,summary=self.encode(agents,zones,globals_);batch,n,_=encoded.shape;available=initial_learned_availability(fixed_occupants,n)
        commands=[];probability_rows=[];logp=torch.zeros(batch,dtype=torch.float64);entropy=torch.zeros((batch,4),dtype=torch.float64);prefix_sum=torch.zeros((batch,64),dtype=torch.float64);prefix_max=torch.zeros((batch,64),dtype=torch.float64);prefix_has=torch.zeros((batch,1),dtype=torch.bool)
        for token in range(4):
            logits,hidden=self.candidate_logits(encoded,summary,token);logits=logits+self.prefix_adjustment(summary,hidden,prefix_sum,prefix_max);support=torch.cat((available&legal_masks[:,:,token].bool(),torch.ones((batch,1),dtype=torch.bool)),1);fixed=fixed_occupants[:,token];has_fixed=fixed>=0;support[has_fixed]=False;support[has_fixed,fixed[has_fixed]]=True;masked=logits.masked_fill(~support,-torch.inf);probs=torch.softmax(masked,1)
            if forced_commands is not None:choice=forced_commands[:,token]
            elif uniforms is None:
                tie=torch.cat((opaque_ranks,torch.full((batch,1),2**30,dtype=opaque_ranks.dtype)),1);best=masked.max(1,keepdim=True).values;choice=torch.where(masked==best,tie,torch.iinfo(tie.dtype).max).argmin(1)
            else:choice=(probs.cumsum(1)<uniforms[:,token,None]).sum(1).clamp_max(n)
            probability_rows.append(probs);selected_probability=probs.gather(1,choice[:,None]).squeeze(1)
            if _evaluation_support_valid_forcing:
                if not bool(support.gather(1,choice[:,None]).all()):raise ModelContractError("teacher-forced command is outside masked support")
                selected_log_probability=torch.log_softmax(masked,1).gather(1,choice[:,None]).squeeze(1)
            else:
                if bool((selected_probability<=0).any()):raise ModelContractError("teacher-forced command is outside masked support")
                selected_log_probability=torch.log(selected_probability)
            commands.append(choice);logp+=selected_log_probability;positive=probs>0;safe_probs=torch.where(positive,probs,torch.ones_like(probs));entropy[:,token]=-(torch.where(positive,probs*torch.log(safe_probs),torch.zeros_like(probs))).sum(1);chosen_agent=choice<n;available[torch.arange(batch)[chosen_agent],choice[chosen_agent]]=False;chosen_hidden=hidden[torch.arange(batch),choice];nonnull=variable_prefix_mask(fixed_occupants,token,choice,n)[:,None];prefix_sum=prefix_sum+torch.where(nonnull,chosen_hidden,torch.zeros_like(chosen_hidden));next_max=torch.where(prefix_has,torch.maximum(prefix_max,chosen_hidden),chosen_hidden);prefix_max=torch.where(nonnull,next_max,prefix_max);prefix_has=prefix_has|nonnull
        return {"command":torch.stack(commands,1),"log_probability":logp,"token_entropies":entropy,"value":self.critic(summary),"token_probabilities":torch.stack(probability_rows,1)}
    def critic(self,summary:torch.Tensor)->torch.Tensor:
        hidden=self.linear(self.linear(summary,"critic.0"),"critic.1");return self.linear(hidden,"critic.out",False).squeeze(1)

class DirectSetAR(MAPR4):
    SHAPES=direct_parameter_shapes()
    def __init__(self,parameters:Mapping[str,torch.Tensor]):_ExplicitModule.__init__(self,parameters)
    def p(self,name:str)->torch.Tensor:return self.parameters_by_name[_key("base."+name if not name.startswith("residual.") else name)]
    def residual(self,summary:torch.Tensor,hidden:torch.Tensor,prefix_sum:torch.Tensor,prefix_max:torch.Tensor)->torch.Tensor:
        x=torch.cat((summary,hidden,prefix_sum,prefix_max),1);h=self.linear(self.linear(x,"residual.0"),"residual.1");return self.linear(h,"residual.out",False).squeeze(1)
    def prefix_adjustment(self,summary:torch.Tensor,hidden:torch.Tensor,prefix_sum:torch.Tensor,prefix_max:torch.Tensor)->torch.Tensor:
        batch,candidates,_=hidden.shape;state=summary[:,None,:].expand(-1,candidates,-1);psum=prefix_sum[:,None,:].expand(-1,candidates,-1);pmax=prefix_max[:,None,:].expand(-1,candidates,-1);x=torch.cat((state,hidden,psum,pmax),2);h=self.linear(self.linear(x,"residual.0"),"residual.1");return self.linear(h,"residual.out",False).squeeze(2)

def shared_initial_parameter_sets(base:Mapping[str,torch.Tensor],residual_hidden:Mapping[str,torch.Tensor])->tuple[dict[str,torch.Tensor],dict[str,torch.Tensor]]:
    if set(base)!=set(mapr_parameter_shapes()):raise ModelContractError("MAPR base initialization inventory differs")
    direct={"base."+name:value.detach().clone() for name,value in base.items()}
    for name in ("residual.0.weight","residual.0.bias","residual.1.weight","residual.1.bias"):
        if name not in residual_hidden:raise ModelContractError("DIRECT residual hidden initialization absent")
        direct[name]=residual_hidden[name].detach().clone()
    direct["residual.out.weight"]=torch.zeros((1,64),dtype=torch.float64);direct["residual.out.bias"]=torch.zeros(1,dtype=torch.float64)
    if any(not torch.equal(direct["base."+name],value) for name,value in base.items()):raise AssertionError("shared initialization not bitwise equal")
    return {name:value.detach().clone() for name,value in base.items()},direct
