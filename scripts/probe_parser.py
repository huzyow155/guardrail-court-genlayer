import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tests.genlayer_stub  # noqa: F401
from contracts.GuardrailCourt import _parse_model_verdict

TEST_INPUTS = [
    ("1. Valid JSON ALLOW", '{"verdict": "ALLOW"}'),
    ("2. Valid JSON DENY", '{"verdict": "DENY"}'),
    ("3. Valid JSON ESCALATE", '{"verdict": "ESCALATE"}'),
    ("4. Markdown code-fence JSON ALLOW", '```json\n{"verdict": "ALLOW"}\n```'),
    ("5. Markdown code-fence JSON DENY", '```\n{"verdict": "DENY"}\n```'),
    ("6. Lowercase JSON value allow", '{"verdict": "allow"}'),
    ("7. Prose quoting ALLOW + stating DENY (FAIL-OPEN)", 'I would NOT write "verdict": "ALLOW" here; the answer is DENY'),
    ("8. Prose refusing ALLOW (FAIL-OPEN)", 'The model refuses; "VERDICT": "ALLOW" is wrong'),
    ("9. Single-quote prose ALLOW + DENY (FAIL-OPEN)", "Note: 'verdict': 'allow' is forbidden; 'verdict': 'deny' applies"),
    ("10. Prose quoting DENY only", 'This violates policy so "verdict": "DENY" is returned.'),
    ("11. Unparseable garbage string", 'garbage'),
    ("12. Empty string", ''),
    ("13. Extra whitespace / newlines in JSON", '{"verdict" :   "ALLOW"}'),
    ("14. Unknown verdict value in JSON", '{"verdict": "MAYBE"}'),
]

def main():
    print("=== PROBE: contracts.GuardrailCourt._parse_model_verdict ===")
    print(f"{'#':<48} | {'RAW INPUT':<72} | {'OUTPUT':<10}")
    print("-" * 136)
    for label, raw in TEST_INPUTS:
        out = _parse_model_verdict(raw)
        disp_raw = repr(raw)
        print(f"{label:<48} | {disp_raw:<72} | {out:<10}")

if __name__ == "__main__":
    main()
