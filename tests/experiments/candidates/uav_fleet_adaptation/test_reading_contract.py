"""Scientific identity/counter failures cannot be certified from a full-looking panel."""
import copy
from dataclasses import asdict
import json

import pytest

from experiments.candidates.uav_fleet_adaptation.evaluation import ARMS, EvalSpec
from experiments.candidates.uav_fleet_adaptation.host import EVAL_WORLD_IDS, TRAIN_WORLD_IDS
from experiments.candidates.uav_fleet_adaptation.study import (
    DIRECTION, OBJECT_ID, PARENT_SHA256, EXPECTED_OPTIMIZERS, validate_worker,
)
from experiments.candidates.uav_fleet_adaptation.training import TrainSpec
from experiments.candidates.uav_fleet_adaptation.reader import verify_sampler


def valid_worker():
    expected = {"new_fits":2,"training_episodes":1024,"training_team_steps":512000,
        "outer_updates":64,"evaluation_episodes":128,"evaluation_team_steps":64000,
        "total_native_steps":576000,"mask_requests":8160000,"motion_requests":3456000}
    digests = {"I":"a"*64,"A":"b"*64,"F":"c"*64}
    row = {"schema":1,"direction":DIRECTION,"object_id":OBJECT_ID,"launch_sha":"d"*40,
        "status":"collected","worker_status":"complete","counts":expected,
        "config":{"direction":DIRECTION,"object_id":OBJECT_ID,"launch_sha":"d"*40,
            "arms":ARMS,"training_world_ids":TRAIN_WORLD_IDS,"evaluation_world_ids":EVAL_WORLD_IDS,
            "train_spec":asdict(TrainSpec()),"eval_spec":asdict(EvalSpec()),"expected":expected},
        "parent":{"checkpoint_sha256_before":PARENT_SHA256,"checkpoint_sha256_after":PARENT_SHA256,
                  "final_parameter_normalizer_digest":digests["I"]},
        "fits":{arm:{"status":"complete","initial_digest":digests["I"],"final_digest":digests[arm],
                     "optimizer_calls":EXPECTED_OPTIMIZERS,"outer_updates":32,
                     "training_team_steps":256000,"training_episodes":512} for arm in ("A","F")},
        "frozen_checks":{arm:{"initial_digest":digests[arm],"final_digest":digests[arm],
            "normalizers_unchanged":True,"optimizer_calls":{key:0 for key in EXPECTED_OPTIMIZERS}}
            for arm in digests}}
    return json.loads(json.dumps(row))


def test_only_reader_failure_can_be_repaired_over_completed_unchanged_worker():
    row = valid_worker()
    validate_worker(row)
    row.update(status="failed",failure_stage="reader")
    validate_worker(row)
    row["failure_stage"] = "final_worker_checks"
    with pytest.raises(ValueError,match="worker incomplete"):
        validate_worker(row)


@pytest.mark.parametrize("corruption",("parent","update","norm","optimizer","source","movement"))
def test_refuse_complete_looking_but_invalid_worker(corruption):
    row = valid_worker()
    if corruption == "parent":
        row["parent"]["checkpoint_sha256_after"] = "e"*64
    elif corruption == "update":
        row["fits"]["F"]["optimizer_calls"]["discoverer_actor"] -= 1
    elif corruption == "norm":
        row["frozen_checks"]["I"]["normalizers_unchanged"] = False
    elif corruption == "optimizer":
        row["frozen_checks"]["F"]["optimizer_calls"]["coordinator"] = 1
    elif corruption == "source":
        row["config"]["launch_sha"] = "0"*40
    elif corruption == "movement":
        row["fits"]["A"]["final_digest"] = row["fits"]["A"]["initial_digest"]
    with pytest.raises(ValueError):
        validate_worker(row)


def test_sampler_counts_require_actual_full_agent_axis_and_discriminator_epochs():
    audit = {"optimizer_calls":{key:value//32 for key,value in EXPECTED_OPTIMIZERS.items()},
        "configured_epochs":15,"num_actual_time_steps":500,"dropped_time_tail_steps":0,
        "discoverer":{"batches":[[10,32]]*3000,"sample_presentations":960000,"valid_presentations":960000},
        "coordinator":{"batch_sizes":[800]*15,"sample_presentations":12000},
        "discriminator":{"team":{"records":8000,"batch_sizes":[8000]*15,"sample_presentations":120000},
            "individual":{"records":64000,"batch_sizes":[16000]*60,"sample_presentations":960000}}}
    verify_sampler(audit)
    fewer = copy.deepcopy(audit)
    fewer["discoverer"]["batches"] = [[10,32]]*375
    with pytest.raises(ValueError,match="recurrent sampler"):
        verify_sampler(fewer)
    fewer = copy.deepcopy(audit)
    fewer["discriminator"]["individual"]["sample_presentations"] -= 16000
    with pytest.raises(ValueError,match="individual discriminator"):
        verify_sampler(fewer)
