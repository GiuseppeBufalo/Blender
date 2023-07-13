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

"""
    Zen UV Copy / Paste uv coordinates system
"""


import bpy
import bmesh
from mathutils import Vector
from bpy.props import BoolProperty, EnumProperty
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    get_mesh_data,
    resort_objects,
    update_indexes,
    resort_by_type_mesh,
    resort_by_type_mesh_in_edit_mode_and_sel,
    )
from ZenUV.stacks.utils import Cluster
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.clib.lib_init import StackSolver
from ZenUV.utils.constants import ZUV_COPIED, ZUV_STORED


class ZUV_OT_UV_Copy_Param(bpy.types.Operator):
    ''' Store selected UV island to mesh data '''
    bl_idname = "uv.zenuv_copy_param"
    bl_label = ZuvLabels.OT_COPY_PARAM_LABEL
    bl_description = ZuvLabels.OT_COPY_PARAM_DESC
    bl_options = {'REGISTER', 'UNDO'}

    st_store_mode: EnumProperty(
        name=ZuvLabels.PREF_OT_COPY_MODE_LABEL,
        description=ZuvLabels.PREF_OT_COPY_MODE_DESC,
        items=[
            (
                "ISLAND",
                ZuvLabels.PREF_OT_COPY_MODE_ISLAND_LABEL,
                ZuvLabels.PREF_OT_COPY_MODE_ISLAND_DESC
            ),
            (
                "FACES",
                ZuvLabels.PREF_OT_COPY_MODE_FACES_LABEL,
                ZuvLabels.PREF_OT_COPY_MODE_FACES_DESC
            ),
        ],
        default="ISLAND"
    )

    desc: bpy.props.StringProperty(name="Description", default=ZuvLabels.OT_COPY_PARAM_DESC, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        desc = properties.desc
        return desc

    uv_copy_dict = dict()
    objs = None

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        scene = context.scene
        self.objs = resort_objects(context, context.objects_in_mode)
        if not self.objs:
            self.check_copy_conditions(scene)
            return {"CANCELLED"}
        update_indexes(self.objs)
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        self.objs = resort_objects(context, context.objects_in_mode)
        # self.uv_copy_dict = dict()
        for obj in self.objs:
            self.uv_copy_dict = dict()
            me, bm = get_mesh_data(obj)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            if self.st_store_mode == "ISLAND":
                islands_for_process = island_util.get_island(context, bm, uv_layer)
            else:
                islands_for_process = island_util.get_selected_faces(context, bm)
            self.uv_copy_dict.update({obj.name: {"faces": [face.index for island in islands_for_process for face in island], "uv_layer": uv_layer.name}})
        total = sum([len(faces) for name, faces in self.uv_copy_dict.items()])
        if total:
            # store loops in scene data
            scene.zen_uv[ZUV_STORED] = self.uv_copy_dict
            self.report({"INFO"}, "Zen UV: Data stored.")
            return {"FINISHED"}
        else:
            self.check_copy_conditions(scene)
            return {"CANCELLED"}

    def check_copy_conditions(self, scene):
        if scene.zen_uv.get(ZUV_STORED, None):
            del scene.zen_uv[ZUV_STORED]
        self.report({"WARNING"}, "Zen UV: There are no selection.")


class ZUV_OT_UV_Paste_Param(bpy.types.Operator):
    ''' Paste selected Island to stored position '''
    bl_idname = "uv.zenuv_paste_param"
    bl_label = ZuvLabels.OT_PASTE_PARAM_LABEL
    bl_description = ZuvLabels.OT_PASTE_PARAM_DESC
    bl_options = {'REGISTER', 'UNDO'}

    use_stack_offset: BoolProperty(
        name="Stack Offset",
        default=False,
        description="Use Stack Offset",
    )
    fit_proportional: BoolProperty(
        name="Keep Proportion",
        default=True,
        description="Preserve proportion of the island",
    )
    st_fit_mode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_MATCH_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_MATCH_DESC,
        items=[
            (
                "tc",
                ZuvLabels.PREF_OT_PASTE_MATCH_HOR_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_HOR_DESC
            ),
            (
                "lc",
                ZuvLabels.PREF_OT_PASTE_MATCH_VERT_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_VERT_LABEL
            ),
        ],
        default="tc"
    )
    st_store_mode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_TYPE_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_TYPE_DESC,
        items=[
            (
                "ISLAND",
                ZuvLabels.PREF_OT_PASTE_TYPE_ISLAND_LABEL,
                ZuvLabels.PREF_OT_PASTE_TYPE_ISLAND_DESC
            ),
            (
                "FACES",
                ZuvLabels.PREF_OT_PASTE_TYPE_FACES_LABEL,
                ZuvLabels.PREF_OT_PASTE_TYPE_FACES_DESC
            ),
        ],
        default="ISLAND"
    )
    MatchMode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_MATCH_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_MATCH_DESC,
        items=[
            (
                "TD",
                ZuvLabels.PREF_OT_PASTE_MATCH_TD_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_TD_DESC
            ),
            (
                "FIT",
                ZuvLabels.PREF_OT_PASTE_MATCH_FIT_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_FIT_DESC
            ),
            (
                "NOTHING",
                ZuvLabels.PREF_OT_PASTE_MATCH_NOTHING_LABEL,
                ZuvLabels.PREF_OT_PASTE_MATCH_NOTHING_DESC
            ),
        ],
        default="TD"
    )
    silent: BoolProperty(
        default=False,
        description="Show stacking report",
        options={'HIDDEN'}
    )
    TransferMode: EnumProperty(
        name=ZuvLabels.PREF_OT_PASTE_TRANS_MODE_LABEL,
        description=ZuvLabels.PREF_OT_PASTE_TRANS_MODE_DESC,
        items=[
            (
                "STACK",
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_STACK_LABEL,
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_STACK_DESC
            ),
            (
                "TRANSFER",
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_TRANS_LABEL,
                ZuvLabels.PREF_OT_PASTE_TRANS_MODE_TRANS_DESC
            ),
        ],
        default="STACK"
    )
    AreaMatch: BoolProperty(
        name=ZuvLabels.PREF_OT_AREA_MATCH_LABEL,
        default=True,
        description=ZuvLabels.PREF_OT_AREA_MATCH_DESC,
        # options={'HIDDEN'}
    )
    move: BoolProperty(
        name=ZuvLabels.PREF_OT_PASTE_MOVE_LABEL,
        default=False,
        description=ZuvLabels.PREF_OT_PASTE_MOVE_DESC,
        # options={'HIDDEN'}
    )
    master_data = None
    master = None
    # clusters = []
    objs = None

    def invoke(self, context, event):
        self.objs = resort_by_type_mesh(context)
        if not self.objs:
            return {"CANCELLED"}
        update_indexes(self.objs)
        self.master_data = context.scene.zen_uv.get(ZUV_STORED).to_dict()
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        # layout.prop(self, "st_store_mode")
        # layout.separator_spacer()
        main_box = layout.box()
        main_box.label(text="Main Settings:")
        row = main_box.row(align=False)
        # row.label(text="Use Stack Offset")
        row.prop(self, "st_store_mode")
        # row.prop(self, "use_stack_offset")
        main_box.prop(self, "TransferMode")
        if self.TransferMode == 'TRANSFER':
            self.AreaMatch = True
            box = layout.box()
            self.draw_prop_on_right(layout=box, props="use_stack_offset", text="Stack Offset:")
            self.draw_prop_on_right(layout=box, props="move", text='Position:')
            r = box.row(align=True)
            r.label(text="Size:")
            r.prop(self, "MatchMode", text="")

            if self.MatchMode == 'FIT':
                box = box.box()
                box.label(text="Fit Settings:")
                box.prop(self, "fit_proportional")
                if self.fit_proportional:
                    row = box.row(align=True)
                    row.prop(self, "st_fit_mode", expand=True)

        if self.TransferMode == 'STACK':
            box = layout.box()
            box.label(text="Stacking Options:")
            box.prop(self, "use_stack_offset")
            box.prop(self, "AreaMatch")

    def draw_prop_on_right(self, layout=None, props=None, text=""):
        r = layout.row(align=True)
        r1 = r.row(align=True)
        r1.label(text=text)
        r2 = r.row(align=True)
        r2.alignment = 'RIGHT'
        r2.prop(self, props, text="")

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return (active_object is not None
                and active_object.type == 'MESH'
                and context.mode == 'EDIT_MESH'
                and context.scene.zen_uv.get(ZUV_STORED, False)
                )

    def execute(self, context):
        if not StackSolver() and self.TransferMode == 'STACK':
            self.report(
                {'WARNING'},
                "Zen UV Library is not installed! Install Library for activate Stack mode."
            )
            self.TransferMode = 'TRANSFER'
        self.objs = resort_by_type_mesh(context)
        faces_mode = self.st_store_mode == 'FACES'

        for master_obj_name, data in self.master_data.items():
            self.master = Cluster(context, master_obj_name, data["faces"])
            self.master.set_uv_layer(data["uv_layer"])
            if not self.AreaMatch:
                self.master.sim_index = int(self.master.sim_index)

        clusters = []
        for obj in self.objs:
            me, bm = get_mesh_data(obj)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            if self.st_store_mode == "ISLAND":
                islands_for_process = island_util.get_island(context, bm, uv_layer)
            else:
                islands_for_process = island_util.get_selected_faces(context, bm)

            for island in islands_for_process:
                # if island:
                cluster = Cluster(context, obj, island)
                if not self.AreaMatch:
                    cluster.sim_index = int(cluster.sim_index)
                clusters.append(cluster)

        for cl in clusters:
            cl.mode = faces_mode
            if not self.use_stack_offset:
                cl.offset = Vector((0.0, 0.0))
            cl.remap(
                self.master,
                transfer_params=self.TransferMode == "TRANSFER",
                match_position=self.move,
                match_mode=self.MatchMode,
                st_fit_mode=self.st_fit_mode,
                keep_proportion=self.fit_proportional
            )
            cl.update_mesh()
        context.scene.zen_uv[ZUV_STORED] = self.master_data
        # del self.master
        return {"FINISHED"}


class ZUV_OT_Copy_UV(bpy.types.Operator):
    ''' Store selected UV island to mesh data '''
    bl_idname = "uv.zenuv_copy_uv"
    bl_label = ZuvLabels.OT_COPY_UV_LABEL
    bl_description = ZuvLabels.OT_COPY_UV_DESC
    bl_options = {'REGISTER', 'UNDO'}

    desc: bpy.props.StringProperty(name="Description", default=ZuvLabels.OT_COPY_UV_DESC, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        desc = properties.desc
        return desc

    uv_copy_dict = dict()
    objs = None

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        uv_sync = scene.tool_settings.use_uv_select_sync
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.check_copy_conditions(scene)
            return {"CANCELLED"}
        self.uv_copy_dict = dict()
        for obj in objs:
            me, bm = get_mesh_data(obj)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            data_type = "LOOP"
            if context.area.type == 'IMAGE_EDITOR':
                if uv_sync:
                    if scene.tool_settings.mesh_select_mode[:] == (False, False, True):
                        data_type = "FACE"
            else:
                if scene.tool_settings.mesh_select_mode[:] == (False, False, True):
                    data_type = "FACE"

            self.uv_copy_dict.update({obj.name: {"loops": self.detect_loops(context, bm, data_type), "uv_layer": uv_layer.name, "data_type": data_type}})

            bmesh.update_edit_mesh(me, loop_triangles=False)

        total = sum([len(loops) for name, loops in self.uv_copy_dict.items()])
        if total:
            scene.zen_uv[ZUV_COPIED] = self.uv_copy_dict
            self.report({"INFO"}, "Zen UV: UV data stored.")
            return {"FINISHED"}
        else:
            self.check_copy_conditions(scene)
            return {"CANCELLED"}

    def check_copy_conditions(self, scene):
        if scene.zen_uv.get(ZUV_COPIED, None):
            del scene.zen_uv[ZUV_COPIED]
        self.report({"WARNING"}, "Zen UV: There are no selection.")

    def detect_loops(self, context, bm, data_type):
        in_loops = [loop for f in bm.faces for loop in f.loops]

        for index, ele in enumerate(in_loops):
            ele.index = index

        source_layer = bm.loops.layers.uv.verify()
        uv_sync = context.scene.tool_settings.use_uv_select_sync

        if context.area.type == "IMAGE_EDITOR":
            if not uv_sync:
                loops = [loop.index for loop in in_loops if loop[source_layer].select and loop.vert.select]
            elif uv_sync:
                if data_type == "FACE":
                    loops = [loop.index for loop in in_loops if loop.face.select]
                else:
                    loops = [loop.index for loop in in_loops if loop.vert.select]
        else:
            if data_type == "FACE":
                loops = [loop.index for loop in in_loops if loop.face.select]
            else:
                loops = [loop.index for loop in in_loops if loop.vert.select]

        return loops


class ZUV_OT_Paste_UV(bpy.types.Operator):

    bl_idname = "uv.zenuv_paste_uv"
    bl_label = ZuvLabels.OT_PASTE_UV_LABEL
    bl_description = "Paste the parameters saved earlier to selected Islands/Faces"

    @classmethod
    def description(cls, context, properties):
        return properties.desc

    desc: bpy.props.StringProperty(name="Description", default=ZuvLabels.OT_PASTE_UV_DESC, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "EDIT_MESH"
            and context.scene.zen_uv.get(ZUV_COPIED, False)
        )

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: There are no selected objects.")
            return {'CANCELLED'}

        self.master_data = context.scene.zen_uv.get(ZUV_COPIED).to_dict()

        objs_dict = dict()
        for obj in objs:
            objs_dict.update({obj.name: obj})

        processed = False
        for master_obj_name, data in self.master_data.items():
            if master_obj_name in objs_dict:
                obj = objs_dict[master_obj_name]
                me = obj.data
                bm = bmesh.from_edit_mesh(me)
                source_loops_idxs = data["loops"]
                source_layer_name = data["uv_layer"]
                source_layer = bm.loops.layers.uv.get(source_layer_name)
                dest_layer = bm.loops.layers.uv.verify()
                dest_layer_name = dest_layer.name

                if source_layer_name == dest_layer_name:
                    self.report({'WARNING'}, "Zen UV: Source and Destination UV Map is the same.")
                    return {'CANCELLED'}

                if source_layer:
                    self.paste_uv(context, bm, source_layer, source_loops_idxs, dest_layer)
                    processed = True

                bmesh.update_edit_mesh(me)

            if not processed:
                self.report({'WARNING'}, "Zen UV: There is no stored data for selected objects.")
                return {'CANCELLED'}

        return {"FINISHED"}

    def paste_uv(self, context, bm, source_layer, source_loops_idxs, dest_layer):
        in_loops = [loop for f in bm.faces for loop in f.loops]
        loops = [in_loops[idx] for idx in source_loops_idxs]

        for loop in loops:
            loop[dest_layer].uv = loop[source_layer].uv


if __name__ == '__main__':
    pass
