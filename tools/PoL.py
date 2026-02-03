#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* PoL == Point-on-Line

********************************************************************

* Date                 : 2025-03-17
* Copyright            : (C) 2024 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

.. note::
    * to import these methods for usage in python console:
    * from LinearReferencing import tools
    * import LinearReferencing.tools.PoL
    * from LinearReferencing.tools.PoL import PoL

********************************************************************
"""
# for the return-value of @classmethod
from __future__ import annotations

import qgis
import numbers
import math
import sys
import os


from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsCoordinateTransform,
    QgsVectorLayer,
    QgsPointXY,
    QgsPoint,
    QgsCoordinateReferenceSystem,
    QgsSpatialIndex,
    QgsWkbTypes,
)

from LinearReferencing.tools.MyDebugFunctions import debug_log
from LinearReferencing.settings.exceptions import *
from LinearReferencing.tools.LinearReferencedGeometry import LinearReferencedGeometry, LinestringStatistics

sqlite_conn = None
try:
    import sqlite3
    sqlite_conn = sqlite3.connect(":memory:")
    sqlite_conn.enable_load_extension(True)
    sqlite_conn.execute('SELECT load_extension("mod_spatialite")')
    sqlite_conn.execute("SELECT InitSpatialMetaData();")
except Exception as e:
    # problems with Macs
    pass
    #print("No sqlite!")

class PoL(LinearReferencedGeometry):
    """Point-On-Line: Point snapped on a line with calculated stationings, coordinates and vertex-metas"""
    # Rev. 2026-01-13

    def __init__(self):
        """constructor without arguments and functionalities
        instances are created via @classmethods init_by_...
        """
        # Rev. 2026-01-13
        super().__init__()

        # snap_x_lyr/snap_y_lyr => mouse-position snapped on reference-line, refLyr-projection
        self.snap_x_lyr: float | None = None
        self.snap_y_lyr: float | None = None

        # snap_x_cvs/snap_y_cvs => mouse-position snapped on reference-line, canvas-projection
        self.snap_x_cvs: float | None = None
        self.snap_y_cvs: float | None = None

        # absolute N-stationing of snapped point in refLyr-units
        # first calculated and base for all other conversions
        self.snap_n_abs: float | None = None

        # relative N-stationing 0...1 as fract of range 0...geometry-length
        self.snap_n_fract: float | None = None

        # interpolated M-value of snapped point (if refLyr M-enabled)
        self.snap_m_abs: float | None = None

        # interpolated M-value of snapped point as fract of range minM...maxM
        # if refLyr M-enabled and geometry is ST_IsValidTrajectory (single parted, ascending M-values, see https://postgis.net/docs/ST_IsValidTrajectory.html)
        self.snap_m_fract: float | None = None

        # interpolated Z-value of snapped point (if refLyr Z-enabled)
        self.snap_z_abs: float | None = None

        # indizes and measurements of vertices before and after the snapped point on reference-line

        # vertex past PoL
        self.next_vertex_index: int | None = None


    @classmethod
    def init_by_stationing(
        cls,
        ref_lyr: QgsVectorLayer,
        ref_fid: int,
        stationing_xyz: float,
        lr_mode: str,
    )->PoL:
        """init with reference-feature + stationing

        Args:
            ref_lyr (QgsVectorLayer)
            ref_fid (int): feature-id
            stationing_xyz (float): numerical stationing from
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Returns:
            PoL
        """
        # Rev. 2026-01-13
        pol_instance = cls()
        if pol_instance.query_reference_geom(ref_lyr, ref_fid):
            if pol_instance.update_stationing(stationing_xyz, lr_mode):
                return pol_instance


    @classmethod
    def init_by_reference_geom(
        cls,
        reference_geom: QgsGeometry,
        ref_crs,
        stationing_xyz: float,
        lr_mode: str,
    )->PoL:
        """init with reference_geom + stationing_from + stationing_to

        Args:
            reference_geom (QgsGeometry): Reference-Geometry
            ref_crs (QgsCoordinateReferenceSystem): Projection of geometry
            stationing_xyz (float): numerical stationing
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Raises:
            GeometryInvalidException

        Returns:
            PoL
        """
        # Rev. 2026-01-13

        pol_instance = cls()
        linestring_statistics = LinestringStatistics(reference_geom)
        if not linestring_statistics.invalid_reason:
            pol_instance.reference_geom = reference_geom
            pol_instance.ref_crs = ref_crs
            pol_instance.linestring_statistics = linestring_statistics
            if pol_instance.update_stationing(stationing_xyz, lr_mode):
                return pol_instance
        else:
            raise GeometryInvalidException(linestring_statistics.invalid_reason)


    @classmethod
    def init_by_snap_to_layer(
        cls,
        ref_lyr: QgsVectorLayer,
        point_geom: (
            QgsGeometry | QgsPointXY | QgsPoint
        ),
        point_geom_crs: QgsCoordinateReferenceSystem,
        snap_tolerance: float,
        ref_lyr_sp_idx: QgsSpatialIndex,
        snap_mode: str = "prefer_nearest",
    )->PoL:
        """init with ref_lyr + point_geom

        Args:
            ref_lyr (QgsVectorLayer): Reference-Layer
            ref_crs (QgsCoordinateReferenceSystem): Projection of geometry
            point_geom (QgsGeometry | QgsPointXY | QgsPoint): Point-Geometry, multiple types possible
            point_geom_crs (QgsCoordinateReferenceSystem): Projection of the points
            snap_tolerance (float): max. distance to reference-line
            ref_lyr_sp_idx (QgsSpatialIndex): Spatial-Index with flags=QgsSpatialIndex.FlagStoreFeatureGeometries, speed-up find a fitting reference-line
            snap_mode (string): prefer_nearest/prefer_start_point. Defaults to prefer_nearest.

        Returns:
            PoL
        """
        # Rev. 2026-01-13
        pol_instance = cls()
        linestring_wkb_types = [
            QgsWkbTypes.LineString,
            QgsWkbTypes.MultiLineString,
            QgsWkbTypes.LineStringZ,
            QgsWkbTypes.MultiLineStringZ,
            QgsWkbTypes.LineStringM,
            QgsWkbTypes.MultiLineStringM,
            QgsWkbTypes.LineStringZM,
            QgsWkbTypes.MultiLineStringZM,
        ]
        if isinstance(ref_lyr, QgsVectorLayer):
            pol_instance.ref_crs = ref_lyr.crs()
            if ref_lyr.dataProvider().wkbType() in linestring_wkb_types:

                if isinstance(point_geom, QgsGeometry):
                    # point_geom = point_geom
                    pass
                elif isinstance(point_geom, QgsPointXY):
                    point_geom = QgsGeometry.fromPointXY(point_geom)
                elif isinstance(point_geom, QgsPoint):
                    point_geom = QgsGeometry.fromPoint(point_geom)
                else:
                    raise ArgumentInvalidException("point_geom",point_geom)

                if isinstance(point_geom, QgsGeometry):

                    # transform point_geom from point_geom_crs to reference-crs
                    point_geom.transform(
                        QgsCoordinateTransform(
                            point_geom_crs,
                            pol_instance.ref_crs,
                            QgsProject.instance(),
                        )
                    )

                    ref_fid = None
                    # Note: nearestNeighbor returns ids in range of their distance
                    if snap_mode == "prefer_nearest":
                        if snap_tolerance > 0:
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom.asPoint(), 1, snap_tolerance
                            )
                        else:
                            # can return multiple fids if equidistant
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom.asPoint(), 1
                            )

                        if ref_fids:
                            ref_fid = ref_fids[0]
                        else:
                            raise GeometryConstructException("no_nearest_neighbor_within_snap_tolerance")

                    elif snap_mode == "prefer_start_point":
                        if snap_tolerance > 0:
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom.asPoint(), 2, snap_tolerance
                            )
                        else:
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom.asPoint(), 2
                            )

                        if ref_fids:
                            # tricky: query two nearestNeighbors and return the one with smallest lineLocatePoint
                            # simulates Advanced Snapping -> "Line Endpoints" (although the *start*-point is used here)
                            len_dict = {}
                            for ref_fid in ref_fids:
                                reference_feature = ref_lyr.getFeature(ref_fid)
                                if reference_feature.isValid() and reference_feature.hasGeometry():
                                    len_dict[ref_fid] = reference_feature.geometry().lineLocatePoint(
                                        point_geom
                                    )

                            # Note: inpredictable if two geometries have the same lineLocatePoint
                            ref_fid = min(len_dict, key=len_dict.get)
                        else:
                            raise GeometryConstructException("no_nearest_neighbor_within_snap_tolerance")

                    if ref_fid is not None:
                        if pol_instance.query_reference_geom(ref_lyr, ref_fid):
                            snap_n_abs = pol_instance.reference_geom.lineLocatePoint(
                                point_geom
                            )
                            if pol_instance.update_stationing(snap_n_abs, "Nabs"):
                                return pol_instance
                    else:
                        raise GeometryConstructException("no_nearest_neighbor_within_snap_tolerance")
            else:
                raise LayerTypeException(ref_lyr.name(),"linestring")
        else:
            raise LayerTypeException(ref_lyr.name(),"vector")


    @classmethod
    def init_by_snap_to_feature(
        cls,
        ref_lyr: QgsVectorLayer,
        ref_fid: int,
        point_geom: (
            QgsGeometry | QgsPointXY | QgsPoint
        ),
        point_geom_crs: QgsCoordinateReferenceSystem,
        snap_tolerance: float = 0,
    )->PoL:
        """init by pre-fetched ref_fid and point-geometry

        Args:
            ref_lyr (QgsVectorLayer): Reference-Layer
            ref_fid (int): Feature-ID
            point_geom (QgsGeometry | QgsPointXY | QgsPoint)
            point_geom_crs (QgsCoordinateReferenceSystem): Projection of the points
            snap_tolerance (float, optional): optional max distance for snapping. Defaults to 0.

        Returns:
            PoL
        """
        # Rev. 2026-01-13

        pol_instance = cls()

        if pol_instance.query_reference_geom(ref_lyr, ref_fid):
            if isinstance(point_geom, QgsGeometry):
                # point_geom = point_geom
                pass
            elif isinstance(point_geom, QgsPointXY):
                point_geom = QgsGeometry.fromPointXY(point_geom)
            elif isinstance(point_geom, QgsPoint):
                point_geom = QgsGeometry.fromPoint(point_geom)
            else:
                raise ArgumentInvalidException("point_geom",point_geom)


            # transform point_geom from point_geom_crs to reference-crs
            point_geom.transform(
                QgsCoordinateTransform(
                    point_geom_crs,
                    pol_instance.ref_crs,
                    QgsProject.instance(),
                )
            )

            abs_dist = pol_instance.reference_geom.distance(point_geom)
            if not snap_tolerance or abs_dist <= snap_tolerance:

                snap_n_abs = pol_instance.reference_geom.lineLocatePoint(point_geom)
                if pol_instance.update_stationing(snap_n_abs, "Nabs"):
                    return pol_instance



    @classmethod
    def init_by_snap_to_geom(
        cls,
        reference_geom,
        ref_crs,
        point_geom: (
            QgsGeometry | QgsPointXY | QgsPoint
        ),
        point_geom_crs: QgsCoordinateReferenceSystem,
        snap_tolerance: float = 0,
    )->PoL:
        """init by reference_geom and point-geometry

        Args:
            reference_geom (QgsGeometry): Reference-Geometry
            ref_crs (QgsCoordinateReferenceSystem): Projection of Geometry
            point_geom (QgsGeometry | QgsPointXY | QgsPoint)
            point_geom_crs (QgsCoordinateReferenceSystem): Projection of the points
            snap_tolerance (float, optional): optional max distance for snapping. Defaults to 0.

        Returns:
            PoL
        """
        # Rev. 2026-01-13
        pol_instance = cls()

        validated_point_geom = None
        if isinstance(point_geom, QgsGeometry):
            validated_point_geom = point_geom
        elif isinstance(point_geom, QgsPointXY):
            validated_point_geom = QgsGeometry.fromPointXY(point_geom)
        elif isinstance(point_geom, QgsPoint):
            validated_point_geom = QgsGeometry.fromPoint(point_geom)
        else:
            raise ArgumentInvalidException("point_geom",point_geom)

        linestring_statistics = LinestringStatistics(reference_geom)
        if not linestring_statistics.invalid_reason:
            pol_instance.reference_geom = reference_geom
            pol_instance.ref_crs = ref_crs
            pol_instance.linestring_statistics = linestring_statistics
            # transform point_geom from point_geom_crs to reference-crs
            validated_point_geom.transform(
                QgsCoordinateTransform(
                    point_geom_crs, ref_crs, QgsProject.instance()
                )
            )

            abs_dist = reference_geom.distance(validated_point_geom)
            if not snap_tolerance or abs_dist <= snap_tolerance:
                snap_n_abs = reference_geom.lineLocatePoint(validated_point_geom)
                if pol_instance.update_stationing(snap_n_abs, "Nabs"):
                    return pol_instance
            else:
                raise GeometryConstructException("no_nearest_neighbor_within_snap_tolerance")
        else:
            raise GeometryInvalidException(linestring_statistics.invalid_reason)



    def get_stationing(self, lr_mode: str) -> float|None:
        """tool-function returning stationing according to lr_mode

        Args:
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Raises:
            NotImplementedError: wrong lr_mode
            PropMissingException: property not numeric

        Returns:
            float|None: stationing_xyz, None if not numeric
        """
        # Rev. 2026-01-13

        if lr_mode == "Nabs":
            if isinstance(self.snap_n_abs,numbers.Number):
                return self.snap_n_abs
            else:
                raise PropMissingException("snap_n_abs")
        elif lr_mode == "Nfract":
            if isinstance(self.snap_n_fract,numbers.Number):
                return self.snap_n_fract
            else:
                raise PropMissingException("snap_n_fract")
        elif lr_mode == "Mabs":
            if isinstance(self.snap_m_abs,numbers.Number):
                return self.snap_m_abs
            else:
                raise PropMissingException("snap_m_abs")
        elif lr_mode == "Mfract":
            if isinstance(self.snap_m_fract,numbers.Number):
                return self.snap_m_fract
            else:
                raise PropMissingException("snap_m_fract")
        else:
            raise NotImplementedError(f"lr_mode {lr_mode}")


    def check_geometry(self,reference_geom:QgsGeometry, check_lr_mode:str)->bool:
        """Checks new geometry for existing PoL-Instance
        F. e. if the user selects another feature
        Check only, internal values stay untouched

        Args:
            reference_geom (QgsGeometry): new geometry
            check_lr_mode (str): Determinates lr_mode for stationing check/recalculation
                Nabs => check current snap_n_abs
                Nfract => check current snap_n_fract
                Mabs => check curent snap_m_abs
                Mfract => check current snap_m_fract

        Returns:
            bool: check_ok?
        """
        # Rev. 2026-01-13
        stationing_xyz = self.get_stationing(check_lr_mode)

        if stationing_xyz is not None:
            return self.check_stationing(reference_geom, stationing_xyz, check_lr_mode)


    def update_geometry(self,reference_geom:QgsGeometry, keep_lr_mode:str)->tuple:
        """Updates the reference-geometry of a PoL-Instance
        F. e. if the user edits the assigned reference-layer-feature-geometry

        Args:
            reference_geom (QgsGeometry): altered geometry
            keep_lr_mode (str): Determinates lr_mode for stationing recalculation
                Nabs => recalculation conserves snap_n_abs and changes all other stationings (and coordinates)
                Nfract => recalculation conserves snap_n_fract and changes all other stationings (and coordinates)
                Mabs => recalculation conserves snap_m_abs and changes all other stationings (and coordinates)
                Mfract => recalculation conserves snap_m_fract and changes all other stationings (and coordinates)

        Returns:
            bool: update_ok?
        """
        # Rev. 2026-01-13
        # step 1: check geometry
        linestring_statistics = LinestringStatistics(reference_geom)

        if not self.linestring_statistics.invalid_reason:
            # step 2: get current stationings for the desired lr_mode
            stationing_xyz = self.get_stationing(keep_lr_mode)

            if stationing_xyz is not None:
                # step 3: recaclulate stationigs: current_stationing with keep_lr_mode on changed geometry
                parsed_stationings = self.parse_stationing(stationing_xyz, keep_lr_mode)
                if parsed_stationings:
                    self.linestring_statistics = linestring_statistics

                    self.reference_geom = reference_geom

                    self.snap_n_abs = parsed_stationings["snap_n_abs"]
                    self.snap_n_fract = parsed_stationings["snap_n_fract"]
                    self.snap_m_abs = parsed_stationings["snap_m_abs"]
                    self.snap_m_fract = parsed_stationings["snap_m_fract"]
                    self.snap_z_abs = parsed_stationings["snap_z_abs"]
                    self.next_vertex_index = parsed_stationings["next_vertex_index"]
                    self.snap_x_lyr = parsed_stationings["snap_x_lyr"]
                    self.snap_y_lyr = parsed_stationings["snap_y_lyr"]
                    self.snap_x_cvs = parsed_stationings["snap_x_cvs"]
                    self.snap_y_cvs = parsed_stationings["snap_y_cvs"]
                    return True
        else:
            raise GeometryInvalidException(linestring_statistics.invalid_reason)


    def update_stationing(self, stationing_xyz: float, lr_mode: str)->bool:
        """parses stationing_xyz to snap_n_abs using self.reference_geom and lr_mode
        Note:
            only updates metadata, if stationing could be parsed
            parse-errors are returned, but not written to error-log

        Args:
            stationing_xyz (float): numerical stationing
            lr_mode (str): LinearReference-Mode: Nabs/Nfract/Mabs/Mfract
                Nabs => Natural stationing
                Nfract => N-value stationing in range 0...1
                Mabs => M-value stationing
                Mfract => M-value stationing in range 0...1

        Returns:
            bool: update successfull?

        """
        # Rev. 2026-01-13
        parsed_stationings = self.parse_stationing(stationing_xyz, lr_mode)
        if parsed_stationings:
            self.snap_n_abs = parsed_stationings["snap_n_abs"]
            self.snap_n_fract = parsed_stationings["snap_n_fract"]
            self.snap_m_abs = parsed_stationings["snap_m_abs"]
            self.snap_m_fract = parsed_stationings["snap_m_fract"]
            self.snap_z_abs = parsed_stationings["snap_z_abs"]
            self.next_vertex_index = parsed_stationings["next_vertex_index"]
            self.snap_x_lyr = parsed_stationings["snap_x_lyr"]
            self.snap_y_lyr = parsed_stationings["snap_y_lyr"]
            self.snap_x_cvs = parsed_stationings["snap_x_cvs"]
            self.snap_y_cvs = parsed_stationings["snap_y_cvs"]
            return True

    def move_stationing(self,delta_n_abs)->bool:
        """moves stationing by delta_n_abs

        If the stationing gets out-of-bounds, it is snapped to start/end


        Args:
            delta_n_abs (float): numerical distance, positive: move up, negative: move down

        Returns:
            bool: update successfull?
        """
        # Rev. 2026-01-13

        old_snap_n_abs = self.snap_n_abs
        new_snap_n_abs = old_snap_n_abs + delta_n_abs
        ref_len = self.reference_geom.length()
        new_snap_n_abs = max(min(new_snap_n_abs,ref_len),0)
        return self.update_stationing(
            new_snap_n_abs, "Nabs"
        )

    def snap_to_end(self)->bool:
        """snaps point to end

        Returns:
            bool: update successfull?
        """
        # Rev. 2026-01-13

        return self.update_stationing(
            self.reference_geom.length(), "Nabs"
        )

    def snap_to_start(self)->bool:
        """snaps point to start

        Returns:
            bool: update successfull
        """
        # Rev. 2026-01-13

        return self.update_stationing(
            0, "Nabs"
        )

    def geometry(self)->tuple:
        """get Point-Geometry for snap_n_abs on reference_geom

        Returns:
            QgsGeometry
        """
        # Rev. 2026-01-13
        if self.reference_geom:
            if self.snap_n_abs is not None:
                point_geom = self.reference_geom.interpolate(self.snap_n_abs)
                if point_geom and not point_geom.isEmpty():
                    return point_geom
                else:
                    raise Exception("point_interpolation_failed")
            else:
                raise Exception("missing_snap_n_abs_from")
        else:
            raise Exception("missing_reference_geom")

