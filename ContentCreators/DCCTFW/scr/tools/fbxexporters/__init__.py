"""
TODO:
GeneraL
- need to go through all the exporters and make sure things are consistent, over the long development period i have 
used various ways to do the same thing in the different exporters 

- look at callbacks. open causes dialog to close
- open to correct tab
-store last used tab
-back up file info
-highlight models items with no export items
--make sure model is not exported with nothing in it
-rt open FBX file in current Maya session
-color to tell if export setting (or other stuff) have been changed

-After you add a new variable to fbx_exporter_data it will not exist to read until data is initialized this will cause 
errors. Figure out a way to add vars so that no errors are thrown. Add a new variable to a class and be able to open 
tool and populate UI without errors. There is an example of how to do this in refresh_model_tree_ui for 
model.triangulate
-Custom tag to show what version of the exporter you are using

Model Tree
-replace 'for layer in self.model_layers:' with function
-populate_models_classes should be called populate_layers_classes..?

Anim Tree
- i am using itemChanged and itemDoubleClicked in a confusing way. This maybe happening across all the trees 
-- self.ui.tre_animations.itemDoubleClicked.connect
-- self.ui.tre_animations.itemChanged.connect

- Update path on reference file. So if it is updated in the rig file it will propagate to the animation files.
-Add export functionality for muted animation layers (see Michael's email "Fwd: SG Tools Update - Animator's Edition 07/13/17")
-Can we export option to make it easier to bring assets into dev environment (Kyle)
-Animators do not seem to need unique export options 
-Default is to use Maya file name for animation name from Maya file (low priority)


"""

"""

Data flow:

The authoritative version of the data is in fileInfo. We are using ElementTree (an xml writer/parser) for this. 
The data as stored in fileInfo is a standard xml format so it san be written to disk and used as you would normally
use an xml file 

To see the data you can use the pm.fileInfo commands in the script editor

    pm.fileInfo.keys()
    pm.fileInfo.has_key('_fbx_model_layer_Default Layer')
    pm.fileInfo['_fbx_model_layer_Default Layer'] 
    
There is a command to remove all data from fileInfo .clear(). This will wipe all data used in the UI so should only be
used if you are willing to lose all export and option data.

the only fileInfo operation which is does not use pm is remove key. We used maya.cmd for this as i could not find a pm 
function to do it 

1. When the UI is initialized the data is read from fileInfo and moved into container classes
2. Those are defined in this __init__.py file (LayerData(), AnimationData()...)
3. Once the containers are populated from fileInfo the data is then populated in the UI
4. When data is changed in the UI the containers are updated and the data is feed back into fileInfo
5. Then the these steps are repeated from step 1.    

When an operation (like export) is called the container data is used not the user facing data in the UI

You can see both the UI and container data from the script editor as well

    import fbxexporters
    
    root = fbxexporters.fbx_model_exporter_ui.ModelExporterUI.ui.tre_models.invisibleRootItem()
    child_count = root.childCount()
    item = fbxexporters.fbx_model_exporter_ui.ModelExporterUI.ui.tre_models.topLevelItem(0)
    
    fbxexporters.fbx_model_exporter_ui.ModelExporterUI.model_layers[0].models[0].name
    fbxexporters.fbx_model_exporter_ui.ModelExporterUI.model_layers[0].models[0].path

"""


"""
How to add a new variable to data: 

<Using AnimationData.start_frame as an example>

in __init__ module <__init__.py>
-add variable to data class <AnimationData>
-add to __str__ for data class <AnimationData>

in ui module <fbx_exporter_ui.py>
-if needed add to function that is called on tree being updated <tre_animations_changed>
-add to refresh tree function <refresh_anim_tree_ui>
-add to function that creates new data based on user request <add_animation>

in data module <fbx_exporter_data.py>
-add to function that creates xml data <create_actor_xml>
-add to function that populates data class <populate_actors_classes>
-add to function that is called to change/update data <change_start_end_frame> 
-if needed add to other functions that apply to data changes <set_maya_to_data_range>
"""


class ExportUtilities(object):
    """
    class for getting relative path for .ui files
    """
    def __init__(self):
        pass

    # def get_ui_dir(*args):
    #     sgtools_ws_root = prefUtils.readPrefsNestedKey("p4SwitchPref", "sgToolsDirectory")
    #     ui_rel_path = r"Scripts\fbxexporters".replace("\\", "/")
    #     rtn_dir = os.path.join(sgtools_ws_root, ui_rel_path).replace("\\", "/")
    #     return rtn_dir


class GlobalExportOptions(object):
    """
    Global Export options that will always be the same for SG exports
    """

    def __init__(self):
        # Global
        self.fbx_export_input_connections = False
        self.fbx_export_in_ascii = True
        self.fbx_export_convert_unit_string = 'cm'
        self.fbx_export_scale_factor = 1
        self.fbx_export_embedded_textures = False


class ExportOptions:
    """
    Individual export option that will change based on user selection for asset
    """
    def __init__(self):
        self.fbx_export_override_path = None
        self.fbx_export_override_options = None
        self.fbx_export_smoothing_groups = True
        self.fbx_export_hard_edges = False
        self.fbx_export_tangents = True
        self.fbx_export_smooth_mesh = False
        self.fbx_export_animation_only = False
        self.fbx_export_instances = False
        self.fbx_export_zero = False
        self.fbx_export_triangulate = False

    def __str__(self):
        return ('fbx_export_override_path :: {0}\n fbx_export_override_options :: {1}\n fbx_export_smoothing_groups :: '
                '{2}\n fbx_export_hard_edges :: {3}\n fbx_export_tangents :: {4}\n fbx_export_smooth_mesh :: {5}\n '
                'fbx_export_animation_only :: {5}\n fbx_export_instances :: {6}\n fbx_export_zero :: {7}\n '
                'fbx_export_triangulate :: {8}\n'.
                format(self.fbx_export_override_path, self.fbx_export_override_options,
                       self.fbx_export_smoothing_groups, self.fbx_export_hard_edges, self.fbx_export_tangents,
                       self.fbx_export_smooth_mesh, self.fbx_export_animation_only, self.fbx_export_instances,
                       self.fbx_export_zero, self.fbx_export_triangulate))


class Debug(object):
    """fbx_export_zero
    debug data. may add error messaging but for now it is just a bool val to use debug options or not
    """
    debug = True


class Identifiers:
    """
    list of str used by the exporter
    collected here to avoid magic strings and easily change
    """
    actor_identifier = '_fbx_export_actor_'
    animations_str = 'animations'
    animation_path_str = '_animation_path_'
    model_layer_str = 'layers'
    model_str = 'model'
    models_str = 'models'
    model_layer_identifier = '_fbx_export_model_layer_'
    model_xml_path = './models/model'
    rig_identifier = '_fbx_export_rig_'
    rig_layer_identifier = '_fbx_export_rig_'
    rigs_str = 'rigs'
    root_str = 'root'
    scene_layer_identifier = '_fbx_scene_layer_'


class AnimationData:
    """
    collection of data for animation export
    used to hold data for reading and writing to fileInfo
    """
    def __init__(self):
        self.actor_name = None
        self.anim_name = None
        self.start_frame = None
        self.end_frame = None
        self.path = None
        self.override_path = None
        self.rig_name = None
        self.framerate = None
        self.muted_layers = None
        self.export_version = None

    def __str__(self):
        return (
            'actor_name :: {0}\n anim_name :: {1}\n start_frame :: {2}\n end_frame :: {3}\n path :: {4}\n '
            'override_path :: {5}\n rig_name ::  {6}\n framerate :: {7}\n muted_layers :: {8}\n'.format(
                self.actor_name,self.anim_name, self.start_frame, self.end_frame, self.path, self.override_path,
                self.rig_name, self.framerate, self.muted_layers))


class ActorLayerData(object):
    """
    collection of data for acyot export
    used to hold data for reading and writing to fileInfo
    """
    def __init__(self):
        # the name needs to be the group name that is referenced from the rig file
        self.name = None
        self.export_items = []
        self.path = None
        self.animations = []
        self.export_version = None
        self.uuid = None
        self.root = None

    def __str__(self):
        return 'name :: {0}\n path :: {1}\n animations :: {2}\n uuid :: {3}'.format(self.name, self.path,
                                                                                         self.animations, self.uuid)


class RigLayerData(object):
    """
    collection of data for rig export
    used to hold data for reading and writing to fileInfo
    """
    def __init__(self):
        self.name = None
        self.model_name = None
        self.root = None
        self.animation_path = None
        self.rig_path = None
        self.export_version = None
        self.models = []
        self.export_items = []
        self.uuid = None

    def __str__(self):
        return 'name :: {0}\n rig path :: {1}\n anim_path :: {2}\n models :: {3}\n export_items :: {4}'.\
            format(self.name, self.rig_path, self.animation_path, self.models, self.export_items)


class RigModelData(object):
    """
    collection of data for rig export
    used to hold data for reading and writing to fileInfo
    """
    def __init__(self):
        self.name = None
        self.path = None
        self.export_version = None
        self.export_items = []
        self.uuid = None
        self.influences = None

    def __str__(self):
        return 'name :: {0}\n path :: {1}\n anim_path :: {2}\n export items :: {3}\n influences :: {4}'.format(
            self.name, self.path,
            self.path,
            self.export_items,
            self.influences
        )


class LayerData(object):
    """
    collection of data for layers export. includes a list of ModelData contained in the layer
    used to hold data for reading and writing to fileInfo
    """
    def __init__(self):
        self.name = None
        self.path = None
        self.type = None
        self.models = []
        self.color = None

        # export options
        self.fbx_export_override_path = False
        self.fbx_export_override_options = False
        self.fbx_export_smoothing_groups = True
        self.fbx_export_hard_edges = False
        self.fbx_export_tangents = True
        self.fbx_export_smooth_mesh = False
        self.fbx_export_animation_only = False
        self.fbx_export_instances = False
        self.fbx_export_zero = False
        self.fbx_export_triangulate = False

    def __str__(self):
        return 'name :: {0}\n path :: {1}\n type :: {2}\n models :: {3}\n use override path :: {4}\n use override options :: {5}'.format(
            self.name, self.path, self.type, self.models, self.fbx_export_override_path, self.fbx_export_override_options)


class UserOptionsData(object):
    def __init__(self):
        self.save_to_disk = False
        self.auto_select_in_scene = False
        self.active_tab = True

    def __str__(self):
        return 'save_to_disk :: {0}\n auto_select_in_scene :: {1}\n active_tab :: {2}\n'.format(
            self.save_to_disk, self.auto_select_in_scene, self.active_tab)


class ModelData(object):
    """
    collection of data for model export
    used to hold data for reading and writing to fileInfo
    """
    def __init__(self):
        self.name = None
        self.export_items = []
        self.path = None
        self.export_version = None
        self.uuid = None
        self.color = None

        # export options
        self.fbx_export_override_layer_path = False
        self.fbx_export_override_layer_options = False
        self.fbx_export_smoothing_groups = True
        self.fbx_export_hard_edges = False
        self.fbx_export_tangents = True
        self.fbx_export_smooth_mesh = False
        self.fbx_export_animation_only = False
        self.fbx_export_instances = False
        self.fbx_export_triangulate = False
        self.fbx_export_zero = False

    def __str__(self):
        return 'name :: {0}\n path :: {1}\n uuid :: {2}\n fbx_export_smoothing_groups :: {3}\n fbx_export_hard_edges '\
               ':: {4}\n fbx_export_tangents :: {5}\n fbx_export_smooth_mesh :: {6}\n fbx_export_animation_only :: {7}'\
               '\n fbx_export_instances :: {8}\n fbx_export_triangulate :: {9}\n fbx_export_zero :: {10}\n ' \
               'export items :: {11}\n override path :: {12}\n override options :: {13}'.format(
                self.name, self.path, self.uuid, self.fbx_export_smoothing_groups, self.fbx_export_hard_edges,
                self.fbx_export_tangents, self.fbx_export_smooth_mesh, self.fbx_export_animation_only,
                self.fbx_export_instances, self.fbx_export_triangulate, self.fbx_export_zero, self.export_items,
                self.fbx_export_override_layer_path, self.fbx_export_override_layer_options)








