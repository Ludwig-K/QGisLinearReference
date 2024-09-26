#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* customized Delegates for QTableView and QTableWidget

********************************************************************

* Date                 : 2024-01-23
* Copyright            : (C) 2023 by Ludwig Kniprath
* Email                : ludwig at kni minus online dot de

********************************************************************

this program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

********************************************************************
"""

# Rev. 2024-01-23

from PyQt5 import QtCore, QtGui, QtWidgets
from LinearReferencing.tools.MyDebugFunctions import debug_log, debug_print

import numbers

class QLocaleDelegate(QtWidgets.QStyledItemDelegate):
    """base for all delegates"""
    def __init__(self,parent = None):
        super().__init__(parent)
        # own delegate for number/date/time-formatting
        self.q_locale = QtCore.QLocale.system()

    def set_q_locale(self,q_locale):
        """setter for q_locale"""
        self.q_locale = q_locale


class DateDelegate(QLocaleDelegate):
    """delegate for date-contents, f. e. QtCore.QDateTime.currentDateTime()"""
    def __init__(self,parent = None):
        super().__init__(parent)

    def displayText(self, value, locale):
        """ return formatted date-string, does not use locale, because some locale settings seem to be ignored"""
        try:
            return self.q_locale.toString(value, 'yyyy-MM-dd')
        except:
            pass


class TimeDelegate(QLocaleDelegate):
    """delegate for time-contents, f. e. QtCore.QDateTime.currentTime()"""
    def __init__(self,parent = None):
        super().__init__(parent)


    # Note: if stored as milliseconds instead of time, f.e. QtCore.QDateTime.currentDateTime().toMSecsSinceEpoch(),
    # implement suitable delegate with datetime.datetime.fromtimestamp(value / 1000).strftime('%H:%M:%S')
    def displayText(self, value, locale):
        """ return formatted time-string, does not use locale, because some locale settings seem to be ignored"""
        try:
            return self.q_locale.toString(value, 'hh:mm:ss')
        except:
            pass



class SelectBorderDelegate(QLocaleDelegate):
    def __init__(self, border_bottom_color:QtGui.QColor = QtGui.QColor('#BBBBBB'), border_bottom_width:int = 1, border_right_color:QtGui.QColor = QtGui.QColor('#BBBBBB'), border_right_width: int = 1, parent=None):
        """
        :param border_bottom_color: color of border, only selected
        :param border_bottom_width: width of border, only selected
        :param border_right_color: color of border, allways drawn
        :param border_right_width: width of border, allways drawn
        :param parent: Qt-Hierarchy
        """
        super().__init__(parent)
        self.border_bottom_color = border_bottom_color
        self.border_bottom_width = border_bottom_width
        self.border_right_color = border_right_color
        self.border_right_width = border_right_width


    def initStyleOption(self, option, index):
        """Reimplemented, sets the alignment"""
        super().initStyleOption(option, index)
        # is this option selected?
        selected = option.state & QtWidgets.QStyle.State_Selected
        # if it is, bold
        option.font.setBold(selected)
        # fake "unselect" to use normal colors
        #if selected:
            #option.state = option.state & ~ QtWidgets.QStyle.State_Selected

    def paint(self, painter, option, index):
        painter.save()
        super().paint(painter, option, index)

        # right cell border to visualize columns
        pen = painter.pen()
        pen.setColor(self.border_right_color)
        pen.setWidth(self.border_right_width)
        painter.setPen(pen)
        painter.drawLine(option.rect.bottomRight(),option.rect.topRight())
        painter.restore()

        selected = bool(option.state & QtWidgets.QStyle.State_Selected)

        if selected:
            # draw bottom line
            pen = painter.pen()
            pen.setColor(self.border_bottom_color)
            pen.setWidth(self.border_bottom_width)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

class DoubleSelectBorderDelegate(SelectBorderDelegate):
    """
    draws a single cell with border dependend on select-state
    only for numerical values, which are formatted according to QLocale and user-defined precision
    see https://stackoverflow.com/questions/66847632/how-to-style-the-entire-line-instead-of-all-cells/66851157#66851157
    """

    def __init__(self, border_bottom_color:QtGui.QColor = QtGui.QColor('#BBBBBB'), border_bottom_width:int = 1, border_right_color:QtGui.QColor = QtGui.QColor('#BBBBBB'), border_right_width: int = 1, precision:int = 2, parent=None):
        """
        :param border_bottom_color: color of border, only selected
        :param border_bottom_width: width of border, only selected
        :param border_right_color: color of border, allways drawn
        :param border_right_width: width of border, allways drawn
        :param precision: num decimals
        :param parent: Qt-Hierarchy
        """
        super().__init__(border_bottom_color,border_bottom_width,border_right_color,border_right_width,parent)
        self.precision = precision

    def displayText(self, value, locale) -> str:
        """returns numerical values q_locale.formatted and self.precision-rounded
        or nothing, if the value is not numeric, f.e. Null"""
        try:
            return self.q_locale.toString(float(value), 'f', self.precision)
        except:
            pass



class PaddingLeftDelegate(SelectBorderDelegate):
    """column-wise left aligned and left padded, used for Cell-Widgets with Icons (QTwCellWidget with QTwToolButton)
    the necessary padding is (number * width) + (number - 1 *  spacing) + ContentsMargins-left + ContentsMargins-Right
    currently
    width = 20px
    spacing = 3px
    ContentsMargins-left = 3px
    ContentsMargins-right = 3px

    1 icon => 1 * 20 + (1-1) * 3 + 3 + 3 = 26
    2 icons => 2 * 20 + (2-1) * 3 + 3 + 3 = 49
    3 icons => 3 * 20 + (3-1) * 3 + 3 + 3 = 72
    4 icons => 4 * 20 + (4-1) * 3 + 3 + 3 = 95
    5 icons => 5 * 20 + (5-1) * 3 + 3 + 3 = 118
    6 icons => 6 * 20 + (6-1) * 3 + 3 + 3 = 141
    7 icons => 7 * 20 + (7-1) * 3 + 3 + 3 = 164

    alternative:
    prepend multiple blanks
    blank = '\u2007' (figure space => in fonts with monospaced digits, equal to the width of one digit)
    blank = '\u00A0'  (no-break space)
    reference_item.setText(f"{blank * 8}# {ref_id}")
    """

    def __init__(self, padding_left_0:int, padding_left_1:int = 0, border_bottom_color:QtGui.QColor = QtGui.QColor('#BBBBBB'), border_bottom_width:int = 1, border_right_color:QtGui.QColor = QtGui.QColor('#BBBBBB'), border_right_width: int = 1, parent=None):
        """initialize
        :param padding_left_0: padding-left for first level (with collapse/expand-buttons) in pixel, only used inside tree-views
        :param padding_left_1: padding-left for second lefel (collapsable/expandable area) in pixel
        :param border_bottom_color: color of border
        :param border_bottom_width: width of border
        :param border_right_color: color of border, allways drawn
        :param border_right_width: width of border, allways drawn
        :param parent: Qt-Hierarchy
        """
        super().__init__(border_bottom_color,border_bottom_width,border_right_color,border_right_width,parent)
        self.padding_left_0 = padding_left_0
        self.padding_left_1 = padding_left_1


    def initStyleOption(self, option, index):
        """Reimplemented, sets the alignment,
        must be left-aligned to enable left-padding"""
        super().initStyleOption(option, index)
        #see https://doc.qt.io/qt-5/qt.html#AlignmentFlag-enum
        option.displayAlignment = QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft

    def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:
        """Reimplemented:
        Returns the size needed by the delegate to display the item specified by index, taking into account the style information provided by option.
        returns super().sizeHint + padding_left_0
        rsp. super().sizeHint + padding_left_1 for indizes with parent"""
        super_size_hint = super().sizeHint(option, index)
        if index.parent().isValid():
            # index with parent => level 1
            super_size_hint.setWidth(super_size_hint.width() + self.padding_left_1)
        else:
            # index without parent => level 0
            super_size_hint.setWidth(super_size_hint.width() + self.padding_left_0)

        return super_size_hint

    def paint(self, painter, option, index):
        """Remplemented: moves the drawing-rect and the position of text padding_left_0 rsp. padding_left_1  to right"""
        painter.save()

        rect_org = QtCore.QRect(option.rect)
        if index.parent().isValid():
            option.rect.adjust(self.padding_left_1,0,0,0)
        else:
            option.rect.adjust(self.padding_left_0, 0, 0, 0)

        super().paint(painter, option, index)

        # only for selected options:
        # additionally draw the left-padding-gap with rect in highlight-color and bottom line
        selected = bool(option.state & QtWidgets.QStyle.State_Selected)
        if selected:
            # draw fill-gap
            rect_org.setLeft(0)
            rect_org.setRight(option.rect.left())
            painter.fillRect(rect_org,option.palette.brush(QtGui.QPalette.Highlight))

            # draw bottom line
            pen = painter.pen()
            pen.setColor(self.border_bottom_color)
            pen.setWidth(self.border_bottom_width)
            painter.setPen(pen)
            bl = QtCore.QPoint(0,option.rect.bottom())
            br = QtCore.QPoint(option.rect.left(),option.rect.bottom())
            painter.drawLine(bl,br)

        painter.restore()

