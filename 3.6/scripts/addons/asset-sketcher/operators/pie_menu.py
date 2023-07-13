import bpy
from bpy.types import Menu
from bpy.props import FloatProperty, IntProperty, BoolProperty, StringProperty, CollectionProperty, FloatVectorProperty, EnumProperty, IntVectorProperty


class ASSET_SKETCHER_OT_SetSketchMode(bpy.types.Operator):
    bl_idname = "asset_sketcher.set_sketch_mode"
    bl_label = "Set Sketch Mode"
    bl_description = ""
    bl_options = {"REGISTER"}

    mode: StringProperty(default="PAINT")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        wm = context.window_manager
        wm.asset_sketcher.sketch_mode = self.mode
        return {"FINISHED"}

class ASSET_SKETCHER_MT_menu(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Sketch Mode"
    bl_idname = "ASSET_SKETCHER_MT_menu"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):

        layout = self.layout
        pie = layout.menu_pie()
        pie.operator("asset_sketcher.set_sketch_mode",text="Paint", icon="BRUSH_DATA").mode = "PAINT"
        pie.operator("asset_sketcher.set_sketch_mode",text="Grid", icon="GRID").mode = "GRID"
        pie.operator("asset_sketcher.set_sketch_mode",text="Scale", icon="FULLSCREEN_ENTER").mode = "SCALE"
        pie.operator("asset_sketcher.set_sketch_mode",text="Line", icon="LINE_DATA").mode = "LINE"