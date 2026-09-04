from pathlib import Path


def test_b01_namespace_does_not_import_r01_r02_result_schemas():
    root = Path("experiments/candidates/finite_resource_relational_inductive_efficiency/b01")
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    for forbidden in (
        "FRRIE_MANIFEST_V2", "FRRIE_CHECKPOINT_V2", "FRRIE_COMPLETE_PANEL_RESULT_V2",
        "FRRIE_R02", "SIMULTANEOUS_MEAN_INFERENCE",
    ):
        assert forbidden not in source
