"""Frozen B10 trajectory recorder plus H_T's final tie audit."""
import numpy as np
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.capture import (
    Recorder as B10Recorder, CaptureEnv, TimedController, memory_record,
    plan_record as b10_plan_record,
)


def tie_record(controller):
    detail=controller.last_decision
    masks={}
    for name in ("top_score_mask","min_travel_mask"):
        value=np.asarray(detail[name],dtype=bool)
        if value.ndim!=1 or len(value)>16:
            raise AssertionError("invalid bounded H_T tie audit")
        masks["plan_"+name]=np.pad(value,(0,16-len(value)),constant_values=False)
    return dict(plan_h_selected=np.int16(detail["h_selected"]),
                plan_tie_changed=np.bool_(detail["tie_changed"]),**masks)


def plan_record(controller,step):
    return b10_plan_record(controller,step)|tie_record(controller)


class Recorder(B10Recorder):
    def __init__(self,limit,arm):
        if arm!="H_T":
            raise ValueError("B11 records only its new H_T trajectory")
        super().__init__(limit,"H_A")  # Exact current-only tracker recording semantics.

    def on_step(self,**kwargs):
        index=self.plan_count
        super().on_step(**kwargs)
        if kwargs["t"]%30==0:
            for name,value in tie_record(kwargs["controller"]).items():
                self._store(self.plans,name,index,(self.limit+29)//30,value)
