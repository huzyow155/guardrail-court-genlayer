import json

with open('scripts/deploy/live_evidence.json') as f:
    live = json.load(f)

print(f"{'Run Key':<30} | {'Tx Hash':<66} | {'latencySec'}")
print("-" * 115)
for k, v in live['runs'].items():
    if k == 'e_velocity_sequence':
        for idx, sv in enumerate(v, 1):
            run_name = f"{k}.slice_{idx}"
            print(f"{run_name:<30} | {sv['tx']:<66} | {sv.get('latencySec')}")
    else:
        print(f"{k:<30} | {v['tx']:<66} | {v.get('latencySec')}")
