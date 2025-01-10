import logging
import pymel.core as pm

import scr
from scr.tools.fbxexporters import Debug
from scr.tools.fbxexporters import GlobalExportOptions


class FBXExport(object):

    def __init__(self):
        self.logger = logging.getLogger(scr.logger_name)

        self.global_export_options = GlobalExportOptions()
        self.zero_matrix = pm.datatypes.Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0],
                                                [0.0, 0.0, 0.0, 1.0]])

    def export_global_options(self):
        """
        sets up the default export options that will remain consistent across all exports
        """
        if Debug.debug: print(('calling :: {0} '.format('export_global_options')))

        # Global
        pm.mel.FBXExportScaleFactor(self.global_export_options.fbx_export_scale_factor)

        """
        HACK
        removing FBXExportConvertUnitString as it is causing issues with scale in unity where the rig is brought in at 
        .01 scale fro x,y,z . Removing it fixes the rig export to unity i need to test how it impacts other exports as 
        well as rig exports to unreal
        """
        pm.mel.FBXExportConvertUnitString(v=self.global_export_options.fbx_export_convert_unit_string)
        """
        above...remove for rig
        """

        pm.mel.FBXExportInputConnections(v=self.global_export_options.fbx_export_input_connections)
        pm.mel.FBXExportInAscii(v=self.global_export_options.fbx_export_in_ascii)
        pm.mel.FBXExportEmbeddedTextures(v=self.global_export_options.fbx_export_embedded_textures)

    def export_rig_setup(self, models, model_name, root_name, export_dir):
        '''
        set up process for exporting a single rig

        @param models: geo in scene to be selected for export
        @type models: [str]
        @param model_name: name of export layer
        @type model_name: str
        @param root_name: name of root joint to be select for export
        @type root_name: str
        @param export_dir: path
        @type export_dir: export location
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0} '.format('export_rig_setup')))

        pm.mel.FBXResetExport()

        # removing until rig scale issue is resolved
        # self.export_global_options()
        self.export_rig_options()
        success = self.export_rig(models, model_name, root_name, export_dir)
        return success

    def export_animation_setup(self, name, path, start, end):
        '''
        set up process for exporting a single animation

        @param name: fbx export name
        @type name: str
        @param path: path
        @type path: str
        @param start: start frame
        @type start: str
        @param end: end frame
        @type end: str
        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0} '.format('export_rig_setup')))

        pm.playbackOptions(animationStartTime=start, animationEndTime=end)
        pm.playbackOptions(min=start, max=end)

        pm.mel.FBXResetExport()
        self.export_global_options()
        self.export_animation_options()
        self.export_animation(name, path)

    @staticmethod
    def export_animation_options():
        '''
        fbx options for animation export

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0} '.format('export_rig_options')))

        # this is from the original exporter. i am not sure how to include it if it is needed
        # pm.Mel.eval("FBXProperty Export|IncludeGrp|Animation -v true;")

        pm.mel.FBXExportBakeComplexAnimation(v=True)
        pm.mel.FBXExportReferencedAssetsContent(v=True)

    def export_rig_options(self):
        '''
        fbx options for rig export

        @return:
        @rtype:
        '''
        if Debug.debug: print(('calling :: {0} '.format('export_rig_options')))

        """
        copying from def export_global_options until i figure out the FBXExportConvertUnitString and how it relates to 
        the scale of .01 being imported on the rig
        """
        pm.mel.FBXExportInputConnections(v=self.global_export_options.fbx_export_input_connections)
        pm.mel.FBXExportInAscii(v=self.global_export_options.fbx_export_in_ascii)
        pm.mel.FBXExportEmbeddedTextures(v=self.global_export_options.fbx_export_embedded_textures)

        pm.mel.FBXExportSkins(v=True)
        pm.mel.FBXExportAnimationOnly(v=False)

    @staticmethod
    def export_model_options(options):
        """
        fbx options for model export

        :param options: class with export options
        :type options: either ModelData() or LayerData()
        """
        if Debug.debug: print(('calling :: {0} '.format('export_model_options')))

        pm.mel.FBXExportSmoothingGroups(v=options.fbx_export_smoothing_groups)
        pm.mel.FBXExportHardEdges(v=options.fbx_export_hard_edges)
        pm.mel.FBXExportTangents(v=options.fbx_export_tangents)
        pm.mel.FBXExportSmoothMesh(v=options.fbx_export_smooth_mesh)
        pm.mel.FBXExportAnimationOnly(v=options.fbx_export_animation_only)
        pm.mel.FBXExportInstances(v=options.fbx_export_instances)
        pm.mel.FBXExportTriangulate(v=options.fbx_export_triangulate)

    def export_model_setup(self, model, export_path, options):
        """
        runs a series of commands for exporting model

        :param model: asset to be exported
        :type model: ModelData()
        :param export_path: path to export fbx to
        :type export_path: str
        :param options: options to export fbx with
        :type options: ModelData() or LayerData()
        """
        if Debug.debug: print(('calling :: {0} '.format('export_model_setup')))

        pm.mel.FBXResetExport()
        self.export_global_options()
        self.export_model_options(options)
        # added = self.do_p4(export_path)
        self.pre_export_model(model, export_path, options)

        # # removing we need to figure out a way to determine if the user has P4 or SVN
        # if not added:
        #     pipelineTools.sg_p4Utils.add(export_path)

    def test_models_exist(self, model):
        '''
        tests if model in ModelData exists

        :param model: model(s) to export...export items
        :type model: ModelData()
        @return:
        @rtype:
        '''

        missing = []

        for item in range(len(model.export_items)):
            if pm.objExists(model.export_items[item]):
                pass
                # print(('found :: {0}'.format(model.export_items[item])))
            else:
                # print(('missing :: {0}'.format(model.export_items[item])))
                missing.append(model.export_items[item])

        for miss in missing:
            model.export_items.remove(miss)

        return model

    def pre_export_model(self, model, export_path, options):
        """
        currently this is just performing the task of moving the model to 0,0,0 for Unreal exports
        ...and then moving it back after the export

        :param model: model(s) to export...export items
        :type model: ModelData()
        :param export_path: path to export fbx to
        :type export_path: str
        """
        if Debug.debug : print(('calling :: {0} '.format('pre_export_model')))

        model = self.test_models_exist(model)

        if model.fbx_export_zero or options.fbx_export_zero:
            model_matrixs = {}
            for item in model.export_items:
                export_item = pm.ls(item)[0]
                model_matrixs[item] = export_item.getMatrix()
                export_item.setMatrix(self.zero_matrix)

            self.export_model(model, export_path)

            for item in model.export_items:
                export_item = pm.ls(item)[0]
                export_item.setMatrix(model_matrixs[item])
        else:
            self.export_model(model, export_path)

    @staticmethod
    def remove_pipe(name):
        """
         addresses issue where maya adds a '|' to make the model name unique

        :param name:
        :type name:
        :return:
        :rtype:
        """

        if name.find('|') > -1:
            b = name.split('|')[-1]
            return b

        return name

    def export_animation(self, name, export_dir):
        """
        runs FBXExport call to export animation

        @param name: export file name
        @type name: str
        @param export_dir: export directory
        @type export_dir: str
        @return: success
        @rtype: bool
        """

        if Debug.debug: print('calling :: {0}'.format('export_animation'))

        export_path = export_dir + '\\' + name + '.fbx'

        if pm.ls(selection=True):

            mess = ('\nExporting {0} to {1}'.format(name, export_path))
            self.logger.info(mess)

            pm.mel.FBXExport(s=True, f=export_path)
            pm.select(clear=True)
            return True

    def export_rig(self, models, model_name, root_name, export_dir):
        '''
        runs FBXExport call to export rig

        @param models: models to export
        @type models: [str]
        @param model_name: fbx export name
        @type model_name: str
        @param root_name: root joint to export
        @type root_name: str
        @param export_dir: location for export
        @type export_dir: str
        @return:
        @rtype:
        '''

        try:
            pm.select(clear=True)
            export_models = []
            for model in models:
                export_models.append(self.remove_pipe(model))

            pm.select(export_models, root_name)

            model_name = self.remove_pipe(model_name)
            export_path = export_dir + '\\' + model_name + '.fbx'

            if pm.ls(selection=True):
                mess = ('\nExporting {0} to {1}'.format(model_name, export_path))
                self.logger.info(mess)

                pm.mel.FBXExport(s=True, f=export_path)
                pm.select(clear=True)

                return True
        except:
            return False

    def export_model(self, model, export_path):
        """
        call to export. throws an error if model geo does not exist

        :param model: model(s) to export...export items
        :type model: ModelData()
        :param export_path: path to export fbx to
        :type export_path: str
        """
        if Debug.debug: print(('calling :: {0} '.format('export_model')))

        pm.select(clear=True)
        pm.select(model.export_items)

        if pm.ls(selection=True):
            mess = ('\nExporting {0} to {1}'.format(', '.join(model.export_items), export_path))
            self.logger.info(mess)

            pm.mel.FBXExport(s=True, f=export_path)
            pm.select(clear=True)
        else:
            if model.export_items:
                out = ('Model(s) not found for export :: {0}'.format(', '.join(model.export_items)))
            else:
                out = 'No Models found in export items for export.'

            pm.confirmDialog(title='No model found', message=out, button=['OK'])

    """
    \/\/\/\/\/\/\/\/    P4    \/\/\/\/\/\/\/\/
    """

    @staticmethod
    def do_p4(path):
        """

        :param path: export path for fbx
        :type path: str
        :return: has fbx already been added to p4
        :rtype: bool
        """
        if Debug.debug : print(('calling :: {0} '.format('do_p4')))

        pass

        # path = os.path.realpath(path).replace('@', '%40').replace('\\', '/')
        # p4_path_reveal = pipelineTools.sg_p4Utils.p4_depot_local_path_reveal(path)
        # added = False
        # if p4_path_reveal:
        #     p4_path = p4_path_reveal["depotFile"]
        #     added = pipelineTools.sg_p4Utils.isP4(p4_path)
        #
        #     if added:
        #         if not pipelineTools.sg_p4Utils.isLatest(p4_path)[0]:
        #             pipelineTools.sg_p4Utils.syncFile(p4_path)
        #         pipelineTools.sg_p4Utils.checkOut(p4_path)
        #
        # return added


Exporter = FBXExport()
