"""Earth Engine authentication - for standalone use only.

A host application (SpectraLab) initialises Earth Engine itself and passes the
`ee` module in; nothing else in amdtool authenticates. This module is for the
CLIs and notebooks.

Moved 2026-09-14 from python/ee_auth.py, which now wraps it and passes its own
legacy key path and env var, so the CLIs resolve credentials exactly as before.

Resolution order, first match wins:

  1. each variable in ``env_keys`` - a path to a service-account JSON key.
     Default: ``$GEE_SERVICE_ACCOUNT_KEY``, then SpectraLab's
     ``$GEE_SERVICE_ACCOUNT_JSON``, so one key serves both applications.
  2. ``legacy_key``, if given and that file exists.
  3. ``$GEE_PROJECT`` - a Google Cloud project id, using the personal
     credentials stored by ``earthengine authenticate``.
  4. Otherwise ``CredentialsError`` (a ``RuntimeError``) saying what to set up.

The key file's contents are never printed. ``ee`` is imported inside
``init_ee`` so importing this module needs no earthengine-api.
"""

import json
import os

from amdtool.errors import CredentialsError

ENV_KEY = "GEE_SERVICE_ACCOUNT_KEY"
SPECTRALAB_ENV_KEY = "GEE_SERVICE_ACCOUNT_JSON"
ENV_PROJECT = "GEE_PROJECT"
DEFAULT_ENV_KEYS = (ENV_KEY, SPECTRALAB_ENV_KEY)

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


def resolve_credentials(legacy_key=None, env_keys=DEFAULT_ENV_KEYS):
    """Decide how to authenticate, without contacting Earth Engine.

    Returns ``("service_account", key_path)`` or ``("user", project_id)``.
    Raises ``CredentialsError`` with setup instructions when nothing is configured.
    """
    for var in env_keys:
        key = os.environ.get(var)
        if key:
            if not os.path.isfile(key):
                raise CredentialsError(
                    "%s is set, but no file exists at %r.\n\n%s"
                    % (var, key, SETUP_HELP))
            return "service_account", key
    if legacy_key and os.path.isfile(legacy_key):
        return "service_account", legacy_key
    project = os.environ.get(ENV_PROJECT)
    if project:
        return "user", project
    raise CredentialsError("No Earth Engine credentials found.\n\n" + SETUP_HELP)


def init_ee(legacy_key=None, env_keys=DEFAULT_ENV_KEYS):
    """Initialise Earth Engine and return the ``ee`` module."""
    mode, detail = resolve_credentials(legacy_key, env_keys)
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
            raise CredentialsError(
                "Earth Engine did not accept project %r with personal "
                "credentials: %s\n\nRun `earthengine authenticate` once, and "
                "check that the project has the Earth Engine API enabled and "
                "is registered for Earth Engine.\n\n%s"
                % (detail, exc, SETUP_HELP)) from exc
    return ee
