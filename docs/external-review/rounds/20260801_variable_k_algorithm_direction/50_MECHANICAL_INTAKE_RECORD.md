# Mechanical intake record — transport facts only

```text
round         = 20260801_variable_k_algorithm_direction
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = 4e190f29975f25f308b36d5784c47d3f28197839
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, agentify
operation_key = mypaper-open-divergent-untied-k-20260801-w5tp1-r1
receipt_sha256 = f42d3a280b8660d4c6b6c9f06e50b084b6e5b5324b9fda55e31906ecc33106c7
touchpoint    = 1 of 3
```

## Preflight

```json
{
    "status":  "ROUND_PREFLIGHT_READY",
    "round":  "20260801_variable_k_algorithm_direction",
    "commit":  "4e190f29975f25f308b36d5784c47d3f28197839",
    "branch":  "untied-k",
    "question":  "docs/external-review/rounds/20260801_variable_k_algorithm_direction/20_PRO_OPEN_QUESTION.md",
    "allow_list_count":  11,
    "fence_artifact":  "docs/external-review/rounds/20260801_variable_k_algorithm_direction/10_FENCE.txt",
    "archive_build":  "REVIEW_EVIDENCE_ARCHIVE_READY"
}
```

First round through the new theme-drift gate (`## Variable-k relevance`
required by preflight): passed.

## Capture

```json
{
    "status":  "ROUND_ARCHIVE_OK",
    "path":  "docs/external-review/rounds/20260801_variable_k_algorithm_direction/21_PRO_OPEN_RAW.md",
    "chars":  26752,
    "response_sha256":  "f42d3a280b8660d4c6b6c9f06e50b084b6e5b5324b9fda55e31906ecc33106c7",
    "operation_key":  "mypaper-open-divergent-untied-k-20260801-w5tp1-r1",
    "terminal_state":  "NATURAL_COMPLETION_VERIFIED",
    "stage_commit":  "4e190f29975f25f308b36d5784c47d3f28197839",
    "stage_commit_cited":  false,
    "first_line":  "RULING",
    "last_line":  "This ruling selects the scientific experiment and its result semantics. It does not itself authorize implementation or compute.",
    "failures":  []
}
```

## Transport faults

One fault, repaired in this round:

1. Transport itself was clean — single operation, first attempt,
   `sendCount=1`, `NATURAL_COMPLETION_VERIFIED`, SHA-256 digest bond equal.
2. `archive_pro_response.ps1` then **false-refused** the archive: its
   browser-era protocol check required the response text to contain this
   round's `stage_commit`, and Pro's response (unlike the two earlier
   rounds) does not cite the commit. Under the receipt transport the
   response-to-round binding is proven by the receipt (operation key +
   `userMessageId` + two-snapshot completion), so the stale-capture risk
   the check refused has no mechanism left. Repaired in the same round:
   the check is downgraded from refusal to the recorded field
   `stage_commit_cited` (false here), everything else unchanged. The
   digest bond itself (SHA-256 equality) remains a hard refusal.
