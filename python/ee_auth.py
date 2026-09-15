"""One place for Earth Engine authentication.

**Since 2026-09-14 this is a thin wrapper over ``amdtool.auth``.** It passes the
legacy key path and only ``$GEE_SERVICE_ACCOUNT_KEY``, so resolution here is
unchanged; ``amdtool.auth`` used directly also accepts SpectraLab's
``$GEE_SERVICE_ACCOUNT_JSON``. ``tests/test_auth.py`` checks every path below
against this file as committed before the change.

Replaces five identical copies of ``init_ee()`` - in gee_classify,
catchment_delineation, catchment_dem, match_scenes and watershed_nap - each of
which hard-coded a service-account key path inside a *sibling repository* on
the author's machine. On any other machine every Earth Engine script died with
a bare ``FileNotFoundError`` naming a directory that does not exist there, and
nothing said a service account was what was wanted.

Resolution order, first match wins:

  1. ``$GEE_SERVICE_ACCOUNT_KEY`` - path to a service-account JSON key.
  2. The author's legacy key path, if that file exists. This keeps the
     original machine working with no configuration at all.
  3. ``$GEE_PROJECT`` - a Google Cloud project id. Uses the personal
     credentials stored by ``earthengine authenticate``, which is what most
     new users will have; a service account is not required.
  4. Otherwise a ``RuntimeError`` that says exactly what to set up.

The key file's contents are never printed.
"""

import os

import _amdtool_path  # noqa: F401
from amdtool import auth as _auth
from amdtool.auth import ENV_KEY, ENV_PROJECT, SETUP_HELP  # noqa: F401

LEGACY_KEY = r"D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json"


def resolve_credentials():
    """Decide how to authenticate, without contacting Earth Engine.

    Returns ``("service_account", key_path)`` or ``("user", project_id)``.
    Raises ``RuntimeError`` with setup instructions when nothing is configured.
    """
    return _auth.resolve_credentials(legacy_key=LEGACY_KEY, env_keys=(ENV_KEY,))


def init_ee():
    """Initialise Earth Engine and return the ``ee`` module."""
    return _auth.init_ee(legacy_key=LEGACY_KEY, env_keys=(ENV_KEY,))


if __name__ == "__main__":
    # `python python/ee_auth.py` - a credentials check that touches nothing else.
    try:
        m, d = resolve_credentials()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
    where = os.path.basename(d) if m == "service_account" else d
    print("credentials: %s (%s)" % (m, where))
    init_ee()
    print("Earth Engine initialised OK")
