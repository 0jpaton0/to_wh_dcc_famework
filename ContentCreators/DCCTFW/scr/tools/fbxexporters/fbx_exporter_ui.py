import os
import maya.OpenMaya as OpenMaya
import pymel.core as pm
import maya.OpenMayaAnim as OpenMayaAnim
import random
import logging
import tempfile
from pathlib import Path

from PySide6 import QtWidgets, QtGui, QtUiTools, QtCore
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QTreeWidgetItemIterator
from maya import OpenMayaUI as OpenMayaUI
from shiboken6 import wrapInstance

import scr
from scr.tools.fbxexporters import fbx_exporter_export
from scr.tools.fbxexporters import fbx_exporter_data
from scr.tools.fbxexporters import fbx_exporter_ui
from scr.tools.fbxexporters import Identifiers
from scr.tools.fbxexporters import Debug
from scr.tools.fbxexporters import ExportOptions
from scr.tools.fbxexporters import ActorLayerData
from scr.tools.fbxexporters import AnimationData
from scr.tools.fbxexporters import RigModelData
from scr.tools.fbxexporters import RigLayerData
from scr.tools.fbxexporters import ModelData
from scr.tools.fbxexporters import LayerData
from scr.tools.fbxexporters import UserOptionsData
from scr.framework.dialogs import dialogs


class FbxCharacterExporterUI(QtWidgets.QMainWindow):

    def __init__(self):
        maya_main = self.get_maya_main_window()
        super(FbxCharacterExporterUI, self).__init__(maya_main)

        ui_path = os.path.join(scr.framework_paths['tool_path'], 'fbxexporters', 'fbx_character_exporter.ui')

        self.ui = self.load_ui(ui_path, maya_main)
        self.ui.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # initialize class vars
        self.logger = logging.getLogger(scr.logger_name)
        self.ExportData = fbx_exporter_data.ExporterData
        self.FbxExporter = scr.framework.ToolHelpers()
        self.Exporter = fbx_exporter_export.Exporter
        self.ExportOptions = ExportOptions
        self.framework_paths = scr.framework_paths['project_path']
        self.Browsers = dialogs.Browsers()
        self.Save = scr.framework.SaveFiles()
        self.Project = scr.project_data

        self.tool_name = 'FBX Exporter'
        self.tool_version = '3.0'

        # self.ui.setWindowTitle(self.tool_name + self.Project.name)
        self.item_widget_size = QSize(-1, 20)

        # rig anim vars
        self.actors_layers = []
        self.rig_layers = []
        self.old_anim_name = None
        self.old_rig_name = None
        self.rig_column_double_clicked = None
        self.anim_column_double_clicked = None
        self.anim_column_clicked = None

        # model vars
        self.model_layers = []
        self.user_options = UserOptionsData()
        self.old_layer = None
        self.model_column_double_clicked = None

        # ui events
        # main menu buttons
        self.ui.btn_export_selected.clicked.connect(self.btn_export_selected_clicked)
        self.ui.btn_select_selected.clicked.connect(self.btn_select_selected_clicked)
        self.ui.btn_delete_selected.clicked.connect(self.btn_delete_selected_clicked)

        # add Debug menu item
        self.ui.act_show_function_calls.setChecked(False)
        Debug.debug = False
        self.ui.act_show_function_calls.changed.connect(self.set_debug)
        self.ui.act_project_trunk.triggered.connect(self.set_project_trunk)
        self.ui.act_export_xml.triggered.connect(self.ExportData.export_xml)
        self.ui.act_import_xml.triggered.connect(self.ExportData.import_xml)

        # anim buttons
        # self.ui.btn_add_actor.clicked.connect(self.btn_add_actor_clicked)
        # self.ui.btn_add_anim_to_actor.clicked.connect(self.btn_add_anim_to_actor_clicked)

        # rig tree
        self.ui.tre_rigs.itemDoubleClicked.connect(self.tre_rigs_double_clicked)
        self.ui.tre_rigs.itemChanged.connect(self.tre_rigs_changed)
        self.ui.tre_rigs.customContextMenuRequested.connect(self.rt_click_rig_tree)

        # anim tree
        self.ui.tre_animations.customContextMenuRequested.connect(self.rt_click_anim_tree)
        self.ui.tre_animations.itemDoubleClicked.connect(self.tre_animations_double_clicked)
        self.ui.tre_animations.itemClicked.connect(self.tre_animations_clicked)
        self.ui.tre_animations.itemChanged.connect(self.tre_animations_changed)
        self.ui.tre_animations.itemPressed.connect(self.tre_animations_pressed)

        # model tree
        self.ui.tre_models.itemDoubleClicked.connect(self.tre_models_double_clicked)
        self.ui.tre_models.itemChanged.connect(self.tre_models_changed)
        # self.ui.tre_models.itemSelectionChanged.connect(self.tre_models_selection_changed)
        self.ui.tre_models.customContextMenuRequested.connect(self.rt_click_model_tree)

        # callbacks
        self.kAfterOpen_update_data = None
        self.kAfterSave_file_saved = None
        self.kAfterNew_file_new = None
        self.kAfterRename = None

    # >>>>>>>>>>>>>>>>>>>>>>>>  main menu setup start <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

    def eventFilter(self, obj, event):
        """
        catches close event override for QObject

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
        if Debug.debug: print(('calling :: {0}'.format('run')))

        self.remove_callbacks()
        self.add_callbacks()
        self.populate_trees_ui()
        self.ui.show()
        self.ui.lab_log.setText('Welcome to the FBX Exporter')

    def close_event(self):
        """
        called from the eventFilter on close
        """
        # self.remove_callbacks()
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

    # >>>>>>>>>>>>>>>>>>>>>>>>  main menu setup end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

    # >>>>>>>>>>>>>>>>>>>>>>>>  callbacks start <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

    def file_opened(self, *args):
        """
        callback for Maya file opened
        """
        pass

        # closing current ui and populating new ui based on new file opening
        try:
            if self.ui.isVisible():
                self.ui.close()
                initialize_module()
        except:
            # no except needed if self.ui is not visible it has been deleted and does not need to be initialized
            pass

    def file_new(self, *args):
        """
        callback for new Maya file
        """
        try:
            if self.ui.isVisible():
                self.ui.close()
        except:
            # no except needed if self.ui is not visible it has been deleted and does not need to be closed
            pass

    def file_saved(self, *args):
        """
        callback for saved Maya file
        """
        pass
        # if self.user_options.save_to_disk:
        #     self.write_fileInfo_to_disk()

    def add_callbacks(self):
        """
        assigning callbacks to variables so they can be tracked and cleanep up later
        """
        # callbacks
        self.kAfterOpen_update_data = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterOpen,
                                                                         self.file_opened)
        self.kAfterSave_file_saved = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterSave,
                                                                        self.file_saved)
        self.kAfterNew_file_new = OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kAfterNew, self.file_new)
        # self.kAfterRename = OpenMaya.MNodeMessage.addNameChangedCallback(OpenMaya.MObject(), self.name_changed)

    def remove_callbacks(self):
        """
        removes callback created in __init__()
        """
        if Debug.debug: print(('calling :: {0}'.format('remove_callbacks')))

        if self.kAfterOpen_update_data:
            OpenMaya.MSceneMessage.removeCallback(self.kAfterOpen_update_data)

        if self.kAfterSave_file_saved:
            OpenMaya.MSceneMessage.removeCallback(self.kAfterSave_file_saved)

        if self.kAfterNew_file_new:
            OpenMaya.MSceneMessage.removeCallback(self.kAfterNew_file_new)

        if self.kAfterRename:
            OpenMaya.MNodeMessage.removeCallback(self.kAfterRename)

    # >>>>>>>>>>>>>>>>>>>>>>>>  callbacks end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< #

    def remove_model_click(self, item):
        """
        separating out this remove model call because it needs to have a populate ui call in it
        ...otherwise calls to remove_model fail because the ui has already been refreshed

        :param item: model tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('remove_model_click')))

        items = self.get_selected_items_from_active_tab()
        for item in items:
            self.remove_model(item)

        self.populate_model_tree_ui()

    def remove_model(self, item):
        """
        removes model from layer tree item.

        :param item: model tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('remove_model')))

        fbx_exporter_data.ExporterData.remove_model(item)

    def add_item_to_model(self, item):
        """
        right click call to add model to layer item

        :param item: layer tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('add_item_to_model')))

        temp_list = []
        selected = pm.ls(selection=True, type='transform')
        for sel in selected:
            temp_list.append(sel.name())

        self.ui.tre_models.blockSignals(True)

        for layer in self.model_layers:
            if item.parent():
                if layer.name == item.parent().text(0):
                    for model in layer.models:
                        if model.name == item.text(0):
                            temp_list = temp_list + model.export_items
                            model.export_items = set(temp_list)

                            self.ExportData.write_model_layer_data_to_fileinfo(self.model_layers)

        self.ui.tre_models.blockSignals(False)
        self.populate_model_tree_ui()

    def remove_item_from_model(self, item):
        """
        right click call to remove model from layer item

        :param item: model tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('remove_item_from_model')))

        selected = pm.ls(selection=True, type='transform')

        self.ui.tre_models.blockSignals(True)

        for layer in self.model_layers:
            if layer.name == item.parent().text(0):
                for model in layer.models:
                    if model.name == item.text(0):
                        for sel in selected:
                            if sel.name() in model.export_items:
                                model.export_items.remove(sel.name())

                        self.ExportData.write_model_layer_data_to_fileinfo(self.model_layers)

        self.ui.tre_models.blockSignals(False)
        self.populate_model_tree_ui()

    def print_export_items(self, item):
        """
        right click call to print the items export items

        :param item: tree item model
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('print_export_items')))

        for layer in self.model_layers:
            if layer.name == item.parent().text(0):
                for model in layer.models:
                    if model.name == item.text(0):
                        for export_item in model.export_items:
                            print(('\t{0}'.format(export_item)))

    def remove_model_layer_click(self, item):
        """
        separating out this remove model layer call because it needs to have a populate ui call in it
        ...otherwise calls to remove_model_layer fail because the ui has already been refreshed

        :param item: layer tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('remove_model_click')))

        self.remove_model_layer(item)
        self.populate_model_tree_ui()

    def remove_model_layer(self, item):
        """
        removes layer from model tree.

        :param item: layer tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('remove_model_layer')))

        items = self.get_selected_items_from_active_tab()
        for item in items:
            fbx_exporter_data.ExporterData.remove_key(Identifiers.model_layer_identifier + item.text(0))

        self.populate_model_tree_ui()

    def select_from_exporter(self):
        """
        looks at item selected in the exporter and selects same models in the maya scene

        @param item: ui item
        @type item: tree widget item
        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('select_from_exporter')))

        pm.select(clear=True)
        select_set = set()

        items = self.get_selected_items_from_active_tab()
        for item in items:
            if item.whatsThis(0) == Identifiers.rig_layer_identifier:
                for layer in self.rig_layers:
                    if layer.name == item.text(0):
                        select_set.add(layer.root)
            elif item.whatsThis(0) == Identifiers.rigs_str:
                for layer in self.rig_layers:
                    for model in layer.models:
                        if model.name == item.text(0):
                            for export_item in model.export_items:
                                select_set.add(export_item)
            if item.whatsThis(0) == Identifiers.model_layer_str:
                for layer in self.model_layers:
                    if layer.name == item.text(0):
                        for model in layer.models:
                            for export_item in model.export_items:
                                select_set.add(export_item)
            elif item.whatsThis(0) == Identifiers.models_str:
                for layer in self.model_layers:
                    for model in layer.models:
                        if model.name == item.text(0):
                            for export_item in model.export_items:
                                select_set.add(export_item)

        select_list = list(select_set)

        try:
            pm.select(select_list)
        except:
            out = 'Item not founds in scene..'
            self.logger.error(out)
            self.ui.lab_log.setText(out)

    def get_kids_from_export_layer(self, export_layer):

        print('export_layer :: '.format(export_layer))
        print('export_layer kids :: '.format(export_layer.childCount()))

        kids = []
        for i in range(export_layer.childCount()):
            kids.append(export_layer.child(i))

        return kids

    def get_selected_items_from_active_tab(self):
        """
        gets the selected item from the active tab. returns selectd item and parent if it has one
        """
        if Debug.debug: print(('calling :: {0}'.format('get_selected_items_from_active_tab')))

        items = []
        index = self.ui.tab_widget.currentIndex()
        if self.ui.tab_widget.tabText(index) == Identifiers.rigs_str:
            items = self.ui.tre_rigs.selectedItems()
        elif self.ui.tab_widget.tabText(index) == Identifiers.animations_str:
            items = self.ui.tre_animations.selectedItems()
        elif self.ui.tab_widget.tabText(index) == Identifiers.models_str:
            items = self.ui.tre_models.selectedItems()

        children = []
        parents = []
        for item in items:
            if item.childCount() > 0:
                parents.append(item)
                children = children + self.get_kids_from_export_layer(item)
            elif item.parent():
                children.append(item)

        selected_kids = []
        for a_parent in parents:
            for i in range(a_parent.childCount() - 1):
                selected_kids.append(a_parent.child(i))

        out_kids = list(set(children + selected_kids))

        return out_kids

    def get_tree_from_tab(self):
        """
        gets tree from active tab
        """
        if Debug.debug: print(('calling :: {0}'.format('get_tree_from_tab')))

        tree = None
        current_widget = self.ui.tab_widget.currentWidget()
        for child in current_widget.children():
            if type(child) == QtWidgets.QTreeWidget:
                tree = child

        return tree

    def get_item_based_on_names(self, names):
        """
        gets list of tree items based on list of names

        @param names: list of names to find items for
        @type names: list
        @return: list of items
        @rtype: list
        """
        if Debug.debug: print(('calling :: {0}'.format('get_item_based_on_name')))

        items = []

        iterator = QTreeWidgetItemIterator(self.ui.tre_models)
        while iterator.value():
            item = iterator.value()
            if item.text(0) in names:
                items.append(item)

            iterator += 1

        return items

    def get_expand_items(self):
        """
        gets list of items that have been expanded in tree

        @return: tree items
        @rtype: list
        """
        if Debug.debug: print(('calling :: {0}'.format('get_expand_items')))

        tree = self.get_tree_from_tab()
        if tree is not None:
            expanded_list = []

            item_count = tree.topLevelItemCount()
            for i in range(item_count):
                current_item = tree.topLevelItem(i)
                if current_item.isExpanded():
                    expanded_list.append(current_item.text(0))

            return expanded_list

    def set_expand_items(self, expanded_list):
        """
        expands tree items in tree based on provided list

        @param expanded_list: tree items to expand
        @type expanded_list: list
        """
        if Debug.debug: print(('calling :: {0}'.format('set_expand_items')))

        tree = self.get_tree_from_tab()

        if tree is not None:
            item_count = tree.topLevelItemCount()
            for i in range(item_count):
                current_item = tree.topLevelItem(i)
                test = expanded_list.count(str(current_item.text(0)))
                if test != 0:
                    current_item.setExpanded(True)

    # def deselect_selected(self):
    #     """
    #     deselects selected items in active tree
    #     """
    #     selected_items = self.get_selected_items_from_active_tab()
    #
    #     for item in selected_items:
    #         item.setSelected(False)

    """
    \/\/\/\/\/\/\/\/    Menu    \/\/\/\/\/\/\/\/
    """

    def btn_delete_selected_clicked(self):
        """
        event triggered by btn_delete_selected clicked

        handles generic cases for ui (not tree) button to delete whatever is selected
        """
        if Debug.debug: print(('calling :: {0}'.format('btn_delete_selected_clicked')))

        items = []
        index = self.ui.tab_widget.currentIndex()
        if self.ui.tab_widget.tabText(index) == Identifiers.rig_layer_identifier:
            items.append(self.ui.tre_rigs.selectedItems())
            for item in items:
                self.remove_rig(item)
        elif self.ui.tab_widget.tabText(index) == Identifiers.animations_str:
            items = self.ui.tre_animations.selectedItems()
            if items[0].whatsThis(0) == Identifiers.model_layer_str:
                self.remove_actors(items)
            elif items[0].whatsThis(0) == Identifiers.animations_str:
                self.remove_animations(items)
        elif self.ui.tab_widget.tabText(index) == Identifiers.models_str:
            items = self.ui.tre_models.selectedItems()
            for item in items:
                if item.whatsThis(0) == Identifiers.model_layer_str:
                    self.remove_model_layer(item)
                elif item.whatsThis(0) == Identifiers.models_str:
                    self.remove_model(item)

    def add_rig_model(self, layer_name):
        '''
        add model(s) as single model to rig later
        populates rig model class

        @param layer_name: name of layer to add model(s) to
        @type layer_name: str
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('add_rig_model')))

        add_models = []
        trans = pm.ls(selection=True)
        if trans:
            for tran in trans:
                if self.FbxExporter.is_group(tran):
                    add_models.append(tran.name())
                else:
                    shape = tran.getShape()
                    if shape.nodeType() == 'mesh':
                        add_models.append(tran.name())

        if add_models:
            for rig in self.rig_layers:
                if rig.name == layer_name:
                    model_data = RigModelData()
                    model_data.name = add_models[0]
                    model_data.uuid = self.FbxExporter.get_uuid(add_models[0])
                    model_data.path = rig.rig_path
                    model_data.export_items = add_models
                    model_data.influences = '0'
                    rig.models.append(model_data)

                    self.ExportData.write_rig_data_to_fileinfo(self.rig_layers)
                    self.populate_rig_tree_ui()


    # add export layer >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def get_active_tab(self):
        index = self.ui.tab_widget.currentIndex()
        if self.ui.tab_widget.tabText(index) == Identifiers.rigs_str:
            return (Identifiers.rigs_str)
        elif self.ui.tab_widget.tabText(index) == Identifiers.animations_str:
            return (Identifiers.animations_str)
        elif self.ui.tab_widget.tabText(index) == Identifiers.models_str:
            return (Identifiers.models_str)

    def btn_add_export_layer_clicked(self):
        """
        event triggered by btn_delete_selected clicked

        handles generic cases for ui (not tree) button to delete whatever is selected
        """
        active_tab = self.get_active_tab()
        print(('active_tab :: {0}'.format(active_tab)))

        match active_tab:
            case Identifiers.rigs_str:
                self.add_rig_layer()
            case Identifiers.animations_str:
                self.add_actor_layer()
            case Identifiers.models_str:
                self.add_model_layer()

    def add_rig_layer(self):
        '''
        adds selected joint to data as rig layer
        populates rig class

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('add_rig_layer')))

        select_root = pm.ls(selection=True)
        if select_root:
            select_root = select_root[0]
            if select_root.type() == 'joint':

                caption = 'Select Rig file path'
                rig_path = self.Browsers.get_existing_directory(caption, self.framework_paths)
                if rig_path:
                    # removing for work on new requirements for adding multiple joint chains in one scene
                    # parent = self.get_top_level_parent(select_root)
                    rig_layer_data = RigLayerData()
                    rig_layer_data.name = select_root.name()
                    rig_layer_data.model_name = select_root.name()
                    rig_layer_data.root = select_root.name()
                    use_path = self.FbxExporter.get_relative_path(rig_path)
                    rig_layer_data.rig_path = use_path
                    rig_layer_data.uuid = self.FbxExporter.get_uuid(select_root.name())
                    rig_layer_data.export_items.append(select_root.name())

                    caption = 'Select Animation folder path'
                    anim_path = self.Browsers.get_existing_directory(caption, use_path)
                    self.add_rig_attr(select_root)
                    select_root.setAttr(Identifiers.root_str, select_root.name())
                    if anim_path:
                        relative_path = self.FbxExporter.get_relative_path(anim_path)
                        rig_layer_data.animation_path = relative_path
                        # parent = self.get_top_level_parent(select_root)
                        self.update_anim_path_attr(select_root, relative_path)

                    self.rig_layers.append(rig_layer_data)
                    self.ExportData.write_rig_data_to_fileinfo(self.rig_layers)
                    self.populate_rig_tree_ui()
            else:
                out = 'No root node selected. Please select the parent of a joint chain and try again.'
                self.logger.error(out)
                self.ui.lab_log.setText(out)
        else:
            out = 'No root node selected. Please select the parent of a joint chain and try again.'
            self.logger.error(out)
            self.ui.lab_log.setText(out)

    # add export layer >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def btn_add_anim_to_actor_clicked(self):
        '''
        event triggered by btn_add_anim_to_actor clicked

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('btn_add_anim_to_actor_clicked')))

        # currently you can only add a uniquely named animation to only one actor
        # i am leaving this open to change by reducing the select to one item and
        # sending add animation a list

        selected = self.get_selected_items_from_active_tab()
        if selected:
            items = [selected[0]]
            self.add_animations(items)
        else:
            out = 'Please select an actor and try again'
            pm.confirmDialog(title='No Actor selected', message=out, button=['OK'])

    def set_project_trunk(self):
        '''
        open project trunk dialog for editing

        @return:

        @rtype:
        '''

        TrunkUI = fbx_exporter_ui.ProjectTrunkUI()
        TrunkUI.run()

    def set_debug(self):
        """
        turns on the option to print out functions as they are called
        """
        if Debug.debug: print(('calling :: {0}'.format('set_debug')))

        Debug.debug = self.ui.act_show_function_calls.isChecked()

    def cmb_current_index_changed(self, influences):
        '''
        event triggered by change in combo box for then number of influences in a skin cluster

        @param influences: number of influences selected from the drop down
        @type influences: str
        @return:
        @rtype:
        '''

        item = self.get_selected_items_from_active_tab()[0]
        self.ExportData.change_rig_influences(item, influences)
        self.populate_rig_tree_ui()

    """
    \/\/\/\/\/\/\/\/    Animation UI    \/\/\/\/\/\/\/\/
    """

    # def act_export_char_triggered(self):
    #     """
    #     calls for character data to be written to disk
    #     """
    #     if Debug.debug : print(('calling :: {0}'.format('act_export_char_triggered')))
    #     keys = []
    #
    #     selected = self.ui.tre_animations.selectedItems()
    #     for select in selected:
    #         if select.whatsThis(0) == Identifiers.rig_layer_identifier:
    #             keys.append(self.ExportData.get_xml(Identifiers.actor_identifier + select.text(0)))

    def btn_export_selected_clicked(self):
        """
        event triggered by btn_export_selected clicked

        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('btn_export_selected_clicked')))

        items = self.ui.tre_animations.selectedItems()

        for item in items:
            if item.whatsThis(0) == Identifiers.model_layer_str:
                for layer in self.actors_layers:
                    for animation in layer.animations:
                        self.export_animation(animation, layer)

            elif item.whatsThis(0) == Identifiers.animations_str:
                for layer in self.actors_layers:
                    for animation in layer.animations:
                        if animation.anim_name == item.text(0):
                            self.export_animation(animation, layer)

    def btn_select_selected_clicked(self):
        """
        event triggered by btn_export_all clicked

        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('btn_export_all_clicked')))

        if self.actors_layers:
            self.Save.query_save_scene_on_export()

        for actor in self.actors_layers:
            for animation in actor.animations:
                self.export_animation(animation, actor)

    # hack need to marry the next 2 with combine dialog
    # 1
    def select_from_scene(self):
        """
        looks at models selected in the Maya scene and selected the same assets in the tree view
        """
        if Debug.debug: print(('calling :: {0}'.format('btn_select_from_scene_clicked')))

        scene_selections = pm.ls(selection=True, type='transform')

        names = []
        for selection in scene_selections:
            names.append(selection.name())

        if names:
            model_names = []
            for name in names:
                model = self.get_model_from_export_item_name(name)
                model_names.append(model.name)
            model_names = list(set(model_names))
            items = self.FbxExporter.get_tree_item_from_name(model_names, self.ui.tre_models)

            self.deselect_selected()

            for item in items:
                item.setSelected(True)
                item.parent().setExpanded(True)

    def update_user_options(self):
        if Debug.debug: print(('calling :: {0}'.format('update_user_options')))

        user_options = UserOptionsData()

        user_options.auto_select_in_scene = self.ui.act_auto_select_in_scene.isChecked()
        user_options.save_to_disk = self.ui.act_enable_save_to_disk.isChecked()

        self.ExportData.write_user_option_data_to_prefs(user_options)

    def export_options(self, item):
        """
        called from right click option. opens export option ui for viewing or editing

        :param item: tree item (model or layer)
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('export_options')))

        # having issue here "RuntimeError: Internal C++ object (PySide2.QtWidgets.QTreeWidgetItem)
        # so i am grabbing the item name before it is deleted. blocking signals did not work
        item_name = item.text(0)
        if item.whatsThis(0) == Identifiers.models_str:
            item_parent_name = item.parent().text(0)

        # self.ui.tre_models.blockSignals(True)

        if item.whatsThis(0) == Identifiers.model_layer_str:
            print('model_layer_str')
            for layer in self.model_layers:
                if layer.name == item_name:
                    update_layer = layer
                    model_options = ModelExportUI(update_layer, Identifiers.model_layer_str)
                    if model_options.ui.exec_():
                        self.ExportData.write_model_layer_data_to_fileinfo(self.model_layers)
                        self.populate_model_tree_ui()

        elif item.whatsThis(0) == Identifiers.models_str:
            print('model_str')
            for layer in self.model_layers:
                if layer.name == item_parent_name:
                    for model in layer.models:
                        if item_name == model.name:
                            model_options = ModelExportUI(model, Identifiers.models_str)
                            if model_options.ui.exec_():
                                self.ExportData.write_model_layer_data_to_fileinfo(self.model_layers)
                                self.populate_model_tree_ui()

        # self.ui.tre_models.blockSignals(False)

    def export_model_layer(self, item):
        """
        called from layer item right click option. export layer contents (...model items)

        :param item: layer tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('export_model_layer')))

        if scr.framework_paths['project_path']:
            root = self.ui.tre_models.invisibleRootItem()

            for tree_child in range(root.childCount()):
                layer_item = self.ui.tre_models.topLevelItem(tree_child)
                if layer_item.text(0) == item.text(0):
                    for model_item in range(layer_item.childCount()):
                        self.export_model(layer_item.child(model_item))
        else:
            out = ('No project Path found.')
            self.logger.critical(out)
            self.ui.lab_log.setText(out)

    @staticmethod
    def set_export_options(data, class_type):
        """
        set up generic option class with data from model or layer item

        :param class_type: either layer or model
        :type class_type: str
        :param data: layer or model class
        :type data: layer or model class from __init__()
        :return Options: export option
        :rtype Options: ExportOptions() class
        """
        if Debug.debug: print(('calling :: {0}'.format('set_export_options')))

        options = ExportOptions()
        if class_type == Identifiers.models_str:
            options.fbx_export_override_path = data.fbx_export_override_layer_path
            options.fbx_export_override_options = data.fbx_export_override_layer_options
        options.fbx_export_triangulate = data.fbx_export_triangulate
        options.fbx_export_instances = data.fbx_export_instances
        options.fbx_export_animation_only = data.fbx_export_animation_only
        options.fbx_export_smooth_mesh = data.fbx_export_smooth_mesh
        options.fbx_export_tangents = data.fbx_export_tangents
        options.fbx_export_hard_edges = data.fbx_export_hard_edges
        options.fbx_export_zero = data.fbx_export_zero
        options.fbx_export_smoothing_groups = data.fbx_export_smoothing_groups

        return options

    def get_export_dir(self, layer_path, model, identifier):
        """
        returns export directory for models and layers

        :param model: model data
        :type model: ModelData()
        :param identifier: says what type of object it is
        :type identifier: str
        :param layer_path: path that the layer points at
        :type layer_path: str
        :return: path to append (model name + .fbx) to
        :rtype: str
        """
        if Debug.debug: print(('calling :: {0}'.format('get_export_dir')))

        if layer_path:
            fail = False
            if identifier == Identifiers.model_layer_str:
                if os.path.isdir(layer_path):
                    return layer_path
                else:
                    export_dir = scr.framework_paths['project_path'] + '\\' + layer_path
                    if os.path.isdir(export_dir):
                        return export_dir
                    else:
                        fail = True

            elif identifier == Identifiers.models_str:
                if os.path.isdir(model.path):
                    return model.path
                else:
                    if model.fbx_export_override_layer_path:
                        export_dir = scr.framework_paths['project_path'] + '\\' + model.path
                        if os.path.isdir(export_dir):
                            return export_dir
                        else:
                            fail = True
                    else:
                        export_dir = scr.framework_paths['project_path'] + '\\' + layer_path
                        if os.path.isdir(export_dir):
                            return export_dir
                        else:
                            fail = True

            if fail:
                out = 'Export directory {0} was not found. Make sure you have the correct path(s) selected. ' \
                    .format(export_dir)
                pm.confirmDialog(title='No valid path found', message=out, button=['OK'])

                return scr.framework_paths['project_path']

        else:
            out = 'There is no export layer path set, Please set a path for the export layer.'
            pm.confirmDialog(title='No export layer path found', message=out, button=['OK'])

            return None

    def export_model(self, item):
        """
        called from layer item right click option. export layer contents (...model items)

        :param item: layer tree item
        :type item: QTreeWidgetItem
        """

        if scr.framework_paths['project_path']:
            for layer in self.model_layers:
                if item.parent().text(0) == layer.name:
                    for model in layer.models:
                        if item.text(0) == model.name:
                            if model.fbx_export_override_layer_path:
                                export_dir = self.get_export_dir(layer.path, model, Identifiers.models_str)
                            else:
                                export_dir = self.get_export_dir(layer.path, '', Identifiers.model_layer_str)

                            if export_dir:
                                export_path = export_dir + '\\' + model.name + '.fbx'
                                if model.fbx_export_override_layer_options:
                                    options = self.set_export_options(model, Identifiers.models_str)
                                else:
                                    options = self.set_export_options(layer, Identifiers.model_layer_str)

                                self.Exporter.export_model_setup(model, export_path, options)
        else:
            out = ('No project Path found.')
            self.logger.critical(out)
            self.ui.lab_log.setText(out)

    def add_multiple_models(self, layer_name, model_name, use_name=None, from_selection=True, mess=True):
        """
        called when user wants to add a model item to a layer item.
        ...populates layer with new model and calls to right to data

        :param model_name: single model name
        :type model_name: dag node name
        :param layer_name: name of the layer to add the model to
        :type layer_name: str
        :param from_selection: model is selected in the scene instead of from a separate dialog (SelectSomething)
        :type from_selection: bool
        """
        if Debug.debug: print(('calling :: {0}'.format('add_model')))

        add_models = []
        if from_selection:
            trans = pm.ls(selection=True, type='transform')
            for tran in trans:
                if self.FbxExporter.is_group(tran):
                    add_models.append(tran.name())
                else:
                    shape = tran.getShape()
                    if shape.nodeType() == 'mesh':
                        add_models.append(tran.name())
        else:
            add_models.append(model_name)

        if add_models:
            valid_models = []
            not_valid_models = []
            for layer in self.model_layers:
                if layer_name == layer.name:
                    for add_model in add_models:
                        found = False
                        for model in layer.models:
                            if model.name == add_model:
                                found = True
                                not_valid_models.append(add_model)
                        if not found:
                            valid_models.append(add_model)

                    if valid_models:
                        for model in valid_models:
                            model_data = ModelData()

                            if use_name:
                                model_data.name = use_name
                            else:
                                model_data.name = model

                            model_data.export_items.append(model)
                            model_data.uuid = self.FbxExporter.get_uuid(model)
                            layer.models.append(model_data)
                    else:
                        out = ('{0} already added to Layer'.format(not_valid_models))
                        pm.confirmDialog(title='Model already added', message=out, button=['OK'])

            self.ExportData.write_model_layer_data_to_fileinfo(self.model_layers)
            self.populate_model_tree_ui()

        elif mess:
            out = 'No model selected to add.'
            pm.confirmDialog(title='No Model selected', message=out, button=['OK'])

    def add_model_layer(self):
        """
        called by user button or right click to add a layer item, Creates layer name based on
        export folder name. Adds random number to layer name if it is already in data
        """
        if Debug.debug: print(('calling :: {0}'.format('add_model_layer')))

        import random

        model_layer_data = LayerData()
        model_layer_data.fbx_export_override_layer_path = False
        model_layer_data.fbx_export_override_options = False
        path = self.Browsers.get_existing_directory('Model Layer export path', scr.framework_paths['project_path'])
        use_path = self.FbxExporter.get_relative_path(path)
        if use_path:
            model_layer_data.path = use_path
        else:
            return None

        if model_layer_data.path:
            name = Path(pm.sceneName()).stem

            if not self.ExportData.check_exists_layer(Identifiers.model_layer_identifier + name):
                model_layer_data.name = name
            else:
                model_layer_data.name = (name + '_' + str(random.randint(100, 999)))
            print('model_layer_data.name :: {}'.format(model_layer_data.name))

            self.model_layers.append(model_layer_data)
            self.add_multiple_models(name, None, None, mess=False)
            self.ExportData.write_model_layer_data_to_fileinfo(self.model_layers)
            self.populate_model_tree_ui()

    # >>>>>>>>>>>>>>>>>>>>>>>>  trees  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#
    def populate_trees_ui(self):
        """
        function that calls for building/displaying all the data for the character ui
        """
        if Debug.debug: print(('calling :: {0}'.format('populate_trees_ui')))
        self.populate_anim_tree_ui()
        self.populate_rig_tree_ui()
        self.populate_model_tree_ui()

    # >>>>>>>>>>>>>>>>>>>>>>>>  animation tree  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#
    def populate_anim_tree_ui(self):
        '''
        get data from fileinfo and calls for anim ui to be built with that data

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('populate_anim_tree_ui')))

        self.actors_layers = self.ExportData.build_actor_class_from_data()
        self.refresh_anim_tree_ui()


    def refresh_anim_tree_ui(self):
        '''
        recreates anim tree from actor and anim classes (these classes should be updated brfore calling this function)

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('refresh_anim_tree_ui')))

        self.ui.lab_log.setText('')

        expanded_items = self.get_expand_items()
        self.ui.tre_animations.clear()

        for character in self.actors_layers:
            character_item = QtWidgets.QTreeWidgetItem()
            character_item.setSizeHint(0, QSize(-1, 20))
            character_item.setText(0, character.name)
            character_item.setWhatsThis(0, Identifiers.model_layer_str)

            for animation in character.animations:
                animation_item = QtWidgets.QTreeWidgetItem()
                animation_item.setFlags(animation_item.flags() | Qt.ItemIsEditable)
                animation_item.setSizeHint(0, QSize(-1, 20))
                animation_item.setWhatsThis(0, Identifiers.animations_str)
                animation_item.setText(0, animation.anim_name)
                animation_item.setText(1, animation.start_frame)
                animation_item.setText(2, animation.end_frame)
                animation_item.setText(3, animation.path)
                animation_item.setText(4, animation.override_path)
                animation_item.setText(5, animation.muted_layers)
                character_item.addChild(animation_item)

            self.ui.tre_animations.addTopLevelItem(character_item)
            self.set_expand_items(expanded_items)

    def create_animation_tree_menu(self):
        '''
        creates right click option for the anim tree

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('create_animation_tree_menu')))

        rt_click_menu = QtWidgets.QMenu()

        add_shot_action = rt_click_menu.addAction('Add Rig for animation')
        add_shot_action.triggered.connect(self.add_actor_layer)
        rt_click_menu.addAction(add_shot_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def create_character_menu(self, item):
        '''
        creates right click option for actors in anim tree

        @param item: every anim item in tree
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('create_character_menu')))

        rt_click_menu = QtWidgets.QMenu()

        add_animation_action = rt_click_menu.addAction('Add Animation')
        add_animation_action.triggered.connect(lambda: self.add_animations([item]))
        rt_click_menu.addAction(add_animation_action)

        remove_character_action = rt_click_menu.addAction('Remove Character')
        remove_character_action.triggered.connect(lambda: self.remove_actors([item]))
        rt_click_menu.addAction(remove_character_action)

        # export_all_action = rt_click_menu.addAction('Select Character')
        # export_all_action.triggered.connect(lambda: self.select_from_exporter(item))
        # rt_click_menu.addAction(export_all_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def tre_animations_double_clicked(self, item, column):
        '''
        event for when an item in the anm tree in double clicked

        @param item: anim or actor item
        @type item: tree item
        @param column: column the item is in
        @type column: int
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('tre_animations_double_clicked')))

        print('anim double clicked :: {}, {}'.format(item, column))

        # the arg for column from QTreeWidget.itemChanged seems to return 0 unless the column is writable..?
        # So i am grabbing the correct column for tre_animations_changed here
        self.anim_column_double_clicked = column

        if column == 0:
            self.old_anim_name = item.text(0)
        elif column == 3:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        elif column == 4:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        elif column == 5:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def tre_animations_pressed(self, item, column):
        '''
        called from event for tre_animations pressed. sets the class var for what last column pressed is

        @param item: animation
        @type item: tree item
        @param column: column
        @type column: int
        @return:
        @rtype:
        '''

        self.anim_column_clicked = column

    def tre_animations_clicked(self, item, column):
        """
        called from event for tre_animations clicked

        @param item: anim ui item
        @type item: tree widget item
        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('tre_animations_clicked')))

        if item.whatsThis(0) == Identifiers.model_layer_str:
            for actor in self.actors_layers:
                if actor.name == item.text(0):
                    pm.select(actor.name)

    def tre_animations_changed(self, item):
        '''
        event that is called when a data for a tree item has changed in the ui

        @param item: item that was changed
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('tre_animations_changed')))

        print('anim changed :: {}'.format(item))

        if item.parent() is not None:
            if self.anim_column_double_clicked == 0:
                self.ExportData.change_animation_name(item, item.text(0), self.old_anim_name)
                self.populate_anim_tree_ui()
            if self.anim_column_double_clicked == 1:
                self.ExportData.change_start_end_frame(item, item.text(1), 1)
                self.populate_anim_tree_ui()
            if self.anim_column_double_clicked == 2:
                self.ExportData.change_start_end_frame(item, item.text(2), 2)
                self.populate_anim_tree_ui()
            if self.anim_column_double_clicked == 4:
                for actor in self.actors_layers:
                    if item.parent().text(0) == actor.name:
                        export_dir = self.get_export_directory(actor.path)

                relative_path = self.get_path(export_dir)
                self.ExportData.change_override_path(item, relative_path, 4)
                self.populate_anim_tree_ui()

    # >>>>>>>>>>>>>>>>>>>>>>>>  animation tree end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

    # >>>>>>>>>>>>>>>>>>>>>>>>  rig tree start <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#
    def populate_rig_tree_ui(self):
        '''
        get data for rig from fileInfo, puts it in rig_layers and calls the rig tree to be updated

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('populate_rig_tree_ui')))

        self.rig_layers = self.ExportData.build_class_from_data(Identifiers.rig_layer_identifier)
        self.refresh_rig_tree_ui()

    def refresh_rig_tree_ui(self):
        '''
        creates rig data in the rig tree based on rig class in rig_layers

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('refresh_rig_tree_ui')))

        self.ui.lab_log.setText('')

        expanded_items = self.FbxExporter.get_expand_items(self.ui.tre_rigs)
        self.clear_rig_tree_ui()

        for rig in self.rig_layers:

            rig_item = QtWidgets.QTreeWidgetItem()
            rig_item.setFlags(rig_item.flags() | Qt.ItemIsEditable)
            rig_item.setText(0, rig.name)
            rig_item.setText(1, rig.rig_path)
            rig_item.setText(2, rig.animation_path)
            rig_item.setWhatsThis(0, Identifiers.rig_layer_identifier)

            for model in rig.models:
                model_item = QtWidgets.QTreeWidgetItem()
                model_item.setFlags(model_item.flags() | Qt.ItemIsEditable)
                model_item.setWhatsThis(0, Identifiers.rigs_str)
                model_item.setText(0, model.name)

                # adding drop down for skin influences
                combo_box = QtWidgets.QComboBox()
                combo_box.setFixedWidth(60)
                combo_box.addItem('')
                combo_box.addItem('1')
                combo_box.addItem('2')
                combo_box.addItem('3')

                if eval(model.influences):
                    combo_box.setCurrentIndex(int(model.influences))
                else:
                    combo_box.setCurrentIndex(0)

                combo_box.currentIndexChanged.connect(self.cmb_current_index_changed)

                rig_item.addChild(model_item)
                self.ui.tre_rigs.setItemWidget(model_item, 3, combo_box)

            self.ui.tre_rigs.addTopLevelItem(rig_item)
            self.FbxExporter.set_expand_items(self.ui.tre_rigs, expanded_items)
            self.ui.tre_rigs.setColumnWidth(0, 160)
            self.ui.tre_rigs.setColumnWidth(3, 62)

    def create_rig_menu(self, item):
        '''
        creates context menu for rig layer item

        @param item: rig item
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('create_rig_menu')))

        rt_click_menu = QtWidgets.QMenu()

        add_export_action = rt_click_menu.addAction('Export Rig Layer')
        add_export_action.triggered.connect(lambda: self.export_rig_layer(item))
        rt_click_menu.addAction(add_export_action)

        rt_click_menu.addSeparator()

        add_export_action = rt_click_menu.addAction('Add model(s) as single rig export')
        add_export_action.triggered.connect(lambda: self.add_rig_model(item.text(0)))
        rt_click_menu.addAction(add_export_action)

        add_export_action = rt_click_menu.addAction('Add model(s) as multiple rig exports')
        add_export_action.triggered.connect(lambda: self.add_multiple_rig_model(item.text(0)))
        rt_click_menu.addAction(add_export_action)

        rt_click_menu.addSeparator()

        add_remove_action = rt_click_menu.addAction('Remove Rig Layer')
        add_remove_action.triggered.connect(lambda: self.remove_rig(item))
        rt_click_menu.addAction(add_remove_action)

        add_select_action = rt_click_menu.addAction('Select Rig')
        add_select_action.triggered.connect(lambda: self.select_from_exporter())
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def create_rig_tree_menu(self):
        '''
        creates context menu for rig tree

        @param item: rig item
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('create_rig_tree_menu')))

        rt_click_menu = QtWidgets.QMenu()

        add_rig_action = rt_click_menu.addAction('Add Rig Layer')
        add_rig_action.triggered.connect(self.add_rig_layer)
        rt_click_menu.addAction(add_rig_action)

        rt_click_menu.addSeparator()

        add_rig_action = rt_click_menu.addAction('Export All')
        add_rig_action.triggered.connect(self.export_all_rigs)
        rt_click_menu.addAction(add_rig_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def tre_rigs_double_clicked(self, item, column):
        """
        event triggered by tree model item itemDoubleClicked (model or layer)

        :param item: model or layer tree item
        :type item: QTreeWidgetItem
        :param column: column of the item double clicked
        :type column: int
        """
        if Debug.debug: print(('calling :: {0}'.format('tre_models_double_clicked')))

        self.rig_column_double_clicked = column
        if self.rig_column_double_clicked == 0:
            self.old_rig_name = item.text(0)
            if item.whatsThis(0) == Identifiers.rig_layer_identifier:
                self.ExportData.change_rig_name(item, self.old_rig_name)
            elif item.whatsThis(0) == Identifiers.rigs_str:
                self.ExportData.change_rig_name(item, self.old_rig_name)
        if self.rig_column_double_clicked == 1 or self.rig_column_double_clicked == 2:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def tre_rigs_changed(self, item):
        """
        event triggered by tree model item itemChanged...if data in the item has been accessed by user contact
        this could be related to the user making name or path changes

        :param item: model tree item ()
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('tre_models_changed')))

        if self.rig_column_double_clicked == 0:
            self.ExportData.change_rig_name(item, self.old_rig_name)

        if self.rig_column_double_clicked == 1 or self.rig_column_double_clicked == 2:
            if self.rig_column_double_clicked == 1:
                caption = 'Rig file path'
            if self.rig_column_double_clicked == 2:
                caption = 'Animation folder path'

            start_path = self.get_folder_path(item)
            path = self.Browsers.get_open_filename(caption, start_path, '*.fbx')
            if path:
                path = self.FbxExporter.get_relative_path(path)

                if self.rig_column_double_clicked == 1:
                    self.ExportData.change_rig_layer_path(item, path, 'rig_path')

                    # update the attr for anim path
                    self.update_rig_anim_path(item, path)

                if self.rig_column_double_clicked == 2:
                    self.ExportData.change_rig_layer_path(item, path, 'anim_path')

                    # update the attr for anim path
                    self.update_rig_anim_path(item, path)

        self.populate_rig_tree_ui()

    def create_rig_model_menu(self, item):
        '''
        creates context menu for rig model item

        @param item: rig item
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('create_model_menu')))

        rt_click_menu = QtWidgets.QMenu()

        add_export_action = rt_click_menu.addAction('Export Model Rig')
        add_export_action.triggered.connect(lambda: self.export_rig(item))
        rt_click_menu.addAction(add_export_action)

        rt_click_menu.addSeparator()

        add_export_action = rt_click_menu.addAction('Add Model to Export Items')
        add_export_action.triggered.connect(lambda: self.add_model_export_item(item))
        rt_click_menu.addAction(add_export_action)

        add_export_action = rt_click_menu.addAction('Remove Model from Export Items')
        add_export_action.triggered.connect(lambda: self.remove_model_export_item(item))
        rt_click_menu.addAction(add_export_action)

        rt_click_menu.addSeparator()

        add_remove_action = rt_click_menu.addAction('Remove Rig Model')
        add_remove_action.triggered.connect(lambda: self.remove_rig_model(item))
        rt_click_menu.addAction(add_remove_action)

        add_select_action = rt_click_menu.addAction('Select Rig Model')
        add_select_action.triggered.connect(lambda: self.select_from_exporter())
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.addSeparator()

        add_select_action = rt_click_menu.addAction('Test influences')
        add_select_action.triggered.connect(lambda: self.test_influences(item))
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def rt_click_rig_tree(self, pos):
        '''
        event for right click action on rig tree

        @param pos: cursor location
        @type pos: QPoint
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('rt_click_rig_tree')))

        item = self.ui.tre_rigs.itemAt(pos)
        # selected = self.ui.tre_rigs.selectedItems()

        if item is not None:
            whats_this = item.whatsThis(0)
            if whats_this == Identifiers.rig_layer_identifier:
                self.create_rig_menu(item)
            elif whats_this == Identifiers.rigs_str:
                self.create_rig_model_menu(item)
        elif item is None:
            self.create_rig_tree_menu()

    # >>>>>>>>>>>>>>>>>>>>>>>>  rig tree end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

    # >>>>>>>>>>>>>>>>>>>>>>>>  model tree start <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

    def populate_model_tree_ui(self):
        """
        intermediary method that populates model layers (containing models) data from file info
        ...all the fileinfo interaction take place in the fbx_export_data module
        """
        if Debug.debug: print(('calling :: {0}'.format('populate_model_tree_ui')))

        self.model_layers = self.ExportData.build_class_from_data(Identifiers.model_layer_identifier)
        self.refresh_model_tree_ui()

    def refresh_model_tree_ui(self):
        """
        updates model tree with data from container classes for models and layers
        """
        if Debug.debug: print(('calling :: {0}'.format('refresh_model_tree_ui')))

        expanded_items = self.FbxExporter.get_expand_items(self.ui.tre_models)

        self.ui.tre_models.clear()

        for layer in self.model_layers:
            layer_item = QtWidgets.QTreeWidgetItem()
            layer_item.setFlags(layer_item.flags() | Qt.ItemIsEditable)
            layer_item.setSizeHint(0, QSize(-1, 20))
            layer_item.setWhatsThis(0, Identifiers.model_layer_str)
            layer_item.setText(0, layer.name)
            layer_item.setText(1, layer.path)

            # if layer.override_path:
            #     layer_item.setCheckState(1, Qt.Checked)
            #     layer_item.setText(1, 'True')
            # else:
            #     layer_item.setCheckState(1, Qt.Unchecked)
            #     layer_item.setText(1, 'False')

            # color = 0
            for model in layer.models:
                model_item = QtWidgets.QTreeWidgetItem()
                model_item.setFlags(model_item.flags() | Qt.ItemIsEditable)
                model_item.setSizeHint(0, QSize(-1, 20))
                model_item.setWhatsThis(0, Identifiers.models_str)
                model_item.setText(0, model.name)
                model_item.setText(1, model.path)
                layer_item.addChild(model_item)

                # if color:
                #     for i in range(model_item.columnCount()):
                #         # removing alternating colors. After
                #         # model_item.setBackground(i, QtGui.QBrush(self.dark_grey))
                #         model_item.setBackground(i, QtGui.QBrush(self.grey))
                # else:
                #     for i in range(model_item.columnCount()):
                #         model_item.setBackground(i, QtGui.QBrush(self.grey))

                # color = not color

            self.ui.tre_models.addTopLevelItem(layer_item)
            self.FbxExporter.set_expand_items(self.ui.tre_models, expanded_items)
            self.ui.tre_models.setColumnWidth(0, 180)

    def tre_models_double_clicked(self, item, column):
        """
        event triggered by tree model item itemDoubleClicked (model or layer)

        :param item: model or layer tree item
        :type item: QTreeWidgetItem
        :param column: column of the item double clicked
        :type column: int
        """
        if Debug.debug: print(('calling :: {0}'.format('tre_models_double_clicked')))

        print('model double clicked :: {} {}'.format(item, column))

        # the arg for column from QTreeWidget.itemChanged seems to return 0 unless the column is writable..?
        # So i am grabbing the correct column for tre_animations_changed here
        self.model_column_double_clicked = column
        if self.model_column_double_clicked == 0:
            self.old_layer = item.text(0)
        if self.model_column_double_clicked == 1:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def tre_models_changed(self, item):
        """
        event triggered by tree model item itemChanged...if data in the item has been accessed by user contact
        this could be related to the user making name or path changes

        :param item: model tree item ()
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('tre_models_changed')))

        print('model changed :: {}'.format(item))

        if self.model_column_double_clicked == 1:
            print('.model_column_double_clicked :: {}'.format(self.model_column_double_clicked))
            start_path = self.get_folder_path(item)
            path = self.Browsers.open_save_file_browser('Model file path', start_path, '*.fbx')

            if path:
                path = self.FbxExporter.get_relative_path(path)

                if item.whatsThis(0) == Identifiers.model_layer_str:
                    self.ExportData.change_layer_path(item, path)
                elif item.whatsThis(0) == Identifiers.models_str:
                    self.ExportData.change_model_path(item, path)

        self.populate_model_tree_ui()

    def tre_models_selection_changed(self):
        """
        event triggered by tree model item itemSelectionChanged
        """
        pass

    def create_model_menu(self, item):
        """
        creates the right click menu options for the model QTreeWidgetItem

        :param item: model item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('create_model_menu')))

        rt_click_menu = QtWidgets.QMenu()

        add_export_action = rt_click_menu.addAction('Export Model')
        add_export_action.triggered.connect(lambda: self.export_model(item))
        rt_click_menu.addAction(add_export_action)

        add_export_action = rt_click_menu.addAction('Export Option')
        add_export_action.triggered.connect(lambda: self.export_options(item))
        rt_click_menu.addAction(add_export_action)

        rt_click_menu.addSeparator()

        add_select_action = rt_click_menu.addAction('Add to Export Items')
        add_select_action.triggered.connect(lambda: self.add_item_to_model(item))
        rt_click_menu.addAction(add_select_action)

        add_select_action = rt_click_menu.addAction('Remove from Export Items')
        add_select_action.triggered.connect(lambda: self.remove_item_from_model(item))
        rt_click_menu.addAction(add_select_action)

        add_select_action = rt_click_menu.addAction('Print Export Items')
        add_select_action.triggered.connect(lambda: self.print_export_items(item))
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.addSeparator()

        add_select_action = rt_click_menu.addAction('Select from Exporter')
        add_select_action.triggered.connect(lambda: self.select_from_exporter())
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.addSeparator()

        add_remove_action = rt_click_menu.addAction('Remove Model')
        add_remove_action.triggered.connect(lambda: self.remove_model_click(item))
        rt_click_menu.addAction(add_remove_action)

        rt_click_menu.addSeparator()

        add_select_action = rt_click_menu.addAction('Open FBX Folder')
        add_select_action.triggered.connect(lambda: self.open_path_folder(item))
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def create_model_layer_menu(self, item):
        """
        creates the right click menu options for the layer QTreeWidgetItem

        :param item: layer item
        :type item: QTreeWidgetItem
        """

        if Debug.debug: print(('calling :: {0}'.format('create_rig_menu')))

        rt_click_menu = QtWidgets.QMenu()

        add_export_action = rt_click_menu.addAction('Export Layer Contents')
        add_export_action.triggered.connect(lambda: self.export_model_layer(item))
        rt_click_menu.addAction(add_export_action)

        add_select_action = rt_click_menu.addAction('Export Option')
        add_select_action.triggered.connect(lambda: self.export_options(item))
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.addSeparator()

        add_select_action = rt_click_menu.addAction('Add scene selection for export')
        add_select_action.triggered.connect(lambda: self.add_multiple_models(item.text(0), None))
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.addSeparator()

        add_remove_action = rt_click_menu.addAction('Remove Layer(s)')
        add_remove_action.triggered.connect(lambda: self.remove_model_layer_click(item))
        rt_click_menu.addAction(add_remove_action)

        rt_click_menu.addSeparator()

        add_select_action = rt_click_menu.addAction('Select from Exporter')
        add_select_action.triggered.connect(lambda: self.select_from_exporter())
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.addSeparator()

        add_select_action = rt_click_menu.addAction('Open FBX Folder')
        add_select_action.triggered.connect(lambda: self.open_path_folder(item))
        rt_click_menu.addAction(add_select_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def create_model_tree_menu(self):
        """
        creates the right click menu options for the model QTreeWidget
        """
        if Debug.debug: print(('calling :: {0}'.format('create_model_tree_menu')))

        rt_click_menu = QtWidgets.QMenu()
        add_model_tree_action = rt_click_menu.addAction('Add Layer')
        add_model_tree_action.triggered.connect(self.add_model_layer)
        rt_click_menu.addAction(add_model_tree_action)

        rt_click_menu.addSeparator()

        add_model_tree_action = rt_click_menu.addAction('Select from Maya scene')
        add_model_tree_action.triggered.connect(lambda: self.select_from_scene())
        rt_click_menu.addAction(add_model_tree_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def rt_click_model_tree(self, pos):
        """
        determines where what tree item the cursor is over and calls for creation of a right click menu

        :param pos: position of cursor during right click
        :type pos: pos
        """
        if Debug.debug: print(('calling :: {0}'.format('rt_click_model_tree')))

        item = self.ui.tre_models.itemAt(pos)

        if item is not None:
            whats_this = item.whatsThis(0)
            if whats_this == Identifiers.model_layer_str:
                self.create_model_layer_menu(item)
            elif whats_this == Identifiers.models_str:
                self.create_model_menu(item)
        elif item is None:
            self.create_model_tree_menu()

    # >>>>>>>>>>>>>>>>>>>>>>>>  model tree end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

    def get_path(self, export_dir):
        '''
        opens browser and return relative path

        @param export_dir: path
        @type export_dir: str
        @return: relative path based on project path
        @rtype: str
        '''

        overrider_path = self.Browsers.open_save_file_browser('Model file path', export_dir)
        relative_path = self.FbxExporter.get_relative_path(overrider_path)
        return relative_path

    def initialize_character_data(self, actor):
        """
        populates data in ActorLayerData() for use in self.actors_layers

        @param actor: node selected in maya scene
        @type actor: dag node
        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('populate_character_data')))

        character_data = ActorLayerData()
        character_data.name = actor.name()

        character_data.export_items.append(actor.name())
        character_data.path = actor.getAttr(Identifiers.animation_path_str)
        character_data.root = actor.name()

        self.actors_layers.append(character_data)

    def create_animation_menu(self, item):
        '''
        creates right click option for animation in anim tree

        @param item: every anim item in tree
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('create_animation_menu')))

        rt_click_menu = QtWidgets.QMenu()

        set_range_action = rt_click_menu.addAction('Set Maya to UI time range')
        set_range_action.triggered.connect(lambda: self.set_maya_to_data_range(item))
        rt_click_menu.addAction(set_range_action)

        set_mute_action = rt_click_menu.addAction('Mute selected layers')
        set_mute_action.triggered.connect(lambda: self.set_selected_muted_layers(item))
        rt_click_menu.addAction(set_mute_action)

        remove_mute_action = rt_click_menu.addAction('Un-Mute selected layers')
        remove_mute_action.triggered.connect(lambda: self.remove_selected_muted_layers(item))
        rt_click_menu.addAction(remove_mute_action)

        remove_mute_action = rt_click_menu.addAction('Edit multiple entries')
        remove_mute_action.triggered.connect(lambda: self.edit_multiple_entries())
        rt_click_menu.addAction(remove_mute_action)

        rt_click_menu.exec_(QtGui.QCursor.pos())

    def rt_click_anim_tree(self, pos):
        '''
        event for right click action

        @param pos: where the cursor is located
        @type pos: QPoint
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('rt_click_anim_tree')))

        item = self.ui.tre_animations.itemAt(pos)
        if item is not None:
            if item.whatsThis(0) == Identifiers.model_layer_str:
                self.create_character_menu(item)
            elif item.whatsThis(0) == Identifiers.animations_str:
                self.create_animation_menu(item)
        elif item is None:
            self.create_animation_tree_menu()

    """
    \/\/\/\/\/\/\/\/    Export rig    \/\/\/\/\/\/\/\/
    """

    def export_rig_layer(self, item):
        '''
        exports mesh child of rig

        @param item: model to export
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('export_rig')))

        out = 'During the rig export process this file will be saved do you wish to continue?'
        confirm = pm.confirmDialog(title='Rig export check', message=out, button=['Yes', 'No'], defaultButton='Yes',
                                   cancelButton='No')

        if self.framework_paths and confirm == 'Yes':
            root = self.ui.tre_rigs.invisibleRootItem()

            for tree_child in range(root.childCount()):
                layer_item = self.ui.tre_rigs.topLevelItem(tree_child)

                if layer_item.text(0) == item.text(0):
                    for model_item in range(layer_item.childCount()):
                        pm.refresh(suspend=True)
                        self.export_rig(layer_item.child(model_item))
                        pm.refresh(suspend=False)
        else:
            out = 'Please select a Project Trunk and try again'
            pm.confirmDialog(title='No Project Trunk', message=out, button=['OK'])

    def export_all_rigs(self):

        root = self.ui.tre_rigs.invisibleRootItem()
        for child in range(root.childCount()):
            self.export_rig_layer(root.child(child))

    def export_rig(self, item):
        """
        Exports individual rig by selecting the model and root nodes
        Export saves a temporary version of the rig file and flattens the model and root for the FBX
        After export the original file is opened and the temporary file is deleted

        :param item: the ui element of the rig to be exported
        :type item: QTreeWidgetItem
        :return:
        :rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('export_rig')))

        if self.framework_paths:
            for layer in self.rig_layers:
                if item.parent().text(0) == layer.name:
                    export_dir = self.get_export_directory(layer.rig_path)
                    for model in layer.models:
                        if item.text(0) == model.name:
                            over_weighted = self.test_influences(item, from_export=True)
                            if not over_weighted:
                                temp_save_name = self.get_rig_temp_path()
                                original_save_path = pm.sceneName()
                                if os.access(pm.sceneName(), os.W_OK):
                                    pm.saveFile()
                                    pm.saveAs(temp_save_name)
                                    for export_item in model.export_items:
                                        success = self.flatten_rig(export_item)
                                    if success:
                                        success = self.flatten_rig(layer.root)
                                        if success:
                                            used_models = model.export_items
                                            used_models.append(layer.root)

                                            self.clean_scene(used_models)
                                            success = self.Exporter.export_rig_setup(model.export_items, model.name, layer.root,
                                                                           export_dir)

                                            if success:
                                                pm.saveFile()
                                                pm.openFile(original_save_path)
                                                os.remove(temp_save_name)

                                                out = ('{} rig exported'.format(item.text(0)))
                                                self.logger.info(out)
                                                self.ui.lab_log.setText(out)
                                            else:
                                                out = ('{} rig export failed!'.format(item.text(0)))
                                                self.logger.error(out)
                                                self.ui.lab_log.setText(out)
                                else:
                                    out = ('Maya file is read-only, please checkout this Maya file')
                                    self.logger.error(out)
                                    self.ui.lab_log.setText(out)

                            else:
                                out = ('Export failed! There are over the max number of influences on {0}'.
                                       format(model.name))
                                self.logger.error(out)
                                self.ui.lab_log.setText(out)
        else:
            out = 'Please select a Project Trunk and try again'
            pm.confirmDialog(title='No Project Trunk', message=out, button=['OK'])

    @staticmethod
    def flatten_rig(node):
        '''
        set rig parent to world so the fbx is export flat instead of under a group or other node

        @param node: root node of rig
        @type node: joint
        @return:
        @rtype:
        '''
        if pm.objExists(node):
            pm.parent(node, world=True)
            return True
        else:
            print('{0} model not found to export'.format(node))
            return False

    def clean_scene(self, used_models):
        '''
        clean scene to get it ready for export to fbx. gets rid of stuff that is not to be exported

        @param used_models: models to be exports
        @type used_models: str
        @return:
        @rtype:
        '''

        if Debug.debug: print(('calling :: {0}'.format('clean_scene')))

        scene_transforms = pm.ls(assemblies=True)
        scene_parents = []
        for scene_transform in scene_transforms:
            parent = self.get_top_level_parent(scene_transform)
            scene_parents.append(parent)

        models = []
        for used_model in used_models:
            models.append(self.Exporter.remove_pipe(used_model))

        parents = []
        for scene_parent in scene_parents:
            if not type(scene_parent.getShape()) == pm.nodetypes.Camera:
                parents.append(self.Exporter.remove_pipe(scene_parent.name()))

        # remove any non joint nodes
        delete1 = []
        for parent in parents:
            parent_node = pm.ls(parent)[0]
            if type(parent_node) == pm.nodetypes.Joint:
                kid_nodes = pm.listRelatives(parent_node, allDescendents=True)
                for kid in kid_nodes:
                    if type(kid) != pm.nodetypes.Joint:
                        delete1.append(kid)

        delete2 = list(set(models).symmetric_difference(set(parents)))
        pm.delete(delete1, delete2)

    @staticmethod
    def get_rig_temp_path():
        '''
        locaton to save temp file which has been prepared for export

        @return:
        @rtype:
        '''

        prefix = Identifiers.rigs_str + '_' + str(random.randint(100, 999)) + '_'
        path_list = os.path.split(pm.sceneName())
        if path_list[0]:
            temp_save_name = prefix + path_list[1]
            return tempfile.gettempdir() + '\\' + temp_save_name
        else:
            print('Please save rig file to create a scene path')

    """
    \/\/\/\/\/\/\/\/    get influences    \/\/\/\/\/\/\/\/

    """

    def test_influences(self, item, from_export=False):
        '''
        controls the process of seeing if there are more then the max defined amount of influences on model verts

        @param item: mesh to test
        @type item: tree item
        @param from_export: whether the function is being called for export or just a test
        @type from_export:
        @return:
        @rtype:
        '''

        mesh = None
        max_influences = None

        for layer in self.rig_layers:
            for model in layer.models:
                if model.name == item.text(0):
                    if pm.objExists(model.name):
                        mesh = pm.ls(model.name)[0]
                        max_influences = int(model.influences)

        if mesh and max_influences:
            skin_cluster = self.get_skincluster(mesh)

            if skin_cluster:
                skinFn = self.get_MFnSkinCluster(skin_cluster)

                # get the MDagPath for all influence
                infDags = OpenMaya.MDagPathArray()
                skinFn.influenceObjects(infDags)

                # create a dictionary whose key is the MPlug indice id and
                # whose value is the influence list id
                infIds = {}
                infs = []
                for x in range(infDags.length()):
                    infPath = infDags[x].fullPathName()
                    infId = int(skinFn.indexForInfluenceObject(infDags[x]))
                    infIds[infId] = x
                    infs.append(infPath)

                weights = self.get_weights_dict(skinFn, infIds)

                over_weighted = []
                for x in weights.keys():
                    if len(weights[x]) > max_influences:
                        over_weighted.append(x)

                if over_weighted:
                    if not from_export:
                        out = ('{0} has {1} verts which have more than ({2}) influences. This rig will not export'.
                               format(mesh, len(over_weighted), max_influences))
                        self.logger.error(out)
                        self.ui.lab_log.setText(out)

                        [pm.select(mesh.vtx[x], add=True) for x in over_weighted]
                        pm.selectMode(component=True)
                        return []
                    else:
                        return over_weighted

    def get_skincluster(self, mesh):
        '''
        get the skin cluster for mesh arg

        @param mesh: mesh to get skin cluster for
        @type mesh: transform
        @return: skin cluster
        @rtype: skinCluster node
        '''
        for node in pm.listHistory(mesh):
            if type(node) == pm.nodetypes.SkinCluster:
                return node

    def get_MFnSkinCluster(self, skincluster):
        '''
        gets the MFnSkinCluster class from a given skin cluster

        @param skincluster: skin cluster
        @type skincluster: skinCluster
        @return:
        @rtype:
        '''

        # get the MFnSkinCluster for skinCluster
        selList = OpenMaya.MSelectionList()
        selList.add(skincluster.name())
        clusterNode = OpenMaya.MObject()
        selList.getDependNode(0, clusterNode)
        skinFn = OpenMayaAnim.MFnSkinCluster(clusterNode)
        return skinFn

    def get_weights_dict(self, skinFn, infIds):
        '''
        creates a dictionary with a vert id key and value of a dict whose key is the influence id and value is the
        weight for that influence

        @param skinFn: skin cluster
        @type skinFn: MFnSkinCluster
        @param infIds: dictionary whose key is the MPlug indice id and whose value is the influence list id
        @type infIds: dict
        @return: the weights are stored in dictionary, the key is the vert Id, the value is another dictionary whose
        key is the influence id and value is the weight for that influence
        @rtype: dict
        '''

        wlPlug = skinFn.findPlug('weightList')
        wPlug = skinFn.findPlug('weights')
        wlAttr = wlPlug.attribute()
        wAttr = wPlug.attribute()
        wInfIds = OpenMaya.MIntArray()

        weights = {}
        for vId in range(wlPlug.numElements()):
            vert_weights = {}
            # tell the weights attribute which vertex id it represents
            wPlug.selectAncestorLogicalIndex(vId, wlAttr)
            # get the indice of all non-zero weights for this vert
            wPlug.getExistingArrayAttributeIndices(wInfIds)
            # create a copy of the current wPlug
            infPlug = OpenMaya.MPlug(wPlug)
            for infId in wInfIds:
                # tell the infPlug it represents the current influence id
                infPlug.selectAncestorLogicalIndex(infId, wAttr)
                # add this influence and its weight to this verts weights
                try:
                    vert_weights[infIds[infId]] = infPlug.asDouble()
                except KeyError:
                    # assumes a removed influence
                    pass
            weights[vId] = vert_weights

        return weights

    # >>>>>>>>>>>>>>>>>>>>>>>>  generic ui functions <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#
    def remove_actors(self, items):
        '''
        removes actor from ui and data

        @param item: actor to remove
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('remove_actors')))

        for item in items:
            fbx_exporter_data.ExporterData.remove_key(Identifiers.actor_identifier + item.text(0))

        self.populate_anim_tree_ui()

    def add_actor_layer(self):
        '''
        adds selected (scene) actor to data

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('add_actor')))

        SelectUI = fbx_exporter_ui.SelectSomething(Identifiers.rig_layer_identifier)
        results = SelectUI.result
        to_add = pm.ls(results)
        for add in to_add:
            self.initialize_character_data(add)
            self.ExportData.write_anim_data_to_fileinfo(self.actors_layers)
            self.populate_anim_tree_ui()

    def remove_animations(self, items):
        '''
        removes anim from ui and data

        @param item: anim to remove
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('remove_animation')))

        for item in items:
            fbx_exporter_data.ExporterData.remove_animation(item)

        self.populate_anim_tree_ui()

    def add_animations(self, items):
        '''
        adds anim to given actor layer

        @param item: actor to add anim to
        @type item: tree item
        @return:
        @rtype:
        '''

        if Debug.debug: print(('calling :: {0}'.format('add_animation')))

        # lin_anim_name is the qt ui element that the user will enter the animation name
        if self.ui.lin_anim_name.text() != '':
            file_name = self.ui.lin_anim_name.text()

            for actor in self.actors_layers:
                for item in items:
                    if item.text(0) == actor.name:
                        animation_data = AnimationData()
                        actor.animations.append(animation_data)
                        animation_data.name = actor.name
                        animation_data.anim_name = file_name
                        animation_data.start_frame = str(int(pm.playbackOptions(q=True, minTime=True)))
                        animation_data.end_frame = str(int(pm.playbackOptions(q=True, maxTime=True)))
                        animation_data.path = actor.path

                        animation_data.override_path = ''

            self.ExportData.write_anim_data_to_fileinfo(self.actors_layers)
            self.populate_anim_tree_ui()

    def get_animlayers(self):
        """
        get all anim layers beside the Base layer

        @return: list of animation layers
        @rtype: list
        """

        if Debug.debug: print(('calling :: {0}'.format('get_animlayers')))

        if pm.animLayer(query=True, root=True):
            return pm.animLayer(pm.animLayer(q=True, root=True), q=True, children=True)
        else:
            return None

    def get_muted_layers(self):
        """
        gets all the muted anim layers

        @return: list of muted layers
        @rtype: list of str
        """

        muted = []

        anim_layers = self.get_animlayers()

        if anim_layers:
            for anim_layer in anim_layers:
                if pm.animLayer(anim_layer, query=True, mute=True):
                    muted.append(anim_layer.name())

            return muted
        else:
            return None

    def set_muted_layer(self, muted_layers):
        """
        get list of layers and mutes those layers

        @param muted_layers: list of muted layers
        @type muted_layers: list of str
        @return:
        @rtype:
        """

        kids = pm.animLayer(pm.animLayer(q=True, root=True), q=True, children=True)
        if kids:
            for kid in kids:
                if kid.name() in muted_layers:
                    pm.animLayer(kid.name(), edit=True, mute=True)
                else:
                    pm.animLayer(kid.name(), edit=True, mute=False)

    def export_animation(self, animation, layer):
        """
        sets up and exports a single animation

        @param animation: data for animation to be exported
        @type animation: AnimationData()
        @param layer: rig layer
        @type layer: ActorLayerData()
        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('export_animation')))

        # set time range for specific animation
        min = pm.playbackOptions(min=True, q=True)
        max = pm.playbackOptions(max=True, q=True)
        start = pm.playbackOptions(animationStartTime=True, q=True)
        end = pm.playbackOptions(animationEndTime=True, q=True)

        root = None

        # get joint name from root as root has namespace
        find_joint = layer.root.split(':')[-1]
        parent = self.get_top_level_parent(layer.root)
        # copy hierarchy to flatten
        copy = pm.duplicate(parent, rr=True, inputConnections=True)
        # get joints
        shapes = pm.listRelatives(copy, allDescendents=True, type='joint')
        # get root joint
        for shape in shapes:
            if shape.name() == find_joint:
                root = shape
                break

        # get export path...there might be an override path
        if animation.override_path is None:
            export_dir = self.get_export_directory(animation.path)
        else:
            export_dir = self.get_export_directory(animation.override_path)

        # get the layers that are muted before making any changes for anim export
        muted_layers = self.get_muted_layers()

        if muted_layers:
            # turn off layers that have been added to data as being muted
            if animation.muted_layers:
                mutes = animation.muted_layers.split(', ')
                for mute in mutes:
                    pm.animLayer(mute, mute=True, edit=True)

        if root:
            pm.parent(root, world=True)
            pm.delete(copy)
            self.Exporter.export_animation_setup(animation.anim_name, export_dir,
                                                 animation.start_frame, animation.end_frame)
            pm.delete(root)

            pm.playbackOptions(animationStartTime=start, animationEndTime=end)
            pm.playbackOptions(min=min, max=max)
        else:
            print('Rig root was not found')

        if muted_layers:
            self.set_muted_layer(muted_layers)

    def edit_multiple_entries(self):
        '''
        currently just called from context menu. looks at last clicked column and determines which values in an
        animation needs to be updated. Once the values are determined all of the selected animation items are updated
        with that value

        one thing that should be noted it that first class function, with the same arg signature, are assigned in
        conditional statements then run on each selected item in a for loop

        @return:
        @rtype:
        '''

        column = None
        new_val = None
        func = None

        # get common data for all selected items based on the last registered column
        if self.anim_column_clicked == 1:
            new_val = self.Browsers.open_prompt_dialog('Entry field for multiple edit', 'Enter Start Frame')
            if new_val.isdigit():
                func = self.ExportData.change_start_end_frame
                column = 1
            else:
                pm.confirmDialog(title='Input error', message='Try again with an integer', button=['OK'])
                self.edit_multiple_entries()

        if self.anim_column_clicked == 2:
            new_val = self.Browsers.open_prompt_dialog('Entry field for multiple edit', 'Enter End Frame')
            if new_val.isdigit():
                func = self.ExportData.change_start_end_frame
                column = 2
            else:
                pm.confirmDialog(title='Input error', message='Try again with an integer', button=['OK'])
                self.edit_multiple_entries()

        if self.anim_column_clicked == 4:
            new_val = self.get_path(self.framework_paths)
            if not new_val:
                new_val = ''

            func = self.ExportData.change_override_path
            column = 4

        # populate selected items fields with data from above
        if None not in (column, new_val, func):
            selected = self.get_selected_items_from_active_tab()
            for select in selected:
                func(select, new_val, column)

            self.populate_anim_tree_ui()

    def set_maya_to_data_range(self, item):
        '''
        calls export data module to set mayas time range to given item

        @param item: animation item
        @type item: tree item
        @return:
        @rtype:
        '''

        if Debug.debug: print(('calling :: {0}'.format('set_maya_range_to_data')))

        self.ExportData.set_maya_to_data_range(item)
        self.populate_anim_tree_ui()

    def remove_selected_muted_layers(self, item):
        """
        removed muted layer data for animation

        @param item: animation item
        @type item: tree widget item
        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('set_muted_layers')))

        self.ExportData.remove_selected_animlayers(item)
        self.populate_anim_tree_ui()

    def set_selected_muted_layers(self, item):
        """
        set muted data for animation

        @param item: animation item
        @type item: tree widget item
        @return:
        @rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('set_muted_layers')))

        self.ExportData.set_selected_animlayers(item)
        self.populate_anim_tree_ui()

    """
    \/\/\/\/\/\/\/\/    Rig UI    \/\/\/\/\/\/\/\/
    """

    def clear_rig_tree_ui(self):
        '''
        removes existing data from tree

        @return:
        @rtype:
        '''
        self.ui.tre_rigs.clear()

    def remove_rig_model(self, item):
        '''
        call exporter data class to remove model from rig layer

        @param item: model item to remove
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('remove_rig')))

        items = self.get_selected_items_from_active_tab()
        for item in items:
            fbx_exporter_data.ExporterData.remove_rig_model(item)
        self.populate_rig_tree_ui()

    def remove_rig(self, item):
        '''
        calls exporter data class to remove rig layer from data

        @param item: rig to remove
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('remove_rig')))

        fbx_exporter_data.ExporterData.remove_key(Identifiers.rig_layer_identifier + item.text(0))
        self.populate_rig_tree_ui()

    def add_rig_attr(self, rig):
        '''
        adds attributes to rig to be used to populate animation exporter

        @param rig: parent group that contains the root joint for the rig
        @type rig: group transform
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('add_rig_attr')))

        if not rig.hasAttr(Identifiers.rig_identifier):
            rig.addAttr(Identifiers.rig_identifier, attributeType=bool)
            rig.setAttr(Identifiers.rig_identifier, 1)

        if not rig.hasAttr(Identifiers.animation_path_str):
            rig.addAttr(Identifiers.animation_path_str, dataType='string')

        if not rig.hasAttr(Identifiers.root_str):
            rig.addAttr(Identifiers.root_str, dataType='string')

    def get_top_level_parent(self, root):
        '''
        gets top level parent of root joint

        @param root: rig root
        @type root: joint
        @return: rig group parent
        @rtype: group transform
        '''
        if Debug.debug: print(('calling :: {0}'.format('get_root_parent')))

        parents = pm.listRelatives(root, allParents=True)
        if parents:
            parent = parents[0]
            return self.get_top_level_parent(parent)
        else:
            return root

    def add_multiple_rig_model(self, layer_name):
        '''
        event for adding multiple models as seperate models in the rig layer

        @param layer_name: name of rig layer to add models to
        @type layer_name: str
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('add_rig_model')))

        add_models = []
        trans = pm.ls(selection=True)
        if trans:
            for tran in trans:
                if self.FbxExporter.is_group(tran):
                    add_models.append(tran.name())
                else:
                    shape = tran.getShape()
                    if shape.nodeType() == 'mesh':
                        add_models.append(tran.name())

        if add_models:
            for rig in self.rig_layers:
                if rig.name == layer_name:
                    for model in add_models:
                        # set1 = set(rig.models)
                        # set2 = set(add_models)
                        # rig.models = list(set1.union(set2))
                        model_data = RigModelData()
                        model_data.name = model
                        model_data.uuid = self.FbxExporter.get_uuid(model)
                        model_data.path = rig.rig_path
                        model_data.influences = 0
                        model_data.export_items.append(model)
                        rig.models.append(model_data)

                    self.ExportData.write_rig_data_to_fileinfo(self.rig_layers)
                    self.populate_rig_tree_ui()

    def remove_model_export_item(self, item):
        '''
        removes model data from rig layer and calls to update tree

        @param item: model to remove
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('add_model_export_item')))

        remove_models = []
        trans = pm.ls(selection=True)
        if trans:
            for tran in trans:
                if self.FbxExporter.is_group(tran):
                    remove_models.append(tran.name())
                else:
                    shape = tran.getShape()
                    if shape.nodeType() == 'mesh':
                        remove_models.append(tran.name())

        updated = False
        if remove_models:
            for rig in self.rig_layers:
                if rig.name == item.parent().text(0):
                    for model in rig.models:
                        if item.text(0) == model.name:
                            for remove_model in remove_models:
                                if remove_model in model.export_items:
                                    model.export_items.remove(remove_model)
                                    updated = True

        if updated:
            self.ExportData.write_rig_data_to_fileinfo(self.rig_layers)
            self.populate_rig_tree_ui()

    def add_model_export_item(self, item):
        '''
        called by event to add model to export item list for model in a rig layer

        @param item: model item to add model to
        @type item: tree item
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('add_model_export_item')))

        add_models = []
        trans = pm.ls(selection=True)
        if trans:
            for tran in trans:
                if self.FbxExporter.is_group(tran):
                    add_models.append(tran.name())
                else:
                    shape = tran.getShape()
                    if shape.nodeType() == 'mesh':
                        add_models.append(tran.name())

        updated = False
        if add_models:
            for rig in self.rig_layers:
                if rig.name == item.parent().text(0):
                    for model in rig.models:
                        if item.text(0) == model.name:
                            set1 = set(model.export_items)
                            set2 = set(add_models)
                            model.export_items = list(set1.union(set2))
                            updated = True

        if updated:
            self.ExportData.write_rig_data_to_fileinfo(self.rig_layers)
            self.populate_rig_tree_ui()

    def get_export_directory(self, path):
        """
        returns export directory for models and layers

        @param path: path
        @type path: str
        @return: export directory for animation or rig
        @rtype: str
        """
        if Debug.debug: print(('calling :: {0}'.format('get_export_dir')))

        if path:
            if os.path.isdir(path):
                return path
            else:
                export_dir = self.framework_paths + '\\' + path
                if os.path.isdir(export_dir):
                    return export_dir
                elif os.path.isdir(self.framework_paths):
                    return self.framework_paths
                else:
                    print('Project path does not exist. Reverting broswer to Maya user path')
                    return pm.workspace.getPath()

        else:
            out = 'There is no export rig path set, Please set a path for the export layer and try again.'
            pm.confirmDialog(title='No export layer path found', message=out, button=['OK'])
            return None

    def open_path_folder(self, item):
        """
        right click call to open file browser where fbx lives for tree item

        :param item: model or layer item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('open_path_folder')))

        open_path = self.get_folder_path(item)
        path = self.Browsers.get_open_filename('Layer file path', open_path, '*.*')
        if path:
            os.startfile(path)

    def get_folder_path(self, item):
        """
        right click call to open file browser where fbx lives for tree item

        :param item: model or layer item
        :type item: QTreeWidgetItem
        """
        if Debug.debug: print(('calling :: {0}'.format('open_path_folder')))

        if item.whatsThis(0) == Identifiers.rig_layer_identifier:
            for rig in self.rig_layers:
                if rig.name == item.text(0):
                    print('rig.name :: {}'.format(rig.name))
                    if rig.rig_path is None:
                        rig.rig_path = self.framework_paths
                    if rig.animation_path is None:
                        rig.animation_path = self.framework_paths
                    export_dir = self.get_export_directory(rig.rig_path)
                    return export_dir
        elif item.whatsThis(0) == Identifiers.models_str:
            for layer in self.model_layers:
                for model in layer.models:
                    if model.name == item.text(0):
                        print('model.name :: {}'.format(model.name))
        elif item.whatsThis(0) == Identifiers.model_layer_str:
            for layer in self.actors_layers:
                for animation in layer.animations:
                    if animation.name == item.text(0):
                        print('animation.name :: {}'.format(animation.name))

    def update_anim_path_attr(self, model, path):
        '''
        calls to add animation path to model attribute

        @param model: model to add attr to
        @type model: mesh node
        @param path: animation path
        @type path: str
        @return:
        @rtype:
        '''
        if model.hasAttr(Identifiers.animation_path_str):
            model.setAttr(Identifiers.animation_path_str, path)
        else:
            self.add_rig_attr(model)
            self.update_anim_path_attr(model, path)

    def update_rig_anim_path(self, item, path):
        '''
        updates anim path on change event

        @param item: rig item
        @type item: tree item
        @param path: animation path
        @type path: str
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('update_rig_anim_path')))

        for rig in self.rig_layers:
            if rig.name == item.text(0):
                model = pm.ls(rig.export_items[0])[0]
                self.update_anim_path_attr(model, path)


class ModelExportUI(QtWidgets.QDialog):

    def __init__(self, item, type):
        super(ModelExportUI, self).__init__()
        # ExportUtils = ExportUtilities()

        ui_path = os.path.join(scr.framework_paths['tool_path'], 'fbxexporters', 'model_export_options.ui')
        self.ui = QtUiTools.QUiLoader().load(ui_path)
        self.item = item
        self.result = self.item
        self.type = type

        self.FbxExporter = scr.framework.ToolHelpers()
        self.ExportData = fbx_exporter_data.ExporterData

        # properties unique to layers
        if self.type == Identifiers.model_layer_str:
            self.ui.ckb_fbx_export_override_path.setEnabled(False)
            self.ui.ckb_fbx_export_override_options.setEnabled(False)

        # properties shared across models and layers
        self.ui.ckb_fbx_export_override_path.stateChanged.connect(self.override_path_changed)
        self.ui.ckb_fbx_export_override_options.stateChanged.connect(self.override_options_changed)
        self.ui.ckb_fbx_export_smoothing_groups.stateChanged.connect(self.smoothing_groups_changed)
        self.ui.ckb_fbx_export_split_normals.stateChanged.connect(self.split_normals_changed)
        self.ui.ckb_fbx_export_tangents.stateChanged.connect(self.tangents_changed)
        self.ui.ckb_fbx_export_smooth_mesh.stateChanged.connect(self.smooth_mesh_changed)
        self.ui.ckb_fbx_export_triangulate.stateChanged.connect(self.triangulate_changed)
        self.ui.ckb_fbx_export_animation_only.stateChanged.connect(self.animation_only_changed)
        self.ui.ckb_fbx_export_instances.stateChanged.connect(self.export_instances_changed)
        self.ui.ckb_fbx_export_zero.stateChanged.connect(self.export_zero_changed)
        self.ui.btn_ok.clicked.connect(self.btn_ok_clicked)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_clicked)

        self.initialize_checkboxes()

    def btn_ok_clicked(self):
        """
         event triggered by OK button clicked
         assigns result to be used by function that opened ui
        """
        self.result = self.item
        self.ui.accept()

    def btn_cancel_clicked(self):
        """
         event triggered by Cancel button clicked
         closes ui
        """
        self.ui.reject()

    def initialize_checkboxes(self):
        """
        initializes all the checkboxs for ui
        """

        # # properties unique to layers
        # # these are depricated
        # if self.type == Identifiers.model_layer_str:
        #     self.ui.ckb_fbx_export_override_path.setChecked(self.item.fbx_export_override_path)
        #     self.ui.ckb_fbx_export_override_options.setChecked(self.item.fbx_export_override_options)

        if self.type == Identifiers.models_str:
            self.ui.ckb_fbx_export_override_path.setChecked(self.item.fbx_export_override_layer_path)
            self.ui.ckb_fbx_export_override_options.setChecked(self.item.fbx_export_override_layer_options)

        # properties shared across models and layers
        self.ui.ckb_fbx_export_smoothing_groups.setChecked(self.item.fbx_export_smoothing_groups)
        self.ui.ckb_fbx_export_split_normals.setChecked(self.item.fbx_export_hard_edges)
        self.ui.ckb_fbx_export_tangents.setChecked(self.item.fbx_export_tangents)
        self.ui.ckb_fbx_export_smooth_mesh.setChecked(self.item.fbx_export_smooth_mesh)
        self.ui.ckb_fbx_export_animation_only.setChecked(self.item.fbx_export_animation_only)
        self.ui.ckb_fbx_export_instances.setChecked(self.item.fbx_export_instances)
        self.ui.ckb_fbx_export_zero.setChecked(self.item.fbx_export_zero)
        self.ui.ckb_fbx_export_triangulate.setChecked(self.item.fbx_export_triangulate)

    def override_path_changed(self):
        """
         event triggered by override path box statechanged
        """

        if not self.item.path:
            start_path = scr.framework_paths['project_path']
            path = self.Browsers.open_save_folder_browser('Model file path', start_path)

            if path:
                path = self.FbxExporter.get_relative_path(path)
                self.item.path = path

        if self.type == Identifiers.models_str:
            self.item.fbx_export_override_layer_path = self.ui.ckb_fbx_export_override_path.isChecked()

    def override_options_changed(self):
        """
         event triggered by override options box statechanged
        """
        self.item.fbx_export_override_layer_options = self.ui.ckb_fbx_export_override_options.isChecked()

    def smoothing_groups_changed(self):
        """
         event triggered by smoothing box statechanged
        """
        self.item.fbx_export_smoothing_groups = self.ui.ckb_fbx_export_smoothing_groups.isChecked()

    def split_normals_changed(self):
        """
         event triggered by split normal box statechanged
        """
        self.item.fbx_export_hard_edges = self.ui.ckb_fbx_export_split_normals.isChecked()

    def tangents_changed(self):
        """
         event triggered by tangents box statechanged
        """
        self.item.fbx_export_tangents = self.ui.ckb_fbx_export_tangents.isChecked()

    def smooth_mesh_changed(self):
        """
         event triggered by smooth mesh box statechanged
        """
        self.item.fbx_export_smooth_mesh = self.ui.ckb_fbx_export_smooth_mesh.isChecked()

    def triangulate_changed(self):
        """
         event triggered by triangulate box statechanged
        """
        self.item.fbx_export_triangulate = self.ui.ckb_fbx_export_triangulate.isChecked()

    def animation_only_changed(self):
        """
         event triggered by animation only box statechanged
        """
        self.item.fbx_export_animation_only = self.ui.ckb_fbx_export_animation_only.isChecked()

    def export_instances_changed(self):
        """
         event triggered by export instances box statechanged
        """
        self.item.fbx_export_instances = self.ui.ckb_fbx_export_instances.isChecked()

    def export_zero_changed(self):
        """
         event triggered by export zero box statechanged
        """
        self.item.fbx_export_zero = self.ui.ckb_fbx_export_zero.isChecked()


# global ModelExportUI
ModelExporterUI = None

global Controls_UI
Controls_UI = None


def initialize_module():
    """
    initializes CharacterExporterUI so data is refreshed
    ...used to regenerate ui on file open callback
    """

    CharacterExporterUI = FbxCharacterExporterUI()
    CharacterExporterUI.run()


Controls_UI = FbxCharacterExporterUI()


class SelectSomething(QtWidgets.QMainWindow):

    def __init__(self, find_what):
        maya_main = self.get_maya_main_window()
        super(SelectSomething, self).__init__(maya_main)
        # ExportUtils = ExportUtilities()

        ui_path = os.path.join(scr.framework_paths['tool_path'], 'fbxexporters', 'fselect_something.ui')
        self.ui = self.load_ui(ui_path, maya_main)
        self.ui.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.ui.lst_add_objects.itemDoubleClicked.connect(self.item_doubleClicked)
        self.ui.btn_ok.clicked.connect(self.btn_ok_clicked)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_clicked)
        self.ExportData = fbx_exporter_data.ExporterData
        self.find_what = find_what
        self.result = []
        self.mesh = 'mesh'

        self.get_valid_objects()
        self.run()

    def run(self):
        """
        opens ui, probably called from user request in SG Tools drop down
        """
        self.ui.exec_()

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

    def item_doubleClicked(self):
        self.get_selected_objects()
        self.ui.accept()

    def btn_ok_clicked(self):
        self.get_selected_objects()
        self.ui.accept()

    def btn_cancel_clicked(self):
        self.ui.reject()

    def get_selected_objects(self):
        for item in self.ui.lst_add_objects.selectedItems():
            self.result.append(item.text())

    # def test_valid_object(self, tran):
    #     if Debug.debug : print(('calling :: {0}'.format('test_valid_object')))
    #
    #     print('\nget_valid_objects\n')
    #
    #     test = False
    #
    #     if self.find_attr_name == Identifiers.model_identifier:
    #         shape = tran.getShape()
    #         if shape is not None:
    #             if shape.nodeType() == self.mesh and not self.ExportData.object_in_data(tran.name(),
    #                                                                                     self.find_attr_name):
    #                 test = True
    #     elif self.find_attr_name == Identifiers.rig_layer_identifier:
    #         if tran.hasAttr(self.find_attr_name) and not self.ExportData.object_in_data(tran.name(),
    #                                                                                     self.find_attr_name):
    #             test = True
    #     elif self.find_attr_name == Identifiers.actor_identifier:
    #         if tran.hasAttr(self.find_attr_name) and not self.ExportData.object_in_data(tran.name(),
    #                                                                                     self.find_attr_name):
    #             test = True
    #
    #     return test

    def get_valid_objects(self):
        if Debug.debug : print(('calling :: {0}'.format('get_valid_object')))

        print('\nget_valid_objects\n find_what :: {0}'.format(self.find_what))

        if self.find_what == Identifiers.rig_layer_identifier:
            joints = pm.ls(exactType='joint')
            for j in joints:
                if not pm.listRelatives(j, type='joint', parent=True):
                    if j.hasAttr('_fbx_export_rig_'):
                        print(' joint :: {0}'.format(j))
                        self.ui.lst_add_objects.addItem(j.name())

        # if self.find_what == Identifiers.rig_layer_identifier:
        #     trans = pm.ls(tr=True)
        #     for tran in trans:
        #         if self.test_valid_object(tran):
        #             self.ui.lst_add_objects.addItem(tran.name())





