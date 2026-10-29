"""Find the stretches of a recording where Krish speaks cleanly enough to train a voice clone.

A segment is judged on what sits in its own pauses. In a clean voiceover the gaps between words
drop to room tone; under a music bed they stay loud. That one measure separates the two without a
separation model, and it is why separated audio is never promoted to the clean tier: Demucs leaves
artifacts a clone learns as part of the voice.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

from content_watcher.read import audio as cw_audio

from . import media

RATE = 16_000
FRAME = 0.02  # seconds per energy frame
MIN_SEGMENT, MAX_SEGMENT = 3.0, 30.0
CLEAN_SNR, REVIEW_SNR = 30.0, 20.0  # dB between speech and its own pauses
BED_MARGIN = 12.0  # pauses this far above the file's room tone mean something else is playing
LOUD_PAUSE = -45.0  # dBFS; no quiet room sits this loud, so a bed under the whole file still shows
CLIP_LIMIT = 2  # flat-topped runs at full scale allowed in one segment
DIGITAL_SILENCE = -90.0  # frames below this are padding, not a room


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speech_db: float | None = None
    pause_db: float | None = None
    snr_db: float | None = None
    room_db: float | None = None  # the file's room tone, for reading pause_db against
    bed: bool = False
    clipped: int = 0  # flat-topped runs at full scale inside the segment
    speaker: float | None = None  # cosine to Krish's enrolment voice, when a verifier is installed
    tier: str = "rejected"  # clean, review, rejected
    reasons: list[str] = field(default_factory=list)  # why it was demoted
    notes: list[str] = field(default_factory=list)  # what is true but does not demote it

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 2)

    def as_dict(self) -> dict:
        data = asdict(self)
        data["duration"] = self.duration
        return data


def frame_db(samples) -> "numpy.ndarray":
    import numpy

    size = int(RATE * FRAME)
    usable = len(samples) - len(samples) % size
    if usable <= 0:
        return numpy.array([], dtype=numpy.float32)
    blocks = samples[:usable].reshape(-1, size).astype(numpy.float64)
    rms = numpy.sqrt((blocks ** 2).mean(axis=1))
    return (20 * numpy.log10(numpy.maximum(rms, 1e-7))).astype(numpy.float32)


def room_tone(db) -> float:
    """The file's quietest steady level: the 5th percentile of frame energy, ignoring digital silence."""
    import numpy

    live = db[db > DIGITAL_SILENCE] if len(db) else db
    return float(numpy.percentile(live, 5)) if len(live) else -120.0


def group(pieces: list[dict], *, minimum: float = MIN_SEGMENT, maximum: float = MAX_SEGMENT) -> list[Segment]:
    """Join transcript sentences into training segments without splitting a sentence."""
    segments: list[Segment] = []
    current: Segment | None = None
    for piece in pieces:
        text = piece["text"].strip()
        if not text:
            continue
        joinable = current is not None and piece["start"] - current.end < 0.8 and piece["end"] - current.start <= maximum
        if joinable and current.duration < minimum * 2:
            current.end, current.text = piece["end"], f"{current.text} {text}"
        else:
            if current is not None:
                segments.append(current)
            current = Segment(piece["start"], piece["end"], text)
    if current is not None:
        segments.append(current)
    return segments


def _pauses(segment: Segment, words: list[dict]) -> list[tuple[float, float]]:
    inside = [w for w in words if w["start"] >= segment.start - 0.05 and w["end"] <= segment.end + 0.05]
    gaps = []
    for a, b in zip(inside, inside[1:]):
        if b["start"] - a["end"] >= 0.12:
            gaps.append((a["end"] + 0.03, b["start"] - 0.03))
    return gaps


def measure(segment: Segment, db, words: list[dict], floor: float, clips: list[float]) -> Segment:
    import numpy

    def span(a: float, b: float):
        return db[int(a / FRAME):max(int(b / FRAME), int(a / FRAME) + 1)]

    body = span(segment.start, segment.end)
    if not len(body):
        segment.reasons.append("empty")
        return segment
    segment.speech_db = round(float(numpy.percentile(body, 90)), 1)
    gaps = _pauses(segment, words)
    pause_frames = numpy.concatenate([span(a, b) for a, b in gaps]) if gaps else numpy.array([])
    if len(pause_frames) >= 5:
        segment.pause_db = round(float(numpy.median(pause_frames)), 1)
    else:  # no usable pauses: fall back to the quietest tenth of the segment itself
        segment.pause_db = round(float(numpy.percentile(body, 10)), 1)
    if segment.pause_db <= DIGITAL_SILENCE:
        # Pauses cut to digital silence: the audio was gated or spliced, so the room is unknown.
        segment.notes.append("pauses are digital silence (gated or spliced)")
        segment.pause_db = round(max(floor, DIGITAL_SILENCE), 1)
    segment.snr_db = round(segment.speech_db - segment.pause_db, 1)
    segment.room_db = round(floor, 1)
    segment.bed = (segment.pause_db - floor > BED_MARGIN and segment.pause_db > -50) or segment.pause_db > LOUD_PAUSE
    segment.clipped = sum(1 for t in clips if segment.start <= t <= segment.end)
    return segment


def judge(segment: Segment, *, speaker_floor: float | None = None) -> Segment:
    reasons = segment.reasons
    if segment.duration < MIN_SEGMENT:
        reasons.append(f"too short ({segment.duration}s)")
    if segment.bed:
        reasons.append(f"something plays under the pauses ({segment.pause_db} dBFS, room tone {segment.room_db} dBFS)")
    if segment.clipped > CLIP_LIMIT:
        reasons.append(f"clipped ({segment.clipped} flat-topped runs)")
    if segment.snr_db is not None and segment.snr_db < REVIEW_SNR:
        reasons.append(f"noisy ({segment.snr_db} dB speech over pauses)")
    if speaker_floor is not None and segment.speaker is not None and segment.speaker < speaker_floor:
        reasons.append(f"not Krish's voice (similarity {segment.speaker:.2f})")
    if segment.speaker is None:
        segment.notes.append("speaker not verified")
    if reasons:
        segment.tier = "rejected"
    elif segment.snr_db is not None and segment.snr_db >= CLEAN_SNR:
        segment.tier = "clean"
    else:
        segment.tier = "review"
        reasons.append(f"good, not studio ({segment.snr_db} dB speech over pauses)")
    return segment


ENVELOPE_FLOOR = -60.0  # dB; below this everything is "quiet", so gated and encoded copies still line up
SAME_AUDIO = 0.9  # normalised correlation of loudness contours; different speech sits far lower


def envelope(db):
    import numpy

    return numpy.maximum(numpy.asarray(db, dtype=numpy.float32), ENVELOPE_FLOOR)


def best_match(piece, whole) -> float:
    """Highest normalised cross-correlation of a segment's loudness contour anywhere inside another file's."""
    import numpy

    a = numpy.asarray(piece, dtype=numpy.float64)
    b = numpy.asarray(whole, dtype=numpy.float64)
    m, n = len(a), len(b)
    if m < 50 or n < m or a.std() < 1e-6:
        return 0.0
    a = (a - a.mean()) / (a.std() * m)
    size = 1 << int(numpy.ceil(numpy.log2(n + m)))
    corr = numpy.fft.irfft(numpy.fft.rfft(b, size) * numpy.fft.rfft(a[::-1], size), size)[m - 1:n]
    sums = numpy.concatenate(([0.0], numpy.cumsum(b)))
    squares = numpy.concatenate(([0.0], numpy.cumsum(b * b)))
    window_mean = (sums[m:] - sums[:-m]) / m
    window_std = numpy.sqrt(numpy.maximum((squares[m:] - squares[:-m]) / m - window_mean ** 2, 1e-12))
    return float(numpy.max(corr / window_std))


def repeat_of(segment: "Segment", own, others: dict) -> str | None:
    """The key of an already-kept file that contains this segment's audio, if any."""
    piece = own[int(segment.start / FRAME):int(segment.end / FRAME)]
    for key, whole in others.items():
        if best_match(piece, whole) >= SAME_AUDIO:
            return key
    return None


@dataclass
class VoiceRead:
    source: str
    duration: float
    room_tone_db: float
    loudness: dict
    heard: str
    segments: list[Segment]
    envelope: object = None  # loudness contour, FRAME seconds per value, for finding the same audio in other cuts

    def minutes(self, tier: str) -> float:
        return round(sum(s.duration for s in self.segments if s.tier == tier) / 60, 2)

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceRead":
        import base64

        import numpy

        fields = Segment.__dataclass_fields__
        segments = [Segment(**{k: v for k, v in row.items() if k in fields}) for row in data["segments"]]
        contour = None
        if data.get("envelope"):
            contour = numpy.frombuffer(base64.b64decode(data["envelope"]), dtype=numpy.float16).astype(numpy.float32)
        return cls(data["source"], data["duration"], data["room_tone_db"], data["loudness"], data["heard"], segments, contour)

    def as_dict(self) -> dict:
        import base64

        import numpy

        contour = (base64.b64encode(numpy.asarray(self.envelope, dtype=numpy.float16).tobytes()).decode()
                   if self.envelope is not None else None)
        return {"source": self.source, "duration": self.duration, "room_tone_db": self.room_tone_db, "envelope": contour,
                "loudness": self.loudness, "heard": self.heard,
                "minutes": {t: self.minutes(t) for t in ("clean", "review", "rejected")},
                "segments": [s.as_dict() for s in self.segments]}


def read(path: Path, *, heard=None, verifier=None, speaker_floor: float = 0.45) -> VoiceRead:
    """Measure every sentence-bounded segment of one recording. Nothing is written."""
    samples = media.samples16k(path)
    db = frame_db(samples)
    floor = room_tone(db)
    heard = heard or cw_audio.transcribe(path)
    pieces = heard.segments if heard.heard == "words" else []
    segments = group(pieces)
    clips = media.clip_events(path) if segments else []
    for segment in segments:
        measure(segment, db, heard.words, floor, clips)
        if verifier is not None and not segment.reasons:
            segment.speaker = verifier.similarity(samples[int(segment.start * RATE):int(segment.end * RATE)], RATE)
        judge(segment, speaker_floor=speaker_floor if verifier is not None else None)
    return VoiceRead(path.name, round(len(samples) / RATE, 2), round(floor, 1), cw_audio.loudness(path),
                     heard.heard if heard.heard == "words" else f"{heard.heard}:{heard.heard_class}", segments,
                     envelope(db))
