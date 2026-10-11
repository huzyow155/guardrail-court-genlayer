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
  - `max_amount`: Per-action cap string (non-negative integer <= 18 digits, `"0"` = unlimited).
  - `window_cap`: 10-action rolling window cap string (non-negative integer <= 18 digits, `"0"` = unlimited).
- **Returns**: `policy_id` (e.g., `"1"`).
- **Latency**: ~1-3s (deterministic execution).

#### 2. `set_paused(policy_id: str, paused: bool) -> None`
- **Caller**: Must be the policy `owner`.
- **Purpose**: Emergency pause switch. When paused, `request_action` immediately rejects requests.
- **Errors**: Raises `"only the policy owner may pause or unpause"`.
- **Latency**: ~1-3s.

#### 3. `request_action(policy_id: str, category: str, amount: str, description: str) -> str`
- **Caller**: Must be the designated `agent` of the policy.
- **Parameters**:
  - `policy_id`: ID of the policy to evaluate against.
  - `category`: Category string matching `^[a-z0-9_-]{1,30}$`.
  - `amount`: Non-negative integer string <= 18 digits.
  - `description`: Untrusted description of the proposed action (5 to 600 chars).
- **Returns**: `decision_id` (e.g., `"1"`).
- **Latency**:
  - `HARD_LIMIT` / `VELOCITY` trips: ~1-3s.
  - Validator LLM consensus (`JUDGE`): ~15-25s.

#### 4. `resolve_escalation(decision_id: str, outcome: str) -> None`
- **Caller**: Must be the policy `owner`.
- **Parameters**:
  - `decision_id`: ID of the decision with status `PENDING_OWNER`.
  - `outcome`: String `"ALLOW"` or `"DENY"`.
- **Latency**: ~1-3s.

---

## Public View Methods

| Method | Parameters | Return Type | Description |
| :--- | :--- | :--- | :--- |
| `is_cleared` | `decision_id: str` | `bool` | Returns `true` if decision status is `CLEARED`, otherwise `false`. Primary hook for executors. |
| `get_policy` | `policy_id: str` | `str` (JSON) | Retrieves full policy object. |
| `get_decision` | `decision_id: str` | `str` (JSON) | Retrieves full decision object. |
| `list_policies_by_owner`| `owner: str, limit: int` | `str` (JSON array) | Returns newest policies created by owner (limit <= 20). |
| `list_policies_by_agent`| `agent: str, limit: int` | `str` (JSON array) | Returns newest policies assigned to agent (limit <= 20). |
| `list_decisions` | `policy_id: str, limit: int`| `str` (JSON array) | Returns recent decisions under policy (limit <= 20). |
| `pending_escalations` | `policy_id: str` | `str` (JSON array) | Returns all decisions currently awaiting owner resolution. |
| `latest_decision_id` | `policy_id: str` | `str` | Returns the newest decision ID string. |
| `get_policy_stats` | `policy_id: str` | `str` (JSON) | Breakdown of verdicts, sources, cleared, and pending counts. |

---

## Exact JSON Schemas (From Live On-Chain State)

### Policy Record Schema
```json
{
  "schema_version": "1",
  "id": "1",
  "owner": "0xe5baa16fa51409c5649ada121dfc156db9b1a36b",
  "agent": "0x2ed1c538aeae0f1c1c0409280972c05e760a3504",
  "text": "The agent may buy cloud credits, domain renewals and developer tools...",
  "policy_sha": "c6a94334a7b4b8b174071faa94f089e331fcc05a756e77f8f6a246e8d7656578",
  "max_amount": "100",
  "window_cap": "400",
  "paused": false,
  "seq": "1"
}
```

### Decision Record Schema
```json
{
  "schema_version": "1",
  "id": "1",
  "policy_id": "1",
  "seq": "1",
  "category": "dev_tools",
  "amount": "45",
  "description": "Annual domain renewal for api.myservice.io via DNS registrar",
  "verdict": "ALLOW",
  "source": "JUDGE",
  "status": "CLEARED",
  "resolved_by_owner": false
}
```

### Policy Stats Schema
```json
{
  "schema_version": "1",
  "policy_id": "1",
  "total_decisions": 1,
  "cleared_count": 1,
  "pending_owner_count": 0,
  "verdicts": {
    "ALLOW": 1,
    "DENY": 0,
    "ESCALATE": 0
  },
  "sources": {
    "HARD_LIMIT": 0,
    "VELOCITY": 0,
    "JUDGE": 1
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
When verifying GenLayer transactions, a transaction is only successful when **both** conditions hold:
```javascript
const isSuccess = receipt.status_name === 'ACCEPTED' &&
  receipt.consensus_data?.leader_receipt?.[0]?.execution_result === 'SUCCESS';
```
If `result_name` indicates `UNDETERMINED` or `MAJORITY_DISAGREE`, check `receipt.result.payload` for the underlying error message.
