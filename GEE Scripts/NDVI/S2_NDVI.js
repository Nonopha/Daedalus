// This script creates a composite NDVI image from Sentinel-2 data
// Example code used to modify, clip & export
// Comments included are from the original code

var studyArea = ee.FeatureCollection('projects/git712-gds/assets/Extent');

// Function to mask clouds using the Sentinel-2 QA band.
function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
              .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  return image.updateMask(mask).divide(10000)
              .select(["B.*"])
              .copyProperties(image, ["system:time_start"]);
}

// Load and filter Sentinel-2 collection
var collection = ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterDate('2016-01-01', '2016-12-31') // Adjust how you want to filter the dates
    .filterBounds(studyArea)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    .map(maskS2clouds);

// Compute NDVI and mean
var withNDVI = collection.map(function(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
  return image.addBands(ndvi);
});

var meanNDVI = withNDVI.select('NDVI').mean()
                .clip(studyArea);  // Clip to study area

// Display result
Map.centerObject(studyArea, 11);
Map.addLayer(meanNDVI, {min: 0, max: 1, palette: ['brown', 'yellow', 'green']}, 'Mean NDVI');

// Export to Google Drive
Export.image.toDrive({
  image: meanNDVI,
  description: 'Mean_NDVI_2016_Jonkershoek', //Remember to change the description
  folder: 'GEE_exports',
  fileNamePrefix: 'mean_ndvi_2016_jonkershoek', // Change the file name prefix as needed
  region: studyArea.geometry(),
  scale: 10,
  crs: 'EPSG:4326',
  maxPixels: 1e13
});