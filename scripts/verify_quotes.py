import urllib.request
import re
import sys

QUOTES = [
    {
        "name": "NVIDIA NeMo Guardrails",
        "url": "https://github.com/NVIDIA-NeMo/Guardrails",
        "quote": "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."
    },
    {
        "name": "Open Policy Agent (GitHub)",
        "url": "https://github.com/open-policy-agent/opa",
        "quote": "Open Policy Agent (OPA) is an open source, general-purpose policy engine that enables unified, context-aware policy enforcement across the entire stack."
    },
    {
        "name": "Open Policy Agent (Docs Decoupling)",
        "url": "https://www.openpolicyagent.org/docs/latest/",
        "quote": "OPA decouples policy decision-making from policy enforcement."
    },
    {
        "name": "Cedar Policy Language",
        "url": "https://docs.cedarpolicy.com/",
        "quote": "Cedar is a language for writing authorization policies and making authorization decisions based on those policies."
    },
    {
        "name": "Safe Modules",
        "url": "https://github.com/safe-fndn/safe-modules",
        "quote": "A collection of modules that can be used with the Safe contract"
    },
    {
        "name": "Zodiac Protocol",
        "url": "https://github.com/gnosisguild/zodiac",
        "quote": "Zodiac is a collection of tools built according to an open standard."
    }
]

def normalize_text(text: str) -> str:
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode basic HTML entities
    text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def verify_all():
    req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    all_ok = True
    print("=== VERIFYING PRIOR ART QUOTES AGAINST SOURCE URLS ===")
    
    for item in QUOTES:
        name = item["name"]
        url = item["url"]
        quote = item["quote"]
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_html = resp.read().decode('utf-8', errors='ignore')
                norm_html = normalize_text(raw_html)
                
                norm_quote = re.sub(r'\s+', ' ', quote).strip()
                if norm_quote in norm_html:
                    print(f"[OK] {name}")
                    print(f"     URL: {url}")
                    print(f"     Quote: \"{norm_quote}\"\n")
                else:
                    print(f"[FAIL] {name}")
                    print(f"       URL: {url}")
                    print(f"       Quote: \"{norm_quote}\"\n")
                    all_ok = False
        except Exception as e:
            print(f"[ERROR] {name} ({url}): {e}\n")
            all_ok = False

    if all_ok:
        print("ALL QUOTES VERIFIED: Every quote is an exact, continuous verbatim substring of its live source page.")
        sys.exit(0)
    else:
        print("SOME QUOTES FAILED VERIFICATION.")
        sys.exit(1)

if __name__ == '__main__':
    verify_all()
