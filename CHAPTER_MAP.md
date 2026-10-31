# Chapter map

The second-edition candidate retains eighteen chapters. This map distinguishes implemented mechanisms from their limits; it does not establish public release or publication.

| Chapters | Current files | State |
|---|---|---|
| 1–6: evaluation and evidence | fixtures/quality.json, fixtures/security.json, security_lab/runner.py, starter.py, model_eval.py | Stub quality and deterministic policy comparison; separate owned CPU model setup and known-case evaluation |
| 7: exposure | security_lab/service.py, security_lab/drills.py | Owned temporary loopback HTTP only; no production gateway or backend protection claim |
| 8–11: access, retrieved injection, tools | security_lab/policy.py, service.py, model_eval.py | Ephemeral server-owned credentials, finite real-model observations and external tool checks; no production identity provider |
| 12: output handling | security_lab/protocol.py, model_eval.py, runner.py | Strict JSON/schema including numeric-overflow rejection, distinct provider adapters and HTML-escaped evidence |
| 13: provenance | security_lab/recovery.py, fixtures/trusted-manifest.json | Trusted-reference fixture checks and tamper control; no full supply-chain attestation |
| 14: resource bounds | security_lab/service.py, drills.py, starter.py, model_eval.py | Body/worker/connection and process-local token quota; inspected CPU/memory container limits and bounded client responses; no GPU cancellation or cross-restart budget |
| 15: audit | security_lab/policy.py, tests/test_lab.py | Minimal in-memory events; no persistent audit service |
| 16–18: incident/recovery/release | security_lab/recovery.py, drills.py, edition-manifest.json | Synthetic data-only fresh restore with bounded reads/exact schema version, current revocation checks; code edition book-v2.0.0; verify its immutable release commit separately |

Future work must meet the book's evidence contracts; this table prevents planned features from being described as delivered.
