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
from qgis._core import QgsPointLocator, QgsVectorLayer, QgsGeometry, QgsMapLayerType, QgsWkbTypes, QgsProject, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransform, QgsPointXY, QgsLineString, Qgis


def get_linestring_layers(iface) -> list:
    '''scant die aktuellen Layer des Projektes und liefert eine Liste der originären linestring-Layer
    virtuelle Layer wie z. B. bereits vorhandene line_on_line-Layer werden dabei übergangen
    ein derzeit geeigneter aktiver Layer dieses Typs ist der erste Eintrag der Ergebnisliste
    :param iface: QgsInterface "Abstract base class defining interfaces exposed by QgisApp and made available to plugins."
    '''
    ll = []

    # Layerliste nach geeigneten Layern durchsuchen via dataProvider().name()
    # => https://api.qgis.org/api/classQgsDataProvider.html => memory/virtual/ogr
    """for cl in QgsProject.instance().mapLayers().values():
        if cl.type() == QgsMapLayerType.VectorLayer:
            print(cl.dataProvider().name())"""
    # Vorzugsbehandlung des aktiven Layers
    if iface.activeLayer():
        if iface.activeLayer().type() == QgsMapLayerType.VectorLayer and iface.activeLayer().geometryType() == QgsWkbTypes.LineGeometry and iface.activeLayer().dataProvider().name() != 'virtual':
            ll.append(iface.activeLayer())

    #die restlichen Layer des Projektes
    for cl in QgsProject.instance().mapLayers().values():
        if cl.type() == QgsMapLayerType.VectorLayer and cl.geometryType() == QgsWkbTypes.LineGeometry and cl.dataProvider().name() != 'virtual' and cl not in ll:
            ll.append(cl)

    return ll


class OneLayerFilter(QgsPointLocator.MatchFilter):
    '''Filter für das Snapping:
    Nur auf Features eines bestimmten Layers Snappen
    hier doppelt, da ohnehin my_snap_config.setMode(QgsSnappingConfig.AdvancedConfiguration) auf den reference_layer gesetzt wurde'''

    def __init__(self, layer):
        QgsPointLocator.MatchFilter.__init__(self)
        self.layer = layer

    def acceptMatch(self, m):
        return m.layer() == self.layer


class OneFeatureFilter(QgsPointLocator.MatchFilter):
    '''Filter für das Snapping:
    Nur auf ein bestimmtes Feature eines bestimmten Layers snappen'''

    def __init__(self, layer, fid):
        QgsPointLocator.MatchFilter.__init__(self)
        self.layer = layer
        self.fid = fid

    def acceptMatch(self, m):
        return m.layer() == self.layer and m.featureId() == self.fid


def get_segment_geom(vlayer: QgsVectorLayer, fid: int, start: float,
                     end: float, offset: float = 0, to_epsg: str = None) -> QgsGeometry:
    '''liefert das Liniensegment start...end für ein bestimmtes Feature,
    <QgsGeometry: LineString (...)>
    Die Reihenfolge der Stationierungsangaben start/end wird mit min(start,end)/max(start,end) geswitcht.
    Beispiel: interpolated_line = get_segment_geom(iface.activeLayer(),1,20,40,10,'EPSG:4326')
    :param vlayer: Referenz-Linien-Layer
    :param fid: Feature-ID im Referenz-Linien-Layer
    :param start: Start-Stationierung
    :param end: End-Stationierung
    :param offset: Abstand des erzeugten Liniensegments von der Bezugslinie positiv: links, negativ: rechts von der Bezugslinie in Digitalisier-Richtung
    :param to_epsg: optionale Projektion des Ergebnisses, falls z. B. im Canvas eine andere Projektion als im Layer vorliegt
    Beispiele:
    iface.mapCanvas().mapSettings().destinationCrs().authid()
    'EPSG:4326'
    default: keine Projektion => Ergebnis in vlayer-Projektion,
    :raises ValueError: bei Layertyp/Geometrietyp != VectorLayer/LineGeometry
    '''

    if (vlayer is not None) and (fid is not None):
        if vlayer.type() == QgsMapLayerType.VectorLayer and vlayer.geometryType() == QgsWkbTypes.LineGeometry:
            snapped_feature = vlayer.getFeature(fid)
            # getFeature liefert immer ein QgsFeature, das hat aber keine Geometrie/Attribute, wenn die fid nicht gefunden wird
            if snapped_feature.hasGeometry():
                # mehrere Stunden suchen&fluchen, um auf das Pendant line_substring/ST_LineSubString... zu kommen

                #geom = snapped_feature.geometry()
                #=> <QgsGeometry: LineStringM (307127.072824815986678 5656137.51322958432137966 0...

                #geom_pl = geom.asPolyline()
                #=> [<QgsPointXY: POINT(315119.52447292604483664 5651067.53584263008087873)>, <QgsPointXY:...

                #geom_ls = QgsLineString(geom_pl)
                #=> <QgsLineString: LineString (315119.52447292604483664 5651067.53584263008087873,

                from_m = min(start, end)
                to_m = max(start, end)


                #substr_ls = geom_ls.curveSubstring(from_m, to_m)
                #=> <QgsLineString: LineString (315121.32432889757910743 5651062.87102553993463516,

                #substr_geom = QgsGeometry(substr_ls)
                #=> <QgsGeometry: LineString (315121.32432889757910743 5651062.87102553993

                #OneLiner:
                substr_geom = QgsGeometry(QgsLineString(snapped_feature.geometry().asPolyline()).curveSubstring(from_m, to_m))

                if offset:
                    #:param distance: buffer distance
                    #:param segments: for round joins, number of segments to approximate quarter-circle
                    #param joinStyle: join style for corners in geometry (Round (default) Miter (spitz) Bevel (gefast), siehe https://docs.qgis.org/3.22/en/docs/user_manual/processing_algs/qgis/vectorgeometry.html)
                    #:param miterLimit: limit on the miter ratio used for very sharp corners (JoinStyleMiter only)
                    substr_geom = substr_geom.offsetCurve(offset, 1, Qgis.JoinStyle.Round, 0)
                    #=> <QgsGeometry: LineString (315125.98914598737610504 5651064.67088151164352894,

                if to_epsg != vlayer.crs().authid():
                    tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(to_epsg), vlayer.crs(),
                                                QgsProject.instance())
                    substr_geom.transform(tr)

                return substr_geom
        else:
            raise ValueError("get_segment_geom: Eingangslayer '{}' ist kein Linienlayer".format(vlayer.name()))


def line_locate_point(vlayer: QgsVectorLayer, fid: int, x: float, y: float, xy_epsg: str) -> float:
    '''liefert die Stationierung eines Punktes auf einer Linie für ein bestimmtes Feature,
    Beispiel: m = line_locate_point(iface.activeLayer(),1,50.74566, 6.48769,'EPSG:4326','EPSG:25832')
    :param vlayer: Referenz-Linien-Layer
    :param fid: Feature-ID im Referenz-Linien-Layer
    :param x: Punkt-Koordinate x
    :param y: Punkt-Koordinate y
    :param xy_epsg: Projektion der Punkt-Koordinaten
    iface.mapCanvas().mapSettings().destinationCrs().authid()
    'EPSG:4326'
    :raises ValueError: bei Layertyp/Geometrietyp != VectorLayer/LineGeometry
    '''

    if (vlayer is not None) and (fid is not None):
        if vlayer.type() == QgsMapLayerType.VectorLayer and vlayer.geometryType() == QgsWkbTypes.LineGeometry:
            snapped_feature = vlayer.getFeature(fid)
            # getFeature liefert immer ein QgsFeature, das hat aber keine Geometrie/Attribute, wenn die fid nicht gefunden wird
            if snapped_feature.hasGeometry():
                snapped_geom = snapped_feature.geometry()
                snapped_point = QgsGeometry.fromPointXY(QgsPointXY(x,y))
                #Punktkoordinaten vom canvas in der dort vorliegenden Projektion, diese müssen für lineLocatePoint auf die Projektion des Linienlayers transformiert werden
                if xy_epsg != vlayer.crs().authid():
                    tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(xy_epsg), vlayer.crs(), QgsProject.instance())
                    snapped_point.transform(tr)

                snapped_m = snapped_geom.lineLocatePoint(snapped_point)
                return snapped_m
        else:
            raise ValueError("line_locate_point: Eingangslayer '{}' ist kein Linienlayer".format(vlayer.name()))


def line_interpolate_point(vlayer: QgsVectorLayer, fid: int, distance: float, to_epsg: str = None) -> QgsGeometry:
    '''liefert einen Punkt auf einer Feature-Linie
    <QgsGeometry: PointM (...)>
    Beispiel:
    interpolated_point = line_interpolate_point(iface.activeLayer(),1,20,'EPSG:4326')
    :param vlayer: der Eingangslayer, Typ: Linie, z. B. iface.activeLayer()
    :param fid: Datensatz-ID
    :param distance: Abstand vom Startpunkt der Linie passend zur Projektion dieses Layers
    :param to_epsg: optionale Projektion des Ergebnisses,
    Beispiele:
    iface.mapCanvas().mapSettings().destinationCrs().authid()
    'EPSG:4326'
    defaults: vlayer-Projektion,
    :raises ValueError: bei Layertyp/Geometrietyp != VectorLayer/LineGeometry
    '''
    if vlayer.type() == QgsMapLayerType.VectorLayer and vlayer.geometryType() == QgsWkbTypes.LineGeometry:
        snapped_feature = vlayer.getFeature(fid)
        # getFeature liefert immer ein QgsFeature, das hat aber keine Geometrie/Attribute, wenn die fid nicht gefunden wird
        if snapped_feature.hasGeometry():
            snapped_geom = snapped_feature.geometry()
            snapped_point = snapped_geom.interpolate(distance)
            if to_epsg != vlayer.crs().authid():
                sourceCrs = vlayer.crs()
                destCrs = QgsCoordinateReferenceSystem(to_epsg)
                tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                snapped_point.transform(tr)

            return snapped_point
    else:
        raise ValueError("line_interpolate_point: Eingangslayer '{}' ist kein Linienlayer".format(vlayer.name()))
