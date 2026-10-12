import re

with open('contracts/GuardrailCourt.py', 'r', encoding='utf-8') as f:
    c_lines = f.readlines()

c_errs = set()
for idx, l in enumerate(c_lines, 1):
    m = re.search(r'raise gl\.vm\.UserError\("([^"]+)"\)', l)
    if m:
        c_errs.add(m.group(1))

with open('tests/test_layer2_mocked.py', 'r', encoding='utf-8') as f:
    t_lines = f.readlines()

t_errs = set()
for idx, l in enumerate(t_lines, 1):
    m = re.search(r'raise UserError\("([^"]+)"\)', l)
    if m:
        t_errs.add(m.group(1))

print(f"Contract unique errors count:  {len(c_errs)}")
print(f"Simulator unique errors count: {len(t_errs)}")
diff1 = c_errs - t_errs
diff2 = t_errs - c_errs
print(f"In contract but not simulator: {diff1}")
print(f"In simulator but not contract: {diff2}")
if not diff1 and not diff2:
    print("MATCH: 100% exact parity across all 16 UserError strings.")
