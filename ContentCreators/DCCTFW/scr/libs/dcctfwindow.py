import os
from shiboken6 import wrapInstance
import maya.OpenMayaUI as OpenMayaUI
from PySide6 import QtWidgets, QtUiTools, QtCore


class DCCFWindow(QtWidgets.QMainWindow):

    def __init__(self, ui_path):
        maya_main = self.get_maya_main_window()
        super(DCCFWindow, self).__init__(maya_main)

        self.ui_path = ui_path

        ui_path = os.path.join(self.ui_dir,
                               self.ui_file)
        self.ui = self.load_ui(ui_path, maya_main)
        self.ui.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

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

    def show(self):

        if self.ui is not None:
            self.ui.show()

    def hide(self):

        if self.ui is not None:
            self.ui.hide()

    @property
    def is_visible(self):

        return self.ui is not None and self.ui.isVisible()


class TestUI(DCCFWindow):

    def run(self):
        self.show()

print('here1')
t = TestUI('C:\\stuff\\code\\python\\packages\\DCCTFW\\scr\\tests\\testtool01\\test_tool.ui')
print(dir(t))
print('here2')
