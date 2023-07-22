#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* some Tool-Functions

.. note::
    import to console from Path (LinearReferencing-plugin-folder in current QGis-Profile-Folder)

    or use:

    ``import LinearReferencing.MyToolFunctions``

    or use (f.e.):

    ``from LinearReferencing.MyToolFunctions import get_linestring_layers``

********************************************************************

* Date                 : 2023-02-12
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""
from __future__ import annotations
from PyQt5 import QtCore
import qgis
from qgis import core


def qt_format(in_string,*args):
    """special for QtCore.QCoreApplication.translate in dialogs, tooltips...
    Some richtext-markups are supported:
    https://doc.qt.io/qtforpython-5/overviews/richtext-html-subset.html#supported-html-subset
    but special-chars and formatting tags are often difficult to translate, because they appear in escaped form inside the pylupdate5-created ts-file
    this function uses special wildcards to avoid these problems
    inside the translate-strings they have to be embedded with {curly} braces
    :param in_string: input
    :param *args: optional "normal" format-parameters, which replace numerical wildcards {0} {1}... by their index
    """
    # Rev. 2023-07-03
    qt_wildcards = {
        'apos': "'",
        'nbsp': "&nbsp;",
        'arrow': "➜",
        'br': "<br />",
        'hr': "<hr />",
        'b1': "<b>",
        'b2': "</b>",
        'lt': "&lt;",
        'gt': "&gt;",
        'ul_1': "<ul style='margin: 0 0 0 0;'>",
        'ul_2': "</ul>",
        'li_1': "<li>",
        'li_2': "</li>",
        #avoids implicit word-wrap in tooltips:
        'div_pre_1': "<div style='white-space:nowrap; margin: 0 0 0 0;'>",
        'div_pre_2': "</div>",
        'div_ml_1': "<div style='margin: 0 0 0 10;'>",
        'div_ml_2': "</div>",
    }
    # ** => spreads the dictionary to name=value pairs
    return in_string.format(*args,**qt_wildcards)

def select_by_value(wdg_with_model,select_value,col_idx = 0,role_idx = 0):
    """helper-function that selects an item in a QComboBox by its value, blocks any signals
    :param wdg_with_model: Widget wit a model, f.e. QComboBox
    :param select_value: the compare-value
    :param col_idx: the index of the column of the data-model, whose data will be compared, always 0 with QComboBox
    :param role_idx: the role in the items, whose data will be compared, see https://doc.qt.io/qt-5/qt.html#ItemDataRole-enum
    0 ➜ DisplayRole (Text of the option)
    256 ➜ UserRole (Data of the option)
    """
    first_item_idx = wdg_with_model.model().index(0, col_idx)
    # param 4 "-1": limits num of matches, here -1 ➜ no  limit, return all matches
    matching_items = wdg_with_model.model().match(first_item_idx, role_idx, select_value, -1, QtCore.Qt.MatchExactly)
    if matching_items:
        first_matching_item = matching_items.pop(0)
        with QtCore.QSignalBlocker(wdg_with_model):
            wdg_with_model.setCurrentIndex(first_matching_item.row())




def get_segment_geom(line_geometry:qgis.core.QgsGeometry, measure_from:float,measure_to:float, offset:float = 0)->qgis.core.QgsGeometry:
    """calculate line-segment measure_from...measure_to on line_geometry with optional offset"""
    is_single = qgis.core.QgsWkbTypes.isSingleType(line_geometry.wkbType())

    if is_single:
        ls = line_geometry.constGet()
    else:
        #experimental... implemented for shape-file-based refLyr
        ls = line_geometry.constGet().geometryN(0)

    m_from = min(measure_from, measure_to)
    m_to = max(measure_from, measure_to)
    segment_geom = qgis.core.QgsGeometry(ls.curveSubstring(m_from, m_to))

    if segment_geom:
        if offset:
            # Bug on QGis in Windows: no Geometry with Offset 0
            # distance – buffer distance
            # segments – for round joins, number of segments to approximate quarter-circle
            # joinStyle – join style for corners in geometry
            # miterLimit – limit on the miter ratio used for very sharp corners (JoinStyleMiter only)
            segment_geom = segment_geom.offsetCurve(offset, 8, qgis.core.Qgis.JoinStyle.Round, 0)

        return segment_geom


def get_feature_by_value(vlayer: qgis.core.QgsVectorLayer, field: qgis.core.QgsField, value: str | int) -> qgis.core.QgsFeature|None:
    """Returns first feature from layer by query on a single value,
    intended for use on PK-field and PK-Value, where only one feature is expected
    sample:
    found_feature = get_feature_by_value(iface.activeLayer(),iface.activeLayer().fields()[0],1)
    """
    request = qgis.core.QgsFeatureRequest()
    # expression independent of type of field and value
    request.setFilterExpression(f'"{field.name()}" = \'{value}\'')
    queried_features = vlayer.getFeatures(request)

    # return the first feature
    for feature in queried_features:
        return feature





def get_unique_layer_name(layer_names: list, layer_name_template: str, first_i: str = '') -> str:
    """get unique Layername replacing Wildcard {curr_i} with inkremented integer
    :param layer_names: Liste of the current layernames  f. e. via [layer.name() for layer in  qgis.core.QgsProject.instance().mapLayers().values()]
    :param layer_name_template: template with Wildcard {curr_i}
    :param first_i: optional replacement for fist run
    """
    if not '{curr_i}' in layer_name_template:
        layer_name_template = layer_name_template + '{curr_i}'

    layer_name = layer_name_template.format(curr_i=first_i)

    i = 1
    while layer_name in layer_names:
        layer_name = layer_name_template.format(curr_i=i)
        i += 1

    return layer_name


def get_data_layers() -> dict:
    """return dictionary of all loaded non-geometry-layers

    .. note:: Import to console via
    ``from LinearReferencing.MyToolFunctions import get_data_layers``

    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """
    ld = {}
    no_geometry_wkb_types = [
        qgis.core.QgsWkbTypes.NoGeometry
    ]
    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in no_geometry_wkb_types:
            ld[cl.id()] = cl
    return ld


def get_linestring_layers()->dict:
    """
    return dict of all linestring-type-layers in current project.

    .. note:: Import to console via
    ``from LinearReferencing.MyToolFunctions import get_linestring_layers``

    """
    ld = {}
    linestring_wkb_types = [
        qgis.core.QgsWkbTypes.LineString25D,
        qgis.core.QgsWkbTypes.MultiLineString25D,
        qgis.core.QgsWkbTypes.LineString,
        qgis.core.QgsWkbTypes.MultiLineString,
        qgis.core.QgsWkbTypes.LineStringZ,
        qgis.core.QgsWkbTypes.MultiLineStringZ,
        qgis.core.QgsWkbTypes.LineStringM,
        qgis.core.QgsWkbTypes.MultiLineStringM,
        qgis.core.QgsWkbTypes.LineStringZM,
        qgis.core.QgsWkbTypes.MultiLineStringZM,
        # problematic: Shape-Format doesn't distinguish between single- and multi-geometry-types
        # unpredictable though, how measures on multi-linestring will be located
    ]
    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        # ➜ https://api.qgis.org/api/classQgsDataProvider.html ➜ memory/virtual/ogr
        #  Skip Virtual-layers: and cl.dataProvider().name() != 'virtual'
        if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in linestring_wkb_types:
            ld[cl.id()] = cl
    return ld


def get_point_show_layers() -> dict:
    """returns a list of potential point-show-layers: VectorLayer, PointGeometry, not editable, not ogr ( ➜ virtual layer or database-view, not file-based)
    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """
    # Rev. 2023-05-22
    ld = {}
    single_point_wkb_types = [
        qgis.core.QgsWkbTypes.Point25D,
        qgis.core.QgsWkbTypes.Point,
        qgis.core.QgsWkbTypes.PointZ,
        qgis.core.QgsWkbTypes.PointM,
        qgis.core.QgsWkbTypes.PointZM,
    ]

    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_point_wkb_types:
            if cl.dataProvider().name() not in ['ogr']:
                caps = cl.dataProvider().capabilities()
                if not (caps & qgis.core.QgsVectorDataProvider.AddFeatures):
                    if not (caps & qgis.core.QgsVectorDataProvider.DeleteFeatures):
                        if not (caps & qgis.core.QgsVectorDataProvider.ChangeAttributeValues):
                            ld[cl.id()] = cl

    return ld

def get_line_show_layers() -> dict:
    """returns a list of potential point-show-layers: VectorLayer, PointGeometry, not editable, not ogr ( ➜ virtual layer or database-view, not file-based)
    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """
    # Rev. 2023-05-22
    ld = {}
    single_line_wkb_types = [
        qgis.core.QgsWkbTypes.LineString25D,
        qgis.core.QgsWkbTypes.LineString,
        qgis.core.QgsWkbTypes.LineStringZ,
        qgis.core.QgsWkbTypes.LineStringM,
        qgis.core.QgsWkbTypes.LineStringZM,
    ]

    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_line_wkb_types:
            if cl.dataProvider().name() not in ['ogr']:
                caps = cl.dataProvider().capabilities()
                if not (caps & qgis.core.QgsVectorDataProvider.AddFeatures):
                    if not (caps & qgis.core.QgsVectorDataProvider.DeleteFeatures):
                        if not (caps & qgis.core.QgsVectorDataProvider.ChangeAttributeValues):
                            ld[cl.id()] = cl

    return ld


def get_point_layers() -> dict:
    """return dictionary of loaded point-layers

    .. note:: Import to console via
    ``from LinearReferencing.MyToolFunctions import get_point_layers``

    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """
    ld = {}
    single_point_wkb_types = [
        qgis.core.QgsWkbTypes.Point25D,
        qgis.core.QgsWkbTypes.Point,
        qgis.core.QgsWkbTypes.PointZ,
        qgis.core.QgsWkbTypes.PointM,
        qgis.core.QgsWkbTypes.PointZM,
    ]
    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_point_wkb_types:
            ld[cl.id()] = cl
    return ld


class OneLayerFilter(qgis.core.QgsPointLocator.MatchFilter):
    """Filter for Snapping: snap only features of a certain layer"""

    def __init__(self, layer):
        qgis.core.QgsPointLocator.MatchFilter.__init__(self)
        self.layer = layer

    def acceptMatch(self, m):
        return m.layer() == self.layer


class OneFeatureFilter(qgis.core.QgsPointLocator.MatchFilter):
    """Filter for Snapping: snap only on one feature of a certain layer"""

    def __init__(self, layer, fid):
        qgis.core.QgsPointLocator.MatchFilter.__init__(self)
        self.layer = layer
        self.fid = fid

    def acceptMatch(self, m):
        return m.layer() == self.layer and m.featureId() == self.fid


