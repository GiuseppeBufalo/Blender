

import bpy
import bmesh
import blf
import bgl
from mathutils import Matrix, Vector, Quaternion
from mathutils import bvhtree
from bpy_extras import view3d_utils
import gpu
from gpu_extras.batch import batch_for_shader
import math
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
)



shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
shader2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

handle3d = None
handle3dtext = None
handle3drect = None

lines = []
txtall = []
rects = []


def draw_3d(self, context):
    global lines
    draw_line(lines, (1, 1, 0, 1), True, True, 1)



def draw_text_callback(self, context):
    global txtall
    sc = bpy.context.preferences.system.ui_scale    
    left = 100 * sc
    sp = 20 * 1.7 * sc
    top = len(txtall) * sp + 50 * sc
    off = 0
    for p in txtall:
        off += sp
        draw_text( [left, top - off], p)



def draw_text(pos, text):
    if pos == None:
        return
    font_id = 0  # XXX, need to find out how best to get this.
    # draw some text
    sc = bpy.context.preferences.system.ui_scale
    blf.color(font_id, 1, 1, 1, 1)
    blf.position(font_id, pos[0], pos[1], 0)
    blf.size(font_id, math.floor(16 * sc), 72)
    blf.draw(font_id, text)


    
def draw_line(points, color, blend=False, smooth=False, width=1):
    global shader

    if blend:
        bgl.glEnable(bgl.GL_BLEND)
    if smooth:
        bgl.glEnable(bgl.GL_LINE_SMOOTH)

    if width != 1:
        bgl.glLineWidth(width)

    shader.bind()
    shader.uniform_float("color", color)
    batch = batch_for_shader(shader, 'LINES', {"pos": points})
    batch.draw(shader)

    bgl.glDisable(bgl.GL_BLEND)
    bgl.glDisable(bgl.GL_LINE_SMOOTH)
    bgl.glLineWidth(1)   


def draw_rect_callback(self, context):
    global rects
    #vertices = ((100, 100), (300, 100), (100, 200), (300, 200))
    vertices = rects
    indices = ((0, 1, 2), (2, 1, 3))

    shader2d.bind()
    shader2d.uniform_float("color", (0, 0, 0, 0.3))
    batch = batch_for_shader(shader2d, 'TRIS', {"pos": vertices}, indices=indices)
    batch.draw(shader)


def draw_handle_add(arg):
    global handle3d
    print('add draw')
    handle3d = bpy.types.SpaceView3D.draw_handler_add(
        draw_3d, arg, 'WINDOW', 'POST_VIEW')

def text_handle_add(arg):
    global handle3dtext
    print('add text')
    handle3dtext = bpy.types.SpaceView3D.draw_handler_add(
        draw_text_callback, arg, 'WINDOW', 'POST_PIXEL')

def rect_handle_add(arg):
    global handle3drect
    print('add rect')
    handle3drect = bpy.types.SpaceView3D.draw_handler_add(
        draw_rect_callback, arg, 'WINDOW', 'POST_PIXEL')


def draw_handle_remove():    
    global handle3d
    if handle3d != None:
        print('remove draw')
        bpy.types.SpaceView3D.draw_handler_remove(
            handle3d, 'WINDOW')   
    global handle3dtext
    if handle3dtext != None:
        print('remove text')
        bpy.types.SpaceView3D.draw_handler_remove(
            handle3dtext, 'WINDOW')   
    global handle3drect
    if handle3drect != None:
        print('remove rect')
        bpy.types.SpaceView3D.draw_handler_remove(
            handle3drect, 'WINDOW')   
          