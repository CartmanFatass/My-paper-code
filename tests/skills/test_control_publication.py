"""Development-only publication checks; no scientific launch integration."""
import importlib.util
from pathlib import Path
import shutil
import tomllib

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('publish_claude', ROOT/'tools/publish_claude_control.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


def test_publication_preserves_native_metadata_and_detects_drift(tmp_path):
    for folder in ['.agents/skills', '.codex/agents', '.claude/agents']:
        shutil.copytree(ROOT/folder, tmp_path/folder, ignore=shutil.ignore_patterns('__pycache__'))
    headers = {p.name:p.read_text().split('---',2)[1] for p in (tmp_path/'.claude/agents').glob('*.md')}
    publisher.publish(tmp_path)
    assert publisher.publish(tmp_path, check=True) == []
    for name, before in headers.items():
        after = (tmp_path/'.claude/agents'/name).read_text().split('---',2)[1]
        for field in ['tools:', 'model:']:
            assert next(x for x in before.splitlines() if x.startswith(field)) == next(x for x in after.splitlines() if x.startswith(field))
    target = tmp_path/'.claude/skills/hmasd-scientific-tools/SKILL.md'
    target.write_text(target.read_text()+'\nforeign edit\n')
    before = target.read_bytes()
    assert target.relative_to(tmp_path).as_posix() in publisher.publish(tmp_path, check=True)
    assert target.read_bytes() == before  # check mode must not overwrite a writer
    publisher.publish(tmp_path)
    assert publisher.publish(tmp_path, check=True) == []


def test_generated_tree_carries_references_helpers_and_hub_adaptation():
    outputs = publisher.generated()
    canonical = ROOT/'.claude/skills/hmasd-chatgpt-pro-transport'
    for relative in ['references/agentify.md', 'references/send-hit-point-recovery.md']:
        assert canonical/relative in outputs
    script = 'hmasd-scientific-tools/scripts/summarize_runs.py'
    assert outputs[ROOT/'.claude/skills'/script] == (ROOT/'.agents/skills'/script).read_bytes().replace(b'\r\n', b'\n')
    hub = outputs[ROOT/'.claude/skills/hmasd-research-hub/SKILL.md'].decode()
    assert 'HMASDTransport' not in hub and 'send Root one paragraph' not in hub
    assert 'hmasd-experiment-tracker' in hub and publisher.CONSTITUTION in hub


def test_publication_is_independent_of_checkout_line_endings(tmp_path):
    for folder in ['.agents/skills', '.codex/agents', '.claude/agents']:
        shutil.copytree(ROOT/folder, tmp_path/folder, ignore=shutil.ignore_patterns('__pycache__'))
    publisher.publish(tmp_path)
    # Simulate an older Windows checkout with CRLF canonical files.
    for source in (tmp_path/'.agents/skills').rglob('*'):
        if source.is_file() and source.suffix in {'.md', '.py', '.yaml', '.yml', '.json', '.toml'}:
            source.write_bytes(source.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    assert publisher.publish(tmp_path, check=True) == []


def test_native_roles_preserve_complete_shared_body_without_prose_rewriting():
    outputs = publisher.generated()
    for native, shared in publisher.ROLE_MAP.items():
        body = tomllib.loads((ROOT/'.codex/agents'/f'{shared}.toml').read_text(encoding='utf-8'))['developer_instructions']
        assert body in outputs[ROOT/'.claude/agents'/f'{native}.md'].decode()
