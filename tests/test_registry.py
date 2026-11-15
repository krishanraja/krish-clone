"""The registry of approved synthetic voices and likenesses: its format, its refusals, and adding Krish's approval of a
scored record. Invented names, words and hashes only."""

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from krish_clone import cli, panel, registry
from tests.test_panel import fill_sheet, listeners_file, make_pack

ROOT = Path(__file__).resolve().parents[1]
GOOD = {"name": "krish-voice-1", "kind": "voice", "platform": "elevenlabs", "scored_pack_sha256": "a" * 64,
        "approved_words": "test words, not Krish's", "approved_on": "2026-11-20",
        "score": {"listeners": 12, "pairs": 10, "picked_the_clone": 0.52, "verdict": "pass"}}


def text(*entries) -> str:
    return json.dumps({"format": registry.FORMAT, "approvals": list(entries)})


def but(**changes) -> dict:
    entry = copy.deepcopy(GOOD)
    entry.update(changes)
    return entry


class RegistryFormatTest(unittest.TestCase):
    def test_the_committed_registry_is_readable_and_holds_no_approval_yet(self):
        self.assertEqual(registry.load(), [])
        self.assertEqual(json.loads(registry.DEFAULT.read_text())["format"], registry.FORMAT)

    def test_the_documented_reader_matches_the_code(self):
        doc = (ROOT / "docs" / "REGISTRY.md").read_text(encoding="utf-8")
        for fact in (registry.FORMAT, registry.RAW_URL, *registry.REQUIRED, *registry.OPTIONAL):
            self.assertIn(fact, doc)
        self.assertTrue(registry.RAW_URL.endswith("/main/config/synthetic-approvals.json"))

    def test_a_good_entry_reads_back(self):
        (entry,) = registry.parse(text(GOOD))
        self.assertEqual((entry.name, entry.kind, entry.platform, entry.approved_words),
                         ("krish-voice-1", "voice", "elevenlabs", "test words, not Krish's"))
        self.assertIs(registry.find([entry], "krish-voice-1", "voice"), entry)
        self.assertIsNone(registry.find([entry], "krish-voice-1", "likeness"))

    def test_anything_malformed_refuses_the_whole_registry(self):
        bad = {
            "a platform id field": but(voice_id="21m00Tcm4TlvDq8ikWAM"),
            "an id-shaped name": but(name="krish-21m00tcm4tlvdq8ikwam"),
            "an uppercase name": but(name="Krish-Voice"),
            "a one-word name": but(name="krish"),
            "a short hash": but(scored_pack_sha256="a" * 63),
            "an uppercase hash": but(scored_pack_sha256="A" * 64),
            "a voice from the wrong platform": but(platform="heygen"),
            "an unknown kind": but(kind="face"),
            "no words": but(approved_words="  "),
            "a bad date": but(approved_on="20 Nov 2026"),
            "a score with extra fields": but(score={**GOOD["score"], "per_listener": {}}),
            "a withdrawal before the approval": but(withdrawn={"words": "no", "on": "2026-11-01"}),
            "a missing field": {k: v for k, v in GOOD.items() if k != "approved_on"},
        }
        for why, entry in bad.items():
            with self.subTest(why), self.assertRaises(registry.RegistryError):
                registry.parse(text(entry))
        for why, payload in {"not JSON": "{", "another format": json.dumps({"format": "x/1", "approvals": []}),
                             "approvals not a list": json.dumps({"format": registry.FORMAT, "approvals": {}}),
                             "a name twice": text(GOOD, but(scored_pack_sha256="b" * 64)),
                             "a hash twice": text(GOOD, but(name="krish-voice-2"))}.items():
            with self.subTest(why), self.assertRaises(registry.RegistryError):
                registry.parse(payload)

    def test_a_withdrawn_approval_never_matches(self):
        (entry,) = registry.parse(text(but(withdrawn={"words": "test: take it back", "on": "2026-11-21"})))
        self.assertFalse(entry.active)
        self.assertIsNone(registry.find([entry], "krish-voice-1", "voice"))


class RegistryAddTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.root = Path(self.tmp.name)
        key = make_pack(root)
        out = root / "panel"
        panel.build(key, listeners_file(root, approved=True), out, seed=4)
        for i in range(1, 11):
            panel.record_answers(out, f"L{i:02d}", fill_sheet(out, f"L{i:02d}", catch=5))
        self.record = root / "record.json"
        _, self.sha = panel.write_record(key, out / panel.ANSWERS, out, self.record, name="krish-voice-1",
                                         kind="voice", platform="elevenlabs", today="2026-11-20")
        self.file = root / "synthetic-approvals.json"
        self.file.write_text(registry.DEFAULT.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_his_words_the_date_and_the_record_hash_go_in(self):
        entry = registry.add(self.file, self.record, "test words, not Krish's", "2026-11-21")
        self.assertEqual((entry.scored_pack_sha256, entry.approved_on), (self.sha, "2026-11-21"))
        (read,) = registry.load(self.file)
        self.assertEqual(read, entry)
        self.assertEqual(read.score, {"listeners": 10, "pairs": 10, "picked_the_clone": 0.5, "verdict": "pass"})
        with self.assertRaises(registry.RegistryError):  # one entry per approved clone
            registry.add(self.file, self.record, "again", "2026-11-22")
        registry.withdraw(self.file, "krish-voice-1", "test: take it back", "2026-11-23")
        self.assertIsNone(registry.find(registry.load(self.file), "krish-voice-1", "voice"))

    def test_an_approval_before_the_score_or_without_words_is_refused(self):
        with self.assertRaises(registry.RegistryError):
            registry.add(self.file, self.record, "test words", "2026-11-19")
        with self.assertRaises(registry.RegistryError):
            registry.add(self.file, self.record, "", "2026-11-21")
        self.assertEqual(registry.load(self.file), [])

    def test_the_command_lists_checks_and_adds(self):
        def run(*argv):
            with redirect_stdout(io.StringIO()) as printed:
                code = cli.main(["registry", *argv, "--file", str(self.file)])
            return code, printed.getvalue()

        self.assertEqual(run("list"), (0, "no synthetic voice or likeness is approved\n"))
        self.assertEqual(run("check")[0], 0)
        self.assertEqual(run("add", "--record", str(self.record))[0], 3)
        code, printed = run("add", "--record", str(self.record), "--words", "test words, not Krish's", "--on", "2026-11-21")
        self.assertEqual(code, 0)
        self.assertIn(self.sha, printed)
        self.assertIn("krish-voice-1", run("list")[1])


if __name__ == "__main__":
    unittest.main()
