#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* Qt-Dialog for Line-on-line-Features

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

import sys

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
    QTimer,
    QObject,
    QEvent,
    QSize
)

from PyQt5.QtGui import(
    QIcon,
    QFont,
    QPalette,
    QColor
)

from PyQt5.QtWidgets import(
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTabWidget,
    QGroupBox,
    QLabel,
    QStatusBar,
    QApplication,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QScrollArea,
    QTreeView,
    QAbstractItemView,
    QToolBar,
    QPushButton,
    QToolButton
)


from LinearReferencing.qt.MyQtWidgets import (
    MyPaddingLeftDelegate,
    QtbIco,
    MyFeatureSelectorQComboBox,
    MyLayerSelectorQComboBox,
    MyFieldSelectorQComboBox,
    QDoubleNoSpinBox,
    QDoubleSpinBoxDefault,
    HLine,
    QGroupBoxExpandable,
    MyLogTable,
    MyToolbarSpacer,
    QcbxToggleGridRows
)

# pyrcc5-compiled icons,
# path-like-addressable in all PyQt-scripts of this plugin
# f.e. the toolbar-icons below ':icons/....svg'
from LinearReferencing.icons import resources

from LinearReferencing.i18n.SQLiteDict import SQLiteDict

# global variable, translations de_DE and en_US
MY_DICT = SQLiteDict()


class LolDialog(QDockWidget):
    """Dialog for QGis-Plugin LinearReferencing, Line-on-line-Features
    note:
        QDockWidget -> dockable Window
        requires self.iface.addDockWidget(...) to be dockable within the MainWindow
    """

    # own signal, emitted by reimplemented eventFilter on dialog Close
    dialog_close = pyqtSignal(bool)

    # own signal, emitted by reimplemented eventFilter if the dialog gets focus
    dialog_activated = pyqtSignal(bool)

    def __init__(self, parent=None):
        """Constructor
        :param parent: optional Qt-Parent-Element for Hierarchy
        """

        QDockWidget.__init__(self, parent)



        self.setWindowTitle(MY_DICT.tr("LoL_dialog_title"))

        # needed for the reimplemented eventFilter which monitors the Close/WindowActivate/WindowDeActivate of this dialog
        self.installEventFilter(self)

        # to avoid ShutDown-Warning
        # Warning: QMainWindow::saveState(): 'objectName' not set for QDockWidget 0x55bc0824c790 'LinearReferencing: Point-on-Line;
        self.setObjectName("LoL-Dialog")


        # Application-Standard-Font
        base_font = QFont()

        # base_font = QFont("Arial")
        # base_font.setStyleHint(QFont.SansSerif)

        default_font_s = QFont(base_font)
        default_font_s.setPointSize(8)

        default_font_m = QFont(base_font)
        default_font_m.setPointSize(10)


        cbx_font_m = QFont(base_font)
        cbx_font_m.setPointSize(9)


        fixed_font = QFont("Monospace")
        fixed_font.setStyleHint(QFont.TypeWriter)
        fixed_font.setPixelSize(12)


        main_wdg = QWidget()
        main_wdg.setLayout(QVBoxLayout())

        # items in VBox:
        # 1. scrollable main content with QTabWidget Stationing/Edit/Settings
        # 2. status-bar
        main_wdg.layout().setContentsMargins(10, 10, 10, 0)



        # central widget with mutiple tabs
        self.tbw_central = QTabWidget(self)

        self.tbw_central.setTabPosition(QTabWidget.TabPosition.North)

        # Begin Measurement-Tab ######################################################################################
        if True:
            measurement_container_wdg = QWidget(self)
            measurement_container_wdg.setLayout(QVBoxLayout())
            measurement_container_wdg.setStyleSheet(
                "QWidget {background-color: #FFFFFFFF;}"
            )

            self.measurement_grb = QGroupBox(self)
            self.measurement_grb.setLayout(QGridLayout())
            row = 0

            self.measurement_grb.layout().addWidget(
                QLabel(MY_DICT.tr("ref_layer_lbl"), self), row, 0
            )

            # shows the currentl selected reference-layer and type
            self.qlbl_selected_ref_lyr = QLabel()
            self.measurement_grb.layout().addWidget(
                self.qlbl_selected_ref_lyr, row, 1, 1, 5
            )


            self.qtb_measurement_data_layer = QToolBar()
            self.qtb_measurement_data_layer.setIconSize(QSize(18,18))
            self.measurement_grb.layout().addWidget(self.qtb_measurement_data_layer, row, 5)

            row += 1

            self.measurement_grb.layout().addWidget(
                QLabel(MY_DICT.tr("ref_line_lbl"), self), row, 0
            )

            column_pre_settings = [
                # Spalte 0: Tree-Column
                {
                    "header": MY_DICT.tr("qcbn_reference_feature_pol_fid_hlbl"),
                    "font": fixed_font,
                },
                {
                    "header": MY_DICT.tr("qcbn_reference_feature_pol_name_hlbl"),
                    "alignment": Qt.AlignLeft,
                },
                {
                    "header": MY_DICT.tr("qcbn_reference_feature_pol_length_hlbl"),
                    "alignment": Qt.AlignRight,
                    "font": fixed_font,
                },
            ]

            self.qcbn_ref_lyr_select = MyFeatureSelectorQComboBox(
                self, column_pre_settings, "#{0} '{1}'", False
            )
            self.qcbn_ref_lyr_select.setToolTip(
                MY_DICT.tr("qcbn_reference_feature_ttp")
            )
            self.qcbn_ref_lyr_select.view_tool_tip = MY_DICT.tr(
                "qcbn_reference_feature_ttp"
            )
            self.qcbn_ref_lyr_select.setFont(cbx_font_m)

            self.measurement_grb.layout().addWidget(
                self.qcbn_ref_lyr_select, row, 1, 1, 4
            )


            self.qtb_measurement_reference_layer = QToolBar()
            self.qtb_measurement_reference_layer.setIconSize(QSize(18,18))
            self.measurement_grb.layout().addWidget(self.qtb_measurement_reference_layer, row, 5)


            row += 1
            self.measurement_grb.layout().addWidget(
                QLabel(MY_DICT.tr("canvas_x_y_lbl"), self), row, 0
            )

            self.dnspbx_canvas_x = QDoubleNoSpinBox(self)
            self.dnspbx_canvas_x.setToolTip(MY_DICT.tr("canvas_x_y_ttp"))
            self.measurement_grb.layout().addWidget(self.dnspbx_canvas_x, row, 1)

            self.dnspbx_canvas_y = QDoubleNoSpinBox(self)
            self.dnspbx_canvas_y.setToolTip(MY_DICT.tr("canvas_x_y_ttp"))
            self.measurement_grb.layout().addWidget(self.dnspbx_canvas_y, row, 2)

            sub_wdg = QWidget()
            sub_wdg.setLayout(QHBoxLayout())

            offset_lbl = QLabel(MY_DICT.tr("offset_lbl"), self)
            sub_wdg.layout().addWidget(offset_lbl)

            self.measurement_grb.layout().addWidget(sub_wdg, row, 3)

            self.dspbx_offset = QDoubleSpinBoxDefault(self)
            self.dspbx_offset.setToolTip(MY_DICT.tr("offset_ttp"))
            self.measurement_grb.layout().addWidget(self.dspbx_offset, row, 4)


            row += 1

            self.qtb_measurement_tools = QToolBar()
            self.qtb_measurement_tools.setIconSize(QSize(18,18))

            self.measurement_grb.layout().addWidget(
                self.qtb_measurement_tools, row, 1, 1, 5
            )

            # Insert or Edit Measurements
            if True:
                row += 1
                self.cbx_edit_grp = QcbxToggleGridRows(MY_DICT.tr("edit_grp_lbl"),MY_DICT.tr("edit_grp_ttp"),self.measurement_grb,row + 1,row + 2)
                self.measurement_grb.layout().addWidget(
                    self.cbx_edit_grp, row, 0, 1, 5
                )
                row += 1
                # self.qlbl_edit_data_feature = QLabel('')
                # self.qlbl_edit_data_feature.setAlignment(Qt.AlignCenter)
                # #self.qlbl_edit_data_feature.setStyleSheet("border: 1px solid silver; padding: 0px;")
                # self.qlbl_edit_data_feature.setToolTip(MY_DICT.tr("edit_data_fid_ttp"))
                # self.measurement_grb.layout().addWidget(self.qlbl_edit_data_feature, row, 1,1,3)


                self.qtb_edit_data_feature_post = QToolBar()
                self.qtb_edit_data_feature_post.setIconSize(QSize(18,18))
                self.measurement_grb.layout().addWidget(self.qtb_edit_data_feature_post, row,1,1,4)


            row += 1
            from_lbl = QLabel(MY_DICT.tr("from_lbl"), self)
            from_lbl.setStyleSheet("QLabel {color:green;}")
            self.measurement_grb.layout().addWidget(
                from_lbl, row, 1, 1, 2, Qt.AlignCenter
            )

            to_lbl = QLabel(MY_DICT.tr("to_lbl"), self)
            to_lbl.setStyleSheet("QLabel {color:red;}")

            self.measurement_grb.layout().addWidget(
                to_lbl, row, 3, 1, 2, Qt.AlignCenter
            )

            delta_lbl = QLabel(MY_DICT.tr("delta_lbl"), self)
            delta_lbl.setStyleSheet("QLabel {color:gray;}")

            self.measurement_grb.layout().addWidget(
                delta_lbl, row, 5, Qt.AlignCenter
            )

            row += 1
            self.measurement_grb.layout().addWidget(
                HLine(self, 2, "#00FF00"), row, 1, 1, 2
            )

            self.measurement_grb.layout().addWidget(
                HLine(self, 2, "#FF0000"), row, 3, 1, 2
            )


            self.measurement_grb.layout().addWidget(
                HLine(self, 2, "#aaaaaa"), row, 5
            )

            # N-abs-stationings
            if True:


                row += 1

                # N-abs-area with toggle-function
                self.cbx_n_abs_grp = QcbxToggleGridRows(MY_DICT.tr("n_abs_grp_lbl"),MY_DICT.tr("n_abs_grp_ttp"),self.measurement_grb,row + 1,row + 2)
                self.measurement_grb.layout().addWidget(
                    self.cbx_n_abs_grp, row, 0, 1, 5
                )

                row += 1
                self.dspbx_n_abs_from = QDoubleSpinBoxDefault(
                    self, 0, sys.float_info.max
                )
                self.measurement_grb.layout().addWidget(
                    self.dspbx_n_abs_from, row, 1,1,2
                )



                self.dspbx_n_abs_to = QDoubleSpinBoxDefault(
                    self, 0, sys.float_info.max
                )
                self.measurement_grb.layout().addWidget(
                    self.dspbx_n_abs_to, row, 3,1,2
                )

                self.dspbx_delta_n_abs = QDoubleSpinBoxDefault(self)
                self.measurement_grb.layout().addWidget(
                    self.dspbx_delta_n_abs, row, 5
                )
            # N-fract-stationings
            if True:

                row += 1

                self.cbx_n_fract_grp = QcbxToggleGridRows(MY_DICT.tr("n_fract_grp_lbl"),MY_DICT.tr("n_fract_grp_ttp"),self.measurement_grb,row + 1,row + 2)

                self.measurement_grb.layout().addWidget(
                    self.cbx_n_fract_grp, row, 0, 1, 5
                )

                row += 1

                self.dspbx_n_fract_from = QDoubleSpinBoxDefault(
                    self, 0, 100
                )
                self.measurement_grb.layout().addWidget(
                    self.dspbx_n_fract_from, row,1,1,2
                )

                self.dspbx_n_fract_to = QDoubleSpinBoxDefault(self, 0, 100)
                self.measurement_grb.layout().addWidget(
                    self.dspbx_n_fract_to, row, 3,1,2
                )


                # negativ if against digitize-direction
                self.dspbx_delta_n_fract = QDoubleSpinBoxDefault(
                    self, -100, 100
                )
                self.measurement_grb.layout().addWidget(
                    self.dspbx_delta_n_fract, row, 5
                )
            # M-abs-stationings
            if True:
                row += 1

                self.cbx_m_abs_grp = QcbxToggleGridRows(MY_DICT.tr("m_abs_grp_lbl"),MY_DICT.tr("m_abs_grp_ttp"),self.measurement_grb,row + 1,row + 3)
                self.measurement_grb.layout().addWidget(
                    self.cbx_m_abs_grp, row, 0, 1, 5
                )

                row += 1

                # m-value-range defined by geometry-vertex-m-values
                self.dspbx_m_abs_from = QDoubleSpinBoxDefault(self)
                self.measurement_grb.layout().addWidget(
                    self.dspbx_m_abs_from, row, 1, 1, 2
                )

                # m-value-range defined by geometry-vertex-m-values
                self.dspbx_m_abs_to = QDoubleSpinBoxDefault(self)
                self.measurement_grb.layout().addWidget(
                    self.dspbx_m_abs_to, row, 3, 1, 2
                )



                self.dspbx_delta_m_abs = QDoubleSpinBoxDefault(self)
                self.measurement_grb.layout().addWidget(
                    self.dspbx_delta_m_abs, row, 5
                )

                row += 1

                self.qlbl_m_valid_hint = QLabel(self)
                self.qlbl_m_valid_hint.setStyleSheet("color:red;")
                self.measurement_grb.layout().addWidget(
                    self.qlbl_m_valid_hint, row, 1, 1, 6
                )
            # M-fract-stationings
            if True:

                # hide/show if reference-layer is m-enabled
                row += 1

                self.cbx_m_fract_grp = QcbxToggleGridRows(MY_DICT.tr("m_fract_grp_lbl"),MY_DICT.tr("m_fract_grp_ttp"),self.measurement_grb,row + 1,row + 2)

                self.measurement_grb.layout().addWidget(
                    self.cbx_m_fract_grp, row, 0, 1, 5
                )
                row += 1

                self.dspbx_m_fract_from = QDoubleSpinBoxDefault(
                    self, 0, 100
                )
                self.measurement_grb.layout().addWidget(
                    self.dspbx_m_fract_from, row, 1, 1, 2
                )

                self.dspbx_m_fract_to = QDoubleSpinBoxDefault(self, 0, 100)
                self.measurement_grb.layout().addWidget(
                    self.dspbx_m_fract_to, row, 3, 1, 2
                )

                self.dspbx_delta_m_fract = QDoubleSpinBoxDefault(self)
                self.dspbx_delta_m_fract.setRange(-100, 100)
                self.measurement_grb.layout().addWidget(
                    self.dspbx_delta_m_fract, row, 5
                )
            # Z-values (elevation)
            if True:

                # hide/show if reference-layer is z-enabled
                row += 1

                self.cbx_z_grp = QcbxToggleGridRows(MY_DICT.tr("z_grp_lbl"),MY_DICT.tr("z_grp_ttp"),self.measurement_grb,row + 1,row + 2)

                self.measurement_grb.layout().addWidget(
                    self.cbx_z_grp, row, 0, 1, 5
                )

                row += 1

                self.dnspbx_z_from = QDoubleNoSpinBox(self)
                self.measurement_grb.layout().addWidget(self.dnspbx_z_from, row, 1, 1, 2)

                self.dnspbx_z_to = QDoubleNoSpinBox(self)
                self.measurement_grb.layout().addWidget(self.dnspbx_z_to, row, 3, 1, 2)

                self.dnspbx_delta_z_abs = QDoubleNoSpinBox(self)
                self.measurement_grb.layout().addWidget(
                    self.dnspbx_delta_z_abs, row, 5
                )
            # Snap-Coords-area with toggle-function
            if True:
                row += 1


                self.cbx_snap_coords_grp = QcbxToggleGridRows(MY_DICT.tr("snap_x_y_lbl"),'',self.measurement_grb,row + 1,row + 2)
                self.measurement_grb.layout().addWidget(
                    self.cbx_snap_coords_grp, row, 0, 1, 5
                )

                row += 1

                self.dnspbx_snap_x_from = QDoubleNoSpinBox(self)
                self.dnspbx_snap_x_from.setToolTip(MY_DICT.tr("snap_x_y_ttp"))
                self.measurement_grb.layout().addWidget(self.dnspbx_snap_x_from, row, 1)

                self.dnspbx_snap_y_from = QDoubleNoSpinBox(self)
                self.dnspbx_snap_y_from.setToolTip(MY_DICT.tr("snap_x_y_ttp"))
                self.measurement_grb.layout().addWidget(self.dnspbx_snap_y_from, row, 2)

                self.dnspbx_snap_x_to = QDoubleNoSpinBox(self)
                self.dnspbx_snap_x_to.setToolTip(MY_DICT.tr("snap_x_y_ttp"))
                self.measurement_grb.layout().addWidget(self.dnspbx_snap_x_to, row, 3)

                self.dnspbx_snap_y_to = QDoubleNoSpinBox(self)
                self.dnspbx_snap_y_to.setToolTip(MY_DICT.tr("snap_x_y_ttp"))
                self.measurement_grb.layout().addWidget(self.dnspbx_snap_y_to, row, 4)



            measurement_container_wdg.layout().addWidget(self.measurement_grb)


            # add a stretch below to push the contents to the top and not spread it vertically
            measurement_container_wdg.layout().addStretch(1)

            stationing_qsa = QScrollArea(self)
            stationing_qsa.setWidgetResizable(True)
            stationing_qsa.setStyleSheet("QScrollArea {border-style: none;}")
            stationing_qsa.setWidget(measurement_container_wdg)


            self.tbw_central.addTab(
                stationing_qsa, MY_DICT.tr("stationing_tab")
            )
            # End measurement_container_wdg ######################################################################################

        # Begin Feature-Selection-Tab ######################################################################################
        if True:

            feature_selection_wdg = QWidget(self)
            feature_selection_wdg.setLayout(QVBoxLayout())
            feature_selection_wdg.setStyleSheet(
                "QWidget {background-color: #FFFFFFFF;}"
            )

            self.qtb_feature_selection = QToolBar()
            self.qtb_feature_selection.setIconSize(QSize(18,18))
            self.qtb_feature_selection.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            feature_selection_wdg.layout().addWidget(self.qtb_feature_selection)

            self.qtrv_feature_selection = QTreeView()
            self.qtrv_feature_selection.setFont(fixed_font)
            self.qtrv_feature_selection.setAlternatingRowColors(True)
            self.qtrv_feature_selection.setIconSize(QSize(10, 10))
            self.qtrv_feature_selection.setUniformRowHeights(True)
            self.qtrv_feature_selection.setWordWrap(False)
            self.qtrv_feature_selection.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.qtrv_feature_selection.setSortingEnabled(True)


            # delegates padding the text-contents to the right side to get space for indexWidgets with function-icons
            # must be stored somewhere to avoid garbage-collection
            self.feature_selection_delegates = {}
            # column 0: remove-from-selection-icon
            self.feature_selection_delegates[0] = MyPaddingLeftDelegate(
                20
            )
            self.qtrv_feature_selection.setItemDelegateForColumn(0, self.feature_selection_delegates[0])

            self.feature_selection_delegates[1] = MyPaddingLeftDelegate(
                20
            )
            self.qtrv_feature_selection.setItemDelegateForColumn(1, self.feature_selection_delegates[1])


            pal = self.qtrv_feature_selection.palette()
            hightlight_brush = pal.brush(QPalette.Highlight)
            hightlight_brush.setColor(QColor("#AAFFF09D"))
            pal.setBrush(QPalette.Highlight, hightlight_brush)
            pal.setColor(QPalette.HighlightedText, QColor("#000000"))
            self.qtrv_feature_selection.setPalette(pal)
            self.qtrv_feature_selection.header().setStretchLastSection(True)

            feature_selection_wdg.layout().addWidget(self.qtrv_feature_selection)

            feature_selection_qsa = QScrollArea(self)
            feature_selection_qsa.setWidgetResizable(True)
            feature_selection_qsa.setStyleSheet("QScrollArea {border-style: none;}")
            feature_selection_qsa.setWidget(feature_selection_wdg)


            self.tbw_central.addTab(
                feature_selection_qsa, MY_DICT.tr("feature_selection_tab")
            )


        # PostProcessing-Tab
        if True:
            po_pro_container_wdg = QWidget(self)
            po_pro_container_wdg.setLayout(QVBoxLayout())
            po_pro_container_wdg.setStyleSheet("QWidget {background-color: #FFFFFFFF;}")

            qgb_po_pro_settings = QGroupBoxExpandable(
                MY_DICT.tr("qgb_po_pro_settings_ttl"), True, self
            )
            qgb_po_pro_settings.setLayout(QGridLayout())



            row = 0

            qgb_po_pro_settings.layout().addWidget(
                QLabel(MY_DICT.tr("pp_ref_lyr_lbl"), self), row, 0
            )
            column_pre_settings = [
                {"header": "Layer"},
                {"header": "Geometry"},
                {"header": "Provider"},
                {"header": "idx"},
            ]
            self.qcbn_pp_ref_lyr = MyLayerSelectorQComboBox(
                self, column_pre_settings, show_disabled=True
            )
            self.qcbn_pp_ref_lyr.setToolTip(MY_DICT.tr("pp_ref_lyr_ttp"))

            qgb_po_pro_settings.layout().addWidget(self.qcbn_pp_ref_lyr, row, 1)


            self.qtb_po_pro_settings = QToolBar()
            self.qtb_po_pro_settings.setIconSize(QSize(18,18))
            qgb_po_pro_settings.layout().addWidget(self.qtb_po_pro_settings, row, 2)


            row += 1

            qgb_po_pro_settings.layout().addWidget(
                QLabel(MY_DICT.tr("pp_ref_lyr_id_field_lbl"), self), row, 0
            )

            column_pre_settings = [
                {"header": "Field-Name"},
                {"header": "Field-Type"},
                {"header": "PK"},
                {"header": "Index"},
            ]
            self.qcbn_pp_ref_lyr_id_field = MyFieldSelectorQComboBox(
                self, column_pre_settings
            )
            self.qcbn_pp_ref_lyr_id_field.setToolTip(
                MY_DICT.tr("pp_ref_lyr_id_field_ttp")
            )

            qgb_po_pro_settings.layout().addWidget(
                self.qcbn_pp_ref_lyr_id_field, row, 1
            )


            row += 1




            po_pro_container_wdg.layout().addWidget(qgb_po_pro_settings)


            self.qtb_po_pro = QToolBar()
            self.qtb_po_pro.setIconSize(QSize(18,18))
            self.qtb_po_pro.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            po_pro_container_wdg.layout().addWidget(self.qtb_po_pro)

            # table to show the selected edit-features
            self.qtrv_po_pro_selection = QTreeView()

            self.qtrv_po_pro_selection.setFont(fixed_font)
            self.qtrv_po_pro_selection.setAlternatingRowColors(True)
            self.qtrv_po_pro_selection.setIconSize(QSize(10, 10))
            self.qtrv_po_pro_selection.setUniformRowHeights(True)
            self.qtrv_po_pro_selection.setWordWrap(False)
            self.qtrv_po_pro_selection.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.qtrv_po_pro_selection.setSortingEnabled(True)

            # delegates padding the text-contents to the right side to get space for indexWidgets with function-icons
            # must be stored somewhere to avoid garbage-collection
            self.po_pro_selection_delegates = {}
            # column 0: remove-from-selection-icon
            self.po_pro_selection_delegates[0] = MyPaddingLeftDelegate(
                20
            )
            self.qtrv_po_pro_selection.setItemDelegateForColumn(0, self.po_pro_selection_delegates[0])

            self.po_pro_selection_delegates[1] = MyPaddingLeftDelegate(
                20
            )
            self.qtrv_po_pro_selection.setItemDelegateForColumn(1, self.po_pro_selection_delegates[1])


            pal = self.qtrv_po_pro_selection.palette()
            hightlight_brush = pal.brush(QPalette.Highlight)
            hightlight_brush.setColor(QColor("#AAFFF09D"))
            pal.setBrush(QPalette.Highlight, hightlight_brush)
            pal.setColor(QPalette.HighlightedText, QColor("#000000"))
            self.qtrv_po_pro_selection.setPalette(pal)
            self.qtrv_po_pro_selection.header().setStretchLastSection(False)

            po_pro_container_wdg.layout().addWidget(self.qtrv_po_pro_selection)


            self.qtb_po_pro_edit = QToolBar()
            self.qtb_po_pro_edit.setIconSize(QSize(18,18))
            self.qtb_po_pro_edit.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            po_pro_container_wdg.layout().addWidget(self.qtb_po_pro_edit)


            self.tbw_central.addTab(po_pro_container_wdg, MY_DICT.tr('po_pro_tab'))



        # Start settings_container_wdg
        if True:

            settings_container_wdg = QWidget(self)
            settings_container_wdg.setLayout(QVBoxLayout())
            settings_container_wdg.setStyleSheet(
                "QWidget {background-color: #FFFFFFFF;}"
            )

            if True:
                layers_and_fields_grb = QGroupBoxExpandable(
                    MY_DICT.tr("layers_and_fields_gb_title"), True, self
                )
                layers_and_fields_grb.setLayout(QGridLayout())

                row = 0

                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("ref_lyr_lbl"), self), row, 0
                )
                column_pre_settings = [
                    {"header": "Layer"},
                    {"header": "Geometry"},
                    {"header": "Provider"},
                    {"header": "idx"},
                ]
                self.qcbn_ref_lyr = MyLayerSelectorQComboBox(
                    self, column_pre_settings, show_disabled=True
                )
                self.qcbn_ref_lyr.setToolTip(MY_DICT.tr("ref_lyr_ttp"))

                layers_and_fields_grb.layout().addWidget(self.qcbn_ref_lyr, row, 1)

                self.qtb_ref_layer_2 = QToolBar()
                self.qtb_ref_layer_2.setIconSize(QSize(18,18))
                layers_and_fields_grb.layout().addWidget(self.qtb_ref_layer_2, row, 2)



                row += 1

                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("ref_lyr_id_field_lbl"), self), row, 0
                )

                column_pre_settings = [
                    {"header": "Field-Name"},
                    {"header": "Field-Type"},
                    {"header": "PK"},
                    {"header": "Index"},
                ]
                self.qcbn_ref_lyr_id_field = MyFieldSelectorQComboBox(
                    self, column_pre_settings
                )
                self.qcbn_ref_lyr_id_field.setToolTip(
                    MY_DICT.tr("ref_lyr_id_field_ttp")
                )

                layers_and_fields_grb.layout().addWidget(
                    self.qcbn_ref_lyr_id_field, row, 1
                )

                row += 1

                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("data_lyr_lbl"), self), row, 0
                )

                column_pre_settings = [
                    {"header": "Layer"},
                    {"header": "Geometry"},
                    {"header": "Provider"},
                    {"header": "idx"},
                ]
                self.qcbn_data_lyr = MyLayerSelectorQComboBox(
                    self, column_pre_settings, show_disabled=True
                )
                self.qcbn_data_lyr.setToolTip(MY_DICT.tr("data_lyr_ttp"))
                layers_and_fields_grb.layout().addWidget(self.qcbn_data_lyr, row, 1)


                self.qtb_data_layer_2 = QToolBar()
                self.qtb_data_layer_2.setIconSize(QSize(18,18))
                layers_and_fields_grb.layout().addWidget(self.qtb_data_layer_2, row, 2)


                row += 1
                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("data_lyr_id_field_lbl"), self), row, 0
                )
                column_pre_settings = [
                    {"header": "Field-Name"},
                    {"header": "Field-Type"},
                    {"header": "PK"},
                    {"header": "Index"},
                ]
                self.qcbn_data_lyr_id_field = MyFieldSelectorQComboBox(
                    self, column_pre_settings
                )
                self.qcbn_data_lyr_id_field.setToolTip(
                    MY_DICT.tr("data_lyr_id_field_ttp")
                )
                layers_and_fields_grb.layout().addWidget(
                    self.qcbn_data_lyr_id_field, row, 1
                )

                row += 1

                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("data_lyr_reference_field_lbl"), self),
                    row,
                    0,
                )
                column_pre_settings = [
                    {"header": "Field-Name"},
                    {"header": "Field-Type"},
                    {"header": "PK"},
                    {"header": "Index"},
                ]
                self.qcbn_data_lyr_reference_field = (
                    MyFieldSelectorQComboBox(self, column_pre_settings)
                )
                self.qcbn_data_lyr_reference_field.setToolTip(
                    MY_DICT.tr("data_lyr_ref_field_ttp")
                )
                layers_and_fields_grb.layout().addWidget(
                    self.qcbn_data_lyr_reference_field, row, 1
                )

                row += 1

                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("data_lyr_offset_field_lbl"), self),
                    row,
                    0,
                )
                column_pre_settings = [
                    {"header": "Field-Name"},
                    {"header": "Field-Type"},
                    {"header": "PK"},
                    {"header": "Index"},
                ]
                self.qcbn_data_lyr_offset_field = MyFieldSelectorQComboBox(
                    self, column_pre_settings
                )
                self.qcbn_data_lyr_offset_field.setToolTip(
                    MY_DICT.tr("data_lyr_offset_field_ttp")
                )
                layers_and_fields_grb.layout().addWidget(
                    self.qcbn_data_lyr_offset_field, row, 1
                )

                row += 1

                layers_and_fields_grb.layout().addWidget(
                    QLabel(
                        MY_DICT.tr("data_lyr_stationing_from_field_lbl"), self
                    ),
                    row,
                    0,
                )
                column_pre_settings = [
                    {"header": "Field-Name"},
                    {"header": "Field-Type"},
                    {"header": "PK"},
                    {"header": "Index"},
                ]
                self.qcbn_data_lyr_stationing_from_field = (
                    MyFieldSelectorQComboBox(self, column_pre_settings)
                )
                self.qcbn_data_lyr_stationing_from_field.setToolTip(
                    MY_DICT.tr("data_lyr_stationing_field_ttp")
                )
                layers_and_fields_grb.layout().addWidget(
                    self.qcbn_data_lyr_stationing_from_field, row, 1
                )

                row += 1

                layers_and_fields_grb.layout().addWidget(
                    QLabel(
                        MY_DICT.tr("data_lyr_stationing_to_field_lbl"), self
                    ),
                    row,
                    0,
                )
                column_pre_settings = [
                    {"header": "Field-Name"},
                    {"header": "Field-Type"},
                    {"header": "PK"},
                    {"header": "Index"},
                ]
                self.qcbn_data_lyr_stationing_to_field = (
                    MyFieldSelectorQComboBox(self, column_pre_settings)
                )
                self.qcbn_data_lyr_stationing_to_field.setToolTip(
                    MY_DICT.tr("data_lyr_stationing_field_ttp")
                )
                layers_and_fields_grb.layout().addWidget(
                    self.qcbn_data_lyr_stationing_to_field, row, 1
                )

                row += 1
                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("lr_mode_lbl")), row, 0
                )

                self.qcb_lr_mode = QComboBox(self)
                self.qcb_lr_mode.setToolTip(MY_DICT.tr("lr_mode_ttp"))
                self.qcb_lr_mode.setFont(cbx_font_m)

                layers_and_fields_grb.layout().addWidget(self.qcb_lr_mode, row, 1)

                row += 1
                # new: storage-precision, avoid pi-like stationing 3.14159265359...
                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("storage_precision_lbl"), self), row, 0
                )
                self.qcb_storage_precision = QComboBox()
                self.qcb_storage_precision.setFont(cbx_font_m)
                self.qcb_storage_precision.setToolTip(
                    MY_DICT.tr("storage_precision_ttp")
                )
                layers_and_fields_grb.layout().addWidget(self.qcb_storage_precision, row, 1)

                # Show-Layer

                row += 1
                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("show_layer_lbl"), self), row, 0
                )
                column_pre_settings = [
                    {"header": "Layer"},
                    {"header": "Geometry"},
                    {"header": "Provider"},
                    {"header": "idx"},
                ]
                self.qcbn_show_lyr = MyLayerSelectorQComboBox(
                    self, column_pre_settings, show_disabled=True
                )
                self.qcbn_show_lyr.setToolTip(MY_DICT.tr("show_layer_ttp"))
                layers_and_fields_grb.layout().addWidget(self.qcbn_show_lyr, row, 1)

                self.qtb_show_layer = QToolBar()
                self.qtb_show_layer.setIconSize(QSize(18,18))
                layers_and_fields_grb.layout().addWidget(self.qtb_show_layer, row, 2)




                row += 1

                layers_and_fields_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("show_layer_back_reference_field_lbl")),
                    row,
                    0,
                )
                column_pre_settings = [
                    {"header": "Field-Name"},
                    {"header": "Field-Type"},
                    {"header": "PK"},
                    {"header": "Index"},
                ]
                self.qcbn_show_lyr_back_reference_field = (
                    MyFieldSelectorQComboBox(self, column_pre_settings)
                )
                self.qcbn_show_lyr_back_reference_field.setToolTip(
                    MY_DICT.tr("show_layer_back_reference_field_ttp")
                )

                layers_and_fields_grb.layout().addWidget(
                    self.qcbn_show_lyr_back_reference_field, row, 1
                )

                settings_container_wdg.layout().addWidget(layers_and_fields_grb)

            if True:
                # ============================================================
                misc_grb = QGroupBoxExpandable(
                    MY_DICT.tr("misc_grpbx"), False, self
                )
                misc_grb.setLayout(QGridLayout())

                row = 0

                # new: display-precision, avoid pi-like stationing 3.14159265359...
                misc_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("display_precision_lbl"), self), row, 0
                )
                self.qcb_display_precision = QComboBox()
                self.qcb_display_precision.setFont(cbx_font_m)
                self.qcb_display_precision.setToolTip(
                    MY_DICT.tr("display_precision_ttp")
                )
                misc_grb.layout().addWidget(self.qcb_display_precision, row, 1)

                row += 1
                qlbl_snap_mode = QLabel(MY_DICT.tr("snap_mode_lbl"))
                qlbl_snap_mode.setToolTip(MY_DICT.tr("snap_mode_container_ttp"))
                misc_grb.layout().addWidget(qlbl_snap_mode, row, 0)

                snap_mode_container_wdg = QWidget()
                snap_mode_container_wdg.setLayout(QVBoxLayout())

                self.cb_snap_mode_vertex = QCheckBox("Vertex")
                self.cb_snap_mode_vertex.setToolTip(MY_DICT.tr("snap_mode_vertex_ttp"))
                self.cb_snap_mode_vertex.setFont(cbx_font_m)
                snap_mode_container_wdg.layout().addWidget(self.cb_snap_mode_vertex)

                self.cb_snap_mode_segment = QCheckBox("Segment")
                self.cb_snap_mode_segment.setToolTip(
                    MY_DICT.tr("snap_mode_segment_ttp")
                )
                self.cb_snap_mode_segment.setFont(cbx_font_m)
                snap_mode_container_wdg.layout().addWidget(self.cb_snap_mode_segment)

                # Area and Centroid omitted for linestring-layer

                self.cb_snap_mode_middle_of_segment = QCheckBox(
                    "MiddleOfSegment"
                )
                self.cb_snap_mode_middle_of_segment.setToolTip(
                    MY_DICT.tr("snap_mode_middle_of_segment_ttp")
                )
                self.cb_snap_mode_middle_of_segment.setFont(cbx_font_m)
                snap_mode_container_wdg.layout().addWidget(
                    self.cb_snap_mode_middle_of_segment
                )

                # since QGIS 3.20
                self.cb_snap_mode_line_endpoint = QCheckBox("LineEndpoint")
                self.cb_snap_mode_line_endpoint.setToolTip(
                    MY_DICT.tr("snap_mode_line_endpoint")
                )
                self.cb_snap_mode_line_endpoint.setFont(cbx_font_m)
                snap_mode_container_wdg.layout().addWidget(
                    self.cb_snap_mode_line_endpoint
                )

                misc_grb.layout().addWidget(snap_mode_container_wdg, row, 1)

                row += 1
                # new: snap_distance
                misc_grb.layout().addWidget(
                    QLabel(MY_DICT.tr("snap_tolerance_lbl"), self), row, 0
                )
                self.qsb_snap_tolerance = QSpinBox(self)
                self.qsb_snap_tolerance.setRange(0, 1000)
                self.qsb_snap_tolerance.setFont(cbx_font_m)
                self.qsb_snap_tolerance.setToolTip(MY_DICT.tr("snap_tolerance_ttp"))
                misc_grb.layout().addWidget(self.qsb_snap_tolerance, row, 1)

                misc_grb.layout().addWidget(MyToolbarSpacer(), row, 2)

                settings_container_wdg.layout().addWidget(misc_grb)

            # add a stretch below to push the contents to the top and not spread it vertically
            settings_container_wdg.layout().addStretch(1)

            settings_qsa = QScrollArea(self)
            settings_qsa.setWidgetResizable(True)
            settings_qsa.setStyleSheet("QScrollArea {border-style: none;}")

            settings_qsa.setWidget(settings_container_wdg)

            self.tbw_central.addTab(settings_qsa, MY_DICT.tr("settings_tab"))

            # End settings_container_wdg ######################################################################################

        # Log-Area
        if True:

            log_container_wdg = QWidget(self)
            log_container_wdg.setLayout(QVBoxLayout())
            log_container_wdg.setStyleSheet("QWidget {background-color: #FFFFFFFF;}")

            self.qtw_log_messages = MyLogTable(self)
            self.qtw_log_messages.setFont(default_font_m)
            log_container_wdg.layout().addWidget(self.qtw_log_messages)

            self.qtb_log_container = QToolBar()
            self.qtb_log_container.setIconSize(QSize(18,18))
            self.qtb_log_container.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            log_container_wdg.layout().addWidget(self.qtb_log_container)



            self.tbw_central.addTab(log_container_wdg, MY_DICT.tr("log_tab"))
            # end log_container_wdg


        self.tbw_central.setTabToolTip(0, MY_DICT.tr("stationing_tab_ttp"))
        self.tbw_central.setTabToolTip(1, MY_DICT.tr("feature_selection_tab_ttp"))
        self.tbw_central.setTabToolTip(2, MY_DICT.tr('po_pro_tab_ttp'))
        self.tbw_central.setTabToolTip(3, MY_DICT.tr("settings_tab_ttp"))
        self.tbw_central.setTabToolTip(4, MY_DICT.tr("log_tab_ttp"))


        self.qwdg_tbw_corner = QWidget()
        self.qwdg_tbw_corner.setLayout(QHBoxLayout())
        self.qwdg_tbw_corner.layout().setAlignment(Qt.AlignRight)
        self.qwdg_tbw_corner.layout().setContentsMargins(0, 0, 0, 0)

        self.qtb_show_help = QToolButton(self)
        self.qtb_show_help.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.qtb_show_help.setIcon(QIcon(":icons/plugin-help.svg"))
        self.qtb_show_help.setToolTip('Show help')

        self.qwdg_tbw_corner.layout().addWidget(self.qtb_show_help)

        self.qtb_toggle_top_level = QToolButton(self)
        self.qtb_toggle_top_level.setCheckable(True)
        self.qtb_toggle_top_level.setChecked(False)
        self.qtb_toggle_top_level.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.qtb_toggle_top_level.setIcon(QIcon(":icons/mDockify.svg"))
        self.qtb_toggle_top_level.setToolTip('Dock/Undock window')
        self.qwdg_tbw_corner.layout().addWidget(self.qtb_toggle_top_level)


        self.tbw_central.setCornerWidget(self.qwdg_tbw_corner,corner = Qt.TopRightCorner)


        main_wdg.layout().addWidget(self.tbw_central)

        # fake "statusbar" as separate widget
        # Note: self.setStatusBar() rsp. self.statusBar() only available for QMainWindow, not for dialogs
        self.status_bar = QStatusBar(self)
        self.status_bar.setStyleSheet("QStatusBar {background-color: silver;}")
        self.status_bar.setFixedHeight(25)
        self.status_bar.setFont(default_font_s)

        # The QTimer object is made into a child of this object so that, when this object is deleted, the timer is deleted too
        self.status_bar_timer = QTimer(self)

        # A single-shot timer fires only once, non-single-shot timers fire every interval milliseconds.
        self.status_bar_timer.setSingleShot(True)

        self.status_bar_timer.timeout.connect(self.reset_status_bar)

        self.pbtn_tool_mode_indicator = QtbIco(
            QIcon(":icons/mActionOptions.svg"),
            MY_DICT.tr("current_tool_mode_ttp"),
            self,
        )
        self.status_bar.addPermanentWidget(self.pbtn_tool_mode_indicator, 0)
        main_wdg.layout().addWidget(self.status_bar)




        # pendant to setCentralWidget in QMainWindow
        self.setWidget(main_wdg)

    def reset_status_bar(self):
        """restore normal style, slot connected to self.status_bar_timer.timeout"""
        self.status_bar.clearMessage()
        self.status_bar.setStyleSheet("QStatusBar {background-color: silver;}")

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """reimplemented and activated via self.installEventFilter(self)
        filters all signals for this dialog,
        used here for the special events LoLDialog - Close/WindowActivate/WindowDeactivate
        signal connected to slot inside LolEvt
        """
        # source == self not necessary
        if source == self and event.type() == QEvent.Close:
            self.dialog_close.emit(True)
            return False
        if source == self and event.type() == QEvent.WindowActivate:
            self.dialog_activated.emit(True)
            return False
        elif source == self and event.type() == QEvent.WindowDeactivate:
            self.dialog_activated.emit(False)
            return False
        else:
            # debug_print("eventFilter",type(source),type(event))
            # delegate all other events to default-handler
            return super().eventFilter(source, event)


# for Tests outside QGis:
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LolDialog(None)
    window.show()

    app.exec_()
