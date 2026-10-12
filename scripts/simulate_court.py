# Interactive Terminal Simulation Demo
# Runs a step-by-step local simulator of GuardrailCourt showcasing policy setup,
# normal clears, hard-limit denials, velocity limit trips, and owner inbox escalation.

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'contracts')))

from guardrail_helpers import parse_model_verdict, velocity_guard


def run_demo():
    print("=" * 70)
    print("GUARDRAIL COURT: POLICY GATE INTERACTIVE SIMULATION")
    print("=" * 70)

    policy = {
        "id": "1",
        "owner": "0x1111111111111111111111111111111111111111",
        "agent": "0x2222222222222222222222222222222222222222",
        "text": "The agent may buy cloud credits, domain renewals and developer tools. It may not buy gift cards or gambling.",
        "max_amount": 100,
        "window_cap": 400,
    }
    print(f"\n[1] Registered Policy 1:")
    print(f"    Owner: {policy['owner']}")
    print(f"    Agent: {policy['agent']}")
    print(f"    Velocity Cap (10 most recent same-category decisions): {policy['window_cap']}")
    print(f"    Policy Text: {policy['text']}")

    history = []

    def evaluate_request(category, amount, desc):
        print(f"\n---> Agent Requests Action: [{category}] Amount: {amount}")
        print(f"     Description: '{desc}'")
        
        # Hard limit
        if amount > policy['max_amount']:
            print("     [EVALUATION] Exceeds max per-action cap! Short-circuiting.")
            return {"verdict": "DENY", "source": "HARD_LIMIT", "status": "DENIED"}
        
        # Velocity
        vel = velocity_guard(history, category, amount, policy['window_cap'])
        if vel == "ESCALATE":
            print("     [EVALUATION] Trips category velocity cap! Escalating to owner.")
            return {"verdict": "ESCALATE", "source": "VELOCITY", "status": "PENDING_OWNER"}

        # Model Judge simulation
        print("     [EVALUATION] Within numeric caps. Multi-validator consensus running...")
        if "gift" in desc.lower() or "gambling" in desc.lower():
            v = "DENY"
        elif "meetup" in desc.lower() or "sponsor" in desc.lower():
            v = "ESCALATE"
        else:
            v = "ALLOW"

        st = "CLEARED" if v == "ALLOW" else ("DENIED" if v == "DENY" else "PENDING_OWNER")
        return {"verdict": v, "source": "JUDGE", "status": st}

    test_actions = [
        ("dev_tools", 45, "Annual domain renewal for api.myservice.io"),
        ("gifts", 50, "Amazon gift card for contractor"),
        ("infrastructure", 150, "GPU server upgrade (exceeds 100)"),
        ("research", 75, "Developer conference sponsorship ticket with lunch"),
    ]

    for cat, amt, desc in test_actions:
        res = evaluate_request(cat, amt, desc)
        print(f"     => Verdict: {res['verdict']} | Source: {res['source']} | Status: {res['status']}")
        history.insert(0, {"category": cat, "amount": str(amt), **res})

    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    run_demo()
