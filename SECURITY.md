# Security policy and lab scope

Only test systems you own or are explicitly authorized to test. This prototype has no network client/server and cannot target third parties. Unsafe examples operate only on synthetic in-memory dictionaries. Do not add real documents, tokens, logs, device controls, arbitrary shell execution, or unbounded tools.

Current limitations: no production identity provider, process isolation, secure secret store, encryption, network boundary, model adapter, persistent audit, deadline or cumulative resource enforcement. The strict policy is a small teaching example and must not be advertised as complete protection.

Use the repository's private vulnerability-reporting facility if enabled. If it is unavailable, open an issue asking for a private reporting route without posting sensitive details, secrets, exploit data or private logs. A private contact address has not been supplied, so none is invented here. No response-time promise is made for the prototype.

Never copy a credential or private document into an issue or pull request. Use synthetic reproduction and minimal evidence. The author approved MIT and public code distribution on October 23, 2026. Secret/private-data and dependency checks precede each push and release. Recheck these before each edition tag.
