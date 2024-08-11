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
from xmlrpc.client import Boolean
import bpy
import bmesh

from ZenUV.utils.transform import move_island
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    fit_uv_view,
    select_by_context,
    set_face_int_tag,
    resort_by_type_mesh_in_edit_mode_and_sel
)

from ZenUV.prop.zuv_preferences import get_prefs

from ZenUV.utils.generic import ZUV_PANEL_CATEGORY, ZUV_REGION_TYPE, ZUV_SPACE_TYPE
from ZenUV.utils.constants import PACK_EXCLUDED_FACEMAP_NAME, PACK_EXCLUDED_V_MAP_NAME


class pLogger:
    """ Simple process logger.
        Main purpose is logging processes in the multi object selection mode
    """
    def __init__(self) -> None:
        self.storage = []

    def store(self, value: Boolean):
        self.storage.append(value)

    def get_result(self):
        return True in self.storage


class ZuvPackExcludedLabels:

    PT_EXCLUDED_LABEL = "Excluded"
    POPUP_PROPS_LABEL = "Pack Excluded Properties"

    OT_OFFSET_EXCLUDED_LABEL = "Offset Excluded"
    OT_OFFSET_EXCLUDED_DESC = "Move Islands tagged as Excluded from Packing out of UV Area"

    PROP_OFFSET_EXCLUDED_LABEL = "Offset"
    PROP_OFFSET_EXCLUDED_DESC = "Offset value"

    OT_TAG_EXCL_LABEL = "Tag Excluded"
    OT_TAG_EXCL_DESC = "Tag Islands as Excluded from Packing"

    OT_UNTAG_EXCL_LABEL = "Untag Excluded"
    OT_UNTAG_EXCL_DESC = "Untag Islands tagged as Excluded from Packing"

    OT_HIDE_EXCL_LABEL = "Hide"
    OT_HIDE_EXCL_DESC = "Hide Islands tagged as Excluded from Packing"

    OT_UNHIDE_EXCL_LABEL = "Unhide"
    OT_UNHIDE_EXCL_DESC = "Unhide Islands tagged as Excluded from Packing"

    OT_DISPLAY_EXCL_LABEL = "Display Excluded"
    OT_DISPLAY_EXCL_DESC = "Display Islands tagged as Excluded from Packing"

    OT_SELECT_EXCL_LABEL = "Select Excluded"
    OT_SELECT_EXCL_DESC = "Select Islands tagged as Excluded from Packing"

    OT_PROP_SELECT_EXCL_LABEL = "Clear"
    OT_PROP_SELECT_EXCL_DESC = "Clear previous selection"


class SYSTEM_PT_PackExcluded_UV(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_label = ZuvPackExcludedLabels.PT_EXCLUDED_LABEL
    bl_parent_id = "ZUV_PT_UVL_Pack"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "SYSTEM_PT_PackExcluded_UV"
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return get_prefs().packEngine != "UVPACKER"

    def draw(self, context):
        draw_pack_excluded_section(self, context)


class SYSTEM_PT_PackExcluded(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_label = ZuvPackExcludedLabels.PT_EXCLUDED_LABEL
    bl_parent_id = "ZUV_PT_Pack"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "SYSTEM_PT_PackExcluded"
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return get_prefs().packEngine != "UVPACKER"

    def draw(self, context):
        draw_pack_excluded_section(self, context)


class ZUV_PT_pExclude_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV Pack Excluded Section Properties"""
    bl_idname = "ZUV_PT_pExclude_Properties"
    bl_label = ZuvPackExcludedLabels.POPUP_PROPS_LABEL
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        layout.prop(get_prefs(), 'ExcludedColor')


def draw_pack_excluded_section(self, context):
    """ Pack Excluded Section """
    layout = self.layout
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator(ZUV_OT_OffsetPackExcluded.bl_idname)
    row.popover(panel="ZUV_PT_pExclude_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.operator(ZUV_OT_Tag_PackExcluded.bl_idname)
    row.operator(ZUV_OT_UnTag_PackExcluded.bl_idname)
    row = col.row(align=True)
    row.operator(ZUV_OT_Hide_PackExcluded.bl_idname)
    row.operator(ZUV_OT_UnHide_PackExcluded.bl_idname)

    col.operator(ZUV_OT_Select_PackExcluded.bl_idname)

    col.prop(context.scene.zen_display, "p_excluded", toggle=True, icon='HIDE_OFF')


class ExclusionObj:

    def __init__(self, object_name, excluded_faces, sel_faces) -> None:
        self.obj_name = object_name
        self.faces = excluded_faces
        self.selection = sel_faces


class PackExcludedFactory:

    exclusion = []

    @classmethod
    def ensure_facemap(self, bm, facemap_name):
        """ Return facemap int type or create new """
        facemap = bm.faces.layers.int.get(facemap_name)
        if not facemap:
            facemap = bm.faces.layers.int.new(facemap_name)
        return facemap

    @classmethod
    def get_pack_excluded_map_from(self, _obj):
        """ Return excluded VC Layer or None """
        return _obj.data.vertex_colors.get(PACK_EXCLUDED_V_MAP_NAME) or None

    @classmethod
    def tag_pack_excluded(self, context, objs, action):
        """
        Tag or untag Pack Excluded depend on action='TAG' / 'UNTAG'
        """
        log = pLogger()
        for obj in objs:
            me, bm, uv_layer = self._get_obj_bm_data(obj)
            pack_excluded_facemap = self.ensure_facemap(bm, PACK_EXCLUDED_FACEMAP_NAME)
            islands_for_process = island_util.get_island(context, bm, uv_layer)
            log.store(len(islands_for_process) != 0)

            if action == "TAG":
                tag = 1
            elif action == "UNTAG":
                tag = 0

            set_face_int_tag(islands_for_process, pack_excluded_facemap, int_tag=tag)
            bmesh.update_edit_mesh(me)

        return log.get_result()

    @classmethod
    def _get_obj_bm_data(self, obj):
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        return me, bm, uv_layer

    @classmethod
    def offset_tagged_islands(self, context, objs, direction):
        log = pLogger()
        for obj in objs:
            me, bm, uv_layer = self._get_obj_bm_data(obj)
            pack_excluded_facemap = self.ensure_facemap(bm, PACK_EXCLUDED_FACEMAP_NAME)
            uv_layer = bm.loops.layers.uv.verify()
            for island in island_util.get_islands(context, bm):
                if True in [face[pack_excluded_facemap] for face in island]:
                    log.store(True)
                    move_island(island, uv_layer, move_vector=direction)
                log.store(False)
            bmesh.update_edit_mesh(me)
        return log.get_result()

    @classmethod
    def select_excluded(self, context, objs, clear):
        log = pLogger()
        for obj in objs:
            me, bm, uv_layer = self._get_obj_bm_data(obj)
            pack_excluded_facemap = self.ensure_facemap(bm, PACK_EXCLUDED_FACEMAP_NAME)
            islands_for_select = [island for island in island_util.get_islands(context, bm) if True in [f[pack_excluded_facemap] for f in island]]
            log.store(len(islands_for_select) != 0)

            if clear:
                select_by_context(context, bm, [bm.faces], state=False)

            select_by_context(context, bm, islands_for_select, state=True)
            bmesh.update_edit_mesh(me)
        return log.get_result()

    def hide_by_facemap(self, context, objs):
        self.exclusion.clear()
        log = pLogger()
        for obj in objs:
            me, bm, uv_layer = self._get_obj_bm_data(obj)
            _facemap = self.ensure_facemap(bm, PACK_EXCLUDED_FACEMAP_NAME)
            islands = [island for island in island_util.get_islands(context, bm) if True in [f[_facemap] for f in island]]
            log.store(len(islands) != 0)

            ex_faces = [f.index for island in islands for f in island]
            sel_faces = [f.index for island in islands for f in island if f.select]
            self.exclusion.append(ExclusionObj(obj.name, ex_faces, sel_faces))

            for i in ex_faces:
                bm.faces[i].hide_set(True)

            bmesh.update_edit_mesh(me)
        return log.get_result()

    def unhide_by_facemap(self, objs):
        log = pLogger()
        for obj in objs:
            me, bm, uv_layer = self._get_obj_bm_data(obj)
            _facemap = self.ensure_facemap(bm, PACK_EXCLUDED_FACEMAP_NAME)
            hidden_faces = [f.index for f in bm.faces if f.hide and f[_facemap]]
            log.store(len(hidden_faces) != 0)

            for i in hidden_faces:
                bm.faces[i].hide_set(False)

            bmesh.update_edit_mesh(me)
        return log.get_result()

    def unhide_by_stored(self, context):
        if self.exclusion:
            for st in self.exclusion:
                me, bm, uv_layer = self._get_obj_bm_data(context.scene.objects[st.obj_name])
                if st.faces:
                    for i in st.faces:
                        bm.faces[i].hide_set(False)
                bmesh.update_edit_mesh(me)
            return True
        return False

    def restore_selection(self, context):
        if self.exclusion:
            for st in self.exclusion:
                me, bm, uv_layer = self._get_obj_bm_data(context.scene.objects[st.obj_name])
                if st.selection:
                    for i in st.selection:
                        bm.faces[i].select = True
                bmesh.update_edit_mesh(me)
            return True
        return False


class ZUV_OT_OffsetPackExcluded(bpy.types.Operator):
    bl_idname = "uv.zenuv_offset_pack_excluded"
    bl_label = ZuvPackExcludedLabels.OT_OFFSET_EXCLUDED_LABEL
    bl_description = ZuvPackExcludedLabels.OT_OFFSET_EXCLUDED_DESC
    bl_options = {'REGISTER', 'UNDO'}

    offset: bpy.props.FloatVectorProperty(
        name=ZuvPackExcludedLabels.PROP_OFFSET_EXCLUDED_LABEL,
        description=ZuvPackExcludedLabels.PROP_OFFSET_EXCLUDED_DESC,
        size=2,
        default=(1.0, 0.0),
        subtype='XYZ'
    )

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        PEF = PackExcludedFactory()
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        res = PEF.offset_tagged_islands(context, objs, self.offset)
        if not res:
            self.report({'WARNING'}, "Zen UV: There is no Excluded Islands.")
            return {'CANCELLED'}
        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_Tag_PackExcluded(bpy.types.Operator):
    """
    Operator to Tag PackExcluded Islands
    """
    bl_idname = "uv.zenuv_tag_pack_excluded"
    bl_label = ZuvPackExcludedLabels.OT_TAG_EXCL_LABEL
    bl_description = ZuvPackExcludedLabels.OT_TAG_EXCL_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        res = PackExcludedFactory.tag_pack_excluded(context, objs, action="TAG")
        if not res:
            self.report({'WARNING'}, "Zen UV: There is no Selection.")
            return {'CANCELLED'}

        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_Hide_PackExcluded(bpy.types.Operator):
    """
    Operator to Hide PackExcluded Islands
    """
    bl_idname = "uv.zenuv_hide_pack_excluded"
    bl_label = ZuvPackExcludedLabels.OT_HIDE_EXCL_LABEL
    bl_description = ZuvPackExcludedLabels.OT_HIDE_EXCL_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        PEF = PackExcludedFactory()
        res = PEF.hide_by_facemap(context, objs)
        if not res:
            self.report({'WARNING'}, "Zen UV: There is no Excluded Islands for Hide.")
            return {'CANCELLED'}

        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_UnHide_PackExcluded(bpy.types.Operator):
    """
    Operator to Hide PackExcluded Islands
    """
    bl_idname = "uv.zenuv_unhide_pack_excluded"
    bl_label = ZuvPackExcludedLabels.OT_UNHIDE_EXCL_LABEL
    bl_description = ZuvPackExcludedLabels.OT_UNHIDE_EXCL_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        PEF = PackExcludedFactory()
        res = PEF.unhide_by_facemap(objs)
        if not res:
            self.report({'WARNING'}, "Zen UV: Nothing Unhided")
            return {'CANCELLED'}

        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_UnTag_PackExcluded(bpy.types.Operator):
    """
    Operator to Untag Pack Excluded Islands
    """
    bl_idname = "uv.zenuv_untag_pack_excluded"
    bl_label = ZuvPackExcludedLabels.OT_UNTAG_EXCL_LABEL
    bl_description = ZuvPackExcludedLabels.OT_UNTAG_EXCL_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        res = PackExcludedFactory.tag_pack_excluded(context, objs, action="UNTAG")
        if not res:
            self.report({'WARNING'}, "Zen UV: There is no Selection.")
            return {'CANCELLED'}

        fit_uv_view(context, mode="checker")
        return {'FINISHED'}


class ZUV_OT_Display_PackExcluded(bpy.types.Operator):
    bl_idname = "uv.zenuv_display_pack_excluded"
    bl_label = ZuvPackExcludedLabels.OT_DISPLAY_EXCL_LABEL
    bl_description = ZuvPackExcludedLabels.OT_DISPLAY_EXCL_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.zen_display.p_excluded = not context.scene.zen_display.p_excluded
        return {"FINISHED"}


class ZUV_OT_Select_PackExcluded(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_pack_excluded"
    bl_label = ZuvPackExcludedLabels.OT_SELECT_EXCL_LABEL
    bl_description = ZuvPackExcludedLabels.OT_SELECT_EXCL_DESC
    bl_options = {'REGISTER', 'UNDO'}

    clear_sel: bpy.props.BoolProperty(
        name=ZuvPackExcludedLabels.OT_PROP_SELECT_EXCL_LABEL,
        description=ZuvPackExcludedLabels.OT_PROP_SELECT_EXCL_DESC,
        default=True
    )

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        res = PackExcludedFactory.select_excluded(context, objs, self.clear_sel)

        if not res:
            self.report({'WARNING'}, "Zen UV: There is no Excluded Islands.")
            return {'CANCELLED'}

        return {"FINISHED"}


pack_exlusion_classes = [
    ZUV_OT_Tag_PackExcluded,
    ZUV_OT_UnTag_PackExcluded,
    ZUV_OT_Select_PackExcluded,
    ZUV_OT_OffsetPackExcluded,
    ZUV_OT_Hide_PackExcluded,
    ZUV_OT_UnHide_PackExcluded
]

pack_exclusion_panels = [
    SYSTEM_PT_PackExcluded_UV,
    SYSTEM_PT_PackExcluded,
    ZUV_PT_pExclude_Properties,
]


def register_pack_exclusion():
    from bpy.utils import register_class
    for cl in pack_exlusion_classes:
        register_class(cl)
    for cl in pack_exclusion_panels:
        register_class(cl)


def unregister_pack_exclusion():
    from bpy.utils import unregister_class
    for cl in pack_exclusion_panels:
        unregister_class(cl)
    for cl in pack_exlusion_classes:
        unregister_class(cl)


if __name__ == '__main__':
    pass
