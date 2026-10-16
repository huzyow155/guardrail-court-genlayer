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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples', 'consumer')))
import GuardedVaultV2
from GuardedVaultV2 import GuardedVaultV2 as VaultContract


class TestV2Vault(unittest.TestCase):
    def setUp(self):
        self.owner = "0x" + "1" * 40
        self.agent = "0x" + "2" * 40
        self.recipient = "0x" + "3" * 40
        self.stranger = "0x" + "8" * 40
        self.court_addr = "0x" + "c" * 40

        # Deploy Court and register in stub contract directory
        gl.message.sender_address.as_hex = self.owner
        self.court = CourtContract()
        gl.register_contract(self.court_addr, self.court)

        # Deploy GuardedVaultV2 connected to Court
        self.vault = VaultContract(self.court_addr)

        # Default model result
        gl.nondet.prompt_result = '{"verdict": "ALLOW"}'

        # Create policy in Court
        self.pid = self.court.create_policy(
            agent=self.agent,
            text="Standard operating policy for guarded consumer vault integration.",
            max_amount="1000",
            window_cap="5000",
            allowed_recipients=json.dumps([self.recipient]),
            allowed_assets=json.dumps(["USDC"])
        )

    def test_vault_positive_execution(self):
        calldata_hash = "beef" * 16
        category = "transfer"
        asset = "USDC"
        amount = "250"

        # 1. Agent requests action in Court -> CLEARED
        gl.message.sender_address.as_hex = self.agent
        did = self.court.request_action(self.pid, category, self.recipient, asset, amount, calldata_hash, "Vault transfer request")

        # 2. Vault checks is_cleared_for and executes successfully
        gl.message.sender_address.as_hex = self.agent
        executed_id = self.vault.execute(did, self.pid, category, self.recipient, asset, amount, calldata_hash)
        self.assertEqual(executed_id, did)
        self.assertTrue(self.vault.is_executed(did))

        # 3. Execution record exists in vault
        record = json.loads(self.vault.get_execution(did))
        self.assertEqual(record["decision_id"], did)
        self.assertEqual(record["recipient"], self.recipient.lower())
        self.assertEqual(record["asset"], asset)
        self.assertEqual(record["amount"], amount)
        self.assertEqual(record["calldata_hash"], calldata_hash.lower())
        self.assertEqual(record["caller"], self.agent.lower())

    def test_vault_replay_attack_rejected(self):
        calldata_hash = "beef" * 16
        category = "transfer"
        asset = "USDC"
        amount = "100"

        # Agent requests and clears action
        gl.message.sender_address.as_hex = self.agent
        did = self.court.request_action(self.pid, category, self.recipient, asset, amount, calldata_hash, "Action to test replay")
        self.vault.execute(did, self.pid, category, self.recipient, asset, amount, calldata_hash)
        self.assertTrue(self.vault.is_executed(did))

        # Second execution attempt with same decision_id must revert
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did, self.pid, category, self.recipient, asset, amount, calldata_hash)
        self.assertIn("decision has already been executed", str(cm.exception))

    def test_vault_mismatch_parameters_rejected(self):
        calldata_hash = "cafe" * 16
        category = "transfer"
        asset = "USDC"
        amount = "200"

        gl.message.sender_address.as_hex = self.agent
        did = self.court.request_action(self.pid, category, self.recipient, asset, amount, calldata_hash, "Action to test mismatches")

        # Mismatch 1: Wrong amount (e.g. agent asks for 200, but vault caller tries to execute 201)
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did, self.pid, category, self.recipient, asset, "201", calldata_hash)
        self.assertIn("clearance does not match this action", str(cm.exception))

        # Mismatch 2: Wrong recipient (vault caller diverts to stranger)
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did, self.pid, category, self.stranger, asset, amount, calldata_hash)
        self.assertIn("clearance does not match this action", str(cm.exception))

        # Mismatch 3: Wrong calldata_hash (tampered transaction calldata)
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did, self.pid, category, self.recipient, asset, amount, "dead" * 16)
        self.assertIn("clearance does not match this action", str(cm.exception))

        # Mismatch 4: Wrong policy_id
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did, "999", category, self.recipient, asset, amount, calldata_hash)
        self.assertIn("clearance does not match this action", str(cm.exception))

    def test_vault_uncleared_decisions_rejected(self):
        calldata_hash = "beef" * 16
        category = "transfer"
        asset = "USDC"
        amount = "100"

        # 1. Denied action
        gl.message.sender_address.as_hex = self.agent
        did_denied = self.court.request_action(self.pid, category, self.recipient, asset, "1001", calldata_hash, "Over hard limit")
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did_denied, self.pid, category, self.recipient, asset, "1001", calldata_hash)
        self.assertIn("clearance does not match this action", str(cm.exception))

        # 2. Unresolved escalation
        gl.nondet.prompt_result = '{"verdict": "ESCALATE"}'
        did_escalated = self.court.request_action(self.pid, category, self.recipient, asset, amount, calldata_hash, "Suspicious action")
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did_escalated, self.pid, category, self.recipient, asset, amount, calldata_hash)
        self.assertIn("clearance does not match this action", str(cm.exception))

        # 3. Cleared decision on a paused policy raises "clearance does not match this action"
        gl.nondet.prompt_result = '{"verdict": "ALLOW"}'
        did_cleared = self.court.request_action(self.pid, category, self.recipient, asset, amount, calldata_hash, "Safe action")
        gl.message.sender_address.as_hex = self.owner
        self.court.set_paused(self.pid, True)
        gl.message.sender_address.as_hex = self.agent
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.execute(did_cleared, self.pid, category, self.recipient, asset, amount, calldata_hash)
        self.assertIn("clearance does not match this action", str(cm.exception))
        # restore unpaused
        gl.message.sender_address.as_hex = self.owner
        self.court.set_paused(self.pid, False)

    def test_vault_unexecuted_query_reverts(self):
        with self.assertRaises(gl.vm.UserError) as cm:
            self.vault.get_execution("nonexistent_decision")
        self.assertIn("execution not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
