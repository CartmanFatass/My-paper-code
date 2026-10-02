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
