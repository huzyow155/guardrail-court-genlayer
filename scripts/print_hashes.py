import hashlib
import os

FILES_TO_CHECK = [
    "contracts/GuardrailCourt.py",
    "contracts/GuardrailCourtV2.py",
    "examples/consumer/GuardedVaultV2.py",
    "docs/V2_DESIGN.md",
    "docs/ERROR_CODES.md",
    "tests/test_v2_parser.py",
    "tests/test_v2_guards.py",
    "tests/test_v2_binding.py",
    "tests/test_v2_lifecycle.py",
    "tests/test_v2_vault.py",
]

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print(f"| {'File':<40} | {'SHA-256 Checksum':<64} | {'Status':<10} |")
    print(f"|{'-'*42}|{'-'*66}|{'-'*12}|")
    for fpath in FILES_TO_CHECK:
        if os.path.exists(fpath):
            checksum = get_sha256(fpath)
            status = "FOUND"
        else:
            checksum = "NOT_FOUND"
            status = "MISSING"
        print(f"| `{fpath}`{' '*(38-len(fpath))} | `{checksum}` | {status:<10} |")

if __name__ == "__main__":
    main()
