Disposition

The frozen proposal does not survive as one coherent, meaning-preserving correction.

The smallest decisive defect is the change of estimand introduced by the sample-size-two selectors. Cross-fitting successfully prevents a tape from both selecting and evaluating an action, but it identifies the held-out value of actions chosen by noisy finite-tape selectors. It does not identify the value of the true conditional-mean-maximizing actions. In particular:

corrected D can be positive when one action is uniquely optimal in both graphs;

corrected Q can be positive when the true optimal-action sets coincide;

corrected Q can be zero when those true optimal-action sets are disjoint.

The independent-product initial-state law is also not derived from the antecedent card. It is an internally coherent new population choice, but it is separate from the estimator repair. Thus the candidate crosses the one-correction boundary on two logically independent coordinates.

This is a definition-level rejection, not an empirical no-opportunity result.

1. What is coherent and survives

The support-graph intervention itself is coherent.

Starting from p=(1,2,3,4),

R(H(p))=R(2,1,3,4)=(4,2,1,3),

and

H(R(p))=H(4,1,2,3)=(1,4,2,3).

The common sentinel is stipulated not to alter p, so the two first-renewal potential-outcome worlds can share their public state while differing in the latent support assignment. Pairing the same state and future disturbance tape across graphs and actions then defines a clean simulator intervention U
q
	​

(a,w). The repository card confirms the marginal initial-state declarations, the public first-renewal alias, the event maps, and the simulator-only scope. 
GitHub

The cross-fit construction also has one exact and useful property. Conditional on a selection fold Z, if 
a
(Z) is any selected action and Z
′
 is the independent evaluation fold,

E[
V
Z
′
	​

(
a
(Z))∣Z]=V(
a
(Z)).

Thus held-out evaluation is unbiased for the true value of the action that the selector actually returned. No evaluation optimism from tape reuse remains.

That is the useful lemma. It is not, however, an oracle-maximization lemma.

2. The exact estimand mismatch

At a fixed public state, let

V
q
	​

(a)=E
W
	​

[U(q,a,W)]

be the true conditional full-mission value, and define

V
ˉ
(a)=
2
V
0
	​

(a)+V
1
	​

(a)
	​

.

The intended oracle advantage is

D
⋆
=
2
1
	​

[
a
max
	​

V
0
	​

(a)+
a
max
	​

V
1
	​

(a)]−
a
max
	​

V
ˉ
(a).

Let the two-tape selection fold return graph-specific actions

a
0
	​

,
a
1
	​

 and pooled action 
a
c
	​

.
After averaging out the independent held-out fold, the corrected law instead targets

D
cf
	​

=E
sel
	​

[
2
V
0
	​

(
a
0
	​

)+V
1
	​

(
a
1
	​

)
	​

−
V
ˉ
(
a
c
	​

)].

Define selector regrets

r
q
	​

=
a
max
	​

V
q
	​

(a)−E
sel
	​

V
q
	​

(
a
q
	​

)≥0

and

r
c
	​

=
a
max
	​

V
ˉ
(a)−E
sel
	​

V
ˉ
(
a
c
	​

)≥0.

Then the exact relation is

D
cf
	​

=D
⋆
−
2
r
0
	​

+r
1
	​

	​

+r
c
	​

.
	​


Consequently, equality with the intended oracle requires

r
c
	​

=
2
r
0
	​

+r
1
	​

	​

,

or some stronger condition such as all three selectors choosing true optimizers almost surely. Neither condition follows from cross-fitting, from two tapes per fold, from common random numbers, or from the frozen plant law.

This is not a small-sample approximation to the same estimand. It is a different physical/statistical question: whether the pooled two-tape selector suffers more or less regret than the two graph-specific two-tape selectors.

For S, the situation is less damaging but still distinct. If 
a
q
+
	​

 and 
a
q
−
	​

 are the selection-fold maximum and minimum,

S
cf
	​

=
2
1
	​

q
∑
	​

E[V
q
	​

(
a
q
+
	​

)−V
q
	​

(
a
q
−
	​

)].

Because a selected action cannot have true value above the true maximum or below the true minimum,

S
cf
	​

≤S
⋆
=
2
1
	​

q
∑
	​

[
a
max
	​

V
q
	​

(a)−
a
min
	​

V
q
	​

(a)].

So a positive population lower bound on S
cf
	​

 is conservative evidence of action sensitivity. But the per-fold quantity can be negative: the action labeled “maximum” from the selection fold can be worse on true value than the action labeled “minimum.” The displayed −0.52 case is therefore material, not an arithmetic mistake.

No analogous ordering exists for D, and there is no useful equivalence for Q.

3. Calculation audit
Initial-state copula

The card lists

v∼U[0,0.03],y∼U[−0.01,0.01],ϕ∼U[−0.01,0.01],

but states only that initial draws are paired across controllers. By contrast, the later three disturbance coordinates are explicitly described as independently equiprobable. There is no global statement making the three initial coordinates mutually independent. 
GitHub
+1

For unit-uniform coordinates,

f
θ
	​

(u
v
	​

,u
y
	​

,u
ϕ
	​

)=1+θ(1−2u
y
	​

)(1−2u
ϕ
	​

),0<∣θ∣<1,

is strictly positive because f
θ
	​

≥1−∣θ∣>0. Its u
y
	​

 and u
ϕ
	​

 marginal perturbations integrate to zero, while

E
θ
	​

[u
y
	​

u
ϕ
	​

]
	​

=
4
1
	​

+θ(∫
0
1
	​

u(1−2u)du)
2
=
4
1
	​

+
36
θ
	​

.
	​


That displayed calculation is correct. The product measure is therefore one member of a non-singleton family with the named marginals, not a consequence of those marginals.

Equal-value witness

For independent

K
12
	​

,K
34
	​

∼Binomial(2,
2
1
	​

),
E[K
12
	​

−1]=E[K
34
	​

−1]=0.

Hence

E[(K
12
	​

−1)(K
34
	​

−1)]=0,

and the displayed expectations of

D=
4
(K
12
	​

−1)(K
34
	​

−1)
	​

,S=
2
(K
12
	​

−1)(K
34
	​

−1)
	​


are zero. The supplied witness’s Q=0 is also preserved.

The general lemma is only that equal true action means force population D
cf
	​

=S
cf
	​

=0. It does not generally force the candidate Q to zero, because Q thresholds finite held-out sample inequalities rather than true means.

The R/C counterexample

The stated true means are correct:

V
0
	​

(a
0
	​

,a
1
	​

,a
2
	​

)=(0.64,0.42,0.28),
V
1
	​

(a
0
	​

,a
1
	​

,a
2
	​

)=(0.86,0.18,0.60).

With all other actions at 0.5, a
0
	​

 is uniquely optimal in both graphs and uniquely maximizes the graph-average value.

The selection-fold probabilities are

P(RR)=
25
1
	​

,P(mixed)=
25
8
	​

,P(CC)=
25
16
	​

.

For a mixed selection fold the graph selectors are a
1
	​

 and a
0
	​

, while the pooled selector is a
2
	​

. The bilateral held-out comparison fails only on an RR evaluation fold, so

Q=
25
8
	​

25
24
	​

=
625
192
	​

=0.3072.

The held-out true-value D cases are −0.07,0.20,0, giving

D=
25
1
	​

(−0.07)+
25
8
	​

(0.20)=
2500
153
	​

=0.0612.

The S cases are −0.52,0.23,0.52, giving

S=
25
1
	​

(−0.52)+
25
8
	​

(0.23)+
25
16
	​

(0.52)=
625
241
	​

=0.3856.

All those displayed calculations are correct. Swapping the folds leaves their population expectations unchanged.

Also correct is the conversion

0.025×36.4 s=0.91 s.
4. The original numerical counterexample has a support defect—but it can be removed

The values in the original table are not literally all available under this simulator’s U.

Since v
′
≤1.6,

x
n
	​

≤0.16n.

Starting from x=0, docking at x≥24.5 requires at least

n≥⌈
0.16
24.5
	​

⌉=154.

Therefore any nonzero completion value satisfies

U=1−
364
n
	​

≤
364
210
	​

≈0.5769,

and every nonzero U lies on the 1/364 grid. Values 0.6,0.8,0.9,1 are consequently outside the literal scalar support.

There is a second exact-support issue: a complete horizon tape consists of finitely many independent fair binary disturbance coordinates. An event determined by that tape has dyadic probability, whereas 1/5 is not dyadic.

These observations prevent the original table from being claimed as an exact plant realization. They do not rescue the selector law. A support-matched version retains the counterexample.

Let R have probability 1/4, for example by defining it from one designated outcome of two fair disturbance bits. Let all entries below be divided by 364:

action	graph 0, R	graph 0, C	graph 1, R	graph 1, C
a
0
	​

	0	146	55	182
a
1
	​

	164	55	164	0
a
2
	​

	182	18	109	109
every other action	91	91	91	91

Every nonzero entry is an exact admissible U-grid value, the largest is 182/364=0.5, and the same tape type is shared across graphs and actions.

The true means are approximately

V
0
	​

=(0.300824, 0.225962, 0.162088),
V
1
	​

=(0.412775, 0.112637, 0.299451),

with every other action equal to 0.25. Thus a
0
	​

 remains uniquely optimal in both graphs and uniquely optimal in graph-average value; the oracle graph-specific advantage and oracle disjointness indicator are both zero.

The selection patterns remain the same. The corrected population quantities become

Q
cf
	​

=
8
3
	​

16
15
	​

=
128
45
	​

≈0.35156,
D
cf
	​

=
46592
1455
	​

≈0.03123,
S
cf
	​

=
5824
885
	​

≈0.15196.

They still exceed 0.20, 0.025, and 0.060.

This version respects the explicit scalar-value grid, the elementary speed envelope, the fair-bit tape probabilities, boundedness, and shared-tape coupling. I do not claim that the frozen numerical dynamics have been constructively proved to realize this exact table. Conversely, the card contains no rank-invariance, monotone-action-ordering, or selector-consistency theorem that excludes it. Therefore no algebraic identity between the corrected functional and the oracle functional follows from the frozen simulator restrictions.

5. Q is bidirectionally non-equivalent to optimal-set disjointness

The preceding example gives

Q
⋆
=0,Q
cf
	​

>0.35.

The opposite direction also holds within the scalar support. Scale the deterministic example to

V
0
	​

(a
0
	​

,a
1
	​

)=(0.5,0),V
1
	​

(a
0
	​

,a
1
	​

)=(0,0.5).

Then the graph-specific optimal sets are disjoint, and

D
⋆
=0.25,Q
⋆
=1.

But either lexicographically selected common action equals one graph’s selected optimum. In that graph, the required strict held-out superiority over the common action is impossible. Hence

Q
cf
	​

=0.

So corrected Q is neither a lower bound nor an upper bound on prevalence of disjoint true optimal-action sets. It measures a different event:

two noisy graph-specific selectors return different actions, and each selected action beats the noisy pooled selector on another two tapes.

That event may be scientifically definable, but it is not the intended oracle disjointness property.

6. The product state law is a second, independent correction

The independent product law is internally single-valued and graph-invariant once explicitly adopted. It is nevertheless not derived from the antecedent mission law.

A deterministic pushforward does not fill in a missing copula. Here the first-renewal public state retains the relevant public plant coordinates; the setup aliases them across q but does not erase their joint distribution. The card’s separate marginal declarations therefore induce multiple possible first-renewal populations. 
GitHub
+1

The two changes are independent:

Holding the state population fixed, replacing same-tape extrema by split-fold selectors changes the statistical functional.

Holding the selector law fixed, replacing an unspecified copula by the product copula changes the population measure over which that functional is averaged.

No equality or causal identity joins those operations. Calling both “the opportunity-law correction” does not make them one meaning-preserving correction.

Even granting the product population would not cure the selector estimand. Even curing the selector estimand would not derive the product population.

7. Remaining scientific interpretation and claim ceiling

The remaining coherent interpretation is a new finite-selector assay under a newly adopted product population:

Compare the true held-out values of graph-specific actions selected from two disturbance tapes against the true held-out value of a pooled action selected from those same two selection tapes, and measure the probability of bilateral strict wins on two additional tapes.

Cross-fitting validly identifies that finite-selector functional. The equal-value D/S lemma remains useful, and S
cf
	​

 remains conservative for true action range. But that functional cannot be called the intended graph-specific oracle first-action opportunity.

The disposition does not imply:

that the frozen simulator lacks graph-specific first-action opportunity;

that the foundation would fail or pass competence;

that a common action is actually optimal in the numerical plant;

that any adapter would fail or succeed;

a bounded empirical no-opportunity result;

any result about general chronology, semigroup composition, arbitrary hold periods, variable populations, real aircraft, safety, deployment, or flight.

The repository object is still definition-only and records that scientific activity and the relevant execution authorities have not begun. 
GitHub

Finally, the cited literature supports only the broad plausibility of rigid cable-suspended multi-quadrotor dynamics and unilateral tension, formation and disturbance control, suspension-failure reassignment, and sampled-data analysis. It supplies no validation of this simulator’s event maps, incidence vectors, numerical plant, state copula, catalogue, thresholds, or selector functional. 
ScienceDirect
+3
Robotics Proceedings
+3
AIST Staff
+3

Narrow final disposition: the graph intervention and held-out evaluation mechanism are coherent, but no single meaning-preserving corrected opportunity law survives. The decisive failure is the substitution of a two-tape selector-performance functional for the intended true-mean oracle opportunity; the independent-product state law is additionally a separate population choice, so the proposal cannot satisfy the one-correction boundary.