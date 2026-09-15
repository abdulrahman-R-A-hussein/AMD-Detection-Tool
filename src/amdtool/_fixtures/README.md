# Test fixtures (package data)

Small, committed extracts so tests run offline - in this repository and in
host applications such as SpectraLab - without Earth Engine or `data/`.

| file | provenance |
|---|---|
| `cmd_huff_run_oh_30m.csv` | the 30 m rows of `data/matched/cmdgeo_l8_huff_run_oh.csv`: Landsat 8 leaf-off `NDVI_stress` and the full index panel at 49 Huff Run, Ohio stations, with WQP station-median chemistry. Produced by `python/cmd_detect.py --extract --season leafoff --radii 30,60,100 --regions huff_run_oh` (CMD1 amendment 2). |

These are **test inputs, not results**. A number computed from one fixture
watershed is not a finding and must not be reported as one.
