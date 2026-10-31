# Security policy and lab scope

Only test systems you own or are explicitly authorized to test. The default baseline is offline. The owned service drill binds numeric loopback; the optional model client accepts only explicitly selected numeric-loopback endpoints and refuses redirects/proxies. Unsafe examples operate only on synthetic in-memory dictionaries. Do not add real documents, credentials, private logs, device controls, arbitrary shell execution or unbounded tools.

Current limitations: no production identity provider, process isolation, secure secret store, encryption, LAN/TLS gateway, persistent audit, cross-restart quota or upstream inference cancellation. Finite connection lifetime and process-local work quota are limited fixture controls. Python http.server is not for production. Policy and model adapter are teaching examples, not complete protection.

Use the repository's private vulnerability-reporting facility if enabled. If it is unavailable, open an issue asking for a private reporting route without posting sensitive details, secrets, exploit data or private logs. A private contact address has not been supplied, so none is invented here. No response-time promise is made for this educational companion.

Never copy a credential or private document into an issue or pull request. Use synthetic reproduction and minimal evidence. The first edition was publicly distributed under MIT; that historical approval does not establish release of this candidate. Secret/private-data and dependency checks precede each push and release. Recheck these before each edition tag.
