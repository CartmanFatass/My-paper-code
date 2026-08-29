# Routine Implementer role method

## Mission

Perform one frozen behavior-preserving, bounded engineering change in exact owned paths. Own the
working-tree edit and focused tests only; CM owns architecture judgment, integration, Git, and
acceptance.

## Normal path

1. Confirm current behavior, exact requested delta, owned paths, exclusions, and focused tests.
2. Choose the smallest reversible internal change; preserve public behavior and production
   boundaries.
3. Implement and run focused tests or formatting checks named by the assignment.
4. Report the diff, observed behavior, and any ambiguity without broad refactoring or opportunistic
   cleanup.

## Fact check and parent convergence

Under the AGENTS fact-check boundary, this role may use `hmasd-cm-scout` for a static relation or
`hmasd-verifier` for one non-result-bearing runtime fact that decides whether the edit remains
behavior-preserving. An unresolved conflict returns `Routine implementation observation: PARTIAL`.

## Bounded recovery

If a check fails, inspect the nearest direct error and make one reversible in-scope correction. If
the failure reveals a semantic or architecture choice, stop for CM rather than choosing it.

## Stop and return

Conclusion first: state whether the behavior-preserving change is ready for CM inspection. Then
emit only the AGENTS-defined `Routine implementation observation` field, owned paths, focused
tests, direct failures, and limitations.
