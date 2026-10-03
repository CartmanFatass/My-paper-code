"""Aggregate purchase stop; cancellation never grants a replacement mission."""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, wait
import os
from pathlib import Path
import signal
import time

from experiments.candidates.uav_fleet_transmission.b10_service_assignment.budget import (
    CpuBudget, children_cpu, BudgetStop,
)
from .contract import CPU_LIMIT, WALL_LIMIT, BYTE_LIMIT, write_json

STOP_NAME = "purchase-stop.json"
STOP_GRACE_SECONDS = 60.
KILL_GRACE_SECONDS = 5.
REAP_GRACE_SECONDS = 5.


def request_stop(out, reason, **facts):
    path = Path(out)/STOP_NAME
    # Exclusive creation preserves the first failure. Parallel workers may arrive
    # here together; losing this race does not change the accepted stop reason.
    import json
    from .contract import clean
    try:
        with path.open("x") as stream:
            json.dump(clean(dict(reason=reason, **facts)), stream, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        pass


def check_stop(out):
    if (Path(out)/STOP_NAME).exists() or (Path(out)/"cpu-review-stop.json").exists():
        raise BudgetStop("B01 purchase stopped; preserve prefix without completing missing work")


def _process_identity(pid):
    try:
        value = (Path("/proc")/str(pid)/"stat").read_text()
        fields = value[value.rfind(")")+2:].split()
        return int(fields[1]), int(fields[19])
    except (FileNotFoundError, ProcessLookupError):
        return None


def _descendants(processes):
    """Capture descendants of these owned pool children, pinned by start ticks."""
    roots = {process.pid for process in processes if process.is_alive()}
    rows = {}
    for path in Path("/proc").iterdir():
        if path.name.isdecimal():
            value = _process_identity(int(path.name))
            if value is not None:
                rows[int(path.name)] = value
    owned = set(roots)
    while True:
        more = {pid for pid, (parent, _) in rows.items() if parent in owned}
        if more <= owned:
            break
        owned |= more
    return {pid: rows[pid][1] for pid in owned-roots if pid in rows}


def _signal_descendants(identities, sig):
    for pid, started in identities.items():
        current = _process_identity(pid)
        if current is None or current[1] != started:
            continue
        try:
            # pidfd pins the actual Linux process across signal dispatch. If a
            # descendant exits meanwhile, no later owner of its PID is signaled.
            descriptor = os.pidfd_open(pid)
            try:
                current = _process_identity(pid)
                if current is not None and current[1] == started:
                    signal.pidfd_send_signal(descriptor, sig)
            finally:
                os.close(descriptor)
        except ProcessLookupError:
            pass


def _live_descendants(identities):
    return [pid for pid, started in identities.items()
            if (current := _process_identity(pid)) is not None and current[1] == started]


def _escalate(processes, descendants, *, kill):
    descendants.update(_descendants(processes))
    _signal_descendants(descendants, signal.SIGKILL if kill else signal.SIGTERM)
    for process in processes:
        if process.is_alive():
            (process.kill if kill else process.terminate)()


def allocated_bytes(paths):
    seen, total = set(), 0
    for root in map(Path, paths):
        if not root.exists():
            continue
        for path in [root, *root.rglob("*")]:
            try:
                stat = path.lstat()
            except FileNotFoundError:
                continue
            key = (stat.st_dev, stat.st_ino)
            if key not in seen:
                seen.add(key)
                total += stat.st_blocks*512
    return total


class PurchaseBudget(CpuBudget):
    def __init__(self, out, prior_cpu_seconds, *, cpu_origin, child_origin,
                 wall_origin, storage_paths):
        super().__init__(out, prior_cpu_seconds, cpu_origin=cpu_origin,
                         child_origin=child_origin, limit=CPU_LIMIT)
        self.wall_origin, self.storage_paths = wall_origin, list(storage_paths)
        self.storage_sample_time = -float("inf")
        self.storage_bytes = 0

    def poll(self):
        was_stopped = self.stopped
        alive = super().poll()
        now = time.monotonic()
        if now - self.storage_sample_time >= 30:
            self.storage_bytes = allocated_bytes(self.storage_paths)
            self.storage_sample_time = now
        self.last.update(operation_wall_seconds=now-self.wall_origin,
                         allocated_bytes=self.storage_bytes,
                         wall_limit_seconds=WALL_LIMIT, allocated_byte_limit=BYTE_LIMIT,
                         storage_paths=[str(p) for p in self.storage_paths])
        if not alive and not was_stopped:
            request_stop(self.out, "aggregate CPU protective stop", **self.last)
        if not was_stopped and (now-self.wall_origin >= WALL_LIMIT or self.storage_bytes >= BYTE_LIMIT):
            request_stop(self.out, "wall/storage protective stop", **self.last)
        if (self.out/STOP_NAME).exists():
            self.stopped = True
        return not self.stopped


def execute(executor, jobs, workers, worker, payload, on_result, budget):
    """At most workers accepted tasks, immediate stop propagation, one drain."""
    remaining = iter(jobs)
    pending, submitted = {}, []
    owned_processes = getattr(executor, "_b01_owned_processes", {})
    descendants = getattr(executor, "_b01_descendants", {})
    stop_started = terminated_at = killed_at = None
    manager = getattr(executor, "_b01_pool_manager", None)
    escalation = dict(status="cooperative", affected_jobs=[], events=[])

    def capture_pool_children():
        for process in (getattr(executor, "_processes", None) or {}).values():
            owned_processes[process.pid] = process
        executor._b01_owned_processes = owned_processes

    def persist_escalation():
        try:
            write_json(budget.out/"stop-escalation.json", escalation)
        except OSError as error:
            # An output-device failure must not disable the process stop itself.
            import sys
            print("B01 stop receipt could not be saved: " + repr(error), file=sys.stderr, flush=True)

    def begin_shutdown():
        nonlocal manager
        if getattr(executor, "_b01_shutdown_started", False):
            return
        capture_pool_children()
        manager = getattr(executor, "_executor_manager_thread", None)
        executor._b01_pool_manager = manager
        descendants.update(_descendants(list(owned_processes.values())))
        executor._b01_descendants = descendants
        executor._b01_shutdown_started = True
        executor.shutdown(wait=False, cancel_futures=True)

    def submit_one():
        if not budget.poll():
            return False
        spec = next(remaining, None)
        if spec is None:
            return False
        submitted.append(spec["job_key"])
        try:
            pending[executor.submit(worker, payload(spec))] = spec
            capture_pool_children()
        except BaseException as error:
            capture_pool_children()
            request_stop(budget.out, "executor submission failed", job=spec, error=repr(error))
            on_result(dict(**spec, status="unreconciled", error=repr(error)))
            return False
        return True

    for _ in range(min(workers, len(jobs))):
        if not submit_one():
            break
    while True:
        admitted = budget.poll()
        capture_pool_children()
        now = time.monotonic()
        if not admitted:
            if stop_started is None:
                stop_started = now
                escalation["affected_jobs"] = [spec["job_key"] for spec in pending.values()]
                # Begin pool shutdown even if all futures already resolved:
                # a worker initializer/exit or its manager can still be stuck.
                begin_shutdown()
                persist_escalation()
            processes = list(owned_processes.values())
            if terminated_at is None and now-stop_started >= STOP_GRACE_SECONDS:
                _escalate(processes, descendants, kill=False)
                terminated_at = now
                escalation.update(status="terminated", owned_worker_pids=[p.pid for p in processes],
                                  descendant_identities=descendants)
                escalation["events"].append(dict(action="SIGTERM", after_stop_seconds=now-stop_started))
                persist_escalation()
            elif terminated_at is not None and killed_at is None and now-terminated_at >= KILL_GRACE_SECONDS:
                _escalate(processes, descendants, kill=True)
                killed_at = now
                escalation["status"] = "killed"
                escalation["events"].append(dict(action="SIGKILL", after_stop_seconds=now-stop_started))
                persist_escalation()
            elif killed_at is not None and now-killed_at >= REAP_GRACE_SECONDS:
                alive = [p.pid for p in processes if p.is_alive()]
                live_descendants = _live_descendants(descendants)
                manager_alive = manager is not None and manager.is_alive()
                unresolved = bool(alive or live_descendants or manager_alive or pending)
                escalation.update(status="unreconciled-after-kill" if unresolved else "reaped",
                                  unreaped_worker_pids=alive, live_descendant_pids=live_descendants,
                                  pool_manager_alive=manager_alive)
                # Even if the process is gone, a broken pool manager may leave a
                # Future pending. Do not hang at its implicit atexit join.
                executor._b01_nonblocking_shutdown = unresolved
                for future, spec in list(pending.items()):
                    pending.pop(future)
                    on_result(dict(**spec, status="terminated_unreconciled",
                                   error="bounded stop escalation; retain last saved prefix, no replacement"))
                persist_escalation()
                break
        if not pending:
            # Normal shutdown is also observed: continue normal budget polling,
            # without imposing a new time gate on a successful phase.
            begin_shutdown()
        draining = getattr(executor, "_b01_shutdown_started", False) and (
            any(p.is_alive() for p in owned_processes.values()) or _live_descendants(descendants)
            or (manager is not None and manager.is_alive()))
        if not pending and not draining:
            break
        done, _ = wait(tuple(pending), timeout=1., return_when=FIRST_COMPLETED)
        if not pending:
            time.sleep(.1)
        for future in done:
            spec = pending.pop(future)
            try:
                row = future.result()
            except BaseException as error:
                row = dict(**spec, status="unreconciled", error=repr(error))
            if row["status"] != "completed":
                request_stop(budget.out, "worker/reader failed", job=spec, result=row)
            on_result(row)
        if not budget.poll():
            for future, spec in list(pending.items()):
                if future.cancel():
                    del pending[future]
                    on_result(dict(**spec, status="cancelled"))
        else:
            while len(pending) < workers and submit_one():
                pass
    budget.poll()
    if getattr(executor, "_b01_shutdown_started", False) and not getattr(executor, "_b01_nonblocking_shutdown", False):
        for process in owned_processes.values():
            process.join(timeout=0.)
        if stop_started is not None:
            escalation.update(status="reaped", unreaped_worker_pids=[], live_descendant_pids=[])
            persist_escalation()
    return submitted
