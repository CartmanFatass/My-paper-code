"""Independent old-row/action memory recursion, no candidate wrapper import."""
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, _row, _tick, _nav, original
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reference import ReferencePolicy
from .contract import DETERMINISTIC, PROGRAMS

def _off(row):
    own, users, observed, peers = original._parse(row)
    n, p = len(users), len(peers)
    if n:
        present = original._power(np.concatenate((own[None, :], peers), axis=0), users)
        residual = np.zeros(n, dtype=np.float64)
        if p < 4:
            residual = np.maximum(present[0] / (10. ** (observed / 10.)) - present[1:].sum(axis=0) - original.NOISE, 0.)
        power = present.copy()
        power[0] = 0.
        denominator = power.sum(axis=0, keepdims=True) - power + residual + original.NOISE
        with np.errstate(divide="ignore"):
            sinr = 10. * np.log10(power / denominator)
        chosen = np.zeros_like(sinr, dtype=bool)
        for station in range(1 + p):
            order = np.argsort(-sinr[station], kind="stable")[:10]
            chosen[station, order] = sinr[station, order] >= original.THRESHOLD
        served = float(chosen.sum())
        quality = float(np.where(chosen, np.clip((sinr - 3.) / 30., 0., 1.), 0.).sum() / max(served, 1.))
        score = .7 * served / 50. + .3 * quality
    else:
        served = score = 0.
    return score, served, (1 + p) * n



class Reference:
    def __init__(self, program, parent, *, world, agent, sampling_root):
        if program not in PROGRAMS or ((program in DETERMINISTIC) != (sampling_root is None)):
            raise ValueError("independent B11 program/address required")
        family = "Hdirect" if program == "Hdirect_ZERO" else "C"
        self.original = ReferencePolicy(family, parent if family == "Hdirect" else None,
            world=world, agent=agent, sampling_root=sampling_root)
        self.program, self.agent, self.remembered = program, agent, None
        self.counters = self.original.counters
        for key in ("policy_requests", "off_setup_links", "off_score_evaluations", "off_logical_ticks",
                    "off_sinr_slots", "memory_created", "memory_consumed", "bypass_requests"):
            self.counters[key] = 0

    def query(self, observed, clock, navigation):
        observed, clock, navigation = _row(observed), _tick(clock), _nav(navigation)
        own, users, measured, peers = original._parse(observed)
        count, eligible = len(users), self.agent == (clock//4)%5
        prior = self.remembered
        details = dict(origin_available=False, origin_tick=-1, origin_agent=-1,
            origin_row=np.zeros(104,dtype=np.float32), origin_count=-1, origin_c_index=-1,
            origin_issued_index=-1, origin_nav=-1, stored_index=-1)
        self.counters["policy_requests"] += 1
        if prior is not None:
            # This state was derived below from a source C answer and observed
            # positive-count strict OFF win, never from a saved candidate flag.
            if clock != prior["origin_tick"]+4 or eligible or navigation != prior["origin_nav"]:
                raise AssertionError("independent memory clock/nav recurrence")
            details.update(prior)
            selected = prior["stored_index"]
            result = dict(action_index=selected, command=COMMANDS[selected].copy(), next_nav=prior["origin_nav"],
                fallback=False, features=np.full(114,np.nan,dtype=np.float32), n_current=count, n_peers=len(peers),
                memo_hit=False, scores=np.full(27,np.nan), served=np.full(27,np.nan), c_index=-1,
                probabilities=np.eye(27,dtype=np.float64)[selected], innovation=-1., entropy=0.)
            score=service=np.nan
            evaluated=off=False
            self.remembered=None
            self.counters["memory_consumed"] += 1
            self.counters["bypass_requests"] += 1
        else:
            result = self.original.query(observed, clock, navigation)
            score=service=np.nan
            evaluated=off=False
            if self.program.endswith("ZERO"):
                off = eligible and count == 0
            elif eligible:
                score, service, links = _off(observed)
                evaluated=True
                anchor=int(result["c_index"])
                if np.all(result["served"] == 0.) and service == 0.:
                    selected, off = anchor, count == 0
                elif service > 0. and score > max(result["scores"]):
                    selected, off = 0, True
                else:
                    selected, off = anchor, False
                for key, amount in (("off_setup_links",links),("off_score_evaluations",1),
                                    ("off_logical_ticks",4),("off_sinr_slots",links)):
                    self.counters[key] += amount
                result.update(action_index=selected, command=COMMANDS[selected].copy(),
                              probabilities=np.eye(27,dtype=np.float64)[selected], entropy=0.)
                if self.program in ("CJ_KEEP", "CJ_RETURN") and off and count > 0:
                    retained = selected if self.program == "CJ_KEEP" else anchor
                    details.update(origin_available=True, origin_tick=clock, origin_agent=self.agent,
                        origin_row=observed.copy(), origin_count=count, origin_c_index=anchor,
                        origin_issued_index=selected, origin_nav=int(result["next_nav"]), stored_index=retained)
                    self.remembered=dict(details)
                    self.counters["memory_created"] += 1
        result.update(details, eligible=bool(eligible), requested_off=bool(off), gate_count=min(count,10),
            gate_prediction=0., off_score=score, off_service=service, off_evaluated=evaluated,
            c_available=prior is None, pending_before=prior is not None, pending_after=self.remembered is not None,
            memory_consumed=prior is not None, memory_created=prior is None and self.remembered is not None,
            motion_index=int(result["action_index"]))
        return result
