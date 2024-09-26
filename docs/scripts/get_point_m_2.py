from qgis.core import *
from qgis.gui import *

@qgsfunction(group='Custom', referenced_columns=[],usesgeometry=False)
def get_point_m_2(in_geom: qgis.core.QgsGeometry, stationing_m: float) -> float:
    """similar as PostGis or SQLite st_line_locate_point
    works on multi-geometries, scanning each part
    returns first hit (stationing_m between last and current vertex-m)
    expects m-values (strictly) ascending, else no hit traversing the vertices
    performance is dependend on the number of iterations (number of runs until hit => number of vertices and position of hit in the front or rear area of the line)
    :param in_geom:
    :param stationing_m:
    :returns: stationing_n
    Note: Custom Python expression functions should return a single QVariant-compatible value
    if used as a normal Python function outside the expression builder, it could return a lot of useful information, this return part is commented below
    :raise: TypeError if in_geom is Null or has wrong type
    """
    abstr_geom = in_geom.constGet()
    if abstr_geom:
        if abstr_geom.wkbType() in [Qgis.WkbType.LineStringM , Qgis.WkbType.LineStringZM, Qgis.WkbType.MultiLineStringM, Qgis.WkbType.MultiLineStringZM]:
            if isinstance(abstr_geom, qgis.core.QgsLineString):
                # only one geometry
                geom_parts = [abstr_geom]
            elif isinstance(abstr_geom, qgis.core.QgsMultiLineString):
                # list of sub-geometries, even if there is only one
                geom_parts = abstr_geom
            else:
                # empty geometry
                raise TypeError('function called with empty geometry')
                return
            
            part_idx = 0
            for geom_part in geom_parts:
                p_min_m = geom_part[0].m()
                p_max_m = geom_part[-1].m()
                # pre-check this part to avoid useless sequential scans
                if stationing_m >= p_min_m and stationing_m <= p_max_m:
                    # initial value
                    last_vertex = geom_part[0]
                    stationing_n = 0
                    # iterate through all vertices...
                    for vertex_idx in range(1, geom_part.vertexCount()):
                        current_vertex = geom_part[vertex_idx]
                        delta_x = current_vertex.x() - last_vertex.x()
                        delta_y = current_vertex.y() - last_vertex.y()
                        # Note: vertices have z- and m-property, even if the geometry-type has not
                        delta_z = current_vertex.z() - last_vertex.z()
                        delta_n = (delta_x**2 + delta_y**2)**.5
                        # ... and stop as soon as stationing_m is in range last_vertex.m() ... current_vertex.m()
                        if last_vertex.m() <= stationing_m and current_vertex.m() > stationing_m:
                            # proportional distribution
                            delta_m = (stationing_m - last_vertex.m()) / (current_vertex.m() - last_vertex.m())
                            
                            x = last_vertex.x() + delta_m * delta_x
                            y = last_vertex.y() + delta_m * delta_y
                            z = last_vertex.z() + delta_m * delta_z
                            
                            stationing_n += delta_m * delta_n
                            
                            # return-variant 1 (for use as normal Python-Function outside expressions): tuple of multiple values
                            # point_geom = qgis.core.QgsGeometry(qgis.core.QgsPoint(x, y, z, stationing_m))
                            # return point_geom, stationing_n, part_idx, vertex_idx-1
                            # return-variant 2 (for use as custom Python expression function): single QVariant-compatible value
                            return stationing_n
                        
                        # accumulation of the natural stationing
                        stationing_n += delta_n
                        last_vertex = current_vertex
                        
                part_idx += 1
        else:
            raise TypeError(F"function called with wrong geometry-type, required: '(Multi)LineString(Z)M' current: '{abstr_geom.wkbType().name}'")
                
    else:
        raise TypeError(F"function called with wrong geometry-type required: '(Multi)LineString(Z)M' current: '{in_geom}'")