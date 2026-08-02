# Mechanical intake record — transport facts only

```text
round         = 20260801_vk0_result_disposition
reviewer_key  = open_divergent
branch        = untied-k
conversation  = 6a63979e-35d8-83e8-8da7-10de59a5fdeb
stage_commit  = 0670b81d2efb09076174f671bc01487a30e0ab96
question      = 20_PRO_OPEN_QUESTION.md
raw           = 21_PRO_OPEN_RAW.md
transport     = project_manager_direct, agentify
operation_key = mypaper-open-divergent-untied-k-20260801-w5tp3-r1
receipt_sha256 = 2d157b30259e5cd61c24585191668e0247444cc5054beb3a58855984658e0fb8
touchpoint    = 3 of 3
```

## Preflight

```json
{
    "status":  "ROUND_PREFLIGHT_READY",
    "round":  "20260801_vk0_result_disposition",
    "commit":  "0670b81d2efb09076174f671bc01487a30e0ab96",
    "branch":  "untied-k",
    "allow_list_count":  11,
    "archive_build":  "REVIEW_EVIDENCE_ARCHIVE_READY"
}
```

## Capture

```json
{
    "status":  "ROUND_ARCHIVE_OK",
    "path":  "docs/external-review/rounds/20260801_vk0_result_disposition/21_PRO_OPEN_RAW.md",
    "chars":  14020,
    "response_sha256":  "2d157b30259e5cd61c24585191668e0247444cc5054beb3a58855984658e0fb8",
    "operation_key":  "mypaper-open-divergent-untied-k-20260801-w5tp3-r1",
    "terminal_state":  "NATURAL_COMPLETION_VERIFIED",
    "stage_commit":  "0670b81d2efb09076174f671bc01487a30e0ab96",
    "stage_commit_cited":  false,
    "first_line":  "DISPOSITION",
    "failures":  []
}
```

## Transport faults

none — single operation, first attempt, `sendCount=1`,
`NATURAL_COMPLETION_VERIFIED`, digest bond equal.
