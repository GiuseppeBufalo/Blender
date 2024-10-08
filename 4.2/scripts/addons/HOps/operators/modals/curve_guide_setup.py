import bpy
from mathutils import Vector
from bpy.types import Operator
from bpy.props import IntProperty, FloatProperty
from ... utils.blender_ui import get_dpi, get_dpi_factor
from ... graphics.drawing2d import draw_text, set_drawing_dpi
from ... utility import addon
from . import infobar

deformtypes = ["Deform", "Twist", "Shear", "Scale", "Stretch"]


class HOPS_OT_CurveGuide(Operator):
    bl_idname = "mesh.curve_guide"
    bl_label = "Curve Guide"
    bl_description = "Preconfiguration for Mira Tools Curve Guide"
    bl_options = {"REGISTER", "GRAB_CURSOR", "BLOCKING"}

    first_mouse_x : IntProperty()
    first_value : FloatProperty()
    second_value : IntProperty()
    precision : IntProperty(default=50)

    def modal(self, context, event):
        curve = context.scene.mi_curguide_settings
        # offset_x = event.mouse_region_x - self.last_mouse_x

        if event.type == 'WHEELUPMOUSE':
            if curve.points_number < 12:
                curve.points_number += 1

        if event.type == 'WHEELDOWNMOUSE':
            if curve.points_number > 2:
                curve.points_number -= 1

        if event.mouse_region_x % self.precision == 0:
            if event.mouse_region_x > self.last_mouse_x:
                self.set_deformtype(curve)
            elif event.mouse_region_x < self.last_mouse_x:
                self.set_deformtype(curve, previous=True)

        if event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}:
            bpy.ops.mira.curve_guide('INVOKE_DEFAULT')
            infobar.remove(self)
            return {"FINISHED"}

        if event.type in {'RIGHTMOUSE', 'ESC', 'BACK_SPACE'}:
            infobar.remove(self)
            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_region_x
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.last_mouse_x = event.mouse_region_x
        self.start_mouse_position = Vector((event.mouse_region_x, event.mouse_region_y))

        # args = (context, )
        # self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, args, "WINDOW", "POST_PIXEL")
        context.window_manager.modal_handler_add(self)
        infobar.initiate(self)
        return {'RUNNING_MODAL'}

    def finish(self):
        # bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, "WINDOW")
        infobar.remove(self)
        return {"FINISHED"}

    def set_deformtype(self, curve, previous=False):
        currenttype = curve.deform_type
        currentidx = deformtypes.index(currenttype)

        if previous:
            if currenttype == deformtypes[0]:
                nexttype = deformtypes[-1]
            else:
                nexttype = deformtypes[currentidx + -1]
        else:
            if currenttype == deformtypes[-1]:
                nexttype = deformtypes[0]
            else:
                nexttype = deformtypes[currentidx + 1]

        curve.deform_type = nexttype
