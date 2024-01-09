import bpy
import bmesh
import blf
import gpu
import os
import mathutils
import math
import addon_utils
import traceback
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    FloatVectorProperty,
    PointerProperty,
    CollectionProperty,
    EnumProperty,
)
from bpy_extras import view3d_utils
from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper
from . import utils
from . import objects
from . import ui
from . import textures

class QT_MT_Quick_Menu_Pie(bpy.types.Menu):
    bl_label = "QuickTexture"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        scale_x = 0.9
        scale_y = 0.9
        other = pie.column()
        other_menu = other.box().column()
        other_menu.scale_y = scale_y
        other_menu.scale_x = scale_x
        other_menu.label(text="Layers")
        other_menu.operator("object.quicktexture_box")
        other_menu.operator("object.quicktexture_view")
        other_menu.operator("object.quicktexture_uv")
        other_menu.operator("object.quicktexture_triplanar")
        other = pie.column()
        other_menu = other.box().column()
        other_menu.label(text="Masks")
        other_menu.operator("qt.texturemask_qt")
        other_menu.operator("qt.edgesmask_qt")
        other_menu.operator("qt.dirtmask_qt")
        other_menu.operator("qt.depthmask_qt")
        other_menu.operator("qt.vertexmask_qt")
        other_menu.operator("qt.heightmask_qt")
        other_menu.operator("qt.normalmask_qt")
        other_menu.operator("qt.randomizeperobject_qt")
        other_menu.operator("qt.variationmask_qt")
        other_menu.operator("qt.detiling_qt")
        other_menu.operator("qt.smudge_qt")
        other_menu.operator("qt.replacemaps")
        other = pie.column()
        other_menu = other.box().column()
        other_menu.operator("object.quicktexturedecal")
        other_menu.operator("qt.paintover_qt")
        other_menu.operator("qt.apply_paintover_qt")
        other_menu.operator("object.photomodelingplane")
        other_menu.operator("object.photomodelingbox")
        other_menu.operator("object.photomodelingapply")
        other_menu.operator("qt.makeunique")
        other_menu.operator("qt.resetmaterial")

class QT_OT_Quick_Menu_Pie_call(bpy.types.Operator):
    bl_idname = "object.quicktexturepie"
    bl_label = "Pie Menu"
    bl_description = "QuickTexture Pie Menu"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="QT_MT_Quick_Menu_Pie")
        return {"FINISHED"}

class MyPropertiesQT(bpy.types.PropertyGroup):
    startup_prefs: BoolProperty(name="startup_prefs", description="startup_prefs", default=False)

    running_qt: IntProperty(name="running_qt", description="running_qt", default=0)

    # hotkeys
    hk_qt_quicktexture: StringProperty(name="name", description="name", default="")
    hk_qt_quicktexture_ctrl: BoolProperty(name="ctrl", description="ctrl", default=False)
    hk_qt_quicktexture_shift: BoolProperty(name="shift", description="shift", default=False)
    hk_qt_quicktexture_alt: BoolProperty(name="alt", description="alt", default=False)
    
    hk_qt_quicktexture_decal: StringProperty(name="name", description="name", default="")
    hk_qt_quicktexture_decal_ctrl: BoolProperty(name="ctrl", description="ctrl", default=False)
    hk_qt_quicktexture_decal_shift: BoolProperty(name="shift", description="shift", default=False)
    hk_qt_quicktexture_decal_alt: BoolProperty(name="alt", description="alt", default=False)

    hk_qt_quicktexture_paintover: StringProperty(name="name", description="name", default="")
    hk_qt_quicktexture_paintover_ctrl: BoolProperty(name="ctrl", description="ctrl", default=False)
    hk_qt_quicktexture_paintover_shift: BoolProperty(name="shift", description="shift", default=False)
    hk_qt_quicktexture_paintover_alt: BoolProperty(name="alt", description="alt", default=False)
    
    # settings
    render_engine: BoolProperty(name="render_engine", description="render_engine", default=0)
    filepath: StringProperty(name="filepath", description="filepath", default="none")
    uv_mode: EnumProperty(
        items = [
            ('UV','UV','','',0), 
            ('Triplanar','Triplanar','','',1),
            ('View','View','','',2),
            ('Procedural Box','Procedural Box','','',3),
        ],
        name = "UV Mode",
        default = 'Procedural Box')
    multilayer: BoolProperty(name="MultiLayer", description="Create Multilayer QuickTexture with automatic Dirt and Edges Masks", default=False)
    save_original_mat: BoolProperty(
        name="save_original_mat",
        description="Save a copy of the original pre Bake material in the scene after Baking",
        default=1,
    )
    makeunique: BoolProperty(name="makeunique",description="Make the material unique after copying",default=1,)
    alpha_type: BoolProperty(name="alpha_type",description="Alpha Type",default=0)
    active_map: IntProperty(name="active_map", description="active_map", default=1)
    active_layer: IntProperty(name="active_layer", description="active_layer", default=1)
    total_layers: IntProperty(name="total_layers", description="total_layers", default=1)
    active_material: IntProperty(name="active_material", description="Material Index", default=0, min=0, max=4)
    total_materials: IntProperty(name="total_materials", description="Total Materials", default=0, min=0, max=4)

    # decal
    decal_coord: FloatVectorProperty(name="Decal Coord", description="Decal Coord", default=(0, 0, 0), subtype="XYZ")
    res: IntProperty(
        name="Decal Resolution",
        description="Decal Resolution",
        default=1,
        min=0,
        max=10,
    )
    offset: FloatProperty(
        name="Decal Offset",
        description="Decal Offset",
        default=0.01,
        min=0.0001,
        max=10,
    )
    paintover_res: IntProperty(
        name="Paintover Resolution",
        description="Paintover Resolution",
        default=4,
        min=1,
        max=10,
    )
    paintover_offset: FloatProperty(
        name="Paintover Offset",
        description="Paintover Offset",
        default=0.003,
        min=0.0001,
        max=10,
    )
    paintover: IntProperty(
        name="Paintover Resolution",
        description="Paintover Resolution is a Multiplier on your current Viewport Size",
        default=2,
        min=1,
        max=4,
    )
    overscan: FloatProperty(
        name="Paintover Overscan",
        description="Adjust this value if your object is not being entirely covered by the Paintover",
        default=1.1,
        min=1,
        max=2,
    )

    # baking
    preview_mat: PointerProperty(type=bpy.types.Material)
    edges_radius_preview: FloatProperty(
        name="edges_radius_preview",
        description="Edges Radius Preview",
        default=0.3,
        min=0.001,
        max=10,
        update = utils.update_edges_radius
    )
    dirt_radius_preview: FloatProperty(
        name="dirt_radius_preview",
        description="Dirt Radius Preview",
        default=0.3,
        min=0.001,
        max=10,
        update = utils.update_dirt_radius
    )
    in_bake_preview: BoolProperty(name="in_bake_preview", description="in_bake_preview", default=0)
    bakepath: StringProperty(name="bakepath", description="Bake Output Directory Path", default="")
    bakename: StringProperty(name="bakename", description="Baked Texture Name", default="QT_Bake")
    bakeres: IntProperty(name="bakeres", description="Bake Resolution", default=1024, min=1, max=8192)
    samples: IntProperty(name="samples", description="Cycles Bake Samples", default=64, min=1, max=10000) 

class QT_PT_panel(bpy.types.Panel):
    bl_label = "QUICKTEXTURE"
    bl_category = "QuickTools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        if not bpy.context.window_manager.my_toolqt.running_qt:
            bpy.context.window_manager.my_toolqt.running_qt = 1
            wm = bpy.context.window_manager
            kc = wm.keyconfigs.user
            for m in kc.keymaps:
                for k in m.keymap_items:
                    if "quicktexture" in k.idname:
                        s = k.idname
                        id = s.split(".")[1]
                        if id == 'quicktexture':
                            bpy.context.window_manager.my_toolqt.hk_qt_quicktexture = k.type
                            if k.ctrl:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_ctrl = k.ctrl
                            if k.shift:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_shift = k.shift
                            if k.alt:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_alt = k.alt
                        if id == 'quicktexturedecal':
                            bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal = k.type
                            if k.ctrl:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal_ctrl = k.ctrl
                            if k.shift:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal_shift = k.shift
                            if k.alt:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal_alt = k.alt
                        if id == 'quicktexturepaintover':
                            bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover = k.type
                            if k.ctrl:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover_ctrl = k.ctrl
                            if k.shift:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover_shift = k.shift
                            if k.alt:
                                bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover_alt = k.alt
                                
        box = layout.box()
        row = box.row()
        hotkey = "["
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_ctrl:
            hotkey += ("Ctrl ")
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_shift:
            hotkey += ("Shift ")
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_alt:
            hotkey += ("Alt ")
        hotkey += (bpy.context.window_manager.my_toolqt.hk_qt_quicktexture)
        hotkey += ("] QuickTexture")
        row.label(text=hotkey)
        row = box.row()
        row.label(text="[Ctrl D] Quick Menu")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "uv_mode", text="Mode")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "multilayer", text="Multilayer")

        box = layout.box()
        row = box.row()
        hotkey = "["
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal_ctrl:
            hotkey += ("Ctrl ")
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal_shift:
            hotkey += ("Shift ")
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal_alt:
            hotkey += ("Alt ")
        hotkey += (bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_decal)
        hotkey += ("] QuickDecal")
        row.label(text=hotkey)
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "res", text="Decal Resolution")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "offset", text="Decal Offset")
        row = box.row()
        box = layout.box()
        row = box.row()
        hotkey = "["
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover_ctrl:
            hotkey += ("Ctrl ")
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover_shift:
            hotkey += ("Shift ")
        if bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover_alt:
            hotkey += ("Alt ")
        hotkey += (bpy.context.window_manager.my_toolqt.hk_qt_quicktexture_paintover)
        hotkey += ("] QuickPaintover")
        row.label(text=hotkey)
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "paintover_res", text="Paintover Resolution")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "paintover_offset", text="Paintover Offset")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "paintover", text="Paintover Tex Resolution")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "overscan", text="Paintover Overscan")
        row = box.row()
        row.operator(QT_OT_apply_paintover_qt.bl_idname)
        
        box = layout.box()
        row = box.row()
        row.label(text="EDIT")
        row = box.row()
        row.label(text="[G] Move")
        row = box.row()
        row.label(text="[S] Scale")
        row = box.row()
        row.label(text="[R] Rotate ")
        row = box.row()
        row.label(text="[Shift S] Stretch X")
        row = box.row()
        row.label(text="[Alt S] Stretch Y")
        row = box.row()
        row.label(text="[BRACKETS] Rotate 90 Degrees")
        row = box.row()
        row.label(text="[P] Reproject View")
        row = box.row()
        row.label(text="[Tab] Preview Final Texture")
        row = box.row()
        row.label(text="[K] Reset All Settings")
        box = layout.box()
        row = box.row()
        row.label(text="LAYERS")
        row = box.row()
        row.label(text="[Ctrl B] Procedural Box")
        row = box.row()
        row.label(text="[Ctrl V] View")
        row = box.row()
        row.label(text="[Shift T] Triplanar")
        row = box.row()
        row.label(text="[Q] Previous")
        row = box.row()
        row.label(text="[W] Next")
        row = box.row()
        row.label(text="[Shift D] Duplicate")
        row = box.row()
        row.label(text="[Del] Delete")
        row = box.row()
        row.label(text="[Ctrl Num] Switch Material")
        box = layout.box()
        row = box.row()
        row.label(text="MAPS")
        row = box.row()
        row.label(text="[1] Combined")
        row = box.row()
        row.label(text="[2] Roughness")
        row = box.row()
        row.label(text="[3] Bump")
        row = box.row()
        row.label(text="[4] Mask")
        row = box.row()
        row.label(text="[5] Alpha")
        row = box.row()
        row.label(text="[6] UV")
        row = box.row()
        row.label(text="[7] Variation")
        row = box.row()
        row.label(text="[8] Randomization Per Object")
        row = box.row()
        row.label(text="[9] Metal")
        row = box.row()
        row.label(text="[0] Displacement")
        row = box.row()
        row.label(text="[Ctrl I] Invert Map")
        row = box.row()
        row.label(text="[Ctrl R] Replace Map")
        box = layout.box()
        row = box.row()
        row.label(text="MASKS")
        row = box.row()
        row.label(text="[Ctrl M] Texture Mask")
        row = box.row()
        row.label(text="[Ctrl C] Edge Mask")
        row = box.row()
        row.label(text="[Ctrl A] Dirt Mask")
        row = box.row()
        row.label(text="[Ctrl H] Height Mask")
        row = box.row()
        row.label(text="[Ctrl N] Normal Mask")
        row = box.row()
        row.label(text="[Alt H] Depth Mask")
        row = box.row()
        row.label(text="[Alt V] Variation")
        row = box.row()
        row.label(text="[Shift V] Vertex Color")
        row = box.row()
        row.label(text="[Ctrl O] Randomize Per Object")
        row = box.row()
        row.label(text="[Shift U] De-Tiling")
        row = box.row()
        row.label(text="[Shift A] Smudge UVs")
        row = box.row()
        row.label(text="[Backspace] Delete")
        box = layout.box()
        row = box.row()
        row.operator(QT_OT_makeunique.bl_idname)
        row = box.row()
        row.operator(QT_OT_copymats.bl_idname)
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "makeunique",
            text="Unlink Material After Copy",
        )
        row = box.row()
        row.operator(QT_OT_resetmaterial.bl_idname)
        box = layout.box()
        row = box.row()
        row.label(text="BAKING")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "bakename", text="Name")
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "bakepath",
            text="Directory",
        )
        row.operator(BakeFileSelector.bl_idname, icon="FILE_FOLDER", text="")
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "bakeres",
            text="Bake Resolution",
            slider=1,
        )
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "samples",
            text="Bake Samples",
            slider=1,
        )
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "save_original_mat",
            text="Save Original Mat",
            slider=False,
        )
        row = box.row()
        row.operator(bakeTextures.bl_idname)
        box = layout.box()
        row = box.row()
        row.label(text="Dirt and Edges uses CYCLES Render Engine")
        row = box.row()
        row.operator(previewTextures.bl_idname)
        if bpy.context.window_manager.my_toolqt.in_bake_preview:
            row = box.row()
            row.operator(bakePreviewTextures.bl_idname)
            row = box.row()
            row.prop(
                bpy.context.window_manager.my_toolqt,
                "edges_radius_preview",
                text="Edges Radius",
                slider=True,
            )
            row.prop(
                bpy.context.window_manager.my_toolqt,
                "dirt_radius_preview",
                text="Dirt Radius",
                slider=True,
            )

class BakeFileSelector(bpy.types.Operator, ExportHelper):
    bl_idname = "wm.bakefileselector"
    bl_label = "Directory"
    
    filename_ext = ""

    def execute(self, context):
        fdir = self.properties.filepath
        dirpath = os.path.dirname(fdir)
        bpy.context.window_manager.my_toolqt.bakepath = dirpath
        return {"FINISHED"}

def draw_quickTexture(self, context):
    if context.area != self.init_area:
        return

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(1.0)

    if bpy.context.window_manager.my_toolqt.running_qt and self.shader:
        addon = "QuickTexture"
        addon_width = blf.dimensions(0, addon)[0]
        ui.draw_text(addon, self.regX, self.regY, 1, 2, -addon_width, 'Center', 0)
        
        if self.blend:
            text_hotkey = "[G]"
            command = "Height"
            val = str(round(self.blend.inputs[2].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 7, -text_width, 'Right', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 7, -text_width + text_hotkey_width, 'Right', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_move, 7, -text_value_width, 'Right', 1)

            text_hotkey = "[S]"
            command = "Scale"
            val = str(round(self.blend.inputs[3].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 6, -text_width, 'Right', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 6, -text_width + text_hotkey_width, 'Right', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_scale, 6, -text_value_width, 'Right', 1)

            text_hotkey = "[R]"
            command = "Roughness"
            val = str(round(self.blend.inputs[5].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, -text_width, 'Right', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 5, -text_width + text_hotkey_width, 'Right', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_rotate, 5, -text_value_width, 'Right', 1)

            text_hotkey = "[X]"
            command = "Exponent"
            val = str(round(self.blend.inputs[8].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
            ui.draw_text(val, self.regX, self.regY, self.x, 4, -text_value_width, 'Right', 1)

            text_hotkey = "[H]"
            command = "Detail"
            val = str(round(self.blend.inputs[4].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
            ui.draw_text(val, self.regX, self.regY, self.h, 3, -text_value_width, 'Right', 1)

            text_hotkey = "[V]"
            command = "Distortion"
            val = str(round(self.blend.inputs[6].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
            ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
            
            text_hotkey = "[C]"
            command = "Contrast"
            val = str(round(self.blend.inputs[7].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
            ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

        else:
            active_map = "Combined"
            if bpy.context.window_manager.my_toolqt.active_map == 1:
                active_map = "Combined"
            elif bpy.context.window_manager.my_toolqt.active_map == 2:
                active_map = "Roughness"
            elif bpy.context.window_manager.my_toolqt.active_map == 3:
                active_map = "Bump"
            elif bpy.context.window_manager.my_toolqt.active_map == 4:
                active_map = "Mask"
            elif bpy.context.window_manager.my_toolqt.active_map == 5:
                active_map = "Alpha"
            elif bpy.context.window_manager.my_toolqt.active_map == 6:
                active_map = "UV"
            elif bpy.context.window_manager.my_toolqt.active_map == 7:
                active_map = "Variation"
            elif bpy.context.window_manager.my_toolqt.active_map == 8:
                active_map = "Randomization"
            elif bpy.context.window_manager.my_toolqt.active_map == 9:
                active_map = "Metal"
            elif bpy.context.window_manager.my_toolqt.active_map == 0:
                active_map = "Displacement"

            text_hotkey = "Active Material:"
            command = str(bpy.context.window_manager.my_toolqt.active_material+1) + " / " + str(bpy.context.window_manager.my_toolqt.total_materials)
            text_command = command
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_width = text_hotkey_width + text_command_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width/2, 'Bottom', 1)
            ui.draw_text(text_command, self.regX, self.regY, 1, 1, -text_width/2 + text_hotkey_width, 'Bottom', 1)
                
            text_hotkey = "Active Layer: "
            command = str(bpy.context.window_manager.my_toolqt.active_layer) + " / " + str(bpy.context.window_manager.my_toolqt.total_layers)
            text_command = command
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_width = text_hotkey_width + text_command_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width/2, 'Bottom', 1)
            ui.draw_text(text_command, self.regX, self.regY, 1, 2, -text_width/2 + text_hotkey_width, 'Bottom', 1)
            
            text_hotkey = "Active Map: "
            command = active_map
            text_command = command
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_width = text_hotkey_width + text_command_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width/2, 'Bottom', 1)
            ui.draw_text(text_command, self.regX, self.regY, 1, 3, -text_width/2 + text_hotkey_width, 'Bottom', 1)

            activemask = "None"
            if self.smudge:
                activemask = "Smudge"
            if self.variation:
                activemask = "Variation"
            if self.detiling:
                activemask = "Detiling"
            if self.randcolor and self.randrough:
                activemask = "Random"
            if self.texture_mask:
                activemask = "Texture"
            if self.edge_mask:
                activemask = "Edge"
            if self.dirt_mask:
                activemask = "Dirt"
            if self.depth_mask:
                activemask = "Depth"
            if self.height_mask:
                activemask = "Height"
            if self.normal_mask:
                activemask = "Normal"
            text_hotkey = "Layer Mask: "
            command = activemask
            text_command = " " + command
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_width = text_hotkey_width + text_command_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width/2, 'Bottom', 1)
            ui.draw_text(text_command, self.regX, self.regY, 1, 4, -text_width/2 + text_hotkey_width, 'Bottom', 1)
    
            # combined
            if bpy.context.window_manager.my_toolqt.active_map == 1:
                text_hotkey = "[H]"
                command = "Hue"
                val = str(round(self.diffuse_hue_sat.inputs[0].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.h, 4, -text_value_width, 'Right', 1)

                text_hotkey = "[V]"
                command = "Value"
                val = str(round(self.diffuse_hue_sat.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.v, 3, -text_value_width, 'Right', 1)

                text_hotkey = "[C]"
                command = "Contrast"
                val = str(round(self.diffuse_bright_contrast.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.c, 2, -text_value_width, 'Right', 1)

                text_hotkey = "[X]"
                command = "Saturation"
                val = str(round(self.diffuse_hue_sat.inputs[1].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.x, 1, -text_value_width, 'Right', 1)

            # roughness
            elif bpy.context.window_manager.my_toolqt.active_map == 2:
                text_hotkey = "[V]"
                command = "Value"
                val = str(round(self.rough_hue_sat.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                
                text_hotkey = "[C]"
                command = "Contrast"
                val = str(round(self.rough_bright_contrast.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)
                
            # bump
            elif bpy.context.window_manager.my_toolqt.active_map == 3:
                text_hotkey = "[V]"
                command = "Value"
                val = str(round(self.bump_hue_sat.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                
                text_hotkey = "[C]"
                command = "Contrast"
                val = str(round(self.bump_bright_contrast.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

            # texture mask
            elif bpy.context.window_manager.my_toolqt.active_map == 4:
                if self.texture_mask:
                    text_hotkey = "[V]"
                    command = "Value"
                    val = str(round(self.texture_mask.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                    
                    text_hotkey = "[C]"
                    command = "Contrast"
                    val = str(round(self.texture_mask.inputs[5].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

                elif self.edge_mask:
                    text_hotkey = "[G]"
                    command = "Detail"
                    val = str(round(self.edge_mask.inputs[1].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 7, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 7, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_move, 7, -text_value_width, 'Right', 1)

                    text_hotkey = "[S]"
                    command = "Scale"
                    val = str(round(self.edge_mask.inputs[0].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 6, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 6, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_scale, 6, -text_value_width, 'Right', 1)

                    text_hotkey = "[R]"
                    command = "Roughness"
                    val = str(round(self.edge_mask.inputs[2].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 5, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_rotate, 5, -text_value_width, 'Right', 1)

                    text_hotkey = "[X]"
                    command = "Distortion"
                    val = str(round(self.edge_mask.inputs[3].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.x, 4, -text_value_width, 'Right', 1)

                    text_hotkey = "[H]"
                    command = "Radius"
                    val = str(round(self.edge_mask.inputs[5].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.h, 3, -text_value_width, 'Right', 1)

                    text_hotkey = "[V]"
                    command = "Strength"
                    val = str(round(self.edge_mask.inputs[6].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                    
                    text_hotkey = "[C]"
                    command = "Contrast"
                    val = str(round(self.edge_mask.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

                elif self.dirt_mask:
                    text_hotkey = "[G]"
                    command = "Detail"
                    val = str(round(self.dirt_mask.inputs[1].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 7, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 7, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_move, 7, -text_value_width, 'Right', 1)

                    text_hotkey = "[S]"
                    command = "Scale"
                    val = str(round(self.dirt_mask.inputs[0].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 6, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 6, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_scale, 6, -text_value_width, 'Right', 1)

                    text_hotkey = "[R]"
                    command = "Roughness"
                    val = str(round(self.dirt_mask.inputs[2].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 5, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_rotate, 5, -text_value_width, 'Right', 1)

                    text_hotkey = "[X]"
                    command = "Distortion"
                    val = str(round(self.dirt_mask.inputs[3].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.x, 4, -text_value_width, 'Right', 1)

                    text_hotkey = "[H]"
                    command = "Distance"
                    val = str(round(self.dirt_mask.inputs[5].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.h, 3, -text_value_width, 'Right', 1)

                    text_hotkey = "[V]"
                    command = "Strength"
                    val = str(round(self.dirt_mask.inputs[6].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                    
                    text_hotkey = "[C]"
                    command = "Contrast"
                    val = str(round(self.dirt_mask.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

                elif self.height_mask:
                    text_hotkey = "[G]"
                    command = "Detail"
                    val = str(round(self.height_mask.inputs[2].default_value[2], 2))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 7, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 7, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_move, 7, -text_value_width, 'Right', 1)

                    text_hotkey = "[H]"
                    command = "Height"
                    val = str(round(self.height_mask.inputs[0].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 6, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 6, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.h, 6, -text_value_width, 'Right', 1)

                    text_hotkey = "[S]"
                    command = "Scale"
                    val = str(round(self.height_mask.inputs[1].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 5, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_scale, 5, -text_value_width, 'Right', 1)

                    text_hotkey = "[R]"
                    command = "Roughness"
                    val = str(round(self.height_mask.inputs[2].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_rotate, 4, -text_value_width, 'Right', 1)

                    text_hotkey = "[X]"
                    command = "Distortion"
                    val = str(round(self.height_mask.inputs[3].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.x, 3, -text_value_width, 'Right', 1)

                    text_hotkey = "[V]"
                    command = "Exponent"
                    val = str(round(self.height_mask.inputs[6].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                    
                    text_hotkey = "[C]"
                    command = "Contrast"
                    val = str(round(self.height_mask.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

                elif self.normal_mask:
                    text_hotkey = "[G]"
                    command = "Detail"
                    val = str(round(self.normal_mask.inputs[1].default_value, 2))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 6, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 6, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_move, 6, -text_value_width, 'Right', 1)

                    text_hotkey = "[S]"
                    command = "Scale"
                    val = str(round(self.normal_mask.inputs[0].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 5, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_scale, 5, -text_value_width, 'Right', 1)

                    text_hotkey = "[R]"
                    command = "Roughness"
                    val = str(round(self.normal_mask.inputs[2].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.edit_rotate, 4, -text_value_width, 'Right', 1)

                    text_hotkey = "[X]"
                    command = "Distortion"
                    val = str(round(self.normal_mask.inputs[3].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.x, 3, -text_value_width, 'Right', 1)

                    text_hotkey = "[V]"
                    command = "Exponent"
                    val = str(round(self.normal_mask.inputs[6].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                    
                    text_hotkey = "[C]"
                    command = "Contrast"
                    val = str(round(self.normal_mask.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

                if self.depth_mask:
                    text_hotkey = "[V]"
                    command = "Value"
                    val = str(round(self.depth_mask.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                    
                    text_hotkey = "[C]"
                    command = "Contrast"
                    val = str(round(self.depth_mask.inputs[6].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

            # alpha
            elif bpy.context.window_manager.my_toolqt.active_map == 5:
                text_hotkey = "[V]"
                command = "Value"
                val = str(round(self.alpha_hue_sat.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                
                text_hotkey = "[C]"
                command = "Contrast"
                val = str(round(self.alpha_bright_contrast.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

            # uv
            elif bpy.context.window_manager.my_toolqt.active_map == 6:
                if self.detiling:
                    text_hotkey = "[G]"
                    command = "Strength"
                    val = str(round(self.detiling.inputs[1].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 6, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 6, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 6, -text_value_width, 'Right', 1)

                    text_hotkey = "[X]"
                    command = "Noise"
                    val = str(round(self.detiling.inputs[2].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 4, -text_value_width, 'Right', 1)

                    text_hotkey = "[H]"
                    command = "Detail"
                    val = str(round(self.detiling.inputs[3].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 3, -text_value_width, 'Right', 1)

                    text_hotkey = "[S]"
                    command = "Scale"
                    val = str(round(self.detiling.inputs[6].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 5, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 5, -text_value_width, 'Right', 1)

                    text_hotkey = "[R]"
                    command = "Roughness"
                    val = str(round(self.detiling.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)

                    text_hotkey = "[V]"
                    command = "Distortion"
                    val = str(round(self.detiling.inputs[5].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 1, -text_value_width, 'Right', 1)

                elif self.smudge:
                    text_hotkey = "[V]"
                    command = "Value"
                    val = str(round(self.smudge.inputs[4].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)
                    
                    text_hotkey = "[C]"
                    command = "Contrast"
                    val = str(round(self.smudge.inputs[5].default_value, 3))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.c, 1, -text_value_width, 'Right', 1)

                elif self.diffuse_tex.projection == "BOX":
                    text_hotkey = "[C]"
                    command = "Triplanar Blend"
                    val = str(round(self.diffuse_tex.projection_blend, 2))
                    text_command = " " + command + ":" + " "
                    text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                    text_command_width = blf.dimensions(0, text_command)[0]
                    text_value_width = blf.dimensions(0, val)[0]
                    text_width = text_hotkey_width + text_command_width + text_value_width
                    ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                    ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                    ui.draw_text(val, self.regX, self.regY, self.v, 2, -text_value_width, 'Right', 1)

            # variation
            elif bpy.context.window_manager.my_toolqt.active_map == 7:
                text_hotkey = "[V]"
                command = "Value"
                val = str(round(self.variation.inputs[5].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 4, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.v, 4, -text_value_width, 'Right', 1)
                
                text_hotkey = "[C]"
                command = "Contrast"
                val = str(round(self.variation.inputs[6].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.c, 3, -text_value_width, 'Right', 1)

                text_hotkey = "[X]"
                command = "Saturation"
                val = str(round(self.variation.inputs[4].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.x, 2, -text_value_width, 'Right', 1)

                text_hotkey = "[H]"
                command = "Hue"
                val = str(round(self.variation.inputs[8].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.h, 1, -text_value_width, 'Right', 1)

            # randomization
            elif bpy.context.window_manager.my_toolqt.active_map == 8:
                text_hotkey = "[H]"
                command = "Hue"
                val = str(round(self.randcolor.inputs[1].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 5, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.h, 5, -text_value_width, 'Right', 1)
                
                text_hotkey = "[V]"
                command = "Value"
                val = str(round(self.randcolor.inputs[3].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 3, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.v, 3, -text_value_width, 'Right', 1)
                
                text_hotkey = "[C]"
                command = "Roughness"
                val = str(round(self.randrough.inputs[1].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.c, 2, -text_value_width, 'Right', 1)
                
                text_hotkey = "[X]"
                command = "Saturation"
                val = str(round(self.randcolor.inputs[2].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.x, 1, -text_value_width, 'Right', 1)
                
            # displacement
            elif bpy.context.window_manager.my_toolqt.active_map == 0:
                text_hotkey = "[C]"
                val = str(round(self.disp.inputs[1].default_value, 3))
                command = "Midlevel"
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 2, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.c, 2, -text_value_width, 'Right', 1)

                text_hotkey = "[V]"
                val = str(round(self.disp.inputs[2].default_value, 3))
                command = "Scale"
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, -text_width, 'Right', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, 1, -text_width + text_hotkey_width, 'Right', 1)
                ui.draw_text(val, self.regX, self.regY, self.v, 1, -text_value_width, 'Right', 1)

            if bpy.context.window_manager.my_toolqt.active_layer > 1 and self.mix:
                if self.ao_tex.image and self.normal_tex.image:
                    height = 10
                elif self.ao_tex.image or self.normal_tex.image:
                    height = 9
                else:
                    height = 8
                text_hotkey = "[O]"
                command = "Layer Mix"
                val = str(round(self.mix.inputs[0].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, height, 0, 'Left', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, height, text_hotkey_width, 'Left', 1)
                ui.draw_text(val, self.regX, self.regY, self.edit_opacity, height, text_hotkey_width + text_command_width, 'Left', 1)
                                
            if self.ao_tex.image and self.ao_strength:
                if self.normal_tex.image:
                    height = 9
                else:
                    height = 8
                text_hotkey = "[A]"
                command = "AO"
                val = str(round(self.ao_strength.inputs[0].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, height, 0, 'Left', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, height, text_hotkey_width, 'Left', 1)
                ui.draw_text(val, self.regX, self.regY, self.edit_ao, height, text_hotkey_width + text_command_width, 'Left', 1)
                
            if self.normal_tex.image:
                height = 8
                text_hotkey = "[Shift N]"
                command = "Normal"
                val = str(round(self.normal_strength.inputs[0].default_value, 3))
                text_command = " " + command + ":" + " "
                text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
                text_command_width = blf.dimensions(0, text_command)[0]
                text_value_width = blf.dimensions(0, val)[0]
                text_width = text_hotkey_width + text_command_width + text_value_width
                ui.draw_text(text_hotkey, self.regX, self.regY, 2, height, 0, 'Left', 1)
                ui.draw_text(text_command, self.regX, self.regY, 0, height, text_hotkey_width, 'Left', 1)
                ui.draw_text(val, self.regX, self.regY, self.edit_normal, height, text_hotkey_width + text_command_width, 'Left', 1)
                            
            text_hotkey = "[Shift B]"
            command = "Bump"
            val = str(round(self.bump_strength.inputs[1].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 7, 0, 'Left', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 7, text_hotkey_width, 'Left', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_bump, 7, text_hotkey_width + text_command_width, 'Left', 1)
                                                            
            text_hotkey = "[L]"
            command = "Subsurface"
            val = str(round(self.shader.inputs[7].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 6, 0, 'Left', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 6, text_hotkey_width, 'Left', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_sss, 6, text_hotkey_width + text_command_width, 'Left', 1)
                
            text_hotkey = "[E]"
            command = "Emission"
            val = str(round(self.shader.inputs[27].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 5, 0, 'Left', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 5, text_hotkey_width, 'Left', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_emission, 5, text_hotkey_width + text_command_width, 'Left', 1)

            text_hotkey = "[Shift Ctrl C]"
            command = "Emission Contrast"
            val = str(round(self.emission_bright_contrast.inputs[2].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 4, 0, 'Left', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 4, text_hotkey_width, 'Left', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_emission_bright_contrast, 4, text_hotkey_width + text_command_width, 'Left', 1)
            
            text_hotkey = "[Shift H]"
            command = "Specular"
            val = str(round(self.shader.inputs[12].default_value, 3))
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 3, 0, 'Left', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 3, text_hotkey_width, 'Left', 1)
            ui.draw_text(val, self.regX, self.regY, self.edit_specular, 3, text_hotkey_width + text_command_width, 'Left', 1)

            text_hotkey = "[Alt C]"
            command = "Extension: "
            val = self.diffuse_tex.extension
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 2, 0, 'Left', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 2, text_hotkey_width, 'Left', 1)
            ui.draw_text(val, self.regX, self.regY, 1, 2, text_hotkey_width + text_command_width, 'Left', 1)

            text_hotkey = "[Alt A]"
            command = "Alpha Channel: "
            if bpy.context.window_manager.my_toolqt.alpha_type:
                val = "Alpha"
            else:
                val = "Diffuse" 
            text_command = " " + command + ":" + " "
            text_hotkey_width = blf.dimensions(0, text_hotkey)[0]
            text_command_width = blf.dimensions(0, text_command)[0]
            text_value_width = blf.dimensions(0, val)[0]
            text_width = text_hotkey_width + text_command_width + text_value_width
            ui.draw_text(text_hotkey, self.regX, self.regY, 2, 1, 0, 'Left', 1)
            ui.draw_text(text_command, self.regX, self.regY, 0, 1, text_hotkey_width, 'Left', 1)
            ui.draw_text(val, self.regX, self.regY, 1, 1, text_hotkey_width + text_command_width, 'Left', 1)

class quickTexture(bpy.types.Operator):
    bl_idname = "object.quicktexture"
    bl_label = "QuickTexture"
    bl_description = "Create QuickTexture"
    bl_options = {"REGISTER", "UNDO"}

    def reset(self):
        self.edit_move = 0
        self.edit_scale = 0
        self.edit_rotate = 0
        self.edit_sss = 0
        self.edit_emission = 0
        self.edit_emission_bright_contrast = 0
        self.edit_specular = 0
        self.edit_scale_horizontal = 0
        self.edit_scale_vertical = 0
        self.edit_bump = 0
        self.edit_normal = 0
        self.h = 0
        self.v = 0
        self.c = 0
        self.edit_opacity = 0
        self.x = 0
        self.edit_ao = 0
        self.ctrl = 0
        self.alt = 0
        self.shift = 0

    def get_nodes(self, ob):
        nodes = utils.get_nodes(ob)
        # refactor
        if nodes:
            # general stuff
            self.mat = nodes[0]
            self.out = nodes[1]
            self.layer = nodes[2]
            self.nodes = nodes[3]
            self.node_tree = nodes[4]
            self.layer_out = nodes[5]
            self.shader = nodes[6]
            self.mix = nodes[7]
            self.tex_coord = nodes[8]
            # mapping
            self.diffuse_mapping = nodes[9]
            self.rough_mapping = nodes[10]
            self.bump_mapping = nodes[11]
            self.alpha_mapping = nodes[12]
            self.disp_mapping = nodes[13]
            self.metal_mapping = nodes[53]
            self.normal_mapping = nodes[56]
            # textures
            self.diffuse_tex = nodes[14]
            self.rough_tex = nodes[15]
            self.bump_tex = nodes[16]
            self.normal_tex = nodes[17]
            self.alpha_tex = nodes[18]
            self.disp_tex = nodes[19]
            self.ao_tex = nodes[20]
            self.metal_tex = nodes[54]
            # clamp
            self.roughness_clamp = nodes[21]
            self.bump_clamp = nodes[22]
            self.alpha_clamp = nodes[23]
            # hue
            self.diffuse_hue_sat = nodes[24]
            self.rough_hue_sat = nodes[25]
            self.bump_hue_sat = nodes[26]
            self.alpha_hue_sat = nodes[27]
            # contrast
            self.diffuse_bright_contrast = nodes[28]
            self.rough_bright_contrast = nodes[29]
            self.bump_bright_contrast = nodes[30]
            self.alpha_bright_contrast = nodes[31]
            # invert
            self.rough_invert = nodes[32]
            self.bump_invert = nodes[33]
            self.alpha_invert = nodes[34]
            self.metal_invert = nodes[55]
            # bump
            self.bump = nodes[35]
            # disp
            self.disp = nodes[36]
            # strength
            self.bump_strength = nodes[37]
            self.normal_strength = nodes[38]
            self.ao_strength = nodes[39]
            # masks
            self.texture_mask = nodes[40]
            self.edge_mask = nodes[41]
            self.dirt_mask = nodes[42]
            self.depth_mask = nodes[43]
            self.height_mask = nodes[44]
            self.normal_mask = nodes[45]
            self.smudge = nodes[46]
            self.randcolor = nodes[47]
            self.randrough = nodes[48]
            self.variation = nodes[49]
            self.detiling = nodes[50]
            self.edge = nodes[51]
            self.dirt = nodes[52]
            # emission
            self.emission_bright_contrast = nodes[57]
                    
    def modal(self, context, event):
        try:
            self.init_area.tag_redraw()

            ob = bpy.context.active_object
            if not ob:
                ui.close(self._handle)
                return {"FINISHED"}
            
            self.view_vector = mathutils.Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
            self.coord = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
            self.regX, self.regY, self.window_active, self.zoomlevel, self.window = utils.window_info(
                context,
                event,
                bpy.context.preferences.addons[__package__].preferences.viewport_drawing_border,
                self.init_area 
            )

            # change this to only be done when needed. not super easy since im calling other classes that need to finish first
            self.get_nodes(ob)

            if event.type.startswith("NDOF"):
                return {"PASS_THROUGH"}

            if not self.window_active:
                return {"PASS_THROUGH"}

            if not bpy.context.window_manager.my_toolqt.running_qt:
                ui.close(self._handle)
                return {"FINISHED"}

            if event.type == "LEFTMOUSE" and event.value == "PRESS":
                if any([
                    self.edit_move,
                    self.edit_scale,
                    self.edit_rotate,
                    self.edit_sss,
                    self.edit_emission,
                    self.edit_emission_bright_contrast,
                    self.edit_specular,
                    self.edit_scale_horizontal,
                    self.edit_scale_vertical,
                    self.edit_bump,
                    self.edit_normal,
                    self.h,
                    self.v,
                    self.c,
                    self.edit_opacity,
                    self.x,
                    self.edit_ao
                ]):
                    self.reset()
                else:
                    if not self.alt and not self.ctrl:
                        ui.close(self._handle)
                        return {"FINISHED"}
                    else:
                        return {"PASS_THROUGH"}

            if event.type == "MOUSEMOVE":
                # settings that are controlled by mouse movement
                if self.edit_move:
                    self.mouse_sample_x.append(event.mouse_region_x)
                    self.mouse_sample_y.append(event.mouse_region_y)
                    if len(self.mouse_sample_x) > 1:
                        current = mathutils.Vector((self.mouse_sample_x[-1], self.mouse_sample_y[-1]))
                        previous = mathutils.Vector((self.mouse_sample_x[-2], self.mouse_sample_y[-2]))

                        delta = -0.005
                        delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult
                        if self.shift == 1:
                            delta *= 0.4
                        if self.ctrl == 1:
                            delta *= 4
                        if self.alt == 1:
                            delta *= 8                       
                        aim = (previous - current).normalized()
                        dist = (previous - current).length * delta
                        aim.resize_3d()
                        
                        if not aim:
                            aim = mathutils.Vector((0, 0, 0))
                        
                        if self.blend:
                            self.blend.inputs[2].default_value += ( aim[0] * dist * -1 )
                        else:
                            mat = None
                            if bpy.context.window_manager.my_toolqt.active_map == 1:
                                mat = mathutils.Matrix.Rotation( self.diffuse_mapping.inputs[2].default_value[2], 4, "Z", )
                            if bpy.context.window_manager.my_toolqt.active_map == 2:
                                mat = mathutils.Matrix.Rotation( self.rough_mapping.inputs[2].default_value[2], 4, "Z", )
                            if bpy.context.window_manager.my_toolqt.active_map == 3:
                                mat = mathutils.Matrix.Rotation( self.bump_mapping.inputs[2].default_value[2], 4, "Z" )
                            if bpy.context.window_manager.my_toolqt.active_map == 4:
                                if self.texture_mask:
                                    mat = mathutils.Matrix.Rotation( self.texture_mask.inputs[2].default_value[2], 4, "Z", )
                                if self.depth_mask:
                                    mat = mathutils.Matrix.Rotation( self.depth_mask.inputs[2].default_value[2], 4, "Z", )
                            if bpy.context.window_manager.my_toolqt.active_map == 5:
                                mat = mathutils.Matrix.Rotation( self.alpha_mapping.inputs[2].default_value[2], 4, "Z", )
                            if bpy.context.window_manager.my_toolqt.active_map == 6:
                                if self.smudge:
                                    mat = mathutils.Matrix.Rotation( self.smudge.inputs[2].default_value[2], 4, "Z", )
                            if bpy.context.window_manager.my_toolqt.active_map == 7:
                                if self.variation:
                                    mat = mathutils.Matrix.Rotation( self.variation.inputs[2].default_value[2], 4, "Z", )
                            if bpy.context.window_manager.my_toolqt.active_map == 9:
                                mat = mathutils.Matrix.Rotation( self.metal_mapping.inputs[2].default_value[2], 4, "Z", )
                            if bpy.context.window_manager.my_toolqt.active_map == 0:
                                mat = mathutils.Matrix.Rotation( self.disp_mapping.inputs[2].default_value[2], 4, "Z", )
                            view = mathutils.Vector((self.rv3d.view_matrix[2][0:3])).normalized()
                            viewmat = self.rv3d.view_matrix.normalized().to_3x3()
                            basemat = mathutils.Matrix().to_3x3()
                            viewdot = view.dot(mathutils.Vector((0, 0, 1)))
                            angle = viewmat[0].angle(basemat[0])
                            dirdot = viewmat[0].dot(mathutils.Vector((0, -1, 0)))
                            if dirdot > 0:
                                mat2 = mathutils.Matrix.Rotation(-angle, 4, "Z")
                            else:
                                mat2 = mathutils.Matrix.Rotation(angle, 4, "Z")

                            if mat:
                                if not self.tex_coord.label == 'Procedural UV':
                                    aim.rotate(mat)

                                if abs(viewdot) > 0.99:
                                    aim.rotate(mat2)

                                xval = aim[0]
                                yval = aim[1]

                                if abs(viewdot) > 0.99:
                                    if not self.tex_coord.label == 'Procedural UV':
                                        xval = aim[0]
                                        yval = aim[1]

                            if bpy.context.window_manager.my_toolqt.active_map == 1:
                                self.diffuse_mapping.inputs[1].default_value[0] += ( xval * dist )
                                self.diffuse_mapping.inputs[1].default_value[1] += ( yval * dist )
                                self.diffuse_mapping.inputs[1].default_value[2] = 1

                                self.rough_mapping.inputs[1].default_value[0] += ( xval * dist )
                                self.rough_mapping.inputs[1].default_value[1] += ( yval * dist )
                                self.rough_mapping.inputs[1].default_value[2] = 1

                                self.bump_mapping.inputs[1].default_value[0] += ( xval * dist )
                                self.bump_mapping.inputs[1].default_value[1] += ( yval * dist )
                                self.bump_mapping.inputs[1].default_value[2] = 1

                                self.alpha_mapping.inputs[1].default_value[0] += ( xval * dist )
                                self.alpha_mapping.inputs[1].default_value[1] += ( yval * dist )
                                self.alpha_mapping.inputs[1].default_value[2] = 1

                                if self.normal_mapping:
                                    self.normal_mapping.inputs[1].default_value[0] += ( xval * dist )
                                    self.normal_mapping.inputs[1].default_value[1] += ( yval * dist )
                                    self.normal_mapping.inputs[1].default_value[2] = 1

                                if self.disp_mapping:
                                    self.disp_mapping.inputs[1].default_value[0] += ( xval * dist )
                                    self.disp_mapping.inputs[1].default_value[1] += ( yval * dist )
                                    self.disp_mapping.inputs[1].default_value[2] = 1

                                if self.metal_mapping:
                                    self.metal_mapping.inputs[1].default_value[0] += ( xval * dist )
                                    self.metal_mapping.inputs[1].default_value[1] += ( yval * dist )
                                    self.metal_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.active_map == 2:
                                self.rough_mapping.inputs[1].default_value[0] += ( xval * dist )
                                self.rough_mapping.inputs[1].default_value[1] += ( yval * dist )
                                self.rough_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.active_map == 3:
                                self.bump_mapping.inputs[1].default_value[0] += ( xval * dist )
                                self.bump_mapping.inputs[1].default_value[1] += ( yval * dist )
                                self.bump_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.active_map == 4:
                                if self.texture_mask:
                                    self.texture_mask.inputs[1].default_value[0] += (xval * dist)
                                    self.texture_mask.inputs[1].default_value[1] += (yval * dist)
                                    self.texture_mask.inputs[1].default_value[2] = 1
                                if self.depth_mask:
                                    self.texture_mask.inputs[1].default_value[1] += (yval * dist)
                                if self.edge_mask:
                                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                                    self.edge_mask.inputs[1].default_value += delta
                                if self.dirt_mask:
                                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                                    self.dirt_mask.inputs[1].default_value += delta
                                if self.height_mask:
                                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                                    self.height_mask.inputs[0].default_value[2] += delta
                                if self.normal_mask:
                                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                                    self.normal_mask.inputs[1].default_value += delta

                            elif bpy.context.window_manager.my_toolqt.active_map == 5:
                                if self.alpha_mapping:
                                    self.alpha_mapping.inputs[1].default_value[0] += ( xval * dist ) 
                                    self.alpha_mapping.inputs[1].default_value[1] += ( yval * dist ) 
                                    self.alpha_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.active_map == 6:
                                if self.smudge:
                                    self.smudge.inputs[1].default_value[0] += ( xval * dist ) 
                                    self.smudge.inputs[1].default_value[1] += ( yval * dist ) 
                                if self.detiling:
                                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                                    self.detiling.inputs[1].default_value += delta 

                            elif bpy.context.window_manager.my_toolqt.active_map == 7:
                                if self.variation:
                                    self.variation.inputs[1].default_value[0] += ( xval * dist )
                                    self.variation.inputs[1].default_value[1] += ( yval * dist )
                                    self.variation.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.active_map == 9:
                                if self.metal_mapping:
                                    self.metal_mapping.inputs[1].default_value[0] += ( xval * dist )
                                    self.metal_mapping.inputs[1].default_value[1] += ( yval * dist )
                                    self.metal_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.active_map == 0:
                                if self.disp_mapping:
                                    self.disp_mapping.inputs[1].default_value[0] += ( xval * dist )
                                    self.disp_mapping.inputs[1].default_value[1] += ( yval * dist )
                                    self.disp_mapping.inputs[1].default_value[2] = 1

                if self.edit_scale:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)

                    if self.blend:
                        self.blend.inputs[3].default_value += delta
                    else:
                        if bpy.context.window_manager.my_toolqt.active_map == 1:
                            self.diffuse_mapping.inputs[3].default_value[0] += ( delta * self.diffuse_mapping.inputs[3].default_value[0] )
                            self.diffuse_mapping.inputs[3].default_value[1] += ( delta * self.diffuse_mapping.inputs[3].default_value[1] )
                            self.diffuse_mapping.inputs[3].default_value[2] += ( delta * self.diffuse_mapping.inputs[3].default_value[2] )

                            self.rough_mapping.inputs[3].default_value[0] += ( delta * self.rough_mapping.inputs[3].default_value[0] )
                            self.rough_mapping.inputs[3].default_value[1] += ( delta * self.rough_mapping.inputs[3].default_value[1] )
                            self.rough_mapping.inputs[3].default_value[2] += ( delta * self.rough_mapping.inputs[3].default_value[2] )

                            self.bump_mapping.inputs[3].default_value[0] += ( delta * self.bump_mapping.inputs[3].default_value[0] )
                            self.bump_mapping.inputs[3].default_value[1] += ( delta * self.bump_mapping.inputs[3].default_value[1] )
                            self.bump_mapping.inputs[3].default_value[2] += ( delta * self.bump_mapping.inputs[3].default_value[2] )

                            self.alpha_mapping.inputs[3].default_value[0] += ( delta * self.alpha_mapping.inputs[3].default_value[0] )
                            self.alpha_mapping.inputs[3].default_value[1] += ( delta * self.alpha_mapping.inputs[3].default_value[1] )
                            self.alpha_mapping.inputs[3].default_value[2] += ( delta * self.alpha_mapping.inputs[3].default_value[2] )

                            if self.normal_mapping:
                                self.normal_mapping.inputs[3].default_value[0] += ( delta * self.normal_mapping.inputs[3].default_value[0] )
                                self.normal_mapping.inputs[3].default_value[1] += ( delta * self.normal_mapping.inputs[3].default_value[1] )
                                self.normal_mapping.inputs[3].default_value[2] += ( delta * self.normal_mapping.inputs[3].default_value[2] )

                            if self.disp_mapping:
                                self.disp_mapping.inputs[3].default_value[0] += ( delta * self.disp_mapping.inputs[3].default_value[0] )
                                self.disp_mapping.inputs[3].default_value[1] += ( delta * self.disp_mapping.inputs[3].default_value[1] )
                                self.disp_mapping.inputs[3].default_value[2] += ( delta * self.disp_mapping.inputs[3].default_value[2] )

                            if self.metal_mapping:
                                self.metal_mapping.inputs[3].default_value[0] += ( delta * self.metal_mapping.inputs[3].default_value[0] )
                                self.metal_mapping.inputs[3].default_value[1] += ( delta * self.metal_mapping.inputs[3].default_value[1] )
                                self.metal_mapping.inputs[3].default_value[2] += ( delta * self.metal_mapping.inputs[3].default_value[2] )

                        elif bpy.context.window_manager.my_toolqt.active_map == 2:
                            self.rough_mapping.inputs[3].default_value[0] += ( delta * self.rough_mapping.inputs[3].default_value[0] )
                            self.rough_mapping.inputs[3].default_value[1] += ( delta * self.rough_mapping.inputs[3].default_value[1] )
                            self.rough_mapping.inputs[3].default_value[2] += ( delta * self.rough_mapping.inputs[3].default_value[2] )

                        elif bpy.context.window_manager.my_toolqt.active_map == 3:
                            self.bump_mapping.inputs[3].default_value[0] += ( delta * self.bump_mapping.inputs[3].default_value[0] )
                            self.bump_mapping.inputs[3].default_value[1] += ( delta * self.bump_mapping.inputs[3].default_value[1] )
                            self.bump_mapping.inputs[3].default_value[2] += ( delta * self.bump_mapping.inputs[3].default_value[2] )

                        elif bpy.context.window_manager.my_toolqt.active_map == 4:
                            if self.texture_mask:
                                self.texture_mask.inputs[3].default_value[0] += delta * self.texture_mask.inputs[3].default_value[0]
                                self.texture_mask.inputs[3].default_value[1] += delta * self.texture_mask.inputs[3].default_value[1]
                                self.texture_mask.inputs[3].default_value[2] += delta * self.texture_mask.inputs[3].default_value[2]
                            if self.depth_mask:
                                self.depth_mask.inputs[3].default_value[0] += delta * self.depth_mask.inputs[3].default_value[0]
                                self.depth_mask.inputs[3].default_value[1] += delta * self.depth_mask.inputs[3].default_value[1]
                                self.depth_mask.inputs[3].default_value[2] += delta * self.depth_mask.inputs[3].default_value[2]
                            if self.edge_mask:
                                self.edge_mask.inputs[0].default_value += delta
                            if self.dirt_mask:
                                self.dirt_mask.inputs[0].default_value += delta
                            if self.height_mask:
                                self.height_mask.inputs[1].default_value += delta
                            if self.normal_mask:
                                self.normal_mask.inputs[0].default_value += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 5:
                            if self.alpha_mapping:
                                self.alpha_mapping.inputs[3].default_value[0] += ( delta * self.alpha_mapping.inputs[3].default_value[0] )
                                self.alpha_mapping.inputs[3].default_value[1] += ( delta * self.alpha_mapping.inputs[3].default_value[1] )
                                self.alpha_mapping.inputs[3].default_value[2] += ( delta * self.alpha_mapping.inputs[3].default_value[2] )

                        elif bpy.context.window_manager.my_toolqt.active_map == 6:
                            if self.smudge:
                                self.smudge.inputs[3].default_value[0] += ( delta * self.smudge.inputs[3].default_value[0] )
                                self.smudge.inputs[3].default_value[1] += ( delta * self.smudge.inputs[3].default_value[1] )
                                self.smudge.inputs[3].default_value[2] += ( delta * self.smudge.inputs[3].default_value[2] )
                            if self.detiling:
                                self.detiling.inputs[6] += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 7:
                            if self.variation:
                                self.variation.inputs[3].default_value[0] += ( delta * self.variation.inputs[3].default_value[0] )
                                self.variation.inputs[3].default_value[1] += ( delta * self.variation.inputs[3].default_value[1] )
                                self.variation.inputs[3].default_value[2] += ( delta * self.variation.inputs[3].default_value[2] )

                        elif bpy.context.window_manager.my_toolqt.active_map == 9:
                            if self.metal_mapping:
                                self.metal_mapping.inputs[3].default_value[0] += ( delta * self.metal_mapping.inputs[3].default_value[0] )
                                self.metal_mapping.inputs[3].default_value[1] += ( delta * self.metal_mapping.inputs[3].default_value[1] )
                                self.metal_mapping.inputs[3].default_value[2] += ( delta * self.metal_mapping.inputs[3].default_value[2] )

                        elif bpy.context.window_manager.my_toolqt.active_map == 0:
                            if self.disp_mapping:
                                self.disp_mapping.inputs[3].default_value[0] += ( delta * self.disp_mapping.inputs[3].default_value[0] )
                                self.disp_mapping.inputs[3].default_value[1] += ( delta * self.disp_mapping.inputs[3].default_value[1] )
                                self.disp_mapping.inputs[3].default_value[2] += ( delta * self.disp_mapping.inputs[3].default_value[2] )

                if self.edit_rotate == 1:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    if self.blend:
                        self.blend.inputs[5].default_value += delta
                    else:
                        if bpy.context.window_manager.my_toolqt.active_map == 1:
                            self.diffuse_mapping.inputs[2].default_value[2] += delta
                            self.rough_mapping.inputs[2].default_value[2] += delta
                            self.bump_mapping.inputs[2].default_value[2] += delta
                            self.alpha_mapping.inputs[2].default_value[2] += delta
                            if self.metal_mapping:
                                self.metal_mapping.inputs[2].default_value[2] += delta
                            if self.normal_mapping:
                                self.normal_mapping.inputs[2].default_value[2] += delta
                            if self.disp_mapping:
                                self.disp_mapping.inputs[2].default_value[2] += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 2:
                            self.rough_mapping.inputs[2].default_value[2] += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 3:
                            self.bump_mapping.inputs[2].default_value[2] += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 4:
                            if self.texture_mask:
                                self.texture_mask.inputs[2].default_value[2] += delta
                            if self.depth_mask:
                                self.depth_mask.inputs[2].default_value[2] += delta
                            if self.edge_mask:
                                self.edge_mask.inputs[2].default_value += delta
                            if self.dirt_mask:
                                self.dirt_mask.inputs[2].default_value += delta
                            if self.height_mask:
                                self.height_mask.inputs[2].default_value += delta
                            if self.normal_mask:
                                self.normal_mask.inputs[1].default_value += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 5:
                            self.alpha_mapping.inputs[2].default_value[2] += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 6:
                            if self.smudge:
                                self.smudge.inputs[2].default_value[2] += delta
                            if self.detiling:
                                self.detiling.inputs[4].default_value += delta

                        elif bpy.context.window_manager.my_toolqt.active_map == 7:
                            if self.variation:
                                self.variation.inputs[2].default_value[2] += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 9:
                            if self.metal_mapping:
                                self.metal_mapping.inputs[2].default_value[2] += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 0:
                            if self.disp_mapping:
                                self.disp_mapping.inputs[2].default_value[2] += delta

                if self.h:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context) * 0.5
                    if self.blend:
                        self.blend.inputs[4].default_value += delta
                    else:
                        if bpy.context.window_manager.my_toolqt.active_map == 1:
                            self.diffuse_hue_sat.inputs[0].default_value += delta
                            if self.diffuse_hue_sat.inputs[0].default_value < 0:
                                self.diffuse_hue_sat.inputs[0].default_value = 0
                            if self.diffuse_hue_sat.inputs[0].default_value > 5:
                                self.diffuse_hue_sat.inputs[0].default_value = 5

                        if bpy.context.window_manager.my_toolqt.active_map == 4:
                            if self.depth_mask:
                                self.depth_mask.inputs[7].default_value += delta
                            if self.edge_mask:
                                self.edge_mask.inputs[5].default_value += delta
                            if self.dirt_mask:
                                self.dirt_mask.inputs[5].default_value += delta
                            if self.height_mask:
                                self.height_mask.inputs[2].default_value += delta
                            
                        if bpy.context.window_manager.my_toolqt.active_map == 6:
                            if self.detiling:
                                self.detiling.inputs[3].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 7:
                            if self.variation:
                                self.variation.inputs[8].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 8:
                            if self.randcolor:
                                self.randcolor.inputs[1].default_value += delta * 20

                if self.v:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context) * 0.5
                    if self.blend:
                        self.blend.inputs[6].default_value += delta
                    else:
                        if bpy.context.window_manager.my_toolqt.active_map == 1:
                            self.diffuse_hue_sat.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 2:
                            self.rough_hue_sat.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 3:
                            self.bump_hue_sat.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 4:
                            if self.texture_mask:
                                self.texture_mask.inputs[4].default_value += delta
                            if self.depth_mask:
                                self.depth_mask.inputs[4].default_value += delta
                            if self.edge_mask:
                                self.edge_mask.inputs[6].default_value += delta
                            if self.dirt_mask:
                                self.dirt_mask.inputs[6].default_value += delta
                            if self.height_mask:
                                self.height_mask.inputs[6].default_value += delta
                            if self.normal_mask:
                                self.normal_mask.inputs[6].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 5:
                            self.alpha_hue_sat.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 6:
                            if self.smudge:
                                self.smudge.inputs[4].default_value += delta
                            if self.detiling:
                                self.detiling.inputs[5].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 7:
                            if self.variation:
                                self.variation.inputs[5].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 8:
                            if self.randcolor:
                                self.randcolor.inputs[3].default_value += delta * 10

                        if bpy.context.window_manager.my_toolqt.active_map == 0:
                            if self.disp:
                                self.disp.inputs[2].default_value += delta

                if self.c:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context) * 0.5
                    if self.blend: 
                        self.blend.inputs[7].default_value += delta
                    else:
                        if bpy.context.window_manager.my_toolqt.active_map == 1:
                            self.diffuse_bright_contrast.inputs[ 2 ].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 2:
                            self.rough_bright_contrast.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 3:
                            self.bump_bright_contrast.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 4:
                            if self.texture_mask:
                                self.texture_mask.inputs[5].default_value += delta
                            if self.depth_mask:
                                self.depth_mask.inputs[5].default_value += delta
                            if self.edge_mask:
                                self.edge_mask.inputs[4].default_value += delta
                            if self.dirt_mask:
                                self.dirt_mask.inputs[4].default_value += delta
                            if self.height_mask:
                                self.height_mask.inputs[4].default_value += delta
                            if self.normal_mask:
                                self.normal_mask.inputs[4].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 5:
                            self.alpha_bright_contrast.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 6:
                            if self.diffuse_tex.projection == "BOX":
                                self.diffuse_tex.projection_blend += delta
                                self.ao_tex.projection_blend += delta
                                self.rough_tex.projection_blend += delta
                                self.alpha_tex.projection_blend += delta
                                self.normal_tex.projection_blend += delta
                                self.bump_tex.projection_blend += delta
                                self.disp_tex.projection_blend += delta
                                if self.mask_tex:
                                    self.mask_tex.projection_blend += delta
                            if self.smudge:
                                self.smudge.inputs[5].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 7:
                            if self.variation:
                                self.variation.inputs[6].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 8:
                            if self.randrough:
                                self.randrough.inputs[1].default_value += delta * 10

                        if bpy.context.window_manager.my_toolqt.active_map == 0:
                            if self.disp:
                                self.disp.inputs[1].default_value += delta

                if self.x:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context) * 0.5
                    if self.blend: 
                        self.blend.inputs[8].default_value += delta
                    else:
                        if bpy.context.window_manager.my_toolqt.active_map == 1:
                            self.diffuse_hue_sat.inputs[1].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 4:
                            if self.edge_mask:
                                self.edge_mask.inputs[3].default_value += delta
                            if self.dirt_mask:
                                self.dirt_mask.inputs[3].default_value += delta
                            if self.height_mask:
                                self.height_mask.inputs[3].default_value += delta
                            if self.normal_mask:
                                self.normal_mask.inputs[3].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 6:
                            if self.detiling:
                                self.detiling.inputs[2].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 7:
                            if self.variation:
                                self.variation.inputs[4].default_value += delta

                        if bpy.context.window_manager.my_toolqt.active_map == 8:
                            if self.randcolor:
                                self.randcolor.inputs[2].default_value += delta * 2

                if self.edit_scale_horizontal:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    
                    if bpy.context.window_manager.my_toolqt.active_map == 1:
                        self.diffuse_mapping.inputs[3].default_value[0] += ( delta * self.diffuse_mapping.inputs[3].default_value[0] )
                        self.rough_mapping.inputs[3].default_value[0] += ( delta * self.rough_mapping.inputs[3].default_value[0] )
                        self.bump_mapping.inputs[3].default_value[0] += ( delta * self.bump_mapping.inputs[3].default_value[0] )
                        self.alpha_mapping.inputs[3].default_value[0] += ( delta * self.alpha_mapping.inputs[3].default_value[0] )
                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[0] += ( delta * self.disp_mapping.inputs[3].default_value[0] )
                        if self.metal_mapping:
                            self.metal_mapping.inputs[3].default_value[0] += ( delta * self.metal_mapping.inputs[3].default_value[0] )
                        if self.normal_mapping:
                            self.normal_mapping.inputs[3].default_value[0] += ( delta * self.normal_mapping.inputs[3].default_value[0] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 2:
                        self.rough_mapping.inputs[3].default_value[0] += ( delta * self.rough_mapping.inputs[3].default_value[0] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 3:
                        self.bump_mapping.inputs[3].default_value[0] += ( delta * self.bump_mapping.inputs[3].default_value[0] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 4:
                        if self.texture_mask:
                            self.texture_mask.inputs[3].default_value[0] += delta * self.texture_mask.inputs[3].default_value[0]
                        if self.depth_mask:
                            self.depth_mask.inputs[3].default_value[0] += delta * self.depth_mask.inputs[3].default_value[0]

                    elif bpy.context.window_manager.my_toolqt.active_map == 5:
                        self.alpha_mapping.inputs[3].default_value[0] += ( delta * self.alpha_mapping.inputs[3].default_value[0] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 6:
                        if self.smudge:
                            self.smudge.inputs[3].default_value[0] += ( delta * self.smudge.inputs[3].default_value[0] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 7:
                        if self.variation:
                            self.variation.inputs[3].default_value[0] += ( delta * self.variation.inputs[3].default_value[0] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 9:
                        if self.metal_mapping:
                            self.metal_mapping.inputs[3].default_value[0] += ( delta * self.metal_mapping.inputs[3].default_value[0] ) 

                    elif bpy.context.window_manager.my_toolqt.active_map == 0:
                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[0] += ( delta * self.disp_mapping.inputs[3].default_value[0] ) 

                if self.edit_scale_vertical:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)

                    if bpy.context.window_manager.my_toolqt.active_map == 1:
                        self.diffuse_mapping.inputs[3].default_value[1] += ( delta * self.diffuse_mapping.inputs[3].default_value[1] )
                        self.rough_mapping.inputs[3].default_value[1] += ( delta * self.rough_mapping.inputs[3].default_value[1] )
                        self.bump_mapping.inputs[3].default_value[1] += ( delta * self.bump_mapping.inputs[3].default_value[1] )
                        self.alpha_mapping.inputs[3].default_value[1] += ( delta * self.alpha_mapping.inputs[3].default_value[1] )
                        if self.metal_mapping:
                            self.metal_mapping.inputs[3].default_value[1] += ( delta * self.metal_mapping.inputs[3].default_value[1] )
                        if self.normal_mapping:
                            self.normal_mapping.inputs[3].default_value[1] += ( delta * self.normal_mapping.inputs[3].default_value[1] )
                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[1] += ( delta * self.disp_mapping.inputs[3].default_value[1] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 2:
                        self.rough_mapping.inputs[3].default_value[1] += ( delta * self.rough_mapping.inputs[3].default_value[1] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 3:
                        self.bump_mapping.inputs[3].default_value[1] += ( delta * self.bump_mapping.inputs[3].default_value[1] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 4:
                        if self.texture_mask:
                            self.texture_mask.inputs[3].default_value[1] += delta * self.texture_mask.inputs[3].default_value[1]
                        if self.depth_mask:
                            self.depth_mask.inputs[3].default_value[1] += delta * self.depth_mask.inputs[3].default_value[1]

                    elif bpy.context.window_manager.my_toolqt.active_map == 5:
                        self.alpha_mapping.inputs[3].default_value[1] += ( delta * self.alpha_mapping.inputs[3].default_value[1] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 6:
                        if self.smudge:
                            self.smudge.inputs[3].default_value[1] += ( delta * self.smudge.inputs[3].default_value[1] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 7:
                        if self.variation:
                            self.variation.inputs[3].default_value[1] += ( delta * self.variation.inputs[3].default_value[1] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 9:
                        if self.metal_mapping:
                            self.metal_mapping.inputs[3].default_value[1] += ( delta * self.metal_mapping.inputs[3].default_value[1] )

                    elif bpy.context.window_manager.my_toolqt.active_map == 0:
                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[1] += ( delta * self.disp_mapping.inputs[3].default_value[1] )

                if self.edit_sss:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    
                    self.shader.inputs[7].default_value += delta
                    if self.shader.inputs[7].default_value < 0:
                        self.shader.inputs[7].default_value = 0
                    if self.shader.inputs[7].default_value > 1:
                        self.shader.inputs[7].default_value = 1
                    
                if self.edit_ao:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    if self.ao_strength:
                        self.ao_strength.inputs[0].default_value += delta

                if self.edit_emission:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    self.shader.inputs[27].default_value += delta

                if self.edit_emission_bright_contrast:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    self.emission_bright_contrast.inputs[2].default_value += delta

                if self.edit_opacity:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    if self.mix: 
                        self.mix.inputs[0].default_value += delta

                if self.edit_specular:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    self.shader.inputs[12].default_value += delta

                if self.edit_normal:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    if self.normal_strength:
                        self.normal_strength.inputs[0].default_value += delta

                if self.edit_bump:
                    delta = utils.cursor_warp(self.shift, self.ctrl, event, self.window, context)
                    self.bump_strength.inputs[1].default_value += delta

            elif event.type in {"LEFT_ALT", "RIGHT_ALT"}:
                if event.value == "PRESS":
                    self.alt = 1
                if event.value == "RELEASE":
                    self.alt = 0
                return {"PASS_THROUGH"}

            elif event.type in {"LEFT_SHIFT", "RIGHT_SHIFT"}:
                if event.value == "PRESS":
                    self.shift = 1
                if event.value == "RELEASE":
                    self.shift = 0
                return {"PASS_THROUGH"}

            elif event.type in {"LEFT_CTRL", "RIGHT_CTRL", "OSKEY"}:
                if event.value == "PRESS":
                    self.ctrl = 1
                if event.value == "RELEASE":
                    self.ctrl = 0
                return {"PASS_THROUGH"}
            
            elif event.type == "MIDDLEMOUSE":
                return {"PASS_THROUGH"}

            elif event.type == "RIGHTMOUSE":
                return {"PASS_THROUGH"}

            elif event.type == "WHEELUPMOUSE":
                return {"PASS_THROUGH"}

            elif event.type == "WHEELDOWNMOUSE":
                return {"PASS_THROUGH"}
            
            elif event.type == "G" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.edit_move:
                    self.reset()
                    self.mouse_sample_x = []
                    self.mouse_sample_y = []
                else:
                    self.reset()
                    self.edit_move = 1
                    self.mouse_sample_x = []
                    self.mouse_sample_y = []

            elif event.type == "S" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.shift:
                    self.edit_scale_vertical = 0
                    if self.edit_scale_horizontal:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_scale_horizontal = 1

                elif self.alt:
                    self.edit_scale_horizontal = 0
                    if self.edit_scale_vertical:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_scale_vertical = 1

                else:
                    if self.edit_scale:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_scale = 1

            elif event.type == "R" and event.value == "PRESS":
                self.get_nodes(ob)
                if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                    if self.edit_rotate:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_rotate = 1

                elif event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                    self.ctrl = 0
                    self.alt = 0
                    self.shift = 0
                    bpy.ops.qt.replacemaps("INVOKE_DEFAULT")

            elif event.type == "P" and event.value == "PRESS":
                self.get_nodes(ob)

                if self.tex_coord.label == 'View':
                    self.reset()

                    resetparm = 0
                    empty_uv = None
                    for modifier in ob.modifiers:
                        if modifier.name.startswith( "QT_UV_View_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer) ):
                            resetparm = 1
                            mod = ob.modifiers.get( modifier.name )
                            empty_uv = mod.projectors[0].object
                            empty_uv.rotation_euler = ( context.region_data.view_rotation.to_euler() )

                        if modifier.name.startswith("QT_Decal"):
                            coord = event.mouse_region_x, event.mouse_region_y
                            normal = mathutils.Vector( (self.rv3d.perspective_matrix[2][0:3]) ).normalized()
                            oldloc = ob.location
                            newloc = utils.coord_on_plane( self.region, self.rv3d, coord, oldloc, normal )
                            ob.rotation_euler = ( self.rv3d.view_rotation.to_euler() )
                            ob.location = newloc

                            scene = context.scene
                            viewlayer = context.view_layer
                            view_vector = view3d_utils.region_2d_to_vector_3d(self.region, self.rv3d, coord)
                            ray_origin = view3d_utils.region_2d_to_origin_3d(self.region, self.rv3d, coord)
                            result, location, normal, index, hitobj, mathutils.Matrix = scene.ray_cast( viewlayer.depsgraph, ray_origin, view_vector )

                            if hitobj:
                                node_obj = None
                                for mod in ob.modifiers:
                                    if mod.name.startswith("QT_Decal"):
                                        geomod = mod
                                node_tree = bpy.data.node_groups[geomod.node_group.name]
                                for n in node_tree.nodes:
                                    if n.type == "OBJECT_INFO":
                                        if node_obj != n:
                                            node_obj = n
                                node_obj.inputs[0].default_value = hitobj
                                if node_obj:
                                    ob.parent = None
                                    bpy.data.objects[hitobj.name].select_set(True)
                                    bpy.context.view_layer.objects.active = hitobj
                                    bpy.ops.object.parent_set(type="OBJECT")
                                    bpy.ops.object.select_all(action="DESELECT")
                                    bpy.data.objects[ob.name].select_set(True)
                                    bpy.context.view_layer.objects.active = ob
                    if resetparm:
                        if self.diffuse_mapping:
                            self.diffuse_mapping.inputs[1].default_value[0] = 0.15
                            self.diffuse_mapping.inputs[1].default_value[1] = 0.15

                            self.rough_mapping.inputs[1].default_value[0] = 0.15
                            self.rough_mapping.inputs[1].default_value[1] = 0.15

                            self.bump_mapping.inputs[1].default_value[0] = 0.15
                            self.bump_mapping.inputs[1].default_value[1] = 0.15

                            self.alpha_mapping.inputs[1].default_value[0] = 0.15
                            self.alpha_mapping.inputs[1].default_value[1] = 0.15

                            self.metal_mapping.inputs[1].default_value[0] = 0.15
                            self.metal_mapping.inputs[1].default_value[1] = 0.15
                else:
                    msg = "Must be View Layer"
                    self.report({'WARNING'}, msg)

            elif event.type == "M" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        bpy.ops.qt.texturemask_qt("INVOKE_DEFAULT")
                    else:
                        msg = "Must be on Layer 2-5"
                        self.report({'WARNING'}, msg)
                                
            elif event.type == "N" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl == 0 and self.alt == 0 and self.shift == 1:
                    if self.edit_normal:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_normal = 1
                elif self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        # check if mask exists on current layer
                        mask = 0
                        for n in self.nodes:
                            if n.name.endswith("Mask_"+ str(bpy.context.window_manager.my_toolqt.active_layer)):
                                mask = 1
                        if mask == 0:
                            bpy.ops.qt.normalmask_qt("INVOKE_DEFAULT")
                    else:
                        msg = "Must be on Layer 2-5"
                        self.report({'WARNING'}, msg)
                else:
                    return {"PASS_THROUGH"}

            elif event.type == "L" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.edit_sss:
                    self.reset()
                else:
                    self.reset()
                    self.edit_sss = 1

            elif event.type == "A" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        # check if mask exists on current layer
                        mask = 0
                        for n in self.nodes:
                            if n.name.endswith("Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer)):
                                mask = 1
                        if mask == 0:
                            bpy.ops.qt.dirtmask_qt("INVOKE_DEFAULT")
                    else:
                        msg = "Must be on Layer 2-5"
                        self.report({'WARNING'}, msg)

                elif self.ctrl == 0 and self.shift == 0 and self.alt == 1:
                    self.reset()
                    bpy.context.window_manager.my_toolqt.alpha_type = not bpy.context.window_manager.my_toolqt.alpha_type 
                    if bpy.context.window_manager.my_toolqt.alpha_type:
                        self.node_tree.links.new( self.alpha_tex.outputs[0], self.alpha_hue_sat.inputs[4], )
                    else:
                        self.node_tree.links.new( self.alpha_tex.outputs[1], self.alpha_hue_sat.inputs[4], )

                elif self.ctrl == 0 and self.shift == 1 and self.alt == 0:
                    self.reset()
                    # check if mask exists on current layer
                    mask = 0
                    for n in self.nodes:
                        if n.name.endswith( "Smudge_Tex_" + str( bpy.context.window_manager.my_toolqt.active_layer ) ):
                            mask = 1
                    if mask == 0:
                        bpy.ops.qt.smudge_qt("INVOKE_DEFAULT")

                elif self.ctrl == 0 and self.shift == 0 and self.alt == 0:
                    if self.edit_ao:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_ao = 1

            elif event.type == "E" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl == 0 and self.shift == 0 and self.alt == 0:
                    if self.edit_emission:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_emission = 1

            elif event.type == "B" and event.value == "PRESS":
                self.get_nodes(ob)
                # NEW BOX LAYER
                if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer < 5:
                        bpy.ops.qt.boxlayer_qt("INVOKE_DEFAULT")

                if self.shift == 1 and self.ctrl == 0 and self.alt == 0:
                    if self.edit_bump:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_bump = 1

            elif event.type == "H" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        # check if mask exists on current layer
                        mask = 0
                        for n in self.nodes:
                            if n.name.endswith( "Mask_" + str( bpy.context.window_manager.my_toolqt.active_layer ) ):
                                mask = 1

                        if mask == 0:
                            bpy.ops.qt.heightmask_qt("INVOKE_DEFAULT")
                    else:
                        msg = "Must be on Layer 2-5"
                        self.report({'WARNING'}, msg)

                elif self.ctrl == 0 and self.alt == 1 and self.shift == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        # check if mask exists on current layer
                        mask = 0
                        for n in self.nodes:
                            if n.name.endswith( "Mask_" + str( bpy.context.window_manager.my_toolqt.active_layer ) ):
                                mask = 1

                        if mask == 0:
                            bpy.ops.qt.depthmask_qt("INVOKE_DEFAULT")
                    else:
                        msg = "Must be on Layer 2-5"
                        self.report({'WARNING'}, msg)

                elif self.ctrl == 0 and self.alt == 0 and self.shift == 1:
                    if self.edit_specular:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_specular = 1

                else:
                    if self.h:
                        self.reset()
                    else:
                        self.reset()
                        self.h = 1

            elif event.type == "V" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer < 5:
                        bpy.ops.qt.viewlayer_qt("INVOKE_DEFAULT")

                elif self.ctrl == 0 and self.alt == 0 and self.shift == 1:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        bpy.ops.qt.vertexmask_qt("INVOKE_DEFAULT")
                    else:
                        msg = "Must be on Layer 2-5"
                        self.report({'WARNING'}, msg)

                elif self.ctrl == 0 and self.alt == 1 and self.shift == 0:
                    self.reset()
                    bpy.ops.qt.variationmask_qt("INVOKE_DEFAULT")

                elif self.ctrl == 0 and self.alt == 0 and self.shift == 0:
                    if self.v:
                        self.reset()
                    else:
                        self.reset()
                        self.v = 1

            elif event.type == "C" and event.value == "PRESS":
                self.get_nodes(ob)

                if self.ctrl == 1 and self.alt == 0 and self.shift == 1:
                    if self.edit_emission_bright_contrast:
                        self.reset()
                    else:
                        self.reset()
                        self.edit_emission_bright_contrast = 1

                elif self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        # check if mask exists on current layer
                        mask = 0
                        for n in self.nodes:
                            if n.name.endswith( "Mask_" + str( bpy.context.window_manager.my_toolqt.active_layer ) ):
                                mask = 1
                        if mask == 0:
                            bpy.ops.qt.edgesmask_qt("INVOKE_DEFAULT")
                    else:
                        msg = "Must be on Layer 2-5"
                        self.report({'WARNING'}, msg)

                elif self.alt == 1 and self.shift == 0 and self.ctrl == 0:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_map == 1:
                        if self.diffuse_tex:
                            if self.diffuse_tex.extension == "CLIP":
                                self.diffuse_tex.extension = "REPEAT"
                            else:
                                self.diffuse_tex.extension = "CLIP"

                        if self.rough_tex:
                            if self.rough_tex.extension == "CLIP":
                                self.rough_tex.extension = "REPEAT"
                            else:
                                self.rough_tex.extension = "CLIP"

                        if self.bump_tex:
                            if self.bump_tex.extension == "CLIP":
                                self.bump_tex.extension = "REPEAT"
                            else:
                                self.bump_tex.extension = "CLIP"

                        if self.normal_tex:
                            if self.normal_tex.extension == "CLIP":
                                self.normal_tex.extension = "REPEAT"
                            else:
                                self.normal_tex.extension = "CLIP"

                        if self.alpha_tex:
                            if self.alpha_tex.extension == "CLIP":
                                self.alpha_tex.extension = "REPEAT"
                            else:
                                self.alpha_tex.extension = "CLIP"

                        if self.metal_tex:
                            if self.metal_tex.extension == "CLIP":
                                self.metal_tex.extension = "REPEAT"
                            else:
                                self.metal_tex.extension = "CLIP"

                    elif bpy.context.window_manager.my_toolqt.active_map == 2:
                        if self.rough_tex:
                            if self.rough_tex.extension == "CLIP":
                                self.rough_tex.extension = "REPEAT"
                            else:
                                self.rough_tex.extension = "CLIP"

                    elif bpy.context.window_manager.my_toolqt.active_map == 3:
                        if self.bump_tex:
                            if self.bump_tex.extension == "CLIP":
                                self.bump_tex.extension = "REPEAT"
                            else:
                                self.bump_tex.extension = "CLIP"

                    elif bpy.context.window_manager.my_toolqt.active_map == 4:
                        tex = self.texture_mask.node_tree.nodes.get("QT_Tex")
                        if tex.extension == "CLIP":
                            tex.extension = "REPEAT"
                        else:
                            tex.extension = "CLIP"

                    elif bpy.context.window_manager.my_toolqt.active_map == 5:
                        if self.alpha_tex:
                            if self.alpha_tex.extension == "CLIP":
                                self.alpha_tex.extension = "REPEAT"
                            else:
                                self.alpha_tex.extension = "CLIP"

                    elif bpy.context.window_manager.my_toolqt.active_map == 9:
                        if self.metal_tex:
                            if self.metal_tex.extension == "CLIP":
                                self.metal_tex.extension = "REPEAT"
                            else:
                                self.metal_tex.extension = "CLIP"

                elif self.alt == 0 and self.shift == 0 and self.shift == 0:
                    if self.c:
                        self.reset()
                    else:
                        self.reset()
                        self.c = 1

            elif event.type == "O" and event.value == "PRESS":
                self.get_nodes(ob)
                if bpy.context.window_manager.my_toolqt.active_layer > 1:
                    if self.ctrl == 0 and self.alt == 0 and self.shift == 0:
                        if self.edit_opacity:
                            self.reset()
                        else:
                            self.edit_opacity = 1

                if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                    self.get_nodes(ob)
                    self.reset()
                    bpy.ops.qt.randomizeperobject_qt("INVOKE_DEFAULT") 

            elif event.type == "I" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl:
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_map == 2:
                        self.rough_invert.inputs[0].default_value = not self.rough_invert.inputs[0].default_value
                    elif bpy.context.window_manager.my_toolqt.active_map == 3:
                        self.bump_invert.inputs[0].default_value = not self.bump_invert.inputs[0].default_value
                    elif bpy.context.window_manager.my_toolqt.active_map == 4:
                        if self.texture_mask:
                            self.texture_mask.inputs[5].default_value = not self.texture_mask.inputs[5].default_value
                        if self.height_mask:
                            self.height_mask.inputs[6].default_value = not self.height_mask.inputs[6].default_value
                        if self.normal_mask:
                            self.normal_mask.inputs[5].default_value = not self.normal_mask.inputs[5].default_value
                        if self.depth_mask:
                            self.depth_mask.inputs[6].default_value = not self.depth_mask.inputs[6].default_value
                    elif bpy.context.window_manager.my_toolqt.active_map == 5:
                        self.alpha_invert.inputs[0].default_value = not self.alpha_invert.inputs[0].default_value
                    elif bpy.context.window_manager.my_toolqt.active_map == 6:
                        self.smudge.inputs[6].default_value = not self.smudge.inputs[6].default_value
                    elif bpy.context.window_manager.my_toolqt.active_map == 7:
                        if self.variation:
                            self.variation.inputs[7].default_value = not self.variation.inputs[7].default_value
                    elif bpy.context.window_manager.my_toolqt.active_map == 9:
                        self.metal_invert.inputs[0].default_value = not self.metal_invert.inputs[0].default_value
                            
            elif event.type == "D" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                    self.reset()
                    bpy.ops.wm.call_menu_pie(name="QT_MT_Quick_Menu_Pie")
                # duplicate
                elif self.ctrl == 0 and self.shift == 1 and self.alt == 0 and not self.blend:
                    self.get_nodes(ob)
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.total_layers < 5:
                        textures.duplicate(self.mat, self.out)
                        self.get_nodes(ob)
                    else:
                        msg = "Maximum Layers (5) Reached"
                        self.report({'WARNING'}, msg)
                    
            # ACTIVE MAP
            # combined
            elif event.type in {"ONE"} and event.value == "PRESS":
                if self.ctrl:
                    bpy.context.window_manager.my_toolqt.active_material = 0
                    bpy.context.window_manager.my_toolqt.active_map = 1
                    bpy.context.window_manager.my_toolqt.active_layer = 1
                else:
                    if not self.blend:
                        bpy.context.window_manager.my_toolqt.active_map = 1
                        if self.mix:
                            self.node_tree.links.new( self.layer_out.inputs[0], self.mix.outputs[0] )
                        else:
                            self.node_tree.links.new( self.layer_out.inputs[0], self.shader.outputs[0] )
                self.get_nodes(ob)
                self.reset()

            # roughness
            elif event.type in {"TWO"} and event.value == "PRESS":
                if self.ctrl:
                    if len(ob.material_slots) > 1:
                        bpy.context.window_manager.my_toolqt.active_material = 1
                        bpy.context.window_manager.my_toolqt.active_map = 1
                        bpy.context.window_manager.my_toolqt.active_layer = 1
                else:
                    if not self.blend:
                        bpy.context.window_manager.my_toolqt.active_map = 2
                        self.node_tree.links.new( self.layer_out.inputs[0], self.roughness_clamp.outputs[0] )
                self.get_nodes(ob)
                self.reset()

            # bump
            elif event.type in {"THREE"} and event.value == "PRESS": 
                if self.ctrl:
                    if len(ob.material_slots) > 2:
                        bpy.context.window_manager.my_toolqt.active_material = 2
                        bpy.context.window_manager.my_toolqt.active_map = 1
                        bpy.context.window_manager.my_toolqt.active_layer = 1
                else:
                    if not self.blend:
                        bpy.context.window_manager.my_toolqt.active_map = 3
                        if self.bump_clamp:
                            self.node_tree.links.new( self.layer_out.inputs[0], self.bump_clamp.outputs[0] )
                self.get_nodes(ob)
                self.reset()
                            
            # mask
            elif event.type in {"FOUR"} and event.value == "PRESS": 
                if self.ctrl:
                    if len(ob.material_slots) > 3:
                        bpy.context.window_manager.my_toolqt.active_material = 3
                        bpy.context.window_manager.my_toolqt.active_map = 1
                        bpy.context.window_manager.my_toolqt.active_layer = 1
                else:
                    if self.texture_mask:
                        bpy.context.window_manager.my_toolqt.active_map = 4
                        self.node_tree.links.new(self.layer_out.inputs[0], self.texture_mask.outputs[0])
                    elif self.edge_mask:
                        bpy.context.window_manager.my_toolqt.active_map = 4
                        self.node_tree.links.new(self.layer_out.inputs[0], self.edge_mask.outputs[0])
                    elif self.dirt_mask:
                        bpy.context.window_manager.my_toolqt.active_map = 4
                        self.node_tree.links.new(self.layer_out.inputs[0], self.dirt_mask.outputs[0])
                    elif self.depth_mask:
                        bpy.context.window_manager.my_toolqt.active_map = 4
                        self.node_tree.links.new(self.layer_out.inputs[0], self.depth_mask.outputs[0])
                    elif self.height_mask:
                        bpy.context.window_manager.my_toolqt.active_map = 4
                        self.node_tree.links.new(self.layer_out.inputs[0], self.height_mask.outputs[0])
                    elif self.normal_mask:
                        bpy.context.window_manager.my_toolqt.active_map = 4
                        self.node_tree.links.new(self.layer_out.inputs[0], self.normal_mask.outputs[0])
                    else:
                        msg = "No Mask Detected"
                        self.report({'WARNING'}, msg)
                self.get_nodes(ob)
                self.reset()
                
            # alpha
            elif event.type in {"FIVE"} and event.value == "PRESS":
                if self.ctrl:
                    if len(ob.material_slots) > 4:
                        bpy.context.window_manager.my_toolqt.active_material = 4
                        bpy.context.window_manager.my_toolqt.active_map = 1
                        bpy.context.window_manager.my_toolqt.active_layer = 1
                else:
                    if not self.blend:
                        bpy.context.window_manager.my_toolqt.active_map = 5
                        self.node_tree.links.new( self.layer_out.inputs[0], self.alpha_clamp.outputs[0] )
                self.get_nodes(ob)
                self.reset()

            # uv
            elif event.type in {"SIX"} and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()

                if self.detiling or self.smudge or self.tex_coord.label == 'Triplanar':
                    bpy.context.window_manager.my_toolqt.active_map = 6
                else:
                    msg = "No De-Tiling, Smudge or Triplanar Layer Detected"
                    self.report({'WARNING'}, msg)
                
            # variation
            elif event.type == "SEVEN":
                self.get_nodes(ob)
                self.reset()
                
                if self.variation:
                    bpy.context.window_manager.my_toolqt.active_map = 7
                    self.node_tree.links.new( self.layer_out.inputs[0], self.variation.outputs[0] )
                else:
                    msg = "No Variation Mask Detected"
                    self.report({'WARNING'}, msg)

            # randomization per object
            elif event.type == "EIGHT":
                self.get_nodes(ob)
                self.reset()
                
                if self.randcolor and self.randval:
                    bpy.context.window_manager.my_toolqt.active_map = 8
                else:
                    msg = "No Randomization Mask Detected"
                    self.report({'WARNING'}, msg)

            # metallic
            elif event.type in {"NINE"} and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()

                if not self.blend:
                    bpy.context.window_manager.my_toolqt.active_map = 9
                    self.node_tree.links.new( self.layer_out.inputs[0], self.metal_invert.outputs[0] )

            elif event.type == "Q" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()
                if self.shift == 0 and self.ctrl == 0 and self.alt == 1:
                    return {"PASS_THROUGH"}
                else:
                    if bpy.context.window_manager.my_toolqt.active_layer > 1:
                        bpy.context.window_manager.my_toolqt.active_map = 1
                        bpy.context.window_manager.my_toolqt.active_layer -= 1
                        layer = self.mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
                        if layer:
                            if self.mix:
                                self.node_tree.links.new( self.layer_out.inputs[0], self.mix.outputs[0] )
                            else:
                                self.node_tree.links.new( self.layer_out.inputs[0], self.shader.outputs[0] )
                            self.mat.node_tree.links.new(self.out.inputs[0], layer.outputs[0])
                            if self.disp_tex.image:
                                self.mat.node_tree.links.new(self.out.inputs[2], layer.outputs[1])
                            self.mat.node_tree.links.new(self.out.inputs[0], layer.outputs[0])
                            self.get_nodes(ob)

            elif event.type == "W" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()
                if bpy.context.window_manager.my_toolqt.active_layer < 5:
                    if bpy.context.window_manager.my_toolqt.total_layers > bpy.context.window_manager.my_toolqt.active_layer: 
                        bpy.context.window_manager.my_toolqt.active_map = 1
                        bpy.context.window_manager.my_toolqt.active_layer += 1
                        layer = self.mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
                        if layer:
                            if self.mix:
                                self.node_tree.links.new( self.layer_out.inputs[0], self.mix.outputs[0] )
                            else:
                                self.node_tree.links.new( self.layer_out.inputs[0], self.shader.outputs[0] )
                            if self.disp_tex.image:
                                self.mat.node_tree.links.new(self.out.inputs[2], layer.outputs[1])
                            self.mat.node_tree.links.new(self.out.inputs[0], layer.outputs[0])
                            self.get_nodes(ob)
                            
            elif event.type == "TAB" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()
                if self.mix:
                    self.node_tree.links.new( self.layer_out.inputs[0], self.mix.outputs[0] )
                else:
                    self.node_tree.links.new( self.layer_out.inputs[0], self.shader.outputs[0] )

            elif event.type == "U" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.shift == 1 and self.ctrl == 0 and self.alt == 0:
                    bpy.context.window_manager.my_toolqt.active_map = 6
                    bpy.ops.qt.detiling_qt("INVOKE_DEFAULT")
                self.reset()

            elif event.type == "BACK_SPACE" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()

                if self.texture_mask:
                    self.nodes.remove(self.texture_mask)
                elif self.edge_mask:
                    self.nodes.remove(self.edge_mask)
                elif self.dirt_mask:
                    self.nodes.remove(self.dirt_mask)
                elif self.height_mask:
                    self.nodes.remove(self.height_mask)
                elif self.normal_mask:
                    self.nodes.remove(self.normal_mask)
                elif self.depth_mask:
                    self.nodes.remove(self.depth_mask)
                elif self.variation:
                    self.nodes.remove(self.variation)
                elif self.randcolor and self.randrough:
                    self.nodes.remove(self.randcolor)
                    self.nodes.remove(self.randrough)
                elif self.detiling:
                    self.nodes.remove(self.detiling)
                elif self.smudge:
                    self.nodes.remove(self.smudge)
                vertex_color = self.nodes.get("QT_VertexColor")
                if vertex_color:
                    self.nodes.remove(vertex_color)

                bpy.context.window_manager.my_toolqt.active_map = 1
                if self.mix:
                    self.node_tree.links.new( self.layer_out.inputs[0], self.mix.outputs[0] )
                else:
                    self.node_tree.links.new( self.layer_out.inputs[0], self.shader.outputs[0] )

            elif event.type == "DEL" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()

                layer1 = self.mat.node_tree.nodes.get("QT_Layer_1")
                layer2 = self.mat.node_tree.nodes.get("QT_Layer_2")
                layer3 = self.mat.node_tree.nodes.get("QT_Layer_3")
                layer4 = self.mat.node_tree.nodes.get("QT_Layer_4")
                layer5 = self.mat.node_tree.nodes.get("QT_Layer_5")

                if bpy.context.window_manager.my_toolqt.total_layers > 1 and not self.blend:
                    self.mat.node_tree.nodes.remove(self.layer)
                    bpy.context.window_manager.my_toolqt.total_layers -= 1

                    if bpy.context.window_manager.my_toolqt.active_layer == 1:
                        if layer2:
                            self.mat.node_tree.links.new(layer2.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer2.outputs[1], self.out.inputs[2])
                            layer2.name = 'QT_Layer_1'
                            new_name = layer2.node_tree.name.replace("QT_Layer_2", "QT_Layer_1", 1)
                            layer2.node_tree.name = new_name
                        if layer3:
                            self.mat.node_tree.links.new(layer3.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer3.outputs[1], self.out.inputs[2])
                            layer3.name = 'QT_Layer_2'
                            new_name = layer3.node_tree.name.replace("QT_Layer_3", "QT_Layer_2", 1)
                            layer3.node_tree.name = new_name
                        if layer4:
                            self.mat.node_tree.links.new(layer4.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer4.outputs[1], self.out.inputs[2])
                            layer4.name = 'QT_Layer_3'
                            new_name = layer4.node_tree.name.replace("QT_Layer_4", "QT_Layer_3", 1)
                            layer4.node_tree.name = new_name
                        if layer5:
                            self.mat.node_tree.links.new(layer5.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer5.outputs[1], self.out.inputs[2])
                            layer5.name = 'QT_Layer_4'
                            new_name = layer5.node_tree.name.replace("QT_Layer_5", "QT_Layer_4", 1)
                            layer5.node_tree.name = new_name

                    if bpy.context.window_manager.my_toolqt.active_layer == 2:
                        if layer1:
                            layer1.name = 'QT_Layer_1'
                            self.mat.node_tree.links.new(layer1.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer1.outputs[1], self.out.inputs[2])
                        if layer3:
                            self.mat.node_tree.links.new(layer1.outputs[0], layer3.inputs[0])
                            self.mat.node_tree.links.new(layer1.outputs[1], layer3.inputs[1])
                            self.mat.node_tree.links.new(layer3.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer3.outputs[1], self.out.inputs[2])
                            layer3.name = 'QT_Layer_2'
                            new_name = layer3.node_tree.name.replace("QT_Layer_3", "QT_Layer_2", 1)
                            layer3.node_tree.name = new_name
                        if layer4:
                            self.mat.node_tree.links.new(layer4.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer4.outputs[1], self.out.inputs[2])
                            layer4.name = 'QT_Layer_3'
                            new_name = layer4.node_tree.name.replace("QT_Layer_4", "QT_Layer_3", 1)
                            layer4.node_tree.name = new_name
                        if layer5:
                            self.mat.node_tree.links.new(layer5.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer5.outputs[1], self.out.inputs[2])
                            layer5.name = 'QT_Layer_4'
                            new_name = layer5.node_tree.name.replace("QT_Layer_5", "QT_Layer_4", 1)
                            layer5.node_tree.name = new_name

                    if bpy.context.window_manager.my_toolqt.active_layer == 3:
                        if layer2:
                            self.mat.node_tree.links.new(layer2.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer2.outputs[1], self.out.inputs[2])
                        if layer4:
                            self.mat.node_tree.links.new(layer2.outputs[0], layer4.inputs[0])
                            self.mat.node_tree.links.new(layer2.outputs[1], layer4.inputs[1])
                            layer4.name = 'QT_Layer_3'
                            new_name = layer4.node_tree.name.replace("QT_Layer_4", "QT_Layer_3", 1)
                            layer4.node_tree.name = new_name
                        if layer5:
                            layer5.name = 'QT_Layer_4'
                            new_name = layer5.node_tree.name.replace("QT_Layer_5", "QT_Layer_4", 1)
                            layer5.node_tree.name = new_name

                    if bpy.context.window_manager.my_toolqt.active_layer == 4:
                        if layer3:
                            self.mat.node_tree.links.new(layer3.outputs[0], self.out.inputs[0])
                            self.mat.node_tree.links.new(layer3.outputs[1], self.out.inputs[2])
                        if layer5:
                            self.mat.node_tree.links.new(layer3.outputs[0], layer5.inputs[0])
                            self.mat.node_tree.links.new(layer3.outputs[1], layer5.inputs[1])
                            layer5.name = 'QT_Layer_4'
                            new_name = layer5.node_tree.name.replace("QT_Layer_5", "QT_Layer_4", 1)
                            layer5.node_tree.name = new_name

                    if bpy.context.window_manager.my_toolqt.active_layer == 5:
                        self.mat.node_tree.links.new(layer4.outputs[0], self.out.inputs[0])
                        self.mat.node_tree.links.new(layer4.outputs[1], self.out.inputs[2])

                    bpy.context.window_manager.my_toolqt.active_layer -= 1

                    self.get_nodes(ob)
                    self.reset()

            elif event.type == "LEFT_BRACKET" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()
                
                if bpy.context.window_manager.my_toolqt.active_map == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] -= math.pi / 2
                    self.rough_mapping.inputs[2].default_value[2] -= math.pi / 2
                    self.bump_mapping.inputs[2].default_value[2] -= math.pi / 2
                    self.alpha_mapping.inputs[2].default_value[2] -= math.pi / 2
                    self.metal_mapping.inputs[2].default_value[2] -= math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 2:
                    self.rough_mapping.inputs[2].default_value[2] -= math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 3:
                    self.bump_mapping.inputs[2].default_value[2] -= math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 4:
                    self.texture_mask.inputs[2].default_value[2] -= math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 5:
                    self.alpha_mapping.inputs[2].default_value[2] -= math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 9:
                    self.metal_mapping.inputs[2].default_value[2] -= math.pi / 2

            elif event.type == "RIGHT_BRACKET" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()

                if bpy.context.window_manager.my_toolqt.active_map == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] += math.pi / 2
                    self.rough_mapping.inputs[2].default_value[2] += math.pi / 2
                    self.bump_mapping.inputs[2].default_value[2] += math.pi / 2
                    self.alpha_mapping.inputs[2].default_value[2] += math.pi / 2
                    self.metal_mapping.inputs[2].default_value[2] -= math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 2:
                    self.rough_mapping.inputs[2].default_value[2] += math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 3:
                    self.bump_mapping.inputs[2].default_value[2] += math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 4:
                    self.texture_mask.inputs[2].default_value[2] += math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 5:
                    self.alpha_mapping.inputs[2].default_value[2] += math.pi / 2

                elif bpy.context.window_manager.my_toolqt.active_map == 9:
                    self.metal_mapping.inputs[2].default_value[2] += math.pi / 2
                
            elif event.type == "K" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()
                
                if self.tex_coord.label == "Decal":
                    if self.diffuse_mapping:
                        self.diffuse_mapping.inputs[1].default_value[0] = 0
                        self.diffuse_mapping.inputs[1].default_value[1] = 0
                        self.diffuse_mapping.inputs[1].default_value[2] = 0

                        self.diffuse_mapping.inputs[2].default_value[0] = 0
                        self.diffuse_mapping.inputs[2].default_value[1] = 0
                        self.diffuse_mapping.inputs[2].default_value[2] = 0

                        self.diffuse_mapping.inputs[3].default_value[0] = 1
                        self.diffuse_mapping.inputs[3].default_value[1] = 1
                        self.diffuse_mapping.inputs[3].default_value[2] = 1

                    if self.rough_mapping:
                        self.rough_mapping.inputs[1].default_value[0] = 0
                        self.rough_mapping.inputs[1].default_value[1] = 0
                        self.rough_mapping.inputs[1].default_value[2] = 0

                        self.rough_mapping.inputs[2].default_value[0] = 0
                        self.rough_mapping.inputs[2].default_value[1] = 0
                        self.rough_mapping.inputs[2].default_value[2] = 0

                        self.rough_mapping.inputs[3].default_value[0] = 1
                        self.rough_mapping.inputs[3].default_value[1] = 1
                        self.rough_mapping.inputs[3].default_value[2] = 1

                    if self.bump_mapping:
                        self.bump_mapping.inputs[1].default_value[0] = 0
                        self.bump_mapping.inputs[1].default_value[1] = 0
                        self.bump_mapping.inputs[1].default_value[2] = 0

                        self.bump_mapping.inputs[2].default_value[0] = 0
                        self.bump_mapping.inputs[2].default_value[1] = 0
                        self.bump_mapping.inputs[2].default_value[2] = 0

                        self.bump_mapping.inputs[3].default_value[0] = 1
                        self.bump_mapping.inputs[3].default_value[1] = 1
                        self.bump_mapping.inputs[3].default_value[2] = 1

                    if self.alpha_mapping:
                        self.alpha_mapping.inputs[1].default_value[0] = 0
                        self.alpha_mapping.inputs[1].default_value[1] = 0
                        self.alpha_mapping.inputs[1].default_value[2] = 0

                        self.alpha_mapping.inputs[2].default_value[0] = 0
                        self.alpha_mapping.inputs[2].default_value[1] = 0
                        self.alpha_mapping.inputs[2].default_value[2] = 0

                    if self.metal_mapping:
                        self.metal_mapping.inputs[1].default_value[0] = 0
                        self.metal_mapping.inputs[1].default_value[1] = 0
                        self.metal_mapping.inputs[1].default_value[2] = 0

                        self.metal_mapping.inputs[2].default_value[0] = 0
                        self.metal_mapping.inputs[2].default_value[1] = 0
                        self.metal_mapping.inputs[2].default_value[2] = 0

                else:
                    width, height = self.diffuse_tex.image.size
                    size = width / height
                    self.diffuse_mapping.inputs[1].default_value[0] = 0
                    self.diffuse_mapping.inputs[1].default_value[1] = 0
                    self.diffuse_mapping.inputs[1].default_value[2] = 0
                    self.diffuse_mapping.inputs[2].default_value[0] = 0
                    self.diffuse_mapping.inputs[2].default_value[1] = 0
                    self.diffuse_mapping.inputs[2].default_value[2] = 0
                    self.diffuse_mapping.inputs[3].default_value[0] = size
                    self.diffuse_mapping.inputs[3].default_value[1] = 1
                    self.diffuse_mapping.inputs[3].default_value[2] = 1

                    if self.rough_mapping:
                        self.rough_mapping.inputs[1].default_value[0] = 0
                        self.rough_mapping.inputs[1].default_value[1] = 0
                        self.rough_mapping.inputs[1].default_value[2] = 0
                        self.rough_mapping.inputs[2].default_value[0] = 0
                        self.rough_mapping.inputs[2].default_value[1] = 0
                        self.rough_mapping.inputs[2].default_value[2] = 0
                        self.rough_mapping.inputs[3].default_value[0] = size
                        self.rough_mapping.inputs[3].default_value[1] = 1
                        self.rough_mapping.inputs[3].default_value[2] = 1

                    if self.bump_mapping:
                        self.bump_mapping.inputs[1].default_value[0] = 0
                        self.bump_mapping.inputs[1].default_value[1] = 0
                        self.bump_mapping.inputs[1].default_value[2] = 0
                        self.bump_mapping.inputs[2].default_value[0] = 0
                        self.bump_mapping.inputs[2].default_value[1] = 0
                        self.bump_mapping.inputs[2].default_value[2] = 0
                        self.bump_mapping.inputs[3].default_value[0] = size
                        self.bump_mapping.inputs[3].default_value[1] = 1
                        self.bump_mapping.inputs[3].default_value[2] = 1

                    if self.shader:
                        self.shader.inputs[7].default_value = 0
                        self.shader.inputs[12].default_value = 0.5
                        self.shader.inputs[27].default_value = 0

                    if self.alpha_mapping:
                        self.alpha_mapping.inputs[1].default_value[0] = 0
                        self.alpha_mapping.inputs[1].default_value[1] = 0
                        self.alpha_mapping.inputs[1].default_value[2] = 0
                        self.alpha_mapping.inputs[2].default_value[0] = 0
                        self.alpha_mapping.inputs[2].default_value[1] = 0
                        self.alpha_mapping.inputs[2].default_value[2] = 0
                        self.alpha_mapping.inputs[3].default_value[0] = size
                        self.alpha_mapping.inputs[3].default_value[1] = 1
                        self.alpha_mapping.inputs[3].default_value[2] = 1

                    if self.metal_mapping:
                        self.metal_mapping.inputs[1].default_value[0] = 0
                        self.metal_mapping.inputs[1].default_value[1] = 0
                        self.metal_mapping.inputs[1].default_value[2] = 0
                        self.metal_mapping.inputs[2].default_value[0] = 0
                        self.metal_mapping.inputs[2].default_value[1] = 0
                        self.metal_mapping.inputs[2].default_value[2] = 0
                        self.metal_mapping.inputs[3].default_value[0] = size
                        self.metal_mapping.inputs[3].default_value[1] = 1
                        self.metal_mapping.inputs[3].default_value[2] = 1

                if self.ao_strength:
                    self.ao_strength.inputs[0].default_value = 0
                if self.normal_strength:
                    self.normal_strength.inputs[0].default_value = 0
                if self.bump_strength:
                    self.bump_strength.inputs[1].default_value = 0
                if self.shader:
                    self.shader.inputs[7].default_value = 0
                    self.shader.inputs[12].default_value = 0.5
                    self.shader.inputs[27].default_value = 0
                if self.diffuse_hue_sat:
                    self.diffuse_hue_sat.inputs[0].default_value = 0.5
                    self.diffuse_hue_sat.inputs[1].default_value = 1
                    self.diffuse_hue_sat.inputs[2].default_value = 1
                if self.rough_hue_sat:
                    self.rough_hue_sat.inputs[0].default_value = 0.5
                    self.rough_hue_sat.inputs[1].default_value = 1
                    self.rough_hue_sat.inputs[2].default_value = 1
                if self.bump_hue_sat:
                    self.bump_hue_sat.inputs[0].default_value = 0.5
                    self.bump_hue_sat.inputs[1].default_value = 1
                    self.bump_hue_sat.inputs[2].default_value = 1
                if self.alpha_hue_sat:
                    self.alpha_hue_sat.inputs[0].default_value = 0.5
                    self.alpha_hue_sat.inputs[1].default_value = 1
                    self.alpha_hue_sat.inputs[2].default_value = 1
                if self.diffuse_bright_contrast:
                    self.diffuse_bright_contrast.inputs[2].default_value = 0
                if self.rough_bright_contrast:
                    self.rough_bright_contrast.inputs[2].default_value = 0
                if self.bump_bright_contrast:
                    self.bump_bright_contrast.inputs[2].default_value = 0
                if self.alpha_bright_contrast:
                    self.alpha_bright_contrast.inputs[2].default_value = 0
                if self.emission_bright_contrast:
                    self.emission_bright_contrast.inputs[2].default_value = 0

            elif event.type == "ZERO" and event.value == "PRESS":
                self.get_nodes(ob)
                self.reset()
                if not self.blend:
                    if self.disp_tex.image:
                        bpy.context.window_manager.my_toolqt.active_map = 0
                        if self.mix:
                            self.node_tree.links.new( self.layer_out.inputs[0], self.mix.outputs[0] )
                        else:
                            self.node_tree.links.new( self.layer_out.inputs[0], self.shader.outputs[0] )
                    else:
                        msg = "No Displacement Map Detected"
                        self.report({'WARNING'}, msg)
                    
            elif event.type == "X" and event.value == "PRESS":
                self.get_nodes(ob)
                if self.x:
                    self.reset()
                else:
                    self.reset()
                    self.x = 1
                    
            elif event.type == "T" and event.value == "PRESS":
                if event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                    ui.close(self._handle)
                    return {"FINISHED"}
                if event.ctrl == 0 and event.shift == 1 and event.alt == 0:
                    self.get_nodes(ob)
                    self.reset()
                    if bpy.context.window_manager.my_toolqt.active_layer < 5:
                        bpy.ops.qt.triplanar_qt("INVOKE_DEFAULT")
                                    
            elif event.type == "Z":
                if self.ctrl:
                    msg = "Repeated Undos without pause can crash QuickTexture. Please Undo carefully"
                    self.report({'WARNING'}, msg)
                return {"PASS_THROUGH"}

            elif event.type == "ESC":
                self.reset()
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_0":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_1":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_2":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_3":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_4":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_5":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_6":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_7":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_8":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_9":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_PERIOD":
                return {"PASS_THROUGH"}

            elif event.type == "PERIOD":
                return {"PASS_THROUGH"}
            
            return {"RUNNING_MODAL"}

        except Exception:
            ui.close(self._handle)
            addon_name = 'QuickTexture 2024'
            addon_module = [m for m in addon_utils.modules() if m.bl_info.get('name') == addon_name][0]
            addon_version = str(addon_module.bl_info.get('version'))
            blender_version = bpy.app.version_string
            msg = "Blender " + blender_version + "\n" + \
                addon_name + " " + addon_version + "\n" + \
                "An unexpected error has occurred. Please update QuickTools via the instructions found at ALKSNDR.COM/QUICKTOOLS" + "\n" + \
                "Check full log in the system console and submit an error report at ALKSNDR.COM/QUICKTOOLS"
            self.report({'ERROR'}, msg)
            traceback.print_exc()
            return {"FINISHED"}

    def invoke(self, context, event):
        # settings
        if not bpy.context.window_manager.my_toolqt.startup_prefs:
            bpy.context.window_manager.my_toolqt.startup_prefs = 1

        scene_count = len(bpy.data.scenes)
        viewlayer_count = len(bpy.context.scene.view_layers)
        if scene_count > 1 or viewlayer_count > 1:
            msg = "QuickTools does not support more than 1 scene or view layer per file. Please delete all but one scene and one view layer."
            self.report({'ERROR'}, msg)
            return {"FINISHED"}
        
        if bpy.context.scene.name != 'Scene':
            bpy.context.scene.name = 'Scene'
        if bpy.context.view_layer.name != 'ViewLayer':
            bpy.context.view_layer.name = 'ViewLayer'

        if not bpy.context.preferences.view.language == 'en_US':
            msg = "QuickTools fully supports the English Language and may have bugs in others. Set your Blender to en_US"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        # settings
        bpy.context.window_manager.my_toolqt.active_map = 1
        bpy.context.window_manager.my_toolqt.active_layer = 1
        bpy.context.window_manager.my_toolqt.total_layers = 1
        bpy.context.window_manager.my_toolqt.active_material = 0
        bpy.context.window_manager.my_toolqt.alpha_type = 0
        bpy.context.window_manager.my_toolqs.running_qs = 0
        bpy.context.window_manager.my_toolqs.running_qd = 0
        bpy.context.window_manager.my_toolqs.running_qc = 0
        bpy.context.window_manager.my_toolqt.running_qt = 1           

        ob = bpy.context.active_object
        sel = bpy.context.selected_objects
        edit = 0
        
        if ob:
            if ob.type not in {"MESH", "CURVE"}:
                msg = "Select a Mesh or Curve Object"
                self.report({'ERROR'}, msg)
                return {"FINISHED"}

        if sel:
            for ob in sel:
                if ob.type == 'CURVE':
                    bpy.ops.object.convert(target="MESH")
                    sel = bpy.context.selected_objects
                if ob.type not in {"MESH", "CURVE"}:
                    msg = "Select a Mesh or Curve Object"
                    self.report({'ERROR'}, msg)
                    return {"FINISHED"}
            for ob in sel:
                if ob.mode == "EDIT":
                    bpy.ops.object.mode_set(mode="OBJECT")
                    utils.make_single_user(ob)
                    bpy.ops.object.mode_set(mode="EDIT")
                else:
                    utils.make_single_user(ob)
                if ob.mode == "EDIT":
                    edit = 1
                    bpy.ops.object.mode_set(mode="OBJECT")
                    temp = 1
                    for mat in ob.data.materials:
                        if mat.name == 'TEMP_QT':
                            temp = 0
                            material = mat
                    if temp:
                        material = bpy.data.materials.new(name="TEMP_QT")
                        ob.data.materials.append(material)
                    ob.active_material_index = len(ob.material_slots) - 1
                    for poly in ob.data.polygons:
                        if poly.select:
                            poly.material_index = len(ob.material_slots) - 1
            bpy.context.window_manager.my_toolqt.active_material = len(ob.material_slots) - 1
            # reset transform unless decal
            mod = ob.modifiers.get("QT_Decal")
            if not mod:
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for r in area.regions:
                    if r.type == "UI":
                        npanel = r.width

        self.init_area = context.area
        self.regX = context.region.width - npanel
        self.regY = context.region.height
        self.region = context.region
        self.rv3d = context.region_data
        self.region3D = bpy.context.space_data.region_3d
        self.oldSel = context.selected_objects
        self.view_vector = mathutils.Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
        self.regX, self.regY, self.window_active, self.zoomlevel, self.window = utils.window_info(
            context,
            event,
            bpy.context.preferences.addons[__package__].preferences.viewport_drawing_border,
            self.init_area 
        )
        
        # collections
        if "QuickTexture" in bpy.data.collections:
            self.collection = bpy.data.collections["QuickTexture"]
            bpy.data.collections["QuickTexture"].hide_viewport = False
            bpy.data.collections["QuickTexture"].hide_render = False
        else:
            self.collection = objects.make_collection("QuickTexture", context)

        collections = bpy.context.view_layer.layer_collection.children
        for collection in collections:
            if collection.name == "QuickTexture":
                if collection.hide_viewport:
                    collection.hide_viewport = False
     
        self.coord = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))
        self.coord_firstclick = mathutils.Vector((0, 0))
        self.coord_lastclick = mathutils.Vector((0, 0))
        self.coord_hotkeyclick = mathutils.Vector((0, 0))
        self.avg_2d = mathutils.Vector((0, 0))
        self.mouse_sample_x = []
        self.mouse_sample_y = []
        self.hotkey_press = []
        self.lmb = False
        self.rmb = False
        self.mmb = False
        self.alt = False
        self.ctrl = False
        self.shift = False

        # edit
        self.edit_ao = False
        self.edit_move = False
        self.edit_scale = False
        self.edit_rotate = False
        self.edit_sss = False
        self.edit_emission = False
        self.edit_emission_bright_contrast = False
        self.h = False
        self.v = False
        self.c = False
        self.edit_opacity = False
        self.x = False
        self.edit_specular = False
        self.edit_scale_vertical = False
        self.edit_scale_horizontal = False
        self.edit_bump = False
        self.edit_normal = False
        
        # nodes
        self.mat = None
        self.out = None
        self.layer = None
        self.nodes = None
        self.node_tree = None
        self.layer_out = None
        self.shader = None
        self.mix = None
        self.tex_coord = None
        self.diffuse_mapping = None
        self.rough_mapping = None
        self.bump_mapping = None
        self.metal_mapping = None
        self.roughness_clamp = None
        self.bump_clamp = None
        self.diffuse_tex = None
        self.diffuse_hue_sat = None
        self.diffuse_bright_contrast = None
        self.metal_tex = None
        self.rough_tex = None
        self.rough_bright_contrast = None
        self.rough_invert = None
        self.rough_hue_sat = None
        self.bump_tex = None
        self.bump_bright_contrast = None
        self.bump = None
        self.bump_strength = None
        self.bump_invert = None
        self.bump_hue_sat = None
        self.normal_tex = None
        self.normal_strength = None
        self.alpha_mapping = None
        self.alpha_tex = None
        self.alpha_bright_contrast = None
        self.alpha_invert = None
        self.metal_invert = None
        self.alpha_hue_sat = None
        self.alpha_clamp = None
        self.ao_tex = None
        self.ao_strength = None
        self.disp = None
        self.disp_tex = None
        self.disp_mapping = None
        self.texture_mask = None
        self.smudge = None
        self.randcolor = None
        self.randval = None
        self.variation = None
        self.blend = None
        self.emission_bright_contrast = None
        
        # ui
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_quickTexture, args, "WINDOW", "POST_PIXEL")
        context.window_manager.modal_handler_add(self)

        # object exists
        if not edit:
            if len(sel) == 1 and ob:
                bpy.context.window_manager.my_toolqt.total_materials = len(ob.data.materials)
                if ob.data.materials:
                    for mat in ob.data.materials:
                        if mat:
                            # QT exists so go into QT Edit
                            if mat.name.startswith("QT") and not mat.name.startswith("QT_Paintover"):
                                layer = None
                                layers = []
                                blend = mat.node_tree.nodes.get("QT_Blend")
                                layer1 = mat.node_tree.nodes.get("QT_Layer_1")
                                if layer1:
                                    bpy.context.window_manager.my_toolqt.active_layer = 1
                                    bpy.context.window_manager.my_toolqt.total_layers = 1
                                    layers.append(layer1)
                                layer2 = mat.node_tree.nodes.get("QT_Layer_2")
                                if layer2:
                                    bpy.context.window_manager.my_toolqt.active_layer = 2
                                    bpy.context.window_manager.my_toolqt.total_layers = 2
                                    layers.append(layer2)
                                layer3 = mat.node_tree.nodes.get("QT_Layer_3")
                                if layer3:
                                    bpy.context.window_manager.my_toolqt.active_layer = 3
                                    bpy.context.window_manager.my_toolqt.total_layers = 3
                                    layers.append(layer3)
                                layer4 = mat.node_tree.nodes.get("QT_Layer_4")
                                if layer4:
                                    bpy.context.window_manager.my_toolqt.active_layer = 4
                                    bpy.context.window_manager.my_toolqt.total_layers = 4
                                    layers.append(layer4)
                                layer5 = mat.node_tree.nodes.get("QT_Layer_5")
                                if layer5:
                                    bpy.context.window_manager.my_toolqt.active_layer = 5
                                    bpy.context.window_manager.my_toolqt.total_layers = 5
                                    layers.append(layer5)
                                # connects combined map to end point for every layer
                                for layer in layers:
                                    mix = layer.node_tree.nodes.get("QT_Mix")
                                    shader = layer.node_tree.nodes.get("QT_Shader")
                                    layer_out = layer.node_tree.nodes.get("OUT")
                                    if mix:
                                        layer.node_tree.links.new(layer_out.inputs[0], mix.outputs[0])
                                    else:
                                        layer.node_tree.links.new(layer_out.inputs[0], shader.outputs[0])
                                out = mat.node_tree.nodes.get("QT_Output")
                                if layer1:
                                    layer = layer1
                                if layer2:
                                    layer = layer2
                                if layer3:
                                    layer = layer3
                                if layer4:
                                    layer = layer4
                                if layer5:
                                    layer = layer5
                                # connects max possible layer to end point
                                if out and layer:
                                    mat.node_tree.links.new(out.inputs[0], layer.outputs[0])
                                    mat.node_tree.links.new(out.inputs[2], layer.outputs[1])
                                if blend:
                                    mat.node_tree.links.new(out.inputs[0], blend.outputs[0])
                                    mat.node_tree.links.new(out.inputs[2], blend.outputs[1])
                                return {"RUNNING_MODAL"}
                            # attempt to remake existing material into QT
                            else:
                                files = []
                                img_spec = None
                                for mod in addon_utils.modules():
                                    if mod.bl_info["name"].startswith("QuickTexture"):
                                        filepath = mod.__file__
                                dirpath = os.path.dirname(filepath)
                                fullpath = os.path.join(dirpath, "QT_Presets.blend")
                                for n in mat.node_tree.nodes:
                                    if n.type == 'TEX_IMAGE':
                                        if n.image:
                                            img_spec = n.image.name
                                            files.append(img_spec)
                                    if n.type == 'GROUP':
                                        for node in n.node_tree.nodes:
                                            if node.type == 'TEX_IMAGE':
                                                if node.image:
                                                    img_spec = node.image.name
                                                    files.append(img_spec)
                                if img_spec:
                                    if len(ob.data.materials) > 0:
                                        for m in ob.data.materials:
                                            if m:
                                                m = None
                                    textures.create_material(ob, img_spec, files, None, fullpath, 0, 0)
                                    return {"RUNNING_MODAL"}
                                else:
                                    if len(ob.data.materials) > 0:
                                        for m in ob.data.materials:
                                            if m:
                                                m = None
                        # cleanup mats
                        else:
                            bpy.ops.object.material_slot_remove()
                            bpy.context.window_manager.my_toolqt.total_materials = len(ob.data.materials)
                            bpy.context.window_manager.my_toolqt.active_material = 0

                if bpy.context.window_manager.my_toolqt.multilayer:
                    bpy.context.window_manager.my_toolqt.uv_mode == 'Procedural Box'
                
                if bpy.context.window_manager.my_toolqt.uv_mode == 'UV':
                    # create uvs if they dont exist
                    if len(ob.data.uv_layers) == 0:
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.select_all(action="SELECT")
                            bpy.ops.uv.smart_project()
                            bpy.ops.object.editmode_toggle()
                # remove uvs if not using UV mode
                else:
                    if len(ob.data.uv_layers) > 0:
                        uvs = [uv for uv in ob.data.uv_layers if uv != ob.data.uv_layers]
                        while uvs:
                            ob.data.uv_layers.remove(uvs.pop())
                            
                if bpy.context.window_manager.my_toolqt.uv_mode == "View":
                    empty_ob = objects.create_empty( "QT_UV_View_1", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 0 )
                    col = bpy.data.collections["QuickTexture"]
                    objects.add_to_collection(empty_ob.name, col, context)

                    empty_ob.rotation_euler = ( context.region_data.view_rotation.to_euler() )

                    rmod1 = ob.modifiers.new(name="QT_UV_View_1", type="UV_PROJECT")
                    rmod1.projector_count = 1
                    rmod1.projectors[0].object = bpy.data.objects[empty_ob.name]
                    rmod1.uv_layer = "QT_UV_View_1"

                    local_bbox_center = 0.125 * sum( (mathutils.Vector(b) for b in ob.bound_box), mathutils.Vector() )
                    global_bbox_center = ob.matrix_world @ local_bbox_center
                    empty_ob.location = global_bbox_center
        
                    # parenting
                    bpy.ops.object.select_all(action="DESELECT")
                    bpy.data.objects[empty_ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = empty_ob
                    bpy.context.object.hide_viewport = False
                    bpy.context.object.hide_render = False
                    bpy.context.object.hide_select = False
                    bpy.data.objects[empty_ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = empty_ob
                    bpy.data.objects[ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = ob
                    bpy.ops.object.parent_set(type="OBJECT")
                    bpy.ops.object.select_all(action="DESELECT")
                    bpy.data.objects[empty_ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = empty_ob
                    bpy.context.object.hide_viewport = True
                    bpy.context.object.hide_render = True
                    bpy.context.object.hide_select = True
                    bpy.ops.object.select_all(action="DESELECT")
                    bpy.data.objects[ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = ob
                
                    layer = ob.data.uv_layers.get("QT_UV_View_Layer_1")
                    if layer is None:
                        uvname = "QT_UV_View_Layer_1"
                        ob.data.uv_layers.new(name=uvname)
                        ob.data.uv_layers[uvname].active = True
                        bpy.ops.object.editmode_toggle()
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.uv.project_from_view( camera_bounds=False, correct_aspect=True, scale_to_bounds=False )
                        bpy.ops.object.editmode_toggle()
                    
                if bpy.context.window_manager.my_toolqt.uv_mode == "Procedural Box":
                    layer = ob.data.uv_layers.get("QT_UV_Box_Layer")
                    if layer is None:
                        uvname = "QT_UV_Box_Layer"
                        ob.data.uv_layers.new(name=uvname)
                        ob.data.uv_layers[uvname].active = True
                        bpy.ops.object.editmode_toggle()
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.uv.project_from_view( camera_bounds=False, correct_aspect=True, scale_to_bounds=False )
                        bpy.ops.object.editmode_toggle()

                    # Procedural UV setup
                    empty_uv1 = objects.create_empty( "QT_UV_Z_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
                    empty_uv2 = objects.create_empty( "QT_UV_Z_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
                    empty_uv3 = objects.create_empty( "QT_UV_Y_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
                    empty_uv4 = objects.create_empty( "QT_UV_Y_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
                    empty_uv5 = objects.create_empty( "QT_UV_X_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
                    empty_uv6 = objects.create_empty( "QT_UV_X_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
                    col = bpy.data.collections["QuickTexture"]
                    objects.add_to_collection(empty_uv1.name, col, context)
                    objects.add_to_collection(empty_uv2.name, col, context)
                    objects.add_to_collection(empty_uv3.name, col, context)
                    objects.add_to_collection(empty_uv4.name, col, context)
                    objects.add_to_collection(empty_uv5.name, col, context)
                    objects.add_to_collection(empty_uv6.name, col, context)

                    # Z
                    empty_uv2.rotation_euler.y = math.pi
                    empty_uv2.rotation_euler.z = math.pi
                    # Y
                    empty_uv3.rotation_euler.x = -math.pi / 2
                    empty_uv3.rotation_euler.y = math.pi
                    empty_uv4.rotation_euler.x = math.pi / 2
                    # X
                    empty_uv5.rotation_euler.z = math.pi / 2
                    empty_uv5.rotation_euler.x = math.pi / 2
                    empty_uv6.rotation_euler.z = -math.pi / 2
                    empty_uv6.rotation_euler.x = math.pi / 2

                    mod = ob.modifiers.get("QT_UV_Box")
                    if mod is None:
                        rmod1 = ob.modifiers.new(name="QT_UV_Box", type="UV_PROJECT")
                        rmod1.projector_count = 6
                        rmod1.projectors[0].object = bpy.data.objects[empty_uv1.name]
                        rmod1.projectors[1].object = bpy.data.objects[empty_uv2.name]
                        rmod1.projectors[2].object = bpy.data.objects[empty_uv3.name]
                        rmod1.projectors[3].object = bpy.data.objects[empty_uv4.name]
                        rmod1.projectors[4].object = bpy.data.objects[empty_uv5.name]
                        rmod1.projectors[5].object = bpy.data.objects[empty_uv6.name]
                        rmod1.uv_layer = "QT_UV_Box_Layer"
                    bpy.ops.object.select_all(action="DESELECT")
                    bpy.data.objects[ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = ob
                    
            # blend QT objects from active to all selected
            if len(sel) == 2 and ob:
                ob = bpy.context.active_object
                mat = ob.data.materials[-1]
                for material in ob.data.materials:
                    self.blend = material.node_tree.nodes.get("QT_Blend")

                for obj in sel:
                    if ob != obj:
                        source_mat = obj.data.materials[-1]

                if not self.blend:
                    layer1 = source_mat.node_tree.nodes.get("QT_Layer_1")
                    layer2 = source_mat.node_tree.nodes.get("QT_Layer_2")
                    layer3 = source_mat.node_tree.nodes.get("QT_Layer_3")
                    layer4 = source_mat.node_tree.nodes.get("QT_Layer_4")
                    layer5 = source_mat.node_tree.nodes.get("QT_Layer_5")

                    # get blend group node
                    filepath = None
                    for mod in addon_utils.modules():
                        if mod.bl_info["name"].startswith("QuickTexture"):
                            filepath = mod.__file__
                    dirpath = os.path.dirname(filepath)
                    fullpath = os.path.join(dirpath, "QT_Presets.blend")
                    original_group = bpy.data.node_groups.get("QT_Blend")
                    if not original_group:
                        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
                            data_to.node_groups = [
                                name for name in data_from.node_groups if name == ("QT_Blend")
                            ]
                        original_group = bpy.data.node_groups["QT_Blend"]
                    group = original_group.copy()

                    group_node = mat.node_tree.nodes.new(type="ShaderNodeGroup")
                    group_node.node_tree = bpy.data.node_groups[group.name]
                    group_node.name = "QT_Blend"
                    self.blend = group_node

                    layer = mat.node_tree.nodes.get("QT_Layer_5")
                    if not layer:
                        layer = mat.node_tree.nodes.get("QT_Layer_4")
                    if not layer:
                        layer = mat.node_tree.nodes.get("QT_Layer_3")
                    if not layer:
                        layer = mat.node_tree.nodes.get("QT_Layer_2")
                    if not layer:
                        layer = mat.node_tree.nodes.get("QT_Layer_1")

                    # connect the blend properly with the latest layer to the out node
                    out = mat.node_tree.nodes.get("QT_Output")
                    if layer:
                        mat.node_tree.links.new(layer.outputs[0], self.blend.inputs[0])
                        mat.node_tree.links.new(layer.outputs[1], self.blend.inputs[1])
                        mat.node_tree.links.new(self.blend.outputs[0], out.inputs[0])
                        mat.node_tree.links.new(self.blend.outputs[1], out.inputs[2])

                    blend_shader = self.blend.node_tree.nodes.get("QT_Shader") 
                    blend_disp = self.blend.node_tree.nodes.get("QT_Disp")
                
                    # creating all the cloned layers in the blend group
                    if layer1:
                        l1 = self.blend.node_tree.nodes.new(type="ShaderNodeGroup")
                        l1.node_tree = bpy.data.node_groups[layer1.node_tree.name]
                        self.blend.node_tree.links.new(l1.outputs[0], blend_shader.inputs[2])
                        self.blend.node_tree.links.new(l1.outputs[1], blend_disp.inputs[1])
                    if layer2:
                        l2 = self.blend.node_tree.nodes.new(type="ShaderNodeGroup")
                        l2.node_tree = bpy.data.node_groups[layer2.node_tree.name]
                        self.blend.node_tree.links.new(l1.outputs[0], l2.inputs[0])
                        self.blend.node_tree.links.new(l1.outputs[1], l2.inputs[1])
                        self.blend.node_tree.links.new(l2.outputs[0], blend_shader.inputs[2])
                        self.blend.node_tree.links.new(l2.outputs[1], blend_disp.inputs[1])
                    if layer3:
                        l3 = self.blend.node_tree.nodes.new(type="ShaderNodeGroup")
                        l3.node_tree = bpy.data.node_groups[layer3.node_tree.name]
                        self.blend.node_tree.links.new(l2.outputs[0], l3.inputs[0])
                        self.blend.node_tree.links.new(l2.outputs[1], l3.inputs[1])
                        self.blend.node_tree.links.new(l3.outputs[0], blend_shader.inputs[2])
                        self.blend.node_tree.links.new(l3.outputs[1], blend_disp.inputs[1])
                    if layer4:
                        l4 = self.blend.node_tree.nodes.new(type="ShaderNodeGroup")
                        l4.node_tree = bpy.data.node_groups[layer4.node_tree.name]
                        self.blend.node_tree.links.new(l3.outputs[0], l4.inputs[0])
                        self.blend.node_tree.links.new(l3.outputs[1], l4.inputs[1])
                        self.blend.node_tree.links.new(l4.outputs[0], blend_shader.inputs[2])
                        self.blend.node_tree.links.new(l4.outputs[1], blend_disp.inputs[1])
                    if layer5:
                        l5 = self.blend.node_tree.nodes.new(type="ShaderNodeGroup")
                        l5.node_tree = bpy.data.node_groups[layer5.node_tree.name]
                        self.blend.node_tree.links.new(l4.outputs[0], l5.inputs[0])
                        self.blend.node_tree.links.new(l4.outputs[1], l5.inputs[1])
                        self.blend.node_tree.links.new(l5.outputs[0], blend_shader.inputs[2])
                        self.blend.node_tree.links.new(l5.outputs[1], blend_disp.inputs[1])
                return {"RUNNING_MODAL"}
            if len(sel) > 2:
                msg = "Blending QuickTextures is only supported between exactly two selected objects"
                self.report({'ERROR'}, msg)
        bpy.ops.qt.material_qt("INVOKE_DEFAULT")
        return {"RUNNING_MODAL"}

class QT_OT_material_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.material_qt"
    bl_label = "Create Material"
    bl_description = "Create QuickTexture"
    bl_options = {"PRESET", "UNDO"}

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        ob = bpy.context.active_object
        sel = bpy.context.selected_objects
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            return {"FINISHED"}
        else:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
        img_spec = bpy.data.images[f.name]
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")
        
        if ob and sel:
            textures.create_material(
                ob,
                img_spec,
                self.files,
                dirname,
                fullpath,
                0,
                0
            )
            if bpy.context.window_manager.my_toolqt.multilayer:
                edge_lengths = []
                me = ob.data
                bpy.ops.object.editmode_toggle()
                bm = bmesh.from_edit_mesh(me)
                for e in bm.edges:
                    edge_lengths.append(e.calc_length())
                bpy.ops.object.editmode_toggle()
                min_edge = min(edge_lengths)

                textures.new_layer(
                    ob,
                    img_spec,
                    self.files,
                    dirname,
                    fullpath,
                    layer_type = "Procedural Box"
                )
                mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
                textures.edges_mask(
                    ob,
                    fullpath,
                    mat
                )
                bpy.context.window_manager.my_toolqt.active_map = 1

                nodes = utils.get_nodes(ob)
                mix = nodes[7]
                node_tree = nodes[4]
                layer_out = nodes[5]
                shader = nodes[6]
                diffuse_hue_sat = nodes[24]
                rough_hue_sat = nodes[25]
                bump_strength = nodes[37]
                edge_mask = nodes[41]
                if mix:
                    node_tree.links.new(layer_out.inputs[0], mix.outputs[0])
                else:
                    node_tree.links.new(layer_out.inputs[0], shader.outputs[0])
                bump_strength.inputs[1].default_value = 0
                diffuse_hue_sat.inputs[2].default_value = 1.5
                rough_hue_sat.inputs[2].default_value = 0
                edge_mask.inputs[5].default_value = min_edge
                
                textures.new_layer(
                    ob,
                    img_spec,
                    self.files,
                    dirname,
                    fullpath,
                    layer_type = "Procedural Box"
                )
                textures.dirt_mask(
                    ob,
                    fullpath,
                    mat
                )

                nodes = utils.get_nodes(ob)
                mix = nodes[7]
                node_tree = nodes[4]
                layer_out = nodes[5]
                shader = nodes[6]
                diffuse_hue_sat = nodes[24]
                rough_hue_sat = nodes[25]
                bump_strength = nodes[37]
                dirt_mask = nodes[42]
                if mix:
                    node_tree.links.new(layer_out.inputs[0], mix.outputs[0])
                else:
                    node_tree.links.new(layer_out.inputs[0], shader.outputs[0])
                bump_strength.inputs[1].default_value = 0
                diffuse_hue_sat.inputs[2].default_value = 0.5
                rough_hue_sat.inputs[2].default_value = 1
                dirt_mask.inputs[5].default_value = min_edge * 2

        # create ref plane
        else:
            ob = objects.create_image_plane(self, context, f.name, img_spec)
            layer = ob.data.uv_layers.get("QT_UV_Box_Layer")
            if layer is None:
                uvname = "QT_UV_Box_Layer"
                ob.data.uv_layers.new(name=uvname)
                ob.data.uv_layers[uvname].active = True
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.uv.project_from_view( camera_bounds=False, correct_aspect=True, scale_to_bounds=False )
                bpy.ops.object.editmode_toggle()

            # Procedural UV setup
            empty_uv1 = objects.create_empty( "QT_UV_Z_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv2 = objects.create_empty( "QT_UV_Z_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv3 = objects.create_empty( "QT_UV_Y_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv4 = objects.create_empty( "QT_UV_Y_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv5 = objects.create_empty( "QT_UV_X_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv6 = objects.create_empty( "QT_UV_X_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            col = bpy.data.collections["QuickTexture"]
            objects.add_to_collection(empty_uv1.name, col, context)
            objects.add_to_collection(empty_uv2.name, col, context)
            objects.add_to_collection(empty_uv3.name, col, context)
            objects.add_to_collection(empty_uv4.name, col, context)
            objects.add_to_collection(empty_uv5.name, col, context)
            objects.add_to_collection(empty_uv6.name, col, context)

            # Z
            empty_uv2.rotation_euler.y = math.pi
            empty_uv2.rotation_euler.z = math.pi
            # Y
            empty_uv3.rotation_euler.x = -math.pi / 2
            empty_uv3.rotation_euler.y = math.pi
            empty_uv4.rotation_euler.x = math.pi / 2
            # X
            empty_uv5.rotation_euler.z = math.pi / 2
            empty_uv5.rotation_euler.x = math.pi / 2
            empty_uv6.rotation_euler.z = -math.pi / 2
            empty_uv6.rotation_euler.x = math.pi / 2

            mod = ob.modifiers.get("QT_UV_Box")
            if mod is None:
                rmod1 = ob.modifiers.new(name="QT_UV_Box", type="UV_PROJECT")
                rmod1.projector_count = 6
                rmod1.projectors[0].object = bpy.data.objects[empty_uv1.name]
                rmod1.projectors[1].object = bpy.data.objects[empty_uv2.name]
                rmod1.projectors[2].object = bpy.data.objects[empty_uv3.name]
                rmod1.projectors[3].object = bpy.data.objects[empty_uv4.name]
                rmod1.projectors[4].object = bpy.data.objects[empty_uv5.name]
                rmod1.projectors[5].object = bpy.data.objects[empty_uv6.name]
                rmod1.uv_layer = "QT_UV_Box_Layer"
            bpy.ops.object.select_all(action="DESELECT")
            bpy.data.objects[ob.name].select_set(True)
            bpy.context.view_layer.objects.active = ob
            textures.create_material(
                ob,
                img_spec,
                self.files,
                dirname,
                fullpath,
                1,
                0
            )
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            ob.name = 'QT_Photomodel_' + ob.name
            bpy.context.window_manager.my_toolqt.running_qt = 0
        return {"FINISHED"}

class QT_OT_boxlayer_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.boxlayer_qt"
    bl_label = "New Box Layer"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Box Layer Texture"

    files: CollectionProperty(type=bpy.types.PropertyGroup)
    
    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer >= 5:
            msg = "Maximum Amount of Layers (5) Reached"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        layer = ob.data.uv_layers.get("QT_UV_Box_Layer")
        if not layer:
            uvname = "QT_UV_Box_Layer"
            ob.data.uv_layers.new(name=uvname)
            ob.data.uv_layers[uvname].active = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.project_from_view( camera_bounds=False, correct_aspect=True, scale_to_bounds=False )
            bpy.ops.object.editmode_toggle()

            # Procedural UV setup
            empty_uv1 = objects.create_empty( "QT_UV_Z_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv2 = objects.create_empty( "QT_UV_Z_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv3 = objects.create_empty( "QT_UV_Y_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv4 = objects.create_empty( "QT_UV_Y_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv5 = objects.create_empty( "QT_UV_X_Plus", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            empty_uv6 = objects.create_empty( "QT_UV_X_Min", "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 1 )
            col = bpy.data.collections["QuickTexture"]
            objects.add_to_collection(empty_uv1.name, col, context)
            objects.add_to_collection(empty_uv2.name, col, context)
            objects.add_to_collection(empty_uv3.name, col, context)
            objects.add_to_collection(empty_uv4.name, col, context)
            objects.add_to_collection(empty_uv5.name, col, context)
            objects.add_to_collection(empty_uv6.name, col, context)

            # Z
            empty_uv2.rotation_euler.y = math.pi
            empty_uv2.rotation_euler.z = math.pi
            # Y
            empty_uv3.rotation_euler.x = -math.pi / 2
            empty_uv3.rotation_euler.y = math.pi
            empty_uv4.rotation_euler.x = math.pi / 2
            # X
            empty_uv5.rotation_euler.z = math.pi / 2
            empty_uv5.rotation_euler.x = math.pi / 2
            empty_uv6.rotation_euler.z = -math.pi / 2
            empty_uv6.rotation_euler.x = math.pi / 2

            mod = ob.modifiers.get("QT_UV_Box")
            if mod is None:
                rmod1 = ob.modifiers.new(name="QT_UV_Box", type="UV_PROJECT")
                rmod1.projector_count = 6
                rmod1.projectors[0].object = bpy.data.objects[empty_uv1.name]
                rmod1.projectors[1].object = bpy.data.objects[empty_uv2.name]
                rmod1.projectors[2].object = bpy.data.objects[empty_uv3.name]
                rmod1.projectors[3].object = bpy.data.objects[empty_uv4.name]
                rmod1.projectors[4].object = bpy.data.objects[empty_uv5.name]
                rmod1.projectors[5].object = bpy.data.objects[empty_uv6.name]
                rmod1.uv_layer = "QT_UV_Box_Layer"
            bpy.ops.object.select_all(action="DESELECT")
            bpy.data.objects[ob.name].select_set(True)
            bpy.context.view_layer.objects.active = ob
       
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            return {"FINISHED"}
        else:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
        img_spec = bpy.data.images[f.name]
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")

        textures.new_layer(
            ob,
            img_spec,
            self.files,
            dirname,
            fullpath,
            layer_type = "Procedural Box"
        )
        return {"FINISHED"}

class QT_OT_viewlayer_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.viewlayer_qt"
    bl_label = "New View Layer"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New View Layer Texture"

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer >= 5:
            msg = "Maximum Amount of Layers (5) Reached"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        
        layer2 = None
        layer3 = None
        layer4 = None

        ob2 = None
        ob3 = None
        ob4 = None

        mod2 = ob.modifiers.get("QT_UV_View_2")
        mod3 = ob.modifiers.get("QT_UV_View_3")
        mod4 = ob.modifiers.get("QT_UV_View_4")

        for n in ob.data.uv_layers:
            if n.name.startswith("QT_UV_View_Layer_2"):
                layer2 = n
            if n.name.startswith("QT_UV_View_Layer_3"):
                layer3 = n
            if n.name.startswith("QT_UV_View_Layer_4"):
                layer4 = n

        if bpy.context.window_manager.my_toolqt.active_layer == 2 and layer2:
            # UV
            for n in ob.data.uv_layers:
                if n.name.startswith("QT_UV_View_Layer_4"):
                    n.name = "QT_UV_View_Layer_5"
                if n.name.startswith("QT_UV_View_Layer_3"):
                    n.name = "QT_UV_View_Layer_4"
                if n.name.startswith("QT_UV_View_Layer_2"):
                    n.name = "QT_UV_View_Layer_3"

            # MODIFIERS
            if mod4:
                mod4.name = "QT_UV_View_5"
                mod4.uv_layer = "QT_UV_View_Layer_5"
                ob4 = mod4.projectors[0].object
            if mod3:
                mod3.name = "QT_UV_View_4"
                mod3.uv_layer = "QT_UV_View_Layer_4"
                ob3 = mod3.projectors[0].object
            if mod2:
                mod2.name = "QT_UV_View_3"
                mod2.uv_layer = "QT_UV_View_Layer_3"
                ob2 = mod2.projectors[0].object

            # OBJECTS
            if ob4:
                ob4.name = "QT_UV_View_5"

            if ob3:
                ob3.name = "QT_UV_View_4"

            if ob2:
                ob2.name = "QT_UV_View_3"

        if bpy.context.window_manager.my_toolqt.active_layer == 3 and layer3:
            # UV
            for n in ob.data.uv_layers:
                if n.name.startswith("QT_UV_View_Layer_4"):
                    n.name = "QT_UV_View_Layer_5"
                if n.name.startswith("QT_UV_View_Layer_3"):
                    n.name = "QT_UV_View_Layer_4"

            # MODIFIERS
            if mod4:
                mod4.name = "QT_UV_View_5"
                mod4.uv_layer = "QT_UV_View_Layer_5"
                ob4 = mod4.projectors[0].object
            if mod3:
                mod3.name = "QT_UV_View_4"
                mod3.uv_layer = "QT_UV_View_Layer_4"
                ob3 = mod3.projectors[0].object

            # OBJECTS
            if ob4:
                ob4.name = "QT_UV_View_5"

            if ob3:
                ob3.name = "QT_UV_View_4"

        if bpy.context.window_manager.my_toolqt.active_layer == 4 and layer4:
            # UV
            for n in ob.data.uv_layers:
                if n.name.startswith("QT_UV_View_4"):
                    n.name = "QT_UV_View_5"

            # MODIFIERS
            if mod4:
                mod4.name = "QT_UV_View_5"
                mod4.uv_layer = "QT_UV_View_Layer_5"
                ob4 = mod4.projectors[0].object

            # OBJECTS
            if ob4:
                ob4.name = "QT_UV_View_5"

        uvname = "QT_UV_View_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer+1)
        ob.data.uv_layers.new(name=uvname)
        empty_ob = objects.create_empty( uvname, "SINGLE_ARROW", mathutils.Vector((0, 0, 0)), context, 0 )
        col = bpy.data.collections["QuickTexture"]
        objects.add_to_collection(empty_ob.name, col, context)
        empty_ob.rotation_euler = context.region_data.view_rotation.to_euler()
        local_bbox_center = 0.125 * sum((mathutils.Vector(b) for b in ob.bound_box), mathutils.Vector())
        global_bbox_center = ob.matrix_world @ local_bbox_center
        empty_ob.location = global_bbox_center
        rmod1 = ob.modifiers.new(name=uvname, type="UV_PROJECT")
        rmod1.projector_count = 1
        rmod1.projectors[0].object = bpy.data.objects[empty_ob.name]
        rmod1.uv_layer = "QT_UV_View_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer+1)

        # parenting
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects[empty_ob.name].select_set(True)
        bpy.context.view_layer.objects.active = empty_ob
        bpy.context.object.hide_viewport = False
        bpy.context.object.hide_render = False
        bpy.context.object.hide_select = False
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects[empty_ob.name].select_set(True)
        bpy.context.view_layer.objects.active = empty_ob
        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.parent_set(type="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects[empty_ob.name].select_set(True)
        bpy.context.view_layer.objects.active = empty_ob
        bpy.context.object.hide_viewport = True
        bpy.context.object.hide_render = True
        bpy.context.object.hide_select = True
        bpy.ops.object.select_all(action="DESELECT")

        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            return {"FINISHED"}
        else:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
        img_spec = bpy.data.images[f.name]
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")

        textures.new_layer(
            ob,
            img_spec,
            self.files,
            dirname,
            fullpath,
            layer_type = "View"
        )
        return {"FINISHED"}
    
class QT_OT_triplanar_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.triplanar_qt"
    bl_label = "New Triplanar Layer"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Triplanar Layer Texture"

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer >= 5:
            msg = "Maximum Amount of Layers (5) Reached"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object       
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            return {"FINISHED"}
        else:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
        img_spec = bpy.data.images[f.name]
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")

        textures.new_layer(
            ob,
            img_spec,
            self.files,
            dirname,
            fullpath,
            layer_type = "Triplanar"
        )
        return {"FINISHED"}

class QT_OT_texturemask_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.texturemask_qt"
    bl_label = "Texture Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Texture Mask"

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer == 1:
            msg = "Cannot create Mask on Layer 1"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)        
        if len(self.files) > 0:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]
        
            for mod in addon_utils.modules():
                if mod.bl_info["name"].startswith("QuickTexture"):
                    filepath = mod.__file__
            dirpath = os.path.dirname(filepath)
            fullpath = os.path.join(dirpath, "QT_Presets.blend")

            mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
            textures.texture_mask(
                ob,
                img_spec,
                fullpath,
                mat
            )
        return {"FINISHED"}

class QT_OT_edgesmask_qt(bpy.types.Operator):
    bl_idname = "qt.edgesmask_qt"
    bl_label = "Edges Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Edges Mask"

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer == 1:
            msg = "Cannot create Mask on Layer 1"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")
        
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
        textures.edges_mask(
            ob,
            fullpath,
            mat
        )
        return {"FINISHED"}

class QT_OT_dirtmask_qt(bpy.types.Operator):
    bl_idname = "qt.dirtmask_qt"
    bl_label = "Dirt Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Dirt Mask"

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer == 1:
            msg = "Cannot create Mask on Layer 1"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")
        
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
        textures.dirt_mask(
            ob,
            fullpath,
            mat
        )
        return {"FINISHED"}

class QT_OT_depthmask_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.depthmask_qt"
    bl_label = "Depth Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Depth Mask"

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer == 1:
            msg = "Cannot create Mask on Layer 1"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)        
        if len(self.files) > 0:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]
        
            for mod in addon_utils.modules():
                if mod.bl_info["name"].startswith("QuickTexture"):
                    filepath = mod.__file__
            dirpath = os.path.dirname(filepath)
            fullpath = os.path.join(dirpath, "QT_Presets.blend")

            mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
            textures.depth_mask(
                ob,
                img_spec,
                fullpath,
                mat
            )
        return {"FINISHED"}

class QT_OT_vertexmask_qt(bpy.types.Operator):
    bl_idname = "qt.vertexmask_qt"
    bl_label = "Vertex Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Vertex Mask"

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer == 1:
            msg = "Cannot create Mask on Layer 1"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        
        col = ob.data.color_attributes.active_color
        if col:
            vertex = col.name
            mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
            textures.vertex_mask(
                ob,
                mat,
                vertex
            )
        else:
            msg = "No Color Attributes Detected"
            self.report({'ERROR'}, msg)
        return {"FINISHED"}

class QT_OT_heightmask_qt(bpy.types.Operator):
    bl_idname = "qt.heightmask_qt"
    bl_label = "Height Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Height Mask"

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer == 1:
            msg = "Cannot create Mask on Layer 1"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")
        
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
        textures.height_mask(
            ob,
            fullpath,
            mat
        )
        return {"FINISHED"}

class QT_OT_normalmask_qt(bpy.types.Operator):
    bl_idname = "qt.normalmask_qt"
    bl_label = "Normal Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Normal Mask"

    def execute(self, context):
        if bpy.context.window_manager.my_toolqt.active_layer == 1:
            msg = "Cannot create Mask on Layer 1"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        ob = bpy.context.active_object
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")
        
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
        textures.normal_mask(
            ob,
            fullpath,
            mat
        )
        return {"FINISHED"}

class QT_OT_randomizeperobject_qt(bpy.types.Operator):
    bl_idname = "qt.randomizeperobject_qt"
    bl_label = "Randomize Per Object"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Randomize Per Object"
    
    def execute(self, context):
        ob = bpy.context.active_object
        
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")
        
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
        textures.randomize_per_object(
            ob,
            fullpath,
            mat
        )
        return {"FINISHED"}

class QT_OT_variationmask_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.variationmask_qt"
    bl_label = "Variation Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Variation Mask"
    
    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        ob = bpy.context.active_object
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)        
        if len(self.files) > 0:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]
        
            for mod in addon_utils.modules():
                if mod.bl_info["name"].startswith("QuickTexture"):
                    filepath = mod.__file__
            dirpath = os.path.dirname(filepath)
            fullpath = os.path.join(dirpath, "QT_Presets.blend")

            mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
            textures.variation(
                ob,
                img_spec,
                fullpath,
                mat
            )
        return {"FINISHED"}

class QT_OT_detiling_qt(bpy.types.Operator):
    bl_idname = "qt.detiling_qt"
    bl_label = "Detiling"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Detiling"
    
    def execute(self, context):
        ob = bpy.context.active_object
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
        textures.detiling(
            ob,
            fullpath,
            mat
        )
        return {"FINISHED"}

class QT_OT_smudge_qt(bpy.types.Operator):
    bl_idname = "qt.smudge_qt"
    bl_label = "Smudge Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Smudge Mask"

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects
        ob = sel[0]
        dirname = os.path.dirname(self.filepath)

        if len(self.files) > 0:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]
            width, height = img_spec.size
            bpy.context.window_manager.my_toolqt.active_map = 7
            objects.smudge_mask(
                self,
                context,
                img_spec,
                ob.data.materials[bpy.context.window_manager.my_toolqt.active_material],
                bpy.context.window_manager.my_toolqt.active_layer,
            )
        return {"FINISHED"}

class QT_OT_replacemaps_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.replacemaps"
    bl_label = "Replace Texture"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Replace Texture Maps" 

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        f = self.files[0]
        img_path = os.path.join(dirname, f.name)
        bpy.ops.image.open(filepath=img_path)
        bpy.data.images[f.name].filepath = img_path
        img_spec = bpy.data.images[f.name]

        ob = bpy.context.active_object
        if not ob:
            msg = "Nothing was selected"
            self.report({'WARNING'}, msg)
            return {"FINISHED"}
        
        textures.replace(ob, img_spec, self.files, dirname)
            
        return {"FINISHED"}

class QT_OT_copymats(bpy.types.Operator):
    bl_idname = "qt.copymats"
    bl_label = "Copy Material"
    bl_description = "Select target objects then select source"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        sel = bpy.context.selected_objects
        if not obj or not sel:
            msg = "Select a Target and Source object to Copy Material"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        # convert to geo if curve
        ob = sel[-1]
        act = bpy.context.view_layer.objects.active

        bpy.ops.object.select_all(action="DESELECT")
        for ob in sel:
            if ob.type == 'CURVE':
                bpy.context.view_layer.objects.active = ob
                bpy.data.objects[ob.name].select_set(True)
                bpy.ops.object.convert(target="MESH")

        for ob in sel:
            bpy.context.view_layer.objects.active = ob
            bpy.data.objects[ob.name].select_set(True)
        sel = bpy.context.selected_objects

        bpy.context.view_layer.objects.active = act

        bpy.ops.object.make_links_data(type="MATERIAL")

        if bpy.context.window_manager.my_toolqt.makeunique:
            sel = bpy.context.selected_objects
            for ob in sel:
                if ob != act:
                    mat = ob.active_material
                    if mat:
                        if mat.name.startswith("QT"):
                            ob.active_material = mat.copy()
                            for n in ob.active_material.node_tree.nodes:
                                if n.type == 'GROUP':
                                    original_group = n.node_tree
                                    single_user_group = original_group.copy()
                                    n.node_tree = single_user_group
                                    for nn in n.node_tree.nodes:
                                        if nn.type == 'GROUP':
                                            original_group = nn.node_tree
                                            single_user_group = original_group.copy()
                                            nn.node_tree = single_user_group

        procuvs = 0
        for layer in act.data.uv_layers:
            if layer.name.startswith("QT_UV"):
                procuvs = 1

        if procuvs:
            bpy.ops.object.select_all(action="DESELECT")

            for ob in sel:
                if ob != act:
                    bpy.context.view_layer.objects.active = ob
                    bpy.data.objects[ob.name].select_set(True)

                    box1 = None
                    layer1 = None
                    layer2 = None
                    layer3 = None
                    layer4 = None
                    layer5 = None

                    box1 = act.data.uv_layers.get("QT_UV_Box_Layer")
                    layer1 = act.data.uv_layers.get("QT_UV_View_Layer_1")
                    layer2 = act.data.uv_layers.get("QT_UV_View_Layer_2")
                    layer3 = act.data.uv_layers.get("QT_UV_View_Layer_3")
                    layer4 = act.data.uv_layers.get("QT_UV_View_Layer_4")
                    layer5 = act.data.uv_layers.get("QT_UV_View_Layer_5")

                    if layer1:
                        check = ob.data.uv_layers.get("QT_UV_View_Layer_1")
                        if not check:
                            uvname = "QT_UV_View_Layer_1"
                            ob.data.uv_layers.new(name=uvname)
                            ob.data.uv_layers[uvname].active = True
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.select_all(action="SELECT")
                            bpy.ops.uv.project_from_view(
                                camera_bounds=False,
                                correct_aspect=True,
                                scale_to_bounds=False,
                            )
                            bpy.ops.object.editmode_toggle()

                    if layer2:
                        check = ob.data.uv_layers.get("QT_UV_View_Layer_2")
                        if not check:
                            uvname = "QT_UV_View_Layer_2"
                            ob.data.uv_layers.new(name=uvname)
                            ob.data.uv_layers[uvname].active = True
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.select_all(action="SELECT")
                            bpy.ops.uv.project_from_view(
                                camera_bounds=False,
                                correct_aspect=True,
                                scale_to_bounds=False,
                            )
                            bpy.ops.object.editmode_toggle()

                    if layer3:
                        check = ob.data.uv_layers.get("QT_UV_View_Layer_3")
                        if not check:
                            uvname = "QT_UV_View_Layer_3"
                            ob.data.uv_layers.new(name=uvname)
                            ob.data.uv_layers[uvname].active = True
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.select_all(action="SELECT")
                            bpy.ops.uv.project_from_view(
                                camera_bounds=False,
                                correct_aspect=True,
                                scale_to_bounds=False,
                            )
                            bpy.ops.object.editmode_toggle()

                    if layer4:
                        check = ob.data.uv_layers.get("QT_UV_View_Layer_4")
                        if not check:
                            uvname = "QT_UV_View_Layer_4"
                            ob.data.uv_layers.new(name=uvname)
                            ob.data.uv_layers[uvname].active = True
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.select_all(action="SELECT")
                            bpy.ops.uv.project_from_view(
                                camera_bounds=False,
                                correct_aspect=True,
                                scale_to_bounds=False,
                            )
                            bpy.ops.object.editmode_toggle()

                    if layer5:
                        check = ob.data.uv_layers.get("QT_UV_View_Layer_5")
                        if not check:
                            uvname = "QT_UV_View_Layer_5"
                            ob.data.uv_layers.new(name=uvname)
                            ob.data.uv_layers[uvname].active = True
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.select_all(action="SELECT")
                            bpy.ops.uv.project_from_view(
                                camera_bounds=False,
                                correct_aspect=True,
                                scale_to_bounds=False,
                            )
                            bpy.ops.object.editmode_toggle()

                    if box1:
                        check = ob.data.uv_layers.get("QT_UV_Box_Layer")
                        if not check:
                            uvname = "QT_UV_Box_Layer"
                            ob.data.uv_layers.new(name=uvname)
                            ob.data.uv_layers[uvname].active = True
                            bpy.ops.object.editmode_toggle()
                            bpy.ops.mesh.select_all(action="SELECT")
                            bpy.ops.uv.project_from_view(
                                camera_bounds=False,
                                correct_aspect=True,
                                scale_to_bounds=False,
                            )
                            bpy.ops.object.editmode_toggle()

                    boxmod1 = None
                    mod1 = None
                    mod2 = None
                    mod3 = None
                    mod4 = None
                    mod5 = None

                    modobj1a = None
                    modobj1b = None
                    modobj1c = None
                    modobj1d = None
                    modobj1e = None
                    modobj1f = None

                    modobj2 = None
                    modobj3 = None
                    modobj4 = None
                    modobj5 = None

                    boxmod1 = act.modifiers.get("QT_UV_Box")
                    mod1 = act.modifiers.get("QT_UV_View_1")
                    mod2 = act.modifiers.get("QT_UV_View_Layer_2")
                    mod3 = act.modifiers.get("QT_UV_View_Layer_3")
                    mod4 = act.modifiers.get("QT_UV_View_Layer_4")
                    mod5 = act.modifiers.get("QT_UV_View_Layer_5")

                    if boxmod1:
                        modobj1a = boxmod1.projectors[0].object
                        modobj1b = boxmod1.projectors[1].object
                        modobj1c = boxmod1.projectors[2].object
                        modobj1d = boxmod1.projectors[3].object
                        modobj1e = boxmod1.projectors[4].object
                        modobj1f = boxmod1.projectors[5].object

                    if mod1:
                        modobj2 = mod1.projectors[0].object

                    if mod2:
                        modobj3 = mod2.projectors[0].object

                    if mod3:
                        modobj4 = mod3.projectors[0].object

                    if mod4:
                        modobj5 = mod4.projectors[0].object

                    if mod5:
                        modobj6 = mod5.projectors[0].object

                    boxmod1_check = ob.modifiers.get("QT_UV_Box")
                    mod1_check = ob.modifiers.get("QT_UV_View_1")
                    mod2_check = ob.modifiers.get("QT_UV_View_Layer_2")
                    mod3_check = ob.modifiers.get("QT_UV_View_Layer_3")
                    mod4_check = ob.modifiers.get("QT_UV_View_Layer_4")
                    mod5_check = ob.modifiers.get("QT_UV_View_Layer_5")

                    if not boxmod1_check:
                        if boxmod1:
                            rmod1 = ob.modifiers.new(
                                name="QT_UV_Box", type="UV_PROJECT"
                            )
                            rmod1.projector_count = 6
                            rmod1.projectors[0].object = modobj1a
                            rmod1.projectors[1].object = modobj1b
                            rmod1.projectors[2].object = modobj1c
                            rmod1.projectors[3].object = modobj1d
                            rmod1.projectors[4].object = modobj1e
                            rmod1.projectors[5].object = modobj1f
                            rmod1.uv_layer = "QT_UV_Box_Layer"

                    if not mod1_check:
                        if mod1:
                            rmod1 = ob.modifiers.new(
                                name="QT_UV_View_1", type="UV_PROJECT"
                            )
                            rmod1.projector_count = 1
                            rmod1.projectors[0].object = modobj2
                            rmod1.uv_layer = "QT_UV_View_Layer_1"

                    if not mod2_check:
                        if mod2:
                            rmod1 = ob.modifiers.new(
                                name="QT_UV_View_Layer_2", type="UV_PROJECT"
                            )
                            rmod1.projector_count = 1
                            rmod1.projectors[0].object = modobj3
                            rmod1.uv_layer = "QT_UV_View_Layer_2"

                    if not mod3_check:
                        if mod3:
                            rmod1 = ob.modifiers.new(
                                name="QT_UV_View_Layer_3", type="UV_PROJECT"
                            )
                            rmod1.projector_count = 1
                            rmod1.projectors[0].object = modobj4
                            rmod1.uv_layer = "QT_UV_View_Layer_3"

                    if not mod4_check:
                        if mod4:
                            rmod1 = ob.modifiers.new(
                                name="QT_UV_View_Layer_4", type="UV_PROJECT"
                            )
                            rmod1.projector_count = 1
                            rmod1.projectors[0].object = modobj5
                            rmod1.uv_layer = "QT_UV_View_Layer_4"

                    if not mod5_check:
                        if mod5:
                            rmod1 = ob.modifiers.new(
                                name="QT_UV_View_Layer_5", type="UV_PROJECT"
                            )
                            rmod1.projector_count = 1
                            rmod1.projectors[0].object = modobj6
                            rmod1.uv_layer = "QT_UV_View_Layer_5"

        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = act
        bpy.data.objects[act.name].select_set(True)
        return {"FINISHED"}
    
class QT_OT_resetmaterial(bpy.types.Operator):
    bl_idname = "qt.resetmaterial"
    bl_label = "Reset Material"
    bl_description = "Reset Material and all QuickTexture related attributes on the object for a clean slate"
    bl_options = {"PRESET", "UNDO"}
    
    def execute(self, context):
        ob = bpy.context.active_object
        if not ob:
            msg = "No Object Was Selected"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}
        sel = bpy.context.selected_objects
        for ob in sel:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            if ob.data.materials:
                for mat in ob.data.materials:
                    bpy.ops.object.material_slot_remove()
                uvs = [uv for uv in ob.data.uv_layers]
                while uvs:
                    ob.data.uv_layers.remove(uvs.pop())
                ob.modifiers.clear()
        return {"FINISHED"}

class QT_OT_makeunique(bpy.types.Operator):
    bl_idname = "qt.makeunique"
    bl_label = "Make Material Unique"
    bl_description = "Make Unique"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            msg = "No Object Was Selected"
            self.report({'ERROR'}, msg)
            return {"FINISHED"}

        sel = bpy.context.selected_objects
        for ob in sel:
            mat = ob.active_material
            if mat:
                if mat.name.startswith("QT"):
                    ob.active_material = mat.copy()
                    for n in ob.active_material.node_tree.nodes:
                        if n.type == 'GROUP':
                            original_group = n.node_tree
                            single_user_group = original_group.copy()
                            n.node_tree = single_user_group
                            for nn in n.node_tree.nodes:
                                if nn.type == 'GROUP':
                                    original_group = nn.node_tree
                                    single_user_group = original_group.copy()
                                    nn.node_tree = single_user_group
        return {"FINISHED"}

class quickTextureDecal(bpy.types.Operator):
    bl_idname = "object.quicktexturedecal"
    bl_label = "QuickDecal"
    bl_description = "Create QuickTexture Mesh Decal"
    bl_options = {"REGISTER", "UNDO"}

    def modal(self, context, event):
        return {"FINISHED"}

    def invoke(self, context, event):
        ob = bpy.context.active_object
        if ob.type not in {"MESH", "CURVE"}:
            self.report({"ERROR"}, "Decals can only be projected onto Mesh or Curve Objects")
            bpy.ops.object.select_all(action="DESELECT")
            return {"FINISHED"}
        
        bpy.context.window_manager.my_toolqt.decal_coord = ((event.mouse_region_x, event.mouse_region_y, 0))
        bpy.ops.qt.decal_qt("INVOKE_DEFAULT")
        return {"RUNNING_MODAL"}

class QT_OT_decal_qt(bpy.types.Operator, ImportHelper):
    bl_idname = "qt.decal_qt"
    bl_label = "Create Decal Material"
    bl_description = "Create QuickTexture Mesh Decal"
    bl_options = {"PRESET", "UNDO"}

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.running_qt = 0
        dirname = os.path.dirname(self.filepath)

        ob = bpy.context.active_object
        sel = bpy.context.selected_objects

        for f in self.files:
            if len(self.files) == 0:
                return {"FINISHED"}
            else:
                f = self.files[0]
                img_path = os.path.join(dirname, f.name)
                bpy.ops.image.open(filepath=img_path)
                bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]

        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")

        # create decal
        if sel:
            ob = objects.create_decal( self, context, sel, img_spec)
            textures.create_material(ob, img_spec, self.files, dirname, fullpath, 0, 1)
            bpy.ops.object.select_all(action="DESELECT")
            bpy.data.objects[ob.name].select_set(True)
            bpy.context.view_layer.objects.active = ob

            # setup decal position
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            reg = context.region
            rv3d = context.region_data
            coord = (bpy.context.window_manager.my_toolqt.decal_coord[0], bpy.context.window_manager.my_toolqt.decal_coord[1])
            ray = utils.ray_cast(reg, rv3d, coord, context)
            view_vector = mathutils.Vector((rv3d.perspective_matrix[2][0:3])).normalized()
            if ray[0]:
                hit_loc = ray[0]
                ob.location = (hit_loc + view_vector * -3)
            else:
                ob.location = (ob.location + view_vector * -10)
                self.report({"WARNING"}, "Projection missed. Place your mouse cursor over an object when creating a QuickDecal and try again")

            # setup alpha border
            colattr = ob.data.color_attributes.new(
                name = 'QT_Decal_Alpha',
                type = 'FLOAT_COLOR',
                domain = 'POINT',
            )
            cols = []
            for v_index in range(len(ob.data.vertices)):
                cols += [0,0,0,1]
            colattr.data.foreach_set("color", cols)

            # geo node modifier
            if len(sel) > 0:
                with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
                    data_to.node_groups = [
                        name for name in data_from.node_groups if name.startswith("QT_Decal")
                    ]

                geomod = ob.modifiers.new(name="QT_Decal", type="NODES")
                original_group = bpy.data.node_groups["QT_Decal"]
                single_user_group = original_group.copy()
                geomod.node_group = single_user_group

                node_tree = bpy.data.node_groups[geomod.node_group.name]
                for n in node_tree.nodes:
                    if n.name == "Join Geometry":
                        node_join = n

                for i in range(len(sel)):
                    node_object = node_tree.nodes.new("GeometryNodeObjectInfo")
                    node_object.transform_space = "RELATIVE"
                    node_object.inputs[0].default_value = sel[i]
                    node_tree.links.new(node_object.outputs[3], node_join.inputs[0])

                geomod["Input_2"] = bpy.context.window_manager.my_toolqt.res
                geomod["Input_3"] = bpy.context.window_manager.my_toolqt.offset
                if ray[0]:
                    geomod["Input_13"] = True
                else:
                    geomod["Input_13"] = False

                # parenting
                bpy.context.view_layer.objects.active = sel[0]
                bpy.data.objects[ob.name].select_set(True)
                bpy.data.objects[sel[0].name].select_set(True)

                bpy.ops.object.parent_set(type="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")

            bpy.data.objects[ob.name].select_set(True)
            bpy.context.view_layer.objects.active = ob

            bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS", center="MEDIAN")
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        # create ref
        else:
            ob = objects.create_image_plane(self, context, f.name, img_spec)
            ob.name = 'QT_Ref_' + ob.name
            textures.create_material(
                ob,
                img_spec,
                self.files,
                dirname,
                fullpath,
                0,
                1
            )
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.context.window_manager.my_toolqt.running_qt = 0
        return {"FINISHED"}

class quickTexturePaintover(bpy.types.Operator):
    bl_idname = "object.quicktexturepaintover"
    bl_label = "QuickPaintover"
    bl_description = "Create QuickTexture Paintover by selecting the objects you want to paint over and the camera you want to project from"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        ob = bpy.context.active_object
        sel = bpy.context.selected_objects
        view_perspective = None

        cam = bpy.context.scene.camera
        if not cam:
            self.report({"ERROR"}, "You must have an active scene camera and be looking through it to Paintover")

        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                view_perspective = a.spaces[0].region_3d.view_perspective

        if not view_perspective == 'CAMERA':
            self.report({"ERROR"}, "You must be looking through a Camera to Paintover")
            return {"FINISHED"}

        for obj in sel:
            if obj.type not in {"MESH", "CURVE"}:
                self.report({"ERROR"}, "Select only Mesh or Curve Objects to Paintover")
                bpy.ops.object.select_all(action="DESELECT")
                return {"FINISHED"}

        if not ob and not sel:
            self.report({"ERROR"}, "Select Mesh or Curve Objects to Paintover")
            return {"FINISHED"}

        if not bpy.context.preferences.filepaths.image_editor:
            self.report({"ERROR"}, "Image Editor .EXE file location not set in Addon Preferences")
            return {"FINISHED"}
        
        bpy.context.window_manager.my_toolqt.decal_coord = ((event.mouse_region_x, event.mouse_region_y, 0))
        bpy.ops.qt.paintover_qt("INVOKE_DEFAULT")
        return {"FINISHED"}

class QT_OT_paintover_qt(bpy.types.Operator):
    bl_idname = "qt.paintover_qt"
    bl_label = "Create Paintover"
    bl_description = "Create QuickTexture Paintover Object"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.running_qt = 0

        sel = bpy.context.selected_objects
        cam = bpy.context.scene.camera
        paintover = None
        geomod = None

        region = bpy.context.region
        width = region.width
        height = region.height
        rv3d = context.region_data
        view_vector = mathutils.Vector((rv3d.perspective_matrix[2][0:3])).normalized()
        hit_loc, bounding_box_corners = utils.find_closest_bounding_point(sel, cam.location)

        min_bbox = min(bounding_box_corners)
        max_bbox = max(bounding_box_corners)
        dist = (mathutils.Vector((max_bbox)) - mathutils.Vector((min_bbox))).length

        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__
        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")

        hit = hit_loc + view_vector * -1
        depth = (cam.location - hit).length * 1

        for obj in sel:
            if obj.name.startswith("QT_Paintover"):
                paintover = obj

        if paintover:
            geomod = None
            bpy.ops.object.duplicate()
            paintover = bpy.context.active_object
            bpy.data.objects[paintover.name].select_set(True)
            for mat in paintover.data.materials:
                bpy.ops.object.material_slot_remove()
            for mod in paintover.modifiers:
                if mod.name.startswith("QT_Decal"):
                    geomod = mod
                    break
            if geomod:
                copy = geomod.node_group.copy()
                geomod.node_group = copy
                geomod["Input_3"] *= 1.1
        else:
            paintover = objects.create_paintover(cam, depth)

            dim_max = max(paintover.dimensions)
            fac = dist / dim_max
            if dist > dim_max:
                paintover.scale *= fac

            # geo nodes
            with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
                data_to.node_groups = [
                    name for name in data_from.node_groups if name.startswith("QT_Decal")
                ]

            geomod = paintover.modifiers.new(name="QT_Decal", type="NODES")
            original_group = bpy.data.node_groups["QT_Decal"]
            single_user_group = original_group.copy()
            geomod.node_group = single_user_group

            node_tree = bpy.data.node_groups[geomod.node_group.name]
            for n in node_tree.nodes:
                if n.name == "Join Geometry":
                    node_join = n

            singlesided = None
            for obj in sel:
                node_object = node_tree.nodes.new("GeometryNodeObjectInfo")
                node_object.transform_space = "RELATIVE"
                node_object.inputs[0].default_value = obj
                node_tree.links.new(node_object.outputs[3], node_join.inputs[0])

                if obj.dimensions[0] < 0.0001 or obj.dimensions[1] < 0.0001 or obj.dimensions[2] < 0.0001:
                    singlesided = True

            # temp fix because geo nodes does weird things when raycasting and deleting misses on single sided objects
            if not singlesided:
                geomod["Input_13"] = True

            geomod["Input_2"] = bpy.context.window_manager.my_toolqt.paintover_res
            geomod["Input_3"] = bpy.context.window_manager.my_toolqt.paintover_offset

        textures.create_paintover(paintover, fullpath, width, height)
        bpy.ops.object.mode_set(mode="OBJECT")

        if geomod:
            geomod.show_viewport = 0
            bpy.ops.paint.texture_paint_toggle()
            bpy.ops.paint.brush_select(image_tool='FILL')
            strokes = [{
                "name": "",
                "location": (0, 0, 0),
                "mouse": (0, 0),
                "mouse_event": (0,0),
                "x_tilt": 0,
                "y_tilt": 0,
                "size": 100,
                "pressure": 1,
                "pen_flip": False,
                "time": 0,
                "is_start": True
                }]
            bpy.ops.paint.image_paint(stroke=strokes)
            geomod.show_viewport = 1

        res = bpy.context.window_manager.my_toolqt.paintover
        bpy.context.scene.tool_settings.image_paint.screen_grab_size[0] = width * res
        bpy.context.scene.tool_settings.image_paint.screen_grab_size[1] = height * res
        paintover.hide_set(True)
        bpy.ops.image.project_edit()
        paintover.hide_set(False)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.data.objects[paintover.name].select_set(True)
        bpy.data.objects[paintover.name].select_set(True)
        self.report({"INFO"}, "Remember to save a SINGLE LAYER file in your image editor then Apply Paintover")
        return {"FINISHED"}

class QT_OT_apply_paintover_qt(bpy.types.Operator):
    bl_idname = "qt.apply_paintover_qt"
    bl_label = "Apply Paintover"
    bl_description = "Apply Paintover will update the texture of the Paintover Object. Ensure Image Editor file is merged down to ONE layer"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.running_qt = 0
        ob = bpy.context.active_object

        if not ob:
            self.report({"ERROR"}, "Select a QuickPaintover Object")
            return {"FINISHED"}

        if not ob.name.startswith("QT_Paintover"):
            self.report({"ERROR"}, "Select a QuickPaintover Object")
            return {"FINISHED"}

        if ob.type not in {"MESH", "CURVE"}:
            self.report({"ERROR"}, "Select a QuickPaintover Object")
            bpy.ops.object.select_all(action="DESELECT")
            return {"FINISHED"}

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.paint.texture_paint_toggle()
        bpy.ops.image.project_apply()
        bpy.ops.object.mode_set(mode="OBJECT")
        for image in bpy.data.images:
            if image.name.startswith("QT_Paintover"):
                image.pack()
        self.report({"INFO"}, "Paintover Applied")
        return {"FINISHED"}

class bakeTextures(bpy.types.Operator):
    bl_idname = "wm.baketextures"
    bl_label = "Bake QuickTexture"
    bl_description = "Bake All Textures"
    bl_options = {"PRESET", "UNDO"}

    _timer = None
    _mat = None
    _render = None
    _samples = None

    @classmethod
    def poll(cls, context):
        if not bpy.context.window_manager.my_toolqt.in_bake_preview:
            return True

    def Bake(self, context):
        yield 1

        obj = context.active_object
        if obj and len(obj.data.materials) > 0:
            node_tree = None
            self._mat = obj.data.materials[0]
            node_tree = self._mat.node_tree
            maps = ["DIFFUSE", "ROUGHNESS", "NORMAL", "METAL", "ALPHA"]
            metal_tex = None

            for bake in maps:
                sel = bpy.context.selected_objects
                if len(sel) > 1:
                    bpy.context.scene.render.bake.use_selected_to_active = True

                for n in node_tree.nodes:
                    if n.type == 'GROUP':
                        if n.name.startswith("QT_Layer"):
                            layer = n
                            shader = n.node_tree.nodes.get("QT_Shader")
                            metal_tex = n.node_tree.nodes.get("QT_Metal_Tex")
                            metal_invert = n.node_tree.nodes.get("QT_Metal_Invert")
                            alpha_clamp = n.node_tree.nodes.get("QT_Alpha_Clamp")
                            for link in shader.inputs[1].links:
                                n.node_tree.links.remove(link)
                            if bake == 'METAL':
                                layer.node_tree.links.new(metal_invert.outputs[0], shader.inputs[2])
                            if bake == 'ALPHA':
                                layer.node_tree.links.new(alpha_clamp.outputs[0], shader.inputs[2])

                if bake == 'METAL':
                    if metal_tex:
                        if not metal_tex.image:
                            continue
                
                # prepare bake node
                bake_spec = ( bpy.context.window_manager.my_toolqt.bakename + "_" + bake + ".png" )
                bake_path = os.path.join( bpy.context.window_manager.my_toolqt.bakepath, bake_spec )
                bake_node = node_tree.nodes.new("ShaderNodeTexImage")
                bake_image = bpy.data.images.new(
                    bake_spec,
                    bpy.context.window_manager.my_toolqt.bakeres,
                    bpy.context.window_manager.my_toolqt.bakeres,
                )
                bake_node.image = bake_image
                bake_node.select = True
                node_tree.nodes.active = bake_node
                bake_node.show_texture = True

                uv_node = node_tree.nodes.new("ShaderNodeUVMap")
                uv_node.uv_map = obj.data.uv_layers[0].name
                node_tree.links.new(uv_node.outputs[0], bake_node.inputs[0])

                # multi material
                for x in range(len(obj.data.materials)):
                    if x > 1:
                        img_node = obj.data.materials[x].node_tree.nodes.new( "ShaderNodeTexImage" )
                        img_node.image = bake_image
                        img_node.select = True
                        obj.data.materials[x].node_tree.nodes.active = img_node
                        img_node.show_texture = True
                
                if bake == 'DIFFUSE':
                    bpy.context.scene.render.bake.use_pass_indirect = False
                    bpy.context.scene.render.bake.use_pass_direct = False
                    while bpy.ops.object.bake("INVOKE_DEFAULT", type='DIFFUSE') != { "RUNNING_MODAL" }:
                        yield 1
                elif bake == 'ROUGHNESS':
                    bake_node.image.colorspace_settings.name = "Non-Color"
                    while bpy.ops.object.bake("INVOKE_DEFAULT", type='ROUGHNESS') != { "RUNNING_MODAL" }:
                        yield 1
                elif bake == 'NORMAL':
                    while bpy.ops.object.bake("INVOKE_DEFAULT", type='NORMAL') != { "RUNNING_MODAL" }:
                        yield 1
                elif bake == 'METAL':
                    bake_node.image.colorspace_settings.name = "Non-Color"
                    while bpy.ops.object.bake("INVOKE_DEFAULT", type='ROUGHNESS') != { "RUNNING_MODAL" }:
                        yield 1
                elif bake == 'ALPHA':
                    bake_node.image.colorspace_settings.name = "Non-Color"
                    while bpy.ops.object.bake("INVOKE_DEFAULT", type='ROUGHNESS') != { "RUNNING_MODAL" }:
                        yield 1

                # bake
                while not bake_image.is_dirty:
                    yield 1
                bake_image.save_render(filepath=bake_path)
                bpy.data.images.remove(bake_image)
                node_tree.nodes.remove(bake_node)
                node_tree.nodes.remove(uv_node)
        yield 0

    def modal(self, context, event):
        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.report({"INFO"}, "Baking map cancelled")
            return {"CANCELLED"}

        if event.type == "TIMER":

            result = next(self.BakeCrt)

            if result == -1:
                self.report({"INFO"}, "Baking map cancelled")
                return {"CANCELLED"}

            if result == 0:
                # finish
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                self.report({"INFO"}, "Baking map completed")

                self._mat.name = bpy.context.window_manager.my_toolqt.bakename
                obj = context.active_object

                # remove other uvs
                uvs = [ uv for uv in obj.data.uv_layers if uv != obj.data.uv_layers.active ]
                while uvs:
                    obj.data.uv_layers.remove(uvs.pop())

                # remove other mats
                for i, mat in reversed(list(enumerate(obj.data.materials))):
                    obj.data.materials.pop(index=i)
                obj.data.materials.append(self._mat)

                # create basic non QT mat with baked textures - user can always remake it as QT
                textures.baked_material(self._mat.node_tree)

                context.scene.render.engine = self._render
                bpy.context.scene.cycles.samples = self._samples
                return {"FINISHED"}
        return {"PASS_THROUGH"}

    def execute(self, context: bpy.context):
        if bpy.data.is_saved:
            abs_filepath = bpy.path.abspath('//')
            if not os.path.isdir(str(abs_filepath+"textures")):
                os.mkdir(str(abs_filepath+"textures"))

        if not context.active_object.select_get() or not context.active_object.type == "MESH":
            self.report({"WARNING"}, "No valid selected objects")
            return {"FINISHED"}

        if not len(str(bpy.context.window_manager.my_toolqt.bakepath)) > 0:
            if bpy.data.is_saved:
                abs_filepath = bpy.path.abspath('//')
                if not os.path.isdir(str(abs_filepath+"QT_Textures")):
                    os.mkdir(str(abs_filepath+"QT_Textures"))
                else:
                    bpy.context.window_manager.my_toolqt.bakepath = str(abs_filepath+"QT_Textures")
            else:
                self.report({"WARNING"}, "Select baking file path")
                return {"FINISHED"}

        if not len(str(bpy.context.window_manager.my_toolqt.bakename)) > 0:
            self.report({"WARNING"}, "Select baking file name")
            return {"FINISHED"}

        ob = bpy.context.active_object
        mat = ob.active_material

        if not mat:
            self.report({"WARNING"}, "Selected Object has No Materials")
            return {"FINISHED"}

        if not mat.name.startswith("QT_"):
            self.report({"WARNING"}, "Baking only works on QuickTextures")
            return {"FINISHED"}

        # unique mat first
        if bpy.context.window_manager.my_toolqt.save_original_mat:
            if mat and mat.name.startswith("QT"):
                ob.active_material = mat.copy()
                for n in ob.active_material.node_tree.nodes:
                    if n.type == 'GROUP':
                        original_group = n.node_tree
                        single_user_group = original_group.copy()
                        n.node_tree = single_user_group
                        for nn in n.node_tree.nodes:
                            if nn.type == 'GROUP':
                                original_group = nn.node_tree
                                single_user_group = original_group.copy()
                                nn.node_tree = single_user_group

        # store settings
        self._samples = bpy.context.scene.cycles.samples
        self._render = context.scene.render.engine

        # settings
        if context.scene.render.engine != "CYCLES":
            context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.samples = bpy.context.window_manager.my_toolqt.samples
        bpy.context.scene.render.image_settings.file_format = 'PNG'

        # prepare
        bpy.ops.object.convert(target="MESH")

        uv = 0
        mat = ob.data.materials[0]
        layer = mat.node_tree.nodes.get("QT_Layer_1")
        if layer:
            coord = layer.node_tree.nodes.get("QT_Coord") 
            if coord.label == 'UV':
                uv = 1
                bpy.context.object.data.uv_layers[0].active = True
                bpy.context.object.data.uv_layers[0].active_render = True

        if not uv:
            bpy.context.active_object.data.uv_layers.new(name="QT_SmartUVMap")
            bpy.context.object.data.uv_layers["QT_SmartUVMap"].active = True
            bpy.context.object.data.uv_layers["QT_SmartUVMap"].active_render = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project()
            bpy.ops.object.editmode_toggle()

        # modal
        self.BakeCrt = self.Bake(context)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

class previewTextures(bpy.types.Operator):
    bl_idname = "wm.previewtextures"
    bl_label = "Preview Dirt and Edges"
    bl_description = "Preview Dirt and Edges"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context: bpy.context):
        if not context.active_object.select_get() or not context.active_object.type == "MESH":
            self.report({"WARNING"}, "No valid selected objects")
            return {"FINISHED"}

        obj = context.active_object
        mat = obj.active_material
        create = 1

        if mat:
            if mat.name.startswith("QT_Preview"):
                obj.active_material = bpy.context.window_manager.my_toolqt.preview_mat
                if bpy.context.window_manager.my_toolqt.render_engine:
                    context.scene.render.engine = "CYCLES"
                else:
                    context.scene.render.engine = "BLENDER_EEVEE"
                    bpy.context.window_manager.my_toolqt.render_engine = 0
                bpy.context.window_manager.my_toolqt.in_bake_preview = 0
                create = 0
            else:
                create = 1
        else:
            create = 1

        if create:
            bpy.context.window_manager.my_toolqt.preview_mat = mat
            bpy.context.window_manager.my_toolqt.in_bake_preview = 1

            # import preview mat and set it
            filepath = None
            for mod in addon_utils.modules():
                if mod.bl_info["name"].startswith("QuickTexture"):
                    filepath = mod.__file__
            dirpath = os.path.dirname(filepath)
            fullpath = os.path.join(dirpath, "QT_Presets.blend")
            with bpy.data.libraries.load(fullpath, link=False) as (
                data_from,
                data_to,
            ):
                data_to.materials = [
                    name
                    for name in data_from.materials
                    if name.startswith("QT_Preview")
                ]

            preview_mat = bpy.data.materials["QT_Preview"]
            obj.active_material = preview_mat

            if context.scene.render.engine == "CYCLES":
                bpy.context.window_manager.my_toolqt.render_engine = 1
            else:
                bpy.context.window_manager.my_toolqt.render_engine = 0

            if context.scene.render.engine != "CYCLES":
                context.scene.render.engine = "CYCLES"
        return {"FINISHED"}

class bakePreviewTextures(bpy.types.Operator):
    bl_idname = "wm.bakepreviewtextures"
    bl_label = "Bake Dirt and Edges Masks"
    bl_description = "Bake Dirt and Edges Masks"
    bl_options = {"PRESET", "UNDO"}

    _timer = None
    _mat = None

    _render = None
    _samples = None

    @classmethod
    def poll(cls, context):
        if bpy.context.window_manager.my_toolqt.in_bake_preview:
            return True

    def Bake(self, context):
        yield 1

        obj = context.active_object

        uvmap = None
        if len(obj.data.uv_layers) > 0:
            for layer in obj.data.uv_layers:
                uvmap = layer

        if obj and len(obj.data.materials) > 0:
            node_tree = None
            self._mat = obj.active_material
            node_tree = self._mat.node_tree
            maplist = ["Dirt", "Edges"]

            for i in range(len(maplist)):

                bake_spec = ( bpy.context.window_manager.my_toolqt.bakename + "_" + maplist[i] + ".png" )
                bake_spec = "QT_" + obj.name + "_" + maplist[i] + ".png"
                bake_path = os.path.join(
                    bpy.context.window_manager.my_toolqt.bakepath, bake_spec
                )
                bake_node = node_tree.nodes.new("ShaderNodeTexImage")
                bake_image = bpy.data.images.new(
                    bake_spec,
                    bpy.context.window_manager.my_toolqt.bakeres,
                    bpy.context.window_manager.my_toolqt.bakeres,
                )
                bake_node.image = bake_image
                bake_node.select = True
                node_tree.nodes.active = bake_node
                bake_node.show_texture = True

                uv_node = node_tree.nodes.new("ShaderNodeUVMap")
                uv_node.uv_map = uvmap.name
                node_tree.links.new(uv_node.outputs[0], bake_node.inputs[0])

                for n in node_tree.nodes:
                    if n.name == "Shader_Edges":
                        edges = n
                    if n.name == "Shader_Dirt":
                        dirt = n
                    if n.name == "Material Output":
                        out = n
                    if n.name == "Vector Math":
                        combined = n

                if i == 0:
                    node_tree.links.new(dirt.outputs[0], out.inputs[0])
                else:
                    node_tree.links.new(edges.outputs[0], out.inputs[0])

                node_tree.links.new(uv_node.outputs[0], bake_node.inputs[0])

                while bpy.ops.object.bake("INVOKE_DEFAULT", type='EMIT') != { "RUNNING_MODAL" }:
                    yield 1
                while not bake_image.is_dirty:
                    yield 1

                bake_image.save_render(filepath=bake_path)

                bpy.data.images.remove(bake_image)

                node_tree.links.new(combined.outputs[0], out.inputs[0])
                node_tree.nodes.remove(bake_node)
                node_tree.nodes.remove(uv_node)
        yield 0

    def modal(self, context, event):
        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.report({"INFO"}, "Baking map cancelled")
            return {"CANCELLED"}

        if event.type == "TIMER":

            result = next(self.BakeCrt)

            if result == -1:
                self.report({"INFO"}, "Baking map cancelled")
                return {"CANCELLED"}

            if result == 0:
                # finish
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                self.report({"INFO"}, "Baking map completed")
                bpy.context.window_manager.my_toolqt.in_bake_preview = 0

                context.active_object.active_material = bpy.context.window_manager.my_toolqt.preview_mat
                if bpy.context.window_manager.my_toolqt.render_engine:
                    context.scene.render.engine = "CYCLES"
                    context.scene.render.engine = self._render
                    bpy.context.scene.cycles.samples = self._samples
                else:
                    context.scene.render.engine = "BLENDER_EEVEE"
                    bpy.context.window_manager.my_toolqt.render_engine = 0
                return {"FINISHED"}
            
        return {"PASS_THROUGH"}

    def execute(self, context: bpy.context):
        if not len(str(bpy.context.window_manager.my_toolqt.bakepath)) > 0:
            if bpy.data.is_saved:
                abs_filepath = bpy.path.abspath('//')
                if not os.path.isdir(str(abs_filepath+"QT_Textures")):
                    os.mkdir(str(abs_filepath+"QT_Textures"))
                else:
                    bpy.context.window_manager.my_toolqt.bakepath = str(abs_filepath+"QT_Textures")
            else:
                self.report({"WARNING"}, "No valid file path")
                return {"FINISHED"}

        bpy.context.window_manager.my_toolqt.forceprocedural = 0

        # only works on active object
        obj = context.active_object
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects[obj.name].select_set(True)
        bpy.context.view_layer.objects.active = obj

        # store settings
        self._samples = bpy.context.scene.cycles.samples
        self._render = context.scene.render.engine

        # settings
        if context.scene.render.engine != "CYCLES":
            context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.samples = bpy.context.window_manager.my_toolqt.samples

        if len(obj.data.uv_layers) > 0:
            uvs = [
                u
                for u in obj.data.uv_layers
                if u != obj.data.uv_layers
            ]
            while uvs:
                obj.data.uv_layers.remove(uvs.pop())

        bpy.context.active_object.data.uv_layers.new(name="QT_SmartUVMap")
        bpy.context.object.data.uv_layers["QT_SmartUVMap"].active = True
        bpy.context.object.data.uv_layers["QT_SmartUVMap"].active_render = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.convert(target='MESH')

        # modal
        self.BakeCrt = self.Bake(context)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

class quicktexture_uv(bpy.types.Operator):
    bl_idname = "object.quicktexture_uv"
    bl_label = "UV"
    bl_description = "QuickTexture Use Object's UV's"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.uv_mode = 'UV'
        bpy.ops.qt.material_qt("INVOKE_DEFAULT")
        return {"FINISHED"}

class quicktexture_view(bpy.types.Operator):
    bl_idname = "object.quicktexture_view"
    bl_label = "View"
    bl_description = "QuickTexture Procedural From View"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.uv_mode = 'View'
        bpy.ops.qt.material_qt("INVOKE_DEFAULT")
        return {"FINISHED"}

class quicktexture_box(bpy.types.Operator):
    bl_idname = "object.quicktexture_box"
    bl_label = "Procedural Box"
    bl_description = "QuickTexture Procedural Box"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.uv_mode = 'Procedural Box'
        bpy.ops.qt.material_qt("INVOKE_DEFAULT")
        return {"FINISHED"}

class quicktexture_triplanar(bpy.types.Operator):
    bl_idname = "object.quicktexture_triplanar"
    bl_label = "Triplanar"
    bl_description = "QuickTexture Triplanar"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.context.window_manager.my_toolqt.uv_mode = 'Triplanar'
        bpy.ops.qt.material_qt("INVOKE_DEFAULT")
        return {"FINISHED"}

class photomodelingplane(bpy.types.Operator):
    bl_idname = "object.photomodelingplane"
    bl_label = "Photomodeling Plane"
    bl_description = "Make a Photomodeling Plane"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):

        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.window_manager.my_toolqt.uv_mode = 'Procedural Box'
        bpy.ops.object.quicktexturedecal("INVOKE_DEFAULT")
        return {"FINISHED"}

class photomodelingbox(bpy.types.Operator):
    bl_idname = "object.photomodelingbox"
    bl_label = "Photomodeling Box"
    bl_description = "Make a Photomodeling Box"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.window_manager.my_toolqt.uv_mode = 'Procedural Box'
        bpy.ops.object.quicktexture("INVOKE_DEFAULT")
        return {"FINISHED"}

class photomodelingapply(bpy.types.Operator):
    bl_idname = "object.photomodelingapply"
    bl_label = "Apply Photomodel"
    bl_description = "Apply Photomodel"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):
        bpy.ops.object.convert(target='MESH')
        return {"FINISHED"}