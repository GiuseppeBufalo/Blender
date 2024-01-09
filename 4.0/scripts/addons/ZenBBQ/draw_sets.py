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

# Copyright 2021, Alex Zhornyak

import bpy
import bmesh

from timeit import default_timer as timer

from .commonFunc import ZBBQ_Consts

from .draw_cache import EdgesCacher

from .vlog import Log

_cache = {}
_draw_handlers = {}


class FakeGroup:
    def __init__(self) -> None:
        self.name = 'FakeGroup'
        self.layer_name = ZBBQ_Consts.customDataLayerRadiusName


class ZBBQ_EdgeLayerManager:
    id_group = 'edge_b'           # edge, vert, face ...
    id_mask = 'ZBVE'            # ZSEG, ZSVG, ZSFG ...
    id_element = 'edge'         # edge, vert, face
    is_unique = False

    @classmethod
    def get_cacher(self):
        return EdgesCacher()

    @classmethod
    def get_bm(self, p_obj):
        bm = bmesh.from_edit_mesh(p_obj.data)
        return bm

    @classmethod
    def get_obj_highlighted_groups(self, p_obj):
        result = []

        bm = self.get_bm(p_obj)
        dataLayer = bm.verts.layers.float.get(ZBBQ_Consts.customDataLayerRadiusName)
        if dataLayer:
            result.append(FakeGroup())

        return result


def is_object_cage_visible(p_obj):
    return all(not it.show_on_cage for it in p_obj.modifiers
               if it.is_active and it.show_viewport and it.show_in_editmode)


def is_draw_active():
    return len(_draw_handlers) > 0


def is_draw_handler_enabled(p_mgr_cls):
    s_idname = p_mgr_cls.id_group
    return s_idname in _draw_handlers


def remove_draw_handler(p_mgr_cls, context):
    s_idname = p_mgr_cls.id_group
    if s_idname in _draw_handlers:
        _do_remove_draw_handler(s_idname, context)


def _do_remove_draw_handler(s_idname, context):
    for h in _draw_handlers[s_idname]:
        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
    del _draw_handlers[s_idname]
    Log.debug('Clear handler:', s_idname)
    if hasattr(context, "area"):
        if context.area is not None:
            context.area.tag_redraw()


def _do_add_draw_handler(p_mgr_cls, context):
    s_idname = p_mgr_cls.id_group

    args = (p_mgr_cls, context)
    _draw_handlers[s_idname] = (bpy.types.SpaceView3D.draw_handler_add(draw_bevel_callback_3d, args, 'WINDOW', 'POST_VIEW'),
                                bpy.types.SpaceView3D.draw_handler_add(draw_bevel_callback_2d, args, 'WINDOW', 'POST_PIXEL'))
    Log.debug('Add draw_handler:', s_idname)

    # optional: switch others
    for key in list(_draw_handlers):
        if not key == s_idname:
            _do_remove_draw_handler(key, context)


def remove_all_handlers3d():
    for handles in _draw_handlers.values():
        for h in handles:
            bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
    _draw_handlers.clear()


def reset_all_draw_cache():
    global _cache
    _cache = {}


def get_mgr_cache(p_mgr_cls):
    global _cache
    if p_mgr_cls.id_group not in _cache:
        _cache[p_mgr_cls.id_group] = {}

    return _cache[p_mgr_cls.id_group]


def get_obj_cache(p_mgr_cls, p_obj):
    global _cache
    p_mgr_cache = get_mgr_cache(p_mgr_cls)
    if p_obj not in p_mgr_cache:
        p_mgr_cache[p_obj] = p_mgr_cls.get_cacher()

    return p_mgr_cache[p_obj]


def reset_obj_cache(p_mgr_cls, p_obj):
    global _cache
    p_mgr_cache = get_mgr_cache(p_mgr_cls)
    p_mgr_cache[p_obj] = p_mgr_cls.get_cacher()


def check_update_cache(p_mgr_cls, p_obj):
    p_display_groups = p_mgr_cls.get_obj_highlighted_groups(p_obj)
    if len(p_display_groups):
        p_obj_cache = get_obj_cache(p_mgr_cls, p_obj)
        p_obj_cache.check_draw_cache_prepared(p_mgr_cls, p_obj, p_display_groups, b_calc_vol=True)


def check_update_cache_on_change(p_mgr_cls, p_obj, p_obj_eval):
    p_display_groups = p_mgr_cls.get_obj_highlighted_groups(p_obj)
    if len(p_display_groups):
        p_obj_cache = get_obj_cache(p_mgr_cls, p_obj)
        p_obj_cache.check_draw_cache_prepared(p_mgr_cls, p_obj, p_display_groups, b_calc_vol=True)


def update_cache_group(p_mgr_cls, p_obj, p_group):
    p_obj_cache = get_obj_cache(p_mgr_cls, p_obj)

    try:
        p_display_groups = p_mgr_cls.get_obj_highlighted_groups(p_obj)
        p_obj_cache.check_draw_cache_prepared(p_mgr_cls, p_obj, p_display_groups)
        p_obj_cache.build_group_cache(p_mgr_cls, p_obj, p_group, p_display_groups)
    except ReferenceError as e:
        Log.error('update_cache_group', e)


def mark_groups_modified(p_mgr_cls, p_obj):
    p_obj_cache = get_obj_cache(p_mgr_cls, p_obj)
    p_obj_cache.force_rebuild_cache = True


def draw_bevel_callback_2d(p_mgr_cls, context):
    pass


def draw_bevel_callback_3d(p_mgr_cls, context):
    if context.mode in {'EDIT_MESH'}:
        start = timer()

        for p_obj in context.objects_in_mode:
            p_display_groups = p_mgr_cls.get_obj_highlighted_groups(p_obj)
            if len(p_display_groups):
                b_draw_cage = is_object_cage_visible(p_obj)
                if b_draw_cage:
                    p_obj_cache = get_obj_cache(p_mgr_cls, p_obj)
                    p_obj_cache.z_order = 1
                    p_obj_cache.draw(p_mgr_cls, p_obj, p_display_groups)

        timespan = timer() - start
        if timespan > 0.2:
            Log.debug('Draw BGL 3D:', p_obj.name, timespan)


if __name__ == "__main__":
    pass
