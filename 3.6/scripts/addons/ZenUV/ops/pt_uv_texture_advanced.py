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

# <pep8 compliant>

# Original idea Oleg Stepanov (DotBow) https://github.com/DotBow/Blender-Launcher

import bpy
from bpy.app.handlers import load_post, persistent
from bpy.types import Operator, Panel
from bpy.utils import register_class, unregister_class
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.hops_integration import show_uv_in_3dview
from ZenUV.utils.generic import (
    ZenKeyEventSolver,
    resort_by_type_mesh_in_edit_mode_and_sel
)
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.utils.base_clusters.base_cluster import BaseCluster, ProjectCluster
from ZenUV.utils.constants import ADV_UV_MAP_NAME_PATTERN


class projCluster(
    BaseCluster,
    ProjectCluster,
):
    def __init__(self, context, obj, island, bm=None) -> None:
        super().__init__(context, obj, island, bm)


def add_uv_texture(self, obj):
    print('Process obj:', obj.name)

    if len(obj.data.uv_layers) == 8:
        return False
    
    uv_map = obj.data.uv_layers.new()
    uv_map.active = True

    bpy.ops.object.editmode_toggle()

    bpy.ops.mesh.select_all(action='SELECT')

    if self.mode == 'SMART':
        bpy.ops.uv.smart_project(
            angle_limit=66.0, island_margin=0.01, area_weight=0.0)
    elif self.mode == 'CUBE':
        bpy.ops.uv.cube_project()
    elif self.mode == 'CYLINDER':
        bpy.ops.uv.cylinder_project()
    elif self.mode == 'SPHERE':
        bpy.ops.uv.sphere_project()

    bpy.ops.object.editmode_toggle()

    return True


class AddUVMaps(Operator):

    bl_description = ZuvLabels.OT_ADD_UV_MAPS_DESC
    bl_idname = "mesh.add_uvs"
    bl_label = "Add UV Map"
    bl_options = {'REGISTER', 'UNDO'}

    desc: bpy.props.StringProperty(
        name="Description",
        default=ZuvLabels.OT_ADD_UV_MAPS_DESC,
        options={'HIDDEN'}
    )

    mode: bpy.props.EnumProperty(
        name='Unwrap Mode',
        items=[
            ('DEFAULT', 'Default', ''),
            ('SMART', 'Smart', ''),
            ('CUBE', 'Cube', ''),
            ('CYLINDER', 'Cylinder', ''),
            ('SPHERE', 'Sphere', ''),
        ],
        default='DEFAULT'
    )
    is_modifier_right: bpy.props.BoolProperty(name='Is Zen Modifier key', default=False, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        addon_prefs = get_prefs()
        zk_mod = addon_prefs.bl_rna.properties['zen_key_modifier'].enum_items
        zk_mod = zk_mod.get(addon_prefs.zen_key_modifier)
        cls.desc = ZuvLabels.OT_ADD_UV_MAPS_DESC.replace("*", zk_mod.name)
        return cls.desc

    def invoke(self, context, event):
        self.is_modifier_right = ZenKeyEventSolver(context, event, get_prefs()).solve()
        return self.execute(context)

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "Select something.")
            return {'CANCELLED'}

        was_mode = context.mode
        active_ob = context.active_object

        if was_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')

        if self.is_modifier_right:

            for ob in objs:
                context.view_layer.objects.active = ob
                result = add_uv_texture(self, ob)
                if not result:
                    self.report({'WARNING'}, "Cannot add more than 8 UV maps")

            context.view_layer.objects.active = active_ob
        else:
            result = add_uv_texture(self, active_ob)
            if not result:
                self.report({'WARNING'}, "Cannot add more than 8 UV maps")

        # for obj in objs:
        #     if len(obj.data.uv_layers) == 1:
        #         if obj.mode == 'OBJECT':
        #             cluster = ProjectCluster()
        #             cluster.set_object(obj)
        #             cluster.set_fit_to_uv(False)
        #             cluster.set_transform(obj.matrix_world)
        #             cluster.project_obj_mode()
        #         elif obj.mode == 'EDIT':
        #             me, bm = get_mesh_data(obj)
        #             cluster = projCluster(context, obj, bm.faces, bm)
        #             cluster.set_fit_to_uv(False)
        #             cluster.set_transform(obj.matrix_world)
        #             cluster.project()
        #             bmesh.update_edit_mesh(me)

        for obj in objs:
            obj.select_set(True)

        if was_mode != 'OBJECT':
            bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class RemoveUVMaps(Operator):

    bl_description = ZuvLabels.OT_REMOVE_UV_MAPS_DESC
    bl_idname = "mesh.remove_uvs"
    bl_label = ""
    bl_options = {'INTERNAL'}

    desc: bpy.props.StringProperty(
        name="Description",
        default=ZuvLabels.OT_REMOVE_UV_MAPS_DESC,
        options={'HIDDEN'}
    )
    is_modifier_right: bpy.props.BoolProperty(name='Is Zen Modifier key', default=False, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        addon_prefs = get_prefs()
        zk_mod = addon_prefs.bl_rna.properties['zen_key_modifier'].enum_items
        zk_mod = zk_mod.get(addon_prefs.zen_key_modifier)
        cls.desc = ZuvLabels.OT_REMOVE_UV_MAPS_DESC.replace("*", zk_mod.name)
        return cls.desc

    def invoke(self, context, event):
        is_modifier_right = ZenKeyEventSolver(context, event, get_prefs()).solve()
        # if event.alt:
        if is_modifier_right:
            active_ob = context.active_object

            # for ob in context.selected_objects:
            for ob in resort_by_type_mesh_in_edit_mode_and_sel(context):
                context.view_layer.objects.active = ob
                redraw()
                if bpy.ops.mesh.uv_texture_remove.poll():
                    bpy.ops.mesh.uv_texture_remove()

            context.view_layer.objects.active = active_ob
        else:
            if bpy.ops.mesh.uv_texture_remove.poll():
                bpy.ops.mesh.uv_texture_remove()

        bpy.ops.ed.undo_push(message="Remove active UV Maps")
        return {'FINISHED'}


class ShowUVMap(Operator):

    bl_description = ZuvLabels.OT_SHOW_UV_MAP_DESC
    bl_idname = "mesh.show_uvs"
    bl_label = ZuvLabels.OT_SHOW_UV_MAP_LABEL
    bl_options = {'INTERNAL'}

    desc: bpy.props.StringProperty(
        name="Description",
        default=ZuvLabels.OT_SHOW_UV_MAP_DESC,
        options={'HIDDEN'}
    )

    @classmethod
    def description(cls, context, properties):
        addon_prefs = get_prefs()
        zk_mod = addon_prefs.bl_rna.properties['zen_key_modifier'].enum_items
        zk_mod = zk_mod.get(addon_prefs.zen_key_modifier)
        cls.desc = ZuvLabels.OT_SHOW_UV_MAP_DESC.replace("*", zk_mod.name)
        return cls.desc

    def execute(self, context):
        show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=False)
        return {'FINISHED'}


class RemoveInactiveUVMaps(Operator):

    bl_description = ZuvLabels.OT_CLEAN_REMOVE_UV_MAPS_DESC
    bl_idname = "mesh.remove_inactive_uvs"
    bl_label = ZuvLabels.OT_CLEAN_REMOVE_UV_MAPS_LABEL
    bl_options = {'INTERNAL', 'UNDO_GROUPED'}

    desc: bpy.props.StringProperty(
        name="Description",
        default=ZuvLabels.OT_CLEAN_REMOVE_UV_MAPS_DESC,
        options={'HIDDEN'}
    )
    is_modifier_right: bpy.props.BoolProperty(name='Is Zen Modifier key', default=False, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        addon_prefs = get_prefs()
        zk_mod = addon_prefs.bl_rna.properties['zen_key_modifier'].enum_items
        zk_mod = zk_mod.get(addon_prefs.zen_key_modifier)
        cls.desc = ZuvLabels.OT_CLEAN_REMOVE_UV_MAPS_DESC.replace("*", zk_mod.name)
        return cls.desc

    def invoke(self, context, event):
        self.is_modifier_right = ZenKeyEventSolver(context, event, get_prefs()).solve()
        # if event.alt:
        if self.is_modifier_right:
            active_ob = context.active_object

            # for ob in context.selected_objects:
            for ob in resort_by_type_mesh_in_edit_mode_and_sel(context):
                context.view_layer.objects.active = ob
                redraw()
                self.remove_inactive_uvs(ob)

            context.view_layer.objects.active = active_ob
        else:
            self.remove_inactive_uvs(context.active_object)

        return {'FINISHED'}

    def remove_inactive_uvs(self, ob):
        active_index = ob.data.uv_layers.active_index

        if active_index != -1:
            active_name = ob.data.uv_layers[active_index].name
            i = 0

            while len(ob.data.uv_layers) > 1:
                layer = ob.data.uv_layers[i]

                if layer.name != active_name:
                    layer.active = True
                    bpy.ops.mesh.uv_texture_remove()
                    i = 0
                else:
                    i = 1


class RenameUVMaps(Operator):

    bl_description = ZuvLabels.OT_RENAME_UV_MAPS_DESC
    bl_idname = "mesh.rename_uvs"
    bl_label = ZuvLabels.OT_RENAME_UV_MAPS_LABEL
    bl_options = {'REGISTER', 'UNDO'}

    name_pattern: bpy.props.StringProperty(name="Name", default=ADV_UV_MAP_NAME_PATTERN)

    use_numbering: bpy.props.BoolProperty(
        name='Use Numbering',
        default=True,
        description='Use numbering along renaming',
        )

    use_default_name: bpy.props.BoolProperty(
        name='Use Default Name (UVMap)',
        default=False,
        description='Use native name (UVMap)',
        )

    active_only: bpy.props.BoolProperty(
        name='Active Only',
        default=False,
        description='Rename Active UV Maps only',
        )

    desc: bpy.props.StringProperty(
        name="Description",
        default=ZuvLabels.OT_RENAME_UV_MAPS_DESC,
        options={'HIDDEN'}
    )
    is_modifier_right: bpy.props.BoolProperty(name='Is Zen Modifier key', default=False, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        addon_prefs = get_prefs()
        zk_mod = addon_prefs.bl_rna.properties['zen_key_modifier'].enum_items
        zk_mod = zk_mod.get(addon_prefs.zen_key_modifier)
        cls.desc = ZuvLabels.OT_RENAME_UV_MAPS_DESC.replace("*", zk_mod.name)
        return cls.desc

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.enabled = not self.use_default_name
        row.prop(self, "name_pattern")
        layout.prop(self, "use_default_name")
        layout.prop(self, "use_numbering")
        layout.prop(self, "active_only")

    def invoke(self, context, event):
        wm = context.window_manager
        self.is_modifier_right = ZenKeyEventSolver(context, event, get_prefs()).solve()
        return wm.invoke_props_dialog(self)
        # return {'FINISHED'}

    def execute(self, context):
        # if event.alt:
        if self.is_modifier_right:
            # for ob in context.selected_objects:
            for ob in resort_by_type_mesh_in_edit_mode_and_sel(context):
                self.rename_uvs(ob)
        else:
            self.rename_uvs(context.active_object)
        return {'FINISHED'}

    def rename_uvs(self, ob):
        uv_layers = ob.data.uv_layers if not self.active_only else [layer for layer in ob.data.uv_layers if layer.active]
        name = 'UVMap' if self.use_default_name else self.name_pattern

        for i in range(0, len(uv_layers)):
            if self.use_numbering:
                uv_layers[i].name = name + str(i + 1)
            else:
                uv_layers[i].name = name


class SyncUVMapsIDs(Operator):
    #     """\
    # - Set the same active UV Map index for all selected objects.
    # - Hold Zen Modifier Key to enable/disable automatic synchronisation.
    # - Blue background - UV Maps are synchronised.
    # - Red background - UV Maps are desynchronised"""
    bl_description = ZuvLabels.OT_SYNC_UV_MAPS_DESC
    bl_idname = "mesh.sync_uv_ids"
    bl_label = ZuvLabels.OT_SYNC_UV_MAPS_LABEL
    bl_options = {'INTERNAL'}

    desc: bpy.props.StringProperty(
        name="Description",
        default=ZuvLabels.OT_SYNC_UV_MAPS_DESC,
        options={'HIDDEN'}
    )
    is_modifier_right: bpy.props.BoolProperty(name='Is Zen Modifier key', default=False, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        addon_prefs = get_prefs()
        zk_mod = addon_prefs.bl_rna.properties['zen_key_modifier'].enum_items
        zk_mod = zk_mod.get(addon_prefs.zen_key_modifier)
        cls.desc = ZuvLabels.OT_SYNC_UV_MAPS_DESC.replace("*", zk_mod.name)
        return cls.desc

    def invoke(self, context, event):
        self.is_modifier_right = ZenKeyEventSolver(context, event, get_prefs()).solve()
        # if event.alt:
        if self.is_modifier_right:
            scene = context.scene

            if ('auto_sync_uv_ids' in scene) and scene['auto_sync_uv_ids']:
                scene['auto_sync_uv_ids'] = False
            else:
                bpy.ops.wm.auto_sync_uv_ids('INVOKE_DEFAULT')
        else:
            self.sync_uvs(context)

        return {'FINISHED'}

    def sync_uvs(self, context):
        try:
            active_index = context.active_object.data.uv_layers.active_index

            if active_index != -1:
                # for ob in context.selected_objects:
                for ob in resort_by_type_mesh_in_edit_mode_and_sel(context):
                    if len(ob.data.uv_layers) >= active_index:
                        ob.data.uv_layers.active_index = active_index
        except Exception:
            print("Zen UV: Sync UV Maps Error!")

        return {'FINISHED'}


class AutoSyncUVMapsIDs(Operator):
    #     """\
    # Automatically set the same active UV Map
    # index for all selected objects"""
    bl_description = ZuvLabels.OT_AUTO_SYNC_UV_MAPS_DESC
    bl_idname = "wm.auto_sync_uv_ids"
    bl_label = ZuvLabels.OT_AUTO_SYNC_UV_MAPS_LABEL
    bl_options = {'INTERNAL'}

    _timer = None
    _index = -1
    _count = 0

    def modal(self, context, event):
        scene = context.scene

        # Prevent properties from been lost on undo
        if 'auto_sync_uv_ids' not in scene:
            scene['auto_sync_uv_ids'] = True
            scene['auto_sync_uv_ids_state'] = True
            redraw()

        if not scene['auto_sync_uv_ids']:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            selected_objects = context.selected_objects
            count = len(selected_objects)

            # Perform only on multiple objects
            if count > 1:
                ob = context.active_object
                active_index = ob.data.uv_layers.active_index

                # Perform only if selection or active index changed
                if (count != self._count) or (active_index != self._index):
                    self._index = active_index
                    self._count = count

                    if active_index != -1:
                        state = True

                        for ob in selected_objects:
                            if ob.type == "MESH" and len(ob.data.uv_layers) > active_index:
                                ob.data.uv_layers.active_index = active_index
                            else:
                                state = False

                        scene['auto_sync_uv_ids_state'] = state
                    else:
                        scene['auto_sync_uv_ids_state'] = False
            else:
                if not scene['auto_sync_uv_ids_state']:
                    scene['auto_sync_uv_ids_state'] = True
                    redraw()

                self._count = 0

        return {'PASS_THROUGH'}

    def execute(self, context):
        self._ob = context.active_object
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        context.scene['auto_sync_uv_ids'] = True
        context.scene['auto_sync_uv_ids_state'] = True
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        context.scene['auto_sync_uv_ids'] = False
        context.scene['auto_sync_uv_ids_state'] = False


class DATA_PT_uv_texture_advanced(Panel):
    bl_label = ZuvLabels.PT_ADV_UV_MAPS_LABEL
    bl_order = 0
    bl_category = "Zen UV"
    bl_region_type = "UI"
    bl_context = ""
    bl_space_type = "VIEW_3D"

    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'}

    @classmethod
    def poll(cls, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        engine = context.engine
        return addon_prefs.enable_pt_adv_uv_map and context.active_object and context.active_object.type == "MESH" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        draw_pt_uv_texture_advanced(context, layout)
        draw_copy_paste(layout)


class DATA_PT_UVL_uv_texture_advanced(Panel):
    bl_label = ZuvLabels.PT_ADV_UV_MAPS_LABEL
    bl_order = 0
    bl_category = "Zen UV"
    bl_region_type = "UI"
    bl_context = ""
    bl_space_type = "IMAGE_EDITOR"

    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'}

    @classmethod
    def poll(cls, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        engine = context.engine
        return addon_prefs.uv_enable_pt_adv_uv_map and context.active_object and context.active_object.type == "MESH" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        draw_pt_uv_texture_advanced(context, layout)
        draw_copy_paste(layout)


def draw_pt_uv_texture_advanced(context, layout):
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences

    row = layout.row()
    row.operator(RemoveInactiveUVMaps.bl_idname, icon='TRASH')
    row.operator(RenameUVMaps.bl_idname, icon='SORTALPHA')

    scene = context.scene
    _depress = False

    if 'auto_sync_uv_ids' in scene:
        auto_sync_uv_ids = scene['auto_sync_uv_ids']
        _depress = auto_sync_uv_ids

        if auto_sync_uv_ids:
            state = scene['auto_sync_uv_ids_state']

            row = row.row()
            row.alert = not state

    row.operator(
        SyncUVMapsIDs.bl_idname, text="",
        icon='UV_SYNC_SELECT',
        depress=_depress
        )

    me = context.object.data
    row = layout.row()
    col = row.column()

    col.template_list(
        "MESH_UL_uvmaps", "uvmaps",
        me,
        "uv_layers",
        me.uv_layers,
        "active_index",
        rows=2
    )

    col = row.column(align=True)
    col.operator(AddUVMaps.bl_idname, icon='ADD', text="")
    col.operator(RemoveUVMaps.bl_idname, icon='REMOVE', text="")
    if addon_prefs.hops_uv_activate:
        col.operator(ShowUVMap.bl_idname, icon='HIDE_OFF', text="")


def draw_copy_paste(layout):
    row = layout.row(align=True)

    row.operator("uv.zenuv_copy_uv", icon="COPYDOWN")
    row.operator("uv.zenuv_paste_uv", icon="PASTEDOWN")


def redraw():
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


classes = (
    AddUVMaps,
    RemoveUVMaps,
    AutoSyncUVMapsIDs,
    RemoveInactiveUVMaps,
    RenameUVMaps,
    SyncUVMapsIDs,
    DATA_PT_uv_texture_advanced,
)


@persistent
def _load_post(dummy):
    scene = bpy.context.scene

    if ('auto_sync_uv_ids' in scene) and scene['auto_sync_uv_ids']:
        bpy.ops.wm.auto_sync_uv_ids('INVOKE_DEFAULT')


def register_pt_uv_texture_advanced():
    for cls in classes:
        register_class(cls)

    load_post.append(_load_post)


def unregister_pt_uv_texture_advanced():
    for cls in classes:
        unregister_class(cls)

    load_post.remove(_load_post)


if __name__ == "__main__":
    pass
