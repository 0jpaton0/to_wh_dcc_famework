import os
from PySide6 import QtWidgets, QtUiTools, QtCore
from maya import OpenMayaUI as OpenMayaUI
from shiboken6 import wrapInstance

import scr
from scr.examples.qtuidialog import qt_ui_dialog_mod02
from scr.examples.qtuidialog import qt_ui_dialog_mod03


class QtUiDialog01(QtWidgets.QMainWindow):

    def __init__(self):
        maya_main = self.get_maya_main_window()
        super(QtUiDialog01, self).__init__(maya_main)
        ui_path = os.path.join(scr.framework_paths['examples_path'], 'qtuidialog\\', 'qt_ui_dialog.ui')
        self.ui = self.load_ui(ui_path, maya_main)
        self.ui.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.ui.btn_ok.clicked.connect(self.btn_ok_clicked)
        self.ui.btn_not_ok.clicked.connect(self.btn_not_ok_clicked)

        m2 = qt_ui_dialog_mod02.QtUiDialog02()
        m3 = qt_ui_dialog_mod03.QtUiDialog03()

    def eventFilter(self, obj, event):
        """
        catches close event

        :param obj: QObject
        :param event: QEvent
        :return:
        """

        if obj is self.ui and event.type() == QtCore.QEvent.Close:
            self.close_event()
            return True
        return False

    def run(self):
        """
        opens ui, probably called from user request in SG Tools drop down
        """

        self.ui.show()

    def close_event(self):
        """
        called from the eventFilter on close
        """
        print('\nclosing')

        self.ui.close()

    @staticmethod
    def get_maya_main_window():
        """
        gets the pointer to the window to use as ui

        :return: maya_main
        :rtype: python wrapper for a C++ object instantiated at a given memory address
        """
        main_window_pointer = OpenMayaUI.MQtUtil.mainWindow()
        maya_main = wrapInstance(int(main_window_pointer), QtWidgets.QWidget)
        return maya_main

    @staticmethod
    def load_ui(ui_path, parent=None):
        """
        loads the .ui file from a path

        :param ui_path: path to .ui file
        :type ui_path: str
        :param parent: this is a top level ui element with no parent
        :type parent: None
        :return: ui
        :rtype: QUiLoader
        """
        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(ui_path)
        uifile.open(QtCore.QFile.ReadOnly)
        ui = loader.load(uifile, parent)
        uifile.close()
        return ui

    def btn_ok_clicked(self):
        self.ui.lbl_text_field.setText('I am OK')

    def btn_not_ok_clicked(self):
        self.ui.lbl_text_field.setText('I am not OK')