"""Pick it yourself: the exact range a user asked for, as a clip range.

Either a time range or two quotes found in the stored transcript ("from this
.. to that"). Quotes match on normalized words: case, accents and punctuation
are ignored, Devanagari works as typed, and Hinglish typed against a
Devanagari transcript matches its transliteration (``render.hinglish``).
The result is snapped to word boundaries and held to MIN_SECONDS-MAX_SECONDS.
"""
import re
import unicodedata

from silentshorts.render import hinglish
from silentshorts.render.recut import MAX_TOTAL_SECONDS, transcript_words
from silentshorts.selection.clip_selection import snap_clip_to_words

MIN_SECONDS = 5.0
MAX_SECONDS = MAX_TOTAL_SECONDS   # 180 s: above any job's clip max (CLIP_MAX_CEILING)
_ACCENTS = re.compile("[̀-ͯ]")   # Latin combining marks only: Devanagari keeps its vowel signs


class CutError(ValueError):
    """A request that cannot become a clip; the message is safe to show."""


def tokens(text):
    """Lowercase words without accents or punctuation. Zero-width joiners go."""
    t = _ACCENTS.sub("", unicodedata.normalize("NFKD", str(text or "")))
    t = unicodedata.normalize("NFC", t).casefold()
    out = []
    for ch in t:
        cat = unicodedata.category(ch)
        if cat == "Cf":
            continue
        out.append(" " if cat[0] in "PSZ" or cat == "Cc" else ch)
    return "".join(out).split()


def _loose(tok):
    """Hinglish spellings vary (aa/a, ee/i, oo/u, doubled consonants, w/v)."""
    tok = tok.replace("ee", "i").replace("oo", "u").replace("w", "v")
    return re.sub(r"(.)\1+", r"\1", tok)


def _matches(flat, query):
    """``[(first word index, last word index)]`` of every run of ``query`` tokens."""
    n = len(query)
    return [(flat[p][1], flat[p + n - 1][1]) for p in range(len(flat) - n + 1)
            if [t for t, _ in flat[p:p + n]] == query]


def find_quotes(words, from_text, to_text):
    """``(start, end)`` from the first word of ``from_text`` to the last word
    of the first ``to_text`` after it that makes a MIN-MAX clip. ``words`` are
    ``recut.transcript_words``. Raises CutError with what went wrong."""
    qf, qt = tokens(from_text), tokens(to_text)
    if not qf or not qt:
        raise CutError("Both quotes need at least one word.")
    loose = not hinglish.has_devanagari(f"{from_text} {to_text}") and any(
        hinglish.has_devanagari(w["w"]) for w in words)
    flat = []
    for i, w in enumerate(words):
        text = hinglish.transliterate(w["w"]) if loose else w["w"]
        flat.extend((_loose(t) if loose else t, i) for t in tokens(text))
    if loose:
        qf, qt = [_loose(t) for t in qf], [_loose(t) for t in qt]
    froms, tos = _matches(flat, qf), _matches(flat, qt)
    if not froms:
        raise CutError(f"Could not find “{from_text}” in the transcript.")
    spans = [(words[fa]["s"], words[tb]["e"]) for fa, _ in froms for ta, tb in tos if ta >= fa]
    if not spans:
        raise CutError(f"Could not find “{to_text}” after “{from_text}” in the transcript.")
    for s, e in spans:
        if MIN_SECONDS <= e - s <= MAX_SECONDS:
            return s, e
    s, e = spans[0]
    raise CutError(f"From “{from_text}” to “{to_text}” is {e - s:.0f} s; a clip must be "
                   f"{MIN_SECONDS:g}-{MAX_SECONDS:g} s.")


def resolve(transcript, source_duration, start=None, end=None, from_text=None, to_text=None):
    """The clip range ``(start, end)`` in source seconds for a cut request."""
    words = transcript_words(transcript)
    if from_text is not None or to_text is not None:
        if not words:
            raise CutError("This job has no transcript to search; send a time range instead.")
        start, end = find_quotes(words, from_text or "", to_text or "")
    elif start is None or end is None:
        raise CutError("Send start and end, or from_text and to_text.")
    start, end = float(start), float(end)
    if not (start == start and end == end) or start < 0:   # NaN or negative
        raise CutError("start and end must be seconds from the start of the video.")
    if source_duration and end > float(source_duration) + 0.5:
        raise CutError(f"The video is only {float(source_duration):.0f} s long.")
    if not MIN_SECONDS <= end - start <= MAX_SECONDS:
        raise CutError(f"A clip must be {MIN_SECONDS:g}-{MAX_SECONDS:g} s; this one is {end - start:.1f} s.")
    bound = float(source_duration) if source_duration else end + 1.0   # unknown length: room for the tail
    s, e = snap_clip_to_words(start, min(end, bound), words, bound,
                              min_duration=MIN_SECONDS, max_duration=MAX_SECONDS)
    return s, e
