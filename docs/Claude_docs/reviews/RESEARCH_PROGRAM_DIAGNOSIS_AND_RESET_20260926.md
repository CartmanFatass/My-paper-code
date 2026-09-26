# HMASD research programme: diagnosis and reset — 2026-09-26

Author: Claude Code (Fable 5.1), at the owner's request, after reading the Codex Root report
`docs/Claude_docs/inbox/HMASD_RESEARCH_STATUS_WORKFLOW_AND_FAILURE_MODES_20260926.md`.
Read-only: nothing launched, no direction record edited, 0 fits. Read from `main` at `15abf5f66`
(working tree), the node `hmasd-wsl-node` was queried only for `uptime`.

Provenance the reader should weigh: Claude drafted the operating constitution and the role bodies
on 2026-09-16, and wrote the 09-14 and 09-22 reviews that this document audits. Where those
contributed to the problem, this review says so (section 4.3 and 5).

**中文摘要。** 瓶颈不在算法，也不在 Codex 或 Claude 的能力，而在三件事：(1) 宿主选错了两个月，
S1 是静态、稠密奖励、无耦合的任务，"解开 k / 解开 N" 在那里不可能显出价值，最后一周更漂到了一个
两智能体、总算力 121 秒的玩具宿主（CrossingHost）；(2) 仪器分辨率不够，单种子探索加三区组确认，
在已测得的种子标准差 .055–.08 J 下，任何 < .15 J 的真实效应都必然读成"不确定，结束投入"，
五天关掉十二个方向就是这台机器的正常输出；(3) 工作流把一次 100 分钟的训练包进一天的文书，
宪章十天改了 25 次，一周 60 多次 Pro 咨询，95% 的提交只碰文档；八天里可计量的训练总共约 73 小时，暂停以来 GPU 节点空转。
被埋没的最重要科学事实：普通局部循环 PPO（LOCAL1）与完整 HMASD 在 S1 上互无可靠优势
（N8 时 HMASD 落后 .014 J，N4 领先 .027 J，N6 混合）。这就是 09-14 评审要求的"层次结构前提检验"的答案，
但没人把它当作答案。建议：以 S7（能耗、充电站争用、移动用户、无人机临时失效）为唯一冻结宿主，
先做基准套件（启发式 / LOCAL1 / 中央快照 flat / 固定 k 的 HMASD，5 种子，学习曲线），
第一篇论文是基准 + 基线 + 一个有差距处的结构化方法；充电往返天然是变时长宏动作、充电离线天然是
变人数，所以"HMASD 为基础"与"UAV 场景为起点"在 S7 上不是二选一。工作流只删不加：冻结宪章与
方向 30 天，一个 DM 跑固定队列，Pro 与独立评审只在计划/论文主张边界出现，结果表 + 曲线取代散文数字。
需要 owner 拍板的六项见第 8 节。

---

## 1. Verdict

The programme is not failing because the ideas are bad or the models are weak. It is failing
because three layers were set up so that success was unlikely and failure was unreadable:

1. **The host.** From 09-18 to 09-25 every learning result came from Scenario 1: static users,
   dense per-tick reward, fixed roster, no events. Neither "untie k" nor "untie N" can matter there,
   and the 09-14 and 09-21 reviews said so. On 09-25 the programme then moved its main line to
   CrossingHost, a two-agent finite-model toy whose whole B03 batch (six fits) cost 121 seconds of
   compute and produced a +0.5% effect. Four independent contexts (DM, ResearchCritic, Pro, Root)
   endorsed the next batch there. None asked whether the host could answer a UAV question.
2. **The instrument.** Exploration is one training seed per arm; confirmation is three blocks read
   with a df=2 interval. The measured seed SD on S1 is .055–.08 J. Under that noise a true effect
   below about .15 J is arithmetically guaranteed to read "inconclusive" at n=3 and "inside noise" at
   n=1. B15 is the textbook case: three positive blocks (+.087/+.089/+.038 J), lower CI bound
   −.0000079, verdict "not established, investment ended". Twelve directions were opened after
   09-21; ten are archived, one is in reserve, one is paused. Three confirmations were run on
   UAV hosts (B15, B20, C01) and none was established; the one prewritten rule that passed
   (PPC B02) is on the two-agent toy. The loop is a
   machine that converts underpowering into defensible closure, and its language makes closure look
   like rigour. My 09-14 review (R3) predicted this mechanism; the fix was not adopted.
3. **The workflow.** The pipeline (DM → L0 → Implementer → engineering Reviewer → launch → wait →
   independent numerical reading → ResearchCritic → Pro → Root portfolio review → archive) turns a
   100-minute fit into a day of documents. Since the constitution was adopted, 95% of commits touch
   only documents; the constitution itself was amended 25 times in ten days; six project reviews and
   75 archive files were produced in six days; more than 60 Pro consultations were sent in one week. The
   compute node has been idle since the pause; the run summaries account for about 73 measured
   hours of training over the same eight days, part of it on the CPU host. The structure has no role that can execute a strategic
   change (host, benchmark, seeds); each review produces the next batch instead.

The single most consequential scientific fact in 6.9 MB of notebooks is buried and unlabeled:
**on Scenario 1, a plain local recurrent PPO (LOCAL1) and full HMASD (H6) show no reliable advantage
in either direction** (three blocks at 360k steps: H6 − LOCAL1 at N8 mean −.014 J, at N4 +.027 J,
N6 mixed; fresh-world replay confirms the N8 sign). That is the hierarchy-premise test the 09-14
review asked for as R1, obtained by accident in ACG B16/B17 and never recognized as such.

**Recommendation in one sentence:** stop opening directions, freeze one UAV host family (Scenario 7
and the unused service-restoration environment), build a five-seed baseline suite with learning
curves as the first deliverable, and let the structured methods (HMASD skills, variable-duration
commitments, roster handling) compete only where the suite shows a gap. Sections 6–8 give the plan,
the costs and the six decisions only the owner can take.

## 2. The numbers behind the verdict

| Quantity | Value | Source |
| --- | ---: | --- |
| Commits 2026-08-25 → 09-26 / touching only docs, skills, role bodies or tools | 5,721 / 5,334 (93%) | `git log --name-only` |
| Commits since the constitution (09-16) / docs-only | 596 / 564 (95%) | same |
| Constitution amendments 09-16 → 09-25 | 25 commits | `git log -- docs/project/OPERATING_CONSTITUTION.md` |
| Project reviews / archive files 09-21 → 09-26 | 6 / 75 | `docs/research/archive/` |
| Direction-level Pro consultations (sections "Pro question") / of which 09-21 → 09-25 | 67 / 60 | `grep '^## Pro question'` across NOTES |
| NOTES lines added 09-18 → 09-25 / RESEARCH.md + archive lines added | ≈78,000 / ≈29,700 | `git log --numstat` |
| Notebook bytes: total / largest (agent_count) / S7 | 6.9 MB / 1.56 MB / 0.96 MB | `wc -c` |
| Directions opened since 09-21 / archived / reserve / paused | 12 / 10 / 1 / 1 | RESEARCH.md tables |
| Confirmations run on UAV hosts / established | 3 (B15, B20, C01) / 0 | CLAIM notes |
| Confirmation whose prewritten rule passed | 1 (PPC B02, two-agent toy) | PPC CLAIM |
| Wall time of one 360k-step S1 fit (CPU, 4 threads) | ≈100 min (5,988 s) | ACG run summaries |
| Wall time of one 180k-step S7 fit at H3000 | 84–102 min | S7 B09 summary |
| Whole PPC line, 20 fits, B01–B03 | ≈17 min of compute | PPC NOTES/CLAIM |
| Measured compute in run summaries that record wall time, since 09-18 | ≈73 h across 93 runs | `wall_seconds` fields |
| Node `hmasd-wsl-node` at 18:05 on 09-26 | load 0.00 (idle since the pause), up 8 d 22 h | `uptime` over ssh |
| Measured seed SD on S1 (five D1280 blocks / paired difference) | .055 / .074 J | FSD B01/B02 |
| Detectable effect at n=3 blocks with that SD, roughly | ≥ .15 J | 09-14 review §5.1, B15 |

The compute column and the documentation column are the owner's frustration quantified: about
73 measured hours of training produced about 108,000 lines of prose, 70 adviser answers and 25
rule changes, and the node has stood idle since the pause while the latest reviews were written.

## 3. What has actually been established (defensible claims)

1. HMASD reproduces on Alice-and-Bob (R41B, July). Unchanged.
2. On Scenario 1 at 360k steps, a competent flat learner exists (LOCAL1: shared recurrent PPO,
   local observations, central critic; third-block J45 .49 at N6, .42 at N8), and full HMASD has no reliable
   advantage over it: N8 −.014 J (three blocks; fresh worlds +.026 J for LOCAL1), N4 +.027 J for
   HMASD, N6 mixed. The earlier "hierarchy beats flat" numbers (FSD D1280 vs CF, +.29 J) were
   against a control that never learned (CF J45 .14–.29). So the hierarchy premise on the dense
   static host is answered: no measurable benefit at this budget, an N-dependent tie.
3. Mixed-count training (B19/B20) and mixed-layout training (A2/C01) did not reproduce their
   development-pair positives; both remain inconclusive at n=3 and n=5 with adverse point estimates.
4. On Scenario 7 at H3000, the learner is now competent: from a common initialization (J 609) the
   ordinary arm reached J 986 and QoS/step .34 at 180k steps (B09). Auxiliary/feedback training,
   station-continuity rules and guarded continuity changed recovery counts but not complete J
   (B09 −82 J for feedback training; B10 −46 J; B11 −3 J). A heuristic upper reference exists in
   code (`estimate_heuristic_qos_feasibility`) but has never been reported: the one S7 summary that
   mentions the check (`b07_of_a01`) records it disabled, and no S7 notebook entry reports it.
5. On CrossingHost, weighted imitation of a planning teacher beats plain behaviour cloning by
   +11 to +22 jobs per 256 contexts (B02, sign confirmed in five blocks) and by +14/+17 jobs on a
   fixed archive (B03, +0.53% of completions). Correct, tiny, and unconnected to any UAV decision.
6. Negatives that are real but narrow: dense/query encoders (LOE), cap-10 joint duration (JDSL),
   goal-conditioned aggregation (GCEA), skip-slow-channel timing (C2). Each rests on one training
   seed per arm and constrains only its recipe.

Nothing above is a publishable positive. Items 2 and 4 are the two assets a paper can be built on:
a competent flat baseline and a coupled UAV host where the learner works.

## 4. Diagnosis by layer

### 4.1 Questions and scope

"Untie k and untie N in HMASD" is a general-MARL contribution aimed at NeurIPS-class venues. It
needs a benchmark on which fixed-k or fixed-N learners demonstrably lose. The programme never
built or borrowed one; it tested the axes on S1, where nothing changes in time and the roster is
fixed, then on toys built per direction. That is why the owner's suspicion is correct: the questions
as posed were too ambitious *for the hosts used*, not too ambitious in themselves.

The drift is dated. 09-24: the adopted plan still names S1/S7 comparisons. 09-25: the A/B/C replan
moves the priority to "compress planning into a history policy" on CrossingHost. 09-26: Pro
(11,554 characters), the ResearchCritic (MATERIAL_DISSENT on attribution, not on the host), and
Root all choose six more fits there. The report you received is honest that "the project-level
contribution remains to be reviewed"; what it does not say is that the host makes the review moot.

The owner's two framings ("HMASD as foundation" vs "UAV scenario as starting point") are a false
choice once the host is Scenario 7. S7 natively contains both axes: a charging trip is a
variable-duration macro-action (untie k), and UAVs offline for charging or S4 failures are roster
changes (untie N). This was the 2×2 argument of my 09-21/09-22 notes (RECORDED); the two
preconditions that were missing then are now met: the learner is competent at H3000, and a
matched-information flat baseline exists (LOCAL1). What is still missing is the heuristic upper
reference and a measured seed SD on S7.

### 4.2 Methodology and instrument

- Exploration at one seed per arm, then closure. LOE, JDSL, GCEA, DBT, FMDV closed on a single
  training instance per arm. The constitution allows single-seed exploration; it does not say what
  to do when the result lands inside noise, so the default became "investment ended".
- Confirmation at n=3 blocks with a df=2 t-interval. B15 (n=3) and B20 (n=3) were inconclusive
  or adverse exactly as the seed SD predicts; C01 at n=5 still straddled zero. A variance-derived
  rule (effect > 2× measured seed SD, five seeds) was recommended on 09-14 and not adopted.
- No learning curves as a standard artifact. Endpoint J at rollout 45 decides; the 09-22 review
  showed H6 vs SET flips sign between rollout 30 and 45.
- Every direction built its own baseline and evaluation panel (SET, LOCAL1, F, U, O, CF …) and its
  own world seeds, so baseline seeds never accumulate across directions. The shared S1 reference
  recipe proposed on 09-22 (DECIDE-1) was not adopted.
- Package comparisons everywhere, component attribution nowhere; the notebooks then spend
  thousands of lines saying so.

### 4.3 Workflow and the DM structure

The constitution says "roles relieve work; they are not departments". In practice a DM session
loads roughly 100 KB of instructions (constitution 36 KB, DM body 17 KB, the two method skills
44 KB; about 150 KB when the other skills load) and runs
a seven-role pipeline per batch. Three consequences follow from the record:

- **Cadence mismatch.** Decisions are made at LLM speed (a portfolio review per day, ten Pro
  consultations per day), fits take 100 minutes, and the owner can read perhaps one page a day.
  The loop therefore optimizes what it can produce fastest: defensible documents.
- **Parallel independent DMs destroyed comparability.** By design the DMs cannot talk; each built
  its own baseline and panel; the Root layer added reviews rather than a shared benchmark.
- **No owner of strategic change.** Every external review since 09-14 asked for the same three
  things (a host with coupling, a shared benchmark with learning curves, five seeds with a
  variance-derived rule). The adoption audit:

| Advice | Date | Outcome |
| --- | --- | --- |
| R1 headroom: flat MAPPO vs HMASD on the UAV host, 5 seeds, curves | 09-14 | Answered by accident (ACG B16/B17, 3 blocks, no curves), never recognized |
| R2 one external benchmark per axis, retire per-direction hosts | 09-14 | Not adopted; 12 new directions, 4 host families in 5 days |
| R3 five seeds, effect > 2× seed SD, abolish fixed MEI | 09-14 | Not adopted; n=3 blocks with df=2 intervals |
| R4 two directions, slow cadence, owner selects runs | 09-14 | Inverted: 12 directions, 6 reviews in 6 days |
| DECIDE-1 shared S1 reference recipe + panel, SET as flat arm | 09-22 | Not adopted; LOCAL1 later superseded SET inside one direction only |
| Seeds concentrated on ACG H6 vs SET | 09-22 | Adopted as B15 at n=3 → inconclusive, then comparator changed |
| S7 competence/reference phase before more auxiliary fits | 09-22 | Half adopted: H3000 gave competence; upper reference still never reported |

Claude's share: the constitution and role bodies of 09-16 are mine, and they left the Pro triggers,
the critic role and the "one result-bearing study per DM" rule broad enough to generate this
cadence. My 09-22 advice to concentrate seeds on H6 vs SET accepted n=3 as the minimum; it should
have insisted on five and on the variance rule. The 09-21 joint-skills recommendation became
complementary_skill_learning B01–B09 in three days with two sign reversals; that line churned too.

This is not a Codex-versus-Claude question. The DMs' notebooks are careful, numerically verified
and honest about limits. The structure, not the model, decided that the next batch is always a
nearby comparison on the current host.

## 5. Answers to the seven questions in the Codex report

1. **Which repeated pattern has direct evidence?** Two: underpower-then-close (B15's lower bound
   −.0000079; single-seed closures of LOE/JDSL/GCEA/DBT/FMDV; B20 adverse at n=3) and host
   mismatch (S1 for k/N; CrossingHost for UAV). The report's diagnosis ("a valid local comparison
   keeps replacing the project question") is correct but downstream: without a fixed benchmark
   and host with coupling, no local comparison can connect to the project question. The report is
   fair to the accumulated work; it undervalues the one strategic fact it contains (item 3.2 above).
2. **UAV goal vs PPC.** PPC is a detour; nothing on CrossingHost changes a UAV decision. Keep the
   original goal and change the host; on S7 the goal and the UAV scenario coincide (4.1).
3. **One problem to prioritize.** "On a coupled UAV host, does any structured coordination (HMASD
   skills, variable-duration commitments, explicit roster handling) beat a competent recurrent PPO
   and a heuristic reference, by how much relative to seed SD, and on which subtask?" Strongest
   simple alternative: LOCAL1 with matched exposure. Existing material is insufficient to choose the
   *method*; it is sufficient to choose the *host and baseline suite*, which is the point.
4. **PPC B04.** Do not run. It cannot change any project-level choice; its remaining local value is
   below the attention it costs. Archive with the B03 result; the code and prospectus are preserved.
5. **Is the independent reviewer sufficient?** Not as structured. Four contexts endorsed a toy host
   because all four received the same candidate list and the same framing. What changes judgement
   is an external frame: a frozen benchmark, a results table the owner reads, and independent
   review at paper-claim boundaries rather than per batch.
6. **Keep / delete.** Keep: sha-pinned launches and admission, common random numbers and matched
   world seeds, raw-output retention, per-world loss retention, technical-failure quarantine,
   engineering review for core changes. Delete: per-batch Pro consultation, per-batch critic pass,
   archive snapshots per plan change, manual transcription of manifests, notebook entries longer
   than a page, daily portfolio reviews, three parallel DMs with private baselines.
7. **What improved since 09-14/09-22, what repeats.** Improved: matched-information flat baselines
   exist (SET, LOCAL1, F), confirmations use fresh blocks, the entry-mask defect was fixed in all
   arms, S7 is competent at H3000, raw evidence is retained, technical failures are recorded as such.
   Repeats: single-seed closures, per-direction hosts and panels, direction turnover, documentation
   volume, rule churn, and drift away from the UAV host.

**On the report itself**, as it asked: it is accurate and unusually honest about Root's own choices,
its four-way separation of outcome types (adverse, imprecise, technically incomplete, narrow
positive) is right, and its proposed next deliverable ("state the one scientific question first") is
the right instinct. Its limits: it stays inside the frame (PPC as main line, remedy as another Root
document), it never questions the host or the seed instrument, it does not quantify process cost
although Git contains it, and it treats the MATERIAL_DISSENT cycles as evidence that review works
when the same cycles approved the toy.

## 6. Options and recommendation

| Option | What it is | Time to a first draft | Risk | Fit with owner's aims |
| --- | --- | --- | --- | --- |
| A. HMASD-methods programme (MARL venue) | Build or borrow a benchmark where fixed k/N provably lose; then the mechanism | 3–6 months | High; a positive is not owed | Matches original ambition; nothing publishable until the benchmark exists |
| B. UAV subproblems (wireless/applied venue) | One frozen S7-class host, 2–3 subtasks, baseline suite, one structured method | 4–8 weeks | Moderate; publishable as benchmark + analysis even if the structured method loses | Matches "several well-motivated subproblems" |
| C. Hybrid (recommended) | B first on S7; A's mechanisms enter only where the suite shows a gap, on the same host | B's timeline for paper 1; A follows | Moderate | Keeps HMASD alive as a candidate, not as a premise |

**Recommendation: C.** The reasoning is the adoption audit: every path that starts with a mechanism
has ended in closure; the path that starts with a benchmark has never been tried and is the one
deliverable the field also lacks (the 2026 UAV-MEC benchmarking paper and the 2025 coverage papers
found in a quick search use bespoke simulators; the search found no shared open benchmark that
combines charging contention, backhaul relay and outages).

**Venue first.** A wireless venue (TVT, IoT-J, TCCN) values a convincing system model, strong
heuristic and learned baselines and multi-seed curves; algorithmic novelty can be modest. A MARL
venue values the reverse. The choice defines what "publishable subproblem" means and should be
made before the first fit (DECIDE-1).

### Subproblem tracks on the frozen host (marked per the owner's rule)

| Track | Host | Status | What the paper would claim |
| --- | --- | --- | --- |
| T1 Energy/charging coordination: chargers of capacity 1, return risk, shared slots | S7-S2/S3, H3000 | TRIED as fixed rules (B05–B11), RECORDED as learning (B09); **NEW** as a benchmark task with baseline suite, curves, and charging trips treated as variable-duration commitments | Whether structured commitment/skill assignment beats recurrent PPO and a heuristic on service–risk |
| T2 Coverage under RPGM user mobility with fleet churn from charging exits and S4 failures | S7-S4 | RECORDED (env exists; variable_n_fleet_churn old and technically incomplete); **NEW** on S7 | The untie-N question in its natural form: survivor policies under a changing roster |
| T3 Outage restoration on real demand traces | `envs/uav_service_restoration` (Milan traces, LP scheduler, scripted controllers) | **NEW in execution**: built, zero fits, data not yet validated | A realistic restoration benchmark; learned vs scripted controllers |

Baseline suite for every track: heuristic upper/lower reference, LOCAL1 (recurrent PPO, local
observations), SET (central-snapshot flat), HMASD fixed k=10; later the D2 interruption variant as
the untie-k candidate. Five seeds, learning curves, one evaluation panel per task, seed SD measured
before any confirmation rule is set.

### First four weeks, sized to the actual node

| Week | Work | Cost |
| --- | --- | --- |
| 0 | Freeze: no new directions, no constitution edits, PPC B04 archived. Write the one-page benchmark spec for T1 (host preset, horizon, panel, metrics, seeds). Report the heuristic feasibility reference on the T1 panel (0 fits). | 1–2 days, 0 fits |
| 1 | T1 baseline suite: LOCAL1, SET, HMASD-k10 × 5 seeds at 180k/H3000 | 15 fits ≈ 25 h serial on the RTX 4070 (two concurrent if memory admits) |
| 2 | Read curves; measure S7 seed SD; decide whether exposure must grow (extend to 540k where curves have not plateaued). Start T3 data validation in parallel (CPU, 0 fits). | ≤ 15 more fits |
| 3–4 | The first structured candidate on T1 only where the suite shows a gap ≥ 2× seed SD to the best baseline; otherwise T2. Draft the benchmark section of paper 1. | ≤ 15 fits |

Do not run the full 3-track grid first; 45 fits at 5 h would be ten node-days and would reproduce
the old pattern of buying breadth before resolution.

## 7. Workflow changes: delete, do not add

Within the current constitution (Root or the acting DM can do these today):

1. One programme, one host family, one queue. Root either dissolves into the single DM or does
   nothing but keep the queue. No direction is opened for 30 days.
2. One results table (JSON in Git, per the CSV-is-ignored rule) and learning curves become the
   primary artifact; a notebook entry is at most one page and points at the table.
3. Never archive on a single seed. Results inside noise go to an "undetermined" bin in the table;
   the loop moves on without calling it a negative or a closure.
4. Pro is reused by default; the four section-5 triggers are interpreted at plan and paper-claim
   boundaries, not per batch. ResearchCritic runs on paper claims and on the benchmark spec, not
   on every result.
5. Engineering review stays for core code and launch/admission code; direction-local runners get
   author checks plus the existing tests.
6. Report the missing references before any new comparison: S7 heuristic feasibility on the fixed
   panel, and the S7 seed SD.

Requiring owner amendment (section 7 of the constitution):

- Freeze the constitution for 30 days; the next amendment is a single consolidated one.
- Section 2: collapse Root/DM for this programme into one executing session; drop the
  three-track ceiling to one track until paper 1 exists.
- Section 5: Pro consultation at plan boundaries and paper claims only (roughly once a week).
- Section 8: confirmation is five fresh seeds per arm and an effect larger than twice the seed SD
  measured on that host; "three blocks with a df=2 interval" is retired.
- Section 4: the results table plus learning curves is the index of results; RESEARCH.md keeps the
  question, host, queue and pause, and retires nothing per batch.
- Owner cadence: one 30-minute reading of the table and curves per week, with a stated default
  (continue the queue) if the owner is absent, so no wait is introduced.

## 8. Decisions only the owner can take

- **[DECIDE-1] Venue class:** wireless/applied venue first (recommended) or MARL venue.
- **[DECIDE-2] Host freeze:** Scenario 7 family plus the restoration environment as the only hosts;
  Scenario 1 retired to sanity checks; CrossingHost archived with its results.
- **[DECIDE-3] Thirty-day freeze** on new directions and constitution amendments.
- **[DECIDE-4] Who executes:** one Codex DM running the queue, or the Claude session as the DM
  under the existing "Claude is one direct DM" rule; Root dissolved for the period.
- **[DECIDE-5] Cadence amendments** to sections 2, 4, 5 and 8 as listed in section 7.
- **[DECIDE-6] PPC B04:** archive unlaunched (recommended) or run once and then archive.

With DECIDE-2 and DECIDE-4 answered, the T1 benchmark spec and the heuristic reference can be
produced in a day and the first 15 fits can start on the idle node.

## Appendix A. Sources read

`docs/Claude_docs/inbox/HMASD_RESEARCH_STATUS_WORKFLOW_AND_FAILURE_MODES_20260926.md`;
`docs/project/OPERATING_CONSTITUTION.md`; `docs/research/RESEARCH.md` (background 1–8, tables,
plan, routing); `docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md`,
`2026-09-25/RESEARCH-decision-learning-adopted.md`, `2026-09-26/RESEARCH.md` (question, full Pro
answer, dissent, adoption); PPC NOTES (B01 contract, B03 complete, B04 prospectus, handoff) and
CLAIM; ACG B20 CLAIM and B16 complete section; spatial C01 CLAIM; S7 NOTES B09 complete and the
final approach decision; `.codex/agents/hmasd-direction-manager.toml`,
`hmasd-research-critic.toml`; `.agents/skills/hmasd-scientific-tools/SKILL.md`,
`hmasd-research-engineering/SKILL.md`; `envs/pettingzoo/scenario1.py` reward,
`envs/pettingzoo/relay/energy_aware.py`, `envs/uav_service_restoration/README.md`;
`docs/research/baselines/scenario_1/BASELINE_SET_RESULT_20260904.md`; the two earlier Claude
reviews of 09-14 and 09-22; run summaries under `runs/` for wall time, admission timestamps and
the S7 feasibility flag; `git log` for commit, amendment and line counts.

External anchors (quick search, not a literature audit): a 2026 benchmarking paper on MARL for
UAV-assisted MEC (https://doi.org/10.3390/technologies14040202); congestion-aware CTDE-MAPPO for
swarm trajectory planning (https://arxiv.org/abs/2606.16386); multi-UAV coverage with
power-efficient connectivity, PIMRC 2025 (https://arxiv.org/html/2503.23669v1); variational
offline multi-agent skill discovery, IJCAI 2025 (https://www.ijcai.org/proceedings/2025/0538.pdf);
inter-agent relative representations for multi-agent option discovery
(https://arxiv.org/pdf/2512.24827); HMASD (https://proceedings.neurips.cc/paper_files/paper/2023/hash/c276c3303c0723c83a43b95a44a1fcbf-Abstract-Conference.html).

Not verified here: the S7 heuristic reference values themselves, the S7 seed SD, the state of the
Milan trace preprocessing, and whether the 4070 admits two concurrent 180k fits.
