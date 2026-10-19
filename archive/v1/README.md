# Archive: Guardrail Court V1 (SUPERSEDED)

> **WARNING: DO NOT INTEGRATE OR USE GUARDRAIL COURT V1 IN PRODUCTION.**
>
> The files in this directory represent the historical **Guardrail Court V1** release (`0x6C553Ba27a768D71b570a106D9D2e13553b4103c`) and its consumer (`0x8849b28f8a1a5B1d0b38FE67c2980Cbb80f24e93`).
> This version has been **completely superseded by Guardrail Court V2** (`contracts/GuardrailCourtV2.py`, deployed at `0xF5797dDB4ce419ec50351BF9B48D5C24D5330d7b`).

---

## Why V1 is Archived
V1 is preserved in this repository solely because its on-chain deployment on GenLayer Studionet is immutable, and its execution evidence is preserved for historical auditability and reproducible verification.

The reviewer identified critical structural flaws in the V1 design:

1. **Parser Substring Fallback (Fail-Open Vulnerability)**:
   - When JSON parsing failed, `contracts/GuardrailCourt.py` ran a substring fallback that scanned raw upper-cased text for `'"VERDICT": "ALLOW"' in upper_text` before checking `DENY`.
   - Any model response outputting explanatory prose quoting an `ALLOW` fragment (such as a refusal or negation: `The model refuses; "VERDICT": "ALLOW" is wrong`) was erroneously accepted by the fallback branch as `ALLOW`.
2. **Unbound Advisory Clearance (`is_cleared`)**:
   - In V1, `is_cleared(decision_id)` returned a naked boolean flag indicating whether the decision status was `CLEARED`.
   - The clearance was not bound to the action's recipient, asset, amount, or calldata hash. Downstream consumers could not cryptographically verify what action was cleared, permitting replay or parameter substitution.
3. **Unescaped Prompt Boundaries**:
   - V1 delimited prompt context using plain-text markers (`=== BEGIN REQUESTED ACTION ===`) without JSON encapsulation, leaving prompt boundaries susceptible to delimiter-spoofing injection attacks.

---

## Superseded V1 Files in this Directory
- [`GuardrailCourt.py`](GuardrailCourt.py): Superseded V1 court contract (`0x6C553Ba27a768D71b570a106D9D2e13553b4103c`, SHA-256: `dd3c61182f299699a55a3ffefb64fb472dba0b37c7b68def92235a577e179bbc`).
- [`GuardedVault.py`](GuardedVault.py): Superseded V1 vault consumer (`0x8849b28f8a1a5B1d0b38FE67c2980Cbb80f24e93`).
- [`LIMITATIONS_V1.md`](LIMITATIONS_V1.md): Superseded limitations document detailing V1 parser flaws and window mechanics.
- [`docs/`](docs/): Historical V1 documentation (`DESIGN_V1.md`, `INTEGRATION_V1.md`, `VERIFICATION_V1.md`, `ERROR_CODES_V1.md`, `RECEIPTS_V1.md`).
- Historical probe and milestone artifacts: `GuardrailCourtCore.py`, `Probe.py`, `guardrail_helpers.py`, `guardrail_types.py`, `check_parity.py`, `diff_helpers.py`, `find_hallucinations.py`, `tx_raw.json`.

---

## Active Contract
For all active integrations, tests, and documentation, refer exclusively to **Guardrail Court V2**:
- Main Contract: `contracts/GuardrailCourtV2.py`
- Main Consumer: `examples/consumer/GuardedVaultV2.py`
- Integration Guide: `docs/INTEGRATION.md`
- Verification Registry: `docs/VERIFICATION.md`
- Design Specifications: `docs/DESIGN.md`
- Current Limitations: `docs/LIMITATIONS.md`
