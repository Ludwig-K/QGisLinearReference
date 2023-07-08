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

from LinearReferencing.tools.MyToolFunctions import qt_format


class LolDialog(QtWidgets.QDockWidget):
    """Dialogue for QGis-Plugin LinearReferencing, Line-on-line-Features
    .. note::
        QtWidgets.QDockWidget => dockable Window
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



        self.setWindowTitle("LinearReferencing: Line-on-Line")

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

        # items in VBox:
        # 1. scrollable main content with QtWidgets.QTabWidget Measure/Edit/Settings
        # 2. status-bar
        main_wdg.layout().setContentsMargins(10, 10, 10, 0)



        self.measure_container_wdg = QtWidgets.QWidget(self)
        self.measure_container_wdg.setLayout(QtWidgets.QVBoxLayout())

        row = 0

        # area with edit-widgets:
        self.measure_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('LolDialog','Measurement:'), self)
        self.measure_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.measure_grb.setCheckable(True)
        self.measure_grb.setChecked(True)
        self.measure_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.measure_grb.setLayout(QtWidgets.QGridLayout())
        self.measure_container_wdg.layout().addWidget(self.measure_grb)

        sub_row = 0

        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Reference-Line:'), self), row, 0)

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
        self.pb_open_ref_form.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Open feature-form"))
        sub_wdg.layout().addWidget(self.pb_open_ref_form)

        self.pb_zoom_to_ref_feature = QtWidgets.QPushButton(self)
        self.pb_zoom_to_ref_feature.setFixedSize(20, 20)
        self.pb_zoom_to_ref_feature.setStyleSheet("QPushButton { border: none; }")
        self.pb_zoom_to_ref_feature.setIconSize(QtCore.QSize(16, 16))
        self.pb_zoom_to_ref_feature.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
        self.pb_zoom_to_ref_feature.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_zoom_to_ref_feature.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Zoom to feature"))
        sub_wdg.layout().addWidget(self.pb_zoom_to_ref_feature)

        sub_wdg.layout().addStretch()

        sub_wdg.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Offset:'), self))
        self.dspbx_offset = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_offset.setFont(spbx_font_m)
        self.dspbx_offset.setRange(-99999999, 99999999)
        self.dspbx_offset.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}{b1}Distance to reference-line{b2}{hr}{div_ml_1} {gt} 0 {arrow} left{br} {lt} 0 {arrow} right{br} = 0 {arrow} on line{br} click/ctrl-/shift-/ctrl+shift-click:{br} 1{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}/ 10{nbsp}{nbsp}/ 100{nbsp}{nbsp}/ 1000 m{div_ml_2}{div_pre_2}")))
        sub_wdg.layout().addWidget(self.dspbx_offset)
        self.measure_grb.layout().addWidget(sub_wdg, sub_row, 1, 1, 4)

        unit_widget_1 = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_1, sub_row, 5)
        self.layer_unit_widgets.append(unit_widget_1)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Cursor-Position x/y:'), self), sub_row, 0)
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
        from_lbl = QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','From:'), self)
        to_lbl = QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','To:'), self)
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
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Snapped Point x/y:'), self), sub_row, 0)
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
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Measure (abs/fract):'), self), sub_row, 0)

        self.dspbx_measure_from = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_measure_from.setFont(spbx_font_m)
        self.dspbx_measure_from.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog', "{div_pre_1}{b1}Measured From-Point{b2}{hr}{div_ml_1}- range 0...length_of_line{br}- click/ctrl-/shift-/ctrl+shift-click:{br}{nbsp}{nbsp}{nbsp}1{nbsp}{nbsp}{nbsp}{nbsp}/ 10{nbsp}{nbsp}/ 100{nbsp}{nbsp}/ 1000 m{div_ml_2}{div_pre_2}")))
        self.measure_grb.layout().addWidget(self.dspbx_measure_from, sub_row, 1)

        self.dspbx_measure_fract_from = tools.MyQtWidgets.QDoubleSpinBoxPercent(self)
        self.dspbx_measure_fract_from.setFont(spbx_font_m)
        self.dspbx_measure_fract_from.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}{b1}Measured From-Point as percentage{b2}{hr}{div_ml_1}- range 0...100{br}- click/ctrl-click:{br}{nbsp}{nbsp}{nbsp}1{nbsp}{nbsp}{nbsp}{nbsp}/ 10 %{div_ml_2}{div_pre_2}")))

        self.measure_grb.layout().addWidget(self.dspbx_measure_fract_from, sub_row, 2)

        self.dspbx_measure_to = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_measure_to.setFont(spbx_font_m)
        # valueChanged-Signal only with [Enter], not with every change
        self.dspbx_measure_to.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog', "{div_pre_1}{b1}Measured To-Point{b2}{hr}{div_ml_1}- range 0...length_of_line{br}- click/ctrl-/shift-/ctrl+shift-click:{nbsp}{nbsp}{nbsp}{br}1{nbsp}{nbsp}{nbsp}{nbsp}/ 10{nbsp}{nbsp}/ 100{nbsp}{nbsp}/ 1000 m{div_ml_2}{div_pre_2}")))
        self.measure_grb.layout().addWidget(self.dspbx_measure_to, sub_row, 3)

        self.dspbx_measure_fract_to = tools.MyQtWidgets.QDoubleSpinBoxPercent(self)
        self.dspbx_measure_fract_to.setFont(spbx_font_m)
        self.dspbx_measure_fract_to.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}{b1}Measured To-Point as percentage{b2}{hr}{div_ml_1}- range 0...100{br}- click/ctrl-click:{br}{nbsp}{nbsp}{nbsp}1{nbsp}{nbsp}{nbsp}{nbsp}/ 10 %{div_ml_2}{div_pre_2}")))
        self.measure_grb.layout().addWidget(self.dspbx_measure_fract_to, sub_row, 4)

        unit_widget_4_b = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_4_b, sub_row, 5)
        self.layer_unit_widgets.append(unit_widget_4_b)

        self.measure_grb.layout().addWidget(QtWidgets.QLabel('/ [%]', self), sub_row, 6)

        sub_row += 1
        self.measure_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Length:'), self), sub_row, 0)

        sub_wdg = QtWidgets.QWidget()
        sub_wdg.setLayout(QtWidgets.QHBoxLayout())

        self.tbtn_move_segment_start = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_start.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_start.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_start.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowLeft.svg'))
        self.tbtn_move_segment_start.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"move segment to reference-line-start-point"))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_start)
        
        self.tbtn_prepend_segment = QtWidgets.QToolButton(self)
        self.tbtn_prepend_segment.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_prepend_segment.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_prepend_segment.setIcon(QtGui.QIcon(':icons/mActionDoubleArrowLeft.svg'))
        self.tbtn_prepend_segment.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}prepend segment:{br}new to-measurement == old from-measurement{div_pre_2}")))
        sub_wdg.layout().addWidget(self.tbtn_prepend_segment)

        self.tbtn_move_segment_down = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_down.setAutoRepeat(True)
        self.tbtn_move_segment_down.setAutoRepeatDelay(500)
        self.tbtn_move_segment_down.setAutoRepeatInterval(100)
        self.tbtn_move_segment_down.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_down.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_down.setIcon(QtGui.QIcon(':icons/mActionArrowLeft.svg'))
        self.tbtn_move_segment_down.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}move segment towards reference-line-start-Point{div_ml_1}click/ctrl-/shift-/ctrl+shift-click{br} 1{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}/ 10{nbsp}{nbsp}/ 100{nbsp}{nbsp}/ 1000 m{div_ml_2}{div_pre_2}")))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_down)

        self.dspbx_distance = tools.MyQtWidgets.QDoubleSpinBoxDefault(self)
        self.dspbx_distance.setFont(spbx_font_m)
        self.dspbx_distance.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}enlarge/shrink segment{div_ml_1}{arrow} keeps From-, moves To-Point{br}{arrow} click/ctrl-/shift-/ctrl+shift-click{br}1{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}/ 10{nbsp}{nbsp}/ 100{nbsp}{nbsp}/ 1000 m{div_pre_2}")))
        sub_wdg.layout().addWidget(self.dspbx_distance)

        self.tbtn_move_segment_up = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_up.setAutoRepeat(True)
        self.tbtn_move_segment_up.setAutoRepeatDelay(500)
        self.tbtn_move_segment_up.setAutoRepeatInterval(100)
        self.tbtn_move_segment_up.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_up.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_up.setIcon(QtGui.QIcon(':icons/mActionArrowRight.svg'))
        self.tbtn_move_segment_up.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}move segment towards reference-line-end-point{br}click/ctrl-/shift-/ctrl+shift-click{br} 1{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}/ 10{nbsp}{nbsp}/ 100{nbsp}{nbsp}/ 1000 m{div_pre_2}")))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_up)

        self.tbtn_append_segment = QtWidgets.QToolButton(self)
        self.tbtn_append_segment.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_append_segment.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_append_segment.setIcon(QtGui.QIcon(':icons/mActionDoubleArrowRight.svg'))
        self.tbtn_append_segment.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}append segment{br}new from-measurement == old to-measurement{div_pre_2}")))
        sub_wdg.layout().addWidget(self.tbtn_append_segment)

        self.tbtn_move_segment_end = QtWidgets.QToolButton(self)
        self.tbtn_move_segment_end.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowRight.svg'))
        self.tbtn_move_segment_end.setStyleSheet("QToolButton { border: none; }")
        self.tbtn_move_segment_end.setIconSize(QtCore.QSize(16, 16))
        self.tbtn_move_segment_end.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"move segment to reference-line-end-point"))
        sub_wdg.layout().addWidget(self.tbtn_move_segment_end)

        self.pb_zoom_to_segment = QtWidgets.QPushButton(self)
        self.pb_zoom_to_segment.setFixedSize(20, 20)
        self.pb_zoom_to_segment.setStyleSheet("QPushButton { border: none; }")
        self.pb_zoom_to_segment.setIconSize(QtCore.QSize(16, 16))
        self.pb_zoom_to_segment.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
        self.pb_zoom_to_segment.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_zoom_to_segment.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"zoom to segment"))
        sub_wdg.layout().addWidget(self.pb_zoom_to_segment)

        self.measure_grb.layout().addWidget(sub_wdg, sub_row, 1, 1, 4)

        unit_widget_4_c = QtWidgets.QLabel('[]', self)
        self.measure_grb.layout().addWidget(unit_widget_4_c, sub_row, 5)
        self.layer_unit_widgets.append(unit_widget_4_c)

        sub_row += 1

        self.pbtn_move_from_point = QtWidgets.QPushButton(self)
        self.pbtn_move_from_point.setText(QtCore.QCoreApplication.translate('LolDialog',"move From-Point"))
        self.pbtn_move_from_point.setIcon(QtGui.QIcon(':icons/linear_referencing_point.svg'))
        self.pbtn_move_from_point.setCheckable(True)
        self.pbtn_move_from_point.setChecked(False)
        self.pbtn_move_from_point.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"drag and drop From-Point on selected reference-line"))
        self.measure_grb.layout().addWidget(self.pbtn_move_from_point, sub_row, 1, 1, 2)

        self.pbtn_move_to_point = QtWidgets.QPushButton(self)
        self.pbtn_move_to_point.setText(QtCore.QCoreApplication.translate('LolDialog',"move To-Point"))
        self.pbtn_move_to_point.setIcon(QtGui.QIcon(':icons/linear_referencing_to_point.svg'))
        self.pbtn_move_to_point.setCheckable(True)
        self.pbtn_move_to_point.setChecked(False)
        self.pbtn_move_to_point.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"drag and drop To-Point on selected reference-line"))
        self.measure_grb.layout().addWidget(self.pbtn_move_to_point, sub_row, 3, 1, 2)

        sub_row += 1

        # change offset of current segment interactive on canvas
        self.pb_move_segment = QtWidgets.QPushButton(self)
        self.pb_move_segment.setText(QtCore.QCoreApplication.translate('LolDialog',"Move Segment"))
        self.pb_move_segment.setIconSize(QtCore.QSize(25, 25))
        self.pb_move_segment.setIcon(QtGui.QIcon(':icons/mActionMoveFeatureCopyLine.svg'))
        self.pb_move_segment.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_move_segment.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Move segment interactive:{div_ml_1}[{nbsp}{nbsp}{nbsp}]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} measurement{br}[shift]{nbsp}{arrow} offset{br}[ctrl]{nbsp}{nbsp}{nbsp}{arrow} offset and measurement{div_ml_2}{div_pre_2}")))
        self.pb_move_segment.setCheckable(True)
        self.measure_grb.layout().addWidget(self.pb_move_segment, sub_row, 1, 1, 4)

        sub_row += 1

        self.pbtn_resume_measure = QtWidgets.QPushButton(self)
        self.pbtn_resume_measure.setText(QtCore.QCoreApplication.translate('LolDialog',"Resume measurement"))
        self.pbtn_resume_measure.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_resume_measure.setIcon(QtGui.QIcon(':icons/mActionMeasure.svg'))
        self.pbtn_resume_measure.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Reset results and start new measurement"))
        self.measure_grb.layout().addWidget(self.pbtn_resume_measure, sub_row, 1, 1, 4)

        sub_row += 1

        row += 1

        # area with edit-widgets:
        self.edit_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('LolDialog','Storage:'), self)
        self.edit_grb.setCheckable(True)
        self.edit_grb.setChecked(False)
        self.edit_grb.setMaximumHeight(20)
        self.edit_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.edit_grb.setLayout(QtWidgets.QHBoxLayout())
        self.measure_container_wdg.layout().addWidget(self.edit_grb)

        self.edit_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Selected PK:"), self))

        # pk of the current edit feature
        self.le_edit_data_pk = QtWidgets.QLineEdit(self)
        # always disabled
        self.le_edit_data_pk.setEnabled(False)
        self.edit_grb.layout().addWidget(self.le_edit_data_pk)

        # add this Segment to data-layer
        self.pbtn_update_feature = QtWidgets.QPushButton(self)
        self.pbtn_update_feature.setText(QtCore.QCoreApplication.translate('LolDialog',"Update"))
        self.pbtn_update_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_update_feature.setIcon(QtGui.QIcon(':icons/mActionFileSave.svg'))
        self.pbtn_update_feature.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Update selected feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_update_feature)

        # add this Segment to data-layer
        self.pbtn_insert_feature = QtWidgets.QPushButton(self)
        self.pbtn_insert_feature.setText(QtCore.QCoreApplication.translate('LolDialog',"Insert"))
        self.pbtn_insert_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_insert_feature.setIcon(QtGui.QIcon(':icons/mActionAddManualTable.svg'))
        self.pbtn_insert_feature.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Insert feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_insert_feature)

        # delete this Segment
        self.pbtn_delete_feature = QtWidgets.QPushButton(self)
        self.pbtn_delete_feature.setText(QtCore.QCoreApplication.translate('LolDialog',"Delete"))
        self.pbtn_delete_feature.setIconSize(QtCore.QSize(25, 25))
        self.pbtn_delete_feature.setIcon(QtGui.QIcon(':icons/mActionDeleteSelectedFeatures.svg'))
        self.pbtn_delete_feature.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Delete selected feature..."))
        self.edit_grb.layout().addWidget(self.pbtn_delete_feature)

        self.measure_container_wdg.layout().addWidget(self.edit_grb)

        row += 1

        self.selection_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('LolDialog','Feature-Selection:'), self)
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
        self.pbtn_select_features.setText(QtCore.QCoreApplication.translate('LolDialog',"Select feature(s)"))
        self.pbtn_select_features.setMinimumWidth(25)
        self.pbtn_select_features.setIcon(QtGui.QIcon(':icons/select_point_features.svg'))
        self.pbtn_select_features.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Select features from Show-Layer:{br}click point or drag rectangle{br}{nbsp}{nbsp}{nbsp}[Shift]{nbsp}{arrow} append{br}{nbsp}{nbsp}{nbsp}[Ctrl]{nbsp}{nbsp}{arrow} remove{div_pre_2}")))
        self.pbtn_select_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_select_features)

        self.pbtn_insert_all_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_all_features.setText(QtCore.QCoreApplication.translate('LolDialog',"Insert all Features"))
        self.pbtn_insert_all_features.setMinimumWidth(25)
        self.pbtn_insert_all_features.setIcon(QtGui.QIcon(':icons/mActionSelectAll.svg'))
        self.pbtn_insert_all_features.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Insert all features from Data-Layer"))
        self.pbtn_insert_all_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_all_features)

        self.pbtn_insert_selected_data_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_selected_data_features.setText(QtCore.QCoreApplication.translate('LolDialog',"Insert selected Data-Layer-features"))
        self.pbtn_insert_selected_data_features.setMinimumWidth(25)
        self.pbtn_insert_selected_data_features.setIcon(QtGui.QIcon(':icons/mActionSelectPartial.svg'))
        self.pbtn_insert_selected_data_features.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Insert selected features from Data-Layer:{div_ml_1}[{nbsp}{nbsp}{nbsp}]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} replace{br}[Shift]{nbsp}{arrow} append{div_ml_2}{div_pre_2}")))
        self.pbtn_insert_selected_data_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_selected_data_features)

        self.pbtn_insert_selected_show_features = QtWidgets.QToolButton(self)
        self.pbtn_insert_selected_show_features.setText(QtCore.QCoreApplication.translate('LolDialog',"Insert selected Show-Layer-Features"))
        self.pbtn_insert_selected_show_features.setMinimumWidth(25)
        self.pbtn_insert_selected_show_features.setIcon(QtGui.QIcon(':icons/mActionSelectPartial.svg'))
        self.pbtn_insert_selected_show_features.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Insert selected features from Show-Layer:{div_ml_1}[{nbsp}{nbsp}{nbsp}]{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{nbsp}{arrow} replace{br}[Shift]{nbsp}{arrow} append{div_ml_2}{div_pre_2}")))
        self.pbtn_insert_selected_show_features.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        sub_sub_wdg.layout().addWidget(self.pbtn_insert_selected_show_features)

        self.selection_grb.layout().addWidget(sub_sub_wdg)

        # table to show the selected edit-features
        self.qtw_selected_pks = QtWidgets.QTableWidget()
        self.qtw_selected_pks.setFont(default_font_m)
        self.qtw_selected_pks.setIconSize(QtCore.QSize(20, 20))
        # minimum row height
        self.qtw_selected_pks.verticalHeader().setMinimumSectionSize(40)
        # minimum column width
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
        self.pbtn_zoom_to_feature_selection.setText(QtCore.QCoreApplication.translate('LolDialog',"Zoom to Feature-Selection"))
        self.pbtn_zoom_to_feature_selection.setMinimumWidth(25)
        self.pbtn_zoom_to_feature_selection.setIcon(QtGui.QIcon(':icons/mActionPanToSelected.svg'))
        self.pbtn_zoom_to_feature_selection.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Zoom to selected features"))
        sub_sub_wdg.layout().addWidget(self.pbtn_zoom_to_feature_selection)

        self.pbtn_clear_features = QtWidgets.QPushButton(self)
        self.pbtn_clear_features.setText(QtCore.QCoreApplication.translate('LolDialog',"Clear Feature-Selection"))
        self.pbtn_clear_features.setMinimumWidth(25)
        self.pbtn_clear_features.setIcon(QtGui.QIcon(':icons/mActionDeselectActiveLayer.svg'))
        sub_sub_wdg.layout().addWidget(self.pbtn_clear_features)

        self.selection_grb.layout().addWidget(sub_sub_wdg)

        self.measure_container_wdg.layout().addWidget(self.selection_grb, 1)

        # spacer between self.selection_grb and Status-Bar
        self.measure_container_wdg.layout().addStretch(0)

        ## second tab: settings...
        row = 0

        self.layers_and_fields_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('LolDialog','Layers and Fields:'), self)
        self.layers_and_fields_grb.setCheckable(True)
        self.layers_and_fields_grb.setChecked(True)
        self.layers_and_fields_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.layers_and_fields_grb.setLayout(QtWidgets.QGridLayout())

        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Reference-Layer...'), self), row, 0)
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
        self.qcbn_reference_layer.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Reference-Layer{div_ml_1}- linestring/m/z{br}- multi-linestring/m/z{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_reference_layer, row, 1)

        self.pb_open_ref_tbl = QtWidgets.QPushButton(self)
        self.pb_open_ref_tbl.setFixedSize(20, 20)
        self.pb_open_ref_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_ref_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_ref_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_ref_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_ref_tbl.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Open attribute-table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_ref_tbl, row, 2)

        self.pb_call_ref_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_ref_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_ref_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_ref_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_ref_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_ref_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_ref_disp_exp_dlg.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Edit Display-Expression for this layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_ref_disp_exp_dlg, row, 3)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','      ... ID-Field:'), self), row, 0)
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
        self.qcbn_reference_layer_id_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}ID-Field, assignment to Data-Layer{div_ml_1}- type integer or string{br}- unique, not null{br}- typically the PK-field{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_reference_layer_id_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Data-Layer...'), self), row, 0)
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
        self.qcbn_data_layer.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Store measured LoL-features{div_ml_1}- geometry-less{br}- insert/update/delete-privileges{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer, row, 1)

        self.pb_open_data_tbl = QtWidgets.QPushButton(self)
        self.pb_open_data_tbl.setFixedSize(20, 20)
        self.pb_open_data_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_data_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_data_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_data_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_data_tbl.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Open attribute-table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_data_tbl, row, 2)

        self.pb_call_data_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_data_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_data_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_data_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_data_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_data_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_data_disp_exp_dlg.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Edit Display-Expression for this layer"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_data_disp_exp_dlg, row, 3)

        self.pbtn_create_data_layer = QtWidgets.QPushButton(self)
        self.pbtn_create_data_layer.setText(QtCore.QCoreApplication.translate('LolDialog',"...or create"))
        self.pbtn_create_data_layer.setMaximumWidth(100)
        self.pbtn_create_data_layer.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Create GPKG-Layer for storing measurement-data"))
        self.layers_and_fields_grb.layout().addWidget(self.pbtn_create_data_layer, row, 4)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','      ... ID-Field:'), self), row, 0)
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
        self.qcbn_data_layer_id_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Field with unique key{div_ml_1}- type integer or string{br}- typically the PK-field{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_id_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','      ... Reference-Field:'), self), row, 0)
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
        self.qcbn_data_layer_reference_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Assignment to Reference-Layer{div_ml_1}- type matching to Reference-Layer-ID-field{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_reference_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','      ... Measure-From-Field:'), self), row, 0)
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
        self.qcbn_data_layer_measure_from_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Field for storing measurement-from{div_ml_1}- distance of segment-start to startpoint of assigned line{br}- numeric type{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_measure_from_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','      ... Measure-To-Field:'), self), row, 0)
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
        self.qcbn_data_layer_measure_to_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Field for storing measurement-to{div_ml_1}- distance of segment-end to startpoint of assigned line{br}- numeric type{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_measure_to_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','      ... Offset-Field:'), self), row, 0)
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
        self.qcbn_data_layer_offset_field.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Field for offset{div_ml_1}- distance to assigned reference-Line{br}- numeric type{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_offset_field, row, 1)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog','Show-Layer...'), self), row, 0)
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
        self.qcbn_show_layer.setToolTip(qt_format(QtCore.QCoreApplication.translate('LolDialog',"{div_pre_1}Layer for Line-on-Line-features{div_ml_1}- geometry-type Linestring{br}- source-type virtual or ogr{br}(f.e. imported PostGIS or GPKG-view){div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer, row, 1)

        self.pb_open_show_tbl = QtWidgets.QPushButton(self)
        self.pb_open_show_tbl.setFixedSize(20, 20)
        self.pb_open_show_tbl.setStyleSheet("QPushButton { border: none; }")
        self.pb_open_show_tbl.setIconSize(QtCore.QSize(16, 16))
        self.pb_open_show_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
        self.pb_open_show_tbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_open_show_tbl.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Open attribute-table"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_open_show_tbl, row, 2)

        self.pb_call_show_disp_exp_dlg = QtWidgets.QPushButton(self)
        self.pb_call_show_disp_exp_dlg.setFixedSize(20, 20)
        self.pb_call_show_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
        self.pb_call_show_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
        self.pb_call_show_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
        self.pb_call_show_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
        self.pb_call_show_disp_exp_dlg.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Edit Display-Expression"))
        self.layers_and_fields_grb.layout().addWidget(self.pb_call_show_disp_exp_dlg, row, 3)

        self.pbtn_create_show_layer = QtWidgets.QPushButton(self)
        self.pbtn_create_show_layer.setText(QtCore.QCoreApplication.translate('LolDialog',"...or create"))
        self.pbtn_create_show_layer.setMaximumWidth(100)
        self.pbtn_create_show_layer.setToolTip(QtCore.QCoreApplication.translate('LolDialog',"Create virtual Layer for LoL-features"))
        self.layers_and_fields_grb.layout().addWidget(self.pbtn_create_show_layer, row, 4)

        row += 1
        self.layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"      ... Back-Reference-Field:")), row, 0)
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
        self.qcbn_show_layer_back_reference_field.setToolTip(QtCore.QCoreApplication.translate('LolDialog',qt_format("{div_pre_1}Reference to Data-Layer{div_ml_1}- type matching Data-Layer-ID-field{br}- typically the PK-field{div_ml_2}{div_pre_2}")))
        self.layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer_back_reference_field, row, 1)

        self.settings_container_wdg = QtWidgets.QWidget(self)
        self.settings_container_wdg.setLayout(QtWidgets.QVBoxLayout())
        self.settings_container_wdg.layout().addWidget(self.layers_and_fields_grb)

        self.style_grb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('LolDialog','Styles:'), self)
        self.style_grb.setCheckable(True)
        self.style_grb.setChecked(False)
        self.style_grb.setMaximumHeight(20)
        self.style_grb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.style_grb.setLayout(QtWidgets.QGridLayout())

        # see https://qgis.org/pyqgis/master/gui/QgsVertexMarker.html
        point_symbol_items = {0: "None", 1: "Cross", 2: "X", 3: "Box", 4: "Circle", 5: "Double-Triangle", 6: "Triangle", 7: "Rhombus", 8: "Inverted Triangle"}

        # see https://doc.qt.io/qt-6/qt.html#PenStyle-enum
        # 6 Qt.CustomDashLine not implemented here...
        line_symbol_items = {0: "None", 1: "Solid", 2: "Dash", 3: "Dot", 4: "DashDot", 5: "DashDotDot"}

        row = 0
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Symbol")), row, 1)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Size")), row, 2)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Width")), row, 3)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Color")), row, 4)
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Fill-Color")), row, 5)

        row += 1
        # From-Point
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"From-Point:")), row, 0)
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
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"To-Point:")), row, 0)
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
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Segment-Line:")), row, 0)
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
        self.style_grb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Reference-Line:")), row, 0)
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

        self.store_configurations_gb = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate('LolDialog','Store/Restore configurations:'), self)
        self.store_configurations_gb.setCheckable(True)
        self.store_configurations_gb.setChecked(False)
        self.store_configurations_gb.setMaximumHeight(20)
        self.store_configurations_gb.setStyle(tools.MyQtWidgets.GroupBoxProxyStyle())
        self.store_configurations_gb.setLayout(QtWidgets.QVBoxLayout())

        self.store_configurations_gb.layout().addWidget(QtWidgets.QLabel(QtCore.QCoreApplication.translate('LolDialog',"Stored configurations:")))

        self.lw_stored_settings = QtWidgets.QListWidget()
        self.lw_stored_settings.setFont(default_font_m)
        self.lw_stored_settings.setFixedHeight(100)
        self.lw_stored_settings.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.store_configurations_gb.layout().addWidget(self.lw_stored_settings)

        self.pb_store_configuration = QtWidgets.QPushButton(QtCore.QCoreApplication.translate('LolDialog',"Store current configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_store_configuration)

        self.pb_restore_configuration = QtWidgets.QPushButton(QtCore.QCoreApplication.translate('LolDialog',"Restore selected configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_restore_configuration)

        self.pb_delete_configuration = QtWidgets.QPushButton(QtCore.QCoreApplication.translate('LolDialog',"Delete selected Configuration..."))
        self.store_configurations_gb.layout().addWidget(self.pb_delete_configuration)

        self.settings_container_wdg.layout().addWidget(self.store_configurations_gb)

        self.settings_container_wdg.layout().addStretch(1)

        self.tbw_central = QtWidgets.QTabWidget(self)

        self.tbw_central.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        self.tbw_central.addTab(self.measure_container_wdg, QtCore.QCoreApplication.translate('LolDialog','Measurement'))

        self.tbw_central.addTab(self.settings_container_wdg, QtCore.QCoreApplication.translate('LolDialog','Settings'))

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


