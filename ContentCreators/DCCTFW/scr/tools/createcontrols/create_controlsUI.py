from PySide6 import QtUiTools
from PySide6.QtWidgets import QDialog, QColorDialog
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QButtonGroup as ButtonGroup
from shiboken6 import wrapInstance

import os
import scr

from maya import OpenMayaUI as OpenMayaUI
import pymel.core as pm


"""
ToDo: 
    Colors are not always correct. it seems like some color are not applied properly
    Dialog gets obscured by Maya when not in focus. Maybe make it dockable
    Write Curve Points may not work with all curve shape. i just use nurbs circle for this 
    Make the setting of colors part of the control class..?
    When you select multiples joint ou can assume the color will be the same on all controls
    Add parenting for controls when more then one joint is selected
    
Usage:
    Change .UI path if needed
    Evaluate script in Maya script editor
"""


class ControlsUI(QtWidgets.QMainWindow):

    def __init__(self):
        maya_main = self.get_maya_main_window()
        super(ControlsUI, self).__init__(maya_main)
        ui_path = os.path.join(scr.framework_paths['tool_path'], 'createcontrols', 'create_controls.ui')
        self.ui = self.load_ui(ui_path, maya_main)
        self.ui.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.ui.btn_create_control.clicked.connect(self.create_control_btn_pressed)
        self.ui.btn_write_curve_points.clicked.connect(self.write_curve_points_btn_pressed)
        self.ui.btn_pick_color.clicked.connect(self.pick_color_btn_pressed)
        self.ui.sld_scale.valueChanged.connect(self.scale_sld_changed)

        self.group_orient_radio_buttons = ButtonGroup()
        self.group_orient_radio_buttons.addButton(self.ui.rad_down_x, 0)
        self.group_orient_radio_buttons.addButton(self.ui.rad_down_y, 1)
        self.group_orient_radio_buttons.addButton(self.ui.rad_down_z, 2)

        self.ui.rad_down_y.setChecked(True)
        self.color_dialog = QColorDialog()
        self.rgb_color = (0, 0, 40, 255)
        self.scale = self.ui.sld_scale.value()

        self.ui.show()

    def run(self):
        """
        opens ui, probably called from user request in SG Tools drop down
        """
        self.ui.show()


    @staticmethod
    def get_maya_main_window():
        """
        gets the pointer to the window to use as ui

        :return: maya_main
        :rtype: python wrapper for a C++ object instantiated at a given memory address
        """
        main_window_pointer = OpenMayaUI.MQtUtil.mainWindow()
        maya_main = wrapInstance(int(main_window_pointer), QtWidgets.QWidget)
        return maya_main

    @staticmethod
    def load_ui(ui_path, parent=None):
        """
        loads the .ui file from a path

        :param ui_path: path to .ui file
        :type ui_path: str
        :param parent: this is a top level ui element with no parent
        :type parent: None
        :return: ui
        :rtype: QUiLoader
        """
        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(ui_path)
        uifile.open(QtCore.QFile.ReadOnly)
        ui = loader.load(uifile, parent)
        uifile.close()
        return ui

    @staticmethod
    def write_curve_points_btn_pressed():
        """ initializes GetControlShape class which then reads the point locations from
        the selected curve and write them to the script editor window
        """
        get_control_shape = GetControlShape()
        get_control_shape.write_control_points()

    def scale_sld_changed(self):
        self.scale = self.ui.sld_scale.value() * 10

    def pick_color_btn_pressed(self):
        self.rgb_color = self.color_dialog.getColor().getRgb()

    def create_control_btn_pressed(self):
        """Events for Create Control button press
        """
        shape_index = self.ui.cbx_create_shape.currentIndex()
        constraint_index = self.ui.cbx_constraint_type.currentIndex()

        create_control = CreateControl()
        create_control.create_control(shape_index, constraint_index, self.group_orient_radio_buttons.checkedId(),
                                      self.rgb_color, self.scale)


class CreateControl(object):

    def __init__(self):
        self.color_dialog = QColorDialog()
        self.scale_multiply = .35

    def get_shape(self, name, scale):

        # dictionary that returns function that create curve controls
        shape_switcher = {
            0: self.circle_shape(name, scale),
            1: self.diamond_shape(name, scale),
            2: self.octagon_shape(name, scale),
            3: self.pentagon_shape(name, scale),
            4: self.square_shape(name, scale),
            5: self.triangle_shape(name, scale),
            6: self.cross_shape(name, scale),
            7: self.sphere_shape(name, scale)
        }

        return shape_switcher

    @staticmethod
    def circle_shape(name, scale):
        """ function called by shape_switch dict
        :return: function that creates a Circle Node
        """
        circle_control = CircleControl(name, scale)
        return circle_control.create_curve

    @staticmethod
    def octagon_shape(name, scale):
        """ function called by shape_switch dict
        :return: function that creates a Octagon Node
        """
        octagon_control = OctagonControl(name, scale)
        return octagon_control.create_curve

    @staticmethod
    def pentagon_shape(name, scale):
        """ function called by shape_switch dict
        :return: function that creates a Pentagon Node
        """
        pentagon_control = PentagonControl(name, scale)
        return pentagon_control.create_curve

    @staticmethod
    def square_shape(name, scale):
        """ function called by shape_switch dict
        :return: function that creates a Square Node
        """
        square_control = SquareControl(name, scale)
        return square_control.create_curve

    @staticmethod
    def triangle_shape(name, scale):
        """function called by shape_switch dict
        :return: Triangle Node
        """
        triangle_control = TriangleControl(name, scale)
        return triangle_control.create_curve

    @staticmethod
    def cross_shape(name, scale):
        """function called by shape_switch dict
        :return: Cross Node
        """
        cross_control = CrossControl(name, scale)
        return cross_control.create_curve

    @staticmethod
    def sphere_shape(name, scale):
        """function called by shape_switch dict
        :return: function that creates a Sphere Node
        """
        sphere_control = SphereControl(name, scale)
        return sphere_control.create_curve

    @staticmethod
    def diamond_shape(name, scale):
        """function called by shape_switch dict
        :return: function that creates a Sphere Node
        """
        diamond_control = DiamondControl(name, scale)
        return diamond_control.create_curve

    @staticmethod
    def get_joint_radius(joint_node):
        """
        :param joint_node: joint
        :return: joint radius
        """
        return joint_node.getAttr('radius')

    @staticmethod
    def create_group(base_name, children):
        """ creates group to put control in so the control is zeroed out
        :param base_name: string
        :param children: control transform
        :return:
        """
        return pm.group(children, name='grp_' + base_name)

    @staticmethod
    def get_selected_joints():
        """
        :return: selected joint in the viewport
        """
        return pm.ls(selection=True, visible=True, type='joint')

    @staticmethod
    def remove_all_constraints(node):
        """removes all constraints from given node after it has been placed at joints center by a parent constraint
        :param node: group
        """
        constraints = node.listConnections(type='constraint')
        pm.delete(constraints)

    @staticmethod
    def parent_constraint(parent_node, child_node, maintain_offset=False):
        """ Add constraints from parent to child
        :param parent_node: joint or curve transform
        :param child_node: group or joint
        :param maintain_offset: bool
        :return: constrained node
        """
        return pm.parentConstraint(parent_node, child_node, maintainOffset=maintain_offset)

    @staticmethod
    def point_constraint(parent_node, child_node, maintain_offset=False):
        """ Add constraints from parent to child
        :param parent_node: joint or curve transform
        :param child_node: group or joint
        :param maintain_offset: bool
        :return: constrained node
        """
        return pm.pointConstraint(parent_node, child_node, maintainOffset=maintain_offset)

    @staticmethod
    def orient_constraint(parent_node, child_node, maintain_offset=False):
        """ Add constraints from parent to child
        :param parent_node: joint or curve transform
        :param child_node: group or joint
        :param maintain_offset: bool
        :return: constrained node
        """
        return pm.orientConstraint(parent_node, child_node, maintainOffset=maintain_offset)

    def add_constraint(self, parent_node, child_node, maintain_offset, constraint_index):
        """ figures out from dialog widget index what constraint type to use
        :param parent_node: node to be parent
        :param child_node: node to be child
        :param maintain_offset: bool
        :param constraint_index: constraint type
        :return:
        """
        if constraint_index == 0:
            self.parent_constraint(parent_node, child_node, maintain_offset)
        elif constraint_index == 1:
            self.orient_constraint(parent_node, child_node, maintain_offset)
        else:
            self.point_constraint(parent_node, child_node, maintain_offset)

    @staticmethod
    def orient_control_down_joint(orient_index, control_shape):
        """ changes to way the curve is facing based on dialog widget index
        :param orient_index: int, from dialog drop down
        :param control_shape: curve
        """
        z = (90, 0, 0)
        x = (0, 0, 90)

        if orient_index == 0:
            pm.xform(control_shape, ro=x)
        elif orient_index == 2:
            pm.xform(control_shape, ro=z)

    def get_control_shape(self, base_name, shape_index, scale):
        """ requests function from dictionary. the function creates the shape the index suggested
        :param base_name: string
        :param shape_index: int, from dialog drop down
        :return: requested shape
        """
        shape_switcher = self.get_shape('cnt_' + base_name, scale)
        control_shape = shape_switcher.get(shape_index, None)
        control_shape = control_shape()
        return control_shape

    @staticmethod
    def change_node_color(control_shape, rgb_color):
        """ sets shape color to what the users selected in the color picker
        :param control_shape: curve
        :param rgb_color: rgb values
        """
        control_shape.setAttr('overrideEnabled', True)
        control_shape.setAttr('overrideRGBColors', True)
        control_shape.setAttr('overrideColorRGB', rgb_color)

    def create_control(self, shape_index, constrain_index, orient_index, rgb_color, scale):
        """ controls the control creation process
        :param shape_index: int, what style shape to create
        :param constrain_index: int, what style constraint to use
        :param orient_index: int, which way the curve should face
        :param rgb_color: tuple, color
        :param scale: float, scale multiplier
        """
        selected_joints = self.get_selected_joints()

        if len(selected_joints) > 0:
            for joint_node in selected_joints:
                joint_node_name = joint_node.name()
                base_name = joint_node_name.replace('jnt_', '')

                # build control
                radius = self.get_joint_radius(joint_node)
                print('radius, scale : {}, {} '.format(radius, scale))
                scale = (radius * scale) * self.scale_multiply
                print(' scale : {} '.format(scale))
                control_shape = self.get_control_shape(base_name, shape_index, scale)
                if orient_index != 1:
                    self.orient_control_down_joint(orient_index, control_shape)
                self.change_node_color(control_shape, rgb_color)

                # clean up transform and history
                node_utils = NodeUtils()
                node_utils.clean_node(control_shape)

                control_group = self.create_group(base_name, control_shape)
                self.parent_constraint(joint_node, control_group)
                self.remove_all_constraints(control_group)
                self.add_constraint(control_shape, joint_node, False, constrain_index)
        else:
            pm.confirmDialog(title='Error', message='No joints selected.')


class Controls(object):

    def __init__(self, name, scale=1):
        """ default point values for curve. these will almost always be overwritten by child classes
        """
        self.points = [(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9)]
        self.degree = 1
        self.name = name
        self.scale = scale

    def create_curve(self):
        """ creates a curve base on initialized points and degree. this will sometimes be overwritten by child classes
        :return: curve
        """
        control = pm.curve(name=self.name, point=self.points, degree=self.degree)
        pm.scale(control, [self.scale, self.scale, self.scale])
        return control

    @staticmethod
    def add_under_one_transform(parent_trans, child_trans):
        """ puts two shapes under curve transform. gets shape from child and puts it under parent trans
        :param parent_trans: parent transform
        :param child_trans: child transform
        """
        import maya.mel as mel

        shape = child_trans.getShape()
        cmd_line = ('parent -s -r {} {}'.format(shape.name(), parent_trans.name()))
        mel.eval(cmd_line)
        pm.delete(child_trans)


class CircleControl(Controls):
    """child of Controls(). overwrite create_curve with simple circle
    """
    def create_curve(self, normal=(0, 1, 0)):
        """ overwrites parent method
        :return: circle control
        """
        scale_offset = 3.7
        control = pm.circle(name=self.name, normal=normal, center=(0, 0, 0), radius=(self.scale * scale_offset))[0]
        return control


class SphereControl(Controls):
    """ child of Controls(). overwrites create_curve and creates a 3 circles which are then call parents
    add_under_one_transform()
    """
    def create_curve(self):
        """ overwrites parent method
        :return: sphere control
        """
        circle = CircleControl('None', self.scale)
        c1 = circle.create_curve((1, 0, 0))
        c2 = circle.create_curve((0, 1, 0))
        self.add_under_one_transform(c1, c2)
        c3 = circle.create_curve((0, 0, 1))
        self.add_under_one_transform(c1, c3)
        node_utils = NodeUtils()
        node_utils.clean_node(c1)

        c1.rename(self.name)
        return c1


class SquareControl(Controls):
    """ child of Controls(). overwrites points and degrees in __init__
    """
    def __init__(self, name, scale=1):
        """
        :param name: string, name of control
        :param scale: int, scale change if needed
        """
        self.points = [(2.4591395573886306e-16, 2.4591395573886306e-16, -4.016079671462465),
                        (-4.016079671462465, 3.0115773876126253e-32, -4.918279114777261e-16),
                        (-7.377418672165891e-16, -2.4591395573886306e-16, 4.016079671462465),
                        (4.016079671462465, -6.023154775225251e-32, 9.836558229554523e-16),
                        (1.2295697786943153e-15, 2.4591395573886306e-16, -4.016079671462465)]

        self.degree = 1
        self.name = name
        self.scale = scale


class DiamondControl(Controls):
    """ child of Controls(). overwrites create_curve and creates a 3 circles which are then call parents
    add_under_one_transform()
    """

    def create_curve(self):
        """ overwrites parent method
        :return: cube control
        """
        square = SquareControl('None')
        node_utils = NodeUtils()

        s1 = square.create_curve()
        s1.setAttr('rx', 90)
        node_utils.clean_node(s1)
        s2 = square.create_curve()
        s2.setAttr('rz', 90)
        node_utils.clean_node(s2)
        self.add_under_one_transform(s1, s2)
        s3 = square.create_curve()
        self.add_under_one_transform(s1, s3)
        node_utils = NodeUtils()
        node_utils.clean_node(s1)
        s1.rename(self.name)
        pm.scale(s1, [self.scale, self.scale, self.scale])
        return s1


class OctagonControl(Controls):
    """ child of Controls(). overwrites points and degrees in __init__
    """
    def __init__(self, name, scale):
        self.points = [(2.4427634641829964e-16, 2.4427634641829974e-16, -3.989335481681321),
                        (-2.8208861715249633, 1.7272946103585402e-16, -2.8208861715249647),
                        (-3.9893354816813207, 1.1356522544005551e-31, -1.5765439759684875e-15),
                        (-2.820886171524964, -1.7272946103585384e-16, 2.8208861715249625),
                        (-2.442763464182997e-16, -2.442763464182996e-16, 3.9893354816813194),
                        (2.820886171524964, -1.7272946103585384e-16, 2.8208861715249625),
                        (3.9893354816813207, 8.365000086519744e-32, -1.0879912831318882e-15),
                        (2.820886171524964, 1.7272946103585404e-16, -2.820886171524965),
                        (2.442763464182997e-16, 2.442763464182998e-16, -3.989335481681322)]

        self.degree = 1
        self.name = name
        self.scale = scale


class PentagonControl(Controls):
    """ child of Controls(). overwrites points and degrees in __init__
    """
    def __init__(self, name, scale):
        self.points = [(1.3040819086416795e-17, 2.1263676358327497e-16, -3.47262188136728),
                        (-3.651330727320916, 5.019673072120466e-17, -0.8197748241558889),
                        (-2.2566464936512007, -2.1263676358327492e-16, 3.47262188136728),
                        (2.2566464936512, -2.1263676358327497e-16, 3.47262188136728),
                        (3.651330727320916, 5.0196730721204587e-17, -0.8197748241558878),
                        (8.655225327462043e-16, 2.1263676358327497e-16, -3.47262188136728)]

        self.degree = 1
        self.name = name
        self.scale = scale


class TriangleControl(Controls):
    """ child of Controls(). overwrites points and degrees in __init__
    """
    def __init__(self, name, scale):
        self.points = [(9.183081642692758e-16, 1.8913076212063658e-16, -3.088739745244372),
                        (-3.5665694467470654, -1.8913076212063624e-16, 3.0887397452443666),
                        (3.5665694467470654, -1.8913076212063639e-16, 3.0887397452443692),
                        (3.4330474845823783e-15, 1.8913076212063653e-16, -3.088739745244371)]

        self.degree = 1
        self.name = name
        self.scale = scale


class CrossControl(Controls):
    """ child of Controls(). overwrites points and degrees in __init__
    """
    def __init__(self, name, scale):
        self.points = [(2.4556551909882437e-16, 2.455655190988242e-16, -4.0103892692945635),
                        (-1.1718253273425385, 1.7322853072073328e-16, -2.829036598002651),
                        (-0.6279168261233541, 3.844881656213676e-17, -0.6279168261233545),
                        (-2.8290365980026495, 7.175360681449211e-17, -1.1718253273425399),
                        (-4.010389269294563, 8.638091516413883e-32, -1.1325904982009639e-15),
                        (-2.8290365980026495, -7.175360681449193e-17, 1.1718253273425374),
                        (-0.6279168261233532, -3.844881656213656e-17, 0.6279168261233523),
                        (-1.1718253273425383, -1.7322853072073308e-16, 2.829036598002648),
                        (4.222984565732482e-16, -2.45565519098824e-16, 4.010389269294562),
                        (1.171825327342539, -1.7322853072073308e-16, 2.8290365980026473),
                        (0.6279168261233536, -3.8448816562136586e-17, 0.6279168261233523),
                        (2.8290365980026495, -7.175360681449188e-17, 1.1718253273425365),
                        (4.010389269294563, 1.5172918514474569e-31, -2.1998087365714835e-15),
                        (2.8290365980026486, 7.175360681449214e-17, -1.1718253273425407),
                        (0.6279168261233532, 3.844881656213676e-17, -0.627916826123355),
                        (1.1718253273425376, 1.7322853072073328e-16, -2.829036598002651),
                        (-1.3127837574693454e-15, 2.455655190988242e-16, -4.0103892692945635)]

        self.degree = 1
        self.name = name
        self.scale = scale


class NodeUtils(object):
    def __init__(self):
        pass

    def delete_history(self, node):
        """ delete history of given node
        :param node: node
        """
        pm.delete(node, constructionHistory=True)

    def freeze_transform(self, node):
        """ freeze transform of given node
        :param node: node
        """
        pm.makeIdentity(node, apply=True, t=1, r=1, s=1, n=2)

    def clean_node(self, node):
        """ freeze transform and deletes history of given node
        :param node: node
        """
        self.freeze_transform(node)
        self.delete_history(node)


class GetControlShape(object):

    def __init__(self):
        self.cnt_dict = {
            'degree': None,
            'spans': None,
            'form': None,
            'control_points': None,
            'points': None,
            'knots': None
        }

    def get_control_shape(self, shapes):
        """ populates shape dictionary with data to write to script editor
        :param shapes: list of shapes
        :return: list of shape dictionaries
        """
        shape_datas = []

        for shape in shapes:
            shape_data = self.cnt_dict
            num_control_points = shape.getAttr('controlPoints', s=1)

            points = []
            for index in range(num_control_points):
                points.append(shape.getAttr('cv[' + str(index) + ']'))

            shape_data.update({
                'degree': shape.getAttr('degree'),
                'spans': shape.getAttr('spans'),
                'form': shape.getAttr('form'),
                'control_points': shape.getAttr('controlPoints', s=1),
                'knots': shape.getKnots(),
                'points': points
            })

            shape_datas.append(shape_data)

        return shape_datas

    def write_control_points(self):
        """ starting point for writing shape
        """
        shape_datas = self.get_shape_data()

        for shape_data in shape_datas:
            print('...start...')
            for vector in shape_data['points']:
                print('{},'.format(tuple(vector)))
            print('...end...')

    @staticmethod
    def get_all_shapes(transform):
        """ gets shapes from transform
        :param transform: transform
        :return: list of shapes
        """
        return transform.listRelatives(type='shape')

    def get_shape_data(self):
        """ gets selected curve from viewport and calls function to populates dictionaries
        :return: list of shape dictionaries
        """
        curv = pm.ls(selection=True)[0]
        pm.select(clear=True)
        shapes = self.get_all_shapes(curv)
        shape_datas = self.get_control_shape(shapes)

        return shape_datas


global Controls_UI
Controls_UI = None


Controls_UI = ControlsUI()