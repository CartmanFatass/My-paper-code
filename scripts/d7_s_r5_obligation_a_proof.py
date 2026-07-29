"""D7.S R5 obligation A -- proof harness for the exposure-certified derangement.

Closes obligation A of Pro's R5 ruling. This is a DEVELOPMENT PROOF HARNESS and
is deliberately standalone: it imports nothing from the audit path, is imported
by nothing, and steps no environment. It is not the R5 control implementation --
that is not authorized -- it is the enumeration Pro required in order to check
that a forbidden-diagonal LAP actually returns the minimum-distance derangement
under the registered tie-break.

Findings recorded in
`docs/research/designs/D7_S_R5_OBLIGATION_A_SUPPORT_DERIVATION.md`:

  * cost is right: 360 random trials, zero mismatches against exhaustive search;
  * the registered lexicographic tie-break is NOT what the bare solver returns
    (counterexample: symmetric ring, n=4) -- it needs the canonicalisation pass
    implemented here;
  * `n >= 2` is necessary but NOT sufficient for a full derangement once
    eligibility condition 6 removes edges (witness: allowed=[{2},{2},{0,1}]).

Run:
    C:\\Users\\fires\\.conda\\envs\\hmasd-amd-cpu\\python.exe scripts/d7_s_r5_obligation_a_proof.py
"""
import itertools

import numpy as np
from scipy.optimize import linear_sum_assignment

RNG_SEED = 20260729
# A large FINITE sentinel, never `inf`: with `inf` the solver raises instead of
# reporting infeasibility, which would hide the very case obligation A6 exists
# to witness.
BIG = 1e12
EPS = 1e-9


def cost_matrix(agent_pos, duty_pos):
    n, m = len(agent_pos), len(duty_pos)
    C = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            C[i, j] = np.linalg.norm(
                np.asarray(agent_pos[i][:2], dtype=float)
                - np.asarray(duty_pos[j][:2], dtype=float))
    return C


def _solve(M):
    r, c = linear_sum_assignment(M)
    return list(zip(r.tolist(), c.tolist())), float(M[r, c].sum())


def canonical_min_derangement(C, forbidden, n):
    """Lexicographically smallest minimum-distance derangement.

    The registered tie-break is lexicographic by (duty_id, uav_id). The bare
    solver does not honour it, so: solve for the optimal cost, then walk duties
    ascending and fix the smallest agent id whose forced completion still
    attains that cost. Returns (pairs, cost) or (None, None) if infeasible.
    """
    M0 = C.copy()
    for (i, j) in forbidden:
        M0[i, j] = BIG
    opt = _solve(M0)[1]
    if opt >= BIG / 2:
        return None, None

    fixed = {}
    for j in range(n):
        for i in range(n):
            if i in fixed.values() or M0[i, j] >= BIG / 2:
                continue
            T = M0.copy()
            for i2 in range(n):
                if i2 != i:
                    T[i2, j] = BIG
            for j2 in range(n):
                if j2 != j:
                    T[i, j2] = BIG
            for (fj, fi) in fixed.items():
                for i2 in range(n):
                    if i2 != fi:
                        T[i2, fj] = BIG
                for j2 in range(n):
                    if j2 != fj:
                        T[fi, j2] = BIG
            if abs(_solve(T)[1] - opt) <= EPS:
                fixed[j] = i
                break
        if j not in fixed:
            return None, None
    pairs = [(i, j) for j, i in sorted(fixed.items())]
    return pairs, float(sum(C[i, j] for i, j in pairs))


def brute_force(C, forbidden, n):
    """Exhaustive minimum over derangements, with the registered tie-break."""
    best_cost = best_key = best = None
    for perm in itertools.permutations(range(n)):
        pairs = [(i, perm[i]) for i in range(n)]
        if any(p in forbidden for p in pairs):
            continue
        c = float(sum(C[i, perm[i]] for i in range(n)))
        key = tuple(sorted((j, i) for i, j in pairs))
        if (best_cost is None or c < best_cost - EPS
                or (abs(c - best_cost) <= EPS and key < best_key)):
            best_cost, best_key, best = c, key, pairs
    return best, best_cost


def hall_witness(n, allowed):
    """Smallest agent set S with |N(S)| < |S|, or None if Hall's condition holds."""
    for size in range(1, n + 1):
        for S in itertools.combinations(range(n), size):
            nbr = set()
            for i in S:
                nbr |= allowed[i]
            if len(nbr) < len(S):
                return {"S": list(S), "neighbourhood": sorted(nbr)}
    return None


def _ring(n, r=10.0):
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([np.cos(ang), np.sin(ang)], axis=1) * r


def main():
    rng = np.random.default_rng(RNG_SEED)
    ok = True

    print("=== A5 cost: canonical solver vs exhaustive enumeration ===")
    mismatches = trials = 0
    for n in range(2, 8):
        for _ in range(60):
            trials += 1
            C = cost_matrix(rng.uniform(-50, 50, (n, 2)), rng.uniform(-50, 50, (n, 2)))
            forb = {(i, i) for i in range(n)}
            can, can_c = canonical_min_derangement(C, forb, n)
            bf, bf_c = brute_force(C, forb, n)
            if can is None or abs(can_c - bf_c) > 1e-9:
                mismatches += 1
    print(f"  trials={trials} mismatches={mismatches}")
    ok &= (mismatches == 0)

    print("\n=== A5 tie-break: constructed exact ties ===")
    for n in (3, 4, 5, 6, 7):
        pts = _ring(n)
        C = cost_matrix(pts, pts)
        forb = {(i, i) for i in range(n)}
        can, _ = canonical_min_derangement(C, forb, n)
        bf, _ = brute_force(C, forb, n)
        raw, _ = _solve(np.where(np.eye(n, dtype=bool), BIG, C))
        same = sorted((j, i) for i, j in can) == sorted((j, i) for i, j in bf)
        raw_same = sorted((j, i) for i, j in raw) == sorted((j, i) for i, j in bf)
        print(f"  ring n={n}  canonical_matches={same}  bare_solver_matches={raw_same}")
        ok &= same

    print("\n=== A5 determinism: one tied input, repeated solves ===")
    pts = _ring(6)
    C = cost_matrix(pts, pts)
    forb = {(i, i) for i in range(6)}
    distinct = {tuple(canonical_min_derangement(C, forb, 6)[0]) for _ in range(20)}
    print(f"  distinct results over 20 solves={len(distinct)}")
    ok &= (len(distinct) == 1)

    print("\n=== A6 existence: all non-incumbent edges legal ===")
    for n in (1, 2, 3, 4):
        allowed = [set(j for j in range(n) if j != i) for i in range(n)]
        w = hall_witness(n, allowed)
        print(f"  n={n} derangement_exists={w is None} witness={w}")

    print("\n=== A6 existence: eligibility condition 6 removes edges ===")
    allowed = [{2}, {2}, {0, 1}]
    w = hall_witness(3, allowed)
    print(f"  allowed={allowed} witness={w}")
    print("  => infeasible at n=3, so a cardinality test alone is NOT the support rule")
    ok &= (w is not None)

    print("\n=== A3: |U_e| == |D_e| by construction ===")
    a3 = True
    for _ in range(2000):
        n_duties = int(rng.integers(2, 9))
        n_air = int(rng.integers(1, n_duties + 1))
        duties = list(range(n_duties))
        rng.shuffle(duties)
        m0 = {d: u for u, d in enumerate(duties[:n_air])}
        eligible = {u for u in range(n_air) if rng.random() < 0.7}
        D_e = {d for d, u in m0.items() if u in eligible}
        U_e = {m0[d] for d in D_e}
        if len(U_e) != len(D_e):
            a3 = False
            break
    print(f"  held_on_every_sample={a3}")
    ok &= a3

    print(f"\nOBLIGATION_A_CHECKS_PASS={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
