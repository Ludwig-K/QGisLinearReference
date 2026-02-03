#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* LoL == Line-on-Line

********************************************************************

* Date                 : 2025-07-07
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
    * import LinearReferencing.tools.LoL
    * from LinearReferencing.tools.LoL import LoL

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
    Qgis
)

from LinearReferencing.tools.MyDebugFunctions import debug_log, debug_print
from LinearReferencing.settings.exceptions import *
from LinearReferencing.tools.LinearReferencedGeometry import LinearReferencedGeometry, LinestringStatistics

class LoL(LinearReferencedGeometry):
    """Line-On-Line
    Segment on line between two stationings
    """
    # Rev. 2026-01-13

    def __init__(self):
        """constructor without arguments and functionalities
        instances are created via @classmethods init_by_...
        """
        # Rev. 2026-01-13
        super().__init__()

        # ofset between reference-line and segment, > 0 left, < 0 right, == 0 on the line
        self.offset: float | None = None

        # snap_x_lyr/snap_y_lyr => mouse-positions snapped on reference-line, refLyr-projection
        self.snap_x_lyr_from: float | None = None
        self.snap_y_lyr_from: float | None = None
        self.snap_x_lyr_to: float | None = None
        self.snap_y_lyr_to: float | None = None

        # snap_x_cvs/snap_y_cvs => mouse-positions snapped on reference-line, canvas-projection
        self.snap_x_cvs_from: float | None = None
        self.snap_y_cvs_from: float | None = None
        self.snap_x_cvs_to: float | None = None
        self.snap_y_cvs_to: float | None = None

        # absolute N-stationing of snapped point in refLyr-units
        # first calculated and base for all other conversions
        self.snap_n_abs_from: float | None = None
        self.snap_n_abs_to: float | None = None

        # relative N-stationing 0...1 as fract of range 0...geometry-length
        self.snap_n_fract_from: float | None = None
        self.snap_n_fract_to: float | None = None

        # interpolated M-value of snapped point (if refLyr M-enabled)
        self.snap_m_abs_from: float | None = None
        self.snap_m_abs_to: float | None = None

        # interpolated M-value of snapped point as fract of range minM...maxM
        # if refLyr M-enabled and geometry is ST_IsValidTrajectory (single parted, ascending M-values, see https://postgis.net/docs/ST_IsValidTrajectory.html)
        self.snap_m_fract_from: float | None = None
        self.snap_m_fract_to: float | None = None

        # interpolated Z-value of snapped point (if refLyr Z-enabled)
        self.snap_z_abs_from: float | None = None
        self.snap_z_abs_to: float | None = None

        # indizes and measurements of vertices before and after the snapped point on reference-line

        # vertices past
        self.next_vertex_index_from: int | None = None
        self.next_vertex_index_to: int | None = None



    def get_stationings(self, lr_mode: str) -> tuple|None:
        """tool-function returning stationing according to lr_mode

        Args:
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Raises:
            NotImplementedError: wrong lr_mode
            PropMissingException: if at least one of the stationigs is not numeric

        Returns:
            tuple|None: (double: stationing_from, double: stationing_to) or None if one is not numeric
        """
        # Rev. 2026-01-13
        stationing_from_xyz = None
        stationing_to_xyz = None
        if lr_mode == "Nabs":
            if isinstance(self.snap_n_abs_from,numbers.Number):
                stationing_from_xyz = self.snap_n_abs_from
            else:
                raise PropMissingException("snap_n_abs_from")
            if isinstance(self.snap_n_abs_to,numbers.Number):
                stationing_to_xyz = self.snap_n_abs_to
            else:
                raise PropMissingException("snap_n_abs_to")
        elif lr_mode == "Nfract":
            if isinstance(self.snap_n_fract_from,numbers.Number):
                stationing_from_xyz = self.snap_n_fract_from
            else:
                raise PropMissingException("snap_n_fract_from")
            if isinstance(self.snap_n_fract_to,numbers.Number):
                stationing_to_xyz = self.snap_n_fract_to
            else:
                raise PropMissingException("snap_n_fract_to")
        elif lr_mode == "Mabs":
            if isinstance(self.snap_m_abs_from,numbers.Number):
                stationing_from_xyz = self.snap_m_abs_from
            else:
                raise PropMissingException("snap_m_abs_from")
            if isinstance(self.snap_m_abs_to,numbers.Number):
                stationing_to_xyz = self.snap_m_abs_to
            else:
                raise PropMissingException("snap_m_abs_to")
        elif lr_mode == "Mfract":
            if isinstance(self.snap_m_fract_from,numbers.Number):
                stationing_from_xyz = self.snap_m_fract_from
            else:
                raise PropMissingException("snap_m_fract_from")
            if isinstance(self.snap_m_fract_to,numbers.Number):
                stationing_to_xyz = self.snap_m_fract_to
            else:
                raise PropMissingException("snap_m_fract_to")
        else:
            raise NotImplementedError(f"lr_mode {lr_mode}")

        if stationing_from_xyz is not None and stationing_to_xyz is not None:
            return stationing_from_xyz, stationing_to_xyz

    def move_segment(self,delta_n_abs)->bool:
        """moves segment by delta_n_abs

        If the from/to-stationings get out-of-bounds, the segment is snapped to start/end keeping the old length
        Nabs-from/to = 0/self.reference_geom.length()

        Args:
            delta_n_abs (float): numerical distance, positive: move up, negative: move down

        Returns:
            bool: update successfull? else: Exception
        """
        # Rev. 2026-01-13

        old_from = self.snap_n_abs_from
        old_to = self.snap_n_abs_to

        old_len = abs(old_to - old_from)

        new_from = old_from + delta_n_abs
        new_to = old_to + delta_n_abs

        if delta_n_abs < 0 and new_from < 0 or new_to < 0:
            # keep reverse
            if new_from < new_to:
                new_from = 0
                new_to = old_len
            else:
                new_from = old_len
                new_to = 0
        else:
            ref_len = self.reference_geom.length()
            if new_to > ref_len or new_from > ref_len:
                # keep reverse
                if new_from < new_to:
                    new_to = ref_len
                    new_from = ref_len - old_len
                else:
                    new_to = ref_len - old_len
                    new_from = ref_len

        return self.update_stationings(
            new_from, new_to, "Nabs"
        )

    def snap_to_end(self)->bool:
        """snaps segment to end keeping the old natural length

        Returns:
            bool: update successfull? else: Exception
        """
        # Rev. 2026-01-13
        old_from = self.snap_n_abs_from
        old_to = self.snap_n_abs_to
        old_len = abs(old_to - old_from)

        ref_len = self.reference_geom.length()
        if old_from < old_to:
            new_from = ref_len - old_len
            new_to = ref_len
        else:
            new_from = ref_len
            new_to = ref_len - old_len

        return self.update_stationings(
            new_from, new_to, "Nabs"
        )

    def snap_to_start(self)->bool:
        """snaps segment to start keeping the old natural length

        Returns:
            bool: update successfull? else: Exception
        """
        # Rev. 2026-01-13
        old_from = self.snap_n_abs_from
        old_to = self.snap_n_abs_to
        old_len = abs(old_to - old_from)


        if old_from < old_to:
            new_from = 0
            new_to = old_len
        else:
            new_to = 0
            new_from = old_len

        return self.update_stationings(
            new_from, new_to, "Nabs"
        )


    def flip_down(self)->bool:
        """flips segment towards start by old natural length

        Returns:
            bool: update successfull? else: Exception
        """
        # Rev. 2026-01-13
        old_from = self.snap_n_abs_from
        old_to = self.snap_n_abs_to
        old_len = abs(old_to - old_from)

        new_from = old_from - old_len
        new_to = old_to - old_len

        if new_from < 0 or new_to < 0:
            # keep reverse
            if new_from < new_to:
                new_from = 0
                new_to = old_len
            else:
                new_from = old_len
                new_to = 0

        return self.update_stationings(
            new_from, new_to, "Nabs"
        )

    def flip_up(self)->bool:
        """flips segment towards end by old natural length

        Returns:
            bool: update successfull? else: Exception
        """
        # Rev. 2026-01-13
        old_from = self.snap_n_abs_from
        old_to = self.snap_n_abs_to
        old_len = abs(old_to - old_from)

        new_from = old_from + old_len
        new_to = old_to + old_len
        ref_len = self.reference_geom.length()
        if new_to > ref_len or new_from > ref_len:
            # keep reverse
            if new_from < new_to:
                new_to = ref_len
                new_from = ref_len - old_len
            else:
                new_to = ref_len - old_len
                new_from = ref_len

        return self.update_stationings(
            new_from, new_to, "Nabs"
        )

    def update_stationing_from(self, stationing_xyz_from: float, lr_mode: str)->bool:
        """parses stationing_xyz_from to from-stationings using self.reference_geom and lr_mode
        Only updates metadata, if stationings could be parsed.

        Args:
            stationing_xyz_from (float): numerical stationing from-point
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Returns:
            tuple: (bool: update successfull?, str: error_msg)
        """
        # Rev. 2026-01-13
        parsed_stationings = self.parse_stationing(stationing_xyz_from, lr_mode)
        if parsed_stationings:
            self.snap_n_abs_from = parsed_stationings["snap_n_abs"]
            self.snap_n_fract_from = parsed_stationings["snap_n_fract"]
            self.snap_m_abs_from = parsed_stationings["snap_m_abs"]
            self.snap_m_fract_from = parsed_stationings["snap_m_fract"]
            self.snap_z_abs_from = parsed_stationings["snap_z_abs"]
            self.next_vertex_index_from = parsed_stationings["next_vertex_index"]
            self.snap_x_lyr_from = parsed_stationings["snap_x_lyr"]
            self.snap_y_lyr_from = parsed_stationings["snap_y_lyr"]
            self.snap_x_cvs_from = parsed_stationings["snap_x_cvs"]
            self.snap_y_cvs_from = parsed_stationings["snap_y_cvs"]
            return True

    def update_stationing_to(self, stationing_xyz_to: float, lr_mode: str)->bool:
        """parses stationing_xyz_to to all stationings using self.reference_geom and lr_mode
        Only updates metadata, if stationings could be parsed.

        Args:
            stationing_xyz_to (float): numerical stationing to-point
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Returns:
            bool: update successfull? else: Exception
        """
        # Rev. 2026-01-13
        parsed_stationings = self.parse_stationing(stationing_xyz_to, lr_mode)
        if parsed_stationings:
            self.snap_n_abs_to = parsed_stationings["snap_n_abs"]
            self.snap_n_fract_to = parsed_stationings["snap_n_fract"]
            self.snap_m_abs_to = parsed_stationings["snap_m_abs"]
            self.snap_m_fract_to = parsed_stationings["snap_m_fract"]
            self.snap_z_abs_to = parsed_stationings["snap_z_abs"]
            self.next_vertex_index_to = parsed_stationings["next_vertex_index"]
            self.snap_x_lyr_to = parsed_stationings["snap_x_lyr"]
            self.snap_y_lyr_to = parsed_stationings["snap_y_lyr"]
            self.snap_x_cvs_to = parsed_stationings["snap_x_cvs"]
            self.snap_y_cvs_to = parsed_stationings["snap_y_cvs"]
            return True

    def update_delta_stationings(
        self, segment_length_xyz: float, lr_mode: str, keep: str
    )->bool:
        """update stationings via segment-length

        Args:
            segment_length_xyz (float): new segment-length
            lr_mode (str): Nabs/Nfract/Mabs/Mfract
            keep (str):  from/to/center
                from => from-stationing is kept, to-stationing modified
                to => to-stationing is kept, from-stationing modified
                center => center-point is kept, both stationings modified
        Returns:
            bool: update successfull? else: Exception
        """
        # Rev. 2026-01-13
        if lr_mode == "Nabs":
            if keep == "from":
                new_from = self.snap_n_abs_from
                new_to = self.snap_n_abs_from + segment_length_xyz
            elif keep == "to":
                new_to = self.snap_n_abs_to
                new_from = self.snap_n_abs_to - segment_length_xyz
            elif keep == "center":
                snap_n_abs_center = 0.5 * (self.snap_n_abs_to + self.snap_n_abs_from)
                new_to = snap_n_abs_center + 0.5 * segment_length_xyz
                new_from = snap_n_abs_center - 0.5 * segment_length_xyz
            else:
                raise NotImplementedError(f"keep '{keep}'")
        elif lr_mode == "Nfract":
            if keep == "from":
                new_from = self.snap_n_fract_from
                new_to = self.snap_n_fract_from + segment_length_xyz
            elif keep == "to":
                new_to = self.snap_n_fract_to
                new_from = self.snap_n_fract_to - segment_length_xyz
            elif keep == "center":
                snap_n_fract_center = 0.5 * (
                    self.snap_n_fract_to + self.snap_n_fract_from
                )
                new_to = snap_n_fract_center + 0.5 * segment_length_xyz
                new_from = snap_n_fract_center - 0.5 * segment_length_xyz
            else:
                raise NotImplementedError(f"keep '{keep}'")
        elif lr_mode == "Mabs":
            if self.linestring_statistics.m_enabled:
                if self.linestring_statistics.m_valid:
                    if keep == "from":
                        new_from = self.snap_m_abs_from
                        new_to = self.snap_m_abs_from + segment_length_xyz
                    elif keep == "to":
                        new_to = self.snap_m_abs_to
                        new_from = self.snap_m_abs_to - segment_length_xyz
                    elif keep == "center":
                        snap_m_abs_center = 0.5 * (
                            self.snap_m_abs_to + self.snap_m_abs_from
                        )
                        new_to = snap_m_abs_center + 0.5 * segment_length_xyz
                        new_from = snap_m_abs_center - 0.5 * segment_length_xyz
                    else:
                        raise NotImplementedError(f"keep '{keep}'")
                else:
                    raise GeometryNotMValidException(self.linestring_statistics.m_error)
            else:
                raise GeometryNotMValidException(f"Geometry-Type {self.linestring_statistics.wkbType_name}")
        elif lr_mode == "Mfract":
            if self.linestring_statistics.m_enabled:
                if self.linestring_statistics.m_valid:
                    if keep == "from":
                        new_from = self.snap_m_fract_from
                        new_to = self.snap_m_fract_from + segment_length_xyz
                    elif keep == "to":
                        new_to = self.snap_m_fract_to
                        new_from = self.snap_m_fract_to - segment_length_xyz
                    elif keep == "center":
                        snap_m_fract_center = 0.5 * (
                            self.snap_m_fract_to + self.snap_m_fract_from
                        )
                        new_to = snap_m_fract_center + 0.5 * segment_length_xyz
                        new_from = snap_m_fract_center - 0.5 * segment_length_xyz
                    else:
                        raise NotImplementedError(f"keep '{keep}'")
                else:
                    raise GeometryNotMValidException(self.linestring_statistics.m_error)
            else:
                raise GeometryNotMValidException(f"Geometry-Type {self.linestring_statistics.wkbType_name}")
        else:
            raise NotImplementedError(f"lr_mode '{lr_mode}'")

        return self.update_stationings(new_from, new_to, lr_mode)


    def check_geometry(self,reference_geom:QgsGeometry, check_lr_mode:str)->bool:
        """Checks new geometry for existing LoL-Instance
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
        try:
            stationings_xyz = self.get_stationings(check_lr_mode)

            if stationings_xyz:
                stationing_from_xyz = stationings_xyz[0]
                stationing_to_xyz = stationings_xyz[1]

                self.check_stationing(reference_geom, stationing_from_xyz, check_lr_mode)
                self.check_stationing(reference_geom, stationing_to_xyz, check_lr_mode)

                return True
        except:
            return False



    def update_geometry(self,reference_geom:QgsGeometry, keep_lr_mode:str)->bool:
        """Updates the reference-geometry of a LoL-Instance
        F. e. if the user edits the assigned reference-layer-feature-geometry
        ref_fid stays untouched

        Args:
            reference_geom (QgsGeometry): altered geometry
            keep_lr_mode (str): Determinates lr_mode for stationing recalculation
                Nabs => recalculation conserves snap_n_abs_from/snap_n_abs_to and changes all other stationings (and coordinates)
                Nfract => recalculation conserves snap_n_fract_from/snap_n_fract_to and changes all other stationings (and coordinates)
                Mabs => recalculation conserves snap_m_abs_from/snap_m_abs_to and changes all other stationings (and coordinates)
                Mfract => recalculation conserves snap_m_fract_from/snap_m_fract_to and changes all other stationings (and coordinates)

        Returns:
            bool: update_ok?
        """
        # Rev. 2026-01-13

        # step 1: check geometry
        self.linestring_statistics = LinestringStatistics(reference_geom)


        if not self.linestring_statistics.invalid_reason:
            # step 2: change the reference-geometry
            self.reference_geom = reference_geom

            # step 3: get current stationings for the desired lr_mode
            stationings_xyz = self.get_stationings(keep_lr_mode)

            if stationings_xyz:

                stationing_from_xyz = stationings_xyz[0]
                stationing_to_xyz = stationings_xyz[1]

                # step 4: recaclulate from-stationigs: current_stationing with keep_lr_mode on changed geometry
                parsed_stationings_from = self.parse_stationing(stationing_from_xyz, keep_lr_mode)
                parsed_stationings_to = self.parse_stationing(stationing_to_xyz, keep_lr_mode)

                if parsed_stationings_from and parsed_stationings_to:
                    self.snap_n_abs_from = parsed_stationings_from["snap_n_abs"]
                    self.snap_n_fract_from = parsed_stationings_from["snap_n_fract"]
                    self.snap_m_abs_from = parsed_stationings_from["snap_m_abs"]
                    self.snap_m_fract_from = parsed_stationings_from["snap_m_fract"]
                    self.snap_z_abs_from = parsed_stationings_from["snap_z_abs"]
                    self.next_vertex_index_from = parsed_stationings_from["next_vertex_index"]
                    self.snap_x_lyr_from = parsed_stationings_from["snap_x_lyr"]
                    self.snap_y_lyr_from = parsed_stationings_from["snap_y_lyr"]
                    self.snap_x_cvs_from = parsed_stationings_from["snap_x_cvs"]
                    self.snap_y_cvs_from = parsed_stationings_from["snap_y_cvs"]


                    self.snap_n_abs_to = parsed_stationings_to["snap_n_abs"]
                    self.snap_n_fract_to = parsed_stationings_to["snap_n_fract"]
                    self.snap_m_abs_to = parsed_stationings_to["snap_m_abs"]
                    self.snap_m_fract_to = parsed_stationings_to["snap_m_fract"]
                    self.snap_z_abs_to = parsed_stationings_to["snap_z_abs"]
                    self.next_vertex_index_to = parsed_stationings_to["next_vertex_index"]
                    self.snap_x_lyr_to = parsed_stationings_to["snap_x_lyr"]
                    self.snap_y_lyr_to = parsed_stationings_to["snap_y_lyr"]
                    self.snap_x_cvs_to = parsed_stationings_to["snap_x_cvs"]
                    self.snap_y_cvs_to = parsed_stationings_to["snap_y_cvs"]
                else:
                    raise GeometryConstructException("Stationings could not be parsed")
            else:
                raise PropMissingException(keep_lr_mode)
        else:
            raise GeometryInvalidException(self.linestring_statistics.invalid_reason)




    def update_offset(self, offset: float):
        """checks and sets offset

        Args:
            offset (float): offset to reference-geom, > 0 left, < 0 right, == 0 on the line, defaults to 0

        """
        # Rev. 2026-01-13
        try:
            self.offset = float(offset)
        except:
            raise ArgumentInvalidException("offset",offset)



    def update_stationings(
        self, stationing_xyz_from: float, stationing_xyz_to: float, lr_mode: str
    )->bool:
        """parses stationing_xyz_from and stationing_xyz_to to all stationings using self.reference_geom and lr_mode
        Note:
            only updates metadata, if both stationings could be parsed
            parse-errors are returned, but not written to error-log

        Args:
            stationing_xyz_from (float): numerical stationing from-point
            stationing_xyz_to (float): numerical stationing to-point
            lr_mode (str): Nabs/Nfract/Mabs/Mfract

        Returns:
            bool: update successfull? else: Exception...
        """
        # Rev. 2026-01-13

        parsed_stationings_from = self.parse_stationing(stationing_xyz_from, lr_mode)
        parsed_stationings_to = self.parse_stationing(stationing_xyz_to, lr_mode)
        if parsed_stationings_from and parsed_stationings_to:
            self.snap_n_abs_from = parsed_stationings_from["snap_n_abs"]
            self.snap_n_fract_from = parsed_stationings_from["snap_n_fract"]
            self.snap_m_abs_from = parsed_stationings_from["snap_m_abs"]
            self.snap_m_fract_from = parsed_stationings_from["snap_m_fract"]
            self.snap_z_abs_from = parsed_stationings_from["snap_z_abs"]
            self.next_vertex_index_from = parsed_stationings_from["next_vertex_index"]
            self.snap_x_lyr_from = parsed_stationings_from["snap_x_lyr"]
            self.snap_y_lyr_from = parsed_stationings_from["snap_y_lyr"]
            self.snap_x_cvs_from = parsed_stationings_from["snap_x_cvs"]
            self.snap_y_cvs_from = parsed_stationings_from["snap_y_cvs"]

            self.snap_n_abs_to = parsed_stationings_to["snap_n_abs"]
            self.snap_n_fract_to = parsed_stationings_to["snap_n_fract"]
            self.snap_m_abs_to = parsed_stationings_to["snap_m_abs"]
            self.snap_m_fract_to = parsed_stationings_to["snap_m_fract"]
            self.snap_z_abs_to = parsed_stationings_to["snap_z_abs"]
            self.next_vertex_index_to = parsed_stationings_to["next_vertex_index"]
            self.snap_x_lyr_to = parsed_stationings_to["snap_x_lyr"]
            self.snap_y_lyr_to = parsed_stationings_to["snap_y_lyr"]
            self.snap_x_cvs_to = parsed_stationings_to["snap_x_cvs"]
            self.snap_y_cvs_to = parsed_stationings_to["snap_y_cvs"]

            return True


    @classmethod
    def init_by_stationings(
        cls,
        ref_lyr: QgsVectorLayer,
        ref_fid: int,
        stationing_xyz_from: float,
        stationing_xyz_to: float,
        offset: float,
        lr_mode: str
    )-> tuple:
        """init with reference-feature + stationing_from + stationing_to

        Args:
            ref_lyr (QgsVectorLayer)
            ref_fid (int): feature-id
            stationing_xyz_from (float): numerical stationing from
            stationing_xyz_to (float): numerical stationing to
            offset (float, optional): Distance to reference-line > 0 left, < 0 right, == 0 on the line
            lr_mode (str): Nabs/Nfract/Mabs/Mfract
        Returns:
            tuple (LoL|None, None|error_msg)
        """
        # Rev. 2026-01-13


        lol_instance = cls()
        lol_instance.update_offset(offset)
        if lol_instance.query_reference_geom(ref_lyr, ref_fid):
            lol_instance.update_stationings(
                stationing_xyz_from, stationing_xyz_to, lr_mode
            )
            return lol_instance

    @classmethod
    def init_by_reference_geom(
        cls,
        reference_geom: QgsGeometry,
        ref_crs:QgsCoordinateReferenceSystem,
        stationing_xyz_from: float,
        stationing_xyz_to: float,
        offset: float,
        lr_mode: str
    )->LoL:
        """init with reference_geom + stationing_from + stationing_to

        Args:
            reference_geom (QgsGeometry): Reference-Geometry
            ref_crs (QgsCoordinateReferenceSystem): Projection of geometry
            stationing_xyz_from (float): numerical stationing from
            stationing_xyz_to (float): numerical stationing to
            lr_mode (str): Nabs/Nfract/Mabs/Mfract
            offset (float, optional): Distance to reference-line. Defaults to 0.
        Returns:
            LoL
        """
        # Rev. 2026-01-13
        lol_instance = cls()
        lol_instance.update_offset(offset)
        linestring_statistics = LinestringStatistics(reference_geom)
        if not linestring_statistics.invalid_reason:
            lol_instance.reference_geom = reference_geom
            lol_instance.ref_crs = ref_crs
            lol_instance.linestring_statistics = linestring_statistics
            if lol_instance.update_stationings(
                stationing_xyz_from, stationing_xyz_to, lr_mode
            ):
                return lol_instance
        else:
            raise GeometryInvalidException(linestring_statistics.invalid_reason)

    @classmethod
    def init_by_snap_to_layer(
        cls,
        ref_lyr: QgsVectorLayer,
        point_geom_from: QgsGeometry | QgsPointXY | QgsPoint,
        point_geom_to: QgsGeometry | QgsPointXY | QgsPoint,
        point_geom_crs: QgsCoordinateReferenceSystem,
        snap_tolerance: float,
        ref_lyr_sp_idx: QgsSpatialIndex,
        offset: float,
        snap_mode: str = "prefer_nearest"
    )-> tuple:
        """init with ref_lyr + point_from + point_to

        Args:
            ref_lyr (QgsVectorLayer): Reference-Layer
            point_geom_from (QgsGeometry | QgsPointXY | QgsPoint): From-Geometry, multiple types possible
            point_geom_to (QgsGeometry | QgsPointXY | QgsPoint): To-Geometry, multiple types possible
            point_geom_crs (QgsCoordinateReferenceSystem): Projection of the points
            snap_tolerance (float): max. distance to reference-line
            ref_lyr_sp_idx (QgsSpatialIndex): Spatial-Index with flags=QgsSpatialIndex.FlagStoreFeatureGeometries, speed-up find a fitting reference-line
            offset (float): distance to reference-line, > 0 left, < 0 right, == 0 on the line
            snap_mode (string): prefer_nearest/prefer_start_point. Defaults to prefer_nearest.
        Returns:
            tuple (LoL|None, None|error_msg)
        """
        # Rev. 2026-01-13

        lol_instance = cls()
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
        lol_instance.update_offset(offset)

        if isinstance(ref_lyr, QgsVectorLayer):
            lol_instance.ref_crs = ref_lyr.crs()
            if ref_lyr.dataProvider().wkbType() in linestring_wkb_types:

                if isinstance(point_geom_from, QgsGeometry):
                    # point_geom_from = point_geom_from
                    pass
                elif isinstance(point_geom_from, QgsPointXY):
                    point_geom_from = QgsGeometry.fromPointXY(point_geom_from)
                elif isinstance(point_geom_from, QgsPoint):
                    point_geom_from = QgsGeometry.fromPoint(point_geom_from)
                else:
                    return None, "point_from_geom_type_invald"

                if isinstance(point_geom_to, QgsGeometry):
                    # point_geom_to = point_geom_to
                    pass
                elif isinstance(point_geom_to, QgsPointXY):
                    point_geom_to = QgsGeometry.fromPointXY(point_geom_to)
                elif isinstance(point_geom_to, QgsPoint):
                    point_geom_to = QgsGeometry.fromPoint(point_geom_to)
                else:
                    return None, "point_to_geom_type_invald"

                if isinstance(point_geom_from, QgsGeometry) and isinstance(
                    point_geom_to, QgsGeometry
                ):

                    # transform point_geom from point_geom_crs to reference-crs
                    point_geom_from.transform(
                        QgsCoordinateTransform(
                            point_geom_crs,
                            lol_instance.ref_crs,
                            QgsProject.instance(),
                        )
                    )
                    point_geom_to.transform(
                        QgsCoordinateTransform(
                            point_geom_crs,
                            lol_instance.ref_crs,
                            QgsProject.instance(),
                        )
                    )

                    # identify reference-feature by point_geom_from
                    ref_fid = None
                    # Note: nearestNeighbor returns ids in range of their distance
                    if snap_mode == "prefer_nearest":
                        if snap_tolerance > 0:
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom_from.asPoint(), 1, snap_tolerance
                            )
                        else:
                            # can return multiple fids if equidistant
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom_from.asPoint(), 1
                            )

                        if ref_fids:
                            ref_fid = ref_fids[0]
                        else:
                            return None, "no_nearest_neighbor_within_snap_tolerance"

                    elif snap_mode == "prefer_start_point":
                        if snap_tolerance > 0:
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom_from.asPoint(), 2, snap_tolerance
                            )
                        else:
                            ref_fids = ref_lyr_sp_idx.nearestNeighbor(
                                point_geom_from.asPoint(), 2
                            )

                        if ref_fids:
                            # tricky: query two nearestNeighbors and return the one with smallest lineLocatePoint
                            # simulates Advanced Snapping -> "Line Endpoints" (although the *start*-point is used here)
                            len_dict = {}
                            for ref_fid in ref_fids:
                                reference_feature = ref_lyr.getFeature(ref_fid)
                                if reference_feature.isValid() and reference_feature.hasGeometry():
                                    len_dict[ref_fid] = reference_feature.geometry().lineLocatePoint(
                                        point_geom_from
                                    )
                            # Note: inpredictable if two geometries have the same lineLocatePoint
                            ref_fid = min(len_dict, key=len_dict.get)
                        else:
                            return None, "no_nearest_neighbor_within_snap_tolerance"

                    if ref_fid is not None:
                        if lol_instance.query_reference_geom(ref_lyr, ref_fid):

                            snap_n_abs_from = (
                                lol_instance.reference_geom.lineLocatePoint(
                                    point_geom_from
                                )
                            )
                            snap_n_abs_to = lol_instance.reference_geom.lineLocatePoint(
                                point_geom_to
                            )

                            update_result, error_msg = lol_instance.update_stationings(
                                snap_n_abs_from, snap_n_abs_to, "Nabs"
                            )
                            if update_result:
                                return lol_instance, None
                            else:
                                return None, error_msg

                        else:
                            return None, error_msg
                    else:
                        return None, "no_nearest_neighbor_within_snap_tolerance"

            else:
                return None,"reference_layer_not_type_linestring"
        else:
            return None, "reference_layer_not_type_vector"



    @classmethod
    def init_by_snap_to_feature(
        cls,
        ref_lyr: QgsVectorLayer,
        ref_fid: int,
        point_geom_from: QgsGeometry | QgsPointXY | QgsPoint,
        point_geom_to: QgsGeometry | QgsPointXY | QgsPoint,
        point_geom_crs: QgsCoordinateReferenceSystem,
        offset: float,
        snap_tolerance: float = 0
    )-> tuple:
        """init by pre-fetched ref_fid and point-geometry

        Args:
            ref_lyr (QgsVectorLayer): Reference-Layer
            ref_fid (int): Feature-ID
            point_geom_from (QgsGeometry | QgsPointXY | QgsPoint)
            point_geom_to (QgsGeometry | QgsPointXY | QgsPoint)
            point_geom_crs (QgsCoordinateReferenceSystem): Projection of the points
            offset (float): distance to reference-line, > 0 left, < 0 right, == 0 on the line
            snap_tolerance (float, optional): optional max distance for snapping. Defaults to 0.


        Returns:
            tuple (LoL|None, None|error_msg)
        """
        # Rev. 2026-01-13
        lol_instance = cls()
        lol_instance.update_offset(offset)

        if lol_instance.query_reference_geom(ref_lyr, ref_fid):
            if isinstance(point_geom_from, QgsGeometry):
                # point_geom_from = point_geom_from
                pass
            elif isinstance(point_geom_from, QgsPointXY):
                point_geom_from = QgsGeometry.fromPointXY(point_geom_from)
            elif isinstance(point_geom_from, QgsPoint):
                point_geom_from = QgsGeometry.fromPoint(point_geom_from)
            else:
                return None,"point_from_geom_type_invald"

            if isinstance(point_geom_to, QgsGeometry):
                # point_geom_to = point_geom_to
                pass
            elif isinstance(point_geom_to, QgsPointXY):
                point_geom_to = QgsGeometry.fromPointXY(point_geom_to)
            elif isinstance(point_geom_to, QgsPoint):
                point_geom_to = QgsGeometry.fromPoint(point_geom_to)
            else:
                return None,"point_to_geom_type_invald"

            if isinstance(point_geom_from, QgsGeometry) and isinstance(
                point_geom_to, QgsGeometry
            ):
                # transform point_geom from point_geom_crs to reference-crs
                point_geom_from.transform(
                    QgsCoordinateTransform(
                        point_geom_crs,
                        lol_instance.ref_crs,
                        QgsProject.instance(),
                    )
                )
                point_geom_to.transform(
                    QgsCoordinateTransform(
                        point_geom_crs,
                        lol_instance.ref_crs,
                        QgsProject.instance(),
                    )
                )

                abs_dist_from = lol_instance.reference_geom.distance(point_geom_from)
                abs_dist_to = lol_instance.reference_geom.distance(point_geom_to)

                if not snap_tolerance or (
                    abs_dist_from <= snap_tolerance and abs_dist_to <= snap_tolerance
                ):

                    snap_n_abs_from = lol_instance.reference_geom.lineLocatePoint(
                        point_geom_from
                    )
                    snap_n_abs_to = lol_instance.reference_geom.lineLocatePoint(
                        point_geom_to
                    )
                    update_result, error_msg = lol_instance.update_stationings(
                        snap_n_abs_from, snap_n_abs_to, "Nabs"
                    )

                    if update_result:
                        return lol_instance, None
                    else:
                        return None, error_msg

                else:
                    return None, "snap_tolerance_check_failed"
        else:
            return None, error_msg

    @classmethod


    @classmethod
    def init_by_snap_to_geom(
        cls,
        reference_geom: QgsGeometry,
        ref_crs: QgsCoordinateReferenceSystem,
        point_geom_from: QgsGeometry | QgsPointXY | QgsPoint,
        point_geom_to: QgsGeometry | QgsPointXY | QgsPoint,
        point_geom_crs: QgsCoordinateReferenceSystem,
        offset: float,
        snap_tolerance: float = 0
    )-> tuple:
        """init by reference_geom and point-geometries

        Args:
            reference_geom (QgsGeometry): Reference-Geometry
            ref_crs (QgsCoordinateReferenceSystem): Projection of Geometry
            point_geom_from (QgsGeometry | QgsPointXY | QgsPoint)
            point_geom_to (QgsGeometry | QgsPointXY | QgsPoint)
            point_geom_crs (QgsCoordinateReferenceSystem): Projection of the points
            offset (float): distance to reference-line, > 0 left, < 0 right, == 0 on the line
            snap_tolerance (float, optional): optional max distance for snapping. Defaults to 0.

        Returns:
            tuple (LoL|None, None|error_msg)
        """
        # Rev. 2026-01-13
        lol_instance = cls()

        validated_point_geom_from = None
        if isinstance(point_geom_from, QgsGeometry):
            validated_point_geom_from = point_geom_from
        elif isinstance(point_geom_from, QgsPointXY):
            validated_point_geom_from = QgsGeometry.fromPointXY(point_geom_from)
        elif isinstance(point_geom_from, QgsPoint):
            validated_point_geom_from = QgsGeometry.fromPoint(point_geom_from)
        else:
            return None, "point_from_geom_type_invald"

        validated_point_geom_to = None
        if isinstance(point_geom_to, QgsGeometry):
            validated_point_geom_to = point_geom_to
        elif isinstance(point_geom_to, QgsPointXY):
            validated_point_geom_to = QgsGeometry.toPointXY(point_geom_to)
        elif isinstance(point_geom_to, QgsPoint):
            validated_point_geom_to = QgsGeometry.toPoint(point_geom_to)
        else:
            return None, "point_to_geom_type_invald"

        lol_instance.update_offset(offset)

        if validated_point_geom_from and validated_point_geom_to:
            linestring_statistics = LinestringStatistics(reference_geom)
            if not linestring_statistics.invalid_reason:
                lol_instance.reference_geom = reference_geom
                lol_instance.ref_crs = ref_crs
                lol_instance.linestring_statistics = linestring_statistics

                # transform point_geom from point_geom_crs to reference-crs
                validated_point_geom_from.transform(
                    QgsCoordinateTransform(
                        point_geom_crs, ref_crs, QgsProject.instance()
                    )
                )
                validated_point_geom_to.transform(
                    QgsCoordinateTransform(
                        point_geom_crs, ref_crs, QgsProject.instance()
                    )
                )

                abs_dist_from = reference_geom.distance(validated_point_geom_from)
                abs_dist_to = reference_geom.distance(validated_point_geom_to)
                if not snap_tolerance or (
                    abs_dist_from <= snap_tolerance and abs_dist_to <= snap_tolerance
                ):

                    snap_n_abs_from = reference_geom.lineLocatePoint(validated_point_geom_from)
                    snap_n_abs_to = reference_geom.lineLocatePoint(validated_point_geom_to)
                    update_result, error_msg = lol_instance.update_stationings(
                        snap_n_abs_from, snap_n_abs_to, "Nabs"
                    )
                    if update_result:
                        return lol_instance, None
                    else:
                        return  None, error_msg
                else:
                    return None,"snap_tolerance_check_failed"
            else:
                return None, linestring_statistics.invalid_reason


    def get_from_point_geom(self)->QgsGeometry:
        """get Point-Geometry for snap_n_abs_from on reference_geom

        Returns:
            QgsGeometry
        """
        # Rev. 2026-01-13
        if self.reference_geom:
            if self.snap_n_abs_from is not None:
                point_geom = self.reference_geom.interpolate(self.snap_n_abs_from)
                if point_geom and not point_geom.isEmpty():
                    return point_geom
                else:
                    raise Exception("point_interpolation_failed")
            else:
                raise Exception("snap_n_abs_missing")
        else:
            raise Exception("reference_geom_missing")


    def get_to_point_geom(self)->QgsGeometry:
        """get Point-Geometry for snap_n_abs_to on reference_geom

        Returns:
            QgsGeometry
        """
        # Rev. 2026-01-13
        if self.reference_geom:
            if self.snap_n_abs_to is not None:
                point_geom = self.reference_geom.interpolate(self.snap_n_abs_to)
                if point_geom and not point_geom.isEmpty():
                    return point_geom
                else:
                    raise Exception("point_interpolation_failed")
            else:
                raise Exception("snap_n_abs_missing")
        else:
            raise Exception("reference_geom_missing")


    def geometry(
        self,
        offset: float = None,
        multi_mode: str = 'merge'
    ) -> QgsGeometry:
        """calculate line-segment with optional offset

        Args:
            offset (float, optional): >0 left, < 0 right,  0 on reference line to reference-line.
                Defaults to self.offset
            multi_mode (str, optional): merge/first/last
                Multi-Linien mergen oder das erste/letzte Segment nehmen?
                Defaults to 'merge'.

        Returns:
            QgsGeometry: segment_geom
        """
        # Rev. 2026-01-13

        single_linestring_wkb_types = [
            QgsWkbTypes.LineString25D,
            QgsWkbTypes.LineString,
            QgsWkbTypes.LineStringZ,
            QgsWkbTypes.LineStringM,
            QgsWkbTypes.LineStringZM,
        ]

        multi_linestring_wkb_types = [
            QgsWkbTypes.MultiLineString25D,
            QgsWkbTypes.MultiLineString,
            QgsWkbTypes.MultiLineStringZ,
            QgsWkbTypes.MultiLineStringM,
            QgsWkbTypes.MultiLineStringZM,
        ]

        if offset is None:
            offset = self.offset

        if self.reference_geom:
            if self.snap_n_abs_from is not None:
                if self.snap_n_abs_to is not None:
                    if not self.linestring_statistics:
                        self.linestring_statistics = LinestringStatistics(self.reference_geom)

                    if self.linestring_statistics.n_valid:
                        # switch values, curveSubstring requires from <= to
                        n_from = min(self.snap_n_abs_from, self.snap_n_abs_to)
                        n_to = max(self.snap_n_abs_from, self.snap_n_abs_to)

                        abstr_geom = None
                        if self.reference_geom.wkbType() in single_linestring_wkb_types:
                            abstr_geom = self.reference_geom.constGet()
                        elif self.reference_geom.wkbType() in multi_linestring_wkb_types:
                            # either use the first
                            #
                            # or merge segments, which was already checked => n_valid
                            if multi_mode == 'merge':
                                # Note: always merge on a cloned geometry, else QGis-Crash...
                                # Note 2: already checked with linestring_statistics.n_valid
                                merged_geom = QgsGeometry(self.reference_geom)
                                merged_geom = merged_geom.mergeLines()
                                if merged_geom.wkbType() in single_linestring_wkb_types:
                                    abstr_geom = merged_geom.constGet()
                                else:
                                    raise Exception("geometry_multi_parted")
                            elif multi_mode == 'first':
                                abstr_geom = self.reference_geom.constGet().lineStringN(0)
                            elif multi_mode == 'last':
                                abstr_geom = self.reference_geom.constGet().lineStringN(-1)
                            else:
                                raise Exception("geometry_multi_parted")

                        segment_geom = QgsGeometry(abstr_geom.curveSubstring(n_from, n_to))

                        if segment_geom:
                            if offset:
                                # Bug on QGis in Windows: no Geometry with Offset 0
                                # distance – buffer distance
                                # segments – for round joins, number of segments to approximate quarter-circle
                                # joinStyle – join style for corners in geometry
                                # miterLimit – limit on the miter ratio used for very sharp corners (JoinStyleMiter only)
                                segment_geom = segment_geom.offsetCurve(
                                    offset, 8, Qgis.JoinStyle.Round, 0
                                )
                            return segment_geom
                        else:
                            # empty geometry
                            raise Exception("curveSubstring_failed")
                    else:
                        raise Exception("reference_geom_invalid")
                else:
                    raise Exception("snap_n_abs_to_missing")
            else:
                raise Exception("snap_n_abs_from_missing")
        else:
            raise Exception("reference_geom_missing")



