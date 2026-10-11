# Architectural Design: Guardrail Court

## Overview
**Guardrail Court** is an advisory policy gate intelligent contract running on GenLayer Studionet (GenVM). It enables human owners to define natural-language policies alongside hard numeric spending parameters for autonomous AI agents, and provides multi-validator consensus to judge risky actions before execution.

---

## The Consensus Primitive

### What Validators Compare
The non-deterministic function provided to `gl.eq_principle.strict_eq(run_judge)` outputs **exactly one canonical string**:
- `"ALLOW"`
- `"DENY"`
- `"ESCALATE"`

Inside the non-deterministic block, each validator runs `gl.nondet.exec_prompt(prompt)`. The raw model output is stripped of markdown fences, parsed defensively as JSON for `verdict`, trimmed, and upper-cased. If the result exactly matches `"ALLOW"`, `"DENY"`, or `"ESCALATE"`, that label is returned.

### Fail-Closed Principle
Any unparseable string, malformed JSON, prompt-injection rambling, missing key, or unexpected output deterministically resolves to `"ESCALATE"`. In Guardrail Court, consensus never defaults to `ALLOW`.

### What Is Deliberately Excluded from Consensus
- **Free-Form Rationales**: Validators never compare natural-language explanations, chain-of-thought traces, or markdown justifications. Earlier Studionet deployments proved that LLM-extracted secondary fields diverge across diverse validator model architectures (Grok, Claude, Gemini, Qwen), which would break `strict_eq` consensus.
- **Timestamps and Dynamic External State**: All inputs into the prompt are precomputed and fetched from deterministic GenVM storage *before* entering the non-deterministic block. Storage access inside the non-deterministic function is strictly avoided.

---

## Two-Tier Evaluation Architecture

1. **Deterministic Guard Tier (Pre-LLM)**
   Executed entirely by deterministic Python code before any validator LLM call:
   - **`HARD_LIMIT`**: If `max_amount > 0` and `amount > max_amount`, the action is immediately rejected with verdict `DENY`, source `HARD_LIMIT`, and status `DENIED`. Zero LLM latency (~1s).
   - **`VELOCITY`**: Evaluates `velocity_guard(history, category, amount, window_cap, window=10)`. Sums all cleared amounts within the last 10 decisions in the same category. If `window_cap > 0` and `cleared_sum + amount > window_cap`, the action trips the velocity limit and is routed to verdict `ESCALATE`, source `VELOCITY`, and status `PENDING_OWNER`. Zero LLM latency (~1s).

2. **Multi-Validator Consensus Tier (`JUDGE`)**
   Actions that satisfy both numeric guards are evaluated by multi-validator LLM consensus against the owner's policy text and the last 8 decisions in the category. Validators converge on `ALLOW` (`CLEARED`), `DENY` (`DENIED`), or `ESCALATE` (`PENDING_OWNER`).

---

## State Model and Schema

All persistent state is stored in `TreeMap[str, str]` with sorted JSON keys, compact separators (`,`, `:`), and `"schema_version": "1"`.

### Data Tables
1. **`policies`**: `id -> { schema_version, id, owner, agent, text, policy_sha, max_amount, window_cap, paused, seq }`
2. **`decisions`**: `id -> { schema_version, id, policy_id, seq, category, amount, description, verdict, source, status, resolved_by_owner }`
3. **`by_owner`**: `owner_address_lower -> JSON list of policy IDs (newest first, max 50)`
4. **`by_agent`**: `agent_address_lower -> JSON list of policy IDs (newest first, max 50)`
5. **`by_policy`**: `policy_id -> JSON list of decision IDs (newest first, max 60)`
6. **`meta`**: `next_policy`, `next_decision` counters.

### Status Transitions
- `CLEARED`: Action allowed by model `JUDGE` or owner resolution. `is_cleared` returns `true`.
- `DENIED`: Action rejected by `HARD_LIMIT`, model `JUDGE`, or owner resolution. `is_cleared` returns `false`.
- `PENDING_OWNER`: Action tripped `VELOCITY` or model `JUDGE` returned `ESCALATE`. Halted until owner calls `resolve_escalation(decision_id, outcome)`. `is_cleared` returns `false` while pending.

---

## Discovery and Bounded Querying

To guarantee efficient frontend rendering and prevent denial-of-service through unbounded storage iteration, all query views enforce strict upper bounds:
- `list_policies_by_owner(owner, limit=10)` (max limit: 20)
- `list_policies_by_agent(agent, limit=10)` (max limit: 20)
- `list_decisions(policy_id, limit=10)` (max limit: 20)
- `pending_escalations(policy_id)` (returns pending actions up to 20)
- `latest_decision_id(policy_id)`
- `get_policy_stats(policy_id)` (summary of total decisions, cleared count, pending owner count, verdicts, and sources).
