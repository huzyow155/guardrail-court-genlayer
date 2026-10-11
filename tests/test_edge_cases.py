import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))

from guardrail_helpers import (
    is_valid_address,
    is_valid_amount_str,
    is_valid_category,
    parse_model_verdict,
    velocity_guard,
)


class TestEdgeCasesAndLimits(unittest.TestCase):

    def test_zero_amount_and_unlimited_caps(self):
        # "0" amount is valid non-negative integer
        self.assertTrue(is_valid_amount_str("0"))
        # When window_cap is 0, velocity_guard should always PASS
        history = [
            {"category": "ops", "amount": "1000", "verdict": "ALLOW", "status": "CLEARED"},
            {"category": "ops", "amount": "5000", "verdict": "ALLOW", "status": "CLEARED"},
        ]
        self.assertEqual(velocity_guard(history, "ops", 999999, window_cap=0), "PASS")

    def test_category_boundary_lengths(self):
        # 1 character category
        self.assertTrue(is_valid_category("a"))
        self.assertTrue(is_valid_category("1"))
        # 30 characters category
        self.assertTrue(is_valid_category("a" * 30))
        # 31 characters category (too long)
        self.assertFalse(is_valid_category("a" * 31))

    def test_model_verdict_fence_variations(self):
        fenced_with_language = "```json\n{\"verdict\": \"DENY\"}\n```"
        fenced_plain = "```\n{\"verdict\": \"DENY\"}\n```"
        fenced_with_spacing = "```json\n\n   {\"verdict\": \"ALLOW\"}   \n\n```"
        
        self.assertEqual(parse_model_verdict(fenced_with_language), "DENY")
        self.assertEqual(parse_model_verdict(fenced_plain), "DENY")
        self.assertEqual(parse_model_verdict(fenced_with_spacing), "ALLOW")

    def test_velocity_window_truncation_to_10(self):
        # If there are 15 historical decisions in same category, velocity_guard inspects only the last 10
        history = []
        # Add 5 old cleared decisions of amount 100
        for i in range(5):
            history.append({"category": "test_cat", "amount": "100", "status": "CLEARED"})
        # Add 10 newer cleared decisions of amount 10
        for i in range(10):
            history.insert(0, {"category": "test_cat", "amount": "10", "status": "CLEARED"})
        
        # Newest 10 decisions have sum = 10 * 10 = 100
        # If window_cap is 150 and amount is 40 -> 100 + 40 = 140 <= 150 -> PASS
        # If it incorrectly included the older 5 * 100 = 500, it would fail
        self.assertEqual(velocity_guard(history, "test_cat", 40, window_cap=150, window=10), "PASS")


if __name__ == '__main__':
    unittest.main()
