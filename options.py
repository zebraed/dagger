#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

from . import utils


class TagOption(object):
    TAG_ROOT  = 'dagStructure'
    TAG_NODE  = 'node'
    TAG_OPT   = 'option'


class Option(object):
    pass


class AttribOption(dict):
    pass

attrib_opt = {
'translate': utils.get_translate,
'rotate': utils.get_rotate,
'scale': utils.get_scale,
'pivot': utils.get_pivot,
'visibility': utils.get_visibility,
'shapes': utils.get_shapes,
'nodeType': utils.get_nodeType,
#'isInstance': utils.is_instance,
'uuid': utils.get_uuid,
}
