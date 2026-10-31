import json
import tempfile
import unittest
from pathlib import Path

from krish_clone import cli, sources


def config(directory: Path, **status) -> Path:
    path = directory / "sources.json"
    entries = [{"id": key, "name": key, "drive_id": "x", "kind": "video", "status": value,
                "local_path": str(directory / key) if value == "approved" else None} for key, value in status.items()]
    path.write_text(json.dumps({"sources": entries}), encoding="utf-8")
    return path


class SourcesTest(unittest.TestCase):
    def test_shipped_config_approves_only_what_krish_approved(self):
        shipped = {s.id: s for s in sources.load()}
        self.assertEqual([k for k, s in shipped.items() if s.status == "approved"], ["episodes", "inbox"])
        self.assertIn("Krish, 2026-10-29", shipped["episodes"].approval)
        self.assertTrue(shipped["episodes"].local_path.endswith("3 Posts"))
        self.assertIn("Krish, 2026-10-31", shipped["inbox"].approval)
        self.assertTrue(shipped["inbox"].local_path.endswith("Video Engine\\Inbox"))

    def test_pending_unknown_and_pathless_sources_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = config(Path(tmp), a="pending", b="approved")
            with self.assertRaises(sources.NotApproved):
                sources.require_approved("a", path)
            with self.assertRaises(sources.NotApproved):
                sources.require_approved("nope", path)
            self.assertEqual(sources.require_approved("b", path).id, "b")
            sources.set_status("a", "approved", path)  # approved but no local_path on this machine
            with self.assertRaises(sources.NotApproved):
                sources.require_approved("a", path)

    def test_set_status_writes_only_the_named_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = config(Path(tmp), a="pending", b="pending")
            sources.set_status("b", "rejected", path)
            self.assertEqual([s.status for s in sources.load(path)], ["pending", "rejected"])

    def test_cli_refuses_files_without_an_approved_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = config(root, a="approved", b="pending")
            (root / "a").mkdir()
            outside = root / "elsewhere.wav"
            outside.write_bytes(b"")
            common = ["--config", str(path), "inventory", str(outside), "--out", str(root / "lib"), "--no-face"]
            self.assertEqual(cli.main(common), 3)  # no source named
            self.assertEqual(cli.main(common + ["--source", "b"]), 3)  # pending
            self.assertEqual(cli.main(common + ["--source", "a"]), 3)  # outside the approved folder
            self.assertFalse((root / "lib").exists())


if __name__ == "__main__":
    unittest.main()
