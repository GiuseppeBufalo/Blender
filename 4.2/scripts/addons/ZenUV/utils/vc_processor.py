# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

""" Zen UV Vertex Color Processor """
import random
import bpy
import bmesh
from mathutils import Color


Z_PINNED_V_MAP_NAME = "zen_uv_pinned"
Z_FINISHED_V_MAP_NAME = "zen_uv_finished"
Z_TD_BALANCED_V_MAP_NAME = "zen_uv_TD_balanced"
Z_TD_PRESETS_V_MAP_NAME = "zen_uv_TD_presets"


def get_zen_vc_map_from(_obj, vc_map_name):
    """ Return VC Layer by vc_map_name or None """
    return _obj.data.vertex_colors.get(vc_map_name) or None


def disable_zen_vc_map(_obj, _vc_map_name):
    """ Disable Finished VC and remove VC from object data """
    _vc_layer = get_zen_vc_map_from(_obj, _vc_map_name)
    if _vc_layer:
        _vc_layer.active = False
        _obj.data.vertex_colors.remove(_vc_layer)


def enshure_face_color_map(bm, facemap_name):
    facemap = bm.faces.layers.string.get(facemap_name)
    if not facemap:
        facemap = bm.faces.layers.string.new(facemap_name)
    return facemap


def set_color_tag(islands_for_process, color_facemap, _color):
    _color = (str(_color[0]) + '#' + str(_color[1]) + '#' + str(_color[2])).encode()
    for island in islands_for_process:
        for face in island:
            face[color_facemap] = _color


def set_color_layer(bm, map_name):
    if not bm.loops.layers.color.get(map_name):
        color_layer = bm.loops.layers.color.new(map_name)
    else:
        color_layer = bm.loops.layers.color.get(map_name)
    return color_layer


def set_v_color(faces, color_layer, color, randomize):
    color = color[0], color[1], color[2], 1
    if randomize:
        color = hue_shift(color)

    for face in faces:
        for loop in face.loops:
            loop[color_layer] = color
    return color


def hue_shift(color):
    color_h = Color()
    color_h.r = color[0]
    color_h.g = color[1]
    color_h.b = color[2]
    color_h.h = random.random()
    return [color_h.r, color_h.g, color_h.b, 1]


def update_vcolor(obj):
    # bm = bmesh.from_edit_mesh(me)
    # if bm.is_wrapped:
    # obj.update_from_editmode()
    bmesh.update_edit_mesh(obj.data, loop_triangles=False)
    # bpy.ops.object.mode_set(mode='VERTEX_PAINT')
    # bpy.ops.object.mode_set(mode="EDIT")
    # else:
    #     bm.to_mesh(me)
    #     me.update()


def get_random_color():
    """generate rgb using a list comprehension"""
    r, g, b = [random.random() for i in range(3)]
    return r, g, b, 1


if __name__ == '__main__':
    pass
