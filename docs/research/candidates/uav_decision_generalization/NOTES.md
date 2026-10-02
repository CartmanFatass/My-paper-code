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
