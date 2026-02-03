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
    * from LinearReferencing.tools.MyTools import open_attribute_table

********************************************************************
"""
from __future__ import annotations
import sys,typing, math, locale, sqlite3, re, numbers

import collections.abc
from typing import Any, Generator

from PyQt5.QtGui import QCursor, QStandardItem

from PyQt5.QtWidgets import (
    QApplication, QDialog, QWidget
)

from PyQt5.QtCore import QLocale, QSettings, Qt, QMetaObject, QPoint, QSignalBlocker, QVariant, QTimer


from qgis.core import (
    QgsGeometry,
    QgsAbstractGeometry,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsRectangle,
    QgsPointXY,
    Qgis,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsMultiLineString,
    QgsLineString,
    QgsPoint,
    QgsField,
    QgsFeature,
    QgsFeatureRequest,
    QgsProject,
    QgsVectorDataProvider,
    QgsFeatureIterator,
    QgsVertexId,
    NULL,
    QgsUnsetAttributeValue,
)

from qgis.gui import QgisInterface, QgsAttributeDialog

from typing import Any


from LinearReferencing.settings.exceptions import *

from LinearReferencing.tools.MyDebugFunctions import (
    debug_log,
    get_debug_pos,
)


sqlite_conn = sqlite3.connect(":memory:")
spatialite_conn = None
try:
    sqlite_conn.enable_load_extension(True)
    # Bug in macOS
    sqlite_conn.execute('SELECT load_extension("mod_spatialite")')
    sqlite_conn.execute("SELECT InitSpatialMetaData();")
    spatialite_conn = sqlite_conn
except Exception as e:
    spatialite_conn = None

locale.setlocale(locale.LC_ALL, "")


def get_field_values(vl:QgsVectorLayer,field:QgsField|int|str)->set:
    """get set of field-values from layer

    Args:
        vl (QgsVectorLayer):
        field (QgsField|int|str): field/name/index

    Returns:
        set: unique field-values
    """
    # -1 if field not found => empty set
    fidx = -1
    if isinstance(field, str):
        # quite tolerant: case insensitiv and client-side-alias (case insensitive) accepted
        # these tolerance is accepted in QgsFeatureRequest, too
        fidx = vl.fields().lookupField(field)
    elif isinstance(field, QgsField):
        fidx = vl.fields().lookupField(field.name())
    elif isinstance(field, int):
        fidx = field
    else:
        raise TypeError('field_definition_invalid')

    return vl.uniqueValues(fidx)

def list_intersection(check_list:list, in_list:list)->list:
    """returns common elements from check_list and in_list, used f.e. in cvs_draw_lr_geom to find drawable geometries

    Args:
        check_list (list)
        in_list (list)

    Returns:
        list: common values from both lists, unique
    """
    # Rev. 2025-11-22
    return list(set(check_list).intersection(set(in_list)))

def list_difference(check_list:list, in_list:list)->list:
    """returns differences between check_list and in_list, used f.e. in cvs_draw_lr_geom to identify false keys

    Args:
        check_list (list)
        in_list (list)

    Returns:
        list: values from check_list not existing in in_list, unique
    """
    # Rev. 2025-11-22
    return list(set(check_list) - set(in_list))


def check_attribute_value(attribute_value:Any)->bool:
    """check if single attribute-value is set and usable f.e. for relations or feature-inserts/updates

    Args:
        attribute_value (Any)

    Returns:
        bool
    """
    # Rev. 2025-10-26
    return attribute_value != NULL and not isinstance(attribute_value,QVariant) and not isinstance(attribute_value,QgsUnsetAttributeValue)



def sys_get_locale() -> QLocale:
    """check QSettings affecting number format
        QGis > Settings > Options > Override System Locale > Locale (numbers, date and currency formats)
        QGis > Settings > Options > Override System Locale > Show group (thousand) seperator

    Returns:
        QLocale
    """
    # Rev. 2025-10-04
    if QSettings().value("locale/overrideFlag", type=bool):
        # => lcid in QGis differing from system-settings
        # default: 'en_US' (if overrideFlag is set but no userLocale defined)
        # globalLocale => QGis-Options-Dialog "Locale (numbers, date and currency formats)"
        lcid = QSettings().value("locale/globalLocale", "en_US")
    else:
        # take the system-lcid
        lcid = QLocale.system().name()

    my_locale = QLocale(lcid)

    # caveat: this value is read from QGIS.ini, therefore the returned value can be a non-boolean as f.e. 'false'
    show_group_separator = QSettings().value("locale/showGroupSeparator", True) in [
        True,
        "True",
        "true",
        "1",
        1,
    ]

    if show_group_separator:
        my_locale.setNumberOptions(
            my_locale.numberOptions() | ~QLocale.OmitGroupSeparator
        )
    else:
        my_locale.setNumberOptions(
            my_locale.numberOptions() | QLocale.OmitGroupSeparator
        )

    return my_locale


def get_mods() -> dict:
    """get list of certain keyboard modifiers used for the current event

    Returns:
        dict: dict key: n/s/c/a/m value: bool, if this KeyboardModifier is currently in use
    """
    # Rev. 2025-01-15
    all_mods = {
        "n": Qt.NoModifier,
        "s": Qt.ShiftModifier,
        "c": Qt.ControlModifier,
        "a": Qt.AltModifier,  # on Linux: move window
        "m": Qt.MetaModifier,  # will open StartMenu after release
    }

    return_value = {}
    for check_mod in all_mods:
        mod = all_mods.get(check_mod)
        if mod == Qt.NoModifier:
            # binärer Sonderfall für NoModifier (int 0, binär 00000):
            # 11111 & 00000 = 00000 bool False
            # 00000 & 00000 = 00000 bool auch False !
            # => auf Gleicheit checken
            # 00000 == 00000 ? True
            return_value[check_mod] = bool(QApplication.keyboardModifiers() == mod)
        else:
            # binärer Regelfall für alle anderen (check auf mindestens ein an gleicher Position gesetztes Einzelbit):
            # 10011 & 00010 = 00010 => bool True
            return_value[check_mod] = bool(QApplication.keyboardModifiers() & mod)
    return return_value


def check_mods(check_mods: str = "")->bool:
    """checks combination of keyboard-modifier
    Combinations must be checked before singles!

    Sample:

        if check_mods():
            # no modifiers
            pass
        elif check_mods('cs'):
            # ctrl + shift
            pass
        elif check_mods('s'):
            # shift
            pass
        elif check_mods('c'):
            # ctrl
            pass
        else:
            # anything else
            pass

    Args:
        check_mods (str, optional): string with chars 'n' (NoModifier) 's' (ShiftModifier) 'c' (ControlModifier) 'a' (AltModifier) 'm' (MetaModifier) or empty (=='n', NoModifier) and '+' (and) or '|' (or) for combinator (default '+' and). Defaults to "".

    Raises:
        NotImplementedError: if one of the check_mods is not a key in the dict returned from get_mods (n/s/c/a/m)

    Returns:
        bool:
    """
    modifiers = get_mods()

    # only one kind of combinator
    combinator = "or" if "|" in check_mods else "and"

    check_mods = check_mods.replace("+", "")
    check_mods = check_mods.replace("|", "")

    if check_mods == "":
        check_mods = "n"

    if combinator == "and":
        for check_mod in check_mods:
            if check_mod in modifiers:
                if not modifiers.get(check_mod):
                    return False
            else:
                raise NotImplementedError(
                    f"keyboardModifier '{check_mod}' not implemented!"
                )
        # all checks done, no return so far
        return True

    else:
        for check_mod in check_mods:
            if check_mod in modifiers:
                if modifiers.get(check_mod):
                    # one of the modifiers was pressed!
                    return True
            else:
                raise NotImplementedError(
                    f"keyboardModifier '{check_mod}' not implemented!"
                )

    return False







def find_attribute_tables(
    iface: QgisInterface,
    vl: QgsVectorLayer,
    include_docked: bool = False,
) -> list:
    """searches for attribute-tables of a specific layer
    rather complicated because
    - these dialogs are QDockWidgets docked/floating in iface.mainWindow() or TopLevel-Widgets (toggle by small icon top right "Dock Attribute Table")
    - identified by objectName(): QgsAttributeTableDialog/layer-id

    Args:
        iface (QgisInterface):
        vl (QgsVectorLayer): find attribute-tables for this layer
        include_docked (bool, optional): include docked attribute-tables, which belong to iface.mainWindow(). Defaults to False.

    Returns:
        list: list of attribute_table_widgets
    """
    # Rev. 2025-10-04
    attribute_tables = []

    # TopLevelWidget (QDialog containing QDialog)
    top_level_dialogs = [
        wdg for wdg in QApplication.topLevelWidgets() if isinstance(wdg, QDialog)
    ]
    for dlg in top_level_dialogs:
        top_level_sub_dialogs = dlg.findChildren(
            QDialog, options=Qt.FindDirectChildrenOnly
        )
        for sub_dlg in top_level_sub_dialogs:
            if f"QgsAttributeTableDialog/{vl.id()}" in sub_dlg.objectName():
                attribute_tables.append(sub_dlg)

    if include_docked:
        # QDockWidget:
        main_window_dialogs = iface.mainWindow().findChildren(
            QDialog, options=Qt.FindChildrenRecursively
        )
        for dlg in main_window_dialogs:
            if f"QgsAttributeTableDialog/{vl.id()}" in dlg.objectName():
                attribute_tables.append(dlg)

    return attribute_tables


def open_attribute_table(
    iface: QgisInterface,
    vl: QgsVectorLayer,
    new_if_missing: bool = True,
):
    """opens rsp. re-opens an attribute-table for a layer

    Note: no Exception, if layer is None

    Args:
        iface (QgisInterface)
        vl (QgsVectorLayer)
        new_if_missing (bool, optional): opens a new attribute-table, if none was found. Defaults to True.
    """
    # Rev. 2025-10-04

    if isinstance(vl,QgsVectorLayer):
        attribute_tables = find_attribute_tables(iface, vl, False)
        if attribute_tables:
            vl.reload()
            last_dlg = attribute_tables[-1]
            last_dlg.show()
            last_dlg.activateWindow()
        else:
            if new_if_missing:
                iface.showAttributeTable(vl)
    else:
        raise LayerNotFoundException()


def show_feature_form(
    iface: QgisInterface,
    vl: QgsVectorLayer,
    feature_id: int
):
    """replacement for iface.openFeatureForm()
    ensures only one feature-form for the same feature
    re-freshes and focusses existing feature-form for this layer/feature

    Args:
        iface (QgisInterface)
        vl (QgsVectorLayer)
        feature_id (int)

    Raises:
        FeatureNotFoundException
        ArgumentInvalidException
        LayerNotFoundException

    Returns:
        QgsAttributeDialog | None: Attribute-Dialog see https://api.qgis.org/api/classQgsAttributeDialog.html or None, if feature exists no more
    """
    # Rev. 2026-01-16

    if isinstance(vl,QgsVectorLayer):
        if isinstance(feature_id,int):
            # current "fresh" feature with all intermediate uncommitted/committed edits
            cf = vl.getFeature(feature_id)
            if cf and cf.isValid():
                # ObjectName, used from iface.openFeatureForm to identify the dialog
                my_object_name = f"featureactiondlg:{vl.id()}:{feature_id}"
                for dialog in iface.mainWindow().findChildren(QDialog):
                    # Highlander, forces dialog-reload with actual feature
                    if dialog.objectName() == my_object_name:
                        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
                        dialog.close()
                        # delayed recall
                        QTimer.singleShot(10, lambda iface=iface,vl=vl,feature_id=feature_id: show_feature_form(iface, vl,feature_id))
                        return
                iface.openFeatureForm(vl,cf,False,False)
            else:
                raise FeatureNotFoundException(vl.name(),feature_id)
        else:
            raise ArgumentInvalidException("feature_id",feature_id)
    else:
        raise LayerNotFoundException()

def qtrv_extract_items(
    qtrv, col_idx: int, role: int = None, value: Any = None
) -> collections.abc.Iterable:
    """Items einer Spalte/Rolle aus der rekursiven Struktur zurückliefern

    Args:
        col_idx (int): nur diese Spalte untersuchen
        role (int, optional): optionaler Filter auf eine spezielle Rolle in dieser Spalte
        value (Any, optional): optionaler Filter auf einen Wert dieser Spalte und Rolle

    Raises:
        Exception: if called before any data was loaded

    Returns:
        collections.abc.Iterable: [QStandardItem]

    Yields:
        tuple(QStandardItem)
    """

    # Rev. 2025-01-26

    def recurse(parent: QStandardItem) -> Generator[QStandardItem, None, None]:
        for row in range(parent.rowCount()):
            # the filtered column
            child_n = parent.child(row, col_idx)
            # can be None
            if child_n:
                if role is not None:
                    if value is not None:
                        if child_n.data(role) == value:
                            yield (child_n)
                    else:
                        if child_n.data(role) is not None:
                            yield (child_n)
                else:
                    yield (child_n)

            # column 0 in this row, contains the self-reference
            child_0 = parent.child(row, 0)
            if child_0.hasChildren():
                yield from recurse(child_0)

    if qtrv.model():
        root = qtrv.model().invisibleRootItem()
        if root is not None:
            yield from recurse(root)
    else:
        # raise in generator-functions can kill the process
        raise Exception(
            "MyQtTreeView: no model() => no data loaded, extract_values not possible..."
        )


def select_by_value(
    wdg_with_model: QWidget,
    select_value: str | float | int,
    col_idx: int = 0,
    role_idx: int = 0,
):
    """helper-function that selects an item in a QComboBox by its value, blocks any signals

    Args:
        wdg_with_model (QWidget): Widget wit a model, e.g. QComboBox
        select_value (str | float | int): the compare-value
        col_idx (int, optional): the index of the column of the data-model, whose data will be compared, always 0 with QComboBox. Defaults to 0.
        role_idx (int, optional): the role in the items, whose data will be compared, see https://doc.qt.io/qt-5/qt.html#ItemDataRole-enum, mostly Qt.DisplayRole or Qt.UserRole
            0 -> DisplayRole (Text of the option)
            256 -> UserRole (Data of the option). Defaults to 0.
    """
    # Rev. 2025-10-04
    first_item_idx = wdg_with_model.model().index(0, col_idx)
    # param 4 "-1": limits num of matches, here -1 -> no  limit, return all matches
    matching_items = wdg_with_model.model().match(
        first_item_idx, role_idx, select_value, -1, Qt.MatchExactly
    )
    if matching_items:
        first_matching_item = matching_items.pop(0)
        with QSignalBlocker(wdg_with_model):
            wdg_with_model.setCurrentIndex(first_matching_item.row())





def get_feature_by_value(
    vlayer: QgsVectorLayer,
    field: QgsField | str | int,
    value: typing.Any,
) -> QgsFeature:
    """Returns first feature from layer by query on a single value,
    intended for use on PK-field and PK-Value, where only one feature is expected

    Args:
        vlayer (QgsVectorLayer)
        field (QgsField | str): queryable-attribute, can be a QgsField or the name of a QgsField or the field-index
        value (typing.Any): any queryable-attribute-value, usually numeric or string, will be used in FilterExpression with 'value'

    Raises:
        FieldNotFoundException
        ArgumentInvalidException
        QueryResultEmptyException (!)

    Returns:
        QgsFeature
    """
    # Rev. 2025-01-08
    # return the first feature
    request = QgsFeatureRequest()
    field_name = None
    if isinstance(field, str):
        # quite tolerant: case insensitiv and client-side-alias (case insensitive) accepted
        # these tolerance is accepted in QgsFeatureRequest, too
        fidx = vlayer.fields().lookupField(field)
        if fidx >= 0:
            field_name = field
        else:
            raise FieldNotFoundException(vlayer.name(),field)
    elif isinstance(field, QgsField):
        field_name = field.name()
    elif isinstance(field, int):
        if 0 <= field < vlayer.fields().size():
            field_name = vlayer.fields().at(field).name()
        else:
            raise FieldNotFoundException(vlayer.name(),field)
    else:
        raise ArgumentInvalidException("field",field)

    if field_name:
        try:
            request.setFilterExpression(f"\"{field_name}\" = '{value}'")
            # next raises StopIteration, if query-result is empty
            return next(vlayer.getFeatures(request))
        except StopIteration:
            raise QueryResultEmptyException(vlayer.name(),field,value)
        # all other Exceptions will bubble up



def select_in_layer(layer_id: str, feature_id: int, iface:QgisInterface):
    """select feature in associated layer"""
    # Rev. 2026-01-12
    vl = QgsProject.instance().mapLayer(layer_id)
    if vl and isinstance(vl, QgsVectorLayer):
        cf = vl.getFeature(feature_id)
        if cf and cf.isValid():
            if check_mods("c"):
                vl.deselect(feature_id)
            elif check_mods("s"):
                vl.select(feature_id)
            else:
                vl.removeSelection()
                vl.select(feature_id)
        else:
            raise FeatureNotFoundException(vl.name(),feature_id)
    else:
        raise LayerNotFoundException(layer_id)


def get_unique_string(used_strings: list, template: str, start_i: int = 1) -> str:
    """get unique string replacing Wildcard {curr_i} with incremented integer
    escaped wildcard if template defined as f-string: {{curr_i}}

    Args:
        used_strings (list): List of already used strings, f.e. table-names in a GeoPackage or layer in QGis-Project [layer.name() for layer in  QgsProject.instance().mapLayers().values()]
        template (str): template with Wildcard {curr_i}
        start_i (int, optional): start index for incrementing. Defaults to 1.

    Returns:
        str
    """
    # Rev. 2025-10-09

    if not '{curr_i}' in template:
        template += ' {curr_i}'

    while True:
        return_string = template.format(curr_i=start_i)
        if not return_string in used_strings:
            return return_string
        start_i += 1


@staticmethod
def get_features_by_value(
    vlayer: QgsVectorLayer,
    field: QgsField | str | int,
    value: typing.Any,
) -> list:
    """Returns all features from layer by query on a single value,
    intended f.e. to query all data-features assigned to the same reference-feature

    Args:
        vlayer (QgsVectorLayer)
        field (QgsField | str): queryable-attribute, can be a QgsField or the name of a QgsField or the field-index
        value (typing.Any): any queryable-attribute-value, usually numeric or string, will be used in FilterExpression with 'value'

    Returns:
        list [QgsFeature] (may be empty)
    """
    # Rev. 2025-01-08
    fl = []
    request = QgsFeatureRequest()
    field_name = None
    if isinstance(field, str):
        # quite tolerant: case insensitiv and client-side-alias (case insensitive) accepted
        # these tolerance is accepted in QgsFeatureRequest, too
        fidx = vlayer.fields().lookupField(field)
        if fidx >= 0:
            field_name = field
        else:
            raise Exception('field_not_found')
    elif isinstance(field, QgsField):
        field_name = field.name()
    elif isinstance(field, int):
        if 0 <= field < vlayer.fields().size():
            field_name = vlayer.fields().at(field).name()
        else:
            raise IndexError('field_index_out_of_bounds')
    else:
        raise TypeError('field_definition_invalid')

    if field_name:
        request.setFilterExpression(f"\"{field_name}\" = '{value}'")
        fl = list(vlayer.getFeatures(request))

    return fl
