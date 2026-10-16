# User Error Specification

This document catalogues every user-facing error condition raised by **Guardrail Court** as a `gl.vm.UserError`.

---

## Guardrail Court V2 Error Specification (Current)

### Policy Creation Errors (`create_policy`)
- `"agent must be a valid address"`: Raised if the `agent` parameter is not a 42-character string starting with `0x` containing valid hexadecimal characters.
- `"policy text length must be between 30 and 1200 characters"`: Raised if `text` is shorter than 30 characters or longer than 1200 characters.
- `"max_amount must be a valid non-negative integer string"`: Raised if `max_amount` contains non-digit characters, is empty, has leading zeros, or exceeds 18 digits.
- `"max_amount must be >= 1"`: Raised if `max_amount` evaluates to 0.
- `"window_cap must be a valid non-negative integer string"`: Raised if `window_cap` contains non-digit characters, is empty, has leading zeros, or exceeds 18 digits.
- `"window_cap must be >= max_amount"`: Raised if `window_cap` is strictly less than `max_amount`.
- `"allowed_recipients must contain between 1 and 10 items"`: Raised if `allowed_recipients` JSON array has 0 or >10 items, or contains duplicates.
- `"invalid address in allowed_recipients"`: Raised if an item in `allowed_recipients` is not a valid 42-character hex address.
- `"allowed_assets must contain between 1 and 10 items"`: Raised if `allowed_assets` JSON array has 0 or >10 items, or contains duplicates.
- `"invalid asset in allowed_assets"`: Raised if an asset symbol in `allowed_assets` does not match `^[A-Za-z0-9_-]{2,10}$`.

### Policy Management Errors (`set_paused`, `get_policy`, `get_policy_stats`)
- `"policy not found"`: Raised when accessing or operating on a policy ID that does not exist in storage.
- `"only the policy owner may pause or unpause"`: Raised if a caller other than the registered policy owner attempts to call `set_paused`.
- `"policy is paused"`: Raised when an agent calls `request_action` against a policy currently paused by its owner.
- `"only the registered agent may request actions"`: Raised if an account other than the policy's assigned `agent` calls `request_action`.

### Action Request Errors (`request_action`)
- `"invalid category format"`: Raised if the category string does not match `^[a-z0-9_-]{1,30}$`.
- `"recipient must be a valid address"`: Raised if `recipient` is not a 42-character string starting with `0x` containing valid hexadecimal characters.
- `"invalid asset format"`: Raised if `asset` does not match `^[A-Za-z0-9_-]{2,10}$`.
- `"amount must be a valid non-negative integer string"`: Raised if `amount` is invalid, negative, decimal, contains non-digits, has leading zeros, or exceeds 18 digits.
- `"amount must be >= 1"`: Raised if `amount` evaluates to 0.
- `"calldata_hash must be a 64-character hex string"`: Raised if `calldata_hash` is not a 64-character lowercase hex string (`0x` prefix is prohibited).
- `"justification length must be between 5 and 600 characters without control chars"`: Raised if `justification` length is outside [5, 600] or contains any control character (`ord < 32`), including newline and tab, or `0x7F`.
- `"too many pending escalations"`: Raised when a policy already has >= 10 unresolved pending escalations in queue.

### Escalation Resolution Errors (`resolve_escalation`)
- `"decision not found"`: Raised if `resolve_escalation` is called on a non-existent decision ID.
- `"only the policy owner may resolve escalations"`: Raised if anyone other than the policy owner attempts to resolve a pending action.
- `"decision is not pending owner resolution"`: Raised if the decision is in `CLEARED` or `DENIED` status.
- `"decision has already been resolved"`: Raised if `resolve_escalation` is called a second time on an already resolved decision.
- `"outcome must be ALLOW or DENY"`: Raised if the owner supplies an outcome string other than `ALLOW` or `DENY`.

### Consumer Guard Errors (`GuardedVaultV2`)
- `"decision has already been executed"`: Raised if `execute_action` is called with a `decision_id` that was already executed by the vault.
- `"clearance does not match this action"`: Raised if `court.view().is_cleared_for(...)` returns `False` due to invalid decision, uncleared status, or mismatch in policy_id, category, recipient, asset, amount, or calldata_hash.
- `"execution not found"`: Raised if querying execution history for an unexecuted `decision_id`.

### Parser Fail-Closed Rules and Boundaries (`_parse_verdict`)
- **2000-character parser cap**: If `len(raw_output) > 2000`, the parser immediately defaults to `"ESCALATE"` to reject oversized or noise payloads.
- **3-token contradiction rule**: If the raw output contains 2 or more distinct tokens from the set `{"allow", "deny", "escalate"}` (case-insensitive), it immediately fails closed to `"ESCALATE"`.
- **Calldata Limitation**: `calldata_hash` is a string supplied by the caller; the contract binds it into `action_hash` but cannot verify it equals the hash of any real calldata, and the validators do not decode calldata. The consumer must hash the calldata it will actually execute and pass that same value.

---

## Guardrail Court V1 Error Specification (Historical / Superseded)

### Policy Creation Errors
- `"agent must be a valid address"`
- `"policy text length must be between 30 and 1200 characters"`
- `"max_amount must be a valid non-negative integer string"`
- `"window_cap must be a valid non-negative integer string"`

### Policy Management Errors
- `"policy not found"`
- `"only the policy owner may pause or unpause"`
- `"policy is paused"`
- `"only the registered agent may request actions"`

### Action Request Errors
- `"invalid category format"`
- `"amount must be a valid non-negative integer string"`
- `"description length must be between 5 and 600 characters"`

### Escalation Resolution Errors
- `"decision not found"`
- `"only the policy owner may resolve escalations"`
- `"decision is not pending owner resolution"`
- `"decision has already been resolved"`
- `"outcome must be ALLOW or DENY"`
