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
import os, qgis
import numbers
import re
import typing
import webbrowser
import traceback
import pathlib

from typing import Any
from qgis.gui import (
    QgsMapToolEmitPoint,
    QgisInterface,
    QgsSnapIndicator,
    QgsMapMouseEvent,
    QgsExpressionBuilderDialog,
    QgsMapTool,
)

from PyQt5.QtWidgets import QApplication, QMessageBox, QAction, QDockWidget

from PyQt5.QtGui import QColor, QIcon, QFont, QStandardItem


from qgis.core import (
    QgsWkbTypes,
    QgsPointLocator,
    QgsCoordinateReferenceSystem,
    QgsRectangle,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsProject,
    QgsApplication,
    QgsVectorLayer,
    QgsAction,
    QgsAttributeTableConfig,
    QgsGeometry,
    QgsFeature,
    Qgis,
    QgsSnappingConfig,
    QgsPoint,
    QgsFeatureRequest,
)

from LinearReferencing.settings.exceptions import *

from LinearReferencing.tools.MyTools import (
    check_mods,
    select_in_layer,
    qtrv_extract_items,
    sys_get_locale,
    show_feature_form,
    get_feature_by_value,
    open_attribute_table,
    get_field_values,
    get_unique_string
)

from LinearReferencing.tools.MyDebugFunctions import (
    get_debug_pos,
    get_debug_file_line,
    debug_log,
    debug_print
)


from LinearReferencing.settings.constants import Qt_Roles

from PyQt5.QtCore import (
    QUuid,
    Qt,
    QDateTime,
    QSignalBlocker,
    QLocale,
    QMetaType,
    QItemSelectionModel,
    QLocale,
    QObject,
    QPoint
)

from LinearReferencing.qt.MyQtWidgets import MyEditToolButton, MyDeleteToolButton, MyLogItem

from enum import Flag, auto

from LinearReferencing.i18n.SQLiteDict import SQLiteDict


# global variable
MY_DICT = SQLiteDict()


# QgsMapToolEmitPoint
class LrEvt(QgsMapToolEmitPoint):
    """abstract Base-Class for LolEvt and PolEvt for digitize linear-referenced PoL/LoL-Features
    Here implemented methods and properties are identical for the derived Sub-Classes LolEvt/PolEvt and their dialogs LolDialog/PolDialog
    """
    # Rev. 2026-01-12

    def __init__(self, iface: QgisInterface):
        """initialize this mapTool
        :param iface: interface to QgisApp
        """
        # Rev. 2026-01-10

        # the dialog for this MapTool as class-variable and later initialized as instance-variable
        self.my_dialog = None  # dialogs.LolDialog or PoLDialog

        # Sub-Dialog, initialized on demand, see sys_create_data_lyr
        # stored as property to keep user-data
        self.create_data_lyr_dialog = None

        # log-message-count, incremented with dlg_append_log_message
        self.lmc = 0

        # pre-defined IDs used to identify the QActions in Reference, Data- and Show-Layer
        # Note 1: also embedded as string into Python-action-code for debug purpose aka #   action_id='{self._show_ref_feature_act_id.toString()}'
        # Note 2: user-defined QgsActions get a randomly generated QUuid
        # Note 3: invalid QuUIDs result in PyQt5.QUuid('{00000000-0000-0000-0000-000000000000}')

        # commonly used in PolEvt and LolEvt
        self._show_feature_form_act_id = QUuid("2aaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        self._show_ref_feature_act_id = QUuid("3aaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

        # LolEvt
        self._zoom_lol_feature_act_id = QUuid("1aaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

        # PolEvt
        self._zoom_pol_feature_act_id = QUuid("11aaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")





        # Log-Messages inside init, whichg will populate not yet existing Message-Log afterwards
        self.message_log = []
        #self.sys_log_message("INFO","__init__")


        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        # iface for access to QGis-Application
        self.iface = iface
        self.system_vs = SVS.INIT
        self.stored_settings = StoredSettings()
        self.derived_settings = DerivedSettings()
        self.session_data = SessionData()
        self.signal_slot_cons = SignalSlotConnections()

        # initialize the settings-"containers" with blank "templates" (StoredSettings => different versions implemented in PolEvt/LolEvt)
        # restore settings from last usage in this project
        self.sys_restore_stored_settings()

        # convenience: auto-register the first non-virtual Linestring-Layer
        if not QgsProject.instance().mapLayer(self.stored_settings.refLyrId):
            # layerTreeRoot => layers on TOC-Order
            linestring_wkb_types = [
                QgsWkbTypes.LineString,
                QgsWkbTypes.MultiLineString,
                QgsWkbTypes.LineStringZ,
                QgsWkbTypes.MultiLineStringZ,
                QgsWkbTypes.LineStringM,
                QgsWkbTypes.MultiLineStringM,
                QgsWkbTypes.LineStringZM,
                QgsWkbTypes.MultiLineStringZM,
            ]
            for ltr_layer in QgsProject.instance().layerTreeRoot().findLayers():
                ref_lyr = ltr_layer.layer()
                # same check as in sys_connect_ref_lyr
                if (
                    ref_lyr.isValid()
                    and ref_lyr.type() == Qgis.LayerType.VectorLayer
                    and ref_lyr.dataProvider().wkbType() in linestring_wkb_types
                    and ref_lyr.dataProvider().name() != "virtual"
                ):
                    self.stored_settings.refLyrId = ref_lyr.id()
                    self.sys_log_message("INFO",f"reference-layer detected: '{ref_lyr.name()}'")
                    break

        self.sys_restore_derived_settings()


        # QgsSnapIndicator: tiny snap-icon
        # must be stored as reference
        # any access to QgsSnapIndicator(self.iface.mapCanvas()) will not affect self.snap_indicator
        # the icon is used with some canvasMoveEvents
        self.snap_indicator = QgsSnapIndicator(self.iface.mapCanvas())

        self.my_locale = sys_get_locale()

        #self.sys_log_message("INFO",f"locale: {self.my_locale.name()}")

        # dummy-QAction, only to uncheck all current checked QActions from mapToolActionGroup (including some toolmode-QActions of this plugin)
        # previous: self.stm_pausing()
        # now: self.qact_pausing.trigger()
        self.qact_pausing = QAction(
            QIcon(":icons/pause-circle-outline.svg"), MY_DICT.tr("lr_toolmode_pausing")
        )
        self.qact_pausing.setCheckable(True)
        self.qact_pausing.triggered.connect(self.stm_pausing)
        self.iface.mapToolActionGroup().addAction(self.qact_pausing)

        arrow_cursor = Qt.ArrowCursor
        # pointing_hand_cursor = Qt.PointingHandCursor
        # open_hand_cursor = Qt.OpenHandCursor
        # cross_cursor = Qt.CrossCursor
        # wait_cursor = Qt.WaitCursor
        # size_hor_cursor = Qt.SizeHorCursor
        size_all_cursor = Qt.SizeAllCursor
        forbidden_cursor = Qt.ForbiddenCursor
        crosshair_cursor = QgsApplication.getThemeCursor(
            QgsApplication.Cursor.CrossHair
        )
        select_cursor = QgsApplication.getThemeCursor(QgsApplication.Cursor.Select)

        self.session_data.dlg_last_width = 700
        self.session_data.dlg_last_height = 500

        # possible values for runtime_settings.tool_mode,
        # key: runtime_settings.tool_mode,
        # value: list [tool_tip, tool_mode_cursor, tool_mode_icon]
        self.tool_modes = {
            # Tool-Modes for LolEevt and PolEvt
            "initialized": [
                MY_DICT.tr("map_tool_initialized"),
                arrow_cursor,
                QIcon(":icons/mIconSuccess.svg"),
            ],
            "pausing": [
                MY_DICT.tr("lr_toolmode_pausing"),
                arrow_cursor,
                QIcon(":icons/pause-circle-outline.svg"),
            ],
            "disabled": [
                MY_DICT.tr("lr_toolmode_disabled"),
                forbidden_cursor,
                QIcon(":icons/alert-outline.svg"),
            ],
            "select_features": [
                MY_DICT.tr("lr_toolmode_select_features"),
                select_cursor,
                QIcon(":icons/select_pol_feature.svg"),
            ],

            "select_edit_feature": [
                MY_DICT.tr("lr_toolmode_select_edit_feature"),
                select_cursor,
                QIcon(":icons/select_pol_feature.svg"),
            ],


            # LolEevt-Tool-Modes
            "set_from_point": [
                MY_DICT.tr("lol_toolmode_set_from_point"),
                crosshair_cursor,
                QIcon(":icons/set_from_point.svg"),
            ],
            "set_to_point": [
                MY_DICT.tr("lol_toolmode_set_to_point"),
                crosshair_cursor,
                QIcon(":icons/set_to_point.svg"),
            ],
            "measure_segment": [
                MY_DICT.tr("lol_toolmode_measure_segment"),
                crosshair_cursor,
                QIcon(":icons/re_digitize_lol.svg"),
            ],
            "move_segment": [
                MY_DICT.tr("lol_toolmode_move_segment"),
                size_all_cursor,
                QIcon(":icons/move_segment.svg"),
            ],
            "change_offset": [
                MY_DICT.tr("lol_toolmode_change_offset"),
                size_all_cursor,
                QIcon(":icons/change_offset.svg"),
            ],
            "change_feature_offset": [
                MY_DICT.tr("lol_toolmode_change_feature_offset"),
                size_all_cursor,
                QIcon(":icons/change_offset.svg"),
            ],
            "move_po_pro_segment": [
                MY_DICT.tr("lol_toolmode_move_po_pro_segment"),
                size_all_cursor,
                QIcon(":icons/move_po_pro_segment.svg"),
            ],
            "move_po_pro_from": [
                MY_DICT.tr("lol_toolmode_move_po_pro_from"),
                size_all_cursor,
                QIcon(":icons/move_po_pro_from_point.svg"),
            ],
            "move_po_pro_to": [
                MY_DICT.tr("lol_toolmode_move_po_pro_to"),
                size_all_cursor,
                QIcon(":icons/move_po_pro_to_point.svg"),
            ],
            "move_lol_feature": [
                MY_DICT.tr("lol_toolmode_move_lol_feature"),
                size_all_cursor,
                QIcon(":icons/move_segment.svg"),
            ],

            # PolEvt-Tool-Modes
            "measure_stationing": [
                MY_DICT.tr("pol_toolmode_measure_stationing"),
                crosshair_cursor,
                QIcon(":icons/linear_referencing_point.svg"),
            ],
            "move_measured_point": [
                MY_DICT.tr("pol_toolmode_move_measured_point"),
                size_all_cursor,
                QIcon(":icons/move_pol_feature.svg"),
            ],
            "move_po_pro_point": [
                MY_DICT.tr("pol_toolmode_move_po_pro_point"),
                size_all_cursor,
                QIcon(":icons/move_po_pro_point.svg"),
            ],

        }

        # tabs in both dialogs and their indices
        self.dialog_tabs = {
            "measurement": 0,
            "feature_selection": 1,
            "post_processing": 2,
            "settings": 3,
            "message_log": 4,
        }
        # reversed key and values
        self.dialog_tabs_reverse = {v: k for k, v in self.dialog_tabs.items()}







        # try/catch because of UniqueConnection which ensures no Double-Connects but raises TypeError: connection is not unique
        try:
            # customVariablesChanged => f.e. change of language-settings, number-format...
            self.signal_slot_cons.application_connections.append(
                QgsApplication.instance().customVariablesChanged.connect(
                    self.gui_refresh, Qt.UniqueConnection
                )
            )
        except:
            pass

        try:
            # triggered *before* the project is saved to file
            # store the plugin-settings in project-file
            self.signal_slot_cons.project_connections.append(
                QgsProject.instance().writeProject.connect(
                    self.sys_store_settings, Qt.UniqueConnection
                )
            )
        except:

            pass

        try:
            # triggered if a stored project is opened
            # reread settings and refresh settings-tab to reflect project-layers and stored settings of the opened project
            self.signal_slot_cons.project_connections.append(
                QgsProject.instance().readProject.connect(
                    self.sys_restart_session, Qt.UniqueConnection
                )
            )
        except:
            pass

        try:
            # connect some signals in project to register TOC-changes (especially layersRemoved)
            # Note: legendLayersAdded instead of layersAdded because "Emitted, when a layer was added to the registry and the legend"
            # and legend-refresh uses QgsProject.instance().layerTreeRoot and not QgsProject.instance().mapLayers
            self.signal_slot_cons.project_connections.append(
                QgsProject.instance().legendLayersAdded.connect(
                    self.ps_project_legendLayersAdded, Qt.UniqueConnection
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.project_connections.append(
                QgsProject.instance().layersRemoved.connect(
                    self.ps_project_layersRemoved, Qt.UniqueConnection
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.canvas_connections.append(
                self.iface.mapCanvas().mapToolSet.connect(
                    self.cs_mapToolSet, Qt.UniqueConnection
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.layer_tree_view_connections.append(
                QgsProject.instance()
                .layerTreeRoot()
                .layerOrderChanged.connect(
                    self.dlg_populate_settings, Qt.UniqueConnection
                )
            )
        except:
            pass

    def sys_log_message(self,error_level,message_content):
        """append log-item to message_log"""
        # Rev. 2026-01-11
        message_string = str(message_content)

        file, line, function = get_debug_file_line(2)

        self.message_log.append({
            'time': QDateTime.currentDateTime(),
            'error_level': error_level,
            'message_content': message_string,
            'file': file,
            'line': line,
            'function': function,
        })

    def dlg_show_message_log(self):
        """writes self.message_log to self.my_dialog.qtw_log_messages"""
        # Rev. 2026-01-11




        if self.my_dialog:
            for log_item in self.message_log:
                self.lmc += 1

                self.my_dialog.qtw_log_messages.model().appendRow(
                    [
                        MyLogItem(self.lmc),
                        MyLogItem(log_item.get('time')),
                        MyLogItem(log_item.get('error_level'),bg_color=log_item.get('error_level')),
                        MyLogItem(log_item.get('message_content')),
                        MyLogItem(os.path.basename(log_item['file']),log_item.get('file')),
                        MyLogItem(log_item.get('line')),
                        MyLogItem(log_item.get('function')),
                    ]
                )

            #self.my_dialog.qtw_log_messages.resizeRowsToContents()
            self.my_dialog.qtw_log_messages.resizeColumnsToContents()




    def tool_get_extent_mode_pol(self) -> str | None:
        """get extent-mode for cvs_draw_lr_geom depending on keyboard-modifiers
        Variant for Point-Features (PoL) => defaults to pan_center
        Returns:
            str|None
        """
        # Rev. 2026-01-10
        extent_mode = "pan_center"
        if check_mods("sc"):
            extent_mode = None
        elif check_mods("s"):
            extent_mode = "pan_center_opt_in"
        elif check_mods("c"):
            extent_mode = "pan_center_opt_out"

        return extent_mode


    def tool_get_extent_mode_lol(self) -> str | None:
        """get extent-mode for cvs_draw_lr_geom depending on keyboard-modifiers
        Variant for Line- or Polygon-Features (LoL) => defaults to zoom_bounds_out
        Returns:
            str|None
        """
        # Rev. 2026-01-10
        extent_mode = "zoom_bounds_out"
        if check_mods("sc"):
            extent_mode = None
        elif check_mods("s"):
            extent_mode = "pan_center_opt_in"
        elif check_mods("c"):
            extent_mode = "pan_center_opt_out"

        return extent_mode



    def dlg_refresh_po_pro_edit(self):
        """wrapper to refresh PostProcessing-Edit-Section"""
        # Rev. 2026-01-10
        self.dlg_reset_po_pro_edit()
        self.dlg_populate_po_pro_edit()
        self.dlg_refract_po_pro_edit()



    def dlg_refresh_settings(self):
        """wrapper to refresh settings-tab"""
        # Rev. 2026-01-10
        self.dlg_reset_settings()
        self.dlg_populate_settings()
        self.dlg_refract_settings()

    def dlg_refresh_po_pro_settings(self):
        """wrapper to refresh PostProcessing-Settings-Section"""
        # Rev. 2026-01-10
        self.dlg_reset_po_pro_settings()
        self.dlg_populate_po_pro_settings()
        self.dlg_refract_po_pro_settings()

    def stm_pausing(self):
        """sets tool_mode 'pausing'"""
        # Rev. 2026-01-10
        self.sys_set_tool_mode("pausing")

    @staticmethod
    def eval_crs_units(crs: QgsCoordinateReferenceSystem) -> tuple:
        """gets some metadata from (layer/canvas)-crs, depending on geographic (lat/lon) or projected (m)
        used for dialog (unit-widgets, precision) and canvas-zoom-or-pan decisions

        Args:
            crs (QgsCoordinateReferenceSystem):

        Returns:
            tuple(str, int, int) unit, display_precision, measure_default_step
        """
        # Rev. 2026-01-10
        # simple: crs.isGeographic() == True (°, lat/lon) vs. isGeographic() == False (projected CRS), sufficient in 99.9 %
        # for exotic crs:
        mu = crs.mapUnits()
        if mu == Qgis.DistanceUnit.Meters:
            unit = "m"
            display_precision = 2
            measure_default_step = 1
        elif mu == Qgis.DistanceUnit.Kilometers:
            unit = "km"
            display_precision = 3
            measure_default_step = 0.001
        elif mu == Qgis.DistanceUnit.Feet:
            unit = "ft"
            display_precision = 1
            measure_default_step = 1
        elif mu == Qgis.DistanceUnit.NauticalMiles:
            unit = "NM"
            display_precision = 3
            measure_default_step = 0.001
        elif mu == Qgis.DistanceUnit.Yards:
            unit = "yd"
            display_precision = 1
            measure_default_step = 0.001
        elif mu == Qgis.DistanceUnit.Miles:
            unit = "mi"
            display_precision = 3
            measure_default_step = 0.001
        elif mu == Qgis.DistanceUnit.Degrees:
            unit = "°"
            display_precision = 5
            measure_default_step = 0.0001
        elif mu == Qgis.DistanceUnit.Centimeters:
            unit = "cm"
            display_precision = 0
            measure_default_step = 10
        elif mu == Qgis.DistanceUnit.Millimeters:
            unit = "mm"
            display_precision = 0
            measure_default_step = 100
        elif mu == Qgis.DistanceUnit.Inches:
            unit = "in"
            display_precision = 0
            measure_default_step = 10
        else:
            if crs.isGeographic():
                # lat/lon
                unit = "°"
                display_precision = 5
                measure_default_step = 0.0001
            else:
                unit = "m"
                display_precision = 2
                measure_default_step = 1

        return unit, display_precision, measure_default_step

    def cvs_hide_markers(self, hide_markers: list = None, keep_markers: list = None):
        """hide temporary graphics

        Args:
            hide_markers (list, optional): combination of marker-types, if empty: hide all markers. Defaults to None.
                - sn -> stationing point
                - sn_mp -> same for multiple aggregated features
                - en -> stationing point for edit-purpose
                - snf -> from-point
                - snt -> to-point
                - sgn -> segment
                - sg0 -> segment without offset
                - rfl -> reference-line
                - enf -> from-point for edit
                - ent -> to-point for edit
                - caca -> cached stationing on cached reference-line
                - cuca -> current-to-cached-reference-line-differences
                - cacu -> cached-to-current-reference-line-differences
                - rflca -> cached reference-line
                - sg0caca -> cached segment on cached reference line without offset
                - snfcaca -> from-point of cached segment
                - sntcaca -> to-point of cached segment
            keep_markers (list, optional): same marker-types, negative-list for graphics to be kept
        """
        # Rev. 2026-01-10
        if keep_markers is None:
            keep_markers = []

        if not hide_markers:
            # hide all:
            for key, marker in self.canvas_graphics.items():
                if not key in keep_markers:
                    marker.hide()
        else:
            # hide selected
            for key in hide_markers:
                if not key in keep_markers:
                    if self.canvas_graphics.get(key):
                        self.canvas_graphics[key].hide()

        self.canvas_graphics["sel"].hide()
        self.cvs_hide_snap()

    def cvs_hide_snap(self):
        """hides self.snap_indicator by setting invalid match"""
        # Rev. 2026-01-10
        # self.snap_indicator.setMatch(QgsPointLocator.Match())
        self.snap_indicator.setVisible(False)

    def cvs_show_snap(self, match: QgsPointLocator.Match):
        """shows self.snap_indicator

        Args:
            match (QgsPointLocator.Match)
        """
        # Rev. 2026-01-10
        self.snap_indicator.setMatch(match)
        self.snap_indicator.setVisible(True)


    def sys_log_exception(self,e):
        try:
            exception_string = str(e)

            path = pathlib.Path(__file__)
            plugin_folder = str(path.parent.parent.absolute())

            exception_trace = ""
            e_trc = traceback.format_exception(e)
            for trc_idx, trc in enumerate(e_trc):
                # print(type(trc))
                # <class 'str'>
                stripped_trc = trc.replace(plugin_folder, ".")

                exception_trace += f"{trc_idx * " "} {trc_idx} {stripped_trc}"

            print(exception_trace)


            if self.my_dialog:
                self.lmc += 1

                # debug-info
                file, line, function = get_debug_file_line(2)

                self.my_dialog.qtw_log_messages.model().appendRow(
                    [
                        MyLogItem(self.lmc),
                        MyLogItem(QDateTime.currentDateTime()),
                        MyLogItem("EXCEPTION",bg_color='EXCEPTION'),
                        MyLogItem(exception_string,exception_trace),
                        MyLogItem(os.path.basename(file),file),
                        MyLogItem(line),
                        MyLogItem(function),
                    ]
                )

                self.my_dialog.tbw_central.tabBar().setTabTextColor(
                    self.dialog_tabs["message_log"], QColor("red")
                )
                #  and open the message-log-tab
                self.dlg_show_tab("message_log")


            #self.dlg_append_log_message("EXCEPTION", e)
        except Exception as e:
            # Exception while handling Exception:
            self.iface.messageBar().pushMessage(
                "LinearReferencing", str(e), level=Qgis.Critical, duration=20
            )


    def dlg_append_log_message(
        self,
        error_level: str,
        message_content: Any,
        show_status_message: bool = True,
        show_iface_message: bool = False,
    ):
        """appends log-message to self.Dialog.qtw_log_messages
        adds file-name and line-number for debug-convenience
        different message-types are displayed with different durations

        Args:
            error_level (str): INFO/SUCCESS/WARNING/CRITICAL/EXCEPTION, implemented with specific background-colors
            message_content (Any)
            show_status_message (bool, optional): additional show in dialog-status-bar. Defaults to True.
            show_iface_message (bool, optional): additional iface.messageBar().pushMessage(). Defaults to False.
        """
        # Rev. 2026-01-10

        message_string = str(message_content)

        if self.my_dialog:
            # counter-variable and message-range
            self.lmc += 1

            # debug-info
            file, line, function = get_debug_file_line(2)

            self.my_dialog.qtw_log_messages.model().appendRow(
                [
                    MyLogItem(self.lmc),
                    MyLogItem(QDateTime.currentDateTime()),
                    MyLogItem(error_level,bg_color=error_level),
                    MyLogItem(message_string),
                    MyLogItem(os.path.basename(file),file),
                    MyLogItem(line),
                    MyLogItem(function),
                ]
            )




            if error_level in ["WARNING","CRITICAL","EXCEPTION"]:
                # symbolize with red tab-text-color
                self.my_dialog.tbw_central.tabBar().setTabTextColor(
                    self.dialog_tabs["message_log"], QColor("red")
                )
                #  and open the message-log-tab
                self.dlg_show_tab("message_log")



            # Additional output to Dialog-Status-Bar
            if show_status_message:
                self.dlg_show_status_message(error_level, message_string)

            if show_iface_message:
                # append file/line/function for additinal use in messageBar:
                level = Qgis.Info
                duration = 5
                # different background-colors to symbolize message-type
                if error_level == "WARNING":
                    level = Qgis.Warning
                    duration = 10
                elif error_level == "SUCCESS":
                    level = Qgis.Success
                    duration = 5
                elif error_level == "INFO":
                    level = Qgis.Info
                    duration = 5
                elif error_level == "CRITICAL":
                    level = Qgis.Critical
                    duration = 20
                elif error_level == "EXCEPTION":
                    level = Qgis.Warning
                    duration = 10
                iface_message = f"{message_string} (file '{os.path.basename(file)}' line {line} function '{function}')"
                self.iface.messageBar().pushMessage(
                    "LinearReferencing", iface_message, level=level, duration=duration
                )

    def dlg_clear_log_messages(self):
        """method clears qtw_log_messages and resets tabText-content and -color"""
        # Rev. 2026-01-10
        self.my_dialog.qtw_log_messages.model().removeRows(
            0, self.my_dialog.qtw_log_messages.model().rowCount()
        )
        self.my_dialog.tbw_central.tabBar().setTabText(
            self.dialog_tabs["message_log"], MY_DICT.tr("log_tab")
        )
        self.my_dialog.tbw_central.tabBar().setTabTextColor(
            self.dialog_tabs["message_log"], QColor("black")
        )

    def dlg_check_log_messages(self):
        """method removes bold-font from new appended messages and resets tabText-content and -color"""
        # Rev. 2026-01-11
        for rc in range(self.my_dialog.qtw_log_messages.model().rowCount()):
            for cc in range(self.my_dialog.qtw_log_messages.model().columnCount()):
                # apply default-font
                item = self.my_dialog.qtw_log_messages.model().item(rc, cc)
                item.setData(QFont(), Qt.FontRole)

        # reset tab-text (remove *number of new messages)
        self.my_dialog.tbw_central.tabBar().setTabText(
            self.dialog_tabs["message_log"], MY_DICT.tr("log_tab")
        )
        # reset possibly red-tab-text-color of last WARNING or WARNING-Message
        self.my_dialog.tbw_central.tabBar().setTabTextColor(
            self.dialog_tabs["message_log"], QColor("black")
        )

    def cvs_set_extent(
        self,
        extent_mode: str,
        x_coords: list,
        y_coords: list,
        projection: QgsCoordinateReferenceSystem = None,
    ):
        """zooms to combined x_coords/y_coords
        if zoom_xyz and no calculated bounds the extent-mode ist changed to pan_center_xyz

        Args:
            self.iface.mapCanvas() (_type_): usually self.iface.mapCanvas()
            extent_mode (str):
                zoom_bounds => zoom bounds
                zoom_bounds_in => zoom bounds + zoom_in
                zoom_bounds_out => zoom bounds + zoom_out
                zoom_bounds_pan_first => zoom bounds and pan to first coordinate-pair
                zoom_bounds_pan_last => zoom bounds and pan to last coordinate-pair

                pan_center => pan to bounds_center
                pan_center_in => pan to bounds_center + zoom_in
                pan_center_out => pan to bounds_center + zoom_out

                pan_center_opt_in =>  if bounds_center == extent_center => canvas_in, else pan_center
                pan_center_opt_out => if bounds_center == extent_center => canvas_out, else pan_center

                canvas_in => zoom_in current canvas_extent, x_coords/y_coords not required
                canvas_out => zoom_out current canvas_extent, x_coords/y_coords not required
            x_coords (list): list of x-coords, same crs
            y_coords (list): list of y-coords, same crs
            projection (QgsCoordinateReferenceSystem, optional): optional projection of the coordinates (f.e. refLyr), if omitted, canvas-crs is assumed. Defaults to None.

        Raises:
            NotImplementedError: if extent_mode is not implemented
            AttributeError: if x_coords/y_coords is needed but empty
        """
        # Rev. 2026-01-11
        zoom_factor_in = 0.8  # 8 / 10
        zoom_factor_out = 1.25  # Kehrwert, 10 / 8
        # QgsRectangle
        canvas_extent = self.iface.mapCanvas().extent()

        # QgsPointXY
        canvas_center = canvas_extent.center()

        # no coords required
        if extent_mode == "canvas_out":
            self.iface.mapCanvas().zoomByFactor(zoom_factor_out)
        elif extent_mode == "canvas_in":
            self.iface.mapCanvas().zoomByFactor(zoom_factor_in)
        else:
            if x_coords and y_coords:
                x_min = min(x_coords)
                y_min = min(y_coords)
                x_max = max(x_coords)
                y_max = max(y_coords)

                bounds = QgsRectangle(x_min, y_min, x_max, y_max)

                if bounds.isEmpty():
                    # fall-back for empty == single-point-bounds
                    if extent_mode in [
                        "zoom_bounds",
                        "zoom_bounds_pan_first",
                        "zoom_bounds_pan_last",
                    ]:
                        extent_mode = "pan_center"
                    elif extent_mode in ["zoom_bounds_in"]:
                        extent_mode = "pan_center"
                    elif extent_mode in ["zoom_bounds_out"]:
                        extent_mode = "pan_center"
                    # print('bounds is empty')
                    # raise RuntimeError(f"calculated bounds from x_coords/y_coords is empty...")
                    # self.dlg_append_log_message('WARNING', MY_DICT.tr('no_extent_calculable'))

                if projection:
                    tr = QgsCoordinateTransform(
                        projection,
                        self.iface.mapCanvas().mapSettings().destinationCrs(),
                        QgsProject.instance(),
                    )
                    bounds = tr.transformBoundingBox(bounds)

                bounds_center = bounds.center()

                if extent_mode == "zoom_bounds":
                    self.iface.mapCanvas().setExtent(bounds)
                elif extent_mode == "zoom_bounds_in":
                    bounds.scale(zoom_factor_in)
                    self.iface.mapCanvas().setExtent(bounds)
                elif extent_mode == "zoom_bounds_out":
                    bounds.scale(zoom_factor_out)
                    self.iface.mapCanvas().setExtent(bounds)
                elif extent_mode == "zoom_bounds_pan_first":
                    self.iface.mapCanvas().setExtent(bounds)
                    first_x = x_coords[0]
                    first_y = y_coords[0]
                    first_x_point = QgsPointXY(last_x, last_y)
                    if projection:
                        tr = QgsCoordinateTransform(
                            projection,
                            self.iface.mapCanvas().mapSettings().destinationCrs(),
                            QgsProject.instance(),
                        )
                        first_point = tr.transform(first_point)
                    self.iface.mapCanvas().setCenter(first_point)
                elif extent_mode == "zoom_bounds_pan_last":
                    self.iface.mapCanvas().setExtent(bounds)
                    last_x = x_coords[-1]
                    last_y = y_coords[-1]
                    last_point = QgsPointXY(last_x, last_y)
                    if projection:
                        tr = QgsCoordinateTransform(
                            projection,
                            self.iface.mapCanvas().mapSettings().destinationCrs(),
                            QgsProject.instance(),
                        )
                        last_point = tr.transform(last_point)
                    self.iface.mapCanvas().setCenter(last_point)

                elif extent_mode == "pan_center":
                    self.iface.mapCanvas().setCenter(bounds_center)
                elif extent_mode == "pan_center_in":
                    self.iface.mapCanvas().setExtent(
                        canvas_extent.scaled(zoom_factor_in, bounds_center)
                    )
                elif extent_mode == "pan_center_out":
                    self.iface.mapCanvas().setExtent(
                        canvas_extent.scaled(zoom_factor_out, bounds_center)
                    )
                elif extent_mode == "pan_center_opt_in":
                    if canvas_center == bounds_center:
                        self.iface.mapCanvas().setExtent(
                            canvas_extent.scaled(zoom_factor_in, bounds_center)
                        )
                    else:
                        self.iface.mapCanvas().setCenter(bounds_center)
                elif extent_mode == "pan_center_opt_out":
                    if canvas_center == bounds_center:
                        self.iface.mapCanvas().setExtent(
                            canvas_extent.scaled(zoom_factor_out, bounds_center)
                        )
                    else:
                        self.iface.mapCanvas().setCenter(bounds_center)
                elif extent_mode == "canvas_in":
                    self.iface.mapCanvas().zoomByFactor(zoom_factor_in)
                elif extent_mode == "canvas_out":
                    self.iface.mapCanvas().zoomByFactor(zoom_factor_out)
                else:
                    raise NotImplementedError(
                        f"extent_mode '{extent_mode}' not implemented..."
                    )

                self.iface.mapCanvas().refresh()

            else:
                # raise AttributeError(f"missing x_coords/y_coords...")
                pass

    def gui_show_tool_mode(self, tool_mode: str):
        """show tool_mode in dialog and gui
        Args:
            tool_mode (str): self.session_data.tool_mode
        """
        # Rev. 2026-01-11
        # show canvas-cursor dependend on tool-mode:
        tool_mode_metas = self.tool_modes.get(tool_mode)

        if tool_mode_metas:
            tool_tip = f"<b>{tool_mode}:</b><br/>{tool_mode_metas[0]}"
            tool_mode_cursor = tool_mode_metas[1]
            tool_mode_icon = tool_mode_metas[2]
            self.iface.mapCanvas().setCursor(tool_mode_cursor)

            if self.my_dialog:
                self.my_dialog.pbtn_tool_mode_indicator.setToolTip(tool_tip)
                self.my_dialog.pbtn_tool_mode_indicator.setIcon(tool_mode_icon)

    def gui_add_layer_action_zoom_ref_feature(self, vl: QgsVectorLayer):
        """adds or replaces a QgsAction in vector-layer to zoom/pan/highlight feature on map from attribute-table
        same functionality for both MapTools, using the registered reference-layer
        Args:
            vl (QgsVectorLayer)
            mt (str) mt_LolEvt/mt_PolEvt
        """
        # Rev. 2026-01-11
        command = f"""try:
    feature_id=[%@id%]
    layer_id='[%@layer_id%]'
    mt = None
    try:
        mt = qgis.utils.plugins['LinearReferencing'].mt_{type(self).__name__}
    except:
        qgis.utils.iface.messageBar().pushMessage('LinearReferencing-Plugin not loaded/initialized', level=Qgis.Warning)
    if mt:
        # check if called from registered reference-layer
        if layer_id == mt.stored_settings.refLyrId:
            mt.st_zoom_reference_feature(feature_id)
        else:
            qgis.utils.iface.messageBar().pushMessage('LinearReferencing', 'Zoom-Function called from unregistered layer', level=Qgis.Info)
except Exception as e:
    qgis.utils.iface.messageBar().pushMessage('Error in LinearReferencing-Plugin (st_zoom_reference_feature)', f'{{e}}', level=Qgis.Warning)
"""
        if isinstance(vl, QgsVectorLayer):
            # delete existing actions
            action_list = [
                action
                for action in vl.actions().actions()
                if action.id() == self._show_ref_feature_act_id
            ]
            for action in action_list:
                vl.actions().removeAction(action.id())

            show_feature_action = QgsAction(
                self._show_ref_feature_act_id,
                QgsAction.ActionType.GenericPython,
                f"Show feature on map\n[click] → Zoom/Pan\n[shift-click] → zoom-in\n[ctrl-click] → zoom-out\n[shift + ctrl-click] → Flash",
                command,
                ":icons/mIconZoom.svg",
                False,
                "Show feature",
                # 'Feature' => open feature-form from feature-form because of attribute-tables in QgsDualView-mode
                {"Form", "Feature", "Layer"},
                "",
            )

            vl.actions().addAction(show_feature_action)

            atc = vl.attributeTableConfig()
            if not atc.actionWidgetVisible():
                # QgsAttributeTableConfig.ButtonList / QgsAttributeTableConfig.DropDown
                atc.setActionWidgetStyle(QgsAttributeTableConfig.ButtonList)
                atc.setActionWidgetVisible(True)
                vl.setAttributeTableConfig(atc)

            vl.reload()



    def gui_add_layer_action_show_feature_form(self, vl: QgsVectorLayer):
        """adds or replaces a QgsAction in vector-layer to open feature-form from attribute-table
        same functionality for both MapTools and implemented to all registered layers (reference/data/show)
        Args:
            vl (QgsVectorLayer)
        """
        # Rev. 2026-01-11
        command = f"""try:
    feature_id=[%@id%]
    layer_id='[%@layer_id%]'
    mt = None
    try:
        mt = qgis.utils.plugins['LinearReferencing'].mt_{type(self).__name__}
    except:
        qgis.utils.iface.messageBar().pushMessage('LinearReferencing-Plugin not loaded/initialized', level=Qgis.Warning)
    if mt:
        mt.lact_show_feature_form(layer_id,feature_id)
except Exception as e:
    qgis.utils.iface.messageBar().pushMessage('Error in LinearReferencing-Plugin (lact_show_feature_form)', f'{{e}}', level=Qgis.Warning)
"""
        if isinstance(vl, QgsVectorLayer):
            # delete existing actions
            # same action_id as in FileSync
            action_list = [
                action
                for action in vl.actions().actions()
                if action.id() == self._show_feature_form_act_id
            ]
            for action in action_list:
                vl.actions().removeAction(action.id())

            show_feature_form_action = QgsAction(
                self._show_feature_form_act_id,
                QgsAction.ActionType.GenericPython,
                f"Show feature form",
                command,
                ":icons/mActionFormView.svg",
                False,
                "Show feature form",
                # 'Feature' => open feature-form from feature-form because of attribute-tables in QgsDualView-mode
                {"Feature", "Canvas", "Layer"},
                "",
            )

            vl.actions().addAction(show_feature_form_action)

            atc = vl.attributeTableConfig()
            if not atc.actionWidgetVisible():
                # QgsAttributeTableConfig.ButtonList / QgsAttributeTableConfig.DropDown
                atc.setActionWidgetStyle(QgsAttributeTableConfig.ButtonList)
                atc.setActionWidgetVisible(True)
                vl.setAttributeTableConfig(atc)

            vl.reload()

    def lact_show_feature_form(self, layer_id: str, feature_id: int):
        """called from layer-action
        identical implemented in both map-tools
        registered for data/reference/show-layer, but callable from any vector-layer
        Args:
            layer_id (str)
            feature_id (int)
        """
        # Rev. 2026-01-11
        vl = QgsProject.instance().mapLayer(layer_id)
        if vl and isinstance(vl, QgsVectorLayer):
            show_feature_form(self.iface, vl, feature_id)

    def lact_remove_layer_actions(self):
        """removes all actions with the registered action-ids from all vector-layers
        Note:
        used in case of sys_unload, so evtl. triggered identical for LolEvt and PolEvt
        """
        # Rev. 2026-01-11
        for cl in QgsProject.instance().mapLayers().values():
            if cl.type() == Qgis.LayerType.VectorLayer:
                action_found = False
                for action in cl.actions().actions():
                    if action.id() in [
                        self._show_feature_form_act_id,
                        self._show_ref_feature_act_id,
                        self._zoom_lol_feature_act_id,
                        self._zoom_pol_feature_act_id,
                    ]:
                        cl.actions().removeAction(action.id())
                        action_found = True
                # reload to show tables without actions, only if necessary
                if action_found:
                    cl.reload()

    def st_zoom_reference_feature(self, ref_fid: int):
        """zoom to reference-feature in derived_settings.refLyr

        Args:
            ref_fid (int): feature-id
        """
        # Rev. 2026-01-11
        extent_mode = self.tool_get_extent_mode_lol()

        if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            self.cvs_draw_reference_geom(
                ref_fid=ref_fid, extent_mode=extent_mode, flash_geometry=True
            )
            self.dlg_select_feature_selection_row(ref_fid=ref_fid)

    def cvs_draw_reference_geom(
        self,
        ref_id: int | str = None,
        ref_fid: int = None,
        data_fid: int = None,
        extent_mode: str = None,
        flash_geometry: bool = False,
        crs: QgsCoordinateReferenceSystem = None,
    ):
        """draw (highlight), zoom or flash reference-geometry
        Feature can be defined by multiple ways

        Args:
            ref_id (int | str, optional): ID of reference-feature, queried against refLyrIdField. Defaults to None.
            ref_fid (int, optional): Feature-ID of reference-feature. Defaults to None.
            data_fid (int, optional): feature-id of data-feature, subquery to assigened rererence-feature. Defaults to None.
            extent_mode (str, optional):
                zoom_bounds/zoom_bounds_in/zoom_bounds_out pan_center/pan_center_in/pan_center_out pan_center_opt_in/pan_center_opt_out canvas_in/canvas_out.
                see cvs_set_extent.
                Defaults to None.
            flash_geometry (bool, optional): temporary flash effect. Defaults to False.
            crs (QgsCoordinateReferenceSystem, optional): projection of geometry in case of parameters reference_geom/ref_feature. Defaults to None, than self.derived_settings.refLyr.crs() assumed
        """
        # Rev. 2026-01-11
        self.canvas_graphics["rfl"].hide()

        reference_geom = self.tool_get_reference_geom(
            ref_fid, ref_id, data_fid
        )

        if crs is None:
            crs = self.derived_settings.refLyr.crs()

        tr_vl_2_cvs = QgsCoordinateTransform(
            crs,
            self.iface.mapCanvas().mapSettings().destinationCrs(),
            QgsProject.instance(),
        )
        # transform to canvas-crs
        reference_geom.transform(tr_vl_2_cvs)

        if extent_mode:
            extent = reference_geom.boundingBox()
            x_coords = [extent.xMaximum(), extent.xMinimum()]
            y_coords = [extent.yMaximum(), extent.yMinimum()]

            self.cvs_set_extent(
                extent_mode,
                x_coords,
                y_coords,
            )
            self.iface.mapCanvas().refresh()

        self.canvas_graphics["rfl"].setToGeometry(
            reference_geom
        )
        self.canvas_graphics["rfl"].show()

        if flash_geometry:
            self.iface.mapCanvas().flashGeometries([reference_geom])

    def tool_get_reference_geom(
        self,
        ref_fid: int = None,
        ref_id: int | str = None,
        data_fid: int = None,
    ) -> QgsGeometry|None:
        """get geometry by multiple ways

        Args:
            ref_feature (QgsFeature, optional): get geometry from Feature. Defaults to None.
            ref_fid (int, optional): query geometry with QGis-fid. Defaults to None.
            ref_id (int | str, optional): query geometry with registered self.derived_settings.refLyrIdField. Defaults to None.
            data_fid (int, optional): query geometry with fid of data-feature. Defaults to None.

        Returns:
            tuple: QgsGeometry|None
        """
        # Rev. 2026-01-11

        ref_feature = self.tool_get_reference_feature(
            ref_fid, ref_id, data_fid
        )
        return ref_feature.geometry()

    def tool_get_reference_feature(
        self,
        ref_fid: int = None,
        ref_id: int | str = None,
        data_fid: int = None,
    ) -> QgsFeature|None:
        """get reference-feature by multiple ways. Feature mus exist, be valid, and has geometry, else Exceptions
        Args:
            ref_fid (int, optional): query geometry with QGis-fid. Defaults to None.
            ref_id (int | str, optional): query geometry with registered self.derived_settings.refLyrIdField. Defaults to None.
            data_fid (int, optional): query geometry with fid of data-feature. Defaults to None.

        Raises:
            FeatureWithoutGeometryException
            FeatureNotFoundException
            LayerNotRegisteredException

        Returns:
            QgsFeature
        """
        # Rev. 2026-01-11
        if ref_fid is not None:
            if SVS.REFERENCE_LAYER_EXISTS in self.system_vs:
                ref_feature = self.derived_settings.refLyr.getFeature(ref_fid)
                if ref_feature:
                    if ref_feature.isValid() and ref_feature.hasGeometry():
                        return ref_feature
                    else:
                        raise FeatureWithoutGeometryException(self.derived_settings.refLyr.name(),ref_fid)
                else:
                    raise FeatureNotFoundException(self.derived_settings.refLyr.name(),ref_fid)
            else:
                raise LayerNotRegisteredException("RefLyr")

        elif ref_id is not None:
            if SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
                ref_feature = get_feature_by_value(
                    self.derived_settings.refLyr,
                    self.derived_settings.refLyrIdField,
                    ref_id,
                )
                if ref_feature.isValid() and ref_feature.hasGeometry():
                    return ref_feature
                else:
                    raise FeatureWithoutGeometryException(self.derived_settings.refLyr.name(),ref_id)
            else:
                raise LayerNotRegisteredException("RefLyr")

        elif data_fid is not None:
            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                data_feature = self.tool_get_data_feature(data_fid=data_fid)
                ref_id = data_feature[
                    self.derived_settings.dataLyrReferenceField.name()
                ]
                # recursive call with queried ref_id
                return self.tool_get_reference_feature(
                    ref_id=ref_id
                )
            else:
                raise LayerNotRegisteredException("RefLyr + DataLyr")
        else:
            raise ArgumentMissingException("ref_feature/ref_fid/ref_id/data_fid ")



    def tool_get_po_pro_reference_feature(
        self,
        ref_fid: int = None,
        ref_id: int | str = None,
        data_fid: int = None,
    ) -> QgsFeature|None:
        """get Post-Processing-Reference-feature by multiple ways

        Args:
            ref_fid (int, optional): QGis-fid of reference-feature
            ref_id (int | str, optional): registered self.derived_settings.refLyrIdField
            data_fid (int, optional): fid of data-feature

        Returns:
            QgsFeature|None
        """
        # Rev. 2026-01-11
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs:
            # first get reference-feature
            ref_feature = self.tool_get_reference_feature(ref_fid = ref_fid, ref_id=ref_id,data_fid=data_fid)
            ref_id = ref_feature[
                self.derived_settings.refLyrIdField.name()
            ]
            # then get PostProcessing-Cached-Feature
            return get_feature_by_value(
                self.derived_settings.poProRefLyr,
                self.derived_settings.poProRefLyrIdField,
                ref_id,
            )
        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr + PoProLyr")



    def tool_get_data_feature(
        self,
        data_fid: int = None,
        data_id: int | str = None,
        show_fid: int = None,
    ) -> QgsFeature|None:
        """get data-feature
        Args:
            data_fid: fid of data-feature
            data_id: id of data-feature, queried against self.derived_settings.dataLyrIdField
            show_fid: id of show-feature

        Raises:
            LayerNotRegisteredException
            ArgumentMissingException

        Returns:
            QgsFeature | None

        """
        # Rev. 2026-01-11
        if data_fid is not None:
            if SVS.DATA_LAYER_EXISTS in self.system_vs:
                data_feature = self.derived_settings.dataLyr.getFeature(data_fid)
                if data_feature and data_feature.isValid():
                    return data_feature
                else:
                    raise FeatureNotFoundException(self.derived_settings.dataLyr.name(),data_fid)
        elif data_id is not None:
            if (
                SVS.DATA_LAYER_EXISTS | SVS.DATA_LAYER_NECESSARY_FIELDS_DEFINED
            ) in self.system_vs:
                return get_feature_by_value(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyrIdField,
                    data_id,
                )
            else:
                raise LayerNotRegisteredException("DataLyr")

        elif show_fid is not None:
            if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
                show_feature = self.tool_get_show_feature(show_fid=show_fid)
                data_id = show_feature[self.derived_settings.showLyrBackReferenceField.name()]
                return get_feature_by_value(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyrIdField,
                    data_id,
                )
        else:
            raise ArgumentMissingException("data_fid/data_id/show_fid")



    def tool_get_show_feature(
        self,
        show_fid: int = None,
        data_fid: int = None,
        data_id: int | str = None,
    ) -> QgsFeature:
        """get feature from show-layer

        Args:
            show_fid (int, optional): fid of show-feature
            data_fid (int, optional): fid of data-feature
            data_id (int | str, optional): id of data-feature, queried against self.derived_settings.dataLyrIdField

        Returns:
            QgsFeature
        """
        # Rev. 2026-01-11
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            if show_fid is not None:
                show_feature = self.derived_settings.showLyr.getFeature(show_fid)
                if show_feature and show_feature.isValid():
                    return show_feature
                else:
                    raise FeatureNotFoundException(self.derived_settings.showLyr.name(),show_fid)
            elif data_fid is not None:
                if data_fid > 0:
                    data_feature = self.tool_get_data_feature(
                        data_fid=data_fid
                    )
                    data_id = data_feature[self.stored_settings.dataLyrIdFieldName]
                    return get_feature_by_value(
                        self.derived_settings.showLyr,
                        self.derived_settings.showLyrBackReferenceField,
                        data_id,
                    )

            elif data_id is not None:
                data_feature = self.tool_get_data_feature(data_id=data_id)
                data_id = data_feature[self.stored_settings.dataLyrIdFieldName]
                return get_feature_by_value(
                    self.derived_settings.showLyr,
                    self.derived_settings.showLyrBackReferenceField,
                    data_id,
                )
            else:
                raise ArgumentMissingException("data_fid/data_id/show_fid")
        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr + ShowLyr")

    def sys_connect_data_layer_slots(self, data_lyr:QgsVectorLayer):
        """connects dataLyr signals and slots, same in LolEvt/PolEvt

        Args:
            data_lyr (QgsVectorLayer)
        """
        # Rev. 2026-01-11
        # try/catch because of UniqueConnection which ensures no Double-Connects but raises TypeError: connection is not unique
        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.editingStarted.connect(
                    self.ls_data_lyr_editingStarted,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.editingStopped.connect(
                    self.ls_data_lyr_editingStopped,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.editCommandStarted.connect(
                    self.ls_data_lyr_editCommandStarted,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.attributeValueChanged.connect(
                    self.ls_data_lyr_attributeValueChanged,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.editCommandEnded.connect(
                    self.ls_data_lyr_editCommandEnded,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.committedAttributeValuesChanges.connect(
                    self.ls_data_lyr_committedAttributeValuesChanges,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.featuresDeleted.connect(
                    self.ls_data_lyr_featuresDeleted,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.featureAdded.connect(
                    self.ls_data_lyr_featureAdded,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.committedFeaturesAdded.connect(
                    self.ls_data_lyr_committedFeaturesAdded,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.afterCommitChanges.connect(
                    self.ls_data_lyr_afterCommitChanges,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.beforeCommitChanges.connect(
                    self.ls_data_lyr_beforeCommitChanges,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.subsetStringChanged.connect(
                    self.ls_data_lyr_subsetStringChanged,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        try:
            self.signal_slot_cons.data_lyr_connections.append(
                data_lyr.displayExpressionChanged.connect(
                    self.ls_data_lyr_displayExpressionChanged,
                    Qt.UniqueConnection,
                )
            )
        except:
            pass

        self.system_vs |= SVS.DATA_LAYER_SLOTS_CONNECTED



    def sys_connect_po_pro_ref_layer(self):
        """connects the registered self.stored_settings.poProRefLyrId
        """
        # Rev. 2026-01-11
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            pp_ref_lyr = QgsProject.instance().mapLayer(self.stored_settings.poProRefLyrId)
            if pp_ref_lyr:
                if (
                    pp_ref_lyr.isValid()
                    and pp_ref_lyr.type() == Qgis.LayerType.VectorLayer
                    and pp_ref_lyr.dataProvider().wkbType() == self.derived_settings.refLyr.dataProvider().wkbType()
                    and pp_ref_lyr.dataProvider().name() != "virtual"
                    and pp_ref_lyr.crs().isValid()
                    and pp_ref_lyr.crs() == self.derived_settings.refLyr.crs()
                ):

                    self.system_vs |= SVS.PO_PRO_REF_LAYER_EXISTS
                    self.system_vs |= SVS.PO_PRO_REF_LAYER_HAS_SAME_CRS
                    self.system_vs |= SVS.PO_PRO_REF_LAYER_HAS_SAME_GEOMETRY_TYPE

                    self.stored_settings.poProRefLyrId = pp_ref_lyr.id()
                    self.derived_settings.poProRefLyr = pp_ref_lyr

                    if self.stored_settings.poProRefLyrIdFieldName:
                        fnx = (
                            self.derived_settings.poProRefLyr.dataProvider()
                            .fields()
                            .indexOf(self.stored_settings.poProRefLyrIdFieldName)
                        )
                        if (
                            fnx >= 0
                            and
                            self.derived_settings.poProRefLyr.dataProvider()
                            .fields()[fnx]
                            .type()
                            ==
                            self.derived_settings.refLyrIdField.type()

                        ):
                            self.derived_settings.poProRefLyrIdFieldName = (
                                self.derived_settings.poProRefLyr.fields()[
                                    fnx
                                ]
                            )
                            self.derived_settings.poProRefLyrIdField = self.derived_settings.poProRefLyr.fields()[fnx]
                            self.system_vs |= SVS.PO_PRO_REF_LAYER_NECESSARY_FIELDS_DEFINED

                            # double check with combined flag
                            self.system_vs |= SVS.PO_PRO_REF_LAYER_CONNECTED
                else:
                    self.dlg_append_log_message("WARNING",MY_DICT.tr("po_pro_ref_lyr_invalid", pp_ref_lyr.name()))


    def sys_connect_ref_lyr(self) -> None:
        """checks and prepares Reference-Layer via self.stored_settings.refLyrId
        - sets self.derived_settings.refLyr
        - configures and activates canvas-snap-settings for this layer
        signal-slot-connections in the derived classes
        """
        # Rev. 2026-01-11

        pk_field_types = [
            QMetaType.Int,
            QMetaType.UInt,
            QMetaType.LongLong,
            QMetaType.ULongLong,
            QMetaType.QString,
        ]

        linestring_wkb_types = [
            QgsWkbTypes.LineString,
            QgsWkbTypes.MultiLineString,
            QgsWkbTypes.LineStringZ,
            QgsWkbTypes.MultiLineStringZ,
            QgsWkbTypes.LineStringM,
            QgsWkbTypes.MultiLineStringM,
            QgsWkbTypes.LineStringZM,
            QgsWkbTypes.MultiLineStringZM,
        ]

        ref_lyr = QgsProject.instance().mapLayer(self.stored_settings.refLyrId)
        if ref_lyr:
            if (
                ref_lyr.isValid()
                and ref_lyr.type() == Qgis.LayerType.VectorLayer
                and ref_lyr.dataProvider().wkbType() in linestring_wkb_types
                and ref_lyr.dataProvider().name() != "virtual"
            ):

                #self.sys_log_message("INFO",f"reference-layer '{ref_lyr.name()}'")
                self.system_vs |= SVS.REFERENCE_LAYER_EXISTS
                self.system_vs |= SVS.REFERENCE_LAYER_IS_LINESTRING

                self.derived_settings.refLyr = ref_lyr

                self.sys_apply_snapping_config()

                #self.sys_log_message("INFO","Snap-Configuration applied")


                if ref_lyr.crs().isValid():
                    self.system_vs |= SVS.REFERENCE_LAYER_HAS_VALID_CRS
                    linestring_m_types = [
                        QgsWkbTypes.LineStringM,
                        QgsWkbTypes.MultiLineStringM,
                        QgsWkbTypes.LineStringZM,
                        QgsWkbTypes.MultiLineStringZM,
                    ]

                    if ref_lyr.dataProvider().wkbType() in linestring_m_types:
                        self.system_vs |= SVS.REFERENCE_LAYER_M_ENABLED

                    linestring_z_types = [
                        QgsWkbTypes.LineStringZ,
                        QgsWkbTypes.MultiLineStringZ,
                        QgsWkbTypes.LineStringZM,
                        QgsWkbTypes.MultiLineStringZM,
                    ]

                    if ref_lyr.dataProvider().wkbType() in linestring_z_types:
                        self.system_vs |= SVS.REFERENCE_LAYER_Z_ENABLED



                    if self.stored_settings.refLyrIdFieldName:
                        fnx = (
                            self.derived_settings.refLyr.dataProvider()
                            .fields()
                            .indexOf(self.stored_settings.refLyrIdFieldName)
                        )
                        if (
                            fnx >= 0
                            and self.derived_settings.refLyr.dataProvider()
                            .fields()[fnx]
                            .type()
                            in pk_field_types
                        ):
                            self.derived_settings.refLyrIdField = (
                                self.derived_settings.refLyr.dataProvider().fields()[
                                    fnx
                                ]
                            )
                            self.system_vs |= (
                                SVS.REFERENCE_LAYER_NECESSARY_FIELDS_DEFINED
                            )

                            self.gui_add_layer_action_zoom_ref_feature(ref_lyr)
                            self.gui_add_layer_action_show_feature_form(ref_lyr)

                            self.system_vs |= SVS.REFERENCE_LAYER_ACTIONS_ADDED

                            # re-connect and register
                            # try/catch because of UniqueConnection which ensures no Double-Connects but raises TypeError: connection is not unique
                            try:
                                self.signal_slot_cons.ref_lyr_connections.append(
                                    ref_lyr.displayExpressionChanged.connect(
                                        self.ls_ref_lyr_displayExpressionChanged,
                                        Qt.UniqueConnection,
                                    )
                                )
                            except:
                                pass

                            try:
                                self.signal_slot_cons.ref_lyr_connections.append(
                                    ref_lyr.subsetStringChanged.connect(
                                        self.ls_ref_lyr_subsetStringChanged,
                                        Qt.UniqueConnection,
                                    )
                                )
                            except:
                                pass

                            try:
                                self.signal_slot_cons.ref_lyr_connections.append(
                                    ref_lyr.geometryChanged.connect(
                                        self.ls_ref_lyr_geometryChanged,
                                        Qt.UniqueConnection,
                                    )
                                )
                            except:
                                pass



                            self.system_vs |= SVS.REFERENCE_LAYER_ACTIONS_ADDED

                            self.system_vs |= SVS.REFERENCE_LAYER_CONNECTED

                            self.sys_log_message("SUCCESS",f"reference-layer '{ref_lyr.name()}' connected")



                else:
                    self.dlg_append_log_message(
                        "WARNING", MY_DICT.tr("ref_lyr_crs_invalid")
                    )
            else:
                self.dlg_append_log_message(
                    "WARNING",
                    MY_DICT.tr("ref_lyr_invalid", self.stored_settings.refLyrId),
                )
        else:
            # Layer not found => disconnect current assigned reference-layer
            self.sys_disconnect_ref_lyr()

    def sys_disconnect_ref_lyr(self):
        """reverse to sys_connect_reference_lyr
        only disconnects and resets signal_slot_cons.ref_lyr_connections
        keeps stored_settings and derived_settings"""
        # Rev. 2026-01-11
        try:
            if self.derived_settings.refLyr:
                action_ids = [
                    self._zoom_lol_feature_act_id,
                    self._show_feature_form_act_id,
                    self._show_ref_feature_act_id,
                ]
                action_list = [
                    action
                    for action in self.derived_settings.refLyr.actions().actions()
                    if action.id() in action_ids
                ]
                for action in action_list:
                    self.derived_settings.refLyr.actions().removeAction(action.id())

                self.derived_settings.refLyr.reload()

                for conn_id in self.signal_slot_cons.ref_lyr_connections:
                    self.derived_settings.refLyr.disconnect(conn_id)

            self.stored_settings.refLyrId = None
            self.stored_settings.refLyrIdFieldName = None

            self.derived_settings.refLyr = None
            self.derived_settings.refLyrIdField = None
            self.signal_slot_cons.ref_lyr_connections = []

            self.system_vs &= ~SVS.REFERENCE_LAYER_CONNECTED
        except RuntimeError as e:
            # RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
            pass

    def sys_apply_snapping_config(self):
        """applies plugin-defined snap-settings for registered reference-layer
        necessary for most MapTools
        - AdvancedConfiguration
        - self.stored_settings.snapMode
        - self.stored_settings.snapTolerance (units=Qgis.MapToolUnit.Pixels)
        - disables snap to other layers
        """
        # Rev. 2026-01-11
        if self.derived_settings.refLyr:
            current_snap_config = QgsProject.instance().snappingConfig()
            current_snap_config.setEnabled(True)
            current_snap_config.setMode(QgsSnappingConfig.AdvancedConfiguration)

            idv_ls_dict = current_snap_config.individualLayerSettings()

            for c_vl in idv_ls_dict:
                c_idv_ls = idv_ls_dict[c_vl]

                if c_vl == self.derived_settings.refLyr:
                    c_idv_ls.setEnabled(True)
                    c_idv_ls.setTypeFlag(
                        Qgis.SnappingTypes(self.stored_settings.snapMode)
                    )
                    c_idv_ls.setUnits(Qgis.MapToolUnit.Pixels)
                    c_idv_ls.setTolerance(self.stored_settings.snapTolerance)
                else:
                    # only snap to refLyr
                    c_idv_ls.setEnabled(False)

                current_snap_config.setIndividualLayerSettings(c_vl, c_idv_ls)
                current_snap_config.setIntersectionSnapping(False)
                QgsProject.instance().setSnappingConfig(current_snap_config)



    def dlg_show_status_message(self, error_level: str, message_content: Any):
        """displays message in self.my_dialog.status_bar
        style status_bar (color, background-color) dependend on error_level
        starts self.my_dialog.status_bar_timer, which will reset style and clear status_bar after xxx Milliseconds dependend on error_level
        :param error_level: INFO/SUCCESS/WARNING/CRITICAL, according to dlg_append_log_message
        :param message_content:
        """
        # Rev. 2026-01-11
        message_string = str(message_content)
        if self.my_dialog:
            self.my_dialog.status_bar.clearMessage()

            duration_ms = 2500
            css = "QStatusBar {background-color: silver; color: black; font-weight: normal;}"
            if error_level == "INFO":
                duration_ms = 2500
                css = "QStatusBar {background-color: silver; color: black; font-weight: normal;}"

            elif error_level == "SUCCESS":
                duration_ms = 2500
                css = "QStatusBar {background-color: silver; color: green; font-weight: normal;}"

            elif error_level == "WARNING":
                duration_ms = 5000
                css = "QStatusBar {background-color: silver; color: red; font-weight: normal;}"

            elif error_level == "CRITICAL":
                duration_ms = 5000
                css = "QStatusBar {background-color: orange; color: red; font-weight: bolr;}"

            self.my_dialog.status_bar.showMessage(message_string, duration_ms)
            self.my_dialog.status_bar.setStyleSheet(css)
            # QTimer, timeout connected to my_dialog.reset_status_bar, which will reset style and clear contents
            self.my_dialog.status_bar_timer.start(duration_ms)

    def tool_snap_to_ref_layer(self, event: QgsMapMouseEvent) -> tuple|None:
        """snap event-point to any feature in self.derived_settings.refLyr using the map canvas snapping utils configuration, see sys_apply_snapping_config

        Args:
            event (QgsMapMouseEvent)

        Returns:
            tuple(ref_fid:int, snap_n_abs:float, match:QgsPointLocator.Match)|None
        """
        # Rev. 2026-01-11
        # snapPoint will snap the points using the map canvas snapping utils configuration
        event.snapPoint()
        match = event.mapPointMatch()

        # depending on canvas snapping utils configuration multiple layers can be snap-targets
        if match.isValid():
            if match.layer() == self.derived_settings.refLyr:
                # snap occured, but no parameter filter_feature_id or match
                ref_fid = match.featureId()

                # QgsMapMouseEvent => match.point() => QgsPointXY with canvas-crs
                match_point_geom = QgsGeometry.fromPoint(QgsPoint(match.point()))
                match_point_geom.transform(
                    QgsCoordinateTransform(
                        qgis.utils.iface.mapCanvas().mapSettings().destinationCrs(),
                        self.derived_settings.refLyr.crs(),
                        QgsProject.instance(),
                    )
                )

                # calculate natural stationing
                # feature and geometry must exist and be valid, else there was no match
                ref_geom = self.tool_get_reference_geom(ref_fid=ref_fid)
                snap_n_abs = ref_geom.lineLocatePoint(match_point_geom)
                return ref_fid, snap_n_abs, match



    def tool_snap_to_ref_feature(self, event: QgsMapMouseEvent, ref_fid: int) -> float:
        """snap event-point to specific feature in reference-layer
        does *not* use snap-config, but lineLocatePoint, to snap to nearest vertex/edge
        Args:
            event (QgsMapMouseEvent): Mouse-Event on canvas
            ref_fid (int): feature-id from reference-layer

        Returns:
            float: natural stationing of nearest point
        """
        # Rev. 2026-01-11
        reference_geom = self.tool_get_reference_geom(ref_fid=ref_fid)
        if reference_geom:
            return self.tool_snap_to_ref_geom(event, reference_geom)

    def tool_snap_to_ref_geom(
        self, event: QgsMapMouseEvent, ref_geom: QgsGeometry
    ) -> float:
        """snap event-point to reference-geometry
        does *not* use snap-config, but lineLocatePoint, to snap to nearest vertex/edge
        Args:
            event (QgsMapMouseEvent): Mouse-Event on canvas
            ref_geom (QgsGeometry): Geometry, assume having same projection as self.derived_settings.refLyr

        Returns:
            float: natural stationing of nearest point
        """
        # Rev. 2026-01-11
        event_point_geom = QgsGeometry.fromPoint(QgsPoint(event.mapPoint()))
        event_point_geom.transform(
            QgsCoordinateTransform(
                self.iface.mapCanvas().mapSettings().destinationCrs(),
                self.derived_settings.refLyr.crs(),
                QgsProject.instance(),
            )
        )
        return ref_geom.lineLocatePoint(event_point_geom)


    def dlg_reset_po_pro_settings(self):
        """reset settings-area in PostProcessing-Tab"""
        # Rev. 2026-01-12
        if self.my_dialog:
            clear_widgets = [
                self.my_dialog.qcbn_pp_ref_lyr,
                self.my_dialog.qcbn_pp_ref_lyr_id_field,
            ]

            for widget in clear_widgets:
                widget.blockSignals(True)
                widget.clear()
                widget.setEnabled(False)

            self.qact_start_post_processing.setEnabled(False)
            self.qact_open_po_pro_ref_lyr.setEnabled(False)
            self.qact_zoom_po_pro_selection.setEnabled(False)
            self.qact_clear_po_pro_selection.setEnabled(False)

    def sys_create_po_pro_ref_lyr(self,only_assigned:bool = False):
        """create poProRefLyr as cloned self.derived_settings.refLyr

        Args:
            only_assigned (bool, optional): Only assigend or all reference-features. Defaults to False.
        """
        # Rev. 2026-01-12
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:

            if only_assigned:
                # clone only assigned features,
                # pros: smaller layer
                # cons: resulting-layer only usable for Pol rsp. Lol, because they may have different assignments
                data_lyr_ref_ids = get_field_values(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyrReferenceField,
                )
                ref_lyr_ref_ids = get_field_values(
                    self.derived_settings.refLyr, self.derived_settings.refLyrIdField
                )

                common_ref_ids = ref_lyr_ref_ids.intersection(data_lyr_ref_ids)


                if common_ref_ids:

                    # warn missing references
                    if common_ref_ids != data_lyr_ref_ids:
                        missing_ref_ids = data_lyr_ref_ids - common_ref_ids
                        self.dlg_append_log_message(
                            "INFO", MY_DICT.tr("po_pro_missing_reference_ids", missing_ref_ids)
                        )

                    ref_lyr_fids = []
                    for ref_id in common_ref_ids:
                        ref_feature = get_feature_by_value(
                            self.derived_settings.refLyr,
                            self.derived_settings.refLyrIdField,
                            ref_id,
                        )
                        ref_lyr_fids.append(ref_feature.id())

                    # materialize => cloned scratch-layer, same crs/type/fields
                    po_pro_ref_lyr = self.derived_settings.refLyr.materialize(
                        QgsFeatureRequest().setFilterFids(ref_lyr_fids)
                    )
                else:
                    # either empty DataLyr or empty RefLyr or no valid assignments
                    raise LayerCreateException("PoProRefLyr","no assigned reference features")
            else:
                # full-clone with all reference-features
                po_pro_ref_lyr = self.derived_settings.refLyr.materialize(QgsFeatureRequest())


            layer_names = [
                layer.name() for layer in QgsProject.instance().mapLayers().values()
            ]
            template = (
                f"Cached RefLyr [{{curr_i}}] '{self.derived_settings.refLyr.name()}' (memory)"
            )
            po_pro_ref_lyr_name = get_unique_string(layer_names, template, 1)

            po_pro_ref_lyr.setName(po_pro_ref_lyr_name)

            QgsProject.instance().addMapLayer(po_pro_ref_lyr)
            po_pro_ref_lyr_id_field = po_pro_ref_lyr.fields().field(
                self.derived_settings.refLyrIdField.name()
            )
            self.stored_settings.poProRefLyrId = po_pro_ref_lyr.id()
            self.stored_settings.poProRefLyrIdFieldName = po_pro_ref_lyr_id_field.name()
            self.sys_restart_session()

            self.dlg_append_log_message(
                "SUCCESS", MY_DICT.tr("po_pro_ref_lyr_created")
            )


    def s_append_to_feature_selection(self):
        """Adds features from dataLyr to self.session_data.selected_data_fids"""
        # Rev. 2026-01-12
        try:
            selection_mode = "select_all"
            if check_mods("sc"):
                selection_mode = "remove_selected"
            elif check_mods("s"):
                selection_mode = "append_selected"
            elif check_mods("c"):
                selection_mode = "select_selected"

            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                current_selection_set = set(
                    self.derived_settings.dataLyr.selectedFeatureIds()
                )

                complete_set = {f.id() for f in self.derived_settings.dataLyr.getFeatures()}

                if selection_mode == "select_all":
                    self.session_data.selected_data_fids = complete_set

                elif selection_mode == "select_selected":
                    self.session_data.selected_data_fids = current_selection_set

                elif selection_mode == "remove_selected":
                    self.session_data.selected_data_fids -= current_selection_set

                else:
                    # or selection_mode == 'append_selected':
                    self.session_data.selected_data_fids |= current_selection_set

                self.dlg_refresh_feature_selection()
            else:
                raise LayerNotRegisteredException("RefLyr + DataLyr")
        except Exception as e:
            self.sys_log_exception(e)


    def s_select_current_ref_fid(self):
        """highlights and optionally zooms to the current selected Reference-Feature,
        triggered by currentIndexChanged on qcbn_ref_lyr_select (QComboBoxN)"""
        # Rev. 2026-01-12

        # default: no zoom if scrolled through QComboBoxN without modifier
        try:
            extent_mode = None
            if check_mods("s") or check_mods("c"):
                extent_mode = "zoom_bounds_out"

            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                ref_fid = self.my_dialog.qcbn_ref_lyr_select.currentData(Qt_Roles.REF_FID)
                if ref_fid is not None:
                    self.cvs_draw_reference_geom(
                        ref_fid=ref_fid, extent_mode=extent_mode, flash_geometry=True
                    )
                else:
                    pass
                    #raise UserSelectionException("Reference-Feature")
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_select_in_ref_layer(self):
        """selects current_ref_fid (current selected Reference-Feature in qcbn_ref_lyr_select) in reference-layer"""
        # Rev. 2026-01-12
        try:
            ref_fid = self.my_dialog.qcbn_ref_lyr_select.currentData(Qt_Roles.REF_FID)
            if ref_fid is not None:
                select_in_layer(self.stored_settings.refLyrId, ref_fid, self.iface)
            else:
                raise NotInSelectionException("Reference-Selection",ref_fid)
        except Exception as e:
            self.sys_log_exception(e)


    def cvs_zoom_current_ref_fid(self):
        """highlights and zooms current_ref_fid (current selected Reference-Feature in qcbn_ref_lyr_select)"""
        # Rev. 2026-01-12
        try:
            ref_fid = self.my_dialog.qcbn_ref_lyr_select.currentData(Qt_Roles.REF_FID)
            if ref_fid is not None:
                self.st_zoom_reference_feature(ref_fid)
            else:
                raise NotInSelectionException("Reference-Selection",ref_fid)
        except Exception as e:
            self.sys_log_exception(e)




    def s_clear_feature_selection(self):
        """clear self.session_data.selected_data_fids, refresh Feature-Selection"""
        # Rev. 2026-01-12
        try:
            self.cvs_hide_markers()
            self.session_data.selected_data_fids = set()
            self.dlg_refresh_feature_selection()
        except Exception as e:
            self.sys_log_exception(e)

    def s_toggle_edit_mode(self):
        """toggles data-layer-edit-mode"""
        # Rev. 2026-01-12
        try:
            if SVS.DATA_LAYER_UPDATE_ENABLED in self.system_vs:
                if SVS.DATA_LAYER_EDITABLE in self.system_vs:
                    # yes/no/cancel-dialog to store edits
                    self.iface.vectorLayerTools().stopEditing(self.derived_settings.dataLyr)
                else:
                    self.iface.vectorLayerTools().startEditing(
                        self.derived_settings.dataLyr
                    )
        except Exception as e:
            self.sys_log_exception(e)

    def s_filter_data_lyr(self):
        """creates a filter-query on data-layer (provider-side) for the current selected features
        show-layers using data-layer are filtered too
        ctrl-click removes filter"""
        # Rev. 2026-01-12
        try:
            # Note: layers are not filterable if in edit-mode
            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                if not SVS.DATA_LAYER_EDITABLE in self.system_vs:
                    if check_mods("c"):
                        # [ctrl-click] => remove any filter
                        self.derived_settings.dataLyr.setSubsetString("")
                    else:
                        if self.session_data.selected_data_fids:
                            # Note:
                            # the subset is a provider-side-query-expression, so it must use the *provider*-side-ID-field, not the QGis internal feature-id
                            data_ids = set()
                            fail_data_fids = set()
                            for data_fid in self.session_data.selected_data_fids:
                                try:
                                    data_feature = self.tool_get_data_feature(
                                        data_fid=data_fid
                                    )
                                    data_ids.add(
                                        data_feature[
                                            self.derived_settings.dataLyrIdField.name()
                                        ]
                                    )
                                except Exception as e:
                                    fail_data_fids.add(data_fid)

                            if data_ids:
                                # tricky: {tuple(list)} => round brackets, string-ids automatically enquoted
                                filter_expression = f'"{self.derived_settings.dataLyrIdField.name()}" in {tuple(data_ids)}'
                                # leider bleibt bei nur einem Element sowas wie "ID in (1,)"
                                filter_expression = re.sub(",\)$", ")", filter_expression)

                                self.derived_settings.dataLyr.setSubsetString(filter_expression)

                            if fail_data_fids:
                                self.dlg_append_log_message(
                                    "INFO", MY_DICT.tr("feature_selection_fail_data_fids", fail_data_fids)
                                )
                                #self.session_data.selected_data_fids -= fail_data_fids
                                #self.dlg_refresh_feature_selection()


                        else:
                            # currently no features in selection => remove filter
                            self.derived_settings.dataLyr.setSubsetString("")
                else:
                    raise LayerIsEditableException(self.derived_settings.refLyr.name(),"add filter not allowed on editable layers")
        except Exception as e:
            self.sys_log_exception(e)

    def s_transfer_feature_selection(self):
        """transfer complete feature-selection to data- and show-layer"""
        # Rev. 2026-01-12
        try:
            self.cvs_hide_markers()

            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:

                selection_mode = "replace_selection"
                if check_mods("c"):
                    selection_mode = "remove_from_selection"
                elif check_mods("s"):
                    selection_mode = "add_to_selection"

                if self.session_data.selected_data_fids:
                    # same feature in data-layer and show-layer can have different fids
                    show_fids = set()
                    if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                        for data_fid in self.session_data.selected_data_fids:
                            try:
                                show_feature = self.tool_get_show_feature(
                                    data_fid=data_fid
                                )
                                show_fids.add(show_feature.id())
                            except Exception as e:
                                pass

                    if selection_mode == "replace_selection":
                        self.derived_settings.dataLyr.removeSelection()
                        self.derived_settings.dataLyr.select(
                            list(self.session_data.selected_data_fids)
                        )
                        if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                            self.derived_settings.showLyr.removeSelection()
                            self.derived_settings.showLyr.select(list(show_fids))
                    elif selection_mode == "remove_from_selection":
                        self.derived_settings.dataLyr.deselect(
                            list(self.session_data.selected_data_fids)
                        )
                        if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                            self.derived_settings.showLyr.deselect(list(show_fids))
                    else:
                        self.derived_settings.dataLyr.select(
                            list(self.session_data.selected_data_fids)
                        )
                        if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                            self.derived_settings.showLyr.select(list(show_fids))

                else:
                    raise IterableEmptyException("Feature-Selection")
            else:
                raise LayerNotRegisteredException("RefLyr + DataLyr")
        except Exception as e:
            self.sys_log_exception(e)



    def s_start_post_processing(self):
        """start PostProcessing"""
        # Rev. 2026-01-12
        try:
            self.cvs_hide_markers()
            self.session_data.po_pro_feature = None
            self.dlg_reset_po_pro_edit()
            self.sys_refresh_po_pro_cache()
            self.dlg_refresh_po_pro_selection()
            self.dlg_refract_po_pro_settings()
        except Exception as e:
            self.sys_log_exception(e)

    def s_save_po_pro_feature(self):
        """save self.session_data.po_pro_feature to data-layer"""
        # Rev. 2026-01-13
        try:
            self.cvs_hide_markers()
            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                if (
                    SVS.DATA_LAYER_UPDATE_ENABLED
                    | SVS.DATA_LAYER_EDITABLE
                ) in self.system_vs:
                    if self.session_data.po_pro_feature is not None:

                        update_result = self.sys_save_feature(
                            self.session_data.po_pro_feature.data_fid,
                            self.session_data.po_pro_feature.lr_geom_current
                        )
                        if update_result:
                            self.dlg_append_log_message(
                                "SUCCESS", MY_DICT.tr("feature_update_successfull")
                            )

                        else:
                            raise FeatureUpdateException(self.derived_settings.dataLyr.name(),self.session_data.po_pro_feature.data_fid)

                        self.cvs_show_po_pro_difference(self.session_data.po_pro_feature)
                        self.dlg_select_po_pro_selection_row(
                            data_fid=self.session_data.po_pro_feature.data_fid
                        )

                    else:
                        raise PropMissingException("po_pro_feature")
                else:
                    raise LayerNotEditableException(self.derived_settings.dataLyr.name())

                self.dlg_refresh_po_pro_edit()
                self.qact_pausing.trigger()
            else:
                raise LayerNotRegisteredException("RefLyr + DataLyr")

        except Exception as e:
            self.sys_log_exception(e)

    def s_open_ref_form(self):
        """open attribute-form for selected reference-feature in qcbn_ref_lyr_select"""
        # Rev. 2026-01-12
        try:
            ref_fid = self.my_dialog.qcbn_ref_lyr_select.currentData(Qt_Roles.REF_FID)
            if ref_fid is not None:
                self.lact_show_feature_form(self.stored_settings.refLyrId, ref_fid)
            else:
                raise UserSelectionException("Reference-Feature")
        except Exception as e:
            self.sys_log_exception(e)


    def s_open_show_tbl(self):
        """opens the Show-Layer-attribute-table"""
        # Rev. 2026-01-12
        if SVS.SHOW_LAYER_EXISTS in self.system_vs:
            open_attribute_table(self.iface, self.derived_settings.showLyr)

    def s_open_data_tbl(self):
        """opens the Data-Layer-attribute-table"""
        # Rev. 2026-01-12
        try:
            open_attribute_table(self.iface, self.derived_settings.dataLyr)
        except Exception as e:
            self.sys_log_exception(e)

    def s_open_ref_tbl(self):
        """opens the Reference-Layer-attribute-table"""
        # Rev. 2026-01-12
        try:
            open_attribute_table(self.iface, self.derived_settings.refLyr)
        except Exception as e:
            self.sys_log_exception(e)

    def s_open_po_pro_ref_lyr_tbl(self):
        """opens the PostProcessing-Reference-Layer-attribute-table"""
        # Rev. 2026-01-12
        try:
            open_attribute_table(self.iface, self.derived_settings.poProRefLyr)
        except Exception as e:
            self.sys_log_exception(e)

    def s_define_ref_lyr_display_expression(self):
        """opens the dialog for editing the displayExpression of Reference-Layer
        if expression is accepeted the displayExpressionChanged-Signal-Slot will be triggered
        """
        # Rev. 2026-01-12
        try:
            if SVS.REFERENCE_LAYER_USABLE in self.system_vs:
                dlg = QgsExpressionBuilderDialog(
                    self.derived_settings.refLyr,
                    self.derived_settings.refLyr.displayExpression(),
                )
                dlg.setWindowTitle(
                    MY_DICT.tr(
                        "edit_display_exp_dlg_title", self.derived_settings.refLyr.name()
                    )
                )
                exec_result = dlg.exec()
                if exec_result:
                    # expressionBuilder -> https://api.qgis.org/api/classQgsExpressionBuilderWidget.html
                    if dlg.expressionBuilder().isExpressionValid():
                        self.derived_settings.refLyr.setDisplayExpression(
                            dlg.expressionText()
                        )
                        self.dlg_append_log_message(
                            "SUCCESS",
                            MY_DICT.tr(
                                "display_exp_valid", self.derived_settings.refLyr.name()
                            ),
                        )
                        # dialog-refresh is done by trigger
                    else:
                        raise LayerExpressionInvalidException(self.derived_settings.refLyr.name())
            else:
                raise LayerNotRegisteredException("RefLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def s_define_data_lyr_display_expression(self):
        """opens the dialog for editing the displayExpression of Data-Layer
        if expression is accepeted the displayExpressionChanged-Signal-Slot will be triggered
        """
        # Rev. 2026-01-12
        try:
            if SVS.DATA_LAYER_EXISTS in self.system_vs:
                dlg = QgsExpressionBuilderDialog(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyr.displayExpression(),
                )
                dlg.setWindowTitle(
                    MY_DICT.tr(
                        "edit_display_exp_dlg_title", self.derived_settings.dataLyr.name()
                    )
                )
                exec_result = dlg.exec()
                if exec_result:
                    if dlg.expressionBuilder().isExpressionValid():
                        self.derived_settings.dataLyr.setDisplayExpression(
                            dlg.expressionText()
                        )
                        self.dlg_append_log_message(
                            "SUCCESS",
                            MY_DICT.tr(
                                "display_exp_valid", self.derived_settings.dataLyr.name()
                            ),
                        )
                        # dialog-refresh is done by trigger
                    else:
                        raise LayerExpressionInvalidException(self.derived_settings.dataLyr.name())
            else:
                raise LayerNotRegisteredException("DataLyr")
        except Exception as e:
            self.sys_log_exception(e)

    def st_delete_data_feature(self, data_fid):
        """deleted feature from dataLyr, triggered from Feature-Selection"""
        # Rev. 2026-01-12
        try:
            if (
                SVS.DATA_LAYER_EXISTS
                | SVS.DATA_LAYER_EDITABLE
                | SVS.DATA_LAYER_DELETE_ENABLED
            ) in self.system_vs:
                data_feature = self.tool_get_data_feature(data_fid=data_fid)

                dialog_result = QMessageBox.question(
                    None,
                    f"LinearReferencing ({get_debug_pos()})",
                    MY_DICT.tr("delete_feature", data_fid),
                    buttons=QMessageBox.Yes | QMessageBox.No,
                    defaultButton=QMessageBox.Yes,
                )

                if dialog_result == QMessageBox.Yes:
                    # still inside edit-buffer, no commit
                    self.derived_settings.dataLyr.beginEditCommand(
                        "st_delete_feature"
                    )
                    self.derived_settings.dataLyr.deleteFeature(data_fid)
                    self.derived_settings.dataLyr.endEditCommand()
            else:
                raise LayerNotEditableException(self.derived_settings.dataLyr.name())
        except Exception as e:
            self.sys_log_exception(e)



    def scc_lr_mode(self) -> None:
        """changes lr_mode, type of stationing-storage, in QComboBox,
        stored in settings
        affects stationings on update/insert by this plugin
        """
        # Rev. 2026-01-12
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            lr_mode = self.my_dialog.qcb_lr_mode.currentData()
            if (
                lr_mode == "Mabs"
                and not SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs
            ):
                # double check: this option only exists in dialog, if the layer is M-enabled
                self.dlg_append_log_message(
                    "WARNING", MY_DICT.tr("ref_lyr_not_m_enabled")
                )
                return

            if lr_mode != self.stored_settings.lrMode:
                if (
                    self.derived_settings.dataLyr
                    and self.derived_settings.dataLyr.featureCount()
                ):

                    self.dlg_append_log_message(
                        "WARNING", MY_DICT.tr("lr_mode_switch_affects_map_positions")
                    )

                if self.derived_settings.showLyr:
                    self.dlg_append_log_message(
                        "WARNING", MY_DICT.tr("lr_mode_switch_disconnects_show_lyr")
                    )
                    self.sys_disconnect_show_lyr()

                self.stored_settings.lrMode = lr_mode

                # the change of the lrMode makes the previous created/selected showLyr no more suitable => disconnect
                self.sys_restore_derived_settings()

                self.dlg_refract_measurement()
                # refresh the list of selectable show-layers
                self.dlg_populate_settings()
                # changed lr_mode requires validation
                self.dlg_refresh_feature_selection()

                self.cvs_hide_markers()

    def scc_storage_precision(self) -> None:
        """changes storage-precision of Data-Layer in QComboBox,
        stored in settings
        affects stationings on update/insert by this plugin and display-preciosion of some table-widgets
        value-range in dialog from -1 (max. precision, no rounding) ... 8
        """
        # Rev. 2026-01-12
        self.stored_settings.storagePrecision = self.my_dialog.qcb_storage_precision.currentData()

    def scc_display_precision(self) -> None:
        """changes display-precision of Data-Layer in QComboBox,
        stored in settings
        affects stationings on update/insert by this plugin and display-preciosion of some table-widgets
        value-range in dialog from 0 ... 8
        """
        # Rev. 2026-01-12
        self.stored_settings.displayPrecision = self.my_dialog.qcb_display_precision.currentData()
        self.dlg_apply_number_format()

    def ssc_show_layer_back_reference_field(self) -> None:
        """change Back-Reference-Field of N-Show-Layer in QComboBox"""
        # Rev. 2026-01-12
        self.stored_settings.showLyrBackReferenceFieldName = self.my_dialog.qcbn_show_lyr_back_reference_field.currentData(
            Qt_Roles.RETURN_VALUE
        )

        self.sys_restart_session()

    def ssc_data_lyr_id_field(self) -> None:
        """change ID-field for Data-Layer in QComboBox"""
        # Rev. 2026-01-12
        self.stored_settings.dataLyrIdFieldName = self.my_dialog.qcbn_data_lyr_id_field.currentData(Qt_Roles.RETURN_VALUE)

        self.sys_restart_session()

    def scc_change_snap_tolerance(self, i: int) -> None:
        """triggered by valueChanged of qsb_snap_tolerance
        value-range: positive integer
        Args:
            i (int): new value
        """
        # Rev. 2026-01-12
        self.stored_settings.snapTolerance = i
        self.sys_apply_snapping_config()

    def ls_ref_lyr_displayExpressionChanged(self):
        """display-expression for reference-layer was altered"""
        # Rev. 2026-01-12
        self.dlg_refresh_feature_selection()
        self.dlg_refresh_ref_lyr_select()

    def ls_data_lyr_displayExpressionChanged(self):
        """layers display-expression has changed => refresh feature-selection"""
        # Rev. 2026-01-12
        self.dlg_refresh_feature_selection()
        self.dlg_refresh_measurement()
        self.dlg_refresh_po_pro_selection()
        self.dlg_refresh_po_pro_edit()

    def dlg_refresh_feature_selection(self):
        """wrapper to refresh feature-selection-widget"""
        # Rev. 2026-01-12
        self.dlg_reset_feature_selection()
        self.dlg_populate_feature_selection()
        self.dlg_refract_feature_selection()

    def ls_data_lyr_editingStopped(self):
        """Emitted *after* editing-session on this layer has ended.
        """
        # Rev. 2026-01-12

        self.system_vs &= ~SVS.DATA_LAYER_EDITABLE
        self.dlg_refract_measurement()
        self.dlg_refract_feature_selection()
        self.dlg_refract_po_pro_selection()
        self.dlg_refract_po_pro_edit()

        if self.derived_settings.showLyr:
            self.derived_settings.showLyr.updateExtents()

        # self.my_dialog.pbtn_insert_stationing.setEnabled(False)


    def st_select_po_pro_ref_feature(self, ref_id: str | int):
        """select/unselect features in table/layer by reference-id in refLyr/poProRefLyr

        Args:
            ref_id (str|int): ID (not feature.id())
        """
        # Rev. 2026-01-12
        try:
            if (
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED
                in self.system_vs
            ):
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
                if check_mods("c"):
                    # [ctrl] => remove from selection
                    self.derived_settings.refLyr.deselect(ref_feature.id())
                    self.derived_settings.poProRefLyr.deselect(
                        po_pro_ref_feature.id()
                    )
                elif check_mods("s"):
                    # [shift] => add to selection
                    self.derived_settings.refLyr.select(ref_feature.id())
                    self.derived_settings.poProRefLyr.select(
                        po_pro_ref_feature.id()
                    )
                else:
                    # no modifier => replace selection
                    self.derived_settings.refLyr.removeSelection()
                    self.derived_settings.poProRefLyr.removeSelection()
                    self.derived_settings.refLyr.select(ref_feature.id())
                    self.derived_settings.poProRefLyr.select(
                        po_pro_ref_feature.id()
                    )

            self.qact_pausing.trigger()

        except Exception as e:
            self.sys_log_exception(e)


    def st_zoom_po_pro_ref_feature(self, ref_id: str | int):
        """Zoom to reference-feature poPro-reference-feature

        Args:
            ref_id (str|int): ID (not feature.id())
        """
        # Rev. 2026-01-12
        self.cvs_hide_markers()

        extent_mode = self.tool_get_extent_mode_lol()

        if (
            SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED
            in self.system_vs
        ):
            reference_geom = self.tool_get_reference_geom(ref_id=ref_id)
            po_pro_ref_feature = get_feature_by_value(
                self.derived_settings.poProRefLyr,
                self.derived_settings.poProRefLyrIdField,
                ref_id,
            )
            if po_pro_ref_feature.hasGeometry():
                po_pro_reference_geom = po_pro_ref_feature.geometry()
                tr_vl_2_cvs = QgsCoordinateTransform(
                    self.derived_settings.refLyr.crs(),
                    self.iface.mapCanvas().mapSettings().destinationCrs(),
                    QgsProject.instance(),
                )
                reference_geom.transform(tr_vl_2_cvs)
                po_pro_reference_geom.transform(tr_vl_2_cvs)

                if extent_mode:
                    ref_extent = reference_geom.boundingBox()
                    po_pro_extent = po_pro_reference_geom.boundingBox()
                    x_coords = [
                        ref_extent.xMaximum(),
                        ref_extent.xMinimum(),
                        po_pro_extent.xMaximum(),
                        po_pro_extent.xMinimum(),
                    ]
                    y_coords = [
                        ref_extent.yMaximum(),
                        ref_extent.yMinimum(),
                        po_pro_extent.yMaximum(),
                        po_pro_extent.yMinimum(),
                    ]

                    self.cvs_set_extent(
                        extent_mode,
                        x_coords,
                        y_coords,
                    )
                    self.iface.mapCanvas().refresh()

                self.canvas_graphics["rfl"].setToGeometry(reference_geom)
                self.canvas_graphics["rfl"].show()

                self.canvas_graphics["rflca"].setToGeometry(
                    po_pro_reference_geom
                )
                self.canvas_graphics["rflca"].show()

                self.iface.mapCanvas().flashGeometries(
                    [reference_geom, po_pro_reference_geom]
                )

            else:
                raise FeatureWithoutGeometryException(self.derived_settings.poProRefLyr.name(),ref_id)

        self.qact_pausing.trigger()



    def ls_data_lyr_featuresDeleted(self, fids: list):
        """Emitted when a feature has been deleted.
        Also on commit of a new uncommitted feature (feature with negative fid gets deleted, a copy with positive incremented fid will be inserted).
        emitted only once
        usage:
            scan fids to check if one is currently contained in selected_data_fids (and listed in qtrv_feature_selection)
            remove this fid from selected_data_fids
            after scan: refresh afterwards to reflect all deletes if necessary
        Note:
            monitors feature-deletes in edit-buffer, which must not be committed
        Note 2: the similar featureDelete-signal for single-feature-deletes is not connected

        Args:
            fid (int): fid of deleted features
        """
        # Rev. 2026-01-12
        if self.my_dialog:

            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:

                if self.session_data.committ_pending:
                    self.session_data.last_deleted_fids = [
                        fid for fid in fids if fid < 0
                    ]

                dif_select = self.session_data.selected_data_fids - set(fids)
                if (
                    len(dif_select) < len(self.session_data.selected_data_fids)
                    and not self.session_data.committ_pending
                ):
                    # no refresh if a committ is running, because there may be many deleted uncommitted features and the feature-selection will be refreshed once after all committs
                    self.session_data.selected_data_fids = dif_select
                    self.dlg_refresh_feature_selection()


                if (
                    self.session_data.edit_feature_fid in fids
                ):
                    self.cvs_hide_markers()
                    self.session_data.edit_feature_fid = None
                    self.dlg_reset_measurement()

                if (
                    self.session_data.po_pro_feature
                    and self.session_data.po_pro_feature.data_fid in fids
                ):
                    self.cvs_hide_markers()
                    self.session_data.po_pro_feature = None
                    self.dlg_reset_po_pro_edit()

    def ls_data_lyr_committedFeaturesAdded(self, layer_id: str, added_features: list):
        """triggered on save of new features from editBuffer to provider
        this will trigger some connected signals in the further course

        featuresDeleted => buffered features with negative fid will get deleted
        featureAdded => copies of the previously deleted features are added with positive incremented fid

        Args:
            layer_id (str): id of the layer, not necessary here, because exclusively connected to dataLyr
            added_features (list)
        """
        # Rev. 2026-01-12
        if self.session_data.committ_pending:
            self.session_data.last_committed_fids = [
                added_feature.id() for added_feature in added_features
            ]
            self.session_data.last_selected_fids = list(
                self.session_data.selected_data_fids
            )
            self.session_data.last_deleted_fids = []

    def ls_data_lyr_beforeCommitChanges(self):
        """triggered on committ *before* data is saved to provider
        used here to set self.session_data.committ_pending as flag for featureAdded and featuresDeleted slots in the further course
        """
        # Rev. 2026-01-12
        # reset cache:
        self.session_data.last_selected_fids = []
        self.session_data.last_committed_fids = []
        self.session_data.last_deleted_fids = []
        # set flag:
        self.session_data.committ_pending = True

    def ls_data_lyr_afterCommitChanges(self):
        """triggered after all changes from editBuffer are saved to provider
        usage here:
        check...
        are new features added (negative fid)?
        have these been previously listed in feature-selection?
        if so:
        add the new feature-ids (now positive) to feature selection
        refresh the dialog
        """
        # Rev. 2026-01-12
        if (
            self.session_data.committ_pending
            and self.session_data.last_selected_fids
            and self.session_data.last_committed_fids
            and self.session_data.last_deleted_fids
        ):

            # dict, key: old_fid (negative) value: new_fid (positive)
            mapped_fids = dict(
                zip(
                    self.session_data.last_deleted_fids,
                    self.session_data.last_committed_fids,
                )
            )

            for old_fid, new_fid in mapped_fids.items():
                if old_fid in self.session_data.last_selected_fids:
                    self.session_data.selected_data_fids.add(new_fid)

            self.dlg_refresh_feature_selection()

        # reset commit-cache
        self.session_data.last_selected_fids = []
        self.session_data.last_committed_fids = []
        self.session_data.last_deleted_fids = []
        # and flag
        self.session_data.committ_pending = False

    def ls_data_lyr_featureAdded(self, fid: int):
        """Emitted when a new feature has been added to the layer.
        Also on commit of a new uncommitted feature (feature with negative fid gets deleted, a copy with positive incremented fid will be inserted).

        Args:
            fid (int): fid of new feature, always negative
        """
        # Rev. 2026-01-12

        if self.my_dialog:
            # "normal" featureAdded, not triggered by committ of so far uncommitted features
            if not self.session_data.committ_pending:

                if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                    # append new feature to selection...
                    self.tool_append_to_feature_selection(fid, True)
                    self.dlg_refresh_feature_selection()

    def ls_ref_lyr_subsetStringChanged(self):
        """reference-layer filter has changed => refresh all affected dialog-widgets"""
        # Rev. 2026-01-12
        self.dlg_refresh_feature_selection()
        self.dlg_refresh_po_pro_selection()
        self.dlg_refresh_po_pro_edit()
        self.dlg_refresh_measurement()
        self.dlg_refresh_ref_lyr_select()





    def ls_ref_lyr_geometryChanged(self, fid: int, geometry: QgsGeometry):
        """triggered by geometry-edits in reference-layer in edit-buffer, also if these edits were not saved at the end of the edit-session

        if the referenced-geometry of lr_geom or used in feature-selection has changed, the assigned linear referenced geometries must be recalculated and can get invalid,
        f. e. if a linear referenced point positioned at the end and the reference-geometry was shortened


        Args:
            fid (int): edited feature-id
            geometry (QgsGeometry): altered Geometry
        """
        # Rev. 2026-01-12
        self.cvs_hide_markers()

        affected_lrefs_found = False

        # Check 1: is this reference-id shown in current feature-selection?
        if self.my_dialog and self.my_dialog.qtrv_feature_selection.model():
            model = self.my_dialog.qtrv_feature_selection.model()

            matches = model.match(
                # search in column 0
                model.index(0, 0),
                Qt_Roles.REF_FID,
                fid,
                1,
                Qt.MatchExactly | Qt.MatchRecursive,
            )

            if matches:
                self.dlg_refresh_feature_selection()
                affected_lrefs_found |= True

        # Check 2: is this reference-id shown in current post-processing-selection?
        if self.my_dialog and self.my_dialog.qtrv_po_pro_selection.model():
            model = self.my_dialog.qtrv_po_pro_selection.model()

            matches = model.match(
                # search in column 0
                model.index(0, 0),
                Qt_Roles.REF_FID,
                fid,
                1,
                Qt.MatchExactly | Qt.MatchRecursive,
            )

            if matches:
                self.dlg_refresh_po_pro_selection()
                affected_lrefs_found |= True

        # Check 3: is this reference-geom currently used for self.session_data.lr_geom_runtime?
        if self.session_data.lr_geom_runtime is not None:
            # check, if the edited feature-id is the referenced feature-id in lr_geom_runtime
            if self.session_data.lr_geom_runtime.ref_fid == fid:
                # update geometry of lr_geom_runtime, which will recalculate linestring_statistics and stationings
                try:
                    self.session_data.lr_geom_runtime.update_geometry(
                        geometry, self.stored_settings.lrMode
                    )
                    # Geometry is accepted, stationings valid
                    # PolEvt or LolEvt? Derived cvs_draw_lr_geom with different canvas-grafics
                    if type(self).__name__ == "PolEvt":
                        draw_markers = ["sn", "rfl"]
                    else:
                        draw_markers = ["snf", "snt", "sgn", "sg0", "rfl"]

                    self.cvs_draw_lr_geom(
                        self.session_data.lr_geom_runtime,
                        draw_markers,
                    )
                    self.dlg_populate_measurement()
                except Exception as e:
                    # either geometry or stationings not accepted
                    self.session_data.lr_geom_runtime = None
                    self.dlg_reset_measurement()
                    # bubble up
                    #raise e
                    affected_lrefs_found |= True

        # Check 4: is this reference-geom currently used for self.session_data.po_pro_feature?
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs and self.session_data.po_pro_feature is not None and self.session_data.po_pro_feature.ref_fid == fid:
            try:
                self.session_data.po_pro_feature.lr_geom_current.update_geometry(
                    geometry, self.stored_settings.lrMode
                )
                # geometry is accepted, stationings valid
                self.cvs_show_po_pro_difference(self.session_data.po_pro_feature)
            except Exception as e:
                # geometry not accepted
                self.session_data.po_pro_feature = None
                self.dlg_refresh_po_pro_edit()
                # bubble up

                affected_lrefs_found |= True


        if affected_lrefs_found:
            self.dlg_append_log_message("INFO", MY_DICT.tr("ref_geom_changed_affected_lrefs_found",fid))


    def st_show_po_pro_ref_geom_diffs(self, ref_id: int|str):
        """shows differences between cached and current reference-geometries
        Compare-Layers-Variant
        Args:
            ref_id (int|str): ID in refLyr and poProRefLyr (not feature.id())
        """
        # Rev. 2026-01-12
        self.cvs_hide_markers()

        extent_mode = self.tool_get_extent_mode_lol()

        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs:

            reference_geom = self.tool_get_reference_geom(ref_id=ref_id)
            po_pro_ref_feature = get_feature_by_value(self.derived_settings.poProRefLyr,self.derived_settings.poProRefLyrIdField,ref_id)
            if po_pro_ref_feature.hasGeometry():
                po_pro_reference_geom = po_pro_ref_feature.geometry()

                x_coords = []
                y_coords = []
                flash_geoms = []

                tr_vl_2_cvs = QgsCoordinateTransform(
                    self.derived_settings.refLyr.crs(),
                    self.iface.mapCanvas().mapSettings().destinationCrs(),
                    QgsProject.instance(),
                )


                if not reference_geom.equals(po_pro_reference_geom):
                    ca_cu_diff_geom = po_pro_reference_geom.difference(reference_geom)
                    flash_geoms.append(ca_cu_diff_geom)
                    ca_cu_diff_extent = ca_cu_diff_geom.boundingBox()
                    ca_ca_diff_extent = tr_vl_2_cvs.transformBoundingBox(
                        ca_cu_diff_extent
                    )
                    x_coords.append(ca_ca_diff_extent.xMinimum())
                    x_coords.append(ca_ca_diff_extent.xMaximum())
                    y_coords.append(ca_ca_diff_extent.yMinimum())
                    y_coords.append(ca_ca_diff_extent.yMaximum())

                    cu_ca_diff_geom = reference_geom.difference(po_pro_reference_geom)
                    flash_geoms.append(cu_ca_diff_geom)
                    cu_ca_diff_extent = cu_ca_diff_geom.boundingBox()
                    cu_ca_diff_extent = tr_vl_2_cvs.transformBoundingBox(
                        cu_ca_diff_extent
                    )
                    x_coords.append(cu_ca_diff_extent.xMinimum())
                    x_coords.append(cu_ca_diff_extent.xMaximum())
                    y_coords.append(cu_ca_diff_extent.yMinimum())
                    y_coords.append(cu_ca_diff_extent.yMaximum())

                    self.canvas_graphics["cacu"].setToGeometry(
                        ca_cu_diff_geom, self.derived_settings.refLyr
                    )
                    self.canvas_graphics["cacu"].show()

                    self.canvas_graphics["cuca"].setToGeometry(
                        cu_ca_diff_geom, self.derived_settings.refLyr
                    )
                    self.canvas_graphics["cuca"].show()

                    if extent_mode:
                        self.cvs_set_extent(
                            extent_mode,
                            x_coords,
                            y_coords,
                        )
                        self.iface.mapCanvas().refresh()

                    self.iface.mapCanvas().flashGeometries(flash_geoms)

            else:
                raise FeatureWithoutGeometryException(self.derived_settings.poProRefLyr.name(),ref_id)


        self.qact_pausing.trigger()




    def cs_mapToolSet(self, new_tool: QgsMapTool, old_tool: QgsMapTool):
        """triggered by change of MapTool in canvas, f.e  switch from measure_stationing to pan

        Args:
            new_tool (QgsMapTool)
            old_tool (QgsMapTool)
        """
        # Rev. 2026-01-12
        if new_tool != self:
            self.gui_show_tool_mode("pausing")

    def ps_project_layersRemoved(self, removed_layer_ids: typing.Iterable[str]):
        """triggered by QgsProject.instance().layersRemoved
        check settings, refresh dialog
        :param removed_layer_ids: List of removed layer-IDs, mostly only one
        """
        # Rev. 2026-01-12
        re_init_map_tool = False

        for layer_id in removed_layer_ids:
            # check if it was a plugin-used layer
            if layer_id == self.stored_settings.refLyrId:
                self.stored_settings.refLyrId = ""
                re_init_map_tool |= True
            elif layer_id == self.stored_settings.dataLyrId:
                self.stored_settings.dataLyrId = ""
                re_init_map_tool |= True
            elif layer_id == self.stored_settings.showLyrId:
                self.stored_settings.showLyrId = ""
                re_init_map_tool |= True
            elif layer_id == self.stored_settings.poProRefLyrId:
                self.stored_settings.poProRefLyrId = ""
                re_init_map_tool |= True

        if re_init_map_tool:
            self.sys_restore_derived_settings()
            self.dlg_reset()
            self.dlg_append_log_message("INFO", MY_DICT.tr("plugin_used_layer_removed"))
        else:
            # refresh settings-section, f. e. the combo-boxes for layer- and field-selection
            self.dlg_populate_settings()
            self.dlg_populate_po_pro_settings()


    def dlg_reset(self):
        """complete reset of dialog with all form-widgets"""
        # Rev. 2026-01-12
        if self.my_dialog:
            self.dlg_apply_number_format()

            self.dlg_reset_measurement()
            self.dlg_reset_ref_lyr_select()
            self.dlg_reset_feature_selection()
            self.dlg_reset_po_pro_settings()
            self.dlg_reset_po_pro_selection()
            self.dlg_reset_po_pro_edit()
            #self.dlg_clear_log_messages()
            self.my_dialog.status_bar.clearMessage()

            # re-populate some widgets
            self.dlg_refresh_settings()
            self.dlg_refresh_po_pro_settings()
            self.dlg_refresh_ref_lyr_select()



    def gui_refresh(self):
        """complete refresh of all gui-elements, triggered by QgsApplication.instance().customVariablesChanged (locale, number-format...)
        reloads language, if settings have changed (affects plugin-messages and dialog-contents)
        """
        # Rev. 2026-01-12
        self.my_locale = sys_get_locale()
        global MY_DICT
        MY_DICT = SQLiteDict()
        if self.my_dialog:
            self.my_dialog.close()
            self.my_dialog = None

        self.dlg_init()

    def dlg_show(self):
        """shows and positions the dialog"""
        # Rev. 2026-01-12
        if self.my_dialog:
            if self.my_dialog.isHidden():
                self.my_dialog.show()
                if self.my_dialog.isFloating():
                    self.my_dialog.resize(self.session_data.dlg_last_width,self.session_data.dlg_last_height)


            self.my_dialog.setFocus()
            # if its tabbed:
            self.my_dialog.raise_()

    def dlg_store_size_and_position(self):
        """stores position and size of last used insert-form
        """
        # Rev. 2026-01-21
        # sender is the featureFormEventFilter, which is triggered on resize/move of the dataLyr-feature-attribute-forms
        # the feature_form is a property of this event-filter, its current position and size is stored as list in self.session_data.last_dlg_position
        event_filter = QObject().sender()
        left = event_filter.feature_form.mapToGlobal(QPoint(0, 0)).x()
        top = event_filter.feature_form.mapToGlobal(QPoint(0, 0)).y()
        width = event_filter.feature_form.rect().width()
        height = event_filter.feature_form.rect().height()
        self.session_data.last_dlg_position = [left, top, width, height]


    def dlg_toggle_top_level(self,checked:bool):
        """toggle dialog between TopLevel (free undockable window) and docked (with move and docked enabled, but floatable disabled)

        Args:
            checked (bool): checked-status of self.my_dialog.qtb_toggle_top_level
        """
        # Rev. 2026-01-12
        if self.my_dialog:
            if checked:
                # DockWidgetMovable => dock-border can be changed by drag&drop
                self.my_dialog.setFeatures(QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
                self.my_dialog.setFloating(False)

            else:
                self.my_dialog.setFeatures(QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetClosable)
                self.my_dialog.setFloating(True)
                self.my_dialog.resize(self.session_data.dlg_last_width,self.session_data.dlg_last_height)
                # Note 1: the last window-size is resetted by setFloating, therefore restore previously stored size
                # Note 2: the previous floating-window-position is stored/restored by default

            self.my_dialog.setFocus()
            # if its tabbed:
            self.my_dialog.raise_()


    def ps_project_legendLayersAdded(self):
        """triggered by QgsProject.instance().legendLayersAdded, layer added to project *and* legend"""
        # Rev. 2026-01-12
        self.dlg_populate_settings()
        self.dlg_refresh_po_pro_settings()

    def dlg_close(self):
        """connected to dialog_close-signal"""
        # Rev. 2026-01-12
        if self.my_dialog:
            # may already be unset if called with QGis-close
            if self.my_dialog.isFloating():
                self.session_data.dlg_last_width = self.my_dialog.width()
                self.session_data.dlg_last_height = self.my_dialog.height()

        self.cvs_hide_markers()
        self.iface.mapCanvas().unsetMapTool(self)


    def st_show_reference_feature_form(self, ref_fid: int):
        """shows feature-form for reference-layer

        Args:
            ref_fid (int): feature-id
        """
        # Rev. 2026-01-12
        try:
            show_feature_form(self.iface, self.derived_settings.refLyr, ref_fid)
            self.dlg_select_feature_selection_row(ref_fid=ref_fid)
        except Exception as e:
            self.sys_log_exception(e)

    def sys_unload(self):
        """called from LinearReference.sys_unload() on plugin-sys_unload and/or QGis-shut-down or project-close for both MapTools, if initialized"""
        # Rev. 2026-01-12
        self.iface.mapCanvas().unsetMapTool(self)


        self.iface.actionPan().trigger()
        self.sys_store_settings()

        self.snap_indicator.setVisible(False)
        self.cvs_hide_snap()

        # hide *and* remove canvas-graphics, they are *not* garbage-collected and deleted with self!
        self.cvs_hide_markers()

        for key, marker in self.canvas_graphics.items():
            self.iface.mapCanvas().scene().removeItem(marker)

        self.lact_remove_layer_actions()
        # Note to self.signal_slot_cons:
        # the registered connections will automatically be garbage-collected on unload
        self.sys_disconnect_data_lyr()
        self.sys_disconnect_ref_lyr()

        try:
            for conn_id in self.signal_slot_cons.application_connections:
                QgsApplication.instance().disconnect(conn_id)
            self.signal_slot_cons.application_connections = []
        except RuntimeError as e:
            # RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
            pass

        try:
            for conn_id in self.signal_slot_cons.project_connections:
                QgsProject.instance().disconnect(conn_id)
            self.signal_slot_cons.project_connections = []
        except RuntimeError as e:
            # RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
            pass
        try:
            for conn_id in self.signal_slot_cons.canvas_connections:
                self.iface.mapCanvas().disconnect(conn_id)
            self.signal_slot_cons.canvas_connections = []
        except RuntimeError as e:
            # RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
            pass

        try:
            for conn_id in self.signal_slot_cons.layer_tree_view_connections:
                QgsProject.instance().layerTreeRoot().disconnect(conn_id)
            self.signal_slot_cons.layer_tree_view_connections = []
        except RuntimeError as e:
            # RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
            pass

        # last action to avoid "self has no attribute my_dialog"
        # might be removed already
        # 'NoneType' object has no attribute 'close'
        # probably not necessary because of gc, dialog as part of the unloaded QgsMapToolEmitPoint is deleted (and closed...) automatically
        if self.my_dialog:
            self.my_dialog.close()
            del self.my_dialog


    def s_tbw_central_currentChanged(self, tab_index: int):
        """
        implemented for security/convenience
        triggered by tbw_central (QTabWidget) for tab_index == 2 (Settings-Section)
        -> Reread/Refresh Settings and update Dialog-Settings-Tab
        :param tab_index:
        """
        # Rev. 2026-01-12
        try:
            if tab_index == self.dialog_tabs['measurement']:
                self.dlg_refract_measurement()
                self.dlg_refract_ref_lyr_select()
            elif tab_index == self.dialog_tabs['feature_selection']:
                self.dlg_refract_feature_selection()
            elif tab_index == self.dialog_tabs['post_processing']:
                self.dlg_refract_po_pro_selection()
                self.dlg_refract_po_pro_edit()
                self.dlg_refract_po_pro_settings()
            elif tab_index == self.dialog_tabs['settings']:
                self.dlg_refresh_settings()
            else:
                # Message-Log
                pass
        except Exception as e:
            self.sys_log_exception(e)


    def tool_append_to_feature_selection(self, data_fid: int, do_select: bool = True):
        """if necessary:
        add data_fid to selected_data_fids
        refresh qtrv_feature_selection

        Args:
            data_fid (int): feature-id
            do_select (bool, optional): Select row for this data_fid. Defaults to True.
        """
        # Rev. 2026-01-12

        if not data_fid in self.session_data.selected_data_fids:
            self.session_data.selected_data_fids.add(data_fid)
            # refresh to show the possibly appended self.session_data.selected_data_fids
            self.dlg_refresh_feature_selection()

        if do_select:
            self.dlg_select_feature_selection_row(data_fid)

    def dlg_feature_selection_get_pre_settings(self):
        """stores Qt-Settings from qtrv_feature_selection for later restore with dlg_feature_selection_apply_pre_settings:
            - column-widths
            - sort-order
            - row-selections
            - scroll-positions

            Must be called *before* model().clear()

            settings are stored under self.session_data.last_feature_selection_settings

        """
        # Rev. 2026-01-12
        pre_settings = {}

        if self.my_dialog:
            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                if self.my_dialog.qtrv_feature_selection.model() is not None:

                    # store "layout" before model is cleared
                    pre_settings["old_indicator"] = (
                        self.my_dialog.qtrv_feature_selection.header().sortIndicatorSection()
                    )
                    pre_settings["old_order"] = (
                        self.my_dialog.qtrv_feature_selection.header().sortIndicatorOrder()
                    )

                    # https://doc.qt.io/archives/qt-5.15/qscrollbar.html
                    pre_settings["old_scroll_position_h"] = (
                        self.my_dialog.qtrv_feature_selection.horizontalScrollBar().value()
                    )
                    pre_settings["old_scroll_position_v"] = (
                        self.my_dialog.qtrv_feature_selection.verticalScrollBar().value()
                    )

                    pre_settings["old_column_widths"] = []
                    # only store widths, if data was already loaded
                    if self.my_dialog.qtrv_feature_selection.model().rowCount():
                        for col_idx in range(
                            self.my_dialog.qtrv_feature_selection.model().columnCount()
                        ):
                            pre_settings["old_column_widths"].append(
                                self.my_dialog.qtrv_feature_selection.columnWidth(col_idx)
                            )

                    pre_settings["old_expended_ref_fids"] = {}
                    for row_nr in range(
                        self.my_dialog.qtrv_feature_selection.model()
                        .invisibleRootItem()
                        .rowCount()
                    ):
                        child_idx = self.my_dialog.qtrv_feature_selection.model().index(
                            row_nr, 0
                        )
                        ref_fid = child_idx.data(Qt_Roles.REF_FID)
                        pre_settings["old_expended_ref_fids"][ref_fid] = (
                            self.my_dialog.qtrv_feature_selection.isExpanded(child_idx)
                        )

                    pre_settings["old_selected_ref_fids"] = []
                    pre_settings["old_selected_data_fids"] = []

                    if (
                        self.my_dialog.qtrv_feature_selection.selectionModel().hasSelection()
                    ):
                        extracted_items = qtrv_extract_items(
                            self.my_dialog.qtrv_feature_selection, 0, Qt_Roles.REF_FID
                        )
                        for extracted_item in extracted_items:
                            if self.my_dialog.qtrv_feature_selection.selectionModel().isSelected(
                                extracted_item.index()
                            ):
                                pre_settings["old_selected_ref_fids"].append(
                                    extracted_item.data(Qt_Roles.REF_FID)
                                )

                        extracted_items = qtrv_extract_items(
                            self.my_dialog.qtrv_feature_selection, 1, Qt_Roles.DATA_FID
                        )
                        for extracted_item in extracted_items:
                            if self.my_dialog.qtrv_feature_selection.selectionModel().isSelected(
                                extracted_item.index()
                            ):
                                pre_settings["old_selected_data_fids"].append(
                                    extracted_item.data(Qt_Roles.DATA_FID)
                                )
        self.session_data.last_feature_selection_settings = pre_settings


    def dlg_po_pro_selection_get_pre_settings(self):
        """stores Qt-Settings from qtrv_po_pro_selection for later restore with dlg_po_pro_selection_apply_pre_settings:
            - column-widths
            - sort-order
            - row-selections
            - scroll-positions

            Must be called *before* model().clear()

            settings are stored under self.session_data.last_po_pro_selection_settings
        """
        # Rev. 2026-01-12
        pre_settings = {}

        if self.my_dialog:
            if (SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED) in self.system_vs:

                if self.my_dialog.qtrv_po_pro_selection.model() is not None:
                    # store "layout" before model is cleared
                    pre_settings["old_indicator"] = (
                        self.my_dialog.qtrv_po_pro_selection.header().sortIndicatorSection()
                    )
                    pre_settings["old_order"] = (
                        self.my_dialog.qtrv_po_pro_selection.header().sortIndicatorOrder()
                    )

                    # https://doc.qt.io/archives/qt-5.15/qscrollbar.html
                    pre_settings["old_scroll_position_h"] = (
                        self.my_dialog.qtrv_po_pro_selection.horizontalScrollBar().value()
                    )
                    pre_settings["old_scroll_position_v"] = (
                        self.my_dialog.qtrv_po_pro_selection.verticalScrollBar().value()
                    )

                    pre_settings["old_column_widths"] = []
                    # only store widths, if data was already loaded
                    if self.my_dialog.qtrv_po_pro_selection.model().rowCount():
                        for col_idx in range(
                            self.my_dialog.qtrv_po_pro_selection.model().columnCount()
                        ):
                            pre_settings["old_column_widths"].append(
                                self.my_dialog.qtrv_po_pro_selection.columnWidth(col_idx)
                            )

                    pre_settings["old_expended_ref_fids"] = {}
                    for row_nr in range(
                        self.my_dialog.qtrv_po_pro_selection.model()
                        .invisibleRootItem()
                        .rowCount()
                    ):
                        child_idx = self.my_dialog.qtrv_po_pro_selection.model().index(
                            row_nr, 0
                        )
                        ref_fid = child_idx.data(Qt_Roles.REF_FID)
                        pre_settings["old_expended_ref_fids"][ref_fid] = (
                            self.my_dialog.qtrv_po_pro_selection.isExpanded(child_idx)
                        )

                    pre_settings["old_selected_ref_fids"] = []
                    pre_settings["old_selected_data_fids"] = []

                    if (
                        self.my_dialog.qtrv_po_pro_selection.selectionModel().hasSelection()
                    ):
                        extracted_items = qtrv_extract_items(
                            self.my_dialog.qtrv_po_pro_selection, 0, Qt_Roles.REF_FID
                        )
                        for extracted_item in extracted_items:
                            if self.my_dialog.qtrv_po_pro_selection.selectionModel().isSelected(
                                extracted_item.index()
                            ):
                                pre_settings["old_selected_ref_fids"].append(
                                    extracted_item.data(Qt_Roles.REF_FID)
                                )

                        extracted_items = qtrv_extract_items(
                            self.my_dialog.qtrv_po_pro_selection, 1, Qt_Roles.DATA_FID
                        )
                        for extracted_item in extracted_items:
                            if self.my_dialog.qtrv_po_pro_selection.selectionModel().isSelected(
                                extracted_item.index()
                            ):
                                pre_settings["old_selected_data_fids"].append(
                                    extracted_item.data(Qt_Roles.DATA_FID)
                                )
        self.session_data.last_po_pro_selection_settings = pre_settings


    def st_remove_from_po_pro_selection(self,data_id:str|int = None,ref_id:str|int = None):
        """remove one row (data_id) or complete branch (ref_id) from PoPro-Cache and refresh selection

        Args:
            data_id (str | int, optional): ID of data-feature not feature.id()
            ref_id (str | int, optional): ID of reference-feature, not feature.id()
        """
        # Rev. 2026-01-12
        if data_id and data_id in self.session_data.po_pro_cache:
            del self.session_data.po_pro_cache[data_id]

        if data_id and self.session_data.po_pro_feature and self.session_data.po_pro_feature.data_id == data_id:
            self.session_data.po_pro_feature = None

        if ref_id:
            del_data_ids = {key for key in self.session_data.po_pro_cache if self.session_data.po_pro_cache[key]['ref_id'] == ref_id}

            for del_data_id in del_data_ids:
                del self.session_data.po_pro_cache[del_data_id]

                if self.session_data.po_pro_feature and self.session_data.po_pro_feature.data_id == del_data_id:
                    self.session_data.po_pro_feature = None

        self.dlg_refresh_po_pro_selection()
        self.dlg_refresh_po_pro_edit()

    def st_remove_from_feature_selection(self, data_fids: list):
        """removes features from feature-selection
        called from qtrv_feature_selection with list of assigned_data_fids or single [assigned_data_fid]

        Args:
            data_fids (list)
        """
        # Rev. 2026-01-12
        for data_fid in data_fids:
            self.session_data.selected_data_fids.discard(data_fid)

        self.dlg_refresh_feature_selection()

    def s_zoom_to_feature_selection(self, checked: bool):
        """wrapper to call cvs_draw_feature_selection with specific extent-mode

        Args:
            checked (bool): check-state if triggered from QAction
        """
        # Rev. 2026-01-12
        try:
            if self.session_data.selected_data_fids:
                extent_mode = self.tool_get_extent_mode_lol()
                self.cvs_draw_feature_selection(extent_mode=extent_mode)
                self.qact_pausing.trigger()
            else:
                raise IterableEmptyException("Feature-Selection")

        except Exception as e:
            self.sys_log_exception(e)

    def s_clear_po_pro_selection(self, checked: bool):
        """clear Post-Processing-Cache"""
        # Rev. 2026-01-12
        try:
            self.cvs_hide_markers()
            self.session_data.po_pro_feature = None
            self.session_data.po_pro_cache = dict()
            self.dlg_refresh_po_pro_selection()
            self.dlg_refresh_po_pro_edit()
        except Exception as e:
            self.sys_log_exception(e)

    def s_zoom_to_po_pro_selection(self, checked: bool):
        """wrapper to call cvs_draw_po_pro_selection with specific extent-mode

        Args:
            checked (bool): check-state if triggered from QAction
        """
        # Rev. 2026-01-12
        try:
            if self.session_data.po_pro_cache:
                extent_mode = self.tool_get_extent_mode_lol()
                self.cvs_draw_po_pro_selection(extent_mode=extent_mode)
                self.qact_pausing.trigger()
            else:
                raise IterableEmptyException("PostProcessing-Selection")
        except Exception as e:
            self.sys_log_exception(e)

    def dlg_refract_feature_selection(self):
        """Refresh QActions and function-widgets in Feature-Selection-Tab"""
        # Rev. 2026-01-12
        if self.my_dialog:
            #  and self.derived_settings.dataLyr.featureCount() > 0
            self.qact_append_data_features.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
            )

            self.qact_select_from_table.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
            )

            # and self.derived_settings.showLyr.featureCount() > 0
            self.qact_select_features.setEnabled(
                SVS.ALL_LAYERS_CONNECTED in self.system_vs
            )

            self.qact_clear_feature_selection.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
                and len(self.session_data.selected_data_fids) > 0
            )

            self.qact_zoom_feature_selection.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
                and len(self.session_data.selected_data_fids) > 0
            )

            self.qact_transfer_feature_selection.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
                and len(self.session_data.selected_data_fids) > 0
            )

            # and len(self.session_data.selected_data_fids) > 0
            # alter filter not in edit-mode
            self.qact_filter_by_feature_selection.setEnabled(
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs
                and not SVS.DATA_LAYER_EDITABLE in self.system_vs
            )

            # MyEditToolButton => not used so far...
            edit_tool_buttons = self.my_dialog.qtrv_feature_selection.findChildren(
                MyEditToolButton
            )
            update_enabled = (
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                | SVS.DATA_LAYER_EDITABLE
                | SVS.DATA_LAYER_UPDATE_ENABLED
            ) in self.system_vs
            for edit_tool_button in edit_tool_buttons:
                edit_tool_button.setEnabled(update_enabled)
                # edit_tool_button.setVisible(update_enabled)

            delete_tool_buttons = self.my_dialog.qtrv_feature_selection.findChildren(
                MyDeleteToolButton
            )
            delete_enabled = (
                SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                | SVS.DATA_LAYER_EDITABLE
                | SVS.DATA_LAYER_DELETE_ENABLED
            ) in self.system_vs
            for delete_tool_button in delete_tool_buttons:
                delete_tool_button.setEnabled(delete_enabled)
                # delete_tool_button.setVisible(delete_enabled)

    def dlg_refract_po_pro_selection(self):
        """refresh buttons in qtrv_po_pro_selection, f.e. after start of dataLyr-edit-session
        Buttons are identified by special subclasses of QToolButton: MyEditToolButton and MyDeleteToolButton
        """
        # Rev. 2026-01-12
        # nothing to do so far...


        pass

    def dlg_refract_po_pro_settings(self):
        """refresh some buttons in PostProcessing-Tab"""
        # Rev. 2026-01-12
        if self.my_dialog:
            self.qact_start_post_processing.setEnabled(
                (
                    SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                    | SVS.PO_PRO_REF_LAYER_CONNECTED
                    | SVS.DATA_LAYER_UPDATE_ENABLED
                )
                in self.system_vs
            )

            self.qact_open_po_pro_ref_lyr.setEnabled(SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs)

            self.qact_zoom_po_pro_selection.setEnabled(
                (
                    SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                    | SVS.PO_PRO_REF_LAYER_CONNECTED
                    | SVS.DATA_LAYER_UPDATE_ENABLED
                )
                in self.system_vs
                and self.my_dialog.qtrv_po_pro_selection.model().rowCount() > 0
            )

            self.qact_clear_po_pro_selection.setEnabled(
                (
                    SVS.REFERENCE_AND_DATA_LAYER_CONNECTED
                    | SVS.PO_PRO_REF_LAYER_CONNECTED
                    | SVS.DATA_LAYER_UPDATE_ENABLED
                )
                in self.system_vs
                and self.my_dialog.qtrv_po_pro_selection.model().rowCount() > 0
            )

    def dlg_populate_po_pro_settings(self):
        """fill layer- and field-select-widgets in PostProcessing-Tab"""
        # Rev. 2026-01-12
        if self.my_dialog:

            block_widgets = [
                self.my_dialog.qcbn_pp_ref_lyr,
                self.my_dialog.qcbn_pp_ref_lyr_id_field,
            ]

            for widget in block_widgets:
                widget.blockSignals(True)

            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
                # filter: same geometry-type and projection as, but not virtual (ShowLyr) or reference layer itself
                self.my_dialog.qcbn_pp_ref_lyr.load_data(
                    {
                        "geometry_type": [self.derived_settings.refLyr.geometryType()],
                        "crs": [self.derived_settings.refLyr.crs()]
                    },
                    {
                        "data_provider": ["virtual"],
                        "layer_id": [self.stored_settings.refLyrId,self.stored_settings.showLyrId],
                    },
                )
                self.my_dialog.qcbn_pp_ref_lyr.setEnabled(True)

                if self.derived_settings.poProRefLyr:
                    self.my_dialog.qcbn_pp_ref_lyr.select_by_value(
                        [[0, Qt_Roles.RETURN_VALUE, Qt.MatchExactly]],
                        self.derived_settings.poProRefLyr.id(),
                        True,
                    )
                    # Reference-Layer is selected, now select the Id-Field, same type as ID-Field in Reference-Layer
                    enable_criteria = {
                        "field_type": [self.derived_settings.refLyrIdField.type()],
                        # field_origin == 1 => no calculated fields
                        # Perhaps workaround, if the field-type between Reference and PoProReference-Layer are different (f.e. different int-type)
                        #"field_origin": [1],
                    }

                    self.my_dialog.qcbn_pp_ref_lyr_id_field.load_data(
                        self.derived_settings.refLyr, enable_criteria
                    )
                    self.my_dialog.qcbn_pp_ref_lyr_id_field.setEnabled(True)

                    if self.derived_settings.poProRefLyrIdField:
                        self.my_dialog.qcbn_pp_ref_lyr_id_field.select_by_value(
                            [[0, Qt_Roles.RETURN_VALUE, Qt.MatchExactly]],
                            self.derived_settings.poProRefLyrIdField.name(),
                            True,
                        )

            for widget in block_widgets:
                widget.blockSignals(False)


    def dlg_refresh_po_pro_selection(self):
        """wrapper to refresh po_pro_selection"""
        # Rev. 2026-01-12
        self.dlg_reset_po_pro_selection()
        self.dlg_populate_po_pro_selection()
        self.dlg_refract_po_pro_selection()



    def dlg_feature_selection_apply_pre_settings(self):
        """restores previous look of qtrv_feature_selection via self.session_data.last_feature_selection_settings
            should be called delayed, because the widget must have been painted to know its width/height
            (resizeColumnToContents, horizontalScrollBar, verticalScrollBar)
        """
        # Rev. 2026-01-12
        if self.my_dialog:
            if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:

                if self.session_data.last_feature_selection_settings:
                    # restore previous sort:
                    pre_settings = self.session_data.last_feature_selection_settings
                    old_indicator = pre_settings.get("old_indicator")
                    old_order = pre_settings.get("old_order")
                    if old_indicator is not None and old_order is not None:
                        self.my_dialog.qtrv_feature_selection.sortByColumn(
                            old_indicator, old_order
                        )

                    # restore previous expended or collapsed rows
                    old_expended_ref_fids = pre_settings.get("old_expended_ref_fids")
                    if old_expended_ref_fids:
                        for row_nr in range(
                            self.my_dialog.qtrv_feature_selection.model()
                            .invisibleRootItem()
                            .rowCount()
                        ):
                            child_idx = (
                                self.my_dialog.qtrv_feature_selection.model().index(
                                    row_nr, 0
                                )
                            )
                            ref_fid = child_idx.data(Qt_Roles.REF_FID)
                            if ref_fid in old_expended_ref_fids:
                                self.my_dialog.qtrv_feature_selection.setExpanded(
                                    child_idx, old_expended_ref_fids[ref_fid]
                                )
                            else:
                                self.my_dialog.qtrv_feature_selection.setExpanded(
                                    child_idx, True
                                )
                    else:
                        self.my_dialog.qtrv_feature_selection.expandAll()

                    # restore column-widths
                    old_column_widths = pre_settings.get("old_column_widths")
                    if old_column_widths:
                        for col_idx, col_width in enumerate(old_column_widths):
                            self.my_dialog.qtrv_feature_selection.setColumnWidth(
                                col_idx, col_width
                            )
                    else:
                        for col_idx in range(
                            self.my_dialog.qtrv_feature_selection.model().columnCount(),
                        ):
                            self.my_dialog.qtrv_feature_selection.resizeColumnToContents(
                                col_idx
                            )

                    # restore selection
                    # Note:
                    # single-select => either selected reference-features, or selected data-features
                    old_selected_ref_fids = pre_settings.get("old_selected_ref_fids")
                    if old_selected_ref_fids:
                        for ref_fid in old_selected_ref_fids:
                            self.dlg_select_feature_selection_row(ref_fid=ref_fid)

                    old_selected_data_fids = pre_settings.get("old_selected_data_fids")
                    if old_selected_data_fids:
                        for data_fid in old_selected_data_fids:
                            self.dlg_select_feature_selection_row(data_fid)

                    old_scroll_position_h = pre_settings.get("old_scroll_position_h")
                    old_scroll_position_v = pre_settings.get("old_scroll_position_v")
                    if old_scroll_position_h is not None:
                        self.my_dialog.qtrv_feature_selection.horizontalScrollBar().setValue(
                            old_scroll_position_h
                        )
                    if old_scroll_position_v is not None:
                        self.my_dialog.qtrv_feature_selection.verticalScrollBar().setValue(
                            old_scroll_position_v
                        )
                else:
                    self.my_dialog.qtrv_feature_selection.expandAll()
                    for col_idx in range(
                        self.my_dialog.qtrv_feature_selection.model().columnCount(),
                    ):
                        self.my_dialog.qtrv_feature_selection.resizeColumnToContents(
                            col_idx
                        )



    def dlg_po_pro_selection_apply_pre_settings(self):
        """restores previous look of qtrv_po_pro_selection from self.session_data.last_po_pro_selection_settings
            should be called delayed, because the widget must have been painted to know its width/height
            (resizeColumnToContents, horizontalScrollBar, verticalScrollBar)

        """
        # Rev. 2026-01-12
        if self.my_dialog:
            if (SVS.REFERENCE_AND_DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED) in self.system_vs:

                if self.session_data.last_po_pro_selection_settings:
                    pre_settings = self.session_data.last_po_pro_selection_settings
                    # restore previous sort:
                    old_indicator = pre_settings.get("old_indicator")
                    old_order = pre_settings.get("old_order")
                    if old_indicator is not None and old_order is not None:
                        self.my_dialog.qtrv_po_pro_selection.sortByColumn(
                            old_indicator, old_order
                        )

                    # restore previous expended or collapsed rows
                    old_expended_ref_fids = pre_settings.get("old_expended_ref_fids")
                    if old_expended_ref_fids:
                        for row_nr in range(
                            self.my_dialog.qtrv_po_pro_selection.model()
                            .invisibleRootItem()
                            .rowCount()
                        ):
                            child_idx = (
                                self.my_dialog.qtrv_po_pro_selection.model().index(
                                    row_nr, 0
                                )
                            )
                            ref_fid = child_idx.data(Qt_Roles.REF_FID)
                            if ref_fid in old_expended_ref_fids:
                                self.my_dialog.qtrv_po_pro_selection.setExpanded(
                                    child_idx, old_expended_ref_fids[ref_fid]
                                )
                            else:
                                self.my_dialog.qtrv_po_pro_selection.setExpanded(
                                    child_idx, True
                                )
                    else:
                        self.my_dialog.qtrv_po_pro_selection.expandAll()

                    # restore column-widths
                    old_column_widths = pre_settings.get("old_column_widths")
                    if old_column_widths:
                        for col_idx, col_width in enumerate(old_column_widths):
                            self.my_dialog.qtrv_po_pro_selection.setColumnWidth(
                                col_idx, col_width
                            )
                    else:
                        for col_idx in range(
                            self.my_dialog.qtrv_po_pro_selection.model().columnCount(),
                        ):
                            self.my_dialog.qtrv_po_pro_selection.resizeColumnToContents(
                                col_idx
                            )

                    # restore selection
                    # Note:
                    # single-select => either selected reference-features, or selected data-features
                    old_selected_ref_fids = pre_settings.get("old_selected_ref_fids")
                    if old_selected_ref_fids:
                        for ref_fid in old_selected_ref_fids:
                            self.dlg_select_po_pro_selection_row(ref_fid=ref_fid)

                    old_selected_data_fids = pre_settings.get("old_selected_data_fids")
                    if old_selected_data_fids:
                        for data_fid in old_selected_data_fids:
                            self.dlg_select_po_pro_selection_row(data_fid)

                    old_scroll_position_h = pre_settings.get("old_scroll_position_h")
                    old_scroll_position_v = pre_settings.get("old_scroll_position_v")
                    if old_scroll_position_h is not None:
                        self.my_dialog.qtrv_po_pro_selection.horizontalScrollBar().setValue(
                            old_scroll_position_h
                        )
                    if old_scroll_position_v is not None:
                        self.my_dialog.qtrv_po_pro_selection.verticalScrollBar().setValue(
                            old_scroll_position_v
                        )

                else:
                    self.my_dialog.qtrv_po_pro_selection.expandAll()
                    for col_idx in range(
                        self.my_dialog.qtrv_po_pro_selection.model().columnCount(),
                    ):
                        self.my_dialog.qtrv_po_pro_selection.resizeColumnToContents(
                            col_idx
                        )


    def dlg_select_qcbn_reference_feature(self, ref_fid:int):
        """select row in self.my_dialog.qcbn_ref_lyr_select
        Args:
            ref_fid (int): feature.id()
        """
        # Rev. 2026-01-12
        if self.my_dialog:
            with QSignalBlocker(self.my_dialog.qcbn_ref_lyr_select):
                if ref_fid:
                    self.my_dialog.qcbn_ref_lyr_select.select_by_value(
                        [[0, Qt_Roles.REF_FID, Qt.MatchExactly]], ref_fid, True
                    )
                else:
                    self.my_dialog.qcbn_ref_lyr_select.set_current_index(-1)

    def sys_restore_stored_settings(self):
        """restores self.stored_settings from QgsProject.instance()"""
        # Rev. 2026-01-12

        # Note: same StoredSettings, but not all keys used for PolEvt
        self.stored_settings = StoredSettings()

        # Note: key for QgsProject.instance().readEntry() with prepended "PolEvt"/"LolEvt"
        for prop_name in self.stored_settings._str_props:
            key = f"/{type(self).__name__}/{prop_name}"
            restored_value, type_conversion_ok = QgsProject.instance().readEntry(
                "LinearReferencing", key
            )
            if type_conversion_ok:
                setattr(self.stored_settings, prop_name, restored_value)

        for prop_name in self.stored_settings._int_props:
            key = f"/{type(self).__name__}/{prop_name}"
            restored_value, type_conversion_ok = QgsProject.instance().readNumEntry(
                "LinearReferencing", key
            )
            if type_conversion_ok:
                setattr(self.stored_settings, prop_name, restored_value)

        for prop_name in self.stored_settings._double_props:
            key = f"/{type(self).__name__}/{prop_name}"
            restored_value, type_conversion_ok = QgsProject.instance().readDoubleEntry(
                "LinearReferencing", key
            )
            if type_conversion_ok:
                setattr(self.stored_settings, prop_name, restored_value)

        for prop_name in self.stored_settings._bool_props:
            key = f"/{type(self).__name__}/{prop_name}"
            restored_value, type_conversion_ok = QgsProject.instance().readBoolEntry(
                "LinearReferencing", key
            )
            if type_conversion_ok:
                setattr(self.stored_settings, prop_name, restored_value)

    def sys_restore_derived_settings(self):
        """checks the current configuration, performs multiple tasks:
        Use and check self.stored_settings
        connects referenced layers and stores layers/fields in self.derived_settings
        generates self.system_vs
        """
        # Rev. 2026-01-12
        self.system_vs = SVS.INIT
        self.derived_settings = DerivedSettings()
        self.sys_connect_ref_lyr()
        if SVS.REFERENCE_LAYER_CONNECTED in self.system_vs:
            self.sys_connect_data_lyr()
            if SVS.DATA_LAYER_CONNECTED in self.system_vs:
                self.sys_connect_show_layer()
                self.sys_connect_po_pro_ref_layer()

        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            if self.stored_settings.lrMode in ["Mabs", "Mfract"]:
                if not SVS.REFERENCE_LAYER_M_ENABLED in self.system_vs:
                    self.stored_settings.lrMode = "Nabs"
                    self.dlg_append_log_message(
                        "WARNING", MY_DICT.tr("auto_switched_lr_mode")
                    )
                    if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                        self.dlg_append_log_message(
                            "WARNING", MY_DICT.tr("lr_mode_switch_disconnects_show_lyr")
                        )
                        self.sys_disconnect_show_lyr()


    def stm_select_features(self):
        """set tool-mode select_features: select referenced features from showLyr to feature-selection"""
        # Rev. 2026-01-12
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            self.sys_set_tool_mode("select_features")

    def cpe_select_features(self, event: QgsMapMouseEvent):
        """canvas press for tool_modes 'select_features'

        Args:
            event (QgsMapMouseEvent)
        """
        # Rev. 2026-01-12
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            event_with_left_btn = bool(Qt.LeftButton & event.buttons())
            self.session_data.cvs_mouse_down = None
            self.canvas_graphics["sel"].hide()
            if event_with_left_btn:
                self.session_data.cvs_mouse_down = event.mapPoint()

    def cme_select_features(self, event: QgsMapMouseEvent):
        """canvas move for tool_modes 'select_features'

        Args:
            event (QgsMapMouseEvent)
        """
        # Rev. 2026-01-12
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            event_with_left_btn = bool(Qt.LeftButton & event.buttons())
            if event_with_left_btn and self.session_data.cvs_mouse_down is not None:
                down_pt_map = QgsPointXY(
                    self.session_data.cvs_mouse_down.x(),
                    self.session_data.cvs_mouse_down.y(),
                )
                move_pt_map = QgsPointXY(event.mapPoint().x(), event.mapPoint().y())
                selection_geom = QgsGeometry.fromRect(
                    QgsRectangle(down_pt_map, move_pt_map)
                )
                self.canvas_graphics["sel"].setToGeometry(selection_geom, None)
                self.canvas_graphics["sel"].show()

    def cre_select_features(self, event: QgsMapMouseEvent):
        """canvas release for tool_mode 'select_features'

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-12
        self.cvs_hide_markers()
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            if self.session_data.cvs_mouse_down is not None:

                # important: independend clone of old selection by set(set)
                old_selection = set(self.session_data.selected_data_fids)

                selected_data_fids = self.tool_select_features_by_rect(
                    self.session_data.cvs_mouse_down.x(),
                    self.session_data.cvs_mouse_down.y(),
                    event.mapPoint().x(),
                    event.mapPoint().y(),
                )[0]


                if check_mods("s"):
                    # add_to_selection
                    self.session_data.selected_data_fids |= selected_data_fids
                elif check_mods("c"):
                    # remove_from_selection
                    self.session_data.selected_data_fids -= selected_data_fids
                else:
                    # replace selection
                    self.session_data.selected_data_fids = selected_data_fids

                if self.session_data.selected_data_fids:
                    self.cvs_draw_feature_selection(extent_mode=None)

                self.dlg_refresh_feature_selection()

        self.session_data.cvs_mouse_down = None



    def stm_select_edit_feature(self):
        """set tool-mode select_edit_feature: select single feature from showLyr for edit and/or feature-selection"""
        # Rev. 2026-01-12
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            self.sys_set_tool_mode("select_edit_feature")

    def cpe_select_edit_feature(self, event: QgsMapMouseEvent):
        """canvas press for tool_modes 'select_edit_feature'

        Args:
            event (QgsMapMouseEvent)
        """
        # Rev. 2026-01-12
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            event_with_left_btn = bool(Qt.LeftButton & event.buttons())
            self.session_data.cvs_mouse_down = None
            self.canvas_graphics["sel"].hide()
            if event_with_left_btn:
                self.session_data.cvs_mouse_down = event.mapPoint()

    def cme_select_edit_feature(self, event: QgsMapMouseEvent):
        """canvas move for tool_mode 'select_edit_feature'

        Args:
            event (QgsMapMouseEvent)
        """
        # Rev. 2026-01-12
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            event_with_left_btn = bool(Qt.LeftButton & event.buttons())
            if event_with_left_btn and self.session_data.cvs_mouse_down is not None:
                down_pt_map = QgsPointXY(
                    self.session_data.cvs_mouse_down.x(),
                    self.session_data.cvs_mouse_down.y(),
                )
                move_pt_map = QgsPointXY(event.mapPoint().x(), event.mapPoint().y())
                selection_geom = QgsGeometry.fromRect(
                    QgsRectangle(down_pt_map, move_pt_map)
                )
                self.canvas_graphics["sel"].setToGeometry(selection_geom, None)
                self.canvas_graphics["sel"].show()

    def cre_select_edit_feature(self, event: QgsMapMouseEvent):
        """canvas release for tool_mode 'select_edit_feature'

        Args:
            event (QgsMapMouseEvent):
        """
        # Rev. 2026-01-12
        self.cvs_hide_markers()
        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            if self.session_data.cvs_mouse_down is not None:

                selected_data_fids = self.tool_select_features_by_rect(
                    self.session_data.cvs_mouse_down.x(),
                    self.session_data.cvs_mouse_down.y(),
                    event.mapPoint().x(),
                    event.mapPoint().y(),
                )[0]

                if selected_data_fids:
                    # append all to feature-selection
                    for fid in selected_data_fids:
                        self.tool_append_to_feature_selection(fid)

                    if len(selected_data_fids) > 1:
                        self.dlg_append_log_message("INFO", MY_DICT.tr("multiple_features_selected"))
                        self.dlg_show_tab("feature_selection")
                    else:
                        data_fid = selected_data_fids.pop()
                        lr_geom_runtime = self.tool_get_feature_lr_geom(
                            data_fid=data_fid
                        )
                        self.session_data.lr_geom_runtime = lr_geom_runtime
                        self.session_data.edit_feature_fid = data_fid

                        if type(self).__name__ == "PolEvt":
                            self.cvs_draw_lr_geom(
                                self.session_data.lr_geom_runtime,
                                ["sn","rfl"],
                                flash_markers = ["sn"],
                            )
                        else:
                            self.cvs_draw_lr_geom(
                                self.session_data.lr_geom_runtime,
                                ["snf", "snt", "sgn", "sg0", "rfl"],
                                flash_markers = ["snf", "snt"],
                            )
                        self.dlg_refresh_measurement()
                        self.dlg_show_tab("measurement")

        self.session_data.cvs_mouse_down = None


    def dlg_refresh_measurement(self):
        """wrapper to refresh measurement-tab (excl. ref_lyr_select)"""
        # Rev. 2026-01-12
        self.dlg_reset_measurement()
        self.dlg_populate_measurement()
        self.dlg_refract_measurement()

    def dlg_show_tab(self, tab_name: str):
        """switch to dialog-tab by name without triggering any signals
        Args:
            tab_name (str): see self.dialog_tabs
                - measurement
                - feature_selection
                - settings
                - message_log
                - post_processing
        """
        # Rev. 2026-01-12
        tab_index = self.dialog_tabs.get(tab_name)
        if tab_index is not None:
            self.my_dialog.tbw_central.blockSignals(True)
            self.my_dialog.tbw_central.setCurrentIndex(tab_index)
            self.my_dialog.tbw_central.blockSignals(False)

    def tool_select_features_by_rect(
        self, x1: float, y1: float, x2: float, y2: float
    ) -> tuple:
        """select show-features/data-features by rect
        Args:
            x1 (float): x-coordinate, typically self.session_data.cvs_mouse_down.x()
            y1 (float): y-coordinate, typically self.session_data.cvs_mouse_down.y()
            x2 (float): x-coordinate, typically event.mapPoint().x()
            y2 (float): y-coordinate, typically event.mapPoint().y()

        Returns:
            tuple (data_fids:set,show_fids:set)
        """
        # Rev. 2026-01-12
        # Note: event_with_left_btn allways returns False for canvasReleaseEvents!
        selected_data_fids = set()
        selected_show_fids = set()

        if SVS.ALL_LAYERS_CONNECTED in self.system_vs:
            if self.session_data.cvs_mouse_down is not None:

                # coords identical => mouse-down == mouse-up => simple klick
                if x1 == x2 and y1 == y2:
                    delta_pixel = 10
                    delta_map_units = (
                        delta_pixel * self.iface.mapCanvas().mapUnitsPerPixel()
                    )
                    min_x = min(x1, x2) - delta_map_units
                    min_y = min(y1, y2) - delta_map_units
                    max_x = max(x1, x2) + delta_map_units
                    max_y = max(y1, y2) + delta_map_units

                    down_pt_map = QgsPointXY(min_x, min_y)
                    up_pt_map = QgsPointXY(max_x, max_y)
                else:
                    down_pt_map = QgsPointXY(x1, y1)
                    up_pt_map = QgsPointXY(x2, y2)

                selection_rect = QgsRectangle(down_pt_map, up_pt_map)

                tr = QgsCoordinateTransform(
                    self.iface.mapCanvas().mapSettings().destinationCrs(),
                    self.derived_settings.showLyr.crs(),
                    QgsProject.instance(),
                )
                filter_rect = tr.transformBoundingBox(selection_rect)

                request = QgsFeatureRequest()
                request.setFilterRect(filter_rect)
                request.setFlags(QgsFeatureRequest.ExactIntersect)

                show_fids = {
                    f.id() for f in self.derived_settings.showLyr.getFeatures(request)
                }

                for show_fid in show_fids:
                    try:
                        data_feature = self.tool_get_data_feature(
                            show_fid=show_fid
                        )
                        selected_show_fids.add(show_fid)
                        selected_data_fids.add(data_feature.id())
                    except Exception as e:
                        self.sys_log_exception(e)

        return selected_data_fids, selected_show_fids

    def st_show_data_feature_form(self, data_fid: int):
        """shows feature-form for data-layer

        Args:
            data_fid (int): feature-id
        """
        # Rev. 2026-01-12
        try:
            show_feature_form(self.iface, self.derived_settings.dataLyr, data_fid)
            self.dlg_select_feature_selection_row(data_fid)
        except Exception as e:
            self.sys_log_exception(e)

    def s_show_edit_feature_form(self):
        """shows feature-form for self.session_data.edit_feature_fid
        """
        # Rev. 2026-01-12
        try:
            show_feature_form(self.iface, self.derived_settings.dataLyr, self.session_data.edit_feature_fid)
        except Exception as e:
            self.sys_log_exception(e)

    def s_show_po_pro_feature_form(self):
        """shows feature-form for self.session_data.po_pro_feature
        """
        # Rev. 2026-01-12
        try:
            show_feature_form(self.iface, self.derived_settings.dataLyr, self.session_data.po_pro_feature.data_fid)
        except Exception as e:
            self.sys_log_exception(e)

    def st_select_po_pro_data_feature(self,data_id:int|str):
        """select feature in dataLyr, if po-pro-cached-metas exist

        Args:
            data_id (int|str): id, not feature.id()
        """
        # Rev. 2026-01-12
        if SVS.DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs:
            if data_id in self.session_data.po_pro_cache:
                data_feature = get_feature_by_value(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyrIdField,
                    data_id,
                )

                # these features/forms will have different contents if dataLyr is modified
                if check_mods("c"):
                    # [ctrl] => remove from selection
                    self.derived_settings.dataLyr.deselect(data_feature.id())
                elif check_mods("s"):
                    # [shift] => add to selection
                    self.derived_settings.dataLyr.select(data_feature.id())
                else:
                    # no modifier => replace selection
                    self.derived_settings.dataLyr.removeSelection()
                    self.derived_settings.dataLyr.select(data_feature.id())
            else:
                raise NotInSelectionException("po_pro_cache", data_id)
        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr + PoProLyr")


    def st_show_po_pro_data_feature_form(self,data_id:int|str):
        """shows feature-form for dataLyr, if po-pro-cached metas are stored

        Args:
            data_id (int|str): id, not feature.id()
        """
        # Rev. 2026-01-12
        if SVS.DATA_LAYER_CONNECTED | SVS.PO_PRO_REF_LAYER_CONNECTED in self.system_vs:
            if data_id in self.session_data.po_pro_cache:
                data_feature = get_feature_by_value(
                    self.derived_settings.dataLyr,
                    self.derived_settings.dataLyrIdField,
                    data_id,
                )

                # feature/cached-metas will have different contents if dataLyr was modified
                show_feature_form(self.iface, self.derived_settings.dataLyr, data_feature.id())
            else:
                raise NotInSelectionException("po_pro_cache", data_id)
        else:
            raise LayerNotRegisteredException("RefLyr + DataLyr + PoProLyr")

    def scc_change_snap_mode(self, s: int) -> None:
        """triggered by dialog-checkboxes
        Args:
            s (int): status 0 / 2 unchecked / checked (no Tristate) (not used here, because the status of all checkboxes must be taken into account)
        """
        # Rev. 2026-01-12

        # see enum Qgis::SnappingType https://api.qgis.org/api/classQgis.html#a20359634719ea6fe787aafc159b15739
        # Qgis.SnappingType.NoSnap => 0
        self.stored_settings.snapMode = Qgis.SnappingType.NoSnap
        if self.my_dialog.cb_snap_mode_vertex.checkState() == Qt.Checked:
            self.stored_settings.snapMode |= Qgis.SnappingType.Vertex
        if self.my_dialog.cb_snap_mode_segment.checkState() == Qt.Checked:
            self.stored_settings.snapMode |= Qgis.SnappingType.Segment
        if self.my_dialog.cb_snap_mode_middle_of_segment.checkState() == Qt.Checked:
            self.stored_settings.snapMode |= Qgis.SnappingType.MiddleOfSegment
        if self.my_dialog.cb_snap_mode_line_endpoint.checkState() == Qt.Checked:
            # since QGIS 3.20
            self.stored_settings.snapMode |= Qgis.SnappingType.LineEndpoint

        self.stored_settings.snapTolerance = self.my_dialog.qsb_snap_tolerance.value()

        self.sys_apply_snapping_config()

        self.dlg_refresh_settings()

    def ssc_data_lyr_reference_field(self) -> None:
        """change Reference-id-field of Data-Layer-Reference-field in QComboBox
        unsets some follow-up-settings, which possibly don't fit anymore and have to be reconfigured by the user
        """
        # Rev. 2026-01-12
        self.stored_settings.dataLyrReferenceFieldName = (
            self.my_dialog.qcbn_data_lyr_reference_field.currentData(
                Qt_Roles.RETURN_VALUE
            )
        )

        self.sys_restart_session()

    def sys_restart_session(self):
        """restart session after configuration changes:
        store current settings
        restore current settings
        restore derived_settings
        reset dialog
        """
        # Rev. 2026-01-12

        self.lact_remove_layer_actions()
        self.cvs_hide_markers()
        self.sys_store_settings()
        self.stored_settings = StoredSettings()
        self.session_data = SessionData()
        self.sys_restore_stored_settings()
        self.sys_restore_derived_settings()

        self.dlg_reset()

    def ssc_ref_lyr(self) -> None:
        """change Reference-Layer in QComboBox"""
        # Rev. 2026-01-12
        self.stored_settings.refLyrId = self.my_dialog.qcbn_ref_lyr.currentData(
            Qt_Roles.RETURN_VALUE
        )
        self.sys_restart_session()


    def ssc_pp_ref_lyr(self) -> None:
        """change PostProcessing-Reference-Layer in QComboBox"""
        # Rev. 2026-01-12
        self.stored_settings.poProRefLyrId = None
        self.stored_settings.poProRefLyrIdFieldName = None

        self.session_data.po_pro_cache = dict()

        self.stored_settings.poProRefLyrId = self.my_dialog.qcbn_pp_ref_lyr.currentData(
            Qt_Roles.RETURN_VALUE
        )
        self.sys_connect_po_pro_ref_layer()
        self.dlg_refresh_po_pro_settings()
        self.dlg_refresh_po_pro_edit()
        self.dlg_refresh_po_pro_selection()

    def ssc_pp_ref_lyr_id_field(self) -> None:
        """change PostProcessing-Reference-Layer-ID-Field in QComboBox
        """
        # Rev. 2026-01-12
        self.session_data.po_pro_cache = dict()

        self.stored_settings.poProRefLyrIdFieldName = (
            self.my_dialog.qcbn_pp_ref_lyr_id_field.currentData(Qt_Roles.RETURN_VALUE)
        )
        self.sys_restart_session()

    def ssc_ref_lyr_id_field(self) -> None:
        """change Reference-Layer-ID-Field in QComboBox
        this can be any unique field, f.e. the usual numerical auto-incrementing fid-field
        affects SVS.REFERENCE_LAYER_USABLE in self.system_vs
        """
        # Rev. 2026-01-12
        self.stored_settings.refLyrIdFieldName = (
            self.my_dialog.qcbn_ref_lyr_id_field.currentData(Qt_Roles.RETURN_VALUE)
        )
        self.sys_restart_session()

    def ssc_data_lyr(self) -> None:
        """change Data-Layer in QComboBox"""
        # Rev. 2026-01-12
        self.stored_settings.dataLyrId = self.my_dialog.qcbn_data_lyr.currentData(
            Qt_Roles.RETURN_VALUE
        )

        self.sys_restart_session()

    def ls_data_lyr_editCommandStarted(self, edit_cmd):
        """triggered if beginEditCommand(edit_cmd) is called with dataLyr
        this happens with interactive geometry-edits ('update_lol_feature','update_pol_feature')
        or with submit of feature-form ('Attributes changed', update and insert),  or in table ('Attribute changed')
        or in FIeld calculator ('Field calculator' triggered once even for multiple features)
        but only once per command, even if multiple attributes have changed (stationing-from + stationing-to)
        therefore prefered to attributeValueChanged, which fires once for every attribute
        disadvantage: no control, which attribute has changed
        """
        # Rev. 2026-01-12
        self.session_data.last_data_lyr_edit_cmd = edit_cmd
        self.session_data.edited_data_fids = set()

    def ls_data_lyr_editCommandEnded(self):
        """triggered, if the started edit-command has succesfull ended:
        check, if the logged edited_data_fids affects a feature in self.session_data.selected_data_fids
        """
        # Rev. 2026-01-12
        affected_data_fids = self.session_data.selected_data_fids.intersection(
            self.session_data.edited_data_fids
        )

        if affected_data_fids:
            self.dlg_refresh_feature_selection()


        self.session_data.edited_data_fids = set()

        if (
            SVS.ALL_LAYERS_CONNECTED in self.system_vs
            and self.derived_settings.showLyr.dataProvider().name() == "virtual"
        ):
            # non-virtual (==ogr-Layer from external database) only need to reload after commit
            # note: triggerRepaint() similar to reload()
            self.derived_settings.showLyr.reload()

    def tool_format_number(self, number: numbers.Number) -> str:
        """type-check and number-format dependend on type
        used inside my_dialog.qtrv_feature_selection/qtrv_po_pro_selection

        Args:
            number (numbers.Number)

        Returns:
            str ('NaN' if number is not numeric, f.e. NULL or None)
        """
        # Rev. 2026-01-12
        if isinstance(number, numbers.Number):
            if isinstance(number, int):
                # return ints as string
                return str(number)
            else:
                # return floats formatted
                return self.my_locale.toString(
                    number,
                    "f",
                    self.stored_settings.displayPrecision,
                )
        else:
            return "NaN"


    def dlg_show_help(self):
        """opens documentation according to current opened tab
        note: PoL and LoL use the same documentation
        """
        # Rev. 2026-01-12

        # use tab-key as hashtag
        # Note: hash/search... not recognized with local urls under Windows/Chrome,
        # perhaps because file:// does not support parameters, while http:// or entered URLs in Browser-Adress-Bar does (Bug?)
        # so only the website is opened without scroll to the hash
        # therefore no local help-files, but the web-based solution


        # necessary: the registered tab-ids in self.dialog_tabs are used as hash for the opened html-file and must have according element-ids
        tab_id = self.dialog_tabs_reverse.get(self.my_dialog.tbw_central.currentIndex())

        # two versions implemented: de (german) and en (all other languages)
        # my_locale.name() is a string composed of language, underscore and country'de_DE', 'de_AT', 'de_CH', 'de_BE', 'de_LI'... -> 'de'

        release = "2.1.0"
        language = "en"
        if self.my_locale.name()[0:2] == "de":
            language = "de"

        url = f"http://kni-online.de/LinearReferencing/Release%20{release}/index.{language}.html#{tab_id}"
        webbrowser.open_new_tab(url)


    def ls_data_lyr_attributeValueChanged(self, fid: int, idx: int, value: Any):
        """triggered by any change of attribute-value
        triggered once for every feature and every attribute,
        f. e. moveSegment => stationing_from + stationing_to triggered
        or a bulk-field-edit from Field-Calculator: triggered once for each feature
        Usage here:
        Log all edited feature-ids for later ls_data_lyr_editCommandEnded to check, if a listed feature was affected
        and the (complete) feature-selection has to be refreshed


        Args:
            fid (int): feature-id
            idx (int): field-index
            value (Any): altered value
        """
        # Rev. 2026-01-12
        # log each field-edit, not only geometry-affecting
        self.session_data.edited_data_fids.add(fid)

    def ls_data_lyr_committedAttributeValuesChanges(
        self, layer_id: str, fid_attribute_map: dict
    ):
        """Emitted when attribute value changes are saved to the provider,
        emitted *after* commit and only *once*, if edit-session ends and data is saved or on intermediate saves, but only if there are features with changed values
        emitted if new features are committed first time
        not emitted on geometry-only edits

        Note:
            signal emitted *before* editingStopped

        Args:
            layer_id (str)
            fid_attribute_map (dict):
                key 1: fid
                value: sub-dict mit key attribut-index and value changed value
                f.e. {4: {2: 22501.0}} => fid 4, attribute nr. 2 was changed to 22501
        """
        # Rev. 2026-01-12
        # indices of fields in dataLyr for check if dlg_reset_feature_selection is necessary
        if SVS.REFERENCE_AND_DATA_LAYER_CONNECTED in self.system_vs:
            geom_idcs, check_idcs = self.tool_get_data_lyr_indices()

            refresh_show_lyr = False
            for data_fid, changed_attributes in fid_attribute_map.items():
                for field_index, changed_value in changed_attributes.items():
                    refresh_show_lyr |= field_index in geom_idcs

            if (
                refresh_show_lyr
                and SVS.ALL_LAYERS_CONNECTED in self.system_vs
                and self.derived_settings.showLyr.dataProvider().name() != "virtual"
            ):
                # refresh showLyr, if linear-referencing attribute was changed
                # here only for non-virtual show-layers:
                # because of committ any non-virtual (== ogr) layer will reflect these changes
                # and any virtual layer will already be reloaded via editCommandEnded
                # triggerRepaint is similar
                self.derived_settings.showLyr.reload()

    def ls_data_lyr_editingStarted(self):
        """Emitted when editing-session on this layer has started.
        set system_vs (instead of sys_restore_derived_settings) to enable some edit-buttons
        """
        # Rev. 2026-01-12
        self.system_vs |= SVS.DATA_LAYER_EDITABLE
        self.dlg_refract_po_pro_selection()
        self.dlg_refract_measurement()
        self.dlg_refract_po_pro_edit()
        self.dlg_refract_feature_selection()

    def ls_data_lyr_subsetStringChanged(self):
        """layers filter has changed => refresh all affected dialog-widgets"""
        # Rev. 2026-01-12
        self.dlg_refresh_feature_selection()
        self.dlg_refresh_po_pro_selection()
        self.dlg_refresh_po_pro_edit()
        self.dlg_refresh_measurement

    def sys_disconnect_show_lyr(self):
        """disconnects the registered show-layer"""
        # Rev. 2026-01-12
        try:
            if self.derived_settings.showLyr:
                action_ids = [
                    self._zoom_pol_feature_act_id,
                    self._show_feature_form_act_id,
                    self._zoom_lol_feature_act_id,
                ]
                action_list = [
                    action
                    for action in self.derived_settings.showLyr.actions().actions()
                    if action.id() in action_ids
                ]
                for action in action_list:
                    self.derived_settings.showLyr.actions().removeAction(action.id())

                self.derived_settings.showLyr.reload()

            self.stored_settings.showLyrId = None
            self.stored_settings.showLyrBackReferenceFieldName = None
            self.derived_settings.showLyr = None
            self.derived_settings.showLyrBackReferenceField = None

            self.dlg_populate_settings()
        except Exception as e:
            # RuntimeError: wrapped C/C++ object of type QgsVectorLayer has been deleted
            pass
        self.system_vs &= ~SVS.SHOW_LAYER_CONNECTED

    def sys_store_settings(self):
        """store all permanent settings to QgsProject.instance()
        the "internal" values (with underscores) are stored (with underscores too) and restored later
        Triggered on sys_unload and QgsProject.instance().writeProject(...) *before* the project is saved to file
        changes only appear, if the project is saved to disk

        Note:
            StoredSettings use partially different keys for LolEvt/PolEvt
        """
        # Rev. 2026-01-12
        # Note: /{type(self).__name__}/ => different QgsProject.instance()-storage-keys via prepended "LolEvt"/"PolEvt"
        for prop_name in self.stored_settings._str_props:
            prop_value = getattr(self.stored_settings, prop_name)
            key = f"/{type(self).__name__}/{prop_name}"
            QgsProject.instance().writeEntry("LinearReferencing", key, prop_value)

        for prop_name in self.stored_settings._int_props:
            prop_value = getattr(self.stored_settings, prop_name)
            key = f"/{type(self).__name__}/{prop_name}"
            QgsProject.instance().writeEntry("LinearReferencing", key, prop_value)

        for prop_name in self.stored_settings._bool_props:
            prop_value = getattr(self.stored_settings, prop_name)
            key = f"/{type(self).__name__}/{prop_name}"
            QgsProject.instance().writeEntryBool("LinearReferencing", key, prop_value)

        for prop_name in self.stored_settings._double_props:
            prop_value = getattr(self.stored_settings, prop_name)
            key = f"/{type(self).__name__}/{prop_name}"
            QgsProject.instance().writeEntryDouble("LinearReferencing", key, prop_value)

    def ssc_show_layer(self) -> None:
        """change Show-Layer in QComboBox, items are filtered to suitable layer-types"""
        # Rev. 2026-01-12
        self.stored_settings.showLyrId = self.my_dialog.qcbn_show_lyr.currentData(
            Qt_Roles.RETURN_VALUE
        )

        self.sys_restart_session()

    def st_select_in_layer(self, data_fid):
        """selects/unselects feature in data- and show-layer(s) from qtrv_feature_selection
        :param data_fid:
        """
        # Rev. 2026-01-12
        try:
            selection_mode = "replace_selection"
            if check_mods("s"):
                selection_mode = "add_to_selection"
            elif check_mods("c"):
                selection_mode = "remove_from_selection"

            data_feature = self.tool_get_data_feature(data_fid=data_fid)
            self.dlg_select_feature_selection_row(data_fid)

            show_fid = None
            if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                data_id = data_feature[self.stored_settings.dataLyrIdFieldName]

                try:
                    show_feature = self.tool_get_show_feature(data_id=data_id)
                    show_fid = show_feature.id()
                except:
                    show_fid = None

            if selection_mode == "replace_selection":
                self.derived_settings.dataLyr.removeSelection()
                self.derived_settings.dataLyr.select(data_fid)
                if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                    self.derived_settings.showLyr.removeSelection()
                    if show_fid is not None:
                        self.derived_settings.showLyr.select(show_fid)
            elif selection_mode == "remove_from_selection":
                self.derived_settings.dataLyr.deselect(data_fid)
                if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                    if show_fid is not None:
                        self.derived_settings.showLyr.deselect(show_fid)
            else:
                self.derived_settings.dataLyr.select(data_fid)
                if SVS.SHOW_LAYER_CONNECTED in self.system_vs:
                    if show_fid is not None:
                        self.derived_settings.showLyr.select(show_fid)

        except Exception as e:
            self.sys_log_exception(e)

    def dlg_reset_ref_lyr_select(self):
        """resets qcbn_ref_lyr_select and some QActions"""
        # Rev. 2026-01-12
        if self.my_dialog:
            self.my_dialog.qcbn_ref_lyr_select.clear()
            self.my_dialog.qcbn_ref_lyr_select.setDisabled(True)

            disable_actions = [
                self.qact_open_ref_table,
                self.qact_open_ref_form,
                self.qact_zoom_ref_feature,
                self.qact_select_in_ref_layer,
            ]
            for action in disable_actions:
                action.setDisabled(True)

            self.my_dialog.qlbl_selected_ref_lyr.clear()




    def dlg_populate_ref_lyr_select(self):
        """populates some refLyr-dependend-widgets in Measurement-Section
        independend from session_data.lr_geom_current"""
        # Rev. 2026-01-12
        if self.my_dialog and SVS.REFERENCE_LAYER_USABLE in self.system_vs:
            column_settings = [
                # Feld-Inhalte des Layers via QGis-expressions
                {
                    "display_expression": "@id",
                    "custom_sort_expression": "@id",
                    # 'option_text_expression': self.derived_settings.refLyr.displayExpression(),
                },
                {
                    "display_expression": self.derived_settings.refLyr.displayExpression(),
                    "custom_sort_expression": self.derived_settings.refLyr.displayExpression(),
                },
                #
                {
                    "display_expression": f"format_number(length($geometry),{self.stored_settings.displayPrecision})",
                    "custom_sort_expression": "length($geometry)",
                },
            ]
            self.my_dialog.qcbn_ref_lyr_select.blockSignals(True)
            self.my_dialog.qcbn_ref_lyr_select.load_data(
                column_settings, self.derived_settings.refLyr
            )
            self.my_dialog.qcbn_ref_lyr_select.setCurrentIndex(-1)
            self.my_dialog.qcbn_ref_lyr_select.blockSignals(False)

            self.my_dialog.qlbl_selected_ref_lyr.setText(
                self.derived_settings.refLyr.name()
                + " ("
                + self.derived_settings.refLyr.wkbType().name
                + ")"
            )






    def dlg_refresh_ref_lyr_select(self):
        """wrapper to reset/populate/refract qcbn_ref_lyr_select and some QActions in Measurement-Tab"""
        # Rev. 2026-01-12
        self.dlg_reset_ref_lyr_select()
        self.dlg_populate_ref_lyr_select()
        self.dlg_refract_ref_lyr_select()

    def dlg_refract_ref_lyr_select(self):
        """refreshes some refLyr-dependend QActions in Measurement-Tab"""
        # Rev. 2026-01-12
        if self.my_dialog:
            # Note: this QAction is used multiple
            self.qact_open_ref_table.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )

            # the triggered slots of these actions require a selected row in self.my_dialog.qcbn_ref_lyr_select, which is not checked here but on runtime
            self.qact_open_ref_form.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )
            self.qact_zoom_ref_feature.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )
            self.qact_select_in_ref_layer.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )

            self.my_dialog.qcbn_ref_lyr_select.setEnabled(
                SVS.REFERENCE_LAYER_USABLE in self.system_vs
            )





    def dlg_select_feature_selection_row(
        self, data_fid: int = None, ref_fid: int = None
    ):
        """visually select row in qtrv_feature_selection

        searches for
        Qt_Roles.REF_FID in column 0 and/or
        Qt_Roles.DATA_FID in column 1

        Args:
            data_fid (int): feature-id of data-layer
            ref_fid (int): feature-id of reference-layer
        """
        # Rev. 2026-01-12

        with QSignalBlocker(self.my_dialog.qtrv_feature_selection):
            with QSignalBlocker(self.my_dialog.qtrv_feature_selection.selectionModel()):
                model = self.my_dialog.qtrv_feature_selection.model()
                selection_model = self.my_dialog.qtrv_feature_selection.selectionModel()
                selection_model.clearSelection()

                matches = []
                if ref_fid:
                    matches = model.match(
                        # search in column 0
                        model.index(0, 0),
                        Qt_Roles.REF_FID,
                        ref_fid,
                        1,
                        Qt.MatchExactly | Qt.MatchRecursive,
                    )

                elif data_fid:
                    matches = model.match(
                        # search in column 1
                        model.index(0, 1),
                        Qt_Roles.DATA_FID,
                        data_fid,
                        1,
                        Qt.MatchExactly | Qt.MatchRecursive,
                    )
                else:
                    raise ArgumentMissingException("ref_fid/data_fid")

                for index in matches:
                    # select whole row
                    selection_model.select(
                        index,
                        QItemSelectionModel.Select | QItemSelectionModel.Rows,
                    )
                    # and (re-)open the parent branch
                    self.my_dialog.qtrv_feature_selection.setExpanded(
                        index.parent(), True
                    )

        self.my_dialog.qtrv_feature_selection.update()

    def dlg_select_po_pro_selection_row(self, data_fid: int = None, ref_fid:int = None):
        """visually select row in qtrv_po_pro_selection
        Qt_Roles.REF_FID in column 0 and/or
        Qt_Roles.DATA_FID in column 1

        Args:
            data_fid (int): feature-id of data-layer
            ref_fid (int): feature-id of reference-layer
        """
        # Rev. 2026-01-12

        with QSignalBlocker(self.my_dialog.qtrv_po_pro_selection):
            with QSignalBlocker(self.my_dialog.qtrv_po_pro_selection.selectionModel()):
                model = self.my_dialog.qtrv_po_pro_selection.model()
                selection_model = self.my_dialog.qtrv_po_pro_selection.selectionModel()
                selection_model.clearSelection()
                # find the matching row, returns only 1 match, MatchRecursive for TreeView
                if data_fid:
                    matches = model.match(
                        # search in column 1
                        model.index(0, 1),
                        Qt_Roles.DATA_FID,
                        data_fid,
                        1,
                        Qt.MatchExactly | Qt.MatchRecursive,
                    )

                elif ref_fid:
                    matches = model.match(
                        # search in column 0
                        model.index(0, 0),
                        Qt_Roles.REF_FID,
                        ref_fid,
                        1,
                        Qt.MatchExactly | Qt.MatchRecursive,
                    )
                else:
                    raise ArgumentMissingException("ref_fid/data_fid")

                for index in matches:
                    # select whole row
                    selection_model.select(
                        index,
                        QItemSelectionModel.Select | QItemSelectionModel.Rows,
                    )
                    # and (re-)open the parent branch
                    self.my_dialog.qtrv_po_pro_selection.setExpanded(
                        index.parent(), True
                    )

        self.my_dialog.qtrv_po_pro_selection.update()

    def flags(self):
        """reimplemented for tool_mode 'select_features' with ShiftModifier: disables the default-zoom-behaviour
        see: https://gis.stackexchange.com/questions/449523/override-the-zoom-behaviour-of-qgsmaptoolextent
        """
        # Rev. 2026-01-12
        return super().flags() & ~QgsMapToolEmitPoint.AllowZoomRect


class SignalSlotConnections:
    """store established signal-slot-connections for later disconnect on unload or if configuration changes
    Note 1: signal-slot-connections will stay alive if only dialog is closed
    Note 2: signal-slot-connections will be garbage-collected on Plugin-unload or project-close"""
    # Rev. 2026-01-12

    def __init__(self):
        """Blanko"""
        # Rev. 2026-01-12
        self.data_lyr_connections = []
        self.ref_lyr_connections = []
        self.show_lyr_connections = []
        self.application_connections = []
        self.project_connections = []
        self.layer_tree_view_connections = []
        self.canvas_connections = []


class PoProFeature:
    """container for single selected feature for PostProcessing-Edit-purposes, partially redundant"""
    # Rev. 2026-01-12

    def __init__(self):
        """Blanko"""
        # Rev. 2026-01-12
        # feature.id()
        self.data_fid = None
        # feature-id (Attribute-Value)
        self.data_id = None

        # reference-feature.id()
        self.ref_fid = None
        # reference-feature-id (Attribute-Value)
        self.ref_id = None

        # current linear referenced geometry
        self.lr_geom_current = None
        # cached  linear referenced geometry with original values
        self.lr_geom_cached = None


class SVS(Flag):
    """SystemValidState
    Store and check system-settings
    stored in self.system_vs
    positve-flags: each bit symbolizes a fulfilled precondition
    """
    # Rev. 2026-01-12

    INIT = auto()

    REFERENCE_LAYER_EXISTS = auto()
    REFERENCE_LAYER_HAS_VALID_CRS = auto()
    REFERENCE_LAYER_IS_LINESTRING = auto()

    REFERENCE_LAYER_M_ENABLED = auto()
    REFERENCE_LAYER_Z_ENABLED = auto()
    REFERENCE_LAYER_NECESSARY_FIELDS_DEFINED = auto()
    REFERENCE_LAYER_ACTIONS_ADDED = auto()

    DATA_LAYER_EXISTS = auto()
    DATA_LAYER_NECESSARY_FIELDS_DEFINED = auto()
    DATA_LAYER_SLOTS_CONNECTED = auto()
    DATA_LAYER_ACTIONS_ADDED = auto()
    DATA_PO_PRO_LAYER_CREATED = auto()

    DATA_LAYER_INSERT_ENABLED = auto()
    DATA_LAYER_UPDATE_ENABLED = auto()
    DATA_LAYER_DELETE_ENABLED = auto()
    DATA_LAYER_EDITABLE = auto()

    SHOW_LAYER_EXISTS = auto()
    SHOW_LAYER_NECESSARY_FIELDS_DEFINED = auto()
    SHOW_LAYER_ACTIONS_ADDED = auto()

    PO_PRO_REF_LAYER_EXISTS = auto()
    # same CRS and geometry-type as Reference-Layer
    # dummy, because else it would not be connected
    PO_PRO_REF_LAYER_HAS_SAME_CRS = auto()
    PO_PRO_REF_LAYER_HAS_SAME_GEOMETRY_TYPE = auto()
    PO_PRO_REF_LAYER_NECESSARY_FIELDS_DEFINED = auto()



    # some combinations for convenience:
    REFERENCE_LAYER_USABLE = (
        REFERENCE_LAYER_EXISTS
        | REFERENCE_LAYER_HAS_VALID_CRS
        | REFERENCE_LAYER_IS_LINESTRING
    )

    REFERENCE_LAYER_CONNECTED = (
        REFERENCE_LAYER_USABLE
        | REFERENCE_LAYER_NECESSARY_FIELDS_DEFINED
        | REFERENCE_LAYER_ACTIONS_ADDED
    )

    DATA_LAYER_CONNECTED = (
        DATA_LAYER_EXISTS
        | DATA_LAYER_NECESSARY_FIELDS_DEFINED
        | DATA_LAYER_SLOTS_CONNECTED
        | DATA_LAYER_ACTIONS_ADDED
        | DATA_PO_PRO_LAYER_CREATED
    )

    REFERENCE_AND_DATA_LAYER_CONNECTED = (
        REFERENCE_LAYER_CONNECTED | DATA_LAYER_CONNECTED
    )

    PO_PRO_REF_LAYER_USABLE = (
        PO_PRO_REF_LAYER_EXISTS
        | PO_PRO_REF_LAYER_HAS_SAME_CRS
        | PO_PRO_REF_LAYER_HAS_SAME_GEOMETRY_TYPE
    )

    PO_PRO_REF_LAYER_CONNECTED = (
        PO_PRO_REF_LAYER_USABLE
        | PO_PRO_REF_LAYER_NECESSARY_FIELDS_DEFINED
    )

    SHOW_LAYER_CONNECTED = (
        SHOW_LAYER_EXISTS
        | SHOW_LAYER_NECESSARY_FIELDS_DEFINED
        | SHOW_LAYER_ACTIONS_ADDED
    )

    # not PO_PRO_REF_LAYER_CONNECTED
    ALL_LAYERS_CONNECTED = (
        REFERENCE_LAYER_CONNECTED | DATA_LAYER_CONNECTED | SHOW_LAYER_CONNECTED
    )

    def __str__(self):
        """stringify implemented for debug-purpose"""
        # Rev. 2026-01-12
        result_str = ""

        all_items = [item.name for item in self.__class__]

        longest_item = max(all_items, key=len)
        max_len = len(longest_item)

        # single-bit-flags
        for item in self.__class__:
            # format(item.value, '024b')
            if item.value == (item.value & -item.value):
                result_str += f"{item.name:<{max_len}}    {item in self}\n"
        # multi-bit-flags
        for item in self.__class__:
            # format(item.value, '024b')
            if item.value != (item.value & -item.value):
                result_str += f"* {item.name:<{max_len}}  {item in self}\n"

        return result_str


class SessionData:
    """Template for self.session_data: Session-Data"""

    def __init__(self):
        """Blanko"""
        # Rev. 2026-01-12

        # currently selected toolmode, will affect the canvasMove/Press/Release-Events
        # list of available tool_modes see self::tool_modes
        self.tool_mode = None

        # the previous selected toolmode, switch-back-by-canvas-click-convenience for tool_mode 'pausing'
        self.previous_tool_mode = None

        # canvas-point, type QgsPointXY, event.mapPoint(), canvas-projection
        # used to check, if mouse-up has the same position and for drag
        self.cvs_mouse_down = None

        # stationing for mouse-press event on canvas, type float
        self.snap_n_abs_mouse_down = None

        # linear referenced geometry for runtime-usage without feature
        # type LoL/PoL
        self.lr_geom_runtime = None

        # bundle of metadata for edit-purpose
        # one selected feature
        #edit_feature = None  # PoProFeature()
        self.edit_feature_fid = None  # int, feature.id() of selected data-feature

        # bundle of metadata for PostProcessing-edit-purpose
        # one selected feature
        self.po_pro_feature = None  # PoProFeature()

        # set of selected Data-Layer-fids for "Feature-Selection"
        # set => unique
        # {int}
        self.selected_data_fids = set()

        # offset for new self.session_data.lr_geom_runtime,
        # displayed in self.my_dialog.dspbx_offset
        # only for LoLEvt
        self.current_offset = 0

        # set by ls_data_lyr_editCommandStarted
        # Name of this command
        # not evaluated so far...
        self.last_data_lyr_edit_cmd = ""

        # feature-ids from data-layer, which have been affected by attributeValueChanged
        # will be resetted after editCommandStarted and/or editCommandEnded
        # set => unique
        self.edited_data_fids = set()

        # set True by ls_data_lyr_beforeCommitChanges
        self.committ_pending = False

        # feature-ids from last committedFeaturesAdded
        # fid after storage => provider => positive
        self.last_committed_fids = []

        # feature-ids from last featuresDeleted
        # fid from editBuffer => negative or positive, depending on previous commit
        self.last_deleted_fids = []

        # feature-ids from feature-selection => negative or positive, depending on previous commit
        self.last_selected_fids = []

        self.last_dlg_position = []

        # cached stationing-metadata of affected data-features for PostProcessing
        # key: ID of data-features
        # value: sub-dict with stationing-metas
        """
        Dictionary-Keys for LolEvt:
        self.session_data.po_pro_cache[data_id] = {
            'data_fid': ...,
            'data_id': ...,
            'stationing_from': ...,
            'stationing_to': ...,
            'offset': ...,
            'reference_id': ...
        }
        Dictionary-Keys for  PolEvt:
        self.session_data.po_pro_cache[data_id] = {
            'data_fid': ...,
            'data_id': ...,
            'stationing': ...,
            'reference_id': ...
        }
        """
        self.po_pro_cache = dict()

        self.last_feature_selection_settings = None
        self.last_po_pro_selection_settings = None

        # stored floating-dialog-size for restore
        self.dlg_last_width = 700
        self.dlg_last_height = 500

    def __str__(self):
        """stringify implemented for debug-purpose"""
        # Rev. 2026-01-12
        result_str = ""
        property_list = [
            prop
            for prop in dir(self)
            if not prop.startswith("__") and not callable(getattr(self, prop))
        ]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str


class StoredSettings:
    """template for self.stored_settings -> stored settings
    alphanumeric values like layer-IDs, colors, sizes, stored in QGis-Project
    all properties are stored in project
    defined with property-getter-and-setter to register any user-setting-changes,
    which then set the QGis-Project "dirty" and have these changes stored on sys_store_settings with save
    so every write-access to these properties, that should not set the "dirty"-Flag, must be done to the _internal-properties

    Note:
        new variables have to be taken into account in _str_props/_int_props/_bool_props/_double_props for sys_store_settings/sys_restore_stored_settings/s_store_configuration/s_restore_configuration
    """
    # Rev. 2026-01-12

    def __init__(self):
        """blanko-constructor
        """
        # Rev. 2026-01-12
        self._str_props = [
            "lrMode",
            "refLyrId",
            "refLyrIdFieldName",
            "dataLyrId",
            "dataLyrIdFieldName",
            "dataLyrReferenceFieldName",
            "showLyrId",
            "showLyrBackReferenceFieldName",
            # PolEvt only:
            "dataLyrStationingFieldName",
            # LolEvt only:
            "dataLyrStationingFromFieldName",
            "dataLyrStationingToFieldName",
            "dataLyrOffsetFieldName",
            "poProRefLyrId",
            "poProRefLyrIdFieldName"
        ]
        self._bool_props = []

        self._int_props = [
            "storagePrecision",
            "displayPrecision",
            "snapTolerance",
            "snapMode",
        ]

        self._double_props = []

        # linear-reference-mode
        # how are stationings calculated?
        # variants:
        # Nabs N natural with absolute stationings => data-layer with 2 numerical columns from/to 0...reference-line length
        # Mabs M measured with Vertex-M-values => data-layer with 2 numerical columns from/to
        # Nfract natural with relative stationings => data-layer with 2 numerical columns from/to 0...1 fraction of the reference-line length
        # perhaps extended in later releases?
        self.lrMode = "Nabs"

        # ID of the used reference-layer
        self.refLyrId = None

        # Name of the ID-Field in reference-layer
        self.refLyrIdFieldName = None

        # ID of data-layer
        self.dataLyrId = None

        # Name of ID-Field in data-layer
        self.dataLyrIdFieldName = None

        # Name of n:1 reference-Field from data-layer to reference-layer
        self.dataLyrReferenceFieldName = None

        # ID of (mostly virtual) show-layer
        self.showLyrId = None

        # 1:1-reference-field between show- and data-layer, usually the PK-Fields in both layers
        self.showLyrBackReferenceFieldName = None

        # storage-precision, stationings will get rounded
        self.storagePrecision = -1

        # display-precision fo dialog
        self.displayPrecision = 2

        # Snap-Tolerance in canvas-Pixel,
        # used as is for snap-configuration or
        self.snapTolerance = 5

        # new since rel. 2.0.1: snapMode, a combination of Qgis::SnappingType (enum)
        # see https://api.qgis.org/api/classQgis.html#a20359634719ea6fe787aafc159b15739
        # default: Segment + LineEndpoint => 2 + 32 = 34
        self.snapMode = Qgis.SnappingType.Segment | Qgis.SnappingType.LineEndpoint

        # only for PolEvt: Field for stationing in DataLyr
        self.dataLyrStationingFieldName = None

        # only for LolEvt: Field for stationing-from in DataLyr
        self.dataLyrStationingFromFieldName = None
        # only for LolEvt: Field for stationing-to in DataLyr
        self.dataLyrStationingToFieldName = None
        # only for LolEvt: Field for offset in DataLyr
        self.dataLyrOffsetFieldName = None

        # optional for PostProcessing-variant "compare-layer"
        self.poProRefLyrId = None
        self.poProRefLyrIdFieldName = None

    def __str__(self):
        """stringify implemented for debug-purpose"""
        # Rev. 2026-01-12
        result_str = ""
        property_list = [
            prop
            for prop in dir(self)
            if not prop.startswith("_") and not callable(getattr(self, prop))
        ]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str


class DerivedSettings:
    """template for self.derived_settings,
    parsed from self.stored_settings (key strings like Layer-IDs, Field-Names)
    to QGis/Qt-Objects (QgsVectorLayer, QgsField)"""
    # Rev. 2026-01-12

    def __init__(self):
        """blanko-constructor
        """
        # Rev. 2026-01-12

        self.refLyr = None
        self.refLyrIdField = None
        self.dataLyr = None
        self.dataLyrIdField = None
        self.dataLyrReferenceField = None
        self.showLyr = None
        self.showLyrBackReferenceField = None

        # for PolEvt:
        self.dataLyrStationingField = None

        # for LolEvt:
        self.dataLyrStationingFromField = None
        self.dataLyrStationingToField = None
        self.dataLyrOffsetField = None

        # user-defined Reference-Layer
        self.poProRefLyr = None
        self.poProRefLyrIdField = None




    def __str__(self):
        """stringify implemented for debug-purpose"""
        # Rev. 2026-01-12
        result_str = ""
        property_list = [
            prop
            for prop in dir(self)
            if not prop.startswith("_") and not callable(getattr(self, prop))
        ]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str
