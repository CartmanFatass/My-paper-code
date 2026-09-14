# Independent B13 engineering review

Full direct App completion report from native /root/rv_s_h_rcle_b13, independent Sol/high
Reviewer, App01a09ee1-8f20-7c02-b486-3289b97b85d9, to the actual RCLE parent
App01a09e10-9d9f-7f82-87c0-d58cbe0c7618. The native final separately confirms this event.
No reviewer file or source edit was made. The following report is preserved as received;
DM acceptance and the synthetic-versus-native displacement clarification are in ENGINEERING.md.

---

REVIEW_COMPLETE event RCLE-B13-ENG-REVIEW-91811C61-20260914-01

Independent Sol/high read-only engineering review of preparation SHA 91811c61cff2617f0b691c793dd40a7df76c5bdb against baseline 2ef3096104d92345a191278316a9f421f808be73 is complete. No material finding was found.

Coverage: reviewed the B13 card and inherited B12/B11 contract, MARL_RUNTIME_ENGINEERING_SPEC general requirements, ENGINEERING_SCOPE_SPEC §§4, 5, 7.1–7.3, evidence-spec §§11.8–11.10, relevant RL/MARL scientific-reading passages, full changed policy/study/runner/test sources, reachable sampled/modal/Adam/publication path, commit metadata, and recorded ENGINEERING/TEST_RESULT/TEST_OUTPUT evidence. The 66-addition/6-deletion non-test source diff adds no prohibited §4 machinery; runner is 28 lines; commit says scope:none. git diff --check passed. Independently recomputed the fixed work law: 65,536 training + 2,560 evaluation = 68,096 episodes; 4,358,144 ticks; 2,128 native32 batches; 1,024 Adam steps; 16,384 sampled evaluation phase draws; 8,192 modal team decisions. Existing evidence records 24 focused synthetic/legacy/E01 tests passed in 11.24s with scratch removed; I did not repeat the full suite without a new concern.

Direct facts: policy.py registers one FP64 eta scalar only for learned greedy-anchored models and applies exp(eta)*log(q) inside the actual normalized sampled/modal law; eta0 consumes no RNG. The real full-Y score path passes all model parameters to Adam. study.py fixes B13 seed33/object/domain, runs panels in sampled-init/final1024/greedy/nearest/modal order, suppresses modal phase draws, saves scalar/model/optimizer metadata, reports separate sampled and modal D_g/D_n outputs, and measures zero parameter displacement across evaluation. Legacy B08–B12 paths omit the scalar and retain their state_dict/parameter inventory. The scientific-reading assumption is that the extra scalar changes the public-observation policy/optimization but not information access or reward; deterministic modal execution is a separate evaluation policy, so it is correctly reported separately and cannot isolate a pure learning effect.

Artifacts: reviewed docs/research/candidates/roster_consistent_latent_exploration/b13_learned_prior_20260914/{ENGINEERING.md,TEST_RESULT.json,TEST_OUTPUT.txt}; no review file or source edit was created. Unrelated untracked B10 transport artifacts were left untouched.

Remaining limits: no native B13/scientific-root run exists, so actual remote admission, full native trajectory/publication, runtime/RSS, learned eta trajectory, and scientific result remain unverified. The synthetic driver mocks native rollout/uniform/update and is interface/semantic evidence only. B11 SIG11 remains outside this change.

Next owner/action: RCLE DM resolves this no-finding evidence and owns technical acceptance. Any native B13 invocation remains dependent on the actual Portfolio direction decision and then the card’s exact-SHA remote-first admission/monitor path. This review is independent technical evidence, not execution permission or lifecycle disposition.
