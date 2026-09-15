# Blind search — the tool does not find mine sources it was not told about, on this archive

**Date:** 2026-09-15 · **Pre-registration:**
[`BLIND_SEARCH_PREREGISTRATION_2026-09-14.md`](BLIND_SEARCH_PREREGISTRATION_2026-09-14.md),
committed in `ad05971` **before any landscape point was extracted**. That commit
is an ancestor of every commit containing blind-search code changes or results.
**Raw output:** [`report_blind_search_2026-09-15.txt`](report_blind_search_2026-09-15.txt) ·
**Field frame:** [`blind_search_field_frame_2026-09-15.csv`](blind_search_field_frame_2026-09-15.csv)

## Verdicts, as registered

| | sites | flagged at 5% budget | recall (95% CI) | binomial p | Holm level | FerricIron1-only / baseline-only | McNemar p | **verdict** |
|---|---|---|---|---|---|---|---|---|
| **H-BS1** — districts never used to choose the index | 32 | 4 | 0.125 (0.050–0.281) | 0.074 | 0.05 | 3 / 1 | 0.31 | **NO SIGNAL DETECTED** |
| **H-BS2** — unused stations in the districts that chose it | 50 | 14 | 0.280 (0.175–0.417) | 1.0 × 10⁻⁷ | 0.025 | 12 / 4 | 0.038 | **NOT BETTER THAN BARE GROUND** |

Holm, as registered: H-BS2 has the smaller p, so it was tested first at 0.025
and rejected. H-BS1 was then tested at 0.05 and not rejected. H-BS2's comparison
with bare ground was evaluated at its own level, 0.025. The McNemar p of 0.038
misses that level. Under the registered verdict table, that makes H-BS2 **NOT
BETTER THAN BARE GROUND**, whatever 0.038 would have meant at 0.05.

> **Both verdicts are reported with equal prominence.** Neither is a discovery
> signal. On this archive, a `FerricIron1` flag is **not** evidence of an
> unrecorded mine source.

### H-BS1 — the independence test

- **One site short.** The registered rejection point was 5 of 32 sites
  (p = 0.020 at 5); the test found 4 (p = 0.074). Recall is 2.5× the budget, but
  its interval runs from 1× to 5.6×.
- **Power:** 0.54 at a threefold lift, 0.80 at fourfold, 0.98 at sixfold. As
  stated in advance, **a NO SIGNAL verdict here does not exclude a threefold
  lift.** It rules out a large one.
- **Lake City dominates:** 21 of the 32 sites, and it flagged 1 (recall 0.048,
  equal to the budget). Alma flagged 2 of 6; Creede 1 of 5.

### H-BS2 — where the index was chosen

- Recall is **5.6× the budget** (14 of 50; p = 1.0 × 10⁻⁷). Per district:
  Central City 4 of 9, Leadville 2 of 12, Ouray 2 of 6, Silverton 6 of 23.
- **But the bare-ground baseline flags many of the same sites.** `FerricIron1`
  flagged 12 sites the baseline missed, and the baseline flagged 4 that
  `FerricIron1` missed. The direction favours `FerricIron1`; the registered test
  does not.
- Even a DISCOVERY SIGNAL here would not have shown transfer, because these
  districts chose the index (registration §12).

## Sensitivity and secondary analyses — reported, never verdicts

| analysis | H-BS1 flagged / n (p) | H-BS2 flagged / n (p) | H-BS2 FerricIron1-only / baseline-only, McNemar p |
|---|---|---|---|
| **primary (5%, 250 m, max, unscoreable = not flagged)** | **4 / 32 (0.074)** | **14 / 50 (<0.0001)** | **12 / 4, 0.038** |
| budget 1% | 1 / 32 (0.28) | 4 / 50 (0.0016) | 4 / 2, 0.34 |
| budget 10% | 5 / 32 (0.21) | 21 / 50 (<0.0001) | 19 / 6, 0.0073 |
| spring-only sites included | 4 / 33 (0.081) | 20 / 93 (<0.0001) | 17 / 4, 0.0036 |
| median site score | 2 / 32 (0.48) | 13 / 50 (<0.0001) | 11 / 4, 0.059 |
| unscoreable sites excluded | identical: no site was unscoreable | identical | identical |
| link distance 100 m | 4 / 41 (0.15) | 15 / 55 (<0.0001) | 13 / 4, 0.025 |
| link distance 500 m | 4 / 20 (0.016) | 13 / 42 (<0.0001) | 11 / 2, 0.011 |
| station level | 5 / 72 stations | 28 / 103 stations | — |
| snow-masked composite | **not run** — see Limitations | | |

How to read them:
- **Some variants would have cleared the H-BS2 bare-ground comparison at 0.025**
  (10% budget, spring sites included, 500 m linking). The median score and the
  1% budget do not. The verdict rests on the variant fixed in advance, and the
  table exists so that nobody can pick a winner afterwards.
- **H-BS1 at 500 m (p = 0.016)** comes from merging Lake City's many stations into
  fewer sites, which shrinks n from 32 to 20 while the four flagged sites stay.
  The registered unit is the 250 m site.

## Is the flagged ground just bare ground?

Share of flagged landscape points (5% budget) in NLCD 2019 class 31, Barren:

| district | flagged | whole landscape sample | enrichment |
|---|---|---|---|
| Alma | 0.160 | 0.115 | 1.4× |
| Central City | 0.040 | 0.009 | 4.4× |
| Creede | 0.060 | 0.051 | 1.2× |
| Lake City | 0.280 | 0.121 | 2.3× |
| Leadville | 0.080 | 0.052 | 1.5× |
| Ouray | 0.170 | 0.120 | 1.4× |
| Silverton | 0.380 | 0.221 | 1.7× |

**Flagged ground is enriched for barren land in every district.** This agrees
with the H-BS2 verdict and with finding B2 that bare ground confounds these
indices. NLCD shares NDVI-related physics with the scores, so this is
supporting evidence, not an independent test.

## Tertiary — T-86, in-sample, NOT evidence of discovery

The 86 B2 targets, the points the index was chosen on, form 37 sites: 9 flagged,
recall 0.243, p = 6.8 × 10⁻⁵, baseline 6. This is in-sample by construction and
is labelled as such.

## The landscape sample

2,000 random points per district (seed 20260914). Alma dropped 7 points with no
valid pixel (1,993 valid); every other district kept 2,000.

| district | scenes | stations | valid landscape points | FerricIron1 5% cutoff |
|---|---|---|---|---|
| Alma | 62 | 10 | 1,993 | 1.812 |
| Creede | 58 | 13 | 2,000 | 1.743 |
| Lake City | 120 | 50 | 2,000 | 1.811 |
| Central City | 61 | 37 | 2,000 | 1.719 |
| Leadville | 59 | 46 | 2,000 | 1.873 |
| Ouray | 120 | 73 | 2,000 | 1.787 |
| Silverton | 120 | 92 | 2,000 | 1.922 |

No district FAILED.

## The field sampling frame (registration §10)

40 clusters drawn with seed 20260915, allocated by largest remainder: Alma 7,
Creede 6, Lake City 6, Ouray 6, Central City 5, Leadville 5, Silverton 5. Of
these, 32 are single points and 8 are pairs. The frame's header states both
verdicts.

> **Visiting these clusters as candidate mine sources is NOT supported by this
> test.** H-BS1 found no signal, and H-BS2 found no advantage over bare ground.
> In the registration's words (§12), flags would then "mostly be spoil and
> outcrop". The frame remains a valid probability sample for `FIELD_CAMPAIGN.md`
> H-DISC — field chemistry there would measure precision, which this archive
> cannot — but it is **not a list of detections.**

## What it means

- **MAY NOT claim:** that the tool finds unrecorded mine sources in scene-wide
  search. It has now been tested, pre-registered, and the answer on this archive
  is no.
- **Still standing:** severity ranking at known sources within a district
  (`ARM_B2_SEEP_DETECTION_2026-08-14.md`, with its three-of-four-districts
  caveat, audit 2026-09-14 item 8).
- **Not excluded:** a modest lift in new districts (H-BS1 power 0.54 at
  threefold), and a real advantage over bare ground that this sample size could
  not resolve (H-BS2 direction 12 vs 4). Either needs a larger or field-based
  test, registered in advance, not a re-analysis of this one.

## Disclosures and limitations

- **Written before the data** (registration §11): the index, statistic, buffer
  and sensor were chosen on the 86 B2 targets, which lie in H-BS2's districts.
  Red Mountain Pass, natural iron-oxide alteration, lies inside the Silverton and
  Ouray boxes. Known sources are agency-monitored, so recall on them is not
  recall on unknown sources. Precision cannot be measured from the archive.
- **The snow-masked sensitivity was not run.** It needs a second extraction
  (roughly a day at this run's pace). The primary composite does not mask snow.
  This is a registered sensitivity left undone, not a verdict risk:
  `python python/blind_search.py --extract --snow-masked`, then re-run the analysis.
- **The extraction ran across two sessions.** The first process
  (2026-09-14 20:40) ended with its Claude session partway through Ouray. Ouray
  and Silverton were re-extracted from 2026-09-15 09:34 with behaviour-identical
  code (`tests/test_source_parity.py`); the five finished districts were not
  touched.
- **Earth Engine returned intermittent HTTP 502/503 errors, and this machine had
  two short DNS outages.** Every one recovered within the client's retries, and
  no district was re-run or FAILED. The rule that such errors mean re-extraction,
  not FAILED, was committed before any result (`724acc8`).
- **Analysis code completed before the analysis.** Two registered sensitivities
  (§9 link distance, §10 frame notice) were missing. They were implemented and
  tested on synthetic data and committed in `d5c30f3`, before the analysis ran.

## Reproduce

```
python python/blind_search_sites.py > validation/report_blind_search_sites_2026-09-14.txt
python python/blind_search.py --extract
python python/blind_search.py --analyse --registration validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md --out validation/report_blind_search_2026-09-15.txt
python python/blind_search.py --frame --registration validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md --out validation/blind_search_field_frame_2026-09-15.csv
```

The `data/matched/blindsearch_s2_*.csv` extractions are gitignored and are
regenerated by `--extract`. The analysis refuses to run unless the registration
is committed and the site list matches its registered SHA-256.
