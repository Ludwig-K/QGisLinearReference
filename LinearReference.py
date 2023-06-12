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
# Rev. 2023-04-21
import os, qgis, webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from LinearReferencing import tools, map_tools
from LinearReferencing.tools.MyDebugFunctions import get_debug_pos as gdp
from LinearReferencing.tools.MyDebugFunctions import debug_print

from LinearReferencing.icons import resources

class LinearReference(object):
    """container-object for this plugin, *must* contain some standard-functions, *can* contain much more..."""
    # Rev. 2023-04-21

    # basic settings: which actions and maptools should be available?
    install_LolEvt = True
    install_PolEvt = True
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

        # because __init__ is executed even if no project exists the initialization of mapTools must be delayed to take place as soon as an existing project is loaded
        qgis.core.QgsProject.instance().readProject.connect(self.read_project)

        # triggered *before* the project is saved to file
        qgis.core.QgsProject.instance().writeProject.connect(self.store_settings)

        # no further initialization, the mapTools are only created when they are needed


    def read_project(self):
        """delayed initialization of the mapTools as soon as an existing project is opened
        advantage:
        settings from the opened project are restored, checked and everything already prepared before the Plugin-Actions are triggered
        """
        # Rev. 2023-04-27

        if self.install_LolEvt:
            if not self.mt_LolEvt:
                self.mt_LolEvt = map_tools.LolEvt(self.iface)

            self.mt_LolEvt.restore_settings()
            self.mt_LolEvt.refresh_gui()



        if self.install_PolEvt:
            if not self.mt_PolEvt:
                self.mt_PolEvt = map_tools.PolEvt(self.iface)

            self.mt_PolEvt.restore_settings()
            self.mt_PolEvt.refresh_gui()


    def install_translator(self):
        """Find and load QtLinguist-File *.qm"""
        # Rev. 2023-04-21
        if QtCore.QSettings().value('locale/overrideFlag', type=bool):
            # locale in QGis-Settings perhaps different from system, default: 'en_US' (if overrideFlag is set but no userLocale defined)
            locale = QtCore.QSettings().value('locale/userLocale', 'en_US')
        else:
            locale = QtCore.QLocale.system().name()

        try:
            # search translation-file for locale
            # uses only first two chars, 'de_DE' 'de_AT' 'de_CH' 'de_BE' 'de_LI' ➜ 'de',
            plugin_dir = os.path.dirname(__file__)
            qm_path = os.path.join(plugin_dir, 'i18n', 'LinearReferencing_{}.qm'.format(locale[0:2]))
            if os.path.exists(qm_path):
                # store as Plugin-Property, else destroyd/garbage-collected and no translations :-(
                self.translator = QtCore.QTranslator()
                load_result = self.translator.load(qm_path)
                if load_result:
                    QtCore.QCoreApplication.installTranslator(self.translator)
                else:
                    raise Exception(f"Translator-File '{qm_path}' not loaded...")
            else:
                raise Exception(f"Translator-Datei '{qm_path}' not found...")
        except Exception as e:
            # only german translation partially implemented
            # print(f"Expected exception in {gdp()}: \"{e}\"")
            pass


    def tr(self, message: str) -> str:
        """ Wrapper for Qt-Translations outside from Qt-Objects"""
        # Rev. 2023-04-21
        return QtCore.QCoreApplication.translate(type(self).__name__, message)

    def initGui(self):
        """"standard-to_implement-function for plugins: adapt/extend GUI triggered by plugin-activation or project-open"""
        # Rev. 2023-04-21
        self.lref_toolbar = self.iface.addToolBar('LinearReferencingToolbar')
        self.lref_toolbar.setObjectName('LinearReferencingToolbar')
        self.lref_toolbar.setToolTip('LinearReferencing Toolbar')


        if self.install_PolEvt:
            ## PolEvt
            self.qact_PolEvt = QtWidgets.QAction(QtGui.QIcon(':icons/linear_referencing_point.svg'),"Measure and Digitize Point-on-Line Features",self.iface.mainWindow())
            self.qact_PolEvt.setCheckable(True)
            self.qact_PolEvt.triggered.connect(self.set_map_tool_PolEvt)
            self.qact_PolEvt.setEnabled(True)
            self.qact_PolEvt.setToolTip(self.tr("<b>LinearReferencing</b><hr>Measure and Digitize Point-on-Line Features"))
            self.lref_toolbar.addAction(self.qact_PolEvt)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_PolEvt)
            self.iface.mapToolActionGroup().addAction(self.qact_PolEvt)

        if self.install_LolEvt:
            self.qact_LolEvt = QtWidgets.QAction(QtGui.QIcon(':icons/linear_referencing.svg'),"Measure and Digitize Line-on-Line Features",self.iface.mainWindow())
            self.qact_LolEvt.setCheckable(True)
            self.qact_LolEvt.triggered.connect(self.set_map_tool_LolEvt)
            self.qact_LolEvt.setEnabled(True)
            self.qact_LolEvt.setToolTip(self.tr('<b>LinearReferencing</b><hr>Measure and Digitize Line-on-Line Features'))
            self.lref_toolbar.addAction(self.qact_LolEvt)
            self.iface.mapToolActionGroup().addAction(self.qact_LolEvt)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_LolEvt)

        if self.install_Help:
            self.qact_ShowHelp = QtWidgets.QAction(QtGui.QIcon(':icons/account-question-outline.svg'),"Show Help",self.iface.mainWindow())
            self.qact_ShowHelp.triggered.connect(self.show_help)
            self.lref_toolbar.addAction(self.qact_ShowHelp)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_ShowHelp)
            self.qact_ShowHelp.setToolTip(self.tr('<b>LinearReferencing</b><hr>Show Help'))


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

    # def set_map_tool_LolEvt(self, checked: bool) -> None:
    #     """set this MapTool for the canvas
    #     :param checked: Status of the checkable Action
    #     """
    #     # Rev. 2023-04-21
    #
    #     if checked:
    #         # already initialized if an existing project was opened
    #         if not self.mt_LolEvt:
    #             self.mt_LolEvt = map_tools.LolEvt(self.iface)
    #
    #         self.iface.mapCanvas().setMapTool(self.mt_LolEvt)
    #         if self.mt_LolEvt.my_dialogue.first_run:
    #             # if opened first time the 0/0-Standard-Window-Position can be problematic, even not visible, on MultiMonitors
    #             self.mt_LolEvt.my_dialogue.move(int(self.iface.mainWindow().x() + 0.7 * self.iface.mainWindow().width()), int(self.iface.mainWindow().y() + 0.2 * self.iface.mainWindow().height()))
    #             self.mt_LolEvt.my_dialogue.first_run = False
    #         self.mt_LolEvt.my_dialogue.show()
    #     else:
    #         self.mt_LolEvt.my_dialogue.hide()
    #         self.iface.actionPan().trigger()

    def set_map_tool_PolEvt(self) -> None:
        """set this MapTool for the canvas"""
        # Rev. 2023-04-21
        if not self.mt_PolEvt:
            self.mt_PolEvt = map_tools.PolEvt(self.iface)

        # restores a minimized or hidden (==closed) window
        if (QtCore.Qt.WindowMinimized & self.mt_PolEvt.my_dialogue.windowState()) or not self.mt_PolEvt.my_dialogue.isVisible():
            self.mt_PolEvt.my_dialogue.setWindowState(QtCore.Qt.WindowActive)

        self.iface.mapCanvas().setMapTool(self.mt_PolEvt)
        self.mt_PolEvt.refresh_gui()
        self.mt_PolEvt.my_dialogue.show()





    def set_map_tool_LolEvt(self) -> None:
        """set this MapTool for the canvas"""
        # Rev. 2023-04-21
        if not self.mt_LolEvt:
            self.mt_LolEvt = map_tools.LolEvt(self.iface)

        # restores a minimized or hidden (==closed) window
        if (QtCore.Qt.WindowMinimized & self.mt_LolEvt.my_dialogue.windowState())  or not self.mt_LolEvt.my_dialogue.isVisible():
            self.mt_LolEvt.my_dialogue.setWindowState(QtCore.Qt.WindowActive)
        self.iface.mapCanvas().setMapTool(self.mt_LolEvt)
        self.mt_LolEvt.refresh_gui()
        self.mt_LolEvt.my_dialogue.show()







