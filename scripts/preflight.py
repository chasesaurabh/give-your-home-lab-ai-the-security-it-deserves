"""Bounded first-pass privacy/secret/import inventory. Not a full security audit."""

import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = {".gitignore", ".gitattributes", "README.md", "LICENSE", "SECURITY.md",
              "CONTRIBUTING.md", "VERSION_MATRIX.md", "CHAPTER_MAP.md",
              "requirements.txt", "edition-manifest.json"}
DIRECTORIES = {"security_lab", "fixtures", "tests", "scripts"}
PATTERNS = {
    "github_token": r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b",
    "aws_access_key": r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "provider_key": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b",
    "local_windows_path": r"[A-Za-z]:[\\/](?:Users|Saurabh)[\\/]",
    "email_address": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
}


def inspect():
    files, findings, modules = [], [], set()
    for entry in sorted(ROOT.iterdir()):
        if entry.name in {".git", "reports", "__pycache__"}:
            continue
        if entry.is_file() and entry.name in ROOT_FILES:
            files.append(entry)
        elif entry.is_dir() and entry.name in DIRECTORIES:
            for path in sorted(entry.rglob("*")):
                if "__pycache__" in path.parts:
                    continue
                if path.is_file():
                    files.append(path)
        else:
            findings.append({"path": entry.name, "rule": "unapproved_root_entry"})
    digests = {}
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix not in {".md", ".json", ".py", ".txt"} and path.name not in {".gitignore", ".gitattributes", "LICENSE"}:
            findings.append({"path": relative, "rule": "unapproved_file_type"})
            continue
        raw = path.read_bytes()
        content = raw.decode("utf-8")
        digests[relative] = hashlib.sha256(raw).hexdigest()
        for rule, pattern in PATTERNS.items():
            if re.search(pattern, content):
                # Report only path and rule, never the potential secret itself.
                findings.append({"path": relative, "rule": rule})
        if path.suffix == ".py":
            for node in ast.walk(ast.parse(content)):
                if isinstance(node, ast.Import):
                    modules.update(item.name.split(".")[0] for item in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    modules.add(node.module.split(".")[0])
    external = sorted(modules - sys.stdlib_module_names - {"security_lab"})
    if external:
        findings.append({"path": "Python import inventory", "rule": "external_dependencies"})
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    if any(line.strip() and not line.lstrip().startswith("#") for line in requirements):
        findings.append({"path": "requirements.txt", "rule": "dependency_review_needed"})
    return {"scope": "allowlisted working files only; excludes git, reports and caches",
            "files_checked": len(digests), "file_sha256": digests,
            "imports": sorted(modules), "third_party_imports": external,
            "findings": findings,
            "limitations": ["Pattern checks miss many secrets and personal-data forms.",
                            "No git history exists yet; history must be scanned before release.",
                            "Import inventory is not a vulnerability-database audit.",
                            "Python runtime and OS require separate patch/advisory review.",
                            "Manual private-data and license review remains required."]}


if __name__ == "__main__":
    report = inspect()
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report["findings"]))
