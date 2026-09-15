"""Credential resolution: amdtool.auth, and python/ee_auth.py against itself as
committed before it became a wrapper. Never contacts Earth Engine."""
import pytest

from amdtool import auth
from amdtool.errors import AmdToolError, CredentialsError

VARS = ("GEE_SERVICE_ACCOUNT_KEY", "GEE_SERVICE_ACCOUNT_JSON", "GEE_PROJECT")


@pytest.fixture
def clean_env(monkeypatch):
    for v in VARS:
        monkeypatch.delenv(v, raising=False)
    return monkeypatch


@pytest.fixture
def key(tmp_path):
    p = tmp_path / "key.json"
    p.write_text("{}")          # never read by resolve_credentials
    return str(p)


def _outcome(fn):
    try:
        return ("ok",) + tuple(fn())
    except RuntimeError as exc:
        return ("error", str(exc))


def test_spectralab_variable_is_accepted_by_default(clean_env, key):
    clean_env.setenv("GEE_SERVICE_ACCOUNT_JSON", key)
    assert auth.resolve_credentials() == ("service_account", key)


def test_amdtool_variable_wins_over_spectralab(clean_env, key, tmp_path):
    other = tmp_path / "other.json"
    other.write_text("{}")
    clean_env.setenv("GEE_SERVICE_ACCOUNT_KEY", key)
    clean_env.setenv("GEE_SERVICE_ACCOUNT_JSON", str(other))
    assert auth.resolve_credentials() == ("service_account", key)


def test_nothing_configured_is_a_credentials_error_and_a_runtime_error(clean_env):
    with pytest.raises(CredentialsError) as ei:
        auth.resolve_credentials()
    assert isinstance(ei.value, RuntimeError) and isinstance(ei.value, AmdToolError)
    assert "GEE_PROJECT" in str(ei.value)


@pytest.mark.parametrize("case", ["env_key", "env_key_missing_file", "legacy_file",
                                  "project", "nothing", "spectralab_var_only"])
def test_ee_auth_wrapper_resolves_exactly_as_before(case, clean_env, key, tmp_path, legacy):
    import ee_auth
    old = legacy("ee_auth")
    absent = str(tmp_path / "absent.json")
    legacy_path = absent
    if case == "env_key":
        clean_env.setenv("GEE_SERVICE_ACCOUNT_KEY", key)
    elif case == "env_key_missing_file":
        clean_env.setenv("GEE_SERVICE_ACCOUNT_KEY", absent)
    elif case == "legacy_file":
        legacy_path = key
    elif case == "project":
        clean_env.setenv("GEE_PROJECT", "some-project")
    elif case == "spectralab_var_only":
        clean_env.setenv("GEE_SERVICE_ACCOUNT_JSON", key)   # the CLIs never read it
    clean_env.setattr(ee_auth, "LEGACY_KEY", legacy_path)
    clean_env.setattr(old, "LEGACY_KEY", legacy_path)
    assert _outcome(ee_auth.resolve_credentials) == _outcome(old.resolve_credentials)


def test_ee_auth_keeps_its_public_names(legacy):
    import ee_auth
    old = legacy("ee_auth")
    for name in ("LEGACY_KEY", "ENV_KEY", "ENV_PROJECT", "SETUP_HELP"):
        assert getattr(ee_auth, name) == getattr(old, name), name
