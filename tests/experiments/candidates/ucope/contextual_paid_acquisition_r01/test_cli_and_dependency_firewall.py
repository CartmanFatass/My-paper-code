import argparse
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01.cli import build_parser, main
from experiments.candidates.ucope.contextual_paid_acquisition_r01.contract import CONTRACT_ID, default_manifest


EXPECTED = {
    "describe": set(),
    "check-contract": {"manifest"},
    "preflight-support": {"manifest", "output_root"},
    "validate-preflight": {"artifact"},
}


def _command_parsers(parser):
    subparsers = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
    assert len(subparsers) == 1
    return subparsers[0].choices


def test_cli_surface_is_exactly_nonresult_and_has_no_override_flags():
    commands = _command_parsers(build_parser())
    assert set(commands) == set(EXPECTED)
    for name, command in commands.items():
        destinations = {action.dest for action in command._actions if action.dest != "help"}
        assert destinations == EXPECTED[name]
        for action in command._actions:
            if action.dest != "help":
                assert action.required is True
    rendered = " ".join(option for command in commands.values() for action in command._actions for option in action.option_strings)
    for forbidden in ("--seed", "--context", "--cost", "--reliability", "--k", "--threshold", "--arm", "--retry", "--partial", "--train", "--evaluate", "--result"):
        assert forbidden not in rendered.lower()


@pytest.mark.parametrize("argv", [
    ["train"], ["evaluate"], ["publish-result"], ["describe", "--seed", "x"],
    ["preflight-support", "--manifest", "x", "--output-root", "y", "--episodes", "1"],
])
def test_cli_rejects_result_commands_and_overrides(argv):
    with pytest.raises(SystemExit):
        build_parser().parse_args(argv)


def test_describe_and_check_contract_are_nonresult(tmp_path, capsys):
    assert main(["describe"]) == 0
    described = json.loads(capsys.readouterr().out)
    assert described == {
        "commands": ["describe", "check-contract", "preflight-support", "validate-preflight"],
        "contract_id": CONTRACT_ID,
        "feature_names": list(described["feature_names"]),
        "phase": "BELIEF",
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(default_manifest("TEST_ONLY", 640)), encoding="utf-8")
    assert main(["check-contract", "--manifest", str(manifest)]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked == {"contract_id": CONTRACT_ID, "mode": "TEST_ONLY", "valid": True}


def test_clean_process_cli_and_preflight_import_do_not_load_torch_or_historical_runtime():
    code = r'''
import sys
from experiments.candidates.ucope.contextual_paid_acquisition_r01.cli import build_parser
from experiments.candidates.ucope.contextual_paid_acquisition_r01.support import preflight_support
assert set(next(a for a in build_parser()._actions if hasattr(a, "choices") and a.choices).choices) == {"describe", "check-contract", "preflight-support", "validate-preflight"}
bad = [name for name in sys.modules if name == "torch" or name.startswith("torch.") or "variable_k_paid_probe_r01_r03" in name or name.endswith("native_backend")]
assert not bad, bad
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=Path.cwd(), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_cli_source_registers_no_training_evaluation_or_publication_imports():
    source = Path("experiments/candidates/ucope/contextual_paid_acquisition_r01/cli.py").read_text(encoding="utf-8").lower()
    for forbidden in ("train_one_seed", "evaluate_heldout_cells", "publish_complete_result", "variable_k_paid_probe_r01_r03", "native_backend"):
        assert forbidden not in source
