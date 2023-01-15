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
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QFrame


class VLineWidget(QFrame):
    def __init__(self,line_width: float, line_color: str, parent=None):
        super().__init__(parent)
        self.setLineWidth(line_width)
        #self.setMidLineWidth(line_width)
        self.setPalette(QPalette(QColor(line_color)))
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)