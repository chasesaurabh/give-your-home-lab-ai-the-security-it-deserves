# Version and environment matrix

| Component | Current status |
|---|---|
| Python | 3.12.14 tested on Windows; use a maintained security patch for your environment |
| OS | Windows host; exact reported version in private book evidence / generated run report |
| Third-party Python dependencies | None; requirements.txt records the empty application dependency set |
| Python/OS vulnerabilities | Not covered by an empty package set; review maintained patches and official advisories before release |
| Models / serving runtimes | Finite local run with vLLM 0.30.0 and alias nemotron-super-120b-fp4. Read-only server configuration names NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4; alias/provider metadata do not attest loaded weights. |
| Containers | Core lab needs none; the separate model runtime was observed in a container read-only. No container-isolation test is claimed. |
| Linux / macOS | Not tested |
| Security/dependency audit tools | Gitleaks 8.30.1 staged/history scans plus bounded privacy/import preflight; no complete runtime/OS vulnerability audit implied |

No cross-platform or performance claims follow from this initial matrix. Pin the actual reader environment and any later dependencies/model artifacts at edition freeze, and reproduce from a clean checkout. Empty requirements are intentional, not a missing lockfile.

## Second-edition CPU starter, October 30, 2026

The earlier table describes the first release. The second-edition code adds an owned CPU starter. A separate clean local clone and no-pip virtual environment reproduced all22tests,23drills and the CPU lifecycle using the existing runtime/model cache. This is local checkout reproduction, not a fresh OS or independently downloaded public release. Use the release commit as the exact code reference.

| Component | Observed refresh setup |
|---|---|
| Python | 3.12.14, Windows AMD64; 22 acceptance methods passed |
| Docker engine | 29.8.0, Linux x86_64; 24 logical CPUs and 67,310,301,184 bytes RAM visible to engine |
| Container limits | Eight CPU equivalents, 6 GiB RAM, no additional swap allowance; no GPU requested |
| Ollama | 0.40.12, image digest `sha256:20d1bbfbabe1c97ba4b16301f08a20d8484bcf77047742a3cb71c613d8e12d0b` |
| Model | `qwen3:4b-instruct-2507-q4_K_M`, manifest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` |
| Loaded-model report | Q4_K_M, 4,096 context, reported GPU allocation zero |
| Clean-helper run | Fresh model volume; sixteen parsed attempts; quality 2/6, legitimate tool controls 0/2, injection no-proposal 8/8 |
| Recovery | Stopped server produced URLError; restarted server produced schema-valid M01, retaining its wrong citation |
| Cleanup | Owned container and network removed; named model volume retained |

The image was already in the host cache, then pulled/checked by digest. The model volume was new and its model download completed. This is not a fresh operating-system or empty-image-cache installation test. Docker reported image size 8,472,901,144 bytes; that is not compressed network download size or total disk needed. The post-evaluation container snapshot was 5.395 GiB of its 6 GiB limit, **not peak memory**. Model-file size alone does not determine host RAM needs.

The first fresh-volume run exposed a Windows locale decoding error in Docker progress capture. After keeping subprocess streams as bytes and decoding successful stdout explicitly as UTF-8, the second fresh-volume run completed without that diagnostic and retained identical case-level answer/citation/proposal outcomes. The failure was preserved; it was not erased by the rerun.

No unseen-case benchmark, GPU comparison, Linux-host/macOS qualification, egress-isolation test, production authentication or independent loaded-weight attestation is claimed. The familiar corpus and prompt were unchanged. These scores describe the observed setup, not model suitability for every application.


## Partial-setup recovery correction — October 31 UTC / October 30 Chicago

A later review found that a failed container creation followed by failed network cleanup could leave a report that said to inspect an ID it had not recorded. The corrected starter saves the network ID immediately after acquisition. Controlled fault-injection runs used real disposable Docker networks: the original omitted the ID, and the corrected run retained the exact ID. The harness removed each exact network and verified its absence. No container or model ran in this failure-path test. All 23 current acceptance tests passed, including the new regression; the 22-test/model lifecycle observation above remains historical. The model request, fixture and scoring code are unchanged. A later complete lifecycle of the corrected implementation is recorded below; public-reader acquisition remains a separate check.


## Corrected implementation reproduction — October 31 UTC / October 30 Chicago

A clean Git archive of private source commit 9e81f276001dd63c51894543a3000d03ee4cd473 and a newly created no-pip environment passed all 23 acceptance methods, 23/23 service/recovery contracts and the expected baseline contrast. Every implementation digest matched the archive bytes. The complete CPU lifecycle returned 16 parsed attempts, quality 2/6, legitimate tool controls 0/2 and injection no-proposal 8/8. The stopped-provider request failed and restart returned a schema-valid response; these are lifecycle observations, not improved model quality. The exact owned container and network were removed and their absence independently inspected. Runtime/model downloads were cached; no fresh OS or public-download reproduction is claimed. The published implementation digests identify these executed bytes.
