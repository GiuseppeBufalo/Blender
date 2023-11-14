import bpy
from bpy.props import FloatProperty
from ... utils.mesh import get_coords
from ... utils.draw import draw_points
from ... utils.registration import get_prefs
from ... colors import normal, white


class DrawRealMirror(bpy.types.Operator):
    bl_idname = "machin3.draw_realmirror"
    bl_label = "MACHIN3: Draw RealMirror"

    time: FloatProperty(name="Time (s)", default=0.5)
    steps: FloatProperty(name="Steps", default=0.05)

    alpha: FloatProperty(name="Alpha", default=0.3, min=0.1, max=1)

    normal_offset = 0.002

    def draw_VIEW3D(self, args):
        alpha = (self.countdown / (self.time * get_prefs().modal_hud_timeout)) * self.alpha

        for coords, color in self.batches:
            draw_points(coords, color=color, alpha=alpha)

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
        from .. real_mirror import mirrored, custom_normals

        self.batches = []

        for obj, cn in zip(mirrored, custom_normals):
            offset = sum([d for d in obj.dimensions]) / 3 * self.normal_offset
            coords = get_coords(obj.data, mx=obj.matrix_world, offset=offset)
            color = normal if cn else white
            self.batches.append((coords, color))

        args = (self, context)
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (args, ), 'WINDOW', 'POST_VIEW')

        self.TIMER = context.window_manager.event_timer_add(self.steps, window=context.window)

        self.countdown = self.time * get_prefs().modal_hud_timeout

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
