import sys
import types
import json

def setup_genlayer_stub():
    """
    Installs a minimal GenVM / genlayer stub into sys.modules
    allowing direct import and execution of GuardrailCourt contracts.
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
            inst.executions = MockTreeMap()
            inst.executed_decisions = MockTreeMap()
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
        last_prompt = None
        @classmethod
        def exec_prompt(cls, prompt):
            cls.last_prompt = prompt
            return cls.prompt_result

    class MockEqPrinciple:
        @staticmethod
        def strict_eq(fn):
            return fn()

    class MockMessage:
        class sender_address:
            as_hex = "0x1111111111111111111111111111111111111111"

    class ContractProxy:
        def __init__(self, target):
            self._target = target
        def view(self):
            return self._target
        def __getattr__(self, name):
            return getattr(self._target, name)

    class MockGL:
        Contract = MockContract
        vm = MockVM
        public = MockPublic
        nondet = MockNondet
        eq_principle = MockEqPrinciple
        message = MockMessage
        _registered_contracts = {}

        @classmethod
        def register_contract(cls, address, instance):
            cls._registered_contracts[str(address).lower()] = instance

        @classmethod
        def get_contract_at(cls, address):
            addr = str(address).lower()
            if addr in cls._registered_contracts:
                return ContractProxy(cls._registered_contracts[addr])
            # If target instance happens to have matching address or is registered
            raise ValueError(f"No contract registered at {addr}")

    mod.gl = MockGL
    mod.TreeMap = MockTreeMap
    mod.Address = str

    sys.modules["genlayer"] = mod
    return mod

# Auto-setup on import
setup_genlayer_stub()
