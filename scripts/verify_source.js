const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

async function main() {
  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deploy/deployments.json'), 'utf8'));
  const deployTxHash = deployments.deployTxHash;
  const localContractPath = path.join(__dirname, '../contracts/GuardrailCourt.py');
  const localCode = fs.readFileSync(localContractPath, 'utf8');
  const localSha256 = crypto.createHash('sha256').update(localCode, 'utf8').digest('hex');

  const client = createClient({
    chain: chains.studionet,
    account: createAccount(),
  });

  console.log("Fetching deploy transaction receipt for:", deployTxHash);
  const receipt = await client.waitForTransactionReceipt({ hash: deployTxHash });
  
  console.log("Receipt status:", receipt.status_name);
  console.log("Recipient contract address:", receipt.recipient);
  console.log("Local code SHA-256:", localSha256);
  console.log("Registered deployments.json SHA-256:", deployments.sourceSha256);

  const matched = (deployments.sourceSha256 === localSha256);
  console.log("SHA-256 match verified:", matched);

  // Dump calldata envelope info
  if (receipt.data && receipt.data.calldata) {
    console.log("Receipt calldata readable:", receipt.data.calldata.readable);
  }
}

main().catch(err => {
  console.error("Verification error:", err);
  process.exit(1);
});
