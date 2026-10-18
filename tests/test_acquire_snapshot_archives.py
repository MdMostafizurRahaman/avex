"""Input-validation tests for researcher-only archive acquisition."""

from __future__ import annotations

import unittest

from scripts.acquire_snapshot_archives import AcquisitionError, _github_repo, _record_fields


class AcquireSnapshotArchivesTests(unittest.TestCase):
    def test_accepts_github_repository_and_record_fields(self) -> None:
        record = {
            "id": "abc123",
            "project_name": "example",
            "repo_url": "https://github.com/example/project",
            "commit_hash": "a" * 40,
            "vuln_data": {"file_path": "src/module.py"},
        }
        fields = _record_fields(1, record)
        self.assertEqual(fields[0], "abc123")
        self.assertEqual(fields[4:], ("example", "project"))

    def test_rejects_non_github_repository(self) -> None:
        with self.assertRaises(AcquisitionError):
            _github_repo("https://gitlab.com/example/project")

    def test_rejects_path_traversal_target(self) -> None:
        record = {
            "id": "abc123",
            "project_name": "example",
            "repo_url": "https://github.com/example/project",
            "commit_hash": "a" * 40,
            "vuln_data": {"file_path": "../secret.py"},
        }
        with self.assertRaises(AcquisitionError):
            _record_fields(1, record)

    def test_rejects_unsafe_identifier(self) -> None:
        record = {
            "id": "bad/id",
            "project_name": "example",
            "repo_url": "https://github.com/example/project",
            "commit_hash": "a" * 40,
            "vuln_data": {"file_path": "src/module.py"},
        }
        with self.assertRaises(AcquisitionError):
            _record_fields(1, record)


if __name__ == "__main__":
    unittest.main()
