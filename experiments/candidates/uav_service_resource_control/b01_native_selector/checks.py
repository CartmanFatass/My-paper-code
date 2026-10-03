"""Bounded pre-submission checks; native effects and real private models forbidden.

The cumulative receipt includes failed checks. This utility is never a native
health probe and cannot admit or retry any part of the scientific purchase.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("tests", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    cpu_start, wall_start = time.process_time(), time.perf_counter()
    prior_children = resource.getrusage(resource.RUSAGE_CHILDREN)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    import numpy as np
    import pytest
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    from experiments.candidates.uav_fleet_transmission.b10_service_assignment import controller as b10
    from experiments.candidates.uav_fleet_transmission.b11_travel_ties import controller as b11
    from experiments.candidates.uav_fleet_transmission.b12_resource_assignment import energy
    from experiments.candidates.uav_service_resource_control.b01_native_selector import study
    from experiments.candidates.uav_service_resource_control.b01_native_selector.contract import write_json

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    path = out/"checks.json"
    ledger = json.loads(path.read_text()) if path.exists() else dict(
        attempts=[], counts={}, latest_tests={}, cpu_seconds=0., native_steps=0, real_rf_samples=0)
    if ledger["attempts"] and "source_files" not in ledger["attempts"][-1]:
        ledger["attempts"][-1]["source_files"] = ledger["checked_source_files"]
    counts = {key: 0 for key in ("mock_controller_proposals", "mock_candidate_queries", "synthetic_Adam_steps",
        "public_flight_edges", "public_target_returns", "variable_power_arguments", "constant_power_arguments",
        "public_law_bundles", "forbidden_effect_attempts")}
    limits = dict(mock_controller_proposals=976, mock_candidate_queries=768, synthetic_Adam_steps=64,
        public_flight_edges=64, public_target_returns=32, variable_power_arguments=128,
        constant_power_arguments=24, public_law_bundles=8)

    def spend(key):
        if key in limits and ledger["counts"].get(key, 0)+counts[key] >= limits[key]:
            raise RuntimeError("declared cumulative preparation exposure exhausted: "+key)
        counts[key] += 1

    def wrapped(original, key):
        def call(*pos, **kw):
            spend(key)
            return original(*pos, **kw)
        return call

    def forbidden(*pos, **kw):
        counts["forbidden_effect_attempts"] += 1
        raise AssertionError("real native/private-model effect forbidden in B01 preparation")

    b10.AssignmentController.propose = wrapped(b10.AssignmentController.propose, "mock_controller_proposals")
    b10.AssignmentController._query = wrapped(b10.AssignmentController._query, "mock_candidate_queries")
    torch.optim.Adam.step = wrapped(torch.optim.Adam.step, "synthetic_Adam_steps")
    energy.flight_edge = wrapped(energy.flight_edge, "public_flight_edges")
    energy.target_return = wrapped(energy.target_return, "public_target_returns")
    original_power, original_constants = energy.power, energy.PublicLaw.constants
    def power(*pos, **kw):
        spend("constant_power_arguments" if kw.get("constant", False) else "variable_power_arguments")
        return original_power(*pos, **kw)
    def constants(law):
        if law._constants is None:
            spend("public_law_bundles")
        return original_constants(law)
    energy.power, energy.PublicLaw.constants = power, constants
    b10.LawfulServiceModel = b11.LawfulServiceModel = forbidden
    study.make_env = study.make_eval_config = forbidden

    class Record:
        def pytest_runtest_logreport(self, report):
            key = report.nodeid
            if report.failed:
                ledger["latest_tests"][key] = "failed"
            elif report.when == "call":
                ledger["latest_tests"][key] = "passed" if report.passed else "skipped"

    selected = args.tests[1:] if args.tests[:1] == ["--"] else args.tests
    if not selected:
        selected = ["tests/experiments/candidates/uav_service_resource_control/b01_native_selector"]
    attempt = len(ledger["attempts"])+1
    log_path = out/f"attempt_{attempt:02d}.txt"
    if log_path.exists():
        raise FileExistsError(log_path)
    with log_path.open("w", buffering=1) as stream, redirect_stdout(stream), redirect_stderr(stream):
        code = pytest.main(["-q", *selected], plugins=[Record()])
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (time.process_time()-cpu_start + child.ru_utime+child.ru_stime
           - prior_children.ru_utime-prior_children.ru_stime)
    fake_protocol = sum(getattr(module, "FAKE_PROTOCOL_PROPOSALS", 0) for name, module in sys.modules.items()
                        if name.endswith("test_replay"))
    count = dict(counts, fake_reader_protocol_proposals=fake_protocol)
    ledger["attempts"].append(dict(attempt=attempt, pytest_args=selected, exit_code=int(code),
        log=log_path.name, log_sha256=hashlib.sha256(log_path.read_bytes()).hexdigest(),
        cpu_seconds=cpu, wall_seconds=time.perf_counter()-wall_start, counts=count))
    ledger["cpu_seconds"] += cpu
    for key, value in count.items():
        ledger["counts"][key] = ledger["counts"].get(key, 0)+value
    ledger["status"] = "accepted" if code == 0 and not counts["forbidden_effect_attempts"] and all(
        value == "passed" for value in ledger["latest_tests"].values()) else "incomplete"
    files = list(Path(__file__).parent.glob("*.py")) + list((ROOT/
        "tests/experiments/candidates/uav_service_resource_control/b01_native_selector").glob("*.py"))
    ledger["checked_source_files"] = {str(file.relative_to(ROOT)): hashlib.sha256(file.read_bytes()).hexdigest()
                                      for file in sorted(files)}
    ledger["attempts"][-1]["source_files"] = ledger["checked_source_files"]
    ledger["environment"] = dict(python=sys.version, numpy=np.__version__, torch=torch.__version__,
                                  torch_threads=torch.get_num_threads(), numeric_thread_env=1)
    ledger["limits"] = limits
    ledger["scope"] = ("real native steps0/private RF0; mocked frozen-controller requests and actual synthetic optimizer/public-law arguments counted; "
                       "fake reader protocol calls are dictionary/array wiring assertions without a real controller/physics/learner")
    write_json(path, ledger)
    print(log_path.read_text())
    print(json.dumps(dict(status=ledger["status"], cpu_seconds=ledger["cpu_seconds"], counts=ledger["counts"]), indent=2))
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
