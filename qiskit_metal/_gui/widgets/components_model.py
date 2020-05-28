# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# Zlatko Minev

import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtWidgets import QTableView
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QPixmap, QIcon
from .._toolbox_qt import blend_colors
from .._handle_qt_messages import catch_exception_slot_pyqt
class ComponentsTableModel(QAbstractTableModel):

    """
    Design compoentns Table model that shows the names of the compoentns and
    their class names etc.

    MVC class
    See https://doc.qt.io/qt-5/qabstracttablemodel.html

    Can be accessed with
        t = gui.ui.tableComponents
        model = t.model()
        index = model.index(1,0)
        model.data(index)
    """
    __timer_interval = 500  # ms

    def __init__(self, gui, logger, parent=None, tableView: QTableView = None):
        super().__init__(parent=parent)
        self.logger = logger
        self.gui = gui
        self._tableView = tableView # the view used to preview this model, used to refresh
        self.columns = ['Name', 'QComponent class', 'QComponent module', 'Build status']
        self._row_count = -1

        self._create_timer()

    @property
    def design(self):
        return self.gui.design

    def _create_timer(self):
        """
        Refresh the model number of rows, etc. there must be a smarter way?
        """
        self._timer = QtCore.QTimer(self)
        self._timer.start(self.__timer_interval)
        self._timer.timeout.connect(self.refresh_auto)

    def refresh(self):
        """Force refresh.   Completly rebuild the model."""
        self.modelReset.emit()

    def refresh_auto(self):
        """
        Update row count etc.
        """
        # We could not do if the widget is hidden - TODO: speed performace?

        # TODO: This should probably just be on a global timer for all changes detect
        # and then update all accordingly
        new_count = self.rowCount()

        # if the number of rows have changed
        if self._row_count != new_count:
            #self.logger.info('Number of components changed')

            # When a model is reset it should be considered that all
            # information previously retrieved from it is invalid.
            # This includes but is not limited to the rowCount() and
            # columnCount(), flags(), data retrieved through data(), and roleNames().
            # This will loose the current selection.
            # TODO: This seems overkill to just change the total number of rows?
            self.modelReset.emit()

            self._row_count = new_count
            self._tableView.resizeColumnsToContents()

    def rowCount(self, parent: QModelIndex = None):
        if self.design:  # should we jsut enforce this
            return int(len(self.design.components))
        else:
            return 0

    def columnCount(self, parent: QModelIndex = None):
        return len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """ Set the headers to be displayed. """

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self.columns):
                    return self.columns[section]

        elif role == Qt.FontRole:
            if section == 0:
                font = QFont()
                font.setBold(True)
                return font

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're
            implementing this function just to see how it's done, as we
            manually adjust each tableView to have NoEditTriggers.
        """
        # https://doc.qt.io/qt-5/qt.html#ItemFlag-enum

        if not index.isValid():
            return Qt.ItemIsEnabled

        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                                   Qt.ItemIsSelectable )#| Qt.ToolTip)  # ItemIsEditable

    # @catch_exception_slot_pyqt()
    def data(self, index: QModelIndex, role:int = Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
            returning data, return None (PySide equivalent of QT's
            "invalid QVariant").
        """

        if not index.isValid() or not self.design:
            return

        component_name = list(self.design.components.keys())[index.row()]

        if role == Qt.DisplayRole:

            if index.column() == 0:
                return component_name
            elif index.column() == 1:
                return self.design.components[component_name].__class__.__name__
            elif index.column() == 2:
                return self.design.components[component_name].__class__.__module__
            elif index.column() == 3:
                return self.design.components[component_name].status

        # The font used for items rendered with the default delegate. (QFont)
        elif role == Qt.FontRole:
            if index.column() == 0:
                font = QFont()
                font.setBold(True)
                return font

        elif role == Qt.BackgroundRole:

            component = self.design.components[component_name]
            if component.status != 'good': # Did the component fail the build
                #    and index.column()==0:
                if not self._tableView:
                    return QBrush(QColor('#FF0000'))
                table = self._tableView
                color = table.palette().color(table.backgroundRole())
                color = blend_colors(color, QColor('#FF0000'), r=0.6)
                return QBrush(color)

        elif role == Qt.DecorationRole:

            if index.column() == 0:
                component = self.design.components[component_name]
                if component.status != 'good': # Did the component fail the build
                    return QIcon(":/basic/warning")

        elif role == Qt.ToolTipRole or role == Qt.StatusTipRole:
            component = self.design.components[component_name]
            text = f"""Component name= "{component.name}" instance of class "{component.__class__.__name__}" from module "{component.__class__.__module__}" """
            return text
