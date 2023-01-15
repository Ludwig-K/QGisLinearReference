# QGisLinearReference
QGis-Python-Plugin for linear referenced data(point-on-line/line_on_line-Layers)

Enables the user to create a virtual layer with geometries defined by the reference to a line-vector and *one* (point_on_line) or *two* measures (from...to) on that line and an optional offset (line_on_line).

The original purpose were "events" along rivers, e. g. care measures on the riverbanks.

These layers need a reference-layer with geometry type linestring or linestringM (but the M-Value is regrettably not used) and a table with a field, that holds the reference to the line-layer (usually the fid-column of the line-theme), a float-type column with the from-measure, a float-type column with the to-measure, an optional float-column with the parallel offset of the created line-segment from the refeerence line (positive: left side, negative: right side in the direction of the line-geometry). And any number of additional fields for the attribute-data of the point or the line-segment.

You can also use the plugin just to visiualize the position of points/line-segments along a line.

This is my first plugin for QGis, so please be patient and report bugs, ideas for missing features or translation-errors. 
