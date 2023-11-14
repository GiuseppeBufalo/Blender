import bpy
from bpy.props import StringProperty
from ... utils.modifier import get_displace


class Set(bpy.types.Operator):
    bl_idname = "machin3.set_default_property"
    bl_label = "MACHIN3: Set Default Property"
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty(name="Mode", default="HEIGHT")

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.DM.isdecal and get_displace(context.active_object)

    @classmethod
    def description(cls, context, properties):
        if properties.mode == 'HEIGHT':
            return "Set Decal Height from selected Decal"

    def execute(self, context):
        dm = context.scene.DM

        if self.mode == 'HEIGHT':
            displace = get_displace(context.active_object)
            dm.height = displace.mid_level

        return {'FINISHED'}


class Reset(bpy.types.Operator):
    bl_idname = "machin3.reset_default_property"
    bl_label = "MACHIN3: Reset Default Property"
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty(name="Mode", default="SCALE")

    @classmethod
    def description(cls, context, properties):
        if properties.mode == 'SCALE':
            return "Reset Global Scale to 1"
        elif properties.mode == 'WIDTH':
            return "Reset Panel Width or to 0.04"
        elif properties.mode == 'HEIGHT':
            return "Reset Decal Height to 0.9999"
        elif properties.mode == 'OFFSET':
            return "Reset Offset to 0"
        elif properties.mode == 'PADDING':
            return "Reset Padding to 1"

    def execute(self, context):
        dm = context.scene.DM

        if self.mode == 'SCALE':
            dm.globalscale = 1

        elif self.mode == 'WIDTH':
            dm.panelwidth = 0.04

        elif self.mode == 'HEIGHT':
            dm.height = 0.9998

        elif self.mode == 'OFFSET':
            dm.create_infotext_offset = (0, 0)

        elif self.mode == 'PADDING':
            dm.create_infotext_padding = (1, 1)

        return {'FINISHED'}
