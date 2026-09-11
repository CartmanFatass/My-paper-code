# Research status and advice at the owner-directed pause (2026-09-04)

Written by Claude Code (Fable 5.1) at the owner's request ("read-only, check research status and
then write your advice under docs"). Read-only session: no experiment was run, no object touched,
no commit made. Basis: `origin/main` at `e4c0c93c7` (2026-09-05T02:00Z, "Complete owner-directed
research pause and final handoff"), `PORTFOLIO.md`, the 2026-09-04 audit ledger (338 rows), the
final handoff `docs/research/portfolio/handoffs/2026-09-04-resumed-round-pause.md`, the intake
documents of the six invested entries, and a direct probe of the remote node over SSH. The local
checkout `C:/Projects/HMASD` is 348 commits behind `origin/main` and dirty; everything below was
read from `origin/main`, not from the working tree.

Markers as in the earlier guidance: **[DECIDE]** only the owner can choose; **[ASK]** the author
would settle by default but wants confirmed; unmarked items are Object-tier recommendations Root
or a DM can apply under the standing delegation once the owner resumes the loop.

## 1. Where the loop is (observation)

- Loop state is `PAUSED / OWNER_DIRECT` after the owner's 「这轮完毕后暂停即可」. The round drained
  cleanly, the final handoff is integrated, the heartbeat is paused with its 30-minute recurrence
  retained, Transport is idle.
- Live compute is zero. Verified independently: no Python process on the Windows host; the remote
  `agent-task` supervisor on `wsl_4070` lists no running task; 14 GB of 15 GB RAM free; the RTX 4070
  is idle.
- Lifecycle: 22 source IDs, 14 `ACTIVE` grouped into nine route agendas (N1–N5, K1–K4), 8 `PARKED`
  reserves. The owner adopted the two-category / six-family / nine-route map earlier today.

Throughput of 2026-09-04 (observation, from `origin/main`):

| Quantity | Count |
| --- | --- |
| Commits to `main` today | 442 |
| Direction documents dated 20260904 | 298 |
| Science cards dated today | 42 |
| Result-evidence documents dated today | 46 |
| Pro conversations archived today | 12 |
| Audit-ledger rows today | 338 |
| Owner inbox items today / answered | 208 / 2 |
| Owner briefs (Chinese) written | 26 |

## 2. State of the nine routes (observation)

| Route | Source | Latest valid result | Boundary at the pause |
| --- | --- | --- | --- |
| K1 | FSD | E3 heterogeneous-hazard discriminator: 13 of 18 cells valid (all small and medium rows, `large_d0_seed1`) | 5 large cells never launched; aggregate rule deliberately unread until all 18 are valid |
| N1 | FRRIE | R05 contact-active R128: `R02_SMALL_OR_ROSTER_MIXED`, both roster gaps inside MEI 0.005 (+0.00047 / −0.00087) | R06 (shared Adam LR 0.003, same root) frozen but its candidate is unaccepted (35/91 orchestration, missing export binding); r04/attempt02 failure cause still unresolved |
| N2 | VNFC | R03 causal one-deviation census: calibration only, `BLOCKED_WALL_CAP` | projected 347,623 s against a 2,700 s cap (about 129×); second recast already spent; lowest sequencing |
| N3 | DISH, FOLR, RCLE, VSP-02 | DISH B01 complete: `FTS-B0 TRIGGER_SUPPORT_INSUFFICIENT`, 48 no-trigger rows, 0/3 usable seeds. FOLR B04 `WITHIN_MEI` (+0.0026 vs 0.05); simple LATCH reference 0.9987 above KEEP 0.852 | DISH A01 retained-prefix trigger-funnel diagnostic carded, not implemented |
| N4 | CBSC | none on the current host; online B1 never ran (r06 exit 6, r07 never created) | second implementation return unaccepted: 90/108 = 83% orchestration against the 30% rule, learner/replay/three tables missing |
| N5 | MGTAP | B03 `SELECTED_INSIDE_MEI` (+0.00066 vs 0.01) | Pro `PARK_CURRENT_ALLOCATION_COORDINATE_FAMILY`; no successor |
| K2 | CRTO | B04 `BR-D NO_TRUE_GAIN`: TRUE residual costs 0.0115 (SHORT) / 0.0071 (LONG) over RAW; B03 paired-order incompetent; B02 negative; B01 comparator-weak | "coupled seed" question pending, nothing frozen; A01 trace still blocked on a remote sparse-materialisation dependency |
| K3 | UCOPE | paid-acquisition B01 (5/6 policies, +0.0214) preserved | numerical-locus diagnostic never launched; two drafts failed the orchestration rule (58%), interface inspection found no conforming path |
| K4 | SCDMP, VSP-C1 | A01 one-sided duration-action relevance; A02 stopped (population not established) | prospective agenda only; D6 family parked by Pro |

Reserves parked today by owner-direct decision: ACVC (after a second recast; certificate interval
straddles the 0.25 threshold), EOCIV, RECCT, EC4G, Scope-1s. EGRCR, Orbit and APFI were already
parked.

## 3. What the evidence says (assessment)

**Every learner comparison completed today landed inside its own minimum effect of interest or
returned no gain.** FRRIE R05, FOLR B04, MGTAP B02/B03, CRTO B03/B04 and the earlier E2 `NEITHER`
all read the same way. The intakes are honest about it ("no stable effect claim"), but the pattern
has two readings that the current objects cannot separate:

1. the mechanisms are null on these toys; or
2. the objects are too small to see anything: one root, one seed, 128 low-learning-rate updates
   (FRRIE), a single 60-second panel (MGTAP), a single seed-0 residual intervention (CRTO).

The FRRIE R05 intake itself lists "limited effective learning at 128 low-LR updates" as a surviving
alternative. A "within MEI" reading from one seed is not evidence of equivalence, and every route
that keeps producing one-seed rungs will keep producing non-decisions. This is the main scientific
cost of the day: 46 result documents, and the only object that can still move a decision is FSD E3,
because it was designed with three seeds per cell from the start.

**Effective live science is narrower than the nine-route map suggests.** Of the six "invested
entries" named in the adopted map, three are blocked on things that are not science (CBSC and
UCOPE on the orchestration rule, VNFC on the cost cap), one has its family parked by Pro (MGTAP).
What can actually run on resume is FSD E3, FRRIE R06, the DISH A01 diagnostic, and a CRTO
follow-up nobody has frozen.

**The engineering-scope rule is now the single largest blocker.** The 30% orchestration share
(`ENGINEERING_SCOPE_SPEC.md` §5) is a ratio over the diff. Small diffs that reuse existing science
modules are almost entirely glue by construction: CBSC's 108-line direct path is 83% orchestration
because the science is imported, UCOPE's draft is 58%, FRRIE R06 is 38%. The rule was written to
stop machinery from growing, and it has done that; but as a ratio it now penalises exactly the thin
runners the spec wants. Three of six invested entries are held by it.

**The owner surfaces are flooded.** 208 inbox items, 154 of them object-tier `decision` items
that were already auto-applied, and 2 answered. The 26 Chinese briefs are the useful reading; the
decision items are not.

**Compute is underused and serialised.** Every run today was CPU, one thread, and the remote E3
cells were launched one after another (launch receipts at 13:45, 14:41, 15:35, 16:41, 18:29,
21:39, 23:46, 00:52 UTC). Each medium/large cell takes about 45 minutes; the five remaining large
cells would take about four hours sequentially or about ninety minutes three-at-a-time. The GPU was
never touched, which is correct for E3 (changing device would change the object) but should be
declared up front for the next UAV-host object.

## 4. Advice

### 4.1 On resume, finish E3 first and read it (recommendation)

FSD E3 is the closest decision-relevant result in the whole portfolio: 13/18 valid, five cells left,
about 45 minutes each on `wsl_4070`. Run the five large cells concurrently (three at a time is
safe against the 4 GiB floor with 14 GB free; each still needs its own fresh receipt), then apply
the frozen aggregate rule. Nothing else in the portfolio is within a day of a verdict.

**[ASK]** Owner prediction slot for E3: the six earlier prediction requests were marked `not
taken (unattended)`. E3 is the one worth taking. The question is whether D2 (`c = 0.25`) beats the
best fixed-`k` D0 learner when hazards are heterogeneous, per row and in aggregate.

### 4.2 Amend the orchestration rule [DECIDE]

Three of six invested entries are held by a ratio that cannot be met by a thin runner. Options:

- (a) **Recommended.** Keep the 30% share but apply it only when the diff adds at least 300
  runtime lines; below that, cap orchestration at an absolute 150 lines. A 108-line diff that is
  83% glue is then 90 orchestration lines and passes; a 2,000-line diff still must be 70% science.
- (b) Count a line that calls an existing science module (learner, replay, evaluator) as science.
  Simpler, but gameable by wrapping.
- (c) Owner-direct acceptance of the CBSC candidate and the UCOPE draft as conforming, leaving the
  rule as written. Unblocks today, blocks again next week.

Whichever is chosen, it is a spec edit and therefore excluded from the standing delegation. Until
it is decided, CBSC, UCOPE and FRRIE R06 cannot move, and their DMs will keep writing bounded
engineering returns that consume Pro and audit rows without producing science.

### 4.3 VNFC: park N2 or authorise a sampled census [DECIDE]

The exact census is infeasible by two orders of magnitude on the declared cap, and the direction
has spent both recasts. Leaving it queued at lowest sequencing means each resume re-reads the same
blocker. Options:

- (a) **Recommended.** PARK N2 with the calibration as the re-entry evidence; re-entry requires a
  bounded object whose projection is inside the cap.
- (b) Owner-direct a sampled census (a fixed random subset of the candidate records, declared
  size, declared seed) as a new object with its own cap. This is a different estimand and must be
  carded as such; it does not restore the exact-census claim.
- (c) Raise the cap. Not recommended: the cap is per arm and the projection is 96 hours.

### 4.4 No more one-seed learner rungs (recommendation)

Before any route freezes another learner comparison, the card should carry at least three seeds
or three roots, or state why one is decision-relevant. Concretely for FRRIE R06 **[ASK]**: the
card reuses one root and one seed. An R128 root costs about 2,000 s locally and less on the remote
node, so three roots are affordable inside one session. Widening R06 to three roots is a treatment
change inside the accepted mechanism and stays Object tier; it should be made before the CM
re-implements, not after the result reads "within MEI" again.

### 4.5 Move the duration line to the UAV host after E3 [DECIDE]

The owner's target is multi-UAV, and the evidence spec allows B on the UAV learner directly without
a toy win or a headroom number. Nothing in the current nine routes touches the UAV environment.
FSD already has a runnable candidate: E2b, transfer of D2 `c = 0.25` to UAV scenario 1, which the
DM declined in favour of E3 at 02:45 today. Regardless of E3's verdict, E2b is the natural next
object for K1: if E3 is positive it is the transfer test; if E3 is `NEITHER` again, the toy has
said what it can and the UAV host is where the question lives. Declare device (CPU or CUDA) and
thread count on the card before implementation so the run can use the 4070.

### 4.6 CRTO: take K2 to Convergence with a PARK recommendation [ASK]

Four rungs on the same host (B01 comparator-weak, B02 negative, B03 paired-order incompetent, B04
no true gain with a measured cost over RAW) is enough to ask Pro whether the residual-trigger
family has anything left on this host. The pending "coupled seed" question would be a fifth
one-seed rung. The A01 update-252..264 trace can stay as the retained diagnostic if Pro wants it.

### 4.7 DISH A01 diagnostic: proceed on resume (recommendation)

Three complete seeds with zero triggers despite nonzero learner exposure is a measurement fact
worth locating before any more learner budget. The carded retained-prefix funnel diagnostic is
cheap and outcome-blind. Implement and run it first in N3; do not add seeds or force triggers.

### 4.8 Owner surfaces: change what reaches the inbox [DECIDE]

The console was designed for the owner to grade decisions; in practice 154 auto-applied
object-tier items arrived in one day and two were read. Proposal: object-tier `decision` items go
to a daily digest file, and the inbox receives only briefs, prediction requests, direction- and
portfolio-tier items, close calls, critic dissents and second recasts. That is an edit to
`tools/owner_console/item.py` and the owner README, both outside the standing delegation.
Meanwhile the useful reading is `docs/research/portfolio/owner/briefs/`, 26 one-page Chinese
briefs, one per valid result.

### 4.9 Reconcile the owner checkout [ASK]

`C:/Projects/HMASD` is 348 commits behind `origin/main` with 23 modified tracked files, including
`AGENTS.md`, `.codex/*.toml`, the transport skills and FRRIE b01 code, plus untracked corpus and
decision files. Codex integrates elsewhere and the handoff asks that this tree not be pulled, reset
or stashed. The risk is that authority edits made here (`AGENTS.md`, `.codex/`) diverge from what
Codex has already integrated under the same headings. Suggested order: diff `AGENTS.md` and each
`.codex/*.toml` against `origin/main`; commit the edits that are still intended, by pathspec; drop
the ones that were superseded; then fast-forward. The author did not modify anything.

### 4.10 Compute (recommendation)

- Launch independent cells concurrently on the remote node, each with its own receipt; the
  serial pattern today cost about six hours of wall time on E3 alone.
- Record peak RSS on remote cells. Every E3 cell is `resources_unmeasured`, so the concurrency
  advice above rests on the local observation that three small cells ran together in 9.4 GB.
- Keep E3 on CPU as frozen. Declare CUDA on new UAV-host cards.

## 5. Proposed resume order

1. Owner decides 4.2 (orchestration rule), 4.3 (VNFC), 4.8 (inbox policy). These are the three
   items that no DM can move.
2. Root resumes with the working set: FSD (five E3 cells, concurrent), N3 (DISH A01 diagnostic),
   FRRIE (R06 widened to three roots if 4.4 is accepted, after the rule change), CRTO (Convergence
   round with PARK recommendation), and the fifth slot to CBSC or UCOPE once the rule is amended.
3. E3 aggregate read; owner prediction scored; FSD DM freezes E2b on the UAV host.
4. Portfolio snapshot updated with the E3 verdict before any other new family is opened.

## 6. Not verified in this session

- Test-suite health on `origin/main`: not run (the local tree is stale, and the request was
  read-only).
- Remote artifact integrity beyond the hash statements in the intakes.
- Per-cell E3 values: deliberately not read, to keep the aggregate outcome-blind as the card
  requires.
- Whether the `hmasd-experiment-tracker` custom role loads on a fresh runtime; the handoff
  records one successful direct ACK and one `unknown agent_type` earlier in the day.
