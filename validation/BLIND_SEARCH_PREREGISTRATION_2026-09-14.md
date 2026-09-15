# Blind-search pre-registration — does the tool find mine sources it was not told about?

**Written 2026-09-14. Committed BEFORE any landscape point is extracted.**
Commit ancestry is the proof: the commit adding this file must be an ancestor of
the first commit containing blind-search score data. If it is not, this
registration is void.

**Committed in the same commit, and fixed by it:**

| artifact | what it fixes |
|---|---|
| `python/blind_search_sites.py` | the deterministic sample definition |
| `validation/blind_search_sites_2026-09-14.csv` | the sample itself — **321 rows, SHA-256 `6ee8aec0a6a25c09d04d906bc0b451b9f480fd57721679a0805ce8d8d6a93eb5`** |
| `validation/report_blind_search_sites_2026-09-14.txt` | site counts and the exact power tables quoted below |

The site script reads station **metadata only** — locations and site types —
and no index value or imagery, so building the sample could not peek at the
outcome.

---

## 1. Why this test exists

Every validated result in this project scored a **known monitoring station**.
The gap between *scoring known points correctly* and *finding unknown sites* is
the difference between a severity tool and a discovery tool, and it has never
been measured (`validation/DECISION_LOG.md`; `docs/GRANT_CASE.md` §3). The field
campaign's discovery hypothesis (`docs/FIELD_CAMPAIGN.md`, H-DISC) needs to know
whether scene-wide flags are worth visiting before money is spent on it.

## 2. The question

**At a fixed flagged-area budget, what fraction of known mine-source sites fall
inside the highest-scoring part of their district's landscape — and is that more
than bare ground alone would flag?**

This measures **recall on known sources**. It cannot measure precision — whether
flagged ground without a record is a source — and it does not estimate recall on
unknown sources, because agencies monitor sources they already know about (§11).

---

## 3. The sample — fixed

**Source station:** `fetch_wqp.site_category(site_type) == "source"` —
mine discharge, adit, tailings pile, waste-rock pile, tunnel/shaft/mine, or
spring — with a latitude and longitude. This is B2's definition.

**Mine-type station:** a source station whose `site_type` is not `Spring`.

**Site:** single-linkage cluster of source stations within **250 m**.

**Primary site set:** sites containing **at least one mine-type station**.
Spring-only sites are a sensitivity set.

> **Why springs are not primary.** A natural spring is not a mine source. In
> H-BS2, **43 of 93 sites are spring-only** (68 of 162 stations are springs).
> Keeping them primary would have made nearly half of that test a measure of
> finding springs. This was decided from site-type metadata before any score
> existed. It costs power — H-BS2 at a threefold lift falls from 0.91 (all 93
> sites) to **0.64** (50 mine sites) — and that cost is accepted because a test
> of the wrong thing is worth less than a weaker test of the right one.

### Two co-primary hypotheses

| | districts | exclusions | primary sites | sensitivity sites |
|---|---|---|---|---|
| **H-BS1** | Alma, Creede, Lake City — never used for any index choice | any station inside an analysed district's box, or within 250 m of a B2 target | **32** | 33 |
| **H-BS2** | Silverton, Ouray, Leadville, Central City | the 86 B2 targets, and any station within 250 m of one | **50** | 93 |
| T-86 *(tertiary, in-sample)* | the four analysed districts | — | 37 | 41 |

Per district, primary sites: Alma 6 · Creede 5 · Lake City 21 · Silverton 23 ·
Ouray 6 · Leadville 12 · Central City 9.

**Independence of H-BS1, verified:** Creede, Alma and Lake City were **never
extracted in B2** — no `seep_*` file exists for them, despite a code comment
saying otherwise (`AUDIT_2026-09-14_ARMA_AND_TOOLING.md` §6). Their only prior
use was the retracted Arm A, which scored upstream mineral loadings, not
source-point buffers. Two Alma stations also appear in Leadville's station file
(the boxes overlap) and are counted once, under Leadville.

---

## 4. The score — fixed

Identical to B2's Sentinel-2 path (`python/seep_detect.py` `s2_composite`,
`index_image`, `extract_buffers`) as of the commit adding this file:

| step | value |
|---|---|
| collection | `COPERNICUS/S2_SR_HARMONIZED` |
| dates | 2013-01-01 – 2020-12-31 (Sentinel-2 SR effectively 2017 onward) |
| months | May – July |
| scene filter | `CLOUDY_PIXEL_PERCENTAGE` < 20, then the **120** least-cloudy scenes |
| pixel mask | SCL classes 1, 3, 8, 9, 10 removed (**snow, class 11, is not**) |
| bands | B1, B2, B3, B4, **B8A** → SR_B5, B11, B12; scaled 1/10000, clamped 0–1 |
| composite | median; indices computed per scene (`add_indices`) |
| water | removed with the classifier's own water test (`water_term`) |
| **index** | **`FerricIron1` = SR_B4 / SR_B2** |
| **statistic** | **p90** over a **60 m** circular buffer, `reduceRegions` at **20 m** |

**Disclosed:** index, statistic, buffer and sensor were all chosen by B2 on the
86 targets, which lie in H-BS2's districts. That is why H-BS1 exists.

**Site score** = the **maximum** of its stations' scores. A station with no
valid pixel is ignored within its site. **A site with no scoreable station is
counted as NOT flagged** — the tool cannot find what it cannot score.

---

## 5. Landscape sample and cutoff — fixed

- Per district, **2,000** points from
  `ee.FeatureCollection.randomPoints(region_geometry(district), 2000, seed=20260914)`,
  scored with the same statistic as §4.
- Points with no valid pixel are dropped and **counted**. Fewer than 1,000 valid
  points in a district is reported as a limitation; there is no re-draw.
- **Cutoff** = the district's empirical quantile of valid landscape scores at
  **1 − X**, using `numpy.quantile` with its default linear method.
- A site is **flagged** if its score ≥ its own district's cutoff.
- No label enters the cutoff, so there is no leakage.

**Budget X: 5% primary.** 1% and 10% are secondary.

---

## 6. Bare-ground baseline — fixed

A tool that simply flags unvegetated ground would find exposed mine workings too.
The comparison asks whether `FerricIron1` does better than that.

- **Baseline score = −(`NDVI_stress` mean)** over the same 60 m buffer and
  composite. `NDVI_stress` is standard NDVI (`water_indices.ndvi_stress_ee`), so
  its negative ranks barer ground higher. The mean is used because the p90 would
  select each buffer's greenest pixel.
- Its own landscape cutoff, from the same 2,000 points per district, same rule.

---

## 7. Tests and verdicts — fixed

For each hypothesis *h*, at the 5% budget: *k* = primary sites flagged by
`FerricIron1`, *n* = primary sites.

1. **Binomial:** one-sided exact p for recall > 0.05.
2. **Holm** over H-BS1 and H-BS2, family α = 0.05. The smaller p is tested at
   **0.025**; the other at **0.05**, and only if the first was rejected. If both
   p-values are equal, H-BS1 is tested first. Call hypothesis *h*'s level α_h.
3. **McNemar:** exact one-sided, on the same sites. *b* = sites flagged by
   `FerricIron1` only, *c* = sites flagged by the baseline only. p = P(X ≥ *b*)
   for X ~ Binomial(*b* + *c*, 0.5); p = 1 when *b* + *c* = 0. Evaluated at α_h.

### Verdict for each hypothesis — mutually exclusive, exhaustive rows

| binomial rejected under Holm? | McNemar p ≤ α_h? | verdict |
|---|---|---|
| yes | yes | **DISCOVERY SIGNAL** |
| yes | no | **NOT BETTER THAN BARE GROUND** |
| no | (not evaluated for the verdict) | **NO SIGNAL DETECTED** |

A NO SIGNAL verdict is reported with that hypothesis's raw p-value and its power
(§8).

---

## 8. Power — computed before any data

Exact one-sided binomial, 5% budget (`report_blind_search_sites_2026-09-14.txt`):

| hypothesis | n | reject if ≥ | at α = 0.025: r = 0.15 / 0.20 / 0.30 | at α = 0.05: r = 0.15 / 0.20 / 0.30 |
|---|---|---|---|---|
| **H-BS1** | 32 | 5 | **0.54 / 0.80 / 0.98** | 0.54 / 0.80 / 0.98 |
| **H-BS2** | 50 | 7 (α 0.025) · 6 (α 0.05) | **0.64 / 0.90 / 1.00** | 0.78 / 0.95 / 1.00 |

*r* is true recall; r = 0.15 is a threefold lift over the budget.

**Stated in advance:** a NO SIGNAL DETECTED verdict on H-BS1 **does not exclude**
a threefold lift. It rules out a large one.

---

## 9. Secondary and sensitivity analyses — reported, never verdicts

- Budgets 1% and 10%.
- Sensitivity site set (spring-only sites included).
- Site score as the **median** of its stations instead of the maximum.
- Unscoreable sites **excluded** instead of counted not-flagged.
- **Station-level** recall.
- **Snow-masked** composite (SCL class 11 added to the mask).
- Link distance **100 m** and **500 m**.
- Per-district recall with Wilson 95% intervals.
- Share of flagged landscape points in NLCD 2019 class 31 (barren).
- **T-86** recall — in-sample for index choice and labelled as such.

---

## 10. Field sampling frame — produced after the verdicts

For `docs/FIELD_CAMPAIGN.md` H-DISC, regardless of outcome:

1. Take landscape points at or above each district's 5% `FerricIron1` cutoff.
2. Drop any within **500 m** of any WQP station of any site type.
3. Cluster the rest at 250 m.
4. Draw **40 clusters**, seed **20260915**, allocated across districts in
   proportion to their cluster counts (largest remainder).

This is **a sampling frame, not a list of detections**. If the verdict is NO
SIGNAL DETECTED on both hypotheses, the report must say that visiting these
clusters is not supported by this test.

---

## 11. Disclosures, written before the data

- Index, statistic, buffer and sensor were chosen on the 86 B2 targets, in the
  H-BS2 districts.
- **Natural alteration:** Red Mountain Pass, a natural iron-oxide area, lies
  inside the Silverton and Ouray boxes. Natural acid rock drainage is chemically
  AMD-like, so a high score there is not an error of chemistry — but it is not a
  mine source either.
- **Known sources are a biased sample.** Agencies monitor what they already
  know; recall on them is not recall on unknown sources.
- **Precision cannot be measured from the archive.** "Unrecorded" means only "no
  WQP station nearby".
- The primary composite does **not** mask snow (§9 tests it).
- The WQP site-type vocabulary may misclassify some stations.
- If a district cannot be extracted after the safe memory levers (band subset,
  batch floor 1), it is reported **FAILED**, its sites are removed from that
  hypothesis, and the reduced n and its power are reported with the verdict.
  **The scene cap and composite are never changed for one district.**

---

## 12. What each outcome would mean

| outcome | meaning |
|---|---|
| DISCOVERY SIGNAL on H-BS1 | the index finds mine sources above bare ground in districts it was never tuned on — the first archival discovery evidence |
| DISCOVERY SIGNAL on H-BS2 only | it works where the index was chosen but has not been shown to transfer |
| NOT BETTER THAN BARE GROUND | it finds exposed ground; scene-wide flags would mostly be spoil and outcrop |
| NO SIGNAL DETECTED | recall is not above the budget at this power; field visits to flagged ground are not supported by this test |

Every outcome is reported as prominently as any other.

## 13. Reproduce

```
python python/blind_search_sites.py > validation/report_blind_search_sites_2026-09-14.txt
python python/blind_search.py --registration validation/BLIND_SEARCH_PREREGISTRATION_2026-09-14.md
```
