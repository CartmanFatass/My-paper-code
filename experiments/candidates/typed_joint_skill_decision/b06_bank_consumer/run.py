"""Preparation-only B06 stdlib stage parent; certification/investment must bind first."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import selectors
import resource
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import contract as c
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import evidence as e
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import billing, commitment


class ExecTransport:
    """Exactly one fresh exec at a time; failed child is reaped and never retried."""
    def __init__(self, store, bill):
        self.store, self.bill, self.active = store, bill, None

    def __call__(self, job, request, on_ready):
        if self.active is not None:
            raise RuntimeError("sequential child ownership required")
        base = "children/" + job["id"]
        self.store.write(base + "/request.json", request)
        read_parent, write_child = os.pipe()
        read_child, write_parent = os.pipe()
        started = time.monotonic()
        own_started = time.process_time()
        reaped_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        counts_before = self.bill.counter_snapshot()
        exited_at = None
        process = None
        selector = selectors.DefaultSelector()
        pending = b""
        try:
            with c.relative(self.store.root, base + "/stdout.log").open("xb") as stdout, \
                    c.relative(self.store.root, base + "/stderr.log").open("xb") as stderr:
                command = [sys.executable, "-B", "-m",
                    "experiments.candidates.typed_joint_skill_decision.b06_bank_consumer.worker",
                    "--request", str(c.relative(self.store.root, base + "/request.json")),
                    "--request-sha256", self.store.files[base + "/request.json"]["sha256"],
                    "--read-fd", str(read_child), "--write-fd", str(write_child)]
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                           pass_fds=(read_child, write_child), cwd=ROOT)
                self.active = process
                os.close(read_child)
                read_child = None
                os.close(write_child)
                write_child = None
                selector.register(read_parent, selectors.EVENT_READ)
                complete = None
                while process.poll() is None or selector.get_map():
                    self.bill.current_gpu_child_seconds = time.monotonic() - started if job["gpu"] else 0.
                    self.bill.check()
                    for key, _ in selector.select(.1):
                        block = os.read(key.fd, 65536)
                        if not block:
                            selector.unregister(key.fd)
                            if pending:
                                raise RuntimeError("incomplete child protocol frame")
                            continue
                        pending += block
                        if len(pending) > 1024 ** 2:
                            raise RuntimeError("oversized child protocol frame")
                        while b"\n" in pending:
                            line, pending = pending.split(b"\n", 1)
                            message = json.loads(line)
                            if message["kind"] == "selection_ready":
                                permission = on_ready(message)
                                os.write(write_parent, c.encoded(permission))
                            elif message["kind"] == "complete":
                                if complete is not None:
                                    raise RuntimeError("duplicate child completion")
                                complete = message
                            elif message["kind"] == "failed":
                                raise RuntimeError("first child scientific failure: " + message.get("error", "unknown"))
                            else:
                                raise RuntimeError("unknown child protocol kind")
                exit_code = process.wait()
                exited_at = time.monotonic()
                self.store.write(base + "/process-exit.json", {"pid": process.pid, "exit_code": exit_code, "retry": False})
                if exit_code != 0 or job["stage"] == "cold" and complete is None:
                    raise RuntimeError("first child terminal failure: " + job["id"])
            outcome_path = c.relative(self.store.root, base + "/outcome.json")
            outcome = json.loads(outcome_path.read_bytes())
            manifest_path = c.relative(self.store.root, base + "/artifacts.json")
            self.store.merge(job, json.loads(manifest_path.read_bytes()))
            self.store.register(base + "/artifacts.json")
            for stream in ("stdout", "stderr"):
                self.store.register(base + "/" + stream + ".log")
            return outcome
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                if exited_at is None:
                    exited_at = time.monotonic()
                if base + "/process-exit.json" not in self.store.files:
                    self.store.write(base + "/process-exit.json", {"pid": process.pid, "exit_code": process.returncode, "retry": False})
                if job["gpu"]:
                    self.bill.charge("gpu_child_microseconds", max(0, round((exited_at - started) * 1e6)))
            self.bill.current_gpu_child_seconds = 0.
            reaped_after = resource.getrusage(resource.RUSAGE_CHILDREN)
            counts_after = self.bill.counter_snapshot()
            self.store.write(base + "/stage-cost.json", {"job": job, "spawned": process is not None,
                "exit_code": None if process is None else process.returncode,
                "wall_seconds_including_parent_manifest_merge": time.monotonic() - started,
                "parent_cpu_seconds": time.process_time() - own_started,
                "reaped_child_cpu_seconds": reaped_after.ru_utime + reaped_after.ru_stime
                    - reaped_before.ru_utime - reaped_before.ru_stime,
                "gpu_child_seconds": 0. if process is None or not job["gpu"] else exited_at - started,
                "gpu_phase_seconds": (counts_after["gpu_reserved_microseconds"] - counts_before["gpu_reserved_microseconds"]) / 1e6,
                "before_counters": counts_before, "after_counters": counts_after,
                "counter_delta": {key: counts_after[key] - value for key, value in counts_before.items()},
                "retry": False, "record_write_tail": "not included in preceding stage sample; covered by parent terminal sample"})
            self.active = None
            selector.close()
            for fd in (read_parent, write_parent, read_child, write_child):
                if fd is not None:
                    os.close(fd)


def run_pipeline(store, bill, transport, parent, bank, original_input):
    """Internal composition for admitted inputs; opaque callbacks permit zero-query mock tests.

    This function is not a public certification entry point. CLI and actual worker both
    refuse pending certification. Neither tests nor a synthetic bank confer run authority.
    """
    assets, initials, cases = [], {}, []
    final_seal = None
    for template in c.jobs():
        job = dict(template)
        request = {"parent": parent, "job": job, "original_input": original_input,
                   "prior_parent_cpu_seconds": e.old.cpu()["total_seconds"]}
        if job["stage"] == "fit":
            stream = job["fit"]["stream"]
            job["new_stream"] = stream not in initials
            request.update(bank={**bank, "files": {k: v for k, v in bank["files"].items()
                                  if k.startswith("raw/bank/train/")}}, initial_hashes=dict(initials))
        elif job["stage"] == "endpoint":
            if len(assets) != 6 or set(initials) != {0, 1}:
                raise AssertionError("six independently sealed fits before fresh access")
            digest = store.seal("final-assets-manifest.json")
            final_seal = {"path": "final-assets-manifest.json", "sha256": digest}
            request.update(bank=bank, assets=list(assets), final_seal=final_seal, inherited_files=dict(store.files))
        elif job["stage"] == "cold":
            asset = next((a for a in assets if a["fit"]["id"] == job["arm"]), None)
            request.update(checkpoint_path=None if asset is None else str(store.root / asset["path"]),
                           checkpoint_sha256=None if asset is None else asset["sha256"])
        elif job["stage"] == "reader":
            if len(cases) != 1152:
                raise AssertionError("complete fixed native cases before whole CPU reader")
            request.update(bank=bank, assets=list(assets), cases=list(cases), inherited_files=dict(store.files))
        ready = None
        decision = None
        stage_started = time.monotonic()
        parent_cpu_started = time.process_time()
        def on_ready(message):
            nonlocal ready, decision
            if job["stage"] != "cold" or ready is not None:
                raise AssertionError("single immutable cold selection required")
            # Preserve B04's endpoint: arrival, before any post-commit reference read.
            arrived_wall = time.monotonic() - stage_started
            arrived_parent_cpu = time.process_time() - parent_cpu_started
            selection = "raw/main/" + str(job["world"]) + "/" + job["arm"] + "/selection.json"
            if message["selection"] != selection:
                raise AssertionError("cold selection ownership")
            ready = message["sha256"]
            # Read immutable selection before any reference/endpoint access.
            decision = store.selection(selection, ready)
            reference = store.load("commitments/" + str(job["world"]) + ".json")
            commitment.verify(decision, reference, world=job["world"], arm=job["arm"],
                              launch_sha=parent["launch_sha"], input_sha256=c.SCIENCE_INPUT)
            decision.update(parent_cold_selection_seconds=arrived_wall,
                            selection_child_cpu=message["cpu"],
                            selection_parent_cpu_seconds=arrived_parent_cpu,
                            cold_scope="fresh exec through immutable selection-ready; full GPU child measured separately")
            bill.check()
            return {"kind": "verified", "sha256": ready}
        try:
            bill.check()
            bill.charge("spawn_attempts")
            result = transport(job, request, on_ready)
            bill.charge("spawn_completed")
            if job["stage"] == "fit":
                asset = result["asset"]
                observed = {int(k): value for k, value in result["initial_hashes"].items()}
                if asset["fit"] != job["fit"] or set(observed) != set(initials) | {stream}:
                    raise AssertionError("fit/initializer stream identity")
                if any(observed[k] != value for k, value in initials.items()) or observed[stream] != asset["initial_sha256"]:
                    raise AssertionError("same-stream actual initial weights differ across fit processes")
                store.check(asset["path"], asset["sha256"])
                if job["new_stream"]:
                    store.check("raw/initial/stream" + str(stream) + ".pt")
                initials = observed
                assets.append(asset)
            elif job["stage"] == "cold":
                if ready is None or result["kind"] != "complete":
                    raise AssertionError("cold child completed without lawful immutable commitment")
                selection = "raw/main/" + str(job["world"]) + "/" + job["arm"] + "/selection.json"
                store.check(selection, ready)
                decision.update(case_counts=result["case_counts"], child_total_cpu=result["cpu"],
                                parent_case_wall_seconds=time.monotonic() - stage_started)
                base = "raw/main/" + str(job["world"]) + "/" + job["arm"]
                store.write(base + "/decision.json", decision)
                store.write(base + "/matched-endpoint.json", result["matched_endpoint"])
                cases.append({"world": job["world"], "arm": job["arm"], "decision": base + "/decision.json",
                              "native": base + "/native.json", "trace": base + "/trace.jsonl.gz",
                              "queries": base + "/queries.jsonl.gz", "matched_endpoint": result["matched_endpoint"],
                              "selection_counts": decision["selection_counts"]})
            elif job["stage"] == "reader":
                billing.count_complete(bill.counter_snapshot(), cases)
                summary = dict(result["summary"])
                summary.update(schema=1, direction=c.DIRECTION, launch_sha=parent["launch_sha"],
                               scientific_source_sha=c.SCIENCE_SHA, scientific_input_sha256=c.SCIENCE_INPUT,
                               consumer_input_sha256=parent["consumer_input_sha256"], checkpoint_input_sha256=c.SCIENCE_INPUT,
                               bill=bill.snapshot(), diagnostics=result["diagnostics"],
                               bank_producer_source_sha=bank["producer_source_sha"],
                               bank_producer_input_sha256=bank["producer_input_sha256"],
                               bank_manifest_sha256=bank["manifest_sha256"])
                bill.seal_counts(store)
                store.write("summary.json", summary)
                store.seal()
                return summary
        except BaseException as exc:
            store.failure_prefix(job)
            bill.seal_counts(store)
            store.write("failure.json", {"job": job, "type": type(exc).__name__, "error": str(exc),
                                         "bill": bill.snapshot(), "retry": False, "continuation": False})
            store.seal()
            raise
    raise AssertionError("missing terminal reader")


def terminal_resources(store, bill, error):
    """Post-seal check/sample without recursive self-hashing or manifest overwrite."""
    manifest_path = store.root / "artifact-manifest.json"
    digest = c.sha(manifest_path) if manifest_path.exists() else None
    resource_error = None
    try:
        bill.last_disk_time = -float("inf")
        bill.check(pending=65536)
    except BaseException as exc:
        resource_error = {"type": type(exc).__name__, "error": str(exc)}
    value = {"status": "complete" if error is None and resource_error is None else "failed",
             "manifest_sha256": digest, "bill_after_manifest_hashing": bill.snapshot(),
             "pipeline_error": None if error is None else {"type": type(error).__name__, "error": str(error)},
             "post_seal_resource_error": resource_error,
             "record_scope": "unbound terminal record deliberately outside immutable manifest; bind by terminal collection",
             "final_record_write_and_counter_close_tail": "unmeasured; not zero; 64KiB space reserved"}
    e.durable(store.root / "terminal-resource.json", c.encoded(value))
    if resource_error is not None and error is None:
        raise RuntimeError("post-seal resource boundary: " + resource_error["error"])


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--seed", required=True, type=int, choices=[0])
    p.add_argument("--launch-sha", required=True)
    p.add_argument("--input-manifest", required=True, type=Path)
    p.add_argument("--input-manifest-sha256", required=True)
    return p


def main(argv=None):
    started = time.monotonic()
    args = parser().parse_args(argv)
    from scripts.hmasd_admission import require_admission
    admission = dict(require_admission(__file__, direction=c.DIRECTION))
    spec = json.loads(os.environ.get("HMASD_ADMISSION_V1", "{}"))
    if (Path(spec["source_root"]).resolve() != ROOT or Path(spec["output_root"]).resolve() != args.out.resolve()
            or admission["sha"] != args.launch_sha):
        raise ValueError("exact admitted source/output/launch identity required")
    launch = json.loads((args.out / "launch-manifest.json").read_bytes())
    if launch["sha"] != args.launch_sha or launch["command_sha256"] != admission["command_sha256"]:
        raise ValueError("actual launcher identity mismatch")
    binding = c.bound_json(args.input_manifest, args.input_manifest_sha256)
    limits = c.investment(binding.get("investment"))
    paid_preparation = c.preparation_cost(binding.get("preparation_cost"), ROOT)
    original = c.scientific_binding(binding, ROOT)
    certified = c.certify_bank(binding.get("bank"))  # Always refuses until real final interface is bound.
    roots = {str(Path(value).resolve()) for value in binding["disk_roots"]}
    expected_roots = {str(ROOT), str(args.out.resolve()), str(Path(certified.root).resolve()),
                      str(Path(binding["own_scratch"]).resolve())}
    if roots != expected_roots or args.out.resolve() == Path(certified.root).resolve():
        raise ValueError("one declared bank/source/output/scratch scope; no old asset or per-child bank replicas")
    c.guard_parent()
    c.threads()
    os.environ["CUDA_CACHE_PATH"] = str(Path(binding["own_scratch"]) / "b06-cuda-cache")
    store = e.ParentStore(args.out)
    deployment = {"limits": limits, "disk_roots": binding["disk_roots"],
                  "started_monotonic": started, "prior_bank_cost": certified.prior_cost,
                  "prior_preparation_cost": paid_preparation}
    shared = billing.Shared(args.out / "shared-counters.bin", create=True)
    bill = billing.Bill(shared, deployment)
    parent = {"pid": os.getpid(), "identity": c.process_identity(os.getpid()), "admission": admission, "source_root": str(ROOT), "out": str(args.out),
              "launch_sha": args.launch_sha, "source_binding": {key: binding[key] for key in
                    ("scientific_source_sha", "scientific_input_sha256", "frozen_sources")},
              "investment": binding["investment"], "deployment": deployment,
              "consumer_input_sha256": args.input_manifest_sha256,
              "counter_path": str(args.out / "shared-counters.bin")}
    # Scope/real certification publication is still pending; no default roots or budgets.
    store.write("config.json", {"launch_sha": args.launch_sha, "consumer_input_sha256": args.input_manifest_sha256,
                              "scientific_source_sha": c.SCIENCE_SHA, "scientific_input_sha256": c.SCIENCE_INPUT,
                              "binding": binding, "admission": admission})
    error = None
    try:
        run_pipeline(store, bill, ExecTransport(store, bill), parent, vars(certified), original)
        return 0
    except BaseException as exc:
        error = exc
        raise
    finally:
        try:
            terminal_resources(store, bill, error)
        finally:
            shared.close()


if __name__ == "__main__":
    raise SystemExit(main())
