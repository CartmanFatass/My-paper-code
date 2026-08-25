# External Pro: G50 correction-recheck-v2 immutable target excerpts

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
review_scope=correction_only_recheck_v2
round=20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_correction_recheck_v2
stage_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
audit_target_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
repair_implementation_code_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
superseded_implementation_code_commit=5aeb3b7745847ca39edf556af29067506ead4c00
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

This is a bounded evidence correction. Do not reopen the G50 design, request
new code, alter thresholds or seeds, run compute, or interpret any result.
Return exactly one terminal token: `AUDIT_DISPOSITION=ALIGNED`,
`AUDIT_DISPOSITION=MISMATCH`, or `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY`.

## Immutable `git-show` excerpt A: target selector

Source: `scripts/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py`
at `b8290699f5c10c593bbc21a6666c17950fae84d3`, lines 940-958:

```python
def select_g50_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or not bool(
        metrics["reference_access_pass"]
    ):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["reference_access_pass"])
        and bool(metrics["null_access_pass"])
        and bool(metrics["fresh_single_immediate_noninferior"])
    ):
        return NULL_SUFFICIENT_BRANCH
    if bool(metrics["reference_access_pass"]) and (
        bool(metrics["null_access_confident_fail"])
        or bool(metrics["material_common_fast_anchor_advantage"])
    ):
        return REFERENCE_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH
```

## Immutable `git-show` excerpt B: focused non-confident failure witness

Source: `tests/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_test.py`
at `b8290699f5c10c593bbc21a6666c17950fae84d3`:

```python
def test_reference_access_failure_precedes_favorable_comparison_without_confidence(
    runner,
) -> None:
    assert runner.select_g50_result_branch(
        {
            "operational_valid": True,
            "source_valid": True,
            "reference_access_pass": False,
            "reference_access_confident_fail": False,
            "null_access_pass": True,
            "null_access_confident_fail": False,
            "fresh_single_immediate_noninferior": True,
            "material_common_fast_anchor_advantage": True,
        }
    ) == runner.SOURCE_FAILURE_BRANCH
```

## Immutable `git-show` excerpt C: exact repair diff

Source: `git diff --unified=8 5aeb3b7745847ca39edf556af29067506ead4c00 b8290699f5c10c593bbc21a6666c17950fae84d3`
for the selector and witness:

```diff
-    if not bool(metrics["source_valid"]) or bool(
-        metrics["reference_access_confident_fail"]
+    if not bool(metrics["source_valid"]) or not bool(
+        metrics["reference_access_pass"]
     ):
         return SOURCE_FAILURE_BRANCH
```

```diff
+def test_reference_access_failure_precedes_favorable_comparison_without_confidence(
+    runner,
+) -> None:
+    assert runner.select_g50_result_branch(
+        {
+            "operational_valid": True,
+            "source_valid": True,
+            "reference_access_pass": False,
+            "reference_access_confident_fail": False,
+            "null_access_pass": True,
+            "null_access_confident_fail": False,
+            "fresh_single_immediate_noninferior": True,
+            "material_common_fast_anchor_advantage": True,
+        }
+    ) == runner.SOURCE_FAILURE_BRANCH
```

## Single bounded question

Do these exact target-bound excerpts prove that commit
`b8290699f5c10c593bbc21a6666c17950fae84d3` closes only the original G50
code-science mismatch - absolute `not reference_access_pass` precedence with
confidence remaining diagnostic-only—without changing any other frozen G50
contract or formal authority?

Return only one of the three declared terminal tokens. Use `MISMATCH` only if
you identify a remaining exact conflict in the target bytes above or in the
allow-listed target evidence, and name that exact conflict plus its smallest
in-contract correction. Use `SCIENTIFIC_AMBIGUITY` only for one unstated,
result-changing choice that prevents this limited judgment.
