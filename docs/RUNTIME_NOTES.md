# Runtime Probe Findings (Milestone 0)

## Overview
A dedicated probe contract (`Probe.py`, now in `archive/Probe.py`) was deployed and executed live on GenLayer Studionet (Chain ID 61999) to verify VM capabilities, consensus primitives, execution latency, and environment expectations prior to implementing the core contract.

- **Probe Contract Address**: `0xCafd1A568d5A55eb7E1135F0Fe31137114D5Fe42`
- **Deploy Transaction**: `0xef76f606fb197b9366042827e4c509fb44d126d71c86d7690fa8ebc2b5061368`
- **Consensus Transaction**: `0xcb6562321804ccc0e724a33e2ef6e6bd6549cc7e425f659884935556777eda6e`
- **Measured Consensus Latency**: `22.18s`

---

## Probe Verification Matrix

| Feature / Probe Addition | Expected Behavior | Studionet Preview Result | Notes / Details |
| :--- | :--- | :--- | :--- |
| **Sender Address Access** | `gl.message.sender_address.as_hex` | Verified | Returns standard `0x...` hex string. Consistent with address string. |
| **Address Casing** | Hex casing stability | Verified | Always lower-case addresses in contract storage (`addr.lower()`) to ensure case-insensitive matching across callers. |
| **Address Class Validation** | Global `Address` class | Available (`ADDR_1`) | `Address` class is defined in global scope; strict regex `^0x[0-9a-fA-F]{40}$` also verified for input validation. |
| **Equivalence Consensus** | `gl.eq_principle.strict_eq(fn)` | Verified (`strict_eq_passed: true`) | Strict equality on canonical strings produced consensus across validators with `MAJORITY_AGREE`. |
| **Prompt Execution** | `gl.nondet.exec_prompt(...)` | Returns string | Returned prompt string containing `"PONG"`. Defensive trimming and uppercase parsing functioned reliably. |
| **HTTP Web Fetch (200)** | `gl.nondet.web.get(raw_github_url)` | Verified (`GH_200`, length 2217) | Successfully fetched GitHub fixture file body bytes and decoded to UTF-8 string. |
| **HTTP Web Fetch (404)** | `gl.nondet.web.get(missing_url)` | Verified (`NF_404`) | Non-existent URL returned HTTP 404 cleanly without runtime crash. |
| **Stdlib inside Methods** | `urllib.parse`, `ipaddress`, `re`, `hashlib`, `json` | Verified | All imported and executed successfully inside contract methods. |
| **View Return Types: `bool`** | `@gl.public.view def f() -> bool:` | Verified (`true boolean`) | Views can return native boolean types directly to JavaScript SDK callers. |
| **View Return Types: `list[str]`** | `@gl.public.view def f() -> list[str]:` | Verified (`['alpha', 'beta']`) | Views can return lists of strings directly to JavaScript SDK callers. |
| **Zero-Balance Multiple Wallets** | Owner & Agent separate accounts | Verified | Both owner and agent throwaway wallets operate without funding (gas price 0 on Studionet). |
| **UserError Class** | `gl.vm.UserError("...")` | Verified | Standard exception class raised for input or state violations. |

---

## Implications for Guardrail Court Implementation

1. **View Return Type for `is_cleared`**:
   The runtime probe confirmed that view methods returning `bool` serialize and return native JavaScript boolean values (`true` / `false`) cleanly. `is_cleared(decision_id) -> bool` can return a native `bool`.
2. **Consensus String & Parser Fallback**:
   Validators compute a single canonical string (`ALLOW`, `DENY`, or `ESCALATE`) in the non-deterministic block. The model output is stripped of markdown fences and parsed as JSON. Outputs that do not parse as valid JSON generally yield `ESCALATE`; **HOWEVER**, the fallback branch matches the substring `"VERDICT": "ALLOW"` (or `'VERDICT': 'ALLOW'`) in upper-cased prose and returns `ALLOW` (see `test_parser_fallback_documents_known_fail_open_path` and `docs/LIMITATIONS.md` #1). The deployed contract is immutable.
3. **Storage Handling**:
   Addresses will be normalized to lower-case hex before indexing in `by_owner` and `by_agent` `TreeMap[str, str]`.
4. **Guard Short-Circuiting**:
   `HARD_LIMIT` and `VELOCITY` calculations run deterministically before calling `gl.eq_principle.strict_eq`. When a rule trips, the decision is recorded without an LLM call (measured Studionet latency in `live_evidence.json`: **5.261s** and **5.305s**, n=2; owner resolve: **8.472s**, n=1; JUDGE consensus: **11.934s to 32.026s**, arithmetic mean **19.02s**, n=8; 3s polling interval introduces up to +/-3s quantization).
