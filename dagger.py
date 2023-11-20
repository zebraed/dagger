#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import re
from distutils.util import strtobool

from maya import cmds
from maya.api import OpenMaya as om

from xml import etree
if not sys.version_info.major == 2:
    from xml.etree import ElementTree as ET
    dict_get_keys = lambda d: d.keys()
    dict_get_values = lambda d: d.values()
    dict_get_items = lambda d: d.items()
else:
    from xml.etree import cElementTree as ET
    dict_get_keys = lambda d: list(d)
    dict_get_values = lambda d: list(d.values())
    dict_get_items = lambda d: list(d.items())
    unicode = str
    basestring = str
    from importlib import reload

from xml.dom import minidom

from . import utils
from . import options


class XMLmixin:
    TAG_ROOT  = options.TagOption.TAG_ROOT
    TAG_NODE  = options.TagOption.TAG_NODE
    TAG_OPT   = options.TagOption.TAG_OPT

    @classmethod
    def __create_new_element(cls, name, tag, options=None):
        """Private Method
        Create New element tag data.

        Args:
            name (str): New TAG name attribute
            tag (str): New TAG name.The constant is usually used.
            options (dict, optional): can set any attributes in dictionary.
            The key and value of the dictionary are set in the following attributes:
            name: option's name
            value: option's value.
            type: option's value type.

        Returns:
            Element: Element data with the new TAG name created.
        """
        ele = ET.Element(tag)
        ele.set('name', name.split('|')[-1])
        ele.set('fullpath', name)
        if options:
            for k, v in dict_get_items(options):
                ele_opt = ET.SubElement(ele, cls.TAG_OPT)
                ele_opt.set('name', k)
                ele_opt.set('value', str(v))
                match = re.search(r"'(.+?)'", str(type(v)))
                type_name = match.group(1)
                ele_opt.set('type', type_name)
        return ele

    @classmethod
    def create_new_nodeTag(cls, name, options=None):
        return cls.__create_new_element(name, cls.TAG_NODE, options)

    @classmethod
    def find_named_element(cls, ele, fullpathName, options=None):
        """
        Find and return the Elementtag that has already been created.

        Args:
            ele (Element): Element data.
            fullpathName (str): Full pass name to find.
            options (dict, optional): can set any attributes in dictionary.

        Returns:
            Element: target Element data.
        """
        split_node_list = fullpathName.split('|')[1:]
        ele_curr = ele
        target_fp = ''
        for i_node in split_node_list:
            target_fp += ''.join(['|', i_node])
            ele_pre = ele_curr
            for grp in ele_curr.findall(cls.TAG_NODE):
                if grp.attrib['fullpath'] == target_fp:
                    ele_curr = grp
                    break
            if ele_curr is ele_pre:
                ele_new = cls.create_new_nodeTag(target_fp, options)
                ele_curr.append(ele_new)
                ele_curr = ele_new
        return ele_curr

    @staticmethod
    def restore_option(options):
        """
        Restore from xml options attrib.

        Args:
            options (list): options attrib list.

        Returns:
            dict: restore option dict.
        """
        restore_opt = dict()
        for i_opt in options:
            k = i_opt.attrib['name']
            v = i_opt.attrib['value']
            typ = i_opt.attrib['type']
            if typ == 'bool':
                typ_eval = lambda x, y : x((strtobool(y)))
            else:
                typ_eval = lambda x, y : x(y)
            if typ == 'NoneType':
                restore_opt[k] = None
            else:
                restore_opt[k] = typ_eval(eval(typ), v)
        return restore_opt

    @staticmethod
    def isEqual(xml1, xml2):
        rootA = etree.fromstring(xml1)
        rootB = etree.fromstring(xml2)
        return etree.tostring(rootA) == etree.tostring(rootB)


class NTree(object):
    """
    N-array Tree data class.

    N-array tree is a tree data structure where each node can have at most N children.
    It is a generalization of binary tree where each node can have at most 2 children.

            +---+
            | a |
        +----+--+-+
        |         |
        +---+    +---+
        | b |    | c |
    +--+    +    +   +
    |       |    |   |
    d1      d2   d3  d4

    The above diagram shows a sample N-array tree where each node can have at most 3 children (N = 3).
    The node "a" has 3 children "b", "c", and "d". The nodes "b" and "c" have 2 children each, while the
    nodes "d1", "d2", "d3", and "d4" are leaf nodes with no children.
    """
    def __init__(self, name, parent=None, opt=None):
        super(NTree, self).__init__()
        self.name = name
        self.short_name = None
        if name.startswith('|'):
            self.short_name = name.split('|')[-1]
        if parent is None:
            parent = list()
        self.childs = list()
        self.parent = parent
        if opt:
            for k, v in dict_get_items(opt):
                setattr(self, k, v)
        self.opt = opt

    def __str__(self):
        return str(self.name)

    def __call__(self, name, parent, opt=None):
        return self.__class__(name, parent, opt=opt)

    def has_children(self):
        return True if self.childs else False

    def has_parent(self):
        return True if self.parent else False

    def add(self, args, opt=None):
        if not isinstance(args, (list, tuple)):
            chs = [args]
        else:
            chs = args
        if isinstance(chs[0], (list, tuple)):
            chs = args[0]
        rets = list()
        for ch in chs:
            tree_obj = self(ch, parent=self, opt=opt)
            self.childs.append(tree_obj)
            rets.append(tree_obj)
        return rets

    def printout(self, depth=0, long=False):
        tab = "\t" * depth
        if not long:
            if self.short_name:
                name = self.short_name
            else:
                name = self.name
        else:
            name = self.name
        print(tab + name)

        if len(self.childs) < 1:
            return
        for ch in self.childs:
            ch.printout(depth + 1)

    def find_add(self, par, name, opt=None):
        if self.name != par:
            for ch in self.childs:
                ch.find_add(par, name, opt=opt)
        else:
            return self.add(name, opt=opt)
        return 0

    def find(self, par, name):
        ret = None
        if self.name != par:
            for ch in self.childs:
                ret = ch.find(par, name)
                if ret:
                    return ret
        else:
            return self

    def sibling(self):
        if self.has_parent():
            if self.parent.childs:
                ch_list = self.parent.childs
                sibling_list = list()
                for i_ch in ch_list:
                    if i_ch.name == self.name:
                        continue
                    else:
                        sibling_list.append(i_ch)
                return sibling_list


class DAGtree(NTree):
    def __init__(self, name, parent=None, opt=None):
        super(DAGtree, self).__init__(name, parent, opt)

    @property
    def fullpath(self):
        return utils.getNode(self.name, long=True)

    def restoreAttrs(self, attrs):
        for attr in attrs:
            if hasattr(self, attr):
                print(self.opt)
                val = self.opt[attr]
                print(attr)
                print(val)
                if val is not None:
                    cmds.setAttr(self.name + '.' + attr, val)
                    print('Restore {}: '.format(attr) + self.name)


class DAGstructure(XMLmixin, object):
    """
    DAG structure data class.

    e.g.)
    dag_tree = DAGstructure('Euclid')

    # set root node name and construct dag hierarchy.
    dag_tree.construct('all)

    # print out.
    dag_tree.output()

    # get treeObj by name.
    dag_pPlane1 = dag_tree.get_obj('pPlane1')

    """
    def __init__(self, name, xml_path=None, attrib_opt=None, **opt):
        super(DAGstructure, self).__init__()
        self.name = name
        self.opt  = opt
        self.root = None
        if attrib_opt is None:
            attrib_opt = options.attrib_opt
        self.set_option_attrib(attrib_opt)
        if xml_path:
            self.set_xml_path(xml_path)

    def __eq__(self, rhs):
        if isinstance(rhs, DAGstructure):
            return self.__dict__ == rhs.__dict__
        else:
            return False

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def set_option_attrib(self, opt):
        self.attrib_opt = opt

    def traverse(self, root='', topdown=True):
        """
        Traverse all and generate DAG tree structure data.

        Args:
            root (str, optional): root node name. Defaults to ''.
            topdown (bool, optional): Defaults to True.
        """
        if root == '' or root is None:
            root = self.root
        childs = root.childs
        childs_list = [i_child for i_child in childs] if childs else []

        if topdown:
            yield (root, childs_list)
        for name in childs_list:
            for x in self.traverse(name, topdown):
                yield x
        if not topdown:
            yield (root, childs_list)

    def construct(self, name, parent=''):
        """
        Construct dag DAGtree data hierarchy from scene recursively.

        Args:
            name (str): top dag node name.
            parent (str, optional): Use if you want to specify parent node. Defaults to ''.
        """
        def _set_option_attrib(name, opt):
            set_opt = dict()
            for k , v_func in dict_get_items(opt):
                set_opt[k] = v_func(name)
            return set_opt

        def _get_parent(nodes, fullpath_names):
            """
            Get parent node from fullpath name list.

            Args:
                nodes (obj):
                fullpath_names (node): fullpath

            Returns:
                _type_: _description_
            """
            node = fullpath_names[-1]
            for name in reversed(fullpath_names):
                if name == node:
                    continue
                if name in nodes:
                    return name
            return None

        opt = _set_option_attrib(name, self.attrib_opt)
        self.root = DAGtree(name, opt=opt)

        def __construct(dagPath, parent='', __construct=None):
            fullpath_name = dagPath.fullPathName()
            short_nodename = fullpath_name.split('|')[-1]
            if parent != '':
                _parent = _get_parent(utils.get_parentNode(fullpath_name),
                                      fullpath_name.split('|')
                                      )
                if _parent:
                    if self.child_list:
                        if short_nodename in self.child_list:
                            # TODO
                            if not 'expandShape' in self.opt:
                                _fp_name = utils.getNode(short_nodename, long=True)
                                if not cmds.objectType(_fp_name, isa='shape'):
                                    opt = _set_option_attrib(short_nodename,
                                                             self.attrib_opt
                                                             )
                                    self.root.find_add(_parent,
                                                       short_nodename,
                                                       opt=opt
                                                       )
                    else:
                        return

            c_num = dagPath.childCount()
            if c_num > 0:
                for i_num in range(c_num):
                    child_mObj = dagPath.child(i_num)
                    mfn_dag = om.MFnDagNode(child_mObj)
                    child_dag = mfn_dag.getPath()
                    ret = __construct(child_dag, parent=fullpath_name)
                    if not ret:
                        continue
            else:
                return

        self.child_list = utils.get_all_childs(name)
        dagPath = utils.get_dagPathObj(name)
        __construct.__defaults__ = (__construct,)
        __construct(dagPath, parent)

    def set_xml_path(self, xml_path):
        """
        Set XML path.

        Args:
            xml_path (str): xml file path
        """
        self.xml_path = xml_path

    def export_xml(self, root_path, assetName=None):
        """
        Export to XML file as DAG tree hierarchy infomation.

        Args:
            root_path (str): directory root path.
            assetName (str, optional): prefix name of the file name
                of the XML file.The default set value is self.name. Defaults to None.
        """
        if not assetName:
            assetName = self.name
        elem_root = ET.Element(self.TAG_ROOT)
        ele_curr = elem_root
        for root_obj, i_child in self.traverse():
            if root_obj != '':
                ele_curr = self.find_named_element(elem_root,
                                                   root_obj.fullpath,
                                                   root_obj.opt
                                                   )
            for ch in i_child:
                ele_curr.append(self.create_new_nodeTag(ch.fullpath, ch.opt))
        output_filename = '/'.join([root_path, assetName + '_dagInfo.xml'])
        output_file(elem_root, str(output_filename))
        self.set_xml_path(output_filename)

    @classmethod
    def import_xml(cls, xml_file):
        """
        Import XML data from file path.

        Args:
            xml_file (str): dag info xml file path.

        Returns:
            cls: DAGstructure class
        """
        data = ET.parse(xml_file)
        root = data.getroot()
        node = root.find('node')
        name = node.get('name')
        dag_structure = cls(name, xml_path=xml_file)

        def __construct(elem, parent_node, __construct=None):
            node_name = elem.get('fullpath')
            restore_opt = cls.restore_option(elem.findall('option'))
            dag_structure.root.find_add(par=parent_node,
                                        name=node_name,
                                        opt=restore_opt
                                        )
            for child_elem in elem.findall('node'):
                __construct(child_elem, node_name)

        __construct.__defaults__ = (__construct,)
        restore_opt = cls.restore_option(node.findall('option'))
        dag_structure.root = DAGtree(name, opt=restore_opt)

        for child_elem in node.findall('node'):
            __construct(child_elem, dag_structure.name)

        return dag_structure

    def get_obj(self, name):
        """
        Get tree dag object by string name.
        """
        return self.root.find(par=name, name='')

    def restore_parent(self):
        """
        Restore to parent of DAG structure.
        """
        for _, i_child in self.traverse():
            for c in i_child:
                try:
                    cmds.parent(c.name, c.parent.name)
                except:
                    pass

    def restore_attributes(self, root='', attrs=['visibility']):
        if root == '':
            root = self.root
        if not isinstance(attrs, (list, tuple)):
            attrs = [attrs]
        root.restoreAttrs(attrs)
        for root, child_elem in self.traverse():
            for elem in child_elem:
                elem.restoreAttrs(attrs)

    def build(self, root='', maintainUUID=True, restoreAttr=True):
        """
        Build the DAG hierarchy where the data is constructed.

        Args:
            root (Element): root Element node.
            maintainUUID (bool, optional): If you want to reproduce UUID, use True.
        """
        def _create_node(elem, parent_node):
            if type(elem) is list:
                elem = elem[0]
            if elem.name.startswith('|'):
                node_name = elem.name.split('|')[-1]
            else:
                node_name = elem.name

            node_type = elem.opt['nodeType']
            if maintainUUID:
                uuid = elem.opt['uuid']
            else:
                uuid = ''
            return utils.create_node(node_name, node_type, uuid, parent=parent_node)

        if root == '':
            root = self.root
        _create_node(root, parent_node='')
        for root, child_elem in self.traverse():
            for elem in child_elem:
                _create_node(elem, parent_node=root.name)

    def printout(self, depth=0):
        """
        print output root dag DAGtree hierarchy.

        Args:
            depth (int, optional): _description_. Defaults to 0.
        """
        self.root.printout(depth)


def output_file(element, file_name):
    with open(file_name, 'wb') as fp:
        fp.write(minidom.parseString(ET.tostring(element)).toprettyxml(encoding="utf-8"))
        print('# output file : ' + file_name)


if __name__ == "__main__":
    """
    a = dagger.DAGstructure('jointTest')

    a.construct('all')
    a.printout()

    a.export_xml('D:/')
    cmds.delete('all')

    a = a.import_xml('D:/nPlaneTest4_dagInfo.xml')
    a = a.import_xml('D:/jointTest_dagInfo.xml')

    a.build()
    """