# Local AI Security Lab

Dedicated companion for **Give Your Home Lab AI the Security It Deserves: Test Your Models, Protect Your Data, and Keep Your Agents Under Control**.

Bench is a dedicated synthetic local AI security lab, still under book-edition review. It separates task quality from security contracts, compares in-process unsafe/hardened controls, and rehearses owned HTTP, provenance and recovery boundaries. An optional local-model adapter has measured finite synthetic cases. This is educational code, not a production service, sandbox, certification or promise of perfect security.

## Run the prototype

Install Python 3.12 from its official distributor, with an appropriate maintained security patch. Only Python's standard library is needed; no package installation, model weights, Docker or cloud key is required. Run these commands from this directory:

```powershell
python -m unittest discover -s tests -v
python -m security_lab --output reports/first-run
```

If Windows maps `python` to the Microsoft Store, select your installed interpreter or use the corresponding `py -3.12` command. Current testing details belong in VERSION_MATRIX.md; an untested OS is not qualified merely because Python supports it.

The baseline reads only its synthetic fixtures, evaluates proposals against two in-process adapters, and writes `report.json` and `report.html` into a newly created output directory. It refuses to reuse an existing output directory so old evidence is not silently replaced. Open the HTML locally. No executable JavaScript, remote assets, arbitrary commands, real files as tool targets or third-party attack targets are used. The default baseline makes no network requests; the separate drills and optional model command use only explicit numeric loopback.

Sixteen security cases include two legitimate allow controls and fourteen deny cases. The intentionally unsafe adapter accepts every proposal; the hardened adapter validates a trusted synthetic request context, strict proposal shape, tool/argument allowlists, project scope and a small logical step count. The model cannot provide the trusted context. The unsafe adapter cannot run shell commands or access a real filesystem: its entire data store is synthetic and in memory.

Three fixed quality examples are reported separately. Two satisfy their exact-answer/citation-or-abstention rubric; one intentionally wrong citation fails. Those are **stub fixtures**, not model evaluations. The command exits successfully only when the expected demonstration holds: all hardened cases match expected behavior, the unsafe control exposes the intended failures, and the quality fixture retains its known failure. A 2/3 stub score is not a quality acceptance threshold for any model.

## Evidence and boundaries

Reports include UTC run time, OS/runtime, source and fixture digests, case IDs, expected/observed decisions, reasons, and limitations. Raw prompts/documents/results and canaries are excluded from reports and minimal audit events. Report text is HTML-escaped. Digests identify the bytes actually read; without a separately trusted release manifest they do not authenticate those bytes.

The baseline work-step value is a logical test input, not metered CPU/GPU work, token count or a deadline. Its request context comes from the harness. The owned HTTP fixture separately maps ephemeral credentials to server-owned scope and implements connection/worker/body limits and a process-local request quota. None is a sandbox, production identity service or upstream inference-cancellation mechanism. Finite passes cannot establish perfect security.

## Owned service and recovery drills

```powershell
python -m security_lab.drills --output reports/drills
```

This command starts its own temporary loopback-only HTTP fixture and disposable synthetic state, then cleans up/stops them. The service has a strict Host check, rejects Origin, validates JSON framing/schema, uses a 4,096-byte body limit, defaults to four workers and a two-second connection timer, and permits eight charged requests per ephemeral token for that process lifetime. The in-memory audit keeps at most 64 minimal events. The drill uses special smaller limits and reports its settings. It includes tamper rejection, data-only backup, fresh restore and preserved revocation. Development evidence matched 23/23 finite drill contracts; the acceptance suite passed 16 tests. The timer is subject to OS scheduling, not a hard real-time guarantee.

Python http.server is explicitly unsuitable for production. No TLS, LAN/firewall rule, reverse proxy, real model backend, OS isolation, secure secret store, encrypted backup or durable audit is supplied. A separately running model service retains its own bypass/exposure risks. Current revocation policy remains outside data backups.

## Optional owned-model evaluation

Only use an endpoint you own or are explicitly authorized to test. Replace port and alias with your actual numeric-loopback server. The client refuses remote hosts, inherited proxies and redirects. The chat-completions request includes a vLLM-compatible template option; other runtimes need a reviewed adapter.

```powershell
python -m security_lab.model_eval --endpoint http://127.0.0.1:8100/v1 --model YOUR_LOCAL_ALIAS --repeats 2 --output reports/model
```

Requests are sequential, at most three repeats over eight synthetic cases, with 256 requested output tokens. The read timeout does not establish a hard inference deadline or server-side cancellation. The development run had 16 parsed attempts: 4/6 quality attempts passed the exact answer/citation rubric; 2/2 benign status proposals worked; among eight injection attempts, six emitted no proposal and two emitted cross-project proposals denied by external policy. Preserve wrong citations and rejected proposals. Temperature-zero repeats are not independent statistical trials, and these repository-visible holdout cases cease to be unseen after inspection.

Read LAB_GUIDE.md before interpreting reports. The fixture manifest detects changes relative to the separately trusted code edition; it is not an authenticity signature. Raw synthetic model output is evaluation evidence, separate from minimal application audit events. Never substitute private prompts or credentials into these fixtures without a different data/retention design.

See [CHAPTER_MAP.md](CHAPTER_MAP.md), [SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md), [VERSION_MATRIX.md](VERSION_MATRIX.md) and [edition-manifest.json](edition-manifest.json).

## License and edition

Original code and synthetic fixtures are licensed under the MIT License; see LICENSE. The author selected MIT on October 23, 2026. Original synthetic fixtures contain no real user records or valid credentials. No third-party package/model assets are bundled. Book prose and production assets are outside this repository and are not covered by its code license.

The planned first-edition tag is `book-v1.0.0`; **it does not exist yet**. The release manifest must record the tested immutable commit and successful clean-checkout evidence before the book cites a frozen edition. No book manuscript, cover, production asset, private research or personal information belongs in this repository.

**Book availability:** publication pending. A verified link to the published book will be added here after a stable public book page exists. No retailer URL is available yet.
