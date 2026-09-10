"""Two-task CM benchmark: prepare, boundary delivery, snapshots, launch, export and judge."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import random
import secrets
import shutil
import subprocess
import sys
from uuid import uuid4

from _host import events, materials

BASE = Path(__file__).resolve().parent
COLLECTION = BASE.parents[1]
VERSION = "cm-pair-v1"
BOUNDARIES = ("located", "checked", "reviewed", "accepted")


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(workspace, *args):
    return subprocess.run(["git", "-C", str(workspace), *args], check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout.rstrip("\r\n")


def all_files(root):
    """Do not follow links or copy Git internals / scratch into evidence."""
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in sorted(dirs) if d not in (".git", "temp", "__pycache__", ".pytest_cache")
                   and not (Path(folder) / d).is_symlink()]
        for name in sorted(files):
            path = Path(folder) / name
            if path.is_symlink():
                raise ValueError(f"Linked candidate files are not supported: {path}")
            yield path


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in all_files(root)}


def choose_tasks(seed, difficulty="mixed", bank=None):
    if bank is None:
        from _host.task_bank import TASKS as bank
    rng = random.Random(seed)
    classics = sorted(k for k, v in bank.items() if v["kind"] == "classic")
    first = rng.choice(classics)
    others = sorted(k for k, v in bank.items() if v["kind"] == "non_example" and
                    (difficulty == "any" or v["difficulty"] != bank[first]["difficulty"]))
    if not others:
        raise ValueError("Task bank lacks a non-example at a different estimated difficulty")
    return [first, rng.choice(others)]


def install_task(workspace, task_id):
    from _host.task_bank import TASKS, install
    install(workspace, task_id)
    materials.write(workspace / f"tasks/{task_id}.md", TASKS[task_id]["brief"])


def task_message(state, include_brief=True):
    if state["finished"]:
        return "COMPLETE: the two-task sequence is closed. Give the user the final delivery; do not self-grade."
    task_id = state["tasks"][state["position"]]
    task = state["task_metadata"][task_id]
    cmd = [state["python"], *task["public_command"]]
    details = (f"\n{task['brief']}\n\nPublic check argv: {json.dumps(cmd, ensure_ascii=False)}\n"
               if include_brief else f"\nTask facts remain in tasks/{task_id}.md.\n")
    return f"Task {state['position'] + 1}/2: {task_id}{details}Next checkpoint: {BOUNDARIES[state['phase']]}\n"


def candidate_message(directory, state, extra="", include_brief=True):
    message = (extra + "\n\n" if extra else "") + task_message(state, include_brief)
    state["message"] = message
    workspace = Path(state["workspace"])
    materials.write(workspace / "CURRENT.md", message)
    save(directory / "state.json", state)
    return message


def prepare(args):
    from _host.task_bank import TASKS
    if args.seed is None:
        args.seed = secrets.randbits(32)
    probe = subprocess.run([args.python, "-B", "-c",
        "import json,sys,numpy,torch;print(json.dumps({'python':sys.version.split()[0],'numpy':numpy.__version__,'torch':torch.__version__}))"],
        capture_output=True, text=True, encoding="utf-8", timeout=30)
    if probe.returncode:
        raise ValueError("Selected --python must provide NumPy 1.26.3 and Torch 2.7.0+cpu: " + probe.stderr)
    dependencies = json.loads(probe.stdout)
    if dependencies["numpy"] != "1.26.3" or dependencies["torch"] != "2.7.0+cpu":
        raise ValueError(f"Task dependency versions differ from the frozen contract: {dependencies}")
    scenario = "cm_direct_review" if args.mode == "direct" else "cm_delegation_granularity"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:8]
    # --root is for an isolated installation/test fixture; it never changes production files.
    collection = Path(args.root).resolve() if args.root else COLLECTION
    # Both roots stay inside the directory opened by the existing CM session.
    # _host remains protocol-private, not an OS-level secrecy boundary.
    entry = collection / scenario / "workspace"
    directory = entry / "_host/runs" / run_id
    workspace = entry / run_id
    directory.mkdir(parents=True)
    workspace.mkdir(parents=True)
    runtime_dir = directory / "runtime"
    # Copy the small executable input bundle; later maintenance cannot alter this run.
    shutil.copytree(BASE / "_host/task_bank", runtime_dir / "_host/task_bank",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for relative in ("materials.py", "events.py", "runtime.py", "completion.py", "judge_schema.json", "pricing.json"):
        shutil.copy2(BASE / "_host" / relative, runtime_dir / "_host" / relative)
    shutil.copy2(BASE / "runner.py", runtime_dir / "runner.py")
    tasks = choose_tasks(args.seed, args.difficulty)
    state = {"id": run_id, "version": VERSION, "created": now(), "finished": None,
             "mode": args.mode, "level": args.level, "delivery": args.delivery,
             "seed": args.seed, "difficulty_policy": args.difficulty, "tasks": tasks,
             "task_metadata": {k: TASKS[k] for k in tasks}, "position": 0, "phase": 0,
             "workspace": str(workspace), "python": str(Path(args.python).resolve()),
             "runtime_dir": str(runtime_dir),
             "cm": args.cm, "implementer": args.implementer, "reviewer": args.reviewer,
             "task_minutes": args.task_minutes, "checkpoints": [], "launch": None,
             "dependencies": dependencies,
             "runtime_verification": "unmeasured", "library_cost": "unmeasured"}
    materials.install(workspace, state, BASE)
    install_task(workspace, tasks[0])
    materials.write(workspace / "notes/neighbor.md", events.NEIGHBOR_BASE)
    materials.write(workspace / "notes/team.md", "Independent documentation note.\n")
    materials.write(workspace / ".gitignore", "__pycache__/\n*.pyc\ntemp/\n.pytest_cache/\n")
    shim = ("# Candidate command entry; host implementation is outside the candidate boundary.\n"
            "import subprocess, sys\n"
            "if len(sys.argv) < 2 or sys.argv[1] not in ('next','checkpoint','status'):\n"
            "    raise SystemExit('Candidate commands: next, checkpoint, status')\n"
            f"raise SystemExit(subprocess.call([sys.executable, {str(runtime_dir / 'runner.py')!r}, "
            f"*sys.argv[1:], '--run', {str(directory)!r}]))\n")
    materials.write(workspace / "benchmark.py", shim)
    candidate_message(directory, state)
    git(workspace, "init", "-b", "main")
    git(workspace, "config", "user.name", "CM Benchmark")
    git(workspace, "config", "user.email", "cm-benchmark@example.invalid")
    git(workspace, "config", "core.autocrlf", "false")
    git(workspace, "config", "core.hooksPath", str(workspace / ".git/disabled-hooks"))
    paths = [p.relative_to(workspace).as_posix() for p in all_files(workspace)]
    git(workspace, "add", "--", *paths)
    git(workspace, "commit", "-m", "Freeze candidate task and protocol", "--", *paths)
    remote = directory / "origin.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    git(workspace, "remote", "add", "origin", str(remote))
    git(workspace, "push", "-u", "origin", "main")
    state["base_commit"] = git(workspace, "rev-parse", "HEAD")
    state["input_hashes"] = hashes(workspace)
    state["host_hashes"] = hashes(runtime_dir)
    # Host launch script is outside the candidate Git tree and has no global config side effects.
    quote = lambda x: "'" + str(x).replace("'", "''") + "'"
    materials.write(directory / "START.ps1", f"& {quote(sys.executable)} {quote(runtime_dir / 'runner.py')} launch --run {quote(directory)}\nexit $LASTEXITCODE\n")
    save(directory / "state.json", state)
    print(json.dumps({"run": str(directory), "workspace": str(workspace), "tasks": tasks,
                      "estimated_difficulty": [TASKS[t]["difficulty"] for t in tasks],
                      "start": str(directory / "START.ps1"), "models_launched": False}, ensure_ascii=False, indent=2))
    return directory


def snapshot(directory, state, boundary, note):
    workspace = Path(state["workspace"])
    index = len(state["checkpoints"])
    folder = directory / "snapshots" / f"{index:02}-{boundary}"
    if folder.exists():
        raise ValueError(f"Snapshot already exists; inspect interrupted checkpoint before retry: {folder}")
    for path in all_files(workspace):
        target = folder / "code" / path.relative_to(workspace)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    owned = [p for t in state["tasks"][:state["position"] + 1] for p in state["task_metadata"][t]["owned_paths"]]
    record = {"at": now(), "task": state["tasks"][state["position"]], "boundary": boundary,
              "note": note, "snapshot": str(folder), "head": git(workspace, "rev-parse", "HEAD"),
              "status": git(workspace, "status", "--porcelain"),
              "diff": git(workspace, "diff", "HEAD", "--"),
              "log": git(workspace, "log", "--format=%H %s", "--max-count=20"),
              "owned_uncommitted_diff": git(workspace, "diff", "HEAD", "--", *owned),
              "origin_head": git(workspace, "rev-parse", "origin/main"),
              "committed_neighbor": git(workspace, "show", "HEAD:notes/neighbor.md"),
              "hashes": hashes(folder / "code")}
    save(folder / "record.json", record)
    state["checkpoints"].append(record)


def checkpoint(args, directory, state):
    if state["finished"]:
        raise ValueError("This run is already closed")
    expected = BOUNDARIES[state["phase"]]
    if args.boundary != expected:
        raise ValueError(f"Expected {expected}, got {args.boundary}; next reprints current state")
    workspace = Path(state["workspace"])
    note = (workspace / args.note).resolve()
    if not note.is_relative_to(workspace / "work") or not note.is_file():
        raise ValueError("--note must be an existing file under this workspace's work/")
    snapshot(directory, state, expected, note.relative_to(workspace).as_posix())
    extra = events.deliver(workspace, state["position"], expected, lambda *a: git(workspace, *a))
    state["phase"] += 1
    include_brief = False
    if state["phase"] == len(BOUNDARIES):
        state["phase"] = 0
        state["position"] += 1
        if state["position"] == 2:
            state["finished"] = now()
        else:
            before = set(hashes(workspace))
            install_task(workspace, state["tasks"][state["position"]])
            added = sorted(set(hashes(workspace)) - before)
            git(workspace, "add", "--", *added)
            git(workspace, "commit", "-m", "Deliver next frozen engineering task", "--", *added)
            git(workspace, "push", "origin", "main")
            current_hashes = hashes(workspace)
            state["input_hashes"].update({p: current_hashes[p] for p in added})
            extra += "\nA second bounded task has arrived. Retain the first task's accepted behavior and continue in this CM session."
            include_brief = True
    message = candidate_message(directory, state, extra, include_brief)
    if state["finished"] and (state.get("launch") or {}).get("mode") == "existing_session":
        from _host.completion import detach
        detach(directory, state)
        message += ("\nAutomatic finalization is waiting for THIS CM turn to end, then it will export, "
                    "independently assess and measure costs. End with the actual delivery and link "
                    f"{directory / 'REPORT.md'}. Do not wait for or inspect grading in this CM session.")
    print(message)


def public_status(state):
    return {"id": state["id"], "completed_boundaries": len(state["checkpoints"]),
            "total_boundaries": 8, "finished": state["finished"],
            "expected": None if state["finished"] else BOUNDARIES[state["phase"]]}


def judge(directory, state):
    from _host import runtime
    result = runtime.judge(directory, state, BASE)
    save(directory / "judgement.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = argparse.ArgumentParser(add_help=False)
    prep.add_argument("--mode", choices=("direct", "delegation"), required=True)
    prep.add_argument("--seed", type=int, help="Omit to draw and record a random seed")
    prep.add_argument("--difficulty", choices=("mixed", "any"), default="mixed")
    prep.add_argument("--level", choices=tuple(materials.LEVELS), default="L0")
    prep.add_argument("--delivery", choices=("fresh", "reuse"), default="fresh")
    preferred_python = Path.home() / ".conda/envs/hmasd-amd-cpu/python.exe"
    prep.add_argument("--python", default=str(preferred_python) if preferred_python.is_file() else sys.executable)
    prep.add_argument("--task-minutes", type=int, default=30)
    prep.add_argument("--cm", nargs=2, default=["gpt-6-astra", "medium"], metavar=("MODEL", "EFFORT"))
    prep.add_argument("--implementer", nargs=2, default=["gpt-5.6-terra", "high"], metavar=("MODEL", "EFFORT"))
    prep.add_argument("--reviewer", nargs=2, default=["gpt-6-astra", "high"], metavar=("MODEL", "EFFORT"))
    prep.add_argument("--root", help="Alternate isolated benchmark collection directory")
    sub.add_parser("prepare", parents=[prep])
    begin_parser = sub.add_parser("begin", parents=[prep])
    begin_parser.add_argument("--session", default=os.environ.get("CODEX_THREAD_ID"), help="Existing top-level CM session; normally read from CODEX_THREAD_ID")
    for name in ("next", "checkpoint", "status", "export", "launch", "judge", "assess", "cost", "finalize"):
        command = sub.add_parser(name)
        command.add_argument("--run", required=True, help="Absolute host run directory returned by prepare")
        if name == "checkpoint":
            command.add_argument("--boundary", choices=BOUNDARIES, required=True)
            command.add_argument("--note", required=True)
        if name in ("launch", "assess"):
            command.add_argument("--codex", help="Native Codex executable or .cmd path")
        if name == "launch":
            command.add_argument("--with-assessment", action="store_true", help="After CM closure also run the separate independent model judge")
        if name == "cost":
            command.add_argument("--pricing-json", type=Path, default=BASE / "_host/pricing.json")
            command.add_argument("--script", type=Path, default=Path.home() / ".agents/skills/codex-task-cost-analysis/scripts/codex_task_cost_analysis.py")
        if name == "export":
            command.add_argument("--session", help="Actual CM root session ID when started outside launch")
            command.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    args = parser.parse_args(argv)
    if args.command in ("prepare", "begin"):
        if args.task_minutes <= 0:
            parser.error("--task-minutes must be positive")
        if args.command == "begin":
            if not args.session:
                raise ValueError("Current CM session ID is unavailable; supply --session from the actual runtime")
            with contextlib.redirect_stdout(io.StringIO()):
                directory = prepare(args)
            state = read(directory / "state.json")
            state["session_cwd"] = str(Path.cwd().resolve())
            state["launch"] = {"mode": "existing_session", "session_id": args.session, "started": now(),
                               "codex_home": os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))}
            save(directory / "state.json", state)
            materials.write(directory / "REPORT.md", "# CM benchmark\n\n当前 CM 正在执行两题；结束后自动更新评分与成本。\n")
            print(json.dumps({"run": str(directory), "workspace": state["workspace"],
                              "seed": state["seed"], "cm": "this existing session; do not spawn a CM",
                              "next": "Read the run workspace AGENTS.md, then invoke its benchmark.py next",
                              "automatic_completion": "after the final checkpoint and CM turn closure"}, ensure_ascii=False, indent=2))
        else:
            prepare(args)
        return 0
    directory = Path(args.run).resolve()
    state = read(directory / "state.json")
    frozen = Path(state["runtime_dir"]).resolve()
    if frozen != BASE:
        return subprocess.call([sys.executable, "-B", str(frozen / "runner.py"),
                                *(sys.argv[1:] if argv is None else argv)])
    if args.command == "next":
        print(state["message"])
    elif args.command == "status":
        print(json.dumps(public_status(state), ensure_ascii=False))
    elif args.command == "checkpoint":
        checkpoint(args, directory, state)
    elif args.command == "judge":
        judge(directory, state)
    elif args.command == "finalize":
        from _host.completion import finalize
        finalize(directory, state, BASE)
    else:
        from _host import runtime
        getattr(runtime, args.command)(args, directory, state, BASE)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
