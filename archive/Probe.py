# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from genlayer import *


class Probe(gl.Contract):
    probe_results: str

    def __init__(self):
        sender = gl.message.sender_address
        sender_hex = sender.as_hex
        sender_str = str(sender)

        import hashlib
        import re

        test_hash = hashlib.sha256(b"guardrail_court_probe").hexdigest()[:12]
        re_ok = bool(re.match(r"^[0-9a-f]+$", test_hash))
        user_error_ok = (gl.vm.UserError.__name__ == "UserError")

        report = {
            "sender_address": sender_hex,
            "sender_str": sender_str,
            "hashlib_test": test_hash,
            "re_ok": re_ok,
            "user_error_class": "gl.vm.UserError" if user_error_ok else "UNKNOWN",
            "strict_eq_passed": False,
            "prompt_decision": "",
            "raw_gh_status": 0,
            "raw_gh_len": 0,
            "notfound_status": 0,
            "urllib_ok": False,
            "ipaddress_ok": False,
            "address_cls_available": False,
            "bool_view_works": True,
        }
        self.probe_results = json.dumps(report)

    @gl.public.view
    def get_results(self) -> str:
        return self.probe_results

    @gl.public.view
    def test_bool_view(self) -> bool:
        return True

    @gl.public.view
    def test_list_view(self) -> list[str]:
        return ["alpha", "beta"]

    @gl.public.write
    def probe_consensus(self) -> None:
        def compute_nondet() -> str:
            import urllib.parse
            import ipaddress
            import re

            split_res = urllib.parse.urlsplit("https://example.com/test")
            ip_obj = ipaddress.ip_address("127.0.0.1")
            urllib_ok = (split_res.hostname == "example.com")
            ipaddress_ok = ip_obj.is_loopback

            addr_available = False
            try:
                # Test if Address class is exposed in global scope
                addr_inst = Address("0x1111111111111111111111111111111111111111")
                addr_available = bool(addr_inst)
            except Exception:
                addr_available = False

            # Test prompt for deterministic single canonical output
            prompt_res = gl.nondet.exec_prompt(
                "Respond with exactly one word: PONG. Do not add any punctuation or other words."
            )
            raw_s = str(prompt_res).strip().upper()
            decision = "PONG" if "PONG" in raw_s else "UNKNOWN"

            # Deterministic static fixtures
            gh_url = "https://raw.githubusercontent.com/huzyow155/guardrail-court-genlayer/main/fixtures/policies.md"
            gh_status = 0
            gh_len = 0
            try:
                resp = gl.nondet.web.get(gh_url)
                gh_status = int(resp.status)
                body_bytes = resp.body
                body_str = body_bytes.decode("utf-8") if isinstance(body_bytes, (bytes, bytearray)) else str(body_bytes)
                gh_len = len(body_str)
            except Exception:
                gh_status = -1

            nf_url = "https://raw.githubusercontent.com/huzyow155/guardrail-court-genlayer/main/fixtures/nonexistent_404.md"
            nf_status = 0
            try:
                nfresp = gl.nondet.web.get(nf_url)
                nf_status = int(nfresp.status)
            except Exception:
                nf_status = -1

            # Produce single canonical string
            out_code = f"GH_{gh_status}_LEN_{gh_len}_NF_{nf_status}_DEC_{decision}_URL_{1 if urllib_ok else 0}_IP_{1 if ipaddress_ok else 0}_ADDR_{1 if addr_available else 0}"
            return out_code

        eq_val = gl.eq_principle.strict_eq(compute_nondet)

        curr = json.loads(self.probe_results)
        curr["strict_eq_passed"] = True
        curr["consensus_string"] = eq_val
        curr["raw_gh_status"] = 200 if "GH_200" in eq_val else 0
        curr["notfound_status"] = 404 if "NF_404" in eq_val else 0
        curr["urllib_ok"] = True if "URL_1" in eq_val else False
        curr["ipaddress_ok"] = True if "IP_1" in eq_val else False
        curr["prompt_decision"] = "PONG" if "DEC_PONG" in eq_val else "UNKNOWN"
        curr["address_cls_available"] = True if "ADDR_1" in eq_val else False
        self.probe_results = json.dumps(curr)
