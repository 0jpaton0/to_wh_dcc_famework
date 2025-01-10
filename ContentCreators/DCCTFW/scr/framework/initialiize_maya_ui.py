import pathlib
import glob
import os
import json
import logging

from PySide6 import QtWidgets
from shiboken6 import wrapInstance
import maya.OpenMayaUI as OpenMaya
import maya.mel as mel
import maya.cmds as cmds

import scr
from scr import tests
from scr.framework.dialogs import project_data_ui

logger = logging.getLogger(scr.logger_name)


class ShelfData:
    name = ''
    import_line = ''
    initialize_line = ''
    run_line = ''
    icon = ''


class ManageToolShelf(object):
    def __init__(self):
        self.current_win_path = pathlib.Path(__file__).resolve().parent.parent.parent
        self.path_str = self.current_win_path.__str__()
        self.icon_path = self.path_str + '\\icons'

        self.json_path = scr.framework_paths['json_path']
        self.json_find_string = 'DCCF shelf'
        self.shelf_items = []
        self.shelf_name = 'DCCF'
        self.shelf = None

        self.run()

    def run(self):
        # icons = self.get_icons()
        self.delete_existing_shelf()
        self.get_shelf_data_from_json()
        self.create_shelf()

    def delete_existing_shelf(self):
        """
        checks to see if there is an existing shlf and it there is deletes it
        """
        if cmds.shelfLayout(self.shelf_name, exists=True):
            cmds.deleteUI(self.shelf_name, layout=True)

    def get_shelf_data_from_json(self):
        """
        loads project jason file and populates ShelfData() with project data to be used
        by the framework
        """

        try:
            f = open(self.json_path, 'r')
            shelf_data = json.load(f)
        except Exception as Argument:
            logger.critical('Failed to load jason project file...: {}'.format(Argument))

        for data in shelf_data[self.json_find_string]:
            shelf_data = ShelfData()
            shelf_data.name = data['name']
            shelf_data.import_line = data['import']
            shelf_data.initialize_line = data['initialize']
            shelf_data.run_line = data['run']
            shelf_data.icon_line = data['icon']

            self.shelf_items.append(shelf_data)

    def create_shelf(self):
        main_shelf = mel.eval('$tempMelVar=$gShelfTopLevel')
        self.shelf = cmds.shelfLayout(self.shelf_name, p=main_shelf)

        for item in self.shelf_items:
            a_icon_path = self.icon_path + '\\' + item.icon_line + '.png'

            if os.path.exists(a_icon_path):
                command = item.import_line + '\n' + item.initialize_line + '\n' + item.run_line
                cmds.shelfButton(style='iconAndTextVertical', image1=a_icon_path, sourceType='python',
                                 command=command)

        cmds.setParent('..')

    def get_icons(self):
        os.chdir(self.icon_path)
        icons = []
        for f in glob.glob("*.*"):
            icons.append(pathlib.Path(f).stem)

        return icons


class BarData:
    name = ''
    label = ''
    action = ''


main_window = None
main_menu_bar = None


class LogMap:
    def __init__(self, name, level, action):
        self.name = name
        self.level = level
        self.action = action

    def __str__(self):
        return'name :: {}\nlevel :: {}\naction :: {}'.format(self.name, self.level, self.action)


class ManageToolBar(object):
    def __init__(self):
        self.long = int
        self.current_log_level = scr.default_log_level
        self.unittest_out = scr.framework_paths['unittest_path'] + '\\tests.log'

        # contains LogMap classes that define dropdown menu actions
        self.actions = []

        # menu action in case we need them later
        self.debug_action = None
        self.info_action = None
        self.warning_action = None
        self.error_action = None
        self.critical_action = None

        self.initialize_bar_widgets()
        self.set_log_level_to_default()

    def initialize_action(self, name, level, action):
        action.setCheckable(True)
        # logging level is set in scr.__init__
        if scr.default_log_level == level:
            action.setChecked(True)
        else:
            action.setChecked(False)
        self.actions.append(LogMap(name, level, action))

    def initialize_bar_widgets(self):
        # get maya  menu bar
        menu_bar = self.get_main_menu_bar()

        # Create a menu called "File"
        file_menu = QtWidgets.QMenu('DCCF')
        file_menu_debug = QtWidgets.QMenu('Debug')
        file_menu_support = QtWidgets.QMenu('Support')
        file_menu_project = QtWidgets.QMenu('Project')
        file_menu.addMenu(file_menu_debug)
        file_menu.addMenu(file_menu_support)
        file_menu.addMenu(file_menu_project)
        file_menu_debug.addAction('Unit tests', self.run_unittests)
        file_menu_support.addAction('Email Support', self.support_email)
        file_menu_project.addAction('Project data', self.open_project_data)

        logging_menu = QtWidgets.QMenu('Set Log level')
        self.debug_action = logging_menu.addAction('debug', lambda: self.update_log_level(10))
        self.initialize_action('debug', 10, self.debug_action)

        self.info_action = logging_menu.addAction('info', lambda: self.update_log_level(20))
        self.initialize_action('info', 20, self.info_action)

        self.warning_action = logging_menu.addAction('warning', lambda: self.update_log_level(30))
        self.initialize_action('warning', 30, self.warning_action)

        self.error_action = logging_menu.addAction('error', lambda: self.update_log_level(40))
        self.initialize_action('error', 40, self.error_action)

        self.critical_action = logging_menu.addAction('critical', lambda: self.update_log_level(50))
        self.initialize_action('critical', 50, self.critical_action)

        file_menu_debug.addMenu(logging_menu)
        menu_bar.addMenu(file_menu)

    def run_unittests(self):
        cmds.scriptEditorInfo(historyFilename=self.unittest_out, writeHistory=True)
        tests.run_unittests()
        # stop output capture
        cmds.scriptEditorInfo(writeHistory=False)

    def support_email(self):
        print('Support triggered')

        # no support for you!

    @staticmethod
    def open_project_data():
        project_data_ui.ProjectDataMayaUI()


    def invert_selection(self):
        print('invert_selection :: {}'.format(self.current_log_level))

        for action in self.actions:
            if action.level != self.current_log_level:
                action.action.setChecked(False)
            else:
                action.action.setChecked(True)

    def update_log_level(self, new_level=0):
        from scr import logger as logger

        level_name = ''
        match new_level:
            case 10:
                level_name = 'Debug'
                self.debug_action.checked = True
                self.current_log_level = 10
                self.invert_selection()
            case 20:
                level_name = 'Info'
                self.info_action.checked = True
                self.current_log_level = 20
                self.invert_selection()
            case 30:
                level_name = 'Warning'
                self.warning_action.checked = True
                self.current_log_level = 30
                self.invert_selection()
            case 40:
                level_name = 'Error'
                self.error_action.checked = True
                self.current_log_level = 40
                self.invert_selection()
            case 50:
                level_name = 'Critical'
                self.critical_action.checked = True
                self.current_log_level = 50
                self.invert_selection()

        if scr.get_logger_level() != new_level:
            logger.info('<Info> Logging level updated to {}'.format(level_name))
            scr.set_logger_level(new_level)
        else:
            logger.info('<Info> Logging already set to {}'.format(level_name))

    def get_main_window(self):
        """
        Gets the Maya main window widget.
        Returns:
            (QWidget): Maya main window.
        """
        global main_window

        if main_window:
            return main_window

        main_window_ptr = OpenMaya.MQtUtil.mainWindow()
        main_window = wrapInstance(self.long(main_window_ptr), QtWidgets.QWidget)
        return main_window

    def get_main_menu_bar(self):
        """
        Gets the Maya main menu bar as a QMenuBar
        Returns:
            (QtWidgets.QMenuBar): The main menu bar for Maya.
        """
        global main_menu_bar

        if main_menu_bar:
            return main_menu_bar

        main_menu_bar = self.get_main_window().findChild(QtWidgets.QMenuBar, '')
        return main_menu_bar

    def set_log_level_to_default(self):
        scr.set_logger_level(scr.default_log_level)
