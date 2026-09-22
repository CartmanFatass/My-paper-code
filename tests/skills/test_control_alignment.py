"""Development-only alignment regressions; no browser, launch or runtime certification."""
import importlib.util
from pathlib import Path
import shutil
import tomllib
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('alignment_publisher', ROOT/'tools/publish_claude_control.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


def native_fixture(root, monkeypatch):
    # These are exact production source files. The frontmatter below is deliberately a
    # fixture; preservation does not prove any user's effective model/effort/permissions.
    paths = [
        '.codex/agents/hmasd-direction-manager.toml',
        '.codex/agents/hmasd-reviewer.toml',
        '.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md',
    ]
    for path in paths:
        dst = root/path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/path, dst)
    roles = {'hmasd-reviewer':'hmasd-reviewer'}
    monkeypatch.setattr(publisher, 'ROLE_MAP', roles)
    header = '\nname: fixture\nmodel: fixture-model\ntools: Read, Bash\ndescription: preserve the whole native header\n'
    for role in roles:
        dst = root/'.claude/agents'/f'{role}.md'
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text('---'+header+'---\noriginal body\n')
    return header


@pytest.mark.parametrize('path', [
    '.claude/skills/hmasd-orphan/SKILL.md',
    '.claude/skills/hmasd-example/old_helper.py',
    '.claude/agents/hmasd-retired.md',
])
def test_unexpected_output_detected_without_deletion(tmp_path, monkeypatch, path):
    expected = tmp_path/'.claude/skills/hmasd-example/SKILL.md'
    expected.parent.mkdir(parents=True)
    expected.write_bytes(b'correct\n')
    ghost = tmp_path/path
    ghost.parent.mkdir(parents=True, exist_ok=True)
    ghost.write_bytes(b'preserve original bytes\n')
    monkeypatch.setattr(publisher, 'generated', lambda root: {expected:b'correct\n'})
    assert path in publisher.publish(tmp_path, check=True)
    assert path in publisher.publish(tmp_path)
    assert ghost.read_bytes() == b'preserve original bytes\n'


def test_non_hmasd_output_and_bytecode_are_not_owned(tmp_path, monkeypatch):
    for path in ['.claude/skills/another-plugin/SKILL.md',
                 '.claude/skills/hmasd-example/__pycache__/module.cpython-311.pyc',
                 '.claude/agents/unrelated.md']:
        dst=tmp_path/path; dst.parent.mkdir(parents=True, exist_ok=True);dst.write_bytes(b'x')
    monkeypatch.setattr(publisher, 'generated', lambda root:{})
    assert publisher.publish(tmp_path, check=True) == []


def test_check_does_not_overwrite_foreign_edits(tmp_path, monkeypatch):
    target=tmp_path/'.claude/skills/hmasd-example/SKILL.md'
    target.parent.mkdir(parents=True);target.write_bytes(b'foreign edit\n')
    monkeypatch.setattr(publisher, 'generated', lambda root:{target:b'expected\n'})
    assert publisher.publish(tmp_path, check=True)
    assert target.read_bytes()==b'foreign edit\n'


def test_claude_shared_writer_and_native_header(tmp_path, monkeypatch):
    header = native_fixture(tmp_path, monkeypatch)
    publisher.publish(tmp_path)
    assert publisher.publish(tmp_path, check=True) == []
    hub=(tmp_path/'.claude/skills/hmasd-research-hub/SKILL.md').read_text()
    assert "You publish your own direction's RESEARCH standing/results to main" in hub
    assert 'no Root acknowledgment is required' in hub
    assert 'You also integrate your own commits into main' not in hub
    assert 'HMASDTransport' not in hub and 'HMASDExperimentMonitor' not in hub
    assert 'hmasd-experiment-tracker' not in hub
    assert 'hmasd-pro-transport' not in publisher.ROLE_MAP
    for role in publisher.ROLE_MAP:
        assert (tmp_path/'.claude/agents'/f'{role}.md').read_text().split('---',2)[1]==header


def test_retired_wait_roles_are_not_generated(tmp_path, monkeypatch):
    native_fixture(tmp_path, monkeypatch)
    out = publisher.generated(tmp_path)
    assert tmp_path/'.claude/agents/hmasd-experiment-tracker.md' not in out
    assert tmp_path/'.claude/agents/hmasd-pro-transport.md' not in out
    assert tmp_path/'.claude/skills/hmasd-pro-transport/SKILL.md' not in out


@pytest.mark.parametrize('change', ['reword', 'repeat'])
def test_role_prose_changes_publish_without_sentence_anchors(tmp_path, monkeypatch, change):
    native_fixture(tmp_path, monkeypatch)
    path=tmp_path/'.codex/agents/hmasd-direction-manager.toml'
    text=path.read_text()
    old="You publish your own direction's RESEARCH standing/results to main; no Root acknowledgment is required."
    replacement=old+'\n'+old if change == 'repeat' else 'Publish the owned direction result entry from current main.\nRoot approval is not required.'
    path.write_text(text.replace(old, replacement, 1))
    expected=tomllib.loads(path.read_text())['developer_instructions']
    output=publisher.generated(tmp_path)
    hub=output[tmp_path/'.claude/skills/hmasd-research-hub/SKILL.md'].decode()
    assert expected in hub
    assert replacement in hub
    assert publisher.publish(tmp_path, check=True)  # New generated bytes are still detected.


def test_crlf_shared_method_does_not_change_generated_semantics(tmp_path, monkeypatch):
    native_fixture(tmp_path, monkeypatch)
    before = publisher.generated(tmp_path)
    source=tmp_path/'.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md'
    source.write_bytes(source.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
    assert publisher.generated(tmp_path)==before


@pytest.mark.parametrize('path', [
    '.agents/skills/hmasd-pro-research-prompt-author/SKILL.md',
    '.agents/skills/hmasd-portfolio-task/SKILL.md',
    '.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md',
])
def test_callers_and_consumer_share_target_fields(path):
    text=(ROOT/path).read_text()
    for field in ['repository', 'branch', 'source_sha', 'target_path', 'question_heading', 'answer_heading']:
        assert field in text


def test_both_targets_and_complete_answer_boundary_are_documented():
    text=(ROOT/'.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md').read_text()
    for term in ['NOTES.md', 'RESEARCH.md', 'immutable commit', 'against source_sha',
                 'against\n   its parent', 'short chat receipt', 'answer unavailable',
                 'Unrelated intervening commits']:
        assert term in text
    assert '`NOTES.md` section must contain the answer' not in text


def test_frozen_source_and_control_adoption_not_automatic():
    dm=(ROOT/'.codex/agents/hmasd-direction-manager.toml').read_text()
    for term in ['original card', 'owner pause first', 'no per-idea owner approval',
                 'Disk publication is not proof', 'Do not rebind, relaunch or resend']:
        assert term in dm


def test_retired_wait_roles_are_unregistered_and_absent():
    config = (ROOT/'.codex/config.toml').read_text()
    for name in ['HMASDTransport', 'HMASDExperimentMonitor']:
        assert f'[agents.{name}]' not in config
    for path in [
        '.codex/agents/hmasd-transport.toml',
        '.codex/agents/hmasd-experiment-monitor.toml',
        '.claude/agents/hmasd-pro-transport.md',
        '.claude/agents/hmasd-experiment-tracker.md',
        '.claude/skills/hmasd-pro-transport/SKILL.md',
    ]:
        assert not (ROOT/path).exists()


def test_browser_config_has_no_retired_subagent_model():
    config = tomllib.loads((ROOT/'.codex/hmasd-transport.toml').read_text())
    assert config['mode'] == 'browser_procedure'
    assert config['backend'] == 'host_specific'
    assert 'model' not in config
    assert 'reasoning_effort' not in config
    assert config['provider']['model']
