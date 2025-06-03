// Example script to load and visualize ERA5 climate reanalysis parameters in
// Google Earth Engine

var studyArea = ee.FeatureCollection('projects/git712-gds/assets/Extent'); // Replace with your asset ID

// Load ERA5 daily mean 2m air temperature for July 2019
var era5_2mt = ee.ImageCollection('ECMWF/ERA5/DAILY')
                   .select('mean_2m_air_temperature')
                   .filterDate('2016-01-01', '2019-01-31')
                   .filterBounds(studyArea);

// Compute mean temperature over the month
var meanTemp = era5_2mt.mean().clip(studyArea);

// Visualization parameters
var vis2mt = {
  min: 250,
  max: 320,
  palette: [
    '000080', '0000d9', '4000ff', '8000ff', '0080ff', '00ffff', '00ff80',
    '80ff00', 'daff00', 'ffff00', 'fff500', 'ffda00', 'ffb000', 'ffa400',
    'ff4f00', 'ff2500', 'ff0a00', 'ff00ff'
  ]
};

// Center map and add clipped temperature layer
Map.centerObject(studyArea, 10);
Map.addLayer(meanTemp, vis2mt, 'Mean 2m Temp (July 2019)');

// Export the mean temperature image to Google Drive
Export.image.toDrive({
  image: meanTemp,
  description: 'Mean_2m_Temp_July2019_Jonkershoek',
  folder: 'GEE_exports',
  fileNamePrefix: 'mean_2m_temp_july2019_jonkershoek',
  region: studyArea.geometry(),
  scale: 1000, // ERA5 native resolution is ~31km, but 1000m gives decent granularity
  crs: 'EPSG:4326',
  maxPixels: 1e13
});