"""Checkpoint CPU accounting and dispatch stop, never an outcome-dependent stop."""
from __future__ import annotations
from concurrent.futures import FIRST_COMPLETED, wait
import os
from pathlib import Path
import resource
import time
from .contract import CPU_REVIEW_SECONDS, write_json


class BudgetStop(RuntimeError):
    pass


def check_worker_stop(out):
    if (Path(out)/"cpu-review-stop.json").exists():
        raise BudgetStop("B10 cumulative CPU review boundary; preserve incomplete prefix")


def children_cpu():
    r=resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime+r.ru_stime


def active_descendant_cpu(root_pid, proc=Path("/proc")):
    """Linux CPU of live descendants plus their already-reaped descendants."""
    rows={}
    ticks=float(os.sysconf("SC_CLK_TCK"))
    for path in proc.iterdir():
        if not path.name.isdecimal():
            continue
        try:
            text=(path/"stat").read_text()
            fields=text[text.rfind(")")+2:].split()
            rows[int(path.name)]=(int(fields[1]),sum(int(fields[k]) for k in (11,12,13,14))/ticks)
        except (FileNotFoundError, ProcessLookupError):
            continue
    descendants={root_pid}
    while True:
        more={pid for pid,(parent,_) in rows.items() if parent in descendants}
        grown=descendants|more
        if grown==descendants:
            break
        descendants=grown
    return sum(rows[pid][1] for pid in descendants if pid!=root_pid and pid in rows),len(descendants)-1


class CpuBudget:
    def __init__(self, out, prior_cpu_seconds, *, cpu_origin, child_origin, limit=CPU_REVIEW_SECONDS):
        if not 0 <= prior_cpu_seconds < limit:
            raise ValueError("prior cost exhausts or invalidates this fixed CPU purchase")
        self.out=Path(out)
        self.prior=float(prior_cpu_seconds)
        self.cpu_origin=float(cpu_origin)
        self.child_origin=float(child_origin)
        self.limit=float(limit)
        self.stopped=False
        self.last={}
        self.maximum_seen=0.0

    def poll(self):
        # A worker may exit while /proc is being read. Repeat a moving-reap
        # sample; retain the maximum checkpoint total, disclose non-atomicity.
        stable=False
        for _ in range(3):
            before=children_cpu()
            live, processes=active_descendant_cpu(os.getpid())
            after=children_cpu()
            if before==after:
                stable=True
                break
        parent=max(0.,time.process_time()-self.cpu_origin)
        reaped=max(0.,after-self.child_origin)
        total=self.prior+parent+reaped+live
        self.maximum_seen=max(self.maximum_seen,total)
        self.last=dict(prior_cpu_seconds=self.prior,parent_cpu_seconds=parent,
            reaped_descendant_cpu_seconds=reaped,live_descendant_cpu_seconds=live,
            live_descendants=processes,checkpoint_cpu_seconds=total,
            maximum_checkpoint_cpu_seconds=self.maximum_seen,limit_cpu_seconds=self.limit,
            stable_reap_snapshot=stable,
            scope="prior declared checks/phases plus current parent and all live/reaped descendants; Linux process accounting")
        if self.maximum_seen >= self.limit and not self.stopped:
            self.stopped=True
            write_json(self.out/"cpu-review-stop.json",dict(**self.last,
                status="review-stop",performance_result=False,
                action="stop new dispatch; active workers/readers preserve at next 100-decision checkpoint"))
        return not self.stopped


def execute_budgeted(executor, jobs, workers, payload, on_result, submitted, *, worker_fn, budget):
    remaining=iter(jobs)
    pending={}
    errors=[]
    stopped=False

    def submit_one():
        nonlocal stopped
        if not budget.poll():
            stopped=True
            return False
        try:
            job=next(remaining)
        except StopIteration:
            return False
        submitted.append(job["job_key"])
        try:
            future=executor.submit(worker_fn,payload(job))
        except BaseException as error:
            row=dict(**job,status="unreconciled",error=repr(error))
            errors.append(row)
            on_result(row)
            stopped=True
            return False
        pending[future]=job
        return True

    for _ in range(min(workers,len(jobs))):
        if stopped or not submit_one():
            break
    while pending:
        if not budget.poll():
            stopped=True
        done,_=wait(tuple(pending),timeout=1.,return_when=FIRST_COMPLETED)
        for future in done:
            job=pending.pop(future)
            try:
                row=future.result()
            except BaseException as error:
                row=dict(**job,status="unreconciled",error=repr(error))
                errors.append(row)
            on_result(row)
            if row["status"] not in ("completed","partial"):
                stopped=True
        if stopped:
            for future,job in list(pending.items()):
                if future.cancel():
                    pending.pop(future)
                    on_result(dict(**job,status="cancelled",error="unstarted executor work cancelled after stop"))
        else:
            while len(pending)<workers and submit_one():
                pass
    budget.poll()
    return submitted,errors
