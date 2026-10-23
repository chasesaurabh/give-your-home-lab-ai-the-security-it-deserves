import http.client
import json
from pathlib import Path
import secrets
import socket
import tempfile
import time
import unittest

from security_lab.policy import RequestContext, hardened
from security_lab.protocol import local_endpoint, strict_json
from security_lab.recovery import (fixture_manifest, make_backup, reconcile_old_identity_snapshot,
                                   restore_backup, rotate_credential, verify_fixtures)
from security_lab.runner import ROOT, load_fixture
from security_lab.service import owned_service

STATUS={"proposal":{"tool":"status","args":{"target":"bench"}}}


def post(server, token=None, value=STATUS, headers=None):
    connection=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
    raw=json.dumps(value)
    request_headers={"Content-Type":"application/json"}
    if token is not None:
        request_headers["Authorization"]="Bearer "+token
    request_headers.update(headers or {})
    connection.request("POST","/propose",body=raw,headers=request_headers)
    response=connection.getresponse()
    result=response.status,json.loads(response.read())
    connection.close()
    return result


class TransportAndRecoveryTests(unittest.TestCase):
    def test_raw_framing_and_json_rejections_reach_intended_guard(self):
        with owned_service(work_limit=30) as server:
            token=next(iter(server.credentials))
            scenarios=[
                ([("Content-Length","2"),("Content-Length","2")],b"{}",400,"framing"),
                ([("Transfer-Encoding","chunked"),("Content-Length","2")],b"{}",400,"framing"),
                ([("Content-Length","-1")],b"",400,"framing"),
                ([("Content-Length","0")],b"",413,"body_limit"),
                ([("Content-Length","2"),("Content-Type","text/plain")],b"{}",415,"content_type"),
                ([("Content-Length","5")],b"[1,2]",400,"request_schema"),
                ([("Content-Length","25")],b'{"proposal":null,"x":NaN}',400,"json"),
                ([],b'{"proposal":null,"proposal":null}',400,"json")]
            for headers,body,expected,reason in scenarios:
                with self.subTest(reason=reason,headers=[h[0] for h in headers]):
                    # For the non-finite case compute the exact wire length too.
                    if b"NaN" in body:
                        headers=[("Content-Length",str(len(body)))]
                    if not headers:
                        headers=[("Content-Length",str(len(body)))]
                    conn=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
                    conn.putrequest("POST","/propose",skip_host=True,skip_accept_encoding=True)
                    conn.putheader("Host",f"127.0.0.1:{server.server_port}")
                    conn.putheader("Authorization","Bearer "+token)
                    if not any(k=="Content-Type" for k,v in headers):
                        conn.putheader("Content-Type","application/json")
                    for key,value in headers:
                        conn.putheader(key,value)
                    conn.endheaders(body)
                    response=conn.getresponse()
                    data=json.loads(response.read())
                    self.assertEqual((response.status,data["reason"]),(expected,reason))
                    conn.close()

    def test_bounded_audit_evicts_old_events_under_real_requests(self):
        with owned_service(work_limit=80) as server:
            token=next(iter(server.credentials))
            self.assertEqual(post(server,token)[0],200)
            first=server.audit[0]["request_id"]
            for attempt in range(69):
                self.assertEqual(post(server,token)[0],200)
            self.assertEqual(len(server.audit),64)
            self.assertNotIn(first,{event.get("request_id") for event in server.audit})

    def test_loopback_auth_scope_and_no_raw_audit(self):
        with owned_service() as server:
            self.assertEqual(server.server_address[0],"127.0.0.1")
            token=next(iter(server.credentials))
            self.assertEqual(post(server)[0],401)
            self.assertEqual(post(server,token)[0],200)
            foreign={"proposal":{"tool":"read_document","args":{"project":"beta","document":"private"}}}
            self.assertEqual(post(server,token,foreign)[0],403)
            self.assertEqual(post(server,token,headers={"Origin":"http://untrusted.invalid"})[0],403)
            self.assertEqual(post(server,token,headers={"Host":"untrusted.invalid"})[0],403)
            self.assertNotIn(token,json.dumps(list(server.audit)))
            self.assertNotIn(server.documents["beta"]["private"],json.dumps(list(server.audit)))
            server.revoke(token)
            self.assertEqual(post(server,token)[0],401)

    def test_body_schema_duplicates_and_cumulative_quota(self):
        with owned_service(work_limit=4) as server:
            token=next(iter(server.credentials))
            self.assertEqual(post(server,token,{"proposal":STATUS["proposal"],"project":"beta"})[0],400)
            self.assertEqual(post(server,token,{"padding":"x"*4100})[0],413)
            self.assertEqual(post(server,token)[0],200)
            self.assertEqual(post(server,token)[0],200)
            self.assertEqual(post(server,token)[0],429)
        with self.assertRaises(ValueError):
            strict_json('{"project":"alpha","project":"beta"}')

    def test_absolute_connection_lifetime_and_concurrency_capacity(self):
        with owned_service(lifetime=0.3,workers=1) as server:
            first=socket.create_connection(server.server_address,timeout=2)
            first.sendall(b"POST /propose HTTP/1.1\r\n")
            time.sleep(0.03)
            with socket.create_connection(server.server_address,timeout=2) as second:
                self.assertIn(b"503",second.recv(128))
            start=time.monotonic()
            try:
                while first.recv(1024):
                    pass
            except ConnectionResetError:
                pass
            first.close()
            self.assertLess(time.monotonic()-start,1.5)
            # Capacity returns when the timed-out connection is closed.
            time.sleep(0.05)
            token=next(iter(server.credentials))
            self.assertEqual(post(server,token)[0],200)

    def test_recovery_preserves_scope_and_revocation(self):
        documents=load_fixture("documents.json")
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            backup=folder/"backup.json"
            checksum=make_backup(documents,backup)
            restored=restore_backup(backup,checksum,folder/"restored.json")
            self.assertEqual(restored,documents)
            proposal={"tool":"read_document","args":{"project":"beta","document":"private"}}
            self.assertFalse(hardened(proposal,RequestContext(True),1,restored).allowed)
            permitted={"tool":"read_document","args":{"project":"alpha","document":"runbook"}}
            self.assertTrue(hardened(permitted,RequestContext(True),1,restored).allowed)
            old,new=secrets.token_urlsafe(24),secrets.token_urlsafe(24)
            current={old:RequestContext(True)}
            stale=dict(current)
            revoked=set()
            rotate_credential(current,old,new,revoked)
            recovered=reconcile_old_identity_snapshot(stale,current,revoked)
            self.assertNotIn(old,recovered)
            self.assertIn(new,recovered)
            self.assertIn(old,revoked)
            with self.assertRaises(FileExistsError):
                restore_backup(backup,checksum,folder/"restored.json")
            backup.write_bytes(backup.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                restore_backup(backup,checksum,folder/"tampered.json")

    def test_fixture_tamper_negative_control_and_endpoint_restriction(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            item=folder/"fixture.json"
            item.write_text('{"synthetic":true}',encoding="utf-8")
            manifest=fixture_manifest(folder)
            self.assertTrue(verify_fixtures(folder,manifest))
            item.write_text('{"synthetic":false}',encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_fixtures(folder,manifest)
        self.assertEqual(local_endpoint("http://127.0.0.1:8100/v1/"),"http://127.0.0.1:8100/v1")
        for endpoint in ["http://example.invalid:80/v1","http://localhost:8100/v1",
                         "http://127.0.0.1:8100/v1?target=elsewhere",
                         "http://name:password@127.0.0.1:8100/v1"]:
            with self.assertRaises(ValueError):
                local_endpoint(endpoint)


if __name__=="__main__":
    unittest.main()
