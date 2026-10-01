"""Episode-local one-use own-command memory, consumed before C or navigation."""
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, _row, _tick, _nav, original
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.policies import Policy as OriginalPolicy
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.policies import off_score, select_cj, ZERO_INDEX
from .contract import DETERMINISTIC, MEMORY, PROGRAMS

EXTRA = ("policy_requests", "off_setup_links", "off_score_evaluations", "off_logical_ticks", "off_sinr_slots",
         "memory_created", "memory_consumed", "bypass_requests")


def raw_count(row):
    return int(np.count_nonzero(row[3:63].reshape(20,3)[:,2] > 0))


class Policy:
    def __init__(self, program, parent, *, world, agent, sampling_root):
        if program not in PROGRAMS or ((program in DETERMINISTIC) != (sampling_root is None)):
            raise ValueError("fixed B11 program/private address required")
        family = "Hdirect" if program == "Hdirect_ZERO" else "C"
        self.base = OriginalPolicy(family, parent if family == "Hdirect" else None,
                                   world=world, agent=agent, sampling_root=sampling_root)
        self.program, self.agent, self.pending = program, agent, None
        self.counters = self.base.counters
        for key in EXTRA:
            self.counters[key] = 0

    def query(self, row, tick, nav):
        row, tick, nav = _row(row), _tick(tick), _nav(nav)
        eligible, n = self.agent == (tick//4)%5, raw_count(row)
        before = self.pending is not None
        origin = dict(origin_available=False, origin_tick=-1, origin_agent=-1,
                      origin_row=np.zeros(104,dtype=np.float32), origin_count=-1,
                      origin_c_index=-1, origin_issued_index=-1, origin_nav=-1, stored_index=-1)
        self.counters["policy_requests"] += 1
        if before:
            saved = self.pending
            if tick != saved["origin_tick"]+4 or eligible or nav != saved["origin_nav"]:
                raise AssertionError("memory requires next noneligible boundary and stored post-origin nav")
            self.pending = None
            origin.update(saved)
            choice = saved["stored_index"]
            probabilities = np.eye(27,dtype=np.float64)[choice]
            _, _, _, peers = original._parse(row)
            answer = dict(action_index=choice, command=COMMANDS[choice].copy(), next_nav=nav,
                fallback=False, features=np.full(114,np.nan,dtype=np.float32),
                n_current=n, n_peers=len(peers), memo_hit=False, scores=np.full(27,np.nan),
                served=np.full(27,np.nan), c_index=-1, probabilities=probabilities,
                innovation=-1., entropy=0.)
            requested_off, off_evaluated, score, service = False, False, np.nan, np.nan
            self.counters["memory_consumed"] += 1
            self.counters["bypass_requests"] += 1
        else:
            answer = self.base.query(row, tick, nav)
            off_evaluated, score, service = False, np.nan, np.nan
            requested_off = eligible and n == 0 if self.program in ("C_ZERO", "Hdirect_ZERO") else False
            if self.program.startswith("CJ") and eligible:
                score, service, links = off_score(row)
                choice, requested_off = select_cj(answer, score, service)
                off_evaluated = True
                for key, value in (("off_setup_links",links),("off_score_evaluations",1),
                                   ("off_logical_ticks",4),("off_sinr_slots",links)):
                    self.counters[key] += value
                answer.update(action_index=choice, command=COMMANDS[choice].copy(),
                              probabilities=np.eye(27,dtype=np.float64)[choice], entropy=0.)
            if self.program in MEMORY and eligible and requested_off and n > 0:
                stored = int(answer["action_index"] if self.program == "CJ_KEEP" else answer["c_index"])
                origin.update(origin_available=True, origin_tick=tick, origin_agent=self.agent,
                    origin_row=row.copy(), origin_count=n, origin_c_index=int(answer["c_index"]),
                    origin_issued_index=int(answer["action_index"]), origin_nav=int(answer["next_nav"]),
                    stored_index=stored)
                self.pending = dict(origin)
                self.counters["memory_created"] += 1
        answer.update(origin, eligible=bool(eligible), requested_off=bool(requested_off),
            gate_count=min(n,10), gate_prediction=0., off_score=score, off_service=service,
            off_evaluated=off_evaluated, c_available=not before, pending_before=before,
            pending_after=self.pending is not None, memory_consumed=before,
            memory_created=(not before and self.pending is not None), motion_index=int(answer["action_index"]))
        if requested_off and not eligible:
            raise AssertionError("ineligible OFF")
        return answer
