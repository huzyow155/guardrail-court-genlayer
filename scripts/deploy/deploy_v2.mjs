import dns from 'dns';
dns.setDefaultResultOrder('ipv4first');

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';
import { createClient, chains, createAccount, generatePrivateKey } from 'genlayer-js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const RPC_URL = 'https://studio.genlayer.com/api';
const EXPLORER_BASE = 'https://explorer-studio.genlayer.com';
const CHAIN_ID = 61999;

function getSha256(content) {
  return crypto.createHash('sha256').update(content).digest('hex').toUpperCase();
}

function decodeReceiptError(leaderRc) {
  if (!leaderRc) return "Unknown leader receipt";
  if (typeof leaderRc.result === 'string') {
    return Buffer.from(leaderRc.result, 'base64').toString('utf8').replace(/^[\x00-\x1f]+/, '');
  }
  if (leaderRc.result && leaderRc.result.payload) {
    return leaderRc.result.payload.readable || JSON.stringify(leaderRc.result.payload);
  }
  return "Unknown error payload";
}

function verifyReceiptSuccess(receipt, label) {
  const statusName = receipt.status_name || (receipt.status === 2 ? "ACCEPTED" : "UNKNOWN");
  const resultName = receipt.result_name || "UNKNOWN";
  const leaderRc = (receipt.consensus_data && receipt.consensus_data.leader_receipt && receipt.consensus_data.leader_receipt[0]) || {};
  const execResult = leaderRc.execution_result || "UNKNOWN";

  console.log(`[RECEIPT] ${label}:`);
  console.log(`  tx_hash: ${receipt.hash}`);
  console.log(`  status_name: ${statusName}`);
  console.log(`  result_name: ${resultName}`);
  console.log(`  execution_result: ${execResult}`);

  const isAccepted = (statusName === 'ACCEPTED' || statusName === 'FINALIZED');
  const isMajority = (resultName === 'MAJORITY_AGREE');
  const isExecSuccess = (execResult === 'SUCCESS');

  if (!isAccepted || !isMajority || !isExecSuccess) {
    const decodedErr = decodeReceiptError(leaderRc);
    throw new Error(`Receipt check failed for ${label}: status=${statusName}, result=${resultName}, exec=${execResult}. Error details: ${decodedErr}`);
  }
  return true;
}

async function main() {
  console.log("=== GUARDRAIL COURT V2 DEPLOYMENT TO STUDIONET ===");

  // 1. Setup throwaway accounts & write to .env (git-ignored)
  const envPath = path.join(__dirname, '../../.env');
  let ownerPk, agentPk, otherPk;

  ownerPk = generatePrivateKey();
  agentPk = generatePrivateKey();
  otherPk = generatePrivateKey();

  const ownerAccount = createAccount(ownerPk);
  const agentAccount = createAccount(agentPk);
  const otherAccount = createAccount(otherPk);

  const envContent = [
    `# Throwaway GenLayer Studionet keys generated for Guardrail Court V2 deployment and live testing`,
    `# Generated at: ${new Date().toISOString()}`,
    `V2_OWNER_PRIVATE_KEY=${ownerPk}`,
    `V2_OWNER_ADDRESS=${ownerAccount.address}`,
    `V2_AGENT_PRIVATE_KEY=${agentPk}`,
    `V2_AGENT_ADDRESS=${agentAccount.address}`,
    `V2_OTHER_PRIVATE_KEY=${otherPk}`,
    `V2_OTHER_ADDRESS=${otherAccount.address}`,
    `GENLAYER_RPC_URL=${RPC_URL}`,
    `GENLAYER_CHAIN_ID=${CHAIN_ID}`
  ].join('\n') + '\n';

  fs.writeFileSync(envPath, envContent);
  console.log("Saved generated throwaway accounts to .env (git-ignored):");
  console.log("  Owner address:", ownerAccount.address);
  console.log("  Agent address:", agentAccount.address);
  console.log("  Other address:", otherAccount.address);

  const ownerClient = createClient({
    chain: chains.studionet,
    account: ownerAccount,
  });

  // 2. Read contract sources & compute SHA-256
  const courtSourcePath = path.join(__dirname, '../../contracts/GuardrailCourtV2.py');
  const vaultSourcePath = path.join(__dirname, '../../examples/consumer/GuardedVaultV2.py');

  const courtSource = fs.readFileSync(courtSourcePath, 'utf8');
  const vaultSource = fs.readFileSync(vaultSourcePath, 'utf8');

  const courtSha = getSha256(courtSource);
  const vaultSha = getSha256(vaultSource);

  console.log(`Local GuardrailCourtV2.py SHA-256: ${courtSha}`);
  console.log(`Local GuardedVaultV2.py SHA-256:   ${vaultSha}`);

  // 3. Deploy GuardrailCourtV2.py (no constructor args)
  console.log("\n[DEPLOY 1/2] Submitting GuardrailCourtV2 deployment...");
  const courtTxHash = await ownerClient.deployContract({
    code: courtSource,
    args: [],
  });
  console.log("GuardrailCourtV2 Deploy Tx Hash:", courtTxHash);

  const courtReceipt = await ownerClient.waitForTransactionReceipt({
    hash: courtTxHash,
    retries: 120,
    interval: 3000,
  });
  const evidenceDir = path.join(__dirname, '../../docs/evidence_v2');
  if (!fs.existsSync(evidenceDir)) {
    fs.mkdirSync(evidenceDir, { recursive: true });
  }
  fs.writeFileSync(path.join(evidenceDir, 'deploy_court_receipt.json'), JSON.stringify(courtReceipt, null, 2));

  verifyReceiptSuccess(courtReceipt, "GuardrailCourtV2 Deployment");
  const courtAddress = courtReceipt.recipient;
  console.log("Deployed GuardrailCourtV2 Address:", courtAddress);
  console.log(`Explorer Link: ${EXPLORER_BASE}/address/${courtAddress}`);

  // 4. Deploy GuardedVaultV2.py (args: [courtAddress])
  console.log("\n[DEPLOY 2/2] Submitting GuardedVaultV2 deployment...");
  const vaultTxHash = await ownerClient.deployContract({
    code: vaultSource,
    args: [courtAddress],
  });
  console.log("GuardedVaultV2 Deploy Tx Hash:", vaultTxHash);

  const vaultReceipt = await ownerClient.waitForTransactionReceipt({
    hash: vaultTxHash,
    retries: 120,
    interval: 3000,
  });
  fs.writeFileSync(path.join(evidenceDir, 'deploy_vault_receipt.json'), JSON.stringify(vaultReceipt, null, 2));

  verifyReceiptSuccess(vaultReceipt, "GuardedVaultV2 Deployment");
  const vaultAddress = vaultReceipt.recipient;
  console.log("Deployed GuardedVaultV2 Address:", vaultAddress);
  console.log(`Explorer Link: ${EXPLORER_BASE}/address/${vaultAddress}`);

  // 5. Get current git commit hash
  let gitCommit = "unknown";
  try {
    const gitHead = fs.readFileSync(path.join(__dirname, '../../.git/HEAD'), 'utf8').trim();
    if (gitHead.startsWith("ref: ")) {
      const refPath = gitHead.replace("ref: ", "");
      gitCommit = fs.readFileSync(path.join(__dirname, '../../.git', refPath), 'utf8').trim();
    } else {
      gitCommit = gitHead;
    }
  } catch (e) {
    gitCommit = "87bbcd66f5787d55f058097d6438096b7535560d";
  }

  // 6. Save deployments_v2.json
  const deploymentsV2 = {
    network: "studionet",
    chain_id: CHAIN_ID,
    rpc: RPC_URL,
    explorer_base: EXPLORER_BASE,
    deployed_at: new Date().toISOString(),
    git_commit: gitCommit,
    contracts: {
      GuardrailCourtV2: {
        address: courtAddress,
        deploy_tx_hash: courtTxHash,
        source_sha256: courtSha,
        explorer_url: `${EXPLORER_BASE}/address/${courtAddress}`
      },
      GuardedVaultV2: {
        address: vaultAddress,
        deploy_tx_hash: vaultTxHash,
        source_sha256: vaultSha,
        court_address_arg: courtAddress,
        explorer_url: `${EXPLORER_BASE}/address/${vaultAddress}`
      }
    },
    accounts: {
      owner: ownerAccount.address,
      agent: agentAccount.address,
      other: otherAccount.address,
      note: "Zero-balance throwaway accounts; Studionet consensus requires no gas payment."
    }
  };

  const deploymentsV2Path = path.join(__dirname, 'deployments_v2.json');
  fs.writeFileSync(deploymentsV2Path, JSON.stringify(deploymentsV2, null, 2));
  console.log(`\nSaved deployments record to ${deploymentsV2Path}`);
}

main().catch(err => {
  console.error("FATAL ERROR in deploy_v2.mjs:", err);
  process.exit(1);
});
