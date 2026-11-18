"""The registry of approved synthetic voices and likenesses: its format, its refusals, the approvals it holds,
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
# The approvals, with each sha256 computed apart from this code, as docs/REGISTRY.md shows:
#   printf '%s' '<the canonical description>' | sha256sum
APPROVED = {
    "krish-voice-elevenlabs": ("voice", "elevenlabs", "Krish Remix", "FOupAntbAMhJ9n9Q4dfC",
                               "e2e0cbaea9545a5e455cc60e4d77f3b8906b4c9c7a977efb330a579f5de4f9d1"),
    "krish-avatar-heygen": ("likeness", "heygen", "Krish Raja", "fa0069900c1049acbadc045c7866cdc5",
                            "f63dd89366687f06efcc9ace8fe9b5d3191e7323177b833883cd86601da20e75"),
    "krish-voice-heygen": ("voice", "heygen", "Krish Voice", "76d9dedcfa2d4f628beb43090e74e473",
                           "49b63e7540867514c4940b9ef516de0a2540ca4bd84528e84b88be0b554e4fd1"),
    "krish-voice-elevenlabs-v2": ("voice", "elevenlabs", "Krish v2", "EWMCMyM8o9ZcYCijk7nx",
                                  "e467fc8e2b0bd62da76615fb8fe1df0b0e1bd19aceb15d0ca42e685790dbfb09"),
    "krish-still-higgsfield-1": ("likeness", "higgsfield", "Headshot 1, colour-corrected (round 2 bank)",
        "b1684a272ba1c0151202f5a3799aba9241a09fcfd02ac9843458b4796fdb63c9",
        "dc07a86e38427724f76c3693d10e2a49f6667c17c83fe209dbeb667490718521"),
    "krish-still-higgsfield-3": ("likeness", "higgsfield", "Headshot 3, colour-corrected (round 2 bank)",
        "04ba73f8fb1432188657c9362051231d01d4a1e74828e6d462ecc28dc7aad8ce",
        "d3442f5fbf4ce970aae2ca74c112496b126a71502c865a20f206d5adc2f6bc24"),
    "krish-still-higgsfield-4": ("likeness", "higgsfield", "Headshot 4, colour-corrected (round 2 bank)",
        "f92390dc5ae042d46a61f83bf210f79d5aee1bc28b3331fb0a7269a962346bff",
        "2bd25765c2146b38b99fe02cfe65c4699061f4de31f0f18b5c3877dd7dd733b6"),
    "krish-still-higgsfield-6": ("likeness", "higgsfield", "Headshot 6, colour-corrected (round 2 bank)",
        "c977de98edcf92de9a959061479c274c869f7732bb9344a48366349119295e08",
        "6623481521b6327d89539ae8f493e52a44bfea33d0631b339e543116ce647c51"),
    "krish-still-higgsfield-5": ("likeness", "higgsfield", "Headshot 5, loft window, three-quarter (round 4, variant A)",
        "2a312e8f7469017d1585928d715a198d287a2f9d8f1216cb341dcc83f99eb377",
        "1f68a3794a057c5504f3b5668d96628b7a65db26b813b6e48172663a6f70fc8e"),
    "krish-still-higgsfield-1-shoulders": ("likeness", "higgsfield", "Headshot 1 with broader shoulders, in between (round 5)",
        "272152829a05fac72b01579a190608f94642116fdb0fdb5d788c3dd65d8fbcaf",
        "d59682d74539206a8a21fc4adea1ea439babeca3bb35d29993181b9d2f3d0861"),
}
# His approvals by date: the three of 15 November came in one answer; Krish v2 on 17 November; four generated
# headshots in one answer on 18 November (each pinned by its file's sha256).
APPROVED_ON = {"krish-voice-elevenlabs": "2026-11-15", "krish-avatar-heygen": "2026-11-15",
               "krish-voice-heygen": "2026-11-15", "krish-voice-elevenlabs-v2": "2026-11-17",
               **{f"krish-still-higgsfield-{n}": "2026-11-18" for n in ("1", "3", "4", "6", "5", "1-shoulders")}}


def text(*entries) -> str:
    return json.dumps({"format": registry.FORMAT, "approvals": list(entries)})


def but(base=GOOD, **changes) -> dict:
    entry = copy.deepcopy(base)
    entry.update(changes)
    return entry


def without(base: dict, *keys) -> dict:
    return {k: v for k, v in base.items() if k not in keys}


class RegistryFormatTest(unittest.TestCase):
    def test_the_committed_registry_holds_his_approvals(self):
        approvals = registry.load()
        self.assertEqual(json.loads(registry.DEFAULT.read_text())["format"], registry.FORMAT)
        self.assertEqual([a.name for a in approvals], list(APPROVED))
        words = {a.approved_words for a in approvals if a.approved_on == "2026-11-15"}
        self.assertEqual(len(words), 1)  # one answer of his approved all three of 15 November
        self.assertIn("FOupAntbAMhJ9n9Q4dfC", words.pop())
        for entry in approvals:
            kind, platform, platform_name, platform_ref, sha = APPROVED[entry.name]
            with self.subTest(entry.name):
                self.assertEqual((entry.kind, entry.platform, entry.platform_name, entry.platform_ref),
                                 (kind, platform, platform_name, platform_ref))
                self.assertEqual((entry.basis, entry.approved_on, entry.score),
                                 ("own_say_so", APPROVED_ON[entry.name], None))
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
