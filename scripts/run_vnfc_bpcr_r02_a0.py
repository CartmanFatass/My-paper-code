"""Single executable route for VNFC-BPCR-R02 finite-law A0.

The application accepts no arguments and has no runtime-selectable law or output path.  Importing
this module performs no probe, import-path mutation, filesystem operation, or A0 work.
"""

import sys


A0_NAMESPACE = "temp/vnfc-r02-a0/VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"
LAW = "VNFC-R02-ORC-B64-Q52-U64-V1"
PYCACHE_PREFIX = A0_NAMESPACE + "/kernel-pycache-empty"


class CliContractError(RuntimeError):
    pass


class EarlyAuditHook:
    """Audit hook installable before any import other than ``sys``."""

    def __init__(self):
        self.installed = False
        self.enforcing = False
        self.reset_done = False
        self.events = []
        self.allowed_reads = set()
        self.declared_outputs = set()
        self.created = set()
        self.verifier = None
        self.identity_verifier = None
        self._internal = False

    @staticmethod
    def _fold(value):
        return str(value).replace("\\", "/").casefold()

    @classmethod
    def _forbidden(cls, value):
        base = cls._fold(value).rsplit("/", 1)[-1]
        return base.endswith((".pth", ".pyc", ".pyo")) or base in (
            "sitecustomize", "sitecustomize.py", "usercustomize", "usercustomize.py"
        )

    def install(self, addaudithook):
        if self.installed:
            raise CliContractError("early audit hook already installed")
        addaudithook(self)
        self.installed = True

    def reset_accumulator(self):
        if not self.installed or self.enforcing or self.reset_done:
            raise CliContractError("early audit accumulator reset drift")
        self.events[:] = []
        self.reset_done = True

    def begin_enforcement(self, allowed_reads, declared_outputs, verifier=None, identity_verifier=None):
        if not self.installed or not self.reset_done or self.enforcing:
            raise CliContractError("early audit enforcement transition drift")
        self.allowed_reads = {self._fold(path) for path in allowed_reads}
        self.declared_outputs = {self._fold(path) for path in declared_outputs}
        exact = {self._fold(A0_NAMESPACE + "/A0_CONFORMANCE.json"), self._fold(A0_NAMESPACE + "/INCOMPLETE.json")}
        if self.declared_outputs != exact:
            raise CliContractError("early audit output declaration drift")
        self.verifier = verifier
        self.identity_verifier = identity_verifier
        self.enforcing = True

    def __call__(self, event, args):
        if self._internal:
            return
        if event == "open":
            record = ("open", args[0], args[1] if len(args) > 1 else "r", args[2] if len(args) > 2 else 0)
        elif event == "import":
            record = ("import", args[0] if args else "")
        elif event in ("os.rename", "os.replace", "os.remove", "os.unlink", "os.rmdir", "os.mkdir"):
            record = (event,) + tuple(args)
        else:
            return
        self.events.append(record)
        if len(record) > 1 and self._forbidden(record[1]):
            raise CliContractError("forbidden early audit path/module")
        if not self.enforcing:
            return
        if self.verifier is None:
            raise CliContractError("continuous audit verifier is absent")
        self.verifier((record,), self.allowed_reads, self.declared_outputs)
        if record[0] == "open":
            path = self._fold(record[1])
            mode = "r" if record[2] is None else str(record[2])
            flags = int(record[3] or 0)
            create = "x" in mode
            if not create and flags:
                # The verifier has already rejected nonexclusive write flags.
                create = path in self.declared_outputs and path not in self.allowed_reads
            if create:
                if path in self.created or self.created:
                    raise CliContractError("terminal output create is repeated or nonexclusive")
                self.created.add(path)
            elif path in self.allowed_reads:
                if self.identity_verifier is None:
                    raise CliContractError("continuous read identity verifier is absent")
                self._internal = True
                try:
                    self.identity_verifier(record[1])
                finally:
                    self._internal = False


def exact_argv_contract(argv):
    """The frozen application argv is the empty tuple, without even help/version switches."""
    observed = tuple(argv)
    if observed:
        raise CliContractError("VNFC R02 A0 accepts zero application arguments")
    return {
        "schema": "VNFC_R02_A0_EXECUTABLE_CLI_V1",
        "law": LAW,
        "application_argv": (),
        "namespace": A0_NAMESPACE,
        "terminal_outputs": ("A0_CONFORMANCE.json", "INCOMPLETE.json"),
        "terminal_outputs_mutually_exclusive": True,
        "terminal_outputs_create_once": True,
    }


def execute_exact_route(argv, *, bootstrap, route, pid):
    """Execute the sole A0 route with injected boundaries for non-result tests."""
    contract = exact_argv_contract(argv)
    gate = bootstrap(contract=contract, pid=pid)
    if gate is None:
        raise CliContractError("dependency gate returned no context")
    effective_pid = gate.pid if pid is None else pid
    gate.assert_active(effective_pid)
    if gate.namespace != A0_NAMESPACE:
        raise CliContractError("dependency gate namespace drift")
    result = route(gate=gate, namespace=A0_NAMESPACE, law=LAW)
    if not isinstance(result, dict) or result.get("namespace") != A0_NAMESPACE:
        raise CliContractError("A0 route returned an invalid terminal identity")
    observed_law = result.get("law", result.get("law_config"))
    if observed_law != LAW or result.get("status") not in ("PASS_CONFORMANT", "FAIL_LAW", "INCOMPLETE"):
        raise CliContractError("A0 route returned an invalid law/status")
    return result


def bootstrap_with_backend(backend, *, pid):
    """Exact same-PID preflight order driven by an injectable platform backend."""
    order = []
    startup = backend.startup_observation()
    order.append("verify:startup")
    hook = EarlyAuditHook()
    hook.install(backend.addaudithook)
    order.append("install:audit-hook")
    backend.reject_forbidden_modules()
    order.append("reject:site-customize")
    imported = {}
    for name in ("pathlib", "csv", "base64", "hashlib"):
        imported[name] = backend.import_module(name)
        order.append("import:" + name)
    if pid is None:
        pid = backend.process_id(imported)
    frozen = backend.frozen_authority_observation(imported)
    order.extend(("verify:anchors", "verify:torch-record", "verify:source-manifest"))
    hook.reset_accumulator()
    order.append("audit:reset-accumulator")
    backend.append_site_packages()
    order.append("sys.path.append:C:/Users/fires/.conda/envs/hmasd-amd-cpu/Lib/site-packages")
    for name in ("ctypes", "ctypes.wintypes", "torch"):
        imported[name] = backend.import_module(name)
        order.append("import:" + name)
    runtime = backend.runtime_observation(imported)
    order.append("verify:runtime-controls")
    probes_one = backend.probe_round(imported, 1)
    order.append("probe:round-1")
    snapshot_one = backend.module_snapshot(imported, 1)
    order.append("snapshot:1")
    probes_two = backend.probe_round(imported, 2)
    order.append("probe:round-2")
    snapshot_two = backend.module_snapshot(imported, 2)
    order.append("snapshot:2")
    source_observation = backend.preprobe_source_observation(imported, frozen, hook.events)
    resources = backend.opened_resource_rows(imported, hook.events, frozen)
    content_manifest = frozen["content_manifest"]
    content_rows = backend.content_observed_rows(imported, content_manifest)
    gate_module = backend.load_gate_module(imported)
    order.append("source-load:r02-kernel-gate-after-preprobe")
    gate_module.verify_startup(startup)
    gate_module.verify_anchor_rows(frozen["anchor_rows"])
    source_rows = gate_module.verify_source_manifest(frozen["source_manifest_bytes"])
    if int(frozen["record_verified_entries"]) <= 0:
        raise CliContractError("wheel RECORD did not verify any content-bound row")
    gate_module.verify_runtime_identity(runtime)
    gate_module.verify_probe_outputs(probes_one, probes_two)
    gate_module.verify_snapshots(snapshot_one, snapshot_two, frozen["module_rows"])
    gate_module.verify_preprobe_source_union(
        dependency_rows=source_observation["dependency_rows"],
        runner_row=source_observation["runner_row"], manifest=content_manifest,
        main_module=source_observation["main_module"],
        early_repo_modules=source_observation["early_repo_modules"],
        early_repo_reads=source_observation["early_repo_reads"],
        repo_root=source_observation["repo_root"],
    )
    gate_module.verify_rows(resources, frozen["resource_rows"], gate_module.RESOURCE_ROWS, gate_module.RESOURCE_BYTES, gate_module.RESOURCE_ROOT, "probe-resource")
    gate_module.verify_content_manifest(content_manifest, content_rows, source_rows)
    order.extend(("verify:two-snapshots", "verify:942-sources", "verify:31-resources"))
    allowed_rows = tuple(source_rows) + tuple(frozen["resource_rows"]) + tuple(frozen["module_rows"]) + tuple(content_rows)
    absolute_rows = tuple(backend.absolute_allowed_read_rows(allowed_rows))
    allowed_paths = tuple(row[0] for row in absolute_rows)
    declared_outputs = (A0_NAMESPACE + "/A0_CONFORMANCE.json", A0_NAMESPACE + "/INCOMPLETE.json")
    hook.begin_enforcement(
        allowed_paths, declared_outputs, gate_module.verify_audit_events,
        backend.verify_continuous_read_identity,
    )
    order.append("audit:begin-continuous-enforcement")
    receipt = {
        "schema": "VNFC_R02_A0_KERNEL_GATE_RECEIPT_V1",
        "law": LAW,
        "pid": int(pid),
        "source_root_sha256": gate_module.SOURCE_ROOT,
        "probe_resource_root_sha256": gate_module.RESOURCE_ROOT,
        "module_root_sha256": gate_module.MODULE_ROOT,
        "probe_output_bits": tuple(row[3] for row in gate_module.EXPECTED_PROBES),
        "snapshot_equality": True,
        "continuous_audit": True,
        "bootstrap_order": tuple(order),
        "content_manifest": dict(content_manifest),
        "preprobe_runner_row": tuple(content_manifest["preprobe_runner_row"]),
        "preprobe_python_rows": int(content_manifest["preprobe_python_rows"]),
        "preprobe_python_serialization_bytes": int(content_manifest["preprobe_python_serialization_bytes"]),
        "preprobe_python_root_sha256": str(content_manifest["preprobe_python_root_sha256"]),
        "allowed_read_rows": absolute_rows,
    }
    return gate_module.GateContext(pid, allowed_paths, hook, receipt)


class _RealDependencyBackend:
    """Windows observation backend.  It performs dependency preflight only, never A0 work."""

    python_prefix = "C:/Users/fires/.conda/envs/hmasd-amd-cpu"
    system32 = "C:/Windows/System32"
    site_packages = python_prefix + "/Lib/site-packages"
    prospective_content_manifest = None

    def __init__(self):
        self._startup = None
        self._authority = None
        self._module_handles = None
        self._continuous_rows = None
        self._continuous_imported = None

    @staticmethod
    def _fold(path):
        value = str(path).replace("\\", "/")
        if value.startswith("//?/"):
            value = value[4:]
        return value.casefold()

    def _normalize_dependency(self, path):
        value = self._fold(path)
        prefix = self.python_prefix.casefold()
        if value != prefix and not value.startswith(prefix + "/"):
            raise CliContractError("dependency source escaped frozen Python prefix")
        return "<PYTHON_PREFIX>" + value[len(prefix):]

    def _normalize_module(self, path):
        value = self._fold(path)
        for prefix, marker in ((self.python_prefix.casefold(), "<PYTHON_PREFIX>"), (self.system32.casefold(), "<SYSTEM32>")):
            if value == prefix or value.startswith(prefix + "/"):
                return marker + value[len(prefix):]
        raise CliContractError("compiled module escaped frozen roots")

    @staticmethod
    def _digest(payload, hashlib):
        return hashlib.sha256(payload).hexdigest()

    def startup_observation(self):
        forbidden = tuple(name for name in ("site", "sitecustomize", "usercustomize") if name in sys.modules)
        self._startup = {
            "dont_write_bytecode": sys.dont_write_bytecode,
            "no_site": sys.flags.no_site,
            "no_user_site": sys.flags.no_user_site,
            "ignore_environment": sys.flags.ignore_environment,
            "isolated": sys.flags.isolated,
            "pycache_prefix": str(sys.pycache_prefix).replace("\\", "/"),
            "sys_path": tuple(str(path).replace("\\", "/") for path in sys.path),
            "loaded_forbidden": forbidden,
            # Verified before dependency import by the first ordered pathlib operation below.  The
            # hook already forbids any bytecode open, and -B forbids writes in the meantime.
            "pycache_empty_before": False,
        }
        return self._startup

    @staticmethod
    def addaudithook(hook):
        sys.addaudithook(hook)

    @staticmethod
    def reject_forbidden_modules():
        forbidden = [name for name in ("site", "sitecustomize", "usercustomize") if name in sys.modules]
        if forbidden:
            raise CliContractError("site/customization module was loaded")

    @staticmethod
    def import_module(name):
        if name == "ctypes.wintypes":
            return __import__(name, fromlist=("wintypes",))
        return __import__(name)

    @staticmethod
    def process_id(_imported):
        # pathlib has imported os under the installed hook; no pre-hook os import occurs.
        return sys.modules["os"].getpid()

    @staticmethod
    def _parse_literal_tables(text):
        rows = []
        for line in text.splitlines():
            if not line.startswith("| `<") or not line.endswith("` |"):
                continue
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) != 3 or not cells[1].isdigit():
                continue
            path = cells[0][1:-1].casefold().replace("<python_prefix>", "<PYTHON_PREFIX>").replace("<system32>", "<SYSTEM32>")
            digest = cells[2][1:-1]
            if len(digest) == 64 and all(char in "0123456789abcdef" for char in digest):
                rows.append((path, int(cells[1]), digest))
        if len(rows) != 132:
            raise CliContractError("kernel authority did not expose exactly 132 literal rows")
        return tuple(rows[:20]), tuple(rows[20:51]), tuple(rows[51:])

    def frozen_authority_observation(self, imported):
        pathlib, csv, base64, hashlib = (imported[name] for name in ("pathlib", "csv", "base64", "hashlib"))
        pycache = pathlib.Path(PYCACHE_PREFIX)
        self._startup["pycache_empty_before"] = pycache.is_dir() and next(pycache.iterdir(), None) is None
        root = pathlib.Path.cwd()
        kernel_path = root / "docs/research/candidates/variable_n_fleet_churn/VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_KERNEL_BYTE_MANIFEST_20260901.md"
        source_path = root / "docs/research/candidates/variable_n_fleet_churn/VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_PYTHON_SOURCE_MANIFEST_20260901.tsv"
        kernel_text = kernel_path.read_text("utf-8")
        anchors, resources, modules = self._parse_literal_tables(kernel_text)
        observed_anchors = []
        for normalized, _size, _digest in anchors:
            if normalized.startswith("<PYTHON_PREFIX>"):
                physical = self.python_prefix + normalized[len("<PYTHON_PREFIX>"):]
            else:
                physical = self.system32 + normalized[len("<SYSTEM32>"):]
            payload = pathlib.Path(physical).read_bytes()
            observed_anchors.append((normalized, len(payload), self._digest(payload, hashlib)))
        record_path = pathlib.Path(self.site_packages) / "torch-2.7.0.dist-info/RECORD"
        record_bytes = record_path.read_bytes()
        entries = 0
        text = record_bytes.decode("utf-8", "strict")
        for row in csv.reader(text.splitlines()):
            if len(row) != 3:
                raise CliContractError("torch RECORD row is malformed")
            relative, digest_field, size_field = row
            if not digest_field:
                continue
            if not digest_field.startswith("sha256=") or not size_field.isdecimal():
                raise CliContractError("torch RECORD identity is unsupported")
            payload = (pathlib.Path(self.site_packages) / relative).read_bytes()
            digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
            if len(payload) != int(size_field) or digest != digest_field[7:]:
                raise CliContractError("torch RECORD content identity drift")
            entries += 1
        self._authority = {
            "anchor_rows": tuple(observed_anchors),
            "source_manifest_bytes": source_path.read_bytes(),
            "record_verified_entries": entries,
            "resource_rows": resources,
            "module_rows": modules,
        }
        if self.prospective_content_manifest is None:
            raise CliContractError("prospective literal R02 source/input manifest is not integrated")
        self._authority["content_manifest"] = self.prospective_content_manifest
        return self._authority

    def append_site_packages(self):
        if tuple(str(path).replace("\\", "/") for path in sys.path) != (
            self.python_prefix + "/python310.zip", self.python_prefix + "/DLLs",
            self.python_prefix + "/lib", self.python_prefix,
        ):
            raise CliContractError("sys.path drifted before manual site-packages append")
        sys.path.append(self.site_packages)

    @staticmethod
    def _processor_identifier(imported):
        ctypes, wintypes = imported["ctypes"], imported["ctypes.wintypes"]
        advapi32 = ctypes.WinDLL("advapi32.dll", use_last_error=True)
        size = wintypes.DWORD(512 * ctypes.sizeof(wintypes.WCHAR))
        buffer = ctypes.create_unicode_buffer(512)
        status = advapi32.RegGetValueW(
            wintypes.HKEY(0x80000002),
            "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0",
            "Identifier", 0x00000002, None, buffer, ctypes.byref(size),
        )
        if status != 0:
            raise CliContractError("processor Identifier registry observation failed")
        return buffer.value

    @classmethod
    def runtime_observation(cls, imported):
        torch = imported["torch"]
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(True)
        if hasattr(torch, "set_flush_denormal"):
            torch.set_flush_denormal(False)
        windows = sys.getwindowsversion()
        return {
            "python": sys.version,
            "torch": torch.__version__,
            "torch_commit": torch.version.git_version,
            "windows": "%d.%d.%d" % (windows.major, windows.minor, windows.build),
            "processor": cls._processor_identifier(imported),
            "torch_cpu_capability": torch.backends.cpu.get_cpu_capability(),
            "controls": {
                "device": "cpu", "dtype": "float64", "intraop_threads": torch.get_num_threads(),
                "interop_threads": torch.get_num_interop_threads(),
                "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                "autocast": False, "amp": False, "tf32": False, "jit": False, "compile": False,
                "fused": False, "foreach": False, "denormal_preservation": True,
                "rounding": "nearest_ties_even", "fma": False,
            },
        }

    @staticmethod
    def probe_round(imported, _round_number):
        torch = imported["torch"]
        specifications = (
            ("sigmoid_R02", "torch.ops.aten.sigmoid.default", "-0x1.0000000000000p+0", torch.ops.aten.sigmoid.default),
            ("exp_R02", "torch.ops.aten.exp.default", "-0x1.0000000000000p+0", torch.ops.aten.exp.default),
            ("log_R02", "torch.ops.aten.log.default", "0x1.0000000000000p-1", torch.ops.aten.log.default),
            ("sqrt_R02", "torch.ops.aten.sqrt.default", "0x1.0000000000000p-2", torch.ops.aten.sqrt.default),
        )
        rows = []
        for name, schema, input_bits, operation in specifications:
            tensor = torch.tensor([float.fromhex(input_bits)], dtype=torch.float64, device="cpu").contiguous()
            if tuple(tensor.shape) != (1,) or tuple(tensor.stride()) != (1,):
                raise CliContractError("probe tensor layout drift")
            rows.append((name, schema, input_bits, float(operation(tensor)[0].item()).hex()))
        return tuple(rows)

    def module_snapshot(self, imported, _round_number):
        ctypes, wintypes, hashlib = imported["ctypes"], imported["ctypes.wintypes"], imported["hashlib"]
        if self._module_handles is None:
            self._module_handles = (
                ctypes.WinDLL("kernel32.dll", use_last_error=True),
                ctypes.WinDLL("psapi.dll", use_last_error=True),
            )
        kernel32, psapi = self._module_handles
        process = kernel32.GetCurrentProcess()
        needed = wintypes.DWORD()
        capacity = 256
        while True:
            handles = (wintypes.HMODULE * capacity)()
            if not psapi.EnumProcessModules(process, handles, ctypes.sizeof(handles), ctypes.byref(needed)):
                raise CliContractError("EnumProcessModules failed")
            count = needed.value // ctypes.sizeof(wintypes.HMODULE)
            if count <= capacity:
                break
            capacity = count
        rows = []
        for handle in handles[:count]:
            buffer = ctypes.create_unicode_buffer(32768)
            if not psapi.GetModuleFileNameExW(process, handle, buffer, len(buffer)):
                raise CliContractError("GetModuleFileNameExW failed")
            physical = buffer.value
            normalized = self._normalize_module(physical)
            with open(physical, "rb") as stream:
                payload = stream.read()
            rows.append((normalized, len(payload), hashlib.sha256(payload).hexdigest()))
        if len({row[0] for row in rows}) != len(rows):
            raise CliContractError("duplicate normalized compiled module")
        return tuple(sorted(rows, key=lambda row: row[0].encode("utf-8")))

    def preprobe_source_observation(self, imported, _frozen, events):
        pathlib, hashlib = imported["pathlib"], imported["hashlib"]
        preexisting_events = tuple(events)
        dependency_rows = []
        runner_row = None
        early_repo_modules = []
        dynamic = {("torch.classes", "_classes.py"), ("torch.ops", "_ops.py")}
        repo_root = pathlib.Path.cwd().absolute()
        main_metadata = None
        for name, module in tuple(sys.modules.items()):
            path = getattr(module, "__file__", None)
            spec = getattr(module, "__spec__", None)
            loader = type(getattr(spec, "loader", getattr(module, "__loader__", None))).__name__
            if "SourcelessFileLoader" in loader:
                raise CliContractError("sourceless module loaded")
            if not path:
                continue
            physical = pathlib.Path(path)
            if not physical.exists():
                if (name, physical.name) not in dynamic or getattr(spec, "origin", None) is not None:
                    raise CliContractError("nonexistent module source is not a frozen namespace")
                continue
            folded = str(physical).casefold()
            if folded.endswith((".pyc", ".pyo")):
                raise CliContractError("bytecode module loaded")
            if not folded.endswith(".py"):
                continue
            payload = physical.read_bytes()
            absolute = physical.absolute()
            resolved = physical.resolve(strict=True)
            digest = hashlib.sha256(payload).hexdigest()
            if name == "__main__":
                normalized = "<REPO_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py"
                runner_row = (normalized, len(payload), digest)
                main_metadata = {
                    "name": "__main__", "file": str(absolute), "resolved_file": str(resolved),
                    "origin": str(absolute), "loader": loader, "exists": True,
                }
                continue
            try:
                normalized = self._normalize_dependency(str(resolved))
            except CliContractError:
                early_repo_modules.append((name, str(absolute)))
                continue
            dependency_rows.append((normalized, len(payload), digest))
        if main_metadata is None or runner_row is None:
            main_metadata = {
                "name": "__main__", "file": getattr(sys.modules.get("__main__"), "__file__", None),
                "resolved_file": "", "origin": "", "loader": "", "exists": False,
            }
            runner_row = ("<REPO_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py", 0, "0" * 64)
        early_repo_reads = []
        repo_folded = self._fold(repo_root)
        for event in preexisting_events:
            if event[0] != "open" or not isinstance(event[1], (str, bytes)):
                continue
            try:
                opened = self._fold(pathlib.Path(event[1]).resolve())
            except (OSError, ValueError):
                continue
            if opened.startswith(repo_folded + "/"):
                early_repo_reads.append(opened)
        return {
            "dependency_rows": tuple(sorted(dependency_rows, key=lambda row: row[0].encode("utf-8"))),
            "runner_row": runner_row, "main_module": main_metadata,
            "early_repo_modules": tuple(early_repo_modules),
            "early_repo_reads": tuple(early_repo_reads), "repo_root": str(repo_root),
        }

    def opened_resource_rows(self, imported, events, frozen):
        pathlib, hashlib = imported["pathlib"], imported["hashlib"]
        source_paths = set()
        module_paths = set()
        for normalized, _size, _digest in frozen["module_rows"]:
            prefix = self.python_prefix if normalized.startswith("<PYTHON_PREFIX>") else self.system32
            marker = "<PYTHON_PREFIX>" if normalized.startswith("<PYTHON_PREFIX>") else "<SYSTEM32>"
            module_paths.add(self._fold(prefix + normalized[len(marker):]))
        rows = {}
        site = self.site_packages.casefold()
        for event in tuple(events):
            if event[0] != "open" or not isinstance(event[1], (str, bytes)):
                continue
            physical = pathlib.Path(event[1]).resolve()
            folded = self._fold(physical)
            if not folded.startswith(site + "/") or folded in module_paths:
                continue
            if folded.endswith(".py"):
                source_paths.add(folded)
                continue
            if folded.endswith((".pyc", ".pyo", ".pth")):
                raise CliContractError("forbidden opened dependency path")
            if physical.is_file():
                payload = physical.read_bytes()
                normalized = self._normalize_dependency(physical)
                rows[normalized] = (normalized, len(payload), hashlib.sha256(payload).hexdigest())
        return tuple(sorted(rows.values(), key=lambda row: row[0].encode("utf-8")))

    @staticmethod
    def content_observed_rows(_imported, _manifest):
        raise CliContractError("content observations are unavailable until literal manifest integration")

    @staticmethod
    def load_gate_module(_imported):
        # Reached only after a prospective content manifest is supplied by CM.
        raise CliContractError("kernel gate source-load is blocked until content manifest integration")

    def absolute_allowed_read_rows(self, rows):
        absolute = []
        for path, size, digest in rows:
            if path.startswith("<PYTHON_PREFIX>"):
                physical = self.python_prefix + path[len("<PYTHON_PREFIX>"):]
            elif path.startswith("<SYSTEM32>"):
                physical = self.system32 + path[len("<SYSTEM32>"):]
            else:
                physical = path
            absolute.append((self._fold(physical), size, digest))
        result = tuple(absolute)
        self._continuous_rows = {row[0]: row for row in result}
        return result

    def verify_continuous_read_identity(self, path):
        if self._continuous_rows is None:
            raise CliContractError("continuous identity map is absent")
        normalized = self._fold(path)
        expected = self._continuous_rows.get(normalized)
        if expected is None:
            raise CliContractError("continuous read path is undeclared")
        hashlib = sys.modules.get("hashlib")
        if hashlib is None:
            raise CliContractError("hashlib is absent during continuous read verification")
        with open(path, "rb") as stream:
            payload = stream.read()
        observed = (normalized, len(payload), hashlib.sha256(payload).hexdigest())
        if observed != expected:
            raise CliContractError("continuous read size/hash drift")


def _real_bootstrap(*, contract, pid):
    """Run only the frozen dependency preflight and return its same-PID context."""
    del contract
    required = (
        sys.dont_write_bytecode is True,
        sys.flags.no_site == 1,
        sys.flags.no_user_site == 1,
        sys.flags.ignore_environment == 1,
        sys.flags.isolated == 1,
        str(sys.pycache_prefix).replace("\\", "/") == PYCACHE_PREFIX,
    )
    if not all(required):
        raise CliContractError("exact -I -B -S -X pycache_prefix startup was not satisfied")
    return bootstrap_with_backend(_RealDependencyBackend(), pid=pid)


def _real_route(*, gate, namespace, law):
    if law != LAW or namespace != A0_NAMESPACE:
        raise CliContractError("internal A0 route identity drift")
    gate.assert_active()
    from pathlib import Path
    from experiments.candidates.variable_n_fleet_churn_r02 import artifact

    document = artifact.execute_a0(Path(namespace), gate.receipt)
    if document.get("status") == "INCOMPLETE":
        artifact.validate_incomplete_artifact(document)
    else:
        artifact.validate_complete_artifact(document)
    return dict(document)


def main(argv=None, *, bootstrap=None, route=None, pid=None):
    argv = sys.argv[1:] if argv is None else argv
    bootstrap = _real_bootstrap if bootstrap is None else bootstrap
    route = _real_route if route is None else route
    try:
        execute_exact_route(argv, bootstrap=bootstrap, route=route, pid=pid)
    except (CliContractError, RuntimeError) as error:
        sys.stderr.write("VNFC_R02_A0_INCOMPLETE: %s\n" % error)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
