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

import pathlib, os, sys, datetime

from PyQt5.QtCore import qDebug

# global counter-variable used in debug_log
debug_log_ctr = 0

# global counter-variable
dbg_ctr = 0

def get_debug_pos(back_steps: int = 1) -> str:
    """returns debug-footprint (Filename + Line-Number) for Messages

    Args:
        back_steps (int, optional): get File/Line from Function, which called get_debug_pos. Defaults to 1.

    Returns:
        str
    """
    # Rev. 2025-10-04
    frame = sys._getframe(0)  # current get_debug_pos function

    for bs in range(back_steps):
        frame = frame.f_back

    return f"{os.path.basename(os.path.realpath(frame.f_code.co_filename))} #{frame.f_lineno}"


def get_debug_file_line(back_steps: int = 1) -> tuple:
    """returns debug-footprint (Path + Line-Number)

    Args:
        back_steps (int, optional): get File/Line from Function, which called get_debug_pos. Defaults to 1.

    Returns:
        tuple: (path,line-nr,function-name)
    """
    # Rev. 2026-01-13
    frame = sys._getframe(0)  # current get_debug_pos function

    for bs in range(back_steps):
        frame = frame.f_back

    return (
        os.path.realpath(frame.f_code.co_filename),
        frame.f_lineno,
        frame.f_code.co_name,
    )





def debug_log(*args, **kwargs):
    """quicky for debugging to console

    Args:
        args: any number of debug-objects, appended stringified
        kwargs: any number of keyword-objects, key prepended to __str__()-stringified output
    """
    # Rev. 2025-10-04
    global debug_log_ctr

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

            return

        frame = frame.f_back
        fc += 1





def debug_print(
    *args,
    debug_title: str = None,
    show_backtrace: bool = True,
    output_to: str = "console",
    **kwargs,
) -> str:
    """Write Debug-Messages to console or qDebug (for debugging QGis-Crashes).

    Args:
        args: any number of debug-objects, appended stringified
        debug_title (str, optional): optional title. Defaults to None.
        show_backtrace (bool, optional): include backtrace. Defaults to True.
        output_to (str, optional):
            - qDebug -> output to terminal qgis is started from (default)
            - console -> output to console.
            Defaults to "console".
        kwargs: any number of keyword-objects, key prepended to __str__()-stringified output

    Returns:
        str
    """
    # Rev. 2026-01-13
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
    stripped_file = last_trace["file"].replace(plugin_folder, ".")

    if not debug_title:
        debug_title = last_trace["function"]

    max_length_fn = max(max_length_fn, len(debug_title))
    max_length_fn += 8

    log_string = "--------------------------------------------------------------------------------------------------------------"
    log_string += f"\n{dbg_ctr}:\t{datetime.datetime.now().strftime('%H:%M:%S')}\t{debug_title:<{max_length_fn}}\t{stripped_file:<{max_length_fi}}\t#{last_trace['lineno']}"

    if args:
        i = 0
        for arg in args:
            i += 1
            log_string += "\n\t" + str(i) + "\t" + str(arg)

    if kwargs:
        for key in kwargs:
            log_string += "\n\t" + str(key) + "\t" + str(kwargs[key])

    if show_backtrace:
        backtrace_part = f"Backtrace:"
        backtrace = list(reversed(backtrace))
        # the debug_print-call itself
        backtrace.pop()
        backtrace_idx = 0

        for trace_step in backtrace:
            backtrace_idx += 1
            file, function, lineno = map(trace_step.get, ("file", "function", "lineno"))
            function += "(...)"
            stripped_file = file.replace(plugin_folder, ".")
            backtrace_part += f"\n\t\t{backtrace_idx}\t{function:<{max_length_fn}}\t{stripped_file:<{max_length_fi}}\t#{lineno}"

        log_string += f"\n\n\t{backtrace_part}"

    if output_to == "qDebug":
        # qDebug appears in the console window qgis is started from
        # Note to encode: qDebug-strings are expected to be ascii
        # without encode:
        # UnicodeEncodeError: 'ascii' codec can't encode character '\xe0' in position 4: ordinal not in range(128)
        qDebug(log_string.encode("utf-8"))
    elif output_to == "console":
        # print appears in Python-Console
        print(log_string)

    return log_string
