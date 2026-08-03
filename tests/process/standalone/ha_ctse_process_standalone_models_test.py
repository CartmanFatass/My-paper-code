from __future__ import annotations

import ast
from pathlib import Path
import subprocess

import torch

import ha_ctse_process.standalone_agent as standalone_agent
import ha_ctse_process.standalone_models as standalone_models


ROOT = Path(__file__).resolve().parents[3]
BASE_COMMIT = "bddb4311227741139c00c0a51ac7b1f3e4358caf"
MOVED_NAMES = (
    "mlp",
    "sparsemax",
    "InteractionCompactEncoder",
    "CompactTeamBridge",
    "FixedSkillPrimitivePolicy",
    "LowLevelPolicy",
    "ScalarRunningMeanStd",
    "RecurrentLowLevelPolicy",
    "Box",
    "Discrete",
    "StrictHMASDMAPPOLowLevelPolicy",
    "HighActionSample",
    "SkillDurationPolicy",
    "ProcessEncoder",
)
AGENT_REFERENCES = {
    "InteractionCompactEncoder",
    "CompactTeamBridge",
    "FixedSkillPrimitivePolicy",
    "LowLevelPolicy",
    "ScalarRunningMeanStd",
    "RecurrentLowLevelPolicy",
    "StrictHMASDMAPPOLowLevelPolicy",
    "SkillDurationPolicy",
    "ProcessEncoder",
}


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _definitions(tree: ast.Module) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }


def test_models_are_uniquely_owned_without_aliases_or_reverse_edge():
    agent_tree = _tree(ROOT / "ha_ctse_process" / "standalone_agent.py")
    models_tree = _tree(ROOT / "ha_ctse_process" / "standalone_models.py")
    agent_definitions = _definitions(agent_tree)
    model_definitions = _definitions(models_tree)

    assert set(MOVED_NAMES) <= set(model_definitions)
    assert set(MOVED_NAMES).isdisjoint(agent_definitions)
    assert all(not hasattr(standalone_agent, name) for name in MOVED_NAMES)
    for node in ast.walk(models_tree):
        if isinstance(node, ast.Import):
            assert all(alias.name != "ha_ctse_process.standalone_agent" for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "ha_ctse_process.standalone_agent"


def test_moved_definition_asts_match_the_ticket_base():
    base_source = subprocess.run(
        [
            "git",
            "-c",
            "core.longpaths=true",
            "show",
            f"{BASE_COMMIT}:ha_ctse_process/standalone_agent.py",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    base_definitions = _definitions(ast.parse(base_source))
    model_definitions = _definitions(
        _tree(ROOT / "ha_ctse_process" / "standalone_models.py")
    )

    for name in MOVED_NAMES:
        assert ast.dump(
            model_definitions[name], include_attributes=False
        ) == ast.dump(base_definitions[name], include_attributes=False)


def test_agent_uses_only_module_qualified_model_references():
    tree = _tree(ROOT / "ha_ctse_process" / "standalone_agent.py")
    bare_references = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    } & set(MOVED_NAMES)
    qualified_references = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "standalone_models"
    }
    module_imports = [
        alias
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "ha_ctse_process.standalone_models"
    ]

    assert not bare_references
    assert AGENT_REFERENCES <= qualified_references
    assert len(module_imports) == 1
    assert module_imports[0].asname == "standalone_models"


def test_recurrent_low_state_dict_and_deterministic_forward_parity():
    kwargs = dict(
        obs_dim=4,
        state_dim=8,
        n_agents=2,
        n_skills=3,
        num_team_codes=2,
        action_dim=3,
        hidden_dim=7,
        action_space_type="discrete",
    )
    torch.manual_seed(71)
    source = standalone_models.RecurrentLowLevelPolicy(**kwargs)
    restored = standalone_models.RecurrentLowLevelPolicy(**kwargs)
    restored.load_state_dict(source.state_dict())

    assert list(restored.state_dict()) == list(source.state_dict())
    for key, value in source.state_dict().items():
        torch.testing.assert_close(restored.state_dict()[key], value, rtol=0.0, atol=0.0)

    obs = torch.arange(16, dtype=torch.float32).reshape(4, 4) / 10.0
    skills = torch.tensor([0, 1, 2, 0])
    states = torch.arange(32, dtype=torch.float32).reshape(4, 8) / 20.0
    team_codes = torch.tensor([0, 1, 0, 1])
    agent_ids = torch.tensor([0, 1, 0, 1])
    actor_hxs = torch.zeros(4, 7)
    critic_hxs = torch.zeros(4, 7)
    source_outputs = source.act(
        obs,
        skills,
        actor_hxs,
        states,
        team_codes,
        critic_hxs,
        agent_ids,
        deterministic=True,
    )
    restored_outputs = restored.act(
        obs,
        skills,
        actor_hxs,
        states,
        team_codes,
        critic_hxs,
        agent_ids,
        deterministic=True,
    )
    for actual, expected in zip(restored_outputs, source_outputs):
        torch.testing.assert_close(actual, expected, rtol=0.0, atol=0.0)
