"""Per-language notes appended to the moment-picker prompts, and the copy fix-up.

The prompt templates stay untouched (tests format them by name); the call site
adds one note after the formatted prompt. Only Hindi has notes today.
"""
from silentshorts.render import hinglish

# ``why`` is shown to the user next to the clip (Telegram, dashboard), so it
# follows the same script rule as the copy.
COPY_FIELDS = ("viral_hook_text", "video_title_for_youtube_short",
               "video_description_for_tiktok", "video_description_for_instagram", "why")

_JUDGE = "The transcript is in Hindi (Devanagari). Judge it as Hindi."
# A 4B model ignored a bare "write in Hinglish" at the end of the prompt and answered in
# English (measured on a real Hindi talk); with an example, and said at both ends, it complied.
# The examples are single words or marked "never copy": full example sentences were
# pasted verbatim into hooks by the 4B model.
_HINGLISH = ("Write the title, hook text, descriptions and why in Hinglish: Hindi in Roman letters, "
             "the way people type it on Instagram. Not English. Do not use Devanagari. "
             "Keep English words, names and acronyms in their normal English spelling "
             "(GTA, UFO, bro, game, video), never spelled out phonetically.")
_DEVANAGARI = ("Write the title, hook text, descriptions and why in Hindi, in Devanagari script, "
               "for example \"यह ट्रिक कैसे काम करती है\". Not English.")


def note(language, script=hinglish.HINGLISH, copy=False):
    if language != "hi":
        return ""
    if not copy:
        return _JUDGE
    return f"{_JUDGE} {_DEVANAGARI if hinglish.normalize_script(script) == hinglish.DEVANAGARI else _HINGLISH}"


def add(prompt, language, script=hinglish.HINGLISH, copy=False):
    """``prompt`` with the language note appended (unchanged for other languages).
    ``copy`` is for prompts whose answer carries titles, hooks or descriptions."""
    n = note(language, script, copy)
    if not n:
        return prompt
    # Copy instructions are said first as well: the prompt's own copy rules come last.
    return f"{n}\n\n{prompt}\n\nNOTE: {n}\n" if copy else f"{prompt}\n\nNOTE: {n}\n"


def finalize_copy(clips, language, script=hinglish.HINGLISH):
    """Hinglish jobs: a model that answered in Devanagari anyway has its copy
    transliterated here, because the hook and caption fonts have no Devanagari.
    Returns how many fields changed. Clips are edited in place."""
    if language != "hi" or hinglish.normalize_script(script) != hinglish.HINGLISH:
        return 0
    changed = 0
    for clip in clips or []:
        for field in COPY_FIELDS:
            value = clip.get(field)
            if isinstance(value, str) and hinglish.has_devanagari(value):
                clip[field] = hinglish.transliterate(value)
                changed += 1
    return changed
