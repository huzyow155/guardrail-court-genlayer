import dns from 'dns';
dns.setDefaultResultOrder('ipv4first');

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const rpc = 'https://studio.genlayer.com/api';
  const deploymentsPath = path.join(__dirname, 'deploy/deployments_v2.json');
  const deployments = JSON.parse(fs.readFileSync(deploymentsPath, 'utf8'));

  const targets = [
    {
      name: 'GuardrailCourtV2',
      address: deployments.contracts.GuardrailCourtV2.address,
      txHash: deployments.contracts.GuardrailCourtV2.deploy_tx_hash,
      localFile: path.join(__dirname, '../contracts/GuardrailCourtV2.py'),
      extractedFile: path.join(__dirname, '../docs/evidence_v2/extracted_court_round2.py'),
    },
    {
      name: 'GuardedVaultV2',
      address: deployments.contracts.GuardedVaultV2.address,
      txHash: deployments.contracts.GuardedVaultV2.deploy_tx_hash,
      localFile: path.join(__dirname, '../examples/consumer/GuardedVaultV2.py'),
      extractedFile: path.join(__dirname, '../docs/evidence_v2/extracted_vault_round2.py'),
    }
  ];

  let outputLog = [];
  function log(msg = '') {
    console.log(msg);
    outputLog.push(msg);
  }

  log('======================================================================');
  log('GUARDRAIL COURT V2: FRESH SOURCE VERIFICATION (ROUND 2)');
  log(`Timestamp: ${new Date().toISOString()}`);
  log(`Network: Studionet (RPC: ${rpc})`);
  log('======================================================================\n');

  for (const t of targets) {
    log(`--- Verifying ${t.name} ---`);
    log(`Contract Address: ${t.address}`);
    log(`Deploy Tx Hash:   ${t.txHash}`);

    // 1. Fetch deploy transaction from RPC
    const res = await fetch(rpc, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'eth_getTransactionByHash',
        params: [t.txHash],
        id: 1
      })
    });
    const resJson = await res.json();
    if (!resJson.result || !resJson.result.data || !resJson.result.data.contract_code) {
      throw new Error(`Failed to retrieve contract_code from deploy tx ${t.txHash}`);
    }

    // 2. Decode deploy tx payload
    const rawB64 = resJson.result.data.contract_code;
    const chainBuf = Buffer.from(rawB64, 'base64');
    const localBuf = fs.readFileSync(t.localFile);

    const chainSha = crypto.createHash('sha256').update(chainBuf).digest('hex').toUpperCase();
    const localSha = crypto.createHash('sha256').update(localBuf).digest('hex').toUpperCase();

    // 3. First and last 16 bytes
    const first16Hex = chainBuf.subarray(0, 16).toString('hex');
    const first16Raw = JSON.stringify(chainBuf.subarray(0, 16).toString('utf8'));
    const last16Hex = chainBuf.subarray(-16).toString('hex');
    const last16Raw = JSON.stringify(chainBuf.subarray(-16).toString('utf8'));

    log(`Payload Length:   ${chainBuf.length} bytes (Local: ${localBuf.length} bytes)`);
    log(`First 16 bytes (hex): ${first16Hex}`);
    log(`First 16 bytes (raw): ${first16Raw}`);
    log(`Last 16 bytes (hex):  ${last16Hex}`);
    log(`Last 16 bytes (raw):  ${last16Raw}`);
    log(`On-Chain SHA-256: ${chainSha}`);
    log(`Local SHA-256:    ${localSha}`);

    // 4. Write extracted source to disk
    fs.writeFileSync(t.extractedFile, chainBuf);
    log(`Wrote extracted on-chain source to: ${path.relative(path.join(__dirname, '../..'), t.extractedFile)}`);

    // 5. Diff check
    const isExact = chainBuf.equals(localBuf);
    log(`Byte-for-byte exact equality: ${isExact}`);
    if (!isExact) {
      log(`DIFFERENCE DETECTED between on-chain payload and ${t.localFile}`);
      throw new Error(`Diff detected on ${t.name}`);
    } else {
      log(`Diff output against ${path.relative(path.join(__dirname, '../..'), t.localFile)}: [EMPTY DIFF - 0 bytes difference]\n`);
    }
  }

  log('======================================================================');
  log('FINAL VERIFICATION RESULT: Byte-for-byte 1:1 match for all V2 contracts.');
  log('Local repository source matches deployed on-chain source byte for byte.');
  log('======================================================================');

  // Save to docs/evidence_v2/source_verification_round2.txt
  const outPath = path.join(__dirname, '../docs/evidence_v2/source_verification_round2.txt');
  fs.writeFileSync(outPath, outputLog.join('\n') + '\n', 'utf8');
  console.log(`Saved verification report to: ${outPath}`);
}

main().catch(err => {
  console.error('Source verification failed:', err);
  process.exit(1);
});
