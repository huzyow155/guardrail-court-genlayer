import dns from 'dns';
dns.setDefaultResultOrder('ipv4first');

import fs from 'fs';
import path from 'path';
import assert from 'assert';
import { fileURLToPath } from 'url';
import { createClient, chains } from 'genlayer-js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  console.log("================================================================================");
  console.log("       STATISTICS RECAPTURE & INDEPENDENT RECOMPUTATION AUDIT                   ");
  console.log("================================================================================");

  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deploy/deployments_v2.json'), 'utf8'));
  const client = createClient({ chain: chains.studionet });
  const courtAddr = deployments.contracts.GuardrailCourtV2.address;

  const policies = ["1", "2", "3"];
  const finalStatsReport = {};

  for (const pid of policies) {
    console.log(`\n--- Auditing Policy ${pid} ---`);
    const rawStats = await client.readContract({
      address: courtAddr,
      functionName: 'get_policy_stats',
      args: [pid]
    });
    const contractStats = JSON.parse(rawStats);
    console.log(`Contract get_policy_stats("${pid}"):`, JSON.stringify(contractStats, null, 2));

    // Read all decisions for this policy
    const rawDecs = await client.readContract({
      address: courtAddr,
      functionName: 'list_decisions',
      args: [pid, 50]
    });
    const decisions = JSON.parse(rawDecs);
    console.log(`Retrieved ${decisions.length} stored decisions for Policy ${pid}.`);

    // Independent recomputation from individual decisions
    const recomputed = {
      policy_id: pid,
      schema_version: "2",
      total_decisions: decisions.length,
      cleared_count: 0,
      pending_owner_count: 0,
      verdicts: { ALLOW: 0, DENY: 0, ESCALATE: 0 },
      sources: {
        HARD_LIMIT: 0,
        RECIPIENT_GUARD: 0,
        ASSET_GUARD: 0,
        VELOCITY: 0,
        JUDGE: 0
      }
    };

    for (const d of decisions) {
      if (d.status === "CLEARED") recomputed.cleared_count++;
      if (d.status === "PENDING_OWNER") recomputed.pending_owner_count++;
      if (d.verdict in recomputed.verdicts) recomputed.verdicts[d.verdict]++;
      if (d.source in recomputed.sources) recomputed.sources[d.source]++;
    }

    console.log(`Independently Recomputed Stats for Policy ${pid}:`, JSON.stringify(recomputed, null, 2));

    // Assert exact equality
    assert.strictEqual(contractStats.total_decisions, recomputed.total_decisions, `Total decisions mismatch on policy ${pid}`);
    assert.strictEqual(contractStats.cleared_count, recomputed.cleared_count, `Cleared count mismatch on policy ${pid}`);
    assert.strictEqual(contractStats.pending_owner_count, recomputed.pending_owner_count, `Pending count mismatch on policy ${pid}`);
    assert.deepStrictEqual(contractStats.verdicts, recomputed.verdicts, `Verdicts mismatch on policy ${pid}`);
    assert.deepStrictEqual(contractStats.sources, recomputed.sources, `Sources mismatch on policy ${pid}`);

    console.log(`ASSERTION PASSED: Contract stats for Policy ${pid} EXACTLY match independent recomputation.`);
    finalStatsReport[`policy_${pid}`] = contractStats;
  }

  const evidenceDir = path.join(__dirname, '../docs/evidence_v2');
  fs.writeFileSync(path.join(evidenceDir, 'case_12_stats.json'), JSON.stringify(finalStatsReport, null, 2));
  console.log("\nSaved recaptured stats across policies 1, 2, and 3 to docs/evidence_v2/case_12_stats.json");
}

main().catch(err => {
  console.error("FATAL ERROR in verify_all_stats.mjs:", err);
  process.exit(1);
});
