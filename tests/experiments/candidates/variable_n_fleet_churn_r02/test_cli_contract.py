import importlib.util
from pathlib import Path

import pytest

from experiments.candidates.variable_n_fleet_churn_r02 import kernel_gate


SCRIPT = Path(__file__).parents[4] / "scripts" / "run_vnfc_bpcr_r02_a0.py"


def load_cli():
    spec = importlib.util.spec_from_file_location("vnfc_r02_a0_cli_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_import_has_no_execution_or_filesystem_side_effect(monkeypatch):
    writes = []
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: writes.append((args, kwargs)))
    cli = load_cli()
    assert writes == []
    assert cli.A0_NAMESPACE == "temp/vnfc-r02-a0/VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"


def test_cli_accepts_exactly_zero_application_arguments():
    cli = load_cli()
    contract = cli.exact_argv_contract(())
    assert contract["application_argv"] == ()
    assert contract["terminal_outputs"] == ("A0_CONFORMANCE.json", "INCOMPLETE.json")
    for argv in (("--help",), ("--law", cli.LAW), ("--output", "elsewhere"), ("A0",)):
        with pytest.raises(cli.CliContractError):
            cli.exact_argv_contract(argv)


class Context:
    namespace = "temp/vnfc-r02-a0/VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"

    def __init__(self):
        self.pids = []

    def assert_active(self, pid):
        self.pids.append(pid)


def test_exact_route_has_one_gate_panel_artifact_path_and_fixed_law_namespace():
    cli = load_cli()
    context = Context()
    calls = []

    def bootstrap(**kwargs):
        calls.append(("bootstrap", kwargs))
        return context

    def route(**kwargs):
        calls.append(("route", kwargs))
        return {"namespace": cli.A0_NAMESPACE, "law": cli.LAW, "status": "PASS_CONFORMANT"}

    result = cli.execute_exact_route((), bootstrap=bootstrap, route=route, pid=71)
    assert result["status"] == "PASS_CONFORMANT"
    assert context.pids == [71]
    assert calls[0][0] == "bootstrap" and calls[1] == (
        "route", {"gate": context, "namespace": cli.A0_NAMESPACE, "law": cli.LAW}
    )


def test_route_refuses_missing_gate_namespace_or_terminal_identity():
    cli = load_cli()
    with pytest.raises(cli.CliContractError, match="no context"):
        cli.execute_exact_route((), bootstrap=lambda **_kwargs: None, route=lambda **_kwargs: {}, pid=1)
    wrong = Context()
    wrong.namespace = "other"
    with pytest.raises(cli.CliContractError, match="namespace drift"):
        cli.execute_exact_route((), bootstrap=lambda **_kwargs: wrong, route=lambda **_kwargs: {}, pid=1)
    for result in ({}, {"namespace": cli.A0_NAMESPACE, "law": "other", "status": "PASS_CONFORMANT"}):
        def invalid_route(**_kwargs):
            return result

        with pytest.raises(cli.CliContractError):
            cli.execute_exact_route((), bootstrap=lambda **_kwargs: Context(), route=invalid_route, pid=1)


def test_real_route_fails_closed_in_an_ordinary_interpreter(capsys):
    cli = load_cli()
    assert cli.main(()) == 2
    assert "INCOMPLETE" in capsys.readouterr().err


class FakeBootstrapBackend:
    def __init__(self, monkeypatch):
        digest = "0" * 64
        self.source = (("<PYTHON_PREFIX>/a.py", 1, digest),)
        self.resource = (("<PYTHON_PREFIX>/lib/site-packages/x.txt", 1, digest),)
        self.module = (("<SYSTEM32>/x.dll", 1, digest),)
        for stem, rows in (("SOURCE", self.source), ("RESOURCE", self.resource), ("MODULE", self.module)):
            serialized = kernel_gate.canonicalize_rows(rows)
            monkeypatch.setattr(kernel_gate, stem + "_ROWS", 1)
            monkeypatch.setattr(kernel_gate, stem + "_BYTES", len(serialized))
            monkeypatch.setattr(kernel_gate, stem + "_ROOT", __import__("hashlib").sha256(serialized).hexdigest())
        self.source_bytes = kernel_gate.canonicalize_rows(self.source)
        self.events = []
        self.runner = ("<REPO_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py", 7, "2" * 64)
        self.content = (self.runner,)
        self.content_manifest = kernel_gate.build_content_manifest(self.content, self.source, self.runner)

    def startup_observation(self):
        return {
            "dont_write_bytecode": True, "no_site": 1, "no_user_site": 1,
            "ignore_environment": 1, "isolated": 1,
            "pycache_prefix": kernel_gate.PYCACHE_PREFIX,
            "sys_path": kernel_gate.INITIAL_SYS_PATH,
            "loaded_forbidden": (), "pycache_empty_before": True,
        }

    def addaudithook(self, hook):
        self.hook = hook

    def process_id(self, _imported):
        self.events.append("os.getpid")
        return 515

    def reject_forbidden_modules(self):
        return None

    def import_module(self, name):
        self.events.append("import:" + name)
        return name

    def frozen_authority_observation(self, _imported):
        return {"anchor_rows": kernel_gate.ANCHOR_ROWS, "source_manifest_bytes": self.source_bytes,
                "record_verified_entries": 1, "resource_rows": self.resource, "module_rows": self.module,
                "content_manifest": self.content_manifest}

    def append_site_packages(self):
        self.events.append("append-site")

    def runtime_observation(self, _imported):
        return {**kernel_gate.EXPECTED_RUNTIME, "controls": {
            "device": "cpu", "dtype": "float64", "intraop_threads": 1, "interop_threads": 1,
            "deterministic_algorithms": True, "autocast": False, "amp": False, "tf32": False,
            "jit": False, "compile": False, "fused": False, "foreach": False,
            "denormal_preservation": True, "rounding": "nearest_ties_even", "fma": False,
        }}

    def probe_round(self, _imported, _round):
        return kernel_gate.EXPECTED_PROBES

    def module_snapshot(self, _imported, _round):
        return self.module

    def preprobe_source_observation(self, _imported, _frozen, _events):
        path = "C:/repo/scripts/run_vnfc_bpcr_r02_a0.py"
        return {
            "dependency_rows": self.source, "runner_row": self.runner,
            "main_module": {"name": "__main__", "file": path, "resolved_file": path,
                            "origin": path, "loader": "SourceFileLoader", "exists": True},
            "early_repo_modules": (), "early_repo_reads": (), "repo_root": "C:/repo",
        }

    def opened_resource_rows(self, _imported, _events, _frozen):
        return self.resource

    def content_observed_rows(self, _imported, _manifest):
        return self.content

    def load_gate_module(self, _imported):
        self.events.append("load-gate")
        return kernel_gate

    def absolute_allowed_read_rows(self, rows):
        result = tuple(("c:/allowed/" + str(index), size, digest) for index, (_path, size, digest) in enumerate(rows))
        self.allowed = {row[0] for row in result}
        return result

    def verify_continuous_read_identity(self, path):
        if str(path).replace("\\", "/").casefold() not in self.allowed:
            raise kernel_gate.GateError("continuous identity drift")


def test_injected_bootstrap_encodes_early_hook_exact_order_two_snapshots_and_same_pid(monkeypatch):
    cli = load_cli()
    backend = FakeBootstrapBackend(monkeypatch)
    context = cli.bootstrap_with_backend(backend, pid=919)
    assert context.assert_active(919)
    order = context.receipt["bootstrap_order"]
    assert order[:7] == (
        "verify:startup", "install:audit-hook", "reject:site-customize",
        "import:pathlib", "import:csv", "import:base64", "import:hashlib",
    )
    assert order.index("audit:reset-accumulator") < order.index("import:ctypes")
    assert order.index("probe:round-1") < order.index("snapshot:1") < order.index("probe:round-2") < order.index("snapshot:2")
    assert order.index("snapshot:2") < order.index("source-load:r02-kernel-gate-after-preprobe")
    assert order[-1] == "audit:begin-continuous-enforcement"
    assert context.receipt["preprobe_runner_row"] == backend.runner
    assert context.receipt["preprobe_python_rows"] == 2
    context.audit_hook("open", ("C:/allowed/0", "r", 0))
    context.audit_hook.identity_verifier = lambda _path: (_ for _ in ()).throw(kernel_gate.GateError("identity drift"))
    with pytest.raises(kernel_gate.GateError, match="identity drift"):
        context.audit_hook("open", ("C:/allowed/0", "r", 0))


def test_uninjected_pid_seam_uses_backend_os_getpid_after_ordered_stdlib_imports(monkeypatch):
    cli = load_cli()
    backend = FakeBootstrapBackend(monkeypatch)
    context = cli.bootstrap_with_backend(backend, pid=None)
    assert context.pid == 515
    assert backend.events[:4] == ["import:pathlib", "import:csv", "import:base64", "import:hashlib"]
    assert backend.events[4] == "os.getpid"


def test_injected_bootstrap_rejects_snapshot_and_source_tamper(monkeypatch):
    cli = load_cli()
    backend = FakeBootstrapBackend(monkeypatch)
    backend.module_snapshot = lambda _imports, round_number: backend.module if round_number == 1 else ()
    with pytest.raises(kernel_gate.GateError, match="snapshots"):
        cli.bootstrap_with_backend(backend, pid=1)

    backend = FakeBootstrapBackend(monkeypatch)
    original = backend.preprobe_source_observation
    backend.preprobe_source_observation = lambda imports, frozen, events: {
        **original(imports, frozen, events), "dependency_rows": ()
    }
    with pytest.raises(kernel_gate.GateError, match="loaded-python-source"):
        cli.bootstrap_with_backend(backend, pid=1)
