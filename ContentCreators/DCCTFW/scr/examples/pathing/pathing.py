import scr
import os

'''
scr.framework_paths is a dict for commonly used paths on the project and the tool directory. It is populated at run 
time based on relative tool paths, user env vars and python __file__ location 

Only project path in scr.framework_paths from user env vars
'project_path' - C:\_p4\Projects\FishMonger

All tool paths
'tool_root_path' - C:\_p4\Tools\ContentCreators\DCCTFW
'xml_path' <project data doc> - C:\_p4\Projects\FishMonger\project_data.xml
'json_path' <maya shelf data> - C:\_p4\Projects\FishMonger\Content\Art\Maya\shelf.json
'icon_path' - C:\_p4\Tools\ContentCreators\DCCTFW\icons
'scr_path' - C:\_p4\Tools\ContentCreators\DCCTFW\scr
'framework_path' - C:\_p4\Tools\ContentCreators\DCCTFW\scr\framework
'libs_path' - C:\_p4\Tools\ContentCreators\DCCTFW\scr\libs
'site-packages_path' - C:\_p4\Tools\ContentCreators\DCCTFW\scr\libs\site-packages
'plugins_path' - C:\_p4\Tools\ContentCreators\DCCTFW\scr\plugins
'examples_path' - C:\_p4\Tools\ContentCreators\DCCTFW\scr\examples
'tool_path' - C:\_p4\Tools\ContentCreators\DCCTFW\scr\tools
'''

type(scr.framework_paths)
# Result: <class 'dict'>

scr.framework_paths['tool_path']
# Result: C:\_p4\Tools\ContentCreators\DCCTFW\scr\tools\

scr.framework_paths['site-packages_path']
# Result: C:\_p4\Tools\ContentCreators\DCCTFW\scr\libs\site-packages\

# example
ui_path = os.path.join(scr.framework_paths['examples_path'], 'qtuidialog\\', 'qt_ui_dialog.ui')



