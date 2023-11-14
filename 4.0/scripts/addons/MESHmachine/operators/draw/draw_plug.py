import bpy
from bpy.props import FloatProperty
from ... utils.mesh import get_coords
from ... utils.draw import draw_lines
from ... utils.registration import get_prefs


class DrawPlug(bpy.types.Operator):
    bl_idname = "machin3.draw_plug"
    bl_label = "MACHIN3: Draw Plug"

    time: FloatProperty(name="Time (s)", default=1)
    steps: FloatProperty(name="Steps", default=0.05)

    alpha: FloatProperty(name="Alpha", default=0.3, min=0.1, max=1)

    def draw_VIEW3D(self, args):
        alpha = (self.countdown / (self.time * get_prefs().modal_hud_timeout)) * self.alpha

        draw_lines(self.coords, indices=self.indices, alpha=alpha)


    def modal(self, context, event):
        context.area.tag_redraw()


        if self.countdown < 0:

            context.window_manager.event_timer_remove(self.TIMER)

            bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')
            return {'FINISHED'}


        if event.type == 'TIMER':
            self.countdown -= self.steps

        return {'PASS_THROUGH'}

    def execute(self, context):

        active = context.active_object
        mx = active.matrix_world

        from .. plug import vert_ids

        self.indices = vert_ids
        self.coords = get_coords(active.data, mx=mx)

        args = (self, context)
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (args, ), 'WINDOW', 'POST_VIEW')

        self.TIMER = context.window_manager.event_timer_add(self.steps, window=context.window)

        self.countdown = self.time * get_prefs().modal_hud_timeout

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
