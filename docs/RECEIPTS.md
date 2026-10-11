# Transaction Receipts Registry (Three-Condition Verification)

This document catalogues the transaction receipts for all deployed contracts and live execution rounds on GenLayer Studionet (Chain ID 61999).

> **Receipt Verification Rules on GenLayer Studionet**:
> 1. `status_name`: Expected `ACCEPTED` (or `FINALIZED` when read retroactively after finalization block range).
> 2. `result_name`: Expected `MAJORITY_AGREE` (indicates validator consensus reached agreement).
> 3. `consensus_data.leader_receipt[0].execution_result`:
>    - `SUCCESS` for valid state transitions.
>    - `ERROR` for expected policy, boundary, or permission rejections (with exact `gl.vm.UserError` string returned in `result.payload`).

---

## Complete Receipts Matrix

| Category / Step | Transaction Hash | `status_name` | `result_name` | Leader Result | Notes / On-Chain Payload |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Probe Deploy** | `0xef76f606fb197b9366042827e4c509fb44d126d71c86d7690fa8ebc2b5061368` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Probe contract deployed to `0xCafd1A56...` |
| **Probe Consensus** | `0xcb6562321804ccc0e724a33e2ef6e6bd6549cc7e425f659884935556777eda6e` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Strict equality consensus verified |
| **Core Deploy** | `0x398f6c55e1daf336e8f85ab75b1487ae518ed04eb0a5bcfbfba2d8bc61b5035b` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Core contract deployed to `0xAA4eaa01...` |
| **Core Create Policy** | `0x1059582b37275e5a39c46ce31430c5cde8f92dd3fbb58b90019e88e2ecad81bc` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Initial policy created |
| **Core Action 1** | `0x44e19c924882ec03fea2ab94d1b76d5d6ee20e41a974eca9e2b6079dc7b77b2b` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Action 1 evaluated and cleared |
| **Full Deploy (Official)** | `0xe7a7ec9e6e1b1cf9f07696d251dc08118b7c865121551107850abb2938d81136` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Official `GuardrailCourt` (`0x6C553Ba2...`) |
| **Full Create Policy 1** | `0x83dc3ed5ca97b34c9d508e0593d61428ad3a734836f183fc3d84bb3f4e6d677e` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Policy 1 (Cap 100, Window Cap 400) |
| **Run (a) Clear ALLOW** | `0x9a52e1031febbdbde4c9bdccb85b31a8a4212ae0c403a4836253f9571bb6d131` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 1 (Domain renewal): `ALLOW` (`JUDGE`) |
| **Run (b) Clear DENY** | `0xf6cee5bcec34932a6022bff401307fa2aac906632cc5ec1ea021d727003c90df` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 2 (Gift card): `DENY` (`JUDGE`) |
| **Run (c) Model ESCALATE** | `0xad1894bed165db218c7e66151efc3fe31148d7feca1deaf777baa0876e184d81` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 3 (Conference ticket): `ESCALATE` (`JUDGE`) |
| **Run (d) HARD_LIMIT DENY** | `0x60251f8d782ac69f51b55cd4b545e36862163b52a3d63735440138bf52e7af05` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 4 (Amount 150 > 100): `DENY` (`HARD_LIMIT`) |
| **Run (e-1) Velocity Slice 1** | `0x0e4fc56d48bd1e9ff4de153f84245902e72387d3705f1e20eaf971666ad15d80` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 5 (Cloud ops 90): `ALLOW` (`JUDGE`) |
| **Run (e-2) Velocity Slice 2** | `0x678e4979af4e252688ab3b11fa77a0fa791956695a1234c5012afd4315bcf8c0` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 6 (Cloud ops 90): `ALLOW` (`JUDGE`) |
| **Run (e-3) Velocity Slice 3** | `0x9e9077d4141eb1ab5809deefcaba5afd95d86676bc7a081f77eac10ba42e7869` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 7 (Cloud ops 90): `ALLOW` (`JUDGE`) |
| **Run (e-4) Velocity Slice 4** | `0x923e276540c49d16e7a3bbd0450da16623bb67861825ae1216796beb4e914a04` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 8 (Cloud ops 90): `ALLOW` (`JUDGE`) |
| **Run (e-5) Velocity Slice 5** | `0x87339f78182a6b95bbc465154b9b0ed825f4aa5687665d1585d5e631387e1604` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 9 (Salami slice 90): `ESCALATE` (`VELOCITY`) |
| **Run (f) Owner Resolve** | `0x5fbd13afeef7029c70ee2b51377a1e0d8646517aa269430c25b784137b25fadd` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 3 resolved to `ALLOW` by owner |
| **Run (g) Injection Test** | `0x5f71327df1b6d8c725572cc9e7572b16c186ddf6efc0bf497ce6a68eed33ff67` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Decision 10 (Casino voucher): `DENY` (`JUDGE`) |
| **Run (h) Policy 1 Pause** | `0xf739cb6bb69a7d4a9a065b16be46edf6c721fd6453548b666bca46ba40fa93a4` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Policy 1 paused: `paused: true` |
| **Policy 2 Create** | `0x9aa708d8932c09b646f08102adb5badf374a7684ea18193f19a8ad55f40cf4e6` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Created Policy 2 for dedicated permission audit |
| **Intruder Request Action** | `0xe62d783d1e913b169641c3f398349925af9650b3b89be094947159c20870047e` | `FINALIZED` | `MAJORITY_AGREE` | `ERROR` | Blocked: `only the registered agent may request actions` |
| **Intruder Set Paused** | `0x6ce369518733bab92c962ee8e46c873615049f8ad6ae89894e8ee971e07b22c4` | `FINALIZED` | `MAJORITY_AGREE` | `ERROR` | Blocked: `only the policy owner may pause or unpause` |
| **Policy 2 Owner Pause** | `0xe78850e17b1b513b6bcb66a4db6ed006556807290c5592f2852ab3a303b95a9e` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Policy 2 paused by owner |
| **Agent Action while Paused** | `0x3679e7700b0f95f39f8031ebce3cbee8cbe88757ae617430f7c4516a4824e300` | `FINALIZED` | `MAJORITY_AGREE` | `ERROR` | Blocked: `policy is paused` |
| **Policy 2 Owner Resume** | `0x8a3b779fd512bf3bbf4621416d1d619aea983c9f6f121c716e2203276ce29e7d` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Policy 2 unpaused (`paused: false`) |
| **GuardedVault Deploy** | `0x8b966471667987e8b1731cbf622437f7093ed81149b1050b74b34e51b41300ce` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Consumer contract deployed to `0xc3B3Ea32...` |
| **GuardedVault Execute Cleared** | `0x103a9f8bc7ff9e7fba40d4bd2fc429699ca4ebf23c969ec866c90fb60404e85a` | `FINALIZED` | `MAJORITY_AGREE` | `SUCCESS` | Cross-contract call verified: Decision 1 executed |
| **GuardedVault Neg 1 (Denied)** | `0x75b8e07483247932ef801f7986262f4aa51fc8428eeab82c388e317d23a31746` | `ACCEPTED` | `MAJORITY_AGREE` | `ERROR` | Blocked: `action is not cleared by GuardrailCourt` |
| **GuardedVault Neg 2 (Re-execute)** | `0x248f3b6745d99051ab8fa5c60d39b784559bc7be189ebc86b9c7be05ffbf59c1` | `ACCEPTED` | `MAJORITY_AGREE` | `ERROR` | Blocked: `decision has already been executed` |

---

*Note on status names*: When queried immediately after execution, status is reported as `ACCEPTED`. When queried retroactively across subsequent blocks, GenLayer consensus marks the block as `FINALIZED`. Both represent valid validator acceptance.
