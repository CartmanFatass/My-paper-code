"""Generic exact information-prefix relaxation; no ACVC host inputs."""
from fractions import Fraction as F
from hashlib import sha512


DENOMINATOR = 2**511


def integer(label):
    return int.from_bytes(sha512(f"synthetic-prefix-common512/{label}".encode("utf-8")).digest(), "big")


def rational(label):
    """Positive dyadic fraction with a canonical 512-bit denominator."""
    return F(2 * (integer(label) % (DENOMINATOR // 2)) + 1, DENOMINATOR)


def synthetic_inputs(contexts=12, actions=3, check=lambda: None):
    # Two atoms per context, normalized within each regime. No scientific table.
    atoms = []
    check()
    k = 2 * contexts
    b = 2 * (DENOMINATOR // (2 * k)) + 1
    radius = b // (8 * k)
    for regime in range(2):
        numerators = [b + 2 * (integer(f"atom/{regime}/{j}") % (2 * radius + 1) - radius)
                      for j in range(k - 1)]
        numerators.append(DENOMINATOR - sum(numerators))
        atoms.append(tuple(F(numerator, DENOMINATOR) for numerator in numerators))
        check()
    contexts_given_regime = tuple(tuple(row[2*c] + row[2*c+1] for c in range(contexts))
                                  for row in atoms)
    multipliers = tuple(rational(f"multiplier/{i}") for i in range(2))
    budgets = tuple(rational(f"budget/{i}") for i in range(2))
    scores = []
    for r in range(2):
        row = []
        for c in range(contexts):
            row.append(tuple((1 if integer(f"score/{r}/{c}/{a}/sign") % 2 == 0 else -1)
                             * rational(f"score/{r}/{c}/{a}") for a in range(actions)))
            check()
        scores.append(tuple(row))
    return tuple(atoms), contexts_given_regime, tuple(scores), multipliers, budgets


def structural_counts(atom_count=24, contexts=12, actions=3, prefix=4):
    histories = sum(atom_count ** depth for depth in range(prefix))
    return {"histories": histories, "action_scores": histories * contexts * actions,
            "terms_per_score": 2, "tail_scores": 2 * contexts * actions,
            "history_expansions": histories - 1}


def prefix_bound(atoms, context_probabilities, scores, multipliers, budgets,
                 *, prior=(F(1, 2), F(1, 2)), horizon=12, prefix=4, check=lambda: None):
    """Evaluate the relaxed bound with exact unnormalised history masses.

    Rows of atoms are normalized conditional laws; context probabilities are
    their current-frame marginals. Scores depend on regime and current frame,
    never on current truth. Action order is input order (first maximum wins).
    The callback checks only resources, including during exact aggregation.
    """
    check()
    contexts = len(context_probabilities[0])
    actions = len(scores[0][0])
    regimes = len(prior)
    total = horizon * sum((x * y for x, y in zip(multipliers, budgets)), F(0))

    def visit(depth, masses):
        nonlocal total
        for context in range(contexts):
            weighted = [masses[r] * context_probabilities[r][context] for r in range(regimes)]
            action_scores = [sum((weighted[r] * scores[r][context][a]
                                  for r in range(regimes)), F(0)) for a in range(actions)]
            total += max(action_scores)
        check()
        if depth + 1 < prefix:
            for atom in range(len(atoms[0])):
                child = tuple(masses[r] * atoms[r][atom] for r in range(regimes))
                visit(depth + 1, child)

    visit(0, prior)
    for regime in range(regimes):
        for context in range(contexts):
            total += ((horizon - prefix) * prior[regime] * context_probabilities[regime][context]
                      * max(scores[regime][context]))
            check()
    return total
