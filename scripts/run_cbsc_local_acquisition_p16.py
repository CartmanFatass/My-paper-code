#!/usr/bin/env python3
"""Prepare one pinned CBSC runtime through the prospective P16 route."""

import time

ORIGIN = time.monotonic()  # Before task imports, CLI/bootstrap, jobs and clients.

import argparse
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("out", "source", "ssh", "ssh-target", "powershell", "remote-python",
                 "remote-repo", "remote-out", "candidate", "retained", "uv", "handle",
                 "supervisor", "tmux"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--worker-origin", type=float, help=argparse.SUPPRESS)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    from experiments.candidates.capability_bound_semantic_currentness.local_acquisition_p16.local import chain
    from experiments.candidates.capability_bound_semantic_currentness.local_acquisition_p16.processes import WindowsJob, remaining

    if args.worker_origin is not None:
        return 0 if chain(args, args.worker_origin)["ready"] else 1
    # In-process one-shot deadline, not a watcher process or polling service.
    # Forced controller exit closes its sole job handle even if publication stalls.
    cutoff = threading.Timer(max(0, ORIGIN + 600 - time.monotonic()), os._exit, args=(124,))
    cutoff.daemon = True
    cutoff.start()
    result = {"ready": False, "phase": "bootstrap", "handle": args.handle,
              "command_source_sha": args.source, "seed": args.seed,
              "metadata_collected": False, "remote_acceptance": "uncertain if worker started"}
    job = None
    try:
        job = WindowsJob([sys.executable, str(Path(__file__).resolve()),
                          *(sys.argv[1:] if argv is None else argv), "--worker-origin", str(ORIGIN)])
        job.resume()
        code = job.wait(remaining(ORIGIN + 540))
        job.close()
        job = None
        worker_path = Path(args.out) / "worker_result.json"
        if worker_path.exists():
            result = json.loads(worker_path.read_text(encoding="utf-8"))
        result["local_exit_code"] = code
        if code != 0:
            result["ready"] = False
    except Exception as exc:
        worker_path = Path(args.out) / "worker_result.json"
        if worker_path.exists():
            try:
                result = json.loads(worker_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        result["ready"] = False
        result["error"] = str(exc)
    finally:
        if job is not None:
            job.close()
    result["whole_wall_seconds"] = time.monotonic() - ORIGIN
    if result["whole_wall_seconds"] > 600:
        result["ready"] = False
        result["error"] = "Complete wall bound exceeded"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "command_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    readback = json.loads(result_path.read_text(encoding="utf-8"))
    if time.monotonic() - ORIGIN > 600:
        readback["ready"] = False
        readback["error"] = "Complete publication/readback bound exceeded"
        result_path.write_text(json.dumps(readback, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(readback))
    cutoff.cancel()
    return 0 if readback["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
