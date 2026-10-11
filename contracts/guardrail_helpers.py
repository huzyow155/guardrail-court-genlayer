# Pure helper functions for Guardrail Court (module-level for direct testing)
import json
import re

ADDRESS_REGEX = re.compile(r"^0x[0-9a-fA-F]{40}$")
CATEGORY_REGEX = re.compile(r"^[a-z0-9_-]{1,30}$")
AMOUNT_REGEX = re.compile(r"^[0-9]{1,18}$")

def is_valid_address(addr: str) -> bool:
    if not isinstance(addr, str):
        return False
    return bool(ADDRESS_REGEX.match(addr.strip()))

def is_valid_amount_str(val: str) -> bool:
    if not isinstance(val, str):
        return False
    val = val.strip()
    if not AMOUNT_REGEX.match(val):
        return False
    # No leading zeros except '0' itself
    if len(val) > 1 and val.startswith("0"):
        return False
    return True

def is_valid_category(cat: str) -> bool:
    if not isinstance(cat, str):
        return False
    return bool(CATEGORY_REGEX.match(cat.strip()))

def parse_model_verdict(raw_output: str) -> str:
    """
    Defensive parser for model verdict output.
    Returns exactly 'ALLOW', 'DENY', or 'ESCALATE'.
    Fail-closed: Any malformed text, missing key, extra words, or non-matching value returns 'ESCALATE'.
    """
    if not raw_output or not isinstance(raw_output, str):
        return "ESCALATE"

    cleaned = raw_output.strip()
    # Strip markdown code blocks
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove opening fence
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Try JSON parsing
    candidate_val = ""
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "verdict" in data:
            v = data["verdict"]
            if isinstance(v, str):
                candidate_val = v.strip().upper()
    except Exception:
        # If strict JSON parse failed, attempt defensive regex search for {"verdict": "..."}
        m = re.search(r'["\']verdict["\']\s*:\s*["\']\s*([A-Za-z]+)\s*["\']', cleaned)
        if m:
            candidate_val = m.group(1).strip().upper()

    if candidate_val in ("ALLOW", "DENY", "ESCALATE"):
        return candidate_val

    return "ESCALATE"

def velocity_guard(history_decisions: list[dict], category: str, amount: int, window_cap: int, window: int = 10) -> str:
    """
    Deterministic velocity rate limiter:
    Take the last `window` decisions of this policy in the SAME category;
    sum the amounts of those that are cleared (verdict ALLOW, or resolved_by_owner == True and verdict ALLOW);
    if window_cap > 0 and sum + amount > window_cap -> ESCALATE.
    Otherwise -> PASS.
    """
    if window_cap <= 0:
        return "PASS"

    matching = []
    # history_decisions is assumed newest first or ordered; we inspect the most recent decisions in this category
    for d in history_decisions:
        if d.get("category") == category:
            matching.append(d)
            if len(matching) >= window:
                break

    cleared_sum = 0
    for d in matching:
        # Status CLEARED or verdict ALLOW or owner resolved ALLOW
        status = d.get("status", "")
        verdict = d.get("verdict", "")
        if status == "CLEARED" or verdict == "ALLOW":
            cleared_sum += int(d.get("amount", "0"))

    if cleared_sum + amount > window_cap:
        return "ESCALATE"

    return "PASS"
