import bpy
from bpy.props import FloatProperty
from mathutils import Vector
from ... utils.draw import  draw_mesh_wire, draw_label
from ... utils.ui import get_scale, init_timer_modal, set_countdown, get_timer_progress
from ... utils.registration import get_prefs
from ... colors import white, yellow

class DrawUnGroupable(bpy.types.Operator):
    bl_idname = "machin3.draw_ungroupable"
    bl_label = "MACHIN3: Draw Ungroupable"
    bl_options = {'INTERNAL'}

    time: FloatProperty(name="Time (s)", default=1)
    alpha: FloatProperty(name="Alpha", default=1, min=0.1, max=1)
    def draw_HUD(self, context):
        if context.area == self.area:
            scale = get_scale(context)
            alpha = get_timer_progress(self) * self.alpha

            for loc2d, _ in self.batches:
                draw_label(context, title="Ungroupable", coords=loc2d - Vector((0, 36 * scale)), color=yellow, alpha=alpha)
                draw_label(context, title="Object is parented", coords=loc2d - Vector((0, 54 * scale)), color=white, alpha=alpha / 2)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            alpha = get_timer_progress(self) * self.alpha * 0.5

            for _, batch in self.batches:
                draw_mesh_wire(batch, color=yellow, alpha=alpha)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        else:
            self.finish(context)
            return {'CANCELLED'}

        if self.countdown < 0:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        context.window_manager.event_timer_remove(self.TIMER)
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

    def execute(self, context):
        from .. group import ungroupable_batches
        self.batches = ungroupable_batches

        self.time = get_prefs().HUD_fade_group * 4
        init_timer_modal(self)

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (context, ), 'WINDOW', 'POST_VIEW')
        self.TIMER = context.window_manager.event_timer_add(0.01, window=context.window)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
