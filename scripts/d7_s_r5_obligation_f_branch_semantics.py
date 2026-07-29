"""D7.S R5 obligation F -- branch semantics, frozen synthetically.

D7_S_R5_DEVELOPMENT_OBLIGATIONS_NOT_A_RESULT

Closes obligation F. Pro ordered this FIRST, before any treatment data exists,
so that a development observation cannot acquire an interpretation the
comparator does not support. Purely synthetic: no environment, no episode, no
audit-path import, no D_A inference.

The one-sided meaning being protected:

    pi_der is a MEMBER of the no-persistence policy class, not its optimum, so
    V_D <= V*_notP. Equivalence therefore REFUTES persistence necessity, while
    "materially worse" establishes only that THIS least-distance derangement is
    worse. There must be no code path from a worse result to
    PERSISTENCE_NECESSARY_SOURCE.

Run:
    C:\\Users\\fires\\.conda\\envs\\hmasd-amd-cpu\\python.exe scripts/d7_s_r5_obligation_f_branch_semantics.py
"""
import itertools

MATERIALITY_MARGIN = 5.0

# The complete result vocabulary. PERSISTENCE_NECESSARY_SOURCE is deliberately
# ABSENT: it is not reachable from this comparator by any input, and the guard
# below proves it rather than asserting it.
R5_PART_A_LABELS = (
    "COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY",
    "MIN_DISTANCE_DERANGEMENT_WORSE",
    "DERANGEMENT_CONTROL_UNRESOLVED",
    "DERANGEMENT_CONTROL_SUPPORT_INSUFFICIENT",
    "DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY",
    "INVALID_EVENT_ALIGNED_AUDIT",
)

FORBIDDEN_LABEL = "PERSISTENCE_NECESSARY_SOURCE"


def r5_part_a_branch(*, exposure_ok, pretreatment_support_ok, post_start_total,
                     lower_contrast_lcb, lower_contrast_ucb, upper_contrast_lcb):
    """The frozen R5 Part-A result map.

    Contrasts follow the registered R4 convention, with
    `D_A = G(derangement) - G(constructive_mixed)`:

        lower contrast = D_A + MATERIALITY_MARGIN
        upper contrast = MATERIALITY_MARGIN - D_A

    Precedence is fail-closed and severity-ordered. An instrument that did not
    do what it claims is never allowed to emit a mechanism reading, however
    clean its numbers look.
    """
    # 1. The instrument did not instantiate the intervention it claims.
    if not exposure_ok:
        return "INVALID_EVENT_ALIGNED_AUDIT"

    # 2. The control stopped being total after treatment began. Topology-level
    #    abort, never selective deletion of the one adverse episode.
    if not post_start_total:
        return "DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY"

    # 3. Pre-treatment support never qualified. A support outcome, explicitly
    #    NOT equivalence, inferiority or zero effect.
    if not pretreatment_support_ok:
        return "DERANGEMENT_CONTROL_SUPPORT_INSUFFICIENT"

    # 4. Only now may the statistics speak.
    equivalent = (lower_contrast_lcb > 0.0) and (upper_contrast_lcb > 0.0)
    materially_worse = lower_contrast_ucb < 0.0

    if equivalent and materially_worse:
        # Structurally unreachable: D_A cannot be both inside and below the
        # margin. Refuse rather than pick, so a future numeric change cannot
        # silently choose the friendlier reading.
        return "INVALID_EVENT_ALIGNED_AUDIT"
    if equivalent:
        return "COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY"
    if materially_worse:
        # NOT a necessity finding. Comparator-specific negative only.
        return "MIN_DISTANCE_DERANGEMENT_WORSE"
    return "DERANGEMENT_CONTROL_UNRESOLVED"


def interpretation(label):
    """What each label licenses. Kept beside the map so a reader cannot pair a
    branch with a meaning it was never given."""
    return {
        "COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY":
            "an exposure-certified no-persistence controller matched the persistent "
            "controller within the registered margin; individual-persistence "
            "necessity is REFUTED at this scale",
        "MIN_DISTANCE_DERANGEMENT_WORSE":
            "this least-distance derangement is worse; source necessity remains "
            "UNRESOLVED because V_D <= V*_notP",
        "DERANGEMENT_CONTROL_UNRESOLVED":
            "the interval overlaps the equivalence and worse regions; no mechanism "
            "reading",
        "DERANGEMENT_CONTROL_SUPPORT_INSUFFICIENT":
            "pre-treatment support floors were not met; a support outcome, NOT "
            "equivalence, inferiority or zero effect",
        "DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY":
            "the control stopped being total after treatment began; that topology's "
            "Part-A units are discarded entirely",
        "INVALID_EVENT_ALIGNED_AUDIT":
            "the instrument did not do what it claims; no mechanistic result",
    }[label]


# ---------------------------------------------------------------------------
# Paired negatives -- deliberately wrong maps that MUST be caught.
# ---------------------------------------------------------------------------

def _mutant_worse_means_necessary(**kw):
    """The R4-shaped error: a worse control arm read as proof of necessity."""
    label = r5_part_a_branch(**kw)
    return FORBIDDEN_LABEL if label == "MIN_DISTANCE_DERANGEMENT_WORSE" else label


def _mutant_support_reads_as_equivalence(**kw):
    """A support miss quietly reported as equivalence -- the 'no data looks like
    no effect' failure."""
    label = r5_part_a_branch(**kw)
    return ("COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY"
            if label == "DERANGEMENT_CONTROL_SUPPORT_INSUFFICIENT" else label)


def _mutant_exposure_ignored(*, exposure_ok, **kw):
    """Exposure failure ignored, so the statistics are allowed to speak from an
    instrument that never forced renewal."""
    return r5_part_a_branch(exposure_ok=True, **kw)


def _mutant_post_start_drops_episode(*, post_start_total, **kw):
    """Post-start infeasibility handled by dropping the episode instead of
    aborting the topology."""
    return r5_part_a_branch(post_start_total=True, **kw)


# ---------------------------------------------------------------------------

_GRID_CONTRASTS = (
    # (lower_lcb, lower_ucb, upper_lcb, expected_when_clean)
    (4.32, 6.69, 3.31, "COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY"),   # R4-shaped equivalence
    (0.10, 2.00, 0.10, "COUNTEREXAMPLE_TO_PERSISTENCE_NECESSITY"),   # barely inside
    (-3.0, -0.5, 9.00, "MIN_DISTANCE_DERANGEMENT_WORSE"),            # clearly worse
    (-9.0, -6.0, 12.0, "MIN_DISTANCE_DERANGEMENT_WORSE"),            # far worse
    (-1.0, 3.00, 2.00, "DERANGEMENT_CONTROL_UNRESOLVED"),            # straddles below
    (2.00, 6.00, -1.0, "DERANGEMENT_CONTROL_UNRESOLVED"),            # straddles above
    (-2.0, 4.00, -2.0, "DERANGEMENT_CONTROL_UNRESOLVED"),            # straddles both
)


def _enumerate():
    for exposure_ok, support_ok, total in itertools.product((True, False), repeat=3):
        for lo_lcb, lo_ucb, up_lcb, expected in _GRID_CONTRASTS:
            yield dict(exposure_ok=exposure_ok, pretreatment_support_ok=support_ok,
                       post_start_total=total, lower_contrast_lcb=lo_lcb,
                       lower_contrast_ucb=lo_ucb, upper_contrast_lcb=up_lcb), expected


def main():
    ok = True
    cases = list(_enumerate())
    print(f"=== F: exhaustive branch enumeration ({len(cases)} cases) ===")

    labels_seen = set()
    bad = 0
    for kw, expected in cases:
        label = r5_part_a_branch(**kw)
        labels_seen.add(label)
        if label not in R5_PART_A_LABELS:
            print(f"  UNKNOWN LABEL {label} for {kw}")
            bad += 1
            continue
        clean = kw["exposure_ok"] and kw["pretreatment_support_ok"] and kw["post_start_total"]
        if clean and label != expected:
            print(f"  WRONG {label} != {expected} for {kw}")
            bad += 1
        if not kw["exposure_ok"] and label != "INVALID_EVENT_ALIGNED_AUDIT":
            print(f"  exposure failure did not dominate: {label}")
            bad += 1
        if kw["exposure_ok"] and not kw["post_start_total"] \
                and label != "DERANGEMENT_CONTROL_NOT_TOTAL_ON_TOPOLOGY":
            print(f"  post-start failure did not dominate: {label}")
            bad += 1
    print(f"  mismatches={bad}")
    print(f"  labels reached: {len(labels_seen)}/{len(R5_PART_A_LABELS)}")
    ok &= (bad == 0)

    print("\n=== F: every frozen label is reachable ===")
    for lab in R5_PART_A_LABELS:
        hit = lab in labels_seen
        print(f"  {lab:44s} reachable={hit}")
        ok &= hit

    print("\n=== F: the forbidden label is unreachable ===")
    forbidden_hits = sum(1 for kw, _ in cases if r5_part_a_branch(**kw) == FORBIDDEN_LABEL)
    in_vocab = FORBIDDEN_LABEL in R5_PART_A_LABELS
    print(f"  {FORBIDDEN_LABEL} produced by {forbidden_hits} of {len(cases)} cases")
    print(f"  present in the frozen vocabulary: {in_vocab}")
    ok &= (forbidden_hits == 0 and not in_vocab)

    print("\n=== F: paired negatives -- each MUST go red ===")
    negatives = (
        ("worse read as necessity", _mutant_worse_means_necessary),
        ("support miss read as equivalence", _mutant_support_reads_as_equivalence),
        ("exposure failure ignored", _mutant_exposure_ignored),
        ("post-start drops the episode", _mutant_post_start_drops_episode),
    )
    for name, mutant in negatives:
        caught = False
        for kw, _ in cases:
            if mutant(**kw) != r5_part_a_branch(**kw):
                caught = True
                break
        print(f"  {name:36s} detected={caught}")
        ok &= caught

    print("\n=== F: interpretations are attached to every label ===")
    for lab in R5_PART_A_LABELS:
        txt = interpretation(lab)
        ok &= bool(txt)
    worse_txt = interpretation("MIN_DISTANCE_DERANGEMENT_WORSE")
    says_unresolved = "UNRESOLVED" in worse_txt
    print(f"  'worse' interpretation states source necessity UNRESOLVED: {says_unresolved}")
    ok &= says_unresolved

    print(f"\nOBLIGATION_F_CHECKS_PASS={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
