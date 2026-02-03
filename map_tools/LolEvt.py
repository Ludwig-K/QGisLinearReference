#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* MapTool for digitizing Line-Events in MapCanvas

********************************************************************

* Date                 : 2024-06-15
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
import math
import os
import numbers
import urllib


from PyQt5.QtCore import Qt, QSignalBlocker, QMetaType, QTimer, QLocale

from PyQt5.QtGui import (
    QIcon,
    QFont,
    QColor,
    QCursor,
    QStandardItemModel,
)

from PyQt5.QtWidgets import QAction, QActionGroup, QLabel

from LinearReferencing.tools.LinearReferencedGeometry import LinestringStatistics

from LinearReferencing.settings.exceptions import *

from PyQt5.QtWidgets import QMessageBox, QToolButton, QDockWidget

from typing import Any


from LinearReferencing import tools


from LinearReferencing.dialogs import LolDialog, LolCreateDataLayerDialog


from LinearReferencing.tools.LoL import LoL
from LinearReferencing.settings.constants import (
    Qt_Roles,
    QT_INT,
    QT_DOUBLE,
)
from LinearReferencing.map_tools.LrEvt import LrEvt, SVS, PoProFeature


from LinearReferencing.tools.MyDebugFunctions import (
    debug_log,
    debug_print,
    get_debug_pos,
)

from LinearReferencing.qt.MyQtWidgets import (
    MyToolButton,
    MyDeleteToolButton,
    MyStandardItem,
    MyCellWidget,
    MyToolbarSpacer,
    featureFormEventFilter
)

from LinearReferencing.tools.MyTools import (
    check_mods,
    check_attribute_value,
    show_feature_form,
    get_unique_string,
    select_in_layer,
    get_features_by_value,
    list_intersection,
    list_difference,
    sys_get_locale,
    get_field_values,
    get_feature_by_value,
)

from LinearReferencing.i18n.SQLiteDict import SQLiteDict

from qgis.gui import (
    QgisInterface,
    QgsMapMouseEvent,
    QgsAttributeEditorContext,
    QgsVertexMarker,
    QgsRubberBand,
)


from qgis.core import (
    QgsProject,
    Qgis,
    QgsWkbTypes,
    QgsGeometry,
    QgsPoint,
    QgsCoordinateTransform,
    QgsFeature,
    QgsCoordinateReferenceSystem,
    QgsVectorDataProvider,
    QgsExpressionContext,
    QgsExpression,
    QgsAction,
    QgsAttributeTableConfig,
    QgsVectorLayer,
    QgsFields,
    QgsField,
    QgsVectorFileWriter,
    QgsUnitTypes,
    QgsCoordinateTransformContext,
    QgsFieldConstraints,
    QgsVectorLayerJoinInfo,
    QgsVectorLayerUtils,
    QgsDefaultValue,
    QgsFeatureRequest,
)

from qgis.gui import QgsMapMouseEvent

# global variable
MY_DICT = SQLiteDict()


# QgsMapToolEmitPoint
class LolEvt(LrEvt):
    """MapTool for Digitize Point-Events via reference-line and measured run-lengths
    to startpoint and endpoint"""

    # Rev. 2026-01-13

    # Nomenclature, functions beginning with...
    # cvs_* => canvas-functions, draw, pan, zoom...
    # dlg_* => dialog-functions, refresh parts of dialog...
    # gui_* => gui-functions, e.g. layer-actions
    # fvs* => check of feature-valid-state, stationing_n valid? referenced feature existing? see FVS
    # s_* => slot-functions triggered by widgets in dialog
    # ssc_* => slot-functions for configuration-change affecting stored_settings
    # st_* => slot-functions triggered from tabular widgets inside dialog
    # stm_* => functions to set a new tool-mode
    # sys_* => system functions
    # tool_* => auxiliary functions
    # stm_* => map-tool-setter, _*_ => name_of_map-tool
    # cpe_* => map-tool canvasPressEvent
    # cme_* => map-tool canvasMoveEvent
    # cre_* => map-tool canvasReleaseEvent

    def __init__(self, iface: QgisInterface):
        """initialize this mapTool
        :param iface: interface to QgisApp
        """
        super().__init__(iface)

        # dictionary for temporal grafics of type QgsRubberBand and QgsVertexMarker
        # z-index dependend on insertion order, last added ar drawn last and on top
        # key => shortcut used as parameter
        # value => QgsMapCanvasItem
        # not all markers used from both MapTools
        self.canvas_graphics = {}

        white = QColor("#ffffffff")
        red = QColor("#ffff0000")
        dark_red = QColor("#ffaf0000")
        red_trans = QColor("#aaff0000")
        green = QColor("#ff00ff00")
        dark_green = QColor("#FF009945")
        blue = QColor("#ff0000ff")
        blue_trans = QColor("#aa0000ff")
        blue_light = QColor("#aa8ea0f0")
        orange_trans = QColor("#aaffbb00")
        # orange = QColor("#ffffbb00")
        # gray_trans = QColor("#c1686868")

        # highlight the current selected reference-line
        # dotted white line to
        self.canvas_graphics["rfl"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["rfl"].setWidth(2)
        self.canvas_graphics["rfl"].setLineStyle(3)
        self.canvas_graphics["rfl"].setColor(white)

        # cached reference-line
        # thin dotted blue/transparent line
        self.canvas_graphics["rflca"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["rflca"].setWidth(1)
        self.canvas_graphics["rflca"].setLineStyle(3)
        self.canvas_graphics["rflca"].setColor(blue_trans)

        # cached segment on cached reference-line with offset
        # thick solid gray line under sgn
        self.canvas_graphics["sgncaca"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        # slightly wider than above sgn
        self.canvas_graphics["sgncaca"].setWidth(18)
        self.canvas_graphics["sgncaca"].setLineStyle(1)
        self.canvas_graphics["sgncaca"].setColor(blue_light)

        # segment on reference-line with offset
        # thick and semi-transparent-orange
        self.canvas_graphics["sgn"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["sgn"].setWidth(12)
        self.canvas_graphics["sgn"].setLineStyle(1)
        self.canvas_graphics["sgn"].setColor(orange_trans)

        # cached segment on cached reference-line without offset
        # thick dotted blue line
        self.canvas_graphics["sg0caca"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["sg0caca"].setWidth(3)
        self.canvas_graphics["sg0caca"].setLineStyle(3)
        self.canvas_graphics["sg0caca"].setColor(blue)

        # segment on reference-line without offset
        # solid red line
        self.canvas_graphics["sg0"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["sg0"].setWidth(2)
        self.canvas_graphics["sg0"].setLineStyle(1)
        self.canvas_graphics["sg0"].setColor(red)

        # difference-geometries cached vs. current reference-line
        # thin dotted blue line
        self.canvas_graphics["cacu"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["cacu"].setWidth(2)
        self.canvas_graphics["cacu"].setLineStyle(3)
        self.canvas_graphics["cacu"].setColor(blue)

        # difference-geometries current vs. cached reference-line
        # thin dotted red line
        self.canvas_graphics["cuca"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["cuca"].setWidth(2)
        self.canvas_graphics["cuca"].setLineStyle(3)
        self.canvas_graphics["cuca"].setColor(red)

        # visualize cached stationing on cached reference-line
        # blue circles
        self.canvas_graphics["caca"] = QgsVertexMarker(self.iface.mapCanvas())
        self.canvas_graphics["caca"].setIconType(4)
        self.canvas_graphics["caca"].setPenWidth(2)
        self.canvas_graphics["caca"].setIconSize(15)
        self.canvas_graphics["caca"].setColor(blue)

        # From-point on reference-line
        # green box
        self.canvas_graphics["snf"] = QgsVertexMarker(self.iface.mapCanvas())
        self.canvas_graphics["snf"].setPenWidth(2)
        self.canvas_graphics["snf"].setIconSize(10)
        self.canvas_graphics["snf"].setIconType(3)
        self.canvas_graphics["snf"].setColor(green)

        # same symbol but for multi-selections, see cvs_draw_feature_selection
        self.canvas_graphics["snf_mp"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Point
        )
        self.canvas_graphics["snf_mp"].setWidth(2)
        self.canvas_graphics["snf_mp"].setIconSize(10)
        self.canvas_graphics["snf_mp"].setIcon(3)
        self.canvas_graphics["snf_mp"].setColor(green)

        # To-point on reference-line
        # red box
        self.canvas_graphics["snt"] = QgsVertexMarker(self.iface.mapCanvas())
        self.canvas_graphics["snt"].setPenWidth(2)
        self.canvas_graphics["snt"].setIconSize(10)
        self.canvas_graphics["snt"].setIconType(3)
        self.canvas_graphics["snt"].setColor(red)

        # same symbol but for multi-selections, see cvs_draw_feature_selection
        self.canvas_graphics["snt_mp"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Point
        )
        self.canvas_graphics["snt_mp"].setWidth(2)
        self.canvas_graphics["snt_mp"].setIconSize(10)
        self.canvas_graphics["snt_mp"].setIcon(3)
        self.canvas_graphics["snt_mp"].setStrokeColor(red)

        # From point for edit
        # green circle
        self.canvas_graphics["enf"] = QgsVertexMarker(self.iface.mapCanvas())
        self.canvas_graphics["enf"].setIconType(4)
        self.canvas_graphics["enf"].setPenWidth(2)
        self.canvas_graphics["enf"].setIconSize(30)
        self.canvas_graphics["enf"].setColor(green)

        # To point for edit
        # red circle
        self.canvas_graphics["ent"] = QgsVertexMarker(self.iface.mapCanvas())
        self.canvas_graphics["ent"].setIconType(4)
        self.canvas_graphics["ent"].setPenWidth(2)
        self.canvas_graphics["ent"].setIconSize(30)
        self.canvas_graphics["ent"].setColor(red)

        # Start-Vertex of cached segment
        # green circle
        self.canvas_graphics["snfcaca"] = QgsVertexMarker(self.iface.mapCanvas())
        self.canvas_graphics["snfcaca"].setIconType(4)
        self.canvas_graphics["snfcaca"].setPenWidth(2)
        self.canvas_graphics["snfcaca"].setIconSize(15)
        self.canvas_graphics["snfcaca"].setColor(dark_green)

        # same symbol but for multi-selections, see cvs_draw_po_pro_selection
        self.canvas_graphics["snfcaca_mp"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Point
        )
        self.canvas_graphics["snfcaca_mp"].setIcon(4)
        self.canvas_graphics["snfcaca_mp"].setWidth(2)
        self.canvas_graphics["snfcaca_mp"].setIconSize(10)
        self.canvas_graphics["snfcaca_mp"].setStrokeColor(dark_green)

        # End-Vertex of cached segment
        # red circle
        self.canvas_graphics["sntcaca"] = QgsVertexMarker(self.iface.mapCanvas())
        self.canvas_graphics["sntcaca"].setIconType(4)
        self.canvas_graphics["sntcaca"].setPenWidth(2)
        self.canvas_graphics["sntcaca"].setIconSize(15)
        self.canvas_graphics["sntcaca"].setColor(dark_red)

        # same symbol but for multi-selections, see cvs_draw_po_pro_selection
        self.canvas_graphics["sntcaca_mp"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Point
        )
        self.canvas_graphics["sntcaca_mp"].setIcon(4)
        self.canvas_graphics["sntcaca_mp"].setWidth(2)
        self.canvas_graphics["sntcaca_mp"].setIconSize(10)
        self.canvas_graphics["sntcaca_mp"].setStrokeColor(dark_red)

        # selection-rect
        # red border, half transparent
        self.canvas_graphics["sel"] = QgsRubberBand(
            self.iface.mapCanvas(), Qgis.GeometryType.Line
        )
        self.canvas_graphics["sel"].setWidth(2)
        self.canvas_graphics["sel"].setFillColor(red_trans)
        self.canvas_graphics["sel"].setStrokeColor(red)

        # initially hide markers
        self.cvs_hide_markers()

        # Qactions, used in dialog
        # Section "Measurement"
        if True:
            self.qact_open_ref_table = QAction(
                QIcon(":icons/mActionOpenTable.svg"),
                MY_DICT.tr("open_reference_layer_table"),
                self.my_dialog,
            )
            self.qact_open_ref_table.triggered.connect(self.s_open_ref_tbl)

            self.qact_open_ref_form = QAction(
                QIcon(":icons/mActionFormView.svg"),
                MY_DICT.tr("open_feature_form_ttp"),
                self.my_dialog,
            )
            self.qact_open_ref_form.triggered.connect(self.s_open_ref_form)

            self.qact_zoom_ref_feature = QAction(
                QIcon(":icons/mIconZoom.svg"),
                MY_DICT.tr("qact_zoom_ref_feature_tbtxt"),
                self.my_dialog,
            )
            self.qact_zoom_ref_feature.triggered.connect(self.cvs_zoom_current_ref_fid)
            self.qact_zoom_ref_feature.setToolTip(
                MY_DICT.tr("qact_zoom_ref_feature_ttp")
            )

            self.qact_select_in_ref_layer = QAction(
                QIcon(":icons/select_in_layer.svg"),
                MY_DICT.tr("transfer_feature_selection_pbtxt"),
                self.my_dialog,
            )
            self.qact_select_in_ref_layer.setToolTip(MY_DICT.tr("select_in_layer_ttp"))
            self.qact_select_in_ref_layer.triggered.connect(self.s_select_in_ref_layer)

            self.qact_move_to_start = QAction(
                QIcon(":icons/mActionTrippleArrowLeft.svg"),
                MY_DICT.tr("move_to_start_ttp"),
            )
            self.qact_move_to_start.triggered.connect(self.s_move_to_start)

            self.qact_flip_down = QAction(
                QIcon(":icons/mActionDoubleArrowLeft.svg"),
                MY_DICT.tr("flip_down_ttp"),
            )
            self.qact_flip_down.triggered.connect(self.s_flip_down)

            self.qact_move_down = QAction(
                QIcon(":icons/mActionArrowLeft.svg"), MY_DICT.tr("move_down_ttp")
            )
            self.qact_move_down.triggered.connect(self.s_move_down)

            self.qact_measure_segment = QAction(
                QIcon(":icons/re_digitize_lol.svg"), MY_DICT.tr("resume_ttp")
            )
            self.qact_measure_segment.setCheckable(True)
            self.qact_measure_segment.triggered.connect(self.stm_measure_segment)
            self.iface.mapToolActionGroup().addAction(self.qact_measure_segment)

            self.qact_move_up = QAction(
                QIcon(":icons/mActionArrowRight.svg"), MY_DICT.tr("move_up_ttp")
            )
            self.qact_move_up.triggered.connect(self.s_move_up)

            self.qact_flip_up = QAction(
                QIcon(":icons/mActionDoubleArrowRight.svg"),
                MY_DICT.tr("flip_up_ttp"),
            )
            self.qact_flip_up.triggered.connect(self.s_flip_up)

            self.qact_move_end = QAction(
                QIcon(":icons/mActionTrippleArrowRight.svg"),
                MY_DICT.tr("move_end_ttp"),
            )
            self.qact_move_end.triggered.connect(self.s_move_to_end)

            self.qact_set_from_point = QAction(
                QIcon(":icons/set_from_point.svg"), MY_DICT.tr("set_from_point_ttp")
            )
            self.qact_set_from_point.setCheckable(True)
            self.qact_set_from_point.triggered.connect(self.stm_set_from_point)
            self.iface.mapToolActionGroup().addAction(self.qact_set_from_point)

            self.qact_set_to_point = QAction(
                QIcon(":icons/set_to_point.svg"), MY_DICT.tr("set_to_point_ttp")
            )
            self.qact_set_to_point.setCheckable(True)
            self.qact_set_to_point.triggered.connect(self.stm_set_to_point)
            self.iface.mapToolActionGroup().addAction(self.qact_set_to_point)

            self.qact_move_segment = QAction(
                QIcon(":icons/move_segment.svg"), MY_DICT.tr("move_segment_ttp")
            )
            self.qact_move_segment.setCheckable(True)
            self.qact_move_segment.triggered.connect(self.stm_move_segment)
            self.iface.mapToolActionGroup().addAction(self.qact_move_segment)

            self.qact_change_offset = QAction(
                QIcon(":icons/change_offset.svg"), MY_DICT.tr("change_offset_ttp")
            )
            self.qact_change_offset.setCheckable(True)
            self.qact_change_offset.triggered.connect(self.stm_change_offset)
            self.iface.mapToolActionGroup().addAction(self.qact_change_offset)

            self.qact_zoom_lr_geom = QAction(
                QIcon(":icons/mIconZoom.svg"),
                MY_DICT.tr("qact_zoom_to_segment_txt"),
            )
            self.qact_zoom_lr_geom.setToolTip(MY_DICT.tr("qact_zoom_to_segment_ttp"))
            self.qact_zoom_lr_geom.triggered.connect(self.s_draw_lr_geom_runtime)

            self.qact_select_edit_feature = QAction(
                QIcon(":icons/select_lol_feature.svg"),
                MY_DICT.tr("qact_select_edit_feature_tbtxt"),
            )
            self.qact_select_edit_feature.setCheckable(True)
            self.qact_select_edit_feature.triggered.connect(
                self.stm_select_edit_feature
            )
            self.iface.mapToolActionGroup().addAction(self.qact_select_edit_feature)

            self.qact_toggle_edit_mode = QAction(
                QIcon(":icons/mActionToggleEditing.svg"),
                MY_DICT.tr("toggle_editing_pbtxt"),
            )
            self.qact_toggle_edit_mode.triggered.connect(self.s_toggle_edit_mode)

            self.qact_show_edit_feature_form = QAction(
                QIcon(":icons/mActionFormView.svg"),
                MY_DICT.tr("show_edit_feature_form_tbtxt"),
            )
            self.qact_show_edit_feature_form.triggered.connect(
                self.s_show_edit_feature_form
            )

            self.qact_update_feature = QAction(
                QIcon(":icons/mActionFileSave.svg"),
                MY_DICT.tr("update_edit_feature_tbtxt"),
            )
            self.qact_update_feature.triggered.connect(self.s_update_feature)

            self.qact_insert_feature = QAction(
                QIcon(":icons/insert_record.svg"),
                MY_DICT.tr("insert_to_data_layer_txt"),
            )
            self.qact_insert_feature.triggered.connect(self.s_insert_feature)

        # Section "Feature-Selection":
        if True:
            self.qact_append_data_features = QAction(
                QIcon(":icons/mActionEditIndentMore.svg"),
                MY_DICT.tr("append_data_features_pbtxt"),
            )
            self.qact_append_data_features.triggered.connect(
                self.s_append_to_feature_selection
            )

            self.qact_select_from_table = QAction(
                QIcon(":icons/mActionOpenTable.svg"),
                MY_DICT.tr("qact_select_from_table_tbtxt"),
            )
            self.qact_select_from_table.setToolTip(
                MY_DICT.tr("qact_select_from_table_ttp")
            )
            self.qact_select_from_table.triggered.connect(self.s_open_data_tbl)

            self.qact_select_features = QAction(
                QIcon(":icons/select_lol_feature.svg"),
                MY_DICT.tr("qact_select_features_tbtxt"),
            )
            self.qact_select_features.setToolTip(MY_DICT.tr("qact_select_features_ttp"))
            self.qact_select_features.setCheckable(True)
            self.qact_select_features.triggered.connect(self.stm_select_features)
            self.iface.mapToolActionGroup().addAction(self.qact_select_features)

            self.qact_zoom_feature_selection = QAction(
                QIcon(":icons/mActionZoomToSelected.svg"),
                MY_DICT.tr("zoom_to_selection_pbtxt"),
            )
            self.qact_zoom_feature_selection.setToolTip(
                MY_DICT.tr("zoom_to_selection_ttp")
            )
            self.qact_zoom_feature_selection.triggered.connect(
                self.s_zoom_to_feature_selection
            )

            self.qact_clear_feature_selection = QAction(
                QIcon(":icons/mIconClearTextHover.svg"),
                MY_DICT.tr("clear_selection_pbtxt"),
            )
            self.qact_clear_feature_selection.triggered.connect(
                self.s_clear_feature_selection
            )

            self.qact_transfer_feature_selection = QAction(
                QIcon(":icons/select_in_layer.svg"),
                MY_DICT.tr("transfer_feature_selection_pbtxt"),
            )
            self.qact_transfer_feature_selection.setToolTip(
                MY_DICT.tr("select_in_layer_ttp")
            )
            self.qact_transfer_feature_selection.triggered.connect(
                self.s_transfer_feature_selection
            )

            self.qact_filter_by_feature_selection = QAction(
                QIcon(":icons/mActionFilter2.svg"),
                MY_DICT.tr("set_feature_selection_filter_pbtxt"),
            )
            self.qact_filter_by_feature_selection.setToolTip(
                MY_DICT.tr("set_feature_selection_filter_ttp")
            )
            self.qact_filter_by_feature_selection.triggered.connect(
                self.s_filter_data_lyr
            )

        # PostProcessing-Section:
        if True:
            self.qact_open_po_pro_ref_lyr = QAction(
                QIcon(":icons/mActionOpenTable.svg"),
                MY_DICT.tr("open_po_pro_ref_lyr_table"),
            )
            self.qact_open_po_pro_ref_lyr.triggered.connect(
                self.s_open_po_pro_ref_lyr_tbl
            )

            self.qact_create_po_pro_ref_lyr = QAction(
                QIcon(":icons/NewDataTable.svg"),
                MY_DICT.tr("qact_create_po_pro_ref_lyr_txt"),
            )
            self.qact_create_po_pro_ref_lyr.setToolTip(
                MY_DICT.tr("qact_create_po_pro_ref_lyr_ttp")
            )
            self.qact_create_po_pro_ref_lyr.triggered.connect(
                self.sys_create_po_pro_ref_lyr
            )

            self.qact_start_post_processing = QAction(
                QIcon(":icons/mActionEditIndentMore.svg"),
                MY_DICT.tr("qact_start_po_pro_tbtxt"),
            )
            self.qact_start_post_processing.setToolTip(
                MY_DICT.tr("qact_start_po_pro_ttp")
            )
            self.qact_start_post_processing.triggered.connect(
                self.s_start_post_processing
            )

            self.qact_zoom_po_pro_selection = QAction(
                QIcon(":icons/mActionZoomToSelected.svg"),
                MY_DICT.tr("zoom_to_selection_pbtxt"),
            )
            self.qact_zoom_po_pro_selection.triggered.connect(
                self.s_zoom_to_po_pro_selection
            )

            self.qact_clear_po_pro_selection = QAction(
                QIcon(":icons/mIconClearTextHover.svg"),
                MY_DICT.tr("clear_selection_pbtxt"),
            )
            self.qact_clear_po_pro_selection.triggered.connect(
                self.s_clear_po_pro_selection
            )

            self.qact_move_po_pro_from_point = QAction(
                QIcon(":icons/move_po_pro_from_point.svg"),
                MY_DICT.tr("qact_move_po_pro_from_point_pp_tbtxt"),
            )
            self.qact_move_po_pro_from_point.setToolTip(
                MY_DICT.tr("qact_move_po_pro_from_point_pp_ttp")
            )
            self.qact_move_po_pro_from_point.setCheckable(True)
            self.qact_move_po_pro_from_point.triggered.connect(
                self.stm_move_po_pro_from
            )
            self.iface.mapToolActionGroup().addAction(self.qact_move_po_pro_from_point)

            self.qact_move_po_pro_to_point = QAction(
                QIcon(":icons/move_po_pro_to_point.svg"),
                MY_DICT.tr("qact_move_po_pro_to_point_tbtxt"),
            )
            self.qact_move_po_pro_to_point.setToolTip(
                MY_DICT.tr("qact_move_po_pro_to_point_pp_ttp")
            )
            self.qact_move_po_pro_to_point.setCheckable(True)
            self.qact_move_po_pro_to_point.triggered.connect(self.stm_move_po_pro_to)
            self.iface.mapToolActionGroup().addAction(self.qact_move_po_pro_to_point)

            self.qact_move_po_pro_segment = QAction(
                QIcon(":icons/move_po_pro_segment.svg"),
                MY_DICT.tr("qact_move_po_pro_segment_pbtxt"),
            )
            self.qact_move_po_pro_segment.setToolTip(
                MY_DICT.tr("qact_move_po_pro_segment_ttp")
            )
            self.qact_move_po_pro_segment.setCheckable(True)
            self.qact_move_po_pro_segment.triggered.connect(
                self.stm_move_po_pro_segment
            )
            self.iface.mapToolActionGroup().addAction(self.qact_move_po_pro_segment)

            self.qact_toggle_po_pro_edit_mode = QAction(
                QIcon(":icons/mActionToggleEditing.svg"),
                MY_DICT.tr("toggle_editing_pbtxt"),
            )
            self.qact_toggle_po_pro_edit_mode.triggered.connect(self.s_toggle_edit_mode)
        # Section "Settings"
        if True:
            self.qact_define_ref_lyr_display_expression = QAction(
                QIcon(":icons/mIconExpression.svg"),
                MY_DICT.tr("edit_ref_lyr_display_exp_ttp"),
                self.my_dialog,
            )
            self.qact_define_ref_lyr_display_expression.triggered.connect(
                self.s_define_ref_lyr_display_expression
            )

            self.qact_open_data_table = QAction(
                QIcon(":icons/mActionOpenTable.svg"),
                MY_DICT.tr("open_data_layer_table"),
            )
            self.qact_open_data_table.triggered.connect(self.s_open_data_tbl)

            self.qact_create_data_lyr = QAction(
                QIcon(":icons/NewDataTable.svg"),
                MY_DICT.tr("qact_create_data_lyr_txt"),
                self.my_dialog,
            )
            self.qact_create_data_lyr.triggered.connect(self.sys_create_data_lyr)

            self.qact_define_data_lyr_display_expression = QAction(
                QIcon(":icons/mIconExpression.svg"),
                MY_DICT.tr("edit_data_lyr_display_exp_ttp"),
                self.my_dialog,
            )
            self.qact_define_data_lyr_display_expression.triggered.connect(
                self.s_define_data_lyr_display_expression
            )

            self.qact_open_show_tbl = QAction(
                QIcon(":icons/mActionOpenTable.svg"),
                MY_DICT.tr("open_show_layer_table"),
                self.my_dialog,
            )
            self.qact_open_show_tbl.triggered.connect(self.s_open_show_tbl)

            self.qact_create_show_lyr = QAction(
                QIcon(":icons/NewDataTable.svg"),
                MY_DICT.tr("qact_create_show_lyr_txt"),
                self.my_dialog,
            )
            self.qact_create_show_lyr.triggered.connect(self.sys_create_show_layer)

        # section Message-Log
        if True:
            self.qact_check_log_messages = QAction(
                QIcon(":icons/Green_check_icon_with_gradient.svg"),
                MY_DICT.tr("qact_check_log_messages_tbtxt"),
                self.my_dialog,
            )
            self.qact_check_log_messages.triggered.connect(self.dlg_check_log_messages)

            self.qact_clear_log_messages = QAction(
                QIcon(":icons/mActionRemove.svg"),
                MY_DICT.tr("qact_clear_log_messages_tbtxt"),
                self.my_dialog,
            )
            self.qact_clear_log_messages.triggered.connect(self.dlg_clear_log_messages)

        self.dlg_init()

        # if a reference-layer is already registered: start measuring
        if self.derived_settings.refLyr is not None:
            self.qact_measure_segment.trigger()
        else:
            # open settings-tab
            self.dlg_show_tab("settings")
            self.sys_log_message("INFO", MY_DICT.tr("register_reference_layer"))
            self.iface.messageBar().pushMessage(
                "Linear-Referencing:",
                MY_DICT.tr("register_reference_layer"),
                level=Qgis.Info,
            )

        self.sys_log_message("SUCCESS", MY_DICT.tr("map_tool_initialized"))

        self.dlg_show_message_log()

    def canvasPressEvent(self, event: QgsMapMouseEvent) -> None:
        """mouseDown on canvas, reimplemented standard-function for QgsMapToolIdentify
        triggered action self.cpe_xxx dependend on self.session_data.tool_mode
        see canvasMoveEvent and canvasReleaseEvent
        :param event:
        """
        # Rev. 2026-01-13
        try:
            if self.session_data.tool_mode != "pausing":
                self.my_dialog.dnspbx_canvas_x.setValue(event.mapPoint().x())
                self.my_dialog.dnspbx_canvas_y.setValue(event.mapPoint().y())

            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.tool_mode == "pausing":
                    # convenience for tool_mode 'pausing': switch-back to previous_tool_mode
                    previous_tool_mode = self.session_data.previous_tool_mode
                    if previous_tool_mode == "set_from_point":
                        self.qact_set_from_point.trigger()
                    elif previous_tool_mode == "set_to_point":
                        self.qact_set_to_point.trigger()
                    elif previous_tool_mode == "move_segment":
                        self.qact_move_segment.trigger()
                    elif previous_tool_mode == "move_po_pro_segment":
                        self.stm_move_po_pro_segment()
                        self.qact_move_po_pro_segment.trigger()
                    elif previous_tool_mode == "move_po_pro_from":
                        self.qact_move_po_pro_from_point.trigger()
                    elif previous_tool_mode == "move_po_pro_to":
                        self.qact_move_po_pro_to_point.trigger()
                    elif previous_tool_mode == "change_offset":
                        self.qact_change_offset.trigger()
                    elif previous_tool_mode == "measure_segment":
                        self.qact_measure_segment.trigger()

                if self.session_data.tool_mode == "set_from_point":
                    self.cpe_set_from_point(event)
                elif self.session_data.tool_mode == "set_to_point":
                    self.cpe_set_to_point(event)
                elif self.session_data.tool_mode == "measure_segment":
                    self.cpe_measure_segment(event)
                elif self.session_data.tool_mode == "move_segment":
                    self.cpe_move_segment(event)
                elif self.session_data.tool_mode == "move_po_pro_segment":
                    self.cpe_move_po_pro_segment(event)
                elif self.session_data.tool_mode == "move_po_pro_from":
                    self.cpe_move_po_pro_from(event)
                elif self.session_data.tool_mode == "move_po_pro_to":
                    self.cpe_move_po_pro_to(event)
                elif self.session_data.tool_mode == "change_offset":
                    self.cpe_change_offset(event)
                elif self.session_data.tool_mode == "select_features":
                    self.cpe_select_features(event)
                elif self.session_data.tool_mode == "select_edit_feature":
                    self.cpe_select_edit_feature(event)

            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        """MouseMove on canvas, reimplemented standard-function for QgsMapToolIdentify
        triggered action self.cme_xxx dependend on self.session_data.tool_mode
        see canvasPressEvent and canvasReleaseEvent
        :param event:
        """
        # Rev. 2026-01-13
        try:
            if self.session_data.tool_mode != "pausing":
                self.my_dialog.dnspbx_canvas_x.setValue(event.mapPoint().x())
                self.my_dialog.dnspbx_canvas_y.setValue(event.mapPoint().y())

            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:

                if self.session_data.tool_mode == "pausing":
                    pass
                elif self.session_data.tool_mode == "set_from_point":
                    self.cme_set_from_point(event)
                elif self.session_data.tool_mode == "set_to_point":
                    self.cme_set_to_point(event)
                elif self.session_data.tool_mode == "measure_segment":
                    self.cme_measure_segment(event)
                elif self.session_data.tool_mode == "move_segment":
                    self.cme_move_segment(event)
                elif self.session_data.tool_mode == "move_po_pro_segment":
                    self.cme_move_po_pro_segment(event)
                elif self.session_data.tool_mode == "move_po_pro_from":
                    self.cme_move_po_pro_from(event)
                elif self.session_data.tool_mode == "move_po_pro_to":
                    self.cme_move_po_pro_to(event)
                elif self.session_data.tool_mode == "change_offset":
                    self.cme_change_offset(event)
                elif self.session_data.tool_mode == "select_features":
                    self.cme_select_features(event)
                elif self.session_data.tool_mode == "select_edit_feature":
                    self.cme_select_edit_feature(event)
            else:
                # avoid raising lots of Exceptions
                self.iface.mapCanvas().unsetMapTool(self)
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)



    def canvasReleaseEvent(self, event: QgsMapMouseEvent) -> None:
        """mouseUp on canvas, reimplemented standard-function for QgsMapToolIdentify
        triggered action self.cre_xxx dependend on self.session_data.tool_mode
        see canvasPressEvent and canvasMoveEvent
        :param event:
        """
        # Rev. 2026-01-13
        try:
            if self.session_data.tool_mode != "pausing":
                self.my_dialog.dnspbx_canvas_x.setValue(event.mapPoint().x())
                self.my_dialog.dnspbx_canvas_y.setValue(event.mapPoint().y())

            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.tool_mode == "pausing":
                    pass
                if self.session_data.tool_mode == "set_from_point":
                    self.cre_set_from_point(event)
                elif self.session_data.tool_mode == "set_to_point":
                    self.cre_set_to_point(event)
                elif self.session_data.tool_mode == "measure_segment":
                    self.cre_measure_segment(event)
                elif self.session_data.tool_mode == "move_segment":
                    self.cre_move_segment(event)
                elif self.session_data.tool_mode == "move_po_pro_segment":
                    self.cre_move_po_pro_segment(event)
                elif self.session_data.tool_mode == "move_po_pro_from":
                    self.cre_move_po_pro_from(event)
                elif self.session_data.tool_mode == "move_po_pro_to":
                    self.cre_move_po_pro_to(event)
                elif self.session_data.tool_mode == "change_offset":
                    self.cre_change_offset(event)
                elif self.session_data.tool_mode == "select_features":
                    self.cre_select_features(event)
                elif self.session_data.tool_mode == "select_edit_feature":
                    self.cre_select_edit_feature(event)

            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def stm_measure_segment(self):
        """set tool mode 'measure_segment'"""
        # Rev. 2026-01-13
        if self.sys_set_tool_mode("measure_segment"):
            self.session_data.lr_geom_runtime = None
            self.session_data.snap_n_abs_mouse_down = None
            self.cvs_hide_markers()
            self.dlg_reset_measurement()
            self.dlg_refract_measurement()

    def cme_measure_segment(self, event: QgsMapMouseEvent):
        """canvas move for tool_mode 'measure_segment'
        Case distinction:
        1. lr_geom_runtime exists and left mouse button => active dragging to-position => no snap, but nearest point stationing
        2. no lr_geom_runtime => show snap on any reference-geometry
        """
        # Rev. 2026-01-13
        event_with_left_btn = bool(Qt.LeftButton & event.buttons())
        self.cvs_hide_markers()
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                if event_with_left_btn:
                    try:
                        snap_n_abs = self.tool_snap_to_ref_feature(
                            event, self.session_data.lr_geom_runtime.ref_fid
                        )
                        if snap_n_abs is not None:
                            # 1. active dragging to-position:
                            self.session_data.lr_geom_runtime.update_stationing_to(
                                snap_n_abs, "Nabs"
                            )

                            self.cvs_draw_lr_geom(
                                self.session_data.lr_geom_runtime,
                                ["snf", "snt", "ent", "sgn", "sg0", "rfl"],
                            )
                            self.dlg_populate_measurement()
                    except:
                        pass
            else:
                snap_result = self.tool_snap_to_ref_layer(event)
                if snap_result:
                    (ref_fid, snap_n_abs, match) = snap_result
                    self.cvs_show_snap(match)
                    self.dlg_select_qcbn_reference_feature(ref_fid)
                    self.cvs_draw_reference_geom(ref_fid=ref_fid)
        else:
            raise LayerNotRegisteredException("RefLyr")

    def cpe_measure_segment(self, event: QgsMapMouseEvent):
        """canvas press for tool_mode 'measure_segment'"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            snap_result = self.tool_snap_to_ref_layer(event)
            if snap_result:
                (ref_fid, snap_n_abs, match) = snap_result
                lr_geom_runtime = LoL.init_by_stationings(
                    self.derived_settings.refLyr,
                    ref_fid,
                    snap_n_abs,
                    snap_n_abs,
                    self.session_data.current_offset,
                    "Nabs",
                )
                self.session_data.lr_geom_runtime = lr_geom_runtime
                self.cvs_draw_lr_geom(self.session_data.lr_geom_runtime, ["snf"])
                self.dlg_populate_measurement()

    def cre_measure_segment(self, event: QgsMapMouseEvent):
        """canvas release for tool_mode 'measure_segment'"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime:
                snap_n_abs = self.tool_snap_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
                if snap_n_abs is not None:
                    self.session_data.lr_geom_runtime.update_stationing_to(
                        snap_n_abs, "Nabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                    self.dlg_refract_measurement()
            else:
                raise RuntimeObjectMissingException("Digitized feature")

        self.qact_pausing.trigger()

    def stm_set_from_point(self):
        """set tool mode 'set_from_point'"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if self.sys_set_tool_mode("set_from_point"):
            if self.session_data.lr_geom_runtime:
                self.cvs_draw_lr_geom(
                    self.session_data.lr_geom_runtime,
                    ["snf", "enf", "snt", "sgn", "sg0", "rfl"],
                    ["snf"],
                    ["snf", "sg0"],
                )

    def cpe_set_from_point(self, event: QgsMapMouseEvent):
        """canvas press for tool_mode 'set_from_point'
        Case distinction:
        1. lr_geom_runtime exists => active dragging from-position => update_stationing_from without snap if reference-feature matches
        2. no lr_geom_runtime => init new one setting from_stationing ==  to_stationing
        """
        # Rev. 2026-01-13
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                snap_n_abs = self.tool_snap_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
                if snap_n_abs is not None:
                    # 1. active dragging from-position:

                    self.session_data.lr_geom_runtime.update_stationing_from(
                        snap_n_abs, "Nabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "enf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

            else:
                snap_result = self.tool_snap_to_ref_layer(event)
                if snap_result:
                    (ref_fid, snap_n_abs, match) = snap_result
                    # 2: new lr_geom_runtime mit staioning_from == stationing_to
                    lr_geom_runtime = LoL.init_by_stationings(
                        self.derived_settings.refLyr,
                        ref_fid,
                        snap_n_abs,
                        snap_n_abs,
                        self.session_data.current_offset,
                        "Nabs",
                    )
                    self.session_data.lr_geom_runtime = lr_geom_runtime
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "enf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

    def cme_set_from_point(self, event: QgsMapMouseEvent):
        """canvas move for tool_mode 'set_from_point'
        Case distinction:
        1. lr_geom_runtime exists and left mouse button => active dragging from-position => no snap, but nearest point stationing
        2. lr_geom_runtime exists without mouse button => show snap on matching reference-feature
        3. no lr_geom_runtime => show snap on any reference line, create new lr_geom_runtime with next set_from_point_cpe
        """
        # Rev. 2026-01-13
        event_with_left_btn = bool(Qt.LeftButton & event.buttons())

        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                if event_with_left_btn:
                    snap_n_abs = self.tool_snap_to_ref_feature(
                        event, self.session_data.lr_geom_runtime.ref_fid
                    )
                    if snap_n_abs is not None:
                        # 1. active dragging from-position:
                        self.session_data.lr_geom_runtime.update_stationing_from(
                            snap_n_abs, "Nabs"
                        )
                        self.cvs_draw_lr_geom(
                            self.session_data.lr_geom_runtime,
                            ["snf", "enf", "snt", "sgn", "sg0", "rfl"],
                        )
                        self.dlg_populate_measurement()

                else:
                    # 2. mouse-move with lr_geom_runtime without mouse-button: show snap, if geometry matches
                    snap_result = self.tool_snap_to_ref_layer(event)
                    if snap_result:
                        (ref_fid, snap_n_abs, match) = snap_result
                        if ref_fid == self.session_data.lr_geom_runtime.ref_fid:
                            self.cvs_show_snap(match)
            else:
                # 3: mouse-move without lr_geom_runtime => show snap and highlight on any reference-geometry
                snap_result = self.tool_snap_to_ref_layer(event)
                if snap_result:
                    (ref_fid, snap_n_abs, match) = snap_result
                    self.cvs_show_snap(match)
                    self.dlg_select_qcbn_reference_feature(ref_fid)
                    self.cvs_draw_reference_geom(ref_fid=ref_fid)

    def cre_set_from_point(self, event: QgsMapMouseEvent):
        """canvas release for tool_mode 'set_from_point'
        if lr_geom_runtime exists: update its stationing_from
        """
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime:
                snap_n_abs = self.tool_snap_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
                if snap_n_abs is not None:
                    self.session_data.lr_geom_runtime.update_stationing_from(
                        snap_n_abs, "Nabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                    self.dlg_refract_measurement()
            else:
                raise RuntimeObjectMissingException("Digitized feature")
        self.qact_pausing.trigger()

    def stm_move_po_pro_from(self):
        """set toolmode move_po_pro_from for self.session_data.po_pro_feature.lr_geom_current"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if self.sys_set_tool_mode("move_po_pro_from"):

            self.dlg_select_po_pro_selection_row(
                self.session_data.po_pro_feature.data_fid
            )

            self.cvs_draw_lr_geom(
                self.session_data.po_pro_feature.lr_geom_current,
                ["snf", "enf", "snt", "sgn", "sg0", "rfl"],
                flash_markers=["enf"],
            )

            self.cvs_draw_lr_geom(
                self.session_data.po_pro_feature.lr_geom_cached,
                ["snfcaca", "sntcaca", "sg0caca"],
                flash_markers=["snfcaca"],
            )

    def cpe_move_po_pro_from(self, event):
        """canvasPressEvent for "move_po_pro_from"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
            | SVS.PO_PRO_REF_LAYER_CONNECTED
            | SVS.DATA_LAYER_EDITABLE
        ) in self.system_vs and self.session_data.po_pro_feature is not None:
            lr_geom_current = self.session_data.po_pro_feature.lr_geom_current
            lr_geom_cached = self.session_data.po_pro_feature.lr_geom_cached
            # snap to current geometry, not to ca_ca_lol.ref_geom
            snap_n_abs = self.tool_snap_to_ref_geom(
                event, lr_geom_current.reference_geom
            )

            if snap_n_abs is not None:

                self.session_data.snap_n_abs_mouse_down = snap_n_abs
                lr_geom_current.update_stationing_from(snap_n_abs, "Nabs")
                self.cvs_draw_lr_geom(
                    lr_geom_current,
                    ["snf", "enf", "snt", "sgn", "sg0", "rfl"],
                )

                self.cvs_draw_lr_geom(
                    lr_geom_cached,
                    ["snfcaca", "sntcaca", "sg0caca"],
                )

    def cme_move_po_pro_from(self, event):
        """canvasMoveEvent for "move_po_pro_from"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        if Qt.LeftButton & event.buttons():
            self.cpe_move_po_pro_from(event)

    def cre_move_po_pro_from(self, event):
        """canvasReleaseEvent for "move_po_pro_from"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
            | SVS.PO_PRO_REF_LAYER_CONNECTED
            | SVS.DATA_LAYER_EDITABLE
        ) in self.system_vs and self.session_data.po_pro_feature is not None:
            self.cpe_move_po_pro_from(event)
            self.s_save_po_pro_feature()

        self.qact_pausing.trigger()

    def stm_move_po_pro_segment(self):
        """set toolmode move_po_pro_segment for self.session_data.po_pro_feature.lr_geom_current"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if self.sys_set_tool_mode("move_po_pro_segment"):
            self.dlg_select_po_pro_selection_row(
                self.session_data.po_pro_feature.data_fid
            )

            self.cvs_draw_lr_geom(
                self.session_data.po_pro_feature.lr_geom_current,
                ["snf", "ent", "enf", "snt", "sgn", "sg0", "rfl"],
                flash_markers=["enf", "ent"],
            )

            self.cvs_draw_lr_geom(
                self.session_data.po_pro_feature.lr_geom_cached,
                ["snfcaca", "sntcaca", "sg0caca"],
                flash_markers=["snfcaca", "sntcaca"],
            )

    def cpe_move_po_pro_segment(self, event):
        """canvasPressEvent for "move_po_pro_segment"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
            | SVS.PO_PRO_REF_LAYER_CONNECTED
            | SVS.DATA_LAYER_EDITABLE
        ) in self.system_vs and self.session_data.po_pro_feature is not None:
            lr_geom_current = self.session_data.po_pro_feature.lr_geom_current
            lr_geom_cached = self.session_data.po_pro_feature.lr_geom_cached
            snap_n_abs = self.tool_snap_to_ref_geom(
                event, lr_geom_current.reference_geom
            )
            if snap_n_abs is not None:
                self.session_data.snap_n_abs_mouse_down = snap_n_abs
                self.cvs_draw_lr_geom(
                    lr_geom_current,
                    ["snf", "snt", "enf", "ent", "sgn", "sg0", "rfl"],
                )
                self.cvs_draw_lr_geom(
                    lr_geom_cached,
                    ["snfcaca", "sntcaca", "sg0caca"],
                )

    def cme_move_po_pro_segment(self, event):
        """canvasMoveEvent for "move_po_pro_segment"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
            | SVS.PO_PRO_REF_LAYER_CONNECTED
            | SVS.DATA_LAYER_EDITABLE
        ) in self.system_vs and self.session_data.po_pro_feature is not None:
            if (
                Qt.LeftButton & event.buttons()
                and self.session_data.snap_n_abs_mouse_down is not None
            ):
                lr_geom_current = self.session_data.po_pro_feature.lr_geom_current
                snap_n_abs = self.tool_snap_to_ref_geom(
                    event, lr_geom_current.reference_geom
                )
                if snap_n_abs is not None:
                    delta_snap_n_abs = (
                        snap_n_abs - self.session_data.snap_n_abs_mouse_down
                    )
                    lr_geom_current.move_segment(delta_snap_n_abs)
                    self.cvs_draw_lr_geom(
                        lr_geom_current,
                        ["snf", "snt", "enf", "ent", "sgn", "sg0", "rfl"],
                    )
                    # self.cvs_draw_lr_geom(
                    #     self.session_data.po_pro_feature.lr_geom_cached,
                    #     ["snfcaca", "sntcaca", "sg0caca"],
                    # )
                    self.session_data.snap_n_abs_mouse_down = snap_n_abs

    def cre_move_po_pro_segment(self, event):
        """canvasReleaseEvent for "move_po_pro_segment"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
            | SVS.PO_PRO_REF_LAYER_CONNECTED
            | SVS.DATA_LAYER_EDITABLE
        ) in self.system_vs and self.session_data.po_pro_feature is not None:
            self.cme_move_po_pro_segment(event)
            self.s_save_po_pro_feature()

        self.qact_pausing.trigger()

    def stm_move_po_pro_to(self):
        """set toolmode move_po_pro_to for self.session_data.po_pro_feature.lr_geom_current"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if self.sys_set_tool_mode("move_po_pro_to"):
            self.dlg_select_po_pro_selection_row(
                self.session_data.po_pro_feature.data_fid
            )

            self.cvs_draw_lr_geom(
                self.session_data.po_pro_feature.lr_geom_current,
                ["snf", "ent", "snt", "sgn", "sg0", "rfl"],
                flash_markers=["ent"],
            )

            self.cvs_draw_lr_geom(
                self.session_data.po_pro_feature.lr_geom_cached,
                ["snfcaca", "sntcaca", "sg0caca"],
                flash_markers=["sntcaca"],
            )

    def cpe_move_po_pro_to(self, event):
        """canvasPressEvent for "move_po_pro_to"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
            | SVS.PO_PRO_REF_LAYER_CONNECTED
            | SVS.DATA_LAYER_EDITABLE
        ) in self.system_vs and self.session_data.po_pro_feature is not None:
            lr_geom_current = self.session_data.po_pro_feature.lr_geom_current
            lr_geom_cached = self.session_data.po_pro_feature.lr_geom_cached
            # snap to current geometry, not to ca_ca_lol.ref_geom
            snap_n_abs = self.tool_snap_to_ref_geom(
                event, lr_geom_current.reference_geom
            )

            if snap_n_abs is not None:

                self.session_data.snap_n_abs_mouse_down = snap_n_abs
                lr_geom_current.update_stationing_to(snap_n_abs, "Nabs")
                self.cvs_draw_lr_geom(
                    lr_geom_current,
                    ["snf", "ent", "snt", "sgn", "sg0", "rfl"],
                )

                self.cvs_draw_lr_geom(
                    lr_geom_cached,
                    ["snfcaca", "sntcaca", "sg0caca"],
                )

    def cme_move_po_pro_to(self, event):
        """canvasMoveEvent for "move_po_pro_to"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        if Qt.LeftButton & event.buttons():
            self.cpe_move_po_pro_to(event)

    def cre_move_po_pro_to(self, event):
        """canvasReleaseEvent for "move_po_pro_to"

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-13
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
            | SVS.PO_PRO_REF_LAYER_CONNECTED
            | SVS.DATA_LAYER_EDITABLE
        ) in self.system_vs and self.session_data.po_pro_feature is not None:
            self.cpe_move_po_pro_to(event)
            self.s_save_po_pro_feature()

        self.qact_pausing.trigger()

    def stm_set_to_point(self):
        """set tool mode 'set_to_point'"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if self.sys_set_tool_mode("set_to_point"):
            if self.session_data.lr_geom_runtime:
                self.cvs_draw_lr_geom(
                    self.session_data.lr_geom_runtime,
                    ["snf", "snt", "ent", "sgn", "sg0", "rfl"],
                    ["snf"],
                    ["snt", "sg0"],
                )

    def cpe_set_to_point(self, event: QgsMapMouseEvent):
        """canvas press for tool_mode 'set_to_point'
        Case distinction:
        1. lr_geom_runtime exists => active dragging from-position => update_stationing_to without snap if reference-feature matches
        2. no lr_geom_runtime => init new one setting from_stationing ==  to_stationing
        """
        # Rev. 2026-01-13
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                snap_n_abs = self.tool_snap_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
                if snap_n_abs is not None:
                    # 1. active dragging to-position:
                    self.session_data.lr_geom_runtime.update_stationing_to(
                        snap_n_abs, "Nabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "ent", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

            else:
                snap_result = self.tool_snap_to_ref_layer(event)
                if snap_result:
                    (ref_fid, snap_n_abs, match) = snap_result
                    # 2: new lr_geom_runtime mit staioning_from == stationing_to
                    lr_geom_runtime = LoL.init_by_stationings(
                        self.derived_settings.refLyr,
                        ref_fid,
                        snap_n_abs,
                        snap_n_abs,
                        self.session_data.current_offset,
                        "Nabs",
                    )
                    self.session_data.lr_geom_runtime = lr_geom_runtime
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "ent", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

    def cme_set_to_point(self, event: QgsMapMouseEvent):
        """canvas move for tool_mode 'set_to_point'
        Case distinction:
        1. lr_geom_runtime exists and left mouse button => active dragging to-position => no snap, but nearest point stationing
        2. lr_geom_runtime exists without mouse button => show snap on matching reference-feature
        3. no lr_geom_runtime => show snap on any reference line, create new lr_geom_runtime with next set_from_point_cpe
        """
        # Rev. 2026-01-13
        event_with_left_btn = bool(Qt.LeftButton & event.buttons())

        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                if event_with_left_btn:
                    snap_n_abs = self.tool_snap_to_ref_feature(
                        event, self.session_data.lr_geom_runtime.ref_fid
                    )
                    if snap_n_abs is not None:
                        # 1. active dragging to-position:
                        self.session_data.lr_geom_runtime.update_stationing_to(
                            snap_n_abs, "Nabs"
                        )
                        self.cvs_draw_lr_geom(
                            self.session_data.lr_geom_runtime,
                            ["snf", "snt", "ent", "sgn", "sg0", "rfl"],
                        )
                        self.dlg_populate_measurement()

                else:
                    # 2. mouse-move with lr_geom_runtime without mouse-button: show snap, if geometry matches
                    snap_result = self.tool_snap_to_ref_layer(event)
                    if snap_result:
                        (ref_fid, snap_n_abs, match) = snap_result
                        if ref_fid == self.session_data.lr_geom_runtime.ref_fid:
                            self.cvs_show_snap(match)
            else:
                # 3: mouse-move without lr_geom_runtime => show snap and highlight on any reference-geometry
                snap_result = self.tool_snap_to_ref_layer(event)
                if snap_result:
                    (ref_fid, snap_n_abs, match) = snap_result
                    self.cvs_show_snap(match)
                    self.dlg_select_qcbn_reference_feature(ref_fid)
                    self.cvs_draw_reference_geom(ref_fid=ref_fid)

    def cre_set_to_point(self, event: QgsMapMouseEvent):
        """canvas release for tool_mode 'set_to_point'
        if lr_geom_runtime exists: update its stationing_to
        """
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime:
                snap_n_abs = self.tool_snap_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
                if snap_n_abs is not None:
                    self.session_data.lr_geom_runtime.update_stationing_to(
                        snap_n_abs, "Nabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                    self.dlg_refract_measurement()
            else:
                raise RuntimeObjectMissingException("Digitized feature")

        self.qact_pausing.trigger()

    def stm_move_segment(self):
        """set tool mode 'move_segment'"""
        # Rev. 2026-01-13
        if self.sys_set_tool_mode("move_segment"):
            self.session_data.snap_n_abs_mouse_down = None
            self.cvs_draw_lr_geom(
                self.session_data.lr_geom_runtime,
                ["snf", "enf", "snt", "ent", "sgn", "sg0"],
                ["sgn", "sg0"],
                ["snf", "snt", "sg0"],
            )
            self.dlg_populate_measurement()

    def cpe_move_segment(self, event: QgsMapMouseEvent):
        """canvas press for tool_mode 'move_segment'"""
        # Rev. 2026-01-13
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime:
                self.session_data.snap_n_abs_mouse_down = self.tool_snap_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
            else:
                raise RuntimeObjectMissingException("Digitized feature")

    def cme_move_segment(self, event: QgsMapMouseEvent):
        """canvas move for tool_mode 'move_segment'"""
        # Rev. 2026-01-13
        if (
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
            and self.session_data.lr_geom_runtime
            and self.session_data.snap_n_abs_mouse_down is not None
        ):
            event_with_left_btn = bool(Qt.LeftButton & event.buttons())
            if event_with_left_btn:
                snap_n_abs = self.tool_snap_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )

                if snap_n_abs is not None:
                    delta = snap_n_abs - self.session_data.snap_n_abs_mouse_down
                    self.session_data.lr_geom_runtime.move_segment(delta)
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "enf", "ent", "sgn", "sg0"],
                    )
                    self.dlg_populate_measurement()

                    # store for next canvasMoveEvent
                    self.session_data.snap_n_abs_mouse_down = snap_n_abs

    def cre_move_segment(self, event: QgsMapMouseEvent):
        """canvas release for tool_mode 'move_segment'"""
        # Rev. 2026-01-13

        self.cvs_hide_markers()
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime:
                # no further calculation, take result from last move_segment_cme
                self.cvs_draw_lr_geom(
                    self.session_data.lr_geom_runtime,
                    ["snf", "snt", "sgn", "sg0", "rfl"],
                )
            else:
                raise RuntimeObjectMissingException("Digitized feature")

        self.qact_pausing.trigger()

    def stm_change_offset(self):
        """set tool mode 'change_offset'"""
        # Rev. 2026-01-13

        if self.sys_set_tool_mode("change_offset"):
            self.session_data.snap_n_abs_mouse_down = None
            self.cvs_draw_lr_geom(
                self.session_data.lr_geom_runtime,
                ["snf", "snt", "sgn", "sg0"],
                ["sgn", "sg0"],
                ["sgn", "sg0"],
            )
            self.dlg_populate_measurement()

    def cpe_change_offset(self, event: QgsMapMouseEvent):
        """canvas press for tool_mode 'change_offset'"""
        # Rev. 2026-01-13
        self.session_data.snap_n_abs_mouse_down = None
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                offset = self.tool_get_offset_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
                if offset is not None:
                    # store in session_data...
                    self.session_data.current_offset = offset

                    # ...and lr_geom_runtime
                    self.session_data.lr_geom_runtime.update_offset(offset)

                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
            else:
                raise RuntimeObjectMissingException("Digitized feature")

    def cme_change_offset(self, event: QgsMapMouseEvent):
        """canvas move for tool_mode 'change_offset'"""
        # Rev. 2026-01-13
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                event_with_left_btn = bool(Qt.LeftButton & event.buttons())
                if event_with_left_btn:
                    # mouseMove after mousePress
                    offset = self.tool_get_offset_to_ref_feature(
                        event, self.session_data.lr_geom_runtime.ref_fid
                    )
                    if offset is not None:
                        # store in session_data...
                        self.session_data.current_offset = offset

                        # ...and lr_geom_runtime
                        self.session_data.lr_geom_runtime.update_offset(offset)

                        self.cvs_draw_lr_geom(
                            self.session_data.lr_geom_runtime, ["sgn", "sg0", "rfl"]
                        )
                        self.dlg_populate_measurement()

    def cre_change_offset(self, event: QgsMapMouseEvent):
        """canvas release for tool_mode 'change_offset'"""
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.lr_geom_runtime is not None:
                offset = self.tool_get_offset_to_ref_feature(
                    event, self.session_data.lr_geom_runtime.ref_fid
                )
                if offset is not None:
                    # store in session_data...
                    self.session_data.current_offset = offset

                    # ...and lr_geom_runtime
                    self.session_data.lr_geom_runtime.update_offset(offset)

                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                    self.dlg_refract_measurement()
            else:
                raise RuntimeObjectMissingException("Digitized feature")

        self.qact_pausing.trigger()

    def sys_save_feature(
        self,
        data_fid: int,
        lr_geom: LoL,
        auto_swap_stationings: bool = True,
    ) -> bool:
        """stores LoL to layer
        direct update without feature-form
        variant with feature-form: s_update_feature
        Args:
            data_fid (int): feature-ID, self.session_data.po_pro_feature.data_fid
            lr_geom (LoL): linear referenced geometry, self.session_data.lr_geom_runtime or self.session_data.po_pro_feature.lr_geom_current
            auto_swap_stationings (bool, optional): Ensure stationing_from < stationing_to. Defaults to True.

        Raises:
            GeometryNotMValidException
            LayerNotMEnabledException
            FeatureWithoutGeometryException
            FeatureNotFoundException
            LayerNotEditableException
            LayerNotRegisteredException

        Returns:
            bool: update_ok? bool else: Exception
        """
        # Rev. 2026-01-12

        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            if (
                SVS.DATA_LAYER_EDITABLE | SVS.DATA_LAYER_UPDATE_ENABLED
                in self.system_vs
            ):

                data_feature = self.tool_get_data_feature(data_fid=data_fid)

                ref_feature = self.tool_get_reference_feature(
                    ref_fid=lr_geom.ref_fid
                )

                if self.stored_settings.lrMode in ["Mabs", "Mfract"]:
                    # check obsolete, else there was no lr_geom_runtime...
                    if SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                        if lr_geom.linestring_statistics.m_valid:
                            raise GeometryNotMValidException(
                                lr_geom.linestring_statistics.m_error,
                                self.derived_settings.refLyr.name(),
                                lr_geom.ref_fid,
                            )
                    else:
                        # should not happen
                        raise LayerNotMEnabledException(
                            self.derived_settings.refLyr.name()
                        )

                stationing_from_xyz, stationing_to_xyz = (
                    lr_geom.get_stationings(self.stored_settings.lrMode)
                )

                if stationing_from_xyz > stationing_to_xyz:
                    if auto_swap_stationings:
                        # swap from-to-measurements
                        stationing_from_xyz, stationing_to_xyz = (
                            stationing_to_xyz,
                            stationing_from_xyz,
                        )

                        self.dlg_append_log_message(
                            "INFO", MY_DICT.tr("from_to_switched")
                        )

                offset = lr_geom.offset

                if self.stored_settings.storagePrecision >= 0:
                    stationing_from_xyz = (
                        math.floor(
                            stationing_from_xyz
                            * 10**self.stored_settings.storagePrecision
                        )
                        / 10**self.stored_settings.storagePrecision
                    )
                    stationing_to_xyz = (
                        math.floor(
                            stationing_to_xyz
                            * 10**self.stored_settings.storagePrecision
                        )
                        / 10**self.stored_settings.storagePrecision
                    )
                    offset = round(
                        offset, self.stored_settings.storagePrecision
                    )
                data_feature[
                    self.derived_settings.dataLyrReferenceField.name()
                ] = ref_feature[self.derived_settings.refLyrIdField.name()]

                data_feature[
                    self.derived_settings.dataLyrStationingFromField.name()
                ] = stationing_from_xyz

                data_feature[
                    self.derived_settings.dataLyrStationingToField.name()
                ] = stationing_to_xyz

                data_feature[
                    self.derived_settings.dataLyrOffsetField.name()
                ] = offset

                self.derived_settings.dataLyr.beginEditCommand(
                    "update_lol_feature"
                )
                self.derived_settings.dataLyr.updateFeature(data_feature)
                self.derived_settings.dataLyr.endEditCommand()

                return True

            else:
                raise LayerNotEditableException(self.derived_settings.dataLyr.name())
        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr")

    def tool_get_offset_to_ref_geom(
        self, event: QgsMapMouseEvent, reference_geom: QgsGeometry
    ) -> float:
        """return offset between event-point and event-point

        Args:
            event (QgsMapMouseEvent): canvas-event from QgsMapTool-XYZ.canvasMoveEvent/canvasPressEvent/canvasReleaseEvent
            reference_geom (QgsGeometry):

        Returns:
            float: <0 left, >0 right, ==0 on the line in digitize-direction
        """
        # Rev. 2026-01-13
        event_point_geom = QgsGeometry.fromPoint(QgsPoint(event.mapPoint()))
        event_point_geom.transform(
            QgsCoordinateTransform(
                self.iface.mapCanvas().mapSettings().destinationCrs(),
                self.derived_settings.refLyr.crs(),
                QgsProject.instance(),
            )
        )
        point_on_line = reference_geom.closestSegmentWithContext(
            event_point_geom.asPoint()
        )

        sqr_dist = point_on_line[0]
        side = point_on_line[3]
        abs_dist = math.sqrt(sqr_dist)
        offset = abs_dist * side * -1

        return offset

    def tool_get_offset_to_ref_feature(
        self, event: QgsMapMouseEvent, ref_fid: int
    ) -> float:
        """return offset between event-point and geometry defined by ref_fid

        Args:
            event (QgsMapMouseEvent): canvas-event from QgsMapTool-XYZ.canvasMoveEvent/canvasPressEvent/canvasReleaseEvent
            reference_geom (QgsGeometry):

        Returns:
            float:
        """
        # Rev. 2026-01-13
        reference_geom = self.tool_get_reference_geom(ref_fid=ref_fid)
        if reference_geom:
            return self.tool_get_offset_to_ref_geom(event, reference_geom)

    def dlg_init(self):
        """initializes the dialog"""
        # Rev. 2026-01-13

        # remove existing dialog
        if self.my_dialog:
            self.my_dialog.close()
            self.my_dialog = None

        self.my_dialog = LolDialog()

        # some custom signals
        self.my_dialog.dialog_close.connect(self.dlg_close)

        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.my_dialog)

        # properties for dock/undock/dockable
        self.my_dialog.setFeatures(
            QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetClosable
        )

        self.my_dialog.setFloating(True)

        start_pos_x = int(
            self.iface.mainWindow().x()
            + self.iface.mainWindow().width()
            - self.session_data.dlg_last_width
            - 20
        )
        start_pos_y = int(self.iface.mainWindow().y() + 200)
        self.my_dialog.move(start_pos_x, start_pos_y)

        self.my_dialog.setHidden(True)

        self.my_dialog.tbw_central.currentChanged.connect(
            self.s_tbw_central_currentChanged
        )

        # context-sensitive help
        self.my_dialog.qtb_show_help.clicked.connect(self.dlg_show_help)
        self.my_dialog.qtb_toggle_top_level.clicked.connect(self.dlg_toggle_top_level)

        # signal/slot assignments for dialog-widgets
        # Section "Measurement"
        if True:
            if True:
                # refLyr-dependend:

                self.my_dialog.qtb_measurement_data_layer.addAction(
                    self.qact_open_ref_table
                )

                self.my_dialog.qcbn_ref_lyr_select.currentIndexChanged.connect(
                    self.s_select_current_ref_fid
                )

                self.my_dialog.qtb_measurement_reference_layer.addAction(
                    self.qact_open_ref_form
                )

                self.my_dialog.qtb_measurement_reference_layer.addAction(
                    self.qact_zoom_ref_feature
                )

                self.my_dialog.qtb_measurement_reference_layer.addAction(
                    self.qact_select_in_ref_layer
                )

            if True:
                # measurement-dependend:
                self.my_dialog.dspbx_offset.valueChanged.connect(self.s_change_offset)

                self.my_dialog.dspbx_n_abs_from.valueChanged.connect(
                    self.s_n_abs_from_edited
                )
                self.my_dialog.dspbx_n_abs_to.valueChanged.connect(
                    self.s_n_abs_to_edited
                )
                self.my_dialog.dspbx_n_fract_from.valueChanged.connect(
                    self.s_n_fract_from_edited
                )
                self.my_dialog.dspbx_n_fract_to.valueChanged.connect(
                    self.s_n_fract_to_edited
                )

                self.my_dialog.dspbx_delta_n_abs.valueChanged.connect(
                    self.s_delta_n_abs_edited
                )
                self.my_dialog.dspbx_delta_n_fract.valueChanged.connect(
                    self.s_delta_n_fract_edited
                )

                self.my_dialog.dspbx_delta_m_abs.valueChanged.connect(
                    self.s_delta_m_abs_edited
                )
                self.my_dialog.dspbx_delta_m_fract.valueChanged.connect(
                    self.s_delta_m_fract_edited
                )

                self.my_dialog.dspbx_m_abs_from.valueChanged.connect(
                    self.s_m_abs_from_edited
                )
                self.my_dialog.dspbx_m_abs_to.valueChanged.connect(
                    self.s_m_abs_to_edited
                )
                self.my_dialog.dspbx_m_fract_from.valueChanged.connect(
                    self.s_m_fract_from_edited
                )
                self.my_dialog.dspbx_m_fract_to.valueChanged.connect(
                    self.s_m_fract_to_edited
                )

            if True:
                # QActions

                self.my_dialog.qtb_measurement_tools.addAction(self.qact_move_to_start)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_flip_down)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_move_down)
                self.my_dialog.qtb_measurement_tools.addWidget(MyToolbarSpacer())
                self.my_dialog.qtb_measurement_tools.addAction(
                    self.qact_measure_segment
                )
                self.my_dialog.qtb_measurement_tools.addWidget(MyToolbarSpacer())
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_move_up)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_flip_up)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_move_end)
                self.my_dialog.qtb_measurement_tools.addWidget(MyToolbarSpacer())
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_set_from_point)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_set_to_point)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_move_segment)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_change_offset)
                self.my_dialog.qtb_measurement_tools.addAction(self.qact_zoom_lr_geom)
                self.my_dialog.qtb_edit_data_feature_post.addAction(
                    self.qact_select_edit_feature
                )

                # Label for selected feature inside QToolBar
                self.qlbl_edit_data_feature = QLabel("")
                self.qlbl_edit_data_feature.setMinimumWidth(100)
                self.qlbl_edit_data_feature.setAlignment(Qt.AlignCenter)
                self.qlbl_edit_data_feature.setStyleSheet(
                    "border: 1px solid silver; padding: 2px;"
                )
                self.qlbl_edit_data_feature.setToolTip(MY_DICT.tr("edit_data_fid_ttp"))
                self.my_dialog.qtb_edit_data_feature_post.addWidget(
                    self.qlbl_edit_data_feature
                )

                self.my_dialog.qtb_edit_data_feature_post.addAction(
                    self.qact_toggle_edit_mode
                )
                self.my_dialog.qtb_edit_data_feature_post.addSeparator()
                self.my_dialog.qtb_edit_data_feature_post.addAction(
                    self.qact_show_edit_feature_form
                )
                self.my_dialog.qtb_edit_data_feature_post.addAction(
                    self.qact_update_feature
                )
                self.my_dialog.qtb_edit_data_feature_post.addSeparator()
                self.my_dialog.qtb_edit_data_feature_post.addAction(
                    self.qact_insert_feature
                )

        # Section "Feature-Selection":
        if True:
            self.my_dialog.qtb_feature_selection.addAction(
                self.qact_append_data_features
            )
            self.my_dialog.qtb_feature_selection.addAction(self.qact_select_from_table)
            self.my_dialog.qtb_feature_selection.addAction(self.qact_select_features)
            self.my_dialog.qtb_feature_selection.addAction(
                self.qact_zoom_feature_selection
            )
            self.my_dialog.qtb_feature_selection.addAction(
                self.qact_clear_feature_selection
            )
            self.my_dialog.qtb_feature_selection.addAction(
                self.qact_transfer_feature_selection
            )
            self.my_dialog.qtb_feature_selection.addAction(
                self.qact_filter_by_feature_selection
            )

        # PostProcessing-Section:
        if True:

            # Widgets and Actions in Post-Processing-Settings
            if True:

                self.my_dialog.qcbn_pp_ref_lyr.currentIndexChanged.connect(
                    self.ssc_pp_ref_lyr
                )

                self.my_dialog.qcbn_pp_ref_lyr_id_field.currentIndexChanged.connect(
                    self.ssc_pp_ref_lyr_id_field
                )

                self.my_dialog.qtb_po_pro_settings.addAction(
                    self.qact_open_po_pro_ref_lyr
                )

                self.my_dialog.qtb_po_pro_settings.addAction(
                    self.qact_create_po_pro_ref_lyr
                )

            # QToolBar qtb_po_pro (between settings and TreeView)
            if True:

                self.my_dialog.qtb_po_pro.addAction(self.qact_start_post_processing)
                self.my_dialog.qtb_po_pro.addAction(self.qact_zoom_po_pro_selection)
                self.my_dialog.qtb_po_pro.addAction(self.qact_clear_po_pro_selection)

            # QActions in qtb_po_pro_edit
            if True:
                self.my_dialog.qtb_po_pro_edit.addAction(
                    self.qact_toggle_po_pro_edit_mode
                )

                self.qlbl_po_pro_feature = QLabel("")
                self.qlbl_po_pro_feature.setMinimumWidth(100)
                self.qlbl_po_pro_feature.setMaximumHeight(30)
                self.qlbl_po_pro_feature.setAlignment(Qt.AlignCenter)
                self.qlbl_po_pro_feature.setStyleSheet(
                    "border: 1px solid silver; padding: 2px;"
                )
                self.qlbl_po_pro_feature.setToolTip(
                    MY_DICT.tr("no_po_pro_feature_selected")
                )
                self.my_dialog.qtb_po_pro_edit.addWidget(self.qlbl_po_pro_feature)

                self.my_dialog.qtb_po_pro_edit.addAction(
                    self.qact_move_po_pro_from_point
                )
                self.my_dialog.qtb_po_pro_edit.addAction(self.qact_move_po_pro_to_point)
                self.my_dialog.qtb_po_pro_edit.addAction(self.qact_move_po_pro_segment)

        # Section "Settings"
        if True:
            # action defined above
            self.my_dialog.qcbn_ref_lyr.currentIndexChanged.connect(self.ssc_ref_lyr)

            self.my_dialog.qtb_ref_layer_2.addAction(self.qact_open_ref_table)

            self.my_dialog.qtb_ref_layer_2.addAction(
                self.qact_define_ref_lyr_display_expression
            )
            self.my_dialog.qcbn_ref_lyr_id_field.currentIndexChanged.connect(
                self.ssc_ref_lyr_id_field
            )

            self.my_dialog.qcbn_data_lyr.currentIndexChanged.connect(self.ssc_data_lyr)

            self.my_dialog.qtb_data_layer_2.addAction(self.qact_open_data_table)

            self.my_dialog.qtb_data_layer_2.addAction(self.qact_create_data_lyr)

            self.my_dialog.qtb_data_layer_2.addAction(
                self.qact_define_data_lyr_display_expression
            )

            self.my_dialog.qcbn_data_lyr_id_field.currentIndexChanged.connect(
                self.ssc_data_lyr_id_field
            )
            self.my_dialog.qcbn_data_lyr_reference_field.currentIndexChanged.connect(
                self.ssc_data_lyr_reference_field
            )
            self.my_dialog.qcbn_data_lyr_offset_field.currentIndexChanged.connect(
                self.ssc_data_lyr_offset_field
            )
            self.my_dialog.qcbn_data_lyr_stationing_from_field.currentIndexChanged.connect(
                self.ssc_data_lyr_stationing_from_field
            )
            self.my_dialog.qcbn_data_lyr_stationing_to_field.currentIndexChanged.connect(
                self.ssc_data_lyr_stationing_to_field
            )
            self.my_dialog.qcbn_show_lyr.currentIndexChanged.connect(
                self.ssc_show_layer
            )

            self.my_dialog.qtb_show_layer.addAction(self.qact_open_show_tbl)

            self.my_dialog.qtb_show_layer.addAction(self.qact_create_show_lyr)

            self.my_dialog.qcbn_show_lyr_back_reference_field.currentIndexChanged.connect(
                self.ssc_show_layer_back_reference_field
            )

            self.my_dialog.qcb_lr_mode.currentIndexChanged.connect(self.scc_lr_mode)
            self.my_dialog.qcb_storage_precision.currentIndexChanged.connect(
                self.scc_storage_precision
            )
            self.my_dialog.qcb_display_precision.currentIndexChanged.connect(
                self.scc_display_precision
            )
            self.my_dialog.cb_snap_mode_vertex.stateChanged.connect(
                self.scc_change_snap_mode
            )
            self.my_dialog.cb_snap_mode_segment.stateChanged.connect(
                self.scc_change_snap_mode
            )
            self.my_dialog.cb_snap_mode_middle_of_segment.stateChanged.connect(
                self.scc_change_snap_mode
            )
            self.my_dialog.cb_snap_mode_line_endpoint.stateChanged.connect(
                self.scc_change_snap_mode
            )
            self.my_dialog.qsb_snap_tolerance.valueChanged.connect(
                self.scc_change_snap_tolerance
            )
        # section Message-Log
        if True:
            self.my_dialog.qtb_log_container.addAction(self.qact_check_log_messages)
            self.my_dialog.qtb_log_container.addAction(self.qact_clear_log_messages)

        # Hide some areas im Measurement-Tab
        self.my_dialog.cbx_edit_grp.setChecked(False)
        self.my_dialog.cbx_n_fract_grp.setChecked(False)
        self.my_dialog.cbx_m_abs_grp.setChecked(False)
        self.my_dialog.cbx_m_fract_grp.setChecked(False)
        self.my_dialog.cbx_z_grp.setChecked(False)
        self.my_dialog.cbx_snap_coords_grp.setChecked(False)
        self.dlg_reset()

        self.dlg_show_tab("measurement")

    def dlg_apply_number_format(self):
        """number-format locale-, settings and reference-layer depending"""
        # Rev. 2026-01-13
        # refresh my_locale
        self.my_locale = sys_get_locale()

        if self.my_dialog:
            # form-widgets for numerical inputs
            # locale: number-format (decimal-sign, thousend-separator)
            locale_apply_widgets = [
                self.my_dialog.dnspbx_canvas_x,
                self.my_dialog.dnspbx_canvas_y,
                self.my_dialog.dspbx_offset,
                self.my_dialog.dnspbx_snap_x_from,
                self.my_dialog.dnspbx_snap_x_to,
                self.my_dialog.dnspbx_snap_y_from,
                self.my_dialog.dnspbx_snap_y_to,
                self.my_dialog.dnspbx_z_from,
                self.my_dialog.dnspbx_z_to,
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_n_fract_from,
                self.my_dialog.dspbx_n_fract_to,
                self.my_dialog.dspbx_m_fract_from,
                self.my_dialog.dspbx_m_fract_to,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_n_fract,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dspbx_delta_m_fract,
                self.my_dialog.dnspbx_delta_z_abs,
            ]

            show_group_separator = not bool(
                self.my_locale.numberOptions() & QLocale.OmitGroupSeparator
            )
            for wdg in locale_apply_widgets:
                with QSignalBlocker(wdg):
                    wdg.setLocale(self.my_locale)
                    wdg.setGroupSeparatorShown(show_group_separator)

            # locale_apply_widgets without fractional-widgets
            precision_apply_widgets = [
                self.my_dialog.dnspbx_canvas_x,
                self.my_dialog.dnspbx_canvas_y,
                self.my_dialog.dspbx_offset,
                self.my_dialog.dnspbx_snap_x_from,
                self.my_dialog.dnspbx_snap_x_to,
                self.my_dialog.dnspbx_snap_y_from,
                self.my_dialog.dnspbx_snap_y_to,
                self.my_dialog.dnspbx_z_from,
                self.my_dialog.dnspbx_z_to,
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dnspbx_delta_z_abs,
            ]

            for wdg in precision_apply_widgets:
                with QSignalBlocker(wdg):
                    wdg.setDecimals(self.stored_settings.displayPrecision)

            if self.my_dialog and SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                # set default-step-width for spinbox-click depending on reference-layer-crs (degree/meter)
                default_step_apply_widgets = [
                    self.my_dialog.dspbx_n_abs_from,
                    self.my_dialog.dspbx_n_abs_to,
                    self.my_dialog.dspbx_m_abs_from,
                    self.my_dialog.dspbx_m_abs_to,
                    self.my_dialog.dspbx_offset,
                    self.my_dialog.dspbx_delta_n_abs,
                    self.my_dialog.dspbx_delta_m_abs,
                ]
                measure_default_step = self.eval_crs_units(
                    self.derived_settings.refLyr.crs()
                )[2]

                for dspbx in default_step_apply_widgets:
                    with QSignalBlocker(dspbx):
                        dspbx.default_step = measure_default_step

    def s_move_to_start(self):
        """moves current measured segment to stationing_from == 0 => start of reference-line"""
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.snap_to_start()
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_move_down(self):
        """moves point in direction start of reference-line, stationings getting smaller"""
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    # step-width dependend on refLyr-crs and keyboard-modifiers
                    delta = self.eval_crs_units(self.derived_settings.refLyr.crs())[2]
                    if check_mods("sc"):
                        delta *= 1000
                    elif check_mods("c"):
                        delta *= 10
                    elif check_mods("s"):
                        delta *= 100
                    self.session_data.lr_geom_runtime.move_segment(-delta)
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_move_up(self):
        """moves point in direction end of reference-line, stationings getting larger"""
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    # step-width dependend on refLyr-crs and keyboard-modifiers
                    delta = self.eval_crs_units(self.derived_settings.refLyr.crs())[2]
                    if check_mods("sc"):
                        delta *= 1000
                    elif check_mods("c"):
                        delta *= 10
                    elif check_mods("s"):
                        delta *= 100
                    self.session_data.lr_geom_runtime.move_segment(delta)
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_flip_down(self):
        """flips the segment in start-direction (down: stationings get smaller):
        old from-stationing becomes new to-stationing,
        new from-stationing becomes old from-stationing - segment-length"""
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.flip_down()
                    self.dlg_populate_measurement()
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_flip_up(self):
        """flips the segment in end-direction (up: stationings get bigger):
        old to-stationing becomes new from-stationing,
        new to-stationing becomes old to-stationing + segment-length"""
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.flip_up()
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_move_to_end(self):
        """moves point to end of reference-line, max stationings"""
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.snap_to_end()
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_draw_lr_geom_runtime(self):
        """draws/zooms self.session_data.lr_geom_runtime"""
        # Rev. 2026-01-13
        try:
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                extent_mode = self.tool_get_extent_mode_lol()

                if self.session_data.lr_geom_runtime is not None:
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["sgn", "sg0", "snf", "snt"],
                        ["sgn", "sg0"],
                        ["snf", "snt", "sgn"],
                        extent_mode,
                    )
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
        except Exception as e:
            self.sys_log_exception(e)

    def dlg_populate_feature_selection(self):
        """Refreshes complete Feature-Selection-Treeview:
        Stores some Qt-Properties, resets the model and restore the Qt-Properties
        formerly used My1nLayerTreeView
        is triggered by user or by any attribute-change of one of the listed features
        derived versions for PolEvt/LolEvt
        """
        # Rev. 2026-01-13

        if self.my_dialog:
            self.my_dialog.qtrv_feature_selection.blockSignals(True)

            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                # colors used as text-color to symbolize OK (green), Error (red), unclear (orange) values
                # white = QColor("#ffffffff")
                red = QColor("#ffff0000")
                # red_trans = QColor("#aaff0000")
                green = QColor("#ff008800")
                # blue =  QColor("#ff0000ff")
                # blue_trans = QColor("#aa0000ff")
                orange = QColor("#ffff7738")

                # font used inside qtrv_feature_selection
                default_font = self.my_dialog.qtrv_feature_selection.font()

                # ExtraBold to symbolize failures/problems
                bold_font = QFont(default_font)
                bold_font.setWeight(81)
                # Features from Data- and Reference-Layer will show their PK and the evaluated displayExpression
                data_context = QgsExpressionContext()
                data_display_exp = QgsExpression(
                    self.derived_settings.dataLyr.displayExpression()
                )
                data_display_exp.prepare(data_context)
                ref_context = QgsExpressionContext()
                ref_display_exp = QgsExpression(
                    self.derived_settings.refLyr.displayExpression()
                )
                ref_display_exp.prepare(ref_context)
                root_item = (
                    self.my_dialog.qtrv_feature_selection.model().invisibleRootItem()
                )
                ok_ref_fids = dict()
                fail_ref_ids = dict()
                no_ref_data_fids = dict()
                fail_data_fids = set()

                for data_fid in self.session_data.selected_data_fids:
                    try:
                        data_feature = self.tool_get_data_feature(data_fid=data_fid)
                        ref_id = data_feature[
                            self.derived_settings.dataLyrReferenceField.name()
                        ]
                        if check_attribute_value(ref_id):

                            try:
                                ref_feature = self.tool_get_reference_feature(ref_id=ref_id)
                                ref_fid = ref_feature.id()
                                ok_ref_fids.setdefault(ref_fid, [])
                                ok_ref_fids[ref_fid].append(data_feature.id())
                            except:
                                fail_ref_ids.setdefault(ref_id, [])
                                fail_ref_ids[ref_id].append(data_feature.id())
                        else:
                            no_ref_data_fids[data_fid] = data_feature.id()
                    except Exception as e:
                        fail_data_fids.add(data_fid)

                # valid reference- and data-feature-iteration
                for ref_fid, assigned_data_fids in ok_ref_fids.items():
                    reference_item = MyStandardItem()
                    reference_function_item = MyStandardItem()
                    reference_item_cell_widget = MyCellWidget()
                    reference_function_cell_widget = MyCellWidget()

                    ref_feature = self.derived_settings.refLyr.getFeature(ref_fid)

                    ref_context.setFeature(ref_feature)
                    display_exp = ref_display_exp.evaluate(ref_context)
                    reference_item.setText(str(display_exp))

                    # falls @id als display-expression definiert ist, ist der evaluierte Ausdruck numerisch und die Sortierung ebenfalls!
                    reference_item.setData(display_exp, Qt_Roles.CUSTOM_SORT)
                    reference_item.setData(ref_fid, Qt_Roles.REF_FID)
                    # Tooltip with feature-id and the display-expression
                    reference_item.setData(f"#{ref_fid} {display_exp}", Qt.ToolTipRole)

                    root_item.appendRow(
                        [
                            reference_item,
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            reference_function_item,
                        ]
                    )

                    qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                    qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                    qtb.pressed.connect(
                        lambda data_fids=assigned_data_fids: self.st_remove_from_feature_selection(
                            data_fids
                        )
                    )
                    reference_item_cell_widget.layout().addWidget(qtb)

                    linestring_statistics = LinestringStatistics(ref_feature.geometry())
                    reference_geom_valid = True
                    reference_geom_invalid_reason = ""
                    if self.stored_settings.lrMode in ["Nabs", "Nfract"]:
                        reference_geom_valid = (
                            linestring_statistics.invalid_reason is None
                        )
                        reference_geom_invalid_reason = (
                            linestring_statistics.invalid_reason
                        )
                    elif self.stored_settings.lrMode == "Mabs":
                        reference_geom_valid = linestring_statistics.m_valid
                        reference_geom_invalid_reason = linestring_statistics.m_error

                    if reference_geom_valid:
                        qtb = MyToolButton(
                            QIcon(":icons/Green_check_icon_with_gradient.svg"),
                            MY_DICT.tr("qtrv_reference_feature_valid_ttp"),
                            cursor=Qt.ArrowCursor,
                        )
                        reference_function_cell_widget.layout().addWidget(qtb)
                    else:
                        qtb = MyToolButton(
                            QIcon(":icons/alert-outline.svg"),
                            MY_DICT.tr(
                                "qtrv_reference_feature_invalid_ttp",
                                reference_geom_invalid_reason,
                            ),
                            cursor=Qt.ForbiddenCursor,
                        )

                        reference_function_cell_widget.layout().addWidget(qtb)

                        reference_item.setData(red, Qt.ForegroundRole)

                    qtb = MyToolButton(
                        QIcon(":icons/mActionFormView.svg"),
                        MY_DICT.tr("show_feature_form_ref_lyr_ttp"),
                    )
                    qtb.pressed.connect(
                        lambda ref_fid=ref_fid: self.st_show_reference_feature_form(
                            ref_fid
                        )
                    )
                    reference_function_cell_widget.layout().addWidget(qtb)

                    qtb = MyToolButton(
                        QIcon(":icons/select_in_layer.svg"),
                        MY_DICT.tr("select_in_layer_ttp"),
                    )
                    qtb.pressed.connect(
                        lambda ref_fid=ref_fid: select_in_layer(
                            self.stored_settings.refLyrId, ref_fid, self.iface
                        )
                    )
                    reference_function_cell_widget.layout().addWidget(qtb)

                    if linestring_statistics.invalid_reason is None:
                        qtb = MyToolButton(
                            QIcon(":icons/zoom_pan.svg"),
                            MY_DICT.tr("zoom_ref_feature_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda ref_fid=ref_fid: self.st_zoom_reference_feature(
                                ref_fid
                            )
                        )
                        reference_function_cell_widget.layout().addWidget(qtb)
                    else:
                        qtb = MyToolButton(
                            QIcon(":icons/zoom_pan.svg"),
                            MY_DICT.tr(
                                "qtrv_reference_feature_invalid_ttp",
                                reference_geom_invalid_reason,
                            ),
                        )
                        qtb.setDisabled(True)
                        reference_function_cell_widget.layout().addWidget(qtb)

                    self.my_dialog.qtrv_feature_selection.setIndexWidget(
                        reference_item.index(), reference_item_cell_widget
                    )

                    self.my_dialog.qtrv_feature_selection.setIndexWidget(
                        reference_function_item.index(), reference_function_cell_widget
                    )

                    for assigned_data_fid in assigned_data_fids:
                        id_item = MyStandardItem()
                        id_item_cell_widget = MyCellWidget()

                        id_function_item = MyStandardItem()
                        id_function_cell_widget = MyCellWidget()

                        assigned_data_feature = (
                            self.derived_settings.dataLyr.getFeature(assigned_data_fid)
                        )
                        this_row_items = []

                        data_context.setFeature(assigned_data_feature)
                        display_exp = str(data_display_exp.evaluate(data_context))

                        tool_tip = f"#{assigned_data_fid}"

                        if assigned_data_fid < 0:
                            display_exp += " *"
                            tool_tip += " (uncommitted)"

                        id_item.setData(display_exp, Qt_Roles.CUSTOM_SORT)
                        id_item.setData(assigned_data_fid, Qt_Roles.DATA_FID)
                        id_item.setData(tool_tip, Qt.ToolTipRole)

                        id_item.setText(display_exp)
                        id_item.setTextAlignment(Qt.AlignLeft)

                        # first item is blank
                        this_row_items.append(MyStandardItem())
                        this_row_items.append(id_item)

                        qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                        qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_remove_from_feature_selection(
                                [data_fid]
                            )
                        )
                        id_item_cell_widget.layout().addWidget(qtb)

                        if "True":
                            stationing_from_item = MyStandardItem()
                            stationing_from_item.setTextAlignment(Qt.AlignRight)

                            stationing_from_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrStationingFromFieldName
                            ]

                            stationing_from_error = ""
                            stationing_from_text = self.tool_format_number(
                                stationing_from_xyz
                            )
                            stationing_from_value = None
                            stationing_from_color = green
                            stationing_from_font = default_font

                            if stationing_from_text != "NaN":
                                stationing_from_value = stationing_from_xyz

                                if reference_geom_valid:
                                    if self.stored_settings.lrMode == "Nabs":
                                        if not (
                                            0
                                            <= stationing_from_xyz
                                            <= linestring_statistics.length
                                        ):
                                            stationing_from_color = red
                                            stationing_from_font = bold_font
                                            stationing_from_error = (
                                                "stationing_from_out_of_bounds"
                                            )
                                    elif self.stored_settings.lrMode == "Nfract":
                                        if not (0 <= stationing_from_xyz <= 1):
                                            stationing_from_color = red
                                            stationing_from_font = bold_font
                                            stationing_from_error = (
                                                "stationing_from_out_of_bounds"
                                            )
                                    elif self.stored_settings.lrMode == "Mabs":
                                        if not (
                                            linestring_statistics.m_min
                                            <= stationing_from_xyz
                                            <= linestring_statistics.m_max
                                        ):
                                            stationing_from_color = red
                                            stationing_from_font = bold_font
                                            stationing_from_error = (
                                                "stationing_from_out_of_bounds"
                                            )
                                else:
                                    stationing_from_color = orange
                                    stationing_from_font = bold_font
                                    stationing_from_error = (
                                        reference_geom_invalid_reason
                                    )
                            else:
                                stationing_from_color = red
                                stationing_from_font = bold_font
                                stationing_from_error = "stationing_from_not_numeric"

                            stationing_from_item.setData(
                                stationing_from_text, Qt.DisplayRole
                            )
                            stationing_from_item.setData(
                                stationing_from_error, Qt.ToolTipRole
                            )
                            stationing_from_item.setData(
                                stationing_from_color, Qt.ForegroundRole
                            )
                            stationing_from_item.setData(
                                stationing_from_font, Qt.FontRole
                            )
                            stationing_from_item.setData(
                                stationing_from_value, Qt_Roles.CUSTOM_SORT
                            )

                            this_row_items.append(stationing_from_item)

                        if True:
                            stationing_to_item = MyStandardItem()
                            stationing_to_item.setTextAlignment(Qt.AlignRight)

                            stationing_to_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrStationingToFieldName
                            ]

                            stationing_to_error = ""
                            stationing_to_text = self.tool_format_number(
                                stationing_to_xyz
                            )
                            stationing_to_value = None
                            stationing_to_color = green
                            stationing_to_font = default_font

                            if stationing_to_text != "NaN":
                                stationing_to_value = stationing_to_xyz
                                if reference_geom_valid:
                                    if self.stored_settings.lrMode == "Nabs":
                                        if not (
                                            0
                                            <= stationing_to_xyz
                                            <= linestring_statistics.length
                                        ):
                                            stationing_to_color = red
                                            stationing_to_font = bold_font
                                            stationing_to_error = (
                                                "stationing_to_out_of_bounds"
                                            )
                                    elif self.stored_settings.lrMode == "Nfract":
                                        if not (0 <= stationing_to_xyz <= 1):
                                            stationing_to_color = red
                                            stationing_to_font = bold_font
                                            stationing_to_error = (
                                                "stationing_to_out_of_bounds"
                                            )
                                    elif self.stored_settings.lrMode == "Mabs":
                                        if not (
                                            linestring_statistics.m_min
                                            <= stationing_to_xyz
                                            <= linestring_statistics.m_max
                                        ):
                                            stationing_to_color = red
                                            stationing_to_font = bold_font
                                            stationing_to_error = (
                                                "stationing_to_out_of_bounds"
                                            )
                                else:
                                    stationing_to_color = orange
                                    stationing_to_font = bold_font
                                    stationing_to_error = reference_geom_invalid_reason
                            else:

                                stationing_to_color = red
                                stationing_to_font = bold_font
                                stationing_to_error = "stationing_to_not_numeric"

                            stationing_to_item.setData(
                                stationing_to_text, Qt.DisplayRole
                            )
                            stationing_to_item.setData(
                                stationing_to_error, Qt.ToolTipRole
                            )
                            stationing_to_item.setData(
                                stationing_to_color, Qt.ForegroundRole
                            )
                            stationing_to_item.setData(
                                stationing_from_font, Qt.FontRole
                            )
                            stationing_to_item.setData(
                                stationing_to_value, Qt_Roles.CUSTOM_SORT
                            )

                            this_row_items.append(stationing_to_item)

                        if True:
                            offset_item = MyStandardItem()
                            offset_item.setTextAlignment(Qt.AlignRight)

                            offset_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrOffsetFieldName
                            ]

                            offset_error = ""
                            offset_text = self.tool_format_number(offset_xyz)
                            offset_value = None
                            offset_color = green
                            offset_font = default_font

                            if offset_text != "NaN":
                                offset_value = offset_xyz

                                if not reference_geom_valid:
                                    offset_color = orange
                                    offset_font = bold_font
                                    offset_error = reference_geom_invalid_reason
                            else:
                                offset_color = red
                                offset_font = bold_font
                                offset_error = "offset_not_numeric"
                            offset_item.setData(offset_text, Qt.DisplayRole)
                            offset_item.setData(offset_error, Qt.ToolTipRole)
                            offset_item.setData(offset_color, Qt.ForegroundRole)
                            offset_item.setData(offset_font, Qt.FontRole)
                            offset_item.setData(offset_value, Qt_Roles.CUSTOM_SORT)
                            this_row_items.append(offset_item)

                        this_row_items.append(id_function_item)

                        reference_item.appendRow(this_row_items)

                        if (
                            not stationing_from_error
                            and not stationing_to_error
                            and not offset_error
                        ):
                            qtb = MyToolButton(
                                QIcon(":icons/Green_check_icon_with_gradient.svg"),
                                MY_DICT.tr("qtrv_feature_selection_feature_valid_ttp"),
                            )
                            id_function_cell_widget.layout().addWidget(qtb)
                        else:
                            # set => unique values
                            joined_error = " ".join(
                                set(
                                    [
                                        stationing_from_error,
                                        stationing_to_error,
                                        offset_error,
                                    ]
                                )
                            )
                            qtb = MyToolButton(
                                QIcon(":icons/alert-outline.svg"),
                                MY_DICT.tr(
                                    "qtrv_feature_selection_feature_invalid_ttp",
                                    joined_error,
                                ),
                                cursor=Qt.ForbiddenCursor,
                            )
                            id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyToolButton(
                            QIcon(":icons/mActionFormView.svg"),
                            MY_DICT.tr("show_feature_form_data_lyr_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_show_data_feature_form(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyToolButton(
                            QIcon(":icons/select_in_layer.svg"),
                            MY_DICT.tr("select_in_layer_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_select_in_layer(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        # append edit-tools only if the linear referenced geometry is valid
                        if (
                            not stationing_from_error
                            and not stationing_to_error
                            and not offset_error
                        ):

                            qtb = MyToolButton(
                                QIcon(":icons/zoom_pan.svg"),
                                MY_DICT.tr("zoom_data_feature_ttp"),
                            )
                            qtb.pressed.connect(
                                lambda data_fid=assigned_data_fid: self.st_zoom_data_feature(
                                    data_fid
                                )
                            )
                            id_function_cell_widget.layout().addWidget(qtb)

                            qtb = MyToolButton(
                                QIcon(":icons/move_segment.svg"),
                                MY_DICT.tr("set_edit_feature_ttp"),
                            )
                            qtb.pressed.connect(
                                lambda data_fid=assigned_data_fid: self.st_set_edit_feature(
                                    data_fid
                                )
                            )
                            id_function_cell_widget.layout().addWidget(qtb)
                        else:
                            # set => unique values
                            joined_error = " ".join(
                                set(
                                    [
                                        stationing_from_error,
                                        stationing_to_error,
                                        offset_error,
                                    ]
                                )
                            )
                            qtb = MyToolButton(
                                QIcon(":icons/zoom_pan.svg"),
                                MY_DICT.tr(
                                    "qtrv_feature_selection_feature_invalid_ttp",
                                    joined_error,
                                )
                            )
                            qtb.setDisabled(True)
                            id_function_cell_widget.layout().addWidget(qtb)

                            qtb = MyToolButton(
                                QIcon(":icons/move_segment.svg"),
                                MY_DICT.tr(
                                    "qtrv_feature_selection_feature_invalid_ttp",
                                    joined_error,
                                )
                            )
                            qtb.setDisabled(True)
                            id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyDeleteToolButton(
                            QIcon(":icons/mActionDeleteSelectedFeatures.svg"),
                            MY_DICT.tr("delete_feature_qtb_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_delete_data_feature(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        self.my_dialog.qtrv_feature_selection.setIndexWidget(
                            id_item.index(), id_item_cell_widget
                        )

                        self.my_dialog.qtrv_feature_selection.setIndexWidget(
                            id_function_item.index(), id_function_cell_widget
                        )

                # invalid reference- with assigned data-feature-iteration
                for ref_id, assigned_data_fids in fail_ref_ids.items():
                    reference_item = MyStandardItem()
                    reference_function_item = MyStandardItem()
                    reference_item_cell_widget = MyCellWidget()
                    reference_function_cell_widget = MyCellWidget()

                    reference_item.setText(
                        MY_DICT.tr(
                            "qtrv_feature_selection_unknown_ref_id_txt",
                            ref_id,
                        )
                    )

                    # falls @id als display-expression definiert ist, ist der evaluierte Ausdruck numerisch und die Sortierung ebenfalls!
                    reference_item.setData(
                        MY_DICT.tr(
                            "qtrv_feature_selection_unknown_ref_id_ttp",
                            ref_id,
                        ),
                        Qt.ToolTipRole,
                    )

                    reference_item.setData(red, Qt.ForegroundRole)
                    reference_item.setData(bold_font, Qt.FontRole)

                    root_item.appendRow(
                        [
                            reference_item,
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            reference_function_item,
                        ]
                    )

                    qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                    qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                    qtb.pressed.connect(
                        lambda data_fids=assigned_data_fids: self.st_remove_from_feature_selection(
                            data_fids
                        )
                    )
                    reference_item_cell_widget.layout().addWidget(qtb)

                    qtb = MyToolButton(
                        QIcon(":icons/alert-outline.svg"),
                        MY_DICT.tr("qtrv_feature_selection_unknown_ref_id_ttp", ref_id),
                        cursor=Qt.ForbiddenCursor,
                    )

                    reference_function_cell_widget.layout().addWidget(qtb)

                    self.my_dialog.qtrv_feature_selection.setIndexWidget(
                        reference_item.index(), reference_item_cell_widget
                    )

                    self.my_dialog.qtrv_feature_selection.setIndexWidget(
                        reference_function_item.index(), reference_function_cell_widget
                    )

                    for assigned_data_fid in assigned_data_fids:
                        id_item = MyStandardItem()
                        id_item_cell_widget = MyCellWidget()

                        id_function_item = MyStandardItem()
                        id_function_cell_widget = MyCellWidget()

                        assigned_data_feature = (
                            self.derived_settings.dataLyr.getFeature(assigned_data_fid)
                        )
                        this_row_items = []

                        data_context.setFeature(assigned_data_feature)
                        display_exp = str(data_display_exp.evaluate(data_context))
                        tool_tip = f"#{assigned_data_fid}"

                        if assigned_data_fid < 0:
                            display_exp += " *"
                            tool_tip += " (uncommitted)"

                        id_item.setData(display_exp, Qt_Roles.CUSTOM_SORT)
                        id_item.setData(assigned_data_fid, Qt_Roles.DATA_FID)
                        id_item.setData(tool_tip, Qt.ToolTipRole)

                        id_item.setText(display_exp)
                        id_item.setTextAlignment(Qt.AlignLeft)

                        # first item is blank
                        this_row_items.append(MyStandardItem())
                        this_row_items.append(id_item)

                        qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                        qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_remove_from_feature_selection(
                                [data_fid]
                            )
                        )
                        id_item_cell_widget.layout().addWidget(qtb)

                        if True:

                            stationing_from_item = MyStandardItem()
                            stationing_from_item.setTextAlignment(Qt.AlignRight)

                            stationing_from_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrStationingFromFieldName
                            ]

                            stationing_from_error = (
                                "no reference-geometry, stationing not verifiable"
                            )
                            stationing_from_text = self.tool_format_number(
                                stationing_from_xyz
                            )
                            stationing_from_value = None
                            stationing_from_color = orange
                            stationing_from_font = default_font

                            if stationing_from_text != "NaN":
                                stationing_from_value = stationing_from_xyz
                            else:
                                stationing_from_color = red
                                stationing_from_font = bold_font
                                stationing_from_error = "stationing_from_not_numeric"

                            stationing_from_item.setData(
                                stationing_from_text, Qt.DisplayRole
                            )
                            stationing_from_item.setData(
                                stationing_from_error, Qt.ToolTipRole
                            )
                            stationing_from_item.setData(
                                stationing_from_color, Qt.ForegroundRole
                            )
                            stationing_from_item.setData(
                                stationing_from_font, Qt.FontRole
                            )
                            stationing_from_item.setData(
                                stationing_from_value, Qt_Roles.CUSTOM_SORT
                            )

                            this_row_items.append(stationing_from_item)

                        if True:

                            stationing_to_item = MyStandardItem()
                            stationing_to_item.setTextAlignment(Qt.AlignRight)

                            stationing_to_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrStationingToFieldName
                            ]

                            stationing_to_error = (
                                "no reference-geometry, stationing not verifiable"
                            )
                            stationing_to_text = self.tool_format_number(
                                stationing_to_xyz
                            )
                            stationing_to_value = None
                            stationing_to_color = orange
                            stationing_to_font = default_font

                            if stationing_to_text != "NaN":
                                stationing_to_value = stationing_to_xyz
                            else:
                                stationing_to_color = red
                                stationing_to_font = bold_font
                                stationing_to_error = "stationing_to_not_numeric"

                            stationing_to_item.setData(
                                stationing_to_text, Qt.DisplayRole
                            )
                            stationing_to_item.setData(
                                stationing_to_error, Qt.ToolTipRole
                            )
                            stationing_to_item.setData(
                                stationing_to_color, Qt.ForegroundRole
                            )
                            stationing_to_item.setData(stationing_to_font, Qt.FontRole)
                            stationing_to_item.setData(
                                stationing_to_value, Qt_Roles.CUSTOM_SORT
                            )

                            this_row_items.append(stationing_to_item)

                        if True:
                            offset_item = MyStandardItem()
                            offset_item.setTextAlignment(Qt.AlignRight)

                            offset_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrOffsetFieldName
                            ]

                            offset_error = "no reference-geometry"
                            offset_text = self.tool_format_number(offset_xyz)
                            offset_value = None
                            offset_color = orange
                            offset_font = default_font

                            if offset_text != "NaN":
                                offset_value = offset_xyz

                            else:
                                offset_color = red
                                offset_font = bold_font
                                offset_error = "offset_not_numeric"

                            offset_item.setData(offset_text, Qt.DisplayRole)
                            offset_item.setData(offset_error, Qt.ToolTipRole)
                            offset_item.setData(offset_color, Qt.ForegroundRole)
                            offset_item.setData(offset_font, Qt.FontRole)
                            offset_item.setData(offset_value, Qt_Roles.CUSTOM_SORT)
                            this_row_items.append(offset_item)

                        this_row_items.append(id_function_item)
                        reference_item.appendRow(this_row_items)

                        qtb = MyToolButton(
                            QIcon(":icons/alert-outline.svg"),
                            MY_DICT.tr(
                                "qtrv_feature_selection_unknown_ref_id_ttp", ref_id
                            ),
                            cursor=Qt.ForbiddenCursor,
                        )

                        id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyToolButton(
                            QIcon(":icons/mActionFormView.svg"),
                            MY_DICT.tr("show_feature_form_data_lyr_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_show_data_feature_form(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyToolButton(
                            QIcon(":icons/select_in_layer.svg"),
                            MY_DICT.tr("select_in_layer_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_select_in_layer(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyDeleteToolButton(
                            QIcon(":icons/mActionDeleteSelectedFeatures.svg"),
                            MY_DICT.tr("delete_feature_qtb_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_delete_data_feature(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        self.my_dialog.qtrv_feature_selection.setIndexWidget(
                            id_item.index(), id_item_cell_widget
                        )

                        self.my_dialog.qtrv_feature_selection.setIndexWidget(
                            id_function_item.index(), id_function_cell_widget
                        )

                # data-feature-iteration with no ref_id
                if no_ref_data_fids:
                    reference_item = MyStandardItem()
                    reference_function_item = MyStandardItem()
                    reference_item_cell_widget = MyCellWidget()
                    reference_function_cell_widget = MyCellWidget()

                    reference_item.setText(
                        MY_DICT.tr("qtrv_feature_selection_no_ref_id_txt")
                    )

                    # falls @id als display-expression definiert ist, ist der evaluierte Ausdruck numerisch und die Sortierung ebenfalls!
                    reference_item.setData(
                        MY_DICT.tr(
                            "qtrv_feature_selection_no_ref_id_ttp",
                        ),
                        Qt.ToolTipRole,
                    )

                    reference_item.setData(red, Qt.ForegroundRole)
                    reference_item.setData(bold_font, Qt.FontRole)

                    root_item.appendRow(
                        [
                            reference_item,
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            reference_function_item,
                        ]
                    )

                    qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                    qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                    qtb.pressed.connect(
                        lambda data_fids=no_ref_data_fids: self.st_remove_from_feature_selection(
                            data_fids
                        )
                    )
                    reference_item_cell_widget.layout().addWidget(qtb)

                    qtb = MyToolButton(
                        QIcon(":icons/alert-outline.svg"),
                        MY_DICT.tr("qtrv_feature_selection_no_ref_id_ttp"),
                        cursor=Qt.ForbiddenCursor,
                    )

                    reference_function_cell_widget.layout().addWidget(qtb)

                    self.my_dialog.qtrv_feature_selection.setIndexWidget(
                        reference_item.index(), reference_item_cell_widget
                    )

                    self.my_dialog.qtrv_feature_selection.setIndexWidget(
                        reference_function_item.index(), reference_function_cell_widget
                    )

                    for assigned_data_fid in no_ref_data_fids:
                        id_item = MyStandardItem()
                        id_item_cell_widget = MyCellWidget()

                        id_function_item = MyStandardItem()
                        id_function_cell_widget = MyCellWidget()

                        assigned_data_feature = (
                            self.derived_settings.dataLyr.getFeature(assigned_data_fid)
                        )
                        this_row_items = []

                        data_context.setFeature(assigned_data_feature)
                        display_exp = str(data_display_exp.evaluate(data_context))
                        tool_tip = f"#{assigned_data_fid}"
                        if assigned_data_fid < 0:
                            display_exp += " *"
                            tool_tip += " (uncommitted)"

                        id_item.setData(display_exp, Qt_Roles.CUSTOM_SORT)
                        id_item.setData(assigned_data_fid, Qt_Roles.DATA_FID)
                        id_item.setData(tool_tip, Qt.ToolTipRole)

                        id_item.setText(display_exp)
                        id_item.setTextAlignment(Qt.AlignLeft)

                        # first item is blank
                        this_row_items.append(MyStandardItem())
                        this_row_items.append(id_item)

                        qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                        qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_remove_from_feature_selection(
                                [data_fid]
                            )
                        )
                        id_item_cell_widget.layout().addWidget(qtb)

                        if True:

                            stationing_from_item = MyStandardItem()
                            stationing_from_item.setTextAlignment(Qt.AlignRight)

                            stationing_from_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrStationingFromFieldName
                            ]

                            stationing_from_error = (
                                "no reference-geometry, stationing not verifiable"
                            )
                            stationing_from_text = self.tool_format_number(
                                stationing_from_xyz
                            )
                            stationing_from_value = None
                            stationing_from_color = orange
                            stationing_from_font = default_font

                            if stationing_from_text != "NaN":
                                stationing_from_value = stationing_from_xyz
                            else:
                                stationing_from_color = red
                                stationing_from_font = bold_font
                                stationing_from_error = "stationing_from_not_numeric"

                            stationing_from_item.setData(
                                stationing_from_text, Qt.DisplayRole
                            )
                            stationing_from_item.setData(
                                stationing_from_error, Qt.ToolTipRole
                            )
                            stationing_from_item.setData(
                                stationing_from_color, Qt.ForegroundRole
                            )
                            stationing_from_item.setData(
                                stationing_from_font, Qt.FontRole
                            )
                            stationing_from_item.setData(
                                stationing_from_value, Qt_Roles.CUSTOM_SORT
                            )

                            this_row_items.append(stationing_from_item)

                        if True:

                            stationing_to_item = MyStandardItem()
                            stationing_to_item.setTextAlignment(Qt.AlignRight)

                            stationing_to_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrStationingToFieldName
                            ]

                            stationing_to_error = (
                                "no reference-geometry, stationing not verifiable"
                            )
                            stationing_to_text = self.tool_format_number(
                                stationing_to_xyz
                            )
                            stationing_to_value = None
                            stationing_to_color = orange
                            stationing_to_font = default_font

                            if stationing_to_text != "NaN":
                                stationing_to_value = stationing_to_xyz
                            else:
                                stationing_to_color = red
                                stationing_to_font = bold_font
                                stationing_to_error = "stationing_to_not_numeric"

                            stationing_to_item.setData(
                                stationing_to_text, Qt.DisplayRole
                            )
                            stationing_to_item.setData(
                                stationing_to_error, Qt.ToolTipRole
                            )
                            stationing_to_item.setData(
                                stationing_to_color, Qt.ForegroundRole
                            )
                            stationing_to_item.setData(stationing_to_font, Qt.FontRole)
                            stationing_to_item.setData(
                                stationing_to_value, Qt_Roles.CUSTOM_SORT
                            )

                            this_row_items.append(stationing_to_item)

                        if True:
                            offset_item = MyStandardItem()
                            offset_item.setTextAlignment(Qt.AlignRight)

                            offset_xyz = assigned_data_feature[
                                self.stored_settings.dataLyrOffsetFieldName
                            ]

                            offset_error = "no reference-geometry"
                            offset_text = self.tool_format_number(offset_xyz)
                            offset_value = None
                            offset_color = orange
                            offset_font = default_font

                            if offset_text != "NaN":
                                offset_value = offset_xyz
                            else:
                                offset_color = red
                                offset_font = bold_font
                                offset_error = "offset_not_numeric"

                            offset_item.setData(offset_text, Qt.DisplayRole)
                            offset_item.setData(offset_error, Qt.ToolTipRole)
                            offset_item.setData(offset_color, Qt.ForegroundRole)
                            offset_item.setData(offset_font, Qt.FontRole)
                            offset_item.setData(offset_value, Qt_Roles.CUSTOM_SORT)
                            this_row_items.append(offset_item)

                        this_row_items.append(id_function_item)
                        reference_item.appendRow(this_row_items)

                        qtb = MyToolButton(
                            QIcon(":icons/alert-outline.svg"),
                            MY_DICT.tr("qtrv_feature_selection_no_ref_id_ttp"),
                            cursor=Qt.ForbiddenCursor,
                        )

                        id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyToolButton(
                            QIcon(":icons/mActionFormView.svg"),
                            MY_DICT.tr("show_feature_form_data_lyr_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_show_data_feature_form(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyToolButton(
                            QIcon(":icons/select_in_layer.svg"),
                            MY_DICT.tr("select_in_layer_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_select_in_layer(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        qtb = MyDeleteToolButton(
                            QIcon(":icons/mActionDeleteSelectedFeatures.svg"),
                            MY_DICT.tr("delete_feature_qtb_ttp"),
                        )
                        qtb.pressed.connect(
                            lambda data_fid=assigned_data_fid: self.st_delete_data_feature(
                                data_fid
                            )
                        )
                        id_function_cell_widget.layout().addWidget(qtb)

                        self.my_dialog.qtrv_feature_selection.setIndexWidget(
                            id_item.index(), id_item_cell_widget
                        )

                        self.my_dialog.qtrv_feature_selection.setIndexWidget(
                            id_function_item.index(), id_function_cell_widget
                        )

                if fail_data_fids:
                    # filter negative-fids, belonging to unsaved features
                    real_fail_data_fids = [fid for fid in fail_data_fids if fid >= 0]
                    if real_fail_data_fids:
                        self.dlg_append_log_message(
                            "INFO",
                            MY_DICT.tr("feature_selection_fail_data_fids", real_fail_data_fids),
                        )

                    self.session_data.selected_data_fids -= fail_data_fids

            QTimer.singleShot(10, self.dlg_feature_selection_apply_pre_settings)

            self.my_dialog.qtrv_feature_selection.blockSignals(False)

    def st_select_po_pro_feature(self, data_id: int | str):
        """selects po_pro_feature, draws/zooms current/cached-differences

        Args:
            data_id (int|str): id, not feature.id()
        """
        # Rev. 2026-01-13
        self.cvs_hide_markers()
        self.session_data.po_pro_feature = None
        extent_mode = self.tool_get_extent_mode_lol()
        if SVS.DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs:
            try:
                po_pro_feature = self.tool_init_po_pro_feature(data_id)
                self.session_data.po_pro_feature = po_pro_feature
                self.cvs_show_po_pro_difference(po_pro_feature, extent_mode)
                self.dlg_select_po_pro_selection_row(data_fid=po_pro_feature.data_fid)
            except Exception as e:
                self.dlg_append_log_message("WARNING", e)

        self.dlg_refresh_po_pro_edit()
        self.qact_pausing.trigger()

    def tool_init_po_pro_feature(self, data_id: int | str) -> PoProFeature:
        """inits PoProFeature with different reference-geometries and stationing from current and cached data
        the return-value can be stored as self.session_data.po_pro_feature

        Args:
            data_id (int | str): ID of DataLyr-Feature, not feature.id()

        Returns:
            PoProFeature
        """
        # Rev. 2026-01-13
        if SVS.DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs:
            if data_id in self.session_data.po_pro_cache:
                data_feature = self.tool_get_data_feature(data_id=data_id)

                stationing_from_xyz = data_feature[
                    self.derived_settings.dataLyrStationingFromField.name()
                ]
                stationing_to_xyz = data_feature[
                    self.derived_settings.dataLyrStationingToField.name()
                ]
                offset = data_feature[
                    self.derived_settings.dataLyrOffsetField.name()
                ]

                ref_id = data_feature[
                    self.derived_settings.dataLyrReferenceField.name()
                ]

                ref_feature = self.tool_get_reference_feature(ref_id=ref_id)
                # note: init_by_stationings, because lol_instance.ref_fid required for later update
                lol_instance = LoL.init_by_stationings(
                    self.derived_settings.refLyr,
                    ref_feature.id(),
                    stationing_from_xyz,
                    stationing_to_xyz,
                    offset,
                    self.stored_settings.lrMode,
                )

                if lol_instance:

                    po_pro_stationing_from_xyz = self.session_data.po_pro_cache[
                        data_id
                    ]["stationing_from"]
                    po_pro_stationing_to_xyz = self.session_data.po_pro_cache[
                        data_id
                    ]["stationing_to"]
                    po_pro_offset = self.session_data.po_pro_cache[data_id][
                        "offset"
                    ]
                    po_pro_ref_id = self.session_data.po_pro_cache[data_id][
                        "ref_id"
                    ]

                    po_pro_ref_feature = get_feature_by_value(
                        self.derived_settings.poProRefLyr,
                        self.derived_settings.poProRefLyrIdField,
                        po_pro_ref_id,
                    )

                    if po_pro_ref_feature.hasGeometry():
                        po_pro_lol_instance = LoL.init_by_reference_geom(
                            po_pro_ref_feature.geometry(),
                            self.derived_settings.poProRefLyr.crs(),
                            po_pro_stationing_from_xyz,
                            po_pro_stationing_to_xyz,
                            po_pro_offset,
                            self.stored_settings.lrMode,
                        )

                        if po_pro_lol_instance:
                            po_pro_feature = PoProFeature()

                            po_pro_feature.data_fid = data_feature.id()
                            po_pro_feature.data_id = data_id
                            po_pro_feature.ref_fid = ref_feature.id()
                            po_pro_feature.ref_id = ref_id
                            po_pro_feature.lr_geom_current = lol_instance
                            po_pro_feature.lr_geom_cached = po_pro_lol_instance
                            return po_pro_feature
                    else:
                        raise FeatureWithoutGeometryException(
                            self.derived_settings.poProRefLyr.name(),
                            po_pro_ref_id,
                        )

            else:
                raise NotInSelectionException("PostProcessing-Cache", data_id)

    def cvs_show_po_pro_difference(
        self, po_pro_feature: PoProFeature, extent_mode: str = None
    ):
        """Show differences of the two geometries in po_pro_feature

        Args:
            po_pro_feature (PoProFeature)
            extent_mode (str, optional): Defaults to None. See cvs_set_extent.
                - zoom_bounds
                - zoom_bounds_in
                - zoom_bounds_out
                - pan_center
                - pan_center_in
                - pan_center_out
                - pan_center_opt_in
                - pan_center_opt_out
                - canvas_in
                - canvas_out
        """
        # Rev. 2026-01-13

        if SVS.DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs:

            x_coords = []
            y_coords = []

            draw_markers = [
                "snf",
                "snt",
                "sgn",
                "sg0",
                "rfl",
            ]
            extent_markers = [
                "sgn",
                "sg0",
            ]

            flash_markers = [
                "sgn",
            ]

            x_coords, y_coords = self.cvs_draw_lr_geom(
                po_pro_feature.lr_geom_current,
                draw_markers,
                extent_markers,
                flash_markers,
            )

            po_pro_draw_markers = ["rflca", "sg0caca", "snfcaca", "sntcaca", "sgncaca"]
            po_pro_extent_markers = ["sgncaca", "sg0caca"]
            po_pro_flash_markers = [
                "sgncaca",
            ]

            po_pro_x_coords, po_pro_y_coords = self.cvs_draw_lr_geom(
                po_pro_feature.lr_geom_cached,
                po_pro_draw_markers,
                po_pro_extent_markers,
                po_pro_flash_markers,
            )

            x_coords += po_pro_x_coords
            y_coords += po_pro_y_coords

            if extent_mode:
                # coordinates transformed to canvas-crs
                self.cvs_set_extent(extent_mode, x_coords, y_coords)

    def tool_get_po_pro_lr_geom(
        self,
        data_id: int | str,
    ) -> LoL:
        """initializes LoL for PostProcessing-feature, used for cvs_draw_po_pro_selection

        Args:
            data_id (int | str): ID of Feature, not feature.id()

        Returns:
            LoL
        """
        # Rev. 2026-01-13

        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED
            in self.system_vs
        ):
            if data_id in self.session_data.po_pro_cache:

                # pre-check metadata from data_feature
                stationing_from_xyz = self.session_data.po_pro_cache[data_id][
                    "stationing_from"
                ]
                stationing_to_xyz = self.session_data.po_pro_cache[data_id][
                    "stationing_to"
                ]
                offset = self.session_data.po_pro_cache[data_id]["offset"]

                ref_id = self.session_data.po_pro_cache[data_id]["ref_id"]


                po_pro_ref_feature = self.tool_get_po_pro_reference_feature(
                    ref_id=ref_id
                )
                if po_pro_ref_feature.hasGeometry():
                    return LoL.init_by_reference_geom(
                        po_pro_ref_feature.geometry(),
                        self.derived_settings.poProRefLyr.crs(),
                        stationing_from_xyz,
                        stationing_to_xyz,
                        offset,
                        self.stored_settings.lrMode,
                    )
                else:
                    raise FeatureWithoutGeometryException(
                        self.derived_settings.poProRefLyr.name(), ref_id
                    )
            else:
                raise NotInSelectionException("PostProcessing-Cache", data_id)
        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr + PoProLyr")

    def tool_get_feature_lr_geom(
        self,
        data_fid: int = None,
        data_id: int | str = None,
        show_fid: int = None,
    ) -> LoL | None:
        """initializes LoL for data-feature

        Args:
            data_fid (int, optional): Feature-ID. Defaults to None.
            data_id (int | str, optional): ID of Feature, checked against dataLyrIdField. Defaults to None.
            show_fid (int, optional): Feature-ID of Show-Layer-Feature. Defaults to None.

        Returns:
            LoL|None
        """
        # Rev. 2026-01-13

        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            data_feature = self.tool_get_data_feature(
                data_fid, data_id, show_fid
            )

            stationing_from_xyz =  data_feature[
                self.derived_settings.dataLyrStationingFromField.name()
            ]

            stationing_to_xyz = data_feature[
                    self.derived_settings.dataLyrStationingToField.name()
                ]


            offset = data_feature[self.derived_settings.dataLyrOffsetField.name()]


            ref_id = data_feature[
                self.derived_settings.dataLyrReferenceField.name()
            ]

            ref_feature = self.tool_get_reference_feature(ref_id=ref_id)
            return LoL.init_by_stationings(
                self.derived_settings.refLyr,
                ref_feature.id(),
                stationing_from_xyz,
                stationing_to_xyz,
                offset,
                self.stored_settings.lrMode,
            )

        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr")

    def cvs_draw_po_pro_selection(
        self,
        draw_markers: list = ["sgn", "sgncaca"],
        extent_markers: list = ["sgn", "sg0", "sgncaca", "sg0caca"],
        flash_markers: list = [
            "sgn",
            "sgncaca",
            "snf_mp",
            "snt_mp",
            "snfcaca_mp",
            "sntcaca_mp",
        ],
        extent_mode: str = "zoom_bounds_out",
    ):
        """Draws and Zooms to current listed PostProcessing-Features

        Args:
            draw_markers (list, optional): Markers to be drawn on canvas. Defaults to ["sgn", "sgncaca"] (Too much: "snf_mp", "snt_mp","snfcaca_mp","sntcaca_mp")
            extent_markers (list, optional): Markers defining the Zoom-Extent. Defaults to ["sgn", "sg0", "sgncaca", "sg0caca"].
            flash_markers (list, optional): Markers to be flashed. Defaults to ["sgn", "sgncaca", "snf_mp", "snt_mp","snfcaca_mp","sntcaca_mp"].
            extent_mode (str, optional): Defaults to "zoom_bounds_out".
        """
        # Rev. 2026-01-13
        combined_markers = draw_markers + extent_markers + flash_markers

        diff_keys = list_difference(combined_markers, self.canvas_graphics.keys())
        if diff_keys:
            print("false keys", diff_keys)

        self.cvs_hide_markers(draw_markers)
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED
        ) in self.system_vs:

            if self.session_data.po_pro_cache:
                tr = QgsCoordinateTransform(
                    self.derived_settings.refLyr.crs(),
                    self.iface.mapCanvas().mapSettings().destinationCrs(),
                    QgsProject.instance(),
                )

                sgn_merge_geoms = []
                sg0_merge_geoms = []
                sgncaca_merge_geoms = []
                sg0caca_merge_geoms = []
                snf_merge_geoms = []
                snt_merge_geoms = []
                snfcaca_merge_geoms = []
                sntcaca_merge_geoms = []

                fail_data_ids = []

                for data_id in self.session_data.po_pro_cache:

                    try:
                        lol_instance = self.tool_get_feature_lr_geom(data_id=data_id)

                        po_pro_lol_instance = self.tool_get_po_pro_lr_geom(data_id=data_id)

                        # first current-stationings on current reference-geom
                        # Segment with offset
                        if "sgn" in combined_markers:
                            segment_geom = lol_instance.geometry()
                            if segment_geom:
                                segment_geom.transform(tr)
                                sgn_merge_geoms.append(segment_geom)
                        # Segment without offset
                        if "sg0" in combined_markers:
                            segment_geom_0 = lol_instance.geometry(0)
                            if segment_geom_0:
                                segment_geom_0.transform(tr)
                                sg0_merge_geoms.append(segment_geom_0)
                        # From-Points
                        if "snf_mp" in combined_markers:
                            from_point_geom = lol_instance.get_from_point_geom()
                            if from_point_geom:
                                from_point_geom.transform(tr)
                                snf_merge_geoms.append(from_point_geom)
                        # To-Points
                        if "snt_mp" in combined_markers:
                            to_point_geom = lol_instance.get_to_point_geom()
                            if to_point_geom:
                                to_point_geom.transform(tr)
                                snt_merge_geoms.append(to_point_geom)

                        # then cached-stationings on cached reference-geom
                        # Segment with offset
                        if "sgncaca" in combined_markers:
                            segment_geom = po_pro_lol_instance.geometry()
                            if segment_geom:
                                segment_geom.transform(tr)
                                sgncaca_merge_geoms.append(segment_geom)
                        # Segment without offset
                        if "sg0caca" in combined_markers:
                            segment_geom_0 = po_pro_lol_instance.geometry(0)

                            if segment_geom_0:
                                segment_geom_0.transform(tr)
                                sg0caca_merge_geoms.append(segment_geom_0)
                        # From-Points
                        if "snfcaca_mp" in combined_markers:
                            from_point_geom = po_pro_lol_instance.get_from_point_geom()
                            if from_point_geom:
                                from_point_geom.transform(tr)
                                snfcaca_merge_geoms.append(from_point_geom)
                        # To-Points
                        if "sntcaca_mp" in combined_markers:
                            to_point_geom = po_pro_lol_instance.get_to_point_geom()
                            if to_point_geom:
                                to_point_geom.transform(tr)
                                sntcaca_merge_geoms.append(to_point_geom)
                    except Exception as e:
                        fail_data_ids.append(data_id)

                x_coords = []
                y_coords = []

                if "sgn" in combined_markers and sgn_merge_geoms:
                    sgn_merged_geom = QgsGeometry.unaryUnion(sgn_merge_geoms)
                    if "sgn" in draw_markers:
                        self.canvas_graphics["sgn"].setToGeometry(sgn_merged_geom)
                        self.canvas_graphics["sgn"].show()

                    if "sgn" in extent_markers:
                        extent = sgn_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())

                    if "sgn" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([sgn_merged_geom])

                if "sg0" in combined_markers and sg0_merge_geoms:
                    sg0_merged_geom = QgsGeometry.unaryUnion(sg0_merge_geoms)
                    if "sg0" in draw_markers:
                        self.canvas_graphics["sg0"].setToGeometry(sg0_merged_geom)
                        self.canvas_graphics["sg0"].show()

                    if "sg0" in extent_markers:
                        extent = sg0_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())

                    if "sg0" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([sg0_merged_geom])

                if "snf_mp" in combined_markers and snf_merge_geoms:
                    snf_merged_geom = QgsGeometry.unaryUnion(snf_merge_geoms)
                    if "snf_mp" in draw_markers:
                        self.canvas_graphics["snf_mp"].setToGeometry(snf_merged_geom)
                        self.canvas_graphics["snf_mp"].show()
                    if "snf_mp" in extent_markers:
                        extent = snf_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())
                    if "snf_mp" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([snf_merged_geom])

                if "snt_mp" in combined_markers and snt_merge_geoms:
                    snt_merged_geom = QgsGeometry.unaryUnion(snt_merge_geoms)
                    if "snt_mp" in draw_markers:
                        self.canvas_graphics["snt_mp"].setToGeometry(snt_merged_geom)
                        self.canvas_graphics["snt_mp"].show()
                    if "snt_mp" in extent_markers:
                        extent = snt_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())
                    if "snt_mp" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([snt_merged_geom])

                if "sgncaca" in combined_markers and sgncaca_merge_geoms:
                    sgncaca_merged_geom = QgsGeometry.unaryUnion(sgncaca_merge_geoms)
                    if "sgncaca" in draw_markers:
                        self.canvas_graphics["sgncaca"].setToGeometry(
                            sgncaca_merged_geom
                        )
                        self.canvas_graphics["sgncaca"].show()

                    if "sgncaca" in extent_markers:
                        extent = sgncaca_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())

                    if "sgncaca" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([sgncaca_merged_geom])

                if "sg0caca" in combined_markers and sg0caca_merge_geoms:
                    sg0caca_merged_geom = QgsGeometry.unaryUnion(sg0caca_merge_geoms)
                    if "sg0caca" in draw_markers:
                        self.canvas_graphics["sg0caca"].setToGeometry(sg0_merged_geom)
                        self.canvas_graphics["sg0caca"].show()

                    if "sg0caca" in extent_markers:
                        extent = sg0caca_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())

                    if "sg0caca" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([sg0caca_merged_geom])

                if "snfcaca_mp" in combined_markers and snfcaca_merge_geoms:
                    snfcaca_merged_geom = QgsGeometry.unaryUnion(snfcaca_merge_geoms)
                    if "snfcaca_mp" in draw_markers:
                        self.canvas_graphics["snfcaca_mp"].setToGeometry(
                            snfcaca_merged_geom
                        )
                        self.canvas_graphics["snfcaca_mp"].show()
                    if "snfcaca_mp" in extent_markers:
                        extent = snfcaca_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())
                    if "snfcaca_mp" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([snfcaca_merged_geom])

                if "sntcaca_mp" in combined_markers and sntcaca_merge_geoms:
                    sntcaca_merged_geom = QgsGeometry.unaryUnion(sntcaca_merge_geoms)
                    if "sntcaca_mp" in draw_markers:
                        self.canvas_graphics["sntcaca_mp"].setToGeometry(
                            sntcaca_merged_geom
                        )
                        self.canvas_graphics["sntcaca_mp"].show()
                    if "sntcaca_mp" in extent_markers:
                        extent = sntcaca_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())
                    if "sntcaca_mp" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([sntcaca_merged_geom])

                if extent_mode:
                    self.cvs_set_extent(
                        extent_mode,
                        x_coords,
                        y_coords,
                    )

                if fail_data_ids:
                    self.dlg_append_log_message(
                        "INFO",
                        MY_DICT.tr("po_pro_fail_data_ids", fail_data_ids),
                    )
            else:
                raise IterableEmptyException("PostProcessing-Selection")

    def cvs_draw_feature_selection(
        self,
        draw_markers: list = ["sgn", "sg0", "snf_mp", "snt_mp"],
        extent_markers: list = ["sgn", "sg0", "snf_mp", "snt_mp"],
        flash_markers: list = ["sgn", "sg0", "snf_mp", "snt_mp"],
        extent_mode: str = "zoom_bounds_out",
    ):
        """draw, zoom and flash feature_selection on canvas

        Args:
            draw_markers (list, optional): Defaults to ["sgn","sg0","snf_mp","snt_mp"]
            extent_markers (list, optional): Defaults to ["sgn","sg0","snf_mp","snt_mp"]
            flash_markers (list, optional): Defaults to ["sgn","sg0","snf_mp","snt_mp"].
            extent_mode (str, optional): Defaults to "zoom_bounds_out".
        """
        # Rev. 2026-01-13
        combined_markers = draw_markers + extent_markers + flash_markers

        diff_keys = list_difference(combined_markers, self.canvas_graphics.keys())
        if diff_keys:
            print("false keys", diff_keys)

        self.cvs_hide_markers(draw_markers)
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            if self.session_data.selected_data_fids:
                tr = QgsCoordinateTransform(
                    self.derived_settings.refLyr.crs(),
                    self.iface.mapCanvas().mapSettings().destinationCrs(),
                    QgsProject.instance(),
                )

                sgn_merge_geoms = []
                sg0_merge_geoms = []
                snf_merge_geoms = []
                snt_merge_geoms = []
                fail_data_fids = []

                for data_fid in self.session_data.selected_data_fids:
                    try:
                        lol_instance = self.tool_get_feature_lr_geom(data_fid=data_fid)


                        # Segment with offset
                        if "sgn" in combined_markers:
                            segment_geom = lol_instance.geometry()
                            if segment_geom:
                                segment_geom.transform(tr)
                                sgn_merge_geoms.append(segment_geom)
                        # Segment without offset
                        if "sg0" in combined_markers:
                            segment_geom_0 = lol_instance.geometry(0)
                            if segment_geom_0:
                                segment_geom_0.transform(tr)
                                sg0_merge_geoms.append(segment_geom_0)
                        # From-Points
                        if "snf_mp" in combined_markers:
                            from_point_geom = lol_instance.get_from_point_geom()
                            if from_point_geom:
                                from_point_geom.transform(tr)
                                snf_merge_geoms.append(from_point_geom)
                        # To-Points
                        if "snt_mp" in combined_markers:
                            to_point_geom = lol_instance.get_to_point_geom()
                            if to_point_geom:
                                to_point_geom.transform(tr)
                                snt_merge_geoms.append(to_point_geom)
                    except:
                        fail_data_fids.append(data_fid)

                if fail_data_fids:
                    # filter negative-fids, belonging to unsaved features
                    real_fail_data_fids = [fid for fid in fail_data_fids if fid >= 0]
                    if real_fail_data_fids:
                        self.dlg_append_log_message(
                            "INFO",
                            MY_DICT.tr("feature_selection_fail_data_fids", real_fail_data_fids),
                        )

                x_coords = []
                y_coords = []

                if "sgn" in combined_markers and sgn_merge_geoms:
                    sgn_merged_geom = QgsGeometry.unaryUnion(sgn_merge_geoms)
                    if "sgn" in draw_markers:
                        self.canvas_graphics["sgn"].setToGeometry(sgn_merged_geom)
                        self.canvas_graphics["sgn"].show()

                    if "sgn" in extent_markers:
                        extent = sgn_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())

                    if "sgn" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([sgn_merged_geom])

                if "sg0" in combined_markers and sg0_merge_geoms:
                    sg0_merged_geom = QgsGeometry.unaryUnion(sg0_merge_geoms)
                    if "sg0" in draw_markers:
                        self.canvas_graphics["sg0"].setToGeometry(sg0_merged_geom)
                        self.canvas_graphics["sg0"].show()

                    if "sg0" in extent_markers:
                        extent = sg0_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())

                    if "sg0" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([sg0_merged_geom])

                if "snf_mp" in combined_markers and snf_merge_geoms:
                    snf_merged_geom = QgsGeometry.unaryUnion(snf_merge_geoms)
                    if "snf_mp" in draw_markers:
                        self.canvas_graphics["snf_mp"].setToGeometry(snf_merged_geom)
                        self.canvas_graphics["snf_mp"].show()
                    if "snf_mp" in extent_markers:
                        extent = snf_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())
                    if "snf_mp" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([snf_merged_geom])

                if "snt_mp" in combined_markers and snt_merge_geoms:
                    snt_merged_geom = QgsGeometry.unaryUnion(snt_merge_geoms)
                    if "snt_mp" in draw_markers:
                        self.canvas_graphics["snt_mp"].setToGeometry(snt_merged_geom)
                        self.canvas_graphics["snt_mp"].show()
                    if "snt_mp" in extent_markers:
                        extent = snt_merged_geom.boundingBox()
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())
                    if "snt_mp" in flash_markers:
                        self.iface.mapCanvas().flashGeometries([snt_merged_geom])

                if extent_mode:
                    self.cvs_set_extent(
                        extent_mode,
                        x_coords,
                        y_coords,
                    )
            else:
                raise IterableEmptyException("Feature-Selection")
        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr")

    def s_n_abs_from_edited(self, stationing_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-from, changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.lr_geom_runtime.snap_n_abs_from
        refreshes dialog and canvas-grafics
        Args:
            stationing_from (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_stationing_from(
                        stationing_from, "Nabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_delta_n_fract_edited(self, delta_n_perc: float) -> None:
        """moves self.session_data.lr_geom_runtime.snap_n_abs_to by change of relative segment-length
        Args:
            delta_n_perc (float), Percent-Value, widget limited to range -100...100
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            delta_n_fract = delta_n_perc / 100
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_delta_stationings(
                        delta_n_fract, "Nfract", "from"
                    )

                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

                else:
                    raise RuntimeObjectMissingException("Digitized feature")
        except Exception as e:
            self.sys_log_exception(e)

    def s_delta_n_abs_edited(self, delta_n_abs: float) -> None:
        """update self.session_data.lr_geom_runtime by change of segment-length
        snap_n_abs_from will be kept, snap_n_abs_to will be modified
        Args:
            delta_n_abs (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_delta_stationings(
                        delta_n_abs, "Nabs", "from"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
        except Exception as e:
            self.sys_log_exception(e)

    def s_delta_m_abs_edited(self, delta_m_abs: float) -> None:
        """moves self.session_data.lr_geom_runtime.snap_n_abs_to by change of absolute M-segment-length
        Args:
            delta_m_abs (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_delta_stationings(
                        delta_m_abs, "Mabs", "from"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_delta_m_fract_edited(self, delta_m_perc: float) -> None:
        """moves self.session_data.lr_geom_runtime.snap_n_abs_to by change of relative M-segment-length
        Args:
            delta_m_perc (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            delta_m_fract = delta_m_perc / 100
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_delta_stationings(
                        delta_m_fract, "Mfract", "from"
                    )

                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_n_abs_to_edited(self, stationing_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-to, changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.lr_geom_runtime.snap_n_abs_to
        refreshes dialog and canvas-grafics
        Args:
            stationing_to (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_stationing_to(
                        stationing_to, "Nabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_m_abs_from_edited(self, stationing_m_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m,
        Conditions:
        reference-layer is m-enabled
        referenced-geometry ST_IsValidTrajectory (single-parted, ascending M-values)
        changed via user-input or spin-Buttons
        Args:
            stationing_m_from (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if (
                SVS.REFERENCE_LAYER_USABLE | SVS.REFERENCE_LAYER_M_ENABLED
                in self.system_vs
            ):
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_stationing_from(
                        stationing_m_from, "Mabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
        except Exception as e:
            self.sys_log_exception(e)

    def s_m_abs_to_edited(self, stationing_m_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m,
        Conditions:
        reference-layer is m-enabled
        referenced-geometry ST_IsValidTrajectory (single-parted, ascending M-values)
        changed via user-input or spin-Buttons
        Args:
            stationing_m_to (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    self.session_data.lr_geom_runtime.update_stationing_to(
                        stationing_m_to, "Mabs"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_n_fract_from_edited(self, stationing_n_perc_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-from (fract, percentage 0...100), changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.lr_geom_runtime.snap_n_abs_from
        refreshes dialog and canvas-grafics
        Args:
            stationing_n_perc_from (float): changed widget-value in percent
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    stationing_n_fract_from = stationing_n_perc_from / 100
                    self.session_data.lr_geom_runtime.update_stationing_from(
                        stationing_n_fract_from, "Nfract"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_n_fract_to_edited(self, stationing_n_perc_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-from (fract, percentage 0...100), changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.lr_geom_runtime.snap_n_abs_to
        refreshes dialog and canvas-grafics
        Args:
            stationing_n_perc_to (float): changed widget-value in percent
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    stationing_n_fract_to = stationing_n_perc_to / 100
                    self.session_data.lr_geom_runtime.update_stationing_to(
                        stationing_n_fract_to, "Nfract"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_m_fract_from_edited(self, stationing_m_perc_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m_fract (percentage),
        Args:
            stationing_m_perc_from (float): changed widget-value in percent
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:
                    stationing_m_fract_from = stationing_m_perc_from / 100
                    self.session_data.lr_geom_runtime.update_stationing_from(
                        stationing_m_fract_from, "Mfract"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()
                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def st_zoom_data_feature(self, data_fid):
        """Zoom to Feature, refresh measurements in dialog"""
        # Rev. 2026-01-12
        extent_mode = self.tool_get_extent_mode_lol()

        lr_geom_runtime = self.tool_get_feature_lr_geom(data_fid=data_fid)
        self.session_data.lr_geom_runtime = lr_geom_runtime
        self.dlg_select_feature_selection_row(data_fid)
        self.dlg_populate_measurement()
        self.dlg_refract_measurement()
        self.cvs_draw_lr_geom(
            self.session_data.lr_geom_runtime,
            ["snf", "snt", "sgn", "rfl"],
            ["sgn", "sg0"],
            ["sgn"],
            extent_mode=extent_mode,
        )

    def st_set_edit_feature(self, data_fid):
        """sets session_data.edit_feature_fid, shows on map and refreshes/opens measurement-tab
        Args:
            data_fid (int):
        """
        # Rev. 2026-01-13
        extent_mode = self.tool_get_extent_mode_lol()
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            lr_geom_runtime = self.tool_get_feature_lr_geom(data_fid=data_fid)
            self.session_data.lr_geom_runtime = lr_geom_runtime
            self.session_data.edit_feature_fid = data_fid
            self.dlg_select_feature_selection_row(data_fid)
            self.cvs_draw_lr_geom(
                self.session_data.lr_geom_runtime,
                ["snf", "snt", "sgn", "sg0", "rfl"],
                ["sgn", "sg0"],
                ["snf", "snt", "sgn"],
                extent_mode,
            )
            self.dlg_refresh_measurement()
            self.dlg_show_tab("measurement")

        self.qact_pausing.trigger()

    def s_m_fract_to_edited(self, stationing_m_perc_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m_fract (percentage),
        Args:
            stationing_m_perc_to (float): changed widget-value in percent
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                if self.session_data.lr_geom_runtime is not None:

                    stationing_m_fract_to = stationing_m_perc_to / 100
                    self.session_data.lr_geom_runtime.update_stationing_to(
                        stationing_m_fract_to, "Mfract"
                    )
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "sgn", "sg0", "rfl"],
                    )
                    self.dlg_populate_measurement()

                else:
                    raise RuntimeObjectMissingException("Digitized feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def cvs_draw_lr_geom(
        self,
        lr_geom: LoL,
        draw_markers: list = [],
        extent_markers: list = [],
        flash_markers: list = [],
        extent_mode: str = None,
    ) -> tuple:
        """draws LoL-Segment: stationing points, segment, reference-line
        usually called with self.session_data.lr_geom_runtime

        Args:
            lr_geom (LoL):
            draw_markers (list, optional): combination of marker-types. Matching to keys in self.canvas_graphics.
                - snf => stationing-from
                - enf => edit stationing-from
                - snt => stationing-to
                - ent => edit stationing-to
                - sgn => Segment
                - sg0 => Segment wo. offset
                - rfl => reference-line
                - rflca => cached reference-line
                - sg0caca => cached segment wo. offset
                - sgncaca => cached segment with offset
                - snfcaca => cached stationing-from on cached reference-line
                - sntcaca => cached stationing-to on cached reference-line
            extent_markers (list, optional): combination of marker-types for extent pan/zoom. Matching to keys in self.canvas_graphics.
            flash_markers (list, optional): combination of marker-types for flash-effect. Matching to keys in self.canvas_graphics.
            extent_mode (str, optional): Defaults to None. See cvs_set_extent.
                - zoom_bounds
                - zoom_bounds_in
                - zoom_bounds_out
                - pan_center
                - pan_center_in
                - pan_center_out
                - pan_center_opt_in
                - pan_center_opt_out
                - canvas_in
                - canvas_out

            Returns:
                tuple: (x_coords,y_coords) in canvas-crs
        """
        # Rev. 2026-01-13

        x_coords = []
        y_coords = []

        self.cvs_hide_markers(draw_markers)

        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if lr_geom and lr_geom.reference_geom:
                tr_vl_2_cvs = QgsCoordinateTransform(
                    self.derived_settings.refLyr.crs(),
                    self.iface.mapCanvas().mapSettings().destinationCrs(),
                    QgsProject.instance(),
                )

                combined_markers = draw_markers + extent_markers + flash_markers

                diff_keys = list_difference(
                    combined_markers, self.canvas_graphics.keys()
                )
                if diff_keys:
                    print("false keys", diff_keys)

                # groups of markers drawing the same geometry with different markers
                snf_markers = ["snf", "enf", "snfcaca"]
                snt_markers = ["snt", "ent", "sntcaca"]
                sgn_markers = ["sgncaca", "sgn"]
                sg0_markers = ["sg0caca", "sg0"]
                rfl_markers = ["rfl", "rflca"]

                if list_intersection(combined_markers, snf_markers):
                    from_point_geom = lr_geom.get_from_point_geom()
                    if from_point_geom:
                        from_point_geom.transform(tr_vl_2_cvs)

                        if "snf" in draw_markers:
                            self.canvas_graphics["snf"].setCenter(
                                from_point_geom.asPoint()
                            )
                            self.canvas_graphics["snf"].show()

                        if "enf" in draw_markers:
                            self.canvas_graphics["enf"].setCenter(
                                from_point_geom.asPoint()
                            )
                            self.canvas_graphics["enf"].show()

                        if "snfcaca" in draw_markers:
                            self.canvas_graphics["snfcaca"].setCenter(
                                from_point_geom.asPoint()
                            )
                            self.canvas_graphics["snfcaca"].show()

                        if list_intersection(flash_markers, snf_markers):

                            self.iface.mapCanvas().flashGeometries([from_point_geom])

                        if list_intersection(extent_markers, snf_markers):
                            x_coords.append(from_point_geom.asPoint().x())
                            y_coords.append(from_point_geom.asPoint().y())

                if list_intersection(combined_markers, snt_markers):

                    to_point_geom = lr_geom.get_to_point_geom()

                    if to_point_geom:

                        to_point_geom.transform(tr_vl_2_cvs)

                        if "snt" in draw_markers:
                            self.canvas_graphics["snt"].setCenter(
                                to_point_geom.asPoint()
                            )
                            self.canvas_graphics["snt"].show()

                        if "ent" in draw_markers:
                            self.canvas_graphics["ent"].setCenter(
                                to_point_geom.asPoint()
                            )
                            self.canvas_graphics["ent"].show()

                        if "sntcaca" in draw_markers:
                            self.canvas_graphics["sntcaca"].setCenter(
                                to_point_geom.asPoint()
                            )
                            self.canvas_graphics["sntcaca"].show()

                        if list_intersection(flash_markers, snt_markers):
                            self.iface.mapCanvas().flashGeometries(
                                [to_point_geom],
                            )

                        if list_intersection(extent_markers, snt_markers):
                            x_coords.append(to_point_geom.asPoint().x())
                            y_coords.append(to_point_geom.asPoint().y())

                if list_intersection(combined_markers, sgn_markers):
                    segment_geom = lr_geom.geometry()
                    if segment_geom:
                        if "sgn" in draw_markers:
                            self.canvas_graphics["sgn"].setToGeometry(
                                segment_geom, self.derived_settings.refLyr
                            )
                            self.canvas_graphics["sgn"].show()

                        if "sgncaca" in draw_markers:
                            self.canvas_graphics["sgncaca"].setToGeometry(
                                segment_geom, self.derived_settings.refLyr
                            )
                            self.canvas_graphics["sgncaca"].show()

                        if list_intersection(flash_markers, sgn_markers):
                            self.iface.mapCanvas().flashGeometries(
                                [segment_geom],
                                self.derived_settings.refLyr.crs(),
                            )

                        if list_intersection(extent_markers, sgn_markers):
                            extent = segment_geom.boundingBox()
                            extent = tr_vl_2_cvs.transformBoundingBox(extent)
                            x_coords.append(extent.xMinimum())
                            x_coords.append(extent.xMaximum())
                            y_coords.append(extent.yMinimum())
                            y_coords.append(extent.yMaximum())

                if list_intersection(combined_markers, sg0_markers):

                    segment_geom_0 = lr_geom.geometry(0)

                    if segment_geom_0:
                        if "sg0" in draw_markers:
                            self.canvas_graphics["sg0"].setToGeometry(
                                segment_geom_0, self.derived_settings.refLyr
                            )
                            self.canvas_graphics["sg0"].show()

                        if "sg0caca" in draw_markers:
                            self.canvas_graphics["sg0caca"].setToGeometry(
                                segment_geom_0, self.derived_settings.refLyr
                            )
                            self.canvas_graphics["sg0caca"].show()

                        if list_intersection(flash_markers, sg0_markers):
                            self.iface.mapCanvas().flashGeometries(
                                [segment_geom_0],
                                self.derived_settings.refLyr.crs(),
                            )

                        if list_intersection(extent_markers, sg0_markers):
                            extent = segment_geom_0.boundingBox()
                            extent = tr_vl_2_cvs.transformBoundingBox(extent)
                            x_coords.append(extent.xMinimum())
                            x_coords.append(extent.xMaximum())
                            y_coords.append(extent.yMinimum())
                            y_coords.append(extent.yMaximum())

                if list_intersection(combined_markers, rfl_markers):
                    if "rfl" in draw_markers:
                        self.canvas_graphics["rfl"].setToGeometry(
                            lr_geom.reference_geom, self.derived_settings.refLyr
                        )
                        self.canvas_graphics["rfl"].show()

                    if "rflca" in draw_markers:
                        self.canvas_graphics["rflca"].setToGeometry(
                            lr_geom.reference_geom, self.derived_settings.refLyr
                        )
                        self.canvas_graphics["rflca"].show()

                    if list_intersection(flash_markers, rfl_markers):
                        self.iface.mapCanvas().flashGeometries(
                            [lr_geom.reference_geom],
                            self.derived_settings.refLyr.crs(),
                        )

                    if list_intersection(extent_markers, rfl_markers):
                        extent = lr_geom.reference_geom.boundingBox()
                        extent = tr_vl_2_cvs.transformBoundingBox(extent)
                        x_coords.append(extent.xMinimum())
                        x_coords.append(extent.xMaximum())
                        y_coords.append(extent.yMinimum())
                        y_coords.append(extent.yMaximum())

                if extent_mode and extent_markers:
                    # coordinates transformed to canvas-crs
                    self.cvs_set_extent(extent_mode, x_coords, y_coords)

            else:
                raise RuntimeObjectMissingException("Digitized feature")

        return (x_coords, y_coords)

    def ssc_data_lyr_stationing_from_field(self) -> None:
        """change stationing_n-field of Data-Layer in QComboBox"""
        # Rev. 2026-01-13
        self.stored_settings.dataLyrStationingFromFieldName = (
            self.my_dialog.qcbn_data_lyr_stationing_from_field.currentData(
                Qt_Roles.RETURN_VALUE
            )
        )

        self.sys_restart_session()

    def ssc_data_lyr_stationing_to_field(self) -> None:
        """change stationing_n-field of Data-Layer in QComboBox"""
        # Rev. 2026-01-13
        self.stored_settings.dataLyrStationingToFieldName = (
            self.my_dialog.qcbn_data_lyr_stationing_to_field.currentData(
                Qt_Roles.RETURN_VALUE
            )
        )

        self.sys_restart_session()

    def ssc_data_lyr_offset_field(self) -> None:
        """change Reference-id-field of Data-Layer-Reference-field in QComboBox
        unsets some follow-up-settings, which possibly don't fit anymore and have to be reconfigured by the user
        """
        # Rev. 2026-01-13
        self.stored_settings.dataLyrOffsetFieldName = (
            self.my_dialog.qcbn_data_lyr_offset_field.currentData(Qt_Roles.RETURN_VALUE)
        )

        if (
            self.derived_settings.showLyr is not None
            and self.derived_settings.showLyr.dataProvider().name() == "virtual"
        ):
            self.dlg_append_log_message("WARNING", MY_DICT.tr("show_lyr_affected"))

        self.sys_restart_session()

    def tool_get_data_lyr_indices(self) -> tuple:
        """returns the field-indices for special fields in dataLyr

        Returns:
            tuple: (geom_idcs: geometry-affecting fields, check_idcs: additional fields used in displayExpression)
        """
        # Rev. 2026-01-13
        if SVS.DATA_LAYER_CONNECTED in self.system_vs:
            geom_idcs = [
                self.derived_settings.dataLyr.fields().indexOf(
                    self.stored_settings.dataLyrStationingFromFieldName
                ),
                self.derived_settings.dataLyr.fields().indexOf(
                    self.stored_settings.dataLyrStationingToFieldName
                ),
                self.derived_settings.dataLyr.fields().indexOf(
                    self.stored_settings.dataLyrOffsetFieldName
                ),
                self.derived_settings.dataLyr.fields().indexOf(
                    self.stored_settings.dataLyrReferenceFieldName
                ),
            ]

            exp = QgsExpression(self.derived_settings.dataLyr.displayExpression())
            check_idcs = list(geom_idcs)
            check_idcs += exp.referencedAttributeIndexes(
                self.derived_settings.dataLyr.fields()
            )
            return geom_idcs, check_idcs
        else:
            raise LayerNotRegisteredException("DataLyr")

    def sys_connect_data_lyr(self) -> None:
        """prepares Data-Layer:
        - checks existance and suitability
        - re-sets self.stored_settings.dataLyrId
        - re-sets self.derived_settings.dataLyr
        - connects signals to slots
        Note:
        different versions for LolEvt/PolEvt because of different field-names in StoredSettings
        """
        # Rev. 2026-01-13
        integer_field_types = [
            QMetaType.Int,
            QMetaType.UInt,
            QMetaType.LongLong,
            QMetaType.ULongLong,
        ]
        pk_field_types = [
            QMetaType.Int,
            QMetaType.UInt,
            QMetaType.LongLong,
            QMetaType.ULongLong,
            QMetaType.QString,
        ]
        numeric_field_types = [
            QMetaType.Int,
            QMetaType.UInt,
            QMetaType.LongLong,
            QMetaType.ULongLong,
            QMetaType.Double,
        ]

        data_lyr = QgsProject.instance().mapLayer(self.stored_settings.dataLyrId)
        if data_lyr:

            # check usability
            if (
                data_lyr.isValid()
                and data_lyr.type() == Qgis.LayerType.VectorLayer
                and data_lyr.dataProvider().name() != "virtual"
                and data_lyr.dataProvider().wkbType() == QgsWkbTypes.NoGeometry
            ):

                self.derived_settings.dataLyr = data_lyr
                self.system_vs |= SVS.DATA_LAYER_EXISTS

                if data_lyr.isEditable():
                    self.system_vs |= SVS.DATA_LAYER_EDITABLE

                if self.stored_settings.dataLyrIdFieldName:
                    fnx = (
                        data_lyr.dataProvider()
                        .fields()
                        .indexOf(self.stored_settings.dataLyrIdFieldName)
                    )
                    if (
                        fnx >= 0
                        and data_lyr.dataProvider().fields()[fnx].type()
                        in pk_field_types
                    ):
                        self.derived_settings.dataLyrIdField = (
                            data_lyr.dataProvider().fields()[fnx]
                        )

                        if (
                            self.derived_settings.refLyr
                            and self.derived_settings.refLyrIdField
                            and self.stored_settings.dataLyrReferenceFieldName
                        ):
                            fnx = (
                                data_lyr.dataProvider()
                                .fields()
                                .indexOf(self.stored_settings.dataLyrReferenceFieldName)
                            )
                            if (
                                fnx >= 0
                                and (
                                    self.derived_settings.refLyrIdField.type()
                                    == data_lyr.dataProvider().fields()[fnx].type()
                                )
                                or (
                                    self.derived_settings.refLyrIdField.type()
                                    in integer_field_types
                                    and data_lyr.dataProvider().fields()[fnx].type()
                                    in integer_field_types
                                )
                            ):
                                self.derived_settings.dataLyrReferenceField = (
                                    data_lyr.dataProvider().fields()[fnx]
                                )

                                if self.stored_settings.dataLyrOffsetFieldName:
                                    fnx = (
                                        data_lyr.dataProvider()
                                        .fields()
                                        .indexOf(
                                            self.stored_settings.dataLyrOffsetFieldName
                                        )
                                    )
                                    if (
                                        fnx >= 0
                                        and data_lyr.dataProvider().fields()[fnx].type()
                                        in numeric_field_types
                                    ):
                                        self.derived_settings.dataLyrOffsetField = (
                                            data_lyr.dataProvider().fields()[fnx]
                                        )

                                        if (
                                            self.stored_settings.dataLyrStationingFromFieldName
                                        ):
                                            fnx = (
                                                data_lyr.dataProvider()
                                                .fields()
                                                .indexOf(
                                                    self.stored_settings.dataLyrStationingFromFieldName
                                                )
                                            )
                                            if (
                                                fnx >= 0
                                                and data_lyr.dataProvider()
                                                .fields()[fnx]
                                                .type()
                                                in numeric_field_types
                                            ):
                                                self.derived_settings.dataLyrStationingFromField = data_lyr.dataProvider().fields()[
                                                    fnx
                                                ]

                                                if (
                                                    self.stored_settings.dataLyrStationingToFieldName
                                                ):
                                                    fnx = (
                                                        data_lyr.dataProvider()
                                                        .fields()
                                                        .indexOf(
                                                            self.stored_settings.dataLyrStationingToFieldName
                                                        )
                                                    )
                                                    if (
                                                        fnx >= 0
                                                        and data_lyr.dataProvider()
                                                        .fields()[fnx]
                                                        .type()
                                                        in numeric_field_types
                                                    ):
                                                        self.derived_settings.dataLyrStationingToField = data_lyr.dataProvider().fields()[
                                                            fnx
                                                        ]
                                                        # Note: check for uniquity with field-names instead of the fields, else TypeError: unhashable type: 'QgsField'
                                                        check_set = set(
                                                            [
                                                                self.derived_settings.dataLyrIdField.name(),
                                                                self.derived_settings.dataLyrReferenceField.name(),
                                                                self.derived_settings.dataLyrStationingFromField.name(),
                                                                self.derived_settings.dataLyrStationingToField.name(),
                                                                self.derived_settings.dataLyrOffsetField.name(),
                                                            ]
                                                        )
                                                        if len(check_set) == 5:

                                                            self.system_vs |= (
                                                                SVS.DATA_LAYER_NECESSARY_FIELDS_DEFINED
                                                            )

                                                            if (
                                                                data_lyr.dataProvider().capabilities()
                                                                & QgsVectorDataProvider.AddFeatures
                                                            ):
                                                                self.system_vs |= (
                                                                    SVS.DATA_LAYER_INSERT_ENABLED
                                                                )
                                                            if (
                                                                data_lyr.dataProvider().capabilities()
                                                                & QgsVectorDataProvider.ChangeAttributeValues
                                                            ):
                                                                self.system_vs |= (
                                                                    SVS.DATA_LAYER_UPDATE_ENABLED
                                                                )
                                                            if (
                                                                data_lyr.dataProvider().capabilities()
                                                                & QgsVectorDataProvider.DeleteFeatures
                                                            ):
                                                                self.system_vs |= (
                                                                    SVS.DATA_LAYER_DELETE_ENABLED
                                                                )

                                                            self.sys_connect_data_layer_slots(
                                                                data_lyr
                                                            )

                                                            self.lact_add_layer_action_select_feature(
                                                                data_lyr
                                                            )

                                                            self.gui_add_layer_action_show_feature_form(
                                                                data_lyr
                                                            )
                                                            self.system_vs |= (
                                                                SVS.DATA_LAYER_ACTIONS_ADDED
                                                            )

                                                            self.system_vs |= (
                                                                SVS.DATA_LAYER_CONNECTED
                                                            )

                                                            self.sys_log_message("SUCCESS", f"data-layer '{data_lyr.name()}' connected")

                                                        else:
                                                            self.dlg_append_log_message(
                                                                "CRITICAL",
                                                                MY_DICT.tr(
                                                                    "duplicate_field_registrations_detected"
                                                                ),
                                                                True,
                                                                True,
                                                            )

        else:
            # Layer not found => disconnect current assigned data-layer
            self.sys_disconnect_data_lyr()

    def sys_disconnect_data_lyr(self):
        """reverse to sys_connect_data_lyr
        only disconnects and resets  signal_slot_cons.data_lyr_connections
        keeps stored_settings and derived_settings"""
        # Rev. 2026-01-13

        try:
            if self.derived_settings.dataLyr:
                action_ids = [
                    self._zoom_lol_feature_act_id,
                    self._show_feature_form_act_id,
                ]
                action_list = [
                    action
                    for action in self.derived_settings.dataLyr.actions().actions()
                    if action.id() in action_ids
                ]
                for action in action_list:
                    self.derived_settings.dataLyr.actions().removeAction(action.id())

                self.derived_settings.dataLyr.reload()

                for conn_id in self.signal_slot_cons.data_lyr_connections:
                    self.derived_settings.dataLyr.disconnect(conn_id)

            self.signal_slot_cons.data_lyr_connections = []

            self.stored_settings.dataLyrId = None
            self.stored_settings.dataLyrIdFieldName = None
            self.stored_settings.dataLyrOffsetFieldName = None
            self.stored_settings.dataLyrReferenceFieldName = None
            self.stored_settings.dataLyrStationingFromFieldName = None
            self.stored_settings.dataLyrStationingToFieldName = None

            self.derived_settings.dataLyr = None
            self.derived_settings.dataLyrIdField = None
            self.derived_settings.dataLyrOffsetField = None
            self.derived_settings.dataLyrReferenceField = None
            self.derived_settings.dataLyrStationingFromField = None
            self.derived_settings.dataLyrStationingToField = None

        except Exception as e:
            # RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
            pass

        self.system_vs &= ~SVS.DATA_LAYER_CONNECTED
        self.dlg_populate_settings()

    def dlg_populate_po_pro_selection(self):
        """refresh PoPro-treeview using prefetched data from self.session_data.po_pro_cache"""
        # Rev. 2026-01-13

        if self.my_dialog:

            self.my_dialog.qtrv_po_pro_selection.blockSignals(True)
            if (
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED
            ) in self.system_vs:

                data_context = QgsExpressionContext()
                data_display_exp = QgsExpression(
                    self.derived_settings.dataLyr.displayExpression()
                )
                data_display_exp.prepare(data_context)

                ref_context = QgsExpressionContext()
                ref_display_exp = QgsExpression(
                    self.derived_settings.refLyr.displayExpression()
                )
                ref_display_exp.prepare(ref_context)

                root_item = (
                    self.my_dialog.qtrv_po_pro_selection.model().invisibleRootItem()
                )

                # fetch common reference-ids used in the three layers

                # refLyr => all assignable reference-ids, consider filter
                ref_lyr_ref_ids = get_field_values(
                    self.derived_settings.refLyr, self.derived_settings.refLyrIdField
                )

                # dataLyer => all currently assigned ref-ids
                data_lyr_ref_ids = get_field_values(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyrReferenceField,
                )

                # poProRefLyr => PostProcessing-Reference-Layer, subset of refLyr
                po_pro_ref_lyr_ref_ids = get_field_values(
                    self.derived_settings.poProRefLyr,
                    self.derived_settings.poProRefLyrIdField,
                )

                # reference-ids of all affected/cached dataLyr-features
                po_pro_cache_ref_ids = {
                    self.session_data.po_pro_cache[data_id]["ref_id"]
                    for data_id in self.session_data.po_pro_cache
                }

                # common ref_ids in all layers
                common_ref_ids = (
                    ref_lyr_ref_ids.intersection(data_lyr_ref_ids)
                    .intersection(po_pro_ref_lyr_ref_ids)
                    .intersection(po_pro_cache_ref_ids)
                )

                missing_ref_ids = po_pro_cache_ref_ids - ref_lyr_ref_ids
                missing_ref_ids |= po_pro_cache_ref_ids - data_lyr_ref_ids
                missing_ref_ids |= po_pro_cache_ref_ids - po_pro_ref_lyr_ref_ids

                if missing_ref_ids:
                    self.dlg_append_log_message(
                        "INFO",
                        MY_DICT.tr("po_pro_missing_reference_ids", missing_ref_ids),
                    )
                fail_ref_ids = []
                fail_data_ids = []
                for ref_id in common_ref_ids:
                    # query current reference-feature from refLyr
                    # should exist, because queried by common ids
                    try:
                        ref_feature = self.tool_get_reference_feature(ref_id=ref_id)
                    except:
                        #but perhaps without or with invalid geometry?
                        fail_ref_ids.append(ref_id)
                        continue

                    ref_fid = ref_feature.id()

                    reference_item = MyStandardItem()
                    reference_item.setData(ref_fid, Qt_Roles.CUSTOM_SORT)
                    reference_item.setData(ref_fid, Qt_Roles.REF_FID)
                    reference_item_cell_widget = MyCellWidget()
                    reference_function_item = MyStandardItem()

                    ref_context.setFeature(ref_feature)
                    display_exp = ref_display_exp.evaluate(ref_context)
                    reference_item.setText(str(display_exp))

                    root_item.appendRow(
                        [
                            reference_item,
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            MyStandardItem(),
                            reference_function_item,
                        ]
                    )

                    qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                    qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                    qtb.pressed.connect(
                        lambda ref_id=ref_id: self.st_remove_from_po_pro_selection(
                            ref_id=ref_id
                        )
                    )
                    reference_item_cell_widget.layout().addWidget(qtb)

                    reference_function_cell_widget = MyCellWidget()

                    qtb = MyToolButton(
                        QIcon(":icons/mActionFormView.svg"),
                        MY_DICT.tr("show_feature_form_ref_lyr_ttp"),
                    )
                    qtb.pressed.connect(
                        lambda ref_fid=ref_fid: self.st_show_reference_feature_form(
                            ref_fid
                        )
                    )
                    reference_function_cell_widget.layout().addWidget(qtb)

                    qtb = MyToolButton(
                        QIcon(":icons/select_in_layer.svg"),
                        MY_DICT.tr("select_in_layer_ttp"),
                    )
                    qtb.pressed.connect(
                        lambda ref_id=ref_id: self.st_select_po_pro_ref_feature(ref_id)
                    )
                    reference_function_cell_widget.layout().addWidget(qtb)

                    qtb = MyToolButton(
                        QIcon(":icons/zoom_pan.svg"),
                        MY_DICT.tr("zoom_ref_feature_ttp"),
                    )
                    qtb.pressed.connect(
                        lambda ref_id=ref_id: self.st_zoom_po_pro_ref_feature(ref_id)
                    )
                    reference_function_cell_widget.layout().addWidget(qtb)

                    qtb = MyToolButton(
                        QIcon(":icons/show_reference_difference.svg"),
                        MY_DICT.tr("show_reference_difference_qtb_ttp"),
                    )
                    qtb.pressed.connect(
                        lambda my_ref_fid=ref_fid: self.st_show_po_pro_ref_geom_diffs(
                            ref_id
                        )
                    )
                    reference_function_cell_widget.layout().addWidget(qtb)

                    self.my_dialog.qtrv_po_pro_selection.setIndexWidget(
                        reference_item.index(),
                        reference_item_cell_widget,
                    )

                    self.my_dialog.qtrv_po_pro_selection.setIndexWidget(
                        reference_function_item.index(),
                        reference_function_cell_widget,
                    )

                    # cached po-pro-features with this ref_id

                    filtered_dict = {
                        data_id: self.session_data.po_pro_cache[data_id]
                        for data_id in self.session_data.po_pro_cache
                        if self.session_data.po_pro_cache[data_id]["ref_id"] == ref_id
                    }

                    for data_id in filtered_dict:

                        data_fid = self.session_data.po_pro_cache[data_id]["data_fid"]



                        try:
                            # check if there is a data-feature for the cached feature
                            assigned_data_feature = self.tool_get_data_feature(
                                data_fid=data_fid
                            )
                            stationing_from_xyz = self.session_data.po_pro_cache[
                                data_id
                            ]["stationing_from"]
                            stationing_to_xyz = self.session_data.po_pro_cache[data_id][
                                "stationing_to"
                            ]

                            offset = self.session_data.po_pro_cache[data_id]["offset"]

                            this_row_items = [MyStandardItem()]

                            id_item = MyStandardItem()
                            id_item_cell_widget = MyCellWidget()

                            id_function_item = MyStandardItem()
                            id_function_item.setData(data_fid, Qt_Roles.CUSTOM_SORT)
                            id_function_item.setData(data_fid, Qt_Roles.DATA_FID)
                            id_function_cell_widget = MyCellWidget()

                            id_item.setData(data_fid, Qt_Roles.CUSTOM_SORT)
                            id_item.setData(data_fid, Qt_Roles.DATA_FID)
                            data_context.setFeature(assigned_data_feature)
                            display_exp = data_display_exp.evaluate(data_context)
                            id_item.setText(str(display_exp))
                            id_item.setTextAlignment(Qt.AlignLeft)

                            qtb = MyToolButton(QIcon(":icons/mIconClearTextHover.svg"))

                            qtb.setToolTip(MY_DICT.tr("remove_from_selection_qtb_ttp"))
                            qtb.pressed.connect(
                                lambda data_id=data_id: self.st_remove_from_po_pro_selection(
                                    data_id=data_id
                                )
                            )
                            id_item_cell_widget.layout().addWidget(qtb)

                            this_row_items.append(id_item)

                            from_item = MyStandardItem()
                            from_item.setData(stationing_from_xyz, Qt_Roles.CUSTOM_SORT)

                            from_item.setText(
                                self.tool_format_number(stationing_from_xyz)
                            )
                            from_item.setTextAlignment(Qt.AlignRight)
                            this_row_items.append(from_item)

                            to_item = MyStandardItem()
                            to_item.setData(stationing_to_xyz, Qt_Roles.CUSTOM_SORT)

                            to_item.setText(self.tool_format_number(stationing_to_xyz))
                            to_item.setTextAlignment(Qt.AlignRight)
                            this_row_items.append(to_item)

                            offset_item = MyStandardItem()
                            offset_item.setData(offset, Qt_Roles.CUSTOM_SORT)

                            offset_item.setText(self.tool_format_number(offset))
                            offset_item.setTextAlignment(Qt.AlignRight)
                            this_row_items.append(offset_item)

                            this_row_items.append(id_function_item)

                            reference_item.appendRow(this_row_items)

                            qtb = MyToolButton(
                                QIcon(":icons/mActionFormView.svg"),
                                MY_DICT.tr("open_feature_form_ttp"),
                            )
                            qtb.pressed.connect(
                                lambda data_id=data_id: self.st_show_po_pro_data_feature_form(
                                    data_id
                                )
                            )
                            id_function_cell_widget.layout().addWidget(qtb)

                            qtb = MyToolButton(
                                QIcon(":icons/select_in_layer.svg"),
                                MY_DICT.tr("select_in_layer_ttp"),
                            )
                            qtb.pressed.connect(
                                lambda data_id=data_id: self.st_select_po_pro_data_feature(
                                    data_id
                                )
                            )
                            id_function_cell_widget.layout().addWidget(qtb)

                            qtb = MyToolButton(
                                QIcon(":icons/show_lol_difference.svg"),
                                MY_DICT.tr("show_lol_difference_qtb_ttp"),
                            )
                            qtb.pressed.connect(
                                lambda data_id=data_id: self.st_select_po_pro_feature(
                                    data_id=data_id
                                )
                            )
                            id_function_cell_widget.layout().addWidget(qtb)

                            self.my_dialog.qtrv_po_pro_selection.setIndexWidget(
                                id_item.index(), id_item_cell_widget
                            )

                            self.my_dialog.qtrv_po_pro_selection.setIndexWidget(
                                id_function_item.index(),
                                id_function_cell_widget,
                            )
                        except Exception as e:
                            fail_data_ids.append(data_id)

                if fail_ref_ids:
                    self.dlg_append_log_message(
                        "INFO",
                        MY_DICT.tr("po_pro_fail_ref_ids", fail_ref_ids),
                    )

                if fail_data_ids:
                    self.dlg_append_log_message(
                        "INFO",
                        MY_DICT.tr("po_pro_fail_data_ids", fail_data_ids),
                    )


            QTimer.singleShot(10, self.dlg_po_pro_selection_apply_pre_settings)

            self.my_dialog.qtrv_po_pro_selection.blockSignals(False)

    def dlg_reset_po_pro_edit(self):
        """resets widgets and QActions in Post-Processing-Edit-Section"""
        # Rev. 2026-01-13
        self.qlbl_po_pro_feature.clear()
        self.qlbl_po_pro_feature.setToolTip(MY_DICT.tr("no_po_pro_feature_selected"))
        self.qact_move_po_pro_from_point.setEnabled(False)
        self.qact_move_po_pro_to_point.setEnabled(False)
        self.qact_move_po_pro_segment.setEnabled(False)

    def dlg_populate_po_pro_edit(self):
        """populates widgets and QActions in Post-Processing-Edit-Section"""
        # Rev. 2026-01-13
        if self.my_dialog:
            if self.session_data.po_pro_feature is not None:
                data_feature = self.tool_get_data_feature(
                    data_fid=self.session_data.po_pro_feature.data_fid
                )
                data_context = QgsExpressionContext()
                data_display_exp = QgsExpression(
                    self.derived_settings.dataLyr.displayExpression()
                )
                data_display_exp.prepare(data_context)

                data_context.setFeature(data_feature)
                data_display_value = data_display_exp.evaluate(data_context)

                self.qlbl_po_pro_feature.setText(f"'{data_display_value}'")
                self.qlbl_po_pro_feature.setToolTip(
                    MY_DICT.tr(
                        "edit_data_fid_with_fid_ttp",
                        self.session_data.po_pro_feature.data_fid,
                        data_display_value,
                    )
                )

    def dlg_refract_po_pro_edit(self):
        """disables/enables QActions in Post-Processing-Edit-Section"""
        # Rev. 2026-01-13
        if self.my_dialog:
            enable_actions = [
                self.qact_move_po_pro_from_point,
                self.qact_move_po_pro_to_point,
                self.qact_move_po_pro_segment,
            ]

            po_pro_feature_exists = self.session_data.po_pro_feature is not None

            edit_enabled = (
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                | SVS.DATA_LAYER_EDITABLE
                | SVS.DATA_LAYER_UPDATE_ENABLED
                | SVS.PO_PRO_REF_LAYER_CONNECTED
                in self.system_vs
            )

            for action in enable_actions:
                action.setEnabled(po_pro_feature_exists & edit_enabled)

            self.qact_toggle_po_pro_edit_mode.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED
                in self.system_vs
            )

            self.qact_toggle_edit_mode.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.DATA_LAYER_UPDATE_ENABLED
                in self.system_vs
            )

    def dlg_reset_po_pro_selection(self):
        """resets model and header for qtrv_po_pro_selection"""
        # Rev. 2026-01-13
        if self.my_dialog:
            if self.my_dialog.qtrv_po_pro_selection.model():
                self.dlg_po_pro_selection_get_pre_settings()
                self.my_dialog.qtrv_po_pro_selection.model().clear()

            header_labels = [
                MY_DICT.tr("qtw_post_processing_reference_layer_hlbl"),
                MY_DICT.tr("qtw_post_processing_data_layer_hlbl"),
                MY_DICT.tr("qtw_post_processing_stationing_from_cached_hlbl"),
                MY_DICT.tr("qtw_post_processing_stationing_to_cached_hlbl"),
                MY_DICT.tr("qtw_post_processing_offset_cached_hlbl"),
                "",
            ]

            root_model = QStandardItemModel()
            self.my_dialog.qtrv_po_pro_selection.setModel(root_model)
            self.my_dialog.qtrv_po_pro_selection.model().setHorizontalHeaderLabels(
                header_labels
            )

    def lact_add_layer_action_select_feature(self, vl: QgsVectorLayer):
        """Adds action to Vectorlayer for zoom to LoL-Feature from form or table

        Args:
            vl (QgsVectorLayer)
        """
        # Rev. 2026-01-13
        action_list = [
            action
            for action in vl.actions().actions()
            if action.id() in [self._zoom_lol_feature_act_id]
        ]
        for action in action_list:
            vl.actions().removeAction(action.id())

        if isinstance(vl, QgsVectorLayer):

            # store all necessary settings to be reusable for other configurations or even without loaded Plugin
            command = """try:
    feature_id=[%@id%]
    layer_id='[%@layer_id%]'
    mt = None
    try:
        mt = qgis.utils.plugins['LinearReferencing'].mt_LolEvt
    except:
        qgis.utils.iface.messageBar().pushMessage('LinearReferencing-Plugin not loaded/initialized', level=Qgis.Warning)
    if mt:
        mt.lact_select_feature(layer_id,feature_id)
except Exception as e:
    print(e)
    qgis.utils.iface.messageBar().pushMessage('Error in LinearReferencing-Plugin (LolEvt.lact_select_feature):', f'{e}', level=Qgis.Warning)
"""
            # Note: if the action is not removed after plugin-uninstall, icons from plugins-resource-file are not found anymore
            # but the QgsAction-constructor accepts only strings (Path to icon, resource supported), no QIcon
            zoom_feature_action = QgsAction(
                self._zoom_lol_feature_act_id,
                QgsAction.ActionType.GenericPython,
                MY_DICT.tr("lact_lol_select_feature_description"),
                command,
                ":icons/re_digitize_lol.svg",
                False,
                "Zoom to feature",
                # 'Feature' => open feature-form from feature-form because of attribute-tables in QgsDualView-mode
                {"Form", "Feature", "Layer"},
                "",
            )

            vl.actions().addAction(zoom_feature_action)

            atc = vl.attributeTableConfig()
            if not atc.actionWidgetVisible():
                # QgsAttributeTableConfig.ButtonList / .DropDown
                atc.setActionWidgetStyle(QgsAttributeTableConfig.ButtonList)
                atc.setActionWidgetVisible(True)
                vl.setAttributeTableConfig(atc)

            vl.reload()

    def lact_select_feature(self, layer_id: str, feature_id: int):
        """select feature in layer
        Args:
            feature_id (int): [%@id%]-Attribute from LayerAction
            layer_id (str): [%@layer_id%]
        """
        # Rev. 2026-01-13
        try:
            extent_mode = self.tool_get_extent_mode_lol()

            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                data_fid = None
                if layer_id in [
                    self.stored_settings.dataLyrId,
                    self.stored_settings.showLyrId,
                ]:
                    if layer_id == self.stored_settings.dataLyrId:
                        data_feature = self.tool_get_data_feature(data_fid=feature_id)
                    elif layer_id == self.stored_settings.showLyrId:
                        data_feature = self.tool_get_data_feature(show_fid=feature_id)

                    data_fid=data_feature.id()

                    lr_geom_runtime = self.tool_get_feature_lr_geom(
                        data_fid=data_fid
                    )
                    self.session_data.lr_geom_runtime = lr_geom_runtime
                    self.session_data.edit_feature_fid = data_fid
                    self.tool_append_to_feature_selection(data_fid)
                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        ["snf", "snt", "enf", "ent", "sgn", "sg0", "rfl"],
                        ["sgn", "sg0"],
                        ["snf", "snt", "sgn"],
                        extent_mode,
                    )
                    self.dlg_refresh_measurement()
                    self.dlg_show_tab("measurement")
                else:
                    raise LayerNotRegisteredException(layer_id)
            else:
                raise LayerNotRegisteredException("RefLyr + DataLyr")

            self.qact_pausing.trigger()

        except Exception as e:
            self.sys_log_exception(e)

    def sys_connect_show_layer(self) -> None:
        """checks and prepares Show-Layer:
        - re-sets self.stored_settings:
            - showLyrId
            - showLyr
        - connects signals to slots

        Note:
            different version for LolEvt/PolEvt because of geometryType-Check and virtual-layer-fields
        """
        # Rev. 2026-01-13

        # connect int-fields of different type in showLyr/dataLyr
        integer_field_types = [
            QMetaType.Int,
            QMetaType.UInt,
            QMetaType.LongLong,
            QMetaType.ULongLong,
        ]

        show_layer = QgsProject.instance().mapLayer(self.stored_settings.showLyrId)
        if show_layer:
            if (
                show_layer.isValid()
                and show_layer.type() == Qgis.LayerType.VectorLayer
                and show_layer.geometryType() == Qgis.GeometryType.Line
            ):
                if show_layer.dataProvider().name() == "virtual":
                    # only enable fitting virtual layers...
                    virtual_check_contents = [
                        self.stored_settings.refLyrId,
                        self.stored_settings.refLyrIdFieldName,
                        self.stored_settings.dataLyrId,
                        self.stored_settings.dataLyrIdFieldName,
                        self.stored_settings.dataLyrReferenceFieldName,
                        self.stored_settings.dataLyrStationingFromFieldName,
                        self.stored_settings.dataLyrStationingToFieldName,
                        self.stored_settings.dataLyrOffsetFieldName,
                        "ST_OffsetCurve",
                        "ST_Line_Substring",
                    ]

                    if self.stored_settings.lrMode in ["Nabs", "Nfract"]:
                        if all(
                            s in show_layer.dataProvider().uri().uri()
                            for s in virtual_check_contents
                        ):
                            self.derived_settings.showLyr = show_layer
                            self.system_vs |= SVS.SHOW_LAYER_EXISTS

                    elif self.stored_settings.lrMode == "Mabs":
                        virtual_check_contents.append("ST_Line_Locate_Point")
                        virtual_check_contents.append("ST_TrajectoryInterpolatePoint")
                        if all(
                            s in show_layer.dataProvider().uri().uri()
                            for s in virtual_check_contents
                        ):
                            self.derived_settings.showLyr = show_layer
                            self.system_vs |= SVS.SHOW_LAYER_EXISTS
                else:
                    self.derived_settings.showLyr = show_layer
                    self.system_vs |= SVS.SHOW_LAYER_EXISTS

                if SVS.SHOW_LAYER_EXISTS in self.system_vs:
                    if (
                        self.derived_settings.dataLyrIdField
                        and self.stored_settings.showLyrBackReferenceFieldName
                    ):
                        fnx = (
                            show_layer.dataProvider()
                            .fields()
                            .indexOf(self.stored_settings.showLyrBackReferenceFieldName)
                        )
                        if (
                            fnx >= 0
                            and (
                                self.derived_settings.dataLyrIdField.type()
                                == show_layer.dataProvider().fields()[fnx].type()
                            )
                            or (
                                self.derived_settings.dataLyrIdField.type()
                                in integer_field_types
                                and show_layer.dataProvider().fields()[fnx].type()
                                in integer_field_types
                            )
                        ):
                            self.derived_settings.showLyrBackReferenceField = (
                                show_layer.dataProvider().fields()[fnx]
                            )
                            self.system_vs |= SVS.SHOW_LAYER_NECESSARY_FIELDS_DEFINED
                            self.lact_add_layer_action_select_feature(show_layer)
                            self.gui_add_layer_action_show_feature_form(show_layer)
                            self.system_vs |= SVS.SHOW_LAYER_ACTIONS_ADDED
                            self.system_vs |= SVS.SHOW_LAYER_CONNECTED

                            self.sys_log_message("SUCCESS", f"show-layer '{show_layer.name()}' connected")

        else:
            self.sys_disconnect_show_lyr()

    def sys_refresh_po_pro_cache(self):
        """finds affected data-features and refreshes self.session_data.po_pro_cache and Treeview"""
        # Rev. 2026-01-13
        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED
        ) in self.system_vs:

            # fetch common reference-ids used in the three layers
            data_lyr_ref_ids = get_field_values(
                self.derived_settings.dataLyr,
                self.derived_settings.dataLyrReferenceField,
            )
            ref_lyr_ref_ids = get_field_values(
                self.derived_settings.refLyr, self.derived_settings.refLyrIdField
            )
            po_pro_ref_ids = get_field_values(
                self.derived_settings.poProRefLyr,
                self.derived_settings.poProRefLyrIdField,
            )

            if not po_pro_ref_ids:
                # possibly an empty memory-layer from last session?
                self.dlg_append_log_message(
                    "WARNING", MY_DICT.tr("po_pro_ref_lyr_empty")
                )
                return

            common_ref_ids = ref_lyr_ref_ids.intersection(
                data_lyr_ref_ids
            ).intersection(po_pro_ref_ids)

            # warn missing references
            if common_ref_ids != data_lyr_ref_ids:
                missing_ref_ids = data_lyr_ref_ids - common_ref_ids
                self.dlg_append_log_message(
                    "INFO", MY_DICT.tr("po_pro_missing_reference_ids", missing_ref_ids)
                )

            # Step 1: find affected data-features

            affected_data_ids = set()
            error_ref_ids = set()
            error_data_ids = set()
            po_pro_cache = dict()
            for ref_id in common_ref_ids:
                try:
                    ref_feature = get_feature_by_value(
                        self.derived_settings.refLyr,
                        self.derived_settings.refLyrIdField,
                        ref_id,
                    )

                    po_pro_ref_feature = get_feature_by_value(
                        self.derived_settings.poProRefLyr,
                        self.derived_settings.poProRefLyrIdField,
                        ref_id,
                    )
                except:
                    # should not happen, since queried by common ids
                    error_ref_ids.add(ref_id)
                    continue

                assigned_data_features = get_features_by_value(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyrReferenceField,
                    ref_id,
                )

                for assigned_data_feature in assigned_data_features:
                    data_id = assigned_data_feature[
                        self.stored_settings.dataLyrIdFieldName
                    ]

                    stationing_from_xyz = assigned_data_feature[
                        self.stored_settings.dataLyrStationingFromFieldName
                    ]

                    stationing_to_xyz = assigned_data_feature[
                        self.stored_settings.dataLyrStationingToFieldName
                    ]

                    offset = assigned_data_feature[
                        self.stored_settings.dataLyrOffsetFieldName
                    ]

                    try:
                        cu_cu_lr_geom = LoL.init_by_reference_geom(
                            ref_feature.geometry(),
                            self.derived_settings.refLyr.crs(),
                            stationing_from_xyz,
                            stationing_to_xyz,
                            offset,
                            self.stored_settings.lrMode,
                        )

                        po_pro_lol_instance = LoL.init_by_reference_geom(
                            po_pro_ref_feature.geometry(),
                            self.derived_settings.poProRefLyr.crs(),
                            stationing_from_xyz,
                            stationing_to_xyz,
                            offset,
                            self.stored_settings.lrMode,
                        )

                        cu_cu_calc_geom = cu_cu_lr_geom.geometry()
                        po_pro_segment = po_pro_lol_instance.geometry()

                        if cu_cu_calc_geom and po_pro_segment:
                            if not po_pro_segment.equals(cu_cu_calc_geom):
                                affected_data_ids.add(data_id)
                                po_pro_cache[data_id] = {
                                    "data_fid": assigned_data_feature.id(),
                                    "data_id": data_id,
                                    "stationing_from": stationing_from_xyz,
                                    "stationing_to": stationing_to_xyz,
                                    "offset": offset,
                                    "ref_id": ref_id,
                                }
                        else:
                            error_data_ids.add(data_id)
                    except:
                        error_data_ids.add(data_id)

            if error_ref_ids:
                self.dlg_append_log_message(
                    "WARNING", MY_DICT.tr("po_pro_error_ref_ids", error_ref_ids)
                )

            if error_data_ids:
                self.dlg_append_log_message(
                    "WARNING", MY_DICT.tr("po_pro_error_data_ids", error_data_ids)
                )

            # Tricky: compare new po_pro_cache with self.session_data.po_pro_cache

            yes_all = None
            no_all = None
            for data_id in po_pro_cache:
                if data_id in self.session_data.po_pro_cache:
                    if po_pro_cache[data_id] != self.session_data.po_pro_cache[data_id]:
                        if yes_all:
                            po_pro_cache[data_id] = self.session_data.po_pro_cache[
                                data_id
                            ]
                        elif no_all:
                            pass
                        else:
                            try:
                                po_pro_feature = self.tool_init_po_pro_feature(data_id)
                                self.cvs_show_po_pro_difference(
                                    po_pro_feature, "zoom_bounds_out"
                                )
                            except:
                                pass

                            dialog_result = QMessageBox.question(
                                None,
                                f"LinearReferencing ({get_debug_pos()})",
                                MY_DICT.tr("keep_po_pro_cached_feature", data_id),
                                buttons=QMessageBox.Yes
                                | QMessageBox.No
                                | QMessageBox.YesAll
                                | QMessageBox.NoAll,
                                defaultButton=QMessageBox.Yes,
                            )

                            if dialog_result in [QMessageBox.Yes, QMessageBox.YesAll]:
                                po_pro_cache[data_id] = self.session_data.po_pro_cache[
                                    data_id
                                ]

                            yes_all = dialog_result == QMessageBox.YesAll

                            no_all = dialog_result == QMessageBox.NoAll

            self.session_data.po_pro_cache = po_pro_cache

    def sys_create_data_lyr(self):
        """create a geometry-less GeoPackage-layer for storing the linear-references

        fid-column (auto-incremented integer)
        join-column to reference-layer (type dependend on reference-layer id-field-type)
        numerical columns for from/to stationing and offset

        register this layer for plugin usage
        """
        # Rev. 2026-01-13
        data_lyr = None
        # self.derived_settings.refLyrIdField, necessary because the type of the created Reference-field must fit to the referenced primary-key-field
        if SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            if self.create_data_lyr_dialog is None:
                self.create_data_lyr_dialog = LolCreateDataLayerDialog(self.iface)

            if self.create_data_lyr_dialog.exec():
                if self.create_data_lyr_dialog.pre_check_ok:

                    id_field_name = self.create_data_lyr_dialog.id_field_name
                    reference_field_name = (
                        self.create_data_lyr_dialog.reference_field_name
                    )
                    stationing_from_field_name = (
                        self.create_data_lyr_dialog.stationing_from_field_name
                    )
                    stationing_to_field_name = (
                        self.create_data_lyr_dialog.stationing_to_field_name
                    )
                    offset_field_name = self.create_data_lyr_dialog.offset_field_name
                    fields = QgsFields()

                    fields.append(QgsField(id_field_name, QT_INT))

                    # same type as refLyrIdField
                    fields.append(
                        QgsField(
                            reference_field_name,
                            self.derived_settings.refLyrIdField.type(),
                        )
                    )

                    fields.append(QgsField(stationing_from_field_name, QT_DOUBLE))

                    fields.append(QgsField(stationing_to_field_name, QT_DOUBLE))

                    fields.append(QgsField(offset_field_name, QT_DOUBLE))

                    if self.create_data_lyr_dialog.layer_type == "memory":
                        memory_layer_name = (
                            self.create_data_lyr_dialog.memory_layer_name
                        )

                        data_lyr = QgsVectorLayer("None", memory_layer_name, "memory")
                        data_lyr.dataProvider().addAttributes(fields)
                        data_lyr.updateFields()

                        # tricky: auto-incremented ID-Field in memory-layer
                        # this is *NOT* the feature-ID
                        default_val = QgsDefaultValue(
                            # f"""CASE WHEN maximum("{id_field_name}") is NULL THEN 1 WHEN "{id_field_name}" is NULL THEN maximum("{id_field_name}")+1 ELSE "{id_field_name}" END""",
                            f"""if (maximum("{id_field_name}") is NULL, 1, maximum("{id_field_name}") + 1)""",
                            applyOnUpdate=False,
                        )

                        data_lyr.setDefaultValueDefinition(
                            data_lyr.fields().lookupField(id_field_name), default_val
                        )

                        # keep memory-layer hidden
                        # vl.setFlags(QgsMapLayer.Private)
                        QgsProject.instance().addMapLayer(data_lyr)

                    else:
                        gpkg_path = self.create_data_lyr_dialog.gpkg_path
                        gpkg_layer_name = self.create_data_lyr_dialog.gpkg_layer_name

                        options = QgsVectorFileWriter.SaveVectorOptions()
                        options.driverName = "gpkg"

                        # stupid implementation, but else error "Opening of data source in update mode failed..."
                        if not os.path.exists(gpkg_path):
                            options.actionOnExistingFile = (
                                QgsVectorFileWriter.CreateOrOverwriteFile
                            )
                        else:
                            options.actionOnExistingFile = (
                                QgsVectorFileWriter.CreateOrOverwriteLayer
                            )

                        options.layerName = gpkg_layer_name

                        # "fid" ist the default-name in GPKG for Feature-ID (Primary key, integer, auto-increment)
                        # if not listed in the field-list it is automatically created
                        # if listed it is automatically used
                        # to use any other integer column add 'options.layerOptions = ["FID=any_other_integer_column_name"]'
                        # see https://gdal.org/drivers/vector/gpkg.html#layer-creation-options
                        options.layerOptions = [f"FID={id_field_name}"]

                        # geometry-less table needs anyway three Dummy-Attributes for geometrie-type, projection and transformation
                        writer = QgsVectorFileWriter.create(
                            gpkg_path,
                            fields,
                            QgsWkbTypes.NoGeometry,
                            QgsCoordinateReferenceSystem(""),  # dummy
                            QgsCoordinateTransformContext(),
                            options,
                        )

                        # creates a SQLite/SpatialLite-table
                        if writer.hasError() == QgsVectorFileWriter.NoError:
                            # Important:
                            # "del writer" *before* "addVectorLayer"
                            # seems to be necessary, else gpkg exists, but created layer not valid
                            # perhaps layer is physically created after "del writer"?
                            del writer

                            uri = gpkg_path + "|layername=" + gpkg_layer_name
                            data_lyr = self.iface.addVectorLayer(
                                uri, gpkg_layer_name, "ogr"
                            )
                        else:
                            # perhaps write-permission?
                            self.dlg_append_log_message(
                                "WARNING",
                                MY_DICT.tr(
                                    "error_creating_layer",
                                    f"{gpkg_path}.{gpkg_layer_name}",
                                    writer.errorMessage(),
                                ),
                            )

                    if data_lyr and data_lyr.isValid():
                        data_lyr.setFieldConstraint(
                            data_lyr.fields().indexOf(id_field_name),
                            QgsFieldConstraints.Constraint.ConstraintUnique,
                        )
                        data_lyr.setFieldConstraint(
                            data_lyr.fields().indexOf(id_field_name),
                            QgsFieldConstraints.Constraint.ConstraintNotNull,
                        )
                        self.stored_settings.dataLyrId = data_lyr.id()
                        self.stored_settings.dataLyrIdFieldName = id_field_name
                        self.stored_settings.dataLyrReferenceFieldName = (
                            reference_field_name
                        )
                        self.stored_settings.dataLyrStationingFromFieldName = (
                            stationing_from_field_name
                        )
                        self.stored_settings.dataLyrStationingToFieldName = (
                            stationing_to_field_name
                        )
                        self.stored_settings.dataLyrOffsetFieldName = offset_field_name

                        self.sys_connect_data_lyr()

                        self.dlg_refract_measurement()
                        self.dlg_populate_settings()
                        self.dlg_reset_feature_selection()
                        self.dlg_refresh_measurement()
                        self.dlg_refresh_po_pro_edit()

                        data_lyr.startEditing()
                        self.iface.setActiveLayer(data_lyr)
                        self.sys_set_tool_mode("measure_segment")
                        self.dlg_show_tab("measurement")

                        self.dlg_append_log_message(
                            "SUCCESS",
                            MY_DICT.tr("data_lyr_created"),
                        )

                        if not self.stored_settings.lrMode or (self.stored_settings.lrMode in ["Mabs", "Mfract"] and not SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs):
                            self.stored_settings.lrMode = "Nabs"
                            self.dlg_append_log_message(
                                "WARNING", MY_DICT.tr("auto_switched_lr_mode")
                            )

                        self.sys_create_show_layer()

                    else:
                        # if for example the GeoPackage is exclusively accessed by "DB Browser for SQLite"...
                        self.dlg_append_log_message(
                            "WARNING",
                            MY_DICT.tr(
                                "error_creating_layer",
                            ),
                        )

                else:
                    self.dlg_append_log_message(
                        "WARNING", self.create_data_lyr_dialog.invalid_reason
                    )
            else:
                # dialog closed by user
                pass

        else:
            self.dlg_append_log_message("WARNING", MY_DICT.tr("ref_lyr_missing"))

    def sys_create_show_layer(self):
        """create and register virtual layer combining Data- and Reference-Layer"""
        # Rev. 2026-01-13
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            # unique name for the virtual layer within project,
            # include current lrMode for convenience
            layer_names = [
                layer.name() for layer in QgsProject.instance().mapLayers().values()
            ]
            template = f"LoL-Show-Layer [{{curr_i}}] '{self.derived_settings.dataLyr.name()}' ({self.stored_settings.lrMode})"
            show_layer_name = get_unique_string(layer_names, template, 1)

            show_lyr_sql = "SELECT"
            field_sql_lst = []
            # only the necessary attributes of Data-Layer are included, the other come via join
            # the field-names are taken from the registered data-layer, they must not correspond to the default names used in sys_create_memory_data_lyr/sys_create_data_lyr
            field_sql_lst.append(
                f" data_lyr.{self.derived_settings.dataLyrIdField.name()}"
            )
            field_sql_lst.append(
                f" data_lyr.{self.derived_settings.dataLyrReferenceField.name()}"
            )
            field_sql_lst.append(
                f" data_lyr.{self.derived_settings.dataLyrStationingFromField.name()}"
            )
            field_sql_lst.append(
                f" data_lyr.{self.derived_settings.dataLyrStationingToField.name()}"
            )
            field_sql_lst.append(
                f" data_lyr.{self.derived_settings.dataLyrOffsetField.name()}"
            )

            # Geometry-Expression with "special comment" according https://docs.qgis.org/testing/en/docs/user_manual/managing_data_source/create_layers.html#creating-virtual-layers
            # ST_Line_Substring and ST_Locate_Between_Measures require from-stationing <= to_stationing, else no result-geometry
            # N-stationing can be done with multi-linestring-geometries, if geometries are either single-parted or multi-parted but without gaps
            # Note: Shape-files are allways multi-type-layers (with mostly single-type geometries)
            # Note 2: the queries expect from-stationing <= to-stationing, they don't return segment-geometries in the reverse case
            # Note 3: the geometry-constructors need a valid offset => no segments with Null/None/''
            line_geom_alias = "line_geom_" + self.stored_settings.lrMode
            if self.stored_settings.lrMode == "Nabs":

                field_sql_lst.append(
                    f"""
                ST_OffsetCurve(
                    ST_Line_Substring(
                        st_linemerge(ref_lyr.geometry),
                        data_lyr.'{self.derived_settings.dataLyrStationingFromField.name()}'/st_length(st_linemerge(ref_lyr.geometry)),
                        data_lyr.'{self.derived_settings.dataLyrStationingToField.name()}'/st_length(st_linemerge(ref_lyr.geometry))
                    ),
                    data_lyr.'{self.derived_settings.dataLyrOffsetField.name()}'
                ) as {line_geom_alias} /*:linestring:{self.derived_settings.refLyr.crs().postgisSrid()}*/"""
                )
            elif self.stored_settings.lrMode == "Nfract":
                # same as above, but stationings as fractions of reference-line-length, so no need for "/st_length(st_linemerge(ref_lyr.geometry))"
                field_sql_lst.append(
                    f"""
                ST_OffsetCurve(
                    ST_Line_Substring(
                        ST_LineMerge(ref_lyr.geometry),
                        data_lyr.'{self.derived_settings.dataLyrStationingFromField.name()}',
                        data_lyr.'{self.derived_settings.dataLyrStationingToField.name()}'
                    ),
                    data_lyr.'{self.derived_settings.dataLyrOffsetField.name()}'
                ) as {line_geom_alias} /*:linestring:{self.derived_settings.refLyr.crs().postgisSrid()}*/"""
                )
            elif self.stored_settings.lrMode == "Mabs":
                # Uuh... quite complicated!
                # see https://www.gaia-gis.it/gaia-sins/spatialite-sql-latest.html:
                #
                # 1. ST_TrajectoryInterpolatePoint(geom, measure)
                # Check if a Geometry corresponds to a valid Trajectory.
                # Return a POINT Geometry being interpolated along the Geometry (that is expected to be a valid Trajectory) accordingly to the given M-value.
                # The interpolated Point will have the same dimensions and SRID of the Trajectory.

                # 2. ST_Line_Locate_Point(geom, point)
                # return a number (between 0.0 and 1.0) representing the location of the closest point on LineString to the given Point, as a fraction of total 2d line length.
                # NULL is returned for invalid arguments

                # 3. ST_Line_Substring(geom, N-fract-from-measure, N-fract-to-measure)
                # Return a Linestring being a substring of the input one starting and ending at the given fractions of total 2d length.
                # Second and third arguments are expected to be in the range between 0.0 and 1.0.
                # NULL is returned for invalid arguments

                # 4. ST_OffsetCurve(geom, offset)
                # return a geometric object representing the corresponding left-sided (positive radius) or right-sided (negative radius) offset curve
                # NULL is returned whenever is not possible deriving an offset curve from the original geometry
                # [a single not-closed LINESTRING is expected as input]offset the segment from line

                field_sql_lst.append(
                    f"""
                ST_OffsetCurve(
                    ST_Line_Substring(
                        ref_lyr.geometry,
                        ST_Line_Locate_Point(
                            ref_lyr.geometry,
                            ST_TrajectoryInterpolatePoint(
                                ref_lyr.geometry,
                                data_lyr.'{self.derived_settings.dataLyrStationingFromField.name()}'
                            )
                        ),
                        ST_Line_Locate_Point(
                            ref_lyr.geometry,
                            ST_TrajectoryInterpolatePoint(
                                ref_lyr.geometry,
                                data_lyr.'{self.derived_settings.dataLyrStationingToField.name()}'
                            )
                        )
                    ),data_lyr.'{self.derived_settings.dataLyrOffsetField.name()}'
                ) as {line_geom_alias} /*:linestring:{self.derived_settings.refLyr.crs().postgisSrid()}*/"""
                )

            else:
                raise NotImplementedError(
                    f"lr_mode '{self.stored_settings.lrMode}' not implemented"
                )

            show_lyr_sql += ",\n".join(field_sql_lst)
            show_lyr_sql += (
                f"\nFROM  '{self.derived_settings.dataLyr.id()}' as data_lyr"
            )
            show_lyr_sql += (
                f"\n  INNER JOIN '{self.derived_settings.refLyr.id()}' as ref_lyr"
            )
            integer_field_types = [
                QMetaType.Int,
                QMetaType.UInt,
                QMetaType.LongLong,
                QMetaType.ULongLong,
            ]
            if (
                self.derived_settings.dataLyrReferenceField.type()
                in integer_field_types
            ):
                show_lyr_sql += f" ON data_lyr.'{self.stored_settings.dataLyrReferenceFieldName}' = ref_lyr.'{self.derived_settings.refLyrIdField.name()}'"
            else:
                # needed with non-integer join-fields, bug?
                # makes the query/layer *very* slow, presumably because of missing indexes?
                # -> better avoid non-integer PKs
                show_lyr_sql += f" ON (data_lyr.'{self.stored_settings.dataLyrReferenceFieldName}' = ref_lyr.'{self.derived_settings.refLyrIdField.name()}') = True"

            # note:
            # layer is valid without urllib.parse.quote, but cl.dataProvider().uri().uri() returns only a partial query
            # Virtual layers created manually via QGis "Create virtual layer"/"Edit virtual layer"-tools are quoted, surprisingly only *partially* for field identifiers and linebreaks
            # uri = f"?query={show_lyr_sql}"
            uri = f"?query={urllib.parse.quote(show_lyr_sql)}"

            # set uid-Field for virtual Layer via "&uid="
            # only for integer-PKs
            # advantage: no artificial fid used, feature.id() returns this value
            # if the Name of a string-PK would be used for that param
            # -> no error
            # -> the layer will show in canvas
            # -> but the associated table has only *one* record
            if self.derived_settings.dataLyrIdField.type() in integer_field_types:
                uri += f"&uid={self.derived_settings.dataLyrIdField.name()}"

            # "&geometry=line_geom:Linestring:25832" -> alias:geometry-type:srid (same as Reference-Layer)
            # variant: "&geometry=line_geom:2:25832"
            # anyway under windows:
            # the "Virtual Layer Dialog shows for "Geometry" allways "Autodetect" instead "Manually defined", so the whole
            # "&geometry=line_geom:Linestring:25832"-part seems to be ignored, bug?
            # but "Autodetect" seems to detect the only geometry in the query-result and its geometry-type and srid
            uri += f"&geometry={line_geom_alias}:Linestring:{self.derived_settings.refLyr.crs().postgisSrid()}"

            show_lyr = QgsVectorLayer(uri, show_layer_name, "virtual")
            if show_lyr and show_lyr.renderer():

                # Join Data-Layer
                qvl_join_data_lyr = QgsVectorLayerJoinInfo()
                qvl_join_data_lyr.setJoinLayer(self.derived_settings.dataLyr)
                qvl_join_data_lyr.setJoinFieldName(
                    self.derived_settings.dataLyrIdField.name()
                )
                # 1:1 join, using the identical field-name
                self.stored_settings.showLyrBackReferenceFieldName = (
                    self.derived_settings.dataLyrIdField.name()
                )
                qvl_join_data_lyr.setTargetFieldName(
                    self.stored_settings.showLyrBackReferenceFieldName
                )
                qvl_join_data_lyr.setUsingMemoryCache(True)
                show_lyr.addJoin(qvl_join_data_lyr)

                # Join Reference-Layer
                qvl_join_ref_lyr = QgsVectorLayerJoinInfo()
                qvl_join_ref_lyr.setJoinLayer(self.derived_settings.refLyr)
                qvl_join_ref_lyr.setJoinFieldName(
                    self.derived_settings.refLyrIdField.name()
                )
                qvl_join_ref_lyr.setTargetFieldName(
                    self.derived_settings.dataLyrReferenceField.name()
                )
                qvl_join_ref_lyr.setUsingMemoryCache(True)
                show_lyr.addJoin(qvl_join_ref_lyr)

                show_lyr.renderer().symbol().setWidthUnit(
                    QgsUnitTypes.RenderUnit.RenderPixels
                )
                show_lyr.renderer().symbol().setWidth(6)
                # mint-green
                show_lyr.renderer().symbol().setColor(QColor("#90EE90"))
                show_lyr.renderer().symbol().setOpacity(0.8)

                # additional, should already be done by uri
                show_lyr.setCrs(self.derived_settings.refLyr.crs())

                QgsProject.instance().addMapLayer(show_lyr)

                self.stored_settings.showLyrId = show_lyr.id()

                self.sys_connect_show_layer()
                self.dlg_populate_settings()
                self.dlg_reset_feature_selection()
                self.dlg_append_log_message("SUCCESS", MY_DICT.tr("show_layer_created"))
            else:
                self.dlg_append_log_message(
                    "WARNING", MY_DICT.tr("error_creating_virtual_layer")
                )
        else:
            self.dlg_append_log_message(
                "INFO", MY_DICT.tr("reference_or_data_lyr_missing")
            )

    def s_update_feature(self):
        """
        opens feature-form for selected feature (self.session_data.edit_feature_fid)
        with updated geometry (self.session_data.lr_geom_runtime)
        layer must be editable
        insert to edit-buffer is done by OK-click on feature-form
        """
        # Rev. 2026-01-13
        # Check: Privileges sufficient and Layer in Edit-Mode
        try:
            if (
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                | SVS.DATA_LAYER_EDITABLE
                | SVS.DATA_LAYER_UPDATE_ENABLED
            ) in self.system_vs:
                if (
                    self.session_data.edit_feature_fid is not None
                    and self.session_data.lr_geom_runtime is not None
                ):
                    data_feature = self.tool_get_data_feature(
                        data_fid=self.session_data.edit_feature_fid
                    )

                    if self.session_data.lr_geom_runtime.ref_fid > 0:
                        # ensure referenced feature is committed to provider
                        ref_feature = self.tool_get_reference_feature(
                            ref_fid=self.session_data.lr_geom_runtime.ref_fid
                        )

                        if self.stored_settings.lrMode in ["Mabs", "Mfract"]:
                            # check obsolete, because there would be no lr_geom_runtime without m-valid geometry
                            if SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                                if (
                                    not self.session_data.lr_geom_runtime.linestring_statistics.m_valid
                                ):
                                    raise GeometryNotMValidException(
                                        self.session_data.lr_geom_runtime.linestring_statistics.m_error,
                                        self.derived_settings.refLyr.name(),
                                        self.session_data.lr_geom_runtime.ref_fid,
                                    )
                            else:
                                # should not happen
                                raise LayerNotMEnabledException(
                                    self.derived_settings.refLyr.name()
                                )

                        ref_id = ref_feature[
                            self.derived_settings.refLyrIdField.name()
                        ]
                        if check_attribute_value(ref_id):
                            # ensure that a valid reference-id is defined
                            stationing_from_xyz, stationing_to_xyz = (
                                self.session_data.lr_geom_runtime.get_stationings(
                                    self.stored_settings.lrMode
                                )
                            )

                            if stationing_from_xyz > stationing_to_xyz:
                                # swap from-to-measurements
                                stationing_from_xyz, stationing_to_xyz = (
                                    stationing_to_xyz,
                                    stationing_from_xyz,
                                )

                                self.dlg_append_log_message(
                                    "INFO", MY_DICT.tr("from_to_switched")
                                )

                            offset = self.session_data.lr_geom_runtime.offset

                            if self.stored_settings.storagePrecision >= 0:
                                stationing_from_xyz = (
                                    math.floor(
                                        stationing_from_xyz
                                        * 10**self.stored_settings.storagePrecision
                                    )
                                    / 10**self.stored_settings.storagePrecision
                                )
                                stationing_to_xyz = (
                                    math.floor(
                                        stationing_to_xyz
                                        * 10**self.stored_settings.storagePrecision
                                    )
                                    / 10**self.stored_settings.storagePrecision
                                )
                                offset = round(
                                    offset,
                                    self.stored_settings.storagePrecision,
                                )

                            feature_form = self.iface.getFeatureForm(
                                self.derived_settings.dataLyr, data_feature
                            )

                            feature_form.attributeForm().changeAttribute(
                                self.derived_settings.dataLyrReferenceField.name(),
                                ref_id,
                            )
                            feature_form.attributeForm().changeAttribute(
                                self.derived_settings.dataLyrOffsetField.name(),
                                offset,
                            )
                            feature_form.attributeForm().changeAttribute(
                                self.derived_settings.dataLyrStationingFromField.name(),
                                stationing_from_xyz,
                            )
                            feature_form.attributeForm().changeAttribute(
                                self.derived_settings.dataLyrStationingToField.name(),
                                stationing_to_xyz,
                            )

                            feature_form.show()

                            if self.session_data.last_dlg_position:
                                # convenience: restore last size
                                # not position, cause feature_form.move() or feature_form.setGeometry(...) results in jumping dialog
                                feature_form.resize(self.session_data.last_dlg_position[2],self.session_data.last_dlg_position[3])


                            eventFilter = featureFormEventFilter(feature_form)
                            eventFilter.feature_form_repositioned.connect(self.dlg_store_size_and_position)

                        else:
                            raise FeatureAttributeInvalidException(
                                self.derived_settings.refLyr.name(),
                                self.session_data.lr_geom_runtime.ref_fid,
                                self.derived_settings.refLyrIdField.name(),
                            )

                    else:
                        raise ReferencedFeatureNotCommittedException(
                            self.derived_settings.refLyr.name(),
                            self.session_data.lr_geom_runtime.ref_fid,
                        )
                else:
                    # should not happen, because the insert-button would be disabled
                    raise RuntimeObjectMissingException("Digitized Feature")
            else:
                # should not happen, because the insert-button would be disabled
                raise LayerNotEditableException(self.derived_settings.dataLyr.name())

        except Exception as e:
            self.sys_log_exception(e)

    def s_insert_feature(self):
        """
        opens feature-form for new feature with geometry-metas (self.session_data.lr_geom_runtime)
        layer must be editable
        insert to edit-buffer is done by OK-click on feature-form
        """
        # Rev. 2026-01-13
        # Check: Privileges sufficient and Layer in Edit-Mode
        try:
            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                if (
                    SVS.DATA_LAYER_EDITABLE | SVS.DATA_LAYER_INSERT_ENABLED
                ) in self.system_vs:
                    if self.session_data.lr_geom_runtime is not None:
                        if self.session_data.lr_geom_runtime.ref_fid > 0:
                            # ensure, reference-feature is committed to provider
                            ref_feature = self.tool_get_reference_feature(
                                ref_fid=self.session_data.lr_geom_runtime.ref_fid
                            )

                            if self.stored_settings.lrMode in ["Mabs", "Mfract"]:
                                # check obsolete, else there was no lr_geom_runtime...
                                if SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                                    if (
                                        not self.session_data.lr_geom_runtime.linestring_statistics.m_valid
                                    ):
                                        raise GeometryNotMValidException(
                                            self.session_data.lr_geom_runtime.linestring_statistics.m_error,
                                            self.derived_settings.refLyr.name(),
                                            self.session_data.lr_geom_runtime.ref_fid,
                                        )
                                else:
                                    # should not happen
                                    raise LayerNotMEnabledException(
                                        self.derived_settings.refLyr.name()
                                    )

                            ref_id = ref_feature[
                                self.derived_settings.refLyrIdField.name()
                            ]
                            if check_attribute_value(ref_id):
                                # ensure ref_id is set
                                stationing_from_xyz, stationing_to_xyz = (
                                    self.session_data.lr_geom_runtime.get_stationings(
                                        self.stored_settings.lrMode
                                    )
                                )

                                if stationing_from_xyz > stationing_to_xyz:
                                    # swap from-to-measurements
                                    stationing_from_xyz, stationing_to_xyz = (
                                        stationing_to_xyz,
                                        stationing_from_xyz,
                                    )

                                    self.dlg_append_log_message(
                                        "INFO", MY_DICT.tr("from_to_switched")
                                    )

                                offset = self.session_data.lr_geom_runtime.offset
                                if self.stored_settings.storagePrecision >= 0:
                                    stationing_from_xyz = (
                                        math.floor(
                                            stationing_from_xyz
                                            * 10
                                            ** self.stored_settings.storagePrecision
                                        )
                                        / 10**self.stored_settings.storagePrecision
                                    )
                                    stationing_to_xyz = (
                                        math.floor(
                                            stationing_to_xyz
                                            * 10
                                            ** self.stored_settings.storagePrecision
                                        )
                                        / 10**self.stored_settings.storagePrecision
                                    )
                                    offset = round(
                                        offset,
                                        self.stored_settings.storagePrecision,
                                    )

                                data_feature = QgsVectorLayerUtils.createFeature(
                                    self.derived_settings.dataLyr
                                )
                                data_feature[
                                    self.derived_settings.dataLyrReferenceField.name()
                                ] = ref_id

                                data_feature[
                                    self.derived_settings.dataLyrOffsetField.name()
                                ] = offset

                                data_feature[
                                    self.derived_settings.dataLyrStationingFromField.name()
                                ] = stationing_from_xyz

                                data_feature[
                                    self.derived_settings.dataLyrStationingToField.name()
                                ] = stationing_to_xyz
                                feature_form = self.iface.getFeatureForm(
                                    self.derived_settings.dataLyr, data_feature
                                )
                                feature_form.setMode(
                                    QgsAttributeEditorContext.AddFeatureMode
                                )
                                # modal => block the app => only one insert-feature-form visible at a time
                                feature_form.setModal(True)
                                feature_form.show()

                                if self.session_data.last_dlg_position:
                                    # convenience: restore last size
                                    # not position, cause feature_form.move() or feature_form.setGeometry(...) results in jumping dialog
                                    feature_form.resize(self.session_data.last_dlg_position[2],self.session_data.last_dlg_position[3])

                                eventFilter = featureFormEventFilter(feature_form)
                                eventFilter.feature_form_repositioned.connect(self.dlg_store_size_and_position)

                            else:
                                raise FeatureAttributeInvalidException(
                                    self.derived_settings.refLyr.name(),
                                    self.session_data.lr_geom_runtime.ref_fid,
                                    self.derived_settings.refLyrIdField.name(),
                                )

                        else:
                            raise ReferencedFeatureNotCommittedException(
                                self.derived_settings.refLyr.name(),
                                self.session_data.lr_geom_runtime.ref_fid,
                            )
                    else:
                        # should not happen, because the insert-button would be disabled
                        raise RuntimeObjectMissingException("Digitized Feature")
                else:
                    # should not happen, because the insert-button would be disabled
                    raise LayerNotEditableException(
                        self.derived_settings.dataLyr.name()
                    )
            else:
                raise LayerNotRegisteredException("RefLyr + DataLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def sys_set_tool_mode(self, tool_mode: str) -> bool:
        """sets self.session_data.tool_mode with simple checks
        Args:
            tool_mode (str):

        Returns:
            bool: True if the tool_mode could be set, False if something went wrong and the tool_mode could not be set
        """
        # Rev. 2026-01-13
        # switch-back-by-canvas-click-convenience
        self.session_data.previous_tool_mode = self.session_data.tool_mode
        self.session_data.tool_mode = None
        self.iface.mapCanvas().setCursor(Qt.ArrowCursor)
        # Snapping to reference-layer could have been disabled
        self.sys_apply_snapping_config()
        # MapTool has possibly changed, f. e. Pan
        self.iface.mapCanvas().setMapTool(self)
        tool_mode_ok = True
        if tool_mode in self.tool_modes:
            if tool_mode in ["select_features", "select_edit_feature"]:
                tool_mode_ok &= SVS.ALL_LAYERS_CONNECTED in self.system_vs
            elif tool_mode in ["measure_segment", "set_from_point", "set_to_point"]:
                tool_mode_ok &= SVS.REFERENCE_LAYER_USABLE in self.system_vs
            elif tool_mode in ["change_offset", "move_segment"]:
                tool_mode_ok &= SVS.REFERENCE_LAYER_USABLE in self.system_vs
                tool_mode_ok &= self.session_data.lr_geom_runtime is not None
            elif tool_mode in [
                "move_po_pro_segment",
                "move_po_pro_from",
                "move_po_pro_to",
            ]:
                tool_mode_ok &= (
                    SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                    | SVS.DATA_LAYER_EDITABLE
                    | SVS.DATA_LAYER_UPDATE_ENABLED
                ) in self.system_vs and self.session_data.po_pro_feature is not None

        else:
            self.dlg_append_log_message(
                "WARNING", MY_DICT.tr("tool_mode_not_implemented", tool_mode)
            )
            tool_mode_ok = False

        if tool_mode_ok:
            self.session_data.tool_mode = tool_mode
            self.gui_show_tool_mode(tool_mode)
        else:
            self.gui_show_tool_mode("disabled")
        return tool_mode_ok

    def dlg_reset_settings(self):
        """reset functional widgets and QActions on the settings-tab"""
        # Rev. 2026-01-13
        if self.my_dialog:
            clear_widgets = [
                self.my_dialog.qcbn_ref_lyr,
                self.my_dialog.qcbn_ref_lyr_id_field,
                self.my_dialog.qcbn_data_lyr,
                self.my_dialog.qcbn_data_lyr_id_field,
                self.my_dialog.qcbn_data_lyr_reference_field,
                self.my_dialog.qcbn_data_lyr_offset_field,
                self.my_dialog.qcbn_data_lyr_stationing_from_field,
                self.my_dialog.qcbn_data_lyr_stationing_to_field,
                self.my_dialog.qcb_lr_mode,
                self.my_dialog.qcb_storage_precision,
                self.my_dialog.qcb_display_precision,
                self.my_dialog.qcbn_show_lyr,
                self.my_dialog.qcbn_show_lyr_back_reference_field,
                self.my_dialog.qsb_snap_tolerance,
            ]

            for widget in clear_widgets:
                widget.blockSignals(True)
                widget.clear()
                widget.setEnabled(False)

            uncheck_widgets = [
                self.my_dialog.cb_snap_mode_vertex,
                self.my_dialog.cb_snap_mode_segment,
                self.my_dialog.cb_snap_mode_middle_of_segment,
                self.my_dialog.cb_snap_mode_line_endpoint,
            ]

            for widget in uncheck_widgets:
                widget.blockSignals(True)
                widget.setChecked(False)
                widget.setEnabled(False)

            disable_actions = [
                self.qact_open_ref_table,
                self.qact_define_ref_lyr_display_expression,
                self.qact_open_data_table,
                self.qact_define_data_lyr_display_expression,
                self.qact_create_data_lyr,
                self.qact_open_show_tbl,
                self.qact_create_show_lyr,
            ]
            for action in disable_actions:
                action.setEnabled(False)

    def dlg_refract_settings(self):
        """refresh QActions and functional widgets on the settings-tab
        Note: the Layer- and Field-Selector-Widgets are enabled in dlg_populate_settings
        """
        # Rev. 2026-01-13
        # Note: this QAction is used multiple
        self.qact_open_ref_table.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )

        self.qact_define_ref_lyr_display_expression.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )

        self.qact_open_data_table.setEnabled(
            (SVS.REFERENCE_LAYER_CONNECTED | SVS.DATA_LAYER_EXISTS) in self.system_vs
        )

        self.qact_define_data_lyr_display_expression.setEnabled(
            (SVS.REFERENCE_LAYER_CONNECTED | SVS.DATA_LAYER_EXISTS) in self.system_vs
        )

        self.qact_create_data_lyr.setEnabled(
            SVS.REFERENCE_LAYER_CONNECTED in self.system_vs
        )

        self.qact_open_show_tbl.setEnabled(SVS.ALL_LAYERS_CONNECTED in self.system_vs)

        self.qact_create_show_lyr.setEnabled(
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
        )

        self.my_dialog.qcb_storage_precision.setEnabled(
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
        )

        self.my_dialog.qcb_display_precision.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )

        self.my_dialog.cb_snap_mode_vertex.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )
        self.my_dialog.cb_snap_mode_segment.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )
        self.my_dialog.cb_snap_mode_middle_of_segment.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )
        self.my_dialog.cb_snap_mode_line_endpoint.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )
        self.my_dialog.qsb_snap_tolerance.setEnabled(
            SVS.REFERENCE_LAYER_USABLE in self.system_vs
        )

    def dlg_populate_settings(self):
        """refreshes the settings-part in dialog"""
        # Rev. 2026-01-13
        if self.my_dialog:

            block_widgets = [
                self.my_dialog.qcbn_ref_lyr,
                self.my_dialog.qcbn_ref_lyr_id_field,
                self.my_dialog.qcbn_data_lyr,
                self.my_dialog.qcbn_data_lyr_id_field,
                self.my_dialog.qcbn_data_lyr_reference_field,
                self.my_dialog.qcbn_data_lyr_offset_field,
                self.my_dialog.qcbn_data_lyr_stationing_from_field,
                self.my_dialog.qcbn_data_lyr_stationing_to_field,
                self.my_dialog.qcb_lr_mode,
                self.my_dialog.qcb_storage_precision,
                self.my_dialog.qcb_display_precision,
                self.my_dialog.qcbn_show_lyr,
                self.my_dialog.qcbn_show_lyr_back_reference_field,
                self.my_dialog.cb_snap_mode_vertex,
                self.my_dialog.cb_snap_mode_segment,
                self.my_dialog.cb_snap_mode_middle_of_segment,
                self.my_dialog.cb_snap_mode_line_endpoint,
                self.my_dialog.qsb_snap_tolerance,
            ]

            for widget in block_widgets:
                widget.blockSignals(True)

            # refresh Settings Layers and Fields...
            self.my_dialog.qcbn_ref_lyr.load_data(
                {"geometry_type": [Qgis.GeometryType.Line]},
                {"data_provider": ["virtual"]},
            )
            self.my_dialog.qcbn_ref_lyr.setEnabled(True)

            if self.derived_settings.refLyr:
                self.my_dialog.qcbn_ref_lyr.select_by_value(
                    [[0, Qt_Roles.RETURN_VALUE, Qt.MatchExactly]],
                    self.derived_settings.refLyr.id(),
                    True,
                )
                # Reference-Layer is selected, now select the Id-Field
                enable_criteria = {
                    "field_type": ["any_pk"],
                    # allow calculated fields
                    # "field_origin": [1],
                }
                self.my_dialog.qcbn_ref_lyr_id_field.load_data(
                    self.derived_settings.refLyr, enable_criteria
                )
                self.my_dialog.qcbn_ref_lyr_id_field.setEnabled(True)

                if self.derived_settings.refLyrIdField:
                    # Qt.ExactMatch doesn't match anything if used for fields, therefore match with role-index 0 (DisplayRole, Text-Content) with the (hopefully unique...) name of the field
                    self.my_dialog.qcbn_ref_lyr_id_field.select_by_value(
                        [[0, Qt_Roles.RETURN_VALUE, Qt.MatchExactly]],
                        self.derived_settings.refLyrIdField.name(),
                        True,
                    )
                    # PK-Field is selected, now the Data-Layer
                    # PK-Field is selected, now the Data-Layer
                    enable_criteria = {
                        "data_provider": ["ogr", "memory"],
                        "geometry_type": [Qgis.GeometryType.Null],
                    }

                    self.my_dialog.qcbn_data_lyr.load_data(enable_criteria)
                    self.my_dialog.qcbn_data_lyr.setEnabled(True)

                    if self.derived_settings.dataLyr:
                        self.my_dialog.qcbn_data_lyr.select_by_value(
                            [[0, Qt_Roles.RETURN_VALUE, Qt.MatchExactly]],
                            self.derived_settings.dataLyr.id(),
                            True,
                        )

                        # dataLyr set, now the ID-Field

                        enable_criteria = {
                            "field_type": ["any_pk"],
                            # allow calculated fields
                            # "field_origin": [1],
                        }

                        self.my_dialog.qcbn_data_lyr_id_field.load_data(
                            self.derived_settings.dataLyr, enable_criteria
                        )
                        self.my_dialog.qcbn_data_lyr_id_field.setEnabled(True)

                        if self.derived_settings.dataLyrIdField:
                            self.my_dialog.qcbn_data_lyr_id_field.select_by_value(
                                [[0, Qt_Roles.RETURN_VALUE, Qt.MatchExactly]],
                                self.derived_settings.dataLyrIdField.name(),
                                True,
                            )
                            # PkField set, now the Reference-Field
                            enable_criteria = {
                                "field_type": [
                                    "any_pk",
                                    self.derived_settings.refLyrIdField.type(),
                                ],
                                # allow calculated fields
                                # "field_origin": [1],
                            }

                            disable_criteria = {
                                "field_name": [
                                    self.derived_settings.dataLyrIdField.name()
                                ],
                                "field_idx": self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes(),
                            }

                            self.my_dialog.qcbn_data_lyr_reference_field.load_data(
                                self.derived_settings.dataLyr,
                                enable_criteria,
                                disable_criteria,
                            )
                            self.my_dialog.qcbn_data_lyr_reference_field.setEnabled(
                                True
                            )

                            if self.derived_settings.dataLyrReferenceField:
                                self.my_dialog.qcbn_data_lyr_reference_field.select_by_value(
                                    [
                                        [
                                            0,
                                            Qt_Roles.RETURN_VALUE,
                                            Qt.MatchExactly,
                                        ]
                                    ],
                                    self.derived_settings.dataLyrReferenceField.name(),
                                )

                                enable_criteria = {"field_type": ["any_number"]}

                                disable_criteria = {
                                    "field_name": [
                                        self.derived_settings.dataLyrIdField.name(),
                                        self.derived_settings.dataLyrReferenceField.name(),
                                    ],
                                    "field_idx": self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes(),
                                }

                                self.my_dialog.qcbn_data_lyr_offset_field.load_data(
                                    self.derived_settings.dataLyr,
                                    enable_criteria,
                                    disable_criteria,
                                )
                                self.my_dialog.qcbn_data_lyr_offset_field.setEnabled(
                                    True
                                )

                                if self.derived_settings.dataLyrOffsetField:
                                    self.my_dialog.qcbn_data_lyr_offset_field.select_by_value(
                                        [
                                            [
                                                0,
                                                Qt_Roles.RETURN_VALUE,
                                                Qt.MatchExactly,
                                            ]
                                        ],
                                        self.derived_settings.dataLyrOffsetField.name(),
                                    )

                                    enable_criteria = {"field_type": ["any_number"]}

                                    disable_criteria = {
                                        "field_name": [
                                            self.derived_settings.dataLyrIdField.name(),
                                            self.derived_settings.dataLyrReferenceField.name(),
                                            self.derived_settings.dataLyrOffsetField.name(),
                                        ],
                                        "field_idx": self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes(),
                                    }

                                    self.my_dialog.qcbn_data_lyr_stationing_from_field.load_data(
                                        self.derived_settings.dataLyr,
                                        enable_criteria,
                                        disable_criteria,
                                    )
                                    self.my_dialog.qcbn_data_lyr_stationing_from_field.setEnabled(
                                        True
                                    )

                                    if self.derived_settings.dataLyrStationingFromField:
                                        self.my_dialog.qcbn_data_lyr_stationing_from_field.select_by_value(
                                            [
                                                [
                                                    0,
                                                    Qt_Roles.RETURN_VALUE,
                                                    Qt.MatchExactly,
                                                ]
                                            ],
                                            self.derived_settings.dataLyrStationingFromField.name(),
                                        )

                                        enable_criteria = {"field_type": ["any_number"]}

                                        disable_criteria = {
                                            "field_name": [
                                                self.derived_settings.dataLyrIdField.name(),
                                                self.derived_settings.dataLyrReferenceField.name(),
                                                self.derived_settings.dataLyrOffsetField.name(),
                                                self.derived_settings.dataLyrStationingFromField.name(),
                                            ],
                                            "field_idx": self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes(),
                                        }
                                        self.my_dialog.qcbn_data_lyr_stationing_to_field.load_data(
                                            self.derived_settings.dataLyr,
                                            enable_criteria,
                                            disable_criteria,
                                        )
                                        self.my_dialog.qcbn_data_lyr_stationing_to_field.setEnabled(
                                            True
                                        )

                                        if (
                                            self.derived_settings.dataLyrStationingToField
                                        ):
                                            self.my_dialog.qcbn_data_lyr_stationing_to_field.select_by_value(
                                                [
                                                    [
                                                        0,
                                                        Qt_Roles.RETURN_VALUE,
                                                        Qt.MatchExactly,
                                                    ]
                                                ],
                                                self.derived_settings.dataLyrStationingToField.name(),
                                            )

                                            if (
                                                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                                                in self.system_vs
                                            ):
                                                lr_modes = {
                                                    "Nabs": MY_DICT.tr("lr_mode_n_abs"),
                                                    "Nfract": MY_DICT.tr(
                                                        "lr_mode_n_fract"
                                                    ),
                                                }
                                                if (
                                                    SVS.REFERENCE_LAYER_M_ENABLED
                                                    in self.system_vs
                                                ):
                                                    lr_modes["Mabs"] = MY_DICT.tr(
                                                        "lr_mode_m_abs"
                                                    )

                                                ic = 0
                                                for key in lr_modes:
                                                    self.my_dialog.qcb_lr_mode.addItem(
                                                        lr_modes[key], key
                                                    )
                                                    if (
                                                        key
                                                        == self.stored_settings.lrMode
                                                    ):
                                                        self.my_dialog.qcb_lr_mode.setCurrentIndex(
                                                            ic
                                                        )
                                                    ic += 1
                                                self.my_dialog.qcb_lr_mode.setEnabled(
                                                    True
                                                )

                                                ic = 0
                                                # -1 => no rounding
                                                for prec in range(-1, 9, 1):
                                                    self.my_dialog.qcb_storage_precision.addItem(
                                                        str(prec), prec
                                                    )
                                                    if (
                                                        prec
                                                        == self.stored_settings.storagePrecision
                                                    ):
                                                        self.my_dialog.qcb_storage_precision.setCurrentIndex(
                                                            ic
                                                        )
                                                    ic += 1

                                            prefetched_layers = []

                                            for cl in (
                                                QgsProject.instance()
                                                .mapLayers()
                                                .values()
                                            ):
                                                if (
                                                    cl.isValid()
                                                    and isinstance(cl, QgsVectorLayer)
                                                    and cl.geometryType()
                                                    == Qgis.GeometryType.Line
                                                ):
                                                    if (
                                                        cl.dataProvider().name()
                                                        == "ogr"
                                                    ):
                                                        # all non-virtual Line-Layers, f.e. PostGIS-Views
                                                        prefetched_layers.append(cl)
                                                    elif (
                                                        cl.dataProvider().name()
                                                        == "virtual"
                                                    ):

                                                        # or virtual-layers with fitting queries
                                                        virtual_check_contents = [
                                                            self.derived_settings.refLyr.id(),
                                                            self.derived_settings.refLyrIdField.name(),
                                                            self.derived_settings.dataLyr.id(),
                                                            self.derived_settings.dataLyrIdField.name(),
                                                            self.derived_settings.dataLyrReferenceField.name(),
                                                            self.derived_settings.dataLyrStationingFromField.name(),
                                                            self.derived_settings.dataLyrStationingToField.name(),
                                                            self.derived_settings.dataLyrOffsetField.name(),
                                                        ]

                                                        if (
                                                            self.stored_settings.lrMode
                                                            in [
                                                                "Nabs",
                                                                "Nfract",
                                                            ]
                                                        ):
                                                            virtual_check_contents.append(
                                                                "ST_Line_Substring"
                                                            )
                                                        elif (
                                                            self.stored_settings.lrMode
                                                            == "Mabs"
                                                        ):
                                                            virtual_check_contents.append(
                                                                "ST_TrajectoryInterpolatePoint"
                                                            )
                                                            virtual_check_contents.append(
                                                                "ST_Line_Substring"
                                                            )
                                                        if all(
                                                            s
                                                            in cl.dataProvider()
                                                            .uri()
                                                            .uri()
                                                            for s in virtual_check_contents
                                                        ):
                                                            prefetched_layers.append(cl)

                                            self.my_dialog.qcbn_show_lyr.load_data(
                                                {"layer": prefetched_layers}
                                            )
                                            self.my_dialog.qcbn_show_lyr.setEnabled(
                                                True
                                            )

                                            if self.derived_settings.showLyr:
                                                self.my_dialog.qcbn_show_lyr.select_by_value(
                                                    [
                                                        [
                                                            0,
                                                            Qt_Roles.RETURN_VALUE,
                                                            Qt.MatchExactly,
                                                        ]
                                                    ],
                                                    self.derived_settings.showLyr.id(),
                                                )

                                                enable_criteria = {
                                                    "field_type": [
                                                        "any_pk",
                                                        self.derived_settings.dataLyrIdField.type(),
                                                    ]
                                                }

                                                disable_criteria = {"field_origin": [2]}
                                                # no join-fields

                                                self.my_dialog.qcbn_show_lyr_back_reference_field.load_data(
                                                    self.derived_settings.showLyr,
                                                    enable_criteria,
                                                    disable_criteria,
                                                )
                                                self.my_dialog.qcbn_show_lyr_back_reference_field.setEnabled(
                                                    True
                                                )

                                                if (
                                                    self.derived_settings.showLyrBackReferenceField
                                                ):
                                                    self.my_dialog.qcbn_show_lyr_back_reference_field.select_by_value(
                                                        [
                                                            [
                                                                0,
                                                                Qt_Roles.RETURN_VALUE,
                                                                Qt.MatchExactly,
                                                            ]
                                                        ],
                                                        self.derived_settings.showLyrBackReferenceField.name(),
                                                    )

            ic = 0
            # no no-rounding
            for prec in range(0, 9, 1):
                self.my_dialog.qcb_display_precision.addItem(str(prec), prec)
                if prec == self.stored_settings.displayPrecision:
                    self.my_dialog.qcb_display_precision.setCurrentIndex(ic)
                ic += 1

            # Snapping-Settings
            self.my_dialog.cb_snap_mode_line_endpoint.setChecked(
                Qgis.SnappingType.LineEndpoint & self.stored_settings.snapMode
                == Qgis.SnappingType.LineEndpoint
            )
            self.my_dialog.cb_snap_mode_vertex.setChecked(
                Qgis.SnappingType.Vertex & self.stored_settings.snapMode
                == Qgis.SnappingType.Vertex
            )
            self.my_dialog.cb_snap_mode_middle_of_segment.setChecked(
                Qgis.SnappingType.MiddleOfSegment & self.stored_settings.snapMode
                == Qgis.SnappingType.MiddleOfSegment
            )
            self.my_dialog.cb_snap_mode_segment.setChecked(
                Qgis.SnappingType.Segment & self.stored_settings.snapMode
                == Qgis.SnappingType.Segment
            )
            self.my_dialog.qsb_snap_tolerance.setValue(
                self.stored_settings.snapTolerance
            )

            for widget in block_widgets:
                widget.blockSignals(False)

    def s_change_offset(self, offset: float) -> None:
        """triggered by offset-QDoubleSpinBox, set self.session_data.current_offset, redraws lr_geom_runtime with new offset
        Args:
            offset (float)
        """
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            self.session_data.current_offset = offset
            if self.session_data.lr_geom_runtime:
                self.session_data.lr_geom_runtime.offset = offset
                self.cvs_draw_lr_geom(
                    self.session_data.lr_geom_runtime,
                    ["snf", "snt", "sgn", "sg0", "rfl"],
                )
            else:
                raise RuntimeObjectMissingException("Digitized feature")
        except Exception as e:
            self.sys_log_exception(e)

    def dlg_reset_feature_selection(self):
        """Reset Feature-Selection-Tab"""
        # Rev. 2026-01-13
        if self.my_dialog:
            disable_actions = [
                self.qact_append_data_features,
            ]
            for action in disable_actions:
                action.setDisabled(True)

            self.dlg_feature_selection_get_pre_settings()

            if self.my_dialog.qtrv_feature_selection.model():
                self.my_dialog.qtrv_feature_selection.model().clear()

            header_labels = [
                MY_DICT.tr("qtrv_feature_selection_reference_lyr_hlbl"),
                MY_DICT.tr("qtrv_feature_selection_data_lyr_hlbl"),
                MY_DICT.tr("qtrv_feature_selection_stored_stationing_from_hlbl"),
                MY_DICT.tr("qtrv_feature_selection_stored_stationing_to_hlbl"),
                MY_DICT.tr("qtrv_feature_selection_offset_hlbl"),
                "",
            ]

            root_model = QStandardItemModel()
            self.my_dialog.qtrv_feature_selection.setModel(root_model)
            self.my_dialog.qtrv_feature_selection.model().setHorizontalHeaderLabels(
                header_labels
            )

    def dlg_reset_measurement(self):
        """clear measurement-widgets in Measurement-Tab
        except some refLayer-dependend-widgets, see dlg_reset_ref_lyr_select"""
        # Rev. 2026-01-13

        if self.my_dialog:

            clear_widgets = [
                self.my_dialog.dnspbx_snap_x_from,
                self.my_dialog.dnspbx_snap_y_from,
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_fract_from,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_fract_from,
                self.my_dialog.dnspbx_z_from,
                self.my_dialog.dnspbx_snap_x_to,
                self.my_dialog.dnspbx_snap_y_to,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_n_fract_to,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_m_fract_to,
                self.my_dialog.dnspbx_z_to,
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_n_fract,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dspbx_delta_m_fract,
                self.my_dialog.dnspbx_delta_z_abs,
                self.my_dialog.qlbl_m_valid_hint,
                self.qlbl_edit_data_feature,
            ]

            for widget in clear_widgets:
                widget.blockSignals(True)
                widget.clear()
                widget.blockSignals(False)

            self.qlbl_edit_data_feature.setToolTip(MY_DICT.tr("edit_data_fid_ttp"))

            disable_widgets = [
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_fract_from,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_fract_from,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_n_fract_to,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_m_fract_to,
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_n_fract,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dspbx_delta_m_fract,
            ]
            for widget in disable_widgets:
                widget.setDisabled(True)

            if SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                # enable only
                self.my_dialog.cbx_m_abs_grp.setEnabled(True)
                self.my_dialog.cbx_m_fract_grp.setEnabled(True)
            else:
                # disable and hide
                self.my_dialog.cbx_m_abs_grp.setEnabled(False)
                self.my_dialog.cbx_m_fract_grp.setEnabled(False)
                self.my_dialog.cbx_m_abs_grp.setChecked(False)
                self.my_dialog.cbx_m_fract_grp.setChecked(False)

            if SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs:
                # enable only
                self.my_dialog.cbx_z_grp.setEnabled(True)
            else:
                # disable and hide
                self.my_dialog.cbx_z_grp.setChecked(False)
                self.my_dialog.cbx_z_grp.setEnabled(False)

            disable_actions = [
                self.qact_move_to_start,
                self.qact_flip_down,
                self.qact_move_down,
                self.qact_measure_segment,
                self.qact_move_up,
                self.qact_flip_up,
                self.qact_move_end,
                self.qact_set_from_point,
                self.qact_set_to_point,
                self.qact_move_segment,
                self.qact_change_offset,
                self.qact_zoom_lr_geom,
                self.qact_toggle_edit_mode,
                self.qact_insert_feature,
                self.qact_update_feature,
                self.qact_select_edit_feature,
                self.qact_show_edit_feature_form,
            ]

            for action in disable_actions:
                action.setEnabled(False)

            self.qact_update_feature.setToolTip(MY_DICT.tr("update_edit_feature_tbtxt"))

            # hide/show some areas dependend on Reference-Layer-Geometry-Type
            self.my_dialog.cbx_edit_grp.setChecked(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
            )
            self.my_dialog.cbx_edit_grp.setVisible(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
            )

            self.my_dialog.cbx_n_abs_grp.setChecked(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )
            self.my_dialog.cbx_n_abs_grp.setVisible(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )

            self.my_dialog.cbx_n_fract_grp.setChecked(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )
            self.my_dialog.cbx_n_fract_grp.setVisible(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )

            self.my_dialog.cbx_m_fract_grp.setChecked(
                SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
            )
            self.my_dialog.cbx_m_fract_grp.setVisible(
                SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
            )

            self.my_dialog.cbx_m_abs_grp.setChecked(
                SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
            )
            self.my_dialog.cbx_m_abs_grp.setVisible(
                SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
            )

            self.my_dialog.cbx_m_fract_grp.setChecked(
                SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
            )
            self.my_dialog.cbx_m_fract_grp.setVisible(
                SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
            )

            self.my_dialog.cbx_z_grp.setChecked(
                SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs
            )
            self.my_dialog.cbx_z_grp.setVisible(
                SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs
            )

            self.my_dialog.cbx_snap_coords_grp.setChecked(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )
            self.my_dialog.cbx_snap_coords_grp.setVisible(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )

    def dlg_refract_measurement(self):
        """enables/disables QActions and Widgets dependend on session_data.lr_geom_runtime, privileges and layer-settings"""
        # Rev. 2026-01-13
        if self.my_dialog:

            measurement_exists = self.session_data.lr_geom_runtime is not None

            enable_n_widgets = [
                self.my_dialog.dnspbx_snap_x_from,
                self.my_dialog.dnspbx_snap_y_from,
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_fract_from,
                self.my_dialog.dnspbx_snap_x_to,
                self.my_dialog.dnspbx_snap_y_to,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_n_fract_to,
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_n_fract,
            ]

            for widget in enable_n_widgets:
                widget.setEnabled(measurement_exists)

            measurement_m_exists_and_valid = (
                SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
                and self.session_data.lr_geom_runtime is not None
                and self.session_data.lr_geom_runtime.linestring_statistics.m_valid
            )

            enable_m_widgets = [
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dspbx_m_fract_from,
                self.my_dialog.dspbx_m_fract_to,
                self.my_dialog.dspbx_delta_m_fract,
            ]

            for widget in enable_m_widgets:
                widget.setEnabled(measurement_m_exists_and_valid)

            measurement_z_exists = (
                SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs
                and self.session_data.lr_geom_runtime is not None
            )

            enable_z_widgets = [
                self.my_dialog.dnspbx_z_from,
                self.my_dialog.dnspbx_z_to,
                self.my_dialog.dnspbx_delta_z_abs,
            ]

            for widget in enable_z_widgets:
                widget.setEnabled(measurement_z_exists)

            enable_actions = [
                self.qact_move_to_start,
                self.qact_flip_down,
                self.qact_move_down,
                self.qact_move_up,
                self.qact_flip_up,
                self.qact_move_end,
                self.qact_move_segment,
                self.qact_change_offset,
                self.qact_zoom_lr_geom,
            ]

            for action in enable_actions:
                action.setEnabled(measurement_exists)

            self.qact_measure_segment.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )
            self.qact_set_from_point.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )
            self.qact_set_to_point.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )

            self.qact_toggle_edit_mode.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.DATA_LAYER_UPDATE_ENABLED
                in self.system_vs
            )

            self.qact_insert_feature.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                | SVS.DATA_LAYER_UPDATE_ENABLED
                | SVS.DATA_LAYER_EDITABLE
                in self.system_vs
                and (self.session_data.lr_geom_runtime is not None)
            )

            self.qact_show_edit_feature_form.setEnabled(
                SVS.DATA_LAYER_CONNECTED in self.system_vs
                and (self.session_data.edit_feature_fid is not None)
            )

            self.qact_update_feature.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                | SVS.DATA_LAYER_UPDATE_ENABLED
                | SVS.DATA_LAYER_EDITABLE
                in self.system_vs
                and (self.session_data.lr_geom_runtime is not None)
                and (self.session_data.edit_feature_fid is not None)
            )

            self.qact_select_edit_feature.setEnabled(
                SVS.ALL_LAYERS_CONNECTED | SVS.DATA_LAYER_UPDATE_ENABLED
                in self.system_vs
            )

    def dlg_populate_measurement(self):
        """shows metadata of self.session_data.lr_geom_runtime in Measurement-Tab"""
        # Rev. 2026-01-13
        if self.my_dialog:
            if self.session_data.lr_geom_runtime:
                block_widgets = [
                    # self.my_dialog.dnspbx_snap_x_from,
                    # self.my_dialog.dnspbx_snap_y_from,
                    self.my_dialog.dspbx_n_abs_from,
                    self.my_dialog.dspbx_n_fract_from,
                    self.my_dialog.dspbx_m_abs_from,
                    self.my_dialog.dspbx_m_fract_from,
                    self.my_dialog.dnspbx_z_from,
                    # self.my_dialog.dnspbx_snap_x_to,
                    # self.my_dialog.dnspbx_snap_y_to,
                    self.my_dialog.dspbx_n_abs_to,
                    self.my_dialog.dspbx_n_fract_to,
                    self.my_dialog.dspbx_m_abs_to,
                    self.my_dialog.dspbx_m_fract_to,
                    # self.my_dialog.dnspbx_z_to,
                    self.my_dialog.dspbx_delta_n_abs,
                    self.my_dialog.dspbx_delta_n_fract,
                    self.my_dialog.dspbx_delta_m_abs,
                    self.my_dialog.dspbx_delta_m_fract,
                    # self.my_dialog.dnspbx_delta_z_abs,
                ]

                for widget in block_widgets:
                    widget.blockSignals(True)

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_x_lyr_from, numbers.Number
                ):
                    self.my_dialog.dnspbx_snap_x_from.setValue(
                        self.session_data.lr_geom_runtime.snap_x_lyr_from
                    )

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_y_lyr_from, numbers.Number
                ):
                    self.my_dialog.dnspbx_snap_y_from.setValue(
                        self.session_data.lr_geom_runtime.snap_y_lyr_from
                    )

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_n_abs_from, numbers.Number
                ):
                    self.my_dialog.dspbx_n_abs_from.setValue(
                        self.session_data.lr_geom_runtime.snap_n_abs_from
                    )

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_n_fract_from, numbers.Number
                ):
                    # TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
                    self.my_dialog.dspbx_n_fract_from.setValue(
                        self.session_data.lr_geom_runtime.snap_n_fract_from * 100
                    )

                if SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_m_abs_from,
                        numbers.Number,
                    ):
                        self.my_dialog.dspbx_m_abs_from.setValue(
                            self.session_data.lr_geom_runtime.snap_m_abs_from
                        )
                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_m_fract_from,
                        numbers.Number,
                    ):
                        self.my_dialog.dspbx_m_fract_from.setValue(
                            self.session_data.lr_geom_runtime.snap_m_fract_from * 100
                        )

                    if (
                        not self.session_data.lr_geom_runtime.linestring_statistics.m_valid
                    ):

                        self.my_dialog.qlbl_m_valid_hint.setText(
                            MY_DICT.tr(
                                "reference_geom_not_m_valid",
                                self.session_data.lr_geom_runtime.linestring_statistics.m_error,
                            )
                        )

                if SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs:
                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_z_abs_from,
                        numbers.Number,
                    ):
                        self.my_dialog.dnspbx_z_from.setValue(
                            self.session_data.lr_geom_runtime.snap_z_abs_from
                        )

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_x_lyr_to, numbers.Number
                ):
                    self.my_dialog.dnspbx_snap_x_to.setValue(
                        self.session_data.lr_geom_runtime.snap_x_lyr_to
                    )

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_y_lyr_to, numbers.Number
                ):
                    self.my_dialog.dnspbx_snap_y_to.setValue(
                        self.session_data.lr_geom_runtime.snap_y_lyr_to
                    )

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_n_abs_to, numbers.Number
                ):
                    self.my_dialog.dspbx_n_abs_to.setValue(
                        self.session_data.lr_geom_runtime.snap_n_abs_to
                    )

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_n_fract_to, numbers.Number
                ):
                    # TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
                    self.my_dialog.dspbx_n_fract_to.setValue(
                        self.session_data.lr_geom_runtime.snap_n_fract_to * 100
                    )

                if SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_m_abs_to, numbers.Number
                    ):
                        self.my_dialog.dspbx_m_abs_to.setValue(
                            self.session_data.lr_geom_runtime.snap_m_abs_to
                        )
                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_m_fract_to,
                        numbers.Number,
                    ):
                        self.my_dialog.dspbx_m_fract_to.setValue(
                            self.session_data.lr_geom_runtime.snap_m_fract_to * 100
                        )

                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_m_abs_from,
                        numbers.Number,
                    ) and isinstance(
                        self.session_data.lr_geom_runtime.snap_m_abs_to, numbers.Number
                    ):
                        delta_m_abs = (
                            self.session_data.lr_geom_runtime.snap_m_abs_to
                            - self.session_data.lr_geom_runtime.snap_m_abs_from
                        )
                        self.my_dialog.dspbx_delta_m_abs.setValue(delta_m_abs)

                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_m_fract_from,
                        numbers.Number,
                    ) and isinstance(
                        self.session_data.lr_geom_runtime.snap_m_fract_to,
                        numbers.Number,
                    ):
                        delta_m_fract = (
                            self.session_data.lr_geom_runtime.snap_m_fract_to
                            - self.session_data.lr_geom_runtime.snap_m_fract_from
                        )
                        self.my_dialog.dspbx_delta_m_fract.setValue(delta_m_fract * 100)

                if SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs:
                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_z_abs_to, numbers.Number
                    ):
                        self.my_dialog.dnspbx_z_to.setValue(
                            self.session_data.lr_geom_runtime.snap_z_abs_to
                        )

                    if isinstance(
                        self.session_data.lr_geom_runtime.snap_z_abs_from,
                        numbers.Number,
                    ) and isinstance(
                        self.session_data.lr_geom_runtime.snap_z_abs_to, numbers.Number
                    ):
                        delta_z_abs = (
                            self.session_data.lr_geom_runtime.snap_z_abs_to
                            - self.session_data.lr_geom_runtime.snap_z_abs_from
                        )
                        self.my_dialog.dnspbx_delta_z_abs.setValue(delta_z_abs)

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_n_abs_from, numbers.Number
                ) and isinstance(
                    self.session_data.lr_geom_runtime.snap_n_abs_to, numbers.Number
                ):
                    delta_n_abs = (
                        self.session_data.lr_geom_runtime.snap_n_abs_to
                        - self.session_data.lr_geom_runtime.snap_n_abs_from
                    )
                    self.my_dialog.dspbx_delta_n_abs.setValue(delta_n_abs)

                if isinstance(
                    self.session_data.lr_geom_runtime.snap_n_fract_from, numbers.Number
                ) and isinstance(
                    self.session_data.lr_geom_runtime.snap_n_fract_to, numbers.Number
                ):
                    delta_n_fract = (
                        self.session_data.lr_geom_runtime.snap_n_fract_to
                        - self.session_data.lr_geom_runtime.snap_n_fract_from
                    )
                    self.my_dialog.dspbx_delta_n_fract.setValue(delta_n_fract * 100)

                # refresh dspbx_offset, independend from measurement, mostly identical to self.session_data.current_offset
                if isinstance(self.session_data.lr_geom_runtime.offset, numbers.Number):
                    self.my_dialog.dspbx_offset.setValue(
                        self.session_data.lr_geom_runtime.offset
                    )

                self.dlg_select_qcbn_reference_feature(
                    self.session_data.lr_geom_runtime.ref_fid
                )

                if (
                    SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
                    and self.session_data.edit_feature_fid
                ):
                    data_feature = self.tool_get_data_feature(
                        data_fid=self.session_data.edit_feature_fid
                    )
                    data_context = QgsExpressionContext()
                    data_display_exp = QgsExpression(
                        self.derived_settings.dataLyr.displayExpression()
                    )
                    data_display_exp.prepare(data_context)

                    data_context.setFeature(data_feature)
                    data_display_value = data_display_exp.evaluate(data_context)

                    self.qlbl_edit_data_feature.setText(f"'{data_display_value}'")
                    self.qlbl_edit_data_feature.setToolTip(
                        MY_DICT.tr(
                            "edit_data_fid_with_fid_ttp",
                            self.session_data.edit_feature_fid,
                            data_display_value,
                        )
                    )

                    self.qact_update_feature.setToolTip(
                        MY_DICT.tr(
                            "update_selected_feature_ttp",
                            self.session_data.edit_feature_fid,
                        )
                    )

                for widget in block_widgets:
                    widget.blockSignals(False)
