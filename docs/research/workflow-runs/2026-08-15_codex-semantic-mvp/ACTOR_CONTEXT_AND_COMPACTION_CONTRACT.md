# Actor Context and Compaction Contract

Conversation context is an expendable execution cache. After compact or resume,
owner-local state is rehydrated from an explicit actor checkpoint and capsule.

## Owners

One Codex session may contain multiple semantic actors. Long-lived kinds are
`PORTFOLIO`, `OPERATIONAL_ROOT`, `EM`, and `CM`. Short-lived kind is `LEAF`.
Actors never share one mutable checkpoint.

## What compaction may not do

`PreCompact`, `PostCompact`, and `SessionStart(compact|resume)` cannot create
or resolve scientific, technical, direction, or portfolio decisions. They
cannot close tasks, resolve ordinary obligations, change owner, or revise a
plan epoch.

## What is restored

Given the same actor id, state version, epoch id/revision, latest owner-authored
semantic commit, open actor-local obligations, and canonical path references,
the capsule is identical regardless of raw child prose or compaction count.

A context acknowledgment becomes stale only when actor `state_version`,
`epoch_id`, or epoch revision changes. Authority file bytes are not a gate.

## Automatic vs explicit restore

Until a live SHADOW topology probe proves otherwise:

- Portfolio and Operational Root may receive automatic session-root capsules
- EM, CM, and leaf do not receive automatic compaction rehydration
- those owners use explicit MCP checkpoint/reanchor tools

## Memory boundary

SQLite stores path references, packet references, control obligations, and
owner-authored reanchor snapshots. It is not scientific truth, technical
acceptance, portfolio authority, or canonical project memory.
