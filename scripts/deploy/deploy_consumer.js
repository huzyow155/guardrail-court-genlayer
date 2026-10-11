const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');
const path = require('path');

async function main() {
  const account = createAccount();
  console.log("Using deployer address:", account.address);
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const deployments = JSON.parse(fs.readFileSync(path.join(__dirname, 'deployments.json'), 'utf8'));
  const guardrailCourtAddress = deployments.contractAddress;
  console.log("Target GuardrailCourt address:", guardrailCourtAddress);

  const codePath = path.join(__dirname, '../../examples/consumer/GuardedVault.py');
  const code = fs.readFileSync(codePath, 'utf8');

  console.log("Deploying GuardedVault consumer contract to Studionet...");
  const deployTxHash = await client.deployContract({
    code: code,
    args: [guardrailCourtAddress],
  });
  console.log("Deploy Tx Hash:", deployTxHash);

  const receipt = await client.waitForTransactionReceipt({
    hash: deployTxHash,
    retries: 120,
    interval: 3000,
  });
  console.log("Deploy Receipt Status:", receipt.status_name, "Result:", receipt.result_name);
  const vaultAddress = receipt.recipient;
  console.log("Deployed GuardedVault Address:", vaultAddress);

  // 1. Attempt to execute Decision 1 (which was CLEARED on GuardrailCourt)
  console.log("\nExecuting cleared Decision 1 on GuardedVault...");
  const execTx1 = await client.writeContract({
    address: vaultAddress,
    functionName: 'execute',
    args: ["1", "Domain renewal invoice payment executed"],
  });
  console.log("Exec Tx Hash:", execTx1);

  const execReceipt1 = await client.waitForTransactionReceipt({
    hash: execTx1,
    retries: 120,
    interval: 3000,
  });
  console.log("Exec 1 Receipt Status:", execReceipt1.status_name, "Result:", execReceipt1.result_name);

  // 2. Read back executions
  const execs = await client.readContract({
    address: vaultAddress,
    functionName: 'list_executions',
    args: [10],
  });
  console.log("GuardedVault executions read back:", execs);

  // 3. Attempt to execute Decision 2 (which was DENIED) - should be blocked
  console.log("\nAttempting to execute DENIED Decision 2 (should revert)...");
  let deniedBlocked = false;
  let deniedErr = "";
  try {
    const execTx2 = await client.writeContract({
      address: vaultAddress,
      functionName: 'execute',
      args: ["2", "Attempting payout for forbidden action"],
    });
    const execReceipt2 = await client.waitForTransactionReceipt({
      hash: execTx2,
      retries: 120,
      interval: 3000,
    });
    if (execReceipt2.result_name === "MAJORITY_DISAGREE" || execReceipt2.status_name === "UNDETERMINED") {
      deniedBlocked = true;
      deniedErr = execReceipt2.result?.payload?.readable || "Transaction reverted";
    }
  } catch (err) {
    deniedBlocked = true;
    deniedErr = err.message;
  }
  console.log("Denied execution successfully blocked:", deniedBlocked, "Error:", deniedErr);

  const consumerOutput = {
    vaultAddress: vaultAddress,
    guardrailCourtAddress: guardrailCourtAddress,
    deployTxHash: deployTxHash,
    deployReceipt: receipt,
    execTx1: execTx1,
    execReceipt1: execReceipt1,
    deniedBlocked: deniedBlocked,
    executions: JSON.parse(execs),
  };

  fs.writeFileSync(
    path.join(__dirname, 'consumer_output.json'),
    JSON.stringify(consumerOutput, null, 2)
  );
  console.log("Saved consumer output to consumer_output.json");
}

main().catch(err => {
  console.error("Consumer error:", err);
  process.exit(1);
});
