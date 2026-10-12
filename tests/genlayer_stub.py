import sys
import types
import json

def setup_genlayer_stub():
    """
    Installs a minimal GenVM / genlayer stub into sys.modules
    allowing direct import and execution of contracts/GuardrailCourt.py.
    """
    if "genlayer" in sys.modules and hasattr(sys.modules["genlayer"], "_is_test_stub"):
        return sys.modules["genlayer"]

    mod = types.ModuleType("genlayer")
    mod._is_test_stub = True

    class MockTreeMap(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        def __class_getitem__(cls, item):
            return cls

    class MockContract:
        def __new__(cls, *args, **kwargs):
            inst = super().__new__(cls)
            inst.policies = MockTreeMap()
            inst.decisions = MockTreeMap()
            inst.by_owner = MockTreeMap()
            inst.by_agent = MockTreeMap()
            inst.by_policy = MockTreeMap()
            inst.meta = MockTreeMap()
            return inst

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
        prompt_result = '{"verdict": "ALLOW"}'
        @classmethod
        def exec_prompt(cls, prompt):
            return cls.prompt_result

    class MockEqPrinciple:
        @staticmethod
        def strict_eq(fn):
            return fn()

    class MockMessage:
        class sender_address:
            as_hex = "0x1111111111111111111111111111111111111111"

    class MockGL:
        Contract = MockContract
        vm = MockVM
        public = MockPublic
        nondet = MockNondet
        eq_principle = MockEqPrinciple
        message = MockMessage

    mod.gl = MockGL
    mod.TreeMap = MockTreeMap
    mod.Address = str

    sys.modules["genlayer"] = mod
    return mod

# Auto-setup on import
setup_genlayer_stub()
