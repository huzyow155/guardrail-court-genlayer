import unittest
import sys
import os
import json
import hashlib

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import genlayer_stub
from genlayer import gl

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))
import GuardrailCourtV2
from GuardrailCourtV2 import GuardrailCourtV2 as CourtContract


def compute_expected_action_hash(policy_id, category, recipient, asset, amount, calldata_hash):
    canonical = f"GC2|{policy_id.strip()}|{category.strip()}|{recipient.strip().lower()}|{asset.strip().lower()}|{amount.strip()}|{calldata_hash.strip().lower()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class TestV2Binding(unittest.TestCase):
    def setUp(self):
        self.owner = "0x" + "1" * 40
        self.agent = "0x" + "2" * 40
        self.recipient = "0x" + "3" * 40
        self.wrong_recipient = "0x" + "4" * 40
        gl.message.sender_address.as_hex = self.owner
        self.court = CourtContract()
        gl.nondet.prompt_result = '{"verdict": "ALLOW"}'

        self.pid = self.court.create_policy(
            agent=self.agent,
            text="Standard binding test policy for verifying cryptographic action commitments.",
            max_amount="1000",
            window_cap="5000",
            allowed_recipients=json.dumps([self.recipient, self.wrong_recipient]),
            allowed_assets=json.dumps(["USDC", "WETH"])
        )

    def test_action_hash_oracle_parity(self):
        policy_id = "1"
        category = "transfer"
        recipient = "0x" + "a" * 40
        asset = "USDC"
        amount = "250"
        calldata_hash = "beef" * 16

        court_hash = self.court.get_action_hash(policy_id, category, recipient, asset, amount, calldata_hash)
        expected_hash = compute_expected_action_hash(policy_id, category, recipient, asset, amount, calldata_hash)
        self.assertEqual(court_hash, expected_hash)

        # Casing insensitivity check
        court_hash_cased = self.court.get_action_hash(policy_id, category, recipient.upper(), "usdc", amount, calldata_hash.upper())
        self.assertEqual(court_hash_cased, expected_hash)

    def test_is_cleared_for_positive_match(self):
        gl.message.sender_address.as_hex = self.agent
        category = "transfer"
        asset = "USDC"
        amount = "150"
        calldata_hash = "c001" * 16
        justification = "Testing positive clearance binding"

        did = self.court.request_action(self.pid, category, self.recipient, asset, amount, calldata_hash, justification)
        
        # Verify positive clearance
        is_cleared = self.court.is_cleared_for(
            decision_id=did,
            policy_id=self.pid,
            category=category,
            recipient=self.recipient,
            asset=asset,
            amount=amount,
            calldata_hash=calldata_hash
        )
        self.assertTrue(is_cleared)

        # Casing variations should also resolve to True due to normalization
        self.assertTrue(self.court.is_cleared_for(
            decision_id=did,
            policy_id=self.pid,
            category=category,
            recipient=self.recipient.upper(),
            asset="usdc",
            amount=amount,
            calldata_hash=calldata_hash.upper()
        ))

    def test_is_cleared_for_mismatch_permutations(self):
        gl.message.sender_address.as_hex = self.agent
        category = "transfer"
        asset = "USDC"
        amount = "150"
        calldata_hash = "c001" * 16
        justification = "Testing mismatch clearance permutations"

        did = self.court.request_action(self.pid, category, self.recipient, asset, amount, calldata_hash, justification)

        # 1. Non-existent decision_id
        self.assertFalse(self.court.is_cleared_for("99999", self.pid, category, self.recipient, asset, amount, calldata_hash))

        # 2. Wrong policy_id
        self.assertFalse(self.court.is_cleared_for(did, "999", category, self.recipient, asset, amount, calldata_hash))

        # 3. Wrong category
        self.assertFalse(self.court.is_cleared_for(did, self.pid, "swap", self.recipient, asset, amount, calldata_hash))

        # 4. Wrong recipient (recipient hijacking prevention)
        self.assertFalse(self.court.is_cleared_for(did, self.pid, category, self.wrong_recipient, asset, amount, calldata_hash))

        # 5. Wrong asset (asset substitution prevention)
        self.assertFalse(self.court.is_cleared_for(did, self.pid, category, self.recipient, "WETH", amount, calldata_hash))

        # 6. Wrong amount (amount inflation prevention)
        self.assertFalse(self.court.is_cleared_for(did, self.pid, category, self.recipient, asset, "151", calldata_hash))
        self.assertFalse(self.court.is_cleared_for(did, self.pid, category, self.recipient, asset, "149", calldata_hash))

        # 7. Wrong calldata_hash (payload tampering prevention)
        wrong_hash = "dead" * 16
        self.assertFalse(self.court.is_cleared_for(did, self.pid, category, self.recipient, asset, amount, wrong_hash))

    def test_is_cleared_for_uncleared_states(self):
        # 1. Denied action
        gl.message.sender_address.as_hex = self.agent
        calldata_hash = "d00d" * 16
        # Hard limit denial (amount 1001 > 1000)
        did_denied = self.court.request_action(self.pid, "transfer", self.recipient, "USDC", "1001", calldata_hash, "Will be denied")
        self.assertFalse(self.court.is_cleared_for(did_denied, self.pid, "transfer", self.recipient, "USDC", "1001", calldata_hash))

        # 2. Pending owner action (not yet resolved)
        gl.nondet.prompt_result = '{"verdict": "ESCALATE"}'
        did_pending = self.court.request_action(self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash, "Will be escalated")
        self.assertFalse(self.court.is_cleared_for(did_pending, self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash))

        # 3. Denied by owner resolution
        gl.message.sender_address.as_hex = self.owner
        self.court.resolve_escalation(did_pending, "DENY")
        self.assertFalse(self.court.is_cleared_for(did_pending, self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash))

        # 4. Cleared by owner resolution
        gl.message.sender_address.as_hex = self.agent
        did_pending2 = self.court.request_action(self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash, "Will be escalated then approved")
        self.assertFalse(self.court.is_cleared_for(did_pending2, self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash))
        gl.message.sender_address.as_hex = self.owner
        self.court.resolve_escalation(did_pending2, "ALLOW")
        self.assertTrue(self.court.is_cleared_for(did_pending2, self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash))


if __name__ == "__main__":
    unittest.main()
