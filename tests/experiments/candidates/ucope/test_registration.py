"""The UCOPE registration gate: refuse an unapproved design before training.

Both defects this candidate has carried were possible only because nothing
compared the design about to run against an approved one. The first trained
every arm to 40% of the registered budget (300 -> 120) and produced eight
plausible numbers describing the short budget rather than the seed. The second
let ``ledger_seed`` collide with a training-derived root, so the evaluation
support was not held out for the first seed. Neither raised anything; both cost
a full training run and an artifact that had to be re-read.

The gate is therefore checked here for the property that makes it worth having:
it raises *before* anything is trained, and it separates silence from approval.
"""

from __future__ import annotations

import pytest

from experiments.candidates.ucope import cross_seed as cs
from experiments.candidates.ucope import crossed_evaluation as ce
from experiments.candidates.ucope import paired_training as pt
from experiments.candidates.ucope import registration as reg


def test_a_design_that_is_not_the_approved_one_refuses_before_training(monkeypatch):
    """The whole point: nothing is trained, so a wrong design costs seconds.

    ``run_registered_experiment`` is replaced by a detonator. If the gate ran
    after training -- or not at all -- this test would fail with the detonator's
    message instead of ``RegistrationMismatch``, which is exactly the failure
    mode the gate exists to prevent.
    """

    def _must_not_run(**_kwargs):
        raise AssertionError("training started despite an unapproved design")

    monkeypatch.setattr(ce, "run_registered_experiment", _must_not_run)

    with pytest.raises(reg.RegistrationMismatch) as raised:
        cs.run_replication(
            seeds=(31_000,),
            evaluation_ledgers=1,
            iterations=1,
            episodes_per_iteration=2,
            evaluation_episodes=2,
            expected_registration_digest="0" * 64,
        )
    assert "Nothing was trained" in str(raised.value)


def test_the_approved_digest_admits_exactly_the_design_it_names(monkeypatch):
    """The other half: the gate must not refuse the design it approved.

    A gate that also blocked conforming runs would be removed within a day, so
    the admitting direction is pinned as tightly as the refusing one.
    """
    captured: list[dict] = []

    def _record(**kwargs):
        captured.append(kwargs)
        raise RuntimeError("gate passed, stopping before the real training")

    registration = reg.build_registration(
        design_identifier="ucope_cross_seed_probe",
        seeds=(31_000,),
        ledger_seed=20_260_808,
        ledger_base=ce.DEFAULT_LEDGER_BASE,
        evaluation_ledgers=1,
        training={
            "iterations": 1,
            "episodes_per_iteration": 2,
            "evaluation_episodes": 2,
        },
    )

    monkeypatch.setattr(ce, "run_registered_experiment", _record)
    # Driven from `run_arguments()` rather than a re-typed argument list: a
    # replication assembled by hand can disagree with the registration it quotes,
    # which is precisely the defect this file's round-trip test pins.
    with pytest.raises(RuntimeError, match="gate passed"):
        cs.run_replication(
            **registration.run_arguments(),
            expected_registration_digest=registration.registration_digest(),
        )
    assert captured and captured[0]["seed"] == 31_000
    assert captured[0]["ledger_base"] == ce.DEFAULT_LEDGER_BASE


@pytest.mark.parametrize(
    "design", ("archived_replication", "held_out_replication"), ids=str
)
def test_the_digest_printed_for_approval_is_the_digest_the_run_recomputes(
    monkeypatch, design
):
    """The round trip the whole gate depends on, and it was broken.

    ``--list-designs`` prints a digest; External Pro approves that literal;
    ``--approved-digest`` quotes it back. The first exercise of this CLI showed
    the runner recomputing a *different* digest, because it hard-coded
    ``design_identifier="ucope_cross_seed_run"`` while the registrable designs
    are named ``..._v2_archived`` and ``..._v3_held_out``. Every approval would
    have been unusable -- a gate that can only refuse is not a gate, and the
    failure would have surfaced only at the moment of running the approved
    experiment.

    Nothing is trained here: the gate is verified by the fact that the design's
    own arguments reach the detonator rather than tripping ``RegistrationMismatch``.
    """
    registration = getattr(reg, design)()

    def _stop_after_the_gate(**_kwargs):
        raise RuntimeError("gate passed")

    monkeypatch.setattr(ce, "run_registered_experiment", _stop_after_the_gate)
    with pytest.raises(RuntimeError, match="gate passed"):
        cs.run_replication(
            **registration.run_arguments(),
            expected_registration_digest=registration.registration_digest(),
        )


def test_a_training_override_moves_the_digest(monkeypatch):
    """``run_arm`` takes arbitrary extras, so the digest covers the whole budget.

    Hashing only (iterations, episodes_per_iteration, evaluation_episodes)
    would let any other training override change what runs while the digest --
    and therefore the approval -- stayed put.
    """
    registration = reg.archived_replication()
    monkeypatch.setattr(
        ce, "run_registered_experiment", lambda **_k: pytest.fail("must not train")
    )
    with pytest.raises(reg.RegistrationMismatch):
        cs.run_replication(
            **{**registration.run_arguments(), "iterations": 1},
            expected_registration_digest=registration.registration_digest(),
        )


def test_silence_and_approval_do_not_look_the_same_in_the_artifact():
    """``None`` is permitted -- the archived run really was unregistered."""
    gate = reg.require_registration(reg.archived_replication(), None)
    assert gate["gated"] is False
    assert "NO PRECOMMITMENT" in gate["status"]
    assert len(gate["registration_digest"]) == 64


def test_the_contamination_verdict_is_part_of_the_registered_identity():
    """A held-out design and a contaminated one must never share a digest.

    They differ only in ``ledger_base``, and a digest that ignored the resulting
    held-out verdict would let an approval granted for the clean design license
    the contaminated one.
    """
    archived = reg.archived_replication()
    held_out = reg.held_out_replication()

    assert archived.disjointness["evaluation_support_is_held_out_for_every_seed"] is False
    assert held_out.disjointness["evaluation_support_is_held_out_for_every_seed"] is True
    assert archived.registration_digest() != held_out.registration_digest()
    assert archived.run_arguments()["ledger_base"] == ce.DEFAULT_LEDGER_BASE
    assert held_out.run_arguments()["ledger_base"] == ce.CLEAN_LEDGER_BASE


def test_every_registered_constant_moves_the_digest():
    """Each field is load-bearing, or the freeze is decorative.

    Written as a sweep rather than one assertion per field so that a constant
    added to ``Registration`` without being hashed shows up here.
    """
    base = reg.build_registration(
        design_identifier="probe",
        seeds=(31_000, 32_000),
        ledger_seed=20_260_808,
        ledger_base=ce.DEFAULT_LEDGER_BASE,
        evaluation_ledgers=4,
    )
    variants = {
        "design_identifier": dict(design_identifier="probe_other"),
        "seeds": dict(seeds=(31_000, 33_000)),
        "ledger_seed": dict(ledger_seed=20_260_809),
        "ledger_base": dict(ledger_base=ce.CLEAN_LEDGER_BASE),
        "evaluation_ledgers": dict(evaluation_ledgers=5),
        "training": dict(
            training={
                "iterations": 1,
                "episodes_per_iteration": 2,
                "evaluation_episodes": 2,
            }
        ),
    }
    arguments = dict(
        design_identifier="probe",
        seeds=(31_000, 32_000),
        ledger_seed=20_260_808,
        ledger_base=ce.DEFAULT_LEDGER_BASE,
        evaluation_ledgers=4,
    )
    for field, override in variants.items():
        moved = reg.build_registration(**{**arguments, **override})
        assert moved.registration_digest() != base.registration_digest(), field


def test_the_digest_does_not_move_with_the_commit_or_the_dirty_flag():
    """Content, not bookkeeping.

    A digest that moved with the commit hash would be re-approved after every
    unrelated edit, and a precommitment nobody can keep is one nobody keeps.
    The source *content* fingerprint and the library versions do enter it.
    """
    identity = reg.scientific_graph_identity()
    assert set(identity) >= {
        "source_commit",
        "registered_sources_dirty",
        "scientific_graph_fingerprint",
        "torch_version",
        "numpy_version",
    }

    first = reg.archived_replication().registration_digest()
    second = reg.archived_replication().registration_digest()
    assert first == second

    # The fingerprint covers the modules a result actually depends on, and the
    # gate module itself: a gate that could be edited without moving the digest
    # would not be a gate.
    assert "experiments/candidates/ucope/registration.py" in reg.SCIENTIFIC_GRAPH_SOURCES
    assert "experiments/candidates/ucope/cross_seed.py" in reg.SCIENTIFIC_GRAPH_SOURCES
    assert "experiments/candidates/ucope/crossed_evaluation.py" in reg.SCIENTIFIC_GRAPH_SOURCES


def test_the_registered_optima_and_support_come_from_the_modules_that_use_them():
    """The registration must not restate constants; it must reference them.

    A second copy of 36.5 / 32.0 or of the crossed weights is a second thing to
    keep in sync, and the falsified ceiling guard was exactly a quantity that
    had drifted from the estimator it claimed to bound.
    """
    registration = reg.archived_replication()
    assert registration.certified_informed_optimum == pt.INFORMED_OPTIMUM
    assert registration.certified_blind_optimum == pt.BLIND_OPTIMUM
    assert registration.switch_point == cs.SWITCH_POINT
    assert registration.support_digest == reg.crossed_support_digest()
    assert len(ce.CROSSED_SUPPORT) == 16


def test_the_support_digest_is_over_exact_weights_not_floats():
    """``Fraction`` stringified, so a float-rounded reweighting cannot hide.

    The weights sum to exactly 1 as rationals; a replication that quietly used
    a different cell set or renormalized weights would be measuring something
    else under the same name.
    """
    from fractions import Fraction

    assert sum(weight for _regime, _bits, weight in ce.CROSSED_SUPPORT) == Fraction(1)
    assert all(
        isinstance(weight, Fraction) for _regime, _bits, weight in ce.CROSSED_SUPPORT
    )
    assert len(reg.crossed_support_digest()) == 64


def test_a_registration_refuses_a_design_it_could_not_run():
    """Cheap structural guards, since a malformed freeze is worse than none."""
    with pytest.raises(ValueError, match="distinct"):
        reg.build_registration(
            design_identifier="probe",
            seeds=(31_000, 31_000),
            ledger_seed=1,
            ledger_base=0,
        )
    with pytest.raises(ValueError, match="evaluation_episodes"):
        reg.Registration(
            design_identifier="probe",
            seeds=(1,),
            training={"iterations": 1, "episodes_per_iteration": 1},
            evaluation_ledgers=1,
            ledger_seed=1,
            ledger_base=0,
            switch_point=0.5,
            certified_informed_optimum=36.5,
            certified_blind_optimum=32.0,
            support_digest="0" * 64,
            disjointness={"evaluation_support_is_held_out_for_every_seed": True},
            source_identity=reg.scientific_graph_identity(),
        )
