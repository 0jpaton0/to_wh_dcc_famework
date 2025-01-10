import os
from PySide6 import QtWidgets, QtUiTools, QtCore
from shiboken6 import wrapInstance

import scr
from maya import OpenMayaUI as OpenMayaUI


class ProjectDataMayaUI(QtWidgets.QMainWindow):

    def __init__(self):
        maya_main = self.get_maya_main_window()
        super(ProjectDataMayaUI, self).__init__(maya_main)

        ui_path = os.path.join(scr.framework_paths['site-packages_path'], 'ccfw_project_data', 'project_data.ui')
        
        self.ui = self.load_ui(ui_path, maya_main)
        self.ui.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.project_data = scr.project_data
        urlLink = "<a href=\"http://www.google.com\">'Project Docs'</a>"

        self.welcome_text = 'Welcome {} team member!'.format(self.project_data.name)
        self.news_text = 'News from {} - {}'.format(self.project_data.news, self.project_data.news_description)
        self.vacation_text = 'Next vacation is {} and will be on {}'.format(self.project_data.vacation_description, self.project_data.vacation)
        self.docs_text = 'Please find {} docs here :\n {}'.format(self.project_data.name, urlLink)
        self.updated_text = 'Last updated by {} on {}'.format(self.project_data.author, self.project_data.last_updated)

        self.run()

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

        self.populate_labels()
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

    def populate_labels(self):
        self.ui.lab_welcome.setText('{}'.format(self.welcome_text))
        self.ui.label_news.setText('{}'.format(self.news_text))
        self.ui.lab_vacation.setText('{}'.format(self.vacation_text))
        self.ui.label_docs.setText('{}'.format(self.docs_text))
        self.ui.label_updated.setText('{}'.format(self.updated_text))

