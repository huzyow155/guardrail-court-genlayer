import dns from 'dns';
dns.setDefaultResultOrder('ipv4first');

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createClient, chains } from 'genlayer-js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deploy/deployments_v2.json'), 'utf8'));
  const client = createClient({ chain: chains.studionet });
  const courtAddr = deployments.contracts.GuardrailCourtV2.address;

  const rawDecs = await client.readContract({
    address: courtAddr,
    functionName: 'list_decisions',
    args: ['2', 20]
  });
  const decs = JSON.parse(rawDecs);
  console.log('Policy 2 decisions count:', decs.length);
  for (const d of decs) {
    console.log(`ID: ${d.id} | seq: ${d.seq} | amount: ${d.amount} | source: ${d.source} | verdict: ${d.verdict} | status: ${d.status} | resolved: ${d.resolved_by_owner} | justification: ${d.justification}`);
  }

  // Also query policy 2 stats
  const rawStats2 = await client.readContract({
    address: courtAddr,
    functionName: 'get_policy_stats',
    args: ['2']
  });
  console.log('\nPolicy 2 Stats:', rawStats2);
}

main().catch(console.error);
