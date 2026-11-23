"""A range piece fetched by stream copy (no force_keyframes_at_cuts) starts at
the keyframe before the range, the pre-roll hidden by the mp4 edit list. The
pipeline relies on ffmpeg honouring it: piece t=0 must be the range start."""
import shutil
import subprocess

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")

from silentshorts.render.ffmpeg_utils import cut_clip  # noqa: E402

RANGE_START = 3.3   # not on a keyframe (-g 48 at 24 fps: one every 2 s)


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("piece")
    src, piece = str(d / "src.mp4"), str(d / "piece.mp4")
    _ff("-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24",
        "-f", "lavfi", "-i", "anoisesrc=sample_rate=48000:amplitude=0.3:seed=7",
        "-t", "12", "-c:v", "libx264", "-g", "48", "-pix_fmt", "yuv420p",
        "-c:a", "aac", src)
    # What yt-dlp's ffmpeg downloader runs for a section without forced keyframes.
    _ff("-ss", str(RANGE_START), "-t", "7", "-i", src, "-c", "copy", piece)
    return d, src, piece


def _gray(path):
    return np.frombuffer(subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-"]),
        np.uint8).reshape(-1, 180, 320)


def _pcm(path):
    return np.frombuffer(subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-f", "s16le", "-"]), np.int16)


def _best_shift(x, y, span):
    def err(sh):
        k = min(len(x), len(y)) - abs(sh)
        a, b = x[max(0, sh):max(0, sh) + k], y[max(0, -sh):max(0, -sh) + k]
        return np.abs(a.astype(np.int64) - b.astype(np.int64)).mean()
    return min(span, key=err), err(min(span, key=err))


def test_cut_from_copied_piece_matches_cut_from_source(media, monkeypatch):
    monkeypatch.setenv("AUDIO_NORMALIZE", "0")
    d, src, piece = media
    a, b = str(d / "from_src.mp4"), str(d / "from_piece.mp4")
    cut_clip(src, a, RANGE_START + 1.0, RANGE_START + 4.0, 1)
    cut_clip(piece, b, 1.0, 4.0, 1)
    fa, fb = _gray(a), _gray(b)
    assert abs(len(fa) - 72) <= 1 and abs(len(fb) - 72) <= 1
    # The first frame may round to its neighbour (<= 1 frame, 42 ms here);
    # a piece read without its edit list would be off by the whole pre-roll.
    shift, err = _best_shift(fa, fb, range(-30, 31))
    assert abs(shift) <= 1 and err < 1.0
    # Audio is cut by sample (noise, so any lag would show): no lag at all.
    lag, _ = _best_shift(_pcm(a), _pcm(b), range(-480, 481, 8))
    assert lag == 0


def test_layout_picker_reads_every_sample_of_a_copied_piece(media):
    pytest.importorskip("cv2")
    from silentshorts.layouts import layout_picker
    _, _, piece = media
    assert len(layout_picker.sample_frames(piece, n=12, width=320)) == 12
