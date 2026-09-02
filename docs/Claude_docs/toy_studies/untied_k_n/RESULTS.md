# Untied-k / untied-N toy study

Standalone numpy-only numerical study. Every random draw is seeded explicitly, so rerunning `untied_toys.py` reproduces these numbers exactly.

## Part K1 - commitment vs reactivity vs identifiability as a function of skill duration k

### K1(i) Commitment loss

Computed: C(k, lambda) = (1/k) * sum_{t=0}^{k-1} (1-lambda)^t, the expected fraction of the k committed steps during which the goal that was current at skill-selection time is still current; the latent goal switches each step with hazard lambda. Exact, no sampling. k in [1, 2, 3, 5, 7, 9, 13, 20, 40], lambda in [0.005, 0.02, 0.05, 0.1, 0.2].

| k | lambda=0.005 | lambda=0.02 | lambda=0.05 | lambda=0.1 | lambda=0.2 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 2 | 0.9975 | 0.9900 | 0.9750 | 0.9500 | 0.9000 |
| 3 | 0.9950 | 0.9801 | 0.9508 | 0.9033 | 0.8133 |
| 5 | 0.9900 | 0.9608 | 0.9049 | 0.8190 | 0.6723 |
| 7 | 0.9851 | 0.9420 | 0.8619 | 0.7453 | 0.5645 |
| 9 | 0.9802 | 0.9236 | 0.8217 | 0.6806 | 0.4810 |
| 13 | 0.9705 | 0.8884 | 0.7487 | 0.5737 | 0.3635 |
| 20 | 0.9539 | 0.8310 | 0.6415 | 0.4392 | 0.2471 |
| 40 | 0.9084 | 0.6929 | 0.4357 | 0.2463 | 0.1250 |

### K1(ii) Identifiability

Computed: Monte-Carlo estimate of Bayes-optimal accuracy A(k) for identifying which of M skills generated a k-step segment. Skill z has drift mu_z on a circle of radius r=1 (M drifts evenly spaced); each step displacement = mu_z + sigma*N(0, I_2). The k-step sum is sufficient: sum ~ N(k*mu_z, k*sigma^2 I), so the Bayes rule under a uniform prior is argmax_z <sum, mu_z> (valid because all ||mu_z|| are equal). 20000 segments per setting, fixed per-setting seeds. M in [4, 8], sigma in [1, 2, 4], k in [1, 2, 3, 5, 7, 9, 13, 20, 40].

| k | M=4, sig=1 | M=4, sig=2 | M=4, sig=4 | M=8, sig=1 | M=8, sig=2 | M=8, sig=4 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.5812 | 0.4145 | 0.3247 | 0.3250 | 0.2174 | 0.1689 |
| 2 | 0.7175 | 0.4789 | 0.3569 | 0.4189 | 0.2571 | 0.1855 |
| 3 | 0.7908 | 0.5275 | 0.3847 | 0.5013 | 0.2962 | 0.2024 |
| 5 | 0.8868 | 0.6118 | 0.4346 | 0.6102 | 0.3523 | 0.2326 |
| 7 | 0.9401 | 0.6810 | 0.4657 | 0.6836 | 0.4042 | 0.2502 |
| 9 | 0.9683 | 0.7277 | 0.4896 | 0.7492 | 0.4438 | 0.2661 |
| 13 | 0.9881 | 0.8137 | 0.5436 | 0.8295 | 0.5091 | 0.3026 |
| 20 | 0.9983 | 0.8903 | 0.6115 | 0.9162 | 0.6106 | 0.3520 |
| 40 | 1.0000 | 0.9737 | 0.7530 | 0.9834 | 0.7728 | 0.4627 |

Chance level: M=4 -> 0.2500, M=8 -> 0.1250. Maximum MC standard error at n=20000 is 0.5/sqrt(n) = 0.0035.

### K1(iii) Combined per-step score and argmax k*

Computed: J(k) = C(k, lambda) * A(k) on the same k grid; each cell reports the grid argmax k* and the value J(k*). C is exact, A is the MC estimate from K1(ii), so k* inherits that MC noise. Rows = (M, sigma), columns = lambda. k grid = [1, 2, 3, 5, 7, 9, 13, 20, 40].

| M, sigma | lambda=0.005 | lambda=0.02 | lambda=0.05 | lambda=0.1 | lambda=0.2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| M=4, sig=1 | k*=13 (J=0.9590) | k*=9 (J=0.8943) | k*=7 (J=0.8103) | k*=5 (J=0.7263) | k*=2 (J=0.6457) |
| M=4, sig=2 | k*=40 (J=0.8845) | k*=20 (J=0.7398) | k*=13 (J=0.6093) | k*=7 (J=0.5075) | k*=2 (J=0.4310) |
| M=4, sig=4 | k*=40 (J=0.6840) | k*=40 (J=0.5217) | k*=13 (J=0.4070) | k*=5 (J=0.3559) | k*=1 (J=0.3247) |
| M=8, sig=1 | k*=40 (J=0.8933) | k*=20 (J=0.7613) | k*=13 (J=0.6210) | k*=9 (J=0.5099) | k*=5 (J=0.4102) |
| M=8, sig=2 | k*=40 (J=0.7020) | k*=40 (J=0.5355) | k*=20 (J=0.3917) | k*=9 (J=0.3021) | k*=3 (J=0.2409) |
| M=8, sig=4 | k*=40 (J=0.4203) | k*=40 (J=0.3206) | k*=13 (J=0.2266) | k*=5 (J=0.1905) | k*=1 (J=0.1689) |

In 8 of the 30 cells the argmax lands on the largest grid point (k=40), so k* is right-censored by the grid there.

## Part K2 - composed (semigroup-consistent) vs direct multi-horizon prediction

Setup shared by every K2 table: d=4 state. LINEAR x_{t+1} = A x_t + w_t with A = 0.95 * blockdiag(Rot(0.3), Rot(0.7)); NONLINEAR x_{t+1} = tanh(A' x_t) + w_t with A' = 1.6 * the same block rotation; w_t ~ N(0, 0.1^2 I). x_0 ~ N(0, I), trajectory length 40, one uniformly random origin t0 in [0, 26] per trajectory (so t0 + 13 <= 39); n_train training origin pairs, 5000 test origin pairs (the test set is fixed per dynamics and shared by both n_train). Feature map: [x, 1] linear, [x, x^2, 1] nonlinear. All fits are ordinary least squares with ridge 1e-6. COMPOSED = one-step fit composed k times. DIRECT-k = one regressor per k in K_train; at a held-out k the mean of the two nearest trained k, at an extrapolation k the nearest trained k (k=9). DIRECT-k-as-input = one regressor on [x, k*x, k^2*x, 1, k, k^2] (with the x^2 terms added in the nonlinear case) trained jointly on all of K_train. Metric: normalized MSE = MSE / Var(x_{t+k}) averaged over the 4 coordinates (1.0 = no better than predicting the marginal mean). Column groups: T = trained (K_train {1,3,5,7,9}), H = held-out interior (K_held {2,4,6,8}), E = extrapolation (K_ext {11,13}).

### K2 LINEAR dynamics, n_train = 200 origin pairs

Computed: normalized MSE per model and per horizon k for the linear system, n_train = 200 training origin pairs, 5000 test origin pairs.

| model | k=1 (T) | k=2 (H) | k=3 (T) | k=4 (H) | k=5 (T) | k=6 (H) | k=7 (T) | k=8 (H) | k=9 (T) | k=11 (E) | k=13 (E) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| COMPOSED | 0.0262 | 0.0544 | 0.0826 | 0.1125 | 0.1444 | 0.1752 | 0.2084 | 0.2428 | 0.2757 | 0.3444 | 0.4173 |
| DIRECT-k | 0.0262 | 0.0843 | 0.0821 | 0.1426 | 0.1425 | 0.2008 | 0.2050 | 0.2611 | 0.2717 | 1.0663 | 2.3139 |
| DIRECT-k-as-input | 0.0639 | 0.1469 | 0.2758 | 0.2195 | 0.1702 | 0.2820 | 0.4123 | 0.3357 | 0.3209 | 5.9805 | 31.5550 |

One-step model's own normalized MSE (the k=1 fit that COMPOSED iterates): 0.0262.

DIRECT inconsistency INC = mean_x ||DIRECT_(k1+k2)(x) - DIRECT_k2(DIRECT_k1(x))|| / ||x_(t+k1+k2)|| over the 5000 test origins (k2=4 is the interpolated held-out operator; the 7- and 9-step targets are trained models): INC(3,4) = 0.1625, INC(5,4) = 0.1817. COMPOSED has INC = 0 by construction.

### K2 LINEAR dynamics, n_train = 2000 origin pairs

Computed: normalized MSE per model and per horizon k for the linear system, n_train = 2000 training origin pairs, 5000 test origin pairs.

| model | k=1 (T) | k=2 (H) | k=3 (T) | k=4 (H) | k=5 (T) | k=6 (H) | k=7 (T) | k=8 (H) | k=9 (T) | k=11 (E) | k=13 (E) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| COMPOSED | 0.0258 | 0.0531 | 0.0804 | 0.1094 | 0.1402 | 0.1700 | 0.2026 | 0.2369 | 0.2697 | 0.3380 | 0.4118 |
| DIRECT-k | 0.0258 | 0.0805 | 0.0803 | 0.1356 | 0.1394 | 0.1934 | 0.2014 | 0.2574 | 0.2685 | 1.0782 | 2.3053 |
| DIRECT-k-as-input | 0.0642 | 0.1417 | 0.2656 | 0.2080 | 0.1638 | 0.2839 | 0.4172 | 0.3370 | 0.3277 | 6.1476 | 32.2670 |

One-step model's own normalized MSE (the k=1 fit that COMPOSED iterates): 0.0258.

DIRECT inconsistency INC = mean_x ||DIRECT_(k1+k2)(x) - DIRECT_k2(DIRECT_k1(x))|| / ||x_(t+k1+k2)|| over the 5000 test origins (k2=4 is the interpolated held-out operator; the 7- and 9-step targets are trained models): INC(3,4) = 0.1488, INC(5,4) = 0.1426. COMPOSED has INC = 0 by construction.

### K2 NONLINEAR dynamics, n_train = 200 origin pairs

Computed: normalized MSE per model and per horizon k for the nonlinear system, n_train = 200 training origin pairs, 5000 test origin pairs.

| model | k=1 (T) | k=2 (H) | k=3 (T) | k=4 (H) | k=5 (T) | k=6 (H) | k=7 (T) | k=8 (H) | k=9 (T) | k=11 (E) | k=13 (E) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| COMPOSED | 0.0575 | 0.0961 | 0.1493 | 0.2014 | 0.3642 | 3.0703 | 858 | 1e+08 | 1.42e+18 | 1.12e+79 | inf |
| DIRECT-k | 0.0575 | 0.1085 | 0.1212 | 0.1539 | 0.1347 | 0.1609 | 0.1443 | 0.1889 | 0.1814 | 0.9865 | 2.1430 |
| DIRECT-k-as-input | 0.1107 | 0.1770 | 0.3133 | 0.2331 | 0.1548 | 0.2380 | 0.3331 | 0.2548 | 0.2311 | 4.8415 | 23.5730 |

One-step model's own normalized MSE (the k=1 fit that COMPOSED iterates): 0.0575.

DIRECT inconsistency INC = mean_x ||DIRECT_(k1+k2)(x) - DIRECT_k2(DIRECT_k1(x))|| / ||x_(t+k1+k2)|| over the 5000 test origins (k2=4 is the interpolated held-out operator; the 7- and 9-step targets are trained models): INC(3,4) = 0.1999, INC(5,4) = 0.1885. COMPOSED has INC = 0 by construction.

### K2 NONLINEAR dynamics, n_train = 2000 origin pairs

Computed: normalized MSE per model and per horizon k for the nonlinear system, n_train = 2000 training origin pairs, 5000 test origin pairs.

| model | k=1 (T) | k=2 (H) | k=3 (T) | k=4 (H) | k=5 (T) | k=6 (H) | k=7 (T) | k=8 (H) | k=9 (T) | k=11 (E) | k=13 (E) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| COMPOSED | 0.0549 | 0.0854 | 0.1246 | 0.1446 | 0.1621 | 0.1977 | 0.2910 | 0.9246 | 20.5784 | 1.52e+10 | 1.09e+46 |
| DIRECT-k | 0.0549 | 0.1079 | 0.1156 | 0.1496 | 0.1272 | 0.1554 | 0.1378 | 0.1840 | 0.1761 | 0.9851 | 2.1693 |
| DIRECT-k-as-input | 0.1039 | 0.1786 | 0.3128 | 0.2289 | 0.1502 | 0.2354 | 0.3317 | 0.2519 | 0.2242 | 4.8209 | 23.5135 |

One-step model's own normalized MSE (the k=1 fit that COMPOSED iterates): 0.0549.

DIRECT inconsistency INC = mean_x ||DIRECT_(k1+k2)(x) - DIRECT_k2(DIRECT_k1(x))|| / ||x_(t+k1+k2)|| over the 5000 test origins (k2=4 is the interpolated held-out operator; the 7- and 9-step targets are trained models): INC(3,4) = 0.1938, INC(5,4) = 0.1805. COMPOSED has INC = 0 by construction.

## Part N1 - coordination coverage under variable N

### N1(i) Coverage under exchangeable independent sampling

Computed: exact P(all K roles covered) = K! * S(N, K) / K^N when each of N agents independently picks one of K roles uniformly at random (a shared policy with no symmetry breaking). S is the Stirling number of the second kind, evaluated in exact integer arithmetic. K in {2,3,4,6}; N in {K, K+1, K+2, K+4, 2K, 3K, 20}; each cell shows the probability and the N it used, since the labels collide for small K.

| K | N=K | N=K+1 | N=K+2 | N=K+4 | N=2K | N=3K | N=20 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 0.500000 (N=2) | 0.750000 (N=3) | 0.875000 (N=4) | 0.968750 (N=6) | 0.875000 (N=4) | 0.968750 (N=6) | 0.999998 (N=20) |
| 3 | 0.222222 (N=3) | 0.444444 (N=4) | 0.617284 (N=5) | 0.825789 (N=7) | 0.740741 (N=6) | 0.922116 (N=9) | 0.999098 (N=20) |
| 4 | 0.093750 (N=4) | 0.234375 (N=5) | 0.380859 (N=6) | 0.622925 (N=8) | 0.622925 (N=8) | 0.874759 (N=12) | 0.987321 (N=20) |
| 6 | 0.015432 (N=6) | 0.054012 (N=7) | 0.114026 (N=8) | 0.271812 (N=10) | 0.437816 (N=12) | 0.784707 (N=18) | 0.847988 (N=20) |

Monte-Carlo check of one row (K=4, N=8; 200000 independent samples, seed 4242): exact = 0.622925, MC = 0.621860, difference = -0.001065, MC standard error = 0.001084 (0.98 SE).

### N1(ii) Size of a team-skill index space

Computed: exact sizes of the joint assignment space K^N (agent-identified: who does what) versus the role-multiplicity / count space C(N+K-1, K-1) (agent-anonymous: how many agents per role), and their ratio. K in {3,4,8}, N in {3,5,7,9,15,21}. Exact integer arithmetic.

| K | N | K^N | C(N+K-1, K-1) | ratio K^N / count space |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 3 | 27 | 10 | 2.7 |
| 3 | 5 | 243 | 21 | 11.6 |
| 3 | 7 | 2,187 | 36 | 60.8 |
| 3 | 9 | 19,683 | 55 | 357.9 |
| 3 | 15 | 14,348,907 | 136 | 105,506.7 |
| 3 | 21 | 10,460,353,203 | 253 | 41,345,269.6 |
| 4 | 3 | 64 | 20 | 3.2 |
| 4 | 5 | 1,024 | 56 | 18.3 |
| 4 | 7 | 16,384 | 120 | 136.5 |
| 4 | 9 | 262,144 | 220 | 1,191.6 |
| 4 | 15 | 1,073,741,824 | 816 | 1,315,860.1 |
| 4 | 21 | 4,398,046,511,104 | 2,024 | 2,172,947,881.0 |
| 8 | 3 | 512 | 120 | 4.3 |
| 8 | 5 | 32,768 | 792 | 41.4 |
| 8 | 7 | 2,097,152 | 3,432 | 611.1 |
| 8 | 9 | 134,217,728 | 11,440 | 11,732.3 |
| 8 | 15 | 35,184,372,088,832 | 170,544 | 206,306,713.2 |
| 8 | 21 | 9,223,372,036,854,775,808 | 1,184,040 | 7,789,746,999,134.1 |

### N1(iii) Churn: expected roles left uncovered after removing one agent

Computed: an assignment covers all K roles with multiplicities as even as possible (N = q*K + rem, so rem roles hold q+1 agents and K-rem hold q). One agent is removed uniformly at random; a role can only become uncovered if it held exactly one agent, so E[# roles left uncovered] = (# roles with m_r = 1) / N. Exact. K in {3,4,8}, N from K to 3K; the smallest N at which the expectation is zero is marked.

**K = 3**

| N | multiplicities | # roles with m=1 | E[uncovered] | |
| ---: | --- | ---: | ---: | --- |
| 3 | 1+1+1 | 3 | 1.0000 |  |
| 4 | 2+1+1 | 2 | 0.5000 |  |
| 5 | 2+2+1 | 1 | 0.2000 |  |
| 6 | 2+2+2 | 0 | 0.0000 | <- smallest N with E = 0 |
| 7 | 3+2+2 | 0 | 0.0000 |  |
| 8 | 3+3+2 | 0 | 0.0000 |  |
| 9 | 3+3+3 | 0 | 0.0000 |  |

Smallest N with E[uncovered] = 0 for K=3: N = 6 (= 2K).

**K = 4**

| N | multiplicities | # roles with m=1 | E[uncovered] | |
| ---: | --- | ---: | ---: | --- |
| 4 | 1+1+1+1 | 4 | 1.0000 |  |
| 5 | 2+1+1+1 | 3 | 0.6000 |  |
| 6 | 2+2+1+1 | 2 | 0.3333 |  |
| 7 | 2+2+2+1 | 1 | 0.1429 |  |
| 8 | 2+2+2+2 | 0 | 0.0000 | <- smallest N with E = 0 |
| 9 | 3+2+2+2 | 0 | 0.0000 |  |
| 10 | 3+3+2+2 | 0 | 0.0000 |  |
| 11 | 3+3+3+2 | 0 | 0.0000 |  |
| 12 | 3+3+3+3 | 0 | 0.0000 |  |

Smallest N with E[uncovered] = 0 for K=4: N = 8 (= 2K).

**K = 8**

| N | multiplicities | # roles with m=1 | E[uncovered] | |
| ---: | --- | ---: | ---: | --- |
| 8 | 1+1+1+1+1+1+1+1 | 8 | 1.0000 |  |
| 9 | 2+1+1+1+1+1+1+1 | 7 | 0.7778 |  |
| 10 | 2+2+1+1+1+1+1+1 | 6 | 0.6000 |  |
| 11 | 2+2+2+1+1+1+1+1 | 5 | 0.4545 |  |
| 12 | 2+2+2+2+1+1+1+1 | 4 | 0.3333 |  |
| 13 | 2+2+2+2+2+1+1+1 | 3 | 0.2308 |  |
| 14 | 2+2+2+2+2+2+1+1 | 2 | 0.1429 |  |
| 15 | 2+2+2+2+2+2+2+1 | 1 | 0.0667 |  |
| 16 | 2+2+2+2+2+2+2+2 | 0 | 0.0000 | <- smallest N with E = 0 |
| 17 | 3+2+2+2+2+2+2+2 | 0 | 0.0000 |  |
| 18 | 3+3+2+2+2+2+2+2 | 0 | 0.0000 |  |
| 19 | 3+3+3+2+2+2+2+2 | 0 | 0.0000 |  |
| 20 | 3+3+3+3+2+2+2+2 | 0 | 0.0000 |  |
| 21 | 3+3+3+3+3+2+2+2 | 0 | 0.0000 |  |
| 22 | 3+3+3+3+3+3+2+2 | 0 | 0.0000 |  |
| 23 | 3+3+3+3+3+3+3+2 | 0 | 0.0000 |  |
| 24 | 3+3+3+3+3+3+3+3 | 0 | 0.0000 |  |

Smallest N with E[uncovered] = 0 for K=8: N = 16 (= 2K).

## Caveats

- **Monte-Carlo error, K1(ii).** Accuracies come from 20,000 segments per setting, so the standard error is at most 0.5/sqrt(20000) = 0.0035. Differences between adjacent k smaller than about 0.01 are inside noise, and the argmax k* in K1(iii) inherits that noise wherever J(k) is flat near its peak, which it often is.
- **Monte-Carlo error, N1(i) check.** The 200,000-sample check has a standard error near 0.001; it verifies the closed form rather than measuring anything independently.
- **Feature-map choice, K2.** The linear system's map [x, 1] contains the true one-step model, so COMPOSED is correctly specified there up to estimation error. The nonlinear map [x, x^2, 1] does not contain tanh, so every nonlinear model is misspecified; COMPOSED's nonlinear numbers are about compounding a *biased* one-step model, not about compounding estimation noise alone. A different feature map would move the nonlinear tables much more than the linear ones.
- **Composing a quadratic map.** With the nonlinear feature map, composing the one-step model k times yields a polynomial of degree 2^k. At larger k this can overflow float64 on some test points; such entries appear as very large values, `inf` or `nan`, and are reported as computed rather than clipped.
- **Sample budget is per model, not per horizon.** n_train counts origin pairs. COMPOSED and each DIRECT-k regressor see n_train rows; DIRECT-k-as-input sees 5*n_train rows because it pools all of K_train. The one-step model is fit only from the (x_t, x_{t+1}) pair of each sampled origin, not from all 39 consecutive transitions of the trajectory. That keeps the budget comparable across models but makes COMPOSED's one-step fit noisier than full trajectory reuse would.
- **Conditioning of the k-as-input model.** Its features include k^2*x, which reaches 81*x at k=9 and 169*x at k=13, so the design matrix is badly scaled and ridge 1e-6 regularizes almost nothing. Its extrapolation columns are a quadratic-in-k extrapolation, which is why they can behave very differently from anything inside K_train.
- **INC uses an interpolated operator.** For (k1,k2) = (3,4) and (5,4) the k2=4 step is the held-out interpolated DIRECT model (mean of the k=3 and k=5 regressors), because 4 is not in K_train; only the composite targets 7 and 9 are trained models. INC therefore measures the inconsistency of the DIRECT scheme as it would actually be deployed, interpolation rule included.
- **Test targets are stochastic.** Targets come from the true noisy dynamics, so a perfect model still has nonzero normalized MSE, and that floor grows with k as process noise accumulates.
- **Grid censoring in K1(iii).** The argmax is taken over the fixed grid [1, 2, 3, 5, 7, 9, 13, 20, 40], and in 8 of the 30 cells it lands on the largest grid point k=40. For those cells the tabulated k* is a lower bound on the unconstrained optimum, not a located interior maximum. J(k) is also flat near its peak in many cells, so k* is only identified to within a grid step or two.
- **Surprises.** (1) In K1(iii) hazard and noise push k* in opposite directions and neither dominates: at fixed (M, sigma) k* falls monotonically as lambda rises (M=4, sigma=1 gives [13, 9, 7, 5, 2] across lambda = [0.005, 0.02, 0.05, 0.1, 0.2]), but the direction of the sigma effect flips with hazard: at lambda = 0.005-0.02 k* is non-decreasing in sigma (noisier segments need a longer commitment before the discriminator separates the skills), while at lambda = 0.1-0.2 it is non-increasing (M=8, lambda=0.2 gives k* = 5, 3, 1 for sigma = 1, 2, 4 - once identifiability is hopeless at any affordable k, the score just buys back commitment). lambda = 0.05 is the turning point and is non-monotone in sigma. The low-hazard/high-noise corner is exactly where the grid runs out. (2) The churn expectation in N1(iii) is exactly zero for every N >= 2K and strictly positive below it, so the whole interesting regime is the narrow band N in [K, 2K). (3) In the nonlinear K2 tables COMPOSED stays within about 1.5x of DIRECT-k out to k=4 and then diverges by many orders of magnitude within a few more steps, while DIRECT-k degrades smoothly; the extra training data (2000 vs 200 origins) moves the point where COMPOSED's normalized MSE first exceeds 1.0 from k=6 to k=9 but does not prevent the divergence.

Total runtime: 0.4 s.
