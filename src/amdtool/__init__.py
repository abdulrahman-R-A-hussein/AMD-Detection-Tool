"""amdtool - the importable library behind the AMD Detection Tool.

Acid and coal mine drainage analysis from satellite imagery and public water
chemistry. Built so another application (SpectraLab) can embed it:

  * no module prints, calls sys.exit, or mutates sys.path;
  * no Earth Engine function initialises Earth Engine - pass an initialised
    `ee`, so the host owns authentication;
  * no data path is derived from this file's location - pass `data_dir`.

What the numbers in this project do and do not license is in
`validation/STATE.md` and `validation/ACCURACY_ASSESSMENT.md` of the source
repository, and in `amdtool.claims`. Read those before citing any output.

The package version (0.1.0) versions this API. The science record is tagged
separately in the repository (v3.10.0 at the time of writing).
"""

__version__ = "0.1.0"
