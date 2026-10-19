// Example: AI Agent Clearance Verification
// Shows how an unattended agent or executor submits a request to GuardrailCourt,
// validates the 3-condition consensus receipt, retrieves the decision record via
// list_decisions (avoiding racy blind reliance on latest_decision_id), and checks is_cleared.

const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');

const GUARDRAIL_COURT_ADDRESS = '0x6C553Ba27a768D71b570a106D9D2e13553b4103c';

function isReceiptSuccessful(receipt) {
  const statusOk =
    receipt.status_name === 'ACCEPTED' || receipt.status_name === 'FINALIZED';
  const resultOk = receipt.result_name === 'MAJORITY_AGREE';
  const leaderOk =
    receipt.consensus_data?.leader_receipt?.[0]?.execution_result === 'SUCCESS';
  return Boolean(statusOk && resultOk && leaderOk);
}

async function agentWorkflowExample({ dryRunReadOnly = false } = {}) {
  const ownerAccount = createAccount();
  const agentAccount = createAccount();

  const ownerClient = createClient({
    chain: chains.studionet,
    account: ownerAccount,
  });

  const agentClient = createClient({
    chain: chains.studionet,
    account: agentAccount,
  });

  if (dryRunReadOnly) {
    console.log('=== DRY-RUN READ VERIFICATION AGAINST STUDIONET ===');
    const decisionsJson = await agentClient.readContract({
      address: GUARDRAIL_COURT_ADDRESS,
      functionName: 'list_decisions',
      args: ['1', 5],
    });
    const decisions = JSON.parse(decisionsJson);
    const targetDecision = decisions.find((d) => d.id === '1') || decisions[0];
    console.log('Fetched Decision from list_decisions("1", 5):', targetDecision);

    const cleared = await agentClient.readContract({
      address: GUARDRAIL_COURT_ADDRESS,
      functionName: 'is_cleared',
      args: [targetDecision.id],
    });
    console.log(`is_cleared("${targetDecision.id}"):`, cleared);
    return { targetDecision, cleared };
  }

  console.log('1. Owner creating a dedicated policy for agent...');
  const createTx = await ownerClient.writeContract({
    address: GUARDRAIL_COURT_ADDRESS,
    functionName: 'create_policy',
    args: [
      agentAccount.address,
      'The agent may purchase developer tools and cloud renewals up to 100. No gifts.',
      '100',
      '400',
    ],
  });
  const createReceipt = await ownerClient.waitForTransactionReceipt({
    hash: createTx,
    retries: 60,
    interval: 3000,
  });
  if (!isReceiptSuccessful(createReceipt)) {
    throw new Error('Policy creation failed 3-condition receipt check');
  }

  const policies = JSON.parse(
    await ownerClient.readContract({
      address: GUARDRAIL_COURT_ADDRESS,
      functionName: 'list_policies_by_owner',
      args: [ownerAccount.address, 5],
    })
  );
  const policyId = policies[0].id;
  console.log('Created Policy ID:', policyId);

  // (a) Call request_action
  const actionCategory = 'dev_tools';
  const actionAmount = '45';
  const actionDesc = 'Annual domain renewal for api.myservice.io via DNS registrar';
  console.log('2. Agent calling request_action...');
  const requestTx = await agentClient.writeContract({
    address: GUARDRAIL_COURT_ADDRESS,
    functionName: 'request_action',
    args: [policyId, actionCategory, actionAmount, actionDesc],
  });
  console.log('request_action tx hash:', requestTx);

  // (b) Validate receipt using the strict 3-condition rule
  const receipt = await agentClient.waitForTransactionReceipt({
    hash: requestTx,
    retries: 120,
    interval: 3000,
  });
  console.log(
    'Receipt 3-condition check:',
    {
      status_name: receipt.status_name,
      result_name: receipt.result_name,
      execution_result: receipt.consensus_data?.leader_receipt?.[0]?.execution_result,
      passed: isReceiptSuccessful(receipt),
    }
  );
  if (!isReceiptSuccessful(receipt)) {
    throw new Error('request_action transaction did not satisfy 3-condition receipt rule');
  }

  // (c) Retrieve decision ID from list_decisions by matching request fields
  // (Note: latest_decision_id can be racy if multiple requests are submitted concurrently under the same policy)
  const recentDecisions = JSON.parse(
    await agentClient.readContract({
      address: GUARDRAIL_COURT_ADDRESS,
      functionName: 'list_decisions',
      args: [policyId, 10],
    })
  );
  const matchedDecision = recentDecisions.find(
    (d) =>
      d.category === actionCategory &&
      d.amount === actionAmount &&
      d.description === actionDesc
  );
  if (!matchedDecision) {
    throw new Error('Could not locate matching decision in list_decisions');
  }
  const decisionId = matchedDecision.id;
  console.log('Matched Decision ID from list_decisions:', decisionId, matchedDecision);

  // (d) Call is_cleared(decisionId) AND verify decision fields match the action before executing
  const isCleared = await agentClient.readContract({
    address: GUARDRAIL_COURT_ADDRESS,
    functionName: 'is_cleared',
    args: [decisionId],
  });
  console.log(`is_cleared("${decisionId}"):`, isCleared);

  if (isCleared && matchedDecision.status === 'CLEARED') {
    console.log('Action CLEARED: Executor verified decision parameters and may proceed.');
  } else {
    console.log(
      `Action NOT cleared. Status: ${matchedDecision.status}, Verdict: ${matchedDecision.verdict}`
    );
  }
}

if (require.main === module) {
  const dryRun = process.argv.includes('--dry-run');
  agentWorkflowExample({ dryRunReadOnly: dryRun }).catch((err) => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { agentWorkflowExample, isReceiptSuccessful };
