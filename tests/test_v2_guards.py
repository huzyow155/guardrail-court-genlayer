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


class TestV2Guards(unittest.TestCase):
    def setUp(self):
        self.owner = "0x" + "1" * 40
        self.agent = "0x" + "2" * 40
        self.recipient1 = "0x" + "3" * 40
        self.recipient2 = "0x" + "4" * 40
        self.stranger = "0x" + "9" * 40
        gl.message.sender_address.as_hex = self.owner
        self.court = CourtContract()
        gl.nondet.prompt_result = '{"verdict": "ALLOW"}'

    def _create_standard_policy(self, max_amount="500", window_cap="1000"):
        gl.message.sender_address.as_hex = self.owner
        pid = self.court.create_policy(
            agent=self.agent,
            text="Standard operating policy for testing guards and velocity limits.",
            max_amount=max_amount,
            window_cap=window_cap,
            allowed_recipients=json.dumps([self.recipient1, self.recipient2]),
            allowed_assets=json.dumps(["USDC", "WETH"])
        )
        return str(pid)

    # -------------------------------------------------------------
    # 1. Policy Creation Validation
    # -------------------------------------------------------------
    def test_policy_creation_validations(self):
        gl.message.sender_address.as_hex = self.owner

        # Invalid agent address
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy("invalid_address", "Policy text that meets the length requirements.", "100", "500", json.dumps([self.recipient1]), json.dumps(["USDC"]))
        self.assertIn("agent must be a valid address", str(cm.exception))

        # Policy text too short (<30)
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Short text", "100", "500", json.dumps([self.recipient1]), json.dumps(["USDC"]))
        self.assertIn("policy text length must be between 30 and 1200 characters", str(cm.exception))

        # Max amount invalid or zero
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "invalid", "500", json.dumps([self.recipient1]), json.dumps(["USDC"]))
        self.assertIn("max_amount must be a valid non-negative integer string", str(cm.exception))

        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "0", "500", json.dumps([self.recipient1]), json.dumps(["USDC"]))
        self.assertIn("max_amount must be >= 1", str(cm.exception))

        # Window cap < max_amount
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "500", "200", json.dumps([self.recipient1]), json.dumps(["USDC"]))
        self.assertIn("window_cap must be >= max_amount", str(cm.exception))

        # Allowed recipients empty
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "100", "500", json.dumps([]), json.dumps(["USDC"]))
        self.assertIn("allowed_recipients must contain between 1 and 10 items", str(cm.exception))

        # Allowed recipients duplicates
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "100", "500", json.dumps([self.recipient1, self.recipient1]), json.dumps(["USDC"]))
        self.assertIn("allowed_recipients must contain between 1 and 10 items", str(cm.exception))

        # Allowed recipients invalid address
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "100", "500", json.dumps(["0xnotvalid"]), json.dumps(["USDC"]))
        self.assertIn("invalid address in allowed_recipients", str(cm.exception))

        # Allowed assets empty
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "100", "500", json.dumps([self.recipient1]), json.dumps([]))
        self.assertIn("allowed_assets must contain between 1 and 10 items", str(cm.exception))

        # Allowed assets duplicates
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "100", "500", json.dumps([self.recipient1]), json.dumps(["USDC", "USDC"]))
        self.assertIn("allowed_assets must contain between 1 and 10 items", str(cm.exception))

        # Allowed assets invalid symbol
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.create_policy(self.agent, "Standard policy text for testing validation rules.", "100", "500", json.dumps([self.recipient1]), json.dumps(["U$DC!"]))
        self.assertIn("invalid asset in allowed_assets", str(cm.exception))

    # -------------------------------------------------------------
    # 2. Action Request Validation
    # -------------------------------------------------------------
    def test_action_request_validations(self):
        pid = self._create_standard_policy()
        calldata_hash = "a" * 64

        # Non-existent policy
        gl.message.sender_address.as_hex = self.agent
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action("999", "transfer", self.recipient1, "USDC", "100", calldata_hash, "Valid justification")
        self.assertIn("policy not found", str(cm.exception))

        # Policy paused
        gl.message.sender_address.as_hex = self.owner
        self.court.set_paused(pid, True)
        gl.message.sender_address.as_hex = self.agent
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", calldata_hash, "Valid justification")
        self.assertIn("policy is paused", str(cm.exception))
        gl.message.sender_address.as_hex = self.owner
        self.court.set_paused(pid, False)

        # Non-registered agent caller
        gl.message.sender_address.as_hex = self.stranger
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", calldata_hash, "Valid justification")
        self.assertIn("only the registered agent may request actions", str(cm.exception))

        gl.message.sender_address.as_hex = self.agent

        # Invalid category
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "TRANSFER_CAPS", self.recipient1, "USDC", "100", calldata_hash, "Valid justification")
        self.assertIn("invalid category format", str(cm.exception))

        # Invalid recipient address
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", "0xbad", "USDC", "100", calldata_hash, "Valid justification")
        self.assertIn("recipient must be a valid address", str(cm.exception))

        # Invalid asset format
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "T", "100", calldata_hash, "Valid justification")
        self.assertIn("invalid asset format", str(cm.exception))

        # Invalid amount or zero
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "0", calldata_hash, "Valid justification")
        self.assertIn("amount must be >= 1", str(cm.exception))

        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "10.5", calldata_hash, "Valid justification")
        self.assertIn("amount must be a valid non-negative integer string", str(cm.exception))

        # Calldata hash invalid (wrong length or prefix)
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", "0x" + "a"*64, "Valid justification")
        self.assertIn("calldata_hash must be a 64-character hex string", str(cm.exception))

        # Justification invalid
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", calldata_hash, "bad")
        self.assertIn("justification length must be between 5 and 600 characters without control chars", str(cm.exception))

        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", calldata_hash, "bad\x00control")
        self.assertIn("justification length must be between 5 and 600 characters without control chars", str(cm.exception))

    # -------------------------------------------------------------
    # 3. Deterministic Hard Guards (Amount, Recipient, Asset)
    # -------------------------------------------------------------
    def test_hard_limit_guard(self):
        pid = self._create_standard_policy(max_amount="500", window_cap="1000")
        gl.message.sender_address.as_hex = self.agent
        calldata_hash = "b" * 64

        # Request 501 > 500
        did = self.court.request_action(pid, "transfer", self.recipient1, "USDC", "501", calldata_hash, "Normal transfer")
        dec = json.loads(self.court.get_decision(did))
        self.assertEqual(dec["status"], "DENIED")
        self.assertEqual(dec["verdict"], "DENY")
        self.assertEqual(dec["source"], "HARD_LIMIT")

    def test_recipient_guard(self):
        pid = self._create_standard_policy()
        gl.message.sender_address.as_hex = self.agent
        calldata_hash = "c" * 64

        # Recipient not in allowlist
        unauthorized_recipient = "0x" + "8" * 40
        did = self.court.request_action(pid, "transfer", unauthorized_recipient, "USDC", "100", calldata_hash, "Normal transfer")
        dec = json.loads(self.court.get_decision(did))
        self.assertEqual(dec["status"], "DENIED")
        self.assertEqual(dec["verdict"], "DENY")
        self.assertEqual(dec["source"], "RECIPIENT_GUARD")

    def test_asset_guard(self):
        pid = self._create_standard_policy()
        gl.message.sender_address.as_hex = self.agent
        calldata_hash = "d" * 64

        # Asset not in allowlist (DAI not in USDC, WETH)
        did = self.court.request_action(pid, "transfer", self.recipient1, "DAI", "100", calldata_hash, "Normal transfer")
        dec = json.loads(self.court.get_decision(did))
        self.assertEqual(dec["status"], "DENIED")
        self.assertEqual(dec["verdict"], "DENY")
        self.assertEqual(dec["source"], "ASSET_GUARD")

    # -------------------------------------------------------------
    # 4. Velocity Guard & 30-Decision Boundary
    # -------------------------------------------------------------
    def test_velocity_guard_cumulative_and_cross_category(self):
        pid = self._create_standard_policy(max_amount="500", window_cap="1000")
        gl.message.sender_address.as_hex = self.agent
        calldata_hash = "e" * 64

        # Action 1: 400 USDC (transfer) -> CLEARED (total = 400 <= 1000)
        did1 = self.court.request_action(pid, "transfer", self.recipient1, "USDC", "400", calldata_hash, "Action 1 transfer")
        dec1 = json.loads(self.court.get_decision(did1))
        self.assertEqual(dec1["status"], "CLEARED")

        # Action 2: 400 WETH (swap) -> CLEARED (total = 800 <= 1000)
        did2 = self.court.request_action(pid, "swap", self.recipient2, "WETH", "400", calldata_hash, "Action 2 swap")
        dec2 = json.loads(self.court.get_decision(did2))
        self.assertEqual(dec2["status"], "CLEARED")

        # Action 3: 300 USDC (rebalance) -> ESCALATED because 800 + 300 = 1100 > 1000
        did3 = self.court.request_action(pid, "rebalance", self.recipient1, "USDC", "300", calldata_hash, "Action 3 rebalance")
        dec3 = json.loads(self.court.get_decision(did3))
        self.assertEqual(dec3["status"], "PENDING_OWNER")
        self.assertEqual(dec3["verdict"], "ESCALATE")
        self.assertEqual(dec3["source"], "VELOCITY")

    def test_velocity_30_decision_boundary(self):
        # max_amount 100, window_cap 500
        pid = self._create_standard_policy(max_amount="100", window_cap="500")
        gl.message.sender_address.as_hex = self.agent
        calldata_hash = "f" * 64

        # Clear 5 actions of 100 (total = 500)
        for i in range(5):
            did = self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", calldata_hash, f"Clearing action {i}")
            dec = json.loads(self.court.get_decision(did))
            self.assertEqual(dec["status"], "CLEARED")

        # Now total cleared in window = 500. Next action of 100 exceeds window_cap (500 + 100 = 600 > 500)
        did_exceeded = self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", calldata_hash, "Exceeding action")
        dec_exceeded = json.loads(self.court.get_decision(did_exceeded))
        self.assertEqual(dec_exceeded["status"], "PENDING_OWNER")
        self.assertEqual(dec_exceeded["verdict"], "ESCALATE")
        self.assertEqual(dec_exceeded["source"], "VELOCITY")

        # Resolve that escalation as DENY so it doesn't count as CLEARED
        gl.message.sender_address.as_hex = self.owner
        self.court.resolve_escalation(did_exceeded, "DENY")

        # Now generate 30 DENIED actions (amount 101 > 100) to push the initial 5 actions out of the 30-decision window
        gl.message.sender_address.as_hex = self.agent
        for i in range(30):
            did_denied = self.court.request_action(pid, "transfer", self.recipient1, "USDC", "101", calldata_hash, f"Denial push {i}")
            dec_denied = json.loads(self.court.get_decision(did_denied))
            self.assertEqual(dec_denied["status"], "DENIED")

        # Now the initial 5 CLEARED actions are >30 decisions ago!
        # An action of 100 should now be CLEARED because window sum is 0 <= 500
        did_new = self.court.request_action(pid, "transfer", self.recipient1, "USDC", "100", calldata_hash, "Fresh action outside window")
        dec_new = json.loads(self.court.get_decision(did_new))
        self.assertEqual(dec_new["status"], "CLEARED")

    # -------------------------------------------------------------
    # 5. Pending Escalation Queue Cap (Max 10)
    # -------------------------------------------------------------
    def test_pending_escalations_queue_cap(self):
        pid = self._create_standard_policy(max_amount="100", window_cap="100")
        gl.message.sender_address.as_hex = self.agent
        calldata_hash = "0" * 64

        # Model always escalates
        gl.nondet.prompt_result = '{"verdict": "ESCALATE"}'

        # Create 10 pending escalations
        for i in range(10):
            did = self.court.request_action(pid, "transfer", self.recipient1, "USDC", "50", calldata_hash, f"Escalation action {i}")
            dec = json.loads(self.court.get_decision(did))
            self.assertEqual(dec["status"], "PENDING_OWNER")

        # Verify pending count
        pending_list = json.loads(self.court.pending_escalations(pid))
        self.assertEqual(len(pending_list), 10)

        # 11th action must revert with UserError("too many pending escalations")
        with self.assertRaises(gl.vm.UserError) as cm:
            self.court.request_action(pid, "transfer", self.recipient1, "USDC", "50", calldata_hash, "11th action")
        self.assertIn("too many pending escalations", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
