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

import qgis, sys
from PyQt5 import QtCore, QtGui, QtWidgets

from LinearReferencing.qt import MyQtWidgets, MyDelegates
from LinearReferencing import tools

# pyrcc5-compiled icons,
# path-like-addressable in all PyQt-scripts of this plugin
# f.e. the toolbar-icons below ':icons/....svg'
from LinearReferencing.icons import resources

from LinearReferencing.i18n.SQLiteDict import SQLiteDict
# global variable, translations de_DE and en_US
MY_DICT = SQLiteDict()


class LolDialog(QtWidgets.QDockWidget):
    """Dialogue for QGis-Plugin LinearReferencing, Line-on-line-Features
    note:
        QtWidgets.QDockWidget -> dockable Window
        requires self.iface.addDockWidget(...) to be dockable within the MainWindow
    """

    # own signal, emitted by reimplemented eventFilter on dialog Close
    dialog_close = QtCore.pyqtSignal(bool)

    # own signal, emitted by reimplemented eventFilter if the dialog gets focus
    dialog_activated = QtCore.pyqtSignal(bool)

    def __init__(self, iface: qgis.gui.QgisInterface, parent=None):
        """Constructor
        :param iface:
        :param parent: optional Qt-Parent-Element for Hierarchy
        """

        QtWidgets.QDockWidget.__init__(self, parent)


        self.iface = iface

        self.setWindowTitle(MY_DICT.tr('LoL_dialog_title'))

        # needed for the reimplemented eventFilter which monitors the Close/WindowActivate/WindowDeActivate of this dialog
        self.installEventFilter(self)

        # to avoid ShutDown-Warning
        # Warning: QMainWindow::saveState(): 'objectName' not set for QDockWidget 0x55bc0824c790 'LinearReferencing: Point-on-Line;
        self.setObjectName("LoL-Dialog")

        # problem on linux-mint: dependend on the system-color-scheme some (not all) tooltips appeare with white text on yellow background
        # Qt-Tooltip-CSS-Bug: for working background-color additional border-style needed (e.g. border-style: none)
        self.setStyleSheet("QToolTip {background-color: #FBF8CA; color: black; padding: 2px; border: 1px solid black}")

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
        # 1. scrollable main content with QtWidgets.QTabWidget Stationing/Edit/Settings
        # 2. status-bar
        main_wdg.layout().setContentsMargins(10, 10, 10, 0)

        # central widget with mutiple tabs
        self.tbw_central = QtWidgets.QTabWidget(self)
        self.tbw_central.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)


        # Begin stationing_container_wdg ######################################################################################
        if True:
            stationing_container_wdg = QtWidgets.QWidget(self)
            stationing_container_wdg.setLayout(QtWidgets.QVBoxLayout())
            stationing_container_wdg.setStyleSheet("QWidget {background-color: #FFFFFFFF;}")

            self.stationing_grb = QtWidgets.QGroupBox(self)
            self.stationing_grb.setLayout(QtWidgets.QGridLayout())
            row = 0

            self.stationing_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('ref_layer_lbl'), self), row, 0)

            # shows the currentl selected reference-layer and type
            self.qlbl_selected_reference_layer = QtWidgets.QLabel()
            self.stationing_grb.layout().addWidget(self.qlbl_selected_reference_layer, row, 1,1,5)



            row += 1

            self.stationing_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('ref_line_lbl'), self), row, 0)

            self.qcbn_reference_feature = MyQtWidgets.QComboBoxN(
                self,
                # note: numerical columns with DoubleSelectBorderDelegate
                # col_names dynamically altered dependend on layer-type
                col_names=['FID', 'Display-Name', 'Length','first-M','last-M'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignRight,QtCore.Qt.AlignRight,QtCore.Qt.AlignRight],
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                show_clear_button=False,
                # no float-contents in the QLineEdit because of delegates with rounded values
                show_template="# {0} {1}",
                tool_tips_by_col_idx=None
            )
            self.qcbn_reference_feature.setFont(cbx_font_m)
            self.qcbn_reference_feature.setToolTip(MY_DICT.tr('ref_line_ttp'))

            self.ref_length_delegate = MyDelegates.DoubleSelectBorderDelegate()
            self.qcbn_reference_feature.view().setItemDelegateForColumn(2, self.ref_length_delegate)

            self.first_m_delegate = MyDelegates.DoubleSelectBorderDelegate()
            self.qcbn_reference_feature.view().setItemDelegateForColumn(3, self.first_m_delegate)

            self.last_m_delegate = MyDelegates.DoubleSelectBorderDelegate()
            self.qcbn_reference_feature.view().setItemDelegateForColumn(4, self.last_m_delegate)


            self.stationing_grb.layout().addWidget(self.qcbn_reference_feature, row, 1, 1, 4)

            self.pb_open_ref_form = QtWidgets.QPushButton(self)
            self.pb_open_ref_form.setFixedSize(20, 20)
            self.pb_open_ref_form.setStyleSheet("QPushButton { border: none; }")
            self.pb_open_ref_form.setIconSize(QtCore.QSize(16, 16))
            self.pb_open_ref_form.setIcon(QtGui.QIcon(':icons/mActionIdentify.svg'))
            self.pb_open_ref_form.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_open_ref_form.setToolTip(MY_DICT.tr('open_form_ttp'))
            self.stationing_grb.layout().addWidget(self.pb_open_ref_form, row, 5)

            self.pb_zoom_to_ref_feature = QtWidgets.QPushButton(self)
            self.pb_zoom_to_ref_feature.setFixedSize(20, 20)
            self.pb_zoom_to_ref_feature.setStyleSheet("QPushButton { border: none; }")
            self.pb_zoom_to_ref_feature.setIconSize(QtCore.QSize(16, 16))
            self.pb_zoom_to_ref_feature.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
            self.pb_zoom_to_ref_feature.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_zoom_to_ref_feature.setToolTip(MY_DICT.tr('zoom_feature_ttp'))

            self.stationing_grb.layout().addWidget(self.pb_zoom_to_ref_feature, row, 6)

            row += 1

            row += 1
            self.stationing_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('canvas_x_y_lbl'), self), row, 0)

            self.dnspbx_canvas_x = MyQtWidgets.QDoubleNoSpinBox(self)
            self.dnspbx_canvas_x.setFont(le_font_m)
            self.stationing_grb.layout().addWidget(self.dnspbx_canvas_x, row, 1)

            self.dnspbx_canvas_y = MyQtWidgets.QDoubleNoSpinBox(self)
            self.dnspbx_canvas_y.setFont(le_font_m)
            self.stationing_grb.layout().addWidget(self.dnspbx_canvas_y, row, 2)

            sub_wdg = QtWidgets.QWidget()
            sub_wdg.setLayout(QtWidgets.QHBoxLayout())

            unit_widget = QtWidgets.QLabel('[]', self)
            sub_wdg.layout().addWidget(unit_widget)
            self.canvas_unit_widgets.append(unit_widget)
            #sub_wdg.layout().addStretch(1)
            offset_lbl = QtWidgets.QLabel(MY_DICT.tr('offset_lbl'), self)
            sub_wdg.layout().addWidget(offset_lbl)

            self.stationing_grb.layout().addWidget(sub_wdg, row, 3)

            self.dspbx_offset = MyQtWidgets.QDoubleSpinBoxDefault(self)
            self.dspbx_offset.setFont(spbx_font_m)
            self.dspbx_offset.setToolTip(MY_DICT.tr('offset_ttp'))
            self.stationing_grb.layout().addWidget(self.dspbx_offset, row, 4)

            unit_widget = QtWidgets.QLabel('[]', self)
            self.layer_unit_widgets.append(unit_widget)
            self.stationing_grb.layout().addWidget(unit_widget, row, 5)

            row += 1
            from_wdg = QtWidgets.QWidget()

            from_wdg.setLayout(QtWidgets.QHBoxLayout())
            from_wdg.layout().setContentsMargins(0, 0, 0, 0)
            from_lbl = QtWidgets.QLabel(MY_DICT.tr('from_lbl'), self)
            #from_lbl.setStyleSheet("color:green;")
            palette = from_lbl.palette()
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 255, 0))
            from_lbl.setPalette(palette)
            from_wdg.layout().addWidget(from_lbl)
            self.pb_set_from_point = QtWidgets.QPushButton(self)
            self.pb_set_from_point.setFixedSize(20, 20)
            self.pb_set_from_point.setCheckable(True)
            #self.pb_set_from_point.setStyleSheet("QPushButton { border: none; }")
            self.pb_set_from_point.setIconSize(QtCore.QSize(18, 18))
            self.pb_set_from_point.setIcon(QtGui.QIcon(':icons/linear_referencing_point.svg'))
            self.pb_set_from_point.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_set_from_point.setToolTip(MY_DICT.tr('set_from_point_ttp'))
            from_wdg.layout().addWidget(self.pb_set_from_point)
            self.stationing_grb.layout().addWidget(from_wdg, row, 1, 1, 2, QtCore.Qt.AlignCenter)

            to_wdg = QtWidgets.QWidget()
            to_wdg.setLayout(QtWidgets.QHBoxLayout())
            to_wdg.layout().setContentsMargins(0, 0, 0, 0)
            to_lbl = QtWidgets.QLabel(MY_DICT.tr('to_lbl'), self)
            palette = to_lbl.palette()
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 0, 0))
            to_lbl.setPalette(palette)
            to_wdg.layout().addWidget(to_lbl)
            self.pb_set_to_point = QtWidgets.QPushButton(self)
            self.pb_set_to_point.setFixedSize(20, 20)
            self.pb_set_to_point.setCheckable(True)
            #self.pb_set_to_point.setStyleSheet("QPushButton { border: none; }")
            self.pb_set_to_point.setIconSize(QtCore.QSize(18, 18))
            self.pb_set_to_point.setIcon(QtGui.QIcon(':icons/linear_referencing_to_point.svg'))
            self.pb_set_to_point.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_set_to_point.setToolTip(MY_DICT.tr('set_to_point_ttp'))
            to_wdg.layout().addWidget(self.pb_set_to_point)

            self.stationing_grb.layout().addWidget(to_wdg, row, 3, 1, 2, QtCore.Qt.AlignCenter)



            row += 1
            self.stationing_grb.layout().addWidget(MyQtWidgets.HLine(self,2, '#00FF00'), row, 1, 1, 2)

            self.stationing_grb.layout().addWidget(MyQtWidgets.HLine(self,2, '#FF0000'), row, 3, 1, 2)




            
            row += 1
            self.stationing_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('snap_x_y_lbl'), self), row, 0)

            self.dnspbx_snap_x_from = MyQtWidgets.QDoubleNoSpinBox(self)
            self.dnspbx_snap_x_from.setFont(le_font_m)
            self.stationing_grb.layout().addWidget(self.dnspbx_snap_x_from, row, 1)

            self.dnspbx_snap_y_from = MyQtWidgets.QDoubleNoSpinBox(self)
            self.dnspbx_snap_y_from.setFont(le_font_m)
            self.stationing_grb.layout().addWidget(self.dnspbx_snap_y_from, row, 2)

            self.dnspbx_snap_x_to = MyQtWidgets.QDoubleNoSpinBox(self)
            self.dnspbx_snap_x_to.setFont(le_font_m)
            self.stationing_grb.layout().addWidget(self.dnspbx_snap_x_to, row, 3)

            self.dnspbx_snap_y_to = MyQtWidgets.QDoubleNoSpinBox(self)
            self.dnspbx_snap_y_to.setFont(le_font_m)
            self.stationing_grb.layout().addWidget(self.dnspbx_snap_y_to, row, 4)


            unit_widget = QtWidgets.QLabel('[]', self)
            self.stationing_grb.layout().addWidget(unit_widget, row, 5)
            self.layer_unit_widgets.append(unit_widget)

            if True:
                # N-absolute-stationings
                row += 1
                self.stationing_grb.layout().addWidget(MyQtWidgets.HLine(self,1, '#B7B7B7'), row, 0, 1, 7)
                row += 1

                # N-abs-area with toggle-function, initially visible
                n_abs_wdg = QtWidgets.QWidget()
                n_abs_wdg.setLayout(QtWidgets.QHBoxLayout())
                n_abs_wdg.layout().setContentsMargins(0, 0, 0, 0)
                n_abs_wdg.setToolTip(MY_DICT.tr('n_abs_grp_ttp'))


                self.pb_toggle_n_abs_grp = QtWidgets.QPushButton(self)
                self.pb_toggle_n_abs_grp.setFixedSize(14, 14)
                self.pb_toggle_n_abs_grp.setIconSize(QtCore.QSize(14, 14))
                self.pb_toggle_n_abs_grp.setIcon(QtGui.QIcon(':icons/minus-box-outline.svg'))
                self.pb_toggle_n_abs_grp.setStyleSheet("QPushButton { border: none; }")
                self.pb_toggle_n_abs_grp.setCursor(QtCore.Qt.PointingHandCursor)
                n_abs_wdg.layout().addWidget(self.pb_toggle_n_abs_grp)
                qlbl_n_abs_group = QtWidgets.QLabel(MY_DICT.tr('n_abs_grp_lbl'), self)
                n_abs_wdg.layout().addWidget(qlbl_n_abs_group)
                self.stationing_grb.layout().addWidget(n_abs_wdg, row, 0, 1, 7, QtCore.Qt.AlignLeft)


                row += 1
                self.qlbl_n_abs = QtWidgets.QLabel(MY_DICT.tr('n_abs_lbl'), self)
                self.stationing_grb.layout().addWidget(self.qlbl_n_abs, row, 0)
                self.dspbx_n_abs_from = MyQtWidgets.QDoubleSpinBoxDefault(self,0, sys.float_info.max)
                self.dspbx_n_abs_from.setFont(spbx_font_m)
                self.stationing_grb.layout().addWidget(self.dspbx_n_abs_from, row, 1,1,2)

                self.dspbx_n_abs_to = MyQtWidgets.QDoubleSpinBoxDefault(self,0, sys.float_info.max)
                self.dspbx_n_abs_to.setFont(spbx_font_m)
                self.stationing_grb.layout().addWidget(self.dspbx_n_abs_to, row, 3,1,2)

                self.qlbl_unit_n_abs = QtWidgets.QLabel('[]', self)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_n_abs, row, 5)
                self.layer_unit_widgets.append(self.qlbl_unit_n_abs)


                row += 1

                self.qlbl_delta_n_abs = QtWidgets.QLabel(MY_DICT.tr('delta_n_lbl'), self)
                self.stationing_grb.layout().addWidget(self.qlbl_delta_n_abs, row, 0)
                self.dspbx_delta_n_abs = MyQtWidgets.QDoubleSpinBoxDefault(self)
                self.dspbx_delta_n_abs.setFont(spbx_font_m)
                self.stationing_grb.layout().addWidget(self.dspbx_delta_n_abs, row, 2,1,2)
                self.qlbl_unit_delta_n_abs = QtWidgets.QLabel('[]', self)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_delta_n_abs, row, 5)
                self.layer_unit_widgets.append(self.qlbl_unit_delta_n_abs)


            if True:
                # N-fract-stationings
                row += 1
                self.stationing_grb.layout().addWidget(MyQtWidgets.HLine(self,1, '#B7B7B7'), row, 0, 1, 7)
                row += 1

                # N-fract-area with toggle-function, initially hidden
                n_fract_wdg = QtWidgets.QWidget()
                n_fract_wdg.setLayout(QtWidgets.QHBoxLayout())
                n_fract_wdg.layout().setContentsMargins(0, 0, 0, 0)
                n_fract_wdg.setToolTip(MY_DICT.tr('n_fract_grp_ttp'))

                self.pb_toggle_n_fract_grp = QtWidgets.QPushButton(self)
                self.pb_toggle_n_fract_grp.setFixedSize(14, 14)
                self.pb_toggle_n_fract_grp.setIconSize(QtCore.QSize(14, 14))
                self.pb_toggle_n_fract_grp.setIcon(QtGui.QIcon(':icons/plus-box-outline.svg'))
                self.pb_toggle_n_fract_grp.setStyleSheet("QPushButton { border: none; }")
                self.pb_toggle_n_fract_grp.setCursor(QtCore.Qt.PointingHandCursor)
                n_fract_wdg.layout().addWidget(self.pb_toggle_n_fract_grp)
                qlbl_n_fract_group = QtWidgets.QLabel(MY_DICT.tr('n_fract_grp_lbl'), self)
                n_fract_wdg.layout().addWidget(qlbl_n_fract_group)
                self.stationing_grb.layout().addWidget(n_fract_wdg, row, 0, 1, 1, QtCore.Qt.AlignLeft)

                row += 1

                self.qlbl_n_fract = QtWidgets.QLabel(MY_DICT.tr('n_fract_lbl'), self)
                self.qlbl_n_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_n_fract, row, 0)
                self.dspbx_n_fract_from = MyQtWidgets.QDoubleSpinBoxDefault(self,0,100)
                self.dspbx_n_fract_from.setFont(spbx_font_m)
                self.dspbx_n_fract_from.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_n_fract_from, row, 1,1,2)

                self.dspbx_n_fract_to = MyQtWidgets.QDoubleSpinBoxDefault(self,0,100)
                self.dspbx_n_fract_to.setFont(spbx_font_m)
                self.dspbx_n_fract_to.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_n_fract_to, row, 3,1,2)
                self.qlbl_unit_n_fract = QtWidgets.QLabel('[%]', self)
                self.qlbl_unit_n_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_n_fract, row, 5)

                row += 1
                self.qlbl_delta_n_fract = QtWidgets.QLabel(MY_DICT.tr('delta_n_fract_lbl'), self)
                self.qlbl_delta_n_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_delta_n_fract, row, 0)
                # negativ if against digitize-direction
                self.dspbx_delta_n_fract = MyQtWidgets.QDoubleSpinBoxDefault(self,-100,100)
                self.dspbx_delta_n_fract.setFont(spbx_font_m)
                self.dspbx_delta_n_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_delta_n_fract, row, 2,1,2)
                self.qlbl_unit_delta_n_fract = QtWidgets.QLabel('[%]', self)
                self.qlbl_unit_delta_n_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_delta_n_fract, row, 5)

            if True:
                # M-abs-stationings
                # m-widgets, will be set visible dynamically if reference-layer is m-enabled
                row += 1
                self.m_abs_grp_hline = MyQtWidgets.HLine(self,1, '#B7B7B7')
                self.stationing_grb.layout().addWidget(self.m_abs_grp_hline, row, 0, 1, 7)
                row += 1

                # M-abs-area with toggle-function, initially hidden
                self.m_abs_grp_wdg = QtWidgets.QWidget()
                self.m_abs_grp_wdg.setLayout(QtWidgets.QHBoxLayout())
                self.m_abs_grp_wdg.layout().setContentsMargins(0, 0, 0, 0)
                self.m_abs_grp_wdg.setToolTip(MY_DICT.tr('m_abs_grp_ttp'))

                self.pb_toggle_m_abs_grp = QtWidgets.QPushButton(self)
                self.pb_toggle_m_abs_grp.setFixedSize(14, 14)
                self.pb_toggle_m_abs_grp.setIconSize(QtCore.QSize(14, 14))
                self.pb_toggle_m_abs_grp.setIcon(QtGui.QIcon(':icons/plus-box-outline.svg'))
                self.pb_toggle_m_abs_grp.setStyleSheet("QPushButton { border: none; }")
                self.pb_toggle_m_abs_grp.setCursor(QtCore.Qt.PointingHandCursor)
                self.m_abs_grp_wdg.layout().addWidget(self.pb_toggle_m_abs_grp)
                qlbl_m_abs_group = QtWidgets.QLabel(MY_DICT.tr('m_abs_grp_lbl'), self)
                self.m_abs_grp_wdg.layout().addWidget(qlbl_m_abs_group)

                self.stationing_grb.layout().addWidget(self.m_abs_grp_wdg, row, 0, 1, 1, QtCore.Qt.AlignLeft)


                row += 1

                self.qlbl_m_abs = QtWidgets.QLabel(MY_DICT.tr('m_abs_lbl'), self)
                self.qlbl_m_abs.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_m_abs, row, 0)
                # m-value-range defined by geometry-vertex-m-values
                self.dspbx_m_abs_from = MyQtWidgets.QDoubleSpinBoxDefault(self)
                self.dspbx_m_abs_from.setFont(spbx_font_m)
                self.dspbx_m_abs_from.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_m_abs_from, row, 1,1,2)

                # m-value-range defined by geometry-vertex-m-values
                self.dspbx_m_abs_to = MyQtWidgets.QDoubleSpinBoxDefault(self)
                self.dspbx_m_abs_to.setFont(spbx_font_m)
                self.dspbx_m_abs_to.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_m_abs_to, row, 3,1,2)
                self.qlbl_unit_m_abs = QtWidgets.QLabel('[...]', self)
                self.qlbl_unit_m_abs.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_m_abs, row, 5)

                row += 1
                self.qlbl_delta_m_abs = QtWidgets.QLabel(MY_DICT.tr('delta_m_abs_lbl'), self)
                self.qlbl_delta_m_abs.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_delta_m_abs, row, 0)
                self.dspbx_delta_m_abs = MyQtWidgets.QDoubleSpinBoxDefault(self)
                self.dspbx_delta_m_abs.setFont(spbx_font_m)
                self.dspbx_delta_m_abs.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_delta_m_abs, row, 2,1,2)
                self.qlbl_unit_delta_m_abs = QtWidgets.QLabel('[...]', self)
                self.qlbl_unit_delta_m_abs.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_delta_m_abs, row, 5)

                row += 1


                self.qlbl_m_abs_valid_hint = QtWidgets.QLabel(self)
                self.qlbl_m_abs_valid_hint.setVisible(False)
                self.qlbl_m_abs_valid_hint.setStyleSheet("color:red;")
                self.stationing_grb.layout().addWidget(self.qlbl_m_abs_valid_hint, row, 1, 1, 6)

            if True:
                # M-fract-stationings
                row += 1
                self.m_fract_grp_hline = MyQtWidgets.HLine(self, 1, '#B7B7B7')
                self.stationing_grb.layout().addWidget(self.m_fract_grp_hline, row, 0, 1, 7)

                row += 1
                # M-fract-area with toggle-function, initially hidden
                self.m_fract_grp_wdg = QtWidgets.QWidget()
                self.m_fract_grp_wdg.setLayout(QtWidgets.QHBoxLayout())
                self.m_fract_grp_wdg.layout().setContentsMargins(0, 0, 0, 0)
                self.m_fract_grp_wdg.setToolTip(MY_DICT.tr('m_fract_grp_ttp'))

                self.pb_toggle_m_fract_grp = QtWidgets.QPushButton(self)
                self.pb_toggle_m_fract_grp.setFixedSize(14, 14)
                self.pb_toggle_m_fract_grp.setIconSize(QtCore.QSize(14, 14))
                self.pb_toggle_m_fract_grp.setIcon(QtGui.QIcon(':icons/plus-box-outline.svg'))
                self.pb_toggle_m_fract_grp.setStyleSheet("QPushButton { border: none; }")
                self.pb_toggle_m_fract_grp.setCursor(QtCore.Qt.PointingHandCursor)
                self.m_fract_grp_wdg.layout().addWidget(self.pb_toggle_m_fract_grp)
                qlbl_m_fract_group = QtWidgets.QLabel(MY_DICT.tr('m_fract_grp_lbl'), self)
                self.m_fract_grp_wdg.layout().addWidget(qlbl_m_fract_group)
                self.stationing_grb.layout().addWidget(self.m_fract_grp_wdg, row, 0, 1, 1, QtCore.Qt.AlignLeft)

                row += 1

                self.qlbl_m_fract = QtWidgets.QLabel(MY_DICT.tr('m_fract_lbl'), self)
                self.qlbl_m_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_m_fract, row, 0)
                self.dspbx_m_fract_from = MyQtWidgets.QDoubleSpinBoxDefault(self,0,100)
                self.dspbx_m_fract_from.setFont(spbx_font_m)
                self.dspbx_m_fract_from.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_m_fract_from, row, 1,1,2)

                self.dspbx_m_fract_to = MyQtWidgets.QDoubleSpinBoxDefault(self,0,100)
                self.dspbx_m_fract_to.setFont(spbx_font_m)
                self.dspbx_m_fract_to.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_m_fract_to, row, 3,1,2)
                self.qlbl_unit_m_fract = QtWidgets.QLabel('[%]', self)
                self.qlbl_unit_m_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_m_fract, row, 5)

                row += 1
                self.qlbl_delta_m_fract = QtWidgets.QLabel(MY_DICT.tr('delta_m_fract_lbl'), self)
                self.qlbl_delta_m_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_delta_m_fract, row, 0)
                self.dspbx_delta_m_fract = MyQtWidgets.QDoubleSpinBoxDefault(self)
                self.dspbx_delta_m_fract.setRange(-100,100)
                self.dspbx_delta_m_fract.setFont(spbx_font_m)
                self.dspbx_delta_m_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dspbx_delta_m_fract, row, 2,1,2)
                self.qlbl_unit_delta_m_fract = QtWidgets.QLabel('[%]', self)
                self.qlbl_unit_delta_m_fract.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_unit_delta_m_fract, row, 5)

                row += 1


                self.qlbl_m_fract_valid_hint = QtWidgets.QLabel(self)
                self.qlbl_m_fract_valid_hint.setVisible(False)
                self.qlbl_m_fract_valid_hint.setStyleSheet("color:red;")
                self.stationing_grb.layout().addWidget(self.qlbl_m_fract_valid_hint, row, 1, 1, 6)

            if True:
                # Z-values (elevation)
                row += 1
                self.z_grp_hline = MyQtWidgets.HLine(self,1, '#B7B7B7')
                self.stationing_grb.layout().addWidget(self.z_grp_hline, row, 0, 1, 7)

                row += 1
                # M-fract-area with toggle-function, initially hidden
                self.z_grp_wdg = QtWidgets.QWidget()
                self.z_grp_wdg.setLayout(QtWidgets.QHBoxLayout())
                self.z_grp_wdg.layout().setContentsMargins(0, 0, 0, 0)
                self.z_grp_wdg.setToolTip(MY_DICT.tr('z_grp_ttp'))

                self.pb_toggle_z_grp = QtWidgets.QPushButton(self)
                self.pb_toggle_z_grp.setFixedSize(14, 14)
                self.pb_toggle_z_grp.setIconSize(QtCore.QSize(14, 14))
                self.pb_toggle_z_grp.setIcon(QtGui.QIcon(':icons/plus-box-outline.svg'))
                self.pb_toggle_z_grp.setStyleSheet("QPushButton { border: none; }")
                self.pb_toggle_z_grp.setCursor(QtCore.Qt.PointingHandCursor)
                self.z_grp_wdg.layout().addWidget(self.pb_toggle_z_grp)
                qlbl_z_group = QtWidgets.QLabel(MY_DICT.tr('z_grp_lbl'), self)
                self.z_grp_wdg.layout().addWidget(qlbl_z_group)
                self.stationing_grb.layout().addWidget(self.z_grp_wdg, row, 0, 1, 1, QtCore.Qt.AlignLeft)

                row += 1

                # z-widgets, will be set visible dynamically if reference-layer is z-enabled

                self.qlbl_z = QtWidgets.QLabel(MY_DICT.tr('stationing_z_lbl'), self)
                self.qlbl_z.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_z, row, 0)
                self.dnspbx_z_from = MyQtWidgets.QDoubleNoSpinBox(self)
                self.dnspbx_z_from.setFont(le_font_m)
                self.dnspbx_z_from.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dnspbx_z_from, row, 1,1,2)

                self.dnspbx_z_to = MyQtWidgets.QDoubleNoSpinBox(self)
                self.dnspbx_z_to.setFont(le_font_m)
                self.dnspbx_z_to.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dnspbx_z_to, row, 3,1,2)

                self.qlbl_z_unit = QtWidgets.QLabel('[...]', self)
                self.qlbl_z_unit.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_z_unit, row, 5)

                row += 1
                self.qlbl_delta_z = QtWidgets.QLabel(MY_DICT.tr('delta_z_lbl'), self)
                self.qlbl_delta_z.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_delta_z, row, 0)
                self.dnspbx_delta_z_abs = MyQtWidgets.QDoubleNoSpinBox(self)
                self.dnspbx_delta_z_abs.setFont(spbx_font_m)
                self.dnspbx_delta_z_abs.setVisible(False)
                self.stationing_grb.layout().addWidget(self.dnspbx_delta_z_abs, row, 2,1,2)
                self.qlbl_delta_z_unit = QtWidgets.QLabel('[...]', self)
                self.qlbl_delta_z_unit.setVisible(False)
                self.stationing_grb.layout().addWidget(self.qlbl_delta_z_unit, row, 5)


            row += 1


            sub_wdg = QtWidgets.QWidget()
            sub_wdg.setLayout(QtWidgets.QHBoxLayout())

            self.tbtn_move_start = QtWidgets.QToolButton(self)
            self.tbtn_move_start.setStyleSheet("QToolButton { border: none; }")
            self.tbtn_move_start.setIconSize(QtCore.QSize(16, 16))
            self.tbtn_move_start.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowLeft.svg'))
            self.tbtn_move_start.setToolTip(MY_DICT.tr('move_to_start_ttp'))
            self.tbtn_move_start.setCursor(QtCore.Qt.PointingHandCursor)
            sub_wdg.layout().addWidget(self.tbtn_move_start)

            self.tbtn_flip_down = QtWidgets.QToolButton(self)
            self.tbtn_flip_down.setIcon(QtGui.QIcon(':icons/mActionDoubleArrowLeft.svg'))
            self.tbtn_flip_down.setStyleSheet("QToolButton { border: none; }")
            self.tbtn_flip_down.setIconSize(QtCore.QSize(16, 16))
            self.tbtn_flip_down.setToolTip(MY_DICT.tr('flip_down_ttp'))
            self.tbtn_flip_down.setCursor(QtCore.Qt.PointingHandCursor)
            sub_wdg.layout().addWidget(self.tbtn_flip_down)

            self.tbtn_move_down = QtWidgets.QToolButton(self)
            self.tbtn_move_down.setAutoRepeat(True)
            self.tbtn_move_down.setAutoRepeatDelay(500)
            self.tbtn_move_down.setAutoRepeatInterval(100)
            self.tbtn_move_down.setStyleSheet("QToolButton { border: none; }")
            self.tbtn_move_down.setIconSize(QtCore.QSize(16, 16))
            self.tbtn_move_down.setIcon(QtGui.QIcon(':icons/mActionArrowLeft.svg'))
            self.tbtn_move_down.setToolTip(MY_DICT.tr('move_down_ttp'))
            self.tbtn_move_down.setCursor(QtCore.Qt.PointingHandCursor)
            sub_wdg.layout().addWidget(self.tbtn_move_down)





            self.pbtn_insert_stationing = QtWidgets.QPushButton(self)
            self.pbtn_insert_stationing.setText(MY_DICT.tr('insert_pbtxt'))
            self.pbtn_insert_stationing.setIconSize(QtCore.QSize(25, 25))
            self.pbtn_insert_stationing.setIcon(QtGui.QIcon(':icons/insert_record.svg'))
            self.pbtn_insert_stationing.setToolTip(MY_DICT.tr('insert_ttp'))
            sub_wdg.layout().addWidget(self.pbtn_insert_stationing, row)

            self.pbtn_update_stationing = QtWidgets.QPushButton(self)
            self.pbtn_update_stationing.setText(MY_DICT.tr('update_blank_pbtxt'))
            self.pbtn_update_stationing.setIconSize(QtCore.QSize(25, 25))
            self.pbtn_update_stationing.setIcon(QtGui.QIcon(':icons/mActionFileSave.svg'))
            self.pbtn_update_stationing.setToolTip(MY_DICT.tr('update_ttp'))
            sub_wdg.layout().addWidget(self.pbtn_update_stationing, row)

            self.pbtn_resume_stationing = QtWidgets.QPushButton(self)
            self.pbtn_resume_stationing.setText(MY_DICT.tr('resume_pbtxt'))
            self.pbtn_resume_stationing.setIconSize(QtCore.QSize(25, 25))
            self.pbtn_resume_stationing.setIcon(QtGui.QIcon(':icons/re_digitize_lol.svg'))
            self.pbtn_resume_stationing.setToolTip(MY_DICT.tr('resume_ttp'))
            self.pbtn_resume_stationing.setCheckable(True)
            sub_wdg.layout().addWidget(self.pbtn_resume_stationing, row)


            self.tbtn_move_up = QtWidgets.QToolButton(self)
            self.tbtn_move_up.setAutoRepeat(True)
            self.tbtn_move_up.setAutoRepeatDelay(500)
            self.tbtn_move_up.setAutoRepeatInterval(100)
            self.tbtn_move_up.setStyleSheet("QToolButton { border: none; }")
            self.tbtn_move_up.setIconSize(QtCore.QSize(16, 16))
            self.tbtn_move_up.setIcon(QtGui.QIcon(':icons/mActionArrowRight.svg'))
            self.tbtn_move_up.setToolTip(MY_DICT.tr('move_up_ttp'))
            self.tbtn_move_up.setCursor(QtCore.Qt.PointingHandCursor)
            sub_wdg.layout().addWidget(self.tbtn_move_up)

            self.tbtn_flip_up = QtWidgets.QToolButton(self)
            self.tbtn_flip_up.setIcon(QtGui.QIcon(':icons/mActionDoubleArrowRight.svg'))
            self.tbtn_flip_up.setStyleSheet("QToolButton { border: none; }")
            self.tbtn_flip_up.setIconSize(QtCore.QSize(16, 16))
            self.tbtn_flip_up.setToolTip(MY_DICT.tr('flip_up_ttp'))
            self.tbtn_flip_up.setCursor(QtCore.Qt.PointingHandCursor)
            sub_wdg.layout().addWidget(self.tbtn_flip_up)

            self.tbtn_move_end = QtWidgets.QToolButton(self)
            self.tbtn_move_end.setIcon(QtGui.QIcon(':icons/mActionTrippleArrowRight.svg'))
            self.tbtn_move_end.setStyleSheet("QToolButton { border: none; }")
            self.tbtn_move_end.setIconSize(QtCore.QSize(16, 16))
            self.tbtn_move_end.setToolTip(MY_DICT.tr('move_end_ttp'))
            self.tbtn_move_end.setCursor(QtCore.Qt.PointingHandCursor)
            sub_wdg.layout().addWidget(self.tbtn_move_end)



            self.stationing_grb.layout().addWidget(sub_wdg, row, 0, 1, 5)

            self.pb_move_segment = QtWidgets.QPushButton(self)
            self.pb_move_segment.setFixedSize(20, 20)
            # without border the checked-status will not be visible
            #self.pb_move_segment.setStyleSheet("QPushButton { border: none; }")
            self.pb_move_segment.setIconSize(QtCore.QSize(16, 16))
            self.pb_move_segment.setIcon(QtGui.QIcon(':icons/move_segment.svg'))
            self.pb_move_segment.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_move_segment.setToolTip(MY_DICT.tr('move_segment_ttp'))
            self.pb_move_segment.setCheckable(True)
            self.stationing_grb.layout().addWidget(self.pb_move_segment, row, 5)

            self.pb_change_offset = QtWidgets.QPushButton(self)
            self.pb_change_offset.setFixedSize(20, 20)
            # without border the checked-status will not be visible
            #self.pb_change_offset.setStyleSheet("QPushButton { border: none; }")
            self.pb_change_offset.setIconSize(QtCore.QSize(16, 16))
            self.pb_change_offset.setIcon(QtGui.QIcon(':icons/change_offset.svg'))
            self.pb_change_offset.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_change_offset.setToolTip(MY_DICT.tr('change_offset_ttp'))
            self.pb_change_offset.setCheckable(True)
            sub_wdg.layout().addWidget(self.pb_change_offset)
            self.stationing_grb.layout().addWidget(self.pb_change_offset, row, 6)

            self.pb_zoom_to_stationings = QtWidgets.QPushButton(self)
            self.pb_zoom_to_stationings.setFixedSize(20, 20)
            self.pb_zoom_to_stationings.setStyleSheet("QPushButton { border: none; }")
            self.pb_zoom_to_stationings.setIconSize(QtCore.QSize(18, 18))
            self.pb_zoom_to_stationings.setIcon(QtGui.QIcon(':icons/mIconZoom.svg'))
            self.pb_zoom_to_stationings.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_zoom_to_stationings.setToolTip(MY_DICT.tr('zoom_to_stationings_ttp'))

            self.stationing_grb.layout().addWidget(self.pb_zoom_to_stationings, row, 7)

            stationing_container_wdg.layout().addWidget(self.stationing_grb)

            row += 1

            # add a stretch below to push the contents to the top and not spread it vertically
            stationing_container_wdg.layout().addStretch(1)


            self.tbw_central.addTab(stationing_container_wdg, MY_DICT.tr('stationing_tab'))
            # End stationing_container_wdg ######################################################################################

        # Begin feature_selection_wdg ######################################################################################
        if True:



            feature_selection_wdg = QtWidgets.QWidget(self)
            feature_selection_wdg.setLayout(QtWidgets.QVBoxLayout())
            feature_selection_wdg.setStyleSheet("QWidget {background-color: #FFFFFFFF;}")

            feature_selection_wdg.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('extend_feature_selection'), self))

            sub_sub_wdg = QtWidgets.QWidget()
            sub_sub_wdg.setLayout(QtWidgets.QGridLayout())

            sub_sub_sub_wdg = QtWidgets.QWidget()
            sub_sub_sub_wdg.setLayout(QtWidgets.QHBoxLayout())
            sub_sub_sub_wdg.layout().setContentsMargins(0, 0, 0, 0)

            self.pbtn_append_data_features = QtWidgets.QPushButton(self)
            self.pbtn_append_data_features.setText(MY_DICT.tr('append_data_features_pbtxt'))
            self.pbtn_append_data_features.setIcon(QtGui.QIcon(':icons/mActionEditIndentMore.svg'))
            self.pbtn_append_data_features.setToolTip(MY_DICT.tr('append_data_features_ttp'))
            sub_sub_sub_wdg.layout().addWidget(self.pbtn_append_data_features)

            self.pb_open_data_tbl_2 = QtWidgets.QPushButton(self)
            self.pb_open_data_tbl_2.setFixedSize(20, 20)
            self.pb_open_data_tbl_2.setStyleSheet("QPushButton { border: none; }")
            self.pb_open_data_tbl_2.setIconSize(QtCore.QSize(16, 16))
            self.pb_open_data_tbl_2.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
            self.pb_open_data_tbl_2.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_open_data_tbl_2.setToolTip(MY_DICT.tr('open_table_ttp'))
            sub_sub_sub_wdg.layout().addWidget(self.pb_open_data_tbl_2)

            sub_sub_wdg.layout().addWidget(sub_sub_sub_wdg,0,0)

            sub_sub_sub_wdg = QtWidgets.QWidget()
            sub_sub_sub_wdg.setLayout(QtWidgets.QHBoxLayout())
            sub_sub_sub_wdg.layout().setContentsMargins(0, 0, 0, 0)
            self.pbtn_append_show_features = QtWidgets.QPushButton(self)
            self.pbtn_append_show_features.setText(MY_DICT.tr('append_show_features_pbtxt'))
            self.pbtn_append_show_features.setIcon(QtGui.QIcon(':icons/mActionEditIndentMore.svg'))
            self.pbtn_append_show_features.setToolTip(MY_DICT.tr('append_show_features_ttp'))
            sub_sub_sub_wdg.layout().addWidget(self.pbtn_append_show_features)

            self.pb_open_show_tbl_2 = QtWidgets.QPushButton(self)
            self.pb_open_show_tbl_2.setFixedSize(20, 20)
            self.pb_open_show_tbl_2.setStyleSheet("QPushButton { border: none; }")
            self.pb_open_show_tbl_2.setIconSize(QtCore.QSize(16, 16))
            self.pb_open_show_tbl_2.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
            self.pb_open_show_tbl_2.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_open_show_tbl_2.setToolTip(MY_DICT.tr('open_table_ttp'))
            sub_sub_sub_wdg.layout().addWidget(self.pb_open_show_tbl_2)

            # button to select edit-features from show-layer
            self.pbtn_select_features = QtWidgets.QPushButton(self)
            self.pbtn_select_features.setFixedSize(20, 20)
            #self.pbtn_select_features.setStyleSheet("QPushButton { border: none; }")
            self.pbtn_select_features.setIconSize(QtCore.QSize(16, 16))
            self.pbtn_select_features.setCheckable(True)
            self.pbtn_select_features.setIcon(QtGui.QIcon(':icons/select_point_features.svg'))
            self.pbtn_select_features.setCursor(QtCore.Qt.PointingHandCursor)
            self.pbtn_select_features.setToolTip(MY_DICT.tr('select_features_ttp'))
            sub_sub_sub_wdg.layout().addWidget(self.pbtn_select_features)



            sub_sub_wdg.layout().addWidget(sub_sub_sub_wdg,0,1)



            feature_selection_wdg.layout().addWidget(sub_sub_wdg)

            # table to show the selected edit-features
            self.qtrv_feature_selection = QtWidgets.QTreeView()
            self.qtrv_feature_selection.setFont(default_font_m)
            self.qtrv_feature_selection.setAlternatingRowColors(True)
            self.qtrv_feature_selection.setIconSize(QtCore.QSize(10, 10))
            self.qtrv_feature_selection.setUniformRowHeights(True)
            self.qtrv_feature_selection.setWordWrap(False)
            self.qtrv_feature_selection.setEditTriggers(self.qtrv_feature_selection.NoEditTriggers)
            self.qtrv_feature_selection.setSortingEnabled(True)

            #self.qtrv_feature_selection.setStyleSheet("QTreeWidget::item {border-bottom: 1px solid rgb(216, 216, 216);}")



            header_labels = [
                MY_DICT.tr('qtrv_feature_selection_reference_and_data_layer_hlbl'),
                MY_DICT.tr('qtrv_feature_selection_stationing_from_hlbl'),
                MY_DICT.tr('qtrv_feature_selection_stationing_to_hlbl'),
                MY_DICT.tr('qtrv_feature_selection_offset_hlbl'),
                MY_DICT.tr('qtrv_feature_selection_seglen_hlbl'),
                MY_DICT.tr('qtrv_feature_selection_show_layer_hlbl'),
            ]

            root_model = QtGui.QStandardItemModel()
            self.qtrv_feature_selection.setModel(root_model)
            self.qtrv_feature_selection.model().setHorizontalHeaderLabels(header_labels)

            # replacement for self.my_dialog.qtrv_feature_selection.resizeColumnToContents(0) => only works if called two times
            # self.qtrv_feature_selection.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents) => column is no more interactive-resizable
            self.qtrv_feature_selection.setColumnWidth(0, 250)


            # reference + data-layer
            self.cdlg_0 = MyDelegates.PaddingLeftDelegate(49,164)
            self.qtrv_feature_selection.setItemDelegateForColumn(0, self.cdlg_0)

            # From
            self.cdlg_1 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_feature_selection.setItemDelegateForColumn(1, self.cdlg_1)

            # To
            self.cdlg_2 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_feature_selection.setItemDelegateForColumn(2, self.cdlg_2)

            # Offset
            self.cdlg_3 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_feature_selection.setItemDelegateForColumn(3, self.cdlg_3)

            # delta
            self.cdlg_4 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_feature_selection.setItemDelegateForColumn(4, self.cdlg_4)

            # show-layer
            self.cdlg_5 = MyDelegates.PaddingLeftDelegate(0,26)
            self.qtrv_feature_selection.setItemDelegateForColumn(5, self.cdlg_5)


            feature_selection_wdg.layout().addWidget(self.qtrv_feature_selection)

            sub_sub_wdg = QtWidgets.QWidget()
            sub_sub_wdg.setLayout(QtWidgets.QGridLayout())

            self.pbtn_zoom_to_feature_selection = QtWidgets.QPushButton(self)
            self.pbtn_zoom_to_feature_selection.setText(MY_DICT.tr('zoom_to_selection_pbtxt'))
            self.pbtn_zoom_to_feature_selection.setIcon(QtGui.QIcon(':icons/mActionPanToSelected.svg'))
            sub_sub_wdg.layout().addWidget(self.pbtn_zoom_to_feature_selection,0,0)

            self.pbtn_clear_features = QtWidgets.QPushButton(self)
            self.pbtn_clear_features.setText(MY_DICT.tr('clear_selection_pbtxt'))
            self.pbtn_clear_features.setIcon(QtGui.QIcon(':icons/mActionDeselectActiveLayer.svg'))
            sub_sub_wdg.layout().addWidget(self.pbtn_clear_features,0,1)


            self.pbtn_transfer_feature_selection = QtWidgets.QPushButton(self)
            self.pbtn_transfer_feature_selection.setText(MY_DICT.tr('transfer_feature_selection_pbtxt'))
            self.pbtn_transfer_feature_selection.setIcon(QtGui.QIcon(':icons/mActionInvertSelection.svg'))
            self.pbtn_transfer_feature_selection.setToolTip(MY_DICT.tr('transfer_feature_selection_ttp'))
            sub_sub_wdg.layout().addWidget(self.pbtn_transfer_feature_selection, 0, 2)

            self.pbtn_feature_selection_to_data_layer_filter = QtWidgets.QPushButton(self)
            self.pbtn_feature_selection_to_data_layer_filter.setText(MY_DICT.tr('set_feature_selection_filter_pbtxt'))
            self.pbtn_feature_selection_to_data_layer_filter.setIcon(QtGui.QIcon(':icons/mActionFilter2.svg'))
            self.pbtn_feature_selection_to_data_layer_filter.setToolTip(MY_DICT.tr('set_feature_selection_filter_ttp'))
            sub_sub_wdg.layout().addWidget(self.pbtn_feature_selection_to_data_layer_filter,0,3)

            feature_selection_wdg.layout().addWidget(sub_sub_wdg)

            self.tbw_central.addTab(feature_selection_wdg, MY_DICT.tr('feature_selection_tab'))
            # End feature_selection_wdg ######################################################################################

        # Begin post_processing_container_wdg ######################################################################################
        if True:


            post_processing_container_wdg = QtWidgets.QWidget(self)
            post_processing_container_wdg.setLayout(QtWidgets.QVBoxLayout())
            post_processing_container_wdg.setStyleSheet("QWidget {background-color: #FFFFFFFF;}")

            ql_info = QtWidgets.QLabel(MY_DICT.tr('po_pro_info_lbl'), self)
            ql_info.setWordWrap(True)
            post_processing_container_wdg.layout().addWidget(ql_info)

            # table to show the selected edit-features
            self.qtrv_po_pro_selection = QtWidgets.QTreeView()
            self.qtrv_po_pro_selection.setFont(default_font_m)
            self.qtrv_po_pro_selection.setAlternatingRowColors(True)
            self.qtrv_po_pro_selection.setIconSize(QtCore.QSize(10, 10))
            self.qtrv_po_pro_selection.setUniformRowHeights(True)
            self.qtrv_po_pro_selection.setWordWrap(False)
            self.qtrv_po_pro_selection.setEditTriggers(self.qtrv_po_pro_selection.NoEditTriggers)
            self.qtrv_po_pro_selection.setSortingEnabled(True)


            header_labels = [
                MY_DICT.tr('qtw_post_processing_reference_and_data_layer_hlbl'),
                MY_DICT.tr('qtw_post_processing_stationing_from_current_hlbl'),
                MY_DICT.tr('qtw_post_processing_stationing_to_current_hlbl'),
                MY_DICT.tr('qtw_post_processing_stationing_from_cached_hlbl'),
                MY_DICT.tr('qtw_post_processing_stationing_to_cached_hlbl')
            ]

            root_model = QtGui.QStandardItemModel()
            self.qtrv_po_pro_selection.setModel(root_model)
            self.qtrv_po_pro_selection.model().setHorizontalHeaderLabels(header_labels)

            self.qtrv_po_pro_selection.setColumnWidth(0, 250)


            self.cdlg_po_pro_0 = MyDelegates.PaddingLeftDelegate(72,164)
            self.qtrv_po_pro_selection.setItemDelegateForColumn(0, self.cdlg_po_pro_0)

            # From current
            self.cdlg_po_pro_1 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_po_pro_selection.setItemDelegateForColumn(1, self.cdlg_po_pro_1)

            # To current
            self.cdlg_po_pro_2 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_po_pro_selection.setItemDelegateForColumn(2, self.cdlg_po_pro_2)

            # From cached
            self.cdlg_po_pro_3 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_po_pro_selection.setItemDelegateForColumn(3, self.cdlg_po_pro_3)

            # To cached
            self.cdlg_po_pro_4 = MyDelegates.DoubleSelectBorderDelegate()
            self.qtrv_po_pro_selection.setItemDelegateForColumn(4, self.cdlg_po_pro_4)


            post_processing_container_wdg.layout().addWidget(self.qtrv_po_pro_selection)



            sub_sub_wdg = QtWidgets.QWidget()
            sub_sub_wdg.setLayout(QtWidgets.QHBoxLayout())

            self.pbtn_zoom_po_pro = QtWidgets.QPushButton(self)
            self.pbtn_zoom_po_pro.setText(MY_DICT.tr('zoom_to_po_pro_selection_pbtxt'))
            self.pbtn_zoom_po_pro.setMinimumWidth(25)
            self.pbtn_zoom_po_pro.setIcon(QtGui.QIcon(':icons/mActionPanToSelected.svg'))
            self.pbtn_zoom_po_pro.setToolTip(MY_DICT.tr('zoom_po_pro_ttp'))
            sub_sub_wdg.layout().addWidget(self.pbtn_zoom_po_pro)


            self.pbtn_clear_po_pro = QtWidgets.QPushButton(self)
            self.pbtn_clear_po_pro.setText(MY_DICT.tr('clear_po_pro_selection_pbtxt'))
            self.pbtn_clear_po_pro.setMinimumWidth(25)
            self.pbtn_clear_po_pro.setIcon(QtGui.QIcon(':icons/mActionDeselectActiveLayer.svg'))
            self.pbtn_clear_po_pro.setToolTip(MY_DICT.tr('clear_po_pro_selection_ttp'))
            sub_sub_wdg.layout().addWidget(self.pbtn_clear_po_pro)


            post_processing_container_wdg.layout().addWidget(sub_sub_wdg)
            self.tbw_central.addTab(post_processing_container_wdg, MY_DICT.tr('post_processing_tab'))
            # End post_processing_container_wdg ######################################################################################

        # Start settings_container_wdg
        if True:


            settings_container_wdg = QtWidgets.QWidget(self)
            settings_container_wdg.setLayout(QtWidgets.QVBoxLayout())
            settings_container_wdg.setStyleSheet("QWidget {background-color: #FFFFFFFF;}")


            layers_and_fields_grb = MyQtWidgets.QGroupBoxExpandable(MY_DICT.tr('layers_and_fields_gb_title'), True, self)
            layers_and_fields_grb.setLayout(QtWidgets.QGridLayout())

            row = 0

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('reference_layer_lbl'), self), row, 0)
            self.qcbn_reference_layer = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Layer', 'Geometry', 'Provider', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_reference_layer.setFont(cbx_font_m)
            self.qcbn_reference_layer.setToolTip(MY_DICT.tr('reference_layer_ttp'))

            layers_and_fields_grb.layout().addWidget(self.qcbn_reference_layer, row, 1)

            self.pb_open_ref_tbl = QtWidgets.QPushButton(self)
            self.pb_open_ref_tbl.setFixedSize(20, 20)
            self.pb_open_ref_tbl.setStyleSheet("QPushButton { border: none; }")
            self.pb_open_ref_tbl.setIconSize(QtCore.QSize(16, 16))
            self.pb_open_ref_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
            self.pb_open_ref_tbl.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_open_ref_tbl.setToolTip(MY_DICT.tr('open_table_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pb_open_ref_tbl, row, 2)

            self.pb_call_ref_disp_exp_dlg = QtWidgets.QPushButton(self)
            self.pb_call_ref_disp_exp_dlg.setFixedSize(20, 20)
            self.pb_call_ref_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
            self.pb_call_ref_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
            self.pb_call_ref_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
            self.pb_call_ref_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_call_ref_disp_exp_dlg.setToolTip(MY_DICT.tr('edit_display_exp_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pb_call_ref_disp_exp_dlg, row, 3)



            row += 1

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('ref_lyr_id_field_lbl'), self), row, 0)

            self.qcbn_ref_lyr_id_field = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Field', 'Type', 'PK', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_ref_lyr_id_field.setFont(cbx_font_m)
            self.qcbn_ref_lyr_id_field.setToolTip(MY_DICT.tr('ref_lyr_id_field_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_ref_lyr_id_field, row, 1)

            row += 1

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('data_layer_lbl'), self), row, 0)

            self.qcbn_data_layer = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Layer', 'Geometry', 'Provider', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_data_layer.setFont(cbx_font_m)
            self.qcbn_data_layer.setToolTip(MY_DICT.tr('data_layer_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer, row, 1)

            self.pb_open_data_tbl = QtWidgets.QPushButton(self)
            self.pb_open_data_tbl.setFixedSize(20, 20)
            self.pb_open_data_tbl.setStyleSheet("QPushButton { border: none; }")
            self.pb_open_data_tbl.setIconSize(QtCore.QSize(16, 16))
            self.pb_open_data_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
            self.pb_open_data_tbl.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_open_data_tbl.setToolTip(MY_DICT.tr('open_table_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pb_open_data_tbl, row, 2)

            self.pb_call_data_disp_exp_dlg = QtWidgets.QPushButton(self)
            self.pb_call_data_disp_exp_dlg.setFixedSize(20, 20)
            self.pb_call_data_disp_exp_dlg.setStyleSheet("QPushButton { border: none; }")
            self.pb_call_data_disp_exp_dlg.setIconSize(QtCore.QSize(16, 16))
            self.pb_call_data_disp_exp_dlg.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
            self.pb_call_data_disp_exp_dlg.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_call_data_disp_exp_dlg.setToolTip(MY_DICT.tr('edit_display_exp_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pb_call_data_disp_exp_dlg, row, 3)

            self.pbtn_create_data_layer = QtWidgets.QPushButton(self)
            self.pbtn_create_data_layer.setFixedSize(20, 20)
            self.pbtn_create_data_layer.setStyleSheet("QPushButton { border: none; }")
            self.pbtn_create_data_layer.setIconSize(QtCore.QSize(16, 16))
            self.pbtn_create_data_layer.setIcon(QtGui.QIcon(':icons/NewDataTable.svg'))
            self.pbtn_create_data_layer.setCursor(QtCore.Qt.PointingHandCursor)

            self.pbtn_create_data_layer.setToolTip(MY_DICT.tr('or_create_data_layer_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pbtn_create_data_layer, row, 4)


            row += 1
            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('data_lyr_id_field_lbl'), self), row, 0)
            self.qcbn_data_layer_id_field = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Field', 'Type', 'PK', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft,QtCore.Qt.AlignLeft,QtCore.Qt.AlignCenter,QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_data_layer_id_field.setFont(cbx_font_m)
            self.qcbn_data_layer_id_field.setToolTip(MY_DICT.tr('data_layer_id_field_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_id_field, row, 1)

            row += 1

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('data_layer_reference_field_lbl'), self), row, 0)
            self.qcbn_data_layer_reference_field = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Field', 'Type', 'PK', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_data_layer_reference_field.setFont(cbx_font_m)
            self.qcbn_data_layer_reference_field.setToolTip(MY_DICT.tr('data_layer_ref_field_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_reference_field, row, 1)

            row +=1

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('data_layer_offset_field_lbl'), self), row, 0)
            self.qcbn_data_layer_offset_field = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Field', 'Type', 'PK', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_data_layer_offset_field.setFont(cbx_font_m)
            self.qcbn_data_layer_offset_field.setToolTip(MY_DICT.tr('data_layer_offset_field_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_offset_field, row, 1)



            row +=1

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('data_layer_stationing_from_field_lbl'), self), row, 0)
            self.qcbn_data_layer_stationing_from_field = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Field', 'Type', 'PK', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_data_layer_stationing_from_field.setFont(cbx_font_m)
            self.qcbn_data_layer_stationing_from_field.setToolTip(MY_DICT.tr('data_layer_stationing_field_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_stationing_from_field, row, 1)

            row += 1

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('data_layer_stationing_to_field_lbl'), self), row, 0)
            self.qcbn_data_layer_stationing_to_field = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Field', 'Type', 'PK', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_data_layer_stationing_to_field.setFont(cbx_font_m)
            self.qcbn_data_layer_stationing_to_field.setToolTip(MY_DICT.tr('data_layer_stationing_field_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_data_layer_stationing_to_field, row, 1)

            row += 1
            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('lr_mode_lbl')), row, 0)
            self.qcb_lr_mode = QtWidgets.QComboBox(self)
            self.qcb_lr_mode.setToolTip(MY_DICT.tr('lr_mode_ttp'))
            self.qcb_lr_mode.setFont(cbx_font_m)

            layers_and_fields_grb.layout().addWidget(self.qcb_lr_mode, row, 1)


            row += 1
            # new: storage-precision, avoid pi-like stationing 3.14159265359...
            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('storage_precision_lbl'), self), row,0)
            self.qcb_storage_precision = QtWidgets.QComboBox()
            self.qcb_storage_precision.setFont(cbx_font_m)
            self.qcb_storage_precision.setToolTip(MY_DICT.tr('storage_precision_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcb_storage_precision, row, 1)




            # Show-Layer

            row += 1
            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('show_layer_lbl'), self), row, 0)
            self.qcbn_show_layer = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Layer', 'Geometry', 'Provider', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_show_layer.setFont(cbx_font_m)
            self.qcbn_show_layer.setToolTip(MY_DICT.tr('show_layer_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer, row, 1)

            self.pb_open_show_tbl = QtWidgets.QPushButton(self)
            self.pb_open_show_tbl.setFixedSize(20, 20)
            self.pb_open_show_tbl.setStyleSheet("QPushButton { border: none; }")
            self.pb_open_show_tbl.setIconSize(QtCore.QSize(16, 16))
            self.pb_open_show_tbl.setIcon(QtGui.QIcon(':icons/mActionOpenTable.svg'))
            self.pb_open_show_tbl.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_open_show_tbl.setToolTip(MY_DICT.tr('open_table_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pb_open_show_tbl, row, 2)

            self.pb_edit_show_layer_display_expression = QtWidgets.QPushButton(self)
            self.pb_edit_show_layer_display_expression.setFixedSize(20, 20)
            self.pb_edit_show_layer_display_expression.setStyleSheet("QPushButton { border: none; }")
            self.pb_edit_show_layer_display_expression.setIconSize(QtCore.QSize(16, 16))
            self.pb_edit_show_layer_display_expression.setIcon(QtGui.QIcon(':icons/mIconExpression.svg'))
            self.pb_edit_show_layer_display_expression.setCursor(QtCore.Qt.PointingHandCursor)
            self.pb_edit_show_layer_display_expression.setToolTip(MY_DICT.tr('edit_display_exp_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pb_edit_show_layer_display_expression, row, 3)

            self.pbtn_create_show_layer = QtWidgets.QPushButton(self)
            self.pbtn_create_show_layer.setFixedSize(20, 20)
            self.pbtn_create_show_layer.setStyleSheet("QPushButton { border: none; }")
            self.pbtn_create_show_layer.setIconSize(QtCore.QSize(16, 16))
            self.pbtn_create_show_layer.setIcon(QtGui.QIcon(':icons/NewDataTable.svg'))
            self.pbtn_create_show_layer.setCursor(QtCore.Qt.PointingHandCursor)

            self.pbtn_create_show_layer.setToolTip(MY_DICT.tr('or_create_show_layer_ttp'))
            layers_and_fields_grb.layout().addWidget(self.pbtn_create_show_layer, row, 4)

            row += 1

            layers_and_fields_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('show_layer_back_reference_field_lbl')), row, 0)
            self.qcbn_show_layer_back_reference_field = MyQtWidgets.QComboBoxN(
                self,
                show_clear_button=True,
                append_index_col=True,
                col_names=['Field', 'Type', 'PK', 'idx'],
                col_alignments=[QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft, QtCore.Qt.AlignCenter, QtCore.Qt.AlignCenter],
                enable_row_by_col_idx=0,
                column_resize_mode=QtWidgets.QHeaderView.ResizeToContents,
                sorting_enabled=True,
                initial_sort_col_idx=3,
                initial_sort_order=QtCore.Qt.AscendingOrder,
                clear_button_icon=QtGui.QIcon(':icons/backspace-outline.svg')
            )
            self.qcbn_show_layer_back_reference_field.setFont(cbx_font_m)
            self.qcbn_show_layer_back_reference_field.setToolTip(MY_DICT.tr('show_layer_back_reference_field_ttp'))
            layers_and_fields_grb.layout().addWidget(self.qcbn_show_layer_back_reference_field, row, 1)



            settings_container_wdg.layout().addWidget(layers_and_fields_grb)

            style_grb = MyQtWidgets.QGroupBoxExpandable(MY_DICT.tr('styles_grpbx'), False, self)
            style_grb.setLayout(QtWidgets.QGridLayout())

            # see https://qgis.org/pyqgis/master/gui/QgsVertexMarker.html
            point_symbol_items = {0: "None", 1: "Cross", 2: "X", 3: "Box", 4: "Circle", 5: "Double-Triangle", 6: "Triangle", 7: "Rhombus", 8: "Inverted Triangle"}

            # see https://doc.qt.io/qt-6/qt.html#PenStyle-enum
            # 6 -> Qt.CustomDashLine not implemented here...
            line_symbol_items = {0: "None", 1: "Solid", 2: "Dash", 3: "Dot", 4: "DashDot", 5: "DashDotDot"}

            row = 0
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('symbol_lbl')), row, 1)
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('size_lbl')), row, 2)
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('width_lbl')), row, 3)
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('color_lbl')), row, 4)
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('fill_color_lbl')), row, 5)

            row += 1
            # Stationing-Point-From
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('stationing_point_from_lbl')), row, 0)
            self.qcb_pt_snf_icon_type = QtWidgets.QComboBox(self)
            self.qcb_pt_snf_icon_type.setFont(cbx_font_m)
            for key in point_symbol_items:
                self.qcb_pt_snf_icon_type.addItem(point_symbol_items[key], key)

            style_grb.layout().addWidget(self.qcb_pt_snf_icon_type, row, 1)
            self.qspb_pt_snf_icon_size = QtWidgets.QSpinBox()
            self.qspb_pt_snf_icon_size.setFont(spbx_font_m)
            self.qspb_pt_snf_icon_size.setRange(0, 100)
            style_grb.layout().addWidget(self.qspb_pt_snf_icon_size, row, 2)
            self.qspb_pt_snf_pen_width = QtWidgets.QSpinBox()
            self.qspb_pt_snf_pen_width.setFont(spbx_font_m)
            self.qspb_pt_snf_pen_width.setRange(0, 20)
            style_grb.layout().addWidget(self.qspb_pt_snf_pen_width, row, 3)
            self.qpb_pt_snf_color = MyQtWidgets.QPushButtonColor()
            style_grb.layout().addWidget(self.qpb_pt_snf_color, row, 4)
            self.qpb_pt_snf_fill_color = MyQtWidgets.QPushButtonColor()
            style_grb.layout().addWidget(self.qpb_pt_snf_fill_color, row, 5)


            row += 1
            # Stationing-Point-To
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('stationing_point_to_lbl')), row, 0)
            self.qcb_pt_snt_icon_type = QtWidgets.QComboBox(self)
            self.qcb_pt_snt_icon_type.setFont(cbx_font_m)
            for key in point_symbol_items:
                self.qcb_pt_snt_icon_type.addItem(point_symbol_items[key], key)

            style_grb.layout().addWidget(self.qcb_pt_snt_icon_type, row, 1)
            self.qspb_pt_snt_icon_size = QtWidgets.QSpinBox()
            self.qspb_pt_snt_icon_size.setFont(spbx_font_m)
            self.qspb_pt_snt_icon_size.setRange(0, 100)
            style_grb.layout().addWidget(self.qspb_pt_snt_icon_size, row, 2)
            self.qspb_pt_snt_pen_width = QtWidgets.QSpinBox()
            self.qspb_pt_snt_pen_width.setFont(spbx_font_m)
            self.qspb_pt_snt_pen_width.setRange(0, 20)
            style_grb.layout().addWidget(self.qspb_pt_snt_pen_width, row, 3)
            self.qpb_pt_snt_color = MyQtWidgets.QPushButtonColor()
            style_grb.layout().addWidget(self.qpb_pt_snt_color, row, 4)
            self.qpb_pt_snt_fill_color = MyQtWidgets.QPushButtonColor()
            style_grb.layout().addWidget(self.qpb_pt_snt_fill_color, row, 5)



            row += 1
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('reference_line_lbl')), row, 0)
            self.qcb_ref_line_style = QtWidgets.QComboBox()
            self.qcb_ref_line_style.setFont(cbx_font_m)
            for key in line_symbol_items:
                # addItem uses role 0 and 256
                self.qcb_ref_line_style.addItem(line_symbol_items[key], key)

            style_grb.layout().addWidget(self.qcb_ref_line_style, row, 1)
            self.qspb_ref_line_width = QtWidgets.QSpinBox()
            self.qspb_ref_line_width.setFont(spbx_font_m)
            self.qspb_ref_line_width.setRange(0, 20)
            style_grb.layout().addWidget(self.qspb_ref_line_width, row, 3)
            self.qpb_ref_line_color = MyQtWidgets.QPushButtonColor()
            style_grb.layout().addWidget(self.qpb_ref_line_color, row, 4)

            row += 1
            style_grb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('segment_line_lbl')), row, 0)
            self.qcb_segment_line_style = QtWidgets.QComboBox()
            self.qcb_segment_line_style.setFont(cbx_font_m)
            for key in line_symbol_items:
                self.qcb_segment_line_style.addItem(line_symbol_items[key], key)
            style_grb.layout().addWidget(self.qcb_segment_line_style, row, 1)
            self.qspb_segment_line_width = QtWidgets.QSpinBox()
            self.qspb_segment_line_width.setFont(spbx_font_m)
            self.qspb_segment_line_width.setRange(0, 20)
            style_grb.layout().addWidget(self.qspb_segment_line_width, row, 3)
            self.qpb_segment_line_color = MyQtWidgets.QPushButtonColor()
            style_grb.layout().addWidget(self.qpb_segment_line_color, row, 4)

            row += 1
            self.pb_reset_style = QtWidgets.QPushButton(MY_DICT.tr('reset_style'))
            self.pb_reset_style.setToolTip(MY_DICT.tr('reset_style_ttp'))
            style_grb.layout().addWidget(self.pb_reset_style, row, 0, 1, 6)
            


            settings_container_wdg.layout().addWidget(style_grb)


            store_configurations_gb = MyQtWidgets.QGroupBoxExpandable(MY_DICT.tr('store_configs_grpbx_lbl'), False, self)
            store_configurations_gb.setLayout(QtWidgets.QVBoxLayout())

            store_configurations_gb.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('stored_configs')))

            self.lw_stored_settings = QtWidgets.QListWidget()
            self.lw_stored_settings.setFont(default_font_m)
            self.lw_stored_settings.setFixedHeight(100)
            self.lw_stored_settings.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            store_configurations_gb.layout().addWidget(self.lw_stored_settings)

            self.pb_store_configuration = QtWidgets.QPushButton(MY_DICT.tr('store_current_config'))
            store_configurations_gb.layout().addWidget(self.pb_store_configuration)

            self.pb_restore_configuration = QtWidgets.QPushButton(MY_DICT.tr('restore_selected_config'))
            store_configurations_gb.layout().addWidget(self.pb_restore_configuration)

            self.pb_delete_configuration = QtWidgets.QPushButton(MY_DICT.tr('delete_selected_config'))
            store_configurations_gb.layout().addWidget(self.pb_delete_configuration)

            settings_container_wdg.layout().addWidget(store_configurations_gb)



            #add a stretch below to push the contents to the top and not spread it vertically
            settings_container_wdg.layout().addStretch(1)
            self.tbw_central.addTab(settings_container_wdg, MY_DICT.tr('settings_tab'))

            # End settings_container_wdg ######################################################################################

        # Log-Area
        if True:


            log_container_wdg = QtWidgets.QWidget(self)
            log_container_wdg.setLayout(QtWidgets.QVBoxLayout())
            log_container_wdg.setStyleSheet("QWidget {background-color: #FFFFFFFF;}")

            self.qtw_log_messages = QtWidgets.QTableView()
            self.qtw_log_messages.setFont(default_font_m)
            self.qtw_log_messages.setIconSize(QtCore.QSize(20, 20))
            self.qtw_log_messages.setAlternatingRowColors(True)
            #rows not resizable without header
            #self.qtw_log_messages.verticalHeader().hide()
            self.qtw_log_messages.setEditTriggers(self.qtw_log_messages.NoEditTriggers)
            self.qtw_log_messages.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
            self.qtw_log_messages.setFocusPolicy(QtCore.Qt.NoFocus)
            self.qtw_log_messages.setSortingEnabled(True)
            self.qtw_log_messages.horizontalHeader().setStretchLastSection(True)
            header_labels = [
                '#',
                'Time',
                'Level',
                'Message',
                'File',
                'Line',
                'Function'
            ]
            self.qtw_log_messages.setModel(QtGui.QStandardItemModel(0, 5))
            self.qtw_log_messages.model().setHorizontalHeaderLabels(header_labels)

            # time in column 1, in model stored as milliseconds since epoche
            self.log_delegate = MyDelegates.TimeDelegate()
            self.qtw_log_messages.setItemDelegateForColumn(1, self.log_delegate)

            log_container_wdg.layout().addWidget(self.qtw_log_messages)

            self.pbtn_check_log_messages = QtWidgets.QPushButton(self)
            self.pbtn_check_log_messages.setText(MY_DICT.tr('check_log_messages_pbtxt'))
            self.pbtn_check_log_messages.setIcon(QtGui.QIcon(':icons/Green_check_icon_with_gradient.svg'))
            log_container_wdg.layout().addWidget(self.pbtn_check_log_messages)

            self.pbtn_clear_log_messages = QtWidgets.QPushButton(self)
            self.pbtn_clear_log_messages.setText(MY_DICT.tr('clear_log_messages_pbtxt'))
            self.pbtn_clear_log_messages.setIcon(QtGui.QIcon(':icons/mActionRemove.svg'))
            log_container_wdg.layout().addWidget(self.pbtn_clear_log_messages)

            self.tbw_central.addTab(log_container_wdg, MY_DICT.tr('log_tab'))
            # end log_container_wdg

        self.tbw_central.setTabToolTip(0,MY_DICT.tr('stationing_tab_ttp'))
        self.tbw_central.setTabToolTip(1, MY_DICT.tr('feature_selection_tab_ttp'))
        self.tbw_central.setTabToolTip(2, MY_DICT.tr('post_processing_tab_ttp'))
        self.tbw_central.setTabToolTip(3, MY_DICT.tr('settings_tab_ttp'))
        self.tbw_central.setTabToolTip(4, MY_DICT.tr('log_tab_ttp'))

        main_wdg.layout().addWidget(self.tbw_central)

        # fake "statusbar" as separate widget
        # Note: self.setStatusBar() rsp. self.statusBar() only available for QMainWindow, not for dialogs
        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.setStyleSheet("QStatusBar {background-color: silver;}")
        self.status_bar.setFixedHeight(25)
        self.status_bar.setFont(default_font_s)

        # The QTimer object is made into a child of this object so that, when this object is deleted, the timer is deleted too
        self.status_bar_timer = QtCore.QTimer(self)

        # A single-shot timer fires only once, non-single-shot timers fire every interval milliseconds.
        self.status_bar_timer.setSingleShot(True)

        self.status_bar_timer.timeout.connect(self.reset_status_bar)


        self.pbtn_tool_mode_indicator = QtWidgets.QPushButton()
        self.pbtn_tool_mode_indicator.setFixedSize(18, 18)
        self.pbtn_tool_mode_indicator.setStyleSheet("QPushButton { border: none; }")
        self.pbtn_tool_mode_indicator.setIconSize(QtCore.QSize(18, 18))
        # Icon and Tooltip will be altered dynamically according to runtime_settings.tool_mode
        self.pbtn_tool_mode_indicator.setIcon(QtGui.QIcon(':icons/mActionOptions.svg'))
        self.pbtn_tool_mode_indicator.setToolTip(MY_DICT.tr('current_tool_mode_ttp'))

        self.status_bar.addPermanentWidget(self.pbtn_tool_mode_indicator, 0)
        main_wdg.layout().addWidget(self.status_bar)

        # pendant to setCentralWidget in QMainWindow
        self.setWidget(main_wdg)


    def reset_status_bar(self):
        """restore normal style, slot connected to self.status_bar_timer.timeout"""
        self.status_bar.clearMessage()
        self.status_bar.setStyleSheet("QStatusBar {background-color: silver;}")

    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """reimplemented and activated via self.installEventFilter(self)
        filters all signals for this dialog,
        used here for the special events LoLDialog - Close/WindowActivate/WindowDeactivate
        signal connected to slot inside LolEvt
        """
        # source == self not necessary
        if source == self and event.type() == QtCore.QEvent.Close:
            self.dialog_close.emit(True)
            return False
        if source == self and event.type() == QtCore.QEvent.WindowActivate:
            self.dialog_activated.emit(True)
            return False
        elif source == self and event.type() == QtCore.QEvent.WindowDeactivate:
            self.dialog_activated.emit(False)
            return False
        else:
            # debug_print("eventFilter",type(source),type(event))
            # delegate all other events to default-handler
            return super().eventFilter(source, event)



# for Tests outside QGis:
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = LolDialog(None)
    window.show()

    app.exec_()