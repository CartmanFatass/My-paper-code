# CCIC B1 revision-05 preactivity work-infeasibility intake

```text
direction=covariance_calibrated_information_clock
affected_revision=CCIC-B1-SCIENCE-20260812-05
source=Root-relayed same-direction CM construction fact
scientific_activity_started=false
question_relevant_data_produced=false
technical_acceptance=withheld
em_disposition=exact_v5_ends_preactivity_infeasible
successor_revision=CCIC-B1-SCIENCE-20260813-06
provider_action=none
cm_action=none
production_authorization=none
```

## Conclusion

Exact revision 05 cannot enter scientific activity. Under its own frozen
architectures and work grammar, every one of the 27 CCIC-versus-RI work cells
violates the required operation ratio `<=1.10`: the `DUP` ratios span
`1.138--1.169`, and `CORR/IND` span `1.271--1.355`. A certificate that merely
shows all 27 cells were encoded cannot satisfy the frozen gate or safely permit
later activity. This is a preactivity feasibility finding, not evidence for or
against CCIC, RI, variable `N`, variable `k`, or task value.

The EM ends exact revision 05 and freezes one complete prospective successor,
revision 06. No result informed the successor. Revision 06 preserves CCIC,
the DGP, actor, axes, tapes, endpoints, inference, thresholds, alternatives,
claim ceiling, second-surface trigger, and activity boundary. Its sole
science-bearing change is a stronger replication-safe RI comparator whose
additional operation budget performs output-relevant nonlinear computation.

## Alternatives adjudicated

### Semantically neutral padding — rejected

Dummy or output-disconnected operations could make accounting ratios pass, but
would only equalize resource burn. They would not exclude the strongest causal
alternative that CCIC received more *useful functional computation* than RI.
Calling that work matching would overstate identification. Padding therefore
does not repair the frozen scientific claim.

### Gate relaxation — rejected

Raising the limit to admit deterministic ratios as high as `1.355` would leave
held-out effects compatible with cell-specific compute advantage. It would
require a materially lower claim ceiling and make RI no longer the strongest
work-matched alternative. The direction has a feasible stronger comparator, so
this loss of identification is unnecessary.

### Useful-compute RI successor — accepted

Revision 06 replaces only `RI-STRONG` with `RI-STRONG-v2`. It retains lineage
quotienting, inputs, targets, samples, updates, actor, and execution information,
but uses one intentionally advantaged 83-scalar row MLP versus CCIC's 82. It
applies a `6 -> 9 -> 2` SiLU MLP to every unique row and one parameter-free but
output-relevant channelwise residual transform before mean pooling and the same
invertible decodes. Thus the comparator spends its matched budget inside a
wider predictive function rather than on no-ops.

For unique row `i`, let

```text
r_i = MLP_6->9->2(z_i,o_i,s_i,log M,t/30,k/5)
h_i = r_i + tanh(r_i)
g = mean_i h_i
Delta ell_hat = 8*sinh(g_1)
J_hat = 1e-4+softplus(g_2)
```

The same residual path is used in training and execution. Training still
targets `asinh(Delta ell/8)` and normalized positive `J`, with no clipping.
Because lineage quotienting precedes the network, literal copies still cannot
change its unique table or output.

## Prospective work identity

Under the unchanged work grammar, with received rows `N` and unique rows
`M=1` for `DUP`, otherwise `M=N`, the shared prefix remains
`C(N,M)=14N+M-5`. CCIC remains

```text
W_CCIC = C(N,M) + 391M + 13 = 14N + 392M + 8.
```

`RI-STRONG-v2` counts per unique row: `6 -> 9` linear `225`, width-nine SiLU
`45`, `9 -> 2` linear `74`, and the two-channel residual transform `8`;
two-channel mean pooling costs `4M+2`, and the two decodes cost `10`. Hence

```text
W_RI_v2 = C(N,M) + 356M + 12 = 14N + 357M + 7.
```

The frozen per-tuple ratios are therefore:

| `N` | regime | `M` | CCIC ops | RI-v2 ops | ratio |
|---:|---|---:|---:|---:|---:|
| 2 | `DUP` | 1 | 428 | 392 | 1.091837 |
| 5 | `DUP` | 1 | 470 | 434 | 1.082949 |
| 8 | `DUP` | 1 | 512 | 476 | 1.075630 |
| 2 | `CORR/IND` | 2 | 820 | 749 | 1.094793 |
| 5 | `CORR/IND` | 5 | 2038 | 1862 | 1.094522 |
| 8 | `CORR/IND` | 8 | 3256 | 2975 | 1.094454 |

The canonical streaming schedule has peak temporary slots
`P_CCIC=22+6M` and `P_RI_v2=24+6M`; the worst peak ratio is `30/28=1.071429`.
Both operation and peak ratios are therefore at most `1.10` in all 27 cells
before any learned update or stochastic evaluation. The preactivity certificate
must require the literal formulas, complete table, and `passed=true`; merely
encoding cells is insufficient.

## Authority and evidence boundary

Revision 05 retains its historical Pro closure but is no longer eligible for
CM activity because its own work gate is infeasible. Revision 06 is a new
science-bearing composite and is not mathematically closed until the existing
same-direction Pro conversation returns literal `CLOSED` and this EM intakes
it. This intake authorizes no provider send, CM work, test, compute, production,
Gemini turn, second surface, or UAV claim.
