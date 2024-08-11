'''
Copyright (C) 2016 Andreas Esau
andreasesau@gmail.com

Created by Andreas Esau

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
    
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
import math
import bgl
import blf
import bpy_extras
from . functions import *
from . operators.sketch_operator import get_zoom
import gpu
from gpu_extras.batch import batch_for_shader

def restore_opengl_defaults():
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    # bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

def get_grid_mat(self,context):
    wm = context.window_manager
    asset_sketcher = wm.asset_sketcher
    mat_rot = Matrix.Rotation(math.radians(90.0),4,'X')
    mat_trans = Matrix.Translation(self.projected_mouse)
    mat = mat_trans @ mat_rot
    
    if asset_sketcher.sketch_plane_axis == "XY":
        mat_rot = Matrix.Rotation(math.radians(0),4,'X')
        mat_trans = Matrix.Translation(self.projected_mouse)
        mat = mat_trans @ mat_rot
    if asset_sketcher.sketch_plane_axis == "YZ":
        mat_rot = Matrix.Rotation(math.radians(90.0),4,'Y')
        mat_trans = Matrix.Translation(self.projected_mouse)
        mat = mat_trans @ mat_rot
    elif asset_sketcher.sketch_plane_axis == "XZ":
        mat_rot = Matrix.Rotation(math.radians(90.0),4,'X')
        mat_trans = Matrix.Translation(self.projected_mouse)
        mat = mat_trans @ mat_rot
    return mat

def draw_coords(coords=[], color=(1.0,1.0,1.0,1.0), draw_type="LINE_STRIP", shader_type="2D_UNIFORM_COLOR", line_width=2): # draw_types -> LINE_STRIP, LINES, POINTS
    bgl.glLineWidth(line_width)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)

    shader = gpu.shader.from_builtin(shader_type)
    batch = batch_for_shader(shader, draw_type, {"pos": coords})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

    bgl.glDisable(bgl.GL_BLEND)
    bgl.glDisable(bgl.GL_LINE_SMOOTH)
    return shader

def draw_brush_cursor(self,context,event):
    wm = context.window_manager
    asset_sketcher = wm.asset_sketcher
    region = bpy.context.region
    rv3d = bpy.context.space_data.region_3d

    self.circle_color = [0.102758, 0.643065, 1.000000, 1.000000]
    if event.ctrl and not self.f_key and event.type != "MIDDLEMOUSE":
        self.circle_color = [1.000000, 0.202489, 0.401234, 1.000000]
    elif self.f_key:
        self.circle_color = [1.0, 1.0, 1.0, .7]

    ### draw brush
    if wm.asset_sketcher.sketch_mode in ["SCALE", "PAINT", "LINE"]:
        ### draw line for LINE mode
        if wm.asset_sketcher.sketch_mode == "LINE" and self.brush_stroke and not event.ctrl and not event.shift and not self.f_key:
            if wm.asset_sketcher.sketch_mode == "PAINT" or (wm.asset_sketcher.sketch_mode == "LINE" and self.asset_item.asset_distance_mode == "DISTANCE"):
                segments = int((self.stroke_length / self.stroke_distance))
                stroke_distance = self.stroke_distance
            elif wm.asset_sketcher.sketch_mode == "LINE" and self.asset_item.asset_distance_mode == "FIXED":
                segments = self.asset_item.asset_count - 1
                stroke_distance = self.stroke_length / segments
            self.stroke_end_pos = self.stroke_start_pos + self.stroke_direction * stroke_distance * (segments)
            stroke_start_pos_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, self.stroke_start_pos)
            mouse_project_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, self.stroke_end_pos)
            coords = []
            coords.append(stroke_start_pos_2d)
            coords.append(mouse_project_2d)
            draw_coords(coords=coords, color=self.circle_color, draw_type="LINES")

            mouse_project_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, self.projected_mouse)
            coords = []
            stroke_start_pos_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, self.stroke_end_pos)
            coords.append(stroke_start_pos_2d)
            coords.append(mouse_project_2d)
            draw_coords(coords=coords,color=self.circle_color)

            coords = []
            for i in range(segments+1):
                p = self.stroke_start_pos + self.stroke_direction * stroke_distance * i
                p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
                coords.append((p_2d))
            draw_coords(coords=coords, color=self.circle_color, draw_type="POINTS")

        ### draw brush circle
        steps = 32
        angle = (2*math.pi)/steps

        if self.brush_stroke:
            radius = (wm.asset_sketcher.brush_size/2) * self.pen_pressure
        else:
            radius = (wm.asset_sketcher.brush_size/2)

        ### calc smooth visual normal interpolation

        rot_mat = self.ground_normal_current.rotation_difference(Vector((0, 0, 1))).to_matrix().to_3x3()

        coords = []
        for i in range(steps+1):
            x = self.projected_mouse[0] + radius*math.cos(angle*i)
            y = self.projected_mouse[1] + radius*math.sin(angle*i)
            z = self.projected_mouse[2]

            p = Vector((x, y, z))

            ### rotate circle to match the ground normal
            p -= self.projected_mouse
            p = p @  rot_mat
            p += self.projected_mouse

            ### convert 3d vectors to 2d screen
            p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
            if p_2d != None:
                coords.append(p_2d)

        draw_coords(coords=coords, color=self.circle_color)

        ### draw normal direction line
        p1 = self.projected_mouse
        p2 = self.projected_mouse + (self.ground_normal_current * get_zoom(self,context)*.05)
        p1_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p1)
        p2_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p2)
        coords = [p1_2d, p2_2d]
        draw_coords(coords=coords, color=self.circle_color)

        ### draw normal arrow
        # a = [Vector((1,0,0)), Vector((1,1,0)), Vector((0,1,0)),Vector((0,0,0)), Vector((.5,.5,1))]
        a = []
        steps = 12
        for i in range(steps):
            angle = 2*math.pi / steps
            a.append(Vector((.5 +  math.cos(i*angle) ,.5 +  math.sin(i*angle), 0)))
            a.append(Vector((.5 +  math.cos((i+1)*angle) ,.5 +  math.sin((i+1)*angle), 0)))
            a.append(Vector((.5, .5, 2.5)))
        a_2d = []

        normal_rotation = (self.ground_normal_current.reflect(Vector((0,1,0))).reflect(Vector((1,0,0)))).rotation_difference(Vector((0,0,1)))
        for point in a:
            rotated_point =  p2 + (normal_rotation @ (point - Vector((.5,.5,0))) * get_zoom(self,context)*.005)
            a_2d.append(bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, rotated_point ))

        draw_coords(coords=a_2d, color=self.circle_color, draw_type="TRIS", shader_type="2D_UNIFORM_COLOR")

        coords = [p1_2d]
        draw_coords(coords=coords, color=self.circle_color, draw_type="POINTS", shader_type="2D_UNIFORM_COLOR",line_width=5)


    elif wm.asset_sketcher.sketch_mode == "GRID":


        mat = get_grid_mat(self,context)

        ### draw tile square
        coords = []
        p = self.projected_mouse + (Vector((asset_sketcher.sketch_grid_size/2,asset_sketcher.sketch_grid_size/2,0)) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        if p_2d != None:
            coords.append(p_2d)

        p = self.projected_mouse + (Vector((asset_sketcher.sketch_grid_size/2,-asset_sketcher.sketch_grid_size/2,0)) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        if p_2d != None:
            coords.append(p_2d)

        p = self.projected_mouse + (Vector((-asset_sketcher.sketch_grid_size/2,-asset_sketcher.sketch_grid_size/2,0)) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        if p_2d != None:
            coords.append(p_2d)

        p = self.projected_mouse + (Vector((-asset_sketcher.sketch_grid_size/2,asset_sketcher.sketch_grid_size/2,0)) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        if p_2d != None:
            coords.append(p_2d)

        p = self.projected_mouse + (Vector((asset_sketcher.sketch_grid_size/2,asset_sketcher.sketch_grid_size/2,0)) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        if p_2d != None:
            coords.append(p_2d)

        draw_coords(coords=coords, color=self.circle_color)

def draw_scale_line(self,context,event):
    wm = context.window_manager
    region = bpy.context.region
    rv3d = bpy.context.space_data.region_3d
    #
    #
    self.circle_color = [0.102758, 0.643065, 1.000000, 1.000000]
    if event.ctrl and not self.f_key and event.type != "MIDDLEMOUSE" and not self.scale_stroke:
        self.circle_color = [1.000000, 0.202489, 0.401234, 1.000000]
    #
    # ### draw line code here
    p1 = self.stroke_start_pos
    p2 = self.stroke_start_pos + (self.stroke_direction*(self.stroke_start_pos - self.mouse_on_plane).length)
    p1_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p1)
    p2_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p2)
    if self.scale_stroke:
        coords = [p1_2d, p2_2d]
        draw_coords(coords=coords, color=self.circle_color,draw_type="LINE_STRIP", shader_type="2D_UNIFORM_COLOR",line_width=3)

    p = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, self.projected_mouse)
    if self.scale_stroke:
        bgl.glPointSize(14)
        p = p2_2d

    coords = [p]
    if p != None:
        draw_coords(coords=coords, color=self.circle_color, draw_type="POINTS", shader_type="2D_UNIFORM_COLOR", line_width=14)
    
def draw_text(self,context,event):  
    wm = context.window_manager
    region = bpy.context.region
    rv3d = bpy.context.space_data.region_3d


    self.circle_color = [0.102758, 0.643065, 1.000000, 1.000000]
    if event.ctrl and not self.f_key:
        self.circle_color = [1.000000, 0.202489, 0.401234, 1.000000]
    elif self.f_key:
        self.circle_color = [1.0, 1.0, 1.0, .7]

    ### draw brush size text

    if self.f_key or event.alt or self.f_key_shift or self.scale_stroke:
        # bgl.glColor4f(1.0, 1.0, 1.0, .7)
        text_pos = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, self.projected_mouse)
        if text_pos != None:
            blf.position(0, text_pos[0]-30, text_pos[1]+10, 0)
        blf.size(0, 18, 72)


    if self.f_key:

        blf.draw(0, "Size: " + str(round(wm.asset_sketcher.brush_size,2)))
    elif self.f_key_shift:
        blf.draw(0, "Density: " + str(wm.asset_sketcher.brush_density))
    elif event.alt:
        blf.draw(0, str(self.picked_asset_name))
    if self.scale_stroke:
        vec = Vector((0,1,0))# * self.ground_normal_mat
        angle = vec.rotation_difference(self.stroke_direction.normalized()).to_euler()

        #angle = self.stroke_direction.normalized().rotation_difference(Vector((0,1,0))).to_euler()


        text1 = "Scale: " + str(round(self.stroke_length,2))
        text2 = "Angle: " + str(round(math.degrees(angle[2]),2))
        blf.draw(0, text1)
        #blf.position(0, text_pos[0]-30, text_pos[1]+10+20, 0)
        #blf.draw(0, text2)

    restore_opengl_defaults()


def draw_grid(self,context,event):
    wm = context.window_manager
    asset_sketcher = wm.asset_sketcher
    region = bpy.context.region
    rv3d = bpy.context.space_data.region_3d

    self.circle_color = [0.102758, 0.643065, 1.000000, 1.000000]
    if event.ctrl and event.type != "MIDDLEMOUSE":
        self.circle_color = [1.000000, 0.202489, 0.401234, 1.000000]

    ### Plane XY
    mat = get_grid_mat(self,context)

    ### draw tile grid
    grid_size = 18
    for i in range(grid_size):

        self.circle_color = [0.102758, 0.643065, 1.000000, .4]

        coords = []
        offset = Vector(((grid_size/2)-.5,(grid_size/2)-.5,0))*asset_sketcher.sketch_grid_size

        p = self.projected_mouse + ((Vector((0,i*asset_sketcher.sketch_grid_size,0)) -offset) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        coords.append(p)

        p = self.projected_mouse + ((Vector(((grid_size-1)*asset_sketcher.sketch_grid_size,i*asset_sketcher.sketch_grid_size,0)) -offset) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        coords.append(p)

        p = self.projected_mouse + ((Vector((i*asset_sketcher.sketch_grid_size,0,0)) -offset) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        coords.append(p)

        p = self.projected_mouse + ((Vector((i*asset_sketcher.sketch_grid_size,(grid_size-1)*asset_sketcher.sketch_grid_size,0))-offset) @ mat)
        p_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        coords.append(p)
        draw_coords(coords=coords, color=self.circle_color, draw_type="LINES", shader_type="3D_UNIFORM_COLOR",line_width=1)