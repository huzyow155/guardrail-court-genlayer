import os
import sys

DIRECTORIES = ["contracts", "examples", "docs", "tests"]

def scan_file(filepath):
    non_ascii = []
    with open(filepath, "rb") as f:
        content = f.read()
    for idx, byte_val in enumerate(content):
        if byte_val > 127:
            non_ascii.append((idx, byte_val))
    return len(content), non_ascii

def main():
    total_files = 0
    total_bytes = 0
    violations = 0
    
    print(f"| {'Directory / File':<45} | {'Bytes':<10} | {'Non-ASCII Bytes':<16} | {'Status':<6} |")
    print(f"|{'-'*47}|{'-'*12}|{'-'*18}|{'-'*8}|")

    for directory in DIRECTORIES:
        if not os.path.exists(directory):
            continue
        for root, _, files in os.walk(directory):
            for fname in files:
                # Only check relevant text files: python, markdown, json
                if fname.endswith((".py", ".md", ".json", ".txt", ".js")):
                    fpath = os.path.join(root, fname).replace("\\", "/")
                    size, bad_bytes = scan_file(fpath)
                    total_files += 1
                    total_bytes += size
                    status = "OK" if len(bad_bytes) == 0 else "FAIL"
                    if len(bad_bytes) > 0:
                        violations += 1
                    print(f"| `{fpath}`{' '*(43-len(fpath))} | {size:<10} | {len(bad_bytes):<16} | {status:<6} |")

    print(f"\nScanned {total_files} files ({total_bytes} bytes). Total files with non-ASCII: {violations}")
    if violations > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
