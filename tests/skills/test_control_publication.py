"""Development-only publication checks; no scientific launch integration."""
import importlib.util
from pathlib import Path
import shutil

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


def test_generated_helpers_resolve_in_complete_skill_tree():
    outputs = publisher.generated()
    canonical = ROOT/'.claude/skills/hmasd-chatgpt-pro-transport'
    for relative in ['scripts/native_transport.py','references/agentify.md','references/unrecoverable-conversation.md']:
        assert canonical/relative in outputs
    # Shared publication preserves executable helper bytes, not a pointer shell.
    script = 'hmasd-pro-research-prompt-author/scripts/render_packet.py'
    assert outputs[ROOT/'.claude/skills'/script] == (ROOT/'.agents/skills'/script).read_bytes().replace(b'\r\n', b'\n')


def test_publication_is_independent_of_checkout_line_endings(tmp_path):
    for folder in ['.agents/skills', '.codex/agents', '.claude/agents']:
        shutil.copytree(ROOT/folder, tmp_path/folder, ignore=shutil.ignore_patterns('__pycache__'))
    publisher.publish(tmp_path)
    # Simulate an older Windows checkout with CRLF canonical files.
    for source in (tmp_path/'.agents/skills').rglob('*'):
        if source.is_file() and source.suffix in {'.md', '.py', '.yaml', '.yml', '.json', '.toml'}:
            source.write_bytes(source.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    assert publisher.publish(tmp_path, check=True) == []
