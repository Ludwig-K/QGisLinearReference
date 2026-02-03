#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* Tools for measuring and digitizing Point-on-Line and Line-on-Line-Events

********************************************************************

* Date                 : 2026-01-13
* Copyright            : (C) 2026 by Ludwig Kniprath
* Email                : ludwig at kni-online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""

import qgis, webbrowser
from PyQt5.QtCore import QSettings, QLocale
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

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
    # Rev. 2026-01-13

    # basic settings: which actions and maptools should be available?
    install_PolEvt = True
    install_LolEvt = True
    install_Help = True

    def __init__(self, iface: qgis.gui.QgisInterface):
        """standard-to-implement-function for plugins, Constructor for the Plugin.
        Triggered
        a. on open QGis with activated plugin (even start QGis with blank project)
        b. on plugin-initialization
        Note: in case a: runs before any layer is loaded
        :param iface: interface to running QGis-App
        :type iface: qgis.gui.QgisInterface
        """
        # Rev. 2026-01-13

        self.iface = iface

        # Toolbar for the three actions qact_PolEvt qact_LolEvt and qact_ShowHelp
        self.lref_toolbar = self.iface.addToolBar("LinearReferencingToolbar")
        self.lref_toolbar.setObjectName("LinearReferencingToolbar")
        self.lref_toolbar.setToolTip("LinearReferencing Toolbar")

        # initialized map-Tools
        # dependend on install_PolEvt/install_LolEvt
        self.mt_LolEvt = None

        self.mt_PolEvt = None

        # actions which will show in and can be triggered by toolbar and menu
        # dependend on install_PolEvt/install_LolEvt/install_Help
        self.qact_LolEvt = None
        self.qact_PolEvt = None

        self.qact_ShowHelp = None


    def initGui(self):
        """ standard-to-implement-function: adapt/extend GUI
        Triggered
        a. on open QGis with activated plugin (even start QGis with blank project)
        b. on plugin-initialization
        Note: in case a: runs before any layer is loaded"""
        # Rev. 2026-01-13


        if self.install_PolEvt:
            self.qact_PolEvt = QAction(
                QIcon(":icons/linear_referencing_point.svg"),
                # text for menu
                MY_DICT.tr("qact_PolEvt_qaction_text"),
                self.iface.mainWindow(),
            )
            self.qact_PolEvt.triggered.connect(self.sys_init_PolEvt)
            self.qact_PolEvt.setEnabled(True)
            # ToolTip for Toolbar-Icon
            self.qact_PolEvt.setToolTip(MY_DICT.tr("qact_pol_ttp"))
            self.lref_toolbar.addAction(self.qact_PolEvt)
            # also in menubar
            self.iface.addPluginToMenu("LinearReferencing", self.qact_PolEvt)



        if self.install_LolEvt:
            self.qact_LolEvt = QAction(
                QIcon(":icons/re_digitize_lol.svg"),
                MY_DICT.tr("qact_LolEvt_qaction_text"),
                self.iface.mainWindow(),
            )
            self.qact_LolEvt.triggered.connect(self.sys_init_LolEvt)
            self.qact_LolEvt.setEnabled(True)
            self.qact_LolEvt.setToolTip(MY_DICT.tr("qact_lol_ttp"))
            self.lref_toolbar.addAction(self.qact_LolEvt)
            self.iface.addPluginToMenu("LinearReferencing", self.qact_LolEvt)



        if self.install_Help:
            self.qact_ShowHelp = QAction(
                QIcon(":icons/plugin-help.svg"),
                MY_DICT.tr("qact_ShowHelp_qaction_text"),
                self.iface.mainWindow(),
            )
            self.qact_ShowHelp.triggered.connect(self.show_help)
            self.lref_toolbar.addAction(self.qact_ShowHelp)
            self.iface.addPluginToMenu("LinearReferencing", self.qact_ShowHelp)
            self.qact_ShowHelp.setToolTip(MY_DICT.tr("qact_show_help_ttp"))

    def unload(self):
        """standard-to_implement-function for each plugin:
        reset the GUI
        triggered by plugin-deactivation, project-close, QGis-Quit
        """
        # Rev. 2026-01-13
        # reset GUI:
        if self.qact_PolEvt:
            self.iface.removeToolBarIcon(self.qact_PolEvt)
            self.iface.removePluginMenu("LinearReferencing", self.qact_PolEvt)


        if self.qact_LolEvt:
            self.iface.removeToolBarIcon(self.qact_LolEvt)
            self.iface.removePluginMenu("LinearReferencing", self.qact_LolEvt)


        if self.qact_ShowHelp:
            self.iface.removeToolBarIcon(self.qact_ShowHelp)
            self.iface.removePluginMenu("LinearReferencing", self.qact_ShowHelp)

        # remove toolbar
        # calling deleteLater() on the toolbar object schedules it for deletion and completely removes it also from the view -> toolbars menu
        if self.lref_toolbar:
            self.lref_toolbar.deleteLater()
            del self.lref_toolbar

        # sys_unload-Function passed to the initialized MapTools
        if self.mt_PolEvt:
            self.mt_PolEvt.sys_unload()
            del self.mt_PolEvt

        if self.mt_LolEvt:
            self.mt_LolEvt.sys_unload()
            del self.mt_LolEvt



    def sys_init_PolEvt(self) -> None:
        """initialize MapTool, triggered by click on Toolbar or Menu
        self.iface.mapCanvas().setMapTool(...) see PolEvt.sys_set_tool_mode"""
        # Rev. 2026-01-13
        if not self.mt_PolEvt:
            # init on first usage
            self.mt_PolEvt = PolEvt(self.iface)

        # show/raise dialog
        self.mt_PolEvt.dlg_show()


    def sys_init_LolEvt(self) -> None:
        """initialize MapTool if not existing
        show dialog
        set tool-mode, if reference-layer is registered
        """
        # Rev. 2026-01-13
        if not self.mt_LolEvt:
            # init on first usage
            self.mt_LolEvt = LolEvt(self.iface)

        # show/raise dialog
        self.mt_LolEvt.dlg_show()



    def show_help(self):
        """display help
        previous version used local documentation included in Plugin
        since version 2.0.1 no local helpfiles but use htmlpreview.github.io
        """
        # Rev. 2026-01-13

        # QLocale.system().name() is a string composed of language, underscore and country
        # for the translation the language is sufficient:
        # 'de_DE', 'de_AT', 'de_CH', 'de_BE', 'de_LI'... -> 'de'
        # 'en_US', 'en_GB'... -> 'en'

        release = "2.1.0"
        language = "en"
        if QLocale.system().name()[0:2] == "de":
            language = "de"

        url = f"http://kni-online.de/LinearReferencing/Release%20{release}/index.{language}.html"
        webbrowser.open_new_tab(url)


