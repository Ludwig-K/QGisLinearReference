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
# Icons: https://materialdesignicons.com/

def classFactory(iface):
    '''Zentrale Funktion zur Initialisierung aller Plugins,
    Rückgabewert ist ein Objekt mit bestimmten Methoden, die bei der Aktivierung des Plugins ausgeführt werden'''
    from .MyPlugin import LinearReferencePlugin
    return LinearReferencePlugin(iface)



