"""Hinglish: Hindi in Roman letters, the way people type it on social media.

A deterministic, local Devanagari -> Roman mapper (no LLM, no dependency).
Transliteration is per word, so a caption keeps every word timing it had:
``hinglish_words`` changes only the ``word`` text, never ``start``/``end``.

Two layers:
  * ``COMMON`` overrides the strict mapping for the frequent words whose
    social-media spelling differs from it (``है`` -> ``hai``, ``में`` -> ``mein``).
  * ``_romanize`` is the rule mapper, with schwa deletion: the inherent "a" of a
    consonant is dropped word-finally and in the V C_ C V context
    (``कैसे`` -> ``kaise``, ``जानता`` -> ``jaanta``, ``मतलब`` -> ``matlab``).

Several spellings are valid for one Hindi word (``achha``/``accha``); the
dictionary fixes the common one and the rules pick a consistent lowercase one.
"""
import re
import unicodedata

HINGLISH = "hinglish"
DEVANAGARI = "devanagari"

_DEVA_RUN = re.compile("[ऀ-ॿ‌‍]+")
_HAS_DEVA = re.compile("[ऀ-ॿ]")


def has_devanagari(text):
    return bool(_HAS_DEVA.search(text or ""))


def normalize_script(value):
    """The job's ``hindi_script`` field: ``devanagari``, anything else is ``hinglish``."""
    return DEVANAGARI if str(value or "").strip().lower() == DEVANAGARI else HINGLISH


_INDEPENDENT = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऑ": "o", "ऍ": "e",
}
_MATRA = {
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ॉ": "o", "ॅ": "e",
}
_CONSONANT = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
}
# consonant + nukta
_NUKTA = {"क": "q", "ख": "kh", "ग": "g", "ज": "z", "ड": "d", "ढ": "dh", "फ": "f", "य": "y"}
_VIRAMA, _NUKTA_MARK = "्", "़"
_ANUSVARA, _CHANDRABINDU, _VISARGA = "ं", "ँ", "ः"
_LABIAL = set("पफबभम")
_DIGITS = {ord("०") + i: str(i) for i in range(10)}
_PUNCT = {"।": ".", "॥": ".", "॰": "."}


def _units(word):
    """Split a Devanagari run into units: dicts with the roman consonant ``c``,
    its vowel ``v`` (None = inherent schwa, "" = virama, else explicit) and a
    nasal/visarga ``coda``. Independent vowels and strays are units with c=""."""
    word = unicodedata.normalize("NFC", word).replace("ज्ञ", "\u0000")  # ज्ञ is one sound, "gy"
    out, i, n = [], 0, len(word)
    while i < n:
        ch = word[i]
        if ch in _CONSONANT or ch == "\u0000":
            roman, i = _CONSONANT.get(ch, "gy"), i + 1
            if i < n and word[i] == _NUKTA_MARK:
                roman = _NUKTA.get(ch, roman)
                i += 1
            unit = {"c": roman, "v": None, "coda": ""}
            if i < n and word[i] in _MATRA:
                unit["v"], i = _MATRA[word[i]], i + 1
            elif i < n and word[i] == _VIRAMA:
                unit["v"], i = "", i + 1
            out.append(unit)
        elif ch in _INDEPENDENT:
            out.append({"c": "", "v": _INDEPENDENT[ch], "coda": ""})
            i += 1
        elif ch in (_ANUSVARA, _CHANDRABINDU, _VISARGA):
            if ch == _VISARGA:
                coda = "h"
            elif ch == _ANUSVARA and i + 1 < n and word[i + 1] in _LABIAL:
                coda = "m"
            else:
                coda = "n"
            if out:
                out[-1]["coda"] += coda
            else:
                out.append({"c": coda, "v": "", "coda": ""})
            i += 1
        elif ch in "‌‍" or ch == _NUKTA_MARK:
            i += 1
        else:
            out.append({"c": ch, "v": "", "coda": "", "raw": True})
            i += 1
    return out


def _has_vowel(u):
    return u["v"] is None or u["v"] != ""


def _romanize(word):
    """Strict rule-based mapping of one Devanagari run, with schwa deletion."""
    units = _units(word)
    keep = [True] * len(units)  # does the unit sound a vowel?
    last = len(units) - 1
    # Right to left, so the decision for a schwa sees the final state of the
    # syllable after it (matlab: b loses it, l keeps it, t loses it).
    for i in range(last, 0, -1):
        u = units[i]
        if u["v"] is not None or u.get("raw") or u["coda"]:
            continue
        if i == last:
            keep[i] = False
        elif (_has_vowel(units[i - 1]) and not units[i - 1]["coda"]  # jindagi: a closed syllable keeps it
              and keep[i + 1] and _has_vowel(units[i + 1])
              and units[i + 1]["c"] != "y"):  # rupaye, samaya: the schwa before ya stays
            keep[i] = False
    out = []
    for i, u in enumerate(units):
        if u.get("raw"):
            out.append(u["c"])
            continue
        v = u["v"]
        if v is None:
            v = "a" if keep[i] else ""
        elif i == last and not u["coda"]:  # word-final matras read short
            v = {"aa": "a", "ee": "i"}.get(v, v)
        out.append(u["c"] + v + u["coda"])
    return "".join(out)


# Frequent words whose social-media spelling differs from the strict mapping.
COMMON = {
    # to be
    "है": "hai", "हैं": "hain", "हूँ": "hoon", "हूं": "hoon", "हो": "ho", "था": "tha", "थी": "thi",
    "थे": "the", "थीं": "thin", "होगा": "hoga", "होगी": "hogi", "होंगे": "honge", "हुआ": "hua",
    "हुई": "hui", "हुए": "hue", "होता": "hota", "होती": "hoti", "होते": "hote", "होना": "hona",
    "नहीं": "nahi", "नही": "nahi", "ना": "na",
    # pronouns
    "मैं": "main", "मैंने": "maine", "में": "mein", "मेरा": "mera", "मेरी": "meri", "मेरे": "mere",
    "मुझे": "mujhe", "मुझको": "mujhko", "हम": "hum", "हमें": "hamein", "हमने": "humne",
    "हमारा": "hamara", "हमारी": "hamari", "हमारे": "hamare",
    "तुम": "tum", "तुम्हें": "tumhe", "तुम्हारा": "tumhara", "तुम्हारी": "tumhari", "तुमने": "tumne",
    "तू": "tu", "तेरा": "tera", "तेरी": "teri", "तेरे": "tere", "तुझे": "tujhe",
    "आप": "aap", "आपका": "aapka", "आपकी": "aapki", "आपके": "aapke", "आपको": "aapko", "आपने": "aapne",
    "वो": "woh", "वह": "woh", "वे": "woh", "वही": "wahi", "यह": "yeh", "ये": "ye", "यही": "yahi",
    "उसे": "use", "उसका": "uska", "उसकी": "uski", "उसके": "uske", "उसने": "usne", "उसको": "usko",
    "उन्हें": "unhe", "उन्होंने": "unhone", "उनका": "unka", "उनकी": "unki", "उनके": "unke",
    "इसे": "ise", "इसका": "iska", "इसकी": "iski", "इसके": "iske", "इसने": "isne", "इसको": "isko",
    "इन": "in", "उन": "un", "अपना": "apna", "अपनी": "apni", "अपने": "apne", "खुद": "khud",
    # question words and places
    "क्या": "kya", "क्यों": "kyun", "क्यूँ": "kyun", "क्योंकि": "kyunki", "कैसे": "kaise",
    "कैसा": "kaisa", "कैसी": "kaisi", "कौन": "kaun", "कब": "kab", "कहाँ": "kahan", "कहां": "kahan",
    "यहाँ": "yahan", "यहां": "yahan", "वहाँ": "wahan", "वहां": "wahan", "किस": "kis",
    "किसी": "kisi", "किसको": "kisko", "कोई": "koi", "कुछ": "kuch", "कितना": "kitna",
    "कितनी": "kitni", "कितने": "kitne",
    # particles and conjunctions
    "और": "aur", "या": "ya", "लेकिन": "lekin", "मगर": "magar", "पर": "par", "तो": "toh",
    "भी": "bhi", "ही": "hi", "तक": "tak", "से": "se", "को": "ko", "के": "ke", "की": "ki",
    "का": "ka", "कि": "ki", "ने": "ne", "पे": "pe", "जो": "jo", "जब": "jab", "तब": "tab",
    "जैसे": "jaise", "जैसा": "jaisa", "जैसी": "jaisi", "फिर": "phir", "अब": "ab", "अभी": "abhi",
    "कभी": "kabhi", "हमेशा": "hamesha", "अगर": "agar", "इसलिए": "isliye", "बल्कि": "balki",
    "चाहे": "chahe", "वाला": "wala", "वाली": "wali", "वाले": "wale", "लिए": "liye",
    "सिर्फ": "sirf", "सिर्फ़": "sirf", "बस": "bas", "बिल्कुल": "bilkul", "बिलकुल": "bilkul",
    "ज़रूर": "zaroor", "जरूर": "zaroor", "शायद": "shayad", "वैसे": "waise", "ऐसा": "aisa",
    "ऐसे": "aise", "ऐसी": "aisi", "इतना": "itna", "इतनी": "itni", "इतने": "itne",
    "उतना": "utna", "जितना": "jitna", "सारा": "saara", "सारे": "saare", "साथ": "saath",
    "बाद": "baad", "पहले": "pehle", "पहला": "pehla", "पहली": "pehli", "आगे": "aage",
    "पीछे": "peeche", "ऊपर": "upar", "नीचे": "neeche", "अंदर": "andar", "बाहर": "bahar",
    # quantity
    "सब": "sab", "सबको": "sabko", "सभी": "sabhi", "बहुत": "bahut", "थोड़ा": "thoda",
    "ज़्यादा": "zyada", "ज्यादा": "zyada", "कम": "kam", "एक": "ek", "दो": "do", "तीन": "teen",
    "चार": "chaar", "पाँच": "paanch", "पांच": "paanch", "छह": "chhe", "छः": "chhe", "सात": "saat",
    "आठ": "aath", "नौ": "nau", "दस": "das", "सौ": "sau", "हज़ार": "hazaar", "हजार": "hazaar",
    "लाख": "lakh", "करोड़": "crore",
    # verbs
    "करना": "karna", "करता": "karta", "करती": "karti", "करते": "karte", "करो": "karo",
    "करें": "karein", "किया": "kiya", "कर": "kar", "करके": "karke", "कहा": "kaha", "कहना": "kehna",
    "कहते": "kehte", "कहता": "kehta", "कहती": "kehti", "बोला": "bola", "बोलना": "bolna",
    "बोलो": "bolo", "देखो": "dekho", "देखा": "dekha", "देखना": "dekhna", "देख": "dekh",
    "देखिए": "dekhiye", "सुनो": "suno", "सुना": "suna", "सुन": "sun", "सुनिए": "suniye",
    "जाना": "jaana", "जाता": "jaata", "जाती": "jaati", "जाते": "jaate", "गया": "gaya",
    "गई": "gayi", "गए": "gaye", "गये": "gaye", "जा": "ja", "जाओ": "jao", "आना": "aana",
    "आया": "aaya", "आई": "aayi", "आए": "aaye", "आओ": "aao", "आ": "aa", "लो": "lo", "ले": "le",
    "लेना": "lena", "लिया": "liya", "दे": "de", "देना": "dena", "दिया": "diya", "देता": "deta",
    "मिला": "mila", "मिलना": "milna", "पता": "pata", "जानता": "jaanta", "जानती": "jaanti",
    "जानते": "jaante", "जान": "jaan", "जानना": "jaanna", "समझ": "samajh", "समझा": "samjha",
    "समझना": "samajhna", "चाहिए": "chahiye", "चाहता": "chahta", "चाहती": "chahti",
    "सकता": "sakta", "सकती": "sakti", "सकते": "sakte", "पड़ता": "padta", "रहा": "raha",
    "रही": "rahi", "रहे": "rahe", "रहना": "rehna", "रहता": "rehta", "लगता": "lagta",
    "लगा": "laga", "लगी": "lagi", "बताओ": "batao", "बता": "bata", "बताइए": "bataiye",
    "बताया": "bataya", "बनाया": "banaya", "बनाना": "banana", "मानो": "maano", "रखना": "rakhna",
    "पूछा": "poocha", "सोचो": "socho", "सोचता": "sochta", "सोचा": "socha",
    # adjectives, nouns
    "अच्छा": "achha", "अच्छी": "achhi", "अच्छे": "achhe", "बुरा": "bura", "सही": "sahi",
    "गलत": "galat", "ठीक": "theek", "बड़ा": "bada", "बड़ी": "badi", "बड़े": "bade",
    "छोटा": "chhota", "नया": "naya", "नई": "nayi", "नए": "naye", "पुराना": "purana",
    "पूरा": "poora", "पूरी": "poori", "दूसरा": "doosra", "सच": "sach", "झूठ": "jhooth",
    "आसान": "aasaan", "मुश्किल": "mushkil", "लोग": "log", "लोगों": "logon", "बात": "baat",
    "बातें": "baatein", "काम": "kaam", "समय": "samay", "आज": "aaj", "कल": "kal", "परसों": "parso",
    "दिन": "din", "रात": "raat", "सुबह": "subah", "शाम": "shaam", "साल": "saal", "घर": "ghar",
    "देश": "desh", "दुनिया": "duniya", "ज़िंदगी": "zindagi", "जिंदगी": "zindagi", "प्यार": "pyaar",
    "दोस्त": "dost", "दोस्तों": "doston", "भाई": "bhai", "यार": "yaar", "भगवान": "bhagwan",
    "पैसा": "paisa", "पैसे": "paise", "मतलब": "matlab", "नाम": "naam", "शुरू": "shuru",
    "खत्म": "khatam", "मदद": "madad", "कोशिश": "koshish", "बच्चा": "bachcha", "बच्चे": "bachche",
    "लड़का": "ladka", "लड़की": "ladki", "आदमी": "aadmi", "औरत": "aurat", "हाँ": "haan",
    "हां": "haan", "अरे": "arre", "वाह": "waah", "भारत": "bharat", "हिंदी": "hindi",
    "हिन्दी": "hindi", "कहानी": "kahani", "सवाल": "sawaal", "जवाब": "jawaab", "वीडियो": "video",
    "चैनल": "channel", "सब्सक्राइब": "subscribe", "लाइक": "like", "शेयर": "share",
    "कमेंट": "comment", "फोन": "phone", "मोबाइल": "mobile", "इंटरनेट": "internet",
    "ऑनलाइन": "online", "टाइम": "time", "फ्री": "free", "सरकार": "sarkar", "पैसों": "paison",
}

# Devanagari digits and the danda are handled by the rules; the dictionary
# keys are stored NFC like the input.
COMMON = {unicodedata.normalize("NFC", k): v for k, v in COMMON.items()}


def transliterate(text, use_common=True):
    """Roman text for ``text``: every Devanagari run is transliterated, the rest
    (English words, digits, punctuation, spaces) is left as it is."""
    def one(m):
        run = unicodedata.normalize("NFC", m.group(0))
        if use_common and run in COMMON:
            return COMMON[run]
        return _romanize(run).lower()
    text = (text or "").translate(_DIGITS)
    for mark, roman in _PUNCT.items():
        text = text.replace(mark, roman)
    return _DEVA_RUN.sub(one, text)


def hinglish_words(words):
    """Copy of a word list ({word, start, end}) with the text transliterated and
    every timing untouched."""
    return [{**w, "word": transliterate(w.get("word", ""))} for w in words]


def for_captions(transcript, script=HINGLISH):
    """The transcript the caption renderer should read: a Hindi transcript with
    ``hinglish`` script gets its words transliterated (per word, timings kept);
    anything else comes back as it was. The stored transcript is never changed."""
    if not transcript or transcript.get("language") != "hi" or normalize_script(script) != HINGLISH:
        return transcript
    segments = [{**seg, "text": transliterate(seg.get("text", "")),
                 "words": hinglish_words(seg.get("words") or [])}
                for seg in transcript.get("segments") or []]
    return {**transcript, "segments": segments}
