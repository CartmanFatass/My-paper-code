from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "hmasd-workflow-outsource" / "SKILL.md"
TEMPLATE = ROOT / ".agents" / "skills" / "hmasd-workflow-outsource" / "references" / "prompt-template.md"


def test_workflow_outsource_initial_contract_creates_one_native_terra_high_agent() -> None:
    skill_text = SKILL.read_text(encoding="utf-8")
    template_text = TEMPLATE.read_text(encoding="utf-8")

    assert "initial contract creates exactly one `gpt-5.6-terra` subagent with `high`" in skill_text
    assert "`gpt-5.6-terra` subagent with `high`" in skill_text
    assert "spawn_agent" in skill_text
    assert "model=gpt-5.6-terra" in skill_text
    assert "reasoning_effort=high" in skill_text
    assert "fork_turns=none" in skill_text
    assert "create_thread" in skill_text
    assert "send_message_to_thread" in skill_text
    assert "OUTSOURCE_TARGET_THREAD" not in skill_text
    assert "01a058a7-a26c-77d3-b220-d621a615df79" not in skill_text
    assert "TARGET_AGENT=<FRESH_NATIVE_TERRA_HIGH for INITIAL/REPLACEMENT" in template_text
    assert "TARGET_THREAD_ID" not in template_text
    assert "model=gpt-5.6-terra" in template_text
    assert "reasoning_effort=high" in template_text


def test_workflow_outsource_reuses_original_agent_for_same_task_follow_up() -> None:
    skill_text = SKILL.read_text(encoding="utf-8")
    template_text = TEMPLATE.read_text(encoding="utf-8")

    assert "same `REQUEST_ID` or `TASK_IDENTITY` is the same task" in skill_text
    assert "recover its original returned agent handle" in skill_text
    assert "For `FOLLOW_UP_REUSE`" in skill_text
    assert "use `followup_task`" in skill_text
    assert "Do not call `spawn_agent`" in skill_text
    assert "DISPATCH_MODE=INITIAL|FOLLOW_UP_REUSE|REPLACEMENT" in template_text
    assert "TASK_IDENTITY=<stable task identity" in template_text
    assert "original returned agent handle for FOLLOW_UP_REUSE" in template_text


def test_workflow_outsource_replaces_only_an_unrecoverable_or_unavailable_agent() -> None:
    skill_text = SKILL.read_text(encoding="utf-8")
    template_text = TEMPLATE.read_text(encoding="utf-8")

    assert "only when the original handle cannot be\nrecovered or is unavailable" in skill_text
    assert "Do not create a replacement for a busy agent" in skill_text
    assert "record the original handle (if known) and a concrete" in skill_text
    assert "replacement_reason" in skill_text
    assert "REPLACEMENT_REASON=<NONE unless DISPATCH_MODE=REPLACEMENT" in template_text
    assert "replacement_reason=<NONE unless replacement" in template_text
