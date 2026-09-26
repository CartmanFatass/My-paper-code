

## 2026-09-25 — Main space reclamation: redundant support packages removed

Owner-requested storage cleanup only; no new experiment or changed result. Removed the
three support bundles listed below from current main. For the repeat package, 73 members
match existing sibling files or raw-archive members byte-for-byte; the sole unmatched
577-byte collection-preparation record is historical bookkeeping. For current-increment,
34 members match and the remaining 19 are compiled Python caches. The persistence local
support bundle contains test-fixture checkpoints/output and obsolete collection scripts/state,
not the retained native CURRENT_ONLY/PERSISTENT result archives. The original raw result
archives, compact positive/adverse/failed readings and their hashes remain unchanged. No
archive or backup was created. Old support references/receipts describe historical locations;
the exact removed bytes remain available at commit `7263736e03a24db68b0c4e9b8fc4f2c47b2090c6`, not at current-main paths.

- [entity_augmentation_repeat_b01_781901_782001/SUPPORT_RAW.tar.gz](https://github.com/CartmanFatass/My-paper-code/blob/7263736e03a24db68b0c4e9b8fc4f2c47b2090c6/docs/research/candidates/vap_folr_core/entity_augmentation_repeat_b01_781901_782001/SUPPORT_RAW.tar.gz): removed 38,419,425 bytes; original SHA256 `e982297bc0d60f0797a5788020dc9b27d89f1a5018961862002dab659558f974`.
- [entity_current_increment_b01_781801/SUPPORT_RAW.tar.gz](https://github.com/CartmanFatass/My-paper-code/blob/7263736e03a24db68b0c4e9b8fc4f2c47b2090c6/docs/research/candidates/vap_folr_core/entity_current_increment_b01_781801/SUPPORT_RAW.tar.gz): removed 19,195,846 bytes; original SHA256 `e39832b6c183e2edb8b3cf8683c4e4eb4b2d985c769b3d502898d7187dd6feb7`.
- [entity_persistence_b01_781701/LOCAL_SUPPORT_RAW.tar.gz](https://github.com/CartmanFatass/My-paper-code/blob/7263736e03a24db68b0c4e9b8fc4f2c47b2090c6/docs/research/candidates/vap_folr_core/entity_persistence_b01_781701/LOCAL_SUPPORT_RAW.tar.gz): removed 10,215,537 bytes; original SHA256 `afd2e666084222be49aed5b27711f89e0df9eb3e4f325f1dfa7c6c4e5e538e74`.

Allocated bytes removed for these bundles: 67837952. The separate obsolete FSD test reference tape freed 44290048 allocated bytes; no source consumer or open file reference was found. Git history space is measured separately.
