# User Error Specification

This document catalogues every user-facing error condition raised by **Guardrail Court** as a `gl.vm.UserError`.

## Policy Creation Errors
- `"agent must be a valid address"`: Raised if the `agent` parameter is not a 42-character string starting with `0x` containing valid hexadecimal characters.
- `"policy text length must be between 30 and 1200 characters"`: Raised if `text` is shorter than 30 characters or longer than 1200 characters.
- `"max_amount must be a valid non-negative integer string"`: Raised if `max_amount` contains non-digit characters, is empty, has leading zeros, or exceeds 18 digits.
- `"window_cap must be a valid non-negative integer string"`: Raised if `window_cap` contains non-digit characters, is empty, has leading zeros, or exceeds 18 digits.

## Policy Management Errors
- `"policy not found"`: Raised when accessing or operating on a policy ID that does not exist in storage.
- `"only the policy owner may pause or unpause"`: Raised if a caller other than the registered policy owner attempts to call `set_paused`.
- `"policy is paused"`: Raised when an agent calls `request_action` against a policy currently paused by its owner.
- `"only the registered agent may request actions"`: Raised if an account other than the policy's assigned `agent` calls `request_action`.

## Action Request Errors
- `"invalid category format"`: Raised if the category string does not match `^[a-z0-9_-]{1,30}$`.
- `"amount must be a valid non-negative integer string"`: Raised if `amount` is invalid, negative, decimal, or over 18 digits.
- `"description length must be between 5 and 600 characters"`: Raised if the action description is shorter than 5 or longer than 600 characters.

## Escalation Resolution Errors
- `"decision not found"`: Raised if `resolve_escalation` is called on a non-existent decision ID.
- `"only the policy owner may resolve escalations"`: Raised if anyone other than the policy owner attempts to resolve a pending action.
- `"decision is not pending owner resolution"`: Raised if the decision is in `CLEARED` or `DENIED` status.
- `"decision has already been resolved"`: Raised if `resolve_escalation` is called a second time on an already resolved decision.
- `"outcome must be ALLOW or DENY"`: Raised if the owner supplies an outcome string other than `ALLOW` or `DENY`.
