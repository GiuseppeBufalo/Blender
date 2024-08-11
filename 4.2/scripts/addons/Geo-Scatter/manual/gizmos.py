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

import numpy as np

import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
from bpy.types import Gizmo, GizmoGroup
from bpy_extras import view3d_utils

from . import debug
from .debug import log, debug_mode, verbose

from ..resources.translate import translate


class SC5GizmoManager():
    restore = {}
    
    index = -1
    group = None
    
    surface = None
    target = None
    
    rotation_offsets = [0.0, 0.0, 0.0]
    rotation_uni_offset = 0.0
    
    @classmethod
    def clear(cls, ):
        cls.restore = {}
        cls.index = -1
        cls.group = None
        cls.surface = None
        cls.target = None
        cls.rotation_offsets = [0.0, 0.0, 0.0]
        cls.rotation_uni_offset = 0.0


class SC5ScaleUniformCustomWidget(Gizmo):
    bl_idname = "VIEW3D_GT_sc5_scale_uniform_custom_widget"
    bl_target_properties = (
        {"id": "offset", "type": 'FLOAT', "array_length": 3, },
    )
    __slots__ = (
        "custom_shape",
        "init_mouse_y",
        "init_value",
    )
    
    UNIT_CUBE_TRIANGLES = [
        (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5),
        (-0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
        (0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5),
        (0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
        (0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5),
        (-0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5),
        (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5),
        (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5),
        (0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5),
        (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5),
        (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5),
        (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5),
    ]
    
    def _update_offset_matrix(self):
        pass
    
    def draw(self, context):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape)
    
    def draw_select(self, context, select_id):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape, select_id=select_id)
    
    def setup(self):
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('TRIS', self.UNIT_CUBE_TRIANGLES)
    
    def invoke(self, context, event):
        self.init_mouse_y = event.mouse_y
        self.init_value = self.target_get_value("offset")
        return {'RUNNING_MODAL'}
    
    def exit(self, context, cancel):
        if(cancel):
            self.target_set_value("offset", self.init_value)
    
    def modal(self, context, event, tweak):
        delta = (event.mouse_y - self.init_mouse_y) / 10.0
        if('SNAP' in tweak):
            delta = round(delta)
        if('PRECISE' in tweak):
            delta /= 10.0
        v = Vector(self.init_value)
        value = v - (v.normalized() * delta)
        self.target_set_value("offset", value)
        return {'RUNNING_MODAL'}


class SC5ManipulatorWidgetGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_sc5_manipulator"
    bl_label = "Maipulator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}
    
    @classmethod
    def poll(cls, context):
        # target = bpy.data.objects.get(bpy.context.scene.my_properties.target)
        # if(len(target.data.vertices) == 0):
        #     return False
        # return True
        
        # if(not Manager.active):
        #     return False
        
        # print("!!!!!!!!!!!!")
        
        if(SC5GizmoManager.index != -1 and SC5GizmoManager.surface is not None):
            return True
        return False
        
        # props = context.scene.my_properties
        # o = bpy.data.objects.get(props.surface)
        # if(o):
        #     return True
        # return False
    
    def __init__(self, ):
        SC5GizmoManager.group = self
    
    def __del__(self, ):
        # SC5GizmoManager.group = None
        pass
    
    def _target(self, ):
        # surface = bpy.context.scene.scatter5.emitter
        # target = surface.scatter5.get_psy_active().scatter_obj
        # return target
        return bpy.data.objects.get(SC5GizmoManager.target)
    
    def _surface(self, ):
        # surface = bpy.context.scene.scatter5.emitter
        # return surface
        return bpy.data.objects.get(SC5GizmoManager.surface)
    
    def _props(self, ):
        return bpy.context.scene.scatter5.manual.tool_manipulator
    
    def draw_prepare(self, context, ):
        # print("draw_prepare")
        self._refresh_translation(context)
        self._refresh_rotation(context)
        self._refresh_scale(context)
        
        # print(SC5GizmoManager.index)
        
        wm = self._surface().matrix_world
        
        rv3d = context.space_data.region_3d
        self.tu.matrix_basis = rv3d.view_matrix.to_3x3().inverted().to_4x4()
        
        target = self._target()
        ml = Matrix.Translation(wm @ target.data.vertices[SC5GizmoManager.index].co).to_4x4()
        self.ru.matrix_basis = ml @ rv3d.view_matrix.to_3x3().inverted().to_4x4()
        
        # self._screen_axis = Vector((0,0,1)) @ rv3d.view_matrix.to_3x3().inverted().to_4x4()
        
        # region = context.region
        # w = region.width
        # h = region.height
        # vs = np.array([
        #     target.data.vertices[Manager.index].co.to_tuple(),
        # ], dtype=np.float32, )
        #
        # # _, q, _ = rv3d.view_matrix.decompose()
        # # # a, _ = q.to_axis_angle()
        # # a = Vector((0,0,1))
        # # a.rotate(q)
        
        region = context.region
        co = view3d_utils.location_3d_to_region_2d(region, rv3d, wm @ target.data.vertices[SC5GizmoManager.index].co, )
        if(co is not None):
            # log("ok")
            # NOTE: if coord is behind the origin of a perspective view, ignore and leave it as it is. gizmo is not visible at this stage anyway
            self._screen_axis = view3d_utils.region_2d_to_vector_3d(region, rv3d, co)
        # else:
        #     log("coord is behind the origin of a perspective view")
        
        # ns = np.array([
        #     # Vector(Vector((0,0,1)) @ rv3d.view_matrix.to_3x3().inverted().to_4x4()).to_tuple(),
        #     # view3d_utils.region_2d_to_vector_3d(region, rv3d, [w / 2, h / 2]).normalized(),
        #     # a.to_tuple(),
        #     # view3d_utils.region_2d_to_vector_3d(region, rv3d, co),
        #     self._screen_axis.to_tuple(),
        # ], dtype=np.float32, )
        # cs = np.array([
        #     (1.0, 1.0, 1.0, 1.0, ),
        # ], dtype=np.float32, )
        # points(target, vs, ns, cs, )
        
        self._switcher(context)
    
    def invoke_prepare(self, context, gizmo, ):
        # when gizmo is about to be used?
        pass
    
    def _switcher(self, context, ):
        t = not self._props().translation
        self.tx.hide = t
        self.ty.hide = t
        self.tz.hide = t
        self.tu.hide = t
        
        r = not self._props().rotation
        self.rx.hide = r
        self.ry.hide = r
        self.rz.hide = r
        self.ru.hide = r
        
        s = not self._props().scale
        self.sx.hide = s
        self.sy.hide = s
        self.sz.hide = s
        self.su.hide = s
    
    def _build_translation(self, a, ):
        g = self.gizmos.new("GIZMO_GT_arrow_3d")
        
        def getf():
            target = self._target()
            # return target.data.vertices[SC5GizmoManager.index].co[a]
            
            co = target.data.vertices[SC5GizmoManager.index].co
            wm = self._surface().matrix_world
            co = wm @ co
            return co[a]
        
        def setf(value):
            target = self._target()
            # target.data.vertices[SC5GizmoManager.index].co[a] = value
            
            co = target.data.vertices[SC5GizmoManager.index].co
            wm = self._surface().matrix_world
            co = wm @ co
            co[a] = value
            co = wm.inverted() @ co
            target.data.vertices[SC5GizmoManager.index].co = co
        
        g.target_set_handler("offset", get=getf, set=setf, )
        
        if(a == 0):
            g.color = 1.0, 0.0, 0.0
        elif(a == 1):
            g.color = 0.0, 1.0, 0.0
        elif(a == 2):
            g.color = 0.0, 0.0, 1.0
        g.alpha = 0.5
        g.color_highlight = g.color
        g.alpha_highlight = 1.0
        g.scale_basis = 1.0
        # g.scale_basis = 0.75
        # g.length = 0.5
        g.length = 1.25
        g.line_width = 3
        
        return g
    
    def _build_rotation(self, a, ):
        g = self.gizmos.new("GIZMO_GT_dial_3d")
        
        def getf():
            target = self._target()
            v = target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector[a]
            SC5GizmoManager.rotation_offsets[a] = v
            return v
        
        def setf(value):
            d = 0.0
            if(value != SC5GizmoManager.rotation_offsets[a]):
                d = SC5GizmoManager.rotation_offsets[a] - value
                SC5GizmoManager.rotation_offsets[a] = value
            
            target = self._target()
            # target.data.attributes['manual_private_r_base'].data[Manager.index].vector[a] = value
            ls = ['X', 'Y', 'Z']
            e = Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector)
            # e.rotate_axis(ls[a], value)
            e.rotate_axis(ls[a], d)
            target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector = [e.x, e.y, e.z]
        
        g.target_set_handler("offset", get=getf, set=setf, )
        
        if(a == 0):
            g.color = 1.0, 0.0, 0.0
        elif(a == 1):
            g.color = 0.0, 1.0, 0.0
        elif(a == 2):
            g.color = 0.0, 0.0, 1.0
        g.alpha = 0.5
        g.color_highlight = g.color
        g.alpha_highlight = 1.0
        g.use_draw_modal = True
        g.scale_basis = 1.0
        g.line_width = 3
        
        g.draw_options = {'CLIP'}
        
        return g
    
    def _build_scale(self, a, ):
        g = self.gizmos.new("GIZMO_GT_arrow_3d")
        
        def getf():
            target = self._target()
            return target.data.attributes['manual_private_s_base'].data[SC5GizmoManager.index].vector[a] / 10
        
        def setf(value):
            target = self._target()
            target.data.attributes['manual_private_s_base'].data[SC5GizmoManager.index].vector[a] = value * 10
        
        g.target_set_handler("offset", get=getf, set=setf, )
        
        if(a == 0):
            g.color = 1.0, 0.0, 0.0
        elif(a == 1):
            g.color = 0.0, 1.0, 0.0
        elif(a == 2):
            g.color = 0.0, 0.0, 1.0
        g.alpha = 0.5
        g.color_highlight = g.color
        g.alpha_highlight = 1.0
        g.draw_style = 'BOX'
        g.scale_basis = 1.0
        # g.scale_basis = 1.25
        # g.scale_basis = 0.75
        # g.length = 0.75
        g.length = 1.5
        g.line_width = 3
        
        return g
    
    def rebuild(self, ):
        # print("rebuild..", id(self))
        self.gizmos.clear()
        self.setup(bpy.context)
    
    def setup(self, context, ):
        # print("setup..")
        
        self.tx = self._build_translation(0)
        self.ty = self._build_translation(1)
        self.tz = self._build_translation(2)
        
        g = self.gizmos.new("GIZMO_GT_move_3d")
        
        def getf():
            target = self._target()
            # return target.data.vertices[SC5GizmoManager.index].co
            co = target.data.vertices[SC5GizmoManager.index].co
            wm = self._surface().matrix_world
            co = wm @ co
            return co
        
        def setf(value):
            target = self._target()
            # target.data.vertices[SC5GizmoManager.index].co = value
            wm = self._surface().matrix_world
            co = wm.inverted() @ Vector(value)
            target.data.vertices[SC5GizmoManager.index].co = co
        
        g.target_set_handler("offset", get=getf, set=setf, )
        g.color = 1.0, 1.0, 1.0
        g.alpha = 0.5
        g.color_highlight = g.color
        g.alpha_highlight = 1.0
        # g.scale_basis = 0.2
        # g.scale_basis = 0.35
        g.scale_basis = 0.25
        g.line_width = 3
        g.use_draw_modal = True
        self.tu = g
        
        self._refresh_translation(context)
        
        # -----------------------------------------
        
        self.rx = self._build_rotation(0)
        self.ry = self._build_rotation(1)
        self.rz = self._build_rotation(2)
        
        g = self.gizmos.new("GIZMO_GT_dial_3d")
        
        def getf():
            target = self._target()
            # return target.data.vertices[Manager.index].co
            # Manager.rotation_uni_offset
            # return 0.0
            return SC5GizmoManager.rotation_uni_offset
        
        def setf(value):
            d = 0.0
            if(value != SC5GizmoManager.rotation_uni_offset):
                d = SC5GizmoManager.rotation_uni_offset - value
                SC5GizmoManager.rotation_uni_offset = value
            
            target = self._target()
            # target.data.vertices[Manager.index].co = value
            axis = self._screen_axis
            # q = Quaternion(axis, d)
            q = Quaternion(axis, -d)
            
            '''
            e = Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector)
            e.rotate(q)
            target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector = [e.x, e.y, e.z]
            '''
            
            # wm = self._surface().matrix_world.inverted()
            wm = self._surface().matrix_world
            _, wr, _ = wm.decompose()
            wr = wr.to_matrix().to_4x4()
            # q.rotate(wr)
            
            # DEBUG
            # debug.points(self._target(), self._surface().matrix_world @ self._target().data.vertices[SC5GizmoManager.index].co, axis, )
            # DEBUG
            
            e = Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector)
            e.rotate(wr)
            e.rotate(q)
            e.rotate(wr.inverted())
            target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector = [e.x, e.y, e.z]
        
        g.target_set_handler("offset", get=getf, set=setf, )
        g.color = 1.0, 1.0, 1.0
        g.alpha = 0.5
        g.color_highlight = g.color
        g.alpha_highlight = 1.0
        g.scale_basis = 1.2
        g.line_width = 3
        g.use_draw_modal = True
        self.ru = g
        
        self._refresh_rotation(context)
        
        # -----------------------------------------
        
        self.sx = self._build_scale(0)
        self.sy = self._build_scale(1)
        self.sz = self._build_scale(2)
        
        u = self.gizmos.new(SC5ScaleUniformCustomWidget.bl_idname)
        
        def getf():
            target = self._target()
            return target.data.attributes['manual_private_s_base'].data[SC5GizmoManager.index].vector
        
        def setf(value):
            target = self._target()
            target.data.attributes['manual_private_s_base'].data[SC5GizmoManager.index].vector = value
        
        u.target_set_handler("offset", get=getf, set=setf, )
        
        u.color = 1.0, 1.0, 1.0
        u.alpha = 0.5
        u.color_highlight = u.color
        u.alpha_highlight = 1.0
        # u.scale_basis = 0.02
        u.scale_basis = 0.15
        u.use_draw_modal = True
        self.su = u
        
        self._refresh_scale(context)
    
    def _refresh_translation(self, context, ):
        # target = self._target(context, )
        target = self._target()
        
        # print("_refresh_translation:", Manager.index)
        # print("!")
        
        ml = Matrix.Translation(target.data.vertices[SC5GizmoManager.index].co).to_4x4()
        # mr = Euler(target.data.attributes['manual_rotation'].data[Manager.index].vector).to_matrix().to_4x4()
        mr = Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
        m = ml @ mr
        space = mr.normalized()
        
        # loc = Vector(target.matrix_world @ space.inverted() @ target.data.vertices[Manager.index].co)
        loc = Vector(target.matrix_world @ target.data.vertices[SC5GizmoManager.index].co)
        
        wm = self._surface().matrix_world
        loc = wm @ loc
        
        # -----------------------------------
        
        v = loc.copy()
        v.x = v.x - self.tx.target_get_value("offset")[0]
        a = Matrix.Rotation(np.radians(90), 3, 'Y')
        m = Matrix.LocRotScale(v, a, None)
        self.tx.matrix_basis = m.normalized()
        # self.x.matrix_space = space
        
        v = loc.copy()
        v.y = v.y - self.ty.target_get_value("offset")[0]
        a = Matrix.Rotation(np.radians(-90), 3, 'X')
        m = Matrix.LocRotScale(v, a, None)
        self.ty.matrix_basis = m.normalized()
        # self.y.matrix_space = space
        
        v = loc.copy()
        v.z = v.z - self.tz.target_get_value("offset")[0]
        a = Matrix.Rotation(np.radians(0.0), 3, 'X')
        m = Matrix.LocRotScale(v, a, None)
        self.tz.matrix_basis = m.normalized()
        # self.z.matrix_space = space
        
        # -----------------------------------
        
        # # self.tu.matrix_basis = Matrix()
        # rv3d = context.space_data.region_3d
        # self.tu.matrix_basis = rv3d.view_matrix.to_3x3().inverted().to_4x4()
    
    def _refresh_rotation(self, context):
        # target = self._target(context, )
        target = self._target()
        
        # print("!")
        
        wm = self._surface().matrix_world
        
        _, wr, _ = wm.decompose()
        wr = wr.to_matrix().to_4x4()
        
        ml = Matrix.Translation(wm @ target.data.vertices[SC5GizmoManager.index].co).to_4x4()
        # mr = Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
        mr = wr @ Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
        
        a = Matrix.Rotation(np.radians(90.0), 3, 'Y').to_4x4()
        # self.x.matrix_basis = a
        self.rx.matrix_basis = ml @ (mr @ a)
        # self.x.matrix_space = mr
        
        a = Matrix.Rotation(np.radians(-90.0), 3, 'X').to_4x4()
        # self.y.matrix_basis = a
        self.ry.matrix_basis = ml @ (mr @ a)
        # self.y.matrix_space = mr
        
        a = Matrix.Rotation(np.radians(0.0), 3, 'X').to_4x4()
        # self.z.matrix_basis = a
        self.rz.matrix_basis = ml @ (mr @ a)
        # self.z.matrix_space = mr
    
    def _refresh_scale(self, context, ):
        '''
        # target = self._target(context, )
        target = self._target()
        
        # print("!")
        
        ml = Matrix.Translation(target.data.vertices[SC5GizmoManager.index].co).to_4x4()
        # mr = Euler(target.data.attributes['manual_rotation'].data[Manager.index].vector).to_matrix().to_4x4()
        mr = Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
        m = ml @ mr
        space = mr.normalized()
        
        loc = Vector(target.matrix_world @ space.inverted() @ target.data.vertices[SC5GizmoManager.index].co)
        
        # -----------------------------------
        
        v = loc.copy()
        v.x = v.x - self.sx.target_get_value("offset")[0]
        mr = Matrix.Rotation(np.radians(90), 3, 'Y')
        m = Matrix.LocRotScale(v, mr, None)
        self.sx.matrix_basis = m.normalized()
        self.sx.matrix_space = space
        
        v = loc.copy()
        v.y = v.y - self.sy.target_get_value("offset")[0]
        mr = Matrix.Rotation(np.radians(-90), 3, 'X')
        m = Matrix.LocRotScale(v, mr, None)
        self.sy.matrix_basis = m.normalized()
        self.sy.matrix_space = space
        
        v = loc.copy()
        v.z = v.z - self.sz.target_get_value("offset")[0]
        mr = Matrix.Rotation(np.radians(0.0), 3, 'X')
        m = Matrix.LocRotScale(v, mr, None)
        self.sz.matrix_basis = m.normalized()
        self.sz.matrix_space = space
        
        v = loc.copy()
        mr = Matrix.Rotation(np.radians(0.0), 3, 'X')
        m = Matrix.LocRotScale(v, mr, None)
        self.su.matrix_basis = m.normalized()
        self.su.matrix_space = space
        '''
        
        # FIXME gizmo should stick to center, too tired to get this matrix madness.. i am sure offset have to be subtracted from location.. somehow..
        target = self._target()
        wm = self._surface().matrix_world
        
        _, wr, _ = wm.decompose()
        wr = wr.to_matrix().to_4x4()
        
        ml = Matrix.Translation(wm @ target.data.vertices[SC5GizmoManager.index].co).to_4x4()
        # mr = Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
        mr = wr @ Euler(target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
        
        xv = self.sx.target_get_value("offset")[0]
        yv = self.sy.target_get_value("offset")[0]
        zv = self.sz.target_get_value("offset")[0]
        
        a = Matrix.Rotation(np.radians(90), 3, 'Y').to_4x4()
        self.sx.matrix_basis = ml @ (mr @ a)
        # self.sx.matrix_offset.col[3][2] = -self.sx.target_get_value("offset")[0]
        a = Matrix.Rotation(np.radians(-90), 3, 'X').to_4x4()
        self.sy.matrix_basis = ml @ (mr @ a)
        # self.sy.matrix_offset.col[3][2] = -self.sy.target_get_value("offset")[0]
        a = Matrix.Rotation(np.radians(0.0), 3, 'X').to_4x4()
        self.sz.matrix_basis = ml @ (mr @ a)
        # self.sz.matrix_offset.col[3][2] = -self.sz.target_get_value("offset")[0]
        
        a = Matrix.Rotation(np.radians(0.0), 3, 'X').to_4x4()
        self.su.matrix_basis = ml @ (mr @ a)
    
    def refresh(self, context, ):
        self._refresh_translation(context)
        self._refresh_rotation(context)
        self._refresh_scale(context)


# @verbose
def init():
    SC5GizmoManager.clear()


# @verbose
def deinit():
    SC5GizmoManager.clear()


classes = (
    SC5ScaleUniformCustomWidget,
    SC5ManipulatorWidgetGroup,
)
