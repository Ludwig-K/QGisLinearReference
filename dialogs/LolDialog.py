#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* Qt-Dialogue for Line-on-line-Features

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


class LolDialog(QtWidgets.QDockWidget):
    """Dialogue for QGis-Plugin LinearReferencing, Line-on-line-Features
    .. note::
        QtWidgets.QDockWidget ➜ dockable Window
        requires self.iface.addDockWidget(...) to be dockable within the MainWindow
    """
    # Rev. 2023-05-06

    dialog_close = QtCore.pyqtSignal(bool)
    """own dialog-close-signal, emitted on closeEvent"""

    def __init__(self, iface: qgis.gui.QgisInterface, parent=None):
        """Constructor
        :param parent: optional Qt-Parent-Element for Hierarchy
        """
        # Rev. 2023-05-06
        QtWidgets.QDockWidget.__init__(self, parent)

        self.iface = iface

        # initial True, but can be toggled via toggle_dockable
        self.is_dockable = True

        # store/restore the frameGeometry for toggle_dockable/set_dockable
        self.last_frame_geometry = None

        self.setWindowTitle(self.tr("Linear Referencing: Line-on-Line"))

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

        main_wdg = QtWidgets.QWidget()

        main_wdg.setLayout(QtWidgets.QVBoxLayout())

        # three items in VBox:
        # 1. small toggle-docking-icon
        # 2. main content with QtWidgets.QTabWidget Measure/Edit/Settings
        # 3. status-bar
        main_wdg.layout().setContentsMargins(10, 0, 10, 0)

        # 1. small toggle-docking-icon, right top, for toggle the sometimes annyoing docking-behavior
        # see LolEvt.toggle_dockable
        sub_widget = QtWidgets.QWidget(main_wdg)
        sub_widget.setLayout(QtWidgets.QHBoxLayout())
        sub_widget.setFixedHeight(25)
        sub_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.pb_dockable = QtWidgets.QPushButton('', sub_widget)
        self.pb_dockable.setFixedSize(16, 16)
        self.pb_dockable.setIconSize(QtCore.QSize(15, 15))
        self.pb_dockable.setStyleSheet("QPushButton { border: none}")
        self.pb_dockable.setToolTip(self.tr("toggle window dockable/undockable"))
        self.pb_dockable.setIcon(QtGui.QIcon(':icons/lock-open-variant-outline.svg'))
        self.pb_dockable.clicked.connect(self.toggle_dockable)
        sub_widget.layout().addWidget(self.pb_dockable, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        main_wdg.layout().addWidget(sub_widget)

        self.measure_container_wdg = QtWidgets.QWidget(self)
        self.measure_container_wdg.setLayout(QtWidgets.QVBoxLayout())

        row = 0

        # area with edit-widgets:
        self.measure_grb = QtWidgets.QGroupBox(self.tr('Measure:'), self)
        self.measure_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.measure_grb.setCheckable(True)
        self.measure_grb.setChecked(True)
        self.measure_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.measure_grb.setLayout(QtWidgets.QGridLayout())
        self.measure_container_wdg.layout().addWidget(self.measure_grb)

        sub_row = 0

        self.measure_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Reference-Line:'), self), row, 0)

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
        self.qcbn_snapped_ref_fid.setMinimumWidth(250)
        sub_wdg.layout().addWidget(self.qcbn_snapped_ref_fid)

        self.pb_open_ref_form = QtWidgets.QPushButton(self)
        self.pb_open_ref_form.setFixedSize(20, 20)
        self.pb_open_ref_form.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_ref_form.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_ref_form.setIcon(QtGui.QIcon(':icons/mActionIdentify.svg'))
        self.pb_open_ref_form.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_ref_form.setToolTip(self.tr("Open Form"))
        sub_wdg.layout().addWidget(self.pb_open_ref_form)

        self.pb_zoom_to_ref_feature = QtWidgets.QPushButton(self)
        self.pb_zoom_to_ref_feature.setFixedSize(20, 20)
        self.pb_zoom_to_ref_feature.setStyleSheet("QPushButton { border: none; }")
        self.pb_zoom_to_ref_feature.setIconSize(QtCore.QSize(16, 16))
        self.pb_zoom_to_ref_feature.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
        self.pb_zoom_to_ref_feature.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_zoom_to_ref_feature.setToolTip(self.tr("Zoom to Feature"))
        sub_wdg.layout().addWidget(self.pb_zoom_to_ref_feature)

        sub_wdg.layout().addStretch()

        sub_wdg.layout().addWidget(QtWidgets.QLabel(self.tr('Offset:'), self))
        self.dspbx_offset = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_offset.setFont(spbx_font_m)
        self.dspbx_offset.setRange(-99999999, 99999999)
        self.dspbx_offset.setToolTip(self.tr("Segment-distance to reference-line\n   > 0 left\n   < 0 right\n   ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000"))
        sub_wdg.layout().addWidget(self.dspbx_offset)
        self.measure_grb.layout().addWidget(sub_wdg, sub_row, 1, 1, 4)

        unit_widget_1 = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_1, sub_row, 5)
        self.layer_unit_widgets.append(unit_widget_1)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Cursor-Position x/y:'), self), sub_row, 0)
        self.le_map_x = QtWidgets.QLineEdit(self)
        self.le_map_x.setFont(le_font_m)
        self.le_map_y = QtWidgets.QLineEdit(self)
        self.le_map_y.setFont(le_font_m)
        self.measure_grb.layout().addWidget(self.le_map_x, sub_row, 1, 1, 2)
        self.measure_grb.layout().addWidget(self.le_map_y, sub_row, 3, 1, 2)
        unit_widget_2 = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_2, sub_row, 5)
        self.canvas_unit_widgets.append(unit_widget_2)

        sub_row += 1
        from_lbl = QtWidgets.QLabel(self.tr('From:'), self)
        to_lbl = QtWidgets.QLabel(self.tr('To:'), self)
        to_lbl.setMargin(2)
        from_lbl.setFixedWidth(200)
        from_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)
        from_lbl.setMargin(2)
        to_lbl.setFixedWidth(200)
        to_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)
        # tricky/buggy?: without background-color there appears no border-bottom
        from_lbl.setStyleSheet("background-color: transparent; color:green; border-bottom: 2px solid green;")
        to_lbl.setStyleSheet("background-color: transparent; color: red; border-bottom: 2px solid red;")

        self.measure_grb.layout().addWidget(from_lbl, sub_row, 1, 1, 2, QtCore.Qt.AlignCenter)
        self.measure_grb.layout().addWidget(to_lbl, sub_row, 3, 1, 2, QtCore.Qt.AlignCenter)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Snapped Point x/y:'), self), sub_row, 0)
        self.le_snap_pt_from_x = QtWidgets.QLineEdit(self)
        self.le_snap_pt_from_x.setFont(le_font_m)
        self.le_snap_pt_from_y = QtWidgets.QLineEdit(self)
        self.le_snap_pt_from_y.setFont(le_font_m)
        self.le_snap_pt_to_x = QtWidgets.QLineEdit(self)
        self.le_snap_pt_to_x.setFont(le_font_m)
        self.le_snap_pt_to_y = QtWidgets.QLineEdit(self)
        self.le_snap_pt_to_y.setFont(le_font_m)
        self.measure_grb.layout().addWidget(self.le_snap_pt_from_x, sub_row, 1)
        self.measure_grb.layout().addWidget(self.le_snap_pt_from_y, sub_row, 2)
        self.measure_grb.layout().addWidget(self.le_snap_pt_to_x, sub_row, 3)
        self.measure_grb.layout().addWidget(self.le_snap_pt_to_y, sub_row, 4)
        unit_widget_3 = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_3, sub_row, 5)
        self.canvas_unit_widgets.append(unit_widget_3)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Measure (abs / fract):'), self), sub_row, 0)

        self.dspbx_measure_from = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_measure_from.setFont(spbx_font_m)
        self.dspbx_measure_from.setToolTip(self.tr("Measure From-Point\n - range 0...length_of_line\n - units accordingly Layer-Projection\n - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000"))
        self.measure_grb.layout().addWidget(self.dspbx_measure_from, sub_row, 1)

        self.dspbx_measure_fract_from = tools.MyQtWidgets.QDoubleSpinBoxPercent(self)
        self.dspbx_measure_fract_from.setFont(spbx_font_m)
        self.dspbx_measure_fract_from.setToolTip(self.tr("Measure-From as percentage\n - range 0...100"))

        self.measure_grb.layout().addWidget(self.dspbx_measure_fract_from, sub_row, 2)

        self.dspbx_measure_to = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_measure_to.setFont(spbx_font_m)
        # valueChanged-Signal only with [Enter], not with every change
        self.dspbx_measure_to.setToolTip(self.tr("Measure To-Point\n - range 0...length_of_line\n - units accordingly Layer-Projection\n - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000"))
        self.measure_grb.layout().addWidget(self.dspbx_measure_to, sub_row, 3)

        self.dspbx_measure_fract_to = tools.MyQtWidgets.QDoubleSpinBoxPercent(self)
        self.dspbx_measure_fract_to.setFont(spbx_font_m)
        self.dspbx_measure_fract_to.setToolTip(self.tr("Measure-To as percentage\n - range 0...100"))
        self.measure_grb.layout().addWidget(self.dspbx_measure_fract_to, sub_row, 4)

        unit_widget_4_b = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_4_b, sub_row, 5)
        self.layer_unit_widgets.append(unit_widget_4_b)

        self.measure_grb.layout().addWidget(QtWidgets.QLabel('/ [%]', self), sub_row, 6)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Length:'), self), sub_row, 0)

        sub_wdg = QtWidgets.QWidget()
        sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        self.tbtn_move_segment_start = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_start.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_start.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_start.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowLeft.svg'))
        self.tbtn_move_segment_start.setToolTip(self.tr("moves segment to reference-line-start-point"))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_start)
        
        self.tbtn_prepend_segment = QtWidgets.QToolButton(self)
        self.tbtn_prepend_segment.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_prepend_segment.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_prepend_segment.setIcon(QtGui.QIcon(':icons/mActionDoubleArrowLeft.svg'))
        self.tbtn_prepend_segment.setToolTip(self.tr("'prepend' segment (new to-measure == old from-measure)"))
        sub_wdg.layout().addWidget(self.tbtn_prepend_segment)

        self.tbtn_move_segment_down = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_down.setAutoRepeat(True)
        self.tbtn_move_segment_down.setAutoRepeatDelay(500)
        self.tbtn_move_segment_down.setAutoRepeatInterval(100)
        self.tbtn_move_segment_down.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_down.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_down.setIcon(QtGui.QIcon(':icons/mActionArrowLeft.svg'))
        self.tbtn_move_segment_down.setToolTip(self.tr("move segment towards reference-line-start-point\n   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000"))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_down)

        self.dspbx_distance = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_distance.setFont(spbx_font_m)
        self.dspbx_distance.setToolTip(self.tr("enlarge/shrink segment\n   - keeps From-Point, moves To-Point\n   - units accordingly Layer-Projection\n   - ctrl/shift/ctrl+shift spinbutton-click-modifiers with factors 10/100/1000"))
        sub_wdg.layout().addWidget(self.dspbx_distance)

        self.tbtn_move_segment_up = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_up.setAutoRepeat(True)
        self.tbtn_move_segment_up.setAutoRepeatDelay(500)
        self.tbtn_move_segment_up.setAutoRepeatInterval(100)
        self.tbtn_move_segment_up.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_up.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_up.setIcon(QtGui.QIcon(':icons/mActionArrowRight.svg'))
        self.tbtn_move_segment_up.setToolTip(self.tr("move segment towards reference-line-end-point\n   - ctrl/shift/ctrl+shift click-modifiers with factors 10/100/1000"))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_up)

        self.tbtn_append_segment = QtWidgets.QToolButton(self)
        self.tbtn_append_segment.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_append_segment.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_append_segment.setIcon(QtGui.QIcon(':icons/mActionDoubleArrowRight.svg'))
        self.tbtn_append_segment.setToolTip(self.tr("'append' segment (new from-measure == old to-measure)"))
        sub_wdg.layout().addWidget(self.tbtn_append_segment)

        self.tbtn_move_segment_end = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_end.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowRight.svg'))
        self.tbtn_move_segment_end.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_end.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_end.setToolTip(self.tr("move segment to reference-line-end-point"))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_end)

        self.pb_zoom_to_segment = QtWidgets.QPushButton(self)
        self.pb_zoom_to_segment.setFixedSize(20, 20)
        self.pb_zoom_to_segment.setStyleSheet("QPushButton { border: none; }")
        self.pb_zoom_to_segment.setIconSize(QtCore.QSize(16, 16))
        self.pb_zoom_to_segment.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
        self.pb_zoom_to_segment.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_zoom_to_segment.setToolTip(self.tr("zoom to segment"))
        sub_wdg.layout().addWidget(self.pb_zoom_to_segment)

        self.measure_grb.layout().addWidget(sub_wdg, sub_row, 1, 1, 4)

        unit_widget_4_c = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_4_c, sub_row, 5)
        self.layer_unit_widgets.append(unit_widget_4_c)

        sub_row += 1

        self.pbtn_move_from_point = QtWidgets.QPushButton(self)
        self.pbtn_move_from_point.setText(self.tr("move From-Point"))
        self.pbtn_move_from_point.setIcon(QtGui.QIcon(':icons/linear_referencing_point.svg'))
        self.pbtn_move_from_point.setCheckable(True)
        self.pbtn_move_from_point.setChecked(False)
        self.pbtn_move_from_point.setToolTip(self.tr("move From-Point by mouse-down and drag on selected reference-line"))
        self.measure_grb.layout().addWidget(self.pbtn_move_from_point, sub_row, 1, 1, 2)

        self.pbtn_move_to_point = QtWidgets.QPushButton(self)
        self.pbtn_move_to_point.setText(self.tr("move To-Point"))
        self.pbtn_move_to_point.setIcon(QtGui.QIcon(':icons/linear_referencing_to_point.svg'))
        self.pbtn_move_to_point.setCheckable(True)
        self.pbtn_move_to_point.setChecked(False)
        self.pbtn_move_to_point.setToolTip(self.tr("move To-Point by mouse-down and drag on selected reference-line"))
        self.measure_grb.layout().addWidget(self.pbtn_move_to_point, sub_row, 3, 1, 2)

        sub_row += 1

        # change offset of current segment interactive on canvas
        self.pb_move_segment = QtWidgets.QPushButton(self)
        self.pb_move_segment.setText(self.tr("Move segment"))
        self.pb_move_segment.setIconSize(QtCore.QSize(25, 25))
        self.pb_move_segment.setIcon(QtGui.QIcon(':icons/mActionMoveFeatureCopyLine.svg'))
        self.pb_move_segment.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_move_segment.setToolTip(self.tr("Move segment interactive:\n   [-]\t-> change measure, keep offset\n [shift]\t-> change offset, keep measure\n  [ctrl]\t-> change offset and measure"))
        self.pb_move_segment.setCheckable(True)
        self.measure_grb.layout().addWidget(self.pb_move_segment, sub_row, 1, 1, 4)

        sub_row += 1

        self.pbtn_resume_measure = QtWidgets.QPushButton(self)
        self.pbtn_resume_measure.setText(self.tr("Resume measure"))
        self.pbtn_resume_measure.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_resume_measure.setIcon(QtGui.QIcon(':icons/mActionMeasure.svg'))
        self.pbtn_resume_measure.setToolTip(self.tr("Reset results and start new measure"))
        self.measure_grb.layout().addWidget(self.pbtn_resume_measure, sub_row, 1, 1, 4)

        sub_row += 1

        row += 1

        # area with edit-widgets:
        self.edit_grb = QtWidgets.QGroupBox(self.tr('Storage:'), self)
        self.edit_grb.setCheckable(True)
        self.edit_grb.setChecked(False)
        self.edit_grb.setMaximumHeight(20)
        self.edit_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.edit_grb.setLayout(QtWidgets.QHBoxLayout())
        self.measure_container_wdg.layout().addWidget(self.edit_grb)

        self.edit_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Selected PK:"), self))

        # pk of the current edit feature
        self.le_edit_data_pk = QtWidgets.QLineEdit(self)
        # always disabled
        self.le_edit_data_pk.setEnabled(False)
        self.edit_grb.layout().addWidget(self.le_edit_data_pk)

        # add this Segment to data-layer
        self.pbtn_update_feature = QtWidgets.QPushButton(self)
        self.pbtn_update_feature.setText(self.tr("Update"))
        self.pbtn_update_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_update_feature.setIcon(QtGui.QIcon(':icons/mActionFileSave.svg'))
        self.pbtn_update_feature.setToolTip(self.tr("Update selected feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_update_feature)

        # add this Segment to data-layer
        self.pbtn_insert_feature = QtWidgets.QPushButton(self)
        self.pbtn_insert_feature.setText(self.tr("Insert"))
        self.pbtn_insert_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_insert_feature.setIcon(QtGui.QIcon(':icons/mActionAddManualTable.svg'))
        self.pbtn_insert_feature.setToolTip(self.tr("Insert feature / duplicate selected feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_insert_feature)

        # delete this Segment
        self.pbtn_delete_feature = QtWidgets.QPushButton(self)
        self.pbtn_delete_feature.setText(self.tr("Delete"))
        self.pbtn_delete_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_delete_feature.setIcon(QtGui.QIcon(':icons/mActionDeleteSelectedFeatures.svg'))
        self.pbtn_delete_feature.setToolTip(self.tr("Delete selected feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_delete_feature)

        self.measure_container_wdg.layout().addWidget(self.edit_grb)

        row += 1

        self.selection_grb = QtWidgets.QGroupBox(self.tr('Feature-Selection:'), self)
        self.selection_grb.setCheckable(True)
        self.selection_grb.setChecked(False)
        self.selection_grb.setMaximumHeight(20)
        self.selection_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.selection_grb.setLayout(QtWidgets.QVBoxLayout())

        sub_row = 0

        sub_sub_wdg = QtWidgets.QWidget()
        sub_sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        # button to select edit-features from show-layer
        self.pbtn_select_features = QtWidgets.QToolButton(self)
        self.pbtn_select_features.setCheckable(True)
        self.pbtn_select_features.setText(self.tr("Select Feature(s)"))
        self.pbtn_select_features.setMinimumWidth(25)
        self.pbtn_select_features.setIcon(QtGui.QIcon(':icons/select_point_features.svg'))
        self.pbtn_select_features.setToolTip(self.tr("Select Features from Show-Layer\n    click (point) or drag (rectangle)\n    [Shift] ➜ append\n    [Ctrl] ➜ remove"))
        self.pbtn_select_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_select_features)

        self.pbtn_insert_all_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_all_features.setText(self.tr("Insert all Features"))
        self.pbtn_insert_all_features.setMinimumWidth(25)
        self.pbtn_insert_all_features.setIcon(QtGui.QIcon(':icons/mActionSelectAll.svg'))
        self.pbtn_insert_all_features.setToolTip(self.tr("Insert all Features from Data-Layer\n    [Shift] ➜ append"))
        self.pbtn_insert_all_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_all_features)

        self.pbtn_insert_selected_data_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_selected_data_features.setText(self.tr("Insert selected Data-Layer-Features"))
        self.pbtn_insert_selected_data_features.setMinimumWidth(25)
        self.pbtn_insert_selected_data_features.setIcon(QtGui.QIcon(':icons/mActionSelectPartial.svg'))
        self.pbtn_insert_selected_data_features.setToolTip(self.tr("Insert selected Features from Data-Layer\n    [Shift] ➜ append"))
        self.pbtn_insert_selected_data_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_selected_data_features)

        self.pbtn_insert_selected_show_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_selected_show_features.setText(self.tr("Insert selected Show-Layer-Features"))
        self.pbtn_insert_selected_show_features.setMinimumWidth(25)
        self.pbtn_insert_selected_show_features.setIcon(QtGui.QIcon(':icons/mActionSelectPartial.svg'))
        self.pbtn_insert_selected_show_features.setToolTip(self.tr("Insert selected Features from Show-Layer\n    [Shift] ➜ append"))
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
        # initial sort-column and order
        self.qtw_selected_pks.sortItems(0, 0)
        self.qtw_selected_pks.setMinimumHeight(200)

        self.qtw_selected_pks.horizontalHeader().setStretchLastSection(True)
        # self.qtw_selected_pks.setStyleSheet("QToolButton {background-color: transparent; border-style: none;}")
        self.qtw_selected_pks.setWordWrap(False)

        self.selection_grb.layout().addWidget(self.qtw_selected_pks)

        sub_sub_wdg = QtWidgets.QWidget()
        sub_sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        self.pbtn_zoom_to_feature_selection = QtWidgets.QPushButton(self)
        self.pbtn_zoom_to_feature_selection.setText(self.tr("Zoom to feature-selection"))
        self.pbtn_zoom_to_feature_selection.setMinimumWidth(25)
        self.pbtn_zoom_to_feature_selection.setIcon(QtGui.QIcon(':icons/mActionPanToSelected.svg'))
        self.pbtn_zoom_to_feature_selection.setToolTip(self.tr("Zoom to selected features"))
        sub_sub_wdg.layout().addWidget(self.pbtn_zoom_to_feature_selection)

        self.pbtn_clear_features = QtWidgets.QPushButton(self)
        self.pbtn_clear_features.setText(self.tr("Clear Feature-Selection"))
        self.pbtn_clear_features.setMinimumWidth(25)
        self.pbtn_clear_features.setIcon(QtGui.QIcon(':icons/mActionDeselectActiveLayer.svg'))
        sub_sub_wdg.layout().addWidget(self.pbtn_clear_features)

        self.selection_grb.layout().addWidget(sub_sub_wdg)

        self.measure_container_wdg.layout().addWidget(self.selection_grb, 1)

        # spacer between self.selection_grb and Status-Bar
        self.measure_container_wdg.layout().addStretch(0)

        ## second tab: settings...
        row = 0

        self.layers_and_fields_grb = QtWidgets.QGroupBox(self.tr('Layers and Fields:'), self)
        self.layers_and_fields_grb.setCheckable(True)
        self.layers_and_fields_grb.setChecked(True)
        self.layers_and_fields_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.layers_and_fields_grb.setLayout(QtWidgets.QGridLayout())

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Reference-Layer...'), self), row, 0)
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
        self.qcbn_reference_layer.setToolTip(self.tr("Reference-layer, provides linestring-geometries\n  geometry-Type linestring/m/z\n  multi-linestring/m/z"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_reference_layer, row, 1)

        self.pb_open_ref_tbl = QtWidgets.QPushButton(self)
        self.pb_open_ref_tbl.setFixedSize(20, 20)
        self.pb_open_ref_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_ref_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_ref_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_ref_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_ref_tbl.setToolTip(self.tr("Open Table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_ref_tbl, row, 2)

        self.pb_call_ref_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_ref_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_ref_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_ref_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_ref_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_ref_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_ref_disp_exp_dlg.setToolTip(self.tr("Edit Display-Expression for this Layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_ref_disp_exp_dlg, row, 3)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('      ... ID-Field:'), self), row, 0)
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
        self.qcbn_reference_layer_id_field.setToolTip(self.tr("Identifier-Field, used for assignment to Data-Layer\n   type integer or string, unique, not null\n   typically the PK-Field"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_reference_layer_id_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Data-Layer...'), self), row, 0)
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
        self.qcbn_data_layer.setToolTip(self.tr("Layer for storing the attributes of Line-on-Line-features:\n   geometry-less\n   Editable\nRequired Fields:\n   ID-Field (PK)\n   Reference-Field\n   Measure-From-Field\n   Measure-To-Field\n   Offset-Field"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer, row, 1)

        self.pb_open_data_tbl = QtWidgets.QPushButton(self)
        self.pb_open_data_tbl.setFixedSize(20, 20)
        self.pb_open_data_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_data_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_data_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_data_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_data_tbl.setToolTip(self.tr("Open Table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_data_tbl, row, 2)

        self.pb_call_data_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_data_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_data_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_data_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_data_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_data_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_data_disp_exp_dlg.setToolTip(self.tr("Edit Display-Expression for this Layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_data_disp_exp_dlg, row, 3)

        self.pbtn_create_data_layer = QtWidgets.QPushButton(self)
        self.pbtn_create_data_layer.setText(self.tr("...or create"))
        self.pbtn_create_data_layer.setMaximumWidth(100)
        self.pbtn_create_data_layer.setToolTip(self.tr("Create a non-geometry GPKG-Layer for storing measure-data"))
        self.layers_and_fields_grb.layout().addWidget(self.pbtn_create_data_layer, row, 4)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('      ... ID-Field:'), self), row, 0)
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
        self.qcbn_data_layer_id_field.setToolTip(self.tr("Field with unique key,\n   type integer or string\n   typically the PK-Field"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_id_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('      ... Reference-Field:'), self), row, 0)
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
        self.qcbn_data_layer_reference_field.setToolTip(self.tr("Field for assignment to Reference-Layer\n   type matching to Reference-Layer-ID-Field"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_reference_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('      ... Measure-From-Field:'), self), row, 0)
        self.qcbn_data_layer_measure_from_field = tools.MyQtWidgets.QComboBoxN(
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
        self.qcbn_data_layer_measure_from_field.setFont(cbx_font_m)
        self.qcbn_data_layer_measure_from_field.setToolTip(self.tr("Field for storing measure-from\n   distance of segment-start to startpoint of assigned line\n   numeric type"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_measure_from_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('      ... Measure-To-Field:'), self), row, 0)
        self.qcbn_data_layer_measure_to_field = tools.MyQtWidgets.QComboBoxN(
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
        self.qcbn_data_layer_measure_to_field.setFont(cbx_font_m)
        self.qcbn_data_layer_measure_to_field.setToolTip(self.tr("Field for storing measure-to\n   distance of segment-end to startpoint of assigned line\n   numeric type"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_measure_to_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('      ... Offset-Field:'), self), row, 0)
        self.qcbn_data_layer_offset_field = tools.MyQtWidgets.QComboBoxN(
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
        self.qcbn_data_layer_offset_field.setFont(cbx_font_m)
        self.qcbn_data_layer_offset_field.setToolTip(self.tr("Field for storing offset\n   offset of the segment to assigned reference-line\n   type numeric\nValues...\n   > 0 ➜ left\n   < 0 ➜ right\n  = 0 ➜ on reference-line"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_offset_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr('Show-Layer...'), self), row, 0)
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
        self.qcbn_show_layer.setToolTip(self.tr("Layer to show the Line-on-Line-Features\nSource-Type:\n     virtual (with query to Reference- and  Data-Layer)\n     ogr (f.e. view in PostGIS or GPKG)"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer, row, 1)

        self.pb_open_show_tbl = QtWidgets.QPushButton(self)
        self.pb_open_show_tbl.setFixedSize(20, 20)
        self.pb_open_show_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_show_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_show_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_show_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_show_tbl.setToolTip(self.tr("Open Table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_show_tbl, row, 2)

        self.pb_call_show_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_show_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_show_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_show_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_show_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_show_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_show_disp_exp_dlg.setToolTip(self.tr("Edit Display-Expression for this Layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_show_disp_exp_dlg, row, 3)

        self.pbtn_create_show_layer = QtWidgets.QPushButton(self)
        self.pbtn_create_show_layer.setText(self.tr("...or create"))
        self.pbtn_create_show_layer.setMaximumWidth(100)
        self.pbtn_create_show_layer.setToolTip(self.tr("Create a virtual Layer for showing the results"))
        self.layers_and_fields_grb.layout().addWidget(self.pbtn_create_show_layer, row, 4)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(self.tr("      ... Back-Reference-Field:")), row, 0)
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
        self.qcbn_show_layer_back_reference_field.setToolTip(self.tr("Field for Back-Reference to data-layer\n   Field-Type and Contents matching to Data-Layer-ID-Field\n   typically the PK-Fields in both layers"))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer_back_reference_field, row, 1)

        self.settings_container_wdg = QtWidgets.QWidget(self)
        self.settings_container_wdg.setLayout(QtWidgets.QVBoxLayout())
        self.settings_container_wdg.layout().addWidget(self.layers_and_fields_grb)

        self.style_grb = QtWidgets.QGroupBox(self.tr('Styles:'), self)
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
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Symbol")), row, 1)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Size")), row, 2)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Width")), row, 3)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Color")), row, 4)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Fill-Color")), row, 5)

        row += 1
        # From-Point
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("From-Point:")), row, 0)
        self.qcb_from_point_icon_type = QtWidgets.QComboBox(self)
        self.qcb_from_point_icon_type.setFont(cbx_font_m)
        for key in point_symbol_items:
            self.qcb_from_point_icon_type.addItem(point_symbol_items[key], key)
        self.style_grb.layout().addWidget(self.qcb_from_point_icon_type, row, 1)
        self.qspb_from_point_icon_size = QtWidgets.QSpinBox()
        self.qspb_from_point_icon_size.setFont(spbx_font_m)
        self.qspb_from_point_icon_size.setRange(0, 100)
        self.style_grb.layout().addWidget(self.qspb_from_point_icon_size, row, 2)
        self.qspb_from_point_pen_width = QtWidgets.QSpinBox()
        self.qspb_from_point_pen_width.setFont(spbx_font_m)
        self.qspb_from_point_pen_width.setRange(0, 20)
        self.style_grb.layout().addWidget(self.qspb_from_point_pen_width, row, 3)
        self.qpb_from_point_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_from_point_color, row, 4)
        self.qpb_from_point_fill_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_from_point_fill_color, row, 5)

        row += 1
        # To-Point
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("To-Point:")), row, 0)
        self.qcb_to_point_icon_type = QtWidgets.QComboBox(self)
        self.qcb_to_point_icon_type.setFont(cbx_font_m)
        for key in point_symbol_items:
            self.qcb_to_point_icon_type.addItem(point_symbol_items[key], key)
        self.style_grb.layout().addWidget(self.qcb_to_point_icon_type, row, 1)
        self.qspb_to_point_icon_size = QtWidgets.QSpinBox()
        self.qspb_to_point_icon_size.setFont(spbx_font_m)
        self.qspb_to_point_icon_size.setRange(0, 100)
        self.style_grb.layout().addWidget(self.qspb_to_point_icon_size, row, 2)
        self.qspb_to_point_pen_width = QtWidgets.QSpinBox()
        self.qspb_to_point_pen_width.setFont(spbx_font_m)
        self.qspb_to_point_pen_width.setRange(0, 20)
        self.style_grb.layout().addWidget(self.qspb_to_point_pen_width, row, 3)
        self.qpb_to_point_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_to_point_color, row, 4)
        self.qpb_to_point_fill_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_to_point_fill_color, row, 5)

        row += 1
        # Segment-Line
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Segment-Line:")), row, 0)
        self.qcb_segment_line_line_style = QtWidgets.QComboBox()
        self.qcb_segment_line_line_style.setFont(cbx_font_m)
        for key in line_symbol_items:
            self.qcb_segment_line_line_style.addItem(line_symbol_items[key], key)
        self.style_grb.layout().addWidget(self.qcb_segment_line_line_style, row, 1)
        self.qspb_segment_line_width = QtWidgets.QSpinBox()
        self.qspb_segment_line_width.setFont(spbx_font_m)
        self.qspb_segment_line_width.setRange(0, 20)
        self.style_grb.layout().addWidget(self.qspb_segment_line_width, row, 3)
        self.qpb_segment_line_color = tools.MyQtWidgets.QPushButtonColor()
        self.style_grb.layout().addWidget(self.qpb_segment_line_color, row, 4)

        row += 1
        self.style_grb.layout().addWidget(QtWidgets.QLabel(self.tr("Reference-Line:")), row, 0)
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

        self.store_configurations_gb = QtWidgets.QGroupBox(self.tr('Store/Restore Configurations:'), self)
        self.store_configurations_gb.setCheckable(True)
        self.store_configurations_gb.setChecked(False)
        self.store_configurations_gb.setMaximumHeight(20)
        self.store_configurations_gb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.store_configurations_gb.setLayout(QtWidgets.QVBoxLayout())

        self.store_configurations_gb.layout().addWidget(QtWidgets.QLabel(self.tr("Stored Configurations:")))

        self.lw_stored_settings = QtWidgets.QListWidget()
        self.lw_stored_settings.setFont(default_font_m)
        self.lw_stored_settings.setFixedHeight(100)
        self.lw_stored_settings.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.store_configurations_gb.layout().addWidget(self.lw_stored_settings)

        self.pb_store_configuration = QtWidgets.QPushButton(self.tr("Store current configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_store_configuration)

        self.pb_restore_configuration = QtWidgets.QPushButton(self.tr("Restore selected configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_restore_configuration)

        self.pb_delete_configuration = QtWidgets.QPushButton(self.tr("Delete selected configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_delete_configuration)

        self.settings_container_wdg.layout().addWidget(self.store_configurations_gb)

        self.settings_container_wdg.layout().addStretch(1)

        self.tbw_central = QtWidgets.QTabWidget(self)

        self.tbw_central.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        self.tbw_central.addTab(self.measure_container_wdg, self.tr('Measure'))

        self.tbw_central.addTab(self.settings_container_wdg, self.tr('Settings'))

        qsa_central = QtWidgets.QScrollArea()
        qsa_central.setWidgetResizable(True)
        qsa_central.setStyleSheet("QScrollArea{border-style: none;}")
        qsa_central.setWidget(self.tbw_central)

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

    def closeEvent(self, e):
        """executed when closing this dialogue (indeed it's not destroid but hided), connected in LolEvt, triggers iface.actionPan() and hides temporal QgsVertexMarker and QgsRubberBand"""
        self.dialog_close.emit(False)

    def reset_measure_widgets(self):
        """resets dialog-widgets with measures"""
        # Rev. 2023-05-10
        with QtCore.QSignalBlocker(self.qcbn_snapped_ref_fid):
            self.qcbn_snapped_ref_fid.clear_selection()

        with QtCore.QSignalBlocker(self.le_map_x):
            self.le_map_x.clear()

        with QtCore.QSignalBlocker(self.le_map_y):
            self.le_map_y.clear()

        with QtCore.QSignalBlocker(self.le_snap_pt_from_x):
            self.le_snap_pt_from_x.clear()

        with QtCore.QSignalBlocker(self.le_snap_pt_from_y):
            self.le_snap_pt_from_y.clear()

        with QtCore.QSignalBlocker(self.le_snap_pt_to_x):
            self.le_snap_pt_to_x.clear()

        with QtCore.QSignalBlocker(self.le_snap_pt_to_y):
            self.le_snap_pt_to_y.clear()

        with QtCore.QSignalBlocker(self.dspbx_measure_from):
            self.dspbx_measure_from.clear()

        with QtCore.QSignalBlocker(self.dspbx_measure_fract_from):
            self.dspbx_measure_fract_from.clear()

        with QtCore.QSignalBlocker(self.dspbx_measure_to):
            self.dspbx_measure_to.clear()

        with QtCore.QSignalBlocker(self.dspbx_measure_fract_to):
            self.dspbx_measure_fract_to.clear()

        with QtCore.QSignalBlocker(self.dspbx_distance):
            self.dspbx_distance.clear()

    def toggle_dockable(self):
        """convenience-Function: dockable dialogs are sometimes annoying
        this toggles the dialog between
        dockable ➜ DockWidgetClosable + DockWidgetMovable + DockWidgetFloatable within QGis-MainWindow, no additional WindowTitle
        undockable ➜ QtCore.Qt.Window, TopLevel, TitleBar witz Icons, WindowStaysOnTopHint, NoDockWidgetFeatures, normal dockable to desktop-edges
        triggered and status shown by small additional icon (lock-open/close)
        :param dockable: optional, if set, sets the new state, else the current state will be taken
        """
        # Rev. 2023-04-28
        if not self.is_dockable:
            self.last_frame_geometry = self.frameGeometry()

        self.set_dockable(not self.is_dockable)
        self.show()

    def set_dockable(self, dockable):
        self.is_dockable = dockable
        if dockable:
            # late addDockWidget ➜ better look&feel
            self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
            # self.setWindowFlag(QtCore.Qt.Window)
            self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
            self.pb_dockable.setIcon(QtGui.QIcon(':icons/lock-outline.svg'))
            self.setFloating(False)
        else:
            self.iface.removeDockWidget(self)
            self.setParent(None)
            self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
            # hide the DockWindow-Toolbar, not needed because of QtCore.Qt.Window ➜ titleBar with min/max/close-buttons with same functionality
            self.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
            self.pb_dockable.setIcon(QtGui.QIcon(':icons/lock-open-variant-outline.svg'))
            if self.last_frame_geometry:
                # position at the previously stored geometry
                self.setGeometry(self.last_frame_geometry)
