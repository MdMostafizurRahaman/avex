"""Filesystem-safety and reproducibility tests for build_conditions.py."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_conditions import ManifestError, SafetyError, build_conditions


class BuildConditionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "controllers").mkdir()
        (self.source / "controllers" / "target.py").write_text("target = 1\n", encoding="utf-8")
        (self.source / "helper.py").write_text("helper = 2\n", encoding="utf-8")
        (self.source / "omit.txt").write_text("excluded\n", encoding="utf-8")
        self.manifest = self.root / "config" / "evidence_manifest.json"
        self.manifest.parent.mkdir()
        self.destination = self.root / "pilot" / "conditions"
        self.manifest_output = self.root / "results" / "manifests"
        self._write_manifest()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_manifest(self, *, traversal: bool = False) -> None:
        target = "../outside.py" if traversal else "controllers/target.py"
        conditions = {}
        for condition in ("E1", "E2", "E3"):
            includes = [target, "helper.py"]
            if traversal:
                excludes = ["controllers/target.py", "helper.py", "omit.txt"]
            else:
                excludes = ["omit.txt"]
            conditions[condition] = {
                "include": includes,
                "exclude": excludes,
                "initial_evidence_files": [target if not traversal else "../outside.py"],
            }
        data = {
            "scenario_id": "test-scenario",
            "source_snapshot": str(self.source),
            "target_file": "controllers/target.py",
            "conditions": conditions,
        }
        self.manifest.write_text(json.dumps(data), encoding="utf-8")

    def _build(self, *, force: bool = False):
        return build_conditions(
            source=self.source,
            destination=self.destination,
            manifest_path=self.manifest,
            manifest_output_dir=self.manifest_output,
            force=force,
        )

    def _tree_hashes(self) -> dict[str, str]:
        return {
            path.relative_to(self.source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.source.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def test_deterministic_output(self) -> None:
        self._build()
        before = {
            path.relative_to(self.destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.destination.rglob("*")) if path.is_file()
        }
        first_manifests = {
            path.name: path.read_bytes() for path in sorted(self.manifest_output.glob("*_manifest.json"))
        }
        self._build(force=True)
        after = {
            path.relative_to(self.destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.destination.rglob("*")) if path.is_file()
        }
        second_manifests = {
            path.name: path.read_bytes() for path in sorted(self.manifest_output.glob("*_manifest.json"))
        }
        self.assertEqual(before, after)
        self.assertEqual(first_manifests, second_manifests)

    def test_source_remains_unchanged(self) -> None:
        before = self._tree_hashes()
        self._build()
        self.assertEqual(before, self._tree_hashes())

    def test_traversal_rejection(self) -> None:
        self._write_manifest(traversal=True)
        with self.assertRaises(ManifestError):
            self._build()
        self.assertFalse(self.destination.exists())

    def test_symlink_escape_rejection(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        try:
            (self.source / "escape.txt").symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaises(SafetyError):
            self._build()
        self.assertFalse(self.destination.exists())

    def test_overwrite_protection(self) -> None:
        self._build()
        with self.assertRaises(FileExistsError):
            self._build()

    def test_correct_exclusion(self) -> None:
        self._build()
        for condition in ("E1", "E2", "E3"):
            workspace = self.destination / condition
            self.assertTrue((workspace / "controllers" / "target.py").is_file())
            self.assertTrue((workspace / "helper.py").is_file())
            self.assertFalse((workspace / "omit.txt").exists())
            record = json.loads((self.manifest_output / f"{condition}_manifest.json").read_text())
            self.assertIn("omit.txt", record["excluded_paths"])
            self.assertEqual([], record["missing_requested_paths"])

    def test_hash_generation(self) -> None:
        results = self._build()
        self.assertEqual(3, len(results))
        for condition in ("E1", "E2", "E3"):
            record = json.loads((self.manifest_output / f"{condition}_manifest.json").read_text())
            self.assertEqual(2, record["file_count"])
            self.assertEqual(2, len(record["files"]))
            for item in record["files"]:
                path = self.destination / condition / item["path"]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            self.assertRegex(record["workspace_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
