#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* some Debug-Tool-Functions

.. note::
    * to import these methods for usage in python console:
    * import LinearReferencing.tools.MyDebugFunctions
    * from LinearReferencing.tools.MyDebugFunctions import get_vlayer_metas


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

import pathlib, tempfile, os, sys, datetime

import io
import qgis
from PyQt5.QtCore import QMetaType, QEvent, qDebug
from PyQt5.QtWidgets import QApplication
from qgis._core import QgsProject, QgsVectorLayer, QgsRasterLayer
from qgis.core import QgsApplication, QgsWkbTypes


def get_debug_pos(back_steps: int = 1) -> str:
    """returns debug-footprint (Filename + Line-Number) for Messages
    :param back_steps: normally 1 -> get File/Line from Function, which called get_debug_pos
    """

    frame = sys._getframe(0)  # current get_debug_pos function

    for bs in range(back_steps):
        frame = frame.f_back

    return f"{os.path.basename(os.path.realpath(frame.f_code.co_filename))} #{frame.f_lineno}"


def get_debug_file_line(back_steps: int = 1) -> tuple:
    """returns debug-footprint (Path + Line-Number)
    :param back_steps: normally 1 -> get File/Line/Function from Function, which called get_debug_pos
    """

    frame = sys._getframe(0)  # current get_debug_pos function

    for bs in range(back_steps):
        frame = frame.f_back

    return os.path.realpath(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name




def get_event_metas(e: QEvent) -> str:
    # Event-Typ
    # et_dict = {getattr(QEvent, att_name): att_name for att_name in vars(QEvent) if type(getattr(QEvent, att_name)) == QEvent.Type}
    et_dict = {114: 'ActionAdded', 113: 'ActionChanged', 115: 'ActionRemoved', 99: 'ActivationChange',
               121: 'ApplicationActivated', 122: 'ApplicationDeactivated', 36: 'ApplicationFontChange',
               37: 'ApplicationLayoutDirectionChange', 38: 'ApplicationPaletteChange', 214: 'ApplicationStateChange',
               35: 'ApplicationWindowIconChange', 68: 'ChildAdded', 69: 'ChildPolished', 71: 'ChildRemoved',
               40: 'Clipboard', 19: 'Close', 200: 'CloseSoftwareInputPanel', 178: 'ContentsRectChange',
               82: 'ContextMenu', 183: 'CursorChange', 52: 'DeferredDelete', 60: 'DragEnter', 62: 'DragLeave',
               61: 'DragMove', 63: 'Drop', 170: 'DynamicPropertyChange', 98: 'EnabledChange', 10: 'Enter',
               124: 'EnterWhatsThisMode', 206: 'Expose', 116: 'FileOpen', 23: 'FocusAboutToChange', 8: 'FocusIn',
               9: 'FocusOut', 97: 'FontChange', 198: 'Gesture', 202: 'GestureOverride', 188: 'GrabKeyboard',
               186: 'GrabMouse', 159: 'GraphicsSceneContextMenu', 164: 'GraphicsSceneDragEnter',
               166: 'GraphicsSceneDragLeave', 165: 'GraphicsSceneDragMove', 167: 'GraphicsSceneDrop',
               163: 'GraphicsSceneHelp', 160: 'GraphicsSceneHoverEnter', 162: 'GraphicsSceneHoverLeave',
               161: 'GraphicsSceneHoverMove', 158: 'GraphicsSceneMouseDoubleClick', 155: 'GraphicsSceneMouseMove',
               156: 'GraphicsSceneMousePress', 157: 'GraphicsSceneMouseRelease', 182: 'GraphicsSceneMove',
               181: 'GraphicsSceneResize', 168: 'GraphicsSceneWheel', 18: 'Hide', 27: 'HideToParent', 127: 'HoverEnter',
               128: 'HoverLeave', 129: 'HoverMove', 96: 'IconDrag', 101: 'IconTextChange', 83: 'InputMethod',
               207: 'InputMethodQuery', 6: 'KeyPress', 7: 'KeyRelease', 169: 'KeyboardLayoutChange',
               89: 'LanguageChange', 90: 'LayoutDirectionChange', 76: 'LayoutRequest', 11: 'Leave',
               125: 'LeaveWhatsThisMode', 88: 'LocaleChange', 177: 'MacSizeChange', 65535: 'MaxUser', 43: 'MetaCall',
               102: 'ModifiedChange', 4: 'MouseButtonDblClick', 2: 'MouseButtonPress', 3: 'MouseButtonRelease',
               5: 'MouseMove', 109: 'MouseTrackingChange', 13: 'Move', 176: 'NonClientAreaMouseButtonDblClick',
               174: 'NonClientAreaMouseButtonPress', 175: 'NonClientAreaMouseButtonRelease',
               173: 'NonClientAreaMouseMove', 0: 'None_', 94: 'OkRequest', 208: 'OrientationChange', 12: 'Paint',
               39: 'PaletteChange', 131: 'ParentAboutToChange', 21: 'ParentChange', 212: 'PlatformPanel',
               217: 'PlatformSurface', 75: 'Polish', 74: 'PolishRequest', 123: 'QueryWhatsThis', 106: 'ReadOnlyChange',
               199: 'RequestSoftwareInputPanel', 14: 'Resize', 205: 'Scroll', 204: 'ScrollPrepare', 117: 'Shortcut',
               51: 'ShortcutOverride', 17: 'Show', 26: 'ShowToParent', 50: 'SockAct', 192: 'StateMachineSignal',
               193: 'StateMachineWrapped', 112: 'StatusTip', 100: 'StyleChange', 171: 'TabletEnterProximity',
               172: 'TabletLeaveProximity', 87: 'TabletMove', 92: 'TabletPress', 93: 'TabletRelease',
               219: 'TabletTrackingChange', 22: 'ThreadChange', 1: 'Timer', 120: 'ToolBarChange', 110: 'ToolTip',
               184: 'ToolTipChange', 194: 'TouchBegin', 209: 'TouchCancel', 196: 'TouchEnd', 195: 'TouchUpdate',
               189: 'UngrabKeyboard', 187: 'UngrabMouse', 78: 'UpdateLater', 77: 'UpdateRequest', 1000: 'User',
               111: 'WhatsThis', 118: 'WhatsThisClicked', 31: 'Wheel', 132: 'WinEventAct', 203: 'WinIdChange',
               24: 'WindowActivate', 103: 'WindowBlocked', 25: 'WindowDeactivate', 34: 'WindowIconChange',
               105: 'WindowStateChange', 33: 'WindowTitleChange', 104: 'WindowUnblocked', 126: 'ZOrderChange'}
    # Mouse-Button
    # mb_dict = {getattr(Qt, att_name): att_name for att_name in vars(Qt) if type(getattr(Qt, att_name)) == Qt.MouseButton}
    mb_dict = {134217727: 'AllButtons', 8: 'XButton1', 4096: 'ExtraButton10', 8192: 'ExtraButton11',
               16384: 'ExtraButton12', 32768: 'ExtraButton13', 65536: 'ExtraButton14', 131072: 'ExtraButton15',
               262144: 'ExtraButton16', 524288: 'ExtraButton17', 1048576: 'ExtraButton18', 2097152: 'ExtraButton19',
               16: 'XButton2', 4194304: 'ExtraButton20', 8388608: 'ExtraButton21', 16777216: 'ExtraButton22',
               33554432: 'ExtraButton23', 67108864: 'ExtraButton24', 32: 'TaskButton', 64: 'ExtraButton4',
               128: 'ExtraButton5', 256: 'ExtraButton6', 512: 'ExtraButton7', 1024: 'ExtraButton8',
               2048: 'ExtraButton9', 1: 'LeftButton', 4: 'MiddleButton', 0: 'NoButton', 2: 'RightButton'}
    # User-Event oder extern getriggert?
    # me_dict = {getattr(Qt, att_name): att_name for att_name in vars(Qt) if type(getattr(Qt, att_name)) == Qt.MouseEventSource}
    me_dict = {0: 'MouseEventNotSynthesized', 3: 'MouseEventSynthesizedByApplication', 2: 'MouseEventSynthesizedByQt',
               1: 'MouseEventSynthesizedBySystem'}

    # Returns the widget at global screen position point, or nullptr if there is no Qt widget there.
    widget = QApplication.instance().widgetAt(e.globalPos())

    return_string = f"{e.__class__.__name__} '{et_dict[e.type()]}' auf '{widget.objectName()}'"
    return_string += f"\n\twidget-Klasse: '{widget.__class__.__name__}'"
    return_string += f"\n\tButton: '{mb_dict[e.button()]}'"
    return_string += f"\n\tSource: '{me_dict[e.source()]}'"
    return_string += f"\n\twidget-x/y: {e.pos().x()}/{e.pos().y()}"
    return_string += f"\n\tscreen-x/y: {e.globalPos().x()}/{e.globalPos().y()}"
    return_string += "\n\tDynamicProperties:"

    # prop_name -> PyQt5.QtCore.QByteArray
    # but access to widget.property(...) is possible via string and original QByteArray
    for prop_name in widget.dynamicPropertyNames():
        return_string += f"\n\t\t{str(prop_name, 'utf-8')} -> {widget.property(prop_name)}"

    return return_string


def get_rlayer_metas(rlayer: QgsRasterLayer) -> str:
    """returns a string with metadata from layer

    Sample-call:

    .. code-block:: text
        from LinearReferencing.MyDebugFunctions import get_rlayer_metas
        print(get_rlayer_metas(iface.activeLayer()))
    """
    layer_name = rlayer.name()
    layer_id = rlayer.id()

    return_string = f"Layer '{layer_name}'"

    if isinstance(rlayer, QgsRasterLayer):
        # QgsRasterDataProvider
        # https://api.qgis.org/api/classQgsRasterDataProvider.html
        uri = rlayer.dataProvider().uri()

        return_string += f"\n\t- id: '{layer_id}'\
        \n\t- Projektion: '{rlayer.crs().authid()}' \
        \n\t- QgsRasterDataProvider:\
        \n\t\t- name: '{rlayer.dataProvider().name()}' \
        \n\t\t- description: '{rlayer.dataProvider().description()}'\
        \n\t\t- dpi: '{rlayer.dataProvider().dpi()}'\
        \n\t\t- extent: '{rlayer.dataProvider().extent()}'\
        \n\t\t- uri: '{rlayer.dataProvider().uri()}'\
        \n\t\t- uri.uri: '{rlayer.dataProvider().uri().uri()}'\
        \n\t\t- providerCapabilities: '{rlayer.dataProvider().capabilitiesString()}'\
        "

    else:
        return_string += "\n...is no QgsRasterLayer!"

    return return_string


def get_vlayer_metas(vlayer: QgsVectorLayer) -> str:
    """returns a string with metadata from layer and fields
    .. Note::
        in the fields of virtual-layers the result of field.typeName() and field.displayType() is '' (bug?),
        but QMetaType.typeName(field.type()) and field.friendlyTypeString() show matching Metadata

    Sample-call:

    .. code-block:: text
        from LinearReferencing.MyDebugFunctions import get_vlayer_metas
        print(get_vlayer_metas(iface.activeLayer()))
    """
    layer_name = vlayer.name()
    layer_id = vlayer.id()

    return_string = f"Layer '{layer_name}'"
    if isinstance(vlayer, QgsVectorLayer):

        # dataProvider.fields(): <class 'qgis._core.QgsFields'>
        # -> only stored fields
        provider_field_names = [field.name() for field in vlayer.dataProvider().fields()]

        # vlayer.fields: <class 'qgis._core.QgsFields'>
        # all fields incl. joined, virtual and not yet saved fields
        # layer_field_names = [field.name() for field in vlayer.fields()]

        # https://api.qgis.org/api/classQgsVectorDataProvider.html

        return_string += f"\n\t- id: '{layer_id}'\
        \n\t- display_expression: '{vlayer.displayExpression()}'\
        \n\t- selectedFeatureCount: '{vlayer.selectedFeatureCount()}' \
        \n\t- Projektion: '{vlayer.crs().authid()}' \
        \n\t- geometryType: '{vlayer.geometryType()}' \
        \n\t- QgsVectorDataProvider:\
        \n\t\t- name: '{vlayer.dataProvider().name()}' \
        \n\t\t- description: '{vlayer.dataProvider().description()}'\
        \n\t\t- wkb_type: '{vlayer.dataProvider().wkbType()}'\
        \n\t\t- geometry_type: '{QgsWkbTypes.displayString(vlayer.dataProvider().wkbType())}'\
        \n\t\t- Projektion: '{vlayer.dataProvider().sourceCrs().authid()}' \
        \n\t\t- storage_type: '{vlayer.dataProvider().storageType()}'\
        \n\t\t- uri: '{vlayer.dataProvider().uri()}'\
        \n\t\t- uri.uri: '{vlayer.dataProvider().uri().uri()}'\
        \n\t\t- featureCount: '{vlayer.dataProvider().featureCount()}'\
        \n\t\t- capabilitiesString: '{vlayer.dataProvider().capabilitiesString()}'\
        \n\t- dependencies:\
        "

        for dp in vlayer.dataProvider().dependencies():
            return_string += f"\n\t\t-Layer-ID: '{dp.layerId()}'"

        return_string += "\n\t- fields:"

        fnx = 0

        # incl. joined-fields
        for field in vlayer.fields():
            # where is the field from?
            source = 'provider'
            expression = vlayer.expressionField(fnx)
            if expression:
                source = f"virtual \n\t\t\t\texpression: '{expression}'"
            elif field.name() not in provider_field_names:
                source = 'joined'

            return_string += f"\n\t\t-Field {fnx}: '{field.name()}'\
        \n\t\t\t-type: '{field.type()}'\
        \n\t\t\t-QMetaType typeName: '{QMetaType.typeName(field.type())}'\
        \n\t\t\t-Field typeName: '{field.typeName()}'\
        \n\t\t\t-displayType: '{field.displayType()}'\
        \n\t\t\t-friendlyTypeString: '{field.friendlyTypeString()}'\
        \n\t\t\t-source: {source}\
        "
            fnx += 1

        pk_field_idzs = vlayer.dataProvider().pkAttributeIndexes()

        return_string += "\n\t- PK-Fields:"

        for pk_field_idx in pk_field_idzs:
            pk_field = vlayer.dataProvider().fields().at(pk_field_idx)
            return_string += f"\n\t\t-Field {pk_field_idx}: '{pk_field.name()}'"

        return_string += "\n\t- actions:"
        # qgis._core.QgsActionManager
        a_mgr = vlayer.actions()
        a_lst = a_mgr.actions()

        # see https://api.qgis.org/api/classQgis.html#a59269e5835c03c5d801a6e2647cea598
        action_type_dict = {
            0: 'Generic',
            1: 'GenericPython',
            2: 'Mac',
            3: 'Windows',
            4: 'Unix',
            5: 'OpenUrl',
            6: 'SubmitUrlEncoded',
            7: 'SubmitUrlMultipart',
        }

        for action in a_lst:
            # qgis._core.QgsAction
            # action.id() -> PyQt5.QtCore.QUuid https://doc.qt.io/qt-5/quuid.html
            # action.type() -> qgis._core.QgsAction.ActionType
            # action.icon() ->  PyQt5.QtGui.QIcon
            # action.name() -> in QGis as "Description" (mandatory)
            # action.shortTitle() -> in QGis as "Short Name" (optional, if not set -> only icon)
            # action.command() -> in QGis "Action Text", dependend from action.type(), e.g. Python-Code
            return_string += f"\n\t\t-action\
            \n\t\t\t-id: '{action.id().toString()}'\
            \n\t\t\t-name: '{action.name()}'\
            \n\t\t\t-shortTitle: '{action.shortTitle()}' \
            \n\t\t\t-type: {action.type()} -> '{action_type_dict[action.type()]}'\
            \n\t\t\t-actionScopes: '{action.actionScopes()}'\
            \n\t\t\t-iconPath: '{action.iconPath()}'\
            \n\t\t\t-command:\n{action.command()}\
            "


    else:
        return_string += "\n...is no QgsVectorLayer!"

    return return_string


def stringify_object_functions(my_obj: object, prefix: str = '') -> str:
    """stringify object-functions (__dunders__ excluded) for debug

    Usage:

    ``debug_print("system_vs", tools.MyDebugFunctions.stringify_object_functions(self.system_vs))``
    :param my_obj: object for inspection, can be class too
    :param prefix: List-prefix for print-output, something like "\t- "

    """
    result_str = ''
    try:
        function_list = [prop for prop in dir(my_obj) if not prop.startswith('__') and callable(getattr(my_obj, prop))]
        if function_list:
            longest_func = max(function_list, key=len)
            max_len = len(longest_func)

            for func in function_list:
                result_str += f"{prefix}{func:<{max_len}} \t {getattr(my_obj, func)}\n"
                doc_string = getattr(my_obj, func).__doc__
                if doc_string:
                    doc_lines = doc_string.splitlines()
                    for line in doc_lines:
                        result_str += f"{' ':<{max_len}} \t {line}\n"

    except Exception as e:
        result_str += f"\nstringify_object_functions failed: {e.__str__()}..."

    return result_str


def log_string_to_file(log_string: str, log_file_name: str = "inspect.txt", temp_sub_dir: str = "mylogs", write_mode: str = 'append') -> str:
    """write string to temp-File
    :param log_string: content for logfile
    :param log_file_name: Filename
    :param temp_sub_dir: Subdirectory in current temp-directory
    :param write_mode:
    - prepend -> output prepended
    - append -> output appended
    - replace -> old content replaced by output
    - single_file -> output respectively to new Log-File with randomized log_file_name (current timestamp included), existing log-files older 10 min are deleted
    :return: path to logfile
    """
    tempdir = tempfile.gettempdir()
    log_dir = os.path.join(tempdir, temp_sub_dir)

    if not os.path.isdir(log_dir):
        try:
            os.mkdir(log_dir)
        except:
            pass

    if os.path.isdir(log_dir):
        if write_mode == 'single_file':
            # pre-delete old log-files
            filtered_file_list = [fn for fn in os.listdir(log_dir) if pathlib.Path(fn).suffix == '.txt' and (datetime.datetime.now() - datetime.datetime.fromheader_line(os.stat(os.path.join(log_dir, fn)).st_ctime)).total_seconds() > 10 * 60]

            for fn in filtered_file_list:
                path = os.path.join(log_dir, fn)
                try:
                    os.remove(path)
                except:
                    pass

            d_now = datetime.datetime.now()
            str_now = d_now.strftime('%Y-%d-%m_%H:%M:%S')
            fd, name = tempfile.mkstemp(suffix=log_file_name, prefix=str_now, dir=log_dir, text=True)
            log_file_path = os.path.join(log_dir, name)
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write(log_string)
            except Exception as e:
                print(f"could not open or create Logfile {log_file_path}: {e.__str__()}...")

        else:
            log_file_path = os.path.join(log_dir, log_file_name)
            try:
                with open(log_file_path, "a+", encoding='utf-8') as f:
                    f.seek(0)
                    if write_mode == 'append':
                        f.write(log_string)
                    elif write_mode == 'prepend':
                        str_old = f.read()
                        f.truncate(0)
                        f.write(log_string)
                        f.write(str_old)
                    elif write_mode == 'replace':
                        f.truncate(0)
                        f.write(log_string)
            except Exception as e:
                print(f"could not open or create Logfile {log_file_path}: {e.__str__()}...")

        return log_file_path
    else:
        print(f"Verzeichnis {log_dir} konnte nicht angelegt werden")


def stringify_object_props(my_obj: object, prefix: str = '') -> str:
    """stringify an object with all its properties (__dunders__ excluded) for debug

    Usage:

    ``debug_print("system_vs", tools.MyDebugFunctions.stringify_object_props(self.system_vs))``
    :param my_obj: object for inspection, can be class too
    :param prefix: List-prefix for print-output, something like "\t- "
    """
    result_str = ''
    try:
        property_list = [prop for prop in dir(my_obj) if not prop.startswith('__') and not callable(getattr(my_obj, prop))]
        if property_list:
            longest_prop = max(property_list, key=len)
            max_len = len(longest_prop)

            for prop in property_list:
                result_str += f"{prefix}{prop:<{max_len}} \t {getattr(my_obj, prop)}\n"

    except Exception as e:
        result_str += f"\nstringify_object_props failed: {e.__str__()}..."

    return result_str


def print_to_string(*args, **kwargs) -> str:
    """Objekte als strings zurückliefern, print(...) in String
    https://stackoverflow.com/questions/39823303/python3-print-to-string
    """
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents


# log function-usages, see debug_log
# 0 => no log
# 1 => log to console
# 2 => log to console and file (helpfully for QGis-crash-debugging)
debug_log_mode = 2
# for debug_log_mode 2: Name for the Log-File, located in the plugin-directory, created if not existing
log_file_name = 'LinearReferencing.log'
debug_log_ctr = 0


def debug_log(*args,**kwargs):
    """quicky for debugging to console or file
    outputs counter, function, file and line where the debug_log-function was called
    uses global debug_log_mode, with this the debug-logs can be stopped for production-usage without the need to delete or comment the function calls
    :param args: any number of debug-objects, appended stringified
    :param kwargs: any number of keyword-objects, key prepended to __str__()-stringified output
    """
    global debug_log_ctr, debug_log_mode, log_file_name

    if debug_log_mode > 0:
        debug_log_ctr += 1

        path = pathlib.Path(__file__)
        plugin_folder = str(path.parent.parent.absolute())
        frame = sys._getframe(0)
        fc = 0
        while frame:
            if fc == 1:
                # 0 => this function itself
                # 1 => the function which called this function
                file = os.path.realpath(frame.f_code.co_filename)
                stripped_file = file.replace(plugin_folder, ".")
                log_string = f"{debug_log_ctr}:\t{frame.f_code.co_name}\t{stripped_file}\t#{frame.f_lineno}"

                if args:
                    # multiple => each one in new line
                    for log_obj in args:
                        log_string += f"\n\t'{str(log_obj)}'"

                if kwargs:
                    for key in kwargs:
                        log_string += f"\n\t'{str(key)}'\t'{str(kwargs[key])}'"

                print(log_string)
                if debug_log_mode == 2:
                    # additionally write to log-file:
                    log_file_path = os.path.join(plugin_folder, log_file_name)
                    with open(log_file_path, "a+", encoding='utf-8') as f:
                        # prepend with date-time and append to log-file
                        d_now = datetime.datetime.now()
                        str_now = d_now.strftime('%Y-%m-%d %H:%M:%S')
                        f.write('\n' + str_now + '\n' + log_string)

                return

            frame = frame.f_back
            fc += 1


dbg_ctr = 0

def debug_print(*args, debug_title: str = None, show_backtrace: bool = True, output_to: str = 'console', **kwargs) -> str:
    """Write Debug-Messages to console or qDebug (for debugging QGis-Crashes).
    :param args: any number of debug-objects, index prepended to __str__()-stringified output
    :param debug_title: optional title
    :param show_backtrace: includes backtrace
    :param output_to:
    - qDebug -> output to terminal qgis is started from (default)
    - console -> output to console
    - all other -> no output, only return result-string, e.g. for log_string_to_file
    :param kwargs: any number of debug-objects, keyword prepended to __str__()-stringified output
    """
    global dbg_ctr
    dbg_ctr += 1

    path = pathlib.Path(__file__)
    # <class 'pathlib.PosixPath'>
    plugin_folder = str(path.parent.parent.absolute())


    backtrace = []
    # get maximum string-length for f-string-adjusted formatting
    max_length_fn = 0
    max_length_fi = 0

    frame = sys._getframe(0)
    while frame:
        file = os.path.realpath(frame.f_code.co_filename)
        function = frame.f_code.co_name
        lineno = frame.f_lineno

        stripped_file = file.replace(plugin_folder, ".")
        max_length_fi = max(max_length_fi, len(stripped_file))
        max_length_fn = max(max_length_fn, len(function))

        currentrace = {"file": file, "function": function, "lineno": lineno}
        backtrace.append(currentrace)
        frame = frame.f_back



    # backtrace[0] ->  debug_print-function itself
    # backtrace[1] -> function which called debug_print
    last_trace = backtrace[1]
    stripped_file = last_trace['file'].replace(plugin_folder, ".")

    if not debug_title:
        debug_title = last_trace['function']

    max_length_fn = max(max_length_fn,len(debug_title))
    max_length_fn += 8


    log_string = "--------------------------------------------------------------------------------------------------------------"
    log_string += f"\n{dbg_ctr}:\t{datetime.datetime.now().strftime('%H:%M:%S')}\t{debug_title:<{max_length_fn}}\t{stripped_file:<{max_length_fi}}\t#{last_trace['lineno']}"

    if args:
        i = 0
        for arg in args:
            i += 1
            log_string += '\n\t' + str(i) + '\t' + str(arg)


    if kwargs:
        for key in kwargs:
            log_string += '\n\t' + str(key) + '\t' + str(kwargs[key])


    if show_backtrace:
        backtrace_part = f"Backtrace:"
        backtrace = list(reversed(backtrace))
        # the debug_print-call itself
        backtrace.pop()
        backtrace_idx = 0

        for trace_step in backtrace:
            backtrace_idx += 1
            file, function, lineno = map(trace_step.get, ('file', 'function', 'lineno'))
            function += '(...)'
            stripped_file = file.replace(plugin_folder, ".")
            backtrace_part += f"\n\t\t{backtrace_idx}\t{function:<{max_length_fn}}\t{stripped_file:<{max_length_fi}}\t#{lineno}"

        log_string += f"\n\n\t{backtrace_part}"


    if output_to == 'qDebug':
        # qDebug appears in the console window qgis is started from
        # Note to encode: qDebug-strings are expected to be ascii
        # without encode:
        # UnicodeEncodeError: 'ascii' codec can't encode character '\xe0' in position 4: ordinal not in range(128)
        qDebug(log_string.encode('utf-8'))
    elif output_to == 'console':
        # print appears in Python-Console
        print(log_string)

    return log_string
