# Restart handoff — 2026-07-26, seam after iteration 21

Read `AGENTS.md`, then this file, then `docs/project/CURRENT_WORK.md`.

Boundary: D7.S part B measurement is COMPLETE and committed (`91e1f08`,
report `46d7475`). The ep64 pooled result is decisive on the stable margin
(B_H +65.965, CI excludes zero; norm_stable −0.6155 against the −0.10
ceiling) and the branch is `SOURCE_NECESSITY_UNRESOLVED` because the flex
half of the gate rides the degenerate `set_flex` arm. All numbers and caveats
are in `CURRENT_WORK.md` under the `d7_s_ep64_*` keys. The 2026-07-25 note in
the previous handoff — "do not start a local H=1500 run" — is superseded: the
user reversed the remote ruling and the run has already completed locally,
sharded eight ways (loss-free; pooling proven).

Execution mode: authorized, user grant 2026-07-26, 19 of 20 iterations
remaining. Loop driver attached this session (hourly ScheduleWakeup fallback;
task notifications primary); it dies with the session — this file and
`CURRENT_WORK.md` are the continuity record.

Open deliverable (exactly one): the single External Pro round carrying the
four coupled items plus the new instrument caveats:

1. `set_flex` realization — definitionally ≡ `constructive`, so the gate's
   flex half cannot legally fire and `U*_flex` shares a term with `B_H`
   (D0 violation);
2. Delta mismatch — keep arms hold the whole window (150 check intervals)
   against D0's frozen Δ of one;
3. horizon structure — H=1500 now supports margin AND normalizer together;
   short horizons stay B_H-degenerate at practical budgets;
4. construction-time topology ignores seeds (wider than this audit);
5. caveats: probe QoS saturation 1.0 in 7/8 shards; `ratio_sign_stable=false`
   on the normalized-stable interval (diagnostic only, gate is point-based);
6. smallest supported claim from part B as it stands, and whether anything
   unblocks `D8`.

Exact next action: finish authoring
`docs/external-review/rounds/20260726_d7_s_part_b_flex_arm_and_instrument/20_PRO_OPEN_QUESTION.md`
as a conditional decision tree with a paths-only evidence allow-list; run the
mandatory adversarial pre-send pass (`hmasd-contract-griller`); repair; commit
and push the stage commit; transport via `$hmasd-review-round` to the
registered conversation. Do not resend any fence already recorded as sent.
