'''
Schell Games Preference Utilities
Set of utilities read and modify preferences
'''

import os
import sys
import ast
import json
import traceback
# import sg_resources.sg_helpMenu
import pymel.core as pm
# from sg_resources.sg_CommandWindowBase_1 import BaseWindow
from functools import partial


def readPrefs(*args):
    'reads, and evaluates the prefs file and returns it as a dictionary'
    
    if os.path.exists((pm.internalVar(upd=True)+'sgPrefs.txt')):
        with open((pm.internalVar(upd=True)+'sgPrefs.txt'), 'r') as f:
            body = f.read()
    
        try:
            prefs = json.loads(body)

        except:
            # old method for reading
            print('New Preference Reading Method Failed, Trying Legacy Method')
            print(sys.exc_info()[1])
            print(traceback.print_tb(sys.exc_info()[2]))
            prefs = ast.literal_eval(body)
        
        return prefs
    else:
        return {}


def readPrefsKey(key, noKeyVal=None, *args):

    prefs = readPrefs()

    if key in prefs:
        return prefs[key]
    else:
        return noKeyVal
    
    
def readPrefsNestedKey(*keys):
    '''A method to get nested key value'''
    
    prefs = readPrefs()
    
    _prefs = prefs
    for key in keys:
        try:
            _prefs = _prefs[key]
        except:
            return None

    return _prefs


def writePrefs(prefs, keys=()):
    'takes a new or modified prefs variable and writes it to a prefs file'
    
    if keys:
        oldPrefs = readPrefs()
        for key in keys:
            if not key in prefs:
                if key in oldPrefs:
                    del oldPrefs[key]
            else:
                oldPrefs[key] = prefs[key]
        prefs = oldPrefs

    newBody = json.dumps(prefs, indent=4, sort_keys=True)
    file_path = (pm.internalVar(upd=True)+'sgPrefs.txt')
    # I am having an occasionally issues where 'with open..' is not able to open SGprefs due to
    # not being writable
    try:
        with open(file_path, 'w') as f:
            f.write(newBody)
    except Exception as e:
        print('Problem loading {0}...{1}'.format(file_path, e))

