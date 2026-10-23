"""Run owned HTTP, provenance and restore exercises; write finite evidence."""
import argparse
from datetime import datetime, timezone
import html
import http.client
import json
from pathlib import Path
import platform
import secrets
import socket
import tempfile
import time

from .policy import RequestContext, hardened
from .recovery import (fixture_manifest, make_backup, reconcile_old_identity_snapshot,
                       restore_backup, rotate_credential, verify_fixtures)
from .runner import ROOT, load_fixture
from .service import owned_service


def request(server, token, body, headers=None):
    connection=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
    selected={"Content-Type":"application/json"}
    if token:
        selected["Authorization"]="Bearer "+token
    selected.update(headers or {})
    connection.request("POST","/propose",json.dumps(body),selected)
    response=connection.getresponse()
    status=response.status
    response.read()
    connection.close()
    return status


def run(destination):
    from .recovery import verify_packaged_fixtures
    verify_packaged_fixtures(ROOT / "fixtures")
    folder=Path(destination)
    folder.mkdir(parents=True,exist_ok=False)
    rows=[]
    def record(name,expected,observed):
        rows.append({"case":name,"expected":expected,"observed":observed,"passed":observed==expected})
    status={"proposal":{"tool":"status","args":{"target":"bench"}}}
    with owned_service(work_limit=5) as server:
        token=next(iter(server.credentials))
        record("listener_loopback","127.0.0.1",server.server_address[0])
        record("anonymous_rejected",401,request(server,None,status))
        record("authorized_status",200,request(server,token,status))
        foreign={"proposal":{"tool":"read_document","args":{"project":"beta","document":"private"}}}
        record("cross_scope_rejected",403,request(server,token,foreign))
        record("origin_rejected",403,request(server,token,status,{"Origin":"http://untrusted.invalid"}))
        record("oversize_rejected",413,request(server,token,{"padding":"x"*4100}))
        record("fourth_charged_request",200,request(server,token,status))
        record("fifth_charged_request",200,request(server,token,status))
        record("quota_exhausted",429,request(server,token,status))
        serialized=json.dumps(list(server.audit))
        record("token_absent_from_audit",True,token not in serialized)
        record("document_absent_from_audit",True,server.documents["beta"]["private"] not in serialized)
        server.revoke(token)
        record("revocation_enforced",401,request(server,token,status))
    with owned_service(lifetime=.3,workers=1) as server:
        start=time.monotonic()
        first=socket.create_connection(server.server_address,timeout=2)
        first.sendall(b"POST /propose HTTP/1.1\r\n")
        time.sleep(.03)
        with socket.create_connection(server.server_address,timeout=2) as second:
            record("worker_capacity_rejected",True,b"503" in second.recv(128))
        try:
            while first.recv(1024):
                pass
        except ConnectionResetError:
            pass
        first.close()
        elapsed=time.monotonic()-start
        record("incomplete_connection_closed_within_1_5_seconds",True,elapsed<1.5)
        rows[-1]["elapsed_seconds"]=round(elapsed,4)
    with tempfile.TemporaryDirectory() as directory:
        work=Path(directory)
        fixtures=work/"fixtures"
        fixtures.mkdir()
        sample=fixtures/"owned.json"
        sample.write_text('{"synthetic":true}',encoding="utf-8")
        manifest=fixture_manifest(fixtures)
        record("known_fixture_accepted",True,verify_fixtures(fixtures,manifest))
        sample.write_text('{"synthetic":false}',encoding="utf-8")
        try:
            verify_fixtures(fixtures,manifest)
            rejected=False
        except ValueError:
            rejected=True
        record("tampered_fixture_rejected",True,rejected)
        backup=work/"backup.json"
        original=load_fixture("documents.json")
        digest=make_backup(original,backup)
        restored=restore_backup(backup,digest,work/"restored.json")
        record("fresh_restore_matches",True,original==restored)
        local={"tool":"read_document","args":{"project":"alpha","document":"runbook"}}
        foreign={"tool":"read_document","args":{"project":"beta","document":"private"}}
        record("restored_scoped_read_allowed",True,hardened(local,RequestContext(True),1,restored).allowed)
        record("restored_cross_scope_denied",False,hardened(foreign,RequestContext(True),1,restored).allowed)
        old,new=secrets.token_urlsafe(24),secrets.token_urlsafe(24)
        current={old:RequestContext(True)}
        stale=dict(current)
        revoked=set()
        rotate_credential(current,old,new,revoked)
        recovered=reconcile_old_identity_snapshot(stale,current,revoked)
        record("unsafe_identity_snapshot_would_reactivate_old",True,old in stale)
        record("revoked_token_not_restored",False,old in recovered)
        record("replacement_token_retained",True,new in recovered)
        backup.write_bytes(backup.read_bytes()+b" ")
        try:
            restore_backup(backup,digest,work/"wrong.json")
            rejected=False
        except ValueError:
            rejected=True
        record("tampered_backup_rejected",True,rejected)
    report={"run_utc":datetime.now(timezone.utc).isoformat(),"python":platform.python_version(),
            "os":platform.system(),"cases":rows,"passed":sum(r["passed"] for r in rows),"total":len(rows),
            "limitations":["Owned synthetic loopback fixture, not a production HTTP stack or TLS service.",
                           "Connection lifetime bounds the fixture connection, not upstream GPU inference.",
                           "Work quota is per throwaway token for this process lifetime; restart resets it.",
                           "No LAN/firewall, OS isolation, encryption-at-rest or physical-backup test.",
                           "Trusted manifests and revocation policy must be protected separately from backups.",
                           "Restore exercises only synthetic JSON state, not arbitrary software installations."]}
    (folder/"drill-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    (folder/"drill-report.html").write_text("<!doctype html><meta charset='utf-8'><title>Bench drills</title>"
        "<h1>Owned service and recovery drills</h1><pre style='white-space:pre-wrap'>"+
        html.escape(json.dumps(report,indent=2))+"</pre>",encoding="utf-8")
    print(f"Drill contracts: {report['passed']}/{report['total']}")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True)
    result=run(parser.parse_args().output)
    raise SystemExit(0 if result["passed"]==result["total"] else 1)
