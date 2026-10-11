# Prior Art Analysis: Guardrail Court vs Existing Solutions

## Overview
Autonomous AI agents are increasingly entrusted with on-chain credentials, API wallets, and autonomous discretionary powers. However, agent systems that govern their own execution suffer from the principal-agent dilemma: the system deciding whether an action fits the owner's intent is often the same model or system executing or benefiting from that action.

This document identifies prior art across existing policy engines, smart contract guardrails, and decentralized architectures, and articulates the specific technical differences of **Guardrail Court**.

---

## Closest Existing Solutions

1. **NeMo Guardrails / Llama Guard / Guardrails AI (Centralized Off-Chain Agent Rails)**
   - *Architecture*: Python libraries or sidecar proxies running LLM/Colang rails alongside an agent process.
   - *Mechanism*: Evaluates user input or tool calls against programmable rails locally before dispatching to external APIs.
   - *Limitation*: Run by the agent operator on local compute. Lack decentralized multi-party consensus, immutable public audit logs, and cross-contract smart contract readability. If an agent process or server is compromised, off-chain rails can be bypassed or disabled silently.

2. **Open Policy Agent (OPA) / AWS Cedar / Rego Engines (Deterministic Logic Gateways)**
   - *Architecture*: Declarative policy engines that evaluate structured JSON contexts against formal logic rules.
   - *Mechanism*: Purely deterministic boolean or attribute-based access control (ABAC).
   - *Limitation*: Cannot interpret open-ended natural language intent (e.g., "nothing that could look like pressuring a customer", "no gifts to individuals"). Require rigid domain-specific schemas and cannot handle semantic ambiguity or evolving natural language contexts.

3. **Gnosis Zodiac / Safe Spending Limits (EVM Smart Contract Modules)**
   - *Architecture*: On-chain smart contract modules attached to Safe multisigs that enforce periodic token allowances per address.
   - *Mechanism*: Deterministic on-chain math: `allowance_left >= transfer_amount`.
   - *Limitation*: Strictly numeric and asset-specific. Cannot evaluate qualitative intent, contextual descriptions, recipient relationship, or business purpose.

4. **GenLayer Prior Art (Dispute Adjudication / Text Analysis Contracts)**
   - *Architecture*: Prior GenLayer contracts (e.g., *MirrorJudge*, *ClauseLab*, *Citation Court*) demonstrated GenVM non-deterministic LLM consensus (`gl.vm.run_nondet` and `gl.eq_principle.strict_eq`) for two-party arbitration or pre-signing contract analysis.
   - *Limitation*: Those contracts focus on post-facto dispute resolution or document analysis rather than a real-time, low-latency, stateful policy gate with deterministic velocity rate-limiting and human-in-the-loop owner escalation.

---

## Comparison Table

| Dimension | NeMo / Guardrails AI | OPA / Cedar | Safe Spending Limits | **Guardrail Court (This Project)** |
| :--- | :--- | :--- | :--- | :--- |
| **Execution Environment** | Centralized server / local python runtime | Centralized service / sidecar | EVM Smart Contract (Safe module) | **GenLayer Studionet Intelligent Contract** |
| **Policy Language** | Natural language / Colang | DSL (Rego / Cedar) | Strict token & numeric parameters | **Natural Language + Hard Numeric Caps** |
| **Validator Consensus** | Single local LLM invocation (0 consensus) | Single evaluator (0 consensus) | Cryptographic signature validation | **Multi-Validator Equivalence Consensus (`strict_eq`)** |
| **Ambiguity Handling** | Fail open or local fallback | Binary match failure | Reject | **Explicit ESCALATE verdict -> Owner Inbox** |
| **Salami-Slicing Defense** | Requires external database | Requires external state | Rolling token allowance per token | **On-Chain Historical Window Velocity Guard (`velocity_guard`)** |
| **On-Chain Audit Log** | None (private server logs) | None | Transaction receipts on EVM | **Public, immutable decision ledger with queries** |
| **Cross-Contract Interoperability** | None | None | EVM contract calls | **Synchronous on-chain view query (`is_cleared`)** |
| **Execution Role** | Interceptor / wrapper | Policy decision point (PDP) | Direct asset transfer limiter | **Advisory Policy Gate (does not hold funds)** |

---

## Technical Distinctness of Guardrail Court

1. **Deterministic Guard Short-Circuiting**:
   Before invoking non-deterministic LLM consensus, deterministic Python routines inside GenVM evaluate hard limits (`HARD_LIMIT`) and rolling 10-decision category velocity (`VELOCITY`). This prevents costly LLM validator rounds when hard rules are broken.
2. **One Clean Consensus Primitive**:
   Validators run an equivalence check (`gl.eq_principle.strict_eq`) on a strictly validated, canonical enum output: `ALLOW`, `DENY`, or `ESCALATE`. Free-form rationales are never fed to consensus, guaranteeing high validator convergence.
3. **Fail-Closed Escalation Protocol**:
   Any unparseable, malformed, or injected model output defaults to `ESCALATE`. Ambiguous actions are halted until the owner manually calls `resolve_escalation`.
4. **Advisory Gate Architecture**:
   The contract is strictly advisory. It never custody funds, execute transactions, or impose gas penalties; downstream executors query `is_cleared(decision_id)` before taking risky actions.
