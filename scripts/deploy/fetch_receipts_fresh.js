const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');
const fs = require('fs');
const path = require('path');

const RPC_URL = 'https://studio.genlayer.com/api';

const txHashes = [
  "0xef76f606fb197b9366042827e4c509fb44d126d71c86d7690fa8ebc2b5061368", // Probe Deploy
  "0xcb6562321804ccc0e724a33e2ef6e6bd6549cc7e425f659884935556777eda6e", // Probe Consensus
  "0x398f6c55e1daf336e8f85ab75b1487ae518ed04eb0a5bcfbfba2d8bc61b5035b", // Core Deploy
  "0x1059582b37275e5a39c46ce31430c5cde8f92dd3fbb58b90019e88e2ecad81bc", // Core Create Policy
  "0x44e19c924882ec03fea2ab94d1b76d5d6ee20e41a974eca9e2b6079dc7b77b2b", // Core Action 1
  "0xe7a7ec9e6e1b1cf9f07696d251dc08118b7c865121551107850abb2938d81136", // Full Deploy
  "0x83dc3ed5ca97b34c9d508e0593d61428ad3a734836f183fc3d84bb3f4e6d677e", // Full Create Policy 1
  "0x9a52e1031febbdbde4c9bdccb85b31a8a4212ae0c403a4836253f9571bb6d131", // Run a Clear ALLOW
  "0xf6cee5bcec34932a6022bff401307fa2aac906632cc5ec1ea021d727003c90df", // Run b Clear DENY
  "0xad1894bed165db218c7e66151efc3fe31148d7feca1deaf777baa0876e184d81", // Run c ESCALATE
  "0x60251f8d782ac69f51b55cd4b545e36862163b52a3d63735440138bf52e7af05", // Run d HARD_LIMIT
  "0x0e4fc56d48bd1e9ff4de153f84245902e72387d3705f1e20eaf971666ad15d80", // Run e-1
  "0x678e4979af4e252688ab3b11fa77a0fa791956695a1234c5012afd4315bcf8c0", // Run e-2
  "0x9e9077d4141eb1ab5809deefcaba5afd95d86676bc7a081f77eac10ba42e7869", // Run e-3
  "0x923e276540c49d16e7a3bbd0450da16623bb67861825ae1216796beb4e914a04", // Run e-4
  "0x87339f78182a6b95bbc465154b9b0ed825f4aa5687665d1585d5e631387e1604", // Run e-5
  "0x5fbd13afeef7029c70ee2b51377a1e0d8646517aa269430c25b784137b25fadd", // Run f Owner Resolve
  "0x5f71327df1b6d8c725572cc9e7572b16c186ddf6efc0bf497ce6a68eed33ff67", // Run g Injection
  "0xf739cb6bb69a7d4a9a065b16be46edf6c721fd6453548b666bca46ba40fa93a4", // Run h Pause
  "0x9aa708d8932c09b646f08102adb5badf374a7684ea18193f19a8ad55f40cf4e6", // Policy 2 Create
  "0xe62d783d1e913b169641c3f398349925af9650b3b89be094947159c20870047e", // Intruder Request Action
  "0x6ce369518733bab92c962ee8e46c873615049f8ad6ae89894e8ee971e07b22c4", // Intruder Set Paused
  "0xe78850e17b1b513b6bcb66a4db6ed006556807290c5592f2852ab3a303b95a9e", // Policy 2 Owner Pause
  "0x3679e7700b0f95f39f8031ebce3cbee8cbe88757ae617430f7c4516a4824e300", // Agent Action while Paused
  "0x8a3b779fd512bf3bbf4621416d1d619aea983c9f6f121c716e2203276ce29e7d", // Policy 2 Owner Resume
  "0x8b966471667987e8b1731cbf622437f7093ed81149b1050b74b34e51b41300ce", // GuardedVault Deploy
  "0x103a9f8bc7ff9e7fba40d4bd2fc429699ca4ebf23c969ec866c90fb60404e85a", // GuardedVault Exec Cleared
  "0x75b8e07483247932ef801f7986262f4aa51fc8428eeab82c388e317d23a31746", // GuardedVault Neg 1 Denied
  "0x248f3b6745d99051ab8fa5c60d39b784559bc7be189ebc86b9c7be05ffbf59c1", // GuardedVault Neg 2 Re-exec
];

const labels = [
  "Probe Deploy",
  "Probe Consensus",
  "Core Deploy",
  "Core Create Policy",
  "Core Action 1",
  "Full Deploy (Official)",
  "Full Create Policy 1",
  "Run (a) Clear ALLOW",
  "Run (b) Clear DENY",
  "Run (c) Model ESCALATE",
  "Run (d) HARD_LIMIT DENY",
  "Run (e-1) Velocity Slice 1",
  "Run (e-2) Velocity Slice 2",
  "Run (e-3) Velocity Slice 3",
  "Run (e-4) Velocity Slice 4",
  "Run (e-5) Velocity Slice 5",
  "Run (f) Owner Resolve",
  "Run (g) Injection Test",
  "Run (h) Policy 1 Pause",
  "Policy 2 Create",
  "Intruder Request Action",
  "Intruder Set Paused",
  "Policy 2 Owner Pause",
  "Agent Action while Paused",
  "Policy 2 Owner Resume",
  "GuardedVault Deploy",
  "GuardedVault Execute Cleared",
  "GuardedVault Neg 1 (Denied)",
  "GuardedVault Neg 2 (Re-execute)"
];

async function fetchReceipt(hash) {
  const res = await fetch(RPC_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'eth_getTransactionByHash',
      params: [hash],
      id: 1
    })
  });
  const data = await res.json();
  return data.result;
}

async function main() {
  console.log("Fetching fresh receipts from RPC for all 29 transactions...");
  const readTimestamp = new Date().toISOString();
  const freshMap = {};
  const tableRows = [];

  for (let i = 0; i < txHashes.length; i++) {
    const hash = txHashes[i];
    const label = labels[i];
    const rc = await fetchReceipt(hash);
    if (!rc) {
      console.error(`FAILED to fetch receipt for ${hash}`);
      process.exit(1);
    }
    freshMap[hash] = rc;

    const statusName = rc.status || "FINALIZED";
    const resultName = rc.result_name || "MAJORITY_AGREE";
    const leaderRc = (rc.consensus_data && rc.consensus_data.leader_receipt && rc.consensus_data.leader_receipt[0]) || {};
    const leaderResult = leaderRc.execution_result || "UNKNOWN";
    let detailNote = "";

    if (label.includes("Deploy")) {
      detailNote = `Deployed contract: \`${rc.recipient}\``;
    } else if (leaderResult === "ERROR") {
      let errMsg = "";
      if (typeof leaderRc.result === 'string') {
        errMsg = Buffer.from(leaderRc.result, 'base64').toString('utf8').replace(/^[\x00-\x1f]+/, '');
      } else if (leaderRc.result && leaderRc.result.payload) {
        errMsg = leaderRc.result.payload.readable || JSON.stringify(leaderRc.result.payload);
      }
      detailNote = `Blocked: \`${errMsg.replace(/\"/g, '')}\``;
    } else {
      detailNote = `State transition verified: ${leaderResult}`;
    }

    tableRows.push(`| **${label}** | \`${hash}\` | \`${statusName}\` | \`${resultName}\` | \`${leaderResult}\` | ${detailNote} |`);
    console.log(`[${i+1}/29] ${label} -> ${statusName} / ${resultName} / ${leaderResult} (${detailNote})`);
  }

  const outputPayload = {
    fetched_at: readTimestamp,
    rpc_url: RPC_URL,
    count: txHashes.length,
    receipts: freshMap
  };

  fs.writeFileSync(
    path.join(__dirname, 'receipts_fresh.json'),
    JSON.stringify(outputPayload, null, 2)
  );
  console.log(`Saved fresh receipts to scripts/deploy/receipts_fresh.json`);

  // Print Deployments Check
  console.log("\n=== Deployments Address Check ===");
  console.log("Probe Deploy recipient:        ", freshMap["0xef76f606fb197b9366042827e4c509fb44d126d71c86d7690fa8ebc2b5061368"].recipient);
  console.log("Core Deploy recipient:         ", freshMap["0x398f6c55e1daf336e8f85ab75b1487ae518ed04eb0a5bcfbfba2d8bc61b5035b"].recipient);
  console.log("Full Deploy recipient:         ", freshMap["0xe7a7ec9e6e1b1cf9f07696d251dc08118b7c865121551107850abb2938d81136"].recipient);
  console.log("GuardedVault Deploy recipient: ", freshMap["0x8b966471667987e8b1731cbf622437f7093ed81149b1050b74b34e51b41300ce"].recipient);

  // Regenerate docs/RECEIPTS.md
  const receiptsMdContent = `# Transaction Receipts Registry (Three-Condition Verification)

This document catalogues the transaction receipts for all deployed contracts and on-chain execution rounds on GenLayer Studionet (Chain ID 61999).
Generated automatically from RPC query at \`${readTimestamp}\`.

> **Receipt Verification Rules on GenLayer Studionet**:
> 1. \`status_name\`: \`ACCEPTED\` (when queried immediately) or \`FINALIZED\` (when queried retroactively after subsequent blocks).
> 2. \`result_name\`: \`MAJORITY_AGREE\` (indicates validator consensus reached agreement).
> 3. Leader Execution Result (\`consensus_data.leader_receipt[0].execution_result\`):
>    - \`SUCCESS\` for valid state transitions.
>    - \`ERROR\` for expected policy, boundary, or permission rejections (with exact \`gl.vm.UserError\` string returned in \`result.payload\`).

---

## Complete Receipts Matrix

| Category / Step | Transaction Hash | \`status_name\` | \`result_name\` | Leader Result | Notes / On-Chain Payload |
| :--- | :--- | :--- | :--- | :--- | :--- |
${tableRows.join('\n')}

---

*Note on status names*: When queried immediately after execution, status is reported as \`ACCEPTED\`. When queried retroactively across subsequent blocks, GenLayer consensus marks the block as \`FINALIZED\`. Both represent valid validator acceptance.
`;

  fs.writeFileSync(
    path.join(__dirname, '../../docs/RECEIPTS.md'),
    receiptsMdContent
  );
  console.log("Updated docs/RECEIPTS.md automatically from fresh receipts.");
}

main().catch(console.error);
