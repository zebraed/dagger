#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

from maya import cmds
from maya.api import OpenMaya as om

from .maya import apiundo as apiundo


class DagModifier(om.MDagModifier):
    """
    Undoable MDagModifier command class.
    """
    def __init__(self, *args, **kwargs):
        super(DagModifier, self).__init__(*args, **kwargs)
        apiundo.commit(self.undoIt, self.doIt)


def create_node(nodeName, nodeType, uuidStr=None, parent=None):
    """
    Create node use api2.0.

    Args:
        nodeName (str): The name of the node to be created
        nodeType (str): Node type name of the node to be created
        uuidStr (str, optional): Used when specifying UUID. Defaults to None.
        parent (str, optional): Used when specifying parent. Defaults to None.

    Returns:
        str: new created node name.
    """
    dg_modifier = DagModifier()
    if parent:
        sel = om.MGlobal.getSelectionListByName(parent)
        parent = sel.getDependNode(0)
        node_obj = dg_modifier.createNode(nodeType, parent)
    else:
        node_obj = dg_modifier.createNode(nodeType)

    node_fn = om.MFnDependencyNode(node_obj)
    if uuidStr:
        uuid = om.MUuid(uuidStr)
        node_fn.setUuid(uuid)
    node_fn.setName(nodeName)
    dg_modifier.doIt()
    return node_fn.name()


def get_dagPathObj(node):
    selection_list = om.MGlobal.getSelectionListByName(node)
    return selection_list.getDagPath(0)


def get_mObject(node):
    selection_list = om.MGlobal.getSelectionListByName(node)
    mObj = selection_list.getDependNode(0)
    return mObj


def get_all_childs(node):
    return cmds.listRelatives(node, c=True, ad=True)


def get_parentNode(node):
    return cmds.listRelatives(node, p=True)


def get_instanceNumber(shape):
    sl = om.MSelectionList()
    sl.add(shape)
    path = om.MDagPath()
    sl.getDagPath(0, path)
    return path.instanceNumber() if path.isValid() else -1


def get_instancePath(shape, iid):
    sl = om.MSelectionList()
    sl.add(shape)
    obj = om.MObject()
    sl.getDependNode(0, obj)
    if obj.isNull():
        return None
    paths = om.MDagPathArray()
    om.MDagPath.getAllPathsTo(obj, paths)
    if iid >= paths.length():
        return None
    return paths[iid].partialPathName()


def get_allInstancePaths(shape):
    sl = om.MSelectionList()
    sl.add(shape)
    obj = om.MObject()
    sl.getDependNode(0, obj)
    if obj.isNull():
        return []
    paths = om.MDagPathArray()
    om.MDagPath.getAllPathsTo(obj, paths)
    names = set()
    for i in range(paths.length()):
        names.add(paths[i].partialPathName())
    lst = list(names)
    lst.sort()
    return lst


def get_uuid(node):
    return cmds.ls(getNode(node, long=True), uuid=True)[0]


def get_nodeType(node):
    return cmds.nodeType(getNode(node, long=True))


def has_shape(node):
    return True if cmds.listRelatives(getNode(node, long=True), c=True, s=True) else False


def get_shapes(node):
    return cmds.listRelatives(getNode(node, long=True), c=True, s=True) or []


def get_fullpath(node):
    return cmds.ls(node, long=True)[0]


def get_visibility(node):
    return cmds.getAttr(node + '.v')


def get_translate(node):
     return cmds.getAttr(node + '.t')


def get_rotate(node):
     return cmds.getAttr(node + '.r')


def get_scale(node):
     return cmds.getAttr(node + '.s')


def get_pivot(node):
     return cmds.xform(node, q=True, pivots=True, ws=True)

def getNode(name, long=False):
    """
    Get node name from current scnene.

    Args:
        name (_type_): _description_
        long (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    if cmds.objExists(name):
        if long:
            return get_fullpath(name)
        else:
            return cmds.ls(name)[0]
    else:
        return None
