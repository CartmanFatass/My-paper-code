# Incident Scope and Recovery Policy

## Levels and routes

| Level | Meaning | Default route |
|---|---|---|
| `E0_OBSERVATION` | fact or anomaly without an action fence | current executor |
| `E1_EXACT_OPERATION_INCIDENT` | one request/process/file/tab/command cannot continue | operator/transport/leaf or recovery owner |
| `E2_ASSIGNMENT_RECOVERY` | current assignment/component needs repair | CM or Workflow Recovery Manager |
| `E3_DOMAIN_OWNER_DECISION` | technical contract or scientific definition may change | CM or EM |
| `E4_CROSS_OWNER_DECISION` | shared resource or owner coordination | Root or Portfolio |
| `E5_USER_AUTHORITY_REQUIRED` | existing owners lack authority | user, with a concrete question |

E0/E1 never jump directly to E5. E2 cannot pause, retire, or scientifically
terminate a direction. Technical E3 cannot create a scientific disposition.
Only an observed authority gap may produce E5. Every boundary report names its
object, affected and unaffected actions, recovery owner, escalation condition,
and `does_not_imply` list.

The exact-operation no-resend fence applies only to that operation identity; it
does not forbid non-sending observation, local repair, unchanged-science work,
or a separately authorized future operation.
