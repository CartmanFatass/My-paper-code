# ACVC-NATIVE-LINK-LOSS-B02 — P79 scientific intake

Date: 2026-09-09. **Valid complete mixed B/EXPLORE.** The fresh matched instance again loses
to fixed retrace F: T−F **−0.0542533634 J**. T−G is **−0.0065945815 J, WITHIN**, so the
previous native T−G gain did not recur. Both learned gates again improve over always-apply C
and lose to F. This supports a bounded adverse reading for unchanged learned selection;
it is not a population, causal, headroom or family-closure conclusion.

## 1. Card, source and evidence checked

Authority: [B02 card §§1–6](ACVC_NATIVE_LINK_LOSS_B02_SCIENCE_CARD_20260909.md) and
[prospective facts](ACVC_NATIVE_LINK_LOSS_B02_P79_PROSPECTIVE_FACTS_20260909.json) at
`56ce830386cfab6be30b217e5cc5b0d0f8109120`, under Root's explicit P79 allocation and the
retained proper-node question. Evidence-spec §§4, 11.4, 11.7 and 11.8 control. Exact scientific
source is `4e019ca35b930c2216fdfe110ba587e222ca7384`; accepted-handle record is
`16625367eadb2f4462c3c1e85da45d38e35c6ddc`; full CM evidence is
`b273dd633a1ce9cd7fe2b39ef747eb3010d9ccea`.

I read the complete [E0 technical return](ACVC_NATIVE_LINK_LOSS_B02_RESULT_EVIDENCE_20260909.md)
against the card, source diff against accepted P78, both changed synthetic tests, the published
summary and retained episode/update records, plus admission, collection and terminal receipts.
The code change only propagates seed 8902 and B02/P79 identity and adds the 14-line launch command.
Binding, models, learner, reporting formulas, private information, actual-command feedback and
stored-proposal/gate-only likelihood are unchanged. The scientific host and fixed DENSE digest
are unchanged. The two tests use a synthetic fixture, with no native prelude. Reused independent
P78 semantic review and unchanged coverage remain applicable; I did not repeat those tests or
construct models, native environments or an additional evaluation.

Read-only arithmetic in [dm_analysis.json](native_link_loss_b02_p79_20260909/dm_analysis.json)
checked unique arm/phase/episode identities, every frozen reset identity, all `S=256J` relations,
all counts, each paired mean/SE/reading and all gate aggregates. The DM checked the summary and
episode-file bytes against collection digests; CM checked all six remote scientific files and
the finite, correctly labelled T/G checkpoints. Source fields and admission agree. The retained
terminal receipt says finished, exit 0 and tmux inactive. No concrete integrity or acceptance
gap was found, and no historical quarantine was reinterpreted.

| Quantity | B02 observed |
|---|---:|
| New matched training instances | 1, master 8902 |
| Training episodes, all retained | 1,024: 512 each T/G |
| Final episodes, all retained | 128: 32 each T/G/C/F |
| Team steps | 294,912 |
| Scored resets / additional unscored constructor resets | 1,152 / 4 |
| Two-episode rollouts / Adam calls | 512 / 2,048 |
| Base agent forwards / gate collection forwards | 1,474,560 / 1,392,640 |

All T/G training reset identities are 890201000–890201511; all four final panels use
890202000–890202031 with their own action streams. The new seed law is disjoint from P78;
within-instance common initialization and reset matching are intentional. No P78 gate was reused.

## 2. Verbatim rule and complete new-instance reading

Card §4:

> Reading rule (apply separately to each declared contrast, keeping the actual signed number):
> **UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**. Separately report
> whether each primary exceeds 0.25 S. Both primary UPs support a meaningful preliminary learned
> correction signal; any favorable T−G adds only finite-budget structured-package evidence. A T−G
> gain cannot rescue a T loss to C or F. If G contains the gain, recommend describing a learned
> correction package. Positive sub-MEI results remain positive; WITHIN is not equivalence. Opposite
> native signs remain adverse even if link or gate statistics improve. Full outcomes and uncertainty
> inform the next unallocated recommendation; no branch automatically launches another instance.

The separate quantities remain `J=S/256`, inherited **0.25 S = 0.0009765625 J**, and
MEI **0.01 J = 2.56 S**. Final mean J: T **0.2239949255**, G **0.2305895069**,
C **0.1704037145**, F **0.2782482889**.

| Declared contrast | Mean ΔJ | Conditional SE J | Mean ΔS | Reading | >0.25 S |
|---|---:|---:|---:|---|---|
| T−C, primary | +0.0535912110 | 0.0109472169 | +13.7193500 | UP | yes |
| T−F, primary | −0.0542533634 | 0.0109171556 | −13.8888610 | DOWN | no |
| T−G | −0.0065945815 | 0.0108858343 | −1.6882129 | WITHIN | no |
| G−C | +0.0601857925 | 0.0113997635 | +15.4075629 | UP | yes |
| G−F | −0.0476587820 | 0.0107632723 | −12.2006482 | DOWN | no |

The primary minimum of the two fixed-contrast means is **−0.0542533634 J**. F is the stronger
fixed-panel reference. No selected-max SE or episode-wise fixed oracle is used. Every fixed
contrast's SE is sample-SD/sqrt(32) over the new paired joint episodes, conditional on this
trained pair and fixed base. UP/DOWN are effect-size readings, not significance tests.
T−G retains its actual negative sign; WITHIN does not establish equivalence or generic superiority.

The descriptive F−C difference is **+0.1078445744 J**. This fixed-rule comparison was introduced
as outcome-informed at P78 and remains a secondary reading of retained panels, not a B02 primary.
The native T−C/G−C gains are reportable learned-correction-package evidence; F improves still more.
Neither old T−G nor an aggregate statistic rescues the current adverse primary.

## 3. Two-instance comparison and mechanism boundary

The allocated new discriminator is answered: the T−F loss recurred, while the T−G gain did not.

| Native contrast | B01 / 8901 | B02 / 8902 |
|---|---:|---:|
| T−C | +0.0671812303, UP | +0.0535912110, UP |
| T−F | −0.0290806349, DOWN | −0.0542533634, DOWN |
| T−G | +0.0369687053, UP | −0.0065945815, WITHIN |
| G−C | +0.0302125251, UP | +0.0601857925, UP |
| G−F | −0.0660493402, DOWN | −0.0476587820, DOWN |

[Two-instance descriptive evidence](native_link_loss_b02_p79_20260909/two_instance_descriptive.json)
retains both signed endpoints, ranges and descriptive SDs. The existing scientific-tools
summarizer used [four T/G endpoint rows](native_link_loss_b02_p79_20260909/independent_training_endpoints.csv)
under the unchanged condition, with actual object IDs retained, and reports
[n=2 per learned arm](native_link_loss_b02_p79_20260909/run_level_summary.json). C/F were not
entered as fictitious trained runs. T/G are matched within an instance, and the two instances
have fresh training and evaluation randomness; observed variation does not isolate training
randomness from new evaluation panels. Their 64 episodes are not pooled into a population SE.
The descriptive mean T−G is +0.0151870619 J, but it does not become a new UP object or remove
the sign variation and repeated losses to F. No training-population conclusion follows from n=2.

Strongest support: both learned packages improve over C in both instances, and the fixed
cue/retrace package F has a still larger observed gain over C. Strongest contradiction to an
adaptive-selection advantage: **T and G each lose to F in both instances**, and the structured
T−G gain is not repeated. This concerns the fixed DENSE/8201, unchanged heads, objective and
512-episode learner budget; it does not prove that selective retrace or history is generally useless.

The unchanged path is joint motion/interference → private observation of own-link eligibility
loss bound to one prior coordinate → apply/retrace of own realized motion → new joint geometry
and native team reward. F itself uses that retained observation history. The comparison does not
separate the anchor predicate, retrace action, dwell effects or partner response, and does not
establish that own-link loss was global service loss. Functional containment in G is consistent
with finite-budget variability; it is not a diagnosis of why the fitted arms differ.

For the unexpected T−G reversal, reuse the question-driven local-library grounding already
recorded in [B01 intake §3](ACVC_NATIVE_LINK_LOSS_B01_INTAKE_20260909.md) and its verified
P68 DACOM/CoDe source passages. It supports keeping competent fixed and same-information
history comparisons visible. Those sources neither explain this reversal nor supply performance
evidence on the UAV host. No new corpus search, novelty claim, causal diagnostic or implementation
requirement is justified by this result. The old R02 positive history witness and R03 finite-host
negative remain separate evidence under their original authority.

## 4. Real learner exposure and prospective predictions

T/G had **50,137 / 49,920** eligible training decisions, respectively (7.6503% / 7.6172% of
their 655,360 agent decisions). Every one of each arm's 1,024 recorded updates had eligible
rows. Training retrace counts were 27,321 / 27,341. Final eligible/retrace counts were
T 3,301/1,837, G 3,190/1,704 and F 3,877/3,877. Every eligible proposed/retrace command was
distinguishable; C's opportunity count remains unmeasured by design. These trajectory-dependent
counts are descriptive and do not identify a causal retrace dose-response.

T/G gate absolute displacements were **1.6698216 / 2.2648809**, relative **0.1773413 / 0.1708186**.
The zero-initial final projections moved by 0.1196913 for T and 0.0757322/0.0952114 for G's
common/residual paths. Critic movement is separate. The result cannot be described as absent
opportunities, absent gate updates or zero gate movement; optimization success is not established.

| B02 prospective DM point J | Observed J | Sign correct |
|---|---:|---|
| T−C +0.040 | +0.0535912110 | yes |
| T−F −0.025 | −0.0542533634 | yes |
| T−G +0.015 | −0.0065945815 | no |

Two of three signs matched; the predicted DOWN primary matched. T−C UP (p=0.75) and
T−F DOWN (p=0.65) occurred; T−G UP (p=0.60), both primary positive (p=0.20) and both
primary UP (p=0.10) did not. All single-event scores and point errors are retained in the
analysis, with no calibration claim. P78 predictions remain unchanged. Owner prediction:
**not taken (unattended)**; both main and direction review queries returned no unapplied reply.

## 5. Complete cost, receipts and engineering conformance

The one accepted handle `acvc-p79-native-link-loss-8902-4e019ca35` ran on `wsl_4070` at
`/home/wu/hmasd-worktrees/acvc-p79-4e019ca35`, with CPU/FP32 and Torch intra/inter-op 1.
Fresh joined actual-node admission at 2026-09-09T11:59:10.378280Z measured
15,627,145,216 physical/effective available bytes and passed. Staged DENSE bytes match the
card digest. CM alone observed the process. The same handle exited 0 at **12:05:07Z**, with
tmux inactive. Supervisor observation-age 386 s is not substituted for measured process wall.

| Complete machine quantity | Seconds |
|---|---:|
| Current focused checks | 5.4396806 |
| Scientific process through actual exit | 357.55 |
| Logical study bill | **362.9896806** |
| T complete bill, including shared work | **191.5703530** |
| G complete bill, including shared work | **207.2332454** |

The complete bill includes the outer timing difference of 17.5826431 s, covering work after
the runner's summary measurement. All checks, startup, C/F evaluation and publication/exit
are charged as the card requires; 300/1800/3600 s caps pass. Peak RSS is 549,380 KiB.
The serial machine critical path equals the summed declared invocation walls. Human waits,
Git/SSH staging and gaps between invocations are separate; aggregate CPU and scratch high-water
are unmeasured. The **two-instance native cohort** totals **736.3966541 s / 2 valid comparisons
= 368.19832705 s per valid instance**, and 589,824 team steps. This is not all-history ACVC cost.

Engineering scope §4: **none added**; no §5 breach. The identity change adds 20 and removes
5 non-test lines; the reused attempt has 484 non-test lines and a 150-line runner. Two focused
checks and retained independent semantic review suffice for the unchanged science. Current test
scratch was cleaned. The old P78 publication scratch remains with the same CM and its existing
`rejected: blocked by policy` removal receipt; no bypass or repeated removal occurred.

[Collection acceptance](native_link_loss_b02_p79_20260909/collection_acceptance.json) records
all byte checks, finite checkpoint checks and complete costs. The verified local runtime copy is
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/exp/native_link_loss_b02_8902_p79_20260909`.
Root owns normal remote worktree/output reclamation after preserving it and the fixed dependency.
The configured fetch used an empty refmap into FETCH_HEAD, leaving the old remote tracking-prefix
collision intact while fetching the exact source successfully. It adds no source or science
ambiguity. There is no live process, monitor handover, retry or further accepted invocation.

## 6. Decisions this intake produces

**Object-tier acceptance.** Options: (a) accept a valid complete mixed B, retaining the adverse
T−F primary and negative WITHIN T−G; (b) quarantine for a concrete integrity defect;
(c) select the favorable two-instance mean as a replacement conclusion. Recommend and select
**(a)**. Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**.
The measurements are trustworthy and the frozen rule was applied. B02 does not consume a C
object; its sole execution allocation is complete and no additional invocation remains.

**Object-tier next-action recommendation.** Options: (a) do not request a third unchanged
T/G training instance as the next follow-up; (b) request another unchanged instance;
(c) tune or expand the learned package now. Recommend and select **(a), advice only**.
Both learned arms lose to F in both independent matched instances, and the original T−G gain
did not recur. A third unchanged pair could add variation, but it is less decision-relevant than
at the previous n=1 boundary; there is no required favorable-seed stopping rule. Immediate tuning
would select a different question and is outside this allocation. The runner and all arms remain
available as evidence or future controls; this recommendation closes no object family and takes
no direction, Portfolio, priority, PARK or UAV-validation disposition.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a), return the bounded result
without proposing another unchanged run**. The allocated discriminator is complete. F is the
strongest observed fixed null for any later selected successor, so its native return remains the
decisive comparison; a changed treatment or family is not selected here. A family close/recast
would go to the existing Convergence node under a separate conforming scope. There is no new
card, master, scientific source, experiment or Pro Send selected after this intake.

The previous close-call item 004 remains historical and is traced through the CLI to the actual
P79 execution/intake, without an invented owner reply. New-card item 005 remains the frozen-card
record. This ordinary acceptance/next recommendation adds no separate owner item. Audit rows are
`acvc-native-link-loss-b02-p79-acceptance-20260909` and
`acvc-native-link-loss-b02-p79-next-20260909` in [the ledger](../../portfolio/audit/2026-09-09.md).
The existing `continue-low-priority (20260904-acvc-009)` instruction remains applied; recasts 2
and lowest sequencing persist. [Chinese owner brief](../../portfolio/owner/briefs/acvc/2026-09-09_native_link_loss_b02.md).

## 7. Claim ceiling and Root return

Direct observation is the two retained finite-budget native comparisons; inference is that the
unchanged learned-selection package has not beaten competent fixed retrace on this host/base.
Engineering conformance supports trusting the data, not adaptive mechanism value. The outcome-
informed DENSE/8201 choice, two matched training instances with their own evaluation panels,
missing tuned headroom record and unisolated cue/action/partner effects bound the claim.
Historical science keeps its original authority. Direction-local next-action advice does not
become a Portfolio or family disposition.

Root can integrate the accepted card/source/handle/terminal/intake chain, close P79 tracking with
the complete bill, and reclaim terminal remote resources after preserving verified copies.
No technical or scientific acceptance work remains in P79. The next unchanged replication is
not recommended; no changed successor has been selected or allocated by this completed batch.
