#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* Qt-Dialogue for Point-on-line-Features

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

import os, qgis
from PyQt5 import QtCore, QtGui, QtWidgets
from LinearReferencing import tools
from LinearReferencing.icons import resources
from LinearReferencing.tools.MyToolFunctions import qt_format

class PolDialog(QtWidgets.QDockWidget):
    """Dialogue for QGis-Plugin LinearReferencing, Point-on-line-Features
    .. note::
        QtWidgets.QDockWidget ➜ dockable Window
        requires self.iface.addDockWidget(...) to be dockable within the MainWindow
    """
    # Rev. 2023-05-03

    dialog_close = QtCore.pyqtSignal(bool)
    """own dialog-close-signal, emitted on closeEvent"""

    def __init__(self, iface: qgis.gui.QgisInterface, parent=None):
        """Constructor
        :param iface:
        :param parent: optional Qt-Parent-Element for Hierarchy
        """
        # Rev. 2023-05-03
        QtWidgets.QDockWidget.__init__(self, parent)

        self.iface = iface

        self.setWindowTitle("LinearReferencing: Point-on-Line")

        # Application-Standard-Font
        base_font = QtGui.QFont()

        # base_font = QtGui.QFont("Arial")
        # base_font.setStyleHint(QtGui.QFont.SansSerif)

        default_font_s = QtGui.QFont(base_font)
        default_font_s.setPointSize(8)

        default_font_m = QtGui.QFont(base_font)
        default_font_m.setPointSize(10)

        le_font_m = QtGui.QFont(base_font)
        le_font_m.setPointSize(10)

        cbx_font_m = QtGui.QFont(base_font)
        cbx_font_m.setPointSize(9)

        spbx_font_m = QtGui.QFont(base_font)
        spbx_font_m.setPointSize(10)

        # some groups of widgets, used for adaptation of Geographic/Projected crs (units, stepwidth and range of QtWidgets.QDoubleSpinBox...)
        self.canvas_unit_widgets = []

        # these widgets get their ranges and precision-settings from current reference-layer dependend on its projection
        self.layer_unit_widgets = []
        self.layer_measure_widgets = []

        main_wdg = QtWidgets.QWidget()
        main_wdg.setLayout(QtWidgets.QVBoxLayout())

        # items in VBox:
        # 1. scrollable main content with QtWidgets.QTabWidget Measure/Edit/Settings
        # 2. status-bar
        main_wdg.layout().setContentsMargins(10, 10, 10, 0)

        self.measure_container_wdg = QtWidgets.QWidget(self)
        self.measure_container_wdg.setLayout(QtWidgets.QVBoxLayout())

        # area with edit-widgets:
        self.measure_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('PolDialog','Measurement:'), self)
        self.measure_grb.setCheckable(True)
        self.measure_grb.setChecked(True)
        self.measure_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.measure_grb.setLayout(QtWidgets.QGridLayout())
        row = 0

        sub_row = 0

        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','Reference-Line:'), self), row, 0)

        sub_wdg = QtWidgets.QWidget()
        sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        self.qcbn_snapped_ref_fid = tools.MyQtWidgets.QComboBoxN(
            self,
            col_names=['FID', 'Label', 'Length'],
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            show_clear_button=False,
            show_template="#{0} '{1}'"
        )
        self.qcbn_snapped_ref_fid.setFont(cbx_font_m)
        # self.qcbn_snapped_ref_fid.setMinimumWidth(250)
        sub_wdg.layout().addWidget(self.qcbn_snapped_ref_fid)

        self.pb_open_ref_form = QtWidgets.QPushButton(self)
        self.pb_open_ref_form.setFixedSize(20, 20)
        self.pb_open_ref_form.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_ref_form.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_ref_form.setIcon(QtGui.QIcon(':icons/mActionIdentify.svg'))
        self.pb_open_ref_form.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_ref_form.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Open attribute-form"))
        sub_wdg.layout().addWidget(self.pb_open_ref_form)

        self.pb_zoom_to_ref_feature = QtWidgets.QPushButton(self)
        self.pb_zoom_to_ref_feature.setFixedSize(20, 20)
        self.pb_zoom_to_ref_feature.setStyleSheet("QPushButton { border: none; }")
        self.pb_zoom_to_ref_feature.setIconSize(QtCore.QSize(16, 16))
        self.pb_zoom_to_ref_feature.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
        self.pb_zoom_to_ref_feature.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_zoom_to_ref_feature.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Zoom to feature"))
        sub_wdg.layout().addWidget(self.pb_zoom_to_ref_feature)

        self.measure_grb.layout().addWidget(sub_wdg, sub_row, 1, 1, 4)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','Cursor-Position x/y:'), self), sub_row, 0)
        self.le_map_x = QtWidgets.QLineEdit(self)
        self.le_map_x.setFont(le_font_m)
        self.le_map_y = QtWidgets.QLineEdit(self)
        self.le_map_y.setFont(le_font_m)
        self.measure_grb.layout().addWidget(self.le_map_x, sub_row, 1)
        self.measure_grb.layout().addWidget(self.le_map_y, sub_row, 2)
        unit_widget_2 = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_2, sub_row, 3)
        self.canvas_unit_widgets.append(unit_widget_2)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','Snapped-Position x/y:'), self), sub_row, 0)
        self.le_snap_pt1_x = QtWidgets.QLineEdit(self)
        self.le_snap_pt1_x.setFont(le_font_m)
        self.le_snap_pt1_y = QtWidgets.QLineEdit(self)
        self.le_snap_pt1_y.setFont(le_font_m)
        self.measure_grb.layout().addWidget(self.le_snap_pt1_x, sub_row, 1)
        self.measure_grb.layout().addWidget(self.le_snap_pt1_y, sub_row, 2)
        unit_widget_3 = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_3, sub_row, 3)
        self.canvas_unit_widgets.append(unit_widget_3)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','Measurement (abs/fract):'), self), sub_row, 0)
        self.dspbx_measure = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_measure.setFont(spbx_font_m)
        self.dspbx_measure.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"{b1}Measurement{b2}{hr}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}range 0...length_of_line{br}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}projection/units accordingly Reference-Layer{br}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}click/ctrl-/shift-/ctrl+shift-click 1/10/100/1000")))
        self.measure_grb.layout().addWidget(self.dspbx_measure, sub_row, 1)

        self.dspbx_measure_fract = tools.MyQtWidgets.QDoubleSpinBoxPercent(self)
        self.dspbx_measure_fract.setFont(spbx_font_m)
        self.dspbx_measure_fract.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"{b1}Measurement{b2}{hr}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}percentage{br}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}range 0...100{br}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}click/ctrl-click 1/10%")))
        self.measure_grb.layout().addWidget(self.dspbx_measure_fract, sub_row, 2)



        unit_widget_4 = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_4, sub_row, 3)
        self.layer_unit_widgets.append(unit_widget_4)
        self.measure_grb.layout().addWidget(QtWidgets.QLabel('/ [%]', self), sub_row, 4)

        sub_row += 1

        sub_wdg = QtWidgets.QWidget()
        sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        self.tbtn_move_start = QtWidgets.QToolButton(self)
        self.tbtn_move_start.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_start.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_start.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowLeft.svg'))
        self.tbtn_move_start.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"move point to reference-line-start-point"))
        sub_wdg.layout().addWidget(self.tbtn_move_start)

        self.tbtn_move_down = QtWidgets.QToolButton(self)
        self.tbtn_move_down.setAutoRepeat(True)
        self.tbtn_move_down.setAutoRepeatDelay(500)
        self.tbtn_move_down.setAutoRepeatInterval(100)
        self.tbtn_move_down.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_down.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_down.setIcon(QtGui.QIcon(':icons/mActionArrowLeft.svg'))
        self.tbtn_move_down.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"move point towards reference-line-start-point{br}click/ctrl-/shift-/ctrl+shift-click{br}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}1/10/100/1000")))
        sub_wdg.layout().addWidget(self.tbtn_move_down)

        self.pbtn_move_point = QtWidgets.QPushButton(self)
        self.pbtn_move_point.setText(QtCore.QCoreApplication.translate('PolDialog',"move Point"))
        self.pbtn_move_point.setIcon(QtGui.QIcon(':icons/linear_referencing_to_point.svg'))
        self.pbtn_move_point.setCheckable(True)
        self.pbtn_move_point.setChecked(False)
        self.pbtn_move_point.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"drag and drop point on selected reference-line"))
        sub_wdg.layout().addWidget(self.pbtn_move_point)

        self.tbtn_move_up = QtWidgets.QToolButton(self)
        self.tbtn_move_up.setAutoRepeat(True)
        self.tbtn_move_up.setAutoRepeatDelay(500)
        self.tbtn_move_up.setAutoRepeatInterval(100)
        self.tbtn_move_up.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_up.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_up.setIcon(QtGui.QIcon(':icons/mActionArrowRight.svg'))
        self.tbtn_move_up.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"move point towards reference-line-end-point{br}click/ctrl-/shift-/ctrl+shift-click{br}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}1/10/100/1000")))
        sub_wdg.layout().addWidget(self.tbtn_move_up)

        self.tbtn_move_end = QtWidgets.QToolButton(self)
        self.tbtn_move_end.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowRight.svg'))
        self.tbtn_move_end.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_end.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_end.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"move point to reference-line-end-point"))
        sub_wdg.layout().addWidget(self.tbtn_move_end)

        self.pb_pan_to_measure = QtWidgets.QPushButton(self)
        self.pb_pan_to_measure.setFixedSize(20, 20)
        self.pb_pan_to_measure.setStyleSheet("QPushButton { border: none; }")
        self.pb_pan_to_measure.setIconSize(QtCore.QSize(16, 16))
        self.pb_pan_to_measure.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
        self.pb_pan_to_measure.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_pan_to_measure.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Pan to measurement"))
        sub_wdg.layout().addWidget(self.pb_pan_to_measure)

        self.measure_grb.layout().addWidget(sub_wdg, sub_row, 0, 1, 4)

        sub_row += 1
        self.pbtn_resume_measure = QtWidgets.QPushButton(self)
        self.pbtn_resume_measure.setText(QtCore.QCoreApplication.translate('PolDialog',"Resume measurement"))
        self.pbtn_resume_measure.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_resume_measure.setIcon(QtGui.QIcon(':icons/mActionMeasure.svg'))
        self.pbtn_resume_measure.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Reset results and start new measurement"))
        self.measure_grb.layout().addWidget(self.pbtn_resume_measure, sub_row, 0, 1, 4)

        self.measure_container_wdg.layout().addWidget(self.measure_grb)

        # area with edit-widgets:
        self.edit_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('PolDialog','Storage:'))
        self.edit_grb.setCheckable(True)
        self.edit_grb.setChecked(False)
        self.edit_grb.setMaximumHeight(20)
        self.edit_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())

        self.edit_grb.setLayout(QtWidgets.QHBoxLayout())

        # area below table for editing a single feature
        # header
        self.edit_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Edit-PK:"), self))

        # and four widgets below
        # pk of the current edit feature, no further functionality
        self.le_edit_data_pk = QtWidgets.QLineEdit(self)
        self.le_edit_data_pk.setFont(le_font_m)
        # always disabled
        self.le_edit_data_pk.setEnabled(False)
        self.edit_grb.layout().addWidget(self.le_edit_data_pk)

        # save-button
        self.pbtn_update_feature = QtWidgets.QPushButton(self)
        self.pbtn_update_feature.setText(QtCore.QCoreApplication.translate('PolDialog',"Update"))
        self.pbtn_update_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_update_feature.setIcon(QtGui.QIcon(':icons/mActionFileSave.svg'))
        self.pbtn_update_feature.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Update selected feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_update_feature)

        self.pbtn_insert_feature = QtWidgets.QPushButton(self)
        self.pbtn_insert_feature.setText(QtCore.QCoreApplication.translate('PolDialog',"Insert"))
        self.pbtn_insert_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_insert_feature.setIcon(QtGui.QIcon(':icons/mActionAddManualTable.svg'))
        self.pbtn_insert_feature.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Insert feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_insert_feature)

        # delete this Segment
        self.pbtn_delete_feature = QtWidgets.QPushButton(self)
        self.pbtn_delete_feature.setText(QtCore.QCoreApplication.translate('PolDialog',"Delete"))
        self.pbtn_delete_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_delete_feature.setIcon(QtGui.QIcon(':icons/mActionDeleteSelectedFeatures.svg'))
        self.pbtn_delete_feature.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Delete selected feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_delete_feature)

        row += 1
        # self.edit_grb.hide()
        self.measure_container_wdg.layout().addWidget(self.edit_grb)

        self.selection_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('PolDialog','Feature-Selection:'), self)
        self.selection_grb.setCheckable(True)
        self.selection_grb.setChecked(False)
        self.selection_grb.setMaximumHeight(20)
        self.selection_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.selection_grb.setLayout(QtWidgets.QVBoxLayout())

        sub_sub_wdg = QtWidgets.QWidget()
        sub_sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        # button to select edit-features from show-layer
        self.pbtn_select_features = QtWidgets.QToolButton(self)
        self.pbtn_select_features.setText(QtCore.QCoreApplication.translate('PolDialog',"Select Features"))
        self.pbtn_select_features.setMinimumWidth(25)
        self.pbtn_select_features.setCheckable(True)
        self.pbtn_select_features.setIcon(QtGui.QIcon(':icons/select_point_features.svg'))
        self.pbtn_select_features.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Select features from Show-Layer:{br}click point or drag rectangle{br}{nbsp}{nbsp}{nbsp}[Shift]{nbsp}{arrow}{nbsp}append{br}{nbsp}{nbsp}{nbsp}[Ctrl]{nbsp}{nbsp}{arrow}{nbsp}remove")))
        self.pbtn_select_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_select_features)

        self.pbtn_insert_all_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_all_features.setText(QtCore.QCoreApplication.translate('PolDialog',"Insert all Features"))
        self.pbtn_insert_all_features.setMinimumWidth(25)
        self.pbtn_insert_all_features.setIcon(QtGui.QIcon(':icons/mActionSelectAll.svg'))
        self.pbtn_insert_all_features.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Insert all features from Data-Layer"))
        self.pbtn_insert_all_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_all_features)

        self.pbtn_insert_selected_data_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_selected_data_features.setText(QtCore.QCoreApplication.translate('PolDialog',"Insert selected Data-Layer-features"))
        self.pbtn_insert_selected_data_features.setMinimumWidth(25)
        self.pbtn_insert_selected_data_features.setIcon(QtGui.QIcon(':icons/mActionSelectPartial.svg'))
        self.pbtn_insert_selected_data_features.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Insert selected features from Data-Layer:{br}[{nbsp}{nbsp}{nbsp}]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}replace{br}[Shift]{nbsp}{arrow}{nbsp}append")))
        self.pbtn_insert_selected_data_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_selected_data_features)

        self.pbtn_insert_selected_show_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_selected_show_features.setText(QtCore.QCoreApplication.translate('PolDialog',"Insert selected Show-Layer-features"))
        self.pbtn_insert_selected_show_features.setMinimumWidth(25)
        self.pbtn_insert_selected_show_features.setIcon(QtGui.QIcon(':icons/mActionSelectPartial.svg'))
        self.pbtn_insert_selected_show_features.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Insert selected features from Show-Layer:{br}[{nbsp}{nbsp}{nbsp}]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow}{nbsp}replace{br}[Shift]{nbsp}{arrow}{nbsp}append")))
        self.pbtn_insert_selected_show_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_selected_show_features)

        self.selection_grb.layout().addWidget(sub_sub_wdg)

        # table to show the selected edit-features
        self.qtw_selected_pks = QtWidgets.QTableWidget()
        self.qtw_selected_pks.setFont(default_font_m)
        self.qtw_selected_pks.setIconSize(QtCore.QSize(20, 20))
        # ➜ minimum row height
        self.qtw_selected_pks.verticalHeader().setMinimumSectionSize(40)
        # ➜ minimum column width
        self.qtw_selected_pks.horizontalHeader().setMinimumSectionSize(125)
        self.qtw_selected_pks.setEditTriggers(self.qtw_selected_pks.NoEditTriggers)
        # SingleSelection
        self.qtw_selected_pks.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.qtw_selected_pks.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.qtw_selected_pks.setFocusPolicy(QtCore.Qt.NoFocus)
        self.qtw_selected_pks.setSortingEnabled(True)
        self.qtw_selected_pks.setMinimumHeight(200)

        self.qtw_selected_pks.horizontalHeader().setStretchLastSection(True)
        # self.qtw_selected_pks.setStyleSheet("QToolButton {background-color: transparent; border-style: none;}")
        self.qtw_selected_pks.setWordWrap(False)
        self.selection_grb.layout().addWidget(self.qtw_selected_pks)

        sub_sub_wdg = QtWidgets.QWidget()
        sub_sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        self.pbtn_zoom_to_feature_selection = QtWidgets.QPushButton(self)
        self.pbtn_zoom_to_feature_selection.setText(QtCore.QCoreApplication.translate('PolDialog',"Zoom to Feature-Selection"))
        self.pbtn_zoom_to_feature_selection.setMinimumWidth(25)
        self.pbtn_zoom_to_feature_selection.setIcon(QtGui.QIcon(':icons/mActionPanToSelected.svg'))
        self.pbtn_zoom_to_feature_selection.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Zoom to selected features"))
        sub_sub_wdg.layout().addWidget(self.pbtn_zoom_to_feature_selection)

        self.pbtn_clear_features = QtWidgets.QPushButton(self)
        self.pbtn_clear_features.setText(QtCore.QCoreApplication.translate('PolDialog',"Clear Feature-Selection"))
        self.pbtn_clear_features.setMinimumWidth(25)
        self.pbtn_clear_features.setIcon(QtGui.QIcon(':icons/mActionDeselectActiveLayer.svg'))
        sub_sub_wdg.layout().addWidget(self.pbtn_clear_features)

        self.selection_grb.layout().addWidget(sub_sub_wdg)

        row += 1
        # the number 1 let grow this group-box over the Stretch below, undocumented feature or bug?
        self.measure_container_wdg.layout().addWidget(self.selection_grb, 1)

        # QSpacerItem(int w, int h, QSizePolicy::Policy hPolicy = QSizePolicy::Minimum, QSizePolicy::Policy vPolicy = QSizePolicy::Minimum)
        # spacer between self.selection_grb and Status-Bar
        self.measure_container_wdg.layout().addStretch(0)

        self.settings_container_wdg = QtWidgets.QWidget(self)
        self.settings_container_wdg.setLayout(QtWidgets.QVBoxLayout())

        row = 0

        self.layers_and_fields_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('PolDialog','Layers and Fields:'), self)
        self.layers_and_fields_grb.setCheckable(True)
        self.layers_and_fields_grb.setChecked(True)
        self.layers_and_fields_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.layers_and_fields_grb.setLayout(QtWidgets.QGridLayout())

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','Reference-Layer...'), self), 0, 0)
        self.qcbn_reference_layer = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Layer', 'Geometry', 'Provider', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_reference_layer.setFont(cbx_font_m)
        self.qcbn_reference_layer.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Reference-Layer type{br}{nbsp}{nbsp}{nbsp}-linestring/m/z{br}{nbsp}{nbsp}{nbsp}-multi-linestring/m/z")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_reference_layer, 0, 1)

        self.pb_open_ref_tbl = QtWidgets.QPushButton(self)
        self.pb_open_ref_tbl.setFixedSize(20, 20)
        self.pb_open_ref_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_ref_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_ref_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_ref_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_ref_tbl.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Open attribute-table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_ref_tbl, 0, 2)

        self.pb_call_ref_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_ref_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_ref_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_ref_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_ref_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_ref_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_ref_disp_exp_dlg.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Edit Display-Expression for this layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_ref_disp_exp_dlg, 0, 3)

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','      ... ID-Field:'), self), 1, 0)
        # self.qcbn_reference_layer_id_field = QComboBox(self)

        self.qcbn_reference_layer_id_field = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Field', 'Type', 'PK', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_reference_layer_id_field.setFont(cbx_font_m)
        self.qcbn_reference_layer_id_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Assignment-key to Data-Layer{br}{nbsp}{nbsp}{nbsp}-type integer or string{br}{nbsp}{nbsp}{nbsp}-typically the PK-Field")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_reference_layer_id_field, 1, 1)

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','Data-Layer...'), self), 2, 0)

        self.qcbn_data_layer = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Layer', 'Geometry', 'Provider', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_data_layer.setFont(cbx_font_m)
        self.qcbn_data_layer.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Store measured PoL-features:{br}{nbsp}{nbsp}{nbsp}-geometry-less{br}{nbsp}{nbsp}{nbsp}-insert/update/delete-privileges")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer, 2, 1)

        self.pb_open_data_tbl = QtWidgets.QPushButton(self)
        self.pb_open_data_tbl.setFixedSize(20, 20)
        self.pb_open_data_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_data_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_data_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_data_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_data_tbl.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Open attribute table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_data_tbl, 2, 2)

        self.pb_call_data_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_data_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_data_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_data_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_data_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_data_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_data_disp_exp_dlg.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Edit Display-Expression for this layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_data_disp_exp_dlg, 2, 3)

        self.pbtn_create_data_layer = QtWidgets.QPushButton(self)
        self.pbtn_create_data_layer.setText(QtCore.QCoreApplication.translate('PolDialog',"...or create"))
        self.pbtn_create_data_layer.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Create a non-geometry GPKG-Layer for storing measurement-data"))
        self.layers_and_fields_grb.layout().addWidget(self.pbtn_create_data_layer, 2, 4)

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','      ... ID-Field:'), self), 3, 0)
        self.qcbn_data_layer_id_field = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Field', 'Type', 'PK', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_data_layer_id_field.setFont(cbx_font_m)
        self.qcbn_data_layer_id_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"ID-field{br}{nbsp}{nbsp}{nbsp}-unique, not null{br}{nbsp}{nbsp}{nbsp}-type integer or string{br}{nbsp}{nbsp}{nbsp}-typically the PK-field")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_id_field, 3, 1)

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','      ... Reference-Field:'), self), 4, 0)
        self.qcbn_data_layer_reference_field = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Field', 'Type', 'PK', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_data_layer_reference_field.setFont(cbx_font_m)
        self.qcbn_data_layer_reference_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Assignment to Reference-Layer{br}-type matching to Reference-Layer-ID-field")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_reference_field, 4, 1)

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','      ... Measurement-Field:'), self), 5, 0)
        self.qcbn_data_layer_measure_field = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Field', 'Type', 'PK', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_data_layer_measure_field.setFont(cbx_font_m)
        self.qcbn_data_layer_measure_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Field for storing measurement{br}{nbsp}{nbsp}{nbsp}-distance to the startpoint of the assigned line{br}{nbsp}{nbsp}{nbsp}-numeric data-type")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_measure_field, 5, 1)

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog','Show-Layer...'), self), 6, 0)
        self.qcbn_show_layer = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Layer', 'Geometry', 'Provider', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_show_layer.setFont(cbx_font_m)
        self.qcbn_show_layer.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Layer to show the Point-on-Line-features{br}{nbsp}{nbsp}{nbsp}-Geometry-type POINT{br}{nbsp}{nbsp}{nbsp}-Source-type virtual or ogr{br}{nbsp}{nbsp}{nbsp}(f.e. imported PostGIS or GPKG-view)")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer, 6, 1)

        self.pb_open_show_tbl = QtWidgets.QPushButton(self)
        self.pb_open_show_tbl.setFixedSize(20, 20)
        self.pb_open_show_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_show_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_show_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_show_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_show_tbl.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Open attribute-table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_show_tbl, 6, 2)

        self.pb_call_show_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_show_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_show_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_show_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_show_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_show_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_show_disp_exp_dlg.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Edit Display-Expression for this layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_show_disp_exp_dlg, 6, 3)

        self.pbtn_create_show_layer = QtWidgets.QPushButton(self)
        self.pbtn_create_show_layer.setText(QtCore.QCoreApplication.translate('PolDialog',"...or create"))
        self.pbtn_create_show_layer.setToolTip(QtCore.QCoreApplication.translate('PolDialog',"Create a virtual layer for showing the results"))
        self.layers_and_fields_grb.layout().addWidget(self.pbtn_create_show_layer, 6, 4)

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"      ... Back-Reference-Field:")), 7, 0)
        self.qcbn_show_layer_back_reference_field = tools.MyQtWidgets.QComboBoxN(
            self,
            show_clear_button=True,
            append_index_col=True,
            col_names=['Field', 'Type', 'PK', 'idx'],
            enable_row_by_col_idx=0,
            column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
            sorting_enabled=True,
            initial_sort_col_idx=3,
            initial_sort_order=QtCore.Qt.AscendingOrder,
            clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
        )
        self.qcbn_show_layer_back_reference_field.setFont(cbx_font_m)
        self.qcbn_show_layer_back_reference_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('PolDialog',"Back-reference to Data-Layer{br}{nbsp}{nbsp}{nbsp}-field-type matching to data-layer-ID-field{br}{nbsp}{nbsp}{nbsp}-typically the PK-field")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer_back_reference_field, 7, 1)

        self.settings_container_wdg.layout().addWidget(self.layers_and_fields_grb)

        self.style_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('PolDialog','Styles:'), self)
        self.style_grb.setCheckable(True)
        self.style_grb.setChecked(False)
        self.style_grb.setMaximumHeight(20)
        self.style_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.style_grb.setLayout(QtWidgets.QGridLayout())

        # see https://qgis.org/pyqgis/master/gui/QgsVertexMarker.html
        point_symbol_items = {0: "None", 1: "Cross", 2: "X", 3: "Box", 4: "Circle", 5: "Double-Triangle", 6: "Triangle", 7: "Rhombus", 8: "Inverted Triangle"}

        # see https://doc.qt.io/qt-6/qt.html#PenStyle-enum
        # 6 ➜ Qt.CustomDashLine not implemented here...
        line_symbol_items = {0: "None", 1: "Solid", 2: "Dash", 3: "Dot", 4: "DashDot", 5: "DashDotDot"}

        row = 0
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Symbol")), row, 1)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Size")), row, 2)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Width")), row, 3)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Color")), row, 4)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Fill-Color")), row, 5)

        row += 1
        # Measure-Point
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Measured-Point:")), row, 0)
        self.qcb_pt_measure_icon_type = QtWidgets.QComboBox(self)
        self.qcb_pt_measure_icon_type.setFont(cbx_font_m)
        for key in point_symbol_items:
            self.qcb_pt_measure_icon_type.addItem(point_symbol_items[key], key)

        self.style_grb.layout().addWidget(self.qcb_pt_measure_icon_type, row, 1)
        self.qspb_pt_measure_icon_size = QtWidgets.QSpinBox()
        self.qspb_pt_measure_icon_size.setFont(spbx_font_m)
        self.qspb_pt_measure_icon_size.setRange(0, 100)
        self.style_grb.layout().addWidget(self.qspb_pt_measure_icon_size, row, 2)
        self.qspb_pt_measure_pen_width = QtWidgets.QSpinBox()
        self.qspb_pt_measure_pen_width.setFont(spbx_font_m)
        self.qspb_pt_measure_pen_width.setRange(0, 20)
        self.style_grb.layout().addWidget(self.qspb_pt_measure_pen_width, row, 3)
        self.qpb_pt_measure_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_pt_measure_color, row, 4)
        self.qpb_pt_measure_fill_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_pt_measure_fill_color, row, 5)

        row += 1
        # Edit-Point
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Edit-Point:")), row, 0)
        self.qcb_pt_edit_icon_type = QtWidgets.QComboBox(self)
        self.qcb_pt_edit_icon_type.setFont(cbx_font_m)
        for key in point_symbol_items:
            self.qcb_pt_edit_icon_type.addItem(point_symbol_items[key], key)
        self.style_grb.layout().addWidget(self.qcb_pt_edit_icon_type, row, 1)
        self.qspb_pt_edit_icon_size = QtWidgets.QSpinBox()
        self.qspb_pt_edit_icon_size.setFont(spbx_font_m)
        self.qspb_pt_edit_icon_size.setRange(0, 100)
        self.style_grb.layout().addWidget(self.qspb_pt_edit_icon_size, row, 2)
        self.qspb_pt_edit_pen_width = QtWidgets.QSpinBox()
        self.qspb_pt_edit_pen_width.setFont(spbx_font_m)
        self.qspb_pt_edit_pen_width.setRange(0, 20)
        self.style_grb.layout().addWidget(self.qspb_pt_edit_pen_width, row, 3)
        self.qpb_pt_edit_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_pt_edit_color, row, 4)
        self.qpb_pt_edit_fill_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_pt_edit_fill_color, row, 5)

        row += 1
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Reference-Line:")), row, 0)
        self.qcb_ref_line_line_style = QtWidgets.QComboBox()
        self.qcb_ref_line_line_style.setFont(cbx_font_m)
        for key in line_symbol_items:
            self.qcb_ref_line_line_style.addItem(line_symbol_items[key], key)
        self.style_grb.layout().addWidget(self.qcb_ref_line_line_style, row, 1)
        self.qspb_ref_line_width = QtWidgets.QSpinBox()
        self.qspb_ref_line_width.setFont(spbx_font_m)
        self.qspb_ref_line_width.setRange(0, 20)
        self.style_grb.layout().addWidget(self.qspb_ref_line_width, row, 3)
        self.qpb_ref_line_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_ref_line_color, row, 4)

        self.settings_container_wdg.layout().addWidget(self.style_grb)

        self.store_configurations_gb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('PolDialog','Store/Restore configurations:'), self)
        self.store_configurations_gb.setCheckable(True)
        self.store_configurations_gb.setChecked(False)
        self.store_configurations_gb.setMaximumHeight(20)
        self.store_configurations_gb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.store_configurations_gb.setLayout(QtWidgets.QVBoxLayout())

        self.store_configurations_gb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('PolDialog',"Stored configurations:")))

        self.lw_stored_settings = QtWidgets.QListWidget()
        self.lw_stored_settings.setFont(default_font_m)
        self.lw_stored_settings.setFixedHeight(100)
        self.lw_stored_settings.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.store_configurations_gb.layout().addWidget(self.lw_stored_settings)

        self.pb_store_configuration = QtWidgets.QPushButton(QtCore.QCoreApplication.translate('PolDialog',"Store current configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_store_configuration)

        self.pb_restore_configuration = QtWidgets.QPushButton(QtCore.QCoreApplication.translate('PolDialog',"Restore selected configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_restore_configuration)

        self.pb_delete_configuration = QtWidgets.QPushButton(QtCore.QCoreApplication.translate('PolDialog',"Delete selected configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_delete_configuration)

        self.settings_container_wdg.layout().addWidget(self.store_configurations_gb)

        self.settings_container_wdg.layout().addStretch(1)

        self.tbw_central = QtWidgets.QTabWidget(self)
        self.tbw_central.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        self.tbw_central.addTab(self.measure_container_wdg, QtCore.QCoreApplication.translate('PolDialog','Measurement'))
        self.tbw_central.addTab(self.settings_container_wdg, QtCore.QCoreApplication.translate('PolDialog','Settings'))

        qsa_central = QtWidgets.QScrollArea()
        qsa_central.setWidgetResizable(True)
        qsa_central.setWidget(self.tbw_central)
        qsa_central.setStyleSheet("QScrollArea{border-style: none;}")

        main_wdg.layout().addWidget(qsa_central)

        # fake "statusbar" as separate widget
        # sized, styled and positioned via addStretch, setContentsMargins and setFixedHeight
        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.setStyleSheet("background-color: silver;")
        self.status_bar.setFixedHeight(20)
        self.status_bar.setFont(default_font_s)
        main_wdg.layout().addWidget(self.status_bar)

        # pendant to setCentralWidget in QMainWindow
        self.setWidget(main_wdg)


    def reset_measure_widgets(self):
        """resets dialog-widgets with measures"""
        # Rev. 2023-05-10

        with QtCore.QSignalBlocker(self.le_map_x):
            self.le_map_x.clear()

        with QtCore.QSignalBlocker(self.le_map_y):
            self.le_map_y.clear()

        with QtCore.QSignalBlocker(self.le_snap_pt1_x):
            self.le_snap_pt1_x.clear()

        with QtCore.QSignalBlocker(self.le_snap_pt1_y):
            self.le_snap_pt1_y.clear()

        with QtCore.QSignalBlocker(self.dspbx_measure):
            self.dspbx_measure.clear()

        with QtCore.QSignalBlocker(self.dspbx_measure_fract):
            self.dspbx_measure_fract.clear()

        with QtCore.QSignalBlocker(self.qcbn_snapped_ref_fid):
            self.qcbn_snapped_ref_fid.clear_selection()

    def closeEvent(self, e: QtCore.QEvent):
        """reimplemented, emitts signal when closing this widget
        :param e: <PyQt5.QtGui.QCloseEvent object at ...>
        """
        # Rev. 2023-05-03
        self.dialog_close.emit(False)
