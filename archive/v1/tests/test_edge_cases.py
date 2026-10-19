import unittest
import sys
import os

# Import genlayer stub and real GuardrailCourt contract
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../tests")))
import genlayer_stub

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import GuardrailCourt

is_valid_address = GuardrailCourt._is_valid_address
is_valid_amount_str = GuardrailCourt._is_valid_amount_str
is_valid_category = GuardrailCourt._is_valid_category
parse_model_verdict = GuardrailCourt._parse_model_verdict
velocity_guard = GuardrailCourt._velocity_guard


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
        # Within history_items passed to _velocity_guard, it takes up to 10 matching category items
        history = []
        # Add 5 old cleared decisions of amount 100
        for i in range(5):
            history.append({"category": "test_cat", "amount": "100", "status": "CLEARED"})
        # Add 10 newer cleared decisions of amount 10
        for i in range(10):
            history.insert(0, {"category": "test_cat", "amount": "10", "status": "CLEARED"})
        
        # Newest 10 matching items have sum = 10 * 10 = 100
        # If window_cap is 150 and amount is 40 -> 100 + 40 = 140 <= 150 -> PASS
        # If it incorrectly included the older 5 * 100 = 500, it would fail
        self.assertEqual(velocity_guard(history, "test_cat", 40, window_cap=150, window=10), "PASS")

    def test_velocity_eviction_by_15_other_category_decisions(self):
        """
        Proves on the real GuardrailCourt contract that request_action fetches only
        policy_history_ids[:15] across the entire policy before filtering by category.
        If 15 newer decisions in category 'other_cat' occur after a 'target_cat' decision,
        the older 'target_cat' decision is pushed outside policy_history_ids[:15] and not counted.
        """
        import json
        gl = GuardrailCourt.gl
        court = GuardrailCourt.GuardrailCourt()
        court.__init__()

        owner = "0x1111111111111111111111111111111111111111"
        agent = "0x2222222222222222222222222222222222222222"

        gl.message.sender_address.as_hex = owner
        pid = court.create_policy(
            agent,
            "Policy allowing target_cat and other_cat purchases up to cap 100 and window 150.",
            "100",
            "150",
        )

        gl.message.sender_address.as_hex = agent
        gl.nondet.prompt_result = '{"verdict": "ALLOW"}'

        # 1. Submit 1 cleared request in 'target_cat' with amount 90 (cumulative in target_cat = 90)
        d1 = court.request_action(pid, "target_cat", "90", "First target_cat purchase of 90")
        self.assertEqual(json.loads(court.get_decision(d1))["status"], "CLEARED")

        # 2. If we immediately requested another 90 in 'target_cat', 90 + 90 = 180 > 150 would ESCALATE.
        # Instead, submit 15 requests in 'other_cat' (amount 10 each) to push d1 out of policy_history_ids[:15].
        for i in range(15):
            court.request_action(pid, "other_cat", "10", f"Intervening other_cat request #{i+1}")

        # 3. Now submit a second request in 'target_cat' with amount 90.
        # Because d1 is at index 15 (16th newest), policy_history_ids[:15] contains only 'other_cat' items.
        # _velocity_guard sees 0 prior 'target_cat' spend (0 + 90 <= 150) and passes to JUDGE -> ALLOW!
        d_after = court.request_action(pid, "target_cat", "90", "Second target_cat purchase after 15 other_cat items")
        dec_after = json.loads(court.get_decision(d_after))
        self.assertEqual(dec_after["source"], "JUDGE")
        self.assertEqual(dec_after["verdict"], "ALLOW")
        self.assertEqual(dec_after["status"], "CLEARED")


if __name__ == '__main__':
    unittest.main()
