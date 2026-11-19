"""Hindi captions: Hinglish words through auto_caption_clip, and the font by script."""
import os

import pytest

from silentshorts.render import hooks, subtitles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tr(language="hi"):
    words = [{"word": " कैसे", "start": 0.0, "end": 0.4}, {"word": " हैं", "start": 0.4, "end": 0.8},
             {"word": " आप", "start": 1.0, "end": 1.4}]
    return {"language": language, "segments": [{"start": 0.0, "end": 1.4, "text": "कैसे हैं आप", "words": words}]}


def _captioned(tmp_path, monkeypatch, script, language="hi"):
    main = pytest.importorskip("silentshorts.pipeline.main")
    clip = str(tmp_path / "x.mp4")
    open(clip, "wb").close()
    seen = {}

    def fake_generate_ass(transcript, *a, **kw):
        seen["transcript"] = transcript
        return False  # stop before ffmpeg
    monkeypatch.setattr(subtitles, "generate_ass", fake_generate_ass)
    if script is None:
        monkeypatch.delenv("HINDI_SCRIPT", raising=False)
    else:
        monkeypatch.setenv("HINDI_SCRIPT", script)
    tr = _tr(language)
    main.auto_caption_clip(clip, tr, 0.0, 3.0)
    return seen["transcript"], tr


def test_hinglish_job_burns_roman_words_with_the_same_timings(tmp_path, monkeypatch):
    sent, original = _captioned(tmp_path, monkeypatch, "hinglish")
    words = sent["segments"][0]["words"]
    assert [w["word"] for w in words] == [" kaise", " hain", " aap"]
    assert [(w["start"], w["end"]) for w in words] == [(0.0, 0.4), (0.4, 0.8), (1.0, 1.4)]
    assert original["segments"][0]["words"][0]["word"] == " कैसे"  # stored transcript untouched


def test_default_script_is_hinglish(tmp_path, monkeypatch):
    sent, _ = _captioned(tmp_path, monkeypatch, None)
    assert sent["segments"][0]["words"][0]["word"] == " kaise"


def test_devanagari_job_and_other_languages_are_left_alone(tmp_path, monkeypatch):
    sent, original = _captioned(tmp_path, monkeypatch, "devanagari")
    assert sent is original
    sent, original = _captioned(tmp_path, monkeypatch, "hinglish", language="en")
    assert sent is original


def test_ass_font_by_script(tmp_path):
    out = tmp_path / "s.ass"
    subtitles.generate_ass(_tr(), 0.0, 2.0, str(out), font_name="Anton")
    text = out.read_text(encoding="utf-8-sig")
    assert "Style: Default,Noto Sans Devanagari," in text and "कैसे" in text
    out2 = tmp_path / "e.ass"
    latin = {"segments": [{"words": [{"word": " hello", "start": 0.0, "end": 0.5}]}]}
    subtitles.generate_ass(latin, 0.0, 2.0, str(out2), font_name="Anton")
    assert "Style: Default,Anton," in out2.read_text(encoding="utf-8-sig")


def test_font_for_text():
    assert subtitles.font_for_text("Anton", ["hello", "नमस्ते"]) == "Noto Sans Devanagari"
    assert subtitles.font_for_text("Anton", ["hello"]) == "Anton"
    assert subtitles.font_for_text("Anton", []) == "Anton"


def test_bundled_font_has_the_glyphs_and_the_others_do_not():
    ttlib = pytest.importorskip("fontTools.ttLib")
    cmap = lambda name: ttlib.TTFont(os.path.join(ROOT, "fonts", name)).getBestCmap()
    deva = cmap("NotoSansDevanagari-Bold.ttf")
    assert all(ord(c) in deva for c in "कखगअआ्ंँ़")
    for other in ("Anton-Regular.ttf", "Montserrat-ExtraBold.ttf", "NotoSerif-Bold.ttf"):
        assert not any(0x900 <= cp <= 0x97F for cp in cmap(other))
    assert os.path.exists(os.path.join(ROOT, "fonts", "NotoSansDevanagari-OFL.txt"))


def test_hook_picks_the_devanagari_font(tmp_path, monkeypatch):
    used = []
    real = hooks.ImageFont.truetype
    monkeypatch.setattr(hooks, "download_font_if_needed", lambda: None)
    monkeypatch.setattr(hooks.ImageFont, "truetype",
                        lambda path, size, *a, **k: used.append(os.path.basename(path)) or real(
                            os.path.join(ROOT, path) if not os.path.isabs(path) else path, size, *a, **k))
    hooks.create_hook_image("क्या बात है", 800, str(tmp_path / "h.png"), font="anton")
    hooks.create_hook_image("what a day", 800, str(tmp_path / "e.png"), font="anton")
    assert used[0] == "NotoSansDevanagari-Bold.ttf" and used[-1] == "Anton-Regular.ttf"
