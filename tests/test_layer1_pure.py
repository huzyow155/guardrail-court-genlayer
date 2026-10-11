import unittest
import sys
import os

# Add contract path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))

from guardrail_helpers import (
    is_valid_address,
    is_valid_amount_str,
    is_valid_category,
    parse_model_verdict,
    velocity_guard,
)


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

        # Code fences stripped
        self.assertEqual(parse_model_verdict('```json\n{"verdict": "ALLOW"}\n```'), "ALLOW")
        self.assertEqual(parse_model_verdict('```\n{"verdict": "DENY"}\n```'), "DENY")

        # Fail closed for extra words, unparseable output, or injection attempts
        self.assertEqual(parse_model_verdict("ALLOW, but check with owner"), "ESCALATE")
        self.assertEqual(parse_model_verdict("allow it"), "ESCALATE")
        self.assertEqual(parse_model_verdict(""), "ESCALATE")
        self.assertEqual(parse_model_verdict(None), "ESCALATE")
        self.assertEqual(parse_model_verdict('{"reason": "good", "decision": "ALLOW"}'), "ESCALATE")
        self.assertEqual(parse_model_verdict('{"verdict": "APPROVED"}'), "ESCALATE")
        self.assertEqual(parse_model_verdict("Total nonsense output here"), "ESCALATE")

    def test_star_test_salami_slicing(self):
        """
        The Star Test (Salami Slicing):
        Per-action cap 100, rolling window cap 400.
        Agent sends six actions of amount 90 in one category ('cloud_ops').
        
        Naive Baseline (per-action judge only):
        - Action 1: 90 <= 100 -> ALLOW
        - Action 2: 90 <= 100 -> ALLOW
        - Action 3: 90 <= 100 -> ALLOW
        - Action 4: 90 <= 100 -> ALLOW
        - Action 5: 90 <= 100 -> ALLOW (FAILS to protect budget! Cumulative 450 > 400)
        - Action 6: 90 <= 100 -> ALLOW (Cumulative 540)
        
        Guardrail Court Mechanism (velocity_guard):
        - Action 1: cleared_sum = 0, + 90 = 90 <= 400 -> PASS
        - Action 2: cleared_sum = 90, + 90 = 180 <= 400 -> PASS
        - Action 3: cleared_sum = 180, + 90 = 270 <= 400 -> PASS
        - Action 4: cleared_sum = 270, + 90 = 360 <= 400 -> PASS
        - Action 5: cleared_sum = 360, + 90 = 450 > 400 -> ESCALATE (CATCHES the attack!)
        - Action 6: cleared_sum = 360, + 90 = 450 > 400 -> ESCALATE
        """
        category = "cloud_ops"
        per_action_cap = 100
        window_cap = 400
        amount = 90

        # Naive Baseline simulation:
        def naive_judge(amt):
            return "ALLOW" if amt <= per_action_cap else "DENY"

        baseline_verdicts = [naive_judge(amount) for _ in range(6)]
        self.assertEqual(baseline_verdicts, ["ALLOW", "ALLOW", "ALLOW", "ALLOW", "ALLOW", "ALLOW"])
        # Proof that naive baseline allowed total of 540 spend despite 400 window cap!

        # Guardrail Court velocity_guard:
        history = []
        guard_results = []
        for i in range(6):
            res = velocity_guard(history, category, amount, window_cap, window=10)
            guard_results.append(res)
            # If passed, simulate cleared decision added to history
            if res == "PASS":
                history.insert(0, {
                    "id": str(i + 1),
                    "category": category,
                    "amount": str(amount),
                    "verdict": "ALLOW",
                    "status": "CLEARED"
                })
            else:
                # Escalated decision is not cleared yet
                history.insert(0, {
                    "id": str(i + 1),
                    "category": category,
                    "amount": str(amount),
                    "verdict": "ESCALATE",
                    "status": "PENDING_OWNER"
                })

        # Verify that velocity_guard safely halts and escalates action 5 and 6!
        expected_guard = ["PASS", "PASS", "PASS", "PASS", "ESCALATE", "ESCALATE"]
        self.assertEqual(guard_results, expected_guard)
        print("\n[STAR TEST] Naive baseline passed all 6 requests (540 total).")
        print("[STAR TEST] Guardrail Court velocity_guard caught and escalated request 5 (450 > 400).")


if __name__ == '__main__':
    unittest.main()
