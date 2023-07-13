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

import bmesh
from mathutils import Vector
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.transform import move_island_sort, centroid, BoundingBox2d, move_island_to_position
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    set_face_int_tag,
    ensure_facemap,
    collect_selected_objects_data,
    select_by_context
)
from ZenUV.utils import vc_processor as vc
FINISHED_FACEMAP_NAME = "ZenUV_Finished"


def pin_island(island, uv_layer, _pin_action):
    for face in island:
        for loop in face.loops:
            loop[uv_layer].pin_uv = _pin_action


def island_in_range(value, _min, _max):
    if _min <= value <= _max:  # and round(value,4)==value:
        return True
    return False


def select_finished(context, bm, _finished_facemap):
    islands = island_util.get_islands(context, bm)
    islands_for_select = [island for island in islands if True in [f[_finished_facemap] for f in island]]
    if not islands_for_select:
        return {"CANCELLED"}
    select_by_context(context, bm, islands_for_select, state=True)


def deselect_finished(bm, _finished_facemap):
    for face in [face for face in bm.faces if face[_finished_facemap]]:
        face.select = False


def hide_finished(bm, _finished_facemap):
    for face in [face for face in bm.faces if face[_finished_facemap]]:
        face.hide_set(True)


def show_in_view_finished(context, bm, _finished_facemap):
    finished_color = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.FinishedColor
    unfinished_color = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.UnFinishedColor
    finished_faces = [face for face in bm.faces if face[_finished_facemap]]
    unfinished_faces = [face for face in bm.faces if not face[_finished_facemap]]
    # for face in [face for face in bm.faces if face[_finished_facemap]]:
    #     face.select = True
    vc.set_v_color(
        unfinished_faces,
        vc.set_color_layer(bm, vc.Z_FINISHED_V_MAP_NAME),
        unfinished_color, randomize=False
    )
    vc.set_v_color(
        finished_faces,
        vc.set_color_layer(bm, vc.Z_FINISHED_V_MAP_NAME),
        finished_color, randomize=False
    )


def finished_sort_islands(bm, islands, finished_facemap):
    ''' Sorting By Tag Finished '''
    uv_layer = bm.loops.layers.uv.verify()
    for island in islands:
        x_base = BoundingBox2d(islands=[island, ], uv_layer=uv_layer).center.x % 1
        x_offset = x_base + 1 if True in [face[finished_facemap] for face in island] else x_base - 1
        move_island_to_position(island, uv_layer, position=Vector((x_offset, 0)), axis=Vector((1.0, 0.0)))


def get_finished_map_from(_obj):
    """ Return finished VC Layer or None """
    return _obj.data.vertex_colors.get(vc.Z_FINISHED_V_MAP_NAME) or None


def refresh_display_finished(context, bm, obj):
    finished_facemap = ensure_facemap(bm, FINISHED_FACEMAP_NAME)
    finished_vc_layer = get_finished_map_from(obj)
    if finished_vc_layer:
        disable_finished_vc(obj, finished_vc_layer)
        show_in_view_finished(context, bm, finished_facemap)
        finished_vc_layer = get_finished_map_from(obj)
        if finished_vc_layer:
            finished_vc_layer.active = True


def disable_finished_vc(_obj, _finished_vc_layer):
    """ Disable Finished VC and remove VC from object data """
    _finished_vc_layer = get_finished_map_from(_obj)
    if _finished_vc_layer:
        _finished_vc_layer.active = False
        _obj.data.vertex_colors.remove(_finished_vc_layer)


def is_finished_activated(context):
    for obj in context.objects_in_mode:
        finished_vc_map = None
        if obj.type == 'MESH':
            vc_map_in_object = obj.data.vertex_colors.get(vc.Z_FINISHED_V_MAP_NAME)
            if not finished_vc_map and vc_map_in_object:
                finished_vc_map = vc_map_in_object
        return finished_vc_map


def finished_enshure_consistency(context, bm):
    """ Tag whole island as UNFINISHED if at last one face in island marked as UNFINISHED"""
    uv_layer = bm.loops.layers.uv.verify()
    fin_fmap = ensure_facemap(bm, FINISHED_FACEMAP_NAME)
    islands = island_util.get_island(context, bm, uv_layer)
    for island in islands:
        # print([f[fin_fmap] for f in island])
        if False in [f[fin_fmap] for f in island]:
            set_face_int_tag([island], fin_fmap, int_tag=0)


def tag_finished(context, action):
    """
    Tag or untag Finished depend on action='TAG' / 'UNTAG'
    """
    # print("Zen UV: Mark Finished Starting")
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    selection_mode = False

    # Pack Islands before to avoid UV broke.
    # bpy.ops.uv.zenuv_pack()

    bms = collect_selected_objects_data(context)
    # work_mode = check_selection_mode()

    for obj in bms:
        # Detect if exist previously selectet elements at least in one object
        if not selection_mode and bms[obj]['pre_selected_faces'] \
                or bms[obj]['pre_selected_edges']:
            selection_mode = True

    for obj in bms:
        # print("\nStart sorting", obj.name)
        bm = bms[obj]['data']
        me = obj.data
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        finished_vc_layer = get_finished_map_from(obj)
        finished_facemap = ensure_facemap(bm, FINISHED_FACEMAP_NAME)

        islands_for_process = island_util.get_island(context, bm, uv_layer)

        if action == "TAG":
            tag = 1
        elif action == "UNTAG":
            tag = 0

        set_face_int_tag(islands_for_process, finished_facemap, int_tag=tag)
        # Set visible Finished faces if Finished VC Layer is apear in obj data.
        if finished_vc_layer:
            disable_finished_vc(obj, finished_vc_layer)
            show_in_view_finished(context, bm, finished_facemap)
            finished_vc_layer = get_finished_map_from(obj)
            if finished_vc_layer:
                finished_vc_layer.active = True

        if addon_prefs.autoFinishedToPinned:
            for island in islands_for_process:
                pin_island(island, uv_layer, tag)

        if addon_prefs.sortAutoSorting:
            finished_sort_islands(bm, islands_for_process, finished_facemap)
            bmesh.update_edit_mesh(me)
