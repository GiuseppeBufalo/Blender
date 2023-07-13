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

""" Zen UV Finishing System """
import bpy
import bmesh

from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    ensure_facemap,
    fit_uv_view,
    get_mesh_data,
    select_by_context,
    resort_by_type_mesh_in_edit_mode_and_sel
)
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.finishing_util import (
    FINISHED_FACEMAP_NAME,
    finished_sort_islands,
    tag_finished,
    select_finished,
)
from ZenUV.ui.pie import ZsPieFactory


class ZUV_OT_Sorting_Islands(bpy.types.Operator):
    bl_idname = "uv.zenuv_islands_sorting"
    bl_label = ZuvLabels.SORTING_LABEL
    bl_description = ZuvLabels.SORTING_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        for obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            bm = bmesh.from_edit_mesh(obj.data)
            finished_facemap = ensure_facemap(bm, FINISHED_FACEMAP_NAME)
            islands_for_process = island_util.get_islands(context, bm)
            finished_sort_islands(bm, islands_for_process, finished_facemap)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)
        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_Tag_Finished(bpy.types.Operator):
    """
    Operator to Tag Finished Islands
    """
    bl_idname = "uv.zenuv_tag_finished"
    bl_label = ZuvLabels.OT_TAG_FINISHED_LABEL
    bl_description = ZuvLabels.OT_TAG_FINISHED_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        tag_finished(context, action="TAG")
        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_UnTag_Finished(bpy.types.Operator):
    """
    Operator to Untag Finished Islands
    """
    bl_idname = "uv.zenuv_untag_finished"
    bl_label = ZuvLabels.OT_UNTAG_FINISHED_LABEL
    bl_description = ZuvLabels.OT_UNTAG_FINISHED_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        tag_finished(context, action="UNTAG")
        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_Display_Finished(bpy.types.Operator):
    bl_idname = "uv.zenuv_display_finished"
    bl_label = ZuvLabels.OT_FINISHED_DISPLAY_LABEL
    bl_description = ZuvLabels.OT_FINISHED_DISPLAY_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        context.scene.zen_display.finished = not context.scene.zen_display.finished
        return {"FINISHED"}


class ZUV_OT_Select_Finished(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_finished"
    bl_label = ZuvLabels.OT_FINISHED_SELECT_LABEL
    bl_description = ZuvLabels.OT_FINISHED_SELECT_DESC
    bl_options = {'REGISTER', 'UNDO'}

    clear_sel: bpy.props.BoolProperty(
        name="Clear",
        description="Clear previous selection",
        default=True
    )

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)
            bm.faces.ensure_lookup_table()
            finished_facemap = ensure_facemap(bm, FINISHED_FACEMAP_NAME)
            if self.clear_sel:
                select_by_context(context, bm, [bm.faces], state=False)
            select_finished(context, bm, finished_facemap)
            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {"FINISHED"}


if __name__ == '__main__':
    pass
