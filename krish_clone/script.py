"""The reading script for the voice session, built from Krish's own scripts.

A Professional Voice Clone learns how he sounds saying the things he says, so the best reading
material is his own writing: his vocabulary, his names and numbers, his rhythm. This takes the
scripts already in an approved source, drops stage directions and near-repeats, adds a drill of
the names and numbers he actually uses (where clones most often slip), and lays the rest out in
five minute blocks. Delivery stays one consistent, natural style throughout: ElevenLabs' PVC
guide says the clone replicates the style of its samples, so varied performances blur it.
Range comes from the words themselves (questions, figures, asides), never from acting.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

TEXT_SUFFIXES = {".md", ".txt"}
SKIP_NAMES = ("read me", "readme", "validation", "credits", "chapters", "review", "captions", "youtube", "substack", "title")
DELIVERY = "Your natural on-camera voice, the one you want the clone to have. Same pace, energy and distance every block."
META = re.compile(r"square brackets|said to camera|written to be said|the video script|\(about \d|every fact comes from"
                  r"|the story in one line|before you record|fact.?check|read it (aloud|out loud) once", re.I)
SHORT_CUT = re.compile(r"90.?second|short|teaser|trailer", re.I)
END_OF_SCRIPT = re.compile(r"^\s*#*\s*(changes from|notes?\b|sources?\b|fact.?check)", re.I)
MONTHS = {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
CHUNK_WORDS = 140
STAGE = re.compile(r"^\s*(\[.*\]|\(.*\)|#+\s.*|[-*_]{3,}|(on screen|b-?roll|cut to|visual|music|sfx|shot|title card|lower third|caption)\b.*:?.*)$", re.I)


def is_script(path: Path) -> bool:
    name = path.name.lower()
    return path.suffix.lower() in TEXT_SUFFIXES and not any(skip in name for skip in SKIP_NAMES)


def clean(text: str) -> list[str]:
    """Paragraphs of spoken words only, in chunks short enough to read in one breath of attention."""
    kept_lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if END_OF_SCRIPT.match(line):
            break  # what follows is about the script, not in it
        kept_lines.append(line)
    paragraphs = []
    for block in re.split(r"\n\s*\n", "\n".join(kept_lines)):
        lines = []
        for line in block.split("\n"):
            if STAGE.match(line):
                continue
            line = re.sub(r"\*\*|__|`|\[[^\]]*\]|\([^)]*(cut|shot|b-?roll|visual|on screen)[^)]*\)", "", line, flags=re.I)
            line = re.sub(r"^\s*([-*>]|\d+[.)])\s+", "", line)
            line = re.sub(r"^\s*[A-Z][A-Z .']{1,20}:\s*", "", line)  # speaker labels such as "KRISH:"
            line = re.sub(r"\d{1,2}:\d{2}(:\d{2})?(,\d+)?\s*(-->)?", "", line).strip()
            if line:
                lines.append(line)
        paragraph = " ".join(lines).strip()
        if len(paragraph.split()) >= 6 and not META.search(paragraph):
            paragraphs += _chunks(paragraph)
    return paragraphs


def _chunks(paragraph: str) -> list[str]:
    """Split a long transcript paragraph at sentence ends into pieces of about CHUNK_WORDS."""
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    pieces, current = [], []
    for sentence in sentences:
        current.append(sentence)
        if sum(len(x.split()) for x in current) >= CHUNK_WORDS:
            pieces.append(" ".join(current))
            current = []
    if current:
        if pieces and sum(len(x.split()) for x in current) < CHUNK_WORDS // 3:
            pieces[-1] += " " + " ".join(current)
        else:
            pieces.append(" ".join(current))
    return pieces


def _shingles(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(words[i:i + 4]) for i in range(max(1, len(words) - 3))}


def unique(paragraphs: list[tuple[str, str]], threshold: float = 0.6) -> list[tuple[str, str]]:
    """Drop near-repeats: the long cut, the short cut and the captions say the same things."""
    kept: list[tuple[str, str, set]] = []
    for source, paragraph in paragraphs:
        grams = _shingles(paragraph)
        if any(len(grams & g) / max(1, min(len(grams), len(g))) >= threshold for _, _, g in kept):
            continue
        kept.append((source, paragraph, grams))
    return [(s, p) for s, p, _ in kept]


def names_and_numbers(paragraphs: list[str], limit: int = 40) -> tuple[list[str], list[str]]:
    starts = set()
    names = Counter()
    for paragraph in paragraphs:
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            words = sentence.split()
            if words:
                starts.add(words[0].strip(".,!?:;\"'"))
            for word in words[1:]:
                token = word.strip(".,!?:;\"'()")
                if token in MONTHS or len(token) < 3 and not token.isupper():
                    continue
                if re.match(r"^[A-Z][A-Za-z0-9.\-]*[A-Za-z0-9]$", token) or re.match(r"^[a-z]+[A-Z][A-Za-z]*$", token):
                    names[token] += 1
    pattern = r"[$£€]?\d+(?:[,.]\d+)*(?:\s?(?:%|per ?cent|billion|million|thousand|bn|k))?"
    numbers = Counter(n.strip() for p in paragraphs for n in re.findall(pattern, p)
                      if len(re.sub(r"\D", "", n)) >= 2 or re.search(r"[$£€%]", n))
    return [n for n, c in names.most_common(limit) if c >= 2], [n for n, _ in numbers.most_common(20)]


@dataclass
class Built:
    markdown: str
    words: int
    minutes: float
    sources: list[str] = field(default_factory=list)


def prefer_long(paths: list[Path]) -> list[Path]:
    """Where an episode folder holds a long script and a short cut of it, read only the long one."""
    by_folder: dict[Path, list[Path]] = {}
    for path in paths:
        by_folder.setdefault(path.parent, []).append(path)
    kept = []
    for folder_paths in by_folder.values():
        longs = [p for p in folder_paths if not SHORT_CUT.search(p.name)]
        kept += longs if longs else folder_paths
    return sorted(kept)


def build(paths: list[Path], *, minutes: float = 75, wpm: float = 150) -> Built:
    raw: list[tuple[str, str]] = []
    for path in prefer_long(paths):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        raw += [(f"{path.parent.name}/{path.name}", p) for p in clean(text)]
    paragraphs = unique(raw)
    names, numbers = names_and_numbers([p for _, p in paragraphs])
    target_words = int(minutes * wpm)
    block_words = int(5 * wpm)
    lines = [
        "# Voice session: reading script", "",
        "For the ElevenLabs Professional Voice Clone. Read it in one session, in one room, with one microphone,",
        "two fists from your mouth, with a pop filter, at the same level throughout. No music, no processing.",
        "A quiet room with soft furnishings; a duvet behind the microphone helps. Record WAV; the engine exports MP3.",
        "If you stumble, pause two seconds and say the sentence again; the engine keeps the clean take.",
        "Take a break between blocks. Water, not coffee.", "",
        f"Target: about {minutes:.0f} minutes at {wpm:.0f} words a minute ({target_words} words).",
        DELIVERY,
        "Level: aim for speech around -20 dB RMS with peaks below -3 dB (ElevenLabs' recommended range).", "",
        "## Warm-up: the names and numbers you actually say", "",
        "Clones slip most on names and figures. Say each one clearly, once, then in the sentence that follows it.", "",
    ]
    if names:
        lines += ["Names: " + ", ".join(names) + ".", ""]
    if numbers:
        lines += ["Figures: " + ", ".join(numbers) + ".", ""]
    lines += ["Questions, rising: Does that matter? Would you trust it? What happens next? Who pays for that?", "",
              "Lists, falling: data, compute, distribution and trust.", ""]
    words, block, block_count = 0, 0, 0
    used_sources: list[str] = []
    for source, paragraph in paragraphs:
        if words >= target_words:
            break
        if block == 0:
            block_count += 1
            lines += [f"## Block {block_count}", ""]
        lines += [paragraph, ""]
        count = len(paragraph.split())
        words += count
        block += count
        if source not in used_sources:
            used_sources.append(source)
        if block >= block_words:
            block = 0
    short = max(0.0, (target_words - words) / wpm)
    lines += ["## Free talk", "",
              "No script: you explaining what you are building, a recent call, a view you hold. Same voice as above.",
              f"Keep going for about {max(5.0, short):.0f} minutes" + (" to reach the target." if short > 0 else "."),
              "This is the most natural audio in the session.", ""]
    return Built("\n".join(lines), words, words / wpm, used_sources)
