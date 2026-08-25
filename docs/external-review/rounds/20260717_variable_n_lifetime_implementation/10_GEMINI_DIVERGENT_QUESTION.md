# Gemini Independent Divergent Implementation-Plan Review

You are an equal-standing divergent reviewer. Independently decide whether the
closed F0/F1 architecture can be implemented by the proposed plan without
quietly reintroducing fixed N, semantic identity, unowned probability factors,
invalid credit or an F1-only capacity advantage.

Read `00_REVIEW_BRIEF.md`, `01_SHARED_SOURCE_MANIFEST.md` and every source
allowed by `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`. The open GPT-5.6 Pro reviewer
will not see your response. Do not defer to it or make the final project
decision.

## Required response

Use these exact sections:

1. **Plan verdict** — exactly one of `ACCEPT_PLAN`, `MODIFY_PLAN`,
   `RETURN_TO_ARCHITECTURE` or `STOP_AT_F0`, with one-sentence rationale.
2. **Contract-to-code audit** — identify which existing interfaces can be
   reused, which fixed-N assumptions must be replaced and any contradiction
   between the plan and current code.
3. **Probability and event ownership** — audit the external gap/order process,
   K-way KEEP/SET action, applied-prefix replay and absence of missing policy
   likelihood factors.
4. **Credit and recurrent continuity** — audit per-owner `gamma^Delta`, macro
   GAE, update truncation, survivor/temporary-leave/rejoin hidden semantics and
   ragged low replay.
5. **F0/F1 causal isolation** — determine whether equal state-dict shape and
   initial-versus-working summary selection are sufficient to make the first
   comparison capacity-, data- and infrastructure-matched.
6. **Required plan corrections** — separate must-fix-before-code items from
   optional/deferred ideas. Give exact file/interface consequences; do not add
   a module unless it replaces a demonstrated necessity.
7. **Implementation sequence and stop point** — propose the smallest staged
   order that can reach focused engineering evidence and state exactly where
   work must stop before any environment or training.
8. **Strongest ordinary-MARL objection** — explain the strongest remaining
   reason F1 may collapse to F0 even if implementation is perfect.

Do not design an experiment, tune thresholds, revive R55/R53, add
environment-specific intrinsic reward, or authorize training.
