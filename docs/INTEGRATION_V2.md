# Guardrail Court V2 Integration Guide (Preview)

Guardrail Court V2 is an intelligent policy gate and decision registry deployed on GenLayer Studionet (Chain ID 61999). It binds AI agent transactions to explicit policy boundaries, requiring consensus-verified model evaluation and strict action-hash validation before downstream execution.

---

## 1. Deployed Addresses (Preview)

- **GuardrailCourtV2**: `0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b`
  - Explorer: [https://explorer-studio.genlayer.com/address/0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b](https://explorer-studio.genlayer.com/address/0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b)
  - Source SHA-256: `94BDA609903A2ECC854269307E628E49869A36B466DAE7CD941553406E12F9F6`
- **GuardedVaultV2 (Consumer Reference)**: `0xc0dF70EE8BEC7003EF6CCfb24590b4D559699b58`
  - Explorer: [https://explorer-studio.genlayer.com/address/0xc0dF70EE8BEC7003EF6CCfb24590b4D559699b58](https://explorer-studio.genlayer.com/address/0xc0dF70EE8BEC7003EF6CCfb24590b4D559699b58)
  - Source SHA-256: `7CB69D7745B0C9354ECA3D1D712EBF7099726298128C3C45E54F8C7CC2060366`

---

## 2. Contract ABI & Public Methods

### GuardrailCourtV2 Methods

#### Write Methods
1. `create_policy(agent: str, text: str, max_amount: str, window_cap: str, allowed_recipients: str, allowed_assets: str) -> str`
   - Callable by: Any policy owner account.
   - Parameters:
     - `agent`: 42-character hex address string (`0x...`).
     - `text`: Policy instructions, between 30 and 1200 characters.
     - `max_amount`: Maximum allowed amount for any single transaction (positive integer string).
     - `window_cap`: Maximum rolling expenditure cap in 30-decision window (integer string >= `max_amount`).
     - `allowed_recipients`: JSON-encoded array or comma-separated list of 1 to 10 valid recipient addresses.
     - `allowed_assets`: JSON-encoded array or comma-separated list of 1 to 10 allowed asset symbols or contract addresses.
   - Returns: Newly allocated `policy_id` (string).

2. `set_paused(policy_id: str, paused: bool) -> None`
   - Callable by: Policy owner only.
   - Parameters:
     - `policy_id`: ID string of the target policy.
     - `paused`: `True` to pause (halts new requests and invalidates clearances); `False` to resume.

3. `request_action(policy_id: str, category: str, recipient: str, asset: str, amount: str, calldata_hash: str, justification: str) -> str`
   - Callable by: Registered agent address only.
   - Parameters:
     - `policy_id`: ID string of the policy.
     - `category`: Category tag string (1-30 chars, lowercase letters, digits, underscore, hyphen).
     - `recipient`: Target recipient address (42-char hex).
     - `asset`: Target asset identifier (e.g. `USDC`).
     - `amount`: Transaction amount (positive integer string).
     - `calldata_hash`: 64-character SHA-256 hex string of the downstream calldata.
     - `justification`: Plaintext justification string (5-600 characters without ASCII control characters).
   - Returns: Newly allocated `decision_id` (string).

4. `resolve_escalation(decision_id: str, outcome: str) -> None`
   - Callable by: Policy owner only.
   - Parameters:
     - `decision_id`: ID string of a decision currently in `PENDING_OWNER` status.
     - `outcome`: Resolution string, strictly `"ALLOW"` or `"DENY"`.

#### View Methods
1. `is_cleared_for(decision_id: str, policy_id: str, category: str, recipient: str, asset: str, amount: str, calldata_hash: str) -> bool`
   - Verifies whether a specific decision was cleared for the exact action parameters.
   - Returns `False` if policy does not exist, policy is paused, decision does not exist, status is not `CLEARED`, or any parameter diverges from the canonical action hash.

2. `get_action_hash(policy_id: str, category: str, recipient: str, asset: str, amount: str, calldata_hash: str) -> str`
   - Returns the canonical SHA-256 hash calculated as `SHA-256("GC2|" + policy_id + "|" + category + "|" + recipient + "|" + asset + "|" + amount + "|" + calldata_hash)`.

3. `is_cleared(decision_id: str) -> bool`
   - Advisory check returning whether `decision.status == "CLEARED"`. Downstream contracts should always call `is_cleared_for` instead.

4. `get_decision(decision_id: str) -> str`
   - Returns full JSON record of the decision.

5. `get_policy(policy_id: str) -> str`
   - Returns full JSON record of the policy.

6. `get_policy_stats(policy_id: str) -> str`
   - Returns JSON object with decision counts, verdicts, and source tallies.

7. `pending_escalations(policy_id: str) -> str`
   - Returns JSON list of decisions with status `PENDING_OWNER`.

8. `list_decisions(policy_id: str, limit: int = 10) -> str`
   - Returns JSON list of up to `limit` recent decisions for the policy.

---

## 3. Real Read-Back JSON Schemas

### Decision Record (`get_decision`)
```json
{
  "action_hash": "d1e58b5135c56d6f439e513e79c70b7225edb3c5b35e9dfde831f2257826ee6d",
  "amount": "40",
  "asset": "USDC",
  "calldata_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "category": "server_ops",
  "id": "1",
  "justification": "Monthly AWS server hosting renewal",
  "policy_id": "1",
  "recipient": "0x1111111111111111111111111111111111111111",
  "resolved_by_owner": false,
  "schema_version": "2",
  "seq": "1",
  "source": "JUDGE",
  "status": "CLEARED",
  "verdict": "ALLOW"
}
```

### Policy Record (`get_policy`)
```json
{
  "agent": "0xd2d6d647bc489f63fe5ed81114db9a70e1e6a766",
  "allowed_assets": [
    "USDC"
  ],
  "allowed_recipients": [
    "0x1111111111111111111111111111111111111111"
  ],
  "id": "1",
  "max_amount": "100",
  "owner": "0x726735ae8ebbd3bea9441ffa66ca934a8fdde4c9",
  "paused": false,
  "policy_sha": "d04fc9a95ec25d30907f1ea5d7107c1b50ce26d8ee150d0617ce71ebdfc8369b",
  "schema_version": "2",
  "seq": "10",
  "text": "Policy: operational server and infrastructure expenses only. Disallow luxury, entertainment, personal, or speculative purchases.",
  "window_cap": "400"
}
```

### Policy Stats Record (`get_policy_stats`)
```json
{
  "cleared_count": 2,
  "pending_owner_count": 3,
  "policy_id": "1",
  "schema_version": "2",
  "sources": {
    "ASSET_GUARD": 1,
    "HARD_LIMIT": 1,
    "JUDGE": 7,
    "RECIPIENT_GUARD": 1,
    "VELOCITY": 0
  },
  "total_decisions": 10,
  "verdicts": {
    "ALLOW": 2,
    "DENY": 5,
    "ESCALATE": 3
  }
}
```

---

## 4. UserError Catalog

The contract raises descriptive errors via `gl.vm.UserError`. Downstream integrations should anticipate these exact error strings:

| Method | Trigger Condition | Exact Error Message |
| :--- | :--- | :--- |
| `create_policy` | Invalid agent address format | `"agent must be a valid address"` |
| `create_policy` | Policy text < 30 or > 1200 chars | `"policy text length must be between 30 and 1200 characters"` |
| `create_policy` | Invalid integer for `max_amount` | `"max_amount must be a valid non-negative integer string"` |
| `create_policy` | `max_amount` < 1 | `"max_amount must be >= 1"` |
| `create_policy` | Invalid integer for `window_cap` | `"window_cap must be a valid non-negative integer string"` |
| `create_policy` | `window_cap` < `max_amount` | `"window_cap must be >= max_amount"` |
| `create_policy` | Allowed recipients list empty or > 10 | `"allowed_recipients must contain between 1 and 10 items"` |
| `create_policy` | Duplicate or invalid recipient address | `"invalid address in allowed_recipients"` / `"allowed_recipients must contain between 1 and 10 items"` |
| `create_policy` | Allowed assets list empty or > 10 | `"allowed_assets must contain between 1 and 10 items"` |
| `create_policy` | Invalid asset format | `"invalid asset in allowed_assets"` |
| `set_paused` | Policy ID not found | `"policy not found"` |
| `set_paused` | Caller is not policy owner | `"only the policy owner may pause or unpause"` |
| `request_action` | Policy ID not found | `"policy not found"` |
| `request_action` | Target policy is paused | `"policy is paused"` |
| `request_action` | Caller is not registered agent | `"only the registered agent may request actions"` |
| `request_action` | Invalid category characters | `"invalid category format"` |
| `request_action` | Recipient address invalid | `"recipient must be a valid address"` |
| `request_action` | Asset identifier invalid | `"invalid asset format"` |
| `request_action` | Amount < 1 or invalid integer | `"amount must be >= 1"` / `"amount must be a valid non-negative integer string"` |
| `request_action` | Calldata hash not 64 hex chars | `"calldata_hash must be a 64-character hex string"` |
| `request_action` | Justification has control chars or length < 5 or > 600 | `"justification length must be between 5 and 600 characters without control chars"` |
| `request_action` | Pending escalations queue >= 10 | `"too many pending escalations"` |
| `resolve_escalation`| Decision ID not found | `"decision not found"` |
| `resolve_escalation`| Caller is not policy owner | `"only the policy owner may resolve escalations"` |
| `resolve_escalation`| Decision not in `PENDING_OWNER` status | `"decision is not pending owner resolution"` |
| `resolve_escalation`| Outcome not `ALLOW` or `DENY` | `"outcome must be ALLOW or DENY"` |
| `GuardedVaultV2.execute` | Decision already executed | `"decision has already been executed"` |
| `GuardedVaultV2.execute` | Clearance check returns `False` | `"clearance does not match this action"` |

---

## 5. Measured On-Chain Latency Benchmarks

Measured across live transactions on GenLayer Studionet (Chain ID 61999):

| Category | Description | Transactions | Min Latency | Mean Latency | Max Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Admin Writes** | `create_policy`, `set_paused`, `resolve_escalation`, `execute` | 21 | 5.17s | 7.85s | 12.57s |
| **Guard-Only Writes** | `HARD_LIMIT`, `RECIPIENT_GUARD`, `ASSET_GUARD`, `VELOCITY` | 16 | 5.37s | 28.86s | 104.66s |
| **Judged Writes** | Validator consensus + non-deterministic model execution | 7 | 18.96s | 45.50s | 115.01s |

---

## 6. Consumer Contract Integration (`GuardedVaultV2` Reference)

Downstream smart contracts must integrate with Guardrail Court V2 by enforcing two atomic controls:
1. **Synchronous Cross-Contract Clearance Validation**: Call `court.view().is_cleared_for(...)` passing all 7 parameters (`decision_id`, `policy_id`, `category`, `recipient`, `asset`, `amount`, `calldata_hash`).
2. **Replay Prevention**: Maintain an on-chain mapping of executed `decision_id` keys to ensure clearances can only be executed once.

```python
# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from genlayer import *

class GuardedVaultV2(gl.Contract):
    guardrail_court_address: Address
    executions: TreeMap[str, str]

    def __init__(self, guardrail_court_address_str: str):
        self.guardrail_court_address = Address(guardrail_court_address_str)

    @gl.public.write
    def execute(
        self,
        decision_id: str,
        policy_id: str,
        category: str,
        recipient: str,
        asset: str,
        amount: str,
        calldata_hash: str,
    ) -> str:
        did = str(decision_id).strip()

        # 1. Prevent replay
        if did in self.executions:
            raise gl.vm.UserError("decision has already been executed")

        # 2. Strict cross-contract view check
        court = gl.get_contract_at(self.guardrail_court_address)
        is_cleared = court.view().is_cleared_for(
            did,
            str(policy_id).strip(),
            str(category).strip(),
            str(recipient).strip(),
            str(asset).strip(),
            str(amount).strip(),
            str(calldata_hash).strip(),
        )
        if not is_cleared:
            raise gl.vm.UserError("clearance does not match this action")

        # 3. Record execution state
        caller = gl.message.sender_address.as_hex.lower()
        exec_record = {
            "schema_version": "2",
            "decision_id": did,
            "recipient": str(recipient).strip().lower(),
            "asset": str(asset).strip(),
            "amount": str(amount).strip(),
            "calldata_hash": str(calldata_hash).strip().lower(),
            "caller": caller,
        }
        self.executions[did] = json.dumps(exec_record, sort_keys=True, separators=(",", ":"))
        return did
```
