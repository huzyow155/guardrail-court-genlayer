# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from genlayer import *


class GuardedVaultV2(gl.Contract):
    guardrail_court_address: Address
    executions: TreeMap[str, str]

    def __init__(self, guardrail_court_address_str: str):
        # Do not assign TreeMap() in __init__
        self.guardrail_court_address = Address(guardrail_court_address_str)

    @gl.public.write
    def execute(
        self,
        decision_id: str,
        policy_id: str,
        category: str,
        recipient: str,
        asset: str,
        amount: str,
        calldata_hash: str,
    ) -> str:
        did = str(decision_id).strip()

        # 1. Revert if already executed
        if did in self.executions:
            raise gl.vm.UserError("decision has already been executed")

        # 2. Cross-contract synchronous view query to GuardrailCourtV2
        court = gl.get_contract_at(self.guardrail_court_address)
        is_cleared = court.view().is_cleared_for(
            did,
            str(policy_id).strip(),
            str(category).strip(),
            str(recipient).strip(),
            str(asset).strip(),
            str(amount).strip(),
            str(calldata_hash).strip(),
        )
        if not is_cleared:
            raise gl.vm.UserError("clearance does not match this action")

        # 3. Mark executed and record execution record
        caller = gl.message.sender_address.as_hex.lower()
        exec_record = {
            "schema_version": "2",
            "decision_id": did,
            "recipient": str(recipient).strip().lower(),
            "asset": str(asset).strip(),
            "amount": str(amount).strip(),
            "calldata_hash": str(calldata_hash).strip().lower(),
            "caller": caller,
        }
        self.executions[did] = json.dumps(exec_record, sort_keys=True, separators=(",", ":"))

        return did

    @gl.public.view
    def get_execution(self, decision_id: str) -> str:
        did = str(decision_id).strip()
        if did not in self.executions:
            raise gl.vm.UserError("execution not found")
        return self.executions[did]

    @gl.public.view
    def is_executed(self, decision_id: str) -> bool:
        return str(decision_id).strip() in self.executions
