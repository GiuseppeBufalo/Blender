import bpy
from bpy.props import StringProperty, FloatProperty
from ... utils.draw import draw_fading_label
from ... utils.object import parent
from ... utils.raycast import get_closest
from ... utils.registration import get_addon_prefs, get_addon, get_prefs
from ... utils.tools import get_tools_from_context, get_tool_options, get_active_tool
from ... utils.tools import prettify_tool_name
from ... utils.view import update_local_view
from ... colors import white, green

boxcutter = None

class SetToolByName(bpy.types.Operator):
    bl_idname = "machin3.set_tool_by_name"
    bl_label = "MACHIN3: Set Tool by Name"
    bl_description = "Set Tool by Name"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Tool name/ID")
    alpha: FloatProperty(name="Alpha", default=0.5, min=0.1, max=1)
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        column.label(text=f"Tool: {self.name}")

    def execute(self, context):
        global first_annotate, first_erase

        active_tool = get_active_tool(context).idname

        if active_tool == 'machin3.tool_hyper_cursor_simple':
            context.space_data.overlay.show_cursor = True

        bpy.ops.wm.tool_set_by_id(name=self.name)

        if 'machin3.tool_hyper_cursor' in self.name:
            size, color = 20, green
        else:
            size, color = 12, white

        draw_fading_label(context, text=prettify_tool_name(self.name), time=get_prefs().HUD_fade_tools_pie, size=size, color=color, move_y=10)

        return {'FINISHED'}

class SetBCPreset(bpy.types.Operator):
    bl_idname = "machin3.set_boxcutter_preset"
    bl_label = "MACHIN3: Set BoxCutter Preset"
    bl_description = "Quickly enable/switch BC tool in/to various modes"
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty()
    shape_type: StringProperty()
    set_origin: StringProperty(default='MOUSE')
    @classmethod
    def poll(cls, context):
        global boxcutter

        if boxcutter is None:
            _, boxcutter, _, _ = get_addon("BoxCutter")

        return boxcutter in get_tools_from_context(context)

    def execute(self, context):
        global boxcutter

        if boxcutter is None:
            _, boxcutter, _, _ = get_addon("BoxCutter")

        tools = get_tools_from_context(context)
        bcprefs = get_addon_prefs('BoxCutter')

        if not tools[boxcutter]['active']:
            bpy.ops.wm.tool_set_by_id(name=boxcutter)

        options = get_tool_options(context, boxcutter, 'bc.shape_draw')

        if options:
            options.mode = self.mode
            options.shape_type = self.shape_type

            bcprefs.behavior.set_origin = self.set_origin
            bcprefs.snap.enable = True

        return {'FINISHED'}

class ToggleAnnotation(bpy.types.Operator):
    bl_idname = "machin3.toggle_annotation"
    bl_label = "MACHIN3: Toggle Annotation"
    bl_description = "Toggle Annotation Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_annotation_layer

    def execute(self, context):
        data = context.annotation_data
        is_visible = any(not layer.hide for layer in data.layers)

        if is_visible:
            vis = {}

            for layer in data.layers:
                vis[layer.info] = layer.hide

                layer.hide = True

            context.scene.M3['annotation_visibility'] = vis

        else:
            vis = context.scene.M3.get('annotation_visibility')

            for layer in data.layers:
                layer.hide = vis[layer.info] if vis and layer.info in vis else False

        return {'FINISHED'}

class SurfaceDraw(bpy.types.Operator):
    bl_idname = "machin3.surface_draw"
    bl_label = "MACHIN3: Surface Draw"
    bl_description = "Surface Draw, create parented, empty GreasePencil object and enter DRAW mode.\nSHIFT: Select the Line tool."
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        bpy.ops.object.mode_set(mode='OBJECT')

        scene = context.scene
        ts = scene.tool_settings
        mcol = context.collection
        view = context.space_data
        active = context.active_object

        existing_gps = [obj for obj in active.children if obj.type == "GPENCIL"]

        if existing_gps:
            gp = existing_gps[0]

        else:
            name = f"{active.name}_SurfaceDrawing"
            gp = bpy.data.objects.new(name, bpy.data.grease_pencils.new(name))

            mcol.objects.link(gp)

            gp.matrix_world = active.matrix_world
            parent(gp, active)

        update_local_view(view, [(gp, True)])

        layer = gp.data.layers.new(name="SurfaceLayer")
        layer.blend_mode = 'MULTIPLY'

        if not layer.frames:
            layer.frames.new(0)

        context.view_layer.objects.active = gp
        active.select_set(False)
        gp.select_set(True)

        gp.color = (0, 0, 0, 1)

        blacks = [mat for mat in bpy.data.materials if mat.name == 'Black' and mat.is_grease_pencil]
        mat = blacks[0] if blacks else bpy.data.materials.new(name='Black')

        bpy.data.materials.create_gpencil_data(mat)
        gp.data.materials.append(mat)

        bpy.ops.object.mode_set(mode='PAINT_GPENCIL')

        ts.gpencil_stroke_placement_view3d = 'SURFACE'

        gp.data.zdepth_offset = 0.01

        ts.gpencil_paint.brush.gpencil_settings.pen_strength = 1

        if not view.show_region_toolbar:
            view.show_region_toolbar = True

        opacity = gp.grease_pencil_modifiers.new(name="Opacity", type="GP_OPACITY")
        opacity.show_expanded = False
        thickness = gp.grease_pencil_modifiers.new(name="Thickness", type="GP_THICK")
        thickness.show_expanded = False

        if event.shift:
            bpy.ops.wm.tool_set_by_id(name="builtin.line")

        else:
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")

        return {'FINISHED'}

class ShrinkwrapGreasePencil(bpy.types.Operator):
    bl_idname = "machin3.shrinkwrap_grease_pencil"
    bl_label = "MACHIN3: ShrinkWrap Grease Pencil"
    bl_description = "Shrinkwrap current Grease Pencil Layer to closest mesh surface based on Surface Offset value"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        if active and active.type == 'GPENCIL':
            return active.data.layers.active

    def execute(self, context):
        dg = context.evaluated_depsgraph_get()

        gp = context.active_object
        mx = gp.matrix_world
        offset = gp.data.zdepth_offset

        layer = gp.data.layers.active
        frame = layer.active_frame

        for stroke in frame.strokes:
            for idx, point in enumerate(stroke.points):
                closest, _, co, no, _, _ = get_closest(mx @ point.co, depsgraph=dg, debug=False)

                if closest:
                    point.co = mx.inverted_safe() @ (co + no * offset)

        return {'FINISHED'}
