import sys
import os

def check_ascii(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    non_ascii = []
    lines = data.split(b'\n')
    for line_no, line in enumerate(lines, 1):
        for col_no, byte in enumerate(line, 1):
            if byte > 127:
                non_ascii.append((line_no, col_no, byte, chr(byte) if byte < 256 else '?'))
    
    if non_ascii:
        print(f"FAILED: Non-ASCII characters found in {filepath}:")
        for line_no, col_no, byte, char in non_ascii[:20]:
            print(f"  Line {line_no}, Col {col_no}: byte 0x{byte:02x} ({char})")
        return False
    else:
        print(f"PASSED: {filepath} is pure ASCII ({len(data)} bytes).")
        return True

if __name__ == '__main__':
    targets = [sys.argv[1]] if len(sys.argv) > 1 else ['contracts', 'examples/consumer']
    all_ok = True
    for target in targets:
        if os.path.isfile(target):
            if not check_ascii(target):
                all_ok = False
        elif os.path.isdir(target):
            for root, dirs, files in os.walk(target):
                for file in files:
                    if file.endswith('.py'):
                        p = os.path.join(root, file)
                        if not check_ascii(p):
                            all_ok = False
    sys.exit(0 if all_ok else 1)
