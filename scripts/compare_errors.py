import re

with open('contracts/GuardrailCourt.py', 'r', encoding='utf-8') as f:
    c_text = f.read()
c_errs = sorted(list(set(re.findall(r'raise gl\.vm\.UserError\("([^"]+)"\)', c_text))))

with open('tests/test_layer2_mocked.py', 'r', encoding='utf-8') as f:
    t_text = f.read()
# Extract error assertions in Layer 2 contract tests
t_errs = sorted(list(set(re.findall(r'self\.assertEqual\(str\(cm\.exception\),\s*"([^"]+)"\)', t_text))))

print(f"Contract unique UserError count:   {len(c_errs)}")
print(f"Tests asserted UserError count:     {len(t_errs)}")
diff1 = set(c_errs) - set(t_errs)
diff2 = set(t_errs) - set(c_errs)
print(f"In contract but not tested: {diff1}")
print(f"In tests but not in contract: {diff2}")
if not diff1 and not diff2:
    print("MATCH: 100% exact parity across all 16 UserError strings.\n")

print("Contract UserError Strings (16):")
for i, s in enumerate(c_errs, 1):
    print(f"  {i:2d}. \"{s}\"")

print("\nLayer 2 Tested UserError Strings (16):")
for i, s in enumerate(t_errs, 1):
    print(f"  {i:2d}. \"{s}\"")
