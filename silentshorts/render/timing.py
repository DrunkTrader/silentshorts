"""Per-step timing lines for the job log.

One line per finished step, e.g.::

    TIMING clip=3 step=reframe encode_s=41.20 wall_s=63.75

``wall_s`` is the step's wall time; ``encode_s`` the part of it spent waiting
on ffmpeg processes that encode video (wrapped in ``encode()``). Clips render
on a thread pool, so the clip number and the open steps are per thread.
"""
import threading
import time
from contextlib import contextmanager

_local = threading.local()


def set_clip(clip):
    """Name the clip this thread is rendering (None for job-level steps)."""
    _local.clip = clip


def _stack():
    if not hasattr(_local, "stack"):
        _local.stack = []
    return _local.stack


@contextmanager
def step(name, clip=None):
    """Time one step and print its TIMING line when it ends (also on error)."""
    clip = clip if clip is not None else getattr(_local, "clip", None)
    rec = {"encode": 0.0}
    stack = _stack()
    stack.append(rec)
    t0 = time.monotonic()
    try:
        yield rec
    finally:
        # By identity: open steps with equal counts compare equal.
        stack[:] = [r for r in stack if r is not rec]
        print(f"TIMING clip={clip if clip is not None else '-'} step={name} "
              f"encode_s={rec['encode']:.2f} wall_s={time.monotonic() - t0:.2f}",
              flush=True)


@contextmanager
def encode():
    """Count the wrapped wall time as encoding in every open step."""
    t0 = time.monotonic()
    try:
        yield
    finally:
        spent = time.monotonic() - t0
        for rec in _stack():
            rec["encode"] += spent
