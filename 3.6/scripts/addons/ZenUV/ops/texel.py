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

""" Zen UV Texel Density system """

import bpy
import bmesh
from mathutils import Color
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.generic import (
    resort_objects,
    get_mesh_data,
    switch_shading_style,
    resort_by_type_mesh_in_edit_mode_and_sel,
    lerp_two_colors,
    remap_ranges,
    filter_instances
)
from ZenUV.utils.texel_density import (
    get_texel_density,
    set_texel_density,
    is_td_display_activated,
    calculate_uv_coverage,
    get_texel_density_in_obj_mode,
    UNITS_CONV,
    TdContext,
    get_td_color_map_from,
    get_td_data

)
from ZenUV.utils import vc_processor as vc
from bpy.props import FloatProperty, EnumProperty, IntProperty
from ZenUV.prop.zuv_preferences import get_prefs


MODE_CONV = {"island": 1, "overall": 0, "asone": 2}


def update_view3d_in_all_screens(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


class ZUV_OT_GetTexelDensity(bpy.types.Operator):
    bl_idname = "uv.zenuv_get_texel_density"
    bl_label = ZuvLabels.OT_GET_TEXEL_DENSITY_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_GET_TEXEL_DENSITY_DESC
    bl_options = {'INTERNAL', 'UNDO_GROUPED'}

    td_inputs = None

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    # def invoke(self, context, event):
    #     td_inputs = TdContext(context)
    #     return self.execute(context)

    def execute(self, context):
        td_inputs = TdContext(context)
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        objs = resort_objects(context, objs)
        if objs:
            addon_prefs.TexelDensity, tmp = get_texel_density(context, objs, td_inputs)
        return {'FINISHED'}


class ZUV_OT_GetTexelDensityOBJ(bpy.types.Operator):
    bl_idname = "uv.zenuv_get_texel_density_obj"
    bl_label = ZuvLabels.OT_GET_TEXEL_DENSITY_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_GET_TEXEL_DENSITY_DESC
    bl_options = {'INTERNAL', 'UNDO_GROUPED'}

    td_inputs = None

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def invoke(self, context, event):
        self.td_inputs = TdContext(context)
        return self.execute(context)

    def execute(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        addon_prefs.TexelDensity, tmp = get_texel_density_in_obj_mode(context, objs, self.td_inputs)
        return {'FINISHED'}


class ZUV_OT_GetUVCoverage(bpy.types.Operator):
    bl_idname = "uv.zenuv_get_uv_coverage"
    bl_label = ZuvLabels.OT_GET_UV_COVERAGE_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_GET_UV_COVERAGE_DESC
    bl_options = {'INTERNAL', 'UNDO_GROUPED'}

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH'

    def execute(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        coverage = 0
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        for obj in objs:
            if obj.mode == "EDIT":
                me, bm = get_mesh_data(obj)
                uv_layer = bm.loops.layers.uv.verify()
                coverage += calculate_uv_coverage(uv_layer, bm.faces)
                bmesh.update_edit_mesh(me, loop_triangles=False)
            else:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                uv_layer = bm.loops.layers.uv.verify()
                coverage += calculate_uv_coverage(uv_layer, bm.faces)
                # bm.to_mesh(obj.data)
                bm.free()
        addon_prefs.UVCoverage = coverage
        return {'FINISHED'}


class ZUV_OT_SetTexelDensity(bpy.types.Operator):
    bl_idname = "uv.zenuv_set_texel_density"
    bl_label = ZuvLabels.OT_SET_TEXEL_DENSITY_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_SET_TEXEL_DENSITY_DESC

    td_inputs = None

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    # def invoke(self, context, event):
    #     self.td_inputs = TdContext(context)
    #     return self.execute(context)

    def execute(self, context):
        self.td_inputs = TdContext(context)
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        objs = resort_objects(context, objs)
        set_texel_density(context, objs, self.td_inputs)
        # if is_td_display_activated(context):
        #     for obj in objs:
        #         me, bm = get_mesh_data(obj)
        #         calculate_td_vcolor_balanced(context, obj, bm, self.td_inputs)
        #         bmesh.update_edit_mesh(me, loop_triangles=False)
        return {'FINISHED'}


class ZUV_OT_SetTexelDensityOBJ(bpy.types.Operator):
    """
    Set Texel Density to selected Objects.
    units:  'km', 'm', 'cm', 'mm', 'um'
            'mil', 'ft', 'in', 'th'
    mode:   'island, 'overall', 'asone'
    """
    bl_idname = "uv.zenuv_set_texel_density_obj"
    bl_label = ZuvLabels.OT_SET_TEXEL_DENSITY_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_SET_TEXEL_DENSITY_OBJ_DESC

    td: FloatProperty(
        name=ZuvLabels.PREF_TEXEL_DENSITY_LABEL,
        description=ZuvLabels.PREF_TEXEL_DENSITY_DESC,
        min=0.001,
        default=1024.0,
        precision=2,
        # options={'HIDDEN'}
    )

    u: IntProperty(
        name="Texture Size X",
        min=1,
        default=1024,
        # options={'HIDDEN'}
    )
    v: IntProperty(
        name="Texture Size Y",
        min=1,
        default=1024,
        # options={'HIDDEN'}
    )

    units: EnumProperty(
        name=ZuvLabels.PREF_UNITS_LABEL,
        description=ZuvLabels.PREF_UNITS_DESC,
        items=[
            ('km', 'km', 'KILOMETERS'),
            ('m', 'm', 'METERS'),
            ('cm', 'cm', 'CENTIMETERS'),
            ('mm', 'mm', 'MILLIMETERS'),
            ('um', 'um', 'MICROMETERS'),
            ('mil', 'mil', 'MILES'),
            ('ft', 'ft', 'FEET'),
            ('in', 'in', 'INCHES'),
            ('th', 'th', 'THOU')
        ],
        default="m",
        # options={'HIDDEN'}
    )

    mode: EnumProperty(
        name=ZuvLabels.PREF_TD_SET_MODE_LABEL,
        description=ZuvLabels.PREF_TD_SET_MODE_DESC,
        items=[
            (
                'island',
                ZuvLabels.PREF_SET_PER_ISLAND_LABEL,
                ZuvLabels.PREF_SET_PER_ISLAND_DESC
            ),
            (
                'overall',
                ZuvLabels.PREF_SET_OVERALL_LABEL,
                ZuvLabels.PREF_SET_OVERALL_DESC
            ),
        ],
        default="overall",
        # options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        objs = filter_instances(context.selected_objects)
        td_inputs = TdContext(context)
        td_inputs.td = self.td
        td_inputs.image_size = (self.u, self.v)
        td_inputs.units = UNITS_CONV[self.units]
        td_inputs.set_mode = self.mode
        td_inputs.obj_mode = True

        set_texel_density(context, objs, td_inputs)
        update_view3d_in_all_screens(context)
        return {'FINISHED'}


class ZUV_OT_TDGetTextureSize(bpy.types.Operator):
    bl_idname = "uv.zenuv_get_image_size_uv_layout"
    bl_label = ZuvLabels.OT_GET_IMAGE_SIZE_ACTIVE_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_GET_IMAGE_SIZE_ACTIVE_DESC

    def execute(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        screen = context.screen
        for area in screen.areas:
            if area.type == 'IMAGE_EDITOR':
                if area.spaces.active.image:
                    addon_prefs.TD_TextureSizeX = area.spaces.active.image.size[0]
                    return {'FINISHED'}
        self.report({'WARNING'}, "There is no Active Image in the UV Editor.")
        return {'CANCELLED'}


class ZUV_OT_Hide_TD(bpy.types.Operator):
    bl_idname = "uv.zenuv_hide_texel_density"
    bl_label = ZuvLabels.OT_HIDE_TD_LABEL
    bl_description = ZuvLabels.OT_HIDE_TD_DESC
    bl_options = {'REGISTER', 'UNDO'}

    map_type: EnumProperty(
        name="Map Type",
        items=[
            ("BALANCED", "Balanced", ""),
            ("PRESETS", "Presets", ""),
            ("ALL", "All", ""),
        ],
        default="BALANCED",
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        return context.selected_objects or context.objects_in_mode

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if self.map_type == "BALANCED":
            for obj in objs:
                vc.disable_zen_vc_map(obj, vc.Z_TD_BALANCED_V_MAP_NAME)
        if self.map_type == "PRESETS":
            for obj in objs:
                vc.disable_zen_vc_map(obj, vc.Z_TD_PRESETS_V_MAP_NAME)
        if self.map_type == "ALL":
            for obj in objs:
                vc.disable_zen_vc_map(obj, vc.Z_TD_PRESETS_V_MAP_NAME)
                vc.disable_zen_vc_map(obj, vc.Z_TD_BALANCED_V_MAP_NAME)
        switch_shading_style(context, "TEXTURE", switch=False)
        return {"FINISHED"}


class ZUV_OT_CurTDtoCheckTD(bpy.types.Operator):
    bl_idname = "zenuv.set_current_td_to_checker_td"
    bl_label = ZuvLabels.OT_SET_CUR_TO_CH_TD_LABEL
    bl_description = ZuvLabels.OT_SET_CUR_TO_CH_TD_DESC
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    #     return context.selected_objects

    def execute(self, context):
        addon_prefs = get_prefs()
        addon_prefs.td_checker = addon_prefs.TexelDensity
        if is_td_display_activated(context):
            bpy.ops.uv.zenuv_display_td_balanced("INVOKE_DEFAULT")
        return {"FINISHED"}


class ZUV_OT_Display_TD_Balanced(bpy.types.Operator):
    """ Display Texel Density Presets """
    bl_idname = "uv.zenuv_display_td_balanced"
    bl_label = ZuvLabels.OT_DISPLAY_TD_LABEL
    bl_description = ZuvLabels.OT_DISPLAY_TD_DESC
    bl_options = {'REGISTER', 'UNDO'}

    face_mode: bpy.props.BoolProperty(name="Per Face", default=False, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.selected_objects or context.objects_in_mode

    def prepare_context(self, context):
        td_inputs = TdContext(context)
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            return False
        self.td_set = get_td_data(context, objs, td_inputs, self.face_mode)
        return True

    def execute(self, context):
        result = self.prepare_context(context)
        if not result:
            return {'CANCELLED'}
        if bpy.ops.uv.zenuv_hide_texel_density.poll():
            bpy.ops.uv.zenuv_hide_texel_density(map_type='ALL')
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        td_color = addon_prefs.td_color_equal.copy()
        les_color = addon_prefs.td_color_less.copy()
        over_color = addon_prefs.td_color_over.copy()
        neutral_td = round(addon_prefs.td_checker, 2)
        presets = []

        ranges = sorted(self.td_set)
        max_ranges = max(ranges)

        max_td = max(self.td_set.keys())
        min_td = min(self.td_set.keys())

        self.td_set[max_td]["color"] = over_color
        presets.append(max_td)

        self.td_set[min_td]["color"] = les_color
        presets.append(min_td)

        presets.append(neutral_td)
        if neutral_td not in self.td_set:
            self.td_set[neutral_td] = {"objs": {}, "color": td_color}
        else:
            self.td_set[neutral_td]["color"] = td_color
        presets = sorted(presets)

        ranges_filled = dict()
        for r in ranges:
            ranges_filled[r] = {"color": self.td_set[r]["color"], "preset": r in presets}

        sub_range = []
        for i in sorted(ranges_filled):
            sub_range.append(i)
            if ranges_filled[i]["preset"] or i == max_ranges:
                first_preset = sub_range[0]
                last_preset = sub_range[-1]
                first_point = ranges_filled[first_preset]
                last_point = ranges_filled[last_preset]

                top_color = last_point["color"]
                bottom_color = first_point["color"]

                preset_range = [first_preset, last_preset]

                no_steps = 101
                ligc = []
                for j in range(no_steps):
                    color = lerp_two_colors(bottom_color, top_color, j / no_steps)
                    ligc.append(color)
                for k in range(len(sub_range)):
                    value = sub_range[k]
                    position = remap_ranges(value, preset_range, (0, 100))
                    # if value not in presets:
                    self.td_set[value]["color"] = Color(ligc[round(position)])

                sub_range = [sub_range[-1], ]

        # Set Vertex Color to Object
        for c_td, data in self.td_set.items():
            for obj_name in data["objs"]:
                obj = context.scene.objects[obj_name]
                obj_mode = obj.mode
                if obj_mode == "EDIT":
                    me, bm = get_mesh_data(obj)
                    bm.faces.ensure_lookup_table()
                    self.set_vcolor_to_mesh(data, obj_name, bm)
                    bmesh.update_edit_mesh(me, loop_triangles=False)
                else:
                    bm = bmesh.new()
                    bm.from_mesh(obj.data)
                    bm.faces.ensure_lookup_table()
                    self.set_vcolor_to_mesh(data, obj_name, bm)
                    try:  # Trap for avoid error if object is multi user mesh
                        bm.to_mesh(obj.data)
                    except Exception:
                        pass
                    bm.free()
                vc_td_layer = get_td_color_map_from(obj, vc.Z_TD_BALANCED_V_MAP_NAME)
                if vc_td_layer:
                    vc_td_layer.active = True
                obj.update_from_editmode()
        switch_shading_style(context, "VERTEX", switch=False)
        return {'FINISHED'}

    def set_vcolor_to_mesh(self, data, obj_name, bm):
        for island in data["objs"][obj_name]:
            island_faces = [bm.faces[i] for i in island]
            vc.set_v_color(
                            island_faces,
                            vc.set_color_layer(bm, vc.Z_TD_BALANCED_V_MAP_NAME),
                            data["color"],
                            randomize=False
                        )


td_classes = (
    ZUV_OT_TDGetTextureSize,
    ZUV_OT_GetTexelDensity,
    ZUV_OT_GetTexelDensityOBJ,
    ZUV_OT_SetTexelDensity,
    ZUV_OT_SetTexelDensityOBJ,
    ZUV_OT_CurTDtoCheckTD,
    ZUV_OT_GetUVCoverage,
    ZUV_OT_Hide_TD,
    ZUV_OT_Display_TD_Balanced
)
