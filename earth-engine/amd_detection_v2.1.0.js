/**
 * Acid Mine Drainage (AMD) and Coal Mine Drainage (CMD) Detection System
 * Advanced Remote Sensing for Environmental Monitoring
 * 
 * Version: 1.5.4
 * Author: Abdulrahman Hussein
 * Affiliation: Kent State University, Department of Earth Sciences
 * Lab: Environmental Remote Sensing Laboratory
 * Supervisor: Dr. Joseph D. Ortiz
 * Website: www.climtawy.com
 * ORCID: 0009-0003-0401-9219
 * Email: abdulrahman@climtawy.com
 * 
 * Based on: Rockwell et al. (2021) USGS Scientific Investigations Map 3466
 * License: MIT
 * 
 * Description:
 * Automated detection and mapping of iron sulfate minerals, acid mine drainage (AMD),
 * and coal mine drainage (CMD) contamination using Landsat 8/9 and Sentinel-2 satellite
 * imagery. Extends USGS terrestrial mineral detection methodology to contaminated water bodies quality assessment.
 * 
 * Citation:
 * Hussein, A. R. A. (2025). Acid Mine Drainage Detection System: Advanced Remote 
 * Sensing for Environmental Monitoring. GitHub. https://github.com/coodawy/AMD-Detection-Tool
 */

var TOOL_VERSION = 'v2.1.0';

// =============================================================================
// STUDY AREAS
// =============================================================================


var studyAreas = {

  'Ganau Pond, Iraq': ee.Geometry.Point([44.940463, 36.214839]).buffer(1000),
  'Iron Mountain, CA': ee.Geometry.Point([-122.5278, 40.6722]).buffer(12000),
  'Summitville, CO': ee.Geometry.Point([-106.5978, 37.4361]).buffer(8000),
  'Silverton, CO': ee.Geometry.Point([-107.665, 37.812]).buffer(15000),
  'Red Mountain Pass, CO': ee.Geometry.Point([-107.72, 37.89]).buffer(10000),
  'Goldfield, NV': ee.Geometry.Point([-117.233, 37.708]).buffer(10000),
  'Bauer Mill, UT': ee.Geometry.Point([-112.388, 40.492]).buffer(3000),
  'Marysvale, UT': ee.Geometry.Point([-112.233, 38.450]).buffer(10000),
  'Atwood Lake, OH': ee.Geometry.Point([-81.246189, 40.549551]).buffer(10000),
  'Piedmont Lake, OH': ee.Geometry.Point([-81.222, 40.154]).buffer(10000),
  'Clendening Lake, OH': ee.Geometry.Point([-81.25360, 40.27006]).buffer(10000),
  'Delaware, OH': ee.Geometry.Point([-83.168502, 40.264754]).buffer(50000),
  'Berkeley Pit, MT': ee.Geometry.Point([-112.5010, 46.0136]).buffer(5000),
  'Penn Mine, CA': ee.Geometry.Point([-120.82, 38.23]).buffer(5000),
  'Leadville, CO': ee.Geometry.Point([-106.30, 39.25]).buffer(15000),
  'Tab-Simco, IL': ee.Geometry.Point([-89.1, 37.7]).buffer(3000),
  'Dukan Lake, Iraq': ee.Geometry.Point([44.921183, 36.125888]).buffer(20000),
  'Monday Creek, OH': ee.Geometry.Point([-82.20948,39.48279]).buffer(15000),
  'Lake Superior, Oh': ee.Geometry.Point([-87.060472,47.548672]).buffer(5000),
  'Lake Toshka, Egypt': ee.Geometry.Point([31.27994, 23.09845]).buffer(100000),
  'Lake Naser, Egypt': ee.Geometry.Point([32.21471, 22.73580]).buffer(100000)
};

var areaNames = Object.keys(studyAreas);
var currentAreaName = areaNames[0];
var currentRegion = studyAreas[currentAreaName];

Map.centerObject(currentRegion, 13);

// Date range for image collection
// Multi-year composite matching paper methodology (2013-2020)
var START_DATE = '2013-01-01';
var END_DATE = '2020-12-31';

// =============================================================================
// CLOUD MASKING THRESHOLDS
// =============================================================================

var CLOUD_THRESHOLDS = {
  CLOUD_PROB: 20,        // Cloud probability threshold (5-60)
  CS_THRESHOLD: 0.60,    // Cloud Score+ cs threshold (0.40-0.80)
  CS_CDF_THRESHOLD: 0.60 // Cloud Score+ cs_cdf threshold (0.40-0.80)
};

// Seasonal filtering definitions
var SEASON_MONTHS = {
  'All Year': null,
  'Summer (Jul-Sep)': [7, 8, 9],      // Avoid snow in mountains
  'Winter (Dec-Feb)': [12, 1, 2],      // Snow/ice studies
  'Spring (Mar-May)': [3, 4, 5],       // Snowmelt season
  'Fall (Sep-Nov)': [9, 10, 11],       // Post-summer, pre-snow
  'Snow-Free (May-Oct)': [5, 6, 7, 8, 9, 10]  // Extended summer
};

// =============================================================================
// IMAGE PROCESSING FUNCTIONS
// =============================================================================

/**
 * Process Landsat Collection 2 Level-2 Surface Reflectance data
 * Applies cloud masking, scaling, and valid range clipping
 */
function processLandsat(image) {
  // Cloud masking using QA_PIXEL band
  var qa = image.select('QA_PIXEL');
  var cloudMask = qa.bitwiseAnd(1<<3).eq(0)  // Bit 3: Cloud
    .and(qa.bitwiseAnd(1<<4).eq(0))          // Bit 4: Cloud confidence
    .and(qa.bitwiseAnd(1<<2).eq(0));         // Bit 2: Cloud shadow
  
  var masked = image.updateMask(cloudMask);
  
  // Select optical bands (B1-B7)
  var bands = masked.select('SR_B[1-7]');
  
  // Apply Landsat Collection 2 scaling formula with clipping to valid range
  // Formula: Reflectance = (DN * 0.0000275) - 0.2
  var scaled = bands.multiply(0.0000275).add(-0.2);
  
  // CRITICAL: Clip to valid reflectance range [0.0, 1.0]
  var clipped = scaled.clamp(0.0, 1.0);
  
  // Rename bands to standard naming
  var renamed = clipped.rename(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']);
  
  return masked.addBands(renamed, null, true);
}

/**
 * Process Sentinel-2 L2A data with multiple cloud masking methods
 * REMOVED: QA60 masking, resampling to 30m
 * ADDED: Cloud Score+ integration, multiple masking methods
 * Native resolution: 10m for B2, B3, B4, B8
 */
function processSentinel2(image) {
  // Select the cloud masking method based on settings
  var cloudMask;
  
  switch(settings.cloudMaskingMethod) {
    case 'SCL+Prob':
      cloudMask = maskSCL_Prob(image);
      break;
    case 'CS':
      cloudMask = maskCS(image);
      break;
    case 'CS_CDF':
      cloudMask = maskCSCDF(image);
      break;
    case 'Hybrid':
      cloudMask = maskHybrid(image);
      break;
    case 'Hybrid Strict':
      cloudMask = maskHybridStrict(image);
      break;
    case 'Unmasked':
      cloudMask = ee.Image(1); // No masking
      break;
    default:
      cloudMask = maskHybrid(image); // Default to Hybrid
  }
  
  // NO RESAMPLING - Keep native 10m resolution for B2, B3, B4, B8
  // Scale and rename to match Landsat naming
  // Mapping: B1→B1, B2→B2, B3→B3, B4→B4, B8→B5, B11→B6, B12→B7
  var scaled = image.select(['B1', 'B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
    .multiply(0.0001)  // Sentinel-2 scale factor (0-10000 to 0-1)
    .clamp(0.0, 1.0)   // Ensure valid reflectance range
    .rename(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']);
  
  return image.addBands(scaled, null, true).updateMask(cloudMask);
}

// =============================================================================
// CLOUD MASKING METHODS FOR SENTINEL-2
// =============================================================================

/**
 * METHOD 1: SCL + Cloud Probability (NO QA60, NO AOT)
 * Uses Scene Classification Layer and cloud probability
 */
function maskSCL_Prob(image) {
  var scl = image.select('SCL');
  var sclClear = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
  var probClear = image.select('MSK_CLDPRB').lte(CLOUD_THRESHOLDS.CLOUD_PROB);
  return sclClear.and(probClear);
}

/**
 * METHOD 2: Cloud Score+ cs Only
 * Requires linking with GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED
 */
function maskCS(image) {
  var cs = image.select('cs');
  return cs.gte(CLOUD_THRESHOLDS.CS_THRESHOLD);
}

/**
 * METHOD 3: Cloud Score+ cs_cdf Only
 * Requires linking with GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED
 */
function maskCSCDF(image) {
  var csCdf = image.select('cs_cdf');
  return csCdf.gte(CLOUD_THRESHOLDS.CS_CDF_THRESHOLD);
}

/**
 * METHOD 4: HYBRID - Combines all effective methods
 * SCL + Prob + CS + CS_CDF (QA60 and AOT removed - they detect nothing)
 */
function maskHybrid(image) {
  // SCL clear mask (detects thick clouds + shadows)
  var scl = image.select('SCL');
  var sclClear = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
  
  // Cloud Prob clear mask (detects clouds)
  var probClear = image.select('MSK_CLDPRB').lte(CLOUD_THRESHOLDS.CLOUD_PROB);
  
  // CS clear mask (detects haze + thin clouds)
  var csClear = image.select('cs').gte(CLOUD_THRESHOLDS.CS_THRESHOLD);
  
  // CS_CDF clear mask (detects haze + thin clouds)
  var csCdfClear = image.select('cs_cdf').gte(CLOUD_THRESHOLDS.CS_CDF_THRESHOLD);
  
  // HYBRID: AND of all EFFECTIVE methods
  var allClear = sclClear.and(probClear).and(csClear).and(csCdfClear);
  
  return allClear;
}

/**
 * METHOD 5: HYBRID STRICT - Even more aggressive
 * Uses stricter thresholds for maximum cloud removal
 */
function maskHybridStrict(image) {
  var scl = image.select('SCL');
  var sclClear = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
  
  // Stricter cloud prob (lower threshold = more aggressive)
  var probClear = image.select('MSK_CLDPRB').lte(15);
  
  // Stricter CS (higher threshold = more aggressive)
  var csClear = image.select('cs').gte(0.65);
  var csCdfClear = image.select('cs_cdf').gte(0.65);
  
  var allClear = sclClear.and(probClear).and(csClear).and(csCdfClear);
  
  return allClear;
}

// =============================================================================
// SENSOR CONFIGURATION
// =============================================================================

var SENSOR_CONFIG = {
  'Landsat 8': {
    collection: 'LANDSAT/LC08/C02/T1_L2',
    processor: processLandsat,
    cloudProperty: 'CLOUD_COVER',
    dateRange: [START_DATE, END_DATE]
  },
  'Landsat 9': {
    collection: 'LANDSAT/LC09/C02/T1_L2',
    processor: processLandsat,
    cloudProperty: 'CLOUD_COVER',
    dateRange: [START_DATE, END_DATE]
  },
  'Sentinel-2': {
    collection: 'COPERNICUS/S2_SR_HARMONIZED',
    processor: processSentinel2,
    cloudProperty: 'CLOUDY_PIXEL_PERCENTAGE',
    dateRange: [START_DATE, END_DATE]
  }
};

// =============================================================================
// SPECTRAL INDICES CALCULATION
// =============================================================================

function calculateAllIndices(image) {
  // Select bands with safe division
  var b1 = image.select('SR_B1');  // Coastal/Aerosol 0.43-0.45 μm
  var b2 = image.select('SR_B2');  // Blue 0.45-0.51 μm
  var b3 = image.select('SR_B3');  // Green 0.53-0.59 μm
  var b4 = image.select('SR_B4');  // Red 0.64-0.67 μm
  var b5 = image.select('SR_B5');  // NIR 0.85-0.88 μm
  var b6 = image.select('SR_B6');  // SWIR1 1.57-1.65 μm
  var b7 = image.select('SR_B7');  // SWIR2 2.11-2.29 μm
  
  // Add epsilon to avoid division by zero
  var epsilon = 0.0001;
  var b1_safe = b1.add(epsilon);
  var b2_safe = b2.add(epsilon);
  var b4_safe = b4.add(epsilon);
  var b5_safe = b5.add(epsilon);
  var b7_safe = b7.add(epsilon);
  
  // 1. IRON SULFATE MINERAL INDEX (Rockwell et al. 2021, Table 4)
  // Formula: (2/1) - (5/4)  =>  (B2/B1) - (B5/B4)
  // v2.0 CORRECTION: v1.5.4 computed (B2+B4)/B1, which is NOT the paper's index
  // (nor the formula in docs/METHODOLOGY.md). The paper subtracts the 5/4 (NIR/Red)
  // ratio specifically to suppress green vegetation: vegetation has high 5/4 -> the
  // index goes strongly negative; iron sulfate (jarosite) has a steep positive 1->2
  // reflectance slope (high 2/1) with low-moderate 5/4 -> the index is positive.
  // Values are now signed (roughly -3..+2); negative = vegetation-like.
  var ironSulfate = b2.divide(b1_safe).subtract(b5.divide(b4_safe))
    .clamp(-5, 5)  // preserve sign; clip only extreme outliers from bad pixels
    .rename('IronSulfate');
  
  // 2. FERRIC IRON 1 "REDNESS INDEX"
  // Formula: B4/B2
  // Detects hematite and goethite
  var ferricIron1 = b4.divide(b2_safe).rename('FerricIron1');
  
  // 3. FERRIC IRON 2 (Crystal Field Electronic Transition)
  // Formula: (B4/B2) × (B4+B6)/(B5)
  // Enhanced ferric iron detection
  var ferricIron2 = b4.divide(b2_safe).multiply(b4.add(b6).divide(b5_safe))
    .rename('FerricIron2');
  
  // 4. FERROUS IRON
  // Formula: (B3+B6)/(B4+B5)
  // Detects chlorite and other ferrous minerals
  var ferrousIron = b3.add(b6).divide(b4.add(b5).add(epsilon))
    .rename('FerrousIron');
  
  // 5. CLAY-SULFATE-MICA INDEX
  // Formula: (B6/B7) - (B5/B4)
  // Detects clay, sulfate, and mica minerals
  var claySulfateMica = b6.divide(b7_safe).subtract(b5.divide(b4_safe))
    .rename('ClaySulfateMica');
  
  // 6. GREEN VEGETATION INDEX
  // Formula: B5/B4 (NDVI-like)
  // Detects vegetation
  var greenVeg = b5.divide(b4_safe).rename('GreenVeg');
  
  // 7. STANDARD INDICES
  var ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');
  var ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI');
  var mndwi = image.normalizedDifference(['SR_B3', 'SR_B6']).rename('MNDWI');
  var brightness = b2.add(b3).add(b4).divide(3).rename('Brightness');
  
  // 8. AWEInsh - Automated Water Extraction Index (Feyisa et al. 2014)
  // Formula: B2 + 2.5×B3 - 1.5×B5 - 0.25×B7
  // Detects water bodies
  var aweinsh = b2.add(b3.multiply(2.5))
    .subtract(b5.multiply(1.5))
    .subtract(b7.multiply(0.25))
    .rename('AWEINSH');
  
  // 9. Turbidity Index (for contaminated water detection)
  // Formula: B4/B2 (red/blue ratio)
  // Higher values = more suspended sediments
  var turbidity = b4.divide(b2_safe).rename('Turbidity');
  
  // ═════════════════════════════════════════════════════════════════════════
  // WATER CONTAMINATION INDICES (Advanced Spectral Analysis)
  // ═════════════════════════════════════════════════════════════════════════
  
  // 10. NIR Anomaly - Critical for AMD water detection
  // Clean water: NIR < 1% (strong H₂O absorption)
  // Contaminated water: NIR = 3-10% (particle scattering from jarosite/goethite)
  // Severe contamination: NIR > 10%
  var nirAnomaly = b5.rename('NIR_Anomaly');
  
  // 11. Iron in Water Index
  // Formula: (Red/Blue) - (NIR/Red)
  // Combines: Red increase (Fe³⁺ color) + NIR increase (particle scattering)
  // Clean water: -0.5 to 0.0, Contaminated: 0.15 to 0.8
  var ironWaterIndex = b4.divide(b2_safe)
    .subtract(b5.divide(b4_safe))
    .rename('IronWaterIndex');
  
  // 12. Yellow Substance Index
  // Formula: Green/Blue
  // Detects dissolved/colloidal iron (Fe³⁺) shifting peak toward yellow-green
  // Clean water: 0.9-1.05, Fe³⁺-rich: 1.15-1.4
  var yellowIndex = b3.divide(b2_safe).rename('YellowIndex');
  
  // 13. Water Depth Proxy
  // Formula: ln(Blue) / ln(Green)
  // Blue penetrates deeper than green; ratio decreases with depth
  // Deep water (>5m): ~1.0-1.1, Shallow (1-3m): 1.2-1.5, Very shallow (<1m): >1.5
  // NOTE: Must mask out land first (negative values cause NaN)
  var b2_log = b2.log().add(epsilon);
  var b3_log = b3.log().add(epsilon);
  var depthProxy = b2_log.divide(b3_log).rename('DepthProxy');
  
  // 14. Red Anomaly - Additional contamination indicator
  // Elevated red reflectance indicates Fe³⁺ coloration or suspended particles
  var redAnomaly = b4.rename('Red_Anomaly');
  
  // 15. Coastal/Blue Ratio - Detects iron sulfate absorption <450nm
  // Iron sulfate minerals absorb strongly in coastal band
  // Higher values = more absorption (more iron sulfate)
  var coastalBlueRatio = b1.divide(b2_safe).rename('CoastalBlueRatio');
  
  // 16. NDBI - Normalized Difference Built-up Index
  // Formula: (SWIR1 - NIR) / (SWIR1 + NIR)
  // High values indicate urban/built-up areas (concrete, asphalt, roofs)
  // Used to exclude false positives from bright artificial surfaces
  var ndbi = image.normalizedDifference(['SR_B6', 'SR_B5']).rename('NDBI');
  
  // Return image with all indices added
  return image.addBands([
    ironSulfate, ferricIron1, ferricIron2, ferrousIron,
    claySulfateMica, greenVeg, ndvi, ndwi, mndwi, brightness, aweinsh, turbidity,
    nirAnomaly, ironWaterIndex, yellowIndex, depthProxy, redAnomaly, coastalBlueRatio, ndbi
  ]);
}

// =============================================================================
// IMAGE COLLECTION LOADING
// =============================================================================

function loadImageCollection() {
  var sensorConfig = SENSOR_CONFIG[settings.currentSensor];
  
  var collection = ee.ImageCollection(sensorConfig.collection)
    .filterBounds(settings.currentRegion)  // Filter by region FIRST
    .filterDate(sensorConfig.dateRange[0], sensorConfig.dateRange[1])
    .filter(ee.Filter.lt(sensorConfig.cloudProperty, 30));  // Max 30% cloud cover
  
  // Apply seasonal filter if selected
  var seasonMonths = SEASON_MONTHS[settings.seasonFilter];
  if (seasonMonths !== null) {
    // v2.0 FIX (audit C7): build an explicit OR over the exact months instead of
    // calendarRange(first, last), which mishandles the winter wrap [12, 1, 2]
    // (that would have been read as calendarRange(12, 2)).
    var monthFilters = seasonMonths.map(function(m) {
      return ee.Filter.calendarRange(m, m, 'month');
    });
    collection = collection.filter(ee.Filter.or.apply(null, monthFilters));
  }
  
  // Link Cloud Score+ for Sentinel-2 if using CS-based methods
  if (settings.currentSensor === 'Sentinel-2' && 
      (settings.cloudMaskingMethod === 'CS' || 
       settings.cloudMaskingMethod === 'CS_CDF' || 
       settings.cloudMaskingMethod === 'Hybrid' || 
       settings.cloudMaskingMethod === 'Hybrid Strict')) {
    var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
    collection = collection.linkCollection(csPlus, ['cs', 'cs_cdf']);
    print('☁️ Cloud Score+ linked for ' + settings.cloudMaskingMethod + ' masking');
  }
  
  // CRITICAL: Print collection info BEFORE processing
  var count = collection.size();
  count.evaluate(function(num) {
    print('═══════════════════════════════════');
    print('📡 SENSOR: ' + settings.currentSensor);
    if (settings.currentSensor === 'Sentinel-2') {
      print('☁️ Cloud Masking: ' + settings.cloudMaskingMethod);
    }
    print('📊 Images found: ' + num);
    if (num === 0) {
      print('⚠️  WARNING: NO IMAGES FOUND!');
      print('   Try: Larger date range, higher cloud cover, or different area');
    }
    print('═══════════════════════════════════');
  });
  
  // Show first and last image dates
  collection.first().get('system:time_start').evaluate(function(first) {
    collection.sort('system:time_start', false).first()
      .get('system:time_start').evaluate(function(last) {
        print('📅 First image: ' + new Date(first).toISOString().split('T')[0]);
        print('📅 Last image:  ' + new Date(last).toISOString().split('T')[0]);
        var days = (last - first) / (1000 * 60 * 60 * 24);
        print('⏱️  Time span: ' + Math.round(days) + ' days');
      });
  });
  
  return collection.map(sensorConfig.processor).map(calculateAllIndices);
}

// =============================================================================
// SETTINGS & THRESHOLDS
// =============================================================================

var settings = {
  // Sensor selection
  currentSensor: 'Landsat 8',
  
  // Cloud masking method (Sentinel-2 only)
  cloudMaskingMethod: 'Hybrid',  // Options: 'SCL+Prob', 'CS', 'CS_CDF', 'Hybrid', 'Hybrid Strict', 'Unmasked'
  
  // NEW: Compositing method
  compositingMethod: 'median',  // Options: 'median', 'mean', 'mosaic', 'latest', 'quality'
  
  // NEW: Date filtering
  useSpecificDate: false,
  specificStartDate: '2024-01-01',
  specificEndDate: '2024-12-31',
  
  // Seasonal filtering
  seasonFilter: 'Summer (Jul-Sep)',  // Default to summer to avoid snow
  
  // Iron sulfate threshold for the corrected (2/1 - 5/4) index.
  // PROVISIONAL v2.0 value pending empirical ROC derivation (plan.md section 4)
  // and the paper's adaptive std-dev thresholding (Tier 2). The old 1.15 was tuned
  // for the incorrect (B2+B4)/B1 index and is NOT valid for this signed index.
  ironSulfateThreshold: 0.10,
  // "Strong iron" cutoff used by the road-bypass override.
  // v2.0.1: lowered 0.35 -> 0.15. Silverton field check (2026-07): known jarosite
  // talus at Red Mountain gives corrected index 0.19 with SWIR1 0.35-0.43, so a
  // 0.35 bypass never fired and the road mask deleted real AMD. 0.15 sits between
  // background p90 (-0.01) and the hotspot value (0.19).
  strongIronThreshold: 0.15,
  // v2.0.1: road mask OFF by default. Evidence: jarosite SWIR1 (0.35-0.43 measured)
  // is HIGHER than asphalt, so "SWIR1>=0.20 = road" cannot separate roads from ore;
  // it also contradicts the paper's dark mask (requires B6 > 0.2125), blocking ALL
  // mineral classes. The corrected 2/1-5/4 index is naturally ~0.0-0.06 on asphalt
  // (flat spectrum), so roads fall below the iron threshold without this mask.
  // Rockwell 2021 uses no road mask and accepts roads as a known limitation.
  useRoadMask: false,
  
  // Ferric iron thresholds
  ferricIron1Threshold: 1.4,
  ferricIron2Threshold: 2.5,
  
  // Ferrous iron threshold
  ferrousIronThreshold: 1.05,
  
  // Clay/mica/sulfate threshold (balanced for desert and humid regions)
  claySulfateMicaThreshold: 0.12,
  
  // Vegetation thresholds
  // v2.0.1: greenVegThreshold (B5/B4 > 1.5) marks ANY vegetation (sparse floor);
  // denseVegThreshold (> 3.0) marks dense canopy. Class 13 uses the sparse range
  // (1.5-3.0) + ferric; class 11 uses dense only. Prevents class 13 from
  // blanketing whole scenes now that hasIron is no longer true everywhere.
  greenVegThreshold: 1.5,
  denseVegThreshold: 3.0,
  ndviMax: 0.25,
  
  // NEW: Adaptive thresholding
  useStdDevThresholds: false,
  ironStdMult: 2.0,
  ferric1StdMult: 1.5,
  ferric2StdMult: 1.5,
  ferrousStdMult: 1.5,
  clayStdMult: 1.5,
  
  // NEW: Index clipping
  useIndexClipping: false,
  
  // Water masking
  useWaterMask: true,
  waterThreshold: 0.3,
  useAWEINSH: true,
  aweinshThreshold: 0.0,  // AWEINSH > 0.0 confirms water
  
  // Built-up area masking (to exclude urban false positives)
  useBuiltUpMask: true,
  builtUpBrightnessMin: 0.18,  // Very bright surfaces (buildings/pavement)
  builtUpNDVIMax: 0.15,        // Low vegetation
  builtUpNDVIMin: -0.1,        // Not too negative
  builtUpMNDWIMax: -0.2,       // Very dry (negative MNDWI)
  
  // Contaminated water detection
  useAdvancedWaterDetection: false,
  // PROVISIONAL v2.0: rescaled to the corrected iron index. Applying a
  // land-calibrated index over water is a known weakness (audit C1); Tier 3
  // replaces water iron detection with a physical Fe3+/AMWI index.
  contaminatedWaterThreshold: 0.10,
  turbidityThreshold: 1.3, // CHANGED: Now adjustable
  
  // ═══════════════════════════════════════════════════════════════════════
  // WATER CONTAMINATION MODULE - Advanced Spectral Analysis
  // ═══════════════════════════════════════════════════════════════════════
  
  // Water Quality Detection Settings
  enableWaterQualityModule: true,  // Toggle entire module on/off
  
  // NIR Anomaly Detection (Critical for AMD water)
  // Clean water: NIR < 1%, Contaminated: NIR = 3-10%, Severe: > 10%
  nirAnomalyThresholdModerate: 0.03,  // 3% - moderate contamination
  nirAnomalyThresholdSevere: 0.08,    // 8% - severe contamination
  
  // Turbidity Index (Red/Blue Ratio)
  // Clean: 0.6-1.0, Contaminated: 1.3-2.5, Severe: > 2.5
  turbidityRatioModerate: 1.3,
  turbidityRatioSevere: 2.0,
  
  // Iron in Water Index
  // Combines red increase (Fe³⁺ color) + NIR increase (particle scattering)
  ironWaterIndexModerate: 0.15,
  ironWaterIndexSevere: 0.50,
  
  // Yellow Substance Index (Green/Blue)
  // Clean: 0.9-1.05, Fe³⁺-rich: 1.15-1.4
  yellowIndexModerate: 1.10,
  yellowIndexSevere: 1.25,
  
  // Water Depth Proxy (ln(Blue)/ln(Green))
  // Deep water: ~1.0-1.1, Shallow: 1.2-1.5, Very shallow: >1.5
  shallowWaterThreshold: 1.3,  // Mask out shallow water < 2m
  
  // NDWI Degradation
  // Clean: > 0.3, Turbid: 0.0-0.3, Contaminated: < 0.0
  ndwiCleanThreshold: 0.2,  // Below this = degraded water quality
  
  // Contamination Score Weighting (0-9 scale; see createWaterQualityClassification)
  useMultiCriteriaScore: true,
  scoreThresholdModerate: 3,  // Score >= 3 = moderate contamination
  scoreThresholdSevere: 5,    // Score >= 5 = severe contamination
  
  // Brightness filtering
  brightnessMin: 0.02,
  brightnessMax: 0.35,  // Increased from 0.20 to allow snow-free high-reflectance rocks
  
  // Dark area masking (Paper: B6 DN < 15000 = 15000*0.0000275-0.2 = 0.2125)
  darkMaskThreshold: 0.2125,
  
  // NDWI comparison (optional, not default)
  useNDWIComparison: false,
  ndwiThreshold: 0.0,
  
  // Accuracy tools
  showAccuracyTools: false,
  
  // Current state
  currentComposite: null,
  currentRegion: currentRegion,
  currentAreaName: currentAreaName
};

// =============================================================================
// NEW: ADAPTIVE THRESHOLDING FUNCTIONS
// =============================================================================

function applyStdDevThresholding(indexImage, bandName, multiplier) {
  var stats = indexImage.reduceRegion({
    reducer: ee.Reducer.mean().combine(ee.Reducer.stdDev(), '', true),
    geometry: settings.currentRegion,
    scale: 100,
    maxPixels: 1e9,
    bestEffort: true
  });

  var mean = ee.Number(stats.get(bandName + '_mean'));
  var stdDev = ee.Number(stats.get(bandName + '_stdDev'));
  var threshold = mean.add(stdDev.multiply(multiplier));

  return indexImage.gt(threshold);
}

function applyIndexClipping(indexImage, bandName, percentileClip) {
  var stats = indexImage.reduceRegion({
    reducer: ee.Reducer.percentile([percentileClip]),
    geometry: settings.currentRegion,
    scale: 100,
    maxPixels: 1e9,
    bestEffort: true
  });
  
  var clipValue = ee.Number(stats.get(bandName + '_p' + percentileClip));
  return indexImage.where(indexImage.lt(clipValue), 0);
}

// =============================================================================
// WATER MASK CREATION
// =============================================================================

// =============================================================================
// UNIFIED WATER MASK - Shared between Land AMD and Water Quality modules
// =============================================================================

function createUnifiedWaterMask() {
  if (!settings.currentComposite) {
    return ee.Image(0);
  }
  
  var mndwi = settings.currentComposite.select('MNDWI');
  var aweinsh = settings.currentComposite.select('AWEINSH');
  var brightness = settings.currentComposite.select('Brightness');
  var ndvi = settings.currentComposite.select('NDVI');
  var ndwi = settings.currentComposite.select('NDWI');
  var nir = settings.currentComposite.select('SR_B5');
  
  // Multi-criteria water detection - prevents land from entering water classification
  // Each criterion removes a different type of false positive:
  // - brightness.lt(0.30): Excludes bright land surfaces
  // - ndvi.lt(0.2): Excludes vegetation
  // - ndwi.gt(-0.1): Additional water confirmation
  // - aweinsh.gt(0.20): CRITICAL - Excludes wet bare soil (raised from 0.0)
  //   Real water: AWEINSH > 0.20-0.25
  //   Wet soil: AWEINSH < 0.20 (lacks water column depth)
  //   Ganau Lake testing: Real water AWEINSH=0.249, Wet soil AWEINSH=0.18-0.19
  var isWater = mndwi.gt(settings.waterThreshold)     // mNDWI > 0.3 (main criterion)
    .and(aweinsh.gt(0.20))                            // CRITICAL FIX: AWEINSH > 0.20 (excludes wet soil)
    .and(brightness.lt(0.30))                         // Excludes bright land surfaces
    .and(ndvi.lt(0.2))                                // Excludes vegetation
    .and(ndwi.gt(-0.1));                              // Additional water confirmation
  
  return isWater;
}

function createContaminatedWaterMask() {
  if (!settings.currentComposite) {
    return {clean: ee.Image(0), contaminated: ee.Image(0), all: ee.Image(0)};
  }
  
  var iron = settings.currentComposite.select('IronSulfate');
  var turbidity = settings.currentComposite.select('Turbidity');
  var brightness = settings.currentComposite.select('Brightness');
  
  // Use UNIFIED water mask
  var isWater = createUnifiedWaterMask();
  
  // IMPROVED CONTAMINATED WATER DETECTION (from edited version)
  // Real contaminated water: high iron + moderate brightness (not too dark, not too bright)
  // False positive in deep water: high iron + very low brightness
  // False positive on land: high iron + very high brightness
  // FIXED: Contaminated water brightness range (from paper analysis)
  // - Minimum 0.05: Not too dark (avoids false positives from deep/dark water)
  // - Maximum 0.20: Not too bright (would be land-like, not water)
  // Previous: 0.02-0.35 was too permissive, allowing bright land pixels
  var isContaminatedWater = iron.gt(settings.contaminatedWaterThreshold)
    .and(isWater)
    .and(brightness.gt(0.05))   // Minimum for real water signal
    .and(brightness.lt(0.20));  // Maximum for water (not land)
  
  // Clean water
  var isCleanWater = isWater.and(isContaminatedWater.not());
  
  return {
    clean: isCleanWater,
    contaminated: isContaminatedWater,
    all: isWater
  };
}

// =============================================================================
// BUILT-UP AREA MASK - Excludes urban false positives
// =============================================================================

function createBuiltUpMask() {
  if (!settings.currentComposite || !settings.useBuiltUpMask) {
    return ee.Image(0);
  }
  
  var brightness = settings.currentComposite.select('Brightness');
  var ndvi = settings.currentComposite.select('NDVI');
  var mndwi = settings.currentComposite.select('MNDWI');
  
  // IMPROVED BUILT-UP DETECTION (from edited version)
  // Buildings: Very bright + Very low NDVI (-0.1 to 0.15)
  //
  // SENSOR-SPECIFIC ADJUSTMENT:
  // - Landsat 8 (30m): Uses 0.18 threshold - larger pixels mix building with surroundings
  // - Sentinel-2 (10m): Uses 0.15 threshold - smaller pixels isolate individual roof spectral signatures
  var isSentinel2 = settings.currentSensor === 'Sentinel-2';
  var brightnessThreshold = isSentinel2 ? 0.15 : settings.builtUpBrightnessMin;  // Lower for S2
  
  // MNDWI LOGIC:
  // - Dry land buildings: MNDWI < -0.20 (strongly negative = very dry)
  // - Water-edge buildings (marinas, docks): MNDWI between -0.1 and +0.1 (water mixing)
  // This catches metal roofs near water that can mimic iron sulfate spectra
  // Real AMD sites have MNDWI outside this range (either very dry or very wet)
  var isDryLandBuilding = mndwi.lt(settings.builtUpMNDWIMax);   // MNDWI < -0.20
  var isWaterEdgeBuilding = mndwi.gt(-0.10).and(mndwi.lt(0.10)); // MNDWI -0.1 to +0.1
  
  var isBuiltUp = brightness.gt(brightnessThreshold)            // Bright surfaces (sensor-adjusted)
    .and(ndvi.lt(settings.builtUpNDVIMax))                      // Low vegetation
    .and(ndvi.gt(settings.builtUpNDVIMin))                      // Not too negative
    .and(isDryLandBuilding.or(isWaterEdgeBuilding));            // Dry OR water-edge building
  
  return isBuiltUp;
}

// =============================================================================
// BOOLEAN CLASSIFICATION - 19 CLASSES
// =============================================================================

function createBooleanClassification() {
  if (!settings.currentComposite) return null;
  
  // Select indices
  var iron = settings.currentComposite.select('IronSulfate');
  var ferric1 = settings.currentComposite.select('FerricIron1');
  var ferric2 = settings.currentComposite.select('FerricIron2');
  var ferrous = settings.currentComposite.select('FerrousIron');
  var clay = settings.currentComposite.select('ClaySulfateMica');
  var greenVeg = settings.currentComposite.select('GreenVeg');
  var brightness = settings.currentComposite.select('Brightness');
  var ndvi = settings.currentComposite.select('NDVI');
  var b3 = settings.currentComposite.select('SR_B3');  // Green
  var b4 = settings.currentComposite.select('SR_B4');  // Red
  var b6 = settings.currentComposite.select('SR_B6');  // SWIR1
  
  // NEW: Apply index clipping if enabled
  if (settings.useIndexClipping) {
    iron = applyIndexClipping(iron, 'IronSulfate', 30);
    ferrous = applyIndexClipping(ferrous, 'FerrousIron', 25);
    ferric1 = applyIndexClipping(ferric1, 'FerricIron1', 10);
    ferric2 = applyIndexClipping(ferric2, 'FerricIron2', 10);
    clay = applyIndexClipping(clay, 'ClaySulfateMica', 20);
  }
  
  // NEW: Create binary masks with adaptive or fixed thresholds
  var hasIron, hasFerric1, hasFerric2, hasFerrous, hasClay;

  if (settings.useStdDevThresholds) {
    hasIron = applyStdDevThresholding(iron, 'IronSulfate', settings.ironStdMult);
    hasFerric1 = applyStdDevThresholding(ferric1, 'FerricIron1', settings.ferric1StdMult);
    hasFerric2 = applyStdDevThresholding(ferric2, 'FerricIron2', settings.ferric2StdMult);
    hasFerrous = applyStdDevThresholding(ferrous, 'FerrousIron', settings.ferrousStdMult);
    hasClay = applyStdDevThresholding(clay, 'ClaySulfateMica', settings.clayStdMult);
  } else {
    hasIron = iron.gt(settings.ironSulfateThreshold);
    hasFerric1 = ferric1.gt(settings.ferricIron1Threshold);
    hasFerric2 = ferric2.gt(settings.ferricIron2Threshold);
    hasFerrous = ferrous.gt(settings.ferrousIronThreshold);
    hasClay = clay.gt(settings.claySulfateMicaThreshold);
  }

  // v2.0.1 (Silverton regression): with the corrected index, hasIron is no longer
  // true almost everywhere, so hasIron.not() stopped suppressing the veg classes
  // and unconstrained "greenVeg > 1.5" let class 13 blanket entire scenes.
  // Split into disjoint sparse (1.5-3.0, needs ferric) and dense (>3.0) ranges,
  // and exclude water.
  var hasSparseVeg = greenVeg.gt(settings.greenVegThreshold)
    .and(greenVeg.lte(settings.denseVegThreshold));
  var hasDenseVeg = greenVeg.gt(settings.denseVegThreshold);

  // Water detection
  var waterMasks = createContaminatedWaterMask();
  
  // Quality masks
  var notBright = brightness.lt(settings.brightnessMax);
  var notDark = b6.gt(settings.darkMaskThreshold).and(brightness.gt(0.05));  // Updated to 0.05 from edited version
  
  // UNIFIED APPROACH: Land AMD NEVER classifies water pixels
  // Water contamination is handled by separate Water Quality module
  // This guarantees zero pixel overlap/contradiction between modules
  var unifiedWater = createUnifiedWaterMask();
  
  // NEW: Built-up area mask to exclude urban false positives
  var builtUpMask = createBuiltUpMask();
  
  // NEW: Vegetation and road masks (same logic as Iron Sulfate layer)
  // This ensures ALL classifications exclude vegetation and roads, not just the Iron Sulfate layer
  var greenRedRatio = b3.divide(b4);
  var noGreenPeak = greenRedRatio.lte(1.0);           // Red ≥ Green (no chlorophyll green peak)
  var lowSWIR1 = b6.lt(0.20);                         // SWIR1 < 0.20 (not road/impervious surface)
  var notDenseVeg = greenVeg.lt(3.5);                 // Not extremely high vegetation index
  var strongIronSignal = iron.gt(settings.strongIronThreshold);  // Strong iron = likely real minerals (v2.0: rescaled)
  
  // Road detection: low NDVI + high SWIR1 + weak iron signal
  // BYPASS road detection if Iron Sulfate > strongIronThreshold (strong detection = real minerals)
  // CRITICAL: Iron oxide minerals (jarosite, goethite) naturally have HIGH SWIR1
  // v2.0.1: road mask now optional (default OFF) - see useRoadMask comment in settings.
  var isRoad = settings.useRoadMask
    ? ndvi.lt(0.25).and(b6.gte(0.20)).and(strongIronSignal.not())
    : ee.Image(0);
  var hasHighIron = iron.gt(settings.ironSulfateThreshold);
  
  // Vegetation/road exclusion mask for ALL classifications
  // A pixel passes if:
  //   1. Green/Red ≤ 1.0 (no vegetation green peak)
  //   2. NOT a road (unless strong iron signal bypasses road check)
  //   3. Either NDVI < 0.25 OR (hasHighIron AND lowSWIR1 AND notDenseVeg)
  var passesVegRoadMask = noGreenPeak
    .and(isRoad.not())
    .and(
      ndvi.lt(settings.ndviMax)
      .or(hasHighIron.and(lowSWIR1).and(notDenseVeg))
    );
  
  // Land mask: exclude water + extreme brightness + dark pixels + built-up areas + vegetation + roads
  // ADDED: notDark mask from paper (prevents division artifacts in dark pixels)
  var amdLandMask = unifiedWater.not()
    .and(notBright)
    .and(notDark)
    .and(builtUpMask.not())
    .and(passesVegRoadMask);
  
  // Standard land mask (for non-AMD minerals) also excludes water, built-up areas, vegetation, roads
  var standardLandMask = amdLandMask;
  
  // BOOLEAN CLASSIFICATION - FIRST-MATCH-WINS (per Rockwell Table 4: "the pixel
  // being assigned to the first class for which all conditions are met").
  // v2.0 FIX (audit A2/A3): v1.5.4 chained .where() which is LAST-match-wins, and
  // an unconditional class-12 fallback overwrote everything -> classes 9,14,17,18,19
  // were unreachable, and classes 2/3/4 (missing hasIron.not) relabeled real AMD.
  // The eq(0) guard below makes assignment genuinely first-match-wins: once a pixel
  // is labeled (nonzero) it is never overwritten. Priority is iron-sulfate (AMD)
  // classes first, matching this tool's AMD focus.
  var classification = ee.Image(0);
  function assignClass(condition, value) {
    // Only assign pixels not yet classified (first-match-wins)
    classification = classification.where(condition.and(classification.eq(0)), value);
  }

  // STEP 1: Iron sulfate classes (most restrictive first)
  // Class 9: Argillic Alteration - Iron + Fe1 + Fe2 + Clay + not too bright
  assignClass(hasIron.and(hasFerric1).and(hasFerric2).and(hasClay).and(amdLandMask).and(notBright), 9);
  // Class 17: Proximal Jarosite - Iron + Fe1 + Fe2 + Clay
  assignClass(hasIron.and(hasFerric1).and(hasFerric2).and(hasClay).and(amdLandMask), 17);
  // Class 12: Major Iron Sulfate - Iron + Fe1 + Clay (NO Fe2)
  assignClass(hasIron.and(hasFerric1).and(hasFerric2.not()).and(hasClay).and(amdLandMask), 12);
  // Class 18: Distal Jarosite - Iron + Fe2 + Clay (NO Fe1)
  assignClass(hasIron.and(hasFerric1.not()).and(hasFerric2).and(hasClay).and(amdLandMask), 18);
  // Class 19: Clay + Ferrous + Iron
  assignClass(hasIron.and(hasFerrous).and(hasClay).and(amdLandMask), 19);
  // Class 14: Oxidizing Sulfides - Iron + Clay ONLY (NO Fe1, NO Fe2)
  assignClass(hasIron.and(hasClay).and(hasFerric1.not()).and(hasFerric2.not()).and(amdLandMask), 14);
  // FALLBACK Class 12: any remaining Iron even without clay. Kept LAST in priority
  // so it no longer overwrites the specific jarosite classes above.
  assignClass(hasIron.and(amdLandMask), 12);

  // STEP 2: Non-iron sulfate classes. hasIron.not() kept for explicit intent; the
  // eq(0) guard already prevents overwriting the STEP 1 iron classes.
  // Class 8: Clay + Major Ferric (Clay + Fe1 + Fe2, no Iron)
  assignClass(hasClay.and(hasFerric1).and(hasFerric2).and(hasIron.not()).and(standardLandMask), 8);
  // Class 7: Clay + Moderate Ferric (Clay + (Fe1 OR Fe2), no Iron)
  assignClass(hasClay.and(hasFerric1.or(hasFerric2)).and(hasIron.not()).and(standardLandMask), 7);
  // Class 6: Clay + Minor Ferric (Clay + Fe1, no Fe2, no Iron)
  assignClass(hasClay.and(hasFerric1).and(hasFerric2.not()).and(hasIron.not()).and(standardLandMask), 6);
  // Class 5: Clay-Sulfate-Mica (Clay only, no Fe1, no Iron)
  assignClass(hasClay.and(hasFerric1.not()).and(hasIron.not()).and(standardLandMask), 5);
  // Class 10: Clay + Ferrous (Clay + Ferrous, no Iron)
  assignClass(hasClay.and(hasFerrous).and(hasIron.not()).and(standardLandMask), 10);
  // Class 2: Major Ferric Iron (Fe1 + Fe2, no Clay, no Iron)  [v2.0: added hasIron.not()]
  assignClass(hasFerric1.and(hasFerric2).and(hasClay.not()).and(hasIron.not()).and(standardLandMask), 2);
  // Class 3: Ferric +/- Ferrous (Fe1 + Ferrous, no Clay, no Iron)  [v2.0: added hasIron.not()]
  assignClass(hasFerric1.and(hasFerrous).and(hasClay.not()).and(hasIron.not()).and(standardLandMask), 3);
  // Class 1: Minor Ferric (Hematite) - Fe1 only, no Fe2, no Clay, no Iron
  assignClass(hasFerric1.and(hasFerric2.not()).and(hasClay.not()).and(hasIron.not()).and(standardLandMask), 1);
  // Class 4: Ferrous/Chlorite (Ferrous only, no Fe1, no Clay, no Iron)  [v2.0: added hasIron.not()]
  assignClass(hasFerrous.and(hasClay.not()).and(hasFerric1.not()).and(hasIron.not()).and(standardLandMask), 4);
  // Class 13: Sparse Veg + Ferric - sparse range (1.5-3.0) + ferric, no iron, not water
  assignClass(hasSparseVeg.and(hasFerric1).and(hasIron.not()).and(unifiedWater.not()), 13);
  // Class 11: Dense Green Vegetation - dense canopy (>3.0) dominates the spectrum,
  // so no ferric exclusion needed (B4/B2 on canopy can exceed 1.4 spuriously)
  assignClass(hasDenseVeg.and(hasIron.not()).and(unifiedWater.not()), 11);

  // REMOVED: Old water classes (20, 21) - now handled by separate Water Quality module
  // Land AMD Classification no longer classifies water pixels at all
  // Water is handled exclusively by createWaterQualityClassification()

  return classification.selfMask().clip(settings.currentRegion);
}

// =============================================================================
// UPDATE COMPOSITE AND CLASSIFICATION
// =============================================================================

// NEW: Compositing method selector
function createComposite(collection) {
  print('🔧 Compositing method: ' + settings.compositingMethod);
  
  switch(settings.compositingMethod) {
    case 'median':
      return collection.median();
    case 'mean':
      return collection.mean();
    case 'mosaic':
      return collection.mosaic();  // First image on top
    case 'latest':
      return collection.sort('system:time_start', false).mosaic();  // Most recent on top
    case 'quality':
      return collection.qualityMosaic('SR_B5');  // Highest NIR (best vegetation/quality)
    default:
      return collection.median();
  }
}

function updateComposite() {
  var collection = loadImageCollection();
  
  // Filter to specific date if enabled
  if (settings.useSpecificDate) {
    print('📅 Using date range: ' + settings.specificStartDate + ' to ' + settings.specificEndDate);
    collection = collection.filterDate(settings.specificStartDate, settings.specificEndDate);
    
    // Check if any images remain
    collection.size().evaluate(function(num) {
      if (num === 0) {
        print('⚠️  WARNING: No images in specified date range!');
      } else {
        print('✅ ' + num + ' images in date range');
      }
    });
  }
  
  var composite = createComposite(collection).clip(settings.currentRegion);
  settings.currentComposite = composite;
  return composite;
}

// =============================================================================
// WATER QUALITY CLASSIFICATION FUNCTION
// =============================================================================

function createWaterQualityClassification() {
  if (!settings.currentComposite) return null;
  
  // ───────────────────────────────────────────────────────────────────────
  // STEP 1: Water Body Extraction (USE UNIFIED MASK + EXCLUDE LAND AMD)
  // ───────────────────────────────────────────────────────────────────────
  
  // Use the SAME water mask as Land AMD module to prevent pixel conflicts
  var waterMask = createUnifiedWaterMask();
  
  // Explicitly exclude any land AMD pixels from water analysis
  // This prevents overlap between Land AMD and Water Quality classifications
  // CRITICAL: unmask(0) required because createBooleanClassification() uses .selfMask()
  // which masks all 0-value pixels (including water). Without unmask, isLandAMD.not()
  // returns MASKED for water pixels, propagating the mask and blanking out water quality.
  var landClassification = createBooleanClassification().unmask(0);
  var isLandAMD = landClassification.gte(1).and(landClassification.lte(19));
  var waterOnlyMask = waterMask.and(isLandAMD.not());
  
  // ───────────────────────────────────────────────────────────────────────
  // STEP 2: Depth Filtering (Remove Shallow Water)
  // ───────────────────────────────────────────────────────────────────────
  
  var depthProxy = settings.currentComposite.select('DepthProxy');
  var ndwi = settings.currentComposite.select('NDWI');
  
  // Keep only deep water (depth proxy < threshold means deeper)
  // This removes bottom-reflectance contamination
  var deepWaterMask = waterOnlyMask.and(depthProxy.lt(settings.shallowWaterThreshold));
  
  // ───────────────────────────────────────────────────────────────────────
  // STEP 3: Calculate Contamination Indices
  // ───────────────────────────────────────────────────────────────────────
  
  var nirAnomaly = settings.currentComposite.select('NIR_Anomaly');
  var turbidityRatio = settings.currentComposite.select('Turbidity');
  var ironWaterIndex = settings.currentComposite.select('IronWaterIndex');
  var yellowIndex = settings.currentComposite.select('YellowIndex');
  var redAnomaly = settings.currentComposite.select('Red_Anomaly');
  var ironSulfateIndex = settings.currentComposite.select('IronSulfate');
  var brightness = settings.currentComposite.select('Brightness');
  
  // ───────────────────────────────────────────────────────────────────────
  // STEP 4: Multi-Criteria Contamination Score (0-9 points; max = 2+2+2+1+1+1)
  // v2.0 FIX (audit C5): true maximum is 9, not the 0-7/0-8 stated in v1.5.4.
  // ───────────────────────────────────────────────────────────────────────
  
  var score = ee.Image(0);

  // v2.0 FIX (audit B): the brightness/validity guard is now applied to EVERY
  // criterion, not just criterion 1. Over dark clean water the ratio-based indices
  // (turbidity B4/B2, yellow B3/B2) are numerically unstable and were scoring false
  // "contamination" (the Atwood failure mode, one criterion over); validBrightness
  // gates them all.
  var validBrightness = brightness.gt(0.05).and(brightness.lt(0.20));

  // Criterion 1: Iron Sulfate Index (PRIMARY)
  score = score.where(ironSulfateIndex.gt(settings.contaminatedWaterThreshold).and(validBrightness), score.add(2));

  // Criterion 2: NIR Anomaly (most diagnostic for dissolved iron)
  score = score.where(nirAnomaly.gt(settings.nirAnomalyThresholdModerate).and(validBrightness), score.add(1));
  score = score.where(nirAnomaly.gt(settings.nirAnomalyThresholdSevere).and(validBrightness), score.add(1));

  // Criterion 3: Turbidity (suspended particles)
  score = score.where(turbidityRatio.gt(settings.turbidityRatioModerate).and(validBrightness), score.add(1));
  score = score.where(turbidityRatio.gt(settings.turbidityRatioSevere).and(validBrightness), score.add(1));

  // Criterion 4: Iron in Water Index
  score = score.where(ironWaterIndex.gt(settings.ironWaterIndexModerate).and(validBrightness), score.add(1));

  // Criterion 5: Yellow Substance (dissolved Fe³⁺)
  score = score.where(yellowIndex.gt(settings.yellowIndexModerate).and(validBrightness), score.add(1));

  // Criterion 6: NDWI Degradation
  score = score.where(ndwi.lt(settings.ndwiCleanThreshold).and(validBrightness), score.add(1));
  
  // Apply water mask to score
  var contaminationScore = score.updateMask(deepWaterMask).rename('ContaminationScore');
  
  // ───────────────────────────────────────────────────────────────────────
  // STEP 5: Three-Class Water Quality Classification
  // ───────────────────────────────────────────────────────────────────────
  
  var classification = ee.Image(0)  // 0 = Clean water
    .where(contaminationScore.gte(settings.scoreThresholdModerate), 1)  // 1 = Moderate contamination
    .where(contaminationScore.gte(settings.scoreThresholdSevere), 2)   // 2 = Severe contamination
    .updateMask(deepWaterMask)
    .rename('WaterQuality');
  
  // ───────────────────────────────────────────────────────────────────────
  // STEP 6: Return Results
  // ───────────────────────────────────────────────────────────────────────
  
  return {
    classification: classification,
    contaminationScore: contaminationScore,
    waterMask: deepWaterMask,
    nirAnomaly: nirAnomaly,
    turbidityRatio: turbidityRatio,
    ironWaterIndex: ironWaterIndex,
    yellowIndex: yellowIndex,
    depthProxy: depthProxy
  };
}

// =============================================================================
// MAIN DETECTION UPDATE FUNCTION
// =============================================================================

function updateDetection() {
  var classification = createBooleanClassification();
  if (!classification) return;
  
  // Classification visualization (LAND ONLY - water handled separately)
  var classVis = {
    min: 1,
    max: 19,  // Only 19 land classes now
    palette: [
      '8B7355', // 1: Minor Ferric (light brown)
      'FF00FF', // 2: Major Ferric Iron (magenta)
      '800080', // 3: Ferric±Ferrous (purple)
      '00CED1', // 4: Ferrous (dark cyan)
      '90EE90', // 5: Clay-Sulfate-Mica (light green)
      'FFFF00', // 6: Clay+Minor Ferric (yellow)
      'FFA500', // 7: Clay+Mod Ferric (orange)
      'FF6347', // 8: Clay+Major Ferric (tomato)
      'FF1493', // 9: Argillic Alteration (deep pink)
      '008B8B', // 10: Clay+Ferrous (dark cyan)
      '228B22', // 11: Dense Vegetation (forest green)
      'FF0000', // 12: Major Iron Sulfate (red)
      '9ACD32', // 13: Sparse Veg+Ferric (yellow-green)
      'FFB6C1', // 14: Oxidizing Sulfides (light pink)
      '000000', // 15: Not used
      '000000', // 16: Not used
      'DC143C', // 17: Proximal Jarosite (crimson)
      '8B0000', // 18: Distal Jarosite (dark red)
      'C71585'  // 19: Clay+Ferrous+Iron (medium violet red)
      // Classes 20, 21 REMOVED - water now handled by Water Quality module
    ]
  };
  
  // ═══════════════════════════════════════════════════════════════════════
  // LAYER VISUALIZATION - ORGANIZED STRUCTURE
  // ═══════════════════════════════════════════════════════════════════════
  
  Map.layers().reset();
  
  // ───────────────────────────────────────────────────────────────────────
  // PRIMARY LAYERS (Always visible by default)
  // ───────────────────────────────────────────────────────────────────────
  
  // 1. LAND AMD CLASSIFICATION (19 classes)
  Map.addLayer(classification, classVis, '🏔️ Land AMD Classification', true);
  
  // 2. WATER QUALITY CLASSIFICATION (3 classes) - Separate from land
  if (settings.enableWaterQualityModule) {
    var waterQualityResult = createWaterQualityClassification();
    
    Map.addLayer(waterQualityResult.classification, {
      min: 0,
      max: 2,
      palette: ['1E90FF', 'FFA500', 'FF0000']  // Blue (clean), Orange (moderate), Red (severe)
    }, '🌊 Water Quality Classification', true);  // VISIBLE by default
    
    // ─────────────────────────────────────────────────────────────────────
    // WATER DIAGNOSTIC LAYERS (For validation - hidden by default)
    // ─────────────────────────────────────────────────────────────────────
    
    Map.addLayer(waterQualityResult.contaminationScore.updateMask(waterQualityResult.waterMask),
      {min: 0, max: 9, palette: ['0000FF', '00FFFF', '00FF00', 'FFFF00', 'FFA500', 'FF4500', 'FF0000', '8B0000']},
      '📊 Water Score (0-9)', false);
    
    Map.addLayer(waterQualityResult.nirAnomaly.updateMask(waterQualityResult.waterMask), 
      {min: 0, max: 0.15, palette: ['000080', '0000FF', '00FFFF', 'FFFF00', 'FF0000']}, 
      '🔬 NIR Anomaly (Water)', false);
    
    Map.addLayer(waterQualityResult.turbidityRatio.updateMask(waterQualityResult.waterMask), 
      {min: 0.5, max: 3.0, palette: ['0000FF', '00FF00', 'FFFF00', 'FF0000']}, 
      '🔬 Turbidity Ratio', false);
  }
  
  // ───────────────────────────────────────────────────────────────────────
  // REFERENCE LAYERS (RGB composites - hidden by default)
  // ───────────────────────────────────────────────────────────────────────
  
  Map.addLayer(settings.currentComposite, {bands: ['SR_B4', 'SR_B3', 'SR_B2'], min: 0, max: 0.3}, 
    '📷 True Color (RGB)', false);
  
  Map.addLayer(settings.currentComposite, {bands: ['SR_B5', 'SR_B4', 'SR_B3'], min: 0, max: 0.3}, 
    '📷 False Color (NIR-R-G)', false);
  
  // ───────────────────────────────────────────────────────────────────────
  // DIAGNOSTIC LAYERS (For validation - hidden by default)
  // ───────────────────────────────────────────────────────────────────────
  
  // Iron Sulfate Index (for land AMD)
  var ironIndex = settings.currentComposite.select('IronSulfate');
  var ndvi = settings.currentComposite.select('NDVI');
  var brightness = settings.currentComposite.select('Brightness');
  var b3 = settings.currentComposite.select('SR_B3');  // Green
  var b4 = settings.currentComposite.select('SR_B4');  // Red
  var builtUpMask = createBuiltUpMask();
  
  // Apply masks: exclude vegetation, dark pixels, water, and built-up areas
  // NDVI mask is essential to detect EXPOSED land iron sulfates (not under vegetation)
  // 
  // PROBLEM: Iron-rich soils can have high NIR reflectance causing false NDVI readings
  // SOLUTION: Multi-criteria vegetation exclusion using spectral signatures
  //
  // Key spectral differences between vegetation and exposed iron soil:
  //   1. Green/Red ratio: Vegetation has Green > Red (chlorophyll), Iron has Red ≥ Green
  //   2. SWIR1 (B6): Vegetation has HIGH SWIR1 (>0.15), Iron soil has LOW SWIR1 (<0.15)
  //   3. GreenVeg index: Very high (>3.5) indicates dense vegetation
  //
  // A pixel looks like iron soil (not vegetation) if ALL of:
  //   - Green/Red ≤ 1.0 (no green peak = not vegetation)
  //   - SWIR1 < 0.15 (low SWIR1 = not vegetation leaf structure)
  //   - GreenVeg < 3.5 (not extremely high vegetation index)
  var unifiedWater = createUnifiedWaterMask();
  var greenRedRatio = b3.divide(b4);
  var b6 = settings.currentComposite.select('SR_B6');  // SWIR1
  var greenVeg = settings.currentComposite.select('GreenVeg');
  var hasHighIron = ironIndex.gt(settings.ironSulfateThreshold);
  
  // Multi-criteria iron soil detection (stricter vegetation AND road exclusion)
  // 
  // KEY INSIGHTS:
  //   1. Green/Red > 1.0 = vegetation (chlorophyll green peak)
  //   2. High SWIR1 (>0.20) + low NDVI + weak iron = roads/buildings (asphalt)
  //   3. High SWIR1 + STRONG iron (>2.5) = REAL iron minerals (iron oxides have high SWIR1!)
  //
  // CRITICAL: Iron oxide minerals (jarosite, goethite) naturally have HIGH SWIR1
  // So we must NOT exclude high SWIR1 when Iron Sulfate Index is strong (>2.5)
  var noGreenPeak = greenRedRatio.lte(1.0);           // Red ≥ Green (no chlorophyll green peak)
  var lowSWIR1 = b6.lt(0.20);                         // SWIR1 < 0.20 (not road/impervious surface)
  var notDenseVeg = greenVeg.lt(3.5);                 // Not extremely high vegetation index
  var strongIronSignal = ironIndex.gt(settings.strongIronThreshold);  // Strong iron = likely real minerals (v2.0: rescaled)
  
  // Road detection: low NDVI + high SWIR1 + weak iron signal
  // BYPASS road detection if Iron Sulfate > strongIronThreshold (strong detection = real minerals)
  // v2.0.1: road mask now optional (default OFF) - see useRoadMask comment in settings.
  var isRoad = settings.useRoadMask
    ? ndvi.lt(0.25).and(b6.gte(0.20)).and(strongIronSignal.not())
    : ee.Image(0);

  // A pixel passes if ALL of:
  //   1. Green/Red ≤ 1.0 (ALWAYS required - no green peak)
  //   2. NOT a road (unless strong iron signal bypasses road check)
  //   3. Either NDVI < 0.25 OR (hasHighIron AND lowSWIR1 AND notDenseVeg)
  var passesVegMask = noGreenPeak
    .and(isRoad.not())
    .and(
      ndvi.lt(settings.ndviMax)
      .or(hasHighIron.and(lowSWIR1).and(notDenseVeg))
    );
  
  var validMask = passesVegMask
    .and(brightness.gt(0.05))                   // Exclude dark pixels
    .and(unifiedWater.not())                    // Exclude water
    .and(builtUpMask.not());                    // Exclude built-up areas
  
  var ironViz = ironIndex.updateMask(validMask);
  
  Map.addLayer(ironViz, {min: 0.0, max: 1.0, palette: ['cyan', 'yellow', 'orange', 'red']},
    '🔬 Iron Sulfate Index', false);
  
  Map.addLayer(settings.currentComposite.select('FerricIron1'), {min: 0, max: 3, palette: ['white', 'yellow', 'red']}, 
    '🔬 Ferric Iron Index', false);
  
  Map.addLayer(settings.currentComposite.select('MNDWI'), {min: -1, max: 1, palette: ['red', 'white', 'blue']}, 
    '🔬 MNDWI (Water)', false);
  
  if (settings.showAccuracyTools) {
    addAccuracyLayers();
  }
  
  return classification;
}

// =============================================================================
// ACCURACY VERIFICATION
// =============================================================================

function addAccuracyLayers() {
  if (!settings.currentComposite) return;
  
  var iron = settings.currentComposite.select('IronSulfate').gt(settings.ironSulfateThreshold);
  var ferric1 = settings.currentComposite.select('FerricIron1').gt(settings.ferricIron1Threshold);
  var clay = settings.currentComposite.select('ClaySulfateMica').gt(settings.claySulfateMicaThreshold);
  
  Map.addLayer(iron.selfMask(), {palette: ['red'], opacity: 0.5}, 'Iron Sulfate Mask', false);
  Map.addLayer(ferric1.selfMask(), {palette: ['orange'], opacity: 0.5}, 'Ferric Iron 1 Mask', false);
  Map.addLayer(clay.selfMask(), {palette: ['green'], opacity: 0.5}, 'Clay Mask', false);
  
  var mndwi = settings.currentComposite.select('MNDWI');
  var wetAreas = mndwi.gt(0.1).and(mndwi.lt(settings.waterThreshold));
  Map.addLayer(wetAreas.selfMask(), {palette: ['yellow'], opacity: 0.6},
    'Wet Areas (0.1 < MNDWI < threshold)', false);
}

// =============================================================================
// VALIDATION TOOLS
// =============================================================================

// LEVEL 1: Internal Consistency Validation
function performInternalValidation() {
  if (!settings.currentComposite) {
    print('⚠️  No composite loaded. Select a region first.');
    return;
  }
  
  print('\n═════════════════════════════════════════════════════════');
  print('🔬 INTERNAL VALIDATION CHECKS');
  print('═════════════════════════════════════════════════════════\n');
  
  var classification = createBooleanClassification();
  
  // Test 1: Class distribution
  var classStats = classification.reduceRegion({
    reducer: ee.Reducer.frequencyHistogram(),
    geometry: settings.currentRegion,
    scale: 90,
    maxPixels: 1e9,
    bestEffort: true
  });
  
  classStats.evaluate(function(stats) {
    var histogram = stats.classification || {};
    var totalPixels = Object.values(histogram).reduce(function(a, b) { return a + b; }, 0);
    
    print('1️⃣  CLASS DISTRIBUTION:');
    print('   Total pixels: ' + totalPixels.toLocaleString());
    print('');
    
    Object.keys(histogram).sort(function(a, b) { return parseInt(a) - parseInt(b); }).forEach(function(classNum) {
      var count = histogram[classNum];
      var percent = (count / totalPixels * 100).toFixed(2);
      if (percent > 0.1) {  // Only show classes > 0.1%
        print('   Class ' + classNum + ': ' + percent + '% (' + count.toLocaleString() + ' pixels)');
      }
    });
    
    // Iron sulfate summary
    var ironSulfateClasses = ['9', '12', '14', '17', '18', '19'];
    var ironPixels = ironSulfateClasses.reduce(function(sum, c) {
      return sum + (histogram[c] || 0);
    }, 0);
    var ironPercent = (ironPixels / totalPixels * 100).toFixed(2);
    
    print('\n2️⃣  IRON SULFATE SUMMARY:');
    print('   Total AMD area: ' + ironPercent + '%');
    
    if (ironPercent > 50) {
      print('   ⚠️  WARNING: >50% classified as AMD!');
      print('   This is unusually high. Check thresholds.');
    } else if (ironPercent < 0.01) {
      print('   ℹ️  INFO: <0.01% classified as AMD');
      print('   Area may be clean or thresholds too strict.');
    } else {
      print('   ✅ Iron sulfate percentage is reasonable');
    }
    
    // Water classification
    var waterPixels = (histogram['20'] || 0) + (histogram['21'] || 0);
    var waterPercent = (waterPixels / totalPixels * 100).toFixed(2);
    var contamPercent = ((histogram['20'] || 0) / totalPixels * 100).toFixed(2);
    var cleanPercent = ((histogram['21'] || 0) / totalPixels * 100).toFixed(2);
    
    print('\n3️⃣  WATER CLASSIFICATION:');
    print('   Total water: ' + waterPercent + '%');
    print('   Contaminated: ' + contamPercent + '% (Class 20)');
    print('   Clean: ' + cleanPercent + '% (Class 21)');
  });
  
  // Test 2: Index value ranges
  var indexChecks = settings.currentComposite.select([
    'IronSulfate', 'FerricIron1', 'FerricIron2', 'ClaySulfateMica'
  ]).reduceRegion({
    reducer: ee.Reducer.minMax(),
    geometry: settings.currentRegion,
    scale: 90,
    maxPixels: 1e9,
    bestEffort: true
  });
  
  indexChecks.evaluate(function(ranges) {
    print('\n4️⃣  INDEX VALUE RANGES:');
    ['IronSulfate', 'FerricIron1', 'FerricIron2', 'ClaySulfateMica'].forEach(function(idx) {
      var min = ranges[idx + '_min'];
      var max = ranges[idx + '_max'];
      if (min !== undefined && max !== undefined) {
        print('   ' + idx + ': ' + min.toFixed(3) + ' to ' + max.toFixed(3));
      }
    });
    
    // Sanity checks
    if (ranges.IronSulfate_max > 3) {
      print('   ⚠️  WARNING: Iron Sulfate max > 3 (unusual for 2/1-5/4 index!)');
    }
    if (ranges.IronSulfate_min < -5) {
      print('   ⚠️  WARNING: Iron Sulfate min < -5 (check preprocessing)');
    }
  });
  
  // Test 3: Spatial clustering
  print('\n5️⃣  SPATIAL PATTERN CHECK:');
  var ironMask = classification.gte(9).and(classification.lte(19));
  var ironPatches = ironMask.connectedPixelCount(100, false);
  
  var patchStats = ironPatches.reduceRegion({
    reducer: ee.Reducer.mean().combine(ee.Reducer.max(), '', true),
    geometry: settings.currentRegion,
    scale: 90,
    maxPixels: 1e9,
    bestEffort: true
  });
  
  patchStats.evaluate(function(stats) {
    var meanSize = stats.classification_mean || 0;
    var maxSize = stats.classification_max || 0;
    print('   Mean patch size: ' + meanSize.toFixed(1) + ' pixels');
    print('   Max patch size: ' + maxSize + ' pixels');
    
    if (meanSize < 2) {
      print('   ⚠️  WARNING: Very small patches (avg < 2 pixels)');
      print('   Classification may be noisy. Consider smoothing.');
    } else {
      print('   ✅ Reasonable clustering detected');
    }
  });
  
  print('\n═════════════════════════════════════════════════════════');
  print('✅ Internal validation complete');
  print('═════════════════════════════════════════════════════════\n');
}


// =============================================================================
// STATISTICS WITH DIAGNOSTICS
// =============================================================================

function calculateStats() {
  if (!settings.currentComposite) return;
  
  statsPanel.setValue('Calculating statistics...');
  
  var classification = createBooleanClassification();
  if (!classification) {
    statsPanel.setValue('No classification generated.');
    return;
  }
  
  var totalArea = settings.currentRegion.area();
  
  // AMD area for statistics is based on BOTH Iron Sulfate and Clay-Sulfate-Mica indices
  // Rockwell et al. (2021): corrected iron sulfate index (2/1 - 5/4) > threshold
  // (provisional 0.10) indicates jarosite; we additionally
  // require ClaySulfateMica > clay threshold so we don't treat all ferric-only areas as AMD.
  // CRITICAL: Also exclude dark pixels (division artifacts), vegetation, and clean water
  var ironIndex = settings.currentComposite.select('IronSulfate');
  var clayIndex = settings.currentComposite.select('ClaySulfateMica');
  var brightness = settings.currentComposite.select('Brightness');
  var ndvi = settings.currentComposite.select('NDVI');
  var mndwi = settings.currentComposite.select('MNDWI');
  
  // Exclusion masks for false positives
  var notTooLow = brightness.gt(0.05);  // Exclude dark pixels (division artifacts)
  var notVegetation = ndvi.lt(settings.ndviMax);  // Exclude dense vegetation
  var notCleanWater = mndwi.lt(settings.waterThreshold);  // Exclude clean water bodies
  
  var amdMask = ironIndex.gt(settings.ironSulfateThreshold)
    .and(clayIndex.gt(settings.claySulfateMicaThreshold))
    .and(notTooLow)
    .and(notVegetation)
    .and(notCleanWater);
  var amdPixelArea = amdMask.multiply(ee.Image.pixelArea());
  
  var amdAreaStats = amdPixelArea.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: settings.currentRegion,
    scale: 30,
    maxPixels: 1e10,
    bestEffort: true
  });
  
  var ironStats = settings.currentComposite.select('IronSulfate').reduceRegion({
    reducer: ee.Reducer.mean().combine(ee.Reducer.minMax(), '', true)
      .combine(ee.Reducer.percentile([10, 50, 90]), '', true),
    geometry: settings.currentRegion,
    scale: 30,
    maxPixels: 1e10,
    bestEffort: true
  });
  
  var bandCheck = settings.currentComposite.select(['SR_B1', 'SR_B2', 'SR_B4']).reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: settings.currentRegion,
    scale: 100,
    maxPixels: 1e9,
    bestEffort: true
  });
  
  totalArea.evaluate(function(total) {
    amdAreaStats.evaluate(function(amdStats) {
      ironStats.evaluate(function(iron) {
        bandCheck.evaluate(function(bands) {
          
          // Get first value from amdStats dictionary (band name may vary)
          var amdArea = (amdStats && Object.keys(amdStats).length > 0) 
            ? amdStats[Object.keys(amdStats)[0]] 
            : 0;
          var amdPercent = (amdArea / total * 100).toFixed(2);
          var amdKm2 = (amdArea / 1e6).toFixed(3);
          
          var statsText = 
            'AREA: ' + settings.currentAreaName + '\n' +
            'Total: ' + (total / 1e6).toFixed(2) + ' km2\n\n' +
            
            'IRON SULFATE MINERALS:\n' +
            '  Area: ' + amdKm2 + ' km2 (' + amdPercent + '%)\n' +
            '  Pixels: ~' + Math.round(amdArea / 900) + '\n\n' +
            
            'IRON SULFATE INDEX:\n' +
            '  Mean: ' + (iron.IronSulfate_mean || 0).toFixed(3) + '\n' +
            '  Median: ' + (iron.IronSulfate_p50 || 0).toFixed(3) + '\n' +
            '  Range: ' + (iron.IronSulfate_min || 0).toFixed(3) + 
            ' to ' + (iron.IronSulfate_max || 0).toFixed(3) + '\n' +
            '  10th percentile: ' + (iron.IronSulfate_p10 || 0).toFixed(3) + '\n' +
            '  90th percentile: ' + (iron.IronSulfate_p90 || 0).toFixed(3) + '\n\n' +
            
            'DIAGNOSTIC (Band Check):\n' +
            '  B1 mean: ' + (bands.SR_B1 || 0).toFixed(4) + '\n' +
            '  B2 mean: ' + (bands.SR_B2 || 0).toFixed(4) + '\n' +
            '  B4 mean: ' + (bands.SR_B4 || 0).toFixed(4) + '\n';
          
          if (iron.IronSulfate_mean < -3 || iron.IronSulfate_mean > 3) {
            statsText += '\n*** WARNING: Unusual values detected! ***\n' +
              'Iron sulfate mean should be 0.5-2.5\n' +
              'Bands may not be scaled correctly.\n';
          }
          
          if (bands.SR_B2 < 0 || bands.SR_B2 > 1) {
            statsText += '\n*** WARNING: Band values out of range! ***\n' +
              'Expected reflectance: 0.0 to 0.4\n' +
              'Actual B2 mean: ' + (bands.SR_B2 || 0).toFixed(4) + '\n' +
              'Check Landsat Collection version.\n';
          }
          
          statsText += '\n' +
            'THRESHOLDS:\n' +
            '  Iron: > ' + settings.ironSulfateThreshold.toFixed(2) + '\n' +
            '  Ferric1: > ' + settings.ferricIron1Threshold.toFixed(2) + '\n' +
            '  Clay: > ' + settings.claySulfateMicaThreshold.toFixed(2);
          
          if (settings.useAdvancedWaterDetection) {
            statsText += '\n  Contaminated H2O: Iron > ' + 
              settings.contaminatedWaterThreshold.toFixed(2) + ' in water';
          }
          
          statsPanel.setValue(statsText);
          print('STATISTICS SUMMARY:\n' + statsText);
        });
      });
    });
  });
}

// Enhanced click handler for detailed spectral analysis
Map.onClick(function(coords) {
  var point = ee.Geometry.Point([coords.lon, coords.lat]);
  
  print('=============================================');
  print('CLICKED AT: ' + coords.lat.toFixed(5) + ', ' + coords.lon.toFixed(5));
  print('Sampling data...');
  
  if (!settings.currentComposite) {
    print('ERROR: No composite loaded!');
    print('Please wait for imagery to load or change study area.');
    return;
  }
  
  var sample = settings.currentComposite.select([
    'SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7',
    'IronSulfate', 'FerricIron1', 'FerricIron2', 'FerrousIron',
    'ClaySulfateMica', 'GreenVeg', 'MNDWI', 'NDVI', 'NDWI', 'Brightness', 'AWEINSH', 'Turbidity', 'NDBI'
  ]).reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: point,
    scale: 30
  });
  
  sample.evaluate(function(props) {
    if (!props || Object.keys(props).length === 0) {
      print('ERROR: No data at this location');
      print('This pixel may be masked (clouds/water) or outside imagery bounds');
      return;
    }
    
    // Index values
    var iron = props.IronSulfate || 0;
    var ferric1 = props.FerricIron1 || 0;
    var ferric2 = props.FerricIron2 || 0;
    var ferrous = props.FerrousIron || 0;
    var clay = props.ClaySulfateMica || 0;
    var greenVeg = props.GreenVeg || 0;
    var mndwi = props.MNDWI || 0;
    var ndvi = props.NDVI || 0;
    var ndwi = props.NDWI || 0;
    var brightness = props.Brightness || 0;
    var turbidity = props.Turbidity || 0;
    var ndbi = props.NDBI || 0;
    var aweinsh = props.AWEINSH || 0;
    
    // Detection flags (matching createBooleanClassification logic)
    var hasIron = iron > settings.ironSulfateThreshold;
    var hasFerric1 = ferric1 > settings.ferricIron1Threshold;
    var hasFerric2 = ferric2 > settings.ferricIron2Threshold;
    var hasFerrous = ferrous > settings.ferrousIronThreshold;
    var hasClay = clay > settings.claySulfateMicaThreshold;
    var hasVeg = greenVeg > settings.greenVegThreshold;
    var isWater = mndwi > settings.waterThreshold && aweinsh > settings.aweinshThreshold;
    var isContaminated = iron > settings.contaminatedWaterThreshold && isWater && brightness > 0.05 && brightness < 0.20;
    var isDarkWater = isWater && brightness < 0.05;
    // Sensor-specific brightness threshold for built-up detection
    // Sentinel-2 (10m) uses 0.15, Landsat (30m) uses 0.18
    var isSentinel2 = settings.currentSensor === 'Sentinel-2';
    var builtUpBrightnessThreshold = isSentinel2 ? 0.15 : settings.builtUpBrightnessMin;
    // MNDWI logic: dry land buildings (< -0.20) OR water-edge buildings (-0.1 to +0.1)
    var isDryLandBuilding = mndwi < settings.builtUpMNDWIMax;  // MNDWI < -0.20
    var isWaterEdgeBuilding = mndwi > -0.10 && mndwi < 0.10;   // Marinas, docks
    var isBuiltUp = brightness > builtUpBrightnessThreshold && 
                    ndvi < settings.builtUpNDVIMax && 
                    ndvi > settings.builtUpNDVIMin && 
                    (isDryLandBuilding || isWaterEdgeBuilding);
    
    // Mask flags (for Iron Sulfate visualization layer)
    var b3Val = props.SR_B3 || 0;
    var b4Val = props.SR_B4 || 0;
    var b6Val = props.SR_B6 || 0;
    var greenRedRatio = b4Val > 0 ? b3Val / b4Val : 0;
    
    // Multi-criteria iron soil detection
    // KEY: Green/Red ≤ 1.0 is ALWAYS required (no vegetation green peak)
    var noGreenPeak = greenRedRatio <= 1.0;           // Red ≥ Green (no chlorophyll green peak)
    var lowSWIR1 = b6Val < 0.20;                      // SWIR1 < 0.20 (not road/impervious surface)
    var notDenseVeg = greenVeg < 3.5;                 // Not extremely high vegetation index
    var strongIronSignal = iron > settings.strongIronThreshold;  // Strong iron = likely real minerals (v2.0: rescaled)

    // Road detection: BYPASS if Iron Sulfate > strongIronThreshold (strong detection = real iron minerals)
    // CRITICAL: Iron oxide minerals (jarosite, goethite) naturally have HIGH SWIR1
    var isRoad = settings.useRoadMask && ndvi < 0.25 && b6Val >= 0.20 && !strongIronSignal;
    
    // New logic: ALWAYS require noGreenPeak AND not a road (unless strong iron bypasses)
    var passesNDVIMask = noGreenPeak && !isRoad && (ndvi < settings.ndviMax || (hasIron && lowSWIR1 && notDenseVeg));
    var passesBrightnessMask = brightness > 0.05;
    var passesWaterMask = !isWater;
    var passesBuiltUpMask = !isBuiltUp;
    
    // Determine classification
    var classification = 'None';
    var napLevel = 'N/A';
    var napColor = '';
    var interpretation = '';
    
    // NEW: Check for built-up area false positive FIRST
    if (isBuiltUp && hasIron) {
      classification = 'BUILDING/URBAN AREA (FALSE POSITIVE)';
      napLevel = 'N/A';
      napColor = '[GRAY]';
      interpretation = 
        '*** BUILT-UP AREA DETECTED ***\n' +
        'Criteria met:\n' +
        '  • Brightness > ' + settings.builtUpBrightnessMin.toFixed(2) + ' (Very bright surface)\n' +
        '  • NDVI near 0 (No vegetation)\n' +
        '  • MNDWI < ' + settings.builtUpMNDWIMax.toFixed(2) + ' (Very dry)\n\n' +
        'High iron value is FALSE POSITIVE.\n' +
        'Likely: Bright roof, pavement, or artificial surface.\n\n' +
        'Actual values:\n' +
        '  Brightness: ' + brightness.toFixed(3) + '\n' +
        '  NDVI: ' + ndvi.toFixed(3) + '\n' +
        '  MNDWI: ' + mndwi.toFixed(3) + '\n' +
        '  NDBI: ' + ndbi.toFixed(3) + ' (reference only)';
    } else if (isDarkWater && iron > settings.contaminatedWaterThreshold) {
      classification = 'DEEP WATER (FALSE POSITIVE)';
      napLevel = 'N/A';
      napColor = '[BLUE]';
      interpretation = 
        '*** DEEP WATER - FALSE POSITIVE ***\n' +
        'High iron value is artifact from low light.\n' +
        'Water too dark (brightness < 0.05).\n' +
        'This is likely clean deep water.\n\n' +
        'Actual values:\n' +
        '  Iron Sulfate: ' + iron.toFixed(3) + '\n' +
        '  Brightness: ' + brightness.toFixed(3) + ' [TOO DARK]\n' +
        '  MNDWI: ' + mndwi.toFixed(3);
    } else if (isWater || isContaminated) {
      classification = 'WATER BODY - See Water Quality Classification';
      napLevel = 'N/A (handled by Water Quality module)';
      napColor = '[BLUE]';
      interpretation = 
        'This pixel is classified as WATER.\n\n' +
        'Water contamination analysis is handled by the separate\n' +
        '🌊 Water Quality Classification layer.\n\n' +
        'Toggle the Water Quality layer ON to see:\n' +
        '  • Blue = Clean water\n' +
        '  • Orange = Moderate contamination\n' +
        '  • Red = Severe contamination\n\n' +
        'Water Quality uses multi-criteria scoring (0-9):\n' +
        '  - NIR Anomaly (dissolved iron)\n' +
        '  - Turbidity (suspended particles)\n' +
        '  - Iron Water Index\n' +
        '  - Yellow Index\n' +
        '  - And more...\n\n' +
        'Raw indices for this pixel:\n' +
        '  MNDWI: ' + mndwi.toFixed(3) + '\n' +
        '  AWEINSH: ' + aweinsh.toFixed(3) + '\n' +
        '  Iron Sulfate: ' + iron.toFixed(3) + '\n' +
        '  Turbidity: ' + turbidity.toFixed(3) + '\n' +
        '  Brightness: ' + brightness.toFixed(3);
    } else if (hasIron && hasClay && hasFerric1) {
      if (iron > 2.0) {
        classification = 'CLASS 14: Abundant Iron Sulfate Minerals';
        napLevel = 'EXTREME (NAP = 1)';
        napColor = '[RED]';
        interpretation = 
          'ABUNDANT JAROSITE DETECTED!\n' +
          'Iron Sulfate Index: ' + iron.toFixed(3) + ' (>0.30 = abundant)\n\n' +
          'This indicates:\n' +
          '  Active pyrite weathering\n' +
          '  High acid production potential\n' +
          '  Likely mine waste or altered rock\n\n' +
          'Comparable to paper Goldfield, NV example.';
      } else {
        classification = 'CLASS 12: Major Iron Sulfate';
        napLevel = 'VERY HIGH (NAP = 2)';
        napColor = '[RED]';
        interpretation = 
          'Major iron sulfate minerals detected.\n' +
          'Likely jarosite from pyrite weathering.\n' +
          'High acid production potential.';
      }
    } else if (hasIron && hasClay) {
      classification = 'CLASS 14: Oxidizing Sulfides';
      napLevel = 'EXTREME (NAP = 1)';
      napColor = '[RED]';
      interpretation = 
        'Weathering pyrite with developing jarosite.\n' +
        'Early stage AMD formation.';
    } else if (hasIron && hasFerric1) {
      // NEW: Iron sulfate fallback - Iron + Ferric1 detected but no clay
      // This matches the classification fallback to Class 12
      classification = 'CLASS 12: Iron Sulfate (No Clay)';
      napLevel = 'HIGH (NAP = 2-3)';
      napColor = '[ORANGE-RED]';
      interpretation = 
        'IRON SULFATE DETECTED!\n' +
        'Iron Sulfate Index: ' + iron.toFixed(3) + ' (>' + settings.ironSulfateThreshold + ')\n' +
        'Ferric Iron 1: ' + ferric1.toFixed(3) + '\n\n' +
        'NOTE: Clay-Sulfate-Mica is below threshold (' + clay.toFixed(3) + ').\n' +
        'This may indicate:\n' +
        '  - Fresh jarosite without clay alteration\n' +
        '  - Acid mine drainage on non-clay substrate\n' +
        '  - Early-stage pyrite oxidation\n\n' +
        'Classification: Fallback to Class 12 (Major Iron Sulfate).';
    } else if (hasIron) {
      // Iron only - no ferric, no clay
      classification = 'CLASS 12: Iron Sulfate (Fallback)';
      napLevel = 'MODERATE-HIGH';
      napColor = '[ORANGE]';
      interpretation = 
        'IRON SULFATE INDEX ELEVATED!\n' +
        'Iron Sulfate Index: ' + iron.toFixed(3) + ' (>' + settings.ironSulfateThreshold + ')\n\n' +
        'Other indices below threshold:\n' +
        '  Ferric Iron 1: ' + ferric1.toFixed(3) + ' (threshold: ' + settings.ferricIron1Threshold + ')\n' +
        '  Clay: ' + clay.toFixed(3) + ' (threshold: ' + settings.claySulfateMicaThreshold + ')\n\n' +
        'This may indicate:\n' +
        '  - Dissolved iron sulfates\n' +
        '  - Weathered pyrite\n' +
        '  - AMD-impacted soil or sediment';
    } else if (hasClay && hasFerric1 && hasFerric2) {
      classification = 'CLASS 8: Clay + Major Ferric';
      napLevel = 'MODERATE';
      napColor = '[ORANGE]';
      interpretation = 'Hydrothermally altered rock.\nNo iron sulfate detected.';
    } else if (hasClay) {
      classification = 'CLASS 5: Clay-Sulfate-Mica';
      napLevel = 'MINIMAL';
      napColor = '[GREEN]';
      interpretation = 'Clay minerals detected.\nNo significant iron.';
    } else if (hasFerric1) {
      classification = 'CLASS 1: Minor Ferric Iron';
      napLevel = 'LOW';
      napColor = '[BROWN]';
      interpretation = 'Natural iron oxides (hematite/goethite).';
    } else {
      classification = 'NO CLASSIFICATION';
      napLevel = 'N/A';
      napColor = '[WHITE]';
      interpretation = 'No significant mineral signatures detected.';
    }
    
    var output = 
      '=============================================\n' +
      'LOCATION: ' + coords.lat.toFixed(5) + ', ' + coords.lon.toFixed(5) + '\n' +
      '=============================================\n\n' +
      'CALCULATED INDICES:\n\n' +
      '  Iron Sulfate = ' + iron.toFixed(3) + (hasIron ? ' [DETECTED]' : ' [Below threshold]') + '\n' +
      '  Ferric Iron 1 = ' + ferric1.toFixed(3) + (hasFerric1 ? ' [DETECTED]' : '') + '\n' +
      '  Ferric Iron 2 = ' + ferric2.toFixed(3) + (hasFerric2 ? ' [DETECTED]' : '') + '\n' +
      '  Ferrous Iron = ' + ferrous.toFixed(3) + (hasFerrous ? ' [DETECTED]' : '') + '\n' +
      '  Clay-Sulfate-Mica = ' + clay.toFixed(3) + (hasClay ? ' [DETECTED]' : '') + '\n' +
      '  GreenVeg = ' + greenVeg.toFixed(3) + (hasVeg ? ' [VEG DETECTED]' : '') + '\n' +
      '  NDVI = ' + ndvi.toFixed(3) + (ndvi > settings.ndviMax ? ' [MASKED]' : ' [OK]') + '\n' +
      '  MNDWI = ' + mndwi.toFixed(3) + (isWater ? ' [WATER]' : ' [LAND]') + '\n' +
      '  Brightness = ' + brightness.toFixed(3) + '\n\n' +
      '=============================================\n' +
      napColor + ' CLASSIFICATION: ' + classification + '\n' +
      'ACID PRODUCTION: ' + napLevel + '\n' +
      '=============================================\n\n' +
      'DETECTION FLAGS:\n' +
      '  hasIron: ' + hasIron + ' (>' + settings.ironSulfateThreshold + ')\n' +
      '  hasFerric1: ' + hasFerric1 + ' (>' + settings.ferricIron1Threshold + ')\n' +
      '  hasFerric2: ' + hasFerric2 + ' (>' + settings.ferricIron2Threshold + ')\n' +
      '  hasFerrous: ' + hasFerrous + ' (>' + settings.ferrousIronThreshold + ')\n' +
      '  hasClay: ' + hasClay + ' (>' + settings.claySulfateMicaThreshold + ')\n' +
      '  hasVeg: ' + hasVeg + ' (>' + settings.greenVegThreshold + ')\n' +
      '  isWater: ' + isWater + '\n' +
      '  isBuiltUp: ' + isBuiltUp + '\n\n' +
      'IRON SULFATE LAYER MASKS:\n' +
      '  --- REQUIRED: No Green Peak ---\n' +
      '  Green/Red: ' + greenRedRatio.toFixed(3) + ' ≤1.0? ' + (noGreenPeak ? 'PASS' : 'FAIL ← VEGETATION EXCLUDED') + '\n' +
      '  --- Road Detection ---\n' +
      '  Road mask: ' + (settings.useRoadMask ? 'ENABLED' : 'DISABLED (v2.0.1 default - SWIR1 cannot separate roads from jarosite)') + '\n' +
      '  Strong Iron (>' + settings.strongIronThreshold + ')? ' + (strongIronSignal ? 'YES → BYPASS road check (real minerals)' : 'NO') + '\n' +
      '  Is Road? (mask on AND NDVI<0.25 AND SWIR1≥0.20 AND Iron≤' + settings.strongIronThreshold + '): ' + (isRoad ? 'YES ← ROAD EXCLUDED' : 'NO') + '\n' +
      '  --- Additional Criteria: ---\n' +
      '  NDVI: ' + ndvi.toFixed(3) + ' <' + settings.ndviMax + '? ' + (ndvi < settings.ndviMax ? 'PASS' : 'needs iron soil check') + '\n' +
      '  SWIR1 (B6): ' + b6Val.toFixed(3) + ' <0.20? ' + (lowSWIR1 ? 'PASS' : (strongIronSignal ? 'N/A (strong iron bypasses)' : 'FAIL (road/impervious)')) + '\n' +
      '  GreenVeg: ' + greenVeg.toFixed(3) + ' <3.5? ' + (notDenseVeg ? 'PASS' : 'FAIL') + '\n' +
      '  --- Final Mask Results: ---\n' +
      '  Vegetation/Road mask: ' + (passesNDVIMask ? 'PASS' : 'FAIL' + (!noGreenPeak ? ' (Green>Red=vegetation)' : (isRoad ? ' (road detected)' : ''))) + '\n' +
      '  Brightness mask: ' + (passesBrightnessMask ? 'PASS' : 'FAIL') + '\n' +
      '  Water mask: ' + (passesWaterMask ? 'PASS' : 'FAIL') + '\n' +
      '  Built-up mask: ' + (passesBuiltUpMask ? 'PASS' : 'FAIL') + '\n' +
      '  OVERALL: ' + (passesNDVIMask && passesBrightnessMask && passesWaterMask && passesBuiltUpMask ? '✓ VISIBLE' : '✗ MASKED OUT') + '\n\n' +
      'INTERPRETATION:\n' +
      interpretation + '\n\n' +
      'RAW BAND REFLECTANCES:\n' +
      '  B1 (Coastal): ' + (props.SR_B1 || 0).toFixed(4) + '\n' +
      '  B2 (Blue): '     + (props.SR_B2 || 0).toFixed(4) + '\n' +
      '  B3 (Green): '    + (props.SR_B3 || 0).toFixed(4) + '\n' +
      '  B4 (Red): '      + (props.SR_B4 || 0).toFixed(4) + '\n' +
      '  B5 (NIR): '      + (props.SR_B5 || 0).toFixed(4) + '\n' +
      '  B6 (SWIR1): '    + (props.SR_B6 || 0).toFixed(4) + '\n' +
      '  B7 (SWIR2): '    + (props.SR_B7 || 0).toFixed(4) + '\n\n' +
      '=============================================';
    
    print(output);
    
    // Update clicked point marker
    Map.layers().forEach(function(layer) {
      if (layer.getName() === 'Clicked Point') {
        Map.remove(layer);
      }
    });
    Map.addLayer(point, {color: 'yellow'}, 'Clicked Point');
  });
});

// =============================================================================
// USER INTERFACE
// =============================================================================

// Create main container panel
var panel = ui.Panel({
  style: {
    width: '330px',
    position: 'top-right'
  }
});

// Create scrollable content panel inside
var scrollPanel = ui.Panel({
  style: {
    maxHeight: '90vh',
    padding: '10px'
  },
  layout: ui.Panel.Layout.flow('vertical')
});

// Title
var title = ui.Label('USGS AMD Detection Tool', {
  fontWeight: 'bold', fontSize: '16px', margin: '0 0 4px 0'
});

var subtitle = ui.Label('Rockwell et al. (2021) - ' + TOOL_VERSION, {
  fontSize: '9px', color: '#666', margin: '0 0 10px 0'
});

// Sensor selector
var sensorLabel = ui.Label('Sensor:', {fontWeight: 'bold', fontSize: '10px', margin: '6px 0 2px 0'});
var sensorSelect = ui.Select({
  items: Object.keys(SENSOR_CONFIG),
  value: settings.currentSensor,
  style: {stretch: 'horizontal'},
  onChange: function(selected) {
    settings.currentSensor = selected;
    print('🔄 Sensor changed to: ' + selected);
    // Show/hide cloud masking selector based on sensor
    if (selected === 'Sentinel-2') {
      cloudMaskLabel.style().set('shown', true);
      cloudMaskSelect.style().set('shown', true);
      cloudMaskHelp.style().set('shown', true);
    } else {
      cloudMaskLabel.style().set('shown', false);
      cloudMaskSelect.style().set('shown', false);
      cloudMaskHelp.style().set('shown', false);
    }
    updateEverything();
  }
});

// Cloud masking method selector (Sentinel-2 only)
var cloudMaskLabel = ui.Label('Cloud Masking:', {
  fontWeight: 'bold', fontSize: '10px', margin: '6px 0 2px 0'
});
var cloudMaskSelect = ui.Select({
  items: ['SCL+Prob', 'CS', 'CS_CDF', 'Hybrid', 'Hybrid Strict', 'Unmasked'],
  value: settings.cloudMaskingMethod,
  style: {stretch: 'horizontal'},
  onChange: function(selected) {
    settings.cloudMaskingMethod = selected;
    print('☁️ Cloud masking changed to: ' + selected);
    updateEverything();
  }
});

var cloudMaskHelp = ui.Label(
  'Hybrid=SCL+Prob+CS+CS_CDF | Strict=more aggressive',
  {fontSize: '8px', color: '#666', fontStyle: 'italic', margin: '1px 0 6px 0'}
);

// Hide cloud masking controls initially if not Sentinel-2
if (settings.currentSensor !== 'Sentinel-2') {
  cloudMaskLabel.style().set('shown', false);
  cloudMaskSelect.style().set('shown', false);
  cloudMaskHelp.style().set('shown', false);
}

// NEW: Compositing method selector
var compositingLabel = ui.Label('Compositing:', {
  fontWeight: 'bold', fontSize: '10px', margin: '6px 0 2px 0'
});
var compositingSelect = ui.Select({
  items: ['median', 'mean', 'mosaic', 'latest', 'quality'],
  value: settings.compositingMethod,
  style: {stretch: 'horizontal'},
  onChange: function(selected) {
    settings.compositingMethod = selected;
    print('🔧 Compositing changed to: ' + selected);
    print('💡 Reload study area to apply changes.');
  }
});

var compositingHelp = ui.Label(
  'median=avg | latest=recent | quality=best',
  {fontSize: '8px', color: '#666', fontStyle: 'italic', margin: '1px 0 6px 0'}
);

// NEW: Season filter selector
var seasonLabel = ui.Label('Season Filter:', {
  fontWeight: 'bold', fontSize: '10px', margin: '6px 0 2px 0'
});
var seasonSelect = ui.Select({
  items: Object.keys(SEASON_MONTHS),
  value: settings.seasonFilter,
  style: {stretch: 'horizontal'},
  onChange: function(selected) {
    settings.seasonFilter = selected;
    print('🌤️ Season filter: ' + selected);
    if (selected === 'All Year') {
      print('   Using all months in date range');
    } else {
      var months = SEASON_MONTHS[selected];
      print('   Filtering to months: ' + months.join(', '));
    }
    print('💡 Reload study area to apply changes.');
  }
});

var seasonHelp = ui.Label(
  'Summer avoids snow | Winter for ice studies',
  {fontSize: '8px', color: '#666', fontStyle: 'italic', margin: '1px 0 6px 0'}
);

// NEW: Date range controls
var dateRangeLabel = ui.Label('Date Filter:', {
  fontWeight: 'bold', fontSize: '10px', margin: '6px 0 2px 0'
});

// FIXED: Removed auto-update from date inputs (was too aggressive while typing)
// Now uses "Apply Date Range" button instead
var startDateBox = ui.Textbox({
  placeholder: 'Start: YYYY-MM-DD',
  value: '',
  style: {stretch: 'horizontal', fontSize: '9px'},
  onChange: function(value) {
    if (value && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      settings.specificStartDate = value;
      settings.useSpecificDate = true;
      print('📅 Start date set: ' + value + ' (click Apply to update)');
    } else if (!value) {
      settings.useSpecificDate = false;
    }
  }
});

var endDateBox = ui.Textbox({
  placeholder: 'End: YYYY-MM-DD',
  value: '',
  style: {stretch: 'horizontal', fontSize: '9px'},
  onChange: function(value) {
    if (value && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      settings.specificEndDate = value;
      settings.useSpecificDate = true;
      print('📅 End date set: ' + value + ' (click Apply to update)');
    } else if (!value) {
      settings.useSpecificDate = false;
    }
  }
});

// NEW: Apply Date Range button (replaces aggressive auto-update)
var applyDatesButton = ui.Button({
  label: 'Apply Date Range',
  style: {stretch: 'horizontal', fontSize: '9px', margin: '2px 0 0 0'},
  onClick: function() {
    var startVal = startDateBox.getValue();
    var endVal = endDateBox.getValue();
    var validStart = startVal && /^\d{4}-\d{2}-\d{2}$/.test(startVal);
    var validEnd = endVal && /^\d{4}-\d{2}-\d{2}$/.test(endVal);
    
    if (validStart && validEnd) {
      settings.useSpecificDate = true;
      print('🔄 Applying date range: ' + startVal + ' to ' + endVal);
      updateEverything();
    } else {
      print('⚠️ Please enter valid dates in YYYY-MM-DD format');
    }
  }
});

var clearDatesButton = ui.Button({
  label: 'Clear Dates',
  style: {stretch: 'horizontal', fontSize: '9px', margin: '2px 0 6px 0'},
  onClick: function() {
    settings.useSpecificDate = false;
    startDateBox.setValue('');
    endDateBox.setValue('');
    print('✅ Date filter cleared. Updating...');
    updateEverything();
  }
});

// Region selector
var regionLabel = ui.Label('Study Area:', {fontWeight: 'bold', fontSize: '10px', margin: '6px 0 2px 0'});
var regionSelect = ui.Select({
  items: areaNames,
  value: currentAreaName,
  style: {stretch: 'horizontal'},
  onChange: function(selected) {
    settings.currentAreaName = selected;
    settings.currentRegion = studyAreas[selected];
    Map.centerObject(settings.currentRegion, 12);
    updateEverything();
  }
});

// Iron Sulfate threshold
var ironLabel = ui.Label('Iron: 0.10', {margin: '8px 0 2px 0', fontSize: '9px'});
var ironSlider = ui.Slider({
  min: -0.5, max: 1.0, value: 0.10, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.ironSulfateThreshold = value;
    ironLabel.setValue('Iron: ' + value.toFixed(2));
    updateDetection();
  }
});

// Ferric Iron 1 threshold
var ferric1Label = ui.Label('Ferric 1: 1.40', {margin: '6px 0 2px 0', fontSize: '9px'});
var ferric1Slider = ui.Slider({
  min: 1.0, max: 2.5, value: 1.4, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.ferricIron1Threshold = value;
    ferric1Label.setValue('Ferric 1: ' + value.toFixed(2));
    updateDetection();
  }
});

// Clay-Sulfate-Mica threshold
var clayLabel = ui.Label('Clay: 0.12', {margin: '6px 0 2px 0', fontSize: '9px'});
var claySlider = ui.Slider({
  min: 0.0, max: 0.5, value: 0.12, step: 0.02,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.claySulfateMicaThreshold = value;
    clayLabel.setValue('Clay: ' + value.toFixed(2));
    updateDetection();
  }
});

// Water mask controls
// Cloud masking threshold controls (Sentinel-2 only)
var cloudThresholdHeader = ui.Label({
  value: '☁️ CLOUD MASKING THRESHOLDS',
  style: {
    fontWeight: 'bold',
    fontSize: '10px',
    margin: '12px 0 4px 0',
    color: '#0066CC'
  }
});

var cloudThresholdHelp = ui.Label({
  value: 'Adjust cloud detection sensitivity (Sentinel-2 only)',
  style: {fontSize: '8px', margin: '0 0 4px 0', color: '#666', fontStyle: 'italic'}
});

// Cloud Probability Threshold
var cloudProbLabel = ui.Label('Cloud Prob: 20', {margin: '4px 0 2px 0', fontSize: '9px'});
var cloudProbSlider = ui.Slider({
  min: 5, max: 60, value: 20, step: 5,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    CLOUD_THRESHOLDS.CLOUD_PROB = value;
    cloudProbLabel.setValue('Cloud Prob: ' + value.toFixed(0));
    if (settings.currentSensor === 'Sentinel-2') {
      print('☁️ Cloud Prob threshold: ' + value);
      updateEverything();
    }
  }
});

// CS Threshold
var csLabel = ui.Label('CS Threshold: 0.60', {margin: '2px 0 2px 0', fontSize: '9px'});
var csSlider = ui.Slider({
  min: 0.40, max: 0.80, value: 0.60, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    CLOUD_THRESHOLDS.CS_THRESHOLD = value;
    csLabel.setValue('CS Threshold: ' + value.toFixed(2));
    if (settings.currentSensor === 'Sentinel-2') {
      print('☁️ CS threshold: ' + value);
      updateEverything();
    }
  }
});

// CS_CDF Threshold
var csCdfLabel = ui.Label('CS_CDF Threshold: 0.60', {margin: '2px 0 2px 0', fontSize: '9px'});
var csCdfSlider = ui.Slider({
  min: 0.40, max: 0.80, value: 0.60, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    CLOUD_THRESHOLDS.CS_CDF_THRESHOLD = value;
    csCdfLabel.setValue('CS_CDF Threshold: ' + value.toFixed(2));
    if (settings.currentSensor === 'Sentinel-2') {
      print('☁️ CS_CDF threshold: ' + value);
      updateEverything();
    }
  }
});

// Cloud masking preset buttons
var cloudPresetLabel = ui.Label('⚡ PRESETS:', {
  fontWeight: 'bold', fontSize: '9px', margin: '8px 0 4px 0', color: '#FF8800'
});

function setCloudPreset(cp, cs, cscdf) {
  CLOUD_THRESHOLDS.CLOUD_PROB = cp;
  CLOUD_THRESHOLDS.CS_THRESHOLD = cs;
  CLOUD_THRESHOLDS.CS_CDF_THRESHOLD = cscdf;
  cloudProbSlider.setValue(cp);
  csSlider.setValue(cs);
  csCdfSlider.setValue(cscdf);
  if (settings.currentSensor === 'Sentinel-2') {
    print('⚡ Cloud preset applied: CP=' + cp + ', CS=' + cs + ', CS_CDF=' + cscdf);
    updateEverything();
  }
}

var cloudPresetPanel = ui.Panel({layout: ui.Panel.Layout.flow('horizontal')});
cloudPresetPanel.add(ui.Button({
  label: '🔥 Strict',
  style: {fontSize: '9px'},
  onClick: function() { setCloudPreset(10, 0.70, 0.70); }
}));
cloudPresetPanel.add(ui.Button({
  label: '⚖️ Default',
  style: {fontSize: '9px'},
  onClick: function() { setCloudPreset(20, 0.60, 0.60); }
}));
cloudPresetPanel.add(ui.Button({
  label: '🌿 Loose',
  style: {fontSize: '9px'},
  onClick: function() { setCloudPreset(40, 0.50, 0.50); }
}));

var waterCheckbox = ui.Checkbox({
  label: 'Exclude Water Bodies',
  value: true,
  style: {fontSize: '9px'},
  onChange: function(checked) {
    settings.useWaterMask = checked;
    waterSlider.setDisabled(!checked);
    updateDetection();
  }
});

var waterLabel = ui.Label('Water: 0.30', {margin: '2px 0 2px 0', fontSize: '9px'});
var waterSlider = ui.Slider({
  min: 0.0, max: 0.6, value: 0.3, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.waterThreshold = value;
    waterLabel.setValue('Water: ' + value.toFixed(2));
    updateDetection();
  }
});

// ═══════════════════════════════════════════════════════════════════════
// ADVANCED THRESHOLDING OPTIONS
// ═══════════════════════════════════════════════════════════════════════

var advancedHeader = ui.Label({
  value: '⚙️ ADVANCED THRESHOLDING',
  style: {
    fontWeight: 'bold',
    fontSize: '10px',
    margin: '12px 0 4px 0',
    color: '#8B4513'
  }
});

var advancedHelp = ui.Label({
  value: 'Paper methods: Adaptive for mountains, Fixed for homogeneous terrain',
  style: {fontSize: '8px', margin: '0 0 4px 0', color: '#666', fontStyle: 'italic'}
});

// Adaptive Thresholds Toggle (from paper Section 3.3)
var adaptiveCheckbox = ui.Checkbox({
  label: 'Use Adaptive Thresholds (mean + N×σ)',
  value: false,
  style: {fontSize: '9px', margin: '0 0 4px 0'},
  onChange: function(checked) {
    settings.useStdDevThresholds = checked;
    adaptiveMultPanel.style().set('shown', checked);
    print(checked ? '📊 Adaptive thresholds ENABLED (recommended for heterogeneous terrain)' : 
                    '📊 Fixed thresholds ENABLED (paper defaults)');
    updateDetection();
  }
});

// Multiplier sliders (only shown when adaptive is enabled)
var adaptiveMultPanel = ui.Panel({style: {shown: false, margin: '0 0 4px 0'}});

var ironMultLabel = ui.Label('Iron σ Mult: 2.0', {margin: '2px 0 2px 0', fontSize: '9px'});
var ironMultSlider = ui.Slider({
  min: 1.0, max: 3.0, value: 2.0, step: 0.1,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.ironStdMult = value;
    ironMultLabel.setValue('Iron σ Mult: ' + value.toFixed(1));
    if (settings.useStdDevThresholds) updateDetection();
  }
});

var ferricMultLabel = ui.Label('Ferric σ Mult: 1.5', {margin: '2px 0 2px 0', fontSize: '9px'});
var ferricMultSlider = ui.Slider({
  min: 1.0, max: 3.0, value: 1.5, step: 0.1,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.ferric1StdMult = value;
    settings.ferric2StdMult = value;
    ferricMultLabel.setValue('Ferric σ Mult: ' + value.toFixed(1));
    if (settings.useStdDevThresholds) updateDetection();
  }
});

adaptiveMultPanel.add(ironMultLabel);
adaptiveMultPanel.add(ironMultSlider);
adaptiveMultPanel.add(ferricMultLabel);
adaptiveMultPanel.add(ferricMultSlider);

// Index Clipping Toggle (from paper Section 3.4)
var clippingCheckbox = ui.Checkbox({
  label: 'Enable Index Clipping (95th percentile)',
  value: false,
  style: {fontSize: '9px', margin: '4px 0 4px 0'},
  onChange: function(checked) {
    settings.useIndexClipping = checked;
    print(checked ? '✂️ Index clipping ENABLED (caps extreme outliers)' : 
                    '✂️ Index clipping DISABLED');
    updateDetection();
  }
});

var clippingHelp = ui.Label({
  value: 'Recommended for Sentinel-2 (noisier than Landsat)',
  style: {fontSize: '8px', margin: '0 0 8px 0', color: '#666', fontStyle: 'italic'}
});

// ═══════════════════════════════════════════════════════════════════════
// WATER QUALITY MODULE
// ═══════════════════════════════════════════════════════════════════════

var waterQualityHeader = ui.Label({
  value: '🌊 WATER CONTAMINATION DETECTION',
  style: {
    fontWeight: 'bold',
    fontSize: '10px',
    margin: '12px 0 4px 0',
    color: '#0066CC'
  }
});

var waterQualityHelp = ui.Label({
  value: 'Separate module - detects sulfate/iron contamination in water bodies',
  style: {fontSize: '8px', margin: '0 0 4px 0', color: '#666', fontStyle: 'italic'}
});

// Enable/disable water quality module
var waterQualityCheckbox = ui.Checkbox({
  label: 'Enable Water Quality Analysis',
  value: true,
  style: {fontSize: '9px', margin: '0 0 8px 0', fontWeight: 'bold'},
  onChange: function(checked) {
    settings.enableWaterQualityModule = checked;
    updateDetection();
  }
});

// NIR Anomaly Moderate Threshold
var nirModLabel = ui.Label('NIR Anomaly (Mod): 0.03', {margin: '4px 0 2px 0', fontSize: '9px'});
var nirModSlider = ui.Slider({
  min: 0.01, max: 0.10, value: 0.03, step: 0.01,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.nirAnomalyThresholdModerate = value;
    nirModLabel.setValue('NIR Anomaly (Mod): ' + value.toFixed(2));
    updateDetection();
  }
});

// NIR Anomaly Severe Threshold
var nirSevLabel = ui.Label('NIR Anomaly (Sev): 0.08', {margin: '2px 0 2px 0', fontSize: '9px'});
var nirSevSlider = ui.Slider({
  min: 0.05, max: 0.15, value: 0.08, step: 0.01,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.nirAnomalyThresholdSevere = value;
    nirSevLabel.setValue('NIR Anomaly (Sev): ' + value.toFixed(2));
    updateDetection();
  }
});

// Turbidity Ratio Moderate
var turbModLabel = ui.Label('Turbidity Ratio (Mod): 1.30', {margin: '2px 0 2px 0', fontSize: '9px'});
var turbModSlider = ui.Slider({
  min: 1.0, max: 2.0, value: 1.3, step: 0.1,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.turbidityRatioModerate = value;
    turbModLabel.setValue('Turbidity Ratio (Mod): ' + value.toFixed(2));
    updateDetection();
  }
});

// Turbidity Ratio Severe
var turbSevLabel = ui.Label('Turbidity Ratio (Sev): 2.00', {margin: '2px 0 2px 0', fontSize: '9px'});
var turbSevSlider = ui.Slider({
  min: 1.5, max: 3.0, value: 2.0, step: 0.1,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.turbidityRatioSevere = value;
    turbSevLabel.setValue('Turbidity Ratio (Sev): ' + value.toFixed(2));
    updateDetection();
  }
});

// Iron in Water Index Moderate
var ironWaterModLabel = ui.Label('Iron Water Index (Mod): 0.15', {margin: '2px 0 2px 0', fontSize: '9px'});
var ironWaterModSlider = ui.Slider({
  min: 0.05, max: 0.50, value: 0.15, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.ironWaterIndexModerate = value;
    ironWaterModLabel.setValue('Iron Water Index (Mod): ' + value.toFixed(2));
    updateDetection();
  }
});

// Yellow Index Moderate
var yellowModLabel = ui.Label('Yellow Index (Mod): 1.10', {margin: '2px 0 2px 0', fontSize: '9px'});
var yellowModSlider = ui.Slider({
  min: 1.0, max: 1.5, value: 1.10, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.yellowIndexModerate = value;
    yellowModLabel.setValue('Yellow Index (Mod): ' + value.toFixed(2));
    updateDetection();
  }
});

// Shallow Water Depth Threshold
var depthLabel = ui.Label('Shallow Water Cutoff: 1.30', {margin: '2px 0 2px 0', fontSize: '9px'});
var depthSlider = ui.Slider({
  min: 1.0, max: 2.0, value: 1.3, step: 0.05,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.shallowWaterThreshold = value;
    depthLabel.setValue('Shallow Water Cutoff: ' + value.toFixed(2));
    updateDetection();
  }
});

// Contamination Score Thresholds
var scoreModLabel = ui.Label('Score Mod Threshold: 3', {margin: '2px 0 2px 0', fontSize: '9px'});
var scoreModSlider = ui.Slider({
  min: 2, max: 5, value: 3, step: 1,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.scoreThresholdModerate = value;
    scoreModLabel.setValue('Score Mod Threshold: ' + value.toFixed(0));
    updateDetection();
  }
});

var scoreSevLabel = ui.Label('Score Sev Threshold: 5', {margin: '2px 0 2px 0', fontSize: '9px'});
var scoreSevSlider = ui.Slider({
  min: 4, max: 7, value: 5, step: 1,
  style: {stretch: 'horizontal'},
  onChange: function(value) {
    settings.scoreThresholdSevere = value;
    scoreSevLabel.setValue('Score Sev Threshold: ' + value.toFixed(0));
    updateDetection();
  }
});

// ═══════════════════════════════════════════════════════════════════════

// Reset button
var resetButton = ui.Button({
  label: 'Reset Defaults',
  style: {stretch: 'horizontal', margin: '8px 0 6px 0', fontSize: '10px'},
  onClick: function() {
    // Land AMD defaults
    ironSlider.setValue(0.10);
    ferric1Slider.setValue(1.4);
    claySlider.setValue(0.12);
    waterCheckbox.setValue(true);
    waterSlider.setValue(0.3);
    
    // Cloud masking defaults
    cloudProbSlider.setValue(20);
    csSlider.setValue(0.60);
    csCdfSlider.setValue(0.60);
    CLOUD_THRESHOLDS.CLOUD_PROB = 20;
    CLOUD_THRESHOLDS.CS_THRESHOLD = 0.60;
    CLOUD_THRESHOLDS.CS_CDF_THRESHOLD = 0.60;
    
    // Water quality defaults
    waterQualityCheckbox.setValue(true);
    nirModSlider.setValue(0.03);
    nirSevSlider.setValue(0.08);
    turbModSlider.setValue(1.3);
    turbSevSlider.setValue(2.0);
    ironWaterModSlider.setValue(0.15);
    yellowModSlider.setValue(1.10);
    depthSlider.setValue(1.3);
    scoreModSlider.setValue(3);
    scoreSevSlider.setValue(5);
    
    print('✅ All thresholds reset to defaults');
  }
});

// Accuracy tools button
var accuracyButton = ui.Button({
  label: 'Toggle Accuracy Tools',
  style: {stretch: 'horizontal', margin: '0 0 6px 0', fontSize: '9px'},
  onClick: function() {
    settings.showAccuracyTools = !settings.showAccuracyTools;
    updateDetection();
  }
});


// Statistics panel
var statsPanel = ui.Label('Loading...', {
  fontSize: '8px',
  whiteSpace: 'pre-wrap',
  padding: '6px',
  margin: '8px 0',
  border: '1px solid #ddd',
  backgroundColor: '#f9f9f9',
  maxHeight: '150px'
});

// Instructions
var instructions = ui.Label(
  'Iron Sulfate Index (2/1-5/4):\n' +
  '  >0.10 = jarosite likely (provisional)\n' +
  '  >0.30 = high confidence\n\n' +
  'Cloud Masking (S2 only):\n' +
  '  Hybrid = Best (all methods)\n' +
  '  Strict = More aggressive\n\n' +
  'Sensor/date changes auto-reload.\n' +
  'Check console for details.',
  {fontSize: '8px', whiteSpace: 'pre', color: '#555', margin: '6px 0'}
);

// Add all controls to scrollable panel
scrollPanel.add(title);
scrollPanel.add(subtitle);
scrollPanel.add(sensorLabel);
scrollPanel.add(sensorSelect);
scrollPanel.add(cloudMaskLabel);
scrollPanel.add(cloudMaskSelect);
scrollPanel.add(cloudMaskHelp);
scrollPanel.add(compositingLabel);
scrollPanel.add(compositingSelect);
scrollPanel.add(compositingHelp);
scrollPanel.add(seasonLabel);
scrollPanel.add(seasonSelect);
scrollPanel.add(seasonHelp);
scrollPanel.add(dateRangeLabel);
scrollPanel.add(startDateBox);
scrollPanel.add(endDateBox);
scrollPanel.add(applyDatesButton);
scrollPanel.add(clearDatesButton);
scrollPanel.add(regionLabel);
scrollPanel.add(regionSelect);
scrollPanel.add(ironLabel);
scrollPanel.add(ironSlider);
scrollPanel.add(ferric1Label);
scrollPanel.add(ferric1Slider);
scrollPanel.add(clayLabel);
scrollPanel.add(claySlider);
scrollPanel.add(cloudThresholdHeader);
scrollPanel.add(cloudThresholdHelp);
scrollPanel.add(cloudProbLabel);
scrollPanel.add(cloudProbSlider);
scrollPanel.add(csLabel);
scrollPanel.add(csSlider);
scrollPanel.add(csCdfLabel);
scrollPanel.add(csCdfSlider);
scrollPanel.add(cloudPresetLabel);
scrollPanel.add(cloudPresetPanel);
scrollPanel.add(waterCheckbox);
scrollPanel.add(waterLabel);
scrollPanel.add(waterSlider);
scrollPanel.add(advancedHeader);
scrollPanel.add(advancedHelp);
scrollPanel.add(adaptiveCheckbox);
scrollPanel.add(adaptiveMultPanel);
scrollPanel.add(clippingCheckbox);
scrollPanel.add(clippingHelp);
scrollPanel.add(waterQualityHeader);
scrollPanel.add(waterQualityHelp);
scrollPanel.add(waterQualityCheckbox);
scrollPanel.add(nirModLabel);
scrollPanel.add(nirModSlider);
scrollPanel.add(nirSevLabel);
scrollPanel.add(nirSevSlider);
scrollPanel.add(turbModLabel);
scrollPanel.add(turbModSlider);
scrollPanel.add(turbSevLabel);
scrollPanel.add(turbSevSlider);
scrollPanel.add(ironWaterModLabel);
scrollPanel.add(ironWaterModSlider);
scrollPanel.add(yellowModLabel);
scrollPanel.add(yellowModSlider);
scrollPanel.add(depthLabel);
scrollPanel.add(depthSlider);
scrollPanel.add(scoreModLabel);
scrollPanel.add(scoreModSlider);
scrollPanel.add(scoreSevLabel);
scrollPanel.add(scoreSevSlider);
scrollPanel.add(resetButton);
scrollPanel.add(accuracyButton);
scrollPanel.add(statsPanel);
scrollPanel.add(instructions);

// Add scrollable panel to main panel, then add to map
panel.add(scrollPanel);
Map.add(panel);

// =============================================================================
// LEGEND
// =============================================================================

// Create the legend panel
var legend = ui.Panel({
  style: {
    position: 'bottom-left',
    padding: '8px 15px',
    backgroundColor: 'white',
    border: '1px solid #ddd'
  }
});

// Add legend title
var legendTitle = ui.Label({
  value: 'AMD Classification (19 Classes)',
  style: {
    fontWeight: 'bold',
    fontSize: '12px',
    margin: '0 0 4px 0',
    padding: '0'
  }
});

// Add the title to the panel
legend.add(legendTitle);

// Create and add the legend content
var legendContent = ui.Panel({
  style: {
    padding: '0',
    margin: '0',
    maxHeight: '300px',
    fontSize: '10px'
  }
});

// AMD Indicator Classes (High Priority)
var amdClasses = [
  {color: 'FFB6C1', label: '14: Oxidizing Sulfides'},
  {color: 'FF0000', label: '12: Major Iron Sulfate'},
  {color: 'DC143C', label: '17: Proximal Jarosite'},
  {color: '8B0000', label: '18: Distal Jarosite'},
  {color: 'FF1493', label: '9: Argillic Alteration'},
  {color: 'C71585', label: '19: Clay+Ferrous+Iron'}
];

// Other Mineral Classes
var otherClasses = [
  {color: 'FF6347', label: '8: Clay+Major Ferric'},
  {color: 'FFA500', label: '7: Clay+Mod Ferric'},
  {color: 'FFFF00', label: '6: Clay+Minor Ferric'},
  {color: '00FF00', label: '5: Clay-Sulfate-Mica'},
  {color: '008B8B', label: '10: Clay+Ferrous'},
  {color: 'FF00FF', label: '2: Major Ferric Iron'},
  {color: 'A0522D', label: '1: Minor Ferric (Hematite)'},
  {color: '800080', label: '3: Ferric+-Ferrous'},
  {color: '00CED1', label: '4: Ferrous (Chlorite)'},
  {color: '228B22', label: '11: Dense Vegetation'},
  {color: '9ACD32', label: '13: Sparse Veg+Ferric'}
];

// Water Classes REMOVED - now handled by separate Water Quality module
// See 🌊 Water Quality Classification layer instead
// (Blue = Clean, Orange = Moderate, Red = Severe)
var waterClasses = [];

// Function to create a single legend item
function createLegendItem(color, label) {
  var colorBox = ui.Label({
    style: {
      backgroundColor: '#' + color,
      padding: '8px',
      margin: '0 0 4px 0'
    }
  });
  
  var description = ui.Label({
    value: label,
    style: {margin: '0 0 4px 8px'}
  });
  
  return ui.Panel({
    widgets: [colorBox, description],
    layout: ui.Panel.Layout.Flow('horizontal')
  });
}

// Add AMD classes to legend
var amdHeader = ui.Label({
  value: 'AMD Indicator Classes:',
  style: {fontWeight: 'bold', margin: '8px 0 4px 0'}
});
legendContent.add(amdHeader);

// Add AMD classes in a grid
var amdGrid = ui.Panel({
  layout: ui.Panel.Layout.Flow('horizontal'),
  style: {stretch: 'horizontal'}
});

// Split into two columns
var col1 = ui.Panel({
  layout: ui.Panel.Layout.Flow('vertical'),
  style: {width: '50%'}
});

var col2 = ui.Panel({
  layout: ui.Panel.Layout.Flow('vertical'),
  style: {width: '50%'}
});

// Add first half to col1, second half to col2
for (var i = 0; i < amdClasses.length; i++) {
  var item = createLegendItem(amdClasses[i].color, amdClasses[i].label);
  if (i < Math.ceil(amdClasses.length / 2)) {
    col1.add(item);
  } else {
    col2.add(item);
  }
}

amdGrid.add(col1);
amdGrid.add(col2);
legendContent.add(amdGrid);

// Add other classes header
var otherHeader = ui.Label({
  value: 'Other Mineral Classes:',
  style: {fontWeight: 'bold', margin: '8px 0 4px 0'}
});
legendContent.add(otherHeader);

// Add other classes in a grid
var otherGrid = ui.Panel({
  layout: ui.Panel.Layout.Flow('horizontal'),
  style: {stretch: 'horizontal'}
});

// Split into two columns
var col3 = ui.Panel({
  layout: ui.Panel.Layout.Flow('vertical'),
  style: {width: '50%'}
});

var col4 = ui.Panel({
  layout: ui.Panel.Layout.Flow('vertical'),
  style: {width: '50%'}
});

// Add first half to col3, second half to col4
for (var j = 0; j < otherClasses.length; j++) {
  var item = createLegendItem(otherClasses[j].color, otherClasses[j].label);
  if (j < Math.ceil(otherClasses.length / 2)) {
    col3.add(item);
  } else {
    col4.add(item);
  }
}

otherGrid.add(col3);
otherGrid.add(col4);
legendContent.add(otherGrid);

// Water classes removed - see Water Quality Classification layer instead
var waterNote = ui.Label({
  value: '💡 Water contamination: See 🌊 Water Quality Classification layer',
  style: {fontStyle: 'italic', margin: '8px 0 4px 0', fontSize: '10px', color: '666'}
});
legendContent.add(waterNote);

// Add legend content to legend panel
legend.add(legendContent);

// Add legend to map
Map.add(legend);

// =============================================================================
// INITIALIZATION
// =============================================================================

// Main update function
function updateEverything() {
  // Show loading message
  print('Loading ' + settings.currentSensor + ' data for ' + settings.currentAreaName + '...');
  
  // Update composite and detection
  var composite = updateComposite();
  var classification = updateDetection();
  
  // Calculate and display statistics
  var stats = calculateStats();
  
  
  print('Done! Use the controls to adjust thresholds and click on the map for pixel values.');
  
  // Print paper reference
  print('\nREFERENCE: Rockwell, B. W., McDougal, R. R., & Gent, C. A. (2021). ' +
        'Improved automated identification and mapping of iron sulfate minerals, ' +
        'other mineral groups, and vegetation using Landsat 8 Operational Land ' +
        'Imager data, San Juan Mountains, Colorado, and Four Corners Region. ' +
        'U.S. Geological Survey Scientific Investigations Map 3466.');
}

// Print welcome message
print('═══════════════════════════════════════════════════════════════');
print('Acid Mine Drainage Detection System ' + TOOL_VERSION);
print('Advanced Remote Sensing for Environmental Monitoring');
print('═══════════════════════════════════════════════════════════════');
print('Author: Abdulrahman Hussein | Kent State University');
print('Website: www.climtawy.com | ORCID: 0009-0003-0401-9219 | License: MIT');
print('═══════════════════════════════════════════════════════════════');
print('Initializing...');

// Run initial update
updateEverything();

// =============================================================================
// EXPORT FUNCTIONS (For reference, not used in UI by default)
// =============================================================================

function exportClassification() {
  if (!settings.currentComposite) return;
  
  var classification = createBooleanClassification();
  var region = settings.currentRegion;
  var name = 'AMD_Classification_' + settings.currentSensor.replace(/\s+/g, '') + 
             '_' + settings.currentAreaName.replace(/[^a-zA-Z0-9]/g, '_') + 
             '_' + ee.Date(Date.now()).format('yyyyMMdd').getInfo();
  
  Export.image.toDrive({
    image: classification,
    description: name,
    scale: 30,
    region: region,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF',
    formatOptions: {
      cloudOptimized: true
    },
    folder: 'GEE_Exports',
    fileNamePrefix: name
  });
  
  print('Export started: ' + name);
}

function exportIndices() {
  if (!settings.currentComposite) return;
  
  var region = settings.currentRegion;
  var name = 'AMD_Indices_' + settings.currentSensor.replace(/\s+/g, '') + 
             '_' + settings.currentAreaName.replace(/[^a-zA-Z0-9]/g, '_') + 
             '_' + ee.Date(Date.now()).format('yyyyMMdd').getInfo();
  
  // Select only the index bands for export
  var indices = settings.currentComposite.select([
    'IronSulfate', 'FerricIron1', 'FerricIron2', 'FerrousIron',
    'ClaySulfateMica', 'NDVI', 'MNDWI', 'AWEINSH', 'NDBI'
  ]);
  
  Export.image.toDrive({
    image: indices,
    description: name,
    scale: 30,
    region: region,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF',
    formatOptions: {
      cloudOptimized: true
    },
    folder: 'GEE_Exports',
    fileNamePrefix: name
  });
  
  print('Export started: ' + name);
}

// v2.0.1: Export a per-pixel CSV for the VPCA spectral-library validator
// (python/vpca_validation.py). Produces one row per sampled pixel with the 7
// surface-reflectance bands the validator expects, the classifier's land class
// and water-quality class, and lon/lat - exactly the columns documented in
// specs/amd-v2/validation-protocol.md.
function exportForVPCA() {
  if (!settings.currentComposite) { print('No composite loaded.'); return; }

  // 7 SR bands (validator input), renamed exactly as the CSV expects.
  var bands = settings.currentComposite.select(
    ['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7']);

  // Classifier outputs, unmasked to sentinels so every pixel gets a label:
  //   class      : 0 = not land-AMD, 1..19 = land mineral class
  //   water_class: -1 = not water, 0 = clean, 1 = moderate, 2 = severe
  var landClass = createBooleanClassification().unmask(0).rename('class');
  var wq = createWaterQualityClassification();
  var waterClass = (wq && wq.classification)
    ? wq.classification.unmask(-1).rename('water_class')
    : ee.Image(-1).rename('water_class');

  var stack = bands.addBands(landClass).addBands(waterClass);

  // Native scale per sensor so we sample real (not resampled) pixels.
  var scale = (settings.currentSensor === 'Sentinel-2') ? 20 : 30;

  // Sample the region. geometries:true keeps coordinates so we can attach
  // lon/lat. Cap the pixel count so the CSV stays small and VPCA runs fast.
  var samples = stack.sample({
    region: settings.currentRegion,
    scale: scale,
    numPixels: 20000,
    seed: 42,
    geometries: true,
    dropNulls: true
  }).map(function(f) {
    var c = f.geometry().coordinates();
    return f.set('lon', c.get(0), 'lat', c.get(1));
  });

  var name = 'VPCA_' + settings.currentSensor.replace(/\s+/g, '') + '_' +
    settings.currentAreaName.replace(/[^a-zA-Z0-9]/g, '_') + '_' +
    ee.Date(Date.now()).format('yyyyMMdd').getInfo();

  Export.table.toDrive({
    collection: samples,
    description: name,
    fileFormat: 'CSV',
    folder: 'GEE_Exports',
    fileNamePrefix: name,
    selectors: ['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7',
                'class','water_class','lon','lat']
  });

  print('VPCA export queued: ' + name +
        '  -> run in Tasks tab, then: python vpca_validation.py --scene ' +
        name + '.csv --sensor ' +
        (settings.currentSensor === 'Sentinel-2' ? 'S2' : 'L8'));
}

// Add export buttons to the UI
var exportPanel = ui.Panel({
  widgets: [
    ui.Button('Export Classification', exportClassification, false, {stretch: 'horizontal'}),
    ui.Button('Export Indices', exportIndices, false, {stretch: 'horizontal'}),
    ui.Button('Export VPCA CSV', exportForVPCA, false, {stretch: 'horizontal'})
  ],
  layout: ui.Panel.Layout.Flow('vertical'),
  style: {position: 'top-right', margin: '10px 10px 0 0', width: '200px'}
});

// v2.0.1: export panel enabled so the VPCA CSV can be produced from the UI.
Map.add(exportPanel);

// =============================================================================
// END OF SCRIPT
// =============================================================================
