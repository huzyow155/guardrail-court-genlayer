# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from genlayer import *


class GuardedVault(gl.Contract):
    guardrail_court_address: Address
    executions: TreeMap[str, str]
    executed_decisions: TreeMap[str, str]
    meta: TreeMap[str, str]

    def __init__(self, guardrail_court_address_str: str):
        self.guardrail_court_address = Address(guardrail_court_address_str)
        self.meta["next_execution"] = "1"

    @gl.public.write
    def execute(self, decision_id: str, note: str) -> str:
        sender = gl.message.sender_address.as_hex.lower()
        did = str(decision_id).strip()

        # Check if already executed
        if did in self.executed_decisions:
            raise gl.vm.UserError("decision has already been executed")

        # Cross-contract synchronous view call to GuardrailCourt.is_cleared
        court = gl.get_contract_at(self.guardrail_court_address)
        is_cleared = court.view().is_cleared(did)
        if not is_cleared:
            raise gl.vm.UserError("action is not cleared by GuardrailCourt")

        exec_id = self.meta.get("next_execution", "1")
        self.meta["next_execution"] = str(int(exec_id) + 1)

        exec_record = {
            "schema_version": "1",
            "id": exec_id,
            "decision_id": did,
            "executor": sender,
            "note": str(note),
        }
        self.executions[exec_id] = json.dumps(exec_record, sort_keys=True, separators=(",", ":"))
        self.executed_decisions[did] = exec_id

        return exec_id

    @gl.public.view
    def list_executions(self, limit: int = 10) -> str:
        if limit <= 0:
            limit = 10
        if limit > 20:
            limit = 20

        count = int(self.meta.get("next_execution", "1")) - 1
        results = []
        for i in range(count, 0, -1):
            sid = str(i)
            if sid in self.executions:
                try:
                    results.append(json.loads(self.executions[sid]))
                except Exception:
                    pass
            if len(results) >= limit:
                break

        return json.dumps(results, sort_keys=True, separators=(",", ":"))
