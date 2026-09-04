# VNFC R02 frozen scalar-kernel byte manifest

## Authority and boundary

This document is the prospective dependency and executable-byte authority for the four scalar
transcendentals and the one transferred BPCR native host library used by
`VNFC-R02-ORC-B64-Q52-U64-V1`. It closes dependencies that the A0 freeze previously deferred to a
future source manifest. It adds neither a law alternative nor a result.

```text
manifest=VNFC-R02-ORC-B64-Q52-U64-V1-REFERENCE-KERNEL-BYTES-20260901
python_prefix=C:\Users\fires\.conda\envs\hmasd-amd-cpu
system32=C:\Windows\System32
python=3.10.20 | packaged by Anaconda, Inc. | (main, Jun 11 2026, 15:13:20) [MSC v.1942 64 bit (AMD64)]
torch=2.7.0+cpu
torch_commit=134179474539648ba7dee1317959529fbd0e7f89
windows=10.0.26200
processor=AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD
torch_cpu_capability=AVX512
```

## Exact primitive calls

Start one fresh process with the exact command prefix
`<PYTHON_PREFIX>/python.exe -I -B -S -X`
`pycache_prefix=<A0_NAMESPACE>/kernel-pycache-empty`
`<REPOSITORY_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py`. There is no `-c`, module, console-entry-point,
or alternate bootstrap branch. Before process creation, the launch controller must verify the
runner's resolved path, size, and SHA-256 against the already content-bound R02 source manifest;
the running process repeats that check before any A0 state creation. The prefix directory must be newly created,
empty before import, and still empty at process exit; require `sys.dont_write_bytecode is True` and
`sys.pycache_prefix` equal to that exact path. Also require `sys.flags.no_site == 1`,
`no_user_site == 1`, `ignore_environment == 1`, and `isolated == 1`. Before any path mutation,
`sys.path` must equal, in order, the four exact paths `<PYTHON_PREFIX>/python310.zip`,
`<PYTHON_PREFIX>/DLLs`, `<PYTHON_PREFIX>/lib`, and `<PYTHON_PREFIX>`. Thus `site` cannot process a
`.pth` or customization file and an unhashed adjacent or wheel `pyc` is neither read nor written.
This same PID must continue through A0 publication; it may not hand the probe receipt to a different
interpreter.

The exact import/control/call order is:

1. The content-bound runner is the sole Python source executed before verifier startup. Its first
   bootstrap action imports only `sys`; verify the flags and initial path above, install the
   source-owned audit hook, and require that `site`, `sitecustomize`, and `usercustomize` are absent
   from `sys.modules`. Require real `sys.modules["__main__"].__file__` to resolve exactly to
   `<REPOSITORY_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py`; it may not be hidden, deleted, rewritten, or
   converted to a non-file alias;
2. import `pathlib`, `csv`, `base64`, and `hashlib`, in that order, and verify every literal file
   row, every nonempty torch `RECORD` entry, and the frozen Python-source manifest below;
3. clear only the audit hook's in-memory path accumulator after successful verification, then append
   exactly `<PYTHON_PREFIX>/Lib/site-packages` with `sys.path.append`; the hook remains installed.
   Do not call `site.addsitedir`, import `site`, execute a `.pth`, or add any other path;
4. import `ctypes`, then `wintypes` from `ctypes`, then `torch`;
5. require the frozen version/commit/CPU identities, set intra-op and inter-op threads to one,
   enable deterministic algorithms, and retain every other kernel control in the parent freeze;
6. construct one new contiguous shape-`(1,)`, stride-`(1)`, CPU float64 tensor per row below and
   invoke the four schemas once in table order;
7. load `kernel32.dll` then `psapi.dll` with `ctypes.WinDLL`, enumerate `SNAPSHOT_1` with
   `EnumProcessModules`, and verify exact normalized set, size, and digest equality against the
   frozen inventory below;
8. repeat step 6 with four newly constructed tensors in the same order, require the same output
   bits, enumerate `SNAPSHOT_2` with the already loaded handles, and require
   `SNAPSHOT_2 == SNAPSHOT_1 == FROZEN_MODULE_SET` byte for byte; at this same boundary require
   loaded Python-source set equality against the union of `FROZEN_PYTHON_SOURCE_SET` and the one-row
   `PREPROBE_R02_SOURCE_SET`; de-duplicate the normalized
   opened probe-resource rows by path and require row-wise equality to all 31 rows of
   `FROZEN_PROBE_RESOURCE_SET`, not a subset, plus exactly 31 canonical rows, 4,450 serialized
   bytes, and root `60f77b5ad27140489a117bd5ecd179c07689115e5a6ffcfb6fb675fc18cbd1c3`;
   then apply the audit-hook rejection rules below; and
9. source-load the content-bound R02/A0 and transferred fixture files, including the frozen BPCR
   Python files below, while requiring `FROZEN_MODULE_SET` to remain exactly 81 rows. Require the
   loaded source set to equal the frozen 942 dependency sources plus the exact Python files in the
   later content-bound R02 source manifest. Verify the six BPCR source rows and the exact cached DLL
   row below. Then, still before any A0 fixture, RNG master, parameter, model, optimizer, native
   session, or persisted row exists and immediately before the first of the 24 formal transferred
   adapter calls, perform the sole native load using the frozen load-only transaction below; and
10. enumerate `POST_NATIVE_SNAPSHOT_1` immediately after that transaction and require exact
   row-wise equality to `FROZEN_POST_NATIVE_MODULE_SET`. Retrieve the cached library once more,
   require object identity, enumerate an identical `POST_NATIVE_SNAPSHOT_2`, and then execute A0 in
   this PID. Require the same 82-row set immediately before and after every one of the 24 formal
   native adapter calls, after the last scalar primitive call, and immediately before publication.
   Keep the audit hook and its enforcement active without another reset through publication. Any
   later compiled-module, source, resource, read, or write drift makes the attempt `INCOMPLETE`.

The four exact default ATen schemas and probes are:

| R02 name | Exact callable | Probe input | Required output bits |
| --- | --- | --- | --- |
| `sigmoid_R02` | `torch.ops.aten.sigmoid.default` | `-0x1.0000000000000p+0` | `0x1.136561454ba86p-2` |
| `exp_R02` | `torch.ops.aten.exp.default` | `-0x1.0000000000000p+0` | `0x1.78b56362cef38p-2` |
| `log_R02` | `torch.ops.aten.log.default` | `0x1.0000000000000p-1` | `-0x1.62e42fefa39efp-1` |
| `sqrt_R02` | `torch.ops.aten.sqrt.default` | `0x1.0000000000000p-2` | `0x1.0000000000000p-1` |

The returned tensor element, read as one binary64 value, is the primitive result. Convenience,
in-place, vector-width-greater-than-one, NumPy, Python `math`, and alternate-overload calls are not
aliases. SiLU remains `RN64(x*sigmoid_R02(x))`; no fused SiLU is allowed. The custom adjoints in
the parent freeze remain source-owned; no framework-fused backward substitutes for them.

## Frozen files

Before any A0 fixture, RNG master, parameter, optimizer state, or persisted row exists, verify the
following sizes and SHA-256 values. In addition, parse the frozen wheel `RECORD` and verify the size
and URL-safe-base64 SHA-256 of every entry whose digest is nonempty. That binds the complete torch
Python and compiled distribution, including any torch DLL loaded transitively. Empty-digest
`RECORD`/bytecode entries do not replace the explicit hashes below.

Every expected version, path, size, digest, capability, schema, and output bit pattern is a literal
input from this document. The implementation may compute observed values only. It must not
regenerate, learn, refresh, accept, or overwrite an expected value from the environment it is
checking. A mismatch stops before A0 state creation as `INCOMPLETE`; changing an expected value
requires an explicitly new prospective law/object, not a manifest refresh.

| Anchor-relative path | Bytes | SHA-256 |
| --- | ---: | --- |
| `<PYTHON_PREFIX>/Lib/site-packages/torch-2.7.0.dist-info/RECORD` | 1308883 | `ca4a2a0bc461be8bdd7f842008fe24ff22900fb0289aa36f14fa884ca6f6938a` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch-2.7.0.dist-info/METADATA` | 29546 | `d8ea5f11979b3df2ee47c21a0f3e3a417e633203e633b9fda3606286dc1a3085` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/version.py` | 279 | `f5bb59ed21e17fc2f4cbc704cc3ca9dfd8590167d3e391a762ef4ec5420e6c85` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/__init__.py` | 103670 | `9e46616b9d27c3553ae7587381510cc5a42e8b6fa1c37694c7dc9ea829b11c9b` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/_ops.py` | 58298 | `30592cf51208b305a1c75390eefc6a5aca2c9380fdf10bf3a62cab2eff013afd` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/_C.cp310-win_amd64.pyd` | 10752 | `02b73340cd80f12ebc84f81766dcae06a690ef77bc503e31043f92457f48c9cd` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/lib/c10.dll` | 1011712 | `2bb3f205434570bcbee9487feca86cecb43d47c600a1b2f7455f7f21ff3ec02e` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/lib/libiomp5md.dll` | 1602400 | `a9c9ddf4bb1477645120b481a14a9bcb02b8da6eece12032376e33a1ba96d2ea` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/lib/torch.dll` | 9728 | `a2a091f1708b8b0cce40026da0b8c7473959aa2a448607fd8c04f752f93cf01d` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/lib/torch_cpu.dll` | 252660224 | `777041be8acb72dbe800911da82f7bb023cc96671efbd527383a0a061d5c1f5c` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/lib/torch_global_deps.dll` | 9728 | `4811387fcf95a7d7d9d2e05b78acb807a3ad7c0eeb513d56a210acc88dcc2c82` |
| `<PYTHON_PREFIX>/Lib/site-packages/torch/lib/torch_python.dll` | 16867328 | `8949c102432e38af6a6850445c191f81d57b170b1b999f9d1b6ab117ccd64b9a` |
| `<PYTHON_PREFIX>/python.exe` | 105288 | `7075cb605dd9d7596074b438b2640c7db0a33c436f0c7046a38c211ab257ad3b` |
| `<PYTHON_PREFIX>/python3.DLL` | 66376 | `b315d9553d61e5c4b024ec681c934ca3744d54b344629c19e00bb07e64373eaa` |
| `<PYTHON_PREFIX>/python310.dll` | 4917576 | `459af11741f27ecd7069fd16d75b48ea79189bd57884f1794d04ff8eb2cc779c` |
| `<PYTHON_PREFIX>/VCRUNTIME140.dll` | 124496 | `0205071c36c17f1efbd70178c852cb7d49985c484202752b8704b7ac6b184e60` |
| `<PYTHON_PREFIX>/VCRUNTIME140_1.dll` | 49744 | `963e45edd064545962e216c12d68071ced94dc8e11862a18f07f14eb2690a57c` |
| `<PYTHON_PREFIX>/msvcp140.dll` | 557648 | `8f141b4454fa78db34bc1f28c571b4da0e00cd2c43f7ad0e282f313036826aae` |
| `<SYSTEM32>/ucrtbase.dll` | 1377496 | `5e7709a6b71bb818260b6f05c5bb3b6ca0c3ca9bc2f58c6242c1cd9d826d0079` |
| `<SYSTEM32>/msvcp_win.dll` | 642016 | `940a41d9d78c2d2d0ece8d8e4735630735f57ffb95466e350dae3535b40a698a` |

## Frozen loaded Python-source and probe-resource sets

The exact dependency/runtime Python sources loaded from process start through `SNAPSHOT_2` are the
rows of
`VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_PYTHON_SOURCE_MANIFEST_20260901.tsv`. Resolve each real
regular source path, replace `\` by `/`, case-fold it, replace the exact case-folded Python prefix
by `<PYTHON_PREFIX>`, and sort by unsigned UTF-8 byte order. The TSV is already the canonical
serialization: one row
`<normalized-path> TAB <unsigned-decimal-byte-length> TAB <lowercase-sha256> LF`, UTF-8, no BOM or
header. Its literal authority is:

```text
python_source_manifest=docs/research/candidates/variable_n_fleet_churn/VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_PYTHON_SOURCE_MANIFEST_20260901.tsv
canonical_python_source_rows=942
canonical_python_source_serialization_bytes=122000
canonical_python_source_root_sha256=56de49297250a6d2d8a9ac1754862df5926b1b5a5a2612545ebc328027d23b53
```

This 942-row table is the immutable dependency/runtime source set. The separately content-bound R02
source manifest must also freeze exactly one pre-probe source row:

```text
PREPROBE_R02_SOURCE_SET =
<REPOSITORY_ROOT>/scripts/run_vnfc_bpcr_r02_a0.py<TAB><byte-length><TAB><lowercase-sha256><LF>
preprobe_r02_source_rows=1
combined_preprobe_python_source_rows=943
combined_preprobe_python_source_serialization_bytes=<literal in content-bound R02 source manifest>
combined_preprobe_python_source_root_sha256=<literal in content-bound R02 source manifest>
```

`<REPOSITORY_ROOT>` resolves prospectively to the clean source-bound checkout root. Canonicalize the
runner exactly like other rows after replacing that resolved root by `<REPOSITORY_ROOT>`. The launch
controller computes observed bytes only; the expected runner row, 943-row union serialization
length, and union root come from the content-bound manifest fixed before process creation and may not
be regenerated from the running checkout.

After probe round two, every real `.py` file named by any loaded module must appear exactly once in
the 942-row dependency set or the one-row pre-probe set, and every row in both sets must be loaded.
The runner must be the real file for `__main__`. A real `.pyc`/`.pyo`, a `SourcelessFileLoader`, any
other source outside `<PYTHON_PREFIX>`, or any extra/missing/digest-different source is `INCOMPLETE`.
Built-in, frozen, and namespace modules with no executable file have no source row. The only loaded
modules permitted to carry a nonempty but nonexistent `__file__` are exactly `torch.classes` with
`_classes.py` and `torch.ops` with `_ops.py`, each with `__spec__.origin is None`; they are dynamic
namespaces, not source files.

The audit hook records `open` and `import` events. From the accumulator reset immediately before the
manual site-packages append through `SNAPSHOT_2`, every real Python source must be in the 942-row
dependency set or the one-row content-bound pre-probe runner set, every compiled module must be in
the 81-row set, and the unique normalized set of every other opened regular file below site-packages must equal all 31 rows of the following exact sorted
`FROZEN_PROBE_RESOURCE_SET` row-wise. It must independently reproduce the frozen 31-row count,
4,450-byte canonical serialization, and root; observing only a subset is `INCOMPLETE`.

The hook remains installed and enforcing after `SNAPSHOT_2` through publication. Every later
regular-file read must resolve to exactly one row in `FROZEN_PYTHON_SOURCE_SET`,
`FROZEN_MODULE_SET`, `FROZEN_POST_NATIVE_MODULE_SET`, `FROZEN_PROBE_RESOURCE_SET`,
`FROZEN_BPCR_NATIVE_SOURCE_SET`, or the prospectively content-bound R02 source/input manifest
(including its exact declared input paths, sizes, and digests). No other read is allowed.
Writes are classified separately and are allowed only for exact create-once A0 output paths declared
prospectively by the content-bound implementation/output manifest under the frozen A0 namespace; a
declared write path does not authorize reading it or any sibling path. Any undeclared create,
truncate, append, overwrite, rename, delete, or read/write open is `INCOMPLETE`.

Independently and unconditionally reject any `.pth`, `.pyc`, `.pyo`, `sitecustomize`, or
`usercustomize` path or module, and require `site`, `sitecustomize`, and `usercustomize` absent from
`sys.modules`. No loaded or opened dependency/distribution file is admitted merely because it
shares a version.

Canonicalize the resource rows with the same TSV rule. The exact aggregate is:

```text
canonical_probe_resource_rows=31
canonical_probe_resource_serialization_bytes=4450
canonical_probe_resource_root_sha256=60f77b5ad27140489a117bd5ecd179c07689115e5a6ffcfb6fb675fc18cbd1c3
```

| Normalized probe-resource path | Bytes | SHA-256 |
| --- | ---: | --- |
| `<PYTHON_PREFIX>/lib/site-packages/alembic-1.18.5.dist-info/entry_points.txt` | 48 | `6b290cdf4b28c7018dd2907b7ad2dcd6ad1c1c96cbf5dcb8e919caf555f82cbc` |
| `<PYTHON_PREFIX>/lib/site-packages/anyio-4.14.2.dist-info/entry_points.txt` | 39 | `fdde98bbaba269998d7b40b2768c22ac4f429a0ef350bda0d3cb50a684b742f7` |
| `<PYTHON_PREFIX>/lib/site-packages/cffi-2.1.1.dist-info/entry_points.txt` | 132 | `a6b6108011f8e27050fe5269bba88c8051b414697880d3b0b6fbe3a03a0b001c` |
| `<PYTHON_PREFIX>/lib/site-packages/fonttools-4.63.0.dist-info/entry_points.txt` | 147 | `f2454775dc5f156038e05483e26069982fb8b82ca7427928cfff5a3496f6dbb6` |
| `<PYTHON_PREFIX>/lib/site-packages/httpx2-2.10.0.dist-info/entry_points.txt` | 45 | `dee899a2b4509500053681da0f1b8cb2691d8eddeb5139ae073f35b4b5c57506` |
| `<PYTHON_PREFIX>/lib/site-packages/idna-3.18.dist-info/entry_points.txt` | 38 | `ec7de718e1daa778e72c4e5eeeaed8c2bf55abc6b107b5888f9f82ff8376be1c` |
| `<PYTHON_PREFIX>/lib/site-packages/jinja2-3.1.6.dist-info/entry_points.txt` | 58 | `38bf39818535783f1cb8f9629227c59e05e97818dac65eab209f0a902ff7afe2` |
| `<PYTHON_PREFIX>/lib/site-packages/jsonschema-4.26.0.dist-info/entry_points.txt` | 51 | `bceeeb5f816cff1215272da99c0b4a8134b17e99e8cc0550d038c29a93319d61` |
| `<PYTHON_PREFIX>/lib/site-packages/mako-1.3.12.dist-info/entry_points.txt` | 512 | `2ec2a452c3ac25061b27633bda16429bdebcc22e4af18c1be6e1710ae37c39b9` |
| `<PYTHON_PREFIX>/lib/site-packages/markdown-3.10.2.dist-info/entry_points.txt` | 1102 | `94c1328a203f659c9f3c20650ef88197e4a253471fa1eb842a9c31c37eb5b0a4` |
| `<PYTHON_PREFIX>/lib/site-packages/mcp-2.0.0.dist-info/entry_points.txt` | 42 | `8271816e8df2185d1824d5df669824020d7e090b4ac67cf1ae5039ddcf2f8980` |
| `<PYTHON_PREFIX>/lib/site-packages/networkx-3.2.1.dist-info/entry_points.txt` | 87 | `6f4156fb39be9bd8ad07e6649bbc3ff1cf725fd58619383eaff37f037d8f006b` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy-1.26.3.dist-info/entry_points.txt` | 144 | `cdd772609b94c3d52e77b2de2dfca75e4eb6febcb49468a10f008882e8017593` |
| `<PYTHON_PREFIX>/lib/site-packages/opentelemetry_api-1.44.0.dist-info/entry_points.txt` | 573 | `7713ead1845b4034b097c42447e23d037f2b6db7ca406e61dae3458e9bd4e95e` |
| `<PYTHON_PREFIX>/lib/site-packages/optuna-4.6.0.dist-info/entry_points.txt` | 43 | `8b9306003171363a3c409d17af73916d0a0292a0ed75b0e5d7888032fc8a10a6` |
| `<PYTHON_PREFIX>/lib/site-packages/pandas-2.2.3.dist-info/entry_points.txt` | 69 | `3952ca3443ecf90ec85b2a5604be9fc6fe7aff3b78b119c423bcdac28eb2ff4c` |
| `<PYTHON_PREFIX>/lib/site-packages/pip-26.1.2.dist-info/entry_points.txt` | 84 | `5617fcb34218817dfb9ad778bc62fbdc13dcc5d2a7a9e0853f3079f9ddf4c7ca` |
| `<PYTHON_PREFIX>/lib/site-packages/pyflakes-3.4.0.dist-info/entry_points.txt` | 47 | `2177bef5ebde52b0271ac0ed807733d88c8f2a809623d6f86d71cb5e8847a931` |
| `<PYTHON_PREFIX>/lib/site-packages/pygame-2.6.1.dist-info/entry_points.txt` | 63 | `74baa5af7675277ae0c0c53fd97fe83081e71c22d77eb1727f30f6aba7b0a0e2` |
| `<PYTHON_PREFIX>/lib/site-packages/pygments-2.20.0.dist-info/entry_points.txt` | 53 | `b945f0f9784c281117e2959c0ada6e4d39cf84bde1ece104da35a2e75550b1af` |
| `<PYTHON_PREFIX>/lib/site-packages/pymupdf-1.28.2.dist-info/entry_points.txt` | 51 | `f4d707fc25641d5b8b3711354d86dfc17c0295590c70cf3dd133132770b97c30` |
| `<PYTHON_PREFIX>/lib/site-packages/pytest-9.1.1.dist-info/entry_points.txt` | 95 | `b21b5de5a40ce6372eff650d87fe4ce166b662590a307535e179bfc6c8d2a4d6` |
| `<PYTHON_PREFIX>/lib/site-packages/pywin32-312.dist-info/entry_points.txt` | 132 | `5c1abaae845c382e80e15b567e62b033cd8c972a6e1eb969834193e88f9200a4` |
| `<PYTHON_PREFIX>/lib/site-packages/setuptools-83.0.0-py3.10.egg-info/entry_points.txt` | 2449 | `ce482d8697ff15af4d544f69e85293dd793d0d1d5f680711538728820b15ee30` |
| `<PYTHON_PREFIX>/lib/site-packages/sympy-1.14.0.dist-info/entry_points.txt` | 39 | `4a9faf2c9a26e0f4658467d8e91a54adeed28d89b7dc936af4d0b0086796f9f4` |
| `<PYTHON_PREFIX>/lib/site-packages/tensorboard-2.18.0.dist-info/entry_points.txt` | 156 | `155d7b0b01bf45380524e80ff11a8528eb4b76b9be8829b813320d4f16f232cf` |
| `<PYTHON_PREFIX>/lib/site-packages/torch-2.7.0.dist-info/entry_points.txt` | 199 | `6fcb77f2adf4d4c2ab2f80b17e7faafe6a29e9b33376466c2a69b61ec9cdb264` |
| `<PYTHON_PREFIX>/lib/site-packages/tqdm-4.69.0.dist-info/entry_points.txt` | 39 | `45e2421fb522dd9ca1e8cd7a1383a1b19d6853b5ad31709f6eda3206118edbd6` |
| `<PYTHON_PREFIX>/lib/site-packages/tqdm-4.69.0.dist-info/metadata` | 57356 | `a0406c7575adf27f56a09afa6fbcdcd8d9951d12ca219698baa5627351b0d9a1` |
| `<PYTHON_PREFIX>/lib/site-packages/uvicorn-0.52.3.dist-info/entry_points.txt` | 46 | `156d70fa191cf50830686a28bccbe6d1963bdf0fcd7327167460147c3b0d1b1c` |
| `<PYTHON_PREFIX>/lib/site-packages/wheel-0.47.0.dist-info/entry_points.txt` | 110 | `24976d480193bcc2db2244d565400cbc628edfd16d59f09517c9a9fcd1fa7b88` |

For module identity, obtain each absolute path with `GetModuleFileNameExW`, strip a leading
`\\?\`, replace `\` by `/`, and case-fold the whole absolute path. Replace the exact prefix
`c:/users/fires/.conda/envs/hmasd-amd-cpu` or `c:/windows/system32` with respectively
`<PYTHON_PREFIX>` or `<SYSTEM32>`. Before the declared native load, paths outside those two
canonical roots are forbidden. After it, the one literal absolute BPCR DLL row below is the sole
additional path. Sort the normalized strings by unsigned UTF-8 byte order. Set equality includes
normalized path, byte length, and SHA-256; no extra, missing, duplicate-normalized, or
digest-different module is legal.

## Frozen normalized sorted post-probe module inventory

The complete `FROZEN_MODULE_SET` follows. It is not regenerated from either observed snapshot.
For its canonical serialization, encode each sorted row as
`<normalized-path> TAB <unsigned-decimal-byte-length> TAB <lowercase-sha256> LF`, with literal ASCII
tab/LF, UTF-8, no BOM, and no header; concatenate all 81 rows. The frozen aggregate is:

```text
canonical_module_rows=81
canonical_module_serialization_bytes=9220
canonical_module_root_sha256=62b2c60f19e912f4deaf3511057eb4ca4544a87083841e190811a9442d3e09b0
```

Each observed snapshot must satisfy row-wise set equality and independently reproduce this literal
serialization length and root. The aggregate is a redundant whole-set check, not a substitute for
any row.

| Normalized module path | Bytes | SHA-256 |
| --- | ---: | --- |
| `<PYTHON_PREFIX>/dlls/_asyncio.pyd` | 67400 | `0221540636f19caa26c5a38e1643fdd9806e5835e2fb7ddab63cb9f5ee83a2af` |
| `<PYTHON_PREFIX>/dlls/_bz2.pyd` | 36168 | `fe39f08575d96292d6abff98dc5241afc997428f773e3673790f58fd88a8213b` |
| `<PYTHON_PREFIX>/dlls/_ctypes.pyd` | 133960 | `6cf4f73fad4685de12b460e0f720fa9e102460f4eb0ffca3196d1fcd638f1bf2` |
| `<PYTHON_PREFIX>/dlls/_hashlib.pyd` | 61256 | `b6dab84d48eb52ae2b661a32a4c2640b6c43db7e7b47f191a321a88b5b893d5e` |
| `<PYTHON_PREFIX>/dlls/_lzma.pyd` | 49480 | `34a551e69bd5934964adb50d47fedae1a9b0aa06e677f1d2a53f645474112dea` |
| `<PYTHON_PREFIX>/dlls/_multiprocessing.pyd` | 35656 | `59af0101bcbfd7dbd2bfd36ab0678196fc019469b9c8878914b818fe0812d2dd` |
| `<PYTHON_PREFIX>/dlls/_overlapped.pyd` | 53064 | `420ec0ffadc0235e8cb292fa14ccb2e5d1a72bf634ac914aa477540231f200ed` |
| `<PYTHON_PREFIX>/dlls/_queue.pyd` | 32072 | `4a0600b3a9db68a172aabbcc9b80ee1ec71f1a6b9e15d85709fcc25bd425c103` |
| `<PYTHON_PREFIX>/dlls/_socket.pyd` | 81224 | `522d29add93e7e582ba31a2bd77abf19cba3d2f1d1d083f74380525bbcbcef83` |
| `<PYTHON_PREFIX>/dlls/_ssl.pyd` | 182600 | `906e5a0fbce52727f60cff33891eb01f1c414e1ba6f5fdab78ab91be58563a34` |
| `<PYTHON_PREFIX>/dlls/_uuid.pyd` | 25928 | `a2fdd3044eba5e46fd10b9a739a0cb5e57656bfe7a58e2121b0f9025a46905ad` |
| `<PYTHON_PREFIX>/dlls/select.pyd` | 31048 | `47669481ae0bc2cba32dde8ead290a0b9e599218cf5a68a54ecb5fe9ed9392ac` |
| `<PYTHON_PREFIX>/dlls/unicodedata.pyd` | 1123144 | `ec479f5c6831964ac12449607f75c1dfaf72c96dc49eed407e22ef9c13919941` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy.libs/libopenblas64__v0.3.23-293-gc2f4bdbb-gcc_10_3_0-2bde3a66a51006b2b53eb373ff767a3f.dll` | 38168576 | `57b87772bf676b5c2d718c79dddc9f039d79ec3319fee1398cc305adff7b69e5` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/core/_multiarray_tests.cp310-win_amd64.pyd` | 65024 | `c6232f57bd136b73eb207edea3a5168125b30062463c4b0248adb7a22bda90e9` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/core/_multiarray_umath.cp310-win_amd64.pyd` | 2836480 | `63c2182191fa73c2e01e66c60e8fd9241fec22f374ee887bd3ef699e4d0b3e33` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/fft/_pocketfft_internal.cp310-win_amd64.pyd` | 110080 | `f13c67179bee2afcb48bb3ad63beeabba0054d7180c0d467b55170d8448011ea` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/linalg/_umath_linalg.cp310-win_amd64.pyd` | 106496 | `a5c7a1e11e95bc20e8abed57b95e8fa17b2318d9b0ff532cbafd8dcf168b7731` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/_bounded_integers.cp310-win_amd64.pyd` | 257024 | `c16edfb2321f6553c67329872b5deea905d066f87c54af50bb42d431fa7200ca` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/_common.cp310-win_amd64.pyd` | 173568 | `1527b0a10add83dafaa61538758da1050297c63d4730675d630d7eded7f3888f` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/_generator.cp310-win_amd64.pyd` | 693248 | `7c99120d7ae4eb4ab4c29d49ae9c82bff17e7ae1dcaf35e1c03d91359577e178` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/_mt19937.cp310-win_amd64.pyd` | 76288 | `539dd8f626a56c4fc8450769a310e2774c9ccccf01db6c0f4d27a4e2840e7efd` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/_pcg64.cp310-win_amd64.pyd` | 83456 | `0214198b612db1e4651a826c47444f098f6f37911476cd05ef264f09d0542066` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/_philox.cp310-win_amd64.pyd` | 69632 | `935d99ea9d412110a06e364c3b8d14f533cce6417e7002793e4ec37387deb8c4` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/_sfc64.cp310-win_amd64.pyd` | 50688 | `f3cce3380b57a8b95a3769c02d10a4b5f8a63744a4f44e9c58fea4176ae7bf52` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/bit_generator.cp310-win_amd64.pyd` | 163840 | `24333cb50d2dee0a953d947c0f0a5a51f5c15d4958b19652715d720dc2dcd395` |
| `<PYTHON_PREFIX>/lib/site-packages/numpy/random/mtrand.cp310-win_amd64.pyd` | 595968 | `3fe777a3e105c77b3c91fac1c2fa19b9b1281102d269e6aafd5652e523d4a87e` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/_c.cp310-win_amd64.pyd` | 10752 | `02b73340cd80f12ebc84f81766dcae06a690ef77bc503e31043f92457f48c9cd` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/asmjit.dll` | 359424 | `36bf5b6376f25d1392466f3a9c0bc665908e95726034809321587d7af01ae878` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/c10.dll` | 1011712 | `2bb3f205434570bcbee9487feca86cecb43d47c600a1b2f7455f7f21ff3ec02e` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/fbgemm.dll` | 4958720 | `8f338a94f16f8ce7de1ab8fd53b581277615f2e318e18a9f8b5311e4b6a473a0` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/libiomp5md.dll` | 1602400 | `a9c9ddf4bb1477645120b481a14a9bcb02b8da6eece12032376e33a1ba96d2ea` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/libiompstubs5md.dll` | 43872 | `73b94d65a4fdefd2ecee199f52dd5e4f7d13e57a3d27a53a01e6180df9375517` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/shm.dll` | 14848 | `82cd53b1ced898eae37d2cd625c6028fe9122614d53319eb5596437bbe04be7b` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch.dll` | 9728 | `a2a091f1708b8b0cce40026da0b8c7473959aa2a448607fd8c04f752f93cf01d` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch_cpu.dll` | 252660224 | `777041be8acb72dbe800911da82f7bb023cc96671efbd527383a0a061d5c1f5c` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch_global_deps.dll` | 9728 | `4811387fcf95a7d7d9d2e05b78acb807a3ad7c0eeb513d56a210acc88dcc2c82` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/torch_python.dll` | 16867328 | `8949c102432e38af6a6850445c191f81d57b170b1b999f9d1b6ab117ccd64b9a` |
| `<PYTHON_PREFIX>/lib/site-packages/torch/lib/uv.dll` | 195072 | `d6e517084425092066d4b26678320eb60edf2c79ade855bd67b829113f999da6` |
| `<PYTHON_PREFIX>/library/bin/ffi.dll` | 41288 | `6792fdc77c477ffbd41e7dd1b08bd07d5989595aaa888cfca1f9884de011ce0d` |
| `<PYTHON_PREFIX>/library/bin/libbz2.dll` | 83216 | `25a4aae35dd89709620106db311af5bca7c868182b961e106a895ae14d2fc98a` |
| `<PYTHON_PREFIX>/library/bin/libcrypto-3-x64.dll` | 7343944 | `83e02d124c675839765df4cf42bf483d239204c5d70e83232ce1cb131c6f7a4f` |
| `<PYTHON_PREFIX>/library/bin/liblzma.dll` | 200520 | `960b67b5188e142ae86e7a3ad0ad417a6c50e7a511b19155ad46061f46d0857f` |
| `<PYTHON_PREFIX>/library/bin/libssl-3-x64.dll` | 1327944 | `8cce38aefaaa530528949a9f3901c09d5578b91fe9b6a0248427c983f1b54559` |
| `<PYTHON_PREFIX>/msvcp140.dll` | 557648 | `8f141b4454fa78db34bc1f28c571b4da0e00cd2c43f7ad0e282f313036826aae` |
| `<PYTHON_PREFIX>/python.exe` | 105288 | `7075cb605dd9d7596074b438b2640c7db0a33c436f0c7046a38c211ab257ad3b` |
| `<PYTHON_PREFIX>/python3.dll` | 66376 | `b315d9553d61e5c4b024ec681c934ca3744d54b344629c19e00bb07e64373eaa` |
| `<PYTHON_PREFIX>/python310.dll` | 4917576 | `459af11741f27ecd7069fd16d75b48ea79189bd57884f1794d04ff8eb2cc779c` |
| `<PYTHON_PREFIX>/vcruntime140.dll` | 124496 | `0205071c36c17f1efbd70178c852cb7d49985c484202752b8704b7ac6b184e60` |
| `<PYTHON_PREFIX>/vcruntime140_1.dll` | 49744 | `963e45edd064545962e216c12d68071ced94dc8e11862a18f07f14eb2690a57c` |
| `<PYTHON_PREFIX>/zlib.dll` | 102728 | `a2e123cc624634d08200b4e5ee6a2828d2df88fd9573b5b5fdd9da336f5738a6` |
| `<SYSTEM32>/advapi32.dll` | 778352 | `04c05b90594ca9ee618fd1fdc567f1d5e15ffec0935401fc935170c4aa37eded` |
| `<SYSTEM32>/bcryptprimitives.dll` | 716376 | `364291fa938a0a20347663e5d63c90c3044e156b581234672cc18900b8d0c721` |
| `<SYSTEM32>/combase.dll` | 3716200 | `065096969039d1cefa7a15222b3951bf3b5950440c9b8e2de25b75a6a4b4a51c` |
| `<SYSTEM32>/crypt32.dll` | 1559304 | `ce33da8c5c866ee0ccb6d20b22369615e12c9205b4253b621ccaf4dd9d3324f7` |
| `<SYSTEM32>/cryptbase.dll` | 59392 | `a3d2cc015de11fc08beb54a08827fee2f63fd8cec9c58273a9120e37fb111c9d` |
| `<SYSTEM32>/cryptsp.dll` | 121384 | `ca7c54c30b17d50da527301a2b80f7a4fbaeb0de44fc5132f8a229211f714f71` |
| `<SYSTEM32>/dbghelp.dll` | 2262488 | `1463249a85bb239fcb536780f3b964c5f2fd68398ffbd35ebec0d65660c8d83e` |
| `<SYSTEM32>/gdi32.dll` | 187456 | `772c73e294a4c5f5e0d4146288af95287a85c074d3aee3fa9f320dc010d7dbfe` |
| `<SYSTEM32>/gdi32full.dll` | 1220456 | `221837c909048eb7fbbb3a6af9f17897f54e4fc70064d423cfca3d19db99db52` |
| `<SYSTEM32>/imagehlp.dll` | 137832 | `58117bbc51c4a56b6c4789e190f33a540b7734e394ada9652e2832e3d2e16588` |
| `<SYSTEM32>/imm32.dll` | 212248 | `700fad44c3c8bd4ccd68b47464234197b378d1aeb95a249e036adfbe8e45eef0` |
| `<SYSTEM32>/iphlpapi.dll` | 220512 | `6adf281a10f9bfe733acca7c5303f0070523e54ef98bf23d3863d3cf02573da0` |
| `<SYSTEM32>/kernel32.dll` | 836208 | `0ab61f2e0d412a585233f1b308c120cba74f800c1030bffe0aabd20df8c6d907` |
| `<SYSTEM32>/kernelbase.dll` | 4199672 | `9d26852459745322b704e2a49e448922839c584d06e208cf9abcd0d857c4b7cd` |
| `<SYSTEM32>/msvcp_win.dll` | 642016 | `940a41d9d78c2d2d0ece8d8e4735630735f57ffb95466e350dae3535b40a698a` |
| `<SYSTEM32>/msvcrt.dll` | 699872 | `744606e3d245647943ab7be0d4132ead491c719b908c207afb775e1ed30299f0` |
| `<SYSTEM32>/mswsock.dll` | 451904 | `46ddbb115b2d6fbf9216f31c2b7c213018709fecaa56e3df835d40a1f629f5b2` |
| `<SYSTEM32>/ntdll.dll` | 2517928 | `b9775b65c47564c2571fb9175e07ec14ce2a771613230afb2c284a0501a369a7` |
| `<SYSTEM32>/ole32.dll` | 1691504 | `185783ea9c2b457ae10b9a31bd9adfc128709a5c8d47bf05cf3fa31188103dcb` |
| `<SYSTEM32>/oleaut32.dll` | 898192 | `bb95ec2fcb2f4ab95921171025805226d4ace7a1764500c310790241c259f61e` |
| `<SYSTEM32>/psapi.dll` | 42864 | `6c8ebe6621224d11ded0c920873d67b5255fd515e8c4ea803cd587c8232bee5c` |
| `<SYSTEM32>/rpcrt4.dll` | 1162648 | `7a83d6f4adb8ddb0132a955697c3cddda8fbe0dbd2a2caec15784df974b02ecc` |
| `<SYSTEM32>/rsaenh.dll` | 245264 | `731771049467b6d01c7028a1269df17da37af8d323621e01a32856e306795400` |
| `<SYSTEM32>/sechost.dll` | 708136 | `26ab024e0bac4ea7f5dbc38dedf5152fb6d1aa9be04dab6947647183d6bd1db3` |
| `<SYSTEM32>/ucrtbase.dll` | 1377496 | `5e7709a6b71bb818260b6f05c5bb3b6ca0c3ca9bc2f58c6242c1cd9d826d0079` |
| `<SYSTEM32>/user32.dll` | 1877488 | `87ae7cca2cb9f368f265faa59ed5e421eb9ec8ee07cf60244ed913ce2ba2e0d4` |
| `<SYSTEM32>/userenv.dll` | 216400 | `432615925936be8b3267e4bad5e5d4b082238b679b8bd7dcfece8868e18e317d` |
| `<SYSTEM32>/version.dll` | 55192 | `cea99f212af557a9613150c5509631403ed0f05f5d9a06ac42039bd59b40e39a` |
| `<SYSTEM32>/win32u.dll` | 170992 | `a8cfcbaf6c3f855f5ba5fb16c91df9ecac65db35a93c8d48da4400466a759388` |
| `<SYSTEM32>/ws2_32.dll` | 542832 | `ab328882e7b545abd349134b0757a148b279652b0621d00e8178a03ed8a23f9b` |

## Frozen transferred BPCR native dependency and phase transition

The formal transferred 24-call path uses
`experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend`. The following six exact
rows are `FROZEN_BPCR_NATIVE_SOURCE_SET`. They must also be rows of the later content-bound R02
source/input manifest. Normalize the resolved checkout root to `<REPOSITORY_ROOT>`, replace `\` by
`/`, sort by unsigned UTF-8 byte order, and serialize with the same TSV rule as the inventories
above.

```text
canonical_bpcr_native_source_rows=6
canonical_bpcr_native_source_serialization_bytes=976
canonical_bpcr_native_source_root_sha256=ca1d223448767617426953f10c717ab666c494c2509a6d1f6b4e4825d6422733
```

| Normalized BPCR source path | Bytes | SHA-256 |
| --- | ---: | --- |
| `<REPOSITORY_ROOT>/experiments/candidates/variable_n_fleet_churn_bpcr_r09/__init__.py` | 357 | `624e17f23411605fdf03bec1d67229c7b523d8590a56efe08c0b32f3736453d6` |
| `<REPOSITORY_ROOT>/experiments/candidates/variable_n_fleet_churn_bpcr_r09/contracts.py` | 4205 | `74a123166b7cfa36c75ef610287d2925e6c422d88b8175666905d6d749bee19b` |
| `<REPOSITORY_ROOT>/experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp` | 21499 | `b5b45c3e8413afe1cc278559a5b8ae67921d6e4a57a363ed2ffb9ad9a07c5c68` |
| `<REPOSITORY_ROOT>/experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_checker.hpp` | 12295 | `c23709add8956b20fec813a6b75443f1a8584f7fe39241d2431a39ed2ed09691` |
| `<REPOSITORY_ROOT>/experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp` | 38908 | `0e30aeb2ef0402ff2914f61978eb74f18034bfc75db5dc61cd52e35c8b6e86ba` |
| `<REPOSITORY_ROOT>/experiments/candidates/variable_n_fleet_churn_bpcr_r09/native_backend.py` | 45512 | `eada0cb64a15032eb034c0b87db5eb86724640b0f274c3e34120ae9891284236` |

The loader's exact three-file C++/HPP domain digest is
`5ec824419f8794504f3179fcc4369687014ed6577ecc8307fab346c2bf3f2c4d`. With implementation-contract
digest `c5d63ecd2624a79b5340b6defa1eb2d6335431c14f5b9ad00b453f9eb3aa65fc`, the already frozen
science-card/public-law digests, compiler digest
`88c8344236a27a6e727e0a8edc49aaa2690bdc7a9464b9d18cc7abe70a9f1c0d`, the source-declared flag
order, and ABI `1`, its source-declared `VNFC-BPCR-R09-NATIVE-BUILD-v1` derivation yields the literal
build key `7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99`. These derivation values
are prospective literals; A0 must not invoke or inspect the compiler to regenerate them.

`FROZEN_BPCR_NATIVE_DLL` is exactly:

| Normalized absolute DLL path | Bytes | SHA-256 |
| --- | ---: | --- |
| `c:/users/fires/appdata/local/temp/hmasd_vnfc_bpcr_r09_native/7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99/bpcr_backend.dll` | 213504 | `dadac9589cf1a885b1acd3891f7411152fa2748cbc34ddbf3537d0b2708f5f68` |

The expected path is that literal absolute path, not a value regenerated from `TEMP`. Absence at
that path, selection or loading from a different build-key directory, more than one normalized
loaded BPCR DLL row, or byte mismatch is `INCOMPLETE`; no compilation is permitted. Other unused
cache entries confer no authority and may not be read or loaded. Read-only PE import inspection
records only `KERNEL32.dll`, already present in the 81-row baseline, but the post-load row-wise
equality below remains authoritative.

The load-only transaction is exact. After importing the frozen module and before any caller can
invoke its backend accessor, require `require_cpp_batched_backend.cache_info().currsize == 0` and
the DLL absent from the live module inventory. A content-bound A0 function saves the original
`native_backend._compiled_path`, replaces only that name with a zero-argument function returning
`pathlib.Path` of the literal DLL path above, calls
`native_backend.require_cpp_batched_backend(build_root=None)` exactly once, and restores the exact
original function object in a `finally` block. The existing accessor's `ctypes.CDLL` call and its
ABI-version, fixture-magic, and structure-size probes are the only native calls before
`POST_NATIVE_SNAPSHOT_1`. The accessor must then have cache size one. Calling `native_build_key`,
`native_toolchain_identity`, `_compiler_path`, `_vs_installation`, or the original
`_compiled_path`; launching a compiler/build/helper subprocess; creating or changing any cache
file; accepting a build-root override; or using a fallback is forbidden. The loaded library and
the later 24 formal calls remain in the original interpreter PID.

`FROZEN_POST_NATIVE_MODULE_SET` is exactly the sorted union of all 81 rows in
`FROZEN_MODULE_SET` and the one `FROZEN_BPCR_NATIVE_DLL` row. Its literal canonical aggregate is:

```text
canonical_post_native_module_rows=82
canonical_post_native_module_serialization_bytes=9435
canonical_post_native_module_root_sha256=ce22039a3888cea1f3e12963e4e0e3fb8eb00753446b332770cb8257c521ed63
```

Both post-load snapshots and every later guard must satisfy row-wise set equality and reproduce
that count, serialization length, and root. The phase change is one-way: the exact 81-row set is
mandatory through the instant before the sole `ctypes.CDLL`; the exact 82-row union is mandatory
from accessor return through publication. Neither set may be widened by a transitive, delayed, or
presentation-specific module.

This byte gate is a non-result conformance precondition. A mismatch creates no A0 observation and
must not be converted into `FAIL_LAW` or algorithm polarity.
