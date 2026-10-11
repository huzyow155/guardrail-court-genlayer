import re

with open('contracts/GuardrailCourt.py', 'r', encoding='utf-8') as f:
    contract_code = f.read()

with open('tests/test_layer2_mocked.py', 'r', encoding='utf-8') as f:
    sim_code = f.read()

contract_errs = set(re.findall(r'raise gl\.vm\.UserError\(["\']([^"\']+)["\']\)', contract_code))
sim_errs = set(re.findall(r'raise UserError\(["\']([^"\']+)["\']\)', sim_code))

print('Contract UserError count:', len(contract_errs))
print('Simulator UserError count:', len(sim_errs))

diff_in_contract_only = sorted(list(contract_errs - sim_errs))
diff_in_sim_only = sorted(list(sim_errs - contract_errs))

print('Errors in contract only:', diff_in_contract_only)
print('Errors in simulator only:', diff_in_sim_only)
