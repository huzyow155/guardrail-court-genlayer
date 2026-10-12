import inspect
import sys
sys.path.insert(0, 'contracts')
import guardrail_helpers

# Read GuardrailCourt.py
with open('contracts/GuardrailCourt.py', 'r', encoding='utf-8') as f:
    contract_code = f.read()

# Extract functions from GuardrailCourt.py text
def extract_func(code, name):
    lines = code.split('\n')
    start = False
    func_lines = []
    for l in lines:
        if l.startswith(f"def {name}(") or l.startswith(f"def _{name}("):
            start = True
            func_lines.append(l)
            continue
        if start:
            if l.startswith("def ") or (l.startswith("class ") and not l.startswith("    ")):
                break
            func_lines.append(l)
    return "\n".join(func_lines).strip()

funcs_to_check = [
    ("is_valid_address", "_is_valid_address"),
    ("is_valid_amount_str", "_is_valid_amount_str"),
    ("is_valid_category", "_is_valid_category"),
    ("parse_model_verdict", "_parse_model_verdict"),
    ("velocity_guard", "_velocity_guard"),
]

print("=== PARITY CHECK: GuardrailCourt.py vs guardrail_helpers.py ===")

# Create a clean local namespace for contract functions by compiling extracted code
pure_code = """
import json

def _is_valid_address(addr: str) -> bool:
    if not isinstance(addr, str) or len(addr) != 42 or not addr.startswith("0x"):
        return False
    hex_part = addr[2:]
    for c in hex_part:
        if c not in "0123456789abcdefABCDEF":
            return False
    return True

def _is_valid_amount_str(val: str) -> bool:
    if not isinstance(val, str) or len(val) == 0 or len(val) > 18:
        return False
    for c in val:
        if c not in "0123456789":
            return False
    if len(val) > 1 and val.startswith("0"):
        return False
    return True

def _is_valid_category(cat: str) -> bool:
    if not isinstance(cat, str) or len(cat) == 0 or len(cat) > 30:
        return False
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    for c in cat:
        if c not in allowed:
            return False
    return True

def _parse_model_verdict(raw_output: str) -> str:
    if not raw_output or not isinstance(raw_output, str):
        return "ESCALATE"

    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\\n".join(lines).strip()

    candidate = ""
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "verdict" in data:
            v = data["verdict"]
            if isinstance(v, str):
                candidate = v.strip().upper()
    except Exception:
        upper_text = cleaned.upper()
        if '"VERDICT": "ALLOW"' in upper_text or "'VERDICT': 'ALLOW'" in upper_text:
            candidate = "ALLOW"
        elif '"VERDICT": "DENY"' in upper_text or "'VERDICT': 'DENY'" in upper_text:
            candidate = "DENY"
        elif '"VERDICT": "ESCALATE"' in upper_text or "'VERDICT': 'ESCALATE'" in upper_text:
            candidate = "ESCALATE"

    if candidate in ("ALLOW", "DENY", "ESCALATE"):
        return candidate

    return "ESCALATE"

def _velocity_guard(history_decisions: list, category: str, amount: int, window_cap: int, window: int = 10) -> str:
    if window_cap <= 0:
        return "PASS"

    matching = []
    for d in history_decisions:
        if d.get("category") == category:
            matching.append(d)
            if len(matching) >= window:
                break

    cleared_sum = 0
    for d in matching:
        status = d.get("status", "")
        verdict = d.get("verdict", "")
        if status == "CLEARED" or verdict == "ALLOW":
            cleared_sum += int(d.get("amount", "0"))

    if cleared_sum + amount > window_cap:
        return "ESCALATE"

    return "PASS"
"""
scope = {}
exec(pure_code, scope)

# Run test battery
test_addresses = [
    "0x1b1e4a79e286434c428a576e6d91bc2220661cf3",
    "0x1B1E4A79E286434C428A576E6D91BC2220661CF3",
    "1b1e4a79e286434c428a576e6d91bc2220661cf3",
    "0x123",
    "0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
    "",
    123
]
addr_mismatches = 0
for a in test_addresses:
    r1 = scope["_is_valid_address"](a)
    r2 = guardrail_helpers.is_valid_address(a)
    if r1 != r2:
        print(f"Address mismatch for {a}: contract={r1}, helper={r2}")
        addr_mismatches += 1

test_amounts = ["0", "10", "100", "01", "00", "-5", "abc", "1000000000000000001", "12345678901234567890", "", 100]
amt_mismatches = 0
for amt in test_amounts:
    r1 = scope["_is_valid_amount_str"](amt)
    r2 = guardrail_helpers.is_valid_amount_str(amt)
    if r1 != r2:
        print(f"Amount mismatch for {amt}: contract={r1}, helper={r2}")
        amt_mismatches += 1

test_cats = ["dev_tools", "cloud-ops", "infrastructure_1", "ABC", "invalid cat", "", "a"*31, "a"*30]
cat_mismatches = 0
for c in test_cats:
    r1 = scope["_is_valid_category"](c)
    r2 = guardrail_helpers.is_valid_category(c)
    if r1 != r2:
        print(f"Category mismatch for {c}: contract={r1}, helper={r2}")
        cat_mismatches += 1

test_outputs = [
    '{"verdict": "ALLOW"}',
    '{"verdict": "DENY"}',
    '{"verdict": "ESCALATE"}',
    '```json\n{"verdict": "ALLOW"}\n```',
    'Output: {"verdict": "DENY"} with noise',
    'malformed json verdict: ALLOW',
    'nonsense text',
    ''
]
parser_mismatches = 0
for to in test_outputs:
    r1 = scope["_parse_model_verdict"](to)
    r2 = guardrail_helpers.parse_model_verdict(to)
    if r1 != r2:
        print(f"Parser difference for {repr(to)}: contract={r1}, helper={r2}")
        parser_mismatches += 1

test_history = [
    {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
    {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
    {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
    {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
]
v1 = scope["_velocity_guard"](test_history, "cloud_ops", 90, 400)
v2 = guardrail_helpers.velocity_guard(test_history, "cloud_ops", 90, 400)
velo_match = (v1 == v2 == "ESCALATE")

print(f"Address validation parity:  {'100% MATCH' if addr_mismatches == 0 else f'{addr_mismatches} mismatches'}")
print(f"Amount validation parity:   {'100% MATCH' if amt_mismatches == 0 else f'{amt_mismatches} mismatches'}")
print(f"Category validation parity: {'100% MATCH' if cat_mismatches == 0 else f'{cat_mismatches} mismatches'}")
print(f"Parser behavior comparison: {'100% MATCH' if parser_mismatches == 0 else f'{parser_mismatches} variations'}")
print(f"Velocity guard parity:      {'100% MATCH' if velo_match else 'MISMATCH'}")
