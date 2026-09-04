"""The exact 64 deterministic BCRH fixture schemas from revision 09."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Sequence


@dataclass(frozen=True, order=True)
class BCRHFixture:
    failed_zone: int
    demand_1: int
    demand_2: int
    blocked_1: int
    blocked_2: int
    failed_relay_present: int

    def validate(self) -> None:
        if self.failed_zone not in (1, 2):
            raise ValueError("failed_zone must be 1 or 2")
        if self.demand_1 not in (1, 2) or self.demand_2 not in (1, 2):
            raise ValueError("demands must be 1 or 2")
        if self.blocked_1 not in (0, 1) or self.blocked_2 not in (0, 1):
            raise ValueError("obstruction flags must be binary")
        if self.failed_relay_present not in (0, 1):
            raise ValueError("failed relay presence must be binary")


def all_bcrh_fixtures() -> tuple[BCRHFixture, ...]:
    fixtures = tuple(
        BCRHFixture(zone, q1, q2, h1, h2, relay)
        for zone, (q1, q2), (h1, h2), relay in product(
            (1, 2), product((1, 2), repeat=2), product((0, 1), repeat=2), (0, 1)
        )
    )
    if len(fixtures) != 64 or len(set(fixtures)) != 64:
        raise AssertionError("revision-09 BCRH fixture cross must contain 64 rows")
    for fixture in fixtures:
        fixture.validate()
    return fixtures


@dataclass(frozen=True)
class HostFixture:
    selected_mask: int
    failed_zone: int
    demand_1: tuple[int, ...]
    demand_2: tuple[int, ...]
    blocked_1: tuple[int, ...]
    blocked_2: tuple[int, ...]
    commands: tuple[tuple[int | None, int | None, int | None, int | None], ...]

    def validate(self) -> None:
        if not 0 < self.selected_mask < 256 or self.failed_zone not in (1, 2):
            raise ValueError("host selected mask or failed zone is invalid")
        if any(len(values) != 12 for values in (self.demand_1, self.demand_2, self.blocked_1, self.blocked_2)):
            raise ValueError("host tapes require twelve pre/post epochs")
        if any(value not in (1, 2) for value in (*self.demand_1, *self.demand_2)):
            raise ValueError("host demand tape is invalid")
        if any(value not in (0, 1) for value in (*self.blocked_1, *self.blocked_2)):
            raise ValueError("host obstruction tape is invalid")
        if len(self.commands) != 12 or any(len(command) != 4 for command in self.commands):
            raise ValueError("host command tape requires twelve four-token commands")
        selected = {rank for rank in range(1, 9) if self.selected_mask & (1 << (rank - 1))}
        for command in self.commands:
            ranks = [item for item in command if item is not None]
            if len(ranks) != len(set(ranks)) or not set(ranks).issubset(selected):
                raise ValueError("host command is not an injective selected-roster command")


def deterministic_host_fixture(failed_zone: int = 1) -> HostFixture:
    """Identity-free public-law conformance tape (not an empirical world)."""
    if failed_zone == 1:
        pre = (1, 3, 2, 4); post = (5, 3, 2, 4)
    elif failed_zone == 2:
        pre = (1, 3, 2, 4); post = (1, 3, 6, 4)
    else:
        raise ValueError("failed zone must be 1 or 2")
    fixture = HostFixture(
        selected_mask=255,
        failed_zone=failed_zone,
        demand_1=(2,) * 12,
        demand_2=(2,) * 12,
        blocked_1=(1,) * 12,
        blocked_2=(1,) * 12,
        commands=(pre,) * 6 + (post,) * 6,
    )
    fixture.validate(); return fixture


@dataclass(frozen=True)
class GeneralAgentState:
    rank: int
    opaque_rank: int
    fast: int
    radio: int
    node: int = 0
    edge_from: int = -1
    edge_to: int = -1
    edge_remaining: int = 0
    destination_node: int = 0
    token: int = -1
    token_state: int = 0
    acquisition_elapsed: int = 0
    energy_fifths: int = 800


@dataclass(frozen=True)
class EpisodeFixture:
    failed_zone: int
    agents: tuple[GeneralAgentState, ...]
    demand_1: tuple[int, ...]
    demand_2: tuple[int, ...]
    blocked_1: tuple[int, ...]
    blocked_2: tuple[int, ...]
    post_commands: tuple[tuple[int | None, ...], ...]
    post_presentations: tuple[tuple[int, ...], ...]

    def validate(self) -> None:
        if self.failed_zone not in (1, 2) or not 4 <= len(self.agents) <= 8:
            raise ValueError("general episode roster/failure is invalid")
        ranks={agent.rank for agent in self.agents}
        if len(ranks)!=len(self.agents) or {agent.opaque_rank for agent in self.agents}!={*range(1,len(self.agents)+1)}:
            raise ValueError("agent and opaque ranks must be unique total orders")
        if any(len(x)!=12 for x in (self.demand_1,self.demand_2,self.blocked_1,self.blocked_2)):
            raise ValueError("general episode requires twelve exogenous epochs")
        if len(self.post_commands)!=6 or any(len(x)!=4 for x in self.post_commands):
            raise ValueError("general episode requires six post-event commands")
        if len(self.post_presentations)!=6 or any(len(x) not in (len(self.agents)-1,len(self.agents)) or len(set(x))!=len(x) or not set(x)<=ranks for x in self.post_presentations):
            raise ValueError("each post-event presentation must contain survivors or a full pre-roster permutation")
        for command in self.post_commands:
            used=[x for x in command if x is not None]
            if len(used)!=len(set(used)) or not set(used)<=ranks:
                raise ValueError("post-event command is not injective")


def deterministic_general_episode(failed_zone: int=1) -> EpisodeFixture:
    types=((1,1,2),(2,0,2),(3,1,1),(4,0,1),(5,1,2),(6,0,2),(7,1,1),(8,0,1))
    agents=tuple(GeneralAgentState(rank,rank,fast,radio) for rank,fast,radio in types)
    if failed_zone==1:
        command=(3,2,5,6);continuation=(3,None,None,None);survivors=(2,3,4,5,6,7,8)
        commands=(command,continuation,(None,None,None,None),(None,None,None,None),(None,None,None,None),(None,None,None,None))
    elif failed_zone==2:
        command=(1,2,3,6);continuation=(None,None,3,None);survivors=(1,2,3,4,6,7,8)
        commands=(command,continuation,(None,None,None,None),(None,None,None,None),(None,None,None,None),(None,None,None,None))
    else:raise ValueError("failed zone must be 1 or 2")
    presentations=tuple(tuple(survivors[(i+j)%7] for j in range(7)) for i in range(6))
    fixture=EpisodeFixture(failed_zone,agents,(2,)*12,(2,)*12,(1,)*12,(1,)*12,commands,presentations)
    fixture.validate();return fixture


@dataclass(frozen=True)
class GeneralBCRHFixture:
    epoch: int
    failed_zone: int
    agents: tuple[GeneralAgentState, ...]
    clearance: tuple[int,int,int,int]
    accrued_fail_delivered: int
    accrued_fail_demand: int
    accrued_total_delivered: int
    accrued_total_demand: int
    demand_1: int
    demand_2: int
    blocked_1: int
    blocked_2: int

    def validate(self)->None:
        if not 0<=self.epoch<=5 or self.failed_zone not in (1,2) or not 1<=len(self.agents)<=7:raise ValueError("general BCRH epoch/post-failure roster invalid")
        if any(x<0 for x in (self.accrued_fail_delivered,self.accrued_fail_demand,self.accrued_total_delivered,self.accrued_total_demand)):raise ValueError("accrued endpoints cannot be negative")


def deterministic_general_bcrh(epoch:int=0)->GeneralBCRHFixture:
    agents=(
        GeneralAgentState(2,2,0,2,node=4,destination_node=4,token=2,token_state=2,acquisition_elapsed=6,energy_fifths=600),
        GeneralAgentState(3,3,1,1,node=1,destination_node=1,token=1,token_state=2,acquisition_elapsed=4,energy_fifths=600),
        GeneralAgentState(5,5,1,2),
    )
    elapsed=min(epoch,3)*20
    fixture=GeneralBCRHFixture(epoch,1,agents,(max(0,20-elapsed),0,0,0),0,elapsed*2,elapsed,elapsed*4,2,2,1,1)
    fixture.validate();return fixture


def deterministic_maximum_bcrh()->GeneralBCRHFixture:
    agents=tuple(GeneralAgentState(rank,rank,rank%2,1+(rank%2),energy_fifths=800) for rank in range(1,8))
    fixture=GeneralBCRHFixture(5,1,agents,(0,0,0,0),200,240,400,480,2,2,1,1)
    fixture.validate();return fixture


@dataclass(frozen=True)
class SensitivityFixture:
    current: GeneralBCRHFixture
    demand_1: tuple[int,int,int]
    demand_2: tuple[int,int,int]
    blocked_1: tuple[int,int,int]
    blocked_2: tuple[int,int,int]

    def validate(self)->None:
        self.current.validate()
        if self.current.epoch!=0:raise ValueError("action sensitivity is defined only at t=0")


def deterministic_sensitivity_fixture()->SensitivityFixture:
    fixture=SensitivityFixture(deterministic_general_bcrh(0),(2,1,2),(2,2,1),(1,0,1),(1,1,0))
    fixture.validate();return fixture
