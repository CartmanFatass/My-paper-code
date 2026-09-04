import base64
import hashlib

import pytest

from experiments.candidates.variable_n_fleet_churn_r02 import kernel_gate as gate


def row_bytes(rows):
    return "".join(f"{path}\t{size}\t{digest}\n" for path, size, digest in rows).encode()


def test_tsv_parser_is_exact_and_does_not_learn_expected_rows():
    rows = (
        ("<PYTHON_PREFIX>/a.py", 1, "0" * 64),
        ("<PYTHON_PREFIX>/b.py", 2, "1" * 64),
    )
    assert gate.parse_tsv_manifest(row_bytes(rows)) == rows
    for tampered in (b"\xef\xbb\xbf" + row_bytes(rows), row_bytes(rows).replace(b"\n", b"\r\n"), row_bytes(rows)[:-1]):
        with pytest.raises(gate.GateError):
            gate.parse_tsv_manifest(tampered)
    with pytest.raises(gate.GateError):
        gate.parse_tsv_manifest(row_bytes((rows[0], rows[0])))


def test_row_set_verifier_rejects_row_size_hash_and_root_drift():
    rows = (("<PYTHON_PREFIX>/a.py", 1, "0" * 64),)
    serialized = row_bytes(rows)
    root = hashlib.sha256(serialized).hexdigest()
    assert gate.verify_rows(rows, rows, 1, len(serialized), root, "synthetic") == rows
    mutations = (
        (("<PYTHON_PREFIX>/x.py", 1, "0" * 64),),
        (("<PYTHON_PREFIX>/a.py", 2, "0" * 64),),
        (("<PYTHON_PREFIX>/a.py", 1, "1" * 64),),
    )
    for observed in mutations:
        with pytest.raises(gate.GateError):
            gate.verify_rows(observed, rows, 1, len(serialized), root, "synthetic")
    with pytest.raises(gate.GateError):
        gate.verify_rows(rows, rows, 1, len(serialized), "f" * 64, "synthetic")


def test_path_normalizers_are_casefolded_root_bound_and_reject_bytecode():
    assert gate.normalize_dependency_path(r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\Lib\X.py") == "<PYTHON_PREFIX>/lib/x.py"
    assert gate.normalize_module_path(r"\\?\C:\Windows\System32\KERNEL32.DLL") == "<SYSTEM32>/kernel32.dll"
    with pytest.raises(gate.GateError):
        gate.normalize_dependency_path(r"D:\other\x.py")
    with pytest.raises(gate.GateError):
        gate.normalize_dependency_path(r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\x.pyc")
    with pytest.raises(gate.GateError):
        gate.normalize_module_path(r"C:\temp\evil.dll")


def test_observed_snapshots_normalize_hash_and_reject_duplicate_roots():
    files = {
        gate.PYTHON_PREFIX + "/B.py": b"bb",
        gate.PYTHON_PREFIX + "/a.py": b"a",
    }
    rows = gate.observe_file_rows(files, normalize=gate.normalize_dependency_path, read_bytes=files.__getitem__)
    assert [row[0] for row in rows] == ["<PYTHON_PREFIX>/a.py", "<PYTHON_PREFIX>/b.py"]
    assert rows[0][1:] == (1, hashlib.sha256(b"a").hexdigest())
    with pytest.raises(gate.GateError, match="duplicate"):
        gate.observe_file_rows(
            (gate.PYTHON_PREFIX + "/A.py", gate.PYTHON_PREFIX + "/a.py"),
            normalize=gate.normalize_dependency_path,
            read_bytes=lambda _path: b"a",
        )


def startup():
    return {
        "dont_write_bytecode": True,
        "no_site": 1,
        "no_user_site": 1,
        "ignore_environment": 1,
        "isolated": 1,
        "pycache_prefix": gate.PYCACHE_PREFIX,
        "sys_path": gate.INITIAL_SYS_PATH,
        "loaded_forbidden": (),
        "pycache_empty_before": True,
    }


@pytest.mark.parametrize("key", tuple(startup()))
def test_startup_flags_paths_and_empty_pycache_fail_closed(key):
    assert gate.verify_startup(startup())
    changed = startup()
    changed[key] = object()
    with pytest.raises(gate.GateError, match="startup drift"):
        gate.verify_startup(changed)


def test_literal_anchor_tamper_is_rejected():
    assert gate.verify_anchor_rows(gate.ANCHOR_ROWS)
    tampered = list(gate.ANCHOR_ROWS)
    tampered[0] = (tampered[0][0], tampered[0][1], "0" * 64)
    with pytest.raises(gate.GateError, match="anchor"):
        gate.verify_anchor_rows(tampered)


def test_wheel_record_verifies_every_nonempty_entry_and_rejects_tamper():
    payload = b"frozen"
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
    record = f"torch/a.py,sha256={encoded},{len(payload)}\ntorch/__pycache__/empty.pyc,,\n".encode()
    assert gate.verify_record(record, "S", lambda path: payload if path == "S/torch/a.py" else b"") == 1
    with pytest.raises(gate.GateError, match="identity mismatch"):
        gate.verify_record(record, "S", lambda _path: b"tampered")
    with pytest.raises(gate.GateError, match="forbidden"):
        gate.verify_record(f"torch/a.pyc,sha256={encoded},{len(payload)}\n".encode(), "S", lambda _path: payload)


def test_exact_probe_order_schema_input_and_output_bits_are_two_round_equal():
    assert gate.verify_probe_outputs(gate.EXPECTED_PROBES, gate.EXPECTED_PROBES) == gate.EXPECTED_PROBES
    tampered = list(gate.EXPECTED_PROBES)
    tampered[0] = tampered[0][:-1] + ("0x0.0p+0",)
    with pytest.raises(gate.GateError, match="probe"):
        gate.verify_probe_outputs(tampered, gate.EXPECTED_PROBES)


def test_loaded_source_rejects_sourceless_pyc_customize_and_extra_source():
    expected = (("<PYTHON_PREFIX>/a.py", 1, "0" * 64),)
    common = {"name": "a", "file": gate.PYTHON_PREFIX + "/a.py", "loader": "SourceFileLoader", "origin": "a.py"}
    # The aggregate is intentionally patched to the synthetic values; expected roots stay immutable.
    with pytest.raises(gate.GateError):
        gate.verify_loaded_sources((common,), expected)
    bad = (
        {**common, "loader": "SourcelessFileLoader"},
        {**common, "file": gate.PYTHON_PREFIX + "/a.pyc"},
        {**common, "name": "sitecustomize"},
        {**common, "file": gate.PYTHON_PREFIX + "/extra.py"},
    )
    for module in bad:
        with pytest.raises(gate.GateError):
            gate.verify_loaded_sources((module,), expected)


def test_audit_gate_rejects_undeclared_reads_writes_and_path_classes():
    allowed = ("c:/frozen/input.tsv",)
    outputs = (gate.A0_NAMESPACE + "/A0_CONFORMANCE.json", gate.A0_NAMESPACE + "/INCOMPLETE.json")
    assert gate.verify_audit_events((('open', 'C:/frozen/input.tsv', 'r', 0),), allowed, outputs)
    forbidden = (
        ("open", "C:/other.txt", "r", 0),
        ("open", outputs[0], "w", 0),
        ("open", outputs[0], "a", 0),
        ("open", outputs[0], "r+", 0),
        ("open", "C:/frozen/x.pth", "r", 0),
        ("import", "sitecustomize"),
        ("os.rename", "a", "b"),
        ("os.mkdir", gate.A0_NAMESPACE),
    )
    for event in forbidden:
        with pytest.raises(gate.GateError):
            gate.verify_audit_events((event,), allowed, outputs)
    assert gate.verify_audit_events((("open", outputs[0], "x", 0),), allowed, outputs)


def test_source_owned_audit_hook_installs_resets_once_then_enforces_continuously():
    installed = []
    hook = gate.AuditHook().install(installed.append)
    assert installed == [hook]
    hook.events.append(("open", "pre-reset", "r", 0))
    hook.reset_accumulator()
    assert hook.events == [] and hook.reset_done
    with pytest.raises(gate.GateError):
        hook.reset_accumulator()
    output = gate.A0_NAMESPACE + "/A0_CONFORMANCE.json"
    incomplete = gate.A0_NAMESPACE + "/INCOMPLETE.json"
    hook.begin_enforcement(("c:/frozen",), (output, incomplete))
    hook("open", ("C:/frozen", "r", 0))
    hook("open", (output, "x", 0))
    with pytest.raises(gate.GateError):
        hook("open", (output, "x", 0))
    with pytest.raises(gate.GateError):
        hook("os.mkdir", (gate.A0_NAMESPACE, 0o777, -1))


class InstalledHook:
    installed = True
    enforcing = True


def test_gate_context_is_same_pid_continuous_and_outputs_are_mutually_exclusive_create_once():
    output = gate.A0_NAMESPACE + "/A0_CONFORMANCE.json"
    context = gate.GateContext(17, ("c:/input",), InstalledHook(), {"allowed_read_rows": ()})
    assert context.assert_active(17)
    assert context.assert_can_read("C:/INPUT")
    with pytest.raises(gate.GateError, match="PID"):
        context.assert_active(18)
    assert context.claim_output(output) == output
    with pytest.raises(gate.GateError):
        context.claim_output(output)
    with pytest.raises(gate.GateError):
        context.claim_output(gate.A0_NAMESPACE + "/INCOMPLETE.json")
    assert context.verify_terminal(17, True, True, True)
    context.close()
    with pytest.raises(gate.GateError):
        context.assert_active(17)


def test_content_manifest_is_prospective_exact_and_output_closed(monkeypatch):
    runner = ("<REPO_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py", 4, hashlib.sha256(b"code").hexdigest())
    rows = (runner,)
    dependency = (("<PYTHON_PREFIX>/a.py", 1, "0" * 64),)
    serialized_dependency = gate.canonicalize_rows(dependency)
    monkeypatch.setattr(gate, "SOURCE_ROWS", 1)
    monkeypatch.setattr(gate, "SOURCE_BYTES", len(serialized_dependency))
    monkeypatch.setattr(gate, "SOURCE_ROOT", hashlib.sha256(serialized_dependency).hexdigest())
    manifest = gate.build_content_manifest(rows, dependency, runner)
    assert gate.verify_content_manifest(manifest, rows, dependency) == rows
    changed = dict(manifest)
    changed["create_once_outputs"] = (gate.A0_NAMESPACE + "/other.json",)
    with pytest.raises(gate.GateError, match="outputs"):
        gate.verify_content_manifest(changed, rows, dependency)
    with pytest.raises(gate.GateError, match="row-set"):
        gate.verify_content_manifest(manifest, ((rows[0][0], rows[0][1], "0" * 64),), dependency)


def synthetic_preprobe_manifest(dependency, runner):
    return gate.build_content_manifest((runner,), dependency, runner)


def test_preprobe_union_requires_visible_exact_unaliased_main_and_no_other_repo_import(monkeypatch):
    dependency = (("<PYTHON_PREFIX>/a.py", 1, "0" * 64),)
    runner = ("<REPO_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py", 2, "1" * 64)
    monkeypatch.setattr(gate, "SOURCE_ROWS", 1)
    serialized = gate.canonicalize_rows(dependency)
    monkeypatch.setattr(gate, "SOURCE_BYTES", len(serialized))
    monkeypatch.setattr(gate, "SOURCE_ROOT", hashlib.sha256(serialized).hexdigest())
    manifest = synthetic_preprobe_manifest(dependency, runner)
    main = {
        "name": "__main__", "file": "C:/repo/scripts/run_vnfc_bpcr_r02_a0.py",
        "resolved_file": "C:/repo/scripts/run_vnfc_bpcr_r02_a0.py",
        "origin": "C:/repo/scripts/run_vnfc_bpcr_r02_a0.py",
        "loader": "SourceFileLoader", "exists": True,
    }
    union = gate.verify_preprobe_source_union(
        dependency_rows=dependency, runner_row=runner, manifest=manifest,
        main_module=main, early_repo_modules=(), early_repo_reads=(), repo_root="C:/repo",
    )
    assert len(union) == 2
    mutations = []
    hidden = dict(main); hidden["file"] = None
    mutations.append((hidden, (), (), runner, manifest))
    aliased = dict(main); aliased["resolved_file"] = "C:/repo/elsewhere.py"
    mutations.append((aliased, (), (), runner, manifest))
    mutations.append((main, (("early", "C:/repo/early.py"),), (), runner, manifest))
    mutations.append((main, (), ("c:/repo/early.py",), runner, manifest))
    mutations.append((main, (), (), (runner[0], runner[1], "2" * 64), manifest))
    missing_runner = dict(manifest); missing_runner["preprobe_runner_row"] = ()
    mutations.append((main, (), (), runner, missing_runner))
    extra_runner = dict(main); extra_runner["file"] = "C:/repo/scripts/extra_runner.py"
    mutations.append((extra_runner, (), (), runner, manifest))
    wrong_root = dict(manifest); wrong_root["preprobe_python_root_sha256"] = "f" * 64
    mutations.append((main, (), (), runner, wrong_root))
    for observed_main, early, reads, observed_runner, observed_manifest in mutations:
        with pytest.raises(gate.GateError):
            gate.verify_preprobe_source_union(
                dependency_rows=dependency, runner_row=observed_runner, manifest=observed_manifest,
                main_module=observed_main, early_repo_modules=early, early_repo_reads=reads, repo_root="C:/repo",
            )


def test_bootstrap_plan_has_exact_import_control_and_same_pid_publication_order():
    plan = gate.bootstrap_plan()
    assert plan[:8] == (
        "import:sys", "verify:startup", "install:audit-hook", "reject:site-customize",
        "import:pathlib", "import:csv", "import:base64", "import:hashlib",
    )
    assert plan.index("audit:reset-accumulator") < plan.index("sys.path.append:" + gate.SITE_PACKAGES)
    assert plan.index("probe:round-1") < plan.index("snapshot:1") < plan.index("probe:round-2") < plan.index("snapshot:2")
    assert plan[-3:] == ("execute:a0-same-pid", "verify:terminal", "publish:create-once")
