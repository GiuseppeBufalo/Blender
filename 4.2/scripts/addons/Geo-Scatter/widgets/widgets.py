# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# (c) 2022 Jakub Uhlik

import time
import datetime
import numpy as np
import ctypes

import bpy
import mathutils
from mathutils import Matrix, Color, Vector, Quaternion
import blf
import gpu
from gpu.types import GPUShader
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

from .shaders import load_shader_code

# DONE: split `ToolTheme` to its own module
# TODO: `ToolOverlay` is obsolete, remove it.. use `widgets.grid.SC5GridOverlay` which provides more options
# TODO: should i `ui_scale` `shadow` and `shadow_offset` values?


class ToolWidgets():
    _cache = {}
    _handlers = []
    _handlers_3d = []
    _initialized = False
    
    DEBUG_MODE = False
    
    # ------------------------------------------------------------------ main >>>
    
    @classmethod
    def init(cls, self, context, ):
        if(cls._initialized):
            return
        
        cls._cache = {}
        # cls._texture_cache = {}
        # cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._draw, (), 'WINDOW', 'POST_PIXEL', )
        
        for a in context.screen.areas:
            if(a.type == 'VIEW_3D'):
                s = a.spaces[0]
                for r in a.regions:
                    if(r.type == 'WINDOW'):
                        h = s.draw_handler_add(cls._draw_2d, (self, context, ), r.type, 'POST_PIXEL', )
                        cls._handlers.append((s, r.type, h, ))
                        
                        h = s.draw_handler_add(cls._draw_3d, (self, context, ), r.type, 'POST_VIEW', )
                        cls._handlers_3d.append((s, r.type, h, ))
        
        cls._initialized = True
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        # bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        # cls._handle = None
        
        for s, a, h in cls._handlers:
            s.draw_handler_remove(h, a, )
        cls._handlers = []
        
        for s, a, h in cls._handlers_3d:
            s.draw_handler_remove(h, a, )
        cls._handlers_3d = []
        
        cls._initialized = False
        cls._cache = {}
        # cls._texture_cache = {}
        cls._tag_redraw()
    
    # ------------------------------------------------------------------ main <<<
    # ------------------------------------------------------------------ elements >>>
    
    @classmethod
    def rectangle_fill_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(((a[0], a[1]), (b[0], a[1]), (a[0], b[1]), (b[0], b[1]), ), dtype=np.float32, )
        indices = np.array(((0, 1, 3), (0, 3, 2)), dtype=np.int32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def rectangle_outline_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(((a[0], a[1]), (b[0], a[1]), (b[0], b[1]), (a[0], b[1]), ), dtype=np.float32, )
        indices = np.array(((0, 1), (1, 2), (2, 3), (3, 0), ), dtype=np.int32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def rectangle_thick_outline_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(((a[0], a[1], 0.0), (b[0], a[1], 0.0), (b[0], b[1], 0.0), (a[0], b[1], 0.0), ), dtype=np.float32, )
        indices = np.array(((0, 1), (1, 2), (2, 3), (3, 0), ), dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def line_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(((a[0], a[1]), (b[0], b[1]), ), dtype=np.float32, )
        indices = np.array(((0, 1), ), dtype=np.int32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def thick_line_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(((a[0], a[1], 0.0, ), (b[0], b[1], 0.0, ), ), dtype=np.float32, )
        indices = np.array(((0, 1), ), dtype=np.int32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def multiple_thick_line_2d(cls, vertices, indices, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(vertices, dtype=np.float32, )
        indices = np.array(indices, dtype=np.int32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def tri_fan_fill_2d(cls, vertices, color=(1.0, 0.0, 0.0, 0.5, ), ):
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices, })
        # NOTE: TRI_FAN deprecated in 3.2
        indices = mathutils.geometry.tessellate_polygon((vertices, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def tri_fan_outline_2d(cls, vertices, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(vertices, dtype=np.float32, )
        i = np.arange(len(vertices))
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def tri_fan_thick_outline_2d(cls, vertices, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(vertices, dtype=np.float32, )
        vertices = np.c_[vertices[:, 0], vertices[:, 1], np.zeros(len(vertices), dtype=vertices.dtype, )]
        i = np.arange(len(vertices))
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def tri_fan_tess_fill_2d(cls, vertices, color=(1.0, 0.0, 0.0, 0.5, ), ):
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        indices = mathutils.geometry.tessellate_polygon((vertices, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def tri_fan_tess_outline_2d(cls, vertices, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(vertices, dtype=np.float32, )
        i = np.arange(len(vertices))
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def tri_fan_tess_thick_outline_2d(cls, vertices, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(vertices, dtype=np.float32, )
        vertices = np.c_[vertices[:, 0], vertices[:, 1], np.zeros(len(vertices), dtype=vertices.dtype, )]
        i = np.arange(len(vertices))
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def circle_fill_2d(cls, center, radius, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vs = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vs, })
        # NOTE: TRI_FAN deprecated in 3.2
        indices = mathutils.geometry.tessellate_polygon((vs, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def circle_outline_2d(cls, center, radius, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vs = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        i = np.arange(steps)
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def circle_thick_outline_2d(cls, center, radius, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        i = np.arange(steps)
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vs, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def circle_thick_outline_dashed_2d(cls, center, radius, steps=32, dash=2, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        # circle > sides * steps > 1 step > 1/2 line and 1/2 gap, so always steps * 2 and magic happen in indices..
        if(dash < 2):
            # otherwise it won't look as round as expected with current `steps`
            dash = 2
        steps = steps * dash
        
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        # magic..
        i = np.arange(steps)
        indices = np.c_[i[::2], i[1::2], ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float("color", color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def circles_path_texture_2d(cls, vertices, radii, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), interpolate=False, interpolate_steps=20, ):
        _, _, width, height = gpu.state.viewport_get()
        
        vertices = np.array(vertices, dtype=np.float32, )
        
        if(interpolate):
            x = vertices[:, 0]
            y = vertices[:, 1]
            ex = x[1:]
            ey = y[1:]
            lsx = np.linspace(x[:-1], ex, interpolate_steps, endpoint=True, )
            lsy = np.linspace(y[:-1], ey, interpolate_steps, endpoint=True, )
            er = radii[1:]
            lsr = np.linspace(radii[:-1], er, interpolate_steps, endpoint=True, )
            vertices = np.c_[lsx.flatten(), lsy.flatten()]
            radii = lsr.flatten()
        
        vertices[:, 0] = -1.0 + (2.0 * (vertices[:, 0] * (1.0 / width)))
        vertices[:, 1] = -1.0 + (2.0 * (vertices[:, 1] * (1.0 / height)))
        
        center = (0, 0, )
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        vs[:, 0] = center[0] + (np.sin(a * angstep) * 1.0)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * 1.0)
        vs[:, 2] = 0.0
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vs, })
        # NOTE: TRI_FAN deprecated in 3.2
        indices = mathutils.geometry.tessellate_polygon((vs, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        
        # z = np.linspace(0.001, 0.002, len(vertices), )
        z = np.linspace(-1.0, -0.999, len(vertices), )
        
        gpu.state.color_mask_set(False, False, False, False, )
        
        with gpu.matrix.push_pop():
            with gpu.matrix.push_pop_projection():
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                shader.bind()
                shader.uniform_float("color", color, )
                for i, v in enumerate(vertices):
                    rx = (2.0 * (radii[i] * (1.0 / width)))
                    ry = (2.0 * (radii[i] * (1.0 / height)))
                    with gpu.matrix.push_pop():
                        vv = Vector((v[0], v[1], z[i]))
                        gpu.matrix.translate(vv)
                        gpu.matrix.scale((rx, ry, ))
                        batch.draw(shader)
        
        gpu.state.color_mask_set(True, True, True, True, )
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            with gpu.matrix.push_pop_projection():
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                shader.bind()
                shader.uniform_float("color", color, )
                for i, v in enumerate(vertices):
                    rx = (2.0 * (radii[i] * (1.0 / width)))
                    ry = (2.0 * (radii[i] * (1.0 / height)))
                    with gpu.matrix.push_pop():
                        vv = Vector((v[0], v[1], z[i]))
                        gpu.matrix.translate(vv)
                        gpu.matrix.scale((rx, ry, ))
                        batch.draw(shader)
        
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def triangle_2d(cls, center, radius, direction, y_offset, color=(1.0, 0.0, 0.0, 0.5, ), ):
        steps = 3
        vertices = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        
        dirangle = np.arctan2(0, 1) - np.arctan2(direction[0], direction[1])
        n = Vector((
            0.0 * np.cos(dirangle) - 1.0 * np.sin(dirangle),
            0.0 * np.sin(dirangle) + 1.0 * np.cos(dirangle),
        ))
        n = n * y_offset
        n = np.array(n, dtype=np.float32, )
        
        a = np.arange(steps, dtype=np.int32, )
        vertices[:, 0] = (np.sin(-dirangle + (a * angstep)) * radius)
        vertices[:, 1] = (np.cos(-dirangle + (a * angstep)) * radius)
        vertices += n.reshape(1, 2)
        c = np.array(center, dtype=np.float32, )
        vertices += c.reshape(1, 2)
        
        indices = np.arange(steps, dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def triangle_outline_2d(cls, center, radius, direction, y_offset, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        steps = 3
        vertices = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        
        dirangle = np.arctan2(0, 1) - np.arctan2(direction[0], direction[1])
        n = Vector((
            0.0 * np.cos(dirangle) - 1.0 * np.sin(dirangle),
            0.0 * np.sin(dirangle) + 1.0 * np.cos(dirangle),
        ))
        n = n * y_offset
        n = np.array(n, dtype=np.float32, )
        
        a = np.arange(steps, dtype=np.int32, )
        vertices[:, 0] = (np.sin(-dirangle + (a * angstep)) * radius)
        vertices[:, 1] = (np.cos(-dirangle + (a * angstep)) * radius)
        vertices += n.reshape(1, 2)
        c = np.array(center, dtype=np.float32, )
        vertices += c.reshape(1, 2)
        
        vertices = np.c_[vertices[:, 0], vertices[:, 1], np.zeros(len(vertices), dtype=np.float32, )]
        
        i = np.arange(steps, dtype=np.int32, )
        indices = np.c_[i, np.roll(i, -1), ]
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def dot_shader_2d(cls, center, diameter=6, bias=0.1, snap=True, color=(1.0, 0.0, 0.0, 0.5, ), ):
        print('`ToolWidgets.dot_shader_3d` is not updated for new style shader creation, do not use. use `ToolWidgets.dot_shader_2_3d` instad')
        return
        
        vert = '''
        in vec2 pos;
        in vec2 uv;
        uniform mat4 ModelViewProjectionMatrix;
        out vec2 iuv;
        
        void main()
        {
            iuv = uv;
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
        }
        '''
        frag = '''
        in vec2 iuv;
        uniform vec4 color;
        uniform float bias;
        out vec4 fragColor;
        
        void main()
        {
            float r = 0.5;
            float d = sqrt(dot(iuv, iuv));
            if(d >= r)
            {
                discard;
            }
            float s = smoothstep(r, r - bias, d);
            vec4 c = vec4(color.r, color.g, color.b, color.a * s);
            fragColor = blender_srgb_to_framebuffer_space(c);
        }
        '''
        
        if(snap):
            # s will be always odd number, so at pixel coordinates it will draw betweeen, this should snap it back to grid
            # TODO: and these are coordinates that look good on mac mouse pointer, check windows and linux
            center = [center[0] - 0.5, center[1] + 0.5, ]
        
        shader = GPUShader(vert, frag, )
        coords = np.array(((0, 0), (1, 0), (1, 1), (0, 1), ), dtype=np.float32, )
        indices = np.array(((0, 1, 2), (0, 2, 3), ), dtype=np.int32, )
        coords = coords - 0.5
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "uv": coords, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.translate(center)
            gpu.matrix.scale((diameter, diameter, ))
            
            shader.bind()
            shader.uniform_float('color', color, )
            shader.uniform_float('bias', bias, )
            
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def dot_shader_3d(cls, matrix, bias=0.1, color=(1.0, 0.0, 0.0, 0.5, ), ):
        print('`ToolWidgets.dot_shader_3d` is not updated for new style shader creation, do not use. use `ToolWidgets.dot_shader_2_3d` instad')
        return
        
        vert = '''
        in vec2 pos;
        in vec2 uv;
        uniform mat4 ModelViewProjectionMatrix;
        out vec2 iuv;
        
        void main()
        {
            iuv = uv;
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
        }
        '''
        frag = '''
        in vec2 iuv;
        uniform vec4 color;
        uniform float bias;
        out vec4 fragColor;
        
        void main()
        {
            float r = 0.5;
            float d = sqrt(dot(iuv, iuv));
            if(d >= r)
            {
                discard;
            }
            float s = smoothstep(r, r - bias, d);
            vec4 c = vec4(color.r, color.g, color.b, color.a * s);
            fragColor = blender_srgb_to_framebuffer_space(c);
        }
        '''
        
        shader = GPUShader(vert, frag, )
        coords = np.array(((0, 0), (1, 0), (1, 1), (0, 1), ), dtype=np.float32, )
        indices = np.array(((0, 1, 2), (0, 2, 3), ), dtype=np.int32, )
        coords = coords - 0.5
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "uv": coords, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            shader.uniform_float('bias', bias, )
            
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def dot_shader_2_2d(cls, center, diameter, snap=True, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vert = '''
        // in vec2 pos;
        // in vec2 uv;
        // uniform mat4 ModelViewProjectionMatrix;
        // uniform vec4 u_viewport;
        // uniform mat4 u_projection;
        // uniform float u_factor;
        // out float offset;
        // out vec2 iuv;
        void main()
        {
            iuv = uv;
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
            float wr = 2.0 / (u_data.u_viewport.z * u_data.u_projection[0][0]);
            float px = gl_Position.w * wr;
            offset = px / u_data.u_factor;
        }
        '''
        frag = '''
        // in vec2 iuv;
        // in float offset;
        // uniform vec4 color;
        // uniform float bias = 0.1;
        // out vec4 fragColor;
        void main()
        {
            vec4 c = vec4(1.0);
            float d = sqrt(dot(iuv, iuv));
            float s = smoothstep(0.5, 0.5 - offset, d);
            c = vec4(u_data.color.r, u_data.color.g, u_data.color.b, u_data.color.a * s);
            fragColor = blender_srgb_to_framebuffer_space(c);
        }
        '''
        
        if(snap):
            # s will be always odd number, so at pixel coordinates it will draw betweeen, this should snap it back to grid
            # TODO: and these are coordinates that look good on mac mouse pointer, check windows and linux
            center = [center[0] - 0.5, center[1] + 0.5, ]
        
        # shader = GPUShader(vert, frag, )
        
        # NOTE: "new style" shader ------------------------------------------- >>>
        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.typedef_source(
            "struct UniformData {\n"
            "    mat4 u_projection;\n"
            "    vec4 u_viewport;\n"
            "    vec4 color;\n"
            "    float u_factor;\n"
            # "    float bias;\n"
            "};\n"
        )
        shader_info.vertex_in(0, 'VEC2', "pos")
        shader_info.vertex_in(1, 'VEC2', "uv")
        shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
        # shader_info.push_constant("VEC4", "u_viewport")
        # shader_info.push_constant("MAT4", "u_projection")
        # shader_info.push_constant("FLOAT", "u_factor")
        # shader_info.push_constant("VEC4", "color")
        # shader_info.push_constant("FLOAT", "bias")
        shader_info.uniform_buf(0, "UniformData", "u_data")
        vert_out = gpu.types.GPUStageInterfaceInfo("vertex_interface")
        vert_out.smooth('FLOAT', "offset")
        vert_out.smooth('VEC2', "iuv")
        shader_info.vertex_out(vert_out)
        shader_info.fragment_out(0, 'VEC4', "fragColor")
        shader_info.vertex_source(vert)
        # NOTE: does not automatically add `blender_srgb_to_framebuffer_space`.. lets provide our own (taken from blender source)
        colorspace = (
        "#undef blender_srgb_to_framebuffer_space\n"
        "vec4 blender_srgb_to_framebuffer_space(vec4 in_color)\n"
        "{\n"
        "    vec3 c = max(in_color.rgb, vec3(0.0));\n"
        "    vec3 c1 = c * (1.0 / 12.92);\n"
        "    vec3 c2 = pow((c + 0.055) * (1.0 / 1.055), vec3(2.4));\n"
        "    in_color.rgb = mix(c1, c2, step(vec3(0.04045), c));\n"
        "    return in_color;\n"
        "}\n"
        )
        shader_info.fragment_source(colorspace + frag)
        shader = gpu.shader.create_from_info(shader_info)
        # NOTE: "new style" shader ------------------------------------------- <<<
        
        coords = np.array(((0, 0), (1, 0), (1, 1), (0, 1), ), dtype=np.float32, )
        indices = np.array(((0, 1, 2), (0, 2, 3), ), dtype=np.int32, )
        coords = coords - 0.5
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "uv": coords, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.translate(center)
            gpu.matrix.scale((diameter, diameter, ))
            
            shader.bind()
            
            # shader.uniform_float('color', color, )
            # shader.uniform_float("u_factor", diameter, )
            # shader.uniform_float("u_viewport", gpu.state.viewport_get(), )
            # shader.uniform_float("u_projection", gpu.matrix.get_projection_matrix(), )
            
            # NOTE: "new style" shader ------------------------------------------- >>>
            
            class _UBO_struct(ctypes.Structure):
                _pack_ = 16
                _fields_ = [
                    # ("ModelViewProjectionMatrix", (ctypes.c_float * 4) * 4),
                    ("u_projection", (ctypes.c_float * 4) * 4),
                    ("u_viewport", ctypes.c_float * 4),
                    ("color", ctypes.c_float * 4),
                    ("u_factor", ctypes.c_float),
                    # ("bias", ctypes.c_float),
                    ("_pad", ctypes.c_float * 3),
                ]
            
            UBO_data = _UBO_struct()
            UBO = gpu.types.GPUUniformBuf(gpu.types.Buffer("UBYTE", ctypes.sizeof(UBO_data), UBO_data))
            
            u_projection = gpu.matrix.get_projection_matrix()
            UBO_data.u_projection[0] = u_projection[0][:]
            UBO_data.u_projection[1] = u_projection[1][:]
            UBO_data.u_projection[2] = u_projection[2][:]
            UBO_data.u_projection[3] = u_projection[3][:]
            UBO_data.u_viewport = gpu.state.viewport_get()
            UBO_data.color = color
            UBO_data.u_factor = diameter
            # UBO_data.bias = 0.1
            
            UBO.update(gpu.types.Buffer("UBYTE", ctypes.sizeof(UBO_data), UBO_data, ))
            shader.uniform_block("u_data", UBO)
            
            # NOTE: "new style" shader ------------------------------------------- <<<
            
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def dot_shader_2_3d(cls, matrix, scale_factor, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vert = '''
        // in vec2 pos;
        // in vec2 uv;
        // uniform mat4 ModelViewProjectionMatrix;
        // uniform vec4 u_viewport;
        // uniform mat4 u_projection;
        // uniform float u_factor;
        // out float offset;
        // out vec2 iuv;
        void main()
        {
            iuv = uv;
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
            
            float wr = 2.0 / (u_data.u_viewport.z * u_data.u_projection[0][0]);
            float px = gl_Position.w * wr;
            offset = px / u_data.u_factor;
        }
        '''
        frag = '''
        // in vec2 iuv;
        // in float offset;
        // uniform vec4 color;
        // // uniform float bias = 0.1;
        // out vec4 fragColor;
        void main()
        {
            vec4 c = vec4(1.0);
            float d = sqrt(dot(iuv, iuv));
            float s = smoothstep(0.5, 0.5 - offset, d);
            
            c = vec4(u_data.color.r, u_data.color.g, u_data.color.b, u_data.color.a * s);
            fragColor = blender_srgb_to_framebuffer_space(c);
        }
        '''
        
        # shader = GPUShader(vert, frag, )
        
        # NOTE: "new style" shader ------------------------------------------- >>>
        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.typedef_source(
            "struct UniformData {\n"
            "    mat4 u_projection;\n"
            "    vec4 u_viewport;\n"
            "    vec4 color;\n"
            "    float u_factor;\n"
            # "    float bias;\n"
            "};\n"
        )
        shader_info.vertex_in(0, 'VEC2', "pos")
        shader_info.vertex_in(1, 'VEC2', "uv")
        shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
        # shader_info.push_constant("VEC4", "u_viewport")
        # shader_info.push_constant("MAT4", "u_projection")
        # shader_info.push_constant("FLOAT", "u_factor")
        # shader_info.push_constant("VEC4", "color")
        # shader_info.push_constant("FLOAT", "bias")
        shader_info.uniform_buf(0, "UniformData", "u_data")
        vert_out = gpu.types.GPUStageInterfaceInfo("vertex_interface")
        vert_out.smooth('FLOAT', "offset")
        vert_out.smooth('VEC2', "iuv")
        shader_info.vertex_out(vert_out)
        shader_info.fragment_out(0, 'VEC4', "fragColor")
        shader_info.vertex_source(vert)
        # NOTE: does not automatically add `blender_srgb_to_framebuffer_space`.. lets provide our own (taken from blender source)
        colorspace = (
        "#undef blender_srgb_to_framebuffer_space\n"
        "vec4 blender_srgb_to_framebuffer_space(vec4 in_color)\n"
        "{\n"
        "    vec3 c = max(in_color.rgb, vec3(0.0));\n"
        "    vec3 c1 = c * (1.0 / 12.92);\n"
        "    vec3 c2 = pow((c + 0.055) * (1.0 / 1.055), vec3(2.4));\n"
        "    in_color.rgb = mix(c1, c2, step(vec3(0.04045), c));\n"
        "    return in_color;\n"
        "}\n"
        )
        shader_info.fragment_source(colorspace + frag)
        shader = gpu.shader.create_from_info(shader_info)
        # NOTE: "new style" shader ------------------------------------------- <<<
        
        coords = np.array(((0, 0), (1, 0), (1, 1), (0, 1), ), dtype=np.float32, )
        indices = np.array(((0, 1, 2), (0, 2, 3), ), dtype=np.int32, )
        coords = coords - 0.5
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "uv": coords, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            
            # shader.uniform_float('color', color, )
            # shader.uniform_float("u_factor", scale_factor)
            # shader.uniform_float("u_viewport", gpu.state.viewport_get())
            # shader.uniform_float("u_projection", gpu.matrix.get_projection_matrix())
            
            # NOTE: "new style" shader ------------------------------------------- >>>
            
            class _UBO_struct(ctypes.Structure):
                _pack_ = 16
                _fields_ = [
                    # ("ModelViewProjectionMatrix", (ctypes.c_float * 4) * 4),
                    ("u_projection", (ctypes.c_float * 4) * 4),
                    ("u_viewport", ctypes.c_float * 4),
                    ("color", ctypes.c_float * 4),
                    ("u_factor", ctypes.c_float),
                    # ("bias", ctypes.c_float),
                    ("_pad", ctypes.c_float * 3),
                ]
            
            UBO_data = _UBO_struct()
            UBO = gpu.types.GPUUniformBuf(gpu.types.Buffer("UBYTE", ctypes.sizeof(UBO_data), UBO_data))
            
            u_projection = gpu.matrix.get_projection_matrix()
            UBO_data.u_projection[0] = u_projection[0][:]
            UBO_data.u_projection[1] = u_projection[1][:]
            UBO_data.u_projection[2] = u_projection[2][:]
            UBO_data.u_projection[3] = u_projection[3][:]
            UBO_data.u_viewport = gpu.state.viewport_get()
            UBO_data.color = color
            UBO_data.u_factor = scale_factor
            # UBO_data.bias = 0.1
            
            UBO.update(gpu.types.Buffer("UBYTE", ctypes.sizeof(UBO_data), UBO_data, ))
            shader.uniform_block("u_data", UBO)
            
            # NOTE: "new style" shader ------------------------------------------- <<<
            
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def cross_thick_outline_2d(cls, center, radius=8, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array((
            (center[0] - radius, center[1], 0.0, ),
            (center[0] + radius, center[1], 0.0, ),
            (center[0], center[1] - radius, 0.0, ),
            (center[0], center[1] + radius, 0.0, ),
        ), dtype=np.float32, )
        indices = np.array(((0, 1), (2, 3)), dtype=np.int32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def label_2d(cls, coords, text, offset=(0, 0), size=11, color=(1.0, 0.0, 0.0, 0.5, ), shadow=True, ):
        font_id = 0
        # ui_scale = bpy.context.preferences.system.ui_scale
        # size = round(size * ui_scale)
        # offset = (offset[0] * ui_scale, offset[1] * ui_scale, )
        
        if(bpy.app.version < (4, 0, 0)):
            blf.size(font_id, size, 72)
        else:
            # 4.0, `dpi` argument is removed
            blf.size(font_id, size)
        blf.color(font_id, *color)
        
        if(shadow):
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
            blf.shadow_offset(font_id, 0, -2)
        
        blf.position(font_id, coords[0] + offset[0], coords[1] + offset[1], 0.0, )
        blf.draw(font_id, text, )
    
    @classmethod
    def tooltip_2d(cls, coords, text, offset=(0, 0), size=11, color=(1.0, 0.0, 0.0, 0.5, ), shadow=True, padding=5, bgfill=(1.0, 0.0, 0.0, 0.5, ), bgoutline=(1.0, 0.0, 0.0, 0.5, ), thickness=2, ):
        font_id = 0
        ui_scale = bpy.context.preferences.system.ui_scale
        # size = round(size * ui_scale)
        # offset = (offset[0] * ui_scale, offset[1] * ui_scale, )
        # padding = padding * ui_scale
        
        if(bpy.app.version < (4, 0, 0)):
            blf.size(font_id, size, 72)
        else:
            # 4.0, `dpi` argument is removed
            blf.size(font_id, size)
        blf.color(font_id, *color)
        
        if(shadow):
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
            blf.shadow_offset(font_id, 0, -2)
        
        blf.position(font_id, coords[0] + offset[0], coords[1] + offset[1], 0.0, )
        
        if(bgfill is not None or bgoutline is not None):
            x, y = coords
            x += offset[0]
            # correct a bit to look better..
            y += offset[1] - (1 * ui_scale)
            # y += offset[1] - 1
            w, _ = blf.dimensions(font_id, text, )
            _, h = blf.dimensions(font_id, 'A', )
            a = (x - padding, y - padding, )
            b = (x + w + padding, y + h + padding, )
            if(bgfill is not None):
                cls.rectangle_fill_2d(a, b, color=bgfill, )
            if(bgoutline is not None):
                # cls.rectangle_outline_2d(a, b, color=bgoutline, )
                cls.rectangle_thick_outline_2d(a, b, color=bgoutline, thickness=thickness, )
        
        blf.draw(font_id, text, )
    
    @classmethod
    def rounded_rectangle_fill_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), steps=32, radius=5.0, ):
        c = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        aa = np.arange(steps, dtype=np.int32, )
        c[:, 0] = np.sin(aa * angstep) * radius
        c[:, 1] = np.cos(aa * angstep) * radius
        
        q = int(steps / 4)
        trc = c[:q + 1].copy()
        brc = c[q:q * 2 + 1].copy()
        blc = c[q * 2:q * 3 + 1].copy()
        tlc = c[q * 3:].copy()
        tlc = np.concatenate([tlc, c[0].copy().reshape((-1, 2))])
        
        trc[:, 0] += b[0] - radius
        trc[:, 1] += b[1] - radius
        brc[:, 0] += b[0] - radius
        brc[:, 1] += a[1] + radius
        blc[:, 0] += a[0] + radius
        blc[:, 1] += a[1] + radius
        tlc[:, 0] += a[0] + radius
        tlc[:, 1] += b[1] - radius
        
        vertices = np.concatenate([trc, brc, blc, tlc, ])
        indices = np.array(mathutils.geometry.tessellate_polygon((vertices, )), dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def rounded_rectangle_outline_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), steps=32, radius=5.0, thickness=2.0, ):
        c = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        aa = np.arange(steps, dtype=np.int32, )
        c[:, 0] = np.sin(aa * angstep) * radius
        c[:, 1] = np.cos(aa * angstep) * radius
        
        q = int(steps / 4)
        trc = c[:q + 1].copy()
        brc = c[q:q * 2 + 1].copy()
        blc = c[q * 2:q * 3 + 1].copy()
        tlc = c[q * 3:].copy()
        tlc = np.concatenate([tlc, c[0].copy().reshape((-1, 2))])
        
        trc[:, 0] += b[0] - radius
        trc[:, 1] += b[1] - radius
        brc[:, 0] += b[0] - radius
        brc[:, 1] += a[1] + radius
        blc[:, 0] += a[0] + radius
        blc[:, 1] += a[1] + radius
        tlc[:, 0] += a[0] + radius
        tlc[:, 1] += b[1] - radius
        
        vertices = np.concatenate([trc, brc, blc, tlc, ])
        vertices = np.c_[vertices[:, 0], vertices[:, 1], np.zeros(len(vertices), dtype=vertices.dtype, )]
        i = np.arange(len(vertices))
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        # shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def fancy_tooltip_2d(cls, coords, text, offset=(0, 0), align=None, size=11, color=(1.0, 0.0, 0.0, 0.5, ), shadow=True, padding=5, steps=32, radius=5.0, bgfill=(1.0, 0.0, 0.0, 0.5, ), bgoutline=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        font_id = 0
        ui_scale = bpy.context.preferences.system.ui_scale
        # size = round(size * ui_scale)
        # offset = (offset[0] * ui_scale, offset[1] * ui_scale, )
        # padding = padding * ui_scale
        # radius = radius * ui_scale
        
        if(bpy.app.version < (4, 0, 0)):
            blf.size(font_id, size, 72)
        else:
            # 4.0, `dpi` argument is removed
            blf.size(font_id, size)
        blf.color(font_id, *color)
        
        if(shadow):
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
            blf.shadow_offset(font_id, 0, -2)
        
        if(align):
            if(align == 'CENTER'):
                w, _ = blf.dimensions(font_id, text, )
                _, h = blf.dimensions(font_id, 'A', )
                wh = int(w / 2)
                hh = int(h / 2)
                coords = (coords[0] - wh, coords[1] - hh, )
        
        blf.position(font_id, coords[0] + offset[0], coords[1] + offset[1], 0.0, )
        
        if(bgfill is not None or bgoutline is not None):
            x, y = coords
            x += offset[0]
            # correct a bit to look better..
            y += offset[1] - (1 * ui_scale)
            # y += offset[1] - 1
            w, _ = blf.dimensions(font_id, text, )
            _, h = blf.dimensions(font_id, 'A', )
            a = (x - padding, y - padding, )
            b = (x + w + padding, y + h + padding, )
            if(bgfill is not None):
                cls.rounded_rectangle_fill_2d(a, b, color=bgfill, steps=steps, radius=radius, )
            if(bgoutline is not None):
                cls.rounded_rectangle_outline_2d(a, b, color=bgoutline, steps=steps, radius=radius, thickness=thickness, )
        
        blf.draw(font_id, text, )
    
    @classmethod
    def fancy_switch_2d(cls, state, coords, dimensions, offset=(0, 0), align=None, color=(1.0, 0.0, 0.0, 0.5, ), steps=32, radius=5.0, bgfill=(1.0, 0.0, 0.0, 0.5, ), bgoutline=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        # ui_scale = bpy.context.preferences.system.ui_scale
        # dimensions = (dimensions[0] * ui_scale, dimensions[1] * ui_scale, )
        # offset = (offset[0] * ui_scale, offset[1] * ui_scale, )
        # radius = radius * ui_scale
        
        if(align):
            if(align == 'CENTER'):
                wh = int(dimensions[0] / 2)
                hh = int(dimensions[1] / 2)
                coords = (coords[0] - wh, coords[1] - hh, )
        
        coords = (coords[0] + offset[0], coords[1] + offset[1], )
        
        a = coords
        b = (coords[0] + dimensions[0], coords[1] + dimensions[1], )
        
        cls.rounded_rectangle_fill_2d(a, b, color=bgfill, steps=steps, radius=radius, )
        cls.rounded_rectangle_outline_2d(a, b, color=bgoutline, steps=steps, radius=radius, thickness=thickness, )
        center = (coords[0] + radius, coords[1] + radius)
        if(state):
            center = (coords[0] + dimensions[0] - radius, coords[1] + radius)
        # cls.circle_fill_2d(center, radius, steps=steps, color=bgfill, )
        r = radius * 0.7
        if(state):
            cls.circle_fill_2d(center, r, steps=steps, color=bgoutline, )
        # else:
        #     c = bgoutline[:3] + (bgoutline[3] / 10, )
        #     cls.circle_fill_2d(center, r, steps=steps, color=c, )
        cls.circle_thick_outline_2d(center, r, steps=steps, color=bgoutline, thickness=thickness, )
    
    @classmethod
    def fancy_button_2d(cls, text, state, coords, dimensions, offset=(0, 0), size=11, color=(1.0, 0.0, 0.0, 0.5, ), shadow=True, steps=32, radius=5.0, bgfill=(1.0, 0.0, 0.0, 0.5, ), bgoutline=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        coords = (coords[0] - int(dimensions[0] / 2), coords[1] - int(dimensions[1] / 2), )
        coords = (coords[0] + offset[0], coords[1] + offset[1], )
        a = coords
        b = (coords[0] + dimensions[0], coords[1] + dimensions[1], )
        
        if(state):
            # c = tuple(color[:3])
            # ca = (color[3], )
            # color = tuple(bgfill[:3]) + ca
            # bgfill = c + (bgfill[3], )
            
            # selected bg is text color + bg alpha
            bgfill = tuple(color[:3]) + (bgfill[3], )
            # selected text color is inverted with original alpha
            color = tuple(np.array(1.0 - np.array(color[:3])).tolist()) + (color[3], )
        
        cls.rounded_rectangle_fill_2d(a, b, color=bgfill, steps=steps, radius=radius, )
        cls.rounded_rectangle_outline_2d(a, b, color=bgoutline, steps=steps, radius=radius, thickness=thickness, )
        
        font_id = 0
        ui_scale = bpy.context.preferences.system.ui_scale
        if(bpy.app.version < (4, 0, 0)):
            blf.size(font_id, size, 72)
        else:
            # 4.0, `dpi` argument is removed
            blf.size(font_id, size)
        blf.color(font_id, *color)
        if(shadow):
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
            blf.shadow_offset(font_id, 0, -2)
        
        w, _ = blf.dimensions(font_id, text, )
        _, h = blf.dimensions(font_id, 'A', )
        wh = int(w / 2)
        hh = int(h / 2)
        coords = (coords[0] + int(dimensions[0] / 2) - wh, coords[1] + int(dimensions[1] / 2) - hh, )
        blf.position(font_id, coords[0], coords[1], 0.0, )
        blf.draw(font_id, text, )
    
    @classmethod
    def label_multiline_left_flag_2d(cls, coords, lines=[], offset=(0, 0), size=11, color=(1.0, 0.0, 0.0, 0.5, ), shadow=True, padding=5, ):
        font_id = 0
        # ui_scale = bpy.context.preferences.system.ui_scale
        # size = round(size * ui_scale)
        # offset = (offset[0] * ui_scale, offset[1] * ui_scale, )
        # padding = padding * ui_scale
        
        if(bpy.app.version < (4, 0, 0)):
            blf.size(font_id, size, 72)
        else:
            # 4.0, `dpi` argument is removed
            blf.size(font_id, size)
        blf.color(font_id, *color)
        
        if(shadow):
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.5)
            blf.shadow_offset(font_id, 0, -2)
        
        _, h = blf.dimensions(font_id, "F", )
        
        coords = (coords[0], coords[1] - h, )
        
        for i, t in enumerate(lines):
            blf.position(font_id, coords[0] + offset[0], coords[1] - (i * (h + padding)) + offset[1], 0.0, )
            blf.draw(font_id, t, )
    
    @classmethod
    def arrow_outline_2d(cls, a, b, arrow_head_height_pixels=10, arrow_head_angle_degrees=20, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        cls.thick_line_2d(a, b, color, thickness, )
        
        d = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        if(d < arrow_head_height_pixels * 1.5):
            arrow_head_height_pixels = d * (1 / 1.5)
        if(arrow_head_height_pixels <= 0.0):
            return
        
        r1 = np.radians(arrow_head_angle_degrees)
        r2 = np.radians(360 - arrow_head_angle_degrees)
        n = a - b
        n.normalize()
        x = n[0] * np.cos(r1) - n[1] * np.sin(r1)
        y = n[0] * np.sin(r1) + n[1] * np.cos(r1)
        b1 = Vector(b) + Vector((x, y)) * arrow_head_height_pixels
        x = n[0] * np.cos(r2) - n[1] * np.sin(r2)
        y = n[0] * np.sin(r2) + n[1] * np.cos(r2)
        b2 = Vector(b) + Vector((x, y)) * arrow_head_height_pixels
        
        cls.thick_line_2d(b, b1, color, thickness, )
        cls.thick_line_2d(b, b2, color, thickness, )
    
    @classmethod
    def circle_outline_3d(cls, matrix, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        i = np.arange(steps)
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def circle_outline_dashed_3d(cls, matrix, steps=32, dash=2, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        # circle > sides * steps > 1 step > 1/2 line and 1/2 gap, so always steps * 2 and magic happen in indices..
        if(dash < 2):
            # otherwise it won't look as round as expected with current `steps`
            dash = 2
        steps = steps * dash
        
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        # magic..
        i = np.arange(steps)
        indices = np.c_[i[::2], i[1::2], ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def circle_fill_3d(cls, matrix, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vs, }, )
        # NOTE: TRI_FAN deprecated in 3.2
        indices = mathutils.geometry.tessellate_polygon((vs, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def triangle_outline_3d(cls, offset, matrix, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        steps = 3
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        vs[:, 0] += offset[0]
        vs[:, 1] += offset[1]
        vs[:, 2] += offset[2]
        
        i = np.arange(steps)
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def triangle_fill_3d(cls, offset, matrix, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        steps = 3
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        vs[:, 0] += offset[0]
        vs[:, 1] += offset[1]
        vs[:, 2] += offset[2]
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vs, }, )
        # NOTE: TRI_FAN deprecated in 3.2
        indices = mathutils.geometry.tessellate_polygon((vs, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def sharp_triangle_outline_3d(cls, offset, matrix, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        steps = 12
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        m = np.zeros(steps, dtype=bool, )
        m[0] = True
        m[5] = True
        m[7] = True
        vs = vs[m]
        
        vs[:, 0] += offset[0]
        vs[:, 1] += offset[1]
        vs[:, 2] += offset[2]
        
        i = np.arange(3)
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def sharp_triangle_fill_3d(cls, offset, matrix, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        steps = 12
        vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        m = np.zeros(steps, dtype=bool, )
        m[0] = True
        m[5] = True
        m[7] = True
        vs = vs[m]
        
        vs[:, 0] += offset[0]
        vs[:, 1] += offset[1]
        vs[:, 2] += offset[2]
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'TRI_FAN', {"pos": vs, }, )
        # NOTE: TRI_FAN deprecated in 3.2
        # indices = mathutils.geometry.tessellate_polygon((vs, ))
        indices = np.arange(3, dtype=np.int32, )
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def thick_line_3d(cls, a, b, matrix, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(((a[0], a[1], a[2], ), (b[0], b[1], b[2], ), ), dtype=np.float32, )
        indices = np.array(((0, 1), ), dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def arrow_3d(cls, point, length, matrix, color=(1.0, 0.0, 0.0, 0.5, ), outer_radius=1 / 20, inner_radius=1 / 60, shoulder_offset=1 / 5, steps=16, ):
        # ---------- vertices ----------
        if(length - shoulder_offset <= 0.0):
            # NOTE: fix situation when total arrow length is smaller that its head offset by drawing only head in total length and adjusted outer radius for it length
            beta = np.arctan(outer_radius / shoulder_offset)
            outer_radius = length * np.tan(beta)
            inner_radius = outer_radius
            shoulder_offset = length
        
        # foot
        foot_vs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        foot_vs[:, 0] = 0.0 + (np.sin(a * angstep) * inner_radius)
        foot_vs[:, 1] = 0.0 + (np.cos(a * angstep) * inner_radius)
        foot_vs = np.concatenate([np.zeros((1, 3), dtype=np.float32, ), foot_vs])
        # body
        body_vsa = foot_vs[1:].copy()
        body_vsb = body_vsa.copy()
        body_vsb[:, 2] = length - shoulder_offset
        body_vs = np.concatenate([body_vsa, body_vsb])
        # shoulder
        shoulder_vsa = body_vsb.copy()
        shoulder_vsb = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        shoulder_vsb[:, 0] = 0.0 + (np.sin(a * angstep) * outer_radius)
        shoulder_vsb[:, 1] = 0.0 + (np.cos(a * angstep) * outer_radius)
        shoulder_vsb[:, 2] = length - shoulder_offset
        shoulder_vs = np.concatenate([shoulder_vsa, shoulder_vsb])
        # head
        head_vs = shoulder_vsb.copy()
        p = np.zeros((1, 3), dtype=np.float32, )
        p[:, 2] = length
        head_vs = np.concatenate([head_vs, p])
        
        # ---------- indices ----------
        # foot
        i = np.arange(steps)
        foot_iis = np.c_[np.zeros(steps, dtype=np.int32), i + 1, np.roll(i, -1) + 1]
        # body
        l = len(foot_vs)
        i = np.arange(steps)
        body_iisa = np.c_[i, np.roll(i, -1), i + steps]
        body_iisa += l
        body_iisb = np.c_[np.roll(i, -1), i + steps, np.roll(np.array(i + steps), -1)]
        body_iisb += l
        body_iis = np.concatenate([body_iisa, body_iisb])
        # shoulder
        l = len(foot_vs) + len(body_vs)
        i = np.arange(steps)
        shoulder_iisa = np.c_[i, np.roll(i, -1), i + steps]
        shoulder_iisa += l
        shoulder_iisb = np.c_[np.roll(i, -1), i + steps, np.roll(np.array(i + steps), -1)]
        shoulder_iisb += l
        shoulder_iis = np.concatenate([shoulder_iisa, shoulder_iisb])
        # head
        l = len(foot_vs) + len(body_vs) + len(shoulder_vs)
        i = np.arange(steps)
        head_iis = np.c_[i, np.roll(i, -1), np.full(steps, steps, dtype=np.int32)]
        head_iis += l
        
        # ---------- combine ----------
        vertices = np.concatenate([foot_vs, body_vs, shoulder_vs, head_vs])
        vertices = vertices.astype(np.float32)
        indices = np.concatenate([foot_iis, body_iis, shoulder_iis, head_iis])
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        # gpu.state.face_culling_set('BACK')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
        # gpu.state.face_culling_set('NONE')
    
    @classmethod
    def box_3d(cls, side_length, matrix, offset=(0.0, 0.0, 0.0, ), color=(1.0, 0.0, 0.0, 0.5, ), ):
        l = side_length / 2
        vertices = np.array([(-l, -l, -l), (-l, -l, l), (-l, l, -l), (-l, l, l), (l, -l, -l), (l, -l, l), (l, l, -l), (l, l, l), ], dtype=np.float32, )
        vertices += offset
        indices = np.array([(1, 2, 0), (3, 6, 2), (7, 4, 6), (5, 0, 4), (6, 0, 2), (3, 5, 7), (1, 3, 2), (3, 7, 6), (7, 5, 4), (5, 1, 0), (6, 4, 0), (3, 1, 5), ], dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def box_outline_3d(cls, side_length, matrix, offset=(0.0, 0.0, 0.0, ), color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        l = side_length / 2
        vertices = np.array([(-l, -l, -l), (-l, -l, l), (-l, l, -l), (-l, l, l), (l, -l, -l), (l, -l, l), (l, l, -l), (l, l, l), ], dtype=np.float32, )
        vertices += offset
        indices = np.array([(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4), (0, 4), (1, 5), (2, 6), (3, 7), ], dtype=np.int32, )
        cls.multiple_thick_lines_3d(vertices, indices, matrix, color, thickness, )
    
    @classmethod
    def icosphere_3d(cls, radius, matrix, offset=(0.0, 0.0, 0.0, ), color=(1.0, 0.0, 0.0, 0.5, ), ):
        vs = [(0.0, 0.0, -1.0), (0.7236073017120361, -0.5257253050804138, -0.44721952080726624), (-0.276388019323349, -0.8506492376327515, -0.4472198486328125), (-0.8944262266159058, 0.0, -0.44721561670303345), (-0.276388019323349, 0.8506492376327515, -0.4472198486328125), (0.7236073017120361, 0.5257253050804138, -0.44721952080726624), (0.276388019323349, -0.8506492376327515, 0.4472198486328125), (-0.7236073017120361, -0.5257253050804138, 0.44721952080726624), (-0.7236073017120361, 0.5257253050804138, 0.44721952080726624), (0.276388019323349, 0.8506492376327515, 0.4472198486328125), (0.8944262266159058, 0.0, 0.44721561670303345), (0.0, 0.0, 1.0), (-0.16245555877685547, -0.49999526143074036, -0.8506544232368469), (0.42532268166542053, -0.30901139974594116, -0.8506541848182678), (0.26286882162094116, -0.8090116381645203, -0.5257376432418823), (0.8506478667259216, 0.0, -0.5257359147071838), (0.42532268166542053, 0.30901139974594116, -0.8506541848182678), (-0.525729775428772, 0.0, -0.8506516814231873), (-0.6881893873214722, -0.49999693036079407, -0.5257362127304077), (-0.16245555877685547, 0.49999526143074036, -0.8506544232368469), (-0.6881893873214722, 0.49999693036079407, -0.5257362127304077), (0.26286882162094116, 0.8090116381645203, -0.5257376432418823), (0.9510578513145447, -0.30901262164115906, 0.0), (0.9510578513145447, 0.30901262164115906, 0.0), (0.0, -0.9999999403953552, 0.0), (0.5877856016159058, -0.8090167045593262, 0.0), (-0.9510578513145447, -0.30901262164115906, 0.0), (-0.5877856016159058, -0.8090167045593262, 0.0), (-0.5877856016159058, 0.8090167045593262, 0.0), (-0.9510578513145447, 0.30901262164115906, 0.0), (0.5877856016159058, 0.8090167045593262, 0.0), (0.0, 0.9999999403953552, 0.0), (0.6881893873214722, -0.49999693036079407, 0.5257362127304077), (-0.26286882162094116, -0.8090116381645203, 0.5257376432418823), (-0.8506478667259216, 0.0, 0.5257359147071838), (-0.26286882162094116, 0.8090116381645203, 0.5257376432418823), (0.6881893873214722, 0.49999693036079407, 0.5257362127304077), (0.16245555877685547, -0.49999526143074036, 0.8506543636322021), (0.525729775428772, 0.0, 0.8506516814231873), (-0.42532268166542053, -0.30901139974594116, 0.8506541848182678), (-0.42532268166542053, 0.30901139974594116, 0.8506541848182678), (0.16245555877685547, 0.49999526143074036, 0.8506543636322021)]
        fs = [(0, 13, 12), (1, 13, 15), (0, 12, 17), (0, 17, 19), (0, 19, 16), (1, 15, 22), (2, 14, 24), (3, 18, 26), (4, 20, 28), (5, 21, 30), (1, 22, 25), (2, 24, 27), (3, 26, 29), (4, 28, 31), (5, 30, 23), (6, 32, 37), (7, 33, 39), (8, 34, 40), (9, 35, 41), (10, 36, 38), (38, 41, 11), (38, 36, 41), (36, 9, 41), (41, 40, 11), (41, 35, 40), (35, 8, 40), (40, 39, 11), (40, 34, 39), (34, 7, 39), (39, 37, 11), (39, 33, 37), (33, 6, 37), (37, 38, 11), (37, 32, 38), (32, 10, 38), (23, 36, 10), (23, 30, 36), (30, 9, 36), (31, 35, 9), (31, 28, 35), (28, 8, 35), (29, 34, 8), (29, 26, 34), (26, 7, 34), (27, 33, 7), (27, 24, 33), (24, 6, 33), (25, 32, 6), (25, 22, 32), (22, 10, 32), (30, 31, 9), (30, 21, 31), (21, 4, 31), (28, 29, 8), (28, 20, 29), (20, 3, 29), (26, 27, 7), (26, 18, 27), (18, 2, 27), (24, 25, 6), (24, 14, 25), (14, 1, 25), (22, 23, 10), (22, 15, 23), (15, 5, 23), (16, 21, 5), (16, 19, 21), (19, 4, 21), (19, 20, 4), (19, 17, 20), (17, 3, 20), (17, 18, 3), (17, 12, 18), (12, 2, 18), (15, 16, 5), (15, 13, 16), (13, 0, 16), (12, 14, 2), (12, 13, 14), (13, 1, 14)]
        
        vertices = np.array(vs, dtype=np.float32, )
        
        '''
        l = len(vertices)
        ones = np.ones(l, dtype=vertices.dtype, )
        vs = np.c_[vertices[:, 0], vertices[:, 1], vertices[:, 2], ones]
        # model = np.array(Matrix(((radius, 0.0, 0.0, 0.0), (0.0, radius, 0.0, 0.0), (0.0, 0.0, radius, 0.0), (0.0, 0.0, 0.0, 1.0))))
        model = np.array(Matrix.Scale(radius, 4))
        vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        vertices = vs[:, 0:3].astype(np.float32)
        '''
        
        indices = np.array(fs, dtype=np.int32, )
        # vertices += np.array(offset, dtype=np.float32, ) * (1 / radius)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.scale((radius, radius, radius, ))
            
            msi = Matrix.Scale(radius, 4).inverted()
            l, r, s = matrix.decompose()
            mt = Matrix.Translation(msi @ l).to_4x4()
            mr = r.to_matrix().to_4x4()
            matrix = mt @ mr
            gpu.matrix.multiply_matrix(matrix)
            
            gpu.matrix.translate(np.array(offset, dtype=np.float32, ) * (1 / radius))
            
            shader.bind()
            shader.uniform_float('color', color, )
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def cone_3d(cls, height, matrix, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        cvs = np.zeros((steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        cvs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        cvs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        tip = np.zeros((1, 3), dtype=np.float32, )
        tip[0][2] = height
        vs = np.concatenate([cvs, np.zeros((1, 3), dtype=np.float32, ), tip, ])
        
        a = np.arange(steps, dtype=np.int32, )
        ctris = np.c_[np.full(steps, steps), a, np.roll(a, -1), ]
        ttris = np.c_[np.full(steps, steps + 1), a, np.roll(a, -1), ]
        indices = np.concatenate([ctris, ttris])
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def cylinder_3d(cls, height, offset, matrix, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        center = [0.0, 0.0, ]
        radius = 1.0
        
        cvs1 = np.zeros((steps, 3), dtype=np.float32, )
        cvs1[:, 0] = center[0] + (np.sin(a * angstep) * radius)
        cvs1[:, 1] = center[1] + (np.cos(a * angstep) * radius)
        
        cvs2 = cvs1.copy()
        cvs2[:, 2] += height
        
        vertices = np.concatenate([cvs1, cvs2])
        # vertices = vertices.astype(np.float32)
        
        vertices[:, 0] += offset[0]
        vertices[:, 1] += offset[1]
        vertices[:, 2] += offset[2]
        
        indices1 = np.array(mathutils.geometry.tessellate_polygon((cvs1, )), dtype=np.int32, )
        # indices2 = np.array(mathutils.geometry.tessellate_polygon((cvs2, )), dtype=np.int32, )
        indices2 = indices1.copy()
        indices2 += len(cvs1)
        
        i = np.arange(steps, dtype=np.int32, )
        a = np.c_[i, np.roll(i, -1), ]
        i += steps
        # b = np.c_[np.roll(i, -1), i, ]
        b = np.c_[i, np.roll(i, -1), ]
        a1 = np.c_[a[:, 0], a[:, 1], b[:, 0]]
        b1 = np.c_[b[:, 0], b[:, 1], a[:, 1]]
        indices3 = np.concatenate([a1, b1, ])
        
        indices = np.concatenate([indices1, indices2, indices3])
        # indices = np.concatenate([indices1, indices2, ])
        # indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def multiple_thick_lines_3d(cls, vertices, indices, matrix, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(vertices, dtype=np.float32, )
        indices = np.array(indices, dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def multiple_triangles_3d(cls, vertices, indices, matrix, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = vertices.astype(np.float32)
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def multiple_thick_lines_flat_3d(cls, vertices, indices, colors, matrix, thickness=2.0, ):
        vertices = np.array(vertices, dtype=np.float32, )
        indices = np.array(indices, dtype=np.int32, )
        colors = np.array(colors, dtype=np.float32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_FLAT_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_FLAT_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, 'color': colors, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            # shader.uniform_float('color', color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def multiple_triangles_flat_3d(cls, vertices, indices, colors, matrix, ):
        vertices = vertices.astype(np.float32)
        indices = indices.astype(np.int32)
        colors = colors.astype(np.float32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_FLAT_COLOR')
        else:
            shader = gpu.shader.from_builtin('FLAT_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, 'color': colors, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            # shader.uniform_float('color', color, )
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def square_fill_3d(cls, co, no, edge_length=1.0, color=(1.0, 0.0, 0.0, 0.5, ), ):
        co = Vector(co)
        no = Vector(no)
        
        # d ----- c
        # |     / | + h
        # |  0.0  | el
        # | /     | - h
        # a ----- b
        h = edge_length / 2
        vertices = [
            Vector((-h, -h, 0.0, )),
            Vector((h, -h, 0.0, )),
            Vector((h, h, 0.0, )),
            Vector((-h, h, 0.0, )),
        ]
        indices = [
            (0, 1, 2),
            (0, 2, 3),
        ]
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        
        mt = Matrix.Translation(co)
        
        up = Vector((0.0, 1.0, 0.0, ))
        x = up.cross(no)
        x.normalize()
        y = no.cross(x)
        y.normalize()
        mr = Matrix()
        mr[0][0] = x.x
        mr[0][1] = y.x
        mr[0][2] = no.x
        mr[1][0] = x.y
        mr[1][1] = y.y
        mr[1][2] = no.y
        mr[2][0] = x.z
        mr[2][1] = y.z
        mr[2][2] = no.z
        
        matrix = mt.to_4x4() @ mr.to_4x4()
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def rectangle_fill_3d(cls, a, b, matrix, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(((a[0], a[1], 0.0), (b[0], a[1], 0.0), (a[0], b[1], 0.0), (b[0], b[1], 0.0), ), dtype=np.float32, )
        indices = np.array(((0, 1, 3), (0, 3, 2), ), dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def rectangle_outline_3d(cls, a, b, matrix, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(((a[0], a[1], 0.0), (b[0], a[1], 0.0), (a[0], b[1], 0.0), (b[0], b[1], 0.0), ), dtype=np.float32, )
        indices = np.array(((0, 1), (1, 3), (3, 2), (2, 0), ), dtype=np.int32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float('color', color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def wedge_thick_outline_2d(cls, center, radius, angle, offset, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        if(angle < 0.0):
            offset += angle
            angle = abs(angle)
        
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        aa = a * angstep
        aa = aa[aa < angle]
        aa = np.concatenate([aa, np.array([angle, ], dtype=aa.dtype, )])
        aa = aa + offset
        
        vs = np.zeros((len(aa), 3), dtype=np.float32, )
        vs[:, 0] = center[0] + (np.sin(aa) * radius)
        vs[:, 1] = center[1] + (np.cos(aa) * radius)
        vs = np.concatenate([vs, np.array([center[0], center[1], 0.0, ], dtype=vs.dtype, ).reshape(-1, 3)])
        
        i = np.arange(len(aa) + 1)
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vs, }, indices=indices, )
        
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        
        gpu.state.blend_set('NONE')
    
    @classmethod
    def wedge_fill_2d(cls, center, radius, angle, offset, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        if(angle < 0.0):
            offset += angle
            angle = abs(angle)
        
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        aa = a * angstep
        aa = aa[aa < angle]
        aa = np.concatenate([aa, np.array([angle, ], dtype=aa.dtype, )])
        aa = aa + offset
        
        vs = np.zeros((len(aa), 2), dtype=np.float32, )
        vs[:, 0] = center[0] + (np.sin(aa) * radius)
        vs[:, 1] = center[1] + (np.cos(aa) * radius)
        vs = np.concatenate([vs, np.array([center[0], center[1], ], dtype=vs.dtype, ).reshape(-1, 2)])
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        indices = mathutils.geometry.tessellate_polygon((vs, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def wedge_thick_outline_3d(cls, matrix, angle, offset, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        if(angle < 0.0):
            offset += angle
            angle = abs(angle)
        
        center = [0.0, 0.0, ]
        radius = 1.0
        
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        aa = a * angstep
        aa = aa[aa < angle]
        aa = np.concatenate([aa, np.array([angle, ], dtype=aa.dtype, )])
        aa = aa + offset
        
        vs = np.zeros((len(aa), 3), dtype=np.float32, )
        vs[:, 0] = center[0] + (np.sin(aa) * radius)
        vs[:, 1] = center[1] + (np.cos(aa) * radius)
        vs = np.concatenate([vs, np.array([center[0], center[1], 0.0, ], dtype=vs.dtype, ).reshape(-1, 3)])
        
        i = np.arange(len(aa) + 1)
        indices = np.c_[i, np.roll(i, -1), ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            # shader.uniform_float("lineSmooth", True, )
            shader.uniform_float("lineWidth", thickness, )
            _, _, w, h = gpu.state.viewport_get()
            shader.uniform_float("viewportSize", (w, h, ))
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def wedge_fill_3d(cls, matrix, angle, offset, steps=32, color=(1.0, 0.0, 0.0, 0.5, ), ):
        if(angle < 0.0):
            offset += angle
            angle = abs(angle)
        
        center = [0.0, 0.0, ]
        radius = 1.0
        
        angstep = 2 * np.pi / steps
        a = np.arange(steps, dtype=np.int32, )
        aa = a * angstep
        aa = aa[aa < angle]
        aa = np.concatenate([aa, np.array([angle, ], dtype=aa.dtype, )])
        aa = aa + offset
        
        vs = np.zeros((len(aa), 3), dtype=np.float32, )
        vs[:, 0] = center[0] + (np.sin(aa) * radius)
        vs[:, 1] = center[1] + (np.cos(aa) * radius)
        vs = np.concatenate([vs, np.array([center[0], center[1], 0.0, ], dtype=vs.dtype, ).reshape(-1, 3)])
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        indices = mathutils.geometry.tessellate_polygon((vs, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def points_px_3d(cls, vertices, matrix, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(vertices, dtype=np.float32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'POINTS', {"pos": vertices, }, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("color", color, )
            
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def points_px_colors_3d(cls, vertices, colors, matrix, ):
        vertices = np.array(vertices, dtype=np.float32, )
        colors = np.array(colors, dtype=np.float32, )
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_FLAT_COLOR')
        else:
            shader = gpu.shader.from_builtin('FLAT_COLOR')
        # shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        batch = batch_for_shader(shader, 'POINTS', {"pos": vertices, "color": colors, }, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            
            batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def round_points_px_3d(cls, vertices, matrix, size=6, color=(1.0, 0.0, 0.0, 0.5, ), ):
        vertices = np.array(vertices, dtype=np.float32, )
        
        vert = '''
        // in vec3 pos;
        // uniform mat4 ModelViewProjectionMatrix;
        // uniform float size;
        void main()
        {
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
            gl_PointSize = size;
        }
        '''
        # NOTE: for some reason it was jumping between color spaces.. i redefined `blender_srgb_to_framebuffer_space` so there is no condition
        frag = '''
        // uniform vec4 color;
        // out vec4 fragColor;
        vec4 blender_srgb_to_framebuffer_space_always(vec4 in_color)
        {
            vec3 c = max(in_color.rgb, vec3(0.0));
            vec3 c1 = c * (1.0 / 12.92);
            vec3 c2 = pow((c + 0.055) * (1.0 / 1.055), vec3(2.4));
            in_color.rgb = mix(c1, c2, step(vec3(0.04045), c));
            return in_color;
        }
        void main()
        {
            float radius = 1.0;
            float r = 0.0;
            vec2 cxy = 2.0 * gl_PointCoord - 1.0;
            r = dot(cxy, cxy);
            if(r > radius)
            {
                discard;
            }
            // fragColor = blender_srgb_to_framebuffer_space(color);
            fragColor = blender_srgb_to_framebuffer_space_always(color);
            // fragColor = color;
        }
        '''
        # shader = GPUShader(vert, frag, )
        
        # NOTE: "new style" shader ------------------------------------------- >>>
        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.vertex_in(0, 'VEC3', "pos")
        shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
        shader_info.push_constant("FLOAT", "size")
        shader_info.push_constant("VEC4", "color")
        shader_info.fragment_out(0, 'VEC4', "fragColor")
        shader_info.vertex_source(vert)
        shader_info.fragment_source(frag)
        shader = gpu.shader.create_from_info(shader_info)
        # NOTE: "new style" shader ------------------------------------------- <<<
        
        batch = batch_for_shader(shader, 'POINTS', {"pos": vertices, }, )
        
        gpu.state.program_point_size_set(True)
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("size", size, )
            shader.uniform_float("color", color, )
            
            batch.draw(shader)
        
        gpu.state.program_point_size_set(False)
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def round_points_px_colors_3d(cls, vertices, colors, matrix, size=6, color=(1.0, 0.0, 0.0, 0.5, ), ):
        # NOTE: currently not used, new style shader setup is not tested if correct
        
        vertices = np.array(vertices, dtype=np.float32, )
        colors = np.array(colors, dtype=np.float32, )
        
        vert = '''
        // in vec3 pos;
        // in vec4 color;
        // uniform mat4 ModelViewProjectionMatrix;
        // uniform float size;
        // out vec4 v_color;
        void main()
        {
            gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
            gl_PointSize = size;
            v_color = color;
        }
        '''
        frag = '''
        // in vec4 v_color;
        // out vec4 fragColor;
        void main()
        {
            float radius = 1.0;
            float r = 0.0;
            vec2 cxy = 2.0 * gl_PointCoord - 1.0;
            r = dot(cxy, cxy);
            if(r > radius)
            {
                discard;
            }
            fragColor = blender_srgb_to_framebuffer_space(v_color);
        }
        '''
        # shader = GPUShader(vert, frag, )
        
        # NOTE: "new style" shader ------------------------------------------- >>>
        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.vertex_in(0, 'VEC3', "pos")
        shader_info.vertex_in(1, 'VEC4', "color")
        shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
        shader_info.push_constant("FLOAT", "size")
        vert_out = gpu.types.GPUStageInterfaceInfo("vertex_interface")
        vert_out.flat('VEC4', "v_color")
        shader_info.vertex_out(vert_out)
        shader_info.fragment_out(0, 'VEC4', "fragColor")
        shader_info.vertex_source(vert)
        # NOTE: does not automatically add `blender_srgb_to_framebuffer_space`.. lets provide our own (taken from blender source)
        colorspace = (
        "#undef blender_srgb_to_framebuffer_space\n"
        "vec4 blender_srgb_to_framebuffer_space(vec4 in_color)\n"
        "{\n"
        "    vec3 c = max(in_color.rgb, vec3(0.0));\n"
        "    vec3 c1 = c * (1.0 / 12.92);\n"
        "    vec3 c2 = pow((c + 0.055) * (1.0 / 1.055), vec3(2.4));\n"
        "    in_color.rgb = mix(c1, c2, step(vec3(0.04045), c));\n"
        "    return in_color;\n"
        "}\n"
        )
        shader_info.fragment_source(colorspace + frag)
        shader = gpu.shader.create_from_info(shader_info)
        # NOTE: "new style" shader ------------------------------------------- <<<
        
        batch = batch_for_shader(shader, 'POINTS', {"pos": vertices, "color": colors, }, )
        
        gpu.state.program_point_size_set(True)
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(matrix)
            
            shader.bind()
            shader.uniform_float("size", size, )
            
            batch.draw(shader)
        
        gpu.state.program_point_size_set(False)
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def vertices_selection_circles_2d(cls, vertices, c_radius, c_steps, c_color, c_thickness, d_diameter, d_color, ):
        dash = 2
        c_steps = c_steps * dash
        
        vs = np.zeros((c_steps, 3), dtype=np.float32, )
        angstep = 2 * np.pi / c_steps
        a = np.arange(c_steps, dtype=np.int32, )
        vs[:, 0] = 0.0 + (np.sin(a * angstep) * c_radius)
        vs[:, 1] = 0.0 + (np.cos(a * angstep) * c_radius)
        i = np.arange(c_steps)
        indices = np.c_[i[::2], i[1::2], ]
        indices = indices.astype(np.int32)
        
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": vs, }, indices=indices, )
        
        # gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')
        
        shader.bind()
        shader.uniform_float("color", c_color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", c_thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        
        for v in vertices:
            with gpu.matrix.push_pop():
                gpu.matrix.translate(v)
                batch.draw(shader)
        
        # gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    # ------------------------------------------------------------------ elements <<<
    # ------------------------------------------------------------------ draw >>>
    
    @classmethod
    def _draw_2d(cls, self, context, ):
        if(not cls._initialized):
            return
        
        # DEBUG --------------------------------------------------------------------------------------
        # if(debug_mode() and cls.DEBUG_MODE):
        if((bpy.app.debug_value != 0) and cls.DEBUG_MODE):
            tab = "    "
            ls = []
            for tool_id, tool_props in cls._cache.items():
                ls.append("'{}': {} item(s)".format(tool_id, len(tool_props)))
                for comp_k, comp_ls in tool_props.items():
                    ls.append("{}'{}': {} item(s)".format(tab * 1, comp_k, len(comp_ls)))
                    for i, d in enumerate(comp_ls):
                        ls.append("{}'{}': {}".format(tab * 2, 'function', d['function']))
                        ls.append("{}'{}':".format(tab * 3, 'arguments', ))
                        for k, v in d['arguments'].items():
                            if(type(v) == Matrix):
                                # ls.append("{}'{}':".format(tab * 4, k, ))
                                # rs = v.row[:]
                                # l = len(rs)
                                # f = ["{:.6f}", ] * l
                                # f = ', '.join(f)
                                # for i in range(l):
                                #     if(i == 0):
                                #         t = "{}[{},".format(tab * 5, f.format(*rs[i].to_tuple()))
                                #     elif(i == l - 1):
                                #         t = "{} {}]".format(tab * 5, f.format(*rs[i].to_tuple()))
                                #     else:
                                #         t = "{} {},".format(tab * 5, f.format(*rs[i].to_tuple()))
                                #     ls.append(t)
                                r = len(v.row[:])
                                c = len(v.col[:])
                                l = r * c
                                f = ["{:.6f}", ] * l
                                f = ', '.join(f)
                                a = []
                                for i in v.row:
                                    a.extend(list(i.to_tuple()))
                                t = f.format(*a)
                                t = "Matrix {}x{}: [{}]".format(r, c, t)
                                ls.append("{}'{}': {}".format(tab * 4, k, t, ))
                            elif(type(v) == Vector):
                                ls.append("{}'{}': {}".format(tab * 4, k, v, ))
                            elif(type(v) == list):
                                ls.append("{}'{}': {}".format(tab * 4, k, v, ))
                            elif(str(type(v)) == "<class 'bpy_prop_array'>"):
                                ls.append("{}'{}': {}".format(tab * 4, k, v[:], ))
                            else:
                                ls.append("{}'{}': {}".format(tab * 4, k, v, ))
            
            x, y, w, h = gpu.state.viewport_get()
            cls.label_multiline_left_flag_2d((x + 10, y + h - 200, ), lines=ls, offset=(0, 0), size=10, color=(1.0, 1.0, 1.0, 0.5, ), shadow=True, padding=5, )
        # DEBUG --------------------------------------------------------------------------------------
        
        if(self._invoke_area != context.area):
            return
        
        for k, v in cls._cache.items():
            for c in v['screen_components']:
                if(not c['function'].endswith('_2d')):
                    continue
                
                fn = getattr(cls, c['function'])
                fn(**c['arguments'])
            
            for c in v['cursor_components']:
                if(not c['function'].endswith('_2d')):
                    continue
                
                fn = getattr(cls, c['function'])
                fn(**c['arguments'])
            
            # then draw any other custom components
            for k in v.keys():
                if(k not in {'screen_components', 'cursor_components', }):
                    for c in v[k]:
                        if(not c['function'].endswith('_2d')):
                            continue
                        fn = getattr(cls, c['function'])
                        fn(**c['arguments'])
    
    @classmethod
    def _draw_3d(cls, self, context, ):
        if(not cls._initialized):
            return
        
        if(self._invoke_area != context.area):
            return
        
        for k, v in cls._cache.items():
            for c in v['screen_components']:
                if(not c['function'].endswith('_3d')):
                    continue
                
                fn = getattr(cls, c['function'])
                fn(**c['arguments'])
            
            for c in v['cursor_components']:
                if(not c['function'].endswith('_3d')):
                    continue
                
                fn = getattr(cls, c['function'])
                fn(**c['arguments'])
            
            # then draw any other custom components
            for k in v.keys():
                if(k not in {'screen_components', 'cursor_components', }):
                    for c in v[k]:
                        if(not c['function'].endswith('_3d')):
                            continue
                        fn = getattr(cls, c['function'])
                        fn(**c['arguments'])
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()
    
    # ------------------------------------------------------------------ draw >>>


classes = ()
