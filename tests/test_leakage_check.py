"""Coverage for configurable leakage and workspace-escape checks."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.leakage_check import main, scan_workspace


class LeakageCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.rules = self.root / "rules.json"
        self._write_rules()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_rules(self, patterns=None, allowlist=None, **extra) -> None:
        value = {
            "schema_version": 1,
            "deny_symlinks": True,
            "deny_git_metadata": True,
            "deny_patch_diff_artifacts": True,
            "max_file_bytes": 1024 * 1024,
            "forbidden_paths": ["ground_truth", "scenario_validation", "answer_key", "expected_verdict", "vulnerable_label", "fixed_label"],
            "forbidden_filename_patterns": [r"(?i)(?:^|[/_.-])expected[_-]?verdict(?:$|[/_.-])"],
            "forbidden_extensions": [".patch", ".diff"],
            "forbidden_artifact_filename_patterns": [r"(?i)(?:^|[_.-])(?:patch|diff)(?:[_.-]|$)"],
            "forbidden_patterns": patterns or [
                {"id": "cve_identifier", "pattern": r"\bCVE-\d{4}-\d{4,}\b", "flags": ["IGNORECASE"]},
                {"id": "cwe_identifier", "pattern": r"\bCWE-\d{1,5}\b", "flags": ["IGNORECASE"]},
                {"id": "answer_marker", "pattern": r"(?i)EXPECTED_VERDICT"},
            ],
            "allowlist": allowlist or [],
        }
        value.update(extra)
        self.rules.write_text(json.dumps(value), encoding="utf-8")

    def test_normal_clean_workspace(self) -> None:
        (self.workspace / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")
        result = scan_workspace(self.workspace, self.rules)
        self.assertTrue(result["clean"])
        self.assertEqual([], result["findings"])
        self.assertEqual(1, result["files_scanned"])

    def test_forbidden_token(self) -> None:
        (self.workspace / "notes.txt").write_text("CVE-2024-47227\n", encoding="utf-8")
        result = scan_workspace(self.workspace, self.rules)
        self.assertFalse(result["clean"])
        self.assertEqual("cve_identifier", result["findings"][0]["code"])
        self.assertEqual(1, result["findings"][0]["line"])

    def test_forbidden_filename(self) -> None:
        (self.workspace / "expected_verdict.json").write_text("{}", encoding="utf-8")
        result = scan_workspace(self.workspace, self.rules)
        self.assertFalse(result["clean"])
        self.assertIn("forbidden_filename", {item["code"] for item in result["findings"]})

    def test_symlink_escape(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_text("private", encoding="utf-8")
        try:
            (self.workspace / "escape.txt").symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        result = scan_workspace(self.workspace, self.rules)
        self.assertFalse(result["clean"])
        self.assertEqual({"symlink", "symlink_escape"}, {item["code"] for item in result["findings"]})

    def test_nested_leakage(self) -> None:
        nested = self.workspace / "a" / "b" / "c"
        nested.mkdir(parents=True)
        (nested / "trace.log").write_text("EXPECTED_VERDICT: CWE-79\n", encoding="utf-8")
        result = scan_workspace(self.workspace, self.rules)
        self.assertEqual("a/b/c/trace.log", result["findings"][0]["path"])
        self.assertGreaterEqual(len(result["findings"]), 2)

    def test_clean_occurrence_is_reported_as_allowlisted(self) -> None:
        text = "Example documentation token: CWE-79 is used as a literal fixture."
        (self.workspace / "fixture.txt").write_text(text, encoding="utf-8")
        self._write_rules(
            allowlist=[{
                "path": "fixture.txt",
                "pattern_id": "cwe_identifier",
                "pattern": r"CWE-79",
                "reason": "Literal fixture used to document the scanner in a test workspace.",
            }]
        )
        result = scan_workspace(self.workspace, self.rules)
        self.assertTrue(result["clean"])
        self.assertEqual([], result["findings"])
        self.assertEqual("CWE-79", result["allowlisted_occurrences"][0]["match"])

    def test_json_output_and_nonzero_exit_for_findings(self) -> None:
        (self.workspace / "answer.txt").write_text("EXPECTED_VERDICT", encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(self.workspace), "--rules", str(self.rules), "--json"])
        self.assertEqual(1, code)
        result = json.loads(output.getvalue())
        self.assertFalse(result["clean"])
        self.assertEqual("answer_marker", result["findings"][0]["code"])


if __name__ == "__main__":
    unittest.main()
