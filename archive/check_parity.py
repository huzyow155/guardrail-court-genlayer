import difflib
import re
import sys

def extract_function_lines(filepath: str, func_name: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    res = []
    in_func = False
    for line in lines:
        if line.startswith(f"def {func_name}(") or line.startswith(f"def _{func_name}("):
            in_func = True
            res.append(line)
            continue
        if in_func:
            # Stop if another top-level def or class begins
            if line.startswith("def ") or line.startswith("class ") or line.startswith("# Aliases"):
                break
            res.append(line)
    return res

def compare_parity():
    print("=== SOURCE CODE PARITY AUDIT ===")
    print("Comparing contracts/GuardrailCourt.py vs contracts/guardrail_helpers.py\n")

    pairs = [
        ("is_valid_address", "_is_valid_address", "is_valid_address"),
        ("is_valid_amount_str", "_is_valid_amount_str", "is_valid_amount_str"),
        ("is_valid_category", "_is_valid_category", "is_valid_category"),
        ("parse_model_verdict", "_parse_model_verdict", "parse_model_verdict"),
        ("velocity_guard", "_velocity_guard", "velocity_guard"),
    ]

    all_match = True
    for label, c_name, h_name in pairs:
        c_lines = extract_function_lines("contracts/GuardrailCourt.py", c_name)
        h_lines = extract_function_lines("contracts/guardrail_helpers.py", h_name)

        if not c_lines:
            print(f"[FAIL] Could not extract {c_name} from GuardrailCourt.py")
            all_match = False
            continue
        if not h_lines:
            print(f"[FAIL] Could not extract {h_name} from guardrail_helpers.py")
            all_match = False
            continue

        # Normalize the definition line name only (remove leading underscore for comparison)
        c_norm = [c_lines[0].replace(f"def {c_name}", f"def {label}")] + c_lines[1:]
        h_norm = [h_lines[0].replace(f"def {h_name}", f"def {label}")] + h_lines[1:]

        # Strip trailing blank lines
        while c_norm and not c_norm[-1].strip():
            c_norm.pop()
        while h_norm and not h_norm[-1].strip():
            h_norm.pop()

        diff = list(difflib.unified_diff(
            c_norm, h_norm,
            fromfile=f"contracts/GuardrailCourt.py:{c_name}",
            tofile=f"contracts/guardrail_helpers.py:{h_name}",
            lineterm=""
        ))

        print(f"--- Function: {label} ---")
        if not diff:
            print("diff rong: Code body, branch logic, and type annotations match 100% line-by-line.\n")
        else:
            print("DETECTED CODE DIFF:")
            for d in diff:
                print(d)
            print()
            all_match = False

    if all_match:
        print("RESULT: 5/5 pure helper functions have diff rong (byte-for-byte logic match after export name normalization).")
        sys.exit(0)
    else:
        print("RESULT: Source code mismatch detected!")
        sys.exit(1)

if __name__ == "__main__":
    compare_parity()
