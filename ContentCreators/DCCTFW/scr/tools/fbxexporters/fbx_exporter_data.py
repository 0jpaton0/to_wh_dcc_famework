import os
import glob
import pymel.core as pm
from xml.etree import ElementTree as ET
from xml.dom import minidom
from distutils.util import strtobool
import logging
import tempfile
from pathlib import Path

from scr.tools.fbxexporters import AnimationData
from scr.tools.fbxexporters import ActorLayerData
from scr.tools.fbxexporters import RigLayerData
from scr.tools.fbxexporters import RigModelData
from scr.tools.fbxexporters import ModelData
from scr.tools.fbxexporters import LayerData
from scr.tools.fbxexporters import UserOptionsData
from scr.tools.fbxexporters import Identifiers
from scr.tools.fbxexporters import Debug


class FBXExporterData(object):

    def __init__(self):
        pass

    def check_exists_layer(self, layer_name):
        """
        check to see if layer already exist in data (fileInfo)

        :param layer_name: name of layer
        :type layer_name: str
        :return: found
        :rtype: bool
        """
        if Debug.debug: print(('calling  :: {0}'.format('check_exists_layer')))

        found = False
        model_layers_fileInfo = self.get_valid_keys_from_fileInfo(layer_name)
        if len(model_layers_fileInfo) > 0:
            found = True

        return found

    def export_animation(self, animation):
        """
        WIP
        :param animation:
        :type animation:
        :param char_identifier:
        :type char_identifier:
        :return:
        :rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('export_animation')))

        print('\nexport_animation\n animation :: {0}'.format(animation))

        # char_name = animation.parent().text(0)
        # anim_name = animation.text(0)
        # anim_path = animation.text(3)
        #
        # val = pm.fileInfo[char_identifier + char_name]
        # anims = val.split(self.separator)

    def remove_rig_model(self, item):
        """
        removes model from fileInfo

        :param item: model tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug : print(('calling :: {0}'.format('remove_model')))

        layer_member = None
        model_member = None
        layers = self.build_class_from_data(Identifiers.rig_layer_identifier)
        for layer in range(len(layers)):
            if item.parent().text(0) == layers[layer].name:
                layer_member = layer
                for mod in range(len(layers[layer].models)):
                    if item.text(0) == layers[layer].models[mod].name:
                        model_member = mod

        layers[layer_member].models.pop(model_member)
        self.write_rig_data_to_fileinfo(layers)

    def remove_model(self, item):
        """
        removes model from fileInfo

        :param item: model tree item
        :type item: QTreeWidgetItem
        """
        if Debug.debug : print(('calling :: {0}'.format('remove_model')))

        layer_member = None
        model_member = None
        layers = self.build_class_from_data(Identifiers.model_layer_identifier)
        for layer in range(len(layers)):
            if item.parent().text(0) == layers[layer].name:
                layer_member = layer
                for mod in range(len(layers[layer].models)):
                    if item.text(0) == layers[layer].models[mod].name:
                        model_member = mod

        layers[layer_member].models.pop(model_member)
        self.write_model_layer_data_to_fileinfo(layers)

    def remove_animation(self, item):
        """
        WIP
        :param item:
        :type item:
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('remove_animation')))

        char_member = None
        anim_member = None
        chars = self.build_class_from_data(Identifiers.actor_identifier)
        for char in range(len(chars)):
            if item.parent().text(0) == chars[char].name:
                char_member = char
                for anim in range(len(chars[char].animations)):
                    if item.text(0) == chars[char].animations[anim].anim_name:
                        anim_member = anim

        chars[char_member].animations.pop(anim_member)
        self.write_anim_data_to_fileinfo(chars)

    def remove_key(self, key_name):
        """
        removes element from fileInfo

        :param key_name: name of key for fileInfo dict
        :type key_name: str
        """
        if Debug.debug: print(('calling :: {0}'.format('remove_character')))

        if key_name in pm.fileInfo:
            import maya.cmds as cmds
            cmds.fileInfo(rm=key_name)

    def object_in_data(self, name, find_attr_name):
        """
        WIP
        :param name:
        :type name:
        :param find_attr_name:
        :type find_attr_name:
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('object_in_data')))
        out = False

        if (find_attr_name + name) in list(pm.fileInfo.keys()):
            out = True

        return out

    def trigger_save(self):
        """
        creates artificial event so maya file can be saved
        """
        if Debug.debug : print(('calling :: {0}'.format('trigger_save')))

        delete_me = pm.polyCube()
        pm.delete(delete_me)

    def create_rig_layer_xml(self, rig):
        """
        WIP
        :param rig:
        :type rig:
        :return:
        :rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('format_rig_string')))

        root = ET.Element("root")
        rig_attr = {'node_type': Identifiers.rigs_str}
        models_attr = {'node_type': Identifiers.models_str}
        model_attr = {'node_type': Identifiers.model_str}

        doc = ET.SubElement(root, Identifiers.rigs_str, attrib=rig_attr)
        meshes = ET.SubElement(doc, Identifiers.models_str, attrib=models_attr)
        ET.SubElement(doc, 'name').text = rig.name
        ET.SubElement(doc, 'model_name').text = rig.model_name
        ET.SubElement(doc, 'root').text = rig.root
        ET.SubElement(doc, 'rig_path').text = rig.rig_path
        ET.SubElement(doc, 'animation_path').text = rig.animation_path
        ET.SubElement(doc, 'uuid').text = rig.uuid

        s = ', '
        ET.SubElement(doc, 'export_items').text = s.join(rig.export_items)

        if rig.models:
            for model in rig.models:
                rig_model = ET.SubElement(meshes, Identifiers.model_str, attrib=model_attr)
                ET.SubElement(rig_model, "name").text = model.name
                ET.SubElement(rig_model, "uuid").text = model.uuid
                ET.SubElement(rig_model, "path").text = model.path
                ET.SubElement(rig_model, "influences").text = str(model.influences)

                s = ', '
                ET.SubElement(rig_model, 'export_items').text = s.join(model.export_items)

        return minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    def create_actor_layer_xml(self, char):
        """
        WIP
        :param char:
        :type char:
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('create_actor_xml')))

        root = ET.Element("root")
        actor_attr = {'node_type': 'actor'}
        anim_attr = {'node_type': 'animation'}
        anims_attr = {'node_type': 'animations'}

        doc = ET.SubElement(root, Identifiers.model_layer_str, attrib=actor_attr)
        animations = ET.SubElement(doc, Identifiers.animations_str, attrib=anims_attr)
        ET.SubElement(doc, 'name').text = char.name
        ET.SubElement(doc, 'anim_path').text = char.path
        ET.SubElement(doc, 'root').text = char.root

        s = ', '
        ET.SubElement(doc, 'export_items').text = s.join(char.export_items)

        for anim in char.animations:
            animation = ET.SubElement(animations, 'animation', attrib=anim_attr)
            ET.SubElement(animation, "animation_name").text = anim.anim_name
            ET.SubElement(animation, "path").text = anim.path
            ET.SubElement(animation, "override_path").text = anim.override_path
            ET.SubElement(animation, "start").text = anim.start_frame
            ET.SubElement(animation, "end").text = anim.end_frame
            ET.SubElement(animation, "muted").text = anim.muted_layers

        return minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    def create_model_layer_xml(self, model_layer):
        """
        creates model layer xml data based on data in arg model_layer

        :param model_layer: model layer data from fileinfo
        :type model_layer: LayerData()
        :return: string
        :rtype: prettyXML formated string
        """
        if Debug.debug : print(('calling :: {0}'.format('create_model_layer_xml')))

        root = ET.Element("root")
        doc = ET.SubElement(root, Identifiers.model_layer_str)
        models = ET.SubElement(doc, Identifiers.models_str)

        ET.SubElement(doc, 'name').text = model_layer.name
        ET.SubElement(doc, 'path').text = model_layer.path
        ET.SubElement(doc, 'fbx_export_override_path').text = str(model_layer.fbx_export_override_path)
        ET.SubElement(doc, 'fbx_export_override_options').text = str(model_layer.fbx_export_override_options)
        ET.SubElement(doc, "fbx_export_smoothing_groups").text = str(model_layer.fbx_export_smoothing_groups)
        ET.SubElement(doc, "fbx_export_hard_edges").text = str(model_layer.fbx_export_hard_edges)
        ET.SubElement(doc, "fbx_export_tangents").text = str(model_layer.fbx_export_tangents)
        ET.SubElement(doc, "fbx_export_smooth_mesh").text = str(model_layer.fbx_export_smooth_mesh)
        ET.SubElement(doc, "fbx_export_animation_only").text = str(model_layer.fbx_export_animation_only)
        ET.SubElement(doc, "fbx_export_instances").text = str(model_layer.fbx_export_instances)
        ET.SubElement(doc, "fbx_export_zero").text = str(model_layer.fbx_export_zero)
        ET.SubElement(doc, "fbx_export_triangulate").text = str(model_layer.fbx_export_triangulate)

        for mod in model_layer.models:
            model = ET.SubElement(models, Identifiers.model_str)
            ET.SubElement(model, "name").text = mod.name
            ET.SubElement(model, "uuid").text = mod.uuid
            ET.SubElement(model, "path").text = mod.path

            s = ', '
            ET.SubElement(model, "export_items").text = s.join(mod.export_items)

            #export options
            ET.SubElement(model, "fbx_export_override_layer_options").text = str(mod.fbx_export_override_layer_options)
            ET.SubElement(model, "fbx_export_override_layer_path").text = str(mod.fbx_export_override_layer_path)
            ET.SubElement(model, "fbx_export_smoothing_groups").text = str(mod.fbx_export_smoothing_groups)
            ET.SubElement(model, "fbx_export_hard_edges").text = str(mod.fbx_export_hard_edges)
            ET.SubElement(model, "fbx_export_tangents").text = str(mod.fbx_export_tangents)
            ET.SubElement(model, "fbx_export_smooth_mesh").text = str(mod.fbx_export_smooth_mesh)
            ET.SubElement(model, "fbx_export_animation_only").text = str(mod.fbx_export_animation_only)
            ET.SubElement(model, "fbx_export_instances").text = str(mod.fbx_export_instances)
            ET.SubElement(model, "fbx_export_zero").text = str(mod.fbx_export_zero)
            ET.SubElement(model, "fbx_export_triangulate").text = str(mod.fbx_export_triangulate)

        # return minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
        return ET.tostring(root)

    def write_model_layer_data_to_fileinfo(self, model_layers):
        """
        write xml data to fileinfo

        :param model_layers: changed layer data from fileinfo
        :type model_layers: [LayerData()]
        """
        if Debug.debug : print(('calling :: {0}'.format('write_model_layer_data_to_fileinfo')))

        for model_layer in model_layers:

            models_string = self.create_model_layer_xml(model_layer)
            fileInfo_key = Identifiers.model_layer_identifier + model_layer.name
            pm.fileInfo[fileInfo_key] = models_string

            self.trigger_save()

    def read_fileInfo_xml_from_disk(self):

        open_directory = self.get_xml_directory()

        layers = []

        files = glob.glob(open_directory[0] + '*' + '.xml')
        for file_path in files:
            if open_directory[1] + '.' in file_path:
                layer_name = file_path.split('.')[1]
                opened_file = open(file_path)
                lines = opened_file.read()
                opened_file.close()

                layers.append(self.populate_models_classes_from_string(lines, Identifiers.model_layer_identifier + layer_name))

                # print('\nread_fileInfo_xml_from_disk\n layer :: {0}'.format(layer))
        return layers

    def get_xml_directory(self, append_save_path):

        file_path = pm.sceneName()
        file_name = os.path.basename(file_path)
        raw_name, extension = os.path.splitext(file_name)
        save_directory = pm.workspace.getPath() + append_save_path
        save_directory + raw_name

        return [save_directory, raw_name]

    @staticmethod
    def test_create_directory(directory):
        """
        test if directory exists, if it does not it is created

        :param directory: directory path
        """

        if not os.path.isdir(directory):
            os.makedirs(directory)

    def export_xml(self):
        '''
        export xml data from fileInfo
        '''

        file_name = Path(pm.sceneName()).stem + '.xml'
        key = self.get_valid_keys_from_fileInfo('_fbx_export_')
        print('key :: {}'.format(key))
        if key:
            rig_value = pm.fileInfo[key]
            rig_value = rig_value.encode().decode('unicode-escape')

            xml_path = os.path.join(tempfile.gettempdir(), file_name)
            with open(xml_path, 'w') as f:
                f.write(rig_value)

            out = ('XML file exported to {}'.format(xml_path))
            self.logger.info(out)
            self.ui.lab_log.setText(out)

    def import_xml(self):

        xml_path = self.Browsers.open_save_file_browser('Pick xml file to import', tempfile.gettempdir(), '*.xml')
        if xml_path:
            with open(xml_path, 'r') as f:
                xml_string = f.read()

        if xml_string:
            print('{}'.format(xml_string))

    def write_user_option_data_to_prefs(self, users_options):
        """
        write user options xml data to fileinfo

        :param users_options: data from Options drop down (ui.men_options)
        :type users_options: UserOptionsData()
        """
        if Debug.debug : print(('calling :: {0}'.format('write_user_option_data_to_prefs')))

        # hack getting rid of sg_prefUtils

        # prefs = sg_prefUtils.readPrefs()
        # export_options = {}
        # export_options[Identifiers.auto_select_in_scene] = users_options.auto_select_in_scene
        # export_options[Identifiers.save_to_disk] = users_options.save_to_disk
        # export_options[Identifiers.active_tab] = users_options.active_tab
        # prefs[Identifiers.options_str] = export_options
        # sg_prefUtils.writePrefs(prefs, [Identifiers.options_str])

        self.trigger_save()

    def write_anim_data_to_fileinfo(self, chars):
        """
        WIP
        :param chars:
        :type chars:
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('write_anim_data_to_fileinfo')))

        for char in chars:
            anim_string = self.create_actor_layer_xml(char)
            fileInfo_key = Identifiers.actor_identifier + char.name
            pm.fileInfo[fileInfo_key] = anim_string

            self.trigger_save()

    def write_rig_data_to_fileinfo(self, rigs):
        """
        WIP
        :param rigs:
        :type rigs:
        :param rig_layer_identifier:
        :type rig_layer_identifier:
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('write_rig_data_to_fileinfo')))

        for rig in rigs:
            rig_string = self.create_rig_layer_xml(rig)
            fileInfo_key = Identifiers.rig_layer_identifier + rig.name
            pm.fileInfo[fileInfo_key] = rig_string

            self.trigger_save()

    def write_rig_fileinfo_to_disk(self, rigs):
        '''
        placeholder for turn ten test

        :param rigs:
        :type rigs:
        :return:
        :rtype:
        '''
        out = ''

        print('here')

        for rig in rigs:
            print('rig :: {}'.format(rig))
            fileInfo_key = Identifiers.rig_layer_identifier + rig.name
            out = pm.fileInfo[fileInfo_key]

        return out


    def populate_actors_classes(self, key):
        """
        WIP
        :param key:
        :type key:
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('populate_actors_classes')))

        char_data = ActorLayerData()

        if pm.fileInfo[key] != '':
            anim_value = pm.fileInfo[key]
            anim_value = anim_value.encode().decode('unicode-escape')
            root = ET.fromstring(anim_value)
            actor = root.find(Identifiers.model_layer_str)
            char_data.name = key.replace(Identifiers.actor_identifier, '')
            char_data.path = actor.find('anim_path').text
            char_data.root = actor.find('root').text
            export_items = actor.find('export_items').text
            char_data.export_items.append(export_items)

            anims = actor.findall('./animations/animation')
            for anim in anims:
                anim_data = AnimationData()
                char_data.animations.append(anim_data)
                anim_data.name = actor.find('name').text
                anim_data.anim_name = anim.find('animation_name').text
                anim_data.path = actor.find('anim_path').text
                anim_data.override_path = anim.find('override_path').text
                anim_data.start_frame = anim.find('start').text
                anim_data.end_frame = anim.find('end').text
                anim_data.path = anim.find('path').text
                anim_data.muted_layers = anim.find('muted').text

        return char_data

    def populate_rig_class(self, key):
        """
        gets data from fileInfo based on key and populates layer data

        :param key: key from fileInfo dict
        :type key: str
        :return: class that contain users option data
        :rtype: UserOptionsData()
        """
        if Debug.debug : print(('calling :: {0}'.format('populate_users_options_classes')))

        rig = RigLayerData()
        if key in pm.fileInfo:
            rig_value = pm.fileInfo[key]
            rig_value = rig_value.encode().decode('unicode-escape')

            root = ET.fromstring(rig_value)
            rig_data = root.find(Identifiers.rigs_str)
            rig.name = rig_data.find('name').text
            rig.model_name = rig_data.find('model_name').text
            rig.root = rig_data.find('root').text
            rig.rig_path = rig_data.find('rig_path').text
            rig.animation_path = rig_data.find('animation_path').text

            export_items = rig_data.find('export_items').text
            rig.export_items = export_items.split(', ')

            models = rig_data.findall(Identifiers.model_xml_path)
            for model in models:
                model_data = RigModelData()
                rig.models.append(model_data)
                model_data.name = model.find('name').text
                model_data.path = model.find('path').text
                model_data.uuid = model.find('uuid').text
                model_data.influences = model.find('influences').text

                export_items = model.find('export_items').text
                model_data.export_items = export_items.split(', ')

        return rig

    def populate_users_options_class(self):

        # hack to work around sg_prefUtils stuff

        users_options_data = UserOptionsData()

        users_options_data.auto_select_in_scene = False
        users_options_data.save_to_disk = False
        users_options_data.active_tab = True

        return users_options_data

    def populate_models_classes(self, layer_value, key):
        """
        called by

        :param layer_value: xml format string
        :param key: (str) name of item as it would be represented in fileInfo
        :return: populated model class used to populate ui
        """

        layer_data = LayerData()

        root = ET.fromstring(layer_value)
        layer = root.find(Identifiers.model_layer_str)
        layer_data.name = key.replace(Identifiers.model_layer_identifier, '')
        layer_data.path = layer.find('path').text

        layer_data.fbx_export_override_path = strtobool(layer.find('fbx_export_override_path').text)
        layer_data.fbx_export_override_options = strtobool(layer.find('fbx_export_override_options').text)
        layer_data.fbx_export_smoothing_groups = strtobool(layer.find('fbx_export_smoothing_groups').text)
        layer_data.fbx_export_hard_edges = strtobool(layer.find('fbx_export_hard_edges').text)
        layer_data.fbx_export_tangents = strtobool(layer.find('fbx_export_tangents').text)
        layer_data.fbx_export_smooth_mesh = strtobool(layer.find('fbx_export_smooth_mesh').text)
        layer_data.fbx_export_animation_only = strtobool(layer.find('fbx_export_animation_only').text)
        layer_data.fbx_export_instances = strtobool(layer.find('fbx_export_instances').text)
        layer_data.fbx_export_zero = strtobool(layer.find('fbx_export_zero').text)
        layer_data.fbx_export_triangulate = strtobool(layer.find('fbx_export_triangulate').text)
        models = layer.findall(Identifiers.model_xml_path)
        for model in models:
            model_data = ModelData()
            layer_data.models.append(model_data)
            model_data.name = model.find('name').text
            model_data.path = model.find('path').text
            model_data.uuid = model.find('uuid').text

            export_items = model.find('export_items').text
            # there is a possibility that there are no export item but that the users wants to keep the item listed
            # in the ui to use later
            if export_items:
                model_data.export_items = export_items.split(', ')

            # export options
            model_data.fbx_export_override_layer_options = strtobool(
                model.find('fbx_export_override_layer_options').text)
            model_data.fbx_export_override_layer_path = strtobool(
                model.find('fbx_export_override_layer_path').text)
            model_data.fbx_export_smoothing_groups = strtobool(model.find('fbx_export_smoothing_groups').text)
            model_data.fbx_export_hard_edges = strtobool(model.find('fbx_export_hard_edges').text)
            model_data.fbx_export_tangents = strtobool(model.find('fbx_export_tangents').text)
            model_data.fbx_export_smooth_mesh = strtobool(model.find('fbx_export_smooth_mesh').text)
            model_data.fbx_export_animation_only = strtobool(model.find('fbx_export_animation_only').text)
            model_data.fbx_export_instances = strtobool(model.find('fbx_export_instances').text)
            model_data.fbx_export_zero = strtobool(model.find('fbx_export_zero').text)
            model_data.fbx_export_triangulate = strtobool(model.find('fbx_export_triangulate').text)

        return layer_data

    def populate_models_classes_from_string(self, xml_string, key):
        pass

        print(('\n xml_string :: {0}\n key :: {1}'.format(xml_string, key)))

        layer_data = self.populate_models_classes(xml_string, key)
        return layer_data

    def populate_models_classes_from_fileInfo(self, key):
        """
        gets data from fileInfo based on key and populates layer data

        :param key: key from fileInfo dict
        :type key: str
        :return: class that contain layer (and model) data
        :rtype: LayerData()
        """
        if Debug.debug : print(('calling :: {0}'.format('populate_model_classes')))

        if key in pm.fileInfo:
            layer_value = pm.fileInfo[key]
            layer_value = layer_value.encode().decode('unicode-escape')
            layer_data = self.populate_models_classes(layer_value, key)
            return layer_data

    def get_valid_keys_from_fileInfo(self, fileInfo_identifier):
        """
        gets a list of valid keys from fileInfo based on a pre-fix to identify the type of data

        :param fileInfo_identifier: the pre-fix for the fileinfo key
        :type fileInfo_identifier: str defined in Identifiers class
        :return fileInfo_keys: list of str (keys) from fileInfo
        :rtype fileInfo_keys: [keys]
        """
        if Debug.debug : print(('calling :: {0}'.format('get_valid_keys')))

        fileInfo_keys = []
        for key in list(pm.fileInfo.keys()):
            if fileInfo_identifier in key:
                fileInfo_keys.append(key)

        return fileInfo_keys

    def build_actor_class_from_data(self):
        """
        WIP
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('build_actor_class_from_data')))
        fileInfo_keys = self.get_valid_keys_from_fileInfo(Identifiers.actor_identifier)

        chars = []
        for key in fileInfo_keys:
            char_data = self.populate_actors_classes(key)
            chars.append(char_data)

        return chars

    def build_model_class_from_data(self):
        """
        gets model data

        :return models: [models]
        :rtype models: [LayerData()]
        """
        if Debug.debug : print(('calling :: {0}'.format('build_model_class_from_data')))

        fileInfo_keys = self.get_valid_keys_from_fileInfo(Identifiers.model_layer_identifier)

        models = []
        for key in fileInfo_keys:
            model_data = self.populate_models_classes_from_fileInfo(key)
            models.append(model_data)

        return models

    def build_rig_class_from_data(self):
        """
        gets populated data based on fileInfo_identifier

        :return users_options: class with populated users options
        :rtype users_options: UserOptionsData()
        """
        if Debug.debug: print(('calling :: {0}'.format('build_rig_class_from_data')))

        fileInfo_keys = self.get_valid_keys_from_fileInfo(Identifiers.rig_layer_identifier)

        rigs = []
        for key in fileInfo_keys:
            rig_data = self.populate_rig_class(key)
            rigs.append(rig_data)

        return rigs

    def build_class_from_data(self, fileInfo_identifier):
        """
        gets populated data based on fileInfo_identifier

        :param fileInfo_identifier: the pre-fix for the fileinfo key
        :type fileInfo_identifier: str defined in Identifiers class
        :return data: populated data
        :rtype data: container class from __init__
        """
        if Debug.debug : print(('calling :: {0}'.format('build_class_from_data')))

        data = []
        if fileInfo_identifier == Identifiers.actor_identifier:
            data = self.build_actor_class_from_data()
        elif fileInfo_identifier == Identifiers.rig_layer_identifier:
            data = self.build_rig_class_from_data()
        elif fileInfo_identifier == (Identifiers.model_layer_identifier or Identifiers.scene_layer_identifier):
            data = self.build_model_class_from_data()

        return data

    def change_start_end_frame(self, item, new_frame, type):
        """
        updates the start or end frame for an animation. this is used as a first class function in
        def edit_multiple_entries so its arg signature needs to stay the same or update dependent functions

        :param item: animation
        :type item: tree item
        :param new_frame: new start or end frame
        :type new_frame: str
        :param type: is it a start or end frame
        :type type: int
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('change_start_frame')))

        chars = self.build_class_from_data(Identifiers.actor_identifier)

        for char in chars:
            if item.parent().text(0) == char.name:
                for anim in char.animations:
                    if item.text(0) == anim.anim_name:
                        if type == 1:
                            anim.start_frame = new_frame
                        elif type == 2:
                            anim.end_frame = new_frame

        self.write_anim_data_to_fileinfo(chars)

    def change_animation_name(self, item, new_name, old_anim_name):
        """
        updates name of an animation

        :param item: animation
        :type item: tree item
        :param new_name: new name for animation
        :type new_name: str
        :param old_anim_name: current name of animation
        :type old_anim_name: str
        :return:
        :rtype:
        """
        if Debug.debug: print(('calling :: {0}'.format('change_animation_name')))

        chars = self.build_class_from_data(Identifiers.actor_identifier)
        for char in chars:
            if item.parent().text(0) == char.name:
                for anim in char.animations:
                    if old_anim_name == anim.anim_name:
                        anim.anim_name = new_name

        self.write_anim_data_to_fileinfo(chars)

    def change_rig_name(self, item, old_name):
        """
        changes the name of a QTreeWidgetItem to users choice

        :param item: tree item to change name
        :type item: QTreeWidgetItem
        :param old_name: old layer name
        :type old_name: str
        """
        if Debug.debug: print(('calling :: {0}'.format('change_rig_name')))

        print('\nchange_rig_layer_name\n item.whatsThis :: {0}\n old_name :: {1}'.format(item.whatsThis(0), old_name))

        if item.whatsThis(0) == Identifiers.rigs_str:
            rigs = self.build_class_from_data(Identifiers.rig_layer_identifier)
            for rig in rigs:
                for model in rig.models:
                    if old_name == model.name:
                        model.name = item.text(0)

        elif item.whatsThis(0) == Identifiers.rig_layer_identifier:
            rigs = self.build_class_from_data(Identifiers.rig_layer_identifier)
            for rig in rigs:
                if old_name == rig.name:
                    rig.name = item.text(0)

            self.remove_key(Identifiers.rig_layer_identifier + old_name)

        self.write_rig_data_to_fileinfo(rigs)

    # def change_rig_layer_name(self, item, old_name):
    #     """
    #     changes the name of a QTreeWidgetItem to users choice
    #
    #     :param item: tree item to change name
    #     :type item: QTreeWidgetItem
    #     :param old_name: old layer name
    #     :type old_name: str
    #     """
    #     if Debug.debug: print(('calling :: {0}'.format('change_rig_name')))
    #
    #     print('\nchange_rig_layer_name\n item.whatsThis :: {0}\n old_name :: {1}'.format(item.whatsThis(0), old_name))
    #
    #     if item.whatsThis(0) == Identifiers.rig_layer_identifier:
    #         rigs = self.build_class_from_data(Identifiers.rig_layer_identifier)
    #         for rig in rigs:
    #             if old_name == rig.name:
    #                 rig.name = item.text(0)
    #
    #         self.remove_key(Identifiers.rig_layer_identifier + old_name)
    #         self.write_rig_data_to_fileinfo(rigs)

    def change_export_item_name(self, old_name, new_name, indentifier):
        '''
        updates export_items data name

        @param old_name: old name for export item
        @type old_name: str
        @param new_name: new name for export item
        @type new_name: str
        @param indentifier: type of item
        @type indentifier: str
        @return: success
        @rtype: bool
        '''
        if Debug.debug: print(('calling :: {0}'.format('change_export_item_name')))

        layers = self.build_class_from_data(indentifier)
        for layer in layers:
            for model in layer.models:
                if old_name in model.export_items:
                    index = model.export_items.index(old_name)
                    model.export_items.pop(index)
                    model.export_items.append(new_name)
                    self.write_model_layer_data_to_fileinfo(layers)
                    return True

        return False

    def change_layer_model_name(self, item, old_name):
        """
        changes the name of a QTreeWidgetItem to users choice

        :param item: tree item to change name
        :type item: QTreeWidgetItem
        :param old_name: old layer name
        :type old_name: str
        """
        if Debug.debug: print(('calling :: {0}'.format('change_layer_name')))

        if item.whatsThis(0) == Identifiers.model_layer_str:
            # see if layer name already exist
            if self.check_exists_layer(Identifiers.model_layer_identifier + item.text(0)):
                out = 'Duplicate layer name :: {0}'.format(item.text(0))
                pm.confirmDialog(title=out,
                                 message='You can not add a Layer a name that already exists.', button=['OK'],
                                 defaultButton='OK')
                return
            else:
                layers = self.build_class_from_data(Identifiers.model_layer_identifier)
                for layer in layers:
                    if old_name == layer.name:
                        layer.name = item.text(0)

                        self.remove_key(Identifiers.model_layer_identifier + old_name)

        elif item.whatsThis(0) == Identifiers.models_str:
            layers = self.build_class_from_data(Identifiers.model_layer_identifier)
            for layer in layers:
                if item.parent().text(0) == layer.name:
                    for model in layer.models:
                        if model.name == old_name:
                            model.name = item.text(0)

        self.write_model_layer_data_to_fileinfo(layers)

    def change_layer_path(self, item, new_path):
        """
        change path for tree item

        :param item: tree item to change path for
        :type item: QTreeWidgetItem
        :param new_path: path to change
        :type new_path: str
        """
        if Debug.debug: print(('calling :: {0}'.format('change_layer_path')))

        layers = self.build_class_from_data(Identifiers.model_layer_identifier)
        for layer in layers:
            if item.text(0) == layer.name:
                layer.path = new_path

        self.write_model_layer_data_to_fileinfo(layers)

    def change_model_path(self, item, new_path):
        """
        change path for tree item

        :param item: model tree item to change path of
        :type item: QTreeWidetItem
        :param new_path: path to change to
        :type new_path: str
        """
        if Debug.debug: print(('calling :: {0}'.format('change_layer_name')))

        layers = self.build_class_from_data(Identifiers.model_layer_identifier)
        for layer in layers:
            if item.parent().text(0) == layer.name:
                for model in layer.models:
                    if model.name == item.text(0):
                        model.path = new_path

        self.write_model_layer_data_to_fileinfo(layers)

    def change_override_path(self, item, path, column):
        """
        change the override path for tree item. this is used as a first class function in
        def edit_multiple_entries so its arg signature needs to stay the same or update dependent functions

        :param item: tree item to change
        :type item: QTreeWidgetItem
        :param path: path to change to
        :type path: str
        :param column: number of the column clicked
        :type column: int
        """

        if Debug.debug : print(('calling :: {0}'.format('change_override_path')))

        chars = self.build_class_from_data(Identifiers.actor_identifier)
        for char in chars:
            if item.parent().text(0) == char.name:
                for anim in char.animations:
                    if item.text(0) == anim.anim_name:
                        if column == 4:
                            anim.override_path = path
        # need to remove from fileInfo as the name of a top level object is the
        self.remove_key(Identifiers.actor_identifier + item.text(0))
        self.write_anim_data_to_fileinfo(chars)

    def change_rig_influences(self, item, influences):
        '''
        updates rigs influence

        @param item: rig item
        @type item: tree item
        @param influences: number of allowed influences
        @type influences: str
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0}'.format('change_rig_layer_path')))

        rig_layers = self.build_class_from_data(Identifiers.rig_layer_identifier)
        for rig in rig_layers:
            if item.parent().text(0) == rig.name:
                for model in rig.models:
                    if model.name == item.text(0):
                        model.influences = influences

        self.write_rig_data_to_fileinfo(rig_layers)

    def change_rig_layer_path(self, item, new_path, asset_type):
        """
        change path for tree item

        :param asset_type: type of asset to change path
        :type asset_type: string
        :param item: tree item to change path for
        :type item: QTreeWidgetItem
        :param new_path: path to change
        :type new_path: str
        """
        if Debug.debug: print(('calling :: {0}'.format('change_rig_layer_path')))

        rig_layers = self.build_class_from_data(Identifiers.rig_layer_identifier)
        for rig in rig_layers:
            if item.text(0) == rig.name:
                if asset_type == 'rig_path':
                    rig.rig_path = new_path
                elif asset_type == 'anim_path':
                    rig.animation_path = new_path

        self.write_rig_data_to_fileinfo(rig_layers)

    def set_maya_to_data_range(self, item):
        """
        event for right click of tree anim item that sets maya playback to the properties of the item

        :param item: animation export item
        :type item: tree item
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('set_maya_to_data_range')))

        chars = self.build_class_from_data(Identifiers.actor_identifier)
        for char in chars:
            if item.parent().text(0) == char.name:
                for anim in char.animations:
                    if item.text(0) == anim.anim_name:
                        pm.playbackOptions(animationStartTime=anim.start_frame, minTime=anim.start_frame,
                                           animationEndTime=anim.end_frame, maxTime=anim.end_frame)

    def get_selected_animlayers(self):
        """
        gets a list of selected animation layers

        :return: names of selected layers
        :rtype: list of str
        """
        if Debug.debug : print(('calling :: {0}'.format('get_selected_animlayers')))

        selected_layers = []
        pm.animLayer(query=True, root=True)

        kids = pm.animLayer(pm.animLayer(q=True, root=True), q=True, children=True)
        if kids:
            for kid in kids:
                if pm.animLayer(kid, query=True, selected=True):
                    selected_layers.append(kid.name())

        return selected_layers

    def remove_selected_animlayers(self, item):
        """
        removes selected anim layer from animation class muted_layers property

        :param item: anim item that had a right click event fired on it
        :type item: tree item
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('set_selected_animlayers')))

        selected_layers = self.get_selected_animlayers()
        if selected_layers:
            chars = self.build_class_from_data(Identifiers.actor_identifier)
            for char in chars:
                if item.parent().text(0) == char.name:
                    for anim in char.animations:
                        if item.text(0) == anim.anim_name:
                            muted_layers = anim.muted_layers.split(', ')
                            new_layers = list(set(muted_layers) - set(selected_layers))
                            anim.muted_layers = ', '.join(new_layers)

            self.write_anim_data_to_fileinfo(chars)

    def set_selected_animlayers(self, item):
        """
        adds selected anim layer to animation class muted_layers property

        :param item: anim item that had a right click event fired on it
        :type item: tree item
        :return:
        :rtype:
        """
        if Debug.debug : print(('calling :: {0}'.format('set_selected_animlayers')))

        selected_layers = self.get_selected_animlayers()
        if selected_layers:
            chars = self.build_class_from_data(Identifiers.actor_identifier)
            for char in chars:
                if item.parent().text(0) == char.name:
                    for anim in char.animations:
                        if item.text(0) == anim.anim_name:
                            if anim.muted_layers:
                                muted_layers = anim.muted_layers.split(', ')
                                anim.muted_layers = ', '.join(muted_layers + selected_layers)
                            else:
                                anim.muted_layers = ', '.join(selected_layers)

            self.write_anim_data_to_fileinfo(chars)


ExporterData = FBXExporterData()
