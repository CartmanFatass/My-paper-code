---
name: hmasd-root-control
description: Use when Root must reconcile one exact HMASD work item, dispatch its closed plan, or record a user-authorized decision.
---

# HMASD Root Control

For one exact `work_id`, first freshly observe native tasks and the relevant
authority/Effect facts. Preserve Root's runtime task mapping with its existing
`tasks.json` CAS.

1. Run Work Packet `reconcile --once` with the explicit observed-task snapshot
   and any typed return/draft. Do not scan ready work or infer a target.
2. Execute only its closed plan through `hmasd_codex_tasks execute-plan`, with
   the exact packet locator, cwd, fresh observations, and known peer work IDs.
   The adapter's short lock and comparator permit disjoint work; overlap is a
   conflict unless Root supplies `--root-override-reason` for an exact
   owned-path comparator conflict or `ACTIVE_PEER_OBSERVATION_UNKNOWN`. The
   adapter records its reason/warning in native history; this is not a
   pre-dispatch acknowledgment or gate.
3. If the override itself is a material decision, its owner records it in the
   appropriate existing authority after the fact. Freshly observe every
   send/create/wait result. Hard Effect identity/schema conflicts, same-Effect
   ownership, and an `UNKNOWN` send/create/Effect commitment cannot be
   overridden; they are observe-only and never replayed.
4. A canonical manager creation is single-flight: freshly list native tasks and
   task cache, create at most once, observe unknown outcomes before any later
   attempt, and CAS only an observed identity.

Use history-derived attempts only: a terminal task without return may resume the
same `work_id` at most three observed deliveries. After the cap, request a
user decision with its exact scope; do not emit bare `BLOCKED`. Root alone
performs runtime/archive/mechanical integration Effects and never resolves an
integration conflict manually.
