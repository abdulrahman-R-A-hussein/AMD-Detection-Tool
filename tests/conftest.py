"""Make the in-repo library and the legacy scripts importable without an install.

`pip install -e .` makes `amdtool` importable on its own; this keeps
`pytest` working from a bare clone too. `python/` is added for the golden
tests, which check that the library still reproduces what the legacy scripts
produced.
"""
import importlib.util
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "src"), os.path.join(ROOT, "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# The last commit before any python/ script became an amdtool wrapper. Parity
# tests import the scripts AS COMMITTED THERE, so they stay meaningful after
# the working copy of a script has turned into a re-export of the library.
LEGACY_REV = "ad05971"


@pytest.fixture
def legacy(tmp_path):
    """legacy("seep_detect") -> python/seep_detect.py exactly as of LEGACY_REV."""
    def load(name):
        try:
            src = subprocess.run(["git", "show", "%s:python/%s.py" % (LEGACY_REV, name)],
                                 cwd=ROOT, capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            pytest.skip("git history for python/%s.py unavailable: %s" % (name, exc))
        path = tmp_path / ("legacy_%s.py" % name)
        path.write_bytes(src)
        spec = importlib.util.spec_from_file_location("legacy_%s" % name, str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return load
