import bpy
from bpy.props import FloatProperty, BoolProperty, IntProperty
from ... utils.draw import draw_line
from ... colors import orange


class DrawMeshCut(bpy.types.Operator):
    bl_idname = "machin3.draw_meshcut"
    bl_label = "MACHIN3: Draw MeshCut"

    countdown: FloatProperty(name="Countdown (s)", default=1)

    alpha: FloatProperty(name="Alpha", default=1, min=0.1, max=1)

    def draw_VIEW3D(self, args):
        alpha = self.countdown / self.time * self.alpha

        for mx, coords in self.cuts:
            draw_line(coords, mx=mx, color=orange, width=3, alpha=alpha)

    def modal(self, context, event):
        context.area.tag_redraw()


        if self.countdown < 0:

            context.window_manager.event_timer_remove(self.TIMER)

            bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')
            return {'FINISHED'}


        if event.type == 'TIMER':
            self.countdown -= 0.1

        return {'PASS_THROUGH'}

    def execute(self, context):

        from .. cut_panel import draw_cuts

        self.cuts = draw_cuts

        args = (self, context)
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (args, ), 'WINDOW', 'POST_VIEW')

        self.TIMER = context.window_manager.event_timer_add(0.1, window=context.window)

        self.time = self.countdown

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
