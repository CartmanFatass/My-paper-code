# FRRIE B01 contact-active R128 R02 remote drain boundary — 2026-09-04

Status: `EXACT_SHA_MATERIALIZED / NOT_LAUNCHED / OWNER_DRAIN_PAUSE`

This is engineering process evidence, not a scientific result. It records the recoverable boundary
at which the owner's drain instruction stopped the R02 invocation before resource admission.

## Bound object and authority

- science card:
  `FRRIE_B01_CONTACT_ACTIVE_R128_R02_SCIENCE_CARD_20260904.md`;
- object: `FRRIE-B01-CONTACT-ACTIVE-R128-R02-20260904`;
- exact pushed science SHA: `36b538ba1b91eede9f528dd315fa624f8c1d53e5`;
- branch: `codex/frrie/dirty-intake-20260904`;
- pack-route object decision: owner item `20260904-frrie-009`, integrated by Root at
  `236dbc14e`;
- planned remote node: `wsl_4070` through `hmasd-wsl-node`;
- planned task: `frrie_b01_contact_r02_36b538ba_01`;
- detached worktree:
  `/home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba`.

The earlier `20260904-frrie-006` identifier was a collision in the isolated branch and is not the
current owner-item identity for this decision. The current identity is `20260904-frrie-009`.

## Directly observed transport facts

The first remote GitHub fetch terminated after approximately 300 seconds with exit `1` and
`SSL connection timeout`. At that point the task, worktree, output root and admission receipt were
absent. No result-bearing command had been accepted.

The unattended object-tier selection then chose the reversible exact-commit pack route. A
non-thin pack was produced only from committed bytes at the already-pushed science SHA. Its facts
are:

- byte length: `1,127,888`;
- local and remote SHA-256:
  `328d41c8a926b5e31732ceacd6ba4fbf15b00166e7f2ba1cebe2f00c9fcf807e`;
- Git pack object hash:
  `9a469f2f4e9ce48424d0bddfd97471dc6afa9f97`;
- local pack verification: pass;
- imported remote pack verification: pass.

The remote detached worktree now has exact HEAD
`36b538ba1b91eede9f528dd315fa624f8c1d53e5`. It is clean including the untracked-file check, and
its required source surface differs from neither HEAD nor the local launch surface. The canonical
required-tree listing covers 61 files and has the same SHA-256 on both hosts:

`4f027476d4b051df3920a4902b74f39d0d26bb4550952708353b717b6e7fe34d`.

## Drain receipt

Immediately before the owner cutoff, and again while draining:

- `agent-task status frrie_b01_contact_r02_36b538ba_01` returned `not_found`;
- the planned output root was absent;
- the planned admission receipt was absent;
- no matching task, runner or worktree-preparation process remained.

Therefore the cutoff preceded task acceptance. No node-local resource preflight, native build,
production RNG/root opening, model or optimizer construction, learner update, evaluation,
`summary.json`, result branch or scientific observation occurred. R02 remains unobserved. The
accepted three-root B01 reading remains bounded to its three literal no-contact paths.

## Recoverable resume boundary

No resume is scheduled while the owner drain pause is in force. If the owner later resumes this
object, the next action is not a retry or successor: query the same planned task and output
identities for absence, recheck the retained exact-SHA worktree and required-surface digest, then
submit one remote `agent-task` whose single command performs a fresh node-local 4 GiB admission
immediately followed by `&&` and the frozen runner. No local fallback, new root, changed card or
changed argv is implied by this record.
