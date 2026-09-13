"""One place for Earth Engine authentication.

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

``ee`` is imported inside ``init_ee`` rather than at module level, as the five
originals did, so that modules importing this one still load in an
environment without earthengine-api installed.
"""

import json
import os

LEGACY_KEY = r"D:\dev\VPCA+STEPWISE-REGRESSION\planty-gee-backend-b357c7b51077.json"

ENV_KEY = "GEE_SERVICE_ACCOUNT_KEY"
ENV_PROJECT = "GEE_PROJECT"

SETUP_HELP = """\
Set up ONE of the following, then re-run:

  A) Personal account (simplest)
       1. Register for Earth Engine and enable the Earth Engine API on a
          Google Cloud project:  https://code.earthengine.google.com
       2. pip install earthengine-api
       3. earthengine authenticate
       4. set GEE_PROJECT=<your-cloud-project-id>        (Windows cmd)
          $env:GEE_PROJECT="<your-cloud-project-id>"     (PowerShell)
          export GEE_PROJECT=<your-cloud-project-id>     (bash)

  B) Service account (unattended runs)
       1. In that Cloud project, create a service account and download a
          JSON key.
       2. Register the service account for Earth Engine access - this is a
          separate step from creating it.
       3. set GEE_SERVICE_ACCOUNT_KEY=<path-to-key.json>

See docs/OPERATOR_GUIDE.md section 0.
"""


def resolve_credentials():
    """Decide how to authenticate, without contacting Earth Engine.

    Returns ``("service_account", key_path)`` or ``("user", project_id)``.
    Raises ``RuntimeError`` with setup instructions when nothing is configured.
    """
    key = os.environ.get(ENV_KEY)
    if key:
        if not os.path.isfile(key):
            raise RuntimeError(
                "%s is set, but no file exists at %r.\n\n%s"
                % (ENV_KEY, key, SETUP_HELP))
        return "service_account", key
    if os.path.isfile(LEGACY_KEY):
        return "service_account", LEGACY_KEY
    project = os.environ.get(ENV_PROJECT)
    if project:
        return "user", project
    raise RuntimeError("No Earth Engine credentials found.\n\n" + SETUP_HELP)


def init_ee():
    """Initialise Earth Engine and return the ``ee`` module."""
    mode, detail = resolve_credentials()
    import ee
    if mode == "service_account":
        with open(detail, encoding="utf-8") as fh:
            info = json.load(fh)
        ee.Initialize(ee.ServiceAccountCredentials(info["client_email"], detail),
                      project=info["project_id"])
    else:
        try:
            ee.Initialize(project=detail)
        except Exception as exc:                            # noqa: BLE001
            raise RuntimeError(
                "Earth Engine did not accept project %r with personal "
                "credentials: %s\n\nRun `earthengine authenticate` once, and "
                "check that the project has the Earth Engine API enabled and "
                "is registered for Earth Engine.\n\n%s"
                % (detail, exc, SETUP_HELP)) from exc
    return ee


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
