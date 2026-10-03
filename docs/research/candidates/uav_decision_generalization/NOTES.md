# uav_decision_generalization

Lead: Codex native DM `/root/dm_decision_generalization`, parent Root
`01a0f779-ace2-74e1-85ad-e0997b61d505`. Author on shared `main` at
`/home/fires/hmasd-wsl`; own this direction's implementation/tests/notebook/runs/scratch.
Other directions and Claude's paused source assets are read-only.

<a id="b00-source-and-reuse"></a>
## 2026-10-02 UTC / 2026-10-01 PDT — Source, reuse and cost reconstruction before selection

**Assigned question.** Can explicit relational/geometric and permutation structure
help a learned assistant turn available training experience about complete UAV
joint decisions into useful new-world decision quality, compared with the
same-data unstructured numerical learner and competent ordinary rules? The target
is reusable decision generalization. A successful package would not identify
architecture causality or pretrained-language value.

Root subsequently relayed the owner's assignment of detailed proposal construction
to the temporary Astra Max Oracle `/root/successor_allocation_review`. This entry
supplies source/asset/cost facts to that selection; it does not select an architecture,
launch a diagnostic, or make the Oracle a standing approval dependency. Root owns
the initial overlap/investment allocation. The DM retains scientific challenge,
subsequent design refinement, execution and reading. **No new fit, model forward,
native/static query, label or result run is selected or executed here.** Work so far
is primary-source reading, saved-file/schema/hash inspection and notebook publication.
An independent ResearchCritic review must cover the actual consequential selection;
the old B01 disposition does not itself select this successor.

### Inherited explanation and scope

Read the current owner resume and relevant published RESEARCH topics 3, 4 and 8 at
`35332c2ce`: shared reward does not create decentralized information; trainability,
new-world decision quality and complete-package usefulness are different; symmetry
must match actual information/action/transition semantics. These alter the proposed
interpretation: this host is one centralized initial complete-layout selection with
a frozen executor, not a test of changing teammates, decentralized credit or an
autoregressive learned executor. Preserve native service/reward consequences, not
just loss, accuracy or coordinate proxies.
Before publication, refreshed `origin/main` and read Root's current three-DM
allocation/owned exploring entry at `9e2d12418`; the substantive background above
is unchanged, and the new allocation records the same source-only preparation.

The original B01 [complete reading](../typed_joint_skill_decision/NOTES.md#b01-complete-reading),
[full independent diagnosis](../typed_joint_skill_decision/NOTES.md#b01-independent-result-review)
and [disposition](../typed_joint_skill_decision/NOTES.md#b01-independent-disposition)
were read in full. Published result `7a488add8`, retirement `09a69ed0e`; exact
recipe source/tests are recoverable at
[`61a2dfa9cde0178d482d0a079c5629c3bcb7789e`](https://github.com/CartmanFatass/My-paper-code/tree/61a2dfa9cde0178d482d0a079c5629c3bcb7789e/experiments/candidates/typed_joint_skill_decision).
The source is retired from current main, not missing empirical evidence.

| B01 quantity, block 1 / 2 / 3 | Values |
|---|---|
| N final training menu regret | .000608594 / .000804063 / .000519219 |
| N final exposed-test menu regret | .098826250 / .101463125 / .101863438 |
| L-F final training regret | .100506875 / .096801875 / .103364375 |
| L-F final exposed-test regret | .123149063 / .083615625 / .106664375 |
| Native menu best minus training-selected fixed | .085838125 / .075858125 / .080320625 |
| Static rule regret | .000596563 / .001286563 / .001146250 |
| N final minus fixed, complete C_bh | -.012988125 / -.025605000 / -.021542813 |

N's real updates and near-perfect training choice weaken an absent-learning or
unable-to-fit account. They do not identify the missing representation, amount of
data, objective or optimizer. L-F's weaker training fit is a different finding.
The complete menu has genuine conditional opportunity, while static ranking wins
341/384 test worlds and both learned packages fall below fixed in every block.
Retain the active severe losses and local gains; no common failure diagnosis, no
general impossibility conclusion, and no claim that flat N tested geometry-aware
learning. A useful gain over fixed/unstructured policies need not beat static to
establish a narrower capability, but static's strong performance remains material
to deployment and further investment.

### Exact decision object and fitted exposure

Source locations below refer to `61a2dfa9c`, paths under the historical direction.
A bounded registered Scout reconstructed these paths read-only; the DM additionally
read the load-bearing representation, preparation, label, optimizer and selection
source and the original complete result review.

- `contract.py:150–214`, `models.py:24–44`: legal learner information is initial UAV
  XYZ `[6,3]`, user XY `[50,2]`, BS XYZ `[3]`, and up to eight complete plans with
  assigned target XYZ `[6,3]`, `kind`, `k`, construction slot, legal mask and display
  order. World/seed IDs, native scores, outcomes and generation provenance are
  excluded. N repeats 121 shared geometry scalars plus 18 assigned-target scalars
  per candidate, divides every coordinate by 5000, and appends kind3+k3+slot8 one-hots:
  **153 inputs**. No learned or training-set normalizer is used.
- `run_b01_native.py:152–187`, `contract.py:91–147`: the menu is built from the full
  reset with a private `PCG64(0)` on a deep-copied environment before outcomes.
  The raw constructor uses geometry, not outcome-ranked full-planner outputs.
  Preferred construction slots are three plain k4/5/6, three relay k4/5/6,
  another distinct relay and one flat. Canonical exact sorted-row XYZ de-duplication
  and relay/flat/plain filling preserve at most eight distinct layouts. Ranking
  within those construction classes uses served-subset size, layout hash, then
  source index; this is construction metadata, not measured Q.
- Target matching minimizes maximum travel distance, then total travel distance
  across the 6! permutations. Exact ties retain the first permutation. B01 passes
  canonical row-sorted layouts into matching and stores targets in UAV identity
  order. `run_b01_native.py:189–205` executes that fixed assignment by the frozen
  closed-loop straight-line move/hold executor over all H500 native steps. No
  averaging of alternative target coordinates occurs.
- `run_b01_native.py:284–298`: label `Q` is complete episode mean
  `coverage_backhauled`, the fraction of 50 users attached to routed UAVs, not the
  contract reward, terminal coverage or a static score. Each world has all eight
  complete outcomes, and soft labels are `softmax(Q/.02)` over legal candidates.
  Feature hashes, slot order and target identities bind labels to prepared inputs.
- `models.py:214–220`, `run_b01_learning.py:183–230`: N is shared-candidate
  153→256→256→1 GELU, 105,473 parameters. Each block has independent 256-train and
  128-test worlds. Base seeds are 106100000/106200000/106300000; N initialization
  uses base+20001 and shuffling base+20002. N fits 64 epochs, batch32, AdamW
  lr .001/weight decay .0001: **512 updates and 16,384 world exposures per fit**.
  Float32 CUDA, TF32 disabled; masks/soft-CE/argmax are fixed. L-F uses the same
  labels and exposure with its frozen 1024-dimensional features and separately
  adapted scorer (1,052,673 parameters, lr .0001). Different capacity/optimization
  is part of that package contrast.

### What structure can and cannot mean here

N already uses one scorer shared across candidate rows. Reversing only candidate
display order changed N's chosen slot in **0/384** old test worlds, versus
**239/384** for L-F. Thus candidate-display dependence is not an established N
bottleneck. The common exact-logit tie rule chooses the first displayed option;
zero observed reversals is not a universal floating-point/tie invariance proof.

User rows are flattened by N without a shared user encoder. The actual
`envs/pettingzoo/uav_env.py:523–556` generator puts five clusters in consecutive
ten-user blocks; within each block is Gaussian draw order, with clipping. Thus
the old flat vector retains a cluster-block ordering cue, even though explicit
cluster labels/centers are excluded and users have equal weight with no separately
sampled demand/type. Removing this ordering is a representation restriction; do
not silently assume the old input was an arbitrarily shuffled set. UAV initial rows and
assigned-target rows are flattened in paired UAV identity order. A representation
may compute coordinate relations/distances from these already supplied values
without collecting another outcome or environment observation. A joint permutation
must preserve each UAV's initial/target pairing. Permuting targets alone changes
the executed assignment; regenerating menus after changing row order is not the
same intervention as changing the scorer's presentation of an already fixed plan.
The constructor, canonical coordinate/hash ordering, assignment ties, native radio
ties and numerical reductions must not be silently equated with arbitrary exact
symmetries of the full data-generation pipeline.

The exact B01 host uses deterministic free-space path loss and no shadowing;
the source's separate 3gpp elevation/LOS branch is not this experiment. The task
fixes a ground plane, altitude limits, box and BS; arbitrary 3-D rotation,
translation or reflection is not justified by the word geometry. The old S7 fixed
NE normalization result in RESEARCH topic8 is specifically adverse and does not
test this host or prove that its generator is invariant. A structured package is
a conjecture about finite learning on this legal object, not an identified cause
of the previous loss.

`run_b01_native.py:251–263` gives the static comparator the legal instantaneous
native radio evaluator on the initial positions and each proposed complete target
layout. `contract.py:217–227` ranks static coverage, with max/total travel/slot
tie breaks; its travel variant uses an arrival-time surrogate. These rules have
known task computation, no future H500 truth and no fit. Full planning is a separate
test-only scale reference, performing flat then relay search with two 3000-query
ceilings. A future learner supplied static coverage, route membership or another
computed physical summary receives additional task computation/knowledge even
though it is derived from the same exogenous geometry; give an ordinary comparator
the same addition and count it. A raw-coordinate representation contrast and that
knowledge-enriched package contrast have different interpretations.

### Existing data can be reused without regenerating B01

At 2026-10-02 00:19 UTC, read-only SSH confirmed all three original roots on
`hmasd-wsl-node`, under `/home/wu/projects/HMASD/runs/typed_joint_skill_decision/`.
The complete manifests and summaries were hashed again and matched published
locators; this check did **not** repeat every per-file hash audit or replay a model.

| Phase | Summary SHA256 | Manifest SHA256 |
|---|---|---|
| `b01_native_a01` | `a483734dbb8aa24c440f83378694945ff99fb038b194b53b5d32ce9ea30eda5a` | `f38fa0f8159ccd45874771886b0977eab15ea2e1978cb94fa41630874b8aca0d` |
| `b01_learning_a01` | `5052c2c2560e707b7ad6ddaddef25fd74bc92444a328889776600d5cc4473b93` | `16aca6b9ec339a7f7fa94b7d4a86eed34d917cbee956a9db2f810f132d32bd85` |
| `b01_read_a01` | `213be039392a3d69b8d66935ae884316875b8e9e371a86d4b5f580fbc1191271` | `d211d941250d3daea7ed14fde17395e6fc8720e831de05d13bbaa192471b94e3` |

Verified the stored schemas and paths (representative record inspected, all six
initial/final checkpoint paths enumerated):

- Native `prepared/b{1,2,3}/{train,test}/{world}/features.json`, `provenance.json`
  and `codec.json`; labels live separately at
  `worlds/b*/{train,test}/{world}/labels.json`, alongside `slot0.json`…`slot7.json`.
  Labels contain `address`, `feature_sha256`, `slot_order`, `Q`, `soft_targets`,
  `ordinary`, all `candidate_results` and raw-trace locators. Existing geometry,
  labels and ordinary scores are therefore sufficient for declared development
  without another reset, candidate construction or native trajectory.
- Learning `fits/b*/{N,L}/initial.pt`, `final.pt`, `optimizer.pt`, config,
  `updates.jsonl`, summary and initial/final/reversed test JSON files are present.
  CPU-cloned N state dictionaries are self-contained once the exact numerical
  architecture is reconstructed. L-F's scorer alone is not the full deployment
  package; it also needs the one retained frozen source/tokenizer and vendor binding.
  The old dedicated environment was retired. This numerical question need not
  restore the entire language runtime or duplicate that weight object.
- Reader `blocks/b1.json`, `b2.json`, `b3.json` retain the original full readings.
  Local compact [summary](../../../../runs/typed_joint_skill_decision/b01_read_a01/summary.json),
  [384-world table](../../../../runs/typed_joint_skill_decision/b01_read_a01/per-world.csv)
  and [cost reading](../../../../runs/typed_joint_skill_decision/b01_read_a01/cost-summary.json)
  already support paired fixed/static/N/L comparisons and old-world regret by
  arithmetic, without model or native calls. All-eight-option Q lives in the
  canonical labels, not the compact CSV.

All B01 test outcomes have been exposed to the research team and this selection.
They can be named development evidence, never a genuinely fresh successor
endpoint. Reusing the old three N final checkpoints would cost zero new N fits,
with inference still billed and the comparison conditional on those training
instances. A new fitted arm, re-fit control, tuning choice, augmentation or label
reweighting must have its own prospective exposure; it is not free because the
data were already paid. Any fresh-world endpoint and all stopping/selection rules
remain to be fixed in the actual selected study.

### Primary-source and historical boundaries supplied to selection

All three local stores were searched; the load-bearing passages below were read
directly. They are antecedents and constraints, not a novelty verdict or proof of
UAV generalization.

- Repository foundation **B01**, Albrecht/Christianos/Schäfer,
  `docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf`, PDF pp.304–307
  (printed pp.275–278), §9.7: distinguish weak agent interchangeability from
  identical-policy optimality; pooled shared parameters can aid learning but can
  impose an inappropriate policy restriction. Mapping here: a shared entity
  encoder must still retain initial/target/role distinctions. The source's
  parameter-sharing example does not establish variable-N or this scorer's gain.
- Inst-sci **MARL-0571**, McClellan et al., JSON
  `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0571.json`, corresponding
  `pdf/MARL-0571.pdf`, pp.3–5: geometry-equivariant messages use relative squared
  distances, with task symmetry assumptions; their vanilla EGNN action output also
  has an exploration bias. This paper's RL action-exploration repair does not
  transfer directly to our offline scalar ranker over a fixed complete menu.
  [Official primary record](https://papers.neurips.cc/paper_files/paper/2024/hash/4830a9b95a2f63fc4b3fe09abc18f045-Abstract-Conference.html).
- Inst-sci **MARL-0078**, Utke/Houssineau/Montana, JSON
  `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0078.json`, corresponding
  `pdf/MARL-0078.pdf`, pp.3–4: MARC's relational abstraction explicitly drops
  absolute position **and distance**, assumes relative predicates suffice, and
  warns that continuous-state abstraction may lose consequential information.
  For this radio task, near/far distances and altitude can matter. The analogy
  motivates representing relationships, not blindly copying its distance-free
  predicates or inheriting its claimed task results.
- My-lib **icml-2023-pmlr-v202-chen23i**, Chen et al., arXiv 2305.18951,
  `/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2023/pmlr-v202-chen23i/arxiv-2305.18951.pdf`,
  pp.3–4: the model preserves the subgroup fixing gravity rather than imposing
  full O(3), because external forces distinguish directions. Mapping: altitude,
  ground, BS and bounds constrain a UAV symmetry claim. Morphology-agnostic
  locomotion results are not evidence that our scalar selector will generalize.
  [Official primary record](https://proceedings.mlr.press/v202/chen23i.html).

July evidence is also not a blank slate. The
[G11 original result](../../cdc/EVIDENCE_NOTES/20260723_SLOT_LAYOUT_INVARIANCE_G11_FORMAL_RESULT.md)
reports invariant outcomes under four controlled slot maps for three imported
checkpoints, zero new optimization; its
[prelaunch source correction](../../cdc/EVIDENCE_NOTES/20260723_SLOT_LAYOUT_INVARIANCE_G11_PRELAUNCH.md)
kept autoregressive position draws, rather than incorrectly remapping them by
lifecycle key. This demonstrates a specific distinction between semantic
relabeling and changing the random decision program; it is not new-world UAV
learning. The [R30 design](../../designs/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md)
already contains complete autoregressive joint editing. The original
[R54 external review](../../../external-review/gpt5_6_pro/20260717_r54_hfsr_result/GPT5_6_PRO_RESPONSE_RAW.md)
accepts implementation validity but reports failed full-set supervised access and
does not identify a unique representation/optimization root cause. It even proposes
direct member–candidate relations as a subsequent conjecture. Therefore neither
complete joint decisions, full inputs, supervision nor relational terminology is
new in itself; these historical contracts are not revived or made admission gates.

### Feasibility and complete price facts, before a design is selected

The numerical representation seam is `numeric_rows`/the scorer, after the frozen
feature object is constructed and before `masked soft-CE → argmax slot`.
Reading preserved data, computing deterministic geometry transforms and training
with it can be isolated in this direction's own small implementation/tests. A fresh
endpoint would additionally use the original read-only native constructor and
executor at their bound hashes. Do not restore the whole retired language recipe,
modify Claude's host, or silently change its assignment/menu semantics. Concrete
implementation L0, high-risk engineering review and launch inputs follow selection.

Already-paid B01 price is **6 fits, 3,072 updates, 4,808,000 native steps,
783,749 static queries, 1,552 full frozen source forwards** and the complete
5,376-scorer-context/9,600-episode reader. Admitted-process CPU was 7,261.651462s;
GPU reserved window 547.037157s. This is cumulative exposure inherited by a
successor, not its new bill. Support was incompletely metered.

The three N fit summaries give active training wall **3.376905 / 3.842079 /
4.060591s**, each for 512 updates. These omit input preparation, process/GPU
reservation, checkpointing and independent reading; they cannot price a new graph
architecture. Old per-world menu construction/matching average about .011/.017s;
static scoring adds about .0043s. N's assembled old test selection is .0291s versus
static .0328s, expressly not a measured complete online benchmark. Native step
timer totals 4642.777401s over 4.808M steps; nested timers overlap and must not be
added as independent CPU.

Exact scalable counts can be declared without a pilot: each new arm retaining
64×256 training exposure costs 512 updates and 16,384 world contexts per block;
three blocks cost 3 fits/1,536 updates/49,152 contexts for that arm. A fresh endpoint
of m worlds with all-eight-option native regret costs **8m H500 episodes = 4000m
native steps**, plus construction/matching/static queries, endpoint inference and
reading. Executing only selected distinct slots can cost less but no longer gives
exact full-menu regret. Reusing old training labels costs zero new label episodes;
choosing fresh training data does not. Full-planner search is optional for a future
scientific question, not automatically copied from B01; if bought, count its
actual search calls and complete episodes. A new model's runtime/RSS/engineering
cost remains unmeasured, not zero or the old MLP's cost.

**Current disposition:** source/asset reconstruction supports a feasible new-world
learning comparison and identifies design hazards, not an empirical geometry
benefit. No architecture, new batch or hypothesis-repair chain is selected here.
Root's concrete initial allocation/design integration is the pending dependency;
this does not stop independent source work or create a per-fit permission loop.
No producer/observer was created, no bulk was copied, and no deletion was performed
in this preparation (0 bytes reclaimed). Original adverse evidence stays canonical.

<a id="b01-concrete-contract-proposal"></a>
## 2026-10-02 — Outcome-free specification of Oracle's A/R proposal, under selection review

Root relayed a temporary-Oracle proposal for six new fits, A/R in each of the
three original data blocks, with frozen original N finals as a third comparator.
Root assigned the actual scientific review to `/root/next_study_review` in a
separate context; that reviewer returns directly to Root. The Oracle confirmed
that exact widths/tensors were not already fixed and could be made concrete here
within its intended comparison. The following is a single proposed instance,
with arithmetic parameter counts only: **no model was instantiated, no forward,
fit, static/native query or executable implementation was performed.** Final
selection and any substantive review changes will be appended, not inferred.

### Comparison, information and fixed tensor instance

Intended comparison is R−A on fresh complete C_bh and equivalent menu regret.
A−old N asks about the richer deterministic geometry/representation package;
R−A asks about a relational computation/sharing package given the same tensors.
Neither contrast isolates invariance, geometry, pretraining, parameter count or
depth as a cause. Fixed/static/travel remain substantive ordinary references;
the full planner remains a separately priced scale reference. The intended
contribution is finite-data decision generalization, without presuming practical
deployment savings against a static rule that costs only about 4.3ms extra.

For each complete candidate, obtain all values from the same existing legal raw
feature object. First divide every physical coordinate by 5000, as old N did.
Original IDs below mean the original feature-row indices, not hidden cluster
labels or new user data. Derive these same tensors once for both A and R:

| Tensor | Shape | Exact content |
|---|---|---|
| U | `[6,12]` | Initial XYZ3, paired assigned-target XYZ3, original UAV-ID one-hot6 |
| Y | `[50,52]` | User XY2, original user-row-ID one-hot50 |
| B | `[3]` | BS XYZ |
| M | `[14]` | Original kind3, k3, construction-slot8 one-hots |
| E_UY | `[6,50,8]` | UAV-to-user relative vector and squared norm, at initial and target positions |
| E_UU | `[6,5,8]` | UAV-to-other-UAV relative vector and squared norm, at initial and target positions; nonself IDs ascending |
| E_UB | `[6,8]` | UAV-to-BS relative vector and squared norm, at initial and target positions |

For each edge, each four-field stage is `(receiver_UAV_XYZ − sender_XYZ,
sum(delta**2))` in normalized coordinates. Users have z=0; BS is unchanged between
stages; a peer uses its own initial or target position respectively. There is no
radio computation, learned forecast, outcome, min/max search, generator cluster
center or static score in these features. All existing user-row cues, full
absolute geometry, metadata and UAV-to-target identity bindings are retained.
Concatenate in the table's order, row-major within tensors: width
`72+2600+3+14+2400+240+48 = 5377`. Candidate display order, legal mask and exact
tie rule are inherited separately from B01.

**A:** one shared per-candidate MLP, `5377→64→64→1`, GELU after its first two
linear layers, all biases enabled, **348,417 parameters**. The one-hot identity
tensors are explicit constants at the corresponding canonical positions; their
inclusion is not counted as additional exogenous information.

**R:** width64 throughout, with all linear biases enabled:

1. Separate U12→64→64, Y52→64→64 and B3→64→64 encoders, GELU after each linear:
   4,992 + 7,552 + 4,416 = **16,960 parameters**. Keep Y/BS embeddings fixed
   across the three subsequent message layers.
2. At each of **three layers**, use independent per-edge-type two-linear MLPs
   `[receiver64,sender64,edge8]136→64→64`, GELU only between linears. Parameters
   share across edges of that type, not across types or layers. Each MLP has
   12,928 parameters; 3 types×3 layers total **116,352**. For each receiving UAV,
   mean its 50 user messages, mean its five other-UAV messages, and retain the
   single BS message. These are three separate 64-vectors.
3. Concatenate the previous UAV embedding and these three aggregates:
   `256→64→64`, GELU between linears, then add the previous embedding and apply
   GELU. Independent updates per layer, **61,824 parameters** across three layers.
4. Read out `[mean(U_final)64,mean(Y)64,B64,M14]`, width206, using
   `206→64→1`, GELU between linears: **13,313 parameters**.

Total R **208,449 parameters**; no layer norm, dropout, data augmentation,
alternative width, distance binning, tie repair or architecture scan. A has about
1.67× R's parameters and is shallower; old N has 105,473 parameters and hidden
width256. These are declared package differences, including optimization
difficulty, not matched-capacity or isolated-symmetry controls. IDs move with
their entities under a presentation reordering; no physical ID exchangeability
or arbitrary geometric symmetry of the host is assumed.

Both new arms propose old N's AdamW lr .001, weight decay .0001, betas(.9,.999),
eps1e-8; 64 epochs, batch32, fixed final checkpoint, no validation selection.
Use each block's original training worlds/labels and order seed `base+20002`;
initialize A with `base+41001` and R with `base+42001`. These are fresh purpose-
specific model seeds, not identical initialization. The old N checkpoint is
frozen and incurs no new N fit. Retain float32/TF32-disabled numerical semantics;
the current configured Torch2.7.0+cu118/NumPy1.26.3 interpreter can support this
numerical-only work without restoring the retired language environment. Actual
node admission and exact dependency verification remain for a selected launch.

### Freshness, external bindings and exact work counts

Proposed fresh world IDs are **106130000–106130127, 106230000–106230127,
106330000–106330127**, one 128-world panel per original block. A saved-file check
found zero intersection with all 1,152 canonical B01 prepared addresses. Full
integer searches of current local candidate source/notebooks/run records found
no prior use; keyed `world/world_id/world_seed/reset_seed/seed` searches in the
remote B01 and coupled-host original records also found no matching world. A
broad non-keyed search found 106130057 inside an old RNG-state array, which is
not world execution. This is a scoped record check, not proof about unavailable
history. No proposed world has been reset or queried by this work.

Training receives only the original train splits. The already-exposed B01 test
worlds remain existing development evidence; **zero new forward** on them is
needed for this proposal. Freeze new weights before fresh labels/outcomes become
available for scientific reading. No source/candidate search, held-out endpoint,
checkpoint or epoch may be selected from fresh outcomes.

Bind the existing canonical native and learning roots through their published
summary/manifest digests above; keep them as external inputs on the compute node,
not copied raw datasets. Each reused N final binds its original state digest:

| Block | Original N final parameter digest |
|---|---|
| 1 | `c61e2846205748d7168e93fc48d0d3c2b0b4b3695ab3cb5223c1fd7a123a786d` |
| 2 | `8e4e76de7a3e300e8a504b2fe04a76128f7799ca7126d616c105e6e57ff4c115` |
| 3 | `be386396f4f3311cd0ad7d5941499883fcd126544b8c0f32236fd0f54d8bdb2e` |

These are parameter digests from the original reader, not `.pt` byte digests;
the existing manifest supplies file-byte identities. Source binding includes the
five original native host/planner/environment files at their B01 hashes and the
retired scorer/contract identity at `61a2dfa9c`. Reconstruct only the required N
architecture in this direction if selected. The remote canonical repository has
a controlled overlay and an old Git HEAD; do not merge/reset it, alter sparse
checkout or infer its state from local HEAD. Use the normal admitted immutable
snapshot and manifest-bound external inputs, with Root handling a genuinely
needed shared configuration change.

| Work | Proposed count |
|---|---:|
| New fits | 6: A/R × 3 original independent data blocks |
| New optimizer updates / training world-context exposures | 3,072 / 98,304 |
| New training-label native episodes | 0 |
| New model endpoint contexts | 4,992 |
| Independent functional reader scorer contexts | 4,992 |
| Endpoint + reader total | **9,984** |
| Fresh menu episodes, if all eight candidates legal | 384×8 = 3,072 H500 |
| Fresh full-planner episodes | 384 H500 |
| Frozen native order-correctness episodes | 16 H500, eight each on first two fresh block-1 worlds |
| Total native steps, eight-candidate case | **1,736,000** |
| Static queries, including ordinary and full planner | **≤2,307,840** = 384×(9+6001) |
| Native reader episode reads | 3,456 unique complete traces + 16 audit-alias records |
| Saved update records read | 3,072 |
| LLM forward/download/model replica | 0 |

Endpoint arithmetic: every new fit reads initial and final on 256 training plus
128 fresh worlds, so `6×2×384 = 4608`; three frozen N finals each read 128 fresh
worlds, adding384. The independent reader covers the same4,992 contexts without
re-running encoders, optimizers or the environment. Static allowance includes
each world's initial position plus eight candidate snapshots and the full
planner's two3000-query ceilings plus one metadata query. Native audit aliases
reuse one verified evidence copy after equality, as in B01. If the inherited
legal-menu contract yields fewer than eight candidates, retain that world and
its mask/fallback; count actual episodes/queries below these bounds rather than
manufacturing alternatives or replacing the world.

The price forecast relayed by Root is **1–3 admitted CPU-hours**, with **5 CPU-hours
and 1 GPU-hour ceilings**; **10–16 support-hour equivalents** and **.6–1GiB new
evidence** forecast separately. New graph runtime remains unmeasured. Source
snapshots, existing input bytes and runtime footprint are separate from new
evidence; report actual allocated peak and full process/readback cost. Any
ceiling-triggered technical stop retains all paid attempts and creates no retry
entitlement. No extra profiling fit, augmentation sweep or surprise reader panel
is included. Numerical correctness checks on small fixtures will be explicit
implementation checks, not new scientific worlds or selective performance screens.

Unresolved selection details are scientific disposition/prediction, the exact
native-tail summaries and useful outcome branches; the independent review can
correct this proposal without adding a second review ladder. Until Root's
initial allocation resolves, the implementation and all result effects remain
unstarted under this concrete scope.

<a id="b01-original-selection-review"></a>
## 2026-10-02 — Original independent selection review and accepted disposition

Root-assigned registered ResearchCritic `/root/next_study_review`, UUID
`01a0f9fe-de22-7d73-82c2-129a0cadede6`, separate context (`fork_turns=none`).
Root verified actual gpt-6-astra/max. Source `/mnt/c/Users/fires/.codex/sessions/2026/10/01/rollout-2026-10-01T17-23-45-01a0f9fe-de22-7d73-82c2-129a0cadede6.jsonl`,
`event_msg/task_complete.last_agent_message`, line218. Exact payload 7077 UTF-8 bytes,
SHA256 `60c359e6ab3e61d0b91c1a0f5ef1407f0d70ba1f8b25ee1286320e1fe1f031e2`. Mechanically preserved in full below.

<!-- BEGIN ORIGINAL A/R SELECTION REVIEW -->
**Recommendation: retain and select this one bounded A/R study.** It addresses a real finite-data generalization problem with a meaningful matched-input comparison. I find no material contradiction requiring a different study, additional diagnostic fits, or another scientific review.

I received no inherited Root/DM conversation. The assignment already contained the Oracle proposal, so this was independent-context review, not blind review.

B01 supports a specific starting point. N’s training regret was .00061/.00080/.00052, versus fresh-test regret .09883/.10146/.10186. L-F’s training regret remained approximately .10. These are different failures; neither establishes missing geometry as the cause. Meanwhile, static scoring reached the menu optimum in **341/384 worlds**, with approximately .001 residual regret. The [original summary](/home/fires/hmasd-wsl/runs/typed_joint_skill_decision/b01_read_a01/summary.json) and retained canonical block files support these distinctions.

The constructive and adverse evidence both matter. From complete raw traces:

- At **106310114**, N achieves C_bh **.53788**, versus fixed **.25384**, with higher contract reward too.
- At **106210018**, N achieves **.00280**, versus fixed **.65560**; its selected trajectory spends **469/500 steps with zero service**.
- At **106310048**, L-F achieves **.05096**, versus N/fixed **.72156**, including **415 zero-service steps**.

These are consequential executed choices with completed trajectories and reached targets. They establish useful local learning behavior alongside severe generalization failures.

The concrete construction is scientifically coherent. A receives the raw record plus explicit geometric calculations; R receives those same quantities through shared entity/edge computation. The supplied specification preserves user row identity—including the generator’s cluster-block cue—UAV initial/assigned-target pairing, BS relations and candidate metadata. It introduces no native radio scores or future outcomes. N already shares its scorer across candidates and had **zero display-reversal choice changes**; R therefore tests entity/edge structure, not a demonstrated candidate-order defect.

The two contrasts remain **package comparisons**:

- **A−old N:** geometric calculations plus changed representation, width, capacity and optimization geometry.
- **R−A:** relational architecture, sharing, depth and associated finite-training behavior.

The primary-source bridge is appropriate: conditional transform-and-aggregate functions motivate shared processing, but do not guarantee sample efficiency at 256 training worlds. [Deep Sets, §§2.2–3](https://proceedings.neurips.cc/paper/2017/file/f22e4747da1aa27e363d86d40ff442fe-Paper.pdf). I also read MARL-0571, pp.3–4, directly in its [local primary-text extraction](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0571.json). Its geometric messages supply an architectural analogy; its equivariance assumptions and RL exploration remedy do not establish this offline ranker’s benefit.

One concrete interpretation correction: **348,417 versus 208,449 parameters is not a functional-capacity ratio.** In A’s fixed flattening, 2,536 identity inputs are constant, including 2,480 always-zero inputs. Their contribution can be folded into the first bias, although they affect initialization, optimization and storage. Preserve that fact; no capacity sweep or extra arm is needed.

The strongest objection is investment value, not feasibility. Static already captures nearly all same-menu opportunity at approximately **4.3 ms additional scoring per world**. Historical assembled selection costs were about **29.1 ms for N versus 32.8 ms for static**, with omitted online costs explicitly acknowledged. Graph processing and feature construction may consume that small margin. This purchase is justified as a **fixed-data learning/generalization study**, not by an assumed deployment speed advantage over full planning.

The complete observation should change decisions as follows:

| Fresh-world outcome | Supported consequence |
|---|---|
| R improves over A and old N across blocks, especially beyond fixed | Retain a conditional relational-package capability; better training fit is unnecessary. No symmetry-causal or deployment claim. |
| A improves over N, with no resolved R increment | Retain the geometric-feature package; additional graph complexity has not earned preference. Similar point estimates do not establish equivalence. |
| R beats A but remains below N/fixed, or gains occur only in training | Preserve the relative effect, but end these exact recipes without automatic extra layers, data or epochs. |
| Effects reverse across blocks or remain imprecise | Report unresolved generalization value; no stable winner or automatic fourth block. |
| Mean coverage improves with adverse reward/service tails | Retain the measured capability and tradeoff together; do not turn it into an unrestricted use claim. |

Three independent downstream training/data blocks remain the inference units. Fresh worlds evaluate those fits; they do not create additional training replication. The outcome-exposed B01 test panel should remain historical development evidence, with no new forwarding or tuning required.

The now-concrete price is adequate for selection:

- **6 fits; 3,072 updates; 98,304 training-context exposures.**
- **Zero new training-label episodes; zero LLM forwards/downloads.**
- **1,736,000 native steps maximum**, including fresh all-option consequences, full-planner reference and 16 correctness episodes.
- **2,307,840 static calls maximum.**
- **4,992 endpoint + 4,992 independent-reader scorer contexts**, plus 3,456 unique episode reads and the declared audit/update reading.

Freeze these counts and the supplied tensors, widths, optimizer settings, seeds and endpoint rule before implementation/results. This is ordinary completion of the selected design, not another review gate. The **1–3 CPU-hour forecast, 5 CPU-hour plus 1 GPU-hour ceiling, 10–16 support-hour forecast and 0.6–1 GiB new-evidence estimate remain forecasts**. R runtime and complete online cost are unmeasured. B01’s approximately 2.017 measured process CPU-hours are inherited cost, not a price guarantee.

I checked all three canonical block tables, manifest/summary hashes, the five pinned native-source hashes, configuration and exit witnesses, all three retained N-final checkpoint file hashes, and **12 complete raw traces** spanning five positive/adverse worlds. I checked feature/label/provenance and native reset bindings in three consequential worlds. I did not execute models, native queries or experiments, replay optimization, repeat every historical byte audit, or certify the unimplemented successor’s engineering correctness.

**MATERIAL_DISSENT: no — I support this bounded six-fit investment as a conditional generalization study. The evidence does not support calling it an identified B01 repair, a symmetry result, or a demonstrated deployment saving.**


<!-- END ORIGINAL A/R SELECTION REVIEW -->

<a id="b01-selected-contract"></a>
### DM disposition and frozen B01 contract, before implementation/effects

Root read the complete independent answer and selected this single A/R investment,
MATERIAL_DISSENT:no. I adopt the comparison and all scope limits. In particular,
A's2,536 identity inputs contain2,480 constants equal to zero; the other56 equal
one. Their first-layer contribution can be folded into a bias, although storage,
initialization and optimization differ. **Raw parameter counts are not functional
capacity ratios.** The numerical1.67 ratio in the proposal describes raw counts
only and is not a reason to favor either arm. No capacity sweep is added.

Freeze the tensors, A348,417/R208,449 parameters, architecture, initialization and
shuffle seeds, optimizer/final-epoch endpoint, training/fresh world IDs and exact
work ceilings in the proposal above. This is an exploratory three-independent-
training/data-block comparison using the same already-paid training examples;
fresh evaluation worlds are nested observations, not extra training replication.
No B01 old-test forward/tuning, LLM call/download, new training label, alternate
checkpoint, supplementary fit or automatic retry is selected.

**Prediction and reading.** The prospective relational-package prediction is a
positive R−A complete fresh C_bh difference (equivalently lower regret) in all
three blocks, with gains beyond old N/fixed supplying evidence of useful
conditional generalization. This is a point prediction, not a calibrated
confidence or an equivalence/adoption criterion. Retain all blocks, world losses
and training readings. If A improves over N without a resolved R increment,
retain A's feature package rather than choose R by sophistication. R−A improvement
below N/fixed, training-only gains, unresolved or sign-reversing effects do not
justify automatic extra epochs/layers/data/seeds. The exact outcome branches of
the original review apply. Ending these recipes would not exhaust the parent
question; subsequent investment must use the complete evidence and an independent
diagnosis, not silently extend this batch.

For every endpoint report training/fresh masked soft-CE, native mean regret,
selected-slot counts, learner movement and complete native C_bh. For fresh
worlds retain original contract-reward mean, frontend capacity with path and
mean relays/routed UAV as secondary native readings. From the same complete
saved selected traces additionally compute episode minimum and p10 C_bh,
zero-coverage step count and longest zero-coverage run, and final100-step mean
C_bh. Keep per-world values/differences and cross-world lower-tail summaries
separate. These measure service harm/continuity, not unmodeled battery safety.
No new episode or proxy-only pass condition is created by reading saved traces.

Primary inference is the mean of the three paired block effects R−A, with all
three signed effects and a descriptive df2 t95 interval. Within-block paired
world intervals describe evaluation variation conditional on a fitted pair.
They do not establish384 independent learning replications or equivalence.
Report A−N, R−N and comparisons with fixed/static/travel/full planner without
substituting a favorable one for the primary comparison. Fixed is each block's
original training-selected construction slot3 with the inherited legal fallback.
All argmax decisions use the original display-order exact-tie rule. The accepted
GPU endpoint choices determine the reported native outcomes; independent CPU
scorer reconstruction uses B01's1e-5/1e-6 tolerance, preserves every component
flag and choice mismatch and does not silently widen tolerance. A flag need not
erase a trustworthy native outcome; a missing/incorrect feature/checkpoint binding
quarantines its dependent reading and is not a negative scientific result.

### L0 — Implement one fixed three-phase A/R comparison

Deliverable: admitted numerical fitting, frozen native fresh-world collection and
independent reading of this exact B01, with compact outputs and one durable bulk
copy. Own only `experiments/candidates/uav_decision_generalization/` and matching
tests for implementation; DM alone owns this notebook, index and Git publication.
Other shared-main writers are active: preserve their edits and all original
typed/Claude files. No authoring checkout, source restore in the old direction,
shared-core/profile edit or result launch belongs to the Implementer.

Use original `61a2dfa9c` contract/data/native/learning/reader code as recoverable
reference where it preserves semantics, without importing retired modules or
copying the unused Laya/tokenizer/vendor stack. New explicit argparse entrypoints
may share small direction-local helpers. Every result entry calls current
`scripts.hmasd_admission.require_admission` before scientific effects, binds its
source/invocation/external input bytes, and uses the actual configured node and
the current launcher. Keep old native five-source digests and the exact feature,
menu, matching, H500 executor, reward, RNG, mask/tie and ordinary-rule semantics.
Save all new weights before generating/reading fresh native outcomes. Load the
old N checkpoint through the exact original numeric architecture/normalization;
do not fit it again.

Fit outputs record actual optimizer/update/context counts, losses, nonzero finite
gradients, parameter movement and initial/final checkpoint identities. Endpoint
and independent-reader budgets total9,984 contexts exactly. Reader reconstructs
scorers independently of the candidate module, reads all complete native traces
and3072 update records, checks actual choices and input identities, and preserves
numerical adverse flags. It does not re-execute an optimizer or native episode.
Source/external-input identities, exit/status, failed attempts and cumulative
CPU/GPU/allocated storage accounting stay recoverable; missing telemetry is
reported as unmeasured, not silently0. Bound scientific call counts and declared
5CPU-hour/1GPU-hour limits, retaining partial outputs on failure rather than
retrying. Reconcile the same accepted native handle throughout observation.

Checks: pure/mock tests for exact tensor schemas/values/IDs, parameter counts,
candidate mapping and dataset split binding; wrong source/file hashes rejected;
tiny deterministic gradient/update and independent-functional-scorer comparisons;
native-runner tests with mocked frozen host/metrics and exact counter arithmetic;
reader tests with fixture traces including severe zero-service intervals. Tests
use `tests/AGENTS.md` scratch lifecycle. No full model/native performance screen
or extra scientific world is a correctness test. Required independent engineering
review covers actual numerical/RNG/result-identity/admission behavior after the
diff exists. The DM reads the diff/checks, resolves findings and accepts it before
publishing exact inputs and launching. This selection requires no further Root
per-run acknowledgment.

### Original adviser provenance and phase boundary

Root subsequently published the temporary Oracle's complete final advice in
[`RESEARCH-three-dm-oracle-design-advice.md`](../../archive/2026-10-01/RESEARCH-three-dm-oracle-design-advice.md),
commit`e3532228b`; final-answer SHA256
`84df55fb2298b8ff2820f7518e7ac86bae1cca01b2b5bcf6400ff2127a7ad802`.
Its A/R section reports the concrete DM tensor instance and supports the already
selected comparison. It is proposal provenance, not an independent review or
implementation certificate. Its informal A≈R branch is read under the explicit
independent-review limitation above: an unresolved contrast does not establish
equivalence. The earlier Oracle relay was an initial proposal, not this final
whole-task answer.

Implementation uses three admitted phases: learning freezes all six initial/final
A/R weight pairs and records3,072 train endpoint contexts; native collection binds
that complete fit manifest before any fresh-world generation, then records1,920
fresh endpoint contexts including frozen N; reading independently reconstructs
all4,992 saved scorer contexts and the complete native/update evidence. The old
test split receives no new forward. All phases consume digest-bound external
locators and an exact cumulative bill; old canonical raw evidence is read in
place rather than copied. Phase completion itself is not the scientific result.

### Implementation handback and engineering cost, before result execution

Registered bounded Implementer`/root/dm_decision_generalization/implement_ar_comparison`
wrote only the assigned direction code/tests, then froze its source for independent
engineering review. The DM read the numerical tensor/model, native collection,
functional reader and binding paths. Two draft integration mistakes were corrected
before any launch: entrypoints now contain the literal admission calls required by
the launcher; the native-step ceiling is1,736,000, not the draft1,718,000 typo.
Actual launch syntax uses the supported`--out` alias so source-snapshot output
remapping and invocation identity apply. Relevant host/environment/configuration
trees have no source diff from original`61a2dfa9c` to current published main.

Final focused checks passed27 scientific tests and4 launcher/admission tests.
The five measured pytest invocations, including resolved fixture/test-import
failures, cost19.41s wall and19.96s process CPU in total. Their sequence was
21passed/1failed(6.67s wall,6.87s CPU),3passed/1failed(.45/.31),
24passed(6.45/6.04),4passed(.22/.22),27passed(5.62/6.52).
The three numerical-suite invocations executed12 synthetic one-context AdamW
updates,12 synthetic training contexts and18 separate candidate/functional-reader
scorer contexts:30 synthetic scorer contexts including training forwards. They
used0actual native/static/environment calls. These are engineering fixture costs,
separate from the six scientific fits and9,984 scientific endpoint/reader contexts;
the measured CPU is carried into the initial cumulative study ledger. Static
compilation, source inspection and CLI-help checks were unmetered, not zero cost.

Checks cover exact shared tensor values/IDs/counts, masks/ties, tiny deterministic
gradient updates, independent layer arithmetic, changed-hash and wrong-address
rejection, old-training-only access, mocked native count arithmetic and complete
trace reading including469zero-service steps. They do not establish CUDA numerical
behavior, actual-node admission or any native performance result. Independent
read-only engineering Reviewer`/root/dm_decision_generalization/review_ar_engineering`
is inspecting this actual fixed implementation; no result operation is active.

### Independent engineering review and DM acceptance

The registered independent Reviewer returned the following complete engineering
answer, without DM conversation inheritance. This review is separate from the
scientific selection review above.

<!-- BEGIN ORIGINAL B01 ENGINEERING REVIEW -->

**No material engineering finding remains in the reviewed implementation. No blocking repair identified.** DM retains acceptance.

Checked the selected contract against all ten direction modules and their callers: admission precedes scientific effects; external manifests and sequential source identities bind each phase; all six fits and saved weights precede fresh generation; old-test records receive no new forward. Tensor construction, paired targets, masks, shuffle/model seeds, AdamW configuration, frozen N loading, GPU-authoritative choices, independent CPU reconstruction, complete native reading, update-chain reading, and count ceilings match the contract.

The five pinned native files match their declared hashes and have no diff from `61a2dfa9c`. Native wrapper semantics are inherited unchanged apart from fresh addresses and phase integration.

Validation:
- **27 numerical/native/reader tests passed:** 5.59s wall, 6.62s process CPU, 317,804 KiB peak RSS.
- **4 launcher/admission tests passed:** 0.23s wall, 0.22s process CPU.
- Existing pytest scratch lifecycle completed normally. No source edits or result-bearing probes.

Residual limits: CUDA execution, actual six-fit runtime/memory, remote external bytes, and the complete production phase sequence were not exercised. Optimizer verification intentionally checks saved chains and terminal state without replaying optimization.

Reviewed package fingerprint: `144e0d73cf892057aceadeaed467af8db063ab24438e323fd943cbece6897bff`—SHA256 of newline-joined, filename-sorted `filename SHA256(bytes)` entries for direction `*.py`.

<!-- END ORIGINAL B01 ENGINEERING REVIEW -->

I accept this fixed implementation after reading its paths and checks and verifying
the exact reviewed ten-module fingerprint. No scientific comparator, seed,
endpoint or budget changed. The Reviewer's necessary independent rerun adds6.84s
measured CPU and5.82s wall; cumulative measured engineering tests are26.80s CPU,
25.23s wall,16 synthetic one-context updates/training contexts and24 separate
synthetic scorer contexts (40including training forwards),0actual native calls.
The initial ledger includes26.80s CPU and0GPU seconds; scientific counters remain
zero. Unmetered source/CLI inspection stays explicitly unmeasured.

The selected executing node is existing`wsl_4070` using its configured numerical
interpreter, with no new environment/profile/download. Old source/data summaries
and manifests were already presence/hash checked; admitted phase loaders verify
all declared canonical input bytes in place before scientific consumption. First
launch will publish this source and the exact three small locator/ledger inputs,
then use fresh actual-node admission. Failure or uncertain acceptance is preserved
under the same native handle, without automatic retry.

### B01 learning acceptance and observation

Source`89845b9746f7f8aa0451e04caf059082639ec671` was published before the
sole supervisor request`uav-decision-generalization-b01-learning-a01`.
The [native manifest](../../../../runs/uav_decision_generalization/b01_learning_a01/launch-manifest.json)
records accepted actual-node admission; the
[fresh memory assessment](../../../../runs/uav_decision_generalization/b01_learning_a01/admission-preflight.json)
passed at2026-10-02T01:04:18Z with14,605,631,488effective available bytes and the
unchanged4GiB floor. The supervisor's exit0 completed launch acceptance, not
the six fits. The same manifest/operation is the recovery identity.

The DM armed`tools/hmasd_wait.py` for this native operation and drained generation1:
accepted/running, matching live runner/supervisor identities, consistent records,
no summary or exit witness yet. Private request is
`temp/directions/uav_decision_generalization/wait-learning.json`; observation
registration is not assumed future delivery. This native DM remains active through
terminal collection, fresh native evaluation and complete independent reading.
No duplicate request, outcome-based choice or new fit is authorized by observation.

### B01 learning terminal collection and prospective fresh phase

The same operation terminated with a consistent valid exit0 and both recorded
processes absent. Observer generation1 emitted READY; its attempted App wake
reported`-32600: direct app-server input is not allowed for unloaded spawned
sub-agents`. The active native DM drained the event directly and consumed it in
generation2. This delivery limitation did not lose the scientific operation or
authorize another launch.

Collected compact manifest/config/summary/status/exit/logs into
[`runs/uav_decision_generalization/b01_learning_a01/`](../../../../runs/uav_decision_generalization/b01_learning_a01/summary.json),
matching SHA256 of every collected terminal file against the canonical remote
bytes. Summary SHA256`7c45a9762c81a072719a4ba48184b60c9beee4dda16ab84eb53e964b026b95dc`;
scientific manifest`c0af7e8079ee9b2e01ce94a88306d5d23c120a499dcd646ba08fd17821377607`.
Canonical initial/final/optimizer weights, all updates and endpoints remain in
the original remote run root, without a bulk replica. Counts are6/6fits,
3,072/3,072updates,49,152contexts per arm,1,536train endpoint contexts per arm,
0native/static calls. The phase reports133.698s wall,125.832s process/finished-child
CPU,128.805s reserved GPU-window wall,1,225,494,528bytes peak process RSS and
399,925,248/492,830,720bytes CUDA allocated/reserved peak. Cumulative measured CPU
including engineering tests is152.632098s. These are technical completion facts;
the complete independent learning/native reading has not happened.

`B01_FIT_INPUT.json` binds this terminal summary/manifest and
`B01_AFTER_FITS_LEDGER.json` carries its exact cumulative counters/CPU/GPU into
the already-selected fresh collection. All six A/R weight pairs predate fresh
geometry generation; their manifest is fixed before the next launch. No endpoint
or hyperparameter is selected from training outcomes, and no scientific input
code changes between the phases.

The completed learning source snapshot`e3329df307ae40388cf383a5b6527463` was
previewed eligible after verified collection. The first apply refused because
the DM's combined measurement/collector parent command itself referenced the
snapshot path (`snapshot is referenced by pid1285789 cmdline`). That parent
exited; measuring separately and invoking the supported collector directly then
passed all normal checks. The snapshot and its Git worktree registration are
absent. Its allocated usage fell820,944,896→0bytes: **820,944,896net bytes reclaimed**.
Required run outputs, manifests/claim and all inherited evidence remain intact;
no copy/archive was made for this deletion. Git object-store size is outside this
working-tree measurement.

### B01 fresh native acceptance and observation

Published source/input commit`6389a9488b76be3e0173dcf38655df443dbad460` preserves
the reviewed numerical source bytes and binds the completed fit manifests.
The sole supervisor request`uav-decision-generalization-b01-native-a01` returned
accepted [native manifest](../../../../runs/uav_decision_generalization/b01_native_a01/launch-manifest.json)
after fresh actual-node admission. It owns the selected384fresh worlds, all
legal menu outcomes, full-planner reference and at most16correctness episodes;
it adds no fitting or new training labels. All GPU fresh decisions precede native
outcome collection within this phase.

The same native handle is registered in private
`temp/directions/uav_decision_generalization/wait-native.json`. Generation3 was
drained and adopted with accepted/running, matching live process identities and
consistent records; summary/exit witness were absent. The learning job remains
terminal/consumed. This is collection in progress, not a read generalization result.

### B01 fresh terminal collection and bound independent reader

The accepted native operation completed with a consistent exit0 at2026-10-02
01:51:00Z. Generation3's checkpoint was drained/rearmed without restarting the
worker; generation4's READY was drained and consumed in generation5. App queue
delivery again reported the known unloaded-child restriction; the active DM read
the original observer events directly. Both recorded native processes are absent.

Every collected compact terminal file was SHA256-compared against its canonical
remote original. [Native summary](../../../../runs/uav_decision_generalization/b01_native_a01/summary.json)
SHA256`007206bf4d5d09f17e34016169fced1cdc811f99daf78ed956c0c26095b0776e`;
scientific manifest SHA256`e03cd4b0d7a9cf8b1cdb39f9190ae24cd30715551d63c390d9742f53e3eb32a6`.
All384fresh worlds have all8legal menu episodes,384full-planner episodes and
16correctness episodes:1,736,000native steps,786,045static queries,0new optimizer
updates. All4,992cumulative GPU endpoint contexts are saved. This phase used
2,284.915s wall,2,264.084082s process/finished-child CPU and4.727246s reserved GPU
window; cumulative measured CPU/GPU are2,416.716184s/133.531748s. Peak process RSS
was611,708,928bytes. Its last scientific storage snapshot records180,043,776new
allocated evidence bytes, excluding later terminal metadata. Both logs are empty.
These are technical completion/count facts, not yet an independently read result.

`B01_FRESH_INPUT.json` (SHA256`f4c313d25d2db582e903880de3e71cd1598c9889cad83592e978755203e6a8e8`)
binds the original canonical native root and these two terminal digests.
`B01_AFTER_NATIVE_LEDGER.json` (SHA256`9eac644d9bcda0fe872869abc3d5ce44fe1c8924560ff84bf7fc2035a94d2fa4`)
continues all37exact cumulative counters and measured CPU/GPU into the selected
reader. No raw/model bulk copy or new scientific input is introduced. The reader
will consume the retained canonical manifests and reconstruct all3,456unique
native episodes,16audit aliases,3,072update records and4,992CPU scorer contexts.

After verified collection, the supported snapshot collector previewed and removed
the terminal native source`cf3c8842fb3948ecb05e0ec921422495`. Its directory and
Git worktree registration are absent; allocated bytes fell820,961,280→0. Together
with the completed learning snapshot, **1,641,906,176net bytes have been reclaimed**.
Canonical unique evidence, source commits and operation claims remain retained.

Root's shared source-snapshot repair`5d4b0619bb373d52a2c9bd0b4f6f1cd4b2ba7102`
only changes creation of future snapshots, materializing inputs outside inherited
sparse patterns. The deployed helper hash was verified as
`83b22ec927b5dd452290a2a331db5b39d62385d831fb867f0c5dae26a254b11d`.
Our accepted operations were unchanged. Reader source/input paths are tracked
direction code and docs locators; their external data roots stay absolute. The new
snapshot uses this repaired helper and the configured`zsh -lic`for complete
partial-clone preparation. Root's actual-node witness anticipates approximately
1.67GiB source materialization, priced separately from new scientific evidence;
its shared object hydration is Root's control cost, not a new fit/native purchase.

### B01 independent reader acceptance

Source/input commit`7a52ac7270ba96a70c1463704cf4140a0641a3bf` was published
before the sole reader supervisor request`uav-decision-generalization-b01-read-a01`.
Actual-node admission accepted at2026-10-02T01:55:37Z; the
[native launch manifest](../../../../runs/uav_decision_generalization/b01_read_a01/launch-manifest.json)
binds operation`36c1972a394b2de599a845377606265359e0f70c8bc70346bb3298e7902c338c`
and immutable source`6ca7e9ec341d40bdb53df4e4e6177249`. The complete preparation
used configured`zsh -lic`. Every exact reader entry/locator/ledger was verified
present in that snapshot and SHA256-identical to published/local inputs; the
scientific loader also verifies all external manifests before consuming data.

Private observer request`temp/directions/uav_decision_generalization/wait-read.json`
registers this original operation in generation6. The observer and active DM keep
the same handle through terminal collection; launch acceptance does not complete
the scientific reading. Root offered reuse of its original independent
`/root/next_study_review` for actual-result diagnosis after full evidence arrives;
no duplicate result Reviewer is assigned here. My own complete reading, costs,
publication and cleanup continue independently of that advice delivery.

<a id="b01-complete-reading"></a>
### B01 complete reading — retained package gain with uncertainty and adverse tails

The admitted reader terminated consistently with exit0 at2026-10-02T02:04:18Z.
Both recorded native processes are absent. Generation6's original READY was
drained/consumed in generation7; observation is now stopped with all three jobs
terminal and no scientific work changed. Every collected terminal file and all
three compact block records match the canonical remote SHA256. The reader
[summary](../../../../runs/uav_decision_generalization/b01_read_a01/summary.json)
SHA256 is`a15e1ba03797f452fa5ad588b5c4091388aafc040e90fbd9e4ff0f28ed50cc7a`;
scientific manifest SHA256 is`58d9414c1224f80875fd776b4ac491eeb32704109f0dfaf2f4940f99d52f9376`.
Canonical full reader outputs remain at
`wsl_4070:/home/wu/projects/HMASD/runs/uav_decision_generalization/b01_read_a01/`:
`raw/blocks/b{1,2,3}.json` contains all384paired world readings; `native/` contains
all reconstructed episode statistics and `learning/` the endpoint/update reading.
The original fresh native traces and learned weights remain at the two locator-bound
canonical roots above. No original B01 test-world forward was added.

The complete reader reconstructed3,456unique H500 episodes,16audit aliases,
3,072update records and4,992CPU scorer contexts; together with saved GPU endpoints
this is exactly9,984scorer contexts. It made0native/static queries and0updates.
All4,992CPU/GPU choices agree. The frozen numerical tolerance flags75contexts
(44A,31N,0R; all at final endpoints); every flag stays in the original rows and
summary. Tolerances were not widened and GPU choices remain authoritative. Full
update-chain checking is not an optimizer replay, and native static query values
remain trusted at the frozen source digests.

The primary fresh complete-coverage difference R−A is positive in all three
independent learning/data blocks, with a weak third block:

| Quantity | Block1 | Block2 | Block3 |
|---|---:|---:|---:|
| R−A complete Cbar_bh | +.041574688 | +.035114375 | +.006254063 |
| R−N | +.045413438 | +.026258750 | +.013903750 |
| R−training-selected fixed | +.020143125 | +.026336250 | +.001640000 |
| R−static | −.063838125 | −.071319063 | −.089985625 |
| R−full planner | −.128539688 | −.140618438 | −.170101875 |
| A−N | +.003838750 | −.008855625 | +.007649688 |
| A final train regret | .000476250 | .000312500 | .000607188 |
| A final fresh regret | .106790938 | .106808437 | .097550625 |
| R final train regret | .045676406 | .053486250 | .057534844 |
| R final fresh regret | .065216250 | .071694063 | .091296563 |
| Frozen N final fresh regret | .110629688 | .097952812 | .105200313 |

The mean of the three primary effects is+.027647708, with the predeclared
descriptive t95 interval[−.019071253,+.074366670] (df2). All-three-positive is an
observed sign pattern, not a precise estimate of repeat-training performance.
The128world intervals condition on each fit;384worlds are not384learning
replications. These fresh worlds use the same generator/task family, not a new
task law or changed user/UAV count. A−N has mixed signs and remains unresolved;
it is neither evidence that distances alone repair the old gap nor an equivalence.

The richer native contract is mixed. R−A reward means are
+.019856540/+.023171619/−.000553428; frontend-capacity differences are
−2.226609/+13.430475/−8.804153Mbps. R has more mean relays in every block.
R−A mean zero-service steps are−6.796875/−3.617188/+1.109375; longest-zero-run
differences−6.093750/−3.039063/+1.632813. Against N, block3 adds8.375mean zero
steps and7.789063mean longest-zero-run steps despite its positive mean coverage
effect; R's maximum longest-zero-run there is435steps versus45forN. The mean
within-episode p10 service difference R−N in block3 is−.002343750. These are
service-continuity adverses; no battery/safety claim follows from these traces.

My current reading is a conditional finite-data package capability: the fixed R
package converts the same paid training exposure into better fresh mean decisions
than A/N/fixed on these three blocks, while A attains nearly exact training fit
without improving fresh quality over N consistently. R's weaker training fit but
smaller fresh regret is compatible with a useful inductive/regularizing package;
it does not identify geometry, permutation invariance, capacity or optimization as
the cause. The point prediction earns retention of the capability/evidence, not
a deployment claim, a reliable magnitude claim or a default extra fit. Strong
ordinary static/travel and full planning remain substantially better, and block3
prevents presenting the mean gain as uniform improvement of the complete contract.
Independent scientific diagnosis and final continuation disposition follow below.

The reader used512.657s wall,515.301041s process/finished-child CPU,0GPU seconds,
and685,846,528bytes peak RSS. Cumulative measured engineering+scientific CPU is
2,932.017230s (.814449CPUh), GPU reserved-window wall133.531748s (.037092GPUh):
6fits/3,072updates/98,304training contexts,1,736,000native steps,786,045static
queries,9,984endpoint+reader contexts,0new training labels/LLM forwards/downloads.
Reader final storage snapshot is12,574,720new allocated bytes before later terminal
metadata. Cumulative/source storage is reported separately at final measured cleanup.
The first two compact-summary arithmetic reads after collection used.002311164s
and.002352691s process CPU,0model/native calls; source/transport/human reading and
helper support time remain unmetered, not zero.

### Additional complete-data reading and path correction

Correction to the preceding canonical navigation: individual endpoint readings
are in`raw/scorers/`, not`learning/`. Update-read aggregates are in the block/summary
records; original optimizer update chains remain under the fit input's`fits/`.
The terminal evidence identities and numerical results above are unchanged.

The compact [DM reading](../../../../runs/uav_decision_generalization/b01_read_a01/dm_complete_reading.json)
is descriptive post-collection arithmetic over the manifest-verified complete
block/scorer/native records, with0model/native calls. It retains world
distributions, numerical flags/timing and14retrospectively selected illustrative
worlds. Selection rules per block were maximum/minimum R−A, maximum/minimum
R−fixed and maximum R longest-zero-run (one overlap). These extreme examples
explain scope and adverse decisions; they are not a new test set or causal test.

R−A win/tie/loss counts are58/43/27,49/50/29,36/50/42 across the blocks. Thus
block3 has more adverse than positive worlds even though its mean effect is
positive. R differs from the frozen slot3 policy in73/85/69worlds; the conditional
mean gain on those deviations is+.035319/+.039659/+.003042, with44/53/36positive
deviations. This is learned conditional choice, with both beneficial and harmful
decisions, rather than a result wholly explained by copying the fixed slot.
Static attains the exact hindsight menu maximum in115/120/111worlds (346/384),
with mean menu regret.001378125/.000375000/.001310938. The full planner is outside
the eight-action menu, so its potentially negative menu-best-minus-policy gap is
not called nonnegative menu regret.

Positive cases are concrete. At106130087, R chooses relay slot5, Cbar_bh .75676,
versus A/N/fixed slot3 at.38360; static chooses the same better complete layout.
At106230071, R slot4 obtains.80136 versus fixed.42500, A.76860 and N.76108.
At106330012, R slot4 obtains.77828 versus fixed.38380, A.69576 and N/static.77468.
Those gains coexist with strong counterexamples: at106130014, R relay slot4
obtains.62052 versus A/static slot5 at.88064; at106230018, R relay slot5 obtains
.60276 versus A flat slot7 at.82548 and static plain slot1 at.90952. None of those
comparisons changes the target assignment or executor.

Block3 retains substantial failures. At106330029, R chooses plain slot1 and gets
Cbar_bh .00212 with474zero-service steps and430consecutive zeros; A/N choose
relay slot4 and get.63028, while fixed/static slot3 get.65560. At106330110, R
again chooses plain slot1: Cbar_bh .01388,447zero-service steps and435consecutive
zeros, versus A/N/static relay slot4 at.65540 with33zero-service steps. These
are wrong complete selections under an unchanged executor. They do not establish
which internal feature, capacity or optimization difference produced the scores.

All75flagged CPU/GPU contexts retain identical choices; the largest absolute logit
difference among these flagged contexts is.00001239776611328125, retained in the
compact DM reading's original comparison fields. Measured GPU endpoint input+scorer
time per fresh context is about1.323ms forA,2.753ms forR and.510ms forN, excluding common
candidate construction/matching and complete deployment costs. This hardware-
specific segment does not establish a useful deployment advantage over static.

The detail extraction used.134698976s process CPU; its first manifest parse failed
on audit-alias rows lacking`path`, before any scientific call, and was corrected
to read only file entries. That failed parse's CPU is unmetered. The subsequent
compact reformat/read used.001735447s CPU. Together with the two initial summary
reads, measured additional arithmetic is.141098278s,0fits/forwards/native calls.
All384formerly fresh outcomes are now exposed for any future design reasoning;
the current study's prospective freshness is not transferable to a revised model.

The terminal reader source snapshot passed supported preview/apply and is absent,
including its Git worktree registration. Its measured allocated usage fell
1,793,269,760→0bytes. All three terminal source snapshots therefore reclaimed
**3,435,175,936net allocated bytes**. The one canonical copy of this study's unique
run evidence currently occupies37,875,712learning +180,060,160native +12,705,792
reader =230,641,664allocated bytes; inherited B01 assets remain separately owned
and unchanged. Local compact records and final scratch cleanup are accounted next.

<a id="b01-independent-result-review"></a>
### B01 original independent result review

Root reused the original independent ResearchCritic context
`/root/next_study_review`, without creating a duplicate reviewer. Root verified
actual turn`01a0fa5f-3e85-7d52-ba1b-4c4571637547`as`gpt-6-astra/max`and supplied
the mechanically extracted complete answer. Original UTF-8 payload:9,512bytes,
SHA256`197e667dcf91fd5ed511d67f46bb488a3f66747a1a1af712a905c66485d3d0d1`.
The following original text is unmodified. Its further42complete trajectory reads,
54reset-identity checks and individual-user examples are independent saved-data
reading, with0model/optimizer/native/static calls; helper arithmetic/support CPU
was not metered into the scientific runner bill.

<!-- BEGIN ORIGINAL B01 INDEPENDENT RESULT REVIEW -->
**建议保留 R 的有限数据泛化能力，结束本次 A/R 固定购买；不把 A 作为几何增量方案继续扩展，也不把 R 升格为静态规则的替代品。** 下一项若继续研究结构作用，我优先比较“训练拟合程度受控的普通 A”与冻结 R，而不是直接给 R 加训练、数据或种子。

本次沿用独立审稿上下文。收到的是任务、证据入口和原方案；我先重建合同、源码及结果，再读 DM 的完整解释。当前 DM 判读与我独立重建的主要事实一致。

我核对了三个阶段的终态、输入摘要／manifest、15 项方向及原生源码绑定；对保留的 fit、fresh 和 reader manifest 文件做了完整字节校验。独立重算三块共 **69 条配对世界向量、81 条原生指标差向量**，核对全部 **4,992 个已保存 CPU/GPU argmax**，检查六条 512-update 链的连续性和有限非零梯度记录。另外读取 **10 个正反世界的 42 条完整 H500 原始轨迹**，重算覆盖、奖励、零服务区间，并从原生用户 mask 检查个体服务反例；另核对六个世界共 54 条轨迹的 reset 身份一致。没有运行模型、优化器、控制器、静态评分或原生环境。其余轨迹的全量重建仍属于已完成 reader 的范围；优化器轨迹没有被独立重演。[冻结合同](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:544)、[完整结果](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b01_read_a01/summary.json)。

主要结果值得保留，但精度有限：

| 新世界完整 C̄_bh | Block 1 | Block 2 | Block 3 |
|---|---:|---:|---:|
| A | .612607 | .603996 | .601403 |
| R | .654181 | .639110 | .607658 |
| 冻结 N | .608768 | .612851 | .593754 |
| 训练选定 fixed | .634038 | .612774 | .606018 |
| static | .718019 | .710429 | .697643 |
| full planner | .782721 | .779728 | .777759 |
| **R−A** | **+.041575** | **+.035114** | **+.006254** |
| **R−fixed** | **+.020143** | **+.026336** | **+.001640** |

三块 R−A 均值为 **+.027648，描述性 df2 t95 区间 [−.019071,+.074367]**。预定的三块同方向预测兑现；这不等于已经精确建立重复训练的总体优势。R−A 的升／同／降世界数为 **58/43/27、49/50/29、36/50/42**，三个中位数均为零，第三块甚至有更多下降世界。128 世界的块内区间条件于各自拟合，不能把 384 世界当成学习复制。

R−N 与 R−fixed 的三个点估计也都为正，但三块区间同样跨零，分别约 **[−.010914,+.067965]**、**[−.015880,+.047959]**。因此合理结论是：**这三个独立训练／数据块显示了可保留的条件泛化增量，幅度和稳定性仍未定。**

训练与新世界的差别清楚地限制了机制解释：

| 菜单 regret | Block 1 | Block 2 | Block 3 |
|---|---:|---:|---:|
| A，训练 | .000476 | .000312 | .000607 |
| A，新世界 | .106791 | .106808 | .097551 |
| R，训练 | .045676 | .053486 | .057535 |
| R，新世界 | .065216 | .071694 | .091297 |
| N，新世界 | .110630 | .097953 | .105200 |

A 几乎记住训练排序，却没有稳定超过旧 N；确定性距离展开这个包没有解决原来的泛化缺口。R 的训练拟合差得多，新世界表现反而较好，支持有用的结构／正则化包这一解释方向。**共享计算、聚合方式、有效自由度、深度、初始化和有限优化仍未分离。** 参数总数也不能解释为功能容量比，尤其 A 有大量固定身份输入。

两臂相对自身初始化都学习了有用选择，但不能用初始化到终点的增量大小比较架构：R 的第一、三块初始化几乎偏向很差的 plain 构造，第二块初始化则几乎总选较好的 slot5。更强的正证据是 R 对训练选定 fixed 的增量和实际有益偏离，而不是恢复了一个差初始化。

普通参照对用途判断仍有决定性意义。static 在 **346/384** 世界达到菜单最大值，三块 regret 仅 **.001378/.000375/.001311**；travel 与它非常接近。R 对 static 的均差为 **−.063838/−.071319/−.089986**。这不是未知未来 Q 泄漏：static 使用合同允许的已知无线规律，reader 未重新查询它，而是核对冻结来源和保存值。full planner 使用更宽的构造搜索，是另行付费的尺度参照，其差距不能全部解释成八菜单内的学习排序误差，也不是逐世界最优保证。

原生正例排除了“R 只是复制 fixed，所以没有学到条件选择”的解释：

- **106130087：**R 选 slot5，C̄_bh **.75676**；A/N/fixed 为 **.38360**。
- **106230071：**R 为 **.80136**，fixed 为 **.42500**。原始用户 mask 显示，R 留下 **2** 名全程从未获得 backhaul 的用户，fixed 为 **19**。
- **106330012：**R 为 **.77828**，fixed 为 **.38380**，A 为 **.69576**。

但同样存在真实、严重的错误选择：

- **106330029：**R 选 plain slot1，C̄_bh **.00212**，有 **474** 个全队零覆盖步、最长连续 **430** 步，最后 100 步均为零；A/N 为 **.63028**，fixed/static 为 **.65560**。R 有 **45/50** 名用户全程未获 backhaul，fixed 为 **8/50**。
- **106330110：**R 为 **.01388**，**447** 个零覆盖步、最长 **435** 步；A/N/static 为 **.65540**。
- **106130014：**R 为 **.62052**，A/static 为 **.88064**；从未获 backhaul 的用户数为 R **13**、A **2**。

这些个体数字来自我对事后选取案例的原始 mask 读取，是反例与正例的补充，不是全 384 世界的新公平性推断。更一般地，团队从未归零不能保证每位用户持续获服务。

其他端点也不支持全面占优。R−A 契约奖励为 **+.019857/+.023172/−.000553**，前端容量为 **−2.227/+13.430/−8.804 Mbps**。第三块 R 相对 N 平均多 **8.375** 个零服务步，最长零区间均值多 **7.789** 步。覆盖增益不能覆盖这些代价；本宿主也没有提供电池安全结论。

数值标记不应删除，也没有证据用它们解释上述错误。共有 **75 个端点上下文、83 个 logit 分量**超出冻结容差：A 44 个上下文、N 31 个、R 为零。全部 **4,992 次 CPU/GPU 选择一致**，标记上下文最大绝对差约 **1.240×10⁻⁵**。原生结果按已保存 GPU 选择读取，未放宽容差；R 的两项严重失败不是 CPU/GPU 选择不一致。

完整成本低于原预算，但并非免费：

- **6 fits、3,072 updates、98,304 训练上下文**；复用原训练标签，新增训练标签和 LLM 前向均为零。
- **1,736,000 原生步、786,045 静态查询、9,984 端点及 reader 上下文**。
- 已计工程和科学链 **2,932.017 CPU 秒，即 .814449 CPU 小时**；GPU 预留窗口 **133.532 秒**，不是 GPU 核心活动时间。
- 新鲜端点的输入构造加 GPU scorer 片段约为 A **1.323 ms**、R **2.753 ms**、N **.510 ms**。它们不含共同候选构造和完整部署成本，不能据此宣布优于 static 的净计算收益。
- 支持工作仍未完整计时。DM 最新清理记录保留一份约 **230.64 MB allocated** 的三阶段证据；该目录分配及删除测量是 DM 的实测记录，我没有重复清理。

最强的简单竞争解释是：**R 在当前有限训练量和 512 次更新下形成了较保守、较不易记忆样本的选择器；优势不一定需要三层消息传递所声称的关系计算。** R 更常选择强的 relay 构造，同时仍做有益和有害的场景选择。固定规则已经控制了“只学一个好 slot”的简单解释，但尚未控制普通 MLP 的训练程度／正则化解释。这是下一项比较应改变的地方。

我的方向建议是：

1. **保留三个 R 终点、完整正反证据及有用实现，结束本批次。** A 相对 N 没有建立稳定几何增量，不按原配方追加；R 的有限泛化能力继续作为后续参照。静态优势限制部署用途，不取消这项学习结果。
2. **不优先购买第四块、更多 R epochs、更多层或更多标签。** 这些会增加投入，却不直接区分当前最强解释。
3. 若继续回答“结构为何有用”，先构造一个有界普通对照：复用相同 A 输入、初始化和数据顺序，按**预先固定的训练拟合规则**选择较早终点，例如每块首次达到该块 R 最终训练 soft-CE 的 epoch，最多原来的 64 epochs；比较它与冻结 A-final/R-final、fixed/static。它检验普通有限优化是否足以获得类似泛化，仍不是纯结构因果实验。若较早 A 接近 R，应优先保留更简单、较便宜的方案；若 R 仍有完整优势，才增加继续投资共享表示的理由。
4. 这项后继目前没有闭合监测前向、reader、支持成本和新评价面板，**尚不构成选定运行**。现在的 384 世界已经曝光，只能作为后续开发证据；不能重新包装成该修改的确认集。DM 可先闭合这一具体比较，也可依据完整机会成本选择不购买，不需要为了维持三个 DM 而立即增加效果实验。

这结束的是当前 A/R 配方的购买，不是广义决策辅助、学习或共享表示问题的责任。

**MATERIAL_DISSENT: no。DM 的主要事实与条件性保留判断得到独立证据支持。我的明确修正是：保留 R 的观察性泛化增量，同时把下一笔投资优先指向普通有限优化这个竞争解释；不从本结果直接推出结构因果、部署优势或自动追加 R 训练。**
<!-- END ORIGINAL B01 INDEPENDENT RESULT REVIEW -->

<a id="b01-independent-disposition"></a>
### DM disposition after the complete independent review

I read the entire original answer and accept its fact reconstruction and bounded
retention judgment; MATERIAL_DISSENT:no. Root independently read and adopted that
same interpretation. The critic's83flagged logit components refine the already
retained75context count, with0changed choices. Its individual-user examples add
an explicit limitation to my team-zero summaries: a team can retain some coverage
while many users receive no service. Those selected examples are not a new
whole-panel fairness estimate. The broader full-contract adverses stay visible.

Keep the three trained R endpoints, useful shared-tensor/scorer/executor/reader
implementation, numerical tests and the complete positive/adverse records. End
this fixed six-fit purchase. A's nearly exact train fit plus unresolved A−N fresh
contrast does not earn an unchanged geometry-flattening expansion. R's worse train
fit is not itself a defect that demands more epochs. Its three positive fresh
mean comparisons against A/N/fixed support conditional finite-data usefulness,
while df2 uncertainty, strong ordinary controls, severe selected-world errors and
block3 reward/continuity costs prevent a robust-magnitude, deployment, universal
service or identified-structure claim. The old raw-N/Laya findings remain scoped
as originally published; they are not rewritten as a common failure mechanism.

The most useful belief change is that a learned complete-choice package can
improve these same-data fresh means without approaching exact training fit.
The unchanged added-distance flat A did not achieve that gain consistently.
This favors studying inductive/regularizing packages over treating train-label
fit as the target, but leaves ordinary finite optimization as a live, simple
competitor to graph-specific explanations. Preserving the observed ability and
its limits is separate from approving another purchase.

For a possible next mechanism question, the critic's fixed train-CE stopping rule
is more discriminating than simply extending R training. Its R thresholds are
already known from the frozen train readings. However, existing A assets retain
only initial/final weights, terminal optimizer state and per-update hashes, not
intermediate epoch weights or complete train-CE monitors. Therefore it needs
three real A refits, up to1,536updates/49,152training exposures plus up to49,152
per-epoch monitoring contexts before independent reading/new evaluation; it is
not a free choice among already-paid checkpoints. It also deliberately changes
optimization exposure and still does not isolate pure invariance. No such fit,
monitor or endpoint is selected or accepted.

My alternative continuation candidate asks whether the frozen learned complete-
choice ability transfers to a different lawful candidate-generation distribution,
with the same original information and competent ordinary controls. That develops
reuse rather than explaining one observed gap, but stable metadata/slot semantics
and a genuinely new endpoint are substantive design constraints. It competes with
ordinary optimization, replication for reliable magnitude, development of other
positive assets, and no purchase on total cost and decision value. These candidates
remain reasoning here, without a new registry, extra architecture or automatic
seed. Root currently owns the concrete cross-question allocation and has assigned
its temporary Oracle to compare those next investments; this is the actual current
planning producer, not a per-run approval requirement. I retain scientific
responsibility for this question through any selected successor.


<a id="b01-final-cleanup"></a>
### B01 final measured cleanup and publication

All three operations are terminal exit0, all observer events consumed and the
observer stopped; current-user open-file inspection found no consumer of the
local deletion targets. The independent result critic has completed its reading.
The earlier three supported remote snapshot removals reclaimed3,435,175,936
allocated bytes. This final local pass removes33Python bytecode files, the four
finished observer/diagnostic scratch files, three duplicate block summaries and
each stage's duplicate manifest, progress and empty stdout/stderr files. No
tracked file was deleted. All15local evidence copies were SHA256-matched to
their retained canonical files immediately before deletion. An initial cleanup
check compared local`blocks/`summaries with remote`raw/blocks/`world records and
correctly failed without deleting anything; the corrected identical relative
paths passed. This inspection is support work, not another scientific reader.

Local allocated usage across all five owned namespaces, including this record
and notebook addition, fell from3,477,504to630,784bytes: **2,846,720net bytes
reclaimed**. Together with source snapshots the measured scoped reduction is
**3,438,022,656bytes**. Every named target is absent; no tool blocker remains.
The three canonical stages retain230,641,664allocated bytes in their original
locations, including all initial/final A/R weights, optimizer/update evidence,
complete fresh traces and independent readings. Inherited B01 assets remain
peer-owned and unchanged. Useful ten-module implementation and four numerical
test files remain; their code fingerprint is unchanged. The stopped observer's
small recovery metadata remains outside the direction; no backup, tar or
duplicate bulk retention was created.
[Exact deletion targets, hashes and measurements](../../../../runs/uav_decision_generalization/b01_read_a01/cleanup.json).

The [shared learning/representation topic](../../RESEARCH.md#learning-representation-finite-data)
now records this finite-data capability, the training-fit reversal and the
unresolved ordinary finite-optimization explanation. The own direction standing ends this fixed purchase and preserves
the long-lived question and unselected continuation choices above.


<a id="b02-source-and-prospective-cooperation"></a>
## B02 source reconstruction and prospective frozen-policy cooperation

2026-10-02 UTC / 2026-10-01 PDT. **Design for one independent selection review;
no new fit, controller/model query, native episode or implementation has begun.**
Root assigned this DM the development of the demonstrated conditional S_L0/S_L1
capability with ordinary control. This is a new complete-use comparison within
the continuing learned-decision question, not another A/R fit, a reopening of
B06 cadence, or a takeover of the peer-owned adaptation/transmission directions.
The namespace remains `uav_decision_generalization`; all A/R findings, endpoints,
adverse cases and measured costs above remain unchanged.

I read the complete temporary Oracle's
[rolling successor advice](../../archive/2026-10-01/RESEARCH-three-dm-rolling-successors.md)
(published `6bcb1a69e7dcff8f83e675baa3d153167ce626bb`), including its proposed
eight-program comparison. The original answer is 10,508 UTF-8 bytes, SHA256
`268559deeeca08a5afc029aaeb58421d3a7224a2fbc022fd473cd12746d71032`, actual turn
`01a0fa64-fe2d-7b40-aefc-fe8234562fce`, Astra/max as verified by Root. It is a
proposal, not independent evidence or an ongoing approval role. Root has assigned
the actual independent selection to `/root/next_study_review`, which independently
reconstructed original B05/B06 sources and raw traces before reading that advice.
This notebook entry supplies the closed comparison for that same review. No
second scientific review, activation pilot or extra fit is requested.

### Question, inherited evidence and the competing ordinary explanation

Can a frozen learned local decision module retain its useful coverage behavior
while a fixed lawful switch to ordinary navigation improves complete service and
continuity on new missions? The contribution sought is conditional usefulness of
the combined control program. It is not a new learning algorithm, an identified
cause of old outages, special value of history, a safety guarantee or a claim
that a teacher must repair its student.

The relevant current background is the shared
[learning/finite-data topic](../../RESEARCH.md#learning-representation-finite-data)
and the N5 sampled-policy/cadence evidence in RESEARCH topics 2 and 4. A/R retained
a finite-data learned capability but did not establish deployment superiority or
pure structure causality. Here the load-bearing positive assets are instead the
two original local S policies. Their legal information, task, reward and costs
are different from A/R; their J values must not be subtracted across hosts.

I read the complete original B05 contract, results and independent disposition,
and B06 source assessment, contract, results and original independent diagnosis:
[B05](../uav_fleet_transmission/NOTES.md#b05-complete-reading),
[B05 independent disposition](../uav_fleet_transmission/NOTES.md#b05-independent-disposition),
[B06](../uav_fleet_transmission/NOTES.md#b06-complete-reading),
[B06 independent disposition](../uav_fleet_transmission/NOTES.md#b06-independent-disposition).
The original adaptation acquisition/recurrence contracts and asset bindings were
also read. The following inherited findings affect this design:

- On B05's 32 paired fresh worlds, S_L1−G J was +.023431 with descriptive interval
  [.012843,.033524], service +1.867981 and p10 service +1.515625. S_L0−G J
  +.013616 remained unresolved, while service, p10 and path had useful tradeoffs.
  Neither lineage's gain establishes uniformly better served-user quality.
- Bstar_L0, the already paid temperature-2 policy, had stronger mean J/service
  than S_L0 and about 1,080 m more travel per UAV. It remains a complete comparator;
  no new calibration is purchased. C, G and the omitted Q controls retain their
  own quality, path and CPU advantages. G is a competent ordinary comparator,
  not a universally best ordinary policy.
- B06's original off-grid count-decline requery did not resolve E−H4 J/service for
  either S lineage, although it substantially reduced travel. The 19-tick team
  outage in S_L0/H4 and E, world 29670024/tape0, preceded E's first extra query at
  t=30. H1's different earlier history is not a same-prefix rescue experiment.
- The original source assessment explicitly declined to prioritize a student-only
  teacher-rescue package as a safety repair. I retain that objection. The proposed
  comparison changes the control source at the original H4 boundaries and applies
  the identical switch to G; it asks a different, complete-use question. It does
  not retroactively turn the failed cadence explanation into evidence for C.
- The current independent review's original-raw reconstruction reports that C's
  zero team-outage episodes can still omit many users: 35/50 never served on
  B05 world29630013 and 38/50 for C/H4 on B06 world29670024. The 19-outage-tick
  S_L0/H4/tape0 episode on the latter world had 17/50 never served. These are
  selected adverse examples, not a panel fairness estimate. They require the
  complete all-user accounting below rather than equating team continuity with
  better service. The final independent original answer will be retained here.

The decisive source correction is that every proposed takeover includes current
q(t)=0. The original local row encodes valid current users in 20 slots, and
`q=min(10, number of valid slots)`. Thus n_current=0 at every takeover. C with
`history=False` clears its current-user set; all 27 predicted candidate scores
and served values are zero. It chooses its existing **deterministic waypoint
sweep fallback**. It still constructs and scores 27 four-tick geometric paths,
but current-user setup and candidate radio-link counts are zero. The student
helper likewise has fallback=true. At this same row/pre-nav, C and the student's
helper compute the same next-nav transition. G's equal-score branch is exactly
.9 probability on C's choice and .1 spread over the other 26 categories. Z(G)
therefore suppresses that random tail at the selected boundaries.

I independently checked these implications in the original `_parse`, `_ingest`,
`_score`, `_sweep_choice`, `analyze`, `_next_nav` and G probability source. The
intervention is consequently deterministic navigation after a whole H4 segment
without legal contacts, not current-user radio re-ranking. It can change physical
motion but can also reduce useful exploration. The ordinary explanation is that
any useful gain comes from selective suppression of stochastic navigation. A
four-tick persistence rule is a fixed conjecture; a current-only rule or constant
mixture could also suffice. No history-specific or S-specific mechanism claim is
licensed by this panel, and no additional threshold/mixture grid is attached.

This finite complete-use experiment currently has better decision value per new
purchase than automatically refitting A. The proposed train-CE-matched A would
require three real fits, up to 1,536 updates/49,152 exposures and up to 49,152
monitoring contexts before its new endpoint and reader. Frozen candidate transfer
remains an interesting different question with unresolved candidate semantics.
Those mechanism/reuse alternatives are deferred, not empirically refuted. The
present comparison develops an existing useful learned asset with zero fitting
and tests a consequential complete service tradeoff against the same added
information/control right. B03 prefix search is assigned to the other DM and is
not duplicated here.

### Frozen host, lawful switch and exact program semantics

Keep the original N5/U50 static-user mission: all transmitters on, non-FDMA,
3 dB service threshold, capacity10 per UAV, original local FP32 rows of width104,
H256, original 27 ordered commands and per-coordinate native clipping. Every
policy decision remains at t=0,4,...,252, held for the next four primitive
transitions. J remains the native mean of .7*served/50 + .3*served-user SINR
quality. There is no added reward, fault, global observation or shorter horizon.

For a parent P in {G,S_L0,S_L1}, define Z(P) independently for each agent:

1. Observe only that agent's original row before each primitive transition and
   maintain its last four q values. At t=0 choose P. At a regular boundary t≥4,
   choose C for the next H4 segment iff q(t−3),q(t−2),q(t−1),q(t) are all zero;
   otherwise choose P. At non-boundaries retain the current command. The window
   is four primitive observations, not four decision boundaries. At t=4 it uses
   observations after transitions 0,1,2,3. It never uses a future transition.
2. Query **only the chosen source** online. An ordinary takeover does not query
   the actor, construct its probabilities or generate its unused uniform. G and
   C use the original full 27-path calculation, including the empty-user branch;
   no new shortcut or rewritten fallback law is introduced.
3. Keep one actual per-agent navigation index, initialized by the original nearest
   waypoint rule. Pass the actual row/pre-nav to the chosen source and apply its
   returned next-nav once. There is no reset on a switch, recurrent hidden state,
   shadow student navigation trajectory or unchosen-source update. Although both
   sources' next-nav agrees at a takeover row, later visited states can differ
   from the unswitched parent's own episode.
4. Each agent/source has its own episode-local original memo cache. The cache key
   is the first103 ordered FP32 row values plus one nav byte, excluding the clock.
   A hit reuses deterministic analysis/logits, never a sampled command. The
   actor is unchanged CPU FP32, one row per miss, eval/inference mode. Sampling
   is original FP64 softmax/categorical code, T1 for S and T2 for Bstar_L0.
5. A stochastic query uses the original stateless uniform addressed by
   `SeedSequence([sampling_root, world, tick, agent])`. Arms on the same world
   and tape share this address. C substitution consumes no stochastic query;
   it cannot shift any later address. Actual draws and reader-only hypothetical
   parent draws are counted separately. No shared RNG stream or action carryover
   is silently substituted.

For the same world/tape, Z(P) and P must have exactly the same first four native
transitions: both query P at t=0 and the first possible takeover is t=4. The
reader will check this invariant. Z cannot protect a zero-service event that
already happened in that first segment, including tick0 in old adverse cases.
Report first-segment and subsequent team-zero ticks separately while retaining
the complete mission; no implicit expectation of eliminating every outage is
introduced. Last-segment and all-user trailing gaps remain in the accounting.

The switch sees neither native connections/user identities nor SINR matrices,
positions of invisible users, evaluator rewards, teammate histories or future
counts. Under this exact N5/all-on/threshold contract, original B06 source/raw
checks establish q equals native own served count; the reader will verify it on
every recorded row again. This equality is not generalized to other hosts.
The online count history is computed only for the three Z programs. Baseline
programs retain their original call paths and costs; all programs' native
counts/user masks can be derived offline for evaluation.

### Complete panel, addresses, predictions and interpretation

The eight programs are C, G, Z(G), S_L0, Z(S_L0), S_L1, Z(S_L1), Bstar_L0.
On each of 32 new worlds, C runs once and each of the seven stochastic programs
runs on two addressed tapes: **480 complete H256 episodes, 122,880 native steps**.
No Bstar_L1 duplicate is needed because its paid temperature is1 and it aliases
S_L1. Q05/Q10 are not added to this finite purchase: G is the fixed same-law
ordinary parent, Z(G) gets exactly the same added count history and switching
right, C supplies deterministic full-time control and Bstar supplies the paid
stronger learned alternative. This selection does not erase Q's previous useful
tradeoffs or prove that no ordinary program can do better.

Freeze prospective main worlds **108310000–108310031**, sampling roots
**108311001,108311002**, actor-constructor seeds **108311011,108311012**,
bootstrap seed **108311091**, master **108311000**. A precise integer-boundary
search of current published research notes, candidate Python/config files and
run configs found no 1083xxxxx identities before this entry. The tempting
107100000 range was rejected because the other DM already uses it. This is a
repository-address check, not a claim about unknown external exposure. Main
episodes use a fixed base arm/tape list in the order above, C tape−1 and other
tapes0,1, rotated left by world index modulo15. Seeds/order never depend on
results. All world observations are fresh for this chosen intervention; old
B05/B06 panels remain exposed development evidence.

The four primary whole-mission J comparisons are Z(S_Li)−S_Li and
Z(S_Li)−Z(G), i=0,1, with both lineages kept separate. The prospective useful
pattern is positive parent and ordinary-matched J increments without hiding
loss of all-user coverage or continuity. Specifically, the intervention predicts
some changed four-tick paths, positive Z(S_i)−S_i J, and reduced mean per-user
longest unserved gap; it also predicts Z(S_i)−Z(G) J>0. These components may fail
separately. No effect-size threshold or interval sign automatically grants
adoption, and no positive trigger/learnability pilot is required.

Retain Z(G)−G, comparisons with C/Bstar_L0, all eight complete levels and all
28 unordered program-pair contrasts as descriptive readings. Also compute,
without any new query, `(Z(S_i)−S_i)−(Z(G)−G)` separately for each lineage. Even
positive primary differences can combine an ordinary switch benefit with an
already-existing S advantage; the interaction is explanatory arithmetic, not a
required significance test or an identified cooperation mechanism.

Average the two tapes within each world before differences and uncertainty.
Use 10,000 common paired-world bootstrap resamples and percentile95 intervals,
with the fixed bootstrap seed. All 32 worlds enter, including inactive or adverse
ones. These are descriptive conditional-world intervals for two fixed learned
assets, not 64 independent worlds, new training replications, confirmation,
equivalence or a reliability guarantee. Show paired values and both tapes for
strong positive/adverse worlds; never select a favorable lineage or metric and
hide the other. No threshold, temperature, new seed, extra panel or rerun is
triggered by an inconclusive or inactive result.

For every episode retain native J and return, mean/p10/min served users, team-zero
ticks and longest team-zero run, coverage and quality reward components, served-
user SINR quality, mean per-UAV path, boundary/low-altitude and zero-displacement
ticks, all query/cache/work counts, measured CPU/wall components and RSS. Quality
averages can change through who is served, not only radio quality for fixed users.
Travel is a reported cost, not a newly invented reward or battery/safety measure.

The **all-50-user service mask** is fixed as
`connections[t, :, user].any()` for all 256 scored post-transition states and all
50 original world user indices. Preserve the full native connection matrix and
this derived mask. Report each user's served ticks/fraction, number/fraction
never served, p10/min user served fraction, and for each user the longest
consecutive zero run inside the mission. Longest runs include leading and
trailing runs; a never-served user has longest gap256. Report the mean/p90/max
of these 50 longest gaps, each user's leading/trailing lengths, and lengths of
closed internal zero runs with explicit left/right mission-boundary censoring
flags. They are observed mission gaps, not estimated premission/postmission
waiting times. The mean of all50 longest gaps is the predeclared continuity
summary; never-served users cannot disappear from the denominator. Initial reset
service is retained for row alignment but is not an extra scored tick. None of
these per-user fields enters a policy or the switch.

### Independent reader and bounded correctness work

The reader independently checks all chosen C source outputs and all chosen
student helper/logit outputs on their actual recorded rows/pre-nav, even on
worker cache hits. At every Z(S) takeover it additionally reconstructs the
unchosen S parent using that same actual row/pre-nav and addressed uniform.
At a Z(G) takeover the independently verified chosen C scores already suffice
to reconstruct the hypothetical G probabilities/choice; do not purchase a
second 27-path calculation. Hypothetical next-nav/cache state is discarded.
This is an action reconstruction on actual histories, not the parent program's
alternative episode, and it supplies no counterfactual reward.

Compare selected and hypothetical parent categories and their entire four-tick
clipped geometric paths from the actual predecision position. A different
category need not be different motion at a boundary. Record actual following-H4
own counts, first regained contact and continued-zero length descriptively;
selection on endogenous histories precludes a causal recovery claim. The reader
checks all257 rows (initial, 255 intermediate and terminal), native own count,
per-user masks, original reward arithmetic, all-on/static-user invariants,
motion/termination, nav transitions, addresses, source selection, costs and
same-world initial identities. It performs **zero native transitions or new
radio-environment queries**; verification from saved native SINR/connections is
distinguished from independent resimulation.

Reserve exactly **16 correctness H256 episodes** on worlds **108310900,108310901**:
two worlds × eight arms × one tape, using audit root **108319001** for stochastic
arms. C runs once per world. Each phase creates one native environment with its
first phase world, then explicitly resets once per episode: two constructor
resets plus496 explicit resets across audit/main. Audit outcomes never select
worlds, assets, gate thresholds or whether the planned opportunity is attractive.
Correctness failures stop and preserve their prefix; audit trigger inactivity is
not a scientific veto. No old-outage-world probe or extra native fixture is added.

Before native audit, bounded synthetic/interface checks may spend at most
**256 full original C source calls and 256 one-row frozen-actor forwards**, counting
reference calls and reviewer reproductions, plus at most10,000 synthetic lawful
count decodes. They have zero native transitions, fits and labels. Their targets
are exact t=4 window alignment, q0 fallback, selected-source-only queries,
nav continuity, cache-hit fresh draws/stateless address invariance, clipping,
all-user censored gaps and incorrect asset/source rejection. Synthetic rows are
not training data or scientific result worlds. This is a total allowance to be
counted, not permission to rerun full suites without accounting. No such call
has yet been made for this study. Numerical/RNG/interface engineering receives
the one applicable engineering review after a concrete bounded implementation;
it does not replace the current independent scientific selection.

### Full prospective bill and sunk-cost context

Let m be main Z(S_L0/S_L1) takeovers and g main Z(G) takeovers. The first boundary
cannot trigger, so m≤40,320 and g≤20,160. For the 16 audit episodes let
m_a≤1,260 and g_a≤630. Set M=m+m_a≤41,580 and Gtake=g+g_a≤20,790. Counts below
are source requests; worker cache misses determine actual full calculations.
The reader deliberately redoes each listed source calculation without relying
on worker cache outputs.

| Scope | Main 480 | Audit 16 | Combined |
|---|---:|---:|---:|
| Native transitions | 122,880 | 4,096 | 126,976 |
| H4 agent decision slots | 153,600 | 5,120 | 158,720 |
| Worker C requests | 51,200+m | 1,920+m_a | 53,120+M |
| Reader C source calculations | 51,200+m | 1,920+m_a | 53,120+M |
| Worker S requests, including Bstar | 102,400−m | 3,200−m_a | 105,600−M |
| Reader S helper/one-row forwards | 102,400 | 3,200 | 105,600 |
| Worker sampled draws | 143,360−m−g | 4,480−m_a−g_a | 147,840−M−Gtake |
| Reader actual+shadow sampling addresses | 143,360 | 4,480 | 147,840 |
| Worker G probability constructions | 40,960−g | 1,280−g_a | 42,240−Gtake |
| Reader G probability constructions | 40,960 | 1,280 | 42,240 |
| Online Z count decodes | 245,760 | 7,680 | 253,440 |
| Online noninitial Z gate checks | 60,480 | 1,890 | 62,370 |
| Reader all257-row count decodes | 616,800 | 20,560 | 637,360 |

Thus worker+reader student source requests are **211,200−M**, at most211,200
before synthetic checks; actual row forwards are no greater because worker
cache hits avoid a forward. C calculations are at most2*(53,120+M), hence at most
**189,400 full C calculations / 5,113,800 candidate trajectories /
20,455,200 modeled ticks and objective reductions**. The extra synthetic ceiling
gives **189,656 C calls / 5,120,712 trajectories / 20,482,848 modeled ticks**, and
at most **211,456 student row forwards**. These are component ceilings, not a
claim that the different extrema are attained together. Cache savings do not
erase source requests, reader work or CPU.

The q0 takeover fact matters to radio accounting. The M extra C requests in each
pass have **zero current-user radio links**, despite their full geometric work.
Using n≤20 and visible peers≤4 for all remaining original C requests, the two
passes have at most229,478,400 candidate and10,624,000 setup link evaluations
(240,102,400 total; Gtake's empty-user cases can only lower this). Adding the256
synthetic C ceiling gives **240,680,960 C radio-link evaluations**. Student
helper setup+extreme links are ≤140 per nonempty query; shadow S takeovers have
zero links. The ceiling is29,568,000 before tests and **29,603,840** including
256 synthetic rows. Native dense power work is separately
275*(126,976+496+2)=**35,055,350 slots**. It is not the C/helper link count.
At most62,370 same-history takeover comparisons each simulate four geometric
steps, **249,480 geometric comparison steps**, with no radio/native rollout.
Native per-user extraction reads496*256*5*50=31,744,000 saved connection entries.
Online+reader slot-presence work is20*(253,440+637,360)=17,816,000 slot tests,
plus at most200,000 synthetic slot tests. These bookkeeping calculations used
source dimensions only, with no effect query.

New fitting, optimizer updates, training contexts/labels, calibration searches,
LLM forwards, model downloads and GPU time are all **zero**. Forecast total
audit/main/reader/test scientific work is **.1–.5 CPU hour**, guided by the paid
B05/B06 timings, with a **1 cumulative CPU-hour stop/re-estimation boundary**
checked between episodes/reader files. This is not an outcome stopping rule;
an incomplete panel remains incomplete, with no silent truncation, altered
algorithm or duplicate retry. Include process entry/import/load, reader and
test CPU separately; record wall time and unmetered support honestly. Expected
support is **8–12 hours**, not zero. Forecast process RSS .6–1 GiB and new
canonical evidence .3–.6 GiB; a fully materialized detached input snapshot is
about1.67 GiB in addition. Use ≤3 GiB new peak disk as the preparation envelope
and measure it on the actual node. These are forecasts, not allocations inferred
from an idle GPU or permission to overrun another accepted study.

The existing assets are paid knowledge: each original S lineage used8,000
supervised updates /4,096,000 presentations, 65,536 label-acquisition native
steps and81,920 expert requests. The complete original B02/B03 pair used2fits,
832episodes/212,992 native steps and205.046 measured worker/reader CPU seconds;
the separate paid Bstar selection used512episodes/131,072 steps and139.828
episode CPU seconds, excluding some setup/reader work. The broader selected
chain through transmission B06 was8fits,2calibrations,2,080,768 native steps
and3,238.693 scoped CPU seconds, excluding separately recorded branches/support.
B05 alone cost106,496 native steps/140.041 CPU seconds; B06 cost286,720/755.536.
Those are inherited costs, not repeated here or a claim that the whole project
costs only that subtotal. A/R's separate6fits/1,736,000 native steps/.814449
measured CPU hour remain in B01 above. Zero new fits does not mean free learning.

### Source identities, external inputs and retention

No frozen peer code or asset is edited. The exact old B05 source is
`54c57af8d2e3860f25a278850055a6aa020e5beb`, result
`fbf908d9571268638f573e747edae0b9fffbedba`; B06 source is
`df149ac620a90931d81fac727fe91a898b9ab760`. The current36 files in the B06
[source map](../../../../runs/uav_fleet_transmission/b06_cadence_a01/config.json)
were checked by SHA256 against that retained config: zero mismatches. This is
source inspection, not a run or a reason to import every old module into the
new implementation. Bind the actual original dependency closure at publication.
The load-bearing modules are:

- original C `experiments/candidates/uav_local_history/b01/controller.py`, SHA256
  `b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2`;
- S/C helper `experiments/candidates/uav_fleet_adaptation/b02/controllers.py`,
  `a2bbbdb877bd988590472a41c336d934a0431b5c560c7e80225cbb630fc3d522`;
- actor/sampling `experiments/candidates/uav_fleet_adaptation/b02/policies.py`,
  `fba732164b07d80fc2f901e6545e6ca281c7db39cd89f9e61cc49bdb40ba4efd`;
- original model `experiments/candidates/uav_fleet_adaptation/b02/model.py`,
  `c9b95b6718262c65591ed106ca81da0abb15b48ef6a8439438618365efc39934`;
- G/Bstar law `experiments/candidates/uav_fleet_transmission/b05_score_sampling/policies.py`,
  `b6a018614df3ee4e32d41d6fd5550850deb8bfe0ec02cf53b6b5efd1291bb986`;
- lawful q definition `experiments/candidates/uav_fleet_transmission/b06_cadence/gate.py`,
  `22fbc4d955c17afb95341fcca9aef8bce334f0f78d1a947c0c2ab3abb46d181c`.

Both actors are original34,715-parameter FP32 114→128→128→27 ReLU networks.
Read-only file presence/size/hash were verified on the canonical node, without
loading either model. Each file is424,487 bytes:

- S_L0: `/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt`,
  file SHA256 `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`,
  state SHA256 `6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c`,
  source `e945483b85c7f8ddfc315c57f36938d6c14201c7`.
- S_L1: `/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/assets/S.pt`,
  file SHA256 `cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d`,
  state SHA256 `c6286dd32097d37b2c2c3039e487a24b756398e3ddffa9dc9e1ec3ef66170699`,
  source `4909c9553300a4a4de6eb79476e818d7b1ceab53`.

B05 canonical raw is on `hmasd-wsl-node` under
`/home/wu/projects/HMASD/runs/uav_fleet_transmission/b05_score_sampling_a01/raw/`:
416NPZ,179,862,927 logical bytes, sorted path/size/SHA inventory digest
`2ad9e833a5a7d4772a99157af46ed999539d90ea7edd99e32340d85425c948cf`.
The compact local [B05 summary](../../../../runs/uav_fleet_transmission/b05_score_sampling_a01/summary.json)
has SHA256 `349a2ca0a1ea10924089ecd1482d3c1025367b1ddcc9dcd32e8e008292c4b70b`.
B06 canonical raw exists locally under
`/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b06_cadence_a01/raw/`:
1,120NPZ,414,546,359 logical bytes, inventory digest
`a58026dd50668a1f0a4c44349aea182c37696acc7ee986024c3a1bfd8cf448db`;
[summary](../../../../runs/uav_fleet_transmission/b06_cadence_a01/summary.json)
SHA256 `36ad2bd66ce59f162144525c79136fec51680108380dfd25ea6996d52fc4d4f8`.
These old traces are evidence, not new execution inputs or fresh test worlds.

A selected implementation would occupy only
`experiments/candidates/uav_decision_generalization/b02_feedback_cooperation/`
and matching tests/runs/temp plus this notebook: fixed contract/asset bindings,
switch/private-state wrapper, complete collector and independent reader. Import
retained kernels rather than copy or revise them; no environment or shared
compute mutation is anticipated. Publish exact code and SHA-bound external
canonical actor locators before any result execution, and use the configured
CPU path on the actual node with fresh admission. Canonical assets need no
duplicate/download. New snapshots use the published full-materialization helper
fix and configured whole-preparation `zsh -lic`; never alter canonical dirty Git,
sparse settings or another accepted snapshot. Keep one canonical complete raw
set, compact source/summary/reader/identity evidence in Git, all adverse/failure
prefixes and both frozen assets. Remove only owned redundant scratch/finished
snapshots after checking consumers and measuring net reclaimed bytes.

### Primary reasoning and historical checks

The three local stores and relevant July/external records were checked before
calling this a contribution. The load-bearing passages were read directly:

- Foundations B01, Albrecht et al., *Multi-Agent Reinforcement Learning:
  Foundations and Modern Approaches*,
  `docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf`, PDF80–83
  (printed51–54): a POSG agent can condition its policy on its lawful observation
  history; that does not make a four-count window a sufficient belief state or
  demonstrate that learned memory is necessary. This supports the information
  contract and its limits.
- InstSci `MARL-0016`, *Models as Agents*,
  `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0016.json`, primary pages2–4,
  with `pdf/MARL-0016.pdf` as source: model-to-return reasoning depends on its
  stated joint-observation/action and reward assumptions. Those assumptions do
  not turn C's local stationary-peer forecast or this count gate into a
  guaranteed closed-loop controller for interacting UAVs.
- My-lib `neurips-2024-f96af360d2a1b1585c3e3a5b82ba4ef7`, *Going Beyond Heuristics
  by Imposing Policy Improvement as a Constraint*, arXiv2507.05328, PDF2–4 at
  `/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/neurips-2024/f96af360d2a1b1585c3e3a5b82ba4ef7/arxiv-2507.05328.pdf`:
  its expected-return improvement constraint motivates comparing complete task
  performance with the heuristic. The constrained trained method and its
  guarantees are not this frozen hand switch; this is the stored arXiv version.
- Mozannar and Sontag (2020), [*Consistent Estimators for Learning to Defer to an
  Expert*](https://proceedings.mlr.press/v119/mozannar20b/mozannar20b.pdf), PDF1–4,
  especially §3 joint system loss and §4 consistency: evaluate the combined
  decision system and expert cost, not expert/student accuracy in isolation.
  Its iid classification setup does not establish a sequential, coupled UAV
  improvement guarantee or make ordinary C a safe expert.
- July [G35 construction](../../designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35.md)
  and the original
  [external audit](../../../external-review/rounds/20260726_continuous_roster_reactive_reduction_g35_design_assertion_audit/21_PRO_OPEN_RAW.md)
  distinguish constructive current-information action from intrinsic history
  necessity. The roster host is different. The
  [July iteration5 disposition](../../../external-review/rounds/20260719_iteration5_postmortem_portfolio/50_DISPOSITION.md)
  also prevents turning useful control into a renewed unsupported skill-channel
  claim. These are evidence and counterarguments, not historical approval gates.

The proposed scope now has a concrete source-level action distinction, complete
ordinary competition and full price. Selection still belongs to the one current
independent review plus Root's cross-question investment resolution. I will
preserve that original recommendation/dissent and my disposition here. There
is no accepted operation to observe and no new result to report at this point.

Prospective clarification before selection, with no additional execution:
own q=0 does not make that UAV radio-inactive. All transmitters stay on; its
new path can alter interference and other agents' service even while its own
current row contains no users. Each agent chooses from the same pretransition
observation matrix before the joint native action is applied. The full native
team and all-user outcomes therefore remain essential; an apparent local
reacquisition can coexist with losses elsewhere. The empty-user C calculation
has no model evidence about those invisible users' prospective service.

The ≤3 GiB new peak-disk forecast assumes at most one fully materialized source
snapshot is retained at a time. Audit and main can share one published input
snapshot while keeping their fixed phase counts; after its worker is terminal
and evidence/consumers are checked, release that snapshot through its supported
lifecycle before preparing a separate reader snapshot. Required unique raw and
actor inputs remain at their canonical locations. If the actual lifecycle needs
overlap, measure and revise that preparation resource estimate rather than
silently treat two 1.67 GiB snapshots as one. This does not change the scientific
query, episode, CPU or fitting envelope.


<a id="b02-selection-review-and-disposition"></a>
### B02 independent selection and resolved disposition

Root read the entire preceding contract and original independent ResearchCritic
answer, then selected this single eight-program purchase. The complete answer
below is mechanically retained without shortening: 7,746 UTF-8 bytes, SHA256
`caf8fa4ab65234f2f1a53b896e417a06c09f0e006f3276117b556a4e10def2da`;
actual turn `01a0fa7d-0e2f-7652-8d5b-e8d6726dfc5f`, Astra/max as verified by
Root. Reviewer `/root/next_study_review` had separate context and original
supporting/adverse sources; its disclosed scope is part of the original answer.

<!-- BEGIN ORIGINAL B02 INDEPENDENT SELECTION REVIEW -->
**建议采纳 `e2e0f252b` 的修订合同，购买这一次 S/C 完整协作用途比较；暂缓 A 早停与 R 菜单迁移。** 选择理由是它能检验一个具体、可撤回的用途判断，并保留强普通竞争者。零新拟合降低了新增成本，但不意味着免费，也不支持新学习能力宣称。[完整合同](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:1221)

我没有继承 Root/DM 的完整会话，但指派已经透露拟议路线与优先级，旧结果段也包含 DM 解读，因此不称盲审。我核对了 B05/B06 的冻结合同、26/36 个源码文件与对应 Git 字节、终态、两份 canonical S 文件哈希及付费温度选择的原始记录；从全部 episode 汇总重建了关键配对均值，并直接检查 **27 条 B05、46 条 B06 完整原始轨迹**，覆盖正例、强反例和中断。检查包括原生连接、服务、奖励、合法 own-count 对齐，及相关几何绑定与移动记录。未重复完整 controller/actor reader、全部历史原始文件或无线物理仿真；没有新增模型、控制器、RNG 或原生查询。

旧证据支持继续使用 S，也限制这次续向的解释：

| 证据 | 本次投资含义 |
|---|---|
| B05 S_L1−G：J **+.023431**，描述区间 **[+.012843,+.033524]**；服务 **+1.868/步**，27/32 世界 J 改善 | 有值得保留、组合的已训练行为 |
| B05 S_L0−G：服务、p10、路径有用，J 区间跨零；两 S 均损失部分 served-user quality | 两条谱系须分别判读，不能只展示 S_L1 |
| B06 H4 下 S_L0/S_L1−G 均值仍为 **+.010681/+.012066** | 加强固定资产的条件用途证据，没有增加训练复制 |
| B06 E 改变了实际移动并显著节省路径，但 E−H4 的 J/服务未确定改善，19 步归零仍存在 | 真实反馈和物理干预都不保证任务收益 |

原始反例尤其重要。B05 世界 `29630013` 的 C 没有团队归零，却有 **35/50 用户从未服务**；B06 世界 `29670024` 的 C/H4 有 **38/50**，而发生19步归零的 S_L0/H4/tape0 有 **17/50**。另一方面，B05 世界 `29630017` 的 S_L1 在两个采样带都明显胜过 G，并减少从未服务人数。团队连续性、个体覆盖和平均服务确实可以分离；这些选取案例不能当作完整面板公平性估计。[B05 汇总](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b05_score_sampling_a01/summary.json)、[B06 汇总](/home/fires/hmasd-wsl/runs/uav_fleet_transmission/b06_cadence_a01/summary.json)

**最重要的源码诊断已进入新合同：每次接管都是无联系人状态下的确定性航点扫描。** Gate 包含当前 `q(t)=0`，故当前合法用户槽为空；C/history=False 的候选服务与分数全零，执行原 waypoint fallback。它没有在这些接管点利用当前用户的无线排序。相同 row/nav 下，学生 helper 的 next-nav 与 C 相同；G 则精确退化为 C 类别概率 .9、其余26类合计 .1。因此最强普通解释是：**选择性地抑制无联系人状态的随机导航，改变探索、访问分布和机间干扰。** 它可能改善恢复，也可能削弱 S 已有的有用探索。[原 C 分支](/home/fires/hmasd-wsl/experiments/candidates/uav_local_history/b01/controller.py:229)

这保留了[旧 teacher-rescue 异议](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_transmission/NOTES.md:3807)：C 没有获得安全专家地位，旧中断也没有被诊断为应由 C 修复。新比较值得购买的变化是保持 H4、改变控制源，并给普通 G 相同历史和切换权。它检验完整用途，不重跑 B06 的额外时刻重查询。同世界、同采样带的父程序与 Z 前四步必然相同，首段已发生的中断无法被 Z 避免。

八个程序足够回答这个有限问题，无需增加混合率、当前计数 gate 或旧反例试跑：

- `Z(S_i)−S_i` 检验增加这条规则的完整净作用。
- `Z(S_i)−Z(G)` 检验相同新增权利下，冻结 S 包是否仍有增量。
- `Z(G)−G` 检验普通反馈控制的收益；C 和 Bstar_L0 保留全时确定性控制及已付强参照。
- 合同加入的 `(Z(S_i)−S_i)−(Z(G)−G)` 有助于区分普通规则收益与原 S 优势的叠加。它无需显著才能保留有用程序，也不能单独识别协作机制。

因此，即使四个主比较都为正，也不证明历史规则独特、学习是必要条件或 S 学会了合作。常量混合或其他普通规则仍可能解释部分收益；在当前用途主张下，不必购买完整因果析因。两条冻结谱系分开、两带先在世界内平均、全部32世界进入读取是合适的；新增世界不增加训练重复。专家协作论文提供联合系统损失的思路，但其 iid 分类结论不能移植为本闭环保证。[Mozannar 与 Sontag，§3–4](https://proceedings.mlr.press/v119/mozannar20b/mozannar20b.pdf)

合同的曝光与服务读取已经充分具体：只查询实际选中源、延续一条真实 nav 状态、定址采样不因 C 接管而移位；reader 的父策略重建仅解释同历史类别和四步裁剪路径，不提供反事实奖励。全50用户 mask、never-served、包含首尾区间的最长未服务段，以及首段和后续团队归零分别保留，能防止用团队均值掩盖个体代价。Gate 后恢复率仍是内生访问状态上的描述。

我独立复算的完整价格与发表合同一致：

| 新购买 | 数量或边界 |
|---|---:|
| 主面板＋工程审计 | 480＋16 个 H256，**126,976 原生步** |
| 新 fit、训练标签、校准、GPU | **全部0** |
| 学生单行前向上界，含 reader/工程 | **211,456** |
| C 候选路径／模型步上界，含工程 | **5,120,712／20,482,848** |
| C／helper 无线链接上界 | **240,680,960／29,603,840** |
| CPU | **.1–.5小时预测**；累计1小时停止重估边界 |
| 支持工作／新增峰值磁盘 | **8–12小时预测／≤3 GiB准备范围** |

这些是分项上界，不假定同时达到；缓存不能抵销 reader 成本。接管处额外 C 调用没有无线链接计算，但仍有几何路径工作。旧 B05/B06 实测完整成本分别为140.041/755.536 CPU秒，只能支持规划预测，不能证明新实现的速度。此前 S 构造、失败续训、校准和 A/R 成本均继续计入各自历史。新实现、实际节点运行时间及资源峰值尚未验证，属于正常工程执行边界。

结果应改变以下具体判断：

- **Z(S) 改善父程序，并保留超过 Z(G) 的 J 增量，同时个体连续性和完整成本可接受：**保留该谱系的具体联合程序；不升级为安全或训练可靠性结论。
- **普通 Z(G) 获益，而 S 的匹配增量未保留：**保留普通反馈能力，结束该 S 融合配方的追加理由；原 S 正面资产继续保留。
- **均值、个体缺口、团队中断或路径互有得失：**保留明确用途取舍，不宣布通用采用优势。
- **稀少接管、物理别名、未定或主动负效应：**完成后结束这条固定规则；不自动加世界、改四步阈值、调温度或训练 gate。技术未完成则保留未完成状态，不计作科学负面。

A 早停仍是检验普通有限优化解释的有区分力方案；暂缓它不会使 R 的结构归因成立。当前没有必须立即维护的结构因果主张，因而先发展已有原生用途的 S 是合理的一次机会成本选择。R 菜单迁移的语义问题也仍未解决。三 DM 配置不构成继续购买任何后继的理由。

**MATERIAL_DISSENT: no — 支持按 `e2e0f252b` 修订合同购买这一次完整0-fit比较；不支持将其解释为安全修复、历史特有机制或新学习增量。**
<!-- END ORIGINAL B02 INDEPENDENT SELECTION REVIEW -->

I read the complete original answer and accept the recommendation and all its
interpretation limits; MATERIAL_DISSENT:no. The ordinary explanation is selective
suppression of empty-contact stochastic navigation, with possible exploration
and interference costs. Original S value is an asset to develop, not a promise
that this switch helps. Keep the four primary comparisons, both lineages,
first-segment invariance, all-user coverage/censored gaps, complete costs and
strong C/G/Bstar alternatives. Inactive, adverse or unresolved results end this
fixed rule without automatic threshold/seed/model expansion. The independent
review and Root's cross-question choice select the declared126,976-step,
zero-fit purchase; no per-stage Root approval is needed. A/R early stopping and
candidate transfer remain deferred alternatives, not refuted or queued runs.
The appended all-on interference and sequential-snapshot clarification changes
no scientific effect/query envelope. Selection is not launch acceptance.

<a id="b02-l0"></a>
### B02 L0: implement the fixed selected cooperation comparison

Deliver one faithful fixed-program comparison and independent saved-trace reader
under `experiments/candidates/uav_decision_generalization/b02_feedback_cooperation/`,
with numerical/RNG/collector/reader tests only under the matching
`tests/experiments/candidates/uav_decision_generalization/b02_feedback_cooperation/`.
Use an explicit module entry supporting bounded synthetic checks, the fixed
16-episode audit plus480-episode main worker, and a no-native full reader.
The preceding prospective contract is the exact science; do not select methods,
seeds, arms, models, query shortcuts or endpoints during implementation.

Reuse original C, helper, frozen actor, categorical law and host by imports;
no frozen/shared/env code edits. The original C hash and actual import closure,
canonical external actor hashes/state identities and paid Bstar temperature
identity must be validated before effects. The worker receives only original
local rows and one actual nav state per agent. Only Z programs maintain the
four-primitive-count window. At t0 query the parent; at t≥4 H4 boundaries use C
iff all four current/past counts are zero; otherwise the parent. Query one source,
update actual nav once, preserve original private memoization and stateless
world/tick/agent sampling. Never query a shadow actor online or move a sample
stream on a C segment. Apply all joint actions after all agent decisions use the
same pretransition observation matrix. Preserve original ordered FP32 commands,
FP64 scores/probabilities/geometry, CPU FP32 one-row actor arithmetic and H4
commitment through H256.

Log enough actual state, observations, source/trigger decisions, nav transitions,
probabilities/logits or C scores, commands/positions, native SINR/connections,
all-user masks and counters to independently reconstruct every chosen query.
Reader C recomputation is one per actual C/G decision; reuse that independently
verified C result for hypothetical parent G on Z(G) takeover. Reader additionally
reconstructs S only at Z(S) takeovers, discards hypothetical state and compares
four-step clipped paths without any native counterfactual rollout. Validate
first-four-transition identity with each parent, all257-row q/native alignment,
all-user gap boundary cases and the complete exact count formula. Report all
predeclared levels, pairs/interactions, paths, tails and disjoint runtime counts.
No read result is complete while promised native traces/reader fields are absent.

The total selected exposure/cost is the preceding table, including the16 full
native audit missions. Synthetic/interface verification may use at most256 full
original C calls,256 one-row frozen-actor forwards and10,000 count decodes across
implementation and reviewer reproductions; instrument/report actual consumption.
Mock/fake wiring checks are separately identified, never reported as native or
frozen-actor validation. They choose no result panel. No result/native launch is
within an Implementer's assignment. Actual node admission follows publication,
focused numerical/RNG engineering review and DM acceptance. Count new process
entry/import/test/worker/reader CPU, enforce the cumulative1CPUh boundary between
complete records, and preserve failure prefixes without automatic rerun.

The Implementer owns only the new code/test paths on shared main, writes no
notebook/index/run records, changes no Git index/branch and spawns no helper.
Other writers are active: preserve their edits. Return the diff, exact checks and
scientific-call consumption, deviations and open risks to the DM. I retain
notebook, shared standing, node/snapshot preparation, actual launch/observation,
collection, independent diagnosis and cleanup responsibilities. No CLAIM is
created for this exploratory fixed-asset use study.

Implementation sequencing clarification, before any scientific call: the worker
collects the16 audit missions, then runs the independent reader core on those
16 saved traces exactly once before main collection. It persists an
`audit_reading.json` bound to its source/config/raw identities and separate
reader counters/CPU. A correctness or budget failure stops; inactivity or an
adverse score does not. The final admitted reader replays the480 main traces
and verifies/adopts the bound audit reading and raw hashes without repeating
those16 source replays. Together they cover all496 episodes with exactly the
preceding total query/native budget. Fresh main environment/policy state and
immutable actor checks prevent audit reading from affecting the deployed main
program. This orders the already paid correctness work, not a new experiment
or scientific selection gate.

Stable implementation CLI is the owned `b02_feedback_cooperation/run.py`, mode
worker or reader, fixed master seed108311000, launch SHA/output, a SHA-bound
actor-input JSON and cumulative-budget JSON; reader additionally receives a
SHA-bound canonical-worker locator. The two original canonical asset records
were extracted with AST literal parsing, without importing a model or querying
a policy, into [B02_ACTOR_INPUT.json](B02_ACTOR_INPUT.json), SHA256
`76aec08610f2ec4844eb43d84ae880e9935c921a64c0535f5ec6d15e655ceaf9`.
The existing paid calibration file is present and has the expected SHA256
`93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50`;
the full input snapshot can verify those original bytes without a new
calibration or a scientific worker's lazy network Git lookup.


<a id="b02-engineering-acceptance"></a>
### B02 engineering acceptance and exact execution inputs — 2026-10-02 UTC

The bounded Implementer returned the10-module worker/reader and focused tests.
I read every production module and the complete test file, independently checked
native observation/termination arithmetic, the gate window, chosen-source-only
queries, one actual navigation state, addressed draws, immutable actors, source
bindings, censored50-user gaps, all comparisons and the cumulative counter table.
The separate registered engineering Reviewer found oneP2 evidence-completeness
gap: Z-parent reset checks alone could accept an internally consistent shifted
SL1/ZSL1 pair or C-only world. This was missing instrumentation, not an observed
native mismatch. The accepted repair validates every raw reset digest and one
common identity per world across all programs/tapes before prefix checks; the
reset identity also binds already saved peer-SINR consistently in collector and
reader. Two pure handcrafted corruption fixtures reject the joint-pair, C-only
and stale peer-SINR cases with zero queries. Reviewer inspected that exact patch
and concluded: **the soleP2 is resolved; no material engineering finding remains**.
I accept the implementation within the selected prospective contract. The actual
16-episode audit is still required; local fake wiring is not frozen-model/native
validation. No new scientific-selection gate or diagnostic purchase was added.

Checks:15 initial focused cases passed across bounded invocations; eight were
independently reproduced, then two new corruption cases passed. The initial
local test-root lookup error was corrected and its isolated rerun passed; it was
not a scientific runtime failure. The actual launcher source guard, frozen
source hashes, calibration identity, AST and whitespace checks passed. Final
source/test inventory fingerprint (compact sorted-key JSON rows of path/SHA256/
bytes/lines) is
`6386472b96b77a8949d9a26204df9697e9fa3a3a43dfc8073101f4368d032de3`.
EntrySHA256 is
`53737a4b43189be430f8535a0088c8445bfe6db22cb7482ccf3dfa2d062ef7be`;
readerSHA256 is
`76a46d751ca0dcbfaa3969be4da8c909ab5ae7d572c9bf6658afa71239f2ddae`.

Measured checks total **40.66CPU seconds /23.58 summed scoped wall seconds**:
Implementer30.71/16.47, original independent review4.92/3.51, repair5.01/3.55,
focused review.02/.05. There were **172 actual synthetic originalC calls,
0 frozen actor forwards,0 native transitions**. Count-decoder budget is charged
conservatively1238;1058 completed decodes and180 precharged early-failure fixture
slots distinguish execution from reservation. Separately, fake wiring used180
fake-actor rows and128 fake-environment steps; these are not scientific exposures.
Source reading, command help, hash extraction, publication and node preparation
remain unmetered support, not zero-cost work. The whole-study256C/256frozen-row/
10000decoder synthetic allowance is unchanged, with84C calls remaining.

[B02_INITIAL_LEDGER.json](B02_INITIAL_LEDGER.json) starts cumulative CPU at40.66s
and carries that conservative synthetic usage; SHA256
`1dd31407e2d7555ee6a5cc8eefe37278d90fc4aebc4f6652e0718f3719e3e4a8`.
The already published original actor locator remains unchanged, and no checkpoint
was copied, downloaded, loaded or forwarded during implementation/review. Worker
will use fresh tag`b02_cooperation_a01`; final reader`b02_read_a01`, with no
production check mode. Both are0-fit CPU-only admitted operations under this
same fixed purchase. The source snapshot repair deployed on the actual node is
verified SHA256`83b22ec927b5dd452290a2a331db5b39d62385d831fb867f0c5dae26a254b11d`.
Canonical control retains lifted pause/exploring/stable lead; its old prose is
not substituted for the current published contract. Available disk exceeds the
single-snapshot3GiB peak forecast. Full snapshot preparation uses configured
`zsh -lic`; no remote sparse/HEAD/dirty-overlay changes. Actual admission and
resource checks are still to occur after exact source publication. Selection
and engineering acceptance are not launch acceptance or a result.


<a id="b02-worker-accepted"></a>
### B02 accepted worker — 2026-10-02 04:02 UTC

Exact inputs were published as`e33a024ee0fc4258ba1ec9ac25fae811218b807f`.
The configured `agent-task` preparation `dmgen-b02-cooperation-a01` finished
exit0 after26s; it is only preparation, not native completion. Actual admitted
worker acceptance is04:02:29.582314UTC on`wsl_4070`, from14,641,598,464B freshly
available physical memory against4GiB floor. Native supervisor/runnerPIDs
1309205/1309206 have matching boot/start identities in the
[original manifest](../../../../runs/uav_decision_generalization/b02_cooperation_a01/launch-manifest.json).
Operation/claim is
`/home/wu/projects/HMASD/.git/hmasd-admission/cafd9b189a91f0d841fad8ae722641df904fb442b7e4d251dc8c50e06e0a31fc.json`;
source snapshot is`.git/hmasd-launch-sources/bdb5d9b61c8e438eb07f1a833ab93dfa`;
canonical output is
`/home/wu/projects/HMASD/runs/uav_decision_generalization/b02_cooperation_a01`.
The manifest,preflight and config were collected and SHA-verified against the
canonical files; configSHA256
`d1df7df988de2e2a16239bb1e189af225cfd2ebcf3f8f6f07497a67081b4f354`.
No canonical checkpoint/raw was copied. Existing remote Git background-gc
warning (`bad tree object dfe82c9813ee82191abb8385cc12a6886fd0a77b`) did not
prevent exact source materialization/admission; no Git repair or sparse/HEAD
change was attempted as part of this study.

The assigning DM armed`tools/hmasd_wait.py` for this exact operation, job
`b02-cooperation-a01`, generation1,45-second deterministic status probes and
600-second checkpoint window. The first drained fact established accepted/
running and consistent native identities, not a result. The native child stays
active and will drain/rearm this same handle through terminal collection. Any
correctness or one-CPU-hour stop preserves its prefix without automatic restart.


<a id="b02-worker-complete-reader-input"></a>
### B02 complete native collection and bound final reader — 2026-10-02 UTC

The original worker exited0 at04:05:18.922UTC with496/496 complete missions:
16 audit plus480 main, exactly126,976 new native transitions,0fits/updates/GPU.
The audit independently reconstructed its16 traces before main and verified
complete fields/commands/counters/identities. Its lack of takeover events is
not an activation screen; the accepted main panel ran unchanged. Main outcomes
have not yet been independently read or interpreted.
[Worker summary](../../../../runs/uav_decision_generalization/b02_cooperation_a01/summary.json)
and[bound audit reading](../../../../runs/uav_decision_generalization/b02_cooperation_a01/audit_reading.json)
retain separate times/counts. Worker CPU167.545230s; with prior engineering,
cumulative208.205232s, plus.394465s measured canonical byte verification.
The slight microsecond self-report difference is preserved as supplied. The
worker component records126.312211s online episodes,2.786749s audit reader,
.280220s constructors,.018943s actor loading and38.147108s import/identity/disk/
serialization/other; peakRSS496,432KiB, native wall164.923s from budget creation.
Self-report terminal tail and unmetered support retain their stated scope.

[Canonical collection witness](../../../../runs/uav_decision_generalization/b02_cooperation_a01/collection.json)
verifies all496 raw files, all16 audit-check files, the11,979,644-byte episodes
manifest and compact records against their original SHA/size bindings. The
unique canonical worker evidence is247,660,544 allocatedB /246,496,164 logicalB.
Only compact metadata was collected; no full raw or actor copy was made.
Observergeneration1 recorded READY at04:05:59UTC. The Codex queue returned
`direct app-server input is not allowed for unloaded spawned sub-agents` despite
the native turn waiting; subsequent same-state drain recovered the valid exit
witness and consistent absent runner/supervisor. Event
`0055f9a1432e138c8a1ace6b` was consumed through generation2 and observation stopped;
no accepted operation was restarted or repeated. Long wait delayed collection,
not the scientific work; delivery failure is distinct from native failure.

After terminal and byte collection, supported snapshot-GC preview/apply with
read-only sudo process inspection confirmed no live consumers and removed exact
snapshot`bdb5d9b61c8e438eb07f1a833ab93dfa`, net allocated
**1,803,276,288B reclaimed**; target now absent, canonical evidence preserved,
no backup/archive/retention copy. [Measured witness](../../../../runs/uav_decision_generalization/b02_cooperation_a01/worker-snapshot-cleanup.json).
This keeps only one full input snapshot present at a time.

The final reader remains the originally selected480 source replays, adopting
rather than repeating16 audit replays. Its input
[B02_WORKER_INPUT.json](B02_WORKER_INPUT.json), SHA256
`65ef728fc646a79f6a87a2af8197913735137f73ed3ef280e9cb64a443a021ce`,
puts the canonical absolute worker root inside the SHA-bound JSON body;
argv points only to this published locator file. Thus the launcher remaps the
locator to the new snapshot but does not reinterpret its external root. The
literal root and both config/summary digests match the just verified canonical
files. No raw copy, native call or model probe is required to establish that
binding. [B02_AFTER_WORKER_LEDGER.json](B02_AFTER_WORKER_LEDGER.json), SHA256
`1746e5136523701a884c21e3fd6aa66d370b5645b1b9606b53c4493076097ed5`,
starts at208.599697 cumulativeCPU seconds, including byte verification, with
unchanged conservative synthetic usage172C/0frozen/1238decodes. Source code and
all frozen actors remain exactly unchanged; reader uses new tag`b02_read_a01`.


<a id="b02-complete-reading"></a>
### B02 complete reading — active navigation switch adds no mean use and harms L1

The complete fixed purchase is technically read. Final reader source
`024d325366ffedd3af6ef8f8a2a08271d981d37f` was admitted04:55:47.254979UTC,
operation`366a9e55215a690b86219c7daffaf360780f6d743624ecce62d270258314b53f`,
snapshot`28aceb68e6e24b3aa942e8eb3b2d666e`, native supervisor/runner1315258/1315259.
It exited0 at04:57:23.673UTC:480/480 independent main source replays VERIFIED,
16 bound audit readings adopted,0 repeated audit replays and0 new native steps.
The reader's first drained state was running; same-handle READY was drained,
consumed through generation2 and observation stopped. Its queue notification
had the same spawned-child delivery limitation; no repeated scientific call.
The original [reading](../../../../runs/uav_decision_generalization/b02_read_a01/reading.json),
SHA256`98b3e648a3d663ad7740f83f7dd8b56857c51e8566855519b816e123759e4236`,
contains all496 evidence identities, all28 unordered paired tables, four primary
comparisons, both interactions, complete costs and same-world/prefix checks.

I additionally read all480 main native traces without importing any policy,
model or environment. Independent arithmetic verified6,240 native metric
reductions, all24,000 per-user served/leading/trailing/longest-gap records and392
paired metric vectors; every one of480 reader-check files was SHA/content checked.
The [DM complete reading](../../../../runs/uav_decision_generalization/b02_read_a01/dm_complete_reading.json)
retains complete levels, every team-zero episode and paired positive/adverse
world/tape examples, with2.987754CPU seconds and0 new queries. Examples were
selected post hoc as descriptive extrema, never as a new test panel.

All means below first average the two tapes within world; C has one deterministic
mission per world. Intervals are the frozen10,000-resample conditional32-world
bootstrap; two inherited fixed actors are not new training replications or
confirmation. Path is mean metres per UAV, not an energy/safety metric. Every
user-gap denominator includes all50 users and both mission-boundary censored
runs; a never-served user has gap256.

| Program | J | Mean served | Service p10 | Never-served users | Mean user longest gap | Path m/UAV |
|---|---:|---:|---:|---:|---:|---:|
| C | 0.356256 | 21.4529 | 20.2969 | 20.8125 | 136.9050 | 2817.523 |
| G | 0.381496 | 23.1844 | 19.4531 | 8.5156 | 110.7906 | 3669.647 |
| ZG | 0.376777 | 22.8442 | 19.4141 | 8.9062 | 113.0300 | 3599.251 |
| SL0 | 0.396703 | 24.4178 | 21.1172 | 9.7188 | 110.5838 | 3037.065 |
| ZSL0 | 0.396299 | 24.4061 | 21.0859 | 9.9844 | 111.3859 | 2998.408 |
| SL1 | 0.403872 | 24.9442 | 21.8203 | 10.2344 | 107.8447 | 3149.010 |
| ZSL1 | 0.396419 | 24.3995 | 21.2266 | 10.3281 | 109.4091 | 3224.403 |
| Bstar0 | 0.400950 | 24.7697 | 20.7812 | 5.4375 | 93.6797 | 4450.787 |

| Primary difference | J mean [95 interval] | Mean-served difference | Mean user longest-gap difference |
|---|---:|---:|---:|
| ZSL0-SL0 | -0.0004045 [-0.0080097, +0.0060650] | -0.011719 | +0.802188 |
| ZSL1-SL1 | -0.0074530 [-0.0173516, -0.0011588] | -0.544617 | +1.564375 |
| ZSL0-ZG | +0.0195218 [+0.0077204, +0.0322549] | +1.561829 | -1.644062 |
| ZSL1-ZG | +0.0196423 [+0.0088041, +0.0317819] | +1.555298 | -3.620937 |

The intermediate prediction succeeded: the student switches made294 and248
source takeovers on20 and22 worlds, changing241 and131 full four-tick physical
paths respectively. They were not dormant. G's same switch made639 takeovers on
18 worlds and changed53 physical paths (55 category changes; two aliased after
clipping). Source reconstruction verifies every takeover has no current legal
users and C takes its original waypoint branch. Next-four-tick contact appeared
after55/294,69/248 and75/639 actual takeovers for ZSL0,ZSL1,ZG. These are selected
on-policy descriptions, not causal rescue probabilities or comparable randomized
subgroups.

The consequential prediction failed. ZSL0−SL0 J is unresolved near zero and its
mean user longest gap increases+.8022ticks. ZSL1−SL1 J and mean served decrease;
service difference−.544617 has interval[−1.220284,−.111266], and longest-gap mean
increases+1.5644ticks (interval crosses zero). Thus changed action paths did not
convert into the proposed mean complete benefit or continuity improvement. ZG−G
also loses J−.0047189[−.0111748,−.0002012], service−.340149 and worsens mean user
gap+2.2394[+.1918,+5.0035]. The ordinary comparison is consequential: selectively
removing its stochastic navigation can also hurt. This does not identify whether
exploration, later occupancy or coupled interference causes any particular loss.

Both Z students still exceed ZG in mean J/service, but the original parents
already exceed G: SL0−G J+.0152073[+.0033496,+.0272557], service+1.233398 and
path−632.582m; SL1−G J+.0223764[+.0129531,+.0331250], service+1.759766 and
path−520.636m. The positive Z−ZG comparison therefore does not establish added
cooperation value. The prewritten interaction is+.0043144[−.0030641,+.0118713]
for L0 and−.0027341[−.0146405,+.0073032] for L1. Those arithmetic differences
remain uncertain and do not identify a student-specific synergy.

Coverage exposes a separate cost of the retained ability. Compared with G,
SL1 leaves+1.71875[+.296875,+3.234375] more users never served despite higher
mean served count. SL0's corresponding+1.203125 interval crosses zero. C leaves
an average20.8125of50 users entirely unserved; all learned programs cover
many more users than C, but neither C's old absence of team zeros nor greater
aggregate student service implies individual continuity. Paid Bstar_L0 remains
a distinct existing alternative: relative to SL0/SL1 its J differences are
+.004247/−.002922, both unresolved, while never-served users fall4.28125/4.796875,
mean user longest gaps fall16.9041/14.1650ticks, and path rises1413.723/1301.777m.
These gap/coverage and path intervals exclude zero. The more diffuse paid
sampling law supplies a useful coverage/travel tradeoff, not blanket superiority.
It adds no new fit or calibration here.

All12 team-zero episodes occur in world108310012, including C and G. Both student
Z programs remove exactly one post-first-segment zero tick in their corresponding
parent missions; they retain the identical first four native transitions. ZG
changes no team-zero count. Two removed late ticks across128 student missions
cannot carry a general reliability claim, and C is not outage-free on this new
panel. In world012/tape0, ZSL0 raises J from.331429 to.341223 and removes one zero
tick, while increasing never-served users9→14. On world012/tape1, ZSL1 removes
one late zero tick but lowers J.362298→.354463 and mean served22.602→21.207.
Service, coverage and team continuity must remain separate.

Large adverse examples are not explained away by the small average. On world
108310000/tape0,122 ZSL0 takeovers accompany J.362072→.198114, mean served
22.3594→9.6602 and mean user longest gap130→196.02; the other tape is identical
to the parent. On world108310016, ZSL1 loses on both tapes: J.442098→.325336 and
.409546→.260485, with mean-served losses7.9141/10.1094, despite no team-zero
transition in any of these four missions. Positive cases remain: world001/tape0
ZSL0 has one takeover, J+.085371 and service+5.804688; world007/tape0 ZSL1
J+.026138 but never-served users4→6. These are complete program outcomes, not
same-history native counterfactuals for individual gate events.

Measured online episode CPU means C.1728s,G.2512s,ZG.2535s,SL0.2539s,ZSL0.2562s,
SL1.2490s,ZSL1.2567s,Bstar0.2928s include resets/native stepping/raw storage;
all query/cache/CPU components remain in the raw episode metadata. The gate is
not a demonstrated deployment speed saving. The complete purchase costs
126,976native steps,78,700 full originalC computations (2,124,900 trajectories /
8,499,600 modeled ticks),170,728 actual frozen-actor rows and0fits/updates/labels/
calibrations/LLM/downloads/GPU. Worker requests105,058S and53,662C; independent
readers add105,600S rows and53,662C recomputations, with private online cache
hits explaining actual computation differences. Separately,172 synthetic C
calls add4,644 trajectories/18,576 modeled ticks; synthetic frozen rows remain0.
All gates, decodes, radio links and mask entries are in the original cost table,
including the conservative1238 synthetic decoder charge versus1058 completed.

CPU ledger increments:40.66s checks +167.545232s worker +.394465s byte verification +
94.694894s reader +2.987754s independent raw reading =
**306.282345s (.0850784CPUh)** under the1CPUh boundary. Original summary fields
retain microsecond component/snapshot timing differences; unmetered support and
terminal self-report tails are not asserted zero. Peak worker/reader RSS is
496432/401744KiB. This is a new0-fit use study, not zero total acquisition cost:
the inherited S chain throughB06 still cost8fits/2calibrations/2,080,768native
steps/3238.693 scoped CPU-s; the separate prior A/R direction study retains its
6fits/1,736,000native steps/.814449CPUh/.03709GPU-reserved-h. These disjoint
histories are not merged into a common task-performance estimand.

Working interpretation before the independent result return: retain the original
S assets' conditional complete service/travel capability and the paid Bstar
coverage alternative; do not adopt this zero-contact C switch or add thresholds,
seeds or a student-only rescue. Physical activation is established, mean package
use and predicted continuity are not; L1's adverse result matters. The fixed
purchase is complete. The broader question of useful learned modules remains
open, with all-user coverage and competent ordinary use laws now stronger
constraints on any constructive successor. A/R optimization control and menu
transfer remain unselected alternatives rather than refutations or queued fits.
The existing independent ResearchCritic is reading original evidence separately;
its full result diagnosis and my disposition will follow here. No new effect is
authorized by this provisional interpretation.


Reader collection additionally verified all480 main-check file identities; its
canonical allocated evidence is4,857,856B at the later completed-directory
measurement. Supported terminal source-GC found no live consumer and removed
exact reader snapshot`28aceb68e6e24b3aa942e8eb3b2d666e`, reclaiming
**1,804,644,352 allocatedB**. Together both sequential snapshots reclaimed
**3,607,920,640B**, with no evidence copy or source archive and both targets gone.
[Reader deletion witness](../../../../runs/uav_decision_generalization/b02_read_a01/reader-snapshot-cleanup.json).
Both observers' consumed/stopped native facts and notification errors are retained
as compact run records. The exact zero-query DM arithmetic source is retained
in the result record alongside its hash; temporary scratch cleanup follows the
independent reading. Original actors, all worker raw, both canonical manifests,
all480main/16audit checks and adverse outcomes remain available.


<a id="b02-independent-result-review"></a>
### B02 original independent result diagnosis — 2026-10-02 UTC

Root reused the existing independent ResearchCritic `/root/next_study_review`
for this actual result, after its source/evidence reconstruction. This is one
substantive result review, not a second experiment or an engineering re-review.
The reviewer explicitly discloses the earlier selection context and visible DM
summary; it is independent diagnosis but not blinded. It reconstructed all480
endpoints/all28 paired vectors, inspected70 complete raw missions and all1181
takeover checks, then compared my published explanation. Its exact scope and
limits are retained below. No new native/model/C queries were purchased.

Root mechanically extracted the complete final answer from
`/mnt/c/Users/fires/.codex/sessions/2026/10/01/rollout-2026-10-01T17-23-45-01a0f9fe-de22-7d73-82c2-129a0cadede6.jsonl`,
line1400, timestamp`2026-10-02T05:18:46.283Z`, actual turn
`01a0fafb-c970-71d3-91df-233235b91b72`, actual runtime`gpt-6-astra/max`.
The original UTF-8 answer is12967bytes, SHA256
`495c7dd77b027fb01eb28d72e672915be45ec8ea8760b7f8edb15d7c280e6967`.
The following bytes are unabridged; the source extraction file was
`/tmp/hmasd-root-b02-cooperation-result-critic-20261001.txt`, with metadata in
`/tmp/hmasd-root-b02-cooperation-result-critic-meta-20261001.json`.

<!-- BEGIN B02 ORIGINAL RESULT CRITIC -->
我的建议是：**结束这条固定零接触接管规则的新增投入，保留原 S0/S1 的服务与路径能力，以及 Bstar0 的个体覆盖用途；当前不买门控修补、追加面板或新 fit。** B02 确实执行了合作，但没有证明合作带来平均新增用途；S1 和普通 G 的接管版本均出现有证据的损失。这不否定冻结学生，也不结束广义学习决策与协作问题。

本轮沿用我此前的 S/C 选题上下文，并可见任务消息中的 DM 摘要，因此不是盲审。我先完成下面的源码、端点及原生轨迹重建，再对照 DM 已发表解释；没有继承其解释作为结论。

**证据边界。** 我核对了冻结合同、worker `e33a024ee0fc4258ba1ec9ac25fae811218b807f`、reader `024d325366ffedd3af6ef8f8a2a08271d981d37f`，逐项比较绑定的32个源码文件，两个版本的相应字节均吻合；直接核对了远端 S0/S1 checkpoint 的 SHA。完整 reader 的 SHA 为指定的 `98b3e648…e4236`，终态 exit0，480主任务 VERIFIED，另采用16个完整审计。

我从原始 episodes 数据独立复算了全部28组成对比较的逐世界向量与均值，未发现差异；独立读取了70个完整主任务 NPZ，包括主要正例、损失极值、全部程序的同世界对照和团队零服务世界。核对内容包括文件身份、共同初始几何、all-on、逐步裁剪运动、局部 own-count、全部50用户服务 mask、原生奖励、路径、从未服务及最长缺口、接管窗口、首四步一致性。没有发现改变比较意义的错配。

我没有重新执行模型、C、环境或 bootstrap，也没有机械重建全部496份 raw 的每个计算。冻结 bootstrap 区间依据已核对的实现和现存结果；全数源重放的工程保证仍来自完整 reader，而非我的第二次实验。入口是[原始 reading](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b02_read_a01/reading.json)及[合同和完整记录](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:2027)。

所有下述区间都是固定两个资产条件下的32世界区间：先平均同世界两条 tape，再作配对统计。两条 tape 不是训练复制，S0/S1 也不是本轮新训练的独立确认实例。

四个主比较重建如下：

| 比较 | J 差及95%区间 | 每步服务人数差 | 平均用户最长缺口差 |
|---|---:|---:|---:|
| Z(S0)−S0 | −0.0004045 [−0.0080097, +0.0060650] | −0.011719 | +0.802188 |
| Z(S1)−S1 | −0.0074530 [−0.0173516, −0.0011588] | −0.544617 | +1.564375 |
| Z(S0)−Z(G) | +0.0195218 [+0.0077204, +0.0322549] | +1.561829 | −1.644062 |
| Z(S1)−Z(G) | +0.0196423 [+0.0088041, +0.0317819] | +1.555298 | −3.620937 |

S0 的合作增量未确定，不是等效证明；S1 的 J 和服务人数区间均为负。更关键的是，**Z(G)−G 本身也损失 J −0.0047189 [−0.0111748, −0.0002012]**，服务减少0.340149，平均用户最长缺口增加2.239375，后者区间也排除零。

所以 Z(S) 超过 Z(G) 不能承担“合作成功”的结论。原学生已经超过 G，而接管还损害了普通对照。预写的交互差：

- `(Z(S0)−S0)−(Z(G)−G)`：+0.0043144 [−0.0030641, +0.0118713]；
- S1 对应差：−0.0027341 [−0.0146405, +0.0073032]。

两者都没有识别学生特有的协作增益。

**值得保留的学习资产很具体。** S0−G 的 J 为 +0.0152073 [+0.0033496, +0.0272557]，每步服务 +1.233398，路径减少632.582米/UAV；S1−G 为 +0.0223764 [+0.0129531, +0.0331250]，服务 +1.759766，路径减少520.636米/UAV。两学生也超过 C。S1 的既有正能力在这批新世界继续出现，S0 本轮也有清楚的条件性优势。

这是固定资产在该 N5、静态用户、H256/H4 使用合同上的原生用途。它不是新学习出来的合作，更不能单凭超过 G，就认定收益来自某种独有的学习表示。普通随机导航、访问分布及采样律仍是强竞争解释。原生质量分量也没有同步提高：S1−G 为 −0.007535，S0−G 为 −0.006867；较高 J 主要伴随更多服务人数。

个体服务进一步改变了用途判断：

| 程序 | 每步服务人数 | 从未服务用户数 | 平均用户最长缺口 | 路径，米/UAV |
|---|---:|---:|---:|---:|
| C | 21.4529 | 20.8125 | 136.9050 | 2817.523 |
| G | 23.1844 | 8.5156 | 110.7906 | 3669.647 |
| S0 | 24.4178 | 9.7188 | 110.5838 | 3037.065 |
| S1 | 24.9442 | 10.2344 | 107.8447 | 3149.010 |
| Bstar0 | 24.7697 | 5.4375 | 93.6797 | 4450.787 |

这些缺口包含全部50用户以及任务首尾的删失段；从未服务用户的最长缺口记为256，没有把他们排除来改善均值。

S1 虽然服务更多，却比 G 平均多 **1.71875 [0.296875, 3.234375]** 个全程未服务用户。因此应保留“聚合服务与路径优势”，不能改写成普遍连续服务优势。

已有 Bstar0 是有实际证据的另一种用途。相对 S0，它平均少4.28125个从未服务用户，最长缺口减少16.9041步，且**全部32个世界的平均用户最长缺口均更短**；代价是路径增加1413.723米/UAV。相对 S1，它少4.796875个从未服务用户、缺口减少14.165步、路径增加1301.777米/UAV。这些覆盖、缺口和路径区间均排除零。Bstar0 与 S0/S1 的 J 差区间跨零，不能称为无损替代，也不能称为普遍更优。它是已付费的覆盖—移动成本取舍，无需再训练才能保留。

**接管是稀疏但真实的主动干预。** Z(S0)、Z(S1)、Z(G) 分别发生294、248、639次接管，改变241、131、53条完整四步裁剪路径。两个学生版本分别在20、22个世界激活；不能把结果归因于未激活。类别改变不必然改变物理路径，这一点已通过完整四步路径而非仅动作编号处理。

源码与 raw 一致表明：触发时当前合法用户集合为空，C 的27个候选服务评分均为零，实际走原有 waypoint 分支。因此这里的 C 接管是**用确定性空用户导航替换父策略的采样行为**，并非发现了更优的当前无线服务动作。G 的原分布为约0.9选择 C，其余动作分摊0.1；同样的接管会取消它的探索性导航。

接管后四步内重新出现本机接触的次数为 S0 55/294、S1 69/248、G 75/639。这些是各自策略诱导状态中的描述，不能当作可比较的救援成功率，更不是同历史 native 反事实。

完整轨迹保留了有用正例，也排除了几个过于方便的统一解释：

- **强烈损失，world108310000/tape0：** Z(S0) 有122次接管，J 从0.362072降至0.198114，服务从22.3594降至9.6602，平均用户最长缺口从130增至196.02；31个用户服务次数下降。另一 tape 与父策略完全相同。不能用接近零的总体均值抹平这类损失。
- **少量干预也能明显有害，world108310016：** Z(S1) 两条 tape 的 J 分别从0.442098降至0.325336、从0.409546降至0.260485。前一条只有**四次接管**，仍少服务7.9141人/步；后一条有140次接管，少服务10.1094人/步。两条均没有团队零服务。这直接反对“损失只是连续接管过久，缩短就能修好”的诊断。
- **普通程序同样失败，world108310006：** Z(G) 两条 tape 都对同一 UAV 接管63次，该 UAV 全任务保持 own-count 为零；原 G 则重新获得接触。两条 J 各损失约0.085。学习器并不是这种不良闭环的必要条件。
- **真实正例，world108310001/tape0：** S0 的一次接管带来 J +0.085371、团队服务 +5.804688，平均最长缺口121.6→88.36。不过被接管 UAV 自身平均服务反而由6.4844降至4.5859，另有13个用户服务减少。局部 own-count 恢复既不是团队收益的充分条件，也不是必要表征。
- **正 J 仍可损失覆盖，world108310007/tape0：** Z(S1) 的 J +0.026138，但从未服务用户由4增至6。

这支持“接管改变导航、后续占位与耦合服务结果”的工作解释；它没有区分探索不足、后续几何与干扰各自的因果贡献。没有必要把未识别的机制包装成一个待修复的已知 bug。

团队零服务的事实也应单独保留。全部这类任务集中在 world108310012，C 本轮也出现了零服务。两个学生 Z 各消除了父轨迹中一个首段之后的零服务 tick，首四步仍完全一致。但是：

- Z(S0)/tape0 的 J 提高并消除一 tick 零服务，同时从未服务用户9→14；
- Z(S1)/tape1 消除一 tick 零服务，同时 J 0.362298→0.354463、服务22.602→21.207。

这保留了局部连续性正例，却不构成安全修复。旧 B05 的 S1−G 正能力、B06 的反例和原“不能优先把仅 S→C 当作安全救援”异议均成立。新旧面板不应相减成修复幅度。

**计算价格已闭合到足以作投资判断。** 本轮480主任务加16审计，共126,976 native steps；零 fit、更新、校准、新训练标签、LLM 调用和 GPU 使用。实际计算包括：

- 170,728个冻结 actor 行前向；
- 78,700次完整原 C 计算，合计2,124,900条候选轨迹、8,499,600个模型运动步；
- 另172次工程 C 调用，增加4,644条轨迹和18,576个模型步；
- 完整源 reader、接管处同历史父命令读取，以及全用户服务重建。

缓存与只查询选中控制源确实减少了在线前向，但不能把“0 fit”称为零计算。q=0 时没有当前用户无线评分，并不免除 C 的几何轨迹工作。

较晚终态 summary 的累计 CPU 为303.294591秒，加入 DM 全量 raw 算术2.987754秒，计量范围合计 **306.282345秒，即0.0850784 CPU小时**。较早 reading 内的302.987546秒不能替代终态数。微秒级分项差保留，不影响判断。该数不包含未计量的人类/代理支持时间和终端自报尾部；8–12小时支持预算仍不能冒充实际测量。

在线任务均值为 C 0.1728秒、G 0.2512秒、S1 0.2490秒、Z(S1) 0.2567秒、Bstar0 0.2928秒，包含环境及存储工作，不能称为纯策略延迟。接管没有证明部署计算节省。历史 S 链取得成本也必须继续保留，不能因本轮冻结复用而归零。两份终态源码 snapshot 的清理记录合计回收3,607,920,640 allocated bytes；必要模型、原生证据和检查记录保留。

我的方向修正是以下三点。

第一，**结束固定 Z 规则的追加投资**。不采用它作为默认合作，不按本批极值修窗口或加锁定时间，不因 S0 区间跨零而自动补 seeds，也不把一次正例变成学生专属救援方案。我们已经获得了原选题所需的完整区分：物理介入存在、局部有益、总体新增用途未建立、普通控制和 S1 都会受损。无需穷尽机制才能停止这一配方。

第二，**将既有能力作为完整程序保留，而不是继续救援它们**。S1 是该合同下聚合服务及路径的有力参考，Bstar0 是更广个体覆盖与更短缺口的参考，G 是不可省略的普通随机导航参照。保留这些用途不意味着在线切换它们；那会是另一项尚未测量的合作程序。实际采用哪个程序必须面对路径、服务量与漏服务之间的取舍，不能事后改 J 或补一个“安全”称谓来制造统一赢家。

第三，**当前不为 B02 分支购买新的 native 或 fit**。下一笔投入不应由“门控失败，所以需要学习门控”自动推出，也不应由本批结束自动转成 A 早停或 R 菜单迁移。这里最小而有用的观察已经完成：父策略、相同合法反馈下的普通程序、完整合作程序和已付费覆盖替代品都有直接对照。再买同样的面板主要会缩小已知差异的不确定性，不足以改变目前的行动选择。

若以后重新提出合作，真正能改变判断的应是一个明确的新用途比较：新程序相对自己的父程序增加完整服务价值，并在全部用户缺口和移动/计算代价下仍值得用，同时接受相同信息权利的普通反馈程序挑战。若只超过普通合作而不超过父程序，继续保留学习资产、拒绝新增合作；若普通反馈同样获益，保留普通用途而不归因于学习特有协同；若新增用途成立，再决定是否值得对新训练实例复制。当前没有这样一个具体、已闭合的新干预，所以没有理由捏造新的 fit 数、seed 数或执行预算。

我与 DM 本次“不采用 Z、不调阈值或扩面板，保留 S 与 Bstar 条件用途”的实质处置一致。最需要防止的解释偏移，是把 Z(S)>Z(G) 写成合作成功，或者把损失解释成已识别的“接管太多”并据此自动排队修补；两者都被直接对照和完整轨迹限制。

**MATERIAL_DISSENT: no。** 同意结束该固定配方的新增投入，并保留上述正能力、个体代价及长期问题；不支持由本结果自动批准任何门控修补、额外面板或新训练。
<!-- END B02 ORIGINAL RESULT CRITIC -->

<a id="b02-independent-disposition"></a>
### B02 DM disposition and standing after independent diagnosis

I have read the whole original answer and accept the substantive disposition.
Root independently read it and reported`MATERIAL_DISSENT:no`. The fixed Z
purchase ends here: no default switch, extra worlds/tapes, gate-duration repair,
learned gate or new fit follows from this result. S_L0/S_L1 retain conditional
aggregate service and shorter-path value against G; Bstar_L0 retains wider
individual reach and shorter gaps at a materially larger travel cost. Neither
is a universal default, safety result, improved quality component or a new
training replication. Broader learned decision assistance remains an open
question; ending this use law does not reject the frozen capabilities.

The review strengthens two constraints on my working explanation. In the
already-read compact world108310016/tape0, only four ZSL1 takeovers accompany
J.442098→.325336 and mean served27.4453→19.5313. The other tape's140 takeovers
are not a common explanation for both losses. “Too much takeover” therefore
cannot be treated as the identified defect that licenses a shorter-window
repair. The critic's independently reconstructed world108310001/tape0 further
shows that the gated UAV's own mean service falls6.4844→4.5859 despite the
team's J+.085371 and served+5.804688. A complete team gain need not follow that
UAV's own average service; this limits a local-restoration narrative without
identifying exploration, position or interference as the causal mediator.
The positive and adverse same-user cases, including users losing service in
positive-J missions, remain evidence rather than exclusions.

The mechanism prediction reached physical action changes, but its proposed
native consequence failed. The complete parent contrasts determine that
judgment; positive Z(S)−Z(G) cannot substitute for them when G's own switch
also loses. Both interaction intervals cross zero. I retain task opportunity
and the original learned program's package value, while weakening this
particular local-feedback collaboration hypothesis. Representation necessity,
training-distribution generality and the causes of individual failures remain
unresolved; none requires more queries before ending the fixed recipe.

The next investment is not automatically another gate or the previously
unselected A early-stop/menu-transfer ideas. A useful continuation must state a
new consequential complete-service comparison, the additional information and
experience it needs, an ordinary program with those same rights, and its full
price. It should exploit the demonstrated aggregate-service or coverage
capability rather than imply the frozen assets need rescue. Root's temporary
Oracle is currently comparing such next questions; this is cross-question
allocation, not a standing approval dependence or a selected new run. I have
supplied existing source and cost facts. There is no active worker, observer,
unread result/advice for B02, or unpriced continuation.

<a id="b02-final-cleanup"></a>
### B02 final measured cleanup and retained evidence

The two completed source snapshots were already removed after their exact
supported GC checks, reclaiming3,607,920,640allocated bytes. Final cleanup checked
both finished preparation tasks, their exit0 records, absent preparation/native
PIDs, no referencing process and the stopped/consumed generation2 observers.
It deleted these exact additional targets:

- Remote `/home/wu/.agent-tasks/dmgen-b02-cooperation-a01`:32,768allocated bytes.
- Remote `/home/wu/.agent-tasks/dmgen-b02-read-a01`:32,768allocated bytes.
- Local `temp/directions/uav_decision_generalization/`:90,112allocated bytes.
- Owned code caches under `experiments/candidates/uav_decision_generalization/`
  and its `b02_feedback_cooperation/`:12,288+135,168allocated bytes.
- Owned test cache under `tests/experiments/candidates/uav_decision_generalization/b02_feedback_cooperation/`:
  61,440allocated bytes.

All six targets are absent. The final deletion reclaimed364,544allocated bytes;
combined B02 target reclamation is **3,608,285,184allocated bytes**, with no
archive, backup, duplicate bulk or new evidence copy. This is measured allocation
of the deleted targets, not a claim about filesystem capacity or Git object-store
shrinking. [Exact final cleanup witness](../../../../runs/uav_decision_generalization/b02_read_a01/final-cleanup.json)
records live-consumer checks and before/after values. No tool blocker or leftover
disposable target remains.

One necessary canonical worker evidence set remains at
`wsl_4070:/home/wu/projects/HMASD/runs/uav_decision_generalization/b02_cooperation_a01`
(496unique raw missions,16audit checks,247,660,544allocated bytes), and the
reader at the sibling`b02_read_a01` (480main checks,4,857,856allocated bytes).
Their manifest/exit/summary identities and all retained positives/adverses
remain published. The two historical actor files stay in their original
canonical locations, unchanged and uncopied. Frozen worker/reader code and
focused tests remain useful for the retained complete-use evidence and its
independent reconstruction; no unused alternate implementation remains.
The compact run records and notebook retain original observer failures and
all exact source identities after disposable launch support is gone.

The final scientific purchase remains126976native steps,0fits/updates/labels/
calibrations/LLM/GPU,170728actual frozen actor rows and78700full C computations
plus172synthetic C calls. The already-published measured computation is
306.282345CPU-s; final documentation/inspection/cleanup support is not included
in that scope and is not asserted zero. The two source-snapshot witnesses and
this final cleanup do not change any native or learner result. B02 is complete,
independently diagnosed, published and cleaned; the scientific question and its
retained capabilities continue under the same DM ownership.

### Source-only clarification supplied for possible next investment

The original S_L0/L1 acquisition is supervised imitation, not an existing
policy-gradient learner with GAE or a value head. Frozen source
`experiments/candidates/uav_fleet_adaptation/b02/model.py:63–139` takes114-feature
rows and integer27-command labels, uses cross-entropy and one continuing Adam;
`study.py:107–180` collects each whole phase before fitting, with C roll-in first
and the current student's roll-in for the two aggregate phases. Saved BC/D1/S
endpoints are copied/frozen; the original fit starts from a new random student,
not from the frozen S now used by B02. Thus a terminal64-tick service return
cannot be passed into the existing trainer unchanged. A new learning method and
its costs would need a separate complete contract; no such fit is selected here.

Each original acquisition fit uses65536training native steps,81920C labels,
8000updates and4096000sample presentations. The saved L0/L1 summaries at
`runs/uav_fleet_adaptation/b02_inheritance_a01/summary.json` and
`b03_inheritance_recurrence_a01/summary.json` respectively report complete worker
CPU101.990389962/92.334372074seconds, including their different evaluation panels
(49152/32768extra native steps). Recorded training-episode CPU plus optimizer
phase CPU is60.927847905/60.715340245seconds, excluding shared imports and
summary overhead; it is not a substitute for complete acquisition/reader/check
cost. The historical source and outcome identities remain owned by that direction.

Registered-service F is currently evaluator-only: its
`b01/metrics.py:26–55` reduces native256×50contacts to four64-tick distinct-user
completion windows, F∈[0,200]. Its scheduler separately has a400byte ordered
integer-metre map via`uav_radio_activation/b01/protocol.py:28–44`, decoded
position reports and known executed commands/masks. Registered-service
`b01/history.py:49–107` reconstructs predicted history from those inputs with the
model; no true per-user ACK is available. The native connections obtained by
`b01/study.py:119–173` remain on the evaluator side. Current S's104-local-row
plus10helper-feature interface has neither registered map nor true completion
bits. A training-only scalar F could preserve actor information rights if
explicitly declared; giving the actor a map, completion bits or true ACK adds
an information/communication interface and needs equally supplied ordinary
comparators. These are feasibility facts for Root's allocation, not a new
architecture selection or an invitation to access evaluator truth online.


<a id="joint-window-prospective-contract"></a>
## 2026-10-02 UTC — joint sustained service windows: source-bound prospective draft

**State: one completed, zero-effect contract-preparation task for Root's next
cross-question selection. This is not an accepted fit, native panel, calibration,
implementation or new direction.** The existing B01/B02 evidence and dispositions
above remain unchanged. Root assigned this bounded preparation after B02 closure;
Claude's direction and pause remain peer-owned and read-only. The proposal would
answer a new direct-learning question on a registered joint-service contract,
not repair Z, relabel the old A/R results, or fine-tune the frozen S actors.
No environment, model, controller, training, RF or toy query was made while
preparing this entry. Work was source reading, existing-summary reading, integer
and geometric arithmetic, literature retrieval, and documentation. Its support
work is not asserted to have zero cost.

The current programme at published `67df2f6066acfa78de63d753dac2709ebe704338`,
[RESEARCH topics 1–2](../../RESEARCH.md#研究背景与共享认识), distinguishes complete
service from local links, legal information from state, and retained learned
capabilities from failed adoption rules. Those distinctions determine the task
endpoint, the explicit information addition, the ordinary comparison and the
interpretation below. The [B02 disposition](#b02-independent-disposition) remains
a reason to read all users and travel: reducing one symptom or improving one
team average does not establish continuity for every user. Its conditional S
capabilities are retained; these supervised 27-command actors are not the native
PPO learner proposed here. The inherited S chain cost 8 fits, 2 calibrations,
2,080,768 native steps and 3238.693 scoped CPU-s; our separate A/R study cost
6 fits, 1,736,000 native steps, .814449 CPUh and .03709 GPU-reserved-h; B02 cost
126,976 native steps and 306.282345 scoped CPU-s. Those disjoint purchases are
not reset, transferred into the new native budget, or re-bought as preliminary
screens.

### Evidence read and the change in question

I read the complete imported Claude proposal, branch report, prompt, toy README,
RESULTS, both saved JSON result sets and the complete toy source. Imported source
is `420381b1a`; the relevant paths and current SHA256 identities are:

| Source under `docs/Claude_docs/` | SHA256 |
| --- | --- |
| `environment_design/SPARSE_WINDOW_RELAY_SCENARIO_DESIGN_20261002.md` | `0aa1810546b466470b55572fb7eb8311af79791305035c6c2e753a75afd6eeec` |
| `deliverables/BRANCH_REPORT_claude_inspiring_ritchie_2kj46g_20261002.md` | `52bad967292425341a87c019e9bddc3ab720d2ebc7e8d74706be3074bd0fdfdb` |
| `deliverables/CODEX_PROMPT_SPARSE_WINDOW_RELAY_20261002.md` | `7f07264ea3273e45cc32df9a5998470ec769c565ad14eeec601f6f0d226f1764` |
| `toy_studies/sparse_window_relay/swr_toy.py` | `893c7837ecbda7a0e0277722aed2000f71ace6c797a2e301a6b4eadd8a2b4800` |

The toy is evidence for its own small target-selection process. It applies one
common external-plus-intrinsic return to Z, z and target REINFORCE updates. Its
intrinsic term is paid once per ten primitive steps; native H uses a different
high/low reward flow and per-tick low reward. Its five-window sequence revisits
site zero; a policy learning that site need not learn all four scheduled sites.
The saved .125 statistic is the fraction of episodes with any hit; .131/5=.0262
is the corresponding mean completed-window fraction. Neither quantity calibrates
native random difficulty. No factor-four reward change, four-arm expansion,
random-hit acceptance range or toy rerun follows from these data.

The complete temporary Oracle answer, including the other DM's resource question,
is preserved unabridged at [the end of this entry](#joint-window-oracle-original).
Root also published it with its own disposition at
[the durable archive](../../archive/2026-10-01/RESEARCH-joint-window-and-resource-allocation-successors.md).
Oracle was the proposed-study adviser, not an independent reviewer. I accept its
central correction: directly compare native H, H without discriminator reward,
and native per-tick SET on one well-defined joint sparse task. I do not accept
7.6 CPUh as the full cost, the toy as an exposure guarantee, or all-zero native
performance as a prior empirical fact. My concrete additions below close the
registration packet, primitive-time score, ordinary controller, source adapter,
world identities, endpoint mode and accounting. They are part of this one draft
for the same independent selection, not a separately selected study.

Historical and primary-source reading changes the interpretation, too:

- [R35/R36 source review](../../decisions/R35_R36_SPARSE_ACCESS_FAILURE_REVIEW_20260715.md)
  already tested sparse access. A count bonus greatly expanded visitation without
  achieving access, and actor-facing task identity/clock differed from critic
  information. Thus sparse reward has been tried; this task explicitly supplies
  the registered task and full clock, without claiming that information alone
  makes it learnable. Old failures constrain extrapolation, not this task's score.
- The September external review's
  [HMASD discussion](../../../Claude_docs/reviews/FOUNDATIONS_AND_METHODOLOGY_CRITICAL_REVIEW_20260914.md)
  distinguishes sparse exploration from dense coverage and preserves the real
  Alice-and-Bob positive anchor. Its then-current negative inventory is historical,
  not a licence to erase subsequent learned capabilities. Its recommended sequence
  and seed quota are advice, not present instructions.
- I read the load-bearing primary passage in **MARL-0553**, Yang et al.,
  *Hierarchical Multi-Agent Skill Discovery*, PDF pp. 5–6, §3.2 and Overall Training:
  `/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0553.pdf`, structured source
  `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0553.json`.
  The coordinator selects joint skills from global state and joint observations;
  the low policy is conditioned on local observation and assigned skill; external
  and mutual-information rewards enter different training levels. That motivates
  a direct task comparison, not a theorem that skills will solve this host.
- All three local library indexes were consulted before any novelty inference.
  `docs/new-libs/corpus/papers/P17/metadata.json` locates MAVEN, but its indexed PDF
  and full-text chunk paths were not materialized here; its metadata is not used
  as primary support. My-lib's `.local-llm-index/titles.tsv` returned sparse
  achievement/temporal-skill candidates; title hits are retrieval leads, not
  evidence or a novelty verdict. This study claims neither new hierarchy nor a
  first sparse-reward experiment. MARL-0553's actual primary passage supplies the
  modest mechanism bridge needed here.

**Question and expected discrimination.** Can a native hierarchical learner turn
its finite interaction budget into complete, newly sampled joint sustained-service
windows, and does the original discriminator-reward package help relative to the
same hierarchy without that reward and a competent flat learner? The proposed
contribution is empirical learning capability and its boundary on a concrete
coupled task, not a new architecture or a claim that learning beats all planning.
Distinct relay positions and persistence might make skill diversity useful;
that is a conjecture. The sharper favorable prediction is H-final exceeding
H-noD-final in completed windows, accompanied by learning beyond the shared
initial policy. H may instead lose because its intrinsic terms dominate rare
external events, optimize distinguishability unrelated to useful relays, or make
optimization harder. SET may learn equally well or better. The ordinary chain
may solve most of the task cheaply. These are consequential alternatives rather
than excuses requiring another fit before reporting the purchase.

The parent question is not restricted to tiny residual gains over an ordinary
policy, but practical adoption and learning evidence remain separate. H versus
H-noD tests the effect of this reward intervention and all downstream changes in
experience. H versus SET is a complete architecture/training/information-routing
package comparison. Neither isolates exploration, permutation symmetry, a unique
need for latent skills, or superiority to every generic exploration bonus.

### One frozen proposed world law; structural feasibility without a query gate

Use the original coupled-host physics: N=6, U=50, square 5000 m, heights 50–150 m,
30 m/s, one-second primitive steps, H=500, free-space radio, 2 GHz, transmit powers
23 dBm, noise −80 dBm, threshold 3 dB, FDMA, no shadowing, 10 associated users per
UAV, one BS at (2500,2500,30), and original routing/association. All transmitters
stay on. `max_hops=3` is retained with its actual BFS semantics (up to three
intermediate UAV relays before BS); it is not described as three total edges.
No energy, collision or packet-loss model is added or silently claimed.

World seed `w` deterministically defines the following, with no rejection or
score-dependent replacement:

1. Keep the native initial UAV law and exact draw order: `RandomState(w)`, for
   UAV IDs 0…5 draw x,y uniformly from [0,5000] and z from [50,150]. The native
   reset draws these before users. The new user generator uses separate streams
   and never consumes or advances this UAV stream.
2. Four nominal far centers are (500,500), (4500,500), (4500,4500), (500,4500).
   Add independent per-axis Uniform[−50,50] jitter, in that order, using
   `PCG64(SeedSequence([w,1]))`. The near center is exactly the BS xy location.
3. Each center has ten users. Use `PCG64(SeedSequence([w,2]))`; in row order draw
   a pair (u,v) uniformly on [0,1)^2 and place a user at radius `100*sqrt(u)` and
   angle `2*pi*v`. Round xy with `np.rint` to integer metres. Rows 0…9 are near;
   rows 10…19,20…29,30…39,40…49 are far clusters 0…3. The host uses exactly these
   decoded integer coordinates as float64, so the registry introduces no hidden
   quantization discrepancy. No clipping is needed under these bounds.
4. `PCG64(SeedSequence([w,3])).permutation(4)` supplies the four far-cluster window
   order. Each cluster appears exactly once. Neither latent jittered centers nor
   future service outcomes enter a policy packet.

Training IDs are `109210000 + 16*e + lane`, e=0…44, lane=0…15: 720 distinct
worlds, identical across all three fits. Fresh endpoint IDs are
`109220000…109220031`. The engineering mission world is `109229000`, separate
from both. No geometry has been generated or evaluated in this preparation.
A literal-integer search of current experiments/tests/research/runs found no use
of these prefixes; incidental float/hash substrings were excluded. This is an
accessible-source identity check, not a claim to have searched unknown external
storage. During implementation, the manifest will bind exact generator/source
bytes and generated coordinates, with duplicate IDs rejected rather than silently
replaced. There is no candidate-pool search or outcome-based seed selection.

The source uses speed-of-light constant 3e8. Its free-space SNR threshold gives
single-link radius `R=(3e8/(4*pi*2e9))*10^5 ≈1193.66 m`. With rounding displacement
at most sqrt(.5) m, a far user's horizontal BS distance is at least
`sqrt(1950^2+1950^2)−100−sqrt(.5) ≈2657.01 m > 2R`.
By the triangle inequality, one UAV cannot both directly reach BS and serve that
far user. This proves a structural need for at least a relay plus a service UAV;
it says nothing about whether a learner discovers or holds such a configuration.

A stationary two-UAV ray chain is geometrically available. Let c be a jittered
center, m its ten registered users' mean, and set UAV xy at BS+(m−BS)/3 and
BS+2(m−BS)/3, both at z=100. Let `r=100+sqrt(.5)` and
`Dmax=sqrt(2050^2+2050^2)`. The horizontal first/second relay separation is at most
`(Dmax+r)/3 <1000 m`; the first link adds only 70 m vertically. A user-to-outer-UAV
horizontal distance is bounded by `Dmax/3+5*r/3`, and adding its 100 m altitude
makes it <1138.63 m, below R. This uses the common center and mean rather than an
incorrect independent worst-case bound. It establishes legal link geometry,
not a globally optimal schedule, simultaneous user-assignment guarantee or a
complete-mission score. Native association/capacity and travel are still executed.
Uniform initial UAV positions can make the first deadline infeasible. Such
worlds remain in every panel; no ordinary score is used to retain or discard them.
All this feasibility work is analytic: **0 additional native/RF/optimization
queries**. Actual travel and completion opportunity are measured inside the fixed
ordinary missions, not a prior admission experiment.

### Registered information, exact proposed tensors and action rights

Every complete programme receives the same immutable reset packet: 50 ordered
xy pairs as little-endian int32 (400 bytes), followed by four uint8 cluster IDs
(4 bytes), **404 additional payload bytes per episode**. Cluster membership is
fixed by public row block. A broadcast is 404 bytes; six logical copies are
2424 bytes. These are the additional task registration bytes, not the full
HMASD uplink/downlink or simulated radio traffic. Existing state/joint-observation
snapshots and their ten-tick frequency remain. The host does not simulate the
packet's airtime, transmission energy, losses or acknowledgements, so none is
claimed free in a real communications system.

At decision state time t=0…499 the policy knows its original clock t/500 and the
full public schedule. At each local row append: 100 registered xy/5000 values;
a 4×4 one-hot schedule flattened in window-major order (16 values); the active
cluster one-hot (4); and `(125−(t mod125))/125` (1). These **121 deterministic
features** give `obs_dim=90+121=211`. At terminal t=500, active and remaining
fields are zero. Current-cluster and remaining-time features are computations
from the schedule and clock, not hidden progress or extra reports.

The original 133-state already includes all 50 user xy values and t/500. Append
only schedule16+active4+remaining1, giving `state_dim=154`; do not duplicate its
map. The same task information therefore reaches all existing state consumers.
The count-stable StateSetEncoder keeps its shared UAV encoder and widths; its
pooled input grows from 230 to 251 by concatenating the 21 task features after
its existing pooled-UAV/user/time entries. Its hidden/output layers, nonlinearities
and parameter ownership follow the original factory. The H actor takes its
211-row and its original skill conditioning/GRU. The SET actor retains the exact
original decomposition into current local row, held global state, held joint
rows and ego ID: input width `211+154+6*211+6=1637`. Its 128-wide shared row encoder
and 256-wide state feature/fusion are retained; fusion input is
`2*128+1+2*211+256=935`. Configuration-derived core buffers use these widths.
The direction-owned shape adapter must ensure every state encoder includes the
21 added task features; silently truncating them would change the comparison.

H's coordinator receives current state154 plus six current local211 rows at
reset and t=10,20,…490. H's low actor receives the current own211 row plus its
assigned z; its critic receives current state and the existing skill information.
SET's low actor directly consumes the held state154 and six211 rows from the
same ten-tick refresh, current own211 row and ego identity; its critic uses
current state. Those complete-program information rights are comparable, but
their internal routes are different and stay different. At a window boundary
such as t=125, the current local task clock changes immediately while the held
central snapshot/assigned H skills remain from t=120 until t=130. This timing is
intentional; no off-grid coordinator query or special window-boundary action is
introduced into H or SET.

Original local entries are retained: own position; up to 20 legal user rows;
up to six legal UAV rows; time; own direct-BS link bit; and the original hop field.
Thus actors are **not** described as having no routing information. The complete
`routing_paths` dictionary, true user ACK masks, paid-window bits and true
consecutive-success counters remain evaluator/training-reward material, never
new actor inputs. No previous reward or hidden counter is added to a GRU input.
The scalar training reward is legal outcome feedback for learning. Both ordinary
programmes receive the same packet, current local rows and held central snapshots;
they have no privileged simulator look-ahead or true progress. Unused legal inputs
are still permitted.

All programmes output six continuous xyz velocity commands each primitive tick.
The original host clips each command to the unit three-ball, multiplies by 30 m
and applies height/box limits. H and SET retain the original unbounded Gaussian
head, followed by this host clip; this is not the bounded-head or macro-target
SET-T recipe. Raw sampled actions/log probabilities remain the learner's recorded
actions; executed clipped commands and clipping rates are reported separately.

### One post-routing window ledger and the real reward/update chain

Index native actions by n=0…499; action n leads to post-state n+1. Window j uses
n=125j…125j+124. For that transition, after native association and routing are
complete, define `y_u(n)=1` iff some UAV i has native `connections[i,u]=1` and
`i in routing_paths`. For the ten users in schedule[j], q(n)=sum y. A private
counter increments when q≥8 and otherwise resets to zero. It resets at every
window boundary. The first counter value 20 in that window emits team reward
R(n)=1, otherwise R(n)=0, and no second payment is possible in that window.
It need not be the same eight users on every tick. This is four 125-step windows,
20 consecutive *primitive* transitions, at most four payments per episode.
No dense or per-user shaping term enters learning (`w_dense=0`).

The new ledger advances only once in a direction-owned wrapper after the full
native `step` returns. It uses the final post-routing connections/routes, updates
its own per-world state and replaces the returned per-agent reward by R(n)/6.
`_compute_reward` remains a pure diagnostic computation with no window mutation.
This is necessary because `uav_env.step` first invokes it with updated user links
but old routes, then `scenario2.step` refreshes UAV links/routes and invokes it
again. The current CoupledRelayHost itself calls the parent diagnostic within
each invocation. Therefore a naive override advancing a counter in that method
would double-count time and sometimes count obsolete routing. Reset clears the
ledger but cannot pay; repeated diagnostic calls cannot alter it. The constructor's
virtual-reset path must initialize window fields before parent use. These are
prospective correctness requirements, not new scientific probes.

The returned training scalar is R/6, preserving the real adapter's reward units.
The complete episode score W=sum R is reported on [0,4], not confused with a
per-agent return. Also retain normalized window fraction W/4. The original
post-routing dense contract `J_dense=mean .5*(C_bh+frontend_capacity_with_path/D)`
is recorded as a secondary native consequence, never added to the reward.
Its throughput component is capacity of a front-end attached to a routed UAV;
it is not an end-to-end bottlenecked traffic rate.

The actual learner is `coupled_host_joint_skills_stage1/runner.py::run_fit`,
`configuration.py` and `models.py`, with shared `hmasd/agent.py`, `networks.py`
and `utils.py`; it is not `macro_runner.py` or the toy. Source at the preparation
boundary has host SHA256 `92b75c0317009380108bd45429892e49ca857b901ae1adbcd5bfe483d89ef469`,
runner `4020dbef217b751fb4efea14b915b4981f1fbc0fdc3a988400f9520b833a87a9`,
configuration `68ea26d61eed348427d083ba9a2701fbd077d87838314b43715488b21e255d8c`,
models `9349b840ddb9a2224a1524a4828db1b59f38742ff76ddcaf09e46d2fbd4b50a6`.
Final executable input identities will be published before any selected launch;
this source examination does not alter Claude's files.

H retains the real d2 route with both interruption costs +infinity, individual
and team cap10, age features off, HA-CTSE off, all six skills resampled together,
6 team and 6 individual labels, and no outcome-triggered skill interruption.
The low-level transition gets external R/6 plus the existing discriminator reward
terms, with lambda_e=1, lambda_D=.05 and lambda_d=.02. Discriminators learn skill
labels from the same actual interaction. The coordinator receives **external
reward only**. More precisely, `_d2_store_transition` (`agent.py:2365–2507`)
stores the segment sum `sum_u gamma^u*(R/6)`; D2 high-level GAE uses
`gamma^elapsed` across those segments (`utils.py:1444–1508`). Thus a shorthand
“accumulates external reward” must not be interpreted as an undiscounted sum.
The high-level path does not multiply that scalar by the low-level lambda_e.
This explicitly corrects the earlier source-discussion shorthand. The toy's
common-return updates and once-per-k bonus cannot establish the scale of this
native per-tick mixture.

H-noD changes exactly `disable_discriminator_rewards=True`, keeping
`disable_discriminator_training=False` and every other H setting. It still
collects the same types of endogenous skill labels and trains both classifiers;
it merely omits their contribution to low-level reward. In the batch path this
skips the reward-logit forwards; it does not remove discriminator parameters,
optimizers, high-level learning or alter action inference. H−H-noD therefore
carries the cost of the same classifier-training machinery and isolates this
reward intervention more narrowly than deleting the modules. It does not say
whether another intrinsic bonus would be better.

SET is the existing complete `algorithm=mappo` path with route off, n_Z=n_z=1,
no high-level/discriminator training or discriminator reward, held central
snapshot enabled, and k restored to10 after the algorithm switch. Low PPO,
value learning, recurrent chunking and primitive action execution are real,
not a target-selector surrogate. H−SET includes their different parameterization,
latent coordination, optimizer work and internal information routing.

Common settings follow the original per-tick FitSpec: hidden/GRU/embedding256,
8 heads, two encoder/decoder layers where present; gamma .99, GAE lambda .95,
15 PPO epochs, sequence batch32, coordinator batch1280, discriminator batch12000;
Adam learning rates all 1e−4, weight decay0, clip .2, value-loss coefficient1,
max gradient norm .5; value normalization on, observation/state normalization
and LR/entropy schedules off. H high/low entropy coefficients .07/.05; SET
high0/low.05. Gaussian logstd initial0, min−20, max2. No weight multiplier,
bonus sweep, head change, longer training, count bonus or extra fit is implicit.
The terminal successor is stored before reset and terminal bootstrap is zero;
recurrent entry masks and terminal/ten-tick segment boundaries keep native
semantics. Final parameter counts and optimizer ownership will be asserted from
these dimensions during selected implementation; they are not outcome-selected
architecture parameters or a new feasibility-fit requirement.

### Complete ordinary programmes

**Scheduled ray chain O.** Compute each cluster's registered ten-user mean m.
For the first three scheduled clusters construct six slots in deadline order,
inner then outer at 1/3 and 2/3 of the BS→m ray, altitude100. At t=0 enumerate
all 6! assignments of UAV IDs to these six slots using the legal initial global
positions. For assignment p, let a_j be the maximum of the two assigned UAVs'
`ceil(Euclidean_distance/30)` for window j=0,1,2. Choose the lexicographically
minimum tuple `(max(0,a_0−105), max(0,a_1−230), max(0,a_2−355),
max_j a_j, sum of all six arrival times, assignment-ID tuple)`. This is an
explicit deadline-first travel heuristic, not service-oracle optimization.
The 105/230/355 targets leave twenty transitions before those window ends;
actual payment may happen earlier while approaching a slot or fail despite
the distance estimate. No outcomes enter the matching objective.

At every primitive tick, for its current target x*, each UAV commands
`a=(x*−x)/max(30, ||x*−x||)` using its lawful current own position. After arrival
it commands zero. At t=130, the first ten-tick global refresh after window zero
ends, release the first pair and send it to the two fourth-cluster ray slots.
Use that same lawful held global snapshot to compare the two pair assignments;
minimize maximum arrival time, then total distance, then UAV IDs. No other pair
is released and there is no paid-window or service-responsive replanning. The
complete programmed schedule is fixed at reset; there is no hidden planner call
at an unscheduled time. Native box/height clipping, association, relay routes
and service still determine the score. This preserves a concrete ordinary
alternative with geometric task knowledge and identical external rights, without
calling it a theoretical ceiling or claiming C safety.

There are 720+2=722 assignment comparisons and 36+4=40 position-to-slot distances
per O mission, with zero radio-score calls, candidate rollouts or learned labels.
Both worker and reader repeat this exact small calculation on the actual input.
O does not query the learner and does not discard a difficult first window.

**Sticky random floor B.** At reset each UAV draws an independent target uniformly
in xy [0,5000]^2 and height[50,150], then uses the same bounded straight-line
per-tick steering formula. At t=10,20,…490, each UAV independently retains its
target with probability .9; otherwise redraws it from the same distribution.
Use a dedicated PCG64 stream seeded by `SeedSequence([w,4])`, process UAV IDs in
order, and draw replacement coordinates only on replacement. B has the same
allowed inputs and reads no hidden reward/counter; the public registry need not
be used. It is a transparent untrained floor, never substituted for O as the
competent ordinary control. Its activity is measured in the fixed panel; no
hit-rate calibration or threshold tuning precedes learning.

The original local C/G and frozen S/Bstar used N5/H256 and a different action,
objective and information contract. Their old performance is not inserted as
an unrun baseline on N6/H500. O and B above are the two actual proposed ordinary
programmes, both with full native outcomes.

### Fixed exposure, initial-policy identity and one endpoint mode

Propose exactly three new 360,000-step fits: H, H-noD and SET. Each uses16 lanes,
500 steps and45 rollouts/updates, hence720 episodes. All see the same ordered720
training world IDs. H/H-noD initialize with seed109230101 and identical complete
module/normalizer state; SET initializes with109230102. After factory creation,
reset training Python/NumPy/Torch RNG with109230201 for both H and H-noD, and
109230202 for SET. This couples H's initial randomness to its ablation, not three
independent learning replications. Reward-induced updates and subsequent
trajectories are allowed to diverge naturally; no cross-arm state, data or
normalizer is synchronized after training starts. Different SET random-call
structure is not represented as matched primitive noise.

Keep initialization and final weights, with no score-selected checkpoint and no
intermediate environment evaluation panels. Read all45 training rollouts for
reward acquisition, counters, intrinsic/external magnitude, gradients, optimizer
counts and complete native service/travel trajectories. Those on-policy curves
are training-exposed evidence, not holdout performance. There is no early stop
for a favorable or unfavorable scientific score. A correctness or resource
failure preserves the prefix and counts the started fit; it is neither a
scientific zero nor permission to restart it automatically.

Evaluate **sampled deployment only**, fixed in advance, once per fresh world per
unique programme. Run one world at a time to make per-world RNG binding
independent of batching; reset recurrent states and all episode-local state.
Before each world use `seed_rng(w+51)` for Python/NumPy/Torch and the exact bound
checkpoint. H/H-noD use their original skill sampler and Gaussian action
sampler, SET its original action sampler. This defines one stochastic deployment
trajectory per world/programme, not a deterministic-versus-sampled selection or
a paired-noise proof across differing architectures. Evaluation uses strict
state loading, train(False)/no_grad, zero optimizer calls and unchanged complete
parameter/normalizer digests. The native `step` path also computes critic values;
those forwards are included in price.

H-initial and H-noD-initial are the same deployment policy **by source and full
input/state/RNG identity**, not because one audit happens to agree. Only the
training reward flag differs. The flag affects `store_transition_batch` reward
construction (`agent.py:4484–4490`), not the skill/action inference path;
`use_discriminator_path` remains true because training stays enabled
(`agent.py:564–567`). Bind identical actor, coordinator, critic, discriminator and
normalizer states, initial skill/hidden/reset masks, core/adapter source hashes,
world packet and sampler RNG state. The noD initial endpoint references the
same 32 H-initial raw trajectories without a second native rollout. One separate
audit world runs both initial configuration labels to verify this wiring; it
cannot substitute for the identity argument. If source or state identity fails,
this deduplication contract has failed: repair the binding before result execution,
not reinterpret the one audit as proving equivalence or buy an unpriced panel.

There are seven **physically evaluated** main programmes: H-initial (also noD
initial), SET-initial, H-final, H-noD-final, SET-final, O and B. There are eight
logical endpoint labels when the noD initial alias is shown. Each unique programme
gets the same32 fresh worlds at500 steps:224 missions/112,000 native steps.
The eight audit missions are initial H/noD/SET, final H/noD/SET, O and B on the
separate declared audit world:8×500=4,000 steps. They are correctness evidence,
not appended to the32-world estimand. Initial audits may precede fitting; final
audits use the selected fit endpoints and do not create a new fit.

The audit and direction tests must cover exact packet/tensor identity, native
post-routing score, idempotent diagnostic reward calls, 19/20/21-length synthetic
service sequences, window boundaries including125/250/375/500, once-only payment,
zero dense learning term, clipping and terminal storage, legal snapshot clocks,
no actor ACK/progress, and H/noD initial identity. Pure-mask/coordinate/config
checks add no environment or RF query. Model-construction/shape inspections add
no optimizer steps; actual inference is covered by these eight missions and
its charged reader replay. No diagnostic fit or calibration panel is included.
A materially necessary extra dynamic training test would be explicitly priced,
not hidden as free engineering or automatically used as a learnability gate.

### Full prospective accounting and resources

The exact finite-effect proposal, after initial-policy deduplication, is:

| Work | Native team steps | Episodes / other dominant work |
| --- | ---: | --- |
| Three fits,360k each | 1,080,000 | 2160 episodes;3 started fits;135 full update calls |
| Seven unique main programmes×32×500 | 112,000 | 224 frozen missions |
| Eight correctness missions×500 | 4,000 | 8 missions outside the estimand |
| Result reader | 0 | all232 frozen missions;all training records;no rerun of the environment |
| Calibration/search/external teacher labels/experimental LLM forwards | 0 | none |
| **Total** | **1,196,000** | **2392 physical missions;7,176,000 UAV transition rows** |

The Oracle's 1,212,000 arithmetic counted the two identical initial H labels as
separate full panels. The reduction is exactly32×500=16,000 steps; it removes no
logical comparison, final programme, world or audit. This is the draft's proposed
price, not an accepted launch ledger. Window bookkeeping executes once per native
step; preserving the host's diagnostic chain means2,392,000 dense-contract
reward-method entries plus2,392,000 parent diagnostic entries. Those repeated
computations are priced through native CPU, not called extra scientific samples.

For each fit, the low buffer has16×500×6=48,000 agent-tick rows per rollout,
4800 ten-step chunks. Batch32 means150 minibatches per epoch,2250 per rollout
and **101,250 actor plus101,250 critic optimizer steps per fit**. Across three
fits that is303,750 of each, and97.2 million agent-tick presentations to each
low network (32.4M per fit). Native collection adds6.48M actor and6.48M critic
rows before any endpoint or reader forwards.

Each H-type fit has800 high-level team records per rollout. Fifteen epochs and
batch1280 give675 coordinator optimizer steps/fit; two fits give1350 and1.08M
team-record presentations, including their associated individual assignments.
D2's held-coordinator evaluation still runs on499 of500 episode steps even with
infinite costs: two fits add718,560 team-row evaluations, alongside72,000 actual
team skill draws and432,000 individual skill assignments. Fixed caps do not
make that internal path cost zero.

Each H-type fit also collects360,000 endogenous team-skill labels and2,160,000
individual labels. Its discriminator buffers clear after every update; original
batch12000/15-epoch loops give675 team-D and2700 individual-D optimizer steps.
Together H/H-noD therefore give1350 team-D and5400 individual-D steps,10.8M team
and64.8M individual classifier row presentations. Total optimizer steps across
all modules/arms are **615,600**. H alone additionally computes per-tick reward
logits on360,000 team and2.16M individual rows; noD skips those reward forwards
but retains all discriminator training above. There are **0 external supervised
or teacher labels**, not “zero labels of every kind.” Initialization, buffer
allocation and strict checkpoint/model construction remain CPU/RSS work.

The endpoint/audit model missions comprise100 H-type and66 SET missions:
83,000 team steps,498,000 low actor rows and498,000 critic rows in the worker.
H contributes5000 team skill draws and49,900 held-coordinator team-row evaluations.
The frozen reader replays those exact model/input/RNG paths once, adding the same
counts, without gradients or native stepping. It checks actions/log probabilities,
hidden/snapshot timing and parameter/normalizer digests. It does not train again
or claim independent replication of every optimizer gradient.

O and B each have33 worker missions (32 main+1 audit). Each produces99,000
individual velocity commands; reader reconstruction repeats them. O's worker
has23,826 assignment comparisons; worker+reader **47,652 comparisons** and2640
position-to-slot distances. There is no static RF menu or planner sampling price
hidden behind the name O. The reader's single geometry reconstruction per initial
state and frozen transition is232×501=116,232 geometries; at300 user links,
15 unordered UAV pairs and6 BS links this is **37,310,472 distinct distance/path-loss
relations**, with both directions checked where native routing uses them. This
is computation on stored states, not a new counterfactual policy/environment query.
For all training and frozen records it independently reduces true user-mask/route
records into1,196,000 window updates and59.8M per-user service indicators. Training
RF is not replayed at every tick: its native records plus the eight correctness
missions and common verified physics path support the training ledger. Any
additional geometry/model replay must be visible in the final query/CPU ledger.

Resets also perform channel work. Preserve explicit counts of constructor and
explicit reset evaluations; the original style has at most752 per fit
(16 construction+16 first resets+45×16 episode-end resets) and two per frozen
mission, **2720 reset evaluations** total. The final unconsumed episode-end reset
is not a training transition; its CPU/RF work is still charged. If the original
eager final reset is retained, its unused IDs are109210720…109210735 (48 reset
materializations across the three fits), not part of either endpoint or training
return estimand. Terminal masks must exclude their values from learning targets.
An implementation may avoid redundant resets without increasing any scientific
exposure, recording actual counts. The model-row totals above enumerate collection,
minibatch and frozen replay work; constructor, bootstrap and diagnostic forwards
are additionally metered in the complete CPU/call ledger, not declared nonexistent.
No timed probe is purchased to estimate the below runtime.

The direct old cost evidence is `resources.cpu_seconds_in_run_fit` in these
original summaries; the field includes that run's collection, optimization,
model/checkpoint work and old panels, not just pure training:

| Original run under `runs/coupled_host_joint_skills_stage1/` | CPU seconds | Recorded wall seconds | Peak RSS KiB |
| --- | ---: | ---: | ---: |
| `b01_fit_H_931201_a01/summary.json` | 21796.376754 | 5442.5108 | 2556868 |
| `b01_fit_H_931307_a01/summary.json` | 20358.216432 | 5068.6177 | 2553112 |
| `b01_fit_H_931413_a01/summary.json` | 21378.762714 | 5284.8161 | 2562960 |
| `b01_fit_SET_932201_a01/summary.json` | 15697.134229 | 3991.3408 | 1112376 |
| `b01_fit_SET_932307_a01/summary.json` | 15545.113997 | 3952.2655 | 1120724 |
| `b01_fit_SET_932413_a01/summary.json` | 16386.693979 | 4165.3953 | 1138868 |
| `b03_fit_SETT_932201_a01/summary.json` (macro, not this learner) | 6438.930791 | 2009.8438 | 503580 |

Those are3 H and3 SET already-paid fits plus the distinct macro fit; none is new
work or a fitted throughput model. The old per-tick panels cost192×500 steps per
fit, more than this proposal's endpoint allocation, but new registered inputs,
full trace recording and reader work add expense. H/H-noD retain expensive
classifier updates. Merely applying the macro 1.79h rate to H is unjustified.

**Prospective full-chain prediction:18–26 CPU hours**, including native training,
initial/final/ordinary/audit execution, frozen forward/physics reading,
construction and necessary checks; **0 GPU hours** under the original CPU path.
This is a transparent forecast with source support and uncertainty, not a claimed
measurement or an accepted cap. Predict roughly5–9 wall hours for computation
with four Torch CPU threads when uncontended, plus **16–28 hours of agent support**
across contract, bounded implementation/review, collection, complete reading,
independent diagnosis, publication and cleanup; these scopes overlap in wall time
and must not be summed as measured elapsed time. There is no inherited10-CPU-hour
veto. A practical resource overrun or implementation change still needs a visible
updated price, not automatic continuation or a disguised additional fit.

Prefer configured `wsl_4070`, one fit at a time, CPU device, Torch threads4;
OMP/MKL/OpenBLAS/NUMEXPR1 as in the measured source. The old environment identities
are Python3.10.21/Torch2.7.0+cu118/NumPy1.26.3; a live available configured profile
must be verified at actual admission, not assumed to survive cleanup. Provisionally
request8 GiB available RAM and8 GiB free disk at each launch; this is a request
for later real-node admission, not a node reservation now. Exact installed
interpreter/profile and memory availability are remaining control facts for
Root/DM at the selected launch boundary; do not modify a shared base environment
or another direction's accepted operation to supply them.

Storage prediction is2–4 GiB new unique evidence/checkpoints plus about1.8 GiB
for one fully materialized source snapshot at a time; compression is not assumed
for admission. Retain compact training records for every tick (positions/actions,
packed association/route/user masks, skills, external/intrinsic reward components
and window events), full232 frozen mission traces for the declared reader, initial
and final states and one canonical copy of necessary reader evidence. Full 300-link
training SINR matrices and duplicate full raw-observation arrays need not be
stored when the declared reader only needs their source-bound native masks and
geometry. Expanded low-level fields, exact serialization and checkpoint bytes
will be measured during implementation and charged; the old .8–2GiB estimate is
not asserted adequate without those measurements. Publish compact summaries,
positive/adverse raw locators/hashes and source identities; keep unique bulk at
one canonical node location. After live-consumer checks remove unused snapshots,
scratch, cache and redundant artifacts and report measured allocated bytes, not
an archival copy chain.

### Full reading, decision and remaining boundaries

Primary paired endpoints are H-final−H-noD-final and H-final−SET-final on W,
reported as per-world differences, mean/median, wins/ties/losses and descriptive
95% paired t intervals with32 worlds. Report H-noD−SET, each final−its declared
initial, and all learned/initial programmes versus O and B without selecting the
best arm or endpoint mode after seeing scores. These are32 deployment-world
samples conditional on one trained instance per arm. They are not32 independent
fits, evidence for training-seed robustness, a confirmation interval, or a reason
to hide discreteness/floor effects. Preserve the actual vector of four completion
bits, completion times and maximum unbroken qualifying run for every mission.
No fabricated minimum-effect gate or pooled endpoint/fit sample count is used.

Read all50 users: total backhauled ticks, never-served count, per-user longest
zero-service run including the start/end censored gaps (500 for never served),
and full user masks. Report near/far and scheduled-cluster service separately,
team zero-service ticks/runs, access versus backhauled coverage, dense J, routed
front-end capacity, routing/association changes, path length per UAV, clipping
and boundary contact. A window can complete by rotating which eight users are
served; it does not prove continuity for each of ten people. Travel is not an
energy measurement in this host. Retain complete native positive, adverse and
zero-window examples with the same users, including first-window travel failure,
last-window unfinished runs and cases where W rises but unserved users or travel
worsen. Opportunity, learned capability, mechanism and complete-use judgments
remain separate.

Training hit counts, first positive window, skill occupancy/recognition, movement,
external/intrinsic magnitude and policy changes are explanatory observations.
They cannot replace the frozen full-service endpoint or establish that MI-induced
exploration caused a gain. The original high-level discounts and the rare R/6
scale make reward competition a serious alternative, explicitly retained before
seeing new data. If H improves over its initial and H-noD yet stays below O, this
can support a limited learning contribution while leaving O the practical
choice. If H/noD/SET all fail while O completes windows, report a fixed native
learning-package/exposure boundary. If O also has little opportunity, report that
complete task difficulty rather than assume an implementation failure, retune the
world law or call learning disproved. No outcome automatically queues a multiplier,
count bonus, extra seeds, fit extension, easier geometry or new gate.

**Feasibility disposition.** Source inspection supplies a feasible direction-local
host wrapper, task adapter, dimension extension and bounded runner/reader based
on the real native learner. No shared learner or paused Claude asset mutation is
currently necessary. The unresolved empirical questions—actual ordinary deadlines,
random/initial hit rate, discovery and useful complete learning—belong inside this
fixed purchase and are not missing prerequisite probes. Exact constructed parameter
counts, serialization sizes, complete source dependency manifest, decoder/terminal
checks and installed runtime availability remain ordinary implementation/admission
facts, explicitly not established by this zero-effect task. If implementation
exposes a material departure from the declared reward/interface/learner or price,
return that departure; do not silently substitute a toy or macro learner.

Root now owns the one cross-question investment decision and its applicable
independent scientific selection review of the Claude proposal, full Oracle answer
and this actual contract. The reviewer should specifically challenge whether this
finite three-instance learning question is worth its18–26CPUh forecast compared
with the remaining questions, whether the ordinary reference is competent for the
added public information, and whether the original reward scaling is an acceptable
fixed first comparison despite its clear failure alternative. Oracle is not that
independent reviewer and is not a continuing approval dependency. There is no
new L0 implementation or selected run yet. If selected, DM will own bounded
implementation, appropriate engineering review, exact publication, fresh admission,
accepted-operation collection, full reading, independent result diagnosis and
measured cleanup without per-fit Root permission. The historical directions,
existing B04 learning-curve fit set, accepted handles and Claude pause remain intact.

<a id="joint-window-oracle-original"></a>
### Complete temporary Oracle answer retained verbatim

Source runtime: `/root/successor_allocation_review`, actual turn
`01a0fb00-4f00-7c31-8c84-2f0859e636f9`, `gpt-6-astra/max`, timestamp
`2026-10-02T05:42:38.287Z`. The source rollout is
`/mnt/c/Users/fires/.codex/sessions/2026/10/01/rollout-2026-10-01T05-41-52-01a0f77c-49e7-7292-91a3-2d8fa8fb1975.jsonl`,
line2403. Root mechanically extracted the original to
`/tmp/hmasd-root-window-resource-oracle-20261001.txt`; metadata is
`/tmp/hmasd-root-window-resource-oracle-meta-20261001.json`.
Original UTF-8 bytes16805, SHA256
`389055881afe6782a2dec70c2a1f4c07af31e78791b5a6671765ccefaf9089ba`, independently
byte-checked here. The answer below is unabridged, including its separate DM3
recommendation; that section grants this DM no ownership or execution scope.
The draft above supplies my disposition and concrete source corrections.

<details>
<summary>Original Oracle final answer, unedited</summary>

<!-- BEGIN JOINT-WINDOW ORACLE ORIGINAL UTF8 -->
**建议保留当前分工：B04 按已选合同继续；DM2 完成一个联合持续服务窗口的三臂学习合同；DM3 完成 C 目标上的 E/B 资源分配合同。** 两项合同准备都有明确终点，均不需要先购买效果筛查。闭合后，我认为它们比修补 S/C 门控、继续改 H_T 同分规则或重复最近的静态排名更值得投入。

这是有历史上下文的建设性建议。我参与过前序设计，也读过 Root、DM 和 critic 的解释，**不是独立盲审或实现正确性证明**。

**新结果改变了什么。**

B02 保留了实际学习能力：S_L0/S_L1 相对 G 的 native J 分别约提高 .0152/.0224，服务增加、路径减少。Bstar 则以更多移动换来较少未服务用户和较短缺口。这些是不同用途的正资产。四步 own-count-zero 接管对 S_L1 和 G 明确不利，而且发生了真实动作变化；正反例也排除了把全部现象归为“导航弱”“接管太晚”或“接管未激活”。当前应结束这个门控配方，保留学生及校准策略的能力。

B11 同样提供了能力，而非默认升级：H_T 相对 H 减少路径约 559 米/UAV、消耗约 8.09 Wh、返航代价约 13.29；但最低用户任务平均 QoS 下降 .01648，完整 J 增益仍不确定。独立 critic 的新证据尤其重要：31 个共同首分歧处，两候选三点模型 QoS/return 相同，真实随后 30 步 QoS 却是 20 升、11 降，29/31 连相应采样时点也不同。**名义同分不意味着服务守恒，较短名义移动也不是无代价改善。** 三次浮点尾数级改选合法，但不构成自动加 epsilon 的理由。

这些结果支持发展“学会联合任务”和“完整服务—资源分配”两个问题，而不是继续追逐最新配方的局部修补。B09 的 F−H 正能力、F−C 缺口，以及此前信息、连续性和普通规划的正反证据均保留。

**第一项：DM2 研究明确任务信息下，技能多样性是否帮助学会跨窗口的联合持续服务。**

我推荐采用下面这个具体实例收敛合同，而非直接执行 Claude 修订稿中的四臂方案。

- 使用冻结 D2 的 N6/U50/H500、自由空间无线、逐 primitive 连续动作和 k=10 技能时钟。四个 125 步窗口分别开放四个远簇，顺序由世界 seed 随机排列，每簇只出现一次。
- 在一个窗口内，**每步至少 8/10 用户有原生回程服务，连续达到 20 步时首次奖励 1**，每窗口最多一次、全任务最多 4。这不要求连续服务的是同八个人；必须同时读取全部 50 用户的服务与缺口，不能把窗口完成等同个体公平。
- 首次采用纯窗口奖励，`w_dense=0`。不同时加入 decoy、count bonus、四倍判别器权重或难度搜索。
- 三个学习臂为原逐步 HMASD 默认配方、同层级关闭判别器奖励、同权限完整 SET。各一个真实 fit、各 360k native steps；同一组训练世界、固定训练终点。它们是三个训练实例，不是三个独立重复。
- H 与 SET 保持原有完整程序的信息分配及同频 held global snapshot。注册坐标、完整窗口顺序和时钟显式授权；真 ACK、路由、窗口进度真值不额外成为 actor 输入。SET 直接消费中央快照而 H 经技能编码使用它，本身就是架构差异，不能声称逐层表示完全相同。

这同时检验一个有用正解释和两个普通解释：判别器可能形成便于复用的联合行为；也可能仅层级承诺就足够，或普通 flat 学习已能解决任务。三臂可以区分这些结果，**不能独立证明判别器优于所有探索奖励，也不能把 H/noD 差唯一归因于探索而排除优化或正则化作用。**

为避免原文“任意单 UAV 不可服务”的无界验收，我建议采用一个明确、有界的世界生成法：四远簇中心为 `(500,500)、(4500,500)、(4500,4500)、(500,4500)`，中心每轴抖动 ±50 米，用户处于中心半径 100 米的圆盘内；初始 UAV 保留原 uniform 法则，近簇另固定公开分布。在当前自由空间常数下，

\[
R=\frac{c}{4\pi f}\,10^{(23-(-80)-3)/20}\approx1193.7\text{ m}.
\]

远用户到 BS 的距离下界约 2657 米，大于 \(2R\)，因此排除单架 UAV 同时直连 BS 并服务该用户。这是由公开传播法则得到的几何约束，**不是学习可达性或完整任务成功证明**；无需逐世界评分、拒绝采样或调到指定随机命中率。

最强普通参照应成为实际程序。我建议一个知道完整日程的 **ray-chain 预置程序**：为前三个截止窗口分别设置 BS→簇中心的 1/3、2/3 两个站位，以时限优先规则完成六架 UAV 的匹配；第一组窗口结束后提前转往第四簇。DM 固定高度、匹配排序、释放时刻和动作公式，采用真实原生执行。它是有竞争力的普通规划参考，不是已经实现的 `O_W`，也不是全局最优上界。初始随机位置造成的首窗可达性不足应保留，不按参考得分筛掉世界。

这个新问题不同于 B04：B04 学习静态完整布局选择及数据曲线；这里学习由实际窗口回报驱动的时序联合控制。也不同于旧 registered-service 的 F——旧 F 是每用户窗口内接触次数汇总，当前 S_L0/S_L1 又是监督学生，不能把它们直接接到一个不存在的 PPO/GAE 接口上。

**主观察及处置。** 首次完整读取应包括训练首次获奖、获奖世界比例、各簇/各窗口完成分布，以及固定最终策略在 32 个 fresh 世界的完整任务。部署采样方式须事前固定；不能看完结果在 sampled、argmax 或温度之间择优。判别器准确率、访问面积或某个早期命中只能辅助解释。

- H 比 noD、SET 有明确条件优势且跨不同簇完成任务：支持进一步研究技能包的经验利用和复现，尚不支持唯一机制或普遍算法优势。
- H≈noD，二者优于 SET：优先保留层级与承诺解释，不继续自动加判别器权重。
- SET 足够好或更好：保留普通学习能力，改变对层级投入的优先级。
- 三者有学习但明显低于普通程序：仍可能是有价值的能力结果，下一步取决于数据效率或可复用性，而非必须胜过教师。
- 三者均未形成任务能力：结束这个冻结任务—接口—曝光配方；不能唯一诊断任务过稀、表示失败，也不自动加 seed、延长训练或改窗口。

**现在值得买的是一次有终点的合同闭合，而不是效果校准链。** DM2 应在约 4–6 支持小时内给出上述世界、输入、普通程序、奖励推进、训练和完整计价的一份准确合同。特别是 `_compute_reward` 在当前宿主会被多处调用；窗口计数应只在完成原生 post-routing step 后推进一次。原配置也有明确的观察/状态编码，不是任意追加维度就自动正确。这些是尚未确定的科学和实现输入，不能靠先跑随机命中率解决。

拟议完整价格为：

| 项目 | 建议账目 |
|---|---:|
| 三次训练 | 3 × 360,000 = **1,080,000 native** |
| 三个初始、三个最终、普通程序、sticky reference；各 32×H500 | **128,000 native** |
| 暂列八个完整审计任务 | **4,000 native** |
| 总计 | **1,212,000 native，3 fits，0监督标签，0 GPU** |
| 完整 CPU 预测 | **16–24 CPUh**，需按适配后的准确合同修订 |
| 支持工作预测 | **16–28 小时**，包含上述合同准备 |
| 存储初估 | 新证据约 **0.8–2 GiB**；保存粒度、reader 和 source 保留方式仍需定价 |

这是初始投资估计，不是已接受边界。**超过 10 CPUh 不构成否决。** 若合同确实承载上述区分，约二十 CPU 小时本身可以值得；应依据正确全价判断，而不是依据错误便宜价购买。

**Claude 77c02de6 的修订是实质新提案，但尚不能按 7.6 CPUh 直接执行。**

它已明确列出四个学习臂，这一点应承认，不能继续说“根本没有计价”。但把各臂按 1.79 CPUh 估算仍用了不同接口的宏动作 SET-T。另有几项会改变比较：

- Toy 的 12.5% 是“episode 至少命中过一次”；`.131/5≈2.62%` 才是 window 比例，不能支持设计中的 5–20% window 校准带。
- Toy 把外在加内在回报用于三个策略层的更新；原 HMASD 高层使用外在回报，低层才加入判别器项。其每段一次的 tabular intrinsic 也不同于原逐 tick 神经判别器。四倍权重不是可直接移植的单位。
- Toy 的主要成功集中在重复开放两次的 site 0，尚未建立跨四簇日程组合能力。
- 原文 40 个用户的 xy FP32 坐标为 320B；400B 对应 50 个用户，仅坐标，不含日程等字段。信息合同必须明确。
- 对固定动作轨迹，延长连续保持要求只会更严格，不能当作降低难度的通用办法。
- 七月 R35/R36 已研究过稀疏访问；“此前只试过稠密任务”“静态规划器按构造最优”“新的正结果将是项目第一次能力”均超出证据。

因此我建议三臂直接完整比较，删除强制 toy→命中率门→改难度→四臂这一进入链。新的合理预算可能更贵，但问题更清楚。

Root 要求的原始价格定位如下。共同字段为 **`resources.cpu_seconds_in_run_fit`**；它包括该旧 `run_fit` 的实际工作，不是纯优化器时间，也不是 wall time。

| 原 summary | CPU 秒 |
|---|---:|
| [H 931201](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b01_fit_H_931201_a01/summary.json) | 21796.376754 |
| [H 931307](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b01_fit_H_931307_a01/summary.json) | 20358.216432 |
| [H 931413](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b01_fit_H_931413_a01/summary.json) | 21378.762714 |
| [SET 932201](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b01_fit_SET_932201_a01/summary.json) | 15697.134229 |
| [SET 932307](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b01_fit_SET_932307_a01/summary.json) | 15545.113997 |
| [SET 932413](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b01_fit_SET_932413_a01/summary.json) | 16386.693979 |
| [宏动作 SET-T 932201](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b03_fit_SETT_932201_a01/summary.json) | **6438.930791** |

前三次逐步 H 为 5.66–6.05 CPUh，逐步 SET 为 4.32–4.55 CPUh。宏动作 SET-T 的 1.79 CPUh 不能按“同为 360k native”推广到它们。

**第二项：DM3 研究同一 C 目标集合中，异质电量的分配是否比最省飞行能量更有完整价值。**

我推荐 E/B，而不是另一轮 H_T 排序微调。它继承 B11 的资源能力及服务代价，同时移除旧短服务模型作为选择依据，询问一个不同的、可被普通方法挑战的问题。

在每个 C 规划时刻，沿真实 assignment provenance 取 `SERVICE、非原 C 排除模式、finite target` 的成员，最多六架。保持该时刻 C 生成的目标多重集、relay/ring/NaN 目标和其他执行规则，仅选择这些 service 成员的目标标签置换。

- **E：**最小化按公开 C 运动与功率法则计算的、不中途改计划的飞抵 Wh。
- **B：**最大化飞抵后返航 slack 的排序向量，先最大化最小 slack，再第二小，依次；完全相同时以 E 次序、保留 base、固定列号消歧。

可写为

\[
s_{ij}=b_i-\frac{E^{fly}_{ij}+E^{return}_{j}}{C_{\rm bat}}-\rho .
\]

必须采用分布目标而非 `sum(slack)`：在当前同容量宿主和固定目标多重集下，总初始电量及总目标返航项对置换不变，最大化 slack 总和会退化成最小化飞抵能量，根本没有测试电量异质性分配。

B−E 是主要新对比；两者对旧 C/H/H_T 的完整结果提供用途与机会成本。E 是强普通竞争者，拥有相同成员、目标和完整置换机会。B 获得更多低储备收益却损害服务，完全可能。

源接口已经足够具体：从 `AssignmentController("C")` 分支接 hook，可避免旧 tracker、short-service model 和 RF 评分；实际 Hungarian 行列及角色可用；选中后在唯一 `act` 之前写回 targets，进入本臂下一轮 C hysteresis。仍须由 DM 固定逐段飞行、最后短步、并行爬升等能量定义，并实现新的 permutation/实际状态 reader。arrival slack 不计后续 C 重规划、guard、充电排队和未来服务，不能称安全证明或精确完整 rollout。

我推荐一次完整 E/B 比较，使用原 32 个已曝光世界，明确是 development；旧 C/H/H_T 只复用绑定的原生证据，不重复飞行。

| 项目 | 初始完整价格 |
|---|---:|
| E/B 主任务与四个工程任务 | **68×H3000 = 204,000 新 native** |
| planning epochs | **6,800** |
| worker＋完整 reader 的置换上限 | **9,792,000** |
| 预计算飞行/slack 边上限，含 reader | **489,600** |
| 学习/旧预测调用 | **0 fit、0标签、0 GPU、0旧 short-service/RF/tracker 调用** |
| CPU 预测 | **2–5 CPUh**，不是已测价格 |
| 支持预测 | **10–16 小时** |
| 新 raw 初估 | **0.8–1.5 GiB**；含一次 source 的保留峰值约 **3–5 GiB** |

公开能量边和置换评价是新计算，不能因“0旧 RF”而记成零模型/零选择成本。每计划预计算至多 36 条边，避免每个置换重复积分；最终存储方式也必须纳入全价。

这里最小有用观察是完整 H3000 的 native J、QoS、返航与储备、路径/Wh、同用户服务、低端用户和右删失缺口，而非证明 target slack 更高。若 B 比 E 改善资源且保留或改善服务，支持进一步发展资源分配；若只交换服务与资源，按用途保留；若连 E/C 都没有完整优势，则结束这套意图 slack 配方。以上任何分支都不自动授权调权、延长预测或加 epsilon。

**为什么通信协议暂列下一候选，而非同时展开。**

通信受限技能组合仍有价值，但当前六类 team skill 的 \(\log_2 6\) 不是完整通信账。还要包括 agent codes、帧头、时钟以及协调器取得全局状态/各 agent 观察的上行信息；原 B/O/L 的实际包也不是一个 team symbol。新的问题应是同 wire budget 下，学习编码与有竞争力的普通 cluster/codebook 协议相比能保留多少完整能力。它需要自己的信息、decoder 和训练合同，不能靠把现有标签重命名为“2.6 bits”得到。已有通信和窗口历史也使其不属于未探索领域。本轮先把窗口学习和 E/B 两个不同问题闭合，避免同时购买三种新接口。

**原始文献桥及本次检查边界。**

HMASD 原论文为 InstSci **MARL-0553，*Hierarchical Multi-Agent Skill Discovery***：

- [结构化 JSON](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0553.json)
- [原论文 PDF](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0553.pdf)

我直接核对了 **PDF p.5 §3.2 “Skill Coordinator”**：输入全局状态和全体观察，自回归生成 team skill 与各 agent skill；以及 **p.6 “Overall Training and Execution” 的 Eq.(4) 前一段、Eq.(4)、Eq.(6)**：高层回报累积外在 team reward，低层加入两个判别器项。这是不能直接移植 toy 三层同回报或 ×4 权重的承重区别。

MAVEN 的持续 latent 与轨迹多样性给出“协调探索可能有用”的桥，不给出这个 UAV 任务上的性能保证；已核其原论文 §4。[MAVEN 原论文](https://proceedings.neurips.cc/paper/2019/file/f816dc0acface7498e10496222e9db10-Paper.pdf)。通信候选参考 IMAC §4 的量化、编码及双向传输区分，不能以 latent 熵替代实际协议账。[IMAC 原论文](https://proceedings.mlr.press/v119/wang20i/wang20i.pdf)

本次复用了仍适用的前序源审计，直接检查了新 B02/B11 compact、正反世界解释、两份完整独立 critic、Claude 77 修订 report/prompt/design/toy 源、上述七份 summary、相关宿主/配置/奖励/assignment 接口；检索了三库及相关七月和外审记录。没有独立重复重建整批原生 raw，也没有运行新策略、模型、RF、native、toy 或 fit。世界与特征适配、奖励单次推进、普通程序及准确 reader/CPU/存储合同仍交两个 DM 闭合。

**MATERIAL_DISSENT: yes——针对把 Claude 77 修订直接视作约 7.6 CPUh 的可执行比较，以及由 toy 强制追加 ×4 和随机命中率准入；不针对联合窗口问题本身。对 B02/B11 保留能力、结束固定配方及 B04 继续执行没有实质异议。** 当前两项零效果合同准备是合适分配；后续选择和执行由 Root 与原 DM 按实际合同推进，本次临时顾问任务结束。


<!-- END JOINT-WINDOW ORACLE ORIGINAL UTF8 -->

</details>


<a id="b03-selected-disposition"></a>
## B03 selected joint-window comparison — 2026-10-02 UTC

Root selected the one complete comparison at
`6a8da6e5351fbcc518a173156686c028a02dd273` after reading the actual prospective
contract and the complete independent scientific selection. I have now read that
entire original, preserved below without abbreviation. It is the reused
`/root/next_study_review` context, actual `gpt-6-astra/max`, turn
`01a0fb33-300c-7f40-908f-7dc3a947d587`; it is independent substantive judgment,
not blind context and not Oracle self-review. MATERIAL_DISSENT:no covers this
three-instance purchase; the original criticism of the different four-arm,
7.6CPUh/weight-transfer/calibration proposal remains. No second selection is
needed for ordinary implementation.

I accept the limited scientific investment and both source/interpretation
corrections. The original DiagGaussian in `hmasd/r_mappo_utils.py:73–109`
initializes logstd at zero and directly exponentiates it. The nominal −20/2
configuration values are ignored on this path. B03 preserves that unbounded
head, its native host clip and its actual entropy/likelihood behavior; it does
not add a variance clamp or substitute TanhDiagGaussian. The prospective mention
of min/max must be read as unused configuration, not an effective bound.

O has stronger structural support than a generic random floor. The declared
geometry bounds arbitrary initial box-to-slot travel by roughly186 ticks and
the t130 reassigned pair's arrival by roughlyt316, leaving substantial later
window opportunity. These are analytic bounds, not measured completion or an
optimality claim. If O performs poorly, the first reading is its already-paid
same-world positions/arrival, association, routing and once-only ledger. A weak O
score alone cannot support the prospective draft's overly broad task-opportunity
explanation; distinguish an ordinary-program limitation or implementation failure
from native reachability. No O pilot, geometry retuning or additional mission is
added by this correction.

The adverse learning prior remains substantial. The review reconstructed old
per-step H/SET final holdout coverage around.211–.235/.132–.225 and roughly
2809–2926 clipped UAV steps per3000 in deterministic missions; SET already had
held global information. The new sparse external R/6 can make this worse. Those
facts constrain optimism without requiring another preliminary fit, changing the
unbounded head, or erasing S0/S1's separately demonstrated capabilities. The
comparison is selected because a different, explicit persistent joint-service
use can make learning meaningful, with matched noD, complete SET, initial-policy
and competent ordinary controls. A positive result is not owed. B04's separate
pre-fit SIGSEGV is a technical event, not learning evidence for B03.

The fixed purchase remains3 fits,1,196,000 native transitions and615,600 optimizer
steps; H/noD initial identity is deduplicated by source/state/input/RNG identity,
not an empirical guess. The forecast remains18–26CPUh and16–28support hours,
0GPU. All users, start/end censored gaps, complete task, travel, model/reader
and failed-work costs remain required. A material implementation deviation or
cost change will be exposed before dependent effects. The ordinary execution
path is now selected, subject to exact source publication and actual-node
admission; no worker has been admitted by this note. Existing source/asset
ownership, Claude pause and other accepted operations remain untouched.

<a id="b03-l0"></a>
### B03 L0 — one admitted native comparison and its complete saved-state reader

Deliverable: a new direction-local package
`experiments/candidates/uav_decision_generalization/b03_joint_window/`, matching
`tests/experiments/candidates/uav_decision_generalization/b03_joint_window/`,
compact records under `runs/uav_decision_generalization/b03_*`, and exact owned
input/ledger files under this notebook's directory. Do not alter B01/B02,
Claude's `coupled_host_joint_skills_stage1` files, `hmasd/`, `envs/`, shared
configuration or launchers. Reuse frozen host/core helpers read-only. The DM
remains the sole notebook/index writer and publisher.

The new `run.py` has explicit worker/reader entry modes, declared seed,
launch SHA, output and SHA-bound input/ledger arguments. It calls runner-side
admission before effects. The worker executes exactly the three fits once,
the seven unique32-world endpoint programmes and eight declared audit missions;
ordinary construction and all physics/reset/model/optimizer events are metered.
The reader binds canonical worker output through a SHA-bound locator's contents,
not a raw absolute argv path that the launcher may rebase to a snapshot. It
reconstructs the232 frozen missions' inputs/actions/RNG and physical service,
and every training window ledger, without native rollout or optimizer replay.
Each accepted worker or reader gets one native handle and same-handle observation;
uncertain/failed acceptance never starts a duplicate.

Invariants are the selected contract above: fixed generated world law/IDs and
404-byte extra packet; obs211/state154/SET1637; original per-step H/noD/SET and
Gaussian semantics; d2 caps10/+infinity; native high/low reward separation and
SMDP discounts; noD classifier training retained; once-only post-routing reward,
R/6 units and w_dense0; fixed sampled deployment; exact initial-state/RNG aliases;
full user masks and censored gaps; ray-chain O and sticky B exactly as declared.
No additional learner, fit, seed, bonus, clock, gate, difficulty search or outcome
selection belongs in this implementation. Preserve sampled versus host-executed
actions, original GRU masks, terminal successors and zero terminal bootstrap.

Use a compact trace schema with a raw manifest and hashes. Store each training
rollout's initial/post-step positions, raw/executed actions, association/routed
user masks, skills, external/intrinsic reward components, window counters/payment
and native service/movement diagnostics; store the full frozen mission inputs,
channel/association/route evidence and action/recurrent replay fields needed by
the independently written reader. Retain initial/final module+normalizer states,
exact configurations, input identities, RNG addresses and optimizer counters.
Do not add full training SINR/observation duplication where the declared reader
does not require it. Measure real bytes and construction parameter counts; source
manifest includes every runtime-consumed scientific dependency, not just the entry.
Partial artifacts survive an exception. No missing trace is repaired by rerunning
an already consumed mission.

Checks before actual result execution are source/schema/config and pure synthetic
ledger/geometry/normalization/control tests using pytest-owned scratch; no extra
environment mission, RF scorer or learner fit. Model construction/shape checks are
separately metered engineering work, with no optimizer or policy forward beyond
the charged audit/inference path. The8 actual audits cover the initial/final
policy sources and complete O/B and are inside1196000; they are correctness
checks, not outcome gates. An independent registered engineering Reviewer checks
reward placement, recurrent/terminal state, RNG, noD identity, source/checkpoint
binding, reader independence and the cost/count ledger. Its purpose is technical;
it does not revisit the accepted science. The DM owns repair and acceptance.

Implementation delegation is bounded to the native worker, schema, task/ordinary
adapters and matching pure tests. The registered Implementer writes only that
new package except DM-owned `independent.py` and its dedicated test, returns a
diff/check costs and deviations, and launches/commits nothing. DM writes the
saved-state independent reader, reviews the worker and owns integration. These
are separate behavior responsibilities sharing a declared trace schema, not
concurrent writers to the same files. Both preserve all other sessions' edits;
all shared Git mutations remain DM-serialized with explicit paths.

Stop the current technical attempt on an identity, count, nonfinite, missing-data
or contract failure and retain the exact partial state. Do not silently clamp,
change runtime, extend exposure or retry. Diagnose the actual failure and record
any materially revised attempt prospectively. Ordinary code repairs and source
publication need no per-fit Root ACK. CPU18–26h is a forecast, not a universal
hard cutoff or unlimited license; actual phase telemetry will support a public
re-estimate if material. Node memory/disk/profile admission precedes actual
execution, with one fit at a time initially and no claim that all selected
projects can occupy the node concurrently.

<a id="b03-independent-selection-original"></a>
### Complete independent scientific selection, retained unedited

The original below is copied byte-for-byte from the published archive at
`6a8da6e5351fbcc518a173156686c028a02dd273`,
`docs/research/archive/2026-10-01/RESEARCH-window-resource-independent-selection.md`.
Original13093UTF8 bytes, SHA256
`62787648765ac42ad7f07470e8cff62d6305fac562b1b675ea3626185f017799`.
Source rollout `/mnt/c/Users/fires/.codex/sessions/2026/10/01/rollout-2026-10-01T17-23-45-01a0f9fe-de22-7d73-82c2-129a0cadede6.jsonl`,
line1959, terminal `2026-10-02T06:23:01.661Z`. Its E/B portion does not assign this
DM another direction. My scientific disposition and L0 are above.

<details>
<summary>Original independent selection</summary>

<!-- BEGIN B03 INDEPENDENT SELECTION ORIGINAL -->
建议购买两项各一次冻结的完整比较：**E/B 的用途判断更直接、成本较低；联合窗口学习值得作为一次风险较高的能力探索。** 不增加前置效果筛查、权重臂或训练重复。当前合同已能承载这两项判断，但须纠正 Gaussian 参数的实际语义，并收紧普通 O 失败时的解释。

本评审复用了我对 B02、B10、B11 的上下文，我也曾提出 H_T；上下文中包含 Root、DM 和 Oracle 的既往解释。因此这不是盲审，也不声称是未受这些解释影响的全新独立上下文。以下结论来自对本次实际合同、承重源码和已付证据的重新核对，不以此前共识为依据。

**一、E/B：支持完整购买，研究对象成立。**

实际对象是 [B12 合同](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_transmission/NOTES.md:8505)，提交 `6fc708f745de10c5b9dcaf0e93fc6ff9dab161bc`。

这不是再微调 H_T。它问的是：在普通 C 已生成的服务目标集合内，分配预计资源负担，能否比只节省飞行能量提供更好的完整任务用途。E 是合适且有竞争力的普通挑战者：与 B 拥有相同合法输入、可动成员和完整置换机会；不需要再添一组“电量盲”臂才能购买这个用途问题。

我核对了实际 Hungarian 行列来源、C 的目标延续与动作生成、公开功率公式、合法电量/站点解码和原生返航余量定义。合同选择完整 leximin 有实质意义。固定成员与目标多重集时，

\[
\sum_i s_{i,\pi(i)}
=\sum_i b_i-\frac{\sum_i E^{fly}_{i,\pi(i)}+\sum_jE^{return}_j}{160}-m\rho .
\]

因此最大化总 slack 会退化成最小飞行能量。完整排序向量才真正改变低资源负担的分配；这不是给 E 换一个名字。

不过，最强竞争解释必须保留：

- **E−C 包含取消部分原分配迟滞的影响。** 原 C 用水平距离并给延续目标约 300 米优惠；E/B 可覆盖这个选择。改善可能来自重新分配或改变持续移动，而不能单独归功于精细能量计算。
- **B−E 不是电量信息的唯一作用。** 两臂输入相同，改变的是分布目标及目标返航要求的使用方式。即使电量接近，return 项也可能改变 B 的排序。
- **各自到达时的 slack 不是同一未来时刻的完整队伍状态。** 它没有计入到达后的悬停服务、下一次规划、实际 guard、返航释放、充电竞争和途中改道。服务成员仍可能是真实路径中的中继；固定 C 的 relay 标签不固定原生路由。
- 每次保持的是**本臂当时**的 C 目标多重集。后续历史、迟滞和布局都会分歧，不能把逐计划代理改善相加为实际节省。

这些限制说明完整原生比较必要，并不构成先买诊断链的理由。合同已经包含从标签、坐标、提交到实际运动的曝光，以及同身份用户的服务和删失缺口，能够区别未激活、标签别名和主动有害的干预。

旧正面资产没有因此失效。H 的服务能力、H_T 对 H 的实际路径约 −559 米/UAV、能耗约 −8.09 Wh 和返航代价改善应保留；H_T 最差用户 QoS 下降、完整 J 优势未确定，以及对 C 仍更费移动和能量，也都必须保留。B09 条件预测收益及完整 F−C 缺口继续有效。E/B 获得资源优势不会自动取代这些不同用途。

我建议按以下结果改变选择：

| 完整结果 | 应改变的判断 |
|---|---|
| B 相对 E 改善资源，并保持或改善服务、个体尾部 | 保留资源分配准则的条件用途；是否扩大，另看收益与全价 |
| B 节省资源但损害服务或拉长同用户缺口 | 保留明确取舍，不称服务公平、安全或默认升级 |
| E 有完整用途，B 没有增量 | 优先保留更简单的 E，降低对 slack 分布目标的投入 |
| 只有到达代理改善，或新臂没有有用的完整取舍 | 结束这个固定配方的自动投入，不自动补权重、预测或样本 |

最小有用观察就是合同中的完整 H3000 比较；一次短期 slack 展示不能替代它。

**二、联合持续窗口：支持购买三实例，但这是能力探索，机制结论要窄。**

实际对象是 [联合窗口合同](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:2446)，提交 `1c1ba086fb1275eb9ee9de07d6260a9e880a456f`。

这次任务改变了什么，现已说清：固定注册地图和完整日程，要求远簇的团队回程服务连续达到阈值；每簇只开放一次，四个窗口不能靠反复完成同一簇获得高分。它与旧静态 dense coverage、监督 S 策略和 B04 布局选择不同，值得直接研究。

按 scientific-tools 的更丰富合同比较方法，公开注册信息是允许的新任务条件。404 字节只是额外任务载荷，不是完整通信价格。普通 O、随机 B 与学习程序得到相同外部权利；因此不必自动增加“没有地图”的全因子对照。相应地，新结果不能解释为对旧信息合同的改进，或真实无线通信零成本。

几个承重设计是成立的：

- 有界几何与公开自由空间法则支持远用户需要中继的结构判断，不依赖筛选世界或调随机命中率。我复核了约 2657 米的远用户距 BS 下界及 ray-chain 链路界。
- `CoupledRelayHost` 确实会在一次 primitive step 内多次计算诊断奖励。把窗口 ledger 放在最终 post-routing step 后、每步只推进一次，是必要的正确接口。
- H 的 d2 高层使用段内折扣外部 `R/6`，跨段使用 `gamma^elapsed`；低层才加入判别器项。不能把 toy 的全层共同回报移植解释到这里。
- noD 只关闭判别器奖励，保留分类器训练及同样的模块结构，是有意义的匹配干预。
- H/noD 初始面板按完整模块、状态、输入和随机数身份去重合理。一个审计世界只能验证接线，不能替代这个身份论证；合同已经区分二者。
- O 已是完整普通程序：预置三对 ray slots、明确匹配次序和 t130 转移，不是一个尚未定义却被称为上界的“规划器”。

**最强不利先验仍然很重。** 我重新读取了旧逐步 H/SET 六份原 summary。最终 holdout H 的回程覆盖约 .211–.235，SET 约 .132–.225；确定性面板每回合约 2809–2926/3000 个 UAV-step 被限幅。它们没有形成有用的普通规划替代。SET 当时已获得 held 全局快照，不能把旧失败全部归为缺少中央信息。其他已付有界头、目标接口等阴性结果也仍然约束乐观预期。

新合同继续原 Gaussian 和熵系数，外部奖励又变为罕见的 `R/6`，因而三臂都没有任务能力是可信的结果分支。**这笔投资值得的理由不是 toy 保证成功，而是新任务确实给持续联合行为一个不同的用途，并有直接 noD、SET、初始策略和普通 O 对照。** 一次固定购买可以改变对这个用途的投入；不需要先证明学习能够成功，但也不能在失败后自动重新解释为“只差更多训练”。

需要作两项具体澄清：

1. **Gaussian 方差没有声明中的配置夹持。** [DiagGaussian 源码](/home/fires/hmasd-wsl/hmasd/r_mappo_utils.py:73)以零 logstd 初始化，随后直接 `exp`，不读取 `continuous_logstd_min/max`；夹持只存在于 TanhDiagGaussian。合同中的 −20/2 应写明是该路径不使用的配置字段。保持原 unbounded 头，不在实现时悄悄补 clamp。这是源语义修正，不是购买新头。
2. **O 接近零不能直接证明整个任务缺乏机会。** 已定边界使任意 box 位置到 ray slot 的保守到达时间约不超过 186 步；t130 转移的那对约至 t316 可到达，而另外两对已预置。结合 FDMA 和静态链的几何余量，O 是有相当强结构依据的参照。若它仍接近零，应先用本批已有轨迹对齐到达、关联、路由和单次 ledger；也可能是 O 程序自身的限制。不能把弱 O 结果直接升级为任务不可达或学习机会不存在。这里没有要求新 O gate，也没有把未运行的 O 称为已测高分或全局最优。

窗口结果应这样使用：

- H 超过共同初始和 noD，并在不同簇形成完成能力：保留这一次判别器奖励干预的条件增量。不能仅凭它归因于探索，或宣称训练种子稳健。
- H/noD 都学会且优于 SET：提高对层级程序的兴趣，但不能从“不显著差异”得到两者等价，也不能唯一归因于承诺机制。
- SET 学会或更好：保留普通学习能力，改变对层级复杂性的优先级。
- 学习程序低于 O 但确有完整能力：能力结果仍成立；是否继续取决于可复用性、效率或实际用途，不要求先赢普通教师。
- 三者均无能力而 O 有：结束这个固定任务—配方—曝光组合的自动投入。它不唯一识别稀疏程度、优化、表示或判别器作用，更不关闭长期学习问题。

一臂一个 fit、H/noD 共用初始化，仍只有一个训练比较块。32 个新世界提供的是条件于这些训练实例的部署差异；不能充当 32 次算法重复。完成窗口也不等于同八个人连续受益：全 50 用户、从未服务和首末删失 gap 是完整用途的一部分，不能退为附属指标。

**三、完整价格值得保留，不能用便宜版本替代。**

我独立重算了主要整数账，并核对旧原生 summary 的成本字段：

| 项目 | E/B | 联合窗口 |
|---|---:|---:|
| 新 native | 204,000，68 回合 | 1,196,000，2392 回合 |
| 新 fit / GPU | 0 / 0 | 3 / 0 |
| 主要额外计算 | ≤9,830,880 置换、491,376 边；旧证据读取另计 | 615,600 optimizer steps；低 actor、critic 各 97.2M 更新呈现 |
| 完整 reader | 新任务及绑定旧 C/H/H_T；不重飞旧策略 | 232 冻结任务的 forward/几何重建，加全部训练 ledger |
| CPU 预测 | 2–5 小时 | 18–26 小时 |
| 停止边界 | 6 已计量 CPU 小时，保留不完整 prefix | 18–26 是预测；明显超支须公开重估，不能当无限续跑许可 |
| 支持工作预测 | 10–16 小时 | 16–28 小时 |

窗口 noD 保留判别器训练，所以不能按“删除整个判别器”估便宜价格。旧逐步 H 是 5.66–6.05 CPUh，逐步 SET 是 4.32–4.55 CPUh；宏动作 SET-T 的 1.79 CPUh 不适用。新 reader 的约 3731 万几何关系、模型回放、存储和采集也不是零成本。E/B 的零旧 RF 调用同样不等于零新分析模型计算。

这些仍是预测，尤其窗口的输入扩展、完整保存和 reader 尚未实测。源快照、唯一证据、副进程 CPU、失败尝试、实际内存和磁盘峰值都应按合同记账。两题保持三个 DM 的责任分工，不要求它们同时占用节点；实际准入仍须服从可用资源。B04 的新 SIGSEGV 是无训练的技术失败，不进入本次学习负证据，也不授权重启或重审其配方。

**四、Claude 原稿的正价值与实质分歧都应留下。**

Claude 修订稿已经给出具体联合任务和 toy，不能说它没有建设性方案。toy 宽版的学习能力也是真实已付资产。但我独立检查源与两个保存 JSON 后，不支持由它直接推出四臂约 7.6 CPUh 的原生购买：

- `.131` 是五窗口任务的平均完成数，窗口比例为 2.62%；`.125` 是至少命中过一次的任务比例。
- toy 的回报进入全部策略层，原生 H 的奖励路径和单位不同，不能强制转移 ×4。
- 默认 toy H 没有建立相对 flat 的优势；×4 对 count-bonus 的最终水平差也未建立技能专属解释。
- 原始两个 JSON 没有后加的 per-site 结果字段。因此重复 site0 的后续分析可保留为报告中的诊断，不能称本次已从这两份 raw 独立重建。
- 对固定轨迹，延长连续保持要求不会降低难度。
- 七月已有稀疏访问研究记录；新成功也不会抹掉 S0/S1 等已保留能力，或成为项目“首次学习能力”。

当前实际三臂合同已经避开这些问题。我支持它，而不支持原稿的强制校准、调难度、×4 进入链。

本次直接核对了两份完整合同、窗口四个声明源 SHA、原生动作/无线/关联/路由/奖励接口、d2 与 noD 路径、七份原成本 summary、Claude 源和保存数据，并复用了此前亲自完成的 B02/B10/B11 正反原生审读；没有重新机械扫描全部旧 raw。未验证的仍包括新实现、完整依赖 manifest、实际运行成本与节点状态。只做了读取和已有数据/公式算术，没有新环境、控制器、模型、RF、fit 或 toy 查询。审查总 CPU 没有完整计量，不能写作零。

**MATERIAL_DISSENT: no——针对本次 E/B 与联合窗口三臂两份实际合同的有限完整投资；以上 Gaussian 源语义及 O 失败解释应明确修正。对 Claude 原稿的 7.6 CPUh 直接购买、强制 ×4 和命中率校准链保留实质反对；这些已不是当前两份合同所购买的内容。**
<!-- END B03 INDEPENDENT SELECTION ORIGINAL -->

</details>


<a id="b03-engineering-acceptance"></a>
### B03 implementation, independent engineering disposition and exact inputs — 2026-10-02 UTC

I accept the bounded new package and independently written saved-state reader under
[B03 L0](#b03-l0). The registered Implementer returned worker/task/adapter/ordinary,
configuration/model-factory, trace/evidence and pure tests; I own integration and
`independent.py`. No shared learner, host, launcher or paused Claude asset was edited.
The registered Astra/high engineering Reviewer read the complete implementation,
contract and checks in a separate bounded assignment. It found one P2 accounting
defect: native PPO calls `actor.evaluate_actions` directly, bypassing module forward
hooks, so actor training presentations were absent from the actual forward ledger.
I added a single transparent method wrapper and T×B agent-tick count, with a pure
mock test of argument/return preservation, single invocation and restoration after
an exception. The same reviewer read that repair and returned:

> P2 resolved. The wrapper records each direct PPO actor evaluation once, counts `T × B` contexts, preserves arguments/return values, and restores the original method on exit. The mock test also covers restoration after an exception.
>
> No material finding remains from this review. No additional tests or scientific queries were run; static-read CPU was unmetered.

This technical acceptance does not add a scientific selection, probe or result.
The sparse reward, unclamped original Gaussian, three instances and exposure remain
as selected. Exact direct-PPO contexts are recorded separately from nested module
hooks; summing every nested hook would double-count presentations.

One local construction/serialization pass used the existing CPU runtime, with
three complete model constructions and no environment, policy forward or optimizer.
Complete H/noD initial module+normalizer digests and constructor RNG before/after
were identical; their configuration difference is only disabled discriminator
reward. This checks the factory contract locally, not identical RNG bits across
Torch builds; the admitted worker repeats complete identity checks on its actual
runtime before using the initial-panel alias. Original Gaussian logstd is zero and
no bound/clamp is present. Nominal −20/2 fields remain ignored.

| Instance | Coordinator | Discoverer | Team D | Individual D | Complete retained parameters |
|---|---:|---:|---:|---:|---:|
| H / H-noD | 3,884,366 | 1,053,511 | 415,764 | 455,596 | 5,809,237 |
| SET | 3,877,956 | 1,412,103 | 0 | 0 | 5,290,059 |

SET's constructed coordinator is inactive in its policy/training route. These are
package totals, not matched active capacity. Temporary modules constructed then
replaced are also counted separately in the construction record. The native
factory, learner and normalization sources remain SHA-bound read-only imports.

The ordinary implementation resolves finite-precision input semantics explicitly:
O's matching uses legal held count-state coordinates decoded from float32 to
float64; O/B steering uses each legal current own-observation coordinate decoded
to float64. Neither reads privileged host positions. Reader arrival diagnostics
use a 1 mm tolerance around the frozen slot, record the residual, and retain actual
association/routes/payments; this is not a target, geometry or steering revision.
Current own observations and held global inputs retain their originally different
quantization/order semantics, including off-grid task-clock changes at t125.

Raw mission/rollout evidence is compressed NumPy NPZ with explicit numeric/bool
dtypes and no object arrays/pickle. Full frozen mission state includes original
float64 positions and channels, association/route/transmitter facts, float32 legal
observations/states, raw and host-executed action dtypes, hidden states, original
policy/skill/logprob/value fields and the once-only ledger. Training saves all
positions, associations/routes/masks, actions, reward components and d2 segment
facts, without redundant full training channel/observation arrays. Initial/final
checkpoints use strict complete module/normalizer state and weights-only loading;
configuration, lineage and digest are checked. SHA-bound manifest entries point to
one canonical raw/checkpoint location; no bulk duplication is part of collection.
The separate reader verifies every promised training ledger and all 232 frozen
missions, including all-user censored gaps, neural/ordinary action replay, routes,
physical relations and complete paired outputs. It performs zero native or
optimizer steps. No audit outcome selects whether to continue the fixed panel.

Measured engineering checks total **22.08 CPU seconds**: Implementer pure fixtures
12.57; independent reader fixtures2.85; full three-factory/serialization process
5.14; P2 mock fixture1.52. The underlying records are in
`runs/uav_decision_generalization/b03_engineering_a01/`. There are24 unique pure
tests (35 executions across staged checks),3 actual model constructions,
0 actual policy forwards/native transitions/fits/optimizer steps,1128 synthetic
ledger advances,1444 synthetic O assignment comparisons/80 distances,
4 O and84 B action calls. Fake wiring and 320 mocked PPO contexts are separately
labeled, not scientific exposure. Source reading/editing, hash/publication/node
preparation and static review support were not fully metered and are not zero.
The earlier B01/B02 cumulative question costs remain in their original records;
this ledger starts B03-specific cumulative measured computation, not a reset of
research history or a claim that prior investment disappeared.

Construction scratch `temp/directions/uav_decision_generalization/b03_factory_a01`
was deleted after the factory process ended and identities were saved: allocated
23,531,520 bytes before,0 after, net23,531,520 bytes reclaimed. No engineering
checkpoint copy/backup remains; the compact serialization/digest witness suffices.

[B03_STUDY_INPUT.json](B03_STUDY_INPUT.json) binds the full frozen contract and
all runtime-consumed local source files found through the static import closure,
including every direction package file and the original five host/factory sources.
[B03_INITIAL_LEDGER.json](B03_INITIAL_LEDGER.json) binds22.08 measured CPU seconds
and all prior engineering counters. Actual-node worker/reader use one accepted
handle apiece; canonical worker output is later referenced through a bound locator
inside JSON, not remapped absolute argv. Planned new worker tag is
`b03_joint_window_a01`, reader `b03_joint_window_read_a01`. Forecast remains
18–26CPUh,0GPU and2–4GiB unique new evidence plus roughly1.8GiB input snapshot;
input expansion and complete reader costs remain actual-run uncertainties.
Configured wsl_4070 runtime and8GiB available physical/effective memory plus8GiB
free disk are checked before effects; no node or operation has yet been admitted.

Input hashes: study`1ef2de83078f508afbea8b023bff35fa9bb5587ef176c5e8b138b85182d43783`; initial ledger`800d51f79bad915acf7e26143dc27393c15c28afe3793b9e637512e433c8279e`. Scientific source manifest contains45 files.


<a id="b03-preparation-refusals"></a>
### B03 preparation refusals, before any scientific operation — 2026-10-02 UTC

Exact scientific inputs were published as `300c58af8e5648fb1c98edbd3618f8f964052dda`.
The first remote supervisor task `dmgen-b03-joint-window-a01` terminated before
opening the launcher: `agent-task` joins argv with spaces, so nested `zsh -lic`
argument quoting was lost and an outer `exec` tried `/home/wu/scripts/hmasd_launch.py`.
Its PID1322939 is absent, tmux is absent, and neither a B03 output directory nor
admission claim exists. Preserve null supervisor exit code rather than inventing
one. The corrected invocation passes one already-shell-quoted complete command
to `agent-task`, keeping the whole preparation in the configured `zsh -lic`.

Second preparation `dmgen-b03-joint-window-prep-a02` reached the maintained launcher
and exited4 after7 seconds before source admission/output/claim. I reproduced its
policy-parser error on both current and published RESEARCH: my prior direction
row had omitted its final pipe, causing the Active parser to skip it. This is my
documentation defect, not a pause or changed ownership. Root was already writing
shared RESEARCH, so I requested its one-character row closure without touching
that concurrent edit or changing state/lead. Scientific input bytes remain fixed.
Both preparation failures consumed0native/model/fit/optimizer effects; their CPU
and control-network work are unmetered, not zero. Compact failure facts are saved
in the engineering run directory. No scientific operation has yet been accepted,
and a control repair does not authorize duplicate or additional exposure.


<a id="b03-worker-accepted"></a>
### B03 sole native worker accepted — 2026-10-02 07:40 UTC

Root clarified that the concurrent shared-index writer was the typed-joint DM;
that writer published the single trailing-pipe repair in
`f7522d3cd4e60c3795fcaa5d3d4b34dd54f2b07b`, with no direction state/lead/science
change. I verified the maintained parser now reads lifted/exploring/our stable
lead. This corrects the writer attribution in the preceding preparation note.
The exact scientific source remains `300c58af8e5648fb1c98edbd3618f8f964052dda`.

Third preparation `dmgen-b03-joint-window-prep-a03` completed exit0 after31 seconds;
this is separate from the scientific worker. Native kernel acceptance was
07:40:45.355283UTC on wsl_4070, claim/operation
`/home/wu/projects/HMASD/.git/hmasd-admission/d586acfdbb3862d3afd87e0d601bba0f91f350d860eb29073cea51ac68c87b93.json`.
Supervisor/runner PIDs1324328/1324329 and their boot/start identities are in the
[original manifest](../../../../runs/uav_decision_generalization/b03_joint_window_a01/launch-manifest.json).
Canonical output is
`/home/wu/projects/HMASD/runs/uav_decision_generalization/b03_joint_window_a01`;
immutable input snapshot is `.git/hmasd-launch-sources/728d72485d07492e9ed7caefcf74c5d7`.
The entire preparation used configured zsh -lic; canonical HEAD/sparse selection,
dirty overlay and other live operations were unchanged.

Runner's fresh resource reading had12,622,876,672 available physical/effective
bytes, exceeding the selected8GiB request, with the required free disk. Actual
runtime is NumPy1.26.3/Torch2.7.0+cu118 on CPU,4Torch/1interop/1BLAS thread and
0GPU; no runtime substitution. Config/manifest/preflight were collected with
canonical SHA verification. ConfigSHA256 is
`0bc410effb3e254ea38f5f23186e5ed975a5492251f333ad059c56932e228e88`;
manifestSHA256 `51a801611b40ef8de14bdb197e6afa079f3e444d4efae99aef041377e5e6e6c6`.
No raw/checkpoint bulk was copied.

I armed tools/hmasd_wait.py job `b03-joint-window-a01` under the owned
`temp/directions/uav_decision_generalization/b03_observation/state`, generation1,
60-second read-only status probes and1500-second checkpoint window. First drain
established matching running native identities and no terminal witness; it is
not merely an unobserved registration. The native DM remains active through
same-handle collection and complete reading. At the first collected progress
snapshot the worker had3500 initial-policy transitions,2actual model
constructions and0fit/update; this is progress, not an outcome or selection gate.
The one fixed worker may finish or fail; neither case authorizes an automatic
extra fit or replay of already consumed missions.


<a id="b03-owner-handoff-snapshot"></a>
### Owner-requested in-progress handoff — 2026-10-02 09:47 UTC

At the owner's explicit handoff request, I wrote
[HANDOFF_20261002_JOINT_WINDOW.md](HANDOFF_20261002_JOINT_WINDOW.md), preserving
scientific history, exact accepted identities, latest09:47:05UTC progress,
observer ownership/method, remaining reader/critique/cleanup and frozen boundaries.
This supplementary document is requested by the owner, not a new routine registry
or completion report. H is technically complete and H-noD has26/45 updates;
total601500 native,28913.067836 workerCPU seconds, error null. No full study
reading or independent result judgment exists yet. The same accepted worker and
native DM observation continue; writing the snapshot does not pause, transfer,
terminate, restart or expand this purchase. Later live state takes precedence.


<a id="b03-worker-complete-reader-input"></a>
### B03 full native collection and exact reader inputs — 2026-10-02 UTC

The original source300c58 worker exited0 at11:18:16.154592UTC. Same-claim READY
was drained in observer generation7: terminal witness is valid, original runner
and supervisor are absent, record consistency has no mismatch. I consumed that
terminal event; no worker rearm/restart was performed. The empty observation
controller moved to generation8 awaiting the separate selected reader job.

All3 fits completed45 rollouts each. Native counts are exactly1196000:
1080000 training and116000 frozen; there are135 training rollout files and232
frozen missions in the bound manifest. Actor/critic optimizer steps are303750
each, coordinator1350, team discriminator1350 and individual discriminator5400,
total615600. The direct PPO counter records97.2M agent-tick presentations.
Endogenous labels are720000team and4320000individual across H/noD; H alone
consumes360000/2160000 intrinsic-reward contexts. Host counts2720 resets,
280 constructors,48 unused final-reset world materializations and2392000 original
plus2392000 coupled dense diagnostic entries are retained. NoD still paid its
classifier updates, while its reward forwards were absent as selected.

Worker process self-report is49889.033756CPU seconds,12590.571796wall seconds,
peak2955396KiB,0GPU; cumulative with22.08 engineering CPU seconds is49911.113756s.
The scope excludes the final self-report write/shutdown and does not pretend
unmetered support was zero. Runtime stderr contains only the original singleton
skill-logit std diagnostic warnings from SET's n_Z/n_z1 path; no failed outcome
or nonfinite saved scientific tensor was reported. Complete independent reader
validation and scientific interpretation are still outstanding.

I collected canonical summary223565B, manifest146558B, initial-alias proof64543B
and original terminal witness557B with SHA checks, plus existing config/launch
records. Unique canonical output totals1379496137 logical/1381117952 allocated
bytes in749 files, including734 raw+metadata files and5 distinct checkpoints.
Bulk stayed in its original node location. These are closed writer identities;
the selected reader will independently verify every referenced file and all
promised semantic checks. The compact
[collection witness](../../../../runs/uav_decision_generalization/b03_joint_window_a01/collection.json)
records sizes/hashes and.030385088CPU seconds of metadata collection.

[B03_WORKER_INPUT.json](B03_WORKER_INPUT.json), SHA256
`6b71d289ad964b847c14337ba1c1b61df4f129c342cc1a09aa2f838be28a7e49`,
holds the canonical root and final config/summary/manifest identities. It is an
external-input locator, not a duplicate or snapshot-relative raw location.
[B03_AFTER_WORKER_LEDGER.json](B03_AFTER_WORKER_LEDGER.json), SHA256
`cad8103ca5ac8803b9e687e74f3f8530fba0b448ae7e232e7c41055319355333`,
starts reader measured cumulative CPU at49911.144141088s with all original
engineering/worker counters. This includes measured metadata collection;
publication, control and GC support remain separately unmetered.
All45 scientific source hashes and the study input are unchanged. The next
snapshot may have a newer publication SHA solely to contain these exact reader
inputs. The fixed reader creates no native transitions, training labels or
optimizer updates; its full planned model/ordinary/geometry/ledger readings and
actual CPU still count. Its successful completion, not worker exit alone, is
needed before a complete scientific result.


The maintained snapshot GC preview verified terminal identities, absent live
references, unchanged source, durable Git reachability and external canonical
outputs. Its exact apply removed only
`.git/hmasd-launch-sources/728d72485d07492e9ed7caefcf74c5d7`:
allocated1813323776B before,0after, net1813323776B reclaimed; the target and its
Git worktree registration are gone. No bulk evidence was moved, copied, tarred
or deleted. [Measured GC witness](../../../../runs/uav_decision_generalization/b03_joint_window_a01/worker-snapshot-cleanup.json).
This releases the previous input snapshot before creating the new reader snapshot;
all canonical result evidence and admission/exit records remain. A final local
source-manifest comparison confirms all45 scientific files still match the
worker input exactly. Cleanup of this disposable source does not turn native
completion into a scientific result or release required unique evidence.


<a id="b03-reader-accepted"></a>
### B03 exact complete reader accepted — 2026-10-02 11:54 UTC

Exact reader inputs were published in `4fe4d7b10d28184c25590d5448f7c6eae5100880`;
all45 scientific sources remain worker300c58-identical. The configured supervisor
preparation `dmgen-b03-joint-window-read-prep-a01` completed exit0 after31s.
The original selected reader was accepted at11:54:30.485075UTC, operation
`/home/wu/projects/HMASD/.git/hmasd-admission/3c2304fb1119d6da9ad827bbe006fbd4aa12841e59fecd5f1c4eac416a719401.json`.
Its native supervisor/runner are1338532/1338533 with original boot/start identities
in the manifest; canonical output is
`/home/wu/projects/HMASD/runs/uav_decision_generalization/b03_joint_window_read_a01`,
source snapshot `.git/hmasd-launch-sources/89f42cc796054e9883dbaafc384af1ec`.
Fresh available physical/effective RAM15330312192B passed the selected8GiB request.
Runtime, information, exposure and all input identities are unchanged. ConfigSHA
`f64dac6b3edc33e902e3710efe3d2aa4c09b470c7c540ecc1781d0c97435f253`
and compact acceptance files were collected and verified against canonical bytes.

I added exactly this read-only status job `b03-joint-window-read-a01` to the
original observer state, generation9, and drained actual running/consistent facts.
The completed worker job remains terminal; no relaunch or duplicate reader exists.
Initial reader progress checked all135 training rollouts/1080000 training ledgers
and6480000 UAV movement ticks in44.539615CPU seconds before entering the frozen
mission reconstruction. Frozen models/physical checks, complete scientific
reading, independent diagnosis and final retention remain outstanding. This
is still progress, not a completed scientific verdict.


<a id="b03-reader-failure-and-repair-l0"></a>
### B03 reader failure, reproduced arithmetic cause and bounded completion L0 — 2026-10-02 UTC

The original worker remains complete and unchanged. Reader `read_a01`, source
4fe4d7b10, exited1 at12:05:51.106813UTC during O/world109220001's movement check,
with exact-array maximum difference2.220446049250313e-16. All135 training rollouts
and167 frozen missions already have durable completed check files: these include
all166 neural missions/83000 model-team forwards plus O/world109220000. The
failure occurs before service, reward or physical reconstruction of the next O
mission. There is no final reading yet. Original summary/exit/status remain under
`runs/uav_decision_generalization/b03_joint_window_read_a01`; failed CPU is
2396.885812s, cumulative52308.029953088s, wall659.753977s, peak719600KiB. All actual
forward/check counts remain charged. Consuming the generation9 BLOCKED event
advances observation to10 without resuming either terminal job.

[Saved-raw reproduction](../../../../runs/uav_decision_generalization/b03_engineering_a01/motion-failure-reproduction.json)
used the original node/runtime and O/world109220001 bytes. At action10/UAV5,
`[.6478229245445858,-.7603696056554017,.04651366713073793]`, a large-array row
view gives norm1.0 whereas its independent copy gives1.0000000000000002. Both
are float64/stride8; their addresses have different alignment. The original host
and recorder each copy the three-vector before norm; the reader retained a view.
Copying each row reproduces all saved executed commands and successor positions
exactly (zero error). This is an actual saved-byte reproduction, not an inference
that generic vectorization changes the sum. Measured repetition cost .013453583
CPU seconds; the first identical read-only invocation lost its stdout because the
local destination directory was mistyped, so its CPU is unmeasured and retained
as support cost, not zero. Neither invocation constructed an environment/model,
queried RF nor advanced a controller.

**L0.** Deliver one read-only completion of the originally selected reader over
unchanged worker evidence. Owned changes are the B03 reader's per-command copy,
explicit SHA-bound reuse of its135+167 completed check files, and focused tests;
no worker, host, learner, task, seeds, model, tolerances or service/payment rules
change. The exact old reader failure/source/summary and every reused check hash
are inputs. Only reader entry/reconstruction/prefix-loading source may differ;
all other worker source bytes must match. Recheck repaired movement arithmetic on
every reused raw mission, and verify its raw/metadata/check identities; no neural
or training check is counted as newly executed. Check the remaining65 ordinary
missions fully, then produce the original full232/2160-mission reductions and
coverage accounting. This combines certified read coverage, not partial native
runs or a resumed fit.

New effects are0 native/fit/optimizer/model-forward. Residual ordinary work is
195000 command reconstructions,32565 physical states/10453365 distance relations,
32500 ledger advances/1625000 user indicators,195000 movement UAV-ticks; repeated
prefix movement costs6981000 UAV-ticks separately. Completed-prefix counts stay
separate from new counts and are combined only for full promised coverage.
Expected additional reader CPU is1–4minutes; engineering/review/support actuals
are added, with no automatic retry on another failure. Preserve original failed
outputs, check the numerical/identity diff with the existing independent
engineering reviewer, publish exact completion inputs, use fresh actual-node
admission, and retain same-handle observation. This repair creates no new
scientific comparison or additional selection gate.

The narrow repair is now implemented. All unchanged43 worker files remain
identical; only `independent.py`, `run.py` and new `reader_prefix.py` differ, with
exact before/after hashes in [B03_READER_PREFIX.json](B03_READER_PREFIX.json).
The new [completion study input](B03_READER_COMPLETION_INPUT.json) pins46 source
files and the unchanged scientific contract. The prefix locator binds every one
of302 old check files (16440026 logical bytes) at its original canonical location;
there is no copy of the bulk output. Every reused raw movement is rechecked,
while old neural/physics/reward checks keep the old source identity. No ULP or
other tolerance changed. The failed ordinary mission is among65 fully unchecked
missions to be read under the corrected arithmetic.

Focused tests13/13 passed, including an owned-copy norm regression, strict
one-ULP rejection, complete prefix roster/hash/source/cumulative-cost rejection,
and separate movement accounting for both recorded dtypes. Tests used1.62CPU
seconds/.70wall seconds and55116KiB peak, no scientific forward/native/update.
Metadata collection used.024476030CPU seconds. The
[after-failure ledger](B03_AFTER_READER_FAILURE_LEDGER.json) starts at
52309.687882701 measured cumulative CPU seconds, retaining all worker and failed
reader counters. Source authoring, engineering review, publication/control and
the first lost-output diagnostic have unmeasured support cost, not zero.

**Original independent engineering increment review**, existing registered
Astra/high `/root/dm_decision_generalization/review_ar_engineering`, read-only:

> No material finding remains in this bounded increment.
>
> - Per-vector copying matches the host’s arithmetic without loosening equality.
> - Reuse binds the failed reader, all 135+167 completed checks, and unchanged raw/metadata identities. Source exceptions are limited to the three reviewed reader files.
> - Reused coverage plus 65 new ordinary checks matches the original totals. The 6,981,000 repeated movement checks are counted separately; failed-reader counts and CPU remain in cumulative cost.
>
> I inspected the existing tests, reproduction record and failed-reader summary. No tests, model/native/RF calls or launches were performed. Static-read CPU was unmetered. Final locator hashes remain for DM publication verification.

**DM disposition:** accepted after reading the diff, test output and actual
saved-byte reproduction. Exact old source and failure are preserved; the change
repairs the reader's copy semantics, not the worker, numerical scientific rule
or comparison. Publish these inputs and admit one read-only completion. Another
failure returns to its actual evidence rather than licensing a native retry.


<a id="b03-reader-complete"></a>
### B03 complete saved-data reading — 2026-10-02 12:38 UTC

The first completion preparation stopped before admission when a lazy Git
commit-object check timed out after30s. The exact published source was then
fetched through the configured whole-command `zsh -lic`; the second preparation
repeated the same unaccepted request, with no code/input/output change. Its
[zero-effect refusal](../../../../runs/uav_decision_generalization/b03_engineering_a01/completion-preparation-a01.json)
is retained. Remote automatic-GC stderr also reported an existing bad-tree/repack
warning; fetch itself exited0. I did not change the canonical checkout, sparse
selection, Git history or shared runtime.

The one completion reader was accepted at12:36:34.195198UTC, source
`2056aa1fa12cab3cb42fae13f495fad54422b1a6`, operation
`/home/wu/projects/HMASD/.git/hmasd-admission/75c596fb189b0d94432f813b52d1a21474e1d836fd539100b214d97340655a66.json`,
canonical output
`/home/wu/projects/HMASD/runs/uav_decision_generalization/b03_joint_window_read_a02`.
Its supervisor/runner1340545/1340546 are now absent with consistent valid exit0
at12:37:28.537646UTC. Source snapshot is
`.git/hmasd-launch-sources/1bc44712a941417aa1cb34de52b600d5`.
Original observation was armed/drained at generation11; its READY was consumed
into12 without resuming either terminal reader or the worker.

All135 training rollouts/2160 training missions and232 frozen missions now have
complete verified coverage. The published
[reading](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/reading.json)
is1567197B/SHA256`eab3cdeff541f4849f6086e5752d0ea9ad59b6e29ab7765a9b047bce5d356c69`;
[summary](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/summary.json)
is51501B/SHA256`968f1f5458dee44ad7d93010a155eadf35719eac167e80d7644eaca47929d15d`.
Original302 prefix checks remain in `read_a01/checks/`;65 new ordinary checks
remain in `read_a02/checks/frozen/`. The reading binds their old/new source and
raw identities; no duplicate canonical raw, checkpoint or old check copy was made.
All6981000 reused UAV movement ticks passed exact copied-vector reconstruction.
The original equality rule remains: no movement, service, route or payment
comparison was relaxed. Both full initial audit traces agree on every saved field.

New counts exactly match the declared remainder:32500 ledgers,1625000 user
indicators,195000 movement UAV-ticks,32565 physical states,10453365 distance
relations,96000 O/99000 B commands,23104 matching comparisons and1280 matching
distances. The original failed reader's83000 model-team forwards/498000 actor
and critic rows remain the only neural replay. This completion has0 new model,
native, fit, optimizer or discriminator queries. Combined coverage satisfies all
original complete-reader count assertions; repeated prefix movement is separately
charged, not substituted for new native data.

Completion CPU50.777541s, wall51.117571s, peak437624KiB,0GPU. Its terminal summary
cumulative is52360.465423701CPU seconds; subsequent compact collection used
.002290127s, making52360.467713828s (14.544574365h) measured B03 cumulative so far.
This includes the failed reader, engineering/tests and measured collections;
self-report excludes its last write/shutdown, and authoring/review/control support
is unmetered. The earlier forecast18–26CPUh was a prediction, not a hard cap.
Worker1196000 native/3fits/615600optimizer remain unchanged. Complete independent
scientific diagnosis and DM result interpretation/cleanup follow below; exit0
alone is not the final scientific disposition.


<a id="b03-complete-reading"></a>
### B03 DM complete scientific reading — 2026-10-02 UTC

**The three trained instances do not establish useful acquisition of this joint
window task. The constructive result is a strong lawful ordinary programme:** O
completed all128/128 fresh windows, while H/H-noD/SET final completed5/6/4.
The favorable H-over-noD prediction was not met. The fixed purchase is complete;
this result does not automatically buy another seed, longer fit, entropy/head
change, reward weight, easier geometry or teacher intervention. The broader
learned-decision question and earlier R/S capabilities remain open. This is my
own full reading before receiving the final independent result diagnosis below.

I read the complete final reductions, all135 training-curve entries, every main
endpoint's four window records and all primary/initial/final comparisons. The
reader verified all232 frozen and2160 training missions; I additionally read70
complete saved native trajectories across ten informative positive/adverse/zero
worlds, all seven distinct programmes, with source-bound masks, payment timing,
positions and full routes. These are selected examples, not a second endpoint
panel. Their [compact factual extracts](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/dm-native-cases.json)
bind the unchanged original raw SHA for each episode. This extra saved-data read
used.294578266CPU seconds,0model/native/RF/optimizer calls; measured B03 cumulative
is now52360.762292094s (14.544656192h), with unmeasured support kept separate.

#### Complete task and individual-service outcome

All numbers below average the same32 fresh worlds for the frozen deployable.
Path is per-UAV metres over500ticks; the gap is each user's longest absence,
including first/last censoring, then averaged over all50 users and worlds.

| Programme | W /4 | Backhauled user fraction | Dense diagnostic J | Never served /50 | Mean user longest gap | Team-zero ticks | Mean path m |
|---|---:|---:|---:|---:|---:|---:|---:|
| H initial (=noD initial) | .15625 | .16843 | .10527 | 37.000 | 405.076 | 116.281 | 13551.0 |
| H final | .15625 | .14971 | .09312 | 35.844 | 411.833 | 158.344 | 13899.4 |
| H-noD final | .18750 | .15219 | .09558 | 35.750 | 410.802 | 145.406 | 14020.6 |
| SET initial | .06250 | .16019 | .10205 | 37.688 | 405.534 | 121.000 | 13560.9 |
| SET final | .12500 | .14523 | .08921 | 35.750 | 411.644 | 150.156 | 13732.4 |
| Sticky B | .34375 | .21545 | .13800 | 15.719 | 326.519 | 38.906 | 9294.9 |
| Scheduled chain O | 4.00000 | .72364 | .45122 | 0.000 | 129.089 | 2.688 | 2208.2 |

All28 pairwise comparisons, every world value and tails remain in the reading;
this table does not replace them. O satisfies the declared score ceiling on this
panel with substantially shorter travel, but it is not a global path optimum or
a real-world energy/safety result. It serves every user sometime, not all50 users
continuously: its mean world maximum same-user gap is364.34375ticks and its mean
p90-user gap361.846875. The first pair intentionally leaves the first cluster at
t130, consistent with a once-only four-window contract. Keep those censored tails
when transferring its capability to a different service objective. Learned finals
have a500-tick worst-user gap in every world. Secondary dense J was never a
learning reward and is not the purchased primary endpoint.

For H-final minus H-noD-final, mean W difference is−.03125 with conditional
paired t95(df31)[−.225176,.162676], wins/losses/ties4/5/23. H-final minus SET-final
is+.03125 [−.113093,.175593],3/2/27. The final-minus-initial W differences are
H0 [−.158616,.158616], noD+.03125 [−.139692,.202192], SET+.0625
[−.064970,.189970]. These intervals describe new-world variation conditional on
three particular fits;32 worlds are not32 learning replications. They do not
establish equivalence, an algorithm ranking, or that no amount/type of learning
can solve the task. Each final has only0–1 payment per mission, whereas O has4.
The useful conclusion is failure of this finite original-recipe acquisition
purchase to produce a competitive complete deployable, including against the
weakly informed but persistent B. Rare locally favorable worlds are retained.

#### Opportunity, exposure and actual learning movement are distinct

The ordinary opportunity is now measured, not just an analytic ray-chain claim.
O's first payment action ranges27…104; its second/third/fourth payments are
always144/269/394, with at least8 users served from each later window's first
tick. Native association and BFS paths confirm actual multihop service. Thus
neither absent joint opportunity nor an unattainable20-tick rule explains this
panel. The full map/schedule and held snapshots were supplied and replay-checked
according to each native programme's actual input routing. This is not the toy
clock/reward flow, an off-policy label fit or an actor granted private ledger/ACK.

All three learners encountered real successes while training: H62 completed
windows across59/720 missions, noD71 across71/720, SET62 across61/720, each from
2880 possible training windows. H and SET each reached2 in at least one training
mission. The low external reward, d2 segment-discounted external-only high
reward, episode terminal masks and retained noD discriminator updates all passed
saved-data checks. No assertion that the learner received zero positive rewards
is tenable. Conversely, these sparse encounters are not evidence of sufficient
credit or systematic exploration. Nine-rollout-block mean W for H is
.0833/.0694/.0764/.0764/.1250, noD .0972/.0903/.0903/.0833/.1319, and SET
.0972/.0694/.0903/.0903/.0833; changing training worlds are not a fixed diagnostic
panel. There is no sustained broad competence hidden by the endpoint.

The parameters moved substantially and optimizer steps occurred. Final relative actor
L2 motion is .997/.981/1.121 for H/noD/SET, critic .981/1.134/.692; H/noD
coordinator .0626/.0681 and SET's inactive coordinator exactly0. This was three
completed fits, not a frozen-weight or missing-update failure. All615600
optimizer steps and original classifier exposure remain charged. H/noD's exact
initial alias is established by complete state/RNG/input identities plus the
full audit, not by equal aggregate outcomes.

The more specific native deficit is usually **reaching a qualifying joint
configuration at all**, not merely holding19ticks instead of20. Of128 final
windows, H121, noD120 and SET120 never reached8 active backhauled users even once.
H has no unpaid≥10-tick near-miss; SET has two11-tick runs. This rejects a
sustain-only summary while leaving geometry, exploration, representation and
credit/optimization as competing, unseparated contributors.

#### Positive and adverse native examples

- World109220016: H-final pays at action269 in window2/cluster0; its initial,
  noD-final and SET-final pay0. Users10…19 all persist for20ticks. The complete
  recorded route through UAV1→0→BS is real joint service; H covers20 users
  sometime versus initial/noD10. It is a preserved local gain, not proof of
  generalized schedule following: H still has30 never-served users, while O
  completes all four windows and serves all50.
- World109220002 reverses the reward-intervention story: H-final never serves a
  scheduled cluster, whereas noD-final pays at222 for cluster0 through the
  multi-UAV0→1→3→BS route. Both have substantial other missed service. The two
  examples prevent a claim that discriminator reward is uniformly helpful or
  uniformly destructive.
- World109220028 is a flat-policy positive and H adverse: SET-final reaches
  cluster2 and pays at240 with route0→5→1→BS; H-final serves no user throughout
  the mission. O moves out of the same initial zero-service state and completes
  all four. Initial geometry is not a universal doom condition.
- World109220020 already offers early cluster0 service to initial policies.
  H-initial pays at37; H-final and SET-final at19, noD at37. H-final's qualifying
  segment retains eight identical users, but every learned programme misses the
  remaining three windows. Faster payment in this favorable start must not be
  mistaken for learned whole-schedule planning.

The payment rule allowed different eight identities, yet the independent raw
reconstruction found all161 main paid segments (including initial/ordinary)
contained at least eight same identities throughout their20ticks. My selected
raw examples agree. There is no observed payment exploitation by rapidly
rotating recipients; all-user tails still expose the much larger continuity
shortfall outside those successful segments.

#### Explanation update and next investment boundary

The original unbounded Gaussian entropy rises on all44 successive update
intervals in every fit: H4.326→8.089, noD4.325→9.344, SET4.356→9.205. Final
clipped UAV-tick means are2990.19/2996.28/2995.53 of3000, up from about2406/2412
at initialization. The independently reported final raw norm means about
6.84/9.67/8.72 are consistent with the saved trajectories I read. Original code
rewards raw Gaussian entropy before the host's radial projection; the nominal
logstd bounds do not apply. This is a consequential shared observed pathway and
an alternative to a hierarchy-only explanation. It is **not an identified common
cause**, proof of incorrect PPO likelihoods, or evidence that a bounded head,
entropy change or a longer fit would improve native W.

H's mean weighted discriminator components are around−.057 per low-level step
late in training while its rare external component is about.0000625; the native
value estimate follows that different mixed target. Those means alone do not
quantify gradient dominance or causal harm. Removing the discriminator reward
was actually tested here and did not rescue complete capability. The failure
cannot be assigned solely to discriminator distraction, and the near-initial
SET/noD endpoints do not show that hierarchy is the distinctive obstacle.

I end the **unchanged three-fit B03 purchase** and retain the ordinary solver,
explicit registered-window benchmark, source-bound rare multihop successes and
all adverse trajectories. I do not adopt any learned final for this task. R's
limited learned decision generalization and S/Bstar's earlier conditional service
uses are not refuted by these different native PPO instances. The broader goal
is still learned decision capability, not endlessly repairing this particular
Gaussian/task combination. A raw-entropy/action-contract explanation could be a
future explicit hypothesis only with a predicted native consequence and an
ordinary/alternative comparison; it is not automatically selected by the visual
symptom. Likewise imitation of a cheap solver is not automatically worthwhile
merely because O now supplies a positive target.

At this handoff boundary no new effect is selected. Root's pending cross-question
allocation may compare a direct acquisition revision, development of retained
positive assets, or leaving this purchase closed; it does not delay publication
or make an idle direction a technical dependency. Any successor must inherit the
actual3-fits/1196000-native cost and the prior A/R and S/C costs, identify what
new capability/understanding it could establish, and receive its applicable
scientific selection. No new architecture, proof, calibration or mandatory pilot
is implied. The independent critic's final judgment and my response are retained
in the next entry rather than replaced by this self-reading.

**Explicit inherited action/entropy counterevidence.** Before any successor
investment, retain the already-published Claude comparisons at
[`coupled_host_joint_skills_stage1/NOTES.md`](../coupled_host_joint_skills_stage1/NOTES.md),
2026-09-29 17:20/18:07 and2026-09-30 01:39, with the02:56 corrections.
SET-V-b (`b02_fit_SETVb_932201_a01`, source889a7e28e) used the native tanh head,
logstd−1/clamp[−5,0]; deterministic clipping fell from about2819 to.5 UAV-ticks,
yet backhauled coverage was.2099 versus the original matched SET.2187. SET-T-b
(`b02_fit_SETT_932201_a01`,186b8649e) used a10-tick absolute-target/straight-line
executor package and reached.3571 versus its random-target floor.3652.
SET-T-b′ (`b03_fit_SETT_932201_a01`,76d5d514b) removed only low entropy bonus
within that macro/bounded package: sigma fell .368→about.20, but coverage.3496
and paired difference−.0075 (SE.0140) did not establish useful recovery. Those
scoped costs3.26/1.07/1.79CPUh and earlier failures remain inherited investment,
not new B03 costs or secretly repeated experiments. The later accepted correction
matters: lower sigma is lower noise scale, not lower precision; logged entropy0
was a reporting branch; far-target rate does not prove the mean unused; shared
reward was not identified as the cause. These were different dense-task/endpoint
contracts, so they do not empirically refute a properly specified B03 successor.
They do refute describing bounded actions, entropy removal or waypoint control
as an untried obvious repair. No paused Claude asset or standing is changed here.


<a id="b03-independent-result-review"></a>
### B03 independent result diagnosis — complete original, 2026-10-02 UTC

Root reused the one applicable ResearchCritic `/root/next_study_review`, UUID
`01a0f9fe-de22-7d73-82c2-129a0cadede6`. This is independent scientific reconstruction
with previously loaded comparison context and received status messages, not a
blind review. It first read original worker/source evidence, then the complete
reader, and only then compared my published `e5c56a80` explanation. No second
result critic was commissioned. Root read and accepted the following complete
answer; I have read it in full and respond immediately below.

Mechanical provenance: session
`/mnt/c/Users/fires/.codex/sessions/2026/10/01/rollout-2026-10-01T17-23-45-01a0f9fe-de22-7d73-82c2-129a0cadede6.jsonl`,
actual turn `01a0fc74-3b8a-7213-a0bd-467a95dc6031`; line2311 `turn_context`
verifies `gpt-6-astra/max`, line2653 `task_complete` at
`2026-10-02T13:05:42.675Z` contains this unchanged15010-byte UTF-8 answer,
SHA256 `35dba162884c32733abdf7e43367ab15c8186413f7869763325c0f3caf77988e`.
[Compact provenance](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/independent-result-review-provenance.json)
retains source-line hashes and the actual runtime fields. Original path/line
citations inside the answer retain the critic's then-current location.

<!-- B03 ORIGINAL RESULT CRITIC BEGIN -->
建议结束原样 H/noD/SET 的 B03 投入，不采用三个最终学习策略；保留 O 的完整联合窗口能力、学习轨迹中的真实多跳正例，以及此前 R、S0/S1 的条件能力。当前证据支持这一处置，不能支持“联合服务不可学习”或“已找到共同失败原因”。

本轮复用既往选题与结果审阅背景，收到过 Root/DM 的状态消息，**不是盲审或全新隔离上下文**。我先重建冻结源码、worker 端点和原生轨迹，待完整 reader 返回后核对，再读 DM 的 `e5c56a80` 解读。

**1. 结果已完整闭合，原读取失败仍是证据的一部分。**

科学 worker 源为 `300c58af8e`，完成三次各 45 rollout 的拟合、1,196,000 native steps、615,600 optimizer steps、135 个训练 rollout、232 个冻结 mission 和五个独立 checkpoint。原 reader 在 O/world `109220001` 的动作精确比较处失败，差值为 `2.220446049250313e−16`。

我读了原失败记录、保存数组复现和 `2056aa1fa` 的完整修复差异。原宿主先复制单条三维动作，旧 reader 使用大数组行视图；其范数分别落在 `1.0000000000000002` 与 `1.0`，跨过严格 `>1` 分支。修复只增加单条动作复制，未放宽容差、服务门槛或支付规则。

最终 reader 绑定旧 302 个检查文件，重新精确核对全部旧 movement，再补齐 65 个普通程序任务；没有重复模型或科学运行。最终 [reading.json](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b03_joint_window_read_a02/reading.json) 的 SHA 为 `eab3cdeff541f4849f6086e5752d0ea9ad59b6e29ab7765a9b047bce5d356c69`。我核对了该身份、46 个源文件 hash、旧检查 hash，以及完整检查中的数值差异。232 个冻结任务的输入与 SINR 重建误差、166 个神经任务的动作/hidden/value 重放误差均为零。训练部分按合同核查保存 ledger、输入和回报，没有重新进行完整 RF 重算。

因此，修复后的读取足以承载本次科学判断；不能删除原失败，亦不能把修复解释成改变科学容差。[原失败与修复边界](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:3824)

**2. 普通 O 获得完整能力；三个学习实例没有建立自身任务收益。**

下表均来自相同 32 个冻结评价世界。成功窗总数的分母为 128；路径按每架 UAV 计；用户缺口包括首尾删失。

| 程序 | 成功窗/128 | 平均回程服务用户数 | 从未服务用户/50 | 每用户最长缺口均值 | 路径 m/UAV |
|---|---:|---:|---:|---:|---:|
| H 初始＝noD 初始 | 5 | 8.421 | 37.000 | 405.076 | 13,551 |
| H 最终 | 5 | 7.486 | 35.844 | 411.833 | 13,899 |
| noD 最终 | 6 | 7.609 | 35.750 | 410.802 | 14,021 |
| SET 初始 | 2 | 8.010 | 37.688 | 405.534 | 13,561 |
| SET 最终 | 4 | 7.261 | 35.750 | 411.644 | 13,732 |
| Sticky B | 11 | 10.773 | 15.719 | 326.519 | 9,295 |
| Scheduled O | **128** | **36.182** | **0** | **129.089** | **2,208** |

主要配对量，以每 mission 完成窗数 \(W\) 为单位：

| 比较 | 平均差 | 条件配对 t95，df31 | 升/降/同 |
|---|---:|---:|---:|
| H 最终 − noD 最终 | −0.03125 | [−0.22518, 0.16268] | 4/5/23 |
| H 最终 − SET 最终 | +0.03125 | [−0.11309, 0.17559] | 3/2/27 |
| H 最终 − H 初始 | 0 | [−0.15862, 0.15862] | 3/3/26 |
| noD 最终 −共同初始 | +0.03125 | [−0.13969, 0.20219] | 4/3/25 |
| SET 最终 − SET 初始 | +0.06250 | [−0.06497, 0.18997] | 3/1/28 |

三个最终策略每个 mission 最多完成一窗，O 在全部世界完成四窗。上述区间均条件于各自这一次拟合，不能把 32 世界当作训练复制，也不能据跨零建立等效性。

次要 dense J 的最终均值为 H `.093123`、noD `.095584`、SET `.089209`，各自低于初始化均值；这些自身差异的区间仍跨零。相对 B，三个最终策略的 J 和平均服务均有负向条件区间，同时从未服务用户、用户最长缺口和路径明显更差。B 是具有目标持续性的普通移动程序；它提供的竞争解释比“网络有没有更新”更有分量。

自身路径变化则较明确：H `+348.36 m`、noD `+469.60 m`、SET `+171.47 m`，三个配对区间均为正。增加的运动没有兑现为完整任务收益。这里没有能耗模型，不能把路径直接换算成能量损失。

我从完整冻结端点独立复算了 **28 对 ×26 个标量＝728 组成对世界向量、均值、标准误与符号计数**，均与最终 reader 一致。

**3. O 证明了合法普通方法的完整用途，也暴露了本任务的边界。**

O 使用公开注册表、完整日程和合法位置输入，通过初始匹配、三对射线站位及 t130 的一次改派完成任务；没有查询私人支付 ledger 或未来服务真值。学习程序也得到公开注册表与日程，但各自的信息路由、表示和计算程序不同，不能称为架构因果控制。[任务与输入](/home/fires/hmasd-wsl/experiments/candidates/uav_decision_generalization/b03_joint_window/task.py:1)、[O 的源码](/home/fires/hmasd-wsl/experiments/candidates/uav_decision_generalization/b03_joint_window/ordinary.py:21)

保存轨迹显示：

- O 第一窗支付 action 在 27–104 之间；后三窗全部固定在 action 144、269、394 支付。
- 后三窗各自全部 125 tick 都达到至少八名活动用户的回程服务。
- 所有 128 个实际站位到达记录均存在，原生关联和多跳路径支持这些支付。

这将“存在联合机会”落实为完整普通程序能力，削弱了任务不可达、窗口太短或缺少合法任务信息的解释。

同时，O 的世界最大同用户缺口均值仍为 **364.344 tick**。第一对 UAV 按合同离开首簇，完成一次支付后可以长期不再服务该簇。O 实现了本合同的四窗目标及全用户至少一次服务；它没有建立全体用户持续连通，也没有建立全局路径最优或能源安全。

O 已达到这个面板的任务分数上限，而且计算便宜。由此购买一个“模仿 O”的新拟合，需要另有可检验用途；不能仅因教师正确就推定压缩学习值得投入。

**4. 本批存在真实学习过程和局部正例，尚未形成可复用的联合控制能力。**

三臂训练期间分别获得 H **62**、noD **71**、SET **62** 次真实窗口支付，来自 720 个训练 mission/臂。H 和 SET 各有两窗成功的训练轨迹。优化确实发生，参数明显移动；这不是零正奖励、冻结权重或缺失更新导致的伪阴性。

但几乎所有未成功窗口连联合服务门槛都没有到达：最终 H/noD/SET 的 128 窗中，分别 **121/120/120 窗从未出现一次 \(q\ge8\)**。主要缺口发生在形成合格联合配置之前；“只是坚持不到第 20 步”不是合适的主解释。

我直接读过的原生正反例包括：

- **109220007，H 的局部正面。** H 初始和 noD/SET 最终都没有支付，H 最终在 action149 完成一窗，十名同身份用户持续服务，通过真实多 UAV 路径回程。但其 team-zero 从初始的 0 增至 115 tick，仍有 30 人从未服务。局部窗口收益伴随别处服务损失。
- **109220026，新增远簇服务。** H 初始没有远簇回程服务；H 最终增加真实远簇服务并在 action111 完成一窗。从未服务人数由 40 降到 30。O 同世界完成四窗。
- **109220004，明显自身退化。** H 初始完成一窗、平均服务 16 人；最终没有支付、平均服务仅 1.154 人，team-zero 达 429 tick。
- **109220029，能力丢失及身份差异。** SET 初始在第四窗成功，最终丢失该成功；noD 最终在第三窗服务另一簇并获得支付。相同总窗数或新增一次支付，不代表同一批用户的连续性改善。
- **109220000，完整负例。** SET 最终移动约 12.3 km/UAV，却全 500 tick 零服务、50 人从未服务。O 在相同世界完成四窗，B 也完成一窗。

一个应保留的正面细节是：虽然支付规则不要求固定的同八人，我重建的 **全部 161 个 main 支付段**实际上均含至少八名同身份用户连续服务 20 步。没有观察到通过快速轮换受益者取得支付的现象。这不能替代成功段以外的完整用户缺口。

这些例子证明拟合后的策略有真实、改变过的联合服务行为；初始策略和 B 也会产生此类事件，完整配对结果尚不能把它们提升为可靠的任务学习增益。

**5. 判别器比较比“共同初始化”更扎实，但其支持范围仍有限。**

我另核对了 H/noD 的 **45 个 `pre_rollout_rng` 完整保存状态，全部严格相同**，训练起始 RNG 也相同；SET 的训练 RNG 不同。H/noD 第一整个 rollout 的动作、位置、技能和支付相同，其低层奖励不同。

因此，H−noD 是一个有效的单次配对训练干预：noD 保留分类器训练，只移除判别器奖励。不能以“H/noD 随机流已经不同”解释结果。更新后的策略和经历不同是该干预的后果；这仍不识别固定同历史下某个技能或分类语义的独立贡献。

源码与保存回报确认：

- 外在奖励为真实窗口支付的 `R/6`。
- d2 高层使用段内折扣外在回报，再按实际段长跨段折扣。
- 判别器奖励进入低层，noD 的分类器更新和费用保留。

H 没有建立优于 noD 的任务收益；noD 也没有恢复完整能力。较大的负判别器奖励均值不能直接推出梯度支配或共同失败原因。分类准确率、标签熵和参数运动也不能替代功能性技能证据。

**6. 动作尺度是承重线索，历史反证禁止把它写成确定修复。**

三臂训练的 raw Gaussian entropy 在全部 44 个相邻 rollout 变化中都上升：

- H：4.326 → 8.089；
- noD：4.325 → 9.344；
- SET：4.356 → 9.205。

最终原始动作范数均值约为 6.84/9.67/8.72，clip 事件约为每 3,000 个 UAV tick 中的 2,990/2,996/2,996。源码中的 Gaussian 未应用名义 logstd clamp；熵项作用于投影前分布，宿主随后做单位球投影。[Gaussian 实现](/home/fires/hmasd-wsl/hmasd/r_mappo_utils.py:73)、[训练熵项](/home/fires/hmasd-wsl/hmasd/agent.py:6860)

这是一个具体的训练目标与执行行为关系：增大原始尺度可以增加原始分布熵，而执行幅度已经基本饱和。现有证据没有证明 PPO likelihood 错误，也没有证明该现象导致了全部服务失败；几何计算、表示、信用分配及有限优化仍未分离。

我按 DM 提示直接补读了旧 coupled-host 的配置、完整 holdout panel 和修订记录：

- 有界速度 SET-V：确定性覆盖 `.209905`；
- 目标点 SET-T：`.357105`；
- 去熵 SET-T：`.34956375`，相对原 SET-T 为 `−.00754125`。

旧任务中，动作约束或噪声尺度确实改变过，服务没有因此成为强能力。尤其旧记录已纠正“σ 下降证明均值不会利用精度”的过强解释。这些旧结果不能替代新 B03 的反事实，但会降低“换有界头、去熵或改目标点就能修复”的投资依据。[旧配置及端点](/home/fires/hmasd-wsl/runs/coupled_host_joint_skills_stage1/b03_fit_SETT_932201_a01/panel_45_holdout_deterministic.json)、[历史更正](/home/fires/hmasd-wsl/docs/research/candidates/coupled_host_joint_skills_stage1/NOTES.md:1995)

**7. 投资建议：当前零新增运行；保留一个明确、可放弃的模型复用问题。**

我赞同 DM 结束本次原样三配方投入、不采用最终策略、保留 O 与完整正反资产的处置。没有理由自动追加种子、延长训练、改奖励尺度或安排熵/动作头扫描。先前 R 的有限泛化、S0/S1 的条件服务能力不受这组三个不同任务的 PPO 实例否定；不同任务的 J 不横向排名。

若 Root 仍希望从本批已付模型中购买一个最小后继观察，较有区分力的候选是：**只比较冻结 SET 初始与最终的确定性均值执行，完整读原 32 世界，并复用既有 O/B 和 sampled 端点作参照。**选择 SET 可避免同时更改高层技能采样；这是新增执行程序的开发性比较，不能回写原 sampled 主结果。

其结果会改变不同判断：

- 最终均值明显优于初始均值，并有完整服务用途：保留“已学到部分均值控制、原采样执行未兑现”的有限资产。
- 初始和最终均值共同提高，二者没有训练增量：优先解释为普通执行方式收益。
- 两者仍弱：降低继续挖掘这两个 checkpoint 的价值，不自动接动作头 fit。

核心费用为 **0 fit、64 个 H500 mission＝32,000 新 native steps**；完整 reader、工程审计和支持费用尚未闭合。这只是值得比较的候选，**不是本次选中的运行，也不是其他研究必须经过的诊断门槛**。结合旧确定性端点的负证据，保持 B03 无后继运行同样合理；我不建议现在购买新训练。

**8. 实际价格与我的检查边界。**

截至 DM 完整自读，B03 累计显式计量为 **52,360.762292094 CPU-s＝14.544656 小时，0 GPU**，包括：

- worker 49,889.033756 CPU-s；
- 原失败 reader 2,396.885812 CPU-s；
- 修复 completion 50.777541 CPU-s；
- 原工程、修复测试及已计量收集/自读。

97.2M actor presentations、分类器标签与更新、83,000 个 reader model-team step、actor/critic **各**498,000 行重放均计价。原生仍为 1,196,000 steps，没有因读取修复增加。原宏动作 SET-T 的 1.79 CPUh 不能替代本次逐步学习价格。作者、审阅、控制、准备和部分收集支持未完全计量；18–26 CPUh 是原预测，不能据低于预测称全部支持免费。

我的实际检查包括：全部冻结/训练 metadata 身份、224 个 main 保存 mask/支付 ledger、28 个完整冻结原生正反例、九个训练 raw、135 条训练曲线、全部最终端点和 728 组成对统计，以及完整 canonical checks 的承重字段。没有重演优化、模型或完整 physics reader，没有复制 bulk。神经重放仍使用原固定 factory，不能当成独立神经实现验证；训练 physics 没有逐 tick 重算；训练复现仍是一 fit/臂。

本评审有效显式计时的保存数据算术约 **2.75 CPU-s**；另一次读取脚本因计时变量覆盖未获得有效耗时，静态阅读、SSH 和写答支持亦未完全计量，均不冒称零成本，未混入 DM 的累计账。

**MATERIAL_DISSENT: no。** 对象是 DM 在 [B03 完整解读](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:3973) 中“结束原样三配方、不采用学习最终策略、保留 O 与历史条件资产、不自动选择修复”的处置。直接依据是 O 的 128/128 完成、学习最终的 5/6/4、未建立的自身收益、完整用户缺口和实际费用。对任何尚未给出的新拟合方案，本答不构成认可。
<!-- B03 ORIGINAL RESULT CRITIC END -->

<a id="b03-independent-disposition"></a>
### B03 DM disposition of the independent result diagnosis

**MATERIAL_DISSENT: no.** I accept the independently reconstructed endpoint,
rare real multihop gains, individual-service adverses and bounded interpretation.
The unchanged three-fit purchase ends; none of its learned finals is adopted.
O's complete four-window capability is retained with its364.344-tick mean world
maximum same-user gap, once-only schedule and absence of a path-optimality or
energy/safety claim. The finding is about these finite fits under this sampled
deployment contract, not the learnability of joint service. Earlier R, S0/S1 and
Bstar capabilities keep their own evidence and task boundaries.

The critic adds a useful precision to the paired comparison: **all45 saved
H/noD pre-rollout RNG states are exactly equal**, as is the initial training RNG;
the first entire rollout's actions, positions, skills and payments are identical.
SET's training RNG differs. The prospective allowance for naturally diverging
trajectories did not assert that RNG states would diverge, and no RNG divergence
is a negative-result explanation here. H/noD is a single paired reward
intervention with retained discriminator training. Later policies and experiences
are endogenous to the reward change, so this still does not identify a fixed-
history skill mechanism. This source/raw finding strengthens the intervention's
identity without turning one fit per arm into replication or equivalence.

The original exact-action reader failure remains published. The copied-vector
repair, unchanged strict comparisons, old302 checks and65 new ordinary checks
support complete coverage without replacing the native experiment or repeating
neural replay. The critic's728 independent paired reductions and28 full native
cases complement my70 full native cases; they are inspections of paid evidence,
not extra evaluation worlds. All161 paid main segments include at least eight
same identities, but that favorable detail does not erase the full-user gaps.

I retain the observed Gaussian scale/host projection relationship as an
unseparated candidate explanation. The old bounded-speed, target-point and
zero-entropy results above prevent treating a head or entropy edit as an obvious
repair. Removing discriminator reward has already failed to establish a useful
complete task gain in this purchase. Parameter change, nonzero successes and
increasing entropy do not individually identify the cause of failure.

The critic's SET-initial/final deterministic-mean comparison would be a new
execution programme on outcome-exposed development worlds: its32000 native-step
core price omits complete reader, audit and support costs. Root explicitly does
not purchase it now; I agree that it is a conditional design candidate, not a
mandatory diagnostic gate or automatic next cell. No action-head fit, additional
seed, imitation fit, longer exposure, reward retuning or other B03 effect is
selected. Wider cross-question allocation stays with Root; it is not an unfinished
B03 collection dependency. A substantive future assignment must inherit these
costs, ordinary opportunities, adverse outcomes and unchanged prior positive
assets, then state the capability and comparison it can actually change.

<a id="b03-final-cleanup"></a>
### B03 terminal evidence, measured cleanup and handoff boundary

The worker and both reader operations are terminal, with valid exit witnesses
and absent original runner/supervisor identities. Worker exit0 finished
2026-10-02 11:18:16.154592UTC; original reader exit1 finished12:05:51.106813UTC;
completion reader exit0 finished12:37:28.537646UTC. All accepted native collection,
full reading, my interpretation and the sole independent scientific disposition
are now complete. There is no unread result, live scientific operation, pending
observer event or selected follow-on producer in this direction.

After consuming terminal events, the private observer was stopped at generation12
and drained with zero pending events; daemon531710 was inactive. Its final state
and all three original status commands are preserved in
[observation-final.json](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/observation-final.json).
The obsolete private state/scratch path was then deleted. Consequently the old
in-progress handoff's drain/rearm instructions are historical: there is no live
state to rearm, and the failed reader's mechanical retry eligibility is not
permission to repeat a scientifically complete study. The native status handles
remain available for read-only reconciliation; no worker is restarted.

I checked durable published source, external canonical outputs and live consumers
before deleting the two terminated reader snapshots through supported GC. The
initial scan refused a protected `/proc/660/cwd`; the documented privileged
read-only process scan resolved that visibility limitation, and verified apply
then removed both targets and their Git worktree registrations. No shared
canonical Git, runtime, partial-clone configuration or unrelated job was changed.
The earlier preparation fetch's existing Git GC warning remains untouched and is
not a scientific or cleanup blocker. Exact measured deletions are:

| Deleted target (remote snapshot suffix or local relative path) | Allocated before | After | Net bytes reclaimed |
|---|---:|---:|---:|
| Worker `.git/hmasd-launch-sources/728d72485d07492e9ed7caefcf74c5d7` | 1813323776 | 0 | 1813323776 |
| Failed reader `.git/hmasd-launch-sources/89f42cc796054e9883dbaafc384af1ec` | 1824731136 | 0 | 1824731136 |
| Completion reader `.git/hmasd-launch-sources/1bc44712a941417aa1cb34de52b600d5` | 1824899072 | 0 | 1824899072 |
| Earlier `temp/directions/uav_decision_generalization/b03_factory_a01` | 23531520 | 0 | 23531520 |
| `temp/directions/uav_decision_generalization/b03_observation` | 122880 | 0 | 122880 |
| Owned B03 source `__pycache__` | 221184 | 0 | 221184 |
| Owned B03 tests `__pycache__` | 81920 | 0 | 81920 |

Final local deletion425984B less its4096B retained cleanup receipt yields421888B
net local reclaim. Together with the three snapshots and earlier factory scratch,
these scoped cleanup measurements give **5486907392 net allocated bytes
(5.110081GiB) reclaimed**. This is a measured target/receipt delta, not a claim
about whole-filesystem free space while other authors write. Useful source and
compact evidence remain; no raw, checkpoint, failed outcome or check was deleted.
[Worker witness](../../../../runs/uav_decision_generalization/b03_joint_window_a01/worker-snapshot-cleanup.json),
[two-reader witness](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/readers-snapshot-cleanup.json),
[local witness](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/local-cleanup.json).

The single canonical remote evidence copy remains at the original three run roots:
worker749 files/1379496137logicalB/1381232640allocatedB;
failed reader310 files/16479040logicalB/17018880allocatedB;
completion74 files/2542645logicalB/2686976allocatedB. Total1400938496allocatedB
includes directory blocks. The earlier worker file-only allocated figure excluded
114688B of directory blocks, not additional scientific data. Keep all734 raw and
metadata files, five distinct initial/final checkpoints, old302 checks and new65
checks. [Retention receipt](../../../../runs/uav_decision_generalization/b03_joint_window_read_a02/retention.json)
binds manifest/summary identities and every new check; old checks remain bound
by `B03_READER_PREFIX.json`. There is no duplicate bulk archive or retention chain.
A small empty owned temp directory may remain; it contains no running state.

Final measured DM chain CPU is **52360.783838954s =14.544662177h**, including the
last.021546860s retention hash/size collection. The critic separately reports
about2.75CPU-s of valid saved-data arithmetic; its.197551768s RNG-state read is
within its own scope and is not added again. One invalid critic timing and some
DM diagnostic stdout-loss/support work remain unmeasured, not zero. Authoring,
source inspection, SSH, admission/control, engineering/scientific review and
writing/cleanup support were not comprehensively CPU-metered. Native totals remain
1196000, three fits,615600 optimizer steps,0GPU, with failed-reader and repair
costs explicitly retained above. The forecast18–26CPUh/16–28supporth is not a
measured all-inclusive invoice and never authorized another run.

The owner-requested [same handoff document](HANDOFF_20261002_JOINT_WINDOW.md) is
updated to this terminal boundary rather than left as an in-progress snapshot.
Direction standing is reserve after the fixed purchase, retaining its scientific
question and current lead until a real reassignment. No owner pause is lifted,
owner is not transferred, and no accepted operation is migrated. Further work
requires a concrete worthwhile selected continuation; none is automatically
queued by this completion.

<a id="successor-investment-20261002"></a>
## 2026-10-02 15:02 UTC — successor investment comparison, before selection

Root assigned the successor native DM `/root/dm_joint_service` one bounded
decision: compare frozen SET initial/final mean deployment, one direct physical
action-distribution comparison, and no further purchase of these B03 assets.
The continuing question remains acquisition/generalization of complete joint UAV
service at explicit information, experience and compute cost. This entry is
source/paid-evidence reading and design only: **0 new fits, native transitions,
model/controller forwards, physics queries or health probes**. The former B03
operations remain terminal; no observer or old session was restored. Stable lead
remains `Codex DM (native child)`; Root owns current routing and cross-question
allocation. No typed/B06 or paused Claude path is changed.

I read the complete startup and Root/three-DM handoff, this direction's final
handoff, the complete14,011-byte Oracle advice in
[the successor archive](../../archive/2026-10-02/RESEARCH-three-dm-handoff-and-next-plan.md),
and the full15,010-byte original B03 result critic and DM response above. Those
unchanged result reviews are reused; one separate-context registered
ResearchCritic `/root/dm_joint_service/continuation_critic`, `fork_turns=none`,
is reviewing this actual investment choice. It receives original sources first,
then prior interpretations, and owes neither another run nor agreement. Its full
answer and my disposition will follow here. No additional Pro consultation is
needed unless that review exposes a distinct unresolved need.

### Evidence that changes the choice

The relevant current published background is RESEARCH topics4,5,8 at
`c3a31d4033637b423f1bd96ce359afeb1e8fa740`, unchanged in Root's new routing/control
publication `1ef16a5dc`. The concrete design effects are: retain capable ordinary
O/B; separate acquisition from deployment and complete individual continuity;
require a native consequence beyond changed motion/entropy; and count a zero-fit
observation's complete reading and support cost. A negative B03 purchase does
not erase the [three R block gains](#b01-independent-disposition) or
[S0/S1 and Bstar uses](#b02-complete-reading). Those are different decision objects,
not evidence that either proposed B03 intervention will work.

I re-read the primary B03 worker config/summary/manifest, final reader
`reading.json`/summary and saved native case extracts. Direct reductions of all
main rows reproduce O128/128, B11, H/noD/SET final5/6/4 and the121/120/120 windows
never reaching eight active backhauled users. The final reading still hashes to
`eab3cdeff541f4849f6086e5752d0ea9ad59b6e29ab7765a9b047bce5d356c69`.
All135 training rows give62/71/62 real payments. Original native metadata also
confirms all45 H/noD pre-rollout RNG states equal, not merely their initial state.
Later policies/experiences differ after the reward intervention. There is one
fit per arm, no equivalence inference, and no missing-update explanation.
O's mean world maximum same-user gap remains364.34375ticks despite all windows
and all50 users served sometime. The original reader failure, copied-vector
arithmetic repair, all accepted exact comparisons and the failed-reader expense
remain untouched.

The stronger competing explanation is incomplete acquisition of useful geometry
and joint configurations under these finite recipes. Lower motion noise may
change occupancy without producing a scheduled relay arrangement. Most final
windows never even have q>=8, so a sustain-only repair has little support.
Mean execution could still reveal a conditional learned capability, but the
existing sampled traces cannot evaluate that closed-loop counterfactual. Increasing
raw Gaussian entropy, raw radius and clipping is a source-confirmed co-occurrence,
not a common-cause diagnosis or an invalid-likelihood proof.

I read the old Claude primary configs, summaries and deterministic holdout
panels, not only their inherited descriptions:

| Frozen run under `runs/coupled_host_joint_skills_stage1/` | Original source | Complete deterministic coverage | What changed and what it failed to establish |
| --- | --- | ---: | --- |
| `b02_fit_SETVb_932201_a01` | `889a7e28ea93cf05cc906adcc22eb3261715ab7a` | .209905 | Tanh box, logstd init−1/clamp[−5,0]; deterministic clip .5/3000 versus old2819, but no strong service recovery; sampled clip remained954/3000. |
| `b02_fit_SETT_932201_a01` | `186b8649e6ddd90b6d4a009594cbd780131d833d` | .357105 | Target every10ticks plus straight-line executor and changed discount/update scale; below the same-interface random-target .3652. |
| `b03_fit_SETT_932201_a01` | `76d5d514b76870f610646617103f3ea3b7bc5345` | .34956375 | Same target package with low-level entropy coefficient0; paired difference−.00754125 from SET-T, not recovered service. |

Each was one360k fit. Their primary resource records give11734.065805,
3867.041483 and6438.930791CPU-s respectively; probes and earlier exposures are
additional inherited costs. The original dense-task/holdout contract differs
from B03's sparse registered windows; these are **not B03 counterfactuals**.
The later accepted correction in Claude NOTES,2026-09-30 02:56, is retained:
sigma .37→.20 is less noise, not lost precision; logged entropy0 was a reporting
branch; far-target counts do not prove an unused mean; shared reward was not
identified as the cause. The evidence makes a generic head/noise cure a weak
purchase argument without declaring every bounded distribution empirically
refuted.

### Alternative1: one complete mean-deployment asset-use question

This would ask whether the *particular* final SET checkpoint contains useful
deterministic closed-loop control beyond its initial checkpoint that its sampled
deployment did not express. Its contribution would be empirical understanding
and conditional asset use, not new learning or a general learning-method claim.
Use only the canonical existing SET initial/final weights, respectively
`ba2eb18a78abfbe4383d105292a53d81d777d71d6549dfa279c9ab30ff765586`
and `9be9c88f867b2dc6a8749bda099429a471731ee041fd01b878486139a407f463`.
No checkpoint search, fine-tuning, H/noD panel or new ordinary fit is needed.

The original32 worlds109220000…109220031 are now outcome-exposed development
worlds, not fresh confirmation. Execute each checkpoint's Gaussian mean at each
primitive tick, with the existing recurrent reset, own211-row, held10-tick
state154/joint rows, actor1637 and public404-byte registration addition. All
singleton SET skills remain the one available label; no hierarchy sampling
intervention is introduced. `DiagGaussian.forward(deterministic=True)` returns
the latent/raw mean. The actual command is its host radial projection, **not**
the expectation of the clipped stochastic action. Float32 command multiplication
precedes addition to float64 position, the copied-three-vector norm and strict
`>1` branch stay, and arena/altitude clipping follows. Density is not an endpoint
or optimization objective here. The native call still computes critic values;
omitting their cost would underprice the existing path.

Keep the original world generator/RNG, seed inference at world+51 after
factory/reset, save actual RNG and recurrent state. Mean execution removes
Gaussian sampling; its RNG consumption need not equal sampled execution and
must not be described as a paired exogenous action-noise tape. Environment
geometry is shared, while closed-loop observations necessarily change. The
reader must replay this declared mean mode on its own saved inputs and preserve
the native movement arithmetic; it cannot infer new paths from old sampled
trajectories. Frozen parameters, normalizers and0optimizer calls are checked.

Core evaluation is64H500=32000native. Including one full correctness mission
per checkpoint on the existing out-of-estimand audit world109229000 gives
**66missions/33000native**. One complete reader adds33000 model-team replay
steps/198000 actor and critic rows **each**,33066 saved-state geometries,
**10614186** distance/path-loss relations,198000UAV movement ticks and1.65M user
indicators. O/B and sampled initial/final retain their already-read original
32-world records without another native panel. No new external labels, fits,
gradient updates or calibration queries. A new reader/audit implementation is
necessary; none is started here.

The initial-to-final mean W contrast is the principal acquisition-use estimand;
the interaction with the already-read sampled initial-to-final contrast locates
mode dependence for these checkpoints. Read q>=8 arrival and paid windows,
all-user first/last/longest gaps, never-served users, dense diagnostic service,
path and full zero-service tails. A meaningful favorable pattern is final mean
exceeding initial mean in completed windows with more qualifying configurations
and a complete service capability, not just less motion or fewer clips. Retain
O's measured four-window capability and B's persistence as lawful use references;
there is no requirement to beat O to observe acquisition, and no case for
deploying an inferior neural programme merely because it beats its own start.

Outcome implications would differ: a final-only useful gain retains a narrow
mean-control asset; a shared initial/final improvement favors a deployment-mode
benefit without a training increment; continued weakness lowers the value of
these two checkpoints. A small or mixed gain keeps that uncertainty. None would
identify entropy during training as the cause, add training replication, rewrite
B03's sampled verdict, or automatically buy a head fit. This observation is
neither an admission gate nor a pilot for alternative2.

**Full forecast, not measured throughput:** .5–1CPUh,0GPU, roughly.25–1compute
wall-hour when available, and4–8agent-support hours across bounded wrapper/reader
work, numerical/RNG review, checks, collection, full reading and publication.
The paid SET main mission bodies sum234.366814832+235.457439795CPU-s; those
469.824254627s exclude construction, write and reader work. The old failed
reader cost2396.885812s for83000model-team steps plus its other checks; scaled
only as an uncertain full-reader anchor, it is not new measured deterministic
throughput. New source/init/reader/audit/support are in the forecast. Existing
SET raw for64 sampled missions is312529276B plus4449509B metadata; predict
.3–.6GiB new unique evidence, about1.7GiB temporary source snapshot and modest
test scratch, approximately2.5–3GiB additional peak disk. Existing checkpoints
stay at their canonical paths, with no duplicate bulk retention. Source hydration,
queue/transport and support are not assumed free or included in the computation
wall forecast. Actual node admission remains a later selected-launch fact.

### Alternative2: direct physical action-distribution package

This would ask whether a different complete sampling/entropy/optimization
package acquires useful scheduled joint service at the same finite information
and720000combined training-step exposure. Two fresh SET fits of360k each would
compare the original Gaussian plus radial projection against one invertible
radial map `a=z/sqrt(1+||z||²)` of a diagonal Gaussian. Keep one common720-world
training law, one new32-world endpoint panel, the same registered task and
actor/critic rights, rewardR/6, per-tick actions and10-tick held snapshots.
Do not replay old fits or include H/noD. Four distinct initial/final programmes
plus fresh O/B would receive32 full H500 missions each and one correctness
mission each:720000+198×500=**819000native**, refining the Oracle's≈820k draft.
Literal new seed addresses are not allocated because this comparison is not
selected. The number of independent training instances remains one per package.

The mathematical map has two tangential Jacobian eigenvalues
`(1+||z||²)^(-1/2)` and one radial `(1+||z||²)^(-3/2)`; hence
`log pi_A(a)=log pi_Z(z)+(5/2)log(1+||z||²)` and
`H(A)=H(Z)-(5/2)E[log(1+||Z||²)]`. It covers the open physical unit ball,
not its exact full-speed boundary, and physical differential entropy is bounded
above by log(4pi/3). This derivation is not a verified numerical implementation
or an empirical claim of useful control. Arena/height limits can still alias
commands. Finite-precision outputs can reach a norm boundary, so the actual
host projection and same copied-vector arithmetic must remain observable.

A credible implementation would store the latent proposal together with the
issued action and their change-of-variables identity, avoiding unstable inverse
recovery near radius1. PPO ratios for a fixed stored latent/action cancel the
fixed Jacobian; the original latent likelihood under a deterministic host map
is not thereby declared wrong. Physical entropy needs a correct current-policy
gradient, not an unweighted stale-action cross-entropy. One explicit option is
the analytic Gaussian entropy minus a pathwise Jacobian expectation using one
fresh3-D normal per presented actor row. That is32.4M additional3-D draws for
the candidate update path, with a separately seeded/saved entropy RNG so those
draws do not silently move the original rollout stream. Same latent initialization
and common rollout draws still give different physical initial distributions
and endogenous trajectories; no bit-identical policy or isolated entropy
intervention is claimed. The coefficient.05 then weights a different entropy
functional, another intended package difference. Numerical gradients, support,
tail stability and RNG ownership would need engineering review before any effect.

The distinctive intermediate conjecture is that the policy need not increase
unbounded raw radial noise to earn the entropy bonus and can allocate useful
interior velocities; low host clipping alone is largely built into the map and
cannot count as success. The consequential prediction would be more q>=8 joint
configurations, paid windows and complete service beyond its own initialization
and the newly trained Gaussian reference, including later-window acquisition.
Geometry, exploration, initialization, entropy and finite optimization change
together. Old SET-V already changed bounded exploration and transformed entropy;
the remaining exact ball-versus-box distinction has no current evidence of
being the important service bottleneck. This is a legitimate untested package
conjecture, with a weak marginal purchase case, not an obvious repair.

Full work would include405000 actor/critic optimizer steps,64.8M actor and
critic agent-tick presentations **each**,4.32M native training actor and critic
rows each,66000 frozen model-team steps and their equal reader replay,
396000 actor/critic rows each per frozen pass,31842558 reader distance relations
and40.95M user-indicator reads. No external teacher labels, online planner
search or experimental LLM query is required; ordinary O/B decisions and
722matching comparisons/O mission remain real work. Training RF need not be
recomputed at every saved tick for this package-use question, consistent with
the old reader scope, but ledger/movement/updates and full frozen physics are read.

**Full forecast:**8–14CPUh,0GPU, about2–5compute wall-hours with the inherited
four-Torch/one-BLAS-thread path, plus12–20agent-support hours; the new density/
gradient/reader overhead is unmeasured. Actual paid B03 SET collection/update
sum is12632.806980858CPU-s per360k fit, not the old macro1.79h rate. Two such
fits already imply7.018CPUh before the revised head, all endpoints, reader,
source/setup and checks. Predict1.5–3GiB unique outputs plus about1.7GiB source
snapshot and bounded test scratch, roughly3.5–5.5GiB additional peak disk.
The declared comparison could retain a useful acquired capability on native
gain, while only changed entropy/radius without q>=8/W improvement would end
this distribution-package purchase. Neither outcome isolates entropy cause;
an adverse or inconclusive package does not refute joint-service learning.
There is no pre-selected sequence of another head or another seed.

### Alternative3 and provisional DM investment judgment

My provisional recommendation is **no new purchase of these B03 checkpoint or
action-distribution alternatives**. This does not infer their unmeasured scores.
The mean comparison is scientifically coherent and much cheaper in CPU, but its
most likely consequential decisions are already available: do not deploy these
sampled finals, retain O, and do not buy a generic bounded-head rescue. A positive
mean result could add a narrow acquired-control asset; the source and paid
traces do not currently supply a specific positive indication that it will do
so, while the older deterministic/low-noise endpoints weaken that expectation.
No planned consumer presently needs these two checkpoints under a new use law.
That makes4–8support hours and a full development-panel reading poor marginal
value compared with retaining the unresolved possibility. This is a value
judgment, not a claim that information without adoption value is worthless.

The two-fit alternative is more expensive and still concentrates on one
implementation symptom after bounded-speed/target/no-entropy revisions under
nearby contracts did not produce strong service. Its distinctive physical-entropy
prediction is well defined, but its native acquisition prediction presently
rests on conjecture beyond those adverse facts. The proposed pair could answer
that conjecture; I do not judge that answer worth8–14CPUh and12–20support hours
now. I do not require a mean-deployment gate, toy success or causal proof to
reach that decision. A future demonstrated need for a transferable joint
controller or a new native-predictive premise may justify a different purchase;
none is manufactured to keep this asset family active.

Stopping this purchase leaves0prospective fits/native/model/RF work and no
producer to await. It preserves the open parent question, O/B and R/S abilities,
all scarce rewards and local multihop positives, and every adverse result.
Sunk costs remain: B03 threefits/1196000native/615600optimizer steps and
14.544662177measured DM CPUh, with separate review/unmeasured support; A/R sixfits/
1736000native/.814449CPUh/.03709reservedGPUh; B02 zero-fits/126976native/
306.282345CPU-s; earlier Claude recipe costs retain their own disjoint ledgers.
They are neither reset nor the reason to spend again. Root can compare this
decline with its distinct fixed-data learning and communication questions;
those other tasks are not a technical dependency of this one.

The two timed remote reads of already-paid JSON used.094517782 and.414156379
CPU-s respectively; other local reading, source inspection, arithmetic and
design/review support were not comprehensively metered and are not zero. No
new implementation, snapshot, bulk copy or scratch was created. This is the
pre-review value judgment, not a final scientific disposition; the one critic's
full recommendation and any dissent are preserved below before publication.


<a id="successor-investment-review-20261002"></a>
## 2026-10-02 15:18 UTC — original independent investment review

Registered ResearchCritic `/root/dm_joint_service/continuation_critic` returned
the following complete answer in its separate context. Its material dissent is
preserved verbatim; it was against the provisional DM no-purchase judgment
above. The critic performed source/paid-evidence reading only, no experiments
or record edits. Original answer follows.

````text
I recommend **revising the no-purchase decision to select one complete frozen SET initial/final mean-deployment comparison: 64 scored H500 missions plus two audit missions, totaling 33,000 native steps and zero fits.** Decline the fresh two-fit action-distribution package.

This is a standalone question about the paid checkpoints’ behavior. Its result would not trigger a head fit, reopen the original B03 purchase, or alter B03’s sampled-deployment verdict.

I received no inherited DM or Root conversation. The assignment supplied the alternatives and factual summaries; I reconstructed the primary records and source semantics before reading the complete prior interpretations, Oracle answer, and DM’s new no-purchase recommendation. That establishes separate-context review, not freedom from model bias.

**The supported diagnosis remains narrower than failure to acquire any useful control.**

The primary evidence supports failure of the three tested sampled deployment programs to establish competitive joint-window capability:

- O completed 128/128 windows; H/noD/SET final completed 5/6/4, versus initial H/noD 5 and SET 2.
- H/noD/SET final never reached eight active backhauled users in 121/120/120 windows. The deficit usually precedes successful sustained service.
- Training nevertheless produced 62/71/62 payments, substantial parameter movement and the declared updates. Neither absent rewards nor missing learning execution explains the result.
- O establishes lawful complete-window opportunity. Its 364.34375-tick mean world maximum same-user gap also preserves the distinction between this once-only objective and continuous user service.

These facts agree with the [complete reading](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b03_joint_window_read_a02/reading.json). I retain the original review’s checked H/noD pairing: all 45 pre-rollout RNG states matched; later policies and experiences differed after the reward intervention. This remains one training instance per arm, without equivalence or population-ranking evidence.

SET’s raw Gaussian entropy increased from 4.356 to 9.205; final sampled commands incurred approximately 2,995.53 clipping events per 3,000 UAV-ticks. The source confirms an unbounded Gaussian followed by native radial projection. These observations do **not** establish an incorrect PPO likelihood or identify the cause of failure. They do establish that evaluating the projected raw mean would implement a materially different closed-loop program.

The strongest adverse reading is substantial: ordinary persistence already performs better than the sampled learners; training payments did not develop into broad competence; SET world `109220000` provides a complete zero-service adverse case. The strongest positive remains limited but real: SET world `109220028` achieved a paid joint-service segment, and fitted parameters changed under actual task experience. Neither pattern tells us what the frozen mean program does.

**My consequential objection concerns the value assigned to the mean comparison.**

The DM correctly acknowledges that a final-only mean-policy gain could reveal acquired control hidden by sampled execution. I disagree that the absence of a current downstream checkpoint consumer makes this question insufficiently valuable at **0.5–1 CPU-hour and 4–8 support hours**.

The empirical distinction is itself central to the assigned question:

1. Did this training instance produce useful control recoverable by a simple, fixed deployment rule?
2. Or would quieter execution benefit initialization similarly, with little useful training increment?
3. Or do both frozen mean programs remain weak?

The initial checkpoint makes this more informative than merely trying deterministic deployment on the final checkpoint. Existing O/B programs provide complete-task references. The study preserves the actual six-agent joint configuration, recurrent control and twenty-tick service requirement.

The nearby adverse experiments substantially weaken a generic noise-reduction repair story. I checked deterministic coverage of `.209905` for SET-V-b, `.357105` for SET-T-b, and `.34956375` for its no-entropy revision, against the target floor’s holdout `.365165`. Low clipping and lower sigma did not establish useful recovery. However, those experiments neither execute these B03 means nor estimate this initial/final deployment-mode interaction. Treating their negative implications as sufficient to decline this much smaller, directly discriminating observation gives them too much influence across changed contracts.

I cannot assign a calibrated probability to a favorable result. My recommendation is an investment judgment: this bounded distinction is worth the full stated price even without immediate adoption. It is not justified by sunk costs, an obligation to obtain a positive, or a claim that deterministic control is likely to succeed.

**The smallest complete observation I recommend is already close to the DM’s alternative 1.**

Use only the canonical SET checkpoints:

- Initial: `checkpoints/SET/initial.pt`, SHA256 `ba2eb18a78abfbe4383d105292a53d81d777d71d6549dfa279c9ab30ff765586`.
- Final: `checkpoints/SET/final.pt`, SHA256 `9be9c88f867b2dc6a8749bda099429a471731ee041fd01b878486139a407f463`.

Score both on all original worlds `109220000…109220031`. These are now outcome-exposed development worlds. Use `109229000` once per checkpoint for correctness auditing, excluded from the estimand. Reuse the existing sampled SET and O/B endpoints without new ordinary missions.

The principal estimand is

\[
\Delta_{\rm mean}=\frac1{32}\sum_w
[W(\mathrm{SET}_{final,mean},w)-W(\mathrm{SET}_{initial,mean},w)].
\]

Report the corresponding deployment-mode interaction against the existing sampled initial/final difference, which is `+0.0625 W/mission`. This is a conditional comparison of these artifacts and worlds. Descriptive paired-world uncertainty cannot supply independent training replication.

Preserve the complete per-world reading: windows completed, windows ever reaching \(q\ge8\), qualified-run lengths, later-window behavior, all-user gaps including leading/trailing censoring, never-served users, dense service diagnostic, travel and zero-service tails. Do not select worlds, checkpoints or alternative mean transformations after exposure.

The implementation semantics are specific:

- Use the original `DiagGaussian` raw mean returned by `deterministic=True`. The executed command is its native projection, **not** the expectation of the projected stochastic command.
- Preserve the copied three-vector norm, strict `>1` projection branch, float32 velocity arithmetic before addition to float64 positions, and subsequent arena/altitude clipping.
- Preserve recurrent reset, current observation, ten-tick held joint snapshot and all existing information rights. I checked that SET’s saved configuration has `n_Z=n_z=1`, no high-level training and the ordinary fixed-clock route. Changing deterministic mode introduces no alternative skill choice.
- Retain the original world construction and inference seeding after factory/reset. Record actual RNG state; do not claim identical sampling-noise consumption across deployment modes. The deterministic switch can change draw consumption even where categorical support is singleton.
- Keep parameters and normalizers frozen, record zero optimizer calls, and retain the existing critic/value computation in the cost.
- Replay the new trajectories in the declared mean mode. Old sampled trajectories cannot provide the counterfactual observations or recurrent histories.

The current worker and reader hard-code sampled execution. The purchased engineering work therefore includes a bounded new evaluation/reader path with source, checkpoint and immutable-state checks. It is not a restart of an old operation.

**The prospective prediction and consequences should remain explicit.**

The constructive conjecture is that final mean deployment forms more qualifying joint configurations than both its own initialization and its sampled deployment, and converts that improvement into paid service. Reduced clipping or motion alone supplies no support.

| Complete outcome | Scientific and investment consequence |
|---|---|
| Final mean shows a useful initial-to-final gain, including meaningful scheduled service | Retain a conditional acquired mean-control asset. This changes the asset judgment; it does not establish entropy causality, generalization or an HMASD advantage. |
| Initial and final both improve, with little resolved training increment | Retain an execution-mode benefit as the main interpretation. Ordinary persistence remains a strong explanation; no learner continuation follows automatically. |
| Both remain weak, or gains are isolated and accompanied by substantial service losses | End this checkpoint-use purchase. Preserve local positives and adverses; do not automatically proceed to a head fit. |
| Technical failure prevents the complete observation | Record missing evidence and actual expense. Do not count it as a scientific negative. |

O need not be beaten to observe acquired capability. Adoption is a separate judgment involving its much stronger complete service, travel and computation. Conversely, a few favorable worlds should not be promoted into useful complete control.

**The full cost is material and should accompany selection.**

I directly read canonical saved metadata and verified:

- SET initial/final 32-world mission bodies: `234.366814832 + 235.457439795 = 469.824254627 CPU-s`.
- Their saved raw/metadata: `312,529,276 + 4,449,509 bytes`.
- SET’s original 45 training collections and updates: `1,590.435664233 + 11,042.371316625 CPU-s`.

The first number excludes construction, writing and the reader. It is not the proposed study’s full price.

The recommended scope totals **66 missions, 33,000 native steps, zero fits/updates/external labels**. Its complete reader adds 33,000 model-team replay steps, 198,000 actor rows and 198,000 critic rows, 33,066 physical states, 10,614,186 distance relations and 1.65 million user-indicator readings. Native inference is additional to those replay counts.

The DM’s full forecast—**0.5–1 CPU-hour, zero GPU, 4–8 support hours, 0.3–0.6 GiB new evidence and roughly 2.5–3 GiB additional peak disk including the temporary source snapshot**—is a reasonable selection estimate grounded in the paid records. It remains unmeasured for the new implementation. Queue, source hydration and incompletely metered support must not become zero-cost claims. No health pilot is needed to make this investment choice; actual node admission remains an execution requirement after selection.

B03’s existing three fits, 1,196,000 native steps, 615,600 optimizer steps and approximately 14.544662 measured CPU-hours remain charged, including the failed reader. Earlier A/R, S and Claude costs retain their separate ledgers.

**I recommend declining the fresh action-distribution pair.**

The radial-map density formula is algebraically correct in three dimensions: the Jacobian determinant is \((1+\|z\|^2)^{-5/2}\). The resulting policy covers the open unit ball and changes physical exploration, initialization, entropy and optimization geometry together. It does not isolate clipping or prove the old likelihood invalid.

The proposed **819,000-native-step, 405,000-update, two-fit** comparison could test a legitimate package conjecture. Its **8–14 CPU-hours and 12–20 support hours**, plus unverified entropy-gradient, numerical and reader work, are a substantially larger purchase. The old bounded-speed and no-entropy adverses lower its marginal value, while the exact ball-versus-box distinction has no demonstrated native importance. I would decline this pair even if no mean observation were selected. The mean observation is therefore not its admission gate.

I also do not infer that Root’s bank or communication alternatives are better simply because they were ranked higher in the Oracle answer. Their proposed acquisitions were outside this review’s primary-source verification.

My checks covered the specified worker/config/manifest and complete-reader records, direct reductions of consequential endpoints, window-failure decomposition and training exposure, selected positive/adverse native-case extracts, critical source/hash bindings, frozen inference semantics, the original reader failure and repaired source, the three specified Claude primary configurations/summaries/holdout panels and corrected interpretation, the full original critic/disposition, complete handoff and Oracle archive, relevant current RESEARCH passages, and the new DM comparison. I reused the prior independent raw reconstruction for unchanged portions. I did not reread every canonical raw trajectory, rerun the reader, reconstruct optimization, load checkpoints into models, or validate a new implementation. No experiment or record edit occurred.

Root should resolve this specific investment disagreement in the existing record. This review supplies a recommendation, not authorization to execute.

**MATERIAL_DISSENT: yes — against the DM’s proposed decline of the single complete frozen SET mean-deployment observation.** The direct basis is the severe sampled projection, source-confirmed distinction between sampled and mean execution, the available initial/final control and O/B references, and the verified cost anchors. There is no dissent over B03’s completed reading, declining the fresh two-fit package, or preserving the broader learning question without promising a repair.
````

<a id="successor-investment-disposition-20261002"></a>
### DM response and revised recommendation for Root allocation

**Revised recommendation: purchase the one complete frozen SET initial/final
mean-deployment observation; decline the fresh two-fit physical-action package.**
I read the full answer and accept its correction to my investment judgment.
The original `MATERIAL_DISSENT: yes` remains, rather than being rewritten as
initial agreement. I have supplied the disagreement to Root and return this
revised recommendation for the actual cross-question allocation/resolution.
No new effect is selected or executed by this entry, and no implementation or
health pilot has begun. This is the assigned substantive design boundary, not a
new per-run approval rule.

The changed judgment is about information value, not a predicted positive score.
My provisional decline put too much weight on absence of a present checkpoint
consumer and on the older dense-contract adverses when valuing this specific
initial/final question. They still argue against buying a generic noise/head
rescue and prevent treating reduced clipping as a sufficient native prediction.
They do not answer whether these paid weights contain a useful mean-control
increment. A complete acquisition-versus-execution distinction is itself useful
empirical understanding within this assigned question. At the stated price, I
now favor obtaining that distinction rather than leaving it unresolved. There is
no new empirical evidence that mean execution will succeed and no calibrated
probability claim. Adviser agreement after reconsideration is not new data.

The recommended comparison remains exactly alternative1 above: the fixed two
checkpoint hashes, all32 original now-exposed development worlds plus one audit
world per checkpoint, the original sparse joint-window contract, lawful paid
O/B and sampled initial/final references, full saved-trajectory reader and no
fit. Its testable constructive prediction is final mean acquiring more q>=8
configurations and paid service beyond both initial mean and final sampled
execution. The principal acquisition-use difference is final mean minus initial
mean; the mode interaction subtracts the observed sampled increment2/32 =
.0625W/mission. All per-world losses, user gaps and service tails remain in the
reading. Neither beating initialization nor fewer clips alone warrants adoption.
These32 worlds cannot become fresh confirmation, and their uncertainty cannot
replace independent training instances.

For avoidance of any undercount, the66 native missions require33000 model-team
steps and198000 actor/critic rows **each**, in addition to the equal complete
reader replay: **66000 total model-team steps and396000 actor rows plus396000
critic rows across native inference and reader**. The stated33066 physical
states/10614186 relations/1.65M user indicators are the independent reader's
work; actual native environment work is also present in the33000 transitions.
The full forecast remains.5–1CPUh,0GPU,4–8support hours,.3–.6GiB unique evidence
and2.5–3GiB additional peak disk, with source/init/reader/audits/checks included
and queue/hydration/support uncertainty explicit. No new throughput was measured.
The critic independently corroborated the paid metadata anchors; its support
cost is separate and incompletely metered, not a zero-cost experiment.

A useful final-only mean gain would retain a conditional acquired asset and
change the checkpoint-use judgment. A common initial/final gain would principally
support an execution-mode benefit. Weak, mixed or heavily adverse service would
end this checkpoint-use purchase without erasing local positives or the parent
learning question. Technical missingness would remain missingness. None of
these outcomes buys a head fit, forces a replication or changes B03's sampled
verdict; any materially new investment needs its own reason and price. The
819000-native/two-fit alternative is declined independently of this observation.

Root owns the current allocation choice; I retain continuity of the broader
joint-service question. No bank or communication task is a technical dependency,
and this recommendation does not rank them without their actual evidence. A
Root decline of this purchase would leave no producer or recurring checkpoint
review. A newly selected substantive question would be a distinct choice, not
work manufactured to maintain a DM count.

The current shared-background topics4/5/8 remain accurate: this review changes
an investment judgment and exposes no new reusable empirical result or scope
correction, so I do not manufacture a background edit. Only this direction's
standing is updated. Original useful code, compact readings, unique bulk evidence
and adverse outcomes remain at their canonical locations. This bounded design
work created no source snapshot, scratch or new bulk; actual deleted targets:
**none; disk bytes reclaimed:0**. There is no cleanup tool blocker or inherited
operation requiring observation. The old B03 cleanup remains separately recorded.

A source check on the review’s entropy numbers confirms they are recorded
optimizer-loss averages for SET rollout1 and rollout45
(4.3561312556266785 and9.205397963523865), not separately measured frozen
initial/final policy entropies. This leaves the co-occurrence diagnosis and
recommendation unchanged.


<a id="b04-selected-contract"></a>
## 2026-10-02 15:36 UTC — B04 selected frozen SET mean comparison and L0

Root read the complete original critic and DM disposition, adopted the specific
investment dissent and selected **only** the complete mean comparison in its
native return, subsequently published at
`e7352cd5afbcc7beb05bbb175347f5c60e88286a`. This resolves the prior selection
boundary: B04 is the one active result-bearing study. It does not reopen the
819000-native/two-fit physical-action purchase or an old operation. I continue
through implementation, review, admission, collection, complete reading,
applicable independent result judgment, own publication and cleanup. No further
per-step Root acknowledgment is needed.

The scientific contract is alternative1 plus the complete original review above.
Its exact endpoints are the two original SET checkpoint hashes; scored worlds
109220000…109220031 and one audit109229000 per endpoint give66H500 missions/
33000 native. The scored panel is development-exposed. Native and reader each
make33000 model-team calls/198000 actor and critic rows each. The independent
reader reconstructs33066 physical states/10614186 distance relations, movement,
all1650000 user indicators, twenty-tick window payments, recurrent inputs, held
state/rows, raw/projected commands and full individual tails. Reuse the already
read sampled SET initial/final and O/B worlds at their fixed identities; no new
ordinary mission, update, label, training attempt, head variant or checkpoint
search. Native inference returns the raw Gaussian mean; the original copied-
vector projection and host arithmetic remain the executed command. RNG starts
after factory/reset at world+51, with actual pre/post states recorded; there is
no stochastic-tape equivalence claim across modes.

**L0 deliverable and ownership.** Add the admitted B04 worker/reader entry under
`experiments/candidates/uav_decision_generalization/b04_set_mean/` and focused
tests under its matching test directory. Reuse the current B03 implementation
and independent physics/ledger/metric reader. Permit only the necessary explicit
keyword extension of B03 `worker.frozen_mission` and `independent.replay_model`
for deterministic inference, retaining sampled `False` as their default. Record
the mean mode and terminal RNG explicitly, reject a reader/mode mismatch, and
leave historical B03 records and frozen source identities unchanged. This is one
bounded behavior change, not a general deployment framework. No shared core,
launcher or another direction edit is authorized. DM exclusively owns NOTES,
study/locator/budget inputs, run collection and index/publication. A registered
Implementer may own only the stated code/test paths, with no Git index mutation,
no result launch, no model/host health call and no children. Main/shared checkout
remains the sole authoring location; concurrent work must be preserved.

**State/identity contract.** The original worker is the canonical remote root
`/home/wu/projects/HMASD/runs/uav_decision_generalization/b03_joint_window_a01`.
Its config/summary/manifest hashes are respectively
`0bc410effb3e254ea38f5f23186e5ed975a5492251f333ad059c56932e228e88`,
`2fe984bf5c203b2b450237c1304a0b074f24c604e7adfe7153f02f1a9a263ae9`,
`6d572b218c091ccd5ca2b8e305c0b1dc074f45efdd24c51029d4edbaa5ac1c95`.
Load the two canonical21.4MB checkpoint files there without copying them into
a new evidence root. Bind their arm, endpoint, original launch identity, complete
configuration/modules/normalizers and state digest before use; require unchanged
parameters/normalizers and zero optimizer calls after each mission and replay.
The existing final B03 reading is
`runs/uav_decision_generalization/b03_joint_window_read_a02/reading.json` with
sha256`eab3cdeff541f4849f6086e5752d0ea9ad59b6e29ab7765a9b047bce5d356c69`.
All46 source paths recorded by that reading currently match published main
exactly. Bind unchanged inherited source bytes against it; only the two explicit
mode extensions above may differ. The B04 source manifest additionally includes
all B04 source files and its actual static dependency closure. Worker and reader
must use identical selected source bytes, input contract and checkpoint binding.
The raw episode remains the inherited B03 task object, while the new study/config/
summary identifies B04 and its mean deployment; no old sampled result is relabeled.

**Implementation/check scope.** Add a strict66-row roster, fresh-output refusal,
exact accepted source/output/launch checks and admission before every scientific
effect. Preserve attempted/completed native counts and partial trace on failure.
Return summary/manifest, complete raw NPZ and per-mission metadata; the reader
checks all66 files and retains compact full per-world/user/window readings. Its
principal contrast is mean-final minus mean-initial and mode interaction minus
the already-paid sampled+.0625W/mission; include mean versus sampled and O/B
service, geometry-acquisition, travel and user-gap contrasts with adverse worlds.
No fitted statistical model or new random bootstrap query is needed; reuse the
existing descriptive paired-world reducer, with no training-replication claim.

Focused tests cover the new admission and duplicate/output guards, exact roster
and external identities, explicit mean/default-sampled dispatch, terminal RNG
and immutable-state checks, preserved numerical motion replay, wrong-mode/hash/
roster refusal, zero-effect counter failures and reference joins. Tests use
mock agents/admission/host and synthetic arrays; no actual checkpoint/model
forward, RF/native episode or health pilot is selected outside the66 missions.
Reuse applicable old checks for unchanged physical/recurrent semantics and run
only the relevant tests, recording measured check CPU/wall and coverage gaps.
Independent engineering review is required for the numerical/RNG/recurrent/
identity effects before scientific execution; it does not repeat the scientific
investment review.

**Execution budget and stop.** Select configured remote `wsl_4070`, CPU device,
Python3.10.21/Torch2.7.0+cu118/NumPy1.26.3, four Torch and one interop/BLAS thread.
No package, device or host change and no health probe is part of this choice.
The full study forecast remains.5–1CPUh,0GPU,.25–1compute wall-hour plus4–8
support hours,.3–.6GiB unique evidence/~2.5–3GiB additional peak disk. Node
admission requests8GiB available physical/effective RAM and at least4GiB free
disk for the new source/output working set, in addition to the normal kernel
floor; the canonical old evidence remains read-only and charged to its own
retained scope. Source publication precedes launch. Worker and reader are two
detached admitted operations with identical scientific source/input, collected
and fully read; release the worker's source snapshot after verified durable
collection and before the reader snapshot so temporary source copies do not
silently double the declared peak.

Hard scientific exposure is66 full missions/33000 native and one complete
33000-step neural reader, with0fits/updates. There is no extra audit/pilot or
rerun allowance. A conservative emergency operating boundary is7200 new-study
CPU-seconds across worker/reader/checks and7200wall-seconds per operation,
checked at bounded mission/replay boundaries; these are watchdogs above the
forecast, not permission to add samples. Report and preserve first failure,
partial evidence and actual paid effects; technical failure is not a scientific
negative and does not authorize a duplicate. No source/identity or numerical
tolerance relaxation is implied. Old B03/A-R/S/Claude costs remain as recorded
above; new-study metering is separate and added, never a reset of sunk costs.
Authoring/transport/review support not metered by the process ledger stays
explicitly unmeasured. Accepted handles use the same-node deterministic observer
and this native child remains active through complete reading.


<a id="b04-implementation-review"></a>
### B04 implementation acceptance and independent engineering review

The registered Implementer `/root/dm_joint_service/mean_implementer` completed
the one L0 change in the shared main checkout, without Git mutations, result
launches, actual checkpoint deserialization/model/host queries or children. I
read all six new B04 modules, both B03 diffs and the complete focused test file.
The new path reuses B03 collection and physical/neural replay through an explicit
`deterministic=False` default, binding mean mode and terminal RNG when selected.
It checks the full mean reset context, exact programme/world/phase roster,
original weight/config/normalizer identities, hook-observed actor/critic rows,
zero updates, guarded admission and fresh output, failure prefixes and the
cumulative ledger. The full reference join uses132 already-paid check files
from their real a01/a02 roots; no baseline raw replay or episode is added.

All scientific tests were synthetic arrays/mock agents, host and admission.
The command family was configured local scientific Python
`/home/fires/.venvs/hmasd-linux-cpu/bin/python -m pytest -q`, targeting
`tests/experiments/candidates/uav_decision_generalization/b04_set_mean/test_mean.py`
and the three existing B03 test files. Actual reported checks were:

| Check | Outcome | CPU seconds | Wall seconds |
|---|---|---:|---:|
| B04 plus three B03 files |41passed,2new mock-fixture failures |5.999787|5.652098|
| After repairing the fixtures |18passed|4.041918|2.926729|
| Expanded complete B04 checks |22passed|6.231500|5.056803|
| Final affected `frozen_dispatch or worker_context` checks |3passed|3.228425|2.187957|

Total check cost is19.501630CPU-s/15.823587wall-s; maximum pytest-process peak
RSS336932KiB. The28 inherited B03 checks passed, including unchanged numerical
fixtures. The two initial failures were test-fixture defects, preserved in this
cost record; they were not result attempts or scientific outcomes. Pytest owned
and removed its scratch. I read these checks rather than rerunning unchanged
ones. After review I clarified three output/error strings only: the comparator
scope now says initial/final endpoints of **one** training instance, and two
shared error labels say frozen rather than sampled policy. No numerical or
control-flow behavior changed. `git diff --check` passes.

The separate registered read-only engineering Reviewer
`/root/dm_joint_service/mean_engineering_review` inspected the actual new files,
the two extensions, tests and reachable inherited paths. Original return:

````text
No material engineering finding remains in the assigned diff.

Reviewed the six new B04 modules, both B03 extensions, focused tests, and reachable inherited paths. Verified:

- Deterministic dispatch reaches the original Gaussian mean; projection and float32 velocity arithmetic remain inherited.
- Worker and reader preserve world order, recurrent resets, ten-tick held inputs, seed placement, terminal RNG checks, and immutable checkpoint state.
- Checkpoint, source, baseline-prefix, worker-locator, and episode identities are bound before dependent work.
- Exact exposure counters, actual actor/critic hooks, cumulative ledger, watchdogs, admission, duplicate-output refusal, and partial-failure evidence remain connected.
- Comparisons exclude audit worlds and retain matched user/window details.

I relied on the supplied passing checks and inspected their coverage; no redundant tests or scientific/runtime queries were launched. No files were changed.

Residual limits: the exact study/ledger/locator JSONs were not yet authored, and remote checkpoint loading, native execution, and numerical replay remain unvalidated at runtime. This review does not establish execution success or scientific acceptance.
````

I accept the implementation subject to the recorded runtime checks and the
narrow exact-input follow-up, not as a successful scientific observation. The
source manifest now binds52 paths: all46 inherited dependencies, with only the
two reviewed mode-extension exceptions, plus the six new B04 files. The exact
study and known-cost inputs are [B04_STUDY_INPUT.json](B04_STUDY_INPUT.json) and
[B04_BUDGET_LEDGER.json](B04_BUDGET_LEDGER.json). The latter starts at
21.957492084 known new-work CPU-s:19.501630 checks,.094517782+.414156379 earlier
paid-metadata reads,.035135747 canonical asset hashing,.027456176 full-reference
hashing/join, and1.884596 local source/contract preparation. The four recorded
metadata-read invocations are the timed remote subset, not every unmetered local
inspection. Other authoring, transport, review and support remain unmeasured,
not zero; the B03 final14.544662177CPUh and other disjoint inherited bills remain
separate and do not become a new allowance.

Canonical input hashing read the original eight worker/checkpoint/reader files
without deserializing a checkpoint. All132 full baseline checks (1,861,338B)
matched the final reading's lineage and scalar metrics; SET66 and the first O
world come from the bound failed-reader prefix, the remaining O/B65 from the
completion reader. Neither failure history nor the original copy repair is
erased by reusing their accepted checks. The new study performs only its own66
mean missions and equal reader.

The same engineering Reviewer completed the narrow exact-input follow-up,
without a new full review or scientific/runtime query. Original return:

````text
No material input-binding finding.

Verified exact schemas and contract, all 52 current source hashes, original checkpoint/ancestor/reading identities, 132 unique baseline rows split 67/65, inherited 44 unchanged sources, all compact lineage joins, 67 prefix-check identities, and the sampled `+.0625` contrast. Remaining full-check byte identities rely on your reported canonical verification.

The ledger correctly sums the supplied costs to `21.957492084` CPU-seconds, separately from B03 sunk costs. These two additional read-only verification blocks measured `0.484222446` CPU-seconds; carry that forward before launch, yielding `22.441714530` known CPU-seconds. Other unmetered support remains unmeasured.

Study SHA-256: `94f72b7bf74fe941f16ef3ab4b9752843e7ae3f4396d0fc6b309a634668c86c2`.

No source writes, scientific queries, or runtime/health probes performed. Terminal worker-locator validation remains deferred until that output exists.
````

I accept that check and carry its.484222446CPU-s and two verification blocks
into the pre-worker ledger: **22.441714530 known new-work CPU-s**. The study
input/source bytes are unchanged; only the known-cost ledger increases. No
actual scientific or native health query was used to validate execution in
advance. The exact worker-locator values will be read from its terminal output,
then published before the reader.

Exact code and inputs are published at
`ba30ca0f3fb861f86b766b134d93d5a27a06dcab`. Study input sha256 is
`94f72b7bf74fe941f16ef3ab4b9752843e7ae3f4396d0fc6b309a634668c86c2`;
pre-worker ledger sha256 is
`42d67b777cd57b2cc2858134b5a78e78b640ba86b8026d00eff056c95413cd85`.
The remote configured `zsh -lic` fetch exited0 and advanced origin/main to that
source. Its existing noninteractive zsh/gitstatus warnings and automatic Git GC
warning (`e0b4af9d04f8a4a53368e3ca0055007c82141449 exists in commit-graph but
not in the object database`) are retained as preparation facts. No source/
checkpoint/native operation was started by that fetch, and no shared Git,
shell or runtime configuration was repaired or replaced. Control preparation
CPU/transport remains unmetered; this is not an extra fit or health pilot.

<a id="b04-worker-acceptance"></a>
#### 2026-10-02 16:08 UTC — fixed mean worker accepted

The configured remote supervisor `dmgen-b04-set-mean-a01` accepted one kernel
invocation; the native kernel then admitted the published `ba30ca0f3fb` source
at16:07:33UTC. Stable operation/claim is
`/home/wu/projects/HMASD/.git/hmasd-admission/281ab737ce51a3598aee694402e18074ea1cc44127b57771ae579581c21843aa.json`,
output `runs/uav_decision_generalization/b04_set_mean_a01/`, retained source
snapshot `dc12271b49d24878badc6eea3f30976b`, supervisor1344118 and
runner1344119 with native birth identities in the collected launch manifest.
The first status had accepted/consistent records and both processes running;
this is execution acceptance, not a read scientific result.

`tools/hmasd_wait.py` registered the exact native operation as
`b04-set-mean-worker-a01` for this assigning child, generation1, with a1500s
window and30s deterministic probes. Its state is direction-owned
`temp/directions/uav_decision_generalization/b04_observation/`; the child
remains active and will drain/rearm this handle, without duplicate launch.
The original launch manifest and admission preflight are collected locally;
raw evidence remains on the admitted node pending complete collection and
verification. No later fit, altered controller or extra baseline is selected.

#### 2026-10-02 16:15 UTC — worker terminal and exact reader inputs

The original worker exited0 at16:09:54UTC; deterministic observation produced
READY with consistent claim/manifest and absent runner/supervisor. This native
child's attempted queue delivery was rejected (`direct app-server input is not
allowed for multi-agent v2 sub-agents`); its still-active local deterministic
wait returned the saved event, which I drained completely and consumed by
same-state rearm to generation2. No work was restarted or moved.

The complete worker reports66 missions,33000 native and frozen-model team
steps,198000 actual actor and198000 critic rows,2 model constructions,0 fits
and0 optimizer steps. Measured worker501.127710CPU-s/133.522782wall-s,
675640KiB peakRSS,0GPU; prior22.441714530 brings worker cumulative to
523.569424530CPU-s. The retained single-Z std-of-one diagnostic warnings
remain in canonical stderr; no warning was treated as evidence of failure or
silently fixed. Complete independent numerical/model/physics reading remains
necessary and has not yet run.

All132 raw/metadata files matched their closed manifest byte counts and hashes:
321783169 logical bytes. The canonical worker directory contains141 files,
321835422 logical/322088960 allocated bytes, at
`wsl_4070:/home/wu/projects/HMASD/runs/uav_decision_generalization/b04_set_mean_a01`.
No raw/checkpoint copy was created. Compact config, summary, manifest and
native records were collected into the matching local run directory;
`collection.json` binds their hashes and the remote evidence location. Metadata
collection/verification consumed.183210609CPU-s, without model/RF/native effects.

After that verification, supported source GC independently checked terminal
native identities, no live references, clean source and durable publication.
It deleted only snapshot `dc12271b49d24878badc6eea3f30976b`; allocated bytes
fell1827221504 to0, net **1827221504B reclaimed**. Preview/apply cost
.195848455/.633048105CPU-s. Claims, raw, metadata and original checkpoints
remain; no backup or retention copy was created. The worker and planned reader
therefore do not retain simultaneous full source snapshots.

The reader uses `B04_READER_WORKER_INPUT.json`, which binds the canonical worker
root and exact config/summary/manifest digests; sha256
`24ddd8e07d97f153d9397c400d4aaa8c464f2c2a78f15d6faa4cf8ffb00c23a9`.
All52 scientific source hashes still match the worker. The separate reader
ledger carries the exact original prior counts plus all worker counts, without
inventing another effect, and **524.651696902 known cumulative CPU-s** before
the narrow deferred engineering input check (including.070165203 preparation
CPU-s). Additional support/transport remains incompletely metered, not zero.
The planned full reader performs exactly33000 replay model team steps,
198000 actor/critic rows each and33066 complete reconstructed physical states,
with0 new native steps and no new baseline collection; audits stay outside the
32-world estimands. No scientific inference is made from terminal status alone.

The existing engineering Reviewer completed the deferred terminal binding
check. Original return, preserved in full:

````text
No material locator, ledger, or source-binding issue.

Verified the locator schema and three hashes against collected files and `collection.json`; terminal 66-row roster and counts; checkpoint, ancestor, and study identities; all 52 current source hashes; and exact worker-prior-plus-counts ledger carryforward.

The `524.651696902` CPU-second prior matches the supplied cost components and exceeds worker cumulative CPU. This check measured another `0.015163338` CPU-seconds: update prior CPU only to **`524.666860240`**, preserving counts.

Raw-file verification relies on the reported canonical collection. No scientific/runtime queries or edits performed.
````

I accept this limited check. The published pre-reader ledger carries
524.666860240CPU-s and unchanged exact prior counts; later reader collection,
scientific arithmetic and support will be reported separately. This closes
the selected engineering input check, without a new scientific choice or
authorization for additional effects.

Reader inputs and compact worker evidence are published at
`0f05d8ec5bdfe405a662359817b5a9cb45549815`; the final reader-ledger digest is
`94ac8f95c1fea74c1bc1e70d1cd12801980b821fdbce3bf18c268deeb772828f`.
Remote fetch exited0 and obtained this source. The existing automatic Git GC
warning now reported `bad tree object dfe82c9813ee82191abb8385cc12a6886fd0a77b`
and `failed to run repack`; no shared Git maintenance was attempted. One
configured supervisor invocation `dmgen-b04-set-mean-read-a01` was submitted
for the selected reader, pending native kernel acceptance. Scientific source
and the original two checkpoint assets are unchanged.

The native reader was accepted at16:16:49UTC, operation
`/home/wu/projects/HMASD/.git/hmasd-admission/ae59a9a5d5255f8de5628389f7cdfea5c91546d51db21a0614d8ab603a253b02.json`,
output `runs/uav_decision_generalization/b04_set_mean_read_a01/`, source
snapshot `57cea9a364734982a798f0db050f4529`, supervisor1345443,
runner1345444. The first native status was accepted/consistent/running.
Same-session deterministic observation registered that exact handle as
`b04-set-mean-reader-a01`, generation3,1500s window/30s probes. The child
remains active through collection, complete reading and independent scientific
disposition; published worker completion alone is not that result boundary.

<a id="b04-complete-reading"></a>
#### 2026-10-02 — complete mean comparison: the final mean does not recover joint service

Both selected operations are terminal, collected and completely read. The
reader exited0 at16:18:49UTC and independently reconstructed all66 missions:
33066 physical states,10614186 distance relations,33000 ledger updates,
1650000 user indicators and198000 movement UAV-ticks. Its pinned neural replay
used33000 team steps and198000 actor plus198000 critic rows; no new native
step, fit or optimizer call occurred. All66 check records have maximum
observation/state/UAV-SINR/user-SINR errors0 and hidden-input/raw-action/value
errors0, one immutable state digest per endpoint, and zero optimizer calls.
The two-way mean-mode metadata/reset/RNG checks passed. Physics/information/
ledger reconstruction is independent; neural replay deliberately reuses the
pinned factory/inference implementation and is not a second neural algorithm.

The full canonical reading is
`wsl_4070:/home/wu/projects/HMASD/runs/uav_decision_generalization/b04_set_mean_read_a01/reading.json`,
2678714B, sha256
`acd3c5df08094396a8016c997387dc5372861a805686298a63dbc8e9583e1ff2`.
Its66 full check files remain beside it with hash identities in
[collection.json](../../../../runs/uav_decision_generalization/b04_set_mean_read_a01/collection.json).
The full checks contain additional error/policy fields intentionally omitted
from the reading's result rows; checking the common result fields matches
exactly. A preliminary full-dictionary equality check returned false for that
field-scope difference, not a numerical discrepancy. The complete reading's
per-user gaps, censoring, all windows and paired tails were retained, including
both audits outside the32-world estimands. No world or checkpoint was selected
after results became visible.

[Compact DM reading](../../../../runs/uav_decision_generalization/b04_set_mean_read_a01/dm-reading.json)
retains all26 scalar summaries for all six programs, all nine paired
comparisons and the mode interaction, all66 mean mission scalar rows, every
qualifying mean window, audit windows, and individual-tail aggregates/extremes.
Independent saved-JSON arithmetic checks416 scalar summaries,7488 paired
world differences and832 interaction differences. This is arithmetic on paid
evidence, with no extra model or physics evaluation. The32 original development
worlds remain outcome-exposed; descriptive t intervals concern these conditional
world contrasts and do not add training instances.

| Program | Completed windows /128 | Windows ever q≥8 /128 | Qualified ticks | Mean backhauled coverage | Mean dense J | Mean team-zero ticks | Mean never-served users | Mean same-user longest gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SET initial, sampled (paid) |2|6|271|.160191|.102053|121.000|37.688|405.534|
| SET final, sampled (paid) |4|8|283|.145228|.089209|150.156|35.750|411.644|
| SET initial, mean |5|5|625|.173879|.107883|123.063|40.656|413.061|
| SET final, mean |2|6|98|.095151|.058789|269.094|33.313|432.433|
| Sticky waypoint B (paid) |11|32|699|.215451|.137996|38.906|15.719|326.519|
| Scheduled ray-chain O (paid) |128|128|14621|.723644|.451225|2.688|0|129.089|

The principal final-minus-initial **mean** contrast is−.09375W/mission,
3 negative worlds/29 ties/0 positive, descriptive t95
[−.200522,.013022]. Its difference from the saved sampled training contrast
(+.0625W/mission) is−.15625,6 negative/25 ties/1 positive, t95
[−.317731,.005231]. These are not evidence of training-population inferiority
or equivalence. They directly fail the constructive prediction that this final
asset's mean deployment would uncover improved joint-window acquisition.

Final mean minus saved final sampled gives−.0625W/mission (2 losses,30 ties,
0 gains); mean initial minus sampled initial gives+.09375 (4 gains,1 loss,
27 ties). A final-only mean observation would have missed this opposing
initialization effect. Final mean is also below B by−.28125W (9 losses,23 ties)
and below O by−3.9375W (all32 losses). The final mean gains no completed window
over either its own initial mean or its saved final sampled deployment.
Changing the evaluation mode is consequential; the direction of its effect
does not establish trained acquisition.

**Native window reading.** Initial mean's five completions are world004/window2,
006/window3,007/window1,014/window0 and020/window0 (world prefix109220).
All five sustain125 qualified ticks across the whole corresponding window.
The trained mean loses the first three, never reaching q≥8 in those particular
later windows. Its two retained completions are the same initial-world
window0 cases014/020 at action19; qualified lengths fall to20/62. There is no
new completed window. Final mean reaches q≥8 in four additional incomplete
cases:007/window0 for7 consecutive ticks,008/window0 for5,
015/window2 for3 and028/window1 for1. Thus ever-q≥8 counts increase5→6
while qualified exposure collapses625→98 and completed windows fall5→2.
Of128 final-mean windows,122 never reach q≥8 and only4 reach it without a
twenty-tick payment. Rare persistence failures exist, but a sustain-only
explanation still misses the overwhelming configuration-acquisition deficit.

**Complete service and individual tails.** Final versus initial mean loses
62982 of the139103 initial served-user ticks (final76121); mean backhauled
coverage falls.0787275 and dense J falls.049093749. J has21 losing worlds,
10 winning and1 tie; its descriptive t95 is[−.074481,−.023706]. Team-zero
ticks rise146.031/mission (24 worse,7 better,1 tie), longest team-zero runs
rise113.063, and mean same-user longest gaps rise19.372. Every mean mission
still contains a never-served user with a full500-tick gap. This is not user
continuity, and the once-only window reward is not a fairness guarantee.

Retain the contrary individual benefit: never-served user-world pairs fall
1301→1066. The trained mean newly serves236 previously unserved users and
loses one previously served user (world002/user15, formerly35 ticks).
Those236 new contacts total13256 served ticks;25 receive one tick only and
123 receive fewer than20. Across all1600 paired user-world identities,253
gain served ticks,282 lose and1065 tie;254 longest gaps shorten,281 lengthen
and1065 tie. More users touched is compatible with less total service and
longer interruptions. World028 is a real local improvement from zero service
to.1472 backhauled coverage/J.091659,24 fewer never-served users and365 fewer
team-zero ticks; it still completes no window. World000's19 new users each
receive only one tick. World021 remains completely unserved under both means.
The original mean's three lost completed-window worlds004/006/007 have
coverage losses.23788/.32536/.18024, gaps longer114.18/152.90/66.66 ticks
and119/356/163 additional team-zero ticks. These losses are not hidden by the
smaller never-served count.

Against final sampled deployment, final mean loses40061 user ticks, increases
team-zero ticks118.938 and mean same-user longest gaps20.789; J is lower in25
worlds and higher in7. Against B it loses96240 user ticks and increases mean
gaps105.913. Against O every one of1600 user-world identities receives fewer
served ticks, though20 longest gaps are shorter; O's distinct364.344-tick mean
world maximum same-user gap remains a limitation, not erased by its large
advantage. Audit world109229000 has W0 for both means; its mean deployment
coverage/J also falls while never-served users fall40→20. Audits remain checks,
not a33rd inferential world.

**Executed action behavior.** Initial mean has0/3000 mean clip events per
mission and travels200.835m/UAV; final mean has2770.844/3000 clip events
(92.3615%) and travels8899.456m/UAV. Final sampled has2995.531 clips (99.8510%)
and travels13732.420m/UAV. Removing evaluation action sampling therefore does
not remove the trained mean's host projection. Final mean spends2331.531
altitude-boundary and1167.813 xy-boundary UAV-ticks per mission versus
903.375/192.094 under final sampled, while zero-displacement events rise to
73.656. These are measured rollout behaviors, not matched-state causal
mediators. Deterministic raw mean followed by the existing host projection is
neither expected projected action nor a new physical-unit-ball policy.

**Working explanation before independent result review.** The exact B03
checkpoint pair does not contain the useful complete-service improvement that
simple mean deployment was proposed to reveal. The result weakens an
evaluation-noise-only concealment explanation and establishes that severe
clipping of this final asset persists without action draws. It does not
identify entropy, projection, sparse credit, optimizer behavior, representation
or team coupling as the training cause; deleting evaluation draws does not
undo how they affected the acquired weights. The lawful O capability still
establishes task opportunity. The few newly reached configurations and user
contacts establish limited behavioral differences, without a competitive
learned deployment package or a general claim that joint service cannot be
learned. Earlier R and S conditional capabilities and all old adverse outcomes
remain intact.

The fixed mean observation is complete, not a gate to the separately declined
two-fit physical-action package. A replication would address training-instance
variation but has no demonstrated useful recipe to replicate; a bound/entropy
repair would still need its own native acquisition prediction and competent
ordinary comparator, and nearby adverse packages continue to count. Reopening
either is not justified merely by the remaining causal uncertainty. My
provisional next judgment is to retain the exact evidence and useful reader,
decline adoption of final mean and stop immediate B03 asset/entropy-head rescue
investment. The broader learning question remains open for Root's substantive
next-question choice. The original separate-context critic is reconstructing
this result independently; its unabridged recommendation and any dissent will
be preserved below before the final disposition.

**Measured cost and retained evidence at this reading boundary.** Reader
396.158241CPU-s/112.517071wall-s,671708KiB peakRSS and0GPU brings its
closed cumulative ledger to920.825101240CPU-s. Subsequent collected-file
hashing/content joins, seven saved-JSON readings, compact arithmetic and
reader-source GC add1.726941969 measured CPU-s: known new DM cost is
**922.552043209CPU-s=.256264456CPUh**, before later review/publication cleanup.
Terminal-write/transport/authoring and other support remain incompletely
metered, not zero. Worker+reader do66000 model team steps/396000 actor rows
and396000 critic rows in total,4 model constructions,33000 actual native
steps,0 new fits and0 optimizer steps. The original B03 three fits/1196000
native steps/615600 optimizer steps and52360.783838954 measured DM CPU-s
remain sunk, not erased by freezing SET; B03+B04 known DM CPU is currently
14.800926634h. Earlier R/S studies and separate review/support bills retain
their own recorded scope. The actual new measured CPU is below the.5–1h
forecast; that observation does not erase the support cost or authorize another
batch.

The reader directory retains75 canonical files,3479100 logical and3633152
allocated file bytes, including2678714B full reading and66 full check files.
Together with the worker, new unique canonical evidence occupies325722112
allocated file bytes; original B03 evidence/checkpoints remain in their bound
locations. The local full-reading copy exists only for active DM/critic
inspection and will be deleted after those consumers finish, while compact
results remain published.

Native event generation3 was fully drained and consumed by rearm to4; the
attempted child queue delivery had the same unsupported-subagent rejection.
Observation was then explicitly stopped, both jobs were ready/consumed and the
observer process was absent. No producer or checkpoint remains running. After
complete output verification, supported GC deleted reader snapshot
`57cea9a364734982a798f0db050f4529`, allocating1827307520B before and0 after.
Preview/apply used.185436895/.606498605CPU-s. Both new source snapshots are
gone and **3654529024B** have been reclaimed so far, with no deletion blocker,
bulk relocation or backup. Native claims, exits and unique outputs remain.

<a id="b04-independent-result-review"></a>
#### 2026-10-02 — original independent scientific result review

Registered ResearchCritic `continuation_critic` returned this complete original
answer at16:46:34UTC. The same separate reviewer context covered selection and
now the completed evidence; this is not a blind review of its own earlier
recommendation. No DM/Root conversation inheritance, new fit, native evaluation
or neural/physical rerun occurred. The12465-character answer is preserved below
without condensation; the original selection dissent remains above.

````text
**Recommend stop the frozen SET mean-action route, retain its complete result, and decline the separate two-fit action-distribution package.** B04 weakens the explanation that useful joint-service behavior was already present in SET’s mean and merely concealed by sampling. It preserves some partial geometric competence, but supplies no useful complete deployment benefit.

This is a follow-up in the same independently created reviewer context used for selection. I reused the earlier B03 reconstruction; no DM/Root conversation history was inherited, and no preferred post-result explanation was supplied.

I checked the original B04 reading, source/configuration bindings, all 66 new full checks, all 132 hash-bound baseline checks, all nine paired comparisons, their user/window details, and all 416 scalar mean/SE/interval summaries. I also inspected 20 distinct native mean-trajectory archives, covering the consequential positive and adverse cases. The source is `b04_set_mean_read_a01/reading.json`, SHA-256 `acd3c5df08094396a8016c997387dc5372861a805686298a63dbc8e9583e1ff2`; its durable copy remains under `/home/wu/projects/HMASD/runs/uav_decision_generalization/` on `wsl_4070`.

The main results are:

| Programme | Completed windows /128 | Windows never reaching q≥8 | Backhauled coverage | Never-served users, mean /50 | Mean user longest gap | Mean path per UAV, m |
|---|---:|---:|---:|---:|---:|---:|
| SET initial, mean | 5 | 123 | 0.173879 | 40.656 | 413.061 | 200.835 |
| SET final, mean | 2 | 122 | 0.095151 | 33.313 | 432.433 | 8,899.456 |
| SET initial, sampled | 2 | 122 | 0.160191 | 37.688 | 405.534 | 13,560.948 |
| SET final, sampled | 4 | 120 | 0.145228 | 35.750 | 411.644 | 13,732.420 |
| B | 11 | 96 | 0.215451 | 15.719 | 326.519 | 9,294.869 |
| O | 128 | 0 | 0.723644 | 0 | 129.089 | 2,208.152 |

The primary mean-action acquisition contrast is **−0.09375 windows per world**, with zero world-level wins, three losses and 29 ties. Its descriptive paired interval is `[−0.200522, 0.013022]`. The sampled acquisition contrast remains `+0.0625`; the mode interaction is `−0.15625`, with interval `[−0.317731, 0.005231]`. These intervals cross zero. They do not establish a population-wide negative training effect, but the complete observed asset comparison contains no positive primary world.

The final mean also has zero W wins against final sampled SET, losing worlds `109220028` and `109220030`; zero wins and nine losses against B; and losses on all 32 worlds against O. Against sampled initialization it exchanges one win (`014`) for one loss (`029`). I checked the remaining initial-mean comparisons as well; none supplies a contrary complete-benefit result.

The native window records explain what those counts mean:

- Initial mean succeeds on worlds `004`, `006`, `007`, `014`, and `020`, with completion actions `269`, `394`, `144`, `19`, and `19`. Each qualifying scheduled window lasts all 125 ticks. These are favorable geometries already served near initialization, preserved by very small movements.
- Final mean retains only `014` and `020`, both completing at action 19 from initially qualifying geometry. Their qualifying scheduled runs shrink from 125 ticks to 20 and 62. It acquires no new completed window.
- Final mean reaches q≥8 without completion in four scheduled windows: `007` for seven ticks, `008` for five, `015` for three, and `028` for one. The other 122 windows never activate the qualifying geometry.
- The `008` failure is specifically late arrival: service persists from actions `[120,184)`, but its scheduled window ends at 125. Calling every active failure “inability to hold geometry” would therefore be wrong.

The individual-service positive is real, but insufficient. Compared with initial mean, final mean newly serves 236 world-user pairs and loses all service for only one. Of those 236 newly served pairs, 123 receive fewer than 20 service ticks, 31 receive at least 100, and none receives 400. They contribute 13,256 service ticks. Meanwhile, the 299 pairs served by initialization fall from 139,103 service ticks to 62,865.

Thus “fewer never-served users” mainly records broader visitation alongside substantial loss of continuity. Total coverage falls by `0.0787275`; team-zero-service time rises from 123.063 to 269.094 ticks per world. Final mean has a 500-tick same-user gap in every world. These are horizon-censored observations, not claims about infinite-duration starvation.

The comparison with final sampled SET is also adverse despite lower movement: coverage falls by `0.05007625`, mean user longest gap increases by `20.78875` ticks, and team-zero time increases by `118.9375`. Mean path falls by 4,832.963 m per UAV, but XY-boundary exposure rises in every world. Lower movement alone is not a native benefit here.

I checked the strongest useful positive beyond the scheduled score. Reconstructing all four target-cluster service histories from saved user-gap records shows:

| Diagnostic, ignoring schedule timing | Initial mean | Final mean | Initial sampled | Final sampled | B | O |
|---|---:|---:|---:|---:|---:|---:|
| World-clusters ever reaching q≥8 | 5 | 20 | 10 | 17 | 74 | 128 |
| World-clusters sustaining q≥8 for ≥20 ticks | 5 | 7 | 7 | 7 | 30 | 128 |

This is a **post hoc diagnostic, not a replacement reward or changed reading rule**. Final mean creates five new sustained visits, all outside the relevant scheduled window:

- `008`, cluster 1: `[120,184)`, 64 ticks; only five count within its window.
- `015`, cluster 1: `[448,468)`, 20 ticks; its window was `[0,125)`.
- `023`, cluster 2: `[63,92)`, 29 ticks; its window was `[250,375)`.
- `030`, cluster 1: `[45,81)`, 36 ticks; its window was `[125,250)`.
- `031`, cluster 3: `[312,340)`, 28 ticks; its window was `[375,500)`.

I checked those positives against native saved connection/path masks. Each contains at least eight identical users throughout its first 20 ticks. Final mean simultaneously loses three sustained geometries present at initialization.

This supports partial geometric reach and occasional holding, and identifies timing as consequential in some cases. It does **not** establish learned schedule-conditioned coordination: sampled initialization already has seven untimed sustained visits, B has 30, and O has 128. Incidental visitation remains a strong simpler explanation. The positive is worth preserving without turning it into an obligation to repair the policy.

My supported diagnosis is therefore narrower than “SET learned nothing”:

1. **The unused useful-mean explanation is weakened substantially for this asset.** The decisive initial-to-final mean comparison is adverse on the frozen objective and on sustained service.
2. **Sampling noise is not the sole source of problematic execution.** Final deterministic means still produce clipping on 92.36% of UAV action-ticks, versus zero for initial mean. The inspected final raw means have large norms even without sampling. This establishes problematic mean execution, not the training cause of those means.
3. **The simpler account fits the evidence:** near-stationary initialization preserves some favorable placements; trained movement broadens visitation but destroys much existing service and rarely puts sustained service in the correct window.
4. **Finite optimization, sparse reward exposure and training/deployment co-adaptation remain unresolved.** Switching to deterministic deployment does not isolate the causal effect of entropy, projection, initialization or optimization during training. B04 cannot refute a different learning recipe or all useful internal representations.
5. **Opportunity remains established by O under the declared information contract.** O’s engineered task knowledge is a substantial computational advantage, not extra hidden observations. Its success establishes feasibility and competent baseline performance; it does not establish easy learnability. Nor does 128/128 make O a complete fairness solution: its retained mean world-maximum same-user gap remains about 364.344 ticks.

The source and comparison checks support this interpretation. All 52 scientific source identities match between worker and reader; current inspected bytes match those manifests. The 198 metadata records across six programmes share the complete initial physical/information digest, initial host RNG and addressed pre-inference RNG within each world. Baseline identities, endpoint identities, audit exclusion and the complete 32-world roster are intact. The accepted reader reports zero observation/state/SINR and neural replay errors.

I did not rerun neural or physical reconstruction. I independently checked saved evidence and arithmetic, and inspected selected raw service histories. Matching initial RNG does not imply a shared action-noise tape after the inference-mode change. The 32 outcome-exposed development worlds remain conditional observations from **one original SET training instance**, not independent training replications.

The selected study has now supplied the smallest worthwhile complete observation for its question. A useful final-over-initial mean gain, with native service benefit, would have supported retaining the asset and considering replication. A generic improvement in both endpoints would mainly have implicated deployment variance. The observed adverse acquisition contrast, together with untimed partial competence, supports closure of this mean-action route.

I do not recommend another frozen panel, a changed window rule, an entropy sweep or a mandatory repair. None is needed to interpret the completed comparison.

The separately declined two-fit package remains genuinely untested. A direct unit-ball distribution could change learning, but it changes initialization, exploration, entropy and action geometry together. B04 does not empirically refute that package, and its negative result is not a failed gate that automatically triggers it. Its approximately **819,000 native steps, 405,000 optimizer updates, 8–14 CPU-hours and 12–20 support-hours** remain a separate investment. Given the competent ordinary controls, weak complete learned benefit, untargeted timing failures and prior dense-task bounded/no-entropy adverse evidence, I still judge its marginal value insufficient within this asset question. No new cross-question assignment is proposed here.

Actual new study cost is 66 H500 missions, including two audits: **33,000 native steps, zero new fits and zero optimizer updates**. Worker CPU is `501.127710` seconds; reader CPU is `396.158241` seconds. The reader’s cumulative ledger is `920.825101240` CPU-seconds, including prechecks and known prior support, before terminal collection/review additions; GPU use is zero. Worker and reader each perform 33,000 model team-steps with 198,000 actor and 198,000 critic agent-rows. The retained B03 programme’s roughly 14.545 CPU-hours and original training costs remain inherited evidence costs, not zero-cost learning.

My 16 metered saved-record arithmetic blocks consumed **2.921449218 CPU-seconds**. This excludes shell/Git/CodeGraph, orchestration, authoring and two failed read-only diagnostics: a removed-snapshot source locator and my initially omitted 10-user cluster offset. Both were corrected against canonical records and the frozen contract; neither involved model, controller, physics or native execution. This is not a complete support-time total.

A supported shared-background update would be:

> B04’s complete frozen SET mean comparison found 2/128 final versus 5/128 initial scheduled joint-service windows, with lower sustained coverage and longer service gaps; final sampled SET retained 4/128. Deterministic deployment did not reveal a task-useful mean in this original training instance. Five newly acquired off-schedule sustained cluster visits preserve partial geometric competence, but do not establish schedule-conditioned learning or complete native benefit. Close this frozen-asset route without a new fit; entropy/projection causality and broader learnability remain unresolved.

**MATERIAL_DISSENT: no — on closing the frozen mean-action route and declining the separate two-fit package under this bounded interpretation.** The original selection dissent remains preserved and was resolved by executing B04. A claim that no geometry was acquired, that projection/entropy caused the failure, or that broader learning is impossible would exceed the evidence.
````

<a id="b04-independent-disposition"></a>
#### 2026-10-02 — DM disposition: close this asset route, preserve partial geometry and timing evidence

I read the complete12465-character original answer and accept its resolved
recommendation: **do not adopt final mean; close the frozen SET mean-action
route; retain its complete positive/adverse evidence and useful reader; decline
the separately priced two-fit action-distribution package.** There is no
material direction disagreement requiring Root resolution. This does not undo
the reviewer's original selection dissent, which correctly led us to buy the
initial/final deployment comparison instead of assuming its answer. The negative
result is useful new evidence; it is not proof that the observation was a bad
investment. One adequate independent scientific review covers this completed
bounded decision; another Pro round has no identified distinct question here.

The reviewer sharpened the explanation in a consequential way. My prior reading
correctly retained the four scheduled qualifying-but-unpaid cases, but the
whole saved trajectories show that **scheduled failure is not uniformly an
inability to hold geometry**. I reconstructed service masks from every saved
user's gap complement for all192 scored records (six programs×32 worlds), with
the frozen contract's target users10+10j through19+10j. This independent
arithmetic reproduces all scheduled qualified-tick counts and the reviewer's
untimed diagnostic. No episode, controller, model, RF computation or fit was
executed; the original calendar and score were not changed.

| Ignoring calendar only as a post hoc diagnostic | Initial mean | Final mean | Initial sampled | Final sampled | B | O |
|---|---:|---:|---:|---:|---:|---:|
| World-clusters ever q≥8 |5|20|10|17|74|128|
| World-clusters with a q≥8 run of at least20 ticks |5|7|7|7|30|128|

Final mean adds five sustained world-cluster visits absent from initial mean
and loses three initial sustained geometries. These five cases do not earn a
payment under the original rule, which requires20 consecutive q≥8 post-action
service ticks **inside that cluster's frozen125-tick window**, resetting the
counter at every boundary. Intervals below are zero-based action addresses,
half-open `[start,stop)`; corresponding post-state rows are action+1.

| World suffix / cluster | Full saved q≥8 run | Frozen window | Qualified ticks inside its window | Payment |
|---|---|---|---:|---:|
|008 /1|[120,184),64 ticks|[0,125)|5|0|
|015 /1|[448,468),20 ticks|[0,125)|0|0|
|023 /2|[63,92),29 ticks|[250,375)|0|0|
|030 /1|[45,81),36 ticks|[125,250)|0|0|
|031 /3|[312,340),28 ticks|[375,500)|0|0|

I also read and byte-verified all five corresponding saved native NPZs. For
every500-action mask, `connections[1:]` joined to the saved nonempty route
mask exactly equals both `routed_user_mask` and the gap reconstruction. The
first20 ticks of each displayed run serve at least eight identical registered
users (10/10/8/10/10 respectively). Saved schedules, active counts and payment
arrays reproduce the zero payments above. These are saved-data readings, not
new evaluations or suffix replays. The008 run genuinely holds for64 ticks but
arrives too late for the20-tick within-window requirement; the other four are
entirely early or late. The term “off-schedule” here means failure to fit a
complete qualifying run inside the required window, not that every tick of008
lies outside it. The exact raw identities and checks are retained in the
compact reading's `posthoc_untimed_diagnostic`.

This changes the working explanation from only a scheduled-geometry deficit
to **limited broadened geometric reach, occasional sustained holding and poor
alignment with the task calendar, alongside destruction of much initial
service**. Preserve all the adverse context: final mean sustains only7/128
world-clusters even when timing is ignored, equal to sampled initialization,
versus B30 and O128. Its actual frozen W remains2/128 versus initial mean5,
final sampled4, B11 and O128. The three lost initial sustained geometries
are004/cluster2 (initial500ticks),006/cluster1 (500) and007/cluster2 (333),
with final runs at most3/12/5ticks respectively. Untimed gains do not establish
a controllable reusable skill or schedule-conditioned learning; incidental
visitation remains a competent explanation. Nor should the236 newly touched
users be described as all negligible:31 receive at least100ticks, while the
299 originally served identities lose service from139103 to62865ticks.
The complete net continuity loss and positive subcases both remain.

The result distinguishes opportunity (lawful O), executed representation
(different mean/sample behavior and partial visits), finite acquisition (no
useful final-over-initial improvement in this one trained asset under either
declared deployment reading) and complete package value (no adopted final).
It does not identify why learning produced these weights, establish population
inferiority/equivalence, or refute the broader learning question. High
deterministic clipping falsifies neither a future distribution design nor all
internal useful representations. The independent two-fit package still costs
approximately819000native/405000optimizer steps/8–14CPUh/12–20support hours,
has never been tested, and is declined on marginal investment value rather
than relabelled an empirical failure of B04.

**Next investment judgment.** No more frozen worlds, altered calendar,
automatic timing adapter, entropy sweep or physical-head fit is selected. A
replication would address seed variation but not a demonstrated useful method;
an immediate repair would add a new package without a discriminating native
prediction. Re-entry would require a separately selected substantive learning
or deployment question connecting timely registered service and preservation
of existing service, with a competent ordinary comparator and explicit total
cost. The observed five visits can inform such a proposal, but do not reserve
that research question or justify another repair by themselves. Root owns any
new cross-question allocation. This direction is **reserve/idle with no live
producer, unread result/advice, selected successor or external dependency**;
this is not a fabricated wait for an owner decision. R/S capabilities and the
open parent question remain, and this completed B04 purchase does not extend.

The additional DM gap reconstruction used.366582099CPU-s; NPZ schema reading
1.766343747CPU-s and the five complete saved-mask checks.093566242CPU-s.
Known new DM cost is now924.778535297CPU-s (.256882926CPUh), before final
cleanup; the scientific review separately reports2.921449218CPU-s for16
arithmetic blocks with its explicitly excluded support/failed-read costs.
These distinct reported scopes remain separate, and neither is a complete
support-time total. The reviewer has finished, so the temporary local full
reading and closed observation scratch have no remaining live consumer.

<a id="b04-final-cleanup"></a>
#### 2026-10-02 — Published closure and measured final cleanup

The complete B04 scientific result, full original independent answer, resolved
disposition, compact reading and directly affected RESEARCH standing/background
were published as `17a02358a608b81f29bf8dd3a6d3a2daf341e8c8` before deletion.
Root subsequently incorporated that result in its own cross-question plan;
the original direction lead and broader question ownership remain unchanged.
Root's separate successor Oracle creates no new B04 effect or selected study.
Both Root and that Oracle explicitly confirmed that they neither use nor need
the temporary local full `reading.json`; the scientific reviewer is finished.
This check concerns an actual possible consumer, not scientific approval.

I removed all16 exact local targets listed in
[`local-cleanup.json`](../../../../runs/uav_decision_generalization/b04_set_mean_read_a01/local-cleanup.json):
the stopped `b04_observation/` directory; eight B04 observer/request/drain/GC/
interstage/diagnostic scratch files; the two new B04 `__pycache__/` directories;
four duplicate worker/reader stdout/stderr files; and the temporary full reader
copy. Before deletion, the observer was stopped at generation4, both READY
events were consumed, its wake was empty and PID593649 was absent. The logs and
full reading matched their retained canonical collection identities. No target
was tracked, and every named target is now absent. These local targets occupied
2,850,816 allocated bytes. The receipt accounts separately for its own storage
and this notebook's allocation growth.

The earlier supported worker and reader snapshot GC receipts remain published:
`dc12271b49d24878badc6eea3f30976b` reclaimed1,827,221,504 bytes and
`57cea9a364734982a798f0db050f4529` reclaimed1,827,307,520 bytes, both with
their exact targets absent. Thus the two remote source snapshots reclaimed
3,654,529,024 allocated bytes. There was no bulk relocation, tarball, backup
chain or replacement copy. The original B03 weights and required positive,
adverse and failed evidence remain; B04's unique raw/check/full-reading evidence
remains at the verified canonical `wsl_4070` run roots. The useful implementation,
tests and compact Git reading remain published. No unused experimental source
was introduced by this study. No cleanup target remains and no tool blocker
remains.

The final deletion script used0.010536494 CPU-s, bringing the known new DM
metered subtotal to924.789071791 CPU-s (about0.257 CPU-hours). Final record/Git/
authoring and otherwise unmetered support are not included and are not zero;
the independent review's separately scoped2.921449218 CPU-s and inherited
B03 cost remain separate. The closed scientific exposure remains66H500,
33000 native steps,0 new fits,0 optimizer updates and0 GPU use. Cleanup adds
no scientific execution and does not extend this batch. This completes the
selected study's execution, full reading, independent judgment, publication
and cleanup; any later investment requires Root's separate substantive choice.


<a id="request-scheduling-source-scope-20261002"></a>
#### 2026-10-02 — New request-scheduling question: bounded source-only investment work

Root assigned the existing lead one source-only successor construction and
investment judgment after reading the complete temporary Oracle advice. The
scientific question is whether native experience can improve complete joint
request scheduling when known shared three-pair UAV ray executors face new
arrivals, travel losses and reassignment opportunity costs. This is a new task
contract, not a repair of B03/B04 or an inference that the five off-schedule
visits identify a timing cause. B04 remains completely closed.

This assignment purchases source/paid-evidence/primary-source reading, precise
contract and cost construction, one independent investment review by the
existing ResearchCritic, and the DM's resolved recommendation to Root. It does
not purchase production implementation, model/controller/physics/native calls,
health queries, a pilot, three fits or the proposed 2,203,200-native package.
Unknown deployment throughput, training value and full support price remain
unknown; source preparation itself is support work, not zero cost. No accepted
operation is reopened, migrated or duplicated. The direction and its current
lead retain ownership; Root owns the eventual full-package selection.

Relevant published-main background was inspected at
`83b947531b52e371f994ace0f2ee48fef8424280`: RESEARCH topics1/3 distinguish task
contract and lawful information from a decentralized-learning claim; topic4
retains ordinary planning, finite acquisition and complete costs separately;
topic5 retains B03's lawful O and B04's adverse mean comparison with its limited
geometric positives; topic8 calls for a consequential prediction with matched
ordinary rights without requiring proved headroom or a toy pass. The nearby
service-age result preserves learning relative to initialization but not a
benefit over strong M; fleet native continuation likewise does not establish
that starting competence automatically becomes a useful learned successor.
These facts require a competent G/R comparison, full waiting/service tails and
an explicit package-level claim, rather than reusing old scores as new-task
opportunity proof. Unchanged earlier relevant reading remains applicable.

<a id="request-scheduling-original-oracle-20261002"></a>
#### 2026-10-02 — Complete original proposal from Root's temporary Oracle

Root requested the original author's native handback, and the author provided
the same complete answer delivered to Root. It is proposal-author advice, not
independent scientific review. The text below is unabridged:8,910 characters,
17,977 UTF-8 bytes, SHA256
`986b0e6503643ac5a2648abe674fb112c6d3410950a4cd3da33ec9eceb1c3656`.
The preceding transport note is excluded from that identity. Source claims,
counts and proposed contracts below remain subject to direct DM verification
and independent challenge; preserving them does not adopt or execute them.

````text
我的首选是另立一个实质性问题：**在服务请求陆续到达、机组重分配会付出飞行与等待代价时，经验学习能否改善整个任务的联合排程，并形成有竞争力的服务—计算取舍？**

我愿意为下面这一次完整比较投入，但对学习器战胜强普通规划的先验保持谨慎。若用途仍限定为 B03 的四个已知固定窗口，现有证据更支持直接保留 O，停止这份学习资产的修复。A 的六 fit 与 C 的十二 codec fit 继续原计划；这里不重复它们，也不接管 Claude 的问题。本建议是方案共作者意见，仍应由独立 ResearchCritic 挑战。

**1．已有结果支持换学习对象，尚不支持某一种修复。**

| 结论层级 | 当前可以说什么 | 不能据此说什么 |
|---|---|---|
| 任务机会 | B03 的合法 O 完成 128/128 窗口；普通几何构造具有完整任务能力。 | 不能推成容易学会、普通策略全局最优或持续公平服务。O 的世界最大同用户缺口均值仍为 364.344 tick。 |
| 表示与执行 | B04 final mean 确实新增五处持续至少 20 tick 的集群访问，同时丢失三处原有持续几何。忽略日历后 sustained 数从 initial mean 的 5 变成 7。 | 7/128 仅等于 sampled initialization，低于 B 的 30、O 的 128；不能称为可控、可复用的已学技能，更不能把“学会等时间”认定为关键修复。 |
| 学习取得与用途 | 原合同中 mean initial→final 为 5→2/128，增量 −0.09375 W/mission；相对 sampled 训练增量的 interaction 为 −0.15625。当前资产没有获得有竞争力的完整部署收益。 | 92.36% 的 final mean 裁剪率不能识别 entropy、投影、优化或初始化的训练因果，也不能否定另一学习对象。 |

这些区分已经得到最终[独立处置](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:5568)支持。我不建议改写旧日历、继续两 fit action-head 包，或因五次正面访问自动购买 timing adapter。

项目内另外三条证据直接影响我的构造：

- `uav_service_age` 的学习器改善自身初始化，却仍输给强普通 M；“学会偏好一个普通程序”可以是真学习，但并不足以建立有用的状态条件决策。[原读数](/home/fires/hmasd-wsl/docs/research/candidates/uav_service_age/NOTES.md:436)
- parent CONT 约少飞 555 m/UAV，完整 J 增量却约为 0.000094；因此本题不能拿动作更平滑、少走路或更少切换替代完整服务结果。[原读数](/home/fires/hmasd-wsl/docs/research/candidates/uav_parent_adaptation/NOTES.md:8852)
- fleet 的 A2−G2 保留了约 +0.001706 J 的真实前视收益；优化后的 A2 仍付出约 2.888 倍 G2 CPU。它支持研究跨时段机会成本，同时要求认真比较普通规划与学习的完整价格。[物理结果](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_transmission/NOTES.md:2421)、[保留成本](/home/fires/hmasd-wsl/docs/research/candidates/uav_parent_adaptation/NOTES.md:8316)

这些是选题依据，不是新题效果量的预测。

**2．首选构造是“随机请求下的联合机组排程”。**

把已经成立的射线组链能力作为各臂共有执行器。学习对象变为：现在释放哪一对 UAV、承担哪一簇的请求，如何承担在途损失、原簇积压和未来请求。这样有一个完整用途，而不必先证明原 SET 为什么失败。

拟定契约如下；所有数值在实现前固定，不用任务分数调难度。

| 项目 | 固定契约 |
|---|---|
| 物理宿主 | 沿用 B03 的 6 UAV、50 注册用户、四个远端十用户簇及原生运动、关联、路由与服务计算。新自有 wrapper 的真实 horizon 为 1,200 tick；必须从宿主初始化延长，不能到原 500 tick 后仅忽略 `done`。 |
| 请求过程 | 在 t=0,20,…,940，四簇分别产生独立 Bernoulli 请求。每世界将 `[0.6,0.3,0.2,0.1]` 随机置换给四簇；概率在 reset 公布，未来实际到达 tape 不公布。每任务期望 57.6 个请求。训练与评价世界、到达流均独立绑定。 |
| 完成条件 | 每簇 FIFO。队首存在期间，该簇至少 8/10 用户获得原生回传服务连续 20 tick，完成一个请求；完成后进度清零，队列为空也清零，服务中断则清零。在途产生的真实服务同样计入，不要求恰好停在航点。 |
| 主目标 | \(C=\sum_{t=0}^{1199}\sum_c n_c(t)+240\sum_c n_c(1200)\)，单位为 **request-ticks**。\(n_c(t)\) 是当 tick 到达处理后、动作服务前的待办数。这等于截尾等待总和，加每个未完成请求 240 tick 的终端代价。训练和评价使用同一目标。 |
| 共有执行器 | 每簇有 BS→用户均值射线的 1/3、2/3 两点，高度 100；每 UAV 使用原有有界直线 `steer`。Reset 将三对机组布置到三个最高到达率簇，以总预计飞行 tick 最小的 6! 分配确定机组，ID 固定破同分。之后 pair membership 固定。 |
| 联合动作 | 每 20 tick 四选一：KEEP，或释放三对中的一对去当前未占据簇。重新分配时，内外两点的两种指派按最大到达时间、总距离、ID 破同分。其余两对继续执行。 |
| 时间权限 | 各臂取得同一时刻的报告；新命令统一在 20 tick 后生效，其间旧目标继续执行。执行器每 tick 只使用自己的位置闭环转向。没有瞬移、暂停请求或独占的快速下发。 |
| 信息权限 | 同样的完整用户地图、公开到达率、六机位置、当前 50 用户 ACK mask、四队列、四进度、六个目标 slot、时钟。新增可靠 ACK/队列报告是本题的明确假设，不能把它带来的收益算作学习。 |

该主目标处理的是请求服务，仍不等于全部 50 用户持续公平。必须同时报告请求完成率、各簇等待与终端积压、全部用户的服务量和长缺口、路径长度、切换次数。尤其不能让“平均请求成本改善”遮住某一簇或背景用户长期失去服务。

逻辑接口可以明确计价：reset 地图与率 404 bytes；每次状态报告 171 bytes，命令 6 bytes；60 个周期共 **11,024 payload bytes/mission**。这只是所声明接口的逻辑负载，不是完整空口费用；报头、可靠重传、能耗和真实射频排队未建模。需要这些性质的用途，不能直接采用本研究结论。

**3．最强普通替代应当是同信息、真实计价的模型前视，而不只是一个弱贪心。**

我建议一次固定比较三个程序：

| 程序 | 明确计算内容 |
|---|---|
| **G：普通队列前视** | 四个候选动作分别评价“命令延迟后固定这些目标 240 tick”的流体队列成本，尾部加 240 倍剩余工作。使用公开到达率、当前积压和进度，以及直飞到达时间；忽略在途偶然服务。它无需训练、无需 RF rollout，并保留 incumbent。 |
| **R：普通随机 rollout** | 对同样四个首动作，在原生物理模型中向前 160 tick，后续每 20 tick 按 G 决策；末端接 G 的剩余成本估计。最多四条独立未来请求 tape，四候选共享每条 tape；实际未来 tape 不可读。模型调用、G 调用、分支复制及延迟全部计价。 |
| **L：经验学习的完整 cost-to-go** | 四候选共享一个两层 128 单元 ReLU scorer：\(\hat Q_\theta(s,a)=Q_G(s,a)/1200+f_\theta(s,a)\)。最后一层置零，使部署初始化按源代码与输入身份逐动作等于 G。通过原生经历学习完整剩余请求成本，不使用 R 标签或私有信息。 |

G 的流体代理须在 L0 中写成确切递推：初始剩余工作为 `max(n−progress/20,0)`；未来公开到达时点加入概率质量；两机均抵达对应 slots 时，每 tick 消耗至多 1/20 单位工作；报告流体面积与终端工作。它是近似普通模型，不能冒充真实请求成本。R 则用真实整数队列、连续进度和原生 RF 纠正前 160 tick 内的这些近似。

R 采用一个真正受计价约束的执行方式：共同 20 秒计算期限内，按 tape 成套计算四候选，最多四套；只使用已经完整完成的成套比较。到期限取消未完成套，若一套也未完成则执行已计算的 G。保存实际完成套数、取消前缀、CPU、wall、期限违约；不让过期任务后台继续占据下一周期。这样不会把任意大的普通搜索当免费参考，也不靠只给 R 某些更弱信息制造学习优势。20 秒是否满足实际节点吞吐目前未知，是完整结果的一部分。

L 用成本形式 Double DQN，固定有限期 \(\gamma=1\)、时间入状态、训练 \(\epsilon=0.1\)、评价贪心；Adam `3e-4`、batch 128、256 transition warm-up、之后每宏步一次更新、每 256 更新复制 target、容量 32,768 的独立 replay。只保留 initialization 和完整训练结束点，不选最好检查点。输入归一化、Huber loss 与梯度限制在源码中一次固定。

这里有两个明确预测：

1. **学习取得：**L-final 相对其源代码同一的 L-initial/G 降低真实 C。
2. **竞争用途：**L-final 相对计价 R 的完整部署表现形成有用改进；如果只接近 R 但便宜，则必须展示包含训练投入的成本曲线。

即便二者成立，也只证明共享组链执行器上的联合排程学习。不能称为学会了底层组链、去中心化 MARL、技能发现，或证明某一种长时信用机制。L 的增量可能包含修正流体近似、减少反复切换及更长期权衡；这份比较不将它们强行拆成已识别因果。

与 A 的区别是这里购买 **native interaction 所取得的在线时序决策**，没有付费 teacher 标记的固定银行覆盖学习；与 C 的区别是信息接口固定，不学习编码器或接收器。

**4．我建议买一个完整三重复比较，不买筛选 pilot。**

- **三次独立 fit**：每次 512 个完整 H1200 任务，训练世界与随机流互不重用。
- **三个互不重叠的评价 block**：每个 fit 对应 32 个新世界；G、R、该 fit 的 L-final 共用该世界的实际请求 tape。L-initial 与 G 在主面板按可证明身份合并。
- **每 block 一个另外的审计世界**：执行 G、R、L-initial、L-final 四标签，检查初始身份及完整路径。审计不是选择模型的额外开发集。
- 不做中间 holdout、不找更好 checkpoint、不按结果改变请求率、预测深度或网络头；没有默认接续 fit。

| 完整新增量 | 数量 |
|---|---:|
| 学习 fit | 3 |
| 训练 native transitions | 1,843,200 |
| 主面板 native transitions | 345,600 |
| 审计 native transitions | 14,400 |
| **合计** | **2,203,200；1,836 个完整任务** |
| 训练宏 transition | 92,160 |
| 优化器更新 | 91,392 |
| Replay transition presentations | 11,698,176 |
| Double-DQN 更新 Q-row forwards 上界 | 70,189,056 |

R 在 99 个任务中的工作上界是 95,040 条候选预测，**15,206,400 个 model-tick**；真实数会因任务尾端及计算期限而减少。独立 reader 完整复算实际使用的 R 比较，worker+reader 上界 **30,412,800 model-tick**。若按每 model-tick 321 项物理关系计，约为 **97.63 亿关系计算**，不能藏在“零额外环境步”里。

完整 reader 应读取全部 300 条冻结任务，核验约 360,300 个状态的运动、服务、队列、目标和成本，并重算全部 G/R/L 决策；取消分支按已记录的确定前缀与取消事实核验，不能用 reader 更快的机器替换实验期限。所有训练队列/服务/动作记录、更新台账、终点权重与训练曲线也要全读。完整读取不等于再做三次 optimizer replay，不能把未购买的重训暗中列入确认。

统计单位必须保守：先在每个 block 内计算 32 个配对世界的均值，再读三个独立 fit/block 的增量与区间；三 fit 的不确定性不能伪装成 96 次独立训练。每个种子的完整正负结果都保留。若三 fit 仍区间宽，这就是本次完整购买的分辨率，不自动增加种子。

**5．全价不低；结果应改变实际选择。**

当前只能给出**规划估算**：约 **20–50 CPU-hours、0 GPU-hours、16–30 支持工时**；R 的原生分支吞吐与独立复算是最大未知项。若经工程构造发现完整价格明显超出这个区间，应在科学执行前更新整包账单，不能用“先看一点分数”决定是否补完。计划内 unique 证据约 2–4 GiB，另计必要 source snapshot；RSS 暂按不超过 8 GiB 设计，实际仍需规定节点的新鲜 admission。

应分开记录：

- native 训练与真实任务执行；
- 模型预测 tick、物理关系、网络前向与 optimizer；
- 在线每次决策的 CPU/wall、完成套数与取消损失；
- 所有请求的等待、未完成代价和用户长缺口；
- 初始化构造、实现、测试、读取、失败尝试及存储。

B03/B04、既有 S/A/R 的历史成本继续留在各自账本，不能因此变为零价。这里也不假定未来有无限次部署来摊薄三 fit。

| 实际结果 | 应改变的选择 |
|---|---|
| L 对 G 有稳定取得，并形成优于 R 的完整服务—成本点 | 保留这项条件明确的联合排程能力。只支持本契约与这份训练预算；向新到达律、规模或能源约束迁移是另外的问题。 |
| L 优于 G，但仍输给 R | 承认学习取得，保留普通前视的能力。若 L 更便宜，只能依据实际服务差与全投入均摊曲线判断是否有条件用途，不能宣布方法胜出。 |
| R 优于 G，L 无可靠增量或退化 | 得到一个有用普通排程程序；停止这份 RL 配方，不转入 head、entropy、种子或预测深度续修。 |
| G 已经与两者相当 | 直接选 G。新任务确有用途，但当前复杂度不需要额外规划或学习。 |
| 三者都不能取得足够请求服务 | 新契约的可用机会尚未建立；不能把共同失败自动归为学习问题，也不能凭旧 O 的满分宣布机会已证明。 |
| C 改善，但某簇积压、完成率或用户长缺口明显恶化 | 保留真实权衡，限制用途。主分数改善不自动产生采用结论。 |

我选择这一投入，而不选择普通 O 模仿或旧 SET 修复，是因为它能回答一个当前 A/C 不会回答的完整问题：**给定已经会执行的合作动作，原生经历能否取得值得使用的跨时段联合选择？** 阴性结果也会直接决定采用 G/R 或停止学习投入。它的理由不依赖“尚未解释的失败一定值得再研究”。

**6．一手资料给出的桥梁与边界。**

我检索了三库入口及七月、既往外部评审。`docs/new-libs` 的目录覆盖不能替代原文；检索不到也不构成不存在或新颖性证据。以下是实际承重的原文：

- **MARL-0553，*Hierarchical Multi-Agent Skill Discovery***：[结构化全文](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0553.json)、[PDF](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0553.pdf)，第 5–6 页算法与优化部分。**DIRECT：**论文同时学习高层协调、低层技能，并通过判别机制提供内在目标。**INFERENCE：**本方案给定低层射线执行器，因此不构成该技能发现机制的成功验证；这是有意缩小学习对象，不能借原论文声誉扩大结论。

- **`icml-2024-pmlr-v235-sivagnanam24a`，*Multi-Agent Reinforcement Learning with Hierarchical Coordination for Emergency Responder Stationing***：[本地 PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-sivagnanam24a/arxiv-2405.13205.pdf)，第 2–5、7–8 页；[官方论文页](https://proceedings.mlr.press/v235/sivagnanam24a.html)。**DIRECT：**随机请求下的主动资源重新布置确有完整服务用途；作者使用普通匹配/流分配与学习控制，并分别报告训练和在线决策代价。**INFERENCE：**它支持本题“已知执行能力之上的动态调度”构造，不提供本 UAV 宿主的阳性保证；其触发方式和对照条件也不能直接移植成我们的因果结论。

- **`icml-2024-pmlr-v235-li24be`，*When Do Skills Help Reinforcement Learning? A Theoretical Analysis of Temporal Abstractions***：[本地 PDF](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-li24be/arxiv-2406.07897.pdf)，第 2–6 页；[官方论文页](https://proceedings.mlr.press/v235/li24be.html)。**DIRECT：**其分析在明确的确定性、稀疏奖励等设定中区分技能的表达与学习困难。**INFERENCE：**给技能并不自动兑现学习收益；我们的随机请求、有限训练与中央排程不满足直接套用其保证的条件。

- **Bertsekas，arXiv:1910.00120，*Multiagent Rollout Algorithms and Reinforcement Learning***：[作者 PDF](https://www.mit.edu/~dimitrib/Multiagent_Rollout.pdf)，第 2–3 页 §1.1、式 1.2–1.3。**DIRECT：**使用基础策略的准确 cost-to-go 和相应期望，可得到 rollout 改进性质。**INFERENCE：**本方案的有限采样、截断与近似终端不继承该保证；它只给出一个应当认真构造的普通替代，实际优劣仍由完整原生结果决定。

七月的[底座失败复盘](/home/fires/hmasd-wsl/docs/research/decisions/R35_R40_SUBSTRATE_FAILURE_REVIEW_20260715.md)与[九月外部基础评审](/home/fires/hmasd-wsl/docs/Claude_docs/reviews/FOUNDATIONS_AND_METHODOLOGY_CRITICAL_REVIEW_20260914.md)要求我保留正面能力、承认宿主与算法间的未证前提。这次继承的是已经测到的几何执行能力和普通前视价值，不是假定 HMASD 在改写任务后自然有效。

我没有编辑、实现、训练或评价新方案，也没有把它宣称为新颖方法。我的原始建议是购买上述一个完整问题；对旧 B03/B04 学习资产的直接修复则停止投入。
````

<a id="request-scheduling-corrected-contract-20261002"></a>
#### 2026-10-02 — Source-reviewed complete candidate, before the investment review

This is the candidate the DM asks the independent ResearchCritic to challenge.
It is still source-only design, not an accepted launch or implementation scope.
The question is whether experience improves complete **centralized request
scheduling with a supplied, common three-pair executor**, at a useful service
and computation price. The intended contribution is an empirical answer and
a potentially useful learned scheduling capability. It is not a new-method,
decentralized-MARL, HMASD, learned-geometric-skill or B03-failure-cause claim.
No score from the new task exists. The task is fixed here without searching
rates, horizons, maps or seeds for learner headroom.

**Original evidence and primary-source reading.** B03/B04's complete positive
and adverse reading above remains controlling. O's128/128 old scheduled
windows is an old-task capability, not proof of the new simultaneous-request
problem. B04's five newly sustained off-calendar visits coexist with the
5-to2 mean-window loss, and do not identify a scheduling cure. The nearby
service-age comparison (its NOTES436–547), parent CONT (8852–8945) and fleet
A2/G2 (fleet NOTES2421–2500; parent retained-cost NOTES8316–8378) were read in
their original contexts: initialization gains, less travel, and genuine
planning gains each differ from complete comparative usefulness.

The DM read Sivagnanam et al., `icml-2024-pmlr-v235-sivagnanam24a`, local PDF
`/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-sivagnanam24a/arxiv-2405.13205.pdf`,
pp2–5 and7–8, and its [official PMLR page](https://proceedings.mlr.press/v235/sivagnanam24a.html).
DIRECT: their emergency-response problem combines assignment, repositioning,
ordinary matching/flow machinery, hierarchy and learning, and reports both
training and online computational costs. Their trigger, task and architecture
search differ; their low-level training takes1–14 days and high-level training
about2 days. INFERENCE: supplied execution plus uncertain future demand can be
a substantive learning object; neither their gains nor their budget transfers
to this UAV contract. The full relevant HMASD structured-source passage,
`/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0553.json`, pp5–6, concerns
its learned hierarchical exploration setting; our supplied executor does not
test its skill-discovery mechanism. Li et al., `icml-2024-pmlr-v235-li24be`,
local PDF at the corresponding `pmlr-v235-li24be/arxiv-2406.07897.pdf`, pp2–6,
defines learning/exploration difficulty in deterministic sparse-reward MDPs;
the stated skill/incompressibility bounds do not cover this stochastic,
finite-horizon request process. No such guarantee is claimed here.
Bertsekas, arXiv:1910.00120, [author PDF](https://www.mit.edu/~dimitrib/Multiagent_Rollout.pdf),
§1.1 pp2–3 Eq1.2/1.3, gives the ordinary rollout comparison with the base
policy's cost-to-go and corresponding expectation. Our sampled, truncated,
deadline-censored R does not inherit that improvement guarantee. These are
load-bearing source passages, not reliance on generated library hints.

The July R35–R40 failure review and the September14 foundations review were
also checked directly. Their relevant adverse lesson is not to declare a
custom task a successful learning substrate from expressivity or from a weak
baseline, nor to treat one policy's evaluation worlds as independent training
replications. Their historical route instructions and quotas are not new
authority. Here a common constructive executor, strong G/R, three independent
fits, fixed complete endpoints and a scoped negative result address that
lesson; they do not establish learnability in advance or remove the cost risk.

**Host and opportunity located in source.** The relevant B03 registry,
`ordinary.ray_slots/steer`, host movement, free-space/FDMA association and
routing code were read, first through CodeGraph and then their required exact
sources. The new wrapper would initialize the real host with `max_steps=1200`
and check that contract; it must not call B03's fixed500 checker and ignore
later `done`. It retains6 UAVs,50 users,23dBm transmit power,−80dBm noise,
3dB eligibility,2GHz carrier,10 associations/UAV, max3 backhaul hops, static
users, FDMA, no shadowing, one central BS at(2500,2500,30), the existing
30m/s bounded motion and `dt=1s`. All six transmit. No collision, battery,
traffic-throughput or radio-contention consequence is newly invented.

The same map law has four nominal corners (500/4500), coordinate jitter±50,
and each integer-rounded user within101m of its cluster centre. Let the
centre-to-BS horizontal distance be R<2900m and the user-mean displacement
be≤101m. A pair settled at its1/3 and2/3 mean-ray slots, z=100, has each
own-cluster user within
`sqrt((2900/3+101+2*101/3)^2+100^2) <1140m` of its outer member. The native
free-space eligibility radius is about1193.662m. Inner-to-BS and outer-to-inner
distances are<1004m; two backhaul hops suffice. Other far clusters and the
central users cannot fill this settled outer member's10 slots: their minimum
distances exceed the same link range, while its own ten are eligible. Thus,
conditional on all three distinct pairs being settled, the source geometry
supports simultaneous routed service of their three clusters. This is a
conditional construction with a substantial distance margin, not a rollout,
an all-arrivals completion guarantee, or a claim about transient association.
Actual in-transit interference through association/routing and arbitrary
initial positions still require the selected native comparison.

The arrivals have expectation57.6/mission, whereas three settled pairs could
finish180 requests over1200 ticks, or144 during the960-tick arrival period.
The offered load is therefore32% of whole-horizon,40% of arrival-period ideal
capacity. Strong G may already be sufficient; this is the main ordinary
explanation to retain. Spare total capacity does not remove travel: an outer
slot transfer between adjacent/opposite nominal corners takes roughly89/126
ticks at maximum speed, before the common20-tick command delay and a new
20-tick service run. Native eligibility can begin sooner than slot arrival.
Four spatial queues compete for three pairs, with interrupted head progress,
unrevealed future arrivals and a terminal backlog charge. This gives a real
finite scheduling decision, but neither a lower bound on G's regret nor a
prediction that the residual must improve it. No preliminary native headroom
panel is proposed.

**Exact request, state and boundary contract.** H=1200 primitive transitions,
indexed t=0,…,1199. Reset draws the same geometry/UAV-initialization law and a
separate random permutation of probabilities[.6,.3,.2,.1]. At each
t∈{0,20,…,940}, each cluster independently receives0/1 request. The four
probabilities are public at reset. The actual arrival tape belongs only to the
task; no G/R/L callable receives its RNG or unread suffix. Each fit uses512
independent training worlds; there is no reuse of a training tape at evaluation.

At t=0, all queues/progress start empty/zero, targets are initialized as below,
then the t=0 arrivals are appended. At each later decision boundary t<1200,
the command selected at t−20 is promoted to active targets, the new arrivals
are appended, and the public report is emitted. The policy selects a pending
command for t+20. Until then the active targets continue executing. At each
primitive tick, charge the sum of queue lengths **after that tick's arrivals
and before service**, execute the one native move, then use the post-movement
routed-user ACK mask to advance the FIFO ledger. A nonempty cluster with≥8
of its ten users routed increments its head's progress; otherwise progress is
zero. At progress20 remove exactly one head at the end of that tick and reset
progress to0, even when another request remains. An empty queue has progress0.
No head receives credit for service before its arrival. Completion time is
t+1; FIFO arrival times permit all residence/tail statistics without changing
the scheduling interface.

At1200 there is no arrival, report for a new action, promotion or service.
Add `240 * sum(terminal queues)` exactly once. The pending command selected
at1180 is never actuated and is counted as terminal-unused, not a useful
intervention. The final read-only report is allowed for accounting. The
objective is
`C = sum_t sum_c N_c(t after arrivals, before service) + 240*sum_c N_c(1200)`.
Its units are request-ticks of **unfinished-request residence**, including the
20 successful service ticks, not waiting-until-service-start. For each request,
its area contribution is completion-minus-arrival or1200-minus-arrival if
unfinished. Training and evaluation use this same nonnegative cost.

All arms get the full50-user map, public rates, float64 six-UAV positions,
current50-user ACK mask, four queue counts, four0…19 head progresses, six
active slot IDs and integer clock. Fixed pair membership is deterministically
reconstructed from the common initial report/map/rates. There is no current
pending command at the report boundary after promotion; within a macrostep it
is stored explicitly by the task/model. Arrival ages need not enter control:
future cost under this objective depends on current counts/progress, not each
head's already-incurred residence; ages remain in the outcome ledger.

The404-byte reset payload comprises50×2 little-endian int32 map coordinates
and four uint8 probability codes[6,3,2,1]. A171-byte report comprises18 float64
positions(144), packed ACK(7), four uint16 queues(8), four uint8 progresses(4),
six uint8 slots(6), and one uint16 clock(2). Unused ACK padding bits are zero.
The command is six uint8 target-slot IDs. Sixty operational report/command
cycles therefore use11,024 logical payload bytes including reset. The terminal
accounting report adds171, giving11,195; training additionally returns one
uint32 macro cost60 times,240 bytes, giving11,435 for that declared training
interface. Simulator bulk logs and branch IPC are separately counted, not
hidden in this payload. Headers, retransmission, reliability, energy and real
radio scheduling remain unmodeled, so these are not air-interface costs.

**Common executor and action set.** Four far clusters each have fixed inner/
outer slots at1/3 and2/3 of their mean ray, height100. At reset select the
three largest public rates, ordered by cluster ID for slot enumeration. Assign
six UAV IDs to their six slots by enumerating6!=720 permutations and minimizing
`(sum ceil(distance/30), sum distance, permutation IDs)`; pair membership then
remains fixed for the mission. This assigns targets, not initial positions:
there is no teleportation. Pair IDs follow the selected-cluster order. At each
boundary there are exactly four actions: KEEP(ID0), or move pair0/1/2(ID1/2/3)
to the cluster missing from the three active pair targets. No two pairs target
the same cluster. For a moved pair's inner/outer assignment, use the current
reported positions and lexicographically minimize `(max ceil(distance/30),
sum distance, UAV IDs)` over its two orientations. Do not silently use the
future positions at command activation. The same deterministic action mapping
is used by G, R, L and their model continuations. At each real tick each UAV
steers from its own current position to its active target using the original
bounded `steer`, including the host's float32 action/movement order.

**G, strengthened before comparison.** The original Oracle's
`N−progress/20` fluid initialization would discount a still-pending head from
the native residence objective and can preserve service work through a native
interruption. The independent critic and DM identified this avoidable weakness
before any new score. Replace it with exact known integer heads plus a fluid
approximation only for future unknown jobs.

For each candidate, simulate `h=min(240,1200−t)` tick predictions with the
current targets for the first20 ticks and the candidate targets thereafter,
holding them for the rest of this G horizon. Predict straight-line bounded
motion at30m/tick from the current report, without an RF call. A cluster is
predicted available only after both members of its assigned pair are within1m
of their slots. This1m convention absorbs harmless kinematic rounding and is
far inside the conditional link margin above. It deliberately misses service
before arrival, cross-pair transient help, and native association variation.
At each future arrival boundary strictly after t and≤940, add the public
probability to a separate expected queue F behind the observed integer queue N.
Start F=0 and preserve observed head progress r. Before service accumulate
`N+F`. If available and N>0, increment r and remove one integer head only at20,
then clear r; no F service is also taken on that tick. If available and N=0,
clear r and drain `min(F,1/20)`. If unavailable, clear r and do not drain either
queue. Finally add `240*(N+F)` at the prediction horizon, including when it is
the real terminal horizon. Sum over clusters. Future fluid mass remains an
approximation, including fractional service across interruptions; it is not
described as an expected exact native queue. Choose `(raw float64 Q_G, actionID)`
minimum. All four candidate costs are computed, so KEEP is a real option.

G has no fitted parameter or private tape. Its known-head correction, full
four-way costs and future-rate rights are also supplied to R/L. Its residual
errors are not deliberately retained to make learning easier. Cache the exact
four Q_G values and candidate features once per collected macro state; replay
must never quietly recompute millions of fresh G calls. Caching is correct
because these values depend on the fixed public state/model, not network
parameters. A later G revision would be a new comparison, not a free update
to one arm after seeing scores.

**R and an enforceable deadline.** R first computes the same four-way G for
fallback. It then evaluates four first actions with up to four common sampled
future-arrival tapes, in complete four-candidate cohorts. For each candidate,
use the native physical model for `d=min(160,1200−t)` steps, the exact integer
FIFO rule, common20-tick command pipeline, and G continuation at each later
20-tick boundary. At the end, if nonterminal, add `min_a Q_G(s_end,a)`; if
terminal, add the actual240-times-backlog cost with no bootstrap. Candidate
scores average full C estimates only over completed cohorts; tie by raw G and
action ID. This is truncated stochastic rollout with an approximate terminal
value, not the exact rollout theorem.

The initial model state is reconstructed exclusively from public geometry,
positions, clock, targets, counts and progress. A full task-wrapper clone is
forbidden because it could carry the actual future-arrival tape. Any initial
RF reconstruction is counted; a single public-state reconstruction may be
shared across the candidate copies. R future draws use a distinct stateless
SeedSequence domain `(R root, world, decision index, tape index)` and never
advance the actual-arrival, fit-exploration or replay streams. Candidates in a
cohort share that tape. Fixed rotated candidate order by world/decision/tape
index prevents one action always occupying the first cancelled prefix; only
complete cohorts affect choice. The public rate law, not actual future bits,
drives these draws. No R trajectory, score or chosen action is a training label.

The20-tick physical command delay equals20 simulated seconds, and the decision
deadline is20 measured wall seconds from receipt of the public report. G, R
and L all use that same command activation time even when faster. Actual task
simulation may execute after computation without exposing later reports to it;
this models a measured computation budget and fixed actuation latency, not a
claim to have built a live real-time radio system. A dedicated sequential
decision process is bounded by a parent monotonic-clock deadline. On expiry
the parent terminates the process group, escalates to kill if needed, joins/
reaps it, and never lets old work run into the next decision. Process start,
IPC, serialization, initial model construction, all completed/cancelled work,
and reap overhead enter the bill. A20s report-to-ready miss is recorded even
if termination takes longer. If G fallback is ready before expiry, R uses it
when no cohort is complete; if not, all arms use KEEP. L/G deadline failure
also falls back to KEEP, never a free fresh late G call. R's completed-cohort
count is part of the executed policy and may depend on state/contention;
deadline censoring is not an unbiased four-tape estimator.

The process writes to parent-owned bounded trace storage. A step/query attempt
is registered before entry; its completed payload is committed before raising
the completion counter. Parent reads it only after process completion/reaping.
An in-flight interrupted call remains an attempted, CPU-paid incomplete call,
not a fabricated completed tick. Save completed cohorts, unused complete
candidates, cancelled-prefix lengths, counters and child CPU, plus every
selection/ready/deadline/cancellation fact. Reader reproduces only recorded
completed prefixes and finished G queries; it must not complete an interrupted
step/cohort, grant additional tapes, or substitute a faster reader's deadline
for the actual selection. This contract requires independent engineering review
before any execution; it is not already-validated cancellation code.

**L, numerical initialization and learning.** For each action the scorer takes
303 fixed features: normalized user coordinates100, public rates4, normalized
positions18, ACK50, queues/48(4), progress/20(4), fixed6×3 pair-membership onehot18,
six current-slot onehots48, six candidate-slot onehots48, action onehot4,
clock/1200(1), and all four `Q_G/1200` values(4). XY normalize by5000, height
as(z−50)/100. No fitted normalizer, clipping of large queue costs, dropout or
R teacher is introduced. The residual is `303→128 ReLU→128 ReLU→1`,55,553
parameters, float32; hidden-layer initialization has its own fit RNG, output
weights/bias are exactly zero. The baseline Q_G remains canonical float64.
Form `Q_hat = float64(Q_G)/1200 + float64(f_float32)` and choose the
lexicographic minimum `(Q_hat, raw Q_G, actionID)`. With zero residual this
matches G even if division makes two distinct raw G costs round to the same
value. Both source checks and the three initial/G audit paths must verify the
claim; zero output alone is not accepted as a float32 equality argument.

Fit three independent instances, each512H1200 missions,60 macro transitions/
mission. Collect all four network rows even on exploratory steps. Training
epsilon=.1 chooses uniformly over all four actions from a separate RNG;
evaluation is greedy. Use a32,768-transition fit-private replay (the30,720
transitions fit without overwrite), first256 transitions with no update, then
one update after each later transition. Sample128 distinct indices uniformly
from current replay, with a distinct replay stream. There are30,464 updates/
fit,91,392 total. Adam lr3e−4, betas(.9,.999), eps1e−8, no weight decay,
Huber delta1 averaged over rows, global gradient-norm cap10; copy online to
target initially and after each256 updates (119 copies/fit after start).

For each20-tick transition the nonnegative macro cost contains all20 residence
charges; the final transition additionally contains240-times-terminal-backlog.
With gamma=1, use the cost-form Double-DQN target
`y = c_macro/1200 + I(nonterminal) * Q_hat_target(s_next,argmin Q_hat_online(s_next))`.
The online argmin uses the same float64 baseline/tie rule, the selected target
value uses its own target residual, and both baseline terms come from cached
canonical G values. The loss compares y against the chosen current action's
Q_hat; terminal samples have no next evaluation/bootstrap. Time is part of
state. Stop-grad targets; no sign inversion or extra reward term. Keep only
the initialization and final endpoint for deployment; retain training curves,
updates, seeds, action/Q/cost records, finite checks and checkpoint identities,
but do not choose a best checkpoint. All preprocessing/G, forward, backward,
optimizer and bookkeeping costs count. Native acquisition may fail or plateau;
there is no promised learning result or automatic fit extension.

**The complete comparison, corrected for shared ordinary work.** Use one common
fresh32-world evaluation panel for all three independently trained endpoints.
Run G and R once per world and each of the three L-final policies once. Add
three distinct audit worlds, one per fit, each running G/R/L-initial/L-final.
Thus training is1536 missions; main evaluation160; audits12; total1708H1200,
2,049,600 native steps, three fits and no teacher labels. This replaces the
Oracle's three separate32-world blocks. It retains three independent acquired
policies while buying32, not96, evaluation worlds; common-world responses and
shared R realization must not be described as independent across fits.

Literal training/evaluation/initialization/R/exploration/replay seed domains
would be committed before implementation checks and result execution if Root
selects this package; they are not consumed or searched now. Main/Audit/G/R
results may not select a model, training horizon or task revision. Read all
training missions, all172 frozen missions and all paid R prefixes. Replay
movement, native masks/physical rules, integer ledgers, costs, targets and
decision timings from saved traces; independently verify all collected G
caches and all frozen L neural decisions. Read the full training action/Q/
update ledger and learning curves, but do not claim an independent replay of
the91,392 optimizer updates or of each changing training network. That would
be an additional purchase. Save enough primitive fields to verify every
training request/service event; preserve all adverse missions, deadline misses
and incomplete prefixes.

Primary contrasts are each fit's world-paired `C(L_final)−C(G)` and
`C(L_final)−C(R)`, with C(R)−C(G) as the ordinary-model comparison. Report each
32-world paired distribution and each of the three fit means; the across-fit
t interval has only2 degrees of freedom and is conditional on this32-world
panel. A world-resampling descriptive interval for the average of the three
fixed policies has a different conditioning scope; no96-world/96-fit fiction
or precise universal reliability claim follows. There is no arbitrary new
minimum-effect threshold invented to force a binary verdict.

Read completed/unfinished requests, residence p50/p90/max, per-cluster backlog,
head interruptions, service and full50-user gaps, team-zero-service runs,
travel, target switches and deadline/cancel tails. A different argmin is not
yet a used intervention: join decision→pending activation→changed movement→
changed native request completion/cost, marking the final unused command.
R/G/L action disagreement at different visited states is not a causal policy
ablation. Better scheduling C cannot substitute for safety, energy or continuous
fair service. If L improves G but loses R, retain genuine acquisition and its
use limit. If it matches R at lower deployment CPU, show the training-inclusive
cost curves `training CPU + N*deployment CPU` and break-even N only when the
denominator is positive, separately for each fit and their total research cost.
No scalar exchange rate between request-ticks and CPU is invented. If G already
suffices or both alternatives lose, that is a useful scoped negative result;
it does not refute learning on other tasks. Complete this one package then
reconsider; no default additional seeds, pilot, task retuning or action-head fit.

**Complete count and price envelope.** These are prospective arithmetic bounds,
not measured throughput. Caching avoids eleven million hidden G recomputations
during optimization. Reader counts below include all1708 native trajectories,
all their G caches, all102 frozen neural missions, and the actually paid R work.

| Purchased item if selected | Complete count / upper bound |
| --- | ---: |
| Independent fits / training missions | 3 /1536 |
| Training native / macro transitions | 1,843,200 /92,160 |
| Frozen missions / native / macro transitions | 172 /206,400 /10,320 |
| Total new native transitions | 2,049,600 |
| Optimizer updates / replay presentations | 91,392 /11,698,176 |
| Update Q-row forwards, terminal-skipping upper bound | 70,189,056 |
| Training collection Q rows | 368,640 |
| Frozen Q rows / matching reader Q rows | 24,480 /24,480 |
| Total worker+reader network Q-row upper bound | 70,606,656 |
| Backward chosen-row presentations | 11,698,176 |
| Native-trajectory independent reader physical states | 2,051,308 |
| Their321-relation physical items | 658,469,868 |
| R missions / attempted decision deadlines | 35 /2100 |
| R model primitive-step upper bound, worker | 5,062,400 |
| R model primitive-step upper bound, worker+reader | 10,124,800 |
| Those R-tick321-relation items | 3,250,060,800 |
| Extra R initial-state RF reconstructions, worker+reader upper bound | 4200 states /1,348,200 relations |
| Collected-state G queries, worker+reader | 204,960 |
| R continuation/tail G queries, worker+reader upper bound | 497,280 |
| All G candidate-prediction ticks, worker+reader upper bound | 608,805,120 |
| Corresponding G cluster-tick recurrences (four clusters) | 2,435,220,480 |
| Native reset assignment permutations, worker | 1,229,760 |

Each full R mission has `16*(53*160+140+120+100+80+60+40+20)=144640`
model steps at most. Tail clipping gives7104 internal four-action G queries/
mission at most, not60×16×8 with a non-existent terminal bootstrap. Completed
prefixes only can make these actual counts lower; failed attempts/cancel CPU
remain charged. Main G horizons yield52,320 candidate-ticks/mission; R's
internal G yields at most6,144,000 candidate-ticks/mission. Source-only
arithmetic evaluated these sums without importing a model or simulator.
There are also native host reset/initial-RF computations, decision-action
mapping/orientation/distance work, clones, summaries, training backprop/Adam,
and prefix I/O. Those are separately metered in the complete implementation;
the table is not a claim that relationship counts exhaust the CPU bill.

Two new read-only metadata passes verified all66 paid B03 O/B metadata file
sizes/hashes against the old manifest, without raw trajectory execution. Old
O33H500 bodies used18.345258739 CPU-s, median.553492531/mission; B used
16.482380450, median.495361005. Mean CPU/tick was.001111834/.000998932.
These put the retained native ordinary host near1ms/step in that past setup,
not a promise about new queue code, G, branch construction or deadline success.
The two metadata-read processes themselves used.028091294 and.024688866 CPU-s.
Other source/literature/arithmetic/authoring work is not fully metered and is
not zero. Prior B03/B04 costs remain separately retained above.

The DM's current planning estimate remains **20–50 CPU-hours,0 GPU-hours**,
roughly8–24 compute wall-hours depending on deadlines/reader throughput.
The complete R decision-deadline sum alone is at most11.667 wall-hours before
reap/start and other work; that is not a runtime prediction. Engineering,
review, implementation, collection and scientific reading are more substantial
than the Oracle's first estimate: budget **24–40 human/agent support hours**,
including this preparation, with elapsed/model usage reported in their actual
units rather than claiming all are measured human labor. The largest unknown
prices are G's2.44-billion small recurrences, trace/cancel handling, full reader
and training. Vectorizing candidate/cluster axes and caching are ordinary
implementation rights for G/R/L, not silently discounted work.

Expect roughly4–8GiB of unique evidence before compression/retention selection,
including all training features/primitive ledgers, model prefixes, complete
frozen evidence and compact readings; original2–4GiB is not treated as a
verified bound. One source snapshot adds about1.8GiB based on B04; sequential
worker/reader source GC avoids two live copies. Plan6–10GiB additional peak
disk and an8GiB actual-node RAM admission floor; peak RSS is presently unknown
(streamed traces and per-fit replay plausibly fit2–4GiB). Existing canonical
raw/checkpoints stay in place without copies. The full package would have a
50-CPU-hour cumulative scientific/check/reader watchdog and the exact exposure
ceilings above, with no retry or extension inferred from completion/failure.
If implementation reveals a material cost/interface change before any result
effect, return the revised complete price to Root; do not run a scored pilot
to justify it. A hard resource stop would be technical incompleteness, not a
negative learning result or permission to extend. Node admission is deferred
to an actual selected launch; no health query was made for this design.

**DM provisional investment view, to be challenged.** I lean toward one full
corrected comparison if Root values this supplied-executor scheduling question
at the above price, because it would distinguish acquisition, correction of
an ordinary approximation, and complete deployment value in a genuine dynamic
allocation problem. The strongest reason to decline is that low load and a
competent G may leave little substantive learning need, while the new queue/
deadline/reader infrastructure costs24–40 support hours and offers no guaranteed
novel method. Three fits do not solve training variance or prove sufficient
training. Choosing no purchase remains defensible; there is no missing pilot,
proof, result rescue or external dependency that forces continued investment.
The independent critic receives this exact integrated contract and original
adverse sources before its final recommendation. Root chooses the eventual
full purchase after reading that original review and the DM disposition.

<a id="request-scheduling-exact-reuse-20261002"></a>
#### 2026-10-02 — Exact ordinary reuse correction before final review

The critic identified one further competent ordinary right before finalizing
its review. At t≥940 the public report already includes the last possible
arrival, so every future tape is empty. R must not compute four identical
deterministic cohorts merely to average them. Sample at most four logical
tapes as before, but reuse a completed cohort with multiplicity whenever its
complete public start state, candidate definition, future-arrival bits and
model/horizon identity are exactly equal. Earlier finite tapes that coincide
receive the same treatment. Preserve tape multiplicities, unique-computation
counts, and the evidence locator for each reuse; cached copies are not new
model calls or independent Monte Carlo samples. A digest is only an index:
validate exact serialized inputs before reuse. This preserves the specified
sample mean and complete-cohort action selection while reducing computation.
The deadline can therefore admit more distinct paid work; its final measured
policy/cost, including reuse, is the comparison of interest.

Exact physical-transition reuse across candidate prefixes is also permitted
where every relevant physical input/action and map identity agrees. Queue
reuse additionally needs the same counts, progress, arrivals and command
pipeline; never infer equality from a matching action label or position alone.
The common first20 physical steps are an obvious possible reuse location,
but their implementation/price is not assumed free or certified here. Keep
logical versus computed prefix/transition counters and source identities.
Independent reading verifies each unique saved prefix once and its reuse
joins, rather than purchasing deterministic copies. This retains the project's
existing exact-reuse capability without adding search depth or tape tuning.

The preceding R/G count table is a conservative **pre-reuse** bound and is
superseded for the proposed implementation by the following tighter maxima
from mandatory empty-tape reuse alone (earlier collisions and valid prefix
reuse can reduce actual work further). At t<940 at most16 candidate branches
are computed, and at t≥940 at most4. Native exposure, neural rows, fits,
ordinary initial-state reconstructions and collected-state G queries do not
change.

| Revised actual-computation upper bound | Count |
| --- | ---: |
| R model steps per mission /35 missions worker | 126,400 /4,424,000 |
| R model steps worker+reader | 8,848,000 |
| Their321-relation physical items | 2,840,208,000 |
| R internal G queries per mission /worker+reader | 6288 /440,160 |
| R internal G candidate-ticks worker+reader | 406,963,200 |
| All collected/R G candidate-ticks worker+reader | 585,688,320 |
| Their four-cluster recurrences | 2,342,753,280 |

The whole-package20–50 CPU-hour and24–40 support-hour planning estimates stay
uncertain rather than shrinking by a made-up proportional factor. Source
arithmetic, not any native/model query, produced this correction. It is a
comparator-quality correction, not evidence that R or L will improve C.

<a id="request-scheduling-initial-program-correction-20261002"></a>
#### 2026-10-02 — Initial-program identity and travel correction during review

After reading the whole integrated candidate, the independent critic found
that mathematical zero-head argmin equality does not by itself imply equal
**executed** behavior under a20s deadline: L-initial could pay neural/process
overhead and fall back to KEEP where G finishes. Three matching audit paths
cannot establish universal deadline equality on the aliased main panel. The
DM accepts this distinction and corrects the prospective deployment contract:
the certified zero-output initialization **uses the canonical G execution
path**, including the same decision process, fallback and deadline behavior.
Its initial checkpoint/output-layer certificate is checked and charged at
startup. L-final uses the actual neural scorer and pays its complete inference/
process/deadline cost. The initial/G alias is therefore defined by their shared
deployed program, not extrapolated from three empirical audit matches.

The three separate initial audit missions remain in the fixed native total.
On their saved public states, separately verify the zero neural output,
float64/raw-G tie rule and action identity for all60 boundaries, outside the
deployed decision deadline. Charge720 Q rows to these worker-side audit checks
and720 to independent reader checks. Actual L-final deployment and neural
reader each use23,760 rows. Their sums are still24,480 each, so the earlier
70,606,656 overall Q-row upper bound and all native/fit counts are unchanged;
the table's generic frozen-Q label includes these explicit audit checks.
This is not a free online neural call or a claim of zero startup/support cost.
Training retains its declared all-four-row collection and exploration, so
its initial exploratory behavior is not claimed to equal G's greedy behavior.

The critic also corrected the simple travel illustration. The preceding
89/126-tick figures apply to an outer UAV staying the outer member. The actual
declared two-orientation min-max assignment can swap inner/outer roles: for
nominal adjacent/opposite corners its maximum flight is instead
`ceil(sqrt(2000^2+(2000/3)^2)/30)=71` and
`ceil(sqrt(2000^2+2000^2)/30)=95` ticks. Those, plus the common20-tick delay
and new20-tick run when needed, are the appropriate nominal scheduling scales.
They remain illustrations, not measured native blackout durations: rates,
initial positions, jitter, source rounding and useful service before slot
arrival still matter. The lower travel price strengthens the credible
ordinary-G-sufficiency alternative; it does not eliminate scheduling or
establish learner headroom.

For an exact source locator, the Li et al. PDF read above is
`/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2024/pmlr-v235-li24be/arxiv-2406.07897.pdf`.
The phrase about transient interaction in the opportunity paragraph refers
to native association/routing competition, **not RF interference**, which
remains absent in the fixed FDMA host. These corrections precede the final
investment recommendation and any scientific effect.


<a id="request-scheduling-independent-review-20261002"></a>
#### 2026-10-02 — Complete original independent investment review

The registered ResearchCritic reused its separate context, reconstructed the
original supportive/adverse evidence before reading the DM preference, then
read the complete integrated candidate and both accepted corrections. This
was not a blind review and the proposal-author Oracle was not treated as an
independent critic. No new host/controller/model/fit/health call was made.
The complete final answer below is preserved without abridgment:
14,059 characters, 14,111 UTF-8 bytes, SHA256
`389d78cdf9b30d66dffbab1fc868c0b2847f065194b6c688718c1cc1835b2b24`. Its recommendation covers the corrected
single exploration and is advice to Root, not execution acceptance.

````markdown
**Recommend one complete exploration under the corrected contract.** Retain the new scheduling question and the accepted revisions: common evaluation worlds, strengthened G, exact R reuse, and the canonical G execution path for L-initial. At the stated **20–50 CPU-hours and 24–40 support hours**, I judge this worth one bounded purchase. The superseded three-block package, a score-screening pilot, and automatic follow-on fits are unsupported.

I reused this ResearchCritic context as requested. I reconstructed the new question against primary evidence before reading the proposal-author Oracle and the DM’s investment preference. This is a source-only selection review; there are no new task outcomes. The prior B03/B04 closures remain intact.

The useful question is whether native experience can acquire better **centralized scheduling of supplied cooperative actions** under new requests, travel, interrupted service and reassignment costs. A positive would establish that conditional capability. It would not establish learned ray construction, skill discovery, decentralized MARL, or an explanation of the old SET failures.

The evidence supports asking this narrower question, while keeping expectations modest:

- The prior independent B03/B04 reconstruction remains applicable. O’s 128/128 scheduled-window success establishes capability on its old task. B04’s final mean lost scheduled successes while adding some sustained off-calendar visits. Those observations neither establish the new queue opportunity nor identify scheduling as a repair.
- I independently checked the service-age paired vectors: learning improved its own initialization, but the final learner remained worse than ordinary M; the reported cost difference was about **+0.269**, with descriptive interval **[0.069, 0.469]**. Acquisition and comparative usefulness separated there.
- I checked the fleet’s native world summaries and the primary B08 reuse result. A2’s mean J gain over G2 was **0.001706**, with six gains and ten ties, heterogeneous service/path consequences, and substantial concentration in one world. Exact reuse preserved the physical outcomes but still left A2 at **2.888 times** G2’s measured worker-plus-reader CPU. Useful foresight exists in the project; its value and price are conditional.

The new contract supplies a more specific opportunity than “the old learner failed, so try another learner.” I read the registry, ray construction, motion, FDMA eligibility, association and routing sources directly. For the declared map bounds, conservative settled-pair distances are approximately:

- inner UAV to BS: at most **1,002.4 m**;
- inner to outer UAV: at most **999.95 m**;
- outer UAV to each own-cluster user: at most **1,125.25 m**.

These fit inside the roughly **1,193.66 m** native eligibility radius. Other users cannot occupy the settled outer member’s ten association slots, and its two-edge backhaul path is admissible. Thus three settled pairs can concurrently serve their three own clusters under the declared host law. This is a source deduction, not a new physical evaluation.

That deduction establishes stationary service opportunity. It does not establish complete request service, useful learner headroom or G’s regret. The strongest simpler alternative remains **ordinary G competence**: expected arrivals use only 40% of ideal settled capacity during the arrival period, with a further drain period afterward. The corrected nominal reassignment scales—**71 ticks adjacent and 95 opposite**, plus the common command delay—also strengthen this alternative compared with the original outer-to-outer illustration. Actual service can begin before waypoint arrival.

Nevertheless, four queues sharing three pairs still create consequential decisions. Moving a pair exchanges service opportunity between clusters, can discard head progress, and commits travel while future arrivals remain unknown. The proposed observation can change whether this owner retains G, R or a learned scheduler. Its information value does not require a preliminary positive panel or an exact headroom proof.

The accepted construction makes that comparison credible:

1. **The objective and boundaries are sufficiently explicit.** C measures unfinished-request residence, including successful service time, plus the terminal backlog charge. Arrivals, pending-command promotion, reporting, movement, service and completion have a declared order. The final command is causally unused and remains marked as such. Counts, progress, positions, active targets, public rates and time provide the relevant control state for this objective; past request ages remain available for outcome reading.

2. **G now treats observed requests competently.** Known FIFO heads retain their full residence cost and lose progress on predicted interruption. Only unknown future work uses the fluid approximation. G remains approximate: fractional future service, waypoint-based availability and omitted transient routing can create errors. Those are declared comparison properties, not demonstrated causes of future learning gains.

3. **R supplies the consequential ordinary comparison.** It uses the same public state and arrival law, reconstructs model state without the private actual-arrival suffix, and charges model work, initialization, cancellation, IPC and deadline losses. Completed cohorts define its executed policy. They do not provide an unbiased four-tape estimate or Bertsekas’s exact-rollout guarantee.

4. **Exact reuse belongs in the ordinary comparator.** After the tick-940 report, future arrival tapes are empty. Paying for four identical cohorts would inflate R’s cost without improving its estimate. The addendum correctly requires exact input identity, preserves multiplicities and reuse joins, and recognizes that faster execution can admit more distinct work before the deadline. The efficient, deadline-limited R is the program to freeze before results.

5. **L-initial’s deployment identity is now properly defined.** Zero residual output proves the mathematical argmin identity, including the float64/raw-G tie rule. It does not prove identical deadline behavior when neural overhead differs. The accepted correction uses the canonical G execution path for deployed initialization and bills the zero-head neural checks separately on saved audit states. L-final pays its actual neural and deadline costs. Training’s exploratory behavior is appropriately excluded from the initialization-equals-G claim.

The cost-form Double-DQN specification is coherent at this design level: nonnegative macro costs, fixed normalization, finite-horizon gamma one, time in state, online minimum with target-network evaluation, terminal bootstrap removal, separate random streams and cached canonical G values. This is not an engineering correctness certification of code that has yet to be implemented.

I recommend the **three independent fits on one common fresh 32-world panel**, with the three separate audit worlds retained. Sharing G/R outcomes keeps the training replication and removes a large purchase of repeated ordinary evaluation. It narrows world coverage from 96 to 32; that limitation must remain visible. It also makes differences between acquired policies easier to inspect without confounding them with different evaluation panels.

I independently reconstructed the revised count arithmetic:

| Item | Corrected quantity or upper bound |
|---|---:|
| Independent fits / training missions | 3 / 1,536 |
| Total native transitions | **2,049,600** |
| Frozen missions | 172 |
| Optimizer updates | 91,392 |
| Replay presentations | 11,698,176 |
| Worker and reader neural Q rows | 70,606,656 |
| Independent native-reader physical states | 2,051,308 |
| R model steps, worker | 4,424,000 |
| R model steps, worker plus reader | **8,848,000** |
| R internal G queries, worker plus reader | 440,160 |
| All G cluster-tick recurrences, worker plus reader | **2,342,753,280** |

These are exposure bounds, not measured throughput. Further exact reuse and deadline cancellations can reduce completed work; failed attempts and their CPU remain charged.

The non-fit bill is substantial. The complete reader, roughly 2.34 billion G recurrences, deadline machinery, trace handling, implementation and scientific reading are material costs. The corrected **4–8 GiB evidence estimate**, source snapshot, disk allowance and uncertain RSS are more credible than treating the Oracle’s original storage estimate as established. No fresh node feasibility or new-controller throughput has been measured. The 50-CPU-hour watchdog is a resource boundary: hitting it before complete reading would produce technical incompleteness, not a negative learning result.

My strongest consequential objection is therefore the combination of **likely ordinary competence and substantial support cost**. The public request law, low offered load, known execution model and strong G/R may leave little useful work for learning. The study earns its price only as this one complete conditional acquisition-and-use comparison. It does not earn a broader research program in advance.

I still favor the purchase because the supplied executor removes an already-exposed geometric acquisition problem, the request process creates a distinct sequential allocation problem, and the corrected comparison can distinguish three useful outcomes: ordinary sufficiency, valuable model-based scheduling, and useful native acquisition. A G-only comparison would leave too much room for interpreting correction of its proxy as a broader learning success. The complete G/R/L study resolves that ambiguity at a bounded price.

The reading must preserve the different consequences of plausible outcomes:

| Observation | Supported judgment and action |
|---|---|
| L improves G across the acquired policies and offers a favorable complete service–compute point against R | Retain a conditional learned scheduling capability. Report training variability, tails and full price. Broader confirmation or transfer remains a separate investment. |
| L improves G but loses to R | Retain acquisition evidence and its comparative limit. Any cheaper online use requires the actual service tradeoff and training-inclusive cost curve. |
| R improves G while L matches or worsens G | Retain the useful ordinary planning result and stop this finite learning recipe. No automatic head, entropy, seed or horizon extension follows. |
| G performs comparably to both alternatives | Prefer G within this contract and end the additional complexity purchase. |
| R rarely completes a cohort | Read this as limited activation and a measured implementation/budget limitation. It does not establish that useful foresight is absent, and it does not automatically authorize a larger search budget. |
| L seldom changes causally used decisions, or changes them adversely | Separate nonactivation from active harm. Neither observation alone diagnoses representation or optimization, or supplies a repair. |
| Outcomes vary sharply across fits, remain uncertain, or trade lower C for severe cluster/user tails | Preserve the heterogeneous or limited result. Complete this purchase without selecting a favorable fit or silently enlarging it. |
| All programs perform poorly on complete request service | Retain the settled geometric construction while acknowledging that full finite-horizon usefulness was not established. A common failure does not isolate a learning defect. |

The three fits are the independent training units. The shared 32 worlds and common R realization induce dependence across their evaluations. The proposed separate conditioning statements for fit-level and world-level descriptive intervals are appropriate. Ninety-six L episodes do not become ninety-six training replications.

Likewise, changed argmins, activated commands, changed movement and changed native completions must remain separate observations. Comparisons between actions at different visited states do not identify a causal scheduling mechanism. Completed-request averages must not hide unfinished requests; the full C ledger, per-cluster backlog, residence tails and all-user service gaps are necessary to judge utility.

I checked the relevant primary passages in MARL-0553’s structured source, the emergency-responder paper’s local PDF and [official publication](https://proceedings.mlr.press/v235/sivagnanam24a.html), Li et al.’s assumptions, and [Bertsekas’s rollout formulation](https://www.mit.edu/~dimitrib/Multiagent_Rollout.pdf). They support the conceptual bridges and their limits. They do not establish this UAV task’s headroom, finite-training success or price. I did not independently check every Li et al. passage cited by the DM.

For the new proposal, I checked the complete [corrected contract and subsequent addenda](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:5906), relevant current source, primary saved results and consequential count arithmetic. The inspected physical source paths were unmodified at HEAD `381e641f325bb077d630480e712e6ccde286c455`. New implementation correctness, deadline enforcement, numerical replay, throughput, memory and storage remain unverified. I made no new controller, model, native, fit or host-health calls. Metered arithmetic in this source review totals approximately **0.0772 CPU-seconds**; source retrieval and review support are incompletely metered.

The shared-background revision should preserve the distinction between supplied cooperative execution, learned centralized scheduling, ordinary planning competence and complete usefulness. Current evidence supports constructing this comparison. It supplies no positive result for it.

**MATERIAL_DISSENT: no.** The DM accepted the consequential comparator, price-design and initialization-identity corrections. I recommend the resulting single complete exploration at the declared price. Root retains the investment decision; this review itself authorizes no implementation or run.
````

<a id="request-scheduling-investment-disposition-20261002"></a>
#### 2026-10-02 — DM disposition and completed source-only return to Root

I read the entire14,111-byte original review and accept its recommendation:
**recommend one complete corrected G/R/L exploration, with three independent
fits,2,049,600 native steps and the full reading, at the explicitly uncertain
20–50 CPU-hour /24–40 support-hour price.** This recommends a purchase; it does
not make that purchase. Root owns the next allocation under the source-only
assignment. B03/B04 stay closed, the separate action-distribution pair stays
untested and declined, and no new model/controller/native/physics/fit/health
call or production implementation has occurred.

The review changed the construction and weakened my travel-based opportunity
argument. Known FIFO residence/progress must be treated exactly in G; the
ordinary planner receives full four-way rights, exact tape/prefix reuse and
all measured cancellation/deadline costs. Sharing32 evaluation worlds removes
repeated ordinary work while narrowing task-law coverage. The nominal71/95
travel scales and40% arrival-period ideal load make G sufficiency more plausible
than the original89/126 illustration suggested. The mathematical zero-head
identity did not establish program identity under a deadline; deployed
initialization now explicitly is the canonical G path, with its separate
neural checks billed. These are substantive corrections, not corroborating
empirical evidence for the learner.

I independently recomputed the consequential native/update/Q-row/R/G counts
and checked the review's reused service-age contrast against its original
paired table (+.269054 L1−M with [.069315,.468793]). The original B08 result
likewise retains exact outputs, lower complete cost for both ordinary methods,
and the2.888276 A2/G2 worker-plus-reader ratio; it supports giving exact reuse
to the new ordinary comparator, not transplanting that measured speedup.
My conservative settled-geometry bound(<1140m outer-to-user) and the critic's
tighter bound both lie below the1193.66m threshold. This changes the scope of
available ordinary execution knowledge: three already-settled distinct pairs
can serve their clusters concurrently under this exact static FDMA law. It
does not establish complete new request service, regret, learnability or
measured throughput. No new physical case was generated to support it.

The investment rationale is therefore limited but substantive: compare native
acquisition and whole-task usefulness where known cooperative execution is
provided and dynamic allocation remains. A result can retain G as sufficient,
retain valuable R, or retain a learned scheduling capability; all three change
the practical method choice. The existing literature and project adverses make
a learned win uncertain. The independent review explicitly values this one
comparison despite that risk and the substantial support cost; it does not
establish an ongoing program, a new-method contribution or a reason to keep
repairing after a negative/uncertain endpoint. I agree. There is no material
dissent remaining, and an additional Pro round offers no distinct unresolved
expertise or disagreement at this decision.

The accepted maximum R computation after mandatory empty-tape reuse is
4,424,000 worker /8,848,000 worker-plus-reader model steps; G's corresponding
whole-study upper bound is2,342,753,280 cluster-tick recurrences. These and the
70,606,656 neural-Q-row upper bound are distinct from2,049,600 native exposure.
There are0 R teacher labels. All raw/full readings, adverse tails, cancelled
prefixes and actual resource cost remain part of the proposed purchase.
The earlier8–24 compute-wall-hour estimate is particularly uncertain: G and
reader work can be serial, so CPU hours cannot be mechanically divided by a
thread count. Whole-package wall time is not measured or a fixed promised
upper bound; if selected it must receive an explicit sufficient operation
watchdog before execution. The50-CPU-hour complete-cost boundary stays as
proposed. Exceeding it without the full reader would be technical incompleteness,
not a negative learning result, and creates no implicit retry authorization.

Root can now choose the complete package or decline it at this actual price.
If selected, the next authorized work would be a concise implementation L0,
fixed literal seed/stream identities, owned code and independent high-risk
engineering review, then published inputs, actual-node admission and one
complete run/reader lifecycle. No preliminary scored panel, rate adjustment,
repair of an old accepted operation or additional training was selected here.
If declined, this completed construction is useful evidence and the broader
question remains open; no replacement idea or recurring check is owed.

This source-only assignment created only the appended notebook record and
the narrow direction/shared-background publication. It created no experiment
code, raw data, source snapshot or observer needing deletion; actual deleted
targets are none and reclaimed disk bytes are0. B04's previously published
3,657,367,552-byte net cleanup remains separate and is not claimed again.
The current advisory and support cost is incompletely metered, not zero:
the two paid-metadata reads used.052780160 CPU-s, original-Oracle preservation
.075605339, and full-critic preservation.093214581; other source retrieval,
arithmetic, authoring and Git work are outside that subtotal. The critic's
separately scoped arithmetic is about.0772 CPU-s. There is no new empirical
outcome to pool with the old runs. The relevant shared background is revised
only for the scoped source deduction and the execution/acquisition distinction;
local contract and investment details stay here.

<a id="b05-selected-contract-l0-20261002"></a>
#### 2026-10-02 — B05 complete request-scheduling exploration selected; L0

Root explicitly selected one complete corrected G/R/L exploration after reading
the whole source contract, addenda, original14,111-byte independent review and
DM disposition. This is new B05 work, not reopening B03/B04. The substantive
contract and all corrections immediately above are binding:3 independent fits,
1536 training/172 frozen missions,2,049,600 native transitions,91,392 learning
updates, the complete native/G/neural/paid-prefix reader and all tails. The
scientific question and negative alternatives are unchanged; the completed
independent selection review applies, with no new Pro or per-phase Root ACK.

The whole accepted ceiling is50 cumulative CPU-hours for scientific execution,
checks and full reader, and72 aggregate operation wall-hours. Preparation,
support, queue delay and publication are reported separately in their real
units and are not zero. The expected20–50 CPU-hour/24–40 support-hour cost,
4–8GiB unique evidence and6–10GiB additional disk including a single roughly
1.8GiB source snapshot remain estimates. We will specify an actual free-disk
floor with reserve for final evidence and one source snapshot before launch,
and retain the8GiB actual-node available-RAM floor; no current hardware health
or throughput has been measured. Worker/reader source snapshots are sequential,
not two simultaneous retained copies. The actual result node remains the
configured WSL primary unless actual admission establishes a reason otherwise.

Root clarified the failure boundary: pre-acceptance synthetic unit tests,
static checks and independent engineering-review findings are ordinary draft
feedback and may be corrected with all costs retained. The first genuine
failure of a formally submitted/actual-admission request, result worker or
full reader stops this purchase and dependent effects; no automatic resubmit,
renamed attempt, replacement fit or unselected continuation. Synthetic checks
may not become undeclared actual model/physics/learning score screening.

**Literal identities fixed now, not searched.** Study master109259999. Fit
indices0,1,2 have training worlds109250000…109250511,
109251000…109251511,109252000…109252511 respectively. The common main panel is
109253000…109253031; audits109253900/109253901/109253902 belong to fits0/1/2.
Initial Torch seeds are109254101/109254102/109254103. Geometry keeps B03's
registered map law, with its `[world,1]` jitter and `[world,2]` user generators;
native UAV initialization uses the world seed. New PCG64 SeedSequence domains
are `[master,20,world]` for the public rate permutation,
`[master,21,world]` for the actual48×4 arrival tape,
`[master,30,world,decision_index,tape_index]` for R's separate future tapes,
`[master,10,fit]` for exploration, and `[master,11,fit]` for replay indices.
The task owns the actual future tape; public objects contain no RNG or suffix.
Frozen program order cycles by world index through G/R/L0-final/L1-final/
L2-final; audit order cycles G/R/L-initial/L-final by audit index. Random draws
and numerical source identities are recorded; ordering creates no extra worlds.
Use separate conditional paired t summaries for each fit and the shared-world
average; no unplanned bootstrap/sampling stream is required for that reading.

**Deliverable and ownership.** Implement the selected study under new owned
`experiments/candidates/uav_decision_generalization/b05_request_schedule/`
and matching tests. New entry `run.py` has explicit worker/reader mode, seed,
launch SHA, output, source/input/budget identities and admission before effects.
Fixed configuration/source/budget JSON stays in the existing direction's docs;
raw/compact outputs use new `runs/uav_decision_generalization/b05_request_a01/`
and `b05_request_read_a01/`; operational scratch stays in this direction's temp.
The DM owns NOTES, executable input acceptance, Git/index publication,
collection and interpretation. No shared core change is planned. Reuse the
existing authoritative host and small identity/physics helpers where suitable,
without changing frozen500-step consumers or copying a shared learner.

First bounded Implementer assignment: pure public state/FIFO/executor/G/feature
semantics, including source-fixed seed identities and exact payload layout.
Owned files are new `__init__.py`, `contract.py`, `task.py`, `ordinary.py`,
`features.py`, and `tests/.../b05_request_schedule/test_core.py` only. No host,
native/RF, Torch, launch, reader, process-supervision, docs or Git mutation by
this helper. It implements one verifiable behavior: four lawful delayed target
choices and the corrected ordinary values/learner features from a public state,
with a native-compatible FIFO ledger. This shared interface is explicit so
subsequent model/runner work can consume it without concurrent file writes.
Helpers are not alone in the checkout; they preserve others' edits and spawn
no children. Later bounded scopes will be recorded here if delegation helps.

The pure state consists of world/tick, int32(50,2) users, four probability codes,
float64(6,3) positions, bool50 ACK, integer4 counts/progress, uint8 six active
slots and immutable three fixed member pairs. Candidate slots are(4,6), slot
ID `2*cluster+inner_or_outer`; initial membership follows the ordered selected
clusters. G returns canonical float64 four costs and counted prediction work;
feature construction returns float32(4,303) plus retained float64 G values.
State/report operations copy or expose immutable arrays; no private ledger
timestamps/future tape escape into public control objects. The FIFO ledger
separates start-of-tick arrival/pre-service charge from end-of-tick ACK service
and applies terminal cost once. Model reconstruction can use public N/r without
inventing arrival ages; actual episode outcome ledgers retain real IDs/times.

**Checks and stop.** First helper tests use fixed synthetic maps/positions/
queues/ACKs only, with no generated scientific world or host/model/RF calls.
Cover arrival/service ordering, twentieth-tick completion, interruption/empty
reset, FIFO and residence conservation, terminal/unused command boundary,
pair/slot legality and orientation ties, current-position delayed mapping,
known-head G recurrence versus a separately written scalar reference, future
fluid/no-arrival tail, payload sizes/padding and303 feature ordering/dtypes.
Record test invocations, failures/corrections and CPU/wall cost; these are
engineering diagnostics, not task scores or G-throughput estimates. Tests own
and clean pytest scratch under the existing temp lifecycle. Later neural and
deadline checks will use separately declared synthetic fixtures/mocks, not
an undeclared native panel or trained-checkpoint selection. Independent
high-risk engineering review must cover the integrated code's numerical,
RNG, replay, identity, deadline/cancel, source and complete-counter behavior.
The DM accepts the diff and checks. Published exact inputs and active ownership
precede any actual scientific launch; actual-node admission is not a reason
to query health or run a pilot during implementation.

**B05 bounded learner implementation scope.** A second disjoint Implementer
may own only `b05_request_schedule/learner.py` and its `test_learner.py`: the
fixed55,553-parameter residual scorer, exact64-bit G/tie composition, replay
with separate sampler, cost-form Double-DQN update/target schedule, and
checkpoint/movement identities. It receives cached(4,303) feature and float64
four-G arrays, not a host, public/actual future tape or G callable. Runner,
deadline policy path and native collection remain the DM's responsibility.
Its checks may construct the **new untrained** scorer on fixed synthetic
bounded feature rows, verify exact zero-head ordering, run two synthetic
128-row gradient/target-copy updates, and use mocked small tensors for
termination, signs, duplicate-index refusal, stream separation and replay
boundaries. They must not load old trained assets, draw real study worlds,
call a physical model or estimate task/throughput scores. Count every actual
synthetic network forward row/backward/optimizer call separately from the
selected worker/reader70,606,656-row and91,392-learning-update exposure. These
correctness diagnostics consume the same complete50-hour CPU budget and
create0 fitted task policies/native transitions. Parameter construction,
zero-head certificate and checkpoint round trips are also timed; tests use
the normal pytest-owned temporary lifecycle. Draft defects may be corrected
under Root's explicit clarification, with attempts and cost retained.

**Pre-execution timing and source clarification.** Root explicitly resolved the
offline training order: each nonterminal report first receives a real20s
monotonic decision window containing canonical four-way G, features, current
network and exploration. Fix the command and its cache before admitting the
previous complete transition to replay and doing at most one offline update.
The fixed command is not reselected; updated weights first act at the next
report. The terminal transition gets its scheduled update without a new G or
command. Replay/Adam time remains fully charged training acquisition, outside
the deployment deadline; this is not claimed as realtime online learning.
Missing a required training G/decision cache at the deadline preserves the
actual fallback/missingness and stops the selected training contract as
technically incomplete. Ordinary declared R cohort cancellation remains a
policy outcome. This adds no update, fit or native transition.

The earlier phrase “host's float32 action/movement order” at the common
executor definition was a source error. Current original
`b03_joint_window/ordinary.py:steer` returns float64;
`envs/pettingzoo/env_adapter.py:_array_to_dict` passes rows unchanged;
`CoupledRelayHost.step` preserves each copied floating vector's dtype; native
velocity multiplication precedes addition to float64 position. FP32 described
the old Gaussian inputs, not ordinary steering. B05 therefore preserves the
original **float64** ordinary steering and strict copied-vector `norm>1`
projection across all arms/model branches. No science ran under the mistaken
description. Root was informed before execution; the information/action/task
and purchased ceilings are unchanged.

**Bounded native integration scope.** After the pure-core handback, the same
Implementer may own only new `native.py` and `test_native.py`, plus correcting
the inaccurate float32 sentence in its own `task.py` docstring. Implement one
native1200-tick host facade with source-fixed users, supplied-public-state
reconstruction, exact float64 common actions, counted reset/RF/step events and
snapshots. It must never clone an actual queue wrapper or arrival suffix into
R. Constructor-reset topology overwritten by the inherited constructor must
be restored from that same completed native reset, without an extra RF call.
For public model reconstruction, install public positions/users before the
first native RF computation using the registered user-generation hook; retain
and count constructor work, then set the public clock and verify the public
ACK. Pure mock tests may exercise plumbing and snapshot/motion contracts; no
actual native construction, channel call, scientific world or rollout is
authorized before the accepted full launch. The DM owns rollout/search,
deadline processes, traces, runner and reader integration. Other files/index
remain outside this helper's ownership; independent engineering review follows.

The accepted pure-core18 checks passed first invocation at1.594610 measured
CPU-s/.557814 wall-s, with8 synthetic G queries,32 values,4,008 candidate-ticks,
16,032 cluster recurrences,24,048 kinematic UAV steps and368 expected-arrival
cluster additions. Native facade11 mock checks passed first invocation at
1.819717 CPU-s/.917193 wall-s; separate static check.005706 CPU/wall-s.
Actual native constructions, scientific worlds and RF calls remain0. The
learner's six pure/mock and one bounded real synthetic check passed first
invocations at6.90 CPU-s/5.19 wall-s:260 actual residual rows,2 backwards and2
optimizer calls, one scorer plus target/validation copies, no fitted task
policy. Its target-copy fixture explicitly set schedule counter255; that
counter is not256 actual diagnostic updates. An added mock-only event sink
check passed at2.57 CPU-s/1.54 wall-s, with0 further real neural calls. The
optional numeric cumulative event callback exposes attempts before calls and
commits after completion to parent-owned storage; it never carries a model,
private arrival tape or replay cache, and a failing sink is not retried.
Unmeasured preparation/static/support work is separate, nonzero, and not an
imputed runtime score. All these measured checks enter the50-hour prior bill.

**Full-reader bounded implementation scope.** A helper may own only new
`reader.py` and `test_reader.py`. The existing written `storage.py`, `worker.py`,
`policy.py` and `rollout.py` define the trace interface; their authorship remains
the DM's. Implement one full audit of the fixed1708 actual records and every
paid committed R prefix/G query, plus fixed-panel/fit-conditional summaries.
Use the existing separately written B03 stateless physical reconstruction and
faithful copied-vector float64 motion; separately reconstruct the FIFO,
target delay, arrivals, assignment, policy features and corrected G. Retain
exact native discrete masks/routes/queues/actions and declared numerical
comparisons; do not invent missing records, complete an interrupted query,
run a native host, replay optimizers or add worlds. Frozen neural inference
uses only the saved final/initial endpoints and the fixed303 input, counted
explicitly. A pure/mock fixture may test accounting and reading plumbing,
without actual RF/G/NN/world/fit calls. The reader input/manifest identities,
whole-budget admission and useful result publication remain DM-owned.

**B05 integration and prospective reading details (before execution).** The
reader will report 95% paired-t descriptive intervals over the32 common worlds
conditional on the frozen endpoints/shared ordinary realization (df31), and
separately over the three fit means conditional on that panel (df2). The
shared-world policy average retains world covariance. These are exploratory
displays, not a new adoption threshold or96 independent training replicates.
Completed/unfinished request residence, all50 user gaps, cluster backlog,
interrupted head service, native movement and actual deadline/cohort exposure
remain alongside C. No optimizer replay or additional counterfactual native
suffix is purchased.

The worker/reader use the configured Linux node, CPU Torch4 threads and
interop1, NumPy/BLAS1, and the configured Python3.10.21/NumPy1.26.3/
Torch2.7.0+cu118 versions; no CUDA work is requested. Native admission precedes
all effects. The selected8GiB available-memory floor is accompanied by12GiB
free output-disk floor after source-snapshot preparation; the4–8GiB unique
evidence and6–10GiB additional-peak forecasts remain unmeasured estimates.
No health pilot or new throughput estimate was run. CPU accounting includes
the parent, live policy PIDs and reaped children; prior measured diagnostic
cost enters the same50-hour bill. Source reading, design and coordination
support remain separately nonzero and incompletely metered.

Independent engineering review identified concrete draft defects that were
corrected before any formal request: duplicate reader Torch interop setup;
missing inclusive mission/acquisition CPU attribution; nonfinite prior-cost
acceptance; an ESRCH reap race; parent-death leakage after a policy child's
`setsid`; and a scientific manifest that inadvertently included mutable
launcher status/logs. Parent catchable termination now unwinds through child
reaping and failure evidence; each policy child also binds Linux's SIGKILL
parent-death signal with both PID-race checks. Spawn identity publication is
protected from catchable stop signals, and startup/send failures reap before
any R trace collection. Abrupt external loss remains incomplete evidence, not
a resumed or replacement fit. The final manifest binds only worker-owned
config, endpoint counts, named fit metadata/checkpoints and raw traces;
launcher terminal/status/log records retain their own lifecycle.

The DM's full reader source read also corrected its proposed1200 reward-entry
expectation: the unchanged native step enters the inherited dense/parent
reward method twice per tick, hence2400 of each in a complete mission. This
does not double the once-per-tick request charge and changes no physical
transition. The reader validates those inherited event identities directly.

Additional DM checks: the first14 pipeline tests plus11 native checks passed
in one invocation at3.339247 child CPU-s/1.796870 wall-s; the arithmetic-only
exposure reconstruction cost.065679 CPU-s. The updated20-test pipeline passed
at4.210313 measured CPU-s/1.768539 wall-s, including a real benign child
termination/reaping fixture, parent-death signal fixture, start/send unwind,
and the actual effect-free launcher's literal admission scanner. A subsequent
immutable-manifest fixture passed1/1 at1.764638 CPU-s/.644628 wall-s. These
invocations add0 actual host, physical, scientific-world, G or neural calls.
Test-owned scratch was removed normally. They establish those local plumbing
properties; native integration, complete reader execution and throughput
remain unexecuted. Reader mock-check attempts and final review are recorded
at acceptance below, including any draft-fixture failures rather than erasing
their cost.

**Reader and engineering acceptance.** The DM read and accepted the full
bounded reader implementation and its checks. Its seven mock/static pytest
invocations consumed13.73 measured self-plus-child CPU-s/4.79 wall-s:
initial11-test pass3.39/1.61; reward-fixture failure1.43/.40 and correction
1.35/.31; publication check1.37/.34; cancellation check1.43/.40; sampler-fixture
failure1.42/.40; final14-test pass3.34/1.33. The two failures were fixture
class-name/signature mistakes; both remain charged. No actual native, RF, G,
neural, optimizer or scientific-world call was made by these reader checks.
The reader independently reconstructs geometry/FIFO/actions/features/G,
replays only committed frozen neural rows and paid committed R prefixes,
validates source-order cancellation frontiers, and streams the full replay
identity from its single canonical trace copy. It checks optimizer state and
updates/sampler lineage without claiming optimizer replay.

The independent Engineering Reviewer found no remaining material/P1+ issue
in the integrated draft and verified all61 source bindings, exact input bytes
and cost arithmetic. It retained actual native/RF integration, complete
worker-to-reader execution, deadlines, memory/disk peaks and throughput as
unexecuted gaps. The DM accepted its concrete corrections. A final small
reporting correction separates all policy-cache misses from true neural-cache
misses; its mocked full-entry regression passed1/1 at1.961803 CPU-s/.918960
wall-s, with134 synthetic policy misses versus99 neural misses. Source/input
generation cost1.569054 CPU-s/.447141 wall-s. Additional review/edit support
is incompletely metered and nonzero.

**Pre-request actual-node choice,2026-10-03 UTC.** Before publication or any
B05 formal request, Root supplied the other direction's original
`runs/typed_joint_skill_decision/b07_consumer_a03/stderr.log` and
`collection-prefix.json`. The DM read both, its current NOTES terminal entry
and independent engineering diagnosis. The remote configured CPython3.10.21
GCC process raised `UnboundLocalError` at `pathlib.py:578` while reading `a`,
although the saved stdlib fragment binds `a` in the preceding `for` at574.
The observed exception is unexplained by that saved ordinary control flow;
the source file is not the executing interpreter state. No CUDA, compiler,
memory, bytecode or shared cause with an older SIGSEGV was established. This
does not prove general remote-node unsafety or corrupt B04's completed result.

For this CPU-only, still unsubmitted purchase, the DM selects the already
configured **local_linux** environment for both worker and reader. This
supersedes the earlier prospective remote version tuple: the existing local
`pyvenv.cfg` identifies CPython3.10.20; installed package metadata and version
source identify NumPy1.26.3/Torch2.7.0+cpu. The selected source checks this exact
tuple and Linux, records the interpreter, and binds the native launch
manifest's node. All earlier B05 correctness checks used this existing
scientific venv, but that limited evidence does not establish long-run
reliability. No interpreter/package installation, health query, native/model
pilot, new fit or changed scientific comparison occurred. Hardware-dependent
deadline activation and measured costs will be conditional on this chosen
node. Throughput remains unknown. The20s deadline,8GiB RAM/12GiB free-disk
admission floors,50 cumulative measured CPU-hour/72 aggregate operation-hour
stops and first-formal-failure boundary remain fixed; an admission failure
does not authorize transfer to another node.

The narrowly changed runtime fixture passed1/1 at1.794653 CPU-s/.712865
wall-s using mocked Torch/version methods only. Regenerating exact inputs
cost1.575587 CPU-s/.458188 wall-s. The current fixed61-source identity is
`7eeaaf614fd8d88023f0baba2ca2aa04804b893acb1ecfec52158e9d0e762210`.
`B05_STUDY_INPUT.json` is24,830 bytes,SHA256
`05998b40a59d7766771e4513051aafb44eeebbe6c75e4bd569faf2fe61f9297b`;
`B05_BUDGET_LEDGER.json` is2,296 bytes,SHA256
`8597434c50befd0ddeb3795ec0da6df66dd0e48b225ba7dd17f924339a068256`.
Its known pre-execution bill is42.901007 CPU-s/19.747903 recorded operation
wall-s; some helper measurements are rounded to centiseconds, one arithmetic
wall measurement is unavailable, and other support is explicitly unknown,
not zero. The prior counters retain8 synthetic G queries/260 actual synthetic
neural rows/two backwards/two optimizer calls; task fits/native transitions
and formal submissions remain0 at this acceptance point.

The same independent Engineering Reviewer completed the focused runtime
revision review: no material finding remains; all61 final source hashes and
both regenerated inputs verify, only `contract.py` and `run.py` changed from
the integrated reviewed closure, and the local-node risk statement preserves
the unresolved cause. The DM accepts these exact bytes and the existing
checks. The local selection expressly supersedes the earlier remote tuple;
native integration/complete execution/throughput remain unvalidated. Source
publication is next, followed by this single actual local admission attempt.

**Worker source publication and accepted operation,2026-10-03 UTC.** Exact
inputs and accepted code were published on main at
`2d754f29308a56a4db81f867ca1b79b5e75f99ad`. The single selected local request
was accepted at00:55:17Z; its authoritative
[native manifest](../../../../runs/uav_decision_generalization/b05_request_a01/launch-manifest.json)
binds the command, node, source snapshot, output and native identities.
No replacement or second request was made. The same operation is observed
with `tools/hmasd_wait.py`, session-owned state
`/home/fires/.local/state/hmasd-wait/01a0fd19-e19a-7bb2-a7b2-1a11bc665a22`,
job `b05_request_a01`, generation1,60s native status cadence and1500s window.
The first drain showed consistent accepted/running identities and empty
stderr; it is observation adoption, not scientific completion. This native
child keeps its turn active through deterministic waits and same-handle
drain/rearm; a possible App queue rejection does not authorize rerouting or
duplicate work. The unchanged first-formal-failure stop and full collection/
reading obligation apply.

At the generation1 observation checkpoint, the same worker remained
accepted/running with664 complete training missions/796,800 native steps,
recorded cumulative CPU2606.598338s and aggregate operation wall1554.574733s;
stderr remained empty. The native-child App delivery was rejected with
`-32600`, as expected for this runtime. The active DM drained that saved event
and rearmed the same operation as generation2; no worker restart, duplicate
request or address change occurred. These progress counts are not a read result.

Generation2 was drained/rearmed as generation3 on the same accepted worker.
At this checkpoint1,282 training missions/1,538,400 native steps were complete,
with third-fit training in progress, cumulative CPU5167.406184s and aggregate
operation wall3057.484078s. Stderr was empty. The repeated native-child queue
rejection did not change worker identity or add work.

Generation3 checkpoint: all three training blocks were complete and the
unchanged worker was evaluating the common panel.1,554 complete missions/
1,864,800 actual native steps and377,920 completed R model ticks were retained;
cumulative CPU6909.194237s, aggregate operation wall4392.069723s, empty stderr.
The DM drained/rearmed the same job as generation4. Full result validation
and interpretation remain outstanding.

<a id="b05-worker-complete"></a>

**B05 worker technically complete; full reading pending,2026-10-03 UTC.**
Generations4–7 were drained/rearmed on the original operation without a
restart; generation8 delivered a saved `READY` event. The native witness
records exit0 at04:09:45Z, both native processes absent, consistent identities,
and empty stdout/stderr. The DM consumed the event as generation9 and stopped
that completed observation before binding the planned reader. Native-child
queue delivery remained rejected; the continuously active native DM read the
deterministic events directly.

The worker's own checks report all1,708 H1200 missions:3 fits/1,536 training
plus172 frozen evaluations,2,049,600 actual native transitions and91,392
optimizer updates/11,698,176 sampled current rows. All11 endpoint count
records were retained. R reports2,100 decisions,8,400 completed logical
cohorts,1,391 exact cohort reuses and4,407,360 computed native model ticks;
the worker's total reserved G candidate-tick count is292,210,560 and its neural
attempted-row count69,609,916. These are worker readings subject to the full
reader, not empirical acceptance by process exit. Cumulative measured CPU
including earlier checks is13,687.793894s; this worker's phase is13,644.892887
CPU-s/11,667.328155 wall-s. The corresponding aggregate operation-wall bill
is11,687.076058s. GPU use is0. Reported self/child RSS peaks are253,616/615,384
KiB and are separate process-scope peaks, not a simultaneous summed peak.

The unique canonical output remains on configured `local_linux` at
`/home/fires/hmasd-wsl/runs/uav_decision_generalization/b05_request_a01`.
Collection verified all5,530 scientific file identities and382,368,563 bytes
against the worker manifest, without copying raw data. Allocated output at
that observation was397,168,640 bytes. The independently timed hash pass
cost1.857394 CPU-s/4.173922 wall-s. Compact
[collection facts](../../../../runs/uav_decision_generalization/b05_request_a01/collection.json)
retain the worker config/summary/manifest identities and source-cleanup facts.
This actual compressed footprint is below the earlier4–8GiB forecast; that
forecast was not an observed storage bound.

The already selected reader is now bound to the exact complete worker by
`B05_WORKER_INPUT.json` (345 bytes,SHA256
`01145a87da1801b7a03a325ed2fbd703fdaed0753c9af06a3b64c1bf680f463d`).
`B05_READER_BUDGET_LEDGER.json` (2,788 bytes,SHA256
`f5358750f0ea39921b9ef68aff4339a577173f52b11d19e807ae602e2b0faa7b`)
carries13,689.651288 cumulative measured CPU-s and11,691.249981 aggregate
operation wall-s, including that collection. Static status/source reading,
compact binding writes and transport/review support remain incompletely
metered and nonzero. The original study input and all61 executable source
digests are unchanged; the integrated engineering acceptance still applies.
The reader adds no native training/evaluation mission or optimizer update;
it performs the fixed complete saved-evidence reconstruction, including paid
R prefixes and all training records, on the same local runtime. The original
50 CPUh/72 operation-wallh stops and first-formal-failure stop remain fixed.
Publishing these exact reader bindings is the next step before its sole
actual-node request. G/R/L service and complete-use judgments await that read.

The native exact-target collector removed worker source snapshot
`.git/hmasd-launch-sources/49b9b182f78c472ebd5f8227396e92b5` after terminal
identity/unique-output verification. Net allocated space reclaimed was
1,830,649,856 bytes; the output allocation stayed397,172,736 bytes. The first
unprivileged preview could not inspect `/proc/454/cwd`; the documented
`--sudo-process-scan` read-only process probe resolved that concrete check,
and apply revalidated eligibility. The target and Git worktree registration
are gone, all unique output remains, and there is no cleanup blocker here.

<a id="b05-reader-a01-failure"></a>

**First reader request closed after an operator digest transcription failure,
2026-10-03 UTC.** The exact complete-worker binding and unchanged reader source
were published at `173754d233b7cd6dcebecf25bff164c284577457`. The DM then
submitted one reader request, accepted at04:17:47Z, whose
[native manifest](../../../../runs/uav_decision_generalization/b05_request_read_a01/launch-manifest.json)
preserves the actual argv. In that command the DM manually omitted two
characters from `--study-input-sha256`, submitting the62-character string
`05998b40a59d7766771e4513051aafb44eeeb6c75e4bd569faf2fe61f9297b`.
The correct, already published64-character digest remains
`05998b40a59d7766771e4513051aafb44eeebbe6c75e4bd569faf2fe61f9297b`.
This was the DM's command transcription error, not changed study bytes.

The accepted runner exited1 at `run.py:95`/`evidence.bound_json`, with
`ValueError: bound input bytes changed`. This frontier precedes source-manifest
construction, completed-worker binding, the study-specific resource check,
runtime setup and reader import/call. Actual reader physical/G/neural/optimizer
work is0; no worker mission was repeated. The native exit witness is valid,
both original processes are absent, and no successor or resend was made.
[Failure summary](../../../../runs/uav_decision_generalization/b05_request_read_a01/summary.json),
[stderr](../../../../runs/uav_decision_generalization/b05_request_read_a01/stderr.log)
and [collection proof](../../../../runs/uav_decision_generalization/b05_request_read_a01/collection.json)
retain the failed argv, correct input digest, terminal identities and missing
read. The independent byte comparison found identical study bytes in the
published commit, live canonical checkout and accepted immutable snapshot;
their common SHA differs from the submitted62-character value. No runtime,
physics, neural or optimizer diagnosis is inferred from this known input error.

This failed request cost.168788 measured CPU-s/.353515 operation wall-s. Its
terminal/byte collection cost.157186 CPU-s/.156911 wall-s, with cumulative
known totals13,689.977262 CPU-s and11,691.760406 aggregate operation wall-s.
Other static/support work remains incompletely metered and nonzero. Worker
raw, checkpoints and all positive/adverse outcomes are unchanged and retained;
the G/R/L complete service comparison is still unread and unvalidated. This
failure is neither evidence against the task opportunity/learner nor evidence
for a particular arm. It establishes only that the invocation did not reach
the selected full reading.

The DM applied Root's explicit first-formal-failure stop, reported immediately
and added no dependent execution. Root subsequently directed preservation
and closure of this request, stated that the unchanged complete selection
review remains applicable, and will explicitly select any corrected reader;
the original50 cumulative CPUh/72 operation-wallh and all paid costs carry
forward, with no new training/mission purchase. A just-issued extra internal
scientific-review request was interrupted on that direction; any reading
support already spent is nonzero, and no new scientific judgment from it is
claimed. The original independent selection advice remains the applicable
review. This is a concrete Root allocation boundary, not a self-authorized
exception for a small error. Reader observation generation11 was drained;
its native failure event and App queue rejection were read without rerouting
or repeating the operation.

<a id="b05-corrected-reader-allocation"></a>

**Root's complete corrected-reader disposition,2026-10-03 UTC:**

> Root已全文读取原reader stderr、launch manifest、FAILED summary、process-exit和worker完成/收集记录，并直接比较输入bytes：当前B05_STUDY_INPUT.json为24,830B，与173754d233读器发布及2d754f293原worker输入逐字节相同；实测SHA为05998b40a59d7766771e4513051aafb44eeebbe6c75e4bd569faf2fe61f9297b（64位），已接受argv为62位。故确认为参数漏写，不能把异常文本误读成文件变更。FAILED summary原phaseCPU .168788、phasewall .3535145、累计CPU13689.820076和operationwall11691.603495已读，counts为空；原exit1见证和源记录保留。
>
> 我现在明确选择一次修正摘要参数的原固定完整reader，建议新tag b05_request_read_a02。先完成原reader同handle终态/observer关闭及必要事实保全，再执行新购买；不得修改旧请求或覆盖失败记录。复用相同worker、study字节和61科学源、原完整读器、原节点及原宣告所有读取工作，不新增fit、mission、控制器分支、optimizer replay或健康/检查点试验。原独立科学选择及工程验收覆盖该未变比较，不需新一轮科学复审。已有聚焦工程事实照常保留。
>
> 把本完整Root处置及你方响应追加到现有NOTES，carry-forward全部已付CPU/wall/failed/support后发布精确reader输入和新预算账本，维持原50累计CPUh/72aggregate-operation-wallh总账及其他既有资源约束，不重置费用。机械地从受绑定bytes取得/核对argv中的摘要，再按新请求做真实节点准入；这不是手动放宽hash guard。原worker/raw保持只读与唯一必要copy，读器实际运行按同handle观察。这个新reader第一次真实请求/准入/执行/读取失败仍停止；不确定接受只协调同一新请求。完整读取与判读、发表、所需清理属于本授权，无需逐步Root批准。Root不另编辑你方NOTES或standing，也不把这一元数据纠正写成科学结论。

**DM response.** Adopt this explicit single corrected-reader allocation as
`b05_request_read_a02`. The original failed request is terminal, its observed
event is consumed and its observation is stopped. Retain every original
failure/worker artifact and unchanged study/worker locator. The fresh budget
ledger adds the failed reader and measured failure collection to the existing
bill; no counter or cost is reset. The launcher argv will be constructed as a
structured argument list with digests calculated from the published input
bytes, compared to the original worker binding before launch; the existing
guard is unchanged. Source bytes, actual local node/runtime, all declared
readings and new request's first-failure stop are unchanged. There is no new
scientific-review round or scientific conclusion from correcting metadata.

The corrected-reader prior is frozen in
`B05_READER_BUDGET_LEDGER_A02.json` (3,449 bytes,SHA256
`12656b66f2b520a0e6f7994c7e8a8d22811a671d6912a04d4225823b95e12343`):
13,689.977262 known cumulative CPU-s and11,691.760406 aggregate operation
wall-s, two prior formal requests including the failed reader,3 existing fits
and all earlier support/missingness. The original study/worker-input digests
remain unchanged. After Root read the failure originals and byte identity,
the supported collector previewed and removed failed-reader snapshot
`.git/hmasd-launch-sources/7561a0c21f6942959e75522dd49b7116` using its read-only
sudo process scan. The target and worktree registration are gone; net
allocated reclamation is1,834,164,224 bytes. The40,960-byte allocated failure
output remains unchanged in size, including original argv, exit and stderr.
Worker and failed-reader source deletions now total3,664,814,080 allocated
bytes reclaimed, without a backup/copy or evidence deletion.

**Corrected reader accepted,2026-10-03 UTC.** Failure evidence, Root's complete
disposition, the new ledger and current standing were published at
`195fc8f44d5a375081e8b851a67671bbe9aafb1a`. The request argument list was
constructed from Git-published bytes, compared to canonical bytes and all61
original source digests, and its study digest matched the completed worker's
bound config. No digest was manually retyped into that launch. The fresh
request `b05_request_read_a02` was accepted at04:29:24Z; its
[native manifest](../../../../runs/uav_decision_generalization/b05_request_read_a02/launch-manifest.json)
is the authoritative command, source, node, output and process identity.
The same session observer adopted job `b05_request_read_a02` as generation14
after closing the prior observer, with the existing60s/1500s cadence/window.
The first drain showed consistent accepted/running identities, empty stderr
and32 completed training-record reconstructions. The DM remains active through
same-handle deterministic observation. This is actual reader execution,
not completed reading or a scientific result; the new first-failure boundary
continues to apply.

<a id="b05-complete-reading"></a>

#### 2026-10-03 — Complete B05 request-scheduling result

**The supplied executor supports complete ordinary request service; this
finite learned residual package worsens the request objective.** Both G and R
complete all1,848 requests in the common32-world main panel. Each of the three
learned final endpoints has higher C than both ordinary programs in every
main world. R retains a useful conditional tail result at a substantially
higher computation/travel price; an unresolved mean-C increment does not erase
that capability. This is a result of the new centralized request task, not a
diagnosis or repair of B03/B04's geometric-skill acquisition failure.

**Complete execution and numerical reading.** Corrected reader A02 exited0
at06:03:27Z on the same configured `local_linux` runtime. Generations14–16
were drained/rearmed on that accepted request; generation17 delivered `READY`.
The event was consumed as generation18 and observation stopped. The native
runner/supervisor were absent with consistent identities and empty stderr/
stdout. No worker or reader was restarted. The earlier A01 digest-transcription
failure, its paid cost and Root's explicit one-reader correction remain above.

The [full reader summary](../../../../runs/uav_decision_generalization/b05_request_read_a02/summary.json)
binds worker source `2d754f29308a56a4db81f867ca1b79b5e75f99ad`, corrected-reader
source `195fc8f44d5a375081e8b851a67671bbe9aafb1a` and the unchanged61-source
scientific identity. All5,530 worker scientific files were reverified. The
reader reconstructs every one of1,708 H1200 missions:1,536 training and172
frozen,2,049,600 motions/2,051,308 physical states. Native masks, routes, FIFO
heads/progress, request completions, costs, commands and motion match exactly.
All102,480 collected four-action G queries and219,248 distinct R-internal G
queries were read; the2,100 mirrored R-base records are excluded from the
distinct total. G costs/features and frozen total Q/residuals match exactly.
Missing policy/neural caches are0. The reader performs24,480 frozen neural-row
evaluations and constructs six scorers; it does not create a new fit, native
evaluation world or optimizer update.

Every paid R prefix is accounted for:4,407,360 model ticks and2,100 initial
physical reconstructions,8,400 completed/selected logical cohorts including
1,391 exact reuses. There are no incomplete native attempts. Each of the2,100
actual R decisions completed all four logical cohorts. Across **all1,708
missions there were zero20s deadline misses**. Thus deadline censoring is not
an explanation for this observed comparison; this fact does not validate
unexercised runtime cancellation cases. The worker and reader each incurred
292,210,560 G candidate-ticks/1,168,842,240 cluster recurrences. These model and
verification operations remain distinct from native training exposure.

**Fixed primary contrasts, lower C is better.** Units are unfinished-request
residence ticks, including successful service time, plus the fixed terminal
backlog charge. The intervals below are exploratory paired t95 intervals
over32 common worlds, conditional on these frozen endpoints and the shared
G/R realization. They are neither96 independent worlds nor96 independent fits.

| Endpoint | Mean C | Mean C−G [descriptive interval] | Mean C−R [descriptive interval] | Unfinished requests / worlds affected |
| --- | ---: | --- | --- | ---: |
| G |2605.5625|reference|—|0 /0|
| R |2545.96875|−59.59375 [−225.37282,+106.18532]|reference|0 /0|
| L0 final |5504.875|+2899.3125 [+2106.10130,+3692.52370]|+2958.90625 [+2160.01181,+3757.80069]|34 /12|
| L1 final |5378.6875|+2773.125 [+2181.58804,+3364.66196]|+2832.71875 [+2254.91362,+3410.52388]|34 /12|
| L2 final |5089.46875|+2483.90625 [+1976.72692,+2991.08558]|+2543.5 [+1954.30697,+3132.69303]|24 /9|

All96 paired L−G and all96 L−R differences are strictly positive. Across the
three independently acquired fit means, the C−G mean is+2718.78125 with the
conditional **df2** interval[+2189.73853,+3247.82397]; against R it is
+2778.375[+2249.33228,+3307.41772]. The different shared-world average-of-fixed-
policies intervals are[+2373.10315,+3064.45935] and
[+2394.80027,+3161.94973]. The three canonical-initialization audits reproduce
G exactly; their G→final costs are2344→2886,3173→6304 and2297→3088. No endpoint,
checkpoint, training length or task condition was selected from these results.

**Retained ordinary capability and its tradeoffs.** R improves C in17 worlds
and worsens it in15; its modest negative mean is not evidence of equivalence,
uniform improvement or a clearly established mean-C surplus. Its tail benefit
is nevertheless observed on the prespecified outcome readings. Mean per-mission
maximum completed-request residence falls330.125→231.8125 ticks, paired
−98.3125[−143.85755,−52.76745],25 better/6 worse/1 same. Mean per-mission maximum
same-user service gap falls546.6875→470.875, paired
−75.8125[−117.93730,−33.68770],23 better/8 worse/1 same. These descriptive
secondary comparisons are not multiplicity-adjusted confirmation. Mean mission
residence p90 barely changes98.615625→97.8125; that contrast remains unresolved.
These are averages of within-mission summaries, not pooled-request quantiles.

R increases mean travel5038.990→7292.349 metres/UAV, paired+2253.359
[+1704.443,+2802.275], with increased travel in29/32 worlds. Mean routed users
per tick decreases36.450234→35.188646 (−1.261589), while request completion stays
complete; the request objective and continuous radio coverage are different
outcomes. Both programs reach every user at least once, but the worst observed
individual gaps are945/664 ticks for G/R. There is no continuity, collision,
battery or radio-energy guarantee.

Concrete positive/adverse cases remain available in the original records.
World109253005 has G→R C4195→3076 and mean travel7633.826→6718.026m/UAV, while
its maximum user gap worsens355→375. World109253017 has C2319→3062 even though
maximum request residence improves284→184 and maximum user gap420→379;
travel increases4369.568→7225.787m/UAV. These cases prohibit a single
"all service improves" description of R. R's sampled native rollout does not
inherit an exact policy-improvement theorem.

**The learned intervention is active and adverse at the complete endpoint.**
On each fit's1,920 main decisions, the residual changes the same-input G argmin
in1089/1100/1156 cases. Commands differ in the same counts;1064/1076/1131 alter
movement at their observed activation positions. The final command is unused
in each of32 missions, and is explicitly excluded from useful activation.
Changed-motion windows contain actual native completions and residence costs.
This establishes executed intervention and complete adverse program outcomes;
it is not an exact counterfactual attribution of each completion to one decision.
Policies visit different later states, so their action disagreements are not
a fixed-state causal ablation.

Mean target changes per mission rise from G's10.9375 UAV-target changes to
72.5/73.9375/70.875; mean head interruptions rise1.09375→7.25/7.59375/6.28125.
Mean travel becomes13080.703/12956.456/12647.351m/UAV; mean routed users/tick
falls to31.347813/31.684557/31.722292. Completed-request maximum residence is
518.75/539.28125/491.90625 ticks on average, while unfinished requests have
observed ages up to860/1000/700 ticks. Those censored requests are not dropped
to make completed-request tails appear favorable. L1 in world109253002 never
serves nine users in cluster1 and completes0/2 of its requests; the1200-tick
user gaps and unfinished ages remain. Local favorable tail/travel comparisons
also remain in the compact diagnostics; no claim of harm on every secondary
metric is made.

**Training happened, without demonstrating useful acquisition.** Each fit
contains30,720 transitions,30,464 updates and119 target copies after the initial
copy; all three replay/final-state identities validate. Parameter L2 motions
are18.622764/17.594558/15.005196 across53392/51743/53519 changed coordinates.
This rules out an unchanged learner. The reader checks the complete stored
action/Q/update ledger, sampler structure, finite diagnostics and frozen final
forwards. It does **not** independently execute the91,392 optimizer updates or
every historical changing-network forward; that was never purchased.

The saved64-episode training blocks give first→last mean C
3718.8125→5379.421875,3494.453125→5347.140625 and
3517.703125→4865.484375. Corresponding means of episode-mean Huber losses are
.016437→.169699,.011755→.070107 and.013665→.015999. These blocks use different
worlds, epsilon .1 and changing policies/targets; they are descriptive training
progress, not fixed-policy before/after evaluations or proof of divergent TD.
Gradient norms are finite, the largest post-cap norm is9.9999981, and no
reported cap excess occurs. The evidence favors an actively worsening finite
learning package over nonexecution, deadline fallback or mere action aliasing.
It does not identify a unique optimization, representation or exploration
cause, nor prove the task unlearnable.

**Complete price and retained evidence.** Worker acquisition for the three fits
is1983.139971/2042.507544/2206.138334 CPU-s (6231.785849 total), including their
native missions, G processing, updates and checkpoint bookkeeping. The narrower
update/offline CPU counters485.774313/527.675318/630.922 do not replace that
acquisition bill. Inclusive main-mission deployment CPU is2.148516 for G,
196.791962 for R and2.871530/2.887332/2.846989 for L0/L1/L2, conditional on the
selected runtime and trace/process contract. R therefore costs about91.6×G
CPU per use. All learned endpoints cost more than G online, so they have no
positive CPU break-even against G. Against R, acquisition-only CPU break-even
is10.23/10.53/11.38 missions, but service costs are much worse: those arithmetic
crossings are **not** utility, quality-preserving or adoption break-even.
No request-tick/CPU exchange rate was defined.

The full A02 reader costs5653.181264 CPU-s/5642.297502 operation wall-s,0 GPU.
At its final summary the known B05 cumulative total, including preparation,
worker, original failed reader and earlier collection, is19343.158526 CPU-s
(5.373100h) and17334.057907 aggregate operation wall-s (4.815016h). The shared
whole-study research intercept is counted once, not once per fit. Separate
worker and reader process RSS peaks are recorded in their summaries; none is
a simultaneous sum. Actual computation was below the20–50 CPUh forecast;
that is a measured price update, not permission to spend the unused ceiling.
Earlier B03/B04 expenditures and incompletely metered design, implementation,
review, publication and scientific support remain additional and nonzero.

Post-result saved-data arithmetic introduced no new model, physics, G or
optimizer call. The full diagnostic reducer cost.801675567 CPU-s/3.425375493
wall-s; two small metered schema reads cost.009599390 CPU-s/.023916195 wall-s;
the collection/hash/compact-summary pass cost.141574234 CPU-s/.145100535 wall-s.
Other interactive reading/arithmetic support was not completely metered.
The [compact diagnostics](../../../../runs/uav_decision_generalization/b05_request_read_a02/diagnostics-summary.json)
retain all primary/secondary components and training blocks. The unique full
checks, curves and diagnostic records stay on configured `local_linux` at
`/home/fires/hmasd-wsl/runs/uav_decision_generalization/b05_request_read_a02`;
[collection](../../../../runs/uav_decision_generalization/b05_request_read_a02/collection.json)
pins1,714 scientific output files/15,641,765 bytes and their identity inventory.
Worker raw/checkpoints remain in their previously verified canonical output.
No sole evidence or adverse mission was discarded to reduce the reported cost.

**Interpretation before independent disposition.** The previously read and
currently published RESEARCH topic5 separated conditional geometric execution,
task opportunity and learned acquisition. B05 now replaces the untested new-
task premise with actual complete G/R request service; low load plus competent
ordinary planning remains a strong explanation for limited mean-C headroom,
but does not establish optimality or erase R's measured tail capability.
Supplying the executor has removed geometric-skill discovery from the learned
decision interface; it did not suffice for this residual TD recipe to improve
complete use. This narrows the tested learning claim without giving a common
cause for the different old B03/B04 failures. Package evidence, component
mechanism, default adoption and next investment remain separate. The original
independent ResearchCritic is reading the complete results and adverse sources;
its substantive recommendation and the DM's resolved continuation judgment
follow below. No follow-on fit, task retuning or new effect is selected here.

<a id="b05-final-cleanup"></a>

**Measured B05 cleanup,2026-10-03 UTC.** The result reviewer confirmed it did
not need the disposable corrected-reader source snapshot; current published
source and all61 bound source hashes cover that reading. The supported native
collector previewed eligibility, rechecked terminal identities/live process
references/reachability, and removed
`.git/hmasd-launch-sources/2d1c05fb36de4ed78104c1f41ae5ca1b`.
Its allocated size fell1,834,201,088→0 bytes and its worktree registration is
gone. The canonical result output was untouched by source removal. The
documented read-only sudo process scan passed; there is no tool blocker.

The worker's immutable manifest and complete reader preserve all11 closed
endpoint count records; its final live-child list is empty. Both native
operations are terminal. The observer is stopped at generation18, every
saved event is consumed and no wake is pending. After checking those consumers,
the DM also deleted the worker's obsolete `scratch/` count buffers, worker and
reader `progress.json`, and the four superseded launch/observer request JSONs
under `temp/directions/uav_decision_generalization/`, then removed that empty
owned directory. These files are outside the5,530 required worker scientific
files; all of those files still exist. No raw trajectory, checkpoint, original
failed request, full independent check or contrary outcome was deleted.

These final-stage deleted targets occupied1,834,733,568 allocated bytes. The
measured combined footprint of this source snapshot, canonical worker/reader
output trees and owned temporary directory fell by **1,834,725,376 bytes net**;
the difference is8,192 bytes of added compact collection accounting. The first
accounting assertion detected one extra4KiB allocation block from writing the
record; its corrected final measure includes that growth. Other writers and
Git object storage are outside this measured scope. The two earlier source
removals separately reclaimed3,664,814,080 bytes as recorded above. No whole-
tree backup, tarball, duplicate raw copy or retention chain was created.

No disposable target remains. Useful B05 source/tests stay on main: the
request/executor/G/R capability and bound adverse learner/complete-reader
reconstruction remain scientific assets. One canonical local worker output
(396,664,832 allocated bytes) retains the source-bound raw/initial/final/
training-state evidence required to reconstruct the full declared comparison;
the reader output occupies16,240,640 allocated bytes including all1,708 checks,
curves, compact readings and provenance. These retained unique records are
the actual leftovers, not an unresolved cleanup failure. The
[collection record](../../../../runs/uav_decision_generalization/b05_request_read_a02/collection.json)
contains exact targets, before/after allocations, native collector result and
all preserved input/output identities.

The source deletion meter reports1.359717597 CPU-s/1.381833690 wall-s; scratch
cleanup reports.121886494 CPU-s/.143836667 wall-s, with the separately recorded
empty-parent bookkeeping cost. Known cumulative B05 CPU before the independent
result review is19345.593921s; remaining accounting, static/support/publication
and final write tails are additional and incompletely metered, not zero.

<a id="b05-independent-result-review"></a>

#### 2026-10-03 — Original independent B05 result review

The registered ResearchCritic reused its separate construction-review context,
reconstructed original evidence before receiving the DM interpretation, and
returned the following complete answer. It was not the proposal coauthor or
engineering reviewer. The earlier interrupted digest-typo consultation does
not substitute for this substantive result review. No new model/native/optimizer
execution was performed in this review.

````text
**Recommend retaining G and R’s conditional ordinary capability, stopping this DDQN recipe, and making no automatic follow-on purchase.** The result changes the explanation from uncertain task opportunity to demonstrated ordinary competence plus actively harmful finite learning.

This is a follow-up in the existing independent review context, reusing the earlier construction analysis. I reconstructed the results before reading the DM’s proposed interpretation and continuation recommendation.

I checked the unchanged 61-source scientific identity and bound inputs; independently reduced all 160 main request ledgers and consequential summaries; examined all three training curves and all 96 learned endpoint score histories; checked selected positive/adverse native arrays, three exact initial-versus-G audits, and two original R rollout traces. I relied on the completed reader for exhaustive physical reconstruction and frozen neural evaluation. I did not repeat its model calls or replay optimizer updates.

| Program | Mean request cost C ↓ | Mean difference from G | Unfinished requests |
|---|---:|---:|---:|
| G | 2605.56 | — | 0 |
| R | 2545.97 | −59.59 | 0 |
| L0 | 5504.88 | +2899.31 | 34 |
| L1 | 5378.69 | +2773.13 | 34 |
| L2 | 5089.47 | +2483.91 | 24 |

Each learned endpoint loses to **both G and R on every main world**. Across three independently trained fit means, L−G is +2718.78, with descriptive df2 interval [+2189.74, +3247.82], conditional on the common evaluation panel. The 96 learned episodes are not 96 independent training replications. These findings agree with the [complete reading](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b05_request_read_a02/reading.json).

The failure extends beyond terminal penalties. Every learned endpoint also increases residence-area cost on every world. For example, L2 raises C from 3335 to 9643 in world 109253023 despite eventually completing every request. Learned policies leave requests unfinished for as long as 860, 1000 and 700 ticks across the three fits; completed-request tails must therefore remain accompanied by unfinished ages.

**The learned intervention was sufficiently exposed to judge this recipe.** It changes movement relative to same-input G on 1064, 1076 and 1131 of 1888 usable decisions. Mean UAV-target changes rise from G’s 10.94 to roughly 71–74 per mission, with more interrupted service, flight and queued residence. This is active adverse intervention, rather than nonactivation, sparse exposure or deadline fallback.

A further diagnostic sharpens that conclusion. The stored **total cost estimates**, including G/1200 plus the residual, are negative on 7676/7680, 7673/7680 and 7266/7680 final action rows. Selected estimates are negative on every L0/L1 decision and 1865/1920 L2 decisions, although actual remaining costs are nonnegative. Saved training estimates begin nonnegative and subsequently drift below zero; late update targets also become negative.

This establishes badly miscalibrated finite value learning. It does **not** establish that a common negative offset caused the action-ranking errors: offsets alone preserve rankings. My inspection of the actual update found positive immediate costs, cost-minimizing selection and terminal-masked bootstrapping. It supplies no identified sign-clamp, longer-training or larger-network repair, and does not substitute for optimizer replay.

The task’s supplied executor and public state are adequate for strong ordinary performance: G and R each complete all 1848 requests. The zero residual represents G and the initial audits reproduce it exactly. Thus task feasibility and representation of a competent baseline are established here; useful acquisition by this finite recipe is not. Broader learnability remains unresolved. This new centralized request task also does not diagnose the earlier B03/B04 geometric-learning failures.

**R has a useful positive result that should survive closure.** Its mean C improvement is uncertain: −59.59, paired descriptive interval [−225.37, +106.19], with 17 gains and 15 losses. Nevertheless:

- Mean within-mission maximum completed-request residence falls by 98.31 ticks, with 25 improvements, six losses and one tie.
- Mean within-mission maximum user-service gap falls by 75.81 ticks, with 23 improvements, eight losses and one tie.
- Both descriptive intervals exclude zero, while remaining secondary, unadjusted exploratory comparisons.

World 109253008 is a particularly useful constructive example: G→R changes C 3007→2352, maximum request residence 484→244, maximum user gap 945→563, and flight 5993→5512 metres/UAV. Conversely, world 109253017 raises C 2319→3062 while improving both maxima. These are real package outcomes; unidentified component contributions do not annul them.

The price is consequential. Across the panel R adds 2253 metres/UAV on average, increases flight in 29/32 worlds, and reduces average routed users by 1.26. Its inclusive deployment CPU averages 196.79 seconds per mission versus G’s 2.15. However, all four cohorts finished at every R decision; the maximum main-panel decision took about seven seconds against the 20-second allowance. R was computationally feasible under this contract. Its approximately 92-fold relative CPU cost does not itself establish impracticality.

Small learned positives also remain: L2 reduces flight and improves average radio service in worlds 109253007 and 109253031. But C rises by 3490 and 5548, and maximum user gaps worsen. Those observations do not support adopting the learned package.

The completed purchase cost **19,343.158526 measured CPU-seconds, or 5.3731 CPU-hours**, through the final reader summary, including the retained failed reader attempt and earlier charged preparation/collection. Training acquisition accounts for 6231.785849 seconds; the full reader for 5653.181264. GPU use was zero. Subsequent support and earlier B03/B04 expenditure remain additional. All learned endpoints cost more than G online, so there is no CPU amortization against G. Their roughly 10–11-mission CPU crossings against R sacrifice the demonstrated service outcomes and are not quality-preserving break-even points. See the [final cost ledger](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b05_request_read_a02/summary.json).

My successful metered saved-data arithmetic totaled approximately **1.388 CPU-seconds**; retrieval, reasoning and some earlier failed schema reads were incompletely metered.

I agree with the DM’s proposed disposition and would **reserve**, rather than immediately select, the R1-versus-R4 computation comparison. It asks a useful direct question: can less model computation retain the observed tail capability? It need not identify R’s components or become a prerequisite for later learned approximation. Given the learner’s uniform primary losses and G’s complete service, another learned fit currently has weaker support than either retaining the existing ordinary choices or investigating their computation cost.

For a new-world capability decision, the proposed complete 32-world G/R4/R1 comparison—96 H1200 missions, 115,200 native transitions, zero fits, and a complete reader—is a reasonable bounded next observation. The **3–6 CPU-hour and 4–8 support-hour figures remain forecasts**, not an accepted price. The one-cohort algorithm, common activation delay, tape rights, exact reuse and accounting must be fixed before selection. R4 already reuses identical cohorts, so R1 cannot simply be priced at one-quarter of its total CPU.

Its outcomes would change actual choices:

- If R1 preserves useful tails and C while materially reducing complete computation, it becomes an ordinary capability worth retaining and reduces the immediate case for learned approximation.
- If reduced computation loses those benefits, retain R4’s conditional value and reject this compression; that result would neither close learning nor justify another fit automatically.
- If R4’s tail advantage fails to carry to the fresh panel, narrow the generalization claim while preserving the original positive evidence.

Reusing the existing panel and adding only R1 is a cheaper, legitimate exploratory alternative, but answers a conditional development-panel question. Neither version is required to close B05. I verified that other substantive work is already selected; I have not independently reviewed its complete evidence sufficiently to rank its scientific return against this reserve.

**MATERIAL_DISSENT: no — I support stopping the unchanged learner and retaining R’s measured tail capability, with no automatic new purchase. The direct evidence supports the DM’s proposed closure and a reserved, explicitly priced ordinary-computation continuation.**
````

The preserved original answer is8,769 characters/8,833 UTF-8 bytes (excluding
the surrounding fence and its separating newline), SHA256
`0699e58f26c39ac2c4eb149076cc31684e6ee3bc10d1a7220edefa34fce60d3f`.

<a id="b05-independent-disposition"></a>

#### 2026-10-03 — DM disposition and next-investment judgment

**Accept the independent diagnosis and close this complete purchase.**
The DM read the entire original answer, compared its figures with the complete
reader/diagnostic records, and accepts `MATERIAL_DISSENT:no`. The independent
reduction of all160 main ledgers, final score histories and selected original
arrays adds useful evidence to the exhaustive reader; it is not another
physical/model/optimizer experiment. Its approximately1.388 measured CPU-s
are additional to the known19345.593921s DM ledger after collection/cleanup.
The combined known subtotal is approximately19346.981921 CPU-s (5.374162h),
with remaining support and earlier studies explicitly additional. No further
review or Pro round is needed to decide this unchanged completed comparison.

The main scientific judgment changes in three specific ways. First, the new
task's ordinary opportunity is now observed: G and R each cleared all requests
in their public stochastic processes on all32 worlds. This goes beyond the
pre-run conditional settled-slot geometry argument, without claiming success
for all possible arrival tapes or optimal G delay. Second, useful-baseline
representation is demonstrated by the zero residual and exact canonical-G
initial audits; merely supplying that representation/executor did not yield
useful acquisition. Third, the learned package is actively adverse, with
strictly greater residence-area cost as well as greater total C in every
main fit-world, frequent changed motion and badly miscalibrated value estimates.
This is stronger evidence than an inactive module or an unread technical failure.

The review's total-Q finding is consequential: in this nonnegative-cost task,
all true remaining costs are nonnegative, whereas7676/7680,7673/7680 and
7266/7680 final action estimates are negative; selected estimates are negative
1920/1920,1920/1920 and1865/1920 times. Saved estimates start nonnegative and
late targets also become negative. The source preserves positive immediate
cost, minimizing actions and terminal masking. This supports a finite value-
learning/calibration failure, while **a shared negative offset alone cannot
explain a bad ranking**. It does not certify historical optimizer arithmetic
or identify a sign error, useful clamp, larger network or longer fit. The
present result therefore does not select one of those repairs. It also does
not explain the different B03/B04 skill-acquisition failures or falsify the
broader learned-decision question.

**Empirical capability, default use and further research are distinct.**
Keep G as the primary-C/economical ordinary reference and do not adopt any of
the three learned finals. Keep R as a real conditional tail capability:
smaller mean maximum residence and user gap, complete request service, specific
jointly favorable worlds, and all counterexamples. The relative92×CPU price
is not a proof of impracticality: R completed every cohort before the20s
deadline, with main-panel decision maximum7.005458s. Its unresolved primary-C
increment, extra flight, lower mean routed-user coverage and nonuniform tail
effects prevent calling it an unconditional replacement. No missing component
attribution annuls this measured package value. Small learned flight/coverage
positives also survive in the records, without overriding uniform primary losses.

I recommend no immediate unchanged learner replication, extra training,
architecture scan, arrival-rate retuning or outcome-selected model. The present
three-fit recipe has a consistent primary loss and useful G already clears all
requests; another such fit has no prediction of a consequential change. A
nonbootstrapped or otherwise revised learner could be a legitimate later
construction, but no specific complete-use improvement follows from the
negative offset alone. The earlier B03~14.544662 CPUh/B04~.257 CPUh and this
B05~5.374 CPUh, plus substantial incompletely metered support, remain cumulative
evidence/cost. That history neither spends an entitlement to further runs nor
makes a contrary learning result impossible.

**The concrete reserved continuation develops the ordinary positive.** If Root
selects further investment in this request capability, a useful next question
is whether one-cohort R1 retains R4's observed tail benefit at lower complete
computation cost, against G under the unchanged task. A fresh32-world complete
G/R4/R1 panel would cost96 H1200 missions/115,200 native transitions/0 fits,
plus all actual model work and its complete reader. The present **3–6 CPUh and
4–8 support-hour** figures are forecasts to refine in source, not an accepted
budget. R4's exact reuse, shared setup/G work, command delay and deadline
handling forbid simply dividing total CPU by four. R1's exact rule and tape/
reuse/accounting contract must be fixed before any selected execution.

This would be a direct capability/use comparison, not a mechanism attribution
gate or a compulsory pilot for learning. Retaining R4's tails and C at lower
computation would create a useful ordinary program and weaken the immediate
need for approximation. Losing the benefit would reject that particular
compression while preserving the original R4 capability; a fresh-panel loss
of R4's advantage would narrow its generalization scope while preserving these
positive observations. No outcome would automatically authorize another fit.
Adding only R1 to the already exposed panel is a cheaper legitimate alternative,
but its estimand is conditional exploratory reuse, not fresh generalization.

The DM and reviewer agree to **reserve** this continuation rather than launch
it now. Stopping the complete B05 purchase already answers the acquired-package
question; neither unknown causation nor another experiment is required for
closure. Root's other selected work provides a real opportunity cost for a
new3–6 CPUh plus support purchase. I favor returning this concrete comparison
for Root's next cross-question allocation over silently using the unused50h
ceiling. The reviewer has not independently ranked those other projects; I do
not describe it as endorsing a cross-project ordering. The decision to reserve
does not shelve R because its mechanism is unknown and does not end ownership
of the wider question.

All selected worker, reader, collection, interpretation, independent advice
and cleanup obligations are complete. There is no active producer, pending
observer event, unread advice, selected successor or external dependency.
Own RESEARCH standing moves to reserve with the original lead retained; the
bounded native return gives Root the evidence and this next-investment
recommendation. New scope would be a new selected purchase with inherited
positive/adverse evidence and cost, not a restart of B05 or a routine repair.

<a id="b06-request-compute-source-scope"></a>

#### 2026-10-03 — Selected source-only construction of ordinary tail capability

Root has read the complete B05 result, original8,833-byte independent review,
cost and cleanup and accepted its closure. The owner has not archived this DM;
the same runtime retains the broader question. Root now selects construction
of one complete G/R4/R1 successor contract asking whether R's observed tail
capability can be retained with less computation. This is **source, already
paid evidence, static arithmetic and record work only**:0 new native, model,
G/R, neural, fit or health effects; no production runner implementation or
formal request is selected. The old5.374 CPUh outcome is not unused credit,
and B05 source, verdicts, data and accepted operations remain frozen.

The candidate starts from a new32-world, three-program H1200 comparison
(96 missions/115,200 native transitions/0 fits), with any genuinely necessary
extra audit missions and the full reader priced explicitly. The exact first-
cohort law, sample coupling across arms, public information, action/deadline
order, existing R4 reuse and all support/retention costs must be specified
before an investment decision. The new tail-use question does not rewrite
B05's primary C or treat a non-significant difference as equivalence. Current
published RESEARCH topic5's observed G/R competence, R's conditional tails and
travel/coverage/CPU costs, and active DDQN adversity are the design premises;
they motivate an ordinary complete capability comparison without making it
a prerequisite for a different learning proposal.

Root has separately reused the original proposal coauthor to compare this
successor with a potentially stronger complete learning/control alternative.
The DM will first construct its source/exposure/price contract independently,
preserve the coauthor's substantive alternative when received, then use the
existing independent scientific-review context for the actual selection
differences. No extra critic/Pro sequence is implied. Root will choose any
new purchase from that complete contract; current work does not authorize
effects or reopening B05. Writes remain in this direction's notebook and
owned standing, with the existing lead and other directions' accepted work
preserved.

<a id="b06-independent-source-contract"></a>

#### 2026-10-03 — DM's independent complete G/R4/R1 contract, before coauthor advice

**Question and prediction.** Can one ordinary sampled future retain a useful
part of R4's complete-request tail capability while reducing its full
computation cost? This is a constructive capability/cost question, not an
explanation of the failed DDQN or a required attribution study before learning.
My prediction is lower complete CPU for R1 and a retained improvement over G
in the two named tails, with uncertain C/travel/coverage tradeoffs. Four
cohorts may instead be important to choosing useful actions, so substantial
tail loss is a real competing prediction. A one-cohort value at an R4-visited
state cannot answer the closed-loop question after their actions diverge.

This independently constructed candidate precedes the requested coauthor
comparison. It is **not purchased, implemented or executed**. Current work
has used source text, saved JSON/file sizes and standard-library arithmetic;
no new task/model/G/R/neural call, fit, runtime health probe or formal launch.
All B05 code/tests remain unchanged. The source reference is the published
worker `2d754f29308a56a4db81f867ca1b79b5e75f99ad`, source identity
`7eeaaf614fd8d88023f0baba2ca2aa04804b893acb1ecfec52158e9d0e762210`;
its complete independent reader is `195fc8f44d5a375081e8b851a67671bbe9aafb1a`.
The load-bearing modules under
`experiments/candidates/uav_decision_generalization/b05_request_schedule/`
are `task.py` (`PublicState`, `initial_assignment`, `candidate_slots`,
`QueueLedger`), `ordinary.py:g_values`, `native.py:RequestHost`,
`rollout.py:future_tape/search`, `policy.py:Endpoint.decide`,
`worker.py:mission`, and the independent `reader.py`/`storage.py` evidence
format. The contract below follows their actual call/order paths.
Current published background is `399cdcde1c8d71f816960410673fd3712cc3203f`,
topic5. Its concrete effect is to retain economical competent G and costly
but deadline-feasible R4, make their observed tails prospectively named
secondary estimands, and decline an automatic negative-Q repair. B05 C stays
its original primary; this new use question does not relabel that result.

**Population, exposure and complete purchase.** Use exactly the new literal
world IDs `109255000..109255031`, in ascending order, under the unchanged B05
world/geometry, rate, arrival and service law. This range does not occur in
the direction's existing source/notebook/study inputs; no geometry or draw
has been generated or inspected. Preserve master109259999 and all existing
RNG domain definitions. These are32 new indexed pseudorandom worlds under
the same law, not a distribution-shift claim or an optimized seed panel.
For world index j, execute `[G,R4,R1]` rotated left by `j mod3`. Every arm
receives a separate complete H1200 mission:96 missions/115,200 task advances,
5,760 timed decisions and96 terminal accounting reports;0 fits,0 updates,
0 acquired checkpoints and0 training/evaluation checkpoint selection.
There is one persistent ordinary endpoint per arm, each actually cold on
its first request, with no warmup mission. All three complete trajectories
are purchased together; no R1 pilot, winner-based extension or intermediate
selection. B05's32 exposed worlds select the question but do not enter the
new panel's uncertainty calculation.

There are **zero additional result audit missions**. No learned deployment
or checkpoint reload exists here. Each of the96 trajectories and every
recorded model prefix is already covered by the complete reader below.
Within saved evidence, the shared initial public state supplies a useful
R1/R4 first-cohort identity check without buying a fourth arm or more
missions. It is a correctness check, not a positive-effect requirement.
Later equal-input encounters may also be compared from saved bytes; unequal
states never acquire a same-output requirement. Focused synthetic/source
checks for a future implementation have0 native/model effects; any proposed
effectful additional test would be separately counted before selection,
not hidden in115,200. Fresh node admission belongs to an actual later launch.

**Unchanged public task and ordinary actions.** Retain N6/U50, static known
geometry, one BS, FDMA/free-space/native routing, three immutable UAV pairs
and the supplied feedback slot executor. Reset exposes all50 user positions
and the permutation of rates[.6,.3,.2,.1]. A report exposes current float64
UAV positions, routed ACKs, four FIFO counts/head progress values, active
slots and tick; pair assignment is known. Actual request IDs/arrival ages,
the task arrival generator and its future tape are not policy inputs.
No actor/critic training, new communication channel, queue-age feature,
low-level learner, arrival-rate tuning or geometry/action expansion occurs.
The same logical bill is404 reset bytes +61×171 report bytes +60×6 command
bytes =11,195 bytes/mission, 1,074,720 bytes for96; this is not measured
wireless energy or an actual network guarantee. There is no training feedback.

Initial assignment still selects the three highest-rate clusters (ID breaks
ties), tests720 UAV permutations using ceil-distance/30 sum, distance sum,
then lexicographic order, and fixes the resulting three pairs. At a report,
action0 keeps all active slots. Actions1/2/3 move the respective immutable
pair to the one currently unassigned cluster; their inner/outer orientation
minimizes maximum ceil-travel, summed distance, then UAV-ID order. Other
pairs retain their slots. Raw steering and executed float64 native actions,
speed30, service threshold8/10 users and20 consecutive qualifying ticks,
FIFO reset/interruption semantics and terminal penalty240 remain identical.
The team cost is C = all pre-service queue residence charges +240×unfinished
requests, with arrivals on t=0,20,...,940 and no later arrivals.

**Entry, deadline and activation order.** At each t=20d, first activate the
previous pending command (except t=0), then insert that tick's actual arrivals
and charge its queue residence. Construct the public report from the current
native positions/ACK, updated counts/progress and active slots. The parent
starts the same20-second wall deadline before first-process spawn or IPC;
ordinary imports, initialization, serialization, G/features, R model work
and message transport are all inside it. Each result must be ready **and
received** by the deadline. Retain the last eligible complete publication:
G result, R's initial G fallback, or R's latest complete cohort average.
If none arrives, KEEP the currently active slots. Cached diagnostics alone
do not retroactively authorize a late command. On expiry terminate/reap the
same child and account for every attempted/completed prefix before any next
effect. A later request may start a replacement endpoint as the original
deadline program prescribes; this is not a replacement mission or retry.

The chosen command becomes pending. Finish this tick and the next19 ticks
under the already active slots; at t+20 activate pending before the next
arrivals/report. A fast R1 cannot activate earlier than R4 or G. All60
decisions are paid, including t1180's command whose activation at1200 falls
outside task motion; no terminal-unused-work optimization is introduced.
Normal deadline fallback is an outcome of the program, not a technical
failure or reason to drop a world. No cohort/arm is rerun merely to finish
more sampling. Save start/ready/receipt/fixed/reaped times, all eligible and
ineligible messages, attempted work and endpoint starts exactly as in B05.

**G, R4 and precisely one R1 cohort.** G is the corrected B05 program:
evaluate all four candidate commands through min(240,1200−t), retain current
slots for its first20 ticks, model known integer heads/progress exactly
under its geometric availability approximation, use rate-fluid only for
unknown future requests, and include240 times remaining known/fluid work.
Choose raw float64 cost, then action ID. Keep its existing feature
construction/timed wrapper when comparing computation, even though no
network consumes the features. No new tuning or changed G approximation.

R4 is the exact existing optimized program, including full-input cohort
reuse. It computes G first and publishes that fallback; then reconstructs
one native model strictly from the public state. For each decision d it
considers tape indices0,1,2,3 in that order. **R1 does the same, but only
tape index0; it does not choose the best tape, resample a rejected tape,
rotate the tape index by world, use expected arrivals, or start cohort1.**
The future draw for index k is PCG64/SeedSequence
`(109259999,30,world,d,k)`, with shape `(number_of_future_times,4)` and
elementwise comparison to the public rates. Future times are t+20,... up
to min(t+min(160,1200−t),940), including the nonterminal G-tail endpoint.
The current tick's arrivals are already in the reported counts and are
never sampled again.

At the same world/tick, R1's sole future tape is exactly R4's tape0, even
after their physical states diverge, since rates and future-time grid agree.
Different k and world addresses use separate streams. Actual arrivals use
the independent existing domain21; rates use20. Neither model receives the
actual future tape or task RNG state. These are common random inputs for a
paired program comparison, not independent realizations between R arms.
G uses the public expected rates only. New actor information is not the
intervention; the computation/sampling allocation is. No cross-arm result
or trajectory cache is permitted, even when a state happens to match.

Within a unique cohort, evaluate all four actions in ascending IDs rotated
left by `(world+d+k) mod4`, preserving the original cancellation-order
semantics. Each branch clones the public reconstructed model, sets its
pending candidate, retains old active slots for20 ticks, then replans with
G at the subsequent20-tick boundaries. Native RF/routing, queue charges,
arrivals, command activation and FIFO completion use the original order.
At a nonterminal160-tick endpoint, activate the last pending command and
insert the endpoint arrivals; add min G as the tail without double-counting
that endpoint's first residence charge. At1200 use the terminal240 charge.
This is a finite sampled model with an approximate G tail, not a theorem-
certified improvement over G. No new tail objective enters its choices.

Publish a cohort only after all four candidate branches finish. After m
eligible complete cohorts, choose the action minimizing `(mean_m_cost,
raw_G_cost,action_ID)`. For R1, m is either0 (G/KEEP fallback) or1. For R4
it is0..4; duplicate cohorts retain their statistical multiplicity in the
mean. The exact reuse key frames source identity, world, reset geometry/
rates, full public report, pairs, future times and sampled bits. Reuse is
only within that decision and only on full-key equality; no approximate
state merge, result reuse between worlds/arms, or discarded adverse sample.
At t≥940 all future tapes are empty, so R4 has one physical cohort and
four logical copies. Earlier identical sampled tapes also reuse. R1 has
one physical/logical cohort if complete. This common setup and late-task
reuse are why total R4 CPU cannot be divided by four.

**Exactly counted dominant work.** The following are complete-worker maxima
with all requests finishing before the deadline, retaining mandatory empty-
tape reuse but not anticipating earlier accidental equality. A deadline or
earlier exact equality can reduce realized work; attempted interrupted work
is still counted and checked. Let h(t)=min(160,1200−t). The sum of h over60
decisions is9,040. R4 has four unique cohorts for47 decisions t<940 and one
for13 later decisions:201 physical/240 logical cohorts per mission. R1 has
60/60. Each physical cohort contains four native branches. Internal G
queries occur at offsets20,...,h−20 plus the nonterminal endpoint; actual
report G is counted once, including R's duplicated trace record.

| Work per complete mission | G | R4 maximum | R1 maximum |
| --- | ---: | ---: | ---: |
| Actual task advances | 1,200 | 1,200 | 1,200 |
| Timed/base G queries | 60 | 60 | 60 |
| Base G candidate-ticks | 52,320 | 52,320 | 52,320 |
| Native public model constructions | 0 | 60 | 60 |
| Native model prefix advances | 0 | 126,400 | 36,160 |
| Internal G queries | 0 | 6,288 | 1,776 |
| Internal G candidate-ticks | 0 | 5,813,760 | 1,536,000 |
| Physical / logical cohorts | 0 / 0 | 201 / 240 | 60 / 60 |

Across32 worlds:115,200 actual advances,3,840 model constructions,
5,201,920 model prefix advances,8,352 physical cohorts/33,408 clones and
9,600 logical cohorts. All G work is263,808 queries/1,055,232 candidate
values/240,215,040 candidate-ticks/960,860,160 four-cluster recurrences;
base queries are5,760 and internal queries258,048. R4's model ceiling alone
is4,044,800; R1's is1,157,120. No native or model transition is substituted
for a fit count. Preserve native constructor/reset/reward/routing event
accounting as well as these dominant counts. Complete R4/R1 future draws
are5,568/1,392 uniforms per mission,222,720 in total, plus18,432 actual
arrival uniforms; all tape generation and comparison work is included.
There is no neural forward,
optimizer replay, teacher-label acquisition or hidden alternate seed search.

**Complete reader and artifact contract.** One bound reader checks every96
mission, all115,296 actual physical states (including constructors), all
115,200 actual motions/actions and every request's FIFO identity/timestamps.
It independently reconstructs saved geometry/rates/actual-arrival draws,
reset assignment, physical links/routes/ACKs, queue costs and pending-command
activation, and checks every completed/partial R record: model initial
state, tape address/bits, branch order, native prefixes, G queries, exact
reuse/multiplicity, scores, publication markers and deadline-selected action.
It validates all possible3,840 model initial physical states and up to
5,201,920 model prefix states, and recomputes up to240,215,040 G candidate-
ticks (the duplicated base record is matched, not charged twice). Total
reader physical-state ceiling is5,321,056. It reconstructs saved work;
it does not buy new native worlds, extra model trajectories or suffixes.
No training/checkpoint/neural checks are needed because none were purchased.
This removes an inapplicable old obligation, not promised model verification.

The implementation, if selected, must retain the unchanged G/R4 algorithms
and source identities and add a separately bound R1 cap rather than edit
B05 evidence. Frozen B05 modules remain the reference; the future direction-
owned entry/reader needs a narrowly reviewed cap, arm labels,96-mission roster,
counter ceilings and schema. Preserve full requested/executed commands,
all native state/motion/routes, actual request tape/ledger and all unique
model prefix evidence, G inputs/scores, cohort aliases and timing/cost
snapshots. Compact per-world metrics, full32 paired vectors, config/source
manifest, terminal status and collection identities go to Git; required
bulk has one canonical run copy. No replacement command is reconstructed
from only an average score. Reader failure preserves the raw/partial result
and limits dependent scientific claims; it does not become a negative result.

**Prospectively read service, tails and price together.** C remains primary
service cost. Name the following key secondary tails before the new worlds:
T = maximum completed-request residence within the mission; W = maximum
longest routed-service gap over all50 users, including leading/trailing
zeros. Retain all request/cluster/user values, unfinished counts/ages,
completed count and total requests. Also report the maximum of completed
residences and observed unfinished ages as a censored lower bound, never
call it a completed-request tail. If an arm has no completed requests its
T is missing with that fact explicit, not zero or an excluded successful
mission; if no requests arrive, report an empty workload separately. A
reduction in completed-only T accompanied by extra unfinished requests is
not evidence of preserved complete-service tails.

Read C's area/terminal components, T/W, per-cluster completions/interruptions,
all-user routed fractions/never-served users, mean routed users per tick,
team-zero-service runs, travel metres per UAV and target changes together.
Travel is movement cost, not unmodeled battery energy. Save inclusive task
CPU/wall (constructor, cold start, actual motion, policy, IPC/cancel/reap,
trace serialization), decision max/quantiles/deadline misses, logical and
physical cohorts, all query counts, reader costs and whole-study costs.
No arbitrary CPU-to-request-cost exchange rate creates a scalar winner.

For each metric report G/R4/R1 means, all32 paired values and signed
R4−G/R1−G/R1−R4 contrasts. Use a descriptive paired-t interval with df31
on world differences, retaining covariance and the shared model tape0;
worlds, not1200 ticks/requests/cohorts, are the inference units. This is a
new exploratory panel after B05 question selection, not multiplicity-
controlled confirmation or independent replication of learned fits. No
missing tail is filled with zero or silently dropped to manufacture32
pairs: print its world and missingness, and withhold an unconditional
32-world T interval if any required T is undefined. C, unfinished service,
W and the saved censored readings remain readable on every world. No
non-significant R1−R4 difference establishes equivalence. No equivalence
margin is invented from B05's observed effect or SE. Clear CPU savings and
recurrent favorable T/W versus G can establish a useful cheaper conditional
program even when causal components or R1−R4 equality remain unidentified.
Any C/unfinished/travel/coverage sacrifice remains visible in that use claim.

Outcomes change the next choice as follows. If R1 is substantially cheaper
and has useful fresh tails versus G, preserve/develop that conditional
program; C and unfinished service determine whether any broader adoption
is warranted. If R4's tails recur but R1 loses them, reject this particular
compression and retain R4's positive; its price alone is not infeasibility.
If R4's tails do not recur, narrow their generalization and reconsider the
tail-use investment without erasing B05. If both planners have new C or
completion harms, preserve those counterexamples rather than promote a
completed-only tail. If uncertainty remains broad, report an unresolved
comparison, not equal programs or an automatically authorized larger panel.
An unforeseen deadline/resource failure is read as part of the executed
program/technical completeness respectively. No branch automatically selects
a new fit, changed arrival rate, more cohorts or an unchanged retry.

**Full price from already-paid measurements, not R4/4.** Saved B05 main JSON
gives G mean2.148516 CPU-s/mission (range2.006917..3.138978), of which timed
policy CPU averages.518043 and other mission work1.630473. R4 averages
196.791962 (184.401466..215.959280), with193.760253 in timed policy and
3.031709 elsewhere;32 R4 missions cost6,297.342780 CPU-s and6,855.382789
wall-s. They performed4,029,440 model advances and1,272 reused logical
cohorts. This paid information supports a computation forecast, not a new
R1 timing measurement. All old R4 decisions met20s; maximum7.005458s is a
measured scope, not a deadline guarantee on a future loaded node.

R1's maximum model work is28.61% of R4's reuse-aware maximum, and its
internal G candidate work26.42%; model construction, base G, IPC and actual
missions are not scaled away. Forecast per mission: G2–4 CPU-s, R4 roughly
185–240, R1 roughly55–90, giving about2.2–3.0 CPUh for the complete96-mission
worker. The old full reader cost5,653.181264 CPU-s; the new physical-state
and G ceilings are respectively82.36% and82.21% of its realized counts.
A proportional center is about4,650 CPU-s (1.29h), with1.1–1.7 CPUh a
planning range rather than a benchmark guarantee. Include source snapshot,
import, hashing, readback, summary, collection and publication work; forecast
**3.5–5.5 new CPUh,0 GPUh**, roughly4–7 operation-wall hours, plus **4–8
support-hours** for bounded implementation/review/publication/reading. Some
support CPU/elapsed time remains unmetered and is explicitly nonzero.

Propose a new8-CPUh/24-aggregate-operation-wall-hour stop for worker plus
reader and charged failed/support scientific calls if Root buys this whole
comparison. This is a proposed ceiling, not an allowance or authority now;
the old50h ceiling is not inherited. Preserve all partial evidence and stop
on the first new formal launch/admission/worker/reader failure or aggregate
cap; no automatic repair/retry, duplicate, extra world or continuation is
purchased. Ordinary valid deadline fallbacks do not trigger that failure rule.
Complete fixed collection/read/publication is inside the forecast, not an
unpriced optional stage. A cap-limited incomplete study is not the promised
96-mission/32-world result. Engineering support beyond the forecast changes the price
presented to Root rather than silently spending an unlimited repair loop.

The selected suitable runtime would remain configured local Linux with the
same Python3.10.20/NumPy1.26.3 numerical stack and native source; it is a CPU
study,0 GPU, one sequential mission/ordinary child and a separate full reader.
No fresh resource survey is performed during this source-only assignment.
An actual later launch needs current node memory/disk admission and preserves
all other accepted workers. The prior sole B05 rollout evidence was about
130 MB for35 R4 missions; increased R model work plus96 actual traces suggests
roughly0.2–0.5 GiB retained bulk, with a1 GiB planning reserve. One immutable
source snapshot was about1.71 GiB allocated; allow2 GiB per concurrently
retained snapshot, explicitly up to4 GiB if worker/reader overlap. Avoid that
overlap when their lifecycle permits collection and retirement first. Keep
the existing8-GiB memory/12-GiB free-disk admission floors rather than infer
availability from old RSS. Required unique evidence stays canonical; close
unused scratch/snapshots only after checking live consumers. These are
storage forecasts, not new allocated data or measured savings.

**Competing investments before the coauthor view.** Adding only32 R1 missions
to B05's exposed panel would be cheaper (38,400 actual advances/1,157,120
maximum model advances plus full reader), but answers conditional development
on the panel that selected the tail finding. A fresh three-arm panel buys
its recurrence and program comparison together; that is my present preference
if another request-tail investment is selected. Repeating DDQN unchanged,
clamping its values or adding fit time has no prediction selected by these
source facts. A complete nonbootstrapped learning/control proposal could
instead add acquisition value; it must be compared on its actual ordinary
competitor, information, target exposure, fresh complete-task result and
full price. It need not first pass R1. Await that concrete alternative and
the one reused independent selection-difference review before recommending
which complete purchase Root should choose. No new effects are selected by
this contract or by its prospective outcome branches.


<a id="b06-coauthor-extension-original"></a>

#### 2026-10-03 — Original coauthor extension, received in full

Root has read the independent three-arm source contract and selected a
seven-endpoint offline-student extension for concrete source-only design
comparison, not execution. It retains G/R4/R1 and adds one deterministic
four-constant calibration plus three new offline neural fits using the
existing35 R trajectories. Root will choose one complete purchase after
the actual revised contract and one reused independent selection review.
There is no review of the superseded three-arm proposal followed by a
second review of this extension. A/C/D's accepted work remains independent.
Current authorization is still0 new native/model/G/R/neural/optimizer/fit
effects, no production implementation, runtime probe or formal request.

The original B05 proposal coauthor delivered the following complete answer
at Root's explicit request. This is coauthor advice, not independent
Scientific Reviewer approval or empirical evidence. Original text:
6,691 characters /13,153 UTF-8 bytes; SHA256
`c11d1b5565378d895f7b413acaf9703640bb0b39c9e17e0b451caf96d830e956`.

```text
我建议把下一项选为**一次完整的“R4 请求排程能力能否用较低计算成本实现”的比较**：保留 DM 已构造的 G/R4/R1，再加入一个简单的四常数标定和三个离线学习端点。共七个端点、32 个新世界，全部一次购买。我的实质异议是：**仅选零 fit 的 R1 比较有价值，但在已保存 teacher 数据的条件下，尚未充分利用这次昂贵比较能够提供的学习信息。**

这是我作为原 B05 方案共作者的建议；独立选择判读仍应由 Scientific Reviewer 完成。A、C、D 已接受的研究继续原安排。

**支持改变分配的事实，是可直接复用的训练数据，而不是对 DDQN 失败原因的新解释。**

我完整读取了 B05 的[原始读器汇总](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b05_request_read_a02/summary.json)、[全部诊断](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b05_request_read_a02/diagnostics-summary.json)和独立判读、处置。原结论应保持：

- 三个 learned endpoints 在全部 32 世界的 C 和 residence-area 上均劣于 G/R；目前没有确定的符号、clamp、网络或追加训练修复。
- G/R 均完成全部 1,848 个请求。R−G 的平均 C 为 −59.59，区间跨零；平均 mission 内最大请求 residence 改善 98.31，最大用户服务 gap 改善 75.81。
- R 同时增加约 2,253 米/UAV 的飞行，并降低平均 routed users。它的约 196.79 CPU-s/mission 明显高于 G 的 2.15，但所有原有 cohort 都满足 20 秒 deadline。这是一项有价格、有副作用且可按时执行的能力。

进一步检查原工件发现，**全部 35 条 R 轨迹——32 条主评价和三条 audit——均保存了 60 个决策的四动作输入与完整四 cohort 成本**：

- 共 2,100 个决策上下文、8,400 个动作特征与平均评分。
- 特征数组为每条轨迹 `(60,4,303)`，与现有 scorer 接口直接匹配。
- 全部 2,100 个决策都完成四 cohort；R 有 360 次相对同状态 G 明确改选。
- 388 个上下文的四个平均评分完全相同；KEEP 占 R 动作约 77%。因此普通 action accuracy 很容易给出误导性的好成绩。
- 这些记录已经过完整 reader；不需要新采集 teacher rollout 才能开始学习。

原始入口是[已保存的 worker manifest](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b05_request_a01/manifest.json)。一个实际接口陷阱是：**R 记录中的 `total_q` 保留的是 G 基值，不能直接当 teacher target**；应从已保存的四个 `cohorts[*].costs` 按原程序的 float64 平均顺序重建，并保留重复 cohort 的权重。

复用后，这 35 个世界全部成为明确暴露的训练/开发资料，不能继续作为新学习方案的 holdout。

**我接受 DM 的 R1 源码契约，并在其上增加一种明确的直接学习方案。**

[DM 的完整契约](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:7636)已经解决关键公平性问题：R1 固定使用 tape0；同世界、同 tick 与 R4 的 tape0 相同，实际到达仍由独立 domain21 产生；四动作共享该未来样本；R1、R4、G 均在 20 tick 后激活命令，使用同一 20 秒 deadline。R1 计算更快不会提前获得物理控制机会。R4 的完整输入复用、截止时最后一个合格完整 publication、延迟和 fallback 均应原样保留。

七个端点为：

| 端点 | 冻结的程序 | 它回答的问题 |
|---|---|---|
| G | 已修正、已验证的原有普通控制器 | 经济且能完整服务的基准 |
| R4 | 原有四 cohort 程序 | 较昂贵能力在新世界是否重现 |
| R1 | DM 已定义的 tape0 单 cohort 程序 | 减少在线采样能否得到有用的价格改善 |
| B | 下述四常数标定 | 学生的收益是否仅需一个简单的全局动作修正 |
| S0、S1、S2 | 同一配方的三个独立初始化、独立 shuffle 学生 | 固定 teacher 数据能否形成低计算的完整闭环控制 |

任务、信息、动作集、原生执行和服务成本均沿用 B05。学生只使用当前合法的 303 维特征及 G 值，不增加请求年龄、实际未来到达或隐藏任务状态。

对上下文 \(s\)，记四 cohort 的平均预测成本为 \(\bar R_a(s)\)，G 动作为 \(g(s)\)。学生复用现有 55,553 参数 scorer，部署评分为

\[
S_\theta(s,a)=G_a(s)/1200+f_\theta(x_{s,a}).
\]

训练目标是四动作的相对成本：

\[
\operatorname{MSE}_{s,a}
\left[
S_\theta(s,a)-S_\theta(s,g)
-\frac{\bar R_a(s)-\bar R_g(s)}{1200}
\right].
\]

这使训练直接针对行动排序有关的差异。它不使用 bootstrap，也不把共同 offset 当作已确认的旧失败机制。标签仍然只是有限模型、有限采样和 G tail 的预测，不能称为真实最优 Q。

具体配方可以完整冻结为：

- 三个新初始化 seed：109255101、109255102、109255103；shuffle 使用独立的新地址，例如 `SeedSequence(109259999,51,fit)`。
- 全部 2,100 个上下文，64 epochs；每批 64 个上下文，保留末批 52 个。
- Adam，学习率 \(3\times10^{-4}\)，默认 betas/epsilon、无 weight decay，固定梯度范数上限 10。
- 每个 fit 2,112 次更新，固定使用最后端点；无 checkpoint 选择、追加 teacher 查询或根据新评价调整 epoch。
- 初始 head 精确为零，初始部署定义为 canonical G；保存证书并离线核验初始网络。无需额外购买三份相同的初始原生轨迹。

简单标定 B 使用同一数据，直接拟合四个常数：

\[
b_a=\operatorname{mean}_s\left[
(\bar R_a-G_a)
-\operatorname{mean}_{a'}(\bar R_{a'}-G_{a'})
\right].
\]

部署时按 `(G_a+b_a, G_a, action_ID)` 排序。它明确计为**一次确定性四参数拟合**；另有三个神经网络优化 fit。若 B 已能实现学生的收益，便没有证据要求更复杂的网络。

**新观察必须是完整闭环评价，不能用旧 R 状态上的排序准确率替代。**

沿用 DM 尚未生成或查看的世界 `109255000..109255031`。每世界运行七条独立的 H1200 轨迹，按世界索引轮换七个端点的执行顺序。每端点首请求真实冷启动，没有 warmup mission；所有 checkpoint 在评价前冻结。R1/R4 不共享跨 arm 缓存。

三份学生都使用同一个旧 teacher bank，因此是三个优化随机性重复，**不是三次独立数据获取**。35 个旧世界、相邻决策的相关性，以及学生偏离 teacher 轨迹后的状态分布，是这次学习方案的主要科学限制。新 32 世界的完整任务恰好检验这种限制，不需要先做一个正面 pilot。

不增加结果 audit mission。每条新轨迹都由完整 reader 检查，学生从冻结 checkpoint 重新加载后重算全部决策；初始 G 等价由源码、证书和离线检查覆盖。

**主要数量如下；相较零 fit 面板，模型预测量完全相同。**

| 项目 | 推荐完整研究 |
|---|---:|
| 新完整任务 | 224 |
| 原生 task advances | 268,800 |
| 定时决策 | 13,440 |
| 新训练所需原生任务／teacher model 查询 | 0／0 |
| 神经网络优化 fit／四常数标定 | 3／1 |
| 优化更新总数 | 6,336 |
| 训练上下文呈现／动作行 forward | 403,200／1,612,800 |
| R model initial constructions | 3,840 |
| R model prefix advances 上限 | 5,201,920 |
| 物理／逻辑 cohort 上限 | 8,352／9,600 |
| G 查询总数上限 | 271,488 |
| G candidate-ticks 上限 | 246,912,000 |
| 完整 reader 的实际任务 physical states | 269,024 |
| reader 全部 actual/model physical states 上限 | 5,474,784 |

R4 每任务的模型上限为 126,400，R1 为 36,160。t≥940 的空未来 tape 使 R4 只需要一个物理 cohort，再以四份逻辑权重参加平均；因此不能把 R4 的完整 CPU 简单除以四。

相较 DM 的 96-mission 面板，新增的是 **153,600 原生 advances 和 6,696,960 G candidate-ticks**。昂贵的 R/model 部分没有增加。

reader 应重建全部旧标签、检查输入文件身份并读取全部更新记录，验证三个初始和最终 checkpoint，以及全部新原生和模型记录。旧 teacher 数据以已通过完整 reader 的哈希绑定工件为依据，不再重复执行旧 4,407,360 个模型 prefix。新 reader 仍完整重算本次全部模型/G 工作。默认不重跑全部 optimizer；初始/最终 bank 检查和新冻结评价在 worker、reader 两侧都计算时，全部神经网络 forward 约 **1,759,680 动作行**，含上述训练 forward。

完整通信逻辑账仍为每任务 11,195 bytes，本次共 2,507,680 bytes；这只是该接口的 payload 账，不代表无线能耗。

**完整新增价格建议报 4–7 CPUh、0 GPUh，加 8–14 support-hours。**

DM 的零 fit 面板为 3.5–5.5 CPUh、4–8 support-hours。额外机器费用较小有实际依据：旧 B05 三个 learned endpoint 的平均完整任务 CPU 分别为 2.872、2.887、2.847 秒，接近 G。这里只用这些已有测量支持量级预测，不当作新学生 benchmark。新增 96 个学生任务和 32 个 B 任务预计约十分之一 CPUh；训练、额外 reader、导入和工件处理另计，并为未知项保留余量。

增加的主要价格是训练数据绑定、独立训练入口、checkpoint 协议、reader 和数值/RNG 复核，预计较窄方案多约 4–6 个支持小时。我不把这项人工与代理工作藏进“免费复用”。

建议新研究采用 **10 CPUh／24 aggregate-operation-wall-hour** 上限，计入 worker、reader 和收费的失败科学调用；不继承旧 50 小时预算。完整运行预计约 5–9 个 operation-wall hours，支持工时另列。保留部分证据与失败状态，不通过自动追加世界、改变配方或替换失败 fit 补齐表面样本数。

已有 B05 的约 **5.374 CPUh，加未完整计量的支持费用**，是此前取得 teacher 资产的实际价格。此次复用只有边际采集费用为零，不能把整个学习路径称为零成本数据获取。

保留 bulk 预估 0.3–0.7 GiB，按 1 GiB 规划；source snapshot 按每个约 2 GiB、可能并存两个计价。实际 launch 沿用 8 GiB 内存、12 GiB 空闲磁盘 admission floor；节点可用性届时检查。旧 R 数据已经成为本研究的明确消费者，应保留一份必要证据。这里没有执行资源探测或新科学调用。

**判读应同时保留获取增量、普通竞争和服务代价。**

C 继续作为主服务成本；预先声明 completed-request 最大 residence \(T\) 和全部 50 用户最大 gap \(W\) 为关键次指标。比较包含：

- 学生相对 G：是否取得初始策略之外的实际能力。
- 学生相对 R1：是否具有竞争力的完整低计算控制。
- 学生相对 B：上下文学习是否超过简单全局标定。
- R1/R4 相对 G、相互之间，以及学生相对 R4：新世界中的能力与价格关系。

同时报告完成数、未完成数及年龄、C 的面积与 terminal 项、全用户覆盖、飞行距离、目标变更、CPU/wall、deadline 和实际调用账。少完成请求而降低 completed-only \(T\)，不能算保留了完整服务能力；无完成请求时 \(T\) 缺失，不能填零。

保留全部 32 个配对值。世界配对区间条件于这三个已拟合模型；另外列三个 fit 的平均差值与随机性范围。不能把 96 个学生世界结果当成 96 个独立 fit，也不能把三份优化重复当成三份 teacher 数据重复。这里是预先定义的新探索比较，不声称多重性控制的确认研究。R1−R4 或学生−R4 区间跨零不建立等价，不从旧观测反推一个便利的非劣界。

这个完整观察能改变实际选择：

- **R1 在新世界保持有用的服务尾部且明显便宜**：保留并发展 R1；学生失败也不妨碍这个正面结果。
- **学生取得超过 G/B 的服务增量，并以较低 CPU 接近有用的 R 能力**：得到条件于本任务、数据和模型的可用学习资产。任何 C、完成率、飞行或覆盖牺牲仍进入使用判断。
- **B 已达到相同用途**：优先保留简单标定，不声称神经网络复杂性必要。
- **三个学生均失败而 R 仍有用**：关闭这一个固定数据、固定目标、固定配方的摊销尝试；继续保留 R 能力。结果不自动授权更多 epoch、DAgger 或 DDQN 修补。
- **R4 尾部在新世界未重现**：收窄原能力的泛化判断，同时保留 B05 的正面与负面原记录。

仅跑 R1 的方案仍然合理：它实现简单、支持费用较低。我的优先级不同，是因为现在有一批已付费、完整保存、接口可直接接入的四动作 teacher 数据；在同一次昂贵 R/reader 比较中，增加有限的支持工作，便能同时比较“减少在线采样”和“离线学习摊销”两条完整实现路径。它不依赖 R1 先胜或先败，也不会把正面 R 能力悬置为失败归因的附属品。若 Root 无法承担这项明确的支持费用增量，我的第二选择是 DM 的完整零 fit 面板；目前证据不支持直接停掉请求排程问题。
```

<a id="b06-seven-endpoint-source-contract"></a>

#### 2026-10-03 — Revised complete seven-endpoint contract for one selection review

**Actual candidate and scope.** I recommend comparing two constructive ways
to reduce the complete cost of the retained R capability: less online
sampling and finite offline amortization. The actual proposed purchase is
G/R4/R1/B/S0/S1/S2 on32 new worlds, preceded by one deterministic four-
constant fit and three fixed neural fits on an already acquired bank.
This supersedes the three-arm *proposed purchase/counts/price*, retaining
its exact task, G/R4/R1 program, sampling, information, delayed activation,
deadline, output and no-extra-audit definitions. It does not supersede B05
or select an effect. Root asked for this source-only comparison after
reading the coauthor's complete answer. No production code, new bank,
network/optimizer call, fit, native/model/G/R evaluation or resource probe
has been performed. All scientific computation below remains prospective.

The new prediction is that fixed full-menu relative-cost supervision can
turn some of R4's useful behavior into low-cost closed-loop control. The
reason for this investment is the available verified four-action data and
R's positive package capability, not an identified DDQN mechanism. A
55,553-parameter network may fail to fit the useful ranking, may overfit
35 correlated worlds, or may produce harmful decisions when its own
trajectory leaves R's state distribution. R1 or a simple global correction
may already capture the useful tradeoff. Those are the intended competing
answers, not contingencies that must be eliminated before buying the study.

**Reused teacher inputs and exposure.** Canonical source is
`runs/uav_decision_generalization/b05_request_a01/`, with original manifest
SHA256 `3c3c7c84af0c0b55a4669e71bbad361d5b4e391e26bd237ee59a3f2aea639026`,
config `e675836d1775dcbb414395109ca062b8a3bb8341d196a39eab80f87db643e668`
and summary `d06794e1287e7fca7fd815ec77a4a1e17f6a133f87c42f023ccf50ca42605edd`.
The completed original reader summary at `b05_request_read_a02/summary.json`
has SHA256 `8a0a24d9ec71fcfbd892e46729b61e98585a2fbba57ca0a5a4456610f9776612`.
Its certification remains scoped to its original source and records, not
to this unimplemented new learner. Before a future use, bind these originals
and the exact required file identities from their manifest; do not retype
truncated digests or infer a whole-bank certificate from only a path.

The bank contains exactly the old32 `main/R` trajectories with world IDs
109253000..109253031 and `audit0/R`, `audit1/R`, `audit2/R` at109253900..902.
Order contexts by ascending numeric world, then decision0..59; action rows
are0..3 within each context. All2,100 contexts/8,400 action rows are used,
including terminal-unused decisions, tied scores and physically aliased
choices. There is no outcome-based pruning or weighting. Every world has60
contexts, so uniform-context loss gives equal total weight to each of
these35 worlds, without making its60 states independent observations.
All35 worlds, including the former audit/main panel, are now declared
training/development exposure for this successor. They are not its holdout.
The coauthor's observations of360 R-versus-G changes,388 all-equal menus
and approximately77% KEEP explain why unweighted action accuracy is weak;
they do not establish learnability or determine a filter.

For each context read its saved float32 `(4,303)` features, canonical
float64 four G costs from the report, and the original four ordered cohort
cost vectors. Reconstruct Rbar with the exact worker operation
`np.mean(np.stack([costs_k for k in (0,1,2,3)]),axis=0,dtype=np.float64)`.
Keep every duplicate cohort as one of those four samples. Require all four
committed cohorts, matching selected complete publications, action IDs,
reuse aliases and saved costs. Read/check the2,100 saved rollout files'
identities and compact score/marker/alias fields against the original
manifest and checked mission records. Do not recompute their native model
prefixes. **R's stored `total_q` is G/1200, not Rbar, and is not a label.**
Old actual C, realized future arrivals, request ages and DDQN outputs do
not enter labels or features. The original three TD checkpoints remain
adverse evidence only; no weights or optimizer state are inherited.

Old inputs are consumed in place, with one canonical copy. A small derived
bank may retain exactly the2,100 feature/G/label rows, ordered source keys
and their identities for the new fit; it is not a copy of the old trajectories
or model evidence. The new worker and reader each reconstruct the label
arithmetic from the bound originals; neither acquires a fresh teacher query.
The original full physical reader is reused as evidence for the old teacher
records. Rechecking hashes/labels is charged new support/verification, not
a second4,407,360-step historical model reconstruction.

**Fixed representation and three supervised fits.** Reuse only the B05
`ResidualScorer` architecture/interface:303→128 ReLU→128 ReLU→1,55,553
CPU float32 parameters, with exact zero output-head weight/bias. Existing
feature slices/scales are unchanged: public user geometry/rates, positions,
ACK, counts/head progress, pair membership, active and candidate slots,
action ID, t/1200 and all four G/1200 values. No feature normalization fit,
age, hidden state, future sample or teacher score is added at deployment.
Retain raw G in float64; the feature copy of G is deliberately float32 as
before. An all-zero residual represents G, but equal mathematical argmins
alone are not a deadline execution certificate.

Initialize the three new scorers at109255101/109255102/109255103 using the
existing forked CPU Torch RNG and default Linear initialization, then zero
their final heads. Seeds refer to optimization replicates, not new bank
draws. Each fit owns one PCG64 shuffle generator from
`SeedSequence((109259999,51,fit_index))`. At each of64 epochs draw a fresh
permutation of all2,100 context indices without replacement, then process
32 batches of64 and the final batch of52 in order; do not drop/pad/resample
the last batch. No evaluation outcome changes a permutation or epoch count.
Each fit therefore makes2,112 updates; total6,336, with403,200 context
presentations and1,612,800 neural action-row forward evaluations. There is
no replay buffer, exploration, target network, bootstrap or online update.

For each context let g be canonical argmin of unscaled float64 G (action ID
breaks a G tie). Let `q = G/1200 + float64(f_theta(x))`. Use precisely the
float64 scalar batch loss

    mean_over_contexts_and_all4actions(
      ((q[a]-q[g]) - (Rbar[a]-Rbar[g])/1200)**2 )

including the anchor's zero row. Compose q before its subtraction in this
fixed order, preserving inference arithmetic. Features, network parameters
and network outputs remain float32; conversion and target/loss arithmetic
are float64, with gradients propagated through the cast to float32
parameters. No cast of raw G to float32, detached learned anchor, clipping
of costs/residuals, label smoothing, sample weighting or auxiliary loss.
The per-batch mean divides by actual `4*batch_size`, including208 in the
last batch. Adam is lr3e-4, betas(.9,.999), eps1e-8, weight_decay0,
amsgradFalse, foreachFalse, fusedFalse, maximizeFalse; clip the total
parameter-gradient L2 norm at10 before each optimizer step. Check finite
loss, every gradient, norm, optimizer state and parameters. No scheduler.
Use the same configured CPU stack, Torch2.7.0+cpu, four Torch intra-op
threads/one inter-op thread and deterministic algorithms; actual whole-
process CPU includes its native thread teams. No CUDA or mixed precision.

This loss constrains relative values only. A common offset is unidentified;
nonnegative absolute outputs are not an admission/adoption rule and a
negative offset alone is not an explanation of ranking. The teacher itself
is the finite four-sample native-prefix/G-tail program, not true optimal Q,
an exact Monte Carlo return or a guarantee of complete-service improvement.

**One competent deterministic four-constant comparator.** I make one
specific correction to the coauthor proposal for independent review. Its
closed-form centered mean is optimal for a centered all-action residual
criterion, but generally not for the actual G-anchored criterion when g(s)
varies with state. To avoid mistaking a weak global fit for a need for
contextual learning, define B as the exact finite least-squares optimum
within four action constants for that same relative-cost loss. This is one
four-constant deterministic fit (three identifiable contrasts), not another
NN seed, grid, fifth baseline or an extra collected label.

Use raw-cost units `y_sa = (Rbar_a-Rbar_g) - (G_a-G_g)` and the row
`A_sa = onehot(a)-onehot(g)`, in the fixed context/action order above.
Starting from zero float64 H[4,4] and z[4], accumulate
`H += np.outer(A,A)` and `z += A*y` for each context/action in that order;
solve the fixed5×5
bordered system `[[H,ones],[ones.T,0]] [b,lambda] = [z,0]` by NumPy1.26.3
`linalg.solve`. No regularization, optimizer, stopping tolerance or tuned
hyperparameter; `sum b=0` fixes the irrelevant common offset. All four
actions occur in every context's contrast menu, so the contrast graph is
connected and H has only the one constant null direction. A singular or
nonfinite result is an implementation/input failure, not permission to use
a pseudoinverse, alternate calibration or new fit. Save H,z,b and the
unscaled normal-equation residual. Do not also fit the original centered-
mean B or select between them. This correction changes neither four fitted
constants nor the seven-arm/teacher/model counts.

B deploys by `(G_a+b_a, G_a, action_ID)` in float64. It retains G's complete
public information and timed G/features work but has no neural forward.
The network can represent action constants via its supplied action ID;
beating B would support this finite contextual package over a competent
constant correction, without proving that a neural architecture is necessary
among all possible ordinary controllers. B's more stringent comparison may
also remove an apparent learning increment; that is valuable information.
The original coauthor formula remains above as an unexecuted proposal,
and the one scientific review is asked to judge this explicit difference.

**Endpoints, cold deployment and zero added audit missions.** Fit B once,
then S0/S1/S2 sequentially in seed order using the same bank. Save the exact
initial and final scorer state dictionaries plus final optimizer/RNG state,
fit/config/source identity and parameter movement. Freeze every final before
any new world. No best-fit/checkpoint selection. Evaluate new worlds
109255000..109255031, ascending, with `[G,R4,R1,B,S0,S1,S2]` rotated left
by world-index mod7. Every endpoint runs its own complete H1200 trajectory:
224 missions/268,800 actual advances/13,440 decisions.0 extra native audit
missions;0 new teacher collection missions. A fresh episode resets task
state/history; persistent endpoints retain only fixed program/weights and
their own operational state, not another arm's trajectory or live task.

Each arm has one freshly spawned persistent deployment endpoint, cold on
that arm's first request (and on any actual deadline-triggered restart),
not newly cold for each mission. Each student loads its final checkpoint
at its first request inside the20s deadline, with file identity
checked before use. Do not deploy the still-warm training object. G/R4/R1/B
use their genuine first-request paths, without unnecessary eager Torch imports
or neural construction in an ordinary endpoint. Process-cold does not mean
uncached operating-system disk pages. Later ordinary requests can retain
their fixed loaded endpoint; cold restarts following deadline expiry keep
the original operational semantics and cost. Use the same delayed command
activation and last eligible publication rule as the independent contract.

Students score all four actions by `(G/1200+float64(f), unscaled_G, action_ID)`
and otherwise KEEP if no complete result is received by the deadline, exactly
as the original learned endpoint. Do not add an early G fallback publication
for students/B that G's original result program did not have. R1/R4 keep
their explicit G publication. Deadline effects remain part of the compared
complete programs. Learned initialization is *defined* as canonical G;
three duplicate initial native evaluations are not bought. Its exact zero-
head certificate and bank forwards are checked separately offline. Final
checkpoint loading, score composition and actual command selection are
checked over every student deployment record by the complete reader.

**Training evidence, full reading and neural counts.** At initialization
and the fixed final endpoint, evaluate all2,100 bank contexts in ascending
order, batches64/last52, without gradients. Save all four residual and
composed scores, relative-loss values, selected action, teacher-score regret,
ties and margins. Initial scores must have exactly zero residual, canonical
G action and a matching zero-head parameter certificate. Do not use an
approximate initial forward as a different deployment policy. Report
complete-menu regret `Rbar[selected]-min(Rbar)`, relative-cost error and
the selection/tie tables; keep action accuracy as a limited diagnostic.
These are performance on the exposed teacher-state distribution, not new
native consequences or fresh generalization. Newly visited student states
do not receive extra R queries for a same-state teacher-regret diagnostic.

Retain each of6,336 update records: attempted/completed counters, fit/epoch/
batch, ordered context indices, actual batch size, pre-update relative loss,
unclipped/clipped norm, parameter/optimizer state identities and CPU/wall.
Save initial/final parameters and complete final optimizer state with step
counts; intermediate update hashes/curves are compact evidence, not an
optimizer replay certificate. Epoch curves are context-weighted summaries
of the33 online minibatch losses measured at changing parameters. They are
not64 separately recomputed fixed-endpoint evaluations; do not add those
extra forwards or claim their stronger meaning. No intermediate checkpoint
selection or gradient reconstruction is part of this purchase.

The independent reader rederives all teacher labels/anchors/features from
the saved public rows and cached G, B's system/solution, shuffle schedules,
batch counts/loss arithmetic available in logs, endpoint movement, zero-head
and optimizer-step identities. It loads all six initial/final checkpoints
and recomputes their full-bank forwards at the same batch shape/order; it
recomputes every final student deployment forward at the original four-row
decision shape. Same bound CPU stack/dtype/batching and source require exact
saved residual/composed-score/action agreement, with finiteness and the
published tie rule. B's independently rebuilt fixed-order H,z/solve and
deployment scores likewise require agreement. It does not execute6,336
additional optimizer steps, certify every historical gradient or infer an
update from a changed parameter hash alone. A consequential discrepancy is
a technical reading failure, not a tolerance tuned after seeing actions.

All new actual/model physics, G, queue and deadline work remains fully
read as in the three-arm contract, now across224 missions. No old teacher
physics is rerun; its bound completed reader is explicitly reused. Required
forward counts (attempts and completed values separately, including any
canceled prefix) are fixed as follows:

| Neural work | Worker action rows | Reader action rows |
| --- | ---: | ---: |
| Three fits,64 full epochs | 1,612,800 | 0 optimizer replay |
| Three initial + three final, full old bank | 50,400 | 50,400 |
| Three final students,32 new missions each | 23,040 | 23,040 |
| Total | 1,686,240 | 73,440 |

Whole-purchase neural forward ceiling is1,759,680 action rows, plus the
training backward/update work already counted. Each fit has2,112 backward/
optimizer steps; no second stochastic teacher-data acquisition is hidden in
that count. Count scorer construction/loading attempts and their cost,
including deployments/restarts, without calling them new optimization fits.
The one B solution consumes the same8,400 action labels and saves four
constants, with0 neural evaluations. No extra neural health/trust panel.
The reader repeats B's numerical solution once as paid verification: two
system solves in the full chain, one fitted asset, not two independent fits.

**Revised dominant work and artifacts.** New G queries total271,488 (13,440
actual reports plus258,048 R-internal), candidate values1,085,952,
candidate-ticks246,912,000 and cluster recurrences987,648,000. Those G
counts apply separately to worker and full reader. R work remains3,840
model initial constructions, at most5,201,920 native prefix advances,
8,352 physical cohorts/33,408 clones and9,600 logical cohorts. Actual
reader physical states increase to269,024; with model initials/prefixes the
complete ceiling is5,474,784. R future draws remain222,720 uniforms;224
actual arrival tapes use43,008. Logical task bytes total2,507,680. The
extension therefore adds153,600 actual advances and6,696,960 G candidate-
ticks to the three-arm candidate, not more R model prediction. Preserve
every counter, interrupted prefix, cold load and failed attempt; a lower
realized count caused by failure is not a completed cheaper program.

New files would be solely in this direction's future
`experiments/candidates/uav_decision_generalization/b06_request_amortization/`,
matching tests, run outputs and scratch, with this notebook/owned standing.
The future entry would buy one worker (data binding/B/three fits/all224
missions) and its complete reader; B05 modules/evidence stay frozen inputs.
This names implementation ownership, not a new implementation authorization.
Exact schema, published input manifest and executable safeguards would be
reviewed under the existing engineering method only if Root selects it.
Do not create a separate direction/registry or make A/C/D consumers of it.

**Costs: asset acquisition, use and research are separate.** A fresh read of
the35 original R mission metadata (no scientific execution) measures
7,026.128558 CPU-s =1.951702 CPUh and7,657.956077 summed mission-wall-s
=2.127210h for those missions. They include42,000 actual native advances,
4,407,360 model prefix advances and2,100 four-cohort decisions, plus the
recorded constructor/decision/native/trace-compression costs. The original
three audit R missions cost232.847532/228.101075/267.837171 CPU-s; main-only
196.79s is not a universal per-world constant. This per-mission bill excludes
final metadata writes and some endpoint/setup/close/hash support. Their
attribution to teacher acquisition is unknown, not zero. The full old reader
also verified other arms/training; its5,653.181264 CPU-s cannot all be assigned
to these35 teacher trajectories. No defensible separate old teacher-reader
CPU measurement was recorded.

The entire B05 research account remains approximately5.374 CPUh plus
incompletely metered support, including unsuccessful TD learning, all
evaluation, complete reading and the retained first-reader error. It is
historical study cost, **not** the intrinsic price of obtaining a35-trajectory
teacher bank. Reuse here has0 marginal task/model *collection* calls, not
free data, free validation or zero end-to-end acquisition cost. Report the
measured old teacher mission charge, its attribution limits, old whole-study
bill, new B/fit acquisition, new deployment, new verification and support
as separate scopes without adding overlapping components twice.

Forecast the proposed **whole new purchase at4–7 CPUh,0 GPUh and5–9 summed
operation-wall hours, plus8–14 support-hours**. The old R main/audit range
supports roughly2.2–3.3 CPUh for the G/R4/R1 base worker; the additional32
B and96 student missions should be of order.1 CPUh, using old learned
mission means2.85–2.89s only as a price analogy, not a new benchmark.
Bank binding, one four-constant fit, three fixed neural fits/checkpoints
and endpoint-bank readings are forecast.05–.30 CPUh. New full-reader RF/G
counts are about84.7%/84.5% of the old reader, giving a proportional center
near1.33 CPUh;1.2–1.8h is a planning range, with cold/import/hash/publication
and uncertain tails retained in the4–7h whole-purchase range. Reader and
training costs are not omitted to quote a cheap online policy. The additional
engineering/numerical/RNG/data-binding work is the main uncertain increment
over the three-arm4–8-support-hour proposal; none has been purchased by the
mere existence of this estimate. Current source/arithmetic/advice support is
unmetered and nonzero, with0 scientific effects.

For every fixed student, show complete-task per-use CPU and service against
**each of G, B, R1 and R4**. Define a CPU crossing only when observed
`c_comparator - c_student > 0`; no crossing otherwise. Keep the numerator's
scope explicit: marginal reuse acquisition (bank handling plus that one
fit/checkpoint construction), a separately shown historical teacher-
acquisition scenario using at least the measured1.951702h plus its unknown
extras, and the whole-study research bill counted once. For S−B incremental
acquisition, show B's own fitting cost and shared bank cost so common costs
are not charged twice. If using acquisition differences, state
`max(0,A_student-A_comparator)/(c_comparator-c_student)` and preserve any
unknown additive cost. Do not multiply a shared bank by three or quote the
three-replicate research purchase as a mandatory deployment cost for one
trained asset. Every crossing sits beside C/T/W/unfinished/travel/coverage;
no CPU crossing establishes value equivalence or assumes a deployment volume.

**Proposed hard bounds, synthetic engineering and failure finalization.**
The proposed new overall ceiling is10 CPUh/24 summed-operation-wall hours,
not inherited B05 credit. Count all new charged computation, failed attempts,
fit/evaluation/reader calls, support checks, setup and collection where
measured. Reserve.5 CPUh and1 wall hour *inside* those ceilings for stopping,
reaping, flushing/hash/partial collection and failure publication; stop new
scientific effects at9.5 cumulative CPUh or23 operation-wall hours. Those
reserves cannot buy another fit or make an incomplete study complete. Pure
engineering checks are forecast at most.5 CPUh within the same bill and
must be synthetic/mocked/static: fabricated small feature/score arrays,
shuffle-address/roundtrip/schema/ceiling/deadline protocol tests, fake scorers,
and saved-data arithmetic. They instantiate no real scorer/optimizer/host,
evaluate no G/R/native physics, generate no new task outcome, and cannot
become an unpriced health pilot. If a necessary effectful check is identified,
its actual calls/cost would change the proposed scope before purchase.

Stop at the first new formal admission/worker/reader failure, including a
required result-stage numerical check, preserve all paid prefix/failed
records, and do not restart,
replace a fit/world, add epochs or silently repair into another attempt.
Normal declared deadline KEEP/G fallback remains a valid program outcome
and is still fully read. Interrupted update/scorer counters remain attempts;
only completed updates/forwards count as completed work. Source/synthetic
implementation defects may be corrected and checked within the declared
pre-execution engineering scope; that does not authorize any effect retry.
Ordinary native fit/reader collection after an eventual accepted purchase
requires no per-fit or source-acceptance Root ACK.

Declare an **8 GiB cap on newly allocated disk for this operation chain**,
with a7 GiB normal-work ceiling and1 GiB failure-finalization reserve inside
that cap. Measure allocated bytes over the disjoint new B06 worker/reader
outputs, their exact launcher-managed source snapshots, B06 scratch and
owned test scratch; count each physical inode once if linked. This includes
source snapshots and required unique bulk, not just logs/free space. Plan
up to4 GiB for two2-GiB source snapshots,1 GiB new unique evidence (.3–.7
GiB forecast),1 GiB active scratch and.5 GiB test/metadata/measurement margin;
these are components of the aggregate ceiling, not independent allowances.
Prefer retiring a collected, unconsumed worker snapshot before creating a
reader snapshot, but do not delete a live consumer or necessary evidence to
fit a forecast. At the normal limit stop new science and retain/finalize;
the reserve cannot be used for new worlds/queries. A cap failure is an
incomplete technical purchase, not a request to pack, back up or move bulk.
The existing canonical B05 evidence is inherited retained usage, reported
separately and consumed in place; it is not newly copied or silently charged
as new allocation. Shared Git objects/other directions' outputs are outside
these owned targets and remain untouched. Source preparation creates no
new snapshot now.

An actual launch would still require fresh configured local-node admission,
the unchanged8-GiB effective memory/12-GiB free-disk floors and preserved
neighbor operations. Free-disk floor is not the operation's disk cap. Actual
RSS is recorded with process scope; runtime/user/system/child CPU and sums of
operation walls are not confused with support elapsed time or simultaneous
host occupancy. A full filesystem or failed observation never licenses a
duplicate worker. Nothing in this source-only task surveys resources or
claims that future admission has already passed.

**Joint reading and investment choices.** Retain the original prospectively
named C, completed-only T, all-user W, unfinished/censored, travel, coverage,
deadline and cost definitions. Read all seven endpoints'32-world vectors;
compare every S against G/B/R1/R4, alongside R4−G/R1−G/R1−R4 and B−G.
Each world's seven records share exogenous geometry/actual arrivals, while
R1/R4 alone share tape0 as already specified. Paired world intervals are
conditional on these fixed student instances and this one teacher bank.
Also show all three fit-mean contrasts and a descriptive df2 interval/range
for optimization variation conditional on that same bank/panel; optionally
the shared-world mean over all three students retains their covariance.
There are three optimization replicates,0 new independent data acquisitions,
and no96-independent-fit interpretation. Tail missingness is explicit;
all new exploratory multiple metrics remain descriptive, without equivalence
claims or a margin fitted to B05. No best student is selected for the headline.

For B and each student retain the stages from score computation through
eligible message, requested/selected command, target alias, delayed activation
and distinct physical action. Compare with cached same-report G and its motion
at the observed activation positions without buying a counterfactual suffix.
If a gain arises while learned scores never control an effective action,
preserve that complete-program gain but do not call it use of acquired
preferences. Deadline fallback, action alias and terminal-unused commands
are distinguishable outcomes, not missing-data substitutions.

First compare each student's initial versus final exposed-bank relative
error/regret and parameter movement, then its actual full-task behavior
versus the ordinary programs. Lower bank loss with worse new service is
an acquired surrogate approximation with adverse complete use, not evidence
that labels were absent or that more epochs must fix it. A useful new native
gain against G/B with a competitive cost/service frontier versus R1/R4 is
a conditional learning capability even without identifying a repaired
component. If B captures the use, retain B without inventing neural necessity.
If R1 captures it, retain R1 regardless of student outcomes. If R4 alone
retains useful tails, preserve it with its actual costs/deadline feasibility.
If R4's tails do not recur, narrow their generalization. If no useful complete
native capability is found, close this fixed-data supervised package, not
all learning. Poor exposed-bank fitting alone cannot reject a student that
produces a useful complete native gain: the approximate teacher labels are
not the scientific objective. Such a result limits a successful-teacher-
amortization explanation while preserving the actual learned package and
its costs/adverses. No branch adds DAgger, teacher queries, epochs, sample rates
or a new architecture automatically. Missing implementation/reader evidence
remains technical incompleteness, not a learning negative.

My present choice is the complete seven-endpoint extension if its8–14
support-hour price is worth purchasing. It adds a direct acquisition question
to almost the same expensive R/full-reader backbone and uses a real existing
capability rather than requiring R1 to win first. The original complete
three-arm study remains the useful lower-support alternative; it addresses
online sampling but leaves this finite amortization opportunity unobserved.
Stopping is also feasible and preserves G/R; I favor the finite extension
because verified aligned teacher inputs make its marginal scientific question
concrete, not because the old budget or a DM slot must be used. Root's A/C/D
studies are real competing investments, not controls or evidence for this
task. Their outcomes are not pooled here. The source contract and original
coauthor dissent now go together to the existing independent critic for
one selection-difference review; Root chooses the actual next purchase.


<a id="b06-independent-selection-review"></a>

#### 2026-10-03 — Complete original independent selection-difference review

The same registered ResearchCritic returned this one consequential review
of the actual seven-endpoint contract, using its separate B05 context. It
read original evidence before the coauthor/DM explanation, independently
reconstructed all2,100 teacher menus and1,391 aliases, and executed no
new scientific calls or coefficient fit. This is the only selection review
of the successor; the earlier three-arm draft did not receive a separate
pass. Its cold-endpoint clarification and bank-fit rejection correction
were accepted during this review and appear in the final source contract.
No additional Pro round has a distinct unresolved question here.

Complete original answer:9,788 characters /9,830 UTF-8 bytes, SHA256
`7d70503fbcf6ff41aadc289e9c4080fbf540c80710a29b15651106c0dae1e4c6`.

```text
**Recommend the corrected seven-endpoint exploration over the three-arm alternative.** It adds a concrete learning question to almost the same expensive rollout-and-reader comparison. The additional **8–14 support-hour commitment** is material; the proposal is worthwhile at that declared price, rather than because the teacher data are already paid for.

This review reuses my independent B05 analysis. I reconstructed the teacher evidence before reading the coauthor’s explanation and final contract. No new policy, model, neural, optimizer, coefficient-fitting or native calls were made.

The evidence supports the proposed starting point. I checked all 35 original R trajectories and all 2,100 associated rollout files against their manifest, reconstructed the four-cohort means, and verified the 1,391 reuse aliases and their multiplicities. The means reproduce every saved R choice. The warning about `total_q` is consequential: it contains G/1200, not the teacher scores.

There is usable decision information, with substantial limitations:

- R differs from same-state G in 360/2,100 contexts. G already matches approximately 83% of teacher choices.
- There are 388 fully tied menus and 593 ties between the two lowest teacher scores. Accuracy alone can therefore flatter an ineffective student.
- G’s mean regret against these saved teacher menus is 19.22 predicted cost ticks. That is a model-score difference, not demonstrated native improvement per decision.
- The bank comprises **35 correlated trajectories**, rather than 2,100 independent environments or three independent teacher acquisitions.

These observations justify a bounded attempt to learn the additional preferences. They do not predict that fitting them will preserve useful behavior after a student’s trajectory departs from the teacher’s.

**The corrected constant comparator is appropriate.** For the declared anchored loss, each design row is \(A=e_a-e_g\), so the normal equations use \(H=\sum AA^\top\) and \(z=\sum Ay\). The bordered solve with \(\sum b=0\) removes the irrelevant common offset. Every context supplies all four actions, making the contrast space connected and the solution identifiable.

The coauthor’s centered-mean formula generally minimizes a different criterion. That difference matters here because G anchors are highly uneven: `[1694,159,146,101]`. Giving B the optimum for the same anchored objective prevents a weak calibration fit from manufacturing an apparent need for contextual learning. One deterministic fit is sufficient for this fixed bank; three identical solves would not provide replication.

B is a competent **global action-correction comparator**. Together with G, R1 and R4, it gives the proposed acquisition claim meaningful ordinary alternatives. Beating B would not establish that neural networks are necessary among all possible state-dependent controllers; the contract appropriately avoids that claim.

The supervised construction is scientifically distinct from repeating DDQN. It uses fixed, complete-menu targets, includes the learned anchor in the gradient, and removes bootstrapping and changing target networks. It tests whether this particular supervision can acquire useful control. It does not identify or repair the cause of B05’s adverse learning.

The new criterion identifies relative values only. Absolute negative outputs or a common offset consequently cannot be imported from the B05 diagnosis as a rejection rule. Conversely, low relative error remains insufficient: targets are finite sampled rollout predictions with an approximate G tail, and the student still runs G online. This is amortization of the additional R computation, not elimination of planning.

**The strongest consequential risk is the gap between fitting teacher menus and controlling new trajectories.** MSE may improve chiefly on large, nonwinning action differences while small decision margins remain inaccurate. Approximate labels, only 35 training worlds, and subsequent state-distribution changes can each undermine complete use. The proposed fresh closed-loop evaluation measures their combined consequence directly. A positive pilot, extra teacher collection, or successful R1 result is unnecessary beforehand.

I requested one substantive reading correction, which the DM accepted: **poor exposed-bank fit must not reject a student that produces useful complete native results.** Such an outcome would limit the explanation that it successfully approximated the teacher, while preserving the acquired package capability. The revised stopping branch now concerns absence of useful complete native capability. This correction adds no effects or cost.

The decision and numerical schedules are sufficiently specified for selection:

- R1 uses exactly tape0; R4 retains ordered cohorts, exact reuse and duplicate weights. Neither receives actual future arrivals.
- Every program retains the same 20-tick activation delay and 20-second deadline. Faster computation supplies no earlier physical intervention.
- There is one persistent deployment endpoint per arm, genuinely cold on its first request and on actual deadline restarts—not a cold-per-mission change.
- All three students have fixed initialization/shuffle streams, 64 epochs, 33 batches per epoch, and fixed final endpoints.
- Initial/final bank checks and deployment checks preserve their respective batch shapes. The proposed reader does not claim to replay historical gradients or optimizer updates.

The reading must still distinguish completed score evaluation, selected command, useful activation and fallback. The stored scores, cached G values, timing and native commands support that distinction without additional queries. A benefit produced through nonactivation or fallback would remain a program outcome, but would not establish use of the learned preferences.

I independently checked the principal arithmetic:

| Item | Three-arm proposal | Seven-endpoint proposal |
|---|---:|---:|
| New complete missions | 96 | 224 |
| Native advances | 115,200 | 268,800 |
| Rollout-model prefix ceiling | 5,201,920 | 5,201,920 |
| Neural optimization fits | 0 | 3 |
| Deterministic constant fits | 0 | 1 |
| Forecast CPU-hours | 3.5–5.5 | 4–7 |
| Forecast support-hours | 4–8 | 8–14 |

The extension’s 6,336 updates, 403,200 context presentations, **1,759,680 total neural forward rows**, 271,488 G queries, 246,912,000 G candidate-ticks and 5,474,784 reader physical-state ceiling agree with the declared schedules. Retaining complete old-teacher identity/label checks while reusing its completed physical verification avoids an unnecessary historical rollout reconstruction.

The cost separation is also sound. The 35 teacher missions consumed **7,026.128558 CPU-seconds** and **7,657.956077 summed mission-wall seconds**. Outer setup/support and teacher-only reader attribution remain unknown. The historical approximately 5.374 CPU-hour B05 research bill is a different scope. Neither should disappear behind “zero marginal collection,” nor should overlapping components be added twice.

The 10 CPU-hour/24 operation-wall-hour ceiling, internal finalization reserves and aggregate 8 GiB allocation cap make the proposed purchase bounded. They are not evidence that an unimplemented study will finish within them. New training/runtime costs, exact numerical reproduction and actual node admission remain unverified. The forecasts are adequately grounded for selection without a hidden health pilot.

The complete observation can change real choices:

- **Students gain useful native capability beyond G/B and offer a competitive service–compute tradeoff against R1/R4:** retain conditional learned assets, including all completion, flight and coverage costs. This supports finite acquisition on one bank, not a general TD repair or independent data-acquisition replication.
- **B supplies the useful behavior:** retain the simpler correction; neural complexity has not earned an incremental claim. A nonsignificant S−B difference alone does not establish equivalence.
- **R1 supplies the useful behavior:** retain its ordinary computation improvement regardless of student outcomes.
- **Bank approximation improves but native use worsens:** record successful surrogate fitting with adverse control. That does not identify distribution shift as the unique cause or authorize more epochs.
- **R4’s tails fail to recur:** narrow their generalization while preserving B05’s original positive and adverse evidence. A separately useful student result would still stand.
- **No student has useful complete capability:** close this fixed-bank recipe without automatic additional labels, DAgger, seeds or architecture changes.

The seven-endpoint design is therefore the smallest proposed complete comparison that answers both the online-sampling and finite-acquisition questions while retaining the important ordinary alternatives. The three-arm version remains the reasonable lower-support choice if Root declines that additional work. I do not prefer stopping on the scientific evidence now available. I have not independently ranked this purchase against A/C/D’s separate research cases.

Metered saved-data, hashing and static arithmetic for this review totaled approximately **8.94 CPU-seconds**; other support remains unmetered. The recommendation applies to the [corrected source contract](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:8160), with implementation and execution still unperformed.

**MATERIAL_DISSENT: no — the verified teacher bank, corrected competent comparator and complete fresh evaluation support the seven-endpoint investment at its stated price. The consequential bank-fit rejection rule was corrected and accepted within this review.**
```

<a id="b06-selection-disposition"></a>

#### 2026-10-03 — DM disposition and source-only return to Root

I have read the full original coauthor answer and this full independent
review. I adopt the recommendation for the corrected seven-endpoint
exploration over the narrower three-arm proposal, at its stated full price.
The reviewer reports MATERIAL_DISSENT:no after the accepted correction;
I preserve its qualification that it has not independently ranked A/C/D.
This is a recommendation for Root's cross-question allocation, not an
effect purchase, implementation acceptance or positive learning result.

The verified bank changes what is feasible:35 already acquired R trajectories
contain all2,100 complete four-action menus with their alias weights and
lawful303-feature interface. The main remaining learning uncertainty is
useful finite fitting and closed-loop behavior on new states, rather than
missing teacher acquisition. It does not identify why DDQN failed. The
reviewer's19.22-tick G regret is against saved model menus, not demonstrated
native per-decision headroom;83% action agreement and many ties prevent an
accuracy-only success story. All old worlds are training/development for
this successor. Three new seeds repeat optimization on one bank, not data
acquisition or independent task populations.

I retain the deterministic G-anchored least-squares B correction. It fits
the same relative objective within four global constants, with a fixed
common-offset gauge; its numerical solve will be executed only if selected.
This is a stronger ordinary comparison than the coauthor's generally
different centered-mean criterion, at the same one-fit/four-constant count.
The full reference is G/B/R1/R4: success against B alone cannot establish
neural necessity or a useful complete value/cost frontier.

The review made one substantive correction to my original outcome wording:
poor bank fit alone cannot reject a useful native student. I removed that
surrogate gate. In either direction, keep package value distinct from its
explanation: useful native results survive uncertain teacher approximation;
better approximation does not redeem adverse native control. A gain from
KEEP/fallback or an inactive learned choice also remains a complete-program
outcome but does not establish deployment of acquired preferences. The final
contract now explicitly reads score/publication/command/alias/activation/
physical-action stages from already purchased evidence, without a new
query or counterfactual suffix. Cold means one persistent arm endpoint on
its first request, plus actual deadline restarts, never cold per mission.

The proposed complete observation is fixed: G/R4/R1/B/S0/S1/S2,32 fresh
worlds109255000..109255031,224 H1200 missions/268,800 native advances,
three64-epoch neural fits/6,336 updates plus one deterministic constant
fit, no new teacher collection and no additional audit mission. R's model
ceiling stays5,201,920 prefix advances; full new reading, all old label/
identity checks and1,759,680 total neural action-row forwards are included.
B is solved once to fit and once in the reader as verification, not a second
independent fit. All endpoints are fixed before fresh evaluation, with the
original G/R4/R1 information, tape coupling, exact reuse and deadline/
20-tick activation contract. Initial deployment is canonical G, separately
certified by zero heads and offline forwards; no old TD checkpoint is reused.

I retain forecast4–7 new CPUh/0GPU,5–9 operation-wall hours and8–14 support
hours. Proposed bounds are10CPUh/24 aggregate-operation-wall hours, with
.5CPUh/1wall reserved inside them for failure finalization, and8GiB new
allocated disk (7GiB normal+1GiB finalization reserve) over exact source
snapshots, new unique outputs and owned scratch/tests. These are proposed
stop bounds, not proof of feasibility or an available allowance. Existing
B05 teacher records are retained in place, not copied into a new backup.
The first new formal/result-stage failure or bound stops further effects;
no automatic retry, repair fit or expanded panel is included. Pure source/
synthetic engineering is separately bounded and adds no scientific calls.

The measured old teacher mission acquisition is1.951702 CPUh plus its
unallocated outer/verification/support scope; the complete B05 study cost
about5.374 CPUh is different. Marginal new collection is0 but asset binding,
training and validation are not free. Report those scopes separately, then
measure any CPU crossing against each of G/B/R1/R4 only for positive per-use
savings and beside actual service differences. Neither a CPU crossing nor
a confidence interval spanning zero establishes value equivalence.

A narrower complete G/R4/R1 comparison remains worthwhile if its lower
4–8-support-hour price is preferred. I favor the extension because the
expensive new R/reader backbone is almost unchanged and verified menu data
make an actual finite-acquisition comparison concrete. Stopping is feasible
and leaves the demonstrated ordinary capabilities intact; I do not prefer
it on this evidence and price alone. This is not a requirement to fill a
DM slot, spend the old budget, explain every mechanism or force a learner
to be useful. Any later extra labels, epochs, architecture or confirmation
would be another material choice, not one of this purchase's automatic
outcome branches.

Before publication I refreshed current main at
`b01283037740bd136dd34b8c70f392787f209527` and read the affected standing/
Root selection text and changed relevant background. The new N8 timing
positive has a different task/interface; it does not transfer a value gain
to these public request queues, and A/C/D remain independent investments.
Our prior topic5 R capability and DDQN adversity remain unchanged. There
is no new reusable empirical judgment requiring another background edit;
this boundary updates only the owned standing and notebook.

The source-only assignment is complete. No production source/test was
changed, no new scientific effect or formal request occurred, and there
is no accepted operation, observer, unread review or launched successor.
The review metered approximately8.94CPU-s of saved-data/hash/arithmetic
work; remaining design, publication and source-reading support is unmetered
and nonzero. No new source snapshot or bulk was created, so there is no
new disposable run tree to retire. The direction's lead and useful old
evidence are unchanged. Publish this contract/original advice/disposition
and the owned standing, then return natively for Root's one complete
purchase choice; do not start implementation or effects on publication.

<a id="b06-selected-purchase-and-l0"></a>

#### 2026-10-03 — Root selects the complete B06 purchase; implementation L0

Root has now read the published final contract (`f8c2ab328`), the complete
9,830-byte independent review and the DM disposition and explicitly selected
one complete B06 purchase. This supersedes the preceding source-only limit,
not the fixed scientific contract. The same DM owns implementation, focused
independent engineering acceptance, published exact inputs, actual admission,
the worker and full reader, scientific reading, own publication and cleanup.
There is no per-fit or implementation Root acknowledgment. The applicable
scientific review is complete, MATERIAL_DISSENT:no; neither the question nor
its comparisons changed in this selection. The current topic5 evidence and
the different-task scope limit of the new timing result remain applicable.

The selected scope is exactly G/R4/R1/B/S0/S1/S2 on worlds109255000..031:
224 H1200 missions/268,800 actual advances, one deterministic G-anchored
four-constant fit and three64-epoch supervised fits on the bound old35 R
trajectories/2,100 menus. No new teacher collection, additional audit/pilot,
old TD weights or optimizer replay. Counts, ordered cohort/alias labels,
303-feature/55,553-parameter interface, mixed-precision relative loss,
canonical initial-G certificate, cold persistent endpoints and complete
reader stay as specified above. Every useful or adverse native outcome is
read independently of teacher-fit quality and mechanism attribution.

Root selects10 cumulative new CPUh and24 aggregate operation-wall hours,
with.5 CPUh/1wall hour inside those totals reserved for stopping/finalization;
stop additional science at9.5 CPUh/23wall hours. The new owned allocation
cap is8GiB (7normal+1finalization), covering exact source snapshots, new
unique outputs and owned scratch/test targets with physical-inode dedup.
Old B05 evidence is consumed in place and remains outside new allocation.
Pure source/mock/static engineering is limited to.5 CPUh within this same
bill. It makes no actual scorer/optimizer/host/G/R/native calls or health
pilot. The approximately8.94 CPU-s of prior independent selection arithmetic
belongs in the new ledger; other unmetered source/advice/support is nonzero.
The first new formal request rejection, admission, worker or reader failure
ends this purchase with paid prefixes retained. No duplicate, automatic
retry, extra seed/world/epoch or repair attempt is selected. Normal declared
deadline fallback is a valid outcome. Uncertain acceptance is reconciled
against the same handle. Use the configured local_linux CPU stack first,
with fresh actual admission only at launch, preserving A/C/D operations.

**Bounded implementation task 1 — fixed-bank acquisition.** Author only
`experiments/candidates/uav_decision_generalization/b06_request_amortization/`
`acquisition.py` and its matching `test_acquisition.py`. The behavior is to
bind/reconstruct the old complete-menu bank, fit the single optimal constant
correction and the three exact supervised endpoints, and emit complete
initial/final/update evidence and counters without task/model collection.
The task owns no runner, rollout, deployment, shared source or notebook.
Reuse the frozen B05 scorer architecture and public feature interface by
import without modifying B05. Imports of the acquisition module must not
eagerly import Torch or construct a model; ordinary deployment must remain
free of unnecessary neural cold-start cost. Expose data binding, fixed-order
constant solving, canonical shuffle schedule, fixed fit/endpoint-evaluation
and checkpoint-load functions for the later worker/reader; document their
signatures in code. Parameter, optimizer, update/batch identities and partial
attempts must survive a failure. Inputs contain only bound public features,
raw float64 G, ordered float64 teacher means and their provenance; outcome
and future-arrival fields cannot become labels/features.

The Implementer reads the final contract and directly required frozen
schemas, implements this one behavior and returns its diff plus metered
mock/static checks. Synthetic tests cover actual last-batch52 schedule,
label aliases/float64 composition/tie ordering and the anchored LS/loss
specification with fabricated arrays and fake numerical backends as needed;
they instantiate no real scorer or optimizer and do not fit the real bank.
Reading/hashing old records or static arithmetic may be metered, but no
new scientific output is evaluated before published execution. The DM will
accept the diff, then assign a subsequent bounded behavior; there is only
one Implementer task active at a time. Other concurrent writers and their
edits remain intact. Helpers have no Git index/commit, notebook, launch or
child-spawn permission. The DM retains ownership of integration, full input
and cost bindings, the runner and subsequent implementation scopes.

The existing independent engineering Reviewer will inspect the complete
new executable difference: learned-anchor gradient and dtype ordering,
fixed-order LS, RNG, checkpoint identity, cold load/IPC/deadline, complete
counter/disk/stop accounting and reader scope. Static/mock coverage does
not certify actual numerics or throughput; those remain paid execution
risks, with no unpriced warm-up or preliminary effect call.

**Acquisition acceptance and next bounded behavior.** The DM has reviewed
the bank/alias binding, exact float64 anchored LS and loss, forked scorer,
fixed64/52 batch schedule, lazy loading and failure journals in the returned
acquisition diff. The accepted paths are only the two L0 paths above;
ready hashes are `9f0667c7d8f10cc860db0877411448845c5a5e4c6622ff530bf7c1252645304b`
(source) and `5eb349a8027914a484673fd7dbf53523d7c28154f3f6cea63a28f20f7aaa01ec`
(tests). Five applicable mock pytest invocations all passed (9/10/1/1/1
checks), including one fabricated35×60 bank and intentionally injected
failure paths; no check invocation failed. Source/schema/scratch checks
also passed. Total measured Implementer CPU11.41s/wall9.25s; peak RSS100,048
KiB and all five owned test directories removed. Actual scorer, optimizer,
backward, coefficient solve, G/R/native, host and scientific world calls
were0. Acceptance is for source behavior and mock coverage, not actual
Torch numerics or the still-unexecuted complete runtime.

The DM's first five contract/budget tests also passed, checking the counted
complete schedule, physical-inode union without following symlinks, the
science/finalization reserve and reader attempt bounds:1.346481 CPU-s and
.698786086wall-s, plus unmetered source-reading/editing support. The next
independent engineering review still covers acquisition and integration.

**Bounded implementation task 2 — complete new saved-evidence reading.**
The same Implementer now owns only new B06 `reader.py` and its matching
`test_reader.py`; the acquisition task is finished and has no concurrent
writer. The behavior is to read the original complete new worker without
additional task trajectories or optimizer replay: bind every new scientific
artifact, independently reconstruct all new actual/model physical and G
records, verify old teacher identities/label arithmetic and lawful features,
repeat the fixed B solve once, replay six scheduled bank endpoints and every
committed student deployment forward, and produce every selected service/
tail/censoring/intervention/cost contrast. It must not rerun old physics.
Reuse frozen B05 independent physical/FIFO/feature/G kernels, adjusting only
the new explicit limits, roster, R1 cap and frozen-policy/acquisition schema;
do not monkeypatch the frozen module or turn incomplete work into complete.
The source reader is distinct from worker execution, while checkpoint/data
loading utilities may be shared with explicit independent arithmetic checks.

The DM owns the new contract, cost/bindings/entry, deployment and worker.
New `storage.py` specifies the exact pruned mission arrays plus independent
`nn_complete` and B/S `score_complete` markers. B uses raw float64 G+b;
S uses G/1200+float64(f32 residual). Metadata preserves the old full timing,
selected cohort list, source/counters and request identities, with training/
initial-audit flags false. R traces have separate arm paths. A cold endpoint
per arm persists across worlds; its final count record is named by arm.
Each fit has its own `fits/fit<i>/` acquisition output and fixed initial,
final, training checkpoint plus initial/final-bank arrays, update journal,
epochs and fit.json. Worker manifests bind all scientific artifacts.

Reader checks are mock/static only before execution, with the same cost/
scratch ownership and0 real scorer/optimizer/solve/G/R/native calls. It reads
all specified outcomes, including no-completion T missingness and observed
unfinished-age lower bounds. Compare each S to G/B/R1/R4 with32 paired-world
vectors conditional on this bank/frozen instance, three fit means conditional
on this same bank/panel, and the named ordinary contrasts. No equivalence,
independent-acquisition claim or best-student selection. All costs and pure
check failures are returned. The DM accepts this second diff and retains
the final independent engineering acceptance and result responsibility.

The DM has completed the worker/deployment integration and begun the existing
independent engineering review. New B06 code imports the frozen B05 physical,
FIFO, feature, G, storage and deadline kernels; none of those files is edited.
R4 calls its original search unchanged. R1 returns normally immediately after
the first original complete-cohort publication, before tape1; the independent
reader explicitly bounds its saved prefixes to that cap. All seven endpoint
processes are persistent across worlds, with actual first-use checkpoint
loading inside the real deadline. No acquisition scorer is handed to deployment.
The worker retains cached-score completion independently of command eligibility,
and the reader distinguishes a completed-but-uncommitted interrupted forward
from a committed residual it can reconstruct.

The first DM integration invocation passed13 checks, including late B score
versus KEEP, exactly20 ticks before physical command activation, preserved
failure prefixes, R1 cap versus unchanged R4, persistent endpoint lifecycle,
entry seed rejection, allocation bounds and phase/aggregate counter accounting.
Cost1.292900 CPU-s/2.922683240 wall-s, child peak85,484KiB. A later focused
mock orchestration check passed1/1 (7 deselected), verifying one bank/one B/three
fits before the complete rotated seven-arm roster and one endpoint per arm:
1.024065 CPU-s/.915942508 wall-s, child peak84,416KiB. Both invocation fixtures
were removed by pytest;14 dependency deprecation warnings are retained in the
receipts. There were no failed test invocations or actual scorer, optimizer,
LS solve, G, R, host or native calls. The synthetic failure injection is test
coverage, not a failed scientific attempt. Later reader checks and engineering
findings will be added to the same cumulative bill.

Current published main was refreshed at e926c44188833f6cd127ad062e721ec48b8bad66.
The Root selection and routing explicitly assign this complete B06 purchase to
the same DM; owner pause remains lifted. The owned direction row still carries
the earlier source-only reserve text, which will be reconciled at the upcoming
source/plan publication before any actual admission. This ordinary standing
update does not require another Root choice. No new formal request has occurred.

**Complete reader acceptance and integration.** The DM has accepted the second
Implementer task: reader.py SHA256
`57111858053e66c0001253eab5f188077141243c9b4d8adc9e574a206aa684b2`
(77,601 bytes), test_reader.py
`8b3561bc6334457d62094dae906462822f58811ca36bb5987a41132db210e6b0`
(35,265 bytes). The complete reader binds every new artifact, reconstructs
all new actual/model/G records, and checks old public features and four ordered
teacher samples without replaying old physics. It performs six prescribed
initial/final bank evaluations and all committed deployment forwards, with no
optimizer replay. It retains completed-but-uncommitted and attempted-incomplete
neural exposure instead of forcing counter equality. C, completed-only T
missingness, unfinished age lower bounds, individual gaps, motion/coverage,
command eligibility/activation and all S-versus-G/B/R1/R4 contrasts remain in
the full reading. Three optimization replicates condition on one shared bank
and panel, with32 paired-world vectors and df2 fit-mean summaries.

Independent engineering review found one material draft defect: the reader
reused the producer's teacher mean and LS assembly, which could self-certify
a shared arithmetic bug. The Implementer replaced that reliance with ordered
branch-outcome/alias reconstruction and independent scalar H/z/bordered-system
assembly. This replaces the original verification path and still makes exactly
one reader solve. The reviewer has inspected this correction; no additional
scientific effect or comparator change was introduced.

Reader mock receipts retain all five invocations:11 passed/6 failed expectations;
21 passed;23 passed;23 passed/1 failed expectation; corrected focused1 passed
(23 deselected). The first failures expected ValueError where the inherited
require correctly raises AssertionError. The later negative timeline fixture
expected a later diagnostic, while the reader correctly rejected the earlier
20-tick-delay inconsistency. Coverage union24 checks;14.21CPU-s/9.02wall-s
including both failed invocations and static checks, peak142,940KiB. All five
pytest scratch directories are gone. These are engineering fixture failures,
not failed scientific launches or evidence of numerical behavior.

After reading the returned code, the DM ran the complete new integration suite
against all14 bound source/test files:48 passed with14 dependency warnings,
4.874430CPU-s/4.831977299wall-s and180,156KiB child peak; AST/hash checks passed
and invocation scratch was removed. Actual numerical runtime, physical reading
and throughput are still untested until the admitted selected purchase. There
were no real scorer/optimizer/backward/LS/G/R/native calls in these checks.

The exact selected study input now binds71 source files and unchanged inherited
B05 dependencies, source identity
`80c9e70ed76cb8ad076b0a78d9c27768f971f1f83c475f99922ccf857f80869a`.
`B06_STUDY_INPUT.json` is13,680 bytes, SHA256
`750796b69686200a152d3ab0cfe3464eb2c53597783ba8601a37868000902a91`.
The prospective new-cost ledger records47.058492 known CPU-s and31.520493542
known operation-wall-s through exact input preparation, including the original
selection arithmetic, every known check failure and3.06CPU-s/3.08wall-s of
engineering review. Final review/publication costs will be appended as known.
Unmetered source/edit/CodeGraph/Git/advice support and unknown selection wall
remain additional and nonzero; the reported sum is not complete wall or support
accounting. The independent reviewer now has the complete ready source, inputs
and integration evidence for final closure before publication/actual admission.

<a id="b06-source-publication-and-first-purchase"></a>

**Independent engineering acceptance and exact first purchase.** The registered
Reviewer completed the full executable review and final identity pass with no
material finding remaining. All71 source hashes, all14 implementation/test
identities and all61 frozen inherited dependencies match; ledger arithmetic
and AST parsing pass. The DM accepts the corrected implementation and its
48-pass mock coverage. Actual Torch/numerical/native reconstruction, throughput
and deadline attainment remain execution risks; neither the reviewer nor the
DM performed a health pilot or real fit/solve/host/query outside the purchase.

The final review adds approximately.499958CPU-s/.501664132wall-s beyond its
previous3.06/3.08 measurement. The final budget input is3,056 bytes, SHA256
`aba525794fc6bb6eb4153e31e5483bf5d0f39b2e61ce6396afc8c3ff77e4711f`, with
47.658729 known new CPU-s/32.022269161 known operation-wall-s
through its last preparation sample. Every known check/review invocation is
included, including the seven corrected reader-fixture expectation failures.
Unknown source/edit/CodeGraph/Git/advice/serialization support remains
additional/nonzero. Study/source identities remain as above.

Publish the exact implementation, tests, inputs and this prospective notebook
on shared main with the owned direction changed to exploring under Root's
already-selected complete purchase. Then make the single formal local_linux
worker request for b06_amortization_a01. The same complete source supplies the
subsequent b06_amortization_read_a01 full reader, using its original worker
locator and an inclusive updated ledger. No second worker, extra world/epoch,
healthy-node trial, automatic retry or unselected effect is authorized. The
first new formal/admission/worker/reader technical failure stops the purchase;
normal deadline fallback remains part of its required complete outcome.

**First formal acceptance,2026-10-03T09:30:59.880899Z.** Exact inputs were
published at `da74047434845cb2f5b1baf3e0023c66ecadf3d9`; the one selected
local_linux worker is accepted under its original
[launch manifest](../../../../runs/uav_decision_generalization/b06_amortization_a01/launch-manifest.json).
The launcher and runner's additional8GiB RAM/12GiB free-disk admission passed;
the saved config reports Python3.10.20/NumPy1.26.3/Torch2.7.0+cpu,4 intra-op/1
interop thread and the bound source identity. Publication itself measured
.800736CPU-s/6.616464391wall-s, to be included in the reader's cumulative ledger.
Launch/observation and later unmetered support remain additional, not zero.

The first observer arm encountered the prior B05 observer's stopped state,
not a scientific refusal or worker failure. Its drained generation18 had no
wake/event pending and only already-read terminal B05 jobs. Rearm19 left those
terminal jobs unchanged; registration of the new worker produced generation20.
The first drain observed the original B06 runner and supervisor running, with
consistent native identities at09:32:01Z. The accepted operation was never
repeated or moved. Observation uses the same native manifest/claim handle via
`temp/directions/uav_decision_generalization/b06_requests/worker-observe.json`;
window1,500s, read-only status interval30s. The native DM stays active through
collection/full reading. This is launch acceptance, not a completed result.

**First execution checkpoint,2026-10-03T09:58Z.** The same admitted worker
remains running with consistent native identities. All three fixed acquisitions
have written fit records; the09:53 progress sample contains26/224 complete
missions,1,276.480665 cumulative measured CPU-s/1,301.589638 operation-wall-s
and1,871,986,688 allocated new-owned bytes. No worker stderr was present.
These are progress facts only; raw prefix costs were visible but no scientific
comparison, selection or plan change is made before the fixed complete reader.
Observer generation20 produced its bounded checkpoint; native App wake returned
-32600 (direct App-server input is not allowed for multi-agent v2 sub-agents).
The active native DM drained that event and rearmed the original handle as
generation21,window1,500s. This observation-delivery failure neither stopped
nor restarted the worker and is separate from technical result failure.

**Checkpoint,2026-10-03T10:25Z.** Original worker running;50/224 missions
complete,2,856.358593 cumulative measured CPU-s/3,083.796112 operation-wall-s,
1,896,128,512 allocated bytes, no stderr. Same-handle observer checkpoint21
drained and rearmed22/window1,500s; native queue refusal remains observation
only. Fixed exposure and limits unchanged; full reading remains pending.

**Checkpoint,2026-10-03T10:51Z.** Original worker running;78/224 missions,
4,373.419188 measured cumulative CPU-s/4,746.900229 operation-wall-s,
1,920,819,200 allocated bytes, no stderr. Same observer22 checkpoint drained
and rearmed23/window1,500s; original worker/plan unchanged.

**Checkpoint,2026-10-03T11:17Z.** Original worker running;105/224 missions,
5,758.211494 measured cumulative CPU-s/6,227.697311 operation-wall-s,
1,945,800,704 allocated bytes, no stderr. Same observer23 checkpoint drained
and rearmed24/window1,500s; original worker/plan unchanged.

**Checkpoint,2026-10-03T11:43Z.** Original worker running;131/224 missions,
7,192.979385 measured cumulative CPU-s/7,756.627341 operation-wall-s,
1,965,203,456 allocated bytes, no stderr. Same observer24 checkpoint drained
and rearmed25/window1,500s; original worker/plan unchanged.

**Checkpoint,2026-10-03T12:10Z.** Original worker running;159/224 missions,
8,721.854511 measured cumulative CPU-s/9,374.113938 operation-wall-s,
1,994,612,736 allocated bytes, no stderr. Same observer25 checkpoint drained
and rearmed26/window1,500s; original worker/plan unchanged.

**Checkpoint,2026-10-03T12:36Z.** Original worker running;189/224 missions,
10,168.842166 measured cumulative CPU-s/10,906.470637 operation-wall-s,
2,020,184,064 allocated bytes, no stderr. Same observer26 checkpoint drained
and rearmed27/window1,500s; original worker/plan unchanged.

**Checkpoint,2026-10-03T13:02Z.** Original worker running;216/224 missions,
11,447.134618 measured cumulative CPU-s/12,269.287054 operation-wall-s,
2,040,303,616 allocated bytes, no stderr. Same observer27 checkpoint drained
and rearmed28/window1,500s; original worker/plan unchanged.

<a id="b06-worker-complete-reader-purchase"></a>

**Original worker complete; full reading pending,2026-10-03T13:13Z.** Native
exit0 at13:09:36.701Z, absent original runner/supervisor and consistent status
were read from the same accepted operation. The controller's READY event28
was drained and acknowledged by rearm29, without another worker. Empty
stdout/stderr, summary COMPLETE, all224 uniquely ordered H1200 missions and
268,800 native advances are present. All seven deployment endpoints started
exactly once. Three fits each made2,112 updates/backwards; total6,336 updates,
403,200 context presentations,1,612,800 training action rows,50,400 initial/final
bank rows and23,040 deployed student rows. The worker reports1,686,240 total
neural rows,270,144 G queries/245,881,600 reserved candidate-ticks, and
5,175,040 R model steps. These are producer exposure/completion facts; the
full independent numerical and physical reconstruction remains required.

Worker source remains `da74047434845cb2f5b1baf3e0023c66ecadf3d9`, with all71
canonical/published source hashes rechecked unchanged. The canonical original
output is `runs/uav_decision_generalization/b06_amortization_a01/` on local_linux.
Its25,186B summary SHA256 is
`1c50b28fe1e1f73682555268cc3461f4b4e5b2873a148a8e51ebb3febaa53673`;
16,244B config `9a76c56e35cf84f5225761f677a48f6d6e04e4ed5c83a4b0a74bf1997d2cddc0`;
1,106,888B per-file identity manifest
`3ef20b267d8c8c93d4e1f6ca19239a97ba89aaf979581e18018acc2b6967f78e`.
The manifest names the one canonical bulk copy, including all mission/rollout
arrays, three initial/final/training checkpoints and journals, and the derived
bank/provenance. These stay in place for the reader; no duplicate bulk collection.

The worker's last meter reports11,980.879742 phase CPU-s/12,842.425336 phase
wall-s, carrying the original47.658729/32.022269 prior once for totals
12,028.538471 CPU-s/12,874.447605 operation-wall-s. New acquisition is separately
189.074781 CPU-s/53.763606 wall-s (not an additional whole-study charge), of
which shared bank handling5.059586 CPU-s and fit0/1/2 costs60.056626/61.114900/
60.520860 CPU-s. Source/output allocated inventory2,052,313,088B; self peak
RSS368,320KiB and child peak368,320KiB are separate process-peak scopes.
Scientific comparison and the claimed affordability remain pending full reading.

The one unchanged-source reader is now prepared at the originally selected
`b06_amortization_read_a01` tag. `B06_WORKER_INPUT.json` is350B, SHA256
`f14fc819f1859730b426273bb456e991ee0986ba28075181dcec335065c6c298`,
and binds exactly the original config/summary/manifest. The4,035B
`B06_READER_BUDGET_LEDGER.json`, SHA256
`8e3a8b6d24e19ac7eb63c303b9f60731e03c6048223b478147e8cf5b3a288593`,
includes the worker cost once, initial publication.800736 CPU-s/6.616464 wall-s
and reader-input/source/hash/roster preparation.379732 CPU-s/.614056 wall-s.
Its known cumulative prior is12,029.718939 CPU-s/12,881.678125 operation-wall-s;
pure engineering48.839197 CPU-s. All unmetered source/edit/observer/launch/Git
support and native/final-serialization tails remain additional/nonzero.

Publish these exact reader inputs, compact worker identity/completion records
and this notebook; current main's owner pause is lifted and this direction
remains exploring under its original lead. Then make the one selected local
reader request. Its actual new NN/model/physical work is exactly the previously
purchased complete reader, with no optimizer replay or old physical replay.
No further worker, extra endpoint, retry or repair is selected. The first
reader formal/admission/runtime failure still stops this purchase.

**Full reader accepted,2026-10-03T13:19:03.795414Z.** Published source/input
commit `4a88c7145540cbee40647e907cef18e4acece6a3` retains all71 scientific
source identities and the exact original study. The one local_linux reader
was accepted with fresh kernel/runner resource admission under its
[original manifest](../../../../runs/uav_decision_generalization/b06_amortization_read_a01/launch-manifest.json).
Its actual process and supervisor were observed running consistently at
13:19:27Z by generation30 in this same session's observer; the original worker
remains terminal and was not restarted. Reader-input publication measured
.828165CPU-s/12.108994wall-s after the frozen ledger sample; add this to the
final cumulative account, alongside unknown support. Same-handle observation
uses `b06_requests/reader-observe.json`,30s status/1,500s checkpoints. The
DM remains active through this complete read and scientific interpretation.

**Full-reader checkpoint,2026-10-03T13:48Z.** The original accepted reader
is running consistently with87/224 missions checked, no stderr,1,721.051884
phase CPU-s/1,668.763310 phase wall-s; known cumulative13,750.770823 CPU-s/
14,550.441435 operation-wall-s plus later publication/unmetered support.
Both source snapshots and canonical outputs account for3,889,561,600 allocated
bytes, below7GiB normal-work stop. Observer30 checkpoint drained/rearmed31,
window1,500s, same operation; no new effects or changed reading.

**Full-reader checkpoint,2026-10-03T14:14Z.** Original reader running;
167/224 missions checked, no stderr,3,236.074325 phase CPU-s/3,157.989955
phase wall-s; known cumulative15,265.793264 CPU-s/16,039.668080 operation-
wall-s,3,889,561,600 allocated bytes. Observer31 checkpoint drained/rearmed32,
window1,500s; fixed reading unchanged.

<a id="b06-complete-reading"></a>

#### 2026-10-03 — Complete B06 fixed-bank learning and ordinary planning comparison

**The students learn the exposed relative-value labels substantially better, but
this does not deliver a useful complete service/CPU replacement for G or either
planner. The ordinary one-cohort program retains a cheaper conditional tail
capability, while four cohorts retain additional request-cost/residence value.**
This is the DM's direct reading; the original independent scientific diagnosis
and resolved next-investment judgment follow below. No new effect, checkpoint
selection, repair fit or extra world follows from these observations.

**Complete paid execution and reading.** The only reader exited 0 at
14:31:09.456Z. Its native runner/supervisor are absent and status is consistent;
stdout/stderr are empty. Generation32 READY was consumed by rearm33 and
observation stopped. Both original worker and original reader succeeded on
first request; no technical-failure exception, restart or additional effect was
used. The canonical local_linux outputs remain
`runs/uav_decision_generalization/b06_amortization_a01/` and
`runs/uav_decision_generalization/b06_amortization_read_a01/`.

The [full summary](../../../../runs/uav_decision_generalization/b06_amortization_read_a01/summary.json)
is 334,713B, SHA256 `d96c839ad22a23c6573c36d0ecd34ffe7a90df5166f5aad1596a7b86b64cd6fe`;
[acquisition checks](../../../../runs/uav_decision_generalization/b06_amortization_read_a01/acquisition-checks.json)
are 29,641B, SHA256 `69fe6f31c5ca392f6c80caf5917fde48cc6704a8a852b27eececd72fcbbb946b`.
They bind worker source `da74047434845cb2f5b1baf3e0023c66ecadf3d9`, reader source
`4a88c7145540cbee40647e907cef18e4acece6a3`, the unchanged 71-file scientific
identity, original bank `d35a36883f81bcdf05248f4de701b19aff309deeb15041e32ef98ff35d865419`,
and the fixed 224-mission rotated roster on worlds 109255000–109255031.

The reader verified all 4,317 worker-manifest scientific files, every new
268,800 motion step / 269,024 actual physical state, masks/routes, arrivals,
FIFO progress/completions, native costs, commands and fixed activation order.
It reconstructed all 5,175,040 R prefix states plus 3,840 initial states,
9,600 selected logical cohorts (1,290 exact reuses) and their 222,720 tape
uniforms, with no incomplete attempt. Worker and reader each account for
270,144 distinct G queries / 245,881,600 candidate-ticks; the 3,840 mirrored
R-base records are excluded from duplicate G work. First-cohort identity
matches for the paired R1/R4 initial public input. Old teacher identities,
2,100 public feature contexts and 8,400 ordered/alias-weighted labels were
checked without replaying old physics or collecting new teachers.

All six initial/final bank forwards and all 23,040 committed deployed student
rows agree in the independent reader. Reader NN rows are exactly 73,440;
worker plus reader total is 1,759,680. All 6,336 update journals, shuffle/RNG,
checkpoint identities and finite diagnostics were checked; no optimizer or
historical changing-network gradient replay was purchased. B's ordered
bordered least-squares solve was independently assembled and checked once.
All seven endpoints started exactly once. Every one of 13,440 actual decisions
met the 20-second deadline, and all committed caches are present; there are
no attempted/completed/uncommitted neural gaps. Maximum decision wall times
G/R1/R4/B/S0/S1/S2 are .1402/6.9717/13.8835/.1294/1.2090/1.0909/1.1724 seconds.
The fixed 20-tick activation delay remains. Thus deadline fallback or an
unexecuted learner does not explain this panel's result; unexercised timeout
paths are not thereby certified.

**Complete service and computation.** Each arm encounters the same 1,803
requests across 32 fresh worlds. C is residence-area cost plus the fixed
240-tick charge per terminal unfinished request; smaller is better. T is the
within-mission maximum *completed* request residence, and W the maximum
same-user service gap. The table gives means of mission summaries, not pooled
request/user quantiles. CPU includes each mission's actual enclosing deployment
work and its persistent endpoint use, including the first cold start.

| Arm | Mean C | Mean T | Mean W | Mean travel m/UAV | Mean CPU s/mission | Unfinished requests / affected worlds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| G | 2601.9375 | 424.40625 | 607.375 | 5100.935 | 3.353334 | 0 / 0 |
| R1 | 2601.6875 | 295.125 | 516.125 | 6915.071 | 81.364700 | 0 / 0 |
| R4 | 2443.15625 | 211 | 518.4375 | 6733.127 | 262.556874 | 0 / 0 |
| B | 3613.25 | 539.8125 | 681.3125 | 14646.539 | 3.263098 | 0 / 0 |
| S0 | 3834.1875 | 549.78125 | 659.34375 | 10977.340 | 4.222370 | 2 / 2 |
| S1 | 4047.84375 | 562.15625 | 694.03125 | 11088.332 | 4.169357 | 6 / 5 |
| S2 | 3843.28125 | 551.5625 | 689.375 | 10957.527 | 4.139062 | 5 / 4 |

These exploratory t95 intervals use 32 paired worlds conditional on the shared
old bank, fixed programs and three optimization replicates. They are not 96
independent worlds, independent teacher acquisitions, equivalence tests or
confirmation. No final student is selected as a winner from this panel.

| Student contrast in C | S0 | S1 | S2 |
| --- | --- | --- | --- |
| minus G | +1232.250 [835.160,1629.340] | +1445.906 [1058.299,1833.514] | +1241.344 [872.211,1610.476] |
| minus R1 | +1232.500 [817.510,1647.490] | +1446.156 [1080.380,1811.932] | +1241.594 [877.002,1606.185] |
| minus R4 | +1391.031 [966.772,1815.290] | +1604.688 [1271.387,1937.988] | +1400.125 [1048.280,1751.970] |
| minus B | +220.938 [−209.586,651.461] | +434.594 [44.665,824.522] | +230.031 [−176.015,636.078] |

The three conditional fit-mean C−G values average +1306.5, df2 interval
[+1006.379,+1606.621]; the separate 32-world average-of-these-three-policies
interval is [+1010.183,+1602.817]. Against B the corresponding mean is +295.188,
with df2 [−4.933,+595.308] and shared-world [−32.176,+622.551]. These differing
conditional scopes cannot be merged into additional acquisition replication.
S0/S1/S2 improve C over G in 3/1/3 worlds and over R1 in 2/1/1; S0 improves
against R4 in three worlds, while S1/S2 lose to R4 in all 32. The favorable
cases remain real observations. For example, at 109255003 S0 lowers G's C
3051→2262 and team travel 46,480.5→28,905.2m, while W worsens 588→704.
At 109255018 S0 beats R4 C 2836→2761, but T/W worsen 142→302 and 524→724.
These cases do not supply a deployable rule for choosing their favorable use.

B also has greater C than G in 30/32 worlds: mean +1011.313
[+760.486,+1262.139]. Its four-constant optimum is an optimum for the exposed
relative-square objective, not for complete native control. Each student
travels about 21.3–22.1km less per team than B and routes 1.465–1.630 more users
per tick on average, with intervals excluding zero for those changes. Those
are retained useful relative capabilities, not a C improvement or an overall
upgrade over G/R. Student mean routed users/tick are 33.138/32.972/33.111,
versus G 36.425, R1 35.510, R4 35.637 and B 31.507. Relative to G, students
add about 35.1–35.9km team travel; continuous radio coverage and request
completion are different outcomes, and distance is not measured energy.

**Retain ordinary tail value and its price.** R1−G C is −.25
[−157.502,+157.002], with 13 better and 19 worse worlds. R4−G C is −158.781
[−320.967,+3.404], with 20 better and 12 worse. Both mean-C increments remain
unresolved, not equivalent. Their prespecified tail readings are useful:
R1−G T/W are −129.281 [−188.407,−70.155] / −91.25 [−142.014,−40.486];
R4−G T/W are −213.406 [−271.095,−155.718] / −88.938 [−143.981,−33.894].
These descriptive secondary results do not replace the primary estimand or
establish uniform improvement. Both finish all requests, as does G.

Reducing four cohorts to one costs service in this complete comparison:
R1−R4 C +158.531 [+29.917,+287.146] and T +84.125 [+44.112,+124.138].
R1 improves C in eight worlds and worsens it in 24. Its W difference −2.313
[−32.419,+27.794] is unresolved, not preserved-value equivalence. R1 reduces
measured CPU from 262.557 to 81.365 seconds/mission, but both are more expensive
than G and both meet the declared deadline. R1/R4 add 10.885/9.793km team travel
and reduce mean routed users/tick by .915/.788 relative to G; R1 is not a
physical-resource upgrade over R4. World 109255006 preserves favorable G→R4
C 3985→2656 and T/W 541/863→241/563, with only 14.0m extra team travel.
At 109255015, G→R4 instead raises C 2268→2985 and W 445→460, despite T
409→283, while adding 23.826km team travel. No single all-service-wins claim
or policy-improvement theorem follows from the sampled planning program.

**Censoring and individual consequences remain.** No workload is empty and
no mission lacks a completed request; T missingness is zero. Students leave
2/6/5 requests unfinished, with maximum observed unfinished ages 300/580/820
and terminal-charge means 15/45/37.5. Most excess C remains residence-area cost:
S−G means +1217.25/+1400.906/+1203.844 before the terminal charge. At 109255016,
S2's completed-request T is only 162, but an unfinished cluster2 request is
already 820 ticks old; the censored maximum must be at least 820. Accordingly
S2's mean censored maximum is 572.125 rather than its completed-only 551.5625.
The reader retains every unfinished identity/age and per-cluster outcome.

All 50 users are served at least once in every mission, but this is not
continuity. Worst observed individual gaps for G/R1/R4/B/S0/S1/S2 are
925/922/922/945/981/1030/1034 ticks. Mean T for every S is worse than G with
positive paired intervals; mean W is worse too, but S0−G W's interval crosses
zero. Means of mission completed-residence p90 are 96.134/97.238/97.963/
133.378/148.941/157.281/139.047 in the same arm order. All arms have identical
mean team-zero-service ticks 4.875; those coarse counts do not erase the
individual gaps or request-scheduling differences. No battery, collision,
energy, universal continuity or all-arrival-tape guarantee was tested.

**Finite fitting succeeded on its exposed objective; complete transfer did not.**
Each scorer made all 64 epochs / 2,112 updates and 134,400 context presentations.
All 192 epoch records were read. Context-weighted online losses start at
.490157/.491514/.491057 and end at .002963/.003989/.003513, with late small
fluctuations; these are changing-model training losses, not 64 independently
fixed endpoint evaluations. Initial/final full-bank loss is the direct endpoint
reading. Parameters move by L2 7.296391/7.308931/7.002549, with
53,652/52,339/52,091 changed coordinates. Maximum recorded gradient norms are
about 1.156/1.245/1.181, below the fixed clipping ceiling10; historical
gradients are finite diagnostics, not independently replayed gradients.

| Exposed-bank endpoint | Mean anchored square loss | Mean model-menu regret (raw request ticks) | Exact first-index teacher agreement | Any teacher minimum |
| --- | ---: | ---: | ---: | ---: |
| Initial canonical G | .504771637 | 19.219500 | .826667 | .828571 |
| Fitted B | .332141700 | 36.520667 | .250000 | .515238 |
| S0 final | .002825349 | 11.106911 | .481429 | .682857 |
| S1 final | .003179516 | 15.334440 | .347619 | .590476 |
| S2 final | .003485640 | 10.045524 | .648571 | .773333 |

B uses raw offsets [452.691409,−88.963437,−54.409412,−309.318560] with the fixed
zero-sum gauge; normal-equation residuals are at most 2.33e−10 and the
constraint residual −1.14e−13. The B endpoint row and any-minimum fractions
above are direct saved-array arithmetic after the full read: no new solve,
network forward, teacher query or physical evaluation. Its lower squared loss
than G nevertheless accompanies larger menu regret. The students reduce
squared error and mean menu regret versus initial G, while reaching a teacher
minimum less often. The bank has 593 tied-minimum contexts; first-index
agreement is deliberately limited, and even the tie-safe frequencies are
not native value. Median teacher first/second margin is 11 raw ticks. Large
aggregate regression improvement therefore does not certify exact ranking
or the value of deploying the induced closed-loop policy. These data neither
prove distribution shift as the cause nor show that no useful student could
be learned from planner information.

**The learned/scored intervention reaches native movement.** B/S0/S1/S2 each
have 1,920 eligible published scores. Their same-input G argmins differ in
1087/840/986/929 cases; all resulting command publications were timely. The
last command in each mission is terminal-unused. Excluding those 32 per arm,
1055/829/974/911 decisions change movement at the actual activation positions.
These changed-motion windows contain respectively 828/763/893/752 completed
requests and nonzero residence costs; they establish executed exposure,
not a causal counterfactual attribution of those outcomes to single choices.
Mean UAV-target changes per mission G/R1/R4/B/S0/S1/S2 are
11.938/26/25.375/108.875/65.875/68.125/65.063; mean FIFO-head interruptions
are 1.406/2.375/2.344/8.875/5.969/5.969/6.469. The supplied executor and
ordinary complete competence remain; inactive branches, fallback and no
parameter movement cannot account for this adverse complete student result.

**Complete cost and honest CPU crossings.** New acquisition costs 189.074781
CPU-s, including the shared bank 5.059586, constant solve .101716, and three
fits 60.056626/61.114900/60.520860 CPU-s plus artifact overhead. It is not added
again to worker cost. Worker deployment sums 11,618.201429 CPU-s, with
173.603532 CPU-s enclosing setup/closing/metadata residual after acquisition.
The full reader costs 4,376.407474 CPU-s / 4,287.369193 wall-s. Its final known
inclusive cumulative account is 16,406.126413 CPU-s (4.557257h) /
17,169.047318 operation-wall-s (4.769180h), plus reader-input publication
.828165 CPU-s / 12.108994 wall-s and later reading/review/publication/cleanup.
Four explicitly metered DM saved-reading calculations add 1.643807 CPU-s /
.619245 wall-s; other support and last-serialization/native-supervisor tails
remain additional/nonzero. Peak new-owned allocation before cleanup is
3,910,459,392B; reader self peak RSS327,656KiB, worker368,320KiB, no GPU.
These are process peaks, not a simultaneous sum. The original10 CPUh/24
operation-wallh/8GiB limits, including their finalization reserves, were not
expanded. Final publication/cleanup costs and actual deleted targets follow.

The measured per-use student CPU savings against R1 are 77.142–77.226 seconds
and against R4 258.335–258.418 seconds. Sharing the already paid bank plus one
new fit gives CPU-only crossings .844–.857 uses against R1 and .252–.256
against R4. Including the historical teacher's measured 7,026.128558 CPU-s
moves those lower bounds to 91.831–91.924 and 27.443–27.450 uses; its extra
outer/verification/support costs remain unknown. The whole-study curves use
the reader's comparison-time 16,403.543209 CPU-s intercept, once for the whole
study: about 212.411–212.640 and 63.477–63.497 uses, before the final enclosing
meter/support additions. No crossing exists against G or B because every
student's measured per-use CPU is greater. None is a matched-service break-even:
the students have worse actual service, G is cheaper, and no deployment volume,
request-tick/CPU exchange rate or equivalence rule was assumed. Original B05's
whole ~5.374 CPUh and its teacher-only1.951702h overlap and are not added twice.

**Working explanation update before independent disposition.** The earlier
[topic5 reading](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据)
separated ordinary task competence, finite DDQN acquisition and R's conditional
tail capability. B06 strengthens the ordinary capability and locates an actual
planning-compute tradeoff. It also establishes strong finite supervised fitting
on one exposed bank, while weakening the proposed inference from those fits
to useful full deployment. It does not repeat or diagnose B05's Bellman/absolute
cost-calibration failure. Saved menu ranking errors, finite noisy teacher targets,
subsequent state visitation and complete-horizon decision consequences remain
unseparated; none is a demonstrated repair prescription. Improved bank loss,
cheaper computation than R or relative travel/coverage gains over B do not
cancel the paid native losses. Conversely, the loss does not refute broader
learning, information use or the retained planning capability. The independent
review now receives these original sources and complete outcomes; it will
challenge the explanation and the next investment, without a new effect.

**Canonical evidence retention for this reading.** Compact reader config,
admission/launch/exit facts, acquisition checks and full per-world summary,
plus each fit's endpoint/epoch record and final endpoint counters, are published
with this entry. The worker manifest already identifies every one of its
4,317 scientific files by exact path, bytes and SHA256. On `local_linux`, retain
that one original worker output, including its bank/provenance, initial/final
weights, final optimizer state, update journals and all actual/model traces;
do not copy the old B05 teacher evidence. The reader's unique 224 per-mission
check files remain at the canonical
`runs/uav_decision_generalization/b06_amortization_read_a01/checks/`, totaling
19,634,934 logical bytes. Their ordered content identity is
`c2820858da84561e9de260964bec2af3ba6f9dba134cfeebbce6f136b9ad7a00`:
SHA256 of the concatenation, in sorted relative-path order, of UTF-8
`relative_path + NUL + file_SHA256_hex + LF`. No bulk copy or new retention
package was made. This inventory/hash reading added .328947 CPU-s /
.158694 operation-wall-s; other support remains additional. Terminal facts
come from `process-exit.json` and reconciled native status; the immutable
`launch-status.json` still records its original `accepted` event.

<a id="b06-independent-review"></a>

#### 2026-10-03 — Original independent B06 ResearchCritic answer

The existing registered ResearchCritic worked in its separate review context,
reconstructed original outcomes before asking for the DM interpretation, and
returned the following complete answer. It made no new scientific execution.
The text below is preserved in full; the DM response follows it.

---

建议 **停止 B06 这套固定 B/S 配方，不追加训练或确认；保留 G 的经济参考地位及 R1/R4 的条件性规划能力。** Parent 的学习与用途问题仍开放。这里最有分量的解释修正是：学生大幅改善了回归拟合，但连训练 bank 内的动作排序保真都未改善，不能把结果讲成“已经学会教师，随后才因新世界分布变化失败”。

本轮沿用此前独立 ResearchCritic 上下文。我先重建原始证据并形成上述判断，之后才读取 DM 的新解释与处置。[DM 完整读数](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md:9220) 已明确区分拟合、决策保真和闭环用途；其停止固定配方、保留条件能力的处置与证据相符。

**实际核查范围。** 我核验了 worker/reader 的来源绑定、共同的 71 文件科学身份，全部 224 个原始 mission NPZ 与 metadata 的哈希，以及原始请求、完成、未完成、成本、用户服务间隔、覆盖和路径。逐个重算了 B/S 保存分数到实际动作的组合与排序，检查了 R1/R4 全部 3,840 次决策的完整 cohort 均值和动作，以及所有 16 个对比的 240 条指标向量。七臂的初始条件、实际到达输入及其 RNG 地址匹配。

我还检查了六个初末 bank 输出、原始 fit/epoch/update 证据，重建全部 192 条 epoch 损失记录，并独立复算 12 条 CPU crossing。未加载模型、重做前向、优化器或物理过程；完整物理重建和前向一致性采用已有[完整 reader](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b06_amortization_read_a01/summary.json)及承重源码检查。历史梯度仍未独立重放。

每臂共同遇到 1,803 个请求。下表除“未完成”是全 panel 总数外，均为 32 个 mission 指标的均值；T 只统计已完成请求，W 是最大单用户服务间隔。

| 臂 | C | T | W | 未完成 | 路径 m/UAV | 覆盖用户/ tick | CPU秒/mission |
|---|---:|---:|---:|---:|---:|---:|---:|
| G | 2601.94 | 424.41 | 607.38 | 0 | 5100.94 | 36.425 | 3.353 |
| R1 | 2601.69 | 295.13 | 516.13 | 0 | 6915.07 | 35.510 | 81.365 |
| R4 | 2443.16 | 211.00 | 518.44 | 0 | 6733.13 | 35.637 | 262.557 |
| B | 3613.25 | 539.81 | 681.31 | 0 | 14646.54 | 31.507 | 3.263 |
| S0 | 3834.19 | 549.78 | 659.34 | 2 | 10977.34 | 33.138 | 4.222 |
| S1 | 4047.84 | 562.16 | 694.03 | 6 | 11088.33 | 32.972 | 4.169 |
| S2 | 3843.28 | 551.56 | 689.38 | 5 | 10957.53 | 33.111 | 4.139 |

三个学生相对 G 的平均 C 增量分别为 **+1232.25、+1445.91、+1241.34**，各自的探索性配对区间均在零以上；相对 R1/R4 也全部更差。相对 B 的 C 增量为 +220.94、+434.59、+230.03，其中 S0/S2 区间跨零。学生相对 B 确实少走约 3.56–3.69 km/UAV、平均多覆盖 1.465–1.630 个用户，但这不足以形成对 G 或规划器的完整替代用途。

三个 fit 的 C−G 均值为 +1306.5，条件 df2 区间为 [+1006.38,+1606.62]。这是同一个 bank、同一个 panel 下的三次优化重复；另一个按共同世界计算的区间回答不同问题。两者都不能成为 96 个独立世界或三次独立教师采集。

**局部正例必须保留，不能据此挑选学生。** 对 G 的 C 改善逐个是：

- S0：世界 003/016/018，分别 −789/−185/−115。
- S1：世界 006，−691。
- S2：世界 003/006/025，分别 −422/−459/−209。

世界编号均省略共同前缀 109255。S0 在 003 同时降低 C、路径并提高覆盖，但 T/W 分别增加 16/116。S2 在 003 同时降低 C/T/W，分别 −422/−145/−173；其路径却增加约 3.68 km/UAV，覆盖减少 2.238。其余正例也保留在完整向量中，尚无可部署规则能事先识别这些有利用途。

完成请求的筛选会改变尾部解读。[S2 世界 016](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b06_amortization_read_a01/checks/main/S2/109255016.json) 的 T 为 162，低于 G 的 581；但它留下了一个已等待 **至少 820 秒**的请求，C 增加 524、W 增加 337。加入这个观察下界后，S2 的平均 censored maximum 是 572.125，而不是 551.5625。三个学生的平均用户最长间隔相对 G 分别增加 35.85/44.69/31.09 秒，同时存在个别用户改善；这些用户记录不是额外独立样本。

**拟合的正面结果是真实的，但其含义有限。** [初末 acquisition 证据](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b06_amortization_read_a01/acquisition-checks.json)支持：

| Bank 指标 | 初始 G | S0 | S1 | S2 |
|---|---:|---:|---:|---:|
| 相对成本 MSE | .504772 | .002825 | .003180 | .003486 |
| 平均教师菜单 regret | 19.2195 | 11.1069 | 15.3344 | 10.0455 |
| 选择教师非最优动作的菜单数 | 360 | 666 | 860 | 476 |
| 1,507 个唯一最优菜单中的正确数 | 1148 | 876 | 693 | 1042 |

所有 64 epochs、2,112 updates/fit 都完成了，参数有实质变化；训练曲线大幅下降，末期有小幅波动。这里已经有“固定小网络能够用有限优化明显拟合这些暴露标签”的证据，不能用“没有学动”解释失败。但较低平均 regret 与更频繁的错误排序同时成立，说明回归改善集中在哪些误差上，和控制需要保住哪些动作差异，并非同一个判断。

388 个教师四动作全并列的菜单，在三个学生中全部变成了严格排序；其中 310/384/191 个改选非 KEEP。B 也提供相同方向的反例：它把平方损失从 .504772 降到 .332142，却把平均教师 regret 提高到 36.5207。最低二乘误差不是任务控制最优性。

这些证据支持“有限回归目标没有保证决策保真”的诊断。教师标签噪声、有限优化、后续状态分布及完整时域后果仍可参与解释，尚不能唯一归因。新损失只约束相对值，共同偏移未被识别，不能搬用 B05 的绝对成本/Bellman offset 故事。

**这也是实际执行的负面干预。** 全部 13,440 次决策按时完成，缓存完整；七个 endpoint 各启动一次。S0/S1/S2 分别有 829/974/911 次已激活运动不同于同状态 G。它们不是未激活或仅有少量选择机会。

其中仍有 743/914/808 次发生在有队列的状态，748/921/814 次发生在 G 成本非全零的状态。因此，末期空队列上的并列破坏确实存在，却不能单独解释大部分损失。直接加一个末期 KEEP 补丁，尚无证据会修复完整 C。上述对应关系也不等于已经识别了每次动作的反事实因果损失。

**R1/R4 的正面能力及代价都应保留。** 相对 G：

- R1 的 T/W 均值下降 129.28/91.25；C 差 −0.25，区间跨零。
- R4 的 T/W 均值下降 213.41/88.94；C 差 −158.78，区间为 [−320.97,+3.40]。
- 两者均完成全部请求，但路径增加、平均覆盖下降，也都有 adverse worlds。

R1 比 R4 少用约 69% CPU，却付出 C +158.53、T +84.13 的代价，两项配对区间均在零以上；W 差异未确定。因此，R1 提供的是另一种有用取舍，不能称为保留等价服务的压缩教师。G、R1、R4 都应继续作为有能力的普通比较对象。

**成本支持停止当前配方，而不是从便宜拟合推导便宜成功。** 三个 fit 各约 60–61 CPU秒，整个新 acquisition 为 189.075 CPU秒；完整研究截至 reader 已用 **4.5573 CPUh / 4.7692 累加 operation-wall h**。另有已测 publication、DM/reviewer 读取及未计支持成本，不能视零。

学生相对 R1/R4 的 CPU-only crossing 很早：已付 bank 加一个 fit，分别约 .84–.86/.25–.26 次使用；计入历史教师的已测成本后，下界约 92/28 次使用。可是学生的实际服务更差，而 G 还更便宜，因此这些均非同等服务的盈亏平衡。相对 G/B 没有学生 CPU crossing。历史教师成本与原 B05 整体研究成本有重叠，不应重复相加。

我的下一投资建议是 **本轮不购买新实验**。复制当前配方主要增加条件于这个 bank 的重复，不能自动解决已观察到的排序—控制问题；更多 epochs、更多数据或改变 loss/gate 也各自改变了待检验假设和成本，现有结果没有指定其中哪一种应立即购买。这一停止不要求证明所有修复都无效，也不关闭学习问题。

最强的建设性保留是：规划存在可用的条件尾部能力，且教师相对值能够低成本拟合。如果 Root 后续选择继续这个问题，我更看重“在明确服务—计算用途下，何时值得支付规划”的比较，而非立即修补当前回归器。最小值得购买的完整观察应是一个冻结调用策略，与同信息、同资源口径的 G/R1/R4 和简单调用规则作配对比较，计入实际调用、训练、完整读取及支持成本，同时保留 C、完成/未完成、T/W、路径、覆盖和选择激活。具体规则、panel、是否训练及完整价格目前尚未冻结，不能把约 60 秒拟合成本当成这项后继研究的报价。

其结果应改变真实选择：普通规则即可取得用途时，不支持学习必要性；学习策略在匹配的普通比较对象上取得完整净收益时，才支持受训练单位限制的窄学习结论；仅降低计算却损失服务时，应记录取舍；未调用或很少改变选择时，只能限制该策略的用途，不能据此否定规划机会。这里没有自动续跑或诊断阶梯的建议。

本次新增纯读取/保存数据算术已测 **6.39885 CPU秒、已知 wall 5.89941秒**；其中一次 schema 定位失败已计入。其他源码阅读、命令及推理支持未完整计时，非零。新增 fit、NN forward、规划查询、物理或 native 调用均为零。

**MATERIAL_DISSENT: no。** 对 DM 当前“停止固定 B/S 配方、保留条件规划能力、不立即购买修补实验”的新投资处置无实质异议；其解释已经保留了训练 bank 内的决策保真不足及完整 native 负面证据。

---

<a id="b06-independent-disposition"></a>

#### 2026-10-03 — DM response and resolved investment

I read and accept the complete independent reconstruction and recommendation.
**End this fixed B/S investment without another fit, loss/KEEP-gate patch,
confirmation, panel or automatic planner repeat. Retain G, R1 and R4 as useful
ordinary alternatives, the finite supervised-fitting capability and every
favorable/adverse learned case.** The larger question of learned decision
modules remains open. No material scientific disagreement is being self-cleared;
the reviewer reports `MATERIAL_DISSENT: no`. This adequate independent review
covers the actual new evidence and stopping decision; no distinct unresolved
expertise question presently motivates an additional Pro consultation.

The consequential refinement is stronger than an undifferentiated transfer
failure. Regression loss and average menu regret improve, while selecting any
teacher minimum becomes less frequent on the already exposed bank. I checked
the saved bank and endpoint arrays directly: 1,507 unique-minimum contexts,
G/S0/S1/S2 correct counts 1,148/876/693/1,042, and nonoptimal counts
360/666/860/476 agree. All 388 all-action teacher ties acquire strict student
orders, with 310/384/191 non-KEEP choices. These are zero-new-forward arithmetic
checks, not additional fitting or evidence from a new distribution. The
observation rejects the narrow story that good regression had already preserved
teacher decisions and only fresh deployment introduced the problem. It does
not identify the ranking errors' unique cause, and lower average teacher regret
remains a genuine positive observation. The target's unidentifiable common
offset also prevents importing B05's absolute-Q explanation into B06.

For clarity, the review's +35.85/+44.69/+31.09 individual-gap increments average
the 50 users' longest gaps and then the 32 worlds; my direct saved-check
recalculation gives +35.852500/+44.691875/+31.085625 ticks. They are distinct
from the mission-level maximum W increments +51.96875/+86.65625/+82.0.
Neither treats users as extra independent worlds. The completed-only T and the
unfinished 820-tick lower bound remain separate. These source checks add known
1.027487 CPU-s/.372907431 operation-wall-s; two non-scientific schema-location
errors and other support are additional/unmetered, not zero. They caused no
model, optimizer, environment or policy call.

The complete native S/B losses and R1/R4 tradeoff change the investment judgment.
Small fitting cost cannot turn inferior service into a matched-use amortization
claim. R1 preserves an ordinary cheaper tail option, with explicit C/T losses
versus R4, while G remains the lower-CPU and competitive primary-cost reference.
All planners met the deadline. No transfer mechanism or equivalence is needed
to retain those useful conditional programs; none justifies a universal upgrade.

The next worthwhile continuation, if Root selects this question again, would
ask when paying for planning has a consequential complete service/compute use,
with G/R1/R4 and a competent same-information ordinary invocation rule. A learned
invocation strategy would need its complete acquisition/deployment/reading
price and an independently reviewed prospective prediction against that rule.
Existing fixed-panel capability is a reason to consider this, not an automatic
new experiment or a mandate to make a small residual around G. Source-level
representation changes, more data, changed relative loss, a KEEP rule and
unchanged replication currently have no evidence-selected predicted repair
strong enough to displace stopping. The broader parent's next allocation belongs
to Root under this native-child assignment. There is no producer, unresolved
operation or external dependency after publication/cleanup; the direction is
idle in reserve, with no scheduled check or selected effect.

The new pure reading cost reported by the ResearchCritic is 6.398850 CPU-s /
5.899410 operation-wall-s. Compact evidence publication `97c79fbcb72d1eb7cf0d96eaa9f20d93ec15dae0`
adds .665721 CPU-s /8.883873 operation-wall-s. These are added once beyond the
reader's inclusive meter, together with its previously recorded later publication
and DM reading costs. Final exact cleanup and publication are recorded below.

<a id="b06-final-cleanup"></a>

#### 2026-10-03 — Publication, measured cleanup and final boundary

The complete quantitative reading and compact original outcomes were published
at `97c79fbcb72d1eb7cf0d96eaa9f20d93ec15dae0`; the complete original independent
answer and resolved stopping judgment at
`2fceacff9866708e8816d045d3577e6b3c4bf044`. Source remains recoverable at the
original worker `da74047434845cb2f5b1baf3e0023c66ecadf3d9` and unchanged-science
reader `4a88c7145540cbee40647e907cef18e4acece6a3`. Publication of the independent
review added .660309 CPU-s /7.838313 operation-wall-s.

Both accepted operations and their observation are terminal, the full reader
and independent review are read, and no helper has an unfinished assigned effect.
The supported snapshot collector freshly reconciled the original process/claim
identities and inspected live Linux references with its read-only privileged
scan before deleting both exact snapshots. Neither had a live consumer. A
scoped consumer search found no external B06 source/output dependency; retained
scientific files were explicitly checked disjoint from deletion targets. The
useful ten-module implementation and four focused tests remain as the canonical
executable definition/reader for the retained ordinary planners and learning
comparison. No unused prototype or standalone helper was added by this study.

Actual deleted targets and their pre-deletion allocated bytes:

| Exact target under `/home/fires/hmasd-wsl/` | Allocated bytes removed |
| --- | ---: |
| `.git/hmasd-launch-sources/48b1e23eed7846f391b23f4a5c6e8f36` | 1,835,995,136 |
| `.git/hmasd-launch-sources/bc68aef94727442cbc082d4f97921e2e` | 1,837,187,072 |
| `runs/uav_decision_generalization/b06_amortization_a01/scratch/` | 118,784 |
| `runs/uav_decision_generalization/b06_amortization_a01/progress.json` | 49,152 |
| `runs/uav_decision_generalization/b06_amortization_read_a01/progress.json` | 12,288 |
| `runs/uav_decision_generalization/b06_amortization_read_a01/reading.json` | 335,872 |
| `temp/directions/uav_decision_generalization/b06_tests/` | 4,096 |
| `temp/directions/uav_decision_generalization/b06_engineering_receipts/` | 36,864 |
| `temp/directions/uav_decision_generalization/b06_requests/` | 12,288 |
| `experiments/candidates/uav_decision_generalization/b06_request_amortization/__pycache__/` | 126,976 |
| `tests/experiments/candidates/uav_decision_generalization/b06_request_amortization/__pycache__/` | 122,880 |

All eleven targets are absent. The declared B06 owned-root inventory, including
directories and deduplicating `(device,inode)` without following symlinks,
fell from **3,910,471,680 to 236,470,272 allocated bytes**: net
**3,674,001,408 bytes reclaimed**. The later pre-cleanup maximum is 12,288B above
the reader meter because subsequent compact receipts/output were written. This
is allocated storage in the named scope, not a claim about Git-object shrinkage
or total host free capacity. No full backup, archive, duplicate output or
retention chain was created. There is no cleanup blocker or leftover target.

All 4,317 manifest-bound scientific files and 224 unique reader check files
remain present in the single canonical outputs. Frozen summaries/configs,
launch and exit facts, fit/epoch records, checkpoints and all positive/adverse
world evidence remain. The removed `reading.json` matched the final summary
in every field except its earlier enclosing cost sample; final summary retains
the later full cost and the comparison-time CPU intercept. Progress prefixes
were superseded by complete outputs, with accepted/checkpoint facts already in
this notebook. Endpoint scratch mirrored the completed counters/cache traces,
which remain in published endpoint records and original mission arrays. The
consumed engineering receipts' checks, hashes, failures and measured costs were
already read and recorded above before their scratch directory was deleted.

The cleanup itself measured **5.100519 CPU-s /5.566700 operation-wall-s**.
Known cumulative new work through this measured cleanup is
**16,422.780218 CPU-s (4.561883h) /17,210.495454 aggregate operation-wall-s
(4.780693h), 0 GPU**, counting each published/reader/acquisition scope once.
This includes the reader's 16,406.126413/17,169.047318 inclusive sample, later
reader-input publication .828165/12.108994, four original DM reading calculations
1.643807/.619245, retention inventory .328947/.158694, later checked-reading
1.027487/.372907, independent review 6.398850/5.899410, evidence publication
.665721/8.883873, review publication .660309/7.838313 and cleanup above.
The final index/closure publication, two later schema-location errors, other
unmetered source/Git/launch/observer/reading support and serialization/native
tails are additional/nonzero. This is a known measured account, not a complete
upper bound on unknown support. No resource ceiling or scientific allowance
was expanded, and no further model/optimizer/planner/physical call occurred.

At this substantive boundary the own RESEARCH standing moves to **reserve/idle**,
with the enduring learning question and original lead retained. Topic5 is
revised to separate task competence, fitted relative values, action fidelity
and complete service/CPU value, while preserving R1/R4 tail capabilities and
their actual tradeoff. There is no active producer, unread result/review,
scheduled continuation or external blocker. The native parent receives the
published result and optional future planning-use question; no additional
effect is selected by this closure.

<a id="b07-prospective-construction-20261003"></a>

#### 2026-10-03 — Source-only construction of online planning-work allocation

Root has assigned this same, non-archived DM bounded prospective construction
after integrating B06 at `f12758b88` and the owner-requested workflow
consolidation at `0a621fd228f84d99f87e6acc4a43a630d430ca16`. This authoring scope
is source reading, saved-data arithmetic and a priced complete comparison;
there is **no new native/model/optimizer/learner check or result launch**.
The existing scientific review supports stopping B06 and considering a useful
planning-use question, but does not substitute for review of the new actual
design. Root owns cross-question selection and a distinct Pro framing question;
no Pro send is delegated here. Accepted A/C work remains independent and its
unfinished outcomes are not inputs to this construction.

I read current published pause/ownership, topic5 and the affected consolidated
methods, reusing the complete primary B06 quantitative reading above. Direct
source reading of B06's endpoint adapter and inherited B05 rollout, deadline,
G and RNG definitions precedes interpretation of the Oracle proposal below.
The [current shared judgment](https://github.com/CartmanFatass/My-paper-code/blob/0a621fd228f84d99f87e6acc4a43a630d430ca16/docs/research/RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据)
changes the question from replacing R with the failed regressor to developing
R's demonstrated conditional tail capability at an explicit computation price.
G remains a strong ordinary alternative, R1/R4 have a real C/T tradeoff, and
all old decisions met deadlines. New computational thrift therefore needs a
complete use comparison; it cannot be credited with an already observed deadline
benefit or called a learned capability when no fit is performed.

<a id="b07-root-oracle-original-20261003"></a>

#### Complete original B/D construction advice from Root's temporary Oracle

Received once through native communication from
`/root/four_dm_allocation_oracle`, under Root's explicit request to preserve
the full original here and share this single source with D/Root. This is the
coauthor's complete message, not an independent Scientific Review or an effect
authorization. Its identity is recorded after the verbatim text.

<!-- B07_ROOT_ORACLE_ORIGINAL_BEGIN -->
I sent the preceding D consultation to D once, in full, as requested.

My preferred allocation is **B on allocating online planning work, and D on direct planner imitation using B’s frozen teacher bank**. B is the stronger immediate purchase. D is a worthwhile, bounded learning study because it tests a different decision objective at modest acquisition cost, with a complete deployment comparison. Neither assignment depends on A/C results or changes their accepted studies.

This is coauthor advice, not the independent Scientific Review.

I reconstructed B06’s original observations before reading its interpretation: all 224 worker mission JSON records, the full 32-world comparison vectors, acquisition records, and source bindings. All 71 bound source files matched. The 224 records reconstruct the request-area costs and terminal unfinished counts; I did not independently rerun native physics or historical optimizer updates. The complete-record reduction used 0.354 CPU seconds, source hashing 0.010 seconds, and the final exposure arithmetic 0.000414 seconds, apart from ordinary source/metadata reading.

The useful starting point is quite specific:

| Endpoint | Mean request cost \(C\), lower better | Mean maximum completed-request residence | Mean worst-user RF service gap | CPU seconds/mission |
|---|---:|---:|---:|---:|
| G | 2601.94 | 424.41 | 607.38 | 3.35 |
| R1 | 2601.69 | 295.13 | 516.13 | 81.36 |
| R4 | 2443.16 | 211.00 | 518.44 | 262.56 |
| Constant B | 3613.25 | 539.81 | 681.31 | 3.26 |
| S0 | 3834.19 | 549.78 | 659.34 | 4.22 |
| S1 | 4047.84 | 562.16 | 694.03 | 4.17 |
| S2 | 3843.28 | 551.56 | 689.38 | 4.14 |

R4–G’s mean \(C\) difference is −158.78, with a paired 95% interval of [−320.97, +3.40]. Its two reported tail reductions are clearer. R1 retains substantial tail improvements over G, but its request cost is +158.53 worse than R4, interval [+29.92, +287.15]. R1 and R4’s worst-user-gap difference remains unresolved; that is not evidence of equivalence.

These are heterogeneous benefits. In world 006, R4 reduces \(C\) from 3985 to 2656. In world 015, it increases \(C\) from 2268 to 2985 despite shortening the maximum completed-request residence. Across the 1803 matched requests, R4 gives 262 shorter residences, 348 longer ones, and 1193 ties. A tail improvement therefore does not mean uniform improvement for individual requests.

The learning evidence is also substantive. Three fits reduce bank relative MSE from 0.50477 to 0.00283–0.00349, yet first-index teacher-minimum agreement falls from 82.67% to 34.76–64.86%. That statistic is **not** agreement with R4’s full tie-breaking rule. All three students materially change commands; they are not inert networks. They leave 2, 6, and 5 requests unfinished, while G/R1/R4 finish all requests. Their shared-bank three-fit mean \(C\) penalty against G is +1306.5. Positive student worlds remain real, but do not rescue the complete comparison. These facts support another carefully chosen learning question; they do not establish learning impossibility or identify a unique regression defect. Sources: [complete reading]( /home/fires/hmasd-wsl/runs/uav_decision_generalization/b06_amortization_read_a01/summary.json), [acquisition checks](/home/fires/hmasd-wsl/runs/uav_decision_generalization/b06_amortization_read_a01/acquisition-checks.json), and [B06 notebook](/home/fires/hmasd-wsl/docs/research/candidates/uav_decision_generalization/NOTES.md).

**1. Assign B one complete study of whether state-dependent scenario allocation improves the ordinary planning cost frontier.**

The question is: *At a fixed ceiling on native forecast work, does deciding when to use two versus four scenarios produce better service than competent fixed allocations?*

The premise is R4’s useful but expensive planning capability and R1’s partial retention of it. The conjecture is that disagreement between the first two scenario decisions identifies occasions worth additional work. The existing results do not establish that conjecture.

Keep the B05/B06 task and lawful interface: six UAVs, the four existing commands, 1200 native ticks, 20-tick decision period and command delay, existing public reset/report, existing 160-tick native forecasts and G continuation. No request ages, private future arrivals, new sensing, reward changes, or learned selector are needed. R2 and R3 can stop the existing search after the corresponding complete cohort, using the same mechanism as R1. The [rollout source](/home/fires/hmasd-wsl/experiments/candidates/uav_decision_generalization/b05_request_schedule/rollout.py) already publishes a decision after each complete cohort.

Use seven fixed endpoints:

- G, R1 and R4.
- Uniform R2 and uniform R3.
- A **fixed clock allocation**, S: during decision indices 0–46, use R4 at odd indices 1, 3, …, 45; R2 at even indices 0, 2, …, 44; and R3 at index 46. Thereafter, two logical cohorts suffice because the future-arrival tapes are empty and exact physical reuse applies.
- An **adaptive allocation**, A: compute two cohorts; compare their individual winners under the existing `(forecast cost, raw G cost, action index)` order. If they disagree and the remaining allowance can fund both additional cohorts while reserving worst-case R2 work for every remaining decision, compute cohorts three and four. Otherwise commit the two-cohort mean. Retain the original deadline and last-complete-publication behavior.

S is necessary. Without it, an A–R3 gain could come from mixing two and four scenarios rather than from identifying useful occasions for extra computation.

Give A a per-mission ceiling of **96,320 native forecast transitions**, equal to uniform R3’s source-derived maximum. Charge attempted work, preserve exact-cohort reuse, and reserve future baseline work before upgrading. This is a ceiling on forecast transitions—not a claim of equal actual CPU time. Publish actual CPU, G work, reuse, deadline outcomes, and unused allowance for every endpoint. Do not label two-scenario agreement a statistical confidence certificate.

The smallest useful complete design is all **32 already exposed B06 worlds**, with exact reuse of the audited G/R1/R4 records and new R2/R3/S/A missions. That is 224 comparison records, of which **128 missions and 153,600 native ticks are newly purchased**. No world subset, tuning panel, or outcome-dependent extension. It is a development comparison on an exposed panel, not fresh-world confirmation. Reuse is valid only while the imported task, ordinary policies, RNG laws and physical interfaces remain source-bound to the existing records.

The leading comparisons are A–S and A–R3 in \(C\), accompanied by the complete cost–service frontier against R1/R2/R4/G. Reconstruct unfinished requests, completed-request residence, worst-user RF gaps, individual request differences, command changes and travel. Retain censoring: a smaller maximum among completed requests does not compensate for leaving an old request unfinished.

Informative outcomes are:

- **Positive:** A improves \(C\) over both S and R3 at the declared work ceiling, with the service and actual-CPU comparisons supporting a useful trade. This supports adaptive allocation on this panel. Any apparent preservation of R4 still needs an explicit preservation criterion; an interval crossing zero is insufficient.
- **Adverse:** S or R3 matches or beats A; disagreement spends work on noise or misses shared errors; early upgrades exhaust useful later allocation. Close this selector. A newly established R2/R3 ordinary frontier can still be a useful result.
- **Inconclusive:** small effects and broad paired intervals. Preserve the complete cost frontier without claiming adaptive value or automatically buying another selector.

The strongest objection is that **R1 already obtains much of the observed tail benefit**, while G completes every request at a fraction of the cost. Also, every B06 endpoint met its deadline. Computation saved by A cannot be advertised as an observed deadline-service benefit. The study must establish a better practical trade, not merely fewer forecasts than R4.

The exposure forecast is:

| Item | New B study |
|---|---:|
| Fits / training updates | 0 / 0 |
| New native missions / ticks | 128 / 153,600 |
| Maximum native forecast transitions, worker | 11,366,400 |
| Model initializations, worker | 7,680 |
| G query ceiling, completed-path calculation | 571,904 |
| Conservative nominal G candidate-tick allowance | About 0.55 billion |
| Worker plus complete reader CPU forecast | **8–12 hours** |
| Additional acceptance/collection allowance | **Up to 2 CPU hours**, explicitly metered |
| Standalone elapsed-time planning range | Roughly 10–16 hours |
| Incremental retained/peak artifact allowance | Roughly 8–12 GiB |
| GPU | 0 |

The CPU forecast uses observed R1/R4 mission costs to interpolate approximately 6.1–6.7 worker CPU hours, then prices the complete reader and uncertainty. The reader must reconstruct the new physical records, G scores, allocations and commands; this is substantial paid reading.

**2. Assign D a separate complete study of direct decision imitation, with the frozen bank and architecture held fixed.**

The question is: *Can direct imitation of the planner’s chosen command produce a useful low-cost deployed policy where relative-value fitting did not?*

This is a direct learning-development question, not a claim that classification is the diagnosed repair for B06. Its value is the controlled contrast between learning numerical relative costs and learning the resulting decision. I prefer one complete test to either abandoning learning from this finite result or entering a sequence of loss, feature and KEEP-rule adjustments.

Use the same sealed bank: 2100 contexts from 35 worlds and four logical R-cohort labels per context. Keep the 303-input, 128–128 hidden-layer residual scorer, its 55,553 parameters, the three byte-identical initial parameter sets, original shuffles, Adam settings, clipping, batch schedule, and 64 epochs.

Make one declared objective change:

\[
a_R=\operatorname{lexargmin}_a
  \left(\overline R_a,\ G_a,\ a\right),\qquad
q_a=G_a/1200+f_\theta(x_a),
\]

and train cross-entropy on `softmax(-q)` with fixed temperature 1 and target \(a_R\). Deploy the original hard score ordering.

A consequential source detail: the archived bank’s `teacher_action` is `argmin(teacher_cost)` with first-index tie-breaking. **Derive \(a_R\) from the saved cost vectors and R4’s actual raw-G tie-break; do not blindly use that archived field.** The [acquisition implementation](/home/fires/hmasd-wsl/experiments/candidates/uav_decision_generalization/b06_request_amortization/acquisition.py:433) makes the distinction explicit.

Use all contexts, including the 388 all-four-cost ties. No filtering, KEEP veto, teacher recollection, architecture change, epoch extension or seed selection. Preserve all three endpoints.

Evaluate **nine arms on 32 fresh worlds**:

- G, R1 and R4;
- all three frozen B06 regression students S0/S1/S2;
- all three new imitation students I0/I1/I2.

That is **288 new missions and 345,600 native ticks**. Reserve the unused world namespace before execution; the exact IDs remain an input-contract item for the selected DM. Finish the complete comparison even if bank fidelity disappoints. There is no “successful training metric” gate that releases deployment testing.

The useful comparisons are paired I–S effects under the matched initialization/shuffle and I against G/R1/R4 in deployment. Report canonical planner-action agreement, agreement with any teacher-cost minimum, teacher regret, margins/ties and physical command agreement. These explain what was learned without substituting for native outcomes.

The central uncertainty is substantial: the teacher’s decision depends on stochastic forecast samples unavailable to the student at deployment. Cross-entropy may learn a modal action and improve agreement while discarding important cost magnitudes. It may also improve bank imitation but fail under the student’s own visited states. Neither outcome by itself identifies a unique mechanism.

Informative outcomes are:

- **Positive:** recurrent deployed improvements over G, with low inference cost, and an advantage over the paired regression students. Prespecified tail gains with unresolved \(C\) would be a retained conditional capability, not proof of full objective improvement or R4 preservation.
- **Adverse:** improved imitation metrics without useful native service; improvement over S that merely returns to G; excessive switching, unfinished requests or degraded individual service. Close this fixed imitation purchase without an automatic new-bank, memory, loss or architecture sweep.
- **Inconclusive:** mixed seeds or uncertain deployment effects. Keep the variation visible; do not select the best fit or reinterpret the 96 student-world outcomes as 96 independent training replications.

The strongest ordinary objection is **G itself**: it already selects a teacher-cost minimum in 82.86% of bank contexts, completes all evaluation requests, and costs less than a student deployment. Improved classification accuracy, or merely beating the failed S endpoints, does not establish a useful learned capability.

The complete marginal cost is:

| Item | New D study |
|---|---:|
| New teacher acquisition | 0 |
| Fits / optimizer updates | 3 / 6,336 |
| Training context presentations | 403,200 |
| Training candidate rows | 1,612,800 |
| New-fit initial/final bank forward rows | 50,400 |
| New native missions / ticks | 288 / 345,600 |
| Maximum native forecast transitions, worker | 5,201,920 |
| Model initializations, worker | 3,840 |
| G query / nominal candidate-tick ceilings | 275,328 / 250,260,480 |
| Worker plus complete reader CPU forecast | **5–8 hours** |
| Additional acceptance/collection allowance | **Up to 1 CPU hour**, explicitly metered |
| Standalone elapsed-time planning range | Roughly 6–10 hours |
| Incremental artifact allowance | Roughly 4–6 GiB |
| GPU | 0 |

The three fits themselves should be around minutes of CPU, based on B06—not hours—but that is a small part of the complete purchase. The historical teacher cost remains **at least 1.952 CPU hours**, with its recorded coverage limitations; it is sunk marginally, not free historically. Do not add overlapping B05 totals twice.

The reader should bind initial/final weights, schedules, journals and endpoint outputs, and reconstruct the complete new native/R/G records. As in B06, such a reader does not establish historical gradient correctness by replaying optimizer updates. The new cross-entropy implementation needs its bounded numerical engineering check priced in acceptance work.

These two assignments have different estimands. B asks whether online planning computation can be allocated better without fitting. D asks whether a frozen planner’s decision capability can be acquired offline and deployed cheaply. D does not use B’s new selector or await its results. A remains the fixed-N8 two-stage value/scorer study; C remains the fixed four-opportunity anticipation comparison. I read their contracts, not unfinished scores.

Both studies should import source-bound frozen B capabilities, with new code in separately owned paths. They should not concurrently refactor the shared frozen implementation. Together they buy **499,200 new native ticks, three fits, approximately 13–20 CPU hours for workers and complete readers, or 16–23 CPU hours including the stated operational reserves**. Authoring/model-token expenditure and actual admitted memory/concurrency are not quantified by the existing run ledger and must be declared separately; I performed no node probe.

If only one purchase is affordable, choose B. D is the second, more uncertain investment. The reason to fund both is their distinct chance to develop an already observed planning capability—not the desire to occupy four DM slots. I make no novelty claim for either proposal.
<!-- B07_ROOT_ORACLE_ORIGINAL_END -->


**Stored original identity:** 16,113 UTF-8 bytes, SHA256
`350a4d05e48b9de3411067ecc9fde07c8df32c2520decefd6a8b1dc67aecbb6a`; the hashed text is exactly between the
markers, excluding the marker lines and its trailing LF. The coauthor reports
.364414 measured CPU-s of evidence/hash/exposure arithmetic, with other support
additional. This is historical constructive advice, not an accepted ranking.

Root subsequently conveyed the owner's explicit reassignment of the constructive
Oracle role to Jev ChatGPT Pro. The native Oracle consultation above is complete;
there is no second native Oracle round or additional adviser tier. Root owns
the not-yet-sent Pro question and cross-question selection. This DM continues
only the bounded source/evidence/cost construction below, without a Pro send,
new result purchase or RESEARCH prose edit while Root updates the shared question.
One applicable independent ResearchCritic review must cover the actual design
chosen for investment; this historical coauthor answer does not discharge it.
