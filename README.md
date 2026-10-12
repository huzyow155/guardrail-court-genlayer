# Guardrail Court

> Natural-language policy gate and multi-validator clearance protocol for autonomous AI agents on GenLayer Studionet.

## Status: Preview

**Contract Address**: [`0x6C553Ba27a768D71b570a106D9D2e13553b4103c`](https://explorer-studio.genlayer.com/address/0x6C553Ba27a768D71b570a106D9D2e13553b4103c)  
**Network**: GenLayer Studionet (Chain ID: 61999)  
**Deploy Transaction**: `0xe7a7ec9e6e1b1cf9f07696d251dc08118b7c865121551107850abb2938d81136`  
**License**: MIT (c) 2026 Hyper

---

## The Problem

Autonomous AI agents equipped with discretionary capabilities, API tokens, or on-chain signing keys operate faster than humans can review. Currently, the entity deciding whether a planned action complies with an owner's intent is typically the agent itself or a single prompt guardrail running on the same host infrastructure. If an agent hallucinates, suffers a prompt injection, or operates under misaligned incentives, unauthorized actions execute immediately without independent review.

---

## The Solution: Guardrail Court

**Guardrail Court** is an on-chain intelligent policy gate where human owners define plain-language rules alongside hard numeric spending parameters. Before taking discretionary actions, the registered agent submits an action request to the contract.

```
                      +-----------------------------+
                      |   AI Agent Action Request   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    1. Hard Limit Guard      |  > max_amount? -> DENY (Zero LLM, ~5s)
                      +--------------+--------------+
                                     | Passes
                                     v
                      +-----------------------------+
                      |  2. Velocity History Guard  |  Cleared sum in category (max 10) > window_cap? -> ESCALATE (~5s)
                      +--------------+--------------+
                                     | Passes
                                     v
                      +-----------------------------+
                      |   3. Multi-Validator LLM    |
                      |          Consensus          |  strict_eq(ALLOW | DENY | ESCALATE)
                      +--------------+--------------+
                                     |
             +-----------------------+-----------------------+
             |                       |                       |
             v                       v                       v
      +--------------+        +--------------+        +--------------+
      |    ALLOW     |        |     DENY     |        |   ESCALATE   |
      | (CLEARED)    |        |   (DENIED)   |        |  (Owner Box) |
      +--------------+        +--------------+        +-------+------+
                                                              |
                                                              v
                                                      Owner Resolves:
                                                      ALLOW or DENY
```

### 1. Two-Tier Evaluation Architecture
1. **Deterministic Guard (Pre-LLM)**:
    - `HARD_LIMIT`: If `amount > max_amount`, rejects immediately with `source: HARD_LIMIT` and `status: DENIED` (5.26s measured).
    - `VELOCITY`: Computes total amount of up to 10 most recent cleared decisions in the same category. If `sum + amount > window_cap`, routes directly to `source: VELOCITY` and `status: PENDING_OWNER` (5.30s measured). Note: Does not aggregate across time duration or across different categories.
2. **Multi-Validator Consensus (`JUDGE`)**:
   - Actions within numeric limits are dispatched to independent validators executing diverse model families.
   - Validators reach consensus exclusively on a single canonical enum: `ALLOW`, `DENY`, or `ESCALATE` (measured range: 11.93s to 32.03s, exact arithmetic mean: 19.02s across n=8 verified transactions).
   - Any ambiguous purchase or malformed response fails closed to `ESCALATE`.

---

## Non-Goals
- **No Execution or Custody**: The contract does not execute transactions, custody tokens, or hold private keys. It publishes clearance decisions.
- **Demo Consumer Role**: The accompanying `GuardedVault` consumer contract is a test harness illustrating cross-contract clearance verification via `court.view().is_cleared(decision_id)`. It does not custody or transfer real cryptocurrencies.
- **Advisory Role**: The contract is advisory unless downstream executors verify `is_cleared(decision_id)`.
- **Currency Agnostic**: The contract does not interpret denominations (USD, EUR, ETH, wei); amounts are non-negative integer strings.
- **Unreported Actions**: It cannot constrain actions that an agent operator fails to submit.
- **Not Scoped Credentials**: It is an audit and authorization gate, not an IAM or API key replacement.

---

## On-Chain Verified Evidence (Studionet)

Transactions executed and verified on GenLayer Studionet (see [`docs/VERIFICATION.md`](docs/VERIFICATION.md) and [`docs/RECEIPTS.md`](docs/RECEIPTS.md)):

| Run | Scenario | Transaction Hash | Verdict | Source | Latency | `is_cleared` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **(a)** | Clear ALLOW (Domain renewal) | `0x9a52e1031febbdbde4c9bdccb85b31a8a4212ae0c403a4836253f9571bb6d131` | `ALLOW` | `JUDGE` | 11.93s | `true` |
| **(b)** | Clear DENY (Gift card for individual) | `0xf6cee5bcec34932a6022bff401307fa2aac906632cc5ec1ea021d727003c90df` | `DENY` | `JUDGE` | 15.45s | `false` |
| **(c)** | Ambiguous purchase (Conference pass & lunch) | `0xad1894bed165db218c7e66151efc3fe31148d7feca1deaf777baa0876e184d81` | `ESCALATE` | `JUDGE` | 18.57s | `false` |
| **(d)** | `HARD_LIMIT` DENY (Amount 150 > cap 100) | `0x60251f8d782ac69f51b55cd4b545e36862163b52a3d63735440138bf52e7af05` | `DENY` | `HARD_LIMIT` | 5.26s | `false` |
| **(e)** | Salami-slicing velocity trip (5 x 90 > 400) | `0x87339f78182a6b95bbc465154b9b0ed825f4aa5687665d1585d5e631387e1604` | `ESCALATE` | `VELOCITY` | 5.30s | `false` |
| **(f)** | Owner resolves Decision 3 to ALLOW | `0x5fbd13afeef7029c70ee2b51377a1e0d8646517aa269430c25b784137b25fadd` | `ALLOW` | Owner | 8.47s | `true` |
| **(g)** | Prompt injection resistance on casino token | `0x5f71327df1b6d8c725572cc9e7572b16c186ddf6efc0bf497ce6a68eed33ff67` | `DENY` | `JUDGE` | 15.28s | `false` |
| **(h)** | Owner Pause kill-switch toggle | `0xf739cb6bb69a7d4a9a065b16be46edf6c721fd6453548b666bca46ba40fa93a4` | `PAUSED` | Owner | 4.88s | Rejects writes |

---

## How to Test

```bash
# Run all layered tests (Pure logic, mocked simulator, consensus simulation, boundary checks)
# Note: Layer 2 and Layer 3 tests execute against an off-chain Python simulator and do not execute under GenVM.
python -m unittest discover tests

# Run security scanners
python scripts/scan_secrets.py
python scripts/scan_banned_words.py
python scripts/scan_ascii.py
```

---

## Deploy to Studionet

```bash
# Install SDK dependencies
npm install

# Deploy probe contract (Milestone 0)
node scripts/deploy/deploy_probe.js

# Deploy core contract verification (Milestone 1)
node scripts/deploy/deploy_core.js

# Deploy full contract and run evidence rounds (Milestone 4)
node scripts/deploy/run_live_evidence.js

# Deploy consumer contract for cross-contract validation (Milestone 5)
node scripts/deploy/deploy_consumer.js
```

---

## Documentation Links
- [`docs/PRIOR_ART.md`](docs/PRIOR_ART.md): Prior art comparison against NeMo Guardrails, OPA, and Safe modules.
- [`docs/DESIGN.md`](docs/DESIGN.md): Consensus primitive design and state schema.
- [`docs/INTEGRATION.md`](docs/INTEGRATION.md): Integration guide for agent runtimes and frontend dashboards.
- [`docs/RUNTIME_NOTES.md`](docs/RUNTIME_NOTES.md): Runtime probe measurements and GenVM behavior.
- [`docs/VERIFICATION.md`](docs/VERIFICATION.md): Deployment hashes, byte-for-byte SHA-256 verification, and receipts.
- [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md): Known limitations, performance characteristics, and threat model.
- [`docs/ERROR_CODES.md`](docs/ERROR_CODES.md): Catalogue of all UserError strings and preconditions.
