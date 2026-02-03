#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
********************************************************************

* Part of the QGis-Plugin LinearReferencing:
* customized QtWidgets

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

import locale
import time
import sys
import numbers
import qgis
import collections.abc
from typing import Any, Generator

from PyQt5.QtCore import (
    Qt,
    QObject,
    QEvent,
    QSize,
    QSignalBlocker,
    QPoint,
    QModelIndex,
    QTimer,
    pyqtSignal,
    QItemSelectionModel,
    QMetaType,
    QVariant
)

from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel,
    QMouseEvent,
    QIcon,
    QPalette,
    QColor,
    QPainter,
    QFont
)

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QTableView,
    QAbstractItemView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QComboBox,
    QFrame,
    QSizeGrip,
    QHeaderView,
    QLineEdit,
    QToolButton,
    QStyleOptionComboBox,
    QStyle,
    QCheckBox,
    QPushButton,
    QTreeView,
    QHBoxLayout,
    QGroupBox,
    QProxyStyle,
    QColorDialog,
    QDoubleSpinBox,
    QStyleOptionSpinBox,
    QStylePainter,
    QStyleOption,
    QSizePolicy
)

from qgis.core import QgsVectorLayer

from LinearReferencing.settings.constants import Qt_Roles

from LinearReferencing import tools

from LinearReferencing.i18n.SQLiteDict import SQLiteDict

# global variable
MY_DICT = SQLiteDict()

from LinearReferencing.tools.MyDebugFunctions import debug_log, debug_print

locale.setlocale(locale.LC_ALL, "")
# sets the locale for all categories to the user’s default setting


class featureFormEventFilter(QObject):
    """event-filter registering window-moves and -resizes
    applied to QGis-feature-forms opened by tool_show_feature_form
    emits signal on window-resize and -move"""
    # https://stackoverflow.com/questions/69007346/how-to-use-eventfilter-and-installeventfilter-methods
    # Rev. 2025-01-12
    # emitted signal with single parameter: the moved/resized feature-form
    # rest is done by connected slot parsing size- and position of the moved object
    feature_form_repositioned = pyqtSignal(QObject)



    def __init__(self, feature_form):
        super().__init__(feature_form)
        self.feature_form = feature_form
        self.feature_form.installEventFilter(self)


    def eventFilter(self, event_obj: QObject, event: QEvent) -> bool:
        if event_obj is self.feature_form and event.type() in [QEvent.Resize, QEvent.Move]:
            self.feature_form_repositioned.emit(event_obj)
        return super().eventFilter(event_obj, event)

class QcbxToggleGridRows(QCheckBox):
    """Pseudo-QGroupBox with toggle-functionality for some specified rows inside a QGridLayout
    only uses GroupBox-Title and Checkbox, not the Box itself"""
    # Rev. 2025-11-29
    def __init__(self, title:str, tool_tip: str, grid_elem: QWidget, start_row:int, end_row:int, initially_open:bool = True, parent:QWidget=None):
        """
        constructor

        Args:
            title (str): Title-Text
            tool_tip (str): ToolTip
            grid_elem (QWidget): Element with Grid-Layout
            start_row (int): Toggle-Area starts at row
            end_row (int): Toggle-Area ends at row
            initially_open (bool): Toggle-Area is initially visible (will not work with __init__, because mostly QcbxToggleGridRows is initialized before the following toggle-rows in grid_elem)
        """
        # Rev. 2026-01-13
        super().__init__(title, parent)
        self.setToolTip(tool_tip)
        self.grid_elem = grid_elem
        self.start_row = start_row
        self.end_row = end_row
        self.grid_rows_visible = initially_open

        self.setCheckable(True)
        self.setStyle(self.CheckBoxProxyStyle())
        self.toggled.connect(self.s_toggle)


        # setChecked will trigger s_toggle, but these rows must initially be set hidden
        if initially_open:
            self.setChecked(True)
        else:
            self.setChecked(False)

    class CheckBoxProxyStyle(QProxyStyle):
        """QProxyStyle to change QCheckBox"""
        # Rev. 2026-01-13

        def drawPrimitive(self, element:QStyle.PrimitiveElement, option:QStyleOption, painter:QPainter, widget: QWidget):
            """derived from super() (QProxyStyle)

            Args:
                element (QStyle.PrimitiveElement): Qt-internal Element inside the widget, here: PE_IndicatorCheckBox inside a QGroupBox
                option (QStyleOption): Style the PrimitiveElement
                painter (QPainter): Draw the PrimitiveElement
                widget (QWidget): Parent-Widget for the PrimitiveElement, here: QGroupBox
            """
            # Rev. 2026-01-13
            if element == QStyle.PE_IndicatorCheckBox and isinstance(widget, QCheckBox):
                # PE_IndicatorCheckBox inside a QCheckBox
                # paint a PE_IndicatorArrowDown rsp. PE_IndicatorArrowRight into widget dependend on isChecked()
                if widget.isChecked():
                    super().drawPrimitive(
                        QStyle.PE_IndicatorArrowDown, option, painter, widget
                    )
                else:
                    super().drawPrimitive(
                        QStyle.PE_IndicatorArrowRight, option, painter, widget
                    )
            else:
                # paint all PrimitiveElement != PE_IndicatorCheckBox in widgets != QGroupBox
                super().drawPrimitive(element, option, painter, widget)

    def s_toggle(self, status: bool):
        """Toggle Check-Box in Dialog:
        set rows from start_row...end_row visible based on isChecked

        Args:
            status (bool): isChecked()-State
        """
        # Rev. 2026-01-13
        for sub_row in range(self.start_row, self.end_row):
            for sub_col in range(self.grid_elem.layout().columnCount()):
                qli = self.grid_elem.layout().itemAtPosition(sub_row, sub_col)
                if qli:
                    qli.widget().setVisible(status)


class MyToolbarSpacer(QWidget):
    """Spacer for QToolBar, added before first and after last to center Toolbar-Icons"""
    # Rev. 2025-11-22
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

class MyStandardItem(QStandardItem):
    """derived QStandardItem used within QStandardItemModel:
    normal sort uses the text() (QtDisplayRole), which is not always usefull, especially for numerical values
    These QStandardItem uses Qt_Roles.CUSTOM_SORT"""
    # Rev. 2025-01-25
    def __init__(self, *args, **kwargs):
        """constructor
        :param args: parameter for super()-constructor
        :param kwargs: parameter for super()-constructor
        """
        # Rev. 2025-01-04
        super().__init__(*args, **kwargs)

    def __lt__(self, other):
        """derived operator for custom sort
        :param self: current QTableWidgetItem
        :param other: the compared QTableWidgetItem
        """
        # Rev. 2025-01-04
        try:
            lt = self.data(Qt_Roles.CUSTOM_SORT) < other.data(Qt_Roles.CUSTOM_SORT)
        except Exception as e:
            # "Leerstellen" im Modell: einer oder beide der sort_role-Werte nicht gesetzt
            # Fehlermeldung: '<' not supported between instances of 'NoneType' and 'NoneType'
            # True => Nullwerte werden aufsteigend am Anfang sortiert
            # False => Nullwerte werden aufsteigend am Ende sortiert
            # => hier notwendig, um erst die data_records und danach die recursive_childs darzustellen, was etwas verwirrend aussieht
            lt = False

        return lt


class MyToolButton(QToolButton):
    """animated-QToolButton inside MyCellWidget of QTreeView"""

    # Rev. 2025-11-08
    def __init__(
        self,
        icon: QIcon,
        tool_tip: str = '',
        base_size: QSize = QSize(20, 20),
        icon_size: QSize = QSize(15, 15),
        cursor: Qt.CursorShape = Qt.PointingHandCursor
    ):
        """constructor
        Args:
            icon (QIcon): optional icon for this button
            tool_tip (str, optional): ToolTip-Text. Defaults to ''.
            base_size (QSize): button-width/height in pixel, optional, default QSize(20, 20), affects padding-left
            icon_size (QSize): icon-width/height in pixel, optional, default QSize(18, 18)
            cursor (Qt.CursorShape, optional): Defaults to Qt.PointingHandCursor.
                Varianten: Qt.ForbiddenCursor, cursor=Qt.ArrowCursor (der "normale" Cursor)
        """
        # Rev. 2025-11-08
        super().__init__()

        self.setBaseSize(base_size)
        self.setIconSize(icon_size)

        self.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self.setCursor(cursor)

        self.setIcon(icon)

        self.setToolTip(tool_tip)


        # setStyleSheet Geschmackssache...
        # ohne: Button im Kästchen
        # Variante ganz ohne Rahmen
        # self.setStyleSheet("QToolButton {border-style: none;}")
        # Vorzugs-Variante mit hover-Kästchen (zusammen mit PointingHandCursor und ToolTip Hinweise auf Funktion)
        self.setStyleSheet(
            "QToolButton { border: 1px solid transparent; } QToolButton::hover {border: 1px solid silver;}"
        )


class MyEditToolButton(MyToolButton):
    """derived MyToolButton for edit-functions
    selectable inside QTreeView qtrv_feature_selection.findChildren(MyEditToolButton)
    enable/disable/hide/show according to dataLyr-is-editable, not used so far"""

    # Rev. 2025-11-08
    def __init__(
        self,
        icon: QIcon,
        tool_tip: str,
        whats_this: str,
    ):
        """constructor
        Args:
            icon (QIcon): icon for this button
            tool_tip (str): ToolTip-Text
            whats_this (str): for setWhatsThis, possible differentiation

        """
        # Rev. 2025-11-08
        super().__init__(icon,tool_tip)

        self.setWhatsThis(whats_this)

        self.setCursor(Qt.PointingHandCursor)

class MyDeleteToolButton(MyEditToolButton):
    """derived MyToolButton for delete-functions
    selectable inside QTreeView qtrv_feature_selection.findChildren(MyDeleteToolButton)
    enable/disable/hide/show according to dataLyr-is-editable"""
        # Rev. 2025-11-08
    def __init__(
        self,
        icon: QIcon,
        tool_tip: str = '',
        whats_this: str = '',
    ):
        """constructor
        Args:
            icon (QIcon): icon for this button
            tool_tip (str): ToolTip-Text
            whats_this (str): for setWhatsThis, possible differentiation
        """
        # Rev. 2025-11-08
        super().__init__(icon,tool_tip,whats_this)


class MyCellWidget(QWidget):
    """default-cell-widget inside QTreeView, just a QWidget with QHboxLayout and some styling (margins, spacing, alignment)
    will contain the MyToolButtons"""

    # Rev. 2025-01-04

    def __init__(self):
        """constructor"""
        # Rev. 2025-01-04
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.layout().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # margins to use around the layout, int left, int top, int right, int bottom
        self.layout().setContentsMargins(3, 0, 3, 0)
        # spacing between widgets inside the layout
        self.layout().setSpacing(3)

class MyPaddingLeftDelegate(QStyledItemDelegate):
    """left padded, necessary to get some space in the left of MyStandardItem for MyCellWidget/MyToolButton
    the necessary padding is (number * width) + (number - 1 *  spacing) + ContentsMargins-left + ContentsMargins-Right
    should be used also for padding_left = 0
    sample-calculation for implemented default-styles in QTreeView
    MyToolButton width = 20px
    MyCellWidget spacing = 3px
    MyCellWidget ContentsMargins-left = 3px
    MyCellWidget ContentsMargins-right = 3px

    1 MyToolButton => 1 * 20 + (1-1) * 3 + 3 + 3 = 26
    2 MyToolButton => 2 * 20 + (2-1) * 3 + 3 + 3 = 49
    3 MyToolButton => 3 * 20 + (3-1) * 3 + 3 + 3 = 72
    4 MyToolButton => 4 * 20 + (4-1) * 3 + 3 + 3 = 95
    5 MyToolButton => 5 * 20 + (5-1) * 3 + 3 + 3 = 118
    6 MyToolButton => 6 * 20 + (6-1) * 3 + 3 + 3 = 141
    7 MyToolButton => 7 * 20 + (7-1) * 3 + 3 + 3 = 164
    """

    def __init__(self, padding_left: int, background_color:str = '', parent=None):
        """initialize with settings for the paint-method
        Args:
            padding_left (int): padding-left in pixel => place for MyCellWidget with n-MyToolButtons
            background_color (str): background-color in rgb-hex
            parent (QWidget): Parent-Object in Qt-Hierarchy
        """
        # Rev. 2026-01-13
        super().__init__(parent)
        self.padding_left = padding_left
        self.background_color = background_color

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Reimplemented:
            Returns the size needed by the delegate to display the item specified by index, taking into account the style information provided by option.
            returns super().sizeHint + padding_left

        Args:
            option (QStyleOptionViewItem)
            index (QModelIndex)

        Returns:
            QSize, width and height for the Widget
        """
        # Rev. 2025-01-04
        super_size_hint = super().sizeHint(option, index)
        super_size_hint.setWidth(super_size_hint.width() + self.padding_left)
        return super_size_hint

    def paint(self, painter:QStylePainter, option:QStyleOption, index:QModelIndex):
        """Remplemented:
        moves the drawing-rect and the position of text padding_left to right

        Args:
            painter (QStylePainter)
            option (QStyleOption)
            index (QModelIndex)
        """
        # Rev. 2025-01-04
        if option.state & QStyle.State_Selected:
            #  draw original un-padded rect in selected options to avoid padding-gap in highlighted background
            painter.fillRect(option.rect, option.palette.brush(QPalette.Highlight))
            option.font.setBold(True)

        if self.background_color:
            painter.fillRect(option.rect, self.background_color)

        # padding the text-contents via adjusted (right-shifted) option.rect
        # the altered option.rect will be used by super().paint, which will draw the contents of the MyStandardItem
        option.rect.adjust(self.padding_left, 0, 0, 0)
        super().paint(painter, option, index)

class MyLogTable(QTableView):
    """Table for Log-Purpose"""
    # Rev. 2025-10-04
    def __init__(self, parent:QWidget):
        """Constructor

        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
        """
        # Rev. 2025-10-06
        super().__init__(parent)
        self.setIconSize(QSize(20, 20))
        self.setAlternatingRowColors(True)
        # rows not resizable without header
        # self.verticalHeader().hide()
        self.setEditTriggers(self.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
        header_labels = ["#", "Time", "Level", "Message", "File", "Line", "Function"]
        self.setModel(QStandardItemModel(0, len(header_labels)))
        self.model().setHorizontalHeaderLabels(header_labels)

        # time in column 1, in model stored as milliseconds since epoche
        self.log_delegate = self.TimeDelegate()
        self.setItemDelegateForColumn(1, self.log_delegate)





    class TimeDelegate(QStyledItemDelegate):
        """delegate for time-contents, f. e. QDateTime.currentTime()"""
        def __init__(self, parent=None):
            super().__init__(parent)

        # Note: if stored as milliseconds instead of time, f.e. QDateTime.currentDateTime().toMSecsSinceEpoch(),
        # implement suitable delegate with datetime.datetime.fromtimestamp(value / 1000).strftime('%H:%M:%S')
        def displayText(self, value, locale):
            """return formatted time-string, does not use locale, because some locale settings seem to be ignored"""
            try:
                return locale.toString(value, "hh:mm:ss")
            except:
                pass

class MyLogItem(QStandardItem):
    """QStandardItem for use in MyLogTable"""
    # default-colors for error-level-symbolization
    bg_colors = {
        'WARNING':  "#FFB839",
        'EXCEPTION':  "#FFB839",
        'SUCCESS': "#B9FFBD",
        'INFO': "#AFC8FF",
        'CRITICAL': "#FF3939",
    }

    def __init__(self, display_value: Any = None,tooltip_value: Any = None, bg_color: str = None, parent = None):
        """constructor

        Args:
            display_value (Any, optional): value for display
            tooltip_value (Any, optional): value for tooltip
            bg_color (str, optional): background-color, key for the above bg_colors-dicth
            parent (QWidget, optional)
        """
        super().__init__(parent)
        base_font = QFont()
        bold_font = QFont(base_font)
        bold_font.setPointSize(10)
        bold_font.setWeight(81)

        self.setData(display_value, Qt.DisplayRole)
        self.setData(tooltip_value, Qt.ToolTipRole)

        if bg_color:
            self.setBackground(QColor(self.bg_colors.get(bg_color)))

        self.setData(bold_font, Qt.FontRole)
        self.setData(
            Qt.AlignVCenter | Qt.AlignLeft,
            Qt.TextAlignmentRole,
        )


class MyQComboBox(QComboBox):
    """pimped QComboBox for fields and layers, uses QTableView for DropDown"""
    # Rev. 2025-10-04
    def __init__(
        self,
        parent:QWidget,
        column_pre_settings: list,
        option_text_template: str = "{0}",
        show_clear_button: bool = False,
    ):
        """constructor

        Args:
            parent (QWidget): Qt-Hierarchy
            column_pre_settings (list): settings for columns
            option_text_template (str, optional): Template for the QLineEdit. Defaults to "{0}".
            show_clear_button (bool, optional): Show the Clear-Button in the LineEdit. Defaults to False.
        """
        # Rev. 2025-10-04
        super().__init__(parent)

        self.column_settings = column_pre_settings

        self.option_text_template = option_text_template

        self.show_clear_button = show_clear_button

        # self.clear_button_icon = self.style().standardIcon(70)
        # optinally define own icon:
        self.clear_button_icon = None

        self.setModel(QStandardItemModel())

        self.resize_mode = "resize_to_contents"
        self.calc_width = 0
        self.calc_height = 0

        self.fix_width = 600
        self.fix_height = 800

        # via handle resizable size
        self.pop_up_width = None
        self.pop_up_height = None

        self.view_tool_tip = None

        self.setView(QTableView(self))

        # row-wise select
        self.view().setSelectionBehavior(QAbstractItemView.SelectRows)

        # some default-settings
        self.view().setShowGrid(True)
        self.view().setSortingEnabled(True)
        self.view().setWordWrap(False)
        self.view().setTextElideMode(Qt.ElideRight)
        self.view().horizontalHeader().show()
        self.view().verticalHeader().hide()
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view().setMinimumHeight(100)
        self.view().setMinimumWidth(200)

        pop_up_frame = self.findChild(QFrame)

        # size-grip in bottom/right corner
        self.qsgr = QSizeGrip(self)
        self.qsgr.setStyleSheet(
            "QSizeGrip {background-color: silver; width: 10px; height: 10px;}"
        )

        self.qsgr.mouseReleaseEvent = self.release_size_grip

        # QBoxLayout
        pop_up_frame.layout().addWidget(self.qsgr, 0, Qt.AlignRight)

        # self.view().verticalHeader().setMinimumSectionSize(20)
        # self.view().verticalHeader().setMaximumSectionSize(20)
        self.view().verticalHeader().setDefaultSectionSize(20)

        # ResizeMode-enum :
        # Interactive -> 0 cols can be resized by user, initial size as defined in col_widths
        # Stretch -> 1 cols will be stretched to the width of the QComboBox -> width of QTableView == width of QCombBox
        # Fixed -> 2 fix defined widths, width of QTableView = sum(col_widths)
        # ResizeToContents -> 3 cols will be stretched to their contents -> width of QTableView = sum(calculated col_widths) + x

        self.view().horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.view().horizontalHeader().setStretchLastSection(True)

        # Breite/Höhe der Icons in QStandardItems, falls diese überhaupt verwendet werden,
        # nicht des ClearButtons
        self.setIconSize(QSize(15, 15))

        if self.show_clear_button:
            self.setLineEdit(QLineEdit())
            self.lineEdit().setClearButtonEnabled(True)
            self.lineEdit().setReadOnly(True)
            self.lineEdit().setFont(self.font())
            # convenience: Click on lineEdit with same popuo-functionality as klick on drop-down-button
            self.lineEdit().mousePressEvent = self.show_popup

            clear_button = self.lineEdit().findChild(QToolButton)
            # note: to show a blank LineEdit if nothing is selected the model needs a blank row in model-data
            clear_button.clicked.connect(lambda: self.setCurrentIndex(-1))
            # enable clear_button in an readOnly == disabled lineEdit()
            clear_button.setEnabled(True)
            # clear_button_icon applied with set_model

    def release_size_grip(self, evt: QMouseEvent):
        """re-implemented mouseReleaseEvent for the QSizeGrip
        stores the resized format for later restore in showPopup"""
        pop_up_frame = self.findChild(QFrame)
        self.pop_up_width = pop_up_frame.width()
        self.pop_up_height = pop_up_frame.height()

        QSizeGrip.mouseReleaseEvent(self.qsgr, evt)

    def set_model(self, in_model: QStandardItemModel):
        """loads model-data and applies some visual settings f.e. headers and tool_tips, width/height/position of

        Args:
            in_model(QStandardItemModel): data for the QComboBox rsp. the DropDown-QTableView
        """
        # Rev. 2025-02-01
        with QSignalBlocker(self):
            self.model().clear()
            self.setModel(in_model)
            for col_idx, column_setting in enumerate(self.column_settings):
                self.model().setHorizontalHeaderItem(
                    col_idx, QStandardItem(column_setting.get("header", ""))
                )
            self.view().setToolTip(self.view_tool_tip)
            self.view().resizeColumnsToContents()
            if self.show_clear_button and self.clear_button_icon:
                # must be applied here because clear_button_icon not parameter of __init__
                self.lineEdit().findChild(QToolButton).setIcon(self.clear_button_icon)

            if self.resize_mode == "resize_to_contents":
                calc_height = 0
                for rc in range(self.model().rowCount()):
                    calc_height += self.view().verticalHeader().sectionSize(rc)
                # if not self.view().horizontalScrollBar().isHidden():
                #     calc_height += self.view().horizontalScrollBar().height()
                #     # wird nicht angezeigt, aber ist trotzdem nicht hidden
                calc_height += self.view().horizontalHeader().height()
                calc_height += self.view().frameWidth() * 2
                calc_height += self.qsgr.height()
                self.calc_height = calc_height
                calc_width = 0
                for cc in range(self.model().columnCount()):
                    calc_width += self.view().columnWidth(cc)
                calc_width += self.view().frameWidth() * 2
                # add margins and paddings, estimated value via try
                # perhaps the sort-icons in header? On windows above the header, under linux beside the header
                calc_width += 15 * self.model().columnCount()
                # because of self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                # if (
                #     self.pop_up_height
                #     == self.window()
                #     .windowHandle()
                #     .screen()
                #     .availableGeometry()
                #     .height()
                # ):
                #     calc_width += 15
                self.calc_width = calc_width

            elif self.resize_mode == "fix_size":
                self.pop_up_width = self.fix_width
                self.pop_up_height = self.fix_height

    def showPopup(self):
        """derived version, which opens popup
        positions it right below the LineEdit and resizes the width and height"""

        QComboBox.showPopup(self)
        pop_up_frame = self.findChild(QFrame)
        if not self.pop_up_width or self.pop_up_height:
            # first time call: calculate size
            if self.resize_mode == "resize_to_contents":
                # enlarge to calculated necessary or LineEdit-width:
                self.pop_up_width = max(self.calc_width, self.width())
                # but not wider then current screen
                self.pop_up_width = min(
                    self.pop_up_width,
                    self.window().windowHandle().screen().availableGeometry().width(),
                )
                self.pop_up_height = min(
                    self.calc_height,
                    self.window().windowHandle().screen().availableGeometry().height(),
                )
            else:
                # resize to fixed size
                self.pop_up_width = self.fix_width
                self.pop_up_height = self.fix_height

        # later: resize to last size, evtl. user defined
        pop_up_frame.resize(self.pop_up_width, self.pop_up_height)

        left = self.mapToGlobal(QPoint(0, 0)).x()
        top = self.mapToGlobal(QPoint(0, 0)).y() + self.height()
        if (
            top + pop_up_frame.height()
            > self.window().windowHandle().screen().availableGeometry().height()
        ):
            top = (
                self.window().windowHandle().screen().availableGeometry().height()
                - pop_up_frame.height()
            )
        pop_up_frame.move(left, top)

    def show_popup(self, event):
        """derived version, which opens popup
        positions it right below the LineEdit and resizes the width and height"""
        self.showPopup()



    def paintEvent(self, event):
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        painter = QStylePainter(self)
        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        if self.currentIndex() > -1:
            option_text_result = self.option_text_template

            # Zugriff auf die Modelldaten, die im dargestellten
            for col_idx, column_setting in enumerate(self.column_settings):
                item_idx = self.model().index(self.currentIndex(), col_idx)
                if column_setting.get("option_text_qexp"):
                    # Spezialwert via Ausdruck
                    option_value = (
                        self.model().itemData(item_idx).get(Qt_Roles.OPTION_TEXT)
                    )
                else:
                    # Default-Wert gem. aktueller Darstellung
                    option_value = self.model().itemData(item_idx).get(Qt.DisplayRole)

                # avoid 'None' as displayValue
                option_text = ""
                if option_value is not None:
                    option_text = str(option_value)

                # f-string-artiges Suchen und Ersetzen {0} => column 0 {1} => column 1...
                option_text_result = option_text_result.replace(
                    f"{{{col_idx}}}", option_text
                )

            if self.show_clear_button:
                # avoid disturbing blinking cursor...
                self.lineEdit().setText(option_text_result)
                # not necessary, lineEdit is readOnly
                # self.lineEdit().clearFocus()
            else:
                option.currentText = option_text_result

            painter.drawControl(QStyle.CE_ComboBoxLabel, option)

    def select_by_value(
        self, cols_roles_flags: list, select_value: Any, block_signals: bool = True
    ) -> QModelIndex|None:
        """scans the recursive data-model for a specific value, selects the first found row and return its row-index

        Args:
            cols_roles_flags (list): list of lists [col_idx, role_idx, flags]
            select_value (Any): the compare-value
            block_signals (bool): do not trigger any indexChanged-signal

        Returns:
            QModelIndex|None if found, else None
        """
        # Rev. 2025-01-22
        if self.model():
            model = self.model()
            for col_role_flag in cols_roles_flags:
                col_idx = col_role_flag[0]
                role_idx = col_role_flag[1]
                flags = col_role_flag[2]
                # only one hit required
                matches = model.match(
                    model.index(0, col_idx), role_idx, select_value, 1, flags
                )
                for index in matches:
                    self.blockSignals(block_signals)
                    self.setCurrentIndex(index.row())
                    self.blockSignals(False)
                    # select the first hit and return to sender
                    return index


class MyLayerSelectorQComboBox(MyQComboBox):
    """QComboBox for select of Project-Layers with multiple and sortable columns, uses QTableView
    Metadata stored in column 0:
        - RETURN_VALUE => layer-id
    """

    def __init__(
        self,
        parent:QWidget,
        column_pre_settings:list,
        option_text_template: str = "{0}",
        show_clear_button: bool = True,
        show_disabled: bool = False,
    ):
        """Constructor
        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
            column_pre_settings (list): Column-Configuration
            option_text_template (str): Template for the QLineEdit if not DropDown
            show_clear_button (bool): Show Clear-Button in the QLineEdit to clear the selection
            show_disabled (bool):
                True => disabled items are listed,
                False (default): disabled items are not listed making the list clearer
        """
        # Rev. 2025-10-06
        super().__init__(
            parent, column_pre_settings, option_text_template, show_clear_button
        )
        self.show_disabled = show_disabled
        self.pop_up_width = 500
        self.pop_up_height = 300
        self.setMaximumWidth(300)

    def load_data(
        self, enable_criteria: dict = {}, disable_criteria: dict = {}
    ):
        """Load data == scan project-layers with the criterias and fill the model

        each key of the criteria-dicts has a check-list:
            layer_type => enable/disable layer according to its type
                coarse structure
                https://api.qgis.org/api/classQgis.html#aa5105ead70f1fd9cd19258c08a9a513b
                enum class Qgis::LayerType
                    0 Vector layer
                    1 Raster layer
                    ...

            geometry_type => enable/disable layer according to its geometry type (automatically filters Vector-Layer)
                https://api.qgis.org/api/classQgis.html#a84964253bb44012b246c20790799c04d
                enum class Qgis::GeometryType : int
                Qgis.GeometryType.Point 0
                1 Line
                2 Polygon
                3 Unknown
                4 Null

            wkb_type => enable/disable layer according to its geometry-wkb-type (automatically filters Vector-Layer)
                fine structure
                https://api.qgis.org/api/classQgis.html#adf94495b88fbb3c5df092267ccc94509
                Qgis.WkbType.Unknown 0
                Qgis.WkbType.Point 1
                Qgis.WkbType.LineString 2 (nur einfache LineString, keine LineStringM/LineStringZ/MultiLineString...)
                Qgis.WkbType.Polygon 3

            data_provider => enable/disable layer according to its dataProvider().name()
                https://api.qgis.org/api/classQgsDataProvider.html
                wms
                ogr
                virtual

            crs => enable/disable layer according to its projection (list of QgsCoordinateReferenceSystem)

            layer_name => list of enabled/disabled layer-names
            layer_id => list of enabled/disabled layer-ids
            layer =>  list of enabled/disabled map-layers

        Args:
            enable_criteria (dict): positive validity-checks, checked first
            disable_criteria (dict): negative validity-checks, checked second
        """
        # Rev. 2026-01-13

        model = QStandardItemModel(0, 4)
        # Leerzeile als erste, um bei setIndex(-1) nicht eine erste Zeile mit Werten darzustellen
        items = [
            MyStandardItem(),
            MyStandardItem(),
            MyStandardItem(),
            MyStandardItem(),
        ]
        model.appendRow(items)
        idx = 0
        # TOC order, may not be draw-order because of "Layer Order", but also geometry-less layers included
        # type: QgsLayerTreeLayer
        ltr_layers = qgis._core.QgsProject.instance().layerTreeRoot().findLayers()
        # TOC-order or Drawing-Order, but no geometry-less layer
        # layers = qgis._core.QgsProject.instance().layerTreeRoot().layerOrder()
        # unordered list, perhaps ordered by add-to-project-range?
        # layers = qgis._core.QgsProject.instance().mapLayers().values()

        # for cl in layers:
        for ltrl_layer in ltr_layers:
            if ltrl_layer.layer() and ltrl_layer.layer().isValid():
                cl = ltrl_layer.layer()
                name_item = MyStandardItem()
                name_item.setData(cl.name(), Qt.DisplayRole)
                name_item.setData(cl.name(), Qt_Roles.CUSTOM_SORT)
                # name_item.setData(cl, Qt.UserRole)
                # RETURN_VALUE => layer-id
                name_item.setData(cl.id(), Qt_Roles.RETURN_VALUE)

                geometry_item = MyStandardItem()
                if isinstance(cl, QgsVectorLayer):
                    display_value = qgis._core.QgsWkbTypes.displayString(
                        cl.dataProvider().wkbType()
                    )
                else:
                    display_value = "Raster"

                geometry_item.setData(display_value, Qt.DisplayRole)
                geometry_item.setData(display_value, Qt_Roles.CUSTOM_SORT)

                provider_item = MyStandardItem()
                if (
                    isinstance(cl, QgsVectorLayer)
                    and cl.dataProvider().name() != "virtual"
                ):
                    display_value = f"{cl.dataProvider().name()} ({cl.dataProvider().storageType()})"
                else:
                    display_value = cl.dataProvider().name()

                provider_item.setData(cl.dataProvider().name(), Qt.DisplayRole)
                provider_item.setData(display_value, Qt_Roles.CUSTOM_SORT)

                index_item = MyStandardItem()
                index_item.setData(idx, Qt.DisplayRole)
                index_item.setData(idx, Qt_Roles.CUSTOM_SORT)

                items = [name_item, geometry_item, provider_item, index_item]

                enabled = True
                if enable_criteria:
                    for key, value_list in enable_criteria.items():
                        if key == "layer_type":
                            enabled &= cl.type() in value_list
                        elif key == "geometry_type":
                            # AttributeError: 'QgsRasterLayer' object has no attribute 'geometryType'
                            enabled &= (
                                hasattr(cl, "geometryType")
                                and cl.geometryType() in value_list
                            )
                        elif key == "wkb_type":
                            # AttributeError: 'QgsRasterLayer' object has no attribute 'geometryType'
                            enabled &= (
                                hasattr(cl, "wkbType") and cl.wkbType() in value_list
                            )
                        elif key == "layer_name":
                            enabled &= cl.name() in value_list
                        elif key == "layer_id":
                            enabled &= cl.id() in value_list
                        elif key == "layer":
                            enabled &= cl in value_list
                        elif key == "data_provider":
                            enabled &= (
                                hasattr(cl, "dataProvider")
                                and cl.dataProvider().name() in value_list
                            )
                        elif key == "crs":
                            enabled &= hasattr(cl, "crs") and cl.crs() in value_list
                        else:
                            raise NotImplementedError(
                                f"enable_criteria '{key}' not implemented"
                            )

                if disable_criteria:
                    for key, value_list in disable_criteria.items():
                        if key == "layer_type":
                            enabled &= cl.type() in value_list
                        elif key == "geometry_type":
                            enabled &= not (
                                hasattr(cl, "geometryType")
                                and cl.geometryType() in value_list
                            )
                        elif key == "wkb_type":
                            # AttributeError: 'QgsRasterLayer' object has no attribute 'geometryType'
                            enabled &= not (
                                hasattr(cl, "wkbType") and cl.wkbType() in value_list
                            )
                        elif key == "layer_name":
                            enabled &= cl.name() not in value_list
                        elif key == "layer_id":
                            enabled &= cl.id() not in value_list
                        elif key == "layer":
                            enabled &= cl not in value_list
                        elif key == "data_provider":
                            enabled &= not (
                                hasattr(cl, "dataProvider")
                                and cl.dataProvider().name() in value_list
                            )
                        elif key == "crs":
                            enabled &= not (
                                hasattr(cl, "crs") and cl.crs() in value_list
                            )
                        else:
                            raise NotImplementedError(
                                f"disable_criteria '{key}' not implemented"
                            )

                for col_idx, item in enumerate(items):
                    item.setEnabled(enabled)

                    column_setting = self.column_settings[col_idx]
                    icon = column_setting.get("icon", None)
                    if icon:
                        item.setData(icon, Qt.DecorationRole)

                    alignment = column_setting.get("alignment", None)
                    if alignment:
                        item.setTextAlignment(alignment)

                    font = column_setting.get("font", None)
                    if font:
                        item.setFont(font)

                    tool_tip = column_setting.get("tool_tip", None)
                    if tool_tip:
                        item.setData(tool_tip, Qt.ToolTipRole)

                if enabled or self.show_disabled:
                    model.appendRow(items)

            idx += 1

        self.set_model(model)


class MyFieldSelectorQComboBox(MyQComboBox):
    """QComboBox for select of layer-field with multiple and sortable columns, uses QTableView
    Field-Metadata stored in column 0 of the model:
        DisplayRole => field-name
        RETURN_VALUE => field-name
    """
    # Rev. 2026-01-13
    # used for pragmatic field_type-check: not the exact field-type, but any integer
    # each of these are interchangeable valid for joins
    integer_field_types = [
        QVariant.Int,
        QVariant.UInt,
        QVariant.LongLong,
        QVariant.ULongLong,

        QMetaType.Int,
        QMetaType.UInt,
        QMetaType.LongLong,
        QMetaType.ULongLong,
    ]

    # resolve wildcard "any_number"
    numeric_field_types = [
        QVariant.Int,
        QVariant.UInt,
        QVariant.LongLong,
        QVariant.ULongLong,
        QVariant.Double,

        QMetaType.Int,
        QMetaType.UInt,
        QMetaType.LongLong,
        QMetaType.ULongLong,
        QMetaType.Double,
    ]

    #resolve wildcard "any_pk": any integer or string
    pk_field_types = [
        QVariant.Int,
        QVariant.UInt,
        QVariant.LongLong,
        QVariant.ULongLong,
        #QVariant.Double,
        QVariant.String,

        QMetaType.Int,
        QMetaType.UInt,
        QMetaType.LongLong,
        QMetaType.ULongLong,
        #QMetaType.Double,
        QMetaType.QString,
    ]

    # note for Qt6: new signature, QMetaType.Type.Int
    # but not deprecated so far

    def __init__(
        self,
        parent:QWidget,
        column_pre_settings:list,
        option_text_template: str = "{0}",
        show_clear_button: bool = True,
        show_disabled: bool = True,
    ):
        """Constructor

        Args:
            parent (QWidget): Qt-Hierarchy
            column_pre_settings (list): settings for columns
            option_text_template (str, optional): Template for the LineEdit. Defaults to "{0}".
            show_clear_button (bool, optional): Show the Clear-Button in the LineEdit. Defaults to True.
            show_disabled (): Show disabled fields (see load_data -> disable_criteria) in the DropDown-QTableView. Defaults to True.
        """
        # Rev. 2026-01-13
        super().__init__(
            parent, column_pre_settings, option_text_template, show_clear_button
        )
        self.show_disabled = show_disabled
        self.pop_up_width = 400
        self.pop_up_height = 250
        self.setMaximumWidth(300)


    def load_data(
        self,
        vector_layer: QgsVectorLayer,
        enable_criteria: dict = {},
        disable_criteria: dict = {},
    ):
        """Load-Data == Scan the fields against enable_criteria/disable_criteria and fill the model

        each key of enable_criteria/disable_criteria has a check-list:
            field_type => enable/disable field according to its type, pragmatic approach for integers, wildcard "any_int" and "any_pk"
            field_origin => enable/disable field according to its origin
            enum class Qgis::FieldOrigin
            1 => Qgis.FieldOrigin.Provider, 2 => Qgis.FieldOrigin.Join, 3 => Qgis.FieldOrigin.Edit 4 => Qgis.FieldOrigin.Expression
            see https://api.qgis.org/api/classQgis.html#aa56ef8dbeaee2fa1961c1a6f7e0f79b2
            field_name => list of enabled/disabled field-names
            field_idx => list of enabled/disabled field-indices

        Args:
            vector_layer (QgsVectorLayer)
            enable_criteria (dict): positive validity-checks (field_type/field_origin/field_name/field_idx), checked first
            disable_criteria (dict): negative validity-checks (field_type/field_origin/field_name/field_idx), checked second
        """
        # Rev. 2026-01-13
        model = QStandardItemModel(0, 4)
        # Leerzeile als erste, um bei setIndex(-1) nicht eine erste Zeile mit Werten darzustellen
        items = [
            MyStandardItem(),
            MyStandardItem(),
            MyStandardItem(),
            MyStandardItem(),
        ]
        model.appendRow(items)
        idx = 0
        fields = vector_layer.fields()

        # pragmatic approach: accept any type of integer, resolve wildcard "any_int" and "any_number"
        enable_field_types = []
        disable_field_types = []

        for key, value_list in enable_criteria.items():
            if key == "field_type":
                enable_field_types = value_list

                int_inters = [ft for ft in enable_field_types if ft in self.integer_field_types]

                if "any_int" in enable_field_types or int_inters:
                    enable_field_types += self.integer_field_types

                if "any_number" in enable_field_types:
                    enable_field_types += self.numeric_field_types

                if "any_pk" in enable_field_types:
                    enable_field_types += self.pk_field_types

                # unique
                enable_field_types = list(dict.fromkeys(enable_field_types))

        for key, value_list in disable_criteria.items():
            if key == "field_type":
                disable_field_types = value_list

                int_inters = [ft for ft in disable_field_types if ft in self.integer_field_types]

                if "any_int" in disable_field_types or int_inters:
                    disable_field_types += self.integer_field_types

                if "any_number" in disable_field_types:
                    disable_field_types += self.numeric_field_types

                if "any_pk" in disable_field_types:
                    disable_field_types += self.pk_field_types

                # unique
                disable_field_types = list(dict.fromkeys(disable_field_types))


        for field in fields:
            name_item = MyStandardItem()
            name_item.setData(field.name(), Qt.DisplayRole)
            name_item.setData(field.name(), Qt_Roles.CUSTOM_SORT)
            name_item.setData(field.name(), Qt_Roles.RETURN_VALUE)


            is_pk_item = MyStandardItem()
            # is_pk_item.setTextAlignment(Qt.AlignCenter)
            if idx in vector_layer.dataProvider().pkAttributeIndexes():
                is_pk_item.setData("✔", Qt.DisplayRole)
                is_pk_item.setData(1, Qt_Roles.CUSTOM_SORT)

            type_item = MyStandardItem()
            type_item.setData(field.friendlyTypeString(), Qt.DisplayRole)
            type_item.setData(field.friendlyTypeString(), Qt_Roles.CUSTOM_SORT)

            index_item = MyStandardItem()
            index_item.setData(idx, Qt.DisplayRole)
            index_item.setData(idx, Qt_Roles.CUSTOM_SORT)

            items = [name_item, type_item, is_pk_item, index_item]

            enabled = True
            if enable_criteria:
                for key, value_list in enable_criteria.items():
                    if key == "field_type":
                        enabled &= field.type() in enable_field_types
                    elif key == "field_origin":
                        enabled &= fields.fieldOrigin(idx) in value_list
                    elif key == "field_name":
                        enabled &= field.name() in value_list
                    elif key == "field_idx":
                        enabled &= idx in value_list
                    else:
                        raise NotImplementedError(
                            f"enable_criteria '{key}' not in field_type/field_origin/field_name/field_idx"
                        )

            if disable_criteria:
                for key, value_list in disable_criteria.items():
                    if key == "field_type":
                        enabled &= field.type() not in disable_field_types
                    elif key == "field_origin":
                        enabled &= fields.fieldOrigin(idx) not in value_list
                    elif key == "field_name":
                        enabled &= field.name() not in value_list
                    elif key == "field_idx":
                        enabled &= idx not in value_list
                    else:
                        raise NotImplementedError(
                            f"disable_criteria '{key}' not in field_type/field_origin/field_name/field_idx"
                        )

            for col_idx, item in enumerate(items):
                item.setEnabled(enabled)

                column_setting = self.column_settings[col_idx]
                icon = column_setting.get("icon", None)
                if icon:
                    item.setData(icon, Qt.DecorationRole)

                alignment = column_setting.get("alignment", None)
                if alignment:
                    item.setTextAlignment(alignment)

                font = column_setting.get("font", None)
                if font:
                    item.setFont(font)

                tool_tip = column_setting.get("tool_tip", None)
                if tool_tip:
                    item.setData(tool_tip, Qt.ToolTipRole)

            if enabled or self.show_disabled:
                model.appendRow(items)

            idx += 1

        self.set_model(model)


class MyFeatureSelectorQComboBox(MyQComboBox):
    """QComboBox with multiple and sortable columns for feature-select, uses QTableView
    only for select, not for edits"""
    # Rev. 2026-01-13
    def __init__(
        self,
        parent,
        column_pre_settings: list,
        option_text_template: str = "{0}",
        show_clear_button: bool = False,
    ):
        """constructor

        Args:
            parent (QWidget): Qt-Hierarchy
            column_pre_settings (list): settings for columns
            option_text_template (str, optional): Template for the LineEdit. Defaults to "{0}".
            show_clear_button (bool, optional): Show the Clear-Button in the LineEdit. Defaults to False.
        """
        # Rev. 2026-01-13
        super().__init__(
            parent, column_pre_settings, option_text_template, show_clear_button
        )

    def load_data(
        self, column_settings: list, reference_layer: QgsVectorLayer
    ):
        """Load-Data == scan the features of the layer and populate model

        Args:
            column_settings (list): Settings for the columns
            reference_layer (QgsVectorLayer): the scaned layer
        """
        # Rev. 2026-01-13
        if isinstance(column_settings, list):
            if isinstance(self.column_settings, list):
                # tricky: merge dictionaries keeping/overwriting existing and append new ones
                for col_idx, column_setting in enumerate(column_settings):
                    self.column_settings[col_idx] |= column_setting
            else:
                self.column_settings = column_settings

        num_cols = len(self.column_settings)
        in_model = QStandardItemModel(0, num_cols)

        ref_context = qgis._core.QgsExpressionContext()

        for col_idx, column_setting in enumerate(self.column_settings):
            display_expression = column_setting.get("display_expression")
            if display_expression:
                display_qexp = qgis._core.QgsExpression(display_expression)
                display_qexp.prepare(ref_context)
                column_setting["display_qexp"] = display_qexp

            custom_sort_expression = column_setting.get("custom_sort_expression")
            if custom_sort_expression:
                custom_sort_qexp = qgis._core.QgsExpression(custom_sort_expression)
                custom_sort_qexp.prepare(ref_context)
                column_setting["custom_sort_qexp"] = custom_sort_qexp

            tooltip_expression = column_setting.get("tooltip_expression")
            if tooltip_expression:
                tooltip_qexp = qgis._core.QgsExpression(tooltip_expression)
                tooltip_qexp.prepare(ref_context)
                column_setting["tooltip_qexp"] = tooltip_qexp

            option_text_expression = column_setting.get("option_text_expression")
            if option_text_expression:
                option_text_qexp = qgis._core.QgsExpression(option_text_expression)
                option_text_qexp.prepare(ref_context)
                column_setting["option_text_qexp"] = option_text_qexp

            original_value_expression = column_setting.get("original_value_expression")
            if original_value_expression:
                original_value_qexp = qgis._core.QgsExpression(
                    original_value_expression
                )
                original_value_qexp.prepare(ref_context)
                column_setting["original_value_qexp"] = original_value_qexp

            current_value_expression = column_setting.get("current_value_expression")
            if current_value_expression:
                current_value_qexp = qgis._core.QgsExpression(current_value_expression)
                current_value_qexp.prepare(ref_context)
                column_setting["current_value_qexp"] = current_value_qexp

        for ref_feature in reference_layer.getFeatures():
            ref_fid = ref_feature.id()
            ref_context.setFeature(ref_feature)
            ref_record = ref_feature.attributeMap()
            this_row_items = []
            for col_idx, column_setting in enumerate(self.column_settings):
                item = MyStandardItem()
                item.setData(ref_fid, Qt_Roles.REF_FID)

                display_qexp = column_setting.get("display_qexp")
                display_value = ""
                if display_qexp:
                    display_value = display_qexp.evaluate(ref_context)
                    item.setData(display_value, Qt.DisplayRole)

                tooltip_qexp = column_setting.get("tooltip_qexp")
                if tooltip_qexp:
                    tooltip_value = tooltip_qexp.evaluate(ref_context)
                    item.setData(tooltip_value, Qt.ToolTipRole)

                option_text_qexp = column_setting.get("option_text_qexp")
                if option_text_qexp:
                    option_text_value = option_text_qexp.evaluate(ref_context)
                    item.setData(option_text_value, Qt_Roles.OPTION_TEXT)

                original_value_qexp = column_setting.get("original_value_qexp")
                if original_value_qexp:
                    original_value = original_value_qexp.evaluate(ref_context)
                    item.setData(original_value, Qt_Roles.ORIGINAL_VALUE)

                current_value_qexp = column_setting.get("current_value_qexp")
                if current_value_qexp:
                    current_value = current_value_qexp.evaluate(ref_context)
                    item.setData(current_value, Qt_Roles.CURRENT_VALUE)

                icon = column_setting.get("icon", None)
                if icon:
                    item.setData(icon, Qt.DecorationRole)

                item.setEnabled(column_setting.get("enabled", True))

                custom_sort_qexp = column_setting.get("custom_sort_qexp")
                # default-Sortierung: alphabetisch nach dargestelltem Inhalt
                custom_sort_value = display_value
                if custom_sort_qexp:
                    custom_sort_value = custom_sort_qexp.evaluate(ref_context)
                item.setData(custom_sort_value, Qt_Roles.CUSTOM_SORT)

                alignment = column_setting.get("alignment", None)
                if alignment:
                    item.setTextAlignment(alignment)

                font = column_setting.get("font", None)
                if font:
                    item.setFont(font)

                this_row_items.append(item)

            in_model.appendRow(this_row_items)

        self.set_model(in_model)


class FlashingQCheckBox(QCheckBox):
    """QCheckBox with flashing borders for x-milli-seconds if user-input is missing or false"""
    # Rev. 2026-01-13
    # stylsheet for flash, ::indicator is the border of the checkbox
    flash_style = "QCheckBox::indicator {border: 3px solid red; background: none;}"
    # stylsheet for no flash, "" resets style to default
    no_flash_style = ""
    # how long?
    flash_total_duration_msec = 2000
    # how fast?
    flash_interval_msec = 100

    def __init__(self, parent:QWidget=None):
        """Constructor

        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
        """
        # Rev. 2025-10-06
        super().__init__(parent)
        self.flash_timer = QTimer(self)
        self.flash_timer.setSingleShot(False)
        self.flash_timer.timeout.connect(self.do_flash)
        # flag-var to switch between flash_style/no_flash_style
        self.is_flashing = False
        # start-time in nano-seconds
        self.timer_started_ns = None

    def start_flash(self):
        """starts the flash and stores current time in self.timer_started_ns"""
        self.setFocus()
        self.flash_timer.start(self.flash_interval_msec)
        self.timer_started_ns = time.perf_counter_ns()

    def do_flash(self):
        """function called every flash_interval_msec until flash_total_duration_msec is reached"""

        flash_time_ns = time.perf_counter_ns() - self.timer_started_ns
        if flash_time_ns < self.flash_total_duration_msec * 1e6:
            # toggles the styles depending on self.is_flashing
            if self.is_flashing:
                self.setStyleSheet(self.no_flash_style)
                self.is_flashing = False
            else:
                self.setStyleSheet(self.flash_style)
                self.is_flashing = True
        else:
            # flash_total_duration_msec is reached, stop the timer and reset the style
            self.flash_timer.stop()
            self.setStyleSheet(self.no_flash_style)


class FlashingBorderQLineEdit(QLineEdit):
    """QLineEdit with flashing borders for x-milli-seconds if user-input is missing or false"""
    # Rev. 2026-01-13
    # stylsheet for flash
    flash_style = "border: 2px solid red"
    # stylsheet for no flash, "" resets style to default
    no_flash_style = ""
    # how long?
    flash_total_duration_msec = 2000
    # how fast?
    flash_interval_msec = 100

    def __init__(self, parent:QWidget=None):
        """Constructor

        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
        """
        # Rev. 2026-01-13
        super().__init__(parent)
        self.flash_timer = QTimer(self)
        self.flash_timer.setSingleShot(False)
        self.flash_timer.timeout.connect(self.do_flash)
        # flag-var to switch between flash_style/no_flash_style
        self.is_flashing = False
        # start-time in nano-seconds
        self.timer_started_ns = None

    def start_flash(self):
        """starts the flash and stores current time in self.timer_started_ns"""
        self.setFocus()
        self.flash_timer.start(self.flash_interval_msec)
        self.timer_started_ns = time.perf_counter_ns()

    def do_flash(self):
        """function called every flash_interval_msec until flash_total_duration_msec is reached"""

        flash_time_ns = time.perf_counter_ns() - self.timer_started_ns
        if flash_time_ns < self.flash_total_duration_msec * 1e6:
            # toggles the styles depending on self.is_flashing
            if self.is_flashing:
                self.setStyleSheet(self.no_flash_style)
                self.is_flashing = False
            else:
                self.setStyleSheet(self.flash_style)
                self.is_flashing = True
        else:
            # flash_total_duration_msec is reached, stop the timer and reset the style
            self.flash_timer.stop()
            self.setStyleSheet(self.no_flash_style)


class ClickableQLineEdit(FlashingBorderQLineEdit):
    """fixes the missing pressed-signal on QLineEdit
    usage here:
    read-only QLineEdit with path to a gpkg-file, the click on the widget is intercepted and instead opens a QT-file-dialog to select a gpkg-file
    """

    # Rev. 2024-12-08

    # "fake" pressed event, which must be connected to the desired slot-method
    pressed = pyqtSignal(bool)

    def __init__(self, parent:QWidget=None):
        """Constructor, original __init__ plus event-filter

        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
        """
        # Rev. 2025-10-06
        super().__init__(parent)
        self.installEventFilter(self)
        self.flashing_border_timer = QTimer(self)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """derived function called on any event, Note: installEventFilter has to be called before

        Args:
            source (QObject): the emitting Qt-Object, in this case self == ClickableQLineEdit-instance
            event (QEvent): the filtered event, any type, see https://doc.qt.io/qt-5/qevent.html#Type-enum
                further actions depend on event.type,
                here: clickable => MouseButtonPress

        Returns:
            bool: either the below defined event.type-specific (MouseButtonPress) or the result super()-eventFilter for any other event-type
        """
        # Rev. 2024-12-08
        if source == self and event.type() == QEvent.MouseButtonPress:
            # emit the "fake" pressed event, which is connected to the desired slot-method
            self.pressed.emit(True)
            return False
        else:
            # delegate all other events to default-handler
            return super().eventFilter(source, event)


class QtbIco(QToolButton):
    """border-less fixed-size icon-button
    derived from QToolButton, so allowing setAutoRepeat"""

    # Rev. 2024-11-30

    def __init__(self, icon: QIcon, tt_txt: str = "", parent:QWidget=None, w: int=20, h: int=20):
        """Constructor

        Args:

            icon (QIcon): f. e. from QResource-File ':icons/mActionTrippleArrowRight.svg'
            tt_txt (str): ToolTip-Text, optional, default ''
            parent (QWidget, optional): Parent-Object in Qt-Hierarchy
            w (int, optional): width, border-width must be taken into account, defaults 20
            h (int, optional): height, border-width must be taken into account, defaults 20
        """
        # Rev. 2025-10-06
        super(QtbIco, self).__init__(parent)

        # style-sheet for isChecked() == True
        self.check_style = (
            "QToolButton::checked { border: 1px solid gray; background-color: silver; }"
        )

        # style-sheet for isChecked() == False
        self.uncheck_style = "QToolButton { border: 1px solid transparent; } QToolButton::hover {background-color: silver;}"

        self.setFixedSize(w, h)
        self.setIconSize(QSize(w, h))
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(icon)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setToolTip(tt_txt)

        self.setStyleSheet(self.uncheck_style)

        # derived QAbstractButton-toggled-signal, only for widgets with setCheckable(True)
        self.toggled.connect(self.s_toggled)

    def s_toggled(self):
        """Slot-Method for the QAbstractButton-toggled-signal
        apply check_style/uncheck_style to symbolize the isChecked-status
        """
        # Rev. 2024-11-30
        if self.isChecked():
            self.setStyleSheet(self.check_style)
        else:
            self.setStyleSheet(self.uncheck_style)


class QpbIco(QPushButton):
    """default QPushButton with optional icon
    derived from QPushButton => auto-scaling width and hight in layout"""

    # Rev. 2024-11-30

    def __init__(
        self,
        pb_txt: str = "",
        tt_txt: str = "",
        icon: QIcon = None,
        ic_w: int = 20,
        ic_h: int = 20,
        parent=None,
    ):
        """Constructor

        Args:
            pb_txt (str): Button-Text
            tt_txt (str): ToolTip-Text
            icon (QIcon): optional, f.e. from QRessource-File ':icons/mActionTrippleArrowRight.svg'
            ic_w (int): width of icon, optional, default 20
            ic_h (int): height of icon, optional, default 20
            parent (QWidget): Parent-Object in Qt-Hierarchy
        """
        # Rev. 2025-10-06

        # Rev. 2024-11-30
        super(QpbIco, self).__init__(parent)

        # style-sheet for isChecked() == True
        self.check_style = "QPushButton::checked { border: 1px solid gray; background-color: silver; padding: 2px;}"

        # style-sheet for isChecked() == False
        self.uncheck_style = "QPushButton { border: 1px solid silver; padding: 2px;} QPushButton::hover {background-color: silver;}"

        self.setCursor(Qt.PointingHandCursor)

        self.setText(pb_txt)
        self.setToolTip(tt_txt)
        self.setMinimumWidth(25)
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(ic_w, ic_h))

        self.setStyleSheet(self.uncheck_style)
        # toggled-signal only for widgets with setCheckable(True)
        self.toggled.connect(self.s_toggled)

    def s_toggled(self):
        """Slot-Method for the QAbstractButton-toggled-signal
        apply check_style/uncheck_style to symbolize the isChecked-status
        """
        # Rev. 2024-11-30
        if self.isChecked():
            self.setStyleSheet(self.check_style)
        else:
            self.setStyleSheet(self.uncheck_style)


class HLine(QFrame):
    """simple horizontal line"""

    # Rev. 2024-11-30
    def __init__(self, parent:QWidget=None, line_width: int = 1, color_hex="#000000"):
        """Constructor

        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
            line_width (int): line-width, optional, default 1
            color_hex (str): line-color rgb-hex, optional, default "#000000" => black
        """
        # Rev. 2025-10-06
        super(HLine, self).__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(line_width)
        self.setContentsMargins(0, 0, 0, 0)
        self.setColor(color_hex)

    def setColor(self, color_hex:str):
        """set line-color, bit complicated in Qt

        Args:
            color_hex (str): color defined in rgb-hex, f.e. "#000000" => black
        """
        if isinstance(color_hex, str):
            pal = self.palette()
            pal.setColor(QPalette.WindowText, QColor(color_hex))
            self.setPalette(pal)




class QGroupBoxExpandable(QGroupBox):
    """QGroupBox with clickable icon and hide/show-functionality
    Note: to show scrollbars in the expanded GroupBox, you have to put the contents into a QScrollArea"""
    _min_height = 20
    _max_height = 12345

    def __init__(self, title:str='', initially_opened: bool = False, parent:QWidget=None):
        """Constructor

        Args:
            title (str): Title-Text
            initially_opened (bool): initially show/hide the Group-Box, defaults False
            parent (QWidget): Parent-Object in Qt-Hierarchy
        """
        # Rev. 2025-10-06
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setStyle(self.GroupBoxProxyStyle())
        self.toggled.connect(self.s_toggle)
        # there seems to be some ugly internal used styleSheet for QGroupBox with bold font and not left-aligned
        self.setStyleSheet("QGroupBox { font-weight: Normal; } ")
        if initially_opened:
            self.setChecked(True)
            self.setMaximumHeight(self._max_height)
        else:
            self.setChecked(False)
            self.setMaximumHeight(self._min_height)

    class GroupBoxProxyStyle(QProxyStyle):
        """QProxyStyle to make QGroupbox expandable
        see:
        https://stackoverflow.com/questions/55977559/changing-qgroupbox-checkbox-visual-to-an-expander
        """

        def drawPrimitive(self, element:QStyle.PrimitiveElement, option:QStyleOption, painter:QPainter, widget: QWidget):
            """derived from super() (QProxyStyle)

            Args:
                element (QStyle.PrimitiveElement): Qt-internal Element inside the widget, here: PE_IndicatorCheckBox inside a QGroupBox
                option (QStyleOption): Style the PrimitiveElement
                painter (QPainter): Draw the PrimitiveElement
                widget (QWidget): Parent-Widget for the PrimitiveElement, here: QGroupBox
            """
            if element == QStyle.PE_IndicatorCheckBox and isinstance(widget, QGroupBox):
                # PE_IndicatorCheckBox inside a QGroupBox
                # paint a PE_IndicatorArrowDown rsp. PE_IndicatorArrowRight into widget dependend on isChecked()
                if widget.isChecked():
                    super().drawPrimitive(
                        QStyle.PE_IndicatorArrowDown, option, painter, widget
                    )
                else:
                    super().drawPrimitive(
                        QStyle.PE_IndicatorArrowRight, option, painter, widget
                    )
            else:
                # paint all PrimitiveElement != PE_IndicatorCheckBox in widgets != QGroupBox
                super().drawPrimitive(element, option, painter, widget)

    def s_toggle(self, status: bool):
        """Toggle Group-Box in Dialog

        Args:
            status (bool): isChecked()-State
        """

        if status:
            self.setMaximumHeight(self._max_height)
        else:
            self.setMaximumHeight(self._min_height)




class QDoubleSpinBoxDefault(QDoubleSpinBox):
    """QDoubleSpinBox to show float values, the up/down arrows larger than default-style (Fusion?)
    customized handling of keyboardModifiers,
    default: 10 * self.singleStep if ctrl-key is hold
    here: three variants with factor 10/100/1000
    parent class for QDoubleNoSpinBox"""
    # Rev. 2026-01-13
    def __init__(
        self,
        parent: QObject = None,
        min_val: float = -sys.float_info.max,
        max_val: float = sys.float_info.max,
        prec: int = 2,
    ):
        """Constructor

        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
            min_val (float): minimum possible value, optional, defaults to -sys.float_info.max
            max_val (float): maximum possible value, optional, defaults to default sys.float_info.max
            prec (int): number of decimals, optional, defaults to 2
        """
        # Rev. 2025-10-06
        super().__init__(parent)

        base_font = QFont()
        spbx_font_m = QFont(base_font)
        spbx_font_m.setPointSize(10)

        self.setFont(spbx_font_m)

        # to make the dialog shrinkable
        self.setMinimumWidth(40)
        # self.setMaximumWidth(150)

        # set limits
        self.setMaximum(max_val)
        self.setMinimum(min_val)

        # set num decimals:
        self.setDecimals(prec)

        # trigger events only after [Enter] or Focus-loss, not on every key-stroke
        self.setKeyboardTracking(False)

        # for this use case:
        self.setAlignment(Qt.AlignRight)

        # fixed_font = QFont("Monospace")
        # fixed_font.setStyleHint(QFont.TypeWriter)
        # fixed_font.setPixelSize(12)
        # self.lineEdit().setFont(fixed_font)
        # or derive font:
        self.lineEdit().setFont(self.font())

        # default-value for single-step
        self.default_step = 1
        self.setSingleStep(self.default_step)

        self.setGroupSeparatorShown(True)

    def mousePressEvent(self, event:QMouseEvent):
        """derived to get other modifier-mechanism for click on Spin-Buttons with ctrl/shift-keys
            ControlModifier => 10 * default_step
            ShiftModifier => 100 * default_step
            ShiftModifier + ControlModifier => 1000 * default_step

        Args:
            event (QMouseEvent)
        """
        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)
        control = self.style().hitTestComplexControl(
            QStyle.CC_SpinBox, opt, event.pos(), self
        )
        if control in [QStyle.SC_SpinBoxUp, QStyle.SC_SpinBoxDown]:
            # the clicked control is one of the two SpinBox-Arrow-Buttons
            single_step = self.default_step
            # check_mods('s') is sufficient, because super().mousePressEvent will factorize 'c' automatically by 10
            if tools.MyTools.check_mods("s"):
                single_step *= 100
            self.setSingleStep(single_step)

        # trigger super-mousePressEvent with altered singleStep
        super().mousePressEvent(event)


class QDoubleNoSpinBox(QDoubleSpinBoxDefault):
    """QSpinBox without buttons
    => QLineEdit, which only accepts and shows numerical values like stationings or coordinates
    """
    # Rev. 2026-01-13
    def __init__(
        self,
        parent: QObject = None,
        min_val: float = -sys.float_info.max,
        max_val: float = sys.float_info.max,
        prec: int = 2,
    ):
        """Constructor

        Args:
            parent (QWidget): Parent-Object in Qt-Hierarchy
            min_val (float): minimum possible value, optional, defaults to -sys.float_info.max
            max_val (float): maximum possible value, optional, defaults to default sys.float_info.max
            prec (int): number of decimals, optional, defaults to 2
        """

        super().__init__(parent, min_val, max_val, prec)


        # for this use case: no Spin-Icons
        self.setButtonSymbols(self.NoButtons)

