# Version and environment matrix

| Component | Current status |
|---|---|
| Python | 3.12.14 available at initialization; execution record determines tested status |
| OS | Windows host; exact reported version in private book evidence / generated run report |
| Third-party Python dependencies | None; requirements.txt records the empty application dependency set |
| Python/OS vulnerabilities | Not covered by an empty package set; review maintained patches and official advisories before release |
| Models / serving runtimes | None executed; no model metrics or compatibility claims |
| Containers | Not used by this prototype |
| Linux / macOS | Not tested |
| Security/dependency audit tools | Initial local pattern/privacy review only until separately recorded; no independent scan verdict invented |

No cross-platform or performance claims follow from this initial matrix. Pin the actual reader environment and any later dependencies/model artifacts at edition freeze, and reproduce from a clean checkout. Empty requirements are intentional, not a missing lockfile.
