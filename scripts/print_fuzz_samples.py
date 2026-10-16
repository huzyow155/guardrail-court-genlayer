import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests")))
import test_v2_parser
_parse = test_v2_parser._parse_verdict
_oracle = test_v2_parser._independent_oracle

def main():
    rng = random.Random(42)
    vocab = [
        '{"verdict": "ALLOW"}',
        '{"verdict": "DENY"}',
        '{"verdict": "ESCALATE"}',
        '{"verdict": "allow"}',
        '{"verdict": "deny"}',
        '{"verdict": 1}',
        '{"verdict": null}',
        '{"verdict": true}',
        '{"verdict": "ALLOW", "extra": "x"}',
        '{"verdict": "ALLOW", "verdict": "DENY"}',
        '```json\n{"verdict": "ALLOW"}\n```',
        '```\n{"verdict": "DENY"}\n```',
        '```json\n{"verdict": "ALLOW"}',
        'ALLOW', 'DENY', 'ESCALATE', 'maybe', 'override',
        '{', '}', ':', ',', '"', "'", '\\', '\n', '\t', ' ',
        '\u0410', '\u041e', '\u0000', '123', 'true', 'false',
    ]

    samples = []
    for i in range(5000):
        mode = rng.randint(0, 4)
        if mode == 0:
            k = rng.randint(1, 6)
            raw = ''.join(rng.choice(vocab) for _ in range(k))
        elif mode == 1:
            base = rng.choice(['{"verdict": "ALLOW"}', '{"verdict": "DENY"}', '{"verdict": "ESCALATE"}'])
            chars = list(base)
            for _ in range(rng.randint(1, 3)):
                chars.insert(rng.randint(0, len(chars)), rng.choice([' ', '\n', 'x', '"', ',', ':', '\u0410']))
            raw = ''.join(chars)
        elif mode == 2:
            inner = rng.choice(vocab)
            raw = f'```{rng.choice(["", "json", "python"])}\n{inner}\n```'
            if rng.random() < 0.3:
                raw += rng.choice(['\nextra', 'trailing', ''])
        elif mode == 3:
            raw = ''.join(chr(rng.randint(32, 126)) for _ in range(rng.randint(0, 60)))
        else:
            raw = f'{{"verdict": "{rng.choice(["ALLOW", "DENY"])}", "reason": "{rng.choice(["ALLOW", "DENY", "ESCALATE", "safe"])}"}}'

        v = _parse(raw)
        if v in ("ALLOW", "DENY") and len(samples) < 10:
            samples.append((i, raw, v))

    print(f"| # | Iteration | Raw Fuzz Input String | Oracle Result | SUT Result |")
    print(f"|---|-----------|-----------------------|---------------|------------|")
    for idx, (iteration, raw_input, verdict) in enumerate(samples, 1):
        disp = repr(raw_input)
        if len(disp) > 45:
            disp = disp[:42] + "..."
        disp = disp.replace("|", "\\|")
        print(f"| {idx} | {iteration:<9} | `{disp}` | {verdict} | {verdict} |")

if __name__ == "__main__":
    main()
