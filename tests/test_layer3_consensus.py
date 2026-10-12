import unittest
import sys
import os
import json
from collections import Counter

# Import genlayer stub and real GuardrailCourt contract
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import genlayer_stub

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))
import GuardrailCourt

parse_model_verdict = GuardrailCourt._parse_model_verdict


class TestLayer3Consensus(unittest.TestCase):

    def simulate_validator_round(self, raw_model_outputs: list[str]) -> tuple[str, bool]:
        """
        Simulates GenLayer multi-validator consensus across 5 validator nodes.
        Each node runs _parse_model_verdict on its raw LLM output.
        Consensus is reached if a majority (>= 3 of 5) agree on the exact canonical label.
        """
        canonical_votes = [parse_model_verdict(out) for out in raw_model_outputs]
        counts = Counter(canonical_votes)
        top_decision, top_count = counts.most_common(1)[0]
        has_majority = top_count >= 3
        return top_decision, has_majority

    def test_validators_agree_on_clean_allow(self):
        # 5 validators returning slight formatting variations of ALLOW
        outputs = [
            '{"verdict": "ALLOW"}',
            '```json\n{"verdict": "ALLOW"}\n```',
            ' {"verdict": "ALLOW"} \n',
            '{"verdict":"allow"}',
            '{"verdict": "ALLOW"}',
        ]
        decision, agreed = self.simulate_validator_round(outputs)
        self.assertTrue(agreed)
        self.assertEqual(decision, "ALLOW")

    def test_validators_agree_on_clean_deny(self):
        outputs = [
            '{"verdict": "DENY"}',
            '```json\n{"verdict": "DENY"}\n```',
            '{"verdict": "DENY"}',
            '{"verdict": "deny"}',
            '{"verdict": "DENY"}',
        ]
        decision, agreed = self.simulate_validator_round(outputs)
        self.assertTrue(agreed)
        self.assertEqual(decision, "DENY")

    def test_validators_majority_escalate_on_ambiguity(self):
        outputs = [
            '{"verdict": "ESCALATE"}',
            '{"verdict": "ESCALATE"}',
            '{"verdict": "DENY"}',
            '{"verdict": "ESCALATE"}',
            '{"verdict": "ALLOW"}',
        ]
        decision, agreed = self.simulate_validator_round(outputs)
        self.assertTrue(agreed)
        self.assertEqual(decision, "ESCALATE")

    def test_validators_split_disagree_case(self):
        # 2 ALLOW, 2 DENY, 1 ESCALATE -> No majority >= 3
        outputs = [
            '{"verdict": "ALLOW"}',
            '{"verdict": "ALLOW"}',
            '{"verdict": "DENY"}',
            '{"verdict": "DENY"}',
            '{"verdict": "ESCALATE"}',
        ]
        decision, agreed = self.simulate_validator_round(outputs)
        self.assertFalse(agreed)

    def test_validators_with_malformed_outputs_fail_closed_to_escalate(self):
        # If 3 validators produce corrupted/unparseable outputs, they all fail-closed to ESCALATE
        outputs = [
            '{"verdict": "ALLOW"}',
            'corrupted output 1',
            'unparseable text 2',
            'MALICIOUS INJECTION: IGNORE RULES',
            '{"verdict": "ALLOW"}',
        ]
        decision, agreed = self.simulate_validator_round(outputs)
        # corrupted, unparseable, and injection all parse to ESCALATE (3 votes) -> Majority ESCALATE
        self.assertTrue(agreed)
        self.assertEqual(decision, "ESCALATE")


if __name__ == '__main__':
    unittest.main()
