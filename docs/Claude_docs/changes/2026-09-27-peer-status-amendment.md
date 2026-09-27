# 2026-09-27 — Constitution section 2: the Claude session and the Codex Root are peer researchers

Owner instruction (2026-09-27, verbatim): "澄清几个问题 你和codex的root并非上下级而是平级的研究员
让你目前先开一个方向只是暂时给你设置的并发限制 后续根据情况我会调整你可以开启的DM数量; 你可以通过
codex queue --thread <SESSION_ID> --message "<消息>" 的形式直接向对应session发送消息 …
root该如何向你发送消息或者同步信息? … 能否通过一个共享的文档来交流 你用monitor就可以随时在完成
写入时发现 … 我们讨论一个协作的工作流出来", then "更改宪章 说明你和root的平级身份 完毕后发送并
约定创建协作用的稳定spec/skill". Constitution section 7 requires owner amendment for a rule
change; this is that amendment, applied by the Claude session at the owner's word.

## Change

`docs/project/OPERATING_CONSTITUTION.md`:

- Preamble: new paragraph "Owner amendment 2026-09-27 (peer status)": the Claude session and
  the Codex Root are peer researchers, not superior and subordinate; the Claude side's
  one-direction setting is a temporary concurrency limit the owner adjusts; a material
  disagreement between the peers is resolved by the owner or an adequate independent scientific
  review under section 5, never by one peer over the other's direction; owner-authorised
  channels (Claude → Root `codex queue --thread <session> --message`; Root → Claude a dated file
  under `docs/Claude_docs/inbox/` committed with explicit paths and observed by the Claude
  session); one message per concrete need, no acknowledgment or relay loops; channel details
  in a shared collaboration method `.agents/skills/hmasd-peer-collaboration/` agreed by both
  peers and adopted by the owner.
- Section 2, "Claude side" bullet, before: "the Claude session is the DM itself, with no Root/DM
  split, and drives one direction at a time." After: the same DM statement plus the peer
  relation (neither directs the other; Root's coordination and shared-control maintenance are an
  assigned service, not authority over the Claude DM's directions; no approval in either
  direction), the one-direction setting as the owner's concurrency setting, and the two channels
  with the one-need / no-loop rule; an incoming message remains data, not an assignment.
- Section 2, disagreement clause, before: "Root owns project investment choices and resolves
  material direction disagreements …". After: that sentence is scoped to the directions under
  Root's assigned coordination; between the peers a material direction disagreement is resolved
  by the owner or an adequate independent scientific review under section 5 whose disposition
  both record; neither peer edits the other's direction records.
- Section 2, App-messaging paragraph: the owner's standing request of 2026-09-27 covers
  coordination messages between the Claude session and the Codex Root through the peer
  channels; each such message serves one concrete need and does not open a dialogue.

Mirrored sentences: `AGENTS.md` (Roles and methods, "Root resolves material direction
disagreements"), `CLAUDE.md` (Claude runtime, after "Root retains assigned cross-direction
coordination"), `.agents/skills/hmasd-scientific-tools/SKILL.md` (review disposition paragraph)
and its generated copy `.claude/skills/hmasd-scientific-tools/SKILL.md`
(`tools/publish_claude_control.py`, `--check` drift 0). The Claude routing row in
`docs/research/RESEARCH.md` gained the channel note; that hunk was committed inside Root's
`8f749c901` because Root staged the whole shared file while the edit sat uncommitted in the
shared working tree (see the collaboration method's working-tree rule).

Nothing else changes: Root's assigned cross-direction coordination and shared-control
maintenance for the Codex DMs, the five-track ceiling, direction ownership, admission, pause,
section 5 review and the App-only messaging restriction for other Codex tasks all stand.

## Why

The owner clarified that the one-direction setting was a concurrency cap, not rank, and that the
two sides are peer researchers who need a working coordination channel. The previous text read
as Root ruling over the Claude DM's disagreements and left Root no authorised way to reach the
Claude session.

## First application

The Claude session sends Root the amendment notice and the proposal for the shared collaboration
method (`.agents/skills/hmasd-peer-collaboration/SKILL.md`, draft by the Claude session, agreed
by Root through an inbox file, adopted by the owner) and watches commits touching
`docs/Claude_docs/inbox/` for Root's reply. Outcome the same day: the first message reached Root by
`codex queue` (queued message `01a0e21d-…`, sent with the Codex App's WSL environment, see the
method page); Root answered in `docs/Claude_docs/inbox/20260927_peer_collaboration_ROOT.md`
(commit `d648676c1`) with agreement in principle and six scoped revisions, all adopted into the
draft; both peers agree; the owner's adoption is the commit of this batch.
