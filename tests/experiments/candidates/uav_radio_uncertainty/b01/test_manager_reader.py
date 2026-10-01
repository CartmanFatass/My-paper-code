"""Eight synthetic rounds and eight actual-prefix reader attempts; no C/env calls."""

from collections import Counter
from copy import deepcopy
import json

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b02.storage import pack_records,unpack_records
from experiments.candidates.uav_radio_uncertainty.b01 import contract as c,protocol as p
from experiments.candidates.uav_radio_uncertainty.b01.manager import Scheduler
from experiments.candidates.uav_radio_uncertainty.b01.read_model import verify_decision


class BoundaryClock:
    def __init__(self,kind):
        self.kind,self.manager,self.late=kind,None,False

    def __call__(self):
        record=self.manager.last_record if self.manager is not None else None
        if self.kind=="entry":
            self.late=True
        elif record is not None:
            if self.kind=="noise" and record["noise_hash"]:
                self.late=True
            if self.kind=="geometry" and len(record["geometry_units"])==2:
                self.late=True
            if self.kind=="radio" and len(record["computed_pairs"])==1:
                self.late=True
        return 2. if self.late else .01

    def cpu(self):
        if self.kind=="finalization":
            self.late=True
        return .005


def test_fixed_eight_rounds_full_terminal_partial_deadlines_and_reader_rejection():
    original_namespace=c.MODEL_NAMESPACE
    # Use pytest's scoped monkeypatch explicitly so production namespace is restored
    # even if a recorded reader discrepancy fails this finite check.
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(c,"MODEL_NAMESPACE",0x54534D43)
        sites=np.column_stack((np.arange(50)*19.,np.arange(50)[::-1]*17.))
        packet=p.encode_map(sites)
        own=np.array([[.1,.2,.2],[.3,.4,.4],[.5,.6,.6],[.7,.8,.8],[.9,.1,1.]],np.float32)
        actual=np.zeros((5,3),np.float32)
        proposals=p.COMMANDS[[0,3,6,9,12]]
        codes=np.full((5,50),80,np.uint8)
        cases=(("P",0,"full"),("U32",0,"full"),("U32",252,"full"),("P",0,"entry"),
               ("U32",0,"noise"),("P",0,"geometry"),("U32",0,"radio"),("U32",0,"finalization"))
        worker,reader=Counter(),Counter()
        for index,(arm,tick,boundary) in enumerate(cases):
            clock=BoundaryClock(boundary)
            manager=Scheduler(arm,packet,c.FIXTURE_SEED,clock=clock,cpu_clock=clock.cpu)
            clock.manager=manager
            result=manager.decide(own,actual,proposals,tick,31,np.arange(5,dtype=np.uint8),codes,started=0.,cpu_started=0.)
            record=result["record"]
            assert result["timely"]==(boundary=="full")
            if not result["timely"]:
                np.testing.assert_array_equal(result["commands"],actual)
                assert result["mask"]==31 and not record["command_sent"]
            if boundary=="full":
                assert record["counts"]["candidate_requests"]==116
                assert record["counts"]["candidate_plans"] in (57,83,87,112)
            if boundary=="finalization":
                assert record["selected_before_deadline"] is not None and record["command_packet"].size==16
                assert record["attempted_bytes"]==391 and record["sent_bytes"]==375
            if tick==252:
                assert record["length"]==1 and record["counts"]["model_normal_values"]==28000
            # This is the production pickle-free round trip, before every reader.
            record=unpack_records(pack_records([record]))[0]
            worker.update(record["counts"])
            if boundary=="noise":
                altered=deepcopy(record)
                altered["noise_hash"]="0"*64
                with pytest.raises(AssertionError):
                    verify_decision(altered,p.decode_map(packet),reader)
                # One reader attempt ends at the altered completed noise digest.
            else:
                verify_decision(record,p.decode_map(packet),reader)
        assert worker["model_normal_values"]==140000
        # The failed digest attempt still generated its paid block; read_model's
        # counters must record attempted/completed draws before digest rejection.
        assert reader["reference_model_normal_values"]==140000
        assert worker["candidate_fleet_scores"]+reader["reference_candidate_fleet_scores"]<=229376
        assert worker["model_normal_values"]+reader["reference_model_normal_values"]<=448000
        print(json.dumps(dict(synthetic_rounds=8,reader_attempts=8,worker=dict(worker),reader=dict(reader)),sort_keys=True))
    assert c.MODEL_NAMESPACE==original_namespace
