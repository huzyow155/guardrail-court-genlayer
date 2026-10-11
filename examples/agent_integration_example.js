# Example: AI Agent Clearance Verification
# Shows how an autonomous agent or executor queries GuardrailCourt before executing an action.

const { createClient, chains, createAccount } = require('genlayer-js');

async function agentWorkflowExample() {
  const client = createClient({
    chain: chains.studionet,
    account: createAccount(), // or loaded agent wallet
  });

  const GUARDRAIL_COURT_ADDRESS = "0x6C553Ba27a768D71b570a106D9D2e13553b4103c";
  const POLICY_ID = "1";

  console.log("1. Agent requesting clearance for purchase...");
  const requestTx = await client.writeContract({
    address: GUARDRAIL_COURT_ADDRESS,
    functionName: 'request_action',
    args: [
      POLICY_ID,
      "dev_tools",
      "45",
      "Annual domain renewal for api.myservice.io via DNS registrar"
    ],
  });
  console.log("Action request tx submitted:", requestTx);

  const receipt = await client.waitForTransactionReceipt({
    hash: requestTx,
    retries: 120,
    interval: 3000,
  });
  console.log("Consensus status:", receipt.status_name, receipt.result_name);

  // Read latest decision ID
  const latestId = await client.readContract({
    address: GUARDRAIL_COURT_ADDRESS,
    functionName: 'latest_decision_id',
    args: [POLICY_ID],
  });
  console.log("Decision ID assigned:", latestId);

  // Check if cleared
  const isCleared = await client.readContract({
    address: GUARDRAIL_COURT_ADDRESS,
    functionName: 'is_cleared',
    args: [latestId],
  });
  console.log("is_cleared check:", isCleared);

  if (isCleared) {
    console.log("Action APPROVED: Proceeding with execution of task.");
  } else {
    const decision = JSON.parse(await client.readContract({
      address: GUARDRAIL_COURT_ADDRESS,
      functionName: 'get_decision',
      args: [latestId],
    }));
    console.log(`Action NOT cleared. Status: ${decision.status}, Verdict: ${decision.verdict}`);
  }
}

if (require.main === module) {
  agentWorkflowExample().catch(console.error);
}

module.exports = { agentWorkflowExample };
