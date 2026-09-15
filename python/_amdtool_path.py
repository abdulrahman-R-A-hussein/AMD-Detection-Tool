"""Make src/amdtool importable from a bare clone.

The python/ scripts are thin wrappers over the `amdtool` package. After
`pip install -e .` this does nothing; without it, it puts the repository's
src/ on sys.path so every documented command keeps working with no install.
Import it before importing amdtool:

    import _amdtool_path  # noqa: F401
"""

import importlib.util
import logging
import os
import sys

if importlib.util.find_spec("amdtool") is None:
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# amdtool logs instead of printing, so a host application decides where messages
# go. The CLIs keep printing them exactly as before - e.g. the
# "      memory limit - retrying at batch=N" lines docs/OPERATOR_GUIDE.md section 0
# tells users to expect.
class _StdoutHandler(logging.StreamHandler):
    """Writes to whatever sys.stdout is when a message is logged, not the object
    it was at import time - so a caller that swaps stdout (a test's capture, a
    GUI log pane) still receives the lines."""

    @property
    def stream(self):
        return sys.stdout

    @stream.setter
    def stream(self, _value):
        pass


_log = logging.getLogger("amdtool")
if not _log.handlers:
    _handler = _StdoutHandler()
    _handler.setFormatter(logging.Formatter("      %(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False
