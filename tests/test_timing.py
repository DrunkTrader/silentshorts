from silentshorts.render import timing


def test_nested_steps_count_encode_in_each_and_close_cleanly(capsys):
    timing.set_clip(3)
    with timing.step("outer") as outer:
        with timing.step("inner"):
            with timing.encode():
                pass
        # inner and outer now hold equal counts: only inner may leave the stack
        assert len(timing._stack()) == 1 and timing._stack()[0] is outer
        with timing.step("sibling"):  # equal counts must not confuse the stack
            pass
    out = capsys.readouterr().out.splitlines()
    assert [line.split()[2] for line in out] == ["step=inner", "step=sibling", "step=outer"]
    assert all(line.startswith("TIMING clip=3 ") for line in out)
    assert timing._stack() == []
    timing.set_clip(None)


def test_step_prints_on_error(capsys):
    try:
        with timing.step("boom", clip=1):
            raise RuntimeError("x")
    except RuntimeError:
        pass
    assert "TIMING clip=1 step=boom" in capsys.readouterr().out
    assert timing._stack() == []
