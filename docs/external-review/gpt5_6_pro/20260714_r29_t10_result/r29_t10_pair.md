# R29-T10 Paired 320K Result

- Status: **PRELIMINARY_FAIL**
- Scope: one paired seed (`29031`), 320K additional environment steps per arm.
- R29-T10 late mean difference (real - probe): `0.031265`;
  paired-update 95% interval `[-0.005331, 0.064452]`.
- Per-skill late differences: `{"0": 0.0407883484354832, "1": 0.08656550445281996, "2": 0.0297151450966745, "3": -0.025269767229889873}`.
- R26 status: probe `PASS`, real `MIXED`;
  full-minus-prior gain `-0.058112`.
- Real reward/env ratio maximum: `0.044672`.
- Real late skill entropy: `0.996980`.
- Task reward relative degradation: `0.315623`.
- Zero-throughput step-fraction worsening: `0.095300`.
- Gate flags: `{"implementation_valid": true, "r26_transfer_pass": false, "safety_pass": false, "score_pass": false}`.

This result is preliminary because there is only one paired seed. The paired
update bootstrap measures late training-update variation, not independent-seed
uncertainty and not the reset-level bootstrap requested for a final family claim.
