"""
TODO:

-if you change the rig export name in the rig tree test influenses no longer works
-auto install
-pre load tools..?
-auto reload all tools
--wrap xtree
-look at using schemes for pathing again
-set up max (and blender)?

-try this?

# QObjects fall out of scope, so making them global here to keep them in scope
main_window = None
main_menu_bar = None

def getMainWindow():
    Gets the Maya main window widget.
    Returns:
        (QWidget): Maya main window.
    global main_window ### <-

-unit test bug or as designed..? (https://github.com/pytest-dev/pytest/issues/3143)
-- unit tests only print to file once every time maya is open. generally print to file using pytest has
been a pain. i tried stdout which did not work so i fell back to cmds.scriptEditorInfo.

this is what i am using now and seems bugged as it only fires once
    cmds.scriptEditorInfo(historyFilename=self.unittest_out, writeHistory=True)
    tests.run_unittests()
    # stop output capture
    cmds.scriptEditorInfo(writeHistory=False)

this is worth looking at agian maybe..?
    pytest -s
    retcode = pytest.main(["-x", "C:\\_p4\\Tools\\ContentCreators\\DCCTFW\\scr\\tests\\"])
    retcode = pytest.main(["-qq", "C:\\_p4\\Tools\\ContentCreators\\DCCTFW\\scr\\tests\\"])
    retcode = pytest.main(["-s", "C:\\_p4\\Tools\\ContentCreators\\DCCTFW\\scr\\tests\\"])
    retcode = pytest.main(["-r", "C:\\_p4\\Tools\\ContentCreators\\DCCTFW\\scr\\tests\\"])
    retcode = pytest.main(["--capture=tee-sys", "C:\\_p4\\Tools\\ContentCreators\\DCCTFW\\scr\\tests\\"])

this is more pythonic but i think mayapy gets in its way...if freezes

    from io import StringIO
    from contextlib import redirect_stdout

    temp_stdout = StringIO()
    with redirect_stdout(temp_stdout):
        result = pytest.main(sys.argv)
    stdout_str = temp_stdout.getvalue()
    # or whatever you want to do with it
    print(stdout_str.upper())

Maybe look at this as well

    cmds.cmdFileOutput(o="c:\\temp\\dbOutput.txt")
    ManageToolBar.run_unittests()
    cmds.cmdFileOutput(c=True)

"""
import sys
import os

def get_tool_root_path():
    """
    return path to top of framework directory

    :return: path to top of framework directory
    :rtype: path
    """
    framework_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.'))

    return framework_root


class DCCTFW(object):
    # called from ...\Tools\ContentCreators\DCCTFW\userSetup.mel via User Env Var MAYA_SCRIPT_PATH
    # sets up MTF

    def __init__(self):
        print('\nWelcome to the DCCF\n...initializing framework')

        # add libs\site-packages to sys.path. need to add it first as it contains a pathing module used to set up
        # project pathing for all framework uses
        tool_root_path = get_tool_root_path()
        if tool_root_path:
            site_packages = os.path.join(tool_root_path, 'DCCTFW\\scr\\libs\\site-packages')

            sys.path.append(site_packages)

            # initialize logging and pytest
            import scr
            # initializes maya shelf and menu bar
            import scr.framework
        else:
            print('Error getting tool root on initialization')




