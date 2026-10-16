# Guardrail Court V2 - Architecture & Design Specification

## 1. Context & Motivation

Following independent security review by zoefunds, Guardrail Court V1 was identified to have two architectural limitations:
1. Clearance was based on natural-language agent descriptions without being bound to the recipient, asset, amount, calldata, or downstream execution.
2. The model parser contained a fallback substring scan that could fail open to `ALLOW` on contradictory, prose-heavy, or malformed outputs.

Guardrail Court V2 provides a comprehensive, ground-up upgrade resolving both vulnerabilities while preserving the determinism and decentralization guarantees of GenLayer Studionet.

---

## 2. Key Changes from V1 to V2

| Feature | Guardrail Court V1 (Legacy) | Guardrail Court V2 |
| :--- | :--- | :--- |
| **Action Clearance** | Unbound advisory flag `is_cleared(decision_id)` | Strictly parameterized binding `is_cleared_for(decision_id, policy_id, category, recipient, asset, amount, calldata_hash)` |
| **Action Identity** | Natural-language description only | Canonical `action_hash = sha256("GC2\|{policy_id}\|{category}\|{recipient}\|{asset}\|{amount}\|{calldata_hash}")` |
| **Model Parser** | Substring fallback scanning for `"VERDICT": "ALLOW"` | Strict single-key JSON parser with duplicate key rejection and dual-token contradiction guard |
| **Parser Fallback Mode** | Fail-open on prose quoting ALLOW | Strict fail-closed: any deviation, extra key, prose, or contradiction resolves to `ESCALATE` |
| **Allowlists** | None (description text only) | Mandatory `allowed_recipients` (1-10 addresses) and `allowed_assets` (1-10 assets) enforced prior to LLM |
| **Spending Limits** | `max_amount=0` (unlimited cap permitted) | Mandatory `max_amount >= 1` and `window_cap >= max_amount` |
| **Velocity Scope** | Filtered by category (evadable via category rotation) | Evaluates all `CLEARED` decisions across the entire policy (last 30 decisions) |
| **Queue Anti-Spam** | Unbounded pending queue | Hard limit: reverts if `>= 10` decisions are currently in `PENDING_OWNER` status |
| **Prompt Construction** | Delimited blocks `=== BEGIN/END ===` | Single structured JSON object; explicit prompt instruction that `justification` is untrusted |
| **Consumer Contract** | `GuardedVault.execute(decision_id, note)` | `GuardedVaultV2.execute(decision_id, policy_id, category, recipient, asset, amount, calldata_hash)` |

---

## 3. Trust Model & Scope of Guarantees

Guardrail Court V2 enforces strict invariants within its execution boundary. To prevent downstream false assumptions, its exact guarantees and non-guarantees are defined below:

### What Guardrail Court V2 Binds & Enforces:
1. **Parameter Integrity**: Clearance is tied 1-to-1 to the exact tuple `(policy_id, category, recipient, asset, amount, calldata_hash)`. Any deviation in downstream execution causes `is_cleared_for` to return `False`.
2. **Deterministic Pre-LLM Filters**:
   - `HARD_LIMIT`: Requests exceeding `max_amount` are immediately rejected with `DENIED` status.
   - `RECIPIENT_GUARD`: Requests with recipients not in `allowed_recipients` are immediately rejected with `DENIED` status.
   - `ASSET_GUARD`: Requests with assets not in `allowed_assets` are immediately rejected with `DENIED` status.
   - `VELOCITY`: Sum of cleared amounts across the last 30 policy decisions exceeding `window_cap` forces `ESCALATE` status.
   - `QUEUE_CAP`: Reverts if agent creates more than 10 pending escalations without owner triage.
3. **Fail-Closed Consensus Parsing**: Only identical, clean `{"verdict": "ALLOW"}` output from GenLayer validator consensus can clear an action.

### What Guardrail Court V2 CANNOT and DOES NOT Guarantee:
1. **Calldata Opacity & Caller Assertion**: `calldata_hash` is a string supplied by the caller; the contract binds it into `action_hash` but cannot verify it equals the hash of any real calldata, and the validators do not decode calldata. The consumer must hash the calldata it will actually execute and pass that same value.
2. **Real-World Entity Identity**: The Court verifies that `recipient` is an authorized 42-character hex address on the allowlist. It does not know the real-world identity, beneficial ownership, or legal status of the recipient.
3. **Downstream Enforcement Compliance**: `GuardrailCourtV2` cannot force downstream protocols to query `is_cleared_for`. Downstream consumers (e.g. `GuardedVaultV2`) must explicitly call `court.view().is_cleared_for(...)` and revert if `False`.
4. **Agent Justification Veracity**: The `justification` text submitted by the agent is strictly untrusted natural language. The Court instructs the validator LLM to ignore justifications that contradict structured parameters or policy guidelines.
5. **No Wall-Clock Timestamp in Velocity**: GenVM state access does not provide reliable real-time clocks across validator nodes. The velocity window is measured strictly over the latest 30 discrete decision records on-chain.
