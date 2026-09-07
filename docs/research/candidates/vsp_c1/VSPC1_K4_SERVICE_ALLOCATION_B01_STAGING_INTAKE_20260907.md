# SERVICE-ALLOCATION-B01 — ended staging probe intake, 2026-09-07

**Object-tier technical decision: accept the recorded zero-exposure staging return.**
This intake covers the ended remote source-availability probe through the authoritative
readback at **2026-09-07T14:45:09.457921Z**. It supplies no scientific result, performance sign
or B completion. B objects have no consumption state. The frozen question remains unanswered.

**Current continuation:** Portfolio correction `1b935b04c699e43de9bec183bd93be53bd19110d`
commands P07-VSPC1-STAGE-REPAIR-01. Root has already dispatched that command directly to the
same CM. This intake does not close, hold or duplicate the new command; its later actions and
exposure are outside the ended-probe cutoff recorded here.

## Evidence inspected and rule applied

DM read the full [execution record and E0 technical return](VSPC1_K4_SERVICE_ALLOCATION_B01_EXECUTION_20260907.md)
at CM commit `42689ba47`, including the embedded final handle/worktree readback, and the full
relevant Portfolio correction. Root integrated the return at
`d18e8fd225992d90c0b5bc4199e31244c671e0e2`. The prospective execution record was committed and
pushed as `b3c7290fc` before staging and integrated as `0db0c39ab`. Selected source remains
`faf786e135b3f55e535c898e17e646dcc341bdec`; the
[source/card conformance intake](VSPC1_K4_SERVICE_ALLOCATION_B01_SOURCE_INTAKE_20260907.md)
and [card §§2–7](VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md) remain intact.

The then-current Root stop applied by CM was, verbatim:

> If staging/admission fails, preserve exact failure and stop the affected action without retry.

That instruction explains the historical stop. It is superseded for subsequent work by
Portfolio's correction, which explicitly continues the named-ref bundle/SCP/import repair
and unchanged FACTOR then GENERIC calls. No remote HTTPS availability probe is in that new
command. The historical stop is not current authority to refuse its conforming continuation.

The applicable integrity reading is evidence-spec §11.8.7: direct operational facts remain
reportable, while an unavailable observation cannot acquire a scientific polarity. Card §5
performance branches and the prediction are not evaluated when no selected endpoint exists.
DM inspected the CM record without repeating its source-availability or remote status checks.

## Direct observations and limitations

CM's `git cat-file -t` read for the selected source in `/home/wu/projects/HMASD` triggered the
partial clone's automatic fetch. A process observation saw the fetch/`git-remote-https` chain
at 80 seconds; it remained pending without output after several minutes. CM checked the
owned transport's command line, terminated PID 2740217, and the enclosing read script exited.
No alternate fetch, bundle import, model probe or learner invocation followed under the ended
command. Partial transfer of Git objects is possible and is not scientific exposure.

The wrapper retained stdout only. Git's return code and stderr are unavailable, so this record
does not assign a network, authentication or server cause, or conclude that the source object
was unavailable. **Exact source availability was not established by that aborted read.**
Staging wall/CPU work was not measured completely; the observed pending duration is not an
experiment wall-time or a breach of either unstarted 2,700-second invocation cap.

The E0 record retains the final remote readback at the cutoff above:

| Quantity | Observed fact for the ended probe |
| --- | --- |
| Target worktree `/home/wu/hmasd-worktrees/vspc1-service-allocation-b01-seed402-20260907` | `worktree_exists=false` |
| `vspc1-service-allocation-b01-factor402-20260907` | `not_found` |
| `vspc1-service-allocation-b01-generic402-20260907` | `not_found` |
| Memory admission / receipts / run root | None |
| Selected model / optimizer updates / host episodes / evaluations / checkpoints | Zero / none |
| Accepted experiment / result / monitor adoption | None |

No reward, information, learner or primary measurement was exercised or damaged by a selected
invocation. No result-bearing retry occurred. Missing staging error detail limits causal
diagnosis; it does not invalidate the previous implementation acceptance or count as a negative
B result. Scope §4 additions: none; this return changes documentation only. No source or
card requirement changed and no source-line budget breach was introduced.

## Decisions this intake produces

Options: (a) accept the bounded technical return and preserve the separately authorized
continuation; (b) return a concrete gap in the absence/exposure evidence to CM; (c) hold the
new command until the aborted fetch's full cause is established.

Recommendation and executed choice: **(a)**. The retained readback supports the necessary
no-launch/exposure classification. Missing Git stderr/exit prevents a stronger cause claim,
but does not create a dependency for the explicitly authorized bundle route. There is no
concrete evidence gap requiring (b), and (c) would add an unrequested historical diagnosis.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Kind: technical;
reversible: yes; owner flag: none. See the [audit ledger](../../portfolio/audit/2026-09-07.md).
Owner reviews at this clean boundary returned `[]`; no instruction required application.
Owner prediction remains `not taken`, and the DM's rule-versus-learners prediction remains
unscored. This ordinary technical return creates no P1/P2 item or valid-result Chinese brief.

## Bounded reading and next discriminator

The strongest support is the retained final absence readback, consistent with CM's action
sequence. The strongest limitation is missing Git error output; this intake makes no causal
claim about the transport. No empirical evidence supports or contradicts multiplicative
value learning on this host. Accepted source conformance, existing K4 mechanism boundaries,
the declared MEI and missing new-host headroom record are unchanged; `DIRECTION.md` receives
no mechanism update from an operational stop.

The immediate dependency is already assigned: same-CM committed-object staging under
P07-VSPC1-STAGE-REPAIR-01, followed by the original two calls and their original admission,
comparison and complete caps. Root observes accepted handles, CM retains collection and
technical acceptance, and DM takes in the eventual scientific return. The discriminator
remains update256 FACTOR–GENERIC, both learners against LQ-EXCLUDE, and period-specific
consequences. No extra seed, arm, local fallback, causal audit or Pro round is selected here.
