const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains } = require('genlayer-js');
const fs = require('fs');
const path = require('path');

async function main() {
  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deployments.json'), 'utf8'));
  const contractAddress = deployments.contractAddress;

  const client = createClient({
    chain: chains.studionet,
  });

  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] Fetching fresh state from GenLayer Studionet RPC for contract ${contractAddress}...`);

  const rawPolicy1 = await client.readContract({
    address: contractAddress,
    functionName: 'get_policy',
    args: ["1"],
  });

  const rawPolicy2 = await client.readContract({
    address: contractAddress,
    functionName: 'get_policy',
    args: ["2"],
  });

  const rawDecision1 = await client.readContract({
    address: contractAddress,
    functionName: 'get_decision',
    args: ["1"],
  });

  const rawDecision3 = await client.readContract({
    address: contractAddress,
    functionName: 'get_decision',
    args: ["3"],
  });

  const rawDecision9 = await client.readContract({
    address: contractAddress,
    functionName: 'get_decision',
    args: ["9"],
  });

  const rawDecision10 = await client.readContract({
    address: contractAddress,
    functionName: 'get_decision',
    args: ["10"],
  });

  const rawPolicyStats1 = await client.readContract({
    address: contractAddress,
    functionName: 'get_policy_stats',
    args: ["1"],
  });

  const stateData = {
    fetched_at: timestamp,
    contract_address: contractAddress,
    rpc_url: "https://studio.genlayer.com/api",
    get_policy_1: typeof rawPolicy1 === 'string' ? JSON.parse(rawPolicy1) : rawPolicy1,
    get_policy_2: typeof rawPolicy2 === 'string' ? JSON.parse(rawPolicy2) : rawPolicy2,
    get_decision_1: typeof rawDecision1 === 'string' ? JSON.parse(rawDecision1) : rawDecision1,
    get_decision_3: typeof rawDecision3 === 'string' ? JSON.parse(rawDecision3) : rawDecision3,
    get_decision_9: typeof rawDecision9 === 'string' ? JSON.parse(rawDecision9) : rawDecision9,
    get_decision_10: typeof rawDecision10 === 'string' ? JSON.parse(rawDecision10) : rawDecision10,
    get_policy_stats_1: typeof rawPolicyStats1 === 'string' ? JSON.parse(rawPolicyStats1) : rawPolicyStats1,
  };

  fs.writeFileSync(path.join(__dirname, 'state_fresh.json'), JSON.stringify(stateData, null, 2));

  console.log("--- get_policy(1) ---");
  console.log(JSON.stringify(stateData.get_policy_1, null, 2));
  console.log("--- get_policy(2) ---");
  console.log(JSON.stringify(stateData.get_policy_2, null, 2));
  console.log("--- get_decision(1) ---");
  console.log(JSON.stringify(stateData.get_decision_1, null, 2));
  console.log("--- get_decision(3) ---");
  console.log(JSON.stringify(stateData.get_decision_3, null, 2));
  console.log("--- get_decision(9) ---");
  console.log(JSON.stringify(stateData.get_decision_9, null, 2));
  console.log("--- get_decision(10) ---");
  console.log(JSON.stringify(stateData.get_decision_10, null, 2));
  console.log("--- get_policy_stats(1) ---");
  console.log(JSON.stringify(stateData.get_policy_stats_1, null, 2));

  console.log("\n[OK] State fetched and saved to scripts/deploy/state_fresh.json");
}

main().catch(err => {
  console.error("Error fetching state:", err);
  process.exit(1);
});
