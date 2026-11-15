"""The listening panel and the scored record, on stub clips and invented listeners: no voice, face or name of a real
person enters this repository."""

import csv
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from krish_clone import cli, evaluate, panel

PAIRS = 10


def listeners_file(directory: Path, count: int = 10, approved: bool = False) -> Path:
    path = directory / "listeners.json"
    data = {"format": panel.LISTENERS_FORMAT,
            "listeners": [{"id": f"L{i:02d}", "name": f"Test Listener {i}"} for i in range(1, count + 1)]}
    if approved:
        data["approval"] = {"words": "test words, not Krish's", "on": "2026-11-16"}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def approve(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["approval"] = {"words": "test words, not Krish's", "on": "2026-11-16"}
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")  # a different layout; the list's digest holds


def make_pack(root: Path, pairs: int = PAIRS) -> Path:
    real = [root / f"real{i}.wav" for i in range(pairs)]
    clone = [root / f"clone{i}.wav" for i in range(pairs)]
    for path in real + clone:
        path.write_bytes(path.name.encode())
    return Path(evaluate.ab_pack(real, clone, root / "ab", seed=3)["key_file"])


def fill_sheet(panel_dir: Path, listener: str, catch: int) -> Path:
    """The listener marks the generated clip correctly in their first `catch` pairs and wrongly in the rest."""
    built = json.loads((panel_dir / panel.PANEL_KEY).read_text(encoding="utf-8"))
    plan = built["items"][listener]
    key = {p["pair"]: p["clone"] for p in json.loads(Path(built["key_file"]).read_text(encoding="utf-8"))["pairs"]}
    sheet = panel_dir / f"filled-{listener}.csv"
    with sheet.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["item", "choice"])
        for entry in plan:
            generated = "1" if entry["1"] == key[entry["pair"]] else "2"
            other = "2" if generated == "1" else "1"
            writer.writerow([entry["item"], generated if entry["item"] <= catch else other])
    return sheet


class PanelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.key = make_pack(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_each_listener_gets_their_own_order_and_no_key(self):
        people = listeners_file(self.root)
        out = self.root / "panel"
        built = panel.build(self.key, people, out, seed=11)
        self.assertFalse(built["listeners_approved"])
        plans = built["items"]
        self.assertEqual(sorted(plans), [f"L{i:02d}" for i in range(1, 11)])
        orders = {tuple(e["pair"] for e in plan) for plan in plans.values()}
        self.assertGreater(len(orders), 1, "every listener hears the same order")
        pack = self.key.parent / "pack"
        for listener, plan in plans.items():
            folder = out / listener
            names = sorted(p.name for p in folder.iterdir())
            self.assertEqual(len([n for n in names if n.startswith("pair")]), 2 * PAIRS)
            self.assertIn(panel.SHEET, names)
            self.assertFalse(any("KEY" in n or "_A" in n or "_B" in n for n in names), names)
            for entry in plan:
                for choice in ("1", "2"):
                    clip = next(folder.glob(f"pair{entry['item']:02d}-{choice}.*"))
                    self.assertEqual(clip.read_bytes(), next(pack.glob(f"{entry['pair']}_{entry[choice]}.*")).read_bytes())
        self.assertFalse(any("Test Listener" in p.read_text(errors="ignore") for p in out.rglob("*") if p.is_file()),
                         "a listener's name reached the panel")
        with self.assertRaises(FileExistsError):
            panel.build(self.key, people, out)

    def test_too_few_listeners_or_pairs_are_refused(self):
        with self.assertRaises(panel.Refused):
            panel.build(self.key, listeners_file(self.root, count=9), self.root / "p9")
        (self.root / "small").mkdir()
        small = make_pack(self.root / "small", pairs=4)
        with self.assertRaises(panel.Refused):
            panel.build(small, listeners_file(self.root), self.root / "p4")

    def test_answers_are_recorded_once_and_mapped_back_to_the_pack(self):
        out = self.root / "panel"
        panel.build(self.key, listeners_file(self.root), out, seed=5)
        sheet = fill_sheet(out, "L01", catch=PAIRS)
        self.assertEqual(panel.record_answers(out, "L01", sheet), PAIRS)
        key = {p["pair"]: p["clone"] for p in json.loads(self.key.read_text())["pairs"]}
        rows = list(csv.DictReader((out / panel.ANSWERS).open()))
        self.assertEqual(len(rows), PAIRS)
        self.assertTrue(all(row["choice"] == key[row["pair"]] for row in rows), "a correct pick did not map to the clone")
        with self.assertRaises(panel.Refused):
            panel.record_answers(out, "L01", sheet)
        with self.assertRaises(panel.Refused):
            panel.record_answers(out, "L99", sheet)
        partial = out / "partial.csv"
        partial.write_text("item,choice\n1,1\n2,3\n", encoding="utf-8")
        with self.assertRaises(panel.Refused):
            panel.record_answers(out, "L02", partial)
        self.assertEqual(len(list(csv.DictReader((out / panel.ANSWERS).open()))), PAIRS, "a refused sheet was written")

    def test_the_record_waits_for_krish_and_binds_what_was_scored(self):
        people = listeners_file(self.root)
        out = self.root / "panel"
        panel.build(self.key, people, out, seed=9)
        for i in range(1, 11):
            panel.record_answers(out, f"L{i:02d}", fill_sheet(out, f"L{i:02d}", catch=5))
        record_path = self.root / "record.json"
        kwargs = dict(name="krish-voice-1", kind="voice", platform="elevenlabs", today="2026-11-20")
        with self.assertRaises(panel.Refused):  # the list is not approved yet
            panel.write_record(self.key, out / panel.ANSWERS, out, record_path, **kwargs)
        approve(people)
        record, sha = panel.write_record(self.key, out / panel.ANSWERS, out, record_path, **kwargs)
        self.assertEqual(sha, hashlib.sha256(record_path.read_bytes()).hexdigest())
        self.assertEqual(record["score"]["picked_the_clone"], 0.5)
        self.assertEqual(record["score"]["verdict"], "pass")
        self.assertEqual((record["score"]["listeners"], record["score"]["pairs"]), (10, PAIRS))
        self.assertEqual(record["listeners"]["approved_on"], "2026-11-16")
        self.assertNotIn("Test Listener", record_path.read_text())
        self.assertEqual(panel.read_record(record_path), (record, sha))
        with self.assertRaises(FileExistsError):
            panel.write_record(self.key, out / panel.ANSWERS, out, record_path, **kwargs)
        with self.assertRaises(panel.Refused):  # an id-shaped name never reaches a record
            panel.write_record(self.key, out / panel.ANSWERS, out, self.root / "r2.json",
                               **{**kwargs, "name": "voice-21m00tcm4tlvdq8ikwam"})

    def test_an_incomplete_panel_or_a_failing_clone_is_never_approvable(self):
        people = listeners_file(self.root, approved=True)
        out = self.root / "panel"
        panel.build(self.key, people, out, seed=2)
        for i in range(1, 10):
            panel.record_answers(out, f"L{i:02d}", fill_sheet(out, f"L{i:02d}", catch=PAIRS))
        kwargs = dict(name="krish-voice-1", kind="voice", platform="elevenlabs", today="2026-11-20")
        with self.assertRaises(panel.Refused):  # nine listeners
            panel.write_record(self.key, out / panel.ANSWERS, out, self.root / "r9.json", **kwargs)
        panel.record_answers(out, "L10", fill_sheet(out, "L10", catch=PAIRS))
        record, _ = panel.write_record(self.key, out / panel.ANSWERS, out, self.root / "fail.json", **kwargs)
        self.assertEqual(record["score"]["verdict"], "fail")
        with self.assertRaises(panel.Refused):
            panel.read_record(self.root / "fail.json")

    def test_the_commands_run_end_to_end(self):
        people = listeners_file(self.root, approved=True)
        out = self.root / "panel"
        with redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(cli.main(["abpanel", "--key", str(self.key), "--listeners", str(people),
                                       "--out", str(out), "--seed", "1"]), 0)
        self.assertIn("may now be made through SendLinks", printed.getvalue())
        for i in range(1, 11):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["abrecord", "--panel", str(out), "--listener", f"L{i:02d}",
                                           "--sheet", str(fill_sheet(out, f"L{i:02d}", catch=6))]), 0)
        record = self.root / "record.json"
        with redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(cli.main(["abscore", "--key", str(self.key), "--answers", str(out / panel.ANSWERS),
                                       "--record", str(record), "--panel", str(out), "--clone-name", "krish-voice-1",
                                       "--kind", "voice", "--platform", "elevenlabs"]), 0)
        self.assertIn(hashlib.sha256(record.read_bytes()).hexdigest(), printed.getvalue())
        with redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(cli.main(["abscore", "--key", str(self.key), "--answers", str(out / panel.ANSWERS),
                                       "--record", str(self.root / "x.json")]), 3)
        self.assertIn("refused: --record needs --panel", printed.getvalue())


if __name__ == "__main__":
    unittest.main()
