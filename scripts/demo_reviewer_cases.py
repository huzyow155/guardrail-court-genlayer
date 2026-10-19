import sys
import os
import types

# 1. Setup mock genlayer environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests")))
import genlayer_stub

# 2. Import archived V1 contract
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "archive", "v1")))
import GuardrailCourt as V1Court

# 3. Import active V2 contract
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "contracts")))
import GuardrailCourtV2 as V2Court

# Demonstration test cases highlighting the reviewer's exact reported flaws
CASES = [
    (
        "Prose refusing ALLOW (Reviewer Case)",
        'The model refuses; "VERDICT": "ALLOW" is wrong and violates policy.',
        "Reviewer reported: substring fallback matches '\"VERDICT\": \"ALLOW\"' in prose"
    ),
    (
        "Prose quoting ALLOW inside sentence",
        'In this scenario, I would output "verdict": "ALLOW" if valid, but it is not.',
        "Unparseable prose quoting ALLOW"
    ),
    (
        "Prose stating DENY but quoting ALLOW",
        'I would NOT write "verdict": "ALLOW" here; the answer is DENY',
        "Prose with conflicting token references"
    ),
    (
        "JSON ALLOW with trailing commentary",
        '{"verdict": "ALLOW"}\nNote: this was approved on exception basis.',
        "Valid JSON object corrupted by trailing prose"
    ),
    (
        "Two JSON objects back to back",
        '{"verdict": "ALLOW"}\n{"verdict": "DENY"}',
        "Multiple contradicting verdicts"
    ),
    (
        "Duplicate contradictory keys",
        '{"verdict": "DENY", "verdict": "ALLOW"}',
        "Duplicate key collision"
    ),
    (
        "Extra keys alongside verdict",
        '{"verdict": "ALLOW", "bypass": true}',
        "Extra unexpected schema keys"
    ),
    (
        "Clean exact ALLOW JSON",
        '{"verdict": "ALLOW"}',
        "Exact schema-valid ALLOW"
    ),
    (
        "Clean exact DENY JSON",
        '{"verdict": "DENY"}',
        "Exact schema-valid DENY"
    ),
    (
        "Clean exact ESCALATE JSON",
        '{"verdict": "ESCALATE"}',
        "Exact schema-valid ESCALATE"
    ),
]

def main():
    print("=" * 88)
    print("DEMONSTRATION: Guardrail Court V1 (Archived) vs Guardrail Court V2 (Active)")
    print("Reviewer Feedback: Malformed / ambiguous / prose quoting ALLOW must fail-closed")
    print("=" * 88)
    print(f"{'Case Description':<38} | {'V1 Result':<10} | {'V2 Result':<10} | {'Reviewer Fix':<15}")
    print("-" * 88)

    for desc, raw_output, note in CASES:
        v1_res = V1Court._parse_model_verdict(raw_output)
        v2_res = V2Court._parse_verdict(raw_output)

        if v1_res == "ALLOW" and v2_res == "ESCALATE":
            status = "FIXED (FAIL-CLOSED)"
        elif v1_res == v2_res:
            status = "PARITY"
        else:
            status = "DIFFERENT"

        print(f"{desc:<38} | {v1_res:<10} | {v2_res:<10} | {status:<15}")

    print("=" * 88)
    print("Key finding: In cases where V1 incorrectly accepted prose quoting ALLOW as ALLOW,")
    print("V2 strictly fails closed to ESCALATE, routing to human owner.")
    print("=" * 88)

if __name__ == "__main__":
    main()
