# -----------------------------------------------------------
# Copyright (C) 2022 Ludwig Kniprath
# -----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# ---------------------------------------------------------------------

import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import QSettings, QUrl, pyqtSlot, QVariant

from PyQt5.QtCore import QTranslator, QCoreApplication, QLocale
from qgis.core import QgsProject

from .DigitizeLineEvent import DigitizeLineEvent
from .DigitizePointEvent import DigitizePointEvent
from .MyToolFunctions import get_linestring_layers


class LinearReferencePlugin:
    '''Container-Objekt mit den Hauptfunktionen des Plugins, wird in __init__.py von classFactory() zurückgeliefert '''

    def __init__(self, iface):
        '''Constructor.
        :param iface: Laufzeit-Schnittstelle zum QGis-Programm
        :type iface: QgsInterface
        '''
        self.iface = iface

        # zwei dictionaries mit identischen keys
        self.map_tools = {}
        self.actions = {}

        # Grundeinstellung aller Texte/Meldungen... "en_US", Übersetzungsdatei für "de" und "fr"
        # Spracheinstellung rausfinden
        if QSettings().value('locale/overrideFlag', type=bool):
            # locale in QGis-Settings abweichend vom System definiert?
            locale = QSettings().value('locale/userLocale')
        else:
            # andernfalls Systemeinstellung
            locale = QLocale.system().name()

        # passende Übersetzungsdatei laden
        # verwendet nur die ersten beiden Zeichen von locale, 'de_DE' 'de_AT' 'de_CH' 'de_BE' 'de_LI' => 'de',
        ts_path = os.path.join(os.path.dirname(__file__), 'i18n', 'LinearReferencing_{}.qm'.format(locale[0:2]))
        if os.path.exists(ts_path):
            # als Objekteigenschaft speichern
            self.translator = QTranslator()
            load_result = self.translator.load(ts_path)
            if load_result:
                QCoreApplication.installTranslator(self.translator)
            else:
                # raise Exception("Translator-Datei '{}' nicht geladen...".format(ts_path))
                pass
        else:
            # raise Exception("Translator-Datei '{}' nicht vorhanden...".format(ts_path))
            pass

        QgsProject.instance().layersAdded.connect(self.slot_refresh_dialogs)
        QgsProject.instance().layersRemoved.connect(self.slot_refresh_dialogs)

    def tr(self, message: str) -> str:
        '''innerhalb von Qt liefert QObject.tr() die Übersetzung
        Workaround und zudem verwendbar ohne Qt-Objekt: eigene Implementierung
        Hinweis: falls die Übersetzungsdatei für die aktuelle locale "LinearReferencing_{XY}.qm" nicht vorlag
        oder nicht geladen werden konnte wird der Originaltext zurückgeliefert
        :param context_name: greift auf Kapitel <context><name>...</name> zu
        :param message: String for translation.
        '''
        return QCoreApplication.translate('LinearReferencing', message)

    def initGui(self):
        '''Anpassung des GUI, Standardfunktion eines Plugins'''
        self.actions['DigitizeLineEvent'] = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), 'icons/linear_referencing.svg')),
            self.tr('digitize line_on_line-events'),
            self.iface.mainWindow())
        self.actions['DigitizeLineEvent'].setCheckable(True)
        self.actions['DigitizeLineEvent'].triggered.connect(lambda: self.set_map_tool('DigitizeLineEvent'))
        # Toolbar-Icoon für diese action
        self.iface.addToolBarIcon(self.actions['DigitizeLineEvent'])
        # und Menüeintrag
        self.iface.addPluginToMenu('LinearReferencing', self.actions['DigitizeLineEvent'])

        self.actions['DigitizePointEvent'] = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), 'icons/linear_referencing_point.svg')),
            self.tr('digitize point_on_line-events'),
            self.iface.mainWindow())
        self.actions['DigitizePointEvent'].setCheckable(True)
        self.actions['DigitizePointEvent'].triggered.connect(lambda: self.set_map_tool('DigitizePointEvent'))
        # Toolbar-Icoon für diese action
        self.iface.addToolBarIcon(self.actions['DigitizePointEvent'])
        # und Menüeintrag
        self.iface.addPluginToMenu('LinearReferencing', self.actions['DigitizePointEvent'])

        self.actions['ShowHelp'] = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), 'icons/account-question-outline.svg')),
            self.tr('Show Help'),
            self.iface.mainWindow())

        self.actions['ShowHelp'].triggered.connect(self.show_help)

        self.iface.addPluginToMenu('LinearReferencing', self.actions['ShowHelp'])

        # Aufruf bei Wechsel des MapTools
        self.iface.mapCanvas().mapToolSet.connect(self.reset_tool)

    def unload(self):
        '''GUI zurücksetzen beim Unload des Plugins, Standardfunktion eines Plugins'''
        # Elemente eines dictionaries direkt löschen => RuntimeError: dictionary changed size during iteration
        for map_tool_key in self.actions.copy():
            current_action = self.actions[map_tool_key]
            # current_map_tool = self.map_tools[map_tool_key]
            self.iface.removeToolBarIcon(current_action)
            self.iface.removePluginMenu('LinearReferencing', current_action)
            del self.actions[map_tool_key]

        for map_tool_key in self.map_tools.copy():
            # muss im map_tool implementiert sein, löscht dort z. B. die temporären Punkt/Liniengrafiken
            self.map_tools[map_tool_key].unload()
            del self.map_tools[map_tool_key]

    def show_help(self):
        '''lokale Hilfeseitec/docs/index.html öffnen'''
        import webbrowser
        url = QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), 'docs', 'index.html')).toString()
        webbrowser.open(url, new=2)

    # @pyqtSlot mit irgendeiner Signatur funzt nicht, "TypeError: decorated slot has no signature compatible with layersAdded(QList)", geht aber auch ohne...
    def slot_refresh_dialogs(self, layers):
        '''registriert Zu/Abgänge bei den Layern und aktualisiert die Dialoge'''
        linestring_layers = get_linestring_layers(self.iface)
        if len(linestring_layers) < 1:
            self.iface.messageBar().pushMessage(self.tr('LinearReferencing'),
                                                self.tr("no suitable reference-layer (type linestring) found!")
                                                )
            for key in self.actions:
                self.actions[key].setChecked(False)

        for key in self.map_tools:
            self.map_tools[key].refresh_qcb_reference_layer()

    def set_map_tool(self, map_tool_key: str) -> None:
        '''MapTool bei Bedarf generieren und setzen
        :param map_tool_key: das zu aktivierende map_tool dieses Plugins
        '''

        linestring_layers = get_linestring_layers(self.iface)
        if len(linestring_layers) > 0:

            # alle actions dieses Plugins (derzeit genau eines...) vorab deaktivieren
            for key in self.actions:
                self.actions[key].setChecked(False)

            current_map_tool = None

            if map_tool_key == 'DigitizePointEvent':

                if 'DigitizePointEvent' in self.map_tools:
                    current_map_tool = self.map_tools['DigitizePointEvent']
                else:
                    current_map_tool = DigitizePointEvent(self.iface)
                    self.map_tools['DigitizePointEvent'] = current_map_tool

                current_map_tool.refresh_qcb_reference_layer()
                current_map_tool.dialogue.show()
                current_map_tool.set_layer()

                if current_map_tool.ref_line_layer is not None:
                    # setMapTool => Sets the map tool currently being used on the canvas
                    self.iface.mapCanvas().setMapTool(current_map_tool)
                    self.actions[map_tool_key].setChecked(True)

            elif map_tool_key == 'DigitizeLineEvent':

                if 'DigitizeLineEvent' in self.map_tools:
                    current_map_tool = self.map_tools['DigitizeLineEvent']
                else:
                    current_map_tool = DigitizeLineEvent(self.iface)
                    self.map_tools['DigitizeLineEvent'] = current_map_tool

                current_map_tool.refresh_qcb_reference_layer()
                current_map_tool.dialogue.show()
                current_map_tool.set_layer()

                if current_map_tool.ref_line_layer is not None:
                    # setMapTool => Sets the map tool currently being used on the canvas
                    self.iface.mapCanvas().setMapTool(current_map_tool)

                    self.actions[map_tool_key].setChecked(True)
        else:
            self.iface.messageBar().pushMessage(self.tr('LinearReferencing'),
                                                self.tr("no suitable reference-layer (type linestring) found!")
                                                )
            for key in self.actions:
                self.actions[key].setChecked(False)

    def reset_tool(self, new_tool, old_tool):
        '''das Deaktivieren des MapTool-Icons, wenn der vorherige MapTool 'DigitizeLineEvent' war'''
        for key in self.actions:
            self.actions[key].setChecked(False)
