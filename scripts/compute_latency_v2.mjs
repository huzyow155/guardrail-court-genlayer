import dns from 'dns';
dns.setDefaultResultOrder('ipv4first');

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const evidenceDir = path.join(__dirname, '../docs/evidence_v2');

// Load raw data from case files
const c1 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_01_clean.json'), 'utf8'));
const c2 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_02_hard_limit.json'), 'utf8'));
const c3 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_03_recipient_asset_guard.json'), 'utf8'));
const c4 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_04_velocity_resolve.json'), 'utf8'));
const c5 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_05_semantic_injection.json'), 'utf8'));
const c7 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_07_pause.json'), 'utf8'));
const c8 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_08_pending_cap.json'), 'utf8'));
const c9 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_09_vault.json'), 'utf8'));
const c10 = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_10_validation.json'), 'utf8'));
const c11Raw = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_11_latency.json'), 'utf8'));
const c4b = JSON.parse(fs.readFileSync(path.join(evidenceDir, 'case_04b_velocity_live.json'), 'utf8'));

// All samples with exact timing and genuine source classification
const allSamples = [
  // Setup & Admin writes
  { label: "Setup Create Policy 1", txHash: "0x803da256d22a9e09982938879d5879fa362ee43a61fdb24715005d16ea9be949", durSec: 8.76, class: "admin_writes", source: "create_policy" },
  { label: "Case 8 Create Policy 2", txHash: "0xb88bc70d01970cb30f69ab626cabee408b073fcd8b636c12cf6b8f6f5bff7155", durSec: 5.66, class: "admin_writes", source: "create_policy" },
  { label: "Case 4b Create Policy 3", txHash: c4b.policy_3_creation.tx_hash, durSec: 6.40, class: "admin_writes", source: "create_policy" },
  { label: "Case 7 Owner Pause Policy 1", txHash: "0xd25e8165be376b53a01209eea0a7162e9e82aa6275fca5d507abc9f57d1ae0ae", durSec: 9.03, class: "admin_writes", source: "set_paused(true)" },
  { label: "Case 7 Owner Unpause Policy 1", txHash: "0xaad460f796af15dbbaf7474a6e217b2fdb615ce57b56d5e82f30427e0d1321f8", durSec: 12.57, class: "admin_writes", source: "set_paused(false)" },
  { label: "Case 4 Owner Resolve Decision 8", txHash: "0xae56f47dd56d8772a761505fba53c8a79272afd7431af1bfb7becd3b454d81bb", durSec: 8.75, class: "admin_writes", source: "resolve_escalation" },
  { label: "Case 8 Resolve Pending Decision 20", txHash: "0x3158f601f9eafc5dc64d53d6cf0cbd9c7841dfef823e8e3d6247ac3aec917315", durSec: 9.47, class: "admin_writes", source: "resolve_escalation" },
  { label: "Case 4b Resolve Decision 23", txHash: c4b.step5_owner_resolve.tx.tx_hash, durSec: c4b.step5_owner_resolve.durSec, class: "admin_writes", source: "resolve_escalation" },
  { label: "Case 9 GuardedVault Execute Decision 1", txHash: "0xb4f75402c09bea6fdbf1609e0079eb089d485a93871887b71390c1150cd84280", durSec: 8.49, class: "admin_writes", source: "vault_execute" },
  { label: "Pause Policy 1 for Vault Check", txHash: "0xdcfbce40f0c2b2bc8267ae356243c85a6b49e4980c88fe0160abd23b1e249e93", durSec: 8.58, class: "admin_writes", source: "set_paused(true)" },
  { label: "Unpause Policy 1 post Vault Check", txHash: "0x81b4ce128dda2fb256726a22811ab22acf5f87534184f9669b8a6fdff02e42ac", durSec: 8.65, class: "admin_writes", source: "set_paused(false)" },

  // Guard-Only Writes (Deterministic on-chain checks, zero model call)
  { label: "Case 2: 101 USDC > max_amount 100", txHash: "0x7b92bf05ea02125b59579e5f1cd72620a43fdc17da5af6eec1ff057e1929202a", durSec: 9.03, class: "guard_only", source: "HARD_LIMIT" },
  { label: "Case 3a: Unauthorized Recipient", txHash: "0x240ca57c087568fc9cc8c693911c8f41018b92ea0bd1e9e0b5198fee4a2f4118", durSec: 9.56, class: "guard_only", source: "RECIPIENT_GUARD" },
  { label: "Case 3b: Unauthorized Asset (DAI)", txHash: "0x76213a0c685051858c93651481c2610e8ee974014275ace16c6ea323d21de613", durSec: 9.09, class: "guard_only", source: "ASSET_GUARD" },
  { label: "Case 4b Velocity Trip Action (60 USDC)", txHash: c4b.step3_velocity_trip.tx.tx_hash, durSec: c4b.step3_velocity_trip.durSec, class: "guard_only", source: "VELOCITY" },
  { label: "Case 4b Hard Limit Request (61 USDC)", txHash: c4b.step4_denied_check.hard_limit.tx.tx_hash, durSec: c4b.step4_denied_check.hard_limit.durSec, class: "guard_only", source: "HARD_LIMIT" },

  // Judged Writes (Model consensus executed by validators)
  { label: "Case 1: Clean server_ops 40 USDC", txHash: "0x17ff48e84ee657a47285a61456dfd2580598bcc4e4d196738bef13f4248d6411", durSec: 21.17, class: "judged", source: "JUDGE" },
  { label: "Case 4: Velocity Slice 1 (100 USDC)", txHash: "0x3076db6cdddc7e066893bf5df9599199c7eb29de01d2ccbd90b8a6084fa23f7e", durSec: 33.34, class: "judged", source: "JUDGE" },
  { label: "Case 4: Velocity Slice 2 (100 USDC)", txHash: "0x5eaf3372bc35d395e659c62589733f362513fd08f3e4affc8e54dfc8ccf176a7", durSec: 81.91, class: "judged", source: "JUDGE" },
  { label: "Case 4: Velocity Slice 3 (100 USDC)", txHash: "0x08835f61e6806a553c098718ed3fb2d8a7d6f8f56e81ae17563411ad2142fe3d", durSec: 115.01, class: "judged", source: "JUDGE" },
  { label: "Case 4: Slice 4 (Model Escalation)", txHash: "0x35578eb043ce881a5a503a919167339c689c6ab55ff06a30dbca47d74515cd35", durSec: 51.48, class: "judged", source: "JUDGE" },
  { label: "Case 5a: Semantic NFT Purchase", txHash: "0x21c8777951ff771b02b919583e71b7d4922c69a0e65cbe80420e4ca3388ee515", durSec: 18.96, class: "judged", source: "JUDGE" },
  { label: "Case 5b: Prompt Injection Attempt", txHash: "0x2754665b53f5ff8429fdc6c2a931aee3b1c88feba887917fb99f310bf92ca782", durSec: 24.24, class: "judged", source: "JUDGE" },
  { label: "Case 8: Policy 2 Initial Fill (50 USDC)", txHash: "0x9377cc50b49826af6a4b5fc29a6fa098128e22d6eb019d07cc484d84206008f4", durSec: 23.87, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 1/10", txHash: "0xdd7c01251660c85d42a37fd29365dc801a3f82c15df27118fbde0702a1839ae3", durSec: 22.47, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 2/10", txHash: "0x685b151914aee060854c07d34c3dfc03bd03cbd18ab875fcee46150025f387cc", durSec: 104.66, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 3/10", txHash: "0x03e74b11c6b163b190551b98840ceefd02ac1ae37cfaa613f583b0d690d3d5d6", durSec: 31.81, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 4/10", txHash: "0x63f6935343c045a6a4394471a4d59c54c8289af9507582cee149410977f89e34", durSec: 21.72, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 5/10", txHash: "0x1e13f90b5bd07758ab95a67c8605d5170154365183843c58172e5d7dd9df7ca6", durSec: 15.12, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 6/10", txHash: "0x3e6b1a0e152e5965e5b7fa3efaf4c037c89d27a6e4b5a179d22980e9e8969702", durSec: 35.17, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 7/10", txHash: "0x79926637916fdf5977aa77ef2bedf705caf1b0aaf70533b9395abe53fc45cac5", durSec: 19.31, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 8/10", txHash: "0x3d3a33436a667a9fb1b306400224ffcae365fe35566bb5556b1a91862914af5c", durSec: 31.70, class: "judged", source: "JUDGE" },
  { label: "Case 8: Pending Escalation 9/10", txHash: "0x17f2f5581bf2675431fc7d9103c271d7d4f2238115a15c7c294da37bdfc66bb5", durSec: 15.24, class: "judged", source: "JUDGE" },
  { label: "Case 8: 12th Action After Resolve", txHash: "0x561cdd7d4b7a9682d74a0929f840ee6fcbe9d73543ae0f23e9eab31b592a44c0", durSec: 71.57, class: "judged", source: "JUDGE" },
  { label: "Case 4b Try 1 (60 USDC)", txHash: c4b.step2_tries[0].tx.tx_hash, durSec: c4b.step2_tries[0].durSec, class: "judged", source: "JUDGE" },
  { label: "Case 4b Request within Cap (40 USDC)", txHash: c4b.step4_denied_check.within_cap_40.tx.tx_hash, durSec: c4b.step4_denied_check.within_cap_40.durSec, class: "judged", source: "JUDGE" },

  // Reverted Validation / Gate Writes (Deterministic UserError rejects)
  { label: "Case 7 Agent Action While Paused", txHash: "0x261c5eb040f5d97015f14d57c1ed101e50bf8218ae561a9c29a11baa94d61fba", durSec: 9.03, class: "reverted_validation", source: "revert:policy is paused" },
  { label: "Case 7 Non-Owner Pause Revert", txHash: "0x3251dbe02381196052ff6d687831acf0bfb4108197fd4c3e90adf84a42d98f7b", durSec: 9.66, class: "reverted_validation", source: "revert:not policy owner" },
  { label: "Case 4 Repeat Resolve Revert Check", txHash: "0xc22d50c56bf798cd307588c8ba5614586e2b8bfcb86a2177cfd0667b954c676e", durSec: 8.80, class: "reverted_validation", source: "revert:not pending resolution" },
  { label: "Case 4 Non-Owner Resolve Revert Check", txHash: "0x8cb5ee18851c4fbce2a52d00ee3513e9d28f9e8b6df76c15509ad553e28775fa", durSec: 5.42, class: "reverted_validation", source: "revert:not policy owner" },
  { label: "Case 8 Pending Escalation 10/10", txHash: "0x7289222372a79b933aa9f3b19dc39352539725062c782661e557efdbe0c47ada", durSec: 5.37, class: "reverted_validation", source: "revert:too many pending" },
  { label: "Case 8 11th Action Cap Exceeded Check", txHash: "0x9751c07ba6ca6d67926821096093f1090debc9beea6aec94abb6dcc38ba1af93", durSec: 8.49, class: "reverted_validation", source: "revert:too many pending" },
  { label: "Case 9 GuardedVault Replay Revert Check", txHash: "0xe6ef8621642d51299381ecbc34f9c5505b093e9bc28c0a25f594bf8e94b9c23e", durSec: 5.17, class: "reverted_validation", source: "revert:already executed" },
  { label: "Case 9 GuardedVault Parameter Tamper Check", txHash: "0x75672bf05a8eddbcdc29b57d160d6a4b0a2ba8487582cef2eaa38e0bc553d386", durSec: 8.54, class: "reverted_validation", source: "revert:clearance mismatch" },
  { label: "Case 9 GuardedVault Execution on Paused Policy", txHash: "0xfdd8b9bc0b3f3d2532303e7e7efbb741f54435296e37841002258a592df86f9b", durSec: 8.61, class: "reverted_validation", source: "revert:clearance mismatch" },
  { label: "Validation 10.1 Newline in justification", txHash: "0x966193eb70e1cbbae121de5035928b1851f24da7ac91b29b0f94084eea5dbaa7", durSec: 5.47, class: "reverted_validation", source: "revert:control char in just." },
  { label: "Validation 10.2 Justification < 5 chars", txHash: "0x44f74cffb65094c12389abcc94be6a4e62ab96e76f43049bb7ad01cad82134bb", durSec: 5.21, class: "reverted_validation", source: "revert:justification < 5" },
  { label: "Validation 10.3 Non-agent sender", txHash: "0x34fbf261cc43b553b5a4a11ce2d8b76096aa095f4d6d2bc6767eca2b938684ec", durSec: 5.24, class: "reverted_validation", source: "revert:not agent" },
  { label: "Validation 10.4 Calldata hash not 64 hex chars", txHash: "0x37f65120e973d5d7eaacfc4fca30a2394329852d5f6d88a4ec596a76beeb38d9", durSec: 5.24, class: "reverted_validation", source: "revert:calldata len != 64" },
  { label: "Validation 10.5 Amount = 0", txHash: "0xce4936a7f3bb98bcfc9142672565528fc22b11cb733eccc5b1f86533b3cdb210", durSec: 8.52, class: "reverted_validation", source: "revert:amount < 1" },
];

function calcStats(samples) {
  const arr = samples.map(s => s.durSec);
  if (!arr.length) return { count: 0, min: 0, mean: 0, max: 0 };
  const min = Math.min(...arr);
  const max = Math.max(...arr);
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  return {
    count: arr.length,
    min: parseFloat(min.toFixed(2)),
    mean: parseFloat(mean.toFixed(2)),
    max: parseFloat(max.toFixed(2)),
    samples,
  };
}

const groups = {
  admin_writes: allSamples.filter(s => s.class === "admin_writes"),
  guard_only: allSamples.filter(s => s.class === "guard_only"),
  judged: allSamples.filter(s => s.class === "judged"),
  reverted_validation: allSamples.filter(s => s.class === "reverted_validation"),
};

const stats = {
  admin_writes: calcStats(groups.admin_writes),
  guard_only: calcStats(groups.guard_only),
  judged: calcStats(groups.judged),
  reverted_validation: calcStats(groups.reverted_validation),
};

console.log("=== RECOMPUTED LATENCY BENCHMARKS ===");
console.log(`Judged Writes (n=${stats.judged.count}): min ${stats.judged.min}s, mean ${stats.judged.mean}s, max ${stats.judged.max}s`);
console.log(`Guard-Only Writes (n=${stats.guard_only.count}): min ${stats.guard_only.min}s, mean ${stats.guard_only.mean}s, max ${stats.guard_only.max}s`);
console.log(`Admin Writes (n=${stats.admin_writes.count}): min ${stats.admin_writes.min}s, mean ${stats.admin_writes.mean}s, max ${stats.admin_writes.max}s`);
console.log(`Reverted Validation Gates (n=${stats.reverted_validation.count}): min ${stats.reverted_validation.min}s, mean ${stats.reverted_validation.mean}s, max ${stats.reverted_validation.max}s`);

console.log("\n=== COMPLETE PER-SAMPLE TABLE WITH SOURCE COLUMN ===");
console.log("| Label | Tx Hash | Class | Source / Mechanism | Latency (s) |");
console.log("| :--- | :--- | :--- | :--- | :--- |");
for (const s of allSamples) {
  console.log(`| ${s.label} | \`${s.txHash.slice(0, 10)}...${s.txHash.slice(-6)}\` | ${s.class} | **${s.source}** | ${s.durSec.toFixed(2)}s |`);
}

// Write regenerated case_11_latency.json
fs.writeFileSync(path.join(evidenceDir, 'case_11_latency.json'), JSON.stringify(stats, null, 2));
console.log("\nSaved recomputed latency to docs/evidence_v2/case_11_latency.json");
