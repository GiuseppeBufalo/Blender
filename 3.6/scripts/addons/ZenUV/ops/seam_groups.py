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

""" Zen Seam Groups System """
import bpy
import bmesh
from bpy.types import (
    UIList,
    Operator,
    Panel
)
from bpy.props import StringProperty
from ZenUV.utils.generic import (
    ZUV_PANEL_CATEGORY,
    ZUV_REGION_TYPE,
    ZUV_CONTEXT,
    ZUV_SPACE_TYPE,
    resort_by_type_mesh
)
from ZenUV.ui.labels import ZuvLabels


def enshure_seam_layer(bm, seam_layer_name):
    """ Return layer int type or create new """
    layer = bm.edges.layers.int.get(seam_layer_name)
    if not layer:
        layer = bm.edges.layers.int.new(seam_layer_name)
    return layer


def set_seams_to_group(bm, _layer):
    for edge in bm.edges:
        edge[_layer] = edge.seam


def get_seams_from_group(bm, _layer):
    for edge in bm.edges:
        edge.seam = edge[_layer]


def matching_groups(name, objs):
    # print(f"Input data: {name}")
    for obj in objs:
        f_name, out_index = find_indexes_in_obj(name, obj)
        # print(f"output: f_name: {f_name}, out_index: {out_index}")
        if not f_name:
            out_index = len(obj.zen_sg_list) + 1
        obj.zsg_list_index = out_index


def find_indexes_in_obj(name, obj):
    """ Try to find given sim_index in manual stacks of given object """
    f_name = None
    out_index = None
    list_index = 0
    for item in obj.zen_sg_list:
        if not f_name and item.layer_name == name:
            f_name = name
            out_index = list_index
        list_index += 1
    return f_name, out_index


class ZSGListGroup(bpy.types.PropertyGroup):
    """
    Group of properties representing
    an item in the zen seam groups.
    """

    name: StringProperty(
        name="Name",
        description="A name for this item",
        default="Seams"
    )

    layer_name: StringProperty(
        name="",
        description="",
        default=""
    )


class ZSG_UL_List(UIList):
    """ Zen Seam Groups UIList """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        custom_icon = 'OBJECT_DATAMODE'

        # Make sure code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon=custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(text="", emboss=False, icon=custom_icon)


class ZUV_PT_ZenSeamsGroups(Panel):
    """  Zen Seam Groups Panel """
    bl_label = ZuvLabels.PT_SEAMS_GROUP_LABEL
    bl_context = ZUV_CONTEXT
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        return addon_prefs.enable_pt_seam_group

    def draw(self, context):
        layout = self.layout
        ob = context.object

        row = layout.row()
        col = row.column()
        col.template_list(
            "ZSG_UL_List",
            "name",
            ob,
            "zen_sg_list",
            ob,
            "zsg_list_index",
            rows=2
        )

        col = row.column(align=True)
        col.operator(ZSG_OT_NewItem.bl_idname, text="", icon='ADD')
        col.operator(ZSG_OT_DeleteItem.bl_idname, text="", icon='REMOVE')
        col.separator()

        # col.operator(ZSG_OT_MoveItem.bl_idname, text="", icon='TRIA_UP').direction = 'UP'
        # col.operator(ZSG_OT_MoveItem.bl_idname, text="", icon='TRIA_DOWN').direction = 'DOWN'

        row = layout.row()

        row.operator(ZSG_OT_AssignToGroup.bl_idname)
        row.operator(ZSG_OT_ActivateGroup.bl_idname)


class ZSG_OT_NewItem(Operator):
    """Add a new item to the list."""
    bl_description = ZuvLabels.OT_SGL_NEW_ITEM_DESC
    bl_idname = "zen_sg_list.new_item"
    bl_label = ZuvLabels.OT_SGL_NEW_ITEM_LABEL
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # ob = context.object
        objs = resort_by_type_mesh(context)
        if not objs:
            return {'CANCELLED'}
        for obj in objs:
            obj.zen_sg_list.add()
            name = "Seams"
            _layer_name = "zen_seam_grp"
            i = 1
            while _layer_name in [obj.zen_sg_list[i].layer_name for i in range(len(obj.zen_sg_list))]:
                name = "Seams_{0}".format(str(i))
                _layer_name = "zen_seam_grp_{0}".format(str(i))
                i = i + 1

            obj.zen_sg_list[-1].name = name
            obj.zen_sg_list[-1].layer_name = _layer_name
            obj.zsg_list_index = len(obj.zen_sg_list) - 1

            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            s_layer = bm.edges.layers.int.new(_layer_name)
            set_seams_to_group(bm, s_layer)
            bmesh.update_edit_mesh(me, loop_triangles=False)
        return{'FINISHED'}


class ZSG_OT_DeleteItem(Operator):
    """Delete the selected item from the list."""
    bl_description = ZuvLabels.OT_SGL_DEL_ITEM_DESC
    bl_idname = "zen_sg_list.delete_item"
    bl_label = ZuvLabels.OT_SGL_DEL_ITEM_LABEL
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object.zen_sg_list

    def execute(self, context):
        objs = resort_by_type_mesh(context)
        if not objs:
            return {'CANCELLED'}
        ob = context.active_object
        list_index = ob.zsg_list_index
        init_layer_name = ob.zen_sg_list[list_index].layer_name
        if list_index in range(len(ob.zen_sg_list)):
            matching_groups(ob.zen_sg_list[list_index].layer_name, objs)
        for obj in objs:
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            layer = bm.edges.layers.int.get(init_layer_name)
            if layer:
                bm.edges.layers.int.remove(layer)

            zen_sg_list = obj.zen_sg_list
            index = obj.zsg_list_index
            if index in range(len(ob.zen_sg_list)):
                zen_sg_list.remove(index)
                obj.zsg_list_index = min(max(0, index - 1), len(zen_sg_list) - 1)

        return{'FINISHED'}


class ZSG_OT_MoveItem(Operator):
    """Move an item in the list."""
    bl_description = ZuvLabels.OT_SGL_MOVE_ITEM_DESC
    bl_idname = "zen_sg_list.move_item"
    bl_label = ZuvLabels.OT_SGL_MOVE_ITEM_LABEL
    bl_options = {'INTERNAL'}
    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ""),
            ('DOWN', 'Down', ""),
        )
    )

    @classmethod
    def poll(cls, context):
        return context.object.zen_sg_list

    def move_index(self, context):
        """ Move index of an item render queue while clamping it. """
        index = context.object.zsg_list_index
        list_length = len(context.object.zen_sg_list) - 1
        # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        context.object.zsg_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        zen_sg_list = context.object.zen_sg_list
        index = context.object.zsg_list_index
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        zen_sg_list.move(neighbor, index)
        self.move_index()
        return{'FINISHED'}


class ZSG_OT_AssignToGroup(bpy.types.Operator):
    """ Assign current seams to selected seam group """
    bl_description = ZuvLabels.OT_SGL_ASSIGN_ITEM_DESC
    bl_idname = "uv.zenuv_assign_seam_to_group"
    bl_label = ZuvLabels.OT_SGL_ASSIGN_ITEM_LABEL
    bl_options = {'INTERNAL'}

    def execute(self, context):
        objs = resort_by_type_mesh(context)
        if not objs:
            return {'CANCELLED'}
        ob = context.active_object
        if not len(ob.zen_sg_list):
            bpy.ops.zen_sg_list.new_item()
        list_index = ob.zsg_list_index
        init_name = ob.zen_sg_list[list_index].name
        init_layer_name = ob.zen_sg_list[list_index].layer_name
        if list_index in range(len(ob.zen_sg_list)):
            matching_groups(ob.zen_sg_list[list_index].layer_name, objs)
        for obj in objs:
            if list_index in range(len(obj.zen_sg_list)):
                layer_name = obj.zen_sg_list[list_index].layer_name
                self.assign_to_group(layer_name, obj)
            else:
                obj.zen_sg_list.add()
                obj.zen_sg_list[-1].name = init_name
                obj.zen_sg_list[-1].layer_name = init_layer_name
                obj.zsg_list_index = len(ob.zen_sg_list) - 1
                self.assign_to_group(init_layer_name, obj)
        return {'FINISHED'}

    def assign_to_group(self, layer_name, obj):
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        s_layer = enshure_seam_layer(bm, seam_layer_name=layer_name)
        set_seams_to_group(bm, s_layer)
        bmesh.update_edit_mesh(me, loop_triangles=False)


class ZSG_OT_ActivateGroup(bpy.types.Operator):
    """ Set Seams from active group to current object seams. """
    bl_description = ZuvLabels.OT_SGL_ACTIVATE_ITEM_DESC
    bl_idname = "uv.zenuv_activate_seam_group"
    bl_label = ZuvLabels.OT_SGL_ACTIVATE_ITEM_LABEL
    bl_options = {'INTERNAL'}

    def execute(self, context):
        objs = resort_by_type_mesh(context)
        if not objs:
            return {'CANCELLED'}
        ob = context.active_object
        list_index = ob.zsg_list_index
        if list_index in range(len(ob.zen_sg_list)):
            matching_groups(ob.zen_sg_list[list_index].layer_name, objs)
        for obj in objs:
            if obj.zsg_list_index in range(len(obj.zen_sg_list)):
                SEAMS_LAYER_NAME = obj.zen_sg_list[obj.zsg_list_index].layer_name
                me = obj.data
                bm = bmesh.from_edit_mesh(me)
                s_layer = enshure_seam_layer(bm, seam_layer_name=SEAMS_LAYER_NAME)
                get_seams_from_group(bm, s_layer)
                bmesh.update_edit_mesh(me, loop_triangles=False)
        return {'FINISHED'}


if __name__ == "__main__":
    pass
