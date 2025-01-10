from PySide6 import QtWidgets

import maya.cmds as cmds


class Browsers(object):

    def __init__(self):
        pass

    @staticmethod
    def get_open_filename(caption, directory, file_type):
        file_name, _filter = QtWidgets.QFileDialog.getOpenFileName(None, caption, directory, file_type)
        return file_name

    @staticmethod
    def open_save_file_browser(caption, directory, file_type):
        file_name, _filter = QtWidgets.QFileDialog.getOpenFileName(None, caption, directory, file_type)
        return file_name

    @staticmethod
    def get_existing_directory(caption, directory):
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(None, caption, directory)
        return folder_name

    # @staticmethod
    # def open_save_folder_browser(caption, directory, fileMode=2, fileFilter='*.fbx *.FBX'):
    #     '''
    #     generic browser
    #
    #     @param caption: name of browser
    #     @type caption: str
    #     @param directory: location to open
    #     @type directory: str
    #     @param fileMode: able to select files
    #     @type fileMode: int
    #     @param fileFilter: file types
    #     @type fileFilter: str
    #     @return: path
    #     @rtype: str
    #     '''
    #     if Debug.debug : print('calling :: {0}'.format('open_save_folder_browser'))
    #
    #     folder_name = pm.fileDialog2(fm=fileMode, dir=directory, caption=caption, fileFilter=fileFilter)
    #     if folder_name:
    #         return os.path.abspath(folder_name[0])
    #     else:
    #         return ''

    def open_prompt_dialog(self, title, message):
        '''


        @param title: name of dialog
        @type title: str
        @param message: message in dialog
        @type message: str
        @return: entered text
        @rtype: str
        '''

        result = cmds.promptDialog(
            title=title,
            message=message,
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            return cmds.promptDialog(query=True, text=True)
        else:
            return None
