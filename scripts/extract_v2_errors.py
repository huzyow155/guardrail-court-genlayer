import ast
import os

def extract_errors_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    records = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            # Check if raising gl.vm.UserError
            call = node.exc
            if isinstance(call, ast.Call):
                func_name = ast.unparse(call.func)
                if "UserError" in func_name and call.args:
                    arg = call.args[0]
                    if isinstance(arg, ast.Constant):
                        err_str = arg.value
                        records.append((node.lineno, err_str))
    records.sort(key=lambda x: x[0])
    return records

def main():
    targets = [
        ("contracts/GuardrailCourtV2.py", "GuardrailCourtV2"),
        ("examples/consumer/GuardedVaultV2.py", "GuardedVaultV2"),
    ]
    
    print("| # | File / Contract | Line | Exact gl.vm.UserError String |")
    print("|---|---|---|---|")
    count = 1
    for filepath, name in targets:
        errors = extract_errors_from_file(filepath)
        for lineno, msg in errors:
            print(f"| {count} | `{name}` | {lineno} | `{msg}` |")
            count += 1

if __name__ == "__main__":
    main()
