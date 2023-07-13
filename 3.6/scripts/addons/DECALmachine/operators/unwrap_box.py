import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from .. utils.uv import set_second_uv_channel
from .. items import box_unwrap_items


class BoxUnwrap(bpy.types.Operator):
    bl_idname = "machin3.box_unwrap"
    bl_label = "MACHIN3: Box Unwrap"
    bl_description = "Set up second UV channel with cubic projection for tiling textures or lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    margin: FloatProperty(name="Margin", default=0.01, precision=4, step=0.01, min=0)
    keep_previous_uv_channel_active: BoolProperty(name="Keep previous UV Channel active", default=True)

    unwrap: EnumProperty(name='Unwrap Selection, Shared Materials or Visible Objects', items=box_unwrap_items, default='SELECTION')

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.2
        row.prop(self, "unwrap", expand=True)

        column.prop(self, "margin")
        column.prop(self, "keep_previous_uv_channel_active", toggle=True)

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            return active and not context.active_object.DM.isdecal

    def execute(self, context):
        active = context.active_object

        if self.unwrap == 'SELECTION':
            sel = set(obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.DM.isdecal)
            sel.add(active)

            states = self.get_states(sel, update=True)

        elif self.unwrap == 'SHARED':
            sel = context.selected_objects.copy()
            vis = [obj for obj in context.visible_objects if obj.type == 'MESH' and not obj.DM.isdecal]

            selected_materials = set(mat for obj in sel for mat in obj.data.materials if mat and mat.DM.istrimsheetmat)

            shared = []

            for obj in vis:
                for mat in selected_materials:
                    if mat.name in obj.data.materials:
                        shared.append(obj)
                        break

            bpy.ops.object.mode_set(mode='OBJECT')

            states = self.get_states(shared, select=True)

            bpy.ops.object.mode_set(mode='EDIT')


        elif self.unwrap == 'VISIBLE':
            sel = context.selected_objects.copy()
            vis = set(obj for obj in context.visible_objects if obj.type == 'MESH' and not obj.DM.isdecal and any(mat and mat.DM.istrimsheetmat for mat in obj.data.materials))

            bpy.ops.object.mode_set(mode='OBJECT')

            states = self.get_states(vis, select=True)

            bpy.ops.object.mode_set(mode='EDIT')

        self.box_unwrap()

        bpy.ops.object.mode_set(mode='OBJECT')
        self.reset_states(states, sel, keep_previous_channel=self.keep_previous_uv_channel_active)
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

    def reset_states(self, states, sel, keep_previous_channel=False):
        for obj, d in states.items():
            obj.data.polygons.foreach_set('hide', d['face_hide'])
            obj.data.edges.foreach_set('hide', d['edge_hide'])
            obj.data.vertices.foreach_set('hide', d['vert_hide'])

            obj.data.polygons.foreach_set('select', d['face_select'])
            obj.data.edges.foreach_set('select', d['edge_select'])
            obj.data.vertices.foreach_set('select', d['vert_select'])

            if keep_previous_channel:
                obj.data.uv_layers.active_index = d['active_index']

            if obj not in sel:
                obj.select_set(False)

    def get_states(self, objects, select=False, update=False):
        states = {}

        for obj in objects:
            states[obj] = {}
            states[obj]['active_index'] = obj.data.uv_layers.active_index

            set_second_uv_channel(obj)

            if update:
                obj.update_from_editmode()

            if select:
                obj.select_set(True)

            hide = [0] * len(obj.data.polygons)
            obj.data.polygons.foreach_get('hide', hide)
            states[obj]['face_hide'] = hide

            hide = [0] * len(obj.data.edges)
            obj.data.edges.foreach_get('hide', hide)
            states[obj]['edge_hide'] = hide

            hide = [0] * len(obj.data.vertices)
            obj.data.vertices.foreach_get('hide', hide)
            states[obj]['vert_hide'] = hide

            select = [0] * len(obj.data.polygons)
            obj.data.polygons.foreach_get('select', select)
            states[obj]['face_select'] = select

            select = [0] * len(obj.data.edges)
            obj.data.edges.foreach_get('select', select)
            states[obj]['edge_select'] = select

            select = [0] * len(obj.data.vertices)
            obj.data.vertices.foreach_get('select', select)
            states[obj]['vert_select'] = select

        return states

    def box_unwrap(self):

        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')

        bpy.ops.uv.cube_project(cube_size=1, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=False)

        bpy.ops.uv.average_islands_scale()

        bpy.ops.uv.pack_islands(rotate=False, margin=self.margin)

        bpy.ops.mesh.select_all(action='DESELECT')
