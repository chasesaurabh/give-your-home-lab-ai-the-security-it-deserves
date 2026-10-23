# Version and environment matrix

| Component | Current status |
|---|---|
| Python | 3.12.14 tested on Windows; use a maintained security patch for your environment |
| OS | Windows host; exact reported version in private book evidence / generated run report |
| Third-party Python dependencies | None; requirements.txt records the empty application dependency set |
| Python/OS vulnerabilities | Not covered by an empty package set; review maintained patches and official advisories before release |
| Models / serving runtimes | Finite local run with vLLM 0.30.0 and alias nemotron-super-120b-fp4. Read-only server configuration names NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4; alias/provider metadata do not attest loaded weights. |
| Containers | Not used by this prototype |
| Linux / macOS | Not tested |
| Security/dependency audit tools | Gitleaks 8.30.1 staged/history scans plus bounded privacy/import preflight; no complete runtime/OS vulnerability audit implied |

No cross-platform or performance claims follow from this initial matrix. Pin the actual reader environment and any later dependencies/model artifacts at edition freeze, and reproduce from a clean checkout. Empty requirements are intentional, not a missing lockfile.
