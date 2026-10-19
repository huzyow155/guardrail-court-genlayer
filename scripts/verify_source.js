const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

async function main() {
  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deploy/deployments.json'), 'utf8'));
  const deployTxHash = deployments.deployTxHash;
  const localContractPath = path.join(__dirname, '../archive/v1/GuardrailCourt.py');
  const localCode = fs.readFileSync(localContractPath, 'utf8');
  const localSha256 = crypto.createHash('sha256').update(localCode, 'utf8').digest('hex');

  const client = createClient({
    chain: chains.studionet,
    account: createAccount(),
  });

  console.log("Fetching deploy transaction via RPC for:", deployTxHash);
  const tx = await client.getTransaction({ hash: deployTxHash });
  
  if (!tx || !tx.data || !tx.data.contract_code) {
    throw new Error("Deploy transaction does not contain contract_code in data field");
  }

  const rawBase64 = tx.data.contract_code;
  const chainBuffer = Buffer.from(rawBase64, 'base64');
  const chainSha256 = crypto.createHash('sha256').update(chainBuffer).digest('hex');

  console.log("Chain contract_code field format: base64 (length " + rawBase64.length + " chars)");
  console.log("Chain contract_code decoded byte length:", chainBuffer.length);
  console.log("First 16 bytes (hex):", chainBuffer.slice(0, 16).toString('hex'));
  console.log("Last 16 bytes (hex):", chainBuffer.slice(-16).toString('hex'));
  console.log("Chain decoded SHA-256:", chainSha256);
  console.log("Local code SHA-256:   ", localSha256);

  const matched = (chainSha256 === localSha256);
  console.log("Byte-for-byte SHA-256 match verified against on-chain code:", matched);

  // Write extracted file to disk for git diff comparison
  const extractedPath = path.join(__dirname, 'extracted_from_chain.py');
  fs.writeFileSync(extractedPath, chainBuffer);
  console.log("Saved extracted on-chain code to:", extractedPath);
}

main().catch(err => {
  console.error("Verification error:", err);
  process.exit(1);
});
