import maya.cmds as cmds
from scr import project_data

if project_data.engine == 'Unreal 5':
    '''
    game: 15 fps
    film: 24 fps
    pal: 25 fps
    ntsc: 30 fps
    show: 48 fps
    palf: 50 fps
    ntscf: 60 fps
    
    '''

    # set time frames to 30 fps
    cmds.currentUnit(time="ntsc")

    # set units to centimeters
    cmds.currentUnit(linear='centimeter')

    # set grid size
    cmds.grid( query=True, size=True ) # l and w
    cmds.grid( query=True, divisions=True ) # subdivision
    cmds.grid( query=True, spacing=True ) # gris lines

else:
    pass

