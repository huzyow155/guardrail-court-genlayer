import dns from 'dns';
dns.setDefaultResultOrder('ipv4first');

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function verify() {
  const rpc = 'https://studio.genlayer.com/api';
  const deploymentsPath = path.join(__dirname, 'deployments_v2.json');
  const deployments = JSON.parse(fs.readFileSync(deploymentsPath, 'utf8'));
  
  const courtAddr = deployments.contracts.GuardrailCourtV2.address;
  const vaultAddr = deployments.contracts.GuardedVaultV2.address;

  async function getCode(addr) {
    const res = await fetch(rpc, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'gen_getContractCode', params: [addr], id: 1 })
    });
    const b64 = (await res.json()).result;
    return Buffer.from(b64, 'base64');
  }

  const courtOnChainBuf = await getCode(courtAddr);
  const vaultOnChainBuf = await getCode(vaultAddr);

  const courtLocalBuf = fs.readFileSync(path.join(__dirname, '../../contracts/GuardrailCourtV2.py'));
  const vaultLocalBuf = fs.readFileSync(path.join(__dirname, '../../examples/consumer/GuardedVaultV2.py'));

  const courtOnChainSha = crypto.createHash('sha256').update(courtOnChainBuf).digest('hex').toUpperCase();
  const courtLocalSha = crypto.createHash('sha256').update(courtLocalBuf).digest('hex').toUpperCase();

  const vaultOnChainSha = crypto.createHash('sha256').update(vaultOnChainBuf).digest('hex').toUpperCase();
  const vaultLocalSha = crypto.createHash('sha256').update(vaultLocalBuf).digest('hex').toUpperCase();

  // Save on-chain decoded files to evidence directory
  const evidenceDir = path.join(__dirname, '../../docs/evidence_v2');
  if (!fs.existsSync(evidenceDir)) {
    fs.mkdirSync(evidenceDir, { recursive: true });
  }
  fs.writeFileSync(path.join(evidenceDir, 'GuardrailCourtV2_onchain.py'), courtOnChainBuf);
  fs.writeFileSync(path.join(evidenceDir, 'GuardedVaultV2_onchain.py'), vaultOnChainBuf);

  console.log('=== GuardrailCourtV2 Byte Parity ===');
  console.log('Local length:   ', courtLocalBuf.length);
  console.log('OnChain length: ', courtOnChainBuf.length);
  console.log('Local SHA256:   ', courtLocalSha);
  console.log('OnChain SHA256: ', courtOnChainSha);
  console.log('Equal bytes:    ', courtLocalBuf.equals(courtOnChainBuf));
  console.log('First 16 bytes (hex):', courtOnChainBuf.subarray(0, 16).toString('hex'));
  console.log('First 16 bytes (raw):', JSON.stringify(courtOnChainBuf.subarray(0, 16).toString('utf8')));
  console.log('Last 16 bytes (hex): ', courtOnChainBuf.subarray(-16).toString('hex'));
  console.log('Last 16 bytes (raw): ', JSON.stringify(courtOnChainBuf.subarray(-16).toString('utf8')));

  console.log('\n=== GuardedVaultV2 Byte Parity ===');
  console.log('Local length:   ', vaultLocalBuf.length);
  console.log('OnChain length: ', vaultOnChainBuf.length);
  console.log('Local SHA256:   ', vaultLocalSha);
  console.log('OnChain SHA256: ', vaultOnChainSha);
  console.log('Equal bytes:    ', vaultLocalBuf.equals(vaultOnChainBuf));
  console.log('First 16 bytes (hex):', vaultOnChainBuf.subarray(0, 16).toString('hex'));
  console.log('First 16 bytes (raw):', JSON.stringify(vaultOnChainBuf.subarray(0, 16).toString('utf8')));
  console.log('Last 16 bytes (hex): ', vaultOnChainBuf.subarray(-16).toString('hex'));
  console.log('Last 16 bytes (raw): ', JSON.stringify(vaultOnChainBuf.subarray(-16).toString('utf8')));

  if (!courtLocalBuf.equals(courtOnChainBuf) || !vaultLocalBuf.equals(vaultOnChainBuf)) {
    throw new Error('On-chain bytecode/source does not match local files!');
  }
  console.log('\nByte-for-byte source verification SUCCESSFUL: Exact 1:1 match.');
}

verify().catch(err => {
  console.error('Verification error:', err);
  process.exit(1);
});
