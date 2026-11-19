"""Per-language notes appended to the moment-picker prompts, and the copy fix-up.

The prompt templates stay untouched (tests format them by name); the call site
adds one note after the formatted prompt. Only Hindi has notes today.
"""
from silentshorts.render import hinglish

COPY_FIELDS = ("viral_hook_text", "video_title_for_youtube_short",
               "video_description_for_tiktok", "video_description_for_instagram")

_JUDGE = "The transcript is in Hindi (Devanagari). Judge it as Hindi."
# A 4B model ignored a bare "write in Hinglish" at the end of the prompt and answered in
# English (measured on a real Hindi talk); with an example, and said at both ends, it complied.
_HINGLISH = ("Write the title, hook text and descriptions in Hinglish: Hindi in Roman letters, "
             "the way people type it on Instagram, for example \"yeh trick kaise kaam karti hai\" or "
             "\"kya aap jaante hain?\". Not English. Do not use Devanagari.")
_DEVANAGARI = ("Write the title, hook text and descriptions in Hindi, in Devanagari script, "
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
