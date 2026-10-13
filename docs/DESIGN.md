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

### Fail-Closed Principle (and Known Fallback Exception)
Outputs that do not parse as valid JSON generally resolve to `"ESCALATE"`; **HOWEVER**, when `json.loads` fails, the fallback branch in `_parse_model_verdict` checks for the substring `"VERDICT": "ALLOW"` (or `'VERDICT': 'ALLOW'`) in the upper-cased string *before* checking `"VERDICT": "DENY"`. Consequently, prose containing that substring evaluates to `"ALLOW"` (see `test_parser_fallback_documents_known_fail_open_path` in `tests/test_layer1_pure.py` and `docs/LIMITATIONS.md` #1). The deployed contract on Studionet is immutable.

### What Is Deliberately Excluded from Consensus
- **Free-Form Rationales**: Validators never compare natural-language explanations, chain-of-thought traces, or secondary text fields. Multi-validator consensus on GenLayer requires exact string equivalence (`strict_eq`); comparing free-form text or non-deterministic secondary fields across distinct validator model instances causes divergence and consensus failure.
- **Timestamps and Dynamic External State**: All inputs into the prompt are precomputed and fetched from deterministic GenVM storage *before* entering the non-deterministic block. Storage access inside the non-deterministic function is strictly avoided.

---

## Two-Tier Evaluation Architecture

1. **Deterministic Guard Tier (Pre-LLM)**
   Executed entirely by deterministic Python code before any validator LLM call:
   - **`HARD_LIMIT`**: If `max_amount > 0` and `amount > max_amount`, the action is immediately rejected with verdict `DENY`, source `HARD_LIMIT`, and status `DENIED`. Measured Studionet latency: **5.261s** (n=1, 3s polling interval).
   - **`VELOCITY`**: `request_action` fetches `policy_history_ids[:15]` (the 15 most recent decisions of the entire policy across all categories), then `_velocity_guard(history_items, category, int_amount, win_cap, window=10)` filters for decisions matching `category`, takes up to 10 matching items, and sums `amount` where `status == "CLEARED"` or `verdict == "ALLOW"`. If `window_cap > 0` and `cleared_sum + amount > window_cap`, the action trips the velocity limit and is routed to verdict `ESCALATE`, source `VELOCITY`, and status `PENDING_OWNER`. There is no time-duration window. Measured Studionet latency: **5.305s** (n=1, 3s polling interval).

2. **Multi-Validator Consensus Tier (`JUDGE`)**
   Actions that satisfy both numeric guards are evaluated by multi-validator LLM consensus against the owner's policy text and `history_items[:8]` (the 8 most recent decisions of the entire policy across all categories, formatted with `category`, `amount`, and `verdict` only). Validators converge on `ALLOW` (`CLEARED`), `DENY` (`DENIED`), or `ESCALATE` (`PENDING_OWNER`). Measured Studionet latency: **11.934s to 32.026s** (arithmetic mean **19.02s**, n=8, 3s polling interval).

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
