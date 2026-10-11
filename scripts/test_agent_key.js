const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');

async function testSecondKey() {
  const owner = createAccount();
  const agent = createAccount();
  console.log("Owner address:", owner.address);
  console.log("Agent address:", agent.address);

  const clientAgent = createClient({
    chain: chains.studionet,
    account: agent,
  });

  // Test reading from deployed probe using agent client
  const probeAddress = "0xCafd1A568d5A55eb7E1135F0Fe31137114D5Fe42";
  const res = await clientAgent.readContract({
    address: probeAddress,
    functionName: 'test_bool_view',
    args: [],
  });
  console.log("Agent read test_bool_view succeeded:", res);
}

testSecondKey().catch(console.error);
