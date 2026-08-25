"""Exhaustive first-true revision-09 association/value branch reducer."""
from __future__ import annotations
from itertools import product
from fractions import Fraction
from typing import Mapping

ASSOCIATION_KEYS=("association_invalid","association_opportunity_gate_failed","association_heterogeneous","association_retain","association_decline")
VALUE_KEYS=("value_invalid","physical_gate_failed","comparator_gate_failed","mapr_gate_failed","retain_mapr","retain_direct","fixed_sufficiency","decline_robust_mapr")

def reduce_branches(flags:Mapping[str,bool])->tuple[str,str]:
    if set(flags)!=(set(ASSOCIATION_KEYS)|set(VALUE_KEYS)):raise ValueError("branch predicate inventory differs")
    association=("ASSOCIATION_INVALID" if flags["association_invalid"] else "ASSOCIATION_NONIDENTIFIED_OPPORTUNITY" if flags["association_opportunity_gate_failed"] else "ASSOCIATION_HETEROGENEOUS" if flags["association_heterogeneous"] else "ASSOCIATION_RETAIN" if flags["association_retain"] else "ASSOCIATION_DECLINE" if flags["association_decline"] else "ASSOCIATION_NONIDENTIFIED_PRECISION")
    value=("INVALID" if association=="ASSOCIATION_INVALID" or flags["value_invalid"] else "NONIDENTIFIED_PHYSICAL" if flags["physical_gate_failed"] else "NONIDENTIFIED_COMPARATOR" if flags["comparator_gate_failed"] else "DECLINE_MAPR_INCOMPETENT" if flags["mapr_gate_failed"] else "RETAIN_MAPR_FACTORIZATION" if flags["retain_mapr"] else "RETAIN_BROAD_DIRECT_SET" if flags["retain_direct"] else "FIXED_SUFFICIENCY" if flags["fixed_sufficiency"] else "DECLINE_ROBUST_MAPR" if flags["decline_robust_mapr"] else "NONIDENTIFIED_PRECISION")
    return association,value

def exhaustive_branch_table()->dict[int,tuple[str,str]]:
    keys=ASSOCIATION_KEYS+VALUE_KEYS;return {code:reduce_branches(dict(zip(keys,bits))) for code,bits in enumerate(product((False,True),repeat=len(keys)))}

def derive_branch_flags(intervals:Mapping[str,tuple[Fraction,Fraction]],integrity:Mapping[str,bool])->dict[str,bool]:
    if set(integrity)!={"overall_valid","association_valid"}:raise ValueError("integrity gate inventory differs")
    pops=("aggregate","zone1","zone2")
    def iv(name:str)->tuple[Fraction,Fraction]:
        if name not in intervals:raise ValueError(f"missing named interval: {name}")
        lo,hi=intervals[name]
        if lo>hi:raise ValueError("interval endpoints reversed")
        return lo,hi
    def lower(name:str,threshold:Fraction)->bool:return iv(name)[0]>threshold
    def better(a:str,b:str,pop:str)->bool:return lower(f"fail/{a}-{b}/{pop}",Fraction(1,10))
    def equivalent(a:str,b:str,pop:str)->bool:
        lo,hi=iv(f"fail/{a}-{b}/{pop}");return lo>Fraction(-1,10) and hi<Fraction(1,10)
    def inferior(a:str,b:str,pop:str)->bool:return iv(f"fail/{a}-{b}/{pop}")[1]<Fraction(-1,10)
    def nonharm(a:str,b:str,pop:str)->bool:return lower(f"total/{a}-{b}/{pop}",Fraction(-1,40)) and lower(f"intact/{a}-{b}/{pop}",Fraction(-1,20))
    def harm(a:str,b:str,pop:str)->bool:return iv(f"total/{a}-{b}/{pop}")[1]<Fraction(-1,40) or iv(f"intact/{a}-{b}/{pop}")[1]<Fraction(-1,20)
    def reverse_nonharm(a:str,b:str,pop:str)->bool:return iv(f"total/{a}-{b}/{pop}")[1]<Fraction(1,40) and iv(f"intact/{a}-{b}/{pop}")[1]<Fraction(1,20)
    def all_better(a:str,b:str)->bool:return all(better(a,b,p) and nonharm(a,b,p) for p in pops)
    def heterogeneous(a:str,b:str)->bool:return (better(a,b,"zone1") and inferior(a,b,"zone2")) or (inferior(a,b,"zone1") and better(a,b,"zone2")) or (better(a,b,"aggregate") and any(harm(a,b,p) for p in pops))
    physical=all(lower(f"gate/action_sensitivity/{z}",Fraction(1,4)) for z in ("zone1","zone2"))
    direct_gain=all(lower(f"gate/training_gain/DIRECT/N{n}/zone{z}",Fraction(1,10)) for n in (3,5) for z in (1,2));mapr_gain=all(lower(f"gate/training_gain/MAPR/N{n}/zone{z}",Fraction(1,10)) for n in (3,5) for z in (1,2))
    direct_comp=all(lower(f"gate/competence/DIRECT/{cell}/{endpoint}",Fraction(1,30) if endpoint=="fail" else Fraction(7,10)) for cell in ("N3z1","N3z2","N5z1","N5z2","heldz1","heldz2") for endpoint in ("fail","total"));mapr_comp=all(lower(f"gate/competence/MAPR/{cell}/{endpoint}",Fraction(1,30) if endpoint=="fail" else Fraction(7,10)) for cell in ("N3z1","N3z2","N5z1","N5z2","heldz1","heldz2") for endpoint in ("fail","total"));bcrh_comp=all(lower(f"gate/competence/BCRH/heldz{z}/{endpoint}",Fraction(1,30) if endpoint=="fail" else Fraction(7,10)) for z in (1,2) for endpoint in ("fail","total"));direct_active=all(lower(f"gate/direct_{kind}/{cell}",Fraction(1,10)) for kind in ("residual_active","command_change") for cell in ("N3z1","N3z2","N5z1","N5z2","heldz1","heldz2"))
    assoc_opportunity=all(lower(f"gate/association_opportunity/zone{z}",Fraction(1,4)) and lower(f"gate/association_change/zone{z}",Fraction(1,10)) for z in (1,2))
    assoc_decline=any(equivalent("MAPR","CUT",p) or inferior("MAPR","CUT",p) for p in pops)
    mapr_nonpositive=any(equivalent("MAPR",b,p) or inferior("MAPR",b,p) or harm("MAPR",b,p) for b in ("DIRECT","BCRH") for p in pops) or any(heterogeneous("MAPR",b) for b in ("DIRECT","BCRH"))
    flags={"association_invalid":not integrity["association_valid"],"association_opportunity_gate_failed":not assoc_opportunity,"association_heterogeneous":heterogeneous("MAPR","CUT") or any(harm("MAPR","CUT",p) for p in pops),"association_retain":all_better("MAPR","CUT"),"association_decline":assoc_decline,"value_invalid":not integrity["overall_valid"],"physical_gate_failed":not physical,"comparator_gate_failed":not(direct_gain and direct_comp and bcrh_comp and direct_active),"mapr_gate_failed":not(mapr_gain and mapr_comp),"retain_mapr":all_better("MAPR","DIRECT") and all_better("MAPR","BCRH"),"retain_direct":all_better("DIRECT","BCRH") and all(equivalent("MAPR","DIRECT",p) or inferior("MAPR","DIRECT",p) for p in pops),"fixed_sufficiency":all(all((equivalent(a,"BCRH",p) or inferior(a,"BCRH",p)) and reverse_nonharm(a,"BCRH",p) for p in pops) for a in ("MAPR","DIRECT")),"decline_robust_mapr":mapr_nonpositive}
    return flags

def reduce_from_intervals(intervals:Mapping[str,tuple[Fraction,Fraction]],integrity:Mapping[str,bool])->tuple[str,str]:return reduce_branches(derive_branch_flags(intervals,integrity))
