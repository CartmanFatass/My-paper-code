"""Lazy frozen scientific adapters bound to the admitted B07 complete investment."""
from __future__ import annotations
import argparse
import contextlib
import ctypes
import json
import os
import signal
from pathlib import Path
import sys
import traceback
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import contract as c
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import evidence as e
from experiments.candidates.typed_joint_skill_decision.b06_bank_consumer import billing


def parent_death(expected):
    """Kill the current child if its bound parent dies; close the setup race."""
    if sys.platform != "linux":
        raise RuntimeError("Linux parent-death binding required for this consumer")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_PDEATHSIG failed")
    if os.getppid() != expected["pid"] or c.process_identity(os.getppid()) != expected:
        raise RuntimeError("parent died or identity changed during death-signal setup")


def checked_context(request):
    parent = request["parent"]
    if (parent["pid"] != os.getppid() or parent["admission"]["child_pid"] != os.getppid()
            or parent["admission"]["direction"] != c.DIRECTION
            or parent["admission"]["sha"] != parent["launch_sha"]
            or Path(parent["source_root"]).resolve() != ROOT):
        raise RuntimeError("bound admitted live parent/source identity required")
    if parent["identity"]["pid"] != parent["pid"]:
        raise RuntimeError("parent PID/identity binding mismatch")
    parent_death(parent["identity"])  # Before scientific imports and long fit/reader stages.
    launch = json.loads((Path(parent["out"]) / "launch-manifest.json").read_bytes())
    if launch["sha"] != parent["launch_sha"] or launch["command_sha256"] != parent["admission"]["command_sha256"]:
        raise RuntimeError("child launcher/source identity mismatch")
    c.scientific_binding(parent["source_binding"], ROOT)
    c.selected_investment(parent["investment"])
    if request["job"]["stage"] == "cold" and any(k in request for k in ("bank", "fresh", "endpoints", "commitments", "inherited_files", "receipt", "labels")):
        raise ValueError("cold request must contain only legal world/constants/checkpoint and effect accounting")
    job=request['job'];expected=next((j for j in c.jobs() if j['id']==job['id']),None)
    if expected is None:raise ValueError('undeclared complete-package job')
    if expected['stage']=='fit':expected['new_stream']=job['id'] in ('fit-R1000s0','fit-R4000s1')
    if job!=expected:raise ValueError('original complete-package job fields changed')
    fields={'parent','job','original_input','prior_parent_cpu_seconds'}
    fields|={'fit':{'bank','initial_hashes'},'endpoint':{'bank','assets','final_seal','inherited_files'},
             'cold':{'checkpoint_path','checkpoint_sha256'},'reader':{'bank','assets','cases','inherited_files'}}[job['stage']]
    if set(request)!=fields:raise ValueError('exact legal stage request; no hidden bank/label/receipt payload')
    # Input path/digest is an identity, not a label-bearing bank or receipt payload.
    # Recheck compact proof on every actual exec, with no producer or reader raw replay.
    binding=c.bound_json(parent['consumer_input_path'],parent['consumer_input_sha256'])
    c.executable_binding(binding,ROOT)
    c.scientific_binding(binding,ROOT)
    limits=c.selected_investment(binding['investment'])
    if binding['investment']!=parent['investment'] or limits!=parent['deployment']['limits']:
        raise ValueError('child selected investment/input differs from admitted parent')
    from experiments.candidates.typed_joint_skill_decision.b07_fixed_bank import contract as fixed,read
    proof=read.receipt(binding['bank']['reader'],ROOT)
    producer=fixed.producer({**proof['input']['producer'],'root':binding['bank']['producer_root']},verify_payload=False)
    disk=c.disk_scope(binding,ROOT,parent['out'],producer['root'])
    if parent['deployment']['disk_roots']!=disk['roots']:raise ValueError('child actual deployed disk scope differs from parent')
    stage=request['job']['stage']
    if stage not in ('fit','endpoint','cold','reader'):raise ValueError('unknown admitted stage')
    if stage!='cold':
        bank=request['bank']
        expected={k:v for k,v in producer['files'].items() if stage!='fit' or k.startswith('raw/bank/train/')}
        if (bank['files']!=expected or bank['root']!=producer['root']
            or bank['producer_source_sha']!=fixed.PRODUCER_SHA or bank['producer_input_sha256']!=fixed.PRODUCER_INPUT
            or bank['manifest_sha256']!=fixed.PRODUCER_MANIFEST or bank['certification']['reader']!=binding['bank']['reader']):
            raise ValueError('actual child train/full bank proof identity mismatch')
    original=c.scientific_binding(binding,ROOT)
    if request['original_input']!=original:raise ValueError('child scientific input bytes changed')
    return proof



class Wire:
    def __init__(self, read_fd, write_fd):
        self.reader = os.fdopen(read_fd, "rb")
        self.writer = os.fdopen(write_fd, "wb", buffering=0)
        self.complete = None
        self.failed = None

    def send(self, value):
        self.writer.write(c.encoded(value))
        if value["kind"] == "complete":
            self.complete = value
        elif value["kind"] == "failed":
            self.failed = value

    def recv(self):
        line = self.reader.readline(65537)
        if not line or len(line) > 65536:
            raise RuntimeError("parent handshake missing/oversized")
        return json.loads(line)

    def close(self):
        # Original case_main closes its connection; process exit closes descriptors.
        self.writer.flush()


@contextlib.contextmanager
def raw_meter(bill):
    from experiments.candidates.coupled_host_joint_skills_stage1 import planner
    original = planner.build_candidates
    def counted(*args, **kwargs):
        bill.charge("raw_constructions")
        result = original(*args, **kwargs)
        bill.charge("raw_completed")
        return result
    planner.build_candidates = counted
    try:
        yield
    finally:
        planner.build_candidates = original


def bank_view(binding, split):
    from experiments.candidates.typed_joint_skill_decision.b04.bank import Bank
    files = {name: value for name, value in binding["files"].items() if name.startswith("raw/bank/" + split + "/")}
    return Bank(Path(binding["root"]), files, split, binding["producer_source_sha"], binding["producer_input_sha256"])


def scientific_stage(request, store, wire):
    # Called only after checked_context; imports/initializers are not preparation checks.
    job, parent = request["job"], request["parent"]
    if job["stage"] == "cold":
        # Keep original case_main legal context and complete selection→permission→H500 body.
        from experiments.candidates.typed_joint_skill_decision.b04.run import case_main
        legal = {"parent_pid": parent["pid"], "admission": parent["admission"],
                 "launch_sha": store.launch_sha, "input_sha256": store.input_sha256,
                 "source_root": parent["source_root"], "out": str(store.root),
                 "runtime": store.input_manifest["runtime"],
                 "checkpoint_path": request["checkpoint_path"], "checkpoint_sha256": request["checkpoint_sha256"],
                 "prior_parent_cpu_seconds": request["prior_parent_cpu_seconds"]}
        case_main(wire, legal, store.bill, job["world"], job["arm"])
        if wire.failed is not None or wire.complete is None:
            raise RuntimeError("first cold child failure; no retry: " + str(wire.failed))
        for name in wire.complete["paths"]:
            store.register(name)
        return wire.complete
    from experiments.candidates.typed_joint_skill_decision.b04 import contract as oldc
    from experiments.candidates.typed_joint_skill_decision.b04 import bank, training, online, reader
    job, parent = request["job"], request["parent"]
    oldc.configure(cuda=False, expected=store.input_manifest["runtime"])
    if job["stage"] == "fit":
        train = bank_view(request["bank"], "train")
        view = bank.TrainingBank(train)  # Full16000 load once per each independent fit.
        initials = {int(k): value for k, value in request["initial_hashes"].items()}
        asset = training.fit_once(store, view, job["fit"], initials, engineering=job["engineering"])
        store.write("assets/" + job["fit"]["id"] + ".json", asset)
        return {"asset": asset, "initial_hashes": initials}
    if job["stage"] == "endpoint":
        from .commitment import make
        import numpy as np
        if c.sha(c.relative(store.root, request["final_seal"]["path"])) != request["final_seal"]["sha256"]:
            raise ValueError("six final asset seal changed")
        assets = request["assets"]
        if [asset["fit"] for asset in assets] != list(c.FITS):
            raise ValueError("all six original final assets must precede fresh access")
        for asset in assets:
            c.verify(store.root, asset["path"], store.files[asset["path"]])
        fresh = bank_view(request["bank"], "fresh")
        choices = {}
        for asset in assets:
            with store.bill.gpu():
                oldc.configure(cuda=True, expected=store.input_manifest["runtime"])
                network = online.checkpoint_model(c.relative(store.root, asset["path"]), asset["sha256"],
                    asset["fit"], store.launch_sha, store.input_sha256)
                relative = training.endpoint(store, network, fresh, asset["fit"], "fresh")
                del network
                import torch
                torch.cuda.empty_cache()
            with np.load(c.relative(store.root, relative), allow_pickle=False) as z:
                choices[asset["fit"]["id"]] = json.loads(str(z["records"]))
        for offset, world in enumerate(range(109420000, 109420128)):
            record = fresh.load(world)
            local = {fit_id: rows[offset]["choice"] for fit_id, rows in choices.items()}
            if any(rows[offset]["world"] != world for rows in choices.values()):
                raise ValueError("GPU endpoint commitment world address")
            store.write("commitments/" + str(world) + ".json", make(record, bank.features(record), local))
        return {"fresh_assets": ["raw/endpoints/" + fit["id"] + "/fresh.npz" for fit in c.FITS]}
    if job["stage"] == "reader":
        diagnostics = reader.e.Diagnostics(store)
        try:
            train = bank_view(request["bank"], "train")
            fresh = bank_view(request["bank"], "fresh")
            view = bank.TrainingBank(train)  # Seventh original full16000 load, never optimized.
            cases = {(row["world"], row["arm"]): row for row in request["cases"]}
            from .reader import complete
            summary = complete(store, train, view, fresh, request["assets"], cases, diagnostics)
            return {"summary": summary, "diagnostics": {"path": diagnostics.relative, "count": len(diagnostics)}}
        finally:
            diagnostics.close()
    raise ValueError("undeclared stage")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--read-fd", required=True, type=int)
    parser.add_argument("--write-fd", required=True, type=int)
    args = parser.parse_args(argv)
    request = c.bound_json(args.request, args.request_sha256)
    checked_context(request)  # Every exec rechecks actual input/source/compact witnessed validation.
    c.threads()
    shared = billing.Shared(request["parent"]["counter_path"])
    bill = billing.Bill(shared, request["parent"]["deployment"], child=True,
                        prior_parent_cpu_seconds=request["prior_parent_cpu_seconds"])
    wire = Wire(args.read_fd, args.write_fd)
    store = e.ChildStore(request["parent"]["out"], bill, request["job"], request.get("inherited_files"))
    store.launch_sha = request["parent"]["launch_sha"]
    store.input_sha256 = c.SCIENCE_INPUT
    store.input_manifest = request["original_input"]
    outcome = None
    try:
        if request["job"]["stage"] in ("cold", "reader"):
            with raw_meter(bill):
                outcome = scientific_stage(request, store, wire)
        else:
            outcome = scientific_stage(request, store, wire)
        store.write("children/" + request["job"]["id"] + "/outcome.json", outcome)
        store.finish()
        return 0
    except BaseException as exc:
        # Failure captures only partial bytes/counters; no repair or hidden replay.
        e.durable(c.relative(store.root, "children/" + request["job"]["id"] + "/failure.json"),
                  c.encoded({"type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(),
                             "bill": bill.snapshot(), "retry": False}))
        raise
    finally:
        wire.close()
        shared.close()


if __name__ == "__main__":
    raise SystemExit(main())
