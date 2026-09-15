"""Make src/amdtool importable from a bare clone.

The python/ scripts are thin wrappers over the `amdtool` package. After
`pip install -e .` this does nothing; without it, it puts the repository's
src/ on sys.path so every documented command keeps working with no install.
Import it before importing amdtool:

    import _amdtool_path  # noqa: F401
"""

import importlib.util
import os
import sys

if importlib.util.find_spec("amdtool") is None:
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
