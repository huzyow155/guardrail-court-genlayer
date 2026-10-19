import sys
import types

# Minimal stub to import archive/v1/GuardrailCourt.py directly
genlayer_mod = types.ModuleType("genlayer")
class MockGL:
    Contract = type("Contract", (), {})
    vm = type("vm", (), {"UserError": Exception})
    public = type("public", (), {"write": lambda f: f, "view": lambda f: f})
    nondet = type("nondet", (), {"exec_prompt": lambda p: ""})
    eq_principle = type("eq_principle", (), {"strict_eq": lambda f: f()})
    message = type("message", (), {"sender_address": type("sender_address", (), {"as_hex": "0x0"})})
genlayer_mod.gl = MockGL
genlayer_mod.TreeMap = type("TreeMap", (), {"__class_getitem__": lambda cls, it: cls})
genlayer_mod.Address = str
sys.modules["genlayer"] = genlayer_mod

sys.path.insert(0, "archive/v1")
import GuardrailCourt

test_cases = [
    ("Empty string", ""),
    ("Corrupted text", "I am unsure about this purchase..."),
    ("Malformed JSON", '{"verdict": incomplete'),
    ("Missing verdict key", '{"action": "ALLOW", "amount": 50}'),
    ("Unrecognized verdict", '{"verdict": "MAYBE"}'),
    ("Markdown block invalid", "```json\n{'decision': 'ALLOW'}\n```"),
    ("Valid JSON ALLOW", '{"verdict": "ALLOW"}'),
    ("Valid JSON DENY", '{"verdict": "DENY"}'),
    ("Valid JSON ESCALATE", '{"verdict": "ESCALATE"}'),
]

print("=== REAL CONTRACT PARSER BEHAVIOR TEST (_parse_model_verdict) ===")
for label, tc in test_cases:
    res = GuardrailCourt._parse_model_verdict(tc)
    # Determine final state based on lines 302-308:
    if res == "ALLOW":
        status = "CLEARED"
    elif res == "DENY":
        status = "DENIED"
    else:
        status = "PENDING_OWNER (ESCALATE)"
    print(f"{label:<25} | Input: {repr(tc):<40} -> Verdict: {res:<8} -> State: {status}")
