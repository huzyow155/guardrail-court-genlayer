import dns from 'dns';
dns.setDefaultResultOrder('ipv4first');

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';
import { createClient, chains, createAccount } from 'genlayer-js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const R1 = "0x1111111111111111111111111111111111111111";

function parseEnv(envPath) {
  const content = fs.readFileSync(envPath, 'utf8');
  const env = {};
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx !== -1) {
      env[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
    }
  }
  return env;
}

function extractLeaderError(receipt) {
  try {
    const leaderRc = (receipt.consensus_data && receipt.consensus_data.leader_receipt && receipt.consensus_data.leader_receipt[0]) || {};
    if (typeof leaderRc.result === 'string') {
      return Buffer.from(leaderRc.result, 'base64').toString('utf8').replace(/^[\x00-\x1f]+/, '');
    }
    if (leaderRc.result && leaderRc.result.payload) {
      return leaderRc.result.payload.readable || JSON.stringify(leaderRc.result.payload);
    }
    if (leaderRc.result) {
      return JSON.stringify(leaderRc.result);
    }
    return "Unknown error";
  } catch (e) {
    return `Error extracting error: ${e.message}`;
  }
}

function formatReceiptSummary(rc) {
  const leaderRc = (rc.consensus_data && rc.consensus_data.leader_receipt && rc.consensus_data.leader_receipt[0]) || {};
  return {
    tx_hash: rc.hash,
    status_name: rc.status_name || (rc.status === 2 ? 'ACCEPTED' : 'UNKNOWN'),
    result_name: rc.result_name || 'UNKNOWN',
    execution_result: leaderRc.execution_result || 'UNKNOWN',
    error: leaderRc.execution_result === 'ERROR' ? extractLeaderError(rc) : null,
  };
}

async function main() {
  console.log("================================================================================");
  console.log("       CASE 4b — LIVE VELOCITY GUARD VERIFICATION ON STUDIONET                  ");
  console.log("================================================================================");

  const env = parseEnv(path.join(__dirname, '../../.env'));
  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deployments_v2.json'), 'utf8'));

  const ownerAccount = createAccount(env.V2_OWNER_PRIVATE_KEY);
  const agentAccount = createAccount(env.V2_AGENT_PRIVATE_KEY);

  const courtAddress = deployments.contracts.GuardrailCourtV2.address;

  const ownerClient = createClient({ chain: chains.studionet, account: ownerAccount });
  const agentClient = createClient({ chain: chains.studionet, account: agentAccount });

  const evidenceDir = path.join(__dirname, '../../docs/evidence_v2');
  const allReceiptsPath = path.join(evidenceDir, 'all_receipts.json');
  const allReceipts = fs.existsSync(allReceiptsPath) ? JSON.parse(fs.readFileSync(allReceiptsPath, 'utf8')) : {};

  async function executeWrite(client, label, params, category = 'judged') {
    const t0 = performance.now();
    console.log(`\n[TX] Submitting: ${label}...`);
    const txHash = await client.writeContract(params);
    console.log(`     Tx Hash: ${txHash}`);
    const receipt = await client.waitForTransactionReceipt({
      hash: txHash,
      retries: 120,
      interval: 3000,
    });
    const durSec = (performance.now() - t0) / 1000;
    const summary = formatReceiptSummary(receipt);
    console.log(`     Completed in ${durSec.toFixed(2)}s | Status: ${summary.status_name} | Result: ${summary.result_name} | Exec: ${summary.execution_result}${summary.error ? ' | Msg: ' + summary.error : ''}`);
    allReceipts[txHash] = receipt;
    return { txHash, receipt, durSec, summary };
  }

  // 1. Policy 3 Creation
  console.log("\n--- STEP 1: CREATE POLICY 3 ---");
  const p3Text = "Agent may only pay for server maintenance. Maximum 60 USDC per payment.";
  const p3CreateRes = await executeWrite(ownerClient, "Create Policy 3 (cap 60, window 100)", {
    address: courtAddress,
    functionName: 'create_policy',
    args: [
      agentAccount.address,
      p3Text,
      "60",
      "100",
      JSON.stringify([R1]),
      JSON.stringify(["USDC"]),
    ],
  }, 'admin_writes');

  const p3Id = "3";
  const p3Raw = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'get_policy',
    args: [p3Id],
  });
  console.log("Policy 3 state:", p3Raw);

  // 2. Request 60 USDC (up to 3 tries until CLEARED)
  console.log("\n--- STEP 2: REQUEST 60 USDC (AIMING FOR JUDGE CLEARED) ---");
  let clearedTry = null;
  const tries = [];

  for (let tryNum = 1; tryNum <= 3; tryNum++) {
    const freshCalldata = crypto.randomBytes(32).toString('hex');
    console.log(`\nTry ${tryNum}/3: Submitting 60 USDC (calldata: ${freshCalldata.slice(0, 16)}...)...`);
    const writeRes = await executeWrite(agentClient, `Policy 3 Try ${tryNum} 60 USDC`, {
      address: courtAddress,
      functionName: 'request_action',
      args: [p3Id, "server_ops", R1, "USDC", "60", freshCalldata, "monthly server hosting invoice"],
    }, 'judged');

    const latestId = await ownerClient.readContract({
      address: courtAddress,
      functionName: 'latest_decision_id',
      args: [p3Id],
    });
    const decRaw = await ownerClient.readContract({
      address: courtAddress,
      functionName: 'get_decision',
      args: [latestId],
    });
    const dec = JSON.parse(decRaw);
    console.log(`Try ${tryNum} Result: Decision ID ${latestId} | verdict: ${dec.verdict} | status: ${dec.status} | source: ${dec.source}`);
    tries.push({
      try_num: tryNum,
      tx: writeRes.summary,
      durSec: writeRes.durSec,
      decision: dec,
    });

    if (dec.status === "CLEARED" && dec.verdict === "ALLOW") {
      clearedTry = { tryNum, decisionId: latestId, decision: dec, calldata: freshCalldata, tx: writeRes };
      console.log(`SUCCESS: Try ${tryNum} was CLEARED by JUDGE!`);
      break;
    }
  }

  const case04bData = {
    policy_3_creation: p3CreateRes.summary,
    step2_tries: tries,
    velocity_proven_live: false,
  };

  if (!clearedTry) {
    console.log("\n[WARNING] None of the 3 tries was CLEARED by JUDGE. Stopping Case 4b per prompt instructions.");
    fs.writeFileSync(path.join(evidenceDir, 'case_04b_velocity_live.json'), JSON.stringify(case04bData, null, 2));
    fs.writeFileSync(allReceiptsPath, JSON.stringify(allReceipts, null, 2));
    return;
  }

  // 3. Step 3: Request 60 again (60 + 60 = 120 > 100 -> MUST TRIP VELOCITY)
  console.log("\n--- STEP 3: SUBMIT 60 USDC TO TRIP VELOCITY (60 + 60 = 120 > 100) ---");
  const calldataTrip = crypto.randomBytes(32).toString('hex');
  const tripRes = await executeWrite(agentClient, "Policy 3 Velocity Trip Action (60 USDC)", {
    address: courtAddress,
    functionName: 'request_action',
    args: [p3Id, "server_ops", R1, "USDC", "60", calldataTrip, "monthly server hosting invoice slice 2"],
  }, 'guard_only');

  const tripId = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'latest_decision_id',
    args: [p3Id],
  });
  const tripDecRaw = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'get_decision',
    args: [tripId],
  });
  const tripDec = JSON.parse(tripDecRaw);
  console.log(`Velocity Trip Result: Decision ID ${tripId} | verdict: ${tripDec.verdict} | status: ${tripDec.status} | source: ${tripDec.source} | latency: ${tripRes.durSec.toFixed(2)}s`);

  // Verify is_cleared_for is false
  const tripClearedBefore = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'is_cleared_for',
    args: [tripId, p3Id, "server_ops", R1, "USDC", "60", calldataTrip],
  });
  console.log(`is_cleared_for before resolve: ${tripClearedBefore} (expected: false)`);

  // 4. Step 4: Show DENIED does not count toward sum
  console.log("\n--- STEP 4: SHOW DENIED DOES NOT COUNT TOWARD SUM ---");
  // 4a. Request 61 (HARD_LIMIT denied)
  const calldata61 = crypto.randomBytes(32).toString('hex');
  const hlRes = await executeWrite(agentClient, "Policy 3 Hard Limit Request (61 USDC)", {
    address: courtAddress,
    functionName: 'request_action',
    args: [p3Id, "server_ops", R1, "USDC", "61", calldata61, "Over limit server maintenance"],
  }, 'guard_only');

  const hlId = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'latest_decision_id',
    args: [p3Id],
  });
  const hlDec = JSON.parse(await ownerClient.readContract({ address: courtAddress, functionName: 'get_decision', args: [hlId] }));
  console.log(`Hard Limit Result: Decision ID ${hlId} | verdict: ${hlDec.verdict} | status: ${hlDec.status} | source: ${hlDec.source}`);

  // 4b. Request 40 USDC (60 cleared + 40 = 100 <= 100 window cap) -> Goes to JUDGE!
  console.log("\nSubmitting 40 USDC request (60 cleared + 40 = 100 <= 100 cap -> not blocked by velocity)...");
  const calldata40 = crypto.randomBytes(32).toString('hex');
  const req40Res = await executeWrite(agentClient, "Policy 3 40 USDC Request (within window cap)", {
    address: courtAddress,
    functionName: 'request_action',
    args: [p3Id, "server_ops", R1, "USDC", "40", calldata40, "monthly server hosting invoice part 2"],
  }, 'judged');

  const req40Id = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'latest_decision_id',
    args: [p3Id],
  });
  const req40Dec = JSON.parse(await ownerClient.readContract({ address: courtAddress, functionName: 'get_decision', args: [req40Id] }));
  console.log(`40 USDC Request Result: Decision ID ${req40Id} | verdict: ${req40Dec.verdict} | status: ${req40Dec.status} | source: ${req40Dec.source} (NOT VELOCITY)`);

  // 5. Owner resolves the velocity trip decision (ALLOW)
  console.log("\n--- STEP 5: OWNER RESOLVES VELOCITY TRIP DECISION TO ALLOW ---");
  const resolveTripRes = await executeWrite(ownerClient, `Resolve Decision ${tripId} to ALLOW`, {
    address: courtAddress,
    functionName: 'resolve_escalation',
    args: [tripId, "ALLOW"],
  }, 'admin_writes');

  const tripDecPostRaw = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'get_decision',
    args: [tripId],
  });
  const tripDecPost = JSON.parse(tripDecPostRaw);
  console.log(`Resolved Decision ${tripId}: status: ${tripDecPost.status} | resolved_by_owner: ${tripDecPost.resolved_by_owner}`);

  const tripClearedAfter = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'is_cleared_for',
    args: [tripId, p3Id, "server_ops", R1, "USDC", "60", calldataTrip],
  });
  console.log(`is_cleared_for after resolve: ${tripClearedAfter} (expected: true)`);

  // Query final policy 3 stats
  const p3StatsRaw = await ownerClient.readContract({
    address: courtAddress,
    functionName: 'get_policy_stats',
    args: [p3Id],
  });
  const p3Stats = JSON.parse(p3StatsRaw);
  console.log("\nPolicy 3 Final Stats:", JSON.stringify(p3Stats, null, 2));

  case04bData.velocity_proven_live = (tripDec.source === "VELOCITY" && tripDec.status === "PENDING_OWNER");
  case04bData.step3_velocity_trip = {
    tx: tripRes.summary,
    durSec: tripRes.durSec,
    decision: tripDec,
    is_cleared_for_before: tripClearedBefore,
  };
  case04bData.step4_denied_check = {
    hard_limit: { tx: hlRes.summary, durSec: hlRes.durSec, decision: hlDec },
    within_cap_40: { tx: req40Res.summary, durSec: req40Res.durSec, decision: req40Dec },
  };
  case04bData.step5_owner_resolve = {
    tx: resolveTripRes.summary,
    durSec: resolveTripRes.durSec,
    decision_post: tripDecPost,
    is_cleared_for_after: tripClearedAfter,
  };
  case04bData.policy_3_final_stats = p3Stats;

  fs.writeFileSync(path.join(evidenceDir, 'case_04b_velocity_live.json'), JSON.stringify(case04bData, null, 2));
  fs.writeFileSync(allReceiptsPath, JSON.stringify(allReceipts, null, 2));
  console.log("\nSaved raw evidence to docs/evidence_v2/case_04b_velocity_live.json");
}

main().catch(err => {
  console.error("FATAL ERROR in run_case_04b.mjs:", err);
  process.exit(1);
});
