#!/usr/bin/env python3
"""Sparse-window relay toy (SWR).

A standard-library-only gridworld that keeps the structure of the proposed sparse-reward
UAV-BS scenario (docs/Claude_docs/environment_design/SPARSE_WINDOW_RELAY_SCENARIO_DESIGN_20261002.md)
while costing milliseconds per episode:

* an 11 x 11 grid with the ground base station (BS) at the centre, as in scenario 2;
* four far sites in the corners, each reachable only through a relay chain of UAVs
  (link range 2 cells, access range 1 cell, at most 3 UAV hops), so a corner is served only
  when one UAV holds the single relay cell (3,3)-type position and another holds a cell
  adjacent to the corner (three-UAV chains also exist);
* timed service windows: one site is open at a time (sequence 0,1,2,3,0; 20 ticks each);
  a window pays +1 once the open site has been served for HOLD consecutive ticks inside it
  (sparse, at most 5 per episode); nothing else pays in the sparse variant;
* an optional dense decoy: +dense_decoy per UAV-tick spent within one cell of the BS
  (the deceptive "camp on the near cluster" signal);
* six UAVs, decisions every K = 10 ticks, episode T = 120 ticks (12 decisions); the
  high-level action of a UAV is a target cell (121 choices) executed by a fixed
  one-cell-per-tick executor, mirroring the project's frozen-executor practice.

Arms (all tabular softmax policies trained by REINFORCE with a per-decision baseline):

  flat         one target policy per UAV conditioned on the open site (flat PPO analog)
  flat_count   flat + count-based exploration bonus beta / sqrt(n(coarse configuration))
  hier_nodisc  team skill Z -> per-UAV skill z_i -> shared target policy; no intrinsic reward
  hier_disc    the same hierarchy + HMASD-style discriminator rewards
               lambda_D * log q(Z | coarse configuration) + lambda_d * mean_i log q(z_i | region_i, Z)
               with the project's default weights lambda_D = .05, lambda_d = .02
  hier_disc_x4 the same with four times the weights (.2 / .08)

Zero-learning references: random, sticky_random (keep the previous target w.p. .9),
stay (camp at the BS), region_random (all UAVs draw targets inside one random 3x3 region
per decision; a diagnostic of what regional concentration does to the hit rate) and
ordinary_window (knows the schedule and the chain cells; the ceiling, 5/5).

Everything is seeded explicitly. This is an instrument check, not an HMASD result: the
learners are small analogs (REINFORCE, tabular discriminators), not the project's PPO,
Transformer coordinator or learned low-level skills.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from collections import defaultdict

GRID = 11
N_CELLS = GRID * GRID
BS = (5, 5)
SITES = [(0, 0), (10, 0), (0, 10), (10, 10)]
R_LINK = 2
R_ACCESS = 1
MAX_HOPS = 3
N_UAV = 6
K = 10
T = 120
HOLD = 5
# (site, start_tick, end_tick): the site is open at ticks start <= t < end.
WINDOWS = [(0, 10, 30), (1, 30, 50), (2, 50, 70), (3, 70, 90), (0, 90, 110)]
N_STATES = len(SITES) + 1  # open site id, or 4 = no window open
N_Z = 6
N_z = 6
N_REGIONS = 9


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def cell_xy(c):
    return (c % GRID, c // GRID)


def xy_cell(p):
    return p[1] * GRID + p[0]


def region(p):
    return (p[0] * 3 // GRID) + 3 * (p[1] * 3 // GRID)


def chain_cells(site):
    """Relay cell and access cells of the unique two-UAV chain for a corner site."""
    sx, sy = site
    relay = (3 if sx == 0 else 7, 3 if sy == 0 else 7)
    access = (1 if sx == 0 else 9, 1 if sy == 0 else 9)
    return relay, access


class Env:
    def __init__(self, dense_decoy=0.0):
        self.dense_decoy = float(dense_decoy)

    def reset(self):
        self.t = 0
        self.pos = [BS] * N_UAV
        self.satisfied = [False] * len(WINDOWS)
        self.hold = 0
        self.last_window = None
        self.windows_hit = 0
        self.ext_total = 0.0
        return self.state()

    @staticmethod
    def open_window(t):
        for idx, (_, a, b) in enumerate(WINDOWS):
            if a <= t < b:
                return idx
        return None

    def state(self):
        w = self.open_window(self.t)
        return N_STATES - 1 if w is None else WINDOWS[w][0]

    def served(self, site):
        bs_linked = [i for i in range(N_UAV) if cheb(self.pos[i], BS) <= R_LINK]
        reach = set(bs_linked)
        frontier = list(bs_linked)
        for _ in range(MAX_HOPS - 1):
            nxt = []
            for i in frontier:
                for j in range(N_UAV):
                    if j not in reach and cheb(self.pos[i], self.pos[j]) <= R_LINK:
                        reach.add(j)
                        nxt.append(j)
            frontier = nxt
            if not frontier:
                break
        s = SITES[site]
        return any(cheb(self.pos[j], s) <= R_ACCESS for j in reach)

    def decide(self, targets):
        """Execute one K-tick segment toward the given target cells; return extrinsic reward."""
        ext = 0.0
        for _ in range(K):
            for i in range(N_UAV):
                tx, ty = cell_xy(targets[i])
                x, y = self.pos[i]
                x += (tx > x) - (tx < x)
                y += (ty > y) - (ty < y)
                self.pos[i] = (x, y)
            self.t += 1
            w = self.open_window(self.t)
            if w != self.last_window:
                self.hold = 0
                self.last_window = w
            if w is not None and not self.satisfied[w]:
                if self.served(WINDOWS[w][0]):
                    self.hold += 1
                    if self.hold >= HOLD:
                        self.satisfied[w] = True
                        self.windows_hit += 1
                        ext += 1.0
                else:
                    self.hold = 0
            if self.dense_decoy:
                ext += self.dense_decoy * sum(1 for p in self.pos if cheb(p, BS) <= 1)
        self.ext_total += ext
        return ext

    def coarse_key(self):
        counts = [0] * N_REGIONS
        for p in self.pos:
            counts[region(p)] += 1
        return tuple(counts)

    def regions(self):
        return [region(p) for p in self.pos]


# ----------------------------------------------------------------------------- utilities

def softmax(logits):
    m = max(logits)
    e = [math.exp(v - m) for v in logits]
    s = sum(e)
    return [v / s for v in e]


def sample(probs, rng):
    r = rng.random()
    acc = 0.0
    for i, p in enumerate(probs):
        acc += p
        if r < acc:
            return i
    return len(probs) - 1


def zeros(n):
    return [0.0] * n


# ----------------------------------------------------------------------------- references

def run_reference(name, episodes, dense_decoy, seed):
    rng = random.Random(seed)
    env = Env(dense_decoy)
    totals, hits = [], []
    for _ in range(episodes):
        env.reset()
        targets = [xy_cell(BS)] * N_UAV
        for d in range(T // K):
            s = env.state()
            if name == "random":
                targets = [rng.randrange(N_CELLS) for _ in range(N_UAV)]
            elif name == "sticky_random":
                targets = [t if rng.random() < 0.9 else rng.randrange(N_CELLS) for t in targets]
            elif name == "stay":
                targets = [xy_cell(BS)] * N_UAV
            elif name == "region_random":
                r = rng.randrange(N_REGIONS)
                cells = [c for c in range(N_CELLS) if region(cell_xy(c)) == r]
                targets = [rng.choice(cells) for _ in range(N_UAV)]
            elif name == "ordinary_window":
                targets = [xy_cell(BS)] * N_UAV
                if s < len(SITES):
                    relay, access = chain_cells(SITES[s])
                    order = sorted(range(N_UAV), key=lambda i: cheb(env.pos[i], access))
                    targets[order[0]] = xy_cell(access)
                    order2 = sorted([i for i in range(N_UAV) if i != order[0]],
                                    key=lambda i: cheb(env.pos[i], relay))
                    targets[order2[0]] = xy_cell(relay)
            else:
                raise ValueError(name)
            env.decide(targets)
        totals.append(env.ext_total)
        hits.append(env.windows_hit)
    return summarize(totals, hits)


def summarize(totals, hits):
    n = len(totals)
    mean = sum(totals) / n
    var = sum((v - mean) ** 2 for v in totals) / max(1, n - 1)
    return {
        "episodes": n,
        "mean_ext": mean,
        "se_ext": math.sqrt(var / n),
        "mean_windows": sum(hits) / n,
        "frac_any_window": sum(1 for h in hits if h > 0) / n,
    }


# ----------------------------------------------------------------------------- learners

class Learner:
    """REINFORCE over tabular softmax policies; one object per (arm, seed)."""

    def __init__(self, arm, seed, lr=0.05, baseline_rate=0.02, count_beta=0.1,
                 lambda_D=0.05, lambda_d=0.02):
        self.arm = arm
        self.rng = random.Random(seed)
        self.lr = lr
        self.baseline_rate = baseline_rate
        self.count_beta = count_beta
        self.hier = arm.startswith("hier")
        if arm == "hier_nodisc":
            self.lambda_D, self.lambda_d = 0.0, 0.0
        elif arm == "hier_disc":
            self.lambda_D, self.lambda_d = lambda_D, lambda_d
        elif arm == "hier_disc_x4":
            self.lambda_D, self.lambda_d = 4 * lambda_D, 4 * lambda_d
        else:
            self.lambda_D, self.lambda_d = 0.0, 0.0
        self.use_count = arm == "flat_count"
        if self.hier:
            self.logits_Z = [zeros(N_Z) for _ in range(N_STATES)]
            self.logits_z = [[[zeros(N_z) for _ in range(N_UAV)] for _ in range(N_Z)]
                             for _ in range(N_STATES)]
            self.logits_slot = [zeros(N_CELLS) for _ in range(N_z)]
        else:
            self.logits_flat = [[zeros(N_CELLS) for _ in range(N_STATES)] for _ in range(N_UAV)]
        self.baseline = zeros(T // K)
        self.team_counts = defaultdict(lambda: zeros(N_Z))
        self.ind_counts = defaultdict(lambda: zeros(N_z))
        self.visit_counts = defaultdict(int)
        self.seen = set()  # distinct coarse configurations visited (exploration coverage)

    # -- acting
    def act(self, s):
        """Return (targets, grads, Z, zs); grads = list of (logit_vector, chosen, probs)."""
        grads = []
        if self.hier:
            pZ = softmax(self.logits_Z[s])
            Z = sample(pZ, self.rng)
            grads.append((self.logits_Z[s], Z, pZ))
            zs, targets = [], []
            for i in range(N_UAV):
                vec = self.logits_z[s][Z][i]
                pz = softmax(vec)
                z = sample(pz, self.rng)
                grads.append((vec, z, pz))
                ps = softmax(self.logits_slot[z])
                target = sample(ps, self.rng)
                grads.append((self.logits_slot[z], target, ps))
                zs.append(z)
                targets.append(target)
            return targets, grads, Z, zs
        targets = []
        for i in range(N_UAV):
            vec = self.logits_flat[i][s]
            p = softmax(vec)
            a = sample(p, self.rng)
            grads.append((vec, a, p))
            targets.append(a)
        return targets, grads, None, None

    # -- intrinsic rewards (computed on the configuration at the end of the segment)
    def intrinsic(self, env, Z, zs):
        r = 0.0
        key = env.coarse_key()
        regs = env.regions()
        self.seen.add(key)
        if self.use_count:
            self.visit_counts[key] += 1
            r += self.count_beta / math.sqrt(self.visit_counts[key])
        if self.hier and (self.lambda_D > 0 or self.lambda_d > 0):
            tc = self.team_counts[key]
            n = sum(tc)
            r += self.lambda_D * math.log((tc[Z] + 1.0) / (n + N_Z))
            acc = 0.0
            for i in range(N_UAV):
                ic = self.ind_counts[(regs[i], Z)]
                acc += math.log((ic[zs[i]] + 1.0) / (sum(ic) + N_z))
            r += self.lambda_d * acc / N_UAV
            # discriminators learn from the visited states (tabular maximum likelihood)
            tc[Z] += 1.0
            for i in range(N_UAV):
                self.ind_counts[(regs[i], Z)][zs[i]] += 1.0
        return r

    # -- learning
    def update(self, trajectory):
        """trajectory: list of (grads, reward) per decision; undiscounted returns."""
        G = 0.0
        returns = [0.0] * len(trajectory)
        for d in range(len(trajectory) - 1, -1, -1):
            G += trajectory[d][1]
            returns[d] = G
        for d, (grads, _) in enumerate(trajectory):
            adv = returns[d] - self.baseline[d]
            self.baseline[d] += self.baseline_rate * (returns[d] - self.baseline[d])
            if adv == 0.0:
                continue
            step = self.lr * adv
            for vec, chosen, probs in grads:
                for a in range(len(vec)):
                    vec[a] -= step * probs[a]
                vec[chosen] += step

    def episode(self, env):
        env.reset()
        trajectory = []
        for d in range(T // K):
            s = env.state()
            targets, grads, Z, zs = self.act(s)
            ext = env.decide(targets)
            r = ext + self.intrinsic(env, Z, zs)
            trajectory.append((grads, r))
        self.update(trajectory)
        return env.ext_total, env.windows_hit


def run_learner(arm, episodes, dense_decoy, seed, bin_size=250, final_window=500):
    env = Env(dense_decoy)
    learner = Learner(arm, seed)
    totals, hits = [], []
    for _ in range(episodes):
        tot, h = learner.episode(env)
        totals.append(tot)
        hits.append(h)
    curve = [sum(totals[i:i + bin_size]) / len(totals[i:i + bin_size])
             for i in range(0, episodes, bin_size)]
    final = summarize(totals[-final_window:], hits[-final_window:])
    return {
        "arm": arm, "seed": seed, "dense_decoy": dense_decoy, "episodes": episodes,
        "curve_bin": bin_size, "curve_mean_ext": curve,
        "final_mean_ext": final["mean_ext"], "final_se_ext": final["se_ext"],
        "final_mean_windows": final["mean_windows"], "final_frac_any_window": final["frac_any_window"],
        "all_mean_ext": sum(totals) / episodes,
        "first_rewarded_episode": next((i for i, h in enumerate(hits) if h > 0), None),
        "distinct_configs": len(learner.seen),
    }


# ----------------------------------------------------------------------------- main

REFERENCES = ["random", "sticky_random", "stay", "region_random", "ordinary_window"]
ARMS = ["flat", "flat_count", "hier_nodisc", "hier_disc", "hier_disc_x4"]


def main():
    global R_ACCESS
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=5000)
    ap.add_argument("--ref-episodes", type=int, default=2000)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--decoys", type=float, nargs="+", default=[0.0, 0.002])
    ap.add_argument("--arms", nargs="+", default=ARMS)
    ap.add_argument("--r-access", type=int, default=1,
                    help="access range in cells: 1 = needle (one two-UAV chain per corner), 2 = wider")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()
    R_ACCESS = args.r_access

    out = {"config": {
        "grid": GRID, "bs": BS, "sites": SITES, "r_link": R_LINK, "r_access": R_ACCESS,
        "max_hops": MAX_HOPS, "n_uav": N_UAV, "k": K, "t": T, "hold": HOLD, "windows": WINDOWS,
        "n_Z": N_Z, "n_z": N_z, "episodes": args.episodes, "ref_episodes": args.ref_episodes,
        "seeds": args.seeds, "decoys": args.decoys, "lr": 0.05, "baseline_rate": 0.02,
        "count_beta": 0.1, "lambda_D": 0.05, "lambda_d": 0.02,
    }, "references": [], "learners": []}

    t0 = time.time()
    for decoy in args.decoys:
        for name in REFERENCES:
            res = run_reference(name, args.ref_episodes, decoy, seed=1000)
            res.update({"name": name, "dense_decoy": decoy})
            out["references"].append(res)
            print(f"[ref] decoy={decoy} {name:16s} mean_ext={res['mean_ext']:.4f} "
                  f"windows={res['mean_windows']:.3f} any={res['frac_any_window']:.3f}", flush=True)
    for decoy in args.decoys:
        for arm in args.arms:
            for seed in args.seeds:
                t1 = time.time()
                res = run_learner(arm, args.episodes, decoy, seed)
                res["wall_seconds"] = time.time() - t1
                out["learners"].append(res)
                print(f"[learn] decoy={decoy} {arm:13s} seed={seed} final_ext={res['final_mean_ext']:.3f} "
                      f"windows={res['final_mean_windows']:.3f} any={res['final_frac_any_window']:.3f} "
                      f"first_hit={res['first_rewarded_episode']} ({res['wall_seconds']:.0f}s)", flush=True)
                with open(args.out, "w") as f:
                    json.dump(out, f, indent=1)
    out["total_wall_seconds"] = time.time() - t0
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"done in {out['total_wall_seconds']:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
