# QGisLinearReference #

QGis-Python-Plugin for linear referenced data
- "PoL" => "Point-on-Line" 
- "LoL" => "Line-on-Line"

Original purpose:
"events" along rivers, e.g. buildings along a river (PoL) or care measures on the riverbanks (LoL).

## Uses three types of layers for PoL/LoL: ##

### "data-layer" ###
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
  
### "reference-layer" ###
- vector-layer (GeoPackage, PostGIS, Shape...)
- type linestring/linestringM/linestringZ/linestringMZ... (M-values not taken into account)
  - hint: Shape-files don't differentiate single- and multipart-geometries, therefore also the linestring-xx-multi-versions are possible, but not tested and results not predictable 
- unique-ID-field (type integer or string, usually the primary-key) for join the data-layer

### "show-layer" ###
- virtual layer or imported database-view
- calculate the point/segment-geometries 
  - database f.e. PostGIS-view:
    - recommended in case of requirements respecting
      - performance (QGis-virtual-layer tend to be slow) 
      - security (constraints/foreign keys/transactions/user-privileges/backups...)
      - possibilities (multi-user, Network-Access)
      - and... and...
    - hint: the database should contain both layers to join them in a view and get the security benefits mentioned above, else joins to remote databases must be implemented
  - virtual:
    - QGis-internal solution that combines data- and reference-layer and calculates the PoL/LoL-Features with expressions "ST_Line_Interpolate_Point(...)" or "ST_Line_Substring(...)" 
    - data/reference-layer can come from totally different sources (f.e. join Excel-Table with Shape-File)
    - if created by plugin: initially contain only the minimal necessary fields (ID, reference-ID, measures, offset), all other fields from data- and reference-layer are joined

Samples:

PoL:
``` SQL
SELECT data_lyr.fid as "fid",
 data_lyr.line_ref_id as "line_ref_id",
 data_lyr.measure as "measure",
 ST_Line_Interpolate_Point(ref_lyr.geometry, data_lyr."measure"/st_length(ref_lyr.geometry)) as point_geom
FROM  "data_lyr_xyz" as data_lyr
  INNER JOIN "ref_lyr_xyz" as ref_lyr ON data_lyr."line_ref_id" = ref_lyr."gew_id"
```

LoL:
``` SQL
SELECT data_lyr.upabs_id as "upabs_id",
 data_lyr.line_ref_id as "line_ref_id",
 data_lyr.measure_from as "measure_from",
 data_lyr.measure_to as "measure_to",
 data_lyr.offset as "offset",
 CASE WHEN data_lyr."offset" is null or data_lyr."offset" = 0 THEN ST_Line_Substring(ref_lyr.geometry, min(data_lyr."measure_from",data_lyr."measure_to")/st_length(ref_lyr.geometry),max(data_lyr."measure_from",data_lyr."measure_to")/st_length(ref_lyr.geometry)) ELSE ST_OffsetCurve(ST_Line_Substring(ref_lyr.geometry, min(data_lyr."measure_from",data_lyr."measure_to")/st_length(ref_lyr.geometry),max(data_lyr."measure_from",data_lyr."measure_to")/st_length(ref_lyr.geometry)),data_lyr."offset") END as line_geom /*:linestring:25832*/
FROM  "data_lyr_xyz" as data_lyr
  INNER JOIN "ref_lyr_xyz" as ref_lyr ON data_lyr."line_ref_id" = ref_lyr."gew_id"
```
hint: the expression for LoL-features looks a bit tricky, but the "CASE WHEN"-part was necessary because of a "bug" (?) in QGis (under windows only...), 
which refused to calculate geometries for offset value 0.
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
- the Plugin was developed in 2023 with the newest available QGis-version:
  - 3.30 "s'Hertogenbosch"
  - Windows (11)
  - Linux (Mint 21.1 "Vera")
- not tested with older/LTR-versions
- not tested on QGis for macOS
- please report bugs or ideas for missing features 
- or translation-errors :-)


## More Instructions: ##
[docs/index.html](./docs/index.html)


## Contribute ##
- Issue Tracker: https://github.com/Ludwig-K/QGisLinearReference/issues
- Source Code: https://github.com/Ludwig-K/QGisLinearReference

## Support ##
If you are having issues, please let me know.
You can directly contact me via ludwig@kni-online.de

## License ##
The project is licensed under the GNU GPL 2 license.