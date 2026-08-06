"""Proof-sized tests for the pre-dispatch gate.

Three tests carry the design.

``test_a_number_that_was_never_computed_blocks_dispatch`` is the whole point:
the gate exists because a hand-typed table reached External Pro and a
hand-typed table is where a transcription error lives.

``test_a_rounded_quotation_of_a_computed_value_is_traceable`` protects it from
being disabled: a checker that rejected ``4.4675`` because the artifact holds
``4.467461307208166`` would be turned off within a day.

``test_a_missing_document_review_blocks_dispatch`` pins the other half. The
number check proves each figure was computed; only a clean-context reader
proves the prose describes the code that computed it, and every registration
round rejected for a prose/code mismatch would have been visible to one.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

_SCRIPT = (
    pathlib.Path(__file__).resolve().parents[2]
    / ".claude"
    / "skills"
    / "hmasd-science-dispatch"
    / "scripts"
    / "hmasd_dispatch_receipt.py"
)
_spec = importlib.util.spec_from_file_location("_hmasd_dispatch_receipt", _SCRIPT)
gate = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(gate)


def _item(
    tmp_path: pathlib.Path,
    *,
    question: str,
    truth: dict | None = None,
    manifest_extra: dict | None = None,
    review: str | None = gate.DOCUMENT_REVIEW_ACCEPTS,
) -> tuple[pathlib.Path, pathlib.Path]:
    """A minimal review item rooted at its own temporary repository."""
    root = tmp_path
    item = root / "local_research" / "pro_reviews" / "example_v1"
    item.mkdir(parents=True)
    (item / "20_RAW_QUESTION.md").write_text(question, encoding="utf-8")
    if review is not None:
        (item / "15_DOCUMENT_REVIEW.md").write_text(
            f"Read both sides.\n\n{review}\n", encoding="utf-8"
        )
    manifest: dict = {"truth_sources": []}
    if truth is not None:
        (root / "truth.json").write_text(json.dumps(truth), encoding="utf-8")
        manifest["truth_sources"] = [{"kind": "json", "path": "truth.json"}]
    manifest.update(manifest_extra or {})
    (item / gate.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    return root, item


def test_a_number_that_was_never_computed_blocks_dispatch(tmp_path):
    """The transcription error the gate exists to catch."""
    root, item = _item(
        tmp_path,
        question="The across-seed mean contrast was 4.4675 and the range top was 9.9999.",
        truth={"mean": 4.467461307208166, "maximum": 4.755110466846061},
    )
    receipt = gate.build_receipt(item, root=root)

    assert receipt["terminal"] == "DISPATCH_BLOCKED"
    untraceable = {row["literal"] for row in receipt["number_traceability"]["untraceable"]}
    assert untraceable == {"9.9999"}


def test_a_rounded_quotation_of_a_computed_value_is_traceable(tmp_path):
    """`4.4675` IS `4.467461307208166` at the document's own precision."""
    root, item = _item(
        tmp_path,
        question="mean 4.4675, max 4.7551, exactly 0.5252223610877991",
        truth={
            "mean": 4.467461307208166,
            "maximum": 4.755110466846061,
            "contrast": 0.5252223610877991,
        },
    )
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_PERMITTED"
    assert receipt["number_traceability"]["untraceable"] == []


def test_a_derived_number_needs_a_command_that_derives_it(tmp_path):
    """A t-interval endpoint is in no artifact; declaring its derivation is the point.

    The endpoints here are the real UCOPE ones. Writing this test is what
    revealed that the upper endpoint quoted in the external ruling, 4.6543, is a
    one-digit rounding slip: mean 4.467461307208166 plus half-width
    0.18677317129844437 is 4.65423447850661, which renders as 4.6542 at four
    decimals, and no plausible critical value moves it (the half-width would
    have to reach 0.18678869). Caught by the gate on its first real use, which
    is the argument for the gate.
    """
    question = "Student-t 95% interval 4.2807-4.6542."
    root, item = _item(
        tmp_path, question=question, truth={"mean": 4.467461307208166}
    )
    assert gate.build_receipt(item, root=root)["terminal"] == "DISPATCH_BLOCKED"

    manifest = json.loads((item / gate.MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest["truth_sources"].append(
        {
            "kind": "command",
            "argv": [
                sys.executable,
                "-c",
                "m=4.467461307208166; h=0.18677317129844437; print(m-h, m+h)",
            ],
        }
    )
    (item / gate.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    assert gate.build_receipt(item, root=root)["terminal"] == "DISPATCH_PERMITTED"


def test_an_integer_is_matched_exactly_and_never_by_prefix(tmp_path):
    """Prefix matching would let the registered budget 300 pass against 30012345."""
    root, item = _item(
        tmp_path,
        question="Trained for 300 iterations.",
        truth={"unrelated": 30012345},
    )
    assert gate.build_receipt(item, root=root)["terminal"] == "DISPATCH_BLOCKED"

    (root / "truth.json").write_text(json.dumps({"iterations": 300}), encoding="utf-8")
    assert gate.build_receipt(item, root=root)["terminal"] == "DISPATCH_PERMITTED"


def test_a_digest_is_matched_by_prefix_because_that_is_how_it_is_quoted(tmp_path):
    full = "1f08308e0d7eaedfd4cfab428908e9e0ea8eb34356aa2b61f693969d5184f606"
    root, item = _item(
        tmp_path,
        question=f"sha256 `{full[:8]}...` archived.",
        truth={"sha256": full},
    )
    assert gate.build_receipt(item, root=root)["terminal"] == "DISPATCH_PERMITTED"

    (root / "truth.json").write_text(json.dumps({"sha256": "aaaa" + full[4:]}), encoding="utf-8")
    assert gate.build_receipt(item, root=root)["terminal"] == "DISPATCH_BLOCKED"


def test_prose_structure_is_below_the_substantive_floor(tmp_path):
    """A checker with false positives gets disabled, so the floor is real.

    Section numbers, list markers, ISO dates and small counts must not have to
    be whitelisted one by one.
    """
    question = (
        "## 3.4 The gate\n\n"
        "1. First item\n"
        "2. Second item\n\n"
        "On 2026-08-06 the four rounds closed. See https://example.com/c/6a73a3d1.\n"
    )
    root, item = _item(tmp_path, question=question, truth={})
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_PERMITTED"


def test_the_whitelist_records_what_nobody_recomputed(tmp_path):
    """Whitelisting is allowed, but it is a list, and the list is in the receipt."""
    root, item = _item(
        tmp_path,
        question="Four registration rounds, 2 of them avoidable, 1000 lines.",
        truth={},
        manifest_extra={"whitelist": {"1000": "prose approximation of file size"}},
    )
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_PERMITTED"
    assert receipt["number_traceability"]["whitelisted"] == ["1000"]


def test_a_failing_precondition_blocks_dispatch(tmp_path):
    """The boundary/cleanliness/test bundle is enforced, not reported."""
    root, item = _item(
        tmp_path,
        question="No numbers here.",
        truth={},
        manifest_extra={
            "preconditions": [
                {"name": "always_fails", "argv": [sys.executable, "-c", "raise SystemExit(3)"]}
            ]
        },
    )
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_BLOCKED"
    assert receipt["preconditions"]["checks"][0]["name"] == "always_fails"


def test_a_precondition_may_require_empty_output(tmp_path):
    """`git diff --stat -- <codex paths>` must print nothing, not merely exit 0."""
    root, item = _item(
        tmp_path,
        question="No numbers here.",
        truth={},
        manifest_extra={
            "preconditions": [
                {
                    "name": "boundary_diff_empty",
                    "argv": [sys.executable, "-c", "print('unexpected change')"],
                    "expect_empty_stdout": True,
                }
            ]
        },
    )
    assert gate.build_receipt(item, root=root)["terminal"] == "DISPATCH_BLOCKED"


def test_a_missing_document_review_blocks_dispatch(tmp_path):
    root, item = _item(tmp_path, question="No numbers.", truth={}, review=None)
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_BLOCKED"
    assert "mandatory" in receipt["document_review"]["detail"]


def test_a_document_review_that_found_a_mismatch_blocks_dispatch(tmp_path):
    root, item = _item(
        tmp_path, question="No numbers.", truth={}, review="DOCUMENT_MISMATCH"
    )
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_BLOCKED"
    assert receipt["document_review"]["terminal"] == "DOCUMENT_MISMATCH"


def test_waiving_the_document_review_costs_a_written_reason(tmp_path):
    """An off switch anybody can flip silently is not an escape hatch.

    The clean-context review is a MUST in the workflow, and this script is what
    the workflow cites as its mechanical backstop. A bare
    ``document_review_required: false`` therefore blocks; a waiver with a reason
    passes and the reason travels in the receipt where a later reader sees it.
    """
    root, item = _item(
        tmp_path,
        question="No numbers.",
        truth={},
        review=None,
        manifest_extra={"document_review_required": False},
    )
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_BLOCKED"
    assert "silent waiver is refused" in receipt["document_review"]["detail"]

    manifest = json.loads((item / gate.MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest["document_review_waiver_reason"] = (
        "config-lane edit with no outgoing claim about source behaviour"
    )
    (item / gate.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    receipt = gate.build_receipt(item, root=root)
    assert receipt["terminal"] == "DISPATCH_PERMITTED"
    assert receipt["document_review"]["waiver_reason"].startswith("config-lane")


def test_a_missing_manifest_is_an_error_not_a_pass(tmp_path):
    """Fail closed: no manifest must never read as 'nothing to check'."""
    item = tmp_path / "local_research" / "pro_reviews" / "empty_v1"
    item.mkdir(parents=True)
    with pytest.raises(gate.GateError, match=gate.MANIFEST_NAME):
        gate.build_receipt(item, root=tmp_path)


def test_a_missing_truth_source_is_an_error_not_a_pass(tmp_path):
    """The same failure mode one level down."""
    root, item = _item(tmp_path, question="4.4675", truth={})
    manifest = json.loads((item / gate.MANIFEST_NAME).read_text(encoding="utf-8"))
    manifest["truth_sources"] = [{"kind": "json", "path": "absent.json"}]
    (item / gate.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(gate.GateError, match="absent.json"):
        gate.build_receipt(item, root=root)


def test_a_figure_that_ends_a_sentence_is_still_checked():
    r"""The hole the first draft had, pinned.

    ``(?![\w.])`` after the decimals skipped every number written as
    ``4.4675.`` -- which is most numbers in prose. A gate that silently stops
    checking is worse than no gate, because it reports a pass.
    """
    found = gate.document_literals(
        "The contrast was 9.9999. The budget was 300. Commit bea06c27.",
        skip_patterns=(),
    )
    assert "9.9999" in found["floats"]
    assert "300" in found["integers"]
    assert "bea06c27" in found["hex"]


def test_a_version_like_triple_is_not_read_as_a_figure():
    """The guard the sentence-final fix had to keep."""
    found = gate.document_literals("torch 2.7.0 and numpy 1.26.3", skip_patterns=())
    assert found["floats"] == set()


def test_the_integer_rule_does_not_harvest_the_head_of_a_float():
    found = gate.document_literals("value 4.4675 alone", skip_patterns=())
    assert found["integers"] == set()
    assert found["floats"] == {"4.4675"}
