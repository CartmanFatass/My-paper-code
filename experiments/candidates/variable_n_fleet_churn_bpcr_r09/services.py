"""Deterministic controllers, endpoints, panels, and support-service contracts."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Protocol,Mapping,Sequence
from datetime import datetime

from .association import row_cut,consistent_relabel
from .native_backend import run_native_bcrh_batch,run_native_sensitivity_batch
from .empirical_contract import LEARNED_ARMS,CONCLUSION_ARMS,REPLICATE_ROLES
from .fixtures import EpisodeFixture,GeneralAgentState,all_bcrh_fixtures
from .rng import EmpiricalRNG,address

def endpoints(row:Mapping[str,tuple[int,int]])->dict[str,Fraction]:
    fail=row["fail_endpoint"];total=row["total_endpoint"];intact=row["intact_endpoint"]
    if min(fail[1],total[1],intact[1])<=0:raise ValueError("endpoint denominator is nonpositive")
    return {"R_fail_60":Fraction(*fail),"U_total":Fraction(*total),"U_intact":Fraction(*intact)}

class LearnedController(Protocol):
    def command(self,observation:Mapping[str,object])->tuple[int|None,...]:...

@dataclass(frozen=True)
class BCRHPersistAdapter:
    def command_batch(self,current_states:Sequence[object])->tuple[tuple[int|None,...],...]:return tuple(row["scorer_command"] for row in run_native_bcrh_batch(current_states))
    def sensitivity_batch(self,fixtures:Sequence[object])->tuple[dict[str,object],...]:return run_native_sensitivity_batch(fixtures)

@dataclass(frozen=True)
class CutAdapter:
    def construct(self,score_rows:object,partition_keys:Sequence[tuple[object,...]],derange:object):
        return row_cut(score_rows,partition_keys,derange)  # type: ignore[arg-type]
    def verify_consistent_relabel(self,raw_records:object,presentation:Sequence[int],decoder:object):
        return consistent_relabel(raw_records,presentation,decoder)  # type: ignore[arg-type]

def validation_addresses()->tuple[tuple[str,str,int,int,int,int],...]:
    return tuple((role,arm,checkpoint,n,zone,row) for role in REPLICATE_ROLES for arm in LEARNED_ARMS for checkpoint in (0,256) for n in (3,5) for zone in (1,2) for row in range(32))

def conclusion_addresses()->tuple[tuple[str,str,int,int],...]:
    return tuple((role,arm,zone,row) for role in REPLICATE_ROLES for arm in CONCLUSION_ARMS for zone in (1,2) for row in range(32))

def _draw_below(rng:EmpiricalRNG,limit:int,base:dict[str,object],draw:int,now:datetime)->tuple[int,int]:
    bound=((1<<64)//limit)*limit
    while True:
        word=rng.word(address(**base,draw=draw),now=now);draw+=1
        if word<bound:return word%limit,draw

def _shuffle(values:Sequence[int],rng:EmpiricalRNG,base:dict[str,object],now:datetime)->tuple[int,...]:
    out=list(values);draw=0
    for end in range(len(out)-1,0,-1):index,draw=_draw_below(rng,end+1,base,draw,now);out[end],out[index]=out[index],out[end]
    return tuple(out)

def build_world(rng:EmpiricalRNG,*,replicate_role:str,purpose:str,roster_size:int,failed_zone:int,panel_row:int,now:datetime)->EpisodeFixture:
    if roster_size not in (3,5,7):raise ValueError("world roster differs")
    common={"replicate_role":replicate_role,"purpose":purpose,"roster_size":roster_size,"failed_zone":failed_zone,"update_or_panel_row":panel_row,"episode_row":panel_row,"physical_time":0}
    roster_base={**common,"domain":"training/world" if purpose=="training" else ("validation/world" if purpose=="validation" else "conclusion/world")}
    selected=_shuffle(tuple(range(1,9)),rng,roster_base,now)[:roster_size+1];rank_order=_shuffle(selected,rng,{**roster_base,"purpose":purpose+"/opaque-rank"},now);opaque={rank:i+1 for i,rank in enumerate(rank_order)};types=((1,1,2),(2,0,2),(3,1,1),(4,0,1),(5,1,2),(6,0,2),(7,1,1),(8,0,1));by_rank={rank:(fast,radio) for rank,fast,radio in types};agents=tuple(GeneralAgentState(rank,opaque[rank],*by_rank[rank]) for rank in selected)
    q1=[];q2=[];h1=[];h2=[];states=[]
    for axis in range(4):value,_=_draw_below(rng,2,{**roster_base,"purpose":purpose+f"/initial-{axis}"},0,now);states.append(value)
    for epoch in range(12):
        q1.append(states[0]+1);q2.append(states[1]+1);h1.append(states[2]);h2.append(states[3])
        if epoch<11:
            for axis in range(4):
                obstruction=axis>=2;numerators=((8,2),(3,7)) if not obstruction else ((4,1),(2,3));den=10 if not obstruction else 5;draw,_=_draw_below(rng,den,{**roster_base,"purpose":purpose+f"/transition-{axis}","physical_time":-100+20*epoch},0,now);states[axis]=0 if draw<numerators[states[axis]][0] else 1
    presentation_domain="training/presentation" if purpose=="training" else ("validation/presentation" if purpose=="validation" else "conclusion/presentation");presentations=tuple(_shuffle(selected,rng,{**common,"domain":presentation_domain,"purpose":purpose+"/presentation","physical_time":20*epoch},now) for epoch in range(6));commands=((None,None,None,None),)*6
    fixture=EpisodeFixture(failed_zone,agents,tuple(q1),tuple(q2),tuple(h1),tuple(h2),commands,presentations);fixture.validate();return fixture

def bcrh_certificate()->tuple[dict[str,object],...]:
    from .native_backend import run_native_fixture_batch
    rows=run_native_fixture_batch(all_bcrh_fixtures())
    if len(rows)!=64 or not all(row["scorer_checker_equal"] and row["independent_enumerator_equal"] for row in rows):raise RuntimeError("BCRH 64-fixture certificate failed")
    return rows

class ConcretePanelService:
    """Fixed full-panel coordinator and construction-only dry-run kernel."""
    def __init__(self,frontier:object):self.frontier=frontier
    @staticmethod
    def plan()->dict[str,object]:
        from .bcrh_exception import exception_certificate
        validation=validation_addresses();conclusion=conclusion_addresses()
        if len(validation)!=8192 or len(conclusion)!=4096:raise RuntimeError("panel address cardinality differs")
        return {"schema":"VNFC_BPCR_R09_COMPLETE_PANEL_PLAN_V1","validation":validation,"conclusion":conclusion,"validation_count":8192,"conclusion_count":4096,"bcrh_count":1024,"certificate_count":64,"family_shapes":[(16,12),(16,24),(16,8),(16,28),(16,18)],"inference_coordinates":90,"exception":exception_certificate()}
    @staticmethod
    def reduce_matrices(matrices:Mapping[str,Sequence[Sequence[float]]])->dict[str,object]:
        from .inference import family_intervals
        expected={"efficacy":12,"non_harm":24,"training_gain":8,"competence":28,"mechanism":18}
        if set(matrices)!=set(expected):raise ValueError("five-family matrix inventory differs")
        intervals={name:family_intervals(rows,width) for name,(rows,width) in ((name,(matrices[name],width)) for name,width in expected.items())}
        return {"schema":"VNFC_BPCR_R09_EXACT_FIVE_FAMILY_REDUCTION_V1","intervals":intervals,"coordinate_count":sum(expected.values()),"partition_visits":2949120,"subset_mean_constructions":5898060,"comparison_ceiling":79626150}
    @staticmethod
    def dry_run(fixtures:Sequence[object])->dict[str,object]:
        from .native_backend import NativeInteractiveBatch
        from .inference import complementary_subset_interval
        from .association import row_cut
        materialized=tuple(fixtures)
        if len(materialized) not in (8,32):raise ValueError("panel dry run requires B=8 or B=32")
        batch=NativeInteractiveBatch(materialized)
        try:
            sensitivity=batch.sensitivity()
            for epoch in range(6):
                bcrh=batch.bcrh(include_candidate_records=epoch==0)
                if not all(row["scorer_checker_equal"] and row["independent_enumerator_equal"] and row["candidate_count"]<=1961 for row in bcrh):raise RuntimeError("interactive BCRH dry-run conformance differs")
                rows=batch.step(tuple(row["scorer_command"] for row in bcrh))
            if not all(row["terminal"] for row in rows):raise RuntimeError("panel dry-run terminal differs")
        finally:batch.close()
        cut=row_cut(__import__("numpy").arange(32,dtype=float).reshape(8,4),tuple(("fast",2,15) for _ in range(8)),lambda block:block[1:]+block[:1]);interval=complementary_subset_interval(tuple(float(i) for i in range(16)),12);certificate=bcrh_certificate();plan=ConcretePanelService.plan()
        return {"schema":"VNFC_BPCR_R09_CONSTRUCTION_ONLY_PANEL_DRY_RUN_V1","batch_width":len(materialized),"boundaries":6,"sensitivity_rows":len(sensitivity),"cut_opportunity":cut.opportunity,"interval_q":interval.q,"certificates":len(certificate),"validation_plan":plan["validation_count"],"conclusion_plan":plan["conclusion_count"],"question_relevant_values_retained":False}
    def execute(self,authority:object,rng:EmpiricalRNG,checkpoint_barrier:object,*,now:datetime)->Path:
        """Execute and atomically seal the one complete frozen panel.

        There is deliberately no controller, world, reducer, or publication
        extension point.  The runner supplies only externally validated authority,
        RNG/frontier bindings and the already validated global checkpoint
        barrier path.
        """
        from .evaluation import execute_plan,full_panel_plan
        return execute_plan(
            plan=full_panel_plan(),authority=authority,rng=rng,
            frontier=self.frontier,checkpoint_barrier=checkpoint_barrier,now=now,
        )

def service_contract()->dict[str,object]:
    return {"schema":"VNFC_BPCR_R09_PANEL_SERVICES_V1","controllers":["MAPR","DIRECT","BCRH","CUT"],"validation":{"sizes":[3,5],"failed_zones":[1,2],"worlds_per_cell":32,"checkpoints":[0,256],"rollouts":8192},"conclusion":{"size":7,"worlds_per_replicate":64,"failed_zone_balance":[32,32],"rollouts":4096,"bcrh_rollouts":1024},"endpoints":["R_fail_60","U_total","U_intact"],"diagnostics":["public_state","legal_mask","token_choice","acquisition","clearance","energy_reserve","delivery","direct_ablation","cut_mapping","consistent_relabel","action_sensitivity","bcrh_certificate"],"partial_results":False}
