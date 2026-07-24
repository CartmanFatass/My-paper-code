# Mechanical intake record

```text
record_owner=project_manager
record_scope=transport_provenance_only
scientific_classification=none
```

## Source identity

```text
repository=CartmanFatass/My-paper-code
branch=aggressive
round=20260723_uav_charge_rotation_g2_evidence_contract
stage_commit=68d16b62f980c3be264a4e4d77ef3517969da290
question=docs/external-review/rounds/20260723_uav_charge_rotation_g2_evidence_contract/20_PRO_OPEN_QUESTION.md
raw=docs/external-review/rounds/20260723_uav_charge_rotation_g2_evidence_contract/21_PRO_OPEN_RAW.md
registered_conversation_id=6a5a7735-ab30-83e8-bb88-d0cfb3cea56c
```

The remote evidence-boundary verifier returned `REMOTE_EVIDENCE_READY` for the
stage commit and registered question. The exact freshness fence was absent from
the readable conversation history, submitted once, and then observed as one
visible user turn with all identity fields unchanged.

## Stable response evidence

```text
assistant_message_id=a85de940-8652-4140-a5bc-bee9e110bfb2
stable_snapshot_count=2
stable_snapshot_interval_seconds=4
visible_text_characters=18005
same_message_id=true
visible_text_equal=true
active_stop_control=false
retry_control=false
continue_generation_control=false
transport_recovery=none
```

The stable visible response was written without paraphrase to the raw path and
reread against the captured response. The repository file has only the normal
terminal LF added by the patch writer; all 18,005 visible response characters
are identical and in the same order.

No Project-Manager heartbeat was created, so heartbeat cleanup is vacuously
complete. This record makes no judgment about scientific completeness or
adoption; those belong to the subsequent Project Manager reconciliation.
