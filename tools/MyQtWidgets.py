import os
import re
from typing import Any, Callable
from PyQt5 import QtCore, QtGui, QtWidgets

from LinearReferencing.tools.MyDebugFunctions import debug_print
from LinearReferencing.tools.MyDebugFunctions import get_debug_pos as gdp


class GroupBoxProxyStyle(QtWidgets.QProxyStyle):
    """QProxyStyle to make QGroupbox expandable
    see:
    https://stackoverflow.com/questions/55977559/changing-qgroupbox-checkbox-visual-to-an-expander
    """

    def drawPrimitive(self, element, option, painter, widget):
        if element == QtWidgets.QStyle.PE_IndicatorCheckBox and isinstance(
                widget, QtWidgets.QGroupBox
        ):
            super().drawPrimitive(
                QtWidgets.QStyle.PE_IndicatorArrowDown
                if widget.isChecked()
                else QtWidgets.QStyle.PE_IndicatorArrowRight,
                option,
                painter,
                widget,
            )
        else:
            super().drawPrimitive(element, option, painter, widget)


class QTableWidgetItemCustomSort(QtWidgets.QTableWidgetItem):
    """Problem in QTableWidget:

    * normal items with item.text() are sorted alphabetical
    * "alphanumerical" items with item.setText(str(number)) are sorted alphabetical too, resulting orders like "100","2","3000","4"...
    * real numerical items (item = QTableWidgetItem(), item.setData(0,numeric_val)) are sorted numerical

    If You want to sort columns with text = '# 1' or '€ 25,99' or '$ 5.75' these would be sorted alphabetical too,
    but by using this delegate You can store the numerical value in data-model under a certain and this one is than used for sorting independent of the displayed value
    Another solution could be a Delegate for numerical Values to show these with "decorations" like currency-Symbols
    """

    def __init__(self, sort_role: int = 256):
        """constructor
        :param sort_role:under this role in item.data(...) the sort-values are stored
        """
        super().__init__()
        self.sort_role = sort_role

    def __lt__(self, other):
        """derived operator for custom sort
        :param self: current QTableWidgetItem
        :param other: the compared QTableWidgetItem
        """
        return (self.data(self.sort_role) < other.data(self.sort_role))


class QTableWidgetItemMultipleSort(QtWidgets.QTableWidgetItem):
    """Problem in QTableWidget:

    additionally to QTableWidgetItemCustomSort for sorting a column by multiple and mixed-type field-values

    Usage-Sample:
    sort line-segments by reference-id, measure-from and measure-to ascending
    No Problem in SQL:
    SORT BY ref_id asc, measure_from asc, measure_to asc

    Problem in QGis-Feature-Tables and/or Qt QTableWidgets
    normal sort is for exact one column and the displayed value

    Workaround in QGis could be a expression in a virtual field,
    which concatentates the formatted numerical values, so that the alphabetical sort of this string fits to the natural sort
    """

    # Rev. 2023-05-08

    def __init__(self, *sort_roles):
        """constructor
        :param sort_roles: integer values presumably in the application-specific range (beginning with UserRole = 256) referencing the keys of self.data(...)
        """
        super().__init__()

        self.sort_roles = sort_roles

    def __lt__(self, other) -> bool:
        """derived operator for the custom sort

        * iterates through the roles,
        * returns the first valuable __lt__,
        * continues as long as the self/other values for a role are equal
        * None-Value-Handling: "None" is allways assumed less then any value != "None"

        :param self: current QTableWidgetItem
        :param other: the compared QTableWidgetItem
        :returns bool: True, if "self is less than other"
        """
        for role in self.sort_roles:
            self_val = self.data(role)
            other_val = other.data(role)

            try:
                if self_val is None and other_val is not None:
                    return True
                elif self_val is not None and other_val is None:
                    return False
                elif self_val is None and other_val is None:
                    pass
                else:
                    if self_val < other_val:
                        return True
                    elif self_val > other_val:
                        return False

            except Exception as e:
                # if self.data(role) is not None and other.data(role) is not None:
                # "'<' not supported between instances of 'NoneType' and 'NoneType'"
                return True

        # emergency exit: if data for all rows in self and other is null
        return True


class LambdaDelegate(QtWidgets.QStyledItemDelegate):
    """convert the display-value with function,
    f. e. decorate numerical values with currency-symbols or units, add padding blanks to not overlap cellWidgets...

    * Sample 1: "normal" Function

    .. code-block:: text

    def stringify_fn(val):
        return " " * 15 + "# " + str(val)
    self.delegate = LambdaDelegate(stringify_fn)
    self.qtw_table.setItemDelegateForColumn(0,self.delegate)


    * Sample 2: Lambda-Function

    .. code-block:: text

    self.delegate = LambdaDelegate(lambda val: " " * 15 + "# " + str(val))
    self.qtw_table.setItemDelegateForColumn(1,self.delegate)


    .. note::

    **Important:
    the delegate-function must allways be stored as self.xxx-property, else Python/Qt/QGis-Crash...**

    Hint: doesn't affect the edit-possibilities if setEditTriggers allows editing. The editable content in the LineEdit have no decoration
    """

    def __init__(self, stringify_fn: Callable, parent=None):
        """initialize, precalculates self._padding
        :param stringify_fn: function which takes one argument (value in model) and returns it modified
        :param parent: Qt-Hierarchy
        """
        super().__init__(parent)
        self.stringify_fn = stringify_fn

    def displayText(self, val, locale) -> str:
        """reimplemented, returns the result of the stringify_fn called with val from model
        :param val: item.text() or item.data(0)
        :param locale: PyQt5.QtCore.QLocale ➜ "converts between numbers and their string representations in various languages" ➜ not used
        """
        return self.stringify_fn(val)

    # no need to derive sizeHint, because the size is calculated for the stringified result
    # def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QModelIndex) -> QtCore.QSize:
    #     """Reimplemented: Returns the size needed by the delegate to display the item specified by index, taking into account the style information provided by option.
    #     returns the sizeHint plus icon-widths"""
    #     print(option,index)
    #     super_size_hint = super().sizeHint(option, index)
    #     #super_size_hint.setWidth(super_size_hint.width() + self.get_icons_rect(option.rect).width())
    #     return super_size_hint


class QPushButtonColor(QtWidgets.QPushButton):
    """Pushbutton for color-Selection"""

    color_changed = QtCore.pyqtSignal(str)
    """own signal, emitted if dialog is closed, emitts color.name() ➜ color in HexRgb/HexArgb-String Format"""

    def __init__(self, text: str = '', color: str = None, support_alpha: bool = True, color_as_tooltip: bool = True,
                 color_as_text: bool = True, parent: QtCore.QObject = None):
        """constructor
        :param text: initial text on Button, see set_color(...color_as_text)
        :param color: initial color of the button
        :param support_alpha: colors and dialog with alpha-chanel-support (opacity, 0...256)
        :param color_as_tooltip: setting: use current color (Hex-Format) as Tooltip
        :param color_as_text: setting: use current color in Hex-Format as Button-Text
        :param parent: Parent-Object for Qt-Hierarchy
        """
        super().__init__(text, parent)

        self.color_as_tooltip = color_as_tooltip
        self.color_as_text = color_as_text
        self.support_alpha = support_alpha

        self.setAutoFillBackground(True)
        # without that only colored borders, presumably because of Sub-Widgets inside QPushButton with own palettes?
        self.setFlat(True)
        self.dialog = QtWidgets.QColorDialog()

        self.dialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, self.support_alpha)

        if color:
            self.set_color(color)

        if text:
            self.setText(text)

        self.pressed.connect(self.show_dialog)

    def clear(self):
        self.setText('')
        self.setToolTip('')
        plt = self.palette()
        plt.setColor(QtGui.QPalette.Button,
                     QtWidgets.QApplication.palette().color(QtGui.QPalette.Normal, QtGui.QPalette.Button))
        self.setPalette(plt)

    def set_color(self, color):
        """sets the color of the button
        :param color: (QColor-parseable) string (f.e. Hex-Format) or QColor
        """
        if isinstance(color, str):
            color = QtGui.QColor(color)

        plt = self.palette()
        plt.setColor(QtGui.QPalette.Button, color)
        self.setPalette(plt)

        self.dialog.setCurrentColor(color)

        if self.color_as_tooltip:
            if self.support_alpha:
                self.setToolTip(self.dialog.currentColor().name(QtGui.QColor.HexArgb))
            else:
                self.setToolTip(self.dialog.currentColor().name())

        if self.color_as_text:
            if self.support_alpha:
                self.setText(self.dialog.currentColor().name(QtGui.QColor.HexArgb))
            else:
                self.setText(self.dialog.currentColor().name())

    def show_dialog(self):
        """calls the dialog and applies the result to the button"""
        result = self.dialog.exec()
        if result:
            self.set_color(self.dialog.selectedColor())
            # emit own signal
            if self.support_alpha:
                self.color_changed.emit(self.dialog.selectedColor().name(QtGui.QColor.HexArgb))
            else:
                self.color_changed.emit(self.dialog.selectedColor().name())


class QSpinBoxStyle(QtWidgets.QProxyStyle):
    """custom style with larger (40px) and better klickable Spin-Buttons"""

    def subControlRect(self, control, opt, subControl, widget=None):
        rect = super().subControlRect(control, opt, subControl, widget)
        if control == QtWidgets.QStyle.CC_SpinBox:
            if subControl == QtWidgets.QStyle.SC_SpinBoxUp:
                rect.setTop(0)
                rect.setBottom(int(0.5 * opt.rect.height()))
                rect.setLeft(opt.rect.width() - 40)
                rect.setRight(opt.rect.width())
            elif subControl == QtWidgets.QStyle.SC_SpinBoxDown:
                rect.setTop(int(0.5 * opt.rect.height()))
                rect.setBottom(opt.rect.height())
                rect.setLeft(opt.rect.width() - 40)
                rect.setRight(opt.rect.width())
            elif subControl == QtWidgets.QStyle.SC_SpinBoxEditField:
                rect.setRight(opt.rect.width() - 40)
        return rect


class QSpinBoxStyleNm(QSpinBoxStyle):
    """custom style with larger (40px) and better klickable Spin-Buttons
    additional NoModifier for the Spin-Buttons, because another mechanism with ctrl, shift, ctrl + shift is implemented
    """

    def styleHint(self, hint, opt=None, widget=None, returnData=None):
        # print("styleHint",hint,opt,widget,returnData)
        if hint == 117:
            # 117 ➜ self.style().SH_SpinBox_StepModifier
            # Determines which Qt::KeyboardModifier increases the step rate of QAbstractSpinBox.
            return QtCore.Qt.NoModifier
        return super().styleHint(hint, opt, widget, returnData)


class QDoubleSpinBoxDefault(QtWidgets.QDoubleSpinBox):
    """QDoubleSpinBox to show float values, the up/down arrows larger than default-style (Fusion?)
    customized handling of keyboardModifiers,
    default: 10 * self.singleStep if ctrl-key is hold
    here: three variants with factor 10/100/1000
    customizable: modify self.default_step and/or self.mod_step_factors"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # per default only positive
        self.setRange(0, 999999999)

        self.setKeyboardTracking(False)
        self.setDecimals(1)
        self.setStyle(QSpinBoxStyleNm())

        # default-value for single-step
        self.default_step = 1

        # factor dependent on holded keyboardModifiers when clicking on the Spin-Buttons
        self.mod_step_factors = {'ctrl': 10, 'shift': 100, 'ctrl+shift': 1000}

        self.setSingleStep(self.default_step)

    def mousePressEvent(self, event):
        """derived to get other modifier-mechanism for click on Spin-Buttons with ctrl/shift-keys """
        opt = QtWidgets.QStyleOptionSpinBox()
        self.initStyleOption(opt)
        control = self.style().hitTestComplexControl(
            QtWidgets.QStyle.CC_SpinBox, opt, event.pos(), self
        )
        if control in [QtWidgets.QStyle.SC_SpinBoxUp, QtWidgets.QStyle.SC_SpinBoxDown]:
            step_factor = 1

            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                step_factor = self.mod_step_factors.get('ctrl',10)
            elif QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                step_factor = self.mod_step_factors.get('shift',100)
            elif QtWidgets.QApplication.keyboardModifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
                step_factor = self.mod_step_factors.get('ctrl+shift',1000)

            self.setSingleStep(step_factor * self.default_step)

        # only now the super-mousePressEvent with altered setSingleStep
        super().mousePressEvent(event)


class QDoubleSpinBoxPercent(QtWidgets.QDoubleSpinBox):
    """QDoubleSpinBox to show values in range 0...1 as percentage, same style as QDoubleSpinBoxDefault"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # visible range 0...100 %, internal range 0...1
        self.setRange(0, 100)
        # default: 1 (one click ➜ 100%) here 0.01 (one click ➜ 1%)
        self.setSingleStep(0.01)
        # for the internal range, 4 decimals 0.0001 == 0.01 %
        self.setDecimals(4)
        self.setKeyboardTracking(False)
        self.setStyle(QSpinBoxStyle())

    def textFromValue(self, value):
        """derived, returns internal value (range 0...1) as percent with 2 decimals"""
        return f"{(value * 100):0.2f}"

    def valueFromText(self, text: str) -> float:
        return float(text) / 100


class QComboBoxN(QtWidgets.QComboBox):
    """QtWidgets.QComboBox with multiple and sortable columns, uses QtWidgets.QTableView
    only for select, not for QtWidgets.QComboBox.setEditable(True)
    """

    # default width for resizeMode Interactive and Fixed, if not defined for a column via col_widths
    _default_col_width = 100

    def __init__(self,
                 parent: QtCore.QObject = None,
                 column_resize_mode: int = QtWidgets.QHeaderView.ResizeToContents,
                 show_template: str = '{0}',
                 min_row_height: int = 20,
                 default_row_height: int = 20,
                 max_row_height: int = 20,
                 view_minimal_width: int = 100,
                 col_widths: list = [],
                 show_horizontal_header: bool = True,
                 col_names: list = [],
                 show_vertical_header: bool = False,
                 row_names: list = [],
                 show_clear_button: bool = True,
                 append_index_col: bool = False,
                 enable_row_by_col_idx: int = 0,
                 show_grid: bool = False,
                 sorting_enabled: bool = True,
                 initial_sort_col_idx: int = 0,
                 initial_sort_order: int = QtCore.Qt.AscendingOrder,
                 word_wrap: bool = True,
                 elide_mode: int = QtCore.Qt.ElideRight,
                 icon_size: QtCore.QSize = QtCore.QSize(12, 12),
                 clear_button_icon: QtGui.QIcon = None
                 ):
        """ Constructor, long parameter-list with default-values for style and behaviour, consistent to current purposes (select layer and fields in QGis)
        :param parent: optional parent objekt in Qt-hierarchy
        :param column_resize_mode: see ResizeMode-enum :
            Interactive ➜ 0 cols can be resized by user, initial size as defined in col_widths
            Stretch ➜ 1 cols will be stretched to the width of the QtWidgets.QComboBox ➜ width of QtWidgets.QTableView == width of QCombBox
            Fixed ➜ 2 fix defined widths, width of QtWidgets.QTableView = sum(col_widths)
            ResizeToContents ➜ 3 cols will be stretched to their contents ➜ width of QtWidgets.QTableView = sum(calculated col_widths) + x
        :param show_template: template in f-string-style for display multiple columns in QtWidgets.QComboBox
        defaults '{0}' ➜ Standard, QtCore.Qt.UserRole-contents of the first column, parsed with regular expression and results in self._show_col_idzs
        :param min_row_height: applied to setMinimumSectionSize must fit to widgets/font...
        :param default_row_height: applied to setDefaultSectionSize
        :param max_row_height: applied to setMaximumSectionSize if these values are identical, then setSectionResizeMode(QtWidgets.QHeaderView.Fixed), else QtWidgets.QHeaderView.Interactive
        :param view_minimal_width: *min*-width of DropDown-QtWidgets.QTableView, probably overruled by calculated width, that one depending on resize_mode

        :param col_widths: width of columns, only for resize_mode Interactive and Fixed,
            defaults to self._default_col_width, if the model has more cols then values in col_widths
        :param show_horizontal_header:
        :param col_names: Header-Column-Names, only visible if show_horizontal_header, will be applied to each model. If empty and show_horizontal_header: numerical Column-Headers
        :param show_vertical_header: Shows vertical header (normally == Row-Number), usefully for vertical resizing of the rows
        :param row_names: Row-Headers, only visible if show_vertical_header, will be applied to each model. If empty and show_vertical_header: numerical Row-Headers
        :param show_clear_button: Workaround
            - enable deselection (i.e. setCurrentIndex(-1)) by fake clearButton in self.lineEdit()
            - adds missing feature (or remove bug?) in QtWidgets.QComboBox: show nothing, if nothing selected
            Side-Effects:
            - sets a QtWidgets.QLineEdit (default-property self.lineEdit() but None, if QtWidgets.QComboBox is not editable)
            - self.lineEdit().setClearButtonEnabled(True)
            - manipulate the clicked-action of the clear-button
        :param append_index_col: appends a column to model with the original index, usefully if sorting_enabled,
            must be taken into account in col_names and col_widths
        :param enable_row_by_col_idx: rows of the QtWidgets.QTableView are user-selectable, if at least one item in that row is enabled,
            so every item in a row must be disabled, to make the whole row unselectable
        :param show_grid:
        :param sorting_enabled: sort table by header-click,
            caveat: if enabled, the QtWidgets.QTableView will be automatically sorted by the first column, disabled or empty Rows at last
        :param initial_sort_col_idx:
            only if sorting_enabled and initial_sort_order: sort QtWidgets.QTableView by this column
            if negative: order from behind
        :param initial_sort_order: see https://doc.qt.io/qt-5/qt.html#SortOrder-enum,
            QtCore.Qt.AscendingOrder ➜ 0
            QtCore.Qt.DescendingOrder ➜ 1
        :param word_wrap:
        :param elide_mode: see https://doc.qt.io/qt-5/qt.html#TextElideMode-enum
            QtCore.Qt.ElideLeft ➜ 0 QtCore.Qt.ElideRight ➜ 1 QtCore.Qt.ElideMiddle ➜ 2 QtCore.Qt.ElideNone ➜ 3
        :param icon_size: Applied to QtWidgets.QComboBox and QtWidgets.QTableView
        :param clear_button_icon: if show_clear_button: icon of the Clear-Button (other icons )
            if unset: QtWidgets.QApplication.instance().style().standardIcon(70)
            ➜ nice under linux, ugly with windows
        """
        super().__init__(parent)
        self.append_index_col = append_index_col
        self.enable_row_by_col_idx = enable_row_by_col_idx
        self.show_horizontal_header = show_horizontal_header
        self.col_names = col_names
        self.show_vertical_header = show_vertical_header
        self.row_names = row_names
        self.col_widths = col_widths
        self.sorting_enabled = sorting_enabled
        self.initial_sort_col_idx = initial_sort_col_idx
        self.initial_sort_order = initial_sort_order
        self.word_wrap = word_wrap
        self.view_minimal_width = view_minimal_width
        self.elide_mode = elide_mode
        self.show_grid = show_grid
        self.min_row_height = min_row_height
        self.default_row_height = default_row_height
        self.max_row_height = max_row_height
        self.icon_size = icon_size
        self.column_resize_mode = column_resize_mode

        # "Fixed" requires explicit set col_widths
        if self.column_resize_mode == QtWidgets.QHeaderView.Fixed and self.model().columnCount() != len(
                self.col_widths):
            # stretch ➜ "automatically resize the section to fill the available space. The size cannot be changed by the user or programmatically"
            self.column_resize_mode = QtWidgets.QHeaderView.Stretch

        self.show_template = show_template

        self.show_clear_button = show_clear_button

        self.clear_button_icon = clear_button_icon

        # at runtime (apply_settings): filled from self.show_template via RegExp
        self._show_col_idzs = {}

        self.setView(QtWidgets.QTableView(self))

    def paintEvent(self, event):
        """Reimplemented and enhanced:

            - show multiple columns
            - enable (faked) clearButton
            - adds missing feature (or remove bug?) in QtWidgets.QComboBox: show nothing, if nothing selected (self.currentIndex() == -1)
        """
        option = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(option)
        painter = QtWidgets.QStylePainter(self)
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, option)
        if self.currentIndex() > -1:
            option_text = self.show_template
            for show_col_idx in self._show_col_idzs:
                if show_col_idx >= 0 and show_col_idx < self.model().columnCount():
                    show_col_wildcard = self._show_col_idzs[show_col_idx]
                    item_idx = self.model().index(self.currentIndex(), show_col_idx)
                    show_col_value = str(self.model().itemData(item_idx).get(0, ''))
                    option_text = option_text.replace(show_col_wildcard, show_col_value)

            if self.show_clear_button:
                self.lineEdit().setText(option_text)
                # avoid disturbing blinking cursor...
                self.lineEdit().clearFocus()
                self.lineEdit().show()

            else:
                option.currentText = option_text

            painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, option)
        else:
            if self.lineEdit():
                # avoid empty lineEdit()
                painter.end()
                self.lineEdit().hide()

    def apply_settings(self):
        """all settings can be defined on init, but also at runtime.
        Because of latter the settings must be applied at runtime after the data ist applied, see set_model()
        Called with every set_model()-call.
        Can/Must be called independently (without set_model), if the settings should have changed"""

        # in: show_template = '{0} #{1} [{2}]'
        # out: {0: '{0}', 1: '{1}', 2: '{2}'}
        show_col_wildcards = re.findall("\{[\d+]\}", self.show_template)
        for show_col_wildcard in show_col_wildcards:
            idx = int(re.sub("[^0-9]", "", show_col_wildcard))
            self._show_col_idzs[idx] = show_col_wildcard

        # row-wise select
        self.view().setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # some visual effects
        self.view().setShowGrid(self.show_grid)
        self.view().setSortingEnabled(self.sorting_enabled)
        self.view().setWordWrap(self.word_wrap)
        self.view().setTextElideMode(self.elide_mode)

        # size for Icons in QtWidgets.QComboBox...
        self.setIconSize(self.icon_size)
        # ...and QtWidgets.QTableView
        self.view().setIconSize(self.icon_size)

        if self.show_horizontal_header:
            self.view().horizontalHeader().show()
            if self.col_names:
                self.model().setHorizontalHeaderLabels(self.col_names)
        else:
            self.view().horizontalHeader().hide()

        if self.show_vertical_header:
            self.view().verticalHeader().show()
            if self.row_names:
                self.model().setVerticalHeaderLabels(self.row_names)
        else:
            self.view().verticalHeader().hide()

        if self.sorting_enabled and self.initial_sort_col_idx is not None and self.initial_sort_order is not None:
            sort_col_idx = self.initial_sort_col_idx

            if sort_col_idx < 0:
                sort_col_idx = self.model().columnCount() + sort_col_idx

            if sort_col_idx <= self.model().columnCount():
                # setSortingEnabled triggers automatically sort by first column, which is not allways wanted...
                self.view().sortByColumn(sort_col_idx, self.initial_sort_order)

        self.view().verticalHeader().setMinimumSectionSize(self.min_row_height)
        self.view().verticalHeader().setMaximumSectionSize(self.max_row_height)
        self.view().verticalHeader().setDefaultSectionSize(self.default_row_height)

        if self.min_row_height == self.max_row_height == self.default_row_height:
            self.view().verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        else:
            self.view().verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

        # type(view.horizontalHeader()) == PyQt5.QtWidgets.QtWidgets.QHeaderView,
        # setSectionResizeMode(...) ➜ Interactive/Fixed/Stretch/ResizeToContents see #ResizeMode-enum

        # calculate total width of QTableWidget
        if self.column_resize_mode == QtWidgets.QHeaderView.Fixed:
            cc = 0
            calc_width = 0
            for col_width in self.col_widths:
                self.view().setColumnWidth(cc, col_width)
                calc_width += col_width
                cc += 1
        else:
            self.view().horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.view().resizeColumnsToContents()
            calc_width = self.view().horizontalHeader().length()

        # assume vertical scrolllbar is needed, else a bit to wide
        calc_width += 2 * self.view().frameWidth() + QtWidgets.QApplication.style().pixelMetric(
            QtWidgets.QStyle.PM_ScrollBarExtent)

        #  take view_minimal_width if larger
        calc_width = max(self.view_minimal_width, calc_width)

        self.view().setFixedWidth(calc_width)

        self.view().horizontalHeader().setSectionResizeMode(self.column_resize_mode)
        self.view().horizontalHeader().setStretchLastSection(True)

        # Workaround: Fake ClearButton, use self.lineEdit() with clearButtonEnabled and manipulate its actions
        if self.show_clear_button:
            self.setLineEdit(QtWidgets.QLineEdit())
            self.lineEdit().setClearButtonEnabled(True)
            self.lineEdit().setFont(self.font())
            clear_button = self.lineEdit().findChild(QtWidgets.QToolButton)
            if clear_button:
                clear_button.clicked.connect(lambda: self.setCurrentIndex(-1))
                if self.clear_button_icon:
                    # default: QtWidgets.QApplication.instance().style().standardIcon(70)
                    clear_button.setIcon(self.clear_button_icon)


                # no effect inside QLineEdit...
                # clear_button.setIconSize(QtCore.QSize(8, 8))
                # self.lineEdit().setStyleSheet("QToolButton {width: 5px; height: 5px;}")
                # ugly: clear_button.setFixedSize(15,15)

    def set_model(self, in_model: QtGui.QStandardItemModel):
        """assign model (aka data) to this Widget,
        some model-side-effects (add special cols and rows)
        visual side-effects see apply_settings
        :param in_model:
        """
        # dont trigger any signals

        with QtCore.QSignalBlocker(self):

            if self.append_index_col:
                num_cols = in_model.columnCount()
                # letzte Spalte ergänzen
                for rc in range(in_model.rowCount()):
                    idx_item = QtGui.QStandardItem()
                    # no string because of integer-sorting
                    idx_item.setData(rc, 0)
                    # columnCount == index of new column
                    in_model.setItem(rc, num_cols, idx_item)

            if self.enable_row_by_col_idx is not None and self.enable_row_by_col_idx <= in_model.columnCount():
                for rc in range(in_model.rowCount()):
                    master_enable = in_model.item(rc, self.enable_row_by_col_idx).isEnabled()
                    for cc in range(in_model.columnCount()):
                        in_model.item(rc, cc).setEnabled(master_enable)

            self.setModel(in_model)

            self.apply_settings()
            self.setCurrentIndex(-1)

    def set_current_index(self, current_index: int):
        """select an item via setCurrentIndex but without triggering any signal/slot
        caveat: disabled features can also be selected with this method
        row_idx -1 ➜ select nothing
        :param row_idx: row-index in data-model
        """
        with QtCore.QSignalBlocker(self):
            self.setCurrentIndex(current_index)

    def clear_selection(self):
        """clears the current selection"""
        self.set_current_index(-1)

    def select_by_value(self, col_idx: int, role_idx: int, select_value: Any):
        """finds a row in model by value and selects the assigned option in QtWidgets.QComboBox rsp. QtWidgets.QTableView
        No selection-clear, if not item was found.
        :param col_idx: the index of the column of the data-model, whose data will be compared
        :param role_idx: the role in the items, whose data will be compared, see https://doc.qt.io/qt-5/qt.html#ItemDataRole-enum
        :param select_value: the compare-value
        """
        matching_items = self.get_matching_items(col_idx, role_idx, select_value)
        if matching_items:
            first_matching_item = matching_items.pop(0)
            self.set_current_index(first_matching_item.row())

    def get_matching_items(self, col_idx: int, role_idx: int, select_value: Any) -> list:
        """wrapper for https://doc.qt.io/qt-5/qabstractitemmodel.html#match:
        "Returns a list of indexes for the items in the column of the start index where data stored under the given role matches the specified value."
        how to compare: see https://doc.qt.io/qt-5/qt.html#MatchFlag-enum
        here: MatchExactly ➜ "Performs QVariant-based matching." ➜ "The QVariant class acts like a union for the most common Qt data types."
        :param col_idx: the index of the column of the data-model, whose data will be compared
        :param role_idx: the role in the items, whose data will be compared, see https://doc.qt.io/qt-5/qt.html#ItemDataRole-enum
        :param select_value: the compare-value
        :return: list of items
        """
        first_item_idx = self.model().index(0, col_idx)
        # param 4 "-1": limits num of matches, here -1 ➜ no  limit, return all matches
        matching_items = self.model().match(first_item_idx, role_idx, select_value, -1, QtCore.Qt.MatchExactly)

        return matching_items
