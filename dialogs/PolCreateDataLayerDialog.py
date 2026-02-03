#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* Qt-Dialog for Point-on-line-Features

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
import qgis, sys, os, osgeo
from osgeo import ogr
# else error
# /usr/lib/python3/dist-packages/osgeo/ogr.py:593: FutureWarning: Neither ogr.UseExceptions() nor ogr.DontUseExceptions() has been explicitly called. In GDAL 4.0, exceptions will be enabled by default.
ogr.UseExceptions()
from PyQt5 import QtCore, QtWidgets

from PyQt5.QtGui import(
    QIcon
)

from qgis.core import QgsProject


from LinearReferencing.qt.MyQtWidgets import (
    FlashingBorderQLineEdit,
    ClickableQLineEdit,
    QpbIco,
    FlashingQCheckBox
)

#get_debug_pos, get_debug_file_line, debug_print, debug_log
from LinearReferencing.tools.MyDebugFunctions import debug_print

from LinearReferencing.tools.MyTools import get_unique_string


from LinearReferencing.i18n.SQLiteDict import SQLiteDict

# global variable, translations de_DE and en_US
MY_DICT = SQLiteDict()


class PolCreateDataLayerDialog(QtWidgets.QDialog):
    """Dialog for QGis-Plugin LinearReferencing, Point-on-line-Features, dialog to create data-layer """
    # Rev. 2024-12-07



    def __init__(self, iface: qgis.gui.QgisInterface, parent=None):
        """Constructor
        :param iface: access to running QGis-Application
        :param parent: optional Qt-Parent-Element for Hierarchy
        """
        super().__init__(parent)

        # Result-Properties, parsed by PolEvt.dlg_show_create_data_lyr_dialog
        self.layer_type = None

        self.gpkg_path = None
        self.gpkg_layer_name = None
        self.overwrite_existing_layers = None

        self.memory_layer_name = None

        self.id_field_name = None
        self.reference_field_name = None
        self.stationing_field_name = None

        self.pre_check_ok = True
        self.pre_check_hint = None
        self.invalid_reason = None

        # Sub-Dialog with list of layers
        self.sub_dlg = None


        self.resize(600, 400)

        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.iface = iface
        self.setWindowTitle(MY_DICT.tr('CDL_Dlg_title'))

        self.setObjectName("PolCreateDataLayerDialog")


        self.setLayout(QtWidgets.QGridLayout())

        self.layout().setContentsMargins(10, 10, 10, 10)



        row = 0
        layer_qlbl = QtWidgets.QLabel("Layer:")
        self.layout().addWidget(layer_qlbl, row, 0)

        self.tbw_layer_type = QtWidgets.QTabWidget(self)

        self.tbw_layer_type.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        memory_layer_tab = QtWidgets.QWidget()
        memory_layer_tab.setLayout(QtWidgets.QGridLayout())
        sub_row = 0

        sub_row += 1
        self.memory_layer_name_qlbl = QtWidgets.QLabel(MY_DICT.tr('CDL_Dlg_gpkg_layer_name_lbl') )
        memory_layer_tab.layout().addWidget(self.memory_layer_name_qlbl, sub_row, 0)

        self.memory_layer_name_qle = FlashingBorderQLineEdit(self)
        self.memory_layer_name_qle.setToolTip(MY_DICT.tr('CDL_Dlg_memory_layer_name_ttp'))
        # default-name
        layer_names = [
            layer.name() for layer in QgsProject.instance().mapLayers().values()
        ]
        template = "PoL temp [{curr_i}]"
        memory_layer_name = get_unique_string(layer_names, template, 1)

        self.memory_layer_name_qle.setText(memory_layer_name)
        memory_layer_tab.layout().addWidget(self.memory_layer_name_qle, sub_row, 1)

        self.tbw_layer_type.addTab(memory_layer_tab,'Memory-Layer')

        gpkg_layer_tab = QtWidgets.QWidget()
        gpkg_layer_tab.setLayout(QtWidgets.QGridLayout())

        sub_row = 0
        gpkg_layer_tab.layout().addWidget(QtWidgets.QLabel(MY_DICT.tr('CDL_Dlg_gpkg_path_lbl')), sub_row, 0)

        self.gpkg_path_qle = ClickableQLineEdit(self)

        self.gpkg_path_qle.setReadOnly(True)
        self.gpkg_path_qle.setToolTip(MY_DICT.tr('CDL_Dlg_gpkg_path_ttp'))

        gpkg_layer_tab.layout().addWidget(self.gpkg_path_qle, sub_row, 1)

        self.call_file_dlg_qpb = QpbIco(
                '',
                MY_DICT.tr('CDL_Dlg_call_file_dlg_ttp'),
                QIcon(":icons/mActionFileOpen.svg")
            )
        # else will be triggered by any enter on the dialog
        self.call_file_dlg_qpb.setAutoDefault(False)
        gpkg_layer_tab.layout().addWidget(self.call_file_dlg_qpb, sub_row, 2)



        sub_row += 1
        self.gpkg_layer_name_qlbl = QtWidgets.QLabel(MY_DICT.tr('CDL_Dlg_gpkg_layer_name_lbl') )
        gpkg_layer_tab.layout().addWidget(self.gpkg_layer_name_qlbl, sub_row, 0)

        self.gpkg_layer_name_qle = FlashingBorderQLineEdit(self)
        self.gpkg_layer_name_qle.setToolTip(MY_DICT.tr('CDL_Dlg_gpkg_layer_name_ttp'))
        gpkg_layer_tab.layout().addWidget(self.gpkg_layer_name_qle, sub_row, 1)

        self.list_layers_qpb = QpbIco(
                '',
                MY_DICT.tr('CDL_Dlg_list_layers_ttp'),
                QIcon(":icons/show_gpkg_layers.svg")
            )
        # else will be triggered by any enter on the dialog
        self.list_layers_qpb.setAutoDefault(False)
        gpkg_layer_tab.layout().addWidget(self.list_layers_qpb, sub_row, 2)


        sub_row += 1
        self.overwrite_existing_layers_qlbl = QtWidgets.QLabel(MY_DICT.tr('CDL_Dlg_overwrite_layer_lbl'))
        gpkg_layer_tab.layout().addWidget(self.overwrite_existing_layers_qlbl, sub_row, 0)

        self.overwrite_existing_layers_qcbx = FlashingQCheckBox(self)
        self.overwrite_existing_layers_qcbx.setToolTip(MY_DICT.tr('CDL_Dlg_overwrite_layer_ttp'))
        gpkg_layer_tab.layout().addWidget(self.overwrite_existing_layers_qcbx, sub_row, 1)

        self.tbw_layer_type.addTab(gpkg_layer_tab,'GPKG-Layer')

        self.layout().addWidget(self.tbw_layer_type, row, 1)

        row += 1
        self.id_field_name_qlbl = QtWidgets.QLabel(MY_DICT.tr('CDL_Dlg_id_field_lbl'))
        self.layout().addWidget(self.id_field_name_qlbl, row, 0)

        self.id_field_name_qle = FlashingBorderQLineEdit(self)
        self.id_field_name_qle.setText(MY_DICT.tr('id_field_alias'))
        self.id_field_name_qle.setToolTip(MY_DICT.tr('CDL_Dlg_id_field_ttp'))
        self.layout().addWidget(self.id_field_name_qle, row, 1)

        row += 1
        self.reference_field_name_qlbl = QtWidgets.QLabel(MY_DICT.tr('CDL_Dlg_reference_field_lbl'))
        self.layout().addWidget(self.reference_field_name_qlbl, row, 0)

        self.reference_field_name_qle = FlashingBorderQLineEdit(self)
        self.reference_field_name_qle.setText(MY_DICT.tr('reference_id_field_alias'))
        self.reference_field_name_qle.setToolTip(MY_DICT.tr('CDL_Dlg_reference_field_ttp'))
        self.layout().addWidget(self.reference_field_name_qle, row, 1)

        row += 1
        self.stationing_field_name_qlbl = QtWidgets.QLabel(MY_DICT.tr('CDL_Dlg_stationing_field_lbl'))
        self.layout().addWidget(self.stationing_field_name_qlbl, row, 0)

        self.stationing_field_name_qle = FlashingBorderQLineEdit(self)
        self.stationing_field_name_qle.setText(MY_DICT.tr('stationing_field_alias'))
        self.stationing_field_name_qle.setToolTip(MY_DICT.tr('CDL_Dlg_stationing_field_ttp'))
        self.layout().addWidget(self.stationing_field_name_qle, row, 1)


        row += 1
        # Note: the dialog only pre-checks user-inputs, physical layer-creation is done by PoLEvt
        self.create_data_lyr_qpb = QtWidgets.QPushButton(MY_DICT.tr('CDL_Dlg_create_data_lyr_lbl'), self)

        # else will be triggered by any enter on the dialog
        self.create_data_lyr_qpb.setAutoDefault(False)

        self.layout().addWidget(self.create_data_lyr_qpb, row, 0,1,3)

        #self.layout().setRowStretch(row, 3)




        row += 1
        self.layout().setRowStretch(row, 3)

        row += 1
        self.pre_check_hint_qlbl = QtWidgets.QLabel()
        self.pre_check_hint_qlbl.setWordWrap(True)
        self.pre_check_hint_qlbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.pre_check_hint_qlbl.setStyleSheet("border-style: none; background-color: transparent; color: green;")
        self.pre_check_hint_qlbl.setVisible(False)
        self.layout().addWidget(self.pre_check_hint_qlbl, row, 0, 1, 3)

        row += 1
        self.invalid_reason_qlbl = QtWidgets.QLabel()
        self.invalid_reason_qlbl.setWordWrap(True)
        self.invalid_reason_qlbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.invalid_reason_qlbl.setStyleSheet("border-style: none; background-color: transparent; color: red;")
        self.invalid_reason_qlbl.setVisible(False)
        self.layout().addWidget(self.invalid_reason_qlbl, row, 0, 1, 3)


        row += 1
        # if layer already exists and not shall be overwritten import this layer to current project instead of creatin new one
        self.import_data_lyr_qpb = QtWidgets.QPushButton(MY_DICT.tr('CDL_Dlg_import_data_lyr_lbl'), self)

        # else will be triggered by any enter on the dialog
        self.import_data_lyr_qpb.setAutoDefault(False)
        self.import_data_lyr_qpb.setVisible(False)

        self.layout().addWidget(self.import_data_lyr_qpb, row, 0,1,3)

        self.gpkg_path_qle.pressed.connect(self.call_gpkg_path_dialog)
        self.call_file_dlg_qpb.pressed.connect(self.call_gpkg_path_dialog)
        self.list_layers_qpb.pressed.connect(self.list_layers)

        # Return or Enter key is pressed
        self.create_data_lyr_qpb.pressed.connect(self.check_user_inputs)

        self.import_data_lyr_qpb.pressed.connect(self.import_data_layer)

    def list_layers(self):
        """shows list of layers for selected GeoPackage in dialog-window"""
        # Rev. 2024-12-09
        gpkg_path = self.gpkg_path_qle.text()
        if gpkg_path != '':
            if os.path.isfile(gpkg_path):
                if not self.sub_dlg:
                    self.sub_dlg = QtWidgets.QDialog(self)
                    self.sub_dlg.resize(300, 300)
                    self.sub_dlg.setWindowTitle(MY_DICT.tr('CDL_Dlg_list_of_layers_title'))
                    self.sub_dlg.setObjectName("ListOfLayers")
                    self.sub_dlg.setLayout(QtWidgets.QVBoxLayout())

                    messages_qtxed = QtWidgets.QTextEdit()
                    messages_qtxed.setStyleSheet("border-style: none; background-color: white;")
                    messages_qtxed.setAcceptRichText(True)
                    messages_qtxed.setReadOnly(True)

                    self.sub_dlg.messages_qtxed = messages_qtxed
                    self.sub_dlg.layout().addWidget(messages_qtxed)

                self.sub_dlg.messages_qtxed.clear()
                message_text = MY_DICT.tr('CDL_Dlg_list_of_layers_header',gpkg_path)
                gpkg_layer_names = [lyr.GetName() for lyr in osgeo.ogr.Open(gpkg_path)]
                gpkg_layer_names.sort()
                for layer_name in gpkg_layer_names:
                    message_text += f'  - "{layer_name}"\n'

                self.sub_dlg.messages_qtxed.setText(message_text)

                self.sub_dlg.show()
                self.sub_dlg.activateWindow()
            else:
                self.pre_check_hint_qlbl.setText(MY_DICT.tr('CDL_Dlg_new_layer_hint',gpkg_path))
                self.pre_check_hint_qlbl.setVisible(True)
        else:
            self.invalid_reason_qlbl.setText(MY_DICT.tr('CDL_Dlg_select_layer_hint'))
            self.invalid_reason_qlbl.setVisible(True)
            self.gpkg_path_qle.start_flash()


    def import_data_layer(self):
        """alternatively import existing data-layer from selected GeoPackage"""
        gpkg_path = self.gpkg_path_qle.text()
        gpkg_layer_name = self.gpkg_layer_name_qle.text().strip()

        # get list of already used layer-names to check uniqueness of new layer-name
        if gpkg_path and os.path.isfile(gpkg_path):
            gpkg_layer_names = [lyr.GetName() for lyr in ogr.Open(gpkg_path)]
            if gpkg_layer_name and gpkg_layer_name in gpkg_layer_names:
                uri = gpkg_path + "|layername=" + gpkg_layer_name
                vl = self.iface.addVectorLayer(uri, gpkg_layer_name, "ogr")
                self.reject()



    def check_user_inputs(self):
        """parse user-inputs"""

        self.invalid_reason = None
        self.pre_check_hint = None
        self.pre_check_ok = True


        memory_layer_name = self.memory_layer_name_qle.text().strip()

        gpkg_path = self.gpkg_path_qle.text()
        gpkg_layer_name = self.gpkg_layer_name_qle.text().strip()
        overwrite_existing_layers = self.overwrite_existing_layers_qcbx.isChecked()
        id_field_name = self.id_field_name_qle.text().strip()
        reference_field_name = self.reference_field_name_qle.text().strip()
        stationing_field_name = self.stationing_field_name_qle.text().strip()



        if id_field_name != '':
            self.id_field_name = id_field_name
            if reference_field_name != '':
                if reference_field_name not in [id_field_name]:
                    self.reference_field_name = reference_field_name
                    if stationing_field_name != '':
                        if stationing_field_name not in [id_field_name,reference_field_name]:
                            self.stationing_field_name = stationing_field_name
                        else:
                            self.pre_check_ok = False
                            self.stationing_field_name_qle.start_flash()
                            self.invalid_reason = MY_DICT.tr('CDL_Dlg_field_name_not_unique_rejected_hint')
                    else:
                        self.pre_check_ok = False
                        self.stationing_field_name_qle.start_flash()
                        self.invalid_reason = MY_DICT.tr('CDL_Dlg_field_name_missing_rejected_hint')
                else:
                    self.pre_check_ok = False
                    self.reference_field_name_qle.start_flash()
                    self.invalid_reason = MY_DICT.tr('CDL_Dlg_field_name_not_unique_rejected_hint')
            else:
                self.pre_check_ok = False
                self.reference_field_name_qle.start_flash()
                self.invalid_reason = MY_DICT.tr('CDL_Dlg_field_name_missing_rejected_hint')
        else:
            self.pre_check_ok = False
            self.id_field_name_qle.start_flash()
            self.invalid_reason = MY_DICT.tr('CDL_Dlg_field_name_missing_rejected_hint')

        if self.pre_check_ok:
            if self.tbw_layer_type.currentIndex() == 0:
                self.layer_type = 'memory'
                # memory-layer
                if memory_layer_name != '':
                    self.memory_layer_name = memory_layer_name
                else:
                    self.invalid_reason = MY_DICT.tr('CDL_Dlg_memory_layer_name_missing_rejected_hint')
                    self.memory_layer_name_qle.start_flash()
                    self.pre_check_ok = False

            else:
                self.layer_type = 'gpkg'
                gpkg_layer_names = []
                if gpkg_path != '':
                    self.gpkg_path = gpkg_path

                    # get list of already used layer-names to check uniqueness of new layer-name
                    if os.path.isfile(gpkg_path):
                        gpkg_layer_names = [lyr.GetName() for lyr in ogr.Open(gpkg_path)]

                    # gpkg_layer_name must not start with "sqlite" and must not exist in selected gpkg
                    if gpkg_layer_name != '':
                        self.pre_check_ok = gpkg_layer_name.casefold().find('sqlite', 0, 6) != 0

                        if self.pre_check_ok:
                            if gpkg_layer_name in gpkg_layer_names:
                                self.import_data_lyr_qpb.setVisible(True)
                                if overwrite_existing_layers:
                                    self.pre_check_hint = MY_DICT.tr('CDL_Dlg_overwrite_layer_hint',gpkg_layer_name,gpkg_path)
                                else:
                                    self.invalid_reason = MY_DICT.tr('CDL_Dlg_overwrite_layer_rejected_hint',gpkg_layer_name,gpkg_path)
                                    self.overwrite_existing_layers_qcbx.start_flash()
                                    self.pre_check_ok = False

                        else:
                            self.pre_check_ok = False
                            self.invalid_reason = MY_DICT.tr('CDL_Dlg_sqlite_layer_rejected_hint',gpkg_layer_name)

                        if self.pre_check_ok:
                            self.gpkg_layer_name = gpkg_layer_name
                            self.gpkg_layer_name_qle.setText(gpkg_layer_name)

                    else:
                        self.pre_check_ok = False
                        self.gpkg_layer_name_qle.start_flash()
                        self.invalid_reason = MY_DICT.tr('CDL_Dlg_layer_name_missing_hint',gpkg_path)
                else:
                    self.pre_check_ok = False
                    self.gpkg_path_qle.start_flash()
                    self.invalid_reason = MY_DICT.tr('CDL_Dlg_gpkg_file_missing_hint')


        if self.pre_check_ok:
            # all user-inputs checked => accept (=> positive dialog-exec()-result) and let PoLEvt try to create the layer
            self.accept()

        if self.pre_check_hint:
            self.pre_check_hint_qlbl.setText(self.pre_check_hint)
            self.pre_check_hint_qlbl.setVisible(True)
        else:
            self.pre_check_hint_qlbl.clear()
            self.pre_check_hint_qlbl.setVisible(False)


        if self.invalid_reason:
            self.invalid_reason_qlbl.setText(self.invalid_reason)
            self.invalid_reason_qlbl.setVisible(True)
        else:
            self.invalid_reason_qlbl.clear()
            self.invalid_reason_qlbl.setVisible(False)


    def call_gpkg_path_dialog(self):
        """Sub-Dialog to select existing or to-create gpkg-file"""
        # Rev. 2024-12-07

        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, True)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setNameFilter("geoPackage (*.gpkg)")
        dialog.setWindowTitle(MY_DICT.tr('create_data_lyr'))
        dialog.setDefaultSuffix("gpkg")
        result = dialog.exec()
        if result and dialog.selectedFiles():
            gpkg_path = dialog.selectedFiles()[0]
            self.gpkg_path_qle.setText(gpkg_path)



# for Tests outside QGis:
if __name__ == "__main__":
    sys.path.append('C:/Users/ludwig.kniprath/AppData/Roaming/QGIS/QGIS3/profiles/2022-05-02/python/plugins/LinearReferencing')
    app = QtWidgets.QApplication(sys.argv)

    window = PolCreateDataLayerDialog(None)
    window.show()

    app.exec_()