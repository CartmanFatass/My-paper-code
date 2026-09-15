# Intake — FSD FLAT k correction return (portfolio:cross_direction)

Request `2026-09-15-fsd-flat-k-correction-01` (task `7c5d5aaec`, bound handoff `550ef2f0a`,
base sha `7a34308e3` on `codex/fsd`). Author DM: the Claude hub. Sent 2026-09-15 12:49Z,
one Send, one tab. Response delivered by the ChatGPT GitHub connector at
`codex/fsd 8d76569178340434ae973e43d46685a114688fb1` ("Add FSD FLAT k correction decision",
12:55:41Z): [`archive/RESPONSE.md`](archive/RESPONSE.md) (blob
`a4daca15fbf02158eb30cde1c1a0e33dd570fdce`, 5,591 bytes); Issue #22 delivery comment
`5680531714` at 12:56:43Z. Read from the immutable commit, not from the chat receipt.

## Question posed

Does the DM's deviation stand: FLAT trained with `k = 10` (the D arms' truncated-BPTT chunk
length) instead of the `mappo` switch's `k = rollout_length + 1`, whose earlier "not runnable"
explanation in the investment intake was wrong (the switch is runnable; the real reason is the
gradient-truncation law, review corrections M1a–c at `dc4dbdfcd`)? Options: (1) confirm
`k = 10`; (2) require the switch-selected long k; (3) other.

## Formed decision

**Option 1, `PRO_FINAL / OWNER_DELEGATED`:** FLAT stays at `k = 10` within the existing S
allocation; the four purchased FLAT originals proceed one per block at launch source
`dc4dbdfcdb20ca29a47c1187e9ebf6787483d21b`. The decision supersedes only the prior decision's
"switch-selected long k" requirement; it re-decides nothing else and creates no exposure.

Points the response fixes, checked against the card and the current specification:

- Decisive reason accepted as stated: matching the discoverer actor/critic gradient-truncation
  law; the earlier "not runnable" wording is recorded as incorrect (the intake's appended
  correction already says so). No memory failure or speedup is claimed.
- Recipe unchanged: `off → mappo → k = 10`, single constant skill, no high-level collection,
  training, discriminator training or rewards; actor and critic learn; coordinator forward
  calls still occur (zero optimizer calls is not zero computation); switch-computed high-level
  buffer fields stay as documented inert differences. This is the explicitly corrected flat
  recipe, not unmodified switch reproduction, and matched chunking does not establish equal
  optimisation work or long-k/short-k trajectory equivalence.
- Labels: `GAP_D = J15(D1280) − J15(FLAT_k10)`, `GAP_I = J15(I1280) − J15(FLAT_k10)` keep their
  arithmetic and carry no MEI; they are untuned cross-information package gaps, **not §11.7
  headroom**. The residual "headroom record" wording in the request is not adopted.
- D1280/I1280 fits and the rollout-15 SI1280 primary are unaffected; nothing is stopped,
  restarted, reconfigured, repeated or rescored. The .05 J importance reading, separate
  uncertainty reporting, four blocks, fifteen rollouts, three 32-world H500 panels and the
  4 + 2 rollout-5 accumulation stand.
- Next action is the four FLAT originals only: no k sweep, ablation, pilot, replacement, retry,
  extra panel, extension, grant, specification exception, lifecycle or peer change. Ordinary
  wall plans remain adjustable, not caps. No further Root ratification.
- Access: all eight manifest paths read at the fixed versions; no code executed; no
  decision-critical source gap.

## Conformance check (AGENTS §2, §4.8)

No concrete conflict with the owner instructions of 2026-09-14/15, the card
(`FSD_BASELINE_INTERRUPTION_B01_PROSPECTIVE_CARD_20260915.md` §2, §8) or evidence spec §11
(§11.4 launch conditions, §11.7 headroom definition, §11.8 burden, §11.11 two-axis scope).
The response answers the posed question at its declared evidence class. The card's §8
deviation paragraph and the runner's `FLAT_K = 10` already implement option 1; the only
wording change is that the GAP contrasts are never called headroom (card §7 "Headroom"
heading and the investment intake's "headroom record" phrase are to read "package gap").

## Application

- FLAT fits launch as independent work at the same source bytes `dc4dbdfcd`, one queue
  element per block (`BLOCK.sh <W> <seed> FLAT`, single-token arm), handles
  `fsd-bi-b01-<seed>-FLAT`, with the memory admission inside the supervised command; launch
  facts in the evidence folder's [`EXECUTION.md`](../../../candidates/flexible_skill_duration/baseline_interruption_b01_20260915/EXECUTION.md).
  Concurrency is a technical choice from measured peak RSS (about 2.8 GiB per fit), not a
  scientific parameter.
- Decision record: [`decisions/2026-09-15-fsd-flat-k-correction.md`](../../decisions/2026-09-15-fsd-flat-k-correction.md).
- Ledger row in `docs/research/portfolio/audit/2026-09-15.md`; owner item `20260915-fsd-001`
  traced with this application (no new item: the correction closes the same investment
  decision's open wording).
- Registry: key `portfolio:cross_direction` archived by the transport in phase 2 (facts file
  in the transport archive; if the singular `direction_id` reconciliation was needed again,
  it is recorded there and in `docs/Claude_docs/changes/2026-09-15-control-plane-changes.md`).
