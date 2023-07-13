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

""" Zen Unwrap Operator """
import bpy
import bmesh
from ZenUV.utils.generic import (
    get_mesh_data,
    enshure_facemap,
    collect_selected_objects_data,
    check_selection_mode,
    restore_selection,
    uv_by_xy,
    select_all,
    fit_uv_view,
    Diff,
    set_face_int_tag,
    switch_shading_style
)
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.ops.mark import zuv_mark_seams
from ZenUV.utils.finishing_util import (
    FINISHED_FACEMAP_NAME,
    sort_islands,
    get_finished_map_from,
    disable_finished_vc,
    deselect_finished,
    refresh_display_finished
)
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.hops_integration import show_uv_in_3dview


def check_seams(bm, _seams_exist):
    if not _seams_exist and True in [edge.seam for edge in bm.edges]:
        return True
    else:
        return False


class ZUV_OT_ZenUnwrap(bpy.types.Operator):
    """ Zen Unwrap Operator """
    bl_idname = "uv.zenuv_unwrap"
    bl_label = ZuvLabels.ZEN_UNWRAP_LABEL
    bl_description = ZuvLabels.ZEN_UNWRAP_DESC
    bl_options = {'REGISTER', 'UNDO'}

    action: bpy.props.EnumProperty(
        items=[
            ("NONE", "Zen Unwrap", "Default Zen Unwrap Mode."),
            ("AUTO", "Auto Seams Mode", "Perform Auto Seams Before Zen Unwrap.")],
        default="NONE",
        options={'HIDDEN'}
    )
    mark_switch: bpy.props.BoolProperty(
        name="Mark Switch",
        default=True,
        options={'HIDDEN'}
    )
    mark_selected: bpy.props.BoolProperty(
        name="Mark Selected",
        options={'HIDDEN'},
        default=True
    )
    no_selected_in_selection_mode = False

    def invoke(self, context, event):
        decision = []
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        self.mark_switch = addon_prefs.zen_unwrap_switch
        if self.mark_selected:
            self.mark_selected = addon_prefs.autoSeamsWithUnwrap
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            if True in [x.select for x in bm.edges] or \
                    True in [x.select for x in bm.faces] or \
                    True in [x.select for x in bm.verts]:
                decision.append(True)
            enshure_facemap(bm, facemap_name=FINISHED_FACEMAP_NAME)
        if True in decision:
            return self.execute(context)
        elif addon_prefs.workOnSelected:
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

    # def draw(self, context):
    #     layout = self.layout
    #     # Message: "Nothing is selected. The entire object will be unwrapped."
    #     layout.label(text=ZuvLabels.ZEN_UNWRAP_NO_SELECT_WARN)
    #     self.no_selected_in_selection_mode = True
    #     layout.separator()

    def execute(self, context):
        # print("Zen UV: Unwrap Starting")
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        if addon_prefs.autoActivateUVSync:
            # print("autoActivateUVSync -  Is on")
            context.scene.tool_settings.use_uv_select_sync = True
        selection_mode = False
        seams_exist = False
        # bms = {}
        work_mode = None
        stop_process = False  # Control state after Bring POPUP.
        silent = False

        """ Full Automatic Unwrap Mode. First Perform Auto Seams """
        if self.action == "AUTO":
            # print("mode: ", self.action)
            bpy.ops.uv.zenuv_auto_mark("INVOKE_DEFAULT")
            # self.action = "NONE"

        bms = collect_selected_objects_data(context)
        for obj in bms:
            """ Detect if exist previously selectet elements at least in one object """
            if not selection_mode and \
                    bms[obj]['pre_selected_faces'] or \
                    bms[obj]['pre_selected_edges'] or \
                    bms[obj]['pre_selected_verts']:
                selection_mode = True

            """ Detect if exist seams at least in one object """
            if not seams_exist and True in [edge.seam for edge in bms[obj]['data'].edges]:
                seams_exist = True

        for obj in bms:
            bm = bms[obj]['data']
            pre_selected_faces = bms[obj]['pre_selected_faces']
            pre_selected_edges = bms[obj]['pre_selected_edges']
            # If mesh have no UV layers - clear finished tag and v color finished
            if not bm.loops.layers.uv.items():
                finished_facemap = enshure_facemap(bm, FINISHED_FACEMAP_NAME)
                set_face_int_tag(
                    [bm.faces],
                    finished_facemap,
                    int_tag=0)
                finished_vc_layer = get_finished_map_from(obj)
                if finished_vc_layer:
                    disable_finished_vc(obj, finished_vc_layer)
                    switch_shading_style(context, "MATERIAL", switch=False)

            uv_layer = bm.loops.layers.uv.verify()
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

            """ Check selection mode work with """
            work_mode = check_selection_mode(context)
            reserved_work_mode = context.tool_settings.mesh_select_mode
            # print("Restore 1")
            restore_selection(work_mode, pre_selected_faces, pre_selected_edges)
            pre_selected_faces = [f for f in bm.faces if f.select]
            if selection_mode:
                if not seams_exist:
                    uv_by_xy(bm, obj.data)
                if self.action == "NONE" and self.mark_selected:
                    zuv_mark_seams(context, bm, silent_mode=silent, switch=self.mark_switch)
                    silent = True
            else:  # if nothing selected and mesh have no assigned seams
                if True not in [x.seam for x in bm.edges] and not seams_exist:
                    stop_process = True
                    bpy.ops.wm.call_menu(name="ZUV_MT_ZenUnwrap_Popup")
                    break
                else:
                    select_all(bm, action=True)
                    fit_uv_view(context, mode='all')

            # Unwrap Phase
            if not stop_process:
                if not addon_prefs.workOnSelected:  # If work with whole mesh
                    select_all(bm, action=True)  # Select All
                else:  # If work with only selection
                    # selected_islands = island_util.get_island(context, bm, uv_layer)
                    selected_islands = [[f for f in bm.faces if f.select], ]
                    select_all(bm, action=False)
                    for island in selected_islands:
                        for face in island:
                            face.select = True
                for temp_obj in bms:
                    temp_bm = bms[temp_obj]['data']
                    finished_facemap = enshure_facemap(temp_bm, FINISHED_FACEMAP_NAME)
                    deselect_finished(temp_bm, finished_facemap)
                    bmesh.update_edit_mesh(temp_obj.data, loop_triangles=False)

                bmesh.update_edit_mesh(obj.data, loop_triangles=False)
                bpy.ops.uv.unwrap(method=addon_prefs.UnwrapMethod, margin=addon_prefs.margin)

                # Tag Unwrapped selected faces as Finished
                # if work in Unwrap Selected Only mode and Auto Tag Finished
                if selection_mode and addon_prefs.workOnSelected and addon_prefs.autoTagFinished:
                    finished_facemap = enshure_facemap(bm, FINISHED_FACEMAP_NAME)
                    set_face_int_tag(
                        [[f for f in bm.faces if f.select]],
                        finished_facemap,
                        int_tag=1)
                refresh_display_finished(context, bm, obj)

                select_all(bm, action=False)

            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        # Pack Phase (addon_prefs, "packAfUnwrap")
        if addon_prefs.packAfUnwrap \
            and self.no_selected_in_selection_mode \
                or not stop_process \
                and not addon_prefs.workOnSelected:
            kp_st = addon_prefs.lock_overlapping_mode
            addon_prefs.lock_overlapping_mode = '0'
            bpy.ops.uv.zenuv_pack(display_uv=False)
            addon_prefs.lock_overlapping_mode = kp_st

        # Sortig Phase
        for obj in bms:
            bm = bms[obj]['data']
            if addon_prefs.unwrapAutoSorting and addon_prefs.packEngine == "BLDR":
                all_islands = island_util.get_islands(bm)
                if selection_mode:
                    current_islands = island_util.get_island(context, bm, uv_layer)
                    sort_islands(obj.data, bm, Diff(all_islands, current_islands))
                else:
                    sort_islands(obj.data, bm, all_islands)

            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        # Restore Initial Selection if works in Selection Mode
        if selection_mode:
            for obj in bms:
                restore_selection(work_mode, bms[obj]['pre_selected_faces'], bms[obj]['pre_selected_edges'])
            if len(bms) == 1:
                fit_uv_view(context, mode="selected")
            else:
                fit_uv_view(context, mode="all")

        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            if addon_prefs.unwrapAutoSorting:
                fit_uv_view(context, mode="checker")
            else:
                fit_uv_view(context, mode="all")
        # Restore blender selection mode
        context.tool_settings.mesh_select_mode = reserved_work_mode
        self.action = "NONE"
        # Display UV Widget from HOPS addon
        if addon_prefs.workOnSelected:
            show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=True)
        else:
            show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=False)
        # Reset self values to default
        self.mark_switch = True
        self.mark_selected = True
        return {'FINISHED'}


if __name__ == '__main__':
    pass
