#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* Tools for measuring and digitizing Point-on-Line and Line-on-Line-Events

********************************************************************

* Date                 : 2023-08-21
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni-online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""


import os, qgis, webbrowser,typing
from PyQt5 import QtCore, QtGui, QtWidgets

from LinearReferencing.map_tools.PolEvt import PolEvt
from LinearReferencing.map_tools.LolEvt import LolEvt

# pyrcc5-compiled icons,
# path-like-addressable in all PyQt-scripts of this plugin
# f.e. the toolbar-icons
from LinearReferencing.icons import resources



from LinearReferencing.i18n.SQLiteDict import SQLiteDict
# global variable
MY_DICT = SQLiteDict()

class LinearReference(object):
    """container-object for this plugin, *must* contain some standard-functions, *can* contain much more..."""
    

    # basic settings: which actions and maptools should be available?
    install_PolEvt = True
    install_LolEvt = True
    install_Help = True



    # initialized map-Tools
    # dependend on install_PolEvt/install_LolEvt
    mt_LolEvt = None

    mt_PolEvt = None


    # actions which will show in and can be triggered by toolbar and menu
    # dependend on install_PolEvt/install_LolEvt/install_Help
    qact_LolEvt = None
    qact_PolEvt = None
    qact_ShowHelp = None


    def __init__(self, iface: qgis.gui.QgisInterface):
        """standard-to-implement-function for plugins, Constructor for the Plugin.
        Triggered
        a. on open QGis with activated plugin (even start QGis with blank project)
        b. on plugin-initialization
        Note: in case a: runs before any layer is loaded
        :param iface: interface to running QGis-App
        :type iface: qgis.gui.QgisInterface
        """
        self.iface = iface

    def initGui(self):
        """"standard-to-implement-function: adapt/extend GUI
        Triggered
        a. on open QGis with activated plugin (even start QGis with blank project)
        b. on plugin-initialization
        Note: in case a: runs before any layer is loaded"""
        



        # Toolbar for the three actions qact_PolEvt qact_LolEvt and qact_ShowHelp
        self.lref_toolbar = self.iface.addToolBar('LinearReferencingToolbar')
        self.lref_toolbar.setObjectName('LinearReferencingToolbar')
        self.lref_toolbar.setToolTip('LinearReferencing Toolbar')

        if self.install_PolEvt:
            self.qact_PolEvt = QtWidgets.QAction(QtGui.QIcon(':icons/linear_referencing_point.svg'),MY_DICT.tr('qact_PolEvt_qaction_text'),self.iface.mainWindow())
            self.qact_PolEvt.setCheckable(True)
            self.qact_PolEvt.triggered.connect(self.set_map_tool_PolEvt)
            self.qact_PolEvt.setEnabled(True)
            self.qact_PolEvt.setToolTip(MY_DICT.tr('qact_pol_ttp'))
            self.lref_toolbar.addAction(self.qact_PolEvt)
            # also in menubar
            self.iface.addPluginToMenu('LinearReferencing', self.qact_PolEvt)
            # and register inside mapToolActionGroup
            # only one mapTool can be activated at the same time
            # inside the mapToolActionGroup the QActions will be checked/unchecked automatically on change of MapTool
            self.iface.mapToolActionGroup().addAction(self.qact_PolEvt)

        if self.install_LolEvt:
            self.qact_LolEvt = QtWidgets.QAction(QtGui.QIcon(':icons/re_digitize_lol.svg'),MY_DICT.tr('qact_LolEvt_qaction_text'),self.iface.mainWindow())
            self.qact_LolEvt.setCheckable(True)
            self.qact_LolEvt.triggered.connect(self.set_map_tool_LolEvt)
            self.qact_LolEvt.setEnabled(True)
            self.qact_LolEvt.setToolTip(MY_DICT.tr('qact_lol_ttp'))
            self.lref_toolbar.addAction(self.qact_LolEvt)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_LolEvt)
            self.iface.mapToolActionGroup().addAction(self.qact_LolEvt)


        if self.install_Help:
            self.qact_ShowHelp = QtWidgets.QAction(QtGui.QIcon(':icons/plugin-help.svg'),MY_DICT.tr('qact_ShowHelp_qaction_text'),self.iface.mainWindow())
            self.qact_ShowHelp.triggered.connect(self.show_help)
            self.lref_toolbar.addAction(self.qact_ShowHelp)
            self.iface.addPluginToMenu('LinearReferencing', self.qact_ShowHelp)
            self.qact_ShowHelp.setToolTip(MY_DICT.tr('qact_show_help_ttp'))


    def unload(self):
        """standard-to_implement-function for each plugin:
        reset the GUI
        triggered by plugin-deactivation, project-close, QGis-Quit
        """
        

        # sys_unload-Function passed to the initialized MapTools
        # removes dialogs, temporal graphics, layer-signal-slot-connections etc.
        # possibly not everything necessary on QGis-Quit, because most (QgsVertexMarker/QgsRubberBand/signal-slot-connections...) not stored in QGis-Project
        if self.mt_PolEvt:
            self.mt_PolEvt.sys_unload()
            del self.mt_PolEvt
            # remove the Toolbar-Icons and Menu-Actions
            self.iface.removeToolBarIcon(self.qact_PolEvt)
            self.iface.removePluginMenu('LinearReferencing', self.qact_PolEvt)

        if self.mt_LolEvt:
            self.mt_LolEvt.sys_unload()
            del self.mt_LolEvt
            self.iface.removeToolBarIcon(self.qact_LolEvt)
            self.iface.removePluginMenu('LinearReferencing', self.qact_LolEvt)


        self.iface.removeToolBarIcon(self.qact_ShowHelp)
        self.iface.removePluginMenu('LinearReferencing', self.qact_ShowHelp)

        # activate a standard-MapTool "Pan"
        self.iface.actionPan().trigger()

        # remove toolbar
        # calling deleteLater() on the toolbar object schedules it for deletion and completely removes it also from the view -> toolbars menu
        if self.lref_toolbar:
            self.lref_toolbar.deleteLater()
            del self.lref_toolbar




    def show_help(self):
        """display local help, relative path: ./docs/index.de.html
        constructs and opens a local URL ala
        file:///home/user/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/docs/index.de.html
        """
        # os.path.dirname(__file__) => path of current file == Plugin-Directory inside QGis-profile-folder
        if QtCore.QSettings().value('locale/overrideFlag', type=bool):
            lcid = QtCore.QSettings().value('locale/userLocale', 'en_US')
        else:
            # take settings from system-locale, independent from current app
            lcid = QtCore.QLocale.system().name()

        # lcid is a string composed of language, underscore and country
        # for the translation the language is sufficient:
        # 'de_DE', 'de_AT', 'de_CH', 'de_BE', 'de_LI'... -> 'de'
        # 'en_US', 'en_GB'... -> 'en'
        lcid_language = lcid[0:2]


        if lcid_language == 'de':
            help_file_name = 'index.de.html'
        else:
            help_file_name = 'index.en.html'

        help_path = os.path.join(os.path.dirname(__file__), 'docs', help_file_name)


        url = QtCore.QUrl.fromLocalFile(help_path).toString()
        webbrowser.open(url, new=2)

    def set_map_tool_PolEvt(self) -> None:
        """initialize and set this MapTool for the canvas, triggered by click on Toolbar or Menu"""
        if not self.mt_PolEvt:
            self.mt_PolEvt = PolEvt(self.iface)
        self.iface.mapCanvas().setMapTool(self.mt_PolEvt)
        self.mt_PolEvt.my_dialog.show()
        self.mt_PolEvt.my_dialog.activateWindow()


    def set_map_tool_LolEvt(self) -> None:
        """initialize and set this MapTool for the canvas, triggered by click on Toolbar or Menu"""
        if not self.mt_LolEvt:
            self.mt_LolEvt = LolEvt(self.iface)
        self.iface.mapCanvas().setMapTool(self.mt_LolEvt)
        self.mt_LolEvt.my_dialog.show()
        self.mt_LolEvt.my_dialog.activateWindow()
