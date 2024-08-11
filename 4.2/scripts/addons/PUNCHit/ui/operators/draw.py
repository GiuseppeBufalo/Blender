import bpy
from bpy.props import FloatProperty, StringProperty, FloatVectorProperty
from ... utils.draw import draw_label, draw_init
from ... utils.ui import init_timer_modal, set_countdown, get_timer_progress

class DrawLabels(bpy.types.Operator):
    bl_idname = "machin3.draw_punchit_labels"
    bl_label = "MACHIN3: Draw Labels"
    bl_description = ""
    bl_options = {'INTERNAL'}

    text: StringProperty(name="Text to draw the HUD", default='Text')
    text2: StringProperty(name="Second Text to draw the HUD", default='')
    text3: StringProperty(name="Third Text to draw the HUD", default='')
    coords: FloatVectorProperty(name='Screen Coordinates', size=2, default=(100, 100))
    color: FloatVectorProperty(name='Text Color', size=3, default=(1, 1, 1))
    color2: FloatVectorProperty(name='Text2 Color', size=3, default=(1, 1, 1))
    color3: FloatVectorProperty(name='Text3 Color', size=3, default=(1, 1, 1))
    alpha: FloatProperty(name="Text Alpha", default=0.5, min=0.1, max=1)
    alpha2: FloatProperty(name="Text2 Alpha", default=0.5, min=0.1, max=1)
    alpha3: FloatProperty(name="Text3 Alpha", default=0.5, min=0.1, max=1)
    time: FloatProperty(name="", default=1, min=0.1)
    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'VIEW_3D'

    def draw_HUD(self, context):
        if context.area == self.area:
            progress = get_timer_progress(self)
            alpha = progress * self.alpha
            alpha2 = progress * self.alpha2
            alpha3 = progress * self.alpha3

            draw_init(self)

            draw_label(context, title=self.text, coords=self.coords, center=True, color=self.color, alpha=alpha)

            if self.text2:
                self.offset += 18
                draw_label(context, title=self.text2, coords=self.coords, offset=self.offset, center=True, color=self.color2, alpha=alpha2)

            if self.text3:
                self.offset += 18
                draw_label(context, title=self.text3, coords=self.coords, offset=self.offset, center=True, color=self.color3, alpha=alpha3)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        else:
            self.finish(context)
            return {'FINISHED'}

        if self.countdown < 0:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        context.window_manager.event_timer_remove(self.TIMER)
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')

    def execute(self, context):
        init_timer_modal(self)

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')
        self.TIMER = context.window_manager.event_timer_add(0.1, window=context.window)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
