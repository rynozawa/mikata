from openclaw_companion.distraction import detect_distraction


def test_detects_x_tab() -> None:
    signal = detect_distraction("Home / X - Google Chrome")

    assert signal is not None
    assert signal.category == "social"


def test_detects_game_tab() -> None:
    signal = detect_distraction("Steam - Library")

    assert signal is not None
    assert signal.category == "game"


def test_ignores_work_window() -> None:
    assert detect_distraction("Windows Terminal - OpenClaw Companion") is None
