"""Code moved into amdtool IS the committed code.

Each moved function is compared with its original in python/*.py as committed
at LEGACY_REV. The comparison is on the AST (via ast.unparse), with docstrings
set aside, and every difference must be one of the listed, harmless kinds. Every
constant those functions read is compared by value.

This matters beyond tidiness. The blind-search registration fixes its composite
as "identical to seep_detect.s2_composite", while the extraction runs amdtool's
copy. This file is the code-level proof of that identity. The numeric proof is
the live re-extraction in the refactor gate.
"""
import ast
import difflib

import pytest

import amdtool.imagery as im
import amdtool.stats as st

# (legacy module, function, amdtool module, allowed difference)
MOVED = [
    ("seep_detect", "s2_composite", im, "imports"),
    ("seep_detect", "l8_composite", im, "imports"),
    ("seep_detect", "index_image", im, "imports"),
    ("seep_detect", "_chunks", im, None),
    ("seep_detect", "extract_buffers", im, "print_to_log"),
    ("cmd_detect", "l8_composite_season", im, "imports"),
    ("gee_classify", "process_landsat", im, None),
    ("gee_classify", "add_indices", im, None),
    ("gee_classify", "composite_for_region", im, None),
    ("gee_classify", "water_term", im, "named_water_threshold"),
    ("water_indices", "green_nir_ee", im, None),
    ("water_indices", "ndvi_stress_ee", im, None),
    ("seep_detect", "auc", st, None),
    ("seep_detect", "best_threshold", st, None),
    ("seep_detect", "j_at", st, None),
    ("seep_detect", "_prep_folds", st, None),
    ("seep_detect", "_worst_j_fast", st, "tie_groups"),   # audit item 9, deliberate
    ("seep_detect", "loro_worst_j", st, None),
    ("seep_detect", "perm_p_within_region", st, None),
    ("seep_detect", "benjamini_hochberg", st, None),
    ("seep_detect", "variance_split", st, None),
    ("seep_detect", "spearman", st, None),
    ("cmd_confound", "_rank", st, "numpy_import"),
    ("cmd_confound", "perm_p_within", st, None),
    # cmd_confound.partial_spearman differs by the audit-7 guard; its numbers are
    # proven unchanged by tests/test_golden.py, not by source identity.
]


def _functions(source):
    return {n.name: n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}


def _without_docstring(fn):
    body = list(fn.body)
    first = body[0] if body else None
    if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) \
            and isinstance(first.value.value, str):
        body = body[1:]
    clone = ast.FunctionDef(name=fn.name, args=fn.args, body=body or [ast.Pass()],
                            decorator_list=fn.decorator_list, returns=fn.returns,
                            type_comment=None)
    return ast.unparse(ast.fix_missing_locations(clone)).splitlines()


def _changes(old_fn, new_fn):
    removed, added = [], []
    for line in difflib.unified_diff(_without_docstring(old_fn), _without_docstring(new_fn),
                                     n=0, lineterm=""):
        if line.startswith(("---", "+++", "@@")):
            continue
        (removed if line.startswith("-") else added).append(line[1:].strip())
    return removed, added


@pytest.mark.parametrize("legacy_name,func,module,allowed", MOVED,
                         ids=["%s.%s" % (m[0], m[1]) for m in MOVED])
def test_moved_function_is_the_committed_function(legacy_name, func, module, allowed, legacy):
    old_src = open(legacy(legacy_name).__file__, encoding="utf-8").read()
    new_src = open(module.__file__, encoding="utf-8").read()
    removed, added = _changes(_functions(old_src)[func], _functions(new_src)[func])

    if allowed is None:
        assert (removed, added) == ([], []), (removed, added)
    elif allowed == "imports":
        assert added == [] and removed, (removed, added)
        assert all(r.startswith(("from ", "import ")) for r in removed), removed
    elif allowed == "numpy_import":
        assert (removed, added) == ([], ["import numpy as np"]), (removed, added)
    elif allowed == "print_to_log":
        assert removed == ["print('      memory limit - retrying at batch=%d' % size)"], removed
        assert added == ["log.info('memory limit - retrying at batch=%d', size)"], added
    elif allowed == "tie_groups":
        assert removed == ["for i in tr:"], removed
        assert added == ["for k, i in enumerate(tr):",
                         "if k + 1 < len(tr) and scores[tr[k + 1]] == scores[i]:",
                         "continue"], added
    elif allowed == "named_water_threshold":
        assert len(removed) == len(added) == 1, (removed, added)
        assert removed[0].replace("T['water']", "WATER_MNDWI") == added[0]
    else:
        raise AssertionError(allowed)


def test_every_constant_the_composites_read_is_unchanged(legacy):
    gc, wi, ms = legacy("gee_classify"), legacy("water_indices"), legacy("match_scenes")
    sd, cd = legacy("seep_detect"), legacy("cmd_detect")
    pairs = {
        "START": gc.START, "END": gc.END, "V3_MONTHS": gc.V3_MONTHS,
        "WATER_MNDWI": gc.T["water"], "EPS": wi.EPS, "S2_MAP": ms.S2_MAP,
        "S2_MAX_CLOUD": sd.S2_MAX_CLOUD, "S2_MAX_SCENES": sd.S2_MAX_SCENES,
        "L8_MAX_SCENES": cd.L8_MAX_SCENES, "MIN_SCENES": sd.MIN_SCENES,
        "INDEX_BANDS": sd.INDEX_BANDS,
    }
    wrong = {k: (getattr(im, k), v) for k, v in pairs.items() if getattr(im, k) != v}
    assert not wrong, wrong
