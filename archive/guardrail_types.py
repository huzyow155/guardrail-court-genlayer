# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# Guardrail Court Types Specification
#
# Schemas:
#
# PolicyRecord:
# {
#   "schema_version": "1",
#   "id": str,
#   "owner": str (0x hex lower),
#   "agent": str (0x hex lower),
#   "text": str (30-1200 chars),
#   "policy_sha": str (sha256 hex),
#   "max_amount": str (integer digits),
#   "window_cap": str (integer digits),
#   "paused": bool,
#   "seq": str (counter)
# }
#
# DecisionRecord:
# {
#   "schema_version": "1",
#   "id": str,
#   "policy_id": str,
#   "seq": str,
#   "category": str,
#   "amount": str,
#   "description": str,
#   "verdict": "ALLOW" | "DENY" | "ESCALATE",
#   "source": "HARD_LIMIT" | "VELOCITY" | "JUDGE",
#   "status": "CLEARED" | "DENIED" | "PENDING_OWNER",
#   "resolved_by_owner": bool
# }

SCHEMA_VERSION = "1"
