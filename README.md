# QGisLinearReference
QGis-Python-Plugin for linear referenced data(point-on-line/line_on_line-Layers)

Enables the user to create a virtual layer with geometries defined by the reference to a line-vector and *one* (point_on_line) or *two* measures (from...to) on that line and an optional offset (line_on_line).

The original purpose were "events" along rivers, e. g. care measures on the riverbanks.

These layers need a reference-layer with geometry type linestring or linestringM (but the M-Value is regrettably not used) and a data-table with at least the fields:
1. both types: field that holds the reference to the line-layer (usually the fid-column of the line-theme), 
2. both types: a float-type column with the measure 1, 
3. line_on_line: a float-type column with the measure for Point 2, 
4. line_on_line: an optional float-column with the parallel offset of the created line-segment from the reference line (positive: left side, negative: right side in the direction of the line-geometry). 

And any number of additional fields in the data-table for the necessary data of the point or the line-segment.

The resulting layers are 'memory layer' which you can export to different vector formats.

You can also manually update the features of an existing data-table with virtual Layer or define a target-data-table via plugin

You can also use the plugin just to visiualize the position of points/line-segments along a line.

This is my first plugin for QGis, so please be patient and report bugs, ideas for missing features or translation-errors. 
