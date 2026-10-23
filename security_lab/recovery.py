"""Synthetic data restoration with separately maintained revocation policy."""
import hashlib
import json
from pathlib import Path

from .protocol import strict_json


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_manifest(root):
    return {p.name:digest(p.read_bytes()) for p in sorted(Path(root).glob("*.json"))
            if p.name != "trusted-manifest.json"}


def verify_fixtures(root, trusted_manifest):
    actual = fixture_manifest(root)
    if actual != trusted_manifest:
        raise ValueError("Fixture set or content differs from trusted manifest")
    return True


def verify_packaged_fixtures(root):
    root=Path(root)
    return verify_fixtures(root,strict_json((root/"trusted-manifest.json").read_bytes()))


def make_backup(documents, destination):
    # Backups deliberately omit identities, credentials and security policy.
    raw = json.dumps({"schema":1, "documents":documents},sort_keys=True).encode()
    with Path(destination).open("xb") as output:
        output.write(raw)
    return digest(raw)


def restore_backup(source, expected_digest, destination):
    # Read one byte beyond the acceptance limit to detect overflow without
    # first materializing an arbitrarily large local file in process memory.
    with Path(source).open("rb") as incoming:
        raw = incoming.read(65537)
    if len(raw) > 65536 or digest(raw) != expected_digest:
        raise ValueError("Backup size or digest mismatch")
    value = strict_json(raw)
    if (type(value) is not dict or set(value) != {"schema","documents"}
            or type(value["schema"]) is not int or value["schema"] != 1):
        raise ValueError("Backup schema")
    documents = value["documents"]
    if type(documents) is not dict or any(type(k) is not str or type(v) is not dict for k,v in documents.items()):
        raise ValueError("Document schema")
    if any(type(k) is not str or type(v) is not str for project in documents.values() for k,v in project.items()):
        raise ValueError("Record schema")
    # A fresh target prevents silently replacing current state with an old backup.
    with Path(destination).open("x",encoding="utf-8") as output:
        json.dump(documents,output,sort_keys=True)
    return documents


def rotate_credential(identity_map, old_token, new_token, revoked):
    if old_token not in identity_map or new_token in identity_map or new_token in revoked:
        raise ValueError("Invalid synthetic rotation")
    identity_map[new_token] = identity_map.pop(old_token)
    revoked.add(old_token)


def reconcile_old_identity_snapshot(snapshot, current, revoked):
    # A data restore cannot remove current revocations or reactivate old identities.
    return {token:context for token,context in current.items() if token not in revoked}
