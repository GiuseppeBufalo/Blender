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

import uuid
import numpy as np

import bpy
from bpy.types import Operator
from mathutils import Matrix, Vector, Euler, Quaternion
from mathutils.bvhtree import BVHTree
import bmesh
from bpy.props import EnumProperty, BoolProperty

from . import debug
from .debug import log, debug_mode

from .. resources.translate import translate
from .. ui import ui_templates
from .. utils.str_utils import word_wrap


# TODO: all ops polls should check for all conditions, even though they are not accessible until they are set


class SCATTER5_OT_apply_brush(Operator, ):
    bl_idname = "scatter5.manual_apply_brush"
    bl_label = translate("Apply Brush Settings")
    bl_description = translate("Apply Brush Settings to all points")
    bl_options = {'INTERNAL', }
    
    _allowed = (
        "scatter5.manual_brush_tool_smooth",
        "scatter5.manual_brush_tool_rotation_set",
        "scatter5.manual_brush_tool_scale_set",
        "scatter5.manual_brush_tool_grow_shrink",
        "scatter5.manual_brush_tool_object_set",
        "scatter5.manual_brush_tool_drop_down",
    )
    
    @classmethod
    def poll(cls, context, ):
        try:
            target = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active().scatter_obj
            if(len(target.data.vertices)):
                from .brushes import ToolBox
                tool = ToolBox.reference
                if(tool is not None):
                    if(tool.tool_id in cls._allowed):
                        return True
        except Exception as e:
            pass
        return False
    
    def execute(self, context):
        from .brushes import ToolBox
        tool = ToolBox.reference
        try:
            tool._execute_all()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            return {'CANCELLED'}
        return {'FINISHED'}


class SCATTER5_OT_manual_enter(Operator, ):
    bl_idname = "scatter5.manual_enter"
    bl_label = translate("Enter Manual Mode")
    bl_description = translate("Enter Manual Mode")
    bl_options = set()
        
    #this operator only work for the active psy

    @classmethod
    def poll(cls, context, ):
        if(context.space_data is None):
            # NOTE: this can be None, if blender window is active but mouse is outside of it, like on second monitor ;)
            return False
        if(context.space_data.type != 'VIEW_3D'):
            return False
        
        if(context.mode != 'OBJECT'):
            return False
        
        emitter = bpy.context.scene.scatter5.emitter
        if(emitter is None):
            return False
        psy_active = emitter.scatter5.get_psy_active()
        if(psy_active is None):
            return False
        if(psy_active.s_distribution_method != 'manual_all'):
            return False
        
        surfaces = psy_active.get_surfaces()
        if(not len(surfaces)):
            return False
        for s in surfaces:
            if(s is None):
                return False
        
        return True
    
    def execute(self, context, ):

        emitter = bpy.context.scene.scatter5.emitter
        psy_active = emitter.scatter5.get_psy_active()
        
        # NOTE: stop animation if it is playing
        bpy.ops.screen.animation_cancel(restore_frame=False, )
        
        # NOTE: force refresh uuid surfaces
        from ..scattering.update_factory import update_manual_uuid_surfaces
        update_manual_uuid_surfaces(force_update=True, flush_uuid_cache=psy_active.uuid,)

        # run last or default tool
        last = bpy.context.scene.scatter5.manual.active_tool
        from . import brushes
        ls = brushes.get_all_tool_ids()
        if(last not in ls):
            bpy.context.scene.scatter5.manual.active_tool = "scatter5.manual_brush_tool_spray"
            last = "scatter5.manual_brush_tool_spray"
            log("{}: unknown brush type was set in ~manual.active_brush, resetting to default".format(self.__class__.__name__))
        
        # if last selected tool was index brush and system no longer uses index for instance picking, index brush cannot start, reset it to default
        if(last == "scatter5.manual_brush_tool_object_set"):
            if(psy_active.s_instances_method != "ins_collection" or psy_active.s_instances_pick_method != "pick_idx"):
                last = "scatter5.manual_brush_tool_spray"
                log("{}: unavailable brush type was set in ~manual.active_brush, resetting to default".format(self.__class__.__name__))
        
        c = brushes.get_tool_class(last)
        n = c.bl_idname.split('.', 1)
        o = getattr(getattr(bpy.ops, n[0]), n[1])
        if(o.poll()):
            o('INVOKE_DEFAULT', )
        
        return {'FINISHED'}


class SCATTER5_OT_manual_exit(Operator, ):
    bl_idname = "scatter5.manual_exit"
    bl_label = translate("Exit")
    bl_description = translate("Exit")
    bl_options = {'INTERNAL', }
    
    @classmethod
    def poll(cls, context, ):
        # allow running anytime..
        return True
    
    def execute(self, context):
        from .brushes import ToolBox, panic
        if(ToolBox.reference is not None):
            try:
                # NOTE: integration with custom ui. restore ui
                ToolBox.reference._integration_on_finish(context, None, )
                
                ToolBox.reference._abort(context, None, )
            except Exception as e:
                # NOTE: panic!
                panic(self.__class__.__qualname__)
        else:
            # NOTE: panic!
            panic(self.__class__.__qualname__)
        
        return {'FINISHED'}


class SCATTER5_OT_manual_clear(Operator, ):
    bl_idname = "scatter5.manual_clear"
    bl_label = translate("Clear Points")
    bl_description = translate("Clear all points in system")
    bl_options = {'INTERNAL', 'UNDO'}
    
    @classmethod
    def poll(cls, context, ):
        # NOTE: hmm, available only from mode menu, need something here?
        return True
    
    def execute(self, context, ):
        target = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active().scatter_obj
        l = len(target.data.vertices)
        target.data.clear_geometry()
        self.report({'INFO'}, "Removed {} points.".format(l), )
        return {'FINISHED'}


"""
class SCATTER5_OT_manual_edit(Operator, ):
    bl_idname = "scatter5.manual_edit"
    bl_label = translate("Edit Points")
    bl_description = translate("Edit Points")
    bl_options = {'INTERNAL', 'UNDO', }
    
    @classmethod
    def poll(cls, context, ):
        try:
            target = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active().scatter_obj
            if(len(target.data.vertices)):
                return True
        except Exception as e:
            pass
        return False
    
    def execute(self, context):
        bpy.ops.scatter5.manual_exit()
        bpy.ops.object.select_all(action='DESELECT')
        target = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active().scatter_obj
        target.select_set(True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.view3d.toggle_xray()
        return {'FINISHED'}
"""

"""
def orphans_points_removal(psy):
    '''remove points which surface uuid has been removed from surfaces collections
    used in update_factory.update_manual_uuid_surfaces() on depsgraph updates'''
    
    surfaces = psy.get_surfaces()
    target = psy.scatter_obj
    me = target.data
    
    # is operation necessary? maybe no surfaces? no verts? verts not from manual mode?
    if(not len(surfaces)):
        return None
    if(len(me.vertices) == 0):
        return None
    if("manual_surface_uuid" not in me.attributes):
        return None
    
    # get array of verts uuids
    vs = np.zeros(len(me.vertices), dtype=np.int64,)
    me.attributes["manual_surface_uuid"].data.foreach_get("value", vs, )
    
    # selection of verts to delete
    uuids = np.array([s.scatter5.uuid for s in surfaces])
    todel = np.invert(np.isin(vs, uuids, ))
    
    # nothing to delete?
    if(True not in todel):
        return False
    
    # convert boolean selection to list of verts idx
    me.vertices.foreach_get("index", vs, )
    # https://stackoverflow.com/questions/19984102/select-elements-of-numpy-array-via-boolean-mask-array
    todel = vs[todel]
    
    # bmesh remove
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in todel], context="VERTS", )
    bm.to_mesh(me)
    me.update()
    
    return True
"""


class SCATTER5_OT_manual_clear_orphan_data(Operator, ):
    bl_idname = "scatter5.manual_clear_orphan_data"
    bl_label = translate("Clear Orphan Data")
    bl_description = translate("Clear points not associated to any surfaces")
    bl_options = {'INTERNAL', 'UNDO'}
    
    @classmethod
    def poll(cls, context, ):
        # NOTE: hmm, available only from mode menu, need something here?
        return True
    
    def execute(self, context, ):
        # NOTE: get that from mixin instead defining again on different place
        from .brushes import SCATTER5_OT_common_mixin
        attribute_map = SCATTER5_OT_common_mixin.attribute_map
        attribute_prefix = SCATTER5_OT_common_mixin.attribute_prefix
        
        emitter = context.scene.scatter5.emitter
        psys = emitter.scatter5.get_psy_active()
        target = psys.scatter_obj
        surfaces = psys.get_surfaces()
        surfaces_db = {}
        for s in surfaces:
            surfaces_db[s.scatter5.uuid] = s.name
        
        # NOTE: `_ensure_attributes` functionality
        me = target.data
        for n, t in attribute_map.items():
            nm = '{}{}'.format(attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
        
        # NOTE: `_verify_target_integrity` functionality
        l = len(me.vertices)
        uids = np.zeros(l, dtype=int, )
        me.attributes['{}surface_uuid'.format(attribute_prefix)].data.foreach_get('value', uids, )
        
        uu = np.unique(uids)
        su = set([int(k) for k in surfaces_db.keys()])
        rm = []
        for u in uu:
            if(u not in su):
                rm.append(u)
        ii = np.arange(l, dtype=int, )
        mm = np.zeros(l, dtype=bool, )
        for u in rm:
            m = uids == u
            mm[m] = True
        ii = ii[mm]
        
        if(len(ii)):
            bm = bmesh.new()
            bm.from_mesh(me)
            rm = []
            bm.verts.ensure_lookup_table()
            for i, v in enumerate(bm.verts):
                if(i in ii):
                    rm.append(v)
            for v in rm:
                bm.verts.remove(v)
            bm.to_mesh(me)
            bm.free()
        
        self.report({'INFO'}, "Removed {} points.".format(len(ii)), )
        
        return {'FINISHED'}


class SCATTER5_OT_manual_switch(Operator, ):
    bl_idname = "scatter5.manual_switch"
    bl_label = translate("Switch")
    bl_description = translate("Switch")
    bl_options = {'INTERNAL', }
    
    name: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context, ):
        # allow running anytime..
        return True
    
    def execute(self, context):
        # DONE: after switch, navigation is not working for a first time because previous brush will catch event and cancel itself, interestingly, new brush does not get event at all..
        # DONE: after switch, one instance of stats is drawn extra, those stats are drawn even after manual edit exit
        # TODO: check if this is working with new manipulator out of box or not..
        
        # find desired system index
        e = bpy.context.scene.scatter5.emitter
        assert (self.name in e.scatter5.particle_systems)

        # set psy as active
        e.scatter5.set_interface_active_item(item_type='SCATTER', item_name=self.name)

        # re-run active brush operator
        tool = context.workspace.tools.from_space_view3d_mode(context.mode).idname
        
        from .brushes import get_tool_class
        brush = get_tool_class(tool)
        
        nm = brush.bl_idname.split('.', 1)
        op = getattr(getattr(bpy.ops, nm[0]), nm[1])
        if(op.poll()):

            # if(brush.brush_type == "manipulator"):
            #     # NOTE: extra special care for this one..
            #     from .gizmos import SC5GizmoManager
            #     SC5GizmoManager.index = -1
            #     SC5GizmoManager.group = None
            
            from .brushes import ToolBox, panic
            if(ToolBox.reference is not None):
                try:
                    ToolBox.reference._abort(context, None, )
                except Exception as e:
                    # NOTE: panic!
                    panic(deinit.__qualname__)
            
            # run it again but in different context.. i.e. different target
            op('INVOKE_DEFAULT', )

        else:
            return {'CANCELLED'}

        return {'FINISHED'}


class SCATTER5_OT_manual_scatter_add_new(Operator, ):
    bl_idname = "scatter5.manual_scatter_add_new"
    bl_label = translate("Scatter Selected Asset(s)")
    bl_description = translate("Scatter Selected Asset(s)")
    bl_options = {'INTERNAL', 'UNDO'}
    
    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        scat_op_crea = scat_scene.operators.create_operators
        emitter = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()

        # override these global settings
        old_f_display_allow, old_f_display_bounding_box = scat_op_crea.f_display_allow, scat_op_crea.f_display_bounding_box
        scat_op_crea.f_display_allow = scat_op_crea.f_display_bounding_box = False
        
        # add new system
        bpy.ops.scatter5.add_psy_manual('EXEC_DEFAULT',
            emitter_name=emitter.name,
            surfaces_names="_!#!_".join(s.name for s in psy_active.get_surfaces()),
            psy_color_random=True,
            selection_mode="browser",
            pop_msg=False,
            )

        # switch
        psy_active = emitter.scatter5.get_psy_active()
        bpy.ops.scatter5.manual_switch(name=psy_active.name)
        
        # restore
        scat_op_crea.f_display_allow, scat_op_crea.f_display_bounding_box = old_f_display_allow, old_f_display_bounding_box
        
        return {'FINISHED'}


# DONE: check if it will work with masked attributes -->> well, no error..
class SCATTER5_OT_surfaces_data_to_attributes(Operator, ):
    bl_idname = "scatter5.surfaces_data_to_attributes"
    bl_label = translate("Surfaces Data To Attributes")
    bl_description = translate("Refresh in order to use procedural features relying the vertex-groups/vertex-colors/uv-maps attributes with manual distribution mode")
    bl_options = {'INTERNAL', 'UNDO'}
    
    @classmethod
    def poll(cls, context, ):
        if(context.space_data is None):
            # NOTE: this can be None, if blender window is active but mouse is outside of it, like on second monitor ;)
            return False
        if(context.space_data.type != 'VIEW_3D'):
            return False
        
        if(context.mode != 'OBJECT'):
            return False
        
        emitter = bpy.context.scene.scatter5.emitter
        if(emitter is None):
            return False
        psys = emitter.scatter5.get_psy_active()
        if(psys is None):
            return False
        if(psys.s_distribution_method != 'manual_all'):
            return False
        
        surfaces = psys.get_surfaces()
        if(not len(surfaces)):
            return False
        for s in surfaces:
            if(s is None):
                return False
        
        target = psys.scatter_obj
        if(target is None):
            return False
        
        return True
    
    def transfer(self, surfaces, target, ):
        me = target.data
        l = len(me.vertices)
        vs = np.zeros(l * 3, dtype=np.float64, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        
        from .brushes import SCATTER5_OT_common_mixin
        
        # ensure attributes
        for n, t in SCATTER5_OT_common_mixin.attribute_map.items():
            nm = '{}{}'.format(SCATTER5_OT_common_mixin.attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
        
        uids = np.zeros(l, dtype=int, )
        target.data.attributes['{}surface_uuid'.format(SCATTER5_OT_common_mixin.attribute_prefix)].data.foreach_get('value', uids, )
        
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        
        db = {}
        for s in surfaces:
            if(s.type != 'MESH'):
                # WATCH: ignore anything. but meshes. all objects will get processed, but should be alright, they will not interfere.. i think..
                continue
            
            eo = s.evaluated_get(depsgraph)
            bm = bmesh.new()
            bm.from_object(eo, depsgraph, )
            bmesh.ops.triangulate(bm, faces=bm.faces, )
            bvh = BVHTree.FromBMesh(bm, )
            me = bpy.data.meshes.new('tmp-{}'.format(uuid.uuid1()))
            bm.to_mesh(me)
            bm.free()
            me.update()
            
            vcols = []
            uvs = []
            vgroups = []
            dtype = []
            for ca in me.color_attributes:
                vcols.append(ca.name)
                dtype.append(('vcol_{}_r'.format(ca.name), float))
                dtype.append(('vcol_{}_g'.format(ca.name), float))
                dtype.append(('vcol_{}_b'.format(ca.name), float))
                dtype.append(('vcol_{}_a'.format(ca.name), float))
            for uvl in me.uv_layers:
                uvs.append(uvl.name)
                dtype.append(('uv_{}_x'.format(uvl.name), float))
                dtype.append(('uv_{}_y'.format(uvl.name), float))
            for vg in s.vertex_groups:
                vgroups.append(vg.name)
                dtype.append(('vgroup_{}'.format(vg.name), float))
            
            attributes = np.zeros(l, dtype=dtype, )
            
            mask = uids == s.scatter5.uuid
            db[s.scatter5.uuid] = {
                'o': s,
                'eo': eo,
                'vs': vs[mask],
                'me': me,
                'bvh': bvh,
                'vcols': vcols,
                'uvs': uvs,
                'vgroups': vgroups,
                'attributes': attributes,
            }
        
        def _barycentric_weights(p, a, b, c, ):
            v0 = b - a
            v1 = c - a
            v2 = p - a
            d00 = v0.dot(v0)
            d01 = v0.dot(v1)
            d11 = v1.dot(v1)
            d20 = v2.dot(v0)
            d21 = v2.dot(v1)
            denom = d00 * d11 - d01 * d01
            v = (d11 * d20 - d01 * d21) / denom
            w = (d00 * d21 - d01 * d20) / denom
            u = 1.0 - v - w
            return u, v, w
        
        for uid, item in db.items():
            vs = item['vs']
            me = item['me']
            bvh = item['bvh']
            eo = item['eo']
            attributes = item['attributes']
            vcols = item['vcols']
            uvs = item['uvs']
            vgroups = item['vgroups']
            for i, v in enumerate(vs):
                loc, nor, idx, dst = bvh.find_nearest(v)
                tri = me.polygons[idx]
                ws = _barycentric_weights(loc, *[me.vertices[vi].co.copy() for vi in tri.vertices])
                
                if(vcols):
                    # NOTE: BYTE_COLOR in source color_attributes will be converted to FLOAT_COLOR in target attributes, attributes[n].data[i].color returns float color anyway, so it looks like it is only cosmetic value conversion, internally it is all floats. always..
                    for n in vcols:
                        ca = me.color_attributes[n]
                        if(ca.domain == 'POINT'):
                            vis = tri.vertices
                            c0 = ca.data[vis[0]].color
                            c1 = ca.data[vis[1]].color
                            c2 = ca.data[vis[2]].color
                        else:
                            lis = tri.loop_indices
                            c0 = ca.data[lis[0]].color
                            c1 = ca.data[lis[1]].color
                            c2 = ca.data[lis[2]].color
                        c = [
                            (c0[0] * ws[0]) + (c1[0] * ws[1]) + (c2[0] * ws[2]),
                            (c0[1] * ws[0]) + (c1[1] * ws[1]) + (c2[1] * ws[2]),
                            (c0[2] * ws[0]) + (c1[2] * ws[1]) + (c2[2] * ws[2]),
                            (c0[3] * ws[0]) + (c1[3] * ws[1]) + (c2[3] * ws[2]),
                        ]
                        # so i don't have alpha with floating point errors.. numbers like 0.9999999 and 1.00000001..
                        if(c0[3] == 1.0 and c1[3] == 1.0 and c2[3] == 1.0):
                            c[3] = 1.0
                        
                        attributes['vcol_{}_r'.format(n)][i] = c[0]
                        attributes['vcol_{}_g'.format(n)][i] = c[1]
                        attributes['vcol_{}_b'.format(n)][i] = c[2]
                        attributes['vcol_{}_a'.format(n)][i] = c[3]
                if(uvs):
                    for n in uvs:
                        uvl = me.uv_layers[n]
                        lis = tri.loop_indices
                        v0 = uvl.data[lis[0]].uv
                        v1 = uvl.data[lis[1]].uv
                        v2 = uvl.data[lis[2]].uv
                        uv = [
                            (v0[0] * ws[0]) + (v1[0] * ws[1]) + (v2[0] * ws[2]),
                            (v0[1] * ws[0]) + (v1[1] * ws[1]) + (v2[1] * ws[2]),
                        ]
                        attributes['uv_{}_x'.format(n)][i] = uv[0]
                        attributes['uv_{}_y'.format(n)][i] = uv[1]
                if(vgroups):
                    vi0, vi1, vi2 = tri.vertices
                    
                    v0 = eo.data.vertices[vi0]
                    v1 = eo.data.vertices[vi1]
                    v2 = eo.data.vertices[vi2]
                    
                    for n in vgroups:
                        vg = eo.vertex_groups[n]
                        vgi = vg.index
                        
                        w0 = 0.0
                        w1 = 0.0
                        w2 = 0.0
                        for g in v0.groups:
                            if(g.group == vgi):
                                w0 = g.weight
                                break
                        for g in v1.groups:
                            if(g.group == vgi):
                                w1 = g.weight
                                break
                        for g in v2.groups:
                            if(g.group == vgi):
                                w2 = g.weight
                                break
                        w = (w0 * ws[0]) + (w1 * ws[1]) + (w2 * ws[2])
                        attributes['vgroup_{}'.format(n)][i] = w
        
        attrs = target.data.attributes
        add_vcols = []
        add_uvs = []
        add_vgroups = []
        for uid, item in db.items():
            vcols = item['vcols']
            for n in vcols:
                if(n in attrs.keys()):
                    attrs.remove(attrs[n])
                add_vcols.append(n)
            uvs = item['uvs']
            for n in uvs:
                if(n in attrs.keys()):
                    attrs.remove(attrs[n])
                add_uvs.append(n)
            vgroups = item['vgroups']
            for n in vgroups:
                if(n in attrs.keys()):
                    attrs.remove(attrs[n])
                add_vgroups.append(n)
        
        for n in set(add_vcols):
            attrs.new(n, 'FLOAT_COLOR', 'POINT')
        for n in set(add_uvs):
            attrs.new(n, 'FLOAT2', 'POINT')
        for n in set(add_vgroups):
            attrs.new(n, 'FLOAT', 'POINT')
        
        l = len(target.data.vertices)
        for uid, item in db.items():
            attributes = item['attributes']
            vcols = item['vcols']
            uvs = item['uvs']
            vgroups = item['vgroups']
            
            for n in vcols:
                v = np.c_[
                    attributes['vcol_{}_r'.format(n)],
                    attributes['vcol_{}_g'.format(n)],
                    attributes['vcol_{}_b'.format(n)],
                    attributes['vcol_{}_a'.format(n)],
                ]
                a = np.zeros((l * 4), dtype=np.float64, )
                attrs[n].data.foreach_get('color', a)
                a.shape = (-1, 4)
                m = uids == uid
                a[m] = v[m]
                attrs[n].data.foreach_set('color', a.ravel())
            
            for n in uvs:
                v = np.c_[
                    attributes['uv_{}_x'.format(n)],
                    attributes['uv_{}_y'.format(n)],
                ]
                a = np.zeros((l * 2), dtype=np.float64, )
                attrs[n].data.foreach_get('vector', a)
                a.shape = (-1, 2)
                m = uids == uid
                a[m] = v[m]
                attrs[n].data.foreach_set('vector', a.ravel())
            
            for n in vgroups:
                v = attributes['vgroup_{}'.format(n)]
                a = np.zeros(l, dtype=np.float64, )
                attrs[n].data.foreach_get('value', a)
                m = uids == uid
                a[m] = v[m]
                attrs[n].data.foreach_set('value', a.ravel())
        
        for uid, item in db.items():
            me = item['me']
            bpy.data.meshes.remove(me)
        
        db = None
        
        '''
        # DEBUG
        me = target.data
        l = len(me.vertices)
        vs = np.zeros(l * 3, dtype=np.float64, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        uids = np.zeros(l, dtype=int, )
        from .brushes import SCATTER5_OT_common_mixin
        me.attributes['{}surface_uuid'.format(SCATTER5_OT_common_mixin.attribute_prefix)].data.foreach_get('value', uids, )
        for s in surfaces:
            m = uids == s.scatter5.uuid
            svs = vs[m]
            mw = s.matrix_world
            for i, v in enumerate(svs):
                svs[i] = mw @ Vector(v)
            vs[m] = svs
        
        names = []
        values = []
        for n in set(add_vcols):
            a = np.zeros(l * 4, dtype=np.float64, )
            me.attributes[n].data.foreach_get('color', a, )
            a.shape = (-1, 4)
            names.extend(['{}_r'.format(n), '{}_g'.format(n), '{}_b'.format(n), '{}_a'.format(n), ])
            values.extend([a[:, 0], a[:, 1], a[:, 2], a[:, 3], ])
        for n in set(add_uvs):
            a = np.zeros(l * 2, dtype=np.float64, )
            me.attributes[n].data.foreach_get('vector', a, )
            a.shape = (-1, 2)
            names.extend(['{}_x'.format(n), '{}_y'.format(n), ])
            values.extend([a[:, 0], a[:, 1], ])
        for n in set(add_vgroups):
            a = np.zeros(l, dtype=np.float64, )
            me.attributes[n].data.foreach_get('value', a, )
            names.extend(['{}'.format(n), ])
            values.extend([a, ])
        
        dt = [('x', float), ('y', float), ('z', float), ]
        for n in names:
            dt.append((n, float, ))
        points = np.empty(l, dtype=dt, )
        points['x'] = vs[:, 0]
        points['y'] = vs[:, 1]
        points['z'] = vs[:, 2]
        for i, n in enumerate(names):
            points[n] = values[i]
        
        import space_view3d_point_cloud_visualizer as pcv
        pd = pcv.data.PCVPointData.from_points('_.ply', points)
        viz = pcv.mechanist.PCVOverseer(target, )
        viz.data(pd, )
        viz.props().display.vertex_normals = True
        viz.props().display.vertex_normals_size = 1.0
        viz.props().display.vertex_normals_alpha = 1.0
        viz.props().display.point_size = 6
        viz.props().display.draw_in_front = True
        # DEBUG
        '''
    
    def execute(self, context, ):
        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.get_psy_active()
        surfaces = psys.get_surfaces()
        target = psys.scatter_obj
        self.transfer(surfaces, target, )
        return {'FINISHED'}


class SCATTER5_OT_manual_convert_from_procedural(Operator, ):
    bl_idname = "scatter5.manual_convert_from_procedural"
    bl_label = translate("Convert Points to Manual")
    bl_description = translate("Convert Points to Manual")
    bl_options = {'INTERNAL', }
    
    preserve_appearance: BoolProperty(name=translate("Preserve Appearance"), default=True, description=translate("Set manual indexing to instances to preserve appearence. This is limited 10 objects in instanced collection"), )
    
    @classmethod
    def poll(cls, context, ):
        if(context.space_data is None):
            # NOTE: this can be None, if blender window is active but mouse is outside of it, like on second monitor ;)
            return False
        if(context.space_data.type != 'VIEW_3D'):
            return False
        
        if(context.mode != 'OBJECT'):
            return False
        
        emitter = bpy.context.scene.scatter5.emitter
        if(emitter is None):
            return False
        psys = emitter.scatter5.get_psy_active()
        if(psys is None):
            return False
        # if(psys.s_distribution_method != 'manual_all'):
        #     return False
        
        surfaces = psys.get_surfaces()
        if(not len(surfaces)):
            return False
        for s in surfaces:
            if(s is None):
                return False
        
        target = psys.scatter_obj
        if(target is None):
            return False
        
        return True
    
    def collect(self, context, ):
        from .brushes import ToolSessionCache
        
        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.get_psy_active()
        surfaces = psys.get_surfaces()
        target = psys.scatter_obj
        
        # FIXME: TODO: no idea how to get instance surface uuid, so i will do proximity check for now. if some procedural settings move instances out of surface, well, bad luck..
        
        cache = ToolSessionCache.get(context, surfaces, )
        bvh = cache['bvh']
        f_surface = cache['arrays']['f_surface']
        db = {}
        for s in surfaces:
            db[s.scatter5.uuid] = s.name
        
        depsgraph = bpy.context.evaluated_depsgraph_get()
        instances = []
        
        y = Vector((0.0, 1.0, 0.0))
        z = Vector((0.0, 0.0, 1.0))
        
        for i in depsgraph.object_instances:
            if(i.is_instance):
                if(i.parent.original == target):
                    # mw = i.matrix_world.copy()
                    # world_loc, rot, sca = mw.decompose()
                    # rot = rot.to_euler('XYZ', )
                    # _, world_nor, idx, _ = bvh.find_nearest(world_loc)
                    # uid = f_surface[idx]
                    #
                    # smw = bpy.data.objects.get(db[int(uid)]).matrix_world.copy()
                    # sinvmw = smw.inverted()
                    #
                    # local_loc = sinvmw @ world_loc
                    #
                    # _, _, s = sinvmw.decompose()
                    # ms = Matrix(((s.x, 0.0, 0.0, 0.0), (0.0, s.y, 0.0, 0.0), (0.0, 0.0, s.z, 0.0), (0.0, 0.0, 0.0, 1.0)))
                    # sca = ms @ sca
                    #
                    # mr = rot.to_matrix().to_4x4()
                    # axis_y = mr @ y
                    # axis_z = mr @ z
                    #
                    # instances.append((i.object.original.name, world_loc, world_nor, local_loc, axis_y, axis_z, sca, uid, ))
                    
                    m_world = i.matrix_world.copy()
                    world_loc, _, _ = m_world.decompose()
                    _, world_nor, idx, _ = bvh.find_nearest(world_loc)
                    uid = f_surface[idx]
                    
                    surface_mw = bpy.data.objects.get(db[int(uid)]).matrix_world.copy()
                    surface_mw_inv = surface_mw.inverted()
                    
                    local_loc = surface_mw_inv @ world_loc
                    
                    _, r, s = m_world.decompose()
                    mr = r.to_euler('XYZ', ).to_matrix().to_4x4()
                    axis_y = mr @ y
                    axis_z = mr @ z
                    
                    ms = Matrix(((s.x, 0.0, 0.0, 0.0), (0.0, s.y, 0.0, 0.0), (0.0, 0.0, s.z, 0.0), (0.0, 0.0, 0.0, 1.0)))
                    ms = surface_mw_inv @ ms
                    _, _, scale = ms.decompose()
                    
                    instances.append((i.object.original.name, world_loc, world_nor, local_loc, axis_y, axis_z, scale, uid, ))
        
        '''
        # DEBUG
        # vs = np.array([local_loc for _, _, local_loc, _, _, _, _ in instances], dtype=np.float64, )
        vs = np.array([world_loc for _, world_loc, _, _, _, _, _, _ in instances], dtype=np.float64, )
        vs = np.concatenate([vs, vs, ])
        ys = np.array([y for _, _, _, _, y, _, _, _ in instances], dtype=np.float64, )
        zs = np.array([z for _, _, _, _, _, z, _, _ in instances], dtype=np.float64, )
        ns = np.concatenate([ys, zs, ])
        uids = np.array([uid for _, _, _, _, _, _, _, uid in instances], dtype=int, )
        uids = np.concatenate([uids, uids, ])
        l = len(vs)
        dt = [('x', float), ('y', float), ('z', float),
              ('nx', float), ('ny', float), ('nz', float),
              ('uid', int, ), ]
        points = np.empty(l, dtype=dt, )
        points['x'] = vs[:, 0]
        points['y'] = vs[:, 1]
        points['z'] = vs[:, 2]
        points['nx'] = ns[:, 0]
        points['ny'] = ns[:, 1]
        points['nz'] = ns[:, 2]
        points['uid'] = uids.ravel()
        
        import point_cloud_visualizer as pcv
        pd = pcv.data.PCVPointData.from_points('_.ply', points)
        viz = pcv.mechanist.PCVOverseer(target, )
        viz.data(pd, )
        viz.props().display.vertex_normals = True
        viz.props().display.vertex_normals_size = 1.0
        viz.props().display.vertex_normals_alpha = 1.0
        viz.props().display.point_size = 6
        viz.props().display.draw_in_front = True
        viz.props().display.use_scalar = True
        # DEBUG
        '''
        
        ToolSessionCache.free()
        
        return instances, db
    
    def execute(self, context, ):
        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.get_psy_active()
        # NOTE: switch it off so i get real object instances from depsgraph
        s_display_allow = psys.s_display_allow
        psys.s_display_allow = False
        
        data, db = self.collect(context, )
        
        emitter = bpy.context.scene.scatter5.emitter
        psys = emitter.scatter5.get_psy_active()
        surfaces = psys.get_surfaces()
        target = psys.scatter_obj
        
        psys.s_distribution_method = 'manual_all'
        
        me = target.data
        me.clear_geometry()
        
        from .brushes import SCATTER5_OT_common_mixin
        
        prefix = SCATTER5_OT_common_mixin.attribute_prefix
        # ensure attributes
        for n, t in SCATTER5_OT_common_mixin.attribute_map.items():
            nm = '{}{}'.format(prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
        
        l = len(data)
        me.vertices.add(l)
        
        names = []
        debug_vs = np.zeros((l, 3), dtype=np.float64, )
        vs = np.zeros((l, 3), dtype=np.float64, )
        ns = np.zeros((l, 3), dtype=np.float64, )
        ys = np.zeros((l, 3), dtype=np.float64, )
        zs = np.zeros((l, 3), dtype=np.float64, )
        scas = np.zeros((l, 3), dtype=np.float64, )
        uids = np.zeros(l, dtype=int, )
        for i, (n, wl, wn, ll, y, z, s, uid, ) in enumerate(data):
            names.append(n)
            debug_vs[i] = wl
            vs[i] = ll
            ns[i] = wn
            ys[i] = y
            zs[i] = z
            scas[i] = s
            uids[i] = uid
        
        rng = np.random.default_rng()
        
        me.vertices.foreach_set('co', vs.ravel(), )
        me.attributes['{}id'.format(prefix)].data.foreach_set('value', np.arange(l).ravel(), )
        me.attributes['{}surface_uuid'.format(prefix)].data.foreach_set('value', uids.ravel(), )
        
        me.attributes['{}normal'.format(prefix)].data.foreach_set('vector', ns.ravel(), )
        
        ra = np.zeros(l, dtype=int, ) + 3
        me.attributes['{}private_r_align'.format(prefix)].data.foreach_set('value', ra.ravel(), )
        me.attributes['{}private_r_align_vector'.format(prefix)].data.foreach_set('vector', zs.ravel(), )
        
        ru = np.zeros(l, dtype=int, ) + 2
        me.attributes['{}private_r_up'.format(prefix)].data.foreach_set('value', ru.ravel(), )
        me.attributes['{}private_r_up_vector'.format(prefix)].data.foreach_set('vector', ys.ravel(), )
        rr = rng.random((l, 3, ), )
        me.attributes['{}private_r_random_random'.format(prefix)].data.foreach_set('vector', rr.ravel(), )
        
        me.attributes['{}private_s_base'.format(prefix)].data.foreach_set('vector', scas.ravel(), )
        rr = rng.random((l, 3, ), )
        me.attributes['{}private_s_random_random'.format(prefix)].data.foreach_set('vector', rr.ravel(), )
        
        me.attributes['{}scale'.format(prefix)].data.foreach_set('vector', scas.ravel(), )
        
        def direction_to_rotation(direction, up=Vector((0.0, 1.0, 0.0, )), ):
            x = up.cross(direction)
            x.normalize()
            y = direction.cross(x)
            y.normalize()
            
            m = Matrix()
            m[0][0] = x.x
            m[0][1] = y.x
            m[0][2] = direction.x
            m[1][0] = x.y
            m[1][1] = y.y
            m[1][2] = direction.y
            m[2][0] = x.z
            m[2][1] = y.z
            m[2][2] = direction.z
            
            return m.to_quaternion()
        
        rotation = np.zeros((l, 3), dtype=np.float64, )
        for i in np.arange(l):
            a = direction_to_rotation(Vector(zs[i]), Vector(ys[i]))
            
            uid = uids[i]
            m = bpy.data.objects.get(db[int(uid)]).matrix_world.inverted()
            _, r, _ = m.decompose()
            
            q = Quaternion()
            q.rotate(a)
            q.rotate(r)
            e = q.to_euler('XYZ')
            rotation[i] = (e.x, e.y, e.z, )
        
        me.attributes['{}rotation'.format(prefix)].data.foreach_set('vector', rotation.ravel(), )
        
        align_z = np.zeros((l, 3), dtype=np.float64, )
        align_y = np.zeros((l, 3), dtype=np.float64, )
        for i in np.arange(l):
            v = Vector((0.0, 0.0, 1.0))
            v.rotate(Euler(rotation[i]))
            align_z[i] = v.to_tuple()
            v = Vector((0.0, 1.0, 0.0))
            v.rotate(Euler(rotation[i]))
            align_y[i] = v.to_tuple()
        
        me.attributes['{}align_y'.format(prefix)].data.foreach_set('vector', align_y.ravel(), )
        me.attributes['{}align_z'.format(prefix)].data.foreach_set('vector', align_z.ravel(), )
        
        bpy.ops.scatter5.disable_main_settings()
        
        '''
        # DEBUG
        vs = np.concatenate([debug_vs, debug_vs])
        ns = np.concatenate([align_y, align_z])
        dt = [('x', float), ('y', float), ('z', float),
              ('nx', float), ('ny', float), ('nz', float), ]
        points = np.empty(len(vs), dtype=dt, )
        points['x'] = vs[:, 0]
        points['y'] = vs[:, 1]
        points['z'] = vs[:, 2]
        points['nx'] = ns[:, 0]
        points['ny'] = ns[:, 1]
        points['nz'] = ns[:, 2]
        
        import point_cloud_visualizer as pcv
        pd = pcv.data.PCVPointData.from_points('_.ply', points)
        viz = pcv.mechanist.PCVOverseer(target, )
        viz.data(pd, )
        viz.props().display.vertex_normals = True
        viz.props().display.vertex_normals_size = 1.0
        viz.props().display.vertex_normals_alpha = 1.0
        viz.props().display.point_size = 6
        viz.props().display.draw_in_front = True
        viz.props().display.use_scalar = False
        # DEBUG
        '''
        
        if(self.preserve_appearance):
            unique = sorted(list(set(names)))
            db = {}
            for i, n in enumerate(unique):
                db[n] = i
            
            psys.s_instances_pick_method = 'pick_idx'
            
            ii = np.zeros(l, dtype=int, )
            for i, n in enumerate(names):
                ii[i] = db[n]
            
            me.attributes['{}index'.format(prefix)].data.foreach_set('value', ii.ravel(), )
        
        # notify..
        me.update()
        
        # NOTE: switch it back to keep user settings
        psys.s_display_allow = s_display_allow
        
        return {'FINISHED'}
    
    def invoke(self, context, event, ):
        return bpy.context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        l = self.layout
        l.separator(factor=0.33)
        word_wrap(layout=l, alignment="CENTER", active=True, max_char=55, string=translate("This operator will transfer the procedurally generated points to Manual distribution where you will be able to have precise control thanks to the help of the various brushes."), )
        l.separator(factor=0.33)
        word_wrap(layout=l, alignment="CENTER", active=True, max_char=55, string=translate("Note that this operator is semi-destructive, as it will turn off most procedural features. Manual mode can handle up to 50.000 points depending on your computer."), )
        l.separator(factor=0.33)
        word_wrap(layout=l, alignment="CENTER", active=True, max_char=55, string=translate("Some instance properties cannot be converted. Some only partially. Use option bellow to get close to procedural appearence."), )
        l.separator(factor=0.33)
        r = l.row()
        r.alignment = 'CENTER'
        r.prop(self, 'preserve_appearance', )
        l.separator(factor=0.33)
        word_wrap(layout=l, alignment="CENTER", active=True, max_char=55, string=translate("Press 'OK' to proceed to the conversion"), )
        l.separator()


class SCATTER5_OT_manual_drop_to_ground(Operator, ):
    bl_idname = "scatter5.manual_drop_to_ground"
    bl_label = translate("Drop To Ground")
    bl_description = translate("Drop all points to emitter and ground plane along global Z axis")
    bl_options = {'INTERNAL', 'UNDO'}
    
    @classmethod
    def poll(cls, context, ):
        try:
            target = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active().scatter_obj
            if(len(target.data.vertices)):
                from .brushes import ToolBox
                tool = ToolBox.reference
                if(tool is not None):
                    return True
        except Exception as e:
            pass
        return False
    
    def execute(self, context, ):
        from .brushes import ToolBox, get_tool_class
        tool = ToolBox.reference
        tool_id = tool.tool_id
        if(tool_id != "scatter5.manual_brush_tool_drop_down"):
            opc = get_tool_class("scatter5.manual_brush_tool_drop_down")
            n = opc.bl_idname.split('.', 1)
            op = getattr(getattr(bpy.ops, n[0]), n[1])
            op('INVOKE_DEFAULT', )
        
        props = bpy.context.scene.scatter5.manual.tool_drop_down
        u = props.use_ground_plane
        props.use_ground_plane = True
        bpy.ops.scatter5.manual_apply_brush()
        props.use_ground_plane = u
        
        if(tool_id != "scatter5.manual_brush_tool_drop_down"):
            opc = get_tool_class(tool_id)
            n = opc.bl_idname.split('.', 1)
            op = getattr(getattr(bpy.ops, n[0]), n[1])
            op('INVOKE_DEFAULT', )
        
        return {'FINISHED'}


class SCATTER5_OT_manual_reassign_surface(Operator, ):
    bl_idname = "scatter5.manual_reassign_surface"
    bl_label = translate("Re-Assign Surface By Proximity")
    bl_description = translate("Assign all instances to their closest surface by distance")
    bl_options = {'INTERNAL', 'UNDO'}
    
    @classmethod
    def poll(cls, context, ):
        try:
            target = bpy.context.scene.scatter5.emitter.scatter5.get_psy_active().scatter_obj
            if(len(target.data.vertices)):
                from .brushes import ToolBox
                tool = ToolBox.reference
                if(tool is not None):
                    # make sure any tool is running..
                    return True
        except Exception as e:
            pass
        return False
    
    def execute(self, context, ):
        from .brushes import ToolBox, ToolSessionCache
        # NOTE: lets pretend this is tool of some sort so i have access to internal utilities
        self = ToolBox.reference
        
        me = self._target.data
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        
        for i, v in enumerate(vs):
            v = Vector(v)
            # this should get something no matter how far (if bvh contains some geometry, but if there is none, manual mode should not start at all)
            _, _, idx, _ = self._bvh.find_nearest(v)
            u = int(ToolSessionCache._cache['arrays']['f_surface'][idx])
            uids[i] = u
        
        # NOTE: now, do i need to handle other properties? like scale which depends on surface scale?
        
        vs, _ = self._world_to_surfaces_space(vs, nor=None, uid=uids, )
        self._set_target_attribute_masked(me.vertices, 'co', vs, )
        self._set_target_attribute_masked(me.attributes, 'surface_uuid', uids, )
        # NOTE: force it to update, setting stuff with `foreach_set` will not trigger update
        me.update()
        
        return {'FINISHED'}


classes = (
    # SCATTER5_OT_manual_tool_gesture,
    SCATTER5_OT_manual_clear,
    SCATTER5_OT_manual_clear_orphan_data,
    # SCATTER5_OT_manual_convert_dialog,
    SCATTER5_OT_manual_enter,
    SCATTER5_OT_manual_exit,
    SCATTER5_OT_apply_brush,
    # SCATTER5_OT_manual_edit,
    # SCATTER5_OT_manual_drop,
    SCATTER5_OT_manual_switch,
    SCATTER5_OT_manual_scatter_add_new,
    SCATTER5_OT_surfaces_data_to_attributes,
    SCATTER5_OT_manual_convert_from_procedural,
    # SCATTER5_OT_manual_sync_tool_properties,
    SCATTER5_OT_manual_drop_to_ground,
    SCATTER5_OT_manual_reassign_surface,
)
