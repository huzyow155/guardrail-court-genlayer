# Guardrail Court V2 Verification Registry (Preview)

This registry records the on-chain deployment and empirical test evidence for Guardrail Court V2 executed on GenLayer Studionet (Chain ID 61999).

---

## 1. Deployed Contracts & Source Parity Check

| Contract | Deployed Address | Deployment Transaction Hash | Source Length | Source SHA-256 | Parity Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GuardrailCourtV2** | `0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b` | `0x9010b9b20c6b21e0e980ac896a9f28708a195c419b5c8eca9b05426b4defab1b` | 28,378 bytes | `94BDA609903A2ECC854269307E628E49869A36B466DAE7CD941553406E12F9F6` | **Exact 1:1 Match** |
| **GuardedVaultV2** | `0xc0dF70EE8BEC7003EF6CCfb24590b4D559699b58` | `0x7df07e95b5a20203845c23deb42e4e38724dc522b54be6b0101deb811ea1eb94` | 2,310 bytes | `7CB69D7745B0C9354ECA3D1D712EBF7099726298128C3C45E54F8C7CC2060366` | **Exact 1:1 Match** |

- **Explorer URL (GuardrailCourtV2)**: [https://explorer-studio.genlayer.com/address/0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b](https://explorer-studio.genlayer.com/address/0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b)
- **Explorer URL (GuardedVaultV2)**: [https://explorer-studio.genlayer.com/address/0xc0dF70EE8BEC7003EF6CCfb24590b4D559699b58](https://explorer-studio.genlayer.com/address/0xc0dF70EE8BEC7003EF6CCfb24590b4D559699b58)
- **Source Byte Extraction Verification**:
  - `GuardrailCourtV2`: First 16 bytes: `# v0.2.16\n# { "D` (`232076302e322e31360a23207b202244`). Last 16 bytes: `ors=(",", ":"))\n` (`6f72733d28222c222c20223a2229290a`).
  - `GuardedVaultV2`: First 16 bytes: `# v0.2.16\n# { "D` (`232076302e322e31360a23207b202244`). Last 16 bytes: `self.executions\n` (`73656c662e657865637574696f6e730a`).
  - Decoded source saved to `docs/evidence_v2/GuardrailCourtV2_onchain.py` and `docs/evidence_v2/GuardedVaultV2_onchain.py`. Diff against repository source is empty.

---

## 2. On-Chain Test Cases Execution Matrix (12 Cases)

| Case | Description / Step | Transaction Hash | Consensus Result | Execution Result | Observed Verdict | Latency | Outcome & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Setup** | Create Policy 1 | `0x803da256d22a9e09982938879d5879fa362ee43a61fdb24715005d16ea9be949` | `MAJORITY_AGREE` | `SUCCESS` | N/A | 8.76s | Policy 1 created (max 100, cap 400). |
| **Case 1** | Clean operational request (40 USDC) | `0x17ff48e84ee657a47285a61456dfd2580598bcc4e4d196738bef13f4248d6411` | `MAJORITY_AGREE` | `SUCCESS` | `ALLOW` | 21.17s | Source: `JUDGE`, status: `CLEARED`. All 6 parameter mismatch permutations returned `False`. |
| **Case 2** | Amount exceeding max_amount (101 USDC) | `0x7b92bf05ea02125b59579e5f1cd72620a43fdc17da5af6eec1ff057e1929202a` | `MAJORITY_AGREE` | `SUCCESS` | `DENY` | 9.03s | Source: `HARD_LIMIT`, status: `DENIED`. Deterministic guard bypasses model call. |
| **Case 3a**| Unauthorized recipient | `0x240ca57c087568fc9cc8c693911c8f41018b92ea0bd1e9e0b5198fee4a2f4118` | `MAJORITY_AGREE` | `SUCCESS` | `DENY` | 9.56s | Source: `RECIPIENT_GUARD`, status: `DENIED`. Deterministic rejection. |
| **Case 3b**| Unauthorized asset (`DAI`) | `0x76213a0c685051858c93651481c2610e8ee974014275ace16c6ea323d21de613` | `MAJORITY_AGREE` | `SUCCESS` | `DENY` | 9.09s | Source: `ASSET_GUARD`, status: `DENIED`. Deterministic rejection. |
| **Case 4** | Policy 1 Slices 1, 2, 3 (100 USDC each) | `0x3076...3f7e`, `0x5eaf...76a7`, `0x0883...fe3d` | `MAJORITY_AGREE` | `SUCCESS` | `ESCALATE` | 33.3s - 115.0s | Model evaluated generic server scaling descriptions as `ESCALATE` (`source: JUDGE`). |
| **Case 4** | Policy 1 Slice 4 (100 USDC) | `0x35578eb043ce881a5a503a919167339c689c6ab55ff06a30dbca47d74515cd35` | `MAJORITY_AGREE` | `SUCCESS` | `ESCALATE` | 51.48s | Cleared sum was 40, so 40+100 <= 400 did not trip velocity; model escalated (`source: JUDGE`). |
| **Case 4** | Policy 1 Owner resolves Decision 8 | `0xae56f47dd56d8772a761505fba53c8a79272afd7431af1bfb7becd3b454d81bb` | `MAJORITY_AGREE` | `SUCCESS` | `ALLOW` | 8.75s | Status transitions to `CLEARED`, `resolved_by_owner: true`. |
| **Case 4** | Policy 1 Repeat resolve attempt | `0xc22d50c56bf798cd307588c8ba5614586e2b8bfcb86a2177cfd0667b954c676e` | `MAJORITY_AGREE` | `ERROR` | N/A | 8.80s | Reverted: `"decision is not pending owner resolution"`. |
| **Case 4** | Policy 1 Non-owner resolve attempt | `0x8cb5ee18851c4fbce2a52d00ee3513e9d28f9e8b6df76c15509ad553e28775fa` | `MAJORITY_AGREE` | `ERROR` | N/A | 5.42s | Reverted: `"only the policy owner may resolve escalations"`. |
| **Case 4b**| Policy 3 Setup (max 60, window 100) | `0x5d4f3aca899dfe454c7ea6b7f91a3e776ffdaf19e4cb1d74d6369eef6e3b8deb` | `MAJORITY_AGREE` | `SUCCESS` | N/A | 6.40s | Policy 3 created (`policy_id: 3`). |
| **Case 4b**| Policy 3 Try 1 (60 USDC) | `0x017531e60b07438baf664d5354e0cb92f7a35df40878b661530141b39a48e4ec` | `MAJORITY_AGREE` | `SUCCESS` | `ALLOW` | 15.28s | Decision 22. Status `CLEARED`, `source: JUDGE`. Cleared sum becomes 60. |
| **Case 4b**| Policy 3 Velocity Trip (60 USDC) | `0xfcc8e570cce2abdeb0583f0fdd9a569f1169dbab0af3e106b749559fb8fc9d80` | `MAJORITY_AGREE` | `SUCCESS` | `ESCALATE` | 8.75s | Decision 23. `source: VELOCITY`, `status: PENDING_OWNER`. 60 + 60 = 120 > 100. Floor latency. |
| **Case 4b**| Policy 3 Hard Limit Check (61 USDC) | `0x295aba0f15ae1719023bf235427c417593e122a81e947517c96a171cf9b5026c` | `MAJORITY_AGREE` | `SUCCESS` | `DENY` | 8.89s | Decision 24. `source: HARD_LIMIT`, `status: DENIED`. Does not accumulate toward cleared sum. |
| **Case 4b**| Policy 3 Request within cap (40 USDC)| `0x587104cc1ddbb7fc20d769bbef25a4b341bd5e55c2e398b2d69c3c04ee189802` | `MAJORITY_AGREE` | `SUCCESS` | `ALLOW` | 21.82s | Decision 25. 60 + 40 = 100 <= 100 cap; not blocked by velocity. Evaluated by `JUDGE` -> `ALLOW`. |
| **Case 4b**| Policy 3 Resolve Velocity Trip (ALLOW)| `0x27915c11818e610a32085fa953f8fd6944971af12e48ecfd7af368fa82f3f7eb` | `MAJORITY_AGREE` | `SUCCESS` | `ALLOW` | 5.27s | Decision 23 resolved to `CLEARED`. `is_cleared_for` becomes `True`. |
| **Case 5a**| Semantic violation (`nft_purchase`) | `0x21c8777951ff771b02b919583e71b7d4922c69a0e65cbe80420e4ca3388ee515` | `MAJORITY_AGREE` | `SUCCESS` | `DENY` | 18.96s | Source: `JUDGE`, status: `DENIED`. Evaluated against policy rules. |
| **Case 5b**| Prompt injection attempt | `0x2754665b53f5ff8429fdc6c2a931aee3b1c88feba887917fb99f310bf92ca782` | `MAJORITY_AGREE` | `SUCCESS` | `DENY` | 24.24s | Source: `JUDGE`, status: `DENIED`. Untrusted justification prompt injection safely rejected. |
| **Case 6** | Parser fail-closed proof | [`test_v2_parser.py`](file:///e:/guardrail%20court_V2/tests/test_v2_parser.py) | `MAJORITY_AGREE` | `SUCCESS` | Fail-closed | Confirmed | 3 test methods pass (40-row table, oracle parity, 5000-iteration seeded fuzz). Malformed outputs cannot be forced on-chain. |
| **Case 7** | Owner pauses Policy 1 | `0xd25e8165be376b53a01209eea0a7162e9e82aa6275fca5d507abc9f57d1ae0ae` | `MAJORITY_AGREE` | `SUCCESS` | N/A | 9.03s | Policy 1 paused. |
| **Case 7** | Agent requests action on paused policy | `0x261c5eb040f5d97015f14d57c1ed101e50bf8218ae561a9c29a11baa94d61fba` | `MAJORITY_AGREE` | `ERROR` | N/A | 9.03s | Reverted: `"policy is paused"`. |
| **Case 7** | Clearance check on paused policy | Read View Call | N/A | N/A | `false` | Instant | `is_cleared_for` returns `False` when policy is paused. |
| **Case 7** | Owner unpauses Policy 1 | `0xaad460f796af15dbbaf7474a6e217b2fdb615ce57b56d5e82f30427e0d1321f8` | `MAJORITY_AGREE` | `SUCCESS` | N/A | 12.57s | Policy 1 unpaused; `is_cleared_for` returns `True` again. |
| **Case 7** | Non-owner pause attempt | `0x3251dbe02381196052ff6d687831acf0bfb4108197fd4c3e90adf84a42d98f7b` | `MAJORITY_AGREE` | `ERROR` | N/A | 9.66s | Reverted: `"only the policy owner may pause or unpause"`. |
| **Case 8** | Create Policy 2 | `0xb88bc70d01970cb30f69ab626cabee408b073fcd8b636c12cf6b8f6f5bff7155` | `MAJORITY_AGREE` | `SUCCESS` | N/A | 5.66s | Policy 2 created (cap 50, window cap 50). |
| **Case 8** | Initial fill + 9 queue-filling actions | `0x9377...08f4` + 9 txs | `MAJORITY_AGREE` | `SUCCESS` | `ESCALATE` | 15.1s - 104.7s | Initial fill + 9 filler actions evaluated by model as `ESCALATE` (`source: JUDGE`), bringing queue to 10. |
| **Case 8** | 10th filler attempt (Cap Exceeded) | `0x7289222372a79b933aa9f3b19dc39352539725062c782661e557efdbe0c47ada` | `MAJORITY_AGREE` | `ERROR` | N/A | 5.37s | Queue already at 10. Reverted at gate: `"too many pending escalations"`. |
| **Case 8** | 11th check action (Cap Exceeded) | `0x9751c07ba6ca6d67926821096093f1090debc9beea6aec94abb6dcc38ba1af93` | `MAJORITY_AGREE` | `ERROR` | N/A | 8.49s | Reverted at gate: `"too many pending escalations"`. |
| **Case 8** | Owner resolves 1 pending item | `0x3158f601f9eafc5dc64d53d6cf0cbd9c7841dfef823e8e3d6247ac3aec917315` | `MAJORITY_AGREE` | `SUCCESS` | `DENY` | 9.47s | Frees 1 pending slot. |
| **Case 8** | 12th action retried | `0x561cdd7d4b7a9682d74a0929f840ee6fcbe9d73543ae0f23e9eab31b592a44c0` | `MAJORITY_AGREE` | `SUCCESS` | `ESCALATE` | 71.57s | Enters queue successfully as Decision 21. |
| **Case 9** | Execute Decision 1 on GuardedVaultV2 | `0xb4f75402c09bea6fdbf1609e0079eb089d485a93871887b71390c1150cd84280` | `MAJORITY_AGREE` | `SUCCESS` | N/A | 8.49s | Executed successfully; `is_executed(1)` is `True`. |
| **Case 9** | Replay Decision 1 on GuardedVaultV2 | `0xe6ef8621642d51299381ecbc34f9c5505b093e9bc28c0a25f594bf8e94b9c23e` | `MAJORITY_AGREE` | `ERROR` | N/A | 5.17s | Reverted: `"decision has already been executed"`. |
| **Case 9** | Parameter mismatch on vault execute | `0x75672bf05a8eddbcdc29b57d160d6a4b0a2ba8487582cef2eaa38e0bc553d386` | `MAJORITY_AGREE` | `ERROR` | N/A | 8.54s | Reverted: `"clearance does not match this action"`. |
| **Case 9** | Execute on paused policy | `0xfdd8b9bc0b3f3d2532303e7e7efbb741f54435296e37841002258a592df86f9b` | `MAJORITY_AGREE` | `ERROR` | N/A | 8.61s | Reverted: `"clearance does not match this action"`. |
| **Case 10.1** | Newline in justification | `0x966193eb70e1cbbae121de5035928b1851f24da7ac91b29b0f94084eea5dbaa7` | `MAJORITY_AGREE` | `ERROR` | N/A | 5.47s | Reverted: `"justification length must be between 5 and 600 characters without control chars"`. |
| **Case 10.2** | Justification < 5 characters | `0x44f74cffb65094c12389abcc94be6a4e62ab96e76f43049bb7ad01cad82134bb` | `MAJORITY_AGREE` | `ERROR` | N/A | 5.21s | Reverted: `"justification length must be between 5 and 600 characters without control chars"`. |
| **Case 10.3** | Non-agent sender | `0x34fbf261cc43b553b5a4a11ce2d8b76096aa095f4d6d2bc6767eca2b938684ec` | `MAJORITY_AGREE` | `ERROR` | N/A | 5.24s | Reverted: `"only the registered agent may request actions"`. |
| **Case 10.4** | Calldata hash not 64 hex chars | `0x37f65120e973d5d7eaacfc4fca30a2394329852d5f6d88a4ec596a76beeb38d9` | `MAJORITY_AGREE` | `ERROR` | N/A | 5.24s | Reverted: `"calldata_hash must be a 64-character hex string"`. |
| **Case 10.5** | Amount zero | `0xce4936a7f3bb98bcfc9142672565528fc22b11cb733eccc5b1f86533b3cdb210` | `MAJORITY_AGREE` | `ERROR` | N/A | 8.52s | Reverted: `"amount must be >= 1"`. |
| **Case 11** | Latency benchmark calculation | Computed by script | N/A | N/A | N/A | N/A | Complete dataset persisted in `docs/evidence_v2/case_11_latency.json`. |
| **Case 12** | Stats read-back | Read View Call | N/A | N/A | N/A | Instant | Real stats match transaction history tallies across Policies 1, 2, and 3. |

---

## 3. Latency Summary (Recomputed by Mechanism)

- **Judged Writes (n=20)**: Min `15.12s` | Mean `38.79s` | Max `115.01s`
- **Guard-Only Writes (n=5)**: Min `8.75s` | Mean `9.06s` | Max `9.56s`
- **Admin Writes (n=11)**: Min `5.27s` | Mean `8.33s` | Max `12.57s`
- **Reverted Validation Gates (n=14)**: Min `5.17s` | Mean `7.05s` | Max `9.66s`

