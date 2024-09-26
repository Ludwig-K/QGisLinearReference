#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* some Tool-Functions

********************************************************************

* Date                 : 2023-09-15
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

.. note::
    * to import these methods for usage in python console:
    * from LinearReferencing import tools
    * import LinearReferencing.tools.MyTools
    * from LinearReferencing.tools.MyTools import re_open_attribute_tables

********************************************************************
"""
from __future__ import annotations
import qgis
import sys
import os
import numbers
import typing
import math
import locale
import inspect
from PyQt5 import QtCore, QtWidgets, QtGui
from qgis import core
from LinearReferencing.tools.MyDebugFunctions import debug_print, debug_log
# from enum import Flag, auto
import sqlite3
import re
from LinearReferencing.i18n.SQLiteDict import SQLiteDict
# global variable
# get language-dependend error-messages
MY_DICT = SQLiteDict()

# one global sqlite/spatialite-connection for usage in some below functions
sqlite_conn = sqlite3.connect(':memory:')
sqlite_conn.enable_load_extension(True)
sqlite_conn.execute('SELECT load_extension("mod_spatialite")')
sqlite_conn.execute('SELECT InitSpatialMetaData();')

locale.setlocale(locale.LC_ALL, '')




class PoLFeature:
    """Point-On-Line-Feature
    Point snapped on a line with calculated stationings
    only contains simple and clonable properties
    for runtime-usage, measurement without data-feature
    or for editing of stored vector-layer-feature in case of PolEvt
    """

    # optional fid of data-feature for edit/save-purpose
    data_fid = None

    # allow multiple versions for geometry-input
    # ref_fid =>  default, get geometry from layer by ref_lyr_id and ref_fid
    # cache => cache any geometry
    geom_defined_by = 'ref_fid'

    # pixel-on-screen-coordinates used for check mouse-down == mouse-up
    screen_x = None
    screen_y = None

    # mouse-coordinates in canvas projection
    map_x = None
    map_y = None


    # Layer on which the values are calculated
    ref_lyr_id = None

    # FID of snapped reference-line
    ref_fid = None

    # for geom_defined_by 'cache': reference-geometry (post-processing)
    cached_geom = None

    # projection of reference_geom and cached_geom
    # type str, f.e. 'EPSG:25832'
    reference_authid = None


    # snap_x/snap_y => mouse-position snapped on reference-line, refLyr-projection
    snap_x = None
    snap_y = None
    # interpolated Z-value of snapped point (if refLyr Z-enabled)
    snap_z_abs = None

    # absolute N-stationing of snapped point in refLyr-units
    snap_n_abs = None

    # relative N-stationing 0...1 as fract of range 0...geometry-length
    snap_n_fract = None

    # interpolated M-value of snapped point (if refLyr M-enabled)
    snap_m_abs = None

    # interpolated M-value of snapped point as fract of range minM...maxM
    # if refLyr M-enabled and geometry is ST_IsValidTrajectory (single parted, ascending M-values, see https://postgis.net/docs/ST_IsValidTrajectory.html)
    snap_m_fract = None

    # validity
    is_valid = False

    # reason for not is_valid
    last_error = 'not_initialized'



    def __init__(self):
        pass


    def line_locate_event(self, event:qgis.gui.QgsMapMouseEvent, reference_layer:qgis.core.QgsVectorLayer, ref_fid:int):
        """calculate stationing via lineLocatePoint for single feature, independend from distance, but fixed ref_fid instead of snap
        :param event: MapMouseEvent, coordinates are transformed from canvas-crs to layer-crs
        :param reference_layer: Reference-Layer, type linestringXYZ
        :param ref_fid: ID of reference-feature

        """
        self.geom_defined_by = 'ref_fid'
        self.ref_fid = ref_fid
        linestring_wkb_types = [
            qgis.core.QgsWkbTypes.LineString25D,
            qgis.core.QgsWkbTypes.MultiLineString25D,
            qgis.core.QgsWkbTypes.LineString,
            qgis.core.QgsWkbTypes.MultiLineString,
            qgis.core.QgsWkbTypes.LineStringZ,
            qgis.core.QgsWkbTypes.MultiLineStringZ,
            qgis.core.QgsWkbTypes.LineStringM,
            qgis.core.QgsWkbTypes.MultiLineStringM,
            qgis.core.QgsWkbTypes.LineStringZM,
            qgis.core.QgsWkbTypes.MultiLineStringZM,
        ]
        if reference_layer.type() == qgis.core.QgsMapLayerType.VectorLayer and reference_layer.dataProvider().wkbType() in linestring_wkb_types:
            self.ref_lyr_id = reference_layer.id()
            self.reference_authid = reference_layer.crs().authid()
            reference_geom = self.get_reference_geom()
            if reference_geom:
                point_geom = qgis.core.QgsGeometry.fromPointXY(event.mapPoint())
                point_geom.transform(qgis.core.QgsCoordinateTransform(qgis.utils.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsCoordinateReferenceSystem(self.reference_authid), qgis.core.QgsProject.instance()))
                snap_n_abs = reference_geom.lineLocatePoint(point_geom)
                self.recalc_by_stationing(snap_n_abs,'Nabs')
        else:
            self.is_valid = False
            self.last_error = MY_DICT.tr('exc_reference_layer_type_not_suitable',reference_layer.type())



    def snap_to_layer(self,event:qgis.gui.QgsMapMouseEvent,reference_layer:qgis.core.QgsVectorLayer,filter_feature_id:int = None, paranoid:bool = False)->qgis.core.QgsPointLocator.Match:

        if paranoid:
            linestring_wkb_types = [
                qgis.core.QgsWkbTypes.LineString25D,
                qgis.core.QgsWkbTypes.MultiLineString25D,
                qgis.core.QgsWkbTypes.LineString,
                qgis.core.QgsWkbTypes.MultiLineString,
                qgis.core.QgsWkbTypes.LineStringZ,
                qgis.core.QgsWkbTypes.MultiLineStringZ,
                qgis.core.QgsWkbTypes.LineStringM,
                qgis.core.QgsWkbTypes.MultiLineStringM,
                qgis.core.QgsWkbTypes.LineStringZM,
                qgis.core.QgsWkbTypes.MultiLineStringZM,
            ]
            if reference_layer.type() == qgis.core.QgsMapLayerType.VectorLayer and reference_layer.dataProvider().wkbType() in linestring_wkb_types:
                # set and enable snapping-configuration for this layer, which always will be self.derived_settings.refLyr
                # not necessary, cause already done for  by sys_check_settings > sys_connect_reference_layer
                my_snap_config = qgis.core.QgsProject.instance().snappingConfig()
                my_snap_config.setEnabled(True)
                my_snap_config.setMode(qgis.core.QgsSnappingConfig.AdvancedConfiguration)

                type_flag = qgis.core.Qgis.SnappingTypes(qgis.core.Qgis.SnappingType.Segment | qgis.core.Qgis.SnappingType.LineEndpoint)
                my_snap_config.setIndividualLayerSettings(reference_layer, qgis.core.QgsSnappingConfig.IndividualLayerSettings(enabled=True, type=type_flag, tolerance=10, units=qgis.core.QgsTolerance.UnitType.Pixels))
                my_snap_config.setIntersectionSnapping(False)
                qgis.core.QgsProject.instance().setSnappingConfig(my_snap_config)
            else:
                self.is_valid = False
                self.last_error = MY_DICT.tr('exc_reference_layer_type_not_suitable',reference_layer.type())
                return

        event.snapPoint()
        match = event.mapPointMatch()

        if match.isValid() and match.layer() and match.layer() == reference_layer:
            if filter_feature_id and filter_feature_id != match.featureId():
                # construct invalid match as return value, match.isValid() == False
                match = qgis.core.QgsPointLocator.Match()
            else:
                # default: no ref_fid or ref_fid fitting to match
                self.ref_lyr_id = match.layer().id()
                self.ref_fid = match.featureId()
                self.reference_authid = match.layer().crs().authid()

                layer_point = qgis.core.QgsPoint(match.point())
                layer_point.transform(qgis.core.QgsCoordinateTransform(qgis.utils.iface.mapCanvas().mapSettings().destinationCrs(), match.layer().crs(), qgis.core.QgsProject.instance()))

                reference_geom = match.layer().getFeature(match.featureId()).geometry()

                snap_n_abs = reference_geom.lineLocatePoint(qgis.core.QgsGeometry.fromPoint(layer_point))

                self.recalc_by_stationing(snap_n_abs,'Nabs')


        return match

    def set_cached_geom(self,cached_geom:qgis.core.QgsGeometry,reference_authid:str):
        """
        :param cached_geom:
        :param reference_authid: authority identifier for the CRS, f.e. 'EPSG:25832'
        :return:
        """

        self.geom_defined_by = 'cache'
        self.cached_geom = cached_geom
        self.reference_authid = reference_authid


    def set_ref_fid(self,reference_layer:qgis.core.QgsVectorLayer,ref_fid:int):
        self.ref_lyr_id = None
        self.reference_authid = None
        self.ref_fid = None
        linestring_wkb_types = [
            qgis.core.QgsWkbTypes.LineString25D,
            qgis.core.QgsWkbTypes.MultiLineString25D,
            qgis.core.QgsWkbTypes.LineString,
            qgis.core.QgsWkbTypes.MultiLineString,
            qgis.core.QgsWkbTypes.LineStringZ,
            qgis.core.QgsWkbTypes.MultiLineStringZ,
            qgis.core.QgsWkbTypes.LineStringM,
            qgis.core.QgsWkbTypes.MultiLineStringM,
            qgis.core.QgsWkbTypes.LineStringZM,
            qgis.core.QgsWkbTypes.MultiLineStringZM,
        ]
        if reference_layer.type() == qgis.core.QgsMapLayerType.VectorLayer and reference_layer.dataProvider().wkbType() in linestring_wkb_types:
            reference_feature = reference_layer.getFeature(ref_fid)
            if reference_feature.isValid() and reference_feature.hasGeometry():
                self.ref_lyr_id = reference_layer.id()
                self.reference_authid = reference_layer.crs().authid()
                self.ref_fid = ref_fid
                self.geom_defined_by = 'ref_fid'
            else:
                self.is_valid = False
                self.last_error = MY_DICT.tr('exc_reference_feature_invalid',self.ref_fid,self.reference_layer.name())
        else:
            self.is_valid = False
            self.last_error = MY_DICT.tr('exc_reference_layer_type_not_suitable',reference_layer.type())



    def get_reference_geom(self) -> qgis.core.QgsGeometry:
        """
        mutiple variants for getting the reference-geometry are implemented
        'ref_fid' (default) uses self.ref_lyr_id and self.ref_fid
        'cache' uses self.cached_geom with self.reference_authid
        :return:
        """
        if self.geom_defined_by == 'ref_fid':
            if self.ref_lyr_id:
                reference_layer = qgis.core.QgsProject.instance().mapLayer(self.ref_lyr_id)
                if reference_layer:
                    if self.ref_fid is not None:
                        reference_feature = reference_layer.getFeature(self.ref_fid)
                        if reference_feature.isValid() and reference_feature.hasGeometry():
                            return reference_feature.geometry()
                        else:
                            self.is_valid = False
                            self.last_error = MY_DICT.tr('exc_reference_feature_invalid',self.ref_fid,reference_layer.name())
                    else:
                        self.is_valid = False
                        self.last_error = MY_DICT.tr('exc_ref_fid_not_set')
                else:
                    self.is_valid = False
                    self.last_error = MY_DICT.tr('exc_ref_lyr_not_found',self.ref_lyr_id)
            else:
                self.is_valid = False
                self.last_error = MY_DICT.tr('exc_ref_lyr_id_not_set')
        elif self.geom_defined_by == 'cache':
            if isinstance(self.cached_geom, qgis.core.QgsGeometry):
                return self.cached_geom
            else:
                self.is_valid = False
                self.last_error = MY_DICT.tr('exc_no_cached_geom')

        else:
            self.is_valid = False
            self.last_error = MY_DICT.tr('exc_geom_defined_by',self.geom_defined_by)

    def recalc_by_point(self, point_geom: qgis.core.QgsGeometry):
        """recalculate additional stationing-meta-data for specific reference-feature by point-geometry, which will be snapped to the reference-geometry
        :param point_geom: point-geometry projection according to self.reference_layer
        :param ref_fid: optional replacement for self.ref_fid
        """
        reference_geom = self.get_reference_geom()
        if reference_geom:
            snap_n_abs = reference_geom.lineLocatePoint(point_geom)
            # lineLocatePoint => -1 on error
            if snap_n_abs >= 0:

                self.map_x = point_geom.constGet().x()
                self.map_y = point_geom.constGet().y()
                self.recalc_by_stationing(snap_n_abs, 'Nabs', False)
                self.is_valid = True
                self.last_error = ''
            else:
                self.is_valid = False
                self.last_error = MY_DICT.tr('exc_line_locate_point_failed')



    def recalc_by_stationing(self, stationing_xyz, lr_mode: str, recalc_canvas_coords: bool = True):
        """recalculate additional stationing-meta-data for specific reference-feature (self.reference_layer + self.ref_fid) and a numeric stationing
        :param stationing_xyz: numerical stationing for various lr_modes
        :param lr_mode:
        Nabs => Natural stationing
        Nfract => N-value stationing in range 0...1
        Mabs => M-value stationing
        Mfract => M-value stationing in range 0...1
        Conditions for lr_mode Mabs/Mfract:
        reference-layer m-enabled
        referenced-geometry ST_IsValidTrajectory (single-parted, ascending M-values)
        :param recalc_canvas_coords: replace original canvas-coords (click-position) with recalculated snap-coords
        """
        self.snap_n_abs = None
        self.snap_n_fract = None
        self.snap_x = None
        self.snap_y = None
        self.snap_m_abs = None
        self.snap_m_fract = None
        stationing_n = None

        reference_geom = self.get_reference_geom()
        if reference_geom:
            if lr_mode == 'Nabs':
                if 0 <= stationing_xyz <= reference_geom.length():
                    stationing_n = stationing_xyz
                else:
                    self.is_valid = False
                    self.last_error = MY_DICT.tr('exc_stationing_out_of_range',lr_mode,stationing_xyz)
            elif lr_mode == 'Nfract':
                if 0 <= stationing_xyz <= 1:
                    stationing_n = reference_geom.length() * stationing_xyz
                else:
                    self.is_valid = False
                    self.last_error = MY_DICT.tr('exc_stationing_out_of_range',lr_mode,stationing_xyz)
            elif lr_mode == 'Mabs':
                first_vertex_m, last_vertex_m, error_msg = get_first_last_vertex_m(reference_geom)
                if not error_msg:
                    if first_vertex_m <= stationing_xyz <= last_vertex_m:
                        stationing_n = get_stationing_n_from_m(reference_geom, stationing_xyz)
                    else:
                        self.is_valid = False
                        self.last_error = MY_DICT.tr('exc_stationing_out_of_range',lr_mode,stationing_xyz)
                else:
                    self.is_valid = False
                    self.last_error = error_msg
            elif lr_mode == 'Mfract':
                geom_m_valid, error_msg = check_geom_m_valid(reference_geom)
                if geom_m_valid:
                    if 0 <= stationing_xyz <= 1:
                        first_vertex_m, last_vertex_m, error_msg = get_first_last_vertex_m(reference_geom)
                        if not error_msg:
                            current_m = first_vertex_m + (stationing_xyz * (last_vertex_m - first_vertex_m))
                            stationing_n = get_stationing_n_from_m(reference_geom, current_m)
                        else:
                            self.is_valid = False
                            self.last_error = error_msg
                    else:
                        self.is_valid = False
                        self.last_error = MY_DICT.tr('exc_stationing_out_of_range',lr_mode,stationing_xyz)
                else:
                    self.is_valid = False
                    self.last_error = error_msg
            else:
                self.is_valid = False
                self.last_error = MY_DICT.tr('exc_lr_mode_not_implemented',lr_mode)



            if stationing_n is not None:
                # interpolate automatically calculates interpolated M- and Z-Values
                # M-Z-values are interpolated in range M-Z-vertex-before/M-Z-vertex-after even if check_geom_m_valid returns false
                # NaN, if geometry not M/Z-enabled
                interpolated_point = reference_geom.interpolate(stationing_n)

                if not interpolated_point.isEmpty():
                    self.snap_n_abs = stationing_n
                    self.snap_x = interpolated_point.constGet().x()
                    self.snap_y = interpolated_point.constGet().y()

                    self.is_valid = True
                    self.last_error = ''

                    linestring_m_wkb_types = [
                        qgis.core.QgsWkbTypes.LineStringM,
                        qgis.core.QgsWkbTypes.LineStringZM,
                        qgis.core.QgsWkbTypes.MultiLineStringM,
                        qgis.core.QgsWkbTypes.MultiLineStringZM,
                    ]


                    if reference_geom.wkbType() in linestring_m_wkb_types:
                        # store calculated M-value, even if the geometry is not valid for m-stationing
                        # @ToThink
                        # if check_geom_m_valid(reference_geom):
                        snap_m_abs = interpolated_point.constGet().m()
                        if isinstance(snap_m_abs, numbers.Number) and not math.isnan(snap_m_abs):
                            self.snap_m_abs = snap_m_abs
                            first_vertex_m, last_vertex_m, error_msg = get_first_last_vertex_m(reference_geom)
                            if not error_msg and (last_vertex_m - first_vertex_m) != 0:
                                self.snap_m_fract = (self.snap_m_abs - first_vertex_m) / (last_vertex_m - first_vertex_m)
                                #debug_print(self.snap_m_abs,first_vertex_m,last_vertex_m,self.snap_m_fract)



                    linestring_z_wkb_types = [
                        qgis.core.QgsWkbTypes.LineStringZ,
                        qgis.core.QgsWkbTypes.LineStringZM,
                        qgis.core.QgsWkbTypes.MultiLineStringZ,
                        qgis.core.QgsWkbTypes.MultiLineStringZM,
                    ]

                    self.snap_z_abs = None
                    if reference_geom.wkbType() in linestring_z_wkb_types:
                        snap_z_abs = interpolated_point.constGet().z()
                        if isinstance(snap_z_abs, numbers.Number) and not math.isnan(snap_z_abs):
                            self.snap_z_abs = snap_z_abs

                    if reference_geom.length() > 0:
                        self.snap_n_fract = self.snap_n_abs / reference_geom.length()

                    if recalc_canvas_coords:
                        if self.reference_authid:
                            interpolated_point.transform(qgis.core.QgsCoordinateTransform(qgis.core.QgsCoordinateReferenceSystem(self.reference_authid), qgis.utils.iface.mapCanvas().mapSettings().destinationCrs(), qgis.core.QgsProject.instance()))

                            self.map_x = interpolated_point.constGet().x()
                            self.map_y = interpolated_point.constGet().y()
                        else:
                            self.is_valid = False
                            self.last_error = MY_DICT.tr('reference_authid_not_set')
                else:
                    self.is_valid = False
                    self.last_error = MY_DICT.tr('exc_interpolation_failed',lr_mode,stationing_n)


    def __copy__(self):
        """implementation because of copy.deepcopy-problems if there was f.e. a missing offset in data:
          TypeError: cannot pickle 'QVariant' object"""
        my_clone = PoLFeature()

        # no dunders, no functions, no objects => only literal-values
        property_list = [prop for prop in dir(self) if not prop.startswith('__') and not callable(getattr(self, prop)) and not inspect.isclass(getattr(self, prop))]

        for prop_name in property_list:
            setattr(my_clone, prop_name, getattr(self, prop_name))

        if self.cached_geom:
            my_clone.cached_geom = self.cached_geom

        return my_clone

    def __str__(self):
        result_str = ''
        property_list = [prop for prop in dir(self) if not prop.startswith('__') and not callable(getattr(self, prop))]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str

class LoLFeature:
    """Line-on-Line-Feature
    Two PoLFeatures snapped on the same reference-line
    container-object for stored vector-layer-feature, f.e. for edit-purpose
    instantiated and stored in LolEvt as session_data.edit_feature via tool_select_feature
    """

    # optional fid of data-feature for edit/save-purpose
    data_fid = None

    # allow multiple versions for geometry-input
    # ref_fid =>  default, get geometry from layer by ref_lyr_id and ref_fid
    # cache => cache any geometry
    geom_defined_by = 'ref_fid'

    # Layer on which the values are calculated
    ref_lyr_id = None

    # fid of assigned reference-feature
    ref_fid = None

    # for geom_defined_by 'cache': reference-geometry (post-processing)
    cached_geom = None

    # projection of reference_geom and cached_geom
    # type str, f.e. 'EPSG:25832'
    reference_authid = None

    # stationing-from on assigned reference-line, type PoLFeature, ignoring their ref_lyr_id + ref_fid
    pol_from = None
    # stationing-to on assigned reference-line, type PoLFeature
    pol_to = None

    # offset
    offset = 0

    delta_n_abs = None
    delta_n_fract = None
    delta_m_abs = None
    delta_m_fract = None
    delta_z_abs = None


    is_valid = True

    # reason for not is_valid
    last_error = ''


    def set_pol_from(self,pol_from):
        self.pol_from = pol_from
        self.ref_lyr_id = pol_from.ref_lyr_id
        self.ref_fid = pol_from.ref_fid
        self.calculate_delta_measurements()
        self.check_is_valid()

    def set_pol_to(self,pol_to):
        self.pol_to = pol_to
        self.ref_lyr_id = pol_to.ref_lyr_id
        self.ref_fid = pol_to.ref_fid
        self.calculate_delta_measurements()
        self.check_is_valid()


    def check_is_valid(self)->bool:
        """" checks, sets and returns self.is_valid,
        True if pol_from and pol_to set and valid and with same ref_fid"""
        self.is_valid = self.pol_from is not None and self.pol_from.is_valid and self.pol_to is not None and self.pol_to.is_valid and self.ref_fid is not None and self.ref_fid == self.pol_from.ref_fid and self.ref_fid == self.pol_to.ref_fid

        return self.is_valid

    def calculate_delta_measurements(self):
        self.delta_n_abs = None
        self.delta_n_fract = None
        self.delta_m_abs = None
        self.delta_m_fract = None
        self.delta_z_abs = None

        if self.pol_from and self.pol_from.is_valid:
            if self.pol_to and self.pol_to.is_valid:
                if (self.pol_from.ref_lyr_id == self.pol_to.ref_lyr_id == self.ref_lyr_id) and (self.pol_from.ref_fid == self.pol_to.ref_fid == self.ref_fid):
                    if isinstance(self.pol_from.snap_n_abs, numbers.Number) and isinstance(self.pol_to.snap_n_abs, numbers.Number):
                        self.delta_n_abs = self.pol_to.snap_n_abs - self.pol_from.snap_n_abs

                    if isinstance(self.pol_from.snap_n_fract, numbers.Number) and isinstance(self.pol_to.snap_n_fract, numbers.Number):
                        self.delta_n_fract = self.pol_to.snap_n_fract - self.pol_from.snap_n_fract

                    if isinstance(self.pol_from.snap_m_abs, numbers.Number) and isinstance(self.pol_to.snap_m_abs, numbers.Number):
                        self.delta_m_abs = self.pol_to.snap_m_abs - self.pol_from.snap_m_abs

                    if isinstance(self.pol_from.snap_m_fract, numbers.Number) and isinstance(self.pol_to.snap_m_fract, numbers.Number):
                        self.delta_m_fract = self.pol_to.snap_m_fract - self.pol_from.snap_m_fract

                    if isinstance(self.pol_from.snap_z_abs, numbers.Number) and isinstance(self.pol_to.snap_z_abs, numbers.Number):
                        self.delta_z_abs = self.pol_to.snap_z_abs - self.pol_from.snap_z_abs

    def __copy__(self):
        """implementation because of deepcopy-error if there was f.e. a missing offset in data:
          TypeError: cannot pickle 'QVariant' object"""
        my_clone = LoLFeature()

        # no dunders, no functions, no objects => only literal-values
        property_list = [prop for prop in dir(self) if not prop.startswith('__') and not callable(getattr(self, prop)) and not inspect.isclass(getattr(self, prop))]

        for prop_name in property_list:
            setattr(my_clone, prop_name, getattr(self, prop_name))

        # this property is an object, therefore not clonable
        if self.cached_geom:
            my_clone.cached_geom = self.cached_geom

        # Note: PoLFeature implements its own __copy__()-method
        if self.pol_from:
            my_clone.set_pol_from(self.pol_from.__copy__())

        if self.pol_to:
            my_clone.set_pol_to(self.pol_to.__copy__())

        return my_clone

    def __str__(self):
        result_str = ''
        property_list = [prop for prop in dir(self) if not prop.startswith('__') and not callable(getattr(self, prop))]

        longest_prop = max(property_list, key=len)
        max_len = len(longest_prop)

        for prop in property_list:
            result_str += f"{prop:<{max_len}}    {getattr(self, prop)}\n"

        return result_str


def eval_crs_units(crs_authid: str) -> tuple:
    """
    gets some metadata from (layer/canvas)-crs, used for dialog (unit-widgets, precision) and canvas-zoom-or-pan decisions
    :param crs_authid: f.e. "ETRS:25832"
    :return: tuple(str,float,int,int) unit,zoom_pan_tolerance,display_precision,measure_default_step
    """
    # Rev. 2024-06-24
    # enum class Qgis::DistanceUnit: https://api.qgis.org/api/classQgis.html#a3ea4b03a09f98ff39ea27ad0e5d50614

    crs = qgis.core.QgsCoordinateReferenceSystem(crs_authid)
    #mapUnits(self) -> Qgis.DistanceUnit
    # Returns the units for the projection used by the CRS.
    mu = crs.mapUnits()
    
    if mu == qgis.core.Qgis.DistanceUnit.Meters:
        unit = 'm'
        zoom_pan_tolerance = .1
        display_precision = 2
        measure_default_step = 1
    elif mu == qgis.core.Qgis.DistanceUnit.Kilometers:
        unit = 'km'
        zoom_pan_tolerance = .1 / 1000
        display_precision = 3
        measure_default_step = .001
    elif mu == qgis.core.Qgis.DistanceUnit.Feet:
        unit = 'ft'
        zoom_pan_tolerance = .1 / 0.3048
        display_precision = 1
        measure_default_step = 1
    elif mu == qgis.core.Qgis.DistanceUnit.NauticalMiles:
        unit = 'NM'
        zoom_pan_tolerance = .1 / 1852
        display_precision = 3
        measure_default_step = .001
    elif mu == qgis.core.Qgis.DistanceUnit.Yards:
        unit = 'yd'
        zoom_pan_tolerance = .1 / 0.9144
        display_precision = 1
        measure_default_step = .001
    elif mu == qgis.core.Qgis.DistanceUnit.Miles:
        unit = 'mi'
        zoom_pan_tolerance = .1 / 1609.344
        display_precision = 3
        measure_default_step = .001
    elif mu == qgis.core.Qgis.DistanceUnit.Degrees:
        unit = '°'
        zoom_pan_tolerance = 0.00001
        display_precision = 5
        measure_default_step = 0.0001
    elif mu == qgis.core.Qgis.DistanceUnit.Centimeters:
        unit = 'cm'
        zoom_pan_tolerance = 10
        display_precision = 0
        measure_default_step = 10
    elif mu == qgis.core.Qgis.DistanceUnit.Millimeters:
        unit = 'mm'
        zoom_pan_tolerance = 100
        display_precision = 0
        measure_default_step = 100
    elif mu == qgis.core.Qgis.DistanceUnit.Inches:
        unit = 'in'
        zoom_pan_tolerance = .1 / 0.0254
        display_precision = 0
        measure_default_step = 10
    else:
        # if mu == qgis.core.Qgis.DistanceUnit.Unknown
        unit = '?'
        zoom_pan_tolerance = .1
        display_precision = 0
        measure_default_step = 1

    return unit, zoom_pan_tolerance, display_precision, measure_default_step


def set_layer_extent(layer: qgis.core.QgsVectorLayer) -> qgis.core.QgsRectangle:
    """there is a bug in QGis layer.updateExtents(), that this function only recalculates and sets a correct extent, if the new one is larger than before
    this function recalculates and sets the extent by iterating over all feature-geometries
    :param layer:
    :returns: recalculated extent, if at least one valid geometry is found. Extent-projection == layer-projection
    """
    x_min = sys.float_info.max
    y_min = sys.float_info.max
    x_max = -sys.float_info.max
    y_max = -sys.float_info.max

    for f in layer.getFeatures():
        if f.isValid() and f.hasGeometry():
            bb = f.geometry().boundingBox()
            x_min = min(x_min, bb.xMinimum())
            y_min = min(y_min, bb.yMinimum())
            x_max = max(x_max, bb.xMaximum())
            y_max = max(y_max, bb.yMaximum())

    # valid extent, if x_min/y_min/x_max/y_max have changed, i.e. at least one valid point
    # valid extent will be single point, if there is only one feature or multiple features with the same geometry
    if x_min < sys.float_info.max and y_min < sys.float_info.max and x_max > -sys.float_info.max and y_max > -sys.float_info.max:
        calculated_extent = qgis.core.QgsRectangle(x_min, y_min, x_max, y_max)
        layer.setExtent(calculated_extent)
        return calculated_extent


def to_float(value: typing.Any) -> tuple:
    """converts value of type float/int/str to float
    :param value:
    :returns: tuple(float: numeric_value, bool: convert_ok, str: not_ok_reason)
    """
    numeric_value = None
    convert_ok = None
    not_ok_reason = None

    if isinstance(value, float):
        numeric_value = value
        convert_ok = True
    elif isinstance(value, int):
        numeric_value = float(value)
        convert_ok = True
    elif isinstance(value, str):
        group_seperator = locale.nl_langinfo(locale.THOUSEP)
        # strip group-seperators
        value = value.replace(group_seperator, '')
        try:
            numeric_value = locale.atof(value)
            convert_ok = True
        except Exception as e:
            convert_ok = False
            # Note: value appears en_US-locale-formatted in exception
            not_ok_reason = str(e)

    return (numeric_value, convert_ok, not_ok_reason)


def find_conn(conn_ids: dict, layer_id: str, conn_signal: str, conn_function: str) -> tuple:
    """searches a signal/slot-connection in conn_ids
    the plugin-used layers (reference/data/show) have some signals connected to slots, f. e. to refresh dialog-elements after inserts/updates/deletes
    multiple connections of one layer to the same slot are possible but have to be avoided
    on change of layer or plugin-unload these signals have to be disconnected, therefore each connection is registered in a dictionary
    :param conn_ids: structured dictionary: layer_id > conn_signal > conn_function => conn_id, will be extended, if this connection was not registered before
    :param layer_id: ID of the layer, for which the connection was established and has to be registered
    :param conn_signal: a layer has many connectable signals
    :param conn_function: each signal can be connected to multiple functions
    :returns tuple: (layer_id, conn_signal, conn_function, conn_id) or None
    """
    if layer_id in conn_ids:
        if conn_signal in conn_ids[layer_id]:
            if conn_function in conn_ids[layer_id][conn_signal]:
                conn_id = conn_ids[layer_id][conn_signal][conn_function]
                return (layer_id, conn_signal, conn_function, conn_id)


def register_conn(conn_ids: dict, layer_id: str, conn_signal: str, conn_function: str, conn_id: QtCore.QMetaObject.Connection) -> bool:
    """adds a signal/slot-connection to conn_ids
    the plugin-used layers (reference/data/show) have some signals connected to slots, f. e. to refresh dialog-elements after inserts/updates/deletes
    multiple connections of one layer to the same slot are possible but have to be avoided
    on change of layer or plugin-unload these signals have to be disconnected, therefore each connection is registered in a dictionary
    :param conn_ids: structured dictionary: layer_id > conn_signal > conn_function => conn_id, will be extended, if this connection was not registered before
    :param layer_id: ID of the layer, for which the connection was established and has to be registered
    :param conn_signal: a layer has many connectable signals
    :param conn_function: each signal can be connected to multiple functions
    :param conn_id: the reference to the established connection, used to disconnect
    """
    # Check the structure of the dictionary and expand if necessary
    # setdefault does not create a sub-dict, but will return an empty dict if there is none
    if not layer_id in conn_ids:
        conn_ids.setdefault(layer_id, {})

    if not conn_signal in conn_ids[layer_id]:
        conn_ids[layer_id].setdefault(conn_signal, {})

    if not conn_function in conn_ids[layer_id][conn_signal]:
        conn_ids[layer_id][conn_signal][conn_function] = conn_id
        return True
    else:
        return False


class NumberFormatter():
    """helper-class to convert numbers to string regarding system-lcid or potentially differing QGis-lcid-settings for number-formats and/or decimal seperator"""
    """Note: not more used because of MyQtWidgets.QDoubleNoSpinBox"""

    def __init__(self, prec: int = 2, showGroupSeparator: bool = True, lcid: str = 'en_US', unit: str = '', unit_spacer: str = ' ', default_step: float = 1, tolerance: float = 0):
        """constructor
        :param prec: precision == number of decimal places
        :param showGroupSeparator: format numbers with group-seperator, see QGis-Options-Dialog and QtCore.QSettings().value('lcid/showGroupSeparator', True)
        :param lcid: 'en_US', 'de_DE', see QtCore.QSettings().value('lcid/overrideFlag', type=bool) and QtCore.QSettings().value('lcid/globalLocale', 'en_US')
        :param unit: optional unit for formatted string
        :param unit_spacer: blanks between formatted number and unit
        :param default_step: step-width for spin-boxes in dialog
        :param tolerance: used for numeric decision, if two values are identical (N vs. M-stationing), usually 10^-prec
        """

        self.prec = prec
        self.showGroupSeparator = showGroupSeparator
        self.lcid = lcid
        self.unit = unit
        self.unit_spacer = unit_spacer
        self.default_step = default_step
        self.tolerance = tolerance
        self.my_locale = QtCore.QLocale(self.lcid)

        # the QGis-lcid-settings are adopted on dialog-initialization
        # so any change in QGis-Options will be applied after Plugin- or QGis-reload
        # this is according to the hint in the QGis-options-dialog:
        # "Note: Enabling / changing override in lcid requires an application restart"

        self.set_locale(self.lcid)

    def set_showGroupSeparator(self, showGroupSeparator: bool):
        """setter for showGroupSeparator
        :param showGroupSeparator: True => format numbers with GroupSeperator (point, comma, blank...according to lcid)"""

        self.showGroupSeparator = showGroupSeparator

        # default is with seperator
        if not self.showGroupSeparator:
            self.my_locale.setNumberOptions(QtCore.QLocale.OmitGroupSeparator)

    def set_locale(self, lcid: str):
        """setter for my_locale
        :param lcid: en_US, de_DE
        """

        self.lcid = lcid
        self.my_locale = QtCore.QLocale(self.lcid)

        if not self.showGroupSeparator:
            self.my_locale.setNumberOptions(QtCore.QLocale.OmitGroupSeparator)

    def set_prec(self, prec: int):
        """setter for prec
        :param prec: precision == number of decimals
        """

        self.prec = prec

    def set_unit(self, unit: str, unit_spacer: str = ' '):
        """setter for unit
        :param unit:
        :param unit_spacer:
        """

        self.unit = unit
        self.unit_spacer = unit_spacer

    def set_default_step(self, default_step: float):
        """setter for default_step, step-width in dialog
        :param default_step:
        """

        self.default_step = default_step

    def set_tolerance(self, tolerance: float):
        """setter for tolerance, used for numeric decision, if two points are identical
        :param tolerance:
        """

        self.tolerance = tolerance

    def to_string(self, numerical_value: float, append_unit: bool = False, not_numerical_return='-'):
        """convert number, allways with 'f' => 'Floating point' and fix number of decimal places
        :param numerical_value: numerical value
        :param append_unit: appends self.unit
        :param not_numerical_return: return-value for not numerical value
        """

        if isinstance(numerical_value, numbers.Number):
            # conversion to float to avoid "TypeError: arguments did not match any overloaded call:" "toString(self, float, format: str = 'g', precision: int = 6): argument 1 has unexpected type 'int'"
            if append_unit and self.unit:
                return self.my_locale.toString(float(numerical_value), 'f', self.prec) + self.unit_spacer + self.unit
            else:
                return self.my_locale.toString(float(numerical_value), 'f', self.prec)
        else:
            # not a number, e.g. a null-value inside a feature-attribute
            return not_numerical_return


def re_open_attribute_tables(iface: qgis.gui.QgisInterface, layer: qgis.core.QgsVectorLayer):
    """a problem with the use of feature-actions:
    after feature-deletes the action-icons behave unpredictable
    e.g. stay visible and outside the table, if the features are deleted,
    other problem:
    on table-sort the action-icons are duplicated in the first column...
    this tool-function closes and deletes all attribute-tables for a layer and reopens fresh ones with same size, position and selection
    sort-order, columns-widths and view-mode (table-view/form-view) are conserved, too
    only "show selected only" gets lost...
    :param iface:
    :param layer:
    """
    # Rev. 2024-01-31
    # QgsAttributeTableDialog is not part of iface.mainWindow()-hierarchy, so only queryable via allWidgets()
    for widget in core.QgsApplication.instance().allWidgets():
        if isinstance(widget, QtWidgets.QDialog) and widget.isVisible() and widget.objectName() == f"QgsAttributeTableDialog/{layer.id()}" and widget.parent().windowState() != QtCore.Qt.WindowMinimized:
            last_rect = widget.rect()
            last_x = widget.mapToGlobal(QtCore.QPoint(0, 0)).x()
            last_y = widget.mapToGlobal(QtCore.QPoint(0, 0)).y()
            widget.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            widget.close()

            nt = iface.showAttributeTable(layer)
            # minimize-status, resize and reposition only works with the parent(), which is also a QDialog
            nt.parent().setGeometry(last_rect)
            nt.parent().move(last_x, last_y)

    # restore the previous selection
    layer.reselect()


def re_open_feature_forms(iface: qgis.gui.QgisInterface, layer: qgis.core.QgsVectorLayer):
    """closes and deletes (WA_DeleteOnClose) all QDialog-Instances which are Feature-Forms for that layer
    reopens the valid (feature valid) and visible ones at same size and position
    used for refresh of feature-actions of data- and show-layer on plugin-load and/or settings-change
    """
    # Rev. 2024-01-31
    search = f"featureactiondlg:{layer.id()}:"
    # Note: these QDialogs are part of the QMainWindow-hierarchy, so they can be queried by findChildren
    for widget in iface.mainWindow().findChildren(QtWidgets.QDialog):
        if search in widget.objectName():
            if widget.isVisible():
                fid = int(widget.objectName().replace(search, ''))
                feature = layer.getFeature(fid)
                # getFeature returns allways a feature,
                # but feature.isValid() can return False, e.g. if it doesn't exist/was deleted
                if feature and feature.isValid():
                    last_rect = widget.rect()
                    last_x = widget.mapToGlobal(QtCore.QPoint(0, 0)).x()
                    last_y = widget.mapToGlobal(QtCore.QPoint(0, 0)).y()

                    feature_form = iface.getFeatureForm(layer, feature)
                    feature_form.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
                    # Default-Object-Name for single-feature-forms in QGis, also used in this plugin
                    object_name = f"featureactiondlg:{layer.id()}:{feature.id()}"
                    feature_form.setObjectName(object_name)
                    feature_form.show()
                    # resize and re-position according to the previous dialog-window for this feature
                    feature_form.setGeometry(last_rect)
                    feature_form.move(last_x, last_y)

            widget.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            widget.close()


def get_feature_form(iface: qgis.gui.QgisInterface, layer: qgis.core.QgsVectorLayer, feature: qgis.core.QgsFeature, for_insert: bool = False, default_width: int = 600, default_height: int = 400) -> qgis.gui.QgsAttributeDialog:
    """open feature-form
    update/insert-possibility, if layer is editable
    ensures only one feature-form for the same feature
    closes and reopens existing one at the same position
    uses cursor-position + offset x/y and default_width/default_height, if no former position found
    :param iface:
    :param layer:
    :param feature:
    :param for_insert:
        True for insert, creates a new modal feature-form
    :param default_width: used of no former window was found
    :param default_height: used of no former window was found
    :returns: Attribute-Dialog, see https://api.qgis.org/api/classQgsAttributeDialog.html
    """
    last_params = None
    # Default-Object-Name for single-feature-forms in QGis, also used in this plugin
    object_name = f"featureactiondlg:{layer.id()}:{feature.id()}"

    # search all dialog-widgets with that object-name to retrieve their position and size and close+delete them
    for widget in iface.mainWindow().findChildren(QtWidgets.QDialog):
        if widget.objectName() == object_name:
            # store widget size and position
            last_params = [widget.rect().width(),widget.rect().height(),widget.mapToGlobal(QtCore.QPoint(0, 0)).x(), widget.mapToGlobal(QtCore.QPoint(0, 0)).y()]

            # Highlander => close existing window
            widget.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            widget.close()


    # open new feature-form for this feature
    feature_form = iface.getFeatureForm(layer, feature)
    feature_form.setObjectName(object_name)
    feature_form.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
    #feature_form.show()

    if last_params:
        new_width = last_params[0]
        new_height = last_params[1]
        new_x = last_params[2]
        new_y = last_params[3]
    else:
        new_x = QtGui.QCursor().pos().x() + 50
        new_y = QtGui.QCursor().pos().y() + 50
        new_width = default_width
        new_height = default_height

    # there is a Qt-logic that snaps windows to screen edges and prevents positioning autside screen
    feature_form.setGeometry(new_x, new_y, new_width, new_height)


    if for_insert:
        # https://api.qgis.org/api/classQgsAttributeEditorContext.html
        # Add feature mode, for setting attributes for a new feature.
        # In this mode the dialog will be editable even with an invalid feature and will add a new feature when the form is accepted.
        feature_form.setMode(qgis.gui.QgsAttributeEditorContext.AddFeatureMode)
        # modal => block the app => only one insert-feature-form visible at a time
        feature_form.setModal(True)

    return feature_form


def qt_format(in_string, *args):
    """obsolete special for QtCore.QCoreApplication.translate in dialogs, tooltips...
    Some richtext-markups are supported:
    https://doc.qt.io/qtforpython-5/overviews/richtext-html-subset.html#supported-html-subset
    but special-chars and formatting tags are often difficult to translate, because they appear in escaped form inside the pylupdate5-created ts-file
    this function uses special wildcards to avoid these problems
    inside the translate-strings they have to be embedded with {curly} braces
    :param in_string: input
    :param args: optional "normal" format-parameters, which replace numerical wildcards {0} {1}... by their index
    """

    qt_wildcards = {
        'apos': "'",
        'nbsp': "&nbsp;",
        'arrow': "-&gt;",
        'br': "<br />",
        'hr': "<hr />",
        'b1': "<b>",
        'b2': "</b>",
        'lt': "&lt;",
        'gt': "&gt;",
        'ul_1': "<ul style='margin: 0 0 0 0;'>",
        'ul_2': "</ul>",
        'li_1': "<li>",
        'li_2': "</li>",
        # avoids implicit word-wrap in tooltips:
        'div_pre_1': "<div style='white-space:nowrap; margin: 0 0 0 0;'>",
        'div_pre_2': "</div>",
        'div_ml_1': "<div style='margin: 0 0 0 10;'>",
        'div_ml_2': "</div>",
    }
    # ** => spreads the dictionary to name=value pairs
    return in_string.format(*args, **qt_wildcards)


def select_by_value(wdg_with_model: QtWidgets.QWidget, select_value: str | float | int, col_idx: int = 0, role_idx: int = 0):
    """helper-function that selects an item in a QComboBox by its value, blocks any signals
    :param wdg_with_model: Widget wit a model, e.g. QComboBox
    :param select_value: the compare-value
    :param col_idx: the index of the column of the data-model, whose data will be compared, always 0 with QComboBox
    :param role_idx: the role in the items, whose data will be compared, see https://doc.qt.io/qt-5/qt.html#ItemDataRole-enum
    0 -> DisplayRole (Text of the option)
    256 -> UserRole (Data of the option)
    """
    first_item_idx = wdg_with_model.model().index(0, col_idx)
    # param 4 "-1": limits num of matches, here -1 -> no  limit, return all matches
    matching_items = wdg_with_model.model().match(first_item_idx, role_idx, select_value, -1, QtCore.Qt.MatchExactly)
    if matching_items:
        first_matching_item = matching_items.pop(0)
        with QtCore.QSignalBlocker(wdg_with_model):
            wdg_with_model.setCurrentIndex(first_matching_item.row())


def get_first_last_vertex_m(in_geom: qgis.core.QgsGeometry) -> tuple:
    """returns the minimum/maximum m-value of a Linestring-M-Geometry
    Checks only M-enablementm, not "is_valid_trajectory", because also used from MZTool to recalculate missing M-Values
    :param in_geom:
    :returns: tuple(min, max, error_msg)
    """

    linestring_m_wkb_types = [
        qgis.core.QgsWkbTypes.LineStringM,
        qgis.core.QgsWkbTypes.LineStringZM,
        qgis.core.QgsWkbTypes.MultiLineStringM,
        qgis.core.QgsWkbTypes.MultiLineStringZM,
    ]

    if in_geom.wkbType() in linestring_m_wkb_types:
        abstr_geom = in_geom.constGet()
        if isinstance(abstr_geom, qgis.core.QgsLineString):
            # only one geometry
            return abstr_geom[0].m(), abstr_geom[-1].m(), None
        elif isinstance(abstr_geom, qgis.core.QgsMultiLineString):
            # get first vertex m from first segment and last vertex m from last segment
            # Note: check_geom_m_valid only for single-parted Multi-Linestrings
            return abstr_geom[0][0].m(), abstr_geom[-1][-1].m(), None
        else:
            # should never happen
            return None, None, MY_DICT.tr('exc_get_first_last_vertex_m', str(in_geom.wkbType()))

    else:
        # Note: also occures after splitting a valid single LinestringM-geometry in a MultiLinestringM-Layer,
        # the resulting geometry was a WkbType.MultiLineString (without M-values shown as "nan" in vertex-editor)
        return None, None, MY_DICT.tr('exc_geometry_type_without_m')


def get_point_m(in_geom: qgis.core.QgsGeometry, stationing_m: float) -> tuple:
    """returns the Linestring-M-stationed point
    similar as PostGis st_line_locate_point, but returns single-type-geometry and requires Geometries with ST_IsValidTrajectory (monotonuously ascending M-values)
    see https://www.gaia-gis.it/gaia-sins/spatialite-sql-latest.html
    :returns: tuple(qgis.core.QgsGeometry, error_msg)
    """
    geom_m_valid, error_msg = check_geom_m_valid(in_geom)
    if geom_m_valid:
        # SQLite-pre-condition for ST_TrajectoryInterpolatePoint
        sqlite_cur = sqlite_conn.cursor()
        query = "SELECT ST_AsBinary(ST_TrajectoryInterpolatePoint(ST_GeomFromWkb(:geom_wkb),:stationing_m))"
        sqlite_result = sqlite_cur.execute(query, {'geom_wkb': in_geom.asWkb(), 'stationing_m': stationing_m})
        sqlite_row = sqlite_result.fetchone()
        if sqlite_row[0]:
            geom = qgis.core.QgsGeometry()
            geom.fromWkb(sqlite_row[0])
            return geom, None
        else:
            return None, MY_DICT.tr('exc_no_query_result', query)
    else:
        return None, error_msg


def get_point_m_2(in_geom: qgis.core.QgsGeometry, stationing_m: float) -> qgis.core.QgsGeometry:
    """experimental
    same as get_point_m but without sqlite
    Notes:
    similar as PostGis or SQLite st_line_locate_point
    works on multi-geometries, scanning each part
    m-values within a part must be strictly ascending
    returns first hit or None
    returns None if stationing_m is < first-vertex-m rsp. > last-vertex-m (sqlite returns in theses cases the first rsp. the last vertex)
    performance is dependend on the number of vertices and how many iterations have to be done
    :param in_geom:
    :param stationing_m:
    :returns: geometry or None
    """
    # works with invalid geometries, but results are questionable...
    abstr_geom = in_geom.constGet()

    if isinstance(abstr_geom, qgis.core.QgsLineString):
        # only one geometry
        geom_parts = [abstr_geom]
    elif isinstance(abstr_geom, qgis.core.QgsMultiLineString):
        # list of sub-geometries, even if there is only one
        geom_parts = abstr_geom
    else:
        # empty geometry
        return

    for geom_part in geom_parts:
        p_min_m = geom_part[0].m()
        p_max_m = geom_part[-1].m()
        # pre-check this part to avoid useless sequential scans
        if stationing_m >= p_min_m and stationing_m <= p_max_m:
            # Grund-Idee:
            # In einer while-Schleife die Vertices so lange teilen, bis die Anzahl der sequentiell zu durchsuchenden Vertices < 100 ist
            num_all_vertices = geom_part.vertexCount()

            rc = 0
            finish_start_index = 0
            finish_end_index = num_all_vertices - 1

            chunk_start_idx = 0
            while True:
                rc += 1
                # je Umlauf halbiert sich die Anzahl der untersuchten Stützstellen
                # round 1: num_all_vertices / 2 ** 1 = num_all_vertices / 2
                # round 2: num_all_vertices / 2 ** 2 = num_all_vertices / 4
                num_chunk_vertices = round(num_all_vertices / 2 ** rc)

                chunk_end_idx = min(num_all_vertices - 1, chunk_start_idx + num_chunk_vertices)

                start_m = geom_part[chunk_start_idx].m()
                end_m = geom_part[chunk_end_idx].m()

                if not (start_m <= stationing_m and end_m >= stationing_m):
                    # gesuchter Wert nicht in diesem Chunk, nächste Suche daher in der anderen Hälfte
                    chunk_start_idx = chunk_end_idx

                # Abbruch, sobald die Anzahl der im nächsten Schritt sequentiell zu untersuchenden Stützstellen klein genug ist
                # hier gibt es vermnutlich ein Optimum, aber der Wert 15 passt ganz gut
                if num_chunk_vertices < 15:
                    finish_start_index = chunk_start_idx
                    finish_end_index = min(num_all_vertices - 1, chunk_start_idx + num_chunk_vertices + 1)
                    # finish_start_m = geom_part[finish_start_index].m()
                    # finish_end_m = geom_part[finish_end_index].m()
                    # if finish_start_m <= stationing_m and finish_end_m >= stationing_m:
                    #     print(f"OK: fertig nach {rc} Durchläufen: {stationing_m} befindet sich im Wertebereich {finish_start_m} ... {finish_end_m} => Vertex {finish_start_index} ... {finish_end_index}")
                    #     pass
                    # else:
                    #     print(f"Error: nach {rc} Durchläufen: {stationing_m} nicht im Wertebereich {finish_start_m} ... {finish_end_m} => Vertex {finish_start_index} ... {finish_end_index}")
                    break

            # first vertex as initial value
            last_vertex = geom_part[finish_start_index]
            # range: sequence of integers from start (inclusive) to stop (exclusive) by step.
            for v_idx in range(finish_start_index + 1, finish_end_index + 1):
                current_vertex = geom_part[v_idx]

                # delta_m = (stationing_m - last_vertex.m()) / (current_vertex.m() - last_vertex.m())
                # ZeroDivisionError: float division by zero
                # => keine Interpolation möglich bei gleichbleibenden M-Werten
                if current_vertex.m() == last_vertex.m():
                    continue

                # print(f"Vertex {v_idx} {finish_start_index} ... {finish_end_index} {last_vertex.m()} ... {current_vertex.m()}")
                if last_vertex.m() <= stationing_m and current_vertex.m() >= stationing_m:
                    delta_m = (stationing_m - last_vertex.m()) / (current_vertex.m() - last_vertex.m())
                    x = last_vertex.x() + delta_m * (current_vertex.x() - last_vertex.x())
                    y = last_vertex.y() + delta_m * (current_vertex.y() - last_vertex.y())
                    z = last_vertex.z() + delta_m * (current_vertex.z() - last_vertex.z())
                    return (qgis.core.QgsGeometry(qgis.core.QgsPoint(x, y, z, stationing_m)))

                last_vertex = current_vertex



def get_stationing_n_from_m(in_geom: qgis.core.QgsGeometry, stationing_m: float) -> qgis.core.QgsGeometry:
    """returns the N-stationing of a Linestring-M-stationed point without sqlite
    Notes:
    similar as PostGis or SQLite st_line_locate_point
    works on multi-geometries, scanning each part
    m-values within a part must be strictly ascending
    returns first hit or None
    returns None if stationing_m is < first-vertex-m rsp. > last-vertex-m (sqlite returns in theses cases the stationing of first rsp. the last vertex)
    performance is dependend on the number of vertices,
    replacement for former sqlite-calculation with query
    SELECT ST_Line_Locate_Point(ST_GeomFromWkb(:geom_wkb),ST_TrajectoryInterpolatePoint(ST_GeomFromWkb(:geom_wkb),:stationing_m))*ST_Length(ST_GeomFromWkb(:geom_wkb))
    see https://www.gaia-gis.it/gaia-sins/spatialite-sql-latest.html
    :param in_geom:
    :param stationing_m:
    :returns: unit-less stationing-n (running-distance from start-point to stationed point) or None
    """
    point, error_msg = get_point_m(in_geom, stationing_m)

    if point:
        return in_geom.lineLocatePoint(point)


def check_geom_m_valid(in_geom: qgis.core.QgsGeometry) -> tuple:
    """check geometry-type M-enabled, single-parted and monotonuous ascending m-values,
    Only these geometries are suitable for M-stationing
    not OK: multi-part Multi-Line-Strings, ST_LineMerge would strip any vertex-m-values
    raises nothing, but returns False/None, if geometry is not valid
    :returns: (bool True/False => geometry is valid, str error_msg)
    """
    # https://postgis.net/docs/ST_IsValidTrajectory.html:
    # Tests if a geometry encodes a valid trajectory. A valid trajectory is represented as a LINESTRING with measures (M values). The measure values must increase from each vertex to the next.
    # fastest, all trials with python need longer, because every vertex has to be compared with the vertex before

    geom_m_valid = True
    error_msg = ''

    # two quick pre-checks without SQLite...
    linestring_m_wkb_types = [
        qgis.core.QgsWkbTypes.LineStringM,
        qgis.core.QgsWkbTypes.LineStringZM,
        qgis.core.QgsWkbTypes.MultiLineStringM,
        qgis.core.QgsWkbTypes.MultiLineStringZM,
    ]

    if in_geom.wkbType() in linestring_m_wkb_types:
        if in_geom.constGet().partCount() == 1:
            sqlite_cur = sqlite_conn.cursor()
            query = "SELECT ST_IsValidTrajectory(ST_GeomFromWkb(:geom_wkb))"
            sqlite_result = sqlite_cur.execute(query, {'geom_wkb': in_geom.asWkb()})
            sqlite_row = sqlite_result.fetchone()
            geom_m_valid = bool(sqlite_row[0])
            if not geom_m_valid:
                error_msg = MY_DICT.tr('exc_vertex_m_not_strictly_ascending')
        else:
            geom_m_valid = False
            error_msg = MY_DICT.tr('exc_geometry_multi_parted')
    else:
        geom_m_valid = False
        error_msg = MY_DICT.tr('exc_geometry_type_without_m')

    return geom_m_valid, error_msg



def check_geom_n_valid(in_geom: qgis.core.QgsGeometry) -> tuple:
    """returns True for single LineString, single-parted MultiLineStrings and gapless connected MultiLineString-Geometries
    These geometries are suitable for N-stationing
    :returns: (bool geom_n_valid, str error_msg)"""

    geom_n_valid = True
    error_msg = ''

    single_linestring_wkb_types = [
        qgis.core.QgsWkbTypes.LineString25D,
        qgis.core.QgsWkbTypes.LineString,
        qgis.core.QgsWkbTypes.LineStringZ,
        qgis.core.QgsWkbTypes.LineStringM,
        qgis.core.QgsWkbTypes.LineStringZM,
    ]

    multi_linestring_wkb_types = [
        qgis.core.QgsWkbTypes.MultiLineString25D,
        qgis.core.QgsWkbTypes.MultiLineString,
        qgis.core.QgsWkbTypes.MultiLineStringZ,
        qgis.core.QgsWkbTypes.MultiLineStringM,
        qgis.core.QgsWkbTypes.MultiLineStringZM,
    ]
    if in_geom.wkbType() in single_linestring_wkb_types:
        pass
    elif in_geom.wkbType() in multi_linestring_wkb_types:
        abstr_geom = in_geom.constGet()
        if abstr_geom.partCount() == 1:
            pass
        else:
            # try to merge multi-parted segments, which will only return a QgsLineString, if there are no gaps
            merged_geom = in_geom.mergeLines()
            abstr_geom = merged_geom.constGet()
            if not isinstance(abstr_geom, qgis.core.QgsLineString):
                geom_n_valid = False
                error_msg = MY_DICT.tr('exc_multi_part_geometry_not_mergeable')
    else:
        geom_n_valid = False
        error_msg = MY_DICT.tr('exc_geometry_type_not_n_valid')

    return geom_n_valid, error_msg


def get_segment_geom_n(in_geom: qgis.core.QgsGeometry, stationing_n_from: float, stationing_n_to: float, offset: float = 0) -> tuple:
    """calculate line-segment stationing_n_from...stationing_to on in_geom with optional offset
    Note: stationing_n_from/stationing_n_to flipped, if in wrong order
    :param in_geom:
    :param stationing_n_from:
    :param stationing_n_to:
    :param offset: default 0
    :returns: (qgis.core.QgsGeometry: segment_geom, str; segment_error)
    """
    # single LineString, single-parted MultiLineStrings and connected MultiLineString-Geometries are converted to QgsLineString
    geom_n_valid, error_msg = check_geom_n_valid(in_geom)
    if geom_n_valid:
        merged_geom = in_geom.mergeLines()
        abstr_geom = merged_geom.constGet()

        # switch values, curveSubstring requires from <= to
        n_from = min(stationing_n_from, stationing_n_to)
        n_to = max(stationing_n_from, stationing_n_to)
        segment_geom = qgis.core.QgsGeometry(abstr_geom.curveSubstring(n_from, n_to))

        if segment_geom:
            if offset:
                # Bug on QGis in Windows: no Geometry with Offset 0
                # distance – buffer distance
                # segments – for round joins, number of segments to approximate quarter-circle
                # joinStyle – join style for corners in geometry
                # miterLimit – limit on the miter ratio used for very sharp corners (JoinStyleMiter only)
                segment_geom = segment_geom.offsetCurve(offset, 8, qgis.core.Qgis.JoinStyle.Round, 0)

            return segment_geom, None
        else:
            # empty geometry
            return segment_geom, MY_DICT.tr('exc_curve_substring_failed', n_from, n_to)
    else:
        return None, error_msg


def get_segment_geom_m(in_geom: qgis.core.QgsGeometry, stationing_m_from: float, stationing_m_to: float, offset: float = 0) -> tuple:
    """calculate line-segment stationing_m_from...stationing_m_to on in_geom with optional offset
    Note: stationing_m_from/stationing_m_to flipped, if in wrong order
    see https://www.gaia-gis.it/gaia-sins/spatialite-sql-latest.html
    Note 2: never used, because M-stationings are internally converted to N-stationings
    :param in_geom:
    :param stationing_m_from:
    :param stationing_m_to:
    :param offset: default 0
    :returns: tuple(QgsGeometry, error_msg)
    """
    geom_m_valid, error_msg = check_geom_m_valid(in_geom)
    if geom_m_valid:
        sqlite_cur = sqlite_conn.cursor()
        query = """SELECT ST_AsBinary(ST_OffsetCurve(ST_Locate_Between_Measures(ST_GeomFromWkb(:geom_wkb),:m_from,:m_to),:offset))"""
        m_from = min(stationing_m_from, stationing_m_to)
        m_to = max(stationing_m_from, stationing_m_to)
        sqlite_result = sqlite_cur.execute(query, {'geom_wkb': in_geom.asWkb(), 'm_from': m_from, 'm_to': m_to, 'offset': offset})
        sqlite_row = sqlite_result.fetchone()
        if sqlite_row[0]:
            geom = qgis.core.QgsGeometry()
            geom.fromWkb(sqlite_row[0])
            return geom, None
        else:
            return None, MY_DICT.tr('exc_no_query_result',query)
    else:
        return None, error_msg


def get_feature_by_value(vlayer: qgis.core.QgsVectorLayer, field: qgis.core.QgsField | str, value: typing.Any) -> qgis.core.QgsFeature | None:
    """Returns first feature from layer by query on a single value,
    intended for use on PK-field and PK-Value, where only one feature is expected
    sample:
    found_feature = get_feature_by_value(iface.activeLayer(),iface.activeLayer().fields()[0],1)
    :param vlayer:
    :param field: queryable-attribute, can be a QgsField or the name of a QgsField
    :param value: any queryable-attribute-value, usually numeric or string, will be used in FilterExpression with 'value'
    """

    request = qgis.core.QgsFeatureRequest()
    if isinstance(field, str):
        if field in vlayer.dataProvider().fieldNameMap():
            request.setFilterExpression(f'"{field}" = \'{value}\'')
        else:
            raise NameError(MY_DICT.tr('exc_field_not_found',field,vlayer.name()))
    else:
        request.setFilterExpression(f'"{field.name()}" = \'{value}\'')

    queried_features = vlayer.getFeatures(request)

    # return the first feature
    for feature in queried_features:
        return feature



def str_replace_multi(in_string:str, search_list:list, replace:str = '')->str:
    """replaces a liste of words in a string
    from Bakuriu's answer in https://stackoverflow.com/questions/15658187/replace-all-words-from-word-list-with-another-string-in-python
    sample:
    draw_markers='snf snt enf ent sgn rfl'
    draw_markers = str_replace_multi(draw_markers,['enf','ent'])
    :param in_string:
    :param search_list:
    :param replace: optional replacement
    """
    big_regex = re.compile('|'.join(map(re.escape, search_list)))
    return big_regex.sub(replace, in_string)

def list_replace_multi(in_list:str, search_list:list)->list:
    """replaces a list of elements in a list
    sample:
    draw_markers=['snf','snt','enf','ent','sgn','rfl']
    draw_markers = list_replace_multi(draw_markers,['enf','ent'])
    :param in_list:
    :param search_list:
    """
    return [in_elm for in_elm in in_list if not in_elm in search_list]



def get_unique_string(used_strings: list, template: str, start_i: int = 1) -> str:
    """get unique string replacing Wildcard {curr_i} with incremented integer
    :param used_strings: List of already used strings, f.e. table-names in a GeoPackage or layer in QGis-Project [layer.name() for layer in  qgis.core.QgsProject.instance().mapLayers().values()]
    :param template: template with Wildcard {curr_i}
    :param start_i: start index for incrementing, usually 1
    """
    # avoids endless "while True" below, if '{curr_i}' is missing in template
    if not '{curr_i}' in template:
        template += '{curr_i}'

    while True:
        return_string = template.format(curr_i=start_i)
        if not return_string in used_strings:
            return return_string
        start_i += 1


def get_data_layers() -> dict:
    """return dictionary of all loaded non-geometry-layers
    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """

    ld = {}
    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.isValid():
            if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() == qgis.core.QgsWkbTypes.NoGeometry:
                ld[cl.id()] = cl
    return ld


def get_linestring_layers() -> dict:
    """
    return dict of all linestring-type-layers in current project,
    also multi-line-layers because of shape-format, which doesn't distinguish between single- and multi-geometry-types
    unpredictable, how linear referenced features on multi-linestring will be located
    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """

    ld = {}
    linestring_wkb_types = [
        qgis.core.QgsWkbTypes.LineString25D,
        qgis.core.QgsWkbTypes.MultiLineString25D,
        qgis.core.QgsWkbTypes.LineString,
        qgis.core.QgsWkbTypes.MultiLineString,
        qgis.core.QgsWkbTypes.LineStringZ,
        qgis.core.QgsWkbTypes.MultiLineStringZ,
        qgis.core.QgsWkbTypes.LineStringM,
        qgis.core.QgsWkbTypes.MultiLineStringM,
        qgis.core.QgsWkbTypes.LineStringZM,
        qgis.core.QgsWkbTypes.MultiLineStringZM,
    ]
    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        # -> https://api.qgis.org/api/classQgsDataProvider.html -> memory/virtual/ogr
        #  Skip Virtual-layers: and cl.dataProvider().name() != 'virtual'
        if cl.isValid():
            if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in linestring_wkb_types:
                ld[cl.id()] = cl
    return ld


def get_point_show_layers() -> dict:
    """returns a list of potential point-show-layers:
        - VectorLayer single PointGeometry/z/m
        (the user might export the slow virtual layer as vector-layer or use a database-driven view)
    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """

    ld = {}
    single_point_wkb_types = [
        qgis.core.QgsWkbTypes.Point25D,
        qgis.core.QgsWkbTypes.Point,
        qgis.core.QgsWkbTypes.PointZ,
        qgis.core.QgsWkbTypes.PointM,
        qgis.core.QgsWkbTypes.PointZM,
    ]

    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.isValid() and cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_point_wkb_types:
            if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_point_wkb_types:
                ld[cl.id()] = cl
    return ld


def get_line_show_layers() -> dict:
    """returns a list of potential line-show-layers:
        - VectorLayer type single-linestring/m/z
        (the user might export the slow virtual layer as vector-layer or use a database-driven view)
    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """

    ld = {}
    single_line_wkb_types = [
        qgis.core.QgsWkbTypes.LineString25D,
        qgis.core.QgsWkbTypes.LineString,
        qgis.core.QgsWkbTypes.LineStringZ,
        qgis.core.QgsWkbTypes.LineStringM,
        qgis.core.QgsWkbTypes.LineStringZM,
    ]

    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.isValid() and cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_line_wkb_types:
            ld[cl.id()] = cl
            # if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_line_wkb_types:
            #     if cl.dataProvider().name() not in ['ogr']:
            #         caps = cl.dataProvider().capabilities()
            #         if not (caps & qgis.core.QgsVectorDataProvider.AddFeatures):
            #             if not (caps & qgis.core.QgsVectorDataProvider.DeleteFeatures):
            #                 if not (caps & qgis.core.QgsVectorDataProvider.ChangeAttributeValues):

    return ld


def get_point_layers() -> dict:
    """return dictionary of loaded point-layers
    :returns dict key: layer_id value: layer (qgis.core.QgsVectorLayer)
    """

    ld = {}
    single_point_wkb_types = [
        qgis.core.QgsWkbTypes.Point25D,
        qgis.core.QgsWkbTypes.Point,
        qgis.core.QgsWkbTypes.PointZ,
        qgis.core.QgsWkbTypes.PointM,
        qgis.core.QgsWkbTypes.PointZM,
    ]
    for cl in qgis.core.QgsProject.instance().mapLayers().values():
        if cl.isValid():
            if cl.type() == qgis.core.QgsMapLayerType.VectorLayer and cl.dataProvider().wkbType() in single_point_wkb_types:
                ld[cl.id()] = cl
    return ld


def push_messages(iface: qgis.gui.QgisInterface, success_msg: str = None, info_msg: str = None, warning_msg: str = None, critical_msg: str = None):
    """pushes four kind of messages to self.iface.messageBar
    adds file-name and line-number for debug-convenience
    different message-types are displayed with different durations
    :param iface: qgis.gui.QgisInterface for accessing iface.messageBar()
    :param success_msg:
    :param info_msg:
    :param warning_msg:
    :param critical_msg:
    """

    debug_pos = get_debug_pos(2)
    title = f"LinearReferencing ({debug_pos})"

    if critical_msg:
        iface.messageBar().pushMessage(title, critical_msg, level=qgis.core.Qgis.Critical, duration=20)

    if warning_msg:
        iface.messageBar().pushMessage(title, warning_msg, level=qgis.core.Qgis.Warning, duration=10)

    if info_msg:
        iface.messageBar().pushMessage(title, info_msg, level=qgis.core.Qgis.Info, duration=5)

    if success_msg:
        iface.messageBar().pushMessage(title, success_msg, level=qgis.core.Qgis.Success, duration=3)



class OneLayerFilter(qgis.core.QgsPointLocator.MatchFilter):
    """Filter for Snapping: snap only features of a certain layer"""

    def __init__(self, layer):
        qgis.core.QgsPointLocator.MatchFilter.__init__(self)
        self.layer = layer

    def acceptMatch(self, m):
        return m.layer() == self.layer


class OneFeatureFilter(qgis.core.QgsPointLocator.MatchFilter):
    """Filter for Snapping: snap only on one feature of a certain layer"""

    def __init__(self, layer, fid):
        qgis.core.QgsPointLocator.MatchFilter.__init__(self)
        self.layer = layer
        self.fid = fid

    def acceptMatch(self, m):
        return m.layer() == self.layer and m.featureId() == self.fid
