import bpy
import os
from bpy.props import FloatProperty, IntProperty, BoolProperty, StringProperty, FloatVectorProperty, PointerProperty, CollectionProperty
import math
import bmesh
from bpy_extras import view3d_utils
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import *
from math import *
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       Macro
                       )
import mathutils
import bpy_extras
from bpy_extras.view3d_utils import region_2d_to_location_3d
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras import view3d_utils
from mathutils.geometry import intersect_line_plane
from mathutils.geometry import intersect_line_line
from mathutils.geometry import intersect_line_line_2d
import traceback

from bgl import *
from bpy_extras.io_utils import ImportHelper

import numpy
import random

import addon_utils

from . import utils
from . import objects
from . import maths

class MyPropertiesQT(bpy.types.PropertyGroup):

    ob: PointerProperty(
        type=bpy.types.Object
        )    
      
    running_qt: IntProperty(
        name="running_qt",
        description="running_qt",
        default = 0
        )    

    res: IntProperty(
        name="res",
        description="Resolution of Decal Projection",
        default = 2,
        min = 1,
        max = 4
        ) 

    selected: BoolProperty(
        name="selected",
        description="selected",
        default = 0
        )  

    padding: FloatProperty(
        name="padding",
        description="Padding for Decal Projection",
        default = 0.02,
        min = 0.0001,
        max = 0.1
        )  

    decal: BoolProperty(
        name="decal",
        description="decal",
        default = 0
        )  

    use_uv: BoolProperty(
        name="use_uv",
        description="use_uv",
        default = 0
        ) 

    proc_uv: BoolProperty(
        name="proc_uv",
        description="proc_uv",
        default = 0
        ) 

    blend: BoolProperty(
        name="blend",
        description="blend",
        default = 0
        )  

    mask: BoolProperty(
        name="mask",
        description="mask",
        default = 0
        )

    mode: bpy.props.EnumProperty(
        items=[
            ('view', 'VIEW', 'View Projection', 'view', 0),
            ('box', 'BOX', 'Box Projection', 'box', 1)
        ],
        default='box'
    )
    
    filepath: StringProperty(
        name="filepath",
        description="filepath",
        default = "none"
        )    

    activemap: IntProperty(
        name="activemap",
        description="activemap",
        default = 1,
        min = 1,
        max = 5
        )    
    
    activelayer: IntProperty(
        name="activelayer",
        description="activelayer",
        default = 1,
        min = 1,
        max = 5
        )
        
    metal: BoolProperty(
        name="metal",
        description="metal",
        default = 0
        )    

    bump: FloatProperty(
        name="bump",
        description="bump",
        default = 0.1
        )  

    normal: FloatProperty(
        name="normal",
        description="normal",
        default = 1
        )  

    spec: FloatProperty(
        name="spec",
        description="spec",
        default = 0.5
        )  

    sss: FloatProperty(
        name="sss",
        description="ss",
        default = 0
        )  

    emit: FloatProperty(
        name="emit",
        description="emit",
        default = 0
        )  

    ao: FloatProperty(
        name="ao",
        description="ao",
        default = 0
        )

    diffuse_hue: FloatProperty(
        name="hue",
        description="hue",
        default = 0.5
        )  

    diffuse_val: FloatProperty(
        name="val",
        description="val",
        default = 1,
        min = -30,
        max = 30
        )  

    diffuse_sat: FloatProperty(
        name="sat",
        description="sat",
        default = 1,
        min = -30,
        max = 30
        )

    rough_val: FloatProperty(
        name="roughness_val",
        description="roughness_val",
        default = 1,
        min = -30,
        max = 30
        ) 

    rough_contrast: FloatProperty(
        name="roughness_contrast",
        description="roughness_contrast",
        default = 1,
        min = -30,
        max = 30
        )   

    rough_hue_sat: FloatProperty(
        name="rough_hue_sat",
        description="rough_hue_sat",
        default = 1
        )  

    bump_val: FloatProperty(
        name="bump_val",
        description="bump_val",
        default = 1
        )  

    bump_contrast: FloatProperty(
        name="bump_contrast",
        description="bump_contrast",
        default = 1,
        min = -30,
        max = 30
        )  

    bump_hue_sat: FloatProperty(
        name="bump_hue_sat",
        description="bump_hue_sat",
        default = 1
        )  

    mask_val: FloatProperty(
        name="mask_val",
        description="mask_val",
        default = 1
        )  

    mask_contrast: FloatProperty(
        name="mask_contrast",
        description="mask_contrast",
        default = 1,
        min = -30,
        max = 30
        )  

    mask_hue_sat: FloatProperty(
        name="mask_hue_sat",
        description="mask_hue_sat",
        default = 1
        )  

    alpha_contrast: FloatProperty(
        name="alpha_contrast",
        description="alpha_contrast",
        default = 1,
        min = -30,
        max = 30
        )  

    alpha_hue_sat: FloatProperty(
        name="alpha_hue_sat",
        description="alpha_hue_sat",
        default = 1
        )  

    opacity: FloatProperty(
        name="opacity",
        description="opacity",
        default = 1
        )  

    blendsmoothing: FloatProperty(
        name="blendsmoothing",
        description="blendsmoothing",
        default = 0.001,
        min = 0.001,
        max = 5
        )  

    blendvalue: FloatProperty(
        name="blendvalue",
        description="blendvalue",
        default = 0,
        min = 0,
        max = 1
        )  
    
    blendcontrast: FloatProperty(
        name="blendcontrast",
        description="blendcontrast",
        default = 0,
        min = 0,
        max = 1
        )  

    noiseroughness: FloatProperty(
        name="noiseroughness",
        description="noiseroughness",
        default = 0.5,
        min = 0,
        max = 1
        )  

    noisescale: FloatProperty(
        name="noisescale",
        description="noisescale",
        default = 0,
        min = 0,
        max = 30
        )  
    
    noisedetail: FloatProperty(
        name="noisedetail",
        description="noisedetail",
        default = 2,
        min = 0,
        max = 30
        )  

    noisedistortion: FloatProperty(
        name="noisedistortion",
        description="noisedistortion",
        default = 0,
        min = 0,
        max = 30
        )  

    makeunique: BoolProperty(
        name="makeunique",
        description="Make the material unique after copying",
        default = 1
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
        row.label(text="Ctrl + T = Quick Texture")
        row = box.row()    
        row.label(text="Ctrl + Shift + D = Quick Decal")
        row = box.row()   
        row.label(text="Shift + A = Adjust Decal")                
        row = box.row() 
        row.prop(bpy.context.window_manager.my_toolqt, "res", text="Decal Resolution", slider=True)
        row = box.row() 
        row.prop(bpy.context.window_manager.my_toolqt, "padding", text="Decal Padding", slider=True)
        box = layout.box()
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
        row.label(text="U = UV / Box Mapping Toggle")
        row = box.row()    
        row.label(text="Alt C = Clip / Repeat Toggle")
        row = box.row()    
        row.label(text="Alt A = Color / Alpha Toggle")
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
        row.label(text="4 = Mask (If Exists)")
        row = box.row()    
        row.label(text="5 = Alpha")
        row = box.row()    
        row.label(text="Ctrl I = Invert Map")
        row = box.row()    
        row.label(text="Alt R = Replace Map")
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
        row.label(text="P = Reproject View Layer")
        row = box.row()    
        row.label(text="Del or Ctrl + Backspace = Delete Layer")
        box = layout.box()
        row = box.row()    
        row.label(text="MASKS")
        row = box.row()    
        row.label(text="Ctrl + A = Alpha Texture Mask")
        row = box.row()    
        row.label(text="Ctrl + M = Mask By Texture")
        row = box.row()    
        row.label(text="Alt + H = Mask By Depth Map")
        row = box.row()    
        row.label(text="Ctrl + H = Mask By Height")
        row = box.row()    
        row.label(text="Ctrl + N = Mask By Normal")
        row = box.row()    
        row.label(text="Backspace = Delete Mask")
        box = layout.box()
        row = box.row()    
        row.prop(bpy.context.window_manager.my_toolqt, 'mode', expand=True)
        row = box.row()    
        row.operator(QT_OT_copymats.bl_idname)
        row = box.row()
        row.prop(bpy.context.window_manager.my_toolqt, 'makeunique', text='Unlink Material After Copy')
        row = box.row()  
        row.operator(QT_OT_makeunique.bl_idname)
  
def draw_quickTexture(self, context):
    font_id = 0  # XXX, need to find out how best to get this.
    region = context.region
    bgl.glEnable(bgl.GL_BLEND)

    if bpy.context.window_manager.my_toolqt.running_qt and self.core_shader:
    
# TEXT
        font_id = 0

        if bpy.context.window_manager.my_toolqt.decal:
            text = "QUICK DECAL"
        else:
            text = "QUICK TEXTURE"

        dpi = int(round(bpy.context.preferences.system.ui_scale, 1))
        
        height = blf.dimensions(font_id, text)[1] * 5
        space = (height * 0.5 )
            
        dim_x = blf.dimensions(font_id, text)[0]/2
        blf.position(font_id, self.regX/2 - dim_x, self.regY-space, 0)
        blf.size(font_id, bpy.context.preferences.addons[__package__].preferences.text_size, 72 * dpi)
        blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
        blf.draw(font_id, text) 
        
        text3 = "Active Layer: " + str(self.core_shader.label)
        dim_x4 = blf.dimensions(font_id, text3)[0]
        blf.position(font_id, self.regX/2 - dim_x4/2, space, 0)
        blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
        blf.draw(font_id, text3)   
        
        activemap = 'Combined'
        if bpy.context.window_manager.my_toolqt.activemap == 1:
            activemap = 'Combined'
        elif bpy.context.window_manager.my_toolqt.activemap == 2:
            activemap = 'Roughness'
        elif bpy.context.window_manager.my_toolqt.activemap == 3:
            activemap = 'Bump'
        elif bpy.context.window_manager.my_toolqt.activemap == 4:
            activemap = 'Mask'
        elif bpy.context.window_manager.my_toolqt.activemap == 5:
            activemap = 'Alpha'

        if bpy.context.window_manager.my_toolqt.blend: 
            activemap = 'Blend'

        if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
            text1 = "Active Map: " + activemap
            textLength1 = "Active Map" + activemap
            dim_x3 = blf.dimensions(font_id, text1)[0]
            blf.position(font_id, self.regX/2 - dim_x3/2, space * 2, 0)
            blf.size(font_id, bpy.context.preferences.addons[__package__].preferences.text_size, 72 * dpi)
            blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
            blf.draw(font_id, text1)   
     
            text1 = '(H) Smoothing: ' + str(round(bpy.context.window_manager.my_toolqt.blendsmoothing, 2))         
            text2 = '(V) Value: ' + str(round(bpy.context.window_manager.my_toolqt.blendvalue, 2))
            text3 = '(C) Contrast: ' + str(round(bpy.context.window_manager.my_toolqt.blendcontrast, 2))
                
            dim_x = blf.dimensions(font_id, text1)[0]+30
            blf.position(font_id, self.regX-dim_x, space * 3, 0)
            if self.h:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text1)

            blf.position(font_id, self.regX-dim_x, space * 2, 0)
            if self.v:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text2)

            blf.position(font_id, self.regX-dim_x, space, 0)
            if self.c:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text3)

            text = "(O) Noise Roughness: " +  str(round(bpy.context.window_manager.my_toolqt.noiseroughness, 2))         
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 4, 0)
            if self.o:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)
                        
            text = "(SHIFT B) Noise Detail: " + str(round( bpy.context.window_manager.my_toolqt.noisedetail, 3))
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space, 0)
            if self.shiftb:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)

            text = "(SHIFT H) Noise Scale: " + str(round( bpy.context.window_manager.my_toolqt.noisescale, 3))
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 2, 0)
            if self.shifth:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)
            
            text = "(E) Noise Distortion: " + str(round(bpy.context.window_manager.my_toolqt.noisedistortion, 3))
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 3, 0)
            if self.e:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)

        else:
            if self.diffuse_tex.projection == 'FLAT':
                uvmode = 'Flat'
            else:
                uvmode = 'Box'

            text1 = "UV Mode: " + uvmode
            textLength1 = "UV Mode" + uvmode
            dim_x3 = blf.dimensions(font_id, text1)[0]
            blf.position(font_id, self.regX/2 - dim_x3/2, space * 3, 0)
            blf.size(font_id, bpy.context.preferences.addons[__package__].preferences.text_size, 72 * dpi)
            blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
            blf.draw(font_id, text1)

            text1 = "Active Map: " + activemap
            textLength1 = "Active Map" + activemap
            dim_x3 = blf.dimensions(font_id, text1)[0]
            blf.position(font_id, self.regX/2 - dim_x3/2, space * 2, 0)
            blf.size(font_id, bpy.context.preferences.addons[__package__].preferences.text_size, 72 * dpi)
            blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
            blf.draw(font_id, text1)   

            # combined
            if bpy.context.window_manager.my_toolqt.activemap == 1:        
                text1 = '(H) Hue: ' + str(round(bpy.context.window_manager.my_toolqt.diffuse_hue, 2))         
                text2 = '(V) Value: ' + str(round(bpy.context.window_manager.my_toolqt.diffuse_val, 2))
                text3 = '(C) Saturation: ' + str(round(bpy.context.window_manager.my_toolqt.diffuse_sat, 2))

            # roughness
            if bpy.context.window_manager.my_toolqt.activemap == 2:        
                text1 = '(Ctrl I) Invert'
                text2 = '(V) Value: ' + str(round(bpy.context.window_manager.my_toolqt.rough_hue_sat, 2))
                text3 = '(C) Contrast: ' + str(round(bpy.context.window_manager.my_toolqt.rough_contrast, 2))

            # bump
            if bpy.context.window_manager.my_toolqt.activemap == 3:        
                text1 = '(Ctrl I) Invert'
                text2 = '(V) Value: ' + str(round(bpy.context.window_manager.my_toolqt.bump_hue_sat, 2))
                text3 = '(C) Contrast: ' + str(round(bpy.context.window_manager.my_toolqt.bump_contrast, 2))

            # mask
            if bpy.context.window_manager.my_toolqt.activemap == 4:        
                text1 = '(Ctrl I) Invert'
                text2 = '(V) Value: ' + str(round(bpy.context.window_manager.my_toolqt.mask_hue_sat, 2))
                text3 = '(C) Contrast: ' + str(round(bpy.context.window_manager.my_toolqt.mask_contrast, 2))

            # mask
            if bpy.context.window_manager.my_toolqt.activemap == 5:        
                text1 = '(Ctrl I) Invert'
                text2 = '(V) Value: ' + str(round(bpy.context.window_manager.my_toolqt.alpha_hue_sat, 2))
                text3 = '(C) Contrast: ' + str(round(bpy.context.window_manager.my_toolqt.alpha_contrast, 2))
                
            dim_x = blf.dimensions(font_id, text3)[0]+30
            blf.position(font_id, self.regX-dim_x, space * 3, 0)
            blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
            blf.draw(font_id, text1)

            blf.position(font_id, self.regX-dim_x, space * 2, 0)
            blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
            blf.draw(font_id, text2)

            blf.position(font_id, self.regX-dim_x, space, 0)
            blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
            blf.draw(font_id, text3)
            
            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                opac = str(round(bpy.context.window_manager.my_toolqt.opacity, 2))
            else:
                opac = 'N/A'

            text = "(O) Opacity: " + opac
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 8, 0)
            if self.o:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)
            
            if bpy.context.window_manager.my_toolqt.metal:
                label = 'On'
            else:
                label = 'Off'
                
            text = "(M) Metalness: " + label
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 7, 0)
            if bpy.context.window_manager.my_toolqt.metal:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)
            
            text = "(L) Subsurface: " + str(round(bpy.context.window_manager.my_toolqt.sss, 3))
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 6, 0)
            if self.l:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])
            blf.draw(font_id, text)

            text = "(E) Emission: " + str(round(bpy.context.window_manager.my_toolqt.emit, 3))
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 5, 0)
            if self.e:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)
            
            if self.ao_tex:
                ao =  str(round(bpy.context.window_manager.my_toolqt.ao, 2))
            else:
                ao = 'N/A'

            text = "(A) AO Strength: " + ao
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 4, 0)
            if self.a:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)
            
            text = "(SHIFT B) Bump Strength: " + str(round( bpy.context.window_manager.my_toolqt.bump, 3))
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 3, 0)
            if self.shiftb:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)

            if self.normal_tex:
                norm = str(round(bpy.context.window_manager.my_toolqt.normal, 3))
            else:
                norm = 'N/A'

            text = "(SHIFT N) Normal Strength: " + norm
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space * 2, 0)
            if self.shiftn:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)

            text = "(SHIFT H) Specular Strength: " + str(round( bpy.context.window_manager.my_toolqt.spec, 3))
            dim_x = blf.dimensions(font_id, text)[0]+30
            blf.position(font_id, 15, space, 0)
            if self.shifth:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_accent[0], bpy.context.preferences.addons[__package__].preferences.col_accent[1], bpy.context.preferences.addons[__package__].preferences.col_accent[2], bpy.context.preferences.addons[__package__].preferences.col_accent[3])
            else:
                blf.color(font_id, bpy.context.preferences.addons[__package__].preferences.col_primary[0], bpy.context.preferences.addons[__package__].preferences.col_primary[1], bpy.context.preferences.addons[__package__].preferences.col_primary[2], bpy.context.preferences.addons[__package__].preferences.col_primary[3])        
            blf.draw(font_id, text)
                
class quickTexture(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "object.quicktexture"
    bl_label = "QuickTexture"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):

        if event.type.startswith('NDOF'):
            return {'PASS_THROUGH'}

        # alt nav
        if bpy.context.preferences.addons[__package__].preferences.alt_nav:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                if event.alt:
                    self.alt = 0
                    return {'PASS_THROUGH'} 
            elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                if event.alt:
                    self.alt = 0
                    return {'PASS_THROUGH'} 
        
        # get vars
        if bpy.context.window_manager.my_toolqt.selected:
            if bpy.context.window_manager.my_toolqt.ob:
                if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 0:
                    self.mat = bpy.context.window_manager.my_toolqt.ob.material_slots[0].material
                    if self.mat:                    
                        for n in self.mat.node_tree.nodes:
                            if n.name == 'QT_Output':
                                self.out_material = n

                            if n.name.startswith('QT_Shader'):
                                self.nodes = n.node_tree.nodes
                                self.node_tree = n.node_tree

                            # blend only
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name.startswith('QT_Blend'):
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                        if self.nodes:
                            for n in self.nodes:
                                # ACTIVE LAYER                            
                                if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.core_shader = n
                                    self.final_node = n
                                    
                                if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.final_node = n
                                    
                                if n.name == 'Group Output':
                                    self.out_node = n

                                # coord
                                if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.tex_coord = n

                                # normal
                                if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_tex = n
                                if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_strength = n
                                    bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                                # mapping                                 
                                if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_mapping = n
                                if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_mapping = n
                                if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_mapping = n

                                # clamps
                                if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_clamp = n
                                if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.roughness_clamp = n
                                if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_clamp = n

                                # textures
                                if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_tex = n
                                if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_bright_contrast = n

                                if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_tex = n
                                if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_color_ramp = n
                                if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_invert = n
                                if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                                if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_tex = n
                                if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_color_ramp = n
                                if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bump = n
                                    bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                                if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_invert = n
                                if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                                # masks
                                if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_tex = n
                                if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_color_ramp = n
                                if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_invert = n
                                if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_mapping = n

                                # alpha
                                if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_mapping = n
                                if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_tex = n
                                if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_color_ramp = n
                                if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_invert = n
                                if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_clamp = n

                                # ao
                                if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_tex = n
                                if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_multiply = n
                                    bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                                # height
                                if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_power = n
                                    bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value
                                if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                
                                # blend
                                if bpy.context.window_manager.my_toolqt.blend:
                                    if n.name == ('QT_Blend_Add'):
                                        self.blend_add = n
                                    if n.name == ('QT_Blend_XYZ'):
                                        self.blend_xyz = n
                                    if n.name == ('QT_Blend_Math'):
                                        self.blend_math = n
                                    if n.name == ('QT_Blend_Power'):
                                        self.blend_power = n
                                    if n.name == ('QT_Blend_Clamp'):
                                        self.blend_clamp = n
                                    if n.name == ('QT_Blend_Mix'):
                                        self.blend_mix = n
                                    if n.name == ('QT_Blend_Noise'):
                                        self.blend_noise = n
                                        bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                        bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                        bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                    if n.name == ('QT_Blend_Bright_Contrast'):
                                        self.blend_bright_contrast = n
                                        bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value
                                    if n.name == 'QT_Blend_Mix':
                                        self.final_node = n
                                        self.core_shader = n      
                                                                                             
        try:
            self.regX = context.region.width
            self.regY = context.region.height
            self.view_vector = Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
            context.area.tag_redraw()

            if event.type == 'MOUSEMOVE':
                self.coord = Vector((event.mouse_region_x, event.mouse_region_y))                    
                    
            # pass through if not in proper window area
            self.window_active, self.zoomlevel = utils.window_info(context, event, bpy.context.preferences.addons[__package__].preferences.window_buffer)

            if self.window_active == 0:
                return {'PASS_THROUGH'}

            if bpy.context.window_manager.my_toolqt.running_qt == 0:                
                if self.nodes is not None:
                    for n in self.nodes:
                        if n.name.startswith('QT_Shader_1'):
                            self.final_node = n   

                    for n in self.nodes:
                        if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.final_node = n    
                            
                    self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                    self.out_node.location.y = self.final_node.location.y
                    self.out_node.location.x = self.final_node.location.x + 300     

                    for n in self.nodes:
                        n.select = False
                        if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                            n.select = True

                bpy.context.window_manager.my_toolqt.running_qt = 0
                bpy.context.window_manager.my_toolqt.selected = 0
                bpy.context.window_manager.my_toolqt.decal = 0
                bpy.context.window_manager.my_toolqt.blend = 0
                bpy.context.window_manager.my_toolqt.mask = 0
                bpy.context.window_manager.my_toolqt.ob = None
                bpy.data.collections['QuickTexture'].hide_viewport=True
                bpy.data.collections['QuickTexture'].hide_render=True
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'FINISHED'}
                                    
            if event.type in {'LEFTMOUSE', 'ENTER'} and event.value == 'PRESS':

                if self.g or self.s or self.r or self.l or self.e or self.shifth or self.shifts or self.alts or self.shiftb or self.shiftn or self.ctrli or self.h or self.v or self.c or self.o or self.a or self.ashift:
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
                    self.a = 0
                    self.ashift = 0 

                else:
                    context.area.tag_redraw() 

                    if self.nodes is not None:

                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                self.final_node = n   

                        for n in self.nodes:
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n    

                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300     

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True

                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    bpy.context.window_manager.my_toolqt.selected = 0
                    bpy.context.window_manager.my_toolqt.decal = 0
                    bpy.context.window_manager.my_toolqt.blend = 0
                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.ob = None
                    bpy.data.collections['QuickTexture'].hide_viewport=True
                    bpy.data.collections['QuickTexture'].hide_render=True
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    return {'FINISHED'}

            if event.type == 'MOUSEMOVE':   

                if self.g:

                    self.mouse_sample_x.append(event.mouse_region_x)
                    self.mouse_sample_y.append(event.mouse_region_y)

                    if len(self.mouse_sample_x) > 1:
                        current = Vector((self.mouse_sample_x[-1], self.mouse_sample_y[-1]))
                        previous = Vector((self.mouse_sample_x[-2], self.mouse_sample_y[-2]))

                        delta = -0.005

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
                            aim = Vector((0,0,0))
                        
                        if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask: 
                            if self.blend_add:
                                self.blend_add.inputs[1].default_value[2] += aim[0] * dist * -1    

                            if self.mask_mapping:
                                self.mask_mapping.inputs[1].default_value[2] += aim[0] * dist * -1

                        else:                       
                            if bpy.context.window_manager.my_toolqt.activemap == 1:
                                mat = Matrix.Rotation(self.diffuse_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 2:
                                mat = Matrix.Rotation(self.rough_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 3:
                                mat = Matrix.Rotation(self.bump_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 4:
                                if self.mask_mapping:
                                    mat = Matrix.Rotation(self.mask_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 5:
                                mat = Matrix.Rotation(self.alpha_mapping.inputs[2].default_value[2], 4, "Z")

                            view = Vector((self.rv3d.view_matrix[2][0:3])).normalized()
                            viewmat = self.rv3d.view_matrix.normalized().to_3x3()
                            basemat = Matrix().to_3x3()
                            viewdot = view.dot(Vector((0,0,1)))
                            angle = viewmat[0].angle(basemat[0])
                            dirdot = viewmat[0].dot(Vector((0,-1,0)))
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
                                self.diffuse_mapping.inputs[1].default_value[0] += xval * dist
                                self.diffuse_mapping.inputs[1].default_value[1] += yval * dist
                                self.diffuse_mapping.inputs[1].default_value[2] = 1

                                self.rough_mapping.inputs[1].default_value[0] += xval * dist
                                self.rough_mapping.inputs[1].default_value[1] += yval * dist
                                self.rough_mapping.inputs[1].default_value[2] = 1

                                self.bump_mapping.inputs[1].default_value[0] += xval * dist
                                self.bump_mapping.inputs[1].default_value[1] += yval * dist
                                self.bump_mapping.inputs[1].default_value[2] = 1   

                                self.alpha_mapping.inputs[1].default_value[0] += xval * dist
                                self.alpha_mapping.inputs[1].default_value[1] += yval * dist
                                self.alpha_mapping.inputs[1].default_value[2] = 1  

                            elif bpy.context.window_manager.my_toolqt.activemap == 2:
                                self.rough_mapping.inputs[1].default_value[0] += xval * dist
                                self.rough_mapping.inputs[1].default_value[1] += yval * dist
                                self.rough_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 3:
                                self.bump_mapping.inputs[1].default_value[0] += xval * dist
                                self.bump_mapping.inputs[1].default_value[1] += yval * dist
                                self.bump_mapping.inputs[1].default_value[2] = 1 

                            elif bpy.context.window_manager.my_toolqt.activemap == 4:

                                if self.mask_mapping:
                                    if self.mask_mapping.name.startswith('QT_Add_Mask'):
                                        self.mask_mapping.inputs[1].default_value[2] += xval * dist * -1                
                                    else:
                                        self.mask_mapping.inputs[1].default_value[0] += xval * dist
                                        self.mask_mapping.inputs[1].default_value[1] += yval * dist
                                        self.mask_mapping.inputs[1].default_value[2] = 1      

                            elif bpy.context.window_manager.my_toolqt.activemap == 5:
                                self.alpha_mapping.inputs[1].default_value[0] += xval * dist
                                self.alpha_mapping.inputs[1].default_value[1] += yval * dist
                                self.alpha_mapping.inputs[1].default_value[2] = 1  

                        context.area.tag_redraw()

                if self.s:
                    
                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.003

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[0] += delta * self.diffuse_mapping.inputs[3].default_value[0]
                        self.diffuse_mapping.inputs[3].default_value[1] += delta * self.diffuse_mapping.inputs[3].default_value[1]
                        self.diffuse_mapping.inputs[3].default_value[2] += delta * self.diffuse_mapping.inputs[3].default_value[2]

                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]
                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]
                        self.rough_mapping.inputs[3].default_value[2] += delta * self.rough_mapping.inputs[3].default_value[2]

                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]
                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]
                        self.bump_mapping.inputs[3].default_value[2] += delta * self.bump_mapping.inputs[3].default_value[2] 

                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]
                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]
                        self.alpha_mapping.inputs[3].default_value[2] += delta * self.alpha_mapping.inputs[3].default_value[2]     

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]
                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]
                        self.rough_mapping.inputs[3].default_value[2] += delta * self.rough_mapping.inputs[3].default_value[2]

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:

                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]
                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]
                        self.bump_mapping.inputs[3].default_value[2] += delta * self.bump_mapping.inputs[3].default_value[2]  
                                                
                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[0] += delta * self.mask_mapping.inputs[3].default_value[0]
                            self.mask_mapping.inputs[3].default_value[1] += delta * self.mask_mapping.inputs[3].default_value[1]
                            self.mask_mapping.inputs[3].default_value[2] += delta * self.mask_mapping.inputs[3].default_value[2]

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        
                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]
                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]
                        self.alpha_mapping.inputs[3].default_value[2] += delta * self.alpha_mapping.inputs[3].default_value[2]  

                    context.area.tag_redraw()

                if self.shifts:
                    
                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.003

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[0] += delta * self.diffuse_mapping.inputs[3].default_value[0]

                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]

                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]

                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:

                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]
                                                
                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[0] += delta * self.mask_mapping.inputs[3].default_value[0]

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:

                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]

                    context.area.tag_redraw()

                if self.alts:
                    
                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.003

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10
                    
                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[1] += delta * self.diffuse_mapping.inputs[3].default_value[1]

                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]

                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]

                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]
                                                
                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[1] += delta * self.mask_mapping.inputs[3].default_value[1]

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]

                    context.area.tag_redraw()

                if self.r == 1:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= 0.0025

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
                            
                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[2].default_value[2] += delta 

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_mapping.inputs[2].default_value[2] += delta 

                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                        if self.mask_mapping:
                            self.mask_mapping.inputs[2].default_value[2] += delta

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_mapping.inputs[2].default_value[2] += delta 

                    context.area.tag_redraw()

                if self.l:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.0005

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

                    bpy.context.window_manager.my_toolqt.sss = self.core_shader.inputs[1].default_value

                    context.area.tag_redraw()

                if self.a:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

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

                        bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                    context.area.tag_redraw()

                if self.ashift:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    for modifier in bpy.context.window_manager.my_toolqt.ob.modifiers:
                        if modifier.name == "QT_Displace":
                            mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get("QT_Displace")
                            mod.strength += delta
                            if mod.strength < -5:
                                mod.strength = -5
                            if mod.strength > 5:
                                mod.strength = 5

                    context.area.tag_redraw()

                if self.e:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.01

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:
                            self.blend_noise.inputs[5].default_value += delta
                            if self.blend_noise.inputs[5].default_value < 0:
                                self.blend_noise.inputs[5].default_value = 0
                            if self.blend_noise.inputs[5].default_value > 20:
                                self.blend_noise.inputs[5].default_value = 20

                            bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value

                    else:
                        self.core_shader.inputs[18].default_value += delta
                        if self.core_shader.inputs[18].default_value < 0:
                            self.core_shader.inputs[18].default_value = 0

                        bpy.context.window_manager.my_toolqt.emit = self.core_shader.inputs[18].default_value

                    context.area.tag_redraw()

                if self.o:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.002

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:                            
                            self.blend_noise.inputs[4].default_value += delta
                            if self.blend_noise.inputs[4].default_value < 0:
                                self.blend_noise.inputs[4].default_value = 0
                            if self.blend_noise.inputs[4].default_value > 5:
                                self.blend_noise.inputs[4].default_value = 5

                            bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value

                    else:
                        if self.final_node.name.startswith('QT_Layer'):
                            self.final_node.inputs[0].default_value += delta
                            if self.final_node.inputs[0].default_value < 0:
                                self.final_node.inputs[0].default_value = 0
                            if self.final_node.inputs[0].default_value > 5:
                                self.final_node.inputs[0].default_value = 5

                            bpy.context.window_manager.my_toolqt.opacity = self.final_node.inputs[0].default_value

                    context.area.tag_redraw()

                if self.shifth:

                    delta = (event.mouse_prev_x - event.mouse_x) 

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        delta *= -0.005
                    else:
                        delta *= -0.0005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:
                            self.blend_noise.inputs[2].default_value += delta
                            if self.blend_noise.inputs[2].default_value < 0:
                                self.blend_noise.inputs[2].default_value = 0
                            if self.blend_noise.inputs[2].default_value > 30:
                                self.blend_noise.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value

                    else:
                        self.core_shader.inputs[5].default_value += delta
                        if self.core_shader.inputs[5].default_value < 0:
                            self.core_shader.inputs[5].default_value = 0
                        if self.core_shader.inputs[5].default_value > 5:
                            self.core_shader.inputs[5].default_value = 5

                        bpy.context.window_manager.my_toolqt.spec = self.core_shader.inputs[5].default_value

                    context.area.tag_redraw()

                if self.shiftn:

                    delta = (event.mouse_prev_x - event.mouse_x) 

                    delta *= -0.005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        print ("nothing yet")
                        
                    else:                        
                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value += delta
                            if self.normal_strength.inputs[0].default_value < 0:
                                self.normal_strength.inputs[0].default_value = 0
                            if self.normal_strength.inputs[0].default_value > 5:
                                self.normal_strength.inputs[0].default_value = 5

                            bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                    context.area.tag_redraw()

                if self.shiftb:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:
                            self.blend_noise.inputs[3].default_value += delta
                            if self.blend_noise.inputs[3].default_value < 0:
                                self.blend_noise.inputs[3].default_value = 0
                            if self.blend_noise.inputs[3].default_value > 30:
                                self.blend_noise.inputs[3].default_value = 30

                            bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value

                    else:
                        self.bump_bump.inputs[0].default_value += delta
                        if self.bump_bump.inputs[0].default_value < 0:
                            self.bump_bump.inputs[0].default_value = 0
                        if self.bump_bump.inputs[0].default_value > 5:
                            self.bump_bump.inputs[0].default_value = 5
                        bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value

                    context.area.tag_redraw()

                if self.h:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_power:
                            self.blend_power.inputs[1].default_value += delta
                            if self.blend_power.inputs[1].default_value < 0.001:
                                self.blend_power.inputs[1].default_value = 0.001
                            if self.blend_power.inputs[1].default_value > 5:
                                self.blend_power.inputs[1].default_value = 5

                            bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[0].default_value += delta
                            if self.diffuse_hue_sat.inputs[0].default_value < 0:
                                self.diffuse_hue_sat.inputs[0].default_value = 0
                            if self.diffuse_hue_sat.inputs[0].default_value > 5:
                                self.diffuse_hue_sat.inputs[0].default_value = 5

                            bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value

                    context.area.tag_redraw()
                
                if self.v:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[1].default_value += delta
                            if self.blend_bright_contrast.inputs[1].default_value < -30:
                                self.blend_bright_contrast.inputs[1].default_value = -30
                            if self.blend_bright_contrast.inputs[1].default_value > 30:
                                self.blend_bright_contrast.inputs[1].default_value = 30

                            bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[1].default_value += delta
                            bpy.context.window_manager.my_toolqt.blendvalue = self.mask_bright_contrast.inputs[1].default_value

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[2].default_value += delta
                            if self.diffuse_hue_sat.inputs[2].default_value < -30:
                                self.diffuse_hue_sat.inputs[2].default_value = -30
                            if self.diffuse_hue_sat.inputs[2].default_value > 30:
                                self.diffuse_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 2:
                            self.rough_hue_sat.inputs[2].default_value += delta
                            if self.rough_hue_sat.inputs[2].default_value < -30:
                                self.rough_hue_sat.inputs[2].default_value = -30
                            if self.rough_hue_sat.inputs[2].default_value > 30:
                                self.rough_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 3:
                            self.bump_hue_sat.inputs[2].default_value += delta
                            if self.bump_hue_sat.inputs[2].default_value < -30:
                                self.bump_hue_sat.inputs[2].default_value = -30
                            if self.bump_hue_sat.inputs[2].default_value > 30:
                                self.bump_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 4:
                            self.mask_hue_sat.inputs[2].default_value += delta
                            if self.mask_hue_sat.inputs[2].default_value < -30:
                                self.mask_hue_sat.inputs[2].default_value = -30
                            if self.mask_hue_sat.inputs[2].default_value > 30:
                                self.mask_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 5:
                            self.alpha_hue_sat.inputs[2].default_value += delta
                            if self.alpha_hue_sat.inputs[2].default_value < -30:
                                self.alpha_hue_sat.inputs[2].default_value = -30
                            if self.alpha_hue_sat.inputs[2].default_value > 30:
                                self.alpha_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value

                if self.c:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[2].default_value += delta
                            if self.blend_bright_contrast.inputs[2].default_value < -30:
                                self.blend_bright_contrast.inputs[2].default_value = -30
                            if self.blend_bright_contrast.inputs[2].default_value > 30:
                                self.blend_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[2].default_value += delta
                            bpy.context.window_manager.my_toolqt.blendcontrast = self.mask_bright_contrast.inputs[2].default_value

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[1].default_value += delta
                            if self.diffuse_hue_sat.inputs[1].default_value < -30:
                                self.diffuse_hue_sat.inputs[1].default_value = -30
                            if self.diffuse_hue_sat.inputs[1].default_value > 30:
                                self.diffuse_hue_sat.inputs[1].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 2:
                            self.rough_bright_contrast.inputs[2].default_value += delta
                            if self.rough_bright_contrast.inputs[2].default_value < -30:
                                self.rough_bright_contrast.inputs[2].default_value = -30
                            if self.rough_bright_contrast.inputs[2].default_value > 30:
                                self.rough_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 3:
                            self.bump_bright_contrast.inputs[2].default_value += delta
                            if self.bump_bright_contrast.inputs[2].default_value < -30:
                                self.bump_bright_contrast.inputs[2].default_value = -30
                            if self.bump_bright_contrast.inputs[2].default_value > 30:
                                self.bump_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 4:
                            self.mask_bright_contrast.inputs[2].default_value += delta
                            if self.mask_bright_contrast.inputs[2].default_value < -30:
                                self.mask_bright_contrast.inputs[2].default_value = -30
                            if self.mask_bright_contrast.inputs[2].default_value > 30:
                                self.mask_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 5:
                            self.alpha_bright_contrast.inputs[2].default_value += delta
                            if self.alpha_bright_contrast.inputs[2].default_value < -30:
                                self.alpha_bright_contrast.inputs[2].default_value = -30
                            if self.alpha_bright_contrast.inputs[2].default_value > 30:
                                self.alpha_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[2].default_value

# OS KEYS            
            elif event.type in {'LEFT_ALT', 'RIGHT_ALT'}:
                if event.value == 'PRESS':
                    self.alt = 1
                if event.value == 'RELEASE':
                    self.alt = 0

            elif event.type == 'SPACE':
                return {'PASS_THROUGH'}

            elif event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT'}:
                if event.value == 'PRESS':
                    self.shift = 1

                if event.value == 'RELEASE':
                    self.shift = 0

                return {'PASS_THROUGH'}

            elif event.type in {'LEFT_CTRL', 'RIGHT_CTRL', 'OSKEY'}:

                if event.value == 'PRESS':
                    self.ctrl = 1
                if event.value == 'RELEASE':
                    self.ctrl = 0
                
                return {'PASS_THROUGH'}                 
# KEYS                                  
# 
            # LAYERS            
            elif event.type == 'N':    
                if event.value == 'PRESS':

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

                    if self.ctrl == 0 and self.alt == 0 and self.shift == 0:
                        return {'PASS_THROUGH'}

                    elif self.ctrl == 0 and self.alt == 0 and self.shift == 1:
                        if self.shiftn: 
                            self.shiftn = 0
                        else:
                            self.shiftn = 1

                    elif self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:             
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.normalmask_qt('INVOKE_DEFAULT')

                    elif self.ctrl == 1 and self.alt == 0 and self.shift == 1:

                        if bpy.context.window_manager.my_toolqt.ob.data.materials:
                            for mat in bpy.context.window_manager.my_toolqt.ob.data.materials:
                                if mat:
                                    if mat.name.startswith("QT"):
                                        bpy.ops.object.material_slot_remove()
                            bpy.context.window_manager.my_toolqt.running_qt = 0

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0
                                                                                    
            # MOVE   
            elif event.type == 'G':
                if event.value == 'PRESS':

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

                    if self.g:
                        self.g = 0
                        self.mouse_sample_x = []
                        self.mouse_sample_y = []
                    else:
                        self.g = 1
                        self.mouse_sample_x = []
                        self.mouse_sample_y = []
                                
            # SCALE   
            elif event.type == 'S':   
                if event.value == 'PRESS':
                    
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
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
                            if self.s: 
                                self.s = 0
                            else:
                                self.s = 1

            # ROTATE   
            elif event.type == 'R':
                if event.value == 'PRESS':

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

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:  

                        if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                            if self.r: 
                                self.r = 0
                            else:
                                self.r = 1
                            
                        elif event.ctrl == 0 and event.shift == 0 and event.alt == 1:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.ops.qt.replacemaps('INVOKE_DEFAULT')
                        
                        elif event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.context.window_manager.my_toolqt.running_qt = 0
                            return {'PASS_THROUGH'}

                        elif event.ctrl == 1 and event.shift == 1 and event.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.context.window_manager.my_toolqt.running_qt = 0
                            return {'PASS_THROUGH'}
                                                                    
            # REPROJECT FROM VIEW
            elif event.type == 'P' and event.value == 'PRESS':

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:  
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

                    resetparm = 0
                    empty_uv = None

                    for modifier in bpy.context.window_manager.my_toolqt.ob.modifiers:
                        if modifier.name.startswith('QT_UV_View_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            resetparm = 1
                            mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get(modifier.name)
                            empty_uv = mod.projectors[0].object
                            empty_uv.rotation_euler = context.region_data.view_rotation.to_euler()

                    if empty_uv:
                        cloc = bpy.context.scene.cursor.location
                        empty_uv.location = region_2d_to_location_3d(self.region, self.rv3d, (self.coord), (cloc)) 

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
            elif event.type == 'M' and event.value == 'PRESS':

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
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

                    if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                        self.ctrl = 0
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            
                            # check if mask exists on current layer
                            mask = 0
                            for n in self.nodes:
                                if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    mask = 1

                            if mask == 0:
                                bpy.ops.qt.texturemask_qt('INVOKE_DEFAULT')
                    
                    elif self.ctrl == 0 and self.alt == 0 and self.shift == 0:                
                        bpy.context.window_manager.my_toolqt.metal = not bpy.context.window_manager.my_toolqt.metal 

                        if bpy.context.window_manager.my_toolqt.metal:
                            if self.core_shader:
                                self.core_shader.inputs[4].default_value = 1
                        else:
                            if self.core_shader:
                                self.core_shader.inputs[4].default_value = 0

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # SSS
            elif event.type == 'L':   
                if event.value == 'PRESS':

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
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

                        if self.l: 
                            self.l = 0
                        else:
                            self.l = 1

            # AO
            elif event.type == 'A':   
                if event.value == 'PRESS':

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
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

                        if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            self.alpha_type = 1
                            bpy.ops.qt.replacealpha('INVOKE_DEFAULT')

                        elif self.ctrl == 0 and self.shift == 0 and self.alt == 1:
                            self.ctrl = 0
                            self.shift = 0

                            if self.alpha_type:                            
                                self.node_tree.links.new(self.alpha_tex.outputs[0], self.alpha_color_ramp.inputs[0])
                                self.alpha_type = 0
                            else:                       
                                self.node_tree.links.new(self.alpha_tex.outputs[1], self.alpha_color_ramp.inputs[0])
                                self.alpha_type = 1

                        elif self.ctrl == 0 and self.shift == 1 and self.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            if self.ashift: 
                                self.ashift = 0
                            else:
                                self.ashift = 1

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
            elif event.type == 'E':   
                if event.value == 'PRESS':

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

                    if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                        if self.e: 
                            self.e = 0
                        else:
                            self.e = 1

                    else:
                        bpy.context.window_manager.my_toolqt.running_qt = 0
                        return {'PASS_THROUGH'}

            # BUMP
            elif event.type == 'B':   
                if event.value == 'PRESS':

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
                    self.o = 0                   

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
                        # NEW BOX LAYER
                        if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                            if bpy.context.window_manager.my_toolqt.activelayer < 5:
                                bpy.ops.qt.boxlayer_qt('INVOKE_DEFAULT')    

                    if self.shift == 1 and self.ctrl == 0 and self.alt == 0:
                        if self.shiftb: 
                            self.shiftb = 0
                        else:
                            self.shiftb = 1

                    if self.shift == 1 and self.ctrl == 1 and self.alt == 0:
                        bpy.context.window_manager.my_toolqt.running_qt = 0
                        return {'PASS_THROUGH'}

                    
                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # HUE
            elif event.type == 'H':   
                if event.value == 'PRESS':

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

                    if self.ctrl:
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:                        
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.heightmask_qt('INVOKE_DEFAULT')

                    if self.alt:
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:                        
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.depthmask_qt('INVOKE_DEFAULT')

                    if self.shift:
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

            # VALUE
            elif event.type == 'V':   
                if event.value == 'PRESS':

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

                    # NEW VIEW LAYER
                    if self.ctrl:
                        self.ctrl = 0
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
                            if bpy.context.window_manager.my_toolqt.activelayer < 5:
                                bpy.ops.qt.viewlayer_qt('INVOKE_DEFAULT')

                    else:
                        if self.v: 
                            self.v = 0
                        else:
                            self.v = 1

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # SATURATION
            elif event.type == 'C':   
                if event.value == 'PRESS':

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

                    if self.alt:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            if self.diffuse_tex:
                                if self.diffuse_tex.extension == 'CLIP':
                                    self.diffuse_tex.extension = 'REPEAT'
                                else:
                                    self.diffuse_tex.extension = 'CLIP'

                            if self.rough_tex:
                                if self.rough_tex.extension == 'CLIP':
                                    self.rough_tex.extension = 'REPEAT'
                                else:
                                    self.rough_tex.extension = 'CLIP'

                            if self.bump_tex:
                                if self.bump_tex.extension == 'CLIP':
                                    self.bump_tex.extension = 'REPEAT'
                                else:
                                    self.bump_tex.extension = 'CLIP'

                            if self.normal_tex:
                                if self.normal_tex.extension == 'CLIP':
                                    self.normal_tex.extension = 'REPEAT'
                                else:
                                    self.normal_tex.extension = 'CLIP'

                            if self.alpha_tex:
                                if self.alpha_tex.extension == 'CLIP':
                                    self.alpha_tex.extension = 'REPEAT'
                                else:
                                    self.alpha_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 2:
                            if self.rough_tex:
                                if self.rough_tex.extension == 'CLIP':
                                    self.rough_tex.extension = 'REPEAT'
                                else:
                                    self.rough_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 3:
                            if self.bump_tex:
                                if self.bump_tex.extension == 'CLIP':
                                    self.bump_tex.extension = 'REPEAT'
                                else:
                                    self.bump_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 4:
                            if self.mask_tex:
                                if self.mask_tex.extension == 'CLIP':
                                    self.mask_tex.extension = 'REPEAT'
                                else:
                                    self.mask_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 5:
                            if self.alpha_tex:
                                if self.alpha_tex.extension == 'CLIP':
                                    self.alpha_tex.extension = 'REPEAT'
                                else:
                                    self.alpha_tex.extension = 'CLIP'
                                
                    else:
                        if self.c: 
                            self.c = 0
                        else:
                            self.c = 1

            # OPACITY
            elif event.type == 'O':   
                if event.value == 'PRESS':

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
                    
                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:      
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
                                    if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        self.o = 1

            # INVERT
            elif event.type == 'I' and event.value == 'PRESS':

                if self.ctrl:
                    if bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_invert.inputs[0].default_value = not self.rough_invert.inputs[0].default_value

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_invert.inputs[0].default_value = not self.bump_invert.inputs[0].default_value                       

                    elif bpy.context.window_manager.my_toolqt.activemap == 4:
                        self.mask_invert.inputs[0].default_value = not self.mask_invert.inputs[0].default_value    

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_invert.inputs[0].default_value = not self.alpha_invert.inputs[0].default_value    

                    context.area.tag_redraw()

            # DUPLICATE LAYER
            elif event.shift and event.type == 'D' and event.value == 'PRESS':

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
                        if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer-1)):
                            n.select = False
                            nodes.append(n)

                        if n.name.startswith('QT_Shader_1'):
                            layer1 = n

                        if n.name.startswith('QT_Shader_2'):
                            layer2 = n

                        if n.name.startswith('QT_Shader_3'):
                            layer3 = n
                        
                        if n.name.startswith('QT_Shader_4'):
                            layer4 = n

                    if bpy.context.window_manager.my_toolqt.activelayer == 2 and layer2: 
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith('_4'):                 
                                    n.name = n.name.replace("_4", "_5")   
                                    n.label = n.label.replace("_4", "_5")   
                                    n.location.y -= 2000   
                        if layer3:
                            for n in self.nodes:
                                if n.name.endswith('_3'):                 
                                    n.name = n.name.replace("_3", "_4")   
                                    n.label = n.label.replace("_3", "_4")   
                                    n.location.y -= 2000   
                        if layer2:       
                            for n in self.nodes:
                                if n.name.endswith('_2'):                 
                                    n.name = n.name.replace("_2", "_3")   
                                    n.label = n.label.replace("_2", "_3")   
                                    n.location.y -= 2000       

                    if bpy.context.window_manager.my_toolqt.activelayer == 3 and layer3: 
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith('_4'):                 
                                    n.name = n.name.replace("_4", "_5")   
                                    n.label = n.label.replace("_4", "_5")   
                                    n.location.y -= 2000   
                        if layer3:
                            for n in self.nodes:
                                if n.name.endswith('_3'):                 
                                    n.name = n.name.replace("_3", "_4")   
                                    n.label = n.label.replace("_3", "_4")   
                                    n.location.y -= 2000   

                    if bpy.context.window_manager.my_toolqt.activelayer == 4 and layer4: 
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith('_4'):                 
                                    n.name = n.name.replace("_4", "_5")   
                                    n.label = n.label.replace("_4", "_5")   
                                    n.location.y -= 2000  

                    for node in nodes:
                        if node.type != 'GROUP_OUTPUT':

                            # copy node
                            node_new = self.nodes.new(node.bl_idname)

                            # get old node settings
                            attributes = []
                            input_attributes = ( "default_value", "name" )
                            output_attributes = ( "default_value", "name" )
                            ignore_attributes = ( "rna_type", "type", "dimensions", "inputs", "outputs", "internal_links", "select", "texture_mapping", "color_mapping", "image_user", "color_ramp")
                            for attr in node.bl_rna.properties:
                                if not attr.identifier in ignore_attributes and not attr.identifier.split("_")[0] == "bl":
                                    attributes.append(attr.identifier)

                            # copy attributes
                            for attr in attributes:
                                if hasattr( node_new, attr ):
                                    setattr( node_new, attr, getattr( node, attr ))

                            #copy the attributes for all inputs
                            for i, inp in enumerate(node.inputs):                                
                                # copy input attributes
                                for attr in input_attributes:
                                    if hasattr( node_new.inputs[i], attr ):
                                        setattr( node_new.inputs[i], attr, getattr( inp, attr ))

                            #copy the attributes for all outputs
                            for i, out in enumerate(node.outputs):
                                # copy output attributes
                                for attr in output_attributes:
                                    if hasattr( node_new.outputs[i], attr ):
                                        setattr( node_new.outputs[i], attr, getattr( out, attr ))
                            
                            node_new.location = node.location
                            node_new.location.y -= 2000

                            node_new.name = node.name
   
                            if bpy.context.window_manager.my_toolqt.activelayer == 2:                                       
                                node_new.name = node_new.name.replace("1.001", "2")   
                                node_new.label = node_new.label.replace("Layer_1", "Layer_2")   
                            if bpy.context.window_manager.my_toolqt.activelayer == 3: 
                                node_new.name = node_new.name.replace("2.001", "3")   
                                node_new.label = node_new.label.replace("Layer_2", "Layer_3")   
                            if bpy.context.window_manager.my_toolqt.activelayer == 4: 
                                node_new.name = node_new.name.replace("3.001", "4")   
                                node_new.label = node_new.label.replace("Layer_3", "Layer_4")   
                            if bpy.context.window_manager.my_toolqt.activelayer == 5: 
                                node_new.name = node_new.name.replace("4.001", "5")   
                                node_new.label = node_new.label.replace("Layer_4", "Layer_5")   

                    # NAMES
                    for n in self.nodes:
                        # ACTIVE LAYER             
                        if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer-1)):
                            self.prev_shader = n
                        if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.new_shader = n
                        
                        if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer-1)):
                            self.prev_blend_node = n

                        if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.final_node = n
                        
                        if n.name == 'Group Output':
                            self.out_node = n

                        # coord
                        if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.tex_coord = n

                        # normal
                        if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.normal_tex = n
                        if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.normal_strength = n

                        # mapping                                 
                        if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_mapping = n
                        if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_mapping = n
                        if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_mapping = n

                        # clamps
                        if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_clamp = n
                        if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_clamp = n
                        if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_clamp = n

                        # textures
                        if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_tex = n
                        if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_hue_sat = n
                        if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_bright_contrast = n

                        if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_tex = n
                        if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_color_ramp = n
                        if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_bright_contrast = n
                        if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_invert = n
                        if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_hue_sat = n

                        if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_tex = n
                        if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_color_ramp = n
                        if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_bright_contrast = n
                        if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_bump = n
                        if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_invert = n
                        if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_hue_sat = n

                        # masks
                        if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_tex = n
                        if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_color_ramp = n
                        if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_bright_contrast = n
                        if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_invert = n
                        if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_hue_sat = n
                        if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_mapping = n

                        # alpha
                        if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_mapping = n
                        if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_tex = n
                        if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_color_ramp = n
                        if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_bright_contrast = n
                        if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_invert = n
                        if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_hue_sat = n
                        if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_clamp = n

                        # ao
                        if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.ao_tex = n
                        if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.ao_multiply = n

                        # height
                        if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.blend_power = n
                        if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.blend_noise = n
                        
                        # blend
                        if bpy.context.window_manager.my_toolqt.blend:
                            if n.name == ('QT_Blend_Add'):
                                self.blend_add = n
                            if n.name == ('QT_Blend_XYZ'):
                                self.blend_xyz = n
                            if n.name == ('QT_Blend_Math'):
                                self.blend_math = n
                            if n.name == ('QT_Blend_Power'):
                                self.blend_power = n
                            if n.name == ('QT_Blend_Clamp'):
                                self.blend_clamp = n
                            if n.name == ('QT_Blend_Mix'):
                                self.blend_mix = n
                            if n.name == ('QT_Blend_Noise'):
                                self.blend_noise = n
                            if n.name == ('QT_Blend_Bright_Contrast'):
                                self.blend_bright_contrast = n
                            if n.name == 'QT_Blend_Mix':
                                self.final_node = n
                                self.core_shader = n          

                    # LINKS           
                    if self.tex_coord.label == 'Decal' or n.label == 'View' or n.label == 'Box':
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.diffuse_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.rough_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.bump_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.alpha_mapping.inputs[0])
                    else:
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.diffuse_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.rough_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.bump_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.alpha_mapping.inputs[0])                    

                    self.node_tree.links.new(self.diffuse_mapping.outputs[0], self.diffuse_tex.inputs[0])
                    self.node_tree.links.new(self.diffuse_tex.outputs[0], self.diffuse_hue_sat.inputs[4])
                    self.node_tree.links.new(self.diffuse_hue_sat.outputs[0], self.diffuse_bright_contrast.inputs[0])
                    self.node_tree.links.new(self.diffuse_bright_contrast.outputs[0], self.new_shader.inputs[0])

                    self.node_tree.links.new(self.rough_mapping.outputs[0], self.rough_tex.inputs[0])
                    self.node_tree.links.new(self.rough_tex.outputs[0], self.rough_color_ramp.inputs[0])
                    self.node_tree.links.new(self.rough_color_ramp.outputs[0], self.rough_hue_sat.inputs[4])
                    self.node_tree.links.new(self.rough_hue_sat.outputs[0], self.rough_invert.inputs[1])
                    self.node_tree.links.new(self.rough_invert.outputs[0], self.rough_bright_contrast.inputs[0])
                    self.node_tree.links.new(self.rough_bright_contrast.outputs[0], self.new_shader.inputs[7])
                    
                    self.node_tree.links.new(self.rough_bright_contrast.outputs[0], self.rough_clamp.inputs[0])
                    self.node_tree.links.new(self.rough_clamp.outputs[0], self.new_shader.inputs[7])
                        
                    self.node_tree.links.new(self.bump_tex.outputs[0], self.bump_color_ramp.inputs[0])
                    self.node_tree.links.new(self.bump_color_ramp.outputs[0], self.bump_hue_sat.inputs[4])
                    self.node_tree.links.new(self.bump_hue_sat.outputs[0], self.bump_invert.inputs[1])
                    self.node_tree.links.new(self.bump_invert.outputs[0], self.bump_bright_contrast.inputs[0])
                    self.node_tree.links.new(self.bump_bright_contrast.outputs[0], self.bump_bump.inputs[2])

                    self.node_tree.links.new(self.bump_bright_contrast.outputs[0], self.bump_clamp.inputs[0])
                    self.node_tree.links.new(self.bump_clamp.outputs[0], self.bump_bump.inputs[2])
                    
                    self.node_tree.links.new(self.bump_mapping.outputs[0], self.bump_tex.inputs[0])
                    self.node_tree.links.new(self.bump_bump.outputs[0], self.new_shader.inputs[20])

                    # normal
                    if self.normal_tex:
                        self.node_tree.links.new(self.diffuse_mapping.outputs[0], self.normal_tex.inputs[0])
                        self.node_tree.links.new(self.normal_tex.outputs[0], self.normal_strength.inputs[1])
                        self.node_tree.links.new(self.normal_strength.outputs[0], self.bump_bump.inputs[5])
                    
                    # ao
                    if self.ao_tex:
                        self.node_tree.links.new(self.diffuse_mapping.outputs[0], self.ao_tex.inputs[0])
                        self.node_tree.links.new(self.ao_tex.outputs[0], self.ao_multiply.inputs[2])
                        self.node_tree.links.new(self.diffuse_tex.outputs[0], self.ao_multiply.inputs[1])
                        self.node_tree.links.new(self.ao_multiply.outputs[0], self.diffuse_hue_sat.inputs[4])
                            
                    self.node_tree.links.new(self.alpha_mapping.outputs[0], self.alpha_tex.inputs[0])
                    self.node_tree.links.new(self.alpha_tex.outputs[1], self.alpha_color_ramp.inputs[0])
                    self.node_tree.links.new(self.alpha_color_ramp.outputs[0], self.alpha_hue_sat.inputs[4])
                    self.node_tree.links.new(self.alpha_hue_sat.outputs[0], self.alpha_invert.inputs[1])
                    self.node_tree.links.new(self.alpha_invert.outputs[0], self.alpha_bright_contrast.inputs[0])    
                    self.node_tree.links.new(self.alpha_bright_contrast.outputs[0], self.alpha_clamp.inputs[0])
                    self.node_tree.links.new(self.alpha_clamp.outputs[0], self.new_shader.inputs[19])

                    # BLEND
                    if bpy.context.window_manager.my_toolqt.activelayer == 2:
                        self.blend_node = self.node_tree.nodes.new('ShaderNodeMixShader')
                        self.blend_node.name = 'QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)
                        self.blend_node.inputs[0].default_value = 1

                        self.node_tree.links.new(self.prev_shader.outputs[0], self.blend_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.blend_node.inputs[2])
                        self.node_tree.links.new(self.blend_node.outputs[0], self.out_node.inputs[0])

                        self.blend_node.location.x = self.new_shader.location.x + 300
                        self.blend_node.location.y = self.new_shader.location.y

                        self.out_node.location.y = self.blend_node.location.y
                        self.out_node.location.x = self.blend_node.location.x + 300  

                    if bpy.context.window_manager.my_toolqt.activelayer == 3:

                        self.node_tree.links.new(self.prev_blend_node.outputs[0], self.final_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.final_node.inputs[2])
                        self.node_tree.links.new(self.final_node.outputs[0], self.out_node.inputs[0])

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300  

                    if bpy.context.window_manager.my_toolqt.activelayer == 4:

                        self.node_tree.links.new(self.prev_blend_node.outputs[0], self.final_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.final_node.inputs[2])
                        self.node_tree.links.new(self.final_node.outputs[0], self.out_node.inputs[0])

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300  

                    if bpy.context.window_manager.my_toolqt.activelayer == 5:

                        self.node_tree.links.new(self.prev_blend_node.outputs[0], self.final_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.final_node.inputs[2])
                        self.node_tree.links.new(self.final_node.outputs[0], self.out_node.inputs[0])

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300  

                    for n in self.nodes:
                        if n.name.startswith('QT_Shader_1'):
                            layer1 = n

                        if n.name.startswith('QT_Layer_2'):
                            layer2 = n

                        if n.name.startswith('QT_Layer_3'):
                            layer3 = n
                        
                        if n.name.startswith('QT_Layer_4'):
                            layer4 = n

                        if n.name.startswith('QT_Layer_5'):
                            layer5 = n

                        if n.name.startswith('QT_Blend_1'):
                            blend1 = n

                        if n.name.startswith('QT_Blend_2'):
                            blend2 = n

                        if n.name.startswith('QT_Blend_3'):
                            blend3 = n
                        
                        if n.name.startswith('QT_Blend_4'):
                            blend4 = n

                        if n.name.startswith('QT_Blend_5'):
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
            elif event.type in {'ONE'} and event.value == 'PRESS':

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
                self.o = 0

                if bpy.context.window_manager.my_toolqt.blend == 0:    
                    
                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 1            

                    self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])
                    
            elif event.type in {'TWO'} and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0:    

                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 2          

                    self.node_tree.links.new(self.out_node.inputs[0], self.roughness_clamp.outputs[0])

            elif event.type in {'THREE'} and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0:    
                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 3               

                    if self.bump_clamp:
                        self.node_tree.links.new(self.out_node.inputs[0], self.bump_clamp.outputs[0])     

            elif event.type in {'FOUR'} and event.value == 'PRESS':

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

                if self.blend_noise:
                    bpy.context.window_manager.my_toolqt.mask = 1
                    bpy.context.window_manager.my_toolqt.activemap = 4 
                    self.node_tree.links.new(self.out_node.inputs[0], self.mask_clamp.outputs[0])     

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:    
                    if self.mask_clamp:
                        bpy.context.window_manager.my_toolqt.activemap = 4        
                        self.node_tree.links.new(self.out_node.inputs[0], self.mask_clamp.outputs[0])     

            elif event.type in {'FIVE'} and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0:    

                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 5        

                    self.node_tree.links.new(self.out_node.inputs[0], self.alpha_clamp.outputs[0])

            # ACTIVE LAYER
            elif event.type == 'Q' and event.value == 'PRESS':

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

                if self.shift == 1 and self.ctrl == 1 and self.alt == 0:
                        bpy.context.window_manager.my_toolqt.running_qt = 0
                        return {'PASS_THROUGH'}

                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:    

                        bpy.context.window_manager.my_toolqt.activemap = 1     

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            bpy.context.window_manager.my_toolqt.activelayer -= 1

                            if bpy.context.window_manager.my_toolqt.activelayer == 1:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_1'):
                                        self.core_shader = n     
                                        self.final_node = self.core_shader

                            if bpy.context.window_manager.my_toolqt.activelayer == 2:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_2'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_2'):
                                        self.final_node = n  
                                        
                            if bpy.context.window_manager.my_toolqt.activelayer == 3:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_3'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_3'):
                                        self.final_node = n  

                            if bpy.context.window_manager.my_toolqt.activelayer == 4:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_4'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_4'):
                                        self.final_node = n  

                            if bpy.context.window_manager.my_toolqt.activelayer == 5:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_5'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_5'):
                                        self.final_node = n  
                            
                            self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])
                            self.out_node.location.y = self.final_node.location.y
                            self.out_node.location.x = self.final_node.location.x + 300
                            
                            for n in self.nodes:
                                n.select = False
                                if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    n.select = True
                            
                            bpy.context.window_manager.my_toolqt.proc_uv = 0 

                            for n in self.nodes:
                                if n.select:
                                    if n.name.startswith('QT_UV_Layer_' + (str(bpy.context.window_manager.my_toolqt.activelayer))):

                                        if n.label == 'Decal' or n.label == 'View':
                                            bpy.context.window_manager.my_toolqt.proc_uv = 1 

                                        if n.label == 'Box':
                                            bpy.context.window_manager.my_toolqt.proc_uv = 1                                                  

                            # set parameters
                            bpy.context.window_manager.my_toolqt.emit = self.core_shader.inputs[18].default_value
                            bpy.context.window_manager.my_toolqt.metal = self.core_shader.inputs[4].default_value
                            bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                            bpy.context.window_manager.my_toolqt.spec = self.core_shader.inputs[5].default_value
                            bpy.context.window_manager.my_toolqt.sss = self.core_shader.inputs[1].default_value

                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                bpy.context.window_manager.my_toolqt.opacity = self.final_node.inputs[0].default_value
                            
                            if self.normal_tex:
                                if self.normal_tex.name == 'QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                    bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value
                                else:
                                    self.normal_tex = None

                            if self.ao_tex:
                                if self.ao_tex.name == 'QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                    bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value
                                else:
                                    self.ao_tex = None
                
            elif event.type == 'W' and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:    

                    bpy.context.window_manager.my_toolqt.activemap = 1 

                    passgo = 0

                    if bpy.context.window_manager.my_toolqt.activelayer == 1:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_2'):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 2:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_3'):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 3:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_4'):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 4:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_5'):
                                passgo = 1

                    if passgo:
                        if bpy.context.window_manager.my_toolqt.activelayer < 5:
                            bpy.context.window_manager.my_toolqt.activelayer += 1
                            
                        if bpy.context.window_manager.my_toolqt.activelayer == 2:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_2'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_2'):
                                    self.final_node = n  

                        if bpy.context.window_manager.my_toolqt.activelayer == 3:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_3'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_3'):
                                    self.final_node = n  

                        if bpy.context.window_manager.my_toolqt.activelayer == 4:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_4'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_4'):
                                    self.final_node = n  

                        if bpy.context.window_manager.my_toolqt.activelayer == 5:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_5'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_5'):
                                    self.final_node = n  

                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True

                        bpy.context.window_manager.my_toolqt.proc_uv = 0 

                        for n in self.nodes:
                            if n.select:
                                if n.name.startswith('QT_UV_Layer_' + (str(bpy.context.window_manager.my_toolqt.activelayer))):

                                    if n.label == 'Decal' or n.label == 'View':
                                        bpy.context.window_manager.my_toolqt.proc_uv = 1 

                                    if n.label == 'Box':
                                        bpy.context.window_manager.my_toolqt.proc_uv = 1                                            

                        # set parameters
                        bpy.context.window_manager.my_toolqt.emit = self.core_shader.inputs[18].default_value
                        bpy.context.window_manager.my_toolqt.metal = self.core_shader.inputs[4].default_value
                        bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                        bpy.context.window_manager.my_toolqt.spec = self.core_shader.inputs[5].default_value
                        bpy.context.window_manager.my_toolqt.sss = self.core_shader.inputs[1].default_value
                        
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            bpy.context.window_manager.my_toolqt.opacity = self.final_node.inputs[0].default_value

                        if self.normal_tex:
                            if self.normal_tex.name == 'QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value
                            else:
                                self.normal_tex = None

                        if self.ao_tex:
                            if self.ao_tex.name == 'QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value
                            else:
                                self.ao_tex = None

            # PREVIEW ALL LAYERS
            elif event.type == 'TAB' and event.value == 'RELEASE':

                if bpy.context.window_manager.my_toolqt.blend == 0:   
                    self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       

            # UV/BOX TOGGLE
            elif event.type == 'U' and event.value == 'PRESS':

                if self.tex_coord.label == 'Box':
                    if self.diffuse_tex:
                        if self.diffuse_tex.projection == 'FLAT':
                            self.diffuse_tex.projection = 'BOX'
                            self.diffuse_tex.projection_blend = 0.3
                            self.rough_tex.projection = 'BOX'
                            self.rough_tex.projection_blend = 0.3

                            t_name = self.tex_coord.name
                            t_label = self.tex_coord.label
                            t_location = self.tex_coord.location
                            self.node_tree.nodes.remove(self.tex_coord)
                            self.tex_coord = self.node_tree.nodes.new('ShaderNodeTexCoord')
                            self.tex_coord.name = t_name
                            self.tex_coord.label = t_label
                            self.tex_coord.location = t_location                                  

                            self.node_tree.links.new(self.tex_coord.outputs[0], self.diffuse_mapping.inputs[0])
                            self.node_tree.links.new(self.tex_coord.outputs[0], self.rough_mapping.inputs[0])
                           
                            if self.bump_tex:
                                self.bump_tex.projection = 'BOX'
                                self.bump_tex.projection_blend = 0.3
                                self.node_tree.links.new(self.tex_coord.outputs[0], self.bump_mapping.inputs[0])
                            if self.normal_tex:
                                self.normal_tex.projection = 'BOX'
                                self.normal_tex.projection_blend = 0.3
                            if self.ao_tex:
                                self.ao_tex.projection = 'BOX'
                                self.ao_tex.projection_blend = 0.3
                            if self.alpha_tex:
                                self.alpha_tex.projection = 'BOX'
                                self.alpha_tex.projection_blend = 0.3
                                self.node_tree.links.new(self.tex_coord.outputs[0], self.alpha_mapping.inputs[0])
                            if self.mask_tex:
                                self.mask_tex.projection = 'BOX'
                                self.mask_tex.projection_blend = 0.3
                                self.node_tree.links.new(self.tex_coord.outputs[0], self.mask_mapping.inputs[0])
                            
                        else:
                            self.diffuse_tex.projection = 'FLAT'
                            self.rough_tex.projection = 'FLAT'

                            t_name = self.tex_coord.name
                            t_label = self.tex_coord.label
                            t_location = self.tex_coord.location
                            self.node_tree.nodes.remove(self.tex_coord)
                            self.tex_coord = self.node_tree.nodes.new('ShaderNodeUVMap')
                            self.tex_coord.name = t_name
                            self.tex_coord.label = t_label
                            self.tex_coord.location = t_location
                            self.tex_coord.uv_map = 'QT_UV_Box_Layer_1'

                            self.node_tree.links.new(self.tex_coord.outputs[0], self.diffuse_mapping.inputs[0])
                            self.node_tree.links.new(self.tex_coord.outputs[0], self.rough_mapping.inputs[0])
                            
                            if self.bump_tex:
                                self.bump_tex.projection = 'FLAT'
                                self.node_tree.links.new(self.tex_coord.outputs[0], self.bump_mapping.inputs[0])
                            if self.normal_tex:
                                self.normal_tex.projection = 'FLAT'
                            if self.ao_tex:
                                self.ao_tex.projection = 'FLAT'
                            if self.alpha_tex:
                                self.alpha_tex.projection = 'FLAT'
                                self.node_tree.links.new(self.tex_coord.outputs[0], self.alpha_mapping.inputs[0])
                            if self.mask_tex:
                                self.mask_tex.projection = 'FLAT'
                                self.node_tree.links.new(self.tex_coord.outputs[0], self.mask_mapping.inputs[0])

                    context.area.tag_redraw() 
                
            elif event.type == 'UP_ARROW' and event.value == 'RELEASE':
                return {'PASS_THROUGH'}
                
            elif event.type == 'DOWN_ARROW' and event.value == 'RELEASE':
                return {'PASS_THROUGH'}

            elif event.type == 'BACK_SPACE' and event.value == 'RELEASE':

                if self.ctrl:
                    if bpy.context.window_manager.my_toolqt.blend == 0:    

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:

                            layer1 = None
                            layer2 = None
                            layer3 = None
                            layer4 = None
                            layer5 = None

                            for n in self.nodes:
                                if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.nodes.remove(n)

                            bpy.context.window_manager.my_toolqt.activelayer -= 1

                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_1'):
                                    self.final_node = n   

                            for n in self.nodes:
                                if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.final_node = n    
                                    
                            self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                            self.out_node.location.y = self.final_node.location.y
                            self.out_node.location.x = self.final_node.location.x + 300
                            
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_1'):
                                    layer1 = n

                                if n.name.startswith('QT_Layer_2'):
                                    layer2 = n

                                if n.name.startswith('QT_Layer_3'):
                                    layer3 = n
                                
                                if n.name.startswith('QT_Layer_4'):
                                    layer4 = n

                                if n.name.startswith('QT_Layer_5'):
                                    layer5 = n

                            if bpy.context.window_manager.my_toolqt.activelayer == 1:
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith('_5'):                 
                                            n.name = n.name.replace("_5", "_4")   
                                            n.label = n.label.replace("_5", "_4")   
                                            n.location.y += 2000   
                                if layer4:
                                    for n in self.nodes:
                                        if n.name.endswith('_4'):                 
                                            n.name = n.name.replace("_4", "_3")   
                                            n.label = n.label.replace("_4", "_3")   
                                            n.location.y += 2000   
                                if layer3:          
                                    for n in self.nodes:
                                        if n.name.endswith('_3'):                 
                                            n.name = n.name.replace("_3", "_2")   
                                            n.label = n.label.replace("_3", "_2")   
                                            n.location.y += 2000    

                                    self.node_tree.links.new(layer1.outputs[0], layer3.inputs[1])    
                                    
                            if bpy.context.window_manager.my_toolqt.activelayer == 2:
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith('_5'):                 
                                            n.name = n.name.replace("_5", "_4")   
                                            n.label = n.label.replace("_5", "_4")   
                                            n.location.y += 2000   
                                if layer4:
                                    for n in self.nodes:
                                        if n.name.endswith('_4'):                 
                                            n.name = n.name.replace("_4", "_3")   
                                            n.label = n.label.replace("_4", "_3")   
                                            n.location.y += 2000   

                                    self.node_tree.links.new(layer2.outputs[0], layer4.inputs[1])   

                            if bpy.context.window_manager.my_toolqt.activelayer == 3: 
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith('_5'):                 
                                            n.name = n.name.replace("_5", "_4")   
                                            n.label = n.label.replace("_5", "_4")   
                                            n.location.y += 2000   

                                    self.node_tree.links.new(layer3.outputs[0], layer5.inputs[1])   
                                            
                            for n in self.nodes:
                                n.select = False
                            
                            for n in self.nodes:
                                if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    n.select = True

                            for n in self.nodes:
                                # ACTIVE LAYER                            
                                if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.core_shader = n
                                    self.final_node = n
                                    
                                if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.final_node = n
                                    
                                if n.name == 'Group Output':
                                    self.out_node = n

                                # coord
                                if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.tex_coord = n

                                # normal
                                if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_tex = n
                                if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_strength = n
                                    bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                                # mapping                                 
                                if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_mapping = n
                                if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_mapping = n
                                if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_mapping = n

                                # clamps
                                if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_clamp = n
                                if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.roughness_clamp = n
                                if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_clamp = n

                                # textures
                                if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_tex = n
                                if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_bright_contrast = n

                                if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_tex = n
                                if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_color_ramp = n
                                if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_invert = n
                                if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                                if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_tex = n
                                if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_color_ramp = n
                                if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bump = n
                                    bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                                if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_invert = n
                                if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                                # masks
                                if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_tex = n
                                if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_color_ramp = n
                                if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_invert = n
                                if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_mapping = n

                                # alpha
                                if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_mapping = n
                                if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_tex = n
                                if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_color_ramp = n
                                if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_invert = n
                                if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_clamp = n

                                # ao
                                if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_tex = n
                                if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_multiply = n
                                    bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                                # height
                                if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_power = n
                                    bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value
                                if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                
                                # blend
                                if bpy.context.window_manager.my_toolqt.blend:
                                    if n.name == ('QT_Blend_Add'):
                                        self.blend_add = n
                                    if n.name == ('QT_Blend_XYZ'):
                                        self.blend_xyz = n
                                    if n.name == ('QT_Blend_Math'):
                                        self.blend_math = n
                                    if n.name == ('QT_Blend_Power'):
                                        self.blend_power = n
                                    if n.name == ('QT_Blend_Clamp'):
                                        self.blend_clamp = n
                                    if n.name == ('QT_Blend_Mix'):
                                        self.blend_mix = n
                                    if n.name == ('QT_Blend_Noise'):
                                        self.blend_noise = n
                                        bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                        bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                        bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                    if n.name == ('QT_Blend_Bright_Contrast'):
                                        self.blend_bright_contrast = n
                                        bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value
                                    if n.name == 'QT_Blend_Mix':
                                        self.final_node = n
                                        self.core_shader = n 

                # DELETE MAP ONLY
                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0:    
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            backspace = 0
                            for n in self.nodes:
                                if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.nodes.remove(n)
                                    backspace = 1

                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_1'):
                                        self.final_node = n     
                                    if n.name.startswith('QT_Layer_2'):
                                        self.final_node = n  
                                    if n.name.startswith('QT_Layer_3'):
                                        self.final_node = n  
                                    if n.name.startswith('QT_Layer_4'):
                                        self.final_node = n  
                                    if n.name.startswith('QT_Layer_5'):
                                        self.final_node = n  
                                        
                                self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                                self.out_node.location.y = self.final_node.location.y
                                self.out_node.location.x = self.final_node.location.x + 300 

                                bpy.context.window_manager.my_toolqt.activemap = 1

                                for n in self.nodes:
                                    n.select = False
                                    if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        n.select = True

                    else:
                        backspace = 0
                        for n in self.mat.node_tree.nodes:
                            if n.name.startswith('QT_Blend'):
                                self.mat.node_tree.nodes.remove(n)
                                backspace = 1
                        
                        if backspace:
                            bpy.context.window_manager.my_toolqt.blend = 0

                            for n in self.mat.node_tree.nodes:
                                if n.name == 'QT_Output':
                                    self.out_material = n

                                if n.name.startswith('QT_Shader'):
                                    qtshader = n
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                            self.mat.node_tree.links.new(self.out_material.inputs[0], qtshader.outputs[0])         

            elif event.type == 'DEL' and event.value == 'RELEASE':

                if bpy.context.window_manager.my_toolqt.blend == 0:    
                    if bpy.context.window_manager.my_toolqt.activelayer > 1:

                        layer1 = None
                        layer2 = None
                        layer3 = None
                        layer4 = None
                        layer5 = None

                        for n in self.nodes:
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.nodes.remove(n)

                        bpy.context.window_manager.my_toolqt.activelayer -= 1

                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                self.final_node = n   

                        for n in self.nodes:
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n    
                                
                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300
                        
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                layer1 = n

                            if n.name.startswith('QT_Layer_2'):
                                layer2 = n

                            if n.name.startswith('QT_Layer_3'):
                                layer3 = n
                            
                            if n.name.startswith('QT_Layer_4'):
                                layer4 = n

                            if n.name.startswith('QT_Layer_5'):
                                layer5 = n

                        if bpy.context.window_manager.my_toolqt.activelayer == 1:
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith('_5'):                 
                                        n.name = n.name.replace("_5", "_4")   
                                        n.label = n.label.replace("_5", "_4")   
                                        n.location.y += 2000   
                            if layer4:
                                for n in self.nodes:
                                    if n.name.endswith('_4'):                 
                                        n.name = n.name.replace("_4", "_3")   
                                        n.label = n.label.replace("_4", "_3")   
                                        n.location.y += 2000   
                            if layer3:          
                                for n in self.nodes:
                                    if n.name.endswith('_3'):                 
                                        n.name = n.name.replace("_3", "_2")   
                                        n.label = n.label.replace("_3", "_2")   
                                        n.location.y += 2000    

                                self.node_tree.links.new(layer1.outputs[0], layer3.inputs[1])    
                                
                        if bpy.context.window_manager.my_toolqt.activelayer == 2:
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith('_5'):                 
                                        n.name = n.name.replace("_5", "_4")   
                                        n.label = n.label.replace("_5", "_4")   
                                        n.location.y += 2000   
                            if layer4:
                                for n in self.nodes:
                                    if n.name.endswith('_4'):                 
                                        n.name = n.name.replace("_4", "_3")   
                                        n.label = n.label.replace("_4", "_3")   
                                        n.location.y += 2000   

                                self.node_tree.links.new(layer2.outputs[0], layer4.inputs[1])   

                        if bpy.context.window_manager.my_toolqt.activelayer == 3: 
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith('_5'):                 
                                        n.name = n.name.replace("_5", "_4")   
                                        n.label = n.label.replace("_5", "_4")   
                                        n.location.y += 2000   

                                self.node_tree.links.new(layer3.outputs[0], layer5.inputs[1])   
                                        
                        for n in self.nodes:
                            n.select = False
                        
                        for n in self.nodes:
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True

                        for n in self.mat.node_tree.nodes:
                            if n.name == 'QT_Output':
                                self.out_material = n

                            if n.name.startswith('QT_Shader'):
                                self.nodes = n.node_tree.nodes
                                self.node_tree = n.node_tree

                            # blend only
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name.startswith('QT_Blend'):
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                        for n in self.nodes:
                            # ACTIVE LAYER                            
                            if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.core_shader = n
                                self.final_node = n
                                
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n
                                
                            if n.name == 'Group Output':
                                self.out_node = n

                            # coord
                            if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.tex_coord = n

                            # normal
                            if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.normal_tex = n
                            if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.normal_strength = n
                                bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                            # mapping                                 
                            if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_mapping = n
                            if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_mapping = n
                            if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_mapping = n

                            # clamps
                            if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_clamp = n
                            if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.roughness_clamp = n
                            if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_clamp = n

                            # textures
                            if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_tex = n
                            if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_hue_sat = n
                                bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value
                                bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value
                                bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value
                            if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_bright_contrast = n

                            if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_tex = n
                            if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_color_ramp = n
                            if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_invert = n
                            if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_hue_sat = n
                                bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                            if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_tex = n
                            if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_color_ramp = n
                            if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_bump = n
                                bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                            if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_invert = n
                            if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_hue_sat = n
                                bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                            # masks
                            if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_tex = n
                            if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_color_ramp = n
                            if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_invert = n
                            if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_hue_sat = n
                                bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value
                            if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_mapping = n

                            # alpha
                            if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_mapping = n
                            if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_tex = n
                            if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_color_ramp = n
                            if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_invert = n
                            if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_hue_sat = n
                                bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value
                            if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_clamp = n

                            # ao
                            if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.ao_tex = n
                            if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.ao_multiply = n
                                bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                            # height
                            if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.blend_power = n
                                bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value
                            if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.blend_noise = n
                                bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                            
                            # blend
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name == ('QT_Blend_Add'):
                                    self.blend_add = n
                                if n.name == ('QT_Blend_XYZ'):
                                    self.blend_xyz = n
                                if n.name == ('QT_Blend_Math'):
                                    self.blend_math = n
                                if n.name == ('QT_Blend_Power'):
                                    self.blend_power = n
                                if n.name == ('QT_Blend_Clamp'):
                                    self.blend_clamp = n
                                if n.name == ('QT_Blend_Mix'):
                                    self.blend_mix = n
                                if n.name == ('QT_Blend_Noise'):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                if n.name == ('QT_Blend_Bright_Contrast'):
                                    self.blend_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value
                                if n.name == 'QT_Blend_Mix':
                                    self.final_node = n
                                    self.core_shader = n 

            # ROTATE 90 DEGREES
            elif event.type == 'LEFT_BRACKET' and event.value == 'RELEASE':

                #if bpy.context.window_manager.my_toolqt.proc_uv:                            
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] -= pi/2 
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 
                        
                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 

                context.area.tag_redraw()
                
            elif event.type == 'RIGHT_BRACKET' and event.value == 'RELEASE':
                
                #if bpy.context.window_manager.my_toolqt.proc_uv:
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] += pi/2 
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 
                        
                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 

                context.area.tag_redraw()

            # ROTATE 90 DEGREES
            elif event.type == 'LEFT_ARROW' and event.value == 'RELEASE':

                #if bpy.context.window_manager.my_toolqt.proc_uv:             
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] -= pi/2 
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 
                        
                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 

                context.area.tag_redraw()
                
            elif event.type == 'RIGHT_ARROW' and event.value == 'RELEASE':
                
                #if bpy.context.window_manager.my_toolqt.proc_uv:
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] += pi/2 
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 
                        
                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 

                context.area.tag_redraw()

            # RESET SETTINGS
            elif event.type == 'K' and event.value == 'RELEASE':

                if self.tex_coord.label == 'Decal':
                    width, height = self.diffuse_tex.image.size
                    size = width/height

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

                self.alt = 0
                self.ctrl = 0
                self.shift = 0

                context.area.tag_redraw()
                
            elif event.type in {'MIDDLEMOUSE', 'RET'}:        
                return {'PASS_THROUGH'}
                                                            
            elif event.type == 'RIGHTMOUSE':
                return {'PASS_THROUGH'}           
                                                                                                                                                        
            elif event.type == 'WHEELUPMOUSE':
                return {'PASS_THROUGH'}
            
            elif event.type == 'WHEELDOWNMOUSE':
                return {'PASS_THROUGH'}
                                                                                                           
            elif event.type == 'ZERO':
                return {'PASS_THROUGH'}
                                
            elif event.type == 'SIX':
                return {'PASS_THROUGH'}

            elif event.type == 'SEVEN':
                return {'PASS_THROUGH'}
            
            elif event.type == 'EIGHT':
                return {'PASS_THROUGH'}
            
            elif event.type == 'NINE':
                return {'PASS_THROUGH'}
            
            elif event.type == 'NUMPAD_0':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_1':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_2':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_3':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_4':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_5':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_6':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_7':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_8':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_9':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_PERIOD':
                return {'PASS_THROUGH'}

            elif event.type == 'PERIOD':
                return {'PASS_THROUGH'}

            elif event.type == 'QUOTE':
                return {'PASS_THROUGH'}

            elif event.type == 'MINUS':
                return {'PASS_THROUGH'}

            elif event.type == 'PLUS':
                return {'PASS_THROUGH'}
            
            elif event.type == 'BACK_SLASH':
                return {'PASS_THROUGH'}

            elif event.type == 'EQUAL':
                return {'PASS_THROUGH'}
                                    
            elif event.type == 'NUMPAD_ASTERIX':
                return {'PASS_THROUGH'}

            elif event.type == 'COMMA':
                return {'PASS_THROUGH'}

            elif event.type == 'F3':
                return {'PASS_THROUGH'}

            elif event.type == 'PAUSE':
                return {'PASS_THROUGH'}

            elif event.type == 'INSERT':
                return {'PASS_THROUGH'}

            elif event.type == 'HOME':
                return {'PASS_THROUGH'}

            elif event.type == 'PAGE_UP':
                return {'PASS_THROUGH'}

            elif event.type == 'PAGE_DOWN':
                return {'PASS_THROUGH'}

            elif event.type == 'END':
                return {'PASS_THROUGH'}

            elif event.type == 'F' and event.value == 'PRESS': 
                if event.ctrl or event.shift:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {'PASS_THROUGH'}

            elif event.type == 'X' and event.value == 'PRESS': 
                if event.ctrl:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {'PASS_THROUGH'}

                if event.ctrl and event.shift:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {'PASS_THROUGH'}

            elif event.ctrl and event.shift and event.type == 'D' and event.value == 'PRESS': 
                self.shift = 0
                bpy.context.window_manager.my_toolqt.running_qt = 0
                bpy.context.window_manager.my_toolqt.decal = 1
                bpy.context.window_manager.my_toolqt.selected = 0
                bpy.context.window_manager.my_toolqt.blend = 0
                bpy.context.window_manager.my_toolqt.mask = 0
                bpy.context.window_manager.my_toolqt.ob = None
                bpy.data.collections['QuickTexture'].hide_viewport=True
                bpy.data.collections['QuickTexture'].hide_render=True
                bpy.ops.object.quickdecal('INVOKE_DEFAULT')

    # UNDO - restore stuff that I don't want changed
            elif event.type == 'Z' and event.value == 'PRESS':                    
                return {'PASS_THROUGH'}
            
            if event.type == 'ESC':
                return {'PASS_THROUGH'}
                                                                
            if event.type == 'ACCENT_GRAVE':
                return {'PASS_THROUGH'}
            
    # EXIT
            if event.type == 'T' and event.value == 'PRESS':

                if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                    return {'PASS_THROUGH'}

                elif event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                    context.area.tag_redraw() 
                    if self.nodes is not None:

                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                self.final_node = n   

                        for n in self.nodes:
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n    

                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300     

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True
                                                    
                    bpy.context.window_manager.my_toolqt.decal = 0
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    bpy.context.window_manager.my_toolqt.selected = 0
                    bpy.context.window_manager.my_toolqt.blend = 0
                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.ob = None
                    bpy.data.collections['QuickTexture'].hide_viewport=True
                    bpy.data.collections['QuickTexture'].hide_render=True
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    return {'FINISHED'}

            return {'RUNNING_MODAL'}
            
        except:
            if self.nodes:
                for n in self.nodes:
                    if n.name.startswith('QT_Shader_1'):
                        self.final_node = n     
                    if n.name.startswith('QT_Layer_2'):
                        self.final_node = n  
                    if n.name.startswith('QT_Layer_3'):
                        self.final_node = n  
                    if n.name.startswith('QT_Layer_4'):
                        self.final_node = n  
                    if n.name.startswith('QT_Layer_5'):
                        self.final_node = n  
                self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])            
            bpy.context.window_manager.my_toolqt.running_qt = 0
            bpy.context.window_manager.my_toolqt.selected = 0
            bpy.context.window_manager.my_toolqt.decal = 0
            bpy.context.window_manager.my_toolqt.blend = 0
            bpy.context.window_manager.my_toolqt.mask = 0
            bpy.context.window_manager.my_toolqt.ob = None
            bpy.data.collections['QuickTexture'].hide_viewport=True
            bpy.data.collections['QuickTexture'].hide_render=True
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            traceback.print_exc()
            return {'FINISHED'}

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

        if len(sel) > 0:

            for ob in sel:
                if ob.type not in ['CURVE', 'META', 'MESH']: 
                    return {'FINISHED'}

                if ob.type in ['CURVE', 'META']:
                    bpy.ops.object.convert(target='MESH')
                    sel = bpy.context.selected_objects   

            ob = sel[0]
            ob2 = bpy.context.view_layer.objects.active
            bpy.context.window_manager.my_toolqt.ob = sel[0]
            bpy.context.window_manager.my_toolqt.selected = 1

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
        self.rough_color_ramp = None
        self.rough_bright_contrast = None
        self.rough_invert = None
        self.rough_hue_sat = None
        self.bump_tex = None
        self.bump_color_ramp = None
        self.bump_bright_contrast = None
        self.bump_bump = None
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
        self.alpha_color_ramp = None
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
            self.collection = bpy.data.collections['QuickTexture']
            bpy.data.collections['QuickTexture'].hide_viewport=False
            bpy.data.collections['QuickTexture'].hide_render=False
        else:
            self.collection = objects.make_collection("QuickTexture", context)

        collections = bpy.context.view_layer.layer_collection.children
        for collection in collections:
            if collection.name == 'QuickTexture':
                if collection.hide_viewport == True:
                    collection.hide_viewport = False

        # view
        self.view_vector = Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
        self.window_active, self.zoomlevel = utils.window_info(context, event, bpy.context.preferences.addons[__package__].preferences.window_buffer)
        self.regX = bpy.context.region.width
        self.regY = bpy.context.region.height
                
        # shading style        
        areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
        self.viewlens = 50/(areas[0].spaces[0].lens)     

        # hotkeys
        self.coord = Vector((event.mouse_region_x,event.mouse_region_y))
        self.coord_firstclick = Vector((0,0))
        self.coord_lastclick = Vector((0,0))
        self.coord_hotkeyclick = Vector((0,0))
        self.avg_2d = Vector((0,0))     

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
        self.ashift = False
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
        
        args = (self, context) 
        wm = context.window_manager
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_quickTexture, args, 'WINDOW', 'POST_PIXEL')
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
                        if n.name.startswith('QT_Blend'):
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
                            if n.name.startswith('QT_Shader'):
                                node_group_name = n.name
                                material1 = mat

                # this is the active obj im working on
                for mat in ob2.data.materials:
                    if mat:
                        for n in mat.node_tree.nodes:
                            if n.name.startswith('QT_Shader'):
                                shader_node = n
                                material2 = mat

                            if n.name.startswith('QT_Output'):
                                out_mat = n
                                
        if material1 and material2:
            bpy.context.window_manager.my_toolqt.blend = 1
            objects.blend(self, context, material2, shader_node, out_mat, node_group_name)

        else:            
            if material1 == 0 and material2 == 0:                          
                importbrowser = 1
                # check if QT material exists
                if ob:
                    if ob.data.materials:
                        for mat in ob.data.materials:
                            if mat:
                                importbrowser = 0
                                if mat.name.startswith("QT"):
                                    for n in mat.node_tree.nodes:
                                        if n.name == 'QT_Output':
                                            self.out_material = n
                                        if n.name.startswith('QT_Shader'):
                                            self.nodes = n.node_tree.nodes
                                            self.node_tree = n.node_tree

                                    # set active layer based on latest layer if exists
                                    for n in self.nodes:
                                        if n.name.startswith('QT_Shader_1'):
                                            bpy.context.window_manager.my_toolqt.activelayer = 1  
                                            self.final_node = n    
                                        if n.name.startswith('QT_Layer_2'):
                                            bpy.context.window_manager.my_toolqt.activelayer = 2
                                            self.final_node = n    
                                        if n.name.startswith('QT_Layer_3'):
                                            bpy.context.window_manager.my_toolqt.activelayer = 3
                                            self.final_node = n    
                                        if n.name.startswith('QT_Layer_4'):
                                            bpy.context.window_manager.my_toolqt.activelayer = 4
                                            self.final_node = n    
                                        if n.name.startswith('QT_Layer_5'):
                                            bpy.context.window_manager.my_toolqt.activelayer = 5  
                                            self.final_node = n                                          
                                        if n.name == 'Group Output':
                                            self.out_node = n

                                    self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                                    self.out_node.location.y = self.final_node.location.y
                                    self.out_node.location.x = self.final_node.location.x + 300     

                                    for n in self.nodes:
                                        n.select = False
                                        if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                            n.select = True

                                    for n in self.nodes:
                                        if n.select:
                                            if n.name.startswith('QT_UV_Layer_' + (str(bpy.context.window_manager.my_toolqt.activelayer))):

                                                if n.label == 'Decal' or n.label == 'View':
                                                    bpy.context.window_manager.my_toolqt.proc_uv = 1 

                                                if n.label == 'Box':
                                                    bpy.context.window_manager.my_toolqt.proc_uv = 1                                 

                                # remake material QuickTexture style
                                else:

                                    albedo_spec = None
                                    roughness_spec = None
                                    normal_spec = None
                                    ao_spec = None
                                    alpha_spec = None

                                    for n in mat.node_tree.nodes:
                                        if n.type == 'TEX_IMAGE':

                                            if albedo_spec == None:
                                                if 'albedo' in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[n.image.name]     
                                                if 'diffuse' in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[n.image.name]    
                                                if 'color' in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[n.image.name]   
                                                if 'col' in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[n.image.name]   
                                                if 'basecolor' in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[n.image.name]   
                                                if 'basecol' in str(n.image.name).lower():
                                                    albedo_spec = bpy.data.images[n.image.name]   

                                            if roughness_spec == None:
                                                if 'roughness' in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[n.image.name]     
                                                if 'rough' in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[n.image.name]     
                                                if 'glossiness' in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[n.image.name]    
                                                if 'gloss' in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[n.image.name]    
                                                if 'spec' in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[n.image.name]     
                                                if 'specular' in str(n.image.name).lower():
                                                    roughness_spec = bpy.data.images[n.image.name]     

                                            if normal_spec == None:
                                                if 'normal' in str(n.image.name).lower():
                                                    normal_spec = bpy.data.images[n.image.name]     
                                                if 'norm' in str(n.image.name).lower():
                                                    normal_spec = bpy.data.images[n.image.name]     
                                                if 'nrm' in str(n.image.name).lower():
                                                    normal_spec = bpy.data.images[n.image.name] 

                                            if alpha_spec == None:
                                                if 'opacity' in str(n.image.name).lower():
                                                    alpha_spec = bpy.data.images[n.image.name]     
                                                if 'opac' in str(n.image.name).lower():
                                                    alpha_spec = bpy.data.images[n.image.name]     
                                                if 'alpha' in str(n.image.name).lower():
                                                    alpha_spec = bpy.data.images[n.image.name]     

                                            if ao_spec == None:
                                                if 'ao' in str(n.image.name).lower():
                                                    ao_spec = bpy.data.images[n.image.name]     
                                                if 'ambientocclusion' in str(n.image.name).lower():
                                                    ao_spec = bpy.data.images[n.image.name]     

                                    if albedo_spec:
                                        objects.remake_material(ob, albedo_spec, roughness_spec, normal_spec, alpha_spec, ao_spec)
                                    else:
                                        importbrowser = 1
                
                if importbrowser:
                    # check if object has proc uv
                    hasproc = 0
                    if ob:
                        if len(ob.data.uv_layers)>0:
                            for layer in ob.data.uv_layers:
                                if layer.name.startswith('QT_UV'):
                                    hasproc = 1
                        else:
                            hasproc = 1

                    if hasproc:
                        bpy.context.window_manager.my_toolqt.proc_uv = 1
                    else:
                        bpy.context.window_manager.my_toolqt.proc_uv = 0

                    bpy.ops.qt.material_qt('INVOKE_DEFAULT')

            else:
                bpy.context.window_manager.my_toolqt.running_qt = 0
        
        return {'RUNNING_MODAL'}

class QT_OT_material_qt(Operator, ImportHelper):
    bl_idname = 'qt.material_qt'
    bl_label = 'Create Material'
    bl_options = {'PRESET', 'UNDO'}

    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
  
    def execute(self, context):

        # SHADER
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects   
        if len(sel)>0:
            ob = sel[0]
            dirname = os.path.dirname(self.filepath)

            if len(self.files) == 0:
                bpy.context.window_manager.my_toolqt.running_qt = 0 
                return {'FINISHED'}
            elif len(self.files) == 1:
                f = self.files[0]  
                img_path = (os.path.join(dirname, f.name))
                
                bpy.ops.image.open( filepath = img_path )
                bpy.data.images[f.name].filepath = img_path

            elif len(self.files) > 1:   
                f = self.files[0] 
                for x in self.files:
                    if 'albedo' in str(x.name).lower():
                        f = x
                    if 'diffuse' in str(x.name).lower():
                        f = x
                    if 'color' in str(x.name).lower():
                        f = x
                    if 'col' in str(x.name).lower():
                        f = x
                    if 'basecolor' in str(x.name).lower():
                        f = x
                    if 'basecol' in str(x.name).lower():
                        f = x
                    img_path = (os.path.join(dirname, f.name))

                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    
            img_spec = bpy.data.images[f.name]                
            material = objects.create_material(self, context, img_spec, 0, bpy.context.window_manager.my_toolqt.mode, bpy.context.window_manager.my_toolqt.proc_uv, self.files, dirname, bpy.context.window_manager.my_toolqt.decal, bpy.context.window_manager.my_toolqt.selected)
            bpy.context.window_manager.my_toolqt.selected = 1

        # REFERENCE 
        else:            
            bpy.context.window_manager.my_toolqt.running_qt = 0
            bpy.context.window_manager.my_toolqt.proc_uv = 1
            dirname = os.path.dirname(self.filepath)
            
            for f in self.files:
                if len(self.files) == 0:
                    bpy.context.window_manager.my_toolqt.running_qt = 0 
                    return {'FINISHED'}
                elif len(self.files) == 1:
                    f = self.files[0]  
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                elif len(self.files) > 1:   
                    f = self.files[0] 
                    for x in self.files:
                        if 'albedo' in str(x.name).lower():
                            f = x
                        if 'diffuse' in str(x.name).lower():
                            f = x
                        if 'color' in str(x.name).lower():
                            f = x
                        if 'col' in str(x.name).lower():
                            f = x
                        if 'basecolor' in str(x.name).lower():
                            f = x
                        if 'basecol' in str(x.name).lower():
                            f = x
                        img_path = (os.path.join(dirname, f.name))
                        bpy.ops.image.open( filepath = img_path )      
                        bpy.data.images[f.name].filepath = img_path          
            
            img_spec = bpy.data.images[f.name]
            ob = objects.create_image_plane(self, context, f.name, img_spec)
            material = objects.create_material(self, context, img_spec, 1, bpy.context.window_manager.my_toolqt.mode, bpy.context.window_manager.my_toolqt.proc_uv, self.files, dirname, bpy.context.window_manager.my_toolqt.decal, bpy.context.window_manager.my_toolqt.selected)
            bpy.context.window_manager.my_toolqt.ob = ob

            for layer in ob.data.uv_layers: 
                if layer.name == 'UVMap':
                    ob.data.uv_layers.remove(layer) 
        
        # setup params        
        material.name = 'QT_' + material.name
        if ob.data.materials:
            ob.data.materials[0] = material
        else:
            ob.data.materials.append(material)

        bpy.ops.object.make_links_data(type='MATERIAL')

        px, py = img_spec.size
        if px == 0:
            px = 1000
        if py == 0:
            py = 1000
        size = px/py
        bpy.context.window_manager.my_toolqt.activelayer = 1
        bpy.context.window_manager.my_toolqt.activemap = 1

        # material settings
        material.blend_method = 'HASHED'
        material.shadow_method = 'HASHED'
        material.use_screen_refraction = True
        material.show_transparent_back = False

        if bpy.context.window_manager.my_toolqt.proc_uv:
            newlayer = 0

            if bpy.context.window_manager.my_toolqt.mode == 'view' or bpy.context.window_manager.my_toolqt.decal:
                layer = bpy.context.window_manager.my_toolqt.ob.data.uv_layers.get('QT_UV_View_Layer_1')
                if layer is None:
                    newlayer = 1
                    uvname = 'QT_UV_View_Layer_1'           
                    ob.data.uv_layers.new(name=uvname)
                    ob.data.uv_layers[uvname].active = True
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action='SELECT')   
                    bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=True, scale_to_bounds=False)
                    bpy.ops.object.editmode_toggle()
            
            else:
                layer = bpy.context.window_manager.my_toolqt.ob.data.uv_layers.get('QT_UV_Box_Layer_1')
                if layer is None:
                    newlayer = 1
                    uvname = 'QT_UV_Box_Layer_1'           
                    ob.data.uv_layers.new(name=uvname)
                    ob.data.uv_layers[uvname].active = True
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action='SELECT')   
                    bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=True, scale_to_bounds=False)
                    bpy.ops.object.editmode_toggle()
                                
            if newlayer and bpy.context.window_manager.my_toolqt.mode == 'box':
                # PROJECTION SETUP
                empty_uv1 = objects.create_empty('QT_UV_Z_Plus', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
                empty_uv2 = objects.create_empty('QT_UV_Z_Min', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
                empty_uv3 = objects.create_empty('QT_UV_Y_Plus', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
                empty_uv4 = objects.create_empty('QT_UV_Y_Min', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
                empty_uv5 = objects.create_empty('QT_UV_X_Plus', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
                empty_uv6 = objects.create_empty('QT_UV_X_Min', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)                    
                col = bpy.data.collections['QuickTexture']
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
                empty_uv3.rotation_euler.x = -pi/2  
                empty_uv3.rotation_euler.y = pi
                empty_uv4.rotation_euler.x = pi/2     

                # X
                empty_uv5.rotation_euler.z = pi/2
                empty_uv5.rotation_euler.x = pi/2    

                empty_uv6.rotation_euler.z = -pi/2
                empty_uv6.rotation_euler.x = pi/2     

                mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get('QT_UV_Box')
                if mod is None:
                    rmod1 = ob.modifiers.new(name='QT_UV_Box', type='UV_PROJECT') 
                    rmod1.projector_count = 6
                    rmod1.projectors[0].object = bpy.data.objects[empty_uv1.name]
                    rmod1.projectors[1].object = bpy.data.objects[empty_uv2.name]
                    rmod1.projectors[2].object = bpy.data.objects[empty_uv3.name]
                    rmod1.projectors[3].object = bpy.data.objects[empty_uv4.name]
                    rmod1.projectors[4].object = bpy.data.objects[empty_uv5.name]
                    rmod1.projectors[5].object = bpy.data.objects[empty_uv6.name]
                    rmod1.uv_layer = 'QT_UV_Box_Layer_1'

            if bpy.context.window_manager.my_toolqt.mode == 'view' or bpy.context.window_manager.my_toolqt.decal:  
                empty_ob = objects.create_empty('QT_UV_View_1', 'SINGLE_ARROW', Vector((0,0,0)), context, 0)
                col = bpy.data.collections['QuickTexture']
                objects.add_to_collection(empty_ob.name, col, context)

                if len(sel)>0:
                    empty_ob.rotation_euler = context.region_data.view_rotation.to_euler()
                else:
                    empty_ob.rotation_euler.x = pi/2

                rmod1 = ob.modifiers.new(name='QT_UV_View_1', type='UV_PROJECT') 
                rmod1.projector_count = 1
                rmod1.projectors[0].object = bpy.data.objects[empty_ob.name]

                rmod1.uv_layer = 'QT_UV_View_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)

                local_bbox_center = 0.125 * sum((Vector(b) for b in ob.bound_box), Vector())
                global_bbox_center = ob.matrix_world @ local_bbox_center
                empty_ob.location = global_bbox_center
            
            # parenting                                
            bpy.ops.object.select_all(action='DESELECT')
            
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
                bpy.ops.object.parent_set(type='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')

                bpy.data.objects[empty_ob.name].select_set(True)
                bpy.context.view_layer.objects.active = empty_ob
                bpy.context.object.hide_viewport = True
                bpy.context.object.hide_render = True
                bpy.context.object.hide_select = True
                
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[ob.name].select_set(True)
                bpy.context.view_layer.objects.active = ob

            else:
                if bpy.context.window_manager.my_toolqt.mode == 'view' and len(sel) == 0 or bpy.context.window_manager.my_toolqt.decal and len(sel) == 0:
                    bpy.data.objects[empty_ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = empty_ob

                    bpy.context.object.hide_viewport = False
                    bpy.context.object.hide_render = False
                    bpy.context.object.hide_select = False

                    bpy.data.objects[empty_ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = empty_ob
                
                    bpy.data.objects[ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = ob
                    bpy.ops.object.parent_set(type='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')

                    bpy.data.objects[empty_ob.name].select_set(True)
                    bpy.context.view_layer.objects.active = empty_ob
                    bpy.context.object.hide_viewport = True
                    bpy.context.object.hide_render = True
                    bpy.context.object.hide_select = True

        bpy.ops.object.select_all(action='DESELECT')
        
        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob
                        
        return {'FINISHED'}

class QT_OT_boxlayer_qt(Operator, ImportHelper):
    bl_idname = 'qt.boxlayer_qt'
    bl_label = 'New Box Layer Texture'
    bl_options = {'PRESET', 'UNDO'}

    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
  
    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects   
        ob = sel[0]     
                                                             
        bpy.context.window_manager.my_toolqt.activelayer += 1
        dirname = os.path.dirname(self.filepath)

        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0 
            return {'FINISHED'}
        elif len(self.files) == 1:
            f = self.files[0]  
            img_path = (os.path.join(dirname, f.name))
            bpy.ops.image.open( filepath = img_path )
            bpy.data.images[f.name].filepath = img_path
        elif len(self.files) > 1:   
            f = self.files[0] 
            for x in self.files:
                if 'albedo' in str(x.name).lower():
                    f = x
                if 'diffuse' in str(x.name).lower():
                    f = x
                if 'color' in str(x.name).lower():
                    f = x
                if 'col' in str(x.name).lower():
                    f = x
                if 'basecolor' in str(x.name).lower():
                    f = x
                if 'basecol' in str(x.name).lower():
                    f = x
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]      
        width, height = img_spec.size
        size = width/height
        bpy.context.window_manager.my_toolqt.activemap = 1
        
        layer2 = bpy.context.window_manager.my_toolqt.ob.data.uv_layers.get('QT_UV_Box_Layer_1')
        if not layer2:
            uvname = 'QT_UV_Box_Layer_1'           
            ob.data.uv_layers.new(name=uvname)
            ob.data.uv_layers[uvname].active = True

        bpy.context.window_manager.my_toolqt.proc_uv = 1
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')   
        bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.editmode_toggle()

        # PROJECTION SETUP
        empty_uv1 = None
        empty_uv1 = objects.create_empty('QT_UV_Z_Plus', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
        empty_uv2 = objects.create_empty('QT_UV_Z_Min', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
        empty_uv3 = objects.create_empty('QT_UV_Y_Plus', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
        empty_uv4 = objects.create_empty('QT_UV_Y_Min', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
        empty_uv5 = objects.create_empty('QT_UV_X_Plus', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)
        empty_uv6 = objects.create_empty('QT_UV_X_Min', 'SINGLE_ARROW', Vector((0,0,0)), context, 1)                    
        col = bpy.data.collections['QuickTexture']

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
            empty_uv3.rotation_euler.x = -pi/2  
            empty_uv3.rotation_euler.y = pi
            empty_uv4.rotation_euler.x = pi/2     

            # X
            empty_uv5.rotation_euler.z = pi/2
            empty_uv5.rotation_euler.x = pi/2    

            empty_uv6.rotation_euler.z = -pi/2
            empty_uv6.rotation_euler.x = pi/2     

        mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get('QT_UV_Box')
        if mod is None:
            rmod1 = ob.modifiers.new(name='QT_UV_Box', type='UV_PROJECT') 
            rmod1.projector_count = 6
            rmod1.projectors[0].object = bpy.data.objects[empty_uv1.name]
            rmod1.projectors[1].object = bpy.data.objects[empty_uv2.name]
            rmod1.projectors[2].object = bpy.data.objects[empty_uv3.name]
            rmod1.projectors[3].object = bpy.data.objects[empty_uv4.name]
            rmod1.projectors[4].object = bpy.data.objects[empty_uv5.name]
            rmod1.projectors[5].object = bpy.data.objects[empty_uv6.name]
            rmod1.uv_layer = 'QT_UV_Box_Layer_1'
        
        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob

        objects.box_layer(self, context, img_spec, ob.data.materials[0], bpy.context.window_manager.my_toolqt.activelayer, self.files, dirname, bpy.context.window_manager.my_toolqt.decal, bpy.context.window_manager.my_toolqt.selected)
                        
        return {'FINISHED'}

class QT_OT_viewlayer_qt(Operator, ImportHelper):
    bl_idname = 'qt.viewlayer_qt'
    bl_label = 'New View Layer Texture'
    bl_options = {'PRESET', 'UNDO'}

    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
  
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

        mod2 = bpy.context.window_manager.my_toolqt.ob.modifiers.get('QT_UV_View_2')
        mod3 = bpy.context.window_manager.my_toolqt.ob.modifiers.get('QT_UV_View_3')
        mod4 = bpy.context.window_manager.my_toolqt.ob.modifiers.get('QT_UV_View_4')
        
        for n in ob.data.uv_layers:
            if n.name.startswith('QT_UV_View_Layer_2'):
                layer2 = n
            if n.name.startswith('QT_UV_View_Layer_3'):
                layer3 = n
            if n.name.startswith('QT_UV_View_Layer_4'):
                layer4 = n

        if bpy.context.window_manager.my_toolqt.activelayer == 2 and layer2:
            # UV 
            for n in ob.data.uv_layers:                
                if n.name.startswith('QT_UV_View_Layer_4'):
                    n.name = 'QT_UV_View_Layer_5'
                if n.name.startswith('QT_UV_View_Layer_3'):
                    n.name = 'QT_UV_View_Layer_4'
                if n.name.startswith('QT_UV_View_Layer_2'):
                    n.name = 'QT_UV_View_Layer_3'

            # MODIFIERS
            if mod4:
                mod4.name = 'QT_UV_View_5'
                mod4.uv_layer = 'QT_UV_View_Layer_5'
                ob4 = mod4.projectors[0].object
            if mod3:
                mod3.name = 'QT_UV_View_4'
                mod3.uv_layer = 'QT_UV_View_Layer_4'
                ob3 = mod3.projectors[0].object
            if mod2:
                mod2.name = 'QT_UV_View_3'
                mod2.uv_layer = 'QT_UV_View_Layer_3'
                ob2 = mod2.projectors[0].object
                
            # OBJECTS
            if ob4:
                ob4.name = 'QT_UV_View_5'

            if ob3:
                ob3.name = 'QT_UV_View_4'

            if ob2:
                ob2.name = 'QT_UV_View_3'

        if bpy.context.window_manager.my_toolqt.activelayer == 3 and layer3:
            # UV 
            for n in ob.data.uv_layers:                
                if n.name.startswith('QT_UV_View_Layer_4'):
                    n.name = 'QT_UV_View_Layer_5'
                if n.name.startswith('QT_UV_View_Layer_3'):
                    n.name = 'QT_UV_View_Layer_4'

            # MODIFIERS
            if mod4:
                mod4.name = 'QT_UV_View_5'
                mod4.uv_layer = 'QT_UV_View_Layer_5'
                ob4 = mod4.projectors[0].object
            if mod3:
                mod3.name = 'QT_UV_View_4'
                mod3.uv_layer = 'QT_UV_View_Layer_4'
                ob3 = mod3.projectors[0].object

            # OBJECTS
            if ob4:
                ob4.name = 'QT_UV_View_5'

            if ob3:
                ob3.name = 'QT_UV_View_4'

        if bpy.context.window_manager.my_toolqt.activelayer == 4 and layer4:
            # UV 
            for n in ob.data.uv_layers:                
                if n.name.startswith('QT_UV_View_4'):
                    n.name = 'QT_UV_View_5'

            # MODIFIERS
            if mod4:
                mod4.name = 'QT_UV_View_5'
                mod4.uv_layer = 'QT_UV_View_Layer_5'
                ob4 = mod4.projectors[0].object
                
            # OBJECTS
            if ob4:
                ob4.name = 'QT_UV_View_5'

        bpy.context.window_manager.my_toolqt.proc_uv = 1

        uvname = 'QT_UV_View_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)                
        ob.data.uv_layers.new(name=uvname)

        empty_ob = objects.create_empty(uvname, 'SINGLE_ARROW', Vector((0,0,0)), context, 0)
        col = bpy.data.collections['QuickTexture']
        objects.add_to_collection(empty_ob.name, col, context)
        empty_ob.rotation_euler = context.region_data.view_rotation.to_euler()

        local_bbox_center = 0.125 * sum((Vector(b) for b in ob.bound_box), Vector())
        global_bbox_center = ob.matrix_world @ local_bbox_center
        empty_ob.location = global_bbox_center
         
        rmod1 = ob.modifiers.new(name=uvname, type='UV_PROJECT')
        rmod1.projector_count = 1
        rmod1.projectors[0].object = bpy.data.objects[empty_ob.name]
        rmod1.uv_layer = 'QT_UV_View_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)
        
        # parenting                                
        bpy.ops.object.select_all(action='DESELECT')

        bpy.data.objects[empty_ob.name].select_set(True)
        bpy.context.view_layer.objects.active = empty_ob

        bpy.context.object.hide_viewport = False
        bpy.context.object.hide_render = False
        bpy.context.object.hide_select = False

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[empty_ob.name].select_set(True)
        bpy.context.view_layer.objects.active = empty_ob
        
        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.parent_set(type='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        bpy.data.objects[empty_ob.name].select_set(True)
        bpy.context.view_layer.objects.active = empty_ob
        bpy.context.object.hide_viewport = True
        bpy.context.object.hide_render = True
        bpy.context.object.hide_select = True

        bpy.ops.object.select_all(action='DESELECT')
        
        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob

        #########################################################################
        
        dirname = os.path.dirname(self.filepath)
        if len(self.files) == 0:
            bpy.context.window_manager.my_toolqt.running_qt = 0 
            return {'FINISHED'}
        elif len(self.files) == 1:
            f = self.files[0]  
            img_path = (os.path.join(dirname, f.name))
            bpy.ops.image.open( filepath = img_path )
            bpy.data.images[f.name].filepath = img_path
        elif len(self.files) > 1:   
            f = self.files[0] 
            for x in self.files:
                if 'albedo' in str(x.name).lower():
                    f = x
                if 'diffuse' in str(x.name).lower():
                    f = x
                if 'color' in str(x.name).lower():
                    f = x
                if 'col' in str(x.name).lower():
                    f = x
                if 'basecolor' in str(x.name).lower():
                    f = x
                if 'basecol' in str(x.name).lower():
                    f = x
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                bpy.data.images[f.name].filepath = img_path
        
        img_spec = bpy.data.images[f.name]      
        width, height = img_spec.size
        size = width/height
        bpy.context.window_manager.my_toolqt.activemap = 1
        objects.view_layer(self, context, img_spec, ob.data.materials[0], bpy.context.window_manager.my_toolqt.activelayer, self.files, dirname, bpy.context.window_manager.my_toolqt.decal, bpy.context.window_manager.my_toolqt.selected)
                        
        return {'FINISHED'}

class QT_OT_texturemask_qt(Operator, ImportHelper):
    bl_idname = 'qt.texturemask_qt'
    bl_label = 'New Texture Mask Texture'
    bl_options = {'PRESET', 'UNDO'}

    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
  
    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects   
        ob = sel[0]
        dirname = os.path.dirname(self.filepath)

        if len(self.files) > 0:
            f = self.files[0]
            img_path = (os.path.join(dirname, f.name)) #get filepath properties from collection pointer  
            bpy.ops.image.open( filepath = img_path )
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]      
            width, height = img_spec.size
            size = width/height
            bpy.context.window_manager.my_toolqt.activemap = 4
            objects.texture_mask(self, context, img_spec, ob.data.materials[0], bpy.context.window_manager.my_toolqt.activelayer, bpy.context.window_manager.my_toolqt.proc_uv)
                        
        return {'FINISHED'}

class QT_OT_depthmask_qt(Operator, ImportHelper):
    bl_idname = 'qt.depthmask_qt'
    bl_label = 'New Depth Mask Texture'
    bl_options = {'PRESET', 'UNDO'}

    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
  
    def execute(self, context):

        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        sel = bpy.context.selected_objects   
        ob = sel[0]
        dirname = os.path.dirname(self.filepath)

        if len(self.files) > 0:
            f = self.files[0]
            img_path = (os.path.join(dirname, f.name)) #get filepath properties from collection pointer  
            bpy.ops.image.open( filepath = img_path )
            bpy.data.images[f.name].filepath = img_path
            img_spec = bpy.data.images[f.name]      
            width, height = img_spec.size
            size = width/height
            bpy.context.window_manager.my_toolqt.activemap = 4
            objects.depth_mask(self, context, img_spec, ob.data.materials[0], bpy.context.window_manager.my_toolqt.activelayer, bpy.context.window_manager.my_toolqt.proc_uv)
  
        return {'FINISHED'}

class QT_OT_heightmask_qt(Operator):
    bl_idname = 'qt.heightmask_qt'
    bl_label = 'New Height Mask Texture'
    bl_options = {'PRESET', 'UNDO'}
  
    def execute(self, context):

        sel = bpy.context.selected_objects   
        ob = sel[0]
        bpy.context.window_manager.my_toolqt.activemap = 4
        bpy.context.window_manager.my_toolqt.mask = 1
        objects.height_mask(self, context, ob.data.materials[0], bpy.context.window_manager.my_toolqt.activelayer)
                       
        return {'FINISHED'}

class QT_OT_normalmask_qt(Operator):
    bl_idname = 'qt.normalmask_qt'
    bl_label = 'Normal Mask'
    bl_options = {'PRESET', 'UNDO'}
  
    def execute(self, context):

        sel = bpy.context.selected_objects   
        ob = sel[0]
        bpy.context.window_manager.my_toolqt.activemap = 4
        bpy.context.window_manager.my_toolqt.mask = 1
        objects.normal_mask(self, context, ob.data.materials[0], bpy.context.window_manager.my_toolqt.activelayer)
                        
        return {'FINISHED'}

class QT_OT_replacemaps_qt(Operator, ImportHelper):
    bl_idname = 'qt.replacemaps'
    bl_label = 'Replace Texture'
    bl_options = {'PRESET', 'UNDO'}

    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
  
    def execute(self, context):
        
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        f = self.files[0]
        img_path = (os.path.join(dirname, f.name)) #get filepath properties from collection pointer  
        bpy.ops.image.open( filepath = img_path )
        bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]           

        width, height = img_spec.size
        size = width/height

        nodes = None
        node_tree = None
    
        sel = bpy.context.selected_objects   
        ob = sel[0]     
        mat = ob.material_slots[0].material

        for n in mat.node_tree.nodes:        
            if n.name.startswith('QT_Shader'):
                nodes = n.node_tree.nodes
                node_tree = n.node_tree

        diffuse_mapping = None
        rough_mapping = None
        bump_mapping = None
        mask_mapping = None
        alpha_mapping = None

        diffuse_tex = None
        rough_tex = None
        bump_tex = None
        mask_tex = None
        normal_tex = None
        alpha_tex = None
        ao_tex = None

        albedo_spec = None
        roughness_spec = None
        normal_spec = None
        ao_spec = None
        alpha_spec = None

        if len(self.files) > 1:
            for f in self.files:
                if 'albedo' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]     
                if 'diffuse' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]    
                if 'diff' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]    
                if 'color' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]   
                if 'col' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]   
                if 'basecolor' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]   
                if 'basecol' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    albedo_spec = bpy.data.images[f.name]   
                if 'roughness' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]     
                if 'rough' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]     
                if 'glossiness' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]    
                if 'gloss' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]    
                if 'spec' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]     
                if 'specular' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    roughness_spec = bpy.data.images[f.name]     
                if 'normal' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]     
                if 'norm' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]     
                if 'nor' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]    
                if 'nmap' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name] 
                if 'nrm' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    normal_spec = bpy.data.images[f.name]     
                if 'opacity' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    alpha_spec = bpy.data.images[f.name]     
                if 'opac' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    alpha_spec = bpy.data.images[f.name]     
                if 'alpha' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    alpha_spec = bpy.data.images[f.name]     
                if 'ao' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    ao_spec = bpy.data.images[f.name]     
                if 'ambientocclusion' in str(f.name).lower():
                    img_path = (os.path.join(dirname, f.name))
                    bpy.ops.image.open( filepath = img_path )
                    bpy.data.images[f.name].filepath = img_path
                    ao_spec = bpy.data.images[f.name]     

        if nodes:
            for n in nodes:
                if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    diffuse_mapping = n
                if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    rough_mapping = n
                if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    bump_mapping = n
                if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    mask_mapping = n
                if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    mask_clamp = n
                if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    alpha_mapping = n
                    
                if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    diffuse_tex = n
                if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    rough_tex = n
                if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    bump_tex = n
                if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    normal_tex = n
                if n.name.startswith('QT_Opacity_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    opacity_tex = n
                if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    ao_tex = n
                if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    mask_tex = n
                if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    alpha_tex = n

                if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    layer = n
                if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    layer = n
                                                
        if bpy.context.window_manager.my_toolqt.activemap == 1:

            if diffuse_mapping:
                diffuse_mapping.inputs[3].default_value[0] = size/2
                diffuse_mapping.inputs[3].default_value[1] = 0.5
                diffuse_mapping.inputs[1].default_value[0] = 0.5 + (diffuse_mapping.inputs[3].default_value[0] / 2)
                diffuse_mapping.inputs[1].default_value[1] = 0.25

                if albedo_spec:
                    diffuse_tex.image = albedo_spec
                else:
                    diffuse_tex.image = img_spec

            if rough_mapping:
                rough_mapping.inputs[3].default_value[0] = size/2
                rough_mapping.inputs[3].default_value[1] = 0.5
                rough_mapping.inputs[1].default_value[0] = 0.5 + (rough_mapping.inputs[3].default_value[0] / 2)
                rough_mapping.inputs[1].default_value[1] = 0.25

                if roughness_spec:
                    rough_tex.image = roughness_spec
                else:
                    rough_tex.image = img_spec

            if bump_mapping:
                bump_mapping.inputs[3].default_value[0] = size/2
                bump_mapping.inputs[3].default_value[1] = 0.5
                bump_mapping.inputs[1].default_value[0] = 0.5 + (bump_mapping.inputs[3].default_value[0] / 2)
                bump_mapping.inputs[1].default_value[1] = 0.25

                if albedo_spec:
                    bump_tex.image = albedo_spec
                else:
                    bump_tex.image = img_spec

            if alpha_spec:
                alpha_tex.image = alpha_spec
            else:
                alpha_tex.image = img_spec

            if normal_tex:
                if normal_spec:
                    normal_tex.image = normal_spec

            if ao_tex:
                if ao_spec:
                    ao_tex.image = ao_spec

        elif bpy.context.window_manager.my_toolqt.activemap == 2:

            if rough_mapping:
                rough_mapping.inputs[3].default_value[0] = size/2
                rough_mapping.inputs[3].default_value[1] = 0.5
                rough_mapping.inputs[1].default_value[0] = 0.5 + (rough_mapping.inputs[3].default_value[0] / 2)
                rough_mapping.inputs[1].default_value[1] = 0.25

                if roughness_spec:
                    rough_tex.image = roughness_spec
                else:
                    rough_tex.image = img_spec
        
        elif bpy.context.window_manager.my_toolqt.activemap == 3:

            if bump_mapping:
                bump_mapping.inputs[3].default_value[0] = size/2
                bump_mapping.inputs[3].default_value[1] = 0.5
                bump_mapping.inputs[1].default_value[0] = 0.5 + (bump_mapping.inputs[3].default_value[0] / 2)
                bump_mapping.inputs[1].default_value[1] = 0.25

                if albedo_spec:
                    bump_tex.image = albedo_spec
                else:
                    bump_tex.image = img_spec

        elif bpy.context.window_manager.my_toolqt.activemap == 4:

            if mask_mapping or mask_clamp:

                if mask_mapping:
                    mask_mapping.inputs[3].default_value[0] = size/2
                    mask_mapping.inputs[3].default_value[1] = 0.5
                    mask_mapping.inputs[1].default_value[0] = 0.5 + (mask_mapping.inputs[3].default_value[0] / 2)
                    mask_mapping.inputs[1].default_value[1] = 0.25

                mask_tex.image = img_spec

        elif bpy.context.window_manager.my_toolqt.activemap == 5:

            if alpha_spec:
                alpha_tex.image = alpha_spec
            else:
                alpha_tex.image = img_spec

            if alpha_mapping:
                alpha_mapping.inputs[3].default_value[0] = size/2
                alpha_mapping.inputs[3].default_value[1] = 0.5
                alpha_mapping.inputs[1].default_value[0] = 0.5 + (alpha_mapping.inputs[3].default_value[0] / 2)
                alpha_mapping.inputs[1].default_value[1] = 0.25

        return {'FINISHED'}

class QT_OT_replacealpha_qt(Operator, ImportHelper):
    bl_idname = 'qt.replacealpha'
    bl_label = 'Replace Alpha'
    bl_options = {'PRESET', 'UNDO'}

    files : CollectionProperty(type=bpy.types.PropertyGroup) # Stores properties
  
    def execute(self, context):
        
        bpy.context.window_manager.my_toolqt.filepath = self.filepath
        dirname = os.path.dirname(self.filepath)
        f = self.files[0]
        img_path = (os.path.join(dirname, f.name)) #get filepath properties from collection pointer  
        bpy.ops.image.open( filepath = img_path )
        bpy.data.images[f.name].filepath = img_path

        img_spec = bpy.data.images[f.name]           

        width, height = img_spec.size
        size = width/height

        nodes = None
        node_tree = None
    
        sel = bpy.context.selected_objects
        ob = sel[0]
        mat = ob.material_slots[0].material

        for n in mat.node_tree.nodes:        
            if n.name.startswith('QT_Shader'):
                nodes = n.node_tree.nodes
                node_tree = n.node_tree

        alpha_mapping = None
        alpha_tex = None

        if nodes:
            for n in nodes:
                if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    alpha_mapping = n
                if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    alpha_tex = n
                if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    alpha_color_ramp = n
                if n.name == 'Group Output':
                    out_node = n
                if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                    clamp = n

        if alpha_mapping:
            alpha_mapping.inputs[3].default_value[0] = size/2
            alpha_mapping.inputs[3].default_value[1] = 0.5
            alpha_mapping.inputs[1].default_value[0] = 0.5 + (alpha_mapping.inputs[3].default_value[0] / 2)
            alpha_mapping.inputs[1].default_value[1] = 0.25
            alpha_tex.image = img_spec

            bpy.context.window_manager.my_toolqt.mask = 0 
            bpy.context.window_manager.my_toolqt.activemap = 5        

            node_tree.links.new(out_node.inputs[0], clamp.outputs[0])                
            node_tree.links.new(alpha_tex.outputs[0], alpha_color_ramp.inputs[0])
            
        return {'FINISHED'}

class QT_OT_copymats(Operator):
    bl_idname = 'qt.copymats'
    bl_label = 'Copy Material'
    bl_description = 'Select target objects then select source'
    bl_options = {'PRESET', 'UNDO'}
 
    def execute(self, context):

        sel = bpy.context.selected_objects
        ob = sel[-1]
        act = bpy.context.view_layer.objects.active     

        bpy.ops.object.make_links_data(type='MATERIAL')

        if bpy.context.window_manager.my_toolqt.makeunique:
            sel = bpy.context.selected_objects
            for ob in sel:
                mat = ob.active_material
                if mat:
                    if mat.name.startswith("QT"):
                        ob.active_material = mat.copy()

                        for n in ob.active_material.node_tree.nodes:
                            if n.name.startswith('QT_Shader'):
                                node = n
                                name = n.name
                                nodes = n.node_tree.nodes
                                node_tree = n.node_tree

                            if n.name.startswith("QT_Out"):
                                out = n

                        original_group = node_tree
                        single_user_group = original_group.copy()

                        ob.active_material.node_tree.nodes.remove(node)

                        group_node = ob.active_material.node_tree.nodes.new('ShaderNodeGroup')
                        group_node.node_tree = single_user_group

                        group_node.location = out.location
                        group_node.location.x -= 500

                        group_node.name = name 

                        ob.active_material.node_tree.links.new(out.inputs['Surface'], group_node.outputs[0])
                    
        procuvs = 0
        for layer in act.data.uv_layers:
            if layer.name.startswith('QT_UV'):
                procuvs = 1

        if procuvs:          
            bpy.ops.object.make_links_data(type='MODIFIERS')
            bpy.ops.object.select_all(action='DESELECT')

            for ob in sel:                
                if ob != act:
                    bpy.context.view_layer.objects.active = ob
                    bpy.data.objects[ob.name].select_set(True)

                    layer1 = None
                    layer2 = None

                    layer1 = act.data.uv_layers.get('QT_UV_View_Layer_1')
                    layer2 = act.data.uv_layers.get('QT_UV_Box_Layer_1')

                    if layer1:
                        uvname = 'QT_UV_View_Layer_1'           
                        ob.data.uv_layers.new(name=uvname)
                        ob.data.uv_layers[uvname].active = True
                        bpy.ops.object.editmode_toggle()
                        bpy.ops.mesh.select_all(action='SELECT')   
                        bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=True, scale_to_bounds=False)
                        bpy.ops.object.editmode_toggle()
                    
                    if layer2:
                        uvname = 'QT_UV_Box_Layer_1'           
                        ob.data.uv_layers.new(name=uvname)
                        ob.data.uv_layers[uvname].active = True
                        bpy.ops.object.editmode_toggle()
                        bpy.ops.mesh.select_all(action='SELECT')   
                        bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=True, scale_to_bounds=False)
                        bpy.ops.object.editmode_toggle()
 
        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = act
        bpy.data.objects[act.name].select_set(True)
                            
        return {'FINISHED'}

class QT_OT_makeunique(Operator):
    bl_idname = 'qt.makeunique'
    bl_label = 'Make Material Unique'
    bl_description = 'Make Unique'
    bl_options = {'PRESET', 'UNDO'}
 
    def execute(self, context):

        sel = bpy.context.selected_objects
        for ob in sel:
            mat = ob.active_material
            if mat.name.startswith("QT"):
                ob.active_material = mat.copy()

                for n in ob.active_material.node_tree.nodes:
                    if n.name.startswith('QT_Shader'):
                        node = n
                        name = n.name
                        nodes = n.node_tree.nodes
                        node_tree = n.node_tree

                    if n.name.startswith("QT_Out"):
                        out = n

                original_group = node_tree
                single_user_group = original_group.copy()

                ob.active_material.node_tree.nodes.remove(node)

                group_node = ob.active_material.node_tree.nodes.new('ShaderNodeGroup')
                group_node.node_tree = single_user_group

                group_node.location = out.location
                group_node.location.x -= 500

                group_node.name = name 

                ob.active_material.node_tree.links.new(out.inputs['Surface'], group_node.outputs[0])
                
        return {'FINISHED'}

class quickDecal(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "object.quickdecal"
    bl_label = "QuickDecal"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):

        if event.type.startswith('NDOF'):
            return {'PASS_THROUGH'}

        # alt nav
        if bpy.context.preferences.addons[__package__].preferences.alt_nav:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                if event.alt:
                    self.alt = 0
                    return {'PASS_THROUGH'} 
            elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                if event.alt:
                    self.alt = 0
                    return {'PASS_THROUGH'} 

        # get vars
        if bpy.context.window_manager.my_toolqt.selected:
            if bpy.context.window_manager.my_toolqt.ob:
                if len(bpy.context.window_manager.my_toolqt.ob.material_slots) > 0:
                    self.mat = bpy.context.window_manager.my_toolqt.ob.material_slots[0].material
                    if self.mat:                    
                        for n in self.mat.node_tree.nodes:
                            if n.name == 'QT_Output':
                                self.out_material = n

                            if n.name.startswith('QT_Shader'):
                                self.nodes = n.node_tree.nodes
                                self.node_tree = n.node_tree

                            # blend only
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name.startswith('QT_Blend'):
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                        if self.nodes:
                            for n in self.nodes:
                                # ACTIVE LAYER                            
                                if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.core_shader = n
                                    self.final_node = n
                                    
                                if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.final_node = n
                                    
                                if n.name == 'Group Output':
                                    self.out_node = n

                                # coord
                                if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.tex_coord = n

                                # normal
                                if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_tex = n
                                if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_strength = n
                                    bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                                # mapping                                 
                                if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_mapping = n
                                if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_mapping = n
                                if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_mapping = n

                                # clamps
                                if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_clamp = n
                                if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.roughness_clamp = n
                                if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_clamp = n

                                # textures
                                if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_tex = n
                                if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_bright_contrast = n

                                if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_tex = n
                                if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_color_ramp = n
                                if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_invert = n
                                if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                                if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_tex = n
                                if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_color_ramp = n
                                if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bump = n
                                    bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                                if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_invert = n
                                if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                                # masks
                                if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_tex = n
                                if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_color_ramp = n
                                if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_invert = n
                                if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_mapping = n

                                # alpha
                                if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_mapping = n
                                if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_tex = n
                                if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_color_ramp = n
                                if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_invert = n
                                if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_clamp = n

                                # ao
                                if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_tex = n
                                if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_multiply = n
                                    bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                                # height
                                if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_power = n
                                    bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value
                                if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                
                                # blend
                                if bpy.context.window_manager.my_toolqt.blend:
                                    if n.name == ('QT_Blend_Add'):
                                        self.blend_add = n
                                    if n.name == ('QT_Blend_XYZ'):
                                        self.blend_xyz = n
                                    if n.name == ('QT_Blend_Math'):
                                        self.blend_math = n
                                    if n.name == ('QT_Blend_Power'):
                                        self.blend_power = n
                                    if n.name == ('QT_Blend_Clamp'):
                                        self.blend_clamp = n
                                    if n.name == ('QT_Blend_Mix'):
                                        self.blend_mix = n
                                    if n.name == ('QT_Blend_Noise'):
                                        self.blend_noise = n
                                        bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                        bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                        bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                    if n.name == ('QT_Blend_Bright_Contrast'):
                                        self.blend_bright_contrast = n
                                        bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value
                                    if n.name == 'QT_Blend_Mix':
                                        self.final_node = n
                                        self.core_shader = n

        try:
            self.regX = context.region.width
            self.regY = context.region.height
            self.view_vector = Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
            context.area.tag_redraw() 

            if event.type == 'MOUSEMOVE':
                self.coord = Vector((event.mouse_region_x, event.mouse_region_y))                    
                    
            # pass through if not in proper window area
            self.window_active, self.zoomlevel = utils.window_info(context, event, bpy.context.preferences.addons[__package__].preferences.window_buffer)

            if self.window_active == 0:
                return {'PASS_THROUGH'}

            if bpy.context.window_manager.my_toolqt.running_qt == 0:                
                if self.nodes is not None:
                    for n in self.nodes:
                        if n.name.startswith('QT_Shader_1'):
                            self.final_node = n   

                    for n in self.nodes:
                        if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.final_node = n    
                            
                    self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                    self.out_node.location.y = self.final_node.location.y
                    self.out_node.location.x = self.final_node.location.x + 300     

                    for n in self.nodes:
                        n.select = False
                        if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                            n.select = True

                bpy.context.window_manager.my_toolqt.running_qt = 0
                bpy.context.window_manager.my_toolqt.decal = 0
                bpy.context.window_manager.my_toolqt.selected = 0
                bpy.context.window_manager.my_toolqt.blend = 0
                bpy.context.window_manager.my_toolqt.mask = 0
                bpy.context.window_manager.my_toolqt.ob = None
                bpy.data.collections['QuickTexture'].hide_viewport=True
                bpy.data.collections['QuickTexture'].hide_render=True
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'FINISHED'}
                                    
            if event.type in {'LEFTMOUSE', 'ENTER'} and event.value == 'PRESS':

                if self.g or self.s or self.r or self.l or self.e or self.shifts or self.shiftb or self.shiftn or self.ctrli or self.h or self.v or self.c or self.o or self.a or self.ashift:
                    self.g = 0
                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.shiftn = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.o = 0
                    self.a = 0
                    self.ashift = 0

                else:
                    context.area.tag_redraw() 

                    if self.nodes is not None:

                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                self.final_node = n   

                        for n in self.nodes:
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n    

                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300     

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True

                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    bpy.context.window_manager.my_toolqt.decal = 0
                    bpy.context.window_manager.my_toolqt.selected = 0
                    bpy.context.window_manager.my_toolqt.blend = 0
                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.ob = None
                    bpy.data.collections['QuickTexture'].hide_viewport=True
                    bpy.data.collections['QuickTexture'].hide_render=True
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    return {'FINISHED'}

            if event.type == 'MOUSEMOVE':   

                if self.g:

                    self.mouse_sample_x.append(event.mouse_region_x)
                    self.mouse_sample_y.append(event.mouse_region_y)

                    if len(self.mouse_sample_x) > 1:
                        current = Vector((self.mouse_sample_x[-1], self.mouse_sample_y[-1]))
                        previous = Vector((self.mouse_sample_x[-2], self.mouse_sample_y[-2]))

                        delta = -0.005

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
                            aim = Vector((0,0,0))
                        
                        if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask: 
                            if self.blend_add:
                                self.blend_add.inputs[1].default_value[2] += aim[0] * dist * -1    

                            if self.mask_mapping:
                                self.mask_mapping.inputs[1].default_value[2] += aim[0] * dist * -1

                        else:                            
                            if bpy.context.window_manager.my_toolqt.activemap == 1:
                                mat = Matrix.Rotation(self.diffuse_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 2:
                                mat = Matrix.Rotation(self.rough_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 3:
                                mat = Matrix.Rotation(self.bump_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 4:
                                if self.mask_mapping:
                                    mat = Matrix.Rotation(self.mask_mapping.inputs[2].default_value[2], 4, "Z")
                            if bpy.context.window_manager.my_toolqt.activemap == 5:
                                mat = Matrix.Rotation(self.alpha_mapping.inputs[2].default_value[2], 4, "Z")

                            view = Vector((self.rv3d.view_matrix[2][0:3])).normalized()
                            viewmat = self.rv3d.view_matrix.normalized().to_3x3()
                            basemat = Matrix().to_3x3()
                            viewdot = view.dot(Vector((0,0,1)))
                            angle = viewmat[0].angle(basemat[0])
                            dirdot = viewmat[0].dot(Vector((0,-1,0)))
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
                                self.diffuse_mapping.inputs[1].default_value[0] += xval * dist
                                self.diffuse_mapping.inputs[1].default_value[1] += yval * dist
                                self.diffuse_mapping.inputs[1].default_value[2] = 1

                                self.rough_mapping.inputs[1].default_value[0] += xval * dist
                                self.rough_mapping.inputs[1].default_value[1] += yval * dist
                                self.rough_mapping.inputs[1].default_value[2] = 1

                                self.bump_mapping.inputs[1].default_value[0] += xval * dist
                                self.bump_mapping.inputs[1].default_value[1] += yval * dist
                                self.bump_mapping.inputs[1].default_value[2] = 1   

                                self.alpha_mapping.inputs[1].default_value[0] += xval * dist
                                self.alpha_mapping.inputs[1].default_value[1] += yval * dist
                                self.alpha_mapping.inputs[1].default_value[2] = 1  

                            elif bpy.context.window_manager.my_toolqt.activemap == 2:
                                self.rough_mapping.inputs[1].default_value[0] += xval * dist
                                self.rough_mapping.inputs[1].default_value[1] += yval * dist
                                self.rough_mapping.inputs[1].default_value[2] = 1

                            elif bpy.context.window_manager.my_toolqt.activemap == 3:
                                self.bump_mapping.inputs[1].default_value[0] += xval * dist
                                self.bump_mapping.inputs[1].default_value[1] += yval * dist
                                self.bump_mapping.inputs[1].default_value[2] = 1 

                            elif bpy.context.window_manager.my_toolqt.activemap == 4:

                                if self.mask_mapping:
                                    if self.mask_mapping.name.startswith('QT_Add_Mask'):
                                        self.mask_mapping.inputs[1].default_value[2] += xval * dist * -1                
                                    else:
                                        self.mask_mapping.inputs[1].default_value[0] += xval * dist
                                        self.mask_mapping.inputs[1].default_value[1] += yval * dist
                                        self.mask_mapping.inputs[1].default_value[2] = 1      

                            elif bpy.context.window_manager.my_toolqt.activemap == 5:
                                self.alpha_mapping.inputs[1].default_value[0] += xval * dist
                                self.alpha_mapping.inputs[1].default_value[1] += yval * dist
                                self.alpha_mapping.inputs[1].default_value[2] = 1  

                        context.area.tag_redraw()

                if self.s:
                    
                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.003

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[0] += delta * self.diffuse_mapping.inputs[3].default_value[0]
                        self.diffuse_mapping.inputs[3].default_value[1] += delta * self.diffuse_mapping.inputs[3].default_value[1]
                        self.diffuse_mapping.inputs[3].default_value[2] += delta * self.diffuse_mapping.inputs[3].default_value[2]

                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]
                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]
                        self.rough_mapping.inputs[3].default_value[2] += delta * self.rough_mapping.inputs[3].default_value[2]

                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]
                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]
                        self.bump_mapping.inputs[3].default_value[2] += delta * self.bump_mapping.inputs[3].default_value[2] 

                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]
                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]
                        self.alpha_mapping.inputs[3].default_value[2] += delta * self.alpha_mapping.inputs[3].default_value[2]     

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]
                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]
                        self.rough_mapping.inputs[3].default_value[2] += delta * self.rough_mapping.inputs[3].default_value[2]

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:

                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]
                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]
                        self.bump_mapping.inputs[3].default_value[2] += delta * self.bump_mapping.inputs[3].default_value[2]  
                                                
                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[0] += delta * self.mask_mapping.inputs[3].default_value[0]
                            self.mask_mapping.inputs[3].default_value[1] += delta * self.mask_mapping.inputs[3].default_value[1]
                            self.mask_mapping.inputs[3].default_value[2] += delta * self.mask_mapping.inputs[3].default_value[2]

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:

                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]
                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]
                        self.alpha_mapping.inputs[3].default_value[2] += delta * self.alpha_mapping.inputs[3].default_value[2]  

                    context.area.tag_redraw()

                if self.shifts:
                    
                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.003

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10
                                            
                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[0] += delta * self.diffuse_mapping.inputs[3].default_value[0]

                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]

                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]

                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[0] += delta * self.rough_mapping.inputs[3].default_value[0]

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_mapping.inputs[3].default_value[0] += delta * self.bump_mapping.inputs[3].default_value[0]
                                                
                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                        
                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[0] += delta * self.mask_mapping.inputs[3].default_value[0]

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_mapping.inputs[3].default_value[0] += delta * self.alpha_mapping.inputs[3].default_value[0]

                    context.area.tag_redraw()

                if self.alts:
                    
                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.003

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.activemap == 1:
                        self.diffuse_mapping.inputs[3].default_value[1] += delta * self.diffuse_mapping.inputs[3].default_value[1]

                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]

                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]

                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]

                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[3].default_value[1] += delta * self.rough_mapping.inputs[3].default_value[1]

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_mapping.inputs[3].default_value[1] += delta * self.bump_mapping.inputs[3].default_value[1]
                                                
                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:

                        if self.mask_mapping:
                            self.mask_mapping.inputs[3].default_value[1] += delta * self.mask_mapping.inputs[3].default_value[1]

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_mapping.inputs[3].default_value[1] += delta * self.alpha_mapping.inputs[3].default_value[1]

                    context.area.tag_redraw()

                if self.r == 1:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= 0.0025

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
                            
                    elif bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_mapping.inputs[2].default_value[2] += delta 

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_mapping.inputs[2].default_value[2] += delta 

                    elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:

                        if self.mask_mapping:
                            self.mask_mapping.inputs[2].default_value[2] += delta

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_mapping.inputs[2].default_value[2] += delta 

                    context.area.tag_redraw()

                if self.l:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.0005

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

                    bpy.context.window_manager.my_toolqt.sss = self.core_shader.inputs[1].default_value

                    context.area.tag_redraw()

                if self.a:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

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

                        bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                    context.area.tag_redraw()

                if self.ashift:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    for modifier in bpy.context.window_manager.my_toolqt.ob.modifiers:
                        if modifier.name == "QT_Displace":
                            mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get("QT_Displace")
                            mod.strength += delta
                            if mod.strength < -2:
                                mod.strength = -2
                            if mod.strength > 2:
                                mod.strength = 2

                    context.area.tag_redraw()

                if self.e:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.01

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:
                            self.blend_noise.inputs[5].default_value += delta
                            if self.blend_noise.inputs[5].default_value < -30:
                                self.blend_noise.inputs[5].default_value = -30
                            if self.blend_noise.inputs[5].default_value > 30:
                                self.blend_noise.inputs[5].default_value = 30

                            bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value

                    else:
                        self.core_shader.inputs[18].default_value += delta
                        if self.core_shader.inputs[18].default_value < 0:
                            self.core_shader.inputs[18].default_value = 0

                        bpy.context.window_manager.my_toolqt.emit = self.core_shader.inputs[18].default_value

                    context.area.tag_redraw()

                if self.o:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.002

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:                            
                            self.blend_noise.inputs[4].default_value += delta
                            if self.blend_noise.inputs[4].default_value < 0:
                                self.blend_noise.inputs[4].default_value = 0
                            if self.blend_noise.inputs[4].default_value > 30:
                                self.blend_noise.inputs[4].default_value = 30

                            bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value

                    else:
                        if self.final_node.name.startswith('QT_Layer'):
                            self.final_node.inputs[0].default_value += delta
                            if self.final_node.inputs[0].default_value < 0:
                                self.final_node.inputs[0].default_value = 0
                            if self.final_node.inputs[0].default_value > 30:
                                self.final_node.inputs[0].default_value = 30

                            bpy.context.window_manager.my_toolqt.opacity = self.final_node.inputs[0].default_value

                    context.area.tag_redraw()

                if self.shifth:

                    delta = (event.mouse_prev_x - event.mouse_x) 

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        delta *= -0.005
                    else:
                        delta *= -0.0005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:
                            self.blend_noise.inputs[2].default_value += delta
                            if self.blend_noise.inputs[2].default_value < 0:
                                self.blend_noise.inputs[2].default_value = 0
                            if self.blend_noise.inputs[2].default_value > 30:
                                self.blend_noise.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value

                    else:
                        self.core_shader.inputs[5].default_value += delta
                        if self.core_shader.inputs[5].default_value < 0:
                            self.core_shader.inputs[5].default_value = 0
                        if self.core_shader.inputs[5].default_value > 5:
                            self.core_shader.inputs[5].default_value = 5

                        bpy.context.window_manager.my_toolqt.spec = self.core_shader.inputs[5].default_value

                    context.area.tag_redraw()

                if self.shiftn:

                    delta = (event.mouse_prev_x - event.mouse_x) 

                    delta *= -0.005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        print ("nothing yet")
                        
                    else:                        
                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value += delta
                            if self.normal_strength.inputs[0].default_value < 0:
                                self.normal_strength.inputs[0].default_value = 0
                            if self.normal_strength.inputs[0].default_value > 5:
                                self.normal_strength.inputs[0].default_value = 5

                            bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                    context.area.tag_redraw()

                if self.shiftb:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_noise:
                            self.blend_noise.inputs[3].default_value += delta
                            if self.blend_noise.inputs[3].default_value < 0:
                                self.blend_noise.inputs[3].default_value = 0
                            if self.blend_noise.inputs[3].default_value > 10:
                                self.blend_noise.inputs[3].default_value = 10

                            bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value

                    else:
                        self.bump_bump.inputs[0].default_value += delta
                        if self.bump_bump.inputs[0].default_value < 0:
                            self.bump_bump.inputs[0].default_value = 0
                        if self.bump_bump.inputs[0].default_value > 3:
                            self.bump_bump.inputs[0].default_value = 3
                        bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value

                    context.area.tag_redraw()

                if self.h:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.001

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_power:
                            self.blend_power.inputs[1].default_value += delta
                            if self.blend_power.inputs[1].default_value < 0.001:
                                self.blend_power.inputs[1].default_value = 0.001
                            if self.blend_power.inputs[1].default_value > 5:
                                self.blend_power.inputs[1].default_value = 5

                            bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[0].default_value += delta
                            if self.diffuse_hue_sat.inputs[0].default_value < 0:
                                self.diffuse_hue_sat.inputs[0].default_value = 0
                            if self.diffuse_hue_sat.inputs[0].default_value > 5:
                                self.diffuse_hue_sat.inputs[0].default_value = 5

                            bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value

                    context.area.tag_redraw()
                
                if self.v:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[1].default_value += delta
                            if self.blend_bright_contrast.inputs[1].default_value < -30:
                                self.blend_bright_contrast.inputs[1].default_value = -30
                            if self.blend_bright_contrast.inputs[1].default_value > 30:
                                self.blend_bright_contrast.inputs[1].default_value = 30

                            bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[1].default_value += delta
                            bpy.context.window_manager.my_toolqt.blendvalue = self.mask_bright_contrast.inputs[1].default_value

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[2].default_value += delta
                            if self.diffuse_hue_sat.inputs[2].default_value < -30:
                                self.diffuse_hue_sat.inputs[2].default_value = -30
                            if self.diffuse_hue_sat.inputs[2].default_value > 30:
                                self.diffuse_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 2:
                            self.rough_hue_sat.inputs[2].default_value += delta
                            if self.rough_hue_sat.inputs[2].default_value < -30:
                                self.rough_hue_sat.inputs[2].default_value = -30
                            if self.rough_hue_sat.inputs[2].default_value > 30:
                                self.rough_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 3:
                            self.bump_hue_sat.inputs[2].default_value += delta
                            if self.bump_hue_sat.inputs[2].default_value < -30:
                                self.bump_hue_sat.inputs[2].default_value = -30
                            if self.bump_hue_sat.inputs[2].default_value > 30:
                                self.bump_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 4:
                            self.mask_hue_sat.inputs[2].default_value += delta
                            if self.mask_hue_sat.inputs[2].default_value < -30:
                                self.mask_hue_sat.inputs[2].default_value = -30
                            if self.mask_hue_sat.inputs[2].default_value > 30:
                                self.mask_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 5:
                            self.alpha_hue_sat.inputs[2].default_value += delta
                            if self.alpha_hue_sat.inputs[2].default_value < -30:
                                self.alpha_hue_sat.inputs[2].default_value = -30
                            if self.alpha_hue_sat.inputs[2].default_value > 30:
                                self.alpha_hue_sat.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value

                if self.c:

                    delta = (event.mouse_prev_x - event.mouse_x) 
                    delta *= -0.005

                    if self.shift == 1:
                        delta *= 0.2

                    if self.ctrl == 1:
                        delta *= 4

                    if self.alt == 1:
                        delta *= 10

                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:
                        if self.blend_bright_contrast:
                            self.blend_bright_contrast.inputs[2].default_value += delta
                            if self.blend_bright_contrast.inputs[2].default_value < -30:
                                self.blend_bright_contrast.inputs[2].default_value = 30
                            if self.blend_bright_contrast.inputs[2].default_value > 30:
                                self.blend_bright_contrast.inputs[2].default_value = 30

                            bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value

                        if self.mask_bright_contrast:
                            self.mask_bright_contrast.inputs[2].default_value += delta
                            bpy.context.window_manager.my_toolqt.blendcontrast = self.mask_bright_contrast.inputs[2].default_value

                    else:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            self.diffuse_hue_sat.inputs[1].default_value += delta
                            if self.diffuse_hue_sat.inputs[1].default_value < -30:
                                self.diffuse_hue_sat.inputs[1].default_value = -30
                            if self.diffuse_hue_sat.inputs[1].default_value > 30:
                                self.diffuse_hue_sat.inputs[1].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 2:
                            self.rough_bright_contrast.inputs[2].default_value += delta
                            if self.rough_bright_contrast.inputs[2].default_value < -30:
                                self.rough_bright_contrast.inputs[2].default_value = -30
                            if self.rough_bright_contrast.inputs[2].default_value > 30:
                                self.rough_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 3:
                            self.bump_bright_contrast.inputs[2].default_value += delta
                            if self.bump_bright_contrast.inputs[2].default_value < -30:
                                self.bump_bright_contrast.inputs[2].default_value = -30
                            if self.bump_bright_contrast.inputs[2].default_value > 30:
                                self.bump_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 4:
                            self.mask_bright_contrast.inputs[2].default_value += delta
                            if self.mask_bright_contrast.inputs[2].default_value < -30:
                                self.mask_bright_contrast.inputs[2].default_value = -30
                            if self.mask_bright_contrast.inputs[2].default_value > 30:
                                self.mask_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value

                        if bpy.context.window_manager.my_toolqt.activemap == 5:
                            self.alpha_bright_contrast.inputs[2].default_value += delta
                            if self.alpha_bright_contrast.inputs[2].default_value < -30:
                                self.alpha_bright_contrast.inputs[2].default_value = -30
                            if self.alpha_bright_contrast.inputs[2].default_value > 30:
                                self.alpha_bright_contrast.inputs[2].default_value = 30
                            
                            bpy.context.window_manager.my_toolqt.alpha_contrast = self.alpha_bright_contrast.inputs[2].default_value

# OS KEYS            
            elif event.type in {'LEFT_ALT', 'RIGHT_ALT'}:
                if event.value == 'PRESS':
                    self.alt = 1
                if event.value == 'RELEASE':
                    self.alt = 0

            elif event.type == 'SPACE':
                return {'PASS_THROUGH'}

            elif event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT'}:
                if event.value == 'PRESS':
                    self.shift = 1

                if event.value == 'RELEASE':
                    self.shift = 0

                return {'PASS_THROUGH'}

            elif event.type in {'LEFT_CTRL', 'RIGHT_CTRL', 'OSKEY'}:

                if event.value == 'PRESS':
                    self.ctrl = 1
                if event.value == 'RELEASE':
                    self.ctrl = 0
                
                return {'PASS_THROUGH'}                 
# KEYS                                  
# 
            # LAYERS            
            elif event.type == 'N':    
                if event.value == 'PRESS':

                    self.s = 0
                    self.r = 0
                    self.l = 0
                    self.e = 0
                    self.shifts = 0
                    self.shiftb = 0
                    self.ctrli = 0
                    self.h = 0
                    self.v = 0
                    self.c = 0
                    self.a = 0
                    self.o = 0

                    if self.ctrl == 0 and self.alt == 0 and self.shift == 0:
                        return {'PASS_THROUGH'}

                    elif self.ctrl == 0 and self.alt == 0 and self.shift == 1:
                        if self.shiftn: 
                            self.shiftn = 0
                        else:
                            self.shiftn = 1

                    elif self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:             
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.normalmask_qt('INVOKE_DEFAULT')

                    elif self.ctrl == 1 and self.alt == 0 and self.shift == 1:

                        if bpy.context.window_manager.my_toolqt.ob.data.materials:
                            for mat in bpy.context.window_manager.my_toolqt.ob.data.materials:
                                if mat:
                                    if mat.name.startswith("QT"):
                                        bpy.ops.object.material_slot_remove()
                            bpy.context.window_manager.my_toolqt.running_qt = 0

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0
                        
            # MOVE   
            elif event.type == 'G':
                if event.value == 'PRESS':

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

                    if self.g:
                        self.g = 0
                        self.mouse_sample_x = []
                        self.mouse_sample_y = []
                    else:
                        self.g = 1
                        self.mouse_sample_x = []
                        self.mouse_sample_y = []
                                
            # SCALE   
            elif event.type == 'S':   
                if event.value == 'PRESS':
                    
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
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
                            if self.s: 
                                self.s = 0
                            else:
                                self.s = 1

            # ROTATE   
            elif event.type == 'R':
                if event.value == 'PRESS':

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

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:  

                        if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                            if self.r: 
                                self.r = 0
                            else:
                                self.r = 1
                            
                        elif event.ctrl == 0 and event.shift == 0 and event.alt == 1:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.ops.qt.replacemaps('INVOKE_DEFAULT')
                        
                        elif event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.context.window_manager.my_toolqt.running_qt = 0
                            return {'PASS_THROUGH'}

                        elif event.ctrl == 1 and event.shift == 1 and event.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            bpy.context.window_manager.my_toolqt.running_qt = 0
                            return {'PASS_THROUGH'}
                                                                    
            # REPROJECT FROM VIEW
            elif event.type == 'P' and event.value == 'PRESS':

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:  
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

                    resetparm = 0
                    empty_uv = None

                    for modifier in bpy.context.window_manager.my_toolqt.ob.modifiers:
                        if modifier.name.startswith('QT_UV_View_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            resetparm = 1
                            mod = bpy.context.window_manager.my_toolqt.ob.modifiers.get(modifier.name)
                            empty_uv = mod.projectors[0].object
                            empty_uv.rotation_euler = context.region_data.view_rotation.to_euler()

                    if empty_uv:
                        cloc = Vector((0,0,0))
                        empty_uv.location = region_2d_to_location_3d(self.region, self.rv3d, (self.coord), (cloc)) 

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
            elif event.type == 'M' and event.value == 'PRESS':

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
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

                    if self.ctrl == 1 and self.alt == 0 and self.shift == 0:
                        self.ctrl = 0
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            
                            # check if mask exists on current layer
                            mask = 0
                            for n in self.nodes:
                                if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    mask = 1

                            if mask == 0:
                                bpy.ops.qt.texturemask_qt('INVOKE_DEFAULT')
                    
                    elif self.ctrl == 0 and self.alt == 0 and self.shift == 0:                
                        bpy.context.window_manager.my_toolqt.metal = not bpy.context.window_manager.my_toolqt.metal 

                        if bpy.context.window_manager.my_toolqt.metal:
                            if self.core_shader:
                                self.core_shader.inputs[4].default_value = 1
                        else:
                            if self.core_shader:
                                self.core_shader.inputs[4].default_value = 0

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # SSS
            elif event.type == 'L':   
                if event.value == 'PRESS':

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
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

                        if self.l: 
                            self.l = 0
                        else:
                            self.l = 1

            # AO
            elif event.type == 'A':   
                if event.value == 'PRESS':

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
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

                        if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            self.alpha_type = 1
                            bpy.ops.qt.replacealpha('INVOKE_DEFAULT')

                        elif self.ctrl == 0 and self.shift == 0 and self.alt == 1:
                            self.ctrl = 0
                            self.shift = 0

                            if self.alpha_type:                            
                                self.node_tree.links.new(self.alpha_tex.outputs[0], self.alpha_color_ramp.inputs[0])
                                self.alpha_type = 0
                            else:                       
                                self.node_tree.links.new(self.alpha_tex.outputs[1], self.alpha_color_ramp.inputs[0])
                                self.alpha_type = 1

                        elif self.ctrl == 0 and self.shift == 1 and self.alt == 0:
                            self.ctrl = 0
                            self.alt = 0
                            self.shift = 0
                            if self.ashift: 
                                self.ashift = 0
                            else:
                                self.ashift = 1

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
            elif event.type == 'E':   
                if event.value == 'PRESS':

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

                    if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                        if self.e: 
                            self.e = 0
                        else:
                            self.e = 1

                    else:
                        bpy.context.window_manager.my_toolqt.running_qt = 0
                        return {'PASS_THROUGH'}

            # BUMP
            elif event.type == 'B':   
                if event.value == 'PRESS':

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
                    self.o = 0                   

                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0: 
                        # NEW BOX LAYER
                        if self.ctrl == 1 and self.shift == 0 and self.alt == 0:
                            if bpy.context.window_manager.my_toolqt.activelayer < 5:
                                bpy.ops.qt.boxlayer_qt('INVOKE_DEFAULT')    

                    if self.shift == 1 and self.ctrl == 0 and self.alt == 0:
                        if self.shiftb: 
                            self.shiftb = 0
                        else:
                            self.shiftb = 1

                    if self.shift == 1 and self.ctrl == 1 and self.alt == 0:
                        bpy.context.window_manager.my_toolqt.running_qt = 0
                        return {'PASS_THROUGH'}

                    
                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # HUE
            elif event.type == 'H':   
                if event.value == 'PRESS':

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
                    self.v = 0
                    self.c = 0
                    self.o = 0

                    if self.ctrl:
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:                        
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.heightmask_qt('INVOKE_DEFAULT')

                    if self.alt:
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
                            if bpy.context.window_manager.my_toolqt.activelayer > 1:                        
                                # check if mask exists on current layer
                                mask = 0
                                for n in self.nodes:
                                    if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        mask = 1

                                if mask == 0:
                                    bpy.ops.qt.depthmask_qt('INVOKE_DEFAULT')

                    if self.shift:
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

            # VALUE
            elif event.type == 'V':   
                if event.value == 'PRESS':

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

                    # NEW VIEW LAYER
                    if self.ctrl:
                        self.ctrl = 0
                        if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:   
                            if bpy.context.window_manager.my_toolqt.activelayer < 5:
                                bpy.ops.qt.viewlayer_qt('INVOKE_DEFAULT')

                    else:
                        if self.v: 
                            self.v = 0
                        else:
                            self.v = 1

                    self.ctrl = 0
                    self.shift = 0
                    self.alt = 0

            # SATURATION
            elif event.type == 'C':   
                if event.value == 'PRESS':

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

                    if self.alt:
                        if bpy.context.window_manager.my_toolqt.activemap == 1:
                            if self.diffuse_tex:
                                if self.diffuse_tex.extension == 'CLIP':
                                    self.diffuse_tex.extension = 'REPEAT'
                                else:
                                    self.diffuse_tex.extension = 'CLIP'

                            if self.rough_tex:
                                if self.rough_tex.extension == 'CLIP':
                                    self.rough_tex.extension = 'REPEAT'
                                else:
                                    self.rough_tex.extension = 'CLIP'

                            if self.bump_tex:
                                if self.bump_tex.extension == 'CLIP':
                                    self.bump_tex.extension = 'REPEAT'
                                else:
                                    self.bump_tex.extension = 'CLIP'

                            if self.normal_tex:
                                if self.normal_tex.extension == 'CLIP':
                                    self.normal_tex.extension = 'REPEAT'
                                else:
                                    self.normal_tex.extension = 'CLIP'

                            if self.alpha_tex:
                                if self.alpha_tex.extension == 'CLIP':
                                    self.alpha_tex.extension = 'REPEAT'
                                else:
                                    self.alpha_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 2:
                            if self.rough_tex:
                                if self.rough_tex.extension == 'CLIP':
                                    self.rough_tex.extension = 'REPEAT'
                                else:
                                    self.rough_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 3:
                            if self.bump_tex:
                                if self.bump_tex.extension == 'CLIP':
                                    self.bump_tex.extension = 'REPEAT'
                                else:
                                    self.bump_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 4:
                            if self.mask_tex:
                                if self.mask_tex.extension == 'CLIP':
                                    self.mask_tex.extension = 'REPEAT'
                                else:
                                    self.mask_tex.extension = 'CLIP'

                        elif bpy.context.window_manager.my_toolqt.activemap == 5:
                            if self.alpha_tex:
                                if self.alpha_tex.extension == 'CLIP':
                                    self.alpha_tex.extension = 'REPEAT'
                                else:
                                    self.alpha_tex.extension = 'CLIP'
                                
                    else:
                        if self.c: 
                            self.c = 0
                        else:
                            self.c = 1

            # OPACITY
            elif event.type == 'O':   
                if event.value == 'PRESS':

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
                    
                    if bpy.context.window_manager.my_toolqt.blend or bpy.context.window_manager.my_toolqt.mask:      
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
                                    if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        self.o = 1

            # INVERT
            elif event.type == 'I' and event.value == 'PRESS':

                if self.ctrl:
                    if bpy.context.window_manager.my_toolqt.activemap == 2:
                        self.rough_invert.inputs[0].default_value = not self.rough_invert.inputs[0].default_value

                    elif bpy.context.window_manager.my_toolqt.activemap == 3:
                        self.bump_invert.inputs[0].default_value = not self.bump_invert.inputs[0].default_value                       

                    elif bpy.context.window_manager.my_toolqt.activemap == 4:
                        self.mask_invert.inputs[0].default_value = not self.mask_invert.inputs[0].default_value    

                    elif bpy.context.window_manager.my_toolqt.activemap == 5:
                        self.alpha_invert.inputs[0].default_value = not self.alpha_invert.inputs[0].default_value    

                    context.area.tag_redraw()

            # DUPLICATE LAYER
            elif event.shift and event.type == 'D' and event.value == 'PRESS':

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
                        if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer-1)):
                            n.select = False
                            nodes.append(n)

                        if n.name.startswith('QT_Shader_1'):
                            layer1 = n

                        if n.name.startswith('QT_Shader_2'):
                            layer2 = n

                        if n.name.startswith('QT_Shader_3'):
                            layer3 = n
                        
                        if n.name.startswith('QT_Shader_4'):
                            layer4 = n

                    if bpy.context.window_manager.my_toolqt.activelayer == 2 and layer2: 
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith('_4'):                 
                                    n.name = n.name.replace("_4", "_5")   
                                    n.label = n.label.replace("_4", "_5")   
                                    n.location.y -= 2000   
                        if layer3:
                            for n in self.nodes:
                                if n.name.endswith('_3'):                 
                                    n.name = n.name.replace("_3", "_4")   
                                    n.label = n.label.replace("_3", "_4")   
                                    n.location.y -= 2000   
                        if layer2:       
                            for n in self.nodes:
                                if n.name.endswith('_2'):                 
                                    n.name = n.name.replace("_2", "_3")   
                                    n.label = n.label.replace("_2", "_3")   
                                    n.location.y -= 2000       

                    if bpy.context.window_manager.my_toolqt.activelayer == 3 and layer3: 
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith('_4'):                 
                                    n.name = n.name.replace("_4", "_5")   
                                    n.label = n.label.replace("_4", "_5")   
                                    n.location.y -= 2000   
                        if layer3:
                            for n in self.nodes:
                                if n.name.endswith('_3'):                 
                                    n.name = n.name.replace("_3", "_4")   
                                    n.label = n.label.replace("_3", "_4")   
                                    n.location.y -= 2000   

                    if bpy.context.window_manager.my_toolqt.activelayer == 4 and layer4: 
                        if layer4:
                            for n in self.nodes:
                                if n.name.endswith('_4'):                 
                                    n.name = n.name.replace("_4", "_5")   
                                    n.label = n.label.replace("_4", "_5")   
                                    n.location.y -= 2000  

                    for node in nodes:
                        if node.type != 'GROUP_OUTPUT':

                            # copy node
                            node_new = self.nodes.new(node.bl_idname)

                            # get old node settings
                            attributes = []
                            input_attributes = ( "default_value", "name" )
                            output_attributes = ( "default_value", "name" )
                            ignore_attributes = ( "rna_type", "type", "dimensions", "inputs", "outputs", "internal_links", "select", "texture_mapping", "color_mapping", "image_user", "color_ramp")
                            for attr in node.bl_rna.properties:
                                if not attr.identifier in ignore_attributes and not attr.identifier.split("_")[0] == "bl":
                                    attributes.append(attr.identifier)

                            # copy attributes
                            for attr in attributes:
                                if hasattr( node_new, attr ):
                                    setattr( node_new, attr, getattr( node, attr ))

                            #copy the attributes for all inputs
                            for i, inp in enumerate(node.inputs):                                
                                # copy input attributes
                                for attr in input_attributes:
                                    if hasattr( node_new.inputs[i], attr ):
                                        setattr( node_new.inputs[i], attr, getattr( inp, attr ))

                            #copy the attributes for all outputs
                            for i, out in enumerate(node.outputs):
                                # copy output attributes
                                for attr in output_attributes:
                                    if hasattr( node_new.outputs[i], attr ):
                                        setattr( node_new.outputs[i], attr, getattr( out, attr ))
                            
                            node_new.location = node.location
                            node_new.location.y -= 2000

                            node_new.name = node.name
   
                            if bpy.context.window_manager.my_toolqt.activelayer == 2:                                       
                                node_new.name = node_new.name.replace("1.001", "2")   
                                node_new.label = node_new.label.replace("Layer_1", "Layer_2")   
                            if bpy.context.window_manager.my_toolqt.activelayer == 3: 
                                node_new.name = node_new.name.replace("2.001", "3")   
                                node_new.label = node_new.label.replace("Layer_2", "Layer_3")   
                            if bpy.context.window_manager.my_toolqt.activelayer == 4: 
                                node_new.name = node_new.name.replace("3.001", "4")   
                                node_new.label = node_new.label.replace("Layer_3", "Layer_4")   
                            if bpy.context.window_manager.my_toolqt.activelayer == 5: 
                                node_new.name = node_new.name.replace("4.001", "5")   
                                node_new.label = node_new.label.replace("Layer_4", "Layer_5")   

                    # NAMES
                    for n in self.nodes:
                        # ACTIVE LAYER             
                        if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer-1)):
                            self.prev_shader = n
                        if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.new_shader = n
                        
                        if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer-1)):
                            self.prev_blend_node = n

                        if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.final_node = n
                        
                        if n.name == 'Group Output':
                            self.out_node = n

                        # coord
                        if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.tex_coord = n

                        # normal
                        if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.normal_tex = n
                        if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.normal_strength = n

                        # mapping                                 
                        if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_mapping = n
                        if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_mapping = n
                        if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_mapping = n

                        # clamps
                        if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_clamp = n
                        if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_clamp = n
                        if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_clamp = n

                        # textures
                        if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_tex = n
                        if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_hue_sat = n
                        if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.diffuse_bright_contrast = n

                        if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_tex = n
                        if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_color_ramp = n
                        if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_bright_contrast = n
                        if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_invert = n
                        if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.rough_hue_sat = n

                        if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_tex = n
                        if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_color_ramp = n
                        if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_bright_contrast = n
                        if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_bump = n
                        if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_invert = n
                        if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.bump_hue_sat = n

                        # masks
                        if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_tex = n
                        if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_color_ramp = n
                        if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_bright_contrast = n
                        if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_invert = n
                        if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_hue_sat = n
                        if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.mask_mapping = n

                        # alpha
                        if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_mapping = n
                        if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_tex = n
                        if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_color_ramp = n
                        if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_bright_contrast = n
                        if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_invert = n
                        if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_hue_sat = n
                        if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.alpha_clamp = n

                        # ao
                        if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.ao_tex = n
                        if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.ao_multiply = n

                        # height
                        if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.blend_power = n
                        if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                            self.blend_noise = n
                        
                        # blend
                        if bpy.context.window_manager.my_toolqt.blend:
                            if n.name == ('QT_Blend_Add'):
                                self.blend_add = n
                            if n.name == ('QT_Blend_XYZ'):
                                self.blend_xyz = n
                            if n.name == ('QT_Blend_Math'):
                                self.blend_math = n
                            if n.name == ('QT_Blend_Power'):
                                self.blend_power = n
                            if n.name == ('QT_Blend_Clamp'):
                                self.blend_clamp = n
                            if n.name == ('QT_Blend_Mix'):
                                self.blend_mix = n
                            if n.name == ('QT_Blend_Noise'):
                                self.blend_noise = n
                            if n.name == ('QT_Blend_Bright_Contrast'):
                                self.blend_bright_contrast = n
                            if n.name == 'QT_Blend_Mix':
                                self.final_node = n
                                self.core_shader = n          

                    # LINKS                
                    if self.tex_coord.label == 'Decal' or n.label == 'View' or n.label == 'Box':
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.diffuse_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.rough_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.bump_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[0], self.alpha_mapping.inputs[0])
                    else:
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.diffuse_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.rough_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.bump_mapping.inputs[0])
                        self.node_tree.links.new(self.tex_coord.outputs[2], self.alpha_mapping.inputs[0])    

                    self.node_tree.links.new(self.diffuse_mapping.outputs[0], self.diffuse_tex.inputs[0])
                    self.node_tree.links.new(self.diffuse_tex.outputs[0], self.diffuse_hue_sat.inputs[4])
                    self.node_tree.links.new(self.diffuse_hue_sat.outputs[0], self.diffuse_bright_contrast.inputs[0])
                    self.node_tree.links.new(self.diffuse_bright_contrast.outputs[0], self.new_shader.inputs[0])

                    self.node_tree.links.new(self.rough_mapping.outputs[0], self.rough_tex.inputs[0])
                    self.node_tree.links.new(self.rough_tex.outputs[0], self.rough_color_ramp.inputs[0])
                    self.node_tree.links.new(self.rough_color_ramp.outputs[0], self.rough_hue_sat.inputs[4])
                    self.node_tree.links.new(self.rough_hue_sat.outputs[0], self.rough_invert.inputs[1])
                    self.node_tree.links.new(self.rough_invert.outputs[0], self.rough_bright_contrast.inputs[0])
                    self.node_tree.links.new(self.rough_bright_contrast.outputs[0], self.new_shader.inputs[7])
                    
                    self.node_tree.links.new(self.rough_bright_contrast.outputs[0], self.rough_clamp.inputs[0])
                    self.node_tree.links.new(self.rough_clamp.outputs[0], self.new_shader.inputs[7])
                        
                    self.node_tree.links.new(self.bump_tex.outputs[0], self.bump_color_ramp.inputs[0])
                    self.node_tree.links.new(self.bump_color_ramp.outputs[0], self.bump_hue_sat.inputs[4])
                    self.node_tree.links.new(self.bump_hue_sat.outputs[0], self.bump_invert.inputs[1])
                    self.node_tree.links.new(self.bump_invert.outputs[0], self.bump_bright_contrast.inputs[0])
                    self.node_tree.links.new(self.bump_bright_contrast.outputs[0], self.bump_bump.inputs[2])

                    self.node_tree.links.new(self.bump_bright_contrast.outputs[0], self.bump_clamp.inputs[0])
                    self.node_tree.links.new(self.bump_clamp.outputs[0], self.bump_bump.inputs[2])
                    
                    self.node_tree.links.new(self.bump_mapping.outputs[0], self.bump_tex.inputs[0])
                    self.node_tree.links.new(self.bump_bump.outputs[0], self.new_shader.inputs[20])

                    # normal
                    if self.normal_tex:
                        self.node_tree.links.new(self.diffuse_mapping.outputs[0], self.normal_tex.inputs[0])
                        self.node_tree.links.new(self.normal_tex.outputs[0], self.normal_strength.inputs[1])
                        self.node_tree.links.new(self.normal_strength.outputs[0], self.bump_bump.inputs[5])
                    
                    # ao
                    if self.ao_tex:
                        self.node_tree.links.new(self.diffuse_mapping.outputs[0], self.ao_tex.inputs[0])
                        self.node_tree.links.new(self.ao_tex.outputs[0], self.ao_multiply.inputs[2])
                        self.node_tree.links.new(self.diffuse_tex.outputs[0], self.ao_multiply.inputs[1])
                        self.node_tree.links.new(self.ao_multiply.outputs[0], self.diffuse_hue_sat.inputs[4])
                            
                    self.node_tree.links.new(self.alpha_mapping.outputs[0], self.alpha_tex.inputs[0])
                    self.node_tree.links.new(self.alpha_tex.outputs[1], self.alpha_color_ramp.inputs[0])
                    self.node_tree.links.new(self.alpha_color_ramp.outputs[0], self.alpha_hue_sat.inputs[4])
                    self.node_tree.links.new(self.alpha_hue_sat.outputs[0], self.alpha_invert.inputs[1])
                    self.node_tree.links.new(self.alpha_invert.outputs[0], self.alpha_bright_contrast.inputs[0])    
                    self.node_tree.links.new(self.alpha_bright_contrast.outputs[0], self.alpha_clamp.inputs[0])
                    self.node_tree.links.new(self.alpha_clamp.outputs[0], self.new_shader.inputs[19])

                    # BLEND
                    if bpy.context.window_manager.my_toolqt.activelayer == 2:
                        self.blend_node = self.node_tree.nodes.new('ShaderNodeMixShader')
                        self.blend_node.name = 'QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)
                        self.blend_node.inputs[0].default_value = 1

                        self.node_tree.links.new(self.prev_shader.outputs[0], self.blend_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.blend_node.inputs[2])
                        self.node_tree.links.new(self.blend_node.outputs[0], self.out_node.inputs[0])

                        self.blend_node.location.x = self.new_shader.location.x + 300
                        self.blend_node.location.y = self.new_shader.location.y

                        self.out_node.location.y = self.blend_node.location.y
                        self.out_node.location.x = self.blend_node.location.x + 300  

                    if bpy.context.window_manager.my_toolqt.activelayer == 3:

                        self.node_tree.links.new(self.prev_blend_node.outputs[0], self.final_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.final_node.inputs[2])
                        self.node_tree.links.new(self.final_node.outputs[0], self.out_node.inputs[0])

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300  

                    if bpy.context.window_manager.my_toolqt.activelayer == 4:

                        self.node_tree.links.new(self.prev_blend_node.outputs[0], self.final_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.final_node.inputs[2])
                        self.node_tree.links.new(self.final_node.outputs[0], self.out_node.inputs[0])

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300  

                    if bpy.context.window_manager.my_toolqt.activelayer == 5:

                        self.node_tree.links.new(self.prev_blend_node.outputs[0], self.final_node.inputs[1])
                        self.node_tree.links.new(self.new_shader.outputs[0], self.final_node.inputs[2])
                        self.node_tree.links.new(self.final_node.outputs[0], self.out_node.inputs[0])

                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300  

                    for n in self.nodes:
                        if n.name.startswith('QT_Shader_1'):
                            layer1 = n

                        if n.name.startswith('QT_Layer_2'):
                            layer2 = n

                        if n.name.startswith('QT_Layer_3'):
                            layer3 = n
                        
                        if n.name.startswith('QT_Layer_4'):
                            layer4 = n

                        if n.name.startswith('QT_Layer_5'):
                            layer5 = n

                        if n.name.startswith('QT_Blend_1'):
                            blend1 = n

                        if n.name.startswith('QT_Blend_2'):
                            blend2 = n

                        if n.name.startswith('QT_Blend_3'):
                            blend3 = n
                        
                        if n.name.startswith('QT_Blend_4'):
                            blend4 = n

                        if n.name.startswith('QT_Blend_5'):
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
            elif event.type in {'ONE'} and event.value == 'PRESS':

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
                self.o = 0

                if bpy.context.window_manager.my_toolqt.blend == 0:    
                    
                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 1            

                    self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])
                    
            elif event.type in {'TWO'} and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0:    

                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 2          

                    self.node_tree.links.new(self.out_node.inputs[0], self.roughness_clamp.outputs[0])

            elif event.type in {'THREE'} and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0:    
                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 3               

                    if self.bump_clamp:
                        self.node_tree.links.new(self.out_node.inputs[0], self.bump_clamp.outputs[0])     

            elif event.type in {'FOUR'} and event.value == 'PRESS':

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

                if self.blend_noise:
                    bpy.context.window_manager.my_toolqt.mask = 1
                    bpy.context.window_manager.my_toolqt.activemap = 4 
                    self.node_tree.links.new(self.out_node.inputs[0], self.mask_clamp.outputs[0])     

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:    
                    if self.mask_clamp:
                        bpy.context.window_manager.my_toolqt.activemap = 4        
                        self.node_tree.links.new(self.out_node.inputs[0], self.mask_clamp.outputs[0])     

            elif event.type in {'FIVE'} and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0:    

                    bpy.context.window_manager.my_toolqt.mask = 0 
                    bpy.context.window_manager.my_toolqt.activemap = 5        

                    self.node_tree.links.new(self.out_node.inputs[0], self.alpha_clamp.outputs[0])

            # ACTIVE LAYER
            elif event.type == 'Q' and event.value == 'PRESS':

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

                if self.shift == 1 and self.ctrl == 1 and self.alt == 0:
                        bpy.context.window_manager.my_toolqt.running_qt = 0
                        return {'PASS_THROUGH'}

                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:    

                        bpy.context.window_manager.my_toolqt.activemap = 1     

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            bpy.context.window_manager.my_toolqt.activelayer -= 1

                            if bpy.context.window_manager.my_toolqt.activelayer == 1:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_1'):
                                        self.core_shader = n     
                                        self.final_node = self.core_shader

                            if bpy.context.window_manager.my_toolqt.activelayer == 2:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_2'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_2'):
                                        self.final_node = n  
                                        
                            if bpy.context.window_manager.my_toolqt.activelayer == 3:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_3'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_3'):
                                        self.final_node = n  

                            if bpy.context.window_manager.my_toolqt.activelayer == 4:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_4'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_4'):
                                        self.final_node = n  

                            if bpy.context.window_manager.my_toolqt.activelayer == 5:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_5'):
                                        self.core_shader = n     
                                    if n.name.startswith('QT_Layer_5'):
                                        self.final_node = n  
                            
                            self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])
                            self.out_node.location.y = self.final_node.location.y
                            self.out_node.location.x = self.final_node.location.x + 300
                            
                            for n in self.nodes:
                                n.select = False
                                if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    n.select = True
                            
                            bpy.context.window_manager.my_toolqt.proc_uv = 0 

                            for n in self.nodes:
                                if n.select:
                                    if n.name.startswith('QT_UV_Layer_' + (str(bpy.context.window_manager.my_toolqt.activelayer))):

                                        if n.label == 'Decal' or n.label == 'View':
                                            bpy.context.window_manager.my_toolqt.proc_uv = 1 

                                        if n.label == 'Box':
                                            bpy.context.window_manager.my_toolqt.proc_uv = 1                                            

                            # set parameters
                            bpy.context.window_manager.my_toolqt.emit = self.core_shader.inputs[18].default_value
                            bpy.context.window_manager.my_toolqt.metal = self.core_shader.inputs[4].default_value
                            bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                            bpy.context.window_manager.my_toolqt.spec = self.core_shader.inputs[5].default_value
                            bpy.context.window_manager.my_toolqt.sss = self.core_shader.inputs[1].default_value

                            if bpy.context.window_manager.my_toolqt.activelayer > 1:
                                bpy.context.window_manager.my_toolqt.opacity = self.final_node.inputs[0].default_value
                            
                            if self.normal_tex:
                                if self.normal_tex.name == 'QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                    bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value
                                else:
                                    self.normal_tex = None

                            if self.ao_tex:
                                if self.ao_tex.name == 'QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                    bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value
                                else:
                                    self.ao_tex = None
                
            elif event.type == 'W' and event.value == 'PRESS':

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

                if bpy.context.window_manager.my_toolqt.blend == 0 and bpy.context.window_manager.my_toolqt.mask == 0:    

                    bpy.context.window_manager.my_toolqt.activemap = 1 

                    passgo = 0

                    if bpy.context.window_manager.my_toolqt.activelayer == 1:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_2'):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 2:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_3'):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 3:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_4'):
                                passgo = 1

                    elif bpy.context.window_manager.my_toolqt.activelayer == 4:
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_5'):
                                passgo = 1

                    if passgo:
                        if bpy.context.window_manager.my_toolqt.activelayer < 5:
                            bpy.context.window_manager.my_toolqt.activelayer += 1
                            
                        if bpy.context.window_manager.my_toolqt.activelayer == 2:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_2'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_2'):
                                    self.final_node = n  

                        if bpy.context.window_manager.my_toolqt.activelayer == 3:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_3'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_3'):
                                    self.final_node = n  

                        if bpy.context.window_manager.my_toolqt.activelayer == 4:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_4'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_4'):
                                    self.final_node = n  

                        if bpy.context.window_manager.my_toolqt.activelayer == 5:
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_5'):
                                    self.core_shader = n     
                                if n.name.startswith('QT_Layer_5'):
                                    self.final_node = n  

                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True

                        bpy.context.window_manager.my_toolqt.proc_uv = 0 

                        for n in self.nodes:
                            if n.select:
                                if n.name.startswith('QT_UV_Layer_' + (str(bpy.context.window_manager.my_toolqt.activelayer))):

                                    if n.label == 'Decal' or n.label == 'View':
                                        bpy.context.window_manager.my_toolqt.proc_uv = 1 

                                    if n.label == 'Box':
                                        bpy.context.window_manager.my_toolqt.proc_uv = 1                                         

                        # set parameters
                        bpy.context.window_manager.my_toolqt.emit = self.core_shader.inputs[18].default_value
                        bpy.context.window_manager.my_toolqt.metal = self.core_shader.inputs[4].default_value
                        bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                        bpy.context.window_manager.my_toolqt.spec = self.core_shader.inputs[5].default_value
                        bpy.context.window_manager.my_toolqt.sss = self.core_shader.inputs[1].default_value
                        
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            bpy.context.window_manager.my_toolqt.opacity = self.final_node.inputs[0].default_value

                        if self.normal_tex:
                            if self.normal_tex.name == 'QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value
                            else:
                                self.normal_tex = None

                        if self.ao_tex:
                            if self.ao_tex.name == 'QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer):
                                bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value
                            else:
                                self.ao_tex = None

            # PREVIEW ALL LAYERS
            elif event.type == 'TAB' and event.value == 'RELEASE':

                if bpy.context.window_manager.my_toolqt.blend == 0:   
                    self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                            
            elif event.type == 'UP_ARROW' and event.value == 'RELEASE':
                return {'PASS_THROUGH'}
                
            elif event.type == 'DOWN_ARROW' and event.value == 'RELEASE':
                return {'PASS_THROUGH'}      

            elif event.type == 'BACK_SPACE' and event.value == 'RELEASE':

                if self.ctrl:
                    if bpy.context.window_manager.my_toolqt.blend == 0:    

                        if bpy.context.window_manager.my_toolqt.activelayer > 1:

                            layer1 = None
                            layer2 = None
                            layer3 = None
                            layer4 = None
                            layer5 = None

                            for n in self.nodes:
                                if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.nodes.remove(n)

                            bpy.context.window_manager.my_toolqt.activelayer -= 1

                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_1'):
                                    self.final_node = n   

                            for n in self.nodes:
                                if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.final_node = n    
                                    
                            self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                            self.out_node.location.y = self.final_node.location.y
                            self.out_node.location.x = self.final_node.location.x + 300
                            
                            for n in self.nodes:
                                if n.name.startswith('QT_Shader_1'):
                                    layer1 = n

                                if n.name.startswith('QT_Layer_2'):
                                    layer2 = n

                                if n.name.startswith('QT_Layer_3'):
                                    layer3 = n
                                
                                if n.name.startswith('QT_Layer_4'):
                                    layer4 = n

                                if n.name.startswith('QT_Layer_5'):
                                    layer5 = n

                            if bpy.context.window_manager.my_toolqt.activelayer == 1:
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith('_5'):                 
                                            n.name = n.name.replace("_5", "_4")   
                                            n.label = n.label.replace("_5", "_4")   
                                            n.location.y += 2000   
                                if layer4:
                                    for n in self.nodes:
                                        if n.name.endswith('_4'):                 
                                            n.name = n.name.replace("_4", "_3")   
                                            n.label = n.label.replace("_4", "_3")   
                                            n.location.y += 2000   
                                if layer3:          
                                    for n in self.nodes:
                                        if n.name.endswith('_3'):                 
                                            n.name = n.name.replace("_3", "_2")   
                                            n.label = n.label.replace("_3", "_2")   
                                            n.location.y += 2000    

                                    self.node_tree.links.new(layer1.outputs[0], layer3.inputs[1])    
                                    
                            if bpy.context.window_manager.my_toolqt.activelayer == 2:
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith('_5'):                 
                                            n.name = n.name.replace("_5", "_4")   
                                            n.label = n.label.replace("_5", "_4")   
                                            n.location.y += 2000   
                                if layer4:
                                    for n in self.nodes:
                                        if n.name.endswith('_4'):                 
                                            n.name = n.name.replace("_4", "_3")   
                                            n.label = n.label.replace("_4", "_3")   
                                            n.location.y += 2000   

                                    self.node_tree.links.new(layer2.outputs[0], layer4.inputs[1])   

                            if bpy.context.window_manager.my_toolqt.activelayer == 3: 
                                if layer5:
                                    for n in self.nodes:
                                        if n.name.endswith('_5'):                 
                                            n.name = n.name.replace("_5", "_4")   
                                            n.label = n.label.replace("_5", "_4")   
                                            n.location.y += 2000   

                                    self.node_tree.links.new(layer3.outputs[0], layer5.inputs[1])   
                                            
                            for n in self.nodes:
                                n.select = False
                            
                            for n in self.nodes:
                                if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    n.select = True

                            for n in self.nodes:
                                # ACTIVE LAYER                            
                                if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.core_shader = n
                                    self.final_node = n
                                    
                                if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.final_node = n
                                    
                                if n.name == 'Group Output':
                                    self.out_node = n

                                # coord
                                if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.tex_coord = n

                                # normal
                                if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_tex = n
                                if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.normal_strength = n
                                    bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                                # mapping                                 
                                if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_mapping = n
                                if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_mapping = n
                                if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_mapping = n

                                # clamps
                                if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_clamp = n
                                if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.roughness_clamp = n
                                if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_clamp = n

                                # textures
                                if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_tex = n
                                if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value
                                    bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.diffuse_bright_contrast = n

                                if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_tex = n
                                if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_color_ramp = n
                                if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_invert = n
                                if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.rough_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                                if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_tex = n
                                if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_color_ramp = n
                                if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_bump = n
                                    bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                                if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_invert = n
                                if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.bump_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                                # masks
                                if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_tex = n
                                if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_color_ramp = n
                                if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_invert = n
                                if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.mask_mapping = n

                                # alpha
                                if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_mapping = n
                                if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_tex = n
                                if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_color_ramp = n
                                if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_invert = n
                                if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_hue_sat = n
                                    bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value
                                if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.alpha_clamp = n

                                # ao
                                if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_tex = n
                                if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.ao_multiply = n
                                    bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                                # height
                                if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_power = n
                                    bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value
                                if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                
                                # blend
                                if bpy.context.window_manager.my_toolqt.blend:
                                    if n.name == ('QT_Blend_Add'):
                                        self.blend_add = n
                                    if n.name == ('QT_Blend_XYZ'):
                                        self.blend_xyz = n
                                    if n.name == ('QT_Blend_Math'):
                                        self.blend_math = n
                                    if n.name == ('QT_Blend_Power'):
                                        self.blend_power = n
                                    if n.name == ('QT_Blend_Clamp'):
                                        self.blend_clamp = n
                                    if n.name == ('QT_Blend_Mix'):
                                        self.blend_mix = n
                                    if n.name == ('QT_Blend_Noise'):
                                        self.blend_noise = n
                                        bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                        bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                        bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                    if n.name == ('QT_Blend_Bright_Contrast'):
                                        self.blend_bright_contrast = n
                                        bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value
                                        bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value
                                    if n.name == 'QT_Blend_Mix':
                                        self.final_node = n
                                        self.core_shader = n 

                # DELETE MAP ONLY
                else:
                    if bpy.context.window_manager.my_toolqt.blend == 0:    
                        if bpy.context.window_manager.my_toolqt.activelayer > 1:
                            backspace = 0
                            for n in self.nodes:
                                if n.name.endswith('Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                    self.nodes.remove(n)
                                    backspace = 1

                            if backspace:
                                for n in self.nodes:
                                    if n.name.startswith('QT_Shader_1'):
                                        self.final_node = n     
                                    if n.name.startswith('QT_Layer_2'):
                                        self.final_node = n  
                                    if n.name.startswith('QT_Layer_3'):
                                        self.final_node = n  
                                    if n.name.startswith('QT_Layer_4'):
                                        self.final_node = n  
                                    if n.name.startswith('QT_Layer_5'):
                                        self.final_node = n  
                                        
                                self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                                self.out_node.location.y = self.final_node.location.y
                                self.out_node.location.x = self.final_node.location.x + 300 

                                bpy.context.window_manager.my_toolqt.activemap = 1

                                for n in self.nodes:
                                    n.select = False
                                    if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                        n.select = True

                    else:
                        backspace = 0
                        for n in self.mat.node_tree.nodes:
                            if n.name.startswith('QT_Blend'):
                                self.mat.node_tree.nodes.remove(n)
                                backspace = 1
                        
                        if backspace:
                            bpy.context.window_manager.my_toolqt.blend = 0

                            for n in self.mat.node_tree.nodes:
                                if n.name == 'QT_Output':
                                    self.out_material = n

                                if n.name.startswith('QT_Shader'):
                                    qtshader = n
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                            self.mat.node_tree.links.new(self.out_material.inputs[0], qtshader.outputs[0])         

            elif event.type == 'DEL' and event.value == 'RELEASE':

                if bpy.context.window_manager.my_toolqt.blend == 0:    
                    if bpy.context.window_manager.my_toolqt.activelayer > 1:

                        layer1 = None
                        layer2 = None
                        layer3 = None
                        layer4 = None
                        layer5 = None

                        for n in self.nodes:
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.nodes.remove(n)

                        bpy.context.window_manager.my_toolqt.activelayer -= 1

                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                self.final_node = n   

                        for n in self.nodes:
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n    
                                
                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300
                        
                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                layer1 = n

                            if n.name.startswith('QT_Layer_2'):
                                layer2 = n

                            if n.name.startswith('QT_Layer_3'):
                                layer3 = n
                            
                            if n.name.startswith('QT_Layer_4'):
                                layer4 = n

                            if n.name.startswith('QT_Layer_5'):
                                layer5 = n

                        if bpy.context.window_manager.my_toolqt.activelayer == 1:
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith('_5'):                 
                                        n.name = n.name.replace("_5", "_4")   
                                        n.label = n.label.replace("_5", "_4")   
                                        n.location.y += 2000   
                            if layer4:
                                for n in self.nodes:
                                    if n.name.endswith('_4'):                 
                                        n.name = n.name.replace("_4", "_3")   
                                        n.label = n.label.replace("_4", "_3")   
                                        n.location.y += 2000   
                            if layer3:          
                                for n in self.nodes:
                                    if n.name.endswith('_3'):                 
                                        n.name = n.name.replace("_3", "_2")   
                                        n.label = n.label.replace("_3", "_2")   
                                        n.location.y += 2000    

                                self.node_tree.links.new(layer1.outputs[0], layer3.inputs[1])    
                                
                        if bpy.context.window_manager.my_toolqt.activelayer == 2:
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith('_5'):                 
                                        n.name = n.name.replace("_5", "_4")   
                                        n.label = n.label.replace("_5", "_4")   
                                        n.location.y += 2000   
                            if layer4:
                                for n in self.nodes:
                                    if n.name.endswith('_4'):                 
                                        n.name = n.name.replace("_4", "_3")   
                                        n.label = n.label.replace("_4", "_3")   
                                        n.location.y += 2000   

                                self.node_tree.links.new(layer2.outputs[0], layer4.inputs[1])   

                        if bpy.context.window_manager.my_toolqt.activelayer == 3: 
                            if layer5:
                                for n in self.nodes:
                                    if n.name.endswith('_5'):                 
                                        n.name = n.name.replace("_5", "_4")   
                                        n.label = n.label.replace("_5", "_4")   
                                        n.location.y += 2000   

                                self.node_tree.links.new(layer3.outputs[0], layer5.inputs[1])   
                                        
                        for n in self.nodes:
                            n.select = False
                        
                        for n in self.nodes:
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True

                        for n in self.mat.node_tree.nodes:
                            if n.name == 'QT_Output':
                                self.out_material = n

                            if n.name.startswith('QT_Shader'):
                                self.nodes = n.node_tree.nodes
                                self.node_tree = n.node_tree

                            # blend only
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name.startswith('QT_Blend'):
                                    self.nodes = n.node_tree.nodes
                                    self.node_tree = n.node_tree

                        for n in self.nodes:
                            # ACTIVE LAYER                            
                            if n.name.startswith('QT_Shader_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.core_shader = n
                                self.final_node = n
                                
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n
                                
                            if n.name == 'Group Output':
                                self.out_node = n

                            # coord
                            if n.name.startswith('QT_UV_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.tex_coord = n

                            # normal
                            if n.name.startswith('QT_Normal_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.normal_tex = n
                            if n.name.startswith('QT_Normal_Strength_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.normal_strength = n
                                bpy.context.window_manager.my_toolqt.normal = self.normal_strength.inputs[0].default_value

                            # mapping                                 
                            if n.name.startswith('QT_Diffuse_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_mapping = n
                            if n.name.startswith('QT_Rough_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_mapping = n
                            if n.name.startswith('QT_Bump_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_mapping = n

                            # clamps
                            if n.name.startswith('QT_Clamp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_clamp = n
                            if n.name.startswith('QT_Roughness_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.roughness_clamp = n
                            if n.name.startswith('QT_Bump_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_clamp = n

                            # textures
                            if n.name.startswith('QT_Diffuse_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_tex = n
                            if n.name.startswith('QT_Diffuse_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_hue_sat = n
                                bpy.context.window_manager.my_toolqt.diffuse_hue = self.diffuse_hue_sat.inputs[0].default_value
                                bpy.context.window_manager.my_toolqt.diffuse_sat = self.diffuse_hue_sat.inputs[1].default_value
                                bpy.context.window_manager.my_toolqt.diffuse_val = self.diffuse_hue_sat.inputs[2].default_value
                            if n.name.startswith('QT_Diffuse_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.diffuse_bright_contrast = n

                            if n.name.startswith('QT_Rough_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_tex = n
                            if n.name.startswith('QT_Rough_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_color_ramp = n
                            if n.name.startswith('QT_Rough_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.rough_contrast = self.rough_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Rough_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_invert = n
                            if n.name.startswith('QT_Rough_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.rough_hue_sat = n
                                bpy.context.window_manager.my_toolqt.rough_hue_sat = self.rough_hue_sat.inputs[2].default_value

                            if n.name.startswith('QT_Bump_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_tex = n
                            if n.name.startswith('QT_Bump_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_color_ramp = n
                            if n.name.startswith('QT_Bump_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.bump_contrast = self.bump_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Bump_Bump_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_bump = n
                                bpy.context.window_manager.my_toolqt.bump = self.bump_bump.inputs[0].default_value
                            if n.name.startswith('QT_Bump_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_invert = n
                            if n.name.startswith('QT_Bump_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.bump_hue_sat = n
                                bpy.context.window_manager.my_toolqt.bump_hue_sat = self.bump_hue_sat.inputs[2].default_value

                            # masks
                            if n.name.startswith('QT_Tex_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_tex = n
                            if n.name.startswith('QT_Color_Ramp_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_color_ramp = n
                            if n.name.startswith('QT_Bright_Contrast_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.mask_contrast = self.mask_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Invert_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_invert = n
                            if n.name.startswith('QT_Hue_Sat_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_hue_sat = n
                                bpy.context.window_manager.my_toolqt.mask_hue_sat = self.mask_hue_sat.inputs[2].default_value
                            if n.name.startswith('QT_Mapping_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.mask_mapping = n

                            # alpha
                            if n.name.startswith('QT_Alpha_Mapping_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_mapping = n
                            if n.name.startswith('QT_Alpha_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_tex = n
                            if n.name.startswith('QT_Alpha_Color_Ramp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_color_ramp = n
                            if n.name.startswith('QT_Alpha_Bright_Contrast_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_bright_contrast = n
                                bpy.context.window_manager.my_toolqt.alpha_bright_contrast = self.alpha_bright_contrast.inputs[2].default_value
                            if n.name.startswith('QT_Alpha_Invert_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_invert = n
                            if n.name.startswith('QT_Alpha_Hue_Sat_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_hue_sat = n
                                bpy.context.window_manager.my_toolqt.alpha_hue_sat = self.alpha_hue_sat.inputs[2].default_value
                            if n.name.startswith('QT_Alpha_Clamp_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.alpha_clamp = n

                            # ao
                            if n.name.startswith('QT_AO_Tex_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.ao_tex = n
                            if n.name.startswith('QT_AO_Multiply_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.ao_multiply = n
                                bpy.context.window_manager.my_toolqt.ao = self.ao_multiply.inputs[0].default_value

                            # height
                            if n.name.startswith('QT_Power_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.blend_power = n
                                bpy.context.window_manager.my_toolqt.blendsmoothing = self.blend_power.inputs[1].default_value
                            if n.name.startswith('QT_Noise_Mask_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.blend_noise = n
                                bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                            
                            # blend
                            if bpy.context.window_manager.my_toolqt.blend:
                                if n.name == ('QT_Blend_Add'):
                                    self.blend_add = n
                                if n.name == ('QT_Blend_XYZ'):
                                    self.blend_xyz = n
                                if n.name == ('QT_Blend_Math'):
                                    self.blend_math = n
                                if n.name == ('QT_Blend_Power'):
                                    self.blend_power = n
                                if n.name == ('QT_Blend_Clamp'):
                                    self.blend_clamp = n
                                if n.name == ('QT_Blend_Mix'):
                                    self.blend_mix = n
                                if n.name == ('QT_Blend_Noise'):
                                    self.blend_noise = n
                                    bpy.context.window_manager.my_toolqt.noisedistortion = self.blend_noise.inputs[5].default_value
                                    bpy.context.window_manager.my_toolqt.noiseroughness = self.blend_noise.inputs[4].default_value
                                    bpy.context.window_manager.my_toolqt.noisescale = self.blend_noise.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.noisedetail = self.blend_noise.inputs[3].default_value
                                if n.name == ('QT_Blend_Bright_Contrast'):
                                    self.blend_bright_contrast = n
                                    bpy.context.window_manager.my_toolqt.blendcontrast = self.blend_bright_contrast.inputs[2].default_value
                                    bpy.context.window_manager.my_toolqt.blendvalue = self.blend_bright_contrast.inputs[1].default_value
                                if n.name == 'QT_Blend_Mix':
                                    self.final_node = n
                                    self.core_shader = n 

            # ROTATE 90 DEGREES
            elif event.type == 'LEFT_BRACKET' and event.value == 'RELEASE':
                            
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] -= pi/2 
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 

                context.area.tag_redraw()
                
            elif event.type == 'RIGHT_BRACKET' and event.value == 'RELEASE':
                
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] += pi/2 
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 
                        
                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 

                context.area.tag_redraw()

            # ROTATE 90 DEGREES
            elif event.type == 'LEFT_ARROW' and event.value == 'RELEASE':
                            
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] -= pi/2 
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 
                        
                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] -= pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] -= pi/2 

                context.area.tag_redraw()
                
            elif event.type == 'RIGHT_ARROW' and event.value == 'RELEASE':
                
                if bpy.context.window_manager.my_toolqt.activemap == 1:
                    self.diffuse_mapping.inputs[2].default_value[2] += pi/2 
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 
                        
                elif bpy.context.window_manager.my_toolqt.activemap == 2:
                    self.rough_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 3:
                    self.bump_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 4 and bpy.context.window_manager.my_toolqt.mask == 0:
                    if self.mask_mapping:
                        self.mask_mapping.inputs[2].default_value[2] += pi/2 

                elif bpy.context.window_manager.my_toolqt.activemap == 5:
                    self.alpha_mapping.inputs[2].default_value[2] += pi/2 

                context.area.tag_redraw()

            # RESET SETTINGS
            elif event.type == 'K' and event.value == 'RELEASE':

                if self.tex_coord.label == 'Decal':
                    width, height = self.diffuse_tex.image.size
                    size = width/height

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

                        if self.mask_mapping:
                            self.mask_mapping.inputs[1].default_value[0] = 0
                            self.mask_mapping.inputs[1].default_value[1] = 0
                            self.mask_mapping.inputs[1].default_value[2] = 0
                        
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

                        if self.ao_multiply:
                            self.ao_multiply.inputs[0].default_value = 0

                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value = 0

                        if self.bump_bump:
                            self.bump_bump.inputs[0].default_value = 0

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

                        if self.mask_mapping:
                            self.mask_mapping.inputs[1].default_value[0] = 0
                            self.mask_mapping.inputs[1].default_value[1] = 0
                            self.mask_mapping.inputs[1].default_value[2] = 0
                        
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

                        if self.ao_multiply:
                            self.ao_multiply.inputs[0].default_value = 0

                        if self.normal_strength:
                            self.normal_strength.inputs[0].default_value = 0

                        if self.bump_bump:
                            self.bump_bump.inputs[0].default_value = 0

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

                self.alt = 0
                self.ctrl = 0
                self.shift = 0

                context.area.tag_redraw()
                
            elif event.type in {'MIDDLEMOUSE', 'RET'}:        
                return {'PASS_THROUGH'}
                                                            
            elif event.type == 'RIGHTMOUSE':
                return {'PASS_THROUGH'}           
                                                                                                                                                        
            elif event.type == 'WHEELUPMOUSE':
                return {'PASS_THROUGH'}
            
            elif event.type == 'WHEELDOWNMOUSE':
                return {'PASS_THROUGH'}
                                                                                                           
            elif event.type == 'ZERO':
                return {'PASS_THROUGH'}
                
            elif event.type == 'SIX':
                return {'PASS_THROUGH'}

            elif event.type == 'SEVEN':
                return {'PASS_THROUGH'}
            
            elif event.type == 'EIGHT':
                return {'PASS_THROUGH'}
            
            elif event.type == 'NINE':
                return {'PASS_THROUGH'}
            
            elif event.type == 'NUMPAD_0':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_1':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_2':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_3':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_4':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_5':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_6':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_7':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_8':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_9':
                return {'PASS_THROUGH'}

            elif event.type == 'NUMPAD_PERIOD':
                return {'PASS_THROUGH'}

            elif event.type == 'PERIOD':
                return {'PASS_THROUGH'}

            elif event.type == 'QUOTE':
                return {'PASS_THROUGH'}

            elif event.type == 'MINUS':
                return {'PASS_THROUGH'}

            elif event.type == 'PLUS':
                return {'PASS_THROUGH'}
            
            elif event.type == 'BACK_SLASH':
                return {'PASS_THROUGH'}

            elif event.type == 'EQUAL':
                return {'PASS_THROUGH'}
            
            elif event.type == 'NUMPAD_ASTERIX':
                return {'PASS_THROUGH'}

            elif event.type == 'COMMA':
                return {'PASS_THROUGH'}

            elif event.type == 'F3':
                return {'PASS_THROUGH'}

            elif event.type == 'PAUSE':
                return {'PASS_THROUGH'}

            elif event.type == 'INSERT':
                return {'PASS_THROUGH'}

            elif event.type == 'HOME':
                return {'PASS_THROUGH'}

            elif event.type == 'PAGE_UP':
                return {'PASS_THROUGH'}

            elif event.type == 'PAGE_DOWN':
                return {'PASS_THROUGH'}

            elif event.type == 'END':
                return {'PASS_THROUGH'}

            elif event.type == 'F' and event.value == 'PRESS': 
                if event.ctrl or event.shift:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {'PASS_THROUGH'}

            elif event.type == 'X' and event.value == 'PRESS': 
                if event.ctrl:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {'PASS_THROUGH'}

                if event.ctrl and event.shift:
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    return {'PASS_THROUGH'}

            elif event.ctrl and event.shift and event.type == 'D' and event.value == 'PRESS': 
                self.shift = 0
                bpy.context.window_manager.my_toolqt.running_qt = 0
                bpy.context.window_manager.my_toolqt.decal = 1
                bpy.context.window_manager.my_toolqt.selected = 0
                bpy.context.window_manager.my_toolqt.blend = 0
                bpy.context.window_manager.my_toolqt.mask = 0
                bpy.context.window_manager.my_toolqt.ob = None
                bpy.data.collections['QuickTexture'].hide_viewport=True
                bpy.data.collections['QuickTexture'].hide_render=True
                bpy.ops.object.quickdecal('INVOKE_DEFAULT')

    # UNDO - restore stuff that I don't want changed
            elif event.type == 'Z' and event.value == 'PRESS':                    
                return {'PASS_THROUGH'}
            
            if event.type == 'ESC':
                return {'PASS_THROUGH'}
                                                                
            if event.type == 'ACCENT_GRAVE':
                return {'PASS_THROUGH'}
            
    # EXIT
            if event.type == 'T' and event.value == 'PRESS':

                if event.ctrl == 0 and event.shift == 0 and event.alt == 0:
                    return {'PASS_THROUGH'}

                elif event.ctrl == 1 and event.shift == 0 and event.alt == 0:
                    context.area.tag_redraw() 
                    if self.nodes is not None:

                        for n in self.nodes:
                            if n.name.startswith('QT_Shader_1'):
                                self.final_node = n   

                        for n in self.nodes:
                            if n.name.startswith('QT_Layer_' + str(bpy.context.window_manager.my_toolqt.activelayer)):
                                self.final_node = n    

                        self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])       
                        self.out_node.location.y = self.final_node.location.y
                        self.out_node.location.x = self.final_node.location.x + 300     

                        for n in self.nodes:
                            n.select = False
                            if n.name.endswith(str(bpy.context.window_manager.my_toolqt.activelayer)):
                                n.select = True
                                
                    bpy.context.window_manager.my_toolqt.running_qt = 0
                    bpy.context.window_manager.my_toolqt.selected = 0
                    bpy.context.window_manager.my_toolqt.decal = 0
                    bpy.context.window_manager.my_toolqt.blend = 0
                    bpy.context.window_manager.my_toolqt.mask = 0
                    bpy.context.window_manager.my_toolqt.ob = None
                    bpy.data.collections['QuickTexture'].hide_viewport=True
                    bpy.data.collections['QuickTexture'].hide_render=True
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    return {'FINISHED'}

            return {'RUNNING_MODAL'}
            
        except:
            if self.nodes:
                for n in self.nodes:
                    if n.name.startswith('QT_Shader_1'):
                        self.final_node = n     
                    if n.name.startswith('QT_Layer_2'):
                        self.final_node = n  
                    if n.name.startswith('QT_Layer_3'):
                        self.final_node = n  
                    if n.name.startswith('QT_Layer_4'):
                        self.final_node = n  
                    if n.name.startswith('QT_Layer_5'):
                        self.final_node = n  
                self.node_tree.links.new(self.out_node.inputs[0], self.final_node.outputs[0])            
            bpy.context.window_manager.my_toolqt.running_qt = 0
            bpy.context.window_manager.my_toolqt.decal = 0
            bpy.context.window_manager.my_toolqt.selected = 0
            bpy.context.window_manager.my_toolqt.blend = 0
            bpy.context.window_manager.my_toolqt.mask = 0
            bpy.context.window_manager.my_toolqt.ob = None
            bpy.data.collections['QuickTexture'].hide_viewport=True
            bpy.data.collections['QuickTexture'].hide_render=True
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            traceback.print_exc()
            return {'FINISHED'}

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
        bpy.context.window_manager.my_toolqt.proc_uv = 0

        if len(sel) > 0:
            for ob in sel:
                if ob.type not in ['CURVE', 'META', 'MESH']: 
                    return {'FINISHED'}

                if ob.type in ['CURVE', 'META']:
                    bpy.ops.object.convert(target='MESH')
                    sel = bpy.context.selected_objects   

            ob = sel[0]
            ob2 = bpy.context.view_layer.objects.active
            bpy.context.window_manager.my_toolqt.ob = sel[0]
            bpy.context.window_manager.my_toolqt.selected = 1

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
        self.rough_color_ramp = None
        self.rough_bright_contrast = None
        self.rough_invert = None
        self.rough_hue_sat = None
        self.bump_tex = None
        self.bump_color_ramp = None
        self.bump_bright_contrast = None
        self.bump_bump = None
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
        self.alpha_color_ramp = None
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
            self.collection = bpy.data.collections['QuickTexture']
            bpy.data.collections['QuickTexture'].hide_viewport=False
            bpy.data.collections['QuickTexture'].hide_render=False
        else:
            self.collection = objects.make_collection("QuickTexture", context)

        collections = bpy.context.view_layer.layer_collection.children
        for collection in collections:
            if collection.name == 'QuickTexture':
                if collection.hide_viewport == True:
                    collection.hide_viewport = False

        # view
        self.view_vector = Vector((self.rv3d.perspective_matrix[2][0:3])).normalized()
        self.window_active, self.zoomlevel = utils.window_info(context, event, bpy.context.preferences.addons[__package__].preferences.window_buffer)
        self.regX = bpy.context.region.width
        self.regY = bpy.context.region.height
                
        # shading style        
        areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
        self.viewlens = 50/(areas[0].spaces[0].lens)     

        # hotkeys
        self.coord = Vector((event.mouse_region_x,event.mouse_region_y))
        self.coord_firstclick = Vector((0,0))
        self.coord_lastclick = Vector((0,0))
        self.coord_hotkeyclick = Vector((0,0))
        self.avg_2d = Vector((0,0))     

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
        self.ashift = False
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
        
        args = (self, context) 
        wm = context.window_manager
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_quickTexture, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
                
        # init
        bpy.context.window_manager.my_toolqt.blend = 0
        bpy.context.window_manager.my_toolqt.proc_uv = 1
        bpy.context.window_manager.my_toolqt.decal = 1
    
        # create decal mesh
        appendlist = []
        hidden_objs = []
        appendlist = [(obj) for obj in bpy.context.visible_objects if obj not in bpy.context.selected_objects]

        for ob in appendlist:
            hidden_objs.append(ob)

        if len(hidden_objs) > 0:
            for o in hidden_objs:
                o.hide_set(True)
        
        ob = objects.create_decal(self, context, 'QT_Decal', sel, self.rv3d, self.region, bpy.context.window_manager.my_toolqt.res, bpy.context.window_manager.my_toolqt.padding)
  
        if bpy.context.window_manager.my_toolqt.selected:
            utils.project_geo(self, context, ob, sel, self.rv3d, self.region)
        else:
            utils.align_plane_to_view(self, context, ob, self.rv3d, self.region, self.coord, bpy.context.scene.cursor.location)

        if len(hidden_objs) > 0:
            for o in hidden_objs:
                o.hide_set(False)

        bpy.context.window_manager.my_toolqt.ob = ob
        bpy.ops.object.select_all(action='DESELECT')

        # parenting 
        if len(sel) > 0:                                                                      
            bpy.context.view_layer.objects.active = sel[0]
            bpy.data.objects[ob.name].select_set(True)   
            bpy.data.objects[sel[0].name].select_set(True)      

            bpy.ops.object.parent_set(type='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        
        bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = ob

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')

        if bpy.context.window_manager.my_toolqt.selected:
            bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=False, scale_to_bounds=False)
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.pack_islands(margin=0.001)
            
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.editmode_toggle()
        
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
                                        
        for layer in ob.data.uv_layers: 
            if layer.name == 'UVMap':
                ob.data.uv_layers.remove(layer) 

        bpy.ops.qt.material_qt('INVOKE_DEFAULT')
        
        return {'RUNNING_MODAL'}