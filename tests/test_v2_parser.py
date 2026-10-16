import unittest
import sys
import os
import random
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import genlayer_stub  # noqa: F401

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))
import GuardrailCourtV2

_parse_verdict = GuardrailCourtV2._parse_verdict


def _independent_oracle(raw_input: str) -> str:
    """
    Independent reference oracle for parser behavior.
    Strict fail-closed specification.
    """
    if not isinstance(raw_input, str) or not raw_input:
        return "ESCALATE"

    if len(raw_input) > 2000:
        return "ESCALATE"

    # Secondary contradiction check
    words = []
    curr = []
    for ch in raw_input.lower():
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            curr.append(ch)
        else:
            if curr:
                words.append("".join(curr))
                curr = []
    if curr:
        words.append("".join(curr))
    word_set = set(words)
    verdict_tokens = word_set.intersection({"allow", "deny", "escalate"})
    if len(verdict_tokens) >= 2:
        return "ESCALATE"

    text = raw_input.strip()
    if not text:
        return "ESCALATE"

    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
            inner = lines[1:-1]
            if any(l.strip().startswith("```") for l in inner):
                return "ESCALATE"
            text = "\n".join(inner).strip()
        else:
            return "ESCALATE"

    def no_dups(pairs):
        seen = set()
        out = {}
        for k, v in pairs:
            if k in seen:
                raise ValueError("dup")
            seen.add(k)
            out[k] = v
        return out

    try:
        parsed = json.loads(text, object_pairs_hook=no_dups)
    except Exception:
        return "ESCALATE"

    if not isinstance(parsed, dict) or len(parsed) != 1:
        return "ESCALATE"

    if "verdict" not in parsed:
        return "ESCALATE"

    val = parsed["verdict"]
    if val in ("ALLOW", "DENY", "ESCALATE"):
        return val

    return "ESCALATE"


class TestV2ParserTable(unittest.TestCase):
    TABLE_CASES = [
        # Original 14 probe inputs
        ("1. Valid JSON ALLOW", '{"verdict": "ALLOW"}', "ALLOW"),
        ("2. Valid JSON DENY", '{"verdict": "DENY"}', "DENY"),
        ("3. Valid JSON ESCALATE", '{"verdict": "ESCALATE"}', "ESCALATE"),
        ("4. Markdown code-fence JSON ALLOW", '```json\n{"verdict": "ALLOW"}\n```', "ALLOW"),
        ("5. Markdown code-fence JSON DENY", '```\n{"verdict": "DENY"}\n```', "DENY"),
        ("6. Lowercase JSON value allow", '{"verdict": "allow"}', "ESCALATE"),
        ("7. Prose quoting ALLOW + stating DENY", 'I would NOT write "verdict": "ALLOW" here; the answer is DENY', "ESCALATE"),
        ("8. Prose refusing ALLOW", 'The model refuses; "VERDICT": "ALLOW" is wrong', "ESCALATE"),
        ("9. Single-quote prose ALLOW + DENY", "Note: 'verdict': 'allow' is forbidden; 'verdict': 'deny' applies", "ESCALATE"),
        ("10. Prose quoting DENY only", 'This violates policy so "verdict": "DENY" is returned.', "ESCALATE"),
        ("11. Unparseable garbage string", "garbage", "ESCALATE"),
        ("12. Empty string", "", "ESCALATE"),
        ("13. Extra whitespace in JSON", '{"verdict" :   "ALLOW"}', "ALLOW"),
        ("14. Unknown verdict value in JSON", '{"verdict": "MAYBE"}', "ESCALATE"),
        
        # Extended cases: Cyrillic, duplicates, extra keys, formatting, injection
        ("15. Duplicate key contradictory", '{"verdict": "DENY", "verdict": "ALLOW"}', "ESCALATE"),
        ("16. Duplicate key identical", '{"verdict": "ALLOW", "verdict": "ALLOW"}', "ESCALATE"),
        ("17. Cyrillic lookalike A in ALLOW", '{"verdict": "\u0410LLOW"}', "ESCALATE"),
        ("18. Cyrillic lookalike O in ALLOW", '{"verdict": "ALL\u041eW"}', "ESCALATE"),
        ("19. Cyrillic lookalike E in DENY", '{"verdict": "D\u0415NY"}', "ESCALATE"),
        ("20. Extra key reason with ALLOW", '{"verdict": "ALLOW", "reason": "action looks fine"}', "ESCALATE"),
        ("21. Extra key meta with DENY", '{"verdict": "DENY", "meta": {"risk": "high"}}', "ESCALATE"),
        ("22. Trailing prose after markdown fence", '```json\n{"verdict": "ALLOW"}\n```\nApproved by agent', "ESCALATE"),
        ("23. Leading prose before markdown fence", 'Final output:\n```json\n{"verdict": "ALLOW"}\n```', "ESCALATE"),
        ("24. Multiple markdown fences", '```json\n{"verdict": "ALLOW"}\n```\n```json\n{"verdict": "DENY"}\n```', "ESCALATE"),
        ("25. Unclosed markdown fence", '```json\n{"verdict": "ALLOW"}', "ESCALATE"),
        ("26. Boolean verdict true", '{"verdict": true}', "ESCALATE"),
        ("27. Number verdict 1", '{"verdict": 1}', "ESCALATE"),
        ("28. Array verdict", '{"verdict": ["ALLOW"]}', "ESCALATE"),
        ("29. Null verdict", '{"verdict": null}', "ESCALATE"),
        ("30. Trailing comma in JSON", '{"verdict": "ALLOW",}', "ESCALATE"),
        ("31. Padded verdict string", '{"verdict": " ALLOW "}', "ESCALATE"),
        ("32. Title case Allow", '{"verdict": "Allow"}', "ESCALATE"),
        ("33. Title case Deny", '{"verdict": "Deny"}', "ESCALATE"),
        ("34. Empty object", '{}', "ESCALATE"),
        ("35. JSON list of object", '[{"verdict": "ALLOW"}]', "ESCALATE"),
        ("36. 1MB noise string", '{"verdict": "ALLOW"}' + ' ' * 1000000, "ESCALATE"),
        ("37. Raw text ALLOW only", 'ALLOW', "ESCALATE"),
        ("38. None input", None, "ESCALATE"),
        ("39. Escalate fence block", '```\n{"verdict": "ESCALATE"}\n```', "ESCALATE"),
        ("40. Multi-token contradiction in markdown", '```json\n{"verdict": "ALLOW", "note": "DENY"}\n```', "ESCALATE"),
    ]

    def test_table_inputs(self):
        for label, raw_input, expected in self.TABLE_CASES:
            with self.subTest(label=label):
                actual = _parse_verdict(raw_input)
                self.assertEqual(actual, expected, f"Failed on '{label}': expected {expected}, got {actual}")

    def test_table_matches_independent_oracle(self):
        for label, raw_input, _ in self.TABLE_CASES:
            with self.subTest(label=label):
                actual = _parse_verdict(raw_input)
                oracle_val = _independent_oracle(raw_input)
                self.assertEqual(actual, oracle_val, f"Mismatch with oracle on '{label}'")


class TestV2ParserFuzzer(unittest.TestCase):
    def test_fuzzer_5000_iterations(self):
        rng = random.Random(42)
        vocab = [
            '{"verdict": "ALLOW"}',
            '{"verdict": "DENY"}',
            '{"verdict": "ESCALATE"}',
            '{"verdict": "allow"}',
            '{"verdict": "deny"}',
            '{"verdict": 1}',
            '{"verdict": null}',
            '{"verdict": true}',
            '{"verdict": "ALLOW", "extra": "x"}',
            '{"verdict": "ALLOW", "verdict": "DENY"}',
            '```json\n{"verdict": "ALLOW"}\n```',
            '```\n{"verdict": "DENY"}\n```',
            '```json\n{"verdict": "ALLOW"}',
            'ALLOW', 'DENY', 'ESCALATE', 'maybe', 'override',
            '{', '}', ':', ',', '"', "'", '\\', '\n', '\t', ' ',
            '\u0410', '\u041e', '\u0000', '123', 'true', 'false',
        ]

        allowed_count = 0
        denied_count = 0
        escalated_count = 0

        for i in range(5000):
            # Generate various shapes of mutated input
            mode = rng.randint(0, 4)
            if mode == 0:
                # Random token concatenation
                k = rng.randint(1, 6)
                raw = "".join(rng.choice(vocab) for _ in range(k))
            elif mode == 1:
                # Mutation of valid JSON
                base = rng.choice(['{"verdict": "ALLOW"}', '{"verdict": "DENY"}', '{"verdict": "ESCALATE"}'])
                chars = list(base)
                num_mut = rng.randint(1, 3)
                for _ in range(num_mut):
                    pos = rng.randint(0, len(chars))
                    chars.insert(pos, rng.choice([" ", "\n", "x", "\"", ",", ":", "\u0410"]))
                raw = "".join(chars)
            elif mode == 2:
                # Fenced block mutations
                inner = rng.choice(vocab)
                raw = f"```{rng.choice(['', 'json', 'python'])}\n{inner}\n```"
                if rng.random() < 0.3:
                    raw += rng.choice(["\nextra", "trailing", ""])
            elif mode == 3:
                # Completely arbitrary random string
                length = rng.randint(0, 60)
                raw = "".join(chr(rng.randint(32, 126)) for _ in range(length))
            else:
                # Adversarial contradiction attempts
                raw = f'{{"verdict": "{rng.choice(["ALLOW", "DENY"])}", "reason": "{rng.choice(["ALLOW", "DENY", "ESCALATE", "safe"])}"}}'

            verdict = _parse_verdict(raw)
            oracle_verdict = _independent_oracle(raw)

            # Invariant 1: verdict must strictly be one of the 3 canonical strings
            self.assertIn(verdict, ("ALLOW", "DENY", "ESCALATE"))

            # Invariant 2: must match independent oracle
            self.assertEqual(verdict, oracle_verdict, f"Iteration {i} failed for input: {raw!r}")

            # Invariant 3: fail-closed safety check
            if verdict == "ALLOW":
                allowed_count += 1
                # Must be strictly parseable without any contradiction
                self.assertNotIn("deny", raw.lower())
                self.assertNotIn("escalate", raw.lower())
            elif verdict == "DENY":
                denied_count += 1
                self.assertNotIn("allow", raw.lower())
                self.assertNotIn("escalate", raw.lower())
            else:
                escalated_count += 1

        # Check distribution
        self.assertGreater(escalated_count, 4000)


if __name__ == "__main__":
    unittest.main()
