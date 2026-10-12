import subprocess
import sys

pattern = r'risk_score|reason_code|JUDGE_PARSE_FAIL|window_duration|window_spent|created_at|resolved_at|metadata_hash|action_id|action_type|"actor"|justification|hard_limit_cap|agent_address|\b385\b|DNS_RENEWAL|CASINO_CHIPS|GIFT_CARD|0x538d5D|0x4b78A8|rolling|per hour|3600'
res = subprocess.run(['git', 'grep', '-n', '-i', '-E', pattern, '--', '.', ':!node_modules'], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print('STDERR:', res.stderr, file=sys.stderr)
