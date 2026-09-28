"""The scientific reading requires exact jobs and actual exogenous pairs."""

from copy import deepcopy

from experiments.candidates.uav_radio_placement.b01.readout import ARMS, summarize


def _rows():
    return [{"job_key": f"{arm}/{seed}", "arm": arm, "seed": seed, "status": "completed",
             "qos_per_step": .1 * index, "raw_native_J": 10.0 * index,
             "episode_minimum_battery_ratio": .1,
             "initial_state_sha256": f"init{seed}", "user_xy_trace_sha256": f"users{seed}",
             "rng_state_stream_sha256": f"rng{seed}"}
            for index, arm in enumerate(ARMS) for seed in (1, 2)]


def test_complete_three_program_contrasts_keep_every_signed_world():
    rows = _rows()
    result = summarize(rows, (1, 2), [row["job_key"] for row in rows])
    assert result["status"] == "complete"
    assert set(result["contrasts"]) == {"R_minus_G", "R_minus_H", "G_minus_H"}
    assert result["contrasts"]["R_minus_H"]["metrics"]["raw_native_J"]["mean"] == 20.0
    assert len(result["contrasts"]["R_minus_G"]["worlds"]) == 2


def test_duplicate_missing_or_mismatched_world_is_not_complete_or_paired():
    rows = _rows()
    keys = [row["job_key"] for row in rows]
    duplicate = summarize(rows + [deepcopy(rows[-1])], (1, 2), keys)
    assert duplicate["status"] == "incomplete" and duplicate["duplicate_jobs"]
    assert not duplicate["contrasts"]
    assert summarize(rows[:-1], (1, 2), keys)["status"] == "incomplete"
    rows[-1]["rng_state_stream_sha256"] = "different-stream"
    result = summarize(rows, (1, 2), keys)
    assert result["status"] == "incomplete"
    assert not result["exogenous_pairing_valid"] and not result["contrasts"]
