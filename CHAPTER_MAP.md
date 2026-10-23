# Chapter map

The proposed book outline is awaiting approval. This prototype implements only a bounded slice.

| Proposed chapters | Current files | State |
|---|---|---|
| 1–6: evaluation and evidence | fixtures/quality.json, fixtures/security.json, security_lab/runner.py | Stub quality cases and deterministic policy comparison |
| 7: exposure | None | Not implemented |
| 8–11: access, retrieved injection, tools | security_lab/policy.py, fixtures/documents.json | Synthetic trusted context and tool containment; no real authentication/model |
| 12: output handling | security_lab/runner.py | HTML-escaped evidence |
| 13: provenance | security_lab/runner.py | Byte digests only, not artifact authenticity or full supply-chain verification |
| 14: resource bounds | security_lab/policy.py | Logical step validation only |
| 15: audit | security_lab/policy.py, tests/test_lab.py | Minimal in-memory events; no persistent audit service |
| 16–18: incident/recovery/release | edition-manifest.json | Planning only; no recovery drill or frozen release |

Future work must meet the book's evidence contracts; this table prevents planned features from being described as delivered.
