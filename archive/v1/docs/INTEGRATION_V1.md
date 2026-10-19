# Integration Guide: Guardrail Court

## Overview
**Guardrail Court** is an on-chain advisory gate on GenLayer Studionet designed for autonomous AI agents and automated executors. Downstream executors (vaults, paymasters, trading bots, API wrappers) query `is_cleared(decision_id)` before releasing assets or triggering external side effects.

---

## Contract Interface

### Public Write Methods

#### 1. `create_policy(agent: str, text: str, max_amount: str, window_cap: str) -> str`
- **Caller**: Becomes the `owner` of the policy.
- **Parameters**:
  - `agent`: Hex address string of the AI agent (`0x...` 40 hex chars).
  - `text`: Natural-language policy description (30 to 1200 chars).
  - `max_amount`: Per-action cap string (non-negative integer <= 18 digits; `"0"` = unlimited / disables `HARD_LIMIT`).
  - `window_cap`: Category velocity spending cap string (`"0"` = unlimited / disables `VELOCITY`). When `window_cap > 0`, `request_action` scans `policy_history_ids[:15]` (the 15 most recent decisions of the entire policy across all categories), filters for decisions matching `category` (taking up to 10 matching items), and sums `amount` where `status == "CLEARED"` or `verdict == "ALLOW"`. If `cleared_sum + amount > window_cap`, the request escalates with `source: VELOCITY`.
- **Returns**: `policy_id` (e.g., `"1"`).
- **Latency**: Deterministic state write (measured Studionet deterministic writes in `live_evidence.json`: 5.261s - 5.305s for guards, 8.472s for owner resolution; 3s polling interval introduces +/-3s quantization).

#### 2. `set_paused(policy_id: str, paused: bool) -> None`
- **Caller**: Must be the policy `owner`.
- **Purpose**: Emergency pause switch. When paused, `request_action` immediately rejects requests.
- **Errors**: Raises `"only the policy owner may pause or unpause"`.
- **Latency**: Deterministic state write (not timed with `latencySec` in `live_evidence.json`; comparable deterministic writes measured 5.261s - 8.472s with 3s polling interval).

#### 3. `request_action(policy_id: str, category: str, amount: str, description: str) -> str`
- **Caller**: Must be the designated `agent` of the policy.
- **Parameters**:
  - `policy_id`: ID of the policy to evaluate against.
  - `category`: Category string matching `^[a-z0-9_-]{1,30}$`.
  - `amount`: Non-negative integer string <= 18 digits.
  - `description`: Untrusted description of the proposed action (5 to 600 chars).
- **Returns**: `decision_id` (e.g., `"1"`).
- **Latency**:
  - `HARD_LIMIT` / `VELOCITY` trips: **5.261s** and **5.305s** (n=2 measured in `live_evidence.json`, 3s polling interval).
  - Validator LLM consensus (`JUDGE`): **11.934s to 32.026s** (measured arithmetic mean: **19.02s**, n=8 in `live_evidence.json`, 3s polling interval).

#### 4. `resolve_escalation(decision_id: str, outcome: str) -> None`
- **Caller**: Must be the policy `owner`.
- **Parameters**:
  - `decision_id`: ID of the decision with status `PENDING_OWNER`.
  - `outcome`: String `"ALLOW"` or `"DENY"`.
- **Latency**: **8.472s** (n=1 measured in `live_evidence.json`, 3s polling interval).

---

## Public View Methods

| Method | Parameters | Return Type | Description |
| :--- | :--- | :--- | :--- |
| `is_cleared` | `decision_id: str` | `bool` | Returns `true` if decision status is `CLEARED`, otherwise `false`. Advisory flag only; executors must also verify `get_decision(decision_id)` fields (`policy_id`, `category`, `amount`, `description`) match the action being executed. |
| `get_policy` | `policy_id: str` | `str` (JSON) | Retrieves full policy object. |
| `get_decision` | `decision_id: str` | `str` (JSON) | Retrieves full decision object. |
| `list_policies_by_owner`| `owner: str, limit: int` | `str` (JSON array) | Returns newest policies created by owner (limit <= 20; `by_owner` index capped at 50). |
| `list_policies_by_agent`| `agent: str, limit: int` | `str` (JSON array) | Returns newest policies assigned to agent (limit <= 20; `by_agent` index capped at 50). |
| `list_decisions` | `policy_id: str, limit: int`| `str` (JSON array) | Returns recent decisions under policy (limit <= 20; `by_policy` index capped at 60). |
| `pending_escalations` | `policy_id: str` | `str` (JSON array) | Scans `id_list[:20]` of `by_policy` and returns decisions with `status == "PENDING_OWNER"`. |
| `latest_decision_id` | `policy_id: str` | `str` | Returns the newest decision ID string (`id_list[0]`). |
| `get_policy_stats` | `policy_id: str` | `str` (JSON) | Breakdown of verdicts, sources, cleared, and pending counts across up to 60 stored IDs in `by_policy`. |

---

## Exact JSON Schemas (Verbatim from `scripts/deploy/state_fresh.json`)

### Policy Record Schema (`get_policy("1")`)
```json
{
  "agent": "0x1b1e4a79e286434c428a576e6d91bc2220661cf3",
  "id": "1",
  "max_amount": "100",
  "owner": "0x1bdbf9d058492d2bb0553bf3d9ac5730b5e5d3be",
  "paused": true,
  "policy_sha": "c6a94334a7b4b8b174071faa94f089e331fcc05a756e77f8f6a246e8d7656578",
  "schema_version": "1",
  "seq": "10",
  "text": "The agent may buy cloud credits, domain renewals and developer tools. It may not buy gift cards, tokens, gambling, adult content, or anything intended as a gift to an individual. If a purchase is ambiguous, escalate to the owner.",
  "window_cap": "400"
}
```

### Decision Record Schema (`get_decision("1")`)
```json
{
  "amount": "45",
  "category": "dev_tools",
  "description": "Annual domain renewal for api.myservice.io via DNS registrar",
  "id": "1",
  "policy_id": "1",
  "resolved_by_owner": false,
  "schema_version": "1",
  "seq": "1",
  "source": "JUDGE",
  "status": "CLEARED",
  "verdict": "ALLOW"
}
```

### Policy Stats Schema (`get_policy_stats("1")`)
```json
{
  "cleared_count": 6,
  "pending_owner_count": 1,
  "policy_id": "1",
  "schema_version": "1",
  "sources": {
    "HARD_LIMIT": 1,
    "JUDGE": 8,
    "VELOCITY": 1
  },
  "total_decisions": 10,
  "verdicts": {
    "ALLOW": 6,
    "DENY": 3,
    "ESCALATE": 1
  }
}
```

---

## Standard User Error Messages

All user errors are raised as `gl.vm.UserError` with distinct messages:
- `"agent must be a valid address"`
- `"policy text length must be between 30 and 1200 characters"`
- `"max_amount must be a valid non-negative integer string"`
- `"window_cap must be a valid non-negative integer string"`
- `"policy not found"`
- `"policy is paused"`
- `"only the registered agent may request actions"`
- `"only the policy owner may pause or unpause"`
- `"only the policy owner may resolve escalations"`
- `"invalid category format"`
- `"amount must be a valid non-negative integer string"`
- `"description length must be between 5 and 600 characters"`
- `"decision not found"`
- `"decision is not pending owner resolution"`
- `"decision has already been resolved"`
- `"outcome must be ALLOW or DENY"`

---

## Receipt Success Rule
When verifying GenLayer transactions, a transaction is only successful when **all three** conditions hold:
```javascript
const isSuccess =
  receipt.status_name === 'ACCEPTED' &&
  receipt.result_name === 'MAJORITY_AGREE' &&
  receipt.consensus_data?.leader_receipt?.[0]?.execution_result === 'SUCCESS';
```
If `execution_result` is `'ERROR'` or `result_name` is not `'MAJORITY_AGREE'`, inspect `receipt.consensus_data?.leader_receipt?.[0]?.result?.payload` or `genvm_result.stderr` for the underlying error details.
