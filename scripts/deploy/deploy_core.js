const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');
const path = require('path');

async function main() {
  const owner = createAccount();
  const agent = createAccount();
  console.log("Owner address:", owner.address);
  console.log("Agent address:", agent.address);

  const ownerClient = createClient({
    chain: chains.studionet,
    account: owner,
  });

  const agentClient = createClient({
    chain: chains.studionet,
    account: agent,
  });

  const codePath = path.join(__dirname, '../../contracts/GuardrailCourtCore.py');
  const code = fs.readFileSync(codePath, 'utf8');

  console.log("Deploying GuardrailCourtCore contract to Studionet...");
  const deployTxHash = await ownerClient.deployContract({
    code: code,
    args: [],
  });
  console.log("Deploy Transaction Hash:", deployTxHash);

  const receipt = await ownerClient.waitForTransactionReceipt({
    hash: deployTxHash,
    retries: 120,
    interval: 3000,
  });
  console.log("Deploy Receipt Status:", receipt.status_name);
  console.log("Deploy Receipt Result:", receipt.result_name);
  const contractAddress = receipt.recipient;
  console.log("Deployed Contract Address:", contractAddress);

  if (!contractAddress) {
    throw new Error("No contract address returned");
  }

  // 1. Owner creates a policy
  const policyText = "The agent may buy cloud credits, domain renewals and developer tools. It may not buy gift cards, tokens, gambling, adult content, or anything intended as a gift to an individual. If a purchase is ambiguous, escalate to the owner.";
  console.log("Owner creating policy...");
  const createPolicyTx = await ownerClient.writeContract({
    address: contractAddress,
    functionName: 'create_policy',
    args: [agent.address, policyText, "100", "400"],
  });
  console.log("Create policy Tx Hash:", createPolicyTx);

  const createPolicyReceipt = await ownerClient.waitForTransactionReceipt({
    hash: createPolicyTx,
    retries: 120,
    interval: 3000,
  });
  console.log("Create Policy Receipt Status:", createPolicyReceipt.status_name);
  console.log("Create Policy Receipt Result:", createPolicyReceipt.result_name);

  // Read policy 1
  const policy1 = await ownerClient.readContract({
    address: contractAddress,
    functionName: 'get_policy',
    args: ["1"],
  });
  console.log("Read back Policy 1:", policy1);

  // 2. Agent requests an action (clear ALLOW: domain renewal)
  console.log("Agent requesting action 1 (ALLOW - domain renewal)...");
  const startTime = Date.now();
  const reqActionTx = await agentClient.writeContract({
    address: contractAddress,
    functionName: 'request_action',
    args: ["1", "dev_tools", "45", "Annual domain renewal for api.myservice.io via DNS registrar"],
  });
  console.log("Request Action Tx Hash:", reqActionTx);

  const reqActionReceipt = await agentClient.waitForTransactionReceipt({
    hash: reqActionTx,
    retries: 120,
    interval: 3000,
  });
  const elapsed = (Date.now() - startTime) / 1000;
  console.log(`Action request took ${elapsed.toFixed(2)}s`);
  console.log("Request Action Receipt Status:", reqActionReceipt.status_name);
  console.log("Request Action Receipt Result:", reqActionReceipt.result_name);

  // 3. Read back decision 1 and is_cleared
  const decision1 = await ownerClient.readContract({
    address: contractAddress,
    functionName: 'get_decision',
    args: ["1"],
  });
  console.log("Read back Decision 1:", decision1);

  const isCleared1 = await ownerClient.readContract({
    address: contractAddress,
    functionName: 'is_cleared',
    args: ["1"],
  });
  console.log("is_cleared('1') ->", isCleared1);

  const coreOutput = {
    owner: owner.address,
    agent: agent.address,
    contractAddress: contractAddress,
    deployTxHash: deployTxHash,
    deployReceipt: receipt,
    createPolicyTx: createPolicyTx,
    createPolicyReceipt: createPolicyReceipt,
    reqActionTx: reqActionTx,
    reqActionReceipt: reqActionReceipt,
    actionLatencySec: elapsed,
    policy1: JSON.parse(policy1),
    decision1: JSON.parse(decision1),
    isCleared: isCleared1,
  };

  fs.writeFileSync(
    path.join(__dirname, 'core_output.json'),
    JSON.stringify(coreOutput, null, 2)
  );
  console.log("Milestone 1 Core successfully deployed and verified! Saved to core_output.json");
}

main().catch(err => {
  console.error("Core deployment error:", err);
  process.exit(1);
});
