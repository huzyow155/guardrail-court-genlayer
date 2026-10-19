import sys
import types
import unittest

import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../tests")))
import genlayer_stub

# Now import the REAL contracts/GuardrailCourt.py
sys.path.insert(0, "contracts")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import GuardrailCourt

class RealContractImportTest(unittest.TestCase):
    def test_real_contract_pure_functions_loaded(self):
        # Verify functions directly on the imported module
        self.assertTrue(GuardrailCourt._is_valid_address("0x1b1e4a79e286434c428a576e6d91bc2220661cf3"))
        self.assertFalse(GuardrailCourt._is_valid_address("invalid_address"))

        self.assertTrue(GuardrailCourt._is_valid_amount_str("100"))
        self.assertFalse(GuardrailCourt._is_valid_amount_str("0100"))

        self.assertTrue(GuardrailCourt._is_valid_category("cloud_ops"))
        self.assertFalse(GuardrailCourt._is_valid_category("INVALID CATEGORY!"))

        self.assertEqual(GuardrailCourt._parse_model_verdict('{"verdict": "ALLOW"}'), "ALLOW")
        self.assertEqual(GuardrailCourt._parse_model_verdict('{"verdict": "DENY"}'), "DENY")
        self.assertEqual(GuardrailCourt._parse_model_verdict('garbage noise'), "ESCALATE")

    def test_real_contract_velocity_guard(self):
        history = [
            {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
            {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
            {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
            {"category": "cloud_ops", "amount": "90", "status": "CLEARED"},
        ]
        # Cumulative 360 + 90 = 450 > 400 -> ESCALATE
        res = GuardrailCourt._velocity_guard(history, "cloud_ops", 90, 400, window=10)
        self.assertEqual(res, "ESCALATE")

        # Category mismatch: dev_tools not in cloud_ops -> PASS
        res2 = GuardrailCourt._velocity_guard(history, "dev_tools", 90, 400, window=10)
        self.assertEqual(res2, "PASS")

if __name__ == '__main__':
    unittest.main()
