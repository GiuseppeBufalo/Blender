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

import os
import numpy as np

import bpy
import gpu
from gpu.types import GPUShader
from gpu_extras.batch import batch_for_shader

from .shaders import load_shader_code
from .theme import ToolTheme

# DONE: grid is 3x3 pixels, looks not that good on hidpi displays. scale it somehow with `ui_scale`, but beware, shader is not ready for this.. --->> scalable checkerboard grid is used instead


class GridOverlay():
    _shader = None
    _batch = None
    _handlers = []
    _initialized = False
    _theme = None
    
    @classmethod
    def init(cls, self, context, ):
        if(cls._initialized):
            return
        
        prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences
        if(not prefs.manual_use_overlay):
            return
        
        cls._theme = ToolTheme()
        
        v, f, _ = load_shader_code('CHECKERBOARD')
        cls._shader = gpu.types.GPUShader(v, f, )
        cls._batch = batch_for_shader(cls._shader, 'TRIS', {'position': [(-1, -1), (3, -1), (-1, 3), ], })
        
        cls._handlers = []
        cls._initialized = True
        
        for a in context.screen.areas:
            s = a.spaces[0]
            for r in a.regions:
                try:
                    h = s.draw_handler_add(cls._draw, (self, a, r, ), r.type, 'POST_PIXEL', )
                    cls._handlers.append((s, r.type, h, ))
                except TypeError as e:
                    # NOTE: 3.0 bug: TypeError: unknown space type 'SpaceSpreadsheet'
                    # NOTE: https://developer.blender.org/T94685
                    pass
        
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        for s, r, h in cls._handlers:
            s.draw_handler_remove(h, r, )
        cls._handlers = []
        
        cls._shader = None
        cls._batch = None
        
        cls._theme = None
        
        cls._initialized = False
        cls._tag_redraw()
    
    @classmethod
    def _draw(cls, self, area, region, ):
        # print("*")
        
        if(not cls._initialized):
            return
        
        for a, rt in self._grid_exclude:
            if(area.type == a.type):
                if(rt is None):
                    return
                if(region.type == rt):
                    r = None
                    for r in a.regions:
                        if(r.type == rt):
                            break
                    if(r):
                        x, y, w, h = gpu.state.viewport_get()
                        # WATCH: this is the only way i found to correctly identify area and region being drawn. so when two areas of same type and same dimensions are there, it won't work as expected..
                        if(r.width == w and r.height == h):
                            return
        
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('ALPHA')
        
        cls._shader.bind()
        
        cls._shader.uniform_float('color_a', cls._theme._grid_overlay_color_a, )
        cls._shader.uniform_float('color_b', cls._theme._grid_overlay_color_b, )
        
        cls._shader.uniform_int('size', int(round(cls._theme._grid_overlay_size * cls._theme._ui_scale)), )
        
        cls._batch.draw(cls._shader, )
        # NOTE: do i need that?
        gpu.shader.unbind()
        
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()


"""
class SC5GridOverlay():
    # _darken = 0.25
    _shader = None
    _batch = None
    _handlers = []
    _initialized = False
    _theme = None
    
    @classmethod
    def init(cls, self, context, exclude_areas=['VIEW_3D', ], exclude_regions=['WINDOW', ], invoke_area_only=False, ):
        if(cls._initialized):
            return
        
        cls._theme = ToolTheme()
        
        cls._exclude_areas = exclude_areas
        cls._exclude_regions = exclude_regions
        cls._invoke_area_only = invoke_area_only
        
        # v, f, _ = load_shader_code('GRID_OVERLAY')
        v, f, _ = load_shader_code('CHECKERBOARD')
        cls._shader = gpu.types.GPUShader(v, f, )
        cls._batch = batch_for_shader(cls._shader, 'TRIS', {'position': [(-1, -1), (3, -1), (-1, 3), ], })
        
        cls._handlers = []
        cls._initialized = True
        
        for a in context.screen.areas:
            s = a.spaces[0]
            for r in a.regions:
                try:
                    h = s.draw_handler_add(cls._draw, (self, context, a.type, r.type, ), r.type, 'POST_PIXEL', )
                    cls._handlers.append((s, r.type, h, ))
                except TypeError as e:
                    # NOTE: 3.0 bug: TypeError: unknown space type 'SpaceSpreadsheet'
                    # NOTE: https://developer.blender.org/T94685
                    pass
        
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        for s, r, h in cls._handlers:
            s.draw_handler_remove(h, r, )
        cls._handlers = []
        
        cls._shader = None
        cls._batch = None
        
        cls._theme = None
        
        cls._initialized = False
        cls._tag_redraw()
    
    @classmethod
    def _draw(cls, self, context, area_type, region_type, ):
        if(not cls._initialized):
            return
        
        if(area_type in cls._exclude_areas):
            if(cls._invoke_area_only):
                if(self._invoke_area == context.area):
                    if(len(cls._exclude_regions)):
                        if(region_type in cls._exclude_regions):
                            return
            else:
                if(len(cls._exclude_regions)):
                    if(region_type in cls._exclude_regions):
                        return
                else:
                    return
        
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('ALPHA')
        
        cls._shader.bind()
        # cls._shader.uniform_float('darken', cls._darken, )
        
        cls._shader.uniform_float('color_a', cls._theme._grid_overlay_color_a, )
        cls._shader.uniform_float('color_b', cls._theme._grid_overlay_color_b, )
        
        cls._shader.uniform_int('size', int(round(cls._theme._grid_overlay_size * cls._theme._ui_scale)), )
        
        cls._batch.draw(cls._shader, )
        # NOTE: do i need that?
        gpu.shader.unbind()
        
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
"""

"""
class SCATTER5_OT_grid_overlay_test_operator(bpy.types.Operator, ):
    bl_idname = "scatter5.grid_overlay_test_operator"
    bl_label = "Grid Overlay Test Operator"
    
    def __init__(self):
        print("start..")
    
    def __del__(self):
        print("end.")
    
    def modal(self, context, event):
        if(event.type in {'ESC', }):
            print("exiting..")
            
            SC5GridOverlay.deinit()
            
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        print("invoke..")
        
        # NOTE: executing operator have to define this if `invoke_area_only` is going to be used
        self._invoke_area = context.area
        
        # NOTE: some examples..
        '''
        # leave open 3d views only (default for manual mode)
        SC5GridOverlay.init(self, context, )
        
        # leave open full 3d views, all sidebars, headers..
        SC5GridOverlay.init(self, context, exclude_regions=[], )
        
        # leave open full 3d views, spreadsheets and consoles, all sidebars, headers..
        SC5GridOverlay.init(self, context, exclude_areas=['VIEW_3D', 'SPREADSHEET', 'CONSOLE', ], exclude_regions=[], )
        
        # leave open only invoke 3d view, if invoked in different area type, nothing is open
        SC5GridOverlay.init(self, context, exclude_areas=['VIEW_3D', ], exclude_regions=['WINDOW', ], invoke_area_only=True, )
        '''
        
        # executed from different area, but should run in 3d view, first found will be used
        if(context.area.type != 'VIEW_3D'):
            found = False
            for a in context.screen.areas:
                if(a.type == 'VIEW_3D'):
                    found = True
                    break
            if(not found):
                self.report({'ERROR'}, 'no 3d view found..')
                return {'CANCELLED'}
            self._invoke_area = a
        SC5GridOverlay.init(self, context, exclude_areas=['VIEW_3D', ], exclude_regions=['WINDOW', ], invoke_area_only=True, )
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
"""


classes = ()

'''
if(bpy.app.debug_value != 0):
    classes += (SCATTER5_OT_grid_overlay_test_operator, )
'''
