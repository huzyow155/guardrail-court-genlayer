# Archive: Historical Probe, Milestone 1 Core, and Audit Artifacts

The files in this directory are **not part of the main deployed production contract (`contracts/GuardrailCourt.py`)** and are retained solely as historical audit evidence:

- `GuardrailCourtCore.py`: Milestone 1 core prototype contract (`0x66066238a85609172263F3426fF00C8503871091`).
- `Probe.py`: Milestone 0 runtime probe contract (`0xCafd1A568d5A55eb7E1135F0Fe31137114D5Fe42`).
- `guardrail_helpers.py` & `guardrail_types.py`: Early standalone off-chain helper copies (superseded in Round 4 when all unit tests were wired directly to `contracts/GuardrailCourt.py` via `tests/genlayer_stub.py`).
- `check_parity.py` & `diff_helpers.py`: Round 4 audit scripts used to demonstrate the diff between `guardrail_helpers.py` and `GuardrailCourt.py`.
- `find_hallucinations.py`: Round 3 audit script used to scan for unverified terms.
- `tx_raw.json`: Raw RPC `eth_getTransactionByHash` response for deploy transaction `0xe7a7ec9e6e1b1cf9f07696d251dc08118b7c865121551107850abb2938d81136` used to extract `scripts/extracted_from_chain.py`.
