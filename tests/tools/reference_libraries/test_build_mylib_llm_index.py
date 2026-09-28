"""Focused tests for the My-lib LLM index builder and search (no network, no real PDFs)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[3] / "tools" / "reference_libraries"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"_mylib_{name}", TOOLS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B = _load("build_mylib_llm_index")
S = _load("search_mylib")


def _event(role: str, text: str, cost: float = 0.0, stop: str = "stop", **extra) -> str:
    message = {"role": role, "content": [{"type": "text", "text": text, "textSignature": "sig"}]}
    if role == "assistant":
        message.update({"usage": {"cost": {"total": cost}}, "stopReason": stop, "model": "m", "provider": "p"})
        message.update(extra)
    return json.dumps({"type": "message_end", "message": message})


def _stream(*assistant_texts, cost=0.002, stop="stop", **extra) -> str:
    lines = [json.dumps({"type": "session"}), json.dumps({"type": "agent_start"}), _event("user", "prompt")]
    for text in assistant_texts:
        lines.append(json.dumps({"type": "message_update"}))
        lines.append(_event("assistant", text, cost, stop, **extra))
    lines.append(json.dumps({"type": "agent_end", "messages": []}))
    return "\n".join(lines) + "\n"


def _valid_hint(**overrides):
    hint = {
        "problem_setting": "Cooperative multi-UAV coverage with partial observability.",
        "method_summary": "A hierarchical MARL method where a high-level policy assigns skills to each UAV.",
        "key_mechanism": "Skill assignment by a centralized high-level selector.",
        "mechanism_keywords": ["skill assignment", "hierarchical MARL", "UAV coverage"],
        "marl_setting": "cooperative",
        "topics": ["MARL", "hierarchical-RL", "multi-robot-UAV"],
        "hmasd_relevance": 3,
        "hmasd_relevance_reason": "Directly about hierarchical skill coordination for UAV swarms.",
        "one_line_hint": "hierarchical MARL skill assignment for multi-UAV coverage",
        "confidence": "high",
    }
    hint.update(overrides)
    return hint


# ------------------------------------------------------------------ omp NDJSON parser

def test_parse_takes_last_assistant_text_and_sums_cost():
    parsed = B.parse_omp_ndjson(_stream('{"a": 1}', '{"b": 2}', cost=0.0025) + "not json\n")
    assert parsed["found"] is True
    assert parsed["text"] == '{"b": 2}'
    assert parsed["cost"] == pytest.approx(0.005)
    assert parsed["stop_reason"] == "stop"
    assert parsed["bad_lines"] == 1


def test_parse_ignores_user_message_and_reports_missing_assistant():
    stdout = "\n".join([json.dumps({"type": "session"}), _event("user", "hello")])
    parsed = B.parse_omp_ndjson(stdout)
    assert parsed["found"] is False and parsed["text"] == "" and parsed["cost"] == 0.0


class _Proc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


@pytest.mark.parametrize("proc, kind", [
    (_Proc(124, ""), "timeout"),
    (_Proc(1, "", 'Model "x" not found'), "exit"),
    (_Proc(1, "", "HTTP 429 Too Many Requests"), "rate_limit"),
    (_Proc(1, "", "401 Unauthorized: credential expired"), "auth"),
    (_Proc(0, json.dumps({"type": "session"})), "no_message"),
    (_Proc(0, _stream("", stop="error", errorMessage="RESOURCE_EXHAUSTED")), "rate_limit"),
    (_Proc(0, _stream("", stop="error", errorMessage="boom")), "stop_error"),
])
def test_call_omp_classifies_infrastructure_errors(monkeypatch, tmp_path, proc, kind):
    monkeypatch.setattr(B.subprocess, "run", lambda *a, **k: proc)
    with pytest.raises(B.OmpError) as info:
        B.call_omp("p", "m", "medium", tmp_path)
    assert info.value.kind == kind


def test_call_omp_success_and_command_shape(monkeypatch, tmp_path):
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return _Proc(0, _stream('{"x": 1}', cost=0.001))

    monkeypatch.setattr(B.subprocess, "run", fake_run)
    parsed = B.call_omp("PROMPT", "gemini-3.8-flash", "medium", tmp_path)
    assert parsed["text"] == '{"x": 1}'
    cmd = seen["cmd"]
    assert cmd[:4] == ["timeout", "-k", "10", "120"]
    assert cmd[cmd.index("--model") + 1] == "gemini-3.8-flash"
    assert cmd[cmd.index("--thinking") + 1] == "medium"
    assert cmd[cmd.index("--cwd") + 1] == str(tmp_path)
    assert "--no-tools" in cmd and "--no-session" in cmd and cmd[cmd.index("--mode") + 1] == "json"
    assert cmd[-1] == "PROMPT"


# ------------------------------------------------------------------ hint validation

def test_valid_hint_passes():
    assert B.validate_hint(_valid_hint()) == []


@pytest.mark.parametrize("hint, fragment", [
    ({k: v for k, v in _valid_hint().items() if k != "confidence"}, "missing keys: confidence"),
    (_valid_hint(extra="x"), "unexpected keys: extra"),
    (_valid_hint(problem_setting="word " * 41), "problem_setting has 41 words"),
    (_valid_hint(one_line_hint="w " * 31), "one_line_hint has 31 words"),
    (_valid_hint(mechanism_keywords=["a", "b"]), "need 3 to 8"),
    (_valid_hint(mechanism_keywords=["a", "b", "one two three four five six seven"]), "over 6 words"),
    (_valid_hint(marl_setting="decentralized"), "marl_setting"),
    (_valid_hint(topics=["MARL", "swarms"]), "fixed vocabulary"),
    (_valid_hint(topics=["MARL"]), "need 2 to 6"),
    (_valid_hint(topics=["MARL", "MARL"]), "duplicates"),
    (_valid_hint(hmasd_relevance=4), "integer 0-3"),
    (_valid_hint(hmasd_relevance="3"), "integer 0-3"),
    (_valid_hint(hmasd_relevance=True), "integer 0-3"),
    (_valid_hint(confidence="certain"), "confidence"),
    (_valid_hint(key_mechanism=""), "non-empty string"),
])
def test_invalid_hints_are_reported(hint, fragment):
    errors = B.validate_hint(hint)
    assert any(fragment in e for e in errors), errors


def test_extract_json_tolerates_fences_and_prose():
    assert B.extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert B.extract_json_object('Here: {"a": {"b": 2}} done') == {"a": {"b": 2}}
    with pytest.raises(ValueError):
        B.extract_json_object("no object")


def test_prompt_carries_vocabulary_caps_and_paper_text():
    row = {"title": "T", "venue": "ICML", "year": 2024, "abstract": "abs"}
    prompt = B.build_prompt(row, "x" * 7000 + "\x00\x0c")
    assert "HARD LIMIT 40 words" in prompt and "hierarchical-RL" in prompt and "theory-only" in prompt
    assert "Venue: ICML 2024" in prompt
    assert "x" * 6000 in prompt and "x" * 6001 not in prompt and "\x00" not in prompt
    assert "not a review" in B.SYSTEM_PROMPT
    assert len(B.prompt_version()) == 12


# ------------------------------------------------------------------ catalog join

def _fake_corpus(tmp_path):
    root = tmp_path / "papers"
    files = {
        "iclr-2024/iclr-2024-virtual-1/arxiv-2401.00001.pdf": b"fake",
        "neurips-2025/abc123/arxiv-2502.12345.pdf": b"fake2",
        "2408.01072.pdf": b"loose",
    }
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    matches = {
        "2401.00001": {"venue": "ICLR", "year": 2024, "official_id": "iclr-2024-virtual-1", "title": "Paper One",
                       "authors": [], "official_url": "u1", "title_screen_hits": ["reinforcement"],
                       "arxiv": {"arxiv_id": "2401.00001", "title": "Paper One", "summary": "Sum one",
                                 "authors": ["A"], "published": "1 Jan, 2024"}},
        "2502.12345": {"venue": "NeurIPS", "year": 2025, "official_id": "different-id", "title": "Paper Two",
                       "authors": ["B"], "official_url": "u2", "title_screen_hits": ["multi-agent"],
                       "arxiv": {"arxiv_id": "2502.12345", "title": "Paper Two", "summary": "", "authors": [],
                                 "published": ""}},
    }
    return root, matches


def test_catalog_join_matched_and_loose(tmp_path):
    root, matches = _fake_corpus(tmp_path)
    pdfs = list(root.rglob("*.pdf"))
    info = {"2408.01072.pdf": {"pages": 34, "title": "A Survey on Self-play"}}
    rows, stats = B.build_catalog_rows(pdfs, matches, root,
                                       info_fn=lambda p: info.get(p.name, {"pages": None, "title": None}),
                                       text_fn=lambda p, a, b: "")
    assert [r["id"] for r in rows] == ["iclr-2024-virtual-1", "loose-2408.01072", "neurips-2025-different-id"]
    assert rows[2]["official_id"] == "different-id" and rows[0]["official_id"] == "iclr-2024-virtual-1"
    one = rows[0]
    assert one["venue"] == "ICLR" and one["year"] == 2024 and one["title"] == "Paper One"
    assert one["abstract"] == "Sum one" and one["authors"] == ["A"] and one["published"] == "1 Jan, 2024"
    assert one["pdf_bytes"] == 4 and one["pages"] is None and one["pdf_path"].endswith("arxiv-2401.00001.pdf")
    two = rows[2]
    assert two["authors"] == ["B"] and two["abstract"] is None and two["published"] is None
    loose = rows[1]
    assert loose["title"] == "A Survey on Self-play" and loose["pages"] == 34
    assert loose["venue"] is None and loose["arxiv_id"] is None and loose["abstract"] is None
    assert stats["pdfs"] == 3 and stats["matched"] == 2 and stats["loose"] == 1
    assert stats["dir_id_mismatch"] == 1 and stats["pages_null"] == 2 and stats["duplicate_ids"] == []


def test_catalog_id_disambiguates_hash_ids_reused_across_venues():
    a = {"venue": "ICLR", "year": 2024, "official_id": "121db870b0470dd63bb5bc59c724275a"}
    b = {"venue": "NeurIPS", "year": 2023, "official_id": "121db870b0470dd63bb5bc59c724275a"}
    assert B.catalog_id(a) == "iclr-2024-121db870b0470dd63bb5bc59c724275a"
    assert B.catalog_id(b) == "neurips-2023-121db870b0470dd63bb5bc59c724275a"
    assert B.catalog_id({"venue": "ICML", "year": 2023, "official_id": "icml-2023-virtual-5"}) == "icml-2023-virtual-5"


def test_loose_title_falls_back_to_first_page():
    assert B.first_page_title("arXiv:2408.01072v4 [cs.AI]\n\nA Survey on Self-Play Methods\nAuthor") == \
        "A Survey on Self-Play Methods"


def test_load_matches_indexes_by_arxiv_id(tmp_path):
    path = tmp_path / "m.json"
    path.write_text(json.dumps({"matches": [{"official_id": "a", "arxiv": {"arxiv_id": "1"}},
                                            {"official_id": "b"}, {"official_id": "c", "arxiv": None}]}))
    assert list(B.load_matches(path)) == ["1"]


# ------------------------------------------------------------------ hints pipeline with a fake caller

def _catalog_dir(tmp_path, n=3):
    out = tmp_path / "out"
    out.mkdir()
    rows = [{"id": f"p{i}", "venue": "ICML", "year": 2024, "title": f"Title {i}", "arxiv_id": None,
             "abstract": "abs", "pdf_path": str(tmp_path / f"p{i}.pdf")} for i in range(n)]
    B.write_jsonl(out / "catalog.jsonl", rows)
    return out, rows


def _args(out, tmp_path, **kw):
    base = dict(out=str(out), omp_cwd=str(tmp_path / "cwd"), workers=2, limit=None, ids=None, cost_cap_usd=25.0,
                max_consecutive_infra_errors=5, model="gemini-3.8-flash", thinking="medium", dry_run=False,
                corpus_root=str(tmp_path), matches_json=str(tmp_path / "m.json"))
    base.update(kw)
    return argparse.Namespace(**base)


def test_hint_one_retries_once_with_validation_error(tmp_path):
    prompts = []
    replies = iter([json.dumps(_valid_hint(topics=["swarm"])), json.dumps(_valid_hint())])

    def caller(prompt, model, thinking, cwd):
        prompts.append(prompt)
        return {"text": next(replies), "cost": 0.002, "model": "m", "provider": "p"}

    hints = tmp_path / "hints"
    hints.mkdir()
    res = B.hint_one({"id": "p0", "title": "T", "pdf_path": "x.pdf"}, hints, "m", "medium", tmp_path,
                     caller=caller, text_fn=lambda p, a, b: "body")
    assert res["status"] == "ok" and res["attempts"] == 2 and res["cost_usd"] == pytest.approx(0.004)
    assert "fixed vocabulary" in prompts[1] and prompts[1].startswith(prompts[0])
    rec = json.loads((hints / "p0.json").read_text())
    assert rec["hint"]["hmasd_relevance"] == 3 and rec["prompt_version"] == B.prompt_version()


def test_hint_one_writes_error_file_after_second_failure_and_on_infra_error(tmp_path):
    hints = tmp_path / "hints"
    hints.mkdir()
    res = B.hint_one({"id": "bad", "title": "T", "pdf_path": "x"}, hints, "m", "medium", tmp_path,
                     caller=lambda *a: {"text": "not json", "cost": 0.001}, text_fn=lambda p, a, b: "")
    assert res["status"] == "error" and res["error_kind"] == "validation" and res["attempts"] == 2
    assert json.loads((hints / "bad.error.json").read_text())["raw_output"] == "not json"

    def infra(*a):
        raise B.OmpError("rate_limit", "429", 0.0)

    res = B.hint_one({"id": "inf", "title": "T", "pdf_path": "x"}, hints, "m", "medium", tmp_path,
                     caller=infra, text_fn=lambda p, a, b: "")
    assert res["status"] == "error" and res["error_kind"] == "rate_limit" and res["attempts"] == 1
    assert (hints / "inf.error.json").exists() and not (hints / "inf.json").exists()


def test_cmd_hints_resumes_and_honours_cost_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "pdf_text", lambda p, a=1, b=2: "body")
    out, rows = _catalog_dir(tmp_path, n=4)
    calls = []

    def caller(prompt, model, thinking, cwd):
        calls.append(prompt)
        return {"text": json.dumps(_valid_hint()), "cost": 0.01}

    s1 = B.cmd_hints(_args(out, tmp_path, limit=2, workers=1), caller=caller)
    assert s1["ok"] == 2 and len(calls) == 2
    s2 = B.cmd_hints(_args(out, tmp_path, workers=1, cost_cap_usd=0.03), caller=caller)
    assert s2["ok"] == 1 and s2["not_started"] == 1 and "cost cap" in s2["stopped"]
    assert len(B.read_jsonl(out / "build_log.jsonl")) == 3
    with pytest.raises(SystemExit):
        B.cmd_hints(_args(out, tmp_path, workers=1, cost_cap_usd=0.03), caller=caller)


def test_cmd_hints_stops_on_consecutive_infra_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "pdf_text", lambda p, a=1, b=2: "body")
    out, rows = _catalog_dir(tmp_path, n=6)

    def caller(*a):
        raise B.OmpError("auth", "401 unauthorized")

    s = B.cmd_hints(_args(out, tmp_path, workers=1, max_consecutive_infra_errors=2), caller=caller)
    assert s["error"] == 2 and s["not_started"] == 4 and "consecutive" in s["stopped"]


def test_navigate_and_search(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(B, "pdf_text", lambda p, a=1, b=2: "body")
    out, rows = _catalog_dir(tmp_path, n=3)
    replies = {"Title 0": _valid_hint(),
               "Title 1": _valid_hint(hmasd_relevance=0, topics=["bandits", "theory"], marl_setting="bandit",
                                      one_line_hint="regret bounds for linear bandits",
                                      problem_setting="Stochastic linear bandits.",
                                      method_summary="An optimistic algorithm with confidence ellipsoids.",
                                      key_mechanism="Optimism in the face of uncertainty.",
                                      hmasd_relevance_reason="Single-learner bandit theory.",
                                      mechanism_keywords=["linear bandit", "regret", "UCB"])}

    def caller(prompt, model, thinking, cwd):
        for title, hint in replies.items():
            if f"Title: {title}\n" in prompt:
                return {"text": json.dumps(hint), "cost": 0.001}
        return {"text": "garbage", "cost": 0.001}

    B.cmd_hints(_args(out, tmp_path, workers=2), caller=caller)
    # A stale error file for an id that later succeeded must not count as a failure.
    (out / "hints" / "p0.error.json").write_text(json.dumps({"id": "p0", "status": "error", "error_kind": "timeout"}))
    stats = B.cmd_navigate(_args(out, tmp_path))
    assert stats["hints_ok"] == 2 and stats["hints_error"] == 1 and stats["pending"] == 0
    assert stats["relevance_counts"][3] == 1 and stats["relevance_counts"][0] == 1
    merged = B.read_jsonl(out / "hints.jsonl")
    assert [r["id"] for r in merged] == ["p0", "p1"] and merged[0]["title"] == "Title 0"
    topic_md = (out / "INDEX_BY_TOPIC.md").read_text()
    assert "## multi-robot-UAV (1)" in topic_md and "p0 — Title 0 (ICML 2024)" in topic_md
    rel_md = (out / "INDEX_BY_RELEVANCE.md").read_text()
    assert "## Relevance 3 (1)" in rel_md and "p1" not in rel_md
    readme = (out / "README.md").read_text()
    assert "they are not evidence" in readme and "a miss says nothing beyond this" in readme.lower()
    assert "Failed ids: p2" in readme and B.prompt_version() in readme

    idx = S.load_index(out)
    assert [r["id"] for r in S.search(idx, ["UAV", "hierarchical"])] == ["p0"]
    assert [r["id"] for r in S.search(idx, ["bandit"])] == ["p1"]
    assert S.search(idx, ["uav", "regret"]) == []
    # The relevance reason explains non-relevance in HMASD vocabulary; it must not create matches.
    assert S.search(idx, ["single-learner"]) == []
    assert [r["id"] for r in S.search(idx, ["title"], min_relevance=1)] == ["p0"]
    assert [r["id"] for r in S.search(idx, [], topics=["theory"])] == ["p1"]
    capsys.readouterr()
    assert S.main(["--out", str(out), "multi-uav"]) == 0
    line = capsys.readouterr().out.strip()
    assert line.startswith("p0 | ICML-2024 | Title 0 | ") and line.endswith("multi-UAV coverage")
    assert S.main(["--out", str(out), "--json", "bandit"]) == 0
    assert json.loads(capsys.readouterr().out.strip())["id"] == "p1"
