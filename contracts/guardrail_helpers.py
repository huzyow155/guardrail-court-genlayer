# Pure helper functions for Guardrail Court
# Byte-for-byte logic parity with contracts/GuardrailCourt.py lines 12-103
import json


def is_valid_address(addr: str) -> bool:
    if not isinstance(addr, str) or len(addr) != 42 or not addr.startswith("0x"):
        return False
    hex_part = addr[2:]
    for c in hex_part:
        if c not in "0123456789abcdefABCDEF":
            return False
    return True


def is_valid_amount_str(val: str) -> bool:
    if not isinstance(val, str) or len(val) == 0 or len(val) > 18:
        return False
    for c in val:
        if c not in "0123456789":
            return False
    if len(val) > 1 and val.startswith("0"):
        return False
    return True


def is_valid_category(cat: str) -> bool:
    if not isinstance(cat, str) or len(cat) == 0 or len(cat) > 30:
        return False
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    for c in cat:
        if c not in allowed:
            return False
    return True


def parse_model_verdict(raw_output: str) -> str:
    """
    Defensively extracts ALLOW, DENY, or ESCALATE.
    Defaults to ESCALATE on any deviation, noise, or invalid JSON.
    """
    if not raw_output or not isinstance(raw_output, str):
        return "ESCALATE"

    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

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


def velocity_guard(history_decisions: list, category: str, amount: int, window_cap: int, window: int = 10) -> str:
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


# Aliases matching contract's internal names
_is_valid_address = is_valid_address
_is_valid_amount_str = is_valid_amount_str
_is_valid_category = is_valid_category
_parse_model_verdict = parse_model_verdict
_velocity_guard = velocity_guard
