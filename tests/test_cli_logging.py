"""The python/ CLIs still print amdtool's progress lines exactly as they did.

amdtool logs rather than prints, so a host application controls where messages
go. python/_amdtool_path.py routes the `amdtool` logger to stdout with the
six-space prefix the scripts used. That keeps lines such as
"      memory limit - retrying at batch=N" - which docs/OPERATOR_GUIDE.md
section 0 tells users to expect - on screen.
"""
import logging


def test_retry_line_prints_exactly_as_the_scripts_did(capfd):
    import _amdtool_path  # noqa: F401
    logging.getLogger("amdtool.imagery").info("memory limit - retrying at batch=%d", 12)
    out, _ = capfd.readouterr()
    assert out == "      memory limit - retrying at batch=12\n"


def test_importing_the_shim_twice_does_not_duplicate_lines(capfd):
    import importlib

    import _amdtool_path
    importlib.reload(_amdtool_path)
    logging.getLogger("amdtool.stats").info("once")
    out, _ = capfd.readouterr()
    assert out.count("once") == 1


def test_the_library_alone_does_not_configure_logging():
    import amdtool  # noqa: F401
    for name in ("amdtool.imagery", "amdtool.stats", "amdtool.severity"):
        assert not logging.getLogger(name).handlers
