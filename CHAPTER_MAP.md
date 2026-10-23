# Chapter map

The eighteen-chapter book direction is approved. Code remains under first-edition review; the mapping below distinguishes delivered mechanisms from their limits.

| Proposed chapters | Current files | State |
|---|---|---|
| 1–6: evaluation and evidence | fixtures/quality.json, fixtures/security.json, security_lab/runner.py | Stub quality cases and deterministic policy comparison |
| 7: exposure | security_lab/service.py, security_lab/drills.py | Owned temporary loopback HTTP only; no production gateway or backend protection claim |
| 8–11: access, retrieved injection, tools | security_lab/policy.py, service.py, model_eval.py | Ephemeral server-owned credentials, finite real-model observations and external tool checks; no production identity provider |
| 12: output handling | security_lab/protocol.py, model_eval.py, runner.py | Strict JSON/schema and HTML-escaped evidence |
| 13: provenance | security_lab/recovery.py, fixtures/trusted-manifest.json | Trusted-reference fixture checks and tamper control; no full supply-chain attestation |
| 14: resource bounds | security_lab/service.py, drills.py | Body/worker/connection and process-local token quota; no GPU cancellation or cross-restart budget |
| 15: audit | security_lab/policy.py, tests/test_lab.py | Minimal in-memory events; no persistent audit service |
| 16–18: incident/recovery/release | security_lab/recovery.py, drills.py, edition-manifest.json | Synthetic data-only fresh restore and current revocation checks; immutable edition freeze still pending |

Future work must meet the book's evidence contracts; this table prevents planned features from being described as delivered.
