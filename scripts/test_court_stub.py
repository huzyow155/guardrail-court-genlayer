import sys
sys.path.insert(0, 'tests')
import genlayer_stub
sys.path.insert(0, 'contracts')
import GuardrailCourt
from genlayer import gl

court = GuardrailCourt.GuardrailCourt()
print('Initialized court successfully!')
print('meta:', court.meta)

# 1. create_policy
policy_id = court.create_policy(
    agent='0x2222222222222222222222222222222222222222',
    text='Agent may buy cloud credits and developer tools. No gift cards or casino.',
    max_amount='100',
    window_cap='400'
)
print('Created policy:', policy_id)
print('Policy JSON:', court.get_policy(policy_id))

# 2. Switch sender to agent
gl.message.sender_address.as_hex = '0x2222222222222222222222222222222222222222'

# 3. request_action (ALLOW via JUDGE)
gl.nondet.prompt_result = '{"verdict": "ALLOW"}'
d1 = court.request_action(policy_id, 'cloud_ops', '45', 'Valid server usage invoice')
print('Action 1:', d1, court.get_decision(d1))
print('Action 1 is_cleared:', court.is_cleared(d1))

# 4. request_action (HARD_LIMIT)
d2 = court.request_action(policy_id, 'cloud_ops', '150', 'Large compute instance exceeds 100')
print('Action 2 (HARD_LIMIT):', d2, court.get_decision(d2))

# 5. request_action (VELOCITY)
court.request_action(policy_id, 'cloud_ops', '90', 'Slice 2')
court.request_action(policy_id, 'cloud_ops', '90', 'Slice 3')
court.request_action(policy_id, 'cloud_ops', '90', 'Slice 4')
d5 = court.request_action(policy_id, 'cloud_ops', '90', 'Slice 5 should trip velocity')
print('Action 5 (VELOCITY):', d5, court.get_decision(d5))

# 6. resolve_escalation by owner
gl.message.sender_address.as_hex = '0x1111111111111111111111111111111111111111'
court.resolve_escalation(d5, 'ALLOW')
print('Resolved Action 5:', court.get_decision(d5))
print('Action 5 is_cleared:', court.is_cleared(d5))

# 7. pause toggle
court.set_paused(policy_id, True)
print('Paused policy 1 successfully')

# 8. agent blocked when paused
gl.message.sender_address.as_hex = '0x2222222222222222222222222222222222222222'
try:
    court.request_action(policy_id, 'cloud_ops', '10', 'Blocked while paused')
    print('ERROR: should have failed!')
except gl.vm.UserError as e:
    print('Caught expected UserError while paused:', e)

print('\nALL STUB CONTRACT METHODS EXECUTED DIRECTLY ON contracts/GuardrailCourt.py!')
