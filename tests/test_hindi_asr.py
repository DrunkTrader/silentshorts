"""Language handling in ASR: auto/en/hi, the Hindi model, drift for Devanagari.
Fake Whisper only; nothing is downloaded."""
import sys
import types
from types import SimpleNamespace

import pytest

from silentshorts.pipeline import transcribe_backends as tb


@pytest.fixture
def fake_whisper(monkeypatch):
    """A faster_whisper whose models record who they are and what they were asked."""
    created, calls, unloaded = [], [], []

    class FakeModel:
        def __init__(self, size, device=None, compute_type=None):
            self.size = size
            self.model = SimpleNamespace(unload_model=lambda to_cpu=False: unloaded.append(size))
            created.append(size)

        def detect_language(self, audio):
            return calls.append(("detect", self.size)) or ("hi", 0.97, [])

        def transcribe(self, path, **params):
            calls.append(("transcribe", self.size, params.get("language")))
            seg = SimpleNamespace(start=0.0, end=1.0, text=" नमस्ते", words=[
                SimpleNamespace(word=" नमस्ते", start=0.0, end=1.0)])
            return iter([seg]), SimpleNamespace(language=params.get("language") or "en", duration=1.0)

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=FakeModel))
    monkeypatch.setattr(tb, "_whisper_model", None)
    monkeypatch.setattr(tb, "_whisper_key", None)
    monkeypatch.setattr(tb, "_read_wav_16k", lambda p: [0.0])
    monkeypatch.setattr(tb.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(tb, "_whisper_device", lambda: "cpu")
    monkeypatch.setenv("WHISPER_MODEL", "small")
    monkeypatch.setenv("WHISPER_MODEL_HI", "collabora/faster-whisper-small-hindi")
    return SimpleNamespace(created=created, calls=calls, unloaded=unloaded)


def test_normalize_language():
    assert [tb.normalize_language(v) for v in ("hi", "EN", "auto", "fr", None, "")] == \
        ["hi", "en", "auto", "auto", "auto", "auto"]


def test_forced_hindi_uses_the_hindi_model_without_detection(fake_whisper):
    out = tb._transcribe_with_whisper("v.mp4", "hi")
    assert fake_whisper.calls == [("transcribe", "collabora/faster-whisper-small-hindi", "hi")]
    assert out["language"] == "hi"


def test_forced_english_uses_the_default_model(fake_whisper):
    tb._transcribe_with_whisper("v.mp4", "en")
    assert fake_whisper.calls == [("transcribe", "small", "en")]


def test_auto_detects_with_default_model_then_switches_to_hindi(fake_whisper):
    out = tb._transcribe_with_whisper("v.mp4", "auto")
    assert fake_whisper.calls == [("detect", "small"),
                                  ("transcribe", "collabora/faster-whisper-small-hindi", "hi")]
    assert out["language"] == "hi"
    # the default model was unloaded when the Hindi one replaced it: never both resident
    assert fake_whisper.unloaded == ["small"]
    assert tb._whisper_key[0] == "collabora/faster-whisper-small-hindi"


def test_auto_non_hindi_stays_on_default_model(fake_whisper, monkeypatch):
    monkeypatch.setattr(tb, "_detect_whisper_language", lambda p: "de")
    tb._transcribe_with_whisper("v.mp4", "auto")
    assert fake_whisper.calls == [("transcribe", "small", "de")]


def test_hindi_without_hindi_model_env_uses_default(fake_whisper, monkeypatch):
    monkeypatch.delenv("WHISPER_MODEL_HI")
    tb._transcribe_with_whisper("v.mp4", "hi")
    assert fake_whisper.calls == [("transcribe", "small", "hi")]


def test_failed_detection_falls_back_to_whisper_own_detection(fake_whisper, monkeypatch):
    monkeypatch.setattr(tb, "_detect_whisper_language", lambda p: None)
    tb._transcribe_with_whisper("v.mp4", "auto")
    assert fake_whisper.calls == [("transcribe", "small", None)]


def test_release_models_unloads_the_hindi_model(fake_whisper):
    tb._transcribe_with_whisper("v.mp4", "hi")
    tb.release_models()
    assert fake_whisper.unloaded == ["collabora/faster-whisper-small-hindi"]
    assert tb._whisper_model is None


def test_transcribe_media_passes_language_and_skips_parakeet_for_hindi(monkeypatch):
    monkeypatch.setattr(tb, "_has_audio_stream", lambda p: True)
    monkeypatch.setenv("TRANSCRIBE_BACKEND", "parakeet")
    monkeypatch.setattr(tb, "_transcribe_with_parakeet",
                        lambda p: pytest.fail("parakeet has no Hindi"))
    seen = []
    monkeypatch.setattr(tb, "_transcribe_with_whisper", lambda p, language="auto": seen.append(language) or {})
    tb.transcribe_media("v.mp4", "hi")
    assert seen == ["hi"]


def test_main_transcribe_video_reads_the_job_language(main, monkeypatch, tmp_path):
    from silentshorts.pipeline import transcribe_backends
    seen = []
    monkeypatch.setattr(transcribe_backends, "transcribe_media",
                        lambda p, language="auto": seen.append(language) or {"language": "hi", "segments": []})
    monkeypatch.setattr(transcribe_backends, "release_models", lambda: None)
    monkeypatch.setenv("TRANSCRIBE_LANGUAGE", "hi")
    main.transcribe_video(str(tmp_path / "a.m4a"))
    assert seen == ["hi"]


def test_hindi_is_not_script_drift():
    deva = "नमस्ते दोस्तों, आज का video"
    assert not tb._segment_drifted(deva, "hi")  # Devanagari is expected, Latin words are fine
    assert tb._segment_drifted("Привет", "hi")  # Cyrillic in a Hindi file is
    assert not tb._segment_drifted(deva, "en")  # unchanged: Devanagari is not drift for latn
