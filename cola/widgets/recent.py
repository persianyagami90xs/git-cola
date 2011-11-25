from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import SIGNAL

import cola
from cola import gitcmds
from cola import qtutils
from cola import signals
from cola.widgets import defs
from cola.widgets.browse import GitTreeWidget
from cola.widgets.browse import GitFileTreeModel
from cola.views import standard


def browse_recent():
    parent = qtutils.active_window()
    dialog = RecentFileDialog(parent)
    dialog.resize(parent.width(), min(parent.height(), 420))
    dialog.show()


class UpdateFileListThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.count = 0

    def run(self):
        ref = 'HEAD~%d' % self.count
        filenames = gitcmds.diff_index_filenames(ref)
        self.emit(SIGNAL('filenames'), filenames)


class RecentFileDialog(standard.Dialog):
    def __init__(self, parent):
        standard.Dialog.__init__(self, parent)
        self.setWindowTitle(self.tr('Recently Modified Files'))
        self.setWindowModality(QtCore.Qt.WindowModal)

        self.update_thread = UpdateFileListThread()

        self.count = QtGui.QSpinBox()
        self.count.setMinimum(0)
        self.count.setMaximum(10000)
        self.count.setValue(0)
        self.count.setSuffix(self.tr(' commits ago'))

        self.count_label = QtGui.QLabel()
        self.count_label.setText(self.tr('Showing changes since'))

        self.refresh_button = QtGui.QPushButton()
        self.refresh_button.setText('Refresh')
        self.refresh_button.setIcon(qtutils.reload_icon())
        self.refresh_button.setEnabled(False)

        self.tree = GitTreeWidget(None, parent=self)
        self.tree_model = GitFileTreeModel(self)
        self.tree.setModel(self.tree_model)

        self.expand_button = QtGui.QPushButton()
        self.expand_button.setText('Expand')
        self.expand_button.setIcon(qtutils.open_icon())

        self.collapse_button = QtGui.QPushButton()
        self.collapse_button.setText('Collapse')
        self.collapse_button.setIcon(qtutils.dir_close_icon())

        self.edit_button = QtGui.QPushButton()
        self.edit_button.setText('Edit')
        self.edit_button.setIcon(qtutils.apply_icon())
        self.edit_button.setDefault(True)
        self.edit_button.setEnabled(False)

        self.close_button = QtGui.QPushButton()
        self.close_button.setText('Close')

        toplayout = QtGui.QHBoxLayout()
        toplayout.setMargin(0)
        toplayout.setSpacing(defs.spacing)
        toplayout.addWidget(self.count_label)
        toplayout.addWidget(self.count)
        toplayout.addStretch()
        toplayout.addWidget(self.refresh_button)

        btnlayout = QtGui.QHBoxLayout()
        btnlayout.setMargin(0)
        btnlayout.setSpacing(defs.spacing)
        btnlayout.addWidget(self.expand_button)
        btnlayout.addWidget(self.collapse_button)
        btnlayout.addStretch()
        btnlayout.addWidget(self.edit_button)
        btnlayout.addWidget(self.close_button)

        layout = QtGui.QVBoxLayout()
        layout.setMargin(defs.margin)
        layout.setSpacing(defs.spacing)
        layout.addLayout(toplayout)
        layout.addWidget(self.tree)
        layout.addLayout(btnlayout)
        self.setLayout(layout)

        self.connect(self.tree, SIGNAL('selectionChanged()'),
                     self.selection_changed)

        self.connect(self.tree, SIGNAL('path_chosen'), self.edit_file)

        self.connect(self.count, SIGNAL('valueChanged(int)'),
                     self.count_changed)

        self.connect(self.refresh_button, SIGNAL('clicked()'), self.refresh)

        self.connect(self.update_thread, SIGNAL('filenames'),
                     self.set_filenames)

        self.connect(self.expand_button, SIGNAL('clicked()'),
                     self.tree.expandAll)

        self.connect(self.collapse_button, SIGNAL('clicked()'),
                     self.tree.collapseAll)

        self.connect(self.close_button, SIGNAL('clicked()'), self.accept)
        self.connect(self.edit_button, SIGNAL('clicked()'), self.edit_selected)

        qtutils.add_action(self, 'Refresh', self.refresh, 'Ctrl+R')

        self.update_thread.count = 0
        self.update_thread.start()

    def edit_selected(self):
        filenames = self.tree.selected_files()
        if not filenames:
            return
        self.edit_files(filenames)

    def edit_files(self, filenames):
        cola.notifier().broadcast(signals.edit, filenames)

    def edit_file(self, filename):
        self.edit_files([filename])

    def refresh(self):
        self.refresh_button.setEnabled(False)
        self.count.setEnabled(False)
        self.tree_model.clear()
        self.tree.setEnabled(False)

        self.update_thread.count = self.count.value()
        self.update_thread.start()

    def count_changed(self, value):
        self.refresh_button.setEnabled(True)

    def selection_changed(self):
        """Update actions based on the current selection"""
        filenames = self.tree.selected_files()
        self.edit_button.setEnabled(bool(filenames))

    def set_filenames(self, filenames):
        self.count.setEnabled(True)
        self.tree.setEnabled(True)
        self.tree_model.clear()
        self.tree_model.add_files(filenames)
        self.tree.expandAll()
        self.tree.setFocus(True)
