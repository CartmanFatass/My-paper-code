"""UCOPE prospective registration: freeze the replication before it runs.

WHY THIS EXISTS
---------------
FOLR could not execute a branch without an externally supplied approved digest;
`execute_registered.py` raises before any kernel is observed if the running
registration differs from the one External Pro approved.  UCOPE had no such
object.  It had good provenance -- commit, dirtiness, per-file digests, and the
run arguments written into the artifact -- but provenance is a *record of what
happened*, not a *refusal to do the wrong thing*.  Nothing said no.

Two defects followed directly from that gap, and neither was subtle:

1. ``run_arm``'s default was ``iterations=120`` while the registered run used
   300, so the first cross-seed replication trained every arm to 40% of budget
   and produced eight plausible numbers describing the short budget rather than
   the seed.  Nothing raised.
2. ``ledger_seed = 20_260_808`` equals ``20_260_806 + 2``, which ``run_arm``
   uses as the *training* ledger master seed, while training episode ids start
   at 0 and the evaluation ledger ids are 0..63.  The evaluation support was
   therefore not held out for the first seed.  External Pro found this by
   reading the source; nothing in the source found it.

Both are the same shape: a design choice that lived only in a caller's argument
list, so nothing could compare it against what was registered.

WHAT IS FROZEN, AND WHAT IS DELIBERATELY NOT
--------------------------------------------
The digest covers the design: seeds, the complete training budget, the
evaluation support (ledger count, seed, base), the certified optima and switch
point the readout is judged against, the exactly-weighted crossed support, the
**content fingerprint of the scientific graph**, and the library versions --
because the certificate's exact-rational claims and the float32 training path
are both version-dependent.

It does NOT cover the commit hash or the worktree dirty flag.  Those move
whenever HEAD moves for an unrelated reason, and the point of a precommitment
digest is that it survives every commit that does not change the design.  The
commit travels alongside as human-readable provenance, exactly as External Pro
allowed for FOLR: *"the content fingerprint is the operative binding; a
human-readable commit identity may travel alongside it."*

It also records, inside the frozen identity, whether the registered evaluation
support is actually held out.  A contaminated design is then part of what was
registered rather than a discovery made afterwards.
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from experiments.candidates.ucope import capability_certificate as cc
from experiments.candidates.ucope import crossed_evaluation as ce
from experiments.candidates.ucope import paired_training as pt

RAW_OUTPUT_BINDING = "ucope.registration.v1"

#: Everything that executes the registered replication: the six single-seed
#: provenance sources, the replication driver, and this module.
#:
#: The lesson is FOLR's, and it was Pro's sharpest correction there: freezing
#: the model path while leaving the harness free freezes the wrong half.  A
#: change to ``cross_seed.py`` -- the summariser, the switching-rule
#: classifier, the disjointness diagnostic -- changes the executable scientific
#: proposition with every model file untouched.
SCIENTIFIC_GRAPH_SOURCES = tuple(
    sorted(
        ce._PROVENANCE_SOURCES
        + (
            "experiments/candidates/ucope/cross_seed.py",
            "experiments/candidates/ucope/registration.py",
        )
    )
)


class RegistrationMismatch(RuntimeError):
    """The replication about to run is not the one that was registered."""


def _repository_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def _digest_of(value: Any) -> str:
    """Stable digest over a JSON-shaped structure."""
    hasher = hashlib.sha256()

    def feed(node: Any) -> None:
        if isinstance(node, Mapping):
            hasher.update(b"{")
            for key in sorted(node):
                hasher.update(repr(str(key)).encode("utf-8"))
                feed(node[key])
            hasher.update(b"}")
        elif isinstance(node, (list, tuple)):
            hasher.update(b"[")
            for item in node:
                feed(item)
            hasher.update(b"]")
        else:
            hasher.update(repr(node).encode("utf-8"))

    feed(value)
    return hasher.hexdigest()


def scientific_graph_identity() -> dict[str, Any]:
    """Commit, cleanliness and per-file digests of everything that executes."""
    root = _repository_root()

    def _git(*arguments: str) -> str | None:
        try:
            return subprocess.run(
                ["git", *arguments],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return None

    head = _git("rev-parse", "HEAD")
    commit = head.strip() if head is not None else "UNAVAILABLE"
    status = _git("status", "--porcelain", "--", *SCIENTIFIC_GRAPH_SOURCES)
    dirty = None if status is None else bool(status.strip())

    digests = {}
    for relative in SCIENTIFIC_GRAPH_SOURCES:
        # LF-normalized: this worktree runs core.autocrlf=true, so raw bytes
        # would fingerprint differently on a fresh clone.
        digests[relative] = hashlib.sha256(
            (root / relative).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()

    hasher = hashlib.sha256()
    for relative in SCIENTIFIC_GRAPH_SOURCES:
        hasher.update(relative.encode("utf-8"))
        hasher.update(digests[relative].encode("utf-8"))

    return {
        "source_commit": commit,
        "registered_sources_dirty": dirty,
        "commit_authenticates_the_registration": (
            commit != "UNAVAILABLE" and dirty is False
        ),
        "registered_sources": digests,
        "scientific_graph_fingerprint": hasher.hexdigest(),
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
    }


def crossed_support_digest() -> str:
    """The exactly-weighted evaluation cells, hashed as exact rationals.

    Pro's remedy for the falsified ceiling guard was this estimator; a
    replication that quietly used different cells or different weights would be
    measuring something else under the same name.  ``Fraction`` is stringified
    rather than floated so the digest is over the exact weights.
    """
    return _digest_of(
        [
            {"regime": regime, "bits": list(bits), "weight": str(weight)}
            for regime, bits, weight in ce.CROSSED_SUPPORT
        ]
    )


@dataclass(frozen=True)
class Registration:
    """The frozen identity of one UCOPE replication design."""

    design_identifier: str
    seeds: tuple[int, ...]
    training: Mapping[str, int]
    evaluation_ledgers: int
    ledger_seed: int
    ledger_base: int
    switch_point: float
    certified_informed_optimum: float
    certified_blind_optimum: float
    support_digest: str
    disjointness: Mapping[str, Any]
    source_identity: Mapping[str, Any]
    #: torch intra-op thread count the run pins. It enters the digest because it
    #: changes the update-matmul reduction order and therefore the trained
    #: weights; ``None`` means "whatever the machine's torch default is", which
    #: is not reproducible across core counts and is kept only for designs that
    #: document an already-executed ambient-thread run.
    threads: int | None = None

    def __post_init__(self) -> None:
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("registered seeds must be distinct")
        for name in ("iterations", "episodes_per_iteration", "evaluation_episodes"):
            if name not in self.training:
                raise ValueError(f"the registered training budget needs {name}")
        if self.evaluation_ledgers <= 0:
            raise ValueError("a registration needs at least one evaluation ledger")

    def registration_digest(self) -> str:
        """The precommitment. Stable across commits that do not change design."""
        hasher = hashlib.sha256()
        hasher.update(RAW_OUTPUT_BINDING.encode("utf-8"))
        hasher.update(
            _digest_of(
                {
                    "design_identifier": self.design_identifier,
                    "seeds": list(self.seeds),
                    "training": dict(sorted(self.training.items())),
                    "evaluation_ledgers": self.evaluation_ledgers,
                    "ledger_seed": self.ledger_seed,
                    "ledger_base": self.ledger_base,
                    # Thread count changes the trained weights, so a 1-thread
                    # design and an ambient-thread design must never collide.
                    "threads": self.threads,
                    "switch_point": self.switch_point,
                    "certified_informed_optimum": self.certified_informed_optimum,
                    "certified_blind_optimum": self.certified_blind_optimum,
                    "support_digest": self.support_digest,
                    # The contamination verdict is part of the registered
                    # identity, so a held-out design and a non-held-out one can
                    # never share a digest.
                    "evaluation_support_is_held_out_for_every_seed": bool(
                        self.disjointness[
                            "evaluation_support_is_held_out_for_every_seed"
                        ]
                    ),
                    "scientific_graph_fingerprint": str(
                        self.source_identity["scientific_graph_fingerprint"]
                    ),
                    "torch_version": str(self.source_identity["torch_version"]),
                    "numpy_version": str(self.source_identity["numpy_version"]),
                }
            ).encode("utf-8")
        )
        return hasher.hexdigest()

    def run_arguments(self) -> dict[str, Any]:
        """Exactly the keyword arguments a conforming replication must use.

        ``design_identifier`` is one of them.  It enters the digest, so a run
        that dropped it would compute a different digest from the one printed
        for approval and the gate could never be satisfied -- which is what
        happened the first time this CLI was exercised, with the runner
        hard-coding an identifier the registrable designs did not use.
        """
        return {
            "design_identifier": self.design_identifier,
            "seeds": list(self.seeds),
            "evaluation_ledgers": self.evaluation_ledgers,
            "ledger_seed": self.ledger_seed,
            "ledger_base": self.ledger_base,
            "threads": self.threads,
            **dict(self.training),
        }

    def frozen_record(self) -> dict[str, Any]:
        return {
            "raw_output_binding": RAW_OUTPUT_BINDING,
            "design_identifier": self.design_identifier,
            "registration_digest": self.registration_digest(),
            "run_arguments": self.run_arguments(),
            "switch_point": self.switch_point,
            "certified_informed_optimum": self.certified_informed_optimum,
            "certified_blind_optimum": self.certified_blind_optimum,
            "crossed_support_digest": self.support_digest,
            "evaluation_support_disjointness": dict(self.disjointness),
            "source_identity": dict(self.source_identity),
        }


def build_registration(
    *,
    design_identifier: str,
    seeds: Sequence[int],
    ledger_seed: int,
    ledger_base: int,
    evaluation_ledgers: int = 64,
    training: Mapping[str, int] | None = None,
    threads: int | None = None,
) -> Registration:
    """Construct a frozen registration. Trains nothing and measures nothing.

    ``training`` is the *whole* resolved training keyword set, not the three
    registered fields.  ``run_arm`` accepts arbitrary extras through
    ``**training_kwargs``, so narrowing here would let an override change what
    trains without moving the digest.

    ``threads`` is the pinned torch intra-op thread count. It is a science-
    affecting field (it moves the trained weights), so it enters the digest;
    ``max_workers`` -- the parallel dispatch width -- deliberately does not,
    because dispatch order cannot change a deterministic per-seed result.
    """
    budget = dict(ce.REGISTERED_TRAINING if training is None else training)
    return Registration(
        design_identifier=str(design_identifier),
        seeds=tuple(int(seed) for seed in seeds),
        training=budget,
        evaluation_ledgers=int(evaluation_ledgers),
        ledger_seed=int(ledger_seed),
        ledger_base=int(ledger_base),
        threads=None if threads is None else int(threads),
        switch_point=float(_switch_point()),
        certified_informed_optimum=float(pt.INFORMED_OPTIMUM),
        certified_blind_optimum=float(pt.BLIND_OPTIMUM),
        support_digest=crossed_support_digest(),
        disjointness=ce.evaluation_support_disjointness(
            seeds=seeds,
            ledger_seed=ledger_seed,
            evaluation_ledgers=evaluation_ledgers,
            iterations=budget["iterations"],
            episodes_per_iteration=budget["episodes_per_iteration"],
            ledger_base=ledger_base,
        ),
        source_identity=scientific_graph_identity(),
    )


def _switch_point() -> float:
    """Imported lazily: cross_seed imports this module for the gate."""
    from experiments.candidates.ucope import cross_seed as cs

    return cs.SWITCH_POINT


def archived_replication() -> Registration:
    """The design the v2 artifact actually ran, contamination included.

    Kept so the archived run stays reproducible and so its digest exists as a
    thing that can be named.  Its disjointness verdict is False; that is the
    honest record, not something to be fixed retroactively.

    ``threads=None`` documents the original v2 run, which used the machine's
    ambient torch default (8 on the box it ran on).  It is deliberately NOT
    pinned to 1 here, because that would silently redefine what "the archived
    run" reproduces.
    """
    from experiments.candidates.ucope import cross_seed as cs

    return build_registration(
        design_identifier="ucope_cross_seed_v2_archived",
        seeds=cs.REPLICATION_SEEDS,
        ledger_seed=20_260_808,
        ledger_base=ce.DEFAULT_LEDGER_BASE,
        threads=None,
    )


def held_out_replication() -> Registration:
    """The same design with the evaluation ids moved clear of training.

    The remedy External Pro named that is robust to any seed choice: a ledger is
    ``(id, master_seed, profile)``, so disagreeing on the id is enough, and
    shifting the ids clears every seed at once rather than one at a time.

    ``threads=1`` because this design has no prior executed artifact to match, so
    it is registered at the reproducible, machine-independent thread count from
    the start.  That also lets it run across a process pool without
    oversubscription while staying byte-identical to its own sequential run.  The
    contrast is internally matched -- both arms share this design's thread setting
    -- but External Pro (held-out round, 2026-08-06) corrected the stronger claim
    this docstring once made: it is NOT proven thread-INVARIANT, because the two
    arms follow different optimization trajectories that a float reduction-order
    change can interact with differently.  So this design's contrast estimates the
    count-enabled-minus-count-disabled protocol contrast under ``threads=1``, and
    the absolute v2->v3 shift stays confounded between held-outness and the thread
    change and must not be attributed to either.
    """
    from experiments.candidates.ucope import cross_seed as cs

    return build_registration(
        design_identifier="ucope_cross_seed_v3_held_out",
        seeds=cs.REPLICATION_SEEDS,
        ledger_seed=20_260_808,
        ledger_base=ce.CLEAN_LEDGER_BASE,
        threads=1,
    )


def held_out_severance_replication() -> Registration:
    """The held-out design, read for Pro's support-preserving severance.

    Identical training and evaluation configuration to ``held_out_replication``
    -- same eight seeds, same held-out ``ledger_base``, same ``threads=1`` -- so
    it reproduces the v3 held-out contrast byte-for-byte.  Two separate reasons
    its digest is distinct, and the docstring must not conflate them: at THIS
    commit it differs from ``held_out_replication``'s digest by the
    ``design_identifier`` alone -- the two share an identical source fingerprint;
    and both differ from the HISTORICAL v3 artifact's approved digest
    (``06ab5a7d…``), because the crossed-evaluation source now also computes
    ``support_preserving_severance`` (retain the completed-epoch channel, replace
    the positive count with a draw from its regime-independent prior-predictive
    marginal, average exactly over the crossed support), which moved the content
    fingerprint.  The severance itself adds no RNG draw, so the trained arms and
    their contrast are unchanged; the v4 artifact's contrast equalling v3's is the
    check that the addition perturbed nothing.
    """
    from experiments.candidates.ucope import cross_seed as cs

    return build_registration(
        design_identifier="ucope_cross_seed_v4_held_out_severance",
        seeds=cs.REPLICATION_SEEDS,
        ledger_seed=20_260_808,
        ledger_base=ce.CLEAN_LEDGER_BASE,
        threads=1,
    )


def require_registration(
    registration: Registration, expected_digest: str | None
) -> dict[str, Any]:
    """The gate. Raises BEFORE any training if the design is not the approved one.

    A ``None`` expectation does not raise -- the archived run was genuinely
    unregistered and must stay reproducible -- but the returned record says so,
    and the replication's terminal is downgraded accordingly.  Silence and
    approval must not look the same in the artifact.
    """
    current = registration.registration_digest()
    if expected_digest is None:
        return {
            "gated": False,
            "registration_digest": current,
            "status": (
                "NO PRECOMMITMENT SUPPLIED. This run is not bound to an approved "
                "design; its terminal is downgraded and no result from it may be "
                "reported as a registered replication."
            ),
        }
    if current != expected_digest:
        raise RegistrationMismatch(
            "the replication about to run is not the registered one: current "
            f"{current}, expected {expected_digest}. Nothing was trained."
        )
    return {
        "gated": True,
        "registration_digest": current,
        "expected_registration_digest": expected_digest,
        "status": "the executed design equals the precommitted one",
    }
