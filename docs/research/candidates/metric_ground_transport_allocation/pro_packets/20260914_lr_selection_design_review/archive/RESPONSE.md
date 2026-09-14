**The proposed finite LR-selection comparison is scientifically coherent at its stated prospective B/EXPLORE ceiling. I found no material flaw in its prescribed comparator, per-arm selection rule, fresh-fit holdout estimand or evidence-unit definition that requires replacing the design.** It asks a meaningfully different development question from another fixed-rate recurrence: whether COND remains worth maintaining as an active optional branch when both procedures receive the same specified configuration-selection opportunity. The eight fits buy that changed comparison, not eight replications or an explanation of the earlier native losses.

The main limitation is implementation readiness, not a negative scientific verdict. The published protocol validates supplied evaluation panels and selection records; it does not establish that the native fits completed, that mutable state was fresh, or that selection was persisted before holdout construction. Those dependencies remain for the unfinished runner and its already planned changed-path review. Thirteen reported synthetic tests are not native end-to-end acceptance. No selected rates, native result or launch success is established by these inputs. [Card, opening and §§3–5][S1]; [protocol, `_panels`, `select_learning_rates`, `holdout_primary`][S3]; [reentry intake, first concrete work and final role section][S2]; [TASK][TASK].

Maintained PARK remains a strong alternative. The design is defensible as a bounded investigation, but the evidence does not establish that its expected development value exceeds either PARK or a cheaper recurrence. That comparison remains a reasoned DM judgment. This review neither applies CONTINUE/PARK nor grants funding, resources or launch permission.

## 1. Development value and the limits of the toy motivation

The strongest reason for this object is not simply that tuning is available. The DM has identified a concrete alternative to attributing fixed-setting performance to a representation: scalar learner settings may materially affect the comparison. The question is now about two complete, finitely selected learning procedures. A useful fresh COND-minus-DENSE contrast would support retaining the selected COND option for bounded development; an inside-scale or adverse contrast would weaken that particular case. This can change development effort without changing DENSE's generic default. No hypothetical customer or pre-existing deployment commitment is necessary. [Card, §§1 and 5][S1]; [reentry intake, substantive response to Portfolio][S2].

The toy evidence supports investigating setting sensitivity, but only as a motivating analogy. Its 24 fits used three training seeds and four rates for each actor. Both actors selected the upper grid edge, 3.0. The selected METRIC-minus-FREE AUC residual was +0.0006554780183014955, inside the toy's 0.01 AUC scale, while FREE's selection gain relative to rate 0.1 was +0.20087263319227425. Selection and readout shared the same development panel. These observations make a fixed scalar setting a concrete competing explanation on that toy; they establish neither global optimality nor equivalence. [Toy intake, “What I checked” and “Rule applied verbatim and direct result”][S8].

**They do not establish that native COND losses arose from the Adam learning rate.** The toy used a different allocation task, parameterization and optimization path, with zero-initialized float64 parameters and REINFORCE/SGD-style scalar updates rather than the native recurrent PPO/Adam procedure. Its AUC effect and rate values do not transfer numerically to native final J. The new programme also cannot retrospectively identify the cause of those losses. The reentry intake already makes this distinction; retain it rather than presenting the toy as a native diagnosis. [Toy intake, numerical contract and interpretation][S8]; [new card, §§1–2][S1]; [reentry intake, substantive rationale][S2].

The native contrary evidence remains consequential. Early256 produced +0.015128847632690413 and −0.05684388886006531 J. Equal512 produced +0.005761321371348559, −0.02246957345594415 and +0.02447811898058116 J. TOP8221 and unequal-exposure8231 were adverse for their different procedures. These are not one pooled estimand or a vote over signs. The earlier positive observations remain genuine support for scientific possibility; the adverse observations and observed variability argue against assuming that a three-rate selector will make the optional branch useful. [Prior actual-results review, §§1–3][S6]; [PARK knowledge, retained results and limits][S5].

The prior review's stopping clarification was substantive: inability to prove a mechanism or stable ordering cannot by itself disqualify another B. The DM's subsequent intake accepted that correction and treated PARK as a marginal-value judgment, not a finding of zero information or general inferiority. Reopening a different, explicitly selected programme is consistent with that position; it does not make the earlier PARK scientifically erroneous or reopen the old frozen invocations. [Prior review, §4][S6]; [prior-review intake, findings 1–4 and final disposition][S7]; [current PARK notice][S5].

## 2. What is actually being compared

For arm a, let V(a,k) be its mean validation J after the 8251 fit at candidate k. The prescribed selector is

\[
\widehat k_a=\operatorname*{arg\,max}_{k\in\{\mathrm{base},\mathrm{slow},\mathrm{fast}\}}V(a,k),
\]

with exact ties resolved base, then slow, then fast. The corresponding rates are 3e-4, 1e-4 and 1e-3. Each selected rate is then used in a **new** arm fit at master8252. The evaluated policy is not the winning selection checkpoint. [Card, §3][S1]; [protocol, constants and `select_learning_rates`][S3].

This is an appropriate symmetric opportunity: three configurations, the same training/validation exposure, the same candidate order and the same own-score criterion for each arm. Selecting DENSE by its own highest validation return prevents deliberately choosing a weak DENSE candidate to increase the treatment contrast. Selecting the maximum COND-minus-DENSE difference, choosing a common rate because it favors COND, or overriding an inconvenient DENSE winner would answer a different question. None is prescribed or implemented in the supplied selector. [Card, §3][S1]; [protocol, `select_learning_rates`][S3].

Equal opportunity does not mean optimal tuning, equally accurate selection, equal attainable performance or equal elapsed computation. With one selection master, the best observed candidate can be specific to that initialization and those worlds. Near-ties can make the chosen label unstable. The exact-tie rule is deterministic, not a robustness guarantee. Retain all six candidate means and their panels; do not introduce a tolerance tie, manual override, extra validation or grid extension after seeing them. A slow/fast edge winner remains a finite-grid winner, not evidence that the optimum has been bracketed. [Card, §3][S1]; [protocol, selection record][S3].

The protected native comparison remains five UAVs, fifty uniform users, H256, free-space/no-shadowing, original sum-five-rewards/256 J, legal raw108 actor input, private GRU64 histories, training-only critic information and sampled primitive velocity. COND retains the existing mean visible-partner query and all-partner context; DENSE retains full raw and nonlinear paths. The inherited masked-partner sum/10 is not an invitation to change pooling normalization. PPO retains agent-compound ratios, chunk32, two episodes per rollout, four epochs, entropy0.01 and joint actor/critic clipping0.5. Adam's other settings remain fixed. [Card, §§2–3][S1]; [TASK, protected implementation contract][TASK]; [prior review, §1][S6].

LR therefore changes the joint actor/critic learning procedure, not merely an isolated actor step or attention parameter. Both methods still receive the same legal information. Their representation and optimizer interactions may differ; that is part of the complete procedures being compared, not an information leak or proof of pure geometry. Local recurrence does not reveal partner intent, and shared team reward does not identify individual causal credit. [Card, §§1–2][S1]; [foundations, §§2–4][S10].

## 3. Pairing, state ownership and the selection boundary

### Intentional correlation is not shared mutable state

The card deliberately reuses the 8251 corresponding-arm initialization across rate candidates. This means restoring the same **untrained** COND initialization for each COND candidate and likewise for DENSE, with new optimizer state and new arm/candidate-owned generator instances. It must not mean cloning a previously trained candidate, continuing its Adam moments, or letting its advanced RNG stream feed the next fit. Both arms and all candidates may share address labels as paired experimental inputs while retaining separate mutable objects. [Card, §3][S1]; [protocol, `randomization` docstring and address law][S3].

For b=100000s, training uses resets b+1000+e, persistent velocity b+21 and duration b+4000+e. Evaluation uses resets b+2000+e, velocity b+3000+e and duration b+5000+e. The 256 training and 32 evaluation ranges are separate; 8251 and 8252 separate selection from holdout. Reusing selection validation worlds across candidates is intentional pairing. Different learned trajectories under the same exogenous addresses are expected, not a failure of pairing. [Card, §3][S1]; [protocol, `randomization`][S3].

The six candidate fits consequently are correlated configuration evaluations under one master, not independent replications of the selected programme. Holdout construction must create a new matched pair, private optimizers, environments, recurrent state and generators; no selection weights or optimizer state transfer. The new master is a meaningful fresh-fit boundary under that declared generation law, not a sufficient guarantee supplied merely by writing a different integer in metadata. [Card, §3][S1]; [exposure, independence fields][S4]; [empirical topic, randomness hierarchy][S11].

### What the published protocol establishes, and what it does not

The inspected `_panels` requires the expected arm/rate combinations, stage, evaluation phase, master, LR value, H256, valid episode indices, finite scores and exact evaluation addresses. It rejects duplicates and requires every episode 0–31 in every expected panel, then restores episode order. `select_learning_rates` requires all six panels and computes the two own-score winners. `holdout_primary` checks the complete candidate-mean record, rate labels/values, exact-tie order and consistency of the selected labels with those means; it then accepts only the two selected holdout panels. I found no mismatch between that arithmetic and the prescribed selection/primary. [Protocol, `_panels`, `select_learning_rates`, `holdout_primary`][S3].

**The remaining native-wiring requirements are material to a future integrity claim, but are not newly discovered design defects:**

| Dependency | What must remain true in the completed runner | Consequence if violated |
| --- | --- | --- |
| Complete candidate learning | Each of the six candidate panels belongs to its own complete 256-episode/512-Adam fit at the actual prescribed rate, with correct state ownership and native reward. Evaluation labels alone do not establish this. | The full selected-procedure comparison is unsupported; apparently complete evaluation rows cannot substitute for missing or misconfigured learning. |
| Pre-holdout selection persistence | Finish all candidate fits/panels, select by own J, save the complete selection record and its hash, then construct any holdout fit. The final computation consumes those fixed selections. | Holdout-informed configuration choice is not the declared fresh selected-arm comparison. |
| Fresh holdout learning | Restore neither candidate weights nor optimizer/RNG state; construct and train new8252 arm instances using only the fixed selected rates. | Re-evaluation or continuation of a selected checkpoint is a different procedure and cannot be presented as the card's independent fitted holdout. |

`holdout_used_for_selection=False` is a recorded assertion, not an enforcement mechanism. A byte hash identifies saved content but does not independently prove when it was saved or how the fitted policies were created. The protocol has no native construction, training, persistence-order or optimizer-state consumer to inspect. In particular, its `_panels` consumes evaluation rows, not complete training records. The smallest adequate verification is the already planned focused runner review of these actual producers and consumers, with readable fit counts and the saved-selection-to-holdout path. No new provenance service, historical replay or expensive diagnostic is needed. [Protocol][S3]; [card, §§3–5][S1]; [specification, §§11.4 and 11.8.6][S9].

The present absence of a complete runner is expressly disclosed. It limits certification of implementation and any later result; it does not make the prospective scientific question incoherent. I have not inspected or rerun the unlisted synthetic tests and do not extend their reported success into native acceptance. [Reentry intake, actual execution facts and final section][S2]; [TASK][TASK].

### Missing or damaged candidates

Requiring all six complete trustworthy candidates is appropriate for **this selected complete-procedure estimand**, not a universal B rule. Silently dropping a failed candidate changes the offered search opportunity; choosing among surviving candidates or substituting the base rate changes the selector. A low but valid return is not a failed candidate and must remain eligible under the fixed rule. A missing/nonfinite/misbound required panel instead makes this programme incomplete, with no COND performance polarity. [Card, §3][S1]; [protocol, `_panels`][S3].

The future runner must preserve partial facts and map a protocol rejection to that incomplete status rather than treat it as a low score, proceed with a reduced grid, or launch a replacement. Operational recovery of already produced bytes is separate from extra scientific fitting. Conversely, an administrative problem does not erase an independently trustworthy narrower observation; the failed dependency determines the claim limit. These are already the card and task's intended semantics. [TASK, missing-candidate constraint][TASK]; [specification, §11.8.7][S9].

## 4. Holdout inference and the possible development actions

The sole new primary is

\[
J_{a,e}=\frac{1}{256}\sum_{t=0}^{255}\sum_{i=1}^{5}r_{a,e,i,t},\quad
 d_e=J_{\mathrm{COND},e}-J_{\mathrm{DENSE},e},\quad
 \widehat\Delta=\frac{1}{32}\sum_{e=0}^{31}d_e.
\]

Here the policies are the newly trained8252 instances at the separately selected rates. The protocol reports all own-arm values, ordered differences, their mean and sample-SD divided by sqrt(32). That SE describes final-world sampling variability **conditional on this selection and these fitted policies**. It omits variation from selecting on another master and from another final training pair. The final holdout is fresh relative to selection; it is not an independent replication of the entire research programme or a population confirmation. [Card, §3][S1]; [protocol, `holdout_primary`][S3]; [foundations, §6][S10]; [empirical topic][S11].

A fresh final fit is useful because the new comparison need not reuse the winning validation fluctuation or candidate weights. It still can select a rate poorly suited to the new initialization. Thus a positive result is one realization of the complete programme, and a negative result can reflect selection instability, finite learning, representation differences or their interaction. Neither sign isolates a cause. Six candidate panels cannot be pooled with the final panel to improve an apparent training-level sample size. The whole programme itself was chosen after earlier outcomes and remains adaptive B. [Card, §§1 and 3][S1]; [exposure, independence fields][S4]; [specification, §§11.8.2–11.8.5][S9].

Without an untuned same-holdout comparator, the primary does not estimate how much tuning helped either method. The fact that base is in the grid guarantees an available candidate, not holdout noninferiority to base: selection noise and new training can reverse the ranking. If both winners are base, the fresh contrast remains valid and all eight fits remain real exposure; it does not demonstrate a tuning benefit. If a boundary rate wins, that does not require expanding the grid. Omitting the untuned holdout arm relinquishes the causal tuning-gain claim rather than damaging the selected-procedure primary. No additional arm is needed for the narrower stated question. [Card, §§1 and 3][S1]; [protocol, selection rule][S3]; [empirical topic, whole-method versus mechanism comparison][S11].

MEI0.01 J remains a local useful-development scale, with the inherited0.014 continuously covered-user coverage contribution as its historical rationale. It is not a significance threshold, an oracle gap, an equivalence margin already established statistically, or a repository-wide investment rule. Preserve the actual point estimate, uncertainty and adverse worlds even when assigning the card's descriptive branch. [Card, §3][S1]; [prior review, §1][S6]; [specification, §11.7][S9].

| Complete programme outcome | Scientifically supported interpretation and review of the proposed action |
| --- | --- |
| Holdout Delta > +0.01 | A useful realized selected-COND contrast can favor active, bounded optional-branch development. It does not establish recurrence, the best LR, superiority of geometry, or a reason to change the generic DENSE default. |
| Inclusive −0.01 to +0.01 | This observation supplies no beyond-scale advantage. Retain its sign; it is not equivalence or a population null. PARK or another specifically justified modification is a development judgment, not an automatic consequence of an inconclusive test. |
| Holdout Delta < −0.01 | Adverse evidence for this realized selected-procedure choice. It weakens the case for unchanged optional-branch work but does not show that COND generally fails or that tuning caused the loss. |
| Required candidate, selection or holdout integrity is incomplete | No complete-programme polarity. Preserve independently trustworthy partials and the precise dependency gap, without replacement seeds/candidates, automatic retries or adverse-result wording. |

The positive and negative branches have the same empirical ceiling. Different development actions are legitimate, but a positive result must not make another grid/seed automatic, and an adverse result must not acquire population authority merely because it favors stopping. A later independent fit with fixed selected rates would address those configurations' recurrence; rerunning selection with new selection and holdout masters would address programme repeatability. Those are different possible future questions, neither selected here. The current branch logic is adequately bounded; no customer requirement, positive-first prerequisite or fixed seed quota is warranted. [Card, §5][S1]; [prior review, §§2 and 4][S6]; [specification, §§11.8–11.9][S9].

## 5. Are eight fits proportionate relative to two or PARK?

The prospective counts below are the supplied machine-generated arithmetic, not work executed by this review. [PLANNED_EXPOSURE.json][S4].

| Quantity | Per fit | Selection | Holdout | Complete programme |
| --- | ---: | ---: | ---: | ---: |
| Fits | 1 | 6 | 2 | 8 |
| Training episodes | 256 | 1,536 | 512 | 2,048 |
| Validation/final episodes | 32 | 192 | 64 | 256 |
| Native team ticks | 73,728 | 442,368 | 147,456 | 589,824 |
| Two-episode rollouts | 128 | 768 | 256 | 1,024 |
| Adam calls | 512 | 3,072 | 1,024 | 4,096 |
| Actor collection/evaluation/replay uses | 1,679,360 | 10,076,160 | 3,358,720 | 13,434,880 |

Dominant work is six selection fits plus two fresh holdout fits, five actor histories, H256 and four recurrent PPO passes per rollout. Candidate search has only the three LR settings. There is no joint-action enumeration, controller/trajectory search, checkpoint competition or repeated solver. The six candidate fits are intrinsic to this selected learning procedure, not an A-stage diagnostic that other B work must first pass. Eight fits are the required count for the exact three-rate/two-arm/fresh-fit design; they are not a universal minimum for investigating learning settings. [Card, §§3–4][S1]; [protocol, `planned_exposure`][S3].

An unchanged recurrence costs two fits, 147,456 ticks and1,024 Adam calls. This design therefore uses four times the fits and specified learner exposure for only one final matched comparison. It exchanges additional sampling of fixed-rate recurrence for a different question about configuration selection. The fresh holdout is not dispensable without changing that question: reading the validation maxima would instead evaluate the data used to choose the configurations. A two-fit recurrence is a better-targeted use of work when fixed-rate recurrence is the intended decision; it does not substitute for the six-candidate selected-procedure comparison. [Card, §§1 and 3][S1]; [exposure][S4]; [prior review, work comparison][S6].

**The strongest PARK argument is that the added selection stage may simply add noise and cost to an already weak/mixed native development record.** One selection master can choose a fortunate candidate; no observed native response surface shows that this grid solves a practical weakness. A complete eight-fit programme can still end with one unrepeatable local point. This is stronger than objecting that it cannot prove a mechanism. The DM acknowledges both the extra work and selection instability; its contrary judgment is that testing equal finite selection is more likely than another unchanged draw to change maintenance of the optional branch. That is a concrete but unquantified value judgment, not a new empirical finding. [Reentry intake, substantive response][S2]; [PARK knowledge, stopping reasons][S5].

On that basis, the added work is proportionate to the **changed narrow question**, though its comparative expected payoff remains uncertain. I find no necessity to replace it with a two-fit recurrence, nor evidence that PARK is scientifically wrong. Both are legitimate alternatives whose choice depends on development value rather than completeness of a mechanism explanation. The review supports the coherence of the DM's rationale, not a global ranking or a finding that this is the best use of resources. [Specification, §§11.8–11.9][S9].

The per-fit cost law includes initialization,65,536 collection ticks,512 complete recurrent PPO/Adam calls,8,192 evaluation ticks and assigned checkpoint/publication/readback/exit. Required runner work, focused checks/review, Git/staging, admission, observation, collection/intake, integration and preservation are counted once, not hidden as free support. The earlier188.19/190.58-second pair walls and378.77-second sum are sizing observations only. The new15–30-minute native estimate is explicitly UNMEASURED; four times the fits does not certify four times the wall or the full support cost. [Card, §4][S1]; [prior review, §5][S6].

The1,800-second-per-fit and14,400-second-study watchdogs are ordinary technical plans, not scientific endpoints or owner hard caps. Serial CPU FP32/thread1, fresh physical and effective4GiB admission, and no new paid/peer resource commitment remain the stated execution boundary. Old RSS does not establish future peak memory or availability. Native unit rates, full support/provider/lifetime costs and aggregate CPU remain UNKNOWN. No fresh timing pilot or retrospective cost reconstruction is needed to complete this design review. [Card, §4][S1]; [exposure][S4]; [specification, §§11.8.1 and 11.9][S9].

## 6. Minimal response and actual source limits

**Required change to the specified scientific selector or final estimand: none found.** The material open dependency is implementation of the complete six-fit selection boundary and genuinely fresh holdout, not an absent statistical qualification. The DM's existing runner acceptance should address the three producer/consumer dependencies in §3; protocol-only results must not be described as native conformance. This review adds no numerical task or approval layer.

The claim limits to retain are: toy sensitivity motivates but does not diagnose native failures; validation winners are finite and conditional; fresh final fitting is not programme replication; the paired-world SE excludes selection/training-population uncertainty; and the selected-arm contrast does not identify tuning gain or change DENSE's default automatically. These are largely already explicit. A future assertion that the hash alone proves holdout isolation, that tuning necessarily strengthened DENSE, or that a negative selected contrast establishes broad COND failure would require correction of that assertion, not retrospective alteration of an old result.

All eleven manifest paths were accessed through the connected GitHub connector at their declared versions. Exact paths and full commit references are linked below; the table identifies the passages used. The fixed current [TASK][TASK] was read separately. One transient foundations read disconnected; the same pinned read subsequently succeeded. No decision-relevant or explanatory access gap remains.

| Reference | Actual material used |
| --- | --- |
| [S1 — LR-selection science card][S1] | Complete prospective §§1–5 at3594eafe28ed91b2558fcc064e46ea714edd2e1c. |
| [S2 — DM reentry intake][S2] | Complete changed-question rationale, contrary PARK case, execution limits and final peer-role correction at the same revision. |
| [S3 — protocol.py][S3] | Complete constants, address law, panel checks, own-score selection, holdout reducer and static exposure code at the same revision; inspected, not executed. |
| [S4 — planned exposure][S4] | Complete generated counts, stage multipliers and independence/zero-native-exposure fields at the same revision. |
| [S5 — PARK knowledge][S5] | Current CONTINUE notice and retained historical reasons, signs, reusable assets, limits and reopening conditions at the same revision. |
| [S6 — prior actual-results review][S6] | Complete122-line response at47699fcad5714bbe8cfca43abef78c89a3887b62; especially §§1–5 and claim limits. |
| [S7 — prior-review DM intake][S7] | Complete response to findings and historical disposition/delivery record at3594eafe28ed91b2558fcc064e46ea714edd2e1c. |
| [S8 — toy B03 intake][S8] | Scalar-setting,24-fit, same-panel selection, grid-edge, AUC and inferential-limit passages at the same revision; historical dispatch wording not applied. |
| [S9 — empirical specification][S9] | Adopted §§11.4 and11.7–11.10 at1c6ba284ecd03c20fc6b7e6fa1a3d27efd630abf. No unrelated object exception applied. |
| [S10 — foundations][S10] | §§2–4 and6 at that same method revision; used for information, joint credit, finite learning and uncertainty distinctions. |
| [S11 — empirical topic][S11] | Comparison objects, randomness hierarchy, complete-method attribution and return/cost limits at the same method revision. |

The test suite, full native runner, imported factories/learners, old raw archives, original toy curves and linked outside papers were not retrieved or executed. Reported prior results and technical checks remain source reports rather than new independent reanalysis. I did not read later scientific output from branch advances. The unrelated older attached task does not define this review.

Issue18's live body still describes an older post8231 question. Its five historical delivery comments were reconciled only for publication; none was a matching delivery of this LR-selection review in the checked state. The current TASK controls the response path and scope, and the issue body is left unchanged. Branch HEAD, ancestry and target reads are administrative delivery checks, not replacement scientific inputs. Historical Transport uncertainty, cleanup restrictions, C meanings and family boundaries remain untouched. New scientific imports, model/RNG/environment construction, fitting, evaluation, checkpoint loads, numerical reanalysis, tests and profiling by this review are zero. Only the scoped response publication and its delivery comment are external changes.

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/3594eafe28ed91b2558fcc064e46ea714edd2e1c/docs/research/candidates/metric_ground_transport_allocation/MGTAP_LR_SELECTION_B01_SCIENCE_CARD_20260914.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/3594eafe28ed91b2558fcc064e46ea714edd2e1c/docs/research/candidates/metric_ground_transport_allocation/reentry_20260914/DM_REENTRY_INTAKE.md
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/3594eafe28ed91b2558fcc064e46ea714edd2e1c/experiments/candidates/metric_ground_transport_allocation/mgtap_lr_selection_b01/protocol.py
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/3594eafe28ed91b2558fcc064e46ea714edd2e1c/docs/research/candidates/metric_ground_transport_allocation/reentry_20260914/PLANNED_EXPOSURE.json
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/3594eafe28ed91b2558fcc064e46ea714edd2e1c/docs/research/candidates/metric_ground_transport_allocation/PARK.md
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/47699fcad5714bbe8cfca43abef78c89a3887b62/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260913_early256_results_review/archive/RESPONSE.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/3594eafe28ed91b2558fcc064e46ea714edd2e1c/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260913_early256_results_review/INTAKE.md
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/3594eafe28ed91b2558fcc064e46ea714edd2e1c/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_MAIN_INTAKE_20260904.md
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/1c6ba284ecd03c20fc6b7e6fa1a3d27efd630abf/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/1c6ba284ecd03c20fc6b7e6fa1a3d27efd630abf/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/1c6ba284ecd03c20fc6b7e6fa1a3d27efd630abf/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[TASK]: https://github.com/CartmanFatass/My-paper-code/blob/bceb608c441c7c94ebbded02f011c7eb4d85f675/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260914_lr_selection_design_review/TASK.md
