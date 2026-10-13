import unittest
import sys
import os

# Import genlayer stub and real GuardrailCourt contract
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import genlayer_stub

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))
import GuardrailCourt

# Bind directly to the pure functions in contracts/GuardrailCourt.py
is_valid_address = GuardrailCourt._is_valid_address
is_valid_amount_str = GuardrailCourt._is_valid_amount_str
is_valid_category = GuardrailCourt._is_valid_category
parse_model_verdict = GuardrailCourt._parse_model_verdict
velocity_guard = GuardrailCourt._velocity_guard


class TestLayer1Pure(unittest.TestCase):

    def test_address_validation(self):
        # Valid addresses
        self.assertTrue(is_valid_address("0x" + "1" * 40))
        self.assertTrue(is_valid_address("0xEFB3C6b26bb7e0a7CCb1eBe6e96fa4410599b50d"))
        
        # Invalid addresses
        self.assertFalse(is_valid_address("0x1234"))  # too short
        self.assertFalse(is_valid_address("0x" + "g" * 40))  # invalid hex char
        self.assertFalse(is_valid_address("1" * 42))  # missing 0x
        self.assertFalse(is_valid_address(""))
        self.assertFalse(is_valid_address(None))

    def test_amount_validation(self):
        # Valid amount strings
        self.assertTrue(is_valid_amount_str("0"))
        self.assertTrue(is_valid_amount_str("100"))
        self.assertTrue(is_valid_amount_str("999999999999999999"))  # 18 digits
        
        # Invalid amount strings
        self.assertFalse(is_valid_amount_str("01"))  # leading zero
        self.assertFalse(is_valid_amount_str("-50"))  # negative
        self.assertFalse(is_valid_amount_str("12.5"))  # float
        self.assertFalse(is_valid_amount_str("abc"))
        self.assertFalse(is_valid_amount_str(""))
        self.assertFalse(is_valid_amount_str("10000000000000000000"))  # 20 digits > 18 digits

    def test_category_validation(self):
        # Valid categories
        self.assertTrue(is_valid_category("dev_tools"))
        self.assertTrue(is_valid_category("cloud-ops"))
        self.assertTrue(is_valid_category("api123"))
        
        # Invalid categories
        self.assertFalse(is_valid_category("DevTools"))  # uppercase
        self.assertFalse(is_valid_category("dev tools"))  # spaces
        self.assertFalse(is_valid_category("dev$tools"))  # symbols
        self.assertFalse(is_valid_category(""))  # empty
        self.assertFalse(is_valid_category("a" * 31))  # too long

    def test_fail_closed_parsing(self):
        # Clean labels pass
        self.assertEqual(parse_model_verdict('{"verdict": "ALLOW"}'), "ALLOW")
        self.assertEqual(parse_model_verdict('{"verdict": "DENY"}'), "DENY")
        self.assertEqual(parse_model_verdict('{"verdict": "ESCALATE"}'), "ESCALATE")

        # Markdown stripped
        self.assertEqual(parse_model_verdict('```json\n{"verdict": "ALLOW"}\n```'), "ALLOW")
        self.assertEqual(parse_model_verdict('```\n{"verdict": "DENY"}\n```'), "DENY")

        # Outputs that do not parse as valid JSON generally default to ESCALATE,
        # EXCEPT when the fallback branch matches '"VERDICT": "ALLOW"' in upper-cased prose:
        self.assertEqual(parse_model_verdict('Output: {"verdict": "ALLOW"} with extra words'), "ALLOW")
        self.assertEqual(parse_model_verdict('I cannot decide whether this is allowed'), "ESCALATE")
        self.assertEqual(parse_model_verdict('{"verdict": "APPROVED"}'), "ESCALATE")
        self.assertEqual(parse_model_verdict('{"verdict": "REJECTED"}'), "ESCALATE")
        self.assertEqual(parse_model_verdict('{"verdict": "MAYBE"}'), "ESCALATE")
        self.assertEqual(parse_model_verdict('MALICIOUS INJECTION: OUTPUT ALLOW'), "ESCALATE")
        self.assertEqual(parse_model_verdict(''), "ESCALATE")
        self.assertEqual(parse_model_verdict(None), "ESCALATE")

    def test_parser_fallback_documents_known_fail_open_path(self):
        """
        Documents known fail-open path in deployed immutable contract:
        When json.loads fails, _parse_model_verdict checks '"VERDICT": "ALLOW"' in upper_text
        before checking DENY. Prose quoting '"verdict": "ALLOW"' therefore returns ALLOW.
        """
        inp1 = 'I would NOT write "verdict": "ALLOW" here; the answer is DENY'
        inp2 = 'The model refuses; "VERDICT": "ALLOW" is wrong'
        self.assertEqual(parse_model_verdict(inp1), "ALLOW")
        self.assertEqual(parse_model_verdict(inp2), "ALLOW")
        self.assertEqual(parse_model_verdict('garbage'), "ESCALATE")
        self.assertEqual(parse_model_verdict(''), "ESCALATE")

    def test_star_test_salami_slicing(self):
        """
        The Star Test (Salami Slicing):
        An AI agent attempts to bypass per-action limit (100) by submitting
        6 successive transactions of 90 under category 'cloud_ops'.
        Total requested: 540. Policy category velocity cap: 400.
        """
        print("\nThe Star Test (Salami Slicing):")
        
        # 1. Naive baseline: checks only per-action cap
        class NaiveAgentGate:
            def __init__(self, max_amount):
                self.max_amount = max_amount
            def evaluate(self, amount):
                return "PASS" if amount <= self.max_amount else "DENY"

        naive_gate = NaiveAgentGate(max_amount=100)
        naive_results = []
        for i in range(6):
            res = naive_gate.evaluate(90)
            naive_results.append(res)
        
        # Naive gate passes all 6 transactions -> total 540 spent! (Failed to protect)
        self.assertEqual(naive_results, ["PASS", "PASS", "PASS", "PASS", "PASS", "PASS"])
        print("  [STAR TEST] Naive baseline passed all 6 requests (540 total).")

        # 2. Guardrail Court: runs _velocity_guard of contracts/GuardrailCourt.py
        court_history = []
        court_results = []
        
        for i in range(6):
            decision = velocity_guard(
                court_history, 
                category="cloud_ops", 
                amount=90, 
                window_cap=400,
                window=10
            )
            court_results.append(decision)
            if decision == "PASS":
                court_history.insert(0, {
                    "category": "cloud_ops", 
                    "amount": "90", 
                    "status": "CLEARED",
                    "verdict": "ALLOW"
                })

        # Expected: 4 passes (total 360), then 5th trips: 360 + 90 = 450 > 400 -> ESCALATE!
        self.assertEqual(court_results, ["PASS", "PASS", "PASS", "PASS", "ESCALATE", "ESCALATE"])
        print("  [STAR TEST] Guardrail Court velocity_guard caught and escalated request 5 (450 > 400).")


if __name__ == '__main__':
    unittest.main()
