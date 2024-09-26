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

# Rev. 2024-06-15


from __future__ import annotations
import datetime
import math
import os
import osgeo
import qgis
import sys
import numbers
import typing
import urllib
import collections
import copy
from enum import Flag, auto
import re
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from LinearReferencing import tools, dialogs
from LinearReferencing.tools.MyTools import PoLFeature, LoLFeature
from LinearReferencing.qt import MyQtWidgets
from LinearReferencing.tools.MyDebugFunctions import debug_log, debug_print, get_debug_pos, get_debug_file_line
from LinearReferencing.i18n.SQLiteDict import SQLiteDict
# global variable
MY_DICT = SQLiteDict()


class SessionData:
    """Template for self.session_data: Session-Data"""
    # Rev. 2024-06-15

    # currently selected toolmode, will affect the canvasMove/Press/Release-Events
    # list of available tool_modes see self::tool_modes
    tool_mode = None

    # the previous selected toolmode, switch-back-by-canvas-click-convenience for tool_mode 'pausing'
    previous_tool_mode = None

    # int: fid of the current selected/snapped reference-line
    current_ref_fid = None

    # int: fid which reference-line is currently highlighted, for toggle-functionality, independend from current_ref_fid
    highlighted_ref_fid = None

    # measure-result for mouse-press/release events on canvas, type POL, special for move-actions, sometimes used as flag
    pol_mouse_down = None
    pol_mouse_move = None
    pol_mouse_up = None

    # runtime for editing these points independend but synchronized with measure_feature
    pol_from = None
    pol_to = None

    # runtime-feature from measure-result
    # no data-fid
    # used for inserts
    # type LoLFeature
    measure_feature = None

    # selected feature from feature-selection, mostly for edit-purpose, type LoLFeature
    edit_feature = None

    # current selected post-processing-Feature, type LoLFeature
    # po_pro_cached_feature available via self.session_data.po_pro_data_cache[po_pro_feature.data_fid]
    # po_pro_cached_geom available via self.session_data.po_pro_reference_cache[po_pro_feature.ref_fid]
    po_pro_feature = None

    # list of selected Data-Layer-fids (integers) for "Feature-Selection"
    selected_fids = []

    # dictionary for cached data-features, key = fid of data-layer, value collections.namedtuple with properties StationingN and StationingM
    po_pro_data_cache = {}

    # dictionary of cached geometries, key = fid of reference-layer, value original version of geometry
    po_pro_reference_cache = {}

    # offset for new self.session_data.measure_feature, displayed in self.my_dialog.dspbx_offset
    current_offset = 0

    def __str__(self):
        """stringify implemented for debug-purpose"""
        # Rev. 2024-06-15
        result_str = ''
        property_list = [prop for prop in dir(self) if not prop.startswith('__') and not callable(getattr(self, prop))]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str


class FVS(Flag):
    """
    FeatureValidState for stored LoL-Features
    Constraint-like check of linear-referenced-stationings: binary flag
    positive-flag: Each bit symbolizes a special kind of requirement
    Note: checks of instances are done in range of the auto()-value
    """
    # Rev. 2024-06-15
    INIT = auto()

    DATA_FEATURE_EXISTS = auto()
    REFERENCE_ID_VALID = auto()

    REFERENCE_FEATURE_EXISTS = auto()
    REFERENCE_GEOMETRY_EXIST = auto()

    # complex group-parameter, depends on lrMode und single/multi/mergeable geometries
    REFERENCE_GEOMETRY_VALID = auto()

    # Note: Features outside range are drawn nevertheless in the virtual layers at start-point rsp. end-point of the referenced features
    STATIONING_FROM_NUMERIC = auto()
    STATIONING_TO_NUMERIC = auto()
    STATIONING_FROM_INSIDE_RANGE = auto()
    STATIONING_TO_INSIDE_RANGE = auto()
    STATIONING_FROM_LTEQ_TO = auto()

    OFFSET_NUMERIC = auto()

    # Check-results, done in range of the auto()-value (binary: bitwise from right to left), stopping on first error
    is_valid = True
    first_fail_flag = None

    def check_data_feature_valid(self):
        """full-check validity of the current data-feature
        sets is_valid rsp. first_fail_flag
        """
        # Rev. 2024-06-15

        check_params = (
                self.__class__.INIT |
                self.__class__.DATA_FEATURE_EXISTS |
                self.__class__.REFERENCE_GEOMETRY_VALID |
                self.__class__.STATIONING_FROM_NUMERIC |
                self.__class__.STATIONING_FROM_INSIDE_RANGE |
                self.__class__.STATIONING_TO_NUMERIC |
                self.__class__.STATIONING_TO_INSIDE_RANGE |
                self.__class__.STATIONING_FROM_LTEQ_TO |
                self.__class__.OFFSET_NUMERIC
        )

        self.check(check_params)

    def check(self, required_flags):
        """compares self with a required state
        sets is_valid rsp. first_fail_flag
        :param required_flags: | combination of the required flag-values
        """
        # Rev. 2024-06-15

        # global check for all required flags, stop on first failure
        self.is_valid = required_flags in self
        if not self.is_valid:
            for item in self.__class__:
                # iterate over all possible single-flags up to first failure flag
                # single-flags see http://graphics.stanford.edu/~seander/bithacks.html#DetermineIfPowerOf2)
                if item.value and (item.value & (item.value - 1)) == 0:
                    if (item & required_flags) and not (item & self):
                        self.first_fail_flag = item.name
                        break

    def __str__(self):
        """stringify implemented for debug-purpose"""
        # Rev. 2024-06-15
        result_str = ''
        property_list = [prop for prop in dir(self) if not prop.startswith('__') and not callable(getattr(self, prop))]
        item_list = [item.name for item in self.__class__ if item.value and (item.value & (item.value - 1)) == 0]

        longest_prop = max(property_list, key=len)
        longest_item = max(item_list, key=len)

        max_len = max(len(longest_prop), len(longest_item))

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        for item in self.__class__:
            # iterate over all possible single-flags up to first failure flag
            # single-flags see http://graphics.stanford.edu/~seander/bithacks.html#DetermineIfPowerOf2)
            if item.value and (item.value & (item.value - 1)) == 0:
                if (item & self):
                    result_str += f"{item.name:<{max_len}} => 1 \n"
                else:
                    result_str += f"{item.name:<{max_len}} => 0 \n"

        return result_str


class DerivedSettings:
    """template for self.derived_settings,
    parsed from self.stored_settings (key strings like Layer-IDs, Field-Names)
    to QGis/Qt-Objects (QgsVectorLayer, QgsField)"""
    # Rev. 2024-06-18
    refLyr = None
    refLyrIdField = None
    dataLyr = None
    dataLyrIdField = None
    dataLyrReferenceField = None
    dataLyrStationingFromField = None
    dataLyrStationingToField = None
    dataLyrOffsetField = None
    showLyr = None
    showLyrBackReferenceField = None


class StoredSettings:
    """template for self.stored_settings -> stored settings
    alphanumeric values like layer-IDs, colors, sizes, stored in QGis-Project
    all properties starting with single '_' are stored to project-settings rsp. to project file
    partially defined with property-getter-and-setter to register any user-setting-changes,
    which then set the QGis-Project "dirty" and have these changes stored on sys_store_settings with save
    so every write-access to these properties, that should not set the "dirty"-Flag, must be done to the _internal-properties
    see store/sys_restore_settings()
    """
    # Rev. 2024-06-18

    # linear-reference-mode
    # how are stationings calculated?
    # variants:
    # Nabs N natural with absolute stationings => data-layer with 2 numerical columns from/to 0...reference-line length
    # Mabs M measured with Vertex-M-values => data-layer with 2 numerical columns from/to
    # Nfract natural with relative stationings => data-layer with 2 numerical columns from/to 0...1 fraction of the reference-line length
    # perhaps extended in later releases
    _lrMode = 'Nabs'

    @property
    def lrMode(self):
        return self._lrMode

    @lrMode.setter
    def lrMode(self, value):
        self._lrMode = value
        qgis.core.QgsProject.instance().setDirty(True)

    # ID of the used reference-layer
    _refLyrId = None

    @property
    def refLyrId(self):
        return self._refLyrId

    @refLyrId.setter
    def refLyrId(self, value):
        self._refLyrId = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Name of the ID-Field in reference-layer
    _refLyrIdFieldName = None

    @property
    def refLyrIdFieldName(self):
        return self._refLyrIdFieldName

    @refLyrIdFieldName.setter
    def refLyrIdFieldName(self, value):
        self._refLyrIdFieldName = value
        qgis.core.QgsProject.instance().setDirty(True)

    # ID of data-layer
    _dataLyrId = None

    @property
    def dataLyrId(self):
        return self._dataLyrId

    @dataLyrId.setter
    def dataLyrId(self, value):
        self._dataLyrId = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Name of ID-Field in data-layer
    _dataLyrIdFieldName = None

    @property
    def dataLyrIdFieldName(self):
        return self._dataLyrIdFieldName

    @dataLyrIdFieldName.setter
    def dataLyrIdFieldName(self, value):
        self._dataLyrIdFieldName = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Name of n:1 reference-Field from data-layer to reference-layer
    _dataLyrReferenceFieldName = None

    @property
    def dataLyrReferenceFieldName(self):
        return self._dataLyrReferenceFieldName

    @dataLyrReferenceFieldName.setter
    def dataLyrReferenceFieldName(self, value):
        self._dataLyrReferenceFieldName = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Name of the data-layer-field for stationing_n
    _dataLyrStationingFromFieldName = None

    @property
    def dataLyrStationingFromFieldName(self):
        return self._dataLyrStationingFromFieldName

    @dataLyrStationingFromFieldName.setter
    def dataLyrStationingFromFieldName(self, value):
        self._dataLyrStationingFromFieldName = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Name of the data-layer-field for stationing_n
    _dataLyrStationingToFieldName = None

    @property
    def dataLyrStationingToFieldName(self):
        return self._dataLyrStationingToFieldName

    @dataLyrStationingToFieldName.setter
    def dataLyrStationingToFieldName(self, value):
        self._dataLyrStationingToFieldName = value
        qgis.core.QgsProject.instance().setDirty(True)

    _dataLyrOffsetFieldName = None

    @property
    def dataLyrOffsetFieldName(self):
        """Name of Stationing-Tp-Field in Data-Layer"""
        return self._dataLyrOffsetFieldName

    @dataLyrOffsetFieldName.setter
    def dataLyrOffsetFieldName(self, value):
        self._dataLyrOffsetFieldName = value
        qgis.core.QgsProject.instance().setDirty(True)

    # ID of (mostly virtual) show-layer
    _showLyrId = None

    @property
    def showLyrId(self):
        return self._showLyrId

    @showLyrId.setter
    def showLyrId(self, value):
        self._showLyrId = value
        qgis.core.QgsProject.instance().setDirty(True)

    # 1:1-reference-field between show- and data-layer, usually the PK-Fields in both layers
    _showLyrBackReferenceFieldName = None

    @property
    def showLyrBackReferenceFieldName(self):
        return self._showLyrBackReferenceFieldName

    @showLyrBackReferenceFieldName.setter
    def showLyrBackReferenceFieldName(self, value):
        self._showLyrBackReferenceFieldName = value
        qgis.core.QgsProject.instance().setDirty(True)

    # storage-precision, stationings will get rounded
    _storagePrecision = -1

    @property
    def storagePrecision(self):
        if self._storagePrecision is None:
            self._storagePrecision = -1
        return int(self._storagePrecision)

    @storagePrecision.setter
    def storagePrecision(self, value):
        self._storagePrecision = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # Symbolization with temporal canvas-graphics

    # line-style for highlighted reference-line
    _ref_line_style = 3

    @property
    def ref_line_style(self):
        return int(self._ref_line_style)

    @ref_line_style.setter
    def ref_line_style(self, value):
        self._ref_line_style = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # line-style for highlighted reference-line
    _segment_line_style = 1

    @property
    def segment_line_style(self):
        return int(self._segment_line_style)

    @segment_line_style.setter
    def segment_line_style(self, value):
        self._segment_line_style = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # line-width for highlighted reference-line
    _ref_line_width = 2

    @property
    def ref_line_width(self):
        return int(self._ref_line_width)

    @ref_line_width.setter
    def ref_line_width(self, value):
        self._ref_line_width = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # line-width for LoL-segment
    _segment_line_width = 11

    @property
    def segment_line_width(self):
        return int(self._segment_line_width)

    @segment_line_width.setter
    def segment_line_width(self, value):
        self._segment_line_width = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # line-color for highlighted reference-line
    _ref_line_color = '#96ffff7f'  # semi-transparent yellow

    @property
    def ref_line_color(self):
        return self._ref_line_color

    @ref_line_color.setter
    def ref_line_color(self, value):
        self._ref_line_color = value
        qgis.core.QgsProject.instance().setDirty(True)

    # line-color for LoL-segment
    _segment_line_color = '#FF8C00'  # DarkOrange

    @property
    def segment_line_color(self):
        return self._segment_line_color

    @segment_line_color.setter
    def segment_line_color(self, value):
        self._segment_line_color = value
        qgis.core.QgsProject.instance().setDirty(True)

    # line-color for Show-Layer, mint-green
    # not customizable, but layer can be styled as any other vector-layer
    # applied with opactity 0.8
    # different to segment_line_color
    _show_layer_default_line_color = '#90EE90'  # LightGreen

    @property
    def show_layer_default_line_color(self):
        return self._show_layer_default_line_color

    @show_layer_default_line_color.setter
    def show_layer_default_line_color(self, value):
        self._show_layer_default_line_color = value
        qgis.core.QgsProject.instance().setDirty(True)

    # symbolize a stationing_n on a line
    # Icon-Type for Stationing-Canvas-Graphic
    # 3 => Box
    _pt_snf_icon_type = 3

    @property
    def pt_snf_icon_type(self):
        return int(self._pt_snf_icon_type)

    @pt_snf_icon_type.setter
    def pt_snf_icon_type(self, value):
        self._pt_snf_icon_type = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    _pt_snt_icon_type = 3

    @property
    def pt_snt_icon_type(self):
        return int(self._pt_snt_icon_type)

    @pt_snt_icon_type.setter
    def pt_snt_icon_type(self, value):
        self._pt_snt_icon_type = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # Size for Stationing-Canvas-Graphic
    _pt_snf_icon_size = 16

    @property
    def pt_snf_icon_size(self):
        return int(self._pt_snf_icon_size)

    @pt_snf_icon_size.setter
    def pt_snf_icon_size(self, value):
        self._pt_snf_icon_size = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # Size for Stationing-Canvas-Graphic
    _pt_snt_icon_size = 16

    @property
    def pt_snt_icon_size(self):
        return int(self._pt_snt_icon_size)

    @pt_snt_icon_size.setter
    def pt_snt_icon_size(self, value):
        self._pt_snt_icon_size = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # Size for Stationing-Canvas-Graphic

    # Pen-Width for Stationing-Canvas-Graphic == outline-width
    _pt_snf_pen_width = 3

    @property
    def pt_snf_pen_width(self):
        return int(self._pt_snf_pen_width)

    @pt_snf_pen_width.setter
    def pt_snf_pen_width(self, value):
        self._pt_snf_pen_width = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # Pen-Width for Stationing-Canvas-Graphic == outline-width
    _pt_snt_pen_width = 3

    @property
    def pt_snt_pen_width(self):
        return int(self._pt_snt_pen_width)

    @pt_snt_pen_width.setter
    def pt_snt_pen_width(self, value):
        self._pt_snt_pen_width = int(value)
        qgis.core.QgsProject.instance().setDirty(True)

    # Color for Stationing-Canvas-Graphic == outine-color
    # also used as initial fill-color for show-layer-n
    _pt_snf_color = '#FF00FF00'  # lime

    @property
    def pt_snf_color(self):
        return self._pt_snf_color

    @pt_snf_color.setter
    def pt_snf_color(self, value):
        self._pt_snf_color = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Color for Stationing-Canvas-Graphic == outine-color
    # also used as initial fill-color for show-layer-n
    _pt_snt_color = '#FFFF0000'  # red

    @property
    def pt_snt_color(self):
        return self._pt_snt_color

    @pt_snt_color.setter
    def pt_snt_color(self, value):
        self._pt_snt_color = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Fill-Color for Stationing-Canvas-Graphic
    _pt_snf_fill_color = '#00ffffff'  # white transparent

    @property
    def pt_snf_fill_color(self):
        return self._pt_snf_fill_color

    @pt_snf_fill_color.setter
    def pt_snf_fill_color(self, value):
        self._pt_snf_fill_color = value
        qgis.core.QgsProject.instance().setDirty(True)

    # Fill-Color for Stationing-Canvas-Graphic
    _pt_snt_fill_color = '#00ffffff'  # white transparent

    @property
    def pt_snt_fill_color(self):
        return self._pt_snt_fill_color

    @pt_snt_fill_color.setter
    def pt_snt_fill_color(self, value):
        self._pt_snt_fill_color = value
        qgis.core.QgsProject.instance().setDirty(True)


# QgsMapToolEmitPoint
class LolEvt(qgis.gui.QgsMapToolEmitPoint):
    """MapTool for Digitize Point-Events via reference-line and measured run-lengths
    to startpoint and endpoint"""
    # Rev. 2024-06-18

    # Nomenclature, functions beginning with...
    # cvs_* => canvas-functions, draw, pan, zoom...
    # cpe_xxx => canvasPressEvent-sub-function, xxx => self.session_data.tool_mode
    # cme_xxx => canvasMoveEvent-sub-function, xxx => self.session_data.tool_mode
    # cre_xxx => canvasReleaseEvent-sub-function, xxx => self.session_data.tool_mode
    # dlg_* => dialog-functions, refresh parts of dialog...
    # gui_* => gui-functions, e.g. layer-actions
    # fvs* => check of feature-valid-state, stationing_n valid? referenced feature existing? see FVS
    # s_* => slot-functions triggered by widgets in dialog
    # ssc_* => slot-functions for configuration-change affecting stored_settings
    # st_* => slot-functions triggered from tabular widgets inside dialog
    # stm_* => functions to set a new tool-mode
    # sys_* => system functions
    # tool_* => auxiliary functions

    # the dialog for this MapTool as class-variable and later initialized as instance-variable
    my_dialog = None

    # log-message-count, incremented with dlg_append_log_message
    lmc = 0

    # IDs for identifying and later remove of the layer-actions in dataLyr and showLyr
    _showLyr_act_id = QtCore.QUuid('12345678-abcd-4321-dcba-0123456789ab')
    _dataLyr_act_id = QtCore.QUuid('87654321-dcba-1234-abcd-ba9876543210')

    # a limited number of settings can be stored in and restored from the project-file
    # (registered layers/fields, colors, symbols...)
    _num_storable_settings = 100

    # max number of registered post-processing reference-features, whose geometries are cached in a dictionary, to avoid overflow
    _po_pro_max_ref_feature_count = 100

    # max number of post-processing-features to avoid overflow
    _po_pro_max_feature_count = 500

    def dlg_append_log_message(self, message_type: str, message_content: str, show_status_message: bool = True):
        """appends log-message to self.dialogue.qtw_log_messages
        adds file-name and line-number for debug-convenience
        different message-types are displayed with different durations
        :param message_type: INFO/SUCCESS/WARNING/CRITICAL, implemented with specific background-colors
        :param message_content:
        :param show_status_message: additional show in dialog-status-bar
        """
        # Rev. 2024-06-18
        if self.my_dialog:
            # counter-variable and message-range
            self.lmc += 1

            # debug-info
            file, line, function = get_debug_file_line(2)

            base_font = QtGui.QFont()

            # ExtraBold to symbolize the new messages, can be set to normal for all existing messages font via dlg_check_log_messages
            bold_font = QtGui.QFont(base_font)
            bold_font.setPointSize(10)
            bold_font.setWeight(81)

            lmc_item = QtGui.QStandardItem()
            lmc_item.setData(self.lmc, 0)
            lmc_item.setData(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter, QtCore.Qt.TextAlignmentRole)
            lmc_item.setData(bold_font, QtCore.Qt.FontRole)

            time_item = QtGui.QStandardItem()
            time_item.setData(QtCore.QDateTime.currentDateTime(), 0)
            time_item.setData(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter, QtCore.Qt.TextAlignmentRole)
            time_item.setData(bold_font, QtCore.Qt.FontRole)

            file_item = QtGui.QStandardItem()
            file_item.setData(os.path.basename(file), 0)
            file_item.setData(file, QtCore.Qt.ToolTipRole)
            file_item.setData(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight, QtCore.Qt.TextAlignmentRole)
            file_item.setData(bold_font, QtCore.Qt.FontRole)

            function_item = QtGui.QStandardItem()
            function_item.setData(function, 0)
            function_item.setData(function, QtCore.Qt.ToolTipRole)
            function_item.setData(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight, QtCore.Qt.TextAlignmentRole)
            function_item.setData(bold_font, QtCore.Qt.FontRole)

            line_item = QtGui.QStandardItem()
            line_item.setData(line, 0)
            line_item.setData(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight, QtCore.Qt.TextAlignmentRole)
            line_item.setData(bold_font, QtCore.Qt.FontRole)

            level_item = QtGui.QStandardItem()
            level_item.setData(message_type, 0)
            level_item.setData(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter, QtCore.Qt.TextAlignmentRole)
            level_item.setData(bold_font, QtCore.Qt.FontRole)

            # different background-colors to symbolize message-type
            if message_type == 'WARNING':
                level_item.setBackground(QtGui.QColor('#FFB839'))
            elif message_type == 'SUCCESS':
                level_item.setBackground(QtGui.QColor('#B9FFBD'))
            elif message_type == 'INFO':
                level_item.setBackground(QtGui.QColor('#AFC8FF'))
            elif message_type == 'CRITICAL':
                level_item.setBackground(QtGui.QColor('#FF3939'))

            message_item = QtGui.QStandardItem()
            message_item.setData(message_content, 0)
            message_item.setData(bold_font, QtCore.Qt.FontRole)

            self.my_dialog.qtw_log_messages.model().appendRow([lmc_item, time_item, level_item, message_item, file_item, line_item, function_item])

            # count "uncommitted" messages => font-weight bold in TableView
            ucc = 0
            for rc in range(self.my_dialog.qtw_log_messages.model().rowCount()):
                item_0 = self.my_dialog.qtw_log_messages.model().item(rc, 0)
                if item_0.data(QtCore.Qt.FontRole) != QtGui.QFont():
                    ucc += 1

            # refresh the tab-text with the number of new messages
            self.my_dialog.tbw_central.tabBar().setTabText(4, MY_DICT.tr('log_tab') + ' *' + str(ucc))

            if message_type == 'WARNING':
                # symbolize with red tab-text-color
                self.my_dialog.tbw_central.tabBar().setTabTextColor(4, QtGui.QColor('red'))

            elif message_type == 'CRITICAL':
                # symbolize with red tab-text-color
                self.my_dialog.tbw_central.tabBar().setTabTextColor(4, QtGui.QColor('red'))
                #  and open the message-log-tab
                self.my_dialog.tbw_central.setCurrentIndex(4)

            # vorhergehende Sortierung wiederherstellen
            self.my_dialog.qtw_log_messages.sortByColumn(self.my_dialog.qtw_log_messages.horizontalHeader().sortIndicatorSection(), self.my_dialog.qtw_log_messages.horizontalHeader().sortIndicatorOrder())
            self.my_dialog.qtw_log_messages.resizeRowsToContents()
            self.my_dialog.qtw_log_messages.resizeColumnsToContents()

            # Additional output to Dialog-Status-Bar
            if show_status_message:
                self.dlg_show_status_message(message_type, message_content)

    def dlg_clear_log_messages(self):
        """method clears qtw_log_messages and resets tabText-content and -color"""
        # Rev. 2024-06-18
        self.my_dialog.qtw_log_messages.model().removeRows(0, self.my_dialog.qtw_log_messages.model().rowCount())
        self.my_dialog.tbw_central.tabBar().setTabText(4, MY_DICT.tr('log_tab'))
        self.my_dialog.tbw_central.tabBar().setTabTextColor(4, QtGui.QColor('black'))

    def dlg_check_log_messages(self):
        """method removes bold-font from new appended messages and resets tabText-content and -color"""
        # Rev. 2024-06-18
        for rc in range(self.my_dialog.qtw_log_messages.model().rowCount()):
            for cc in range(self.my_dialog.qtw_log_messages.model().columnCount()):
                # apply default-font
                item = self.my_dialog.qtw_log_messages.model().item(rc, cc)
                item.setData(QtGui.QFont(), QtCore.Qt.FontRole)

        # reset tab-text (remove *number of new messages)
        self.my_dialog.tbw_central.tabBar().setTabText(4, MY_DICT.tr('log_tab'))
        # reset possibly red-tab-text-color of last WARNING or WARNING-Message
        self.my_dialog.tbw_central.tabBar().setTabTextColor(4, QtGui.QColor('black'))

    def __init__(self, iface: qgis.gui.QgisInterface):
        """initialize this mapTool
        :param iface: interface to QgisApp
        """
        # Rev. 2024-06-18
        qgis.gui.QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())

        # iface for access to QGis-Qt-Application
        self.iface = iface

        # nested dictionary, register for each plugin-connected layer-signal (data-layer, reference-layer, show-layer)
        # to avoid double-connect and ensure later disconnect
        # keys: layer_id > conn_signal > conn_function => conn_id
        self.signal_slot_cons = {}

        # list of application-slot-connections, which have to be disconnected on unload, f. e. add/remove layer
        self.application_slot_cons = []

        # list of canvas-slot-connections, which have to be disconnected on unload, f. e. change of canvas projection
        self.canvas_slot_cons = []

        # qgis.gui.QgsSnapIndicator: tiny snap-icon
        # must be stored as reference
        # any access to qgis.gui.QgsSnapIndicator(self.iface.mapCanvas()) will not affect self.snap_indicator
        # the icon is used with some canvasMoveEvents
        self.snap_indicator = qgis.gui.QgsSnapIndicator(self.iface.mapCanvas())

        # role for the data_fid in self.my_dialog.qtrv_feature_selection.model()
        self.data_fid_role = 257

        # role for the ref_fid in self.my_dialog.qcbn_reference_feature
        self.ref_fid_role = 258

        # role for the label of the stored configuration in self.my_dialog.lw_stored_settings
        self.configuration_label_role = 259

        # role for the column-sort in self.my_dialog.qtrv_feature_selection.model(), see QTableWidgetItemCustomSort
        self.custom_sort_role = 260

        # role for the show_fid in self.my_dialog.qtrv_feature_selection.model()
        self.show_fid_role = 261

        # role for some QComboBoxes in the settings-section, which hold the settings-key-value (layers, fields, line-styles, line-widths, symbol-types etc.)
        # uses Qt.UserRole == 256 for simplicity, because this role is used by
        # QComboBox.addItem(const QString &text, const QVariant &userData = QVariant())
        # and as default for QComboBox.currentData(int role = Qt::UserRole)
        self.setting_key_role = 256

        # possible values for runtime_settings.tool_mode, key: runtime_settings.tool_mode, value: Explanation for status-bar, translated
        self.tool_modes = {
            'initialized': MY_DICT.tr('lol_toolmode_initialized'),
            'pausing': MY_DICT.tr('lol_toolmode_pausing'),
            'set_from_point': MY_DICT.tr('lol_toolmode_set_from_point'),
            'set_to_point': MY_DICT.tr('lol_toolmode_set_to_point'),
            'measure_segment': MY_DICT.tr('lol_toolmode_measure_segment'),
            'select_features': MY_DICT.tr('lol_toolmode_select_features'),
            'set_feature_from_point': MY_DICT.tr('lol_toolmode_set_feature_from_point'),
            'set_feature_to_point': MY_DICT.tr('lol_toolmode_set_feature_to_point'),
            'set_po_pro_from_point': MY_DICT.tr('lol_toolmode_set_po_pro_from_point'),
            'set_po_pro_to_point': MY_DICT.tr('lol_toolmode_set_po_pro_to_point'),
            'move_segment': MY_DICT.tr('lol_toolmode_move_segment'),
            'change_offset': MY_DICT.tr('lol_toolmode_change_offset'),
            'change_feature_offset': MY_DICT.tr('lol_toolmode_change_feature_offset'),
            'move_feature': MY_DICT.tr('lol_toolmode_move_feature'),
            'redigitize_feature': MY_DICT.tr('lol_toolmode_redigitize_feature'),
            'move_po_pro_feature': MY_DICT.tr('lol_toolmode_move_po_pro_feature'),

        }

        self.system_vs = self.SVS.INIT

        # initialize the settings-"containers" with blank "templates"
        self.stored_settings = StoredSettings()
        self.derived_settings = DerivedSettings()
        self.session_data = SessionData()

        # restore settings from last usage in this project
        self.sys_restore_settings()

        # temporal canvas-graphics, partially with user-customizable symbolizations
        # z-index dependend on insertion order:

        # segment on reference-line
        self.rb_sgn = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)

        # visualize stationed point on reference-line
        self.vm_snf = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())

        self.vm_snt = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())

        # circle/square to mark selected point for edit
        self.vm_enf = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())
        self.vm_ent = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())

        # symbolize reference_geometry-changes, altered segments in current geometry
        self.rb_rfl_diff_cu = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)

        # symbolize reference_geometry-changes, altered segments in cached geometry
        self.rb_rfl_diff_ca = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)

        # visualize snapped reference-line
        self.rb_rfl = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)

        # segment on reference-line without offset
        self.rb_sg0 = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)

        # selection-rectangle
        self.rb_selection_rect = qgis.gui.QgsRubberBand(self.iface.mapCanvas())

        # symbols for cached PostProcessing-Features, cached stationing-from on cached reference-shape
        self.vm_pt_cnf = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())

        # symbol for PostProcessing-Feature, cached stationing-to on cached reference-shape
        self.vm_pt_cnt = qgis.gui.QgsVertexMarker(self.iface.mapCanvas())

        # symbol for cached PostProcessing-segment-Geometry
        self.rb_csgn = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)

        # symbol for cached reference-line, defined but not used
        self.rb_crfl = qgis.gui.QgsRubberBand(self.iface.mapCanvas(), qgis.core.QgsWkbTypes.LineGeometry)

        # apply the styles
        self.cvs_apply_style_to_graphics()

        # and initially hide them
        self.cvs_hide_markers()

        # change of QGIS3.ini rsp. QGis > Settings > General:  f. e. language, number format etc. => complete reload
        conn_id = qgis.core.QgsApplication.instance().customVariablesChanged.connect(self.gui_refresh)
        self.application_slot_cons.append(conn_id)

        # connect some signals in project to register TOC-changes (especially layersRemoved)
        conn_id = qgis.core.QgsProject.instance().layersAdded.connect(self.s_project_layers_added)
        self.application_slot_cons.append(conn_id)

        conn_id = qgis.core.QgsProject.instance().layersRemoved.connect(self.s_project_layers_removed)
        self.application_slot_cons.append(conn_id)

        # triggered *before* the project is saved to file
        # store the plugin-settings in project-file
        qgis.core.QgsProject.instance().writeProject.connect(self.sys_store_settings)

        # change of projection => replace some unit-widgets in dialog
        conn_id = self.iface.mapCanvas().destinationCrsChanged.connect(self.dlg_apply_canvas_crs)
        self.canvas_slot_cons.append(conn_id)

        self.sys_check_settings()
        self.dlg_init()

        self.dlg_append_log_message('SUCCESS', MY_DICT.tr('LolEvt_initialized'))

        self.session_data.tool_mode = 'initialized'
        self.dlg_show_tool_mode()

        if self.derived_settings.refLyr is not None:
            self.dlg_append_log_message('INFO', MY_DICT.tr('reference_layer_auto_loaded', self.derived_settings.refLyr.name()))
            # self.stm_measure_segment()
        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('load_reference_layer'))

    def canvasPressEvent(self, event: qgis.gui.QgsMapMouseEvent) -> None:
        """mouseDown on canvas, reimplemented standard-function for qgis.gui.QgsMapToolIdentify
        triggered action self.cpe_xxx dependend on self.session_data.tool_mode
        see canvasMoveEvent and canvasReleaseEvent
        :param event:
        """
        # Rev. 2024-06-18

        self.my_dialog.dnspbx_canvas_x.setValue(event.mapPoint().x())
        self.my_dialog.dnspbx_canvas_y.setValue(event.mapPoint().y())

        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.tool_mode == 'pausing':
                # convenience for tool_mode 'pausing': switch-back to previous_tool_mode
                previous_tool_mode = self.session_data.previous_tool_mode
                if previous_tool_mode == 'set_from_point':
                    self.stm_set_from_point()
                elif previous_tool_mode == 'set_to_point':
                    self.stm_set_to_point()
                if previous_tool_mode == 'move_segment':
                    self.stm_move_segment()
                if previous_tool_mode == 'change_offset':
                    self.stm_change_offset()
                elif previous_tool_mode == 'measure_segment':
                    self.stm_measure_segment()
                elif previous_tool_mode == 'set_feature_from_point':
                    if self.session_data.edit_feature:
                        self.stm_set_feature_from_point(self.session_data.edit_feature.data_fid)
                elif previous_tool_mode == 'set_feature_to_point':
                    if self.session_data.edit_feature:
                        self.stm_set_feature_to_point(self.session_data.edit_feature.data_fid)
                if previous_tool_mode == 'change_feature_offset':
                    if self.session_data.edit_feature:
                        self.stm_change_feature_offset(self.session_data.edit_feature.data_fid)
                elif previous_tool_mode == 'move_feature':
                    if self.session_data.edit_feature:
                        self.stm_move_feature(self.session_data.edit_feature.data_fid)
                elif previous_tool_mode == 'redigitize_feature':
                    if self.session_data.edit_feature:
                        self.stm_redigitize_feature(self.session_data.edit_feature.data_fid)
                elif previous_tool_mode == 'move_po_pro_feature':
                    if self.session_data.po_pro_feature:
                        self.stm_move_po_pro_feature(self.session_data.po_pro_feature.data_fid)
                elif previous_tool_mode == 'set_po_pro_from_point':
                    if self.session_data.po_pro_feature:
                        self.stm_set_po_pro_from_point(self.session_data.po_pro_feature.data_fid)
                elif previous_tool_mode == 'set_po_pro_to_point':
                    if self.session_data.po_pro_feature:
                        self.stm_set_po_pro_to_point(self.session_data.po_pro_feature.data_fid)

            if self.session_data.tool_mode == 'set_from_point':
                self.cpe_set_from_point(event)
            elif self.session_data.tool_mode == 'set_to_point':
                self.cpe_set_to_point(event)
            elif self.session_data.tool_mode == 'measure_segment':
                self.cpe_measure_segment(event)
            elif self.session_data.tool_mode == 'move_segment':
                self.cpe_move_segment(event)
            elif self.session_data.tool_mode == 'change_offset':
                self.cpe_change_offset(event)
            elif self.session_data.tool_mode == 'select_features':
                self.cpe_select_features(event)
            elif self.session_data.tool_mode == 'set_feature_from_point':
                self.cpe_set_feature_from_point(event)
            elif self.session_data.tool_mode == 'set_feature_to_point':
                self.cpe_set_feature_to_point(event)
            elif self.session_data.tool_mode == 'change_feature_offset':
                self.cpe_change_feature_offset(event)
            elif self.session_data.tool_mode == 'move_feature':
                self.cpe_move_feature(event)
            elif self.session_data.tool_mode == 'redigitize_feature':
                self.cpe_redigitize_feature(event)
            elif self.session_data.tool_mode == 'set_po_pro_from_point':
                self.cpe_set_po_pro_from_point(event)
            elif self.session_data.tool_mode == 'set_po_pro_to_point':
                self.cpe_set_po_pro_to_point(event)
            elif self.session_data.tool_mode == 'move_po_pro_feature':
                self.cpe_move_po_pro_feature(event)

    def canvasMoveEvent(self, event: qgis.gui.QgsMapMouseEvent) -> None:
        """MouseMove on canvas, reimplemented standard-function for qgis.gui.QgsMapToolIdentify
        triggered action self.cme_xxx dependend on self.session_data.tool_mode
        see canvasPressEvent and canvasReleaseEvent
        :param event:
        """
        # Rev. 2024-06-18
        self.my_dialog.dnspbx_canvas_x.setValue(event.mapPoint().x())
        self.my_dialog.dnspbx_canvas_y.setValue(event.mapPoint().y())

        if self.session_data.tool_mode == 'pausing':
            pass
        elif self.session_data.tool_mode == 'set_from_point':
            self.cme_set_from_point(event)
        elif self.session_data.tool_mode == 'set_to_point':
            self.cme_set_to_point(event)
        elif self.session_data.tool_mode == 'measure_segment':
            self.cme_measure_segment(event)
        elif self.session_data.tool_mode == 'move_segment':
            self.cme_move_segment(event)
        elif self.session_data.tool_mode == 'change_offset':
            self.cme_change_offset(event)
        elif self.session_data.tool_mode == 'select_features':
            self.cme_select_features(event)
        elif self.session_data.tool_mode == 'change_feature_offset':
            self.cme_change_feature_offset(event)
        elif self.session_data.tool_mode == 'set_feature_from_point':
            self.cme_set_feature_from_point(event)
        elif self.session_data.tool_mode == 'set_feature_to_point':
            self.cme_set_feature_to_point(event)
        elif self.session_data.tool_mode == 'move_feature':
            self.cme_move_feature(event)
        elif self.session_data.tool_mode == 'redigitize_feature':
            self.cme_redigitize_feature(event)
        elif self.session_data.tool_mode == 'set_po_pro_from_point':
            self.cme_set_po_pro_from_point(event)
        elif self.session_data.tool_mode == 'set_po_pro_to_point':
            self.cme_set_po_pro_to_point(event)
        elif self.session_data.tool_mode == 'move_po_pro_feature':
            self.cme_move_po_pro_feature(event)




    def canvasReleaseEvent(self, event: qgis.gui.QgsMapMouseEvent) -> None:
        """mouseUp on canvas, reimplemented standard-function for qgis.gui.QgsMapToolIdentify
        triggered action self.cre_xxx dependend on self.session_data.tool_mode
        see canvasPressEvent and canvasMoveEvent
        :param event:
        """
        # Rev. 2024-06-18
        self.my_dialog.dnspbx_canvas_x.setValue(event.mapPoint().x())
        self.my_dialog.dnspbx_canvas_y.setValue(event.mapPoint().y())

        self.cvs_hide_snap()

        if self.session_data.tool_mode == 'pausing':
            pass
        if self.session_data.tool_mode == 'set_from_point':
            self.cre_set_from_point(event)
        elif self.session_data.tool_mode == 'set_to_point':
            self.cre_set_to_point(event)
        elif self.session_data.tool_mode == 'measure_segment':
            self.cre_measure_segment(event)
        elif self.session_data.tool_mode == 'move_segment':
            self.cre_move_segment(event)
        elif self.session_data.tool_mode == 'change_offset':
            self.cre_change_offset(event)
        elif self.session_data.tool_mode == 'select_features':
            self.cre_select_features(event)
        elif self.session_data.tool_mode == 'change_feature_offset':
            self.cre_change_feature_offset(event)
        elif self.session_data.tool_mode == 'set_feature_from_point':
            self.cre_set_feature_from_point(event)
        elif self.session_data.tool_mode == 'set_feature_to_point':
            self.cre_set_feature_to_point(event)
        elif self.session_data.tool_mode == 'move_feature':
            self.cre_move_feature(event)
        elif self.session_data.tool_mode == 'redigitize_feature':
            self.cre_redigitize_feature(event)
        elif self.session_data.tool_mode == 'move_po_pro_feature':
            self.cre_move_po_pro_feature(event)
        elif self.session_data.tool_mode == 'set_po_pro_from_point':
            self.cre_set_po_pro_from_point(event)
        elif self.session_data.tool_mode == 'set_po_pro_to_point':
            self.cre_set_po_pro_to_point(event)

    def stm_measure_segment(self):
        """set tool mode 'measure_segment'"""
        # Rev. 2024-06-18
        if self.sys_set_tool_mode('measure_segment'):
            self.session_data.pol_from = None
            self.session_data.pol_to = None
            self.session_data.measure_feature = None
            self.cvs_hide_markers()
            self.dlg_clear_measurements()
            self.dlg_unselect_qcbn_reference_feature()
            self.dlg_clear_canvas_coords()
            self.dlg_refresh_measure_section()

    def cme_measure_segment(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'measure_segment'"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_move = PoLFeature()
            if event_with_left_btn and self.session_data.measure_feature:
                # pol_from is set and mouse-move with hold left mouse-button => snap to pol_from-feature
                match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.measure_feature.ref_fid)
                if match.isValid():
                    # mouseMove with snap to pol_from.ref_fid
                    self.session_data.pol_to = pol_mouse_move
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn', 'sg0'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)

                else:
                    # mouseMove without snap to pol_from.ref_fid
                    pass
            elif not event_with_left_btn:
                # mouseMove without pol_from and without mouse-button
                match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr)
                if match.isValid():
                    # only refresh snap_indicator on match keeping old position visible
                    self.cvs_show_snap(match)
                    self.dlg_select_qcbn_reference_feature(match.featureId())
                    self.cvs_draw_reference_geom(ref_fid=match.featureId())

    def cpe_measure_segment(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'measure_segment'"""
        # Rev. 2024-06-18

        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_down = PoLFeature()
            # snap to any feature
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr)
            if match.isValid():
                self.session_data.pol_from = pol_mouse_down
                self.session_data.pol_to = pol_mouse_down
                self.session_data.measure_feature = LoLFeature()
                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                self.session_data.measure_feature.offset = self.session_data.current_offset
                self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'rfl'])
                self.dlg_refresh_measurements(self.session_data.measure_feature)
            else:
                self.stm_measure_segment()
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_press_match_on_reference_layer'))

    def cre_measure_segment(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'measure_segment'
        Note: measurement is done in cme_measure_segment"""
        # Rev. 2024-06-18
        self.cvs_hide_markers(['snf', 'enf', 'sgn', 'sg0'])
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.measure_feature:
                # draw self.session_data.measure_feature
                self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn'])
                self.dlg_refresh_measure_section()
                self.sys_set_tool_mode('pausing')

            else:
                self.stm_measure_segment()

    def stm_set_from_point(self):
        """set tool mode 'set_from_point'"""
        # Rev. 2024-06-18
        if self.sys_set_tool_mode('set_from_point'):
            self.cvs_hide_markers(['ent'])
            self.dlg_clear_from_measurements()
            self.dlg_clear_delta_measurements()
            self.dlg_unselect_qcbn_reference_feature()

            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            if self.session_data.measure_feature and self.session_data.measure_feature.pol_from:
                self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'enf', 'snt', 'sgn', 'sg0', 'rfl'], ['snf'], extent_mode)
                self.dlg_refresh_measurements(self.session_data.measure_feature)
                self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
            elif self.session_data.pol_from:
                self.cvs_draw_from_markers(self.session_data.pol_from, ['snf', 'enf', 'rfl'], ['snf'], extent_mode)
                self.dlg_select_qcbn_reference_feature(self.session_data.pol_from.ref_fid)
                self.dlg_refresh_from_measurements(self.session_data.pol_from)

            self.session_data.pol_mouse_down = None

    def cpe_set_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'set_from_point'"""
        # Rev. 2024-06-18
        self.dlg_clear_from_measurements()
        self.dlg_clear_delta_measurements()
        self.session_data.pol_mouse_down = self.session_data.pol_from = None
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr)
            if match.isValid():
                self.session_data.pol_mouse_down = self.session_data.pol_from = pol_mouse_down
                if self.session_data.measure_feature and self.session_data.measure_feature.ref_fid == self.session_data.pol_from.ref_fid:
                    # measure_feature exists with same reference-match
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'enf', 'snt', 'sgn', 'sg0', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                    self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                elif self.session_data.pol_to and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                    # pol_from and pol_to independend but same reference-match
                    self.session_data.measure_feature = LoLFeature()
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'enf', 'snt', 'sgn', 'sg0', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                    self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                else:
                    # no measure_feature or other reference-match => just pol_from
                    self.dlg_refresh_from_measurements(self.session_data.pol_from)
                    self.dlg_select_qcbn_reference_feature(self.session_data.pol_from.ref_fid)
                    # let snt visible
                    self.cvs_hide_markers(['sgn', 'sg0'])
                    self.cvs_draw_from_markers(self.session_data.pol_from, ['snf', 'enf', 'rfl'])


            else:
                self.stm_set_from_point()
                # mousePress without match
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_press_match_on_reference_layer'))

    def cme_set_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'set_from_point'"""
        # Rev. 2024-06-18

        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())

        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr)
            if match.isValid():
                if event_with_left_btn and self.session_data.pol_mouse_down:
                    self.cvs_hide_snap()
                    # left button and pol_mouse_down => drag
                    self.session_data.pol_from = pol_mouse_move
                    if self.session_data.measure_feature and self.session_data.measure_feature.ref_fid == self.session_data.pol_from.ref_fid:
                        # measure_feature exists with same reference-match
                        self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                        self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'enf', 'snt', 'sgn', 'sg0', 'rfl'])
                        self.dlg_refresh_measurements(self.session_data.measure_feature)
                        self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                    elif self.session_data.pol_to and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:

                        # pol_from and pol_to independend but same reference-match
                        self.session_data.measure_feature = LoLFeature()
                        self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                        self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                        self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'enf', 'snt', 'sgn', 'sg0', 'rfl'])
                        self.dlg_refresh_measurements(self.session_data.measure_feature)
                        self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                    else:
                        # no measure_feature or other reference-match
                        self.cvs_hide_markers(['sgn', 'sg0'])
                        self.dlg_clear_from_measurements()
                        self.dlg_clear_delta_measurements()
                        self.dlg_refresh_from_measurements(self.session_data.pol_from)
                        self.cvs_draw_from_markers(self.session_data.pol_from, ['snf', 'enf', 'rfl'])
                        self.dlg_select_qcbn_reference_feature(self.session_data.pol_from.ref_fid)

                else:
                    # no left mouse-button and no pol_mouse_down
                    # => mouseMove before canvasPress
                    # => show snap_indicator, highlight Reference-Geometry, select qcbn_reference_feature
                    self.cvs_show_snap(match)
                    self.cvs_draw_reference_geom(ref_fid=match.featureId())
                    self.dlg_select_qcbn_reference_feature(match.featureId())

    def cre_set_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'set_from_point'"""
        # Rev. 2024-06-18
        self.cvs_hide_markers(['snf', 'enf', 'sgn', 'sg0'])
        self.dlg_clear_from_measurements()
        self.dlg_clear_delta_measurements()

        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_up = PoLFeature()
            match = pol_mouse_up.snap_to_layer(event, self.derived_settings.refLyr)
            # take last match, which could be the same as canvasMove
            if match.isValid():
                self.session_data.pol_from = pol_mouse_up
            # save current pol_from also without match
            if self.session_data.pol_from:

                # initialize measure_feature with same pol_from/pol_to
                if self.session_data.measure_feature is None:
                    self.session_data.measure_feature = LoLFeature()
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_from)

                if self.session_data.measure_feature and self.session_data.measure_feature.ref_fid == self.session_data.pol_from.ref_fid:
                    # measure_feature existing and same reference-match
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                    self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                elif self.session_data.pol_to and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                    # pol_from and pol_to independend but same reference-match
                    self.session_data.measure_feature = LoLFeature()
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                    self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                else:
                    # just pol_from
                    self.session_data.measure_feature = None
                    self.dlg_refresh_from_measurements(self.session_data.pol_from)
                    self.cvs_draw_from_markers(self.session_data.pol_from, ['snf', 'rfl'])
                    self.dlg_select_qcbn_reference_feature(self.session_data.pol_from.ref_fid)

                self.dlg_refresh_measure_section()

                self.sys_set_tool_mode('pausing')
            else:
                self.stm_set_from_point()
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_release_match_on_reference_layer'))

    def stm_set_to_point(self):
        """set tool mode 'set_to_point'"""
        # Rev. 2024-06-18
        if self.sys_set_tool_mode('set_to_point'):
            self.cvs_hide_markers(['enf'])
            self.dlg_clear_to_measurements()
            self.dlg_clear_delta_measurements()
            self.dlg_unselect_qcbn_reference_feature()

            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            if self.session_data.measure_feature and self.session_data.measure_feature.pol_to:
                self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'ent', 'sgn', 'sg0', 'rfl'], ['snt'], extent_mode)
                self.dlg_refresh_measurements(self.session_data.measure_feature)
                self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
            elif self.session_data.pol_to:
                self.cvs_draw_to_markers(self.session_data.pol_to, ['snt', 'ent', 'rfl'], ['snt'], extent_mode)
                self.dlg_select_qcbn_reference_feature(self.session_data.pol_to.ref_fid)
                self.dlg_refresh_to_measurements(self.session_data.pol_to)

            self.session_data.pol_mouse_down = None

    def cpe_set_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'set_to_point'"""
        # Rev. 2024-06-18
        self.dlg_clear_to_measurements()
        self.dlg_clear_delta_measurements()
        self.session_data.pol_mouse_down = self.session_data.pol_to = None
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr)
            if match.isValid():
                self.session_data.pol_mouse_down = self.session_data.pol_to = pol_mouse_down
                if self.session_data.measure_feature and self.session_data.measure_feature.ref_fid == self.session_data.pol_to.ref_fid:
                    # measure_feature exists with same reference-match
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'ent', 'sgn', 'sg0', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                    self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                elif self.session_data.pol_from and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                    # pol_from and pol_to independend but same reference-match
                    self.session_data.measure_feature = LoLFeature()
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'ent', 'sgn', 'sg0', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                    self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                else:
                    # no measure_feature or other reference-match => just pol_to
                    self.dlg_refresh_to_measurements(self.session_data.pol_to)
                    self.dlg_select_qcbn_reference_feature(self.session_data.pol_to.ref_fid)
                    # let snf visible
                    self.cvs_hide_markers(['sgn', 'sg0'])
                    self.cvs_draw_to_markers(self.session_data.pol_to, ['snt', 'ent', 'rfl'])
                    self.dlg_select_qcbn_reference_feature(self.session_data.pol_to.ref_fid)

            else:
                # mousePress without match
                self.stm_set_to_point()
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_press_match_on_reference_layer'))

    def cme_set_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'set_to_point'"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())

        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr)
            if match.isValid():
                if event_with_left_btn and self.session_data.pol_mouse_down:
                    self.cvs_hide_snap()
                    # left button and pol_mouse_down => drag
                    self.session_data.pol_to = pol_mouse_move
                    if self.session_data.measure_feature and self.session_data.measure_feature.ref_fid == self.session_data.pol_to.ref_fid:
                        # measure_feature exists with same reference-match
                        self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                        self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'ent', 'sgn', 'sg0', 'rfl'])
                        self.dlg_refresh_measurements(self.session_data.measure_feature)
                        self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                    elif self.session_data.pol_from and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                        # pol_from and pol_to independend but same reference-match
                        self.session_data.measure_feature = LoLFeature()
                        self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                        self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                        self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'ent', 'sgn', 'sg0', 'rfl'])
                        self.dlg_refresh_measurements(self.session_data.measure_feature)
                        self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
                    else:
                        # no measure_feature or other reference-match
                        self.cvs_hide_markers(['sgn', 'sg0'])
                        self.dlg_clear_to_measurements()
                        self.dlg_clear_delta_measurements()
                        self.dlg_refresh_to_measurements(self.session_data.pol_to)
                        self.cvs_draw_to_markers(self.session_data.pol_to, ['snt', 'ent', 'rfl'])
                        self.dlg_select_qcbn_reference_feature(self.session_data.pol_to.ref_fid)

                else:
                    # no left mouse-button and no pol_mouse_down
                    # => mouseMove before canvasPress
                    # => show snap_indicator, highlight Reference-Geometry, select qcbn_reference_feature
                    self.cvs_show_snap(match)
                    self.cvs_draw_reference_geom(ref_fid=match.featureId())
                    self.dlg_select_qcbn_reference_feature(match.featureId())

    def cre_set_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'set_to_point'"""
        # Rev. 2024-06-18
        self.cvs_hide_markers(['snt', 'ent', 'sgn', 'sg0'])
        self.dlg_clear_to_measurements()
        self.dlg_clear_delta_measurements()

        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            pol_mouse_up = PoLFeature()
            match = pol_mouse_up.snap_to_layer(event, self.derived_settings.refLyr)
            # take last match, which could be the same as canvasMove
            if match.isValid():
                self.session_data.pol_to = pol_mouse_up
            # save current pol_to also without match
            if self.session_data.pol_to:

                # initialize measure_feature with same pol_from/pol_to
                if self.session_data.measure_feature is None:
                    self.session_data.measure_feature = LoLFeature()
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_to)
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                if self.session_data.measure_feature and self.session_data.measure_feature.ref_fid == self.session_data.pol_to.ref_fid:
                    # measure_feature existing and same reference-match
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                elif self.session_data.pol_from and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                    # pol_from and pol_to independend but same reference-match
                    self.session_data.measure_feature = LoLFeature()
                    self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                    self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)
                    self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                else:
                    # just pol_to
                    self.session_data.measure_feature = None
                    self.dlg_refresh_to_measurements(self.session_data.pol_to)
                    self.cvs_draw_to_markers(self.session_data.pol_to, ['snt', 'rfl'])

                self.dlg_refresh_measure_section()

                self.sys_set_tool_mode('pausing')
            else:
                self.stm_set_to_point()
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_release_match_on_reference_layer'))

    def stm_move_segment(self):
        """set tool mode 'move_segment'"""
        # Rev. 2024-06-18
        if self.sys_set_tool_mode('move_segment'):
            self.session_data.pol_mouse_move = None
            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'enf', 'snt', 'ent', 'sgn', 'sg0'], extent_markers=['sgn', 'sg0'], extent_mode=extent_mode)
            self.dlg_refresh_measurements(self.session_data.measure_feature)

    def cpe_move_segment(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'move_segment'"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_move = None
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature and self.session_data.measure_feature.is_valid:
            pol_mouse_down = PoLFeature()
            pol_mouse_down.line_locate_event(event, self.derived_settings.refLyr, self.session_data.measure_feature.ref_fid)
            if pol_mouse_down.is_valid:
                # initializes self.session_data.pol_mouse_move, which will be used and actualized in cme_move_segment to calculate the amount and direction of movement
                self.session_data.pol_mouse_move = pol_mouse_down

    def cme_move_segment(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'move_segment'"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())

        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature and self.session_data.measure_feature.is_valid:

            pol_mouse_move = PoLFeature()
            pol_mouse_move.line_locate_event(event, self.derived_settings.refLyr, self.session_data.measure_feature.ref_fid)

            if pol_mouse_move.is_valid:
                if event_with_left_btn and self.session_data.pol_mouse_move:
                    # mouseMove after mousePress
                    reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
                    if reference_geom:
                        ref_len = reference_geom.length()
                        delta = pol_mouse_move.snap_n_abs - self.session_data.pol_mouse_move.snap_n_abs

                        old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                        old_to = self.session_data.measure_feature.pol_to.snap_n_abs
                        old_len = abs(old_to - old_from)

                        new_from = old_from + delta
                        new_to = old_to + delta

                        if new_to > ref_len or new_from > ref_len:
                            new_to = ref_len
                            new_from = ref_len - old_len

                        if new_from < 0 or new_to < 0:
                            new_from = 0
                            new_to = old_len

                        pol_from = self.session_data.measure_feature.pol_from.__copy__()
                        pol_from.recalc_by_stationing(new_from, 'Nabs')

                        pol_to = self.session_data.measure_feature.pol_to.__copy__()
                        pol_to.recalc_by_stationing(new_to, 'Nabs')

                        self.session_data.measure_feature.set_pol_from(pol_from)
                        self.session_data.measure_feature.set_pol_to(pol_to)

                        self.session_data.pol_from = pol_from
                        self.session_data.pol_to = pol_to

                        self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'enf', 'ent', 'sgn', 'sg0'])
                        self.dlg_refresh_measurements(self.session_data.measure_feature)

                        # store for next canvasMouseMove
                        self.session_data.pol_mouse_move = pol_mouse_move
                    else:
                        self.dlg_append_log_message("WARNING", error_msg)

    def cre_move_segment(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'move_segment'"""
        # Rev. 2024-06-18
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature and self.session_data.measure_feature.is_valid:
            self.cvs_hide_markers(['enf', 'ent', 'sg0'])
            self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])
            self.dlg_refresh_measurements(self.session_data.measure_feature)

            self.sys_set_tool_mode('pausing')

    def stm_change_offset(self):
        """set tool mode 'change_offset'"""
        # Rev. 2024-06-18
        if self.sys_set_tool_mode('change_offset'):
            self.session_data.pol_mouse_down = None
            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'enf', 'snt', 'ent', 'sgn', 'sg0'], extent_markers=['sgn', 'sg0'], extent_mode=extent_mode)
            self.dlg_refresh_measurements(self.session_data.measure_feature)

    def cpe_change_offset(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'change_offset'"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature and self.session_data.measure_feature.is_valid:

            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
            if reference_geom:
                # dummy, used only as flag for cme_change_offset/cre_change_offset
                self.session_data.pol_mouse_down = self.session_data.measure_feature.pol_from.__copy__()

                # calculate the new offset from event-position allready on mousePress
                point_geom = qgis.core.QgsGeometry.fromPointXY(event.mapPoint())
                point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.derived_settings.refLyr.crs(), qgis.core.QgsProject.instance()))
                point_on_line = reference_geom.closestSegmentWithContext(point_geom.asPoint())
                sqr_dist = point_on_line[0]
                # <0 left, >0 right, ==0 on the line
                side = point_on_line[3]
                abs_dist = math.sqrt(sqr_dist)
                calc_offset = abs_dist * side * -1

                # store in session_data...
                self.session_data.current_offset = calc_offset

                # ...and measure_feature
                self.session_data.measure_feature.offset = calc_offset

                self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn', 'sg0', 'rfl'])
                self.dlg_refresh_measurements(self.session_data.measure_feature)
            else:
                self.dlg_append_log_message('WARNING', error_msg)

    def cme_change_offset(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'change_offset'"""
        # Rev. 2024-06-18
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature and self.session_data.measure_feature.is_valid:
            if self.session_data.pol_mouse_down:
                # mouseMove after mousePress
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
                if reference_geom:
                    point_geom = qgis.core.QgsGeometry.fromPointXY(event.mapPoint())
                    point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.derived_settings.refLyr.crs(), qgis.core.QgsProject.instance()))
                    point_on_line = reference_geom.closestSegmentWithContext(point_geom.asPoint())
                    sqr_dist = point_on_line[0]
                    # <0 left, >0 right, ==0 on the line
                    side = point_on_line[3]
                    abs_dist = math.sqrt(sqr_dist)
                    calc_offset = abs_dist * side * -1

                    # store in session_data...
                    self.session_data.current_offset = calc_offset

                    # ...and measure_feature
                    self.session_data.measure_feature.offset = calc_offset

                    self.cvs_draw_feature(self.session_data.measure_feature, ['sgn'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                else:
                    self.dlg_append_log_message('WARNING', error_msg)

    def cre_change_offset(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'change_offset'"""
        # Rev. 2024-06-18
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature and self.session_data.measure_feature.is_valid:
            self.cvs_hide_markers(['enf', 'ent', 'sg0'])
            self.cvs_draw_feature(self.session_data.measure_feature, ['snf', 'snt', 'sgn', 'rfl'])
            self.dlg_refresh_measurements(self.session_data.measure_feature)
            self.sys_set_tool_mode('pausing')

    def stm_select_features(self):
        """set tool-mode select_features: select referenced features from showLyr to feature-selection"""
        # Rev. 2024-06-18
        self.sys_set_tool_mode('select_features')

    def cpe_select_features(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'select_features'"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())
        self.session_data.pol_mouse_down = None
        self.rb_selection_rect.hide()
        if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs and event_with_left_btn:
            # dummy, only for draw a canvas rect in cme_select_features and check via screen_x/screen_y if a point or a rect is drawn in cre_select_features
            self.session_data.pol_mouse_down = PoLFeature()
            self.session_data.pol_mouse_down.screen_x = event.pixelPoint().x()
            self.session_data.pol_mouse_down.screen_y = event.pixelPoint().y()
            self.session_data.pol_mouse_down.map_x = event.mapPoint().x()
            self.session_data.pol_mouse_down.map_y = event.mapPoint().y()

    def cme_select_features(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'select_features'"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())
        if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs and self.session_data.pol_mouse_down is not None and self.session_data.pol_mouse_down.map_x is not None and self.session_data.pol_mouse_down.map_y is not None and event_with_left_btn:
            # draw selection-rectangle with canvas-coords
            down_pt_map = qgis.core.QgsPointXY(self.session_data.pol_mouse_down.map_x, self.session_data.pol_mouse_down.map_y)
            move_pt_map = qgis.core.QgsPointXY(event.mapPoint().x(), event.mapPoint().y())
            selection_geom = qgis.core.QgsGeometry.fromRect(qgis.core.QgsRectangle(down_pt_map, move_pt_map))
            self.rb_selection_rect.setToGeometry(selection_geom, None)
            self.rb_selection_rect.show()

    def cre_select_features(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'select_features'"""
        # Rev. 2024-06-18
        if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs and self.session_data.pol_mouse_down is not None:
            # different select-behaviours dependend from chtrl/shift-modifier
            #  no modifier => new selection
            selection_mode = 'new_selection'
            if QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers():
                selection_mode = 'remove_from_selection'
            elif QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers():
                selection_mode = 'add_to_selection'

            if self.session_data.pol_mouse_down.screen_x == event.pixelPoint().x() and self.session_data.pol_mouse_down.screen_y == event.pixelPoint().y():
                # screen_x/screen_y same as registered in pol_mouse_down => klick => Point => buffered to selection rect
                delta_pixel = 3
                min_x = self.session_data.pol_mouse_down.screen_x - delta_pixel
                max_x = self.session_data.pol_mouse_down.screen_x + delta_pixel
                min_y = self.session_data.pol_mouse_down.screen_y - delta_pixel
                max_y = self.session_data.pol_mouse_down.screen_y + delta_pixel
                down_pt_map = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(QtCore.QPoint(min_x, min_y))
                up_pt_map = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(QtCore.QPoint(max_x, max_y))

            else:
                down_pt_map = qgis.core.QgsPointXY(self.session_data.pol_mouse_down.map_x, self.session_data.pol_mouse_down.map_y)
                up_pt_map = event.mapPoint()

            selection_geom = qgis.core.QgsGeometry.fromRect(qgis.core.QgsRectangle(down_pt_map, up_pt_map))
            selection_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.derived_settings.refLyr.crs(), qgis.core.QgsProject.instance()))

            request = qgis.core.QgsFeatureRequest()
            request.setFilterRect(selection_geom.boundingBox())
            request.setFlags(qgis.core.QgsFeatureRequest.ExactIntersect)

            layer_selected_ids = [f.id() for f in self.derived_settings.showLyr.getFeatures(request)]

            # warning, if new and uncommitted features were selected
            # these features will appear in the getFeatures-result all with id() = 0
            # Note: multiple uncommitted features appear together as only one line in the associated attribute tables of the virtual layers
            num_uncommitted = layer_selected_ids.count(0)

            if num_uncommitted:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('uncommitted_features_selected_on_map', num_uncommitted))

            if 0 in layer_selected_ids:
                layer_selected_ids.remove(0)

            if len(layer_selected_ids) > 0:
                # like implemented in QGis-Select-Features:
                if selection_mode == 'remove_from_selection':
                    for new_id in layer_selected_ids:
                        if new_id in self.session_data.selected_fids:
                            self.session_data.selected_fids.remove(new_id)
                elif selection_mode == 'add_to_selection':
                    self.session_data.selected_fids += layer_selected_ids
                    if len(layer_selected_ids) == 1:
                        # only one feature selected:
                        self.tool_select_feature(layer_selected_ids[0], ['snf', 'snt', 'sgn', 'rfl'])
                else:
                    # selection_mode == 'new_selection'
                    self.session_data.selected_fids = layer_selected_ids
                    if len(layer_selected_ids) == 1:
                        # only one feature selected:
                        self.tool_select_feature(layer_selected_ids[0], ['snf', 'snt', 'sgn', 'rfl'])

                self.tool_check_selected_ids()

        self.rb_selection_rect.hide()
        self.session_data.pol_mouse_down = None
        self.dlg_refresh_feature_selection_section()

    def stm_set_feature_from_point(self, data_fid: int = None):
        """set tool mode set_feature_from_point: set from-point for self.session_data.edit_feature with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None

        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
        self.tool_select_feature(data_fid, ['snf', 'snt', 'enf', 'sgn', 'sg0', 'rfl'], ['snf'], extent_mode)

        self.sys_set_tool_mode('set_feature_from_point')

    def cpe_set_feature_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasPressEvent for tool-mode set_feature_from_point: re-stationing feature on assigned reference-line with immediate storage
        :param event:"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            if match.isValid():
                self.cvs_hide_snap()
                self.session_data.pol_mouse_down = pol_mouse_down
                # first draw enf on original stationing
                self.cvs_draw_feature(self.session_data.edit_feature, ['enf'])
                self.session_data.edit_feature.set_pol_from(pol_mouse_down)
                # then draw other markers on altered stationing
                self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'snt', 'sgn', 'sg0', 'rfl'])


            else:
                # mousePress without match
                self.stm_set_feature_from_point(self.session_data.edit_feature.data_fid)
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_press_match_on_reference_layer'))

    def cme_set_feature_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasMoveEvent for tool-mode set_feature_from_point: re-stationing feature on assigned reference-line with immediate storage
                :param event:"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())

        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)

            if self.session_data.pol_mouse_down and event_with_left_btn:
                self.cvs_hide_snap()
                if match.isValid():
                    # mouse-move after press and cursor on assigned reference-feature
                    self.session_data.edit_feature.set_pol_from(pol_mouse_move)
                    self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'sgn', 'sg0'])
            else:
                self.cvs_show_snap(match)

    def cre_set_feature_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasReleaseEvent for tool-mode set_feature_from_point: re-stationing feature on assigned reference-line with immediate storage
                        :param event:"""
        # Rev. 2024-06-18
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None and self.session_data.pol_mouse_down is not None:
            pol_mouse_up = PoLFeature()
            match = pol_mouse_up.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            if match.isValid():
                self.session_data.edit_feature.set_pol_from(pol_mouse_up)

            # save edit_feature also if there is no match
            self.tool_save_edit_feature(self.session_data.edit_feature)
            self.tool_select_feature(self.session_data.edit_feature.data_fid, ['snf', 'snt', 'sgn', 'rfl'])
            self.sys_set_tool_mode('pausing')

    def stm_set_feature_to_point(self, data_fid: int = None):
        """set tool mode set_feature_to_point: re-stationing feature on assigned reference-line with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None

        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
        self.tool_select_feature(data_fid, ['snf', 'snt', 'ent', 'sgn', 'sg0', 'rfl'], ['snt'], extent_mode)

        self.sys_set_tool_mode('set_feature_to_point')

    def cpe_set_feature_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasPressEvent for tool-mode set_feature_to_point: re-stationing feature on assigned reference-line with immediate storage
        :param event:"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            # Variante ohne Snap, Abstand zur Linie egal
            # pol_mouse_down.line_locate_event(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            # if pol_mouse_down.is_valid:
            if match.isValid():
                self.cvs_hide_snap()
                self.session_data.pol_mouse_down = pol_mouse_down
                # first draw enf on original stationing
                self.cvs_draw_feature(self.session_data.edit_feature, ['ent'])
                self.session_data.edit_feature.set_pol_to(pol_mouse_down)
                # then draw other markers on altered stationing
                self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'snt', 'sgn', 'sg0', 'rfl'])


            else:
                # mousePress without match
                self.stm_set_feature_to_point(self.session_data.edit_feature.data_fid)
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_press_match_on_reference_layer'))

    def cme_set_feature_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasMoveEvent for tool-mode set_feature_to_point: re-stationing feature on assigned reference-line with immediate storage
                :param event:"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())

        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)

            if self.session_data.pol_mouse_down and event_with_left_btn:
                self.cvs_hide_snap()
                if match.isValid():
                    # mouse-move after press and cursor on assigned reference-feature
                    self.session_data.edit_feature.set_pol_to(pol_mouse_move)
                    self.cvs_draw_feature(self.session_data.edit_feature, ['snt', 'sgn', 'sg0'])
            else:
                self.cvs_show_snap(match)

    def cre_set_feature_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasReleaseEvent for tool-mode set_feature_to_point: re-stationing feature on assigned reference-line with immediate storage
                        :param event:"""
        # Rev. 2024-06-18
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None and self.session_data.pol_mouse_down is not None:
            pol_mouse_up = PoLFeature()
            match = pol_mouse_up.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            if match.isValid():
                self.session_data.edit_feature.set_pol_to(pol_mouse_up)

            # save edit_feature also if there is no match
            self.tool_save_edit_feature(self.session_data.edit_feature)
            self.tool_select_feature(self.session_data.edit_feature.data_fid, ['snf', 'snt', 'sgn', 'rfl'])
            self.sys_set_tool_mode('pausing')

    def stm_move_feature(self, data_fid: int = None):
        """set tool mode move_feature: re-stationing feature on assigned reference-line with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_move = None

        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
        self.tool_select_feature(data_fid, ['snf', 'snt', 'enf', 'ent', 'sgn', 'sg0', 'rfl'], ['sgn'], extent_mode)

        self.sys_set_tool_mode('move_feature')

    def cpe_move_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'move_feature'"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_move = None
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            if match.isValid():
                self.session_data.pol_mouse_move = pol_mouse_down
                self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'snt', 'enf', 'ent', 'sgn', 'sg0', 'rfl'])

                self.cvs_hide_snap()
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_match_on_reference_geom', self.session_data.edit_feature.ref_fid))
                self.stm_move_feature(self.session_data.edit_feature.data_fid)

    def cme_move_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'move_feature'"""
        # Rev. 2024-06-18

        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())

        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            if match.isValid():
                if event_with_left_btn and self.session_data.pol_mouse_move:
                    # mouseMove after mousePress

                    reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.edit_feature.ref_fid)
                    if reference_geom:
                        ref_len = reference_geom.length()
                        # delta is calculated from current pol_mouse_move to last self.session_data.pol_mouse_move
                        delta = pol_mouse_move.snap_n_abs - self.session_data.pol_mouse_move.snap_n_abs
                        old_from = self.session_data.edit_feature.pol_from.snap_n_abs
                        old_to = self.session_data.edit_feature.pol_to.snap_n_abs
                        old_len = abs(old_to - old_from)

                        new_from = old_from + delta
                        new_to = old_to + delta

                        if new_to > ref_len or new_from > ref_len:
                            new_to = ref_len
                            new_from = ref_len - old_len

                        if new_from < 0 or new_to < 0:
                            new_from = 0
                            new_to = old_len

                        self.session_data.edit_feature.pol_from.recalc_by_stationing(new_from, 'Nabs')
                        self.session_data.edit_feature.pol_to.recalc_by_stationing(new_to, 'Nabs')
                        self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'snt', 'sgn', 'sg0'])

                        # store this stationing for the next mouse-move-call
                        self.session_data.pol_mouse_move = pol_mouse_move
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)

                else:
                    self.cvs_show_snap(match)

    def cre_move_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'move_feature'"""
        # Rev. 2024-06-18
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None and self.session_data.pol_mouse_move is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
            if match.isValid():
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.edit_feature.ref_fid)
                if reference_geom:
                    ref_len = reference_geom.length()
                    # delta is calculated from current pol_mouse_move to last self.session_data.pol_mouse_move
                    delta = pol_mouse_move.snap_n_abs - self.session_data.pol_mouse_move.snap_n_abs
                    old_from = self.session_data.edit_feature.pol_from.snap_n_abs
                    old_to = self.session_data.edit_feature.pol_to.snap_n_abs
                    old_len = abs(old_to - old_from)

                    new_from = old_from + delta
                    new_to = old_to + delta

                    if new_to > ref_len or new_from > ref_len:
                        new_to = ref_len
                        new_from = ref_len - old_len

                    if new_from < 0 or new_to < 0:
                        new_from = 0
                        new_to = old_len

                    self.session_data.edit_feature.pol_from.recalc_by_stationing(new_from, 'Nabs')
                    self.session_data.edit_feature.pol_to.recalc_by_stationing(new_to, 'Nabs')
                else:
                    self.dlg_append_log_message('WARNING', error_msg)

            # save also without match
            self.tool_save_edit_feature(self.session_data.edit_feature)
            self.session_data.pol_mouse_move = None
            self.tool_select_feature(self.session_data.edit_feature.data_fid, ['snf', 'snt', 'sgn', 'rfl'])
            self.sys_set_tool_mode('pausing')

    def stm_redigitize_feature(self, data_fid: int = None):
        """set tool mode redigitize_feature: re-stationing feature on any reference-line with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None

        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
        self.tool_select_feature(data_fid, ['snf', 'snt', 'enf', 'ent', 'sgn', 'sg0', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)

        self.sys_set_tool_mode('redigitize_feature')

    def cpe_redigitize_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'redigitize_feature'"""
        # Rev. 2024-06-18

        self.session_data.pol_mouse_down = None
        self.cvs_hide_markers()
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            pol_mouse_down = PoLFeature()
            # match without self.session_data.edit_feature.ref_fid => any feature
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr)
            if match.isValid():
                self.session_data.pol_mouse_down = pol_mouse_down

                # first valid mouse-down is used for reference-id, pol_from and pol_to, thus making edit_feature a double-point
                self.session_data.edit_feature.set_pol_from(pol_mouse_down)
                self.session_data.edit_feature.set_pol_to(pol_mouse_down)
                # only draw from-points
                self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'enf', 'rfl'])
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_match_on_reference_layer'))
                self.stm_redigitize_feature(self.session_data.edit_feature.data_fid)

    def cme_redigitize_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'redigitize_feature'"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())
        pol_mouse_move = PoLFeature()
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            if event_with_left_btn and self.session_data.pol_mouse_down:
                match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
                if match.isValid():
                    self.session_data.edit_feature.set_pol_to(pol_mouse_move)
                    self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'snt', 'ent', 'sgn', 'sg0', 'rfl'])
            else:
                # no left button and no pol_mouse_down => mouse-move before valid mouse-press => snap to any feature and show snap-icon
                match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr)
                self.cvs_show_snap(match)
                self.cvs_draw_reference_geom(ref_fid=match.featureId())

    def cre_redigitize_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'redigitize_feature'"""
        # Rev. 2024-06-18
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            if self.session_data.pol_mouse_down:
                pol_mouse_up = PoLFeature()
                match = pol_mouse_up.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.edit_feature.ref_fid)
                if match.isValid():
                    self.session_data.edit_feature.set_pol_to(pol_mouse_up)

                # save also without match
                self.tool_save_edit_feature(self.session_data.edit_feature)

            self.session_data.pol_mouse_down = None
            self.tool_select_feature(self.session_data.edit_feature.data_fid, ['snf', 'snt', 'sgn', 'rfl'])
            self.sys_set_tool_mode('pausing')

    def stm_change_feature_offset(self, data_fid: int = None):
        """set tool mode change_feature_offset: change offset of feature to assigned reference-line with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None

        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
        self.tool_select_feature(data_fid, ['snf', 'snt', 'enf', 'ent', 'sgn', 'sg0', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)

        self.sys_set_tool_mode('change_feature_offset')

    def cpe_change_feature_offset(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas press for tool_mode 'change_feature_offset'"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.edit_feature.ref_fid)
            if reference_geom:
                # dummy, used only as flag for cme_change_offset/cre_change_offset
                # no snap to layer/feature, just calculate offset and draw segment
                self.session_data.pol_mouse_down = self.session_data.edit_feature.pol_from.__copy__()

                point_geom = qgis.core.QgsGeometry.fromPointXY(event.mapPoint())
                point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.derived_settings.refLyr.crs(), qgis.core.QgsProject.instance()))
                point_on_line = reference_geom.closestSegmentWithContext(point_geom.asPoint())
                sqr_dist = point_on_line[0]
                # <0 left, >0 right, ==0 on the line
                side = point_on_line[3]
                abs_dist = math.sqrt(sqr_dist)
                calc_offset = abs_dist * side * -1
                self.session_data.edit_feature.offset = calc_offset
                self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'snt', 'enf', 'ent', 'sgn', 'sg0', 'rfl'])
            else:
                self.dlg_append_log_message('WARNING', error_msg)

    def cme_change_feature_offset(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas move for tool_mode 'change_feature_offset'"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None and self.session_data.pol_mouse_down and event_with_left_btn:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.edit_feature.ref_fid)
            if reference_geom:
                point_geom = qgis.core.QgsGeometry.fromPointXY(event.mapPoint())
                point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.derived_settings.refLyr.crs(), qgis.core.QgsProject.instance()))
                point_on_line = reference_geom.closestSegmentWithContext(point_geom.asPoint())
                sqr_dist = point_on_line[0]
                # <0 left, >0 right, ==0 on the line
                side = point_on_line[3]
                abs_dist = math.sqrt(sqr_dist)
                calc_offset = abs_dist * side * -1
                self.session_data.edit_feature.offset = calc_offset
                self.cvs_draw_feature(self.session_data.edit_feature, ['snf', 'snt', 'enf', 'ent', 'sgn', 'sg0', 'rfl'])
            else:
                self.dlg_append_log_message('WARNING', error_msg)

    def cre_change_feature_offset(self, event: qgis.gui.QgsMapMouseEvent):
        """ canvas release for tool_mode 'change_feature_offset'"""
        # Rev. 2024-06-18
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.pol_mouse_down and self.session_data.edit_feature is not None:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.edit_feature.ref_fid)
            if reference_geom:
                point_geom = qgis.core.QgsGeometry.fromPointXY(event.mapPoint())
                point_geom.transform(qgis.core.QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), self.derived_settings.refLyr.crs(), qgis.core.QgsProject.instance()))
                point_on_line = reference_geom.closestSegmentWithContext(point_geom.asPoint())
                sqr_dist = point_on_line[0]
                # <0 left, >0 right, ==0 on the line
                side = point_on_line[3]
                abs_dist = math.sqrt(sqr_dist)
                calc_offset = abs_dist * side * -1
                self.session_data.edit_feature.offset = calc_offset
                self.tool_save_edit_feature(self.session_data.edit_feature)
            else:
                self.dlg_append_log_message('WARNING', error_msg)

            self.session_data.pol_mouse_down = None
            self.tool_select_feature(self.session_data.edit_feature.data_fid, ['snf', 'snt', 'sgn', 'rfl'])
            self.sys_set_tool_mode('pausing')

    def stm_set_po_pro_from_point(self, data_fid: int = None):
        """set tool mode set_po_pro_from_point: re-stationing Post-Processing-Feature on assigned reference-line with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None

        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        if data_fid in self.session_data.po_pro_data_cache:
            self.cvs_hide_markers()
            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            self.tool_select_po_pro_feature(data_fid, ['snf', 'enf', 'cnf'], ['snf', 'cnf'], extent_mode)
            self.sys_set_tool_mode('set_po_pro_from_point')

        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('po_pro_data_feature_not_in_cache', data_fid))

    def cpe_set_po_pro_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasPressEvent for tool-mode set_po_pro_from_point: re-stationing Post-Processing-Feature on assigned reference-line with immediate storage
                :param event:"""
        # Rev. 2024-06-18
        # self.cvs_hide_markers()
        self.session_data.pol_mouse_down = None
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)
            if match.isValid():
                self.session_data.pol_mouse_down = pol_mouse_down
                # self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['enf'])
                self.session_data.po_pro_feature.set_pol_from(pol_mouse_down)
                self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snf', 'cnf'])
            else:
                # mousePress without match
                self.stm_set_po_pro_from_point()
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_press_match_on_reference_layer'))

    def cme_set_po_pro_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasMoveEvent for tool-mode set_po_pro_from_point: re-stationing Post-Processing-Feature on assigned reference-line with immediate storage
                        :param event:"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)
            if self.session_data.pol_mouse_down and event_with_left_btn:
                self.cvs_hide_snap()
                if match.isValid():
                    # mouse-move after press and cursor on assigned reference-feature
                    self.session_data.po_pro_feature.set_pol_from(pol_mouse_move)
                    self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snf', 'cnf'])
            else:
                # mouse-move before press => only show snap-indicator, if cursor is on assigned reference-feature
                self.cvs_show_snap(match)

    def cre_set_po_pro_from_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasReleaseEvent for tool-mode set_po_pro_from_point: re-stationing Post-Processing-Feature on assigned reference-line with immediate storage
                        :param event:"""
        # Rev. 2024-06-18
        self.cvs_hide_markers()
        self.cvs_hide_snap()
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None and self.session_data.pol_mouse_down is not None:
            pol_mouse_up = PoLFeature()
            match = pol_mouse_up.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)
            if match.isValid():
                self.session_data.po_pro_feature.set_pol_from(pol_mouse_up)

            self.tool_save_edit_feature(self.session_data.po_pro_feature)

        self.session_data.pol_mouse_down = None
        self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snf'])
        self.sys_set_tool_mode('pausing')

    def stm_set_po_pro_to_point(self, data_fid: int = None):
        """set tool mode set_po_pro_from_point: re-stationing feature on assigned reference-line with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-18
        self.cvs_hide_markers()
        self.session_data.pol_mouse_down = None

        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        if data_fid in self.session_data.po_pro_data_cache:
            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            self.tool_select_po_pro_feature(data_fid, ['snt', 'ent', 'cnt'], ['snt', 'cnt'], extent_mode)
            self.sys_set_tool_mode('set_po_pro_to_point')
        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('po_pro_data_feature_not_in_cache', data_fid))

    def cpe_set_po_pro_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasPressEvent for tool-mode set_po_pro_from_point: re-stationing Post-Processing-Feature on assigned reference-line with immediate storage
                :param event:"""
        # Rev. 2024-06-18
        self.session_data.pol_mouse_down = None
        self.cvs_hide_markers()
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)
            if match.isValid():
                self.session_data.pol_mouse_down = pol_mouse_down
                # first draw enf on original stationing
                self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['ent'])
                self.session_data.po_pro_feature.set_pol_to(pol_mouse_down)
                self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snt', 'cnt'])

            else:
                # mousePress without match
                self.stm_set_po_pro_to_point()
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_press_match_on_reference_layer'))

    def cme_set_po_pro_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasMoveEvent for tool-mode set_po_pro_to_point: re-stationing Post-Processing-Feature on assigned reference-line with immediate storage
                        :param event:"""
        # Rev. 2024-06-18
        event_with_left_btn = bool(QtCore.Qt.LeftButton & event.buttons())
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)

            if self.session_data.pol_mouse_down and event_with_left_btn:
                self.cvs_hide_snap()
                if match.isValid():
                    # mouse-move after press and cursor on assigned reference-feature
                    self.session_data.po_pro_feature.set_pol_to(pol_mouse_move)
                    self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snt', 'cnt'])
            else:
                # mouse-move before press => only show snap-indicator, if cursor is on assigned reference-feature
                self.cvs_show_snap(match)

    def cre_set_po_pro_to_point(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasReleaseEvent for tool-mode set_po_pro_to_point: re-stationing Post-Processing-Feature on assigned reference-line with immediate storage
                        :param event:"""
        # Rev. 2024-06-18
        self.cvs_hide_markers()
        self.cvs_hide_snap()
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None and self.session_data.pol_mouse_down is not None:
            pol_mouse_up = PoLFeature()
            match = pol_mouse_up.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)
            if match.isValid():
                self.session_data.po_pro_feature.set_pol_to(pol_mouse_up)

            self.tool_save_edit_feature(self.session_data.po_pro_feature)

        self.session_data.pol_mouse_down = None
        self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snt'])
        self.sys_set_tool_mode('pausing')

    def stm_move_po_pro_feature(self, data_fid: int = None):
        """set tool mode move_po_pro_feature: re-stationing post-processing-feature on assigned reference-line with immediate storage
            :param data_fid: as parameter, else stored as property in cell-widget"""
        # Rev. 2024-06-20
        self.cvs_hide_markers()
        self.session_data.pol_mouse_move = None
        if not data_fid and self.sender():
            data_fid = self.sender().property('data_fid')

        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs:
            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            self.tool_select_po_pro_feature(data_fid, ['snf', 'snt', 'enf', 'ent', 'cnf', 'cnt'], ['snf', 'snt', 'sgn', 'cnf', 'cnt', 'csgn'], extent_mode)
            self.sys_set_tool_mode('move_po_pro_feature')
        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('data_layer_not_editable'))

    def cpe_move_po_pro_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasPressEvent for tool-mode move_po_pro_feature
                        :param event:"""
        # Rev. 2024-06-20
        # self.cvs_hide_markers()
        self.session_data.pol_mouse_move = None
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
            pol_mouse_down = PoLFeature()
            match = pol_mouse_down.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)

            if match.isValid():
                # this tool uses the last move-stationing, not the mouse-down-stationing!
                # 'enf', 'ent',
                self.session_data.pol_mouse_move = pol_mouse_down
                self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snf', 'snt', 'cnf', 'cnt'])
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_match_on_reference_geom', self.session_data.po_pro_feature.ref_fid))

    def cme_move_po_pro_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasMoveEvent for tool-mode move_po_pro_feature
                        :param event:"""
        # Rev. 2024-06-20
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)
            self.cvs_show_snap(match)
            if match.isValid() and self.session_data.pol_mouse_move is not None:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.po_pro_feature.ref_fid)
                if reference_geom:
                    ref_len = reference_geom.length()
                    # delta is calculated from current pol_mouse_move to last self.session_data.pol_mouse_move
                    delta = pol_mouse_move.snap_n_abs - self.session_data.pol_mouse_move.snap_n_abs
                    old_from = self.session_data.po_pro_feature.pol_from.snap_n_abs
                    old_to = self.session_data.po_pro_feature.pol_to.snap_n_abs
                    old_len = abs(old_to - old_from)

                    new_from = old_from + delta
                    new_to = old_to + delta

                    if new_to > ref_len or new_from > ref_len:
                        new_to = ref_len
                        new_from = ref_len - old_len

                    if new_from < 0 or new_to < 0:
                        new_from = 0
                        new_to = old_len

                    self.session_data.po_pro_feature.pol_from.recalc_by_stationing(new_from, 'Nabs')
                    self.session_data.po_pro_feature.pol_to.recalc_by_stationing(new_to, 'Nabs')
                    #'enf', 'ent',
                    self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snf', 'snt', 'cnf', 'cnt'])

                    # store this stationing for the next mouse-move-call
                    self.session_data.pol_mouse_move = pol_mouse_move
                else:
                    self.dlg_append_log_message('WARNING', error_msg)

    def cre_move_po_pro_feature(self, event: qgis.gui.QgsMapMouseEvent):
        """canvasReleaseEvent for tool-mode move_po_pro_feature
                        :param event:"""
        # Rev. 2024-06-20
        self.cvs_hide_markers()
        self.cvs_hide_snap()
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
            pol_mouse_move = PoLFeature()
            match = pol_mouse_move.snap_to_layer(event, self.derived_settings.refLyr, self.session_data.po_pro_feature.ref_fid)

            if match.isValid():
                if self.session_data.pol_mouse_move is not None:
                    reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.po_pro_feature.ref_fid)
                    if reference_geom:
                        ref_len = reference_geom.length()
                        # delta is calculated from current pol_mouse_move to last self.session_data.pol_mouse_move
                        delta = pol_mouse_move.snap_n_abs - self.session_data.pol_mouse_move.snap_n_abs
                        old_from = self.session_data.po_pro_feature.pol_from.snap_n_abs
                        old_to = self.session_data.po_pro_feature.pol_to.snap_n_abs
                        old_len = abs(old_to - old_from)

                        new_from = old_from + delta
                        new_to = old_to + delta

                        if new_to > ref_len or new_from > ref_len:
                            new_to = ref_len
                            new_from = ref_len - old_len

                        if new_from < 0 or new_to < 0:
                            new_from = 0
                            new_to = old_len

                        self.session_data.po_pro_feature.pol_from.recalc_by_stationing(new_from, 'Nabs')
                        self.session_data.po_pro_feature.pol_to.recalc_by_stationing(new_to, 'Nabs')
                        self.tool_save_edit_feature(self.session_data.po_pro_feature)
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_match_on_reference_geom', self.session_data.po_pro_feature.ref_fid))

        self.session_data.pol_mouse_move = None
        self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, ['snf', 'snt'])
        self.sys_set_tool_mode('pausing')

    def cvs_hide_snap(self):
        """hides self.snap_indicator by setting invalid match"""
        # Rev. 2024-07-12
        self.snap_indicator.setMatch(qgis.core.QgsPointLocator.Match())

    def cvs_show_snap(self, match:qgis.core.QgsPointLocator.Match):
        """shows self.snap_indicator"""
        # Rev. 2024-07-12
        self.snap_indicator.setMatch(match)

    def tool_save_edit_feature(self, edit_feature: LoLFeature):
        """save feature to data-layer
        :param edit_feature: self.session_data.edit_feature/self.session_data.po_pro_feature"""
        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs:
            data_feature, error_msg = self.tool_get_data_feature(data_fid=edit_feature.data_fid)

            if data_feature:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=edit_feature.ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():

                        # the stationings and offset are taken from edit_feature as is without new validity-check
                        pol_from = edit_feature.pol_from
                        pol_to = edit_feature.pol_to

                        if pol_from and pol_to and pol_from.snap_n_abs > pol_to.snap_n_abs:
                            pol_from, pol_to = pol_to, pol_from
                            self.dlg_append_log_message('INFO', MY_DICT.tr('from_to_switched'))

                        stationing_from = stationing_to = None

                        if self.stored_settings.lrMode == 'Nabs':
                            if pol_from and pol_from.is_valid:
                                stationing_from = pol_from.snap_n_abs
                            if pol_to and pol_to.is_valid:
                                stationing_to = pol_to.snap_n_abs
                        elif self.stored_settings.lrMode == 'Nfract':
                            if pol_from and pol_from.is_valid:
                                stationing_from = pol_from.snap_n_fract
                            if pol_to and pol_to.is_valid:
                                stationing_to = pol_to.snap_n_fract
                        elif self.stored_settings.lrMode == 'Mabs':
                            if pol_from and pol_from.is_valid:
                                stationing_from = pol_from.snap_m_abs
                            if pol_to and pol_to.is_valid:
                                stationing_to = pol_to.snap_m_abs
                        else:
                            raise NotImplementedError(f"lr_mode '{self.stored_settings.lrMode}' not implemented")

                        offset = edit_feature.offset

                        if self.stored_settings.storagePrecision >= 0:
                            if stationing_from is not None:
                                stationing_from = round(stationing_from, self.stored_settings.storagePrecision)
                            if stationing_to is not None:
                                stationing_to = round(stationing_to, self.stored_settings.storagePrecision)
                            if offset is not None:
                                offset = round(offset, self.stored_settings.storagePrecision)

                        data_feature[self.derived_settings.dataLyrReferenceField.name()] = ref_feature[self.derived_settings.refLyrIdField.name()]
                        data_feature[self.derived_settings.dataLyrStationingFromField.name()] = stationing_from
                        data_feature[self.derived_settings.dataLyrStationingToField.name()] = stationing_to
                        data_feature[self.derived_settings.dataLyrOffsetField.name()] = offset

                        self.derived_settings.dataLyr.beginEditCommand('save_edit_feature')
                        self.derived_settings.dataLyr.updateFeature(data_feature)
                        self.derived_settings.dataLyr.endEditCommand()
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', error_msg)
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('data_layer_not_editable'), True)

    def s_project_layers_removed(self, removed_layer_ids: typing.Iterable[str]):
        """triggered by qgis.core.QgsProject.instance().layersRemoved
        check settings, refresh dialog
        :param removed_layer_ids: List of removed layer-IDs, mostly only one
        """
        # Rev. 2024-06-20
        re_init_dialog = False
        affected_virtual_layer_ids = []

        for layer_id in removed_layer_ids:
            # detect orphaned virtual Show-Layer
            for cl in qgis.core.QgsProject.instance().mapLayers().values():
                if cl.isValid() and cl.dataProvider().name() == 'virtual' and layer_id in cl.dataProvider().uri().uri():
                    affected_virtual_layer_ids.append(cl.id())

            # check if it was a plugin-used layer
            re_init_dialog |= layer_id in [self.stored_settings.refLyrId, self.stored_settings.dataLyrId, self.stored_settings.showLyrId]

        self.sys_check_settings()
        # allways refresh settings-section, f. e. the combo-boxes for layer- and field-selection
        self.dlg_refresh_layer_settings_section()

        if re_init_dialog:
            self.session_data = SessionData()
            self.cvs_hide_markers()
            self.dlg_refresh_po_pro_section()
            self.dlg_refresh_qcbn_reference_feature()
            self.dlg_clear_measurements()
            self.dlg_refresh_measure_section()
            self.dlg_refresh_feature_selection_section()
            self.dlg_apply_ref_lyr_crs()
            self.dlg_append_log_message('INFO', MY_DICT.tr('plugin_used_layer_removed'))

        # second run: delete orphaned virtual layers,
        # double-check, if they weren't already deleted within removed_layer_ids
        for affected_layer_id in affected_virtual_layer_ids:
            # check 1
            if affected_layer_id not in removed_layer_ids:
                cl = qgis.core.QgsProject.instance().mapLayer(affected_layer_id)
                # check 2
                if cl:
                    dialog_result = QtWidgets.QMessageBox.question(
                        None,
                        f"LinearReferencing ({get_debug_pos()})",
                        MY_DICT.tr('delete_orphaned_virtual_layer', cl.name()),
                        buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                        defaultButton=QtWidgets.QMessageBox.Yes
                    )

                    if dialog_result == QtWidgets.QMessageBox.Yes:
                        # check 3: try/catch to avoid "RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted"
                        # note: the layer-removal will trigger the current function again
                        try:
                            qgis.core.QgsProject.instance().removeMapLayer(cl.id())
                        except Exception as e:
                            pass

    def s_project_layers_added(self, layers: typing.Iterable[qgis.core.QgsMapLayer]):
        """triggered by qgis.core.QgsProject.instance().layersAdded
        refresh GUI (settings/dialogs) of the MapTools if necessary
        :param layers: list of layer-objects
        """
        # Rev. 2024-06-20

        # Note: sys_check_settings will connect this layer as reference-layer, if there was none connected before
        self.sys_check_settings()

        # refresh settings, f.e. update the layer-selection-widgets
        self.dlg_refresh_layer_settings_section()

        for cl in layers:
            if cl == self.derived_settings.refLyr:
                # if no reference-layer so far it will be auto-connected by sys_check_settings
                # => re-populate qlbl_selected_reference_layer and qcbn_reference_feature
                self.dlg_refresh_qcbn_reference_feature()

                # refresh measure-widgets (function-elements, line-edits, spinboxes...) if a reference-layer was auto-connected
                self.dlg_refresh_measure_section()
                self.dlg_apply_ref_lyr_crs()
                self.dlg_append_log_message('INFO', MY_DICT.tr('reference_layer_auto_loaded', cl.name()))
                break

    def dlg_init(self):
        """(re)initializes the dialog"""
        # Rev. 2024-06-20
        # default-size and position on first init:
        flotate = True
        start_pos_x = int(self.iface.mainWindow().x() + 0.15 * self.iface.mainWindow().width())
        start_pos_y = int(self.iface.mainWindow().y() + 0.15 * self.iface.mainWindow().height())
        start_width = 720
        start_height = 460
        initial_tab_index = 0

        # if dialog already existed: store its size/position... to open the new one with same size/position...
        if self.my_dialog:
            if self.my_dialog.isFloating():
                start_pos_x = self.my_dialog.x()
                start_pos_y = self.my_dialog.y()
                start_width = self.my_dialog.width()
                start_height = self.my_dialog.height()
            else:
                flotate = False

            initial_tab_index = self.my_dialog.tbw_central.currentIndex()
            # close *and* delete dialog
            self.my_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            self.my_dialog.close()

        # the new one!
        self.my_dialog = dialogs.LolDialog(self.iface)

        # ...docked to QGis-Main-Window
        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.my_dialog)

        # ...floating as before
        self.my_dialog.setFloating(flotate)

        if flotate:
            # ...same size and position as floating before
            self.my_dialog.setGeometry(start_pos_x, start_pos_y, start_width, start_height)

        # ...same open tab as before
        self.my_dialog.tbw_central.setCurrentIndex(initial_tab_index)

        # some custom signals
        self.my_dialog.dialog_close.connect(self.s_dialog_close)
        # sometimes disturbing:
        # reset toolmode if the dialog gets the focus
        # therefore commented
        # self.my_dialog.dialog_activated.connect(self.s_dialog_activated)

        # signal/slot assignments for dialog-widgets
        # Section "Stationing"
        self.my_dialog.qcbn_reference_feature.currentIndexChanged.connect(self.s_select_current_ref_fid)
        self.my_dialog.dspbx_offset.valueChanged.connect(self.s_change_offset)
        self.my_dialog.pb_open_ref_form.pressed.connect(self.s_open_ref_form)
        self.my_dialog.pb_zoom_to_ref_feature.pressed.connect(self.s_zoom_to_ref_feature)
        self.my_dialog.pb_set_from_point.clicked.connect(self.stm_set_from_point)
        self.my_dialog.pb_set_to_point.clicked.connect(self.stm_set_to_point)

        self.my_dialog.pb_toggle_n_abs_grp.pressed.connect(self.dlg_toggle_n_abs_grp)
        self.my_dialog.pb_toggle_n_fract_grp.pressed.connect(self.dlg_toggle_n_fract_grp)
        self.my_dialog.pb_toggle_m_abs_grp.pressed.connect(self.dlg_toggle_m_abs_grp)
        self.my_dialog.pb_toggle_m_fract_grp.pressed.connect(self.dlg_toggle_m_fract_grp)
        self.my_dialog.pb_toggle_z_grp.pressed.connect(self.dlg_toggle_z_grp)

        self.my_dialog.dspbx_n_abs_from.valueChanged.connect(self.s_n_abs_from_edited)
        self.my_dialog.dspbx_n_abs_to.valueChanged.connect(self.s_n_abs_to_edited)
        self.my_dialog.dspbx_n_fract_from.valueChanged.connect(self.s_n_fract_from_edited)
        self.my_dialog.dspbx_n_fract_to.valueChanged.connect(self.s_n_fract_to_edited)

        self.my_dialog.dspbx_delta_n_abs.valueChanged.connect(self.s_delta_n_abs_edited)
        self.my_dialog.dspbx_delta_n_fract.valueChanged.connect(self.s_delta_n_fract_edited)

        self.my_dialog.dspbx_delta_m_abs.valueChanged.connect(self.s_delta_m_abs_edited)
        self.my_dialog.dspbx_delta_m_fract.valueChanged.connect(self.s_delta_m_fract_edited)

        self.my_dialog.dspbx_m_abs_from.valueChanged.connect(self.s_m_abs_from_edited)
        self.my_dialog.dspbx_m_abs_to.valueChanged.connect(self.s_m_abs_to_edited)
        self.my_dialog.dspbx_m_fract_from.valueChanged.connect(self.s_m_fract_from_edited)
        self.my_dialog.dspbx_m_fract_to.valueChanged.connect(self.s_m_fract_to_edited)
        self.my_dialog.tbtn_move_start.pressed.connect(self.s_move_to_start)
        self.my_dialog.tbtn_move_down.pressed.connect(self.s_move_down)
        self.my_dialog.tbtn_move_up.pressed.connect(self.s_move_up)
        self.my_dialog.tbtn_move_end.pressed.connect(self.s_move_to_end)
        self.my_dialog.tbtn_flip_down.pressed.connect(self.s_flip_down)
        self.my_dialog.tbtn_flip_up.pressed.connect(self.s_flip_up)
        self.my_dialog.pb_zoom_to_stationings.pressed.connect(self.s_zoom_to_stationings)
        self.my_dialog.pbtn_resume_stationing.clicked.connect(self.stm_measure_segment)
        self.my_dialog.pbtn_insert_stationing.pressed.connect(self.s_insert_stationing)
        self.my_dialog.pbtn_update_stationing.pressed.connect(self.s_update_stationing)
        self.my_dialog.pb_move_segment.clicked.connect(self.stm_move_segment)
        self.my_dialog.pb_change_offset.clicked.connect(self.stm_change_offset)

        # Section "Feature-Selection":
        self.my_dialog.pbtn_select_features.clicked.connect(self.stm_select_features)
        self.my_dialog.pbtn_append_data_features.pressed.connect(self.s_append_data_features)
        self.my_dialog.pbtn_append_show_features.pressed.connect(self.s_append_show_features)
        self.my_dialog.pbtn_zoom_to_feature_selection.pressed.connect(self.s_zoom_to_feature_selection)
        self.my_dialog.pbtn_clear_features.pressed.connect(self.s_clear_feature_selection)
        self.my_dialog.pbtn_transfer_feature_selection.pressed.connect(self.s_transfer_feature_selection)
        self.my_dialog.pbtn_feature_selection_to_data_layer_filter.pressed.connect(self.s_feature_selection_to_data_layer_filter)

        self.my_dialog.qtrv_feature_selection.doubleClicked.connect(self.st_qtrv_feature_selection_double_click)
        self.my_dialog.qtrv_feature_selection.selectionModel().selectionChanged.connect(self.st_qtrv_feature_selection_selection_changed)

        # Section Post-Processing
        self.my_dialog.pbtn_zoom_po_pro.pressed.connect(self.s_zoom_to_po_pro_selection)
        self.my_dialog.pbtn_clear_po_pro.pressed.connect(self.s_clear_post_processing)
        self.my_dialog.qtrv_po_pro_selection.doubleClicked.connect(self.st_qtrv_post_processing_double_click)
        self.my_dialog.qtrv_po_pro_selection.selectionModel().selectionChanged.connect(self.st_qtrv_po_pro_selection_selection_changed)

        # Section "Layers and Fields"
        self.my_dialog.qcbn_reference_layer.currentIndexChanged.connect(self.ssc_reference_layer)
        self.my_dialog.qcbn_ref_lyr_id_field.currentIndexChanged.connect(self.ssc_ref_lyr_id_field)
        self.my_dialog.pb_open_ref_tbl.pressed.connect(self.s_open_ref_tbl)
        self.my_dialog.pb_call_ref_disp_exp_dlg.pressed.connect(self.s_define_ref_lyr_display_expression)
        self.my_dialog.qcbn_data_layer.currentIndexChanged.connect(self.ssc_data_layer)
        self.my_dialog.pb_open_data_tbl.pressed.connect(self.s_open_data_tbl)
        self.my_dialog.pb_open_data_tbl_2.pressed.connect(self.s_open_data_tbl)
        self.my_dialog.pbtn_create_data_layer.pressed.connect(self.sys_create_data_layer)
        self.my_dialog.pb_call_data_disp_exp_dlg.pressed.connect(self.s_define_data_lyr_display_expression)
        self.my_dialog.qcbn_data_layer_id_field.currentIndexChanged.connect(self.ssc_data_layer_id_field)
        self.my_dialog.qcbn_data_layer_reference_field.currentIndexChanged.connect(self.ssc_data_layer_reference_field)
        self.my_dialog.qcbn_data_layer_offset_field.currentIndexChanged.connect(self.ssc_data_layer_offset_field)
        self.my_dialog.qcbn_data_layer_stationing_from_field.currentIndexChanged.connect(self.ssc_data_layer_stationing_from_field)
        self.my_dialog.qcbn_data_layer_stationing_to_field.currentIndexChanged.connect(self.ssc_data_layer_stationing_to_field)
        self.my_dialog.qcb_lr_mode.currentIndexChanged.connect(self.scc_lr_mode)
        self.my_dialog.qcb_storage_precision.currentIndexChanged.connect(self.scc_storage_precision)

        self.my_dialog.qcbn_show_layer.currentIndexChanged.connect(self.ssc_show_layer)
        self.my_dialog.pb_open_show_tbl.pressed.connect(self.s_open_show_tbl)
        self.my_dialog.pb_open_show_tbl_2.pressed.connect(self.s_open_show_tbl)
        self.my_dialog.pb_edit_show_layer_display_expression.pressed.connect(self.s_define_show_layer_display_expression)
        self.my_dialog.pbtn_create_show_layer.pressed.connect(self.sys_create_show_layer)

        self.my_dialog.qcbn_show_layer_back_reference_field.currentIndexChanged.connect(self.ssc_show_layer_back_reference_field)

        # Section "Styles"
        self.my_dialog.qcb_pt_snf_icon_type.currentIndexChanged.connect(self.scc_pt_snf_icon_type)
        self.my_dialog.qspb_pt_snf_icon_size.valueChanged.connect(self.scc_pt_snf_icon_size)
        self.my_dialog.qspb_pt_snf_pen_width.valueChanged.connect(self.scc_pt_snf_pen_width)
        self.my_dialog.qpb_pt_snf_color.color_changed.connect(self.scc_pt_snf_color)
        self.my_dialog.qpb_pt_snf_fill_color.color_changed.connect(self.scc_pt_snf_fill_color)

        self.my_dialog.qcb_pt_snt_icon_type.currentIndexChanged.connect(self.scc_pt_snt_icon_type)
        self.my_dialog.qspb_pt_snt_icon_size.valueChanged.connect(self.scc_pt_snt_icon_size)
        self.my_dialog.qspb_pt_snt_pen_width.valueChanged.connect(self.scc_pt_snt_pen_width)
        self.my_dialog.qpb_pt_snt_color.color_changed.connect(self.scc_pt_snt_color)
        self.my_dialog.qpb_pt_snt_fill_color.color_changed.connect(self.scc_pt_snt_fill_color)

        self.my_dialog.qpb_ref_line_color.color_changed.connect(self.scc_ref_line_color)
        self.my_dialog.qcb_ref_line_style.currentIndexChanged.connect(self.scc_ref_line_style)
        self.my_dialog.qspb_ref_line_width.valueChanged.connect(self.scc_ref_line_width)

        self.my_dialog.qpb_segment_line_color.color_changed.connect(self.scc_segment_line_color)
        self.my_dialog.qcb_segment_line_style.currentIndexChanged.connect(self.scc_segment_line_style)
        self.my_dialog.qspb_segment_line_width.valueChanged.connect(self.scc_segment_line_width)
        self.my_dialog.pb_reset_style.pressed.connect(self.scc_reset_style)

        self.my_dialog.pb_store_configuration.pressed.connect(self.s_store_configuration)
        self.my_dialog.pb_delete_configuration.pressed.connect(self.s_delete_configuration)
        self.my_dialog.pb_restore_configuration.pressed.connect(self.s_restore_configuration)

        self.my_dialog.pbtn_clear_log_messages.pressed.connect(self.dlg_clear_log_messages)
        self.my_dialog.pbtn_check_log_messages.pressed.connect(self.dlg_check_log_messages)

        # some customizations on select-colors for QTableWidgets, default is blue and white-text, changed to yellow and black text
        # must be defined here (not in LolDialog.py), presumably because the palette is altered to QGis-Application-Default if the dialog-window is opened
        pal = self.my_dialog.qtrv_feature_selection.palette()
        hightlight_brush = pal.brush(QtGui.QPalette.Highlight)
        hightlight_brush.setColor(QtGui.QColor('#AAFFF09D'))
        pal.setBrush(QtGui.QPalette.Highlight, hightlight_brush)
        pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor('#000000'))
        self.my_dialog.qtrv_feature_selection.setPalette(pal)

        pal = self.my_dialog.qtrv_po_pro_selection.palette()
        hightlight_brush = pal.brush(QtGui.QPalette.Highlight)
        hightlight_brush.setColor(QtGui.QColor('#AAFFF09D'))
        pal.setBrush(QtGui.QPalette.Highlight, hightlight_brush)
        pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor('#000000'))
        self.my_dialog.qtrv_po_pro_selection.setPalette(pal)

        self.dlg_refresh_po_pro_section()
        self.dlg_refresh_qcbn_reference_feature()
        self.dlg_clear_measurements()
        self.dlg_refresh_measure_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_style_settings_section()
        self.dlg_refresh_layer_settings_section()
        self.dlg_refresh_stored_settings_section()

        self.dlg_apply_ref_lyr_crs()
        self.dlg_apply_storage_precision()
        self.dlg_apply_locale()
        self.dlg_apply_canvas_crs()

        self.my_dialog.status_bar.clearMessage()

    def dlg_toggle_n_abs_grp(self):
        """toggle visibility of dialog-part"""
        # Rev. 2024-07-28
        minus_icon = QtGui.QIcon(':icons/minus-box-outline.svg')
        plus_icon = QtGui.QIcon(':icons/plus-box-outline.svg')

        toggle_widgets = [
            self.my_dialog.qlbl_n_abs,
            self.my_dialog.dspbx_n_abs_from,
            self.my_dialog.dspbx_n_abs_to,
            self.my_dialog.qlbl_unit_n_abs,
            self.my_dialog.qlbl_delta_n_abs,
            self.my_dialog.dspbx_delta_n_abs,
            self.my_dialog.qlbl_unit_delta_n_abs
        ]

        if self.my_dialog.qlbl_n_abs.isVisible():
            self.my_dialog.pb_toggle_n_abs_grp.setIcon(plus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(False)
        else:
            self.my_dialog.pb_toggle_n_abs_grp.setIcon(minus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(True)

    def dlg_toggle_n_fract_grp(self):
        """toggle visibility of dialog-part"""
        # Rev. 2024-07-28
        minus_icon = QtGui.QIcon(':icons/minus-box-outline.svg')
        plus_icon = QtGui.QIcon(':icons/plus-box-outline.svg')

        toggle_widgets = [
            self.my_dialog.qlbl_n_fract,
            self.my_dialog.dspbx_n_fract_from,
            self.my_dialog.dspbx_n_fract_to,
            self.my_dialog.qlbl_unit_n_fract,
            self.my_dialog.qlbl_delta_n_fract,
            self.my_dialog.dspbx_delta_n_fract,
            self.my_dialog.qlbl_unit_delta_n_fract
        ]

        if self.my_dialog.qlbl_n_fract.isVisible():
            self.my_dialog.pb_toggle_n_fract_grp.setIcon(plus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(False)
        else:
            self.my_dialog.pb_toggle_n_fract_grp.setIcon(minus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(True)

    def dlg_toggle_m_abs_grp(self):
        """toggle visibility of dialog-part"""
        # Rev. 2024-07-28
        minus_icon = QtGui.QIcon(':icons/minus-box-outline.svg')
        plus_icon = QtGui.QIcon(':icons/plus-box-outline.svg')

        toggle_widgets = [
            self.my_dialog.qlbl_m_abs,
            self.my_dialog.dspbx_m_abs_from,
            self.my_dialog.dspbx_m_abs_to,
            self.my_dialog.qlbl_unit_m_abs,
            self.my_dialog.qlbl_delta_m_abs,
            self.my_dialog.dspbx_delta_m_abs,
            self.my_dialog.qlbl_unit_delta_m_abs,
            self.my_dialog.qlbl_m_abs_valid_hint
        ]

        if self.my_dialog.qlbl_m_abs.isVisible():
            self.my_dialog.pb_toggle_m_abs_grp.setIcon(plus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(False)
        else:
            self.my_dialog.pb_toggle_m_abs_grp.setIcon(minus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(True)

    def dlg_toggle_m_fract_grp(self):
        """toggle visibility of dialog-part"""
        # Rev. 2024-07-28
        minus_icon = QtGui.QIcon(':icons/minus-box-outline.svg')
        plus_icon = QtGui.QIcon(':icons/plus-box-outline.svg')

        toggle_widgets = [
            self.my_dialog.qlbl_m_fract,
            self.my_dialog.dspbx_m_fract_from,
            self.my_dialog.dspbx_m_fract_to,
            self.my_dialog.qlbl_unit_m_fract,
            self.my_dialog.qlbl_delta_m_fract,
            self.my_dialog.dspbx_delta_m_fract,
            self.my_dialog.qlbl_unit_delta_m_fract,
            self.my_dialog.qlbl_m_fract_valid_hint
        ]

        if self.my_dialog.qlbl_m_fract.isVisible():
            self.my_dialog.pb_toggle_m_fract_grp.setIcon(plus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(False)
        else:
            self.my_dialog.pb_toggle_m_fract_grp.setIcon(minus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(True)

    def dlg_toggle_z_grp(self):
        """toggle visibility of dialog-part"""
        # Rev. 2024-07-28
        minus_icon = QtGui.QIcon(':icons/minus-box-outline.svg')
        plus_icon = QtGui.QIcon(':icons/plus-box-outline.svg')

        toggle_widgets = [
            self.my_dialog.qlbl_z,
            self.my_dialog.dnspbx_z_from,
            self.my_dialog.dnspbx_z_to,
            self.my_dialog.qlbl_z_unit,
            self.my_dialog.qlbl_delta_z,
            self.my_dialog.dnspbx_delta_z_abs,
            self.my_dialog.qlbl_delta_z_unit
        ]

        if self.my_dialog.qlbl_z.isVisible():
            self.my_dialog.pb_toggle_z_grp.setIcon(plus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(False)
        else:
            self.my_dialog.pb_toggle_z_grp.setIcon(minus_icon)
            for wdg in toggle_widgets:
                wdg.setVisible(True)

    def dlg_refresh_stored_settings_section(self):
        """re-populates the list with the stored Configurations"""
        # Rev. 2024-06-20
        if self.my_dialog:
            self.my_dialog.lw_stored_settings.clear()
            for setting_idx in range(self._num_storable_settings):
                setting_label_xpath = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                setting_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', setting_label_xpath)
                # the label is used for display in QListWidget and as "primary key"
                if setting_label and type_conversion_ok:
                    qlwi = QtWidgets.QListWidgetItem()
                    qlwi.setText(setting_label)
                    qlwi.setData(self.configuration_label_role, setting_label)
                    self.my_dialog.lw_stored_settings.addItem(qlwi)

    def s_restore_configuration(self):
        """restores stored configuration from project-file
        takes the selected Item from QListWidget
        uses its label, which serves as client-side unique identifier,
        in qgis-project-file the storage is under XML-Path LinearReferencing/LolEvtStoredSettings/setting_{setting_idx} with setting_idx in range 0...self._num_storable_settings
        """
        # Rev. 2024-06-20
        row_idx = self.my_dialog.lw_stored_settings.currentRow()
        if row_idx < 0:
            self.dlg_append_log_message('INFO', MY_DICT.tr('select_config_from_list'))
            return
        else:
            selected_item = self.my_dialog.lw_stored_settings.item(row_idx)
            selected_label = selected_item.data(self.configuration_label_role)
            for setting_idx in range(self._num_storable_settings):
                setting_label_xpath = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                setting_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', setting_label_xpath)
                if setting_label and type_conversion_ok:
                    if setting_label == selected_label:
                        self.stored_settings = StoredSettings()
                        property_list = [prop for prop in dir(StoredSettings) if prop.startswith('_') and not prop.startswith('__')]

                        for prop_name in property_list:
                            prop_xpath = f"/LolEvtStoredSettings/setting_{setting_idx}/{prop_name}"
                            restored_value, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', prop_xpath)
                            if restored_value and type_conversion_ok:
                                setattr(self.stored_settings, prop_name, restored_value)

                        self.dlg_append_log_message('SUCCESS', MY_DICT.tr('config_restored', setting_label))
                        self.gui_refresh()
                        break

    def s_delete_configuration(self):
        """deletes stored configuration from project-file
        takes the selected Item from QListWidget
        uses its label, which serves as client-side unique identifier,
        in qgis-project-file the storage is under XML-Path LinearReferencing/LolEvtStoredSettings/setting_{setting_idx} with setting_idx in range 0...9
        asks for confirmation
        """

        row_idx = self.my_dialog.lw_stored_settings.currentRow()
        if row_idx < 0:
            self.dlg_append_log_message('INFO', MY_DICT.tr('select_config_from_list'))
        else:
            selected_item = self.my_dialog.lw_stored_settings.item(row_idx)
            # setting_label is used for display (Role 0) and additionally stored with a special role
            selected_label = selected_item.data(self.configuration_label_role)
            for setting_idx in range(self._num_storable_settings):
                # uses the label as unique identifier, although no "unique contraint" with this value possible in XML-Structure of project-file
                setting_label_xpath = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                setting_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', setting_label_xpath)
                if setting_label and type_conversion_ok:
                    if setting_label == selected_label:
                        dialog_result = QtWidgets.QMessageBox.question(
                            None,
                            f"LinearReferencing ({get_debug_pos()})",
                            MY_DICT.tr('delete_config_dlg_txt', setting_label),
                            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                            defaultButton=QtWidgets.QMessageBox.Yes
                        )

                        if dialog_result == QtWidgets.QMessageBox.Yes:
                            setting_xpath = f"/LolEvtStoredSettings/setting_{setting_idx}"
                            qgis.core.QgsProject.instance().removeEntry('LinearReferencing', setting_xpath)
                            self.dlg_refresh_stored_settings_section()
                            self.dlg_append_log_message('SUCCESS', MY_DICT.tr('config_deleted', setting_label))

    def s_store_configuration(self):
        """stores the current configuration in project-file
        prompts user to enter a label, which serves as client-side unique identifier,
        in qgis-project-file the storage is under XML-Path LinearReferencing/LolEvtStoredSettings/setting_{setting_idx} with setting_idx in range 0...9
        asks for confirmation, if the label already exists"""
        # Rev. 2024-06-20
        row_idx = self.my_dialog.lw_stored_settings.currentRow()
        if row_idx < 0:
            # nothing selected
            default_label = datetime.date.today().strftime('%Y-%m-%d')
        else:
            # convenience:  take selected ListItem for overwrite
            selected_item = self.my_dialog.lw_stored_settings.item(row_idx)
            default_label = selected_item.data(self.configuration_label_role)

        new_label, ok = QtWidgets.QInputDialog.getText(
            None,
            f"LinearReferencing ({get_debug_pos()})",
            MY_DICT.tr('config_label_dlg_title'),
            QtWidgets.QLineEdit.Normal,
            default_label
        )
        if not ok or not new_label:
            pass
        else:
            new_idx = None
            not_used_idx = []
            for setting_idx in range(self._num_storable_settings):
                setting_label_xpath = f"/LolEvtStoredSettings/setting_{setting_idx}/setting_label"
                old_label, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', setting_label_xpath)

                if old_label and type_conversion_ok:
                    if old_label == new_label:
                        dialog_result = QtWidgets.QMessageBox.question(
                            None,
                            f"LinearReferencing ({get_debug_pos()})",
                            MY_DICT.tr('replace_config_dlg_txt', new_label),
                            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                            defaultButton=QtWidgets.QMessageBox.Yes
                        )

                        if dialog_result == QtWidgets.QMessageBox.Yes:
                            new_idx = setting_idx
                        else:
                            return
                else:
                    not_used_idx.append(setting_idx)

            # no stored settings with label == new_label found
            if new_idx is None:
                if not_used_idx:
                    # take the first possible un-used one
                    new_idx = not_used_idx.pop(0)
                else:
                    # or no store, if already _num_storable_settings configurations have been stored
                    self.dlg_append_log_message('INFO', MY_DICT.tr('too_many_stored_settings', self._num_storable_settings))
                    return

            property_dict = {prop: getattr(self.stored_settings, prop) for prop in dir(StoredSettings) if prop.startswith('_') and not prop.startswith('__')}

            for prop_name in property_dict:
                prop_value = property_dict[prop_name]
                # other key then LolEvt
                prop_xpath = f"/LolEvtStoredSettings/setting_{new_idx}/{prop_name}"
                qgis.core.QgsProject.instance().writeEntry('LinearReferencing', prop_xpath, prop_value)

            setting_label_xpath = f"/LolEvtStoredSettings/setting_{new_idx}/setting_label"
            qgis.core.QgsProject.instance().writeEntry('LinearReferencing', setting_label_xpath, new_label)

            self.dlg_refresh_stored_settings_section()
            self.dlg_append_log_message('SUCCESS', MY_DICT.tr('config_stored', new_label))

    @QtCore.pyqtSlot(str, str, dict)
    def sys_layer_slot(self, layer_id: str, conn_signal: str, **kwargs):
        """one function for many purposes
        Standard vector-layer-signals usually provide little information to connected slots
          sys_connect_layer_slot uses sys_layer_slot in a lambda-function, which adds additional informations.
          This standard-connect-method executes actions dependend on the emitting layer, the emitting signal and the standard-signal-parameters (kwargs)
         :param layer_id: ID of the layer, whose signal is connected, this ID is checked to identify the layer and his role within the plugin
         :param conn_signal: which signal is emitted
         :param kwargs: any number of key/value, dependend on the connected signal, see https://api.qgis.org/api/classQgsVectorLayer.html
         """
        # Rev. 2024-06-20
        layer = qgis.core.QgsProject.instance().mapLayer(layer_id)
        if layer:
            # Question 1: Which of the currently plugin-used layer (refLyr, dataLyr, showLyr) has emitted the signal?
            # Question 2: What signal was emitted? Dependend on signal different informations are passed through as "kwargs"
            # The further procedure depends on layer-function within this plugin and the triggered conn_signal.
            if layer == self.derived_settings.refLyr:
                if conn_signal == 'subsetStringChanged':
                    # filter altered or cleared
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_qcbn_reference_feature()
                    self.dlg_refresh_po_pro_section()
                elif conn_signal == 'displayExpressionChanged':
                    # changed display-expression
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_qcbn_reference_feature()
                    self.dlg_refresh_po_pro_section()
                elif conn_signal == 'editingStarted':
                    # start new PostProcessing-Session
                    # reset previously cached reference-features
                    if self.session_data.po_pro_reference_cache or self.session_data.po_pro_data_cache:
                        self.dlg_append_log_message('INFO',MY_DICT.tr('reset_po_pro_cache'))

                    self.session_data.po_pro_reference_cache = {}
                    self.session_data.po_pro_data_cache = {}
                    self.dlg_refresh_po_pro_section()
                    self.cvs_hide_markers(['cnf', 'cnt', 'csgn', 'crfl', 'cuca', 'cacu'])
                elif conn_signal == 'afterCommitChanges':
                    # edits in reference-layer committed
                    self.sys_refresh_po_pro_data_cache()
                    self.dlg_refresh_po_pro_section()
                    if len(self.session_data.po_pro_data_cache):
                        # data-features with changed positions after reference-geometry-edit
                        self.dlg_refresh_feature_selection_section()
                        self.my_dialog.show()
                        self.my_dialog.activateWindow()
                        self.my_dialog.tbw_central.setCurrentIndex(2)
                elif conn_signal == 'editCommandEnded':
                    # reference-feature possibly modified (update/insert/delete), not yet committed
                    self.dlg_refresh_po_pro_section()
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_qcbn_reference_feature()
                elif conn_signal == 'editingStopped':
                    # possibly modified (update/insert/delete) reference-feature, committed or rollbacked
                    self.dlg_refresh_po_pro_section()
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_qcbn_reference_feature()
                elif conn_signal == 'geometryChanged':
                    # geometry-change of reference-layer on QGis-side, not provider
                    # triggered for each altered geometry and any kind of geometry-change (vertex-M/Z-value, new vertex, vertex moved, vertex deleted, geometry split with multi-type-layer...)
                    # the original shape (without not yet committed edits) inserted into self.session_data.po_pro_reference_cache
                    # the collected features in po_pro_reference_cache will be evaluated via sys_refresh_po_pro_data_cache after refLyr-conn_signal == 'afterCommitChanges'
                    fid = kwargs['fid']
                    current_geom = kwargs['geometry']

                    self.sys_refresh_po_pro_reference_cache(fid, current_geom)


                elif conn_signal == 'crsChanged':
                    self.sys_check_settings()
                    self.dlg_apply_ref_lyr_crs()

                else:
                    raise NotImplementedError(f"conn_signal '{conn_signal}' on Layer '{layer_id}' not implemented")

            elif layer == self.derived_settings.dataLyr:
                if conn_signal == 'displayExpressionChanged':
                    # data-layers displayExpression has changed => refresh some parts of the dialog
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()
                elif conn_signal == 'attributeValueChanged':
                    """triggered on change of any attribute-value in edit-buffer:
                        changes in data-layer-attribute-form
                            single form: if the form is closed with Save, triggered once for each altered attribute
                            table with form-view (splitted, left feature-list, right form): on every key-stroke
                        changes in attribute-table (on focus-loose after editing (switching to other row or cell), on enter-key-stroke)
                        interactive edits of stationings by this plugin 
                        caution: *triggered once for each altered attribute*
                        usage here:
                        prevent edits of the self.derived_settings.dataLyrIdField (normally an autoincrement-integer, also used as fid)
                        its value *must never be changed* (else error on commit)
                        (see sys_create_data_layer, where the attribut-form for this field is set to readOnly for additional protection)
                        append edited fid to selected_fids
                        see lsl_data_layer_edit_command_ended for dialog-canvas-refresh
                    """
                    # signal emitted with three parameters: fid, idx (attribute index of the changed attribute) and (changed!) value
                    fid = kwargs['fid']
                    idx = kwargs['idx']
                    # value = kwargs['value']

                    # Check, if the user tried to change the fid
                    pk_field_idzs = self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes()
                    # in QGis the fid is allways an integer and the one and only primary key
                    if idx in pk_field_idzs:
                        data_feature, error_msg = self.tool_get_data_feature(data_fid=fid)

                        if data_feature:

                            feature_request = qgis.core.QgsFeatureRequest(fid)
                            request_result = self.derived_settings.dataLyr.dataProvider().getFeatures(feature_request)
                            feature_list = list(request_result)
                            if feature_list:
                                provider_data_feature = feature_list[0]
                                for idx in pk_field_idzs:
                                    data_feature.setAttribute(idx, provider_data_feature[idx])
                                self.derived_settings.dataLyr.updateFeature(data_feature)
                                self.dlg_append_log_message('WARNING', MY_DICT.tr('update_changed_feature_id_not_allowed'))

                    if fid not in self.session_data.selected_fids:
                        self.session_data.selected_fids.append(fid)

                elif conn_signal == 'editCommandStarted':
                    # Signal emitted when a new edit command has been started.
                    # no further action here, just for interest and completeness...
                    # text = kwargs['text']
                    pass
                elif conn_signal == 'editCommandEnded':
                    """ triggered on endEditCommand
                    requires transaction surrounded by beginEditCommand() rsp. endEditCommand()
                    Note: 
                    all QGis-standard-updates/inserts/deletes from feature-forms or -tables use "beginEditCommand/endEditCommand" and will trigger this event, 
                    in tables after each altered cell (!) 
                    in forms on submit
                    no access to altered data, therefore use attributeValueChanged
                    """
                    # self.cvs_hide_markers()

                    if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
                        self.dlg_refresh_feature_selection_section()
                        self.dlg_refresh_po_pro_section()

                    if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
                        self.derived_settings.showLyr.updateExtents()
                        self.derived_settings.showLyr.triggerRepaint()

                    # refresh canvas-graphics, if the feature still exists ('editCommandEnded' could be triggered by delete)
                    if self.session_data.edit_feature:
                        data_feature, error_msg = self.tool_get_data_feature(data_fid=self.session_data.edit_feature.data_fid)
                        if data_feature:
                            self.tool_select_feature(self.session_data.edit_feature.data_fid, ['snf', 'snt', 'sgn', 'rfl'])



                elif conn_signal == 'featureAdded':
                    """emitted when a feature has been added to data-layer, committed and not committed
                    Note:
                        new feature has negative fid, on insert triggered once (afterward editCommandEnded)
                        setting table not editable and/or save edits will trigger three kind of slots:
                        committedFeaturesAdded (once for all features => inser provider with positive fid)
                        featureAdded (once for every feature => insert in QGis with positive fid)
                        featuresDeleted (once for all features => delete in QGis the features with negative fid)
                    """

                    fid = kwargs['fid']

                    # select the new feature
                    self.tool_select_feature(fid, ['snf', 'snt', 'sgn', 'rfl'])

                elif conn_signal == 'editingStarted':
                    # Emitted when editing-session on this layer has started.
                    # set system_vs (instead of sys_check_settings) to enable some edit-buttons

                    self.system_vs |= self.SVS.DATA_LAYER_EDITABLE
                    self.dlg_refresh_measure_section()
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()

                elif conn_signal == 'editingStopped':
                    # Emitted when editing-session on this layer has ended.
                    # some checks because of altered self.derived_settings and enable/disable of some edit-buttons

                    # set system_vs (instead of sys_check_settings) to disable some edit-buttons

                    self.system_vs &= ~self.SVS.DATA_LAYER_EDITABLE
                    self.dlg_refresh_measure_section()
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()
                    # detect and reflect changes of table-structure, new fields, deleted fields...
                    self.dlg_refresh_layer_settings_section()

                elif conn_signal == 'subsetStringChanged':
                    # filter query edited or cleared
                    # layer can not be in edit-mode, so reload without danger of loosing uncommitted features
                    # self.derived_settings.dataLyr.dataProvider().reloadData()
                    # self.derived_settings.dataLyr.reload()

                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()
                    # reload showLayer and get correct updated extents:
                    if self.derived_settings.showLyr is not None:
                        tools.MyTools.set_layer_extent(self.derived_settings.showLyr)
                        self.derived_settings.showLyr.triggerRepaint()
                        self.iface.mapCanvas().refresh()

                elif conn_signal == 'committedFeaturesAdded':
                    # Emitted when features are added to the provider after save of the edit-session
                    # not committed, if addFeature() is directly applied to dataProvider without transaction/edit-buffer
                    # two parameters: layerId and addedFeatures (C: QgsFeatureList Python: list of QgsFeature)
                    # previously uncommitted features with negative fids in QGis will get positive fid, usually the autoincremented integer providerside id-column
                    # the fids will be appended to self.session_data.selected_fids, so that these new features will be displayed in feature-selection
                    # possibly superfluous, because each feature in committedFeaturesAdded has already been handled by featureAdded

                    # layerId = kwargs['layerId']
                    # addedFeatures = kwargs['addedFeatures']

                    self.dlg_refresh_feature_selection_section()

                elif conn_signal == 'featuresDeleted':
                    # Emitted when features were deleted on layer or its edit-buffer before commit
                    # one parameter: fids => fids of deleted features
                    # note:
                    # before commit all new features have a negative fid
                    # on commit these temporary features get deleted and new ones with positive fids were inserted
                    # see committedFeaturesRemoved
                    # see editCcommandEnded for dialog-canvas-refresh
                    # fids = kwargs['fids']

                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()

                elif conn_signal == 'committedAttributeValuesChanges':
                    # Emitted when attribute value changes are saved to the provider if not in transaction mode.
                    # two parameters:
                    # layerId
                    # changedAttributesValues (QgsChangedAttributesMap, dictionary with fid as key)
                    # layerId = kwargs['layerId']
                    # changedAttributesValues = kwargs['changedAttributesValues']

                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()
                elif conn_signal == 'afterCommitChanges':
                    # Emitted after changes are committed to the data provider.
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()
                elif conn_signal == 'committedFeaturesRemoved':
                    # Emitted when features are deleted from the provider if not in transaction mode.
                    # two parameters:
                    # layerId
                    # deletedFeatureIds (list of ids)
                    # layerId = kwargs['layerId']
                    # deletedFeatureIds = kwargs['deletedFeatureIds']
                    self.cvs_hide_markers()
                    self.dlg_refresh_feature_selection_section()
                    self.dlg_refresh_po_pro_section()
                else:
                    raise NotImplementedError(f"conn_signal '{conn_signal}' on Layer '{layer_id}' not implemented")

            elif layer == self.derived_settings.showLyr:
                if conn_signal == 'displayExpressionChanged':
                    # layers displayExpression has changed => refresh some parts of the dialog
                    self.dlg_refresh_feature_selection_section()
                elif conn_signal == 'subsetStringChanged':
                    # layers filter has changed => refresh some parts of the dialog
                    self.dlg_refresh_feature_selection_section()
                elif conn_signal == 'dataSourceChanged':
                    # print("showLyr dataSourceChanged")
                    self.dlg_refresh_feature_selection_section()
                else:
                    raise NotImplementedError(f"conn_signal '{conn_signal}' on Layer '{layer_id}' not implemented")

            else:
                # disconnect orphaned connection-object for previously used plugin-layer
                if layer_id in self.signal_slot_cons:
                    for conn_signal in self.signal_slot_cons[layer_id]:
                        for conn_function in self.signal_slot_cons[layer_id][conn_signal]:
                            conn_id = self.signal_slot_cons[layer_id][conn_signal][conn_function]
                            layer.disconnect(conn_id)

                    del self.signal_slot_cons[layer_id]

    def dlg_apply_ref_lyr_crs(self):
        """applies the reference-layer-projection to coordinate-display in dialog
        affects some QLabel-widgets which show the current unit,
        num decimals of some measurement-widgets and delegates
        step-width of some measurement-spinboxes
        """
        # Rev. 2024-06-22
        if self.my_dialog and self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:

            unit, zoom_pan_tolerance, display_precision, measure_default_step = tools.MyTools.eval_crs_units(self.derived_settings.refLyr.crs().authid())

            for unit_widget in self.my_dialog.layer_unit_widgets:
                unit_widget.setText(f"[{unit}]")

            # set default-step-width for spinbox-click
            # note: some spinboxes with class QDoubleNoSpinBox have no spin-buttons and don't need to be adjusted
            default_step_apply_widgets = [
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_offset,
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_m_abs,
            ]
            for dspbx in default_step_apply_widgets:
                with QtCore.QSignalBlocker(dspbx):
                    dspbx.default_step = measure_default_step

            # fract-spinboxes excluded, whose step-width and precision is layer-projection independend
            # M-Z-spinboxes pragmatically included, although their range could be totaly independend from layer-projection

            precision_apply_widgets = [
                self.my_dialog.dspbx_offset,
                self.my_dialog.dnspbx_snap_x_from,
                self.my_dialog.dnspbx_snap_y_from,
                self.my_dialog.dnspbx_z_from,
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dnspbx_snap_x_to,
                self.my_dialog.dnspbx_snap_y_to,
                self.my_dialog.dnspbx_z_to,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dnspbx_delta_z_abs
            ]

            for dspbx in precision_apply_widgets:
                with QtCore.QSignalBlocker(dspbx):
                    dspbx.setDecimals(display_precision)

            # numerical values inside QTableWidget or QComboBox
            delegates = [
                self.my_dialog.ref_length_delegate,
            ]
            for delegate in delegates:
                delegate.precision = display_precision

            self.my_dialog.update()

    def dlg_apply_storage_precision(self):
        """stationig-delegates, precision depends on LR-Mode and is not predictable for Mabs because of the M-range
        therfore the storagePrecision is used
        """
        # Rev. 2024-09-23
        if self.my_dialog:
            if self.stored_settings.storagePrecision >= 0:
                storage_precision = self.stored_settings.storagePrecision
            else:
                # -1 => no limit
                storage_precision = 5

            stationing_delegates = [
                self.my_dialog.cdlg_1,
                self.my_dialog.cdlg_2,
                self.my_dialog.cdlg_3,
                self.my_dialog.cdlg_4,
                self.my_dialog.cdlg_po_pro_1,
                self.my_dialog.cdlg_po_pro_2,
                self.my_dialog.cdlg_po_pro_3,
                self.my_dialog.cdlg_po_pro_4,
                self.my_dialog.first_m_delegate,
                self.my_dialog.last_m_delegate
            ]

            for delegate in stationing_delegates:
                delegate.precision = storage_precision

            self.my_dialog.update()

    def dlg_apply_canvas_crs(self):
        """applies the canvas-projection to coordinate-display in dialog
        affects some QLabel-widgets which show the current unit and num decimals of some measurement-widgets
        """
        # Rev. 2024-06-22
        if self.my_dialog:
            unit, zoom_pan_tolerance, display_precision, measure_default_step = tools.MyTools.eval_crs_units(self.iface.mapCanvas().mapSettings().destinationCrs().authid())

            for unit_widget in self.my_dialog.canvas_unit_widgets:
                unit_widget.setText(f"[{unit}]")

            precision_apply_widgets = [
                self.my_dialog.dnspbx_canvas_x,
                self.my_dialog.dnspbx_canvas_y
            ]
            for qdble in precision_apply_widgets:
                with QtCore.QSignalBlocker(qdble):
                    qdble.setDecimals(display_precision)

            self.my_dialog.update()

    def dlg_apply_locale(self):
        """applies the QGis-Locale-Settings (number-format, group-seperator) in dialog-widgets and -delegates """
        # Rev. 2024-06-22
        if self.my_dialog:
            if QtCore.QSettings().value('locale/overrideFlag', type=bool):
                # => lcid in QGis differing from system-settings
                # default: 'en_US' (if overrideFlag is set but no userLocale defined)
                # globalLocale => QGis-Options-Dialog "Locale (numbers, date and currency formats)"
                lcid = QtCore.QSettings().value('locale/globalLocale', 'en_US')
            else:
                # take the system-lcid
                lcid = QtCore.QLocale.system().name()

            show_group_separator = QtCore.QSettings().value('locale/showGroupSeparator', True)

            # caveat: this value is read from QGIS.ini, therefore the returned value can be a non-boolean as f.e. 'false'
            show_group_separator = show_group_separator in [True, 'True', 'true', '1', 1]

            q_locale = QtCore.QLocale(lcid)

            if not show_group_separator:
                q_locale.setNumberOptions(q_locale.numberOptions() | QtCore.QLocale.OmitGroupSeparator)
            else:
                q_locale.setNumberOptions(q_locale.numberOptions() | ~QtCore.QLocale.OmitGroupSeparator)

            # sadly no locale-cascading for the embedded widgets...
            self.my_dialog.setLocale(q_locale)

            # ...thus:
            delegates = [
                self.my_dialog.cdlg_2,
                self.my_dialog.cdlg_3,
                self.my_dialog.cdlg_4,
                # self.cdlg_5,
                self.my_dialog.cdlg_po_pro_2,
                self.my_dialog.cdlg_po_pro_3,
                self.my_dialog.cdlg_po_pro_4,
                self.my_dialog.ref_length_delegate,
                self.my_dialog.first_m_delegate,
                self.my_dialog.last_m_delegate
            ]
            for delegate in delegates:
                delegate.set_q_locale(q_locale)

            locale_apply_widgets = [
                self.my_dialog.dnspbx_canvas_x,
                self.my_dialog.dnspbx_canvas_y,
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
            for widget in locale_apply_widgets:
                widget.set_q_locale(q_locale)

            self.my_dialog.update()

    def tool_check_selected_ids(self):
        """checks and recreates self.session_data.selected_fids"""
        # Rev. 2024-07-28
        checked_fids = []

        if self.SVS.DATA_LAYER_EXISTS in self.system_vs:
            # remove non-integers as f. e. 'automatically created' for uncommitted features
            selected_fids = [_id for _id in self.session_data.selected_fids if isinstance(_id, int)]
            # make unique
            selected_fids = list(dict.fromkeys(selected_fids))
            # check existance in data-layer
            for data_fid in selected_fids:
                data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
                if data_feature:
                    checked_fids.append(data_fid)

            # sort ascending
            checked_fids.sort()

        self.session_data.selected_fids = checked_fids

    def tool_check_po_pro_data_cache(self):
        """checks self.session_data.po_pro_data_cache:
        data_feature existing?
        reference-feature existing?
        cached reference-feature existing?
        same reference-feature for current and cached?
        pol_from and pol_to existing and valid?
        Failures are removed from cache with log_message
        """
        # Rev. 2024-06-22

        # avoid "RuntimeError: dictionary changed size during iteration"
        checked_po_pro_data_cache = {}

        # 'dict_keys' object has no attribute 'sort'
        po_pro_fids = list(self.session_data.po_pro_data_cache.keys())

        # sort ascending
        po_pro_fids.sort()

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            for data_fid in po_pro_fids:
                po_pro_cached_feature = self.session_data.po_pro_data_cache[data_fid]
                # check existance in data-layer
                data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
                if data_feature:
                    # check reference-feature
                    ref_id = data_feature[self.derived_settings.dataLyrReferenceField.name()]
                    ref_feature, error_msg = self.tool_get_reference_feature(data_fid=data_fid)
                    if ref_feature:
                        if po_pro_cached_feature.ref_fid in self.session_data.po_pro_reference_cache:
                            # check cached reference feature
                            if ref_feature.id() == po_pro_cached_feature.ref_fid:
                                if po_pro_cached_feature.pol_from and po_pro_cached_feature.pol_from.is_valid:
                                    if po_pro_cached_feature.pol_to and po_pro_cached_feature.pol_to.is_valid:
                                        checked_po_pro_data_cache[data_fid] = self.session_data.po_pro_data_cache[data_fid]
                                    else:
                                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_to_recalculation_failed'))
                                else:
                                    self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_from_recalculation_failed'))
                            else:
                                self.dlg_append_log_message('WARNING', MY_DICT.tr('po_pro_referenced_features_not_equal', po_pro_cached_feature.ref_fid))
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('po_pro_cached_reference_feature_missing_or_invalid', po_pro_cached_feature.ref_fid))
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)
                else:
                    self.dlg_append_log_message('WARNING', error_msg)

        self.session_data.po_pro_data_cache = checked_po_pro_data_cache

    def tool_get_reference_geom(self, reference_geom: qgis.core.QgsGeometry = None, ref_feature: qgis.core.QgsFeature = None, ref_fid: int = None, ref_id: int | str = None, data_fid: int = None) -> tuple:
        """get geometry by multiple ways
        :param reference_geom: geometry itself as parameter (makes this function universal)
        :param ref_feature: get geometry from Feature
        :param ref_fid: query geometry with QGis-fid
        :param ref_id: query geometry with registered self.derived_settings.refLyrIdField
        :param data_fid: query geometry with fid of data-feature
        :returns: tuple(qgis.core.QgsGeometry,error_msg)
        """
        # Rev. 2024-06-22
        error_msg = None
        if reference_geom and isinstance(reference_geom, qgis.core.QgsGeometry):
            pass
        else:
            ref_feature, error_msg = self.tool_get_reference_feature(ref_feature, ref_fid, ref_id, data_fid)
            if ref_feature:
                if ref_feature.hasGeometry():
                    reference_geom = ref_feature.geometry()
                else:
                    error_msg = MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id())

        return reference_geom, error_msg

    def s_move_to_start(self):
        """moves current measured segment to stationing_from == 0 => start of reference-line"""
        # Rev. 2024-06-22
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                # the button should be disabled otherwise
                old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                old_to = self.session_data.measure_feature.pol_to.snap_n_abs
                old_len = old_to - old_from

                new_from = 0
                new_to = old_len

                pol_from = self.session_data.measure_feature.pol_from.__copy__()
                pol_from.recalc_by_stationing(new_from, 'Nabs')
                if pol_from.is_valid:
                    pol_to = self.session_data.measure_feature.pol_to.__copy__()
                    pol_to.recalc_by_stationing(new_to, 'Nabs')
                    if pol_to.is_valid:
                        self.session_data.measure_feature.set_pol_from(pol_from)
                        self.session_data.measure_feature.set_pol_to(pol_to)
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])
                self.dlg_refresh_measurements(self.session_data.measure_feature)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

    def s_move_down(self):
        """moves point in direction start of reference-line, stationings getting smaller"""
        # Rev. 2024-06-22
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
                if reference_geom:
                    # step-width dependend on refLyr-crs and keyboard-modifiers
                    unit, zoom_pan_tolerance, display_precision, measure_default_step = tools.MyTools.eval_crs_units(self.derived_settings.refLyr.crs().authid())
                    delta = measure_default_step
                    if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                        delta *= 10
                    elif QtCore.Qt.ShiftModifier == QtWidgets.QApplication.keyboardModifiers():
                        delta *= 100
                    elif QtWidgets.QApplication.keyboardModifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
                        delta *= 1000

                    old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                    old_to = self.session_data.measure_feature.pol_to.snap_n_abs

                    old_len = abs(old_to - old_from)

                    new_from = old_from - delta
                    new_to = old_to - delta

                    if new_from < 0 or new_to < 0:
                        new_from = 0
                        new_to = old_len

                    pol_from = self.session_data.measure_feature.pol_from.__copy__()
                    pol_from.recalc_by_stationing(new_from, 'Nabs')
                    if pol_from.is_valid:
                        pol_to = self.session_data.measure_feature.pol_to.__copy__()
                        pol_to.recalc_by_stationing(new_to, 'Nabs')
                        if pol_to.is_valid:
                            self.session_data.measure_feature.set_pol_from(pol_from)
                            self.session_data.measure_feature.set_pol_to(pol_to)
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                    self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

    def s_move_up(self):
        """moves point in direction end of reference-line, stationings getting larger"""
        # Rev. 2024-06-22
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
                if reference_geom:
                    ref_len = reference_geom.length()
                    unit, zoom_pan_tolerance, display_precision, measure_default_step = tools.MyTools.eval_crs_units(self.derived_settings.refLyr.crs().authid())
                    # step-width dependend on refLyr-crs and keyboard-modifiers
                    delta = measure_default_step
                    if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                        delta *= 10
                    elif QtCore.Qt.ShiftModifier == QtWidgets.QApplication.keyboardModifiers():
                        delta *= 100
                    elif QtWidgets.QApplication.keyboardModifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
                        delta *= 1000

                    old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                    old_to = self.session_data.measure_feature.pol_to.snap_n_abs
                    old_len = abs(old_to - old_from)

                    new_from = old_from + delta
                    new_to = old_to + delta

                    if new_to > ref_len or new_from > ref_len:
                        new_to = ref_len
                        new_from = ref_len - old_len

                    pol_from = self.session_data.measure_feature.pol_from.__copy__()
                    pol_from.recalc_by_stationing(new_from, 'Nabs')
                    if pol_from.is_valid:
                        pol_to = self.session_data.measure_feature.pol_to.__copy__()
                        pol_to.recalc_by_stationing(new_to, 'Nabs')
                        if pol_to.is_valid:
                            self.session_data.measure_feature.set_pol_from(pol_from)
                            self.session_data.measure_feature.set_pol_to(pol_to)
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                    self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])
                    self.dlg_refresh_measurements(self.session_data.measure_feature)
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

    def s_flip_down(self):
        """flips the segment in start-direction (down: stationings get smaller):
        old from-stationing becomes new to-stationing,
        new from-stationing becomes old from-stationing - segment-length"""
        # Rev. 2024-06-22
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
            old_from = self.session_data.measure_feature.pol_from.snap_n_abs
            old_to = self.session_data.measure_feature.pol_to.snap_n_abs

            old_len = abs(old_to - old_from)

            new_from = old_from - old_len
            new_to = old_to - old_len

            if new_from < 0:
                new_from = 0
                new_to = old_len

            if new_to < 0:
                new_to = 0
                new_from = old_len

            pol_from = self.session_data.measure_feature.pol_from.__copy__()
            pol_from.recalc_by_stationing(new_from, 'Nabs')
            if pol_from.is_valid:
                pol_to = self.session_data.measure_feature.pol_to.__copy__()
                pol_to.recalc_by_stationing(new_to, 'Nabs')
                if pol_to.is_valid:
                    self.session_data.measure_feature.set_pol_from(pol_from)
                    self.session_data.measure_feature.set_pol_to(pol_to)
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

            self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])
            self.dlg_refresh_measurements(self.session_data.measure_feature)
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

    def s_flip_up(self):
        """flips the segment in end-direction (up: stationings get bigger):
        old to-stationing becomes new from-stationing,
        new to-stationing becomes old to-stationing + segment-length"""
        # Rev. 2024-06-22
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
            if reference_geom:
                ref_len = reference_geom.length()
                old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                old_to = self.session_data.measure_feature.pol_to.snap_n_abs
                old_len = abs(old_to - old_from)

                new_from = old_from + old_len
                new_to = old_to + old_len

                if new_to > ref_len:
                    new_to = ref_len
                    new_from = max(ref_len - old_len, 0)

                if new_from > ref_len:
                    new_to = ref_len
                    new_from = max(ref_len - old_len, 0)

                pol_from = self.session_data.measure_feature.pol_from.__copy__()
                pol_from.recalc_by_stationing(new_from, 'Nabs')

                if pol_from.is_valid:
                    pol_to = self.session_data.measure_feature.pol_to.__copy__()
                    pol_to.recalc_by_stationing(new_to, 'Nabs')

                    if pol_to.is_valid:
                        self.session_data.measure_feature.set_pol_from(pol_from)
                        self.session_data.measure_feature.set_pol_to(pol_to)
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])
                self.dlg_refresh_measurements(self.session_data.measure_feature)
            else:
                self.dlg_append_log_message('WARNING', error_msg)
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

    def s_move_to_end(self):
        """moves point to end of reference-line, max stationings"""
        # Rev. 2024-06-22
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
            if reference_geom:
                ref_len = reference_geom.length()
                old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                old_to = self.session_data.measure_feature.pol_to.snap_n_abs
                old_len = abs(old_to - old_from)

                new_from = ref_len - old_len
                new_to = ref_len

                pol_from = self.session_data.measure_feature.pol_from.__copy__()
                pol_from.recalc_by_stationing(new_from, 'Nabs')
                if pol_from.is_valid:
                    pol_to = self.session_data.measure_feature.pol_to.__copy__()
                    pol_to.recalc_by_stationing(new_to, 'Nabs')

                    if pol_to.is_valid:
                        self.session_data.measure_feature.set_pol_from(pol_from)
                        self.session_data.measure_feature.set_pol_to(pol_to)
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])
                self.dlg_refresh_measurements(self.session_data.measure_feature)
            else:
                self.dlg_append_log_message('WARNING', error_msg)
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

    def scc_ref_line_style(self):
        """change style of reference-line"""
        # Rev. 2024-06-22
        # {0: "None", 1: "Solid", 2: "Dash", 3: "Dot", 4: "DashDot", 5: "DashDotDot"}
        self.stored_settings.ref_line_style = self.my_dialog.qcb_ref_line_style.currentData()
        self.cvs_apply_style_to_graphics()

    def scc_ref_line_width(self, line_width: int):
        """change width of reference-line
        :param line_width: width in pixel
        """
        # Rev. 2024-06-22
        self.stored_settings.ref_line_width = line_width
        self.cvs_apply_style_to_graphics()

    def scc_ref_line_color(self, color: str):
        """change color of reference-line
        :param color: color in HexArgb-Format
        """
        # Rev. 2024-06-22
        self.stored_settings.ref_line_color = color
        self.cvs_apply_style_to_graphics()

    def scc_segment_line_style(self):
        """change style of LoL-segment-geometry"""
        # Rev. 2024-06-22
        # {0: "None", 1: "Solid", 2: "Dash", 3: "Dot", 4: "DashDot", 5: "DashDotDot"}
        self.stored_settings.segment_line_style = self.my_dialog.qcb_segment_line_style.currentData()
        self.cvs_apply_style_to_graphics()

    def scc_segment_line_width(self, line_width: int):
        """change width of LoL-segment-geometry
        :param line_width: width in pixel
        """
        # Rev. 2024-06-22
        self.stored_settings.segment_line_width = line_width
        self.cvs_apply_style_to_graphics()

    def scc_segment_line_color(self, color: str):
        """change color of the LoL-segment-geometry
        :param color: color in HexArgb-Format
        """
        # Rev. 2024-06-22
        self.stored_settings.segment_line_color = color
        self.cvs_apply_style_to_graphics()

    def scc_pt_snf_icon_type(self):
        """change Point-From-Icon-Type"""
        # Rev. 2024-06-22
        # {0: "None", 1: "Cross", 2: "X", 3: "Box", 4: "Circle", 5: "Double-Triangle", 6: "Triangle", 7: "Rhombus", 8: "Inverted Triangle"}
        self.stored_settings.pt_snf_icon_type = self.my_dialog.qcb_pt_snf_icon_type.currentData()
        self.cvs_apply_style_to_graphics()

    def scc_pt_snf_icon_size(self, icon_size: int):
        """change Point-From-Icon-Size
        :param icon_size: size in pixel
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snf_icon_size = icon_size
        self.cvs_apply_style_to_graphics()

    def scc_pt_snf_pen_width(self, pen_width: int):
        """change From-Point-Pen-Width
        :param pen_width: width in pixel
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snf_pen_width = pen_width
        self.cvs_apply_style_to_graphics()

    def scc_pt_snf_color(self, color: str):
        """change Point-From-Icon-Color
        :param color: color in HexArgb-Format
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snf_color = color
        self.cvs_apply_style_to_graphics()

    def scc_pt_snf_fill_color(self, color: str):
        """change Point-From-Icon-Fill-Color
        dependend on pt_snf_icon_type not allways visible
        :param color: color in HexArgb-Format
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snf_fill_color = color
        self.cvs_apply_style_to_graphics()

    def scc_pt_snt_icon_type(self):
        """change Point-To-Icon-Type"""
        # Rev. 2024-06-22
        # {0: "None", 1: "Cross", 2: "X", 3: "Box", 4: "Circle", 5: "Double-Triangle", 6: "Triangle", 7: "Rhombus", 8: "Inverted Triangle"}
        self.stored_settings.pt_snt_icon_type = self.my_dialog.qcb_pt_snt_icon_type.currentData()
        self.cvs_apply_style_to_graphics()

    def scc_pt_snt_icon_size(self, icon_size: int):
        """change Point-To-Icon-Size
        :param icon_size: size in pixel
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snt_icon_size = icon_size
        self.cvs_apply_style_to_graphics()

    def scc_pt_snt_pen_width(self, pen_width: int):
        """change Point-To-Pen-Width
        :param pen_width: width in pixel
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snt_pen_width = pen_width
        self.cvs_apply_style_to_graphics()

    def scc_pt_snt_color(self, color: str):
        """change Point-To-Color
        :param color: color in HexArgb-Format
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snt_color = color
        self.cvs_apply_style_to_graphics()

    def scc_pt_snt_fill_color(self, color: str):
        """change  Point-To-Fill-Color
        dependend on pt_snt_icon_type not allways visible
        :param color: color in HexArgb-Format
        """
        # Rev. 2024-06-22
        self.stored_settings.pt_snt_fill_color = color
        self.cvs_apply_style_to_graphics()

    def cvs_apply_style_to_graphics(self):
        """applies symbolization-styles to canvas-grafics
        some styles customizable via self.stored_settings, some hard coded"""
        # Rev. 2024-06-22
        # current segments, solid light blue
        self.rb_rfl_diff_cu.setWidth(5)
        self.rb_rfl_diff_cu.setLineStyle(1)
        self.rb_rfl_diff_cu.setColor(QtGui.QColor('#FF6495ED')) # CornflowerBlue
        self.rb_rfl_diff_cu.setOpacity(0.6)

        # cached segments, solid dark blue
        self.rb_rfl_diff_ca.setWidth(5)
        self.rb_rfl_diff_ca.setLineStyle(1)
        self.rb_rfl_diff_ca.setColor(QtGui.QColor('#FF483D8B')) #DarkSlateBlue
        self.rb_rfl_diff_ca.setOpacity(0.6)

        self.rb_rfl.setWidth(self.stored_settings.ref_line_width)
        self.rb_rfl.setLineStyle(self.stored_settings.ref_line_style)
        self.rb_rfl.setColor(QtGui.QColor(self.stored_settings.ref_line_color))

        self.rb_sgn.setWidth(self.stored_settings.segment_line_width)
        self.rb_sgn.setLineStyle(self.stored_settings.segment_line_style)
        self.rb_sgn.setColor(QtGui.QColor(self.stored_settings.segment_line_color))

        # solid red line
        self.rb_sg0.setWidth(2)
        self.rb_sg0.setLineStyle(1)
        self.rb_sg0.setColor(QtGui.QColor('#ffff0000'))

        self.vm_snf.setPenWidth(self.stored_settings.pt_snf_pen_width)
        self.vm_snf.setIconSize(self.stored_settings.pt_snf_icon_size)
        self.vm_snf.setIconType(self.stored_settings.pt_snf_icon_type)
        self.vm_snf.setColor(QtGui.QColor(self.stored_settings.pt_snf_color))
        self.vm_snf.setFillColor(QtGui.QColor(self.stored_settings.pt_snf_fill_color))

        self.vm_snt.setPenWidth(self.stored_settings.pt_snt_pen_width)
        self.vm_snt.setIconSize(self.stored_settings.pt_snt_icon_size)
        self.vm_snt.setIconType(self.stored_settings.pt_snt_icon_type)
        self.vm_snt.setColor(QtGui.QColor(self.stored_settings.pt_snt_color))
        self.vm_snt.setFillColor(QtGui.QColor(self.stored_settings.pt_snt_fill_color))

        self.vm_enf.setIconType(4)
        self.vm_enf.setPenWidth(2)
        self.vm_enf.setIconSize(30)
        # same color as vm_snf
        self.vm_enf.setColor(QtGui.QColor(self.stored_settings.pt_snf_color))
        self.vm_enf.setFillColor(QtGui.QColor('#00ffffff'))

        self.vm_ent.setIconType(4)
        self.vm_ent.setPenWidth(2)
        self.vm_ent.setIconSize(30)
        # same color as vm_snt
        self.vm_ent.setColor(QtGui.QColor(self.stored_settings.pt_snt_color))
        self.vm_ent.setFillColor(QtGui.QColor('#00ffffff'))

        # selection-rect, not customizable, red border, half transparent
        self.rb_selection_rect.setWidth(2)
        self.rb_selection_rect.setColor(QtGui.QColor(255, 0, 0, 100))

        # PostProcessing-Symbolization, not customizable
        # cached po-pro-from-point: dark green box, bit larger than default for vm_snf
        self.vm_pt_cnf.setPenWidth(4)
        self.vm_pt_cnf.setIconSize(20)
        self.vm_pt_cnf.setIconType(3)
        self.vm_pt_cnf.setColor(QtGui.QColor('#FF006400')) # DarkGreen
        self.vm_pt_cnf.setOpacity(0.6)

        # cached po-pro-to-point: dark-red box, bit larger than default for vm_snt
        self.vm_pt_cnt.setPenWidth(4)
        self.vm_pt_cnt.setIconSize(20)
        self.vm_pt_cnt.setIconType(3)
        self.vm_pt_cnt.setColor(QtGui.QColor('#FF8B0000')) # DarkRed
        self.vm_pt_cnt.setOpacity(0.6)

        # previous segment on cached reference-line
        self.rb_csgn.setWidth(4)
        self.rb_csgn.setLineStyle(1)
        self.rb_csgn.setColor(QtGui.QColor('#FFD2691E')) # Chocolate

        # cached reference-line, not used
        self.rb_crfl.setWidth(2)
        self.rb_crfl.setLineStyle(1)
        self.rb_crfl.setColor(QtGui.QColor('#50505050'))

        self.iface.mapCanvas().refresh()

    def s_select_current_ref_fid(self):
        """highlights and optionally zooms to the current selected Reference-Feature,
        triggered by currentIndexChanged on qcbn_reference_feature (QComboBoxN)
        see similar dlg_select_qcbn_reference_feature, which also sets self.session_data.current_ref_fid and triggers select in qcbn_reference_feature"""
        # Rev. 2024-06-22
        zoom_to_feature = bool(QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers())
        if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            ref_fid = self.my_dialog.qcbn_reference_feature.currentData(self.ref_fid_role)
            if ref_fid is not None:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=ref_fid)
                if reference_geom:
                    self.session_data.current_ref_fid = ref_fid
                    self.cvs_draw_reference_geom(reference_geom=reference_geom, zoom_to_feature=zoom_to_feature)
                    self.dlg_refresh_measure_section()
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))

    def s_zoom_to_ref_feature(self):
        """highlights and zooms the current selected Reference-Feature,
        triggered by click on pb_zoom_to_ref_feature"""
        # Rev. 2024-06-22
        if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            if self.session_data.current_ref_fid is not None:

                self.cvs_draw_reference_geom(ref_fid=self.session_data.current_ref_fid, zoom_to_feature=True)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))

    def s_dialog_activated(self, activated: bool):
        """re-enables the mapTool with last used tool-mode, if dialog gets focus and other mapTool is active
        convenient if f. e. the mapTool "Pan" was used meanwhile
        triggered by custom signal self.my_dialog.dialog_activated
        not used anymore
        :param activated: True on focus-get, False on focus-blur"""
        # Rev. 2024-06-22
        if activated and self.iface.mapCanvas().mapTool() != self:
            self.iface.mapCanvas().setMapTool(self)
            # check current settings against last used tool_mode
            self.sys_check_settings()

    def s_dialog_close(self):
        """slot for custom signal self.my_dialog.dialog_close, emitted on close of self.my_dialog
        Note: MapTool and (closed == hidden) dialog persist
        """
        # Rev. 2024-06-22
        try:
            self.iface.actionPan().trigger()
            self.cvs_hide_markers()
        except Exception as e:
            pass

    def s_zoom_to_stationings(self):
        """zooms canvas-extent to self.session_data.measure_feature or self.session_data.pol_from ... self.session_data.pol_to"""
        x_coords = []
        y_coords = []
        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers() or QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan'

        if self.session_data.measure_feature is not None:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
            if reference_geom:
                segment_geom, segment_error = tools.MyTools.get_segment_geom_n(reference_geom, self.session_data.measure_feature.pol_from.snap_n_abs, self.session_data.measure_feature.pol_to.snap_n_abs, self.session_data.measure_feature.offset)
                if segment_geom:
                    extent = segment_geom.boundingBox()
                    x_coords.append(extent.xMinimum())
                    x_coords.append(extent.xMaximum())
                    y_coords.append(extent.yMinimum())
                    y_coords.append(extent.yMaximum())

                from_point = reference_geom.interpolate(self.session_data.measure_feature.pol_from.snap_n_abs)
                x_coords.append(from_point.asPoint().x())
                y_coords.append(from_point.asPoint().y())

                to_point = reference_geom.interpolate(self.session_data.measure_feature.pol_to.snap_n_abs)
                x_coords.append(to_point.asPoint().x())
                y_coords.append(to_point.asPoint().y())

            self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode)
        elif self.session_data.pol_from is not None and self.session_data.pol_to is not None and self.session_data.pol_from.is_valid and self.session_data.pol_to.is_valid:
            #  zooms preferably to measure_feature, but also pol_from/pol_to and even on different reference-lines
            # note: if measure_feature exists, pol_from and pol_to will also exist with and same stationings and reference and vice versa
            from_reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.pol_from.ref_fid)
            if from_reference_geom:
                from_point = from_reference_geom.interpolate(self.session_data.pol_from.snap_n_abs)
                x_coords.append(from_point.asPoint().x())
                y_coords.append(from_point.asPoint().y())

            to_reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.pol_to.ref_fid)
            if to_reference_geom:
                to_point = to_reference_geom.interpolate(self.session_data.pol_to.snap_n_abs)
                x_coords.append(to_point.asPoint().x())
                y_coords.append(to_point.asPoint().y())

            self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode)

        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

    def tool_get_data_feature(self, data_feature: qgis.core.QgsFeature = None, data_fid: int = None, data_id: int | str = None) -> tuple:
        """get data-feature
        :param data_feature: check validity and return
        :param data_fid: fid of data-feature
        :param data_id: id of data-feature, queried against self.derived_settings.dataLyrIdField
        :returns: tuple(qgis.core.QgsFeature,error_msg)
        """
        # Rev. 2024-06-22
        error_msg = None
        if data_feature:
            pass
        elif data_fid is not None:
            if self.SVS.DATA_LAYER_EXISTS in self.system_vs:
                data_feature = self.derived_settings.dataLyr.getFeature(data_fid)
                if not (data_feature and data_feature.isValid()):
                    error_msg = MY_DICT.tr('exc_data_feature_not_found_by_data_fid', data_fid)
        elif data_id is not None:
            if (self.SVS.DATA_LAYER_EXISTS | self.SVS.DATA_LAYER_ID_FIELD_DEFINED) in self.system_vs:
                data_feature = tools.MyTools.get_feature_by_value(self.derived_settings.dataLyr, self.derived_settings.dataLyrIdField, data_id)
                if not (data_feature and data_feature.isValid()):
                    error_msg = MY_DICT.tr('exc_data_feature_not_found_by_data_id', data_id)

        if data_feature and isinstance(data_feature, qgis.core.QgsFeature) and data_feature.isValid():
            return data_feature, None
        else:
            return None, error_msg

    def tool_get_show_feature(self, show_feature: qgis.core.QgsFeature = None, show_fid: int = None, data_fid: int = None, data_id: int | str = None) -> tuple:
        """get feature from show-layer
        :param show_feature: check validity and return
        :param show_fid: fid of show-feature
        :param data_fid: fid of data-feature
        :param data_id: id of data-feature, queried against self.derived_settings.dataLyrIdField
        :returns: tuple(qgis.core.QgsFeature, error_msg)
        """
        # Rev. 2024-06-22
        error_msg = None
        if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
            if show_feature:
                pass
            elif show_fid is not None:
                show_feature = self.derived_settings.showLyr.getFeature(show_fid)
                if not (show_feature and show_feature.isValid()):
                    error_msg = MY_DICT.tr('exc_show_feature_not_found_by_show_fid', show_fid)

            elif data_fid is not None:
                if data_fid > 0:
                    data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
                    if data_feature and data_feature.isValid():
                        data_id = data_feature[self.stored_settings.dataLyrIdFieldName]
                        show_feature = tools.MyTools.get_feature_by_value(self.derived_settings.showLyr, self.derived_settings.showLyrBackReferenceField, data_id)
                        if not (show_feature and show_feature.isValid()):
                            error_msg = MY_DICT.tr('exc_show_feature_not_found_by_data_fid', data_fid)
                else:
                    error_msg = MY_DICT.tr('exc_no_show_feature_with_negative_data_fid', data_fid)

            elif data_id is not None:
                data_feature, error_msg = self.tool_get_data_feature(data_id=data_id)
                if data_feature and data_feature.isValid():
                    data_id = data_feature[self.stored_settings.dataLyrIdFieldName]
                    show_feature = tools.MyTools.get_feature_by_value(self.derived_settings.showLyr, self.derived_settings.showLyrBackReferenceField, data_id)
                    if not (show_feature and show_feature.isValid()):
                        error_msg = MY_DICT.tr('exc_show_feature_not_found_by_data_id', data_id)

        if show_feature and isinstance(show_feature, qgis.core.QgsFeature) and show_feature.isValid():
            return show_feature, None
        else:
            return None, error_msg

    def tool_get_reference_feature(self, ref_feature: qgis.core.QgsFeature = None, ref_fid: int = None, ref_id: int | str = None, data_fid: int = None) -> tuple:
        """get reference-feature by multiple ways
        :param ref_feature: check validity and return
        :param ref_fid: get feature by QGis-fid
        :param ref_id: get feature by registered self.derived_settings.refLyrIdField
        :param data_fid: get feature by fid of data-feature
        :returns: tuple(qgis.core.QgsFeature,error_msg)
        """
        # Rev. 2024-06-22
        error_msg = None
        if ref_feature is not None:
            pass
        elif ref_fid is not None:
            if self.SVS.REFERENCE_LAYER_EXISTS in self.system_vs:
                ref_feature = self.derived_settings.refLyr.getFeature(ref_fid)
                if not (ref_feature and ref_feature.isValid()):
                    error_msg = MY_DICT.tr('exc_reference_feature_not_found_by_ref_fid', ref_fid)

        if ref_id is not None:
            if self.SVS.REFERENCE_LAYER_COMPLETE in self.system_vs:
                ref_feature = tools.MyTools.get_feature_by_value(self.derived_settings.refLyr, self.derived_settings.refLyrIdField, ref_id)
                if not (ref_feature and ref_feature.isValid()):
                    error_msg = MY_DICT.tr('exc_reference_feature_not_found_by_ref_id', ref_id)

        elif data_fid is not None:
            if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
                data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
                if data_feature:
                    ref_id = data_feature[self.derived_settings.dataLyrReferenceField.name()]
                    # recursive call with queried ref_id
                    ref_feature, error_msg = self.tool_get_reference_feature(ref_id=ref_id)

        if ref_feature and isinstance(ref_feature, qgis.core.QgsFeature) and ref_feature.isValid():
            return ref_feature, None
        else:
            return None, error_msg

    def tool_check_data_feature(self, data_feature: qgis.core.QgsFeature = None, data_fid=None, data_id=None) -> FVS:
        """checks data_feature via FVS
        callable with various references to data-feature
        :param data_feature: the data-feature itself
        :param data_fid: optionally for querying data_feature by feature-id, usable for temporary features in edit-buffer (fid negative)
        :param data_id: optionally for querying data_feature from self.derived_settings.dataLyr
        :returns: FVS
        """
        # Rev. 2024-06-22
        fvs = FVS.INIT

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            data_feature, error_msg = self.tool_get_data_feature(data_feature, data_fid, data_id)

            if data_feature:
                fvs |= FVS.DATA_FEATURE_EXISTS

                offset = data_feature[self.derived_settings.dataLyrOffsetField.name()]
                stationing_from = data_feature[self.derived_settings.dataLyrStationingFromField.name()]
                stationing_to = data_feature[self.derived_settings.dataLyrStationingToField.name()]

                if isinstance(offset, numbers.Number):
                    fvs |= FVS.OFFSET_NUMERIC

                if isinstance(stationing_from, numbers.Number):
                    fvs |= FVS.STATIONING_FROM_NUMERIC

                if isinstance(stationing_to, numbers.Number):
                    fvs |= FVS.STATIONING_TO_NUMERIC

                if isinstance(stationing_from, numbers.Number) and isinstance(stationing_to, numbers.Number) and stationing_from <= stationing_to:
                    fvs |= FVS.STATIONING_FROM_LTEQ_TO

                ref_id = data_feature[self.derived_settings.dataLyrReferenceField.name()]

                if not (ref_id is None or ref_id == '' or repr(ref_id) == 'NULL'):
                    fvs |= FVS.REFERENCE_ID_VALID
                    reference_geom, error_msg = self.tool_get_reference_geom(ref_id=ref_id)
                    if reference_geom:
                        fvs |= FVS.REFERENCE_FEATURE_EXISTS
                        fvs |= FVS.REFERENCE_GEOMETRY_EXIST
                        ref_len = reference_geom.length()

                        if self.stored_settings.lrMode in ['Nabs', 'Nfract']:
                            geom_n_valid, error_msg = tools.MyTools.check_geom_n_valid(reference_geom)
                            if geom_n_valid:
                                fvs |= FVS.REFERENCE_GEOMETRY_VALID
                        elif self.stored_settings.lrMode in ['Mabs']:
                            geom_m_valid, error_msg = tools.MyTools.check_geom_m_valid(reference_geom)
                            if geom_m_valid:
                                fvs |= FVS.REFERENCE_GEOMETRY_VALID

                        if (FVS.REFERENCE_GEOMETRY_VALID | FVS.STATIONING_FROM_NUMERIC) in fvs:
                            if self.stored_settings.lrMode == 'Nabs':
                                if 0 <= stationing_from <= ref_len:
                                    fvs |= FVS.STATIONING_FROM_INSIDE_RANGE
                            elif self.stored_settings.lrMode == 'Nfract':
                                if 0 <= stationing_from <= 1:
                                    fvs |= FVS.STATIONING_FROM_INSIDE_RANGE
                            elif self.stored_settings.lrMode == 'Mabs':
                                first_vertex_m, last_vertex_m, error_msg = tools.MyTools.get_first_last_vertex_m(reference_geom)
                                if not error_msg:
                                    if first_vertex_m <= stationing_from <= last_vertex_m:
                                        fvs |= FVS.STATIONING_FROM_INSIDE_RANGE

                        if (FVS.REFERENCE_GEOMETRY_VALID | FVS.STATIONING_TO_NUMERIC) in fvs:
                            if self.stored_settings.lrMode == 'Nabs':
                                if 0 <= stationing_to <= ref_len:
                                    fvs |= FVS.STATIONING_TO_INSIDE_RANGE
                            elif self.stored_settings.lrMode == 'Nfract':
                                if 0 <= stationing_to <= 1:
                                    fvs |= FVS.STATIONING_TO_INSIDE_RANGE
                            elif self.stored_settings.lrMode == 'Mabs':
                                first_vertex_m, last_vertex_m, error_msg = tools.MyTools.get_first_last_vertex_m(reference_geom)
                                if not error_msg:
                                    if first_vertex_m <= stationing_to <= last_vertex_m:
                                        fvs |= FVS.STATIONING_TO_INSIDE_RANGE
                    else:
                        #self.dlg_append_log_message('WARNING', error_msg)
                        pass
        return fvs

    def tool_create_lol_feature(self, data_fid: int) -> LoLFeature:
        """initializes LoLFeature by data_fid with values from data_feature
        :param data_fid:
        """
        # Rev. 2024-06-24
        lol_feature = LoLFeature()

        if self.derived_settings.refLyr:
            lol_feature.ref_lyr_id = self.derived_settings.refLyr.id()
            lol_feature.reference_authid = self.derived_settings.refLyr.crs().authid()

            if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
                fvs = self.tool_check_data_feature(data_fid=data_fid)

                fvs.check_data_feature_valid()
                if not fvs.is_valid:
                    # only hints, invalid features can be selected, f.e. for edit
                    # self.dlg_append_log_message('WARNING', MY_DICT.tr(fvs.first_fail_flag))
                    # no more logs, because often called with uncommitted and uncomplete features, f.e. if an empty row was inserted in feature-table
                    pass

                data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
                if data_feature:
                    lol_feature.data_fid = data_fid

                    stationing_from = data_feature[self.derived_settings.dataLyrStationingFromField.name()]
                    stationing_to = data_feature[self.derived_settings.dataLyrStationingToField.name()]
                    lol_feature.offset = data_feature[self.derived_settings.dataLyrOffsetField.name()]
                    ref_id = data_feature[self.derived_settings.dataLyrReferenceField.name()]

                    if ref_id:
                        # ref_id can be NoneType for new inserted and yet incomplete features
                        ref_feature, error_msg = self.tool_get_reference_feature(ref_id=ref_id)

                        if ref_feature:
                            lol_feature.ref_fid = ref_feature.id()

                            if FVS.STATIONING_FROM_INSIDE_RANGE in fvs:
                                pol_from = PoLFeature()
                                pol_from.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                                pol_from.recalc_by_stationing(stationing_from, self.stored_settings.lrMode)
                                if pol_from.is_valid:
                                    lol_feature.set_pol_from(pol_from)
                                else:
                                    self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                            if FVS.STATIONING_TO_INSIDE_RANGE in fvs:
                                pol_to = PoLFeature()
                                pol_to.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                                pol_to.recalc_by_stationing(stationing_to, self.stored_settings.lrMode)
                                if pol_to.is_valid:
                                    lol_feature.set_pol_to(pol_to)
                                else:
                                    self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                        else:
                            self.dlg_append_log_message('WARNING', error_msg)

                    # create lol_feature without valid reference-feature
                    lol_feature.check_is_valid()
                    return lol_feature
                else:
                    if error_msg:
                        self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_or_data_layer_missing'))

    def tool_select_feature(self, data_fid: int, draw_markers: str = None, extent_markers: str = None, extent_mode: str = None):
        """sets self.session_data.edit_feature, the current selected Line-on-Line-Feature, for display and/or editing
        refreshes (if necessary add missing row, else select and refresh) self.my_dialog.qtrv_feature_selection
        :param data_fid: FID of Data-Layer, 1:1-relation
        :param draw_markers: combination of marker-types
        :param extent_markers: combination of marker-types, optional zoom to specific markers
        :param extent_mode: zoom/pan
        """
        # Rev. 2024-06-24

        self.session_data.edit_feature = None

        self.dlg_clear_measurements()
        self.cvs_hide_markers()

        edit_feature = self.tool_create_lol_feature(data_fid)

        if edit_feature:
            self.session_data.edit_feature = edit_feature

            if data_fid not in self.session_data.selected_fids:
                self.session_data.selected_fids.append(data_fid)
                self.dlg_refresh_feature_selection_section()
            else:
                self.dlg_select_feature_selection_row(data_fid)

            self.cvs_draw_feature(edit_feature, draw_markers, extent_markers, extent_mode)

            # additionally use clone for measure_feature in measure-area
            self.session_data.measure_feature = edit_feature.__copy__()
            self.dlg_refresh_measurements(self.session_data.measure_feature)
            self.dlg_select_qcbn_reference_feature(self.session_data.measure_feature.ref_fid)
            self.session_data.current_offset = self.session_data.measure_feature.offset

            if isinstance(edit_feature.offset, numbers.Number):
                with (QtCore.QSignalBlocker(self.my_dialog.dspbx_offset)):
                    self.my_dialog.dspbx_offset.setValue(edit_feature.offset)

            self.dlg_refresh_measure_section()

    def dlg_select_feature_selection_row(self, data_fid: int):
        """visually select row in qtrv_feature_selection
        font-weight and border realized via selectionModel and QStyledItemDelegate
        highlight-color and text via QtGui.QPalette.Highlight rsp. QtGui.QPalette.HighlightedText
        :param data_fid:
        """
        # Rev. 2024-06-24
        with (QtCore.QSignalBlocker(self.my_dialog.qtrv_feature_selection)):
            with QtCore.QSignalBlocker(self.my_dialog.qtrv_feature_selection.selectionModel()):
                model = self.my_dialog.qtrv_feature_selection.model()
                selection_model = self.my_dialog.qtrv_feature_selection.selectionModel()
                selection_model.clearSelection()
                # find the matching row, returns only 1 match, MatchRecursive for TreeView
                matches = model.match(model.index(0, 0), self.data_fid_role, data_fid, 1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                for index in matches:
                    # select whole row
                    selection_model.select(index, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
                    # and (re-)open the parent branch
                    self.my_dialog.qtrv_feature_selection.setExpanded(index.parent(), True)

        self.my_dialog.qtrv_feature_selection.update()

    def dlg_select_po_pro_selection_row(self, data_fid):
        """visually select row in qtrv_po_pro_selection
        font-weight and border realized via selectionModel and QStyledItemDelegate
        highlight-color and text via QtGui.QPalette.Highlight rsp. QtGui.QPalette.HighlightedText
        :param data_fid:
        """
        # Rev. 2024-06-24
        with (QtCore.QSignalBlocker(self.my_dialog.qtrv_po_pro_selection)):
            with QtCore.QSignalBlocker(self.my_dialog.qtrv_po_pro_selection.selectionModel()):
                model = self.my_dialog.qtrv_po_pro_selection.model()
                selection_model = self.my_dialog.qtrv_po_pro_selection.selectionModel()
                selection_model.clearSelection()
                # find the matching row, returns only 1 match
                matches = model.match(model.index(0, 0), self.data_fid_role, data_fid, 1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                for index in matches:
                    # select whole row
                    selection_model.select(index, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
                    # and (re-)open the parent branch
                    self.my_dialog.qtrv_po_pro_selection.setExpanded(index.parent(), True)

        self.my_dialog.qtrv_po_pro_selection.update()

    def s_clear_feature_selection(self):
        """clear self.session_data.selected_fids and self.session_data.edit_feature
        refresh Feature-Selection"""
        # Rev. 2024-06-25
        self.session_data.selected_fids = []
        self.session_data.edit_feature = None
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_measure_section()

    def s_append_data_features(self):
        """Adds features from dataLyr to self.session_data.selected_fids"""
        # Rev. 2024-06-25
        selection_mode = 'select_all'
        if QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers():
            selection_mode = 'append_selected'
        elif QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers():
            selection_mode = 'select_selected'

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            if selection_mode == 'select_selected' or selection_mode == 'append_selected':
                additional_feature_ids = self.derived_settings.dataLyr.selectedFeatureIds()
                if len(additional_feature_ids):
                    if selection_mode == 'select_selected':
                        self.session_data.selected_fids = additional_feature_ids
                    else:
                        self.session_data.selected_fids += additional_feature_ids
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('no_selection_in_data_layer'))
            else:
                # selection_mode = 'select_all'
                additional_feature_ids = [f.id() for f in self.derived_settings.dataLyr.getFeatures()]
                if len(additional_feature_ids):
                    self.session_data.selected_fids = additional_feature_ids
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('no_features_in_data_layer'))

            self.dlg_refresh_feature_selection_section()

    def s_clear_post_processing(self):
        """stops PostProcessing by clearing self.session_data.po_pro_reference_cache/po_pro_data_cache
        and refreshes dialog-section
        """
        # Rev. 2024-09-04
        self.cvs_hide_markers()
        if self.session_data.po_pro_data_cache:
            dialog_result = QtWidgets.QMessageBox.question(
                None,
                f"LinearReferencing ({get_debug_pos()})",
                MY_DICT.tr('clear_post_processing_dlg_txt'),
                buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                defaultButton=QtWidgets.QMessageBox.Yes
            )

            if dialog_result == QtWidgets.QMessageBox.Yes:
                self.session_data.po_pro_reference_cache = {}
                self.session_data.po_pro_data_cache = {}
                self.dlg_refresh_po_pro_section()
                

    def s_zoom_to_po_pro_selection(self):
        """Zooms canvas to post-processing-selection
        iterates through po_pro_selection
        checks validity,
        calculates segment-geometries with cached and current stationings rsp. reference-geometries,
        zooms to their combined extents
        """
        # Rev. 2024-06-25
        x_coords = []
        y_coords = []

        skipped_fids = []
        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            for fid in self.session_data.po_pro_data_cache:
                data_feature, error_msg = self.tool_get_data_feature(data_fid=fid)
                if data_feature:
                    measure_feature = self.tool_create_lol_feature(data_feature.id())

                    cached_feature = self.session_data.po_pro_data_cache[fid]

                    ref_id = data_feature[self.derived_settings.dataLyrReferenceField.name()]

                    offset = data_feature[self.derived_settings.dataLyrOffsetField.name()]

                    ref_feature, error_msg = self.tool_get_reference_feature(ref_id=ref_id)
                    if ref_feature:
                        current_geom = ref_feature.geometry()
                        ref_fid = ref_feature.id()
                        if ref_fid in self.session_data.po_pro_reference_cache:
                            cached_geom = self.session_data.po_pro_reference_cache[ref_fid]

                            cached_pol_from = cached_feature.pol_from
                            cached_pol_to = cached_feature.pol_to

                            if measure_feature.pol_from.is_valid and measure_feature.pol_to.is_valid:
                                try:
                                    current_segment_geom, segment_error = tools.MyTools.get_segment_geom_n(current_geom, measure_feature.pol_from.snap_n_abs, measure_feature.pol_to.snap_n_abs, offset)
                                    if current_segment_geom:
                                        extent = current_segment_geom.boundingBox()
                                        x_coords.append(extent.xMinimum())
                                        x_coords.append(extent.xMaximum())
                                        y_coords.append(extent.yMinimum())
                                        y_coords.append(extent.yMaximum())

                                except Exception as err:
                                    self.dlg_append_log_message('INFO', str(err))

                            if cached_pol_from.is_valid and cached_pol_to.is_valid:
                                try:
                                    cached_segment_geom, segment_error = tools.MyTools.get_segment_geom_n(cached_geom, cached_pol_from.snap_n_abs, cached_pol_to.snap_n_abs, cached_feature.offset)
                                    if cached_segment_geom:
                                        extent = cached_segment_geom.boundingBox()
                                        x_coords.append(extent.xMinimum())
                                        x_coords.append(extent.xMaximum())
                                        y_coords.append(extent.yMinimum())
                                        y_coords.append(extent.yMaximum())

                                except Exception as err:
                                    self.dlg_append_log_message('INFO', str(err))

                        else:
                            skipped_fids.append(fid)
                            # self.dlg_append_log_message('WARNING', MY_DICT.tr('po_pro_cached_reference_feature_missing_or_invalid', ref_fid))
                    else:
                        skipped_fids.append(fid)
                        # self.dlg_append_log_message('WARNING', MY_DICT.tr('po_pro_reference_feature_missing_or_invalid', ref_id))
                else:
                    skipped_fids.append(fid)
                    # self.dlg_append_log_message('WARNING', MY_DICT.tr('po_pro_data_feature_missing_or_invalid', fid))

            # queried extents in layer-projection
            self.cvs_zoom_to_coords(x_coords, y_coords, 'zoom', self.derived_settings.refLyr.crs())

            if len(skipped_fids) > 0:
                self.dlg_append_log_message('INFO', MY_DICT.tr('data_cache_features_dlg_skipped', len(skipped_fids)))

    def s_feature_selection_to_data_layer_filter(self):
        """creates a filter-query on data-layer (provider-side) for the current selected features
        show-layers using data-layer are filtered too
        ctrl-click removes filter"""
        # Rev. 2024-06-25

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            if not self.derived_settings.dataLyr.isEditable():
                if QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers():
                    if self.derived_settings.dataLyr.subsetString() == '':
                        self.dlg_append_log_message('INFO', MY_DICT.tr('no_filter'))
                    else:
                        # clear filter
                        self.derived_settings.dataLyr.setSubsetString('')
                        # rest is done by sys_layer_slot
                else:
                    if self.session_data.selected_fids:

                        # Note:
                        # the subset is q query-expression on the provider-side, so it must use the provider-side-ID-field, not the QGis internal feature._id()
                        # allthough mostly identic, but not allways
                        data_ids = []
                        for fid in self.session_data.selected_fids:
                            data_feature, error_msg = self.tool_get_data_feature(data_fid=fid)
                            if data_feature:
                                data_ids.append(data_feature[self.derived_settings.dataLyrIdField.name()])

                        if data_ids:
                            integer_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong]
                            if self.derived_settings.dataLyrIdField.type() in integer_field_types:
                                # ID-field integer, but the join-concatentation requires an array of strings
                                select_in_string = ','.join([str(_id) for _id in data_ids])
                            else:
                                # ID-field not integer, so the ids for the provider-side concatenated sql-filter-clause have to be enclosed with quotation marks
                                select_in_string = ','.join([("'" + str(_id) + "'") for _id in data_ids])

                            filter_expression = f'"{self.derived_settings.dataLyrIdField.name()}" in ({select_in_string})'
                            self.derived_settings.dataLyr.setSubsetString(filter_expression)
                            # rest is done by sys_layer_slot, dataLyr->subsetStringChanged-signal
                            # dependend show-layer will automatically be filtered, too

                    else:
                        self.dlg_append_log_message('INFO', MY_DICT.tr('no_features_listet'))
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_filter_if_editable'))

    def s_transfer_feature_selection(self):
        """transfer complete feature-selection to data- and show-layer
        see st_select_in_layer for single features"""
        # Rev. 2024-06-25
        # visually remove graphics and unselect qtrv_feature_selection
        self.cvs_hide_markers()

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:

            selection_mode = 'replace_selection'
            if QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers():
                selection_mode = 'remove_from_selection'
            elif QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers():
                selection_mode = 'add_to_selection'

            if self.session_data.selected_fids:
                # same feature in data-layer and show-layer can have different fids
                show_fids = []
                if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                    for data_fid in self.session_data.selected_fids:
                        show_feature, error_msg = self.tool_get_show_feature(data_fid=data_fid)
                        if show_feature:
                            show_fids.append(show_feature.id())

                if selection_mode == 'replace_selection':
                    self.derived_settings.dataLyr.removeSelection()
                    self.derived_settings.dataLyr.select(self.session_data.selected_fids)
                    if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                        self.derived_settings.showLyr.removeSelection()
                        self.derived_settings.showLyr.select(show_fids)
                elif selection_mode == 'remove_from_selection':
                    self.derived_settings.dataLyr.deselect(self.session_data.selected_fids)
                    if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                        self.derived_settings.showLyr.deselect(show_fids)
                else:
                    self.derived_settings.dataLyr.select(self.session_data.selected_fids)
                    if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                        self.derived_settings.showLyr.select(show_fids)

            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_features_listet'))

    def s_zoom_to_feature_selection(self):
        """Zooms canvas to feature-selection
        iterates through self.session_data.selected_fids
        checks validity,
        calculates Point-Geometries and their extent,
        zooms/pans to this extent
        """
        # Rev. 2024-06-25

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            if self.session_data.selected_fids:
                # calculate extent of the selected LoL-Features
                # From-Point, To-Point and Segment-Geometry taken into account
                x_coords = []
                y_coords = []
                # list of feature-ids for features with pol_from/pol_to/segment-calculation-problems
                skipped_fids = []
                for data_fid in self.session_data.selected_fids:
                    data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
                    if data_feature:
                        ref_id = data_feature[self.derived_settings.dataLyrReferenceField.name()]
                        offset = data_feature[self.derived_settings.dataLyrOffsetField.name()]
                        stationing_from = data_feature[self.derived_settings.dataLyrStationingFromField.name()]
                        stationing_to = data_feature[self.derived_settings.dataLyrStationingToField.name()]
                        ref_feature, error_msg = self.tool_get_reference_feature(ref_id=ref_id)
                        if ref_feature:
                            if ref_feature.hasGeometry():
                                pol_from = PoLFeature()
                                pol_from.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                                pol_from.recalc_by_stationing(stationing_from, self.stored_settings.lrMode)

                                if pol_from.is_valid:
                                    projected_point = ref_feature.geometry().interpolate(pol_from.snap_n_abs)
                                    if not projected_point.isEmpty():
                                        x_coords.append(projected_point.asPoint().x())
                                        y_coords.append(projected_point.asPoint().y())
                                else:
                                    skipped_fids.append(data_fid)

                                pol_to = PoLFeature()
                                pol_to.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                                pol_to.recalc_by_stationing(stationing_to, self.stored_settings.lrMode)

                                if pol_to.is_valid:
                                    projected_point = ref_feature.geometry().interpolate(pol_to.snap_n_abs)
                                    if not projected_point.isEmpty():
                                        x_coords.append(projected_point.asPoint().x())
                                        y_coords.append(projected_point.asPoint().y())
                                else:
                                    skipped_fids.append(data_fid)

                                if pol_from.is_valid and pol_to.is_valid:
                                    segment_geom, segment_error = tools.MyTools.get_segment_geom_n(ref_feature.geometry(), pol_from.snap_n_abs, pol_to.snap_n_abs, offset)
                                    if segment_geom:
                                        extent = segment_geom.boundingBox()
                                        x_coords.append(extent.xMinimum())
                                        x_coords.append(extent.xMaximum())
                                        y_coords.append(extent.yMinimum())
                                        y_coords.append(extent.yMaximum())
                                    else:
                                        skipped_fids.append(data_fid)
                                        pass
                            else:
                                skipped_fids.append(data_fid)
                        else:
                            skipped_fids.append(data_fid)
                    else:
                        skipped_fids.append(data_fid)

                self.cvs_zoom_to_coords(x_coords, y_coords, 'zoom', self.derived_settings.refLyr.crs())

                # make unique
                skipped_fids = list(dict.fromkeys(skipped_fids))

                if len(skipped_fids) > 0:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('skipped_invalids_msg', len(skipped_fids), len(self.session_data.selected_fids)))


            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_features_listet'))

    def s_append_show_features(self):
        """Adds features from showLyr to self.session_data.selected_fids
        Note: features must be committed in dataLyr (fid positive)
        """
        # Rev. 2024-06-25

        selection_mode = 'select_all'
        if QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers() and QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers():
            selection_mode = 'append_selected'
        elif QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers():
            selection_mode = 'select_selected'

        if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
            additional_feature_ids = []
            if selection_mode == 'select_selected' or selection_mode == 'append_selected':
                # fids in show-layer can be different from fids in data-layer

                for show_feature in self.derived_settings.showLyr.getSelectedFeatures():
                    data_feature, error_msg = self.tool_get_data_feature(data_id=show_feature[self.stored_settings.showLyrBackReferenceFieldName])
                    if data_feature:
                        additional_feature_ids.append(data_feature.id())

                if len(additional_feature_ids):
                    if selection_mode == 'select_selected':
                        self.session_data.selected_fids = additional_feature_ids
                    else:
                        self.session_data.selected_fids += additional_feature_ids
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('no_selection_in_show_layer'))
            else:
                # selection_mode = 'select_all'
                for show_feature in self.derived_settings.showLyr.getFeatures():
                    data_feature, error_msg = self.tool_get_data_feature(data_id=show_feature[self.stored_settings.showLyrBackReferenceFieldName])
                    if data_feature:
                        additional_feature_ids.append(data_feature.id())

                if len(additional_feature_ids):
                    self.session_data.selected_fids = additional_feature_ids
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('no_features_in_show_layer'))

            self.dlg_refresh_feature_selection_section()

    def s_open_ref_form(self):
        """for self.session_data.current_ref_fid: open attribute-form, highlight geometry on map, optional zoom with shift"""
        # Rev. 2024-07-28
        if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                zoom_to_feature = bool(QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers())
                if ref_feature:
                    # allways show feature-form, if feature exists:
                    feature_form = tools.MyTools.get_feature_form(self.iface, self.derived_settings.refLyr, ref_feature)
                    feature_form.show()
                    # draw and optionally zoom:
                    if ref_feature.hasGeometry():
                        self.cvs_draw_reference_geom(reference_geom=ref_feature.geometry(), zoom_to_feature=zoom_to_feature)
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message("WARNING", error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))

    def s_open_show_tbl(self):
        """opens the Show-Layer-attribute-table"""
        # Rev. 2024-06-25
        if self.SVS.SHOW_LAYER_EXISTS in self.system_vs:
            self.iface.showAttributeTable(self.derived_settings.showLyr)

    def s_open_data_tbl(self):
        """opens the Data-Layer-attribute-table """
        # Rev. 2024-06-25
        if self.SVS.DATA_LAYER_EXISTS in self.system_vs:
            self.iface.showAttributeTable(self.derived_settings.dataLyr)

    def s_open_ref_tbl(self):
        """opens the Reference-Layer-attribute-table """
        # Rev. 2024-06-26

        if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            self.iface.showAttributeTable(self.derived_settings.refLyr)

    def s_define_ref_lyr_display_expression(self):
        """opens the dialog for editing the displayExpression of Reference-Layer
        if expression is accepeted the displayExpressionChanged-Signal-Slot will be triggered"""
        # Rev. 2024-06-26
        if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            dlg = qgis.gui.QgsExpressionBuilderDialog(self.derived_settings.refLyr, self.derived_settings.refLyr.displayExpression())
            dlg.setWindowTitle(MY_DICT.tr('edit_display_exp_dlg_title', self.derived_settings.refLyr.name()))
            exec_result = dlg.exec()
            if exec_result:
                # expressionBuilder -> https://api.qgis.org/api/classQgsExpressionBuilderWidget.html
                if dlg.expressionBuilder().isExpressionValid():
                    self.derived_settings.refLyr.setDisplayExpression(dlg.expressionText())
                    self.dlg_append_log_message('SUCCESS', MY_DICT.tr('display_exp_valid', self.derived_settings.refLyr.name()))
                    # dialog-refresh is done by trigger
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('display_exp_invalid', self.derived_settings.refLyr.name()))

    def s_define_data_lyr_display_expression(self):
        """opens the dialog for editing the displayExpression of Data-Layer
        if expression is accepeted the displayExpressionChanged-Signal-Slot will be triggered
        """
        # Rev. 2024-06-26
        if self.SVS.DATA_LAYER_EXISTS in self.system_vs:
            dlg = qgis.gui.QgsExpressionBuilderDialog(self.derived_settings.dataLyr, self.derived_settings.dataLyr.displayExpression())
            dlg.setWindowTitle(MY_DICT.tr('edit_display_exp_dlg_title', self.derived_settings.dataLyr.name()))
            exec_result = dlg.exec()
            if exec_result:
                if dlg.expressionBuilder().isExpressionValid():
                    self.derived_settings.dataLyr.setDisplayExpression(dlg.expressionText())
                    self.dlg_append_log_message('SUCCESS', MY_DICT.tr('display_exp_valid', self.derived_settings.dataLyr.name()))
                    # dialog-refresh is done by trigger
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('display_exp_invalid', self.derived_settings.dataLyr.name()))

    def s_define_show_layer_display_expression(self):
        """opens the dialog for editing the displayExpression of Show-Layer
        if expression is accepeted the displayExpressionChanged-Signal-Slot will be triggered
        """
        # Rev. 2024-06-27
        if self.SVS.SHOW_LAYER_EXISTS in self.system_vs:
            dlg = qgis.gui.QgsExpressionBuilderDialog(self.derived_settings.showLyr, self.derived_settings.showLyr.displayExpression())
            dlg.setWindowTitle(MY_DICT.tr('edit_display_exp_dlg_title', self.derived_settings.showLyr.name()))
            exec_result = dlg.exec()
            if exec_result:
                if dlg.expressionBuilder().isExpressionValid():
                    self.derived_settings.showLyr.setDisplayExpression(dlg.expressionText())
                    self.dlg_append_log_message('SUCCESS', MY_DICT.tr('display_exp_valid', self.derived_settings.showLyr.name()))
                    # dialog-refresh is done by trigger
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('display_exp_invalid', self.derived_settings.showLyr.name()))

    def s_n_abs_from_edited(self, stationing_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-from, changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.pol_from and self.session_data.measure_feature.pol_from
        refreshes dialog and canvas-grafics
        :param stationing_from: changed widget-value
        """
        # Rev. 2024-06-27
        self.cvs_hide_markers()
        self.dlg_clear_from_measurements()
        self.session_data.pol_from = None
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():
                        pol_from = PoLFeature()
                        pol_from.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_from.recalc_by_stationing(stationing_from, 'Nabs')
                        if pol_from.is_valid:
                            self.session_data.pol_from = pol_from
                            if self.session_data.measure_feature is not None and self.session_data.pol_from.ref_fid == self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_from(pol_from)
                            elif self.session_data.pol_to is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'enf', 'snt', 'sgn', 'rfl'])
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_reference_feature_selected'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_layer_missing'))

    def s_delta_n_fract_edited(self, delta_n_perc: float) -> None:
        """moves self.session_data.measure_feature.pol_to by change of relative segment-length
        :param delta_n_perc: Percent-Value, widget limited to range 0...100"""
        # Rev. 2024-06-28
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        delta_n_fract = max(-100, min(100, delta_n_perc)) / 100
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)

                if reference_geom:
                    ref_len = reference_geom.length()
                    old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                    old_to = self.session_data.measure_feature.pol_to.snap_n_abs
                    old_len = old_to - old_from
                    # widget shows percentage
                    delta_n = ref_len * delta_n_fract

                    delta_len = delta_n - old_len

                    new_from = old_from
                    new_to = old_to + delta_len

                    if new_to > ref_len:
                        new_to = ref_len
                        new_from = max(ref_len - delta_n, 0)

                    pol_from = self.session_data.measure_feature.pol_from.__copy__()
                    pol_from.recalc_by_stationing(new_from, 'Nabs')
                    if pol_from.is_valid:
                        pol_to = self.session_data.measure_feature.pol_to.__copy__()
                        pol_to.recalc_by_stationing(new_to, 'Nabs')

                        if pol_to.is_valid:
                            self.session_data.measure_feature.set_pol_from(pol_from)
                            self.session_data.measure_feature.set_pol_to(pol_to)
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                    self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_layer_missing'))

    def s_delta_n_abs_edited(self, delta_n_abs: float) -> None:
        """moves self.session_data.measure_feature.pol_to by change of absolute segment-length"""
        # Rev. 2024-06-28
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:

            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
                if reference_geom:
                    ref_len = reference_geom.length()
                    old_from = self.session_data.measure_feature.pol_from.snap_n_abs
                    old_to = self.session_data.measure_feature.pol_to.snap_n_abs

                    old_len = abs(old_to - old_from)
                    delta_len = abs(delta_n_abs) - old_len
                    new_from = old_from
                    new_to = old_to + delta_len

                    if new_to > ref_len or new_from > ref_len:
                        new_to = ref_len
                        new_from = max(ref_len - delta_n_abs, 0)

                    pol_from = self.session_data.measure_feature.pol_from.__copy__()
                    pol_from.recalc_by_stationing(new_from, 'Nabs')
                    if pol_from.is_valid:
                        pol_to = self.session_data.measure_feature.pol_to.__copy__()
                        pol_to.recalc_by_stationing(new_to, 'Nabs')

                        if pol_to.is_valid:
                            self.session_data.measure_feature.set_pol_from(pol_from)
                            self.session_data.measure_feature.set_pol_to(pol_to)

                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                    self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_layer_missing'))

    def s_delta_m_abs_edited(self, delta_m_abs: float) -> None:
        """moves self.session_data.measure_feature.pol_to by change of absolute M-segment-length"""
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        if (self.SVS.REFERENCE_LAYER_USABLE | self.SVS.REFERENCE_LAYER_M_ENABLED) in self.system_vs:
            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
                if reference_geom:
                    old_from = self.session_data.measure_feature.pol_from.snap_m_abs

                    new_from = old_from
                    new_to = old_from + delta_m_abs

                    first_vertex_m, last_vertex_m, error_msg = tools.MyTools.get_first_last_vertex_m(reference_geom)
                    if not error_msg:
                        if new_to > last_vertex_m:
                            new_to = last_vertex_m
                            new_from = max(first_vertex_m, new_to - delta_m_abs)

                        pol_from = self.session_data.measure_feature.pol_from.__copy__()
                        pol_from.recalc_by_stationing(new_from, 'Mabs')

                        if pol_from.is_valid:
                            pol_to = self.session_data.measure_feature.pol_to.__copy__()
                            pol_to.recalc_by_stationing(new_to, 'Mabs')
                            if pol_to.is_valid:
                                self.session_data.measure_feature.set_pol_from(pol_from)
                                self.session_data.measure_feature.set_pol_to(pol_to)
                            else:
                                self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                        self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('m_reference_layer_missing'))

    def s_delta_m_fract_edited(self, delta_m_perc: float) -> None:
        """moves self.session_data.measure_feature.pol_to by change of relative M-segment-length"""
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_measurements()
        delta_m_perc = max(-100, min(100, delta_m_perc))
        delta_m_fract = delta_m_perc / 100
        if (self.SVS.REFERENCE_LAYER_USABLE | self.SVS.REFERENCE_LAYER_M_ENABLED) in self.system_vs:
            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.measure_feature.ref_fid)
                if reference_geom:
                    old_from = self.session_data.measure_feature.pol_from.snap_m_abs

                    first_vertex_m, last_vertex_m, error_msg = tools.MyTools.get_first_last_vertex_m(reference_geom)

                    if not error_msg:
                        delta_m_abs = (last_vertex_m - first_vertex_m) * delta_m_fract

                        new_from = old_from
                        new_to = old_from + delta_m_abs

                        if new_to > last_vertex_m:
                            new_to = last_vertex_m
                            new_from = max(first_vertex_m, new_to - delta_m_abs)

                        pol_from = self.session_data.measure_feature.pol_from.__copy__()
                        pol_from.recalc_by_stationing(new_from, 'Mabs')

                        if pol_from.is_valid:
                            pol_to = self.session_data.measure_feature.pol_to.__copy__()
                            pol_to.recalc_by_stationing(new_to, 'Mabs')

                            if pol_to.is_valid:
                                self.session_data.measure_feature.set_pol_from(pol_from)
                                self.session_data.measure_feature.set_pol_to(pol_to)

                            else:
                                self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))

                        self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))

        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('m_reference_layer_missing'))

    def s_n_abs_to_edited(self, stationing_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-to, changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.pol_to and self.session_data.measure_feature.pol_to
        refreshes dialog and canvas-grafics
        :param stationing_to: changed widget-value
        """
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_to_measurements()
        self.session_data.pol_to = None
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:

            # new point via numerical editing
            # current selected reference-feature:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():
                        pol_to = PoLFeature()
                        pol_to.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_to.recalc_by_stationing(stationing_to, 'Nabs')
                        if pol_to.is_valid:
                            self.session_data.pol_to = pol_to
                            if self.session_data.measure_feature is not None and self.session_data.pol_to.ref_fid == self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_to(pol_to)
                            elif self.session_data.pol_from is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_reference_feature_selected', True))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_layer_missing'))

    def s_m_abs_from_edited(self, stationing_m_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m,
        Conditions:
        reference-layer is m-enabled
        referenced-geometry ST_IsValidTrajectory (single-parted, ascending M-values)
        changed via user-input or spin-Buttons
        :param stationing_m_from: changed widget-value
        """
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_from_measurements()
        self.session_data.pol_from = None
        if (self.SVS.REFERENCE_LAYER_USABLE | self.SVS.REFERENCE_LAYER_M_ENABLED) in self.system_vs:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():
                        pol_from = PoLFeature()
                        pol_from.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_from.recalc_by_stationing(stationing_m_from, 'Mabs')

                        if pol_from.is_valid:
                            self.session_data.pol_from = pol_from
                            if self.session_data.measure_feature is not None and self.session_data.pol_from.ref_fid == self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_from(pol_from)
                            elif self.session_data.pol_to is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'enf', 'snt', 'sgn', 'rfl'])
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('m_reference_layer_missing'))

    def s_m_abs_to_edited(self, stationing_m_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m,
        Conditions:
        reference-layer is m-enabled
        referenced-geometry ST_IsValidTrajectory (single-parted, ascending M-values)
        changed via user-input or spin-Buttons
        :param stationing_m_to: changed widget-value
        """
        self.cvs_hide_markers()
        self.dlg_clear_to_measurements()
        self.session_data.pol_to = None
        if (self.SVS.REFERENCE_LAYER_USABLE | self.SVS.REFERENCE_LAYER_M_ENABLED) in self.system_vs:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():
                        pol_to = PoLFeature()
                        pol_to.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_to.recalc_by_stationing(stationing_m_to, 'Mabs')

                        if pol_to.is_valid:
                            self.session_data.pol_to = pol_to
                            if self.session_data.measure_feature is not None and self.session_data.pol_to.ref_fid == self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_to(pol_to)
                            elif self.session_data.pol_from is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message("WARNING", error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('m_reference_layer_missing'))

    def s_n_fract_from_edited(self, stationing_n_perc_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-from (fract, percentage 0...100), changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.pol_from and self.session_data.measure_feature.pol_from
        refreshes dialog and canvas-grafics
        :param stationing_n_perc_from: changed widget-value in percent
        """
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_from_measurements()
        self.session_data.pol_from = None
        stationing_n_fract_from = stationing_n_perc_from / 100
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            # current selected reference-feature:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():
                        pol_from = PoLFeature()
                        pol_from.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_from.recalc_by_stationing(stationing_n_fract_from, 'Nfract')
                        if pol_from.is_valid:
                            self.session_data.pol_from = pol_from
                            if self.session_data.measure_feature and self.session_data.pol_from.ref_fid and self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_from(pol_from)
                            elif self.session_data.pol_to is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'enf', 'snt', 'sgn', 'rfl'])
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_layer_missing'))

    def s_n_fract_to_edited(self, stationing_n_perc_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing-n-from (fract, percentage 0...100), changed via user-input or spin-Buttons
        create or move point on selected reference-feature via numerical editing
        affects self.session_data.pol_to and self.session_data.measure_feature.pol_to
        refreshes dialog and canvas-grafics
        :param stationing_n_perc_to: changed widget-value in percent
        """
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_to_measurements()
        self.session_data.pol_to = None
        stationing_n_fract_to = stationing_n_perc_to / 100
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            # new point via numerical editing
            # current selected reference-feature:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():
                        pol_to = PoLFeature()
                        pol_to.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_to.recalc_by_stationing(stationing_n_fract_to, 'Nfract')
                        if pol_to.is_valid:
                            self.session_data.pol_to = pol_to
                            if self.session_data.measure_feature is not None and self.session_data.pol_to.ref_fid == self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_to(pol_to)
                            elif self.session_data.pol_from is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message("WARNING", error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_layer_missing'))

    def s_m_fract_from_edited(self, stationing_m_perc_from: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m_fract (percentage),
        Conditions:
        reference-layer is m-enabled
        self.session_data.measure_feature.pol_from exists
        referenced-geometry ST_IsValidTrajectory (single-parted, ascending M-values)
        changed via user-input or spin-Buttons
        :param stationing_m_perc_from: changed widget-value in percent
        """
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_from_measurements()
        self.session_data.pol_from = None
        stationing_m_perc_from = max(0, min(100, stationing_m_perc_from))
        stationing_m_fract_from = stationing_m_perc_from / 100
        if (self.SVS.REFERENCE_LAYER_USABLE | self.SVS.REFERENCE_LAYER_M_ENABLED) in self.system_vs:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():
                        pol_from = PoLFeature()
                        pol_from.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_from.recalc_by_stationing(stationing_m_fract_from, 'Mfract')
                        if pol_from.is_valid:
                            self.session_data.pol_from = pol_from
                            if self.session_data.measure_feature is not None and self.session_data.pol_from.ref_fid == self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_from(pol_from)
                            elif self.session_data.pol_to is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'enf', 'snt', 'sgn', 'rfl'])
                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_from.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('m_reference_layer_missing'))


    def tool_draw_and_refresh_session_data(self, draw_markers: list = None, extent_markers: list = None, extent_mode: str = None):
        """helper-function
        draws self.session_data.measure_feature or self.session_data.pol_from/pol_to if measure_feature is not set (draw_markers/extent_markers thinned out then)
        refreshes measurements for measure_feature or self.session_data.pol_from/pol_to if measure_feature is not set
        :param draw_markers: combination of marker-types
        :param extent_markers: combination of marker-types, optional zoom to specific markers
        :param extent_mode: zoom/pan
        """
        # Rev. 2024-07-03
        if not draw_markers:
            draw_markers = []

        if not extent_markers:
            extent_markers = []

        self.cvs_hide_markers(draw_markers)
        self.dlg_clear_measurements()

        if self.session_data.measure_feature and self.session_data.measure_feature.is_valid:
            self.dlg_refresh_measurements(self.session_data.measure_feature)
            self.cvs_draw_feature(self.session_data.measure_feature, draw_markers, extent_markers, extent_mode)
        else:
            if self.session_data.pol_from and self.session_data.pol_from.is_valid:
                self.dlg_refresh_from_measurements(self.session_data.pol_from)
                self.cvs_draw_from_markers(self.session_data.pol_from, draw_markers, extent_markers, extent_mode)

            if self.session_data.pol_to and self.session_data.pol_to.is_valid:
                self.dlg_refresh_to_measurements(self.session_data.pol_to)
                self.cvs_draw_to_markers(self.session_data.pol_to, draw_markers, extent_markers, extent_mode)

        self.dlg_refresh_measure_section()

    def s_m_fract_to_edited(self, stationing_m_perc_to: float) -> None:
        """Slot for valueChanged-Signal of the QDoubleSpinBox for stationing_m_fract (percentage),
        Conditions:
        reference-layer is m-enabled
        self.session_data.measure_feature.pol_to exists
        referenced-geometry ST_IsValidTrajectory (single-parted, ascending M-values)
        changed via user-input or spin-Buttons
        :param stationing_m_perc_to: changed widget-value in percent
        """
        # Rev. 2024-07-03
        self.cvs_hide_markers()
        self.dlg_clear_to_measurements()
        self.session_data.pol_to = None
        stationing_m_perc_to = max(0, min(100, stationing_m_perc_to))
        stationing_m_fract_to = stationing_m_perc_to / 100
        if (self.SVS.REFERENCE_LAYER_USABLE | self.SVS.REFERENCE_LAYER_M_ENABLED) in self.system_vs:
            if self.session_data.current_ref_fid is not None:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.current_ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():

                        pol_to = PoLFeature()
                        pol_to.set_ref_fid(self.derived_settings.refLyr, ref_feature.id())
                        pol_to.recalc_by_stationing(stationing_m_fract_to, 'Mfract')
                        if pol_to.is_valid:
                            self.session_data.pol_to = pol_to
                            if self.session_data.measure_feature is not None and self.session_data.pol_to.ref_fid == self.session_data.measure_feature.ref_fid:
                                self.session_data.measure_feature.set_pol_to(pol_to)
                            elif self.session_data.pol_from is not None and self.session_data.pol_from.ref_fid == self.session_data.pol_to.ref_fid:
                                self.session_data.measure_feature = LoLFeature()
                                self.session_data.measure_feature.set_pol_from(self.session_data.pol_from)
                                self.session_data.measure_feature.set_pol_to(self.session_data.pol_to)

                            self.tool_draw_and_refresh_session_data(['snf', 'ent', 'snt', 'sgn', 'rfl'])

                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('pol_recalculation_failed', pol_to.last_error))
                    else:
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_reference_feature_selected'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('m_reference_layer_missing'))

    def cvs_draw_feature(self, lol_feature: LoLFeature, draw_markers: list = None, extent_markers: list = None, extent_mode: str = None):
        """draws complete lol_feature: stationing points, segment, reference-line
         usually called with lol_feature == self.session_data.edit_feature or self.session_data.measure_feature
        :param lol_feature: selected and parsed LoL-feature
        :param draw_markers: combination of marker-types, all but cache-markers supported here
        :param extent_markers: combination of marker-types, optional zoom to specific markers
        :param extent_mode: zoom/pan
        """
        # Rev. 2024-07-03
        if not draw_markers:
            draw_markers = []

        if not extent_markers:
            extent_markers = []

        # pre-hide all draw_markers
        self.cvs_hide_markers(draw_markers)
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            # mostly called via self.session_data.edit_feature, which could be None
            if lol_feature and lol_feature.check_is_valid():

                if lol_feature.ref_fid:
                    x_coords = []
                    y_coords = []
                    reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=lol_feature.ref_fid)
                    if reference_geom:

                        if 'snf' in draw_markers or 'enf' in draw_markers or 'snf' in extent_markers or 'enf' in extent_markers:

                            if lol_feature.pol_from and lol_feature.pol_from.is_valid:
                                projected_point_n = reference_geom.interpolate(lol_feature.pol_from.snap_n_abs)
                                if not projected_point_n.isEmpty():
                                    projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                                    if 'snf' in draw_markers:
                                        self.vm_snf.setCenter(projected_point_n.asPoint())
                                        self.vm_snf.show()

                                    if 'enf' in draw_markers:
                                        self.vm_enf.setCenter(projected_point_n.asPoint())
                                        self.vm_enf.show()

                                    if 'snf' in extent_markers or 'enf' in extent_markers:
                                        x_coords.append(projected_point_n.asPoint().x())
                                        y_coords.append(projected_point_n.asPoint().y())
                                else:
                                    self.dlg_append_log_message('INFO', MY_DICT.tr('pol_from_recalculation_failed'))
                            else:
                                self.dlg_append_log_message('INFO', MY_DICT.tr('pol_from_recalculation_failed'))

                        if 'snt' in draw_markers or 'ent' in draw_markers or 'snt' in extent_markers or 'ent' in extent_markers:

                            if lol_feature.pol_to and lol_feature.pol_to.is_valid:
                                projected_point_n = reference_geom.interpolate(lol_feature.pol_to.snap_n_abs)
                                if not projected_point_n.isEmpty():
                                    projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                                    if 'snt' in draw_markers:
                                        self.vm_snt.setCenter(projected_point_n.asPoint())
                                        self.vm_snt.show()

                                    if 'ent' in draw_markers:
                                        self.vm_ent.setCenter(projected_point_n.asPoint())
                                        self.vm_ent.show()

                                    if 'snt' in extent_markers or 'ent' in extent_markers:
                                        x_coords.append(projected_point_n.asPoint().x())
                                        y_coords.append(projected_point_n.asPoint().y())
                                else:
                                    self.dlg_append_log_message('INFO', MY_DICT.tr('pol_to_recalculation_failed'))
                            else:
                                self.dlg_append_log_message('INFO', MY_DICT.tr('pol_to_recalculation_failed'))

                        if 'sgn' in draw_markers or 'sgn' in extent_markers:

                            if lol_feature.pol_from and lol_feature.pol_to and lol_feature.pol_from.is_valid and lol_feature.pol_to.is_valid:

                                segment_geom, segment_error = tools.MyTools.get_segment_geom_n(reference_geom, lol_feature.pol_from.snap_n_abs, lol_feature.pol_to.snap_n_abs, lol_feature.offset)
                                if segment_geom:
                                    if 'sgn' in draw_markers:
                                        # always draw, even if there is no geometry, because of cvs_check_marker_visibility
                                        self.rb_sgn.setToGeometry(segment_geom, self.derived_settings.refLyr)
                                        self.rb_sgn.show()

                                    if 'sgn' in extent_markers:
                                        extent = segment_geom.boundingBox()
                                        tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                                        extent = tr.transformBoundingBox(extent)
                                        x_coords.append(extent.xMinimum())
                                        x_coords.append(extent.xMaximum())
                                        y_coords.append(extent.yMinimum())
                                        y_coords.append(extent.yMaximum())
                                    else:
                                        # f.e. pol_from.snap_n_abs == pol_to.snap_n_abs
                                        pass
                                else:
                                    self.rb_sgn.hide()

                            else:
                                self.dlg_append_log_message('INFO', MY_DICT.tr('segment_interpolation_failed'))

                        if 'sg0' in draw_markers or 'sg0' in extent_markers:

                            if lol_feature.pol_from and lol_feature.pol_to and lol_feature.pol_from.is_valid and lol_feature.pol_to.is_valid:

                                segment_geom_0, segment_error = tools.MyTools.get_segment_geom_n(reference_geom, lol_feature.pol_from.snap_n_abs, lol_feature.pol_to.snap_n_abs, 0)

                                if segment_geom_0:
                                    if 'sg0' in draw_markers:
                                        # always draw, even if there is no geometry, because of cvs_check_marker_visibility
                                        self.rb_sg0.setToGeometry(segment_geom_0, self.derived_settings.refLyr)
                                        self.rb_sg0.show()

                                    if segment_geom_0 and 'sg0' in extent_markers:
                                        extent = segment_geom_0.boundingBox()
                                        tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                                        extent = tr.transformBoundingBox(extent)
                                        x_coords.append(extent.xMinimum())
                                        x_coords.append(extent.xMaximum())
                                        y_coords.append(extent.yMinimum())
                                        y_coords.append(extent.yMaximum())
                                    else:
                                        # f.e. pol_from.snap_n_abs == pol_to.snap_n_abs
                                        pass
                                else:
                                    self.rb_sg0.hide()

                            else:
                                self.dlg_append_log_message('INFO', MY_DICT.tr('segment_interpolation_failed'))

                        # Show and zoom reference-feature only in combination with checked data-feature n/m
                        if 'rfl' in draw_markers:
                            self.rb_rfl.setToGeometry(reference_geom, self.derived_settings.refLyr)
                            self.rb_rfl.show()

                        # zoom/pan tor reference-line !?
                        if 'rfl' in extent_markers:
                            extent = reference_geom.boundingBox()
                            tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                            extent = tr.transformBoundingBox(extent)

                            x_coords.append(extent.xMinimum())
                            x_coords.append(extent.xMaximum())
                            y_coords.append(extent.yMinimum())
                            y_coords.append(extent.yMaximum())

                        if extent_mode and extent_markers:
                            # coordinates already transformed to canvas-crs
                            self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode)
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)
            else:
                pass
        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('reference_or_data_layer_missing'))

    def cvs_draw_po_pro_feature(self, po_pro_feature: LoLFeature, draw_markers: list = None, extent_markers: list = None, extent_mode: str = None):
        """shows stationing points, cached points, segments, reference-line for cached post-processing-feature
        :param po_pro_feature: current data-feature, self.session_data.po_pro_feature
        :param draw_markers: combination of draw makers, all types supported here, included cache-markers
        :param extent_markers: optional zoom to combination of extent-markers
        :param extent_mode: zoom/pan
        """

        if not draw_markers:
            draw_markers = []

        if not extent_markers:
            extent_markers = []

        # pre-hide all draw_markers
        self.cvs_hide_markers(draw_markers)
        self.tool_check_po_pro_data_cache()
        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            # called via self.session_data.po_pro_feature, which could be none
            if po_pro_feature:
                if po_pro_feature.data_fid in self.session_data.po_pro_data_cache:

                    x_coords = []
                    y_coords = []

                    po_pro_cached_feature = self.session_data.po_pro_data_cache[self.session_data.po_pro_feature.data_fid]

                    reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=po_pro_cached_feature.ref_fid)

                    if reference_geom:
                        data_feature, error_msg = self.tool_get_data_feature(data_fid=po_pro_cached_feature.data_fid)

                        if data_feature:

                            if 'snf' in draw_markers or 'enf' in draw_markers or 'snf' in extent_markers or 'enf' in extent_markers:

                                projected_point_n = reference_geom.interpolate(po_pro_feature.pol_from.snap_n_abs)
                                if not projected_point_n.isEmpty():
                                    projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                                    if 'snf' in draw_markers:
                                        self.vm_snf.setCenter(projected_point_n.asPoint())
                                        self.vm_snf.show()

                                    if 'enf' in draw_markers:
                                        self.vm_enf.setCenter(projected_point_n.asPoint())
                                        self.vm_enf.show()

                                    if 'snf' in extent_markers or 'enf' in extent_markers:
                                        x_coords.append(projected_point_n.asPoint().x())
                                        y_coords.append(projected_point_n.asPoint().y())

                            if 'snt' in draw_markers or 'ent' in draw_markers or 'snt' in extent_markers or 'ent' in extent_markers:

                                projected_point_n = reference_geom.interpolate(po_pro_feature.pol_to.snap_n_abs)
                                if not projected_point_n.isEmpty():
                                    projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                                    if 'snt' in draw_markers:
                                        self.vm_snt.setCenter(projected_point_n.asPoint())
                                        self.vm_snt.show()

                                    if 'ent' in draw_markers:
                                        self.vm_ent.setCenter(projected_point_n.asPoint())
                                        self.vm_ent.show()

                                    if 'snt' in extent_markers or 'ent' in extent_markers:
                                        x_coords.append(projected_point_n.asPoint().x())
                                        y_coords.append(projected_point_n.asPoint().y())

                            if 'sgn' in draw_markers or 'sgn' in extent_markers:

                                segment_geom, segment_error = tools.MyTools.get_segment_geom_n(reference_geom, po_pro_feature.pol_from.snap_n_abs, po_pro_feature.pol_to.snap_n_abs, po_pro_feature.offset)
                                if segment_geom:
                                    if 'sgn' in draw_markers:
                                        self.rb_sgn.setToGeometry(segment_geom, self.derived_settings.refLyr)
                                        self.rb_sgn.show()

                                    if 'sgn' in extent_markers:
                                        extent = segment_geom.boundingBox()
                                        tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                                        extent = tr.transformBoundingBox(extent)
                                        x_coords.append(extent.xMinimum())
                                        x_coords.append(extent.xMaximum())
                                        y_coords.append(extent.yMinimum())
                                        y_coords.append(extent.yMaximum())
                                    else:
                                        # f.e. pol_from.snap_n_abs == pol_to.snap_n_abs
                                        pass
                                else:
                                    self.rb_sgn.show()

                            if 'sg0' in draw_markers or 'sg0' in extent_markers:

                                segment_geom_0, segment_error = tools.MyTools.get_segment_geom_n(reference_geom, po_pro_feature.pol_from.snap_n_abs, po_pro_feature.pol_to.snap_n_abs, 0)
                                if segment_geom_0:
                                    if 'sg0' in draw_markers:
                                        self.rb_sg0.setToGeometry(segment_geom_0, self.derived_settings.refLyr)
                                        self.rb_sg0.show()

                                    if 'sg0' in extent_markers:
                                        extent = segment_geom_0.boundingBox()
                                        tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                                        extent = tr.transformBoundingBox(extent)
                                        x_coords.append(extent.xMinimum())
                                        x_coords.append(extent.xMaximum())
                                        y_coords.append(extent.yMinimum())
                                        y_coords.append(extent.yMaximum())
                                    else:
                                        # f.e. pol_from.snap_n_abs == pol_to.snap_n_abs
                                        pass
                                else:
                                    self.rb_sg0.hide()

                            cached_geom = self.session_data.po_pro_reference_cache[po_pro_cached_feature.ref_fid]

                            # special case post-processing: cached stationings on cached geometries
                            if 'csgn' in draw_markers or 'csgn' in extent_markers:
                                try:
                                    segment_geom, segment_error = tools.MyTools.get_segment_geom_n(cached_geom, po_pro_cached_feature.pol_from.snap_n_abs, po_pro_cached_feature.pol_to.snap_n_abs, po_pro_cached_feature.offset)
                                    if segment_geom:
                                        if 'csgn' in draw_markers:
                                            self.rb_csgn.setToGeometry(segment_geom, self.derived_settings.refLyr)
                                            self.rb_csgn.show()

                                        if 'csgn' in extent_markers:
                                            extent = segment_geom.boundingBox()
                                            tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                                            extent = tr.transformBoundingBox(extent)
                                            x_coords.append(extent.xMinimum())
                                            x_coords.append(extent.xMaximum())
                                            y_coords.append(extent.yMinimum())
                                            y_coords.append(extent.yMaximum())
                                        else:
                                            # f.e. pol_from.snap_n_abs == pol_to.snap_n_abs
                                            pass
                                    else:
                                        self.rb_csgn.hide()
                                except Exception as err:
                                    self.dlg_append_log_message('INFO', str(err))

                            if 'cnf' in draw_markers or 'cnf' in extent_markers:
                                projected_point_n = cached_geom.interpolate(po_pro_cached_feature.pol_from.snap_n_abs)
                                if not projected_point_n.isEmpty():
                                    projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                                    if 'cnf' in draw_markers:
                                        self.vm_pt_cnf.setCenter(projected_point_n.asPoint())
                                        self.vm_pt_cnf.show()

                                    if 'cnf' in extent_markers:
                                        x_coords.append(projected_point_n.asPoint().x())
                                        y_coords.append(projected_point_n.asPoint().y())

                            if 'cnt' in draw_markers or 'cnt' in extent_markers:

                                projected_point_n = cached_geom.interpolate(po_pro_cached_feature.pol_to.snap_n_abs)
                                if not projected_point_n.isEmpty():
                                    projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                                    if 'cnt' in draw_markers:
                                        self.vm_pt_cnt.setCenter(projected_point_n.asPoint())
                                        self.vm_pt_cnt.show()

                                    if 'cnt' in extent_markers:
                                        x_coords.append(projected_point_n.asPoint().x())
                                        y_coords.append(projected_point_n.asPoint().y())

                            # Show and zoom reference-feature only in combination with checked data-feature n/m
                            if 'rfl' in draw_markers:
                                self.rb_rfl.setToGeometry(reference_geom, self.derived_settings.refLyr)
                                self.rb_rfl.show()

                            # zoom/pan tor reference-line !?
                            if 'rfl' in extent_markers:
                                extent = reference_geom.boundingBox()
                                tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                                extent = tr.transformBoundingBox(extent)

                                x_coords.append(extent.xMinimum())
                                x_coords.append(extent.xMaximum())
                                y_coords.append(extent.yMinimum())
                                y_coords.append(extent.yMaximum())

                            if 'crfl' in draw_markers:
                                self.rb_crfl.setToGeometry(cached_geom, self.derived_settings.refLyr)
                                self.rb_crfl.show()

                            if 'crfl' in extent_markers:
                                extent = cached_geom.boundingBox()
                                tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                                extent = tr.transformBoundingBox(extent)

                                x_coords.append(extent.xMinimum())
                                x_coords.append(extent.xMaximum())
                                y_coords.append(extent.yMinimum())
                                y_coords.append(extent.yMaximum())

                            if extent_mode and extent_markers:
                                # coordinates already transformed to canvas-crs
                                self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode)

                        else:
                            self.dlg_append_log_message('WARNING', error_msg)
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('po_pro_data_feature_not_in_cache', po_pro_feature.data_fid))
            else:
                pass
        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('reference_or_data_layer_missing'))


    def cvs_draw_marker_at(self, stationing_n: float, draw_markers: list = None, extent_markers: list = None, extent_mode: str = None, reference_geom: qgis.core.QgsGeometry = None, ref_feature: qgis.core.QgsFeature = None, ref_id: int | str = None, ref_fid: int = None):
        """draw (multiple) markers at single stationing
        :param stationing_n: stationing along reference-line
        :param draw_markers: list of marker-types
        :param extent_markers: list of marker-types optional for zoom
        :param extent_mode: zoom/pan
        :param reference_geom: geometry queryable via...
        :param ref_feature:
        :param ref_id:
        :param ref_fid:
        """
        # Rev. 2024-07-03
        if not draw_markers:
            draw_markers = []

        if not extent_markers:
            extent_markers = []

        self.cvs_hide_markers(draw_markers)

        reference_geom, error_msg = self.tool_get_reference_geom(reference_geom, ref_feature, ref_id, ref_fid)

        if reference_geom:
            x_coords = []
            y_coords = []

            if 'rfl' in draw_markers:
                self.rb_rfl.setToGeometry(reference_geom, self.derived_settings.refLyr)
                self.rb_rfl.show()

            if 'rfl' in extent_markers:
                extent = reference_geom.boundingBox()
                tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                extent = tr.transformBoundingBox(extent)
                x_coords.append(extent.xMinimum())
                x_coords.append(extent.xMaximum())
                y_coords.append(extent.yMinimum())
                y_coords.append(extent.yMaximum())

            if 'snf' in draw_markers or 'snt' in draw_markers or 'enf' in draw_markers or 'ent' in draw_markers or 'snf' in extent_markers or 'snt' in extent_markers or 'enf' in extent_markers or 'ent' in extent_markers:
                # no pre-check, but try & error
                projected_point = reference_geom.interpolate(stationing_n)
                if not projected_point.isEmpty():
                    projected_point.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                    if 'snf' in draw_markers:
                        self.vm_snf.setCenter(projected_point.asPoint())
                        self.vm_snf.show()

                    if 'enf' in draw_markers:
                        self.vm_enf.setCenter(projected_point.asPoint())
                        self.vm_enf.show()

                    if 'snt' in draw_markers:
                        self.vm_snt.setCenter(projected_point.asPoint())
                        self.vm_snt.show()

                    if 'ent' in draw_markers:
                        self.vm_ent.setCenter(projected_point.asPoint())
                        self.vm_ent.show()

                    if 'snf' in extent_markers or 'snt' in extent_markers or 'enf' in extent_markers or 'ent' in extent_markers:
                        x_coords.append(projected_point.asPoint().x())
                        y_coords.append(projected_point.asPoint().y())
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('point_interpolation_failed', stationing_n))

            if extent_markers and extent_mode:
                self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode)
        else:
            self.dlg_append_log_message('WARNING', error_msg)

    def cvs_draw_reference_geom(self, reference_geom: qgis.core.QgsGeometry = None, ref_feature: qgis.core.QgsFeature = None, ref_id: int | str = None, ref_fid: int = None, data_fid: int = None, zoom_to_feature: bool = False):
        """hide/draw(highlight) and optionally zoom to reference-line
        :param reference_geom: geometry queryable via...
        :param ref_feature:
        :param ref_id:
        :param ref_fid:
        :param data_fid:
        :param zoom_to_feature:
        """
        # Rev. 2024-07-03
        self.rb_rfl.hide()

        reference_geom, error_msg = self.tool_get_reference_geom(reference_geom, ref_feature, ref_fid, ref_id, data_fid)

        if reference_geom:
            if zoom_to_feature:
                extent = reference_geom.boundingBox()
                source_crs = self.derived_settings.refLyr.crs()
                target_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
                tr = qgis.core.QgsCoordinateTransform(source_crs, target_crs, qgis.core.QgsProject.instance())
                extent = tr.transformBoundingBox(extent)
                if extent.area() > 0:
                    self.iface.mapCanvas().setExtent(extent)
                    self.iface.mapCanvas().zoomByFactor(1.3)
                else:
                    # hardly possible: Linestring with all points identical
                    self.iface.mapCanvas().setCenter(extent.center())

                self.iface.mapCanvas().refresh()

            self.rb_rfl.setToGeometry(reference_geom, self.derived_settings.refLyr)
            self.rb_rfl.show()
        else:
            # self.dlg_append_log_message('WARNING', error_msg)
            # no log because often called with new inserted and yet incomplete features without reference
            pass

    def ssc_data_layer_stationing_from_field(self) -> None:
        """change stationing_n-field of Data-Layer in QComboBox"""
        # Rev. 2024-07-03
        self.stored_settings.dataLyrStationingFromFieldName = None
        stationing_field = self.my_dialog.qcbn_data_layer_stationing_from_field.currentData()
        if stationing_field:
            self.stored_settings.dataLyrStationingFromFieldName = stationing_field.name()

        self.sys_check_settings()
        self.tool_restart_session()

    def ssc_data_layer_stationing_to_field(self) -> None:
        """change stationing_n-field of Data-Layer in QComboBox"""
        # Rev. 2024-07-03
        self.stored_settings.dataLyrStationingToFieldName = None

        stationing_field = self.my_dialog.qcbn_data_layer_stationing_to_field.currentData()
        if stationing_field:
            self.stored_settings.dataLyrStationingToFieldName = stationing_field.name()

        self.sys_check_settings()
        self.tool_restart_session()

    def scc_lr_mode(self) -> None:
        """changes lr_mode, type of stationing-storage, in QComboBox,
        stored in settings
        affects stationings on update/insert by this plugin
        """
        # Rev. 2024-07-03
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            lr_mode = self.my_dialog.qcb_lr_mode.currentData()
            if lr_mode == 'Mabs' and not self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                # double check: this option only exists, if the layer is M-enabled
                lr_mode = 'Nabs'
                self.dlg_append_log_message('WARNING', MY_DICT.tr('auto_switched_lr_mode'))

            self.stored_settings.lrMode = lr_mode
        # the change of the lrMode makes the previous created/selected showLyr no more suitable => disconnect
        self.stored_settings.showLyrId = None
        self.stored_settings.showLyrBackReferenceFieldName = None
        self.gui_remove_layer_actions()
        self.sys_check_settings()

        self.dlg_refresh_measure_section()
        self.dlg_refresh_qcbn_reference_feature()
        # refresh the list of selectable show-layers
        self.dlg_refresh_layer_settings_section()
        # changed lr_mode requires validation
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_po_pro_section()
        self.cvs_hide_markers()

    def scc_storage_precision(self) -> None:
        """changes storage-precision of Data-Layer in QComboBox,
        stored in settings
        affects stationings on update/insert by this plugin and display-preciosion of some table-widgets
        """
        # Rev. 2024-07-03
        self.stored_settings.storagePrecision = self.my_dialog.qcb_storage_precision.currentData()
        self.dlg_apply_storage_precision()

    def ssc_show_layer_back_reference_field(self) -> None:
        """change Back-Reference-Field of N-Show-Layer in QComboBox"""
        # Rev. 2024-07-03
        self.stored_settings.showLyrBackReferenceFieldName = None
        back_ref_field = self.my_dialog.qcbn_show_layer_back_reference_field.currentData()
        if back_ref_field:
            self.stored_settings.showLyrBackReferenceFieldName = back_ref_field.name()
        self.sys_check_settings()
        self.tool_restart_session()

    def ssc_data_layer_id_field(self) -> None:
        """change ID-field for Data-Layer in QComboBox"""
        # Rev. 2024-07-03
        self.stored_settings.dataLyrIdFieldName = None

        id_field = self.my_dialog.qcbn_data_layer_id_field.currentData()
        if id_field:
            self.stored_settings.dataLyrIdFieldName = id_field.name()

        self.sys_check_settings()
        self.tool_restart_session()

    def cvs_zoom_to_coords(self, x_coords: list, y_coords: list, extent_mode: str, projection: qgis.core.QgsCoordinateReferenceSystem = None):
        """zooms to combined x_coords/y_coords
        if the extent is very small pan to center and zoom in by 0.75
        :param x_coords: list of x-coords, same crs
        :param y_coords: list of y-coords, same crs
        :param extent_mode: zoom/pan
        :param projection: optional projection of the coordinates (f.e. refLyr), if omitted, canvas-crs is assumed
        """
        # Rev. 2024-07-03
        if x_coords and y_coords:
            x_min = min(x_coords)
            y_min = min(y_coords)
            x_max = max(x_coords)
            y_max = max(y_coords)

            unit, zoom_pan_tolerance, display_precision, measure_default_step = tools.MyTools.eval_crs_units(self.iface.mapCanvas().mapSettings().destinationCrs().authid())

            if x_min <= x_max or y_min <= y_max:
                extent = qgis.core.QgsRectangle(x_min, y_min, x_max, y_max)
                if projection:
                    tr = qgis.core.QgsCoordinateTransform(projection, self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                    extent = tr.transformBoundingBox(extent)

                if extent_mode == 'zoom':
                    if extent.width() >= zoom_pan_tolerance and extent.height() >= zoom_pan_tolerance:
                        self.iface.mapCanvas().setExtent(extent)
                        self.iface.mapCanvas().zoomByFactor(1.3)
                    else:
                        # extent is a point => pan and zoom-in
                        self.iface.mapCanvas().setCenter(extent.center())
                        self.iface.mapCanvas().zoomByFactor(0.75)
                elif extent_mode == 'pan':
                    self.iface.mapCanvas().setCenter(extent.center())

                self.iface.mapCanvas().refresh()
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_extent_calculable'))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('no_extent_calculable'))

    def cvs_check_marker_visibility(self, check_markers: list) -> bool:
        """checks the visibility of check_markers
        used for toggle-on/off of points/segments
        :param check_markers: marker-types
        :returns: True => all markers visible False => at least on not visible
        """
        # Rev. 2024-07-03
        all_markers = {
            'snf': self.vm_snf,  # stationing point from
            'snt': self.vm_snt,  # stationing point to
            'enf': self.vm_enf,  # edit point from
            'ent': self.vm_ent,  # edit point to
            'rfl': self.rb_rfl,  # Reference-Line
            'sgn': self.rb_sgn,  # segment-geometry
            'sg0': self.rb_sg0,  # segment-geometry without offset
            'cnf': self.vm_pt_cnf,  # cached point from
            'cnt': self.vm_pt_cnt,  # cached point to
            'csgn': self.rb_csgn,  # cached segment-geometry
            'crfl': self.rb_crfl  # cached Reference-Line
        }

        for check_marker in check_markers:
            if check_marker in all_markers:
                if not all_markers[check_marker].isVisible():
                    # first hidden marker => return
                    return False
            else:
                raise KeyError(f"marker '{check_marker}' not supported")

        # all check_marker visible
        return True

    def cvs_hide_markers(self, hide_markers: list = None):
        """hide temporary graphics
        :param hide_markers: combination of marker-types
        if empty: hide all markers
        """
        # Rev. 2024-07-03
        if not hide_markers:
            hide_markers = ['snf', 'snt', 'sgn', 'sg0', 'rfl', 'enf', 'ent', 'cnf', 'cnt', 'csgn', 'crfl', 'cuca', 'cacu']

        self.rb_selection_rect.hide()

        if 'snf' in hide_markers:
            self.vm_snf.hide()

        if 'snt' in hide_markers:
            self.vm_snt.hide()

        if 'sgn' in hide_markers:
            self.rb_sgn.hide()

        if 'sg0' in hide_markers:
            self.rb_sg0.hide()

        if 'rfl' in hide_markers:
            self.rb_rfl.hide()

        if 'enf' in hide_markers:
            self.vm_enf.hide()

        if 'ent' in hide_markers:
            self.vm_ent.hide()

        if 'cnf' in hide_markers:
            self.vm_pt_cnf.hide()

        if 'cnt' in hide_markers:
            self.vm_pt_cnt.hide()

        if 'csgn' in hide_markers:
            self.rb_csgn.hide()

        if 'crfl' in hide_markers:
            self.rb_crfl.hide()

        if 'cuca' in hide_markers:
            self.rb_rfl_diff_cu.hide()

        if 'cacu' in hide_markers:
            self.rb_rfl_diff_ca.hide()

    def ssc_data_layer_reference_field(self) -> None:
        """change Reference-id-field of Data-Layer-Reference-field in QComboBox
        unsets some follow-up-settings, which possibly don't fit anymore and have to be reconfigured by the user
        """
        # Rev. 2024-07-03
        self.stored_settings.dataLyrReferenceFieldName = None
        ref_id_field = self.my_dialog.qcbn_data_layer_reference_field.currentData()
        if ref_id_field:
            self.stored_settings.dataLyrReferenceFieldName = ref_id_field.name()

        self.sys_check_settings()
        self.tool_restart_session()

    def ssc_data_layer_offset_field(self) -> None:
        """change Reference-id-field of Data-Layer-Reference-field in QComboBox
        unsets some follow-up-settings, which possibly don't fit anymore and have to be reconfigured by the user
        """
        # Rev. 2024-07-03
        self.stored_settings.dataLyrOffsetFieldName = None

        offset_field = self.my_dialog.qcbn_data_layer_offset_field.currentData()
        if offset_field:
            self.stored_settings.dataLyrOffsetFieldName = offset_field.name()

        # ToThink: adapt showLayer-Queries
        self.sys_check_settings()

        self.tool_restart_session()

        if self.derived_settings.showLyr is not None:
            self.derived_settings.showLyr.triggerRepaint()

    def tool_restart_session(self):
        """restart session after configuration changes"""
        # Rev. 2024-07-03
        self.session_data = SessionData()

        # refresh dialog
        self.dlg_clear_measurements()
        self.dlg_refresh_measure_section()
        self.dlg_refresh_feature_selection_section()
        self.dlg_refresh_layer_settings_section()
        self.dlg_refresh_po_pro_section()
        self.dlg_refresh_qcbn_reference_feature()
        self.cvs_hide_markers()

    def ssc_reference_layer(self) -> None:
        """change Reference-Layer in QComboBox
        side-effect: unsets nearly all follow-up-settings, which possibly don't fit anymore and have to be reconfigured by the user"""
        # Rev. 2024-07-03
        self.stored_settings.refLyrId = None
        selected_reference_layer = self.my_dialog.qcbn_reference_layer.currentData()
        if selected_reference_layer:
            self.stored_settings.refLyrId = selected_reference_layer.id()

        # re-create self.system_vs and self.derived_settings
        self.sys_check_settings()

        self.tool_restart_session()

        self.dlg_apply_ref_lyr_crs()

    def sys_connect_reference_layer(self, reference_layer_id: str) -> None:
        """checks and prepares Reference-Layer:
            - re-sets self.stored_settings.refLyrId and self.derived_settings.refLyr
            - connects signals to slots
            - configures and activates canvas-snap-settings for this layer
            - sets some self.session_data dependend on layer-projection (measure_unit, measure_default_step)
        1:1 subroutine called by sys_check_settings
        :param reference_layer_id: if '', None or layer not found or wrong type... the first suitable linestring-layer in project will be selected
        """
        # Rev. 2024-07-03

        self.stored_settings.refLyrId = None
        self.derived_settings.refLyr = None

        # Note: Plugin accepts Multi-Layer-Types, but no Multi-Geometry-Features in these Layers
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
        ]

        # Note: mapLayer can be called with every string or None without exception
        reference_layer = qgis.core.QgsProject.instance().mapLayer(reference_layer_id)

        # convenience for the basic requisite:
        # if not set so far or not suiitable: take the topmost linestring-layer
        # 'virtual' check to exclude Plugins schow-layer
        if not reference_layer or not (reference_layer.isValid() and reference_layer.type() == qgis.core.QgsMapLayerType.VectorLayer and reference_layer.dataProvider().name() != 'virtual' and reference_layer.dataProvider().wkbType() in linestring_wkb_types):
            for cl in qgis.core.QgsProject.instance().mapLayers().values():
                if cl.isValid() and cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().name() != 'virtual' and cl.dataProvider().wkbType() in linestring_wkb_types:
                    reference_layer = cl
                    break

        if reference_layer:
            self.system_vs |= self.SVS.REFERENCE_LAYER_EXISTS

            if reference_layer.crs().isValid():
                self.system_vs |= self.SVS.REFERENCE_LAYER_HAS_VALID_CRS

                linestring_m_types = [
                    qgis.core.QgsWkbTypes.LineStringM,
                    qgis.core.QgsWkbTypes.MultiLineStringM,
                    qgis.core.QgsWkbTypes.LineStringZM,
                    qgis.core.QgsWkbTypes.MultiLineStringZM,
                ]

                linestring_z_types = [
                    qgis.core.QgsWkbTypes.LineStringZ,
                    qgis.core.QgsWkbTypes.MultiLineStringZ,
                    qgis.core.QgsWkbTypes.LineStringZM,
                    qgis.core.QgsWkbTypes.MultiLineStringZM,
                ]

                if reference_layer.type() == qgis.core.QgsMapLayerType.VectorLayer and reference_layer.dataProvider().wkbType() in linestring_wkb_types:

                    self.system_vs |= self.SVS.REFERENCE_LAYER_IS_LINESTRING

                    if reference_layer.dataProvider().wkbType() in linestring_m_types:
                        self.system_vs |= self.SVS.REFERENCE_LAYER_M_ENABLED
                    elif self.stored_settings.lrMode == 'Mabs':
                        self.stored_settings.lrMode = 'Nabs'
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('auto_switched_lr_mode'))

                    if reference_layer.dataProvider().wkbType() in linestring_z_types:
                        self.system_vs |= self.SVS.REFERENCE_LAYER_Z_ENABLED

                    self.stored_settings.refLyrId = reference_layer.id()
                    self.derived_settings.refLyr = reference_layer

                    # new display-string => refresh of dialog-elements
                    self.sys_connect_layer_slot(reference_layer, 'displayExpressionChanged', self.sys_layer_slot)

                    # very often triggered, f.e. additionally on displayExpressionChanged, once for each changed character?
                    # self.sys_connect_layer_slot(reference_layer, 'layerModified',self.sys_layer_slot)

                    # new filter applied => refresh of dialog-elements
                    self.sys_connect_layer_slot(reference_layer, 'subsetStringChanged', self.sys_layer_slot)

                    # edit-session on reference-layer => initialize post-processing
                    self.sys_connect_layer_slot(reference_layer, 'editingStarted', self.sys_layer_slot)

                    # edit-session on reference-layer => finish post-processing
                    self.sys_connect_layer_slot(reference_layer, 'afterCommitChanges', self.sys_layer_slot)

                    # geometry change in reference-layer => perform post-processing
                    self.sys_connect_layer_slot(reference_layer, 'geometryChanged', self.sys_layer_slot)

                    # edit-command on reference-layer ended (feature modified/inserted/deleted) => refresh qcbn_reference_feature
                    self.sys_connect_layer_slot(reference_layer, 'editCommandEnded', self.sys_layer_slot)

                    # edit-session on reference-layer finished, features possibly modified/inserted/deleted (editCommandEnded), committed or rollbacked
                    self.sys_connect_layer_slot(reference_layer, 'editingStopped', self.sys_layer_slot)

                    self.sys_connect_layer_slot(reference_layer, 'crsChanged', self.sys_layer_slot)

                    self.cvs_set_snap_config()

                    self.system_vs |= self.SVS.REFERENCE_LAYER_CONNECTED

                    # check data-layer-privileges
                    if reference_layer.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.AddFeatures:
                        self.system_vs |= self.SVS.REFERENCE_LAYER_INSERT_ENABLED
                    if reference_layer.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.ChangeAttributeValues:
                        self.system_vs |= self.SVS.REFERENCE_LAYER_UPDATE_ENABLED
                    if reference_layer.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.DeleteFeatures:
                        self.system_vs |= self.SVS.REFERENCE_LAYER_DELETE_ENABLED
                    if reference_layer.isEditable():
                        self.system_vs |= self.SVS.REFERENCE_LAYER_EDITABLE
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('ref_lyr_crs_invalid'))

    def cvs_set_snap_config(self):
        """ Configure Snapping for reference-layer
        Note: snapping settings ar stored in project, not in layer
        """
        # Rev. 2024-08-26
        if self.derived_settings.refLyr:
            my_snap_config = qgis.core.QgsProject.instance().snappingConfig()
            # clear all previous settings
            my_snap_config.clearIndividualLayerSettings()
            # enable snapping
            my_snap_config.setEnabled(True)
            # advanced: layer-wise snapping settings
            my_snap_config.setMode(qgis.core.QgsSnappingConfig.AdvancedConfiguration)
            # combination of snapping-modes
            # 10 Pixel to Segment and LineEndpoint (latter prefered and will override Segment-Snap)
            type_flag = qgis.core.Qgis.SnappingTypes(qgis.core.Qgis.SnappingType.Segment | qgis.core.Qgis.SnappingType.LineEndpoint)
            my_snap_config.setIndividualLayerSettings(self.derived_settings.refLyr, qgis.core.QgsSnappingConfig.IndividualLayerSettings(enabled=True, type=type_flag, tolerance=10, units=qgis.core.QgsTolerance.UnitType.Pixels))
            my_snap_config.setIntersectionSnapping(False)
            qgis.core.QgsProject.instance().setSnappingConfig(my_snap_config)

    def sys_connect_layer_slot(self, layer: qgis.core.QgsVectorLayer, conn_signal: str, conn_function: typing.Callable):
        """adds a signal/slot-connection to self.signal_slot_cons (if this connection was not registered before)
        each layer supports many signals, triggered on specific actions, some of them are usefull for the plugin layers (reference/data/show) and connected to slots, f. e. to refresh dialog-elements after inserts/updates/deletes
        so the dialog will be refreshed by any edit-action on the features (update/insert/delete...), even if done outside plugin, f.e. by geometry-edits in reference-layer or stationing-edit in data-layer.
        - Multiple connections of one layer to the same slot have to be avoided
        - On change of layer or plugin-unload these signals have to be disconnected
        => each connection is registered in self.signal_slot_cons (nested dictionary, layer_id > conn_signal > conn_function => conn_id)
        :param layer: layer, for which the connection have to be established and registered
        :param conn_signal: a layer has many connectable signals
        :param conn_function: each signal can be connected to multiple functions, in this plugin its allways self.sys_layer_slot
        """
        # Rev. 2024-07-03
        if not layer.id() in self.signal_slot_cons:
            self.signal_slot_cons.setdefault(layer.id(), {})

        if not conn_signal in self.signal_slot_cons[layer.id()]:
            self.signal_slot_cons[layer.id()].setdefault(conn_signal, {})

        if not conn_function.__name__ in self.signal_slot_cons[layer.id()][conn_signal]:
            signal_obj = getattr(layer, conn_signal)

            # create lamda-function which adds additional informations about the layer and the signal to the conn_function-call

            # default-lambda
            lambda_fn = lambda: conn_function(layer.id(), conn_signal)
            if conn_signal in ['crsChanged', 'subsetStringChanged', 'displayExpressionChanged', 'editingStarted', 'editingStopped', 'editCommandEnded', 'afterCommitChanges', 'dataSourceChanged']:
                # signals returning nothing:
                pass
            elif conn_signal == 'geometryChanged':
                # signal emitted with two parameters: fid and (changed!) geometry
                # see https://api.qgis.org/api/classQgsVectorLayer.html#ae7dfd1c752b251a03800f34763ddc343
                lambda_fn = lambda fid, geometry: conn_function(layer.id(), conn_signal, fid=fid, geometry=geometry)
            elif conn_signal == 'editCommandStarted':
                # Signal emitted when a new edit command has been started.
                # parameter text Description for this edit command
                # see https://api.qgis.org/api/classQgsVectorLayer.html#a29b8775dd9808d134b7fc6da94524bb6
                lambda_fn = lambda text: conn_function(layer.id(), conn_signal, text=text)
            elif conn_signal == 'attributeValueChanged':
                # signal emitted with three parameters: fid, idx (attribute index of the changed attribute) and (changed!) value
                # see https://api.qgis.org/api/classQgsVectorLayer.html#aabc217b0260dce5899d78704cacc32ae
                lambda_fn = lambda fid, idx, value: conn_function(layer.id(), conn_signal, fid=fid, idx=idx, value=value)
            elif conn_signal == 'featureAdded':
                # signal emitted with parameter fid == id of the new feature (negative if inserted to edit-buffer, positive if edit-buffer-feature is committed)
                # see https://api.qgis.org/api/classQgsVectorLayer.html#ac914dd316a4bb50eb432515950583806
                lambda_fn = lambda fid: conn_function(layer.id(), conn_signal, fid=fid)
            elif conn_signal == 'committedFeaturesAdded':
                # Emitted when features are added to the provider if not in transaction mode
                # two parameters: layerId (doubled) and addedFeatures (C: QgsFeatureList Python: list of QgsFeature)
                # see https://api.qgis.org/api/classQgsVectorLayer.html#a069cafd8b1fa33893e930954111ed03a
                lambda_fn = lambda layerId, addedFeatures: conn_function(layer.id(), conn_signal, layerId=layerId, addedFeatures=addedFeatures)
            elif conn_signal == 'featuresDeleted':
                # Emitted when features were deleted on layer or its edit-buffer before commit
                # one parameter: fids => fids of deleted features
                # see https://api.qgis.org/api/classQgsVectorLayer.html#a4afb4e75ec50673f8a09cc89d8246386
                lambda_fn = lambda fids: conn_function(layer.id(), conn_signal, fids=fids)
            elif conn_signal == 'committedAttributeValuesChanges':
                # Emitted when attribute value changes are saved to the provider if not in transaction mode.
                # two parameters:
                # layerId
                # changedAttributesValues (QgsChangedAttributesMap, dictionary with fid as key)
                # see https://api.qgis.org/api/classQgsVectorLayer.html#a81baaf8b545ffdc12f37fe72d99cfc3d
                lambda_fn = lambda layerId, changedAttributesValues: conn_function(layer.id(), conn_signal, layerId=layerId, changedAttributesValues=changedAttributesValues)
            elif conn_signal == 'committedFeaturesRemoved':
                # Emitted when features are deleted from the provider if not in transaction mode.
                # two parameters:
                # layerId
                # deletedFeatureIds (list of ids)
                # see https://api.qgis.org/api/classQgsVectorLayer.html#a520550b45603ed20d593b1050768bd97
                # triggered, if so far buffered delete (handled by featuresDeleted) is committed.
                lambda_fn = lambda layerId, deletedFeatureIds: conn_function(layer.id(), conn_signal, layerId=layerId, deletedFeatureIds=deletedFeatureIds)
            else:
                # lambda_fn = lambda: conn_function(layer.id(), conn_signal)
                raise NotImplementedError(f"conn_signal '{conn_signal}' on Layer '{layer.id()}' not implemented")

            conn_id = signal_obj.connect(lambda_fn)
            self.signal_slot_cons[layer.id()][conn_signal][conn_function.__name__] = conn_id



    def dlg_refresh_po_pro_section(self):
        """Refreshes qtrv_po_pro_selection TreeView
        uses cached reference line and data-features and lists the affected features
        from here the user can show the previous calculated positions and correct the currently stored stationings
        """
        # Rev. 2024-07-03
        remove_icon = QtGui.QIcon(':icons/mIconClearTextHover.svg')
        zoom_selected_icon = QtGui.QIcon(':icons/mIconZoom.svg')
        zoom_ref_feature_icon = QtGui.QIcon(':icons/mIconZoom.svg')
        identify_icon = QtGui.QIcon(':icons/mActionIdentify.svg')
        previous_line_icon = QtGui.QIcon(':icons/previous_line.svg')
        move_feature_icon = QtGui.QIcon(':icons/move_segment.svg')
        move_from_icon = QtGui.QIcon(':icons/move_lol_from.svg')
        move_to_icon = QtGui.QIcon(':icons/move_lol_to.svg')
        delete_icon = QtGui.QIcon(':icons/mActionDeleteSelectedFeatures.svg')

        # checks the cache, removes all invalid, sorts by data_fid
        self.tool_check_po_pro_data_cache()

        if self.my_dialog:
            with (QtCore.QSignalBlocker(self.my_dialog.qtrv_po_pro_selection)):
                with QtCore.QSignalBlocker(self.my_dialog.qtrv_po_pro_selection.selectionModel()):
                    # order settings for later restore
                    old_indicator = self.my_dialog.qtrv_po_pro_selection.header().sortIndicatorSection()
                    old_order = self.my_dialog.qtrv_po_pro_selection.header().sortIndicatorOrder()
                    expanded_ref_fids = []

                    # store previous expanded branches for later restore
                    for rc in range(self.my_dialog.qtrv_po_pro_selection.model().rowCount()):
                        index = self.my_dialog.qtrv_po_pro_selection.model().index(rc, 0)
                        if self.my_dialog.qtrv_po_pro_selection.isExpanded(index):
                            expanded_ref_fids.append(index.data(self.ref_fid_role))

                    self.my_dialog.pbtn_zoom_po_pro.setEnabled(False)
                    self.my_dialog.pbtn_clear_po_pro.setEnabled(False)

                    # remove contents, but keep header
                    self.my_dialog.qtrv_po_pro_selection.model().removeRows(0, self.my_dialog.qtrv_po_pro_selection.model().rowCount())

                    if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:

                        if len(self.session_data.po_pro_data_cache) > 0 and len(self.session_data.po_pro_reference_cache) > 0:

                            data_context = qgis.core.QgsExpressionContext()
                            # Features from Data- and Reference-Layer will show their PK and the evaluated displayExpression
                            data_display_exp = qgis.core.QgsExpression(self.derived_settings.dataLyr.displayExpression())
                            data_display_exp.prepare(data_context)

                            ref_context = qgis.core.QgsExpressionContext()
                            ref_display_exp = qgis.core.QgsExpression(self.derived_settings.refLyr.displayExpression())
                            ref_display_exp.prepare(ref_context)

                            self.my_dialog.pbtn_zoom_po_pro.setEnabled(True)
                            self.my_dialog.pbtn_clear_po_pro.setEnabled(True)

                            # query dataLyr with self.session_data.selected_fids

                            request = qgis.core.QgsFeatureRequest().setFilterFids(list(self.session_data.po_pro_data_cache.keys()))

                            # correct order to iterate without subqueries on data-layer
                            ref_id_clause = qgis.core.QgsFeatureRequest.OrderByClause(self.derived_settings.dataLyrReferenceField.name(), True)
                            from_clause = qgis.core.QgsFeatureRequest.OrderByClause(self.derived_settings.dataLyrStationingFromField.name(), True)
                            to_clause = qgis.core.QgsFeatureRequest.OrderByClause(self.derived_settings.dataLyrStationingToField.name(), True)
                            orderby = qgis.core.QgsFeatureRequest.OrderBy([ref_id_clause, from_clause, to_clause])
                            request.setOrderBy(orderby)

                            root_item = self.my_dialog.qtrv_po_pro_selection.model().invisibleRootItem()
                            last_ref_id = None
                            reference_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                            for data_feature in self.derived_settings.dataLyr.getFeatures(request):
                                fvs = self.tool_check_data_feature(data_feature=data_feature)
                                fvs.check_data_feature_valid()

                                data_fid = data_feature.id()
                                ref_id = data_feature[self.stored_settings.dataLyrReferenceFieldName]
                                if ref_id != last_ref_id:
                                    last_ref_id = ref_id
                                    reference_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                    # erst hinzufügen, sonst reference_item.index().row() == -1 reference_item.index().column == -1
                                    root_item.appendRow(reference_item)

                                    ref_feature, error_msg = self.tool_get_reference_feature(ref_id=ref_id)
                                    if ref_feature:
                                        ref_fid = ref_feature.id()
                                        reference_item.setData(ref_fid, self.custom_sort_role)
                                        reference_item.setData(ref_fid, self.ref_fid_role)
                                        ref_context.setFeature(ref_feature)
                                        display_exp = ref_display_exp.evaluate(ref_context)
                                        if display_exp == ref_fid or isinstance(display_exp,QtCore.QVariant):
                                            reference_item.setText(f"# {ref_id}")
                                        else:
                                            reference_item.setText(f"# {ref_id} {display_exp}")
                                        cell_widget = MyQtWidgets.QTwCellWidget()
                                        qtb = MyQtWidgets.QTwToolButton()

                                        qtb.setIcon(zoom_ref_feature_icon)
                                        qtb.setToolTip(MY_DICT.tr('highlight_reference_feature_qtb_ttp'))
                                        qtb.pressed.connect(self.st_toggle_ref_feature)
                                        qtb.setProperty("ref_fid", ref_fid)

                                        cell_widget.layout().addWidget(qtb)

                                        qtb = MyQtWidgets.QTwToolButton()
                                        qtb.setIcon(identify_icon)
                                        qtb.setToolTip(MY_DICT.tr('show_feature_form_qtb_ttp'))
                                        qtb.pressed.connect(self.st_open_ref_form)
                                        qtb.setProperty("ref_fid", ref_fid)
                                        cell_widget.layout().addWidget(qtb)

                                        qtb = MyQtWidgets.QTwToolButton()
                                        qtb.setIcon(previous_line_icon)
                                        qtb.setToolTip(MY_DICT.tr('show_po_pro_reference_line_diffs'))
                                        qtb.pressed.connect(self.cvs_toggle_reference_line_diffs)
                                        qtb.setProperty("ref_fid", ref_fid)
                                        cell_widget.layout().addWidget(qtb)

                                        self.my_dialog.qtrv_po_pro_selection.setIndexWidget(reference_item.index(), cell_widget)


                                    else:
                                        # folder for false assignments, missing reference-features
                                        # should not happen here, because this refresh is triggered by geometry-edits in reference-layer
                                        reference_item.setText(MY_DICT.tr('unknown_reference_item', ref_id))
                                        reference_item.setToolTip(error_msg)

                                id_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                id_item.setData(data_fid, self.custom_sort_role)
                                id_item.setData(data_fid, self.data_fid_role)
                                data_context.setFeature(data_feature)
                                display_exp = data_display_exp.evaluate(data_context)

                                if display_exp == data_fid or isinstance(display_exp,QtCore.QVariant):
                                    id_item.setText(f"# {data_fid}")
                                else:
                                    id_item.setText(f"# {data_fid} {display_exp}")

                                stationing_from = data_feature[self.stored_settings.dataLyrStationingFromFieldName]
                                from_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                from_item.setData(stationing_from, self.custom_sort_role)
                                from_item.setText(str(stationing_from))
                                from_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                stationing_to = data_feature[self.stored_settings.dataLyrStationingToFieldName]
                                to_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                to_item.setData(stationing_to, self.custom_sort_role)
                                to_item.setText(str(stationing_to))
                                to_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                cached_feature = self.session_data.po_pro_data_cache[data_fid]

                                cached_stationing_from = cached_stationing_to = 0
                                if self.stored_settings.lrMode == 'Nabs':
                                    cached_stationing_from = cached_feature.pol_from.snap_n_abs
                                    cached_stationing_to = cached_feature.pol_to.snap_n_abs
                                elif self.stored_settings.lrMode == 'Nfract':
                                    cached_stationing_from = cached_feature.pol_from.snap_n_fract
                                    cached_stationing_to = cached_feature.pol_to.snap_n_fract
                                elif self.stored_settings.lrMode == 'Mabs':
                                    cached_stationing_from = cached_feature.pol_from.snap_m_abs
                                    cached_stationing_to = cached_feature.pol_to.snap_m_abs

                                cached_from_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                cached_from_item.setData(cached_stationing_from, self.custom_sort_role)
                                cached_from_item.setText(str(cached_stationing_from))
                                cached_from_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                cached_to_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                cached_to_item.setData(cached_stationing_to, self.custom_sort_role)
                                cached_to_item.setText(str(cached_stationing_to))
                                cached_to_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                reference_item.appendRow([id_item, from_item, to_item, cached_from_item, cached_to_item])

                                cell_widget = MyQtWidgets.QTwCellWidget()

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(remove_icon)
                                qtb.setToolTip(MY_DICT.tr('remove_from_selection_qtb_ttp'))
                                qtb.pressed.connect(self.st_remove_from_po_pro_cache)
                                qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setProperty("data_fid", data_fid)
                                qtb.setIcon(identify_icon)
                                qtb.setToolTip(MY_DICT.tr('show_feature_form_qtb_ttp'))
                                qtb.pressed.connect(self.st_open_data_form)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(zoom_selected_icon)
                                qtb.setToolTip(MY_DICT.tr('zoom_to_edit_pk_ttp'))
                                qtb.pressed.connect(self.cvs_toggle_po_pro_markers)
                                qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(move_feature_icon)
                                qtb.setToolTip(MY_DICT.tr('move_feature_qtb_ttp'))
                                qtb.setEnabled(self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                qtb.clicked.connect(self.stm_move_po_pro_feature)
                                qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(delete_icon)
                                qtb.setToolTip(MY_DICT.tr('delete_feature_qtb_ttp'))
                                qtb.pressed.connect(self.st_delete_feature)
                                qtb.setProperty("data_fid", data_fid)
                                qtb.setEnabled((self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_DELETE_ENABLED) in self.system_vs)
                                cell_widget.layout().addWidget(qtb)

                                self.my_dialog.qtrv_po_pro_selection.setIndexWidget(id_item.index(), cell_widget)

                                cell_widget = MyQtWidgets.QTwCellWidget()

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(move_from_icon)
                                qtb.setToolTip(MY_DICT.tr('set_feature_from_point_ttp'))
                                qtb.setEnabled(self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                qtb.clicked.connect(self.stm_set_po_pro_from_point)
                                qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                self.my_dialog.qtrv_po_pro_selection.setIndexWidget(from_item.index(), cell_widget)

                                cell_widget = MyQtWidgets.QTwCellWidget()

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(move_to_icon)
                                qtb.setToolTip(MY_DICT.tr('set_feature_to_point_ttp'))
                                qtb.setEnabled(self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                qtb.clicked.connect(self.stm_set_po_pro_to_point)
                                qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                self.my_dialog.qtrv_po_pro_selection.setIndexWidget(to_item.index(), cell_widget)

                            # restore previous sort-settings
                            self.my_dialog.qtrv_po_pro_selection.sortByColumn(old_indicator, old_order)

                            self.my_dialog.qtrv_po_pro_selection.expandAll()

                            if self.session_data.po_pro_feature:
                                self.dlg_select_po_pro_selection_row(self.session_data.po_pro_feature.data_fid)

    def st_remove_from_po_pro_cache(self):
        """Removes a feature from PostProcessing-po_pro_data_cache"""
        # Rev. 2024-07-03
        self.cvs_hide_markers(['cnf', 'cnt', 'csgn', 'crfl', 'cuca', 'cacu'])
        data_fid = self.sender().property('data_fid')
        self.session_data.po_pro_data_cache.pop(data_fid, None)
        self.dlg_refresh_po_pro_section()

    def sys_refresh_po_pro_reference_cache(self, ref_fid, current_geom):
        """triggered by conn_signal == 'geometryChanged' from reference-layer (before commit)
        validity-check of the changed and the provider-geometry regarding self.stored_settings.lrMode
        :param ref_fid: fid of the reference-feature
        :param current_geom: changed geometry"""
        # Rev. 2024-07-06

        checked_current_geom = None
        checked_provider_geom = None

        feature_request = qgis.core.QgsFeatureRequest(ref_fid)
        # query returns exactly one feature from provider, if it was committed (fid positive)
        # but nothing, if it has not yet been committed (fid negative)
        for ref_feature in self.derived_settings.refLyr.dataProvider().getFeatures(feature_request):
            provider_geom = ref_feature.geometry()
            if self.stored_settings.lrMode == 'Mabs':
                geom_m_valid, error_msg = tools.MyTools.check_geom_m_valid(current_geom)
                if geom_m_valid:
                    checked_current_geom = current_geom
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_po_pro_current_geom_not_m_valid', ref_fid,error_msg))

                geom_m_valid, error_msg = tools.MyTools.check_geom_m_valid(provider_geom)
                if geom_m_valid:
                    checked_provider_geom = provider_geom
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_po_pro_provider_geom_not_m_valid', ref_fid,error_msg))
            else:
                geom_n_valid, error_msg = tools.MyTools.check_geom_n_valid(current_geom)
                if geom_n_valid:
                    checked_current_geom = current_geom
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_po_pro_current_geom_not_n_valid', ref_fid,error_msg))

                geom_n_valid, error_msg = tools.MyTools.check_geom_n_valid(provider_geom)
                if geom_n_valid:
                    checked_provider_geom = provider_geom
                else:
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_po_pro_provider_geom_not_n_valid', ref_fid,error_msg))


        if checked_current_geom and checked_provider_geom:

            # _po_pro_max_ref_feature_count: original geometries are cached in self.session_data.po_pro_reference_cache (dictionary), that can get very large, if f.e. many selected shapes are moved together

            # keep already cached reference-geometries (from previous 'geometryChanged'-events)
            # => only the first version stays in cache
            if not self.session_data.po_pro_reference_cache.get(ref_fid, None):

                if len(self.session_data.po_pro_reference_cache) < self._po_pro_max_ref_feature_count:
                    self.session_data.po_pro_reference_cache[ref_fid] = checked_provider_geom
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('max_num_po_pro_ref_features_exceeded', self._po_pro_max_ref_feature_count))
        else:
            # remove from po_pro_reference_cache, if existing
            self.session_data.po_pro_reference_cache.pop(ref_fid, None)

            # remove all assigned features from self.session_data.po_pro_data_cache
            ref_feature, error_msg = self.tool_get_reference_feature(ref_fid = ref_fid)
            if ref_feature:
                ref_id = ref_feature[self.derived_settings.refLyrIdField.name()]
                get_data_features_request = qgis.core.QgsFeatureRequest()
                get_data_features_request.setFilterExpression(f'"{self.derived_settings.dataLyrReferenceField.name()}" = \'{ref_id}\'')
                data_features = self.derived_settings.dataLyr.getFeatures(get_data_features_request)
                for data_feature in data_features:
                    self.session_data.po_pro_data_cache.pop(data_feature.id(),None)

                self.dlg_refresh_po_pro_section()


    def sys_refresh_po_pro_data_cache(self, keep_cache: bool = True):
        """fills po_pro_data_cache after the reference-layer-geometry-edits were committed:
        Scans session_data.po_pro_reference_cache (cached previous geometrie) and calculates assigned segments on cached (before commit) and current (after commit) reference-geometries
        stores all features with altered segments to self.session_data.po_pro_data_cache
        Note: po_pro_reference_cache is filled by sys_layer_slot via refLyr geometryChanged-signal and cleared by editingStarted-signal
        :param keep_cache:  True => keep self.session_data.po_pro_data_cache with previously cached stationings
                            False => reset self.session_data.po_pro_data_cache and recalculate segments with current stationings
        """
        # Rev. 2024-07-03
        self.cvs_hide_markers(['cnf', 'cnt', 'csgn', 'crfl', 'cuca', 'cacu'])

        if not keep_cache:
            self.session_data.po_pro_data_cache = {}

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            if self.session_data.po_pro_reference_cache:
                # check the cached geometries, store valid ones (cached and current) in checked_reference_cache if there are any assigned LoL-Features
                checked_reference_cache = {}
                # adfc => affected data feature count
                adfc = 0

                for ref_fid in self.session_data.po_pro_reference_cache:
                    # check, if the cached reference-feature still exists in reference-layer

                    ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=ref_fid)
                    if ref_feature:
                        if ref_feature.hasGeometry():
                            current_geom = ref_feature.geometry()
                            cached_geom = self.session_data.po_pro_reference_cache[ref_fid]

                            ref_id = ref_feature[self.derived_settings.refLyrIdField.name()]

                            get_data_features_request = qgis.core.QgsFeatureRequest()
                            get_data_features_request.setFilterExpression(f'"{self.derived_settings.dataLyrReferenceField.name()}" = \'{ref_id}\'')
                            # QgsFeatureIterator
                            data_features = self.derived_settings.dataLyr.getFeatures(get_data_features_request)

                            for data_feature in data_features:
                                stationing_from = data_feature[self.stored_settings.dataLyrStationingFromFieldName]
                                stationing_to = data_feature[self.stored_settings.dataLyrStationingToFieldName]

                                measure_feature = self.tool_create_lol_feature(data_feature.id())

                                cached_feature = measure_feature.__copy__()
                                cached_feature.pol_from = cached_feature.pol_to = None

                                cached_pol_from = PoLFeature()
                                cached_pol_from.set_cached_geom(cached_geom, self.derived_settings.refLyr.crs().authid())
                                cached_pol_from.recalc_by_stationing(stationing_from, self.stored_settings.lrMode)

                                if cached_pol_from.is_valid:
                                    cached_feature.pol_from = cached_pol_from

                                cached_pol_to = PoLFeature()
                                cached_pol_to.set_cached_geom(cached_geom, self.derived_settings.refLyr.crs().authid())
                                cached_pol_to.recalc_by_stationing(stationing_to, self.stored_settings.lrMode)

                                if cached_pol_to.is_valid:
                                    cached_feature.pol_to = cached_pol_to

                                if measure_feature.pol_from.is_valid and measure_feature.pol_to.is_valid and cached_pol_from.is_valid and cached_pol_to.is_valid:
                                    current_segment_geom, segment_error = tools.MyTools.get_segment_geom_n(current_geom, measure_feature.pol_from.snap_n_abs, measure_feature.pol_to.snap_n_abs)

                                    if current_segment_geom:
                                        cached_segment_geom, segment_error = tools.MyTools.get_segment_geom_n(cached_geom, cached_pol_from.snap_n_abs, cached_pol_to.snap_n_abs)

                                        if cached_segment_geom:
                                            if not current_segment_geom.isEmpty() and not cached_segment_geom.isEmpty():
                                                if not current_segment_geom.equals(cached_segment_geom):
                                                    adfc += 1
                                                    if adfc < self._po_pro_max_feature_count:
                                                        self.session_data.po_pro_data_cache[data_feature.id()] = cached_feature
                                                    else:
                                                        self.dlg_append_log_message('INFO', MY_DICT.tr('max_num_po_pro_features_exceeded', self._po_pro_max_feature_count))
                                            else:
                                                # at least one of the segments was empty, should not happen, if pol_from/pol_to was valid
                                                self.dlg_append_log_message('INFO', MY_DICT.tr('empty_po_pro_feature_skipped', data_feature.id()))
                                else:
                                    self.dlg_append_log_message('INFO', MY_DICT.tr('invalid_po_pro_feature_skipped', data_feature.id()))

                        else:
                            self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)




                if not adfc:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('no_po_pro_features_affected'))
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_po_pro_reference_cache'))

    def cvs_toggle_reference_line_diffs(self):
        """shows/hides/zooms the differences cached/current reference-geometry after commit of edits"""
        # Rev. 2024-07-08
        ref_fid = self.sender().property('ref_fid')

        self.rb_csgn.hide()

        markers_visible = self.rb_rfl_diff_cu.isVisible()

        self.rb_rfl_diff_cu.hide()
        self.rb_rfl_diff_ca.hide()

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers() or QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''

        # toggle on:
        if not markers_visible or extent_mode:

            # both geometries required: current from refLyr and cached from po_pro_reference_cache
            current_geom = cached_geom = None
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=ref_fid)
            if reference_geom:
                current_geom = reference_geom
            else:
                self.dlg_append_log_message('WARNING', error_msg)

            if ref_fid in self.session_data.po_pro_reference_cache:
                cached_geom = self.session_data.po_pro_reference_cache[ref_fid]
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('po_pro_cached_reference_feature_missing_or_invalid', reference_fid))

            # note:
            # the condition "not cached_geom.equals(current_geom)" should always be True, else this geometry were not in self.session_data.po_pro_reference_cache
            if current_geom and cached_geom and not cached_geom.equals(current_geom):
                x_coords = []
                y_coords = []
                ca_cu_diff_geom = cached_geom.difference(current_geom)

                if extent_mode:
                    extent = ca_cu_diff_geom.boundingBox()
                    x_coords.append(extent.xMinimum())
                    x_coords.append(extent.xMaximum())
                    y_coords.append(extent.yMinimum())
                    y_coords.append(extent.yMaximum())

                self.rb_rfl_diff_ca.setToGeometry(ca_cu_diff_geom, self.derived_settings.refLyr)

                cu_ca_diff_geom = current_geom.difference(cached_geom)

                if extent_mode:
                    extent = cu_ca_diff_geom.boundingBox()
                    x_coords.append(extent.xMinimum())
                    x_coords.append(extent.xMaximum())
                    y_coords.append(extent.yMinimum())
                    y_coords.append(extent.yMaximum())

                self.rb_rfl_diff_cu.setToGeometry(cu_ca_diff_geom, self.derived_settings.refLyr)

                if extent_mode:
                    self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode, self.derived_settings.refLyr.crs())

    def tool_select_po_pro_feature(self, data_fid: int, draw_markers: list = None, extent_markers: list = None, extent_mode: str = None):
        """checks and sets self.session_data.po_pro_feature
        :param data_fid: fid of po_pro-feature
        :param draw_markers: optional list of marker-types, here additionally for cached geometries: cnf cnt csgn
        :param extent_markers: optional zoom-to markers
        :param extent_mode: zoom/pan
        """
        if not draw_markers:
            draw_markers = []

        if not extent_markers:
            extent_markers = []

        self.session_data.po_pro_feature = None
        if data_fid in self.session_data.po_pro_data_cache:
            po_pro_cached_feature = self.session_data.po_pro_data_cache[data_fid]
            po_pro_feature = self.tool_create_lol_feature(data_fid)
            if po_pro_feature:
                if po_pro_feature.ref_fid in self.session_data.po_pro_reference_cache:
                    reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=po_pro_feature.ref_fid)
                    if reference_geom:
                        self.session_data.po_pro_feature = po_pro_feature
                        self.dlg_select_po_pro_selection_row(data_fid)
                        self.cvs_draw_po_pro_feature(self.session_data.po_pro_feature, draw_markers, extent_markers, extent_mode)
                    else:
                        self.dlg_append_log_message('WARNING', error_msg)
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('po_pro_cached_reference_feature_missing_or_invalid', po_pro_feature.ref_fid))
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('invalid_po_pro_feature_skipped', data_fid))
        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('po_pro_data_feature_not_in_cache', data_fid))

    def gui_refresh(self):
        """complete refresh of all gui-elements"""
        # Rev. 2024-07-08

        # reload language, if settings have changed, affects plugin-messages and dialog-contents
        # Note:
        # MY_DICT global variable initialized above *for this script*
        # occurrences in other scripts, f.e. LinearReference.py for QGis-ToolBar, are not reloaded
        global MY_DICT

        MY_DICT = SQLiteDict()

        # deletes and recreates current dialog
        self.sys_check_settings()
        self.dlg_init()
        self.cvs_apply_style_to_graphics()
        self.cvs_hide_markers()

    def ssc_ref_lyr_id_field(self) -> None:
        """change Reference-Layer-ID-Field in QComboBox
        this can be any unique field, f.e. the usual numerical auto-incrementing fid-field
        """
        # Rev. 2024-07-08

        self.stored_settings.refLyrIdFieldName = None

        ref_lyr_id_field = self.my_dialog.qcbn_ref_lyr_id_field.currentData()
        if ref_lyr_id_field:
            self.stored_settings.refLyrIdFieldName = ref_lyr_id_field.name()

        self.sys_check_settings()

        self.tool_restart_session()

    def ssc_data_layer(self) -> None:
        """change Data-Layer in QComboBox"""
        # Rev. 2024-07-08
        self.stored_settings.dataLyrId = None

        selected_data_layer = self.my_dialog.qcbn_data_layer.currentData()
        if selected_data_layer:
            self.stored_settings.dataLyrId = selected_data_layer.id()

            storage_type = selected_data_layer.dataProvider().storageType()
            if storage_type in ['XLSX', 'ODS']:
                self.dlg_append_log_message('INFO', MY_DICT.tr('office_format_warning'))

            # check data-layer-privileges only for dlg_append_log_message, the check will be repeated on every sys_connect_data_Layer
            caps = selected_data_layer.dataProvider().capabilities()
            caps_result = []
            if not (caps & qgis.core.QgsVectorDataProvider.AddFeatures):
                caps_result.append("AddFeatures")

            if not (caps & qgis.core.QgsVectorDataProvider.DeleteFeatures):
                caps_result.append("DeleteFeatures")

            if not (caps & qgis.core.QgsVectorDataProvider.ChangeAttributeValues):
                caps_result.append("ChangeAttributeValues")

            if caps_result:
                caps_string = ", ".join(caps_result)

                self.dlg_append_log_message('INFO', MY_DICT.tr('missing_capabilities', caps_string))

        self.sys_check_settings()
        self.tool_restart_session()

    def scc_reset_style(self) -> None:
        """Resets the customizable styles to their default-values"""
        # Rev. 2024-07-08
        self.stored_settings.pt_snf_icon_type = StoredSettings()._pt_snf_icon_type
        self.stored_settings.pt_snf_icon_size = StoredSettings()._pt_snf_icon_size
        self.stored_settings.pt_snf_pen_width = StoredSettings()._pt_snf_pen_width
        self.stored_settings.pt_snf_color = StoredSettings()._pt_snf_color
        self.stored_settings.pt_snf_fill_color = StoredSettings()._pt_snf_fill_color

        self.stored_settings.pt_snt_icon_type = StoredSettings()._pt_snt_icon_type
        self.stored_settings.pt_snt_icon_size = StoredSettings()._pt_snt_icon_size
        self.stored_settings.pt_snt_pen_width = StoredSettings()._pt_snt_pen_width
        self.stored_settings.pt_snt_color = StoredSettings()._pt_snt_color
        self.stored_settings.pt_snt_fill_color = StoredSettings()._pt_snt_fill_color

        self.stored_settings.ref_line_style = StoredSettings()._ref_line_style
        self.stored_settings.ref_line_width = StoredSettings()._ref_line_width
        self.stored_settings.ref_line_color = StoredSettings()._ref_line_color

        self.stored_settings.segment_line_style = StoredSettings()._segment_line_style
        self.stored_settings.segment_line_width = StoredSettings()._segment_line_width
        self.stored_settings.segment_line_color = StoredSettings()._segment_line_color

        self.dlg_refresh_style_settings_section()
        self.cvs_apply_style_to_graphics()

    def sys_connect_data_layer(self, data_layer_id: str) -> None:
        """prepares Data-Layer:
        - checks existance and suitability
        - re-sets self.stored_settings.dataLyrId
        - re-sets self.derived_settings.dataLyr
        - connects signals to slots
        :param data_layer_id: id of data-layer
        """
        # Rev. 2024-07-08
        self.stored_settings.dataLyrId = None
        self.derived_settings.dataLyr = None

        data_layer = qgis.core.QgsProject.instance().mapLayer(data_layer_id)

        # check usability
        if data_layer and data_layer.isValid() and data_layer.type() == qgis.core.QgsMapLayerType.VectorLayer and data_layer.dataProvider().name() != 'virtual' and data_layer.dataProvider().wkbType() == qgis.core.QgsWkbTypes.NoGeometry:

            self.system_vs |= self.SVS.DATA_LAYER_EXISTS

            self.stored_settings.dataLyrId = data_layer.id()
            self.derived_settings.dataLyr = data_layer

            self.sys_connect_layer_slot(data_layer, 'displayExpressionChanged', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'attributeValueChanged', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'editCommandStarted', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'editCommandEnded', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'featureAdded', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'editingStarted', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'editingStopped', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'subsetStringChanged', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'committedFeaturesAdded', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'featuresDeleted', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'committedAttributeValuesChanges', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'afterCommitChanges', self.sys_layer_slot)
            self.sys_connect_layer_slot(data_layer, 'committedFeaturesRemoved', self.sys_layer_slot)

            self.system_vs |= self.SVS.DATA_LAYER_CONNECTED

            # check data-layer-privileges
            if data_layer.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.AddFeatures:
                self.system_vs |= self.SVS.DATA_LAYER_INSERT_ENABLED
            if data_layer.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.ChangeAttributeValues:
                self.system_vs |= self.SVS.DATA_LAYER_UPDATE_ENABLED
            if data_layer.dataProvider().capabilities() & qgis.core.QgsVectorDataProvider.DeleteFeatures:
                self.system_vs |= self.SVS.DATA_LAYER_DELETE_ENABLED
            if data_layer.isEditable():
                self.system_vs |= self.SVS.DATA_LAYER_EDITABLE

    def gui_add_layer_actions(self):
        """adds layer-actions to data- and show-layer"""
        # Rev. 2024-07-08
        # remove all existing plugin-created layer-actions from all layers except the current registered plugin-layer
        self.gui_remove_layer_actions()

        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            # force showing of the action-column in attribute-table
            atc = self.derived_settings.dataLyr.attributeTableConfig()
            if not atc.actionWidgetVisible():
                # qgis.core.QgsAttributeTableConfig.ButtonList / qgis.core.QgsAttributeTableConfig.DropDown
                atc.setActionWidgetStyle(qgis.core.QgsAttributeTableConfig.ButtonList)
                atc.setActionWidgetVisible(True)
                self.derived_settings.dataLyr.setAttributeTableConfig(atc)

            action_dict = {action.id(): action for action in self.derived_settings.dataLyr.actions().actions() if action.id() in [self._dataLyr_act_id]}
            if not self._dataLyr_act_id in action_dict:
                data_layer_action = qgis.core.QgsAction(
                    self._dataLyr_act_id,
                    qgis.core.QgsAction.ActionType.GenericPython,  # int 1
                    MY_DICT.tr('fa_highlight_zoom_ttp'),
                    "from LinearReferencing.map_tools.LolEvt import set_lol_edit_fid\nset_lol_edit_fid([%@id%],'[%@layer_id%]')",
                    ':icons/mIconZoom.svg',
                    False,
                    '',
                    {'Feature'},
                    ''
                )
                self.derived_settings.dataLyr.actions().addAction(data_layer_action)

                tools.MyTools.re_open_attribute_tables(self.iface, self.derived_settings.dataLyr)
                tools.MyTools.re_open_feature_forms(self.iface, self.derived_settings.dataLyr)

        # same for Show-Layer, the action-called python-function "set_lol_edit_fid" will regard, from which layer it was triggered
        if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
            atc = self.derived_settings.showLyr.attributeTableConfig()
            if not atc.actionWidgetVisible():
                # qgis.core.QgsAttributeTableConfig.ButtonList / qgis.core.QgsAttributeTableConfig.DropDown
                atc.setActionWidgetStyle(qgis.core.QgsAttributeTableConfig.ButtonList)
                atc.setActionWidgetVisible(True)
                self.derived_settings.showLyr.setAttributeTableConfig(atc)

            action_dict = {action.id(): action for action in self.derived_settings.showLyr.actions().actions() if action.id() in [self._showLyr_act_id]}
            if not self._showLyr_act_id in action_dict:
                show_layer_action = qgis.core.QgsAction(
                    self._showLyr_act_id,
                    qgis.core.QgsAction.ActionType.GenericPython,  # int 1
                    MY_DICT.tr('fa_highlight_zoom_ttp'),
                    "from LinearReferencing.map_tools.LolEvt import set_lol_edit_fid\nset_lol_edit_fid([%@id%],'[%@layer_id%]')",
                    ':icons/mIconZoom.svg',
                    False,
                    '',
                    {'Feature'},
                    ''
                )
                self.derived_settings.showLyr.actions().addAction(show_layer_action)

                tools.MyTools.re_open_attribute_tables(self.iface, self.derived_settings.showLyr)
                tools.MyTools.re_open_feature_forms(self.iface, self.derived_settings.showLyr)

    def gui_remove_layer_actions(self):
        """removes the layer-actions from dataLyr and showLyr"""
        # Rev. 2024-07-08

        if self.derived_settings.dataLyr:
            # iterate through all registered layer-actions
            for action in self.derived_settings.dataLyr.actions().actions():
                # remove the ones belonging to this MapTool
                if action.id() == self._dataLyr_act_id:
                    self.derived_settings.dataLyr.actions().removeAction(action.id())
                    # sadly no automatic refresh after removeAction, attribute-tables and -forms still show the action-icons
                    tools.MyTools.re_open_attribute_tables(self.iface, self.derived_settings.dataLyr)
                    tools.MyTools.re_open_feature_forms(self.iface, self.derived_settings.dataLyr)

        # same procedure for Show-Layer

        if self.derived_settings.showLyr:
            for action in self.derived_settings.showLyr.actions().actions():
                if action.id() == self._showLyr_act_id:
                    self.derived_settings.showLyr.actions().removeAction(action.id())
                    tools.MyTools.re_open_attribute_tables(self.iface, self.derived_settings.showLyr)
                    tools.MyTools.re_open_feature_forms(self.iface, self.derived_settings.showLyr)

    def ssc_show_layer(self) -> None:
        """change Show-Layer in QComboBox, items are filtered to suitable layer-types"""
        # Rev. 2024-07-08
        self.stored_settings.showLyrId = None
        selected_show_layer = self.my_dialog.qcbn_show_layer.currentData()
        if selected_show_layer:
            self.stored_settings.showLyrId = selected_show_layer.id()

        self.sys_check_settings()
        self.tool_restart_session()

    def sys_connect_show_layer(self, show_layer_id: str) -> None:
        """prepares Show-Layer:
        - re-sets self.stored_settings.showLyrId
        - re-sets self.derived_settings.showLyr
        - connects signals to slots
        :param show_layer_id: ID of show-layer
        """
        # Rev. 2024-07-08
        self.stored_settings.showLyrId = None
        self.derived_settings.showLyr = None

        single_line_wkb_types = [
            qgis.core.QgsWkbTypes.LineString25D,
            qgis.core.QgsWkbTypes.LineString,
            qgis.core.QgsWkbTypes.LineStringZ,
            qgis.core.QgsWkbTypes.LineStringM,
            qgis.core.QgsWkbTypes.LineStringZM,
        ]

        show_layer = qgis.core.QgsProject.instance().mapLayer(show_layer_id)

        # no 'virtual'-check, show-layer could be vector-layer on a database-view
        # and show_layer.dataProvider().name() == 'virtual'
        if show_layer and show_layer.isValid() and show_layer.type() == qgis.core.QgsMapLayerType.VectorLayer and show_layer.dataProvider().wkbType() in single_line_wkb_types:

            # only enable fitting virtual layers...
            virtual_check_contents = [
                self.derived_settings.refLyr.id(),
                self.derived_settings.refLyrIdField.name(),
                self.derived_settings.dataLyr.id(),
                self.derived_settings.dataLyrIdField.name(),
                self.derived_settings.dataLyrReferenceField.name(),
                self.derived_settings.dataLyrStationingFromField.name(),
                self.derived_settings.dataLyrStationingToField.name(),
                'ST_OffsetCurve',
                'ST_Line_Substring'
            ]

            if self.stored_settings.lrMode in ['Nabs', 'Nfract']:
                if all(s in show_layer.dataProvider().uri().uri() for s in virtual_check_contents):
                    self.system_vs |= self.SVS.SHOW_LAYER_EXISTS

            elif self.stored_settings.lrMode == 'Mabs':
                virtual_check_contents.append('ST_Line_Locate_Point')
                virtual_check_contents.append('ST_TrajectoryInterpolatePoint')
                if all(s in show_layer.dataProvider().uri().uri() for s in virtual_check_contents):
                    self.system_vs |= self.SVS.SHOW_LAYER_EXISTS

            if self.SVS.SHOW_LAYER_EXISTS in self.system_vs:
                self.stored_settings.showLyrId = show_layer.id()
                self.derived_settings.showLyr = show_layer

                self.sys_connect_layer_slot(show_layer, 'displayExpressionChanged', self.sys_layer_slot)
                self.sys_connect_layer_slot(show_layer, 'subsetStringChanged', self.sys_layer_slot)
                # detect manual edits on virtual query on this layer
                self.sys_connect_layer_slot(show_layer, 'dataSourceChanged', self.sys_layer_slot)
                self.system_vs |= self.SVS.SHOW_LAYER_CONNECTED

    def dlg_refresh_qcbn_reference_feature(self):
        """re-populates the QComboBoxN with the List of Reference-Layer-Features"""
        # Rev. 2024-07-08
        if self.my_dialog:
            self.my_dialog.qcbn_reference_feature.blockSignals(True)
            self.my_dialog.qlbl_selected_reference_layer.clear()
            self.my_dialog.qcbn_reference_feature.clear()

            if self.derived_settings.refLyr:
                self.my_dialog.qlbl_selected_reference_layer.setText(self.derived_settings.refLyr.name() + ' (' + self.derived_settings.refLyr.wkbType().name + ')')
                # and self.stored_settings.lrMode == 'Mabs'
                if self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                    self.my_dialog.qcbn_reference_feature.col_names = ['FID', 'Display-Name', 'Length', 'first-M', 'last-M']
                else:
                    self.my_dialog.qcbn_reference_feature.col_names = ['FID', 'Display-Name', 'Length']

                in_model = QtGui.QStandardItemModel(0, 3)

                ref_context = qgis.core.QgsExpressionContext()
                ref_display_exp = qgis.core.QgsExpression(self.derived_settings.refLyr.displayExpression())
                for ref_feature in self.derived_settings.refLyr.getFeatures():


                    ref_fid = ref_feature.id()

                    items = {}
                    items[0] = QtGui.QStandardItem()
                    items[0].setData(ref_fid, 0)
                    items[0].setData(ref_fid, self.ref_fid_role)

                    items[1] = QtGui.QStandardItem()

                    ref_context.setFeature(ref_feature)
                    display_exp = ref_display_exp.evaluate(ref_context)

                    if display_exp == ref_fid or isinstance(display_exp, QtCore.QVariant):
                        items[1].setText(f"# {ref_fid}")
                    else:
                        items[1].setText(f"{display_exp}")

                    items[2] = QtGui.QStandardItem()
                    items[2].setData(ref_feature.geometry().length(), 0)

                    # and self.stored_settings.lrMode == 'Mabs'
                    if self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:

                        first_vertex_m, last_vertex_m, error_msg = tools.MyTools.get_first_last_vertex_m(ref_feature.geometry())
                        if not error_msg:
                            items[3] = QtGui.QStandardItem()
                            items[3].setData(first_vertex_m, 0)
                            items[4] = QtGui.QStandardItem()
                            items[4].setData(last_vertex_m, 0)
                        geom_m_valid, error_msg = tools.MyTools.check_geom_m_valid(ref_feature.geometry())
                        if not geom_m_valid:
                            for ic in items:
                                items[ic].setForeground(QtGui.QColor('red'))
                                items[ic].setToolTip(MY_DICT.tr('reference_geom_not_m_valid', ref_feature.id(),error_msg))


                    in_model.appendRow(items.values())

                self.my_dialog.qcbn_reference_feature.set_model(in_model)

                if self.session_data.current_ref_fid is not None:
                    self.my_dialog.qcbn_reference_feature.select_by_value(0, self.ref_fid_role, self.session_data.current_ref_fid)

            self.my_dialog.qcbn_reference_feature.blockSignals(False)

    def sys_create_data_layer(self):
        """create a geometry-less GeoPackage-layer for storing the linear-references

        fid-column (auto-incremented integer)
        join-column to reference-layer (type dependend on reference-layer id-field-type)
        numerical columns for from/to stationing and offset

        register this layer for plugin usage
        """
        # Rev. 2024-07-08

        # Note:
        # field-names for the here created sample-data-layer are hard-coded and language independend
        # but the aliases registered below are language dependend
        id_field_name = 'fid'
        reference_field_name = 'reference_id'
        stationing_from_field_name = 'stationing_from'
        stationing_to_field_name = 'stationing_to'
        offset_field_name = 'offset'

        # self.derived_settings.refLyrIdField, necessary because the type of the created Reference-field must fit to the referenced primary-key-field
        if self.SVS.REFERENCE_LAYER_COMPLETE in self.system_vs:
            # file-dialog for the GeoPackage
            dialog = QtWidgets.QFileDialog()
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
            dialog.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, True)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
            dialog.setNameFilter("geoPackage (*.gpkg)")
            dialog.setWindowTitle(MY_DICT.tr('create_data_layer'))
            dialog.setDefaultSuffix("gpkg")
            result = dialog.exec()
            filenames = dialog.selectedFiles()

            if result:
                gpkg_path = filenames[0]

                # already used names in project...
                used_layer_names = [layer.name() for layer_id, layer in qgis.core.QgsProject.instance().mapLayers().items()]
                if os.path.isfile(gpkg_path):
                    # ... and existing GeoPackage
                    used_layer_names += [lyr.GetName() for lyr in osgeo.ogr.Open(gpkg_path)]

                # unique name for the table/layer within project and GeoPackage:
                suggested_table_name = tools.MyTools.get_unique_string(used_layer_names, 'LoL_Data_Layer_{curr_i}', 1)

                table_name, ok = QtWidgets.QInputDialog.getText(
                    None,
                    f"LinearReferencing ({get_debug_pos()})",
                    MY_DICT.tr('name_for_table_in_gpkg'),
                    QtWidgets.QLineEdit.Normal,
                    suggested_table_name
                )
                if not ok or not table_name:
                    return
                elif table_name in used_layer_names:

                    dialog_result = QtWidgets.QMessageBox.question(
                        None,
                        f"LinearReferencing ({get_debug_pos()})",
                        MY_DICT.tr('replace_table_in_gpkg', table_name),
                        buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                        defaultButton=QtWidgets.QMessageBox.Yes
                    )

                    if dialog_result != QtWidgets.QMessageBox.Yes:
                        return

                fields = qgis.core.QgsFields()
                # necessary fields

                # Note 1:
                # "fid" ist the default-name in GPKG for Feature-ID (Primary key, integer, auto-increment)
                # if not listed in the field-list it is automatically created
                # if listed it is automatically used
                # to use any other integer column add 'options.layerOptions = ["FID=any_other_integer_column_name"]'
                # see https://gdal.org/drivers/vector/gpkg.html#layer-creation-options

                # Note 2: since 3.38 new signature for QgsField-constructor, see https://api.qgis.org/api/classQgsField.html
                # The use of QVariant for the field-type is deprecated, QMetaType is used instead
                # https://doc.qt.io/qt-5/qmetatype.html#Type-enum
                # old -> new:
                # QtCore.QVariant.Int -> QtCore.QMetaType.Type.Int
                # QtCore.QVariant.Double -> QtCore.QMetaType.Type.Double
                # QtCore.QVariant.String -> QtCore.QMetaType.Type.QString (!)

                # Note 3: the enum-integer-value seem to be the same, print(QtCore.QVariant.Int, QtCore.QMetaType.Type.Int) => 2 2

                try:
                    # QGis > 3.34
                    fields.append(qgis.core.QgsField(id_field_name, QtCore.QMetaType.Int))
                except Exception as e:
                    # QGis 3.34 LTR
                    fields.append(qgis.core.QgsField(id_field_name, QtCore.QVariant.Int))



                # same type as refLyrIdField
                fields.append(qgis.core.QgsField(reference_field_name, self.derived_settings.refLyrIdField.type()))

                try:
                    fields.append(qgis.core.QgsField(stationing_from_field_name, QtCore.QMetaType.Double))
                except Exception as e:
                    fields.append(qgis.core.QgsField(stationing_from_field_name, QtCore.QVariant.Double))

                try:
                    fields.append(qgis.core.QgsField(stationing_to_field_name, QtCore.QMetaType.Double))
                except Exception as e:
                    fields.append(qgis.core.QgsField(stationing_to_field_name, QtCore.QVariant.Double))

                try:
                    fields.append(qgis.core.QgsField(offset_field_name, QtCore.QMetaType.Double))
                except Exception as e:
                    fields.append(qgis.core.QgsField(offset_field_name, QtCore.QVariant.Double))


                options = qgis.core.QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "gpkg"

                # stupid implementation, but else error "Opening of data source in update mode failed..."
                if not os.path.exists(gpkg_path):
                    options.actionOnExistingFile = qgis.core.QgsVectorFileWriter.CreateOrOverwriteFile
                else:
                    options.actionOnExistingFile = qgis.core.QgsVectorFileWriter.CreateOrOverwriteLayer

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
                # CREATE TABLE "LR_Points_Data_25" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "reference_id" INTEGER, "stationing_n" REAL)
                if writer.hasError() == qgis.core.QgsVectorFileWriter.NoError:
                    # Important:
                    # "del writer" *before* "addVectorLayer"
                    # seems to be necessary, else gpkg exists, but created layer not valid
                    # perhaps layer is physically created after "del writer"?
                    del writer

                    uri = gpkg_path + '|layername=' + table_name
                    data_lyr = self.iface.addVectorLayer(uri, table_name, "ogr")

                    if data_lyr and data_lyr.isValid():

                        # language-dependend aliases for tables and forms
                        data_lyr.setFieldAlias(data_lyr.fields().indexOf(id_field_name), MY_DICT.tr('id_field_alias'))
                        data_lyr.setFieldAlias(data_lyr.fields().indexOf(reference_field_name), MY_DICT.tr('reference_id_field_alias'))
                        data_lyr.setFieldAlias(data_lyr.fields().indexOf(stationing_from_field_name), MY_DICT.tr('stationing_from_field_alias'))
                        data_lyr.setFieldAlias(data_lyr.fields().indexOf(stationing_to_field_name), MY_DICT.tr('stationing_to_field_alias'))
                        data_lyr.setFieldAlias(data_lyr.fields().indexOf(offset_field_name), MY_DICT.tr('offset_field_alias'))

                        # field-constraints only affect the forms, not for inserts from table
                        data_lyr.setFieldConstraint(data_lyr.fields().indexOf(id_field_name), qgis.core.QgsFieldConstraints.Constraint.ConstraintUnique)
                        data_lyr.setFieldConstraint(data_lyr.fields().indexOf(id_field_name), qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                        data_lyr.setFieldConstraint(data_lyr.fields().indexOf(reference_field_name), qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                        data_lyr.setFieldConstraint(data_lyr.fields().indexOf(stationing_from_field_name), qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                        data_lyr.setFieldConstraint(data_lyr.fields().indexOf(stationing_to_field_name), qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)
                        data_lyr.setFieldConstraint(data_lyr.fields().indexOf(offset_field_name), qgis.core.QgsFieldConstraints.Constraint.ConstraintNotNull)

                        # convenience to avoid manual edits:
                        # make field 0, dataLyrIdField/fid, readOnly,
                        # setting is applied to feature-form and attribute-table, but can be changed by user in layer-properties
                        # see  additional check in lsl_data_layer_attribute_value_changed
                        form_config = data_lyr.editFormConfig()
                        form_config.setReadOnly(0, True)
                        data_lyr.setEditFormConfig(form_config)

                        self.stored_settings.dataLyrId = data_lyr.id()
                        self.stored_settings.dataLyrIdFieldName = id_field_name
                        self.stored_settings.dataLyrReferenceFieldName = reference_field_name
                        self.stored_settings.dataLyrStationingFromFieldName = stationing_from_field_name
                        self.stored_settings.dataLyrStationingToFieldName = stationing_to_field_name
                        self.stored_settings.dataLyrOffsetFieldName = offset_field_name

                        self.sys_check_settings()
                        self.dlg_refresh_layer_settings_section()
                        self.dlg_refresh_feature_selection_section()

                        self.dlg_append_log_message('SUCCESS', MY_DICT.tr('data_layer_created', f"{gpkg_path}.{table_name}"))

                        self.sys_create_show_layer()

                        # convenience
                        self.derived_settings.dataLyr.startEditing()
                        self.iface.setActiveLayer(self.derived_settings.dataLyr)

                        self.my_dialog.tbw_central.setCurrentIndex(0)

                    else:
                        # if for example the GeoPackage is exclusively accessed by "DB Browser for SQLite"...
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('error_creating_layer', f"{gpkg_path}.{table_name}", 'created layer not valid'))

                else:
                    # perhaps write-permission?
                    self.dlg_append_log_message('WARNING', MY_DICT.tr('error_creating_layer', f"{gpkg_path}.{table_name}", writer.errorMessage()))
        else:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('reference_layer_missing'))

    def sys_create_show_layer(self):
        """create and register virtual layer combining Data- and Reference-Layer"""
        # Rev. 2024-07-08
        if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
            # unique name for the virtual layer within project,
            # include current lrMode for convenience
            layer_names = [layer.name() for layer in qgis.core.QgsProject.instance().mapLayers().values()]
            template = f"LoL_Show_Layer_{self.stored_settings.lrMode}_{{curr_i}}"
            show_layer_name = tools.MyTools.get_unique_string(layer_names, template, 1)

            show_lyr_sql = "SELECT"
            field_sql_lst = []
            # only the necessary attributes of Data-Layer are included, the other come via join
            # the field-names are taken from the registered data-layer, they must not correspond to the default names used in sys_create_data_layer
            field_sql_lst.append(f" data_lyr.{self.derived_settings.dataLyrIdField.name()}")
            field_sql_lst.append(f" data_lyr.{self.derived_settings.dataLyrReferenceField.name()}")
            field_sql_lst.append(f" data_lyr.{self.derived_settings.dataLyrStationingFromField.name()}")
            field_sql_lst.append(f" data_lyr.{self.derived_settings.dataLyrStationingToField.name()}")
            field_sql_lst.append(f" data_lyr.{self.derived_settings.dataLyrOffsetField.name()}")

            # Geometry-Expression with "special comment" according https://docs.qgis.org/testing/en/docs/user_manual/managing_data_source/create_layers.html#creating-virtual-layers
            # ST_Line_Substring and ST_Locate_Between_Measures require from-stationing <= to_stationing, else no result-geometry
            # N-stationing can be done with multi-linestring-geometries, if geometries are either single-parted or multi-parted but without gaps
            # Note: Shape-files are allways multi-type-layers (with mostly single-type geometries)
            # Note 2: the queries expect from-stationing <= to-stationing, they don't return segment-geometries in the reverse case
            # Note 3: the geometry-constructors need a valid offset => no segments with Null/None/''
            line_geom_alias = 'line_geom_' + self.stored_settings.lrMode
            if self.stored_settings.lrMode == 'Nabs':

                field_sql_lst.append(f"""
                ST_OffsetCurve(
                    ST_Line_Substring(
                        st_linemerge(ref_lyr.geometry), 
                        data_lyr.'{self.derived_settings.dataLyrStationingFromField.name()}'/st_length(st_linemerge(ref_lyr.geometry)),
                        data_lyr.'{self.derived_settings.dataLyrStationingToField.name()}'/st_length(st_linemerge(ref_lyr.geometry))
                    ),
                    data_lyr.'{self.derived_settings.dataLyrOffsetField.name()}'
                ) as {line_geom_alias} /*:linestring:{self.derived_settings.refLyr.crs().postgisSrid()}*/""")
            elif self.stored_settings.lrMode == 'Nfract':
                # same as above, but stationings as fractions of reference-line-length, so no need for "/st_length(st_linemerge(ref_lyr.geometry))"
                field_sql_lst.append(f"""
                ST_OffsetCurve(
                    ST_Line_Substring(
                        ST_LineMerge(ref_lyr.geometry), 
                        data_lyr.'{self.derived_settings.dataLyrStationingFromField.name()}',
                        data_lyr.'{self.derived_settings.dataLyrStationingToField.name()}'
                    ),
                    data_lyr.'{self.derived_settings.dataLyrOffsetField.name()}'
                ) as {line_geom_alias} /*:linestring:{self.derived_settings.refLyr.crs().postgisSrid()}*/""")
            elif self.stored_settings.lrMode == 'Mabs':
                # Uuh... quite complicated!
                # ST_Locate_Between_Measures does not interpolate, thus returning only segments between fitting vertices:
                # ST_OffsetCurve(ST_Locate_Between_Measures(ref_lyr.geometry, data_lyr.'{self.derived_settings.dataLyrStationingFromField.name()}', data_lyr.'{self.derived_settings.dataLyrStationingToField.name()}'),data_lyr.'{self.derived_settings.dataLyrOffsetField.name()}') as line_geom /*:linestring:{self.derived_settings.refLyr.crs().postgisSrid()}*/
                # New logic:
                # 1. ST_TrajectoryInterpolatePoint(geom, measure) => get M-interpolated from/to-points, if the reference-line "IsValidTrajectory" (single-parted with strict ascending M-values)
                # 2. ST_Line_Locate_Point(geom, point) => get N-stationing for these points
                # 3. ST_Line_Substring(geom, N-from-measure, N-to-measure) => get segment for the interpolated points
                # 4. ST_OffsetCurve(geom, offset) => offset the segment from line
                #
                field_sql_lst.append(f"""
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
                ) as {line_geom_alias} /*:linestring:{self.derived_settings.refLyr.crs().postgisSrid()}*/""")

            else:
                raise NotImplementedError(f"lr_mode '{self.stored_settings.lrMode}' not implemented")

            show_lyr_sql += ',\n'.join(field_sql_lst)
            show_lyr_sql += f"\nFROM  '{self.derived_settings.dataLyr.id()}' as data_lyr"
            show_lyr_sql += f"\n  INNER JOIN '{self.derived_settings.refLyr.id()}' as ref_lyr"
            integer_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong]
            if self.derived_settings.dataLyrReferenceField.type() in integer_field_types:
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

            show_lyr = qgis.core.QgsVectorLayer(uri, show_layer_name, "virtual")
            if show_lyr and show_lyr.renderer():

                # Join Data-Layer
                qvl_join_data_lyr = qgis.core.QgsVectorLayerJoinInfo()
                qvl_join_data_lyr.setJoinLayer(self.derived_settings.dataLyr)
                qvl_join_data_lyr.setJoinFieldName(self.derived_settings.dataLyrIdField.name())
                # 1:1 join, using the identical field-name
                self.stored_settings.showLyrBackReferenceFieldName = self.derived_settings.dataLyrIdField.name()
                qvl_join_data_lyr.setTargetFieldName(self.stored_settings.showLyrBackReferenceFieldName)
                qvl_join_data_lyr.setUsingMemoryCache(True)
                show_lyr.addJoin(qvl_join_data_lyr)

                # Join Reference-Layer
                qvl_join_ref_lyr = qgis.core.QgsVectorLayerJoinInfo()
                qvl_join_ref_lyr.setJoinLayer(self.derived_settings.refLyr)
                qvl_join_ref_lyr.setJoinFieldName(self.derived_settings.refLyrIdField.name())
                qvl_join_ref_lyr.setTargetFieldName(self.derived_settings.dataLyrReferenceField.name())
                qvl_join_ref_lyr.setUsingMemoryCache(True)
                show_lyr.addJoin(qvl_join_ref_lyr)

                # convenience: remove joined duplicates, these fields are almost queried in virtual-layer-uri
                # Note: the aliased field-names from data-layer will stay visible, only the joined ones "table-name_field-name" will be hidden
                atc = show_lyr.attributeTableConfig()
                hide_field_names = [
                    self.derived_settings.dataLyrReferenceField.name(),
                    self.derived_settings.dataLyrStationingToField.name(),
                    self.derived_settings.dataLyrOffsetField.name(),
                ]


                columns = atc.columns()
                for column in columns:
                    if column.name in hide_field_names:
                        column.hidden = True

                atc.setColumns(columns)

                show_lyr.setAttributeTableConfig(atc)

                show_lyr.renderer().symbol().setWidthUnit(qgis.core.QgsUnitTypes.RenderUnit.RenderPixels)
                show_lyr.renderer().symbol().setWidth(6)

                show_lyr.renderer().symbol().setColor(QtGui.QColor(self.stored_settings.show_layer_default_line_color))
                show_lyr.renderer().symbol().setOpacity(0.8)

                # additional, should already be done by uri
                show_lyr.setCrs(self.derived_settings.refLyr.crs())

                qgis.core.QgsProject.instance().addMapLayer(show_lyr)

                self.stored_settings.showLyrId = show_lyr.id()

                self.sys_check_settings()
                self.dlg_refresh_layer_settings_section()
                self.dlg_refresh_feature_selection_section()
                self.dlg_append_log_message('SUCCESS', MY_DICT.tr('show_layer_created', show_layer_name))
            else:
                self.dlg_append_log_message('WARNING', MY_DICT.tr('error_creating_virtual_layer'))

        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('reference_or_data_layer_missing'))

    def s_update_stationing(self):
        """
            opens feature-form for edit_feature, replaces reference and stationing(s) with measure_feature
            layer must be editable
            edit_feature and measure_feature existing and measure_feature.is_valid == True
            insert to edit-buffer is done by OK-click on feature-form
            """
        # Rev. 2024-07-08
        # Check: Privileges sufficient and Layer in Edit-Mode

        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_UPDATE_ENABLED) in self.system_vs:
            if self.session_data.edit_feature is not None:
                data_feature, error_msg = self.tool_get_data_feature(data_fid=self.session_data.edit_feature.data_fid)

                if data_feature:

                    if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                        ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.measure_feature.ref_fid)
                        if ref_feature:
                            if ref_feature.hasGeometry():

                                if self.stored_settings.lrMode == 'Mabs':
                                    geom_m_valid, error_msg = tools.MyTools.check_geom_m_valid(ref_feature.geometry())
                                    if not geom_m_valid:
                                        self.dlg_append_log_message('WARNING', MY_DICT.tr('note_reference_geom_not_m_valid', self.session_data.measure_feature.ref_fid,error_msg))
                                else:
                                    if ref_feature.geometry().constGet().partCount() > 1:
                                        self.dlg_append_log_message('WARNING', MY_DICT.tr('note_reference_geom_multi_parted', self.session_data.measure_feature.ref_fid))

                                pol_from = self.session_data.measure_feature.pol_from.__copy__()
                                pol_to = self.session_data.measure_feature.pol_to.__copy__()

                                if pol_from.snap_n_abs > pol_to.snap_n_abs:
                                    # swap from-to-measurements
                                    pol_from, pol_to = pol_to, pol_from
                                    self.dlg_append_log_message('INFO', MY_DICT.tr('from_to_switched'))

                                if self.stored_settings.lrMode == 'Nabs':
                                    stationing_from = pol_from.snap_n_abs
                                    stationing_to = pol_to.snap_n_abs
                                elif self.stored_settings.lrMode == 'Nfract':
                                    stationing_from = pol_from.snap_n_fract
                                    stationing_to = pol_to.snap_n_fract
                                elif self.stored_settings.lrMode == 'Mabs':
                                    stationing_from = pol_from.snap_m_abs
                                    stationing_to = pol_to.snap_m_abs
                                else:
                                    raise NotImplementedError(f"lr_mode '{self.stored_settings.lrMode}' not implemented")

                                offset = self.session_data.current_offset
                                if self.stored_settings.storagePrecision >= 0:
                                    stationing_from = round(stationing_from, self.stored_settings.storagePrecision)
                                    stationing_to = round(stationing_to, self.stored_settings.storagePrecision)
                                    offset = round(offset, self.stored_settings.storagePrecision)

                                # Note: changes of the feature-attributes via feature.setAttribute(...,...) are possible, shown in feature-form, but not committed by click on the OK-Button
                                # instead, the attribute-values have to be changed inside the form via feature_form.attributeForm().changeAttribute(...,...)
                                feature_form = tools.MyTools.get_feature_form(self.iface, self.derived_settings.dataLyr, data_feature, False)

                                feature_form.attributeForm().changeAttribute(self.derived_settings.dataLyrReferenceField.name(), ref_feature[self.derived_settings.refLyrIdField.name()])
                                feature_form.attributeForm().changeAttribute(self.derived_settings.dataLyrOffsetField.name(), offset)
                                feature_form.attributeForm().changeAttribute(self.derived_settings.dataLyrStationingFromField.name(), stationing_from)
                                feature_form.attributeForm().changeAttribute(self.derived_settings.dataLyrStationingToField.name(), stationing_to)

                                feature_form.show()
                            else:
                                self.dlg_append_log_message('WARNING', MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                        else:
                            self.dlg_append_log_message("WARNING", error_msg)
                    else:
                        # should not happen, because the insert-button would be disabled
                        self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))
                else:
                    self.dlg_append_log_message('WARNING', error_msg)
            else:
                # should not happen, because the insert-button would be disabled
                self.dlg_append_log_message('INFO', MY_DICT.tr('no_edit_feature'))
        else:
            # should not happen, because the insert-button would be disabled
            self.dlg_append_log_message('WARNING', MY_DICT.tr('data_layer_not_editable'))

    def s_insert_stationing(self):
        """
            opens feature-form for new feature with reference and stationing(s)
            layer must be editable
            insert to edit-buffer is done by OK-click on feature-form
            """
        # Rev. 2024-07-08
        # Check: Privileges sufficient and Layer in Edit-Mode

        if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_INSERT_ENABLED) in self.system_vs:
            if self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid:
                ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=self.session_data.measure_feature.ref_fid)
                if ref_feature:
                    if ref_feature.hasGeometry():

                        if self.stored_settings.lrMode == 'Mabs':
                            geom_m_valid, error_msg = tools.MyTools.check_geom_m_valid(ref_feature.geometry())
                            if not geom_m_valid:
                                self.dlg_append_log_message('WARNING', MY_DICT.tr('note_reference_geom_not_m_valid', self.session_data.measure_feature.ref_fid,error_msg))
                        else:
                            if ref_feature.geometry().constGet().partCount() > 1:
                                self.dlg_append_log_message('WARNING',MY_DICT.tr('note_reference_geom_multi_parted',self.session_data.measure_feature.ref_fid))

                        pol_from = self.session_data.measure_feature.pol_from.__copy__()
                        pol_to = self.session_data.measure_feature.pol_to.__copy__()

                        if pol_from.snap_n_abs > pol_to.snap_n_abs:
                            # swap from-to-measurements
                            pol_from, pol_to = pol_to, pol_from
                            self.dlg_append_log_message('INFO', MY_DICT.tr('from_to_switched'))

                        if self.stored_settings.lrMode == 'Nabs':
                            stationing_from = pol_from.snap_n_abs
                            stationing_to = pol_to.snap_n_abs
                        elif self.stored_settings.lrMode == 'Nfract':
                            stationing_from = pol_from.snap_n_fract
                            stationing_to = pol_to.snap_n_fract
                        elif self.stored_settings.lrMode == 'Mabs':
                            stationing_from = pol_from.snap_m_abs
                            stationing_to = pol_to.snap_m_abs
                        else:
                            raise NotImplementedError(f"lr_mode '{self.stored_settings.lrMode}' not implemented")

                        offset = self.session_data.current_offset
                        if self.stored_settings.storagePrecision >= 0:
                            stationing_from = round(stationing_from, self.stored_settings.storagePrecision)
                            stationing_to = round(stationing_to, self.stored_settings.storagePrecision)
                            offset = round(offset, self.stored_settings.storagePrecision)

                        data_feature = qgis.core.QgsVectorLayerUtils.createFeature(self.derived_settings.dataLyr)

                        data_feature[self.derived_settings.dataLyrReferenceField.name()] = ref_feature[self.derived_settings.refLyrIdField.name()]
                        data_feature[self.derived_settings.dataLyrOffsetField.name()] = offset
                        data_feature[self.derived_settings.dataLyrStationingFromField.name()] = stationing_from
                        data_feature[self.derived_settings.dataLyrStationingToField.name()] = stationing_to

                        feature_form = tools.MyTools.get_feature_form(self.iface, self.derived_settings.dataLyr, data_feature, True)
                        feature_form.show()
                    else:
                        self.dlg_append_log_message("WARNING", MY_DICT.tr('exc_reference_feature_wo_geom',ref_feature.id()))
                else:
                    self.dlg_append_log_message("WARNING", error_msg)
            else:
                # should not happen, because the insert-button would be disabled
                self.dlg_append_log_message('WARNING', MY_DICT.tr('no_measurement'))
        else:
            # should not happen, because the insert-button would be disabled
            self.dlg_append_log_message('INFO', MY_DICT.tr('data_layer_not_editable'))

    def st_delete_feature(self):
        """delete feature
            called from QTableWidget (Feature-Selection)
            data_fid stored as property in cell-widget
            """
        # Rev. 2024-07-08
        data_fid = self.sender().property('data_fid')

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
        self.tool_select_feature(data_fid, ['snf', 'snt', 'sgn', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)

        if (self.SVS.DATA_LAYER_EXISTS | self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_DELETE_ENABLED) in self.system_vs:
            data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)

            if data_feature:
                dialog_result = QtWidgets.QMessageBox.question(
                    None,
                    f"LinearReferencing ({get_debug_pos()})",
                    MY_DICT.tr('delete_feature', data_fid),
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    defaultButton=QtWidgets.QMessageBox.Yes
                )

                if dialog_result == QtWidgets.QMessageBox.Yes:
                    try:
                        # still inside edit-buffer, no commit
                        self.derived_settings.dataLyr.beginEditCommand("st_delete_feature")
                        self.derived_settings.dataLyr.deleteFeature(data_fid)
                        self.derived_settings.dataLyr.endEditCommand()
                    except Exception as err:
                        self.dlg_append_log_message('WARNING', f"Exception '{err.__class__.__name__}' in {get_debug_pos()}: {err}")
            else:
                self.dlg_append_log_message('INFO', error_msg)

        else:
            self.dlg_append_log_message('INFO', MY_DICT.tr('no_delete_allowed'))

    def st_qtrv_feature_selection_selection_changed(self, selected_items: QtCore.QItemSelection, deselected_items: QtCore.QItemSelection):
        """
        triggered on selectionChange in self.my_dialog.qtrv_feature_selection.selectionModel, f.e. by click on row-header and click inside the table-row
        https://doc.qt.io/qt-5/qitemselectionmodel.html
        https://doc.qt.io/qt-5/qitemselection.html => list of selection ranges
        https://doc.qt.io/qt-5/qitemselectionrange.html
        :param selected_items: list of selection ranges which is selected now
        :param deselected_items: list of selection ranges which was selected before and now is deselected (f.e. by [ctrl]-click)
        """
        # Rev. 2024-07-08
        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''

        if not selected_items:
            # unselect
            self.session_data.edit_feature = None
            self.dlg_refresh_measure_section()
            self.cvs_hide_markers()

        self.my_dialog.qtrv_feature_selection.selectionModel()

        for sel_range in selected_items:
            # QItemSelectionRange
            for index in sel_range.indexes():
                if index.parent().isValid():
                    # index has parent => data-feature
                    index_0 = index.siblingAtColumn(0)
                    data_fid = index_0.data(self.data_fid_role)
                    self.tool_select_feature(data_fid, ['snf', 'snt', 'sgn', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)
                    # break after first selection-range and first item
                    return
                else:
                    # no parent => reference-feature
                    self.session_data.edit_feature = None
                    self.dlg_refresh_measure_section()
                    self.cvs_hide_markers()
                    # break after first selection-range and first item
                    return

    def st_qtrv_feature_selection_double_click(self, index: QtCore.QModelIndex):
        """emitted on double-click on any cell in qtrv_feature_selection-treeview
        because of tree-structure this can be a double-click on a
        level-0-item => reference-feature or
        level-1-item => data-feature
        selects and zooms feature"""
        # Rev. 2024-07-08
        if index.parent().isValid():
            # index has parent => data-feature
            index_0 = index.siblingAtColumn(0)
            data_fid = index_0.data(self.data_fid_role)
            self.tool_select_feature(data_fid, ['snf', 'snt', 'sgn', 'rfl'], ['snf', 'snt', 'sgn'], 'zoom')
        else:
            # no parent => reference-feature, no further action, but the treeview will automatically expand/collapse on double-click
            pass

    def st_qtrv_post_processing_double_click(self, index: QtCore.QModelIndex):
        """emitted on double-click on any cell in qtrv_po_pro_selection-treeview
        => zoom to po-pro-points and hide other po_pro-graphics
        because of tree-structure this can be a double-click on a
        level-0-item => reference-feature or
        level-1-item => data-feature"""
        # Rev. 2024-07-08
        if index.parent().isValid():
            # index has parent => data-feature
            self.cvs_hide_markers()
            index_0 = index.siblingAtColumn(0)
            data_fid = index_0.data(self.data_fid_role)
            self.tool_select_po_pro_feature(data_fid, ['snf', 'snt', 'sgn', 'rfl', 'cnf', 'cnt', 'csgn'], ['snf', 'snt', 'cnf', 'cnt', 'sgn', 'csgn'], 'zoom')
        else:
            # no parent => reference-feature, no further action, but the treeview will automatically expand/collapse on double-click
            pass

    def st_qtrv_po_pro_selection_selection_changed(self, selected_items: QtCore.QItemSelection, deselected_items: QtCore.QItemSelection):
        """
        triggered on selectionChange in self.my_dialog.qtrv_po_pro_selection.selectionModel, f.e. by click on row-header and click inside the table-row
        https://doc.qt.io/qt-5/qitemselectionmodel.html
        https://doc.qt.io/qt-5/qitemselection.html => list of selection ranges
        https://doc.qt.io/qt-5/qitemselectionrange.html
        :param selected_items: list of selection ranges which is selected now
        :param deselected_items: list of selection ranges which was selected before and now is deselected (f.e. by [ctrl]-click)
        """
        # Rev. 2024-07-08
        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''

        for sel_range in selected_items:
            # QItemSelectionRange
            for index in sel_range.indexes():
                if index.parent().isValid():
                    # index has parent => data-feature
                    self.cvs_hide_markers()
                    index_0 = index.siblingAtColumn(0)
                    data_fid = index_0.data(self.data_fid_role)
                    self.tool_select_po_pro_feature(data_fid, ['snf', 'snt', 'sgn', 'rfl', 'cnf', 'cnt', 'csgn'], ['snf', 'snt', 'cnf', 'cnt', 'sgn', 'csgn'], extent_mode)
                    return
                else:
                    # no parent => reference-feature, no further action, but the treeview will automatically expand/collapse on double-click
                    pass

    def cvs_toggle_feature_markers(self):
        """shows/hides/zooms/pans feature on canvas"""
        # Rev. 2024-07-08
        data_fid = self.sender().property('data_fid')

        draw_markers = ['snf', 'snt', 'sgn', 'rfl']
        extent_markers = ['snf', 'snt', 'sgn']

        # is any feature with the same data_fid currently selected?
        already_selected = self.session_data.edit_feature is not None and self.session_data.edit_feature.data_fid == data_fid

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''

        if not already_selected or extent_mode:
            self.tool_select_feature(data_fid, draw_markers, extent_markers, extent_mode)
        else:
            # toggle
            if self.cvs_check_marker_visibility(draw_markers):
                self.cvs_hide_markers()
            else:
                self.cvs_draw_feature(self.session_data.edit_feature, draw_markers, extent_markers, extent_mode)

    def cvs_toggle_po_pro_markers(self):
        """shows/hides/zooms/pans PostProcessing-feature on canvas"""
        # Rev. 2024-07-08
        data_fid = self.sender().property('data_fid')

        draw_markers = ['snf', 'snt', 'sgn', 'cnf', 'cnt', 'csgn', 'rfl']
        extent_markers = ['snf', 'snt', 'sgn', 'cnf', 'cnt', 'csgn']

        # is any feature with the same data_fid currently selected?
        already_selected = self.session_data.po_pro_feature is not None and self.session_data.po_pro_feature.data_fid == data_fid

        extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''

        if not already_selected or extent_mode:
            self.tool_select_po_pro_feature(data_fid, draw_markers, extent_markers, extent_mode)
        else:
            # toggle
            if self.cvs_check_marker_visibility(draw_markers):
                self.cvs_hide_markers()
            else:
                self.cvs_draw_po_pro_feature(self.session_data.edit_feature, draw_markers, extent_markers, extent_mode)



    def sys_restore_settings(self):
        """restores self.stored_settings from qgis.core.QgsProject.instance(), called from __init__"""
        # Rev. 2024-07-08
        self.stored_settings = StoredSettings()
        # read stored settings from project:
        # filter: startswith('_')
        # -> read and set "hidden" properties, not their property-setter/getter/deleter
        property_list = [prop for prop in dir(StoredSettings) if prop.startswith('_') and not prop.startswith('__')]

        for prop_name in property_list:
            key = f"/LolEvt/{prop_name}"
            restored_value, type_conversion_ok = qgis.core.QgsProject.instance().readEntry('LinearReferencing', key)
            if restored_value and type_conversion_ok:
                setattr(self.stored_settings, prop_name, restored_value)

    def sys_set_tool_mode(self,tool_mode: str)->bool:
        """sets self.session_data.tool_mode with simple checks
        :returns: True if the tool_mode could be set, False if something went wrong and the tool_mode could not be set"""
        # switch-back-by-canvas-click-convenience
        self.session_data.previous_tool_mode = self.session_data.tool_mode

        self.iface.mapCanvas().setCursor(QtCore.Qt.ArrowCursor)

        # MapTool has possibly changed, f. e. Pan
        self.iface.mapCanvas().setMapTool(self)

        # Snapping to reference-layer could have been disabled
        self.cvs_set_snap_config()

        if tool_mode not in self.tool_modes:
            self.dlg_append_log_message('WARNING', MY_DICT.tr('tool_mode_not_implemented', tool_mode))
            return False

        if tool_mode in ['set_feature_from_point', 'set_feature_to_point', 'redigitize_feature']:
            if not (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None:
                return False
        if tool_mode in ['move_feature', 'change_feature_offset']:
            # additional check self.session_data.edit_feature.is_valid
            if not (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.edit_feature is not None and self.session_data.edit_feature.is_valid:
                return False
        elif tool_mode in ['select_features']:
            if not self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
                return False
        elif tool_mode in ['measure_segment', 'set_from_point', 'set_to_point']:
            if not self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                return False
        elif tool_mode in ['change_offset', 'move_segment']:
            if not (self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature and self.session_data.measure_feature.is_valid):
                return False
        elif tool_mode in ['set_po_pro_from_point', 'set_po_pro_to_point']:
            if not (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None:
                return False
        elif tool_mode in ['move_po_pro_feature']:
            # additional check self.session_data.po_pro_feature.is_valid
            if not (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_UPDATE_ENABLED | self.SVS.DATA_LAYER_EDITABLE) in self.system_vs and self.session_data.po_pro_feature is not None and self.session_data.po_pro_feature.is_valid:
                return False

        if tool_mode in ['initialized', 'pausing']:
            self.iface.mapCanvas().setCursor(QtCore.Qt.ArrowCursor)
        elif tool_mode in ['select_features']:
            self.iface.mapCanvas().setCursor(qgis.core.QgsApplication.getThemeCursor(qgis.core.QgsApplication.Cursor.Select))
        else:
            # self.iface.mapCanvas().setCursor(QtCore.Qt.CrossCursor)
            # bit smaller than CrossCursor but with hole in the center
            self.iface.mapCanvas().setCursor(qgis.core.QgsApplication.getThemeCursor(qgis.core.QgsApplication.Cursor.CrossHair))

        self.session_data.tool_mode = tool_mode
        self.dlg_show_tool_mode()
        return True

    def sys_check_settings(self):
        """ checks the current configuration, performs multiple tasks:
                - checks self.stored_settings and re-creates self.derived_settings (checks and re-connects all registered layers)
                - checks self.derived_settings and re-creates self.system_vs
            """
        # Rev. 2024-07-08
        self.system_vs = self.SVS.INIT
        self.derived_settings = DerivedSettings()



        # for type-matching-checks of reference/join-Fields:
        # PKs in databases ar normaly type int, but there are four types of integers, which can be mixed
        # all other possible types (propably string...) must match exact
        integer_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong]
        pk_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong, QtCore.QMetaType.QString]
        numeric_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong, QtCore.QMetaType.Double]

        self.sys_connect_reference_layer(self.stored_settings.refLyrId)

        if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            if self.stored_settings.refLyrIdFieldName:
                fnx = self.derived_settings.refLyr.dataProvider().fields().indexOf(self.stored_settings.refLyrIdFieldName)
                if fnx >= 0 and self.derived_settings.refLyr.dataProvider().fields()[fnx].type() in pk_field_types:
                    self.derived_settings.refLyrIdField = self.derived_settings.refLyr.dataProvider().fields()[fnx]
                    self.system_vs |= self.SVS.REFERENCE_LAYER_ID_FIELD_DEFINED

                    self.sys_connect_data_layer(self.stored_settings.dataLyrId)

                    if self.SVS.DATA_LAYER_CONNECTED in self.system_vs:

                        if self.stored_settings.dataLyrIdFieldName:
                            fnx = self.derived_settings.dataLyr.dataProvider().fields().indexOf(self.stored_settings.dataLyrIdFieldName)
                            if fnx >= 0 and self.derived_settings.dataLyr.dataProvider().fields()[fnx].type() in pk_field_types:
                                self.derived_settings.dataLyrIdField = self.derived_settings.dataLyr.dataProvider().fields()[fnx]
                                self.system_vs |= self.SVS.DATA_LAYER_ID_FIELD_DEFINED

                                if self.derived_settings.refLyr and self.derived_settings.refLyrIdField and self.stored_settings.dataLyrReferenceFieldName:
                                    fnx = self.derived_settings.dataLyr.dataProvider().fields().indexOf(self.stored_settings.dataLyrReferenceFieldName)
                                    if fnx >= 0 and (self.derived_settings.refLyrIdField.type() == self.derived_settings.dataLyr.dataProvider().fields()[fnx].type()) or (self.derived_settings.refLyrIdField.type() in integer_field_types and self.derived_settings.dataLyr.dataProvider().fields()[fnx].type() in integer_field_types):
                                        self.derived_settings.dataLyrReferenceField = self.derived_settings.dataLyr.dataProvider().fields()[fnx]
                                        self.system_vs |= self.SVS.DATA_LAYER_REFERENCE_FIELD_DEFINED

                                        if self.stored_settings.dataLyrOffsetFieldName:
                                            fnx = self.derived_settings.dataLyr.dataProvider().fields().indexOf(self.stored_settings.dataLyrOffsetFieldName)
                                            if fnx >= 0 and self.derived_settings.dataLyr.dataProvider().fields()[fnx].type() in numeric_field_types:
                                                self.derived_settings.dataLyrOffsetField = self.derived_settings.dataLyr.dataProvider().fields()[fnx]
                                                self.system_vs |= self.SVS.DATA_LAYER_OFFSET_FIELD_DEFINED

                                                if self.stored_settings.dataLyrStationingFromFieldName:
                                                    fnx = self.derived_settings.dataLyr.dataProvider().fields().indexOf(self.stored_settings.dataLyrStationingFromFieldName)
                                                    if fnx >= 0 and self.derived_settings.dataLyr.dataProvider().fields()[fnx].type() in numeric_field_types:
                                                        self.derived_settings.dataLyrStationingFromField = self.derived_settings.dataLyr.dataProvider().fields()[fnx]
                                                        self.system_vs |= self.SVS.DATA_LAYER_STATIONING_FROM_FIELD_DEFINED

                                                        if self.stored_settings.dataLyrStationingToFieldName:
                                                            fnx = self.derived_settings.dataLyr.dataProvider().fields().indexOf(self.stored_settings.dataLyrStationingToFieldName)
                                                            if fnx >= 0 and self.derived_settings.dataLyr.dataProvider().fields()[fnx].type() in numeric_field_types:
                                                                self.derived_settings.dataLyrStationingToField = self.derived_settings.dataLyr.dataProvider().fields()[fnx]
                                                                self.system_vs |= self.SVS.DATA_LAYER_STATIONING_TO_FIELD_DEFINED

                                                                self.sys_connect_show_layer(self.stored_settings.showLyrId)
                                                                if self.SVS.SHOW_LAYER_CONNECTED in self.system_vs:

                                                                    if self.derived_settings.dataLyrIdField and self.stored_settings.showLyrBackReferenceFieldName:
                                                                        fnx = self.derived_settings.showLyr.dataProvider().fields().indexOf(self.stored_settings.showLyrBackReferenceFieldName)
                                                                        if fnx >= 0 and (self.derived_settings.dataLyrIdField.type() == self.derived_settings.showLyr.dataProvider().fields()[fnx].type()) or (self.derived_settings.dataLyrIdField.type() in integer_field_types and self.derived_settings.showLyr.dataProvider().fields()[fnx].type() in integer_field_types):
                                                                            self.derived_settings.showLyrBackReferenceField = self.derived_settings.showLyr.dataProvider().fields()[fnx]
                                                                            self.system_vs |= self.SVS.SHOW_LAYER_BACK_REFERENCE_FIELD_DEFINED



        self.gui_add_layer_actions()


    def dlg_show_tool_mode(self):
        """show self.session_data.tool_mode in dialog"""
        # Rev. 2024-07-08
        if self.my_dialog:
            # check/uncheck icons showing current tool_mode:
            self.my_dialog.pb_set_from_point.setChecked(self.session_data.tool_mode == 'set_from_point')
            self.my_dialog.pb_set_to_point.setChecked(self.session_data.tool_mode == 'set_to_point')
            self.my_dialog.pb_change_offset.setChecked(self.session_data.tool_mode == 'change_offset')
            self.my_dialog.pbtn_select_features.setChecked(self.session_data.tool_mode == 'select_features')
            self.my_dialog.pb_move_segment.setChecked(self.session_data.tool_mode == 'move_segment')
            self.my_dialog.pbtn_resume_stationing.setChecked(self.session_data.tool_mode == 'measure_segment')

            if self.session_data.tool_mode:
                tool_mode_description = MY_DICT.tr('lol_toolmode_' + self.session_data.tool_mode)

                tool_tip = MY_DICT.tr('tool_mode_tool_tip',self.session_data.tool_mode,tool_mode_description)
                self.my_dialog.pbtn_tool_mode_indicator.setToolTip(tool_tip)

                # status_message = f"Tool-Mode '{self.session_data.tool_mode}' -> {tool_mode_description}"
                # self.dlg_show_status_message('INFO',status_message)

                tool_mode_icon = QtGui.QIcon(':icons/mActionOptions.svg')

                # show same icon in status-bar as in dialog
                if self.session_data.tool_mode == 'initialized':
                    tool_mode_icon = QtGui.QIcon(':icons/mIconSuccess.svg')
                elif self.session_data.tool_mode == 'pausing':
                    # previous_tool_mode = self.session_data.previous_tool_mode
                    tool_mode_icon = QtGui.QIcon(':icons/pause-circle-outline.svg')
                elif self.session_data.tool_mode == 'set_from_point':
                    tool_mode_icon = QtGui.QIcon(':icons/linear_referencing_point.svg')
                elif self.session_data.tool_mode == 'set_to_point':
                    tool_mode_icon = QtGui.QIcon(':icons/linear_referencing_to_point.svg')
                elif self.session_data.tool_mode == 'measure_segment':
                    tool_mode_icon = QtGui.QIcon(':icons/re_digitize_lol.svg')
                elif self.session_data.tool_mode == 'move_segment':
                    tool_mode_icon = QtGui.QIcon(':icons/move_segment.svg')
                elif self.session_data.tool_mode == 'change_offset':
                    tool_mode_icon = QtGui.QIcon(':icons/change_offset.svg')
                elif self.session_data.tool_mode == 'move_feature':
                    tool_mode_icon = QtGui.QIcon(':icons/move_segment.svg')
                elif self.session_data.tool_mode == 'change_feature_offset':
                    tool_mode_icon = QtGui.QIcon(':icons/change_offset.svg')
                elif self.session_data.tool_mode == 'set_feature_from_point':
                    tool_mode_icon = QtGui.QIcon(':icons/move_lol_from.svg')
                elif self.session_data.tool_mode == 'set_feature_to_point':
                    tool_mode_icon = QtGui.QIcon(':icons/move_lol_to.svg')
                elif self.session_data.tool_mode == 'redigitize_feature':
                    tool_mode_icon = QtGui.QIcon(':icons/re_digitize_lol.svg')
                elif self.session_data.tool_mode == 'select_features':
                    tool_mode_icon = QtGui.QIcon(':icons/select_point_features.svg')
                elif self.session_data.tool_mode == 'move_po_pro_feature':
                    tool_mode_icon = QtGui.QIcon(':icons/move_segment.svg')
                elif self.session_data.tool_mode == 'set_po_pro_from_point':
                    tool_mode_icon = QtGui.QIcon(':icons/move_lol_from.svg')
                elif self.session_data.tool_mode == 'set_po_pro_to_point':
                    tool_mode_icon = QtGui.QIcon(':icons/move_lol_to.svg')

                self.my_dialog.pbtn_tool_mode_indicator.setIcon(tool_mode_icon)

    def dlg_show_status_message(self, message_type: str, message_content: str):
        """displays message in self.my_dialog.status_bar
        style status_bar (color, background-color) dependend on message_type
        starts self.my_dialog.status_bar_timer, which will reset style and clear status_bar after xxx Milliseconds dependend on message_type
        :param message_type: INFO/SUCCESS/WARNING/CRITICAL, according to dlg_append_log_message
        :param message_content:
        """
        # Rev. 2024-07-08
        if self.my_dialog:
            self.my_dialog.status_bar.clearMessage()

            duration_ms = 2500
            css = "QStatusBar {background-color: silver; color: black; font-weight: normal;}"
            if message_type == 'INFO':
                duration_ms = 2500
                css = "QStatusBar {background-color: silver; color: black; font-weight: normal;}"
                # self.iface.messageBar().pushMessage('LinearReferencing', message_content, level=qgis.core.Qgis.Info)

            elif message_type == 'SUCCESS':
                duration_ms = 2500
                css = "QStatusBar {background-color: silver; color: green; font-weight: normal;}"
                # self.iface.messageBar().pushMessage('LinearReferencing', message_content, level=qgis.core.Qgis.Success)
            elif message_type == 'WARNING':
                duration_ms = 5000
                css = "QStatusBar {background-color: silver; color: red; font-weight: normal;}"
                # self.iface.messageBar().pushMessage('LinearReferencing', message_content, level=qgis.core.Qgis.Warning, duration=10)
            elif message_type == 'CRITICAL':
                duration_ms = 5000
                css = "QStatusBar {background-color: orange; color: red; font-weight: bolr;}"
                # self.iface.messageBar().pushMessage('LinearReferencing', message_content, level=qgis.core.Qgis.Critical, duration=20)

            self.my_dialog.status_bar.showMessage(message_content, duration_ms)
            self.my_dialog.status_bar.setStyleSheet(css)
            # QtCore.QTimer, timeout connected to my_dialog.reset_status_bar, which will reset style and clear contents
            self.my_dialog.status_bar_timer.start(duration_ms)

    def dlg_refresh_style_settings_section(self):
        """refresh the style-section: symbol-types, colors, line-width, line-style"""
        # Rev. 2024-07-08
        if self.my_dialog:
            block_widgets = [
                self.my_dialog.qcb_pt_snf_icon_type,
                self.my_dialog.qspb_pt_snf_icon_size,
                self.my_dialog.qspb_pt_snf_pen_width,
                self.my_dialog.qpb_pt_snf_color,
                self.my_dialog.qpb_pt_snf_fill_color,

                self.my_dialog.qcb_pt_snt_icon_type,
                self.my_dialog.qspb_pt_snt_icon_size,
                self.my_dialog.qspb_pt_snt_pen_width,
                self.my_dialog.qpb_pt_snt_color,
                self.my_dialog.qpb_pt_snt_fill_color,

                self.my_dialog.qcb_ref_line_style,
                self.my_dialog.qspb_ref_line_width,
                self.my_dialog.qpb_ref_line_color,

                self.my_dialog.qcb_segment_line_style,
                self.my_dialog.qspb_segment_line_width,
                self.my_dialog.qpb_segment_line_color,

            ]

            for widget in block_widgets:
                widget.blockSignals(True)

            tools.MyTools.select_by_value(self.my_dialog.qcb_pt_snf_icon_type, self.stored_settings.pt_snf_icon_type, 0, self.setting_key_role)
            self.my_dialog.qspb_pt_snf_icon_size.setValue(self.stored_settings.pt_snf_icon_size)
            self.my_dialog.qspb_pt_snf_pen_width.setValue(self.stored_settings.pt_snf_pen_width)
            self.my_dialog.qpb_pt_snf_color.set_color(self.stored_settings.pt_snf_color)
            self.my_dialog.qpb_pt_snf_fill_color.set_color(self.stored_settings.pt_snf_fill_color)

            tools.MyTools.select_by_value(self.my_dialog.qcb_pt_snt_icon_type, self.stored_settings.pt_snt_icon_type, 0, self.setting_key_role)
            self.my_dialog.qspb_pt_snt_icon_size.setValue(self.stored_settings.pt_snt_icon_size)
            self.my_dialog.qspb_pt_snt_pen_width.setValue(self.stored_settings.pt_snt_pen_width)
            self.my_dialog.qpb_pt_snt_color.set_color(self.stored_settings.pt_snt_color)
            self.my_dialog.qpb_pt_snt_fill_color.set_color(self.stored_settings.pt_snt_fill_color)

            tools.MyTools.select_by_value(self.my_dialog.qcb_ref_line_style, self.stored_settings.ref_line_style, 0, self.setting_key_role)
            self.my_dialog.qpb_ref_line_color.set_color(self.stored_settings.ref_line_color)
            self.my_dialog.qspb_ref_line_width.setValue(self.stored_settings.ref_line_width)

            tools.MyTools.select_by_value(self.my_dialog.qcb_segment_line_style, self.stored_settings.segment_line_style, 0, self.setting_key_role)
            self.my_dialog.qpb_segment_line_color.set_color(self.stored_settings.segment_line_color)
            self.my_dialog.qspb_segment_line_width.setValue(self.stored_settings.segment_line_width)

            for widget in block_widgets:
                widget.blockSignals(False)

    def dlg_refresh_layer_settings_section(self):
        """refreshes the settings-part in dialog"""
        # Rev. 2024-07-08
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
        ]

        if self.my_dialog:

            block_widgets = [
                self.my_dialog.qcbn_reference_layer,
                self.my_dialog.qcbn_ref_lyr_id_field,
                self.my_dialog.qcbn_data_layer,
                self.my_dialog.qcbn_data_layer_id_field,
                self.my_dialog.qcbn_data_layer_reference_field,
                self.my_dialog.qcbn_data_layer_offset_field,
                self.my_dialog.qcbn_data_layer_stationing_from_field,
                self.my_dialog.qcbn_data_layer_stationing_to_field,
                self.my_dialog.qcb_lr_mode,
                self.my_dialog.qcb_storage_precision,
                self.my_dialog.qcbn_show_layer,
                self.my_dialog.qcbn_show_layer_back_reference_field,

            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                if hasattr(widget, 'clear') and callable(getattr(widget, 'clear')):
                    widget.clear()
                widget.setEnabled(False)

            pk_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong, QtCore.QMetaType.QString]
            integer_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong]
            numeric_field_types = [QtCore.QMetaType.Int, QtCore.QMetaType.UInt, QtCore.QMetaType.LongLong, QtCore.QMetaType.ULongLong, QtCore.QMetaType.Double]

            # refresh Settings Layers and Fields...
            model = QtGui.QStandardItemModel(0, 3)

            for cl in qgis.core.QgsProject.instance().mapLayers().values():
                if cl.isValid():
                    name_item = QtGui.QStandardItem(cl.name())
                    name_item.setData(cl, self.setting_key_role)
                    name_item.setEnabled(isinstance(cl, qgis.core.QgsVectorLayer) and cl.dataProvider().name() != 'virtual' and cl.dataProvider().wkbType() in linestring_wkb_types)
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

            self.my_dialog.qcbn_reference_layer.set_model(model)
            self.my_dialog.qcbn_reference_layer.setEnabled(True)

            if self.derived_settings.refLyr:
                self.my_dialog.qcbn_reference_layer.select_by_value(0, self.setting_key_role, self.derived_settings.refLyr)
                # Reference-Layer is selected, now select the Id-Field
                model = QtGui.QStandardItemModel(0, 3)
                idx = 0
                for field in self.derived_settings.refLyr.dataProvider().fields():
                    name_item = QtGui.QStandardItem(field.name())
                    name_item.setData(field, self.setting_key_role)
                    name_item.setEnabled(field.type() in pk_field_types)
                    # mark PK-Field with green check-icon
                    is_pk_item = QtGui.QStandardItem()
                    # is_pk_item.setTextAlignment(QtCore.Qt.AlignCenter)
                    if idx in self.derived_settings.refLyr.dataProvider().pkAttributeIndexes():
                        # I love UTF...
                        is_pk_item.setText('✔')
                    type_item = QtGui.QStandardItem(field.friendlyTypeString())
                    items = [name_item, type_item, is_pk_item]
                    model.appendRow(items)
                    idx += 1

                self.my_dialog.qcbn_ref_lyr_id_field.set_model(model)
                self.my_dialog.qcbn_ref_lyr_id_field.setEnabled(True)

                if self.derived_settings.refLyrIdField:
                    # QtCore.Qt.ExactMatch doesn't match anything if used for fields, therefore match with role-index 0 (DisplayRole, Text-Content) with the (hopefully unique...) name of the field
                    self.my_dialog.qcbn_ref_lyr_id_field.select_by_value(0, 0, self.derived_settings.refLyrIdField.name())
                    # PK-Field is selected, now the Data-Layer
                    model = QtGui.QStandardItemModel(0, 3)

                    for cl in qgis.core.QgsProject.instance().mapLayers().values():
                        if cl.isValid():
                            name_item = QtGui.QStandardItem(cl.name())
                            name_item.setData(cl, self.setting_key_role)
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

                    self.my_dialog.qcbn_data_layer.set_model(model)
                    self.my_dialog.qcbn_data_layer.setEnabled(True)

                    if self.derived_settings.dataLyr:
                        self.my_dialog.qcbn_data_layer.select_by_value(0, self.setting_key_role, self.derived_settings.dataLyr)

                        # dataLyr set, now the ID-Field

                        idx = 0
                        model = QtGui.QStandardItemModel(0, 3)

                        for field in self.derived_settings.dataLyr.dataProvider().fields():
                            name_item = QtGui.QStandardItem(field.name())
                            name_item.setData(field, self.setting_key_role)
                            name_item.setEnabled(field.type() in pk_field_types)
                            # mark PK-Field with green check-icon
                            is_pk_item = QtGui.QStandardItem()
                            # is_pk_item.setTextAlignment(QtCore.Qt.AlignCenter)
                            if idx in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes():
                                is_pk_item.setText('✔')
                            type_item = QtGui.QStandardItem(field.friendlyTypeString())
                            items = [name_item, type_item, is_pk_item]
                            model.appendRow(items)
                            idx += 1

                        self.my_dialog.qcbn_data_layer_id_field.set_model(model)
                        self.my_dialog.qcbn_data_layer_id_field.setEnabled(True)

                        if self.derived_settings.dataLyrIdField:
                            self.my_dialog.qcbn_data_layer_id_field.select_by_value(0, 0, self.derived_settings.dataLyrIdField.name())
                            # PkField set, now the Reference-Field
                            idx = 0
                            model = QtGui.QStandardItemModel(0, 3)
                            for field in self.derived_settings.dataLyr.dataProvider().fields():
                                name_item = QtGui.QStandardItem(field.name())
                                name_item.setData(field, self.setting_key_role)
                                # must be same type as type refLyrIdField, not ID-Field and not the selected PK-Field
                                name_item.setEnabled(field != self.derived_settings.dataLyrIdField and
                                                     idx not in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes() and
                                                     (
                                                             (self.derived_settings.refLyrIdField.type() in integer_field_types and field.type() in integer_field_types) or
                                                             field.type() == self.derived_settings.refLyrIdField.type()
                                                     )
                                                     )
                                # mark PK-Field with green check-icon
                                is_pk_item = QtGui.QStandardItem()
                                # is_pk_item.setTextAlignment(QtCore.Qt.AlignCenter)
                                if idx in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes():
                                    is_pk_item.setText('✔')
                                type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                items = [name_item, type_item, is_pk_item]
                                model.appendRow(items)
                                idx += 1

                            self.my_dialog.qcbn_data_layer_reference_field.set_model(model)
                            self.my_dialog.qcbn_data_layer_reference_field.setEnabled(True)

                            if self.derived_settings.dataLyrReferenceField:
                                self.my_dialog.qcbn_data_layer_reference_field.select_by_value(0, 0, self.derived_settings.dataLyrReferenceField.name())

                                idx = 0
                                model = QtGui.QStandardItemModel(0, 3)
                                for field in self.derived_settings.dataLyr.dataProvider().fields():
                                    name_item = QtGui.QStandardItem(field.name())
                                    name_item.setData(field, self.setting_key_role)
                                    # must be same type as type refLyrIdField, not ID-Field and not the selected PK-Field
                                    name_item.setEnabled(field != self.derived_settings.dataLyrIdField and
                                                         field.type() in numeric_field_types and
                                                         field != self.derived_settings.dataLyrIdField and
                                                         field != self.derived_settings.dataLyrReferenceField and
                                                         field != self.derived_settings.dataLyrStationingFromField and
                                                         field != self.derived_settings.dataLyrStationingToField and
                                                         idx not in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes()
                                                         )
                                    # mark PK-Field with green check-icon
                                    is_pk_item = QtGui.QStandardItem()
                                    # is_pk_item.setTextAlignment(QtCore.Qt.AlignCenter)
                                    if idx in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes():
                                        is_pk_item.setText('✔')
                                    type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                    items = [name_item, type_item, is_pk_item]
                                    model.appendRow(items)
                                    idx += 1

                                self.my_dialog.qcbn_data_layer_offset_field.set_model(model)
                                self.my_dialog.qcbn_data_layer_offset_field.setEnabled(True)

                                if self.derived_settings.dataLyrOffsetField:
                                    self.my_dialog.qcbn_data_layer_offset_field.select_by_value(0, 0, self.derived_settings.dataLyrOffsetField.name())

                                    idx = 0
                                    model = QtGui.QStandardItemModel(0, 3)
                                    for field in self.derived_settings.dataLyr.dataProvider().fields():
                                        name_item = QtGui.QStandardItem(field.name())
                                        name_item.setData(field, self.setting_key_role)
                                        # numerical, but no PK and not one of the almost selected fields. Can a double-value be used as PK or Reference-key...?
                                        name_item.setEnabled(
                                            field.type() in numeric_field_types and
                                            field != self.derived_settings.dataLyrIdField and
                                            field != self.derived_settings.dataLyrReferenceField and
                                            field != self.derived_settings.dataLyrOffsetField and
                                            field != self.derived_settings.dataLyrStationingToField and
                                            idx not in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes()
                                        )
                                        # mark PK-Field with green check-icon
                                        is_pk_item = QtGui.QStandardItem()
                                        # is_pk_item.setTextAlignment(QtCore.Qt.AlignCenter)
                                        if idx in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes():
                                            is_pk_item.setText('✔')
                                        type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                        items = [name_item, type_item, is_pk_item]
                                        model.appendRow(items)
                                        idx += 1

                                    self.my_dialog.qcbn_data_layer_stationing_from_field.set_model(model)
                                    self.my_dialog.qcbn_data_layer_stationing_from_field.setEnabled(True)

                                    if self.derived_settings.dataLyrStationingFromField:
                                        self.my_dialog.qcbn_data_layer_stationing_from_field.select_by_value(0, 0, self.derived_settings.dataLyrStationingFromField.name())

                                        idx = 0
                                        model = QtGui.QStandardItemModel(0, 3)
                                        for field in self.derived_settings.dataLyr.dataProvider().fields():
                                            name_item = QtGui.QStandardItem(field.name())
                                            name_item.setData(field, self.setting_key_role)
                                            # numerical, but no PK and not one of the almost selected fields. Can a double-value be used as PK or Reference-key...?
                                            name_item.setEnabled(
                                                field.type() in numeric_field_types and
                                                field != self.derived_settings.dataLyrIdField and
                                                field != self.derived_settings.dataLyrReferenceField and
                                                field != self.derived_settings.dataLyrOffsetField and
                                                field != self.derived_settings.dataLyrStationingFromField and
                                                idx not in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes()
                                            )
                                            # mark PK-Field with green check-icon
                                            is_pk_item = QtGui.QStandardItem()
                                            # is_pk_item.setTextAlignment(QtCore.Qt.AlignCenter)
                                            if idx in self.derived_settings.dataLyr.dataProvider().pkAttributeIndexes():
                                                is_pk_item.setText('✔')
                                            type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                            items = [name_item, type_item, is_pk_item]
                                            model.appendRow(items)
                                            idx += 1

                                        self.my_dialog.qcbn_data_layer_stationing_to_field.set_model(model)
                                        self.my_dialog.qcbn_data_layer_stationing_to_field.setEnabled(True)

                                        if self.derived_settings.dataLyrStationingToField:
                                            self.my_dialog.qcbn_data_layer_stationing_to_field.select_by_value(0, 0, self.derived_settings.dataLyrStationingToField.name())

                                            model = QtGui.QStandardItemModel(0, 3)

                                            single_line_wkb_types = [
                                                qgis.core.QgsWkbTypes.LineString25D,
                                                qgis.core.QgsWkbTypes.LineString,
                                                qgis.core.QgsWkbTypes.LineStringZ,
                                                qgis.core.QgsWkbTypes.LineStringM,
                                                qgis.core.QgsWkbTypes.LineStringZM,
                                            ]

                                            for cl in qgis.core.QgsProject.instance().mapLayers().values():
                                                if cl.isValid():
                                                    name_item = QtGui.QStandardItem(cl.name())
                                                    name_item.setData(cl, self.setting_key_role)
                                                    name_item.setEnabled(False)
                                                    if isinstance(cl, qgis.core.QgsVectorLayer) and cl.dataProvider().wkbType() in single_line_wkb_types:
                                                        if cl.dataProvider().name() == 'virtual':
                                                            # only enable fitting virtual layers...
                                                            virtual_check_contents = [
                                                                self.derived_settings.refLyr.id(),
                                                                self.derived_settings.refLyrIdField.name(),
                                                                self.derived_settings.dataLyr.id(),
                                                                self.derived_settings.dataLyrIdField.name(),
                                                                self.derived_settings.dataLyrReferenceField.name(),
                                                                self.derived_settings.dataLyrStationingFromField.name(),
                                                                self.derived_settings.dataLyrStationingToField.name(),
                                                                'ST_OffsetCurve',
                                                                'ST_Line_Substring'
                                                            ]

                                                            if self.stored_settings.lrMode in ['Nabs', 'Nfract']:
                                                                if all(s in cl.dataProvider().uri().uri() for s in virtual_check_contents):
                                                                    name_item.setEnabled(True)
                                                                    name_item.setToolTip(MY_DICT.tr('virtual_layer_fit_ttp'))
                                                                else:
                                                                    name_item.setToolTip(MY_DICT.tr('virtual_layer_no_fit_ttp'))
                                                            elif self.stored_settings.lrMode == 'Mabs':
                                                                virtual_check_contents.append('ST_Line_Locate_Point')
                                                                virtual_check_contents.append('ST_TrajectoryInterpolatePoint')
                                                                if all(s in cl.dataProvider().uri().uri() for s in virtual_check_contents):
                                                                    name_item.setEnabled(True)
                                                                    name_item.setToolTip(MY_DICT.tr('virtual_layer_fit_ttp'))
                                                                else:
                                                                    name_item.setToolTip(MY_DICT.tr('virtual_layer_no_fit_ttp'))

                                                        else:
                                                            # or any layer type vector, Line, non-virtual, because the user
                                                            # might export the slow virtual-layer to file-based layer
                                                            # or use a database-driven view
                                                            # name_item.setEnabled(True)
                                                            pass


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

                                            self.my_dialog.qcbn_show_layer.set_model(model)
                                            self.my_dialog.qcbn_show_layer.setEnabled(True)

                                            if self.derived_settings.showLyr:
                                                self.my_dialog.qcbn_show_layer.select_by_value(0, self.setting_key_role, self.derived_settings.showLyr)

                                                model = QtGui.QStandardItemModel(0, 3)
                                                idx = 0
                                                for field in self.derived_settings.showLyr.dataProvider().fields():
                                                    name_item = QtGui.QStandardItem(field.name())
                                                    name_item.setData(field, self.setting_key_role)
                                                    # numerical, but no PK and not one of the almost selected fields. Can a double-value be used as PK or Reference-key...?
                                                    name_item.setEnabled(
                                                        (self.derived_settings.dataLyrIdField.type() in integer_field_types and field.type() in integer_field_types) or
                                                        field.type() == self.derived_settings.dataLyrIdField.type()
                                                    )
                                                    # mark PK-Field with green check-icon
                                                    is_pk_item = QtGui.QStandardItem()
                                                    # is_pk_item.setTextAlignment(QtCore.Qt.AlignCenter)
                                                    if idx in self.derived_settings.showLyr.dataProvider().pkAttributeIndexes():
                                                        is_pk_item.setText('✔')
                                                    type_item = QtGui.QStandardItem(field.friendlyTypeString())
                                                    items = [name_item, type_item, is_pk_item]
                                                    model.appendRow(items)
                                                    idx += 1

                                                self.my_dialog.qcbn_show_layer_back_reference_field.set_model(model)
                                                self.my_dialog.qcbn_show_layer_back_reference_field.setEnabled(True)

                                                if self.derived_settings.showLyrBackReferenceField:
                                                    self.my_dialog.qcbn_show_layer_back_reference_field.select_by_value(0, 0, self.derived_settings.showLyrBackReferenceField.name())

            if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
                lr_modes = {
                    'Nabs': MY_DICT.tr('lr_mode_n_abs'),
                    'Nfract': MY_DICT.tr('lr_mode_n_fract'),
                }
                if self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                    lr_modes['Mabs'] = MY_DICT.tr('lr_mode_m_abs')

                ic = 0
                for key in lr_modes:
                    self.my_dialog.qcb_lr_mode.addItem(lr_modes[key], key)
                    if key == self.stored_settings.lrMode:
                        self.my_dialog.qcb_lr_mode.setCurrentIndex(ic)
                    ic += 1
                self.my_dialog.qcb_lr_mode.setEnabled(True)

            ic = 0
            # -1 => no rounding
            for prec in range(-1, 9, 1):
                self.my_dialog.qcb_storage_precision.addItem(str(prec), prec)
                if prec == self.stored_settings.storagePrecision:
                    self.my_dialog.qcb_storage_precision.setCurrentIndex(ic)
                ic += 1
            self.my_dialog.qcb_storage_precision.setEnabled(True)

            for widget in block_widgets:
                widget.blockSignals(False)

            self.my_dialog.pb_open_ref_tbl.setEnabled(self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs)
            self.my_dialog.pb_call_ref_disp_exp_dlg.setEnabled(self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs)
            self.my_dialog.pb_open_data_tbl.setEnabled((self.SVS.REFERENCE_LAYER_COMPLETE | self.SVS.DATA_LAYER_EXISTS) in self.system_vs)
            self.my_dialog.pb_open_data_tbl_2.setEnabled((self.SVS.REFERENCE_LAYER_COMPLETE | self.SVS.DATA_LAYER_EXISTS) in self.system_vs)
            self.my_dialog.pb_call_data_disp_exp_dlg.setEnabled((self.SVS.REFERENCE_LAYER_COMPLETE | self.SVS.DATA_LAYER_EXISTS) in self.system_vs)
            self.my_dialog.pbtn_create_data_layer.setEnabled(self.SVS.REFERENCE_LAYER_COMPLETE in self.system_vs)

            self.my_dialog.pb_open_show_tbl.setEnabled(self.SVS.ALL_LAYERS_COMPLETE in self.system_vs)
            self.my_dialog.pb_open_show_tbl_2.setEnabled(self.SVS.ALL_LAYERS_COMPLETE in self.system_vs)
            self.my_dialog.pb_edit_show_layer_display_expression.setEnabled(self.SVS.ALL_LAYERS_COMPLETE in self.system_vs)
            self.my_dialog.pbtn_create_show_layer.setEnabled(self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs)

    def s_change_offset(self, offset: float) -> None:
        """triggered by offset-QDoubleSpinBox, set self.session_data.current_offset, redraws measure_feature with new offset
        :param offset:"""
        # Rev. 2024-07-08
        self.session_data.current_offset = offset
        if self.session_data.measure_feature and self.session_data.measure_feature.is_valid:
            self.session_data.measure_feature.offset = offset
            self.cvs_draw_feature(self.session_data.measure_feature, draw_markers=['snf', 'snt', 'sgn', 'rfl'])

    def dlg_clear_measurements(self):
        """wrapper to clear measure-section: dialog-measure-from-to-delta-widgets"""
        # Rev. 2024-07-08
        self.dlg_clear_from_measurements()
        self.dlg_clear_to_measurements()
        self.dlg_clear_delta_measurements()

    def dlg_clear_from_measurements(self):
        """clear dialog-measure-from-widgets"""
        # Rev. 2024-07-08
        if self.my_dialog:

            block_widgets = [
                self.my_dialog.dnspbx_snap_x_from,
                self.my_dialog.dnspbx_snap_y_from,
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_fract_from,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_fract_from,
                self.my_dialog.dnspbx_z_from
            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                widget.clear()
                widget.blockSignals(False)

    def dlg_unselect_qcbn_reference_feature(self):
        """clears qcbn_reference_feature"""
        # Rev. 2024-07-08
        if self.my_dialog:
            with (QtCore.QSignalBlocker(self.my_dialog.qcbn_reference_feature)):
                self.my_dialog.qcbn_reference_feature.setCurrentIndex(-1)


    def dlg_select_qcbn_reference_feature(self, ref_fid):
        """set and show/clear self.session_data.current_ref_fid in dialog
        see similar s_select_current_ref_fid triggered by indexChange in qcbn_reference_feature"""
        # Rev. 2024-07-08
        self.session_data.current_ref_fid = ref_fid

        if self.my_dialog:
            with (QtCore.QSignalBlocker(self.my_dialog.qcbn_reference_feature)):
                if ref_fid:
                    self.my_dialog.qcbn_reference_feature.select_by_value(0, self.ref_fid_role, ref_fid)
                else:
                    self.my_dialog.qcbn_reference_feature.set_current_index(-1)

            self.dlg_refresh_measure_section()

    def dlg_clear_canvas_coords(self):
        # Rev. 2024-07-08
        if self.my_dialog:
            self.my_dialog.dnspbx_canvas_x.clear()
            self.my_dialog.dnspbx_canvas_y.clear()

    def dlg_clear_to_measurements(self):
        """clear dialog-measure-to-widgets"""
        # Rev. 2024-07-08
        if self.my_dialog:

            block_widgets = [

                self.my_dialog.dnspbx_snap_x_to,
                self.my_dialog.dnspbx_snap_y_to,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_n_fract_to,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_m_fract_to,
                self.my_dialog.dnspbx_z_to
            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                widget.clear()
                widget.blockSignals(False)

    def dlg_clear_delta_measurements(self):
        """clear dialog-measure-delta-widgets"""
        # Rev. 2024-07-08
        if self.my_dialog:

            block_widgets = [
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_n_fract,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dspbx_delta_m_fract,
                self.my_dialog.dnspbx_delta_z_abs
            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                widget.clear()
                widget.blockSignals(False)

    def dlg_refresh_from_measurements(self, pol_from: POL = None):
        """refreshes dialog-measure-from-widgets"""
        # Rev. 2024-07-08
        if self.my_dialog:
            block_widgets = [
                self.my_dialog.dnspbx_snap_x_from,
                self.my_dialog.dnspbx_snap_y_from,
                self.my_dialog.dspbx_n_abs_from,
                self.my_dialog.dspbx_n_fract_from,
                self.my_dialog.dspbx_m_abs_from,
                self.my_dialog.dspbx_m_fract_from,
                self.my_dialog.dnspbx_z_from,
            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                widget.clear()

            if pol_from and pol_from.is_valid:
                self.my_dialog.dnspbx_snap_x_from.setValue(pol_from.snap_x)
                self.my_dialog.dnspbx_snap_y_from.setValue(pol_from.snap_y)
                self.my_dialog.dspbx_n_abs_from.setValue(pol_from.snap_n_abs)
                if isinstance(pol_from.snap_n_fract, numbers.Number):
                    # TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
                    self.my_dialog.dspbx_n_fract_from.setValue(pol_from.snap_n_fract * 100)
                if self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                    if isinstance(pol_from.snap_m_abs, numbers.Number):
                        self.my_dialog.dspbx_m_abs_from.setValue(pol_from.snap_m_abs)
                    if isinstance(pol_from.snap_m_fract, numbers.Number):
                        self.my_dialog.dspbx_m_fract_from.setValue(pol_from.snap_m_fract * 100)
                if self.SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs:
                    if isinstance(pol_from.snap_z_abs, numbers.Number):
                        self.my_dialog.dnspbx_z_from.setValue(pol_from.snap_z_abs)

                self.dlg_select_qcbn_reference_feature(pol_from.ref_fid)

            for widget in block_widgets:
                widget.blockSignals(False)

    def dlg_refresh_to_measurements(self, pol_to: POL = None):
        """refreshes dialog-measure-to-widgets"""
        # Rev. 2024-07-08
        if self.my_dialog:

            block_widgets = [

                self.my_dialog.dnspbx_snap_x_to,
                self.my_dialog.dnspbx_snap_y_to,
                self.my_dialog.dspbx_n_abs_to,
                self.my_dialog.dspbx_n_fract_to,
                self.my_dialog.dspbx_m_abs_to,
                self.my_dialog.dspbx_m_fract_to,
                self.my_dialog.dnspbx_z_to,
            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                widget.clear()

            if pol_to and pol_to.is_valid:
                self.my_dialog.dnspbx_snap_x_to.setValue(pol_to.snap_x)
                self.my_dialog.dnspbx_snap_y_to.setValue(pol_to.snap_y)
                self.my_dialog.dspbx_n_abs_to.setValue(pol_to.snap_n_abs)
                if isinstance(pol_to.snap_n_fract, numbers.Number):
                    # TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
                    self.my_dialog.dspbx_n_fract_to.setValue(pol_to.snap_n_fract * 100)
                if self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                    if isinstance(pol_to.snap_m_abs, numbers.Number):
                        self.my_dialog.dspbx_m_abs_to.setValue(pol_to.snap_m_abs)
                    if isinstance(pol_to.snap_m_fract, numbers.Number):
                        self.my_dialog.dspbx_m_fract_to.setValue(pol_to.snap_m_fract * 100)
                if self.SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs:
                    if isinstance(pol_to.snap_z_abs, numbers.Number):
                        self.my_dialog.dnspbx_z_to.setValue(pol_to.snap_z_abs)

                self.dlg_select_qcbn_reference_feature(pol_to.ref_fid)

            for widget in block_widgets:
                widget.blockSignals(False)

    def dlg_refresh_delta_measurements(self, lol_feature: LoLFeature):
        """refreshes dialog-measure-delta-widgets"""
        # Rev. 2024-07-08
        if lol_feature:
            lol_feature.calculate_delta_measurements()

            block_widgets = [
                self.my_dialog.dspbx_delta_n_abs,
                self.my_dialog.dspbx_delta_n_fract,
                self.my_dialog.dspbx_delta_m_abs,
                self.my_dialog.dspbx_delta_m_fract,
                self.my_dialog.dnspbx_delta_z_abs
            ]

            for widget in block_widgets:
                widget.blockSignals(True)
                widget.clear()

            if isinstance(lol_feature.delta_n_abs, numbers.Number):
                self.my_dialog.dspbx_delta_n_abs.setValue(lol_feature.delta_n_abs)

            if isinstance(lol_feature.delta_n_fract, numbers.Number):
                self.my_dialog.dspbx_delta_n_fract.setValue(lol_feature.delta_n_fract * 100)

            if isinstance(lol_feature.delta_m_abs, numbers.Number):
                self.my_dialog.dspbx_delta_m_abs.setValue(lol_feature.delta_m_abs)

            if isinstance(lol_feature.delta_m_fract, numbers.Number):
                self.my_dialog.dspbx_delta_m_fract.setValue(lol_feature.delta_m_fract * 100)

            if isinstance(lol_feature.delta_z_abs, numbers.Number):
                self.my_dialog.dnspbx_delta_z_abs.setValue(lol_feature.delta_z_abs)

            for widget in block_widgets:
                widget.blockSignals(False)

    def dlg_refresh_measurements(self, lol_feature: LoLFeature):
        """wrapper refreshes dialog-measure-from-to-delta-widgets + offset"""
        # Rev. 2024-07-08
        if self.my_dialog:
            self.dlg_refresh_from_measurements(lol_feature.pol_from)
            self.dlg_refresh_to_measurements(lol_feature.pol_to)
            self.dlg_refresh_delta_measurements(lol_feature)

            # refresh dspbx_offset, also kind of measurement
            # self.session_data.current_offset stays untouched
            if isinstance(lol_feature.offset, numbers.Number):
                with (QtCore.QSignalBlocker(self.my_dialog.dspbx_offset)):
                    self.my_dialog.dspbx_offset.setValue(lol_feature.offset)

            self.dlg_select_qcbn_reference_feature(lol_feature.ref_fid)

    def cvs_draw_from_markers(self, pol_from: POL, draw_markers: list = None, extent_markers: list = None, extent_mode: str = None):
        """draws from-markers
        :param pol_from: From-Point
        :param draw_markers: combination of marker-types, supported here: snf/enf/rfl
        :param extent_markers: combination of marker-types, optional zoom to specific markers
        :param extent_mode: zoom/pan
        """
        # Rev. 2024-07-08
        if not draw_markers:
            draw_markers = []

        if not extent_markers:
            extent_markers = []

        self.cvs_hide_markers(draw_markers)

        # all_markers = {
        #     'snf': self.vm_snf,  # stationing point from
        #     'enf': self.vm_enf,  # edit point from
        #     'rfl': self.rb_rfl,  # Reference-Line
        # }
        #
        # for check_marker in (draw_markers + extent_markers):
        #     if not check_marker in all_markers:
        #         raise KeyError(f"marker '{check_marker}' not supported")

        # min/max coords, projection is canvas-projection
        x_coords = []
        y_coords = []

        if pol_from:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=pol_from.ref_fid)
            if reference_geom:

                if 'rfl' in extent_markers:
                    # rarely used: pan or zoom to relevant reference-geometry
                    extent = reference_geom.boundingBox()
                    tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                    extent = tr.transformBoundingBox(extent)
                    x_coords.append(extent.xMinimum())
                    x_coords.append(extent.xMaximum())
                    y_coords.append(extent.yMinimum())
                    y_coords.append(extent.yMaximum())

                if 'snf' in extent_markers or 'enf' in extent_markers:
                    projected_point_n = reference_geom.interpolate(pol_from.snap_n_abs)
                    if not projected_point_n.isEmpty():
                        projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))
                        x_coords.append(projected_point_n.asPoint().x())
                        y_coords.append(projected_point_n.asPoint().y())

                # first zoom:
                if extent_markers and extent_mode:
                    self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode)

                # than draw:
                if 'snf' in draw_markers or 'enf' in draw_markers:
                    self.cvs_draw_marker_at(pol_from.snap_n_abs, draw_markers=draw_markers, reference_geom=reference_geom)

                # avoid double draw, if allready done by cvs_draw_marker_at
                if 'rfl' in draw_markers and not ('snf' in draw_markers or 'enf' in draw_markers):
                    self.cvs_draw_reference_geom(reference_geom=reference_geom)
            else:
                self.dlg_append_log_message('WARNING', error_msg)

    def cvs_draw_to_markers(self, pol_to: POL, draw_markers: list = None, extent_markers: list = None, extent_mode: str = None):
        """draws to-markers
        :param pol_to: From-Point
        :param draw_markers: combination of marker-types, supported here: snt/ent/rfl
        :param extent_markers: combination of marker-types, optional zoom to specific markers
        :param extent_mode: zoom/pan
        """
        # Rev. 2024-07-08
        if not draw_markers:
            draw_markers = []

        if not extent_markers:
            extent_markers = []

        self.cvs_hide_markers(draw_markers)

        # all_markers = {
        #     'snt': self.vm_snt,  # stationing point to
        #     'ent': self.vm_ent,  # edit point to
        #     'rfl': self.rb_rfl,  # Reference-Line
        # }
        #
        # for check_marker in (draw_markers + extent_markers):
        #     if not check_marker in all_markers:
        #         raise KeyError(f"marker '{check_marker}' not supported")

        # min/max coords, projection is canvas-projection
        x_coords = []
        y_coords = []

        if pol_to:
            reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=pol_to.ref_fid)
            if reference_geom:

                if 'rfl' in extent_markers:
                    # rarely used: pan or zoom to relevant reference-geometry
                    extent = reference_geom.boundingBox()
                    tr = qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance())
                    extent = tr.transformBoundingBox(extent)
                    x_coords.append(extent.xMinimum())
                    x_coords.append(extent.xMaximum())
                    y_coords.append(extent.yMinimum())
                    y_coords.append(extent.yMaximum())

                if 'snt' in extent_markers or 'ent' in extent_markers:
                    projected_point_n = reference_geom.interpolate(pol_to.snap_n_abs)
                    if not projected_point_n.isEmpty():
                        projected_point_n.transform(qgis.core.QgsCoordinateTransform(self.derived_settings.refLyr.crs(), self.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))
                        x_coords.append(projected_point_n.asPoint().x())
                        y_coords.append(projected_point_n.asPoint().y())

                # first zoom:
                if extent_markers and extent_mode:
                    self.cvs_zoom_to_coords(x_coords, y_coords, extent_mode)

                # than draw:
                if 'snt' in draw_markers or 'ent' in draw_markers:
                    self.cvs_draw_marker_at(pol_to.snap_n_abs, draw_markers=draw_markers, reference_geom=reference_geom)

                # avoid double draw, if allready done by cvs_draw_marker_at
                if 'rfl' in draw_markers and not ('snt' in draw_markers or 'ent' in draw_markers):
                    self.cvs_draw_reference_geom(reference_geom=reference_geom)
            else:
                self.dlg_append_log_message('WARNING', error_msg)

    def dlg_refresh_measure_section(self):
        """refresh measurement-section in dialog:
            apply canvas-projection
            select option from qcbn_reference_feature
            enable buttons
            for populate of form-widgets see
            self.dlg_refresh_measurements()
            self.dlg_refresh_qcbn_reference_feature
            """
        # Rev. 2024-07-08
        if self.my_dialog:
            self.my_dialog.pbtn_insert_stationing.setEnabled(False)

            self.my_dialog.qcbn_reference_feature.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dspbx_offset.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)

            self.my_dialog.dnspbx_snap_x_from.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dnspbx_snap_y_from.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dnspbx_snap_x_to.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dnspbx_snap_y_to.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dspbx_n_abs_from.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dspbx_n_abs_to.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dspbx_n_fract_from.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dspbx_n_fract_to.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dspbx_delta_n_abs.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.dspbx_delta_n_fract.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)

            # convenience: show/hide some dialog-areas dependend on reference-layer-geometry-type
            if self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                # only show the toggle-icon itself, the rest (measure-widgets) gets visible after click on that icon
                toggle_widgets = [
                    self.my_dialog.m_abs_grp_hline,
                    self.my_dialog.m_abs_grp_wdg,
                    self.my_dialog.m_fract_grp_hline,
                    self.my_dialog.m_fract_grp_wdg,
                ]
                for wdg in toggle_widgets:
                    wdg.setVisible(True)
            else:
                toggle_widgets = [
                    self.my_dialog.m_abs_grp_hline,
                    self.my_dialog.m_abs_grp_wdg,
                    self.my_dialog.qlbl_m_abs,
                    self.my_dialog.dspbx_m_abs_from,
                    self.my_dialog.dspbx_m_abs_to,
                    self.my_dialog.qlbl_unit_m_abs,
                    self.my_dialog.qlbl_delta_m_abs,
                    self.my_dialog.dspbx_delta_m_abs,
                    self.my_dialog.qlbl_unit_delta_m_abs,
                    self.my_dialog.qlbl_m_abs_valid_hint,

                    self.my_dialog.m_fract_grp_hline,
                    self.my_dialog.m_fract_grp_wdg,
                    self.my_dialog.qlbl_m_fract,
                    self.my_dialog.dspbx_m_fract_from,
                    self.my_dialog.dspbx_m_fract_to,
                    self.my_dialog.qlbl_unit_m_fract,
                    self.my_dialog.qlbl_delta_m_fract,
                    self.my_dialog.dspbx_delta_m_fract,
                    self.my_dialog.qlbl_unit_delta_m_fract,
                    self.my_dialog.qlbl_m_fract_valid_hint,
                ]

                for wdg in toggle_widgets:
                    wdg.setVisible(False)

                self.my_dialog.pb_toggle_m_abs_grp.setIcon(QtGui.QIcon(':icons/plus-box-outline.svg'))
                self.my_dialog.pb_toggle_m_fract_grp.setIcon(QtGui.QIcon(':icons/plus-box-outline.svg'))


            if self.SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs:
                toggle_widgets = [
                    self.my_dialog.z_grp_hline,
                    self.my_dialog.z_grp_wdg
                ]
                for wdg in toggle_widgets:
                    wdg.setVisible(True)
            else:
                toggle_widgets = [
                    self.my_dialog.z_grp_hline,
                    self.my_dialog.z_grp_wdg,
                    self.my_dialog.qlbl_z,
                    self.my_dialog.dnspbx_z_from,
                    self.my_dialog.dnspbx_z_to,
                    self.my_dialog.qlbl_z_unit,
                    self.my_dialog.qlbl_delta_z,
                    self.my_dialog.dnspbx_delta_z_abs,
                    self.my_dialog.qlbl_delta_z_unit
                ]
                self.my_dialog.pb_toggle_z_grp.setIcon(QtGui.QIcon(':icons/plus-box-outline.svg'))
                for wdg in toggle_widgets:
                    wdg.setVisible(False)


            self.my_dialog.pb_set_from_point.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)
            self.my_dialog.pb_set_to_point.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)

            self.my_dialog.tbtn_move_start.setEnabled(False)
            self.my_dialog.tbtn_move_down.setEnabled(False)
            self.my_dialog.tbtn_move_up.setEnabled(False)
            self.my_dialog.tbtn_flip_up.setEnabled(False)
            self.my_dialog.tbtn_move_end.setEnabled(False)
            self.my_dialog.tbtn_flip_down.setEnabled(False)
            self.my_dialog.pb_zoom_to_stationings.setEnabled(False)
            self.my_dialog.pb_move_segment.setEnabled(False)
            self.my_dialog.pb_change_offset.setEnabled(False)

            self.my_dialog.pbtn_resume_stationing.setEnabled(self.SVS.REFERENCE_LAYER_USABLE in self.system_vs)

            self.my_dialog.pbtn_insert_stationing.setEnabled((self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_INSERT_ENABLED) in self.system_vs and self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid)

            # and self.session_data.edit_feature.is_valid

            if (self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE | self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_UPDATE_ENABLED) in self.system_vs and self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid and self.session_data.edit_feature is not None:
                self.my_dialog.pbtn_update_stationing.setEnabled(True)
                self.my_dialog.pbtn_update_stationing.setText(MY_DICT.tr('update_selected_pbtxt', self.session_data.edit_feature.data_fid))
            else:
                self.my_dialog.pbtn_update_stationing.setEnabled(False)
                self.my_dialog.pbtn_update_stationing.setText(MY_DICT.tr('update_blank_pbtxt'))

            enable_pausing_widgets = self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.measure_feature is not None and self.session_data.measure_feature.is_valid

            self.my_dialog.tbtn_move_start.setEnabled(enable_pausing_widgets)
            self.my_dialog.tbtn_move_down.setEnabled(enable_pausing_widgets)
            self.my_dialog.tbtn_move_up.setEnabled(enable_pausing_widgets)
            self.my_dialog.tbtn_move_end.setEnabled(enable_pausing_widgets)
            self.my_dialog.tbtn_flip_up.setEnabled(enable_pausing_widgets)
            self.my_dialog.tbtn_flip_down.setEnabled(enable_pausing_widgets)

            self.my_dialog.pb_move_segment.setEnabled(enable_pausing_widgets)
            self.my_dialog.pb_change_offset.setEnabled(enable_pausing_widgets)

            self.my_dialog.dspbx_delta_n_abs.setEnabled(enable_pausing_widgets)
            self.my_dialog.dspbx_delta_n_fract.setEnabled(enable_pausing_widgets)

            self.my_dialog.dnspbx_delta_z_abs.setEnabled(enable_pausing_widgets and (self.SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs))

            enable_stationing_widgets = self.SVS.REFERENCE_LAYER_USABLE in self.system_vs and self.session_data.current_ref_fid is not None
            self.my_dialog.dspbx_n_abs_from.setEnabled(enable_stationing_widgets)
            self.my_dialog.dspbx_n_fract_from.setEnabled(enable_stationing_widgets)
            self.my_dialog.dspbx_n_abs_to.setEnabled(enable_stationing_widgets)
            self.my_dialog.dspbx_n_fract_to.setEnabled(enable_stationing_widgets)

            geom_m_valid = False
            self.my_dialog.qlbl_m_abs_valid_hint.clear()
            self.my_dialog.qlbl_m_fract_valid_hint.clear()
            if (self.SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs) and self.session_data.current_ref_fid is not None:
                reference_geom, error_msg = self.tool_get_reference_geom(ref_fid=self.session_data.current_ref_fid)
                if reference_geom:
                    geom_m_valid, error_msg = tools.MyTools.check_geom_m_valid(reference_geom)
                    if not geom_m_valid:
                        self.my_dialog.qlbl_m_abs_valid_hint.setText(MY_DICT.tr('reference_geom_not_m_valid',self.session_data.current_ref_fid,error_msg))
                        self.my_dialog.qlbl_m_fract_valid_hint.setText(MY_DICT.tr('reference_geom_not_m_valid', self.session_data.current_ref_fid,error_msg))

            self.my_dialog.dspbx_m_abs_from.setEnabled(enable_stationing_widgets and geom_m_valid)
            self.my_dialog.dspbx_m_fract_from.setEnabled(enable_stationing_widgets and geom_m_valid)
            self.my_dialog.dspbx_m_abs_to.setEnabled(enable_stationing_widgets and geom_m_valid)
            self.my_dialog.dspbx_m_fract_to.setEnabled(enable_stationing_widgets and geom_m_valid)

            self.my_dialog.dspbx_delta_m_abs.setEnabled(enable_pausing_widgets and geom_m_valid)
            self.my_dialog.dspbx_delta_m_fract.setEnabled(enable_pausing_widgets and geom_m_valid)

            self.my_dialog.dnspbx_z_from.setEnabled(enable_stationing_widgets and (self.SVS.REFERENCE_LAYER_Z_ENABLED in self.system_vs))

            # zooms preferably to measure_feature, but also pol_from/pol_to and even on different reference-lines
            self.my_dialog.pb_zoom_to_stationings.setEnabled((self.session_data.measure_feature and self.session_data.measure_feature.is_valid) or (self.session_data.pol_from is not None and self.session_data.pol_to is not None and self.session_data.pol_from.is_valid and self.session_data.pol_to.is_valid))




    def dlg_refresh_feature_selection_section(self):
        """refreshes the Feature-Selection-TreeView in dialog
            triggered by
            dataLyr-edits,
            dataLyr/referenceLyr/showLyr-provider-edits (e.g. filter)
            layer-configuration-edits in data/reference/show-layer
            plugin-settings-changes e.g. new show-layer
            user-defined selection-change
        """
        # Rev. 2024-07-08

        remove_icon = QtGui.QIcon(':icons/mIconClearTextHover.svg')
        zoom_selected_icon = QtGui.QIcon(':icons/mIconZoom.svg')
        invert_icon = QtGui.QIcon(':icons/mActionInvertSelection.svg')
        move_from_icon = QtGui.QIcon(':icons/move_lol_from.svg')
        move_to_icon = QtGui.QIcon(':icons/move_lol_to.svg')
        change_offset_icon = QtGui.QIcon(':icons/change_offset.svg')
        identify_icon = QtGui.QIcon(':icons/mActionIdentify.svg')
        delete_icon = QtGui.QIcon(':icons/mActionDeleteSelectedFeatures.svg')
        zoom_ref_feature_icon = QtGui.QIcon(':icons/mIconZoom.svg')
        move_feature_icon = QtGui.QIcon(':icons/move_segment.svg')
        redigitize_feature_icon = QtGui.QIcon(':icons/re_digitize_lol.svg')

        self.tool_check_selected_ids()

        if self.my_dialog:
            with (QtCore.QSignalBlocker(self.my_dialog.qtrv_feature_selection)):
                with QtCore.QSignalBlocker(self.my_dialog.qtrv_feature_selection.selectionModel()):

                    # order settings for later restore
                    old_indicator = self.my_dialog.qtrv_feature_selection.header().sortIndicatorSection()
                    old_order = self.my_dialog.qtrv_feature_selection.header().sortIndicatorOrder()
                    expanded_ref_fids = []

                    # store previous expanded branches for later restore
                    for rc in range(self.my_dialog.qtrv_feature_selection.model().rowCount()):
                        index = self.my_dialog.qtrv_feature_selection.model().index(rc, 0)
                        if self.my_dialog.qtrv_feature_selection.isExpanded(index):
                            expanded_ref_fids.append(index.data(self.ref_fid_role))

                    self.my_dialog.pbtn_append_data_features.setEnabled(False)
                    self.my_dialog.pbtn_append_show_features.setEnabled(False)
                    self.my_dialog.pbtn_clear_features.setEnabled(False)
                    self.my_dialog.pbtn_zoom_to_feature_selection.setEnabled(False)
                    self.my_dialog.pbtn_transfer_feature_selection.setEnabled(False)
                    self.my_dialog.pbtn_feature_selection_to_data_layer_filter.setEnabled(False)
                    self.my_dialog.pbtn_select_features.setEnabled(False)

                    # remove contents, but keep header
                    self.my_dialog.qtrv_feature_selection.model().removeRows(0, self.my_dialog.qtrv_feature_selection.model().rowCount())

                    if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:

                        data_context = qgis.core.QgsExpressionContext()
                        data_display_exp = qgis.core.QgsExpression(self.derived_settings.dataLyr.displayExpression())
                        data_display_exp.prepare(data_context)

                        ref_context = qgis.core.QgsExpressionContext()
                        ref_display_exp = qgis.core.QgsExpression(self.derived_settings.refLyr.displayExpression())
                        ref_display_exp.prepare(ref_context)

                        num_data_features = self.derived_settings.dataLyr.featureCount()
                        num_selected_data_features = len(self.session_data.selected_fids)

                        # featureCount on showLyr, can be !=  self.derived_settings.dataLyr.featureCount() because of filter or failing joins
                        num_show_features = 0
                        show_context = None
                        show_display_exp = None
                        if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
                            num_show_features = self.derived_settings.showLyr.featureCount()
                            show_context = qgis.core.QgsExpressionContext()
                            show_display_exp = qgis.core.QgsExpression(self.derived_settings.showLyr.displayExpression())
                            show_display_exp.prepare(show_context)

                        self.my_dialog.pbtn_append_show_features.setEnabled(num_show_features > 0)
                        # check the select-features-button, if at least one Show-Layer is complete and there are features in data-layer (quick&dirty, the show-layers should be checked...)
                        self.my_dialog.pbtn_select_features.setEnabled(num_show_features > 0)

                        self.my_dialog.pbtn_zoom_to_feature_selection.setEnabled(num_selected_data_features > 0)
                        self.my_dialog.pbtn_transfer_feature_selection.setEnabled(num_selected_data_features > 0)

                        self.my_dialog.pbtn_feature_selection_to_data_layer_filter.setEnabled((not self.derived_settings.dataLyr.isEditable()) and len(self.session_data.selected_fids) > 0)

                        self.my_dialog.pbtn_clear_features.setEnabled(len(self.session_data.selected_fids) > 0)

                        added_or_edited_fids = []
                        if self.derived_settings.dataLyr.editBuffer():
                            added_or_edited_fids = self.derived_settings.dataLyr.editBuffer().allAddedOrEditedFeatures()

                        self.my_dialog.pbtn_append_data_features.setEnabled(num_data_features > 0)

                        if self.session_data.selected_fids:
                            # query dataLyr with self.session_data.selected_fids

                            request = qgis.core.QgsFeatureRequest().setFilterFids(self.session_data.selected_fids)

                            # correct order to iterate without subqueries on data-layer
                            ref_id_clause = qgis.core.QgsFeatureRequest.OrderByClause(self.derived_settings.dataLyrReferenceField.name(), True)
                            from_clause = qgis.core.QgsFeatureRequest.OrderByClause(self.derived_settings.dataLyrStationingFromField.name(), True)
                            to_clause = qgis.core.QgsFeatureRequest.OrderByClause(self.derived_settings.dataLyrStationingToField.name(), True)
                            orderby = qgis.core.QgsFeatureRequest.OrderBy([ref_id_clause, from_clause, to_clause])
                            request.setOrderBy(orderby)

                            root_item = self.my_dialog.qtrv_feature_selection.model().invisibleRootItem()
                            last_ref_id = None
                            reference_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                            for data_feature in self.derived_settings.dataLyr.getFeatures(request):
                                fvs = self.tool_check_data_feature(data_feature=data_feature)
                                fvs.check_data_feature_valid()

                                data_fid = data_feature.id()
                                ref_id = data_feature[self.stored_settings.dataLyrReferenceFieldName]
                                if ref_id != last_ref_id:
                                    last_ref_id = ref_id
                                    reference_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                    # erst hinzufügen, sonst reference_item.index().row() == -1 reference_item.index().column == -1
                                    root_item.appendRow(reference_item)

                                    ref_feature, error_msg = self.tool_get_reference_feature(ref_id=ref_id)
                                    if ref_feature:
                                        ref_fid = ref_feature.id()
                                        reference_item.setData(ref_fid, self.custom_sort_role)
                                        reference_item.setData(ref_fid, self.ref_fid_role)
                                        ref_context.setFeature(ref_feature)
                                        display_exp = ref_display_exp.evaluate(ref_context)
                                        # Note: evaluated ref_display_exp will be of type QVariant (stringified 'NULL') for fields without content, otherwise str
                                        if display_exp == ref_fid or isinstance(display_exp, QtCore.QVariant):
                                            reference_item.setText(f"# {ref_id}")
                                        else:
                                            reference_item.setText(f"# {ref_id} {display_exp}")
                                        cell_widget = MyQtWidgets.QTwCellWidget()
                                        qtb = MyQtWidgets.QTwToolButton()

                                        qtb.setIcon(zoom_ref_feature_icon)
                                        qtb.setToolTip(MY_DICT.tr('highlight_reference_feature_qtb_ttp'))
                                        qtb.pressed.connect(self.st_toggle_ref_feature)
                                        qtb.setProperty("ref_fid", ref_fid)

                                        cell_widget.layout().addWidget(qtb)

                                        qtb = MyQtWidgets.QTwToolButton()
                                        qtb.setIcon(identify_icon)
                                        qtb.setToolTip(MY_DICT.tr('show_feature_form_qtb_ttp'))
                                        qtb.pressed.connect(self.st_open_ref_form)
                                        qtb.setProperty("ref_fid", ref_fid)
                                        cell_widget.layout().addWidget(qtb)

                                        self.my_dialog.qtrv_feature_selection.setIndexWidget(reference_item.index(), cell_widget)


                                    else:
                                        # folder for false assignments
                                        reference_item.setText(MY_DICT.tr('unknown_reference_item', ref_id))
                                        reference_item.setToolTip(error_msg)

                                id_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                id_item.setData(data_fid, self.custom_sort_role)
                                id_item.setData(data_fid, self.data_fid_role)
                                data_context.setFeature(data_feature)
                                display_exp = data_display_exp.evaluate(data_context)

                                if display_exp == data_fid or isinstance(display_exp,QtCore.QVariant):
                                    id_item.setText(f"# {data_fid}")
                                else:
                                    id_item.setText(f"# {data_fid} {display_exp}")

                                stationing_from = data_feature[self.stored_settings.dataLyrStationingFromFieldName]
                                from_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                from_item.setData(stationing_from, self.custom_sort_role)
                                from_item.setText(str(stationing_from))
                                from_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                stationing_to = data_feature[self.stored_settings.dataLyrStationingToFieldName]
                                to_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                to_item.setData(stationing_to, self.custom_sort_role)
                                to_item.setText(str(stationing_to))
                                to_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                offset = data_feature[self.stored_settings.dataLyrOffsetFieldName]
                                offset_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                offset_item.setData(offset, self.custom_sort_role)
                                offset_item.setText(str(offset))
                                offset_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                delta_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                if fvs.is_valid and isinstance(stationing_to, numbers.Number) and isinstance(stationing_from, numbers.Number):
                                    # length-calculation based on numeric stationings, not on lol_feature.delta_n_abs
                                    delta_n = stationing_to - stationing_from
                                    delta_item.setData(delta_n, self.custom_sort_role)
                                    delta_item.setText(str(delta_n))
                                    delta_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

                                show_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                show_fid = None
                                if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
                                    show_feature, error_msg = self.tool_get_show_feature(data_fid=data_fid)
                                    if show_feature:
                                        show_fid = show_feature.id()
                                        show_item = MyQtWidgets.QStandardItemCustomSort(self.custom_sort_role)
                                        show_item.setData(show_fid, self.custom_sort_role)
                                        show_item.setData(show_fid, self.show_fid_role)
                                        show_context.setFeature(show_feature)
                                        display_exp = show_display_exp.evaluate(show_context)

                                        if display_exp == show_fid or isinstance(display_exp,QtCore.QVariant):
                                            show_item.setText(f"# {show_fid}")
                                        else:
                                            show_item.setText(f"{display_exp}")

                                all_items = [id_item, from_item, to_item, offset_item, delta_item, show_item]

                                if fvs.is_valid:
                                    for item in all_items:
                                        item.setForeground(QtGui.QColor('green'))
                                else:
                                    for item in all_items:
                                        item.setToolTip(MY_DICT.tr('mvs_data_feature_invalid', data_fid, MY_DICT.tr(fvs.first_fail_flag)))
                                        item.setForeground(QtGui.QColor('red'))
                                        # no bold font possible because of delegate

                                reference_item.appendRow(all_items)

                                cell_widget = MyQtWidgets.QTwCellWidget()

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(remove_icon)
                                qtb.setToolTip(MY_DICT.tr('remove_from_selection_qtb_ttp'))
                                qtb.pressed.connect(self.st_remove_from_feature_selection)
                                qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setProperty("data_fid", data_fid)
                                qtb.setIcon(identify_icon)
                                qtb.setToolTip(MY_DICT.tr('show_feature_form_qtb_ttp'))
                                qtb.pressed.connect(self.st_open_data_form)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(zoom_selected_icon)
                                qtb.setEnabled(fvs.is_valid)
                                if fvs.is_valid:
                                    qtb.setProperty("data_fid", data_fid)
                                    qtb.pressed.connect(self.cvs_toggle_feature_markers)
                                    qtb.setToolTip(MY_DICT.tr('zoom_to_edit_pk_ttp'))
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setProperty("data_fid", data_fid)
                                qtb.setIcon(invert_icon)
                                qtb.setToolTip(MY_DICT.tr('select_in_layer_qtb_ttp'))
                                qtb.pressed.connect(self.st_select_in_layer)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(move_feature_icon)
                                qtb.setEnabled(fvs.is_valid and self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                if fvs.is_valid:
                                    qtb.setProperty("data_fid", data_fid)
                                    qtb.setToolTip(MY_DICT.tr('move_feature_qtb_ttp'))
                                    qtb.clicked.connect(self.stm_move_feature)

                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(redigitize_feature_icon)
                                qtb.setEnabled(self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                if self.SVS.DATA_LAYER_EDITABLE in self.system_vs:
                                    qtb.setToolTip(MY_DICT.tr('lol_redigitize_feature_qtb_ttp'))
                                    qtb.clicked.connect(self.stm_redigitize_feature)
                                    qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(delete_icon)
                                qtb.setEnabled((self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_DELETE_ENABLED) in self.system_vs)
                                if (self.SVS.DATA_LAYER_EDITABLE | self.SVS.DATA_LAYER_DELETE_ENABLED) in self.system_vs:
                                    qtb.setToolTip(MY_DICT.tr('delete_feature_qtb_ttp'))
                                    qtb.pressed.connect(self.st_delete_feature)
                                    qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)

                                self.my_dialog.qtrv_feature_selection.setIndexWidget(id_item.index(), cell_widget)

                                cell_widget = MyQtWidgets.QTwCellWidget()
                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(move_from_icon)
                                qtb.setEnabled(fvs.is_valid and self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                if fvs.is_valid and self.SVS.DATA_LAYER_EDITABLE in self.system_vs:
                                    qtb.setToolTip(MY_DICT.tr('set_feature_from_point_ttp'))
                                    qtb.clicked.connect(self.stm_set_feature_from_point)
                                    qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)
                                self.my_dialog.qtrv_feature_selection.setIndexWidget(from_item.index(), cell_widget)

                                cell_widget = MyQtWidgets.QTwCellWidget()
                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(move_to_icon)

                                qtb.setEnabled(fvs.is_valid and self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                if fvs.is_valid and self.SVS.DATA_LAYER_EDITABLE in self.system_vs:
                                    qtb.setToolTip(MY_DICT.tr('set_feature_to_point_ttp'))
                                    qtb.clicked.connect(self.stm_set_feature_to_point)
                                    qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)
                                self.my_dialog.qtrv_feature_selection.setIndexWidget(to_item.index(), cell_widget)

                                cell_widget = MyQtWidgets.QTwCellWidget()
                                qtb = MyQtWidgets.QTwToolButton()
                                qtb.setIcon(change_offset_icon)
                                qtb.setEnabled(fvs.is_valid and self.SVS.DATA_LAYER_EDITABLE in self.system_vs)
                                if fvs.is_valid and self.SVS.DATA_LAYER_EDITABLE in self.system_vs:
                                    qtb.setToolTip(MY_DICT.tr('change_feature_offset_ttp'))
                                    qtb.clicked.connect(self.stm_change_feature_offset)
                                    qtb.setProperty("data_fid", data_fid)
                                cell_widget.layout().addWidget(qtb)
                                self.my_dialog.qtrv_feature_selection.setIndexWidget(offset_item.index(), cell_widget)

                                if show_fid:
                                    cell_widget = MyQtWidgets.QTwCellWidget()
                                    qtb = MyQtWidgets.QTwToolButton()
                                    # Note: st_open_show_form expects data_fid as attribute
                                    qtb.setProperty("data_fid", data_fid)
                                    qtb.setIcon(identify_icon)
                                    qtb.setToolTip(MY_DICT.tr('show_feature_form_qtb_ttp'))
                                    qtb.pressed.connect(self.st_open_show_form)
                                    cell_widget.layout().addWidget(qtb)
                                    self.my_dialog.qtrv_feature_selection.setIndexWidget(show_item.index(), cell_widget)

                    # restore previous sort-settings
                    self.my_dialog.qtrv_feature_selection.sortByColumn(old_indicator, old_order)

                    for rc in range(self.my_dialog.qtrv_feature_selection.model().rowCount()):
                        index = self.my_dialog.qtrv_feature_selection.model().index(rc, 0)
                        if index.data(self.ref_fid_role) in expanded_ref_fids:
                            self.my_dialog.qtrv_feature_selection.setExpanded(index, True)

                    if self.session_data.edit_feature:
                        self.dlg_select_feature_selection_row(self.session_data.edit_feature.data_fid)

    def st_select_in_layer(self):
        """selects/unselects feature in data- and show-layer(s) from qtrv_feature_selection"""
        # Rev. 2024-07-08
        selection_mode = 'replace_selection'
        if QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers():
            selection_mode = 'remove_from_selection'
        elif QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers():
            selection_mode = 'add_to_selection'

        data_fid = self.sender().property('data_fid')
        data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
        if data_feature:

            show_fid = None
            if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                data_id = data_feature[self.stored_settings.dataLyrIdFieldName]
                show_feature = tools.MyTools.get_feature_by_value(self.derived_settings.showLyr, self.derived_settings.showLyrBackReferenceField, data_id)
                if show_feature and show_feature.isValid():
                    show_fid = show_feature.id()
                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('no_show_feature_for_data_feature', data_id))

            if selection_mode == 'replace_selection':
                self.derived_settings.dataLyr.removeSelection()
                self.derived_settings.dataLyr.select(data_fid)
                if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                    self.derived_settings.showLyr.removeSelection()
                    if show_fid is not None:
                        self.derived_settings.showLyr.select(show_fid)
            elif selection_mode == 'remove_from_selection':
                self.derived_settings.dataLyr.deselect(data_fid)
                if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                    if show_fid is not None:
                        self.derived_settings.showLyr.deselect(show_fid)
            else:
                self.derived_settings.dataLyr.select(data_fid)
                if self.SVS.SHOW_LAYER_COMPLETE in self.system_vs:
                    if show_fid is not None:
                        self.derived_settings.showLyr.select(show_fid)
        else:
            self.dlg_append_log_message('WARNING', error_msg)

    def st_open_data_form(self):
        """opens form for dataLyr
            called from QTableWidget
            data_fid stored as property in cell-widget"""
        # Rev. 2024-07-08
        data_fid = self.sender().property('data_fid')

        data_feature, error_msg = self.tool_get_data_feature(data_fid=data_fid)
        if data_feature:
            extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
            self.tool_select_feature(data_fid, ['snf', 'snt', 'sgn', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)
            feature_form = tools.MyTools.get_feature_form(self.iface, self.derived_settings.dataLyr, data_feature, False, 500, 300)
            feature_form.show()
        else:
            self.dlg_append_log_message("WARNING", error_msg)

    def st_remove_from_feature_selection(self):
        """removes this feature/row from self.session_data.selected_fids/selection-list
            data_fid stored as property in cell-widget
            called from QTableWidget"""
        # Rev. 2024-07-08
        data_fid = self.sender().property('data_fid')
        if self.session_data.edit_feature and data_fid == self.session_data.edit_feature.data_fid:
            self.session_data.edit_feature = None
            self.dlg_refresh_measure_section()
            self.cvs_hide_markers()

        if data_fid in self.session_data.selected_fids:
            self.session_data.selected_fids.remove(data_fid)
            self.dlg_refresh_feature_selection_section()

    def st_open_show_form(self):
        """opens feature-form for showLyr from selection-list
            data_fid stored as property in cell-widget
            called from QTableWidget"""
        # Rev. 2024-07-08
        # bit complicated because fid and id/pk must not be identical:
        # from data_fid to data_id to show-feature
        data_fid = self.sender().property('data_fid')
        if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
            show_feature, error_msg = self.tool_get_show_feature(data_fid=data_fid)
            if show_feature:
                extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
                self.tool_select_feature(data_fid, ['snf', 'snt', 'sgn', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)
                feature_form = tools.MyTools.get_feature_form(self.iface, self.derived_settings.showLyr, show_feature)
                feature_form.show()
            else:
                self.dlg_append_log_message('WARNING', error_msg)

    def st_open_ref_form(self):
        """opens feature-form for refLyr from selection-list
            ref_fid is stored as property in cell-widget
            called from QTableWidget
            """
        # Rev. 2024-07-08
        ref_fid = self.sender().property('ref_fid')
        zoom_to_feature = bool(QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers())

        if self.SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            ref_feature, error_msg = self.tool_get_reference_feature(ref_fid=ref_fid)
            if ref_feature:
                feature_form = tools.MyTools.get_feature_form(self.iface, self.derived_settings.refLyr, ref_feature)
                feature_form.show()
                # draw and optionally zoom:
                if ref_feature.hasGeometry():
                    self.cvs_draw_reference_geom(reference_geom=ref_feature.geometry(), zoom_to_feature=zoom_to_feature)
            else:
                self.dlg_append_log_message("WARNING", error_msg)

    def st_toggle_ref_feature(self):
        """shows/hide/zooms a reference-feature-geometry
            ref_fid is stored as property in cell-widget
            called from QTableWidget
            zoom to feature with shift-click"""
        # Rev. 2024-07-08
        ref_fid = self.sender().property('ref_fid')
        zoom_to_feature = bool(QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers())
        if self.SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            draw_this_line = zoom_to_feature
            draw_this_line |= not self.rb_rfl.isVisible()
            draw_this_line |= ref_fid != self.session_data.highlighted_ref_fid

            if draw_this_line:
                self.cvs_draw_reference_geom(ref_fid=ref_fid, zoom_to_feature=zoom_to_feature)
                self.session_data.highlighted_ref_fid = ref_fid
            else:
                self.rb_rfl.hide()
                self.session_data.highlighted_ref_fid = None

    def sys_store_settings(self):
        """store all permanent settings to qgis.core.QgsProject.instance()
        the "internal" values (with underscores) are stored (with underscores too) and restored later
        Triggered on sys_unload and qgis.core.QgsProject.instance().writeProject(...) *before* the project is saved to file
        changes only appear, if the project is saved to disk
        """
        # Rev. 2024-07-08
        # filter: startswith('_')
        # => use "hidden" properties, not their property-setters
        property_dict = {prop: getattr(self.stored_settings, prop) for prop in dir(StoredSettings) if prop.startswith('_') and not prop.startswith('__')}

        for prop_name in property_dict:
            prop_value = property_dict[prop_name]
            # other key then LolEvt
            key = f"/LolEvt/{prop_name}"
            if prop_value:
                qgis.core.QgsProject.instance().writeEntry('LinearReferencing', key, prop_value)
            else:
                qgis.core.QgsProject.instance().removeEntry('LinearReferencing', key)

    def sys_unload(self):
        """called from LinearReference.sys_unload() on plugin-sys_unload and/or QGis-shut-down or project-close
            checks and writes the settings back to project
            removes dialog and temporal graphics
            """
        # Rev. 2024-07-08
        try:
            # close *and* delete dialog
            self.my_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            self.my_dialog.close()
            self.my_dialog = None
            # no delete, because sometimes crash on unload, possibly the dialog is still required from LinearReference.py?
            # del self.my_dialog

            self.sys_store_settings()

            # remove canvas-graphics
            self.cvs_hide_markers()

            # hide orphaned snap-indicators
            self.cvs_hide_snap()

            self.iface.mapCanvas().scene().removeItem(self.vm_snf)
            self.iface.mapCanvas().scene().removeItem(self.vm_snt)
            self.iface.mapCanvas().scene().removeItem(self.vm_enf)
            self.iface.mapCanvas().scene().removeItem(self.vm_ent)
            self.iface.mapCanvas().scene().removeItem(self.vm_pt_cnt)
            self.iface.mapCanvas().scene().removeItem(self.vm_pt_cnf)
            self.iface.mapCanvas().scene().removeItem(self.rb_csgn)
            self.iface.mapCanvas().scene().removeItem(self.rb_rfl)
            self.iface.mapCanvas().scene().removeItem(self.rb_sgn)
            self.iface.mapCanvas().scene().removeItem(self.rb_sg0)
            self.iface.mapCanvas().scene().removeItem(self.rb_selection_rect)
            self.iface.mapCanvas().scene().removeItem(self.rb_rfl_diff_cu)
            self.iface.mapCanvas().scene().removeItem(self.rb_rfl_diff_ca)

            self.sys_disconnect_layer_slots()
            self.gui_remove_layer_actions()

            for conn_id in self.application_slot_cons:
                qgis.core.QgsApplication.instance().disconnect(conn_id)
            self.application_slot_cons = []

            for conn_id in self.canvas_slot_cons:
                self.iface.mapCanvas().disconnect(conn_id)
            self.canvas_slot_cons = []

            # it was possibly disabled
            # => restore previous setting
            # qgis.core.QgsSettings().setValue('app/askToSaveMemoryLayers', self.save_memory_layers)

        except Exception as e:
            pass

    def sys_disconnect_layer_slots(self):
        """disconnect all in registered layer-slot-connections
        called on unload"""
        # Rev. 2024-07-08
        # traverse signal_slot_cons, check if layer still exists and disconnect the signals/slots
        for layer_id in self.signal_slot_cons:
            layer = qgis.core.QgsProject.instance().mapLayer(layer_id)
            if layer:
                for conn_signal in self.signal_slot_cons[layer_id]:
                    for conn_function in self.signal_slot_cons[layer_id][conn_signal]:
                        conn_id = self.signal_slot_cons[layer_id][conn_signal][conn_function]
                        layer.disconnect(conn_id)
            else:
                # orphaned connection-object for not existing layer
                pass

        self.signal_slot_cons = {}

    def flags(self):
        """reimplemented for tool_mode 'select_features' with ShiftModifier: disables the default-zoom-behaviour
            see: https://gis.stackexchange.com/questions/449523/override-the-zoom-behaviour-of-qgsmaptoolextent"""
        # Rev. 2024-07-08
        return super().flags() & ~qgis.gui.QgsMapToolEmitPoint.AllowZoomRect

    class SVS(Flag):
        """SystemValidState
        Store and check system-settings
        stored in self.system_vs
        positve-flags: each bit symbolizes a fulfilled precondition
        """
        # Rev. 2024-07-08
        INIT = auto()

        REFERENCE_LAYER_EXISTS = auto()
        REFERENCE_LAYER_HAS_VALID_CRS = auto()
        REFERENCE_LAYER_IS_LINESTRING = auto()
        REFERENCE_LAYER_CONNECTED = auto()
        REFERENCE_LAYER_M_ENABLED = auto()
        REFERENCE_LAYER_Z_ENABLED = auto()
        REFERENCE_LAYER_ID_FIELD_DEFINED = auto()
        REFERENCE_LAYER_INSERT_ENABLED = auto()
        REFERENCE_LAYER_UPDATE_ENABLED = auto()
        REFERENCE_LAYER_DELETE_ENABLED = auto()
        REFERENCE_LAYER_EDITABLE = auto()

        DATA_LAYER_EXISTS = auto()
        DATA_LAYER_CONNECTED = auto()
        DATA_LAYER_ID_FIELD_DEFINED = auto()
        DATA_LAYER_REFERENCE_FIELD_DEFINED = auto()
        DATA_LAYER_OFFSET_FIELD_DEFINED = auto()
        DATA_LAYER_STATIONING_FROM_FIELD_DEFINED = auto()
        DATA_LAYER_STATIONING_TO_FIELD_DEFINED = auto()

        DATA_LAYER_INSERT_ENABLED = auto()
        DATA_LAYER_UPDATE_ENABLED = auto()
        DATA_LAYER_DELETE_ENABLED = auto()
        DATA_LAYER_EDITABLE = auto()

        SHOW_LAYER_EXISTS = auto()
        SHOW_LAYER_CONNECTED = auto()
        SHOW_LAYER_BACK_REFERENCE_FIELD_DEFINED = auto()

        # some combinations for convenience:
        REFERENCE_LAYER_USABLE = INIT | REFERENCE_LAYER_EXISTS | REFERENCE_LAYER_HAS_VALID_CRS | REFERENCE_LAYER_IS_LINESTRING | REFERENCE_LAYER_CONNECTED

        REFERENCE_LAYER_COMPLETE = INIT | REFERENCE_LAYER_USABLE | REFERENCE_LAYER_ID_FIELD_DEFINED

        DATA_LAYER_COMPLETE = INIT | DATA_LAYER_EXISTS | DATA_LAYER_CONNECTED | DATA_LAYER_ID_FIELD_DEFINED | DATA_LAYER_REFERENCE_FIELD_DEFINED | DATA_LAYER_OFFSET_FIELD_DEFINED | DATA_LAYER_STATIONING_FROM_FIELD_DEFINED | DATA_LAYER_STATIONING_TO_FIELD_DEFINED

        REFERENCE_AND_DATA_LAYER_COMPLETE = INIT | REFERENCE_LAYER_COMPLETE | DATA_LAYER_COMPLETE

        SHOW_LAYER_COMPLETE = INIT | SHOW_LAYER_EXISTS | SHOW_LAYER_CONNECTED | SHOW_LAYER_BACK_REFERENCE_FIELD_DEFINED

        ALL_LAYERS_COMPLETE = REFERENCE_AND_DATA_LAYER_COMPLETE | SHOW_LAYER_COMPLETE

        def __str__(self):
            """stringify implemented for debug-purpose"""
            # Rev. 2024-08-21
            result_str = ''

            all_items = [item.name for item in self.__class__]

            longest_item = max(all_items, key=len)
            max_len = len(longest_item)

            # single-bit-flags
            for item in self.__class__:
                #format(item.value, '024b')
                if item.value == (item.value & -item.value):
                    result_str += f"{item.name:<{max_len}}    {item in self}\n"
            # multi-bit-flags
            for item in self.__class__:
                #format(item.value, '024b')
                if item.value != (item.value & -item.value):
                    result_str += f"* {item.name:<{max_len}}  {item in self}\n"

            return result_str


def set_lol_edit_fid(fid: int, layer_id: str) -> None:
    """
    Attached to layer.actions, select LinearReferencing-LoL-Feature from table or form
    implemented for dataLyr/showLyr
    The fid gets positive, as soon as the new dataFeature is committed, but must not have the same fid in both layers, e.g. if the showLyr is not a virtual one but comes from a database-view.
    so savely distinguish, from which layer this featureAction was triggered

    Not-committed data-features with negative fids are not listed in any Show-Layer.

    Sample-Code for Action (a QGis expression, where some marked [%...%] wildcards will be replaced by current values):
    .. code-block:: text

        from LinearReferencing.map_tools.LolEvt import set_lol_edit_fid
        set_lol_edit_fid([%@id%],'[%@layer_id%]')


    :param fid: in action-code the wildcard ``[%@id%]`` will be replaced with the fid of the current feature. The value is negative, if the feature is only in edit-buffer, new table-row not yet saved.
    :param layer_id: in action-code the Wildcard ``[%@layer_id%]`` will be replaced with the ID of the layer, data-layer or show-layer from Map-Tool LolEvt accepted
    """
    # Rev. 2024-07-08
    _plugin_name = 'LinearReferencing'

    if _plugin_name in qgis.utils.plugins:
        lref_plugin = qgis.utils.plugins[_plugin_name]
        # access initialized Plugin
        # should not be necessary, because the layer-actions are removed on unload
        if not lref_plugin.mt_LolEvt:
            lref_plugin.set_map_tool_LolEvt()

        if lref_plugin.mt_LolEvt:
            # gefaktes self, da außerhalb des MapTools laufend
            self = lref_plugin.mt_LolEvt
            if self.SVS.REFERENCE_AND_DATA_LAYER_COMPLETE in self.system_vs:
                data_or_show_lyr = qgis.core.QgsProject.instance().mapLayer(layer_id)
                # case distinction: from which layer is this function called? dataLyr or showLyr?
                if data_or_show_lyr == self.derived_settings.dataLyr:
                    self.my_dialog.show()
                    self.my_dialog.activateWindow()
                    extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
                    self.tool_select_feature(fid, ['snf', 'snt', 'sgn', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)

                    self.my_dialog.tbw_central.setCurrentIndex(1)

                elif data_or_show_lyr == self.derived_settings.showLyr:
                    if self.SVS.ALL_LAYERS_COMPLETE in self.system_vs:
                        show_feature, error_msg = self.tool_get_show_feature(show_fid=fid)
                        if show_feature:
                            data_feature, error_msg = self.tool_get_data_feature(data_id=show_feature[self.stored_settings.showLyrBackReferenceFieldName])
                            if data_feature:
                                extent_mode = 'zoom' if (QtCore.Qt.ShiftModifier & QtWidgets.QApplication.keyboardModifiers()) else 'pan' if (QtCore.Qt.ControlModifier & QtWidgets.QApplication.keyboardModifiers()) else ''
                                self.tool_select_feature(data_feature.id(), ['snf', 'snt', 'sgn', 'rfl'], ['snf', 'snt', 'sgn'], extent_mode)
                                self.my_dialog.tbw_central.setCurrentIndex(1)
                            else:
                                self.dlg_append_log_message('WARNING', error_msg)
                        else:
                            self.dlg_append_log_message('WARNING', error_msg)
                    else:
                        self.dlg_append_log_message('INFO', MY_DICT.tr('reference_data_or_show_layer_missing'))

                else:
                    self.dlg_append_log_message('INFO', MY_DICT.tr('layer_not_registered', data_or_show_lyr.name()))
            else:
                self.dlg_append_log_message('INFO', MY_DICT.tr('reference_or_data_layer_missing'))
        else:
            qgis.utils.iface.messageBar().pushMessage(f"MapTool 'LoLEvt' in Plugin '{_plugin_name}' not loaded...", level=qgis.core.Qgis.Critical, duration=20)
    else:
        qgis.utils.iface.messageBar().pushMessage(f"Plugin '{_plugin_name}' missing...", level=qgis.core.Qgis.Critical, duration=20)
