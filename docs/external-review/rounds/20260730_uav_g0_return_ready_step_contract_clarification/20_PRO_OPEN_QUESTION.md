# UAV G0 return-ready step contract clarification

Answer only the frozen contract question below. Do not redesign G0, change
geometry, metrics, confidence rules, controls, episode counts, or protected
fields. Use the GitHub connector and only the allow-listed paths in the shared
manifest. Return one exact disposition token and the complete ASCII addendum
required by that token.

## Exact Code PM diagnosis

The G0 implementation is uncommitted and has not run a scientific experiment.
The prior branch-aware replay repair uses the frozen pre-action service/history
predicate to derive the first causal return-ready step R. For episode 0 with
selected candidate stage/+1, event onset is step 191 and rejoin is step 272.
The implementation's short-window replay gives stored_R=273. The frozen
addendum used by the assignment asserts R=280 and requires all steps through
279 to remain identical before the selected-reserve target may switch.

The first code-level mapping defect was also identified: a reconstruction helper
indexed internal-order safety records using a storage row. Correcting that
mapping reconstructs R=273, so it does not remove the deeper 273-versus-280
contract conflict. The current pre-action predicate is true at step 273 because
the internal owner row is active/at-primary and the pre-action weakest-hotspot
service value is 1.0. Code PM cannot add a seven-step delay or alter service
semantics without a scientific contract decision.

No source commit, formal run, nonformal run, bootstrap, or iteration result
exists for this attempt. The five G0 implementation paths remain uncommitted
and preserved.

## Required decision

Choose exactly one policy, preserving every previously frozen G0 field and
claim boundary:

1. `G0_RETURN_READY_STEP_DISPOSITION=KEEP_CAUSAL_R_273`
   Freeze that the causal return-ready step is the first pre-action step at
   which the registered service/history predicate is true, namely R=273 for
   this episode. State the exact predicate and provide the required mechanical
   addendum changing the episode-specific R assertion from 280 to 273, with no
   artificial delay and no service-semantic change.

2. `G0_RETURN_READY_STEP_DISPOSITION=REVISE_PREDICATE_TO_R_280`
   Freeze that R=280 is required and identify the exact frozen causal input or
   predicate term that makes the predicate false at steps 273-279 and true at
   280. Provide the complete mechanical addendum, without inventing a delay,
   changing service semantics, or using future information.

3. `G0_RETURN_READY_STEP_DISPOSITION=INVALID_REALIZATION_REQUIRED`
   Freeze that the current realization and episode-specific assertion cannot
   both satisfy the registered causal contract. State that no INFEASIBLE,
   ORACLE_ONLY, UNDERPOWERED, or IDENTIFIED result is admissible until the
   contract is corrected and reimplemented.

If neither R=273 nor R=280 can be frozen exactly without violating the current
information boundary, choose INVALID_REALIZATION_REQUIRED.

## Required response format

Return one ASCII-only response with these headings, in this order:

`G0_RETURN_READY_STEP_DISPOSITION`
`G0_RETURN_READY_STEP_PREDICATE`
`G0_RETURN_READY_STEP_ASSERTION`
`G0_RETURN_READY_STEP_INFORMATION_BOUNDARY`
`G0_RETURN_READY_STEP_FAILURE_SEMANTICS`
`G0_RETURN_READY_STEP_PROTECTED_FIELDS`

The first heading must contain exactly one of the three tokens above. Include
the exact predicate, the exact R assertion or invalidity rule, and the complete
mechanical addendum required for Code PM. Do not return an implementation
commit, a compute authorization, or a learned/formal result.
