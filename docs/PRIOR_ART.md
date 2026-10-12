# Prior Art Analysis: Guardrail Court vs Existing Solutions

## Overview
Autonomous AI agents are increasingly entrusted with on-chain signing capabilities, API tokens, and autonomous execution privileges. However, agent systems that govern their own execution suffer from the principal-agent dilemma: the system deciding whether an action fits the owner's intent is often the same model or system executing or benefiting from that action.

This document identifies prior art across existing guardrail frameworks, deterministic policy engines, and smart contract spending limit modules, documents exact search queries and source references, and details the technical boundaries of **Guardrail Court**.

---

## Verified Search Queries & Results

Searches conducted across GitHub repositories and developer registries:
1. `gh search repos "agent policy genlayer"` -> 0 matching repositories found.
2. `gh search repos "agent guardrail genlayer"` -> 0 matching repositories found.
3. `gh search repos "genlayer"` -> Found official GenLayer protocol tools (`genlayer-studio`, `genlayer-cli`, `genlayer-js`, `genlayer-py`) and application prototypes (e.g., `proofworks-genlayer` bounty escrow, `genlayer-living-organism`). None implement an advisory agent guardrail court or multi-validator policy gate.
4. `gh search repos "guardrail"` -> Found off-chain LLM guardrail libraries (`NVIDIA-NeMo/Guardrails`, `guardrails-ai/guardrails`, `Portkey-AI/gateway`, `openai/openai-guardrails-python`).

Conclusion regarding GenLayer prior art: **We found no prior intelligent contract or community project implementing an agent guardrail gate or clearance court on GenLayer Studionet.**

---

## Detailed Examination of Closest External Solutions

### 1. NVIDIA NeMo Guardrails
- **Official Documentation**: [https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/overview](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/overview) (HTTP 200: *About NeMo Guardrails Library | Overview*)
- **Source Repository**: [https://github.com/NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) (HTTP 200: *NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems.*)
- **What Official Documentation Describes**:
  - NeMo Guardrails provides programmable rails using Colang and Python to control LLM outputs, including topical guidance, safety moderation, and LLM self-checking rails.
  - Rails execute within application middleware or Python services to validate conversational context and model inputs/outputs.
- **Architectural Differences in Guardrail Court**:
  - NeMo Guardrails operates within the application server or middleware stack of the agent host.
  - Guardrail Court operates as a smart contract on GenLayer Studionet, where policy verdicts are evaluated via multi-validator equivalence consensus (`gl.eq_principle.strict_eq`) and recorded into persistent on-chain state queryable by other smart contracts.

### 2. Open Policy Agent (OPA) / AWS Cedar
- **OPA Repository**: [https://github.com/open-policy-agent/opa](https://github.com/open-policy-agent/opa) (HTTP 200: *"Open Policy Agent (OPA) is an open source, general-purpose policy engine that enables unified, context-aware policy enforcement across the entire stack."*)
- **OPA Documentation**: [https://www.openpolicyagent.org/docs/latest/](https://www.openpolicyagent.org/docs/latest/) (HTTP 200: *"OPA decouples policy decision-making from policy enforcement."*)
- **Cedar Documentation**: [https://docs.cedarpolicy.com/](https://docs.cedarpolicy.com/) (HTTP 200: *"Cedar is a language for writing authorization policies and making authorization decisions based on those policies."*)
- **What Official Documentation Describes**:
  - OPA: *"OPA decouples policy decision-making from policy enforcement."* ([https://www.openpolicyagent.org/docs/latest/](https://www.openpolicyagent.org/docs/latest/))
  - Cedar: *"Cedar is a language for writing authorization policies and making authorization decisions based on those policies."* ([https://docs.cedarpolicy.com/](https://docs.cedarpolicy.com/))
- **Architectural Differences in Guardrail Court**:
  - OPA and Cedar evaluate structured attribute schemas through deterministic logic engines.
  - Guardrail Court interprets natural-language policy text (e.g. evaluating whether an action description is ambiguous or violates subjective business intent) alongside numeric boundary checks on-chain.

### 3. Safe Smart Account & Safe Allowance Modules
- **Safe Smart Account Repository**: [https://github.com/safe-fndn/safe-smart-account](https://github.com/safe-fndn/safe-smart-account) (HTTP 200: *Safe allows secure management of blockchain assets.*)
- **Safe Modules Repository**: [https://github.com/safe-fndn/safe-modules](https://github.com/safe-fndn/safe-modules) (HTTP 200: *"A collection of modules that can be used with the Safe contract"*)
- **Zodiac Protocol Repository**: [https://github.com/gnosisguild/zodiac](https://github.com/gnosisguild/zodiac) (HTTP 200: *"Zodiac is a collection of tools built according to an open standard."*)
- **What Official Documentation Describes**:
  - Safe allowance modules enforce per-token allowances and time-based spending limits on smart accounts through on-chain EVM checks.
- **Architectural Differences in Guardrail Court**:
  - Safe modules enforce deterministic token transfer caps and call authorizations on EVM chains.
  - Guardrail Court serves as an advisory gate that parses qualitative natural-language description before an action is cleared, recording verdicts on-chain for downstream contract consumption.

---

## External Systems Overview

### NVIDIA NeMo Guardrails
- **Source**: [https://github.com/NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)
- **Verified Quote**: *"NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."*
- **Role**: Middleware and runtime library for conversational AI guardrails.

### Open Policy Agent (OPA) & AWS Cedar
- **OPA Source**: [https://github.com/open-policy-agent/opa](https://github.com/open-policy-agent/opa)
- **OPA Documentation**: [https://www.openpolicyagent.org/docs/latest/](https://www.openpolicyagent.org/docs/latest/)
- **Cedar Documentation**: [https://docs.cedarpolicy.com/](https://docs.cedarpolicy.com/)
- **Verified Quotes**:
  - OPA: *"Open Policy Agent (OPA) is an open source, general-purpose policy engine that enables unified, context-aware policy enforcement across the entire stack."*
  - OPA: *"OPA decouples policy decision-making from policy enforcement."*
  - Cedar: *"Cedar is a language for writing authorization policies and making authorization decisions based on those policies."*
- **Role**: Declarative policy engines evaluating structured data against predefined authorization rules.

### Safe Smart Account & Safe Allowance Modules
- **Safe Modules Source**: [https://github.com/safe-fndn/safe-modules](https://github.com/safe-fndn/safe-modules)
- **Zodiac Protocol Source**: [https://github.com/gnosisguild/zodiac](https://github.com/gnosisguild/zodiac)
- **Verified Quotes**:
  - Safe Modules: *"A collection of modules that can be used with the Safe contract"*
  - Zodiac Protocol: *"Zodiac is a collection of tools built according to an open standard."*
- **Role**: Smart contract modules enforcing on-chain spending allowances and token transfer limits.

---

## What Guardrail Court Does

Guardrail Court operates independently as an intelligent contract on GenLayer Studionet with the following mechanics:
- **Natural-Language Policy Evaluation**: Evaluates proposed actions against natural-language policy text defined by human owners.
- **Multi-Validator Equivalence Consensus**: Runs validator consensus on an explicit 3-way verdict enum (`ALLOW`, `DENY`, or `ESCALATE`) via `gl.eq_principle.strict_eq`.
- **Pre-LLM Numeric Guards**: Executes zero-inference numeric checks (`HARD_LIMIT` against `max_amount`, and per-category `VELOCITY` sum against `window_cap`) before triggering validator LLMs.
- **Fail-Closed Escalation**: Unparseable responses or subjective ambiguity fail closed to `ESCALATE`, routing to the policy owner for manual resolution.
- **Public Decision Ledger**: Records decisions in contract state, exposing a synchronous view query `court.view().is_cleared(decision_id)` for downstream smart contracts.
- **Advisory Role**: Does not hold private keys, custody tokens, or execute financial transactions directly.

---

## Differentiation: What Is NOT New vs What We Found No Precedent For

### What Is NOT New
1. **Agent Guardrail Interception**: Using an intermediary gate to evaluate tool calls or proposed agent actions before dispatch is an established paradigm (demonstrated by [NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)).
2. **Deterministic Spending Caps**: Enforcing per-action amounts and periodic spending allowances is standard practice in smart contract security (demonstrated by [Safe Allowance Modules](https://github.com/safe-fndn/safe-modules)).
3. **Escalation / Human Approval**: Routing ambiguous or high-risk actions to human operators exists in enterprise incident and approval workflows (demonstrated by [PagerDuty](https://www.pagerduty.com/)).

### What We Found No Precedent For (Within Queried Scope)
*Search tools used: `gh search repos` and GitHub search API, executed on 2026-10-11 across queries `agent policy genlayer`, `agent guardrail genlayer`, and `genlayer`. Dựa trên các truy vấn GitHub đã nêu, thực hiện ngày 2026-10-11, không phải khẳng định không có dự án tương tự trên các nguồn khác.*
1. **Multi-Validator Equivalence Consensus on Natural Language Agent Policies**: Evaluating an autonomous agent's qualitative action description against natural-language policy guidelines using GenLayer validator consensus (`gl.eq_principle.strict_eq`), producing an on-chain verdict without external oracles.
2. **Hybrid Guard Architecture on GenVM**: Combining zero-inference deterministic pre-guards (`HARD_LIMIT` and per-category `VELOCITY` calculations) with fail-closed LLM equivalence consensus (`ALLOW`, `DENY`, or `ESCALATE`) in a single smart contract.
