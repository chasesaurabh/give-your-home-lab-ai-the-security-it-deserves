import json
from pathlib import Path
import tempfile
import unittest

from security_lab.policy import RequestContext, audit_event, canary_found, hardened, unsafe
from security_lab.runner import build_report, load_fixture, render_html, write_report


class LabAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.documents = load_fixture("documents.json")
        self.context = RequestContext(True)
        self.canary = self.documents["beta"]["private"]

    def test_fixture_contracts_and_negative_control(self):
        report = build_report()
        self.assertTrue(report["demonstration_intact"])
        self.assertEqual(report["security_summary"]["hardened"], {"matched": 16, "total": 16})
        self.assertEqual(report["security_summary"]["unsafe"], {"matched": 2, "total": 16})
        self.assertEqual(report["quality_summary"]["passed"], 2)
        self.assertEqual(report["quality_summary"]["total"], 3)

    def test_canary_is_actually_exposed_only_in_synthetic_unsafe_path(self):
        proposal = {"tool": "read_document", "args": {"project": "beta", "document": "private"}}
        broken = unsafe(proposal, self.context, 1, self.documents)
        fixed = hardened(proposal, self.context, 1, self.documents)
        self.assertEqual(broken.payload, self.canary)
        self.assertFalse(fixed.allowed)
        self.assertEqual(fixed.payload, "")
        events = [audit_event("canary", "unsafe", broken), audit_event("canary", "hardened", fixed)]
        self.assertFalse(canary_found(events, self.canary))
        self.assertTrue(canary_found(events + [{"accidental_raw_output": self.canary}], self.canary))

    def test_all_report_evidence_excludes_raw_documents_and_payload(self):
        serialized = json.dumps(build_report())
        for project in self.documents.values():
            for raw_document in project.values():
                self.assertNotIn(raw_document, serialized)
        self.assertNotIn('"payload"', serialized)

    def test_unseen_proposal_shapes_cannot_crash_or_grant_authority(self):
        proposals = [[], True, 2, "status", {}, {"tool": []},
                     {"tool": {}, "args": {}},
                     {"tool": "status", "args": {"target": ["bench"]}},
                     {"tool": "status", "args": {"target": "b" * 65}},
                     {"tool": "read_document", "args": {"project": "alpha", "document": "../private"}}]
        for proposal in proposals:
            with self.subTest(proposal=proposal):
                self.assertFalse(hardened(proposal, self.context, 1, self.documents).allowed)

    def test_identity_is_supplied_outside_model_and_scope_is_not_hardcoded(self):
        proposal = {"tool": "read_document", "args": {"project": "beta", "document": "private"}}
        self.assertFalse(hardened(proposal, self.context, 1, self.documents).allowed)
        self.assertTrue(hardened(proposal, RequestContext(True, "synthetic-beta", "beta"), 1, self.documents).allowed)
        self.assertFalse(hardened(proposal, RequestContext(False, "synthetic-beta", "beta"), 1, self.documents).allowed)

    def test_html_labels_are_inert_and_reports_are_not_overwritten(self):
        report = build_report()
        rendered = render_html(report)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "new-run"
            write_report(report, destination)
            self.assertEqual(json.loads((destination / "report.json").read_text(encoding="utf-8")), report)
            with self.assertRaises(FileExistsError):
                write_report(report, destination)


if __name__ == "__main__":
    unittest.main()
