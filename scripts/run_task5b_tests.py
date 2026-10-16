import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests")))
import genlayer_stub
import test_v2_guards
import test_v2_binding
import test_v2_lifecycle

def run_specific_test(test_class, method_name):
    suite = unittest.TestSuite()
    suite.addTest(test_class(method_name))
    runner = unittest.TextTestRunner(verbosity=2)
    print(f"\n================================================================================")
    print(f"RUNNING: {test_class.__name__}.{method_name}")
    print(f"================================================================================")
    result = runner.run(suite)
    return result

def main():
    # 1. Non-agent sender error
    run_specific_test(test_v2_guards.TestV2Guards, "test_action_request_validations")
    
    # 2. Paused policy rejects request_action
    run_specific_test(test_v2_lifecycle.TestV2Lifecycle, "test_pause_unpause_permissions")
    
    # 3. Owner resolution to ALLOW + 7-parameter exact match
    run_specific_test(test_v2_binding.TestV2Binding, "test_is_cleared_for_uncleared_states")
    run_specific_test(test_v2_binding.TestV2Binding, "test_is_cleared_for_mismatch_permutations")
    
    # 4. Velocity counting cleared only, policy-wide, and 30-decision boundary
    run_specific_test(test_v2_guards.TestV2Guards, "test_velocity_guard_cumulative_and_cross_category")
    run_specific_test(test_v2_guards.TestV2Guards, "test_velocity_30_decision_boundary")

if __name__ == "__main__":
    main()
