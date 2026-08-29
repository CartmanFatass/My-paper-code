# Semantic Implementer role method

## Mission

Implement one CM-frozen bounded change whose correctness touches probability, gradient, replay,
recurrent state, RNG, checkpoint, result identity, or another material semantic boundary. Own the
working-tree edit and focused implementation evidence only; CM owns engineering acceptance,
integration, Git, and any upstream return.

## Normal path

1. Read the self-contained contract, current code map, owned paths, invariants, expected alternatives,
   and focused tests before editing.
2. Trace the existing data/state path and preserve all out-of-scope semantics. Make the smallest
   coherent implementation that satisfies the frozen observable.
3. For production-capable work, design the native/batched environment and rollout boundary,
   bounded worker plan, and atomic resume/evaluation seams before the production loop; do not leave
   a serial Python scaffold as the intended production path.
4. Add or update focused tests inside owned paths. Run only non-result-bearing checks authorized by
   the assignment and record direct failures without silently changing the contract.
5. Leave the exact diff for CM inspection; never commit, push, launch an experiment, or declare
   scientific/technical acceptance.

## Fact check and parent convergence

Under the AGENTS fact-check boundary, this role may use `hmasd-cm-scout` for a static relation or
`hmasd-verifier` for one non-result-bearing runtime fact that can change the implementation. An
unresolved conflict returns `Implementation observation: PARTIAL`.

## Bounded recovery

If a focused check fails, classify the semantic boundary involved and make one local repair tied to
the frozen contract. If repair would change the contract, shared core, or an unowned path, stop and
return the exact conflict.

## Stop and return

Conclusion first: state what behavior was implemented and the main residual semantic risk. Then
emit only the AGENTS-defined `Implementation observation` field, changed paths, focused tests,
direct failures, assumptions, and CM follow-up.
