"""One admitted B03 operation: 192 immutable selections, exact aliases, seven flights, full reader."""
from __future__ import annotations

import argparse
import json
import multiprocessing
import os
from pathlib import Path
import platform
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from experiments.candidates.typed_joint_skill_decision.b02 import evidence as e
from experiments.candidates.typed_joint_skill_decision.b03.budget import Bill, COUNTERS, LIMITS


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--launch-sha", required=True)
    p.add_argument("--seed", type=int, choices=[0], required=True)
    p.add_argument("--input-manifest", type=Path, required=True)
    p.add_argument("--input-manifest-sha256", required=True)
    return p


def threads():
    values = {k: "1" for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
    os.environ.update(values)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    return values


def validate_inputs(manifest, root):
    from experiments.candidates.typed_joint_skill_decision.b03.reader import NEW_WORLDS, AUDIT_WORLDS
    expected_limits = {"cpu_seconds": 1800, "fits": 0, "gpu_forwards": 0,
                       "incremental_and_prior_input_disk_bytes": LIMITS["disk_bytes"],
                       "native_steps": 4500, "static_calls": 1155699}
    expected_counts = {"expected_selection_static_calls": 303551, "expected_total_static_calls": 307058,
                       "fits": 0, "native_steps": 4500, "new_main_native_episodes": 7,
                       "new_state_static_checks": 3507, "original_executor_audit_episodes": 2,
                       "reused_G_native_episodes": 64, "reused_P_native_episodes": 64,
                       "reused_Q_native_episodes": 57, "selection_processes": 192,
                       "worst_budget_static_calls": 1155699}
    if (manifest["schema"] != 1 or manifest["study"] != "b03_fixed_prefix_completion"
            or manifest["arms"] != ["G", "Q", "P"] or manifest["prefix_queries"] != 36
            or manifest["horizon"] != 500 or manifest["worlds"] != list(range(107100000, 107100064))
            or manifest["arm_order"] != "rotate [G,Q,P] left by world offset mod3"
            or manifest["new_native_worlds"] != list(NEW_WORLDS)
            or manifest["original_executor_audit_worlds"] != list(AUDIT_WORLDS)
            or manifest["limits"] != expected_limits or manifest["counts"] != expected_counts):
        raise ValueError("fixed B03 contract mismatch")
    for mapping in ("pinned_upstream_sources", "pinned_reused_b02_sources"):
        for relative, digest in manifest[mapping].items():
            if e.sha(e.relative_path(root, relative)) != digest:
                raise ValueError("pinned source mismatch: " + relative)


CHILD_FIELDS = {"parent_pid", "admission", "launch_sha", "source_root", "out", "prior_parent_cpu_seconds"}


def checked_child(context):
    if (set(context) != CHILD_FIELDS or context["parent_pid"] != os.getppid()
            or context["admission"]["child_pid"] != os.getppid()
            or context["admission"]["direction"] != "typed_joint_skill_decision"
            or context["admission"]["sha"] != context["launch_sha"]
            or Path(context["source_root"]).resolve() != ROOT):
        raise RuntimeError("child requires exact legal-only admitted parent context")
    launch = json.loads((Path(context["out"]) / "launch-manifest.json").read_bytes())
    if launch["sha"] != context["launch_sha"] or launch["command_sha256"] != context["admission"]["command_sha256"]:
        raise RuntimeError("child launch identity differs")


def child_write(path, value, bill):
    data = e.encoded(value)
    bill.check(pending=len(data) + 65536)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return e.sha(path)


def case_main(connection, context, bill, world, arm):
    trace, paths = None, []
    try:
        checked_child(context)
        if world not in range(107100000, 107100064) or arm not in ("G", "Q", "P"):
            raise ValueError("undeclared case")
        bill.prior_parent_cpu_seconds = context["prior_parent_cpu_seconds"]
        thread_env = threads()
        before = bill.snapshot()["counters"]
        started = time.perf_counter()
        import numpy as np
        if np.__version__ != "1.26.3" or platform.python_version() != "3.10.21":
            raise RuntimeError("original Python3.10.21/NumPy1.26.3 required")
        from experiments.candidates.typed_joint_skill_decision.b02.native import Native, reset_identity, execute, state, rng_identity
        from experiments.candidates.typed_joint_skill_decision.b03.prefix import choose
        imports = time.perf_counter() - started
        base = f"raw/main/{world}/{arm}"
        query_path = base + "/search-queries.jsonl.gz"
        trace = e.Trace(e.relative_path(context["out"], query_path), bill)
        paths.append(query_path)
        with Native(bill) as native:
            native.query_trace = trace
            t = time.perf_counter()
            env = native.host.make_host(world, area_size=5000)
            host_seconds = time.perf_counter() - t
            decision = choose(env, native.p, world, arm)
            native.query_trace = None
            trace.close()
            trace = None
            t = time.perf_counter()
            decision["reset_identity"] = reset_identity(env, decision)
            decision["timing"].update(import_seconds=imports, host_init_seconds=host_seconds,
                                       execution_identity_reset_seconds=time.perf_counter() - t,
                                       child_selection_seconds=time.perf_counter() - started)
            after = bill.snapshot()["counters"]
            decision["selection_counts"] = {k: after[k] - before[k] for k in COUNTERS}
            expected = decision["flat"]["evaluations"] + decision["relay"]["evaluations"] + 1
            if decision["selection_counts"]["static_calls"] != expected or decision["selection_counts"]["native_steps"] != 0:
                raise AssertionError("selection work/count mismatch")
            decision["threads"] = thread_env
            decision["source_sha"] = context["launch_sha"]
            decision["child_interpreter"] = {"python": platform.python_version(), "numpy": np.__version__, "executable": sys.executable}
            selection_path = base + "/selection.json"
            digest = child_write(e.relative_path(context["out"], selection_path), decision, bill)
            paths.append(selection_path)
            connection.send({"kind": "selection_ready", "path": selection_path, "sha256": digest,
                             "paths": paths, "child_cpu": e.cpu()})
            # No prior outcome, locator, expected rank or alias map is received here.
            gate = connection.recv()
            if set(gate) != {"kind", "selection_sha256", "new_episode"} or gate["kind"] != "verified" or gate["selection_sha256"] != digest:
                raise AssertionError("selection authorization mismatch")
            if gate["new_episode"]:
                from experiments.candidates.typed_joint_skill_decision.b03.reader import NEW_WORLDS
                if arm != "Q" or world not in NEW_WORLDS:
                    raise AssertionError("unlisted native episode")
                original_step = env.step
                first = True
                def guarded_step(*args, **kwargs):
                    nonlocal first
                    if first:
                        actual = {"native_rng_sha256": rng_identity(env), "agents": list(env.agents),
                                  "transmitter_mask": e.plain(env._transmitter_mask), "state": state(env)}
                        if e.encoded(actual) != e.encoded(decision["reset_identity"]):
                            raise AssertionError("first-step full reset identity differs from committed gate")
                        first = False
                    return original_step(*args, **kwargs)
                env.step = guarded_step
                native_path, result_path = base + "/trace.jsonl.gz", base + "/native.json"
                paths.append(native_path)
                result = execute(env, decision, e.relative_path(context["out"], native_path), bill)
                child_write(e.relative_path(context["out"], result_path), result, bill)
                paths.append(result_path)
                bill.charge("main_episodes")
            after = bill.snapshot()["counters"]
            counts = {k: after[k] - before[k] for k in COUNTERS}
            if counts["native_steps"] != (500 if gate["new_episode"] else 0):
                raise AssertionError("case native work differs from accepted alias gate")
            connection.send({"kind": "complete", "paths": paths, "case_counts": counts, "child_cpu": e.cpu()})
    except BaseException as exc:
        if trace is not None:
            trace.close()
        failure = {"type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(),
                   "bill": bill.snapshot(), "world": world, "arm": arm, "paths": paths}
        path = e.relative_path(context["out"], f"raw/main/{world}/{arm}/failure.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        # Failure evidence is retained even when the attempted work exhausted the allowance.
        path.write_bytes(e.encoded(failure))
        connection.send({"kind": "failed", **failure})
    finally:
        connection.close()


def spawn_case(ctx, context, bill, store, prior, diagnostics, world, arm):
    from experiments.candidates.typed_joint_skill_decision.b03.reader import verify_gate
    parent, child = ctx.Pipe(duplex=True)
    context = {**context, "prior_parent_cpu_seconds": e.cpu()["total_seconds"]}
    process = ctx.Process(target=case_main, args=(child, context, bill, world, arm))
    started = time.perf_counter()
    ready, decision, gate, completion = None, None, None, None
    bill.charge("spawn_attempts")
    try:
        process.start()
        child.close()
        while process.is_alive() or parent.poll():
            if parent.poll(.25):
                try:
                    message = parent.recv()
                except EOFError:
                    break
                if message["kind"] == "selection_ready":
                    if ready is not None:
                        raise AssertionError("duplicate selection readiness")
                    ready = time.perf_counter() - started  # Ends BEFORE the first old-outcome read.
                    for relative in message["paths"]:
                        store.register(relative)
                    path = e.relative_path(store.root, message["path"])
                    if e.sha(path) != message["sha256"]:
                        raise AssertionError("immutable child selection hash mismatch")
                    decision = e.load_output(store.root, store.files, message["path"])
                    if decision["world"] != world or decision["arm"] != arm or decision["source_sha"] != context["launch_sha"]:
                        raise AssertionError("child selection address/source mismatch")
                    decision.update(parent_cold_selection_seconds=ready, child_selection_cpu=message["child_cpu"],
                                    cold_latency_scope="fresh process through immutable selection-ready, including required trace/selection serialization; before alias lookup")
                    gate = verify_gate(prior, decision, e.relative_path(store.root, message["paths"][0]), diagnostics, bill)
                    bill.check()
                    store.write(f"raw/main/{world}/{arm}/gate.json", gate)
                    parent.send({"kind": "verified", "selection_sha256": message["sha256"], "new_episode": gate["new_episode"]})
                elif message["kind"] in ("complete", "failed"):
                    completion = message
                else:
                    raise AssertionError("unknown child message")
            bill.check()
        process.join()
        bill.check()
        if completion is not None:
            for relative in completion["paths"]:
                if e.relative_path(store.root, relative).is_file():
                    store.register(relative)
        if process.exitcode != 0 or completion is None or completion["kind"] != "complete" or ready is None:
            store.progress("child_failed", world=world, arm=arm, exitcode=process.exitcode, message=completion)
            raise RuntimeError(f"case {world}/{arm} failed without retry; exit={process.exitcode}, error={completion and completion.get('error')}")
        decision.update(case_counts=completion["case_counts"], child_cpu=completion["child_cpu"],
                        parent_process_wall_seconds=time.perf_counter() - started, process_exitcode=process.exitcode)
        relative = f"raw/main/{world}/{arm}/decision.json"
        store.write(relative, decision)
        bill.charge("spawn_completed")
        bill.charge("selection_processes")
        return {"world": world, "arm": arm, "decision_path": relative, "gate": gate,
                "trace_path": f"raw/main/{world}/{arm}/trace.jsonl.gz" if gate["new_episode"] else None,
                "native_path": f"raw/main/{world}/{arm}/native.json" if gate["new_episode"] else None,
                "selection_static_calls": gate["selection_static_calls"]}
    except BaseException:
        if process.pid is not None and process.is_alive():
            process.terminate()
            process.join()
        base = store.root / "raw" / "main" / str(world) / arm
        if base.exists():
            for path in base.rglob("*"):
                if path.is_file():
                    store.register(str(path.relative_to(store.root)))
        raise
    finally:
        parent.close()
        child.close()


def complete_counts(counts, cases):
    expected = {"static_calls": 307058, "static_completed": 307058, "native_steps": 4500, "native_completed": 4500,
                "fits": 0, "fits_completed": 0, "main_episodes": 7, "audit_episodes": 2,
                "spawn_attempts": 192, "spawn_completed": 192, "selection_processes": 192,
                "alias_gates": 192, "reused_episodes": 185, "prior_episode_reads": 185,
                "reader_state_checks": 3507, "reader_reference_searches": 0}
    by_arm = {arm: sum(c["selection_static_calls"] for c in cases if c["arm"] == arm) for arm in ("G", "Q", "P")}
    if any(counts[k] != n for k, n in expected.items()) or by_arm != {"G": 85192, "Q": 90257, "P": 128102}:
        raise AssertionError(f"complete exact work mismatch: counts={counts}, selection={by_arm}")


def main(argv=None):
    args = parser().parse_args(argv)
    spec = json.loads(os.environ.get("HMASD_ADMISSION_V1", "{}"))
    from scripts.hmasd_admission import require_admission
    admission = dict(require_admission(__file__, direction="typed_joint_skill_decision"))
    source, out = Path(spec["source_root"]).resolve(strict=True), args.out.resolve()
    if (source != ROOT or out != Path(spec["output_root"]).resolve()
            or args.launch_sha != admission["sha"] or len(args.launch_sha) != 40):
        raise ValueError("exact admitted source/output/SHA required")
    launch = json.loads((out / "launch-manifest.json").read_bytes())
    if (Path(launch["source_root"]).resolve() != source or Path(launch["output_root"]).resolve() != out
            or launch["sha"] != args.launch_sha or launch["direction"] != "typed_joint_skill_decision"
            or launch["command_sha256"] != admission["command_sha256"]):
        raise ValueError("launcher identity differs")
    thread_env = threads()
    manifest = e.bound_json(args.input_manifest, args.input_manifest_sha256)
    validate_inputs(manifest, source)
    roots = [source, Path(manifest["prior_root"]).resolve(strict=True), out]
    if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(roots) for b in roots[i + 1:]):
        raise ValueError("source/prior/output roots must be disjoint")
    ctx = multiprocessing.get_context("spawn")
    bill = Bill(ctx.Array("q", len(COUNTERS), lock=False), ctx.Lock(), roots)
    store = e.Store(out, bill)
    diagnostics, prior = [], None
    try:
        bill.check(pending=1048576)
        from experiments.candidates.typed_joint_skill_decision.b03.reader import Prior, complete_reader
        prior = Prior(manifest, source)
        store.write("config.json", {"schema": 1, "study": manifest["study"], "launch_sha": args.launch_sha,
                                    "source_root": source, "admission": admission, "input_manifest_sha256": args.input_manifest_sha256,
                                    "input_manifest_data": manifest, "numerical_threads": thread_env, "seed": 0,
                                    "dtype": "float64", "reader_information_boundary": manifest["reader_information_boundary"],
                                    "argv": sys.argv[1:] if argv is None else argv})
        import numpy as np
        if np.__version__ != "1.26.3" or platform.python_version() != "3.10.21":
            raise RuntimeError("original Python3.10.21/NumPy1.26.3 required")
        context = {"parent_pid": os.getpid(), "admission": admission, "launch_sha": args.launch_sha,
                   "source_root": str(source), "out": str(out)}
        cases = []
        for i, world in enumerate(manifest["worlds"]):
            order = ["G", "Q", "P"]
            for arm in order[i % 3:] + order[:i % 3]:
                cases.append(spawn_case(ctx, context, bill, store, prior, diagnostics, world, arm))
                store.progress("main", completed_cases=len(cases), total_cases=192, world=world, arm=arm)
        store.write_gzip("raw/main/cases.json.gz", cases)
        summary = complete_reader(store, prior, {(c["world"], c["arm"]): c for c in cases}, diagnostics)
        complete_counts(bill.snapshot()["counters"], cases)
        store.write_gzip("raw/reader/checks.json.gz", diagnostics)
        store.write("raw/reader/prior-used-artifacts.json", {"root": prior.root, "manifest_sha256": manifest["prior_manifest_sha256"], "files": prior.used})
        bill.check()
        summary.update(schema=1, direction="typed_joint_skill_decision", launch_sha=args.launch_sha,
                       input_manifest_sha256=args.input_manifest_sha256,
                       diagnostics={"path": "raw/reader/checks.json.gz", "count": len(diagnostics), "format": "gzip compressed complete JSON"},
                       bill=bill.snapshot(), interpreter={"python": platform.python_version(), "numpy": np.__version__, "executable": sys.executable})
        store.write("summary.json", summary)
        store.progress("complete", completed_cases=192, completed_reader_worlds=64)
        return 0
    except BaseException as exc:
        try:
            if "raw/reader/checks.json.gz" not in store.files:
                store.write_gzip("raw/reader/checks.json.gz", diagnostics)
            if prior is not None and "raw/reader/prior-used-artifacts.json" not in store.files:
                store.write("raw/reader/prior-used-artifacts.json", {"root": prior.root, "manifest_sha256": manifest["prior_manifest_sha256"], "files": prior.used})
        except BaseException as preservation_error:
            # A hard-cap failure cannot purchase an unbounded diagnostic dump. Retain
            # every already-written stream plus both errors and attempted counters.
            store.progress("diagnostic_preservation_failed", original_error=str(exc), error=str(preservation_error))
        store.failure(exc)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
