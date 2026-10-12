import difflib

with open('contracts/GuardrailCourt.py', 'r', encoding='utf-8') as f:
    c_lines = f.readlines()
with open('contracts/guardrail_helpers.py', 'r', encoding='utf-8') as f:
    h_lines = f.readlines()

def get_block(lines, start_prefix):
    res = []
    recording = False
    for l in lines:
        if l.startswith(start_prefix):
            recording = True
        elif recording and (l.startswith('def ') or l.startswith('class ') or l.startswith('# -')):
            break
        if recording:
            res.append(l)
    return res

pairs = [
    ('is_valid_address', 'def _is_valid_address', 'def is_valid_address'),
    ('is_valid_amount_str', 'def _is_valid_amount_str', 'def is_valid_amount_str'),
    ('is_valid_category', 'def _is_valid_category', 'def is_valid_category'),
    ('parse_model_verdict', 'def _parse_model_verdict', 'def parse_model_verdict'),
    ('velocity_guard', 'def _velocity_guard', 'def velocity_guard'),
]

for name, c_start, h_start in pairs:
    c_block = get_block(c_lines, c_start)
    h_block = get_block(h_lines, h_start)
    
    # Normalize function name in the def line
    c_norm = [l.replace('def _', 'def ') for l in c_block]
    c_norm = [l.replace('list[dict]', 'list') for l in c_norm]
    h_norm = [l.replace('list[dict]', 'list') for l in h_block]
    
    # Strip comments and docstrings
    c_clean = [l for l in c_norm if not l.strip().startswith('#') and not l.strip().startswith('"""')]
    h_clean = [l for l in h_norm if not l.strip().startswith('#') and not l.strip().startswith('"""')]
    
    diff = list(difflib.unified_diff(c_clean, h_clean, fromfile=f'GuardrailCourt.py:{name}', tofile=f'guardrail_helpers.py:{name}'))
    print(f'=== FUNCTION: {name} ===')
    if not diff:
        print('diff rỗng')
    else:
        for d in diff:
            print(d, end='')
    print()
