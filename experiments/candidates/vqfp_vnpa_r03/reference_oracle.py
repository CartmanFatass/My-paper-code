"""Small fixture-only oracle; never imported by the production entry point."""

from __future__ import annotations

from fractions import Fraction as F

MASK=(1<<32)-1; M0=0xD2511F53; M1=0xCD9E8D57; W0=0x9E3779B9; W1=0xBB67AE85


def philox(root: int, counter: tuple[int,int,int,int]) -> tuple[int,int,int,int]:
    x=list(counter); k0=root&MASK; k1=(root>>32)&MASK
    for round_index in range(10):
        p0=M0*x[0];p1=M1*x[2]
        x=[((p1>>32)^x[1]^k0)&MASK,p1&MASK,((p0>>32)^x[3]^k1)&MASK,p0&MASK]
        if round_index<9:k0=(k0+W0)&MASK;k1=(k1+W1)&MASK
    return tuple(x)


def uniform(root:int,c1:int,c2:int,c3:int,m:int,max_rho:int=1<<20)->tuple[int,int]:
    limit=(1<<32)-((1<<32)%m)
    for rho in range(max_rho+1):
        u=philox(root,(rho//4,c1,c2,c3))[rho%4]
        if u<limit:return u%m,rho
    raise RuntimeError("RNG_ADDRESS_EXHAUSTED")


def _geometry(offsets:tuple[int,...]):
    n=len(offsets);x=[F(192*(2*(i+1)-1)+s,384*n) for i,s in enumerate(offsets)]
    left=[F(0) if i==0 else (x[i-1]+x[i])/2 for i in range(n)]
    right=[F(1) if i==n-1 else (x[i]+x[i+1])/2 for i in range(n)]
    return x,left,right,[r-l for l,r in zip(left,right)]


def _anti(x:F,b:F,g:F)->F:return x+b*(x*x-x)+g*(3*x*x-2*x*x*x-x)
def _lr(weights:list[F])->list[int]:
    total=sum(weights,F());q=[120*w/total for w in weights];n=[x.numerator//x.denominator for x in q]
    order=sorted(range(len(q)),key=lambda i:(-(q[i]-n[i]),i))
    for i in order[:120-sum(n)]:n[i]+=1
    return n
def _treatment(v,d,db,th):return [vi*(1+(th[0]+th[1]*di+th[2]*db+th[3]*(di-db)**2)**2) for vi,di in zip(v,d)]
def _free(v,d,db,th,ph):
    base=_treatment(v,d,db,th);out=[]
    for vi,di,bi in zip(v,d,base):
        z=len(v)*vi-1;r=ph[0]+ph[1]*(di-db)+ph[2]*z+ph[3]*(di-db)*z;r=max(F(-1,2),min(F(1,2),r));out.append(bi*(1+r)**2)
    return out


def fixture_audit()->bytes:
    rows=[]
    for root in (0,202608230200,202608232004):rows.append(f"P|{root}|"+",".join(map(str,philox(root,(0,1,2,0x10000003)))))
    u,rho=uniform(202608230200,1,2,0x01000000,129,64);rows.append(f"U|{u}|{rho}")
    _,left,right,v=_geometry((-48,24,0,48));th=(F(1,2),F(-1,4),F(0),F(1,16));ph=(F(0),F(1,8),F(-1,16),F(1,32));zero=(F(0),)*4
    for h in range(6):
        beta=F(h//2-1,4);gamma=F(h%2,4);m=[_anti(r,beta,gamma)-_anti(l,beta,gamma) for l,r in zip(left,right)];d=[mi/vi for mi,vi in zip(m,v)];db=sum(d,F())/len(d)
        nt=_lr(_treatment(v,d,db,th));nf=_lr(_free(v,d,db,th,ph));ne=_lr(_free(v,d,db,th,zero))
        rows.append(f"H|{h}|{','.join(map(str,nt))}|{','.join(map(str,nf))}|{','.join(map(str,ne))}|{int(nt==ne)}")
    ordering=sorted([(F(1,3),(0,0,0,0),0),(F(1,2),(1,0,0,0),2),(F(1,2),(0,1,0,0),1),(F(1,2),(0,1,0,0),3)],key=lambda r:(-r[0],r[1],r[2]))
    rows.append("ORDER|"+"|".join(str(x[2]) for x in ordering));rows.append("COUNTS|2048|2048|32|768|3072|24576|10|20000|491520000")
    a=F(6277101735386680763835789423207666416102355444464034512895,340282366920938463463374607431768211455)
    b=F(-1606938044258990275541962092341162602522202993782792835301499,1361129467683753853853498429727072845829)
    def canonical(value:F)->str:return f"{value.numerator}/{value.denominator}"
    rows.insert(-1,f"BIG|{canonical(a+b)}|{canonical(a*b)}|{int(a<b)}")
    return ("\n".join(rows)+"\n").encode()


def _canonical(value: F) -> str:
    return f"{value.numerator}/{value.denominator}"


def _stage_next(current: int, draw: int) -> int:
    if draw < 5:
        return current
    other = draw - 5
    return other + 1 if other >= current else other


def _stage_coeff(candidate: int) -> tuple[int, int, int, int]:
    return (
        candidate % 17 - 8,
        (candidate * 3 + 1) % 19 - 9,
        (candidate * 5 + 2) % 23 - 11,
        (candidate * 7 + 3) % 29 - 14,
    )


def _stage_endpoint(v: list[F], m: list[F], command: list[int]) -> F:
    return sum((mi * vi / (vi + F(ni, 600)) for vi, mi, ni in zip(v, m, command)), F())


def _stage_oracle(v: list[F], m: list[F]) -> list[int]:
    records = []
    for i, (vi, mi) in enumerate(zip(v, m)):
        for k in range(120):
            delta = mi * vi / (vi + F(k, 600)) - mi * vi / (vi + F(k + 1, 600))
            records.append((delta, i, k))
    records.sort(key=lambda row: (-row[0], row[1], row[2]))
    command = [0] * len(v)
    for _, i, _ in records[:120]:
        command[i] += 1
    return command


def _stage_score(arm: int, roster: int, block: int, episode: int) -> int:
    return (arm * 97 + roster * 31 + block * 17 + episode * 13 + (arm + 1) * (episode % 7)) % 1009 - 504


def _stage_draw(q: int) -> tuple[F, ...]:
    outputs: list[F] = []
    by_measure: list[list[list[F]]] = [[], []]
    for roster_index, roster in enumerate((6, 12)):
        per_arm_j: list[F] = []
        per_arm_r: list[F] = []
        for arm in range(10):
            sum_j = 0
            sum_r = 0
            for occurrence in range(12):
                source = (q * 29 + occurrence * 7 + 11) % 12
                sampled: list[tuple[int, int, int]] = []
                occurrence_sum = 0
                for h in range(6):
                    for p in range(12):
                        source_episode = h + 6 * ((q * 43 + occurrence * 19 + roster_index * 5 + p * 11) % 12)
                        value = _stage_score(arm, roster, source, source_episode)
                        occurrence_sum += value
                        sampled.append((value, source_episode, p + 12 * h))
                sampled.sort()
                sum_j += occurrence_sum
                sum_r += sum(value for value, _, _ in sampled[:18])
            per_arm_j.append(F(sum_j, 12 * 72))
            per_arm_r.append(F(sum_r, 12 * 18))
        by_measure[0].append(per_arm_j)
        by_measure[1].append(per_arm_r)
    for measure in by_measure:
        # Transpose roster-major reference values to arm-major values.
        values = [[measure[ni][arm] for ni in range(2)] for arm in range(10)]
        v = min(values[0][ni] - values[base][ni] for base in range(4, 8) for ni in range(2))
        f = min(values[0][ni] - values[1][ni] for ni in range(2))
        a = min(values[0][ni] - values[2][ni] for ni in range(2))
        p = min(values[1][ni] - values[0][ni] for ni in range(2))
        g = max(min(values[base][ni] - values[0][ni] for ni in range(2)) for base in range(4, 8))
        h = min(values[8][ni] - values[4][ni] for ni in range(2))
        outputs.extend((v, f, a, p, g, h))
    return tuple(outputs)


def stage_literal_audit(*, host_episodes: int, candidates: int, draws: int) -> bytes:
    """Independent literal oracle for proof-sized stage-R01 equality checks."""
    hosts = []
    rows = ["VQFP-VNPA-R03-STAGE-R01-SYNTHETIC-V1"]
    rosters = (4, 6, 8, 12)
    for episode in range(host_episodes):
        roster = rosters[episode % 4]
        offsets = [-48 + 24 * ((episode * 11 + i * 7 + 3) % 5) for i in range(roster)]
        offsets[0] = -48
        offsets[-1] = 48
        _, left, right, v = _geometry(tuple(offsets))
        counts = [0] * 6
        tape = []
        state = episode % 6
        for step in range(32):
            tape.append(state)
            counts[state] += 1
            state = _stage_next(state, (episode * 13 + step * 7 + 3) % 10)
        hosts.append((roster, left, right, v, counts))
        rows.append(f"H|{episode}|{roster}|{','.join(map(str, offsets))}|{','.join(map(str, counts))}|{','.join(map(str, tape))}")
    candidate_rows = []
    for candidate in range(candidates):
        coefficient = _stage_coeff(candidate)
        theta = tuple(F(x, 16) for x in coefficient)
        phi = tuple(F(x, 16) for x in _stage_coeff(candidate + 37))
        aggregate = F()
        for roster, left, right, v, counts in hosts:
            for state, count in enumerate(counts):
                if not count:
                    continue
                beta, gamma = F(state // 2 - 1, 4), F(state % 2, 4)
                m = [_anti(r, beta, gamma) - _anti(l, beta, gamma) for l, r in zip(left, right)]
                d = [mi / vi for mi, vi in zip(m, v)]
                dbar = sum(d, F()) / roster
                nt = _lr(_treatment(v, d, dbar, theta))
                nf = _lr(_free(v, d, dbar, theta, phi))
                nd, nm = _lr(d), _lr(m)
                nmar = _lr([mi / (600 * vi + 1) for mi, vi in zip(m, v)])
                no = _stage_oracle(v, m)
                u = sum((_stage_endpoint(v, m, command) for command in (nt, nf, nd, nm, nmar, no)), F())
                aggregate += (6 - u) * count
        candidate_rows.append((aggregate, coefficient, candidate))
        rows.append(f"C|{candidate}|{','.join(map(str, coefficient))}|{_canonical(aggregate)}")
    order = sorted(candidate_rows, key=lambda row: (-row[0], row[1], row[2]))
    rows.append("ORDER|" + "|".join(str(row[2]) for row in order))
    all_draws = [_stage_draw(q) for q in range(draws)]
    lo, hi = draws // 40, draws - 1 - draws // 40
    for composite in range(12):
        values = sorted((row[composite], q) for q, row in enumerate(all_draws))
        rows.append(f"R|{composite}|{_canonical(values[lo][0])}|{_canonical(values[hi][0])}")
    return ("\n".join(rows) + "\n").encode()
