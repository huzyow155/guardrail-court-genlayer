# Known Limitations and Threat Model: Guardrail Court

## Scope and Advisory Posture
1. **Advisory Gate Architecture**:
   - Guardrail Court is strictly an advisory policy evaluation contract. It does not custody tokens, hold private keys, or directly intercept raw JSON-RPC requests to an EVM network.
   - Downstream executors (vaults, paymasters, trading wrappers, Safe modules) are required to query `is_cleared(decision_id)` before releasing assets or triggering side effects. If an executor fails to verify clearance, Guardrail Court cannot prevent execution.

2. **Unreported Actions**:
   - The contract cannot govern or audit actions that an agent operator executes directly without calling `request_action`.
   - Security depends on the principle of least privilege at the infrastructure tier: the agent wallet should have zero native token balance or credentials, and only the executor contract (which checks `is_cleared`) holds discretionary privileges.

3. **Denomination and Unit Agnosticism**:
   - Amounts in Guardrail Court are non-negative integer values. The contract does not interpret currency denominations (e.g., USD vs EUR vs ETH vs wei).
   - Policy creators must establish a consistent unit convention across policy texts and numerical limits.

4. **Validator LLM Non-Determinism and Quorum Latency**:
   - Multi-validator LLM consensus requires approximately 12–25 seconds per consensus round.
   - While `HARD_LIMIT` and `VELOCITY` numeric guards short-circuit immediately (~5 seconds), applications requiring sub-second execution cannot rely on the multi-validator `JUDGE` path.

5. **Human-in-the-Loop Escalation Bottlenecks**:
   - Actions flagged as `ESCALATE` (due to ambiguity or velocity limit trips) remain in `PENDING_OWNER` status until the owner manually calls `resolve_escalation`.
   - If an owner is offline or unavailable, urgent agent operations that exceed velocity thresholds will remain paused until resolved.
