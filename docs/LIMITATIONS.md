# Current Limitations and Threat Model: Guardrail Court V2

This document describes the active limits, security boundaries, and operational assumptions of **Guardrail Court V2** (`contracts/GuardrailCourtV2.py`, deployed on Studionet at `0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b`).

For historical limitations of the superseded V1 contract (`contracts/GuardrailCourt.py`, `0x6C553Ba27a768D71b570a106D9D2e13553b4103c`), see [`archive/v1/LIMITATIONS_V1.md`](../archive/v1/LIMITATIONS_V1.md).

---

## 1. Calldata Hash Binding Limitation
- **Behavior**: `calldata_hash` is an agent-supplied 64-character hexadecimal SHA-256 string validated via `_is_valid_calldata_hash`.
- **Limitation**: The court validates format and binds `calldata_hash` immutably into `action_hash`, but it cannot verify whether the hash corresponds to actual calldata, nor do validator LLMs decode execution calldata.
- **Consumer Responsibility**: The downstream consumer (such as `GuardedVaultV2`) must compute the SHA-256 hash of its actual execution payload and assert that `court.is_cleared(decision_id, ...)` matches that exact hash.

---

## 2. Absence of Clearance Expiry (No On-Chain Clock)
- **Behavior**: GenVM contracts currently operate without a synchronized wall-clock timestamp primitive.
- **Limitation**: Clearances issued by Guardrail Court V2 do not expire automatically. A cleared decision remains valid indefinitely until it is either executed by a single-use consumer (e.g. `GuardedVaultV2.executed_decisions`) or rendered un-executable by the owner invoking `set_paused(policy_id, True)`.
- **Mitigation**: Policy owners must use emergency pause (`set_paused`) if an agent's keys or state become compromised. Downstream executors can also track action submission sequence or limit acceptable decision IDs.

---

## 3. Model Judgment Variability and Fail-Closed Escalation
- **Behavior**: The non-deterministic validator LLM step runs within GenVM multi-validator consensus using `gl.eq_principle.strict_eq`. All raw model outputs must conform to exact schema `{"verdict": "ALLOW"|"DENY"|"ESCALATE"}` parsed by `_parse_verdict`.
- **Limitation**: Natural language foundation model interpretations can vary across runs or prompt phrasing, especially when policies or agent justifications are ambiguous, repetitive, or near decision boundaries.
- **Fail-Closed Guarantee**: Any malformed, unparseable, dual-token contradictory, duplicate-key, or non-conforming model output strictly fails closed to `ESCALATE`. Ambiguous actions are never mistakenly cleared; they route safely to the human policy owner's escalation queue (`PENDING_OWNER`).

---

## 4. Conservative Model Escalation on Generic Justifications
- **Empirical Observation**: Live testing on GenLayer Studionet demonstrates that validator consensus adopts a conservative stance towards sparse, repetitive, or generic agent justifications.
- **Operational Reality**: For example, in live test runs, generic justification strings such as "server capacity scaling" resulted in validator escalation (`PENDING_OWNER`) rather than autonomous clearance. Autonomous agents should provide concrete, verifiable context (e.g. invoice IDs, specific service endpoints, or explicit scope references) to allow the validator model to verify policy compliance.

---

## 5. Consumer Authorization Scope
- **Behavior**: `GuardedVaultV2.execute(decision_id, recipient, asset, amount, calldata_hash)` performs strict 5-tuple action-binding verification against `GuardrailCourtV2.is_cleared(...)` and records `self.executed_decisions[decision_id] = True` to prevent double-spending.
- **Limitation**: `GuardedVaultV2` demonstrates cross-contract parameter-bound clearance verification, but does not restrict *who* can trigger `execute` once a valid clearance exists on-chain. Production vaults or paymasters must implement caller access control (e.g., restricting callers to authorized keepers, signers, or specific executor contracts).

---

## 6. Pending Escalation Queue Cap (`10`)
- **Behavior**: To protect human policy owners from inbox flooding attacks, `request_action` enforces a strict cap:
  ```python
  pending_count = sum(1 for item in history_items if item.get("status") == "PENDING_OWNER")
  if pending_count >= 10:
      raise gl.vm.UserError("too many pending escalations")
  ```
- **Operational Reality**: If an agent generates 10 pending escalations without the owner resolving them, subsequent action requests that would otherwise trigger `VELOCITY` or `JUDGE` revert until the owner resolves existing escalations via `resolve_escalation`.

---

## 7. Velocity Window Mechanics (Policy-Wide 30-Decision Window)
- **Behavior**: V2 velocity calculates the sum of `CLEARED` decisions within the 30 most recent decisions across the entire policy (`history_items[:30]`). If `cleared_sum + amount > window_cap`, the request routes to `VELOCITY` guard escalation (`status: PENDING_OWNER`).
- **Limitation**: Velocity tracks cumulative cleared amount over the most recent 30 recorded decisions rather than a calendar time duration (due to lack of on-chain timestamp). If more than 30 decisions intervene, older cleared amounts exit the summation window.
