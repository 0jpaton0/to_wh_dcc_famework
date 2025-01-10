import os
import xml.etree.ElementTree as ET


# PATHING #
def get_tool_root_path():
    """
    return path to top of framework directory

    :return: path to top of framework directory
    :rtype: path
    """
    framework_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
    return framework_root


def get_project_path():
    """
    get path to top of project directory from environment vars
y
    :return: path to top of the project directory
    :rtype: string
    """
    if os.environ.get('GameProjectPath'):
        try:
            os.path.isdir(os.environ['GameProjectPath'])
            return os.environ['GameProjectPath']
        except Exception as Argument:
            pass
            # logger.critical(Argument)
    else:
        pass
        # logger.critical('Failed to get Project path rnv var.')


def set_paths(relative_jason_path, relative_project_xml_path, relative_sitepackages_path):
    """
    creates and populates dictionary that maps path name to its path in the framework

    :param framework_tool_root: path to the top of the framework directory
    :type framework_tool_root: string
    :param framework_project_path: path to the top of the project directory
    :type framework_project_path: string
    :return: framework_paths
    :rtype: dictionary
    """

    framework_tool_root = get_tool_root_path()
    framework_project_path = get_project_path()

    framework_paths = {}
    framework_paths['tool_root_path'] = framework_tool_root + '\\'
    framework_paths['project_path'] = framework_project_path + '\\'

    # relative paths
    project_xml_path = framework_project_path + relative_project_xml_path
    framework_paths['xml_path'] = project_xml_path
    json_path = framework_project_path + relative_jason_path
    framework_paths['json_path'] = json_path
    icon_path = framework_tool_root + '\\icons\\'
    framework_paths['icon_path'] = icon_path
    scr_path = framework_tool_root + '\\scr\\'
    framework_paths['scr_path'] = scr_path
    framework_path = framework_tool_root + '\\scr\\framework\\'
    framework_paths['framework_path'] = framework_path
    libs_path = framework_tool_root + '\\scr\\libs\\'
    framework_paths['libs_path'] = libs_path
    # add site-packages after libs path
    sitepackages_path = framework_paths['libs_path'] + relative_sitepackages_path
    framework_paths['site-packages_path'] = sitepackages_path
    plugins_path = framework_tool_root + '\\scr\\plugins\\'
    framework_paths['plugins_path'] = plugins_path
    examples_path = framework_tool_root + '\\scr\\examples\\'
    framework_paths['examples_path'] = examples_path
    tool_path = framework_tool_root + '\\scr\\tools\\'
    framework_paths['tool_path'] = tool_path
    unittest_path = framework_tool_root + '\\scr\\tests\\'
    framework_paths['unittest_path'] = unittest_path

    return framework_paths


# Project Data #
class ProjectData:

    name = ''
    source = ''
    engine = ''
    docs = ''
    last_updated = ''
    author = ''
    news = ''
    news_description = ''
    vacation = ''
    vacation_description = ''

    def __init__(self):
        pass

    def __str__(self):
        return 'name : {}\nsource : {}\nengine : {}\ndocs : {}\nlast_updated : {}\nauthor : {}\nnews : {}\nnews description : {}\nvacation : {}\nvacation description : {}'. \
            format(self.name, self.source, self.engine, self.docs, self.last_updated, self.author, self.news,
                   self.news_description, self.vacation, self.vacation_description)


def get_project_XML_data(framework_paths):
    """
    populates ProjectData class with data read from the project json file

    :return: class with project data
    :rtype: ProjectData()
    """

    project_data = ProjectData()

    xml_path = framework_paths['xml_path']
    tree = ET.parse(xml_path)
    root = tree.getroot()

    pd = root.findall('ProjectData')[0]
    project_data.name = pd.findtext('Name')
    project_data.source = pd.findtext('Source')
    project_data.engine = pd.findtext('Engine')
    project_data.docs = pd.findtext('Docs')
    project_data.last_updated = pd.findtext('LastUpdated')
    project_data.author = pd.findtext('Author')

    project_data.news = pd.findtext('News')
    news = pd.findall('News')[0]
    project_data.news_description = news.findtext('description')

    project_data.vacation = pd.findtext('Vacation')
    vacation = pd.findall('Vacation')[0]
    project_data.vacation_description = vacation.findtext('description')

    return project_data

