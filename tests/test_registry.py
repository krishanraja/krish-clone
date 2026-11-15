"""The registry of approved synthetic voices and likenesses: its format, its refusals, the three approvals it holds,
and adding Krish's approval on his own say-so or of a scored record. Invented names, words, ids and hashes, except
where a test reads the committed registry back."""

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
GOOD = {"name": "krish-voice-1", "kind": "voice", "platform": "elevenlabs", "basis": "scored_record",
        "approved_sha256": "a" * 64, "approved_words": "test words, not Krish's", "approved_on": "2026-11-20",
        "score": {"listeners": 12, "pairs": 10, "picked_the_clone": 0.52, "verdict": "pass"}}
TEST_REF = "TestVoiceRef00000001"  # shaped like an ElevenLabs voice id, and no one's
OWN = {"name": "krish-voice-test", "kind": "voice", "platform": "elevenlabs", "basis": "own_say_so",
       "platform_name": "Test Voice", "platform_ref": TEST_REF,
       "approved_sha256": registry.subject_sha256("voice", "elevenlabs", "Test Voice", TEST_REF),
       "approved_words": "test words, not Krish's", "approved_on": "2026-11-20"}
# The three approvals of 2026-11-15, with each sha256 computed apart from this code, as docs/REGISTRY.md shows:
#   printf '%s' '<the canonical description>' | sha256sum
APPROVED = {
    "krish-voice-elevenlabs": ("voice", "elevenlabs", "Krish Remix", "FOupAntbAMhJ9n9Q4dfC",
                               "e2e0cbaea9545a5e455cc60e4d77f3b8906b4c9c7a977efb330a579f5de4f9d1"),
    "krish-avatar-heygen": ("likeness", "heygen", "Krish Raja", "fa0069900c1049acbadc045c7866cdc5",
                            "f63dd89366687f06efcc9ace8fe9b5d3191e7323177b833883cd86601da20e75"),
    "krish-voice-heygen": ("voice", "heygen", "Krish Voice", "76d9dedcfa2d4f628beb43090e74e473",
                           "49b63e7540867514c4940b9ef516de0a2540ca4bd84528e84b88be0b554e4fd1"),
}


def text(*entries) -> str:
    return json.dumps({"format": registry.FORMAT, "approvals": list(entries)})


def but(base=GOOD, **changes) -> dict:
    entry = copy.deepcopy(base)
    entry.update(changes)
    return entry


def without(base: dict, *keys) -> dict:
    return {k: v for k, v in base.items() if k not in keys}


class RegistryFormatTest(unittest.TestCase):
    def test_the_committed_registry_holds_his_three_approvals_of_15_november(self):
        approvals = registry.load()
        self.assertEqual(json.loads(registry.DEFAULT.read_text())["format"], registry.FORMAT)
        self.assertEqual([a.name for a in approvals], list(APPROVED))
        words = {a.approved_words for a in approvals}
        self.assertEqual(len(words), 1)  # one answer of his approved all three
        self.assertIn("FOupAntbAMhJ9n9Q4dfC", words.pop())
        for entry in approvals:
            kind, platform, platform_name, platform_ref, sha = APPROVED[entry.name]
            with self.subTest(entry.name):
                self.assertEqual((entry.kind, entry.platform, entry.platform_name, entry.platform_ref),
                                 (kind, platform, platform_name, platform_ref))
                self.assertEqual((entry.basis, entry.approved_on, entry.score), ("own_say_so", "2026-11-15", None))
                self.assertEqual(entry.approved_sha256, sha)
                described = registry.subject(kind, platform, platform_name, platform_ref)
                self.assertEqual(registry.sha256_bytes(described), sha)
                self.assertTrue(entry.active)
                self.assertIs(registry.find(approvals, entry.name, kind), entry)
        # The older cloned voice named "Krish" in his ElevenLabs workspace is not approved.
        self.assertFalse([a for a in approvals if a.platform_name == "Krish"])

    def test_the_documented_reader_matches_the_code(self):
        doc = (ROOT / "docs" / "REGISTRY.md").read_text(encoding="utf-8")
        for fact in (registry.FORMAT, registry.RAW_URL, *registry.REQUIRED, *registry.OPTIONAL, *registry.BASES):
            self.assertIn(fact, doc)
        kind, platform, platform_name, platform_ref, sha = APPROVED["krish-voice-elevenlabs"]
        self.assertIn(registry.subject(kind, platform, platform_name, platform_ref).decode(), doc)
        self.assertIn(sha, doc)
        for name, (*_, platform_ref, _sha) in APPROVED.items():
            self.assertIn(f"| `{name}` |", doc)
            self.assertIn(platform_ref, doc)
        self.assertTrue(registry.RAW_URL.endswith("/main/config/synthetic-approvals.json"))

    def test_a_good_entry_reads_back(self):
        (entry,) = registry.parse(text(GOOD))
        self.assertEqual((entry.name, entry.kind, entry.platform, entry.approved_words),
                         ("krish-voice-1", "voice", "elevenlabs", "test words, not Krish's"))
        self.assertIs(registry.find([entry], "krish-voice-1", "voice"), entry)
        self.assertIsNone(registry.find([entry], "krish-voice-1", "likeness"))

    def test_anything_malformed_refuses_the_whole_registry(self):
        bad = {
            "a field the format does not name": but(voice_id="21m00Tcm4TlvDq8ikWAM"),
            "an id-shaped name": but(name="krish-21m00tcm4tlvdq8ikwam"),
            "an uppercase name": but(name="Krish-Voice"),
            "a one-word name": but(name="krish"),
            "a short hash": but(approved_sha256="a" * 63),
            "an uppercase hash": but(approved_sha256="A" * 64),
            "a likeness from a voice platform": but(kind="likeness"),
            "an unknown kind": but(kind="face"),
            "an unknown basis": but(basis="panel"),
            "no basis": without(GOOD, "basis"),
            "a platform id on a scored record": but(platform_ref=TEST_REF),
            "an own say-so with a hash of something else": but(OWN, approved_sha256="a" * 64),
            "a platform name its hash does not cover": but(OWN, platform_name="Krish"),
            "an own say-so with no platform_ref": without(OWN, "platform_ref"),
            "an own say-so with no platform_name": without(OWN, "platform_name"),
            "an own say-so with a score": but(OWN, score=GOOD["score"]),
            "a key where the id goes": but(OWN, platform_ref="sk_" + "0" * 48),
            "an ElevenLabs id on HeyGen": but(OWN, kind="likeness", platform="heygen"),
            "a padded platform name": but(OWN, platform_name=" Test Voice"),
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
                             "a name twice": text(GOOD, but(approved_sha256="b" * 64)),
                             "a hash twice": text(GOOD, but(name="krish-voice-2"))}.items():
            with self.subTest(why), self.assertRaises(registry.RegistryError):
                registry.parse(payload)

    def test_an_own_say_so_entry_reads_back_and_its_hash_is_of_its_description(self):
        (entry,) = registry.parse(text(OWN))
        self.assertEqual((entry.basis, entry.platform_name, entry.platform_ref), ("own_say_so", "Test Voice", TEST_REF))
        self.assertEqual(registry.subject("voice", "elevenlabs", "Test Voice", TEST_REF),
                         b'{"kind":"voice","platform":"elevenlabs","platform_name":"Test Voice","platform_ref":"' +
                         TEST_REF.encode() + b'"}')
        (heygen,) = registry.parse(text(but(OWN, kind="likeness", platform="heygen", platform_ref="0" * 32,
                                             approved_sha256=registry.subject_sha256("likeness", "heygen", "Test Voice",
                                                                                     "0" * 32))))
        self.assertEqual(heygen.platform, "heygen")

    def test_a_withdrawn_approval_never_matches(self):
        (entry,) = registry.parse(text(but(withdrawn={"words": "test: take it back", "on": "2026-11-21"})))
        self.assertFalse(entry.active)
        self.assertIsNone(registry.find([entry], "krish-voice-1", "voice"))


class OwnSaySoTest(unittest.TestCase):
    """Krish approves a synthetic voice or likeness of himself on his own say-so (Ruling, Krish, 2026-11-15)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / "synthetic-approvals.json"
        self.file.write_text(text(), encoding="utf-8")
        self.fields = {"name": "krish-voice-test", "kind": "voice", "platform": "elevenlabs",
                       "platform_name": "Test Voice", "platform_ref": TEST_REF}

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        with redirect_stdout(io.StringIO()) as printed:
            code = cli.main(["registry", *argv, "--file", str(self.file)])
        return code, printed.getvalue()

    def test_his_words_the_date_and_the_hash_of_what_he_approved_go_in_with_no_record(self):
        entry = registry.add_own_say_so(self.file, **self.fields, words="test words, not Krish's", on="2026-11-20")
        self.assertEqual(entry.approved_sha256, registry.subject_sha256("voice", "elevenlabs", "Test Voice", TEST_REF))
        self.assertEqual((entry.basis, entry.score, entry.approved_on), ("own_say_so", None, "2026-11-20"))
        (read,) = registry.load(self.file)
        self.assertEqual(read, entry)
        with self.assertRaises(registry.RegistryError):  # one entry per approved clone
            registry.add_own_say_so(self.file, **{**self.fields, "name": "krish-voice-again"}, words="again",
                                    on="2026-11-21")
        registry.withdraw(self.file, "krish-voice-test", "test: take it back", "2026-11-22")
        self.assertIsNone(registry.find(registry.load(self.file), "krish-voice-test", "voice"))

    def test_a_name_shaped_like_a_platform_id_is_refused(self):
        for name in ("krish-" + TEST_REF.lower(), "krish-fa0069900c1049acbadc045c7866cdc5", "voice-" + "x" * 16):
            with self.subTest(name), self.assertRaisesRegex(registry.RegistryError, "platform_ref"):
                registry.add_own_say_so(self.file, **{**self.fields, "name": name}, words="test", on="2026-11-20")
        self.assertEqual(registry.load(self.file), [])

    def test_a_ref_not_shaped_like_the_platforms_ids_is_refused(self):
        for platform, ref in (("elevenlabs", "sk_" + "0" * 48), ("elevenlabs", TEST_REF + "x"),
                              ("heygen", TEST_REF), ("heygen", "F" * 32)):
            with self.subTest(ref), self.assertRaises(registry.RegistryError):
                registry.add_own_say_so(self.file, **{**self.fields, "platform": platform, "platform_ref": ref},
                                        words="test", on="2026-11-20")
        self.assertEqual(registry.load(self.file), [])

    def test_the_command_adds_on_his_say_so_and_refuses_half_an_approval(self):
        own = ["krish-voice-test", "--kind", "voice", "--platform", "elevenlabs", "--platform-name", "Test Voice",
               "--platform-ref", TEST_REF]
        self.assertEqual(self.run_cli("add", *own)[0], 3)  # no words, no date
        self.assertEqual(self.run_cli("add", *own[:-2], "--words", "test", "--on", "2026-11-20")[0], 3)  # no ref
        self.assertEqual(self.run_cli("add", *own, "--record", "record.json", "--words", "test",
                                      "--on", "2026-11-20")[0], 3)  # a record and a say-so at once
        self.assertEqual(registry.load(self.file), [])
        code, printed = self.run_cli("add", *own, "--words", "test words, not Krish's", "--on", "2026-11-20")
        self.assertEqual(code, 0)
        self.assertIn(registry.subject_sha256("voice", "elevenlabs", "Test Voice", TEST_REF), printed)
        listed = self.run_cli("list")[1]
        self.assertIn("krish-voice-test", listed)
        self.assertIn("own_say_so", listed)


class RegistryAddTest(unittest.TestCase):
    """The optional route: Krish approves a scored listening-panel record."""
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
        self.file.write_text(text(), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_his_words_the_date_and_the_record_hash_go_in(self):
        entry = registry.add_record(self.file, self.record, "test words, not Krish's", "2026-11-21")
        self.assertEqual((entry.approved_sha256, entry.basis, entry.approved_on),
                         (self.sha, "scored_record", "2026-11-21"))
        (read,) = registry.load(self.file)
        self.assertEqual(read, entry)
        self.assertEqual(read.score, {"listeners": 10, "pairs": 10, "picked_the_clone": 0.5, "verdict": "pass"})
        with self.assertRaises(registry.RegistryError):  # one entry per approved clone
            registry.add_record(self.file, self.record, "again", "2026-11-22")
        registry.withdraw(self.file, "krish-voice-1", "test: take it back", "2026-11-23")
        self.assertIsNone(registry.find(registry.load(self.file), "krish-voice-1", "voice"))

    def test_an_approval_before_the_score_or_without_words_is_refused(self):
        with self.assertRaises(registry.RegistryError):
            registry.add_record(self.file, self.record, "test words", "2026-11-19")
        with self.assertRaises(registry.RegistryError):
            registry.add_record(self.file, self.record, "", "2026-11-21")
        self.assertEqual(registry.load(self.file), [])

    def test_the_command_lists_checks_and_adds(self):
        def run(*argv):
            with redirect_stdout(io.StringIO()) as printed:
                code = cli.main(["registry", *argv, "--file", str(self.file)])
            return code, printed.getvalue()

        self.assertEqual(run("list"), (0, "no synthetic voice or likeness is approved\n"))
        self.assertEqual(run("check")[0], 0)
        self.assertEqual(run("add", "--record", str(self.record))[0], 3)
        self.assertEqual(run("add", "krish-voice-1", "--record", str(self.record), "--words", "test",
                             "--on", "2026-11-21")[0], 3)  # the record names the clone
        code, printed = run("add", "--record", str(self.record), "--words", "test words, not Krish's", "--on", "2026-11-21")
        self.assertEqual(code, 0)
        self.assertIn(self.sha, printed)
        self.assertIn("krish-voice-1", run("list")[1])


if __name__ == "__main__":
    unittest.main()
