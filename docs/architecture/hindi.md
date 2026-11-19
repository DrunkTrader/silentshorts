# Hindi and Hinglish

Job fields on `/api/process` (also JSON and the Telegram panel's Language / Hindi text):

- `language`: `auto` (default), `en`, `hi`. Anything else means `auto`. Stored in the job env as
  `TRANSCRIBE_LANGUAGE`.
- `hindi_script`: `hinglish` (default) or `devanagari`. Env `HINDI_SCRIPT`. Only read when the
  transcript language is `hi`; English and every other language are untouched.

## Transcription (`transcribe_backends`)

- `auto`: `detect_language` of the default Whisper model on the first 30 s (one encoder pass, no
  decode), then one transcription with the language fixed. `en`/`hi` skip the detection.
- `WHISPER_MODEL_HI` (unset by default) replaces the model when the language is `hi`, e.g.
  `collabora/faster-whisper-small-hindi` (CTranslate2, fetched by repo id on first use).
  The singleton is keyed per model and the old one is unloaded before the new one loads, so the two
  are never resident together; `release_models()` is still called after every ASR.
- `hi` never goes through Parakeet (no Hindi). `WHISPER_VAD` is unchanged.
- Script drift: `hi` expects Devanagari; Latin words in it are normal, Cyrillic/Greek count as drift.

## LLM (`llm_backend.model_name(language)`)

For `hi`, every transcript call (score, detail, silent copy) uses `LLM_MODEL_HI` on
`LLM_BASE_URL_HI` (default `LLM_BASE_URL`). The choice is made once in `get_viral_clips`;
`generate_json` finds the matching server from the model name. The Gemini path keeps its model.
Models without a thinking mode (Gemma 3 on Ollama) accept `LLM_REASONING_EFFORT=none` but answer
400 "does not support thinking" to other values; the call is repeated once without the field.

Prompts get a note at the call site (`selection/language_notes.py`), templates are untouched:
"judge it as Hindi", and for copy (detail, silent copy) "write in Hinglish, no Devanagari" or
"in Devanagari". A Hinglish job whose model returned Devanagari anyway has the title, hook and
descriptions transliterated (`language_notes.finalize_copy`): the hook and caption fonts have no
Devanagari glyphs.

## Hinglish (`render/hinglish.py`)

Rule-based Devanagari to Roman: vowels, matras, nukta, anusvara, chandrabindu, visarga, virama,
conjuncts, digits, schwa deletion (`कैसे` kaise, `जानता` jaanta), plus `COMMON`, about 300 frequent
words with the spelling people type (`है` hai, `में` mein). No LLM, no dependency. Output is
lowercase; English words and punctuation stay as they are.

Captions are transliterated per word (`for_captions`), never per segment: `start`/`end` are copied.
The stored transcript stays Devanagari for the LLM, the transcript views and the editor. Only the
job's auto-captions use it; the clip editor's own subtitle re-render reads the stored transcript.

## Devanagari rendering

Anton, Montserrat and Noto Serif have no Devanagari. `fonts/NotoSansDevanagari-Bold.ttf` (SIL OFL,
`NotoSansDevanagari-OFL.txt`) is used by `subtitles.generate_ass` and `hooks.create_hook_image`
whenever the text has Devanagari. The Dockerfile copies `fonts/*.ttf` into fontconfig, so no change
there. The font has no Latin glyphs: in the ASS path libass falls back to another font for English
words; the PIL hook overlay does not, so a Devanagari hook with English words shows boxes for them.
