"""Exceptions. amdtool raises; it never calls sys.exit.

The scripts this library was extracted from called SystemExit and sys.exit from
functions an application would want to call, which would terminate a host
process such as a SpectraLab worker.
"""


class AmdToolError(Exception):
    """Base class for every amdtool error."""


class UnknownRegionError(AmdToolError, KeyError):
    """A region name or slug that is neither curated nor in the overlay."""

    def __str__(self):  # KeyError would otherwise quote the message
        return self.args[0] if self.args else ""


class CredentialsError(AmdToolError, RuntimeError):
    """No usable Earth Engine credentials were found (standalone use only)."""


class InsufficientDataError(AmdToolError, ValueError):
    """Too few usable rows for the requested analysis."""
