#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* MapTool for digitizing Point-Events in MapCanvas
.. note::
    * added to data_layers and virtual-layers as action
    * accessible from tables and forms

********************************************************************

* Date                 : 2023-04-21
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni-online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""
# Rev. 2023-06-18

import os, qgis, webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from LinearReferencing import tools, map_tools
from LinearReferencing.tools.MyDebugFunctions import get_debug_pos as gdp
from LinearReferencing.tools.MyDebugFunctions import debug_print
from LinearReferencing.tools.MyToolFunctions import qt_format

from LinearReferencing.icons import resources

class LinearReference(object):
    """container-object for this plugin, *must* contain some standard-functions, *can* contain much more..."""
    # Rev. 2023-04-21

    # basic settings: which actions and maptools should be available?
    install_PolEvt = True
    install_LolEvt = True
    install_Help = True

    def __init__(self, iface: qgis.gui.QgisInterface):
        """standard-to-implement-function for plugins, Constructor for the Plugin.
        Triggered on *open QGis* ! (even start QGis with blank project!)
        :param iface: interface to running QGis-App
        :type iface: qgis.gui.QgisInterface
        """
        # Rev. 2023-04-21
        self.iface = iface
        self.install_translator()

        self.mt_LolEvt = None
        self.mt_PolEvt = None

        self.qact_LolEvt = None
        self.qact_PolEvt = None

        self.qact_ShowHelp = None

        # connect some signals in project to register TOC-changes (especially layersRemoved)
        qgis.core.QgsProject.instance().layersAdded.connect(self.recheck_settings)
        qgis.core.QgsProject.instance().layersRemoved.connect(self.recheck_settings)

        # triggered *before* the project is saved to file
        qgis.core.QgsProject.instance().writeProject.connect(self.store_settings)

        # no further initialization, the mapTools are only created when they are needed


    def install_translator(self):
        """Find and load compiled QtLinguist-File *.qm"""
        # Rev. 2023-04-21
        if QtCore.QSettings().value('locale/overrideFlag', type=bool):
            # locale in QGis-Settings perhaps different from system, default: 'en_US' (if overrideFlag is set but no userLocale defined)
            locale = QtCore.QSettings().value('locale/userLocale', 'en_US')
        else:
            locale = QtCore.QLocale.system().name()

        try:
            # search translation-file for locale
            # use only first two chars, 'de_DE' 'de_AT' 'de_CH' 'de_BE' 'de_LI' ➜ 'de', en_US ➜ en
            plugin_dir = os.path.dirname(__file__)
            qm_path = os.path.join(plugin_dir, 'i18n', f"LinearReferencing_{locale[0:2]}.qm")
            if os.path.exists(qm_path):
                # must be stored as property, else destroyd/garbage-collected and no translations :-(
                self.translator = QtCore.QTranslator()
                load_result = self.translator.load(qm_path)
                if load_result:
                    QtCore.QCoreApplication.installTranslator(self.translator)
                else:
                    # raise Exception(f"Translator-File '{qm_path}' not loaded...")
                    pass
            else:
                # raise Exception(f"Translator-Datei '{qm_path}' not found...")
                pass
        except Exception as e:
            # print(f"Expected exception in {gdp()}: \"{e}\"")
            pass


    # def tr(self, message: str) -> str:
    #     """ Wrapper for Qt-Translations outside from Qt-Objects"""
    #     # Rev. 2023-04-21
    #     return QtCore.QCoreApplication.translate(type(self).__name__, message)

    def initGui(self):
        """"standard-to_implement-function for plugins: adapt/extend GUI triggered by plugin-activation or project-open"""
        # Rev. 2023-04-21
        self.lref_toolbar = self.iface.addToolBar('LinearReferencingToolbar')
        self.lref_toolbar.setObjectName('LinearReferencingToolbar')
        self.lref_toolbar.setToolTip('LinearReferencing Toolbar')

        # some markup-wildcards for pylupdate5/lsrelease/QtCore.QCoreApplication.translate
        hr = "<hr />"
        b1 = "<b>"
        b2 = "</b>"

        if self.install_PolEvt:
            ## PolEvt
            self.qact_PolEvt = QtWidgets.QAction(QtGui.QIcon(':icons/linear_referencing_point.svg'),QtCore.QCoreApplication.translate('LinearReference',"Measure and Digitize Point-on-Line Features"),self.iface.mainWindow())
            self.qact_PolEvt.setCheckable(True)
            self.qact_PolEvt.triggered.connect(self.set_map_tool_PolEvt)
            self.qact_PolEvt.setEnabled(True)
            self.qact_PolEvt.setToolTip(qt_format(QtCore.QCoreApplication.translate('LinearReference',"{b1}LinearReferencing{b2}{hr}Measure and Digitize Point-on-Line Features")))
            self.lref_toolbar.addAction(self.qact_PolEvt)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_PolEvt)
            self.iface.mapToolActionGroup().addAction(self.qact_PolEvt)

        if self.install_LolEvt:
            self.qact_LolEvt = QtWidgets.QAction(QtGui.QIcon(':icons/linear_referencing.svg'),QtCore.QCoreApplication.translate('LinearReference',"Measure and Digitize Line-on-Line Features"),self.iface.mainWindow())
            self.qact_LolEvt.setCheckable(True)
            self.qact_LolEvt.triggered.connect(self.set_map_tool_LolEvt)
            self.qact_LolEvt.setEnabled(True)
            self.qact_LolEvt.setToolTip(qt_format(QtCore.QCoreApplication.translate('LinearReference','{b1}LinearReferencing{b2}{hr}Measure and Digitize Line-on-Line Features')))
            self.lref_toolbar.addAction(self.qact_LolEvt)
            self.iface.mapToolActionGroup().addAction(self.qact_LolEvt)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_LolEvt)

        if self.install_Help:
            self.qact_ShowHelp = QtWidgets.QAction(QtGui.QIcon(':icons/account-question-outline.svg'),QtCore.QCoreApplication.translate('LinearReference',"Show Help"),self.iface.mainWindow())
            self.qact_ShowHelp.triggered.connect(self.show_help)
            self.lref_toolbar.addAction(self.qact_ShowHelp)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_ShowHelp)
            self.qact_ShowHelp.setToolTip(qt_format(QtCore.QCoreApplication.translate('LinearReference','{b1}LinearReferencing{b2}{hr}Show Help')))


    def recheck_settings(self, layers):
        """refresh settings/dialogs of theMapTools after layer-adds or deletes"""
        # Rev. 2023-04-21
        if self.mt_PolEvt:
            self.mt_PolEvt.refresh_gui()

        if self.mt_LolEvt:
           self.mt_LolEvt.refresh_gui()

    def store_settings(self):
        """write the current ss (stored_settings) to disk on project save"""
        # Rev. 2023-05-25
        if self.mt_PolEvt:
            self.mt_PolEvt.store_settings()

        if self.mt_LolEvt:
           self.mt_LolEvt.store_settings()


    def unload(self):
        """standard-to_implement-function for plugins: reset GUI
        triggered by plugin-deactivation or project-close (!)"""
        # Rev. 2023-04-21
        # call unload-Function of the initialized map_tools
        if self.mt_PolEvt:
            self.mt_PolEvt.unload()

        if self.mt_LolEvt:
            self.mt_LolEvt.unload()

        # allways remove layer-actions, also if the MapTools was not initialized
        for cl in qgis.core.QgsProject.instance().mapLayers().values():
            if cl.type() == qgis.core.QgsMapLayerType.VectorLayer:
                action_list = [action for action in cl.actions().actions() if action.id() in [map_tools.PolEvt._lyr_act_id_1, map_tools.PolEvt._lyr_act_id_2,map_tools.LolEvt._lyr_act_id_1, map_tools.LolEvt._lyr_act_id_2]]
                for action in action_list:
                    cl.actions().removeAction(action.id())

        self.iface.removeToolBarIcon(self.qact_PolEvt)
        self.iface.removePluginMenu('LinearReferencing', self.qact_PolEvt)

        self.iface.removeToolBarIcon(self.qact_LolEvt)
        self.iface.removePluginMenu('LinearReferencing', self.qact_LolEvt)

        self.iface.removeToolBarIcon(self.qact_ShowHelp)
        self.iface.removePluginMenu('LinearReferencing', self.qact_ShowHelp)

        self.iface.actionPan().trigger()

        # remove toolbar
        # calling deleteLater() on the toolbar object schedules it for deletion and
        # completely removes it also from the view -> toolbars menu
        self.lref_toolbar.deleteLater()
        del self.lref_toolbar

        # this should not be necessary, cause signal-slot connections are disconnected, if the slot-function (Python-Functions are objects with destructors) is unloaded (except lambda-Functions)
        # But it should not harm...
        try:
            qgis.core.QgsProject.instance().layersAdded.disconnect(self.recheck_settings)
            qgis.core.QgsProject.instance().layersRemoved.disconnect(self.recheck_settings)
        except Exception as e:
            # TypeError: 'method' object is not connected
            # print(f"Expected exception in {gdp()}: \"{e}\"")
            pass

    def show_help(self):
        """display local help ./docs/index.html"""
        # Rev. 2023-04-21
        url = QtCore.QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), 'docs', 'index.html')).toString()
        webbrowser.open(url, new=2)

    def set_map_tool_PolEvt(self) -> None:
        """set this MapTool for the canvas, triggered by click on Toolbar or Menu"""
        # Rev. 2023-04-21
        # only create if necessary => first call
        if not self.mt_PolEvt:
            self.mt_PolEvt = map_tools.PolEvt(self.iface)

        # restores a minimized or hidden (==closed) window
        if (QtCore.Qt.WindowMinimized & self.mt_PolEvt.my_dialogue.windowState()) or not self.mt_PolEvt.my_dialogue.isVisible():
            self.mt_PolEvt.my_dialogue.setWindowState(QtCore.Qt.WindowActive)

        self.iface.mapCanvas().setMapTool(self.mt_PolEvt)
        self.mt_PolEvt.refresh_gui()
        self.mt_PolEvt.my_dialogue.show()


    def set_map_tool_LolEvt(self) -> None:
        """set this MapTool for the canvas, triggered by click on Toolbar or Menu"""
        # Rev. 2023-04-21
        if not self.mt_LolEvt:
            self.mt_LolEvt = map_tools.LolEvt(self.iface)

        # restores a minimized or hidden (==closed) window
        if (QtCore.Qt.WindowMinimized & self.mt_LolEvt.my_dialogue.windowState())  or not self.mt_LolEvt.my_dialogue.isVisible():
            self.mt_LolEvt.my_dialogue.setWindowState(QtCore.Qt.WindowActive)
        self.iface.mapCanvas().setMapTool(self.mt_LolEvt)
        self.mt_LolEvt.refresh_gui()
        self.mt_LolEvt.my_dialogue.show()
