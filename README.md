# Guardrail Court

> Policy gate for autonomous AI agents on GenLayer Studionet.

## Status: Preview

## Problem
Autonomous agents with wallets, API keys, and discretion act faster than human operators can monitor. Today, the system determining whether an action complies with policy is typically the same agent runtime that benefits from executing it. When off-chain prompt guardrails are bypassed or compromised, unauthorized actions execute immediately without an independent verification layer.

## Mechanism
**Guardrail Court** is an advisory policy gate intelligent contract:
1. **Deterministic Guard**: Evaluates per-action spending limits (`max_amount`) and historical rolling window velocity (`velocity_guard`) using deterministic GenVM logic before calling any model.
2. **Validator Consensus**: For actions within limits, multi-validator consensus evaluates the action description and category against the owner's natural language policy.
3. **Canonical Consensus Primitive**: Validators reach consensus exclusively on a single canonical enum: `ALLOW`, `DENY`, or `ESCALATE`.
4. **Fail-Closed Escalation**: Any ambiguous decision or unparseable model response defaults to `ESCALATE`. The policy owner can review and resolve pending escalations through the contract inbox.

## Non-Goals
- **Execution & Custody**: The contract does not execute transactions, hold tokens, or custody assets.
- **Enforcement**: The contract is strictly advisory unless downstream executors verify `is_cleared(decision_id)`.
- **Unit Agnosticism**: The contract treats amounts as non-negative integer values; it does not interpret fiat or token denominations.
- **Unreported Actions**: It cannot detect or constrain actions that an agent fails to report.
- **Credential Replacement**: It is not a replacement for scoped API keys, least-privilege IAM, or rate limiters.

## Repository Structure
- `contracts/`: Intelligent contracts written in Python for GenVM.
- `scripts/`: Deployment, validation, and security scanner scripts.
- `fixtures/`: Test policies and benchmark test cases.
- `tests/`: Multi-layer test suite (Layer 1 pure logic, Layer 2 mocked GenVM, Layer 3 consensus simulation).
- `docs/`: In-depth documentation on architecture, verification, and integration.

## License
MIT (c) 2026 Hyper
