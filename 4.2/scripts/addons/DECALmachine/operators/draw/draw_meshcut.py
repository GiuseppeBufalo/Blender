import bpy
from bpy.props import FloatProperty, BoolProperty, IntProperty
from ... utils.draw import draw_line
from ... colors import orange
from ... utils.ui import init_timer_modal, set_countdown, get_timer_progress

class DrawMeshCut(bpy.types.Operator):
    bl_idname = "machin3.draw_meshcut"
    bl_label = "MACHIN3: Draw MeshCut"

    time: FloatProperty(name="Time (s)", default=1)
    alpha: FloatProperty(name="Alpha", default=1, min=0.1, max=1)
    def draw_VIEW3D(self, context):
        alpha = get_timer_progress(self) * self.alpha

        for mx, coords in self.cuts:
            draw_line(coords, mx=mx, color=orange, width=3, alpha=alpha)

    def modal(self, context, event):
        context.area.tag_redraw()

        if self.countdown < 0:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        context.window_manager.event_timer_remove(self.TIMER)
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

    def execute(self, context):
        from .. cut_panel import draw_cuts

        self.cuts = draw_cuts

        init_timer_modal(self)

        self.area = context.area
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (context, ), 'WINDOW', 'POST_VIEW')
        self.TIMER = context.window_manager.event_timer_add(0.1, window=context.window)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
