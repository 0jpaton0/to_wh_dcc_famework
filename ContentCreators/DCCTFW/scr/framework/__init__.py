"""
set up units
set up security
set up shelfs
set up project specfic option like export
"""

from PySide6.QtWidgets import QTreeWidgetItemIterator
from PySide6 import QtWidgets
import os

import maya.cmds as cmds

import scr
from scr import project_data
from . import initialiize_maya_ui
from . import initialize_maya


ManageToolShelf = initialiize_maya_ui.ManageToolShelf()
ManageToolBar = initialiize_maya_ui.ManageToolBar()


class SaveFiles(object):

    def __init__(self):
        pass

    def query_save_scene_on_export(self):
        save = cmds.confirmDialog(title='Confirm', message='Would you like the scene file to be saved?',
                                button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')

        if save:
            self.save_scene()

    def save_scene(self):
        file_path = cmds.sceneName()

        if os.access(file_path, os.W_OK):
            cmds.saveFile()


class ToolHelpers(QtWidgets.QMainWindow):

    def __init__(self):
        self.project_path = scr.framework_paths['project_path']

    def get_relative_path(self, path):
        '''
        gets a relative path based on project.path

        @param path: path
        @type path: str
        @return: relative path based on project.path
        @rtype:  str
        '''
        # Project Trunk and path are the same so path == relative path
        if path == self.project_path:
            return path
        elif self.project_path:
            if os.path.commonprefix([path, self.project_path]) == self.project_path:
                try:
                    relative_path = os.path.relpath(path, self.project_path)
                    return relative_path
                except Exception as e:
                    print('Not a relative path {0}'.format(e))

        if os.path.isdir(path):
            return path

    @staticmethod
    def is_group(node):
        """
        determines if node arg is of type 'group'.

        :param node: selected 'node' from maya scene
        :type node: probably a dag object
        :return: bool
        :rtype: bool
        """

        try:
            node.getTransform()
            return False
        except:
            return True

    @staticmethod
    def get_uuid(name):
        """
        gets uuid from node str

        :param name: name
        :type name: str (name of dag node)
        :return uuid: unique number associated with dag object
        :rtype uuid: uuid
        """

        import maya.cmds as cmds
        uuid = cmds.ls(name, uuid=True)[0]

        return uuid

    def get_expand_items(self, tree):
        """
        gets a list of items whose items have been expanded

        :return: expanded_list
        :rtype: list of QTreeWidgetItems
        """

        if tree is not None:
            expanded_list = []

            # get_tree_from_tab fails to return the correct tree after being
            item_count = tree.topLevelItemCount()
            for i in range(item_count):
                current_item = tree.topLevelItem(i)
                if current_item.isExpanded():
                    expanded_list.append(current_item.text(0))

            return expanded_list

    def set_expand_items(self, tree, expanded_list):
        """
        takes a list of tree items and expand so you can see sub items

        :param expanded_list: tree items that have been expanded
        :type expanded_list: list of QTreeWidgetItems
        """

        if tree is not None:
            item_count = tree.topLevelItemCount()
            for i in range(item_count):
                current_item = tree.topLevelItem(i)
                test = expanded_list.count(str(current_item.text(0)))
                if test != 0:
                    current_item.setExpanded(True)

    def get_tree_item_from_name(self, name, tree):
        """
        get tree model item by its name

        :param name: name of item to retrieve
        :param tree: ui tree
        :return:
        """
        print('name :: {}'.format(name))

        items = []
        iterator = QTreeWidgetItemIterator(tree)
        print('iterator :: {}'.format(iterator))
        while iterator.value():
            item = iterator.value()
            print('item.text(0) :: {}'.format(item.text(0)))
            if item.text(0) in name:
                print('appending :: {}'.format(item.text(0)))
                items.append(item)

            iterator += 1

        return items
