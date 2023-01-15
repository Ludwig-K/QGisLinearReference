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
from PyQt5.QtCore import pyqtSlot, QVariant
from qgis._gui import QgsSnapIndicator, QgsMapToolEmitPoint, QgsMapMouseEvent
from qgis._core import Qgis, QgsTolerance, QgsProject, QgsExpression, QgsFeature, \
    QgsFields, QgsField, QgsVectorLayer

from .MyToolFunctions import OneLayerFilter, OneFeatureFilter
from qgis._core import QgsMapLayerType
from qgis._gui import QgsRubberBand, QgsVertexMarker
from PyQt5.QtGui import QColor, QIcon
from .MyDialogs import LRefDockWidget
from qgis.PyQt.QtCore import Qt

from qgis._core import QgsWkbTypes
from .MyToolFunctions import get_segment_geom, line_interpolate_point, line_locate_point
import os


class DigitizeLineEvent(QgsMapToolEmitPoint):
    '''ein Linien-Event digitalisieren
    Logik:
    aktiver Linienlayer
    Snapping-Einstellungen
    Cursor auf die gewünschte Referenz-Linie des aktiven Layers setzen,
    Klick 1
    Klick 2 (Snap muss auf der gleichen Linie sitzen)
    fertig!
    '''

    def __init__(self, iface):
        '''Initialisierung
        :param iface: QgsInterface "Abstract base class defining interfaces exposed by QgisApp and made available to plugins."
        '''
        self.iface = iface

        QgsMapToolEmitPoint.__init__(self, self.iface.mapCanvas())

        # Nachkommastellen für Anzeige von Koordinaten/Messgrößen
        self.num_digits = 1

        # Offset der Linie, Eingabe in self.dialogue
        self.offset = 0

        # der Bezugslayer vom Typ Linie
        self.ref_line_layer = None
        # fid der mit dem ersten Snap definierten Referenzlinie
        self.snapped_fid = None

        # drei temporäre Grafiken
        self.rb_segment = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        self.rb_segment.setColor(QColor(0, 255, 255, 128))
        self.rb_segment.setWidth(8)
        self.rb_segment.hide()

        self.vm_pt_1 = QgsVertexMarker(self.iface.mapCanvas())
        self.vm_pt_1.setIconSize(10)
        self.vm_pt_1.setIconType(QgsVertexMarker.ICON_BOX)
        self.vm_pt_1.setPenWidth(3)
        self.vm_pt_1.setColor(QColor(0, 255, 0))
        self.vm_pt_1.hide()

        self.vm_pt_2 = QgsVertexMarker(self.iface.mapCanvas())
        self.vm_pt_2.setIconSize(10)
        self.vm_pt_2.setIconType(QgsVertexMarker.ICON_BOX)
        self.vm_pt_2.setPenWidth(3)
        self.vm_pt_2.setColor(QColor(255, 0, 0))
        self.vm_pt_2.hide()

        self.project = QgsProject.instance()

        # Stationierung des ersten Punktes
        self.point_1_m = None

        # Stationierung des zweiten Punktes
        self.point_2_m = None

        # Distanz festsetzen, kleines Schloss-Icon im Dialog
        self.dist_locked = False

        #temporäre virtuelle Tabelle
        self.vi_tb = None

        # temporäre virtueller Layer basierend auf dieser Tabelle
        self.vi_ly = None

        # notwendige Snapping-Funktionalität bei der Initialisierung des Map-Tools:
        # aktiver Layer
        # Stützstellen, Anfang/Ende und Ziwschen-Punkte auf der Linie
        # Radius 10 Pixel
        # diese können anschließend aber angepasst werden

        # Referenz auf das kleine Snap-Icon
        self.snap_indicator = QgsSnapIndicator(self.iface.mapCanvas())
        my_snap_config = iface.mapCanvas().snappingUtils().config()
        my_snap_config.setEnabled(True)
        '''
        NoSnap
        Vertex
        Segment
        Area
        Centroid
        MiddleOfSegment
        LineEndpoint
        '''
        type_flag = Qgis.SnappingTypes(
            Qgis.SnappingType.Vertex | Qgis.SnappingType.Segment | Qgis.SnappingType.LineEndpoint)
        my_snap_config.setTypeFlag(type_flag)
        my_snap_config.setUnits(QgsTolerance.UnitType.Pixels)
        my_snap_config.setTolerance(10)
        my_snap_config.setIntersectionSnapping(False)
        '''
        ActiveLayer
        AllLayers
        AdvancedConfiguration => individuelle Einstellungen je Layer
        '''
        my_snap_config.setMode(Qgis.SnappingMode.ActiveLayer)

        QgsProject.instance().setSnappingConfig(my_snap_config)

        # Snap-Icon anzeigen
        self.snap_indicator.setVisible(True)

        # das Ausgabefenster für dieses mapTool
        self.dialogue = LRefDockWidget(iface)

        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dialogue)

        # geht erst nach addDockWidget
        self.dialogue.setFloating(True)
        # Größe gem. setSizePolicy und der LRefDockWidget.sizeHint-Methode auf Minimalgröße setzen
        self.dialogue.adjustSize()

        # self.dialogue.hide()

        # die Signals des Dialogs mit Slots des mapTools verbinden
        self.dialogue.dspbx_offset.valueChanged.connect(self.offset_edited)
        self.dialogue.pbtn_reset.clicked.connect(self.reset)

        # Hinweis:
        # im Weiteren wird das valueChanged-Signal bei setValue() mittels blockSignals(True) unterbunden,
        # da dies nur bei Benutzereingabe ausgelöst werden soll
        self.dialogue.dspbx_pt1_m.valueChanged.connect(self.slot_pt1_m_edited)
        self.dialogue.dspbx_pt2_m.valueChanged.connect(self.slot_pt2_m_edited)
        self.dialogue.dspbx_pt_dist.valueChanged.connect(self.slot_dist_edited)
        self.dialogue.pb_lock_dist.clicked.connect(self.slot_dist_lock)
        self.dialogue.pb_pt1_redigitize.clicked.connect(self.slot_pt1_redigitize)
        self.dialogue.pb_pt2_redigitize.clicked.connect(self.slot_pt2_redigitize)
        self.dialogue.le_snapped_fid.returnPressed.connect(self.slot_snapped_fid_edited)
        self.dialogue.pbtn_create_vl.clicked.connect(self.slot_create_vl)

    @pyqtSlot(bool)
    def slot_pt1_redigitize(self, checked):
        # self.vm_pt_1.hide()
        # self.rb_segment.hide()
        self.point_1_m = None
        self.dialogue.le_map_pt1_x.clear()
        self.dialogue.le_map_pt1_y.clear()
        self.dialogue.le_snap_pt1_x.clear()
        self.dialogue.le_snap_pt1_y.clear()
        self.dialogue.dspbx_pt1_m.clear()
        self.dialogue.dspbx_pt_dist.clear()

    @pyqtSlot(bool)
    def slot_pt2_redigitize(self, checked):
        # self.vm_pt_2.hide()
        # self.rb_segment.hide()
        self.point_2_m = None
        self.dialogue.le_map_pt2_x.clear()
        self.dialogue.le_map_pt2_y.clear()
        self.dialogue.le_snap_pt2_x.clear()
        self.dialogue.le_snap_pt2_y.clear()
        self.dialogue.dspbx_pt2_m.clear()
        self.dialogue.dspbx_pt_dist.clear()

    @pyqtSlot(bool)
    def slot_dist_lock(self, checked):
        '''toggelt self.dist_locked, falls true, wird beim Verschieben eines Punktes der andere mitverschoben, so dass der Abstand erhalten bleibt'''
        self.dist_locked = not self.dist_locked

        if self.dist_locked:
            self.dialogue.pb_lock_dist.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons/lock-outline.svg')))
        else:
            self.dialogue.pb_lock_dist.setIcon(
                QIcon(os.path.join(os.path.dirname(__file__), 'icons/lock-open-variant-outline.svg')))

    def offset_edited(self, offset):
        '''Geänderter Offset im Dialog => Linie neu zeichnen'''
        # da es eine QDoubleSpinBox ist enfällt der Gültigkeitscheck
        self.offset = offset

        segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, self.point_1_m, self.point_2_m,
                                        self.offset)

        if segment_geom:
            # zweiter Parameter bewirkt die Projektion in die SRID dieses Layers
            self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
            self.rb_segment.show()

    @pyqtSlot(float)
    def slot_pt1_m_edited(self, pt1_m: float) -> None:
        '''Slot für das valueChanged-Signal der QDoubleSpinBox für die Stationierung 1
        dies wird bei setValue (laufende Aktualisierung) mittels blockSignal unterbunden und nur bei Benutzereingabe ausgelöst.
        Berechnet aus dem numerischen Stationierungswert die Position des Punktes auf dem Canvas und zeigt diesen und das Liniensegement.
        Aktualisiert das Distanz-Eingabe-Feld.
        :param pt1_m: Abstand des ersten Punktes vom Linienanfang
        '''

        if (self.ref_line_layer is not None) and (self.snapped_fid is not None):
            snapped_feature = self.ref_line_layer.getFeature(self.snapped_fid)
            if snapped_feature:
                snapped_geom = snapped_feature.geometry()

                # Stationierung auf den möglichen Bereich eingrenzen 0...Gesamtlänge
                # < 0 ist im Widget eigentlich unterbunden
                pt1_m = max(0, min(pt1_m, snapped_geom.length()))

                projected_point = line_interpolate_point(self.ref_line_layer, self.snapped_fid, pt1_m,
                                                         self.iface.mapCanvas().mapSettings().destinationCrs().authid())

                if projected_point:
                    if self.point_1_m is not None:
                        delta_dist = pt1_m - self.point_1_m
                    else:
                        delta_dist = 0

                    self.point_1_m = pt1_m


                    if self.dist_locked:
                        self.point_2_m += delta_dist
                        self.point_2_m = max(0, min(self.point_2_m, snapped_geom.length()))
                        #self.point_1_m = self.point_2_m - delta_dist
                        self.dialogue.dspbx_pt2_m.setValue(self.point_2_m)

                    self.dialogue.dspbx_pt1_m.setValue(self.point_1_m)


                    self.draw_point_1()

                    if self.point_1_m is not None and self.point_2_m is not None:
                        point_dist = self.point_2_m - self.point_1_m
                        self.dialogue.dspbx_pt_dist.blockSignals(True)
                        self.dialogue.dspbx_pt_dist.setValue(point_dist)
                        self.dialogue.dspbx_pt_dist.blockSignals(False)

                        segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, self.point_1_m,
                                                        self.point_2_m,
                                                        self.offset)
                        if segment_geom:
                            self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
                            self.rb_segment.show()

    @pyqtSlot()
    def slot_create_vl(self):
        self.vi_ly = None
        self.vi_tb = None
        vi_tb = QgsVectorLayer('None', 'LinearReference Data', 'memory')
        self.vi_tb_fid_field = QgsField("fid", QVariant.Int)
        self.vi_tb_ref_layer_field = QgsField("reference_layer", QVariant.String)
        self.vi_tb_ref_id_field = QgsField("reference_id", QVariant.Int)
        self.vi_tb_from_field = QgsField("from", QVariant.Double)
        self.vi_tb_to_field = QgsField("to", QVariant.Double)
        self.vi_tb_offset_field = QgsField("offset", QVariant.Double)
        self.vi_tb_info_field = QgsField("info", QVariant.String)
        vi_tb.dataProvider().addAttributes([
            self.vi_tb_fid_field,
            self.vi_tb_ref_layer_field,
            self.vi_tb_ref_id_field,
            self.vi_tb_from_field,
            self.vi_tb_to_field,
            self.vi_tb_offset_field,
            self.vi_tb_info_field
        ])
        vi_tb.updateFields()
        QgsProject.instance().addMapLayer(vi_tb)
        self.vi_tb = vi_tb

        #mühsames rausfinden der fid-Spalte
        fid_col_idx_lst = self.ref_line_layer.dataProvider().pkAttributeIndexes()

        if len(fid_col_idx_lst) == 1:
            fid_col_idx = fid_col_idx_lst[0]
            fid_col = self.ref_line_layer.fields().at(fid_col_idx)

            print(fid_col.name(),fid_col)

            vi_ly_sql = """
            SELECT 
            ref_line_layer.\"{}\",
            vi_tb.*,
            ST_OffsetCurve(
                ST_Line_Substring(
                    ref_line_layer.geometry, 
                    min(vi_tb.\"from\", vi_tb.\"to\") / st_length(ref_line_layer.geometry), 
                    max(vi_tb.\"from\", vi_tb.\"to\") / st_length(ref_line_layer.geometry)
                ), 
                vi_tb.\"offset\"
            ) as \"geometry\" /*:linestring:{}*/
            FROM \"{}\" as vi_tb
            INNER JOIN \"{}\" as ref_line_layer ON vi_tb.\"reference_id\" = ref_line_layer.\"{}\"
            """.format(fid_col.name(),self.ref_line_layer.crs().postgisSrid(),self.vi_tb.id(), self.ref_line_layer.id(),fid_col.name())

            #print(vi_ly_sql)
            #vi_ly = QgsVectorLayer("linestring?crs={}".format(self.ref_line_layer.crs().postgisSrid()), "LinearReference Layer", "virtual")
            #blödes Problem: bei QgsVectorLayer mit virtueller abfrage versucht QGis, den Typ und die Projektion anhand der von der Abfrage zurückgelieferten Features zu erkennen.
            #Daher hier einen Datensatz einfügen
            vi_ly = QgsVectorLayer("?query={}".format(vi_ly_sql), "LinearReference Layer", "virtual")

            QgsProject.instance().addMapLayer(vi_ly)
            self.vi_ly = vi_ly


        else:
            raise Exception("keine eindeutige ID-Spalte in Layer '{}' nicht geladen...".format(self.ref_line_layer.name()))




    @pyqtSlot()
    def slot_snapped_fid_edited(self):
        if self.ref_line_layer:
            new_fid = self.dialogue.le_snapped_fid.text()
            # nur Integerwerte, wird aber auch im qt-Formular gecheckt
            if new_fid.isdigit():
                new_fid = int(new_fid)
                # interessanterweise liefert getFeature *immer* ein Feature, aber ohne Attribute und Geometrien
                snapped_feature = self.ref_line_layer.getFeature(new_fid)

                if snapped_feature.hasGeometry():
                    self.snapped_fid = new_fid
                    segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, self.point_1_m,
                                                    self.point_2_m,
                                                    self.offset)

                    if segment_geom:
                        # zweiter Parameter bewirkt die Projektion in die SRID dieses Layers
                        self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
                        self.rb_segment.show()

                else:
                    self.iface.messageBar().pushMessage('LinearReferencing',
                                                        "Kein Feature mit ID {} in Layer {}".format(new_fid,
                                                                                                    self.ref_line_layer.name()),
                                                        level=Qgis.Info,
                                                        duration=3)
                    if self.snapped_fid:
                        self.dialogue.le_snapped_fid.setText(str(self.snapped_fid))
                    else:
                        self.dialogue.le_snapped_fid.clear()
            else:
                self.iface.messageBar().pushMessage('LinearReferencing', "Bitte ganzzahlige Feature-ID eingeben!",
                                                    level=Qgis.Info,
                                                    duration=3)
        else:
            self.iface.messageBar().pushMessage('LinearReferencing', "kein Layer aktiv!", level=Qgis.Warning,
                                                duration=3)

    @pyqtSlot(float)
    def slot_pt2_m_edited(self, pt2_m: float) -> None:
        '''Slot für das valueChanged-Signal der QDoubleSpinBox für die Stationierung 2
        dies wird bei setValue (laufende Aktualisierung) mittels blockSignal unterbunden und nur bei Benutzereingabe ausgelöst.
        Berechnet aus dem numerischen Stationierungswert die Position des Punktes auf dem Canvas und zeigt diesen und das Liniensegement.
        Aktualisiert das Distanz-Eingabe-Feld.
        :param pt2_m: Abstand des ersten Punktes vom Linienanfang
        '''

        if (self.ref_line_layer is not None) and (self.snapped_fid is not None):
            snapped_feature = self.ref_line_layer.getFeature(self.snapped_fid)
            if snapped_feature:
                snapped_geom = snapped_feature.geometry()

                # Stationierung auf den möglichen Bereich eingrenzen 0...Gesamtlänge
                # < 0 ist im Widget eigentlich unterbunden
                pt2_m = max(0, min(pt2_m, snapped_geom.length()))

                projected_point = line_interpolate_point(self.ref_line_layer, self.snapped_fid, pt2_m,
                                                         self.iface.mapCanvas().mapSettings().destinationCrs().authid())

                if projected_point:
                    if self.point_2_m is not None:
                        delta_dist = pt2_m - self.point_2_m
                    else:
                        delta_dist = 0

                    self.point_2_m = pt2_m
                    self.dialogue.dspbx_pt2_m.setValue(self.point_2_m)

                    if self.dist_locked:
                        self.point_1_m += delta_dist
                        self.point_1_m = max(0, min(self.point_1_m, snapped_geom.length()))
                        self.dialogue.dspbx_pt1_m.setValue(self.point_1_m)

                    self.draw_point_2()

                    if (self.point_1_m is not None) and (self.point_2_m is not None):
                        point_dist = self.point_2_m - self.point_1_m
                        self.dialogue.dspbx_pt_dist.blockSignals(True)
                        self.dialogue.dspbx_pt_dist.setValue(point_dist)
                        self.dialogue.dspbx_pt_dist.blockSignals(False)
                        segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, self.point_1_m,
                                                        self.point_2_m,
                                                        self.offset)
                        if segment_geom:
                            self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
                            self.rb_segment.show()

    @pyqtSlot(float)
    def slot_dist_edited(self, dist_m: float) -> None:
        '''Slot für das valueChanged-Signal der QDoubleSpinBox für die Distanz
        dies wird bei setValue (laufende Aktualisierung) mittels blockSignal unterbunden und nur bei Benutzereingabe ausgelöst.
        Nimmt den Stationierungswert 1 plus Distanz, berechnet daraus die Position des Punktes auf dem Canvas und zeigt diesen und das Liniensegement.
        Aktualisiert die Stationierung des zweiten Punktes im Dialog.
        Eigentlich gleiche Auswirkung wie Klick auf die QDoubleSpinBox des zweiten Punktes, erlaubt aber ein exaktes Einstellen der Abschnittslänge
        :param dist_m: Abstand zwischen den beiden Punkten
        '''

        if (self.ref_line_layer is not None) and (self.snapped_fid is not None):
            snapped_feature = self.ref_line_layer.getFeature(self.snapped_fid)
            if snapped_feature:
                snapped_geom = snapped_feature.geometry()

                pt2_m = self.point_1_m + dist_m

                # Stationierung auf den möglichen Bereich eingrenzen 0...Gesamtlänge
                # < 0 ist im Widget eigentlich unterbunden
                pt2_m = max(0, min(pt2_m, snapped_geom.length()))

                projected_point = line_interpolate_point(self.ref_line_layer, self.snapped_fid, pt2_m,
                                                         self.iface.mapCanvas().mapSettings().destinationCrs().authid())

                if projected_point:

                    self.point_2_m = pt2_m
                    self.dialogue.dspbx_pt2_m.setValue(self.point_2_m)
                    point_dist = self.point_2_m - self.point_1_m
                    self.dialogue.dspbx_pt_dist.setValue(point_dist)
                    self.draw_point_2()
                    segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, self.point_1_m,
                                                    self.point_2_m,
                                                    self.offset)
                    if segment_geom:
                        self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
                        self.rb_segment.show()

    def reset(self):
        '''Einstellungen zurücksetzen (außer self.ref_line_layer), Grafiken verbergen, Dialog leeren'''
        self.point_1_m = None
        self.snapped_fid = None
        self.point_2_m = None
        self.dialogue.reset()
        self.rb_segment.hide()
        self.vm_pt_1.hide()
        self.vm_pt_2.hide()
        self.snap_indicator.setVisible(True)

    def unload(self):
        '''Aufräumen, falls das map_tool neu aufgerufen wird oder das Plugin entfernt wird
        zusätzlich zum reset werden die temporären Linien/Punktgrafiken gelöscht'''
        self.reset()
        del self.vm_pt_1
        del self.vm_pt_2
        del self.rb_segment

    def set_layer(self, layer):
        if layer:
            if layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.LineGeometry:
                self.ref_line_layer = layer
                self.dialogue.le_pt1_layer_name.setText(self.ref_line_layer.name())
                self.apply_srids_to_dialogue()
            else:
                pass
                """self.iface.messageBar().pushMessage('LinearReferencing',
                                                    "aktiver Layer '{}' ist kein Linienlayer!".format(
                                                        layer.name()), level=Qgis.Warning, duration=3)"""


        else:
            self.iface.messageBar().pushMessage('LinearReferencing', self.tr("no Layer active!"), level=Qgis.Warning,
                                                duration=3)

    def apply_srids_to_dialogue(self):
        '''einige Änderungen an den Funktionselementen speziell für geographische Projektionen im canvas oder layer
        hier z. B. die Anzahl Nachkommastellen und Schrittweiten der DoubleSpinBoxen und die Längen-Einheiten
        dazu wurden diese Widgets in LRefDockWidget in vier Listen canvas_unit_widgets/layer_unit_widgets canvas_measure_widgets/layer_measure_widgets referenziert
        '''
        if self.iface.mapCanvas().mapSettings().destinationCrs().isGeographic():
            canvas_measure_unit = '[°]'
            canvas_measure_prec = 4
            canvas_measure_step = 0.0001
            self.num_digits = 4
        else:
            canvas_measure_unit = '[m]'
            canvas_measure_prec = 1
            canvas_measure_step = 10
            self.num_digits = 1

        if self.ref_line_layer.crs().isGeographic():
            layer_measure_unit = '[°]'
            layer_measure_prec = 4
            layer_measure_step = 0.0001

        else:
            layer_measure_unit = '[m]'
            layer_measure_prec = 1
            layer_measure_step = 10

        for unit_widget in self.dialogue.canvas_unit_widgets:
            unit_widget.setText(canvas_measure_unit)

        for unit_widget in self.dialogue.layer_unit_widgets:
            unit_widget.setText(layer_measure_unit)

        for measure_widget in self.dialogue.canvas_measure_widgets:
            measure_widget.setDecimals(canvas_measure_prec)
            measure_widget.setSingleStep(canvas_measure_step)

        for measure_widget in self.dialogue.layer_measure_widgets:
            measure_widget.setDecimals(layer_measure_prec)
            measure_widget.setSingleStep(layer_measure_step)

    def canvasMoveEvent(self, event: QgsMapMouseEvent) -> None:
        '''MouseMove auf der Karte, laufende Aktualisierung des Dialogs, Voranzeige des linearen Segments
        :param event: Klick-Event
        '''
        if not self.dialogue.isVisible():
            self.dialogue.show()

        if self.ref_line_layer is not None:
            if self.iface.activeLayer() != self.ref_line_layer:
                pass
                # lästig
                #self.iface.setActiveLayer(self.ref_line_layer)
                #self.iface.messageBar().pushMessage("Plugin 'LinearReferencing'",
                #                                    "Bezugslayer reaktiviert...",
                #                                    level=Qgis.Info)
            snap_filter = OneLayerFilter(self.ref_line_layer)
            if self.snapped_fid:
                # Snapp-Filter für den zweiten Punkt: muss das gleiche Linien-Feature wie beim ersten Punkt sein
                # cooles Feature :-)
                snap_filter = OneFeatureFilter(self.ref_line_layer, self.snapped_fid)

            if (self.point_1_m is None) or (self.point_2_m is None):
                m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)
                self.snap_indicator.setMatch(m)

                point_m = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(event.x(), event.y())
                map_x = point_m.x()
                str_map_x = '{:.{prec}f}'.format(map_x, prec=self.num_digits)
                map_y = point_m.y()
                str_map_y = '{:.{prec}f}'.format(map_y, prec=self.num_digits)

                # laufende Koordinatenanzeige
                if not self.point_1_m:
                    self.dialogue.le_map_pt1_x.setText(str_map_x)
                    self.dialogue.le_map_pt1_y.setText(str_map_y)
                elif not self.point_2_m:
                    self.dialogue.le_map_pt2_x.setText(str_map_x)
                    self.dialogue.le_map_pt2_y.setText(str_map_y)

                if self.snap_indicator.match().type():
                    point_s = self.snap_indicator.match().point()
                    snap_x = point_s.x()
                    str_snap_x = '{:.{prec}f}'.format(snap_x, prec=self.num_digits)
                    snap_y = point_s.x()
                    str_snap_y = '{:.{prec}f}'.format(snap_y, prec=self.num_digits)
                    snapped_feat_id = m.featureId()
                    snapped_m = line_locate_point(self.ref_line_layer, snapped_feat_id, point_s.x(), point_s.y(),
                                                  self.iface.mapCanvas().mapSettings().destinationCrs().authid(),
                                                  self.ref_line_layer.crs().authid())

                    self.dialogue.le_snapped_fid.setText(str(snapped_feat_id))

                    if not self.point_1_m:
                        self.dialogue.le_snap_pt1_x.setText(str_snap_x)
                        self.dialogue.le_snap_pt1_y.setText(str_snap_y)
                        # das valueChanged-Signal unterbinden, dies soll nur ausgelöst werden, wenn vom User getriggert
                        self.dialogue.dspbx_pt1_m.blockSignals(True)
                        self.dialogue.dspbx_pt1_m.setValue(snapped_m)
                        self.dialogue.dspbx_pt1_m.blockSignals(False)
                    elif not self.point_2_m:
                        self.dialogue.le_snap_pt2_x.setText(str_snap_x)
                        self.dialogue.le_snap_pt2_y.setText(str_snap_y)

                        self.dialogue.dspbx_pt2_m.blockSignals(True)
                        self.dialogue.dspbx_pt2_m.setValue(snapped_m)
                        self.dialogue.dspbx_pt2_m.blockSignals(False)

                    if (self.point_1_m is not None):
                        segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, self.point_1_m,
                                                        snapped_m, 0)
                        if segment_geom:
                            self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
                            self.rb_segment.show()

                            # in Digitalisierrichtung positiv
                            point_dist =  snapped_m - self.point_1_m

                            self.dialogue.dspbx_pt_dist.blockSignals(True)
                            self.dialogue.dspbx_pt_dist.setValue(point_dist)
                            self.dialogue.dspbx_pt_dist.blockSignals(False)

                    elif  (self.point_2_m is not None):
                        segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, snapped_m,
                                                        self.point_2_m, 0)
                        if segment_geom:
                            self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
                            self.rb_segment.show()


                        # in Digitalisierrichtung positiv
                        point_dist = self.point_2_m - snapped_m

                        self.dialogue.dspbx_pt_dist.blockSignals(True)
                        self.dialogue.dspbx_pt_dist.setValue(point_dist)
                        self.dialogue.dspbx_pt_dist.blockSignals(False)

    def canvasPressEvent(self, event: QgsMapMouseEvent) -> None:
        '''Klick auf der Karte, setzt die beiden Punkte
        :param event: Klick-Event
        '''
        if self.ref_line_layer:
            if (self.point_1_m is not None) and (self.point_2_m is not None):
                # drittes Klicken => reset
                self.reset()

            # Ergebnisanzeige wie beim canvasMoveEvent
            self.canvasMoveEvent(event)

            snap_filter = OneLayerFilter(self.ref_line_layer)
            if self.snapped_fid:
                # Snapp-Filter für den zweiten Punkt: muss das gleiche Linien-Feature wie beim ersten Punkt sein
                # cooles Feature :-)
                snap_filter = OneFeatureFilter(self.ref_line_layer, self.snapped_fid)

            m = self.iface.mapCanvas().snappingUtils().snapToMap(event.pos(), snap_filter)

            if self.snap_indicator.match().type():
                point_s = self.snap_indicator.match().point()
                snapped_feat_id = m.featureId()

                snapped_m = line_locate_point(self.ref_line_layer, snapped_feat_id, point_s.x(), point_s.y(),
                                              self.iface.mapCanvas().mapSettings().destinationCrs().authid(),
                                              self.ref_line_layer.crs().authid())

                if self.point_1_m is None:
                    self.snapped_fid = snapped_feat_id
                    self.dialogue.le_snapped_fid.setText(str(self.snapped_fid))
                    self.point_1_m = snapped_m
                    self.draw_point_1()
                elif self.point_2_m is None:
                    self.point_2_m = snapped_m
                    self.draw_point_2()


                if (self.point_1_m is not None) and (self.point_2_m) is not None:
                    self.snap_indicator.setVisible(False)
                    point_dist = self.point_2_m - self.point_1_m
                    self.dialogue.dspbx_pt_dist.blockSignals(True)
                    self.dialogue.dspbx_pt_dist.setValue(point_dist)
                    self.dialogue.dspbx_pt_dist.blockSignals(False)

                    segment_geom = get_segment_geom(self.ref_line_layer, self.snapped_fid, self.point_1_m,
                                                    self.point_2_m, self.offset)
                    if segment_geom:
                        self.rb_segment.setToGeometry(segment_geom, self.ref_line_layer)
                        self.rb_segment.show()

    def draw_point_1(self):
        if (self.ref_line_layer is not None) and (self.snapped_fid is not None) and (self.point_1_m is not None):
            projected_point = line_interpolate_point(self.ref_line_layer, self.snapped_fid, self.point_1_m,
                                                     self.iface.mapCanvas().mapSettings().destinationCrs().authid())
            if projected_point is not None:
                self.vm_pt_1.setCenter(projected_point.asPoint())
                self.vm_pt_1.show()
            else:
                self.vm_pt_1.hide()

    def draw_point_2(self):
        if (self.ref_line_layer is not None) and (self.snapped_fid is not None) and (self.point_2_m is not None):
            projected_point = line_interpolate_point(self.ref_line_layer, self.snapped_fid, self.point_2_m,
                                                     self.iface.mapCanvas().mapSettings().destinationCrs().authid())
            if projected_point is not None:
                self.vm_pt_2.setCenter(projected_point.asPoint())
                self.vm_pt_2.show()
            else:
                self.vm_pt_2.hide()
