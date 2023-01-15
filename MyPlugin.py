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
from PyQt5.QtCore import QSettings

from PyQt5.QtCore import QTranslator, QCoreApplication, QLocale

from .MyMapTools import DigitizeLineEvent

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

        # Grundeinstellung aller Texte/Meldungen... "en_US", Übersetzungsdatei aber nur für "de"
        # die Übersetzungsdateien selbst werden via Qt Linguist aus dem Quellcode exrahiert (=> *.ts) und kompiliert (=> *.qm)
        # https://doc.qt.io/qt-5/qtlinguist-index.html
        # Creating Translation Files (*.ts) => Kommandozeilentool lupdate
        # der Aufruf generiert keine neue ts-Datei, sondern ergänzt diese mit neuen Treffern, z. B. aus neuen oder geänderten Quellcode-Dateien
        # Special bei Python:
        # lupdate sucht in den Quellcode-Dateien nach Qt-Objekt-Aufrufen der tr()-Funktion als my_qt_object.tr('...','...'), meckert dann aber "tr() cannot be called without context"
        # Workaround:
        # 1. Verwendung der statischen Variante QCoreApplication.translate("Quark", "Lorem ipsum...")
        # 2. eine eigene tr()-Funktion definieren, diese muss aber dem lupdate mit dem Parameter -tr-function-alias QT_TRANSLATE_NOOP=... mitgeteilt werden
        # lupdate Quellcode.py -tr-function-alias QT_TRANSLATE_NOOP=mein_tr -ts dictionary_de.ts
        # soll der Name der eigenen Funktion ebenfalls tr lauten:
        # lupdate Quellcode.py -tr-function-alias tr=weg_damit,QT_TRANSLATE_NOOP=tr -ts dictionary_de.ts
        # mehrere Dateien via Erweiterung:
        # lupdate -extensions py,ui Scan-verzeichnis -tr-function-alias tr=weg_damit,QT_TRANSLATE_NOOP=tr -ts dictionary_de.ts
        # hier z. B.:
        # cd
        # lupdate -extensions py /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/ -tr-function-alias tr=weg_damit,QT_TRANSLATE_NOOP=tr -ts /home/ludwig/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LinearReferencing/i18n/LinearReferencing_de.ts
        # -recursive => rekursives scannen (default)
        # -no-recursive => nur im aktuellen Verzeichnis
        # -target-language de_DE => wird aber automatisch erkannt
        # -extensions py => als erster Parameter gefolgt vom absoluten Verzeichnispfad
        # -silent => keine Fehlermeldung, z. B. werden mehrzeilige '''-Strings mit "Unterminated C++ string" bemäkelt, tut es nicht bei -extension
        # -no-obsolete => die in einer evtl. bereits vorhandenen ls-Datei nicht mehr verwendeten Einträge entfernen
        # Vorbedingung für Verwendung von pro-Dateien (deprecated): sudo apt-get install qt5-qmake

        # Spracheinstellung rausfinden und Übersetzungsdatei laden
        # geklaut bei "Plugin-Reloader"
        if QSettings().value('locale/overrideFlag', type=bool):
            # locale in QGis-Settings abweichend vom System definiert?
            locale = QSettings().value('locale/userLocale')
        else:
            # andernfalls Systemeinstellung
            locale = QLocale.system().name()

        # dynamischer Pfad zu einer Übersetzungsdatei, die nicht vorhanden sein muss, da nicht alle Sprachmöglichkeiten abgedeckt werden können
        # verwendet aber nur die ersten beiden Zeichen von locale, also wird aus 'de_DE' ein 'de',
        # um auch Österreich de_AT, Schweiz de_CH, Belgien de_BE, Liechtenstein de_LI ... zu bedienen
        ts_path = os.path.join(os.path.dirname(__file__), 'i18n', 'LinearReferencing_{}.qm'.format(locale[0:2]))
        print(ts_path)
        if os.path.exists(ts_path):
            # als Objekteigenschaft speichern
            self.translator = QTranslator()
            load_result = self.translator.load(ts_path)
            if load_result:
                QCoreApplication.installTranslator(self.translator)
            else:
                #raise Exception("Translator-Datei '{}' nicht geladen...".format(ts_path))
                pass
        else:
            #raise Exception("Translator-Datei '{}' nicht vorhanden...".format(ts_path))
            pass


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
            'LinearReferencing',
            self.iface.mainWindow())

        self.actions['DigitizeLineEvent'].setCheckable(True)

        self.actions['DigitizeLineEvent'].triggered.connect(lambda: self.set_map_tool('DigitizeLineEvent'))

        # Toolbar-Icoon für diese action
        self.iface.addToolBarIcon(self.actions['DigitizeLineEvent'])
        # und Menüeintrag
        self.iface.addPluginToMenu('LinearReferencing', self.actions['DigitizeLineEvent'])

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

    def set_map_tool(self, map_tool_key):
        '''MapTool bei Bedarf generieren und setzen'''

        # alle actions dieses Plugins (derzeit genau eines...) vorab deaktivieren
        for key in self.actions:
            self.actions[key].setChecked(False)

        if map_tool_key == 'DigitizeLineEvent':
            # nur bei Erstaufruf neu anlegen, sonst das bereits initialisierte weiterverwenden
            if map_tool_key in self.map_tools:
                current_map_tool = self.map_tools[map_tool_key]
            else:
                current_map_tool = DigitizeLineEvent(self.iface)

            current_map_tool.dialogue.show()
            current_map_tool.set_layer(self.iface.activeLayer())

            if current_map_tool.ref_line_layer is not None:
                # setMapTool => Sets the map tool currently being used on the canvas
                self.iface.mapCanvas().setMapTool(current_map_tool)
                self.actions[map_tool_key].setChecked(True)

                # Referenz im Plugin-Objekt zur Konservierung (sonst ist das lokale current_map_tool nach Beendigung von set_map_tool nicht mehr vorhanden)
                # und Wiederverwendung bei wiederholtem Aufruf
                self.map_tools['DigitizeLineEvent'] = current_map_tool

    def reset_tool(self, new_tool, old_tool):
        '''das Deaktivieren des MapTool-Icons, wenn der vorherige MapTool 'DigitizeLineEvent' war'''
        for key in self.actions:
            self.actions[key].setChecked(False)

        '''if type(old_tool).__name__ == 'DigitizeLineEvent':
            try:
                current_action = self.actions['DigitizeLineEvent']
                # seltsamerweise unter Windows: AttributeError: 'LinearReferencing' object has no attribute 'action'
                current_action.setChecked(False)
            except:
                pass'''
