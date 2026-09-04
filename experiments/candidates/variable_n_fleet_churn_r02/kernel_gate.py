"""Prospective dependency/startup gate for VNFC R02 A0.

The expected identities in this module are frozen inputs.  Observations are accepted only
through explicit function arguments so the verifier can be tested without probing the A0 host.
Importing this module installs no hook, imports no dependency, and performs no filesystem I/O.
"""

import sys


LAW = "VNFC-R02-ORC-B64-Q52-U64-V1"
A0_NAMESPACE = "temp/vnfc-r02-a0/VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"
PYTHON_PREFIX = "C:/Users/fires/.conda/envs/hmasd-amd-cpu"
SYSTEM32 = "C:/Windows/System32"
SITE_PACKAGES = PYTHON_PREFIX + "/Lib/site-packages"
PYCACHE_PREFIX = A0_NAMESPACE + "/kernel-pycache-empty"
SOURCE_MANIFEST = (
    "docs/research/candidates/variable_n_fleet_churn/"
    "VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_PYTHON_SOURCE_MANIFEST_20260901.tsv"
)
KERNEL_MANIFEST = (
    "docs/research/candidates/variable_n_fleet_churn/"
    "VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_KERNEL_BYTE_MANIFEST_20260901.md"
)
INITIAL_SYS_PATH = (
    PYTHON_PREFIX + "/python310.zip",
    PYTHON_PREFIX + "/DLLs",
    PYTHON_PREFIX + "/lib",
    PYTHON_PREFIX,
)
OUTPUT_FILENAMES = ("A0_CONFORMANCE.json", "INCOMPLETE.json")
RUNNER_RELATIVE_PATH = "scripts/run_vnfc_bpcr_r02_a0.py"

SOURCE_ROWS = 942
SOURCE_BYTES = 122000
SOURCE_ROOT = "56de49297250a6d2d8a9ac1754862df5926b1b5a5a2612545ebc328027d23b53"
RESOURCE_ROWS = 31
RESOURCE_BYTES = 4450
RESOURCE_ROOT = "60f77b5ad27140489a117bd5ecd179c07689115e5a6ffcfb6fb675fc18cbd1c3"
MODULE_ROWS = 81
MODULE_BYTES = 9220
MODULE_ROOT = "62b2c60f19e912f4deaf3511057eb4ca4544a87083841e190811a9442d3e09b0"

EXPECTED_RUNTIME = {
    "python": "3.10.20 | packaged by Anaconda, Inc. | (main, Jun 11 2026, 15:13:20) [MSC v.1942 64 bit (AMD64)]",
    "torch": "2.7.0+cpu",
    "torch_commit": "134179474539648ba7dee1317959529fbd0e7f89",
    "windows": "10.0.26200",
    "processor": "AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD",
    "torch_cpu_capability": "AVX512",
}
EXPECTED_PROBES = (
    ("sigmoid_R02", "torch.ops.aten.sigmoid.default", "-0x1.0000000000000p+0", "0x1.136561454ba86p-2"),
    ("exp_R02", "torch.ops.aten.exp.default", "-0x1.0000000000000p+0", "0x1.78b56362cef38p-2"),
    ("log_R02", "torch.ops.aten.log.default", "0x1.0000000000000p-1", "-0x1.62e42fefa39efp-1"),
    ("sqrt_R02", "torch.ops.aten.sqrt.default", "0x1.0000000000000p-2", "0x1.0000000000000p-1"),
)
ANCHOR_ROWS = (
    ("<PYTHON_PREFIX>/lib/site-packages/torch-2.7.0.dist-info/record", 1308883, "ca4a2a0bc461be8bdd7f842008fe24ff22900fb0289aa36f14fa884ca6f6938a"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch-2.7.0.dist-info/metadata", 29546, "d8ea5f11979b3df2ee47c21a0f3e3a417e633203e633b9fda3606286dc1a3085"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/version.py", 279, "f5bb59ed21e17fc2f4cbc704cc3ca9dfd8590167d3e391a762ef4ec5420e6c85"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/__init__.py", 103670, "9e46616b9d27c3553ae7587381510cc5a42e8b6fa1c37694c7dc9ea829b11c9b"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/_ops.py", 58298, "30592cf51208b305a1c75390eefc6a5aca2c9380fdf10bf3a62cab2eff013afd"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/_c.cp310-win_amd64.pyd", 10752, "02b73340cd80f12ebc84f81766dcae06a690ef77bc503e31043f92457f48c9cd"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/lib/c10.dll", 1011712, "2bb3f205434570bcbee9487feca86cecb43d47c600a1b2f7455f7f21ff3ec02e"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/lib/libiomp5md.dll", 1602400, "a9c9ddf4bb1477645120b481a14a9bcb02b8da6eece12032376e33a1ba96d2ea"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch.dll", 9728, "a2a091f1708b8b0cce40026da0b8c7473959aa2a448607fd8c04f752f93cf01d"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch_cpu.dll", 252660224, "777041be8acb72dbe800911da82f7bb023cc96671efbd527383a0a061d5c1f5c"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch_global_deps.dll", 9728, "4811387fcf95a7d7d9d2e05b78acb807a3ad7c0eeb513d56a210acc88dcc2c82"),
    ("<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch_python.dll", 16867328, "8949c102432e38af6a6850445c191f81d57b170b1b999f9d1b6ab117ccd64b9a"),
    ("<PYTHON_PREFIX>/python.exe", 105288, "7075cb605dd9d7596074b438b2640c7db0a33c436f0c7046a38c211ab257ad3b"),
    ("<PYTHON_PREFIX>/python3.dll", 66376, "b315d9553d61e5c4b024ec681c934ca3744d54b344629c19e00bb07e64373eaa"),
    ("<PYTHON_PREFIX>/python310.dll", 4917576, "459af11741f27ecd7069fd16d75b48ea79189bd57884f1794d04ff8eb2cc779c"),
    ("<PYTHON_PREFIX>/vcruntime140.dll", 124496, "0205071c36c17f1efbd70178c852cb7d49985c484202752b8704b7ac6b184e60"),
    ("<PYTHON_PREFIX>/vcruntime140_1.dll", 49744, "963e45edd064545962e216c12d68071ced94dc8e11862a18f07f14eb2690a57c"),
    ("<PYTHON_PREFIX>/msvcp140.dll", 557648, "8f141b4454fa78db34bc1f28c571b4da0e00cd2c43f7ad0e282f313036826aae"),
    ("<SYSTEM32>/ucrtbase.dll", 1377496, "5e7709a6b71bb818260b6f05c5bb3b6ca0c3ca9bc2f58c6242c1cd9d826d0079"),
    ("<SYSTEM32>/msvcp_win.dll", 642016, "940a41d9d78c2d2d0ece8d8e4735630735f57ffb95466e350dae3535b40a698a"),
)


class GateError(RuntimeError):
    """An incomplete-attempt condition at the dependency/startup boundary."""


def _fail(message):
    raise GateError(message)


def _is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _forbidden_name(value):
    folded = str(value).replace("\\", "/").casefold()
    base = folded.rsplit("/", 1)[-1]
    return (
        base.endswith((".pth", ".pyc", ".pyo"))
        or base in ("sitecustomize", "sitecustomize.py", "usercustomize", "usercustomize.py")
    )


def parse_tsv_manifest(data):
    """Parse the exact UTF-8/no-BOM/no-header canonical row serialization."""
    if not isinstance(data, (bytes, bytearray)):
        _fail("manifest must be bytes")
    raw = bytes(data)
    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n") or b"\r" in raw:
        _fail("manifest is not exact UTF-8 LF serialization")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise GateError("manifest is not UTF-8") from error
    rows = []
    seen = set()
    for number, line in enumerate(text[:-1].split("\n"), 1):
        fields = line.split("\t")
        if len(fields) != 3:
            _fail("manifest row %d does not have three fields" % number)
        path, size_text, digest = fields
        if not path or path in seen or _forbidden_name(path):
            _fail("invalid or duplicate manifest path at row %d" % number)
        if not size_text.isascii() or not size_text.isdecimal() or (size_text != "0" and size_text.startswith("0")):
            _fail("noncanonical size at row %d" % number)
        if not _is_sha256(digest):
            _fail("invalid digest at row %d" % number)
        seen.add(path)
        rows.append((path, int(size_text), digest))
    if tuple(rows) != tuple(sorted(rows, key=lambda row: row[0].encode("utf-8"))):
        _fail("manifest rows are not in unsigned UTF-8 order")
    return tuple(rows)


def canonicalize_rows(rows):
    normalized = tuple((str(path), int(size), str(digest)) for path, size, digest in rows)
    if len({path for path, _size, _digest in normalized}) != len(normalized):
        _fail("duplicate normalized path")
    normalized = tuple(sorted(normalized, key=lambda row: row[0].encode("utf-8")))
    for path, size, digest in normalized:
        if not path or size < 0 or not _is_sha256(digest) or _forbidden_name(path):
            _fail("invalid canonical row")
    return "".join("%s\t%d\t%s\n" % row for row in normalized).encode("utf-8")


def verify_rows(observed, expected, row_count, serialization_bytes, root_sha256, label):
    """Require exact row-wise equality and all three redundant frozen aggregate checks."""
    hashlib = __import__("hashlib")
    observed_rows = tuple(sorted(tuple(row) for row in observed))
    expected_rows = tuple(sorted(tuple(row) for row in expected))
    if observed_rows != expected_rows:
        _fail("%s row-set mismatch" % label)
    serialized = canonicalize_rows(observed_rows)
    if len(observed_rows) != row_count:
        _fail("%s row-count mismatch" % label)
    if len(serialized) != serialization_bytes:
        _fail("%s serialization-size mismatch" % label)
    if hashlib.sha256(serialized).hexdigest() != root_sha256:
        _fail("%s root mismatch" % label)
    return observed_rows


def verify_source_manifest(data):
    rows = parse_tsv_manifest(data)
    return verify_rows(rows, rows, SOURCE_ROWS, SOURCE_BYTES, SOURCE_ROOT, "python-source")


def parse_frozen_markdown_tables(text):
    """Parse only literal fenced table rows from the frozen kernel authority document."""
    if not isinstance(text, str):
        _fail("kernel manifest text required")
    rows = []
    for line in text.splitlines():
        if not line.startswith("| `<") or not line.endswith("` |"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 3 or not (cells[0].startswith("`") and cells[0].endswith("`")):
            continue
        path = cells[0][1:-1].casefold().replace("<python_prefix>", "<PYTHON_PREFIX>").replace("<system32>", "<SYSTEM32>")
        digest = cells[2][1:-1] if cells[2].startswith("`") and cells[2].endswith("`") else ""
        if cells[1].isdigit() and _is_sha256(digest):
            rows.append((path, int(cells[1]), digest))
    if len(rows) != 132:
        _fail("frozen kernel manifest must contain exactly 132 literal rows")
    return tuple(rows[:20]), tuple(rows[20:51]), tuple(rows[51:132])


def normalize_dependency_path(path, python_prefix=PYTHON_PREFIX):
    value = str(path).replace("\\", "/")
    if value.startswith("//?/"):
        value = value[4:]
    value = value.casefold()
    prefix = python_prefix.replace("\\", "/").rstrip("/").casefold()
    if value != prefix and not value.startswith(prefix + "/"):
        _fail("dependency path is outside frozen Python prefix")
    normalized = "<PYTHON_PREFIX>" + value[len(prefix):]
    if _forbidden_name(normalized):
        _fail("forbidden dependency path")
    return normalized


def normalize_module_path(path, python_prefix=PYTHON_PREFIX, system32=SYSTEM32):
    value = str(path).replace("\\", "/")
    if value.startswith("//?/"):
        value = value[4:]
    value = value.casefold()
    roots = (
        (python_prefix.replace("\\", "/").rstrip("/").casefold(), "<PYTHON_PREFIX>"),
        (system32.replace("\\", "/").rstrip("/").casefold(), "<SYSTEM32>"),
    )
    for root, marker in roots:
        if value == root or value.startswith(root + "/"):
            normalized = marker + value[len(root):]
            if _forbidden_name(normalized):
                _fail("forbidden module path")
            return normalized
    _fail("module path is outside frozen roots")


def normalize_repo_path(path, repo_root):
    value = str(path).replace("\\", "/")
    if value.startswith("//?/"):
        value = value[4:]
    value = value.casefold()
    root = str(repo_root).replace("\\", "/").rstrip("/").casefold()
    if value != root and not value.startswith(root + "/"):
        _fail("repository path is outside the prospectively bound root")
    normalized = "<REPO_ROOT>" + value[len(root):]
    if _forbidden_name(normalized):
        _fail("forbidden repository source path")
    return normalized


def observe_file_rows(paths, *, normalize, read_bytes):
    """Create normalized size/hash observations without ever deriving expectations from them."""
    hashlib = __import__("hashlib")
    rows = []
    seen = set()
    for path in paths:
        normalized = normalize(path)
        if normalized in seen:
            _fail("duplicate normalized observed path")
        payload = read_bytes(path)
        if not isinstance(payload, (bytes, bytearray)):
            _fail("observed file reader must return bytes")
        payload = bytes(payload)
        rows.append((normalized, len(payload), hashlib.sha256(payload).hexdigest()))
        seen.add(normalized)
    return tuple(sorted(rows, key=lambda row: row[0].encode("utf-8")))


def verify_startup(observation):
    required = {
        "dont_write_bytecode": True,
        "no_site": 1,
        "no_user_site": 1,
        "ignore_environment": 1,
        "isolated": 1,
        "pycache_prefix": PYCACHE_PREFIX,
        "sys_path": INITIAL_SYS_PATH,
        "loaded_forbidden": (),
        "pycache_empty_before": True,
    }
    for key, expected in required.items():
        value = observation.get(key)
        if key == "sys_path":
            try:
                value = tuple(str(item).replace("\\", "/") for item in value or ())
            except TypeError:
                _fail("startup drift: sys_path")
        if value != expected:
            _fail("startup drift: %s" % key)
    return True


def verify_runtime_identity(observation):
    for key, expected in EXPECTED_RUNTIME.items():
        if observation.get(key) != expected:
            _fail("runtime identity drift: %s" % key)
    controls = observation.get("controls", {})
    exact_controls = {
        "device": "cpu", "dtype": "float64", "intraop_threads": 1,
        "interop_threads": 1, "deterministic_algorithms": True,
        "autocast": False, "amp": False, "tf32": False,
        "jit": False, "compile": False, "fused": False, "foreach": False,
        "denormal_preservation": True, "rounding": "nearest_ties_even", "fma": False,
    }
    if controls != exact_controls:
        _fail("kernel control drift")
    return True


def verify_probe_outputs(round_one, round_two):
    expected = tuple((name, schema, input_bits, output_bits) for name, schema, input_bits, output_bits in EXPECTED_PROBES)
    one = tuple(tuple(row) for row in round_one)
    two = tuple(tuple(row) for row in round_two)
    if one != expected or two != expected or one != two:
        _fail("ATen probe schema/order/bits drift")
    return expected


def verify_snapshots(snapshot_one, snapshot_two, expected_modules):
    one = tuple(sorted(tuple(row) for row in snapshot_one))
    two = tuple(sorted(tuple(row) for row in snapshot_two))
    if one != two:
        _fail("compiled-module snapshots differ")
    return verify_rows(one, expected_modules, MODULE_ROWS, MODULE_BYTES, MODULE_ROOT, "module")


def verify_loaded_sources(modules, expected_sources, exists=lambda _path: True):
    """Verify injected module metadata and return its exact normalized source set."""
    rows = []
    dynamic = {("torch.classes", "_classes.py"), ("torch.ops", "_ops.py")}
    for module in modules:
        name = module.get("name")
        file_name = module.get("file")
        loader = str(module.get("loader", ""))
        origin = module.get("origin")
        if name in ("site", "sitecustomize", "usercustomize") or "SourcelessFileLoader" in loader:
            _fail("forbidden loaded module")
        if not file_name:
            continue
        if _forbidden_name(file_name):
            _fail("forbidden loaded source suffix")
        if not exists(file_name):
            if (name, str(file_name).replace("\\", "/").rsplit("/", 1)[-1]) not in dynamic or origin is not None:
                _fail("nonexistent module file is not a frozen dynamic namespace")
            continue
        if not str(file_name).casefold().endswith(".py"):
            continue
        normalized = normalize_dependency_path(file_name)
        matches = [row for row in expected_sources if row[0] == normalized]
        if len(matches) != 1:
            _fail("loaded Python source is not in frozen set")
        rows.append(matches[0])
    return verify_rows(rows, expected_sources, SOURCE_ROWS, SOURCE_BYTES, SOURCE_ROOT, "loaded-python-source")


def verify_record(record_bytes, site_packages, read_bytes):
    """Verify every nonempty torch wheel RECORD digest and size with an injected reader."""
    csv = __import__("csv")
    base64 = __import__("base64")
    hashlib = __import__("hashlib")
    io = __import__("io")
    try:
        text = bytes(record_bytes).decode("utf-8", "strict")
        parsed = csv.reader(io.StringIO(text, newline=""))
    except (UnicodeDecodeError, csv.Error) as error:
        raise GateError("invalid wheel RECORD") from error
    count = 0
    for number, row in enumerate(parsed, 1):
        if len(row) != 3:
            _fail("RECORD row %d is malformed" % number)
        relative, digest_field, size_field = row
        folded = relative.replace("\\", "/")
        if not folded or folded.startswith(("/", "../")) or "/../" in folded:
            _fail("RECORD row %d has forbidden path" % number)
        if not digest_field:
            continue
        if _forbidden_name(folded):
            _fail("RECORD row %d has forbidden content-bound path" % number)
        if not digest_field.startswith("sha256=") or not size_field.isdecimal():
            _fail("RECORD row %d has unsupported identity" % number)
        payload = read_bytes(site_packages.rstrip("/\\") + "/" + folded)
        expected_b64 = digest_field[7:]
        actual_b64 = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
        if len(payload) != int(size_field) or actual_b64 != expected_b64:
            _fail("RECORD row %d identity mismatch" % number)
        count += 1
    if count == 0:
        _fail("RECORD has no content-bound entries")
    return count


def verify_anchor_rows(observed):
    expected = tuple(sorted(ANCHOR_ROWS))
    got = tuple(sorted(tuple(row) for row in observed))
    if got != expected:
        _fail("literal anchor identity mismatch")
    return got


def classify_open(mode, flags=0):
    """Return read/create-once or reject non-create-once writes and read/write modes."""
    mode = "r" if mode is None else str(mode)
    if any(marker in mode for marker in ("+", "w", "a")):
        _fail("truncate/append/read-write open is forbidden")
    if "x" in mode:
        if "r" in mode:
            _fail("read/write create is forbidden")
        return "create_once"
    os = __import__("os")
    o_wronly, o_rdwr = os.O_WRONLY, os.O_RDWR
    o_creat, o_excl, o_trunc, o_append = os.O_CREAT, os.O_EXCL, os.O_TRUNC, os.O_APPEND
    if flags & (o_rdwr | o_trunc | o_append):
        _fail("read/write, truncate, or append flags are forbidden")
    if flags & (o_wronly | o_creat | o_excl):
        if flags & (o_wronly | o_creat | o_excl) == (o_wronly | o_creat | o_excl):
            return "create_once"
        _fail("write is not exclusive create-once")
    return "read"


def verify_audit_events(events, allowed_reads, declared_outputs):
    allowed = {str(path).replace("\\", "/").casefold() for path in allowed_reads}
    outputs = {str(path).replace("\\", "/").casefold() for path in declared_outputs}
    created = set()
    opened = []
    for item in events:
        event = item[0]
        if event == "import":
            name = str(item[1]).casefold()
            if name in ("site", "sitecustomize", "usercustomize") or _forbidden_name(name):
                _fail("forbidden import audit event")
            continue
        if event in ("os.rename", "os.replace", "os.remove", "os.unlink", "os.rmdir", "os.mkdir"):
            _fail("rename/delete audit event is forbidden")
        if event != "open":
            continue
        path, mode = item[1], item[2]
        flags = item[3] if len(item) > 3 else 0
        normalized = str(path).replace("\\", "/").casefold()
        if _forbidden_name(normalized):
            _fail("forbidden opened path")
        kind = classify_open(mode, flags)
        if kind == "read":
            if normalized not in allowed:
                _fail("undeclared read")
        else:
            if normalized not in outputs or normalized in created:
                _fail("undeclared or repeated output create")
            created.add(normalized)
        opened.append((kind, normalized))
    if len(created) > 1:
        _fail("PASS/FAIL and INCOMPLETE outputs are mutually exclusive")
    return tuple(opened)


class GateContext:
    """Same-PID, continuously enforced capability handed to the A0 route."""

    __slots__ = ("pid", "namespace", "allowed_reads", "declared_outputs", "created", "audit_hook", "receipt", "active")

    def __init__(self, pid, allowed_reads, audit_hook, receipt):
        self.pid = int(pid)
        self.namespace = A0_NAMESPACE
        self.allowed_reads = frozenset(str(path).replace("\\", "/").casefold() for path in allowed_reads)
        self.declared_outputs = frozenset(
            (A0_NAMESPACE + "/" + name).casefold() for name in OUTPUT_FILENAMES
        )
        self.created = set()
        self.audit_hook = audit_hook
        self.receipt = dict(receipt)
        self.active = True

    def assert_active(self, pid=None):
        observed_pid = self.pid if pid is None else int(pid)
        if not self.active or observed_pid != self.pid:
            _fail("gate context is inactive or crossed a PID boundary")
        if self.audit_hook is None or not getattr(self.audit_hook, "installed", False) or not getattr(self.audit_hook, "enforcing", False):
            _fail("continuous audit enforcement is not active")
        return True

    def assert_can_read(self, path, identity=None):
        self.assert_active()
        normalized = str(path).replace("\\", "/").casefold()
        if normalized not in self.allowed_reads or normalized in self.declared_outputs:
            _fail("read is outside frozen source/input/dependency sets")
        if identity is not None and tuple(identity) not in self.receipt.get("allowed_read_rows", ()):
            _fail("read identity drift")
        return True

    def claim_output(self, path, exists=lambda _path: False):
        self.assert_active()
        normalized = str(path).replace("\\", "/").casefold()
        if normalized not in self.declared_outputs or normalized in self.created or exists(path):
            _fail("output is undeclared, already claimed, or already exists")
        if self.created:
            _fail("terminal outputs are mutually exclusive")
        self.created.add(normalized)
        return path

    def verify_terminal(self, pid, pycache_empty, snapshots_equal, audit_enforcing):
        self.assert_active(pid)
        if not pycache_empty or not snapshots_equal or not audit_enforcing:
            _fail("terminal gate verification failed")
        observed_created = set(self.created)
        observed_created.update(getattr(self.audit_hook, "created", ()))
        if len(observed_created) != 1 or not observed_created.issubset(self.declared_outputs):
            _fail("exactly one create-once terminal output must be claimed")
        return True

    def close(self):
        self.active = False


class AuditHook:
    """Source-owned audit accumulator/enforcer. Installation is explicit and one-way."""

    __slots__ = ("installed", "enforcing", "reset_done", "events", "allowed_reads", "declared_outputs", "created")

    def __init__(self):
        self.installed = False
        self.enforcing = False
        self.reset_done = False
        self.events = []
        self.allowed_reads = set()
        self.declared_outputs = set()
        self.created = set()

    def install(self, addaudithook=sys.addaudithook):
        if self.installed:
            _fail("audit hook already installed")
        addaudithook(self)
        self.installed = True
        return self

    def reset_accumulator(self):
        if not self.installed or self.enforcing or self.reset_done:
            _fail("audit accumulator reset is allowed exactly before enforcement")
        self.events[:] = []
        self.reset_done = True

    def begin_enforcement(self, allowed_reads, declared_outputs):
        if not self.installed or self.enforcing or not self.reset_done:
            _fail("invalid audit enforcement transition")
        self.allowed_reads = {str(path).replace("\\", "/").casefold() for path in allowed_reads}
        self.declared_outputs = {str(path).replace("\\", "/").casefold() for path in declared_outputs}
        exact_outputs = {(A0_NAMESPACE + "/" + name).casefold() for name in OUTPUT_FILENAMES}
        if self.declared_outputs != exact_outputs:
            _fail("declared output set differs from the frozen two-file boundary")
        self.enforcing = True

    def __call__(self, event, args):
        if event == "open":
            path = args[0]
            mode = args[1] if len(args) > 1 else "r"
            flags = args[2] if len(args) > 2 else 0
            record = ("open", path, mode, flags)
        elif event == "import":
            record = ("import", args[0] if args else "")
        elif event in ("os.rename", "os.replace", "os.remove", "os.unlink", "os.rmdir", "os.mkdir"):
            record = (event,) + tuple(args)
        else:
            return
        self.events.append(record)
        if _forbidden_name(record[1] if len(record) > 1 else ""):
            _fail("forbidden audit event")
        if self.enforcing:
            if record[0] == "open":
                normalized = str(record[1]).replace("\\", "/").casefold()
                kind = classify_open(record[2], record[3])
                if kind == "read":
                    if normalized not in self.allowed_reads:
                        _fail("undeclared read")
                else:
                    if normalized not in self.declared_outputs or normalized in self.created or self.created:
                        _fail("undeclared, repeated, or nonexclusive terminal output create")
                    self.created.add(normalized)
            else:
                verify_audit_events((record,), self.allowed_reads, self.declared_outputs)


def make_gate_context(*, pid, startup, runtime, probes_one, probes_two,
                      source_rows, loaded_source_rows, resource_rows,
                      expected_resource_rows, snapshot_one, snapshot_two,
                      expected_module_rows, allowed_read_rows, audit_hook):
    """Assemble a real-route capability only after every frozen observable passes."""
    verify_startup(startup)
    verify_runtime_identity(runtime)
    verify_probe_outputs(probes_one, probes_two)
    verify_rows(loaded_source_rows, source_rows, SOURCE_ROWS, SOURCE_BYTES, SOURCE_ROOT, "loaded-python-source")
    verify_rows(resource_rows, expected_resource_rows, RESOURCE_ROWS, RESOURCE_BYTES, RESOURCE_ROOT, "probe-resource")
    verify_snapshots(snapshot_one, snapshot_two, expected_module_rows)
    if audit_hook is None or not audit_hook.installed or not audit_hook.enforcing:
        _fail("audit hook did not remain installed and enforcing")
    receipt = {
        "schema": "VNFC_R02_A0_KERNEL_GATE_RECEIPT_V1",
        "law": LAW,
        "pid": int(pid),
        "source_root_sha256": SOURCE_ROOT,
        "probe_resource_root_sha256": RESOURCE_ROOT,
        "module_root_sha256": MODULE_ROOT,
        "probe_output_bits": tuple(row[3] for row in EXPECTED_PROBES),
        "snapshot_equality": True,
        "continuous_audit": True,
        "allowed_read_rows": tuple(tuple(row) for row in allowed_read_rows),
    }
    return GateContext(pid, (row[0] for row in allowed_read_rows), audit_hook, receipt)


def build_content_manifest(source_input_rows, dependency_source_rows, preprobe_runner_row):
    """Build the prospective R02 source/input declaration, never from runtime observations."""
    hashlib = __import__("hashlib")
    rows = tuple(sorted(tuple(row) for row in source_input_rows))
    serialized = canonicalize_rows(rows)
    runner = tuple(preprobe_runner_row)
    if len(runner) != 3 or runner[0] != "<REPO_ROOT>/" + RUNNER_RELATIVE_PATH:
        _fail("prospective preprobe runner row has the wrong canonical path")
    if runner not in rows:
        _fail("preprobe runner row must be present in the content-bound source/input rows")
    dependency_rows = tuple(tuple(row) for row in dependency_source_rows)
    verify_rows(dependency_rows, dependency_rows, SOURCE_ROWS, SOURCE_BYTES, SOURCE_ROOT, "prospective-dependency-source")
    preprobe_rows = tuple(dependency_rows) + (runner,)
    preprobe_serialized = canonicalize_rows(preprobe_rows)
    return {
        "schema": "VNFC_R02_A0_SOURCE_INPUT_OUTPUT_MANIFEST_V1",
        "law": LAW,
        "namespace": A0_NAMESPACE,
        "source_input_rows": rows,
        "source_input_serialization_bytes": len(serialized),
        "source_input_root_sha256": hashlib.sha256(serialized).hexdigest(),
        "preprobe_runner_row": runner,
        "preprobe_python_rows": len(preprobe_rows),
        "preprobe_python_serialization_bytes": len(preprobe_serialized),
        "preprobe_python_root_sha256": hashlib.sha256(preprobe_serialized).hexdigest(),
        "preprobe_rule": "frozen-dependency-942-plus-exact-runner-1",
        "create_once_outputs": tuple(A0_NAMESPACE + "/" + name for name in OUTPUT_FILENAMES),
        "output_semantics": "mutually-exclusive-create-once",
    }


def verify_content_manifest(manifest, observed_rows, dependency_source_rows):
    required = {
        "schema", "law", "namespace", "source_input_rows",
        "source_input_serialization_bytes", "source_input_root_sha256",
        "preprobe_runner_row", "preprobe_python_rows",
        "preprobe_python_serialization_bytes", "preprobe_python_root_sha256", "preprobe_rule",
        "create_once_outputs", "output_semantics",
    }
    if set(manifest) != required:
        _fail("source/input/output manifest fields differ")
    if manifest["schema"] != "VNFC_R02_A0_SOURCE_INPUT_OUTPUT_MANIFEST_V1" or manifest["law"] != LAW:
        _fail("source/input/output manifest identity differs")
    if manifest["namespace"] != A0_NAMESPACE or manifest["output_semantics"] != "mutually-exclusive-create-once":
        _fail("source/input/output manifest boundary differs")
    expected_outputs = tuple(A0_NAMESPACE + "/" + name for name in OUTPUT_FILENAMES)
    if tuple(manifest["create_once_outputs"]) != expected_outputs:
        _fail("source/input/output manifest outputs differ")
    runner = tuple(manifest["preprobe_runner_row"])
    if len(runner) != 3 or runner[0] != "<REPO_ROOT>/" + RUNNER_RELATIVE_PATH:
        _fail("preprobe runner canonical path differs")
    if manifest["preprobe_rule"] != "frozen-dependency-942-plus-exact-runner-1":
        _fail("preprobe source rule differs")
    dependency_rows = tuple(tuple(row) for row in dependency_source_rows)
    if int(manifest["preprobe_python_rows"]) != SOURCE_ROWS + 1:
        _fail("preprobe source row count is not frozen dependency plus one runner")
    union = dependency_rows + (runner,)
    verify_rows(
        union, union, int(manifest["preprobe_python_rows"]),
        int(manifest["preprobe_python_serialization_bytes"]),
        str(manifest["preprobe_python_root_sha256"]), "preprobe-python-union",
    )
    expected_rows = tuple(tuple(row) for row in manifest["source_input_rows"])
    return verify_rows(
        observed_rows,
        expected_rows,
        len(expected_rows),
        int(manifest["source_input_serialization_bytes"]),
        str(manifest["source_input_root_sha256"]),
        "r02-source-input",
    )


def verify_preprobe_source_union(*, dependency_rows, runner_row, manifest,
                                 main_module, early_repo_modules, early_repo_reads, repo_root):
    """Verify the reviewed 942 dependency + one exact source-owned runner semantics."""
    if early_repo_modules:
        _fail("repository/R02 module loaded before the preprobe boundary")
    if early_repo_reads:
        _fail("repository/R02 source read before the preprobe boundary")
    required_main = {"name", "file", "resolved_file", "origin", "loader", "exists"}
    if set(main_module) != required_main or main_module["name"] != "__main__":
        _fail("preprobe __main__ metadata is missing or malformed")
    if main_module["exists"] is not True or not main_module["file"]:
        _fail("preprobe __main__.__file__ is hidden or nonexistent")
    normalized_file = normalize_repo_path(main_module["file"], repo_root)
    normalized_resolved = normalize_repo_path(main_module["resolved_file"], repo_root)
    if normalized_file != "<REPO_ROOT>/" + RUNNER_RELATIVE_PATH or normalized_resolved != normalized_file:
        _fail("preprobe __main__ is aliased or is not the exact runner")
    if normalize_repo_path(main_module["origin"], repo_root) != normalized_file:
        _fail("preprobe __main__ origin differs from its exact source")
    if main_module["loader"] not in ("SourceFileLoader", ""):
        _fail("preprobe __main__ loader differs")
    expected_runner = tuple(manifest["preprobe_runner_row"])
    observed_runner = tuple(runner_row)
    if observed_runner != expected_runner or observed_runner[0] != normalized_file:
        _fail("preprobe runner path/size/digest differs")
    verify_rows(
        dependency_rows, dependency_rows, SOURCE_ROWS, SOURCE_BYTES, SOURCE_ROOT,
        "loaded-python-source",
    )
    union = tuple(dependency_rows) + (observed_runner,)
    return verify_rows(
        union, tuple(dependency_rows) + (expected_runner,),
        int(manifest["preprobe_python_rows"]),
        int(manifest["preprobe_python_serialization_bytes"]),
        str(manifest["preprobe_python_root_sha256"]),
        "preprobe-python-union",
    )


def run_bootstrap_sequence(backend, audit_hook, pid):
    """Execute the frozen dependency preflight against an injectable platform backend.

    The backend is observation-only: all expected roots remain module literals or rows parsed from
    the frozen authority inputs.  This function creates no A0 fixture/RNG/model/output.
    """
    order = []
    startup = backend.startup_observation()
    verify_startup(startup)
    order.append("verify:startup")
    if audit_hook.installed:
        _fail("early audit hook must be installed exactly once by the bootstrap")
    audit_hook.install(backend.addaudithook)
    order.append("install:audit-hook")
    backend.reject_forbidden_modules()
    order.append("reject:site-customize")
    imported = {}
    for name in ("pathlib", "csv", "base64", "hashlib"):
        imported[name] = backend.import_module(name)
        order.append("import:" + name)
    frozen = backend.verify_frozen_authorities(imported)
    verify_anchor_rows(frozen["anchor_rows"])
    source_rows = verify_source_manifest(frozen["source_manifest_bytes"])
    if int(frozen["record_verified_entries"]) <= 0:
        _fail("wheel RECORD was not fully verified")
    order.extend(("verify:anchors", "verify:torch-record", "verify:source-manifest"))
    audit_hook.reset_accumulator()
    order.append("audit:reset-accumulator")
    backend.append_site_packages(SITE_PACKAGES)
    order.append("sys.path.append:" + SITE_PACKAGES)
    for name in ("ctypes", "ctypes.wintypes", "torch"):
        imported[name] = backend.import_module(name)
        order.append("import:" + name)
    runtime = backend.runtime_observation(imported)
    verify_runtime_identity(runtime)
    order.append("verify:runtime-controls")
    probes_one = backend.probe_round(imported, 1)
    verify_probe_outputs(probes_one, EXPECTED_PROBES)
    order.append("probe:round-1")
    snapshot_one = backend.module_snapshot(imported, 1)
    order.append("snapshot:1")
    probes_two = backend.probe_round(imported, 2)
    verify_probe_outputs(EXPECTED_PROBES, probes_two)
    order.append("probe:round-2")
    snapshot_two = backend.module_snapshot(imported, 2)
    order.append("snapshot:2")
    expected_modules = tuple(frozen["module_rows"])
    verify_snapshots(snapshot_one, snapshot_two, expected_modules)
    source_observation = backend.preprobe_source_observation(imported, source_rows, audit_hook.events)
    content_manifest = frozen["content_manifest"]
    verify_preprobe_source_union(
        dependency_rows=source_observation["dependency_rows"],
        runner_row=source_observation["runner_row"], manifest=content_manifest,
        main_module=source_observation["main_module"],
        early_repo_modules=source_observation["early_repo_modules"],
        early_repo_reads=source_observation["early_repo_reads"],
        repo_root=source_observation["repo_root"],
    )
    expected_resources = tuple(frozen["resource_rows"])
    resources = backend.opened_resource_rows(imported, audit_hook.events)
    verify_rows(resources, expected_resources, RESOURCE_ROWS, RESOURCE_BYTES, RESOURCE_ROOT, "probe-resource")
    order.extend(("verify:two-snapshots", "verify:942-sources", "verify:31-resources"))
    content_rows = backend.content_observed_rows(content_manifest)
    verify_content_manifest(content_manifest, content_rows, source_rows)
    allowed_rows = tuple(source_rows) + expected_resources + expected_modules + tuple(content_rows)
    allowed_paths = backend.absolute_allowed_read_paths(allowed_rows)
    declared_outputs = tuple(A0_NAMESPACE + "/" + name for name in OUTPUT_FILENAMES)
    audit_hook.begin_enforcement(allowed_paths, declared_outputs)
    order.append("audit:begin-continuous-enforcement")
    receipt_rows = tuple((str(path).replace("\\", "/").casefold(), size, digest) for path, size, digest in backend.absolute_allowed_read_rows(allowed_rows))
    context = make_gate_context(
        pid=pid, startup=startup, runtime=runtime,
        probes_one=probes_one, probes_two=probes_two,
        source_rows=source_rows, loaded_source_rows=source_observation["dependency_rows"],
        resource_rows=resources, expected_resource_rows=expected_resources,
        snapshot_one=snapshot_one, snapshot_two=snapshot_two,
        expected_module_rows=expected_modules, allowed_read_rows=receipt_rows,
        audit_hook=audit_hook,
    )
    context.receipt["bootstrap_order"] = tuple(order)
    context.receipt["content_manifest"] = dict(content_manifest)
    context.receipt["preprobe_runner_row"] = tuple(content_manifest["preprobe_runner_row"])
    context.receipt["preprobe_python_rows"] = int(content_manifest["preprobe_python_rows"])
    context.receipt["preprobe_python_serialization_bytes"] = int(content_manifest["preprobe_python_serialization_bytes"])
    context.receipt["preprobe_python_root_sha256"] = str(content_manifest["preprobe_python_root_sha256"])
    return context


def bootstrap_plan():
    """Machine-testable exact import/control/call plan; it never executes the probe."""
    return (
        "import:sys", "verify:startup", "install:audit-hook", "reject:site-customize",
        "import:pathlib", "import:csv", "import:base64", "import:hashlib",
        "verify:anchors", "verify:torch-record", "verify:source-manifest",
        "audit:reset-accumulator", "sys.path.append:" + SITE_PACKAGES,
        "import:ctypes", "import:ctypes.wintypes", "import:torch",
        "verify:runtime-controls", "probe:round-1", "load:kernel32", "load:psapi",
        "snapshot:1", "probe:round-2", "snapshot:2", "verify:two-snapshots",
        "verify:942-sources", "verify:31-resources", "audit:begin-continuous-enforcement",
        "source-load:r02-a0", "execute:a0-same-pid", "verify:terminal", "publish:create-once",
    )
