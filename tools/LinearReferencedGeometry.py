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

import qgis
import numbers
import math
import sys
import os

from typing import Self


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
    QgsAbstractGeometry,
    QgsVertexId
)

from LinearReferencing.settings.exceptions import *

from LinearReferencing.tools.MyDebugFunctions import (
    get_debug_pos,
    get_debug_file_line,
    debug_log,
)

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

class LinearReferencedGeometry:
    """Root-Class for linear referenced geometries defined by reference-geom and stationing(s) (+ offset)"""
    # Rev. 2026-01-13

    def __init__(self):
        """constructor without arguments and functionalities
        instances are created via @classmethods init_by_...
        """
        # Rev. 2026-01-13


        # referenced geometry
        self.reference_geom: QgsGeometry | None = None

        # projection of referenced geometry
        self.ref_crs: QgsCoordinateReferenceSystem | None = None

        # if geometry defined by layer and feature-id
        # clientside purpose, storage to DataLyr, internally only used to define self.reference_geom and self.ref_crs
        self.ref_fid: int | None = None


        self.linestring_statistics: LinestringStatistics | None = None

    def query_reference_geom(self, ref_lyr: QgsVectorLayer, ref_fid: int)->bool:
        """query geometry from layer via feature-id and performs check
            sets self.reference_geom, self.ref_crs, self.ref_fid, self.linestring_statistics

        Args:
            ref_lyr (QgsVectorLayer): Reference-Layer
            ref_fid (int): fid of Reference-Feature

        Raises:
            GeometryInvalidException
            FeatureWithoutGeometryException
            FeatureInvalidException
            ArgumentInvalidException

        Returns:
            bool: valid geometry found
        """
        # Rev. 2026-01-13

        if isinstance(ref_lyr, QgsVectorLayer):
            reference_feature = ref_lyr.getFeature(ref_fid)
            if reference_feature.isValid():
                if reference_feature.hasGeometry():
                    linestring_statistics = LinestringStatistics(reference_feature.geometry())
                    if not linestring_statistics.invalid_reason:
                        self.reference_geom = reference_feature.geometry()
                        self.ref_crs = ref_lyr.crs()
                        self.ref_fid = ref_fid
                        self.linestring_statistics = linestring_statistics
                        return True
                    else:
                        raise GeometryInvalidException(linestring_statistics.invalid_reason, f"{ref_lyr.name()} #{ref_fid}")
                else:
                    raise FeatureWithoutGeometryException(ref_lyr.name(),ref_fid)
            else:
                raise FeatureInvalidException(ref_lyr.name(),ref_fid)
        else:
            raise ArgumentInvalidException("ref_lyr",ref_lyr)




    def __str__(self):
        """debug, stringify, all not callable and not dunderscored properties aligned"""
        # Rev. 2026-01-13
        result_str = "\n"
        property_list = [
            prop
            for prop in dir(self)
            if not prop.startswith("__") and not callable(getattr(self, prop))
        ]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            if prop == "reference_geom":
                result_str += (
                    f"{prop:<{max_len}}    {str(getattr(self, prop)):.50}...\n"
                )
            else:
                result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str



    def nabs_to_mfract(self,m_fract:float)->float:
        """implement on demand..."""
        # Rev. 2026-01-13
        pass

    def mfract_to_mabs(self,m_fract:float)->float:
        """Convert mfract to mabs

        Args:
            m_fract (float)

        Returns:
            float: converted value
        """
        # Rev. 2026-01-13
        if self.linestring_statistics.m_valid:
            if m_fract == 0:
                return self.linestring_statistics.m_min
            elif m_fract == 1:
                return self.linestring_statistics.m_max
            elif 0 < m_fract < 1:
                return self.linestring_statistics.m_min + m_fract * (self.linestring_statistics.m_max - self.linestring_statistics.m_min)
            else:
                raise PropOutOfRangeException("m_fract",m_fract,0,1)
        else:
            raise GeometryNotMValidException(self.linestring_statistics.m_error)

    def mabs_to_nabs(self,m_abs:float)->float:
        """Return calculated n-stationing
        either sqlite3 + ST_IsValidTrajectory
        or iterate through vertices and return interpolated m of the first matching vertex-pair

        Geometry must be m-enabled, single-parted and have strictly ascending M-values

        Args:
            m_abs(float)

        Returns:
            float
        """
        # Rev. 2026-01-13

        if self.linestring_statistics.m_valid:
            if m_abs == self.linestring_statistics.m_min:
                return 0
            elif m_abs == self.linestring_statistics.m_max:
                return self.reference_geom.length()
            elif self.linestring_statistics.m_min < m_abs < self.linestring_statistics.m_max:
                if sqlite_conn:
                    sqlite_cur = sqlite_conn.cursor()
                    query = "SELECT ST_Line_Locate_Point(ST_GeomFromWkb(:geom_wkb), ST_TrajectoryInterpolatePoint(ST_GeomFromWkb(:geom_wkb), :m)) * ST_Length(ST_GeomFromWkb(:geom_wkb))"
                    sqlite_result = sqlite_cur.execute(query, {"geom_wkb": self.reference_geom.asWkb(),"m":m_abs})
                    sqlite_row = sqlite_result.fetchone()
                    return sqlite_row[0]
                else:
                    last_vertex = None
                    n = 0
                    for current_vertex in self.reference_geom.constGet().vertices():
                        if last_vertex is not None:
                            if last_vertex.m() <= m_abs <= current_vertex.m():
                                delta_n = last_vertex.distance(current_vertex)
                                delta_m_rel = (m_abs - last_vertex.m()) / (
                                    current_vertex.m() - last_vertex.m()
                                )
                                n += delta_n * delta_m_rel
                                return n
                            else:
                                # calculated pythagorean distance between the vertices
                                n += last_vertex.distance(current_vertex)
                        last_vertex = current_vertex

                    # should never happen, if m_min <= m <= m_max
                    raise PropOutOfRangeException("m_abs",m_abs,self.linestring_statistics.m_min,self.linestring_statistics.m_max)
            else:
                raise PropOutOfRangeException("m_abs",m_abs,self.linestring_statistics.m_min,self.linestring_statistics.m_max)
        else:
            raise GeometryNotMValidException(self.linestring_statistics.m_error)



    def mfract_to_nabs(self, m_fract: float) -> float:
        """calculate snap_n_abs from snap_m_fract
            returns stationing for the first matching vertex-pair for m-valid linestring-m-geometries
            uses mabs_to_nabs, so either via sqlite or by vertex-iteration

        Args:
            abstr_geom (QgsGeometry|QgsAbstractGeometry)
            m_fract (float): range 0...1

        Raises:
            TypeError: wrong geometry type

        Returns:
            float
        """
        # Rev. 2026-01-13
        if self.linestring_statistics.m_valid:
            # no unnecessary calculation for special cases
            return self.mabs_to_nabs(self.mfract_to_mabs(m_fract))
        else:
            raise GeometryNotMValidException(self.linestring_statistics.m_error)

    def nfract_to_nabs(self, n_fract:float) -> float:
        """calculate snap_n_abs from n_fract

        Args:
            n_fract (float)

        Returns:
            float nabs
        """
        # Rev. 2026-01-13
        if 0 <= n_fract <= 1:
            return self.reference_geom.length() * n_fract
        else:
            raise PropOutOfRangeException("n_fract",n_fract,0,1)


    def nabs_to_nabs(self, n_abs: float) -> float | None:
        """check and return n_abs, dummy

        Args:
            abstr_geom (QgsGeometry|QgsAbstractGeometry)
            n_abs (float)

        Returns:
            float | None: checked n_abs
        """
        # Rev. 2026-01-13

        if 0 <= n_abs <= self.reference_geom.length():
            return n_abs
        else:
            raise PropOutOfRangeException("n_abs",n_abs,0,self.reference_geom.length())



    def parse_stationing(self, stationing_xyz: float, lr_mode: str) -> dict:
        """parses numeric stationing with self.reference_geom and lr_mode
            this function uses PoL-properties, but does not alter them
            meant as: try this stationing and return the parsed values

        Args:
            stationing_xyz (float): numerical stationing from/to
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Raises:
            NotImplementedError
            GeometryConstructException
            ArgumentInvalidException
            PropMissingException

        Returns:
            dict: dict with parse-results, all keys, but some values may be None
        """
        # Rev. 2026-01-13
        result = {
            "snap_n_abs": None,
            "snap_n_fract": None,
            "snap_m_abs": None,
            "snap_m_fract": None,
            "snap_z_abs": None,
            "next_vertex_index": None,
            "snap_x_lyr": None,
            "snap_y_lyr": None,
            "snap_x_cvs": None,
            "snap_y_cvs": None,
        }
        snap_n_abs = None

        if self.reference_geom is not None:

            try:
                # check if value is numeric:
                stationing_xyz = float(stationing_xyz)
            except:
                raise ArgumentInvalidException("stationing_xyz",stationing_xyz)

            snap_n_abs = None
            if lr_mode == "Nabs":
                snap_n_abs = self.nabs_to_nabs(stationing_xyz)
            elif lr_mode == "Nfract":
                snap_n_abs = self.nfract_to_nabs(stationing_xyz)
            elif lr_mode == "Mabs":
                snap_n_abs = self.mabs_to_nabs(stationing_xyz)
            elif lr_mode == "Mfract":
                snap_n_abs = self.mfract_to_nabs(stationing_xyz)
            else:
                raise NotImplementedError(f"lr_mode '{lr_mode}'")

            if snap_n_abs is not None:
                result["snap_n_abs"] = snap_n_abs
                interpolated_point = self.reference_geom.interpolate(snap_n_abs)

                if not interpolated_point.isEmpty():
                    result["snap_x_lyr"] = interpolated_point.asPoint().x()
                    result["snap_y_lyr"] = interpolated_point.asPoint().y()
                    result["snap_n_fract"] = (
                        snap_n_abs / self.reference_geom.length()
                    )

                    # Note: no check "is_valid_trajectory", just get interpolated m-value at snap_n_abs_from-position
                    if self.linestring_statistics.m_enabled:
                        snap_m_abs = interpolated_point.constGet().m()
                        if isinstance(
                            snap_m_abs, numbers.Number
                        ) and not math.isnan(snap_m_abs):
                            result["snap_m_abs"] = snap_m_abs
                            m_min = self.linestring_statistics.m_min
                            m_max = self.linestring_statistics.m_max
                            # no 'm_valid'-check
                            if (
                                m_min is not None
                                and m_max is not None
                                and m_min < m_max
                            ):
                                result["snap_m_fract"] = (snap_m_abs - m_min) / (
                                    m_max - m_min
                                )

                    if self.linestring_statistics.z_enabled:
                        snap_z_abs = interpolated_point.constGet().z()
                        if isinstance(
                            snap_z_abs, numbers.Number
                        ) and not math.isnan(snap_z_abs):
                            result["snap_z_abs"] = snap_z_abs

                    # Snapped point in canvase-projection
                    interpolated_point.transform(
                        QgsCoordinateTransform(
                            self.ref_crs,
                            qgis.utils.iface.mapCanvas()
                            .mapSettings()
                            .destinationCrs(),
                            QgsProject.instance(),
                        )
                    )
                    result["snap_x_cvs"] = interpolated_point.asPoint().x()
                    result["snap_y_cvs"] = interpolated_point.asPoint().y()

                    """calculate vertex-metas via self.reference_geom and self.snap_n_abs_from"""

                    point_on_line = self.reference_geom.closestSegmentWithContext(
                        interpolated_point.asPoint()
                    )
                    result["next_vertex_index"] = point_on_line[2]

                    return result
                else:
                    raise GeometryConstructException("interpolation empty")
        else:
            raise PropMissingException("reference_geom")


    @staticmethod
    def check_stationing(reference_geom:QgsGeometry, stationing_xyz:float, lr_mode:str)->bool:
        """check numerical stationing for geometry

        Args:
            reference_geom (QgsGeometry):
            stationing_xyz (float): numerical stationing
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Raises:
            PropOutOfRangeException
            GeometryNotMValidException
            NotImplementedError
            ArgumentInvalidException
            GeometryInvalidException

        Returns:
            bool: check_ok?
        """
        # Rev. 2026-01-13
        linestring_statistics = LinestringStatistics(reference_geom)
        if not linestring_statistics.invalid_reason:
            if isinstance(stationing_xyz, numbers.Number) and not math.isnan(
                stationing_xyz
            ):
                if lr_mode == 'Nabs':
                    if 0 <= stationing_xyz <= linestring_statistics.length:
                        return True
                    else:
                        raise PropOutOfRangeException(f"stationing {lr_mode}",stationing_xyz,0,linestring_statistics.length)
                elif lr_mode == 'Nfract':
                    if 0 <= stationing_xyz <= 1:
                        return True
                    else:
                        raise PropOutOfRangeException(f"stationing {lr_mode}",stationing_xyz,0,1)
                elif lr_mode == 'Mabs':
                    if linestring_statistics.m_enabled:
                        if linestring_statistics.m_valid:
                            if linestring_statistics.m_min <= stationing_xyz <= linestring_statistics.m_max:
                                return True
                            else:
                                raise PropOutOfRangeException(f"stationing {lr_mode}",stationing_xyz,linestring_statistics.m_min,linestring_statistics.m_max)
                        else:
                            raise GeometryNotMValidException(linestring_statistics.m_error)
                    else:
                        raise GeometryNotMValidException(f"Geometry-Type {linestring_statistics.wkbType_name}")

                elif lr_mode == 'Mfract':
                    if linestring_statistics.m_enabled:
                        if linestring_statistics.m_valid:
                            if 0 <= stationing_xyz <= 1:
                                return True
                            else:
                                raise PropOutOfRangeException(f"stationing {lr_mode}",stationing_xyz,0,1)
                        else:
                            raise GeometryNotMValidException(linestring_statistics.m_error)
                    else:
                        raise GeometryNotMValidException(f"Geometry-Type {linestring_statistics.wkbType_name}")
                else:
                    raise NotImplementedError(f"lr_mode {lr_mode}")
            else:
                raise ArgumentInvalidException("stationing_xyz",stationing_xyz)
        else:
            raise GeometryInvalidException(linestring_statistics.invalid_reason)




    def __copy__(self)-> Self:
        """implemented to avoid pickle-error for QgsGeometry"""
        # Rev. 2026-01-13
        my_clone = self.__class__()

        for prop_name in self.__dir__():
            if not prop_name.startswith("__") and not callable(
                getattr(self, prop_name)
            ):
                my_clone.__setattr__(prop_name, getattr(self, prop_name))

        return my_clone

class LinestringStatistics:
    """analyze QgsGeometry and fetch some metadata"""
    # Rev. 2026-01-13

    def __init__(self, reference_geom: QgsGeometry):
        """Constructor

        Args:
            reference_geom (QgsGeometry)
        """
        # Rev. 2026-01-13

        self.num_vertices = None
        self.length = None
        self.partCount = None
        self.wkbType = None
        self.wkbType_name = None
        # Geometry-Type (multi-)Linestring-(Z)M
        self.m_enabled = None
        # additional validation for Mabs-Stationing (single parted, strictly ascending M-Values)
        self.m_valid = None
        # m-validation-error for user
        self.m_error = None
        # if self.m_valid: min m == first vertex M
        self.m_min = None
        # if self.m_valid: max m == last vertex M
        self.m_max = None

        self.z_enabled = None

        # single parted or multi-parted without gaps (mergable)
        self.n_valid = None

        # geometry-parse-error
        self.invalid_reason = None


        if isinstance(reference_geom,QgsGeometry):
            abstr_geom = reference_geom.constGet()

            # first detect invalid geometries:
            # https://api.qgis.org/api/classQgsGeometry.html#a8faaa438425e486a47a26a19fd9f126c
            # => Validates geometry and produces a list of geometry errors.
            geom_validation_result = reference_geom.validateGeometry()

            # empty list if geometry is valid
            if not geom_validation_result:

                # check the geometry-type
                linestring_wkb_types = [
                    QgsWkbTypes.LineString25D,
                    QgsWkbTypes.MultiLineString25D,
                    QgsWkbTypes.LineString,
                    QgsWkbTypes.MultiLineString,
                    QgsWkbTypes.LineStringZ,
                    QgsWkbTypes.MultiLineStringZ,
                    QgsWkbTypes.LineStringM,
                    QgsWkbTypes.MultiLineStringM,
                    QgsWkbTypes.LineStringZM,
                    QgsWkbTypes.MultiLineStringZM,
                ]

                # check M-enabled geometry-type
                linestring_m_wkb_types = [
                    QgsWkbTypes.LineStringM,
                    QgsWkbTypes.LineStringZM,
                    QgsWkbTypes.MultiLineStringM,
                    QgsWkbTypes.MultiLineStringZM,
                ]

                # check Z-enabled geometry-type
                linestring_z_wkb_types = [
                    QgsWkbTypes.LineStringZ,
                    QgsWkbTypes.LineStringZM,
                    QgsWkbTypes.MultiLineStringZ,
                    QgsWkbTypes.MultiLineStringZM,
                ]

                multi_linestring_wkb_types = [
                    QgsWkbTypes.MultiLineString25D,
                    QgsWkbTypes.MultiLineString,
                    QgsWkbTypes.MultiLineStringZ,
                    QgsWkbTypes.MultiLineStringM,
                    QgsWkbTypes.MultiLineStringZM,
                ]


                single_linestring_wkb_types = [
                    QgsWkbTypes.LineString25D,
                    QgsWkbTypes.LineString,
                    QgsWkbTypes.LineStringZ,
                    QgsWkbTypes.LineStringM,
                    QgsWkbTypes.LineStringZM,
                ]



                if reference_geom.wkbType() in linestring_wkb_types:
                    if reference_geom.wkbType() in multi_linestring_wkb_types:
                        if reference_geom.constGet().partCount() == 1:
                            # only use the first
                            #abstr_geom = reference_geom.constGet().lineStringN(0)
                            self.n_valid = True
                        else:
                            merged_geom = reference_geom.mergeLines()
                            if merged_geom.wkbType() in single_linestring_wkb_types:
                                #abstr_geom = merged_geom.constGet()
                                # no gap => mergable
                                # Note: QGis merges splitted but connected geometries automatically on save edits
                                self.n_valid = True
                            else:
                                #return None, f"curveSubstring failed, Geometry multi-parted with gaps"
                                self.n_valid = False
                    else:
                        self.n_valid = True


                    self.m_enabled = reference_geom.wkbType() in linestring_m_wkb_types
                    self.z_enabled = reference_geom.wkbType() in linestring_z_wkb_types

                    if self.m_enabled:
                        try:
                            m_min, m_max = self.check_m_valid(reference_geom)
                            self.m_min = m_min
                            self.m_max = m_max
                            self.m_valid = True
                        except GeometryNotMValidException as e:
                            self.m_valid = False
                            self.m_error = e.invalid_reason



                    self.num_vertices = abstr_geom.nCoordinates()
                    self.length = abstr_geom.length()
                    self.partCount = abstr_geom.partCount()
                    self.wkbType = reference_geom.wkbType()
                    self.wkbType_name = reference_geom.wkbType().name

                else:
                    #raise TypeError('reference_geom_not_type_linestring')
                    self.invalid_reason = 'reference_geom_not_type_linestring'
            else:
                self.invalid_reason = str(geom_validation_result)
        else:
            # raise TypeError('reference_geom_not_type_geometry')
            self.invalid_reason ='reference_geom_not_type_geometry'

    @staticmethod
    def check_m_valid(abstr_geom:QgsGeometry|QgsAbstractGeometry)->tuple:
        """Check M-validity of geometry
        either sqlite3 + ST_IsValidTrajectory
        or iterate through all vertices and detect missing or not ascending vertice-m-values

        Geometry must be m-enabled, single-parted and have strictly ascending M-values

        Args:
            abstr_geom (QgsGeometry|QgsAbstractGeometry)

        Raises:
            GeometryNotMValidException
            ArgumentInvalidException

        Returns:
            tuple: (m_min,m_max)
        """
        # Rev. 2026-01-13

        if isinstance(abstr_geom,QgsGeometry):
            abstr_geom = abstr_geom.constGet()


            linestring_m_wkb_types = [
                QgsWkbTypes.LineStringM,
                QgsWkbTypes.LineStringZM,
                QgsWkbTypes.MultiLineStringM,
                QgsWkbTypes.MultiLineStringZM,
            ]

            if abstr_geom.wkbType() in linestring_m_wkb_types:
                if abstr_geom.partCount() == 1:
                    if sqlite_conn:
                        sqlite_cur = sqlite_conn.cursor()
                        query = "SELECT ST_IsValidTrajectory(ST_GeomFromWkb(:geom_wkb))"
                        sqlite_result = sqlite_cur.execute(query, {"geom_wkb": abstr_geom.asWkb()})
                        sqlite_row = sqlite_result.fetchone()
                        m_valid = bool(sqlite_row[0])
                        if m_valid:
                            first_vertex = abstr_geom.vertexAt(QgsVertexId(0, 0, 0))
                            last_vertex = abstr_geom.vertexAt(QgsVertexId(0, 0, abstr_geom.nCoordinates() - 1))
                            # ST_IsValidTrajectory => M-values strictly ascending => m_min at first, m_max at last vertex
                            m_min = first_vertex.m()
                            m_max = last_vertex.m()
                            return m_min,m_max
                        else:
                            raise GeometryNotMValidException("ST_IsValidTrajectory failed")
                    else:
                        vc = 0
                        last_m = None
                        m_min = sys.float_info.max
                        m_max = sys.float_info.min
                        for vertex in abstr_geom.vertices():
                            if not math.isnan(vertex.m()):
                                m_min = min(m_min, vertex.m())
                                m_max = max(m_max, vertex.m())
                                if last_m is not None:
                                    if vertex.m() <= last_m:
                                        raise GeometryNotMValidException(f"Vertex #{vc} => m_not_ascending")
                                last_m = vertex.m()
                            else:
                                raise GeometryNotMValidException(f"Vertex #{vc} => m_not_numeric!")
                            vc += 1

                        return m_min,m_max
                else:
                    raise GeometryNotMValidException(f"Geometry multiparted")
            else:
                raise GeometryNotMValidException(f"wkbType '{abstr_geom.wkbType()}' not linestring")
        else:
            raise ArgumentInvalidException("abstr_geom",abstr_geom)

    def __str__(self):
        """stringify implemented for debug-purpose"""
        # Rev. 2026-01-13
        result_str = ""
        property_list = [
            prop
            for prop in dir(self)
            if not prop.startswith("__") and not callable(getattr(self, prop))
        ]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str




