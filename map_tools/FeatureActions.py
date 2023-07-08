#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin **LinearReferencing**:
* attribute-actions for data-layers and virtual-layers in the LinearReference-Plugin
.. note::
    * added to data_layers and virtual-layers as action
    * accessible from tables and forms

********************************************************************

* Date                 : 2023-02-12
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""

import qgis
from qgis._core import QgsProject

from PyQt5 import QtCore

from LinearReferencing.tools.MyDebugFunctions import debug_print

from LinearReferencing.tools.MyDebugFunctions import get_debug_pos as gdp

# runs outside plugin or console, so the iface-Variable is initially unset and here resetted as global variable within this module
iface = qgis.utils.iface

_plugin_name = 'LinearReferencing'

from LinearReferencing.tools.MyToolFunctions import qt_format

def edit_line_on_line_feature(fid: int, layer_id: str, zoom_to_feature: bool) -> None:
    """
    Attached to layer.actions, select LinearReferencing-LOL-Feature for edit from table or form

    Sample-Code for Action (a QGis expression, where some marked [%...%] wildcards will be replaced by current values):
    .. code-block:: text

        from LinearReferencing.map_tools.FeatureActions import edit_point_on_line_feature
        edit_point_on_line_feature([%@id%],'[%@layer_id%]')

    :param fid: in action-code the wildcard ``[%@id%]`` will be replaced with the fid of the current feature.
    :param layer_id: in action-code the Wildcard ``[%@layer_id%]`` will be replaced with the ID of the layer, data-layer or show-layer from Map-Tool PolEvt accepted
    :param zoom_to_feature: True ➜ zoom canvas False ➜ just select and highlight see LolEvt.set_edit_pk()
    """

    if _plugin_name in qgis.utils.plugins:
        lref_plugin = qgis.utils.plugins[_plugin_name]
        """access initialized Plugin"""

        if not lref_plugin.mt_LolEvt:
            lref_plugin.set_map_tool_LolEvt()

        if lref_plugin.mt_LolEvt:
            # QgsMapToolEmitPoint: PolEvt initialized MapTool
            mt = lref_plugin.mt_LolEvt
            mt.my_dialogue.show()

            data_or_show_lyr = QgsProject.instance().mapLayer(layer_id)


            if data_or_show_lyr == mt.ds.dataLyr:
                if mt.cf.data_layer_complete:
                    data_feature = data_or_show_lyr.getFeature(fid)
                    if data_feature.isValid():
                        edit_pk = data_feature[mt.ds.dataLyrIdField.name()]
                        mt.set_edit_pk(edit_pk, zoom_to_feature)
                        mt.my_dialogue.edit_grb.setChecked(1)
                        mt.my_dialogue.selection_grb.setChecked(1)
                    else:
                        mt.push_messages(critical_msg=qt_format(QtCore.QCoreApplication.translate('FeatureActions',"no valid Feature for FID '{0}' in Layer '{1}'..."),fid,layer_id))
                else:
                    mt.my_dialogue.tbw_central.setCurrentIndex(1)
                    mt.push_messages(critical_msg=QtCore.QCoreApplication.translate('FeatureActions',"Data-Layer not fully configured in LinearReferencing Line-on-Line-Settings..."))

            elif data_or_show_lyr == mt.ds.showLyr:
                if mt.cf.show_layer_complete:
                    show_feature = data_or_show_lyr.getFeature(fid)
                    if show_feature.isValid():
                        edit_pk = show_feature[mt.ds.showLyrBackReferenceField.name()]
                        mt.set_edit_pk(edit_pk, zoom_to_feature)
                        mt.my_dialogue.edit_grb.setChecked(1)
                        mt.my_dialogue.selection_grb.setChecked(1)
                    else:
                        mt.push_messages(critical_msg=qt_format(QtCore.QCoreApplication.translate('FeatureActions',f"no valid Feature for FID {apos}{0}{apos} in Layer {apos}{1}{apos}..."),fid,layer_id))
                else:
                    mt.my_dialogue.tbw_central.setCurrentIndex(1)
                    mt.push_messages(critical_msg=QtCore.QCoreApplication.translate('FeatureActions',"Show-Layer not fully configured in LinearReferencing Line-on-Line-Settings..."))


            else:
                # called from a table, which currently not registered in the Plugin-map-tool as data-layer or virtual-layer
                mt.my_dialogue.tbw_central.setCurrentIndex(1)
                mt.push_messages(critical_msg=qt_format(QtCore.QCoreApplication.translate('FeatureActions',"Layer {apos}{0}{apos} not registered as Data- or Show-Layer, please configure LinearReferencing Line-on-Line-Settings..."),data_or_show_lyr.name()))
        else:
            iface.messageBar().pushMessage("Plugin 'LinearReferencing' not configured...",level=qgis.core.Qgis.Critical, duration=20)
    else:
        iface.messageBar().pushMessage("Plugin 'LinearReferencing' required, please install and enable!",level=qgis.core.Qgis.Critical, duration=20)





def edit_point_on_line_feature(fid: int, layer_id: str, pan_to_feature: bool) -> None:
    """
    Attached to layer.actions, select LinearReferencing-Pol-Feature for edit from table or form


    Sample-Code for Action (a QGis expression, where some marked [%...%] wildcards will be replaced by current values):
    .. code-block:: text

        from LinearReferencing.map_tools.FeatureActions import edit_point_on_line_feature
        edit_point_on_line_feature([%@id%],'[%@layer_id%]')


    :param fid: in action-code the wildcard ``[%@id%]`` will be replaced with the fid of the current feature.
    :param layer_id: in action-code the Wildcard ``[%@layer_id%]`` will be replaced with the ID of the layer, data-layer or show-layer from Map-Tool PolEvt accepted
    :param pan_to_feature: True ➜ pan canvas False ➜ just select and highlight see PolEvt.set_edit_pk()
    """

    if _plugin_name in qgis.utils.plugins:
        lref_plugin = qgis.utils.plugins[_plugin_name]
        """access initialized Plugin"""

        if not lref_plugin.mt_PolEvt:
            lref_plugin.set_map_tool_PolEvt()

        if lref_plugin.mt_PolEvt:
            # QgsMapToolEmitPoint: PolEvt initialized MapTool
            mt = lref_plugin.mt_PolEvt
            mt.my_dialogue.show()
            data_or_show_lyr = QgsProject.instance().mapLayer(layer_id)
            if data_or_show_lyr == mt.ds.dataLyr:
                if mt.cf.data_layer_complete:
                    data_feature = data_or_show_lyr.getFeature(fid)
                    if data_feature.isValid():
                        edit_pk = data_feature[mt.ds.dataLyrIdField.name()]
                        mt.set_edit_pk(edit_pk, pan_to_feature)
                        mt.my_dialogue.edit_grb.setChecked(1)
                        mt.my_dialogue.selection_grb.setChecked(1)
                    else:
                        mt.push_messages(critical_msg=qt_format(QtCore.QCoreApplication.translate('FeatureActions',"no valid Feature for FID {apos}{0}{apos} in Layer {apos}{1}{apos}..."),fid,layer_id))
                else:
                    mt.push_messages(critical_msg=QtCore.QCoreApplication.translate('FeatureActions',"Data-Layer not fully configured in LinearReferencing Point-on-Line-Settings..."))
                    mt.my_dialogue.tbw_central.setCurrentIndex(1)
            elif data_or_show_lyr == mt.ds.showLyr:
                if mt.cf.show_layer_complete:
                    show_feature = data_or_show_lyr.getFeature(fid)
                    if show_feature.isValid():
                        edit_pk = show_feature[mt.ds.showLyrBackReferenceField.name()]
                        mt.set_edit_pk(edit_pk, pan_to_feature)
                        mt.my_dialogue.edit_grb.setChecked(1)
                        mt.my_dialogue.selection_grb.setChecked(1)
                    else:
                        mt.push_messages(critical_msg=qt_format(QtCore.QCoreApplication.translate('FeatureActions',"no valid Feature for FID {apos}{0}{apos} in Layer {apos}{1}{apos}..."),fid,layer_id))
                else:
                    mt.push_messages(critical_msg=QtCore.QCoreApplication.translate('FeatureActions',"Show-Layer not fully configured in LinearReferencing Point-on-Line-Settings..."))
                    mt.my_dialogue.tbw_central.setCurrentIndex(1)
            else:
                # called from a table, which currently not registered in the Plugin-map-tool as data-layer or virtual-layer
                mt.push_messages(critical_msg=qt_format(QtCore.QCoreApplication.translate('FeatureActions',"Layer {apos}{0}{apos} not registered as Data- or Show-Layer, please configure LinearReferencing Point-on-Line-Settings..."),data_or_show_lyr.name()))
                mt.my_dialogue.tbw_central.setCurrentIndex(1)
        else:
            iface.messageBar().pushMessage("Plugin 'LinearReferencing' not configured...", level=qgis.core.Qgis.Critical, duration=20)
    else:
        iface.messageBar().pushMessage("Plugin 'LinearReferencing' required, please install and enable!",level=qgis.core.Qgis.Critical, duration=20)


