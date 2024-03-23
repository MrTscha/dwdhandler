# dwdhandler
Handles DWD data which is derived from https://opendata.dwd.de/

Station data is stored in a SQLite database.

Raster data is momentarily stored as ASCII. 
Storing as netCDF is planned.

## Examples

Find some examples in the examples subdirectory.

## Some remarks

The package ```pyproj``` is used in some functions, but is not needed.
If desired install the package ```pyproj```.

This mainly concerns the raster data functions, not the download of raster data. 