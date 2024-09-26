# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* initializes and returns the plugin

********************************************************************

* Date                 : October 2014, May 2016 and August 2018
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""


from qgis._gui import QgisInterface
from LinearReferencing.tools.MyDebugFunctions import debug_print


def classFactory(iface:QgisInterface):
    """reimplemented function for initialization of the plugin
    :param iface:
    """
    
    from .LinearReference import LinearReference
    return LinearReference(iface)



