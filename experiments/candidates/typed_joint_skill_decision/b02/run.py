"""Single admitted B02 operation: one fit, 192 serial fresh-process cases, complete reader.

No worker CLI or skip-reader/fit knobs. A spawned callable is computation within its
accepted parent, with an explicit checked parent/admission/source/output context.
"""
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


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--launch-sha", required=True)
    p.add_argument("--seed", required=True, type=int, choices=[0])
    p.add_argument("--input-root", required=True, type=Path)
    p.add_argument("--input-manifest", required=True, type=Path)
    p.add_argument("--input-manifest-sha256", required=True)
    return p


def threads():
    result = {k: "1" for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
    os.environ.update(result)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True  # Keep admitted source allocation immutable after its sample.
    return result


def checked_child(context):
    if (context["parent_pid"] != os.getppid() or context["admission"]["child_pid"] != os.getppid()
            or context["admission"]["direction"] != "typed_joint_skill_decision"
            or context["admission"]["sha"] != context["launch_sha"]
            or Path(context["source_root"]).resolve() != ROOT
            or not Path(context["out"]).is_dir()):
        raise RuntimeError("spawned case is not computation of this admitted parent/source")
    launch = json.loads((Path(context["out"]) / "launch-manifest.json").read_bytes())
    if launch["sha"] != context["launch_sha"] or launch["command_sha256"] != context["admission"]["command_sha256"]:
        raise RuntimeError("child launch identity differs")


def case_main(connection, context, bill, world, arm):
    # Must stay stdlib-only before checking the inherited parent admission.
    trace = None
    paths = []
    try:
        checked_child(context)
        bill.prior_parent_cpu_seconds = context["prior_parent_cpu_seconds"]
        thread_env = threads()
        before = bill.snapshot()["counters"]
        started = time.perf_counter()
        import numpy as np
        from experiments.candidates.typed_joint_skill_decision.b02.native import Native, execute
        from experiments.candidates.typed_joint_skill_decision.b02.search import prepare_and_choose
        import_seconds = time.perf_counter() - started
        base = f"raw/main/{world}/{arm}"
        trace = e.Trace(e.relative_path(context["out"], base + "/search-queries.jsonl.gz"), bill)
        paths.append(base + "/search-queries.jsonl.gz")
        with Native(bill) as native:
            native.query_trace = trace
            t = time.perf_counter()
            env = native.host.make_host(world, area_size=5000)
            host_seconds = time.perf_counter() - t
            fit = None
            t = time.perf_counter()
            if arm == "L":
                fit = e.bound_json(context["model_path"], context["model_sha256"])
            model_seconds = time.perf_counter() - t
            decision = prepare_and_choose(env, native.p, world, arm, fit)
            native.query_trace = None
            trace.close()
            trace = None
            decision["timing"].update(import_seconds=import_seconds, host_init_seconds=host_seconds,
                                       frozen_model_read_seconds=model_seconds,
                                       child_selection_seconds=time.perf_counter() - started)
            decision["threads"] = thread_env
            # Preserve completed search evidence before entering flight.
            pending = e.relative_path(context["out"], base + "/selection.json")
            data = e.encoded(decision)
            bill.check(pending=len(data) + 65536)
            pending.write_bytes(data)
            paths.append(base + "/selection.json")
            connection.send({"kind": "selection_ready", "child_cpu": e.cpu()})
            native_path = base + "/trace.jsonl.gz"
            paths.append(native_path)
            result = execute(env, decision, e.relative_path(context["out"], native_path), bill)
            native_output = base + "/native.json"
            data = e.encoded(result)
            bill.check(pending=len(data) + 65536)
            e.relative_path(context["out"], native_output).write_bytes(data)
            paths.append(native_output)
            bill.charge("main_episodes")
            after = bill.snapshot()["counters"]
            decision["case_counts"] = {k: after[k] - before[k] for k in e.COUNTERS}
            decision["child_cpu"] = e.cpu()
            decision["child_interpreter"] = {"python": platform.python_version(), "executable": sys.executable,
                                               "numpy": np.__version__, "host": platform.node()}
            if decision["case_counts"]["native_steps"] != 500:
                raise AssertionError("case must contain exactly H500 native attempts")
            search_calls = decision["flat"]["evaluations"] + decision["relay"]["evaluations"] + 1
            if decision["case_counts"]["static_calls"] != search_calls:
                raise AssertionError("paid search/static metadata counter mismatch")
            connection.send({"kind": "complete", "decision": decision, "paths": paths})
    except BaseException as exc:
        if trace is not None:
            trace.close()
        # Counter attempt evidence survives even a failed native call; no automatic retry.
        failure = {"type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(),
                   "bill": bill.snapshot(), "world": world, "arm": arm, "paths": paths}
        if Path(context["out"]).is_dir():
            relative = f"raw/main/{world}/{arm}/failure.json"
            path = e.relative_path(context["out"], relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(e.encoded(failure))
            paths.append(relative)
        connection.send({"kind": "failed", **failure})
    finally:
        connection.close()


def spawn_case(ctx, context, bill, store, world, arm):
    parent, child = ctx.Pipe(duplex=False)
    context = {**context, "prior_parent_cpu_seconds": e.cpu()["total_seconds"]}
    process = ctx.Process(target=case_main, args=(child, context, bill, world, arm))
    started = time.perf_counter()
    ready_seconds, selection_cpu, completion = None, None, None
    bill.charge("spawn_attempts")
    try:
        process.start()
        child.close()
        while process.is_alive() or parent.poll():
            if parent.poll(1.0):
                try:
                    message = parent.recv()
                except EOFError:
                    break
                if message["kind"] == "selection_ready":
                    if ready_seconds is not None:
                        raise AssertionError("duplicate selection-ready notification")
                    ready_seconds = time.perf_counter() - started
                    selection_cpu = message["child_cpu"]
                elif message["kind"] in ("complete", "failed"):
                    completion = message
            bill.check()  # self + already reaped + all still-live children, including resource tracker.
        process.join()
        bill.check()
        if completion is not None:
            for relative in completion["paths"]:
                if e.relative_path(store.root, relative).is_file():
                    store.register(relative)
        if process.exitcode != 0 or completion is None or completion["kind"] != "complete":
            store.progress("child_failed", world=world, arm=arm, exitcode=process.exitcode,
                           message=completion, selection_ready_seconds=ready_seconds,
                           parent_process_wall_seconds=time.perf_counter() - started)
            raise RuntimeError(f"case {world}/{arm} failed without retry: exit={process.exitcode}, message={completion and completion.get('error')}")
        if ready_seconds is None:
            raise AssertionError("completed case omitted cold decision readiness")
        decision = completion["decision"]
        decision.update(parent_cold_selection_seconds=ready_seconds,
                        child_selection_cpu=selection_cpu,
                        cold_latency_scope="fresh spawned interpreter through selection-ready; includes required search trace/selection evidence serialization and instrumentation, not uninstrumented production latency",
                        parent_process_wall_seconds=time.perf_counter() - started, process_exitcode=process.exitcode)
        store.write(f"raw/main/{world}/{arm}/decision.json", decision)
        bill.charge("spawn_completed")
        return {"world": world, "arm": arm, "cold_selection_seconds": ready_seconds,
                "process_wall_seconds": decision["parent_process_wall_seconds"], "case_counts": decision["case_counts"]}
    except BaseException:
        if process.pid is not None and process.is_alive():
            process.terminate()
            process.join()
        # Preserve every extant child file after forced/resource termination, including partial gzip.
        base = store.root / "raw" / "main" / str(world) / arm
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file():
                    store.register(str(p.relative_to(store.root)))
        raise
    finally:
        parent.close()
        child.close()


def main(argv=None):
    args = parser().parse_args(argv)
    # Capture path fields before the single-use helper consumes this environment value.
    spec = json.loads(os.environ.get("HMASD_ADMISSION_V1", "{}"))
    from scripts.hmasd_admission import require_admission
    admission = dict(require_admission(__file__, direction="typed_joint_skill_decision"))
    if admission["sha"] != args.launch_sha or len(args.launch_sha) != 40:
        raise ValueError("exact admitted launch SHA required")
    out = args.out.resolve()
    source_root = Path(spec["source_root"]).resolve(strict=True)
    if source_root != ROOT or out != Path(spec["output_root"]).resolve():
        raise ValueError("output/source must match the admitting kernel")
    launch = json.loads((out / "launch-manifest.json").read_bytes())
    if (Path(launch["output_root"]).resolve() != out or Path(launch["source_root"]).resolve() != source_root
            or launch["direction"] != "typed_joint_skill_decision" or launch["sha"] != args.launch_sha
            or launch["command_sha256"] != admission["command_sha256"]):
        raise ValueError("launcher manifest identity mismatch")
    input_root = args.input_root.resolve(strict=True)
    roots = [source_root, input_root, out]
    if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(roots) for b in roots[i + 1:]):
        raise ValueError("incremental source/input/output roots must be distinct and disjoint")
    thread_env = threads()
    ctx = multiprocessing.get_context("spawn")
    bill = e.Bill(ctx.Array("q", len(e.COUNTERS), lock=False), ctx.Lock(), roots)
    store = e.Store(out, bill)
    try:
        bill.check(pending=1024 ** 2)
        manifest = e.bound_json(args.input_manifest, args.input_manifest_sha256)
        paths = e.verify_inputs(manifest, source_root, input_root)
        store.write("config.json", {"schema": 1, "study": "b02_search_branch", "launch_sha": args.launch_sha,
                                    "admission": admission, "source_root": source_root, "out": out,
                                    "input_root": input_root, "input_manifest": args.input_manifest,
                                    "input_manifest_sha256": args.input_manifest_sha256, "input_manifest_data": manifest,
                                    "seed": 0, "numerical_threads": thread_env,
                                    "dtype": "float64", "source_published_before_effects": True,
                                    "prior_cost": {"historical_static_calls": 128288, "B01": "complete bill retained in NOTES; sunk, not new/free labels"},
                                    "argv": sys.argv[1:] if argv is None else argv})
        import numpy as np
        from experiments.candidates.coupled_host_joint_skills_stage1.planner import assign_targets
        from experiments.candidates.typed_joint_skill_decision.b02 import model
        records = [json.loads(p.read_bytes()) for p in paths]
        if [r["world"] for r in records] != [r["world"] for r in manifest["training_records"]]:
            raise ValueError("bound archive payload addresses mismatch")
        def training_assignment(initial, sites):
            bill.charge("matching_calls")
            result = assign_targets(initial, sites)
            bill.charge("matching_completed")
            return result
        rows = [row for record in records for row in model.archive_rows(record, training_assignment)]
        store.write("raw/fit/training-rows.json", rows)
        store.progress("fit_pending", training_rows=len(rows))
        bill.charge("fits")
        fit_started = time.perf_counter()
        fit = model.fit_once(rows)
        fit["fit_wall_seconds"] = time.perf_counter() - fit_started
        bill.charge("fits_completed")
        if not fit["numerically_valid"]:
            import math
            def preserve_nonfinite(value):
                if isinstance(value, dict):
                    return {k: preserve_nonfinite(v) for k, v in value.items()}
                if isinstance(value, list):
                    return [preserve_nonfinite(v) for v in value]
                return repr(value) if isinstance(value, float) and not math.isfinite(value) else value
            store.write("raw/fit/refused-solution.json", preserve_nonfinite(fit))
            raise ValueError("saved ridge solution fails the declared residual/finite tolerance; no deployment or retry")
        fixed_means = [float(np.mean([r["executable_final_reward"] for r in rows if r["rank"] == rank])) for rank in range(3)]
        fixed_rank = max(range(3), key=lambda r: (fixed_means[r], -r))
        if fixed_rank != 0:
            raise AssertionError("complete fallback-adjusted B must alias G")
        fit.update(fixed_rank_means=fixed_means, fixed_rank=fixed_rank,
                   launch_sha=args.launch_sha, archive_manifest_sha256=args.input_manifest_sha256)
        fit["training_decisions"] = []
        for offset in range(0, 192, 3):
            group = rows[offset:offset + 3]
            gains = fit["training_predictions"][offset:offset + 3]
            rank = model.choose_rank([r["initial_candidate"]["contract_reward"] for r in group], gains)
            fit["training_decisions"].append({"world": group[0]["world"], "initial_rank": 0, "final_rank": rank,
                                               "predicted_gains": gains, "selected_fallback": group[rank]["fallback"],
                                               "initial_executable_reward": group[0]["executable_final_reward"],
                                               "final_executable_reward": group[rank]["executable_final_reward"],
                                               "regret": max(r["executable_final_reward"] for r in group) - group[rank]["executable_final_reward"]})
        model_path = store.write("raw/fit/model.json", fit)
        context = {"parent_pid": os.getpid(), "admission": admission, "launch_sha": args.launch_sha,
                   "source_root": str(source_root), "out": str(out), "model_path": str(model_path),
                   "model_sha256": e.sha(model_path)}
        costs = []
        for index, world in enumerate(manifest["test_worlds"]):
            order = ["G", "L", "P"]
            order = order[index % 3:] + order[:index % 3]
            for arm in order:
                costs.append(spawn_case(ctx, context, bill, store, world, arm))
                store.progress("main", completed_cases=len(costs), total_cases=192, world=world, arm=arm)
        store.write("raw/main/case-costs.json", costs)
        from experiments.candidates.typed_joint_skill_decision.b02.native import Native
        from experiments.candidates.typed_joint_skill_decision.b02.reader import complete_reader
        # Refresh input/output hashes before consuming the same accepted bytes in the reader.
        e.verify_inputs(manifest, source_root, input_root)
        with Native(bill) as native:
            summary = complete_reader(store, native, records, rows, fit)
        counts = bill.snapshot()["counters"]
        expected = {"fits": 1, "fits_completed": 1, "main_episodes": 192, "audit_episodes": 12,
                    "native_steps": 102000, "native_completed": 102000, "spawn_attempts": 192,
                    "spawn_completed": 192, "reader_reference_searches": 64, "reader_state_checks": 96192}
        if any(counts[k] != v for k, v in expected.items()) or counts["static_calls"] != counts["static_completed"]:
            raise AssertionError(f"complete exact-work counts differ: {counts}")
        bill.check()
        summary.update(schema=1, status="complete", direction="typed_joint_skill_decision", launch_sha=args.launch_sha,
                       input_manifest_sha256=args.input_manifest_sha256, bill=bill.snapshot(), interpreter={"executable": sys.executable,
                       "python": platform.python_version(), "numpy": np.__version__, "host": platform.node()},
                       numerical_threads=thread_env, tolerances=model.TOLERANCES)
        store.write("summary.json", summary)
        store.progress("complete", completed_cases=192, completed_reader_worlds=64)
        return 0
    except BaseException as exc:
        store.failure(exc)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
