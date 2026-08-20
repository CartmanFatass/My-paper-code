from tools.codex_supervisor.durability.static_guards import scan_package, scan_source_text


def test_scanner_flags_synthetic_violations() -> None:
    violating = '''
def bad(client):
    client.request("turn/start", {})
    connection.execute("UPDATE wake_batches SET state='COMPLETED'")
    connection.execute("INSERT INTO mutation_intents (intent_id) VALUES ('x')")
'''
    found = scan_source_text(violating, name="bad.py")
    assert any("mutating" in item for item in found)
    assert any("protected state" in item for item in found)
    assert any("mutation_intents insert" in item for item in found)


def test_scanner_allows_kernel_modules() -> None:
    clean = '''
from tools.codex_supervisor.durability.transitions import TransitionKernel
def ok():
    kernel.apply(request)
'''
    assert scan_source_text(clean, name="durability/transitions.py") == []


def test_package_scan_runs() -> None:
    violations = scan_package()
    assert isinstance(violations, list)
