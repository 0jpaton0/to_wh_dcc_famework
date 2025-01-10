# fileinfo in used in the fbx exporter
# it is pretty good for storing data in a maya file persistently
# the data is readable if you use .ma and can be used to batch

import pymel.core as pm
import pprint

# look at functions
dir(pm.fileInfo)

# removes all fileinfo data
# pm.fileInfo.clear()

# print keys to editor
pm.fileInfo.keys()
key = '_fbx_export_actor_Rig_Cyl:joint1'
# find key
pm.fileInfo.has_key(key)
# get key value
fileinfo_str = pm.fileInfo[key]

#print
pprint.pprint(fileinfo_str)