import sys
import types
import unittest

# Build lightweight stub for genlayer
genlayer_mod = types.ModuleType("genlayer")

class MockTreeMap:
    def __class_getitem__(cls, item):
        return cls

class MockContract:
    pass

class MockVM:
    class UserError(Exception):
        pass

class MockPublic:
    @staticmethod
    def write(fn):
        return fn
    @staticmethod
    def view(fn):
        return fn

class MockNondet:
    @staticmethod
    def exec_prompt(prompt):
        return '{"verdict": "ALLOW"}'

class MockEqPrinciple:
    @staticmethod
    def strict_eq(fn):
        return fn()

class MockMessage:
    class sender_address:
        as_hex = "0x1b1e4a79e286434c428a576e6d91bc2220661cf3"

class MockGL:
    Contract = MockContract
    vm = MockVM
    public = MockPublic
    nondet = MockNondet
    eq_principle = MockEqPrinciple
    message = MockMessage

genlayer_mod.gl = MockGL
genlayer_mod.TreeMap = MockTreeMap
genlayer_mod.Address = str

sys.modules["genlayer"] = genlayer_mod

# Now import the REAL contracts/GuardrailCourt.py
sys.path.insert(0, "contracts")
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
