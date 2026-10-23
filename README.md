# Local AI Security Lab

Dedicated companion for **Give Your Home Lab AI the Security It Deserves: Test Your Models, Protect Your Data, and Keep Your Agents Under Control**.

**Planning prototype, not the finished book lab.** No real model is loaded or called. This version demonstrates finite in-process application authorization and evidence reporting. It does not authenticate real users, expose a server, provide OS isolation, or establish real-model answer quality, injection resistance, network protection, or resource containment.

## Run the prototype

Install Python 3.12 from its official distributor, with an appropriate maintained security patch. Only Python's standard library is needed; no package installation, model weights, Docker or cloud key is required. Run these commands from this directory:

```powershell
python -m unittest discover -s tests -v
python -m security_lab --output reports/first-run
```

If Windows maps `python` to the Microsoft Store, select your installed interpreter or use the corresponding `py -3.12` command. Current testing details belong in VERSION_MATRIX.md; an untested OS is not qualified merely because Python supports it.

The lab reads only its synthetic fixtures, evaluates proposals against two in-process adapters, and writes `report.json` and `report.html` into a newly created output directory. It refuses to reuse an existing output directory so old evidence is not silently replaced. Open the HTML locally. No JavaScript, remote assets, external network requests, arbitrary commands, real files as tool targets, or third-party attack targets are used.

Sixteen security cases include two legitimate allow controls and fourteen deny cases. The intentionally unsafe adapter accepts every proposal; the hardened adapter validates a trusted synthetic request context, strict proposal shape, tool/argument allowlists, project scope and a small logical step count. The model cannot provide the trusted context. The unsafe adapter cannot run shell commands or access a real filesystem: its entire data store is synthetic and in memory.

Three fixed quality examples are reported separately. Two satisfy their exact-answer/citation-or-abstention rubric; one intentionally wrong citation fails. Those are **stub fixtures**, not model evaluations. The command exits successfully only when the expected demonstration holds: all hardened cases match expected behavior, the unsafe control exposes the intended failures, and the quality fixture retains its known failure. A 2/3 stub score is not a quality acceptance threshold for any model.

## Evidence and boundaries

Reports include UTC run time, OS/runtime, source and fixture digests, case IDs, expected/observed decisions, reasons, and limitations. Raw prompts/documents/results and canaries are excluded from reports and minimal audit events. Report text is HTML-escaped. Digests identify the bytes actually read; without a separately trusted release manifest they do not authenticate those bytes.

The work-step value here is a logical test input, not metered CPU/GPU work, token count, deadline, cancellation or a per-user cumulative quota. The application context is supplied by the harness, not a real authentication layer. The hardened adapter is a teaching slice, not a sandbox or production authorization service. Finite passes cannot establish perfect security.

See [CHAPTER_MAP.md](CHAPTER_MAP.md), [SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md), [VERSION_MATRIX.md](VERSION_MATRIX.md) and [edition-manifest.json](edition-manifest.json).

## License and edition

Original code and synthetic fixtures are licensed under the MIT License; see LICENSE. The author selected MIT on October 23, 2026. Original synthetic fixtures contain no real user records or valid credentials. No third-party package/model assets are bundled. Book prose and production assets are outside this repository and are not covered by its code license.

The planned first-edition tag is `book-v1.0.0`; **it does not exist yet**. The release manifest must record the tested immutable commit and successful clean-checkout evidence before the book cites a frozen edition. No book manuscript, cover, production asset, private research or personal information belongs in this repository.

**Book availability:** publication pending. A verified link to the published book will be added here after a stable public book page exists. No retailer URL is available yet.
