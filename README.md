# QGisLinearReference #

QGis-Python-Plugin for linear referenced data
- "PoL" => "Point-on-Line" 
- "LoL" => "Line-on-Line"

Original purpose:
"events" along rivers, e.g. buildings along a river (PoL) or care measures on the riverbanks (LoL).

## Uses three types of layers for PoL/LoL: ##

### "Data-Layer" ###
- geometry-less "layers" in the current project
- can be created with support of this plugin (GeoPackage)
- or used, if they allready exist as layer in the current project
  - GeoPackage, PostGIS 
  - possible, tested, **not** recommended: Excel, LibreOffice...
- should be editable (insert/update/delete-privileges required, otherwise only viewer-functionality)
- need a 
  - unique-id-field (usually the primary-key)
  - reference-field to join the reference-layer
  - measure-fields (one for PoL, two for LoL, numeric type)
  - for LoL: offset-field (numeric) for the parallel offset of the segments from the referenced line (positive: left side, negative: right side).
  
### "Reference-Layer" ###
- vector-layer (GeoPackage, PostGIS, Shape...)
- type linestring/linestringM/linestringZ/linestringMZ... (M-values not taken into account)
  - hint: Shape-files don't differentiate single- and multipart-geometries, therefore also the linestring-xx-multi-versions are possible, but not tested and results not predictable 
- unique-ID-field (type integer or string, usually the primary-key) for join the data-layer

### "Show-Layer" ###
- virtual layer
- calculate the point/segment-geometries 
- combines data- and reference-layer and calculates the PoL/LoL-Features with expressions "ST_Line_Interpolate_Point(...)" or "ST_Line_Substring(...)" 
- data/reference-layer can come from totally different sources (f.e. join Excel-Table with Shape-File)
- plugin-created with the minimal necessary fields (ID, reference-ID, measures, offset), all other fields from data- and reference-layer are joined

## The plugin can be used in different ways: ##
### Measure ###
- Just show measures for the current cursor-Position on the appropriate feature of the "reference-layer" 
- "Mouse-Press" to set temporary markers ("point-on-line" => one green marker, one measure, "line-on-line" two markers green/red, two measures)
### Create layer ###
- create data-layer for storing features with the relevant reference data (measure, measure-from, measure-to, offset, reference-id)
- create virtual show-layer to show/style/export the features
### data maintenance ###
- import external sources to QGis-project
- show, create, update, delete features
- access plugin-functionality from dialog and/or feature-tables and -forms (the plugin places two "actions" to feature-tables and attribute-forms of data-and show-layer for Zoom/Pan/Edit)

## Addendum ##
- The plugin has been developed under the latest versions since 2023, currently
  - QGIS 3.38.4 'Grenoble'
  - QGIS 3.34.10 'Prizren' (LTR)
  - Windows (10 + 11)
  - Linux (Ubuntu/Mint 21.2)
- not tested (but should run) with older QGis-3-Versions
- not tested on macOS
- please report bugs or ideas for missing features 
- or translation-errors :-)
- or support the plugin-usability for the community with pylupdate5/lsrelease-translations to other languages then english/german


## More Instructions: ##
[docs/index.html](https://htmlpreview.github.io/?https://github.com/Ludwig-K/QGisLinearReference/blob/main/docs/index.html)


## Contribute ##
- Issue Tracker: https://github.com/Ludwig-K/QGisLinearReference/issues
- Source Code: https://github.com/Ludwig-K/QGisLinearReference

## Support ##
If you are having issues, please let me know.
You can directly contact me via ludwig[at]kni-online.de

## License ##
The project is licensed under the GNU GPL 2 license.