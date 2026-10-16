import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import genlayer_stub
from genlayer import gl

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))
import GuardrailCourtV2
from GuardrailCourtV2 import GuardrailCourtV2 as CourtContract


class TestV2Lifecycle(unittest.TestCase):
    def setUp(self):
        self.owner = "0x" + "1" * 40
        self.agent = "0x" + "2" * 40
        self.stranger = "0x" + "8" * 40
        self.recipient = "0x" + "3" * 40
        gl.message.sender_address.as_hex = self.owner
        self.court = CourtContract()
        gl.nondet.prompt_result = '{"verdict": "ALLOW"}'

        self.pid = self.court.create_policy(
            agent=self.agent,
            text="Comprehensive lifecycle test policy covering all operational flows.",
            max_amount="500",
            window_cap="1500",
            allowed_recipients=json.dumps([self.recipient]),
            allowed_assets=json.dumps(["USDC"])
        )

    def test_complete_lifecycle(self):
        calldata_hash = "beef" * 16

        # Step 1: Agent requests action -> Cleared by LLM Judge
        gl.message.sender_address.as_hex = self.agent
        did1 = self.court.request_action(self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash, "First valid request")
        dec1 = json.loads(self.court.get_decision(did1))
        self.assertEqual(dec1["status"], "CLEARED")
        self.assertEqual(dec1["verdict"], "ALLOW")
        self.assertEqual(dec1["source"], "JUDGE")

        # Step 2: Agent requests action -> Escalated by LLM Judge
        gl.nondet.prompt_result = '{"verdict": "ESCALATE"}'
        did2 = self.court.request_action(self.pid, "transfer", self.recipient, "USDC", "100", calldata_hash, "Second suspicious request")
        dec2 = json.loads(self.court.get_decision(did2))
        self.assertEqual(dec2["status"], "PENDING_OWNER")
        self.assertEqual(dec2["verdict"], "ESCALATE")
        self.assertEqual(dec2["source"], "JUDGE")

        # Step 3: Verify pending escalations list
        pending = json.loads(self.court.pending_escalations(self.pid))
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["id"], did2)

        # Step 4: Resolution permissions and validation
        # Stranger attempts resolution
        gl.message.sender_address.as_hex = self.stranger
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.resolve_escalation(did2, "ALLOW")
        self.assertIn("only the policy owner may resolve escalations", str(cm.exception))

        # Owner attempts resolution with invalid outcome
        gl.message.sender_address.as_hex = self.owner
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.resolve_escalation(did2, "MAYBE")
        self.assertIn("outcome must be ALLOW or DENY", str(cm.exception))

        # Owner resolves escalation with ALLOW
        self.court.resolve_escalation(did2, "ALLOW")
        dec2_resolved = json.loads(self.court.get_decision(did2))
        self.assertEqual(dec2_resolved["status"], "CLEARED")
        self.assertEqual(dec2_resolved["verdict"], "ALLOW")
        self.assertTrue(dec2_resolved["resolved_by_owner"])

        # Attempt to resolve again
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.resolve_escalation(did2, "ALLOW")
        self.assertIn("decision is not pending owner resolution", str(cm.exception))

        # Step 5: Verify pending escalations is now empty
        pending_after = json.loads(self.court.pending_escalations(self.pid))
        self.assertEqual(len(pending_after), 0)

        # Step 6: Verify stats
        stats = json.loads(self.court.get_policy_stats(self.pid))
        self.assertEqual(stats["total_decisions"], 2)
        self.assertEqual(stats["cleared_count"], 2)
        self.assertEqual(stats["pending_owner_count"], 0)
        self.assertEqual(stats["verdicts"]["ALLOW"], 2)
        self.assertEqual(stats["verdicts"]["DENY"], 0)

    def test_pause_unpause_permissions(self):
        # Stranger cannot pause
        gl.message.sender_address.as_hex = self.stranger
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.set_paused(self.pid, True)
        self.assertIn("only the policy owner may pause or unpause", str(cm.exception))

        # Owner pauses
        gl.message.sender_address.as_hex = self.owner
        self.court.set_paused(self.pid, True)
        policy = json.loads(self.court.get_policy(self.pid))
        self.assertTrue(policy["paused"])

        # Agent cannot act while paused
        gl.message.sender_address.as_hex = self.agent
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(self.pid, "transfer", self.recipient, "USDC", "50", "a"*64, "Justification while paused")
        self.assertIn("policy is paused", str(cm.exception))

        # Owner unpauses
        gl.message.sender_address.as_hex = self.owner
        self.court.set_paused(self.pid, False)
        policy_unpaused = json.loads(self.court.get_policy(self.pid))
        self.assertFalse(policy_unpaused["paused"])

    def test_query_reverts_on_missing_records(self):
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.get_policy("nonexistent_policy")
        self.assertIn("policy not found", str(cm.exception))

        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.get_decision("nonexistent_decision")
        self.assertIn("decision not found", str(cm.exception))

        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.get_policy_stats("nonexistent_policy")
        self.assertIn("policy not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
