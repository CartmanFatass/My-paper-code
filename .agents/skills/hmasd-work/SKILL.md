---
name: hmasd-work
description: Use when a Superpowers-managed HMASD change touches core algorithm, trainer, runtime, replay, dynamic roster, credit, probability, clocks, masks, checkpoints, collectors, or scientific-evidence semantics.
---

# HMASD Work

## Overview

Use this Skill as the HMASD domain overlay. Superpowers owns the generic
development lifecycle: design, planning, test-first implementation, task
reviews, final verification, and completion. Do not create a second harness,
brief, task-state vocabulary, or reviewer workflow here.

## Establish the Project Boundary

Keep the current root task as active controller. Read `memory/CURRENT_WORK.md`
first. Read `memory/ALGORITHM_PRINCIPLES.md` before changing an algorithm,
reward, or experiment design, and read the active
`memory/IMPLEMENTATION_PLAN.md` section before staged core work.

The active controller alone decides the causal route, architecture,
reuse/replacement/deletion, data and gradient flow, scientific evidence
boundary, experiment authorization, root memory, and Git integration. An
implementer may make engineering decisions inside that frozen design but must
return `BLOCKED` instead of inventing a mechanism, changing the estimand, or
expanding scope.

## Use the Superpowers Lifecycle

- **REQUIRED SUB-SKILL:** Use superpowers:brainstorming for a new design that
  is not already covered by explicit user approval or an accepted HMASD design.
- **REQUIRED SUB-SKILL:** Use superpowers:writing-plans for multi-step work.
- **REQUIRED SUB-SKILL:** Use superpowers:test-driven-development for every
  implementation or bug fix. Observe RED before changing production files.
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development when
  subagents are available; otherwise use superpowers:executing-plans.
- Follow Superpowers task-review cadence and final review. Add no separate
  HMASD review layer or review state machine.
- **REQUIRED SUB-SKILL:** Use superpowers:verification-before-completion before
  any completion, commit, or push claim.

Existing HMASD authorization satisfies the corresponding approval boundary;
do not ask again merely because the lifecycle advances. Work in the active
controller workspace. Do not create a worktree unless the user explicitly
requests one.

## Require One HMASD Contract

Put one `HMASD Contract` section in the active implementation plan. It must
state only the task-specific facts needed to prevent semantic drift:

- causal or engineering goal and authorized evidence boundary;
- reused, replaced, deleted, and added components;
- exact files, symbols, tensor shapes, ordering, and collector path;
- data/state ownership and recurrent-state lifecycle;
- gradient owners, detach boundaries, reward scale, advantage, and credit;
- probability factorization, RNG, replay, masks, clocks, and checkpoints;
- preserved interfaces, dirty-worktree boundary, and explicit non-goals.

Do not create `.codex/collaboration` briefs or a parallel plan. Keep the
persistent staged plan in `memory/IMPLEMENTATION_PLAN.md`.

## Preserve Scientific Meaning

Test-first implementation proves the code contract, not the algorithm claim.
Use the next authorized evidence-bearing experiment to judge capability and
stability. Do not add a separate scientific-verification stage, reinterpret a
valid negative result as an engineering rescue, or launch smoke/formal training
without `$hmasd-experiment` authority.

Reviewers inspect implementation fidelity, probability, gradient, RNG, replay,
clock, checkpoint, collector, stability, scope, and code quality. They do not
choose the algorithm, authorize experiments, edit root memory, or issue the
scientific disposition.
