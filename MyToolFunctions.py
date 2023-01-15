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
from PyQt5.QtCore import QCoreApplication
from qgis._core import QgsPointLocator, QgsExpressionContext, QgsExpression, QgsFeature, QgsFields, QgsField, \
    QgsCoordinateReferenceSystem, QgsVectorLayer, QgsPointXY, QgsGeometry, QgsMapLayerType, QgsWkbTypes





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
    :param to_epsg: optionale Projektion des Ergebnisses,
    Beispiele:
    iface.mapCanvas().mapSettings().destinationCrs().authid()
    'EPSG:4326'
    defaults: vlayer-Projektion,
    :raises ValueError: bei Layertyp/Geometrietyp != VectorLayer/LineGeometry
    '''
    if to_epsg is None:
        to_epsg = vlayer.crs().authid()

    if (vlayer is not None) and (fid is not None):
        if vlayer.type() == QgsMapLayerType.VectorLayer and vlayer.geometryType() == QgsWkbTypes.LineGeometry:
            snapped_feature = vlayer.getFeature(fid)
            # getFeature liefert immer ein QgsFeature, das hat aber keine Geometrie/Attribute, wenn die fid nicht gefunden wird
            if snapped_feature.hasGeometry():

                context = QgsExpressionContext()

                ft_dummy = QgsFeature()
                fields = QgsFields()
                fields.append(QgsField('start'))
                fields.append(QgsField('end'))
                fields.append(QgsField('offset'))
                fields.append(QgsField('from_epsg'))
                fields.append(QgsField('to_epsg'))
                ft_dummy.setFields(fields)

                ft_dummy['start'] = min(start, end)
                ft_dummy['end'] = max(start, end)
                ft_dummy['offset'] = offset
                ft_dummy['from_epsg'] = vlayer.crs().authid()
                ft_dummy['to_epsg'] = to_epsg

                ft_dummy.setGeometry(snapped_feature.geometry())
                context.setFeature(ft_dummy)

                if offset:
                    # Bug in Windows? Mit Offset 0 liefert der Ausdruck '<QgsGeometry: LineString EMPTY>'
                    # unter Linux wird der Ausdruck dagegen auch mit offset 0 korrekt ausgewertet
                    qexp_line_segement = QgsExpression(
                        'transform(offset_curve(line_substring($geometry, "start", "end"),"offset"),"from_epsg","to_epsg")')

                else:
                    qexp_line_segement = QgsExpression(
                        'transform(line_substring($geometry, "start", "end"),"from_epsg","to_epsg")')

                segment_geom = qexp_line_segement.evaluate(context)

                return segment_geom
        else:
            raise ValueError("get_segment_geom: Eingangslayer '{}' ist kein Linienlayer".format(vlayer.name()))


def line_locate_point(vlayer: QgsVectorLayer, fid: int, x: float, y: float, from_epsg: str, to_epsg: str=None) -> float:
    '''liefert die Stationierung eines Punktes auf einer Linie für ein bestimmtes Feature,
    Beispiel: m = line_locate_point(iface.activeLayer(),1,50.74566, 6.48769,'EPSG:4326','EPSG:25832')
    :param vlayer: Referenz-Linien-Layer
    :param fid: Feature-ID im Referenz-Linien-Layer
    :param x: Punkt-Koordinate x
    :param y: Punkt-Koordinate y
    :param from_epsg: Projektion der Punkt-Koordinaten
    :param to_epsg: Ziel-Projektion des Ergebnisses, defaults: vlayer-Projektion
    EPSG-Beispiele:
    iface.mapCanvas().mapSettings().destinationCrs().authid()
    'EPSG:4326'
    :raises ValueError: bei Layertyp/Geometrietyp != VectorLayer/LineGeometry
    '''
    if to_epsg is None:
        to_epsg = vlayer.crs().authid()

    qexp_line_locate_point = QgsExpression(
        'line_locate_point($geometry, transform(make_point("x","y"),"from_epsg","to_epsg"))')

    if (vlayer is not None) and (fid is not None):
        if vlayer.type() == QgsMapLayerType.VectorLayer and vlayer.geometryType() == QgsWkbTypes.LineGeometry:
            snapped_feature = vlayer.getFeature(fid)
            # getFeature liefert immer ein QgsFeature, das hat aber keine Geometrie/Attribute, wenn die fid nicht gefunden wird
            if snapped_feature.hasGeometry():
                ft_dummy = QgsFeature()
                fields = QgsFields()
                fields.append(QgsField('x'))
                fields.append(QgsField('y'))
                fields.append(QgsField('from_epsg'))
                fields.append(QgsField('to_epsg'))
                ft_dummy.setFields(fields)

                context = QgsExpressionContext()
                ft_dummy['x'] = x
                ft_dummy['y'] = y
                ft_dummy['from_epsg'] = from_epsg
                ft_dummy['to_epsg'] = to_epsg

                ft_dummy.setGeometry(snapped_feature.geometry())
                # sonst wird $geometry im expression nicht aufgelöst
                context.setFeature(ft_dummy)
                snapped_m = qexp_line_locate_point.evaluate(context)

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
    if to_epsg is None:
        to_epsg = vlayer.crs().authid()

    if vlayer.type() == QgsMapLayerType.VectorLayer and vlayer.geometryType() == QgsWkbTypes.LineGeometry:

        snapped_feature = vlayer.getFeature(fid)
        # getFeature liefert immer ein QgsFeature, das hat aber keine Geometrie/Attribute, wenn die fid nicht gefunden wird
        if snapped_feature.hasGeometry():
            context = QgsExpressionContext()

            qexp_line_interpolate_point = QgsExpression(
                'transform(line_interpolate_point($geometry, "distance"),"from_epsg","to_epsg")')

            ft_dummy = QgsFeature()
            fields = QgsFields()
            fields.append(QgsField('fid'))
            fields.append(QgsField('distance'))
            fields.append(QgsField('from_epsg'))
            fields.append(QgsField('to_epsg'))
            ft_dummy.setFields(fields)

            ft_dummy['distance'] = distance
            ft_dummy['fid'] = fid
            ft_dummy['from_epsg'] = vlayer.crs().authid()
            ft_dummy['to_epsg'] = to_epsg

            ft_dummy.setGeometry(snapped_feature.geometry())

            context.setFeature(ft_dummy)

            # <QgsGeometry: PointM (322851.50040797801921144 5626978.42803511023521423 67.40000000000000568)>
            projected_point = qexp_line_interpolate_point.evaluate(context)

            return projected_point
    else:
        raise ValueError("line_interpolate_point: Eingangslayer '{}' ist kein Linienlayer".format(vlayer.name()))


class OneLayerFilter(QgsPointLocator.MatchFilter):
    '''Filter für das Snapping:
    Nur auf Features eines bestimmten Layers Snappen'''

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
