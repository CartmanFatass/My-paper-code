"""Fixed envelope: twelve pure cases, eight actual manager rounds, no native/C/RNG.

Radio reference case: twelve batched fleet evaluations plus twelve independent
scalar fleet evaluations, at most 24 total. The eight round records are reused by
the DM's eight actual-prefix reader checks; never rerun a manager for readback.
"""

from collections import Counter
import json

import numpy as np
import pytest

from envs.pettingzoo.uav_radio import (
    greedy_connection_assignment, service_metrics, user_sinr_from_path_loss,
)
from experiments.candidates.uav_radio_uncertainty.b01 import model, protocol as rf_protocol
from experiments.candidates.uav_radio_information_cost.b01 import contract as c, protocol as p
from experiments.candidates.uav_radio_information_cost.b01.manager import Scheduler
from experiments.candidates.uav_user_waiting.b02.storage import pack_records, unpack_records
from experiments.candidates.uav_radio_information_cost.b01.read_model import verify_decision
from experiments.candidates.uav_radio_information_cost.b01.read_native import _wire


def inputs():
    sites = np.column_stack((np.arange(50) * 19., np.arange(50)[::-1] * 17.))
    packet = p.encode_map(sites)
    own = np.array([[.1, .2, .2], [.3, .4, .4], [.5, .6, .6],
                    [.7, .8, .8], [.9, .1, 1.]], np.float32)
    actual = np.zeros((5, 3), np.float32)
    proposals = p.COMMANDS[[0, 3, 6, 9, 12]].copy()
    nav = np.arange(5, dtype=np.uint8)
    codes = np.full((5, 50), 80, np.uint8)
    return packet, own, actual, proposals, nav, codes


class OpaqueCodes:
    def __array__(self, *args, **kwargs):
        raise AssertionError("forbidden loss-code inspection")


PURE_CASES = (
    "quantization", "full_reports", "prior_reports", "information_exclusion",
    "cross_arm_reports", "corrupt_reports", "command_timing", "corrupt_commands",
    "typed_boundaries", "tail_payload", "stationary_moments", "radio_reference",
)


@pytest.mark.parametrize("case", PURE_CASES)
def test_fixed_twelve_typed_codec_boundary_and_moment_cases(case):
    packet, own, actual, proposals, nav, codes = inputs()
    if case == "quantization":
        losses = np.full((5, 50), 80.)
        losses[0, :6] = (39.7, 40.25, 40.75, 167.5, 167.75, 168.)
        quantized, flags = p.encode_losses(losses)
        np.testing.assert_array_equal(quantized[0, :6], (0, 0, 2, 255, 255, 255))
        np.testing.assert_array_equal(flags["clipped_low"][0, :6], (True, False, False, False, False, False))
        np.testing.assert_array_equal(flags["clipped_high"][0, :6], (False, False, False, False, True, True))
    elif case == "full_reports":
        reports = p.encode_reports("P_FULL", own, actual, proposals, 252, nav, codes)
        inherited = rf_protocol.encode_reports(own, actual, proposals, 252, nav, codes)
        assert sum(map(len, reports)) == 375
        assert reports == tuple(bytes((c.VERSION,)) + report[1:] for report in inherited)
        decoded = p.decode_reports("P_FULL", reports, 252)
        np.testing.assert_array_equal(decoded[-1], 40. + .5 * codes)
        np.testing.assert_array_equal(decoded[1], actual)
        np.testing.assert_array_equal(decoded[2], proposals)
        np.testing.assert_array_equal(decoded[3], nav)
    elif case == "prior_reports":
        reports = p.encode_reports("P_PRIOR", own, actual, proposals, 252, nav)
        assert sum(map(len, reports)) == 125
        decoded = p.decode_reports("P_PRIOR", reports, 252)
        assert decoded[-1] is None
        np.testing.assert_array_equal(decoded[0], np.rint(own.astype(np.float64) * (1000., 1000., 100.) + (0., 0., 50.)))
        np.testing.assert_array_equal(decoded[1], actual)
        np.testing.assert_array_equal(decoded[2], proposals)
        np.testing.assert_array_equal(decoded[3], nav)
    elif case == "information_exclusion":
        with pytest.raises(ValueError, match="forbids"):
            p.encode_reports("P_PRIOR", OpaqueCodes(), OpaqueCodes(), OpaqueCodes(),
                             0, OpaqueCodes(), OpaqueCodes())
        # Typed rejection never enters a round: no clock, map, model or array access.
        rejecting = object.__new__(Scheduler)
        rejecting.arm = "P_PRIOR"
        with pytest.raises(ValueError, match="forbids"):
            rejecting.decide(OpaqueCodes(), OpaqueCodes(), OpaqueCodes(), 0, 31,
                             OpaqueCodes(), OpaqueCodes())
        with pytest.raises(ValueError):
            p.encode_reports("P_FULL", own, actual, proposals, 0, nav)
        with pytest.raises(ValueError):
            p.encode_reports("P_FULL", own, actual, proposals, 0, nav, codes.astype(np.int32))
    elif case == "cross_arm_reports":
        for arm, other in (("P_FULL", "P_PRIOR"), ("P_PRIOR", "P_FULL")):
            reports = p.encode_reports(arm, own, actual, proposals, 0, nav,
                                       codes if arm == "P_FULL" else None)
            with pytest.raises(ValueError):
                p.decode_reports(other, reports, 0)
    elif case == "corrupt_reports":
        for arm in c.ARMS:
            reports = p.encode_reports(arm, own, actual, proposals, 0, nav,
                                       codes if arm == "P_FULL" else None)
            for offset, value in ((0, 5), (1, 4), (3, 1), (24, 10)):
                changed = list(reports)
                damaged = bytearray(changed[0])
                damaged[offset] = value
                changed[0] = bytes(damaged)
                with pytest.raises(ValueError):
                    p.decode_reports(arm, changed, 0)
    elif case == "command_timing":
        for arm in c.ARMS:
            command = p.encode_command(arm, 7, 3, 12, 252)
            assert len(command) == 16
            assert p.decode_command(arm, command, 252) == (7, 3, 12)
            assert p.COMMAND.unpack(command)[5] == 252 + c.arm_settings(arm)["delivery"]
            other = c.ARMS[1] if arm == c.ARMS[0] else c.ARMS[0]
            with pytest.raises(ValueError):
                p.decode_command(other, command, 252)
    elif case == "corrupt_commands":
        for arm in c.ARMS:
            command = p.encode_command(arm, 7, 0, 12, 0)
            fields = list(p.COMMAND.unpack(command))
            for index, value in ((0, 5), (1, 0), (2, 3), (3, 1), (4, 1), (5, 4), (6, 27)):
                changed = fields.copy()
                changed[index] = value
                with pytest.raises(ValueError):
                    p.decode_command(arm, p.COMMAND.pack(*changed), 0)
    elif case == "typed_boundaries":
        for mask in (0, 32, True, 1.5):
            with pytest.raises(ValueError):
                p.mask_array(mask)
        for tick in (True, -4, 1, 256, 0.):
            with pytest.raises(ValueError):
                p.report_tick(tick)
        for q in (True, -1, 27, 1.5):
            with pytest.raises(ValueError):
                p.encode_command("P_FULL", 31, 0, q, 0)
        with pytest.raises(ValueError):
            c.arm_settings("P")
        sites = np.tile((2.5, 3.5), (50, 1))
        np.testing.assert_array_equal(p.decode_map(p.encode_map(sites)), np.tile((2., 4.), (50, 1)))
        assert len(packet) == 400
    elif case == "tail_payload":
        for arm, delay, length_sum, delivered, startup in (
            ("P_FULL", 3, 253, 246.7, 2.9), ("P_PRIOR", 2, 254, 254., 2.),
        ):
            settings = c.arm_settings(arm)
            assert settings["delivery"] == delay
            assert sum(min(4, 256 - tick - delay) for tick in range(0, 256, 4)) == length_sum
            assert sum(c.payload_weight(arm, tick) for tick in range(delay, 256)) == pytest.approx(delivered, abs=1e-10)
            assert sum(c.payload_weight(arm, tick) for tick in range(delay)) == pytest.approx(startup, abs=1e-10)
            assert settings["round_bytes"] * 8 / c.BITRATE + settings["pilot_seconds"] + settings["compute_seconds"] == float(delay)
        assert c.arm_settings("P_FULL")["compute_seconds"] == 1.336
        assert c.arm_settings("P_PRIOR")["compute_seconds"] == 1.436
    elif case == "stationary_moments":
        positions = np.array([[0., 0., 50.], [1000., 1000., 150.], [100., 200., 100.],
                              [500., 500., 90.], [30., 30., 70.]])
        commands = np.array([[-1, -1, -1], [1, 1, 1], [1, 0, 0], [0, 0, 0], [-1, -1, -1]])
        moved, rho = model.move(positions, commands)
        np.testing.assert_array_equal(moved[:2], positions[:2])
        assert rho[0] == rho[1] == rho[3] == 1.
        assert rho[2] == np.exp(-30. / c.CORRELATION_METRES)
        mean, variance = np.zeros((5, 50)), np.full((5, 50), c.PRIOR_VARIANCE)
        mu, var = model.moments_step(mean, variance, rho)
        np.testing.assert_array_equal(mu, mean)
        np.testing.assert_allclose(var, variance, rtol=0, atol=1e-14)
        nominal = np.full((5, 50), 80.)
        effective = model.expected_loss(nominal, mean, variance)
        a = np.log(10.) / 10.
        correction = .5 * a * c.PRIOR_VARIANCE
        np.testing.assert_allclose(effective, nominal - correction, rtol=0, atol=2e-14)
        assert correction == pytest.approx(1.973269373, abs=1e-9)
        np.testing.assert_allclose(10. ** ((23. - effective) / 10.),
                                   10. ** ((23. - nominal) / 10.) * np.exp(.5 * a * a * variance),
                                   rtol=1e-14, atol=0)
    else:
        assert case == "radio_reference"
        losses = np.full((3, 5, 50), 100., np.float64)
        losses[0, 0] = 60.
        losses[1] = 80.
        losses[2] = np.arange(250, dtype=np.float64).reshape(5, 50) / 8. + 65.
        for mask in (1, 3, 7, 31):
            native, sinr, grants = model.native_batch(losses, mask)
            for index, loss in enumerate(losses):
                reference = user_sinr_from_path_loss(loss, transmitter_mask=p.mask_array(mask))
                assigned = greedy_connection_assignment(reference)
                values = service_metrics(reference, assigned)
                np.testing.assert_array_equal(sinr[index], reference)
                np.testing.assert_array_equal(grants[index], assigned)
                np.testing.assert_array_equal(native[index], (values["J"], values["served"], values["quality"]))
            np.testing.assert_array_equal(grants[0, 0], np.arange(50) < 10)


class BoundaryClock:
    def __init__(self, kind, arm):
        self.kind, self.arm, self.manager, self.late = kind, arm, None, False

    def __call__(self):
        record = self.manager.last_record if self.manager is not None else None
        if record is not None:
            if self.kind == "reports_encode" and record["report_packets"].size:
                self.late = True
            if self.kind == "prefix" and len(record["prefix_hashes"]) == 1:
                self.late = True
            if self.kind == "radio" and len(record["computed_pairs"]) == 1:
                self.late = True
        allowance = c.arm_settings(self.arm)["compute_seconds"]
        return allowance + 1. if self.late else allowance

    def cpu(self):
        if self.kind == "finalization":
            self.late = True
        return .005


def test_fixed_eight_rounds_and_same_record_actual_prefix_readback():
    packet, own, actual, proposals, nav, codes = inputs()
    cases = (("P_FULL", 0, "full"), ("P_PRIOR", 0, "full"),
             ("P_FULL", 252, "full"), ("P_PRIOR", 252, "full"),
             ("P_FULL", 0, "reports_encode"), ("P_PRIOR", 0, "prefix"),
             ("P_FULL", 0, "radio"), ("P_PRIOR", 0, "finalization"))
    worker, reader = Counter(), Counter()
    rejected_corrupt_wire = 0
    for arm, tick, boundary in cases:
        clock = BoundaryClock(boundary, arm)
        manager = Scheduler(arm, packet, c.FIXTURE_SEED, clock=clock, cpu_clock=clock.cpu)
        clock.manager = manager
        result = manager.decide(own, actual, proposals, tick, 31, nav,
                                codes if arm == "P_FULL" else None, started=0., cpu_started=0.)
        record, counts = result["record"], result["record"]["counts"]
        assert result["timely"] == (boundary == "full")
        assert record["delivery"] == c.arm_settings(arm)["delivery"]
        assert record["effective_tick"] == tick + record["delivery"]
        assert record["length"] == min(4, 256 - tick - record["delivery"])
        assert record["noise_hash"] == "" and record["noise_address"] == []
        assert record["finalization_started"]
        if arm == "P_PRIOR":
            assert record["decoded_losses"].shape == (0, 50) and record["anchor_hash"] == ""
            assert not counts.get("report_loss_codes_encoded", 0)
            assert not counts.get("report_loss_codes_decoded", 0)
            assert not counts.get("anchor_geometry_snapshots", 0)
            assert not counts.get("prefix_conditional_fleet_updates", 0)
            assert not counts.get("candidate_conditional_fleet_updates", 0)
            if record["prior_initialized"]:
                assert record["prior_hash"] == p.array_digest(np.zeros((5, 50)), np.full((5, 50), c.PRIOR_VARIANCE))
                assert counts["prior_initializations"] == 1
        if boundary == "full":
            assert counts["candidate_requests"] == 116
            assert counts["candidate_plans"] in (57, 83, 87, 112)
            assert counts["prefix_kinematic_ticks"] == record["delivery"]
            assert record["attempted_bytes"] == record["sent_bytes"] == record["round_bytes"]
            assert record["wall_seconds"] == record["compute_seconds"]
            mask, member, q = p.decode_command(arm, record["command_packet"].tobytes(), tick)
            expected = proposals.copy()
            expected[member] = p.COMMANDS[q]
            np.testing.assert_array_equal(result["commands"], expected)
            assert result["mask"] == mask and record["selected_pair"] == (q, mask)
        else:
            np.testing.assert_array_equal(result["commands"], actual)
            np.testing.assert_array_equal(record["executed_commands"], actual)
            assert result["mask"] == record["executed_mask"] == 31
            assert not record["command_sent"] and record["selected_pair"] is None
            assert record["cutoff"] == ("candidate_radio" if boundary == "radio" else boundary)
        if boundary == "reports_encode":
            assert record["attempted_bytes"] == 375 and record["sent_bytes"] == 0
            assert not record["decoded"] and not record["report_sent"]
        if boundary == "prefix":
            assert counts["prefix_kinematic_ticks"] == 1
            assert counts["prefix_prior_stationary_reuses"] == 1
            assert record["sent_bytes"] == 125 and not len(record["request_pairs"])
        if boundary == "radio":
            assert len(record["computed_pairs"]) == 1
            assert counts["candidate_fleet_scores"] == record["length"]
            assert counts["candidate_batch_calls"] == 1
        if boundary == "finalization":
            assert record["selected_before_deadline"] is not None
            assert record["finalization_late"] and record["command_packet"].size == 16
            assert record["attempted_bytes"] == 141 and record["sent_bytes"] == 125
        # One actual-prefix replay per paid manager round, after storage roundtrip.
        record = unpack_records(pack_records([record]))[0]
        verify_decision(record, p.decode_map(packet), reader)
        index = tick // 4
        raw = dict(arm=np.array(arm),world=np.array(c.FIXTURE_SEED),horizon=np.array(256),
            proposals=np.zeros((64,5,3),np.float32),post_c_nav=np.zeros((64,5),np.uint8),
            observations=np.zeros((257,5,104),np.float32),round_wall=np.zeros(64),round_cpu=np.zeros(64))
        raw["proposals"][index],raw["post_c_nav"][index] = proposals,nav
        raw["observations"][tick,:,:3] = own
        raw["round_wall"][index],raw["round_cpu"][index] = record["wall_seconds"],record["cpu_seconds"]
        if arm=="P_FULL":
            raw["loss_codes"] = np.zeros((64,5,50),np.uint8)
            raw["loss_codes"][index] = codes
        wire_commands,wire_mask = _wire(record,raw,index,actual,31,reader)
        np.testing.assert_array_equal(wire_commands,result["commands"])
        assert wire_mask == result["mask"]
        if arm=="P_PRIOR" and tick==0 and boundary=="full":
            # Pure packet/evidence rejection: no second candidate/native/C/RNG query.
            corrupt = dict(record,decoded_losses=np.zeros((5,50)))
            with pytest.raises(ValueError,match="decoded_losses"):
                _wire(corrupt,raw,index,actual,31,Counter())
            rejected_corrupt_wire += 1
        worker.update(record["counts"])
    assert worker["candidate_fleet_scores"] <= 3584
    assert reader["reference_decisions"]==8 and rejected_corrupt_wire==1
    assert reader["reference_candidate_fleet_scores"]==worker["candidate_fleet_scores"]
    assert reader["reference_model_normal_values"]==0
    print(json.dumps(dict(synthetic_cases=12, manager_rounds=8,
                         pure_fleet_evaluations=24, worker=dict(worker),reader=dict(reader),
                         corrupt_wire_rejections=rejected_corrupt_wire), sort_keys=True))
