# EGRCR-B1 construction and runtime-readiness technical acceptance

Owner: `direction:expressibility_gated_renewal_credit_relay` Code Project Manager  
Treatment: `EGRCR-B1-ORDERED-JOINER-WAITER-CREDIT-v1`  
Recorded: 2026-08-12 PT

## Acceptance conclusion

The isolated implementation and staged command surface are technically
accepted as ready for the first real calibration launch. No scientific result
or runtime artifact is accepted by this record: shared CPU release is still
pending, so neither calibration nor confirmation has run.

The implementation follows the owner-frozen clarification literally:

- every 128-row calibration/retained-confirmation root has 116 correct and 12
  flipped joiner cues, with parity-cell 14/2 versus 15/1 scheduling selected by
  prospective cue counter-key ranks;
- each confirmation root retains eight rows per
  `(type,lag,ordered_role,sampled_action)` cell at stored `p=0.5`;
- `T_e` is removed once only from the eligible later-joiner record;
- `INTACT` inserts `c*(a_e-p_e)*tilde_kappa_e`, while `BINDING-CUT` inserts
  the identically formed target from `pi(e)`;
- the cut is fixed-point-free and opposite-type within exact action,
  propensity, ordered-role and pre-action nuisance strata, and checks the raw,
  centered and action-conditioned target multisets; and
- all older-waiter GAE and all noneligible records remain ordinary GAE, with no
  debit or reverse relay.

## Accepted paths

- Source package:
  `experiments/candidates/expressibility_gated_renewal_credit_relay/`
- Retained calibration result:
  `docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_CALIBRATION_RESULT.json`
- Retained confirmation result:
  `docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_RESULT.json`

## Exact staged commands

Run calibration first:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.expressibility_gated_renewal_credit_relay --stage calibration --calibration-output docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_CALIBRATION_RESULT.json
```

Only when that command exits zero and the retained artifact reports every
frozen gate passed, run confirmation:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.expressibility_gated_renewal_credit_relay --stage confirmation --calibration-input docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_CALIBRATION_RESULT.json --result-output docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_B1_RESULT.json
```

The confirmation entry point independently rejects a wrong treatment, root
list, opportunity count, missing gate, or failed gate before constructing any
confirmatory batch.

## Resource and activity boundary

The static worst-case registered path accounts for at most 337,920 two-agent
physical ticks: 30,720 calibration fork ticks, 61,440 capped collection ticks,
61,440 confirmatory four-world label ticks, and 184,320 held-out evaluation
ticks. This is below the 1,000,000-tick cap. Expected execution is one CPU
worker, under two minutes and under 256 MiB RSS on the registered interpreter;
hard limits remain 15 minutes and 2 GiB RSS.

Question-relevant activity begins only after one calibration root has produced
legal paired JOINT and SOLO four-world quartets plus the waiter-action and
exposure record. The binding question is not exposed until all calibration
gates pass, every confirmation root supplies its exact 128-edge support, the
complete legal cut exists, and all three matched updates execute.

## Focused technical evidence

- Static source check: `pyflakes` passed for the isolated package.
- Syntax compilation passed for all five package modules.
- Package imports, frozen treatment import, argument-parser construction and
  the real module entry point's `--help` lifecycle all passed under
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.
- No tests were run or modified. No Git operation changed repository state.
- PID 20276 remained live at readiness acceptance; therefore no real
  calibration or confirmation command was launched.

Remaining runtime unknowns are the observed calibration gates, actual wall
time/RSS, confirmatory support before the 512-block cap, and the complete
scientific observable. Those belong to the scheduled real execution and do not
alter source readiness.
