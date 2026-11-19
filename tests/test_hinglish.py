"""Devanagari -> Hinglish: rule mapper (schwa deletion), the common-word
dictionary, and the per-word caption path (timings must never move)."""
import pytest

from silentshorts.render import hinglish
from silentshorts.render.hinglish import _romanize, transliterate

# Strict rules only (no dictionary): the mapper itself.
RULES = {
    "कैसे": "kaise", "जानता": "jaanta", "मतलब": "matlab", "समझ": "samajh",
    "समझना": "samajhna", "लड़का": "ladka", "कमल": "kamal", "अगर": "agar",
    "सत्य": "saty", "मन्दिर": "mandir", "प्यार": "pyaar", "सुबह": "subah",
    "बारह": "baarah", "ज्ञान": "gyaan", "विज्ञान": "vigyaan", "क्षमा": "kshama",
    "श्रद्धा": "shraddha", "कहानी": "kahaani", "जिंदगी": "jindagi", "कंपनी": "kampani",
    "संसार": "sansaar", "बरसात": "barsaat", "नमस्ते": "namaste", "स्कूल": "skool",
    "करना": "karna", "चलता": "chalta", "बनाना": "banaana", "पानी": "paani",
    "ठीक": "theek", "दूर": "door", "आम": "aam", "ऊपर": "oopar", "एक": "ek",
    "ज़रा": "zara", "फ़ोन": "fon", "बड़ा": "bada", "ढ़ाई": "dhaai", "चाँद": "chaand",
    "दुःख": "duhkh", "रात": "raat", "नाम": "naam", "देश": "desh", "ऑफ़िस": "ofis",
}

# With the dictionary: the spellings people actually type.
COMMON = {
    "है": "hai", "हैं": "hain", "नहीं": "nahi", "मैं": "main", "में": "mein", "और": "aur",
    "क्या": "kya", "यह": "yeh", "यही": "yahi", "तो": "toh", "भी": "bhi", "कि": "ki",
    "से": "se", "को": "ko", "के": "ke", "की": "ki", "का": "ka", "हम": "hum", "आप": "aap",
    "वो": "woh", "जानता": "jaanta", "कैसे": "kaise", "बहुत": "bahut", "अच्छा": "achha",
}


@pytest.mark.parametrize("deva,roman", RULES.items())
def test_rule_mapper(deva, roman):
    assert _romanize(deva) == roman


@pytest.mark.parametrize("deva,roman", COMMON.items())
def test_common_words(deva, roman):
    assert transliterate(deva) == roman


def test_phrases_and_mixed_text():
    assert transliterate("क्या बात है") == "kya baat hai"
    assert transliterate("मैं नहीं जानता।") == "main nahi jaanta."
    assert transliterate("आज का video बहुत अच्छा है!") == "aaj ka video bahut achha hai!"
    assert transliterate("१२३ रुपये") == "123 rupaye"
    assert transliterate("hello, world 42") == "hello, world 42"  # no Devanagari: untouched


def test_output_is_lowercase_roman():
    out = transliterate("भारत की राजधानी दिल्ली है। अमेरिका में सरकार")
    assert out == out.lower() and not hinglish.has_devanagari(out)


def test_normalize_script():
    assert hinglish.normalize_script("Devanagari") == "devanagari"
    assert hinglish.normalize_script("hinglish") == "hinglish"
    assert hinglish.normalize_script("x") == "hinglish" and hinglish.normalize_script(None) == "hinglish"


def _hi_transcript():
    words = [{"word": " कैसे", "start": 0.0, "end": 0.4}, {"word": " हैं", "start": 0.4, "end": 0.7},
             {"word": " आप?", "start": 0.9, "end": 1.2}]
    return {"language": "hi", "text": "कैसे हैं आप?",
            "segments": [{"start": 0.0, "end": 1.2, "text": "कैसे हैं आप?", "words": words}]}


def test_captions_are_transliterated_per_word_with_timings_unchanged():
    tr = _hi_transcript()
    out = hinglish.for_captions(tr, "hinglish")
    ow, iw = out["segments"][0]["words"], tr["segments"][0]["words"]
    assert [w["word"] for w in ow] == [" kaise", " hain", " aap?"]
    assert [(w["start"], w["end"]) for w in ow] == [(w["start"], w["end"]) for w in iw]
    assert tr["segments"][0]["words"][0]["word"] == " कैसे"  # the stored transcript is untouched


def test_captions_left_alone_for_devanagari_and_other_languages():
    tr = _hi_transcript()
    assert hinglish.for_captions(tr, "devanagari") is tr
    en = {"language": "en", "segments": [{"text": "hi", "words": [{"word": "hi", "start": 0, "end": 1}]}]}
    assert hinglish.for_captions(en, "hinglish") is en
