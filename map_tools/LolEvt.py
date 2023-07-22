#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* MapTool for digitizing Point-Events in MapCanvas

********************************************************************

* Date                 : 2023-03-01
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

import datetime
import math
import os
import osgeo
import qgis
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from LinearReferencing import tools, dialogs
from LinearReferencing.tools.MyDebugFunctions import debug_print
from LinearReferencing.tools.MyDebugFunctions import get_debug_pos as gdp
from LinearReferencing.tools.MyToolFunctions import qt_format


class LolEvt(qgis.gui.QgsMapToolEmitPoint):
    """MapTool for Digitize Line-on-Line-Events via reference-line and two measured distances from...to"""
    # Rev. 2023-04-21
    my_dialogue = None

    # IDs for identifying the layer-actions in dataLyr and showLyr, different to IDs for DigitzePointEvent
    _lyr_act_id_1 = QtCore.QUuid('11111111-abcd-4321-dcba-999999999999')
    _lyr_act_id_2 = QtCore.QUuid('11111111-DCBA-1234-abcd-999999999999')

    # settings self.ss can be stored for later restore, f.e. if the Pluigin is used for multiple LinearReference-Layers in the same project
    _num_storable_settings = 100

    # possible values for rs.tool_mode, key: rs.tool_mode, value: Explanation for status-bar

    class StoredSettings:
        """class-var, template for stored settings, self.ss, string-vars, stored in QGis-Project
        defined with property-getter-and-setter to register any user-setting-changes,
        which then set the QGis-Project "dirty" and have these changes stored on project-unload with save
        so every write-access to these properties, that should not set the "dirty"-Flag, must be did_it to the _internal-properties
        see f.e. restore_settings()
        """
        # Rev. 2023-04-27
        _refLyrId = None

        @property
        def refLyrId(self):
            """ID of Reference-Layer"""
            return self._refLyrId

        @refLyrId.setter
        def refLyrId(self, value):
            self._refLyrId = value
            qgis.core.QgsProject.instance().setDirty(True)

        _refLyrIdFieldName = None

        @property
        def refLyrIdFieldName(self):
            """Name of PK-Field in Reference-Layer"""
            return self._refLyrIdFieldName

        @refLyrIdFieldName.setter
        def refLyrIdFieldName(self, value):
            self._refLyrIdFieldName = value
            qgis.core.QgsProject.instance().setDirty(True)

        _dataLyrId = None

        @property
        def dataLyrId(self):
            """ID of Data-Layer"""
            return self._dataLyrId

        @dataLyrId.setter
        def dataLyrId(self, value):
            self._dataLyrId = value
            qgis.core.QgsProject.instance().setDirty(True)

        _dataLyrIdFieldName = None

        @property
        def dataLyrIdFieldName(self):
            """Name of PK-Field in Data-Layer"""
            return self._dataLyrIdFieldName

        @dataLyrIdFieldName.setter
        def dataLyrIdFieldName(self, value):
            self._dataLyrIdFieldName = value
            qgis.core.QgsProject.instance().setDirty(True)

        _dataLyrReferenceFieldName = None

        @property
        def dataLyrReferenceFieldName(self):
            """Name of Reference-Field in Data-Layer"""
            return self._dataLyrReferenceFieldName

        @dataLyrReferenceFieldName.setter
        def dataLyrReferenceFieldName(self, value):
            self._dataLyrReferenceFieldName = value
            qgis.core.QgsProject.instance().setDirty(True)

        _dataLyrMeasureFromFieldName = None

        @property
        def dataLyrMeasureFromFieldName(self):
            """Name of Measure-From-Field in Data-Layer"""
            return self._dataLyrMeasureFromFieldName

        @dataLyrMeasureFromFieldName.setter
        def dataLyrMeasureFromFieldName(self, value):
            self._dataLyrMeasureFromFieldName = value
            qgis.core.QgsProject.instance().setDirty(True)

        _dataLyrMeasureToFieldName = None

        @property
        def dataLyrMeasureToFieldName(self):
            """Name of Measure-Tp-Field in Data-Layer"""
            return self._dataLyrMeasureToFieldName

        @dataLyrMeasureToFieldName.setter
        def dataLyrMeasureToFieldName(self, value):
            self._dataLyrMeasureToFieldName = value
            qgis.core.QgsProject.instance().setDirty(True)

        _dataLyrOffsetFieldName = None

        @property
        def dataLyrOffsetFieldName(self):
            """Name of Measure-Tp-Field in Data-Layer"""
            return self._dataLyrOffsetFieldName

        @dataLyrOffsetFieldName.setter
        def dataLyrOffsetFieldName(self, value):
            self._dataLyrOffsetFieldName = value
            qgis.core.QgsProject.instance().setDirty(True)

        _showLyrId = None

        @property
        def showLyrId(self):
            """ID of Show-Layer"""
            return self._showLyrId

        @showLyrId.setter
        def showLyrId(self, value):
            self._showLyrId = value
            qgis.core.QgsProject.instance().setDirty(True)

        _showLyrBackReferenceFieldName = None

        @property
        def showLyrBackReferenceFieldName(self):
            """Name of Back-Reference-Field in Show-Layer for referencing Data-Layer"""
            return self._showLyrBackReferenceFieldName

        @showLyrBackReferenceFieldName.setter
        def showLyrBackReferenceFieldName(self, value):
            self._showLyrBackReferenceFieldName = value
            qgis.core.QgsProject.instance().setDirty(True)

        # Dot
        _ref_line_line_style = 3

        @property
        def ref_line_line_style(self):
            """Style of highlighted reference-line"""
            return int(self._ref_line_line_style)

        @ref_line_line_style.setter
        def ref_line_line_style(self, value):
            self._ref_line_line_style = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _ref_line_width = 3

        @property
        def ref_line_width(self):
            """Width of highlighted reference-line"""
            return int(self._ref_line_width)

        @ref_line_width.setter
        def ref_line_width(self, value):
            self._ref_line_width = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _ref_line_color = '#96ffffff'  # semi-transparent white

        @property
        def ref_line_color(self):
            """Width of highlighted reference-line"""
            return self._ref_line_color

        @ref_line_color.setter
        def ref_line_color(self, value):
            self._ref_line_color = value
            qgis.core.QgsProject.instance().setDirty(True)

        # see https://qgis.org/pyqgis/master/gui/QgsVertexMarker.html
        # self.point_symbol_items = {0: "None", 1: "Cross", 2: "X", 3: "Box", 4: "Circle", 5: "Double-Triangle", 6: "Triangle", 7: "Rhombus", 8: "Inverted Triangle"}
        # colors see https://doc.qt.io/qt-5/qcolor.html
        # Format with 4x2 Hex-Digits ➜ HexArgb
        _from_point_icon_type = 5

        @property
        def from_point_icon_type(self):
            """Icon-Type for From-Point-Canvas-Graphic"""
            return int(self._from_point_icon_type)

        @from_point_icon_type.setter
        def from_point_icon_type(self, value):
            self._from_point_icon_type = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _from_point_icon_size = 15

        @property
        def from_point_icon_size(self):
            """Size for From-Point-Canvas-Graphic"""
            return int(self._from_point_icon_size)

        @from_point_icon_size.setter
        def from_point_icon_size(self, value):
            self._from_point_icon_size = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _from_point_pen_width = 2

        @property
        def from_point_pen_width(self):
            """Pen-Width for From-Point-Canvas-Graphic"""
            return int(self._from_point_pen_width)

        @from_point_pen_width.setter
        def from_point_pen_width(self, value):
            self._from_point_pen_width = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _from_point_color = '#ff54b04a'  # dark green

        @property
        def from_point_color(self):
            """Color for From-Point-Canvas-Graphic"""
            return self._from_point_color

        @from_point_color.setter
        def from_point_color(self, value):
            self._from_point_color = value
            qgis.core.QgsProject.instance().setDirty(True)

        _from_point_fill_color = '#00ffffff'  # white transparent

        @property
        def from_point_fill_color(self):
            """Fill-Color for From-Point-Canvas-Graphic"""
            return self._from_point_fill_color

        @from_point_fill_color.setter
        def from_point_fill_color(self, value):
            self._from_point_fill_color = value
            qgis.core.QgsProject.instance().setDirty(True)

        _to_point_icon_type = 5

        @property
        def to_point_icon_type(self):
            """Icon-Type for to-Point-Canvas-Graphic"""
            return int(self._to_point_icon_type)

        @to_point_icon_type.setter
        def to_point_icon_type(self, value):
            self._to_point_icon_type = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _to_point_icon_size = 15

        @property
        def to_point_icon_size(self):
            """Size for to-Point-Canvas-Graphic"""
            return int(self._to_point_icon_size)

        @to_point_icon_size.setter
        def to_point_icon_size(self, value):
            self._to_point_icon_size = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _to_point_pen_width = 2

        @property
        def to_point_pen_width(self):
            """Pen-Width for to-Point-Canvas-Graphic"""
            return int(self._to_point_pen_width)

        @to_point_pen_width.setter
        def to_point_pen_width(self, value):
            self._to_point_pen_width = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _to_point_color = '#ffdb1e2a'  # dark red

        @property
        def to_point_color(self):
            """Color for to-Point-Canvas-Graphic"""
            return self._to_point_color

        @to_point_color.setter
        def to_point_color(self, value):
            self._to_point_color = value
            qgis.core.QgsProject.instance().setDirty(True)

        _to_point_fill_color = '#00ffffff'  # white transparent

        @property
        def to_point_fill_color(self):
            """Fill-Color for to-Point-Canvas-Graphic"""
            return self._to_point_fill_color

        @to_point_fill_color.setter
        def to_point_fill_color(self, value):
            self._to_point_fill_color = value
            qgis.core.QgsProject.instance().setDirty(True)

        # self.line_symbol_items = {0: "None", 1: "Solid", 2: "Dash", 3: "Dot", 4: "DashDot", 5: "DashDotDot"}
        _segment_line_line_style = 1

        @property
        def segment_line_line_style(self):
            """Style of Line-Segment"""
            return int(self._segment_line_line_style)

        @segment_line_line_style.setter
        def segment_line_line_style(self, value):
            self._segment_line_line_style = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _segment_line_width = 10

        @property
        def segment_line_width(self):
            """Width of Line-Segment"""
            return int(self._segment_line_width)

        @segment_line_width.setter
        def segment_line_width(self, value):
            self._segment_line_width = int(value)
            qgis.core.QgsProject.instance().setDirty(True)

        _segment_line_color = '#ff00ffff'  # cyan

        @property
        def segment_line_color(self):
            """Width of Line-Segment"""
            return self._segment_line_color

        @segment_line_color.setter
        def segment_line_color(self, value):
            self._segment_line_color = value
            qgis.core.QgsProject.instance().setDirty(True)

    class DeferedSettings:
        """empty template for self.ds ➜ defered settings ➜ Qt/QGis-Objects (layers, fields)"""
        # Rev. 2023-05-07
        # basic settings, keys from self.StoredSettings, values restored from project via qgis.core.QgsProject.instance().readEntry(...)
        refLyr = None
        refLyrPkField = None
        dataLyr = None

        dataLyrIdField = None
        dataLyrReferenceField = None
        dataLyrMeasureFromField = None
        dataLyrMeasureToField = None
        dataLyrOffsetField = None

        showLyr = None
        showLyrBackReferenceField = None

    class CheckFlags:
        """"template for self.cf, often needed group-flags, set to False/True in self.check_settings if settings/capabilities/interim results are sufficient"""
        # Rev. 2023-05-08
        reference_layer_defined = False
        reference_layer_complete = False
        data_layer_defined = False
        data_layer_complete = False
        show_layer_defined = False
        show_layer_complete = False
        measure_completed = False
        insert_enabled = False
        update_enabled = False
        delete_enabled = False

    class RuntimeSettings:
        """template for self.rs, runtime-settings"""
        # Rev. 2023-05-08
        # one of the possible toolmodes, see self::tool_modes
        tool_mode = None

        # int (allways): fid of the current snapped reference-line
        snapped_ref_fid = None

        # str|int: fid/pk (mostly identical) of the current edited Feature in Data-Layer
        edit_pk = None

        # flt: current measure-result, distance of the snapped points to the start-point of the snapped reference-line
        current_measure_from = None

        # flt: current measure-result, distance of the snapped points to the start-point of the snapped reference-line
        current_measure_to = None

        # flt: current offset, set via DoubleSpinBox in Dialogue, default 0
        current_offset = 0

        # flt: measure for interacive move of the current segment
        last_measure = 0

        # PointXY, set via canvasPressEvent
        mouse_down_point = None

        # PointXY, set via canvasReleaseEvent
        mouse_up_point = None

        # list of pre-selected Data-Layer-PKs for edit
        selected_pks = []

        #  for display of coordinates and measurements, dependend on canvas-projection
        num_digits = 1

        # register all signal-slot-connections to the three layer for later accurate disconnects
        data_layer_connections = []
        reference_layer_connections = []
        show_layer_connections = []

    def __init__(self, iface: qgis.gui.QgisInterface):
        """initialize
        :param iface: qgis.gui.QgisInterface "Abstract base class defining interfaces exposed by QgisApp and made available to plugins."
        """
        # Rev. 2023-05-08
        qgis.gui.QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())

        self.iface = iface
        """qgis.gui.QgisInterface: Access to QGis-Qt-Application"""

        self.tool_modes = {
            'init': QtCore.QCoreApplication.translate('LolEvt', "Initializing, please wait..."),

            'before_measure': QtCore.QCoreApplication.translate('LolEvt', "hover on Reference-Layer-feature to show coords, click+move+release to take measurement..."),
            'measuring': QtCore.QCoreApplication.translate('LolEvt', "Reference-feature selected and from-point measured; move to desired to-point and release to take measurement..."),
            'after_measure': QtCore.QCoreApplication.translate('LolEvt', "Measurement taken, edit results/insert feature or resume..."),

            'before_move_from_point': QtCore.QCoreApplication.translate('LolEvt', "drag and drop from-point on selected reference-line..."),
            'move_from_point': QtCore.QCoreApplication.translate('LolEvt', "drop from-point at the desired position of the selected line..."),

            'before_move_to_point': QtCore.QCoreApplication.translate('LolEvt', "drag and drop to-point on selected reference-line..."),
            'move_to_point': QtCore.QCoreApplication.translate('LolEvt', "drop to-point at the desired position of the selected line..."),

            'before_move_segment': QtCore.QCoreApplication.translate('LolEvt', "drag and drop segment, supports [ctrl] or [shift] modifiers..."),
            'move_segment': QtCore.QCoreApplication.translate('LolEvt', "drop segment, supports [ctrl] or [shift] modifiers..."),

            'disabled': QtCore.QCoreApplication.translate('LolEvt', "no Reference-Layer (linestring) found or configured, check settings..."),

            'select_features': QtCore.QCoreApplication.translate('LolEvt', "click or draw rect to select features for edit"),

        }

        # initialize the settings-"containers" with blank "templates"
        self.ss = self.StoredSettings()
        self.ds = self.DeferedSettings()
        self.cf = self.CheckFlags()
        self.rs = self.RuntimeSettings()
        self.restore_settings()

        # the order added to canvas determines the drawing-order, latter ones appear on-top
        self.rb_ref = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)
        """qgis.gui.QgsRubberBand: visualize snapped reference-line"""
        self.rb_ref.hide()

        self.rb_segment = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)
        """qgis.gui.QgsRubberBand: visualize line-segment"""
        self.rb_segment.hide()

        self.vm_pt_measure_from = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())
        """qgis.gui.QgsVertexMarker: visualize snapped start-point on reference-line"""
        self.vm_pt_measure_from.hide()

        self.vm_pt_measure_to = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())
        """qgis.gui.QgsVertexMarker: visualize snapped end-point on reference-line"""
        self.vm_pt_measure_to.hide()

        self.rb_selection_rect = qgis.gui.QgsRubberBand(self.iface.mapCanvas())
        """qgis.gui.QgsRubberBand: selection-rectangle for the point-on-line-Features"""
        self.rb_selection_rect.hide()

        self.refresh_canvas_graphics()

        self.snap_indicator = qgis.gui.QgsSnapIndicator(self.iface.mapCanvas())
        """qgis.gui.QgsSnapIndicator: the tiny snap-icon"""

        self.my_dialogue = dialogs.LolDialog(iface)

        # connect Qt-Widget-Signals in dialogue to Slots
        # Measure-Area
        self.my_dialogue.measure_grb.toggled.connect(self.s_measure_grb_toggle)
        self.my_dialogue.qcbn_snapped_ref_fid.currentIndexChanged.connect(self.s_zoom_to_ref_feature)
        self.my_dialogue.pb_open_ref_form.clicked.connect(self.s_open_ref_form)
        self.my_dialogue.pb_zoom_to_ref_feature.clicked.connect(self.s_zoom_to_ref_feature)
        self.my_dialogue.dspbx_offset.valueChanged.connect(self.s_change_offset)
        self.my_dialogue.dspbx_measure_from.valueChanged.connect(self.s_change_measure_from)
        self.my_dialogue.dspbx_measure_fract_from.valueChanged.connect(self.s_change_measure_fract_from)
        self.my_dialogue.dspbx_measure_to.valueChanged.connect(self.s_change_measure_to)
        self.my_dialogue.dspbx_measure_fract_to.valueChanged.connect(self.s_change_measure_fract_to)

        self.my_dialogue.tbtn_move_segment_start.clicked.connect(self.s_move_segment_start)
        self.my_dialogue.tbtn_prepend_segment.clicked.connect(self.s_prepend_segment)
        self.my_dialogue.tbtn_move_segment_down.clicked.connect(self.s_move_segment_down)
        self.my_dialogue.dspbx_distance.valueChanged.connect(self.s_change_distance)
        self.my_dialogue.tbtn_move_segment_up.clicked.connect(self.s_move_segment_up)
        self.my_dialogue.tbtn_append_segment.clicked.connect(self.s_append_segment)
        self.my_dialogue.tbtn_move_segment_end.clicked.connect(self.s_move_segment_end)
        self.my_dialogue.pb_zoom_to_segment.clicked.connect(self.s_zoom_to_segment)

        self.my_dialogue.pbtn_move_from_point.clicked.connect(self.s_move_from_point)
        self.my_dialogue.pbtn_move_to_point.clicked.connect(self.s_move_to_point)
        self.my_dialogue.pb_move_segment.clicked.connect(self.s_move_segment)
        self.my_dialogue.pbtn_resume_measure.clicked.connect(self.s_resume_measure)

        # edit-Section:
        self.my_dialogue.edit_grb.toggled.connect(self.s_edit_grb_toggle)
        self.my_dialogue.pbtn_update_feature.clicked.connect(self.s_update_feature)
        self.my_dialogue.pbtn_insert_feature.clicked.connect(self.s_insert_feature)
        self.my_dialogue.pbtn_delete_feature.clicked.connect(self.s_delete_feature)

        # feature-selection-Section
        self.my_dialogue.selection_grb.toggled.connect(self.s_selection_grb_toggle)
        self.my_dialogue.pbtn_select_features.clicked.connect(self.s_select_features)
        self.my_dialogue.pbtn_clear_features.clicked.connect(self.s_clear_feature_selection)
        self.my_dialogue.pbtn_insert_all_features.clicked.connect(self.s_append_all_features)
        self.my_dialogue.pbtn_insert_selected_data_features.clicked.connect(self.s_append_data_features)
        self.my_dialogue.pbtn_insert_selected_show_features.clicked.connect(self.s_append_show_features)
        self.my_dialogue.pbtn_zoom_to_feature_selection.clicked.connect(self.s_zoom_to_feature_selection)

        self.my_dialogue.qcbn_reference_layer.currentIndexChanged.connect(self.s_change_reference_layer)
        self.my_dialogue.qcbn_reference_layer_id_field.currentIndexChanged.connect(self.s_change_reference_layer_id_field)

        self.my_dialogue.pbtn_create_data_layer.clicked.connect(self.s_create_data_layer)
        self.my_dialogue.pbtn_create_show_layer.clicked.connect(self.s_create_show_layer)
        self.my_dialogue.pb_open_ref_tbl.clicked.connect(self.open_ref_tbl)
        self.my_dialogue.pb_call_ref_disp_exp_dlg.clicked.connect(self.s_define_ref_lyr_display_expression)
        self.my_dialogue.pb_open_data_tbl.clicked.connect(self.open_data_tbl)
        self.my_dialogue.pb_call_data_disp_exp_dlg.clicked.connect(self.s_define_data_lyr_display_expression)
        self.my_dialogue.pb_open_show_tbl.clicked.connect(self.s_open_show_lyr_tbl)
        self.my_dialogue.pb_call_show_disp_exp_dlg.clicked.connect(self.s_define_show_lyr_display_expression)

        self.my_dialogue.qcbn_data_layer.currentIndexChanged.connect(self.s_change_data_layer)
        self.my_dialogue.qcbn_data_layer_id_field.currentIndexChanged.connect(self.s_change_data_layer_id_field)
        self.my_dialogue.qcbn_data_layer_reference_field.currentIndexChanged.connect(self.s_change_data_layer_reference_field)
        self.my_dialogue.qcbn_data_layer_measure_from_field.currentIndexChanged.connect(self.s_change_data_layer_measure_from_field)
        self.my_dialogue.qcbn_data_layer_measure_to_field.currentIndexChanged.connect(self.s_change_data_layer_measure_to_field)
        self.my_dialogue.qcbn_data_layer_offset_field.currentIndexChanged.connect(self.s_change_data_layer_offset_field)
        self.my_dialogue.qcbn_show_layer.currentIndexChanged.connect(self.s_change_show_lyr)
        self.my_dialogue.qcbn_show_layer_back_reference_field.currentIndexChanged.connect(self.s_change_show_lyr_back_ref)

        # from_point
        self.my_dialogue.qcb_from_point_icon_type.currentIndexChanged.connect(self.s_change_from_point_icon_type)
        self.my_dialogue.qspb_from_point_icon_size.valueChanged.connect(self.s_change_from_point_icon_size)
        self.my_dialogue.qspb_from_point_pen_width.valueChanged.connect(self.s_change_from_point_pen_width)
        self.my_dialogue.qpb_from_point_color.color_changed.connect(self.s_change_from_point_color)
        self.my_dialogue.qpb_from_point_fill_color.color_changed.connect(self.s_change_from_point_fill_color)

        # to_point
        self.my_dialogue.qcb_to_point_icon_type.currentIndexChanged.connect(self.s_change_to_point_icon_type)
        self.my_dialogue.qspb_to_point_icon_size.valueChanged.connect(self.s_change_to_point_icon_size)
        self.my_dialogue.qspb_to_point_pen_width.valueChanged.connect(self.s_change_to_point_pen_width)
        self.my_dialogue.qpb_to_point_color.color_changed.connect(self.s_change_to_point_color)
        self.my_dialogue.qpb_to_point_fill_color.color_changed.connect(self.s_change_to_point_fill_color)

        # segment_line
        self.my_dialogue.qpb_segment_line_color.color_changed.connect(self.s_change_segment_line_color)
        self.my_dialogue.qcb_segment_line_line_style.currentIndexChanged.connect(self.s_change_segment_line_line_style)
        self.my_dialogue.qspb_segment_line_width.valueChanged.connect(self.s_change_segment_line_width)

        # ref_line
        self.my_dialogue.qpb_ref_line_color.color_changed.connect(self.s_change_ref_line_color)
        self.my_dialogue.qcb_ref_line_line_style.currentIndexChanged.connect(self.s_change_ref_line_line_style)
        self.my_dialogue.qspb_ref_line_width.valueChanged.connect(self.s_change_ref_line_width)

        self.my_dialogue.dialog_close.connect(self.s_dialog_close)

        self.my_dialogue.layers_and_fields_grb.toggled.connect(self.s_layers_and_fields_grb_toggle)
        self.my_dialogue.style_grb.toggled.connect(self.s_style_grb_toggle)

        self.my_dialogue.store_configurations_gb.toggled.connect(self.s_store_configurations_gb_toggle)
        self.my_dialogue.pb_store_configuration.clicked.connect(self.s_store_configuration)
        self.my_dialogue.pb_delete_configuration.clicked.connect(self.delete_configuration)
        self.my_dialogue.pb_restore_configuration.clicked.connect(self.s_restore_configuration)
        self.my_dialogue.lw_stored_settings.itemDoubleClicked.connect(self.s_restore_configuration)

        self.check_settings()

        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.my_dialogue)
        self.my_dialogue.setFloating(True)
        start_pos_x = int(self.iface.mainWindow().x() + 0.20 * self.iface.mainWindow().width())
        start_pos_y = int(self.iface.mainWindow().y() + 0.20 * self.iface.mainWindow().height())
        self.my_dialogue.setGeometry(start_pos_x, start_pos_y, 740, 520)

    def s_restore_configuration(self):
        """restores stored configuration from project-file
        takes the selected Item from QListWidget
        uses its label, which serves as client-side unique identifier,
        in qgis-project-file the storage is under XML-Path LinearReferencing/LolEvtStoredSettings/setting_{setting_idx} with setting_idx in range 0...9
        """
        # Rev. 2023-05-08

        try_it = True
        did_it = False
        success_msg = ''
        critical_msg = ''
        info_msg = ''
        warning_msg = ''

        row_idx = self.my_dialogue.lw_stored_settings.currentRow()
        if row_idx < 0:
            try_it = False
            critical_msg = QtCore.QCoreApplication.translate('LolEvt', "please select an entry from the list above...")
        else:
            selected_item = self.my_dialogue.lw_stored_settings.item(row_idx)

            selected_label = selected_item.data(256)
            for setting_idx in range(self._num_storable_settings):
                key = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                setting_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', key)
                if setting_label and type_conversion_ok:
                    if setting_label == selected_label:
                        self.ss = self.StoredSettings()
                        self.ds = self.StoredSettings()
                        property_list = [prop for prop in dir(self.StoredSettings) if prop.startswith('_') and not prop.startswith('__')]

                        for prop_name in property_list:
                            key = f"/LolEvtStoredSettings/setting_{setting_idx}/{prop_name}"
                            restored_value, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', key)
                            if restored_value and type_conversion_ok:
                                setattr(self.ss, prop_name, restored_value)
                        did_it = True
                        success_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Configuration {apos}{0}{apos} restored..."), setting_label)
                        break

        if try_it and did_it:
            self.refresh_gui()

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def delete_configuration(self):
        """deletes stored configuration from project-file
        takes the selected Item from QListWidget
        uses its label, which serves as client-side unique identifier,
        in qgis-project-file the storage is under XML-Path LinearReferencing/LolEvtStoredSettings/setting_{setting_idx} with setting_idx in range 0...9
        asks for confirmation
        """
        # Rev. 2023-05-08

        critical_msg = ''
        success_msg = ''
        info_msg = ''
        warning_msg = ''

        row_idx = self.my_dialogue.lw_stored_settings.currentRow()
        if row_idx < 0:
            warning_msg = QtCore.QCoreApplication.translate('LolEvt', "please select an entry from the list above...")
        else:
            selected_item = self.my_dialogue.lw_stored_settings.item(row_idx)

            selected_label = selected_item.data(256)
            for setting_idx in range(self._num_storable_settings):
                # uses the label as unique identifier, although no "unique contraint" with this value possible in XML-Structure of project-file
                key = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                setting_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', key)
                if setting_label and type_conversion_ok:
                    if setting_label == selected_label:
                        dialog_result = QtWidgets.QMessageBox.question(
                            None,
                            f"LinearReferencing ({gdp()})",
                            qt_format(QtCore.QCoreApplication.translate('LolEvt', "Delete configuration {apos}{0}{apos}?"), setting_label),
                            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                            defaultButton=QtWidgets.QMessageBox.Yes
                        )

                        if dialog_result == QtWidgets.QMessageBox.Yes:
                            del_key = f"/LolEvtStoredSettings/setting_{setting_idx}"
                            qgis.core.QgsProject.instance().removeEntry('LinearReferencing', del_key)
                            self.dlg_refresh_stored_settings_section()
                            success_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Configuration {apos}{0}{apos} deleted..."), setting_label)
                        else:
                            info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def s_store_configuration(self):
        """stores the current configuration in project-file
        prompts user to enter a label, which serves as client-side unique identifier,
        in qgis-project-file the storage is under XML-Path LinearReferencing/LolEvtStoredSettings/setting_{setting_idx} with setting_idx in range 0...9
        asks for confirmation, if the label already exists"""
        # Rev. 2023-05-08
        try_it = True
        critical_msg = ''
        success_msg = ''
        info_msg = ''
        warning_msg = ''
        row_idx = self.my_dialogue.lw_stored_settings.currentRow()
        if row_idx < 0:
            default_label = datetime.date.today().strftime('%Y-%m-%d')
        else:
            # convenience:  take selected ListItem for overwrite
            selected_item = self.my_dialogue.lw_stored_settings.item(row_idx)
            default_label = selected_item.data(256)

        new_label, ok = QtWidgets.QInputDialog.getText(None, f"LinearReferencing ({gdp()})", QtCore.QCoreApplication.translate('LolEvt', "Label for configuration:"), QtWidgets.QLineEdit.Normal, default_label)
        if not ok or not new_label:
            info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")
        else:
            new_idx = None
            not_used_idx = []
            for setting_idx in range(self._num_storable_settings):
                key = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                old_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', key)

                if old_label and type_conversion_ok:
                    if old_label == new_label:
                        dialog_result = QtWidgets.QMessageBox.question(
                            None,
                            f"LinearReferencing ({gdp()})",
                            qt_format(QtCore.QCoreApplication.translate('LolEvt', "Replace stored configuration {apos}{0}{apos}?"), new_label),
                            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                            defaultButton=QtWidgets.QMessageBox.Yes
                        )

                        if dialog_result == QtWidgets.QMessageBox.Yes:
                            try_it = True
                            new_idx = setting_idx
                        else:
                            try_it = False
                            info_msg = QtCore.QCoreApplication.translate('LolEvt', 'Canceled by user...')
                else:
                    not_used_idx.append(setting_idx)

            # no stored settings with label == new_label found
            if new_idx == None:
                if not_used_idx:
                    # take the first possible un-used one
                    new_idx = not_used_idx.pop(0)
                else:
                    # or no store, if already _num_storable_settings configurations have been stored
                    try_it = False
                    critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "number of stored settings exceeds maximum ({0})..."), self._num_storable_settings)

            if try_it:
                property_dict = {prop: getattr(self.ss, prop) for prop in dir(self.StoredSettings) if prop.startswith('_') and not prop.startswith('__')}

                for prop_name in property_dict:
                    prop_value = property_dict[prop_name]
                    # other key then PolEvt
                    key = f"/LolEvtStoredSettings/setting_{new_idx}/{prop_name}"
                    qgis.core.QgsProject.instance().writeEntry('LinearReferencing', key, prop_value)

                key = f"/LolEvtStoredSettings/setting_{new_idx}/setting_label"
                qgis.core.QgsProject.instance().writeEntry('LinearReferencing', key, new_label)

                self.dlg_refresh_stored_settings_section()
                success_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Current configuration stored under {apos}{0}{apos}..."), new_label)

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def s_store_configurations_gb_toggle(self, status):
        """Toggle Group-Box in Dialog
        :param status: isChecked()-State
        """
        # Rev. 2023-05-07
        if status:
            self.my_dialogue.store_configurations_gb.setMaximumHeight(16777215)
        else:
            self.my_dialogue.store_configurations_gb.setMaximumHeight(20)

    def s_style_grb_toggle(self, status):
        """Toggle Group-Box in Dialog
        :param status: isChecked()-State
        """
        # Rev. 2023-05-03
        if status:
            self.my_dialogue.style_grb.setMaximumHeight(16777215)
        else:
            self.my_dialogue.style_grb.setMaximumHeight(20)

    def s_layers_and_fields_grb_toggle(self, status):
        """Toggle Group-Box in Dialog
        :param status: isChecked()-State
        """
        # Rev. 2023-05-03
        if status:
            self.my_dialogue.layers_and_fields_grb.setMaximumHeight(16777215)
        else:
            self.my_dialogue.layers_and_fields_grb.setMaximumHeight(20)

    def s_selection_grb_toggle(self, status):
        """Toggle Group-Box in Dialog
        :param status: isChecked()-State
        """
        # Rev. 2023-05-03
        if status:
            # no vertical limit
            self.my_dialogue.selection_grb.setMaximumHeight(16777215)
        else:
            self.my_dialogue.selection_grb.setMaximumHeight(20)

    def s_measure_grb_toggle(self, status):
        """Toggle Group-Box in Dialog
        :param status: isChecked()-State
        """
        # Rev. 2023-05-03
        if status:
            self.my_dialogue.measure_grb.setMaximumHeight(16777215)
        else:
            self.my_dialogue.measure_grb.setMaximumHeight(20)

    def s_edit_grb_toggle(self, status):
        """Toggle Group-Box in Dialog
        :param status: isChecked()-State
        """
        # Rev. 2023-05-03
        if status:
            self.my_dialogue.edit_grb.setMaximumHeight(16777215)
        else:
            self.my_dialogue.edit_grb.setMaximumHeight(20)

    def s_change_ref_line_color(self, color: str):
        """change color in tools.MyQtWidgets.QPushButtonColor-dialog
        :color color: currentColor from QColorDialog in HexArgb-Format
        """
        # Rev. 2023-05-08
        self.ss.ref_line_color = color
        self.refresh_canvas_graphics()

    def s_change_ref_line_width(self, line_width: int):
        """change line-width
        :param line_width:
        """
        # Rev. 2023-05-08
        self.ss.ref_line_width = line_width
        self.refresh_canvas_graphics()

    def s_change_ref_line_line_style(self):
        """change line-style"""
        self.ss.ref_line_line_style = self.my_dialogue.qcb_ref_line_line_style.currentData()
        self.refresh_canvas_graphics()

    def s_change_segment_line_width(self, line_width: int):
        """change line-width
        :param line_width:
        """
        # Rev. 2023-05-08
        self.ss.segment_line_width = line_width
        self.refresh_canvas_graphics()

    def s_change_segment_line_line_style(self):
        """change line-style"""
        # Rev. 2023-05-08
        self.ss.segment_line_line_style = self.my_dialogue.qcb_segment_line_line_style.currentData()
        self.refresh_canvas_graphics()

    def s_change_segment_line_color(self, color: str):
        """change color in tools.MyQtWidgets.QPushButtonColor-dialog
        :color color: currentColor from QColorDialog in HexArgb-Format
        """
        # Rev. 2023-05-08
        self.ss.segment_line_color = color
        self.refresh_canvas_graphics()

    def s_change_to_point_pen_width(self, pen_width: int):
        """change pen-width
        :param pen_width:
        """
        # Rev. 2023-05-08
        self.ss.to_point_pen_width = pen_width
        self.refresh_canvas_graphics()

    def s_change_to_point_icon_size(self, icon_size: int):
        """change icon-size
        :param icon_size:
        """
        # Rev. 2023-05-08
        self.ss.to_point_icon_size = icon_size
        self.refresh_canvas_graphics()

    def s_change_to_point_icon_type(self):
        """change icon-type"""
        # Rev. 2023-05-08
        self.ss.to_point_icon_type = self.my_dialogue.qcb_to_point_icon_type.currentData()
        self.refresh_canvas_graphics()

    def s_change_to_point_color(self, color: str):
        """change color in tools.MyQtWidgets.QPushButtonColor-dialog
        :color color: currentColor from QColorDialog in HexArgb-Format
        """
        # Rev. 2023-05-08
        self.ss.to_point_color = color
        self.refresh_canvas_graphics()

    def s_change_to_point_fill_color(self, color: str):
        """change color in tools.MyQtWidgets.QPushButtonColor-dialog
        :color color: currentColor from QColorDialog in HexArgb-Format
        """
        # Rev. 2023-05-08
        self.ss.to_point_fill_color = color
        self.refresh_canvas_graphics()

    def s_change_from_point_pen_width(self, pen_width: int):
        """change pen-width
        :param pen_width:
        """
        # Rev. 2023-05-08
        self.ss.from_point_pen_width = pen_width
        self.refresh_canvas_graphics()

    def s_change_from_point_icon_size(self, icon_size: int):
        """change icon-size
        :param icon_size:
        """
        # Rev. 2023-05-08
        self.ss.from_point_icon_size = icon_size
        self.refresh_canvas_graphics()

    def s_change_from_point_icon_type(self):
        """change icon-type"""
        # Rev. 2023-05-08
        self.ss.from_point_icon_type = self.my_dialogue.qcb_from_point_icon_type.currentData()
        self.refresh_canvas_graphics()

    def s_change_from_point_color(self, color: str):
        """change color in tools.MyQtWidgets.QPushButtonColor-dialog
        :color color: currentColor from QColorDialog in HexArgb-Format
        """
        # Rev. 2023-05-08
        self.ss.from_point_color = color
        self.refresh_canvas_graphics()

    def s_change_from_point_fill_color(self, color: str):
        """change color in tools.MyQtWidgets.QPushButtonColor-dialog
        :color color: currentColor from QColorDialog in HexArgb-Format
        """
        # Rev. 2023-05-08
        self.ss.from_point_fill_color = color
        self.refresh_canvas_graphics()

    def s_dialog_close(self):
        """slot for signal dialog_close, emitted on self.my_dialogue closeEvent
        switch MapTool and garbage-collection"""
        # Rev. 2023-05-08
        try:
            self.vm_pt_measure_from.hide()
            self.vm_pt_measure_to.hide()
            self.rb_ref.hide()
            self.rb_selection_rect.hide()
            self.rb_segment.hide()
            self.iface.actionPan().trigger()
        except Exception as e:
            # if called on unload and these Markers are already deleted
            # print(f"Expected exception in {gdp()}: \"{e}\"")
            pass

    def check_data_feature(self,check_pk,push_message:bool = True)->bool:
        """check Data-feature: detect Null-Values
        :param check_pk: PK of data-feature
        :param push_message: false => silent mode, no message
        """
        warning_msg = ''
        feature_ok = True
        if self.cf.data_layer_complete and self.cf.reference_layer_complete:
            data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, check_pk)
            if data_feature and data_feature.isValid():
                ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, data_feature[self.ds.dataLyrReferenceField.name()])
                if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                    measure_from = data_feature[self.ds.dataLyrMeasureFromField.name()]
                    measure_to = data_feature[self.ds.dataLyrMeasureToField.name()]
                    offset = data_feature[self.ds.dataLyrOffsetField.name()]

                    if measure_from == '' or measure_from is None or repr(measure_from) == 'NULL':
                        feature_ok = False
                        warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "data-feature with PK {apos}{0}{apos} is invalid: null-value in measure-from-field {apos}{1}.{2}{apos}"), check_pk, self.ds.dataLyr.name(), self.ds.dataLyrMeasureFromField.name())
                    elif measure_to == '' or measure_to is None or repr(measure_to) == 'NULL':
                        feature_ok = False
                        warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "data-feature with PK {apos}{0}{apos} is invalid: null-value in measure-to-field {apos}{1}.{2}{apos}"), check_pk, self.ds.dataLyr.name(), self.ds.dataLyrMeasureToField.name())
                    elif offset == '' or offset is None or repr(offset) == 'NULL':
                        feature_ok = False
                        warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "data-feature with PK {apos}{0}{apos} is invalid: null-value in offset-field {apos}{1}.{2}{apos}"), check_pk, self.ds.dataLyr.name(), self.ds.dataLyrOffsetField.name())
                else:
                    feature_ok = False
                    warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "data-feature with PK {apos}{0}{apos} is invalid: no Reference-feature with ID {apos}{1}{apos} in layer {apos}{2}{apos}"), check_pk, data_feature[self.ds.dataLyrReferenceField.name()], self.ds.refLyr.name())
            else:
                feature_ok = False
                warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "no data-feature with PK {apos}{0}{apos} in layer {apos}{1}{apos}"), check_pk, self.ds.dataLyr.name())
        else:
            feature_ok = False
            warning_msg = QtCore.QCoreApplication.translate('LolEvt', "Missing requirements, Reference- and Data-Layer required, check Line-on-Line-settings...")
            self.my_dialogue.tbw_central.setCurrentIndex(1)

        if warning_msg is not None and push_message:
            self.push_messages(warning_msg=warning_msg)

        return feature_ok

    def set_edit_pk(self, edit_pk, zoom_to_feature: bool = True):
        """set the editable feature,
        called from QTableWidget, from canvasReleaseEvent and from Attribute table/Form-action (see MyFeatureActionFunctions.edit_line_on_line_feature)

        :param edit_pk: PK-value of Show-Layer
        :param zoom_to_feature: True ➜ zoom canvas to segment_geom False ➜ just select and highlight see LolEvt.set_edit_pk()
        """
        # Rev. 2023-05-08

        if self.check_data_feature(edit_pk):

            data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
            ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, data_feature[self.ds.dataLyrReferenceField.name()])
            measure_from = data_feature[self.ds.dataLyrMeasureFromField.name()]
            measure_to = data_feature[self.ds.dataLyrMeasureToField.name()]
            offset = data_feature[self.ds.dataLyrOffsetField.name()]

            self.rs.edit_pk = edit_pk
            self.my_dialogue.le_edit_data_pk.setText(str(edit_pk))

            self.ds.dataLyr.removeSelection()
            self.ds.dataLyr.select(data_feature.id())

            self.my_dialogue.tbw_central.setCurrentIndex(0)
            # triggers s_edit_grb_toggle()
            self.my_dialogue.edit_grb.setChecked(1)

            self.rs.current_measure_from = measure_from
            self.rs.current_measure_to = measure_to
            self.rs.current_offset = offset
            # no duplicates
            if not edit_pk in self.rs.selected_pks:
                self.rs.selected_pks.append(edit_pk)

            self.rs.snapped_ref_fid = ref_feature.id()

            if zoom_to_feature:
                self.zoom_to_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)

            self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
            self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
            self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
            self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
            self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
            self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)
            self.dlg_refresh_offset(self.rs.current_offset)

            self.ds.dataLyr.removeSelection()
            self.ds.dataLyr.select(data_feature.id())
            if self.cf.show_layer_complete:
                show_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.showLyr, self.ds.showLyrBackReferenceField, edit_pk)
                if show_feature and show_feature.isValid():
                    self.ds.showLyr.removeSelection()
                    self.ds.showLyr.select(show_feature.id())

            self.check_settings()
            self.dlg_refresh_measure_section()
            self.dlg_refresh_edit_section()
            self.dlg_refresh_feature_selection_section()

    def s_select_features(self, checked: bool):
        """toggles tool-mode for selecting features from showLyr
        :param checked: status of self.my_dialogue.pbtn_select_features
        """
        # Rev. 2023-05-08
        self.rb_ref.hide()
        self.rb_segment.hide()
        self.vm_pt_measure_from.hide()
        self.vm_pt_measure_to.hide()
        tool_mode = None
        if self.cf.reference_layer_complete and self.cf.data_layer_complete and self.cf.show_layer_complete:
            self.ds.showLyr.removeSelection()
            if checked or type(self.iface.mapCanvas().mapTool()) != LolEvt:
                tool_mode = 'select_features'
            else:
                tool_mode = 'before_measure'

        elif self.cf.reference_layer_defined:
            tool_mode = 'before_measure'

        self.check_settings(tool_mode)
        self.dlg_refresh_feature_selection_section()

    def s_clear_feature_selection(self):
        """remove selected point-features from QTableWidget"""
        # Rev. 2023-05-08
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_edit_section()

    def s_append_all_features(self):
        """Adds all Features to self.rs.selected_pks"""
        # Rev. 2023-05-03
        if self.cf.reference_layer_complete and self.cf.data_layer_complete:
            self.rs.selected_pks = qgis.core.QgsVectorLayerUtils.getValues(self.ds.dataLyr, self.ds.dataLyrIdField.name(), selectedOnly=False)[0]
            self.check_settings()
            self.dlg_refresh_feature_selection_section()
        else:
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "Missing requirements, Reference- and Data-Layer required, check Line-on-Line-settings..."))
            self.my_dialogue.tbw_central.setCurrentIndex(1)

    def s_append_data_features(self):
        """Adds current selected Features from dataLyr to self.rs.selected_pks"""
        # Rev. 2023-05-03
        if self.cf.reference_layer_complete and self.cf.data_layer_complete:
            additional_features = qgis.core.QgsVectorLayerUtils.getValues(self.ds.dataLyr, self.ds.dataLyrIdField.name(), selectedOnly=True)[0]
            if len(additional_features):
                if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                    self.rs.selected_pks += additional_features
                else:
                    self.rs.selected_pks = additional_features
                self.check_settings()
                self.dlg_refresh_feature_selection_section()
            else:
                self.push_messages(info_msg=QtCore.QCoreApplication.translate('LolEvt', "No selection in Data-Layer..."))
        else:
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "Missing requirements, Reference- and Data-Layer required, check Line-on-Line-settings..."))
            self.my_dialogue.tbw_central.setCurrentIndex(1)

    def s_zoom_to_feature_selection(self):
        """Zooms canvas to selected Features"""
        # Rev. 2023-05-08
        if self.cf.reference_layer_complete and self.cf.data_layer_complete and self.rs.selected_pks.__len__():
            data_fids = []
            show_fids = []

            # calculate extent of the selected LoL-Features
            top = -sys.float_info.max
            right = -sys.float_info.max
            left = sys.float_info.max
            bottom = sys.float_info.max

            for edit_pk in self.rs.selected_pks:
                data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
                if data_feature and data_feature.isValid():
                    ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, data_feature[self.ds.dataLyrReferenceField.name()])
                    if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():

                        measure_from = data_feature[self.ds.dataLyrMeasureFromField.name()]
                        measure_to = data_feature[self.ds.dataLyrMeasureToField.name()]
                        offset = data_feature[self.ds.dataLyrOffsetField.name()]
                        # detect Null-Values
                        if offset == '' or offset is None or repr(offset) == 'NULL':
                            offset = 0

                        segment_geom = tools.MyToolFunctions.get_segment_geom(ref_feature.geometry(), measure_from, measure_to, offset)
                        if segment_geom:
                            segment_geom.transform(qgis.core.QgsCoordinateTransform(self.ds.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                            extent = segment_geom.boundingBox()
                            left = min(left, extent.xMinimum())
                            bottom = min(bottom, extent.yMinimum())
                            right = max(right, extent.xMaximum())
                            top = max(top, extent.yMaximum())

                            data_fids.append(data_feature.id())

                        if self.cf.show_layer_complete:
                            show_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.showLyr, self.ds.showLyrBackReferenceField, edit_pk)
                            if show_feature and show_feature.isValid():
                                show_fids.append(show_feature.id())

            self.ds.dataLyr.removeSelection()
            self.ds.dataLyr.selectByIds(data_fids)

            if self.cf.show_layer_complete:
                self.ds.showLyr.removeSelection()
                self.ds.showLyr.selectByIds(show_fids)
                # self.iface.mapCanvas().zoomToSelected(self.ds.showLyr)

            # zoomToSelected without layer:
            if left < right or bottom < top:
                # valuable extent ➜ zoom
                extent = qgis.core.QgsRectangle(left, bottom, right, top)
                self.iface.mapCanvas().setExtent(extent)
                self.iface.mapCanvas().zoomByFactor(1.1)
            elif left == right and bottom == top:
                # theoretical: feature(s) with single point ➜ pan
                center_point = qgis.core.QgsPointXY(left, bottom)
                self.iface.mapCanvas().setCenter(center_point)
            else:
                # no feature or no point calculable, left/top/right/bottom as initialized with +- sys.float_info.max
                self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "no extent calculable for these features"))

    def s_append_show_features(self):
        """Adds current selected Features from showLyr to self.rs.selected_pks"""
        # Rev. 2023-05-03
        if self.cf.reference_layer_complete and self.cf.data_layer_complete and self.cf.show_layer_complete:

            additional_features = qgis.core.QgsVectorLayerUtils.getValues(self.ds.showLyr, self.ds.showLyrBackReferenceField.name(), selectedOnly=True)[0]
            if len(additional_features):
                if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                    self.rs.selected_pks += additional_features
                else:
                    self.rs.selected_pks = additional_features

                self.check_settings()
                self.dlg_refresh_feature_selection_section()
            else:
                self.push_messages(info_msg=QtCore.QCoreApplication.translate('LolEvt', "No selection in Show-Layer..."))
        else:
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "Missing requirements, Reference-, Data- and Show-Layer required, check Line-on-Line-settings..."))
            self.my_dialogue.tbw_central.setCurrentIndex(1)

    def s_update_feature(self):
        """Show feature-form for edit and save segment to Data-Layer"""
        # Rev. 2023-04-27
        try_it = True
        did_it = False
        critical_msg = ''
        success_msg = ''
        info_msg = ''
        warning_msg = ''

        if self.cf.update_enabled and self.rs.edit_pk is not None:
            if self.check_data_feature(self.rs.edit_pk):

                # get current edit-values from runtime-settings, not from dialogue-widgets
                data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, self.rs.edit_pk)
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                num_digits = 2
                if self.ds.refLyr.crs().isGeographic():
                    num_digits = 6

                measure_from = round(self.rs.current_measure_from, num_digits)
                measure_to = round(self.rs.current_measure_to, num_digits)
                offset = round(self.rs.current_offset, num_digits)

                data_feature[self.ds.dataLyrReferenceField.name()] = ref_feature[self.ds.refLyrPkField.name()]
                data_feature[self.ds.dataLyrMeasureFromField.name()] = measure_from
                data_feature[self.ds.dataLyrMeasureToField.name()] = measure_to
                data_feature[self.ds.dataLyrOffsetField.name()] = offset

                if self.ds.dataLyr.isEditable():
                    if self.ds.dataLyr.isModified():
                        dialog_result = QtWidgets.QMessageBox.question(
                            self.my_dialogue,
                            f"LinearReferencing Update Feature ({gdp()})",
                            qt_format(QtCore.QCoreApplication.translate('LolEvt', "{div_pre_1}Layer {apos}{0}{apos} is editable!{div_ml_1}[Yes]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} End edit session with save{br}[No]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} End edit session without save{br}[Cancel]{nbsp}{arrow} Quit...{div_ml_2}{div_pre_2}"), self.ds.dataLyr.name()),
                            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                            defaultButton=QtWidgets.QMessageBox.Yes
                        )

                        if dialog_result == QtWidgets.QMessageBox.Yes:
                            self.ds.dataLyr.commitChanges()
                        elif dialog_result == QtWidgets.QMessageBox.No:
                            self.ds.dataLyr.rollBack()
                        else:
                            try_it = False
                            info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")
                    else:
                        self.ds.dataLyr.rollBack()

                if try_it:
                    try:
                        self.ds.dataLyr.startEditing()
                        dlg_result = self.iface.openFeatureForm(self.ds.dataLyr, data_feature)
                        if dlg_result:
                            update_ref_pk = data_feature[self.ds.dataLyrReferenceField.name()]
                            update_measure_from = data_feature[self.ds.dataLyrMeasureFromField.name()]
                            update_measure_to = data_feature[self.ds.dataLyrMeasureToField.name()]
                            update_ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, update_ref_pk)
                            # User could have changed feature-data in dialog (PK, reference-id, measure)
                            # ➜ validity-check like "reference-id exists in refLyr?" "measure 0 ...referenced_line_length?"
                            if update_ref_feature and update_ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():

                                if ref_feature.geometry().constGet().partCount() > 1:
                                    warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Geometry {apos}{0}{apos} in Layer {apos}{1}{apos} is {2}-parted, Line-on-Line-Feature not calculable"), insert_ref_pk, self.ds.refLyr.name(), ref_feature.geometry().constGet().partCount())

                                if update_measure_from < 0 or update_measure_from > ref_feature.geometry().length() or update_measure_to < 0 or update_measure_to > ref_feature.geometry().length():
                                    info_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "measure-values from {apos}{0}{apos} to {apos}{1}{apos} truncated to range 0 ... {2}"), update_measure_from, update_measure_to, ref_feature.geometry().length())
                                    data_feature[self.ds.dataLyrMeasureFromField.name()] = max(0, min(ref_feature.geometry().length(), update_measure_from))
                                    data_feature[self.ds.dataLyrMeasureToField.name()] = max(0, min(ref_feature.geometry().length(), update_measure_to))

                                self.ds.dataLyr.updateFeature(data_feature)

                                commit_result = self.ds.dataLyr.commitChanges()
                                if commit_result:
                                    did_it = True
                                    success_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Feature with ID {apos}{0}{apos} successfully updated in {apos}{1}{apos}..."), self.rs.edit_pk, self.ds.dataLyr.name())
                                else:
                                    self.ds.dataLyr.rollBack()
                                    critical_msg = str(self.ds.dataLyr.commitErrors())

                            else:
                                self.ds.dataLyr.rollBack()
                                critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Update feature failed, no feature with PK {apos}{0}{apos} in Reference-Layer {apos}{1}{apos} ..."), update_ref_pk, self.ds.refLyr.name())
                        else:
                            self.ds.dataLyr.rollBack()
                            info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")

                    except Exception as err:
                        self.ds.dataLyr.rollBack()
                        critical_msg = f"Exception '{err.__class__.__name__}' in {gdp()}: {err}"
            else:
                critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Update feature failed, no feature {apos}{0}{apos} in Data-layer {apos}{1}{apos} or {apos}{2}{apos} in Reference-Layer {apos}{3}{apos} ..."), self.rs.edit_pk, self.ds.dataLyr.name(), self.rs.snapped_ref_fid, self.ds.refLyr.name())
        else:
            critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Update feature failed, missing privileges in layer {apos}{0}{apos}..."), self.ds.dataLyr.name())

        if did_it:
            if self.cf.show_layer_complete:
                self.ds.showLyr.updateExtents()
                if self.iface.mapCanvas().isCachingEnabled():
                    self.ds.showLyr.triggerRepaint()
                else:
                    self.iface.mapCanvas().refresh()
            self.set_edit_pk(self.rs.edit_pk, False)

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def s_zoom_to_ref_feature(self):
        """zooms to the current snapped Reference-Feature, fid comes from dialog"""
        # Rev. 2023-04-28
        if self.cf.reference_layer_defined:
            ref_fid = self.my_dialogue.qcbn_snapped_ref_fid.currentData()
            if ref_fid is not None:
                ref_feature = self.ds.refLyr.getFeature(ref_fid)
                if ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                    extent = ref_feature.geometry().boundingBox()
                    source_crs = self.ds.refLyr.crs()
                    target_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
                    tr = qgis.core.QgsCoordinateTransform(source_crs, target_crs, qgis.core.QgsProject.instance())
                    extent = tr.transformBoundingBox(extent)
                    self.iface.mapCanvas().setExtent(extent)
                    self.iface.mapCanvas().zoomByFactor(1.1)
                    self.rb_ref.setToGeometry(ref_feature.geometry(), self.ds.refLyr)
                    self.rb_ref.show()
                else:
                    self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "No valid feature with fid {apos}{0}{apos} in Reference-Layer"), ref_fid))

    def s_open_ref_form(self):
        """opens the attribute-form for the Reference-Layer"""
        # Rev. 2023-05-08
        if self.cf.reference_layer_defined:
            # feature-id != PK ➜ always integer
            ref_fid = self.my_dialogue.qcbn_snapped_ref_fid.currentData()
            if ref_fid is not None:
                ref_feature = self.ds.refLyr.getFeature(ref_fid)
                if ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                    self.rb_ref.setToGeometry(ref_feature.geometry(), self.ds.refLyr)
                    self.rb_ref.show()
                    self.iface.openFeatureForm(self.ds.refLyr, ref_feature)
                else:
                    self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Feature with fid {apos}{0}{apos} without geometry"), ref_fid))
            else:
                self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "No feature with fid {apos}{0}{apos} in Reference-Layer"), ref_fid))

    def s_open_show_lyr_tbl(self):
        """opens the Show-Layer-attribute-table """
        # Rev. 2023-05-08
        if self.cf.show_layer_defined:
            self.iface.showAttributeTable(self.ds.showLyr)

    def open_data_tbl(self):
        """opens the Data-Layer-attribute-table """
        # Rev. 2023-05-08
        if self.cf.data_layer_defined:
            self.iface.showAttributeTable(self.ds.dataLyr)

    def open_ref_tbl(self):
        """opens the Reference-Layer-attribute-table """
        # Rev. 2023-05-08
        if self.ds.refLyr is not None:
            self.iface.showAttributeTable(self.ds.refLyr)

    def s_define_ref_lyr_display_expression(self):
        """opens the dialog for editing the displayExpression of Reference-Layer"""
        # Rev. 2023-05-09
        if self.cf.reference_layer_defined:
            dlg = qgis.gui.QgsExpressionBuilderDialog(self.ds.refLyr, self.ds.refLyr.displayExpression())
            dlg.setWindowTitle(qt_format(QtCore.QCoreApplication.translate('LolEvt', "Edit DisplayExpression for Reference-Layer {apos}{0}{apos}"), self.ds.refLyr.name()))
            exec_result = dlg.exec()
            if exec_result:
                # expressionBuilder ➜ https://api.qgis.org/api/classQgsExpressionBuilderWidget.html
                if dlg.expressionBuilder().isExpressionValid():
                    self.ds.refLyr.setDisplayExpression(dlg.expressionText())

                    self.dlg_refresh_feature_selection_section()
                    self.push_messages(success_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Expression {apos}{0}{apos} valid and used as DisplayExpression for Reference-Layer {apos}{1}{apos}"), dlg.expressionText(), self.ds.refLyr.name()))
                else:
                    self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Expression {apos}{0}{apos} invalid and not used as DisplayExpression for Reference-Layer {apos}{1}{apos}, please check syntax!"), dlg.expressionText(), self.ds.refLyr.name()))
        else:
            # should not happen, because QPushButton disabled
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "No Reference-Layer defined yet"))

    def s_define_data_lyr_display_expression(self):
        """opens the dialog for editing the displayExpression of Data-Layer"""
        # Rev. 2023-05-09
        if self.cf.data_layer_defined:
            dlg = qgis.gui.QgsExpressionBuilderDialog(self.ds.dataLyr, self.ds.dataLyr.displayExpression())
            dlg.setWindowTitle(qt_format(QtCore.QCoreApplication.translate('LolEvt', "Edit DisplayExpression for Data-Layer {apos}{0}{apos}"), self.ds.dataLyr.name()))
            exec_result = dlg.exec()
            if exec_result:
                # expressionBuilder ➜ https://api.qgis.org/api/classQgsExpressionBuilderWidget.html
                if dlg.expressionBuilder().isExpressionValid():
                    self.ds.dataLyr.setDisplayExpression(dlg.expressionText())
                    self.dlg_refresh_feature_selection_section()
                    self.push_messages(success_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Expression {apos}{0}{apos} valid and used as DisplayExpression for Data-Layer {apos}{1}{apos}"), dlg.expressionText(), self.ds.dataLyr.name()))
                else:
                    self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Expression {apos}{0}{apos} invalid and not used as DisplayExpression for Data-Layer {apos}{1}{apos}, please check syntax!"), dlg.expressionText(), self.ds.dataLyr.name()))
        else:
            # should not happen, because QPushButton disabled
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "No Data-Layer defined yet"))

    def s_define_show_lyr_display_expression(self):
        """opens the dialog for editing the displayExpression of Show-Layer"""
        # Rev. 2023-05-09
        if self.cf.show_layer_defined:
            dlg = qgis.gui.QgsExpressionBuilderDialog(self.ds.showLyr, self.ds.showLyr.displayExpression())
            dlg.setWindowTitle(qt_format(QtCore.QCoreApplication.translate('LolEvt', "Edit DisplayExpression for Show-Layer {apos}{0}{apos}"), self.ds.showLyr.name()))
            exec_result = dlg.exec()
            if exec_result:
                # expressionBuilder ➜ https://api.qgis.org/api/classQgsExpressionBuilderWidget.html
                if dlg.expressionBuilder().isExpressionValid():
                    self.ds.showLyr.setDisplayExpression(dlg.expressionText())
                    self.dlg_refresh_feature_selection_section()
                    self.push_messages(success_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Expression {apos}{0}{apos} valid and used as DisplayExpression for Show-Layer {apos}{1}{apos}"), dlg.expressionText(), self.ds.showLyr.name()))
                else:
                    self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Expression {apos}{0}{apos} invalid and not used as DisplayExpression for Show-Layer {apos}{1}{apos}, please check syntax!"), dlg.expressionText(), self.ds.showLyr.name()))
        else:
            # should not happen, because QPushButton disabled
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "No Show-Layer defined yet"))

    def s_change_measure_from(self, measure_from: float) -> None:
        """change measure_from in dialog: recalculate distance, from_point and line-segment
        :param measure_from:"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                self.rs.current_measure_from = min(max(0, measure_from), ref_feature.geometry().length())
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)

    def s_change_measure_fract_from(self, measure_fract_from: float) -> None:
        """change measure_fract_from in dialog: recalculate distance, from_point and line-segment
        :param measure_fract_from: Value from DoubleSpinBox, Fractional 0...1
        """
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                measure_fract_from = min(max(0, measure_fract_from), 1)
                self.rs.current_measure_from = measure_fract_from * ref_feature.geometry().length()
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)

    def s_change_measure_fract_to(self, measure_fract_to: float) -> None:
        """change measure_fract_to in dialog: recalculate distance, to_point and line-segment
        :param measure_fract_to: Value from DoubleSpinBox, Fractional 0...1
        """
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                measure_fract_to = min(max(0, measure_fract_to), 1)
                self.rs.current_measure_to = measure_fract_to * ref_feature.geometry().length()
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)

    def s_zoom_to_segment(self):
        """Zooms to current segment, defined by self.rs.xxx"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            self.zoom_to_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)

    def s_move_segment_end(self):
        """moves current segment to end of reference-line"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                delta = min((ref_feature.geometry().length() - self.rs.current_measure_from), (ref_feature.geometry().length() - self.rs.current_measure_to))

                self.rs.current_measure_from += delta
                self.rs.current_measure_to += delta
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)

    def s_move_segment_start(self):
        """moves current segment to start of reference-line"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            delta = min(self.rs.current_measure_from, self.rs.current_measure_to)
            self.rs.current_measure_from -= delta
            self.rs.current_measure_to -= delta

            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)

    def s_prepend_segment(self):
        """prepends current segment in direction of start of reference-line"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                m_from = min(self.rs.current_measure_from, self.rs.current_measure_to)
                m_to = max(self.rs.current_measure_from, self.rs.current_measure_to)
                dist = m_to - m_from

                new_from = m_from - dist
                new_to = m_to - dist
                if new_from < 0:
                    new_from = 0
                    # new_to = new_from + dist

                self.rs.current_measure_from = new_from
                self.rs.current_measure_to = new_to

                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)

    def s_append_segment(self):
        """appends current segment in direction of end of reference-line"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                m_from = min(self.rs.current_measure_from, self.rs.current_measure_to)
                m_to = max(self.rs.current_measure_from, self.rs.current_measure_to)
                dist = m_to - m_from
                new_from = m_from + dist
                new_to = m_to + dist
                if new_to > ref_feature.geometry().length():
                    new_to = ref_feature.geometry().length()
                    # new_from = new_to - dist

                self.rs.current_measure_from = new_from
                self.rs.current_measure_to = new_to
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)

    def s_move_segment_up(self):
        """change measure_from in dialog: recalculate distance, from_point and line-segment
        takes keyboardModifiers into account by factorising the step-width"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:

            delta = 1

            if self.ds.refLyr.crs().isGeographic():
                delta *= 1e-4

            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                delta *= 10
            elif QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                delta *= 100
            elif QtWidgets.QApplication.keyboardModifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
                delta *= 1000

            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)

            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                # not further then line-end
                delta = min((ref_feature.geometry().length() - self.rs.current_measure_from), (ref_feature.geometry().length() - self.rs.current_measure_to), delta)

                self.rs.current_measure_from += delta
                self.rs.current_measure_to += delta
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)

    def s_move_segment_down(self):
        """change measure_from in dialog: recalculate distance, from_point and line-segment
        takes keyboardModifiers into account by factorising the step-width"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:

            delta = 1

            if self.ds.refLyr.crs().isGeographic():
                delta *= 1e-4

            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                delta *= 10
            elif QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                delta *= 100
            elif QtWidgets.QApplication.keyboardModifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
                delta *= 1000

            # not further then line-start
            delta = min(self.rs.current_measure_from, self.rs.current_measure_to, delta)

            self.rs.current_measure_from -= delta
            self.rs.current_measure_to -= delta

            self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
            self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
            self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
            self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
            self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)

    def s_change_offset(self, offset: float) -> None:
        """triggered by offset-QDoubleSpinBox, redraws segment_geom with new offset, if measure_completed
        :param offset:"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            self.rs.current_offset = offset
            self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)

    def s_change_measure_to(self, measure_to: float) -> None:
        """change measure_from in dialog: recalculate distance, from_point and line-segment
        :param measure_to:"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                self.rs.current_measure_to = min(max(0, measure_to), ref_feature.geometry().length())
                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)

    def s_change_distance(self, distance: float) -> None:
        """change distance in dialog: recalculate self.rs.current_measure_to, redraws segment_geom (and recalculates/refills dialog)
        :param distance:"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                old_distance = self.rs.current_measure_to - self.rs.current_measure_from
                delta_distance = distance - old_distance
                self.rs.current_measure_to += delta_distance
                self.rs.current_measure_to = min(ref_feature.geometry().length(), max(0, self.rs.current_measure_to))

                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)

    def zoom_to_segment(self, ref_fid: int, measure_from: float, measure_to: float, offset: float):
        """zoom to segment-geom
        :param ref_fid: ID of feature in Reference-Layer
        :param measure_from: distance of segment-start-point to start of referenced line
        :param measure_to: distance of segment-end-point to start of referenced line
        :param offset: offset of line-segment
        """
        # Rev. 2023-05-08
        ref_feature = self.ds.refLyr.getFeature(ref_fid)
        if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
            segment_geom = tools.MyToolFunctions.get_segment_geom(ref_feature.geometry(), measure_from, measure_to, offset)
            if segment_geom:
                extent = segment_geom.boundingBox()
                source_crs = self.ds.refLyr.crs()
                target_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
                tr = qgis.core.QgsCoordinateTransform(source_crs, target_crs, qgis.core.QgsProject.instance())
                extent = tr.transformBoundingBox(extent)
                self.iface.mapCanvas().setExtent(extent)
                self.iface.mapCanvas().zoomByFactor(1.1)
                # self.rb_ref.setToGeometry(ref_feature.geometry(), self.ds.refLyr)
                # self.rb_ref.show()
        else:
            self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Reference-feature without geometry (Reference-Layer {apos}{0}{apos}, field {apos}{1}{apos}, value {apos}{2}{apos})"), self.ds.refLyr.name(), self.ds.dataLyrReferenceField.name(), data_feature[self.ds.dataLyrReferenceField.name()]))

    def draw_segment(self, ref_fid: int, measure_from: float, measure_to: float, offset: float):
        """show the segment-geom-rubberband
        :param ref_fid: ID of feature in Reference-Layer
        :param measure_from: distance of segment-start-point to start of referenced line
        :param measure_to: distance of segment-end-point to start of referenced line
        :param offset: offset of line-segment
        """
        # Rev. 2023-05-08
        ref_feature = self.ds.refLyr.getFeature(ref_fid)
        if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
            segment_geom = tools.MyToolFunctions.get_segment_geom(ref_feature.geometry(), measure_from, measure_to, offset)
            if segment_geom:
                self.rb_segment.setToGeometry(segment_geom, self.ds.refLyr)
                self.rb_segment.show()

    def draw_from_point(self, ref_fid: int, measure: float):
        """positions and shows vm_pt_measure_from on canvas
        :param ref_fid: ID of feature in Reference-Layer
        :param measure: distance to start of linestring_geom
        """
        # Rev. 2023-05-08
        self.vm_pt_measure_from.hide()
        ref_feature = self.ds.refLyr.getFeature(ref_fid)
        if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
            point_geom = ref_feature.geometry().interpolate(measure)
            if point_geom:
                point_geom.transform(qgis.core.QgsCoordinateTransform(self.ds.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))
                self.vm_pt_measure_from.setCenter(point_geom.asPoint())
                self.vm_pt_measure_from.show()

    def draw_to_point(self, ref_fid: int, measure: float):
        """positions and shows vm_pt_measure_from on canvas
        :param ref_fid: ID of feature in Reference-Layer
        :param measure: distance to start of linestring_geom
        """
        # Rev. 2023-05-08
        self.vm_pt_measure_to.hide()
        ref_feature = self.ds.refLyr.getFeature(ref_fid)
        if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
            point_geom = ref_feature.geometry().interpolate(measure)
            if point_geom:
                point_geom.transform(qgis.core.QgsCoordinateTransform(self.ds.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))
                self.vm_pt_measure_to.setCenter(point_geom.asPoint())
                self.vm_pt_measure_to.show()

    def dlg_refresh_measure_from(self, ref_fid: int, measure: float):
        """shows the from-point-coords (transformed snapped to line-position), measure and fraction in dialogue
        :param ref_fid: fid of referenced line
        :param measure: distance to start-point of referenced line
        """
        # Rev. 2023-05-27
        ref_feature = self.ds.refLyr.getFeature(ref_fid)

        if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
            point_geom = ref_feature.geometry().interpolate(measure)

            if point_geom:
                self.my_dialogue.le_snap_pt_from_x.blockSignals(True)
                self.my_dialogue.le_snap_pt_from_y.blockSignals(True)
                self.my_dialogue.dspbx_measure_from.blockSignals(True)
                self.my_dialogue.dspbx_measure_fract_from.blockSignals(True)

                self.my_dialogue.le_snap_pt_from_x.clear()
                self.my_dialogue.le_snap_pt_from_y.clear()
                self.my_dialogue.dspbx_measure_from.clear()
                self.my_dialogue.dspbx_measure_fract_from.clear()

                # round the values with num_digits, depending on the projection
                str_snap_x = '{:.{prec}f}'.format(point_geom.asPoint().x(), prec=self.rs.num_digits)
                str_snap_y = '{:.{prec}f}'.format(point_geom.asPoint().y(), prec=self.rs.num_digits)

                self.my_dialogue.le_snap_pt_from_x.setText(str_snap_x)
                self.my_dialogue.le_snap_pt_from_y.setText(str_snap_y)

                self.my_dialogue.dspbx_measure_from.setValue(measure)
                self.my_dialogue.dspbx_measure_from.setRange(0, ref_feature.geometry().length())
                self.my_dialogue.dspbx_measure_fract_from.setValue(measure / ref_feature.geometry().length())

                self.my_dialogue.le_snap_pt_from_x.blockSignals(False)
                self.my_dialogue.le_snap_pt_from_y.blockSignals(False)
                self.my_dialogue.dspbx_measure_from.blockSignals(False)
                self.my_dialogue.dspbx_measure_fract_from.blockSignals(False)

    def dlg_refresh_measure_to(self, ref_fid: int, measure: float):
        """shows the to-point-coords (transformed snapped to line-position), measure and fraction in dialogue
        :param ref_fid: fid of referenced line
        :param measure: distance to start-point of referenced line
        """
        # Rev. 2023-05-27

        ref_feature = self.ds.refLyr.getFeature(ref_fid)

        if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
            point_geom = ref_feature.geometry().interpolate(measure)
            if point_geom:
                self.my_dialogue.le_snap_pt_to_x.blockSignals(True)
                self.my_dialogue.le_snap_pt_to_y.blockSignals(True)
                self.my_dialogue.dspbx_measure_to.blockSignals(True)
                self.my_dialogue.dspbx_measure_fract_to.blockSignals(True)

                self.my_dialogue.le_snap_pt_to_x.clear()
                self.my_dialogue.le_snap_pt_to_y.clear()

                self.my_dialogue.dspbx_measure_to.clear()
                self.my_dialogue.dspbx_measure_fract_to.clear()

                # round the values with num_digits, depending on the projection
                str_snap_x = '{:.{prec}f}'.format(point_geom.asPoint().x(), prec=self.rs.num_digits)
                str_snap_y = '{:.{prec}f}'.format(point_geom.asPoint().y(), prec=self.rs.num_digits)

                self.my_dialogue.le_snap_pt_to_x.setText(str_snap_x)
                self.my_dialogue.le_snap_pt_to_y.setText(str_snap_y)

                self.my_dialogue.dspbx_measure_to.setValue(measure)
                self.my_dialogue.dspbx_measure_to.setRange(0, ref_feature.geometry().length())
                self.my_dialogue.dspbx_measure_fract_to.setValue(measure / ref_feature.geometry().length())

                self.my_dialogue.le_snap_pt_to_x.blockSignals(False)
                self.my_dialogue.le_snap_pt_to_y.blockSignals(False)
                self.my_dialogue.dspbx_measure_to.blockSignals(False)
                self.my_dialogue.dspbx_measure_fract_to.blockSignals(False)

    def s_change_data_layer_measure_from_field(self) -> None:
        """change measure-from-field of Data-Layer in QComboBox"""
        # Rev. 2023-05-08
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.ss.dataLyrMeasureFromFieldName = None
        measure_field = self.my_dialogue.qcbn_data_layer_measure_from_field.currentData()
        if measure_field:
            self.ss.dataLyrMeasureFromFieldName = measure_field.name()

        self.check_settings()
        self.refresh_data_layer_actions()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def s_change_data_layer_measure_to_field(self) -> None:
        """change measure-to-field of Data-Layer in QComboBox"""
        # Rev. 2023-05-08
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.ss.dataLyrMeasureToFieldName = None
        measure_to_field = self.my_dialogue.qcbn_data_layer_measure_to_field.currentData()
        if measure_to_field:
            self.ss.dataLyrMeasureToFieldName = measure_to_field.name()
        self.check_settings()
        self.refresh_data_layer_actions()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def s_change_data_layer_offset_field(self) -> None:
        """change offset-field of Data-Layer in QComboBox"""
        # Rev. 2023-05-08
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.ss.dataLyrOffsetFieldName = None
        offset_field = self.my_dialogue.qcbn_data_layer_offset_field.currentData()
        if offset_field:
            self.ss.dataLyrOffsetFieldName = offset_field.name()

        self.check_settings()
        self.refresh_data_layer_actions()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def s_change_show_lyr_back_ref(self) -> None:
        """change Back-Reference-Field of Show-Layer in QComboBox"""
        # Rev. 2023-05-08
        self.ss.showLyrBackReferenceFieldName = None

        back_ref_field = self.my_dialogue.qcbn_show_layer_back_reference_field.currentData()
        if back_ref_field:
            self.ss.showLyrBackReferenceFieldName = back_ref_field.name()
        self.check_settings()
        self.refresh_show_layer_actions()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def s_change_data_layer_id_field(self) -> None:
        """change reference-id-field of Data-Layer-PK-Field in QComboBox"""
        # Rev. 2023-05-08
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.ss.dataLyrIdFieldName = None
        id_field = self.my_dialogue.qcbn_data_layer_id_field.currentData()
        if id_field:
            self.ss.dataLyrIdFieldName = id_field.name()

        self.check_settings()
        self.refresh_data_layer_actions()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def s_change_data_layer_reference_field(self) -> None:
        """change reference-id-field of Data-Layer-reference-field in QComboBox"""
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.ss.dataLyrReferenceFieldName = None
        if self.ss.dataLyrId:
            ref_id_field = self.my_dialogue.qcbn_data_layer_reference_field.currentData()
            if ref_id_field:
                self.ss.dataLyrReferenceFieldName = ref_id_field.name()

        self.check_settings()
        self.refresh_data_layer_actions()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def s_change_reference_layer(self) -> None:
        """change Reference-Layer in QComboBox"""
        # Rev. 2023-05-03
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.ss.refLyrId = None
        self.ss.refLyrIdFieldName = None
        self.ss.dataLyrId = None
        self.ss.dataLyrIdFieldName = None
        self.ss.dataLyrReferenceFieldName = None
        self.ss.dataLyrMeasureFieldName = None
        self.ss.showLyrId = None
        self.ss.showLyrBackReferenceFieldName = None
        reference_layer = self.my_dialogue.qcbn_reference_layer.currentData()
        self.connect_reference_layer(reference_layer)
        self.check_settings()
        self.dlg_refresh_reference_layer_section()
        self.dlg_refresh_measure_section()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def disconnect_reference_layers(self):
        """disconnect all potential reference-layers: disconnect signal/slot"""
        # Rev. 2023-05-22
        disconnect_errors = []
        linestring_layers = tools.MyToolFunctions.get_linestring_layers()
        for layer_id in linestring_layers:
            layer = linestring_layers[layer_id]
            for connection in self.rs.reference_layer_connections:
                try:
                    layer.disconnect(connection)
                except Exception as e:
                    # "'method' object is not connected"
                    disconnect_errors.append(f"'{layer.name()}' disconnect ➜ \"{e}\"")

        self.rs.reference_layer_connections = []

        if disconnect_errors:
            #     print(disconnect_errors)
            pass

    def disconnect_show_layers(self):
        """disconnect all potential show-layers: disconnect signal/slot and removeAction """
        # Rev. 2023-05-22
        disconnect_errors = []
        line_show_layers = tools.MyToolFunctions.get_line_show_layers()
        for layer_id in line_show_layers:
            layer = line_show_layers[layer_id]

            action_list = [action for action in layer.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]]
            for action in action_list:
                layer.actions().removeAction(action.id())

            for connection in self.rs.show_layer_connections:
                try:
                    layer.disconnect(connection)
                except Exception as e:
                    # "'method' object is not connected"
                    disconnect_errors.append(f"'{layer.name()}' disconnect ➜ \"{e}\"")

            attribute_table_widgets = [widget for widget in QtWidgets.QApplication.instance().allWidgets() if isinstance(widget, QtWidgets.QDialog) and widget.objectName() == f"QgsAttributeTableDialog/{layer.id()}"]

            for at_wdg in attribute_table_widgets:
                reload_action = at_wdg.findChild(QtWidgets.QAction, 'mActionReload')
                if reload_action:
                    reload_action.trigger()

        self.rs.show_layer_connections = []
        if disconnect_errors:
            #     print(disconnect_errors)
            pass

    def connect_reference_layer(self, reference_layer) -> None:
        """prepares Reference-Layer:
        sets self.ss.dataLyrId
        adds actions
        connects signals
        cleans previous refLyr
        """
        # Rev. 2023-05-03
        # disconnect all previously connected Reference-Layer
        self.disconnect_reference_layers()
        prev_refLyrId = self.ss.refLyrId
        self.ss.refLyrId = None
        if reference_layer:
            self.ss.refLyrId = reference_layer.id()
            # snapping settings ar stored in canvas, not in layer
            my_snap_config = self.iface.mapCanvas().snappingUtils().config()
            # clear all previous settings
            my_snap_config.clearIndividualLayerSettings()
            # enable snapping
            my_snap_config.setEnabled(True)
            # advanced: layer-wise snapping settings
            my_snap_config.setMode(qgis.core.QgsSnappingConfig.AdvancedConfiguration)
            # combination of snapping-modes
            type_flag = qgis.core.Qgis.SnappingTypes(qgis.core.Qgis.SnappingType.Segment | qgis.core.Qgis.SnappingType.LineEndpoint)
            my_snap_config.setIndividualLayerSettings(reference_layer, qgis.core.QgsSnappingConfig.IndividualLayerSettings(enabled=True, type=type_flag, tolerance=10, units=qgis.core.QgsTolerance.UnitType.Pixels))
            my_snap_config.setIntersectionSnapping(False)
            qgis.core.QgsProject.instance().setSnappingConfig(my_snap_config)

            # second: connect to new refLyr
            # displayExpressionChanged not triggered with configChanged
            # afterCommitChanges ➜ refresh too, if the Reference-Layer was edited
            # QtCore.Qt.UniqueConnection avoids double-connects (throws Exception if already connected)
            self.rs.reference_layer_connections.append(reference_layer.configChanged.connect(self.refresh_gui))
            self.rs.reference_layer_connections.append(reference_layer.displayExpressionChanged.connect(self.refresh_gui))
            self.rs.reference_layer_connections.append(reference_layer.afterCommitChanges.connect(self.dlg_refresh_feature_selection_section))
            self.rs.reference_layer_connections.append(reference_layer.afterCommitChanges.connect(self.dlg_refresh_reference_layer_section))

            # Layer has changed ➜ check and warn if multi-xxx-layer
            if reference_layer.id() != prev_refLyrId:
                multi_linestring_geometry_types = [
                    # problematic: Shape-Format doesn't distinguish between single- and multi-geometry-types
                    # unpredictable though, how measures on multi-linestring will be located
                    qgis.core.QgsWkbTypes.MultiLineString,
                    qgis.core.QgsWkbTypes.MultiLineString25D,
                    qgis.core.QgsWkbTypes.MultiLineStringM,
                    qgis.core.QgsWkbTypes.MultiLineStringZ,
                    qgis.core.QgsWkbTypes.MultiLineStringZM,

                ]

                if reference_layer.dataProvider().wkbType() in multi_linestring_geometry_types:
                    # enum since QGis 3.30
                    # inspect_class = qgis.core.QgsWkbTypes
                    # enum_class = qgis.core.QgsWkbTypes
                    # before 3.30 but still valid:
                    inspect_class = qgis.core.QgsWkbTypes
                    enum_class = qgis.core.QgsWkbTypes.Type
                    keys_by_value = {getattr(inspect_class, att_name): att_name for att_name in vars(inspect_class) if type(getattr(inspect_class, att_name)) == enum_class}
                    wkb_label = keys_by_value[reference_layer.dataProvider().wkbType()]
                    self.push_messages(info_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Reference-Layer {apos}{0}{apos} is of type {apos}{1}{apos}, Line-on-Line-features on multi-lines are not shown"), reference_layer.name(), wkb_label))

    def s_change_reference_layer_id_field(self) -> None:
        """change Reference-Layer-join-field in QComboBox"""
        # Rev. 2023-05-08
        self.rs.selected_pks = []
        self.rs.edit_pk = None
        self.ss.refLyrIdFieldName = None
        self.ss.dataLyrId = None
        self.ss.dataLyrIdFieldName = None
        self.ss.dataLyrReferenceFieldName = None
        self.ss.dataLyrMeasureFromFieldName = None
        self.ss.dataLyrMeasureToFieldName = None
        self.ss.dataLyrOffsetFieldName = None
        self.ss.showLyrId = None
        self.ss.showLyrBackReferenceFieldName = None

        reference_layer_id_field = self.my_dialogue.qcbn_reference_layer_id_field.currentData()
        if reference_layer_id_field:
            self.ss.refLyrIdFieldName = reference_layer_id_field.name()
        self.check_settings()
        self.dlg_refresh_reference_layer_section()
        self.dlg_refresh_measure_section()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def s_change_data_layer(self) -> None:
        """change Data-Layer in QComboBox"""
        # Rev. 2023-05-08
        self.rs.selected_pks = []
        self.rs.edit_pk = None

        self.ss.dataLyrId = None
        self.ss.dataLyrIdFieldName = None
        self.ss.dataLyrReferenceFieldName = None
        self.ss.dataLyrMeasureFromFieldName = None
        self.ss.dataLyrMeasureToFieldName = None
        self.ss.dataLyrOffsetFieldName = None
        self.ss.showLyrId = None
        self.ss.showLyrBackReferenceFieldName = None

        self.connect_data_layer(self.my_dialogue.qcbn_data_layer.currentData())
        self.check_settings()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def disconnect_all_layers(self):
        """remove Plugin-Layer-Actions from Vector-Layers
        removes connected slots
        .. Note::
            * no table refresh ➜ reopen table/form necessary
            * attributeTableConfig.setActionWidgetVisible(True) will be unchanged
        """
        # Rev. 2023-05-08

        self.disconnect_data_layers()
        self.disconnect_reference_layers()
        self.disconnect_show_layers()

    def disconnect_data_layers(self):
        """disconnect all potential data-layers: disconnect signal/slot and removeAction """
        # Rev. 2023-05-22
        disconnect_errors = []
        data_layers = tools.MyToolFunctions.get_data_layers()
        for layer_id in data_layers:
            layer = data_layers[layer_id]

            action_list = [action for action in layer.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]]
            for action in action_list:
                layer.actions().removeAction(action.id())

            for connection in self.rs.data_layer_connections:
                try:
                    layer.disconnect(connection)
                except Exception as e:
                    # "'method' object is not connected"
                    disconnect_errors.append(f"'{layer.name()}' disconnect ➜ \"{e}\"")

            attribute_table_widgets = [widget for widget in QtWidgets.QApplication.instance().allWidgets() if isinstance(widget, QtWidgets.QDialog) and widget.objectName() == f"QgsAttributeTableDialog/{layer.id()}"]

            for at_wdg in attribute_table_widgets:
                reload_action = at_wdg.findChild(QtWidgets.QAction, 'mActionReload')
                if reload_action:
                    reload_action.trigger()

        self.rs.data_layer_connections = []
        if disconnect_errors:
            #     print(disconnect_errors)
            pass

    def connect_all_layers(self):
        if self.ds.dataLyr:
            self.connect_data_layer(self.ds.dataLyr)

        if self.ds.refLyr:
            self.connect_reference_layer(self.ds.refLyr)

        if self.ds.showLyr:
            self.connect_show_layer(self.ds.showLyr)

    def refresh_data_layer_actions(self):
        """refreshes the action-buttons in Data-Layer"""
        if self.ds.dataLyr is not None:
            action_list = [action for action in self.ds.dataLyr.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]]
            for action in action_list:
                self.ds.dataLyr.actions().removeAction(action.id())

            if self.cf.data_layer_complete:
                action_dict = {action.id(): action for action in self.ds.dataLyr.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]}
                if not self._lyr_act_id_1 in action_dict:
                    data_layer_s_h_action = qgis.core.QgsAction(
                        self._lyr_act_id_1,
                        qgis.core.QgsAction.ActionType.GenericPython,  # int 1
                        'Select + Highlight',
                        "from LinearReferencing.map_tools.FeatureActions import edit_line_on_line_feature\nedit_line_on_line_feature([%@id%],'[%@layer_id%]',False)",
                        ':icons/mIconSelected.svg',
                        False,
                        '',
                        {'Feature'},
                        ''
                    )
                    self.ds.dataLyr.actions().addAction(data_layer_s_h_action)
                if not self._lyr_act_id_2 in action_dict:
                    data_layer_s_h_p_action = qgis.core.QgsAction(
                        self._lyr_act_id_2,
                        qgis.core.QgsAction.ActionType.GenericPython,  # int 1
                        'Select + Highlight + Pan',
                        "from LinearReferencing.map_tools.FeatureActions import edit_line_on_line_feature\nedit_line_on_line_feature([%@id%],'[%@layer_id%]',True)",
                        ':icons/mActionPanToSelected.svg',
                        False,
                        '',
                        {'Feature'},
                        ''
                    )

                    self.ds.dataLyr.actions().addAction(data_layer_s_h_p_action)

            atc = self.ds.dataLyr.attributeTableConfig()
            if not atc.actionWidgetVisible():
                # qgis.core.QgsAttributeTableConfig.ButtonList / qgis.core.QgsAttributeTableConfig.DropDown
                atc.setActionWidgetStyle(qgis.core.QgsAttributeTableConfig.ButtonList)
                atc.setActionWidgetVisible(True)
                self.ds.dataLyr.setAttributeTableConfig(atc)

            # tricky: get all associated opened attribute-tables for this Layer and refresh their contents to show the new actions
            attribute_table_widgets = [widget for widget in QtWidgets.QApplication.instance().allWidgets() if isinstance(widget, QtWidgets.QDialog) and widget.objectName() == f"QgsAttributeTableDialog/{self.ds.dataLyr.id()}"]

            for at_wdg in attribute_table_widgets:
                reload_action = at_wdg.findChild(QtWidgets.QAction, 'mActionReload')
                if reload_action:
                    reload_action.trigger()

    def disconnect_data_layer(self):
        """disconnects currently registered Data-Layer"""
        if self.ds.dataLyr:
            action_list = [action for action in self.ds.dataLyr.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]]
            for action in action_list:
                self.ds.dataLyr.actions().removeAction(action.id())

            for connection in self.rs.data_layer_connections:
                try:
                    self.ds.dataLyr.disconnect(connection)
                except Exception as e:
                    # "'method' object is not connected"
                    pass

            attribute_table_widgets = [widget for widget in QtWidgets.QApplication.instance().allWidgets() if isinstance(widget, QtWidgets.QDialog) and widget.objectName() == f"QgsAttributeTableDialog/{self.ds.dataLyr.id()}"]

            for at_wdg in attribute_table_widgets:
                reload_action = at_wdg.findChild(QtWidgets.QAction, 'mActionReload')
                if reload_action:
                    reload_action.trigger()

    def connect_data_layer(self, data_layer) -> None:
        """prepares Data-Layer:
        sets self.ss.dataLyrId
        adds actions
        connects signals
        disconnects previous dataLyr
        """
        # Rev. 2023-05-08
        critical_msg = ''
        success_msg = ''
        info_msg = ''
        warning_msg = ''

        # disconnect
        self.disconnect_data_layer()

        self.ss.dataLyrId = None

        if data_layer:

            # https://doc.qt.io/qt-5/qmetaobject-connection.html
            self.rs.data_layer_connections.append(data_layer.configChanged.connect(self.refresh_gui))
            self.rs.data_layer_connections.append(data_layer.afterCommitChanges.connect(self.dlg_refresh_data_sections))
            self.rs.data_layer_connections.append(data_layer.displayExpressionChanged.connect(self.refresh_gui))

            storage_type = data_layer.dataProvider().storageType()
            if storage_type in ['XLSX', 'ODS']:
                warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Source-Format of chosen Data-Layer {apos}{0}{apos} is a file-based office-format (*.xlsx/*.odf), supported, but not recommended..."), data_layer.name())

            caps = data_layer.dataProvider().capabilities()
            caps_result = []
            if not (caps & qgis.core.QgsVectorDataProvider.AddFeatures):
                caps_result.append("AddFeatures")

            if not (caps & qgis.core.QgsVectorDataProvider.DeleteFeatures):
                caps_result.append("DeleteFeatures")

            if not (caps & qgis.core.QgsVectorDataProvider.ChangeAttributeValues):
                caps_result.append("ChangeAttributeValues")

            if caps_result:
                caps_string = ", ".join(caps_result)
                warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Missing capabilities in Data-Layer: {apos}{0}{apos}, some editing options will not be available"), caps_string)

            self.ss.dataLyrId = data_layer.id()

        self.refresh_data_layer_actions()
        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def dlg_refresh_data_sections(self):
        """wrapper-slot for any Data-Layer-change (update/insert/delete), refreshes parts of the dialog"""
        # Rev. 2023-05-10
        self.dlg_refresh_measure_section()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()

    def refresh_canvas_graphics(self):
        """applies self.ss to canvas-grafics"""
        # Rev. 2023-05-08
        # selection-rect, not customizable
        self.rb_selection_rect.setWidth(2)
        # red border, half transparent
        self.rb_selection_rect.setColor(QtGui.QColor(255, 0, 0, 100))

        if self.ss.ref_line_width is not None:
            self.rb_ref.setWidth(self.ss.ref_line_width)
        if self.ss.ref_line_line_style is not None:
            self.rb_ref.setLineStyle(self.ss.ref_line_line_style)
        if self.ss.ref_line_color is not None:
            self.rb_ref.setColor(QtGui.QColor(self.ss.ref_line_color))

        if self.ss.segment_line_width is not None:
            self.rb_segment.setWidth(self.ss.segment_line_width)
        if self.ss.segment_line_line_style is not None:
            self.rb_segment.setLineStyle(self.ss.segment_line_line_style)
        if self.ss.segment_line_color is not None:
            self.rb_segment.setColor(QtGui.QColor(self.ss.segment_line_color))

        if self.ss.to_point_pen_width is not None:
            self.vm_pt_measure_to.setPenWidth(self.ss.to_point_pen_width)
        if self.ss.to_point_icon_size is not None:
            self.vm_pt_measure_to.setIconSize(self.ss.to_point_icon_size)
        if self.ss.to_point_icon_type is not None:
            self.vm_pt_measure_to.setIconType(self.ss.to_point_icon_type)
        if self.ss.to_point_color is not None:
            self.vm_pt_measure_to.setColor(QtGui.QColor(self.ss.to_point_color))
        if self.ss.to_point_fill_color is not None:
            self.vm_pt_measure_to.setFillColor(QtGui.QColor(self.ss.to_point_fill_color))

        if self.ss.from_point_pen_width is not None:
            self.vm_pt_measure_from.setPenWidth(self.ss.from_point_pen_width)
        if self.ss.from_point_icon_size is not None:
            self.vm_pt_measure_from.setIconSize(self.ss.from_point_icon_size)
        if self.ss.from_point_icon_type is not None:
            self.vm_pt_measure_from.setIconType(self.ss.from_point_icon_type)
        if self.ss.from_point_color is not None:
            self.vm_pt_measure_from.setColor(QtGui.QColor(self.ss.from_point_color))
        if self.ss.from_point_fill_color is not None:
            self.vm_pt_measure_from.setFillColor(QtGui.QColor(self.ss.from_point_fill_color))

        self.iface.mapCanvas().refresh()

    def s_change_show_lyr(self) -> None:
        """change Show-Layer in QComboBox, items are filtered to suitable layer-types"""
        # Rev. 2023-05-03
        self.ss.showLyrId = None
        self.ss.showLyrBackReferenceFieldName = None
        self.connect_show_layer(self.my_dialogue.qcbn_show_layer.currentData())
        self.check_settings()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()

    def connect_show_layer(self, show_layer) -> None:
        """prepares Show-Layer:
        sets self.ss.showLyrId
        adds actions
        connects signals
        cleans previous showLyr
        """
        # Rev. 2023-05-03
        self.disconnect_show_layers()

        self.ss.showLyrId = None
        if show_layer:
            self.ss.showLyrId = show_layer.id()
            self.rs.show_layer_connections.append(show_layer.configChanged.connect(self.refresh_gui))
            self.rs.show_layer_connections.append(show_layer.displayExpressionChanged.connect(self.refresh_gui))
            self.ds.showLyr = show_layer
            self.refresh_show_layer_actions()

    def refresh_show_layer_actions(self):
        if self.ds.showLyr is not None:
            action_list = [action for action in self.ds.showLyr.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]]
            for action in action_list:
                self.ds.showLyr.actions().removeAction(action.id())

            if self.cf.show_layer_complete:
                # BackReference-Field necessary for these layer-actions
                action_dict = {action.id(): action for action in self.ds.showLyr.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]}

                if not self._lyr_act_id_1 in action_dict:
                    show_layer_s_h_action = qgis.core.QgsAction(
                        self._lyr_act_id_1,
                        qgis.core.QgsAction.ActionType.GenericPython,  # int 1
                        'Select + Highlight',
                        "from LinearReferencing.map_tools.FeatureActions import edit_line_on_line_feature\nedit_line_on_line_feature([%@id%],'[%@layer_id%]',False)",
                        ':icons/mIconSelected.svg',
                        False,
                        '',
                        {'Feature'},
                        ''
                    )
                    self.ds.showLyr.actions().addAction(show_layer_s_h_action)
                if not self._lyr_act_id_2 in action_dict:
                    show_layer_s_h_p_action = qgis.core.QgsAction(
                        self._lyr_act_id_2,
                        qgis.core.QgsAction.ActionType.GenericPython,  # int 1
                        'Select + Highlight + Pan',
                        "from LinearReferencing.map_tools.FeatureActions import edit_line_on_line_feature\nedit_line_on_line_feature([%@id%],'[%@layer_id%]',True)",
                        ':icons/mActionPanToSelected.svg',
                        False,
                        '',
                        {'Feature'},
                        ''
                    )
                    self.ds.showLyr.actions().addAction(show_layer_s_h_p_action)

            atc = self.ds.showLyr.attributeTableConfig()
            if not atc.actionWidgetVisible():
                # qgis.core.QgsAttributeTableConfig.ButtonList / qgis.core.QgsAttributeTableConfig.DropDown
                atc.setActionWidgetStyle(qgis.core.QgsAttributeTableConfig.ButtonList)
                atc.setActionWidgetVisible(True)
                self.ds.showLyr.setAttributeTableConfig(atc)

            # tricky: get all associated opened attribute-tables for this Layer and refresh their contents to show the new actions
            attribute_table_widgets = [widget for widget in QtWidgets.QApplication.instance().allWidgets() if isinstance(widget, QtWidgets.QDialog) and widget.objectName() == f"QgsAttributeTableDialog/{self.ds.showLyr.id()}"]

            for at_wdg in attribute_table_widgets:
                reload_action = at_wdg.findChild(QtWidgets.QAction, 'mActionReload')
                if reload_action:
                    reload_action.trigger()

    def show_map_coords_in_dialogue(self, point: qgis.core.QgsPointXY):
        """shows the point-coords (transformed cursor-position) in dialogue
        :param point:
        """
        # Rev. 2023-05-08
        # round the values with num_digits, dependend from the projection
        str_map_x = '{:.{prec}f}'.format(point.x(), prec=self.rs.num_digits)
        str_map_y = '{:.{prec}f}'.format(point.y(), prec=self.rs.num_digits)
        self.my_dialogue.le_map_x.setText(str_map_x)
        self.my_dialogue.le_map_y.setText(str_map_y)

    def dlg_refresh_distance(self, ref_fid: int, measure_from: float, measure_to: float):
        """shows distance  = measure_to - measure_from in DoubleSpinBox
        :param ref_fid: fid of referenced line
        :param measure_from: from-distance to start-point of referenced line
        :param measure_to: to-distance to start-point of referenced line
        """
        # Rev. 2023-05-08
        self.my_dialogue.dspbx_distance.clear()
        ref_feature = self.ds.refLyr.getFeature(ref_fid)

        if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
            point_from_geom = ref_feature.geometry().interpolate(measure_from)
            point_to_geom = ref_feature.geometry().interpolate(measure_to)

            if point_from_geom and point_to_geom:
                with QtCore.QSignalBlocker(self.my_dialogue.dspbx_distance):
                    self.my_dialogue.dspbx_distance.setValue(measure_to - measure_from)
                    self.my_dialogue.dspbx_distance.setRange(0, ref_feature.geometry().length())

    def canvasMoveEvent(self, event: qgis.gui.QgsMapMouseEvent) -> None:
        """reimplemented: MouseMove on canvas
        further action depending on rs.tool_mode
        :param event:
        """
        # Rev. 2023-05-08
        # always show cursor-map-coords
        point_xy = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(event.x(), event.y())
        self.show_map_coords_in_dialogue(point_xy)

        if self.rs.tool_mode == 'move_segment':
            if self.rs.snapped_ref_fid is not None:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)

                ref_projected_point_geom = qgis.core.QgsGeometry.fromPointXY(point_xy)
                ref_projected_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))

                # see https://qgis.org/pyqgis/master/core/QgsGeometry.html#qgis.core.QgsGeometry.closestSegmentWithContext
                # returns tuple: (sqrDist, minDistPoint, nextVertexIndex, leftOrRightOfSegment)
                point_on_line = ref_feature.geometry().closestSegmentWithContext(ref_projected_point_geom.asPoint())
                sqr_dist = point_on_line[0]
                # <0 left, >0 right, ==0 on the line
                side = point_on_line[3]
                abs_dist = math.sqrt(sqr_dist)
                offset = abs_dist * side * -1

                current_measure = ref_feature.geometry().lineLocatePoint(qgis.core.QgsGeometry.fromPointXY(point_on_line[1]))

                delta = current_measure - self.rs.last_measure

                if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                    # change offset and measure
                    next_measure_from = self.rs.current_measure_from + delta
                    next_measure_to = self.rs.current_measure_to + delta
                    next_offset = offset
                elif QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                    # change offset, keep measure
                    next_measure_from = self.rs.current_measure_from
                    next_measure_to = self.rs.current_measure_to
                    next_offset = offset
                else:
                    # change measure, keep offset
                    next_measure_from = self.rs.current_measure_from + delta
                    next_measure_to = self.rs.current_measure_to + delta
                    next_offset = self.rs.current_offset

                self.rs.current_offset = next_offset

                # don't move beyond start/end of reference-line
                if next_measure_from >= 0 and next_measure_from <= ref_feature.geometry().length() and next_measure_to >= 0 and next_measure_to <= ref_feature.geometry().length():
                    self.rs.current_measure_from = next_measure_from
                    self.rs.current_measure_to = next_measure_to
                    self.rs.last_measure = current_measure

                self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                self.dlg_refresh_offset(self.rs.current_offset)
        elif self.rs.tool_mode == 'before_measure':
            # pre-reset dialog-widgets for cursor-coordinates, reference-ids and measures
            snap_filter = tools.MyToolFunctions.OneLayerFilter(self.ds.refLyr)

            m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
            self.snap_indicator.setMatch(m)

            if self.snap_indicator.match().type():
                snapped_ref_fid = m.featureId()
                self.my_dialogue.qcbn_snapped_ref_fid.select_by_value(0, 256, snapped_ref_fid)

                ref_feature = self.ds.refLyr.getFeature(snapped_ref_fid)

                # temporary highlight line under cursor
                self.rb_ref.setToGeometry(ref_feature.geometry(), self.ds.refLyr)
                self.rb_ref.show()

                # show snap-coords
                snapped_point_xy = self.snap_indicator.match().point()
                snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))
                measure = ref_feature.geometry().lineLocatePoint(snapped_point_geom)

                self.dlg_refresh_measure_from(snapped_ref_fid, measure)
        elif self.rs.tool_mode == 'measuring':
            if self.rs.snapped_ref_fid is not None and self.rs.current_measure_from is not None:
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)

                if self.snap_indicator.match().type():
                    # == self.rs.snapped_ref_fid
                    # snapped_ref_fid = m.featureId()
                    ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                    snapped_point_xy = self.snap_indicator.match().point()
                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))

                    self.rs.current_measure_to = ref_feature.geometry().lineLocatePoint(snapped_point_geom)
                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)
        elif self.rs.tool_mode == 'move_from_point':
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)
                if self.snap_indicator.match().type():
                    snapped_point_xy = self.snap_indicator.match().point()
                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))
                    self.rs.current_measure_from = ref_feature.geometry().lineLocatePoint(snapped_point_geom)
                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.dlg_refresh_distance(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to)
        elif self.rs.tool_mode == 'move_to_point':
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)
                if self.snap_indicator.match().type():
                    snapped_point_xy = self.snap_indicator.match().point()
                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))
                    self.rs.current_measure_to = ref_feature.geometry().lineLocatePoint(snapped_point_geom)
                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
        elif self.rs.tool_mode == 'select_features':
            if self.rs.mouse_down_point:
                # draw selection-rectangle
                mouse_move_point = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(event.x(), event.y())
                geom = qgis.core.QgsGeometry.fromRect(qgis.core.QgsRectangle(self.rs.mouse_down_point, mouse_move_point))
                self.rb_selection_rect.setToGeometry(geom, None)
                self.rb_selection_rect.show()

    def dlg_refresh_offset(self, offset: float) -> None:
        """sets the offset-Spinbox
        :param offset:
        """
        # Rev. 2023-05-27
        with QtCore.QSignalBlocker(self.my_dialogue.dspbx_offset):
            self.my_dialogue.dspbx_offset.setValue(offset)

    def canvasReleaseEvent(self, event: qgis.gui.QgsMapMouseEvent) -> None:
        """reimplemented: mouseUp on canvas
       further action depending on rs.tool_mode
       :param event:
       """
        # Rev. 2023-05-08
        # qgis.core.QgsPointXY
        point_xy = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(event.x(), event.y())
        self.show_map_coords_in_dialogue(point_xy)

        if self.rs.tool_mode == 'move_segment':
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)

                ref_projected_point_geom = qgis.core.QgsGeometry.fromPointXY(point_xy)
                ref_projected_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))

                # see https://qgis.org/pyqgis/master/core/QgsGeometry.html#qgis.core.QgsGeometry.closestSegmentWithContext
                # returns tuple: (sqrDist, minDistPoint, nextVertexIndex, leftOrRightOfSegment)
                point_on_line = ref_feature.geometry().closestSegmentWithContext(ref_projected_point_geom.asPoint())
                sqr_dist = point_on_line[0]
                # <0 left, >0 right, ==0 on the line
                side = point_on_line[3]
                abs_dist = math.sqrt(sqr_dist)

                offset = abs_dist * side * -1

                current_measure = ref_feature.geometry().lineLocatePoint(qgis.core.QgsGeometry.fromPointXY(point_on_line[1]))

                delta = current_measure - self.rs.last_measure

                if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                    # change offset and measure
                    next_measure_from = self.rs.current_measure_from + delta
                    next_measure_to = self.rs.current_measure_to + delta
                    next_offset = offset
                elif QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                    # change offset, keep measure
                    next_measure_from = self.rs.current_measure_from
                    next_measure_to = self.rs.current_measure_to
                    next_offset = offset
                else:
                    # change measure, keep offset
                    next_measure_from = self.rs.current_measure_from + delta
                    next_measure_to = self.rs.current_measure_to + delta
                    next_offset = self.rs.current_offset

                if next_measure_from >= 0 and next_measure_from <= ref_feature.geometry().length() and next_measure_to >= 0 and next_measure_to <= ref_feature.geometry().length():
                    self.rs.current_offset = next_offset
                    self.rs.current_measure_from = next_measure_from
                    self.rs.current_measure_to = next_measure_to

                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)

            self.check_settings('before_move_segment')
        elif self.rs.tool_mode == 'measuring':
            self.snap_indicator.setVisible(False)
            if self.rs.snapped_ref_fid is not None and self.rs.current_measure_from is not None:
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)

                if self.snap_indicator.match().type():
                    snapped_ref_fid = m.featureId()
                    ref_feature = self.ds.refLyr.getFeature(snapped_ref_fid)

                    snapped_point_xy = self.snap_indicator.match().point()

                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))

                    self.rs.current_measure_to = ref_feature.geometry().lineLocatePoint(snapped_point_geom)

                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.check_settings('after_measure')
                    self.dlg_refresh_measure_section()
                    self.dlg_refresh_edit_section()
        elif self.rs.tool_mode == 'select_features':
            # end of selection
            self.rb_ref.hide()
            self.rb_segment.hide()
            self.vm_pt_measure_from.hide()
            self.vm_pt_measure_to.hide()
            if self.cf.show_layer_complete:
                self.ds.showLyr.removeSelection()

                if self.rs.mouse_down_point:
                    self.rs.mouse_up_point = point_xy
                    # mouse-down == mouse-up ➜ simple click, no rect...
                    if self.rs.mouse_up_point == self.rs.mouse_down_point:
                        # ...instead buffer with 1 percent of the current canvas-Extent
                        buffer_width = (self.iface.mapCanvas().extent().xMaximum() - self.iface.mapCanvas().extent().xMinimum()) * 0.01
                        buffer_height = (self.iface.mapCanvas().extent().yMaximum() - self.iface.mapCanvas().extent().yMinimum()) * 0.01
                        rect = qgis.core.QgsRectangle(self.rs.mouse_up_point.x() - buffer_width, self.rs.mouse_up_point.y() - buffer_height, self.rs.mouse_up_point.x() + buffer_width, self.rs.mouse_up_point.y() + buffer_height)
                    else:
                        rect = qgis.core.QgsRectangle(self.rs.mouse_down_point.x(), self.rs.mouse_down_point.y(), self.rs.mouse_up_point.x(), self.rs.mouse_up_point.y())

                    tr = qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.showLyr.crs(), qgis.core.QgsProject.instance())
                    projected_rect = tr.transformBoundingBox(rect)

                    request = qgis.core.QgsFeatureRequest()
                    request.setFilterRect(projected_rect)
                    request.setFlags(qgis.core.QgsFeatureRequest.ExactIntersect)

                    new_selected_pks = []
                    for feature in self.ds.showLyr.getFeatures(request):
                        pk = feature[self.ds.dataLyrIdField.name()]
                        new_selected_pks.append(pk)

                    if len(new_selected_pks) > 0:
                        # like implemented in QGis-Select-Features:
                        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                            # remove from Selection
                            for new_pk in new_selected_pks:
                                if new_pk in self.rs.selected_pks:
                                    self.rs.selected_pks.remove(new_pk)
                        elif QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                            # add to selection
                            for new_pk in new_selected_pks:
                                self.rs.selected_pks.append(new_pk)
                        else:
                            # replace selection
                            self.rs.selected_pks = new_selected_pks

                        # make unique
                        self.rs.selected_pks = list(dict.fromkeys(self.rs.selected_pks))

                        # validate self.rs.selected_pks and select features:
                        data_fids = []
                        show_fids = []
                        for edit_pk in self.rs.selected_pks:
                            data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
                            if data_feature:
                                data_fids.append(data_feature.id())

                            show_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.showLyr, self.ds.showLyrBackReferenceField, edit_pk)
                            if show_feature and show_feature.isValid():
                                show_fids.append(show_feature.id())
                        self.ds.showLyr.removeSelection()
                        self.ds.showLyr.select(show_fids)
                        self.ds.dataLyr.removeSelection()
                        self.ds.dataLyr.select(data_fids)

            else:
                self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "Missing requirements: No Show-Layer configured, check Line-on-Line-settings..."))
                self.my_dialogue.tbw_central.setCurrentIndex(1)

            self.rb_selection_rect.hide()
            self.rs.mouse_down_point = None
            self.rs.mouse_up_point = None
            self.dlg_refresh_feature_selection_section()
        elif self.rs.tool_mode == 'move_from_point':
            self.snap_indicator.setVisible(False)
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)
                if self.snap_indicator.match().type():
                    snapped_point_xy = self.snap_indicator.match().point()
                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))
                    self.rs.current_measure_from = ref_feature.geometry().lineLocatePoint(snapped_point_geom)
                    self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)

            self.check_settings('before_move_from_point')

        elif self.rs.tool_mode == 'move_to_point':
            self.snap_indicator.setVisible(False)
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)
                if self.snap_indicator.match().type():
                    snapped_point_xy = self.snap_indicator.match().point()
                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))
                    self.rs.current_measure_to = ref_feature.geometry().lineLocatePoint(snapped_point_geom)
                    self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)

            self.check_settings('before_move_to_point')

    def canvasPressEvent(self, event: qgis.gui.QgsMapMouseEvent) -> None:
        """reimplemented: mouseDown on canvas
        further action depending on rs.tool_mode
        :param event:
        """
        # Rev. 2023-05-08
        # qgis.core.QgsPointXY
        point_xy = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(event.x(), event.y())

        if self.rs.tool_mode == 'before_move_segment':
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                ref_projected_point_geom = qgis.core.QgsGeometry.fromPointXY(point_xy)
                ref_projected_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))

                # see https://qgis.org/pyqgis/master/core/QgsGeometry.html#qgis.core.QgsGeometry.closestSegmentWithContext
                # returns tuple: (sqrDist, minDistPoint, nextVertexIndex, leftOrRightOfSegment)
                point_on_line = ref_feature.geometry().closestSegmentWithContext(ref_projected_point_geom.asPoint())
                current_measure = ref_feature.geometry().lineLocatePoint(qgis.core.QgsGeometry.fromPointXY(point_on_line[1]))
                self.rs.last_measure = current_measure
                self.check_settings('move_segment')

        elif self.rs.tool_mode == 'before_measure':
            snap_filter = tools.MyToolFunctions.OneLayerFilter(self.ds.refLyr)

            m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)

            if self.snap_indicator.match().type():
                snapped_point_xy = self.snap_indicator.match().point()
                snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))

                snapped_ref_fid = m.featureId()
                ref_feature = self.ds.refLyr.getFeature(snapped_ref_fid)
                snapped_ref_geom = ref_feature.geometry()
                self.rs.snapped_ref_fid = ref_feature.id()
                self.my_dialogue.qcbn_snapped_ref_fid.select_by_value(0, 256, self.rs.snapped_ref_fid)
                self.rs.current_measure_from = snapped_ref_geom.lineLocatePoint(snapped_point_geom)
                self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                self.check_settings('measuring')
        elif self.rs.tool_mode == 'before_move_from_point':
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)
                if self.snap_indicator.match().type():
                    snapped_point_xy = self.snap_indicator.match().point()
                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))
                    self.rs.current_measure_from = ref_feature.geometry().lineLocatePoint(snapped_point_geom)
                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.draw_from_point(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.dlg_refresh_measure_from(self.rs.snapped_ref_fid, self.rs.current_measure_from)
                    self.check_settings('move_from_point')
        elif self.rs.tool_mode == 'before_move_to_point':
            if self.cf.measure_completed:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                snap_filter = tools.MyToolFunctions.OneFeatureFilter(self.ds.refLyr, self.rs.snapped_ref_fid)
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)
                if self.snap_indicator.match().type():
                    snapped_point_xy = self.snap_indicator.match().point()
                    snapped_point_geom = qgis.core.QgsGeometry.fromPointXY(snapped_point_xy)
                    snapped_point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.ds.refLyr.crs(), qgis.core.QgsProject.instance()))
                    self.rs.current_measure_to = ref_feature.geometry().lineLocatePoint(snapped_point_geom)
                    self.draw_segment(self.rs.snapped_ref_fid, self.rs.current_measure_from, self.rs.current_measure_to, self.rs.current_offset)
                    self.draw_to_point(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.dlg_refresh_measure_to(self.rs.snapped_ref_fid, self.rs.current_measure_to)
                    self.check_settings('move_to_point')

        elif self.rs.tool_mode == 'show_re_digitized_feature':
            pass
        elif self.rs.tool_mode == 'after_measure':
            self.resume_measure()
        elif self.rs.tool_mode == 'select_features':
            # click on single feature or start of selection-rectangle?
            # see canvasReleaseEvent

            if event.button() == QtCore.Qt.LeftButton:
                self.rs.mouse_up_point = None
                self.rs.mouse_down_point = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(event.x(), event.y())

    def s_create_data_layer(self):
        """create a GeoPackage-"layer" (geometry-less) for storing the linear-references"""
        # Rev. 2023-05-08
        try_it = True
        critical_msg = ''
        success_msg = ''
        info_msg = ''
        warning_msg = ''

        # self.ds.refLyrPkField, necessary because the type of the created reference-field must fit to the referenced primary-key-field
        if self.cf.reference_layer_complete:
            # file-dialog for the GeoPackage
            dialog = QtWidgets.QFileDialog()
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
            dialog.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, True)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
            dialog.setNameFilter("geoPackage (*.gpkg)")
            dialog.setWindowTitle(QtCore.QCoreApplication.translate('LolEvt', "LinearReferencing: Select or create GeoPackage for Line-on-Line-Layer"))
            dialog.setDefaultSuffix("gpkg")
            result = dialog.exec()
            filenames = dialog.selectedFiles()

            if result:

                gpkg_path = filenames[0]
                # only three necessary fields
                data_lyr_fid_field = qgis.core.QgsField("fid", QtCore.QVariant.Int)

                # same type as referenced PK-Field:
                data_lyr_reference_field = qgis.core.QgsField("line_ref_id", self.ds.refLyrPkField.type())

                data_lyr_measure_from_field = qgis.core.QgsField("measure_from", QtCore.QVariant.Double)
                data_lyr_measure_to_field = qgis.core.QgsField("measure_to", QtCore.QVariant.Double)
                data_lyr_offset_field = qgis.core.QgsField("offset", QtCore.QVariant.Double)

                fields = qgis.core.QgsFields()
                fields.append(data_lyr_fid_field)
                fields.append(data_lyr_reference_field)
                fields.append(data_lyr_measure_from_field)
                fields.append(data_lyr_measure_to_field)
                fields.append(data_lyr_offset_field)

                options = qgis.core.QgsVectorFileWriter.SaveVectorOptions()

                options.driverName = "gpkg"

                # already used names in project...
                used_layer_names = [layer.name() for layer_id, layer in qgis.core.QgsProject.instance().mapLayers().items()]

                if os.path.isfile(gpkg_path):
                    # ... and existing GeoPackage
                    used_layer_names += [lyr.GetName() for lyr in osgeo.ogr.Open(gpkg_path)]
                    options.actionOnExistingFile = qgis.core.QgsVectorFileWriter.CreateOrOverwriteLayer

                # unique name for the table/layer within project and GeoPackage:
                table_name = tools.MyToolFunctions.get_unique_layer_name(used_layer_names, 'LineOnLine_Data_Layer_{curr_i}', '1')

                table_name, ok = QtWidgets.QInputDialog.getText(None, f"LinearReferencing ({gdp()})", QtCore.QCoreApplication.translate('LolEvt', "Name for table in GeoPackage:"), QtWidgets.QLineEdit.Normal, table_name)
                if not ok or not table_name:
                    info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user")
                elif table_name in used_layer_names:

                    dialog_result = QtWidgets.QMessageBox.question(
                        None,
                        "LinearReferencing",
                        qt_format(QtCore.QCoreApplication.translate('LolEvt', "Replace existing table {apos}{0}{apos} in GeoPackage {apos}{1}{apos}?"), table_name, gpkg_path),
                        buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                        defaultButton=QtWidgets.QMessageBox.Yes
                    )

                    if dialog_result != QtWidgets.QMessageBox.Yes:
                        info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user")
                        try_it = False

                if try_it:
                    options.layerName = table_name
                    # geometry-less table needs anyway three Dummy-Attributes for geometrie-type, projection and transformation
                    writer = qgis.core.QgsVectorFileWriter.create(
                        gpkg_path,
                        fields,
                        qgis.core.QgsWkbTypes.NoGeometry,
                        qgis.core.QgsCoordinateReferenceSystem(""),  # dummy
                        qgis.core.QgsCoordinateTransformContext(),
                        options
                    )
                    # creates a SQLite/SpatialLite-table with such query:
                    # CREATE TABLE "LR_Points_Data_25" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "reference_id" INTEGER, "measure" REAL)
                    if writer.hasError() == qgis.core.QgsVectorFileWriter.NoError:
                        # Important:
                        # "del writer" *before* "addVectorLayer"
                        # seems to be is necessary
                        # else layer is not valid
                        # perhaps layer is physically created after "del writer"?
                        del writer

                        uri = gpkg_path + '|layername=' + table_name
                        data_lyr = self.iface.addVectorLayer(uri, table_name, "ogr")

                        if data_lyr and data_lyr.isValid():
                            # very unfortunately: constraints only affects the form, edits in the table ar not affected and must be checked by provider
                            data_lyr.setFieldConstraint(0, qgis.core.QgsFieldConstraints.Constraint.ConstraintUnique)
                            data_lyr.setFieldConstraint(0, qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                            data_lyr.setFieldConstraint(1, qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                            data_lyr.setFieldConstraint(2, qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                            data_lyr.setFieldConstraint(3, qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                            data_lyr.setFieldConstraint(4, qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)

                            # data_lyr.updateFields()

                            # data_lyr.reload()

                            self.ss.dataLyrId = data_lyr.id()
                            self.ss.dataLyrIdFieldName = data_lyr_fid_field.name()
                            self.ss.dataLyrReferenceFieldName = data_lyr_reference_field.name()
                            self.ss.dataLyrMeasureFromFieldName = data_lyr_measure_from_field.name()
                            self.ss.dataLyrMeasureToFieldName = data_lyr_measure_to_field.name()
                            self.ss.dataLyrOffsetFieldName = data_lyr_offset_field.name()

                            self.connect_data_layer(data_lyr)
                            self.check_settings()
                            self.dlg_refresh_layer_settings_section()
                            self.dlg_refresh_feature_selection_section()
                            self.resume_measure()
                            success_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Table {apos}{0}{apos}.{apos}{1}{apos} successfully created"), gpkg_path, table_name)
                        else:
                            # if for example the GeoPackage is exclusively accessed by "DB Browser for SQLite"...
                            critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Error creating Data-Layer {apos}{0}{apos}.{apos}{1}{apos}, created layer not valid"), gpkg_path, table_name)

                    else:
                        # perhaps write-permission?
                        critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Error creating Data-Layer {apos}{0}{apos}.{apos}{1}{apos}: {2}"), gpkg_path, table_name, writer.errorMessage())
        else:
            critical_msg = QtCore.QCoreApplication.translate('LolEvt', "missing requirements, Reference-Layer incomplete, check Line-on-Line-settings...")
            self.my_dialogue.tbw_central.setCurrentIndex(1)

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def s_create_show_layer(self):
        """create a virtual layer combining the Data-Layer and the Reference-Layer"""
        # Rev. 2023-05-08
        critical_msg = ''
        success_msg = ''
        info_msg = ''
        warning_msg = ''

        if self.cf.reference_layer_complete and self.cf.data_layer_complete:

            layer_names = [layer.name() for layer in qgis.core.QgsProject.instance().mapLayers().values()]
            layer_name = tools.MyToolFunctions.get_unique_layer_name(layer_names, "LineOnLine_Show_Layer_{curr_i}", '1')

            # unique name for the  virtual layer within project

            layer_name, ok = QtWidgets.QInputDialog.getText(None, f"LinearReferencing ({gdp()})", QtCore.QCoreApplication.translate('LolEvt', "Name for virtual Show-Layer:"), QtWidgets.QLineEdit.Normal, layer_name)
            if ok and layer_name:
                show_lyr_sql = "SELECT"
                field_sql_lst = []

                # only the necessary attributes of Data-Layer are included, the other come via join, reuse the original field-names as aliases
                field_sql_lst.append(f" data_lyr.{self.ds.dataLyrIdField.name()} as \"{self.ds.dataLyrIdField.name()}\"")
                field_sql_lst.append(f" data_lyr.{self.ds.dataLyrReferenceField.name()} as \"{self.ds.dataLyrReferenceField.name()}\"")
                field_sql_lst.append(f" data_lyr.{self.ds.dataLyrMeasureFromField.name()} as \"{self.ds.dataLyrMeasureFromField.name()}\"")
                field_sql_lst.append(f" data_lyr.{self.ds.dataLyrMeasureToField.name()} as \"{self.ds.dataLyrMeasureToField.name()}\"")
                field_sql_lst.append(f" data_lyr.{self.ds.dataLyrOffsetField.name()} as \"{self.ds.dataLyrOffsetField.name()}\"")
                # no refLyr-fields in query, solved via Table-Join

                # Problem/Bug only under windows:
                # if dataLyr has no records ➜ show_lyr.renderer() == None
                # Workaround:
                # Geometry-Expression with "special comment" according https://docs.qgis.org/testing/en/docs/user_manual/managing_data_source/create_layers.html#creating-virtual-layers

                # Bug 2 (only in Windows!):
                # offset == 0 ➜ no result
                # therefore a more complex query:
                no_offset = f"data_lyr.\"{self.ds.dataLyrOffsetField.name()}\" is null or data_lyr.\"{self.ds.dataLyrOffsetField.name()}\" = 0"
                geom_without_offset = f"ST_Line_Substring(ref_lyr.geometry, min(data_lyr.\"{self.ds.dataLyrMeasureFromField.name()}\",data_lyr.\"{self.ds.dataLyrMeasureToField.name()}\")/st_length(ref_lyr.geometry),max(data_lyr.\"{self.ss.dataLyrMeasureFromFieldName}\",data_lyr.\"{self.ss.dataLyrMeasureToFieldName}\")/st_length(ref_lyr.geometry))"
                geom_with_offset = f"ST_OffsetCurve(ST_Line_Substring(ref_lyr.geometry, min(data_lyr.\"{self.ds.dataLyrMeasureFromField.name()}\",data_lyr.\"{self.ds.dataLyrMeasureToField.name()}\")/st_length(ref_lyr.geometry),max(data_lyr.\"{self.ds.dataLyrMeasureFromField.name()}\",data_lyr.\"{self.ds.dataLyrMeasureToField.name()}\")/st_length(ref_lyr.geometry)),data_lyr.\"{self.ds.dataLyrOffsetField.name()}\")"

                field_sql_lst.append(f" CASE WHEN {no_offset} THEN {geom_without_offset} ELSE {geom_with_offset} END as line_geom /*:linestring:{self.ds.refLyr.crs().postgisSrid()}*/")

                # field_sql_lst.append(f" {geom_with_offset} as line_geom /*:linestring:{self.ds.refLyr.crs().postgisSrid()}*/")

                show_lyr_sql += ',\n'.join(field_sql_lst)
                show_lyr_sql += f"\nFROM  \"{self.ds.dataLyr.id()}\" as data_lyr"
                show_lyr_sql += f"\n  INNER JOIN \"{self.ds.refLyr.id()}\" as ref_lyr"
                integer_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong]
                if self.ds.dataLyrReferenceField.type() in integer_field_types:
                    show_lyr_sql += f" ON data_lyr.\"{self.ds.dataLyrReferenceField.name()}\" = ref_lyr.\"{self.ds.refLyrPkField.name()}\""
                else:
                    # needed with non-integer join-fields,
                    # makes the query/layer *very* slow, presumably because of missing indexes?
                    # ➜ better avoid non-integer PKs
                    show_lyr_sql += f" ON (data_lyr.\"{self.ds.dataLyrReferenceField.name()}\" = ref_lyr.\"{self.ds.refLyrPkField.name()}\") = True"

                # urllib.parse.quote? https://docs.python.org/3/library/urllib.parse.html
                # Perhaps not necessary, but "iface.activeLayer().dataProvider().uri().uri()"
                # show_lyr_sql_q = urllib.parse.quote(show_lyr_sql)

                uri = f"?query={show_lyr_sql}"

                # set uid-Field for virtual Layer via "&uid="
                # only for integer-PKs
                # advantage: no artificial fid used, feature.id() returns this value
                # if the Name of a string-PK would be used for that param
                # ➜ no error
                # ➜ the layer will show in canvas
                # ➜ but the associated table has only *one* record
                if self.ds.dataLyrIdField.type() in integer_field_types:
                    uri += f"&uid={self.ds.dataLyrIdField.name()}"

                # &geometry=alias used in show_lyr_sql
                # :2: ➜ :linestring:
                # {epsg} ➜ same as Reference-Layer
                # anyway:
                # under windows:
                # the "Virtual Layer Dialog shows for "Geometry" allways "Autodetect" instead "Manually defined", so the whole
                # "&geometry=point_geom:linestring:25832"-part seems to be ignored
                uri += f"&geometry=line_geom:2:{self.ds.refLyr.crs().postgisSrid()}"

                show_lyr = qgis.core.QgsVectorLayer(uri, layer_name, "virtual")

                if show_lyr and show_lyr.renderer():
                    qvl_join_data_lyr = qgis.core.QgsVectorLayerJoinInfo()
                    qvl_join_data_lyr.setJoinLayer(self.ds.dataLyr)
                    qvl_join_data_lyr.setJoinFieldName(self.ds.dataLyrIdField.name())
                    qvl_join_data_lyr.setTargetFieldName(self.ds.dataLyrIdField.name())
                    qvl_join_data_lyr.setUsingMemoryCache(True)
                    show_lyr.addJoin(qvl_join_data_lyr)

                    qvl_join_ref_lyr = qgis.core.QgsVectorLayerJoinInfo()
                    qvl_join_ref_lyr.setJoinLayer(self.ds.refLyr)
                    qvl_join_ref_lyr.setJoinFieldName(self.ds.refLyrPkField.name())
                    qvl_join_ref_lyr.setTargetFieldName(self.ds.dataLyrReferenceField.name())
                    qvl_join_ref_lyr.setUsingMemoryCache(True)
                    show_lyr.addJoin(qvl_join_ref_lyr)

                    atc = show_lyr.attributeTableConfig()

                    # remove duplicates, these fields are almost queried in virtual-layer-uri
                    hide_field_names = [
                        f"{self.ds.dataLyr.name()}_{self.ds.dataLyrIdField.name()}",
                        f"{self.ds.dataLyr.name()}_{self.ds.dataLyrReferenceField.name()}",
                        f"{self.ds.dataLyr.name()}_{self.ds.dataLyrMeasureFromField.name()}",
                        f"{self.ds.dataLyr.name()}_{self.ds.dataLyrMeasureToField.name()}",
                        f"{self.ds.dataLyr.name()}_{self.ds.dataLyrOffsetField.name()}"
                    ]

                    columns = atc.columns()
                    for column in columns:
                        if column.name in hide_field_names:
                            column.hidden = True

                    atc.setColumns(columns)

                    show_lyr.setAttributeTableConfig(atc)

                    show_lyr.renderer().symbol().setWidthUnit(qgis.core.QgsUnitTypes.RenderUnit.RenderPixels)
                    show_lyr.renderer().symbol().setWidth(6)
                    show_lyr.renderer().symbol().setColor(QtGui.QColor("orange"))
                    show_lyr.renderer().symbol().setOpacity(0.8)

                    show_lyr.setCrs(self.ds.refLyr.crs())
                    show_lyr.updateExtents()

                    qgis.core.QgsProject.instance().addMapLayer(show_lyr)

                    self.ss.showLyrId = show_lyr.id()
                    # queried with the same fieldname
                    self.ss.showLyrBackReferenceFieldName = self.ds.dataLyrIdField.name()
                    self.connect_show_layer(show_lyr)
                    self.check_settings()
                    self.dlg_refresh_layer_settings_section()
                    self.dlg_refresh_feature_selection_section()
                    self.resume_measure()

                    success_msg = QtCore.QCoreApplication.translate('LolEvt', "Virtual Show-Layer created and added...")
                else:
                    critical_msg = QtCore.QCoreApplication.translate('LolEvt', "Error creating virtual Show-Layer...")


            else:
                success_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user")
        else:
            critical_msg = QtCore.QCoreApplication.translate('LolEvt', "Please create or configure Reference- and Data-Layer")

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def s_move_from_point(self):
        """toggle tool-mode for setting From-Point
        :param checked: checked-status of checkable button for toggle
        """
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            self.check_settings('before_move_from_point')
            self.iface.mapCanvas().setMapTool(self)
            self.dlg_refresh_measure_section()
        else:
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "No completed measure yet..."))

    def s_move_segment(self, checked: bool):
        """toggle tool-mode for change measures/offset of current segment interactive on canvas
        :param checked: checked-status of checkable button for toggle
        """
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            if checked:
                self.check_settings('before_move_segment')
            else:
                self.check_settings('after_measure')
            self.iface.mapCanvas().setMapTool(self)
            self.dlg_refresh_measure_section()
        else:
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "No completed measure yet..."))

    def s_move_to_point(self):
        """toggle tool-mode for setting To-Point"""
        # Rev. 2023-05-08
        if self.cf.measure_completed:
            self.check_settings('before_move_to_point')
            self.iface.mapCanvas().setMapTool(self)
            self.dlg_refresh_measure_section()
        else:
            self.push_messages(warning_msg=QtCore.QCoreApplication.translate('LolEvt', "No completed measure yet..."))

    def s_resume_measure(self):
        """slot for resume_measure"""
        # Rev. 2023-05-26
        self.resume_measure()

    def resume_measure(self):
        """reset runtime-settings and dialogue, hide temporal canvas-graphics, set rs.tool_mode and refresh status_bar"""
        # Rev. 2023-04-29
        self.rs.current_measure_from = None
        self.rs.current_measure_to = None
        self.rs.snapped_ref_fid = None
        self.vm_pt_measure_from.hide()
        self.vm_pt_measure_to.hide()
        self.rb_ref.hide()
        self.rb_segment.hide()
        self.check_settings('before_measure')
        self.dlg_refresh_measure_section()
        self.dlg_refresh_edit_section()
        self.my_dialogue.reset_measure_widgets()
        self.iface.mapCanvas().setMapTool(self)

    def s_delete_feature(self):
        """deletes the current selected data-feature after confirmation"""
        # Rev. 2023-04-27
        try_it = True
        did_it = True
        critical_msg = ''
        success_msg = ''
        info_msg = ''
        warning_msg = ''
        if self.rs.edit_pk is not None:
            if self.cf.delete_enabled:
                if self.check_data_feature(self.rs.edit_pk):
                    if self.ds.dataLyr.isEditable():
                        if self.ds.dataLyr.isModified():
                            dialog_result = QtWidgets.QMessageBox.question(
                                None,
                                f"LinearReferencing Update Feature ({gdp()})",
                                qt_format(QtCore.QCoreApplication.translate('LolEvt', "{div_pre_1}Layer {apos}{0}{apos} is editable!{div_ml_1}[Yes]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} End edit session with save{br}[No]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} End edit session without save{br}[Cancel]{nbsp}{arrow} Quit...{div_ml_2}{div_pre_2}"), self.ds.dataLyr.name()),
                                buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                defaultButton=QtWidgets.QMessageBox.Yes
                            )

                            if dialog_result == QtWidgets.QMessageBox.Yes:
                                self.ds.dataLyr.commitChanges()
                            elif dialog_result == QtWidgets.QMessageBox.No:
                                self.ds.dataLyr.rollBack()
                            else:
                                try_it &= False
                                did_it = False
                                info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")
                        else:
                            self.ds.dataLyr.rollBack()

                    if try_it:
                        self.ds.dataLyr.startEditing()
                        dialog_result = QtWidgets.QMessageBox.question(
                            None,
                            f"LinearReferencing ({gdp()})",
                            qt_format(QtCore.QCoreApplication.translate('LolEvt', "Delete feature with id {apos}{0}{apos} from Data-Layer {apos}{1}{apos}?"), self.rs.edit_pk, self.ds.dataLyr.name()),
                            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                            defaultButton=QtWidgets.QMessageBox.Yes
                        )

                        if dialog_result == QtWidgets.QMessageBox.Yes:
                            try:
                                self.ds.dataLyr.deleteFeatures([self.rs.edit_pk])
                                commit_result = self.ds.dataLyr.commitChanges()
                                if commit_result:
                                    did_it = True
                                    success_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Feature with ID {apos}{0}{apos} successfully deleted in Data-Layer {apos}{1}{apos}..."), self.rs.edit_pk, self.ds.dataLyr.name())
                                else:
                                    self.ds.dataLyr.rollBack()
                                    did_it = False
                                    critical_msg = str(self.ds.dataLyr.commitErrors())

                                if self.rs.edit_pk in self.rs.selected_pks:
                                    self.rs.selected_pks.remove(self.rs.edit_pk)

                                self.rs.edit_pk = None
                            except Exception as err:
                                self.ds.dataLyr.rollBack()
                                did_it = False
                                critical_msg = f"Exception '{err.__class__.__name__}' in {gdp()}: {err}"
                        else:
                            self.ds.dataLyr.rollBack()
                            did_it = False
                            info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")
                else:
                    did_it = False
                    warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Delete feature failed, no feature {apos}{0}{apos} in Data-Layer {apos}{1}{apos}..."), self.rs.edit_pk, self.ds.dataLyr.name())
            else:
                did_it = False
                critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Update feature failed, missing privileges in Data-Layer {apos}{0}{apos}..."), self.ds.dataLyr.name())

        if did_it:
            if self.cf.show_layer_complete:
                if self.iface.mapCanvas().isCachingEnabled():
                    self.ds.showLyr.triggerRepaint()
                else:
                    self.iface.mapCanvas().refresh()

            self.resume_measure()

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def s_insert_feature(self):
        """opens insert from with some prefilled contents, from which a new can be inserted to Data-Layer"""
        # Rev. 2023-04-28
        try_it = True
        did_it = False
        success_msg = ''
        info_msg = ''
        critical_msg = ''
        warning_msg = ''

        used_pk = None

        if self.cf.insert_enabled:
            if self.ds.dataLyr.isEditable():
                if self.ds.dataLyr.isModified():
                    dialog_result = QtWidgets.QMessageBox.question(
                        None,
                        f"LinearReferencing Add Feature ({gdp()})",
                        qt_format(QtCore.QCoreApplication.translate('LolEvt', "{div_pre_1}Layer {apos}{0}{apos} is editable!{div_ml_1}[Yes]{nbsp}{nbsp}{nbsp}{nbsp}{arrow} End edit session with save{br}[No]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} End edit session without save{br}[Cancel]{arrow} Quit...{div_ml_2}{div_pre_2}"), self.ds.dataLyr.name()),
                        buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                        defaultButton=QtWidgets.QMessageBox.Yes
                    )

                    if dialog_result == QtWidgets.QMessageBox.Yes:
                        self.ds.dataLyr.commitChanges()
                    elif dialog_result == QtWidgets.QMessageBox.No:
                        self.ds.dataLyr.rollBack()
                    else:
                        try_it = False
                        info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")
                else:
                    self.ds.dataLyr.rollBack()

            if try_it:
                # Pre-Check the referenced Feature
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)

                if ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                    ref_layer_join_value = ref_feature[self.ds.refLyrPkField.name()]
                    # check, if there is a valuable ID, because self.ds.refLyrPkField can be any field in this layer
                    if ref_layer_join_value == '' or ref_layer_join_value is None or repr(ref_layer_join_value) == 'NULL':
                        critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Feature with ID {apos}{0}{apos} in Reference-Layer {apos}{1}{apos} has no value in ID-field {apos}{2}{apos}"), self.rs.snapped_ref_fid, self.ds.refLyr.name(), self.ds.refLyrPkField.name())
                        try_it &= False
                else:
                    critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "No feature with ID {apos}{0}{apos} in Reference-Layer {apos}{1}{apos}"), self.rs.snapped_ref_fid, self.ds.refLyr.name())
                    try_it &= False

                if try_it:
                    data_feature = qgis.core.QgsFeature()
                    data_feature.setFields(self.ds.dataLyr.dataProvider().fields())
                    data_feature[self.ds.dataLyrReferenceField.name()] = ref_layer_join_value

                    # if self.ds.refLyr.crs().isGeographic():
                    #     measure_from = round(self.rs.current_measure_from, 6)
                    #     measure_to = round(self.rs.current_measure_to, 6)
                    #     offset = round(self.rs.current_offset, 6)
                    # else:
                    #     measure_from = round(self.rs.current_measure_from, 2)
                    #     measure_to = round(self.rs.current_measure_to, 2)
                    #     offset = round(self.rs.current_offset, 2)

                    data_feature[self.ds.dataLyrMeasureFromField.name()] = self.rs.current_measure_from
                    data_feature[self.ds.dataLyrMeasureToField.name()] = self.rs.current_measure_to
                    data_feature[self.ds.dataLyrOffsetField.name()] = self.rs.current_offset
                    integer_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong]
                    if self.ds.dataLyrIdField.type() in integer_field_types:
                        # pre-fetch sequence-value for openFeatureForm for convenience
                        # normally integer-pk-Field declared as "INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL"
                        current_pks = qgis.core.QgsVectorLayerUtils.getValues(self.ds.dataLyr, self.ds.dataLyrIdField.name(), selectedOnly=False)[0]
                        if current_pks:
                            new_pk = max(current_pks) + 1
                        else:
                            new_pk = 1
                        data_feature[self.ds.dataLyrIdField.name()] = new_pk
                        # no convenience for string-PKs, but fortunately the FeatureForm checks the uniqueness

                    try:
                        self.ds.dataLyr.startEditing()
                        self.ds.dataLyr.addFeature(data_feature)
                        dlg_result = self.iface.openFeatureForm(self.ds.dataLyr, data_feature)
                        if dlg_result:
                            insert_ref_pk = data_feature[self.ds.dataLyrReferenceField.name()]
                            insert_measure_from = data_feature[self.ds.dataLyrMeasureFromField.name()]
                            insert_measure_to = data_feature[self.ds.dataLyrMeasureToField.name()]
                            ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, insert_ref_pk)

                            # User could have changed feature-data in dialog (PK, reference-id, measure)
                            # ➜ validity-check like "reference-id exists in refLyr?" "measure 0 ...referenced_line_length?"
                            if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():

                                if ref_feature.geometry().constGet().partCount() > 1:
                                    warning_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Linestring-Geometry {apos}{0}{apos} in Reference-Layer {apos}{1}{apos} is {2}-parted, Line-on-Line-feature not calculable"), insert_ref_pk, self.ds.refLyr.name(), ref_feature.geometry().constGet().partCount())

                                if insert_measure_from < 0 or insert_measure_from > ref_feature.geometry().length() or insert_measure_to < 0 or insert_measure_to > ref_feature.geometry().length():
                                    info_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "measure-values from {apos}{0}{apos} to {apos}{1}{apos} truncated to range 0 ... {2}"), insert_measure_from, insert_measure_to, ref_feature.geometry().length())
                                    data_feature[self.ds.dataLyrMeasureFromField.name()] = max(0, min(ref_feature.geometry().length(), insert_measure_from))
                                    data_feature[self.ds.dataLyrMeasureToField.name()] = max(0, min(ref_feature.geometry().length(), insert_measure_to))
                                    self.ds.dataLyr.updateFeature(data_feature)

                                # User could have changed feature-data in dialog (PK, reference-id, measure)
                                # but despite that no client-side validity-check like "reference-id exists in refLyr?" "measure 0 ...referenced_line_length?"
                                commit_result = self.ds.dataLyr.commitChanges()
                                if commit_result:
                                    used_pk = data_feature[self.ds.dataLyrIdField.name()]
                                    did_it = True
                                    success_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "New feature with ID {apos}{0}{apos} successfully added to Data-Layer {apos}{1}{apos}..."), used_pk, self.ds.dataLyr.name())
                                else:
                                    self.ds.dataLyr.rollBack()
                                    critical_msg = str(self.ds.dataLyr.commitErrors())
                            else:
                                self.ds.dataLyr.rollBack()
                                critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "No valid feature with PK {apos}{0}{apos} in Reference-Layer {apos}{1}{apos}..."), insert_ref_pk, self.ds.refLyr.name())
                        else:
                            self.ds.dataLyr.rollBack()
                            info_msg = QtCore.QCoreApplication.translate('LolEvt', "Canceled by user...")

                    except Exception as err:
                        self.ds.dataLyr.rollBack()
                        critical_msg = str(err)


        else:
            critical_msg = qt_format(QtCore.QCoreApplication.translate('LolEvt', "Add feature failed, missing privileges in Data-Layer {apos}{0}{apos}..."), self.ds.dataLyr.name())

        if did_it:
            if self.cf.show_layer_complete:
                self.ds.showLyr.updateExtents()
                if self.iface.mapCanvas().isCachingEnabled():
                    self.ds.showLyr.triggerRepaint()
                else:
                    self.iface.mapCanvas().refresh()
            self.set_edit_pk(used_pk, False)

        self.push_messages(success_msg, info_msg, warning_msg, critical_msg)

    def restore_settings(self):
        """reset all settings and try to restore self.ss from Project"""
        # Rev. 2023-04-27
        self.ss = self.StoredSettings()
        # read stored settings from project:
        # filter: startswith('_')
        # ➜ read and set "hidden" properties, not their property-setter/getter/deleter
        # and not callable(getattr(self.StoredSettings, prop))
        property_list = [prop for prop in dir(self.StoredSettings) if prop.startswith('_') and not prop.startswith('__')]

        for prop_name in property_list:
            key = f"/LolEvt/{prop_name}"
            restored_value, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', key)
            if restored_value and type_conversion_ok:
                setattr(self.ss, prop_name, restored_value)

        # pre-check and set self.cf, finally checked and possibly resetted via check_settings
        reference_layer_defined = (
                self.ss._refLyrId is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._refLyrId) is not None
        )

        # Pre-Check, if Layers and fields exist, see self.cf and self.check_settings for later similar checks
        reference_layer_complete = (
                reference_layer_defined and
                self.ss._refLyrIdFieldName is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._refLyrId).fields().indexOf(self.ss._refLyrIdFieldName) >= 0
        )

        data_layer_complete = (
                self.ss._dataLyrId is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId) is not None and
                self.ss._dataLyrIdFieldName is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId).fields().indexOf(self.ss._dataLyrIdFieldName) >= 0 and
                self.ss._dataLyrReferenceFieldName is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId).fields().indexOf(self.ss._dataLyrReferenceFieldName) >= 0 and
                self.ss._dataLyrMeasureFromFieldName is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId).fields().indexOf(self.ss._dataLyrMeasureFromFieldName) >= 0 and
                self.ss._dataLyrMeasureToFieldName is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId).fields().indexOf(self.ss._dataLyrMeasureToFieldName) >= 0 and
                self.ss._dataLyrOffsetFieldName is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId).fields().indexOf(self.ss._dataLyrOffsetFieldName) >= 0
        )

        show_layer_complete = (
                self.ss._showLyrId is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._showLyrId) is not None and
                self.ss._showLyrBackReferenceFieldName is not None and
                qgis.core.QgsProject.instance().mapLayer(self.ss._showLyrId).fields().indexOf(self.ss._showLyrBackReferenceFieldName) >= 0
        )

        # all or nothing
        if not reference_layer_complete:
            self.ss._refLyrId = None
            self.ss._refLyrIdFieldName = None

        if not reference_layer_complete or not data_layer_complete:
            self.ss._dataLyrId = None
            self.ss._dataLyrIdFieldName = None
            self.ss._dataLyrReferenceFieldName = None
            self.ss._dataLyrMeasureFromFieldName = None
            self.ss._dataLyrMeasureToFieldName = None
            self.ss._dataLyrOffsetFieldName = None

        if not reference_layer_complete or not data_layer_complete or not show_layer_complete:
            self.ss._showLyrId = None
            self.ss._showLyrBackReferenceFieldName = None

        # prepare_xxx_layer() ➜ connects signals/slots
        if qgis.core.QgsProject.instance().mapLayer(self.ss._refLyrId) is not None:
            self.connect_reference_layer(qgis.core.QgsProject.instance().mapLayer(self.ss._refLyrId))

        if qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId) is not None:
            self.connect_data_layer(qgis.core.QgsProject.instance().mapLayer(self.ss._dataLyrId))

        if qgis.core.QgsProject.instance().mapLayer(self.ss._showLyrId) is not None:
            self.connect_show_layer(qgis.core.QgsProject.instance().mapLayer(self.ss._showLyrId))

    def push_messages(self, success_msg: str = None, info_msg: str = None, warning_msg: str = None, critical_msg: str = None):
        """pushes four kind of messages to messageBar
        :param success_msg:
        :param info_msg:
        :param warning_msg:
        :param critical_msg:
        """
        # Rev. 2023-05-23
        debug_pos = gdp(2)
        title = f"LinearReferencing ({debug_pos})"

        # descending by duration
        if critical_msg:
            self.iface.messageBar().pushMessage(title, critical_msg, level=qgis.core.Qgis.Critical, duration=20)

        if warning_msg:
            self.iface.messageBar().pushMessage(title, warning_msg, level=qgis.core.Qgis.Warning, duration=10)

        if info_msg:
            self.iface.messageBar().pushMessage(title, info_msg, level=qgis.core.Qgis.Info, duration=5)

        if success_msg:
            self.iface.messageBar().pushMessage(title, success_msg, level=qgis.core.Qgis.Success, duration=3)

    def check_settings(self, tool_mode: str = None):
        """ restores self.ds from self.ss, checks the current configuration
        :param tool_mode: checks the settings for this tool-mode and set self.rs.tool_mode, if settings are sufficient. If None, self.rs.tool_mode is used
        """
        # Rev. 2023-05-03

        if tool_mode and tool_mode not in self.tool_modes:
            self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "tool_mode {apos}{0}{apos} not implemented..."), tool_mode))
            tool_mode = None

        if not tool_mode:
            # use current toolmode
            tool_mode = self.rs.tool_mode

        if not tool_mode:
            # no current toolmode ➜ first run
            tool_mode = 'before_measure'

        # each time re-init with blank "templates"
        self.ds = self.DeferedSettings()
        self.cf = self.CheckFlags()

        if self.iface.mapCanvas().mapSettings().destinationCrs().isGeographic():
            self.rs.num_digits = 4
        else:
            self.rs.num_digits = 1

        # for type-matching-checks of reference/join-Fields:
        # PKs in databases ar normaly type int, but there are four types of integers, which can be mixed
        # all other possible types (propably string..., UUID) must match exact
        integer_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong]
        pk_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong, QtCore.QVariant.String]
        numeric_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong, QtCore.QVariant.Double]

        # get the resources == loaded layers in current project
        data_layers = tools.MyToolFunctions.get_data_layers()
        linestring_layers = tools.MyToolFunctions.get_linestring_layers()

        # convenience for the basic requisite:
        # if not set so far: take the topmost linestring-layer
        if not self.ss.refLyrId or self.ss.refLyrId not in linestring_layers:
            if linestring_layers:
                new_ref_lyer = list(linestring_layers.values()).pop()
                self.connect_reference_layer(new_ref_lyer)

        if self.ss.refLyrId and self.ss.refLyrId in linestring_layers:
            self.ds.refLyr = linestring_layers[self.ss.refLyrId]

        if self.ds.refLyr and self.ss.refLyrIdFieldName:
            fnx = self.ds.refLyr.dataProvider().fields().indexOf(self.ss.refLyrIdFieldName)
            if fnx >= 0 and self.ds.refLyr.dataProvider().fields()[fnx].type() in pk_field_types:
                self.ds.refLyrPkField = self.ds.refLyr.dataProvider().fields()[fnx]

        if self.ss.dataLyrId and self.ss.dataLyrId in data_layers:
            self.ds.dataLyr = data_layers[self.ss.dataLyrId]

        if self.ds.dataLyr and self.ss.dataLyrIdFieldName:
            fnx = self.ds.dataLyr.dataProvider().fields().indexOf(self.ss.dataLyrIdFieldName)
            if fnx >= 0 and self.ds.dataLyr.dataProvider().fields()[fnx].type() in numeric_field_types:
                self.ds.dataLyrIdField = self.ds.dataLyr.dataProvider().fields()[fnx]

        if self.ds.dataLyr and self.ds.refLyr and self.ds.refLyrPkField and self.ss.dataLyrReferenceFieldName:
            fnx = self.ds.dataLyr.dataProvider().fields().indexOf(self.ss.dataLyrReferenceFieldName)
            if fnx >= 0 and (self.ds.refLyrPkField.type() == self.ds.dataLyr.dataProvider().fields()[fnx].type()) or (self.ds.refLyrPkField.type() in integer_field_types and self.ds.dataLyr.dataProvider().fields()[fnx].type() in integer_field_types):
                self.ds.dataLyrReferenceField = self.ds.dataLyr.dataProvider().fields()[fnx]

        if self.ds.dataLyr and self.ss.dataLyrMeasureFromFieldName:
            fnx = self.ds.dataLyr.dataProvider().fields().indexOf(self.ss.dataLyrMeasureFromFieldName)
            if fnx >= 0 and self.ds.dataLyr.dataProvider().fields()[fnx].type() in numeric_field_types:
                self.ds.dataLyrMeasureFromField = self.ds.dataLyr.dataProvider().fields()[fnx]

        if self.ds.dataLyr and self.ss.dataLyrMeasureToFieldName:
            fnx = self.ds.dataLyr.dataProvider().fields().indexOf(self.ss.dataLyrMeasureToFieldName)
            if fnx >= 0 and self.ds.dataLyr.dataProvider().fields()[fnx].type() in numeric_field_types:
                self.ds.dataLyrMeasureToField = self.ds.dataLyr.dataProvider().fields()[fnx]

        if self.ds.dataLyr and self.ss.dataLyrOffsetFieldName:
            fnx = self.ds.dataLyr.dataProvider().fields().indexOf(self.ss.dataLyrOffsetFieldName)
            if fnx >= 0 and self.ds.dataLyr.dataProvider().fields()[fnx].type() in numeric_field_types:
                self.ds.dataLyrOffsetField = self.ds.dataLyr.dataProvider().fields()[fnx]

        if self.ss.showLyrId and self.ss.showLyrId in linestring_layers and self.ss.showLyrId != self.ss.refLyrId:
            self.ds.showLyr = linestring_layers[self.ss.showLyrId]

        if self.ds.showLyr and self.ds.dataLyrIdField and self.ss.showLyrBackReferenceFieldName:
            fnx = self.ds.showLyr.dataProvider().fields().indexOf(self.ss.showLyrBackReferenceFieldName)
            if fnx >= 0 and (self.ds.dataLyrIdField.type() == self.ds.showLyr.dataProvider().fields()[fnx].type()) or (self.ds.dataLyrIdField.type() in integer_field_types and self.ds.showLyr.dataProvider().fields()[fnx].type() in integer_field_types):
                self.ds.showLyrBackReferenceField = self.ds.showLyr.dataProvider().fields()[fnx]

        self.cf.reference_layer_defined = self.ds.refLyr is not None

        self.cf.reference_layer_complete = (
                self.cf.reference_layer_defined and
                self.ds.refLyrPkField is not None
        )
        self.cf.data_layer_defined = self.ds.dataLyr is not None
        self.cf.data_layer_complete = (
                self.cf.data_layer_defined and
                self.ds.dataLyrIdField is not None and
                self.ds.dataLyrReferenceField is not None and
                self.ds.dataLyrMeasureFromField is not None and
                self.ds.dataLyrMeasureToField is not None and
                self.ds.dataLyrOffsetField is not None
        )
        self.cf.show_layer_defined = self.ds.showLyr is not None
        self.cf.show_layer_complete = (
                self.cf.show_layer_defined and
                self.ds.showLyrBackReferenceField is not None
        )

        if self.rs.snapped_ref_fid is not None:
            if self.cf.reference_layer_defined:
                ref_feature = self.ds.refLyr.getFeature(self.rs.snapped_ref_fid)
                if not (ref_feature and ref_feature.isValid() and ref_feature.hasGeometry()):
                    self.rs.snapped_ref_fid = None
            else:
                self.rs.snapped_ref_fid = None
        checked_edit_pk = None
        if self.cf.reference_layer_complete and self.cf.data_layer_complete:
            # double-check: data_feature and ref_feature
            if self.rs.edit_pk is not None:
                data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, self.rs.edit_pk)
                if data_feature and data_feature.isValid():
                    ref_id = data_feature[self.ss.dataLyrReferenceFieldName]
                    ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, ref_id)
                    if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                        checked_edit_pk = self.rs.edit_pk
        self.rs.edit_pk = checked_edit_pk

        # make unique
        self.rs.selected_pks = list(dict.fromkeys(self.rs.selected_pks))

        checked_selected_pks = []
        if self.cf.reference_layer_complete and self.cf.data_layer_complete and len(self.rs.selected_pks) > 0:
            not_valid_count = 0
            no_ref_layer_count = 0
            # check self.rs.selected_pks: iterate through List of PKs and query features
            for pk in self.rs.selected_pks:
                data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, pk)
                if data_feature and data_feature.isValid():
                    ref_id = data_feature[self.ss.dataLyrReferenceFieldName]
                    ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, ref_id)
                    if ref_feature and ref_feature.isValid() and ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                        checked_selected_pks.append(pk)
                    else:
                        no_ref_layer_count += 1
                else:
                    not_valid_count += 1

            if not_valid_count:
                self.push_messages(info_msg=f"{not_valid_count} feature(s) removed from selection, features not valid")

            if no_ref_layer_count:
                self.push_messages(info_msg=f"{no_ref_layer_count} feature(s) removed from selection, no referenced linestring feature found")

        self.rs.selected_pks = checked_selected_pks

        # check tool_mode and switch if required
        if tool_mode in ['init', 'disabled']:
            if self.cf.reference_layer_defined:
                tool_mode = 'before_measure'
            else:
                tool_mode = 'disabled'
        elif tool_mode in ['before_measure', 'before_move_from_point', 'before_move_to_point', 'move_from_point', 'move_to_point', 'after_measure', 'before_move_segment', 'move_segment']:
            if not self.cf.reference_layer_defined:
                tool_mode = 'disabled'
        elif tool_mode in ['select_features']:
            if not (self.cf.reference_layer_complete and self.cf.data_layer_complete and self.cf.show_layer_complete):
                if self.cf.reference_layer_defined:
                    tool_mode = 'before_measure'
                else:
                    tool_mode = 'disabled'

        self.cf.measure_completed = (
                self.cf.reference_layer_defined and
                self.rs.snapped_ref_fid is not None and
                self.rs.current_measure_from is not None and
                self.rs.current_measure_to is not None and
                self.rs.current_offset is not None
        )

        self.cf.insert_enabled = (
                self.cf.measure_completed and
                self.cf.reference_layer_complete and
                self.cf.data_layer_complete and
                (self.ds.dataLyr.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.AddFeatures)
        )

        self.cf.update_enabled = (
                self.cf.data_layer_complete and
                self.rs.edit_pk is not None and
                (self.ds.dataLyr.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.ChangeAttributeValues)
        )

        self.cf.delete_enabled = (
                self.cf.data_layer_complete and
                self.rs.edit_pk is not None and
                (self.ds.dataLyr.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.DeleteFeatures)
        )

        # see https://doc.qt.io/qt-5/qt.html#CursorShape-enum
        if type(self.iface.mapCanvas().mapTool()) == LolEvt:
            if tool_mode in ['before_measure', 'measuring', 'after_measure', 'select_features']:
                self.iface.mapCanvas().setCursor(QtCore.Qt.CrossCursor)
            elif tool_mode in ['before_move_from_point', 'before_move_to_point', 'before_move_segment']:
                self.iface.mapCanvas().setCursor(QtCore.Qt.OpenHandCursor)
            elif tool_mode in ['move_from_point', 'move_to_point', 'move_segment']:
                self.iface.mapCanvas().setCursor(QtCore.Qt.ClosedHandCursor)
            else:
                self.iface.mapCanvas().setCursor(QtCore.Qt.ArrowCursor)

        self.rs.tool_mode = tool_mode
        # show Toolmode in status_bar
        if self.my_dialogue:
            self.my_dialogue.status_bar.clearMessage()
            self.my_dialogue.status_bar.showMessage(f"{self.rs.tool_mode} ➜ {self.tool_modes.get(self.rs.tool_mode)}")

    def refresh_gui(self):
        """wrapper-slot for any layer-config-change, checks the settings and refreshes GUI (dialog, layer-actions, Snapping, canvas-graphics)"""
        # Rev. 2023-05-10
        self.check_settings()
        self.dlg_refresh_reference_layer_section()
        self.dlg_refresh_measure_section()
        self.dlg_refresh_edit_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()
        self.dlg_refresh_style_settings_section()
        self.dlg_refresh_stored_settings_section()
        self.connect_all_layers()
        self.refresh_canvas_graphics()

    def dlg_refresh_edit_section(self):
        """refreshes the edit-section in dialog"""
        # Rev. 2023-05-10
        if self.my_dialogue:
            self.my_dialogue.pbtn_insert_feature.setEnabled(self.cf.insert_enabled)
            self.my_dialogue.pbtn_update_feature.setEnabled(self.cf.update_enabled and self.rs.edit_pk is not None)
            self.my_dialogue.pbtn_delete_feature.setEnabled(self.cf.delete_enabled and self.rs.edit_pk is not None)
            if self.rs.edit_pk is not None:
                if not self.check_data_feature(self.rs.edit_pk,False):
                    self.rs.edit_pk = None
                    self.my_dialogue.le_edit_data_pk.clear()

    def dlg_refresh_layer_settings_section(self):
        """refreshes the settings-part in dialog"""
        # Rev. 2023-05-10
        if self.my_dialogue:

            block_widgets = [
                self.my_dialogue.qcbn_reference_layer,
                self.my_dialogue.qcbn_reference_layer_id_field,
                self.my_dialogue.qcbn_data_layer,
                self.my_dialogue.qcbn_data_layer_id_field,
                self.my_dialogue.qcbn_data_layer_reference_field,
                self.my_dialogue.qcbn_data_layer_measure_from_field,
                self.my_dialogue.qcbn_data_layer_measure_to_field,
                self.my_dialogue.qcbn_data_layer_offset_field,
                self.my_dialogue.qcbn_show_layer,
                self.my_dialogue.qcbn_show_layer_back_reference_field
            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                widget.clear()

            linestring_layers = tools.MyToolFunctions.get_linestring_layers()
            pk_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong, QtCore.QVariant.String]
            integer_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong]
            numeric_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong, QtCore.QVariant.Double]

            model = QtGui.QStandardItemModel(0, 3)
            for cltrl in qgis.core.QgsProject.instance().layerTreeRoot().findLayers():
                if cltrl.layer():
                    cl = cltrl.layer()
                    if cl.isValid():
                        name_item = QtGui.QStandardItem(cl.name())
                        name_item.setData(cl, 256)
                        name_item.setEnabled(cl.id() in linestring_layers)
                        if isinstance(cl, qgis.core.QgsVectorLayer):
                            geometry_item = QtGui.QStandardItem(qgis.core.QgsWkbTypes.displayString(cl.dataProvider().wkbType()))
                        else:
                            geometry_item = QtGui.QStandardItem("Raster")

                        if isinstance(cl, qgis.core.QgsVectorLayer) and cl.dataProvider().name() != 'virtual':
                            provider_item = QtGui.QStandardItem(f"{cl.dataProvider().name()} ({cl.dataProvider().storageType()})")
                        else:
                            provider_item = QtGui.QStandardItem(cl.dataProvider().name())

                        items = [name_item, geometry_item, provider_item]
                        model.appendRow(items)
            self.my_dialogue.qcbn_reference_layer.set_model(model)
            if self.ds.refLyr:
                self.my_dialogue.qcbn_reference_layer.select_by_value(0, 256, self.ds.refLyr)
                model = QtGui.QStandardItemModel(0, 3)
                idx = 0
                for field in self.ds.refLyr.dataProvider().fields():
                    name_item = QtGui.QStandardItem(field.name())
                    name_item.setData(field, 256)
                    name_item.setEnabled(field.type() in pk_field_types)
                    # mark PK-Field with green check-icon
                    is_pk_item = QtGui.QStandardItem()
                    if idx in self.ds.refLyr.dataProvider().pkAttributeIndexes():
                        is_pk_item.setData(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'), 1)  # DecorationRole
                    type_item = QtGui.QStandardItem(field.friendlyTypeString())
                    items = [name_item, type_item, is_pk_item]
                    model.appendRow(items)
                    idx += 1

                self.my_dialogue.qcbn_reference_layer_id_field.set_model(model)

                if self.ds.refLyrPkField:
                    # QtCore.Qt.ExactMatch doesn't match anything if used for fields, therefore match with role-index 0 (DisplayRole, Text-Content) with the (hopefully unique...) name of the field
                    self.my_dialogue.qcbn_reference_layer_id_field.select_by_value(0, 0, self.ds.refLyrPkField.name())
                    # PK-Field is selected, now the Data-Layer

                    model = QtGui.QStandardItemModel(0, 3)

                    # in ihrer TOC-Reihenfolge
                    for cltrl in qgis.core.QgsProject.instance().layerTreeRoot().findLayers():
                        if cltrl.layer():
                            cl = cltrl.layer()
                            if cl.isValid():
                                name_item = QtGui.QStandardItem(cl.name())
                                name_item.setData(cl, 256)
                                name_item.setEnabled(cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.geometryType() == qgis.core.QgsWkbTypes.NullGeometry)
                                if isinstance(cl, qgis.core.QgsVectorLayer):
                                    geometry_item = QtGui.QStandardItem(qgis.core.QgsWkbTypes.displayString(cl.dataProvider().wkbType()))
                                else:
                                    geometry_item = QtGui.QStandardItem("Raster")

                                if isinstance(cl, qgis.core.QgsVectorLayer) and cl.dataProvider().name() != 'virtual':
                                    provider_item = QtGui.QStandardItem(f"{cl.dataProvider().name()} ({cl.dataProvider().storageType()})")
                                else:
                                    provider_item = QtGui.QStandardItem(cl.dataProvider().name())

                                items = [name_item, geometry_item, provider_item]
                                model.appendRow(items)

                    self.my_dialogue.qcbn_data_layer.set_model(model)

                    if self.ds.dataLyr:
                        self.my_dialogue.qcbn_data_layer.select_by_value(0, 256, self.ds.dataLyr)
                        # dataLyr set, now the ID-Field
                        idx = 0
                        model = QtGui.QStandardItemModel(0, 3)

                        for field in self.ds.dataLyr.dataProvider().fields():
                            name_item = QtGui.QStandardItem(field.name())
                            name_item.setData(field, 256)
                            name_item.setEnabled(field.type() in pk_field_types)
                            # mark PK-Field with green check-icon
                            is_pk_item = QtGui.QStandardItem()
                            if idx in self.ds.refLyr.dataProvider().pkAttributeIndexes():
                                is_pk_item.setData(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'), 1)  # DecorationRole
                            type_item = QtGui.QStandardItem(field.friendlyTypeString())
                            items = [name_item, type_item, is_pk_item]
                            model.appendRow(items)
                            idx += 1

                        self.my_dialogue.qcbn_data_layer_id_field.set_model(model)

                        if self.ds.dataLyrIdField:
                            self.my_dialogue.qcbn_data_layer_id_field.select_by_value(0, 0, self.ds.dataLyrIdField.name())
                            # PkField set, now the Reference-Field
                            idx = 0
                            model = QtGui.QStandardItemModel(0, 3)
                            for field in self.ds.dataLyr.dataProvider().fields():
                                name_item = QtGui.QStandardItem(field.name())
                                name_item.setData(field, 256)
                                # must be same type as type refLyrPkField, not ID-Field and not the selected PK-Field
                                name_item.setEnabled(field != self.ds.dataLyrIdField and
                                                     idx not in self.ds.dataLyr.dataProvider().pkAttributeIndexes() and
                                                     (
                                                             (self.ds.refLyrPkField.type() in integer_field_types and field.type() in integer_field_types) or
                                                             field.type() == self.ds.refLyrPkField.type()
                                                     )
                                                     )
                                # mark PK-Field with green check-icon
                                is_pk_item = QtGui.QStandardItem()
                                if idx in self.ds.refLyr.dataProvider().pkAttributeIndexes():
                                    is_pk_item.setData(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'), 1)  # DecorationRole
                                type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                items = [name_item, type_item, is_pk_item]
                                model.appendRow(items)
                                idx += 1

                            self.my_dialogue.qcbn_data_layer_reference_field.set_model(model)

                            if self.ds.dataLyrReferenceField:
                                self.my_dialogue.qcbn_data_layer_reference_field.select_by_value(0, 0, self.ds.dataLyrReferenceField.name())
                                idx = 0
                                model = QtGui.QStandardItemModel(0, 3)
                                for field in self.ds.dataLyr.dataProvider().fields():
                                    name_item = QtGui.QStandardItem(field.name())
                                    name_item.setData(field, 256)
                                    # numerical, but no PK and not one of the almost selected fields. Can a double-value be used as PK or reference-key...?
                                    name_item.setEnabled(
                                        field.type() in numeric_field_types and
                                        field != self.ds.dataLyrIdField and
                                        field != self.ds.dataLyrReferenceField and
                                        idx not in self.ds.dataLyr.dataProvider().pkAttributeIndexes()
                                    )
                                    # mark PK-Field with green check-icon
                                    is_pk_item = QtGui.QStandardItem()
                                    if idx in self.ds.refLyr.dataProvider().pkAttributeIndexes():
                                        is_pk_item.setData(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'), 1)  # DecorationRole
                                    type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                    items = [name_item, type_item, is_pk_item]
                                    model.appendRow(items)
                                    idx += 1

                                self.my_dialogue.qcbn_data_layer_measure_from_field.set_model(model)

                                if self.ds.dataLyrMeasureFromField:
                                    self.my_dialogue.qcbn_data_layer_measure_from_field.select_by_value(0, 0, self.ds.dataLyrMeasureFromField.name())
                                    idx = 0
                                    model = QtGui.QStandardItemModel(0, 3)
                                    for field in self.ds.dataLyr.dataProvider().fields():
                                        name_item = QtGui.QStandardItem(field.name())
                                        name_item.setData(field, 256)
                                        # numerical, but no PK and not one of the almost selected fields. Can a double-value be used as PK or reference-key...?
                                        name_item.setEnabled(
                                            field.type() in numeric_field_types and
                                            field != self.ds.dataLyrIdField and
                                            field != self.ds.dataLyrReferenceField and
                                            field != self.ds.dataLyrMeasureFromField and
                                            idx not in self.ds.dataLyr.dataProvider().pkAttributeIndexes()
                                        )
                                        # mark PK-Field with green check-icon
                                        is_pk_item = QtGui.QStandardItem()
                                        if idx in self.ds.refLyr.dataProvider().pkAttributeIndexes():
                                            is_pk_item.setData(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'), 1)  # DecorationRole
                                        type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                        items = [name_item, type_item, is_pk_item]
                                        model.appendRow(items)
                                        idx += 1

                                    self.my_dialogue.qcbn_data_layer_measure_to_field.set_model(model)

                                    if self.ds.dataLyrMeasureToField:
                                        self.my_dialogue.qcbn_data_layer_measure_to_field.select_by_value(0, 0, self.ds.dataLyrMeasureToField.name())

                                        idx = 0
                                        model = QtGui.QStandardItemModel(0, 3)
                                        for field in self.ds.dataLyr.dataProvider().fields():
                                            name_item = QtGui.QStandardItem(field.name())
                                            name_item.setData(field, 256)
                                            # numerical, but no PK and not one of the almost selected fields. Can a double-value be used as PK or reference-key...?
                                            name_item.setEnabled(
                                                field.type() in numeric_field_types and
                                                field != self.ds.dataLyrIdField and
                                                field != self.ds.dataLyrReferenceField and
                                                field != self.ds.dataLyrMeasureFromField and
                                                field != self.ds.dataLyrMeasureToField and
                                                idx not in self.ds.dataLyr.dataProvider().pkAttributeIndexes()
                                            )
                                            # mark PK-Field with green check-icon
                                            is_pk_item = QtGui.QStandardItem()
                                            if idx in self.ds.refLyr.dataProvider().pkAttributeIndexes():
                                                is_pk_item.setData(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'), 1)  # DecorationRole
                                            type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                            items = [name_item, type_item, is_pk_item]
                                            model.appendRow(items)
                                            idx += 1

                                        self.my_dialogue.qcbn_data_layer_offset_field.set_model(model)

                                        if self.ds.dataLyrOffsetField:
                                            self.my_dialogue.qcbn_data_layer_offset_field.select_by_value(0, 0, self.ds.dataLyrOffsetField.name())

                                            model = QtGui.QStandardItemModel(0, 3)
                                            for cltrl in qgis.core.QgsProject.instance().layerTreeRoot().findLayers():
                                                if cltrl.layer():
                                                    cl = cltrl.layer()
                                                    if cl.isValid():
                                                        name_item = QtGui.QStandardItem(cl.name())
                                                        name_item.setData(cl, 256)
                                                        # Type vector, Point
                                                        # not (!) ogr
                                                        # ➜ must be database-view or virtual
                                                        # not found pyqgis-solution to detect database-layers
                                                        dep_lst = []
                                                        if cl.dataProvider().name() == 'virtual':
                                                            for dp in cl.dataProvider().dependencies():
                                                                dep_lst.append(dp.layerId())

                                                        name_item.setEnabled(
                                                            cl.id() in linestring_layers and
                                                            cl != self.ds.refLyr and
                                                            (
                                                                # database ...
                                                                cl.dataProvider().name() not in ['ogr', 'virtual'] or
                                                                (
                                                                    # ... or virtual and defined with the registered refLyr.id() and dataLyr.id() int its uri
                                                                    cl.dataProvider().name() == 'virtual' and
                                                                    self.ds.refLyr.id() in dep_lst and
                                                                    self.ds.dataLyr.id() in dep_lst
                                                                )
                                                            )
                                                        )
                                                        if isinstance(cl, qgis.core.QgsVectorLayer):
                                                            geometry_item = QtGui.QStandardItem(qgis.core.QgsWkbTypes.displayString(cl.dataProvider().wkbType()))
                                                        else:
                                                            geometry_item = QtGui.QStandardItem("Raster")

                                                        if isinstance(cl, qgis.core.QgsVectorLayer) and cl.dataProvider().name() != 'virtual':
                                                            provider_item = QtGui.QStandardItem(f"{cl.dataProvider().name()} ({cl.dataProvider().storageType()})")
                                                        else:
                                                            provider_item = QtGui.QStandardItem(cl.dataProvider().name())

                                                        items = [name_item, geometry_item, provider_item]
                                                        model.appendRow(items)

                                            self.my_dialogue.qcbn_show_layer.set_model(model)

                                            if self.ds.showLyr:
                                                self.my_dialogue.qcbn_show_layer.select_by_value(0, 256, self.ds.showLyr)

                                                # last action: Back-Reference from Show- to Data-Layer

                                                model = QtGui.QStandardItemModel(0, 3)
                                                idx = 0
                                                for field in self.ds.showLyr.dataProvider().fields():
                                                    name_item = QtGui.QStandardItem(field.name())
                                                    name_item.setData(field, 256)
                                                    # numerical, but no PK and not one of the almost selected fields. Can a double-value be used as PK or reference-key...?
                                                    name_item.setEnabled(
                                                        (self.ds.dataLyrIdField.type() in integer_field_types and field.type() in integer_field_types) or
                                                        field.type() == self.ds.dataLyrIdField.type()
                                                    )
                                                    # mark PK-Field with green check-icon
                                                    is_pk_item = QtGui.QStandardItem()
                                                    if idx in self.ds.refLyr.dataProvider().pkAttributeIndexes():
                                                        is_pk_item.setData(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'), 1)  # DecorationRole
                                                    type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                                    items = [name_item, type_item, is_pk_item]
                                                    model.appendRow(items)
                                                    idx += 1

                                                self.my_dialogue.qcbn_show_layer_back_reference_field.set_model(model)

                                                if self.ds.showLyrBackReferenceField:
                                                    self.my_dialogue.qcbn_show_layer_back_reference_field.select_by_value(0, 0, self.ds.showLyrBackReferenceField.name())
            for widget in block_widgets:
                widget.blockSignals(False)

            self.my_dialogue.pb_open_ref_tbl.setEnabled(self.cf.reference_layer_defined)
            self.my_dialogue.pb_call_ref_disp_exp_dlg.setEnabled(self.cf.reference_layer_defined)
            self.my_dialogue.pb_open_data_tbl.setEnabled(self.cf.data_layer_defined)
            self.my_dialogue.pb_call_data_disp_exp_dlg.setEnabled(self.cf.data_layer_defined)
            self.my_dialogue.pb_open_show_tbl.setEnabled(self.cf.show_layer_defined)
            self.my_dialogue.pb_call_show_disp_exp_dlg.setEnabled(self.cf.show_layer_defined)
            self.my_dialogue.pbtn_create_show_layer.setEnabled(self.cf.reference_layer_complete and self.cf.data_layer_complete)
            self.my_dialogue.pbtn_create_data_layer.setEnabled(self.cf.reference_layer_complete)

    def dlg_refresh_style_settings_section(self):
        if self.my_dialogue:

            block_widgets = [
                self.my_dialogue.qcb_from_point_icon_type,
                self.my_dialogue.qcb_to_point_icon_type,
                self.my_dialogue.qcb_segment_line_line_style,
                self.my_dialogue.qcb_ref_line_line_style,
                self.my_dialogue.qpb_from_point_color,
                self.my_dialogue.qpb_from_point_fill_color,
                self.my_dialogue.qpb_to_point_color,
                self.my_dialogue.qpb_to_point_fill_color,
                self.my_dialogue.qpb_segment_line_color,
                self.my_dialogue.qpb_ref_line_color,
                self.my_dialogue.qspb_from_point_icon_size,
                self.my_dialogue.qspb_from_point_pen_width,
                self.my_dialogue.qspb_to_point_icon_size,
                self.my_dialogue.qspb_to_point_pen_width,
                self.my_dialogue.qspb_segment_line_width,
                self.my_dialogue.qspb_ref_line_width,
            ]

            for widget in block_widgets:
                widget.blockSignals(True)

            tools.MyToolFunctions.select_by_value(self.my_dialogue.qcb_from_point_icon_type, self.ss.from_point_icon_type, 0, 256)
            tools.MyToolFunctions.select_by_value(self.my_dialogue.qcb_to_point_icon_type, self.ss.to_point_icon_type, 0, 256)
            tools.MyToolFunctions.select_by_value(self.my_dialogue.qcb_segment_line_line_style, self.ss.segment_line_line_style, 0, 256)
            tools.MyToolFunctions.select_by_value(self.my_dialogue.qcb_ref_line_line_style, self.ss.ref_line_line_style, 0, 256)
            self.my_dialogue.qpb_from_point_color.set_color(self.ss.from_point_color)
            self.my_dialogue.qpb_from_point_fill_color.set_color(self.ss.from_point_fill_color)
            self.my_dialogue.qpb_to_point_color.set_color(self.ss.to_point_color)
            self.my_dialogue.qpb_to_point_fill_color.set_color(self.ss.to_point_fill_color)
            self.my_dialogue.qpb_segment_line_color.set_color(self.ss.segment_line_color)
            self.my_dialogue.qpb_ref_line_color.set_color(self.ss.ref_line_color)
            self.my_dialogue.qspb_from_point_icon_size.setValue(self.ss.from_point_icon_size)
            self.my_dialogue.qspb_from_point_pen_width.setValue(self.ss.from_point_pen_width)
            self.my_dialogue.qspb_to_point_icon_size.setValue(self.ss.to_point_icon_size)
            self.my_dialogue.qspb_to_point_pen_width.setValue(self.ss.to_point_pen_width)
            self.my_dialogue.qspb_segment_line_width.setValue(self.ss.segment_line_width)
            self.my_dialogue.qspb_ref_line_width.setValue(self.ss.ref_line_width)

            for widget in block_widgets:
                widget.blockSignals(False)

    def dlg_refresh_reference_layer_section(self):
        """re-populates the QComboBoxN with the List of Reference-Layer-Features"""
        # Rev. 2023-05-03
        if self.my_dialogue and self.ds.refLyr:
            self.my_dialogue.qcbn_snapped_ref_fid.blockSignals(True)

            in_model = QtGui.QStandardItemModel(0, 2)
            context = qgis.core.QgsExpressionContext()
            exp = qgis.core.QgsExpression(self.ds.refLyr.displayExpression())
            for feature in self.ds.refLyr.getFeatures():
                context.setFeature(feature)
                disp_exp_evaluated = exp.evaluate(context)

                items = []
                item = QtGui.QStandardItem()
                item.setData(feature.id(), 0)
                item.setData(feature.id(), 256)
                items.append(item)

                item = QtGui.QStandardItem()
                item.setData(disp_exp_evaluated, 0)
                items.append(item)

                item = QtGui.QStandardItem()
                item.setData(feature.geometry().length(), 0)
                items.append(item)

                in_model.appendRow(items)

            self.my_dialogue.qcbn_snapped_ref_fid.set_model(in_model)

            if self.rs.snapped_ref_fid is not None:
                self.my_dialogue.qcbn_snapped_ref_fid.select_by_value(0, 256, self.rs.snapped_ref_fid)

            self.my_dialogue.qcbn_snapped_ref_fid.blockSignals(False)

    def dlg_refresh_measure_section(self):
        """refresh measure-part in dialog"""
        # Rev. 2023-05-08
        if self.my_dialogue:
            # adapt dialogue to Projection:
            # projected vs. geographic CRS
            # => size-range, num digits, increments of QDoubleSpinBox, units...
            if self.iface.mapCanvas().mapSettings().destinationCrs().isGeographic():
                canvas_measure_unit = '[°]'
            else:
                canvas_measure_unit = '[m]'

            if self.ds.refLyr and self.ds.refLyr.crs().isGeographic():
                layer_measure_unit = '[°]'
                layer_measure_prec = 6
                layer_measure_step = 0.0001
            else:
                layer_measure_unit = '[m]'
                layer_measure_prec = 2
                layer_measure_step = 1

            for unit_widget in self.my_dialogue.canvas_unit_widgets:
                unit_widget.setText(canvas_measure_unit)

            for unit_widget in self.my_dialogue.layer_unit_widgets:
                unit_widget.setText(layer_measure_unit)

            self.my_dialogue.dspbx_offset.default_step = layer_measure_step
            self.my_dialogue.dspbx_offset.setDecimals(layer_measure_prec)

            self.my_dialogue.dspbx_measure_from.default_step = layer_measure_step
            self.my_dialogue.dspbx_measure_from.setDecimals(layer_measure_prec)

            self.my_dialogue.dspbx_measure_to.default_step = layer_measure_step
            self.my_dialogue.dspbx_measure_to.setDecimals(layer_measure_prec)

            self.my_dialogue.dspbx_distance.default_step = layer_measure_step
            self.my_dialogue.dspbx_distance.setDecimals(layer_measure_prec)

            # enable some functional widgets with special requirements

            self.my_dialogue.pbtn_resume_measure.setEnabled(self.cf.reference_layer_defined)
            self.my_dialogue.le_snap_pt_from_x.setEnabled(self.cf.measure_completed)
            self.my_dialogue.le_snap_pt_from_y.setEnabled(self.cf.measure_completed)
            self.my_dialogue.le_snap_pt_to_x.setEnabled(self.cf.measure_completed)
            self.my_dialogue.le_snap_pt_to_y.setEnabled(self.cf.measure_completed)
            self.my_dialogue.tbtn_move_segment_up.setEnabled(self.cf.measure_completed)
            self.my_dialogue.tbtn_move_segment_down.setEnabled(self.cf.measure_completed)
            self.my_dialogue.tbtn_move_segment_start.setEnabled(self.cf.measure_completed)
            self.my_dialogue.tbtn_prepend_segment.setEnabled(self.cf.measure_completed)
            self.my_dialogue.tbtn_move_segment_end.setEnabled(self.cf.measure_completed)
            self.my_dialogue.tbtn_append_segment.setEnabled(self.cf.measure_completed)
            self.my_dialogue.pb_zoom_to_segment.setEnabled(self.cf.measure_completed)
            self.my_dialogue.dspbx_measure_from.setEnabled(self.cf.measure_completed)
            self.my_dialogue.dspbx_measure_to.setEnabled(self.cf.measure_completed)
            self.my_dialogue.dspbx_measure_fract_from.setEnabled(self.cf.measure_completed)
            self.my_dialogue.dspbx_measure_fract_to.setEnabled(self.cf.measure_completed)
            self.my_dialogue.dspbx_distance.setEnabled(self.cf.measure_completed)
            self.my_dialogue.pbtn_move_from_point.setEnabled(self.cf.measure_completed)
            self.my_dialogue.pbtn_move_to_point.setEnabled(self.cf.measure_completed)
            self.my_dialogue.pbtn_move_from_point.setChecked(self.cf.measure_completed and self.rs.tool_mode in ['before_move_from_point', 'move_from_point'])
            self.my_dialogue.pbtn_move_to_point.setChecked(self.cf.measure_completed and self.rs.tool_mode in ['before_move_to_point', 'move_to_point'])
            self.my_dialogue.pb_move_segment.setEnabled(self.cf.measure_completed)
            self.my_dialogue.pb_move_segment.setChecked(self.cf.measure_completed and self.rs.tool_mode in ['before_move_segment', 'move_segment'])

            self.my_dialogue.qcbn_snapped_ref_fid.setEnabled(self.cf.reference_layer_defined)
            self.my_dialogue.pb_open_ref_form.setEnabled(self.cf.reference_layer_defined)
            self.my_dialogue.pb_zoom_to_ref_feature.setEnabled(self.cf.reference_layer_defined)

    def dlg_refresh_stored_settings_section(self):
        """re-populates the list with the stored Configurations within but independend from the dialog"""
        # Rev. 2023-05-08
        if self.my_dialogue:
            self.my_dialogue.lw_stored_settings.clear()
            for setting_idx in range(self._num_storable_settings):
                key = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                setting_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', key)
                if setting_label and type_conversion_ok:
                    qlwi = QtWidgets.QListWidgetItem()
                    qlwi.setText(setting_label)
                    qlwi.setData(256, setting_label)
                    self.my_dialogue.lw_stored_settings.addItem(qlwi)

    def dlg_refresh_feature_selection_section(self):
        """refreshes the Feature-Selection-List within but independend from the dialog"""
        # Rev. 2023-05-03
        # stored for the restore the sort-settings afterward
        if self.my_dialogue:
            # stored for the restore the sort-settings afterward
            prev_sort_col_idx = self.my_dialogue.qtw_selected_pks.horizontalHeader().sortIndicatorSection()
            prev_sort_order = self.my_dialogue.qtw_selected_pks.horizontalHeader().sortIndicatorOrder()

            # make unique
            self.rs.selected_pks = list(dict.fromkeys(self.rs.selected_pks))

            # clear all
            self.my_dialogue.qtw_selected_pks.setRowCount(0)
            self.my_dialogue.qtw_selected_pks.setColumnCount(0)
            self.my_dialogue.qtw_selected_pks.horizontalHeader().setVisible(False)

            # QTableWidget with selected edit-PKs, Show-Layer not necessary, but taken into account
            # signal/slot see:
            # self.my_dialogue.qtw_selected_pks.itemPressed.connect(self.qtw_item_pressed)
            if self.cf.reference_layer_complete and self.cf.data_layer_complete and len(self.rs.selected_pks) > 0:

                edit_features = {}
                # check self.rs.selected_pks: iterate through List of PKs and query features
                for edit_pk in self.rs.selected_pks:
                    if self.check_data_feature(edit_pk, False):
                        data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
                        ref_id = data_feature[self.ss.dataLyrReferenceFieldName]
                        ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, ref_id)
                        if self.cf.show_layer_complete:
                            show_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.showLyr, self.ds.showLyrBackReferenceField, edit_pk)
                            if show_feature and show_feature.isValid():
                                edit_features[edit_pk] = [data_feature, ref_feature, show_feature]
                            else:
                                edit_features[edit_pk] = [data_feature, ref_feature, None]
                        else:
                            edit_features[edit_pk] = [data_feature, ref_feature, None]
                self.rs.selected_pks = list(edit_features.keys())

                self.my_dialogue.qtw_selected_pks.horizontalHeader().setVisible(True)
                self.my_dialogue.qtw_selected_pks.setRowCount(len(self.rs.selected_pks))

                # displayExpression() for single-field: "field_name"
                # displayField() for same field: field_name (no quotes)
                # complexer displayExpression()-sample: "fid" + "line_ref_id" (including all spaces, tabs, linebreaks...)
                # displayField() for this expression: '' (empty string)
                # Logic:
                # Table with meaningful headers and contents,
                #   1. use possibly defined displayExpressions in the two/three involved layers
                #   2. PKs/IDs should always be recognizable, if they aren't already included in the displayExpression

                header_labels = [
                    'Data-Layer',
                    'Reference-Layer from ... to',
                    'Offset'
                ]

                if self.cf.show_layer_complete:
                    header_labels.append('Show-Layer')

                self.my_dialogue.qtw_selected_pks.setColumnCount(len(header_labels))
                self.my_dialogue.qtw_selected_pks.setHorizontalHeaderLabels(header_labels)

                remove_icon = QtGui.QIcon(':icons/mIconClearTextHover.svg')
                highlight_icon = QtGui.QIcon(':icons/mIconSelected.svg')
                pan_icon = QtGui.QIcon(':icons/mActionPanToSelected.svg')
                identify_icon = QtGui.QIcon(':icons/mActionIdentify.svg')

                data_context = qgis.core.QgsExpressionContext()
                # Features from Reference-Layer will show eith their PK and the evaluated displayExpression
                data_display_exp = qgis.core.QgsExpression(self.ds.dataLyr.displayExpression())
                data_display_exp.prepare(data_context)

                ref_context = qgis.core.QgsExpressionContext()
                ref_display_exp = qgis.core.QgsExpression(self.ds.refLyr.displayExpression())
                ref_display_exp.prepare(ref_context)
                if self.cf.show_layer_complete:
                    show_context = qgis.core.QgsExpressionContext()
                    show_display_exp = qgis.core.QgsExpression(self.ds.showLyr.displayExpression())
                    show_display_exp.prepare(show_context)

                rc = 0
                integer_field_types = [QtCore.QVariant.Int, QtCore.QVariant.UInt, QtCore.QVariant.LongLong, QtCore.QVariant.ULongLong]
                for edit_pk in edit_features:
                    data_feature = edit_features[edit_pk][0]
                    ref_feature = edit_features[edit_pk][1]
                    show_feature = edit_features[edit_pk][2]

                    data_pk = data_feature[self.ds.dataLyrIdField.name()]
                    data_context.setFeature(data_feature)
                    data_evaled_exp = data_display_exp.evaluate(data_context)
                    data_label = f"'{data_evaled_exp}'"
                    # expression with dataLyrIdField as single field
                    if data_display_exp.isField() and self.ds.dataLyrIdField.name() in data_display_exp.referencedColumns():
                        if self.ds.dataLyrIdField.type() in integer_field_types:
                            data_label = f"# {data_evaled_exp}"

                    data_measure_from = data_feature[self.ds.dataLyrMeasureFromField.name()]
                    data_measure_to = data_feature[self.ds.dataLyrMeasureToField.name()]
                    data_offset = data_feature[self.ds.dataLyrOffsetField.name()]

                    if self.ds.refLyr.crs().isGeographic():
                        data_measure_from_rd = round(data_measure_from, 5)
                        data_measure_to_rd = round(data_measure_to, 5)
                    else:
                        data_measure_from_rd = round(data_measure_from)
                        data_measure_to_rd = round(data_measure_to)

                    ref_context.setFeature(ref_feature)
                    ref_evaled_exp = ref_display_exp.evaluate(ref_context)
                    ref_label = f"'{ref_evaled_exp}'"

                    # expression with dataLyrIdField as single field
                    if ref_display_exp.isField() and self.ds.refLyrPkField.name() in ref_display_exp.referencedColumns():
                        if self.ds.refLyrPkField.type() in integer_field_types:
                            ref_label = f"# {ref_evaled_exp}"

                    show_back_ref_id = None
                    show_label_plus = None
                    if show_feature:
                        show_back_ref_id = show_feature[self.ds.showLyrBackReferenceField.name()]
                        show_context.setFeature(show_feature)
                        show_evaled_exp = show_display_exp.evaluate(show_context)
                        show_label_plus = f"'{show_evaled_exp}'"
                        # expression with dataLyrIdField as single field
                        if show_display_exp.isField() and self.ds.showLyrBackReferenceField.name() in show_display_exp.referencedColumns():
                            if self.ds.showLyrBackReferenceField.type() in integer_field_types:
                                show_label_plus = f"# {show_evaled_exp}"
                        else:
                            if self.ds.showLyrBackReferenceField.type() in integer_field_types:
                                show_label_plus = f"# {show_back_ref_id} {show_evaled_exp}"
                            else:
                                show_label_plus = f"'{show_back_ref_id}' {show_evaled_exp}"

                    # col 0 (the initial sort-column): line_reference from ... to
                    cc = 0

                    item = tools.MyQtWidgets.QTableWidgetItemMultipleSort(256)
                    item.setData(256, data_pk)
                    item.setText(f"{data_label}")

                    self.my_dialogue.qtw_selected_pks.setItem(rc, cc, item)

                    c_wdg = QtWidgets.QWidget()
                    c_wdg.setLayout(QtWidgets.QHBoxLayout())
                    c_wdg.layout().setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    c_wdg.layout().setContentsMargins(2, 0, 2, 0)
                    c_wdg.layout().setSpacing(2)

                    qtb = QtWidgets.QToolButton()
                    qtb.setIcon(remove_icon)
                    qtb.setCursor(QtCore.Qt.PointingHandCursor)
                    qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Remove feature from selection"))
                    qtb.clicked.connect(self.s_remove_from_feature_selection)
                    qtb.setProperty("edit_pk", edit_pk)
                    qtb.setFixedSize(QtCore.QSize(20, 20))
                    c_wdg.layout().addWidget(qtb)

                    qtb = QtWidgets.QToolButton()
                    qtb.setIcon(highlight_icon)
                    qtb.setCursor(QtCore.Qt.PointingHandCursor)
                    qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Highlight feature and select for edit"))
                    qtb.clicked.connect(self.s_highlight_edit_pk)
                    qtb.setProperty("edit_pk", edit_pk)
                    qtb.setFixedSize(QtCore.QSize(20, 20))
                    c_wdg.layout().addWidget(qtb)

                    qtb = QtWidgets.QToolButton()
                    qtb.setIcon(pan_icon)
                    qtb.setCursor(QtCore.Qt.PointingHandCursor)
                    qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Pan to feature and select for edit"))
                    qtb.clicked.connect(self.s_pan_edit_pk)
                    qtb.setProperty("edit_pk", edit_pk)
                    qtb.setFixedSize(QtCore.QSize(20, 20))
                    c_wdg.layout().addWidget(qtb)

                    qtb = QtWidgets.QToolButton()
                    qtb.setIcon(identify_icon)
                    qtb.setCursor(QtCore.Qt.PointingHandCursor)
                    qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Show feature-form"))
                    qtb.clicked.connect(self.s_open_data_form)
                    qtb.setProperty("edit_pk", edit_pk)
                    qtb.setFixedSize(QtCore.QSize(20, 20))
                    c_wdg.layout().addWidget(qtb)

                    self.my_dialogue.qtw_selected_pks.setCellWidget(rc, cc, c_wdg)

                    cc += 1

                    # Reference-Layer use expression and append ID, if not contained in expression
                    item = tools.MyQtWidgets.QTableWidgetItemMultipleSort(256, 257, 258)
                    item.setData(256, ref_label)
                    item.setData(257, data_measure_from)
                    item.setData(258, data_measure_to)

                    item.setText(f"{ref_label} {data_measure_from_rd} ... {data_measure_to_rd}")
                    self.my_dialogue.qtw_selected_pks.setItem(rc, cc, item)

                    # Reference-Layer with highlight, zoom, identify, FID and Label-Expression
                    c_wdg = QtWidgets.QWidget()
                    c_wdg.setLayout(QtWidgets.QHBoxLayout())
                    c_wdg.layout().setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    c_wdg.layout().setContentsMargins(2, 0, 2, 0)
                    c_wdg.layout().setSpacing(2)

                    qtb = QtWidgets.QToolButton()
                    qtb.setIcon(highlight_icon)
                    qtb.setCursor(QtCore.Qt.PointingHandCursor)
                    qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Highlight Reference-Layer-feature"))
                    qtb.clicked.connect(self.s_highlight_ref_feature_by_edit_pk)
                    qtb.setProperty("edit_pk", edit_pk)
                    qtb.setFixedSize(QtCore.QSize(20, 20))
                    c_wdg.layout().addWidget(qtb)

                    qtb = QtWidgets.QToolButton()
                    qtb.setIcon(pan_icon)
                    qtb.setCursor(QtCore.Qt.PointingHandCursor)
                    qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Zoom to Reference-Layer-feature"))
                    qtb.clicked.connect(self.s_zoom_ref_feature_by_edit_pk)
                    qtb.setProperty("edit_pk", edit_pk)
                    qtb.setFixedSize(QtCore.QSize(20, 20))
                    c_wdg.layout().addWidget(qtb)

                    qtb = QtWidgets.QToolButton()
                    qtb.setIcon(identify_icon)
                    qtb.setCursor(QtCore.Qt.PointingHandCursor)
                    qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Show Reference-Layer attribute-form"))
                    qtb.clicked.connect(self.s_open_ref_form_by_edit_pk)
                    qtb.setProperty("edit_pk", edit_pk)
                    qtb.setFixedSize(QtCore.QSize(20, 20))
                    c_wdg.layout().addWidget(qtb)

                    self.my_dialogue.qtw_selected_pks.setCellWidget(rc, cc, c_wdg)

                    cc += 1
                    # offset
                    item = tools.MyQtWidgets.QTableWidgetItemCustomSort(256)
                    item.setData(256, data_offset)
                    item.setText(str(data_offset))
                    self.my_dialogue.qtw_selected_pks.setItem(rc, cc, item)

                    if self.cf.show_layer_complete:
                        cc += 1
                        item = tools.MyQtWidgets.QTableWidgetItemCustomSort(256)
                        item.setData(256, show_back_ref_id)
                        item.setData(257, edit_pk)

                        item.setText(show_label_plus)

                        self.my_dialogue.qtw_selected_pks.setItem(rc, cc, item)

                        c_wdg = QtWidgets.QWidget()
                        c_wdg.setLayout(QtWidgets.QHBoxLayout())
                        c_wdg.layout().setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                        c_wdg.layout().setContentsMargins(2, 0, 2, 0)
                        c_wdg.layout().setSpacing(2)

                        qtb = QtWidgets.QToolButton()
                        qtb.setIcon(identify_icon)
                        qtb.setCursor(QtCore.Qt.PointingHandCursor)
                        qtb.setToolTip(QtCore.QCoreApplication.translate('LolEvt', "Open Show-Layer attribute-form"))
                        qtb.clicked.connect(self.s_open_show_form_by_edit_pk)
                        qtb.setProperty("edit_pk", edit_pk)
                        qtb.setFixedSize(QtCore.QSize(20, 20))
                        c_wdg.layout().addWidget(qtb)
                        self.my_dialogue.qtw_selected_pks.setCellWidget(rc, cc, c_wdg)

                    rc += 1

                self.dlg_0 = tools.MyQtWidgets.LambdaDelegate(lambda val: " " * 30 + str(val))
                self.my_dialogue.qtw_selected_pks.setItemDelegateForColumn(0, self.dlg_0)
                self.dlg_1 = tools.MyQtWidgets.LambdaDelegate(lambda val: " " * 25 + str(val))
                self.my_dialogue.qtw_selected_pks.setItemDelegateForColumn(1, self.dlg_1)

                if self.cf.show_layer_complete:
                    # only one icon => less padding
                    self.dlg_3 = tools.MyQtWidgets.LambdaDelegate(lambda val: " " * 10 + str(val))
                    self.my_dialogue.qtw_selected_pks.setItemDelegateForColumn(4, self.dlg_3)

                self.my_dialogue.qtw_selected_pks.resizeRowsToContents()
                self.my_dialogue.qtw_selected_pks.resizeColumnsToContents()

                # restore previous sort-settings
                self.my_dialogue.qtw_selected_pks.sortItems(prev_sort_col_idx, prev_sort_order)

            self.my_dialogue.pbtn_select_features.setEnabled(
                self.cf.reference_layer_complete and
                self.cf.data_layer_complete and
                self.cf.show_layer_complete
            )
            self.my_dialogue.pbtn_clear_features.setEnabled(
                self.cf.reference_layer_complete and
                self.cf.data_layer_complete and
                len(self.rs.selected_pks) > 0
            )
            self.my_dialogue.pbtn_zoom_to_feature_selection.setEnabled(
                self.cf.reference_layer_complete and
                self.cf.data_layer_complete and
                len(self.rs.selected_pks) > 0
            )
            self.my_dialogue.pbtn_insert_all_features.setEnabled(
                self.cf.reference_layer_complete and
                self.cf.data_layer_complete
            )
            self.my_dialogue.pbtn_insert_selected_data_features.setEnabled(
                self.cf.reference_layer_complete and
                self.cf.data_layer_complete
            )
            self.my_dialogue.pbtn_insert_selected_show_features.setEnabled(
                self.cf.reference_layer_complete and
                self.cf.data_layer_complete and
                self.cf.show_layer_complete
            )

    def s_open_data_form(self):
        """opens data-form for dataLyr from selection-list-cell-widget, edit_pk stored as property"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')
        data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
        if data_feature and data_feature.isValid():
            self.iface.openFeatureForm(self.ds.dataLyr, data_feature, True)
        else:
            self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "no feature with ID {apos}{0}{apos} in Data-Layer {apos}{1}{apos}"), edit_pk, self.ds.dataLyr.name()))

    def s_highlight_edit_pk(self):
        """select for edit and pan to Feature from selection-list-cell-widget, edit_pk stored as property"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')
        self.set_edit_pk(edit_pk, False)

    def s_remove_from_feature_selection(self):
        """removes this feature/row from self.rs.selected_pks/selection-list, edit_pk stored as property in cell-widget"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')

        if edit_pk in self.rs.selected_pks:
            self.rs.selected_pks.remove(edit_pk)
            self.dlg_refresh_feature_selection_section()

        if edit_pk == self.rs.edit_pk:
            self.rs.edit_pk = None
            self.dlg_refresh_edit_section()

    def s_pan_edit_pk(self):
        """edit and pan to feature from selction-list"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')
        self.set_edit_pk(edit_pk, True)

    def s_open_show_form_by_edit_pk(self):
        """opens feature-form for showLyr from selection-list, edit_pk stored as property in cell-widget"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')
        data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
        if data_feature and data_feature.isValid():
            show_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.showLyr, self.ds.showLyrBackReferenceField, edit_pk)
            if show_feature and show_feature.isValid():
                self.iface.openFeatureForm(self.ds.showLyr, show_feature, True)
            else:
                self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "no feature with value {apos}{0}{apos} in Back-Reference-field {apos}{1}{apos} of Show-Layer {apos}{2}{apos}"), edit_pk, self.ds.showLyrBackReferenceField.name(), self.ds.showLyr.name()))

    def s_open_ref_form_by_edit_pk(self):
        """opens feature-form for refLyr from selection-list, edit_pk stored as property in cell-widget"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')
        data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
        if data_feature and data_feature.isValid():
            ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, data_feature[self.ds.dataLyrReferenceField.name()])
            if ref_feature and ref_feature.isValid():
                self.iface.openFeatureForm(self.ds.refLyr, ref_feature, True)
            else:
                self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "no feature with value {apos}{0}{apos} in field {apos}{1}{apos} of Data-Layer {apos}{2}{apos}"), data_feature[self.ds.dataLyrReferenceField.name()], self.ds.dataLyrReferenceField.name(), self.ds.refLyr.name()))

    def s_highlight_ref_feature_by_edit_pk(self):
        """highlights referenced line-feature from selection-list, edit_pk stored as property in cell-widget"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')
        data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
        if data_feature and data_feature.isValid():
            ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, data_feature[self.ds.dataLyrReferenceField.name()])
            if ref_feature and ref_feature.isValid():
                if ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                    self.rb_ref.setToGeometry(ref_feature.geometry(), self.ds.refLyr)
                    self.rb_ref.show()
                else:
                    self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Feature without geometry (Reference-Layer {apos}{0}{apos}, field {apos}{1}{apos}, value {apos}{3}{apos})"), self.ds.refLyr.name(), self.ds.dataLyrReferenceField.name(), data_feature[self.ds.dataLyrReferenceField.name()]))
            else:
                self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "no feature with value {apos}{0}{apos} in field {apos}{1}{apos} of Reference-Layer {apos}{2}{apos}"), data_feature[self.ds.dataLyrReferenceField.name()], self.ds.dataLyrReferenceField.name(), self.ds.refLyr.name()))

    def s_zoom_ref_feature_by_edit_pk(self):
        """highlight and zoom to referenced line-feature from selection-list, edit_pk stored as property in cell-widget"""
        # Rev. 2023-05-03
        edit_pk = self.sender().property('edit_pk')
        data_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.dataLyr, self.ds.dataLyrIdField, edit_pk)
        if data_feature and data_feature.isValid():
            ref_feature = tools.MyToolFunctions.get_feature_by_value(self.ds.refLyr, self.ds.refLyrPkField, data_feature[self.ds.dataLyrReferenceField.name()])
            if ref_feature and ref_feature.isValid():
                if ref_feature.hasGeometry() and not ref_feature.geometry().isEmpty():
                    extent = ref_feature.geometry().boundingBox()
                    source_crs = self.ds.refLyr.crs()
                    target_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
                    tr = qgis.core.QgsCoordinateTransform(source_crs, target_crs, qgis.core.QgsProject.instance())
                    extent = tr.transformBoundingBox(extent)
                    self.iface.mapCanvas().setExtent(extent)
                    self.iface.mapCanvas().zoomByFactor(1.1)
                    self.rb_ref.setToGeometry(ref_feature.geometry(), self.ds.refLyr)
                    self.rb_ref.show()
                else:
                    self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "Feature without geometry (Reference-Layer {apos}{0}{apos}, field {apos}{1}{apos}, value {apos}{2}{apos})"), self.ds.refLyr.name(), self.ds.dataLyrReferenceField.name(), data_feature[self.ds.dataLyrReferenceField.name()]))
        else:
            self.push_messages(warning_msg=qt_format(QtCore.QCoreApplication.translate('LolEvt', "no feature with value {apos}{0}{apos} in field {apos}{1}{apos} of Reference-Layer {apos}{2}{apos}"), data_feature[self.ds.dataLyrReferenceField.name()], self.ds.dataLyrReferenceField.name(), self.ds.refLyr.name()))

    def store_settings(self):
        """store all permanent settings to project
        the "internal" values (with underscores) are stored (with underscores too) and restored later
        the project must be saved to store these settings in project-file!
        """

        # Rev. 2023-04-27
        # filter: startswith('_')
        # => use "hidden" properties, not their property-setters
        # and not callable(getattr(self.ss, prop))
        property_dict = {prop: getattr(self.ss, prop) for prop in dir(self.StoredSettings) if prop.startswith('_') and not prop.startswith('__')}

        for prop_name in property_dict:
            prop_value = property_dict[prop_name]
            # other key then PolEvt
            key = f"/LolEvt/{prop_name}"
            qgis.core.QgsProject.instance().writeEntry('LinearReferencing', key, prop_value)

        # additional store settings in the dataLyr, so each dataLyr can have its own individual settings and switching the dataLyr in dialog restores these
        # if self.ds.dataLyr:
        #     self.ds.dataLyr.setCustomProperty("LolEvt", property_dict)

    def clear_layer_actions(self):
        """remove Plugin-Layer-Actions from Vector-Layers
        .. Note::
            * no table refresh => reopen table/form necessary
            * attributeTableConfig.setActionWidgetVisible(True) will be unchanged
        """
        # Rev. 2023-05-08
        vlayers = [layer for layer in qgis.core.QgsProject.instance().mapLayers().values() if isinstance(layer, qgis.core.QgsVectorLayer)]
        for vlayer in vlayers:
            # action-id is not unique, layer can have multiple actions with identical id
            action_list = [action for action in vlayer.actions().actions() if action.id() in [self._lyr_act_id_1, self._lyr_act_id_2]]
            for action in action_list:
                vlayer.actions().removeAction(action.id())

    def unload(self):
        """triggered by LinearReference => unload() and project.close()"""
        # Rev. 2023-04-27

        # check and write the settings back to project
        self.check_settings()
        self.store_settings()

        self.disconnect_all_layers()
        try:

            # remove canvas-graphics
            self.iface.mapCanvas().scene().removeItem(self.vm_pt_measure_from)
            del self.vm_pt_measure_from
            self.iface.mapCanvas().scene().removeItem(self.vm_pt_measure_to)
            del self.vm_pt_measure_to
            self.iface.mapCanvas().scene().removeItem(self.rb_segment)
            del self.rb_segment
            self.iface.mapCanvas().scene().removeItem(self.rb_ref)
            del self.rb_ref
            self.iface.mapCanvas().scene().removeItem(self.rb_selection_rect)
            del self.rb_selection_rect

            # remove dialog
            self.my_dialogue.close()
            del self.my_dialogue
        except Exception as e:
            # AttributeError: 'PolEvt' object has no attribute 'vm_pt_measure'
            # print(f"Expected exception in {gdp()}: \"{e}\"")
            pass

    def flags(self):
        """reimplemented:
        here: make ShiftModifier available for tool_mode 'select_features'
        default: zoom to the dragged rectangle when Shift-Key is holded
        see: https://gis.stackexchange.com/questions/449523/override-the-zoom-behaviour-of-qgsmaptoolextent"""
        # Rev. 2023-05-08
        return super().flags() & ~qgis.gui.QgsMapToolEmitPoint.AllowZoomRect
