const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains } = require('genlayer-js');
const fs = require('fs');
const path = require('path');

async function main() {
  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deploy/deployments.json'), 'utf8'));
  const contractAddress = deployments.contractAddress;

  const client = createClient({
    chain: chains.studionet,
  });

  console.log("Reading live stats for contract:", contractAddress);
  const stats = JSON.parse(await client.readContract({
    address: contractAddress,
    functionName: 'get_policy_stats',
    args: ["1"],
  }));
  console.log("Live Policy 1 Stats:", stats);

  const pending = JSON.parse(await client.readContract({
    address: contractAddress,
    functionName: 'pending_escalations',
    args: ["1"],
  }));
  console.log(`Pending escalations: ${pending.length} item(s)`);
}

main().catch(console.error);
