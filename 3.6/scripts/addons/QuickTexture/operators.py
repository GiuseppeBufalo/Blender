import bpy
import os
from os.path import abspath, join, exists
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
import math
import bmesh
from bpy_extras import view3d_utils
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import *
from math import *
from bpy.types import Panel, Menu, Operator, PropertyGroup, Macro
import mathutils
import bpy_extras
from bpy_extras.view3d_utils import region_2d_to_location_3d
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras import view3d_utils
from mathutils.geometry import intersect_line_plane
from mathutils.geometry import intersect_line_line
from mathutils.geometry import intersect_line_line_2d
import traceback

from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper

import numpy
import random

import addon_utils

from . import utils
from . import objects
from . import maths

class VIEW3D_MT_QT_PIE(Menu):
    bl_label = "QuickTexture"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences
        inputs = prefs.inputs
        pie = layout.menu_pie()
        scene = context.scene

        scale_x = 1.1
        scale_y = 1.1

        other = pie.column()
        other_menu = other.box().column()
        other_menu.scale_y = scale_y
        other_menu.scale_x = scale_x
        other_menu.label(text="QUICKTEXTURE")
        other_menu.operator("object.quicktexturebox")
        other_menu.operator("object.quicktextureview")
        other_menu.operator("object.quicktextureuv")
        other_menu.operator("object.quickdecal")
        other_menu.operator("object.photomodelingplane")
        other_menu.operator("object.photomodelingbox")
        other_menu.operator("object.photomodelingapply")


class VIEW3D_OT_PIE_QT_PIE_call(bpy.types.Operator):
    bl_idname = "object.quicktexturepie"
    bl_label = "Pie Menu"
    bl_description = "Calls pie menu"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="VIEW3D_MT_QT_PIE")
        return {"FINISHED"}


def update_ao_radius(self, context):

    ob = bpy.context.active_object
    if ob:
        mat = ob.data.materials[0]
        for n in mat.node_tree.nodes:
            if n.name == 'Group.001':
                ao = n

        ao.inputs[0].default_value = bpy.context.window_manager.my_toolqt.ao_radius_preview

def update_cavity_radius(self, context):

    ob = bpy.context.active_object
    if ob:
        mat = ob.data.materials[0]
        for n in mat.node_tree.nodes:
            if n.name == 'Group':
                cavity = n

        cavity.inputs[0].default_value = bpy.context.window_manager.my_toolqt.cavity_radius_preview

class MyPropertiesQT(bpy.types.PropertyGroup):

    ob: PointerProperty(type=bpy.types.Object)

    preview_mat: PointerProperty(type=bpy.types.Material)

    render_engine: BoolProperty(name="render_engine", description="render_engine", default=0)

    running_qt: IntProperty(name="running_qt", description="running_qt", default=0)

    forceprocedural: BoolProperty(
        name="forceprocedural",
        description="Delete objects original UV's and create QuickTexture procedural UV's",
        default=1,
    )

    res: IntProperty(
        name="res",
        description="Resolution of Decal Projection",
        default=0,
        min=0,
        max=10,
    )

    selected: BoolProperty(name="selected", description="selected", default=0)

    padding: FloatProperty(
        name="padding",
        description="Padding for Decal Projection",
        default=0.02,
        min=0.0001,
        max=0.1,
    )

    cavity_radius_preview: FloatProperty(
        name="cavity_radius_preview",
        description="Cavity Radius Preview",
        default=0.3,
        min=0.001,
        max=10,
        update = update_cavity_radius
    )

    ao_radius_preview: FloatProperty(
        name="ao_radius_preview",
        description="AO Radius Preview",
        default=0.3,
        min=0.001,
        max=10,
        update = update_ao_radius
    )

    decal: BoolProperty(name="decal", description="decal", default=0)

    use_uv: BoolProperty(name="use_uv", description="use_uv", default=0)

    save_original_mat: BoolProperty(
        name="save_original_mat",
        description="Save a copy of the original pre Bake material in the scene after Baking",
        default=1,
    )

    proc_uv: BoolProperty(name="proc_uv", description="proc_uv", default=0)

    in_bake_preview: BoolProperty(name="in_bake_preview", description="in_bake_preview", default=0)

    blend: BoolProperty(name="blend", description="blend", default=0)

    mask: BoolProperty(name="mask", description="mask", default=0)

    mode: bpy.props.EnumProperty(
        items=[
            ("view", "VIEW", "View Projection", "view", 0),
            ("box", "BOX", "Box Projection", "box", 1),
        ],
        default="box",
    )

    filepath: StringProperty(name="filepath", description="filepath", default="none")

    activemap: IntProperty(name="activemap", description="activemap", default=1)

    activelayer: IntProperty(name="activelayer", description="activelayer", default=1)

    metal: BoolProperty(name="metal", description="metal", default=0)

    bump: FloatProperty(name="bump", description="bump", default=1)

    bump_strength: FloatProperty(name="bumpstr", description="bumpstr", default=0.1)

    bump_layer: FloatProperty(name="bumplayer", description="bumplayer", default=-10)

    bevel_radius: FloatProperty(name="bevelradius", description="bevelradius", default=0.1)

    ao_radius: FloatProperty(name="aoradius", description="aoradius", default=0.1)

    normal: FloatProperty(name="normal", description="normal", default=1)

    spec: FloatProperty(name="spec", description="spec", default=0.5)

    sss: FloatProperty(name="sss", description="ss", default=0)

    emit: FloatProperty(name="emit", description="emit", default=0)

    ao: FloatProperty(name="ao", description="ao", default=0)

    diffuse_hue: FloatProperty(name="hue", description="hue", default=0.5)

    diffuse_val: FloatProperty(
        name="val", description="val", default=1, min=-30, max=30
    )

    diffuse_sat: FloatProperty(
        name="sat", description="sat", default=1, min=-30, max=30
    )

    diffuse_contrast: FloatProperty(
        name="diffuse_contrast",
        description="diffuse_contrast",
        default=1,
        min=-30,
        max=30,
    )

    rough_val: FloatProperty(
        name="roughness_val", description="roughness_val", default=1, min=-30, max=30
    )

    rough_contrast: FloatProperty(
        name="roughness_contrast",
        description="roughness_contrast",
        default=1,
        min=-30,
        max=30,
    )

    rough_hue_sat: FloatProperty(
        name="rough_hue_sat", description="rough_hue_sat", default=1
    )

    bump_val: FloatProperty(name="bump_val", description="bump_val", default=1)

    bump_contrast: FloatProperty(
        name="bump_contrast", description="bump_contrast", default=1, min=-30, max=30
    )

    bump_hue_sat: FloatProperty(
        name="bump_hue_sat", description="bump_hue_sat", default=1
    )

    mask_val: FloatProperty(name="mask_val", description="mask_val", default=1)

    mask_contrast: FloatProperty(
        name="mask_contrast", description="mask_contrast", default=1, min=-30, max=30
    )

    mask_hue_sat: FloatProperty(
        name="mask_hue_sat", description="mask_hue_sat", default=1
    )

    alpha_bright_contrast: FloatProperty(
        name="alpha_bright_contrast",
        description="alpha_bright_contrast",
        default=1,
        min=-30,
        max=30,
    )

    alpha_hue_sat: FloatProperty(
        name="alpha_hue_sat", description="alpha_hue_sat", default=0
    )

    random_hue: FloatProperty(name="random_hue", description="random_hue", default=0)

    random_val: FloatProperty(name="random_val", description="random_val", default=0)

    random_contrast: FloatProperty(
        name="random_contrast", description="random_contrast", default=0
    )

    random_sat: FloatProperty(name="random_sat", description="random_sat", default=0)

    random_seed: FloatProperty(name="random_seed", description="random_seed", default=0)

    opacity: FloatProperty(name="opacity", description="opacity", default=1)

    blendsmoothing: FloatProperty(
        name="blendsmoothing",
        description="blendsmoothing",
        default=0.001,
        min=0.001,
        max=5,
    )

    blendvalue: FloatProperty(
        name="blendvalue", description="blendvalue", default=0, min=0, max=1
    )

    disp_str: FloatProperty(
        name="dispstrength", description="dispstrength", default=0.5, min=0, max=1
    )

    blendcontrast: FloatProperty(
        name="blendcontrast", description="blendcontrast", default=0
    )

    noiseroughness: FloatProperty(
        name="noiseroughness", description="noiseroughness", default=0.5, min=0, max=1
    )

    noisescale: FloatProperty(
        name="noisescale", description="noisescale", default=0, min=0, max=30
    )

    noisedetail: FloatProperty(
        name="noisedetail", description="noisedetail", default=2, min=0, max=30
    )

    noisedistortion: FloatProperty(
        name="noisedistortion", description="noisedistortion", default=0, min=0, max=30
    )

    variation_scale: FloatProperty(
        name="variation_scale", description="variation_scale", default=0, min=0, max=30
    )

    variation_smoothness: FloatProperty(
        name="variation_smoothness", description="variation_smoothness", default=0, min=0, max=1
    )

    variation_intensity: FloatProperty(
        name="variation_intensity", description="variation_intensity", default=0, min=0, max=1
    )

    variation_sat: FloatProperty(
        name="variation_sat", description="variation_sat", default=0, min=0, max=1
    )

    makeunique: BoolProperty(
        name="makeunique",
        description="Make the material unique after copying",
        default=1,
    )

    triplanar: BoolProperty(name="triplanar", description="Triplanar Blend", default=0)

    decal_hitloc: FloatVectorProperty(
        name="decal_hitloc", description="hitloc", default=(0, 0, 0), subtype="XYZ"
    )

    decal_raydir: FloatVectorProperty(
        name="decal_raydir",
        description="raydir",
        default=(0, 0, 0),
        subtype="DIRECTION",
    )

    bakepath: StringProperty(
        name="bakepath", description="Bake Output Directory Path", default=""
    )

    bakename: StringProperty(
        name="bakename", description="Baked Texture Name", default="bakeMat"
    )

    bakeres: IntProperty(
        name="bakeres", description="Bake Resolution", default=1024, min=1, max=8192
    )

    tiling_blend_amount: FloatProperty(
        name="tiling_blend_amount",
        description="tiling_blend_amount",
        default=0,
        min=0.0,
        max=100,
    )

    tiling_blend_noise: FloatProperty(
        name="tiling_blend_noise",
        description="tiling_blend_noise",
        default=0,
        min=0,
        max=100,
    )

    smudge_val: FloatProperty(name="uv_val", description="uv_val", default=1)

    smudge_bright_contrast: FloatProperty(
        name="uv_bright_contrast", description="uv_bright_contrast", default=1
    )

    smudge_hue_sat: FloatProperty(
        name="uv_hue_sat", description="uv_hue_sat", default=1
    )

    matindex: IntProperty(
        name="matindex", description="Material Index", default=0, min=0, max=9
    )

    samples: IntProperty(
        name="samples", description="Cycles Bake Samples", default=64, min=1, max=10000
    )


class QT_PT_panel(bpy.types.Panel):
    bl_label = "QUICKTEXTURE"
    bl_category = "QuickTools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        layout = self.layout

        box = layout.box()
        row = box.row()
        row.label(text="GENERAL")
        row = box.row()
        row.label(text="Ctrl + T = Quick Texture")
        row = box.row()
        row.label(text="Ctrl + Shift + D = Quick Decal")
        box = layout.box()
        row = box.row()
        row.label(text="EDIT")
        row = box.row()
        row.label(text="G = Move Texture")
        row = box.row()
        row.label(text="S = Scale Texture")
        row = box.row()
        row.label(text="R = Rotate Texture")
        row = box.row()
        row.label(text="Shift S = Stretch X")
        row = box.row()
        row.label(text="Alt S = Stretch Y")
        row = box.row()
        row.label(text="[ or ← = Rotate 90 Degrees")
        row = box.row()
        row.label(text="] or → = Rotate 90 Degrees")
        row = box.row()
        row.label(text="Alt C = Clip / Repeat Toggle")
        row = box.row()
        row.label(text="Alt A = Color / Alpha Toggle")
        row = box.row()
        row.label(text="Alt D = Shadow Visibility Toggle")
        row = box.row()
        row.label(text="Tab = Preview Final Shader")
        row = box.row()
        row.label(text="K = Reset All Settings")
        row = box.row()
        row.label(text="Alt K = Reset Values")
        row = box.row()
        row.label(text="Shift K = Reset Scale")
        row = box.row()
        row.label(text="Ctrl K = Reset Transforms")
        row = box.row()
        row.label(text="Ctrl Shift N = Reset Shader")
        box = layout.box()
        row = box.row()
        row.label(text="MAPS")
        row = box.row()
        row.label(text="1 = Combined")
        row = box.row()
        row.label(text="2 = Roughness")
        row = box.row()
        row.label(text="3 = Bump")
        row = box.row()
        row.label(text="4 = Mask")
        row = box.row()
        row.label(text="5 = Alpha")
        row = box.row()
        row.label(text="6 = UV")
        row = box.row()
        row.label(text="7 = Tiling")
        row = box.row()
        row.label(text="8 = Randomization")
        row = box.row()
        row.label(text="9 = Variety")
        row = box.row()
        row.label(text="0 = Displacement")
        row = box.row()
        row.label(text="U = Use De-Tiling")
        row = box.row()
        row.label(text="Shift T = Triplanar Blend")
        row = box.row()
        row.label(text="Ctrl I = Invert Map")
        row = box.row()
        row.label(text="Alt R = Replace Map")
        row = box.row()
        row.label(text="Ctrl + Num = Switch Material Layers")
        box = layout.box()
        row = box.row()
        row.label(text="LAYERS")
        row = box.row()
        row.label(text="Ctrl + B = New Box Layer")
        row = box.row()
        row.label(text="Ctrl + V = New View Layer")
        row = box.row()
        row.label(text="Q = Prev Layer")
        row = box.row()
        row.label(text="W = Next Layer")
        row = box.row()
        row.label(text="Shift D = Duplicate Layer")
        row = box.row()
        row.label(text="P = Reproject")
        row = box.row()
        row.label(text="Del = Delete Layer")
        box = layout.box()
        row = box.row()
        row.label(text="MASKS")
        row = box.row()
        row.label(text="Ctrl + M = Mask By Texture")
        row = box.row()
        row.label(text="Ctrl + C = Mask By Cavity")
        row = box.row()
        row.label(text="Ctrl + A = Mask By AO")
        row = box.row()
        row.label(text="Shift + V = Mask By Vertex Color")
        row = box.row()
        row.label(text="Alt + H = Mask By Depth Map")
        row = box.row()
        row.label(text="Ctrl + H = Mask By Height")
        row = box.row()
        row.label(text="Ctrl + N = Mask By Normal")
        row = box.row()
        row.label(text="Shift + A = UV Smudge Mask")
        row = box.row()
        row.label(text="Backspace = Delete Mask")
        box = layout.box()
        row = box.row()
        row.label(text="SETTINGS")
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, "mode", expand=True)
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "forceprocedural",
            text="Force Procedural UVs",
            slider=False,
        )
        box = layout.box()
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "makeunique",
            text="Unlink Material After Copy",
        )
        row = box.row()
        row.operator(QT_OT_copymats.bl_idname)
        row = box.row()
        row.operator(QT_OT_makeunique.bl_idname)
        box = layout.box()
        row = box.row()
        row.label(text="BAKING")
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt, "bakename", text="Bake Texture Name"
        )
        row = box.row()
        row.prop(
            bpy.context.window_manager.my_toolqt,
            "bakepath",
            text="Bake Output Directory",
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
        row = box.row()
        row.operator(bakePreviewTextures.bl_idname)
        row = box.row()
        row.operator(previewTextures.bl_idname)
        row = box.row()
        if bpy.context.window_manager.my_toolqt.in_bake_preview:
            row.prop(
                bpy.context.window_manager.my_toolqt,
                "cavity_radius_preview",
                text="Cavity Radius",
                slider=True,
            )
            row.prop(
                bpy.context.window_manager.my_toolqt,
                "ao_radius_preview",
                text="AO Radius",
                slider=True,
            )


class VIEW3D_MT_QT_PIE1(Menu):
    bl_label = "QuickTexture"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences
        inputs = prefs.inputs
        pie = layout.menu_pie()
        scene = context.scene

        scale_x = 1.1
        scale_y = 1.1

        other = pie.column()
        other_menu = other.box().column()
        other_menu.scale_y = scale_y
        other_menu.scale_x = scale_x
        other_menu.operator(QT_OT_boxlayer_qt.bl_idname)
        other_menu.operator(QT_OT_viewlayer_qt.bl_idname)

        other = pie.column()
        other_menu = other.box().column()
        other_menu.scale_y = scale_y
        other_menu.scale_x = scale_x
        other_menu.operator(QT_OT_texturemask_qt.bl_idname)
        other_menu.operator(QT_OT_depthmask_qt.bl_idname)
        other_menu.operator(QT_OT_heightmask_qt.bl_idname)
        other_menu.operator(QT_OT_normalmask_qt.bl_idname)
        other_menu.operator(QT_OT_vertexmask_qt.bl_idname)
        other_menu.operator(QT_OT_cavitymask_qt.bl_idname)
        other_menu.operator(QT_OT_aomask_qt.bl_idname)
        other_menu.operator(QT_OT_smudge_qt.bl_idname)
        other_menu.operator(QT_OT_replacemaps_qt.bl_idname)
        other_menu.operator(QT_OT_replacealpha_qt.bl_idname)

        other = pie.column()
        other_menu = other.box().column()
        other_menu.scale_y = scale_y
        other_menu.scale_x = scale_x
        other_menu.prop(bpy.context.window_manager.my_toolqt, "mode", expand=True)
        other_menu = other.box().column()
        other_menu.operator(QT_OT_makeunique.bl_idname)

        # other = pie.column()
        # other_menu = other.box().column()
        # other_menu.scale_y=scale_y
        # other_menu.scale_x=scale_x
        # other_menu.prop(bpy.context.window_manager.my_toolqt, "res", text="Decal Resolution", slider=True)
        # other_menu.prop(bpy.context.window_manager.my_toolqt, "padding", text="Decal Padding", slider=True)


def draw_quickTexture(self, context):
    font_id = 0  # XXX, need to find out how best to get this.
    region = context.region

    if bpy.context.window_manager.my_toolqt.running_qt and self.core_shader:

        # TEXT
        font_id = 0

        if bpy.context.window_manager.my_toolqt.decal:
            text = "QUICK DECAL"
        else:
            text = "QUICK TEXTURE"

        dpi = 1

        height = blf.dimensions(font_id, text)[1] * 5
        space = height * 0.5
        dim_x = blf.dimensions(font_id, text)[0] / 2

        dim_x = 30
        height = 30
        space = 20
        space = height * 0.75

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                r3d = area.spaces[0].region_3d
                for r in area.regions:
                    if r.type == "UI":
                        uiWidth = r.width

        blf.position(font_id, self.regX / 2 - dim_x, self.regY - space, 0)
        blf.size(
            font_id,
            bpy.context.preferences.addons[__package__].preferences.text_size,
            72 * dpi,
        )
        blf.color(
            font_id,
            bpy.context.preferences.addons[__package__].preferences.col_accent[0],
            bpy.context.preferences.addons[__package__].preferences.col_accent[1],
            bpy.context.preferences.addons[__package__].preferences.col_accent[2],
            bpy.context.preferences.addons[__package__].preferences.col_accent[3],
        )
        blf.draw(font_id, text)

        text3 = "Active Layer: " + str(self.core_shader.label)
        dim_x4 = blf.dimensions(font_id, text3)[0]
        blf.position(font_id, self.regX / 2 - dim_x4 / 2, space, 0)
        blf.color(
            font_id,
            bpy.context.preferences.addons[__package__].preferences.col_primary[0],
            bpy.context.preferences.addons[__package__].preferences.col_primary[1],
            bpy.context.preferences.addons[__package__].preferences.col_primary[2],
            bpy.context.preferences.addons[__package__].preferences.col_primary[3],
        )
        blf.draw(font_id, text3)

        activemap = "Combined"
        if bpy.context.window_manager.my_toolqt.activemap == 1:
            activemap = "Combined"
        elif bpy.context.window_manager.my_toolqt.activemap == 2:
            activemap = "Roughness"
        elif bpy.context.window_manager.my_toolqt.activemap == 3:
            activemap = "Bump"
        elif bpy.context.window_manager.my_toolqt.activemap == 4:
            activemap = "Mask"
        elif bpy.context.window_manager.my_toolqt.activemap == 5:
            activemap = "Alpha"
        elif bpy.context.window_manager.my_toolqt.activemap == 6:
            activemap = "Tiling"
        elif bpy.context.window_manager.my_toolqt.activemap == 7:
            activemap = "UV"
        elif bpy.context.window_manager.my_toolqt.activemap == 8:
            activemap = "Randomization"
        elif bpy.context.window_manager.my_toolqt.activemap == 9:
            activemap = "Variation"
        elif bpy.context.window_manager.my_toolqt.activemap == 0:
            activemap = "Displacement"

        if bpy.context.window_manager.my_toolqt.blend:
            activemap = "Blend"

        if (
            bpy.context.window_manager.my_toolqt.blend
            or bpy.context.window_manager.my_toolqt.mask
        ):
            text1 = "Active Map: " + activemap
            textLength1 = "Active Map" + activemap
            dim_x3 = blf.dimensions(font_id, text1)[0]
            blf.position(font_id, self.regX / 2 - dim_x3 / 2, space * 2, 0)
            blf.size(
                font_id,
                bpy.context.preferences.addons[__package__].preferences.text_size,
                72 * dpi,
            )
            blf.color(
                font_id,
                bpy.context.preferences.addons[__package__].preferences.col_primary[0],
                bpy.context.preferences.addons[__package__].preferences.col_primary[1],
                bpy.context.preferences.addons[__package__].preferences.col_primary[2],
                bpy.context.preferences.addons[__package__].preferences.col_primary[3],
            )
            blf.draw(font_id, text1)

            if self.bevel_mask:
                text1 = "(H) Radius: " + str(
                    round(bpy.context.window_manager.my_toolqt.bevel_radius, 2)
                )
            elif self.ao_mask:
                text1 = "(H) Radius: " + str(
                    round(bpy.context.window_manager.my_toolqt.ao_radius, 2)
                )
            else:
                text1 = "(H) Smoothing: " + str(
                    round(bpy.context.window_manager.my_toolqt.blendsmoothing, 2)
                )
            text2 = "(V) Value: " + str(
                round(bpy.context.window_manager.my_toolqt.blendvalue, 2)
            )
            text3 = "(C) Contrast: " + str(
                round(bpy.context.window_manager.my_toolqt.blendcontrast, 2)
            )

            dim_x = blf.dimensions(font_id, text1)[0] + 30
            blf.position(font_id, self.regX - dim_x - uiWidth, space * 3, 0)
            if self.h:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text1)

            blf.position(font_id, self.regX - dim_x - uiWidth, space * 2, 0)
            if self.v:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text2)

            blf.position(font_id, self.regX - dim_x - uiWidth, space, 0)
            if self.c:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text3)

            text = "(O) Noise Roughness: " + str(
                round(bpy.context.window_manager.my_toolqt.noiseroughness, 2)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 4, 0)
            if self.o:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            text = "(SHIFT B) Noise Detail: " + str(
                round(bpy.context.window_manager.my_toolqt.noisedetail, 3)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space, 0)
            if self.shiftb:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            text = "(SHIFT H) Noise Scale: " + str(
                round(bpy.context.window_manager.my_toolqt.noisescale, 3)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 2, 0)
            if self.shifth:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            text = "(E) Noise Distortion: " + str(
                round(bpy.context.window_manager.my_toolqt.noisedistortion, 3)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 3, 0)
            if self.e:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

        else:

            text1 = "Active Map: " + activemap
            textLength1 = "Active Map" + activemap
            dim_x3 = blf.dimensions(font_id, text1)[0]
            blf.position(font_id, self.regX / 2 - dim_x3 / 2, space * 2, 0)
            blf.size(
                font_id,
                bpy.context.preferences.addons[__package__].preferences.text_size,
                72 * dpi,
            )
            blf.color(
                font_id,
                bpy.context.preferences.addons[__package__].preferences.col_primary[0],
                bpy.context.preferences.addons[__package__].preferences.col_primary[1],
                bpy.context.preferences.addons[__package__].preferences.col_primary[2],
                bpy.context.preferences.addons[__package__].preferences.col_primary[3],
            )
            blf.draw(font_id, text1)

            # combined
            if bpy.context.window_manager.my_toolqt.activemap == 1:
                text1 = "(H) Hue: " + str(
                    round(bpy.context.window_manager.my_toolqt.diffuse_hue, 2)
                )
                text2 = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.diffuse_val, 2)
                )
                text3 = "(C) Contrast: " + str(
                    round(bpy.context.window_manager.my_toolqt.diffuse_contrast, 2)
                )
                text4 = "(X) Saturation: " + str(
                    round(bpy.context.window_manager.my_toolqt.diffuse_sat, 2)
                )

                dim_x = blf.dimensions(font_id, text3)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space * 4, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text1)

                blf.position(font_id, self.regX - dim_x - uiWidth, space * 3, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text2)

                blf.position(font_id, self.regX - dim_x - uiWidth, space * 2, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text3)

                dim_x = blf.dimensions(font_id, text4)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text4)

            # roughness
            if bpy.context.window_manager.my_toolqt.activemap == 2:
                text1 = "(Ctrl I) Invert"
                text2 = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.rough_hue_sat, 2)
                )
                text3 = "(C) Contrast: " + str(
                    round(bpy.context.window_manager.my_toolqt.rough_contrast, 2)
                )

            # bump
            if bpy.context.window_manager.my_toolqt.activemap == 3:
                text1 = "(Ctrl I) Invert"
                text2 = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.bump_hue_sat, 2)
                )
                text3 = "(C) Contrast: " + str(
                    round(bpy.context.window_manager.my_toolqt.bump_contrast, 2)
                )

            # mask
            if bpy.context.window_manager.my_toolqt.activemap == 4:
                text1 = "(Ctrl I) Invert"
                text2 = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.mask_hue_sat, 2)
                )
                text3 = "(C) Contrast: " + str(
                    round(bpy.context.window_manager.my_toolqt.mask_contrast, 2)
                )

            # mask
            if bpy.context.window_manager.my_toolqt.activemap == 5:
                text1 = "(Ctrl I) Invert"
                text2 = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.alpha_hue_sat, 2)
                )
                text3 = "(C) Contrast: " + str(
                    round(bpy.context.window_manager.my_toolqt.alpha_bright_contrast, 2)
                )

            # tiling
            if bpy.context.window_manager.my_toolqt.activemap == 6:
                if self.diffuse_tex.projection == "FLAT":
                    triblend = "Off"
                else:
                    triblend = "On"
                if self.diffuse_tex.projection == "BOX":
                    text1 = "(H) UV Blend Amount: " + str(
                        round(self.diffuse_tex.projection_blend, 2)
                    )
                else:
                    text1 = "(H) UV Blend Amount: " + str(
                        round(bpy.context.window_manager.my_toolqt.tiling_blend_amount, 2)
                    )
                text2 = "(V) UV Blend Noise: " + str(
                    round(bpy.context.window_manager.my_toolqt.tiling_blend_noise, 2)
                )
                text3 = "(C) Triplanar Blend: " + triblend

            # uv
            if bpy.context.window_manager.my_toolqt.activemap == 7:
                text1 = "(Ctrl I) Invert"
                text2 = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.smudge_hue_sat, 2)
                )
                text3 = "(C) Contrast: " + str(
                    round(
                        bpy.context.window_manager.my_toolqt.smudge_bright_contrast, 2
                    )
                )

            if (
                bpy.context.window_manager.my_toolqt.activemap > 1
                and bpy.context.window_manager.my_toolqt.activemap != 8
                and bpy.context.window_manager.my_toolqt.activemap != 9
            ):
                dim_x = blf.dimensions(font_id, text3)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space * 3, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text1)

                blf.position(font_id, self.regX - dim_x - uiWidth, space * 2, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text2)

                blf.position(font_id, self.regX - dim_x - uiWidth, space, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text3)

            # random
            if bpy.context.window_manager.my_toolqt.activemap == 8:
                text1 = "(H) Hue: " + str(
                    round(bpy.context.window_manager.my_toolqt.random_hue, 2)
                )
                text2 = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.random_val, 2)
                )
                text3 = "(C) Roughness: " + str(
                    round(bpy.context.window_manager.my_toolqt.random_contrast, 2)
                )
                text4 = "(X) Saturation: " + str(
                    round(bpy.context.window_manager.my_toolqt.random_sat, 2)
                )
                text5 = "(Ctrl I) Hue Seed: " + str(
                    round(bpy.context.window_manager.my_toolqt.random_seed, 2)
                )

                dim_x = blf.dimensions(font_id, text3)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space * 5, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text1)

                blf.position(font_id, self.regX - dim_x - uiWidth, space * 4, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text2)

                blf.position(font_id, self.regX - dim_x - uiWidth, space * 3, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text3)

                dim_x = blf.dimensions(font_id, text4)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space * 2, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text4)

                dim_x = blf.dimensions(font_id, text5)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text5)

            # variation
            if bpy.context.window_manager.my_toolqt.activemap == 9:
                text1 = "(H) Scale: " + str(
                    round(bpy.context.window_manager.my_toolqt.variation_scale, 2)
                )
                text2 = "(V) Intensity: " + str(
                    round(bpy.context.window_manager.my_toolqt.variation_intensity, 2)
                )
                text3 = "(C) Smoothness: " + str(
                    round(bpy.context.window_manager.my_toolqt.variation_smoothness, 2)
                )
                text4 = "(X) Saturation: " + str(
                    round(bpy.context.window_manager.my_toolqt.variation_sat, 2)
                )

                dim_x = blf.dimensions(font_id, text4)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space * 1, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text4)

                dim_x = blf.dimensions(font_id, text3)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space * 2, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text3)

                blf.position(font_id, self.regX - dim_x - uiWidth, space * 3, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text2)

                blf.position(font_id, self.regX - dim_x - uiWidth, space * 4, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text1)

            # displacement
            if bpy.context.window_manager.my_toolqt.activemap == 0:
                text = "(V) Value: " + str(
                    round(bpy.context.window_manager.my_toolqt.disp_str, 2)
                )
                dim_x = blf.dimensions(font_id, text)[0] + 30
                blf.position(font_id, self.regX - dim_x - uiWidth, space, 0)
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
                blf.draw(font_id, text)

            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                opac = str(round(bpy.context.window_manager.my_toolqt.opacity, 2))
            else:
                opac = "N/A"

            text = "(O) Layer Mix Amount: " + opac
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 9, 0)
            if self.o:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            if bpy.context.window_manager.my_toolqt.metal:
                label = "On"
            else:
                label = "Off"

            text = "(M) Metalness: " + label
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 8, 0)
            if bpy.context.window_manager.my_toolqt.metal:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            text = "(L) Subsurface: " + str(
                round(bpy.context.window_manager.my_toolqt.sss, 3)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 7, 0)
            if self.l:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            text = "(E) Emission: " + str(
                round(bpy.context.window_manager.my_toolqt.emit, 3)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 6, 0)
            if self.e:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            if self.ao_tex:
                ao = str(round(bpy.context.window_manager.my_toolqt.ao, 2))
            else:
                ao = "N/A"

            text = "(A) AO Strength: " + ao
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 5, 0)
            if self.a:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)
            if bpy.context.window_manager.my_toolqt.bump_layer > 0:
                depth = "OUT"
            elif bpy.context.window_manager.my_toolqt.bump_layer < 0:
                depth = "IN"
            else:
                depth = "NEUTRAL"

            text = "(ALT B) Bump Layer Depth: " + depth
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 3, 0)
            blf.color(
                font_id,
                bpy.context.preferences.addons[__package__].preferences.col_primary[
                    0
                ],
                bpy.context.preferences.addons[__package__].preferences.col_primary[
                    1
                ],
                bpy.context.preferences.addons[__package__].preferences.col_primary[
                    2
                ],
                bpy.context.preferences.addons[__package__].preferences.col_primary[
                    3
                ],
            )
            blf.draw(font_id, text)

            text = "(SHIFT B) Bump Strength: " + str(
                round(bpy.context.window_manager.my_toolqt.bump_strength, 3)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 4, 0)
            if self.shiftb:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            if self.normal_tex:
                norm = str(round(bpy.context.window_manager.my_toolqt.normal, 3))
            else:
                norm = "N/A"

            text = "(SHIFT N) Normal Strength: " + norm
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space * 2, 0)
            if self.shiftn:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)

            text = "(SHIFT H) Specular Strength: " + str(
                round(bpy.context.window_manager.my_toolqt.spec, 3)
            )
            dim_x = blf.dimensions(font_id, text)[0] + 30
            blf.position(font_id, 15, space, 0)
            if self.shifth:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_accent[
                        3
                    ],
                )
            else:
                blf.color(
                    font_id,
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        0
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        1
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        2
                    ],
                    bpy.context.preferences.addons[__package__].preferences.col_primary[
                        3
                    ],
                )
            blf.draw(font_id, text)


class BakeFileSelector(bpy.types.Operator, ExportHelper):
    bl_idname = "wm.bakefileselector"
    bl_label = "Directory"

    filename_ext = ""

    def execute(self, context):
        fdir = self.properties.filepath
        dirpath = os.path.dirname(fdir)
        bpy.context.window_manager.my_toolqt.bakepath = dirpath
        return {"FINISHED"}


class quickTexture(bpy.types.Operator):
    """Create a QuickTexture on the selected object"""

    bl_idname = "object.quicktexture"
    bl_label = "QuickTexture"
    bl_options = {"REGISTER", "UNDO"}

    def modal(self, context, event):

        if event.type.startswith("NDOF"):
            return {"PASS_THROUGH"}

        # alt nav
        if bpy.context.preferences.addons[__package__].preferences.alt_nav:
            if event.type == "LEFTMOUSE" and event.value == "PRESS":
                if event.alt:
                    self.alt = 0
                    return {"PASS_THROUGH"}
            elif event.type == "LEFTMOUSE" and event.value == "PRESS":
                if event.alt:
                    self.alt = 0
                    return {"PASS_THROUGH"}

        # get vars
        if bpy.context.window_manager.my_toolqt.selected:
            if bpy.context.window_manager.my_toolqt.ob:
                if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 0:
                    self.mat = bpy.context.window_manager.my_toolqt.ob.material_slots[
                        bpy.context.window_manager.my_toolqt.matindex
                    ].material
                    if self.mat and self.mat.node_tree:
                        for n in self.mat.node_tree.nodes:
                            if n.name == "QT_Output":
                                self.out_material = n

                            if n.name.startswith("QT_Shader"):
                                self.nodes = n.node_tree.nodes
                                self.node_tree = n.node_tree

                            # blend only
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name.startswith("QT_Blend"):
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                        if self.nodes:
                            for n in self.nodes:
                                # ACTIVE LAYER
                                if n.name.startswith(
                                    "QT_Shader_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.core_shader = n
                                    self.final_node = n

                                if n.name.startswith(
                                    "QT_Layer_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.final_node = n

                                if n.name == "Group Output":
                                    self.out_node = n

                                # coord
                                if n.name.startswith(
                                    "QT_UV_Layer_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.tex_coord = n

                                # normal
                                if n.name.startswith(
                                    "QT_Normal_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.normal_tex = n

                                if n.name.startswith(
                                    "QT_Normal_Strength_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.normal_strength = n
                                    bpy.context.window_manager.my_toolqt.normal = (
                                        self.normal_strength.inputs[0].default_value
                                    )

                                # mapping
                                if n.name.startswith(
                                    "QT_Diffuse_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_mapping = n
                                if n.name.startswith(
                                    "QT_Rough_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_mapping = n
                                if n.name.startswith(
                                    "QT_Bump_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_mapping = n

                                # clamps
                                if n.name.startswith(
                                    "QT_Clamp_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_clamp = n
                                if n.name.startswith(
                                    "QT_Roughness_Clamp_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.roughness_clamp = n
                                if n.name.startswith(
                                    "QT_Bump_Clamp_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_clamp = n

                                # textures
                                if n.name.startswith(
                                    "QT_Diffuse_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_tex = n
                                if n.name.startswith(
                                    "QT_Diffuse_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.diffuse_hue = (
                                        self.diffuse_hue_sat.inputs[0].default_value
                                    )
                                    bpy.context.window_manager.my_toolqt.diffuse_sat = (
                                        self.diffuse_hue_sat.inputs[1].default_value
                                    )
                                    bpy.context.window_manager.my_toolqt.diffuse_val = (
                                        self.diffuse_hue_sat.inputs[2].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Diffuse_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.diffuse_contrast = self.diffuse_bright_contrast.inputs[
                                        2
                                    ].default_value

                                if n.name.startswith(
                                    "QT_Rough_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_tex = n
                                if n.name.startswith(
                                    "QT_Rough_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Rough_Invert_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_invert = n
                                if n.name.startswith(
                                    "QT_Rough_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[
                                        2
                                    ].default_value

                                if n.name.startswith(
                                    "QT_Bump_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_tex = n
                                if n.name.startswith(
                                    "QT_Bump_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Bump_Bump_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_bump = n
                                    bpy.context.window_manager.my_toolqt.bump = (
                                        self.bump_bump.inputs[0].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Bump_Strength_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_strength = n
                                    bpy.context.window_manager.my_toolqt.bump_strength = (
                                        self.bump_strength.inputs[1].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Mix_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_layer = n
                                    bpy.context.window_manager.my_toolqt.bump_layer = (
                                        self.bump_layer.inputs[3].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Bump_Invert_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_invert = n
                                if n.name.startswith(
                                    "QT_Bump_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[
                                        2
                                    ].default_value

                                # masks
                                if n.name.startswith(
                                    "QT_Tex_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_tex = n
                                if n.name.startswith(
                                    "QT_Bright_Contrast_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Invert_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_invert = n
                                if n.name.startswith(
                                    "QT_Hue_Sat_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Mapping_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_mapping = n

                                # alpha
                                if n.name.startswith(
                                    "QT_Alpha_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_mapping = n
                                if n.name.startswith(
                                    "QT_Alpha_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_tex = n
                                if n.name.startswith(
                                    "QT_Alpha_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Alpha_Invert_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_invert = n
                                if n.name.startswith(
                                    "QT_Alpha_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Alpha_Clamp_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_clamp = n

                                # ao
                                if n.name.startswith(
                                    "QT_AO_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.ao_tex = n

                                if n.name.startswith(
                                    "QT_AO_Multiply_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.ao_multiply = n
                                    bpy.context.window_manager.my_toolqt.ao = (
                                        self.ao_multiply.inputs[0].default_value
                                    )

                                if n.name.startswith(
                                    "QT_AO_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.ao_mask = n

                                # cavity
                                if n.name.startswith(
                                    "QT_Bevel_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bevel_mask = n

                                # height
                                if n.name.startswith(
                                    "QT_Power_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.blend_power = n
                                    bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[
                                        1
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Noise_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[
                                        5
                                    ].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[
                                        4
                                    ].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = (
                                        self.blend_noise.inputs[2].default_value
                                    )
                                    bpy.context.window_manager.my_toolqt.noisedetail = (
                                        self.blend_noise.inputs[3].default_value
                                    )

                                # tiling
                                if n.name.startswith(
                                    "QT_Diffuse_Seamless_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_seamless = n
                                if n.name.startswith(
                                    "QT_Rough_Seamless_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_seamless = n
                                if n.name.startswith(
                                    "QT_Bump_Seamless_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_seamless = n
                                if n.name.startswith(
                                    "QT_Alpha_Seamless_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_seamless = n
                                if n.name.startswith(
                                    "QT_Smudge_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.smudge = n

                                # uv
                                if n.name.startswith(
                                    "QT_Tex_Smudge_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.smudge_tex = n
                                if n.name.startswith(
                                    "QT_Bright_Contrast_Smudge_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.smudge_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.smudge_contrast = self.smudge_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Invert_Smudge_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.smudge_invert = n
                                if n.name.startswith(
                                    "QT_Hue_Sat_Smudge_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.smudge_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.smudge_hue_sat = self.smudge_hue_sat.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Mapping_Smudge_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.smudge_mapping = n

                                # random
                                if n.name.startswith(
                                    "QT_RandColor_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.randcolor = n
                                if n.name.startswith(
                                    "QT_RandVal_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.randval = n
                                # random
                                if n.name.startswith(
                                    "QT_Variety_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.variation = n

                                # disp
                                if n.name.startswith(
                                    "QT_Disp_Vec_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.disp_vec = n
                                if n.name.startswith(
                                    "QT_Disp_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.disp_tex = n
                                if n.name.startswith(
                                    "QT_Displacement_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.disp_mapping = n

                                # blend
                                if bpy.context.window_manager.my_toolqt.blend:
                                    if n.name == ("QT_Blend_Add"):
                                        self.blend_add = n
                                    if n.name == ("QT_Blend_XYZ"):
                                        self.blend_xyz = n
                                    if n.name == ("QT_Blend_Math"):
                                        self.blend_math = n
                                    if n.name == ("QT_Blend_Power"):
                                        self.blend_power = n
                                    if n.name == ("QT_Blend_Clamp"):
                                        self.blend_clamp = n
                                    if n.name == ("QT_Blend_Mix"):
                                        self.blend_mix = n
                                    if n.name == ("QT_Blend_Noise"):
                                        self.blend_noise = n
                                        bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[
                                            5
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[
                                            4
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[
                                            2
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[
                                            3
                                        ].default_value
                                    if n.name == ("QT_Blend_Bright_Contrast"):
                                        self.blend_bright_contrast = n
                                        bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[
                                            2
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[
                                            1
                                        ].default_value
                                    if n.name == "QT_Blend_Mix":
                                        self.final_node = n
                                        self.core_shader = n

        try:
            self.regX = context.region.width
            self.regY = context.region.height
            self.view_vector = Vector(
                (self.rv3d.perspective_matrix[2][0:3])
            ).normalized()
            context.area.tag_redraw()

            if event.type == "MOUSEMOVE":
                self.coord = Vector((event.mouse_region_x, event.mouse_region_y))

            # pass through if not in proper window area
            self.window_active, self.zoomlevel = utils.window_info(
                context,
                event,
                bpy.context.preferences.addons[__package__].preferences.window_buffer,
            )

            if self.window_active == 0:
                return {"PASS_THROUGH"}

            if bpy.context.window_manager.my_toolqt.running_qt == 0:
                if self.nodes is not None:
                    for n in self.nodes:
                        if n.name.startswith("QT_Shader_1"):
                            self.final_node = n

                    for n in self.nodes:
                        if n.name.startswith(
                            "QT_Layer_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.final_node = n

                    self.node_tree.links.new(
                        self.out_node.inputs[0], self.final_node.outputs[0]
                    )
                    self.out_node.location.y = self.final_node.location.y
                    self.out_node.location.x = self.final_node.location.x + 300

                    for n in self.nodes:
                        n.select = False
                        if n.name.endswith(
                            str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            n.select = True

                bpy.context.window_manager.my_toolqt.running_qt = 0
                bpy.context.window_manager.my_toolqt.selected = 0
                bpy.context.window_manager.my_toolqt.decal = 0
                bpy.context.window_manager.my_toolqt.blend = 0
                bpy.context.window_manager.my_toolqt.mask = 0
                bpy.context.window_manager.my_toolqt.ob = None
                if "QuickTexture" in bpy.data.collections:
                    bpy.data.collections["QuickTexture"].hide_viewport = True
                    bpy.data.collections["QuickTexture"].hide_render = True
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
                return {"FINISHED"}

            if event.type in {"LEFTMOUSE", "ENTER"} and event.value == "PRESS":

                if (
                    self.g
                    or self.s
                    or self.r
                    or self.l
                    or self.e
                    or self.shifth
                    or self.shifts
                    or self.alts
                    or self.shiftb
                    or self.shiftn
                    or self.ctrli
                    or self.h
                    or self.v
                    or self.c
                    or self.o
                    or self.a
                    or self.x
                ):
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.shifts = 0
                    self.alts = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.x = 0
                    self.a = 0

                else:
                    context.area.tag_redraw()

                    if self.nodes is not None:

                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_1"):
                                self.final_node = n

                        for n in self.nodes:
                            if n.name.startswith(
                                "QT_Layer_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.final_node = n

                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.final_node.outputs[0]
                        )
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(
                                str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                n.select = True

                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    bpy.context.window_manager.my_toolqt.selected = 0
                    bpy.context.window_manager.my_toolqt.decal = 0
                    bpy.context.window_manager.my_toolqt.blend = 0
                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.ob = None
                    if "QuickTexture" in bpy.data.collections:
                        bpy.data.collections["QuickTexture"].hide_viewport = True
                        bpy.data.collections["QuickTexture"].hide_render = True
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
                    return {"FINISHED"}

            if event.type == "MOUSEMOVE":

                if self.g:

                    self.mouse_sample_x.append(event.mouse_region_x)
                    self.mouse_sample_y.append(event.mouse_region_y)

                    if len(self.mouse_sample_x) > 1:
                        current = Vector(
                            (self.mouse_sample_x[-1], self.mouse_sample_y[-1])
                        )
                        previous = Vector(
                            (self.mouse_sample_x[-2], self.mouse_sample_y[-2])
                        )

                        delta = -0.005
                        delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                        if self.shift == 1:
                            delta *= 0.4

                        if self.ctrl == 1:
                            delta *= 4

                        if self.alt == 1:
                            delta *= 8

                        #################################################################################################

                        aim = (previous - current).normalized()
                        dist = (previous - current).length * delta
                        aim.resize_3d()

                        if aim == None:
                            aim = Vector((0, 0, 0))

                        if (
                            bpy.context.window_manager.my_toolqt.blend
                            or bpy.context.window_manager.my_toolqt.mask
                        ):
                            if self.blend_add:
                                self.blend_add.inputs[1].default_value[2] += (
                                    aim[0] * dist * -1
                                )

                            if self.mask_mapping:
                                self.mask_mapping.inputs[1].default_value[2] += (
                                    aim[0] * dist * -1
                                )

                        else:
                            if bpy.context.window_manager.my_toolqt.activemap == 1:
                                mat = Matrix.Rotation(
                                    self.diffuse_mapping.inputs[2].default_value[2],
                                    4,
                                    "Z",
                                )
                            if bpy.context.window_manager.my_toolqt.activemap == 2:
                                mat = Matrix.Rotation(
                                    self.rough_mapping.inputs[2].default_value[2],
                                    4,
                                    "Z",
                                )
                            if bpy.context.window_manager.my_toolqt.activemap == 3:
                                mat = Matrix.Rotation(
                                    self.bump_mapping.inputs[2].default_value[2], 4, "Z"
                                )
                            if bpy.context.window_manager.my_toolqt.activemap == 4:
                                if self.mask_mapping:
                                    mat = Matrix.Rotation(
                                        self.mask_mapping.inputs[2].default_value[2],
                                        4,
                                        "Z",
                                    )
                            if bpy.context.window_manager.my_toolqt.activemap == 5:
                                mat = Matrix.Rotation(
                                    self.alpha_mapping.inputs[2].default_value[2],
                                    4,
                                    "Z",
                                )
                            if bpy.context.window_manager.my_toolqt.activemap == 0:
                                mat = Matrix.Rotation(
                                    self.disp_mapping.inputs[2].default_value[2],
                                    4,
                                    "Z",
                                )

                            view = Vector((self.rv3d.view_matrix[2][0:3])).normalized()
                            viewmat = self.rv3d.view_matrix.normalized().to_3x3()
                            basemat = Matrix().to_3x3()
                            viewdot = view.dot(Vector((0, 0, 1)))
                            angle = viewmat[0].angle(basemat[0])
                            dirdot = viewmat[0].dot(Vector((0, -1, 0)))
                            if dirdot > 0:
                                mat2 = Matrix.Rotation(-angle, 4, "Z")
                            else:
                                mat2 = Matrix.Rotation(angle, 4, "Z")

                            if not bpy.context.window_manager.my_toolqt.proc_uv:
                                aim.rotate(mat)

                            if abs(viewdot) > 0.99:
                                aim.rotate(mat2)

                            xval = aim[0]
                            yval = aim[1]

                            if abs(viewdot) > 0.99:
                                if not bpy.context.window_manager.my_toolqt.proc_uv:
                                    xval = aim[0]
                                    yval = aim[1]

                            if bpy.context.window_manager.my_toolqt.activemap == 1:
                                self.diffuse_mapping.inputs[1].default_value[0] += (
                                    xval * dist
                                )
                                self.diffuse_mapping.inputs[1].default_value[1] += (
                                    yval * dist
                                )
                                self.diffuse_mapping.inputs[1].default_value[2] = 1

                                self.rough_mapping.inputs[1].default_value[0] += (
                                    xval * dist
                                )
                                self.rough_mapping.inputs[1].default_value[1] += (
                                    yval * dist
                                )
                                self.rough_mapping.inputs[1].default_value[2] = 1

                                self.bump_mapping.inputs[1].default_value[0] += (
                                    xval * dist
                                )
                                self.bump_mapping.inputs[1].default_value[1] += (
                                    yval * dist
                                )
                                self.bump_mapping.inputs[1].default_value[2] = 1

                                self.alpha_mapping.inputs[1].default_value[0] += (
                                    xval * dist
                                )
                                self.alpha_mapping.inputs[1].default_value[1] += (
                                    yval * dist
                                )
                                self.alpha_mapping.inputs[1].default_value[2] = 1

                                if self.disp_mapping:
                                    self.disp_mapping.inputs[1].default_value[0] += (
                                        xval * dist
                                    )
                                    self.disp_mapping.inputs[1].default_value[1] += (
                                        yval * dist
                                    )
                                    self.disp_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 2:
                                self.rough_mapping.inputs[1].default_value[0] += (
                                    xval * dist
                                )
                                self.rough_mapping.inputs[1].default_value[1] += (
                                    yval * dist
                                )
                                self.rough_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 3:
                                self.bump_mapping.inputs[1].default_value[0] += (
                                    xval * dist
                                )
                                self.bump_mapping.inputs[1].default_value[1] += (
                                    yval * dist
                                )
                                self.bump_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 4:

                                if self.mask_mapping:
                                    if self.mask_mapping.name.startswith("QT_Add_Mask"):
                                        self.mask_mapping.inputs[1].default_value[
                                            2
                                        ] += (xval * dist * -1)
                                    else:
                                        self.mask_mapping.inputs[1].default_value[
                                            0
                                        ] += (xval * dist)
                                        self.mask_mapping.inputs[1].default_value[
                                            1
                                        ] += (yval * dist)
                                        self.mask_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 5:
                                if self.alpha_mapping:
                                    self.alpha_mapping.inputs[1].default_value[0] += (
                                        xval * dist
                                    )
                                    self.alpha_mapping.inputs[1].default_value[1] += (
                                        yval * dist
                                    )
                                    self.alpha_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 6:
                                for n in self.nodes:
                                    if n.type == "MAPPING":
                                        if not n.name.startswith("QT_Mapping_"):
                                            n.inputs[1].default_value[0] += xval * dist
                                            n.inputs[1].default_value[1] += yval * dist

                            elif bpy.context.window_manager.my_toolqt.activemap == 7:
                                if self.smudge_mapping:
                                    self.smudge_mapping.inputs[1].default_value[0] += (
                                        xval * dist
                                    )
                                    self.smudge_mapping.inputs[1].default_value[1] += (
                                        yval * dist
                                    )
                                    self.smudge_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 0:
                                if self.disp_mapping:
                                    self.disp_mapping.inputs[1].default_value[0] += (
                                        xval * dist
                                    )
                                    self.disp_mapping.inputs[1].default_value[1] += (
                                        yval * dist
                                    )
                                    self.disp_mapping.inputs[1].default_value[2] = 1

                        context.area.tag_redraw()

                if self.s:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.003
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[0] += (
                            delta * self.diffuse_mapping.inputs[3].default_value[0]
                        )
                        self.diffuse_mapping.inputs[3].default_value[1] += (
                            delta * self.diffuse_mapping.inputs[3].default_value[1]
                        )
                        self.diffuse_mapping.inputs[3].default_value[2] += (
                            delta * self.diffuse_mapping.inputs[3].default_value[2]
                        )

                        self.rough_mapping.inputs[3].default_value[0] += (
                            delta * self.rough_mapping.inputs[3].default_value[0]
                        )
                        self.rough_mapping.inputs[3].default_value[1] += (
                            delta * self.rough_mapping.inputs[3].default_value[1]
                        )
                        self.rough_mapping.inputs[3].default_value[2] += (
                            delta * self.rough_mapping.inputs[3].default_value[2]
                        )

                        self.bump_mapping.inputs[3].default_value[0] += (
                            delta * self.bump_mapping.inputs[3].default_value[0]
                        )
                        self.bump_mapping.inputs[3].default_value[1] += (
                            delta * self.bump_mapping.inputs[3].default_value[1]
                        )
                        self.bump_mapping.inputs[3].default_value[2] += (
                            delta * self.bump_mapping.inputs[3].default_value[2]
                        )

                        self.alpha_mapping.inputs[3].default_value[0] += (
                            delta * self.alpha_mapping.inputs[3].default_value[0]
                        )
                        self.alpha_mapping.inputs[3].default_value[1] += (
                            delta * self.alpha_mapping.inputs[3].default_value[1]
                        )
                        self.alpha_mapping.inputs[3].default_value[2] += (
                            delta * self.alpha_mapping.inputs[3].default_value[2]
                        )

                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[0] += (
                                delta * self.disp_mapping.inputs[3].default_value[0]
                            )
                            self.disp_mapping.inputs[3].default_value[1] += (
                                delta * self.disp_mapping.inputs[3].default_value[1]
                            )
                            self.disp_mapping.inputs[3].default_value[2] += (
                                delta * self.disp_mapping.inputs[3].default_value[2]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[0] += (
                            delta * self.rough_mapping.inputs[3].default_value[0]
                        )
                        self.rough_mapping.inputs[3].default_value[1] += (
                            delta * self.rough_mapping.inputs[3].default_value[1]
                        )
                        self.rough_mapping.inputs[3].default_value[2] += (
                            delta * self.rough_mapping.inputs[3].default_value[2]
                        )

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:

                        self.bump_mapping.inputs[3].default_value[0] += (
                            delta * self.bump_mapping.inputs[3].default_value[0]
                        )
                        self.bump_mapping.inputs[3].default_value[1] += (
                            delta * self.bump_mapping.inputs[3].default_value[1]
                        )
                        self.bump_mapping.inputs[3].default_value[2] += (
                            delta * self.bump_mapping.inputs[3].default_value[2]
                        )

                    elif (
                        bpy.context.window_manager.my_toolqt.activemap == 4
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[0] += (
                                delta * self.mask_mapping.inputs[3].default_value[0]
                            )
                            self.mask_mapping.inputs[3].default_value[1] += (
                                delta * self.mask_mapping.inputs[3].default_value[1]
                            )
                            self.mask_mapping.inputs[3].default_value[2] += (
                                delta * self.mask_mapping.inputs[3].default_value[2]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:

                        if self.alpha_mapping:
                            self.alpha_mapping.inputs[3].default_value[0] += (
                                delta * self.alpha_mapping.inputs[3].default_value[0]
                            )
                            self.alpha_mapping.inputs[3].default_value[1] += (
                                delta * self.alpha_mapping.inputs[3].default_value[1]
                            )
                            self.alpha_mapping.inputs[3].default_value[2] += (
                                delta * self.alpha_mapping.inputs[3].default_value[2]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 6:
                        for n in self.nodes:
                            if n.type == "MAPPING":
                                if not n.name.startswith("QT_Mapping_"):
                                    n.inputs[3].default_value[0] += (
                                        delta * n.inputs[3].default_value[0]
                                    )
                                    n.inputs[3].default_value[1] += (
                                        delta * n.inputs[3].default_value[1]
                                    )
                                    n.inputs[3].default_value[2] += (
                                        delta * n.inputs[3].default_value[2]
                                    )

                    elif bpy.context.window_manager.my_toolqt.activemap == 7:
                        if self.smudge_mapping:
                            self.smudge_mapping.inputs[3].default_value[0] += (
                                delta * self.smudge_mapping.inputs[3].default_value[0]
                            )
                            self.smudge_mapping.inputs[3].default_value[1] += (
                                delta * self.smudge_mapping.inputs[3].default_value[1]
                            )
                            self.smudge_mapping.inputs[3].default_value[2] += (
                                delta * self.smudge_mapping.inputs[3].default_value[2]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 0:
                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[0] += (
                                delta * self.disp_mapping.inputs[3].default_value[0]
                            )
                            self.disp_mapping.inputs[3].default_value[1] += (
                                delta * self.disp_mapping.inputs[3].default_value[1]
                            )
                            self.disp_mapping.inputs[3].default_value[2] += (
                                delta * self.disp_mapping.inputs[3].default_value[2]
                            )

                    context.area.tag_redraw()

                if self.shifts:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.003
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[0] += (
                            delta * self.diffuse_mapping.inputs[3].default_value[0]
                        )

                        self.rough_mapping.inputs[3].default_value[0] += (
                            delta * self.rough_mapping.inputs[3].default_value[0]
                        )

                        self.bump_mapping.inputs[3].default_value[0] += (
                            delta * self.bump_mapping.inputs[3].default_value[0]
                        )

                        self.alpha_mapping.inputs[3].default_value[0] += (
                            delta * self.alpha_mapping.inputs[3].default_value[0]
                        )

                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[0] += (
                                delta * self.disp_mapping.inputs[3].default_value[0]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[0] += (
                            delta * self.rough_mapping.inputs[3].default_value[0]
                        )

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:

                        self.bump_mapping.inputs[3].default_value[0] += (
                            delta * self.bump_mapping.inputs[3].default_value[0]
                        )

                    elif (
                        bpy.context.window_manager.my_toolqt.activemap == 4
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[0] += (
                                delta * self.mask_mapping.inputs[3].default_value[0]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:

                        self.alpha_mapping.inputs[3].default_value[0] += (
                            delta * self.alpha_mapping.inputs[3].default_value[0]
                        )

                    elif bpy.context.window_manager.my_toolqt.activemap == 6:
                        for n in self.nodes:
                            if n.type == "MAPPING":
                                if not n.name.startswith("QT_Mapping_"):
                                    n.inputs[3].default_value[0] += (
                                        delta * n.inputs[3].default_value[0]
                                    )

                    elif bpy.context.window_manager.my_toolqt.activemap == 7:
                        if self.smudge_mapping:
                            self.smudge_mapping.inputs[3].default_value[0] += (
                                delta * self.smudge_mapping.inputs[3].default_value[0]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 0:
                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[0] += (
                                delta * self.disp_mapping.inputs[3].default_value[0]
                            )

                    context.area.tag_redraw()

                if self.alts:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.003
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[1] += (
                            delta * self.diffuse_mapping.inputs[3].default_value[1]
                        )

                        self.rough_mapping.inputs[3].default_value[1] += (
                            delta * self.rough_mapping.inputs[3].default_value[1]
                        )

                        self.bump_mapping.inputs[3].default_value[1] += (
                            delta * self.bump_mapping.inputs[3].default_value[1]
                        )

                        self.alpha_mapping.inputs[3].default_value[1] += (
                            delta * self.alpha_mapping.inputs[3].default_value[1]
                        )

                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[1] += (
                                delta * self.disp_mapping.inputs[3].default_value[1]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[1] += (
                            delta * self.rough_mapping.inputs[3].default_value[1]
                        )

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_mapping.inputs[3].default_value[1] += (
                            delta * self.bump_mapping.inputs[3].default_value[1]
                        )

                    elif (
                        bpy.context.window_manager.my_toolqt.activemap == 4
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[1] += (
                                delta * self.mask_mapping.inputs[3].default_value[1]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_mapping.inputs[3].default_value[1] += (
                            delta * self.alpha_mapping.inputs[3].default_value[1]
                        )

                    elif bpy.context.window_manager.my_toolqt.activemap == 6:
                        for n in self.nodes:
                            if n.type == "MAPPING":
                                if not n.name.startswith("QT_Mapping_"):
                                    n.inputs[3].default_value[1] += (
                                        delta * n.inputs[3].default_value[1]
                                    )

                    elif bpy.context.window_manager.my_toolqt.activemap == 7:
                        if self.smudge_mapping:
                            self.smudge_mapping.inputs[3].default_value[1] += (
                                delta * self.smudge_mapping.inputs[3].default_value[1]
                            )

                    elif bpy.context.window_manager.my_toolqt.activemap == 0:
                        if self.disp_mapping:
                            self.disp_mapping.inputs[3].default_value[1] += (
                                delta * self.disp_mapping.inputs[3].default_value[1]
                            )

                    context.area.tag_redraw()

                if self.r == 1:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= 0.0025
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[2].default_value[2] += delta
                        self.rough_mapping.inputs[2].default_value[2] += delta
                        self.bump_mapping.inputs[2].default_value[2] += delta
                        self.alpha_mapping.inputs[2].default_value[2] += delta
                        if self.disp_mapping:
                            self.disp_mapping.inputs[2].default_value[2] += delta

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[2].default_value[2] += delta

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_mapping.inputs[2].default_value[2] += delta

                    elif (
                        bpy.context.window_manager.my_toolqt.activemap == 4
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):
                        if self.mask_mapping:
                            self.mask_mapping.inputs[2].default_value[2] += delta

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_mapping.inputs[2].default_value[2] += delta

                    elif bpy.context.window_manager.my_toolqt.activemap == 6:
                        for n in self.nodes:
                            if n.type == "MAPPING":
                                if not n.name.startswith("QT_Mapping_"):
                                    n.inputs[2].default_value[2] += delta

                    elif bpy.context.window_manager.my_toolqt.activemap == 7:
                        if self.smudge_mapping:
                            self.smudge_mapping.inputs[2].default_value[2] += delta

                    if bpy.context.window_manager.my_toolqt.activemap == 0:
                        if self.disp_mapping:
                            self.disp_mapping.inputs[2].default_value[2] += delta

                    context.area.tag_redraw()

                if self.l:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.0005
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    self.core_shader.inputs[1].default_value += delta
                    if self.core_shader.inputs[1].default_value < 0:
                        self.core_shader.inputs[1].default_value = 0
                    if self.core_shader.inputs[1].default_value > 1:
                        self.core_shader.inputs[1].default_value = 1

                    bpy.context.window_manager.my_toolqt.sss = self.core_shader.inputs[
                        1
                    ].default_value

                    context.area.tag_redraw()

                if self.a:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.001
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if self.ao_multiply:
                        self.ao_multiply.inputs[0].default_value += delta
                        if self.ao_multiply.inputs[0].default_value < 0:
                            self.ao_multiply.inputs[0].default_value = 0
                        if self.ao_multiply.inputs[0].default_value > 30:
                            self.ao_multiply.inputs[0].default_value = 30

                        bpy.context.window_manager.my_toolqt.ao = (
                            self.ao_multiply.inputs[0].default_value
                        )

                    context.area.tag_redraw()

                if self.e:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.01
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.blend_noise:
                            self.blend_noise.inputs[5].default_value += delta
                            if self.blend_noise.inputs[5].default_value < 0:
                                self.blend_noise.inputs[5].default_value = 0
                            if self.blend_noise.inputs[5].default_value > 20:
                                self.blend_noise.inputs[5].default_value = 20

                            bpy.context.window_manager.my_toolqt.noisedistortion = (
                                self.blend_noise.inputs[5].default_value
                            )

                    else:
                        self.core_shader.inputs[20].default_value += delta
                        if self.core_shader.inputs[20].default_value < 0:
                            self.core_shader.inputs[20].default_value = 0

                        bpy.context.window_manager.my_toolqt.emit = (
                            self.core_shader.inputs[20].default_value
                        )

                    context.area.tag_redraw()

                if self.o:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.002
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.blend_noise:
                            self.blend_noise.inputs[4].default_value += delta
                            if self.blend_noise.inputs[4].default_value < 0:
                                self.blend_noise.inputs[4].default_value = 0
                            if self.blend_noise.inputs[4].default_value > 5:
                                self.blend_noise.inputs[4].default_value = 5

                            bpy.context.window_manager.my_toolqt.noiseroughness = (
                                self.blend_noise.inputs[4].default_value
                            )

                    else:
                        if self.final_node.name.startswith("QT_Layer"):
                            self.final_node.inputs[0].default_value += delta
                            if self.final_node.inputs[0].default_value < 0:
                                self.final_node.inputs[0].default_value = 0
                            if self.final_node.inputs[0].default_value > 1:
                                self.final_node.inputs[0].default_value = 1

                            bpy.context.window_manager.my_toolqt.opacity = (
                                self.final_node.inputs[0].default_value
                            )

                    context.area.tag_redraw()

                if self.shifth:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        delta *= -0.005
                    else:
                        delta *= -0.0005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.blend_noise:
                            self.blend_noise.inputs[2].default_value += delta
                            if self.blend_noise.inputs[2].default_value < 0:
                                self.blend_noise.inputs[2].default_value = 0
                            if self.blend_noise.inputs[2].default_value > 30:
                                self.blend_noise.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.noisescale = (
                                self.blend_noise.inputs[2].default_value
                            )

                    else:
                        self.core_shader.inputs[7].default_value += delta
                        if self.core_shader.inputs[7].default_value < 0:
                            self.core_shader.inputs[7].default_value = 0
                        if self.core_shader.inputs[7].default_value > 5:
                            self.core_shader.inputs[7].default_value = 5

                        bpy.context.window_manager.my_toolqt.spec = (
                            self.core_shader.inputs[7].default_value
                        )

                    context.area.tag_redraw()

                if self.shiftn:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    delta *= -0.005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        print("nothing yet")

                    else:
                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value += delta
                            if self.normal_strength.inputs[0].default_value < 0:
                                self.normal_strength.inputs[0].default_value = 0
                            if self.normal_strength.inputs[0].default_value > 5:
                                self.normal_strength.inputs[0].default_value = 5

                            bpy.context.window_manager.my_toolqt.normal = (
                                self.normal_strength.inputs[0].default_value
                            )

                    context.area.tag_redraw()

                if self.shiftb:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.001
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.blend_noise:
                            self.blend_noise.inputs[3].default_value += delta
                            if self.blend_noise.inputs[3].default_value < 0:
                                self.blend_noise.inputs[3].default_value = 0
                            if self.blend_noise.inputs[3].default_value > 30:
                                self.blend_noise.inputs[3].default_value = 30

                            bpy.context.window_manager.my_toolqt.noisedetail = (
                                self.blend_noise.inputs[3].default_value
                            )

                    else:
                        self.bump_strength.inputs[1].default_value += delta
                        if self.bump_strength.inputs[1].default_value < 0:
                            self.bump_strength.inputs[1].default_value = 0
                        if self.bump_strength.inputs[1].default_value > 5:
                            self.bump_strength.inputs[1].default_value = 5
                        bpy.context.window_manager.my_toolqt.bump_strength = (
                            self.bump_strength.inputs[1].default_value
                        )

                    context.area.tag_redraw()

                if self.h:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.001
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.blend_power:
                            self.blend_power.inputs[1].default_value += delta
                            if self.blend_power.inputs[1].default_value < 0.001:
                                self.blend_power.inputs[1].default_value = 0.001
                            if self.blend_power.inputs[1].default_value > 5:
                                self.blend_power.inputs[1].default_value = 5

                            bpy.context.window_manager.my_toolqt.blendsmoothing = (
                                self.blend_power.inputs[1].default_value
                            )
                        if self.bevel_mask:
                            self.bevel_mask.inputs[0].default_value += delta
                            if self.bevel_mask.inputs[0].default_value < 0.001:
                                self.bevel_mask.inputs[0].default_value = 0.001
                            if self.bevel_mask.inputs[0].default_value > 15:
                                self.bevel_mask.inputs[0].default_value = 15

                            bpy.context.window_manager.my_toolqt.bevel_radius = (
                                self.bevel_mask.inputs[0].default_value
                            )
                        if self.ao_mask:
                            self.ao_mask.inputs[1].default_value += delta
                            if self.ao_mask.inputs[1].default_value < 0.001:
                                self.ao_mask.inputs[1].default_value = 0.001
                            if self.ao_mask.inputs[1].default_value > 15:
                                self.ao_mask.inputs[1].default_value = 15

                            bpy.context.window_manager.my_toolqt.ao_radius = (
                                self.ao_mask.inputs[1].default_value
                            )

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[0].default_value += delta
                            if self.diffuse_hue_sat.inputs[0].default_value < 0:
                                self.diffuse_hue_sat.inputs[0].default_value = 0
                            if self.diffuse_hue_sat.inputs[0].default_value > 5:
                                self.diffuse_hue_sat.inputs[0].default_value = 5

                            bpy.context.window_manager.my_toolqt.diffuse_hue = (
                                self.diffuse_hue_sat.inputs[0].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 6:

                            if self.diffuse_seamless:
                                self.diffuse_seamless.inputs[1].default_value += (
                                    delta * 20
                                )
                                if self.diffuse_seamless.inputs[1].default_value < 0:
                                    self.diffuse_seamless.inputs[1].default_value = 0
                                if self.diffuse_seamless.inputs[1].default_value > 100:
                                    self.diffuse_seamless.inputs[1].default_value = 100
                                bpy.context.window_manager.my_toolqt.tiling_blend_amount = self.diffuse_seamless.inputs[
                                    1
                                ].default_value

                                self.rough_seamless.inputs[
                                    1
                                ].default_value = (
                                    bpy.context.window_manager.my_toolqt.tiling_blend_amount
                                )
                                self.bump_seamless.inputs[
                                    1
                                ].default_value = (
                                    bpy.context.window_manager.my_toolqt.tiling_blend_amount
                                )
                                if self.alpha_seamless:
                                    self.alpha_seamless.inputs[
                                        1
                                    ].default_value = (
                                        bpy.context.window_manager.my_toolqt.tiling_blend_amount
                                    )
                            else:
                                if self.diffuse_tex.projection == "BOX":
                                    self.diffuse_tex.projection_blend += delta
                                    self.rough_tex.projection_blend += delta
                                    if self.bump_tex:
                                        self.bump_tex.projection_blend += delta
                                    if self.normal_tex:
                                        self.normal_tex.projection_blend += delta
                                    if self.ao_tex:
                                        self.ao_tex.projection_blend += delta
                                    if self.alpha_tex:
                                        self.alpha_tex.projection_blend += delta
                                    if self.disp_tex:
                                        self.disp_tex.projection_blend += delta
                                    if self.mask_tex:
                                        self.mask_tex.projection_blend += delta

                        if bpy.context.window_manager.my_toolqt.activemap == 8:
                            if self.randcolor:
                                self.randcolor.inputs[2].default_value += delta * 20
                                if self.randcolor.inputs[2].default_value < 0:
                                    self.randcolor.inputs[2].default_value = 0
                                if self.randcolor.inputs[2].default_value > 100:
                                    self.randcolor.inputs[2].default_value = 100
                                bpy.context.window_manager.my_toolqt.random_hue = (
                                    self.randcolor.inputs[2].default_value
                                )
                        if bpy.context.window_manager.my_toolqt.activemap == 9:
                            if self.variation:
                                self.variation.inputs[1].default_value += delta * 20
                                if self.variation.inputs[1].default_value < 0:
                                    self.variation.inputs[1].default_value = 0
                                if self.variation.inputs[1].default_value > 100:
                                    self.variation.inputs[1].default_value = 100
                                bpy.context.window_manager.my_toolqt.variation_scale = (
                                    self.variation.inputs[1].default_value
                                )

                    context.area.tag_redraw()

                if self.v:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.005
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[1].default_value += delta
                            if self.blend_bright_contrast.inputs[1].default_value < -30:
                                self.blend_bright_contrast.inputs[1].default_value = -30
                            if self.blend_bright_contrast.inputs[1].default_value > 30:
                                self.blend_bright_contrast.inputs[1].default_value = 30

                            bpy.context.window_manager.my_toolqt.blendvalue = (
                                self.blend_bright_contrast.inputs[1].default_value
                            )

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[1].default_value += delta
                            bpy.context.window_manager.my_toolqt.blendvalue = (
                                self.mask_bright_contrast.inputs[1].default_value
                            )

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[2].default_value += delta
                            if self.diffuse_hue_sat.inputs[2].default_value < -30:
                                self.diffuse_hue_sat.inputs[2].default_value = -30
                            if self.diffuse_hue_sat.inputs[2].default_value > 30:
                                self.diffuse_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.diffuse_val = (
                                self.diffuse_hue_sat.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 2:
                            self.rough_hue_sat.inputs[2].default_value += delta
                            if self.rough_hue_sat.inputs[2].default_value < -30:
                                self.rough_hue_sat.inputs[2].default_value = -30
                            if self.rough_hue_sat.inputs[2].default_value > 30:
                                self.rough_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.rough_hue_sat = (
                                self.rough_hue_sat.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 3:
                            self.bump_hue_sat.inputs[2].default_value += delta
                            if self.bump_hue_sat.inputs[2].default_value < -30:
                                self.bump_hue_sat.inputs[2].default_value = -30
                            if self.bump_hue_sat.inputs[2].default_value > 30:
                                self.bump_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.bump_hue_sat = (
                                self.bump_hue_sat.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 4:
                            self.mask_hue_sat.inputs[2].default_value += delta
                            if self.mask_hue_sat.inputs[2].default_value < -30:
                                self.mask_hue_sat.inputs[2].default_value = -30
                            if self.mask_hue_sat.inputs[2].default_value > 30:
                                self.mask_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.mask_hue_sat = (
                                self.mask_hue_sat.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 5:
                            self.alpha_hue_sat.inputs[2].default_value += delta
                            if self.alpha_hue_sat.inputs[2].default_value < -30:
                                self.alpha_hue_sat.inputs[2].default_value = -30
                            if self.alpha_hue_sat.inputs[2].default_value > 30:
                                self.alpha_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.alpha_hue_sat = (
                                self.alpha_hue_sat.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 6:

                            if self.diffuse_seamless:
                                self.diffuse_seamless.inputs[2].default_value += delta
                                if self.diffuse_seamless.inputs[2].default_value < 0:
                                    self.diffuse_seamless.inputs[2].default_value = 0
                                if self.diffuse_seamless.inputs[2].default_value > 100:
                                    self.diffuse_seamless.inputs[2].default_value = 100
                                bpy.context.window_manager.my_toolqt.tiling_blend_noise = self.diffuse_seamless.inputs[
                                    2
                                ].default_value

                                self.rough_seamless.inputs[
                                    2
                                ].default_value = (
                                    bpy.context.window_manager.my_toolqt.tiling_blend_noise
                                )
                                self.bump_seamless.inputs[
                                    2
                                ].default_value = (
                                    bpy.context.window_manager.my_toolqt.tiling_blend_noise
                                )
                                if self.alpha_seamless:
                                    self.alpha_seamless.inputs[
                                        2
                                    ].default_value = (
                                        bpy.context.window_manager.my_toolqt.tiling_blend_noise
                                    )

                        if bpy.context.window_manager.my_toolqt.activemap == 7:

                            if self.smudge_hue_sat:
                                self.smudge_hue_sat.inputs[2].default_value += (
                                    delta * 20
                                )
                                if self.smudge_hue_sat.inputs[2].default_value < 0:
                                    self.smudge_hue_sat.inputs[2].default_value = 0
                                if self.smudge_hue_sat.inputs[2].default_value > 20:
                                    self.smudge_hue_sat.inputs[2].default_value = 20

                                bpy.context.window_manager.my_toolqt.smudge_hue_sat = (
                                    self.smudge_hue_sat.inputs[2].default_value
                                )

                        if bpy.context.window_manager.my_toolqt.activemap == 8:

                            if self.randcolor:
                                self.randcolor.inputs[4].default_value += delta * 10
                                if self.randcolor.inputs[4].default_value < 0:
                                    self.randcolor.inputs[4].default_value = 0
                                if self.randcolor.inputs[4].default_value > 100:
                                    self.randcolor.inputs[4].default_value = 100
                                bpy.context.window_manager.my_toolqt.random_val = (
                                    self.randcolor.inputs[4].default_value
                                )

                        if bpy.context.window_manager.my_toolqt.activemap == 9:
                            if self.variation:
                                self.variation.inputs[3].default_value += delta * 5
                                if self.variation.inputs[3].default_value < 0:
                                    self.variation.inputs[3].default_value = 0
                                if self.variation.inputs[3].default_value > 1:
                                    self.variation.inputs[3].default_value = 1
                                bpy.context.window_manager.my_toolqt.variation_intensity = (
                                    self.variation.inputs[3].default_value
                                )

                        if bpy.context.window_manager.my_toolqt.activemap == 0:
                            if self.disp_vec:
                                self.disp_vec.inputs[2].default_value += delta
                                if self.disp_vec.inputs[2].default_value < 0:
                                    self.disp_vec.inputs[2].default_value = 0
                                if self.disp_vec.inputs[2].default_value > 5:
                                    self.disp_vec.inputs[2].default_value = 5
                                bpy.context.window_manager.my_toolqt.disp_str = (
                                    self.disp_vec.inputs[2].default_value
                                )

                if self.c:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.005
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[2].default_value += delta
                            if self.blend_bright_contrast.inputs[2].default_value < -30:
                                self.blend_bright_contrast.inputs[2].default_value = -30
                            if self.blend_bright_contrast.inputs[2].default_value > 30:
                                self.blend_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.blendcontrast = (
                                self.blend_bright_contrast.inputs[2].default_value
                            )

                        if self.mask_bright_contrast:

                            self.mask_bright_contrast.inputs[2].default_value += delta
                            if self.mask_bright_contrast.inputs[2].default_value < -30:
                                self.mask_bright_contrast.inputs[2].default_value = -30
                            if self.mask_bright_contrast.inputs[2].default_value > 30:
                                self.mask_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.blendcontrast = (
                                self.mask_bright_contrast.inputs[2].default_value
                            )
                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_bright_contrast.inputs[
                                2
                            ].default_value += delta
                            if (
                                self.diffuse_bright_contrast.inputs[2].default_value
                                < -30
                            ):
                                self.diffuse_bright_contrast.inputs[
                                    2
                                ].default_value = -30
                            if (
                                self.diffuse_bright_contrast.inputs[2].default_value
                                > 30
                            ):
                                self.diffuse_bright_contrast.inputs[
                                    2
                                ].default_value = 30

                            bpy.context.window_manager.my_toolqt.diffuse_contrast = (
                                self.diffuse_bright_contrast.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 2:
                            self.rough_bright_contrast.inputs[2].default_value += delta
                            if self.rough_bright_contrast.inputs[2].default_value < -30:
                                self.rough_bright_contrast.inputs[2].default_value = -30
                            if self.rough_bright_contrast.inputs[2].default_value > 30:
                                self.rough_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.rough_contrast = (
                                self.rough_bright_contrast.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 3:
                            self.bump_bright_contrast.inputs[2].default_value += delta
                            if self.bump_bright_contrast.inputs[2].default_value < -30:
                                self.bump_bright_contrast.inputs[2].default_value = -30
                            if self.bump_bright_contrast.inputs[2].default_value > 30:
                                self.bump_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.bump_contrast = (
                                self.bump_bright_contrast.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 4:
                            self.mask_bright_contrast.inputs[2].default_value += delta
                            if self.mask_bright_contrast.inputs[2].default_value < -30:
                                self.mask_bright_contrast.inputs[2].default_value = -30
                            if self.mask_bright_contrast.inputs[2].default_value > 30:
                                self.mask_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.mask_contrast = (
                                self.mask_bright_contrast.inputs[2].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 5:
                            self.alpha_bright_contrast.inputs[2].default_value += delta
                            if self.alpha_bright_contrast.inputs[2].default_value < -30:
                                self.alpha_bright_contrast.inputs[2].default_value = -30
                            if self.alpha_bright_contrast.inputs[2].default_value > 30:
                                self.alpha_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[
                                2
                            ].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 7:
                            self.smudge_bright_contrast.inputs[2].default_value += delta
                            if (
                                self.smudge_bright_contrast.inputs[2].default_value
                                < -30
                            ):
                                self.smudge_bright_contrast.inputs[
                                    2
                                ].default_value = -30
                            if self.smudge_bright_contrast.inputs[2].default_value > 30:
                                self.smudge_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.smudge_bright_contrast = self.smudge_bright_contrast.inputs[
                                2
                            ].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 8:

                            if self.randval:
                                self.randval.inputs[1].default_value[2] += delta * 10
                                if self.randval.inputs[1].default_value[2] < 0:
                                    self.randval.inputs[1].default_value[2] = 0
                                if self.randval.inputs[1].default_value[2] > 100:
                                    self.randval.inputs[1].default_value[2] = 100
                                bpy.context.window_manager.my_toolqt.random_contrast = (
                                    self.randval.inputs[1].default_value[2]
                                )

                        if bpy.context.window_manager.my_toolqt.activemap == 9:
                            if self.variation:
                                self.variation.inputs[2].default_value += delta * 2
                                if self.variation.inputs[2].default_value < 0:
                                    self.variation.inputs[2].default_value = 0
                                if self.variation.inputs[2].default_value > 1:
                                    self.variation.inputs[2].default_value = 1
                                bpy.context.window_manager.my_toolqt.variation_smoothness = (
                                    self.variation.inputs[2].default_value
                                )

                if self.x:

                    delta = event.mouse_prev_x - event.mouse_x
                    delta *= -0.005
                    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if (
                        bpy.context.window_manager.my_toolqt.blend == 0
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[1].default_value += delta
                            if self.diffuse_hue_sat.inputs[1].default_value < -30:
                                self.diffuse_hue_sat.inputs[1].default_value = -30
                            if self.diffuse_hue_sat.inputs[1].default_value > 30:
                                self.diffuse_hue_sat.inputs[1].default_value = 30

                            bpy.context.window_manager.my_toolqt.diffuse_sat = (
                                self.diffuse_hue_sat.inputs[1].default_value
                            )

                        if bpy.context.window_manager.my_toolqt.activemap == 8:
                            if self.randcolor:
                                self.randcolor.inputs[3].default_value += delta * 2
                                if self.randcolor.inputs[3].default_value < 0:
                                    self.randcolor.inputs[3].default_value = 0
                                if self.randcolor.inputs[3].default_value > 1:
                                    self.randcolor.inputs[3].default_value = 1
                                bpy.context.window_manager.my_toolqt.random_sat = (
                                    self.randcolor.inputs[3].default_value
                                )

                        if bpy.context.window_manager.my_toolqt.activemap == 9:
                            if self.variation:
                                self.variation.inputs[4].default_value += delta * 5
                                if self.variation.inputs[4].default_value < 0:
                                    self.variation.inputs[4].default_value = 0
                                if self.variation.inputs[4].default_value > 1:
                                    self.variation.inputs[4].default_value = 1
                                bpy.context.window_manager.my_toolqt.variation_sat = (
                                    self.variation.inputs[4].default_value
                                )

            # OS KEYS
            elif event.type in {"LEFT_ALT", "RIGHT_ALT"}:
                if event.value == "PRESS":
                    self.alt = 1
                if event.value == "RELEASE":
                    self.alt = 0

            elif event.type == "SPACE":
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
            # KEYS
            #
            # LAYERS
            elif event.type == "N":
                if event.value == "PRESS":

                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.a = 0
                    self.o = 0
                    self.x = 0

                    if self.ctrl == 0 and self.alt == 0 and self.shift == 0:
                        return {"PASS_THROUGH"}

                    elif self.ctrl == 0 and self.alt == 0 and self.shift == 1:
                        if self.shiftn:
                            self.shiftn = 0
                        else:
                            self.shiftn = 1

                    elif self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                        if (
                            bpy.context.window_manager.my_toolqt.blend == 0
                            and bpy.context.window_manager.my_toolqt.mask == 0
                        ):
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith(
                                        "Mask_"
                                        + str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    ):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.normalmask_qt("INVOKE_DEFAULT")

                    elif self.ctrl == 1 and self.alt == 0 and self.shift == 1:

                        if bpy.context.window_manager.my_toolqt.ob.data.materials:
                            for (
                                mat
                            ) in bpy.context.window_manager.my_toolqt.ob.data.materials:
                                if mat:
                                    if mat.name.startswith("QT"):
                                        bpy.ops.object.material_slot_remove()
                            bpy.context.window_manager.my_toolqt.running_qt = 0

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # MOVE
            elif event.type == "G":
                if event.value == "PRESS":

                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.a = 0
                    self.o = 0
                    self.x = 0

                    if self.g:
                        self.g = 0
                        self.mouse_sample_x = []
                        self.mouse_sample_y = []
                    else:
                        self.g = 1
                        self.mouse_sample_x = []
                        self.mouse_sample_y = []

            # SCALE
            elif event.type == "S":
                if event.value == "PRESS":

                    self.g = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.a = 0
                    self.x = 0

                    if self.shift:
                        self.alts = 0
                        if self.shifts:
                            self.shifts = 0
                        else:
                            self.shifts = 1

                    elif self.alt:
                        self.shifts = 0
                        if self.alts:
                            self.alts = 0
                        else:
                            self.alts = 1

                    else:
                        if (
                            bpy.context.window_manager.my_toolqt.blend == 0
                            and bpy.context.window_manager.my_toolqt.mask == 0
                        ):
                            if self.s:
                                self.s = 0
                            else:
                                self.s = 1

            # ROTATE
            elif event.type == "R":
                if event.value == "PRESS":

                    self.g = 0
                    self.s = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.a = 0
                    self.x = 0

                    if (
                        bpy.context.window_manager.my_toolqt.blend == 0
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):

                        if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                            if self.r:
                                self.r = 0
                            else:
                                self.r = 1

                        elif event.ctrl == 0 and event.shift == 0 and event.alt == 1:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.ops.qt.replacemaps("INVOKE_DEFAULT")

                        elif event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.context.window_manager.my_toolqt.running_qt = 0
                            return {"PASS_THROUGH"}

                        elif event.ctrl == 1 and event.shift == 1 and event.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.context.window_manager.my_toolqt.running_qt = 0
                            return {"PASS_THROUGH"}

            # REPROJECT FROM VIEW
            elif event.type == "P" and event.value == "PRESS":

                if (
                    bpy.context.window_manager.my_toolqt.blend == 0
                    and bpy.context.window_manager.my_toolqt.mask == 0
                ):
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.a = 0
                    self.x = 0

                    resetparm = 0
                    empty_uv = None

                    for modifier in bpy.context.window_manager.my_toolqt.ob.modifiers:
                        if modifier.name.startswith(
                            "QT_UV_View_Layer_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            resetparm = 1
                            mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get(
                                modifier.name
                            )
                            empty_uv = mod.projectors[0].object
                            empty_uv.rotation_euler = (
                                context.region_data.view_rotation.to_euler()
                            )

                        if modifier.name.startswith("QT_Decal"):

                            coord = event.mouse_region_x, event.mouse_region_y
                            normal = Vector(
                                (self.rv3d.perspective_matrix[2][0:3])
                            ).normalized()
                            oldloc = bpy.context.window_manager.my_toolqt.ob.location
                            newloc = utils.coord_on_plane(
                                self.region, self.rv3d, coord, oldloc, normal
                            )
                            bpy.context.window_manager.my_toolqt.ob.rotation_euler = (
                                self.rv3d.view_rotation.to_euler()
                            )
                            bpy.context.window_manager.my_toolqt.ob.location = newloc

                            scene = context.scene
                            viewlayer = context.view_layer
                            view_vector = view3d_utils.region_2d_to_vector_3d(self.region, self.rv3d, coord)
                            ray_origin = view3d_utils.region_2d_to_origin_3d(self.region, self.rv3d, coord)
                            result, location, normal, index, hitobj, matrix = scene.ray_cast(
                                viewlayer.depsgraph, ray_origin, view_vector
                            )

                            if hitobj:
                                node_obj = None
                                for mod in bpy.context.window_manager.my_toolqt.ob.modifiers:
                                    if mod.name.startswith("QT_Decal"):
                                        geomod = mod
                                node_tree = bpy.data.node_groups[geomod.node_group.name]
                                for n in node_tree.nodes:
                                    if n.type == "OBJECT_INFO":
                                        if node_obj != n:
                                            node_obj = n
                                node_obj.inputs[0].default_value = hitobj

                                if node_obj:
                                    # parenting
                                    bpy.context.window_manager.my_toolqt.ob.parent = None

                                    bpy.data.objects[hitobj.name].select_set(True)
                                    bpy.context.view_layer.objects.active = hitobj

                                    bpy.ops.object.parent_set(type="OBJECT")
                                    bpy.ops.object.select_all(action="DESELECT")

                                    bpy.data.objects[bpy.context.window_manager.my_toolqt.ob.name].select_set(True)
                                    bpy.context.view_layer.objects.active = bpy.context.window_manager.my_toolqt.ob

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

            # METAL
            elif event.type == "M" and event.value == "PRESS":

                if (
                    bpy.context.window_manager.my_toolqt.blend == 0
                    and bpy.context.window_manager.my_toolqt.mask == 0
                ):
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.a = 0
                    self.x = 0

                    if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                        self.ctrl = 0
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:

                            # check if mask exists on current layer
                            mask = 0
                            for n in self.nodes:
                                if n.name.endswith(
                                    "Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    mask = 1

                            if mask == 0:
                                bpy.ops.qt.texturemask_qt("INVOKE_DEFAULT")

                    elif self.ctrl == 0 and self.alt == 0 and self.shift == 0:
                        bpy.context.window_manager.my_toolqt.metal = (
                            not bpy.context.window_manager.my_toolqt.metal
                        )

                        if bpy.context.window_manager.my_toolqt.metal:
                            if self.core_shader:
                                self.core_shader.inputs[6].default_value = 1
                        else:
                            if self.core_shader:
                                self.core_shader.inputs[6].default_value = 0

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # SSS
            elif event.type == "L":
                if event.value == "PRESS":

                    if (
                        bpy.context.window_manager.my_toolqt.blend == 0
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):
                        self.g = 0
                        self.s = 0
                        self.r = 0
                        self.e = 0
                        self.shifth = 0
                        self.alts = 0
                        self.shifts = 0
                        self.shiftb = 0
                        self.ctrli = 0
                        self.shiftn = 0
                        self.h = 0
                        self.v = 0
                        self.c = 0
                        self.o = 0
                        self.a = 0
                        self.x = 0

                        if self.l:
                            self.l = 0
                        else:
                            self.l = 1

            elif event.type == "A":
                if event.value == "PRESS":

                    if (
                        bpy.context.window_manager.my_toolqt.blend == 0
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):
                        self.g = 0
                        self.s = 0
                        self.r = 0
                        self.l = 0
                        self.shifth = 0
                        self.alts = 0
                        self.shifts = 0
                        self.shiftb = 0
                        self.ctrli = 0
                        self.shiftn = 0
                        self.h = 0
                        self.v = 0
                        self.c = 0
                        self.o = 0
                        self.e = 0
                        self.x = 0

                        if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                            self.ctrl = 0
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:

                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith(
                                        "Mask_"
                                        + str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    ):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.aomask_qt("INVOKE_DEFAULT")

                        elif self.ctrl == 0 and self.shift == 0 and self.alt == 1:
                            self.ctrl = 0
                            self.shift = 0

                            if self.alpha_type:
                                self.node_tree.links.new(
                                    self.alpha_tex.outputs[0],
                                    self.alpha_hue_sat.inputs[4],
                                )
                                self.alpha_type = 0
                            else:
                                self.node_tree.links.new(
                                    self.alpha_tex.outputs[1],
                                    self.alpha_hue_sat.inputs[4],
                                )
                                self.alpha_type = 1

                        elif self.ctrl == 0 and self.shift == 1 and self.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0

                            # check if mask exists on current layer
                            mask = 0
                            for n in self.nodes:
                                if n.name.endswith(
                                    "Smudge_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    mask = 1

                            if mask == 0:
                                bpy.ops.qt.smudge_qt("INVOKE_DEFAULT")

                        elif self.ctrl == 0 and self.shift == 0 and self.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            if self.a:
                                self.a = 0
                            else:
                                self.a = 1

                        self.ctrl = 0
                        self.shift = 0
                        self.alt = 0

            # EMISSION
            elif event.type == "E":
                if event.value == "PRESS":
                    self.a = 0
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftn = 0
                    self.shiftb = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.x = 0

                    if self.ctrl == 0 and self.shift == 0 and self.alt == 0:
                        if self.e:
                            self.e = 0
                        else:
                            self.e = 1

            # BUMP
            elif event.type == "B":
                if event.value == "PRESS":

                    self.a = 0
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.ctrli = 0
                    self.shiftn = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.x = 0
                    self.o = 0

                    if (
                        bpy.context.window_manager.my_toolqt.blend == 0
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):
                        # NEW BOX LAYER
                        if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                            if bpy.context.window_manager.my_toolqt.activelayer < 5:
                                bpy.ops.qt.boxlayer_qt("INVOKE_DEFAULT")

                    if self.shift == 1 and self.ctrl == 0 and self.alt == 0:
                        if self.shiftb:
                            self.shiftb = 0
                        else:
                            self.shiftb = 1

                    if self.shift == 0 and self.ctrl == 0 and self.alt == 1:
                        if self.bump_layer:
                            if bpy.context.window_manager.my_toolqt.bump_layer < 0:
                                self.bump_layer.inputs[3].default_value = 0
                                bpy.context.window_manager.my_toolqt.bump_layer = 0
                            elif bpy.context.window_manager.my_toolqt.bump_layer > 0:
                                self.bump_layer.inputs[3].default_value = -10
                                bpy.context.window_manager.my_toolqt.bump_layer = -10
                            else:
                                self.bump_layer.inputs[3].default_value = 10
                                bpy.context.window_manager.my_toolqt.bump_layer = 10

                    if self.shift == 1 and self.ctrl == 1 and self.alt == 0:
                        bpy.context.window_manager.my_toolqt.running_qt = 0
                        return {"PASS_THROUGH"}

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # HUE
            elif event.type == "H":
                if event.value == "PRESS":

                    self.a = 0
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftn = 0
                    self.shiftb = 0
                    self.ctrli = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.x = 0

                    if self.ctrl:
                        self.ctrl = 0
                        if (
                            bpy.context.window_manager.my_toolqt.blend == 0
                            and bpy.context.window_manager.my_toolqt.mask == 0
                        ):
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith(
                                        "Mask_"
                                        + str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    ):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.heightmask_qt("INVOKE_DEFAULT")

                    elif self.alt:
                        self.alt = 0
                        if (
                            bpy.context.window_manager.my_toolqt.blend == 0
                            and bpy.context.window_manager.my_toolqt.mask == 0
                        ):
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith(
                                        "Mask_"
                                        + str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    ):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.depthmask_qt("INVOKE_DEFAULT")

                    elif self.shift:
                        if self.shifth:
                            self.shifth = 0
                        else:
                            self.shifth = 1

                    else:
                        if self.h:
                            self.h = 0
                        else:
                            self.h = 1

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            elif event.type in {
                "F1",
                "F2",
                "F3",
                "F4",
                "F5",
                "F6",
                "F7",
                "F8",
                "F9",
                "F10",
                "F11",
                "F12",
            }:
                return {"PASS_THROUGH"}

            elif event.type == "V":
                if event.value == "PRESS":

                    if self.alt:
                        return {"PASS_THROUGH"}

                    else:
                        self.a = 0
                        self.g = 0
                        self.s = 0
                        self.r = 0
                        self.l = 0
                        self.e = 0
                        self.shifth = 0
                        self.alts = 0
                        self.shifts = 0
                        self.shiftb = 0
                        self.shiftn = 0
                        self.ctrli = 0
                        self.h = 0
                        self.c = 0
                        self.o = 0
                        self.x = 0

                        # NEW VIEW LAYER
                        if self.ctrl:
                            self.ctrl = 0
                            if (
                                bpy.context.window_manager.my_toolqt.blend == 0
                                and bpy.context.window_manager.my_toolqt.mask == 0
                            ):
                                if bpy.context.window_manager.my_toolqt.activelayer < 5:
                                    bpy.ops.qt.viewlayer_qt("INVOKE_DEFAULT")

                        elif self.shift:
                            self.shift = 0
                            bpy.ops.qt.vertexmask_qt("INVOKE_DEFAULT")

                        else:
                            if self.v:
                                self.v = 0
                            else:
                                self.v = 1

                        self.ctrl = 0
                        self.shift = 0
                        self.alt = 0

            elif event.type == "C":
                if event.value == "PRESS":

                    self.a = 0
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftn = 0
                    self.shiftb = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.o = 0
                    self.x = 0

                    if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                        if (
                            bpy.context.window_manager.my_toolqt.blend == 0
                            and bpy.context.window_manager.my_toolqt.mask == 0
                        ):
                            self.ctrl = 0
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:

                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith(
                                        "Mask_"
                                        + str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    ):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.cavitymask_qt("INVOKE_DEFAULT")


                    elif self.alt == 1 and self.shift == 0 and self.ctrl == 0:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
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

                        elif bpy.context.window_manager.my_toolqt.activemap == 2:
                            if self.rough_tex:
                                if self.rough_tex.extension == "CLIP":
                                    self.rough_tex.extension = "REPEAT"
                                else:
                                    self.rough_tex.extension = "CLIP"

                        elif bpy.context.window_manager.my_toolqt.activemap == 3:
                            if self.bump_tex:
                                if self.bump_tex.extension == "CLIP":
                                    self.bump_tex.extension = "REPEAT"
                                else:
                                    self.bump_tex.extension = "CLIP"

                        elif bpy.context.window_manager.my_toolqt.activemap == 4:
                            if self.mask_tex:
                                if self.mask_tex.extension == "CLIP":
                                    self.mask_tex.extension = "REPEAT"
                                else:
                                    self.mask_tex.extension = "CLIP"

                        elif bpy.context.window_manager.my_toolqt.activemap == 5:
                            if self.alpha_tex:
                                if self.alpha_tex.extension == "CLIP":
                                    self.alpha_tex.extension = "REPEAT"
                                else:
                                    self.alpha_tex.extension = "CLIP"

                    elif self.alt == 0 and self.shift == 0 and self.shift == 0:
                        if self.c:
                            self.c = 0
                        else:
                            self.c = 1

                        # triplanar
                        if bpy.context.window_manager.my_toolqt.activemap == 6:
                            if (
                                self.tex_coord.label == "Box"
                                or self.tex_coord.label == "UV"
                            ):
                                if self.diffuse_tex:

                                    if self.diffuse_tex.projection == "FLAT":

                                        bpy.context.window_manager.my_toolqt.triplanar = (
                                            1
                                        )

                                        self.diffuse_tex.projection = "BOX"
                                        self.diffuse_tex.projection_blend = 0.3
                                        self.rough_tex.projection = "BOX"
                                        self.rough_tex.projection_blend = 0.3

                                        t_name = self.tex_coord.name
                                        t_label = self.tex_coord.label
                                        t_location = self.tex_coord.location
                                        self.node_tree.nodes.remove(self.tex_coord)
                                        self.tex_coord = self.node_tree.nodes.new(
                                            "ShaderNodeTexCoord"
                                        )
                                        self.tex_coord.name = t_name
                                        self.tex_coord.label = t_label
                                        self.tex_coord.location = t_location

                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[0],
                                            self.diffuse_mapping.inputs[0],
                                        )
                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[0],
                                            self.rough_mapping.inputs[0],
                                        )

                                        if self.bump_tex:
                                            self.bump_tex.projection = "BOX"
                                            self.bump_tex.projection_blend = 0.3
                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[0],
                                                self.bump_mapping.inputs[0],
                                            )
                                        if self.normal_tex:
                                            self.normal_tex.projection = "BOX"
                                            self.normal_tex.projection_blend = 0.3
                                        if self.ao_tex:
                                            self.ao_tex.projection = "BOX"
                                            self.ao_tex.projection_blend = 0.3
                                        if self.alpha_tex:
                                            self.alpha_tex.projection = "BOX"
                                            self.alpha_tex.projection_blend = 0.3
                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[0],
                                                self.alpha_mapping.inputs[0],
                                            )
                                        if self.mask_tex:
                                            self.mask_tex.projection = "BOX"
                                            self.mask_tex.projection_blend = 0.3
                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[0],
                                                self.mask_mapping.inputs[0],
                                            )

                                    else:

                                        bpy.context.window_manager.my_toolqt.triplanar = (
                                            0
                                        )

                                        self.diffuse_tex.projection = "FLAT"
                                        self.rough_tex.projection = "FLAT"

                                        if self.tex_coord.label == "UV":

                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[2],
                                                self.diffuse_mapping.inputs[0],
                                            )
                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[2],
                                                self.rough_mapping.inputs[0],
                                            )

                                            if self.bump_tex:
                                                self.bump_tex.projection = "FLAT"
                                                self.node_tree.links.new(
                                                    self.tex_coord.outputs[2],
                                                    self.bump_mapping.inputs[0],
                                                )
                                            if self.normal_tex:
                                                self.normal_tex.projection = "FLAT"
                                            if self.ao_tex:
                                                self.ao_tex.projection = "FLAT"
                                            if self.alpha_tex:
                                                self.alpha_tex.projection = "FLAT"
                                                self.node_tree.links.new(
                                                    self.tex_coord.outputs[2],
                                                    self.alpha_mapping.inputs[0],
                                                )
                                            if self.mask_tex:
                                                self.mask_tex.projection = "FLAT"
                                                self.node_tree.links.new(
                                                    self.tex_coord.outputs[2],
                                                    self.mask_mapping.inputs[0],
                                                )

                                        else:
                                            t_name = self.tex_coord.name
                                            t_label = self.tex_coord.label
                                            t_location = self.tex_coord.location
                                            self.node_tree.nodes.remove(self.tex_coord)
                                            self.tex_coord = self.node_tree.nodes.new(
                                                "ShaderNodeUVMap"
                                            )
                                            self.tex_coord.name = t_name
                                            self.tex_coord.label = t_label
                                            self.tex_coord.location = t_location
                                            self.tex_coord.uv_map = "QT_UV_Box_Layer_1"

                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[0],
                                                self.diffuse_mapping.inputs[0],
                                            )
                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[0],
                                                self.rough_mapping.inputs[0],
                                            )

                                            if self.bump_tex:
                                                self.bump_tex.projection = "FLAT"
                                                self.node_tree.links.new(
                                                    self.tex_coord.outputs[0],
                                                    self.bump_mapping.inputs[0],
                                                )
                                            if self.normal_tex:
                                                self.normal_tex.projection = "FLAT"
                                            if self.ao_tex:
                                                self.ao_tex.projection = "FLAT"
                                            if self.alpha_tex:
                                                self.alpha_tex.projection = "FLAT"
                                                self.node_tree.links.new(
                                                    self.tex_coord.outputs[0],
                                                    self.alpha_mapping.inputs[0],
                                                )
                                            if self.mask_tex:
                                                self.mask_tex.projection = "FLAT"
                                                self.node_tree.links.new(
                                                    self.tex_coord.outputs[0],
                                                    self.mask_mapping.inputs[0],
                                                )

                                    # mapping scale reset

                                    self.diffuse_mapping.inputs[3].default_value[0] = 1
                                    self.diffuse_mapping.inputs[3].default_value[1] = 1
                                    self.diffuse_mapping.inputs[3].default_value[2] = 1

                                    self.rough_mapping.inputs[3].default_value[0] = 1
                                    self.rough_mapping.inputs[3].default_value[1] = 1
                                    self.rough_mapping.inputs[3].default_value[2] = 1

                                    self.bump_mapping.inputs[3].default_value[0] = 1
                                    self.bump_mapping.inputs[3].default_value[1] = 1
                                    self.bump_mapping.inputs[3].default_value[2] = 1

                                    self.alpha_mapping.inputs[3].default_value[0] = 1
                                    self.alpha_mapping.inputs[3].default_value[1] = 1
                                    self.alpha_mapping.inputs[3].default_value[2] = 1

                                    if self.alpha_mapping:
                                        self.alpha_mapping.inputs[3].default_value[
                                            0
                                        ] = 1
                                        self.alpha_mapping.inputs[3].default_value[
                                            1
                                        ] = 1
                                        self.alpha_mapping.inputs[3].default_value[
                                            2
                                        ] = 1

                                    # smudge
                                    for n in self.node_tree.nodes:
                                        if n.type == "MAPPING":
                                            self.node_tree.links.new(
                                                self.tex_coord.outputs[0],
                                                self.smudge.inputs[0],
                                            )
                                            self.node_tree.links.new(
                                                self.smudge.outputs[0], n.inputs[0]
                                            )

                                context.area.tag_redraw()

            # OPACITY
            elif event.type == "O":
                if event.value == "PRESS":

                    self.a = 0
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifth = 0
                    self.alts = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.x = 0

                    if (
                        bpy.context.window_manager.my_toolqt.blend
                        or bpy.context.window_manager.my_toolqt.mask
                    ):
                        if self.o:
                            self.o = 0
                        else:
                            self.o = 1
                    else:
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            if self.o:
                                self.o = 0
                            else:
                                for n in self.nodes:
                                    if n.name.startswith(
                                        "QT_Layer_"
                                        + str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    ):
                                        self.o = 1

            # INVERT
            elif event.type == "I" and event.value == "PRESS":

                if self.ctrl:
                    if bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_invert.inputs[
                            0
                        ].default_value = not self.rough_invert.inputs[0].default_value

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_invert.inputs[
                            0
                        ].default_value = not self.bump_invert.inputs[0].default_value

                    elif bpy.context.window_manager.my_toolqt.activemap == 4:
                        if self.ao_mask:
                            self.ao_mask.inside = not self.ao_mask.inside
                        else:
                            self.mask_invert.inputs[
                                0
                            ].default_value = not self.mask_invert.inputs[0].default_value

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_invert.inputs[
                            0
                        ].default_value = not self.alpha_invert.inputs[0].default_value

                    elif bpy.context.window_manager.my_toolqt.activemap == 7:
                        self.smudge_invert.inputs[
                            0
                        ].default_value = not self.smudge_invert.inputs[0].default_value

                    elif bpy.context.window_manager.my_toolqt.activemap == 8:
                        if self.randcolor:
                            self.randcolor.inputs[1].default_value += 0.1
                            bpy.context.window_manager.my_toolqt.random_seed = (
                                self.randcolor.inputs[1].default_value
                            )

                    context.area.tag_redraw()

            # PIE
            elif event.ctrl and event.type == "D" and event.value == "PRESS":
                if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                    self.ctrl = 0
                    self.alt = 0
                    self.shift = 0
                    bpy.ops.wm.call_menu_pie(name="VIEW3D_MT_QT_PIE1")

            # SHADOW
            elif event.alt and event.type == "D" and event.value == "PRESS":
                if self.ctrl == 0 and self.shift == 0 and self.alt == 1:
                    self.ctrl = 0
                    self.alt = 0
                    self.shift = 0
                    if self.mat.shadow_method == "HASHED":
                        self.mat.shadow_method = "NONE"
                    else:
                        self.mat.shadow_method = "HASHED"
                    if bpy.context.scene.render.engine == 'CYCLES':
                        bpy.context.object.visible_shadow = not bpy.context.object.visible_shadow
                        bpy.context.object.visible_glossy = not bpy.context.object.visible_glossy
                        bpy.context.object.visible_diffuse = not bpy.context.object.visible_diffuse

            # DUPLICATE LAYER
            elif event.shift and event.type == "D" and event.value == "PRESS":

                if bpy.context.window_manager.my_toolqt.activelayer < 5:
                    bpy.context.window_manager.my_toolqt.activelayer += 1

                    layer1 = None
                    layer2 = None
                    layer3 = None
                    layer4 = None
                    layer5 = None

                    blend1 = None
                    blend2 = None
                    blend3 = None
                    blend4 = None
                    blend5 = None

                    nodes = []
                    for n in self.nodes:
                        if n.name.endswith(
                            str(bpy.context.window_manager.my_toolqt.activelayer - 1)
                        ):
                            n.select = False
                            nodes.append(n)

                        if n.name.startswith("QT_Shader_1"):
                            layer1 = n

                        if n.name.startswith("QT_Shader_2"):
                            layer2 = n

                        if n.name.startswith("QT_Shader_3"):
                            layer3 = n

                        if n.name.startswith("QT_Shader_4"):
                            layer4 = n

                    if bpy.context.window_manager.my_toolqt.activelayer == 2 and layer2:
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith("_4"):
                                    n.name = n.name.replace("_4", "_5")
                                    n.label = n.label.replace("_4", "_5")
                                    n.location.y -= 2000
                        if layer3:
                            for n in self.nodes:
                                if n.name.endswith("_3"):
                                    n.name = n.name.replace("_3", "_4")
                                    n.label = n.label.replace("_3", "_4")
                                    n.location.y -= 2000
                        if layer2:
                            for n in self.nodes:
                                if n.name.endswith("_2"):
                                    n.name = n.name.replace("_2", "_3")
                                    n.label = n.label.replace("_2", "_3")
                                    n.location.y -= 2000

                    if bpy.context.window_manager.my_toolqt.activelayer == 3 and layer3:
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith("_4"):
                                    n.name = n.name.replace("_4", "_5")
                                    n.label = n.label.replace("_4", "_5")
                                    n.location.y -= 2000
                        if layer3:
                            for n in self.nodes:
                                if n.name.endswith("_3"):
                                    n.name = n.name.replace("_3", "_4")
                                    n.label = n.label.replace("_3", "_4")
                                    n.location.y -= 2000

                    if bpy.context.window_manager.my_toolqt.activelayer == 4 and layer4:
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith("_4"):
                                    n.name = n.name.replace("_4", "_5")
                                    n.label = n.label.replace("_4", "_5")
                                    n.location.y -= 2000

                    for node in nodes:
                        if node.type != "GROUP_OUTPUT":

                            # copy node
                            node_new = self.nodes.new(node.bl_idname)

                            # get old node settings
                            attributes = []
                            input_attributes = ("default_value", "name")
                            output_attributes = ("default_value", "name")
                            ignore_attributes = (
                                "rna_type",
                                "type",
                                "dimensions",
                                "inputs",
                                "outputs",
                                "internal_links",
                                "select",
                                "texture_mapping",
                                "color_mapping",
                                "image_user",
                                "color_ramp",
                                "hops",
                                "node_preview",
                                "extremepbr_node_prop",
                                "lightmixer",
                            )
                            for attr in node.bl_rna.properties:
                                if (
                                    not attr.identifier in ignore_attributes
                                    and not attr.identifier.split("_")[0] == "bl"
                                ):
                                    attributes.append(attr.identifier)

                            # copy attributes
                            for attr in attributes:
                                if hasattr(node_new, attr):
                                    setattr(node_new, attr, getattr(node, attr))

                            # copy the attributes for all inputs
                            for i, inp in enumerate(node.inputs):
                                # copy input attributes
                                for attr in input_attributes:
                                    if hasattr(node_new.inputs[i], attr):
                                        setattr(
                                            node_new.inputs[i], attr, getattr(inp, attr)
                                        )

                            # copy the attributes for all outputs
                            for i, out in enumerate(node.outputs):
                                # copy output attributes
                                for attr in output_attributes:
                                    if hasattr(node_new.outputs[i], attr):
                                        setattr(
                                            node_new.outputs[i],
                                            attr,
                                            getattr(out, attr),
                                        )

                            node_new.location = node.location
                            node_new.location.y -= 2000

                            node_new.name = node.name

                            if bpy.context.window_manager.my_toolqt.activelayer == 2:
                                node_new.name = node_new.name.replace("1.001", "2")
                                node_new.label = node_new.label.replace(
                                    "Layer_1", "Layer_2"
                                )
                            if bpy.context.window_manager.my_toolqt.activelayer == 3:
                                node_new.name = node_new.name.replace("2.001", "3")
                                node_new.label = node_new.label.replace(
                                    "Layer_2", "Layer_3"
                                )
                            if bpy.context.window_manager.my_toolqt.activelayer == 4:
                                node_new.name = node_new.name.replace("3.001", "4")
                                node_new.label = node_new.label.replace(
                                    "Layer_3", "Layer_4"
                                )
                            if bpy.context.window_manager.my_toolqt.activelayer == 5:
                                node_new.name = node_new.name.replace("4.001", "5")
                                node_new.label = node_new.label.replace(
                                    "Layer_4", "Layer_5"
                                )

                    # NAMES
                    for n in self.nodes:
                        # ACTIVE LAYER
                        if n.name.startswith(
                            "QT_Shader_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer - 1)
                        ):
                            self.prev_shader = n
                        if n.name.startswith(
                            "QT_Shader_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.new_shader = n

                        if n.name.startswith(
                            "QT_Layer_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer - 1)
                        ):
                            self.prev_blend_node = n

                        if n.name.startswith(
                            "QT_Layer_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.final_node = n

                        if n.name == "Group Output":
                            self.out_node = n

                        # coord
                        if n.name.startswith(
                            "QT_UV_Layer_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.tex_coord = n

                        # normal
                        if n.name.startswith(
                            "QT_Normal_Tex_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.normal_tex = n
                        if n.name.startswith(
                            "QT_Normal_Strength_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.normal_strength = n

                        # mapping
                        if n.name.startswith(
                            "QT_Diffuse_Mapping_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.diffuse_mapping = n
                        if n.name.startswith(
                            "QT_Rough_Mapping_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.rough_mapping = n
                        if n.name.startswith(
                            "QT_Bump_Mapping_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_mapping = n

                        # clamps
                        if n.name.startswith(
                            "QT_Clamp_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.mask_clamp = n
                        if n.name.startswith(
                            "QT_Roughness_Clamp_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.rough_clamp = n
                        if n.name.startswith(
                            "QT_Bump_Clamp_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_clamp = n

                        # textures
                        if n.name.startswith(
                            "QT_Diffuse_Tex_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.diffuse_tex = n
                        if n.name.startswith(
                            "QT_Diffuse_Hue_Sat_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.diffuse_hue_sat = n
                        if n.name.startswith(
                            "QT_Diffuse_Bright_Contrast_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.diffuse_bright_contrast = n

                        if n.name.startswith(
                            "QT_Rough_Tex_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.rough_tex = n
                        if n.name.startswith(
                            "QT_Rough_Bright_Contrast_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.rough_bright_contrast = n
                        if n.name.startswith(
                            "QT_Rough_Invert_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.rough_invert = n
                        if n.name.startswith(
                            "QT_Rough_Hue_Sat_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.rough_hue_sat = n

                        if n.name.startswith(
                            "QT_Bump_Tex_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_tex = n
                        if n.name.startswith(
                            "QT_Bump_Bright_Contrast_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_bright_contrast = n
                        if n.name.startswith(
                            "QT_Bump_Bump_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_bump = n
                        if n.name.startswith(
                            "QT_Bump_Strength_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_strength = n
                        if n.name.startswith(
                            "QT_Bump_Invert_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_invert = n
                        if n.name.startswith(
                            "QT_Bump_Hue_Sat_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.bump_hue_sat = n

                        # masks
                        if n.name.startswith(
                            "QT_Tex_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.mask_tex = n
                        if n.name.startswith(
                            "QT_Bright_Contrast_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.mask_bright_contrast = n
                        if n.name.startswith(
                            "QT_Invert_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.mask_invert = n
                        if n.name.startswith(
                            "QT_Hue_Sat_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.mask_hue_sat = n
                        if n.name.startswith(
                            "QT_Mapping_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.mask_mapping = n

                        # alpha
                        if n.name.startswith(
                            "QT_Alpha_Mapping_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.alpha_mapping = n
                        if n.name.startswith(
                            "QT_Alpha_Tex_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.alpha_tex = n
                        if n.name.startswith(
                            "QT_Alpha_Bright_Contrast_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.alpha_bright_contrast = n
                        if n.name.startswith(
                            "QT_Alpha_Invert_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.alpha_invert = n
                        if n.name.startswith(
                            "QT_Alpha_Hue_Sat_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.alpha_hue_sat = n
                        if n.name.startswith(
                            "QT_Alpha_Clamp_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.alpha_clamp = n

                        # ao
                        if n.name.startswith(
                            "QT_AO_Tex_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.ao_tex = n
                        if n.name.startswith(
                            "QT_AO_Multiply_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.ao_multiply = n

                        # height
                        if n.name.startswith(
                            "QT_Power_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.blend_power = n
                        if n.name.startswith(
                            "QT_Noise_Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            self.blend_noise = n

                        # blend
                        if bpy.context.window_manager.my_toolqt.blend:
                            if n.name == ("QT_Blend_Add"):
                                self.blend_add = n
                            if n.name == ("QT_Blend_XYZ"):
                                self.blend_xyz = n
                            if n.name == ("QT_Blend_Math"):
                                self.blend_math = n
                            if n.name == ("QT_Blend_Power"):
                                self.blend_power = n
                            if n.name == ("QT_Blend_Clamp"):
                                self.blend_clamp = n
                            if n.name == ("QT_Blend_Mix"):
                                self.blend_mix = n
                            if n.name == ("QT_Blend_Noise"):
                                self.blend_noise = n
                            if n.name == ("QT_Blend_Bright_Contrast"):
                                self.blend_bright_contrast = n
                            if n.name == "QT_Blend_Mix":
                                self.final_node = n
                                self.core_shader = n

                    # LINKS
                    if (
                        self.tex_coord.label == "Decal"
                        or self.tex_coord.label == "View"
                        or self.tex_coord.label == "Box"
                    ):
                        self.node_tree.links.new(
                            self.tex_coord.outputs[0], self.diffuse_mapping.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.tex_coord.outputs[0], self.rough_mapping.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.tex_coord.outputs[0], self.bump_mapping.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.tex_coord.outputs[0], self.alpha_mapping.inputs[0]
                        )
                    else:
                        self.node_tree.links.new(
                            self.tex_coord.outputs[2], self.diffuse_mapping.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.tex_coord.outputs[2], self.rough_mapping.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.tex_coord.outputs[2], self.bump_mapping.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.tex_coord.outputs[2], self.alpha_mapping.inputs[0]
                        )

                    self.node_tree.links.new(
                        self.diffuse_mapping.outputs[0], self.diffuse_tex.inputs[0]
                    )
                    self.node_tree.links.new(
                        self.diffuse_tex.outputs[0], self.diffuse_hue_sat.inputs[4]
                    )
                    self.node_tree.links.new(
                        self.diffuse_hue_sat.outputs[0],
                        self.diffuse_bright_contrast.inputs[0],
                    )
                    self.node_tree.links.new(
                        self.diffuse_bright_contrast.outputs[0],
                        self.new_shader.inputs[0],
                    )
                    self.node_tree.links.new(
                        self.diffuse_bright_contrast.outputs[0],
                        self.new_shader.inputs[19],
                    )

                    self.node_tree.links.new(
                        self.rough_mapping.outputs[0], self.rough_tex.inputs[0]
                    )
                    self.node_tree.links.new(
                        self.rough_tex.outputs[0], self.rough_hue_sat.inputs[4]
                    )
                    self.node_tree.links.new(
                        self.rough_hue_sat.outputs[0], self.rough_invert.inputs[1]
                    )
                    self.node_tree.links.new(
                        self.rough_invert.outputs[0],
                        self.rough_bright_contrast.inputs[0],
                    )
                    self.node_tree.links.new(
                        self.rough_bright_contrast.outputs[0], self.new_shader.inputs[9]
                    )

                    self.node_tree.links.new(
                        self.rough_bright_contrast.outputs[0],
                        self.rough_clamp.inputs[0],
                    )
                    self.node_tree.links.new(
                        self.rough_clamp.outputs[0], self.new_shader.inputs[9]
                    )

                    self.node_tree.links.new(
                        self.bump_tex.outputs[0], self.bump_hue_sat.inputs[4]
                    )
                    self.node_tree.links.new(
                        self.bump_hue_sat.outputs[0], self.bump_invert.inputs[1]
                    )
                    self.node_tree.links.new(
                        self.bump_invert.outputs[0], self.bump_bright_contrast.inputs[0]
                    )
                    self.node_tree.links.new(
                        self.bump_bright_contrast.outputs[0], self.bump_bump.inputs[2]
                    )

                    self.node_tree.links.new(
                        self.bump_bright_contrast.outputs[0], self.bump_clamp.inputs[0]
                    )
                    self.node_tree.links.new(
                        self.bump_clamp.outputs[0], self.bump_strength.inputs[0]
                    )
                    self.node_tree.links.new(
                        self.bump_strength.outputs[0], self.bump_bump.inputs[2]
                    )

                    self.node_tree.links.new(
                        self.bump_mapping.outputs[0], self.bump_tex.inputs[0]
                    )
                    self.node_tree.links.new(
                        self.bump_bump.outputs[0], self.new_shader.inputs[22]
                    )

                    # normal
                    if self.normal_tex:
                        self.node_tree.links.new(
                            self.diffuse_mapping.outputs[0], self.normal_tex.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.normal_tex.outputs[0], self.normal_strength.inputs[1]
                        )
                        self.node_tree.links.new(
                            self.normal_strength.outputs[0], self.bump_bump.inputs[3]
                        )

                    # ao
                    if self.ao_tex:
                        self.node_tree.links.new(
                            self.diffuse_mapping.outputs[0], self.ao_tex.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.ao_tex.outputs[0], self.ao_multiply.inputs[2]
                        )
                        self.node_tree.links.new(
                            self.diffuse_tex.outputs[0], self.ao_multiply.inputs[1]
                        )
                        self.node_tree.links.new(
                            self.ao_multiply.outputs[0], self.diffuse_hue_sat.inputs[4]
                        )

                    self.node_tree.links.new(
                        self.alpha_mapping.outputs[0], self.alpha_tex.inputs[0]
                    )
                    self.node_tree.links.new(
                        self.alpha_tex.outputs[1], self.alpha_hue_sat.inputs[4]
                    )
                    self.node_tree.links.new(
                        self.alpha_hue_sat.outputs[0], self.alpha_invert.inputs[1]
                    )
                    self.node_tree.links.new(
                        self.alpha_invert.outputs[0],
                        self.alpha_bright_contrast.inputs[0],
                    )
                    self.node_tree.links.new(
                        self.alpha_bright_contrast.outputs[0],
                        self.alpha_clamp.inputs[0],
                    )
                    self.node_tree.links.new(
                        self.alpha_clamp.outputs[0], self.new_shader.inputs[21]
                    )

                    # BLEND
                    if bpy.context.window_manager.my_toolqt.activelayer == 2:
                        self.blend_node = self.node_tree.nodes.new(
                            "ShaderNodeMixShader"
                        )
                        self.blend_node.name = "QT_Layer_" + str(
                            bpy.context.window_manager.my_toolqt.activelayer
                        )
                        self.blend_node.inputs[0].default_value = 1

                        self.node_tree.links.new(
                            self.prev_shader.outputs[0], self.blend_node.inputs[1]
                        )
                        self.node_tree.links.new(
                            self.new_shader.outputs[0], self.blend_node.inputs[2]
                        )
                        self.node_tree.links.new(
                            self.blend_node.outputs[0], self.out_node.inputs[0]
                        )

                        self.blend_node.location.x = self.new_shader.location.x + 300
                        self.blend_node.location.y = self.new_shader.location.y

                        self.out_node.location.y = self.blend_node.location.y
                        self.out_node.location.x = self.blend_node.location.x + 300

                    if bpy.context.window_manager.my_toolqt.activelayer == 3:

                        self.node_tree.links.new(
                            self.prev_blend_node.outputs[0], self.final_node.inputs[1]
                        )
                        self.node_tree.links.new(
                            self.new_shader.outputs[0], self.final_node.inputs[2]
                        )
                        self.node_tree.links.new(
                            self.final_node.outputs[0], self.out_node.inputs[0]
                        )

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                    if bpy.context.window_manager.my_toolqt.activelayer == 4:

                        self.node_tree.links.new(
                            self.prev_blend_node.outputs[0], self.final_node.inputs[1]
                        )
                        self.node_tree.links.new(
                            self.new_shader.outputs[0], self.final_node.inputs[2]
                        )
                        self.node_tree.links.new(
                            self.final_node.outputs[0], self.out_node.inputs[0]
                        )

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                    if bpy.context.window_manager.my_toolqt.activelayer == 5:

                        self.node_tree.links.new(
                            self.prev_blend_node.outputs[0], self.final_node.inputs[1]
                        )
                        self.node_tree.links.new(
                            self.new_shader.outputs[0], self.final_node.inputs[2]
                        )
                        self.node_tree.links.new(
                            self.final_node.outputs[0], self.out_node.inputs[0]
                        )

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                    for n in self.nodes:
                        if n.name.startswith("QT_Shader_1"):
                            layer1 = n

                        if n.name.startswith("QT_Layer_2"):
                            layer2 = n

                        if n.name.startswith("QT_Layer_3"):
                            layer3 = n

                        if n.name.startswith("QT_Layer_4"):
                            layer4 = n

                        if n.name.startswith("QT_Layer_5"):
                            layer5 = n

                        if n.name.startswith("QT_Blend_1"):
                            blend1 = n

                        if n.name.startswith("QT_Blend_2"):
                            blend2 = n

                        if n.name.startswith("QT_Blend_3"):
                            blend3 = n

                        if n.name.startswith("QT_Blend_4"):
                            blend4 = n

                        if n.name.startswith("QT_Blend_5"):
                            blend5 = n

                    if layer2:
                        self.node_tree.links.new(layer1.outputs[0], layer2.inputs[1])

                    if layer3:
                        self.node_tree.links.new(layer2.outputs[0], layer3.inputs[1])

                    if layer4:
                        self.node_tree.links.new(layer3.outputs[0], layer4.inputs[1])

                    if layer5:
                        self.node_tree.links.new(layer4.outputs[0], layer5.inputs[1])

                    if blend2:
                        self.node_tree.links.new(layer1.outputs[0], blend2.inputs[1])

                    if blend3:
                        self.node_tree.links.new(layer2.outputs[0], blend3.inputs[1])

                    if blend4:
                        self.node_tree.links.new(layer3.outputs[0], blend4.inputs[1])

                    if blend5:
                        self.node_tree.links.new(layer4.outputs[0], blend5.inputs[1])

                    context.area.tag_redraw()

            # ACTIVE MAP
            elif event.type in {"ONE"} and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftn = 0
                self.shiftb = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.x = 0
                self.o = 0

                if self.ctrl:
                    self.ctrl = 0
                    bpy.context.window_manager.my_toolqt.matindex = 0
                    bpy.context.window_manager.my_toolqt.activemap = 1
                    bpy.context.window_manager.my_toolqt.activelayer = 1
                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0:

                        bpy.context.window_manager.my_toolqt.mask = 0
                        bpy.context.window_manager.my_toolqt.activemap = 1

                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.final_node.outputs[0]
                        )
                context.area.tag_redraw()

            elif event.type in {"TWO"} and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shiftn = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if self.ctrl:
                    self.ctrl = 0
                    if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 1:
                        bpy.context.window_manager.my_toolqt.matindex = 1
                        bpy.context.window_manager.my_toolqt.activemap = 1
                        bpy.context.window_manager.my_toolqt.activelayer = 1
                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0:

                        bpy.context.window_manager.my_toolqt.mask = 0
                        bpy.context.window_manager.my_toolqt.activemap = 2

                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.roughness_clamp.outputs[0]
                        )
                context.area.tag_redraw()

            elif event.type in {"THREE"} and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shiftn = 0
                self.shifts = 0
                self.shiftb = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if self.ctrl:
                    self.ctrl = 0
                    if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 2:
                        bpy.context.window_manager.my_toolqt.matindex = 2
                        bpy.context.window_manager.my_toolqt.activemap = 1
                        bpy.context.window_manager.my_toolqt.activelayer = 1
                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0:
                        bpy.context.window_manager.my_toolqt.mask = 0
                        bpy.context.window_manager.my_toolqt.activemap = 3

                        if self.bump_clamp:
                            self.node_tree.links.new(
                                self.out_node.inputs[0], self.bump_clamp.outputs[0]
                            )

                context.area.tag_redraw()

            elif event.type in {"FOUR"} and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.shiftn = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if self.ctrl:
                    self.ctrl = 0
                    if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 3:
                        bpy.context.window_manager.my_toolqt.matindex = 3
                        bpy.context.window_manager.my_toolqt.activemap = 1
                        bpy.context.window_manager.my_toolqt.activelayer = 1
                else:
                    if self.blend_noise:
                        bpy.context.window_manager.my_toolqt.mask = 1
                        bpy.context.window_manager.my_toolqt.activemap = 4
                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.mask_clamp.outputs[0]
                        )

                    if (
                        bpy.context.window_manager.my_toolqt.blend == 0
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):
                        if self.mask_clamp:
                            bpy.context.window_manager.my_toolqt.activemap = 4
                            self.node_tree.links.new(
                                self.out_node.inputs[0], self.mask_clamp.outputs[0]
                            )

                context.area.tag_redraw()

            elif event.type in {"FIVE"} and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.shiftn = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if self.ctrl:
                    self.ctrl = 0
                    if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 4:
                        bpy.context.window_manager.my_toolqt.matindex = 4
                        bpy.context.window_manager.my_toolqt.activemap = 1
                        bpy.context.window_manager.my_toolqt.activelayer = 1
                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0:

                        bpy.context.window_manager.my_toolqt.mask = 0
                        bpy.context.window_manager.my_toolqt.activemap = 5

                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.alpha_clamp.outputs[0]
                        )

                context.area.tag_redraw()

            elif event.type in {"SIX"} and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.shiftn = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if bpy.context.window_manager.my_toolqt.blend == 0:

                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.activemap = 7

                self.node_tree.links.new(
                    self.out_node.inputs[0], self.final_node.outputs[0]
                )

            elif event.type == "SEVEN":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.shiftn = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if bpy.context.window_manager.my_toolqt.blend == 0:

                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.activemap = 6

                self.node_tree.links.new(
                    self.out_node.inputs[0], self.final_node.outputs[0]
                )

            elif event.type == "EIGHT":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.shiftn = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if bpy.context.window_manager.my_toolqt.blend == 0:

                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.activemap = 8

                    # randomize color group
                    if not self.randcolor:
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
                            data_to.node_groups = [
                                name
                                for name in data_from.node_groups
                                if name.startswith("QT_RandColor")
                            ]
                        original_group = bpy.data.node_groups["QT_RandColor"]

                        randcolor = original_group.copy()
                        self.randcolor = self.nodes.new(type="ShaderNodeGroup")
                        self.randcolor.node_tree = bpy.data.node_groups[randcolor.name]
                        self.randcolor.name = "QT_RandColor_" + str(
                            bpy.context.window_manager.my_toolqt.activelayer
                        )

                        self.randcolor.location = self.diffuse_bright_contrast.location
                        self.randcolor.location.x += 200

                        self.node_tree.links.new(
                            self.diffuse_bright_contrast.outputs[0],
                            self.randcolor.inputs[0],
                        )
                        self.node_tree.links.new(
                            self.randcolor.outputs[0], self.core_shader.inputs[0]
                        )

                    # randomize roughness group
                    if not self.randval:
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
                            data_to.node_groups = [
                                name
                                for name in data_from.node_groups
                                if name.startswith("QT_RandVal")
                            ]
                        original_group = bpy.data.node_groups["QT_RandVal"]

                        randval = original_group.copy()
                        self.randval = self.nodes.new(type="ShaderNodeGroup")
                        self.randval.node_tree = bpy.data.node_groups[randval.name]
                        self.randval.name = "QT_RandVal_" + str(
                            bpy.context.window_manager.my_toolqt.activelayer
                        )

                        self.randval.location = self.roughness_clamp.location
                        self.randval.location.x += 200

                        self.node_tree.links.new(
                            self.roughness_clamp.outputs[0], self.randval.inputs[0]
                        )
                        self.node_tree.links.new(
                            self.randval.outputs[0], self.core_shader.inputs[9]
                        )

                self.node_tree.links.new(
                    self.out_node.inputs[0], self.final_node.outputs[0]
                )

            elif event.type == "NINE":
                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.shiftn = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if bpy.context.window_manager.my_toolqt.blend == 0:

                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.activemap = 9

                    if not self.variation:
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
                            data_to.node_groups = [
                                name
                                for name in data_from.node_groups
                                if name.startswith("QT_Variety")
                            ]
                        original_group = bpy.data.node_groups["QT_Variety"]

                        variation = original_group.copy()
                        self.variation = self.nodes.new(type="ShaderNodeGroup")
                        self.variation.node_tree = bpy.data.node_groups[variation.name]
                        self.variation.name = "QT_Variety_" + str(
                            bpy.context.window_manager.my_toolqt.activelayer
                        )

                        self.variation.location = self.diffuse_bright_contrast.location
                        self.variation.location.x += 200

                        self.node_tree.links.new(
                            self.diffuse_bright_contrast.outputs[0],
                            self.variation.inputs[0],
                        )
                        self.node_tree.links.new(
                            self.variation.outputs[0], self.core_shader.inputs[0]
                        )


            # ACTIVE LAYER
            elif event.type == "Q" and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shiftn = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if self.shift == 1 and self.ctrl == 1 and self.alt == 0:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {"PASS_THROUGH"}

                else:
                    if (
                        bpy.context.window_manager.my_toolqt.blend == 0
                        and bpy.context.window_manager.my_toolqt.mask == 0
                    ):

                        bpy.context.window_manager.my_toolqt.activemap = 1

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            bpy.context.window_manager.my_toolqt.activelayer -= 1

                            if bpy.context.window_manager.my_toolqt.activelayer == 1:
                                for n in self.nodes:
                                    if n.name.startswith("QT_Shader_1"):
                                        self.core_shader = n
                                        self.final_node = self.core_shader

                            if bpy.context.window_manager.my_toolqt.activelayer == 2:
                                for n in self.nodes:
                                    if n.name.startswith("QT_Shader_2"):
                                        self.core_shader = n
                                    if n.name.startswith("QT_Layer_2"):
                                        self.final_node = n

                            if bpy.context.window_manager.my_toolqt.activelayer == 3:
                                for n in self.nodes:
                                    if n.name.startswith("QT_Shader_3"):
                                        self.core_shader = n
                                    if n.name.startswith("QT_Layer_3"):
                                        self.final_node = n

                            if bpy.context.window_manager.my_toolqt.activelayer == 4:
                                for n in self.nodes:
                                    if n.name.startswith("QT_Shader_4"):
                                        self.core_shader = n
                                    if n.name.startswith("QT_Layer_4"):
                                        self.final_node = n

                            if bpy.context.window_manager.my_toolqt.activelayer == 5:
                                for n in self.nodes:
                                    if n.name.startswith("QT_Shader_5"):
                                        self.core_shader = n
                                    if n.name.startswith("QT_Layer_5"):
                                        self.final_node = n

                            self.node_tree.links.new(
                                self.out_node.inputs[0], self.final_node.outputs[0]
                            )
                            self.out_node.location.y = self.final_node.location.y
                            self.out_node.location.x = self.final_node.location.x + 300

                            for n in self.nodes:
                                n.select = False
                                if n.name.endswith(
                                    str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    n.select = True

                            bpy.context.window_manager.my_toolqt.proc_uv = 0

                            for n in self.nodes:
                                if n.select:
                                    if n.name.startswith(
                                        "QT_UV_Layer_"
                                        + (
                                            str(
                                                bpy.context.window_manager.my_toolqt.activelayer
                                            )
                                        )
                                    ):

                                        if n.label == "Decal" or n.label == "View":
                                            bpy.context.window_manager.my_toolqt.proc_uv = (
                                                1
                                            )

                                        if n.label == "Box":
                                            bpy.context.window_manager.my_toolqt.proc_uv = (
                                                1
                                            )

                            # set parameters
                            bpy.context.window_manager.my_toolqt.emit = (
                                self.core_shader.inputs[20].default_value
                            )
                            bpy.context.window_manager.my_toolqt.metal = int(
                                self.core_shader.inputs[6].default_value
                            )
                            bpy.context.window_manager.my_toolqt.bump = (
                                self.bump_bump.inputs[0].default_value
                            )
                            bpy.context.window_manager.my_toolqt.bump_strength = (
                                self.bump_strength.inputs[0].default_value
                            )
                            if self.bump_layer:
                                bpy.context.window_manager.my_toolqt.bump_layer = (
                                    self.bump_layer.inputs[0].default_value
                                )
                            bpy.context.window_manager.my_toolqt.spec = (
                                self.core_shader.inputs[7].default_value
                            )
                            bpy.context.window_manager.my_toolqt.sss = (
                                self.core_shader.inputs[1].default_value
                            )

                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                bpy.context.window_manager.my_toolqt.opacity = (
                                    self.final_node.inputs[0].default_value
                                )

                            if self.normal_tex:
                                if self.normal_tex.name == "QT_Normal_Tex_" + str(
                                    bpy.context.window_manager.my_toolqt.activelayer
                                ):
                                    bpy.context.window_manager.my_toolqt.normal = (
                                        self.normal_strength.inputs[0].default_value
                                    )
                                else:
                                    self.normal_tex = None

                            if self.ao_tex:
                                if self.ao_tex.name == "QT_AO_Tex_" + str(
                                    bpy.context.window_manager.my_toolqt.activelayer
                                ):
                                    bpy.context.window_manager.my_toolqt.ao = (
                                        self.ao_multiply.inputs[0].default_value
                                    )
                                else:
                                    self.ao_tex = None

            elif event.type == "W" and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.shiftn = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if (
                    bpy.context.window_manager.my_toolqt.blend == 0
                    and bpy.context.window_manager.my_toolqt.mask == 0
                ):

                    bpy.context.window_manager.my_toolqt.activemap = 1

                    passgo = 0

                    if bpy.context.window_manager.my_toolqt.activelayer == 1:
                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_2"):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 2:
                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_3"):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 3:
                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_4"):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 4:
                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_5"):
                                passgo = 1

                    if passgo:
                        if bpy.context.window_manager.my_toolqt.activelayer < 5:
                            bpy.context.window_manager.my_toolqt.activelayer += 1

                        if bpy.context.window_manager.my_toolqt.activelayer == 2:
                            for n in self.nodes:
                                if n.name.startswith("QT_Shader_2"):
                                    self.core_shader = n
                                if n.name.startswith("QT_Layer_2"):
                                    self.final_node = n

                        if bpy.context.window_manager.my_toolqt.activelayer == 3:
                            for n in self.nodes:
                                if n.name.startswith("QT_Shader_3"):
                                    self.core_shader = n
                                if n.name.startswith("QT_Layer_3"):
                                    self.final_node = n

                        if bpy.context.window_manager.my_toolqt.activelayer == 4:
                            for n in self.nodes:
                                if n.name.startswith("QT_Shader_4"):
                                    self.core_shader = n
                                if n.name.startswith("QT_Layer_4"):
                                    self.final_node = n

                        if bpy.context.window_manager.my_toolqt.activelayer == 5:
                            for n in self.nodes:
                                if n.name.startswith("QT_Shader_5"):
                                    self.core_shader = n
                                if n.name.startswith("QT_Layer_5"):
                                    self.final_node = n

                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.final_node.outputs[0]
                        )
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(
                                str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                n.select = True

                        bpy.context.window_manager.my_toolqt.proc_uv = 0

                        for n in self.nodes:
                            if n.select:
                                if n.name.startswith(
                                    "QT_UV_Layer_"
                                    + (
                                        str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    )
                                ):

                                    if n.label == "Decal" or n.label == "View":
                                        bpy.context.window_manager.my_toolqt.proc_uv = 1

                                    if n.label == "Box":
                                        bpy.context.window_manager.my_toolqt.proc_uv = 1

                        # set parameters
                        bpy.context.window_manager.my_toolqt.emit = (
                            self.core_shader.inputs[20].default_value
                        )
                        bpy.context.window_manager.my_toolqt.metal = int(
                            self.core_shader.inputs[6].default_value
                        )
                        bpy.context.window_manager.my_toolqt.bump = (
                            self.bump_bump.inputs[0].default_value
                        )
                        bpy.context.window_manager.my_toolqt.bump_strength = (
                            self.bump_strength.inputs[0].default_value
                        )
                        if self.bump_layer:
                            bpy.context.window_manager.my_toolqt.bump_layer = (
                                self.bump_layer.inputs[0].default_value
                            )
                        bpy.context.window_manager.my_toolqt.spec = (
                            self.core_shader.inputs[7].default_value
                        )
                        bpy.context.window_manager.my_toolqt.sss = (
                            self.core_shader.inputs[1].default_value
                        )

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            bpy.context.window_manager.my_toolqt.opacity = (
                                self.final_node.inputs[0].default_value
                            )

                        if self.normal_tex:
                            if self.normal_tex.name == "QT_Normal_Tex_" + str(
                                bpy.context.window_manager.my_toolqt.activelayer
                            ):
                                bpy.context.window_manager.my_toolqt.normal = (
                                    self.normal_strength.inputs[0].default_value
                                )
                            else:
                                self.normal_tex = None

                        if self.ao_tex:
                            if self.ao_tex.name == "QT_AO_Tex_" + str(
                                bpy.context.window_manager.my_toolqt.activelayer
                            ):
                                bpy.context.window_manager.my_toolqt.ao = (
                                    self.ao_multiply.inputs[0].default_value
                                )
                            else:
                                self.ao_tex = None

            # PREVIEW ALL LAYERS
            elif event.type == "TAB" and event.value == "RELEASE":

                if bpy.context.window_manager.my_toolqt.blend == 0:
                    self.node_tree.links.new(
                        self.out_node.inputs[0], self.final_node.outputs[0]
                    )

            elif event.type == "U":

                if bpy.context.window_manager.my_toolqt.blend == 0:

                    bpy.context.window_manager.my_toolqt.mask = 0

                    # add seamless node to ALL layers
                    if not self.diffuse_seamless:
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
                            data_to.node_groups = [
                                name
                                for name in data_from.node_groups
                                if name.startswith("QT_Blend")
                            ]
                        original_group = bpy.data.node_groups["QT_Blend"]

                        # iterate over layers
                        for i in range(5):

                            layernum = i + 1

                            normal_tex = None
                            diffuse_mapping = None
                            rough_mapping = None
                            bump_mapping = None
                            diffuse_tex = None
                            rough_tex = None
                            bump_tex = None
                            ao_tex = None
                            diffuse_seamless = None

                            if self.nodes:
                                for n in self.nodes:

                                    # normal
                                    if n.name.startswith(
                                        "QT_Normal_Tex_" + str(layernum)
                                    ):
                                        normal_tex = n

                                    # mapping
                                    if n.name.startswith(
                                        "QT_Diffuse_Mapping_" + str(layernum)
                                    ):
                                        diffuse_mapping = n
                                    if n.name.startswith(
                                        "QT_Rough_Mapping_" + str(layernum)
                                    ):
                                        rough_mapping = n
                                    if n.name.startswith(
                                        "QT_Bump_Mapping_" + str(layernum)
                                    ):
                                        bump_mapping = n

                                    # textures
                                    if n.name.startswith(
                                        "QT_Diffuse_Tex_" + str(layernum)
                                    ):
                                        diffuse_tex = n
                                    if n.name.startswith(
                                        "QT_Rough_Tex_" + str(layernum)
                                    ):
                                        rough_tex = n
                                    if n.name.startswith(
                                        "QT_Bump_Tex_" + str(layernum)
                                    ):
                                        bump_tex = n

                                    # ao
                                    if n.name.startswith("QT_AO_Tex_" + str(layernum)):
                                        ao_tex = n

                                    if n.name.startswith(
                                        "QT_Diffuse_Seamless_" + str(layernum)
                                    ):
                                        diffuse_seamless = n

                            if not diffuse_seamless:
                                if diffuse_tex:
                                    seamless = original_group.copy()
                                    seamless_diffuse_node = self.nodes.new(
                                        type="ShaderNodeGroup"
                                    )
                                    seamless_diffuse_node.node_tree = (
                                        bpy.data.node_groups[seamless.name]
                                    )
                                    seamless_diffuse_node.name = (
                                        "QT_Diffuse_Seamless_" + str(layernum)
                                    )

                                    seamless_diffuse_node.location = (
                                        diffuse_mapping.location
                                    )

                                    self.node_tree.links.new(
                                        diffuse_mapping.outputs[0],
                                        seamless_diffuse_node.inputs[0],
                                    )
                                    self.node_tree.links.new(
                                        seamless_diffuse_node.outputs[0],
                                        diffuse_tex.inputs[0],
                                    )

                                    if normal_tex:
                                        self.node_tree.links.new(
                                            diffuse_mapping.outputs[0],
                                            seamless_diffuse_node.inputs[0],
                                        )
                                        self.node_tree.links.new(
                                            seamless_diffuse_node.outputs[0],
                                            normal_tex.inputs[0],
                                        )
                                    if ao_tex:
                                        self.node_tree.links.new(
                                            diffuse_mapping.outputs[0],
                                            seamless_diffuse_node.inputs[0],
                                        )
                                        self.node_tree.links.new(
                                            seamless_diffuse_node.outputs[0],
                                            ao_tex.inputs[0],
                                        )

                                    seamless_rough_node = self.nodes.new(
                                        type="ShaderNodeGroup"
                                    )
                                    seamless_rough_node.node_tree = (
                                        bpy.data.node_groups[seamless.name]
                                    )
                                    seamless_rough_node.name = (
                                        "QT_Rough_Seamless_" + str(layernum)
                                    )

                                    seamless_rough_node.location = (
                                        rough_mapping.location
                                    )

                                    self.node_tree.links.new(
                                        rough_mapping.outputs[0],
                                        seamless_rough_node.inputs[0],
                                    )
                                    self.node_tree.links.new(
                                        seamless_rough_node.outputs[0],
                                        rough_tex.inputs[0],
                                    )

                                    seamless_bump_node = self.nodes.new(
                                        type="ShaderNodeGroup"
                                    )
                                    seamless_bump_node.node_tree = bpy.data.node_groups[
                                        seamless.name
                                    ]
                                    seamless_bump_node.name = "QT_Bump_Seamless_" + str(
                                        layernum
                                    )

                                    seamless_bump_node.location = bump_mapping.location

                                    self.node_tree.links.new(
                                        bump_mapping.outputs[0],
                                        seamless_bump_node.inputs[0],
                                    )
                                    self.node_tree.links.new(
                                        seamless_bump_node.outputs[0],
                                        bump_tex.inputs[0],
                                    )

                    self.node_tree.links.new(
                        self.out_node.inputs[0], self.final_node.outputs[0]
                    )

            elif event.type == "UP_ARROW" and event.value == "RELEASE":
                return {"PASS_THROUGH"}

            elif event.type == "DOWN_ARROW" and event.value == "RELEASE":
                return {"PASS_THROUGH"}

            elif event.type == "BACK_SPACE" and event.value == "RELEASE":

                if self.ctrl:
                    if bpy.context.window_manager.my_toolqt.blend == 0:

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:

                            layer1 = None
                            layer2 = None
                            layer3 = None
                            layer4 = None
                            layer5 = None

                            for n in self.nodes:
                                if n.name.endswith(
                                    str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.nodes.remove(n)

                            bpy.context.window_manager.my_toolqt.activelayer -= 1

                            for n in self.nodes:
                                if n.name.startswith("QT_Shader_1"):
                                    self.final_node = n

                            for n in self.nodes:
                                if n.name.startswith(
                                    "QT_Layer_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.final_node = n

                            self.node_tree.links.new(
                                self.out_node.inputs[0], self.final_node.outputs[0]
                            )
                            self.out_node.location.y = self.final_node.location.y
                            self.out_node.location.x = self.final_node.location.x + 300

                            for n in self.nodes:
                                if n.name.startswith("QT_Shader_1"):
                                    layer1 = n

                                if n.name.startswith("QT_Layer_2"):
                                    layer2 = n

                                if n.name.startswith("QT_Layer_3"):
                                    layer3 = n

                                if n.name.startswith("QT_Layer_4"):
                                    layer4 = n

                                if n.name.startswith("QT_Layer_5"):
                                    layer5 = n

                            if bpy.context.window_manager.my_toolqt.activelayer == 1:
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith("_5"):
                                            n.name = n.name.replace("_5", "_4")
                                            n.label = n.label.replace("_5", "_4")
                                            n.location.y += 2000
                                if layer4:
                                    for n in self.nodes:
                                        if n.name.endswith("_4"):
                                            n.name = n.name.replace("_4", "_3")
                                            n.label = n.label.replace("_4", "_3")
                                            n.location.y += 2000
                                if layer3:
                                    for n in self.nodes:
                                        if n.name.endswith("_3"):
                                            n.name = n.name.replace("_3", "_2")
                                            n.label = n.label.replace("_3", "_2")
                                            n.location.y += 2000

                                    self.node_tree.links.new(
                                        layer1.outputs[0], layer3.inputs[1]
                                    )

                            if bpy.context.window_manager.my_toolqt.activelayer == 2:
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith("_5"):
                                            n.name = n.name.replace("_5", "_4")
                                            n.label = n.label.replace("_5", "_4")
                                            n.location.y += 2000
                                if layer4:
                                    for n in self.nodes:
                                        if n.name.endswith("_4"):
                                            n.name = n.name.replace("_4", "_3")
                                            n.label = n.label.replace("_4", "_3")
                                            n.location.y += 2000

                                    self.node_tree.links.new(
                                        layer2.outputs[0], layer4.inputs[1]
                                    )

                            if bpy.context.window_manager.my_toolqt.activelayer == 3:
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith("_5"):
                                            n.name = n.name.replace("_5", "_4")
                                            n.label = n.label.replace("_5", "_4")
                                            n.location.y += 2000

                                    self.node_tree.links.new(
                                        layer3.outputs[0], layer5.inputs[1]
                                    )

                            for n in self.nodes:
                                n.select = False

                            for n in self.nodes:
                                if n.name.endswith(
                                    str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    n.select = True

                            for n in self.nodes:
                                # ACTIVE LAYER
                                if n.name.startswith(
                                    "QT_Shader_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.core_shader = n
                                    self.final_node = n

                                if n.name.startswith(
                                    "QT_Layer_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.final_node = n

                                if n.name == "Group Output":
                                    self.out_node = n

                                # coord
                                if n.name.startswith(
                                    "QT_UV_Layer_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.tex_coord = n

                                # normal
                                if n.name.startswith(
                                    "QT_Normal_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.normal_tex = n
                                if n.name.startswith(
                                    "QT_Normal_Strength_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.normal_strength = n
                                    bpy.context.window_manager.my_toolqt.normal = (
                                        self.normal_strength.inputs[0].default_value
                                    )

                                # mapping
                                if n.name.startswith(
                                    "QT_Diffuse_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_mapping = n
                                if n.name.startswith(
                                    "QT_Rough_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_mapping = n
                                if n.name.startswith(
                                    "QT_Bump_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_mapping = n

                                # clamps
                                if n.name.startswith(
                                    "QT_Clamp_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_clamp = n
                                if n.name.startswith(
                                    "QT_Roughness_Clamp_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.roughness_clamp = n
                                if n.name.startswith(
                                    "QT_Bump_Clamp_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_clamp = n

                                # textures
                                if n.name.startswith(
                                    "QT_Diffuse_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_tex = n
                                if n.name.startswith(
                                    "QT_Diffuse_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.diffuse_hue = (
                                        self.diffuse_hue_sat.inputs[0].default_value
                                    )
                                    bpy.context.window_manager.my_toolqt.diffuse_sat = (
                                        self.diffuse_hue_sat.inputs[1].default_value
                                    )
                                    bpy.context.window_manager.my_toolqt.diffuse_val = (
                                        self.diffuse_hue_sat.inputs[2].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Diffuse_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.diffuse_bright_contrast = n

                                if n.name.startswith(
                                    "QT_Rough_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_tex = n
                                if n.name.startswith(
                                    "QT_Rough_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Rough_Invert_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_invert = n
                                if n.name.startswith(
                                    "QT_Rough_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.rough_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[
                                        2
                                    ].default_value

                                if n.name.startswith(
                                    "QT_Bump_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_tex = n
                                if n.name.startswith(
                                    "QT_Bump_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Bump_Bump_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_bump = n
                                    bpy.context.window_manager.my_toolqt.bump = (
                                        self.bump_bump.inputs[0].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Bump_Layer_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_layer = n
                                    bpy.context.window_manager.my_toolqt.bump = (
                                        self.bump_layer.inputs[3].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Bump_Strength_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_strength = n
                                    bpy.context.window_manager.my_toolqt.bump = (
                                        self.bump_strength.inputs[1].default_value
                                    )
                                if n.name.startswith(
                                    "QT_Bump_Invert_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_invert = n
                                if n.name.startswith(
                                    "QT_Bump_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.bump_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[
                                        2
                                    ].default_value

                                # masks
                                if n.name.startswith(
                                    "QT_Tex_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_tex = n
                                if n.name.startswith(
                                    "QT_Bright_Contrast_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Invert_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_invert = n
                                if n.name.startswith(
                                    "QT_Hue_Sat_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Mapping_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.mask_mapping = n

                                # alpha
                                if n.name.startswith(
                                    "QT_Alpha_Mapping_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_mapping = n
                                if n.name.startswith(
                                    "QT_Alpha_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_tex = n
                                if n.name.startswith(
                                    "QT_Alpha_Bright_Contrast_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Alpha_Invert_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_invert = n
                                if n.name.startswith(
                                    "QT_Alpha_Hue_Sat_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[
                                        2
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Alpha_Clamp_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.alpha_clamp = n

                                # ao
                                if n.name.startswith(
                                    "QT_AO_Tex_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.ao_tex = n
                                if n.name.startswith(
                                    "QT_AO_Multiply_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.ao_multiply = n
                                    bpy.context.window_manager.my_toolqt.ao = (
                                        self.ao_multiply.inputs[0].default_value
                                    )

                                # height
                                if n.name.startswith(
                                    "QT_Power_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.blend_power = n
                                    bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[
                                        1
                                    ].default_value
                                if n.name.startswith(
                                    "QT_Noise_Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[
                                        5
                                    ].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[
                                        4
                                    ].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = (
                                        self.blend_noise.inputs[2].default_value
                                    )
                                    bpy.context.window_manager.my_toolqt.noisedetail = (
                                        self.blend_noise.inputs[3].default_value
                                    )

                                # blend
                                if bpy.context.window_manager.my_toolqt.blend:
                                    if n.name == ("QT_Blend_Add"):
                                        self.blend_add = n
                                    if n.name == ("QT_Blend_XYZ"):
                                        self.blend_xyz = n
                                    if n.name == ("QT_Blend_Math"):
                                        self.blend_math = n
                                    if n.name == ("QT_Blend_Power"):
                                        self.blend_power = n
                                    if n.name == ("QT_Blend_Clamp"):
                                        self.blend_clamp = n
                                    if n.name == ("QT_Blend_Mix"):
                                        self.blend_mix = n
                                    if n.name == ("QT_Blend_Noise"):
                                        self.blend_noise = n
                                        bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[
                                            5
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[
                                            4
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[
                                            2
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[
                                            3
                                        ].default_value
                                    if n.name == ("QT_Blend_Bright_Contrast"):
                                        self.blend_bright_contrast = n
                                        bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[
                                            2
                                        ].default_value
                                        bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[
                                            1
                                        ].default_value
                                    if n.name == "QT_Blend_Mix":
                                        self.final_node = n
                                        self.core_shader = n

                # DELETE MAP ONLY
                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0:

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            backspace = 0
                            for n in self.nodes:
                                if n.name.endswith(
                                    "Mask_"
                                    + str(
                                        bpy.context.window_manager.my_toolqt.activelayer
                                    )
                                ):
                                    self.nodes.remove(n)
                                    backspace = 1

                                for n in self.nodes:
                                    if n.name.startswith("QT_Shader_1"):
                                        self.final_node = n
                                    if n.name.startswith("QT_Layer_2"):
                                        self.final_node = n
                                    if n.name.startswith("QT_Layer_3"):
                                        self.final_node = n
                                    if n.name.startswith("QT_Layer_4"):
                                        self.final_node = n
                                    if n.name.startswith("QT_Layer_5"):
                                        self.final_node = n

                                self.node_tree.links.new(
                                    self.out_node.inputs[0], self.final_node.outputs[0]
                                )
                                self.out_node.location.y = self.final_node.location.y
                                self.out_node.location.x = (
                                    self.final_node.location.x + 300
                                )

                                bpy.context.window_manager.my_toolqt.activemap = 1

                                for n in self.nodes:
                                    n.select = False
                                    if n.name.endswith(
                                        str(
                                            bpy.context.window_manager.my_toolqt.activelayer
                                        )
                                    ):
                                        n.select = True

                    else:
                        backspace = 0
                        for n in self.mat.node_tree.nodes:
                            if n.name.startswith("QT_Blend"):
                                self.mat.node_tree.nodes.remove(n)
                                backspace = 1

                        if backspace:
                            bpy.context.window_manager.my_toolqt.blend = 0

                            for n in self.mat.node_tree.nodes:
                                if n.name == "QT_Output":
                                    self.out_material = n

                                if n.name.startswith("QT_Shader"):
                                    qtshader = n
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                            self.mat.node_tree.links.new(
                                self.out_material.inputs[0], qtshader.outputs[0]
                            )

            elif event.type == "DEL" and event.value == "RELEASE":

                if bpy.context.window_manager.my_toolqt.blend == 0:
                    if bpy.context.window_manager.my_toolqt.activelayer > 1:

                        layer1 = None
                        layer2 = None
                        layer3 = None
                        layer4 = None
                        layer5 = None

                        for n in self.nodes:
                            if n.name.endswith(
                                str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.nodes.remove(n)

                        bpy.context.window_manager.my_toolqt.activelayer -= 1

                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_1"):
                                self.final_node = n

                        for n in self.nodes:
                            if n.name.startswith(
                                "QT_Layer_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.final_node = n

                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.final_node.outputs[0]
                        )
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_1"):
                                layer1 = n

                            if n.name.startswith("QT_Layer_2"):
                                layer2 = n

                            if n.name.startswith("QT_Layer_3"):
                                layer3 = n

                            if n.name.startswith("QT_Layer_4"):
                                layer4 = n

                            if n.name.startswith("QT_Layer_5"):
                                layer5 = n

                        if bpy.context.window_manager.my_toolqt.activelayer == 1:
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith("_5"):
                                        n.name = n.name.replace("_5", "_4")
                                        n.label = n.label.replace("_5", "_4")
                                        n.location.y += 2000
                            if layer4:
                                for n in self.nodes:
                                    if n.name.endswith("_4"):
                                        n.name = n.name.replace("_4", "_3")
                                        n.label = n.label.replace("_4", "_3")
                                        n.location.y += 2000
                            if layer3:
                                for n in self.nodes:
                                    if n.name.endswith("_3"):
                                        n.name = n.name.replace("_3", "_2")
                                        n.label = n.label.replace("_3", "_2")
                                        n.location.y += 2000

                                self.node_tree.links.new(
                                    layer1.outputs[0], layer3.inputs[1]
                                )

                        if bpy.context.window_manager.my_toolqt.activelayer == 2:
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith("_5"):
                                        n.name = n.name.replace("_5", "_4")
                                        n.label = n.label.replace("_5", "_4")
                                        n.location.y += 2000
                            if layer4:
                                for n in self.nodes:
                                    if n.name.endswith("_4"):
                                        n.name = n.name.replace("_4", "_3")
                                        n.label = n.label.replace("_4", "_3")
                                        n.location.y += 2000

                                self.node_tree.links.new(
                                    layer2.outputs[0], layer4.inputs[1]
                                )

                        if bpy.context.window_manager.my_toolqt.activelayer == 3:
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith("_5"):
                                        n.name = n.name.replace("_5", "_4")
                                        n.label = n.label.replace("_5", "_4")
                                        n.location.y += 2000

                                self.node_tree.links.new(
                                    layer3.outputs[0], layer5.inputs[1]
                                )

                        for n in self.nodes:
                            n.select = False

                        for n in self.nodes:
                            if n.name.endswith(
                                str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                n.select = True

                        for n in self.mat.node_tree.nodes:
                            if n.name == "QT_Output":
                                self.out_material = n

                            if n.name.startswith("QT_Shader"):
                                self.nodes = n.node_tree.nodes
                                self.node_tree = n.node_tree

                            # blend only
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name.startswith("QT_Blend"):
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                        for n in self.nodes:
                            # ACTIVE LAYER
                            if n.name.startswith(
                                "QT_Shader_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.core_shader = n
                                self.final_node = n

                            if n.name.startswith(
                                "QT_Layer_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.final_node = n

                            if n.name == "Group Output":
                                self.out_node = n

                            # coord
                            if n.name.startswith(
                                "QT_UV_Layer_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.tex_coord = n

                            # normal
                            if n.name.startswith(
                                "QT_Normal_Tex_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.normal_tex = n
                            if n.name.startswith(
                                "QT_Normal_Strength_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.normal_strength = n
                                bpy.context.window_manager.my_toolqt.normal = (
                                    self.normal_strength.inputs[0].default_value
                                )

                            # mapping
                            if n.name.startswith(
                                "QT_Diffuse_Mapping_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.diffuse_mapping = n
                            if n.name.startswith(
                                "QT_Rough_Mapping_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.rough_mapping = n
                            if n.name.startswith(
                                "QT_Bump_Mapping_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_mapping = n

                            # clamps
                            if n.name.startswith(
                                "QT_Clamp_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.mask_clamp = n
                            if n.name.startswith(
                                "QT_Roughness_Clamp_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.roughness_clamp = n
                            if n.name.startswith(
                                "QT_Bump_Clamp_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_clamp = n

                            # textures
                            if n.name.startswith(
                                "QT_Diffuse_Tex_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.diffuse_tex = n
                            if n.name.startswith(
                                "QT_Diffuse_Hue_Sat_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.diffuse_hue_sat = n
                                bpy.context.window_manager.my_toolqt.diffuse_hue = (
                                    self.diffuse_hue_sat.inputs[0].default_value
                                )
                                bpy.context.window_manager.my_toolqt.diffuse_sat = (
                                    self.diffuse_hue_sat.inputs[1].default_value
                                )
                                bpy.context.window_manager.my_toolqt.diffuse_val = (
                                    self.diffuse_hue_sat.inputs[2].default_value
                                )
                            if n.name.startswith(
                                "QT_Diffuse_Bright_Contrast_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.diffuse_bright_contrast = n

                            if n.name.startswith(
                                "QT_Rough_Tex_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.rough_tex = n
                            if n.name.startswith(
                                "QT_Rough_Bright_Contrast_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.rough_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.rough_contrast = (
                                    self.rough_bright_contrast.inputs[2].default_value
                                )
                            if n.name.startswith(
                                "QT_Rough_Invert_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.rough_invert = n
                            if n.name.startswith(
                                "QT_Rough_Hue_Sat_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.rough_hue_sat = n
                                bpy.context.window_manager.my_toolqt.rough_hue_sat = (
                                    self.rough_hue_sat.inputs[2].default_value
                                )

                            if n.name.startswith(
                                "QT_Bump_Tex_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_tex = n
                            if n.name.startswith(
                                "QT_Bump_Bright_Contrast_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.bump_contrast = (
                                    self.bump_bright_contrast.inputs[2].default_value
                                )
                            if n.name.startswith(
                                "QT_Bump_Bump_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_bump = n
                                bpy.context.window_manager.my_toolqt.bump = (
                                    self.bump_bump.inputs[0].default_value
                                )
                            if n.name.startswith(
                                "QT_Bump_Strength_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_strength = n
                                bpy.context.window_manager.my_toolqt.bump_strength = (
                                    self.bump_strength.inputs[1].default_value
                                )
                            if n.name.startswith(
                                "QT_Bump_Invert_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_invert = n
                            if n.name.startswith(
                                "QT_Bump_Hue_Sat_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.bump_hue_sat = n
                                bpy.context.window_manager.my_toolqt.bump_hue_sat = (
                                    self.bump_hue_sat.inputs[2].default_value
                                )

                            # masks
                            if n.name.startswith(
                                "QT_Tex_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.mask_tex = n
                            if n.name.startswith(
                                "QT_Bright_Contrast_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.mask_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.mask_contrast = (
                                    self.mask_bright_contrast.inputs[2].default_value
                                )
                            if n.name.startswith(
                                "QT_Invert_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.mask_invert = n
                            if n.name.startswith(
                                "QT_Hue_Sat_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.mask_hue_sat = n
                                bpy.context.window_manager.my_toolqt.mask_hue_sat = (
                                    self.mask_hue_sat.inputs[2].default_value
                                )
                            if n.name.startswith(
                                "QT_Mapping_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.mask_mapping = n

                            # alpha
                            if n.name.startswith(
                                "QT_Alpha_Mapping_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.alpha_mapping = n
                            if n.name.startswith(
                                "QT_Alpha_Tex_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.alpha_tex = n
                            if n.name.startswith(
                                "QT_Alpha_Bright_Contrast_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.alpha_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[
                                    2
                                ].default_value
                            if n.name.startswith(
                                "QT_Alpha_Invert_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.alpha_invert = n
                            if n.name.startswith(
                                "QT_Alpha_Hue_Sat_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.alpha_hue_sat = n
                                bpy.context.window_manager.my_toolqt.alpha_hue_sat = (
                                    self.alpha_hue_sat.inputs[2].default_value
                                )
                            if n.name.startswith(
                                "QT_Alpha_Clamp_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.alpha_clamp = n

                            # ao
                            if n.name.startswith(
                                "QT_AO_Tex_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.ao_tex = n
                            if n.name.startswith(
                                "QT_AO_Multiply_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.ao_multiply = n
                                bpy.context.window_manager.my_toolqt.ao = (
                                    self.ao_multiply.inputs[0].default_value
                                )

                            # height
                            if n.name.startswith(
                                "QT_Power_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.blend_power = n
                                bpy.context.window_manager.my_toolqt.blendsmoothing = (
                                    self.blend_power.inputs[1].default_value
                                )
                            if n.name.startswith(
                                "QT_Noise_Mask_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.blend_noise = n
                                bpy.context.window_manager.my_toolqt.noisedistortion = (
                                    self.blend_noise.inputs[5].default_value
                                )
                                bpy.context.window_manager.my_toolqt.noiseroughness = (
                                    self.blend_noise.inputs[4].default_value
                                )
                                bpy.context.window_manager.my_toolqt.noisescale = (
                                    self.blend_noise.inputs[2].default_value
                                )
                                bpy.context.window_manager.my_toolqt.noisedetail = (
                                    self.blend_noise.inputs[3].default_value
                                )

                            # blend
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name == ("QT_Blend_Add"):
                                    self.blend_add = n
                                if n.name == ("QT_Blend_XYZ"):
                                    self.blend_xyz = n
                                if n.name == ("QT_Blend_Math"):
                                    self.blend_math = n
                                if n.name == ("QT_Blend_Power"):
                                    self.blend_power = n
                                if n.name == ("QT_Blend_Clamp"):
                                    self.blend_clamp = n
                                if n.name == ("QT_Blend_Mix"):
                                    self.blend_mix = n
                                if n.name == ("QT_Blend_Noise"):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[
                                        5
                                    ].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[
                                        4
                                    ].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = (
                                        self.blend_noise.inputs[2].default_value
                                    )
                                    bpy.context.window_manager.my_toolqt.noisedetail = (
                                        self.blend_noise.inputs[3].default_value
                                    )
                                if n.name == ("QT_Blend_Bright_Contrast"):
                                    self.blend_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[
                                        2
                                    ].default_value
                                    bpy.context.window_manager.my_toolqt.blendvalue = (
                                        self.blend_bright_contrast.inputs[
                                            1
                                        ].default_value
                                    )
                                if n.name == "QT_Blend_Mix":
                                    self.final_node = n
                                    self.core_shader = n

            # ROTATE 90 DEGREES
            elif event.type == "LEFT_BRACKET" and event.value == "RELEASE":

                # if bpy.context.window_manager.my_toolqt.proc_uv:
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] -= pi / 2
                    self.rough_mapping.inputs[2].default_value[2] -= pi / 2
                    self.bump_mapping.inputs[2].default_value[2] -= pi / 2
                    self.alpha_mapping.inputs[2].default_value[2] -= pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] -= pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] -= pi / 2

                elif (
                    bpy.context.window_manager.my_toolqt.activemap == 4
                    and bpy.context.window_manager.my_toolqt.mask == 0
                ):
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] -= pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] -= pi / 2

                context.area.tag_redraw()

            elif event.type == "RIGHT_BRACKET" and event.value == "RELEASE":

                # if bpy.context.window_manager.my_toolqt.proc_uv:
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] += pi / 2
                    self.rough_mapping.inputs[2].default_value[2] += pi / 2
                    self.bump_mapping.inputs[2].default_value[2] += pi / 2
                    self.alpha_mapping.inputs[2].default_value[2] += pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] += pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] += pi / 2

                elif (
                    bpy.context.window_manager.my_toolqt.activemap == 4
                    and bpy.context.window_manager.my_toolqt.mask == 0
                ):
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] += pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] += pi / 2

                context.area.tag_redraw()

            # ROTATE 90 DEGREES
            elif event.type == "LEFT_ARROW" and event.value == "RELEASE":

                # if bpy.context.window_manager.my_toolqt.proc_uv:
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] -= pi / 2
                    self.rough_mapping.inputs[2].default_value[2] -= pi / 2
                    self.bump_mapping.inputs[2].default_value[2] -= pi / 2
                    self.alpha_mapping.inputs[2].default_value[2] -= pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] -= pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] -= pi / 2

                elif (
                    bpy.context.window_manager.my_toolqt.activemap == 4
                    and bpy.context.window_manager.my_toolqt.mask == 0
                ):
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] -= pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] -= pi / 2

                context.area.tag_redraw()

            elif event.type == "RIGHT_ARROW" and event.value == "RELEASE":

                # if bpy.context.window_manager.my_toolqt.proc_uv:
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] += pi / 2
                    self.rough_mapping.inputs[2].default_value[2] += pi / 2
                    self.bump_mapping.inputs[2].default_value[2] += pi / 2
                    self.alpha_mapping.inputs[2].default_value[2] += pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] += pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] += pi / 2

                elif (
                    bpy.context.window_manager.my_toolqt.activemap == 4
                    and bpy.context.window_manager.my_toolqt.mask == 0
                ):
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] += pi / 2

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] += pi / 2

                context.area.tag_redraw()

            # RESET SETTINGS
            elif event.type == "K" and event.value == "RELEASE":

                if self.tex_coord.label == "Decal":
                    width, height = self.diffuse_tex.image.size
                    size = width / height

                    if self.shift:
                        if self.diffuse_mapping:
                            self.diffuse_mapping.inputs[3].default_value[0] = 1
                            self.diffuse_mapping.inputs[3].default_value[1] = 1
                            self.diffuse_mapping.inputs[3].default_value[2] = 1

                        if self.rough_mapping:
                            self.rough_mapping.inputs[3].default_value[0] = 1
                            self.rough_mapping.inputs[3].default_value[1] = 1
                            self.rough_mapping.inputs[3].default_value[2] = 1

                        if self.bump_mapping:
                            self.bump_mapping.inputs[3].default_value[0] = 1
                            self.bump_mapping.inputs[3].default_value[1] = 1
                            self.bump_mapping.inputs[3].default_value[2] = 1

                    if self.ctrl:
                        if self.diffuse_mapping:
                            self.diffuse_mapping.inputs[1].default_value[0] = 0
                            self.diffuse_mapping.inputs[1].default_value[1] = 0
                            self.diffuse_mapping.inputs[1].default_value[2] = 0

                            self.diffuse_mapping.inputs[2].default_value[0] = 0
                            self.diffuse_mapping.inputs[2].default_value[1] = 0
                            self.diffuse_mapping.inputs[2].default_value[2] = 0

                        if self.rough_mapping:
                            self.rough_mapping.inputs[1].default_value[0] = 0
                            self.rough_mapping.inputs[1].default_value[1] = 0
                            self.rough_mapping.inputs[1].default_value[2] = 0

                            self.rough_mapping.inputs[2].default_value[0] = 0
                            self.rough_mapping.inputs[2].default_value[1] = 0
                            self.rough_mapping.inputs[2].default_value[2] = 0

                        if self.bump_mapping:
                            self.bump_mapping.inputs[1].default_value[0] = 0
                            self.bump_mapping.inputs[1].default_value[1] = 0
                            self.bump_mapping.inputs[1].default_value[2] = 0

                            self.bump_mapping.inputs[2].default_value[0] = 0
                            self.bump_mapping.inputs[2].default_value[1] = 0
                            self.bump_mapping.inputs[2].default_value[2] = 0

                        if self.alpha_mapping:
                            self.alpha_mapping.inputs[1].default_value[0] = 0
                            self.alpha_mapping.inputs[1].default_value[1] = 0
                            self.alpha_mapping.inputs[1].default_value[2] = 0

                            self.alpha_mapping.inputs[2].default_value[0] = 0
                            self.alpha_mapping.inputs[2].default_value[1] = 0
                            self.alpha_mapping.inputs[2].default_value[2] = 0

                        if self.mask_mapping:
                            self.mask_mapping.inputs[1].default_value[0] = 0
                            self.mask_mapping.inputs[2].default_value[1] = 0
                            self.mask_mapping.inputs[3].default_value[2] = 0

                    if self.alt:
                        if self.ao_multiply:
                            self.ao_multiply.inputs[0].default_value = 0

                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value = 0

                        if self.bump_bump:
                            self.bump_bump.inputs[0].default_value = 0
                            self.bump_strength.inputs[1].default_value = 0

                        if self.core_shader:
                            self.core_shader.inputs[1].default_value = 0
                            self.core_shader.inputs[5].default_value = 0
                            self.core_shader.inputs[18].default_value = 0

                        if self.blend_noise:
                            self.blend_noise.inputs[5].default_value = 0
                            self.blend_noise.inputs[4].default_value = 0
                            self.blend_noise.inputs[2].default_value = 0
                            self.blend_noise.inputs[3].default_value = 0

                        if self.blend_power:
                            self.blend_power.inputs[1].default_value = 0.001

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

                        if self.mask_hue_sat:
                            self.mask_hue_sat.inputs[0].default_value = 0.5
                            self.mask_hue_sat.inputs[1].default_value = 1
                            self.mask_hue_sat.inputs[2].default_value = 1

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

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[2].default_value = 0

                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[2].default_value = 0

                        if self.alpha_bright_contrast:
                            self.alpha_bright_contrast.inputs[2].default_value = 0

                    if self.shift == 0 and self.ctrl == 0 and self.alt == 0:
                        if self.diffuse_mapping:
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

                        if self.core_shader:
                            self.core_shader.inputs[1].default_value = 0
                            self.core_shader.inputs[18].default_value = 0
                            self.core_shader.inputs[5].default_value = 0
                            self.core_shader.inputs[4].default_value = 0

                        if self.blend_noise:
                            self.blend_noise.inputs[2].default_value = 0
                            self.blend_noise.inputs[5].default_value = 0
                            self.blend_noise.inputs[4].default_value = 0
                            self.blend_noise.inputs[3].default_value = 0

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

                        if self.mask_mapping:
                            self.mask_mapping.inputs[1].default_value[0] = 0
                            self.mask_mapping.inputs[2].default_value[1] = 0
                            self.mask_mapping.inputs[3].default_value[2] = 0

                        if self.ao_multiply:
                            self.ao_multiply.inputs[0].default_value = 0

                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value = 0

                        if self.bump_bump:
                            self.bump_bump.inputs[0].default_value = 0
                            self.bump_strength.inputs[1].default_value = 0

                        if self.core_shader:
                            self.core_shader.inputs[1].default_value = 0
                            self.core_shader.inputs[5].default_value = 0
                            self.core_shader.inputs[18].default_value = 0

                        if self.blend_noise:
                            self.blend_noise.inputs[5].default_value = 0
                            self.blend_noise.inputs[4].default_value = 0
                            self.blend_noise.inputs[2].default_value = 0
                            self.blend_noise.inputs[3].default_value = 0

                        if self.blend_power:
                            self.blend_power.inputs[1].default_value = 0.001

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

                        if self.mask_hue_sat:
                            self.mask_hue_sat.inputs[0].default_value = 0.5
                            self.mask_hue_sat.inputs[1].default_value = 1
                            self.mask_hue_sat.inputs[2].default_value = 1

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

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[2].default_value = 0

                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[2].default_value = 0

                        if self.alpha_bright_contrast:
                            self.alpha_bright_contrast.inputs[2].default_value = 0

                        if self.diffuse_seamless:
                            self.diffuse_seamless.inputs[1].default_value = 0
                            bpy.context.window_manager.my_toolqt.tiling_blend_amount = (
                                self.diffuse_seamless.inputs[1].default_value
                            )
                            self.rough_seamless.inputs[
                                1
                            ].default_value = (
                                bpy.context.window_manager.my_toolqt.tiling_blend_amount
                            )
                            self.bump_seamless.inputs[
                                1
                            ].default_value = (
                                bpy.context.window_manager.my_toolqt.tiling_blend_amount
                            )
                            if self.alpha_seamless:
                                self.alpha_seamless.inputs[
                                    1
                                ].default_value = (
                                    bpy.context.window_manager.my_toolqt.tiling_blend_amount
                                )

                            self.diffuse_seamless.inputs[2].default_value = 0
                            bpy.context.window_manager.my_toolqt.tiling_blend_noise = (
                                self.diffuse_seamless.inputs[2].default_value
                            )
                            self.rough_seamless.inputs[
                                2
                            ].default_value = (
                                bpy.context.window_manager.my_toolqt.tiling_blend_noise
                            )
                            self.bump_seamless.inputs[
                                2
                            ].default_value = (
                                bpy.context.window_manager.my_toolqt.tiling_blend_noise
                            )
                            if self.alpha_seamless:
                                self.alpha_seamless.inputs[
                                    2
                                ].default_value = (
                                    bpy.context.window_manager.my_toolqt.tiling_blend_noise
                                )

                        if self.core_shader:
                            bpy.context.window_manager.my_toolqt.emit = 0
                            self.core_shader.inputs[20].default_value = 0

                else:
                    if self.shift:
                        if self.diffuse_mapping:
                            self.diffuse_mapping.inputs[3].default_value[0] = 1
                            self.diffuse_mapping.inputs[3].default_value[1] = 1
                            self.diffuse_mapping.inputs[3].default_value[2] = 1

                        if self.rough_mapping:
                            self.rough_mapping.inputs[3].default_value[0] = 1
                            self.rough_mapping.inputs[3].default_value[1] = 1
                            self.rough_mapping.inputs[3].default_value[2] = 1

                        if self.bump_mapping:
                            self.bump_mapping.inputs[3].default_value[0] = 1
                            self.bump_mapping.inputs[3].default_value[1] = 1
                            self.bump_mapping.inputs[3].default_value[2] = 1

                    if self.ctrl:
                        if self.diffuse_mapping:
                            self.diffuse_mapping.inputs[1].default_value[0] = 0
                            self.diffuse_mapping.inputs[1].default_value[1] = 0
                            self.diffuse_mapping.inputs[1].default_value[2] = 0

                            self.diffuse_mapping.inputs[2].default_value[0] = 0
                            self.diffuse_mapping.inputs[2].default_value[1] = 0
                            self.diffuse_mapping.inputs[2].default_value[2] = 0

                        if self.rough_mapping:
                            self.rough_mapping.inputs[1].default_value[0] = 0
                            self.rough_mapping.inputs[1].default_value[1] = 0
                            self.rough_mapping.inputs[1].default_value[2] = 0

                            self.rough_mapping.inputs[2].default_value[0] = 0
                            self.rough_mapping.inputs[2].default_value[1] = 0
                            self.rough_mapping.inputs[2].default_value[2] = 0

                        if self.bump_mapping:
                            self.bump_mapping.inputs[1].default_value[0] = 0
                            self.bump_mapping.inputs[1].default_value[1] = 0
                            self.bump_mapping.inputs[1].default_value[2] = 0

                            self.bump_mapping.inputs[2].default_value[0] = 0
                            self.bump_mapping.inputs[2].default_value[1] = 0
                            self.bump_mapping.inputs[2].default_value[2] = 0

                        if self.alpha_mapping:
                            self.alpha_mapping.inputs[1].default_value[0] = 0
                            self.alpha_mapping.inputs[1].default_value[1] = 0
                            self.alpha_mapping.inputs[1].default_value[2] = 0

                            self.alpha_mapping.inputs[2].default_value[0] = 0
                            self.alpha_mapping.inputs[2].default_value[1] = 0
                            self.alpha_mapping.inputs[2].default_value[2] = 0

                        if self.mask_mapping:
                            self.mask_mapping.inputs[1].default_value[0] = 0
                            self.mask_mapping.inputs[1].default_value[1] = 0
                            self.mask_mapping.inputs[1].default_value[2] = 0

                    if self.alt:
                        if self.ao_multiply:
                            self.ao_multiply.inputs[0].default_value = 0

                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value = 0

                        if self.bump_bump:
                            self.bump_bump.inputs[0].default_value = 0
                            self.bump_strength.inputs[1].default_value = 0

                        if self.core_shader:
                            self.core_shader.inputs[1].default_value = 0
                            self.core_shader.inputs[5].default_value = 0
                            self.core_shader.inputs[18].default_value = 0

                        if self.blend_noise:
                            self.blend_noise.inputs[5].default_value = 0
                            self.blend_noise.inputs[4].default_value = 0
                            self.blend_noise.inputs[2].default_value = 0
                            self.blend_noise.inputs[3].default_value = 0

                        if self.blend_power:
                            self.blend_power.inputs[1].default_value = 0.001

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

                        if self.mask_hue_sat:
                            self.mask_hue_sat.inputs[0].default_value = 0.5
                            self.mask_hue_sat.inputs[1].default_value = 1
                            self.mask_hue_sat.inputs[2].default_value = 1

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

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[2].default_value = 0

                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[2].default_value = 0

                        if self.alpha_bright_contrast:
                            self.alpha_bright_contrast.inputs[2].default_value = 0

                        if self.core_shader:
                            bpy.context.window_manager.my_toolqt.emit = 0
                            self.core_shader.inputs[20].default_value = 0

                    if self.shift == 0 and self.ctrl == 0 and self.alt == 0:
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

                        if self.core_shader:
                            self.core_shader.inputs[1].default_value = 0
                            self.core_shader.inputs[18].default_value = 0
                            self.core_shader.inputs[5].default_value = 0
                            self.core_shader.inputs[4].default_value = 0

                        if self.blend_noise:
                            self.blend_noise.inputs[2].default_value = 0
                            self.blend_noise.inputs[5].default_value = 0
                            self.blend_noise.inputs[4].default_value = 0
                            self.blend_noise.inputs[3].default_value = 0

                        if self.alpha_mapping:
                            self.alpha_mapping.inputs[1].default_value[0] = 0
                            self.alpha_mapping.inputs[1].default_value[1] = 0
                            self.alpha_mapping.inputs[1].default_value[2] = 0

                            self.alpha_mapping.inputs[2].default_value[0] = 0
                            self.alpha_mapping.inputs[2].default_value[1] = 0
                            self.alpha_mapping.inputs[2].default_value[2] = 0

                        if self.mask_mapping:
                            self.mask_mapping.inputs[1].default_value[0] = 0
                            self.mask_mapping.inputs[1].default_value[1] = 0
                            self.mask_mapping.inputs[1].default_value[2] = 0

                        if self.ao_multiply:
                            self.ao_multiply.inputs[0].default_value = 0

                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value = 0

                        if self.bump_bump:
                            self.bump_bump.inputs[0].default_value = 0
                            self.bump_strength.inputs[1].default_value = 0

                        if self.core_shader:
                            self.core_shader.inputs[1].default_value = 0
                            self.core_shader.inputs[5].default_value = 0
                            self.core_shader.inputs[18].default_value = 0

                        if self.blend_noise:
                            self.blend_noise.inputs[5].default_value = 0
                            self.blend_noise.inputs[4].default_value = 0
                            self.blend_noise.inputs[2].default_value = 0
                            self.blend_noise.inputs[3].default_value = 0

                        if self.blend_power:
                            self.blend_power.inputs[1].default_value = 0.001

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

                        if self.mask_hue_sat:
                            self.mask_hue_sat.inputs[0].default_value = 0.5
                            self.mask_hue_sat.inputs[1].default_value = 1
                            self.mask_hue_sat.inputs[2].default_value = 1

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

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[2].default_value = 0

                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[2].default_value = 0

                        if self.alpha_bright_contrast:
                            self.alpha_bright_contrast.inputs[2].default_value = 0

                        if self.core_shader:
                            bpy.context.window_manager.my_toolqt.emit = 0
                            self.core_shader.inputs[20].default_value = 0

                self.alt = 0
                self.ctrl = 0
                self.shift = 0

                context.area.tag_redraw()

            elif event.type in {"MIDDLEMOUSE", "RET"}:
                return {"PASS_THROUGH"}

            elif event.type == "RIGHTMOUSE":
                return {"PASS_THROUGH"}

            elif event.type == "WHEELUPMOUSE":
                return {"PASS_THROUGH"}

            elif event.type == "WHEELDOWNMOUSE":
                return {"PASS_THROUGH"}

            elif event.type == "ZERO" and event.value == "PRESS":
                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shiftn = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftb = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.c = 0
                self.o = 0
                self.x = 0

                if bpy.context.window_manager.my_toolqt.blend == 0:
                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.activemap = 0
                context.area.tag_redraw()

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

            elif event.type == "QUOTE":
                return {"PASS_THROUGH"}

            elif event.type == "MINUS":
                return {"PASS_THROUGH"}

            elif event.type == "PLUS":
                return {"PASS_THROUGH"}

            elif event.type == "BACK_SLASH":
                return {"PASS_THROUGH"}

            elif event.type == "EQUAL":
                return {"PASS_THROUGH"}

            elif event.type == "NUMPAD_ASTERIX":
                return {"PASS_THROUGH"}

            elif event.type == "COMMA":
                return {"PASS_THROUGH"}

            elif event.type == "F3":
                return {"PASS_THROUGH"}

            elif event.type == "PAUSE":
                return {"PASS_THROUGH"}

            elif event.type == "INSERT":
                return {"PASS_THROUGH"}

            elif event.type == "HOME":
                return {"PASS_THROUGH"}

            elif event.type == "PAGE_UP":
                return {"PASS_THROUGH"}

            elif event.type == "PAGE_DOWN":
                return {"PASS_THROUGH"}

            elif event.type == "END":
                return {"PASS_THROUGH"}

            elif event.type == "F" and event.value == "PRESS":
                if event.ctrl or event.shift:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {"PASS_THROUGH"}

            elif event.type == "X" and event.value == "PRESS":

                self.a = 0
                self.g = 0
                self.s = 0
                self.r = 0
                self.l = 0
                self.e = 0
                self.shifth = 0
                self.alts = 0
                self.shifts = 0
                self.shiftn = 0
                self.shiftb = 0
                self.ctrli = 0
                self.h = 0
                self.v = 0
                self.o = 0

                if self.x:
                    self.x = 0
                else:
                    self.x = 1

                context.area.tag_redraw()

                if event.ctrl:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {"PASS_THROUGH"}

                if event.ctrl and event.shift:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {"PASS_THROUGH"}

            elif (
                event.ctrl
                and event.shift
                and event.type == "D"
                and event.value == "PRESS"
            ):
                self.shift = 0
                bpy.context.window_manager.my_toolqt.running_qt = 0
                bpy.context.window_manager.my_toolqt.decal = 1
                bpy.context.window_manager.my_toolqt.selected = 0
                bpy.context.window_manager.my_toolqt.blend = 0
                bpy.context.window_manager.my_toolqt.mask = 0
                bpy.context.window_manager.my_toolqt.ob = None
                if "QuickTexture" in bpy.data.collections:
                    bpy.data.collections["QuickTexture"].hide_viewport = True
                    bpy.data.collections["QuickTexture"].hide_render = True
                bpy.ops.object.quickdecal("INVOKE_DEFAULT")

            # UNDO - restore stuff that I don't want changed
            elif event.type == "Z" and event.value == "PRESS":
                return {"PASS_THROUGH"}

            if event.type == "ESC":
                return {"PASS_THROUGH"}

            if event.type == "ACCENT_GRAVE":
                return {"PASS_THROUGH"}

            # EXIT
            if event.type == "T" and event.value == "PRESS":

                if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                    return {"PASS_THROUGH"}

                elif event.ctrl == 0 and event.shift == 1 and event.alt == 0:
                    if (
                        self.tex_coord.label == "Box"
                        or self.tex_coord.label == "UV"
                    ):
                        if self.diffuse_tex:

                            if self.diffuse_tex.projection == "FLAT":

                                bpy.context.window_manager.my_toolqt.triplanar = (
                                    1
                                )

                                self.diffuse_tex.projection = "BOX"
                                self.diffuse_tex.projection_blend = 0.3
                                self.rough_tex.projection = "BOX"
                                self.rough_tex.projection_blend = 0.3

                                t_name = self.tex_coord.name
                                t_label = self.tex_coord.label
                                t_location = self.tex_coord.location
                                self.node_tree.nodes.remove(self.tex_coord)
                                self.tex_coord = self.node_tree.nodes.new(
                                    "ShaderNodeTexCoord"
                                )
                                self.tex_coord.name = t_name
                                self.tex_coord.label = t_label
                                self.tex_coord.location = t_location

                                self.node_tree.links.new(
                                    self.tex_coord.outputs[0],
                                    self.diffuse_mapping.inputs[0],
                                )
                                self.node_tree.links.new(
                                    self.tex_coord.outputs[0],
                                    self.rough_mapping.inputs[0],
                                )

                                if self.bump_tex:
                                    self.bump_tex.projection = "BOX"
                                    self.bump_tex.projection_blend = 0.3
                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[0],
                                        self.bump_mapping.inputs[0],
                                    )
                                if self.normal_tex:
                                    self.normal_tex.projection = "BOX"
                                    self.normal_tex.projection_blend = 0.3

                                if self.ao_tex:
                                    self.ao_tex.projection = "BOX"
                                    self.ao_tex.projection_blend = 0.3

                                if self.alpha_tex:
                                    self.alpha_tex.projection = "BOX"
                                    self.alpha_tex.projection_blend = 0.3
                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[0],
                                        self.alpha_mapping.inputs[0],
                                    )
                                if self.disp_tex:
                                    self.disp_tex.projection = "BOX"
                                    self.disp_tex.projection_blend = 0.3

                                if self.mask_tex:
                                    self.mask_tex.projection = "BOX"
                                    self.mask_tex.projection_blend = 0.3
                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[0],
                                        self.mask_mapping.inputs[0],
                                    )

                            else:

                                bpy.context.window_manager.my_toolqt.triplanar = (
                                    0
                                )

                                self.diffuse_tex.projection = "FLAT"
                                self.rough_tex.projection = "FLAT"

                                if self.tex_coord.label == "UV":

                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[2],
                                        self.diffuse_mapping.inputs[0],
                                    )
                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[2],
                                        self.rough_mapping.inputs[0],
                                    )

                                    if self.bump_tex:
                                        self.bump_tex.projection = "FLAT"
                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[2],
                                            self.bump_mapping.inputs[0],
                                        )
                                    if self.normal_tex:
                                        self.normal_tex.projection = "FLAT"
                                    if self.ao_tex:
                                        self.ao_tex.projection = "FLAT"
                                    if self.alpha_tex:
                                        self.alpha_tex.projection = "FLAT"
                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[2],
                                            self.alpha_mapping.inputs[0],
                                        )
                                    if self.disp_tex:
                                        self.disp_tex.projection = "FLAT"
                                    if self.mask_tex:
                                        self.mask_tex.projection = "FLAT"
                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[2],
                                            self.mask_mapping.inputs[0],
                                        )

                                else:
                                    t_name = self.tex_coord.name
                                    t_label = self.tex_coord.label
                                    t_location = self.tex_coord.location
                                    self.node_tree.nodes.remove(self.tex_coord)
                                    self.tex_coord = self.node_tree.nodes.new(
                                        "ShaderNodeUVMap"
                                    )
                                    self.tex_coord.name = t_name
                                    self.tex_coord.label = t_label
                                    self.tex_coord.location = t_location
                                    self.tex_coord.uv_map = "QT_UV_Box_Layer_1"

                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[0],
                                        self.diffuse_mapping.inputs[0],
                                    )
                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[0],
                                        self.rough_mapping.inputs[0],
                                    )

                                    if self.bump_tex:
                                        self.bump_tex.projection = "FLAT"
                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[0],
                                            self.bump_mapping.inputs[0],
                                        )
                                    if self.normal_tex:
                                        self.normal_tex.projection = "FLAT"
                                    if self.ao_tex:
                                        self.ao_tex.projection = "FLAT"
                                    if self.alpha_tex:
                                        self.alpha_tex.projection = "FLAT"
                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[0],
                                            self.alpha_mapping.inputs[0],
                                        )
                                    if self.disp_tex:
                                        self.disp_tex.projection = "FLAT"
                                    if self.mask_tex:
                                        self.mask_tex.projection = "FLAT"
                                        self.node_tree.links.new(
                                            self.tex_coord.outputs[0],
                                            self.mask_mapping.inputs[0],
                                        )

                            # mapping scale reset

                            self.diffuse_mapping.inputs[3].default_value[0] = 1
                            self.diffuse_mapping.inputs[3].default_value[1] = 1
                            self.diffuse_mapping.inputs[3].default_value[2] = 1

                            self.rough_mapping.inputs[3].default_value[0] = 1
                            self.rough_mapping.inputs[3].default_value[1] = 1
                            self.rough_mapping.inputs[3].default_value[2] = 1

                            self.bump_mapping.inputs[3].default_value[0] = 1
                            self.bump_mapping.inputs[3].default_value[1] = 1
                            self.bump_mapping.inputs[3].default_value[2] = 1

                            self.alpha_mapping.inputs[3].default_value[0] = 1
                            self.alpha_mapping.inputs[3].default_value[1] = 1
                            self.alpha_mapping.inputs[3].default_value[2] = 1

                            if self.alpha_mapping:
                                self.alpha_mapping.inputs[3].default_value[
                                    0
                                ] = 1
                                self.alpha_mapping.inputs[3].default_value[
                                    1
                                ] = 1
                                self.alpha_mapping.inputs[3].default_value[
                                    2
                                ] = 1

                            # smudge
                            for n in self.node_tree.nodes:
                                if n.type == "MAPPING":
                                    self.node_tree.links.new(
                                        self.tex_coord.outputs[0],
                                        self.smudge.inputs[0],
                                    )
                                    self.node_tree.links.new(
                                        self.smudge.outputs[0], n.inputs[0]
                                    )

                        context.area.tag_redraw()

                elif event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                    context.area.tag_redraw()
                    if self.nodes is not None:

                        for n in self.nodes:
                            if n.name.startswith("QT_Shader_1"):
                                self.final_node = n

                        for n in self.nodes:
                            if n.name.startswith(
                                "QT_Layer_"
                                + str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                self.final_node = n

                        self.node_tree.links.new(
                            self.out_node.inputs[0], self.final_node.outputs[0]
                        )
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(
                                str(bpy.context.window_manager.my_toolqt.activelayer)
                            ):
                                n.select = True

                    bpy.context.window_manager.my_toolqt.decal = 0
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    bpy.context.window_manager.my_toolqt.selected = 0
                    bpy.context.window_manager.my_toolqt.blend = 0
                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.ob = None
                    if "QuickTexture" in bpy.data.collections:
                        bpy.data.collections["QuickTexture"].hide_viewport = True
                        bpy.data.collections["QuickTexture"].hide_render = True
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
                    return {"FINISHED"}

            return {"RUNNING_MODAL"}

        except:
            if self.nodes:
                for n in self.nodes:
                    if n.name.startswith("QT_Shader_1"):
                        self.final_node = n
                    if n.name.startswith("QT_Layer_2"):
                        self.final_node = n
                    if n.name.startswith("QT_Layer_3"):
                        self.final_node = n
                    if n.name.startswith("QT_Layer_4"):
                        self.final_node = n
                    if n.name.startswith("QT_Layer_5"):
                        self.final_node = n
                self.node_tree.links.new(
                    self.out_node.inputs[0], self.final_node.outputs[0]
                )
            bpy.context.window_manager.my_toolqt.running_qt = 0
            bpy.context.window_manager.my_toolqt.selected = 0
            bpy.context.window_manager.my_toolqt.decal = 0
            bpy.context.window_manager.my_toolqt.blend = 0
            bpy.context.window_manager.my_toolqt.mask = 0
            bpy.context.window_manager.my_toolqt.ob = None
            if "QuickTexture" in bpy.data.collections:
                bpy.data.collections["QuickTexture"].hide_viewport = True
                bpy.data.collections["QuickTexture"].hide_render = True
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
            traceback.print_exc()
            return {"FINISHED"}

    # INVOKE
    def invoke(self, context, event):

        # init
        self.region = context.region
        self.rv3d = context.region_data
        self.region3D = bpy.context.space_data.region_3d

        bpy.context.window_manager.my_toolqt.running_qt = 1
        sel = bpy.context.selected_objects

        bpy.context.window_manager.my_toolqt.decal = 0

        bpy.context.window_manager.my_toolqt.activemap = 1
        bpy.context.window_manager.my_toolqt.activelayer = 1

        ob = None
        ob2 = None
        bpy.context.window_manager.my_toolqt.proc_uv = 0

        bpy.context.window_manager.my_toolqt.matindex = 0

        importbrowser = 0

        if len(sel) > 0:

            bpy.context.window_manager.my_toolqt.matindex = (
                len(sel[0].material_slots) - 1
            )

            # if we're in edit mode, add a new temp shader no matter what
            if context.active_object.mode == "EDIT":
                importbrowser = 1
                bpy.ops.object.mode_set(mode="OBJECT")
                material = bpy.data.materials.new(name="QT_TEMP")
                bpy.context.window_manager.my_toolqt.matindex += 1
                sel[0].data.materials.append(material)
                sel[0].active_material_index = len(sel[0].material_slots) - 1
                for poly in sel[0].data.polygons:
                    if poly.select:
                        poly.material_index = len(sel[0].material_slots) - 1

            if sel[0].data.users > 0:
                bpy.ops.object.select_linked(type="OBDATA")
                sel_instance = [
                    (i_obj)
                    for i_obj in bpy.context.selected_objects
                    if i_obj.name != sel[0].name
                ]
                bpy.ops.object.make_single_user(
                    object=True,
                    obdata=True,
                    material=False,
                    animation=False,
                )

            isdec = 0
            for modifier in sel[0].modifiers:
                if modifier.name.startswith("QT_Decal"):
                    isdec = 1

            if not isdec:
                bpy.ops.object.transform_apply(
                    location=False, rotation=True, scale=True
                )

            for ob in sel:
                if ob.type not in ["CURVE", "META", "MESH"]:
                    return {"FINISHED"}

                if ob.type in ["CURVE", "META"]:
                    bpy.ops.object.convert(target="MESH")
                    sel = bpy.context.selected_objects

            ob = sel[0]
            ob2 = bpy.context.view_layer.objects.active
            bpy.context.window_manager.my_toolqt.ob = sel[0]
            bpy.context.window_manager.my_toolqt.selected = 1
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        else:
            importbrowser = 1

        # nodes
        self.mat = None
        self.tex_coord = None
        self.nodes = None
        self.node_tree = None
        self.out_node = None
        self.out_material = None
        self.group_node = None
        self.core_shader = None
        self.final_node = None
        self.diffuse_mapping = None
        self.rough_mapping = None
        self.bump_mapping = None
        self.mask_mapping = None
        self.diffuse_tex = None
        self.diffuse_hue_sat = None
        self.diffuse_bright_contrast = None
        self.rough_tex = None
        self.rough_bright_contrast = None
        self.rough_invert = None
        self.rough_hue_sat = None
        self.bump_tex = None
        self.bump_bright_contrast = None
        self.bump_bump = None
        self.bump_strength = None
        self.bump_layer = None
        self.bump_invert = None
        self.bump_hue_sat = None
        self.mask_tex = None
        self.mask_bright_contrast = None
        self.mask_invert = None
        self.mask_hue_sat = None
        self.mask_clamp = None
        self.roughness_clamp = None
        self.bump_clamp = None

        self.diffuse_seamless = None
        self.rough_seamless = None
        self.bump_seamless = None
        self.alpha_seamless = None

        self.smudge = None
        self.smudge_tex = None
        self.smudge_bright_contrast = None
        self.smudge_invert = None
        self.smudge_hue_sat = None
        self.smudge_mapping = None

        self.normal_tex = None
        self.normal_strength = None

        self.alpha_type = 1

        self.alpha_tex = None
        self.alpha_mapping = None
        self.alpha_bright_contrast = None
        self.alpha_invert = None
        self.alpha_hue_sat = None
        self.alpha_clamp = None

        self.ao_tex = None
        self.ao_multiply = None

        self.blend_add = None
        self.blend_xyz = None
        self.blend_math = None
        self.blend_power = None
        self.blend_clamp = None
        self.blend_mix = None
        self.blend_noise = None
        self.blend_bright_contrast = None

        self.bevel_mask = None
        self.ao_mask = None

        self.prev_blend_node = None

        self.randval = None
        self.randcolor = None
        self.variation = None

        self.disp_tex = None
        self.disp_mapping = None
        self.disp_vec = None

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
                if collection.hide_viewport == True:
                    collection.hide_viewport = False

        # view
        self.view_vector = Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
        self.window_active, self.zoomlevel = utils.window_info(
            context,
            event,
            bpy.context.preferences.addons[__package__].preferences.window_buffer,
        )
        self.regX = bpy.context.region.width
        self.regY = bpy.context.region.height

        # shading style
        areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
        self.viewlens = 50 / (areas[0].spaces[0].lens)

        # hotkeys
        self.coord = Vector((event.mouse_region_x, event.mouse_region_y))
        self.coord_firstclick = Vector((0, 0))
        self.coord_lastclick = Vector((0, 0))
        self.coord_hotkeyclick = Vector((0, 0))
        self.avg_2d = Vector((0, 0))

        self.mouse_sample_x = []
        self.mouse_sample_y = []
        self.hotkey_press = []

        self.lmb = False
        self.rmb = False
        self.mmb = False

        self.alt = False
        self.ctrl = False
        self.shift = False

        self.a = False
        self.g = False
        self.s = False
        self.r = False
        self.l = False
        self.e = False
        self.shifth = False
        self.alts = False
        self.shifts = False
        self.shiftb = False
        self.shiftn = False
        self.ctrli = False
        self.h = False
        self.v = False
        self.c = False
        self.o = False
        self.x = False

        args = (self, context)
        wm = context.window_manager
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_quickTexture, args, "WINDOW", "POST_PIXEL"
        )
        context.window_manager.modal_handler_add(self)

        existingshader = 0
        material1 = 0
        material2 = 0
        bpy.context.window_manager.my_toolqt.blend = 0

        if len(sel) == 2 and ob2:
            bpy.context.window_manager.my_toolqt.ob = ob2

            for mat in ob2.data.materials:
                if mat:
                    for n in mat.node_tree.nodes:
                        if n.name.startswith("QT_Blend"):
                            bpy.context.window_manager.my_toolqt.blend = 1
                            existingshader = 1

            if not existingshader:
                if sel[0] == ob2:
                    ob1 = sel[1]
                else:
                    ob1 = sel[0]

                # just grabbing the name of the group here
                for mat in ob1.data.materials:
                    if mat:
                        for n in mat.node_tree.nodes:
                            if n.name.startswith("QT_Shader"):
                                node_group_name = n.name
                                material1 = mat

                # this is the active obj im working on
                for mat in ob2.data.materials:
                    if mat:
                        for n in mat.node_tree.nodes:
                            if n.name.startswith("QT_Shader"):
                                shader_node = n
                                material2 = mat

                            if n.name.startswith("QT_Output"):
                                out_mat = n

        if material1 and material2:
            bpy.context.window_manager.my_toolqt.blend = 1
            importbrowser = 1
            objects.blend(
                self, context, material2, shader_node, out_mat, node_group_name
            )

        else:
            if material1 == 0 and material2 == 0:
                # check if QT material exists
                if ob:
                    if ob.data.materials:
                        for mat in ob.data.materials:
                            if mat:
                                if mat.name.startswith("QT"):
                                    if not importbrowser:

                                        for n in mat.node_tree.nodes:
                                            if n.name == "QT_Output":
                                                self.out_material = n

                                            if n.name.startswith("QT_Shader"):
                                                self.nodes = n.node_tree.nodes
                                                self.node_tree = n.node_tree

                                        # set active layer based on latest layer if exists
                                        for n in self.nodes:
                                            if n.name.startswith("QT_Shader_1"):
                                                bpy.context.window_manager.my_toolqt.activelayer = (
                                                    1
                                                )
                                                self.final_node = n
                                            if n.name.startswith("QT_Layer_2"):
                                                bpy.context.window_manager.my_toolqt.activelayer = (
                                                    2
                                                )
                                                self.final_node = n
                                            if n.name.startswith("QT_Layer_3"):
                                                bpy.context.window_manager.my_toolqt.activelayer = (
                                                    3
                                                )
                                                self.final_node = n
                                            if n.name.startswith("QT_Layer_4"):
                                                bpy.context.window_manager.my_toolqt.activelayer = (
                                                    4
                                                )
                                                self.final_node = n
                                            if n.name.startswith("QT_Layer_5"):
                                                bpy.context.window_manager.my_toolqt.activelayer = (
                                                    5
                                                )
                                                self.final_node = n
                                            if n.name == "Group Output":
                                                self.out_node = n

                                            if n.name.startswith("QT_Diffuse_Tex_1"):
                                                if n.projection == "FLAT":
                                                    bpy.context.window_manager.my_toolqt.triplanar = (
                                                        0
                                                    )

                                        self.node_tree.links.new(
                                            self.out_node.inputs[0],
                                            self.final_node.outputs[0],
                                        )
                                        self.out_node.location.y = (
                                            self.final_node.location.y
                                        )
                                        self.out_node.location.x = (
                                            self.final_node.location.x + 300
                                        )

                                        for n in self.nodes:
                                            n.select = False
                                            if n.name.endswith(
                                                str(
                                                    bpy.context.window_manager.my_toolqt.activelayer
                                                )
                                            ):
                                                n.select = True

                                        for n in self.nodes:
                                            if n.select:
                                                if n.name.startswith(
                                                    "QT_UV_Layer_"
                                                    + (
                                                        str(
                                                            bpy.context.window_manager.my_toolqt.activelayer
                                                        )
                                                    )
                                                ):

                                                    if (
                                                        n.label == "Decal"
                                                        or n.label == "View"
                                                    ):
                                                        bpy.context.window_manager.my_toolqt.proc_uv = (
                                                            1
                                                        )

                                                    if n.label == "Box":
                                                        bpy.context.window_manager.my_toolqt.proc_uv = (
                                                            1
                                                        )

                                # remake material QuickTexture style
                                else:

                                    albedo_spec = None
                                    roughness_spec = None
                                    normal_spec = None
                                    ao_spec = None
                                    alpha_spec = None
                                    disp_spec = None

                                    if mat.node_tree:
                                        for n in mat.node_tree.nodes:
                                            if n.type == "TEX_IMAGE":

                                                if (
                                                    "albedo"
                                                    in str(n.image.name).lower()
                                                ):
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "color" in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "col" in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "basecolor"
                                                    in str(n.image.name).lower()
                                                ):
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "basecol"
                                                    in str(n.image.name).lower()
                                                ):
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "diffuse"
                                                    in str(n.image.name).lower()
                                                ):
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "dif" in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "diff" in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[
                                                        n.image.name
                                                    ]

                                                if "rough" in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "glossiness"
                                                    in str(n.image.name).lower()
                                                ):
                                                    roughness_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "gloss" in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "spec" in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "specular"
                                                    in str(n.image.name).lower()
                                                ):
                                                    roughness_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "roughness"
                                                    in str(n.image.name).lower()
                                                ):
                                                    roughness_spec = bpy.data.images[
                                                        n.image.name
                                                    ]

                                                if "norm" in str(n.image.name).lower():
                                                    normal_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "nrm" in str(n.image.name).lower():
                                                    normal_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "nmap" in str(n.image.name).lower():
                                                    normal_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "normal"
                                                    in str(n.image.name).lower()
                                                ):
                                                    normal_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "nor" in str(n.image.name).lower():
                                                    normal_spec = bpy.data.images[
                                                        n.image.name
                                                    ]

                                                if (
                                                    "opacity"
                                                    in str(n.image.name).lower()
                                                ):
                                                    alpha_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "opac" in str(n.image.name).lower():
                                                    alpha_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "alpha" in str(n.image.name).lower():
                                                    alpha_spec = bpy.data.images[
                                                        n.image.name
                                                    ]

                                                if "ao" in str(n.image.name).lower():
                                                    ao_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "ambientocclusion"
                                                    in str(n.image.name).lower()
                                                ):
                                                    ao_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if (
                                                    "disp"
                                                    in str(n.image.name).lower()
                                                ):
                                                    disp_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "displacement" in str(n.image.name).lower():
                                                    disp_spec = bpy.data.images[
                                                        n.image.name
                                                    ]
                                                if "height" in str(n.image.name).lower():
                                                    disp_spec = bpy.data.images[
                                                        n.image.name
                                                    ]

                                    if albedo_spec:
                                        objects.remake_material(
                                            ob,
                                            mat,
                                            albedo_spec,
                                            roughness_spec,
                                            normal_spec,
                                            alpha_spec,
                                            ao_spec,
                                            disp_spec,
                                        )
                                    else:
                                        if len(ob.data.materials) > 0:
                                            for m in ob.data.materials:
                                                if m:
                                                    m = None
                                            importbrowser = 1
                            else:
                                if len(ob.data.materials) > 0:
                                    for m in ob.data.materials:
                                        if m:
                                            m = None
                                    importbrowser = 1
                    else:
                        importbrowser = 1

                if importbrowser:
                    # check if object has proc uv
                    hasproc = 0
                    if ob:
                        if bpy.context.window_manager.my_toolqt.forceprocedural:
                            if len(ob.data.uv_layers) > 0:
                                uvs = [
                                    uv
                                    for uv in ob.data.uv_layers
                                    if uv != ob.data.uv_layers
                                ]
                                while uvs:
                                    ob.data.uv_layers.remove(uvs.pop())

                        if len(ob.data.uv_layers) > 0:
                            for layer in ob.data.uv_layers:
                                if layer.name.startswith("QT_UV"):
                                    hasproc = 1

                        else:
                            hasproc = 1

                        if len(ob.data.uv_layers) == 0:
                            if not bpy.context.window_manager.my_toolqt.forceprocedural:
                                bpy.ops.object.editmode_toggle()
                                bpy.ops.mesh.select_all(action="SELECT")
                                bpy.ops.uv.smart_project()
                                bpy.ops.object.editmode_toggle()

                    if hasproc:
                        bpy.context.window_manager.my_toolqt.proc_uv = 1
                    else:
                        bpy.context.window_manager.my_toolqt.proc_uv = 0

                    bpy.ops.qt.material_qt("INVOKE_DEFAULT")

            else:
                bpy.context.window_manager.my_toolqt.running_qt = 0

        return {"RUNNING_MODAL"}


class QT_OT_material_qt(Operator, ImportHelper):
    bl_idname = "qt.material_qt"
    bl_label = "Create Material"
    bl_options = {"PRESET", "UNDO"}

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        # SHADER
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects
        if len(sel) > 0:
            ob = sel[0]
            dirname = os.path.dirname(self.filepath)

            if len(self.files) == 0:
                bpy.context.window_manager.my_toolqt.running_qt = 0
                return {"FINISHED"}
            elif len(self.files) == 1:
                f = self.files[0]
                img_path = os.path.join(dirname, f.name)

                bpy.ops.image.open(filepath=img_path)
                bpy.data.images[f.name].filepath = img_path

            elif len(self.files) > 1:
                f = self.files[0]
                for x in self.files:
                    if "albedo" in str(x.name).lower():
                        f = x
                    if "diffuse" in str(x.name).lower():
                        f = x
                    if "color" in str(x.name).lower():
                        f = x
                    if "col" in str(x.name).lower():
                        f = x
                    if "basecolor" in str(x.name).lower():
                        f = x
                    if "basecol" in str(x.name).lower():
                        f = x
                    img_path = os.path.join(dirname, f.name)

                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path

            img_spec = bpy.data.images[f.name]
            material = objects.create_material(
                self,
                context,
                img_spec,
                0,
                bpy.context.window_manager.my_toolqt.mode,
                bpy.context.window_manager.my_toolqt.proc_uv,
                self.files,
                dirname,
                bpy.context.window_manager.my_toolqt.decal,
                bpy.context.window_manager.my_toolqt.selected,
            )
            bpy.context.window_manager.my_toolqt.selected = 1

        # REFERENCE
        else:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            bpy.context.window_manager.my_toolqt.proc_uv = 1
            dirname = os.path.dirname(self.filepath)

            for f in self.files:
                if len(self.files) == 0:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {"FINISHED"}
                elif len(self.files) == 1:
                    f = self.files[0]
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                elif len(self.files) > 1:
                    f = self.files[0]
                    for x in self.files:
                        if "albedo" in str(x.name).lower():
                            f = x
                        if "diffuse" in str(x.name).lower():
                            f = x
                        if "color" in str(x.name).lower():
                            f = x
                        if "col" in str(x.name).lower():
                            f = x
                        if "basecolor" in str(x.name).lower():
                            f = x
                        if "basecol" in str(x.name).lower():
                            f = x
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        bpy.data.images[f.name].filepath = img_path

            img_spec = bpy.data.images[f.name]
            ob = objects.create_image_plane(self, context, f.name, img_spec)
            material = objects.create_material(
                self,
                context,
                img_spec,
                1,
                bpy.context.window_manager.my_toolqt.mode,
                bpy.context.window_manager.my_toolqt.proc_uv,
                self.files,
                dirname,
                bpy.context.window_manager.my_toolqt.decal,
                bpy.context.window_manager.my_toolqt.selected,
            )
            bpy.context.window_manager.my_toolqt.ob = ob

            if len(ob.data.uv_layers) > 0:
                for layer in ob.data.uv_layers:
                    if layer.name == "UVMap":
                        ob.data.uv_layers.remove(layer)

        # setup params
        material.name = "QT_" + material.name
        if ob.data.materials:
            ob.data.materials[-1] = material
        else:
            ob.data.materials.append(material)

        bpy.ops.object.make_links_data(type="MATERIAL")

        px, py = img_spec.size
        if px == 0:
            px = 1000
        if py == 0:
            py = 1000
        size = px / py
        bpy.context.window_manager.my_toolqt.activelayer = 1
        bpy.context.window_manager.my_toolqt.activemap = 1

        # material settings
        material.blend_method = "HASHED"
        material.shadow_method = "HASHED"
        material.use_screen_refraction = True
        material.show_transparent_back = False

        if bpy.context.window_manager.my_toolqt.proc_uv:
            newlayer = 0

            if (
                bpy.context.window_manager.my_toolqt.mode == "view"
                or bpy.context.window_manager.my_toolqt.decal
            ):
                layer = bpy.context.window_manager.my_toolqt.ob.data.uv_layers.get(
                    "QT_UV_View_Layer_1"
                )
                if layer is None:
                    newlayer = 1
                    uvname = "QT_UV_View_Layer_1"
                    ob.data.uv_layers.new(name=uvname)
                    ob.data.uv_layers[uvname].active = True
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action="SELECT")
                    bpy.ops.uv.project_from_view(
                        camera_bounds=False, correct_aspect=True, scale_to_bounds=False
                    )
                    bpy.ops.object.editmode_toggle()

            else:
                layer = bpy.context.window_manager.my_toolqt.ob.data.uv_layers.get(
                    "QT_UV_Box_Layer_1"
                )
                if layer is None:
                    newlayer = 1
                    uvname = "QT_UV_Box_Layer_1"
                    ob.data.uv_layers.new(name=uvname)
                    ob.data.uv_layers[uvname].active = True
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action="SELECT")
                    bpy.ops.uv.project_from_view(
                        camera_bounds=False, correct_aspect=True, scale_to_bounds=False
                    )
                    bpy.ops.object.editmode_toggle()

            if newlayer and bpy.context.window_manager.my_toolqt.mode == "box":
                # PROJECTION SETUP
                empty_uv1 = objects.create_empty(
                    "QT_UV_Z_Plus", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
                )
                empty_uv2 = objects.create_empty(
                    "QT_UV_Z_Min", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
                )
                empty_uv3 = objects.create_empty(
                    "QT_UV_Y_Plus", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
                )
                empty_uv4 = objects.create_empty(
                    "QT_UV_Y_Min", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
                )
                empty_uv5 = objects.create_empty(
                    "QT_UV_X_Plus", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
                )
                empty_uv6 = objects.create_empty(
                    "QT_UV_X_Min", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
                )
                col = bpy.data.collections["QuickTexture"]
                objects.add_to_collection(empty_uv1.name, col, context)
                objects.add_to_collection(empty_uv2.name, col, context)
                objects.add_to_collection(empty_uv3.name, col, context)
                objects.add_to_collection(empty_uv4.name, col, context)
                objects.add_to_collection(empty_uv5.name, col, context)
                objects.add_to_collection(empty_uv6.name, col, context)

                # Z
                empty_uv2.rotation_euler.y = pi
                empty_uv2.rotation_euler.z = pi

                # Y
                empty_uv3.rotation_euler.x = -pi / 2
                empty_uv3.rotation_euler.y = pi
                empty_uv4.rotation_euler.x = pi / 2

                # X
                empty_uv5.rotation_euler.z = pi / 2
                empty_uv5.rotation_euler.x = pi / 2

                empty_uv6.rotation_euler.z = -pi / 2
                empty_uv6.rotation_euler.x = pi / 2

                mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get("QT_UV_Box")
                if mod is None:
                    rmod1 = ob.modifiers.new(name="QT_UV_Box", type="UV_PROJECT")
                    rmod1.projector_count = 6
                    rmod1.projectors[0].object = bpy.data.objects[empty_uv1.name]
                    rmod1.projectors[1].object = bpy.data.objects[empty_uv2.name]
                    rmod1.projectors[2].object = bpy.data.objects[empty_uv3.name]
                    rmod1.projectors[3].object = bpy.data.objects[empty_uv4.name]
                    rmod1.projectors[4].object = bpy.data.objects[empty_uv5.name]
                    rmod1.projectors[5].object = bpy.data.objects[empty_uv6.name]
                    rmod1.uv_layer = "QT_UV_Box_Layer_1"

            if (
                bpy.context.window_manager.my_toolqt.mode == "view"
                or bpy.context.window_manager.my_toolqt.decal
            ):
                empty_ob = objects.create_empty(
                    "QT_UV_View_1", "SINGLE_ARROW", Vector((0, 0, 0)), context, 0
                )
                col = bpy.data.collections["QuickTexture"]
                objects.add_to_collection(empty_ob.name, col, context)

                if len(sel) > 0:
                    empty_ob.rotation_euler = (
                        context.region_data.view_rotation.to_euler()
                    )
                else:
                    empty_ob.rotation_euler.x = pi / 2

                rmod1 = ob.modifiers.new(name="QT_UV_View_1", type="UV_PROJECT")
                rmod1.projector_count = 1
                rmod1.projectors[0].object = bpy.data.objects[empty_ob.name]

                rmod1.uv_layer = "QT_UV_View_Layer_" + str(
                    bpy.context.window_manager.my_toolqt.activelayer
                )

                local_bbox_center = 0.125 * sum(
                    (Vector(b) for b in ob.bound_box), Vector()
                )
                global_bbox_center = ob.matrix_world @ local_bbox_center
                empty_ob.location = global_bbox_center

            # parenting
            bpy.ops.object.select_all(action="DESELECT")

            if bpy.context.window_manager.my_toolqt.decal:
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

            else:
                if (
                    bpy.context.window_manager.my_toolqt.mode == "view"
                    and len(sel) == 0
                    or bpy.context.window_manager.my_toolqt.decal
                    and len(sel) == 0
                ):
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

        return {"FINISHED"}


class QT_OT_boxlayer_qt(Operator, ImportHelper):
    bl_idname = "qt.boxlayer_qt"
    bl_label = "New Box Layer"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Box Layer Texture"

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    @classmethod
    def poll(self, context):
        if bpy.context.window_manager.my_toolqt.activelayer < 5:
            return True
        else:
            return None

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects
        ob = sel[0]

        bpy.context.window_manager.my_toolqt.activelayer += 1
        dirname = os.path.dirname(self.filepath)

        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            return {"FINISHED"}
        elif len(self.files) == 1:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
        elif len(self.files) > 1:
            f = self.files[0]
            for x in self.files:
                if "albedo" in str(x.name).lower():
                    f = x
                if "diffuse" in str(x.name).lower():
                    f = x
                if "color" in str(x.name).lower():
                    f = x
                if "col" in str(x.name).lower():
                    f = x
                if "basecolor" in str(x.name).lower():
                    f = x
                if "basecol" in str(x.name).lower():
                    f = x
                img_path = os.path.join(dirname, f.name)
                bpy.ops.image.open(filepath=img_path)
                bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]
        width, height = img_spec.size
        size = width / height
        bpy.context.window_manager.my_toolqt.activemap = 1

        layer2 = bpy.context.window_manager.my_toolqt.ob.data.uv_layers.get(
            "QT_UV_Box_Layer_1"
        )
        if not layer2:
            uvname = "QT_UV_Box_Layer_1"
            ob.data.uv_layers.new(name=uvname)
            ob.data.uv_layers[uvname].active = True

        bpy.context.window_manager.my_toolqt.proc_uv = 1
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.project_from_view(
            camera_bounds=False, correct_aspect=True, scale_to_bounds=False
        )
        bpy.ops.object.editmode_toggle()

        # PROJECTION SETUP
        empty_uv1 = None
        empty_uv1 = objects.create_empty(
            "QT_UV_Z_Plus", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
        )
        empty_uv2 = objects.create_empty(
            "QT_UV_Z_Min", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
        )
        empty_uv3 = objects.create_empty(
            "QT_UV_Y_Plus", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
        )
        empty_uv4 = objects.create_empty(
            "QT_UV_Y_Min", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
        )
        empty_uv5 = objects.create_empty(
            "QT_UV_X_Plus", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
        )
        empty_uv6 = objects.create_empty(
            "QT_UV_X_Min", "SINGLE_ARROW", Vector((0, 0, 0)), context, 1
        )
        col = bpy.data.collections["QuickTexture"]

        if empty_uv1:
            objects.add_to_collection(empty_uv1.name, col, context)
            objects.add_to_collection(empty_uv2.name, col, context)
            objects.add_to_collection(empty_uv3.name, col, context)
            objects.add_to_collection(empty_uv4.name, col, context)
            objects.add_to_collection(empty_uv5.name, col, context)
            objects.add_to_collection(empty_uv6.name, col, context)

            # Z
            empty_uv2.rotation_euler.y = pi
            empty_uv2.rotation_euler.z = pi

            # Y
            empty_uv3.rotation_euler.x = -pi / 2
            empty_uv3.rotation_euler.y = pi
            empty_uv4.rotation_euler.x = pi / 2

            # X
            empty_uv5.rotation_euler.z = pi / 2
            empty_uv5.rotation_euler.x = pi / 2

            empty_uv6.rotation_euler.z = -pi / 2
            empty_uv6.rotation_euler.x = pi / 2

        mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get("QT_UV_Box")
        if mod is None:
            rmod1 = ob.modifiers.new(name="QT_UV_Box", type="UV_PROJECT")
            rmod1.projector_count = 6
            rmod1.projectors[0].object = bpy.data.objects[empty_uv1.name]
            rmod1.projectors[1].object = bpy.data.objects[empty_uv2.name]
            rmod1.projectors[2].object = bpy.data.objects[empty_uv3.name]
            rmod1.projectors[3].object = bpy.data.objects[empty_uv4.name]
            rmod1.projectors[4].object = bpy.data.objects[empty_uv5.name]
            rmod1.projectors[5].object = bpy.data.objects[empty_uv6.name]
            rmod1.uv_layer = "QT_UV_Box_Layer_1"

        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob

        objects.box_layer(
            self,
            context,
            img_spec,
            ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
            bpy.context.window_manager.my_toolqt.activelayer,
            self.files,
            dirname,
            bpy.context.window_manager.my_toolqt.decal,
            bpy.context.window_manager.my_toolqt.selected,
        )

        return {"FINISHED"}


class QT_OT_viewlayer_qt(Operator, ImportHelper):
    bl_idname = "qt.viewlayer_qt"
    bl_label = "New View Layer"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New View Layer Texture"

    @classmethod
    def poll(self, context):
        if bpy.context.window_manager.my_toolqt.activelayer < 5:
            return True
        else:
            return None

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects
        ob = sel[0]

        bpy.context.window_manager.my_toolqt.activelayer += 1

        ###############################################################################################################

        layer2 = None
        layer3 = None
        layer4 = None

        ob2 = None
        ob3 = None
        ob4 = None

        mod2 = bpy.context.window_manager.my_toolqt.ob.modifiers.get("QT_UV_View_2")
        mod3 = bpy.context.window_manager.my_toolqt.ob.modifiers.get("QT_UV_View_3")
        mod4 = bpy.context.window_manager.my_toolqt.ob.modifiers.get("QT_UV_View_4")

        for n in ob.data.uv_layers:
            if n.name.startswith("QT_UV_View_Layer_2"):
                layer2 = n
            if n.name.startswith("QT_UV_View_Layer_3"):
                layer3 = n
            if n.name.startswith("QT_UV_View_Layer_4"):
                layer4 = n

        if bpy.context.window_manager.my_toolqt.activelayer == 2 and layer2:
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

        if bpy.context.window_manager.my_toolqt.activelayer == 3 and layer3:
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

        if bpy.context.window_manager.my_toolqt.activelayer == 4 and layer4:
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

        bpy.context.window_manager.my_toolqt.proc_uv = 1

        uvname = "QT_UV_View_Layer_" + str(
            bpy.context.window_manager.my_toolqt.activelayer
        )
        ob.data.uv_layers.new(name=uvname)

        empty_ob = objects.create_empty(
            uvname, "SINGLE_ARROW", Vector((0, 0, 0)), context, 0
        )
        col = bpy.data.collections["QuickTexture"]
        objects.add_to_collection(empty_ob.name, col, context)
        empty_ob.rotation_euler = context.region_data.view_rotation.to_euler()

        local_bbox_center = 0.125 * sum((Vector(b) for b in ob.bound_box), Vector())
        global_bbox_center = ob.matrix_world @ local_bbox_center
        empty_ob.location = global_bbox_center

        rmod1 = ob.modifiers.new(name=uvname, type="UV_PROJECT")
        rmod1.projector_count = 1
        rmod1.projectors[0].object = bpy.data.objects[empty_ob.name]
        rmod1.uv_layer = "QT_UV_View_Layer_" + str(
            bpy.context.window_manager.my_toolqt.activelayer
        )

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

        #########################################################################

        dirname = os.path.dirname(self.filepath)
        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0
            return {"FINISHED"}
        elif len(self.files) == 1:
            f = self.files[0]
            img_path = os.path.join(dirname, f.name)
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
        elif len(self.files) > 1:
            f = self.files[0]
            for x in self.files:
                if "albedo" in str(x.name).lower():
                    f = x
                if "diffuse" in str(x.name).lower():
                    f = x
                if "color" in str(x.name).lower():
                    f = x
                if "col" in str(x.name).lower():
                    f = x
                if "basecolor" in str(x.name).lower():
                    f = x
                if "basecol" in str(x.name).lower():
                    f = x
                img_path = os.path.join(dirname, f.name)
                bpy.ops.image.open(filepath=img_path)
                bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]
        width, height = img_spec.size
        size = width / height
        bpy.context.window_manager.my_toolqt.activemap = 1
        objects.view_layer(
            self,
            context,
            img_spec,
            ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
            bpy.context.window_manager.my_toolqt.activelayer,
            self.files,
            dirname,
            bpy.context.window_manager.my_toolqt.decal,
            bpy.context.window_manager.my_toolqt.selected,
        )

        return {"FINISHED"}


class QT_OT_texturemask_qt(Operator, ImportHelper):
    bl_idname = "qt.texturemask_qt"
    bl_label = "Texture Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Texture Mask"

    @classmethod
    def poll(self, context):

        nodes = None
        if bpy.context.window_manager.my_toolqt.activelayer > 1:
            if bpy.context.window_manager.my_toolqt.selected:
                if bpy.context.window_manager.my_toolqt.ob:
                    if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 0:
                        mat = bpy.context.window_manager.my_toolqt.ob.material_slots[
                            bpy.context.window_manager.my_toolqt.matindex
                        ].material
                        if mat:
                            for n in mat.node_tree.nodes:
                                if n.name.startswith("QT_Shader"):
                                    nodes = n.node_tree.nodes
                                    node_tree = n.node_tree
            # check if mask exists on current layer
            mask = 0
            if nodes:
                for n in nodes:
                    if n.name.endswith(
                        "Mask_" + str(bpy.context.window_manager.my_toolqt.activelayer)
                    ):
                        mask = 1

            if mask == 0:
                return True
            else:
                return None
        else:
            return None

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects
        ob = sel[0]
        dirname = os.path.dirname(self.filepath)

        if len(self.files) > 0:
            f = self.files[0]
            img_path = os.path.join(
                dirname, f.name
            )  # get filepath properties from collection pointer
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]
            width, height = img_spec.size
            size = width / height
            bpy.context.window_manager.my_toolqt.activemap = 4
            objects.texture_mask(
                self,
                context,
                img_spec,
                ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
                bpy.context.window_manager.my_toolqt.activelayer,
                bpy.context.window_manager.my_toolqt.proc_uv,
            )

        return {"FINISHED"}


class QT_OT_cavitymask_qt(Operator):
    bl_idname = "qt.cavitymask_qt"
    bl_label = "Cavity Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Cavity Mask"

    @classmethod
    def poll(self, context):

        nodes = None
        if bpy.context.window_manager.my_toolqt.activelayer > 1:
            if bpy.context.window_manager.my_toolqt.selected:
                if bpy.context.window_manager.my_toolqt.ob:
                    if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 0:
                        mat = bpy.context.window_manager.my_toolqt.ob.material_slots[
                            bpy.context.window_manager.my_toolqt.matindex
                        ].material
                        if mat:
                            for n in mat.node_tree.nodes:
                                if n.name.startswith("QT_Shader"):
                                    nodes = n.node_tree.nodes
                                    node_tree = n.node_tree
            # check if mask exists on current layer
            mask = 0
            if nodes:
                for n in nodes:
                    if n.name.endswith(
                        "Mask_" + str(bpy.context.window_manager.my_toolqt.activelayer)
                    ):
                        mask = 1

            if mask == 0:
                return True
            else:
                return None
        else:
            return None

    def execute(self, context):

        ob = bpy.context.active_object

        bpy.context.window_manager.my_toolqt.mask = 1
        bpy.context.window_manager.my_toolqt.activemap = 4
        objects.cavity_mask(
            self,
            context,
            ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
            bpy.context.window_manager.my_toolqt.activelayer,
        )

        return {"FINISHED"}


class QT_OT_aomask_qt(Operator):
    bl_idname = "qt.aomask_qt"
    bl_label = "AO Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New AO Mask"

    @classmethod
    def poll(self, context):

        nodes = None
        if bpy.context.window_manager.my_toolqt.activelayer > 1:
            if bpy.context.window_manager.my_toolqt.selected:
                if bpy.context.window_manager.my_toolqt.ob:
                    if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 0:
                        mat = bpy.context.window_manager.my_toolqt.ob.material_slots[
                            bpy.context.window_manager.my_toolqt.matindex
                        ].material
                        if mat:
                            for n in mat.node_tree.nodes:
                                if n.name.startswith("QT_Shader"):
                                    nodes = n.node_tree.nodes
                                    node_tree = n.node_tree
            # check if mask exists on current layer
            mask = 0
            if nodes:
                for n in nodes:
                    if n.name.endswith(
                        "Mask_" + str(bpy.context.window_manager.my_toolqt.activelayer)
                    ):
                        mask = 1

            if mask == 0:
                return True
            else:
                return None
        else:
            return None

    def execute(self, context):

        ob = bpy.context.active_object

        bpy.context.window_manager.my_toolqt.mask = 1
        bpy.context.window_manager.my_toolqt.activemap = 4
        objects.ao_mask(
            self,
            context,
            ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
            bpy.context.window_manager.my_toolqt.activelayer,
        )

        return {"FINISHED"}


class QT_OT_depthmask_qt(Operator, ImportHelper):
    bl_idname = "qt.depthmask_qt"
    bl_label = "Depth Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Depth Mask"

    @classmethod
    def poll(self, context):

        nodes = None
        if (
            bpy.context.window_manager.my_toolqt.blend == 0
            and bpy.context.window_manager.my_toolqt.mask == 0
        ):
            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                if bpy.context.window_manager.my_toolqt.selected:
                    if bpy.context.window_manager.my_toolqt.ob:
                        if (
                            len(bpy.context.window_manager.my_toolqt.ob.material_slots)
                            > 0
                        ):
                            mat = (
                                bpy.context.window_manager.my_toolqt.ob.material_slots[
                                    bpy.context.window_manager.my_toolqt.matindex
                                ].material
                            )
                            if mat:
                                for n in mat.node_tree.nodes:
                                    if n.name.startswith("QT_Shader"):
                                        nodes = n.node_tree.nodes
                                        node_tree = n.node_tree
                # check if mask exists on current layer
                mask = 0
                if nodes:
                    for n in nodes:
                        if n.name.endswith(
                            "Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            mask = 1

                if mask == 0:
                    return True
                else:
                    return None
            else:
                return None
        else:
            return None

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects
        ob = sel[0]
        dirname = os.path.dirname(self.filepath)

        if len(self.files) > 0:
            f = self.files[0]
            img_path = os.path.join(
                dirname, f.name
            )  # get filepath properties from collection pointer
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]
            width, height = img_spec.size
            size = width / height
            bpy.context.window_manager.my_toolqt.activemap = 4
            objects.depth_mask(
                self,
                context,
                img_spec,
                ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
                bpy.context.window_manager.my_toolqt.activelayer,
                bpy.context.window_manager.my_toolqt.proc_uv,
            )

        return {"FINISHED"}


class QT_OT_vertexmask_qt(Operator):
    bl_idname = "qt.vertexmask_qt"
    bl_label = "Vertex Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Vertex Mask"

    @classmethod
    def poll(self, context):

        nodes = None
        if bpy.context.window_manager.my_toolqt.activelayer > 1:
            if (
                len(bpy.context.window_manager.my_toolqt.ob.material_slots)
                > 0
            ):
                mat = (
                    bpy.context.window_manager.my_toolqt.ob.material_slots[
                        bpy.context.window_manager.my_toolqt.matindex
                    ].material
                )
                if mat:
                    for n in mat.node_tree.nodes:
                        if n.name.startswith("QT_Shader"):
                            nodes = n.node_tree.nodes
                mask = 0
                if nodes:
                    for n in nodes:
                        if n.name.endswith(
                            "Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            mask = 1

                if mask == 0:
                    return True
                else:
                    return None
            else:
                return None
        else:
            return None

    def execute(self, context):

        sel = bpy.context.selected_objects
        ob = sel[0]

        vertex = ob.data.color_attributes.active_color.name
        objects.vertex_mask(
            self,
            context,
            ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
            bpy.context.window_manager.my_toolqt.activelayer, vertex,
        )

        return {"FINISHED"}


class QT_OT_heightmask_qt(Operator):
    bl_idname = "qt.heightmask_qt"
    bl_label = "Height Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Height Mask"

    @classmethod
    def poll(self, context):

        nodes = None
        if (
            bpy.context.window_manager.my_toolqt.blend == 0
            and bpy.context.window_manager.my_toolqt.mask == 0
        ):
            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                if bpy.context.window_manager.my_toolqt.selected:
                    if bpy.context.window_manager.my_toolqt.ob:
                        if (
                            len(bpy.context.window_manager.my_toolqt.ob.material_slots)
                            > 0
                        ):
                            mat = (
                                bpy.context.window_manager.my_toolqt.ob.material_slots[
                                    bpy.context.window_manager.my_toolqt.matindex
                                ].material
                            )
                            if mat:
                                for n in mat.node_tree.nodes:
                                    if n.name.startswith("QT_Shader"):
                                        nodes = n.node_tree.nodes
                                        node_tree = n.node_tree
                # check if mask exists on current layer
                mask = 0
                if nodes:
                    for n in nodes:
                        if n.name.endswith(
                            "Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            mask = 1

                if mask == 0:
                    return True
                else:
                    return None
            else:
                return None
        else:
            return None

    def execute(self, context):

        sel = bpy.context.selected_objects
        ob = sel[0]
        bpy.context.window_manager.my_toolqt.activemap = 4
        bpy.context.window_manager.my_toolqt.mask = 1
        objects.height_mask(
            self,
            context,
            ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
            bpy.context.window_manager.my_toolqt.activelayer,
        )

        return {"FINISHED"}


class QT_OT_normalmask_qt(Operator):
    bl_idname = "qt.normalmask_qt"
    bl_label = "Normal Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Normal Mask"

    @classmethod
    def poll(self, context):

        nodes = None
        if (
            bpy.context.window_manager.my_toolqt.blend == 0
            and bpy.context.window_manager.my_toolqt.mask == 0
        ):
            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                if bpy.context.window_manager.my_toolqt.selected:
                    if bpy.context.window_manager.my_toolqt.ob:
                        if (
                            len(bpy.context.window_manager.my_toolqt.ob.material_slots)
                            > 0
                        ):
                            mat = (
                                bpy.context.window_manager.my_toolqt.ob.material_slots[
                                    bpy.context.window_manager.my_toolqt.matindex
                                ].material
                            )
                            if mat:
                                for n in mat.node_tree.nodes:
                                    if n.name.startswith("QT_Shader"):
                                        nodes = n.node_tree.nodes
                                        node_tree = n.node_tree
                # check if mask exists on current layer
                mask = 0
                if nodes:
                    for n in nodes:
                        if n.name.endswith(
                            "Mask_"
                            + str(bpy.context.window_manager.my_toolqt.activelayer)
                        ):
                            mask = 1

                if mask == 0:
                    return True
                else:
                    return None
            else:
                return None
        else:
            return None

    def execute(self, context):

        sel = bpy.context.selected_objects
        ob = sel[0]
        bpy.context.window_manager.my_toolqt.activemap = 4
        bpy.context.window_manager.my_toolqt.mask = 1
        objects.normal_mask(
            self,
            context,
            ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
            bpy.context.window_manager.my_toolqt.activelayer,
        )

        return {"FINISHED"}


class QT_OT_smudge_qt(Operator, ImportHelper):
    bl_idname = "qt.smudge_qt"
    bl_label = "Smudge Mask"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Create New Smudge Mask"

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects
        ob = sel[0]
        dirname = os.path.dirname(self.filepath)

        if len(self.files) > 0:
            f = self.files[0]
            img_path = os.path.join(
                dirname, f.name
            )  # get filepath properties from collection pointer
            bpy.ops.image.open(filepath=img_path)
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]
            width, height = img_spec.size
            size = width / height
            bpy.context.window_manager.my_toolqt.activemap = 7
            objects.smudge_mask(
                self,
                context,
                img_spec,
                ob.data.materials[bpy.context.window_manager.my_toolqt.matindex],
                bpy.context.window_manager.my_toolqt.activelayer,
                bpy.context.window_manager.my_toolqt.proc_uv,
            )

        return {"FINISHED"}

        return {"FINISHED"}


class QT_OT_replacemaps_qt(Operator, ImportHelper):
    bl_idname = "qt.replacemaps"
    bl_label = "Replace Texture"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Replace Texture Maps"

    @classmethod
    def poll(self, context):
        if (
            bpy.context.window_manager.my_toolqt.blend == 0
            and bpy.context.window_manager.my_toolqt.mask == 0
        ):
            return True
        else:
            return None

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        f = self.files[0]
        img_path = os.path.join(
            dirname, f.name
        )  # get filepath properties from collection pointer
        bpy.ops.image.open(filepath=img_path)
        bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]

        width, height = img_spec.size
        size = width / height

        nodes = None
        node_tree = None

        sel = bpy.context.selected_objects
        ob = sel[0]
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.matindex].material

        for n in mat.node_tree.nodes:
            if n.name.startswith("QT_Shader"):
                nodes = n.node_tree.nodes
                node_tree = n.node_tree

        diffuse_mapping = None
        rough_mapping = None
        bump_mapping = None
        mask_mapping = None
        alpha_mapping = None
        disp_mapping = None

        diffuse_tex = None
        rough_tex = None
        bump_tex = None
        mask_tex = None
        normal_tex = None
        alpha_tex = None
        ao_tex = None
        disp_tex = None

        albedo_spec = None
        roughness_spec = None
        normal_spec = None
        ao_spec = None
        alpha_spec = None
        disp_spec = None

        if len(self.files) > 1:
            for f in self.files:
                if "albedo" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]
                if "diffuse" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]
                if "diff" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]
                if "color" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]
                if "col" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]
                if "basecolor" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]
                if "basecol" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]
                if "roughness" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]
                if "rough" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]
                if "glossiness" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]
                if "gloss" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]
                if "spec" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]
                if "specular" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]
                if "normal" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]
                if "norm" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]
                if "nor" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]
                if "nmap" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]
                if "nrm" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]
                if "opacity" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    alpha_spec = bpy.data.images[f.name]
                if "opac" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    alpha_spec = bpy.data.images[f.name]
                if "alpha" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    alpha_spec = bpy.data.images[f.name]
                if "ao" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    ao_spec = bpy.data.images[f.name]
                if "ambientocclusion" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path
                    ao_spec = bpy.data.images[f.name]
                if "displacement" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    disp_spec = bpy.data.images[f.name]
                if "disp" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    disp_spec = bpy.data.images[f.name]
                if "dis" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    disp_spec = bpy.data.images[f.name]
                if "height" in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    disp_spec = bpy.data.images[f.name]

        if nodes:
            for n in nodes:
                if n.name.startswith(
                    "QT_Diffuse_Mapping_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    diffuse_mapping = n
                if n.name.startswith(
                    "QT_Rough_Mapping_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    rough_mapping = n
                if n.name.startswith(
                    "QT_Bump_Mapping_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    bump_mapping = n
                if n.name.startswith(
                    "QT_Mapping_Mask_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    mask_mapping = n
                if n.name.startswith(
                    "QT_Clamp_Mask_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    mask_clamp = n
                if n.name.startswith(
                    "QT_Alpha_Mapping_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    alpha_mapping = n

                if n.name.startswith(
                    "QT_Diffuse_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    diffuse_tex = n
                if n.name.startswith(
                    "QT_Rough_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    rough_tex = n
                if n.name.startswith(
                    "QT_Bump_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    bump_tex = n
                if n.name.startswith(
                    "QT_Normal_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    normal_tex = n
                if n.name.startswith(
                    "QT_Opacity_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    opacity_tex = n
                if n.name.startswith(
                    "QT_AO_Tex_" + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    ao_tex = n
                if n.name.startswith(
                    "QT_Tex_Mask_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    mask_tex = n
                if n.name.startswith(
                    "QT_Alpha_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    alpha_tex = n

                if n.name.startswith(
                    "QT_Shader_" + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    layer = n
                if n.name.startswith(
                    "QT_Layer_" + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    layer = n

                if n.name.startswith(
                    "QT_Displacement_Mapping_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    disp_mapping = n
                if n.name.startswith(
                    "QT_Disp_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    disp_tex = n

        if bpy.context.window_manager.my_toolqt.activemap == 1:

            if diffuse_mapping:
                diffuse_mapping.inputs[3].default_value[0] = size / 2
                diffuse_mapping.inputs[3].default_value[1] = 0.5
                diffuse_mapping.inputs[1].default_value[0] = 0.5 + (
                    diffuse_mapping.inputs[3].default_value[0] / 2
                )
                diffuse_mapping.inputs[1].default_value[1] = 0.25

                if albedo_spec:
                    diffuse_tex.image = albedo_spec
                else:
                    diffuse_tex.image = img_spec

            if rough_mapping:
                rough_mapping.inputs[3].default_value[0] = size / 2
                rough_mapping.inputs[3].default_value[1] = 0.5
                rough_mapping.inputs[1].default_value[0] = 0.5 + (
                    rough_mapping.inputs[3].default_value[0] / 2
                )
                rough_mapping.inputs[1].default_value[1] = 0.25

                if roughness_spec:
                    rough_tex.image = roughness_spec
                else:
                    rough_tex.image = img_spec

            if bump_mapping:
                bump_mapping.inputs[3].default_value[0] = size / 2
                bump_mapping.inputs[3].default_value[1] = 0.5
                bump_mapping.inputs[1].default_value[0] = 0.5 + (
                    bump_mapping.inputs[3].default_value[0] / 2
                )
                bump_mapping.inputs[1].default_value[1] = 0.25

                if albedo_spec:
                    bump_tex.image = albedo_spec
                else:
                    bump_tex.image = img_spec

            if alpha_spec:
                alpha_tex.image = alpha_spec
            else:
                if albedo_spec:
                    alpha_tex.image = albedo_spec
                else:
                    alpha_tex.image = img_spec

            if normal_tex:
                if normal_spec:
                    normal_tex.image = normal_spec

            if ao_tex:
                if ao_spec:
                    ao_tex.image = ao_spec

            if disp_mapping:
                disp_mapping.inputs[3].default_value[0] = size / 2
                disp_mapping.inputs[3].default_value[1] = 0.5
                disp_mapping.inputs[1].default_value[0] = 0.5 + (
                    disp_mapping.inputs[3].default_value[0] / 2
                )
                disp_mapping.inputs[1].default_value[1] = 0.25

                if disp_spec:
                    disp_tex.image = disp_spec
                else:
                    disp_tex.image = img_spec

        elif bpy.context.window_manager.my_toolqt.activemap == 2:

            if rough_mapping:
                rough_mapping.inputs[3].default_value[0] = size / 2
                rough_mapping.inputs[3].default_value[1] = 0.5
                rough_mapping.inputs[1].default_value[0] = 0.5 + (
                    rough_mapping.inputs[3].default_value[0] / 2
                )
                rough_mapping.inputs[1].default_value[1] = 0.25

                if roughness_spec:
                    rough_tex.image = roughness_spec
                else:
                    rough_tex.image = img_spec

        elif bpy.context.window_manager.my_toolqt.activemap == 3:

            if bump_mapping:
                bump_mapping.inputs[3].default_value[0] = size / 2
                bump_mapping.inputs[3].default_value[1] = 0.5
                bump_mapping.inputs[1].default_value[0] = 0.5 + (
                    bump_mapping.inputs[3].default_value[0] / 2
                )
                bump_mapping.inputs[1].default_value[1] = 0.25

                if albedo_spec:
                    bump_tex.image = albedo_spec
                else:
                    bump_tex.image = img_spec

        elif bpy.context.window_manager.my_toolqt.activemap == 4:

            if mask_mapping or mask_clamp:

                if mask_mapping:
                    mask_mapping.inputs[3].default_value[0] = size / 2
                    mask_mapping.inputs[3].default_value[1] = 0.5
                    mask_mapping.inputs[1].default_value[0] = 0.5 + (
                        mask_mapping.inputs[3].default_value[0] / 2
                    )
                    mask_mapping.inputs[1].default_value[1] = 0.25

                mask_tex.image = img_spec

        elif bpy.context.window_manager.my_toolqt.activemap == 5:
            if alpha_spec:
                alpha_tex.image = alpha_spec
            else:
                alpha_tex.image = img_spec

            if alpha_mapping:
                alpha_mapping.inputs[3].default_value[0] = size / 2
                alpha_mapping.inputs[3].default_value[1] = 0.5
                alpha_mapping.inputs[1].default_value[0] = 0.5 + (
                    alpha_mapping.inputs[3].default_value[0] / 2
                )
                alpha_mapping.inputs[1].default_value[1] = 0.25

        elif bpy.context.window_manager.my_toolqt.activemap == 0:
            if disp_mapping:
                disp_mapping.inputs[3].default_value[0] = size / 2
                disp_mapping.inputs[3].default_value[1] = 0.5
                disp_mapping.inputs[1].default_value[0] = 0.5 + (
                    disp_mapping.inputs[3].default_value[0] / 2
                )
                disp_mapping.inputs[1].default_value[1] = 0.25
                if disp_spec:
                    disp_tex.image = disp_spec
                else:
                    disp_tex.image = img_spec
        return {"FINISHED"}


class QT_OT_replacealpha_qt(Operator, ImportHelper):
    bl_idname = "qt.replacealpha"
    bl_label = "Replace Alpha"
    bl_options = {"PRESET", "UNDO"}
    bl_description = "Replace Alpha Masks"

    @classmethod
    def poll(self, context):
        if (
            bpy.context.window_manager.my_toolqt.blend == 0
            and bpy.context.window_manager.my_toolqt.mask == 0
        ):
            return True
        else:
            return None

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        f = self.files[0]
        img_path = os.path.join(
            dirname, f.name
        )  # get filepath properties from collection pointer
        bpy.ops.image.open(filepath=img_path)
        bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]

        width, height = img_spec.size
        size = width / height

        nodes = None
        node_tree = None

        sel = bpy.context.selected_objects
        ob = sel[0]
        mat = ob.material_slots[bpy.context.window_manager.my_toolqt.matindex].material

        for n in mat.node_tree.nodes:
            if n.name.startswith("QT_Shader"):
                nodes = n.node_tree.nodes
                node_tree = n.node_tree

        alpha_mapping = None
        alpha_tex = None
        alpha_hue_sat = None

        if nodes:
            for n in nodes:
                if n.name.startswith(
                    "QT_Alpha_Mapping_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    alpha_mapping = n
                if n.name.startswith(
                    "QT_Alpha_Tex_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    alpha_tex = n
                if n.name == "Group Output":
                    out_node = n
                if n.name.startswith(
                    "QT_Alpha_Clamp_"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    clamp = n
                if n.name.startswith(
                    "QT_Alpha_Hue_Sat"
                    + str(bpy.context.window_manager.my_toolqt.activelayer)
                ):
                    alpha_hue_sat = n

        if alpha_mapping:
            alpha_mapping.inputs[3].default_value[0] = size / 2
            alpha_mapping.inputs[3].default_value[1] = 0.5
            alpha_mapping.inputs[1].default_value[0] = 0.5 + (
                alpha_mapping.inputs[3].default_value[0] / 2
            )
            alpha_mapping.inputs[1].default_value[1] = 0.25
            alpha_tex.image = img_spec

            bpy.context.window_manager.my_toolqt.mask = 0
            bpy.context.window_manager.my_toolqt.activemap = 5

            node_tree.links.new(out_node.inputs[0], clamp.outputs[0])
            node_tree.links.new(alpha_tex.outputs[0], alpha_hue_sat.inputs[4])

        return {"FINISHED"}


class QT_OT_copymats(Operator):
    bl_idname = "qt.copymats"
    bl_label = "Copy Material"
    bl_description = "Select target objects then select source"
    bl_options = {"PRESET", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj:
            mat = obj.active_material

        if obj and mat:
            if not mat.name.startswith("QT_Preview"):
                return True

    def execute(self, context):

        # convert to geo if curve
        sel = bpy.context.selected_objects
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
                mat = ob.active_material
                if mat:
                    if mat.name.startswith("QT"):
                        ob.active_material = mat.copy()

                        for n in ob.active_material.node_tree.nodes:
                            if n.name.startswith("QT_Shader"):
                                node = n
                                name = n.name
                                nodes = n.node_tree.nodes
                                node_tree = n.node_tree

                            if n.name.startswith("QT_Out"):
                                out = n

                        original_group = node_tree
                        single_user_group = original_group.copy()

                        ob.active_material.node_tree.nodes.remove(node)

                        group_node = ob.active_material.node_tree.nodes.new(
                            "ShaderNodeGroup"
                        )
                        group_node.node_tree = single_user_group

                        group_node.location = out.location
                        group_node.location.x -= 500

                        group_node.name = name

                        ob.active_material.node_tree.links.new(
                            out.inputs["Surface"], group_node.outputs[0]
                        )

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

                    box1 = act.data.uv_layers.get("QT_UV_Box_Layer_1")
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
                        check = ob.data.uv_layers.get("QT_UV_Box_Layer_1")
                        if not check:
                            uvname = "QT_UV_Box_Layer_1"
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

                    modobj1 = None
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
                            rmod1.uv_layer = "QT_UV_Box_Layer_1"

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


class QT_OT_makeunique(Operator):
    bl_idname = "qt.makeunique"
    bl_label = "Make Material Unique"
    bl_description = "Make Unique"
    bl_options = {"PRESET", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj:
            mat = obj.active_material

        if obj and mat:
            if not mat.name.startswith("QT_Preview"):
                return True

    def execute(self, context):

        sel = bpy.context.selected_objects
        for ob in sel:
            mat = ob.active_material
            if mat.name.startswith("QT"):
                ob.active_material = mat.copy()

                for n in ob.active_material.node_tree.nodes:
                    if n.name.startswith("QT_Shader"):
                        node = n
                        name = n.name
                        nodes = n.node_tree.nodes
                        node_tree = n.node_tree

                    if n.name.startswith("QT_Out"):
                        out = n

                original_group = node_tree
                single_user_group = original_group.copy()

                ob.active_material.node_tree.nodes.remove(node)

                group_node = ob.active_material.node_tree.nodes.new("ShaderNodeGroup")
                group_node.node_tree = single_user_group

                group_node.location = out.location
                group_node.location.x -= 500

                group_node.name = name

                ob.active_material.node_tree.links.new(
                    out.inputs["Surface"], group_node.outputs[0]
                )

                if len(group_node.outputs) > 1:
                    ob.active_material.node_tree.links.new(
                        out.inputs["Displacement"], group_node.outputs[1]
                    )

        return {"FINISHED"}



class QT_OT_decal_qt(Operator, ImportHelper):
    bl_idname = "qt.decal_qt"
    bl_label = "Create Decal Material"
    bl_options = {"PRESET", "UNDO"}

    files: CollectionProperty(type=bpy.types.PropertyGroup)  # Stores properties

    def execute(self, context):

        # SHADER
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects

        bpy.context.window_manager.my_toolqt.running_qt = 0
        bpy.context.window_manager.my_toolqt.proc_uv = 0
        bpy.context.window_manager.my_toolqt.decal = 1
        bpy.context.window_manager.my_toolqt.selected = 0

        dirname = os.path.dirname(self.filepath)

        for f in self.files:
            if len(self.files) == 0:
                bpy.context.window_manager.my_toolqt.running_qt = 0
                return {"FINISHED"}
            elif len(self.files) == 1:
                f = self.files[0]
                img_path = os.path.join(dirname, f.name)
                bpy.ops.image.open(filepath=img_path)
                bpy.data.images[f.name].filepath = img_path
            elif len(self.files) > 1:
                f = self.files[0]
                for x in self.files:
                    if "albedo" in str(x.name).lower():
                        f = x
                    if "diffuse" in str(x.name).lower():
                        f = x
                    if "color" in str(x.name).lower():
                        f = x
                    if "col" in str(x.name).lower():
                        f = x
                    if "basecolor" in str(x.name).lower():
                        f = x
                    if "basecol" in str(x.name).lower():
                        f = x
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]

        ob = objects.create_decal(
            self, context, sel, bpy.context.window_manager.my_toolqt.res, img_spec
        )
        mode = "view"

        material = objects.create_material(
            self,
            context,
            img_spec,
            1,
            mode,
            bpy.context.window_manager.my_toolqt.proc_uv,
            self.files,
            dirname,
            bpy.context.window_manager.my_toolqt.decal,
            bpy.context.window_manager.my_toolqt.selected,
        )

        bpy.context.window_manager.my_toolqt.ob = ob

        # setup params
        material.name = "QT_" + material.name
        if ob.data.materials:
            ob.data.materials[0] = material
        else:
            ob.data.materials.append(material)

        # bpy.ops.object.make_links_data(type='MATERIAL')

        bpy.context.window_manager.my_toolqt.activelayer = 1
        bpy.context.window_manager.my_toolqt.activemap = 1

        # material settings
        material.blend_method = "HASHED"
        material.shadow_method = "HASHED"
        material.use_screen_refraction = True
        material.show_transparent_back = False

        bpy.ops.object.select_all(action="DESELECT")

        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob

        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # setup decal position
        if len(sel) > 0:
            pushback = max(sel[0].dimensions)
            ob.location = bpy.context.window_manager.my_toolqt.decal_hitloc
            ob.location = (
                ob.location
                - bpy.context.window_manager.my_toolqt.decal_raydir * pushback
            )

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

        filepath = None
        for mod in addon_utils.modules():
            if mod.bl_info["name"].startswith("QuickTexture"):
                filepath = mod.__file__

        dirpath = os.path.dirname(filepath)
        fullpath = os.path.join(dirpath, "QT_Presets.blend")

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
            geomod["Input_3"] = 0.01

        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name.startswith("QT_AlphaBorder")
            ]

        mat = ob.data.materials[0]
        for n in mat.node_tree.nodes:
            if n.name.startswith("QT_Shader"):
                node_tree = n.node_tree

        for n in node_tree.nodes:
            if n.name == "QT_Alpha_Clamp_1":
                node_clamp = n
            if n.name == "QT_Alpha_Bright_Contrast_1":
                node_bright = n

        original_group_alpha = bpy.data.node_groups["QT_AlphaBorder"]
        alphaborder = original_group_alpha.copy()
        alphaborder_node = node_tree.nodes.new(type="ShaderNodeGroup")
        alphaborder_node.node_tree = bpy.data.node_groups[alphaborder.name]
        alphaborder_node.location.x = node_clamp.location.x - 200
        alphaborder_node.location.y = node_clamp.location.y
        alphaborder_node.name = "QT_AlphaBorder_1"
        node_tree.links.new(node_bright.outputs[0], alphaborder_node.inputs[0])
        node_tree.links.new(alphaborder_node.outputs[0], node_clamp.inputs[0])

        for n in alphaborder_node.node_tree.nodes:
            if n.name == 'Color Attribute':
                n.layer_name = "QT_Decal_Alpha"

        # parenting
        if len(sel) > 0:
            bpy.context.view_layer.objects.active = sel[0]
            bpy.data.objects[ob.name].select_set(True)
            bpy.data.objects[sel[0].name].select_set(True)

            bpy.ops.object.parent_set(type="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")

        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob

        bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS", center="MEDIAN")

        return {"FINISHED"}


class quickDecal(bpy.types.Operator):
    """Project a QuickDecal on the selected object"""

    bl_idname = "object.quickdecal"
    bl_label = "QuickDecal"
    bl_options = {"REGISTER", "UNDO"}

    def modal(self, context, event):

        bpy.context.window_manager.my_toolqt.running_qt = 0
        if "QuickTexture" in bpy.data.collections:
            bpy.data.collections["QuickTexture"].hide_viewport = True
            bpy.data.collections["QuickTexture"].hide_render = True
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
        return {"FINISHED"}

    # INVOKE
    def invoke(self, context, event):

        # init
        self.region = context.region
        self.rv3d = context.region_data
        self.region3D = bpy.context.space_data.region_3d

        bpy.context.window_manager.my_toolqt.running_qt = 1
        sel = bpy.context.selected_objects

        bpy.context.window_manager.my_toolqt.activemap = 1
        bpy.context.window_manager.my_toolqt.activelayer = 1

        ob = None
        ob2 = None

        if len(sel) > 0:
            for ob in sel:
                if ob.type not in ["CURVE", "META", "MESH"]:
                    return {"FINISHED"}

                if ob.type in ["CURVE", "META"]:
                    bpy.ops.object.convert(target="MESH")
                    sel = bpy.context.selected_objects

            ob = sel[0]
            ob2 = bpy.context.view_layer.objects.active
            bpy.context.window_manager.my_toolqt.ob = sel[0]
            bpy.context.window_manager.my_toolqt.selected = 1
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        else:
            bpy.context.window_manager.my_toolqt.selected = 0

        # nodes
        self.mat = None
        self.tex_coord = None
        self.nodes = None
        self.node_tree = None
        self.out_node = None
        self.out_material = None
        self.group_node = None
        self.core_shader = None
        self.final_node = None
        self.diffuse_mapping = None
        self.rough_mapping = None
        self.bump_mapping = None
        self.mask_mapping = None
        self.diffuse_tex = None
        self.diffuse_hue_sat = None
        self.diffuse_bright_contrast = None
        self.rough_tex = None
        self.rough_bright_contrast = None
        self.rough_invert = None
        self.rough_hue_sat = None
        self.bump_tex = None
        self.bump_bright_contrast = None
        self.bump_bump = None
        self.bump_strength = None
        self.bump_layer = None
        self.bump_invert = None
        self.bump_hue_sat = None
        self.mask_tex = None
        self.mask_bright_contrast = None
        self.mask_invert = None
        self.mask_hue_sat = None
        self.mask_clamp = None
        self.roughness_clamp = None
        self.bump_clamp = None

        self.normal_tex = None
        self.normal_strength = None

        self.alpha_type = 1

        self.alpha_tex = None
        self.alpha_mapping = None
        self.alpha_bright_contrast = None
        self.alpha_invert = None
        self.alpha_hue_sat = None
        self.alpha_clamp = None

        self.ao_tex = None
        self.ao_multiply = None

        self.blend_add = None
        self.blend_xyz = None
        self.blend_math = None
        self.blend_power = None
        self.blend_clamp = None
        self.blend_mix = None
        self.blend_noise = None
        self.blend_bright_contrast = None

        self.prev_blend_node = None

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
                if collection.hide_viewport == True:
                    collection.hide_viewport = False

        # view
        self.view_vector = Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
        self.window_active, self.zoomlevel = utils.window_info(
            context,
            event,
            bpy.context.preferences.addons[__package__].preferences.window_buffer,
        )
        self.regX = bpy.context.region.width
        self.regY = bpy.context.region.height

        # shading style
        areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
        self.viewlens = 50 / (areas[0].spaces[0].lens)

        # hotkeys
        self.coord = Vector((event.mouse_region_x, event.mouse_region_y))
        self.coord_firstclick = Vector((0, 0))
        self.coord_lastclick = Vector((0, 0))
        self.coord_hotkeyclick = Vector((0, 0))
        self.avg_2d = Vector((0, 0))

        self.mouse_sample_x = []
        self.mouse_sample_y = []
        self.hotkey_press = []

        self.lmb = False
        self.rmb = False
        self.mmb = False

        self.alt = False
        self.ctrl = False
        self.shift = False

        self.a = False
        self.g = False
        self.s = False
        self.r = False
        self.l = False
        self.e = False
        self.shifth = False
        self.alts = False
        self.shifts = False
        self.shiftb = False
        self.shiftn = False
        self.ctrli = False
        self.h = False
        self.v = False
        self.c = False
        self.o = False
        self.x = False

        args = (self, context)
        wm = context.window_manager
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_quickTexture, args, "WINDOW", "POST_PIXEL"
        )
        context.window_manager.modal_handler_add(self)

        # setup projection
        if len(sel) > 0:
            coord = event.mouse_region_x, event.mouse_region_y
            hitlocation, hitnormal, hitindex, hitobject = utils.ray_cast(
                self.region, self.rv3d, coord, context
            )
            if hitobject:
                bpy.context.window_manager.my_toolqt.decal_hitloc = hitlocation
            else:
                bpy.context.window_manager.my_toolqt.decal_hitloc = Vector((0, 0, 0))
        bpy.context.window_manager.my_toolqt.decal_raydir = Vector(
            (self.rv3d.perspective_matrix[2][0:3])
        ).normalized()

        bpy.ops.qt.decal_qt("INVOKE_DEFAULT")

        return {"RUNNING_MODAL"}


class bakeTextures(Operator):
    bl_idname = "wm.baketextures"
    bl_label = "Bake Textures"
    bl_description = "Bake Textures"
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

        uvmap = None
        if bpy.context.window_manager.my_toolqt.forceprocedural:
            if len(obj.data.uv_layers) > 0:
                for layer in obj.data.uv_layers:
                    if layer.name.startswith("QT_SmartUVMap"):
                        uvmap = layer

        if obj and len(obj.data.materials) > 0:

            node_tree = None
            self._mat = obj.data.materials[0]
            nodes = self._mat.node_tree.nodes
            node_tree = self._mat.node_tree
            maplist = ["DIFFUSE", "ROUGHNESS", "NORMAL"]

            for i in range(len(maplist)):
                sel = bpy.context.selected_objects
                if len(sel) > 1:
                    bpy.context.scene.render.bake.use_selected_to_active = True

                # prepare bake node
                bake_spec = (
                    bpy.context.window_manager.my_toolqt.bakename
                    + "_"
                    + maplist[i]
                    + ".png"
                )
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
                if bpy.context.window_manager.my_toolqt.forceprocedural:
                    uv_node = node_tree.nodes.new("ShaderNodeUVMap")
                    uv_node.uv_map = uvmap.name
                    node_tree.links.new(uv_node.outputs[0], bake_node.inputs[0])
                else:
                    uv_node = None

                # multi material
                for x in range(len(obj.data.materials)):
                    if x > 1:
                        img_node = obj.data.materials[x].node_tree.nodes.new(
                            "ShaderNodeTexImage"
                        )
                        img_node.image = bake_image
                        img_node.select = True
                        obj.data.materials[x].node_tree.nodes.active = img_node
                        img_node.show_texture = True

                baketype = maplist[i]
                if i == 0:
                    bpy.context.scene.render.bake.use_pass_indirect = False
                    bpy.context.scene.render.bake.use_pass_direct = False
                elif i == 2:
                    bake_node.image.colorspace_settings.name = "Non-Color"

                # bake
                while bpy.ops.object.bake("INVOKE_DEFAULT", type=baketype) != {
                    "RUNNING_MODAL"
                }:
                    yield 1
                while not bake_image.is_dirty:
                    yield 1

                bake_image.save_render(filepath=bake_path)

                bpy.data.images.remove(bake_image)

                node_tree.nodes.remove(bake_node)

                if uv_node:
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

                # remove other UV layers
                if bpy.context.window_manager.my_toolqt.forceprocedural:
                    if len(obj.data.uv_layers) > 0:
                        for layer in obj.data.uv_layers:
                            if layer.name.startswith("QT_SmartUVMap"):
                                obj.data.uv_layers[layer.name].active = True
                                obj.data.uv_layers[layer.name].active_render = True

                uvs = [
                    uv for uv in obj.data.uv_layers if uv != obj.data.uv_layers.active
                ]
                while uvs:
                    obj.data.uv_layers.remove(uvs.pop())

                # remove other mats
                for i in range(len(obj.material_slots)):
                    bpy.ops.object.material_slot_remove({"object": obj})
                obj.data.materials.append(self._mat)

                # remove old nodes
                node_tree = self._mat.node_tree

                for n in node_tree.nodes:
                    if n.name.startswith("QT_Output"):
                        out_node = n
                    else:
                        node_tree.nodes.remove(n)

                # recreate node setup with baked textures
                core_shader = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
                core_shader.inputs[19].default_value = (1, 1, 1, 1)
                core_shader.inputs[20].default_value = 0

                node_tree.links.new(core_shader.outputs[0], out_node.inputs[0])

                # diffuse
                bake_spec = (
                    bpy.context.window_manager.my_toolqt.bakename
                    + "_"
                    + "DIFFUSE"
                    + ".png"
                )
                bake_path = os.path.join(
                    bpy.context.window_manager.my_toolqt.bakepath, bake_spec
                )

                bpy.ops.image.open(filepath=bake_path)
                bpy.data.images[bake_spec].filepath = bake_path
                diffuse_spec = bpy.data.images[bake_spec]

                diffuse_tex = node_tree.nodes.new("ShaderNodeTexImage")
                diffuse_tex.image = diffuse_spec
                diffuse_tex.show_texture = True

                node_tree.links.new(diffuse_tex.outputs[0], core_shader.inputs[0])

                # roughness
                bake_spec = (
                    bpy.context.window_manager.my_toolqt.bakename
                    + "_"
                    + "ROUGHNESS"
                    + ".png"
                )
                bake_path = os.path.join(
                    bpy.context.window_manager.my_toolqt.bakepath, bake_spec
                )

                bpy.ops.image.open(filepath=bake_path)
                bpy.data.images[bake_spec].filepath = bake_path
                rough_spec = bpy.data.images[bake_spec]

                rough_tex = node_tree.nodes.new("ShaderNodeTexImage")
                rough_tex.image = rough_spec
                rough_tex.show_texture = True

                rough_tex.image.colorspace_settings.name = "Non-Color"

                node_tree.links.new(rough_tex.outputs[0], core_shader.inputs[9])

                # normal
                bake_spec = (
                    bpy.context.window_manager.my_toolqt.bakename
                    + "_"
                    + "NORMAL"
                    + ".png"
                )
                bake_path = os.path.join(
                    bpy.context.window_manager.my_toolqt.bakepath, bake_spec
                )

                bpy.ops.image.open(filepath=bake_path)
                bpy.data.images[bake_spec].filepath = bake_path
                normal_spec = bpy.data.images[bake_spec]

                normal_tex = node_tree.nodes.new("ShaderNodeTexImage")
                normal_tex.image = normal_spec
                normal_tex.show_texture = True

                normal_tex.image.colorspace_settings.name = "Non-Color"

                normal_strength = node_tree.nodes.new("ShaderNodeNormalMap")
                node_tree.links.new(normal_tex.outputs[0], normal_strength.inputs[1])
                node_tree.links.new(normal_strength.outputs[0], core_shader.inputs[22])

                if bpy.context.window_manager.my_toolqt.forceprocedural:
                    uv_node = node_tree.nodes.new("ShaderNodeUVMap")
                    uv_node.uv_map = "QT_SmartUVMap"
                    node_tree.links.new(uv_node.outputs[0], diffuse_tex.inputs[0])
                    node_tree.links.new(uv_node.outputs[0], rough_tex.inputs[0])
                    node_tree.links.new(uv_node.outputs[0], normal_tex.inputs[0])

                objects.auto_align_nodes(node_tree)

                context.scene.render.engine = self._render
                bpy.context.scene.cycles.samples = self._samples
                bpy.context.window_manager.my_toolqt.forceprocedural = 0

                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context: bpy.context):

        if bpy.data.is_saved:
            abs_filepath = bpy.path.abspath('//')
            if not os.path.isdir(str(abs_filepath+"textures")):
                os.mkdir(str(abs_filepath+"textures"))


        if (
            not context.active_object.select_get()
            or not context.active_object.type == "MESH"
        ):
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
                self.report({"WARNING"}, "No valid file path")
                return {"FINISHED"}

        # unique mat first
        if bpy.context.window_manager.my_toolqt.save_original_mat:
            sel = bpy.context.selected_objects
            for ob in sel:
                mat = ob.active_material
                if mat.name.startswith("QT"):
                    ob.active_material = mat.copy()

                    for n in ob.active_material.node_tree.nodes:
                        if n.name.startswith("QT_Shader"):
                            node = n
                            name = n.name
                            nodes = n.node_tree.nodes
                            node_tree = n.node_tree

                        if n.name.startswith("QT_Out"):
                            out = n

                    original_group = node_tree
                    single_user_group = original_group.copy()

                    ob.active_material.node_tree.nodes.remove(node)

                    group_node = ob.active_material.node_tree.nodes.new(
                        "ShaderNodeGroup"
                    )
                    group_node.node_tree = single_user_group

                    group_node.location = out.location
                    group_node.location.x -= 500

                    group_node.name = name

                    ob.active_material.node_tree.links.new(
                        out.inputs["Surface"], group_node.outputs[0]
                    )

        # store settings
        self._samples = bpy.context.scene.cycles.samples
        self._render = context.scene.render.engine

        # settings
        if context.scene.render.engine != "CYCLES":
            context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.samples = bpy.context.window_manager.my_toolqt.samples

        # prepare
        bpy.ops.object.convert(target="MESH")

        if bpy.context.window_manager.my_toolqt.forceprocedural:
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


class previewTextures(Operator):
    bl_idname = "wm.previewtextures"
    bl_label = "Preview AO / Cavity Toggle"
    bl_description = "Preview AO and Cavity Textures Toggle"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context: bpy.context):

        if (
            not context.active_object.select_get()
            or not context.active_object.type == "MESH"
        ):
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


class bakePreviewTextures(Operator):
    bl_idname = "wm.bakepreviewtextures"
    bl_label = "Bake AO / Cavity Textures"
    bl_description = "Bake AO / Cavity Textures only"
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
            nodes = self._mat.node_tree.nodes
            node_tree = self._mat.node_tree
            maplist = ["AO", "CAVITY"]

            for i in range(len(maplist)):

                bake_spec = (
                    bpy.context.window_manager.my_toolqt.bakename
                    + "_"
                    + maplist[i]
                    + ".png"
                )
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
                    if n.name == "Shader_Cavity":
                        cav = n
                    if n.name == "Shader_AO":
                        ao = n
                    if n.name == "Material Output":
                        out = n
                    if n.name == "Vector Math":
                        combined = n

                if i == 0:
                    node_tree.links.new(ao.outputs[0], out.inputs[0])
                else:
                    node_tree.links.new(cav.outputs[0], out.inputs[0])

                node_tree.links.new(uv_node.outputs[0], bake_node.inputs[0])

                while bpy.ops.object.bake("INVOKE_DEFAULT", type='EMIT') != {
                    "RUNNING_MODAL"
                }:
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

        uv = 0
        uvmap = None
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


class quicktexture_uv(Operator):
    bl_idname = "object.quicktextureuv"
    bl_label = "QuickTexture (UV)"
    bl_description = "QuickTexture Use UV's"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.forceprocedural = 0
        bpy.ops.object.quicktexture("INVOKE_DEFAULT")

        return {"FINISHED"}


class quicktexture_view(Operator):
    bl_idname = "object.quicktextureview"
    bl_label = "QuickTexture Procedural (View)"
    bl_description = "QuickTexture Procedural From View"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.forceprocedural = 1
        bpy.context.window_manager.my_toolqt.mode = "view"
        bpy.ops.object.quicktexture("INVOKE_DEFAULT")

        return {"FINISHED"}


class quicktexture_box(Operator):
    bl_idname = "object.quicktexturebox"
    bl_label = "QuickTexture Procedural (Box)"
    bl_description = "QuickTexture Procedural Box"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):

        bpy.context.window_manager.my_toolqt.forceprocedural = 1
        bpy.context.window_manager.my_toolqt.mode = "box"
        bpy.ops.object.quicktexture("INVOKE_DEFAULT")

        return {"FINISHED"}


class photomodelingplane(Operator):
    bl_idname = "object.photomodelingplane"
    bl_label = "Photomodeling Plane"
    bl_description = "Make a Photomodeling Plane"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):

        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.window_manager.my_toolqt.forceprocedural = 1
        bpy.context.window_manager.my_toolqt.mode = "view"
        bpy.ops.object.quicktexture("INVOKE_DEFAULT")

        return {"FINISHED"}


class photomodelingbox(Operator):
    bl_idname = "object.photomodelingbox"
    bl_label = "Photomodeling Box"
    bl_description = "Make a Photomodeling Box"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):

        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.window_manager.my_toolqt.forceprocedural = 1
        bpy.context.window_manager.my_toolqt.mode = "box"
        bpy.ops.object.quicktexture("INVOKE_DEFAULT")

        return {"FINISHED"}


class photomodelingapply(Operator):
    bl_idname = "object.photomodelingapply"
    bl_label = "Freeze Photomodel"
    bl_description = "Freeze Photomodel"
    bl_options = {"PRESET", "UNDO"}

    def execute(self, context):

        bpy.ops.object.convert(target='MESH')
        return {"FINISHED"}
