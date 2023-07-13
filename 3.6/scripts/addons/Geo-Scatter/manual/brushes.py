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
import math
import random
import traceback
# import time
import numpy as np

import bpy
import bmesh
from bpy.types import Operator
from bpy_extras import view3d_utils
import mathutils
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree

from . import debug
from .debug import log, profile, verbose, stopwatch, profile
from . import config
from .navigator import ToolNavigator
from ..widgets import infobox

from .. resources.translate import translate
from ..ui import ui_manual


# -----------------------------------------------------------------------------------------------------------------------------

# DONE: after all brushes are converted, make major cleanup in `manual_settings`, there is A LOT of unused garbage (well, it happened for compatibility when several tools has been split, this is no longer needed)
# NOTTODO: maybe this is a good time to rethink all attribute system, i mean.. ROTATIONS!!!!!!1!1!11!!!.. or not? BUT, that would need special operator to upgrade old system.

from ..widgets.theme import ToolTheme
from ..widgets.widgets import ToolWidgets
from ..widgets.infobox import SC5InfoBox
# from ..widgets.grid import SC5GridOverlay
from ..widgets.grid import GridOverlay


# NOTTODO: when done, move to own module (?) or maybe even to `__init__`? -->> then i would need to re-import it for every use so i have current state..
class ToolBox():
    tool = None
    reference = None


class ToolSession():
    active = False
    user_tool = None
    user_select = []
    user_active = None
    
    tool_cache = {}
    
    @classmethod
    def reset(cls, ):
        # better to call function that just repeat what is in class definition so i don't forget on something later
        cls.active = False
        cls.user_tool = None
        cls.user_select = []
        cls.user_active = None
        
        cls.tool_cache = {}


# TODO: maybe use F shortcut for brush radius, falloff and affect (weird name, maybe change that as well) AND another (which one?) for brush effects like distance, strength, count, whatever..
# TODO: with two shortcuts i can split 'common' brush props and brush effect specific props. like that every brush will have basics the same (or just missing if not applicable)
# TODO: so, all specific props on different key, so they don't mix with common props..
# TODO: the question is, which key? `D`? is right next to `F`, good, is easy to reach with one hand even with several modifiers..
# DONE: link to preferences and config (rewrite first run at least) so `_collect` is not hard coded
# DONE: new ui for keymap in preferences
# TODO: when done, move to own module (or to `keys`)
# TODO: not sure if `COMMAND` is that important to include it everywhere. oskey is not useable anyway. but it is still modifier..
class ToolKeyConfigurator():
    @staticmethod
    def to_flag(shift, ctrl, alt, cmd, ):
        return (shift << 0) | (ctrl << 1) | (alt << 2) | (cmd << 3)
    
    @staticmethod
    def from_flag(value, ):
        shift = bool(value >> 0 & 1)
        ctrl = bool(value >> 1 & 1)
        alt = bool(value >> 2 & 1)
        cmd = bool(value >> 3 & 1)
        return shift, ctrl, alt, cmd
    
    @classmethod
    def get_string_shortcut_for_tool(cls, tool_id, ):
        db = cls._collect()
        key = tool_id.split('.')[-1]
        if(key in db.keys()):
            v = db[key]
            if(v is not None):
                # NOTE: swap keys order for key combo string so they appear in logical order on screen
                # NOTE: command is irrelevant, i thought it might function as ctrl on mac (windows oskey is not usable in this way), but it would mess up thigs a lot
                ns = ['CTRL', 'ALT', 'SHIFT', 'COMMAND', ]
                bs = cls.from_flag(v['flag'])
                bs = [bs[1], bs[2], bs[0], bs[3], ]
                
                r = ""
                for i in range(4):
                    if(bs[i]):
                        r = "{}{}+".format(r, ns[i])
                k = v['type']
                r = "{}{}".format(r, k)
                return r
        return ""
    
    @classmethod
    def get_fancy_string_shortcut_for_tool(cls, tool_id, ):
        s = cls.get_string_shortcut_for_tool(tool_id, )
        if(s != ''):
            if(s == 'NONE'):
                return ''
            
            d = {
                'ZERO': '0',
                'ONE': '1',
                'TWO': '2',
                'THREE': '3',
                'FOUR': '4',
                'FIVE': '5',
                'SIX': '6',
                'SEVEN': '7',
                'EIGHT': '8',
                'NINE': '9',
                
                'CTRL': '⌃',
                'ALT': '⌥',
                'SHIFT': '⇧',
                'COMMAND': '⌘',
            }
            ls = []
            for i in s.split('+'):
                if(i in d.keys()):
                    ls.append(d[i])
                else:
                    ls.append(i)
            
            s = ' '.join(ls)
        return s
    
    def __init__(self, tool, ):
        try:
            db = self._collect()
        except Exception as e:
            # NOTE: is there is something wrong with keymaps, use defaults. they are generated from static data in `keys` module, should be ok.. unless..
            import traceback
            traceback.print_exc()
            
            db = self._collect_defaults()
        
        evs = {}
        gdefs = tool.tool_gesture_definitions
        
        # NOTE: copy, because i will modify that on the fly if property is radius. this should be enough..
        cp = {}
        for k, v in gdefs.items():
            cp[k] = v
        gdefs = cp
        
        for k, v in db.items():
            if(v is None):
                continue
            if(v['call'] == 'GESTURE'):
                if(gdefs):
                    if(k in gdefs.keys()):
                        v['properties'] = self._gesture_definition_fill_defaults(gdefs[k])
            
            evs[k] = (v['type'], v['value'], v['flag'], )
        
        self._db = db
        self._evs = evs
    
    def check(self, context, event, ):
        d = None
        ev = (event.type, event.value, self.to_flag(event.shift, event.ctrl, event.alt, event.oskey, ), )
        if(ev in self._evs.values()):
            key = list(self._evs.keys())[list(self._evs.values()).index(ev)]
            import copy
            d = copy.deepcopy(self._db[key])
            d['key'] = key
        return d
    
    @staticmethod
    def _gesture_definition_fill_defaults(d, ):
        # the most common gesture definition..
        # NOTE: to be sure, always define at least `property`, `name` and `widget` for floats
        # NOTE: for others `datatype` and `text`..
        # NOTE: the rest is most of the time the same..
        # NOTE: for float radius, it would bu sufficient to pass empty dict.. hehe..
        # NOTE: anyway, better to always define all..
        
        if('widget' in d.keys()):
            if(d['widget'] == 'FUNCTION_CALL'):
                # NOTE: do not mess with function call definition.. it need all set othrwise won't work
                return d
        
        dd = {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        }
        ks = d.keys()
        for k, v in dd.items():
            if(k not in ks):
                d[k] = v
        return d
    
    # NOTE: get config defaults from source
    @classmethod
    def _collect_defaults(cls, ):
        db = {}
        
        from . import keys
        
        for n, e, _ in keys.op_key_defs[2]['items']:
            k = n.split('.')[-1]
            
            if(not k.startswith('manual_brush_tool_')):
                # NOTE: skip ops that are not brush tools
                continue
            
            db[k] = {
                'value': e['value'],
                'type': e['type'],
                'flag': cls.to_flag(getattr(e, 'shift', False),
                                    getattr(e, 'ctrl', False),
                                    getattr(e, 'alt', False),
                                    getattr(e, 'oskey', False), ),
                'call': 'OPERATOR',
                'execute': n,
                'arguments': [],
                'properties': None,
            }
        
        gesture_map = {
            'PRIMARY': '__gesture_primary__',
            'SECONDARY': '__gesture_secondary__',
            'TERTIARY': '__gesture_tertiary__',
            'QUATERNARY': '__gesture_quaternary__',
        }
        
        for n, e, a in keys.mod_key_defs[2]['items']:
            p = a['properties']
            g = p[0][1]
            k = gesture_map[g]
            db[k] = {
                'value': e['value'],
                'type': e['type'],
                'flag': cls.to_flag(getattr(e, 'shift', False),
                                    getattr(e, 'ctrl', False),
                                    getattr(e, 'alt', False),
                                    getattr(e, 'oskey', False), ),
                'call': 'GESTURE',
                'execute': '',
                'arguments': [],
                'properties': None,
            }
        
        # for k, v in db.items():
        #     print(k, v)
        
        return db
    
    # DONE: exclude not brushes and gestures.. somehow
    
    # NOTE: get user config, if something is modified, modified value will be used
    # NOTE: runs once at brush start in case defaults are changed
    @classmethod
    def _collect(cls, ):
        db = {}
        
        gesture_map = {
            'PRIMARY': '__gesture_primary__',
            'SECONDARY': '__gesture_secondary__',
            'TERTIARY': '__gesture_tertiary__',
            'QUATERNARY': '__gesture_quaternary__',
        }
        
        # NOTE: get user modified values, it took me A WHILE to figure this thing
        usermap = getattr(bpy.context.window_manager.keyconfigs.get("Blender user"), "keymaps", None, )
        if(usermap is None):
            # NOTE: background mode, do i need to do something to handle this?
            db = cls._collect_defaults()
            return db
        
        from . import keys
        
        km_name, km_args, km_content = keys.op_key_defs
        km = usermap.find(km_name, **km_args)
        for item in km_content['items']:
            item_id = km.keymap_items.find(item[0])
            if(item_id != -1):
                kmi = km.keymap_items[item_id]
                k = kmi.idname.split('.')[-1]
                
                if(not k.startswith('manual_brush_tool_')):
                    # NOTE: skip ops that are not brush tools
                    continue
                
                v = {
                    'value': kmi.value,
                    'type': kmi.type,
                    'flag': cls.to_flag(kmi.shift, kmi.ctrl, kmi.alt, kmi.oskey),
                    'call': 'OPERATOR',
                    'execute': kmi.idname,
                    'arguments': [],
                    'properties': None,
                }
                db[k] = v
        
        km_name, km_args, km_content = keys.mod_key_defs
        km = usermap.find(km_name, **km_args)
        for kmi in km.keymap_items:
            if(kmi.idname == 'scatter5.manual_tool_gesture'):
                k = gesture_map[getattr(kmi.properties, 'gesture', )]
                v = {
                    'value': kmi.value,
                    'type': kmi.type,
                    'flag': cls.to_flag(kmi.shift, kmi.ctrl, kmi.alt, kmi.oskey),
                    'call': 'GESTURE',
                    'execute': '',
                    'arguments': [],
                    'properties': None,
                }
                db[k] = v
        
        # for k, v in db.items():
        #     print(k, v)
        
        return db


# DONE: do not free cache on tool exit or switch. keep cache while mode is enabled.. but until ui rebuild is done, there is no point in doing this.
# DONE: update tools to use arrays from cache, tools like lasso, smooth and manipulator (maybe others) can use data directly from cache, no need to collect stuff again. get arrays and COPY (IMPORTANT) them. done. -->> only lasso updated, smooth ans manipulator work with target mesh
# NOTTODO: when done, move to own module `session` or `cache` --> too tied to tools, should be still part of it, also same as ToolSession and ToolBox
# DONE: because i am adding mesh datablock, on undo it might get cleared out and i am left with invalid reference -->> no datablock added, use `_cached_arrays_to_mesh_datablock` instead
# TODO: rename to something more descriptive so it is not confused with ToolSession.tool_cache, something like `SceneGeometryCache` or something..
class ToolSessionCache():
    _initialized = False
    _cache = None
    
    @classmethod
    def get(cls, context, surfaces, ):
        log("get()", prefix='SESSION >>>', )
        
        if(not cls._initialized):
            log("_generate()", prefix='SESSION >>>', )
            cls._generate(context, surfaces, )
            cls._initialized = True
        return cls._cache
    
    @classmethod
    def _generate(cls, context, surfaces, ):
        depsgraph = context.evaluated_depsgraph_get()
        
        data = {}
        for i, o in enumerate(surfaces):
            if(o.type != 'MESH'):
                # WATCH: ignore anything. but meshes. all objects will get processed, but should be alright, they will not interfere.. i think..
                continue
            
            eo = o.evaluated_get(depsgraph)
            
            bm = bmesh.new()
            bm.from_object(eo, depsgraph, )
            bm.transform(o.matrix_world)
            # NOTE: noo need for `bmesh.ops.triangulate`, i will use `calc_loop_triangles`..
            me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
            bm.to_mesh(me)
            bm.free()
            
            me.validate()
            me.calc_normals()
            me.calc_loop_triangles()
            
            l = len(me.vertices)
            
            v_co = np.zeros(l * 3, dtype=float, )
            me.vertices.foreach_get('co', v_co)
            v_co.shape = (-1, 3)
            
            v_normal = np.zeros(l * 3, dtype=float, )
            me.vertices.foreach_get('normal', v_normal)
            v_normal.shape = (-1, 3)
            
            l = len(me.loop_triangles)
            
            f_vertices = np.zeros(l * 3, dtype=int, )
            me.loop_triangles.foreach_get('vertices', f_vertices)
            f_vertices.shape = (-1, 3)
            
            f_normal = np.zeros(l * 3, dtype=float, )
            me.loop_triangles.foreach_get('normal', f_normal)
            f_normal.shape = (-1, 3)
            
            f_area = np.zeros(l, dtype=float, )
            me.loop_triangles.foreach_get('area', f_area)
            f_area.shape = (-1, 1)
            
            f_smooth = np.zeros(l, dtype=bool, )
            me.loop_triangles.foreach_get('use_smooth', f_smooth)
            f_smooth.shape = (-1, 1)
            
            bpy.data.meshes.remove(me)
            
            u = o.scatter5.uuid
            
            data[o.name] = {
                'v_co': v_co,
                'v_normal': v_normal,
                'v_surface': u,
                'f_vertices': f_vertices,
                'f_normal': f_normal,
                'f_area': f_area,
                'f_smooth': f_smooth,
                'f_surface': u,
            }
        
        lv = 0
        lf = 0
        
        ls_v_co = []
        ls_v_normal = []
        ls_v_surface = []
        ls_f_vertices = []
        ls_f_normal = []
        ls_f_area = []
        ls_f_smooth = []
        ls_f_surface = []
        for k, v in data.items():
            ls_v_co.append(v['v_co'])
            ls_v_normal.append(v['v_normal'])
            ls_f_normal.append(v['f_normal'])
            ls_f_area.append(v['f_area'])
            ls_f_smooth.append(v['f_smooth'])
            
            l = len(v['v_co'])
            fs = v['f_vertices']
            fs += lv
            ls_f_vertices.append(fs)
            a = np.full(l, v['v_surface'], dtype=int, )
            a.shape = (-1, 1)
            ls_v_surface.append(a)
            lv += l
            
            l = len(fs)
            a = np.full(l, v['f_surface'], dtype=int, )
            a.shape = (-1, 1)
            ls_f_surface.append(a)
            lf += l
        
        all_v_co = np.concatenate(ls_v_co)
        all_v_normal = np.concatenate(ls_v_normal)
        all_v_surface = np.concatenate(ls_v_surface)
        all_f_vertices = np.concatenate(ls_f_vertices)
        all_f_normal = np.concatenate(ls_f_normal)
        all_f_area = np.concatenate(ls_f_area)
        all_f_smooth = np.concatenate(ls_f_smooth)
        all_f_surface = np.concatenate(ls_f_surface)
        
        me = bpy.data.meshes.new(name='tmp-{}'.format(uuid.uuid1()), )
        me.vertices.add(lv)
        me.vertices.foreach_set('co', all_v_co.flatten(), )
        
        me.loops.add(lf * 3)
        me.polygons.add(lf)
        lt = np.full(lf, 3, dtype=int, )
        ls = np.arange(0, lf * 3, 3, dtype=int, )
        me.polygons.foreach_set('loop_total', lt.flatten(), )
        me.polygons.foreach_set('loop_start', ls.flatten(), )
        me.polygons.foreach_set('vertices', all_f_vertices.flatten(), )
        me.polygons.foreach_set('use_smooth', all_f_smooth.flatten(), )
        
        a = me.attributes.new('v_surface', 'INT', 'POINT')
        a.data.foreach_set('value', all_v_surface.flatten(), )
        a = me.attributes.new('f_surface', 'INT', 'FACE')
        a.data.foreach_set('value', all_f_surface.flatten(), )
        
        me.validate()
        
        # # DEBUG
        # o = bpy.data.objects.new('debug', me, )
        # bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
        # # DEBUG
        
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        bvh = BVHTree.FromBMesh(bm, epsilon=0.0, )
        
        bpy.data.meshes.remove(me)
        
        cls._cache = {
            # references to surfaces objects in original order
            'surfaces': surfaces,
            # bvh from merged mesh
            'bvh': bvh,
            # bmesh from merged mesh
            'bm': bm,
            # arrays of attributes of merged mesh
            # NOTE: add more if needed..
            'arrays': {
                'v_co': all_v_co,
                'v_normal': all_v_normal,
                'v_surface': all_v_surface,
                'f_vertices': all_f_vertices,
                'f_normal': all_f_normal,
                'f_area': all_f_area,
                'f_smooth': all_f_smooth,
                'f_surface': all_f_surface,
            },
        }
    
    @classmethod
    def _cached_arrays_to_mesh_datablock(cls, name=None, ):
        if(not cls._initialized):
            return None
        
        if(name is None):
            name = 'tmp-{}'.format(uuid.uuid1())
        
        lv = len(cls._cache['arrays']['v_co'])
        lf = len(cls._cache['arrays']['f_vertices'])
        
        me = bpy.data.meshes.new(name=name, )
        me.vertices.add(lv)
        me.vertices.foreach_set('co', cls._cache['arrays']['v_co'].flatten(), )
        
        me.loops.add(lf * 3)
        me.polygons.add(lf)
        lt = np.full(lf, 3, dtype=int, )
        ls = np.arange(0, lf * 3, 3, dtype=int, )
        me.polygons.foreach_set('loop_total', lt.flatten(), )
        me.polygons.foreach_set('loop_start', ls.flatten(), )
        me.polygons.foreach_set('vertices', cls._cache['arrays']['f_vertices'].flatten(), )
        me.polygons.foreach_set('use_smooth', cls._cache['arrays']['f_smooth'].flatten(), )
        
        a = me.attributes.new('v_surface', 'INT', 'POINT')
        a.data.foreach_set('value', cls._cache['arrays']['v_surface'].flatten(), )
        a = me.attributes.new('f_surface', 'INT', 'FACE')
        a.data.foreach_set('value', cls._cache['arrays']['f_surface'].flatten(), )
        
        # NOTE: i need an update or it might crash
        me.update()
        
        return me
    
    @classmethod
    def free(cls, ):
        if(not cls._initialized):
            return
        
        log("free()", prefix='SESSION >>>', )
        
        cls._cache['surfaces'] = None
        cls._cache['arrays'] = None
        cls._cache['bvh'] = None
        cls._cache['bm'].free()
        cls._cache['bm'] = None
        
        cls._cache = None
        cls._initialized = False


# NOTTODO: separate module with ui rebuild? might be better organized then scattered around brush classes
# DONE: investigate why (some or all?) brushes refuse to work unless mouse is moved a pixel. i suspect because mouse tracking runs on mousemove. maybe it is good idea to run it also on brush start. if shortcut is used, it can be ready to go. when toolbar is clicked it does not matter, but on shortcut it should go -->> yeah, it was it.

# ------------------------------------------------------------------ base classes >>>

# DONE: put somewhere at start mesh.validate() so i don't have deal with errors from users with weird imported meshes with NaN areas polygons. so looks like i need to create bmesh from mesh, and not object, so i got to apply modifiers.. or maybe go with evaluated mesh and loop triangles, copy data (i need that anyway) and make bmesh and bvh together from that? and store all to be used in lasso, etc..

# DONE: is there something i can do with slight delay in screen drawing? -->> conclusion: NO, screen drawing is independent on python. i call it only indirectly. anything that is going to be drawn on screen have to be processed by modal operator before it because i first need to have what to draw and where, then i set it up, `tag_redraw` and wait, when redraw loop kicks in, it will be drawn. so the mechanism is: screen is redrawn (from inside blender), python and operator is run, `modal` gets event and processes data, operator forces another redraw, when actual redraw loop kicks in it is finally on screen. i can't get out of this circle. the faster code i put in operator the better it will get, but i still be a at least one frame after (and i am not speaking of viewport antialiasing samples, so by default i technically lag 8 frames)
# DONE: sometimes (after long testing and constant reloading scripts) center dot starts to behave weirdly. it is much bigger, or flickers. like different texture is taken and drawn instead. there is difference between 2d and 3d dot variant in sizes. maybe pointers to textures got messed up? something is not cleared properly? textures are not removed when no longer used and i run out of possible texture count and it overflows? do i need texture caching then? don't like it... bug in blender? this api is not much used, so it might not be easily noticed..

# DONE: test navigation on ndof device and trackpad, especially manipulator (overridden `_modal()`) and pose brush (`_nav_enabled = False`)
# DONE: use new style numpy dtype, there are still old parts where old style is used

# DONE: ui rebuild, new manual (auto generated) ui menus (if feasible), and get rid of all of old code.. then update utility menu ops
# DONE: after removal of old tools, put props back to `scatter5.manual` (now it is in `manual2` for development..) DON'T FORGET, ALRIGHT?

# ------------------------------------------------------------------ check >>>

# WATCH: all `l = len(me.vertices)` might be invalid, i need to `len(masked_vs)` or `np.sum(active_mask)`, most of the time it is needed for array creation which is no longer case. commented out most of places. watch for the rest, because sometimes it is valid.. rarely..

# ------------------------------------------------------------------ check <<<
# ------------------------------------------------------------------ visual >>>

# WATCH: for `ui_scale` everywhere missing..
# TODO: blender 3.4: The 2D and 3D versions of string enums representing built-in shaders have been merged into a single enum each (8cfca8e1bd). https://developer.blender.org/rB8cfca8e1bd85 so checks for blender 3.4 everywhere. fantastic..
# FIXME: tool change causes status bar to display default text for a single redraw. could this be somehow prevented? or i need to tie that with session?
# TODO: is there a way to get eraser colored cursor at ctrl press down? what is blocking me? other then it is part of gesture? it will color back in gesture.
# TODO: 3d tools, can i somehow draw when out of surface? keep no entry sign, but draw also 3d to 2d converted radius? i can draw it with last 3d location scale, but what if mouse enters surface at different distance? size will jump to new. no smooth transition. don't like that. if there is some way lets do it, but it got to look smooth.

# ------------------------------------------------------------------ visual <<<
# ------------------------------------------------------------------ performance >>>

# TODO: add handler on `depsgraph_update_post` and check if is mesh updated once per tool cycle in all tools (`.updates` on `depsgraph` object passed to handler should get me valuable info about that)
# TODO: single mesh update per cycle should be priority for best performance, so update everything that could be updated to `foreach_*`, except adding one point, that is faster without it. i verified that already
# TODO: observe depsgraph updates while removing all mesh.update() calls so after tool action nothing shows until update is called. then add single well placed update to make sure there is only one. for some reason i see two depsgraph update callbacks. i suspect the second comes from outside and is not related to tool code, but verify that first..
# TODO: check all brushes placement of undo state push is working as expected
# TODO: investigate if writing to attributes trigger mesh update (depsgraph) or not. if it does, don't bother with `mesh.update()` (which will improve performance) and if not, limit to single `mesh.update()` when all is finished (will improve performance as well). also investigate if adding a vertex triggers or not as well..

# ------------------------------------------------------------------ performance <<<
# ------------------------------------------------------------------ functionality >>>

# TODO: investigate why blender is crashing on timer ui restore (calling `panic()` in timer callback), is there something to prevent that?

# ------------------------------------------------------------------ functionality <<<

# DONE: any way to get pressure on timers? it is only available in events, timer do not get any event object. end of story. until pointer is moved no pressure is updated..
# DONE: check all pressure enabled props if they really use pressure to scale itself
# DONE: check if all tools that expose `draw_on` update its value in `_update_references_and_settings` and behaves according to what is set
# DONE: tools with hints, check if some need to draw them when outside of surface. moving in and out of surface while holding lmb and hints showing and hiding is irritating
# DONE: finish update of utility ops from menus (system switching is left, and convert op)
# DONE: error handling with panic for timer calls -->> only error handling. blender keeps crashing when ui is restore on timer event.
# DONE: `brush_type` field is obsolete, remove..
# DONE: rename `Surface Normal Interpolation` to just `Normal Radius` (as in sculpt)? or `Gizmo Interpolation` with `Normal Radius` under it?
# DONE: restoring everything on error really need to change. best would be calling `panic()` on anything. report error so users can screenshot that, then shutdown all. i already have try..except wraped `_modal` and `_invoke` and those two handle almost everything. maybe even change `invoke` into the same form as `modal` have.. before i could just stop tool and done, but now i need to deal with workspace..
# DONE: add one more menu `Location`? for props related to it? put props from tool menu in move tools etc.?
# DONE: change `Mouse Wheel Up/Down` to `Mouse Wheel`, shorter, nicer..
# DONE: replace all `_circle_dot_2d_radius` and `_circle_dot_2d_steps` fake dots with proper shader based circle..
# DONE: `ui_scale` for both sprays count gesture widget crosses
# DONE: `ui_scale` lasso dots and line thicknes
# DONE: `ui_scale` switch and tooltip offsets in boolean gesture
# FIXMENOT: `ui_scale` stength gesture minimal size -->> is seems to be set on `_fixed_radius` * 2, `_fixed_radius` is already `ui_scale`d
# DONE: `ui_scale` values for `fancy_tooltip_2d` and `fancy_switch_2d`
# DONE: find some other way to draw 3d and 2d dots. draw plane and do it all in fragment shader? might be easier then dealing with `GPUTexture` weird stuff
# NOTTODOJUSTYET: cursor 3d widget normal alignment interpolation a few (10?) steps back in history so it does not jump that bloody much on displaced surface, but interpolate only display normal! >>>>>> see `SCATTER5_OT_manual_brush_tool_base._interpolate_normal_by_sampling_around` for details..
# DONE: `LENGTH_3D` gesture widget rework, still real size, from cursor at 0.0 set direct distance to mouse (in 2d, but it must have 3d value, so it is going to be difficult)
# DONE: use mouse wheel while in gesture so there is no need to move mouse.. just an option..
# DONE: gesture definition defaults? unless set on tool it will use value from defaults? another job for `ToolKeyConfigurator`
# NOTTODO: stop drawing widgets while navigating? problem is how to determine that user finished navigating, unless mouse is moved or key pressed i have no event to find out.. >>> i see no way to fix delay..
# NOTTODO: also, check why 3d drawing is jumping a bit with mousewheel zoom while 2d drawing stays in place. this have to something with `POST_VIEW` and `POST_PIXEL` and can't be done anything with it. but verify that. --> well, weird, i guess drawing all 3d to offscreen and then drawing it all at `POST_PIXEL` would fix that, total overkill if you ask me..
# DONE: enable mouse wheel for booleans
# NOTTODO: what to do with tool properties and common mixin functions used in gesture drawing? -->> base + common always, as long as i know that, it will work and i have structured code.. in a way..
# NOTTODO: i think i will move common mixin to base tool, in some nicely structure way, but yes.. it is getting complicated and base cannot work without mixins anyway -->> base + common always, as long as i know that, it will work and i have structured code.. in a way..
# DONE: (3d only?) gestures fails to draw outside of surface, sometimes even throws error
# DONE: review gesture widgets drawing for use of surface matrices, it might not use it directly, but through cpmmon mixin methods
class SCATTER5_OT_manual_brush_tool_base(Operator, ):
    bl_idname = "scatter5.manual_brush_tool_base"
    bl_label = "Tool Base"
    bl_description = "Tool Base"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_base"
    tool_category = 'UNDEFINED'
    tool_label = "Tool Base"
    tool_domain = '3D'
    tool_gesture_definitions = {}
    tool_gesture_space = None
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    @classmethod
    def poll(cls, context, ):
        if(context.space_data is None):
            # NOTE: this can be None, if blender window is active but mouse is outside of it, like on second monitor ;)
            return False
        if(context.space_data.type != 'VIEW_3D'):
            return False
        
        if(context.mode != 'OBJECT'):
            return False
        
        # NOTE: some extra basic checks.. add more as they going to be needed
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
        
        return True
    
    @classmethod
    def description(cls, context, properties, ):
        # k = ToolKeyConfigurator.get_string_shortcut_for_tool(cls.tool_id)
        k = ToolKeyConfigurator.get_fancy_string_shortcut_for_tool(cls.tool_id)
        return "{} [{}]".format(cls.bl_description, k)
    
    # ------------------------------------------------------------------ screen layout utilities >>>
    
    def _in_region(self, mouse_x, mouse_y, region, ):
        x = region.x
        y = region.y
        w = region.width
        h = region.height
        if(mouse_x > x and mouse_x < x + w):
            if(mouse_y > y and mouse_y < y + h):
                return True
        return False
    
    def _is_viewport(self, context, event, ):
        mx = event.mouse_x
        my = event.mouse_y
        
        region = None
        for a in context.screen.areas:
            if(a.type == 'VIEW_3D'):
                for r in a.regions:
                    if(r.type == 'WINDOW'):
                        ok = self._in_region(mx, my, r, )
                        if(not ok):
                            continue
                        region = r
        
        if(region is not None):
            if(region == context.region):
                return True
        
        return False
    
    def _is_3dview_other_regions(self, context, event, ):
        mx = event.mouse_x
        my = event.mouse_y
        
        region = None
        for a in context.screen.areas:
            if(a.type == 'VIEW_3D'):
                for r in a.regions:
                    if(r.type in ('TOOL_HEADER', 'HEADER', 'TOOLS', 'UI', 'HUD', )):
                        ok = self._in_region(mx, my, r, )
                        if(not ok):
                            continue
                        
                        if(a == self._invoke_area):
                            region = r
        
        if(region is not None):
            return True
        
        return False
    
    def _is_sidebar(self, context, event, ):
        mx = event.mouse_x
        my = event.mouse_y
        
        region = None
        for a in context.screen.areas:
            if(a.type == 'VIEW_3D'):
                for r in a.regions:
                    # if(r.type in ('TOOL_HEADER', 'HEADER', 'TOOLS', 'UI', 'HUD', )):
                    if(r.type in ('UI', )):
                        ok = self._in_region(mx, my, r, )
                        if(not ok):
                            continue
                        
                        if(a == self._invoke_area):
                            region = r
        
        if(region is not None):
            return True
        
        return False
    
    def _is_asset_browser(self, context, event, ):
        mx = event.mouse_x
        my = event.mouse_y
        
        for a in context.screen.areas:
            if(a.type == 'FILE_BROWSER'):
                if(a.spaces[0].browse_mode != 'ASSETS'):
                    continue
                
                for r in a.regions:
                    ok = self._in_region(mx, my, r, )
                    if(ok):
                        # deny anything but window with assets icons and tools panel with collections..
                        if(r.type not in ('WINDOW', 'TOOLS', )):
                            return False
                        
                        return True
        
        return False
    
    def _is_debug_console_or_spreadsheet(self, context, event, ):
        mx = event.mouse_x
        my = event.mouse_y
        for a in context.screen.areas:
            if(a.type in ('CONSOLE', 'SPREADSHEET', )):
                for r in a.regions:
                    ok = self._in_region(mx, my, r, )
                    if(ok):
                        return True
        return False
    
    # ------------------------------------------------------------------ screen layout utilities <<<
    
    def _on_any_modal_event(self, context, event, ):
        # NOTE: this is only last resort refresh function, if it can be done without using it, please do so..
        pass
    
    # ------------------------------------------------------------------ widgets methods >>>
    
    # @verbose
    def _widgets_any_event(self, context, event, ):
        # NOTE: this might not be used at all.. idle/outside/press/move/release should cover every case.. at least all widget code will be at one place, and not split into two functions called at different times..
        pass
    
    # @verbose
    def _widgets_clear(self, context, event, ):
        ToolWidgets._cache[self.tool_id]['screen_components'] = []
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: sadly i need this special function because when lmb is down, only mouse events have some callbacks, so until i move mouse, no change in drawing occur, so this is specially called when any modifier key is pressed or released so event modifier property changes.
        # NOTE: this feels messy, say for example that i want something else to be in `cursor_components`, at the same time as modifiers, if i replace list of components, i will lose other elements of cursor, if i extend, every change will add to that another draw call, only i can loop through list primitives, identify those that belong to modifier and do something with it.. not great.. maybe add some id to each component? something that drawing function will ignore, but i can use for identifying? or some other separate callback for always refreshing elements? last time i did not like it. forgot why.
        pass
    
    # @verbose
    def _widgets_mouse_outside(self, context, event, ):
        self._widgets_clear(context, event, )
    
    # @verbose
    def _widgets_mouse_idle(self, context, event, ):
        pass
    
    # @verbose
    def _widgets_mouse_press(self, context, event, ):
        pass
    
    # @verbose
    def _widgets_mouse_move(self, context, event, ):
        pass
    
    # @verbose
    def _widgets_mouse_move_inbetween(self, context, event, ):
        pass
    
    # @verbose
    def _widgets_mouse_release(self, context, event, ):
        pass
    
    # ------------------------------------------------------------------ widgets methods <<<
    # ------------------------------------------------------------------ infobox methods <<<
    
    # NOTTODO: this is not common function, it is very specific because of tool ids. should it be defined outside of base class?
    # DONE: or each tool should define it own list of shortcuts? there is just a few exceptions.. lets let tool define basics on top and then just add generated gestures and undo
    def _infobox_collect_texts(self, ):
        h1 = "Manual Distribution Mode"
        h2 = self.bl_label
        
        ls = []
        
        if(hasattr(self, 'tool_infobox')):
            ls.extend(self.tool_infobox)
        
        def gesture(v, ):
            if(v['properties'] is None):
                return None
            
            k = v['type']
            n = v['properties']['name']
            f = v['flag']
            
            # NOTE: swap keys order for key combo string so they appear in logical order on screen
            # NOTE: command is irrelevant, i thought it might function as ctrl on mac (windows oskey is not usable in this way), but it would mess up thigs a lot
            ns = ['CTRL', 'ALT', 'SHIFT', 'COMMAND', ]
            bs = ToolKeyConfigurator.from_flag(f)
            bs = [bs[1], bs[2], bs[0], bs[3], ]
            
            r = "• {}: ".format(n)
            for i in range(4):
                if(bs[i]):
                    r = "{}{}+".format(r, ns[i])
            r = "{}{}".format(r, k)
            return r
        
        gls = [
            '__gesture_primary__',
            '__gesture_secondary__',
            '__gesture_tertiary__',
            '__gesture_quaternary__',
        ]
        
        if(any(n in self._configurator._db.keys() and self._configurator._db[n]['properties'] is not None for n in gls)):
            # separator if there is any gesture
            ls.append(None)
        
        for i, g in enumerate(gls):
            g = gesture(self._configurator._db[g])
            if(g):
                ls.append(g)
        
        # separator, it so common for all brushes
        ls.append(None)
        
        ls.append("• Undo/Redo: CTRL+(SHIFT)+Z")
        ls.append("• Exit: ESC")
        
        return h1, h2, ls
    
    # ------------------------------------------------------------------ infobox methods >>>
    # ------------------------------------------------------------------ action methods >>>
    
    def _action_any_private(self, context, event, ):
        if(event):
            if(event.is_tablet):
                self._pressure = event.pressure
                if(self._pressure <= 0.001):
                    # prevent zero pressure which might sometimes happen..
                    self._pressure = 0.001
    
    # @verbose
    def _action_timer_private(self, ):
        if(not ToolBox.tool):
            # ignore timer event is tool has been removed meanwhile..
            return
        if(not self._lmb):
            # ignore timers when mouse is not pressed..
            return
        
        self._action_any_private(None, None, )
        
        # NOTE: looks like timer are bugged (or, and it is more probable, i am doing something terribly wrong)
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '6' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '-11768' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '18800' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '18800' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '-21832' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '-21832' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '21800' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '13683' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '-11768' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '-11768' matches no enum in 'Event', '(null)', 'type'
        # WARN (bpy.rna): source/blender/python/intern/bpy_rna.c:1339 pyrna_enum_to_py: current value '-11768' matches no enum in 'Event', '(null)', 'type'
        # NOTE: notice negative indices.. so overflow happening. or event has been freed before passing to handler
        # NOTE: so, i got to handle that without context and event.. lets see..
        
        if(self._action_execute_on in ('TIMER', 'BOTH', )):
            bpy.app.timers.register(self._action_timer_private, first_interval=self._action_timer_interval, )
        
        self._status_action(None, None, )
        
        try:
            self._action_update()
        except Exception as e:
            # self._abort(context, event, )
            # NOTE: if i would restore ui on timer, blender will crash. so, timer errors report and print to console
            # panic(self._action_timer_private.__qualname__)
            
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
    
    # @verbose
    def _action_begin_private(self, context, event, ):
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('TIMER', 'BOTH', )):
            bpy.app.timers.register(self._action_timer_private, first_interval=self._action_timer_interval, )
        
        self._action_begin()
    
    # @verbose
    def _action_update_private(self, context, event, ):
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('MOUSEMOVE', 'BOTH', )):
            self._action_update()
    
    # @verbose
    def _action_update_inbetween_private(self, context, event, ):
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('MOUSEMOVE', 'BOTH', )):
            self._action_update_inbetween()
    
    # @verbose
    def _action_finish_private(self, context, event, ):
        self._action_any_private(context, event, )
        
        self._action_finish()
    
    # @verbose
    def _action_idle_private(self, context, event, ):
        # NOTE: no need for `_action_any_private` because it only updates `_pressure`, this is run when mouse is not pressed, so no pressure
        self._action_idle()
    
    # @verbose
    def _action_idle_inbetween_private(self, context, event, ):
        # NOTE: no need for `_action_any_private` because it only updates `_pressure`, this is run when mouse is not pressed, so no pressure
        self._action_idle_inbetween()
    
    # ------------------------------------------------------------------ action methods <<<
    # ------------------------------------------------------------------ action methods to override in subclasses >>>
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        pass
    
    # @verbose
    def _action_update_inbetween(self, ):
        # NOTE: here is the right spot to do actual brush work
        pass
    
    # @verbose
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        pass
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        pass
    
    # @verbose
    def _action_idle(self, ):
        # NOTE: if i need something to be updated while lmb is not pressd down (e.g. clone tool with sampled points)
        pass
    
    # @verbose
    def _action_idle_inbetween(self, ):
        # NOTE: if i need something to be updated while lmb is not pressd down (e.g. clone tool with sampled points)
        pass
    
    # ------------------------------------------------------------------ action methods to override in subclasses <<<
    # ------------------------------------------------------------------ mouse tracking (2d/3d) >>>
    
    _project_interpolate_normal_on_smooth_faces = True
    
    '''
    # NOTE: awfully slow.. what a pity.. and with lower sample counts it does not work as much..
    _project_interpolate_normal_by_sampling_around_cursor = False
    _project_interpolate_normal_by_sampling_around_cursor_samples = 100
    '''
    
    def _barycentric_weights(self, p, a, b, c, ):
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
    
    def _interpolate_smooth_face_normal(self, loc, nor, idx, ):
        if(loc is None):
            return nor
        if(self._bm is None):
            return nor
        if(not self._bm.is_valid):
            return nor
        
        f = self._bm.faces[idx]
        if(not f.smooth):
            return nor
        
        # smooth surface, iterpolate normal..
        vs = f.verts
        ws = self._barycentric_weights(loc, *[v.co.copy() for v in vs])
        ns = [v.normal.copy() for v in vs]
        n = Vector()
        for i, ni in enumerate(ns):
            # we want... a shrubbery! ni! ni! ni!
            n += ni * ws[i]
        n.normalize()
        return n
    
    '''
    def _interpolate_normal_by_sampling_around(self, loc, nor, ):
        if(loc is None):
            return loc, nor
        
        # rr = self._brush.radius
        rr = self._domain_aware_brush_radius()
        hh = rr * 0.5
        n = self._project_interpolate_normal_by_sampling_around_cursor_samples
        # a = np.radians(15)
        a = np.arctan(rr / hh)
        
        # random directions in cone
        rng = np.random.default_rng(seed=123, )
        z = rng.uniform(np.cos(a), 1.0, n, )
        t = rng.uniform(0.0, np.pi * 2, n, )
        ds = np.c_[np.sqrt(1 - z * z) * np.cos(t), np.sqrt(1 - z * z) * np.sin(t), z]
        ds = ds * -hh
        # shoot from 1.0 above surface
        origin = loc + (nor * hh)
        
        # TODO: i should define `_rotation_to` in base class, now it is part of common mixin, so while i have access to it, tool base is not useable without common mixin
        # rotate directions to align with normal
        q = self._rotation_to(Vector((0.0, 0.0, 1.0)), nor, )
        m = q.to_matrix().to_4x4()
        _, r, _ = m.decompose()
        m = np.array(r.to_matrix().to_4x4(), dtype=float, )
        ns = np.c_[ds, np.ones(len(ds), dtype=ds.dtype, )]
        ns = np.dot(m, ns.T)[0:4].T.reshape((-1, 4))
        directions = ns[:, :3]
        
        # debug.points(self._target, np.full((n, 3), origin, dtype=float, ), directions, )
        
        # ray cast around..
        max_dst = (1.0 / np.cos(a)) * 1.1
        ns = np.full((n, 3), nor, dtype=float, )
        for i in np.arange(n):
            _loc, _nor, _idx, _dst = self._bvh.ray_cast(origin, directions[i], max_dst, )
            if(_loc is not None):
                if(self._project_interpolate_normal_on_smooth_faces):
                    _nor = self._interpolate_smooth_face_normal(_loc, _nor, _idx, )
                ns[i] = _nor
        
        n = Vector((np.average(ns[:, 0], ), np.average(ns[:, 1], ), np.average(ns[:, 2], ), ))
        n.normalize()
        return n
    '''
    
    # @verbose
    def _project_mouse_to_surface(self, context, event, ):
        region = context.region
        rv3d = context.region_data
        coord = (event.mouse_region_x, event.mouse_region_y, )
        
        direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        loc, nor, idx, dst = self._bvh.ray_cast(origin, direction, )
        
        if(self._project_interpolate_normal_on_smooth_faces):
            nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
        
        '''
        if(self._project_interpolate_normal_by_sampling_around_cursor):
            nor = self._interpolate_normal_by_sampling_around(loc, nor, )
        '''
        
        # if(self._brush.use_normal_interpolation):
        if(self._get_prop_value('use_normal_interpolation')):
            nor = self._interpolate_normal_by_neighbouring_connected_faces(loc, nor, idx, dst, )
        
        return loc, nor, idx, dst
    
    # @verbose
    def _on_mouse_move(self, context, event, ):
        # 2d mouse current coordinates
        mouse = Vector((event.mouse_x, event.mouse_y, ))
        if(self._mouse_2d_prev.to_tuple() != mouse.to_tuple()):
            # if coordinates changed from last update, swap old to prev and set current
            self._mouse_2d_prev = self._mouse_2d
            self._mouse_2d = mouse
            # search for prev coordinate that is further than minimal distance
            prev = None
            for i in reversed(range(len(self._mouse_2d_path))):
                a = self._mouse_2d_path[i]
                b = mouse
                d = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
                if(d >= self._mouse_2d_direction_minimal_distance):
                    prev = self._mouse_2d_path[i]
                    break
            # and calculate direction from it. this will smooth direction changes
            if(prev is not None):
                self._mouse_2d_prev = prev
                n = self._mouse_2d - self._mouse_2d_prev
                n.normalize()
                self._mouse_2d_direction = n
            # and append to path history
            self._mouse_2d_path.append(mouse)
            self._mouse_2d_path_direction.append(self._mouse_2d_direction)
        # and store region coordinates, might be needed as well..
        self._mouse_2d_region_prev = self._mouse_2d_region
        self._mouse_2d_region = Vector((event.mouse_region_x, event.mouse_region_y, ))
        rdiff = self._mouse_2d - self._mouse_2d_region
        self._mouse_2d_region_prev = self._mouse_2d_prev - rdiff
        
        # 3d mouse
        # NOTE: 3d mouse (unlike 2d) can have `None` values (i.e. mouse is not above surface), so test for it before using..
        # first project to surface
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        # store raw values
        self._mouse_3d_loc = loc
        self._mouse_3d_nor = nor
        self._mouse_3d_idx = idx
        self._mouse_3d_dst = dst
        # now the mouse tracking part..
        if(loc is not None):
            # if projection is successful
            if(self._mouse_3d is None):
                # and nothing is set yet, set it
                self._mouse_3d = loc
            if(loc != self._mouse_3d):
                # if location changed (mouse moved from last run) calculate distance traveled (in 3d)
                a = loc
                b = self._mouse_3d
                d = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
                # and if distance is larger than minimal distance
                if(d > self._mouse_3d_direction_minimal_distance):
                    # add another step to paths
                    self._mouse_3d_path.append(loc)
                    self._mouse_3d_path_direction.append(self._mouse_3d_direction)
                    # set prev
                    self._mouse_3d_prev = self._mouse_3d
                    self._mouse_3d = loc
                    # and if i have current and prev together
                    if(self._mouse_3d is not None and self._mouse_3d_prev is not None):
                        # calculate direction from them
                        n = self._mouse_3d - self._mouse_3d_prev
                        n.normalize()
                        self._mouse_3d_direction = n
                    else:
                        # or set to none because i can't determine it
                        self._mouse_3d_direction = None
                else:
                    pass
            else:
                pass
        else:
            # unsuccessful projection, set prev and the rest to none..
            self._mouse_3d_prev = self._mouse_3d
            self._mouse_3d = None
            self._mouse_3d_direction = None
        
        # put current values to interpolated so they are not None and can be used
        self._mouse_2d_direction_interpolated = self._mouse_2d_direction
        self._mouse_3d_direction_interpolated = self._mouse_3d_direction
        # if(self._brush.use_direction_interpolation):
        if(self._get_prop_value('use_direction_interpolation')):
            # run interpolation if needed.. will update values with true interpolated ones..
            # TODO: should i split `use_direction_interpolation` to 2d and 3d? average at max 10 vectors.. no big deal. but measure that
            self._interpolate_mouse_movement_direction_2d()
            self._interpolate_mouse_movement_direction_3d()
        
        # track active surface from info i've for already..
        self._mouse_active_surface_uuid = None
        self._mouse_active_surface_name = None
        self._mouse_active_surface_matrix = None
        if(self._mouse_3d is not None):
            u = ToolSessionCache._cache['arrays']['f_surface'][self._mouse_3d_idx]
            # numpy arrays are not hashable, but here i am getting just a single integer value
            self._mouse_active_surface_uuid = int(u)
            self._mouse_active_surface_name = self._surfaces_db[self._mouse_active_surface_uuid]
            # NOTE: lets pretend object will not suddenly disappear.. but get new reference to it, so undo/redo will not interfere. i am not sure when undo/redo handler is run.. i think before this.. but be safe here
            o = bpy.data.objects.get(self._mouse_active_surface_name)
            self._mouse_active_surface_matrix = o.matrix_world.copy()
    
    # @verbose
    def _on_mouse_move_inbetween(self, context, event, ):
        # NOTE: if i ever need calculate something on INBETWEEN_MOUSEMOVE, but for performance reasons, lets stick with MOUSEMOVE only
        if(self._mouse_tracking_inbetween):
            self._on_mouse_move(context, event, )
    
    def _interpolate_normal_by_neighbouring_connected_faces(self, loc, nor, idx, dst, ):
        if(loc is None):
            return nor
        
        # DONE: put this into brush setting, normal interpolation on/off and portion of radius as factor 0-1
        # TODO: so, i am interpolating normal. right now it is used for widget drawing and brush effects. i think it will benefit both at the same time. if it is exposed to user. so no need to split draw and effect normals. drawing on bumpy surface without interpolation result in weird directions, while it is correct, it is not wahat user usually wants. for vegetation it is not good, for rocks it is ok with or without interpolation. make sure that for flat shaded faces it still can be turned off so we have same effect on those as before.
        
        # NOTE: all brushes should have radius defined, even when they are fixed size. in that case it is 1.0 in world units
        r = self._domain_aware_brush_radius()
        
        if(self._get_prop_value('radius_pressure')):
            r = r * self._pressure
        r = r * self._get_prop_value('normal_interpolation_radius_factor')
        
        if(r == 0.0):
            # will result in zero vector, so no need to continue. zero length normal will mess up everything anyway
            return nor
        
        ls = self._bvh.find_nearest_range(loc, r, )
        if(len(ls) <= 1):
            # nothing to interpolate, single face under cursor
            return nor
        
        # TODO: maybe also weight by distance? or at least main normal to contribute more to interpolated normal? maybe i am complicating too much..
        # TODO: or at least some sort of max number of faces? for example 100 faces at max? but if i cache normals, it is not that important..
        fii = [i for l, n, i, d in ls]
        
        # DONE: read flattened triangulated mesh (that one used for bmesh) to arrays, vertices+normals, triangles+normals, maybe everything else as well..
        # DONE: then use it here for example..
        
        ns = self._cache_fs_no[np.array(fii, dtype=int, )]
        
        nor = Vector((np.average(ns[:, 0], ), np.average(ns[:, 1], ), np.average(ns[:, 2], ), ))
        nor.normalize()
        
        return nor
    
    def _interpolate_mouse_movement_direction_3d(self, ):
        if(not self._get_prop_value('use_direction_interpolation')):
            # turned off
            return
        if(self._get_prop_value('direction_interpolation_steps') == 0):
            # zero steps, no interpolation
            return
        
        ns = []
        for v in reversed(self._mouse_3d_path_direction):
            if(v is None):
                # any None breaks it. most likely it means mouse left surface, so it is not tracked
                break
            if(v.length == 0.0):
                # could be zero length? i don't want such vectors
                break
            ns.append(v)
            if(len(ns) >= self._get_prop_value('direction_interpolation_steps')):
                break
        if(not len(ns)):
            # i have no steps to work with
            return
        
        a = np.array(ns, dtype=float, )
        
        # NOTE: some wights to it, first in array is most important (because i go over reversed history), last will contrubute the least
        w = np.linspace(1.0, 1.0 / self._get_prop_value('direction_interpolation_steps'), num=len(a), endpoint=True, retstep=False, dtype=float, axis=0, )
        a = a * w.reshape(-1, 1)
        
        dx = np.average(a[:, 0])
        dy = np.average(a[:, 1])
        dz = np.average(a[:, 2])
        d = Vector((dx, dy, dz))
        d.normalize()
        
        self._mouse_3d_direction_interpolated = d
    
    def _interpolate_mouse_movement_direction_2d(self, ):
        if(not self._get_prop_value('use_direction_interpolation')):
            # turned off
            return
        if(self._get_prop_value('direction_interpolation_steps') == 0):
            # zero steps, no interpolation
            return
        
        ns = []
        for v in reversed(self._mouse_2d_path_direction):
            if(v is None):
                # any None breaks it. most likely it means mouse left surface, so it is not tracked
                break
            if(v.length == 0.0):
                # could be zero length? i don't want such vectors
                break
            ns.append(v)
            if(len(ns) >= self._get_prop_value('direction_interpolation_steps')):
                break
        if(not len(ns)):
            # i have no steps to work with
            return
        
        a = np.array(ns, dtype=float, )
        
        # NOTE: some wights to it, first in array is most important (because i go over reversed history), last will contrubute the least
        w = np.linspace(1.0, 1.0 / self._get_prop_value('direction_interpolation_steps'), num=len(a), endpoint=True, retstep=False, dtype=float, axis=0, )
        a = a * w.reshape(-1, 1)
        
        dx = np.average(a[:, 0])
        dy = np.average(a[:, 1])
        d = Vector((dx, dy))
        d.normalize()
        
        self._mouse_2d_direction_interpolated = d
    
    # ------------------------------------------------------------------ mouse tracking (2d/3d) <<<
    # ------------------------------------------------------------------ key events >>>
    
    # @verbose
    def _on_any_key_press(self, context, event, ):
        pass
    
    # @verbose
    def _on_any_key_repeat(self, context, event, ):
        pass
    
    # @verbose
    def _on_any_key_release(self, context, event, ):
        pass
    
    def _is_key_event(self, context, event, ):
        types = {
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
            'LEFT_CTRL', 'LEFT_ALT', 'LEFT_SHIFT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY',
            'APP', 'GRLESS', 'ESC', 'TAB', 'RET', 'SPACE', 'LINE_FEED', 'BACK_SPACE', 'DEL',
            'SEMI_COLON', 'PERIOD', 'COMMA', 'QUOTE', 'ACCENT_GRAVE', 'MINUS', 'PLUS', 'SLASH', 'BACK_SLASH', 'EQUAL', 'LEFT_BRACKET', 'RIGHT_BRACKET',
            'LEFT_ARROW', 'DOWN_ARROW', 'RIGHT_ARROW', 'UP_ARROW',
            'NUMPAD_0', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9',
            'NUMPAD_PERIOD', 'NUMPAD_SLASH', 'NUMPAD_ASTERIX', 'NUMPAD_MINUS', 'NUMPAD_ENTER', 'NUMPAD_PLUS',
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 'F19', 'F20', 'F21', 'F22', 'F23', 'F24',
            'PAUSE', 'INSERT', 'HOME', 'PAGE_UP', 'PAGE_DOWN', 'END',
            'MEDIA_PLAY', 'MEDIA_STOP', 'MEDIA_FIRST', 'MEDIA_LAST',
            # 'TEXTINPUT', 'WINDOW_DEACTIVATE',
        }
        if(event.type in types):
            return True
        return False
    
    def _modal_shortcuts(self, context, event, ):
        # # is called from `_modal`, after all else is handled (apart from exit), any custom keys can be put here..
        # if(event.type in {'F', } and event.value == 'PRESS'):
        #     print('F on')
        # elif(event.type in {'F', } and event.value == 'RELEASE'):
        #     print('F off')
        pass
        
        '''
        # NOTE: test tool panic abort on error
        if(event.type in {'P', } and event.value == 'PRESS'):
            try:
                1 / 0
            except Exception as e:
                panic(self._modal_shortcuts.__qualname__)
        # NOTE: test tool outside abort
        if(event.type in {'A', } and event.value == 'PRESS'):
            if(ToolBox.reference is not None):
                try:
                    ToolBox.reference._abort(context, event, )
                except Exception as e:
                    # NOTE: panic!
                    panic(self._modal_shortcuts.__qualname__)
        # NOTE: test deinit (whole addon is disabled)
        if(event.type in {'D', } and event.value == 'PRESS'):
            deinit()
        '''
        
        if(debug.debug_mode()):
            # NOTE: i'm so bloody lazy, oh what a effort to move mouse and click toolbar icon, it is exhausting.. there has to be something more comfortable
            if(event.type in ('LEFT_BRACKET', 'RIGHT_BRACKET', ) and event.value == 'PRESS'):
                # get toolbar items
                from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
                ls = []
                tb = VIEW3D_PT_tools_active._tools['OBJECT']
                for td in tb:
                    if(td is not None):
                        ls.append(td.idname)
                # get next or previous `tool_id`
                l = len(ls)
                i = ls.index(self.tool_id)
                if(event.type == 'LEFT_BRACKET'):
                    # prev
                    n = i - 1
                    if(n < 0):
                        n = l - 1
                else:
                    # next
                    n = i + 1
                    if(n >= l):
                        n = 0
                
                # # cancel current operator and run new..
                # idname = get_tool_class(ls[n]).bl_idname
                # n = idname.split('.', 1)
                # op = getattr(getattr(bpy.ops, n[0]), n[1])
                # if(op.poll()):
                #     self._abort(context, event, )
                #     op('INVOKE_DEFAULT', )
                #     return {'CANCELLED'}
                
                # select it in toolbar and let the rest be done automagically.. that's what i call luxury
                bpy.ops.wm.tool_set_by_id(name=ls[n])
    
    # ------------------------------------------------------------------ key events <<<
    # ------------------------------------------------------------------ undo/redo reference handling >>>
    
    @verbose
    def _undo_redo_callback(self, context, event, ):
        # NOTE: get correct references after undo/redo
        self._surfaces = [bpy.data.objects.get(n) for n in self._surfaces_names]
        self._target = bpy.data.objects.get(self._target_name)
        self._props = bpy.context.scene.scatter5.manual
        self._brush = getattr(self._props, self._brush_props_name)
    
    # ------------------------------------------------------------------ undo/redo reference handling <<<
    # ------------------------------------------------------------------ status text >>>
    
    # TODO: `context` and `event` will be `None` in timer brushes on timer action, should they be removed? so i am not tempted to use for some info?
    def _status_action(self, context, event, ):
        # t = "Action text.."
        # bpy.context.workspace.status_text_set(text=t, )
        
        self._status_idle(context, event, )
    
    # TODO: `context` and `event` will be `None` in timer brushes on timer action, should they be removed? so i am not tempted to use for some info?
    def _status_idle(self, context, event, ):
        # t = "Idle text.."
        # bpy.context.workspace.status_text_set(text=t, )
        
        try:
            n = self._emitter.scatter5.get_psy_active().name
            l = len(self._target.data.vertices)
            a = np.sum(self._get_target_active_mask())
            t = 'Active System: "{}", Instances: {}, Orphans: {}'.format(n, a, l - a, )
        except Exception as e:
            t = None
        
        bpy.context.workspace.status_text_set(text=t, )
    
    # ------------------------------------------------------------------ status text <<<
    # ------------------------------------------------------------------ gesture >>>
    
    @verbose
    def _gesture_begin(self, context, event, ):
        if(self._gesture_data['properties']['widget'] == 'FUNCTION_CALL'):
            fn = self._gesture_data['properties']['function']
            args = self._gesture_data['properties']['arguments']
            getattr(self, fn)(**args)
            
            self._gesture_finish(context, event, )
            self._gesture_mode = False
            self._gesture_data = None
            
            return
        
        p = self._gesture_data['properties']['property']
        
        if(self._gesture_data['properties']['property'] == 'radius' and self._get_prop_value('radius_units') == 'VIEW'):
            self._gesture_data['properties']['property'] = 'radius_px'
            s = self._radius_px_to_world(self._context_region, self._context_region_data, self._mouse_3d, 1, )
            self._gesture_data['properties']['change'] /= s
            self._gesture_data['properties']['change_wheel'] /= s
            
            p = self._gesture_data['properties']['property']
            v = self._get_prop_value(p)
        else:
            v = self._get_prop_value(p)
        
        m = (event.mouse_region_x, event.mouse_region_y, )
        self._gesture_data['_property'] = p
        
        if(self._gesture_data['properties']['datatype'] in ('vector', )):
            # vector have to be copied to keep initial values
            self._gesture_data['_inital_property_value'] = v.copy()
        else:
            self._gesture_data['_inital_property_value'] = v
        
        self._gesture_data['_mouse_2d'] = m
        self._gesture_data['_updated_property_value'] = v
        
        loc, nor, _, _ = self._project_mouse_to_surface(context, event, )
        self._gesture_data['_mouse_3d_loc'] = loc
        self._gesture_data['_mouse_3d_nor'] = nor
        
        # number of wheel events so far, they are added or subtracted according to wheel direction
        self._gesture_data['_mouse_wheel'] = 0
        # this is used if min or max value is detected in property so i dan't have "blank" wheel steps
        self._gesture_data['_mouse_wheel_validated'] = 0
        
        if(self._gesture_data['properties']['widget'] in ('LENGTH_3D', )):
            # NOTE: length uses 3d world sizes, but is drawn in 2d on screen..
            # NOTE: lets calculate conversion factor..
            loc = self._gesture_data['_mouse_3d_loc']
            region = context.region
            rv3d = context.region_data
            loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
            n_2d = loc_2d + Vector((1, 0, ))
            n_2d_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, n_2d, loc)
            l = Vector(n_2d_3d - loc).length
            self._gesture_data['_updated_property_value_change_scale'] = l
    
    # @verbose
    def _gesture_update(self, context, event, ):
        # use only left <--> right movement for setting value
        c = ((event.mouse_region_x - self._gesture_data['_mouse_2d'][0]) / self._gesture_data['properties']['change_pixels']) * self._gesture_data['properties']['change']
        
        if(self._gesture_data['properties']['widget'] in ('RADIUS_3D', 'RADIUS_2_5D', )):
            if(self._props.use_radius_exp_scale):
                if(self._get_prop_value('radius_units') == 'VIEW'):
                    s = self._radius_px_to_world(self._context_region, self._context_region_data, self._mouse_3d, 1, )
                    c *= s
                
                if(c < 0.0):
                    c = -np.expm1(abs(c))
                else:
                    c = np.expm1(abs(c))
                
                if(self._get_prop_value('radius_units') == 'VIEW'):
                    c /= s
        
        # # DONE: include this is all gesture definitions
        w = self._gesture_data['properties']['change_wheel']
        
        if(event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', }):
            if(event.type == 'WHEELUPMOUSE'):
                self._gesture_data['_mouse_wheel'] -= 1 * w
            else:
                self._gesture_data['_mouse_wheel'] += 1 * w
        
        if(self._gesture_data['properties']['widget'] in ('LENGTH_3D', )):
            # length need to convert change value
            c = Vector(Vector(self._gesture_data['_mouse_2d']) - Vector((event.mouse_region_x, event.mouse_region_y, ))).length
            c *= self._gesture_data['_updated_property_value_change_scale']
        
        if(self._gesture_data['properties']['widget'] in ('LENGTH_3D', )):
            # length need to convert change value mouse wheel steps in different way as well
            c += (self._gesture_data['_mouse_wheel'] * self._gesture_data['properties']['change']) * self._gesture_data['_updated_property_value_change_scale']
        else:
            c += self._gesture_data['_mouse_wheel'] * self._gesture_data['properties']['change']
        
        if(self._gesture_data['properties']['datatype'] in ('vector', )):
            v = Vector(self._gesture_data['_inital_property_value'])
            v.x += c
            v.y += c
            v.z += c
            # set value, let it sanitize
            self._set_prop_value(self._gesture_data['_property'], v, )
            # Vector have to be copied.. this returns just reference..
            vv = Vector(self._get_prop_value(self._gesture_data['_property']))
            
            # validate mouse wheel steps, if min or max on property is reached, use old value for steps, if not, update with current
            # NOTE: round to 3 decimal places, that's what i use for display on screen, so lets ignore all past 3 decimals
            # NOTE: use vector length so i don't have to compare all axes, wheel is incrementing uniformly anyway..
            if(round(vv.length, 3) > round(v.length, 3)):
                # min is reached, reset mouse wheel
                self._gesture_data['_mouse_wheel'] = self._gesture_data['_mouse_wheel_validated']
            elif(round(vv.length, 3) < round(v.length, 3)):
                # max is reached, reset mouse wheel
                self._gesture_data['_mouse_wheel'] = self._gesture_data['_mouse_wheel_validated']
            else:
                self._gesture_data['_mouse_wheel_validated'] = self._gesture_data['_mouse_wheel']
            
            self._gesture_data['_updated_property_value'] = vv
        elif(self._gesture_data['properties']['datatype'] in ('bool', )):
            # DONE: enable mouse wheel for booleans
            c = event.mouse_region_x - self._gesture_data['_mouse_2d'][0]
            
            if(event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', }):
                if(event.type == 'WHEELUPMOUSE'):
                    c = -self._gesture_data['properties']['change_pixels'] + 1
                else:
                    c = self._gesture_data['properties']['change_pixels'] + 1
            
            v = self._gesture_data['_inital_property_value']
            if(abs(c) > self._gesture_data['properties']['change_pixels']):
                if(c > 0):
                    v = True
                elif(c < 0):
                    v = False
                else:
                    v = v
            self._set_prop_value(self._gesture_data['_property'], v, )
            vv = self._get_prop_value(self._gesture_data['_property'])
            self._gesture_data['_updated_property_value'] = vv
        elif(self._gesture_data['properties']['datatype'] in ('enum', )):
            c = event.mouse_region_x - self._gesture_data['_mouse_2d'][0]
            
            if(event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', }):
                if(event.type == 'WHEELUPMOUSE'):
                    c = -self._gesture_data['properties']['change_pixels'] + 1
                else:
                    c = self._gesture_data['properties']['change_pixels'] + 1
            
            options = self._get_prop_group(self._gesture_data['_property']).bl_rna.properties[self._gesture_data['_property']].enum_items[:]
            db = {}
            for o in options:
                db[o.identifier] = o.value
            
            # WATCH: this is only for two option enum, that is what i need now, if i ever need more options, then i will change it to any length enum. basically pie menu..
            v = self._gesture_data['_inital_property_value']
            v = db[v]
            if(abs(c) > self._gesture_data['properties']['change_pixels']):
                if(c > 0):
                    v = 1
                elif(c < 0):
                    v = 0
                else:
                    v = v
            
            v = list(db.keys())[list(db.values()).index(v)]
            
            self._set_prop_value(self._gesture_data['_property'], v, )
            vv = self._get_prop_value(self._gesture_data['_property'])
            self._gesture_data['_updated_property_value'] = vv
        else:
            v = self._gesture_data['_inital_property_value'] + c
            
            if(self._gesture_data['properties']['widget'] in ('LENGTH_3D', )):
                v = c
            
            if(self._gesture_data['properties']['datatype'] in ('int', )):
                v = int(v)
            if(self._gesture_data['properties']['datatype'] in ('float', )):
                v = float(v)
            
            self._set_prop_value(self._gesture_data['_property'], v, )
            
            # now type should be ok
            vv = self._get_prop_value(self._gesture_data['_property'])
            
            # validate mouse wheel steps, if min or max on property is reached, use old value for steps, if not, update with current
            # NOTE: round to 3 decimal places, that's what i use for display on screen, so lets ignore all past 3 decimals
            if(round(vv, 3) > round(v, 3)):
                # min is reached, reset mouse wheel
                self._gesture_data['_mouse_wheel'] = self._gesture_data['_mouse_wheel_validated']
            elif(round(vv, 3) < round(v, 3)):
                # max is reached, reset mouse wheel
                self._gesture_data['_mouse_wheel'] = self._gesture_data['_mouse_wheel_validated']
            else:
                self._gesture_data['_mouse_wheel_validated'] = self._gesture_data['_mouse_wheel']
            
            self._gesture_data['_updated_property_value'] = vv
    
    @verbose
    def _gesture_finish(self, context, event, ):
        if(self._gesture_data['properties']['widget'] != 'FUNCTION_CALL'):
            # NOTE: push undo state so after draw + undo you keep changes to property
            msg = self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value'])
            bpy.ops.ed.undo_push(message=msg, )
        
        # NOTE: update mouse tracking, if user does not move mouse after gesture is done, it will still have values before gesture started
        self._on_mouse_move(context, event, )
    
    @verbose
    def _gesture_cancel(self, context, event, ):
        v = self._gesture_data['_inital_property_value']
        
        self._set_prop_value(self._gesture_data['_property'], v)
        
        # NOTE: update mouse tracking, if user does not move mouse after gesture is done, it will still have values before gesture started
        self._on_mouse_move(context, event, )
    
    # FIXMENOT: `_gesture_widget` is using functions from legacy mixin (moved from legacy to common mixin, but still, it should be standalone..) -->> as long as i use common props, i should be safe
    # FIXMENOT: `_gesture_widget` is using properties from brushes not defined at this state -->> as long as i use common props, i should be safe
    # DONE: finish `LENGTH` widgets, current state is unsatisfactory -->> new variant, better than before
    # DONE: some widget for lasso density
    # DONE: some widget for speed in random rotation, strength like with -1 to 1 range
    # DONE: make difference between 3d and 2d (not yet implemented, but will be needed) widgets. _3D or _2D suffixes will be enough
    # @verbose
    def _gesture_widget(self, context, event, ):
        if(not self._gesture_mode):
            # NOTE: in case gesture finished at begin state (then it should flip `_gesture_mode` to False by itself..)
            return
        
        widget = self._gesture_data['properties']['widget']
        ls = []
        
        if(widget == 'RADIUS_3D' or widget == 'RADIUS_2_5D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_3d_loc']
            
            if(self._get_prop_value('radius_units') == 'VIEW'):
                s = self._radius_px_to_world(self._context_region, self._context_region_data, self._mouse_3d, 1, )
                vi *= s
                vu *= s
            
            if(loc is not None):
                nor = self._gesture_data['_mouse_3d_nor']
                
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, vi, )
                if(widget == 'RADIUS_2_5D'):
                    mi = mt @ ms
                else:
                    mi = mt @ mr @ ms
                
                ms = self._widgets_compute_surface_matrix_scale_component_3d(vu, )
                if(widget == 'RADIUS_2_5D'):
                    mu = mt @ ms
                else:
                    mu = mt @ mr @ ms
                
                if(self._get_prop_value('radius_units') == 'VIEW'):
                    tt = self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], int(self._gesture_data['_updated_property_value']))
                else:
                    tt = self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value'])
                
                ls = [
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    {
                        'function': 'circle_fill_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mu,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': tt,
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'STRENGTH_3D' or widget == 'STRENGTH_2_5D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            # FIXMENOT: property from brush is used
            r = self._domain_aware_brush_radius()
            
            loc = self._gesture_data['_mouse_3d_loc']
            if(loc is not None):
                r = self._widgets_compute_minimal_widget_size_for_radius_3d(context.region, context.region_data, loc, r, )
                vi = self._gesture_data['_inital_property_value'] * r
                vu = self._gesture_data['_updated_property_value'] * r
                
                nor = self._gesture_data['_mouse_3d_nor']
                
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, vi, )
                if(widget == 'STRENGTH_2_5D'):
                    mi = mt @ ms
                else:
                    mi = mt @ mr @ ms
                
                ms = self._widgets_compute_surface_matrix_scale_component_3d(vu, )
                if(widget == 'STRENGTH_2_5D'):
                    mu = mt @ ms
                else:
                    mu = mt @ mr @ ms
                
                ms = self._widgets_compute_surface_matrix_scale_component_3d(r, )
                if(widget == 'STRENGTH_2_5D'):
                    mmax = mt @ ms
                else:
                    mmax = mt @ mr @ ms
                
                ls = [
                    # max circle (as radius)
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mmax,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    # initial value
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    # update value
                    {
                        'function': 'circle_fill_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mu,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'ANGLE_3D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            # FIXMENOT: property from brush is used
            r = self._domain_aware_brush_radius()
            
            hard_min = self._get_prop_group(self._gesture_data['_property']).bl_rna.properties[self._gesture_data['_property']].hard_min
            hard_max = self._get_prop_group(self._gesture_data['_property']).bl_rna.properties[self._gesture_data['_property']].hard_max
            
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_3d_loc']
            if(loc is not None):
                c = view3d_utils.location_3d_to_region_2d(context.region, context.region_data, loc, )
                r = self._widgets_compute_minimal_widget_size_for_radius_2d(context.region, context.region_data, loc, r, )
                
                tn = self._gesture_data['properties']['name']
                tv = np.degrees(self._gesture_data['_updated_property_value'])
                tt = self._gesture_data['properties']['text'].format(tn, tv)
                tt = "{}°".format(tt)
                
                ls = [
                    # initial value
                    {
                        'function': 'wedge_thick_outline_2d',
                        'arguments': {
                            'center': c,
                            'radius': r,
                            'angle': vi,
                            'offset': 0.0,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    {
                        'function': 'wedge_fill_2d',
                        'arguments': {
                            'center': c,
                            'radius': r,
                            'angle': vi,
                            'offset': 0.0,
                            'steps': self._theme._circle_steps,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    # updated value
                    {
                        'function': 'wedge_thick_outline_2d',
                        'arguments': {
                            'center': c,
                            'radius': r,
                            'angle': vu,
                            'offset': 0.0,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': tt,
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'COUNT_3D'):
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_3d_loc']
            if(loc is not None):
                nor = self._gesture_data['_mouse_3d_nor']
                mt = Matrix.Translation(loc)
                mr = self._direction_to_rotation(nor).to_matrix().to_4x4()
                
                # FIXMENOT: property from brush is used
                r = self._domain_aware_brush_radius()
                
                ms = Matrix(((r, 0.0, 0.0, 0.0), (0.0, r, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                cm = mt @ mr @ ms
                
                dm = mt @ mr @ ms
                
                rng_r = np.random.default_rng(seed=123, )
                rng_t = np.random.default_rng(seed=456, )
                
                r = 1.0
                n = vu
                # s = r / 100
                s = r / 25 * self._theme._ui_scale
                
                def cross(x, y, offset, ):
                    vs = (
                        (x - s, y, 0.0, ),
                        (x + s, y, 0.0, ),
                        (x, y - s, 0.0, ),
                        (x, y + s, 0.0, ),
                    )
                    vs = np.array(vs, dtype=np.float32, )
                    indices = (
                        (0, 1),
                        (2, 3),
                    )
                    indices = np.array(indices, dtype=np.int32, )
                    indices = indices + offset
                    return vs, indices
                
                r = r * np.sqrt(rng_r.random(n, ))
                theta = rng_t.random(n, ) * 2 * np.pi
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                
                vs = []
                indices = []
                c = 0
                for i in range(n):
                    a, b = cross(x[i], y[i], c, )
                    c += len(a)
                    vs.append(a)
                    indices.append(b)
                
                vs = np.concatenate(vs, )
                indices = np.concatenate(indices, )
                
                woc = self._theme._outline_color
                wfc = self._theme._fill_color
                
                ls = [
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': cm,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    {
                        'function': 'multiple_thick_lines_3d',
                        'arguments': {
                            'vertices': vs,
                            'indices': indices,
                            'matrix': dm,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'LENGTH_3D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_3d_loc']
            
            if(loc is not None):
                # matrices for updated
                nor = self._gesture_data['_mouse_3d_nor']
                mt = Matrix.Translation(loc)
                mr = self._direction_to_rotation(nor).to_matrix().to_4x4()
                ms = Matrix(((vu, 0.0, 0.0, 0.0), (0.0, vu, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                model = mt @ mr @ ms
                view = context.region_data.view_matrix
                projection = context.region_data.window_matrix
                # unit circle points
                steps = self._theme._circle_steps
                vs = np.zeros((steps, 3), dtype=float, )
                angstep = 2 * np.pi / steps
                a = np.arange(steps, dtype=int, )
                center = [0.0, 0.0, ]
                radius = 1.0
                vs[:, 0] = center[0] + (np.sin(a * angstep) * radius)
                vs[:, 1] = center[1] + (np.cos(a * angstep) * radius)
                # transform to screen space
                vs = np.c_[vs, np.ones(len(vs), dtype=vs.dtype, )]
                vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
                vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
                vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
                x = vs[:, 0]
                y = vs[:, 1]
                z = vs[:, 1]
                w = vs[:, 3]
                x_ndc = x / w
                y_ndc = y / w
                z_ndc = z / w
                x2d = (x_ndc + 1.0) / 2.0
                y2d = (y_ndc + 1.0) / 2.0
                # # NOTE: do i need some depth? lets go with zeros for now
                # z = np.zeros(len(vs), dtype=float, )
                # vs2d = np.c_[x2d, y2d, z]
                vs2d = np.c_[x2d, y2d]
                # # and normalize path from pixels to 0.0-1.0
                # vertices2d = np.zeros((len(vertices), 2), dtype=float, )
                # vertices2d[:, 0] = vertices[:, 0] * (1.0 / self._context_region.width)
                # vertices2d[:, 1] = vertices[:, 1] * (1.0 / self._context_region.height)
                # to pixel coordinates
                vs2d[:, 0] = vs2d[:, 0] * context.region.width
                vs2d[:, 1] = vs2d[:, 1] * context.region.height
                # fabricate segments indices
                i = np.arange(steps)
                indices = np.c_[i, np.roll(i, -1), ]
                # intersect segments with origin > mouse line
                hit = None
                c = Vector(self._gesture_data['_mouse_2d'])
                d = Vector((event.mouse_region_x, event.mouse_region_y, ))
                n = d - c
                n.normalize()
                # NOTE: move is something ridiculous
                d = c + (n * 10 ** 6)
                c = np.array(c, dtype=float, )
                d = np.array(d, dtype=float, )
                for i, segment in enumerate(indices):
                    a, b = vs2d[segment]
                    hit = mathutils.geometry.intersect_line_line_2d(a, b, c, d)
                    if(hit):
                        break
                
                # initital matrix
                ms = Matrix(((vi, 0.0, 0.0, 0.0), (0.0, vi, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mi = mt @ mr @ ms
                # updated matrix
                ms = Matrix(((vu, 0.0, 0.0, 0.0), (0.0, vu, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mu = mt @ mr @ ms
                
                di = Vector(self._gesture_data['_mouse_2d'])
                du = Vector((event.mouse_region_x, event.mouse_region_y, ))
                
                ls = [
                    # initital circle
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    {
                        'function': 'circle_fill_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    # initial dot
                    {
                        'function': 'dot_shader_2_2d',
                        'arguments': {
                            'center': di,
                            'diameter': self._theme._fixed_center_dot_radius * 2,
                            'color': woc,
                        },
                    },
                    # updated circle
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mu,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # updated dot
                    {
                        'function': 'dot_shader_2_2d',
                        'arguments': {
                            'center': du,
                            'diameter': self._theme._fixed_center_dot_radius * 2,
                            'color': woc,
                        },
                    },
                    # initial to updated connection
                    {
                        'function': 'thick_line_2d',
                        'arguments': {
                            'a': di,
                            'b': du,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        },
                    },
                ]
                
                if(hit):
                    ls.extend([
                        # initial to intersection connection
                        {
                            'function': 'thick_line_2d',
                            'arguments': {
                                'a': di,
                                'b': hit,
                                'color': woc,
                                'thickness': self._theme._outline_thickness,
                            },
                        },
                        # intersection dot
                        {
                            'function': 'dot_shader_2_2d',
                            'arguments': {
                                'center': hit,
                                # 'diameter': self._theme._fixed_center_dot_radius * 2,
                                'diameter': self._theme._fixed_center_dot_radius * 3,
                                'color': woc,
                            },
                        },
                    ])
                
                ls.extend([
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ])
        elif(widget == 'BOOLEAN_2D' or widget == 'BOOLEAN_3D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            
            f = self._theme._fixed_radius
            w = f * 2
            h = f
            r = f / 2
            
            # FIXME: there is weirdness in tooltip and switch final sizes, so i just can't get reliable final size on screen. so i do here something very close and leave intentional gap, which look ok. problem will be if i want something more elaborate from tooltips and buttons. so fix this.. in a fullness of time..
            bh = self._theme._fixed_radius + ((self._theme._text_tooltip_outline_thickness * self._theme._ui_line_width) / 2)
            bh = int(bh / 2) * 2
            import blf
            font_id = 0
            blf.size(font_id, self._theme._text_size, 72)
            _, th = blf.dimensions(font_id, 'A', )
            th = th + ((8 * self._theme._ui_scale) * 2)
            th = th + ((self._theme._text_tooltip_outline_thickness * self._theme._ui_line_width) / 2)
            y = (bh / 2) + th - (6 * self._theme._ui_scale)
            
            ls = [
                {
                    'function': 'fancy_switch_2d',
                    'arguments': {
                        'coords': self._gesture_data['_mouse_2d'],
                        'state': self._gesture_data['_updated_property_value'],
                        'dimensions': (w, h),
                        'offset': (0, 0),
                        'align': 'CENTER',
                        'steps': self._theme._circle_steps,
                        'radius': r,
                        'bgfill': self._theme._text_tooltip_background_color,
                        # 'bgoutline': self._theme._text_tooltip_outline_color,
                        # NOTE: normal outline color, if outline and fill is the same, looks bad..
                        'bgoutline': woc,
                        'thickness': self._theme._text_tooltip_outline_thickness,
                    }
                },
                {
                    'function': 'fancy_tooltip_2d',
                    'arguments': {
                        'coords': self._gesture_data['_mouse_2d'],
                        'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                        # NOTE: (fixed / 2) + padding + radius + outline correction
                        # 'offset': (0, (f / 2) + 8 * self._theme._ui_scale + 4 * self._theme._ui_scale + 1 * self._theme._ui_scale, ),
                        'offset': (0, y),
                        'align': 'CENTER',
                        'size': self._theme._text_size,
                        'color': self._theme._text_color,
                        'shadow': True,
                        'padding': 8 * self._theme._ui_scale,
                        'steps': self._theme._circle_steps,
                        'radius': 4 * self._theme._ui_scale,
                        'bgfill': self._theme._text_tooltip_background_color,
                        'bgoutline': self._theme._text_tooltip_outline_color,
                        'thickness': self._theme._text_tooltip_outline_thickness,
                    }
                },
            ]
        elif(widget == 'SCALE_3D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_3d_loc']
            if(loc is not None):
                nor = self._gesture_data['_mouse_3d_nor']
                mt = Matrix.Translation(loc)
                mr = self._direction_to_rotation(nor).to_matrix().to_4x4()
                
                ms = Matrix(((vi.x, 0.0, 0.0, 0.0), (0.0, vi.y, 0.0, 0.0), (0.0, 0.0, vi.z, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mi = mt @ mr @ ms
                
                ms = Matrix(((vu.x, 0.0, 0.0, 0.0), (0.0, vu.y, 0.0, 0.0), (0.0, 0.0, vu.z, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mu = mt @ mr @ ms
                
                ls = [
                    # initial
                    {
                        'function': 'box_3d',
                        'arguments': {
                            'side_length': 1.0,
                            'matrix': mi,
                            'offset': (0.0, 0.0, 0.5),
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    {
                        'function': 'box_outline_3d',
                        'arguments': {
                            'side_length': 1.0,
                            'matrix': mi,
                            'offset': (0.0, 0.0, 0.5),
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    # updated
                    {
                        'function': 'box_outline_3d',
                        'arguments': {
                            'side_length': 1.0,
                            'matrix': mu,
                            'offset': (0.0, 0.0, 0.5),
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], *vu.to_tuple(), ),
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'STRENGTH_MINUS_PLUS_3D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            # FIXMENOT: property from brush is used
            r = self._domain_aware_brush_radius()
            
            loc = self._gesture_data['_mouse_3d_loc']
            if(loc is not None):
                r = self._widgets_compute_minimal_widget_size_for_radius_3d(context.region, context.region_data, loc, r, )
                
                vi = self._gesture_data['_inital_property_value']
                vu = self._gesture_data['_updated_property_value']
                
                circle_color = woc
                if(vu < 0.0):
                    # NOTE: negative color for negative values
                    a = 1.0 - np.array(woc[:3])
                    circle_color = tuple(a.tolist()) + (woc[3], )
                
                vii = (vi - (-1.0)) / (1.0 - (-1.0))
                vuu = (vu - (-1.0)) / (1.0 - (-1.0))
                vi *= r
                vu *= r
                vii *= r
                vuu *= r
                
                nor = self._gesture_data['_mouse_3d_nor']
                mt = Matrix.Translation(loc)
                mr = self._direction_to_rotation(nor).to_matrix().to_4x4()
                ms = Matrix(((vii, 0.0, 0.0, 0.0), (0.0, vii, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mi = mt @ mr @ ms
                
                ms = Matrix(((vuu, 0.0, 0.0, 0.0), (0.0, vuu, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mu = mt @ mr @ ms
                
                ms = Matrix(((r, 0.0, 0.0, 0.0), (0.0, r, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mmax = mt @ mr @ ms
                
                ls = [
                    # max circle (as radius)
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mmax,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    # initial value
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    {
                        'function': 'circle_fill_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    # update value
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mu,
                            'steps': self._theme._circle_steps,
                            'color': circle_color,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'DENSITY_3D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_3d_loc']
            if(loc is not None):
                # get final size on screen
                r = 1.0
                region = context.region
                rv3d = context.region_data
                loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
                n_2d = loc_2d + Vector((100, 0, ))
                n_2d_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, n_2d, loc)
                n_3d = n_2d_3d - loc
                n_3d.normalize()
                loc_offset = loc + (n_3d * r)
                a = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
                b = view3d_utils.location_3d_to_region_2d(region, rv3d, loc_offset, )
                size = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
                multiplier = 10
                min_size = self._theme._fixed_radius * multiplier
                if(size < min_size):
                    loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
                    loc2_2d = Vector((loc_2d.x, loc_2d.y + min_size))
                    loc2_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, loc2_2d, loc)
                    r = ((loc.x - loc2_3d.x) ** 2 + (loc.y - loc2_3d.y) ** 2 + (loc.z - loc2_3d.z) ** 2) ** 0.5
                
                # generate points
                rng_x = np.random.default_rng(seed=123, )
                rng_y = np.random.default_rng(seed=456, )
                n = int(round(vu * (r ** 2)))
                if(n <= 0):
                    n = 1
                x = rng_x.random(n, dtype=float, )
                y = rng_y.random(n, dtype=float, )
                
                # s = 1.0 / 25
                s = 1.0 / multiplier / 5
                
                def cross(x, y, offset, ):
                    vs = (
                        (x - s, y, 0.0, ),
                        (x + s, y, 0.0, ),
                        (x, y - s, 0.0, ),
                        (x, y + s, 0.0, ),
                    )
                    vs = np.array(vs, dtype=np.float32, )
                    indices = (
                        (0, 1),
                        (2, 3),
                    )
                    indices = np.array(indices, dtype=np.int32, )
                    indices = indices + offset
                    return vs, indices
                
                vertices = []
                indices = []
                c = 0
                for i in range(n):
                    a, b = cross(x[i], y[i], c, )
                    c += len(a)
                    vertices.append(a)
                    indices.append(b)
                
                vertices = np.concatenate(vertices)
                indices = np.concatenate(indices)
                
                vertices[:, 0] += -0.5
                vertices[:, 1] += -0.5
                
                nor = self._gesture_data['_mouse_3d_nor']
                mt = Matrix.Translation(loc)
                mr = self._direction_to_rotation(nor).to_matrix().to_4x4()
                
                ms = Matrix(((r, 0.0, 0.0, 0.0), (0.0, r, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                m = mt @ mr @ ms
                
                ls = [
                    # square
                    {
                        'function': 'rectangle_fill_3d',
                        'arguments': {
                            'a': (-0.5, -0.5, 0.0),
                            'b': (+0.5, +0.5, 0.0),
                            'matrix': m,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    {
                        'function': 'rectangle_outline_3d',
                        'arguments': {
                            'a': (-0.5, -0.5, 0.0),
                            'b': (+0.5, +0.5, 0.0),
                            'matrix': m,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    # points
                    {
                        'function': 'multiple_thick_lines_3d',
                        'arguments': {
                            'vertices': vertices,
                            'indices': indices,
                            'matrix': m,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'TOOLTIP_2D' or widget == 'TOOLTIP_3D'):
            vu = self._gesture_data['_updated_property_value']
            
            if(self._gesture_data['properties']['datatype'] in ('vector', )):
                text = self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], *vu.to_tuple(), )
            else:
                text = self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], vu, )
            
            ls = [
                {
                    'function': 'fancy_tooltip_2d',
                    'arguments': {
                        'coords': self._gesture_data['_mouse_2d'],
                        'text': text,
                        'offset': self._theme._text_tooltip_offset,
                        'align': 'CENTER',
                        'size': self._theme._text_size,
                        'color': self._theme._text_color,
                        'shadow': True,
                        'padding': 8 * self._theme._ui_scale,
                        'steps': self._theme._circle_steps,
                        'radius': 4 * self._theme._ui_scale,
                        'bgfill': self._theme._text_tooltip_background_color,
                        'bgoutline': self._theme._text_tooltip_outline_color,
                        'thickness': self._theme._text_tooltip_outline_thickness,
                    }
                },
            ]
        elif(widget == 'RADIUS_2D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_2d']
            ls = [
                # initial
                {
                    'function': 'circle_thick_outline_2d',
                    'arguments': {
                        'center': loc,
                        'radius': vi,
                        'steps': self._theme._circle_steps,
                        'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
                {
                    'function': 'circle_fill_2d',
                    'arguments': {
                        'center': loc,
                        'radius': vi,
                        'steps': self._theme._circle_steps,
                        'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                    }
                },
                # updated
                {
                    'function': 'circle_thick_outline_2d',
                    'arguments': {
                        'center': loc,
                        'radius': vu,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                {
                    'function': 'fancy_tooltip_2d',
                    'arguments': {
                        'coords': self._gesture_data['_mouse_2d'],
                        'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                        'offset': self._theme._text_tooltip_offset,
                        'align': 'CENTER',
                        'size': self._theme._text_size,
                        'color': self._theme._text_color,
                        'shadow': True,
                        'padding': 8 * self._theme._ui_scale,
                        'steps': self._theme._circle_steps,
                        'radius': 4 * self._theme._ui_scale,
                        'bgfill': self._theme._text_tooltip_background_color,
                        'bgoutline': self._theme._text_tooltip_outline_color,
                        'thickness': self._theme._text_tooltip_outline_thickness,
                    }
                },
            ]
        elif(widget == 'STRENGTH_2D'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            # FIXMENOT: property from brush is used
            r = self._domain_aware_brush_radius()
            if(r < self._theme._fixed_radius * 2):
                r = self._theme._fixed_radius * 2
            
            vi = self._gesture_data['_inital_property_value'] * r
            vu = self._gesture_data['_updated_property_value'] * r
            loc = self._gesture_data['_mouse_2d']
            
            ls = [
                # max circle (as radius)
                {
                    'function': 'circle_thick_outline_2d',
                    'arguments': {
                        'center': loc,
                        'radius': r,
                        'steps': self._theme._circle_steps,
                        'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
                # initial value
                {
                    'function': 'circle_thick_outline_2d',
                    'arguments': {
                        'center': loc,
                        'radius': vi,
                        'steps': self._theme._circle_steps,
                        'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
                {
                    'function': 'circle_fill_2d',
                    'arguments': {
                        'center': loc,
                        'radius': vi,
                        'steps': self._theme._circle_steps,
                        'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                    }
                },
                # update value
                {
                    'function': 'circle_thick_outline_2d',
                    'arguments': {
                        'center': loc,
                        'radius': vu,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                # tooltip
                {
                    'function': 'fancy_tooltip_2d',
                    'arguments': {
                        'coords': self._gesture_data['_mouse_2d'],
                        'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                        'offset': self._theme._text_tooltip_offset,
                        'align': 'CENTER',
                        'size': self._theme._text_size,
                        'color': self._theme._text_color,
                        'shadow': True,
                        'padding': 8 * self._theme._ui_scale,
                        'steps': self._theme._circle_steps,
                        'radius': 4 * self._theme._ui_scale,
                        'bgfill': self._theme._text_tooltip_background_color,
                        'bgoutline': self._theme._text_tooltip_outline_color,
                        'thickness': self._theme._text_tooltip_outline_thickness,
                    }
                },
            ]
        elif(widget == 'RADIUS_2_5D___DO_NOT_USE___USE_RADIUS_3D_INSTEAD'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            vi = self._gesture_data['_inital_property_value']
            vu = self._gesture_data['_updated_property_value']
            loc = self._gesture_data['_mouse_3d_loc']
            
            if(self._get_prop_value('radius_units') == 'VIEW'):
                s = self._radius_px_to_world(self._context_region, self._context_region_data, self._mouse_3d, 1, )
                vi *= s
                vu *= s
            
            if(loc is not None):
                nor = self._gesture_data['_mouse_3d_nor']
                mt = Matrix.Translation(loc)
                ms = Matrix(((vi, 0.0, 0.0, 0.0), (0.0, vi, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mi = mt @ ms
                
                ms = Matrix(((vu, 0.0, 0.0, 0.0), (0.0, vu, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mu = mt @ ms
                
                if(self._get_prop_value('radius_units') == 'VIEW'):
                    tt = self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], int(self._gesture_data['_updated_property_value']))
                else:
                    tt = self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value'])
                
                ls = [
                    # initial
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    {
                        'function': 'circle_fill_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    # updated
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mu,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': tt,
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'STRENGTH_2_5D___DO_NOT_USE___USE_STRENGTH_3D_INSTEAD'):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            # FIXMENOT: property from brush is used
            r = self._domain_aware_brush_radius()
            
            loc = self._gesture_data['_mouse_3d_loc']
            if(loc is not None):
                r = self._widgets_compute_minimal_widget_size_for_radius_3d(context.region, context.region_data, loc, r, )
                vi = self._gesture_data['_inital_property_value'] * r
                vu = self._gesture_data['_updated_property_value'] * r
                
                nor = self._gesture_data['_mouse_3d_nor']
                mt = Matrix.Translation(loc)
                ms = Matrix(((vi, 0.0, 0.0, 0.0), (0.0, vi, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mi = mt @ ms
                
                ms = Matrix(((vu, 0.0, 0.0, 0.0), (0.0, vu, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mu = mt @ ms
                
                ms = Matrix(((r, 0.0, 0.0, 0.0), (0.0, r, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mmax = mt @ ms
                
                ls = [
                    # max circle (as radius)
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mmax,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    # initial value
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': woc[:3] + (self._theme._outline_color_gesture_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                    {
                        'function': 'circle_fill_3d',
                        'arguments': {
                            'matrix': mi,
                            'steps': self._theme._circle_steps,
                            'color': wfc[:3] + (self._theme._fill_color_gesture_helper_alpha, ),
                        }
                    },
                    # update value
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': mu,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # tooltip
                    {
                        'function': 'fancy_tooltip_2d',
                        'arguments': {
                            'coords': self._gesture_data['_mouse_2d'],
                            'text': self._gesture_data['properties']['text'].format(self._gesture_data['properties']['name'], self._gesture_data['_updated_property_value']),
                            'offset': self._theme._text_tooltip_offset,
                            'align': 'CENTER',
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'padding': 8 * self._theme._ui_scale,
                            'steps': self._theme._circle_steps,
                            'radius': 4 * self._theme._ui_scale,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._text_tooltip_outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ]
        elif(widget == 'ENUM_2D' or widget == 'ENUM_3D'):
            # WATCH: this is only for two option enum, that is what i need now, if i ever need more options, then i will change it to any length enum. basically pie menu..
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            vu = self._gesture_data['_updated_property_value']
            
            f = self._theme._fixed_radius
            w = f * 2
            h = f
            r = f / 2
            
            p = int(r / 2)
            x = -(int(w / 2) + p)
            y = 0
            
            options = [(o.identifier, o.name, ) for o in self._get_prop_group(self._gesture_data['_property']).bl_rna.properties[self._gesture_data['_property']].enum_items[:]]
            
            ls = []
            for i, t in options:
                ls.extend((
                    {
                        'function': 'fancy_button_2d',
                        'arguments': {
                            'text': t,
                            'state': bool(i == vu),
                            'coords': self._gesture_data['_mouse_2d'],
                            'dimensions': (w, h),
                            'offset': (x, y),
                            'size': self._theme._text_size,
                            'color': self._theme._text_color,
                            'shadow': True,
                            'steps': self._theme._circle_steps,
                            'radius': r,
                            'bgfill': self._theme._text_tooltip_background_color,
                            'bgoutline': self._theme._outline_color,
                            'thickness': self._theme._text_tooltip_outline_thickness,
                        }
                    },
                ))
                x += w + (p * 2)
        else:
            pass
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    # ------------------------------------------------------------------ gesture <<<
    # ------------------------------------------------------------------ core >>>
    
    def _update_references_and_settings(self, context, event, ):
        # NOTE: lets update these on each modal event as well..
        self._surfaces = [bpy.data.objects.get(n) for n in self._surfaces_names]
        self._target = bpy.data.objects.get(self._target_name)
        self._props = bpy.context.scene.scatter5.manual
        self._brush = getattr(self._props, self._brush_props_name)
    
    def _modal(self, context, event, ):
        # if i need something to be constantly refreshed.. not widgets..
        self._on_any_modal_event(context, event, )
        
        # update..
        self._context_region = context.region
        self._context_region_data = context.region_data
        # update settings..
        self._update_references_and_settings(context, event, )
        
        # ------------------------------------------------------------------ gesture >>>
        if(self._gesture_mode):
            if(event.type in {'ESC', 'RIGHTMOUSE', } and event.value == 'PRESS'):
                self._gesture_cancel(context, event, )
                self._gesture_mode = False
                self._gesture_data = None
            elif(event.type in {'LEFTMOUSE', } and event.value == 'PRESS'):
                self._gesture_finish(context, event, )
                self._gesture_mode = False
                self._gesture_data = None
            elif(event.type in {'MOUSEMOVE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', }):
                self._gesture_update(context, event, )
                self._gesture_widget(context, event, )
            
            # NOTE: early exit while in gesture (and when i just finished)..
            return {'RUNNING_MODAL'}
        # ------------------------------------------------------------------ gesture <<<
        # ------------------------------------------------------------------ exit >>>
        # process exit at the top, so it works in any area..
        if(event.type in {'ESC', } and event.value == 'PRESS'):
            self._abort(context, event, )
            
            # NOTE: integration with custom ui. restore ui
            self._integration_on_finish(context, event, )
            
            return {'CANCELLED'}
        # ------------------------------------------------------------------ exit <<<
        
        # ------------------------------------------------------------------ undo/redo >>>
        if(event.type in {'Z', } and (event.oskey or event.ctrl)):
            self._undo_redo_callback(context, event, )
            # pass through undo..
            return {'PASS_THROUGH'}
        # ------------------------------------------------------------------ undo/redo <<<
        
        # ------------------------------------------------------------------ workspace >>>
        # NOTE: this is better placement, change in toolbar is detected sooner and outside of 3d view..
        
        # NOTE: integration with custom ui. observe active workspace tool and if does not match current operator, stop it, and run new
        active = context.workspace.tools.from_space_view3d_mode(context.mode).idname
        if(self.tool_id != active):
            opc = get_tool_class(active)
            n = opc.bl_idname.split('.', 1)
            op = getattr(getattr(bpy.ops, n[0]), n[1])
            if(op.poll()):
                # i am allowed to run new tool, so stop current tool
                self._abort(context, event, )
                # and run it..
                op('INVOKE_DEFAULT', )
                return {'CANCELLED'}
        
        # ------------------------------------------------------------------ workspace <<<
        
        # ------------------------------------------------------------------ areas >>>
        # allow asset briwser to get events
        in_asset_browser = self._is_asset_browser(context, event, )
        if(in_asset_browser):
            if(not self._lmb):
                self._widgets_mouse_outside(context, event, )
                self._status_idle(context, event, )
                context.window.cursor_modal_restore()
                return {'PASS_THROUGH'}
        
        # allow header, toolbar etc. access..
        in_other_regions = self._is_3dview_other_regions(context, event, )
        if(in_other_regions):
            if(not self._lmb):
                self._widgets_mouse_outside(context, event, )
                self._status_idle(context, event, )
                context.window.cursor_modal_restore()
                return {'PASS_THROUGH'}
        
        if(debug.debug_mode()):
            debug_area = self._is_debug_console_or_spreadsheet(context, event, )
            if(debug_area):
                if(not self._lmb):
                    self._widgets_mouse_outside(context, event, )
                    self._status_idle(context, event, )
                    context.window.cursor_modal_restore()
                    return {'PASS_THROUGH'}
        
        in_viewport = self._is_viewport(context, event, )
        # deny all other areas but initial 3d view (the one passed in context)
        if(not in_viewport):
            if(not self._lmb):
                self._widgets_mouse_outside(context, event, )
                self._status_idle(context, event, )
                # context.window.cursor_modal_restore()
                # context.window.cursor_modal_set('NONE')
                # context.window.cursor_modal_set('WAIT')
                context.window.cursor_modal_set('STOP')
                return {'RUNNING_MODAL'}
        
        # FIXME: if tool is running, any menu that hovers over 3d view and is double clicked in empty ui space (i.e. no ui button) the event passes through and inits tool, this was present also in old system, but nobody ever noticed. problem is, i found no way to detect when mouse is in menu. i would guess all event should be blocked in menu, but they are not. another time to ui related bug report? that will haunt bug tracker for years to come? everybody to scared to even touch it..
        
        # # NOTE: sidebar disabled for now..
        # in_sidebar = self._is_sidebar(context, event, )
        # if(in_sidebar):
        #     if(not self._lmb):
        #         self._widgets_mouse_outside(context, event, )
        #         # standard cursor only on sidebar and only when mouse is not dragged there while lmb is down
        #         context.window.cursor_modal_restore()
        #         return {'PASS_THROUGH'}
        
        # ------------------------------------------------------------------ areas <<<
        
        # everywhere else use tool cursor, even on disabled areas, so user is reminded that tool is running
        context.window.cursor_modal_set(self._cursor_modal_set)
        
        # TODO: i meant that for anything that is linked to mouse directly, i mean `cursor_components`, but is it good approach? shouldn't it be part of idle/press/move/release? with all the troubles with navigation, this is another thing to worry about.. lets think about that some more..
        self._widgets_any_event(context, event, )
        
        # ------------------------------------------------------------------ mouse 2d and 3d coordinates, directions, path, etc.. >>>
        # NOTE: only to update props, no other work to be done here. actual work is dane in action callbacks
        if(event.type == 'MOUSEMOVE'):
            self._on_mouse_move(context, event, )
        elif(event.type == 'INBETWEEN_MOUSEMOVE'):
            self._on_mouse_move_inbetween(context, event, )
        # ------------------------------------------------------------------ mouse 2d and 3d coordinates, directions, path, etc.. <<<
        
        # key events, runs event when mouse is pressed
        # TODO: placement of this might be unuseable, it should be after modifier setting? it is not used yet for anything..
        # TODO: modifiers are detected by set of flags later and tool/gesture shortcuts also later
        # TODO: this does nothing now, and might get useful in tools that defines special behavior..
        if(event.value in {'PRESS', 'RELEASE', }):
            if(self._is_key_event(context, event, )):
                if(event.value == 'PRESS'):
                    if(event.is_repeat):
                        self._on_any_key_repeat(context, event, )
                    else:
                        self._on_any_key_press(context, event, )
                if(event.value == 'RELEASE'):
                    self._on_any_key_release(context, event, )
        
        # ------------------------------------------------------------------ navigation >>>
        if(self._nav and event.type == 'TIMER'):
            # redraw while navigating
            self._widgets_mouse_idle(context, event, )
            self._status_idle(context, event, )
        if(self._nav and event.type != 'TIMER'):
            # i was navigating and now i am not because some other event is here, turn nav off and run anotehr idle redraw
            self._nav = False
            self._widgets_mouse_idle(context, event, )
            self._status_idle(context, event, )
        if(event.type != 'TIMER'):
            # now test if i have another nav event
            # NOTE: warning, in no way i can rely on `self._nav` being correct, when user stops navigating and then does not move mouse or hit any key, no event is fired so i cannot know what is happening, this is only for timer to redraw screen. and screen drawing should be in idle mode, no cursor changes, or i get cursor glitches.. so it will look that user does not iteract with anything, i draw idle state, then user starts navigating and idle state is redrawn, then stops, then idle is being drawn until something happen..
            if(self._nav_enabled):
                self._nav = self._navigator.run(context, event, None, )
            else:
                self._nav = False
            
            if(self._nav):
                # WATCH: maybe this is not needed..
                self._widgets_mouse_idle(context, event, )
            
            # NOTE: for 3d mouse use passing event out, becuase from some unknown reason, if operator is called directly, returns cancelled even when event iscorrect type.
            # TODO: investigate why ndof events are rejected in source/blender/editors/space_view_3d/view3d_navigate_ndof.c @499
            # TODO: and do that the same with trackpad events, it does not behave like mouse events..
            if(not self._nav):
                if(event.type.startswith('NDOF_')):
                    if(self._nav_enabled):
                        self._nav = True
                        return {'PASS_THROUGH'}
                if(event.type.startswith('TRACKPAD')):
                    if(self._nav_enabled):
                        self._nav = True
                        return {'PASS_THROUGH'}
        if(self._nav):
            return {'RUNNING_MODAL'}
        # ------------------------------------------------------------------ navigation <<<
        
        # # NOTE: do i need it? it can be useful, not to care about redrawing. but what about performance? do it manually for now, and see if i get into some problems or not.
        # context.area.tag_redraw()
        
        # ------------------------------------------------------------------ modifiers >>>
        mod = False
        if(event.ctrl != self._ctrl):
            self._ctrl = event.ctrl
            mod = True
        if(event.alt != self._alt):
            self._alt = event.alt
            mod = True
        if(event.shift != self._shift):
            self._shift = event.shift
            mod = True
        if(event.oskey != self._oskey):
            self._oskey = event.oskey
            mod = True
        if(mod):
            # NOTE: i think this is redundant, this should be handled in widgets drawing key mouse functions, if some modifier is on, draw something extra
            self._widgets_modifiers_change(context, event, )
            # NOTE: and for actions, because i pass modal args (context, event, ) all over, it is preffered way to get modifier status, so if something is pressed, do something accordingly, do not rely on another prop somewhere updated on key press/release.
            # NOTE: but yet somehow to refresh widgets on modifier press it is needed...
        # ------------------------------------------------------------------ modifiers <<<
        
        # # ------------------------------------------------------------------ workspace >>>
        #
        # # NOTE: integration with custom ui. observe active workspace tool and if does not match current operator, stop it, and run new
        # active = context.workspace.tools.from_space_view3d_mode(context.mode).idname
        # if(self.tool_id != active):
        #     opc = get_tool_class(active)
        #     n = opc.bl_idname.split('.', 1)
        #     op = getattr(getattr(bpy.ops, n[0]), n[1])
        #     if(op.poll()):
        #         # i am allowed to run new tool, so stop current tool
        #         self._abort(context, event, )
        #         # and run it..
        #         op('INVOKE_DEFAULT', )
        #         return {'CANCELLED'}
        #
        # # ------------------------------------------------------------------ workspace <<<
        
        # ------------------------------------------------------------------ shortcuts >>>
        shortcut = self._configurator.check(context, event, )
        if(shortcut):
            if(shortcut['call'] == 'OPERATOR'):
                # NOTE: this will stop current operator, so no much need for elaborate resetting
                if(shortcut['execute'] != self.tool_id):
                    # get new tool op
                    n = shortcut['execute'].split('.', 1)
                    op = getattr(getattr(bpy.ops, n[0]), n[1])
                    if(op.poll()):
                        # i am allowed to run new tool, so stop current tool
                        self._abort(context, event, )
                        # and run it..
                        op('INVOKE_DEFAULT', )
                        return {'CANCELLED'}
            elif(shortcut['call'] == 'GESTURE'):
                ok = False
                # empty shortcut have properties as None
                if(shortcut['properties'] is not None):
                    # NOTE: 3D and 2.5D gesture widgets need mouse surface location
                    widget = shortcut['properties']['widget']
                    if(widget.endswith('_3D') and self.tool_gesture_space == '3D'):
                        if(self._mouse_3d_loc is not None):
                            ok = True
                    elif(widget.endswith('_2_5D') and self.tool_gesture_space == '3D'):
                        if(self._mouse_3d_loc is not None):
                            ok = True
                    elif(widget.endswith('_2D') and self.tool_gesture_space == '2D'):
                        ok = True
                    elif(widget == 'FUNCTION_CALL'):
                        # NOTE: not sure if i need to diffrentiate to 3d and 2d with this, it have only single use in manipulator..
                        ok = True
                    else:
                        # NOTE: after that, it is unknown definition, skip? error?
                        pass
                
                if(ok):
                    # NOTE: all other functionality has to stop, so navigation, drawing, anything taht is running should stop
                    if(shortcut['properties'] and not event.is_repeat):
                        # NOTE: so, some resets first..
                        if(self._nav):
                            self._nav = False
                            self._widgets_mouse_idle(context, event, )
                            self._status_idle(context, event, )
                        if(self._lmb):
                            self._lmb = False
                            self._action_finish_private(context, event, )
                            self._widgets_mouse_release(context, event, )
                            self._status_idle(context, event, )
                        
                        # gesture properties are set, so tool defines gesture and i can continue
                        self._gesture_mode = True
                        self._gesture_data = shortcut
                        self._gesture_begin(context, event, )
                        self._gesture_widget(context, event, )
                    
                        # NOTE: early exit while in gesture..
                        return {'RUNNING_MODAL'}
        # ------------------------------------------------------------------ shortcuts <<<
        # ------------------------------------------------------------------ props <<<
        if(event.is_tablet):
            self._pressure = event.pressure
            if(self._pressure <= 0.001):
                # prevent zero pressure which might sometimes happen..
                self._pressure = 0.001
        # ------------------------------------------------------------------ props <<<
        # ------------------------------------------------------------------ action >>>
        # in_viewport = self._is_viewport(context, event, )
        #
        # if(not in_viewport):
        #     if(not self._lmb):
        #         self._widgets_mouse_outside(context, event, )
        #         self._status_idle(context, event, )
        #         context.window.cursor_modal_restore()
        #         return {'RUNNING_MODAL'}
        
        # WATCH: this caused to running idle redraw on any event including timers, i think i can exclude timer, but beware of possible consequences
        # if(not self._lmb):
        # WATCH: still too much redraws..
        # if(not self._lmb and event.type != 'TIMER'):
        # WATCH: so, no timers and no betweens
        if(not self._lmb and event.type not in ('TIMER', 'INBETWEEN_MOUSEMOVE', )):
            # call idle when mouse is not pressed down, so i detect modifiers and update
            # when mouse is down press, move and release handles things..
            self._widgets_mouse_idle(context, event, )
            self._status_idle(context, event, )
        
        if(event.type == 'LEFTMOUSE' and event.value == 'PRESS'):
            if(not in_viewport):
                return {'RUNNING_MODAL'}
            self._lmb = True
            self._action_begin_private(context, event, )
            self._widgets_mouse_press(context, event, )
            self._status_action(context, event, )
        elif(event.type == 'MOUSEMOVE'):
            if(self._lmb):
                self._action_update_private(context, event, )
                self._widgets_mouse_move(context, event, )
                self._status_action(context, event, )
            else:
                self._action_idle_private(context, event, )
        elif(event.type == 'INBETWEEN_MOUSEMOVE'):
            if(self._lmb):
                self._action_update_inbetween_private(context, event, )
                self._widgets_mouse_move_inbetween(context, event, )
            else:
                self._action_idle_inbetween_private(context, event, )
        elif(event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            if(not self._lmb):
                return {'RUNNING_MODAL'}
            self._lmb = False
            self._action_finish_private(context, event, )
            self._widgets_mouse_release(context, event, )
            # TODO: is this correct? action or idle status here?
            self._status_action(context, event, )
            return {'RUNNING_MODAL'}
        # ------------------------------------------------------------------ action <<<
        self._modal_shortcuts(context, event, )
        # r = self._modal_shortcuts(context, event, )
        # if(r is not None):
        #     return r
        # # ------------------------------------------------------------------ exit >>>
        # # if(event.type in {'RIGHTMOUSE', 'ESC', 'RET', }):
        # if(event.type in {'ESC', }):
        #     self._abort(context, event, )
        #     return {'CANCELLED'}
        # # ------------------------------------------------------------------ exit <<<
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event, ):
        # m = "{: <{namew}} >>> {}".format(self.modal.__qualname__, 'modal', namew=36, )
        # log(m, prefix='>>>', color='YELLOW', )
        
        if(self._aborted):
            return {'CANCELLED'}
        
        # # NOTE: well, lets add it anyway. windgets should call its own, but in case i forget. calling it twice in row is harmless
        # # NOTE: not sure now, i got navigation timer running 10x per second, this will force constant redrawing.
        # # NOTE: ok, no redraw on any event, leaving it here to remind me next time i am tempted to do it
        # context.area.tag_redraw()
        
        try:
            r = self._modal(context, event, )
            return r
        except Exception as e:
            self._abort(context, event, )
            
            # NOTE: problem in `invoke` and `modal` should end in `panic` where everything should be reset
            panic(self.modal.__qualname__)
            
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            return {'CANCELLED'}
    
    def _invoke(self, context, event, ):
        self._cursor_modal_set = 'PAINT_CROSS'
        
        self._action_execute_on = 'MOUSEMOVE'
        # self._action_execute_on = 'TIMER'
        # self._action_execute_on = 'BOTH'
        self._action_timer_interval = 0.1
        
        # mouse props 2d
        self._mouse_2d = Vector((event.mouse_x, event.mouse_y, ))
        self._mouse_2d_prev = Vector((event.mouse_x, event.mouse_y, ))
        self._mouse_2d_direction = Vector()
        self._mouse_2d_direction_interpolated = Vector()
        self._mouse_2d_region = Vector((event.mouse_region_x, event.mouse_region_y, ))
        self._mouse_2d_region_prev = Vector((event.mouse_region_x, event.mouse_region_y, ))
        # TODO: should be accessible for user? now with interpolation it is more important..
        # self._mouse_2d_direction_minimal_distance = 10
        self._mouse_2d_direction_minimal_distance = 5
        self._mouse_2d_path = [Vector((event.mouse_region_x, event.mouse_region_y, )), ]
        self._mouse_2d_path_direction = [Vector(), ]
        # mouse props 3d
        self._mouse_3d = None
        self._mouse_3d_prev = None
        self._mouse_3d_direction = None
        self._mouse_3d_direction_interpolated = None
        # TODO: should be accessible for user? now with interpolation it is more important..
        # self._mouse_3d_direction_minimal_distance = 0.05
        self._mouse_3d_direction_minimal_distance = 0.02
        self._mouse_3d_path = []
        self._mouse_3d_path_direction = []
        # store projection results as well, minimally normal will became very handy. and i can save some cpu cycles..
        self._mouse_3d_loc = None
        self._mouse_3d_nor = None
        self._mouse_3d_idx = None
        self._mouse_3d_dst = None
        
        self._mouse_tracking_inbetween = False
        
        # mouse surface tracking
        self._mouse_active_surface_name = None
        self._mouse_active_surface_uuid = None
        self._mouse_active_surface_matrix = None
        
        # store references to 3d viewport region and region data so i can later use them for conversion from world to screen space and vice versa when context and event are not available (for example timer handlers)
        self._context_region = context.region
        self._context_region_data = context.region_data
        
        # NOTE: 5.3: get emitter, surfaces(s) and target
        self._emitter = bpy.context.scene.scatter5.emitter
        psys = self._emitter.scatter5.get_psy_active()
        surfaces = psys.get_surfaces()
        
        self._surfaces = surfaces
        self._target = psys.scatter_obj
        
        # store their names
        self._surfaces_names = [o.name for o in surfaces]
        self._surfaces_db = {}
        for s in surfaces:
            self._surfaces_db[s.scatter5.uuid] = s.name
        
        # # NOTE: remove points with not existing uid.. in case of previous error it is the only way, unles trial and error with deleting random vertices in edit mode
        # self._verify_target_integrity(fix=True, )
        
        # NOTE: from now on, i expect uids on vertices to be valid, no checks regarding uids
        # NOTE: better to run this one as well..
        self._ensure_attributes()
        
        # NOTE: meh..
        self._set_target_orphan_mask_at_startup()
        
        self._target_name = self._target.name
        
        # get brush props
        self._props = bpy.context.scene.scatter5.manual
        if(not hasattr(self, '_brush_props_name')):
            # self._brush_props_name = 'default_brush'
            self._brush_props_name = 'tool_default'
        self._brush = getattr(self._props, self._brush_props_name)
        
        # get session cache data
        # TODO: prefix with `_cache_` so i have all organized..
        
        # c = ToolSessionCache.get(context, [self._surface, ])
        c = ToolSessionCache.get(context, self._surfaces, )
        self._bm = c['bm']
        self._bvh = c['bvh']
        self._cache_vs_co = c['arrays']['v_co']
        self._cache_vs_no = c['arrays']['v_normal']
        self._cache_fs_ii = c['arrays']['f_vertices']
        self._cache_fs_no = c['arrays']['f_normal']
        
        # # DEBUG
        # me = ToolSessionCache._cached_arrays_to_mesh_datablock()
        # o = bpy.data.objects.new('debug', me, )
        # bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
        # # DEBUG
        
        # NOTE: for brushes to initialize their own props.. or override base props..
        # NOTE: define its own specific _invoke function, then first call `super()._invoke(context, event, )` then set own stuff
        # NOTE: except reference to brush props, that is set before calling super() and then it won't be overwritten with default
        # NOTE: and it is set by props name `self.brush_props_name` so i can automate its retrieval after undo/redo
    
    def _invoke_private(self, context, event, ):
        if(ToolBox.reference is not None):
            try:
                ToolBox.reference._abort(context, event, )
            except Exception as e:
                # NOTE: panic!
                panic(self.invoke.__qualname__)
        
        ToolBox.tool = self.tool_id
        ToolBox.reference = self
        
        self._configurator = ToolKeyConfigurator(self)
        self._gesture_mode = False
        self._gesture_data = None
        
        # infobox >>>
        t = infobox.generic_infobox_setup(*self._infobox_collect_texts())
        SC5InfoBox.init(t)
        # infobox <<<
        
        self._aborted = False
        
        # NOTE: so i can identify correct 3d view in draw handlers.. maybe use that also for modal evnt handling
        self._invoke_area = context.area
        self._invoke_region = context.region
        
        # overlay grid >>>
        # exclude_areas = ['VIEW_3D', ]
        # if(debug.debug_mode()):
        #     exclude_areas = ['VIEW_3D', 'SPREADSHEET', 'CONSOLE', ]
        # exclude_regions = ['WINDOW', 'UI', 'HEADER', 'TOOLS', ]
        # SC5GridOverlay.init(self, context, exclude_areas=exclude_areas, exclude_regions=exclude_regions, invoke_area_only=True, )
        ex = (
            # default is invoke 3d view with tools and header
            (self._invoke_area, 'WINDOW', ),
            (self._invoke_area, 'TOOLS', ),
            (self._invoke_area, 'HEADER', ),
        )
        # then add asset browser is open
        for a in context.screen.areas:
            if(a.type == 'FILE_BROWSER'):
                if(a.spaces[0].browse_mode == 'ASSETS'):
                    ex += (
                        (a, 'WINDOW', ),
                        (a, 'TOOLS', ),
                    )
        if(debug.debug_mode()):
            for a in context.screen.areas:
                if(a.type in ('CONSOLE', 'SPREADSHEET', )):
                    ex += ((a, None, ), )
        
        self._grid_exclude = ex
        
        GridOverlay.init(self, context, )
        # overlay grid <<<
        
        self._lmb = False
        self._pressure = 1.0
        self._nav = False
        self._nav_enabled = True
        
        self._ctrl = event.ctrl
        self._alt = event.alt
        self._shift = event.shift
        self._oskey = event.oskey
        
        # timer used for screen redrawing during navigation
        self._nav_timer_time_step = 1 / 30
        self._nav_timer = context.window_manager.event_timer_add(self._nav_timer_time_step, window=context.window, )
        
        self._navigator = ToolNavigator(context, )
        
        context.window.cursor_modal_set('WAIT')
        
        self._theme = ToolTheme(self, )
        
        ToolWidgets.init(self, context, )
        ToolWidgets._cache[self.tool_id] = {
            'screen_components': [],
            'cursor_components': [],
        }
        
        # NOTE: run `_invoke` that tools usually override
        self._invoke(context, event, )
        
        context.window.cursor_modal_set(self._cursor_modal_set)
        
        context.window_manager.modal_handler_add(self)
        
        # NOTE: update mouse tracking, if tool is invoked by shortcut, it should be ready to go without mouse moving
        self._on_mouse_move(context, event, )
        
        # NOTE: integration with custom ui. rebuild ui
        self._integration_on_invoke(context, event, )
        # NOTE: set tool in toolbar
        bpy.ops.wm.tool_set_by_id(name=self.tool_id)
        # NOTE: integration with custom ui. write last used tool to be restored at next startup
        bpy.context.scene.scatter5.manual.active_tool = self.tool_id
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event, ):
        m = "{: <{namew}} >>> {}".format(self.invoke.__qualname__, 'invoke', namew=36, )
        log(m, prefix='>>>', )
        log("invoke: {}".format(self.tool_id), prefix='TOOL >>>', )
        
        try:
            r = self._invoke_private(context, event)
            return r
        except Exception as e:
            self._abort(context, event, )
            
            # NOTE: problem in `invoke` and `modal` should end in `panic` where everything should be reset
            panic(self.invoke.__qualname__)
            
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, traceback.format_exc(), )
            return {'CANCELLED'}
    
    # ------------------------------------------------------------------ core <<<
    # ------------------------------------------------------------------ abort & cleanup >>>
    
    def _cleanup(self, context, event, ):
        # NOTE: empty, tool got to define it own if needed..
        pass
    
    @verbose
    def _abort(self, context, event, ):
        log("abort: {}".format(self.tool_id), prefix='TOOL >>>', )
        
        ToolBox.tool = None
        ToolBox.reference = None
        
        ToolWidgets.deinit()
        SC5InfoBox.deinit()
        # SC5GridOverlay.deinit()
        GridOverlay.deinit()
        
        self._cleanup(context, event, )
        
        try:
            # if invoke calls abort, this might not be set yet
            context.window_manager.event_timer_remove(self._nav_timer)
        except Exception as e:
            pass
        
        context.window.cursor_modal_restore()
        context.workspace.status_text_set(text=None, )
        
        self._aborted = True
        
        # # NOTE: integration with custom ui. restore ui
        # self._integration_on_finish(context, event, )
    
    # ------------------------------------------------------------------ abort & cleanup <<<


# NOTTODO: should i always exit to 'builtin.select_box'? in case of error in tool, it is never set back to some builtin tool, then there are constant warnings -->> panic() sets it
# DONE: billboard dot in all 3d widgets
class SCATTER5_OT_common_mixin():
    # ------------------------------------------------------------------ data system >>>
    attribute_map = {
        # public for nodes
        'normal': ['FLOAT_VECTOR', 'POINT', ],
        'rotation': ['FLOAT_VECTOR', 'POINT', ],
        'scale': ['FLOAT_VECTOR', 'POINT', ],
        'index': ['INT', 'POINT', ],
        # 'id': ['FLOAT', 'POINT', ],
        'id': ['INT', 'POINT', ],
        'align_z': ['FLOAT_VECTOR', 'POINT', ],
        'align_y': ['FLOAT_VECTOR', 'POINT', ],
        # surface uuid
        'surface_uuid': ['INT', 'POINT', ],
        
        # # brush location and surface normal at the time of point is generated
        # 'private_loc': ['FLOAT_VECTOR', 'POINT', ],
        # 'private_nor': ['FLOAT_VECTOR', 'POINT', ],
        
        # False: active (default), True: masked (orphan point)
        'private_orphan_mask': ['BOOLEAN', 'POINT', ],
        
        # rotation intermediates v2 / starting points
        # TODO: call this 'private_r_align_z'? or something like that..
        # 'SURFACE_NORMAL' = 0, 'LOCAL_Z_AXIS' = 1, 'GLOBAL_Z_AXIS' = 2, custom vector = 3
        'private_r_align': ['INT', 'POINT', ],
        'private_r_align_vector': ['FLOAT_VECTOR', 'POINT', ],
        # TODO: call this 'private_r_align_y'? or something like that..
        # 'GLOBAL_Y_AXIS' = 0, 'LOCAL_Y_AXIS' = 1, custom vector = 2
        'private_r_up': ['INT', 'POINT', ],
        'private_r_up_vector': ['FLOAT_VECTOR', 'POINT', ],
        # rotation_base value
        'private_r_base': ['FLOAT_VECTOR', 'POINT', ],
        # rotation_random value
        'private_r_random': ['FLOAT_VECTOR', 'POINT', ],
        # 3 random number used for random euler calculation
        'private_r_random_random': ['FLOAT_VECTOR', 'POINT', ],
        
        # scale intermediates v2 / starting points
        'private_s_base': ['FLOAT_VECTOR', 'POINT', ],
        'private_s_random': ['FLOAT_VECTOR', 'POINT', ],
        'private_s_random_random': ['FLOAT_VECTOR', 'POINT', ],
        # 'UNIFORM' = 0, 'VECTORIAL' = 1
        'private_s_random_type': ['INT', 'POINT', ],
        'private_s_change': ['FLOAT_VECTOR', 'POINT', ],
        # 0: direction (1 or -1) - currently unused because there is no point using it, 1: scale increment factor 0.0-1.0, 2: unused
        # NOTE: only single value is used now, but might become handy later.. also it is set at creation time, only set rotation brush regenerates it
        'private_s_change_random': ['FLOAT_VECTOR', 'POINT', ],
        
        'private_z_original': ['FLOAT_VECTOR', 'POINT', ],
        # 0: start, 1: current, 2: lerp factor
        'private_z_random': ['FLOAT_VECTOR', 'POINT', ],
    }
    attribute_prefix = 'manual_'
    
    def _ensure_attributes(self, ):
        me = self._target.data
        for n, t in self.attribute_map.items():
            nm = '{}{}'.format(self.attribute_prefix, n)
            a = me.attributes.get(nm)
            if(a is None):
                me.attributes.new(nm, t[0], t[1])
    
    def _verify_target_integrity(self, fix=True, ):
        raise Exception("do not use")
        
        self._ensure_attributes()
        
        me = self._target.data
        l = len(me.vertices)
        uids = np.zeros(l, dtype=int, )
        me.attributes['{}surface_uuid'.format(self.attribute_prefix)].data.foreach_get('value', uids, )
        
        uu = np.unique(uids)
        su = set([int(k) for k in self._surfaces_db.keys()])
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
        
        if(len(ii) and fix):
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
    
    # NOTE: ----------------------------------------- INTERNAL USE ONLY >>>
    
    def _set_target_orphan_mask_at_startup(self, ):
        self._ensure_attributes()
        
        me = self._target.data
        l = len(me.vertices)
        uids = np.zeros(l, dtype=int, )
        me.attributes['{}surface_uuid'.format(self.attribute_prefix)].data.foreach_get('value', uids, )
        
        uu = np.unique(uids)
        su = set([int(k) for k in self._surfaces_db.keys()])
        rm = []
        for u in uu:
            if(u not in su):
                rm.append(u)
        mask = np.zeros(l, dtype=bool, )
        for u in rm:
            m = uids == u
            # excluded / orphan = True, False is ok to work with.. False is default value
            mask[m] = True
        
        me = self._target.data
        me.attributes['{}private_orphan_mask'.format(self.attribute_prefix)].data.foreach_set('value', mask, )
    
    def _get_target_orphan_mask(self, ):
        me = self._target.data
        l = len(me.vertices)
        mask = np.zeros(l, dtype=bool, )
        me.attributes['{}private_orphan_mask'.format(self.attribute_prefix)].data.foreach_get('value', mask, )
        return mask
    
    def _get_target_active_mask(self, ):
        m = self._get_target_orphan_mask()
        return ~m
    
    def _get_target_shape_dtype_source_access_for_attribute(self, where, what, ):
        me = self._target.data
        l = len(me.vertices)
        
        if(what in self.attribute_map.keys()):
            at = self.attribute_map[what][0]
            if(at == 'FLOAT_VECTOR'):
                dt = float
                sh = (l, 3)
                source = where['{}{}'.format(self.attribute_prefix, what)].data
                access = 'vector'
            elif(at == 'FLOAT'):
                dt = float
                sh = l
                source = where['{}{}'.format(self.attribute_prefix, what)].data
                access = 'value'
            elif(at == 'INT'):
                dt = int
                sh = l
                source = where['{}{}'.format(self.attribute_prefix, what)].data
                access = 'value'
            elif(at == 'BOOLEAN'):
                dt = bool
                sh = l
                source = where['{}{}'.format(self.attribute_prefix, what)].data
                access = 'value'
            else:
                raise Exception("unhandled point attribute type")
        else:
            if(where.rna_type.name == 'Mesh Vertices'):
                if(what == 'co'):
                    dt = float
                    sh = (l, 3)
                    source = where
                    access = 'co'
                else:
                    raise Exception("unhandled vertex attribute type")
            else:
                raise Exception("unhandled data type")
        
        return sh, dt, source, access
    
    def _get_target_attribute_raw(self, where, what, ):
        sh, dt, source, access = self._get_target_shape_dtype_source_access_for_attribute(where, what, )
        a = np.zeros(sh, dtype=dt, ).ravel()
        source.foreach_get(access, a)
        if(type(sh) is not int and len(sh) > 1):
            # WATCH: reshape all multi dimensional, like vectors..  but i use single column in some cases. watch for errors!
            a.shape = (-1, sh[1])
        return a
    
    def _set_target_attribute_raw(self, where, what, values, ):
        sh, dt, source, access = self._get_target_shape_dtype_source_access_for_attribute(where, what, )
        source.foreach_set(access, values.ravel(), )
    
    # NOTE: ----------------------------------------- INTERNAL USE ONLY <<<
    
    # NOTE: `where`: mesh.attributes or mesh.vertices
    # NOTE: `what`: attribute name (without prefix) or vertex property name (only `co` is supported now)
    # NOTE: `mask`: optional, to speed up things, when i need many attribute at once, get mask first once, then just pass it around
    def _get_target_attribute_masked(self, where, what, mask=None, ):
        raw = self._get_target_attribute_raw(where, what, )
        if(mask is None):
            mask = self._get_target_active_mask()
        return raw[mask]
    
    # NOTE: `where`: mesh.attributes or mesh.vertices
    # NOTE: `what`: attribute name (without prefix) or vertex property name (only `co` is supported now)
    # NOTE: `values`: array of values, will be flatten before setting
    # NOTE: `mask`: optional, to speed up things, when i need many attribute at once, get mask first once, then just pass it around
    def _set_target_attribute_masked(self, where, what, values, mask=None, ):
        raw = self._get_target_attribute_raw(where, what, )
        if(mask is None):
            mask = self._get_target_active_mask()
        raw[mask] = values
        self._set_target_attribute_raw(where, what, raw, )
    
    # NOTE: convert vertex indices to masked data indices
    def _get_target_vertex_index_to_masked_index(self, indices, ):
        me = self._target.data
        l = len(me.vertices)
        ii = np.arange(l, dtype=int, )
        mask = self._get_target_active_mask()
        mii = np.arange(np.sum(mask), dtype=int, )
        ii[mask] = mii
        return ii[indices]
    
    # NOTE: convert masked data indices to vertex indices
    def _get_masked_index_to_target_vertex_index(self, indices, ):
        me = self._target.data
        l = len(me.vertices)
        ii = np.arange(l, dtype=int, )
        mask = self._get_target_active_mask()
        mii = ii[mask]
        return mii[indices]
    
    # ------------------------------------------------------------------ data system <<<
    # ------------------------------------------------------------------ property system >>>
    
    # @stopwatch
    def _get_prop_value(self, n, ):
        # NOTE: https://stackoverflow.com/questions/903130/hasattr-vs-try-except-block-to-deal-with-non-existent-attributes
        if(self._props.use_sync):
            # `getattr` should be faster then `hasattr` and `try...except`. props should not be `None` so i can use it.. i hope..
            ls = getattr(self, '_get_prop_sync_props', None, )
            if(ls is None):
                # this will run only once at first use
                ls = self._brush._sync
                setattr(self, '_get_prop_sync_props', ls, )
            # `ls` is tuple for fast search
            if(n in ls):
                return getattr(self._props.tool_default, n, )
        
        return getattr(self._brush, n, )
    
    # @stopwatch
    def _set_prop_value(self, n, v, ):
        if(self._props.use_sync):
            # `getattr` should be faster then `hasattr` and `try...except`. props should not be `None` so i can use it.. i hope..
            ls = getattr(self, '_get_prop_sync_props', None, )
            if(ls is None):
                # this will run only once at first use
                ls = self._brush._sync
                setattr(self, '_get_prop_sync_props', ls, )
            # `ls` is tuple for fast search
            if(n in ls):
                setattr(self._props.tool_default, n, v, )
                return
        
        setattr(self._brush, n, v, )
    
    # @stopwatch
    def _get_prop_group(self, n, ):
        if(self._props.use_sync):
            # `getattr` should be faster then `hasattr` and `try...except`. props should not be `None` so i can use it.. i hope..
            ls = getattr(self, '_get_prop_sync_props', None, )
            if(ls is None):
                # this will run only once at first use
                ls = self._brush._sync
                setattr(self, '_get_prop_sync_props', ls, )
            # `ls` is tuple for fast search
            if(n in ls):
                return self._props.tool_default
        return self._brush
    
    def _domain_aware_brush_radius(self, ):
        if(self.tool_domain == '2D'):
            return self._get_prop_value('radius_2d')
        r = self._get_prop_value('radius')
        u = self._get_prop_value('radius_units')
        if(u == 'VIEW'):
            if(self._mouse_3d is not None):
                r = self._get_prop_value('radius_px')
                r = self._radius_px_to_world(self._context_region, self._context_region_data, self._mouse_3d, r, )
        return r
    
    def _radius_px_to_world(self, region, rv3d, loc, px, ):
        w = region.width
        h = region.height
        c = Vector((w / 2, h / 2, ))
        a = Vector((c.x - (px / 2), c.y))
        b = Vector((c.x + (px / 2), c.y))
        a3 = view3d_utils.region_2d_to_location_3d(region, rv3d, a, loc)
        b3 = view3d_utils.region_2d_to_location_3d(region, rv3d, b, loc)
        d = ((a3.x - b3.x) ** 2 + (a3.y - b3.y) ** 2 + (a3.z - b3.z) ** 2) ** 0.5
        r = d / 2
        return r
    
    # ------------------------------------------------------------------ property system <<<
    
    # NOTE: seems to be unused, but good to have utility.. as long as i use ToolWidgets for drawing everything, screen gets redraw automatically
    def _tag_redraw(self, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()
    
    # ------------------------------------------------------------------ utilities >>>
    
    def _rotation_to(self, a, b):
        # http://stackoverflow.com/questions/1171849/finding-quaternion-representing-the-rotation-from-one-vector-to-another
        # https://github.com/toji/gl-matrix/blob/f0583ef53e94bc7e78b78c8a24f09ed5e2f7a20c/src/gl-matrix/quat.js#L54
        
        a = a.normalized()
        b = b.normalized()
        q = Quaternion()
        
        tmpvec3 = Vector()
        xUnitVec3 = Vector((1, 0, 0))
        yUnitVec3 = Vector((0, 1, 0))
        
        dot = a.dot(b)
        if(dot < -0.999999):
            tmpvec3 = xUnitVec3.cross(a)
            if(tmpvec3.length < 0.000001):
                tmpvec3 = yUnitVec3.cross(a)
            tmpvec3.normalize()
            q = Quaternion(tmpvec3, math.pi)
        elif(dot > 0.999999):
            q.x = 0
            q.y = 0
            q.z = 0
            q.w = 1
        else:
            tmpvec3 = a.cross(b)
            q.x = tmpvec3[0]
            q.y = tmpvec3[1]
            q.z = tmpvec3[2]
            q.w = 1 + dot
            q.normalize()
        return q
    
    def _direction_to_rotation(self, direction, up=Vector((0.0, 1.0, 0.0, )), ):
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
    
    def _point_at(self, loc, target, roll=0.0, ):
        # https://blender.stackexchange.com/questions/5210/pointing-the-camera-in-a-particular-direction-programmatically
        # direction = target - loc
        direction = target
        # direction.negate()
        # q = direction.to_track_quat('-Z', 'Y')
        q = direction.to_track_quat('Z', 'Y')
        q = q.to_matrix().to_4x4()
        if(roll != 0.0):
            rm = Matrix.Rotation(roll, 4, 'Z')
            m = q @ rm
            _, q, _ = m.decompose()
        return q
    
    def _apply_matrix(self, m, loc, nor=None, ):
        if(type(loc) is Vector):
            loc = m @ loc
            if(nor is not None):
                l, r, s = m.decompose()
                mr = r.to_matrix().to_4x4()
                nor = mr @ nor
        else:
            def apply_matrix(m, vs, ns=None, ):
                vs.shape = (-1, 3)
                vs = np.c_[vs, np.ones(vs.shape[0])]
                vs = np.dot(m, vs.T)[0:3].T.reshape((-1))
                vs.shape = (-1, 3)
                if(ns is not None):
                    _, rot, _ = m.decompose()
                    rmat = rot.to_matrix().to_4x4()
                    ns.shape = (-1, 3)
                    ns = np.c_[ns, np.ones(ns.shape[0])]
                    ns = np.dot(rmat, ns.T)[0:3].T.reshape((-1))
                    ns.shape = (-1, 3)
                vs = vs.astype(np.float32)
                if(ns is not None):
                    ns = ns.astype(np.float32)
                return vs, ns
            
            loc, nor = apply_matrix(m, loc, nor, )
        
        return loc, nor
    
    def _apply_matrix_np(self, matrix, vs, ns=None, ):
        _m = np.array(matrix, dtype=float, )
        _vs = np.c_[vs, np.ones(len(vs), dtype=vs.dtype, )]
        _vs = np.dot(_m, _vs.T)[0:4].T.reshape((-1, 4))
        _vs = _vs[:, :3]
        if(ns is not None):
            _, _r, _ = m.decompose()
            _m = np.array(r.to_matrix().to_4x4(), dtype=float, )
            _ns = np.c_[ns, np.ones(len(ns), dtype=ns.dtype, )]
            _ns = np.dot(_m, _ns.T)[0:4].T.reshape((-1, 4))
            _ns = _ns[:, :3]
        return _vs, _ns
    
    def _distance_range(self, vertices, point, radius, ):
        # mask out points in cube around point of side 2x radius
        mask = np.array((point[0] - radius <= vertices[:, 0]) & (vertices[:, 0] <= point[0] + radius) & (point[1] - radius <= vertices[:, 1]) & (vertices[:, 1] <= point[1] + radius) & (point[2] - radius <= vertices[:, 2]) & (vertices[:, 2] <= point[2] + radius), dtype=np.bool, )
        indices = np.arange(len(vertices))
        indices = indices[mask]
        vs = vertices[mask]
        # distance from point for all vertices
        d = ((vs[:, 0] - point[0]) ** 2 + (vs[:, 1] - point[1]) ** 2 + (vs[:, 2] - point[2]) ** 2) ** 0.5
        # remove all with distance > radius
        i = np.arange(len(vs))
        i = i[(d <= radius)]
        return vs[i], d[i], indices[i]
    
    def _distance_ranges(self, vertices, points, radius, ):
        # duplicate vertices points length times
        vs = np.full((len(points), ) + vertices.shape, vertices, )
        # calculate distances per point
        d = ((vs[:, :, 0] - points[:, 0].reshape(-1, 1)) ** 2 + (vs[:, :, 1] - points[:, 1].reshape(-1, 1)) ** 2 + (vs[:, :, 2] - points[:, 2].reshape(-1, 1)) ** 2) ** 0.5
        # select points
        rvs = []
        rd = []
        ri = []
        # indices
        a = np.arange(len(vertices))
        for i in range(len(points)):
            # select indices within radius
            ai = a[(d[i] <= radius)]
            # select data
            rvs.append(vs[i][ai])
            rd.append(d[i][ai])
            ri.append(ai)
        return rvs, rd, ri
    
    def _distance_vectors_2d(self, a, b, ):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
    
    def _distance_vectors_3d(self, a, b, ):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
    
    # ------------------------------------------------------------------ utilities <<<
    # ------------------------------------------------------------------ space conversions >>>
    
    def _world_to_active_surface_space(self, loc, nor=None, ):
        m = self._mouse_active_surface_matrix
        if(m is None):
            raise Exception("_world_to_active_surface_space: 'self._mouse_active_surface_matrix' is None (mouse is outside of any surface)")
        # NOTE: loc, nor either Vector or ndarray, `_apply_matrix` does both
        return self._apply_matrix(m.inverted(), loc, nor, )
    
    def _active_surface_to_world_space(self, loc, nor=None, ):
        m = self._mouse_active_surface_matrix
        if(m is None):
            raise Exception("_active_surface_to_world_space: 'self._mouse_active_surface_matrix' is None (mouse is outside of any surface)")
        # NOTE: loc, nor either Vector or ndarray, `_apply_matrix` does both
        return self._apply_matrix(m, loc, nor, )
    
    def _world_length_to_active_surface_space(self, l, ):
        m = self._mouse_active_surface_matrix
        if(m is None):
            raise Exception("_world_length_to_active_surface_space: 'self._mouse_active_surface_matrix' is None (mouse is outside of any surface)")
        
        m = m.inverted()
        _, _, s = m.decompose()
        ms = Matrix(((s[0], 0.0, 0.0, 0.0), (0.0, s[1], 0.0, 0.0), (0.0, 0.0, s[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        v = Vector((0.0, 0.0, l))
        v = ms @ v
        return v.length
    
    def _world_to_surfaces_space(self, loc, nor=None, uid=None, ):
        if(uid is None):
            # no uid array, use active
            return self._world_to_active_surface_space(loc, nor, )
        
        if(type(loc) == Vector):
            # single location, one matrix
            u = int(uid)
            o = bpy.data.objects.get(self._surfaces_db[u])
            m = o.matrix_world.copy()
            # apply and done
            return self._apply_matrix(m.inverted(), loc, nor, )
        else:
            # array of locations, find matrix for each uid
            # create return arrays
            r_loc = np.zeros(loc.shape, dtype=loc.dtype, )
            if(nor is not None):
                r_nor = np.zeros(nor.shape, dtype=nor.dtype, )
            else:
                r_nor = None
            # find unique uuids
            uu = np.unique(uid)
            for i, u in enumerate(uu):
                # to integer so it matches dict key
                u = int(u)
                # get matrix
                o = bpy.data.objects.get(self._surfaces_db[u])
                m = o.matrix_world.copy()
                
                # NOTE: the only difference between `_world_to_surfaces_space` and `_surfaces_to_world_space`
                m = m.inverted()
                
                # uuid mask
                mask = uid == u
                # apply on masked
                if(nor is not None):
                    vs, ns = self._apply_matrix(m, loc[mask], nor[mask], )
                    # put to return array
                    r_loc[mask] = vs
                    r_nor[mask] = ns
                else:
                    vs, _ = self._apply_matrix(m, loc[mask], None, )
                    # put to return array
                    r_loc[mask] = vs
            
            return r_loc, r_nor
    
    def _surfaces_to_world_space(self, loc, nor=None, uid=None, ):
        if(uid is None):
            # no uid array, use active
            return self._world_to_active_surface_space(loc, nor, )
        
        if(type(loc) == Vector):
            # single location, one matrix
            u = int(uid)
            o = bpy.data.objects.get(self._surfaces_db[u])
            m = o.matrix_world.copy()
            # apply and done
            # NOTE: i will leave this here. it took me 3 hours of desperate debugging because all math was clearly right, only to find, when i looked here in utmost despair, i left `inverted()` from `_world_to_surfaces_space` when i copied whole function to do its inversion..
            # return self._apply_matrix(m.inverted(), loc, nor, )
            return self._apply_matrix(m, loc, nor, )
        else:
            # array of locations, find matrix for each uid
            # create return arrays
            r_loc = np.zeros(loc.shape, dtype=loc.dtype, )
            if(nor is not None):
                r_nor = np.zeros(nor.shape, dtype=nor.dtype, )
            else:
                r_nor = None
            # find unique uuids
            uu = np.unique(uid)
            for i, u in enumerate(uu):
                # to integer so it matches dict key
                u = int(u)
                # get matrix
                o = bpy.data.objects.get(self._surfaces_db[u])
                m = o.matrix_world.copy()
                
                # # NOTE: the only difference between `_world_to_surfaces_space` and `_surfaces_to_world_space`
                # m = m.inverted()
                
                # uuid mask
                mask = uid == u
                # apply on masked
                if(nor is not None):
                    vs, ns = self._apply_matrix(m, loc[mask], nor[mask], )
                    # put to return array
                    r_loc[mask] = vs
                    r_nor[mask] = ns
                else:
                    vs, _ = self._apply_matrix(m, loc[mask], None, )
                    # put to return array
                    r_loc[mask] = vs
            
            return r_loc, r_nor
    
    def _world_length_to_surfaces_space(self, l, uid=None, ):
        if(uid is None):
            # no uid array, use active
            return self._world_length_to_active_surface_space(l, )
        
        if(type(l) == float):
            u = int(uid)
            o = bpy.data.objects.get(self._surfaces_db[u])
            m = o.matrix_world.copy()
            m = m.inverted()
            _, _, s = m.decompose()
            ms = Matrix(((s[0], 0.0, 0.0, 0.0), (0.0, s[1], 0.0, 0.0), (0.0, 0.0, s[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
            v = Vector((0.0, 0.0, l))
            v = ms @ v
            return v.length
        else:
            # create return array
            r_length = np.zeros(l.shape, dtype=l.dtype, )
            uu = np.unique(uid)
            for i, u in enumerate(uu):
                # to integer so it matches dict key
                u = int(u)
                # get matrix
                o = bpy.data.objects.get(self._surfaces_db[u])
                m = o.matrix_world.copy()
                m = m.inverted()
                _, _, s = m.decompose()
                m = Matrix(((s[0], 0.0, 0.0, 0.0), (0.0, s[1], 0.0, 0.0), (0.0, 0.0, s[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
                # uuid mask
                mask = uid == u
                # vectors
                vs = np.zeros((len(mask), 3), dtype=float, )
                vs[:, 2] = l[mask]
                vs, _ = self._apply_matrix(m, vs, None, )
                # WATCH: do i need to calculate vector magnitude? if i just scale? all zero vectors except z axis? i think not.. reading back z should be enough
                # NOTE: i THINK i will not use this anyway, it is here for the sake of completeness. i will use active surface length. i THINK..
                # ls = np.sqrt(np.dot(vs, vs))
                # put to return array
                r_length[mask] = vs[:, 2]
            
            return r_length
    
    # ------------------------------------------------------------------ space conversions <<<
    # ------------------------------------------------------------------ widgets utilities <<<
    
    '''
    def _widgets_compute_fixed_scale_3d(self, region, rv3d, loc, size, ):
        loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
        loc2_2d = Vector((loc_2d.x, loc_2d.y + size))
        loc2_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, loc2_2d, loc)
        s = ((loc.x - loc2_3d.x) ** 2 + (loc.y - loc2_3d.y) ** 2 + (loc.z - loc2_3d.z) ** 2) ** 0.5
        return s
    '''
    
    def _widgets_compute_fixed_scale_3d(self, region, rv3d, loc, size, ):
        w = region.width
        h = region.height
        c = Vector((w / 2, h / 2, ))
        a = c - Vector((size / 2, 0.0))
        b = c + Vector((size / 2, 0.0))
        a3 = view3d_utils.region_2d_to_location_3d(region, rv3d, a, loc)
        b3 = view3d_utils.region_2d_to_location_3d(region, rv3d, b, loc)
        s = ((a3.x - b3.x) ** 2 + (a3.y - b3.y) ** 2 + (a3.z - b3.z) ** 2) ** 0.5
        return s
    
    def _widgets_compute_surface_matrix_components_3d(self, loc, nor, radius, ):
        mt = Matrix.Translation(loc)
        mr = self._direction_to_rotation(nor).to_matrix().to_4x4()
        ms = Matrix(((radius, 0.0, 0.0, 0.0), (0.0, radius, 0.0, 0.0), (0.0, 0.0, radius, 0.0), (0.0, 0.0, 0.0, 1.0)))
        return mt, mr, ms
    
    def _widgets_compute_surface_matrix_scale_component_3d(self, radius, ):
        ms = Matrix(((radius, 0.0, 0.0, 0.0), (0.0, radius, 0.0, 0.0), (0.0, 0.0, radius, 0.0), (0.0, 0.0, 0.0, 1.0)))
        return ms
    
    def _widgets_compute_surface_matrix_scale_component_xy_3d(self, radius, ):
        ms = Matrix(((radius, 0.0, 0.0, 0.0), (0.0, radius, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
        return ms
    
    def _widgets_compute_billboard_rotation_matrix(self, region, rv3d, ):
        _, q, _ = rv3d.view_matrix.inverted().decompose()
        rm = q.to_matrix().to_4x4()
        return rm
    
    def _widgets_compute_minimal_widget_size_for_radius_3d(self, region, rv3d, loc, radius, minimal_size=-1, ):
        # loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
        # n_2d = loc_2d + Vector((100, 0, ))
        # n_2d_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, n_2d, loc)
        # n_3d = n_2d_3d - loc
        # n_3d.normalize()
        # loc_offset = loc + (n_3d * radius)
        # a = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
        # b = view3d_utils.location_3d_to_region_2d(region, rv3d, loc_offset, )
        # size = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
        
        # NOTE: take it from center of viewport, and offset just 10px so i should always fit inside viewport.. hopefuly, who would have smaller viewport anyway..
        w = region.width
        h = region.height
        c = Vector((w / 2, h / 2, ))
        cc = c + Vector((10, 0.0))
        c3 = view3d_utils.region_2d_to_location_3d(region, rv3d, c, loc)
        cc3 = view3d_utils.region_2d_to_location_3d(region, rv3d, cc, loc)
        n3 = cc3 - c3
        n3.normalize()
        o3 = c3 + (n3 * radius)
        o2 = view3d_utils.location_3d_to_region_2d(region, rv3d, o3, )
        size = ((c.x - o2.x) ** 2 + (c.y - o2.y) ** 2) ** 0.5
        
        if(minimal_size < 0):
            # NOTE: default: 2x fixed radius
            minimal_size = self._theme._fixed_radius * 2
        
        if(size < minimal_size):
            loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
            loc2_2d = Vector((loc_2d.x, loc_2d.y + (self._theme._fixed_radius * 2)))
            loc2_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, loc2_2d, loc)
            radius = ((loc.x - loc2_3d.x) ** 2 + (loc.y - loc2_3d.y) ** 2 + (loc.z - loc2_3d.z) ** 2) ** 0.5
        
        return radius
    
    def _widgets_compute_minimal_widget_size_for_radius_2d(self, region, rv3d, loc, radius, minimal_size=-1, ):
        # loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
        # n_2d = loc_2d + Vector((100, 0, ))
        # n_2d_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, n_2d, loc)
        # n_3d = n_2d_3d - loc
        # n_3d.normalize()
        # loc_quasi_2d_offset = loc + (n_3d * radius)
        # c = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
        # q = view3d_utils.location_3d_to_region_2d(region, rv3d, loc_quasi_2d_offset, )
        # radius = ((c.x - q.x) ** 2 + (c.y - q.y) ** 2) ** 0.5
        
        # NOTE: take it from center of viewport, and offset just 10px so i should always fit inside viewport.. hopefuly, who would have smaller viewport anyway..
        w = region.width
        h = region.height
        c = Vector((w / 2, h / 2, ))
        cc = c + Vector((10, 0.0))
        c3 = view3d_utils.region_2d_to_location_3d(region, rv3d, c, loc)
        cc3 = view3d_utils.region_2d_to_location_3d(region, rv3d, cc, loc)
        n3 = cc3 - c3
        n3.normalize()
        o3 = c3 + (n3 * radius)
        o2 = view3d_utils.location_3d_to_region_2d(region, rv3d, o3, )
        radius = ((c.x - o2.x) ** 2 + (c.y - o2.y) ** 2) ** 0.5
        
        if(minimal_size < 0):
            # NOTE: default: 2x fixed radius
            minimal_size = self._theme._fixed_radius * 2
        
        if(radius < minimal_size):
            radius = minimal_size
        
        return radius
    
    # NOTE: return tuples, tuples are faster to work with and existing list can be extended with tuples (which is also faster operation)
    
    def _widgets_fabricate_no_entry_sign(self, event, ):
        woc = self._theme._no_entry_sign_color
        
        # no entry sign coords
        x, y = event.mouse_region_x, event.mouse_region_y
        c = (x, y, )
        v = 0.7071067690849304
        a = (x + self._theme._no_entry_sign_size * v, y + self._theme._no_entry_sign_size * -v, )
        b = (x + self._theme._no_entry_sign_size * -v, y + self._theme._no_entry_sign_size * v, )
        
        ls = (
            # no entry sign
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {
                    'center': c,
                    'radius': self._theme._no_entry_sign_size,
                    'steps': self._theme._circle_steps * 2,
                    'color': woc,
                    'thickness': self._theme._no_entry_sign_thickness,
                }
            },
            {
                'function': 'thick_line_2d',
                'arguments': {
                    'a': a,
                    'b': b,
                    'color': woc,
                    'thickness': self._theme._no_entry_sign_thickness,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_fixed_size_cross_cursor_3d(self, mt, mr, ms, radius, woc, wfc, ):
        m = mt @ mr @ ms
        
        ms = self._widgets_compute_surface_matrix_scale_component_3d(radius / 2, )
        cm = mt @ mr @ ms
        
        ls = (
            # cursor inner circle
            {
                'function': 'circle_outline_3d',
                'arguments': {
                    'matrix': cm,
                    'steps': self._theme._circle_steps,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
            {
                'function': 'circle_fill_3d',
                'arguments': {
                    'matrix': cm,
                    'steps': self._theme._circle_steps,
                    'color': wfc,
                }
            },
            # cursor outer cross
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (-1.0, 0.0, 0.0, ),
                    'b': (-0.5, 0.0, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (0.0, -1.0, 0.0, ),
                    'b': (0.0, -0.5, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (0.5, 0.0, 0.0, ),
                    'b': (1.0, 0.0, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (0.0, 0.5, 0.0, ),
                    'b': (0.0, 1.0, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_center_dot_3d(self, region, rv3d, loc, mt, mr, woc, ):
        r = self._theme._fixed_center_dot_radius * 2
        s = self._widgets_compute_fixed_scale_3d(region, rv3d, loc, r, )
        mr = self._widgets_compute_billboard_rotation_matrix(region, rv3d, )
        ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
        m = mt @ mr @ ms
        ls = (
            {
                'function': 'dot_shader_2_3d',
                'arguments': {
                    'matrix': m,
                    'scale_factor': s,
                    'color': woc,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_direction_triangle_3d(self, loc, nor, radius, woc, ):
        mt = Matrix.Translation(loc)
        mr = self._rotation_to(Vector((0.0, 0.0, 1.0)), nor).to_matrix().to_4x4()
        
        s = radius / 10
        ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
        
        x = mr @ Vector((1.0, 0.0, 0.0))
        y = mr @ Vector((0.0, 1.0, 0.0))
        z = mr @ Vector((0.0, 0.0, 1.0))
        
        d = self._mouse_3d_direction
        if(self._get_prop_value('use_direction_interpolation')):
            d = self._mouse_3d_direction_interpolated
        
        def project_on_plane(p, n, q, ):
            return q - Vector(q - p).dot(n) * n
        
        y2 = project_on_plane(Vector(), z, y)
        d2 = project_on_plane(Vector(), z, d)
        
        q = self._rotation_to(y2, d2).to_matrix().to_4x4()
        
        tm = mt @ (q @ mr) @ ms
        to = (0.0, (radius / s) + 0.5, 0.0)
        
        ls = (
            # direction triangle
            {
                'function': 'triangle_outline_3d',
                'arguments': {
                    'offset': to,
                    'matrix': tm,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
            {
                'function': 'triangle_fill_3d',
                'arguments': {
                    'offset': to,
                    'matrix': tm,
                    'color': woc,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_radius_with_falloff_3d(self, mt, mr, ms, radius, falloff, woc, wfc, ):
        m = mt @ mr @ ms
        
        r = radius * falloff
        ms = self._widgets_compute_surface_matrix_scale_component_3d(r, )
        fm = mt @ mr @ ms
        
        ls = (
            # circle
            {
                'function': 'circle_outline_3d',
                'arguments': {
                    'matrix': m,
                    'steps': self._theme._circle_steps,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
            {
                'function': 'circle_fill_3d',
                'arguments': {
                    'matrix': m,
                    'steps': self._theme._circle_steps,
                    'color': wfc,
                }
            },
            # falloff circle
            {
                'function': 'circle_outline_dashed_3d',
                'arguments': {
                    'matrix': fm,
                    'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                    'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_fixed_size_hints_loc_nor_lines_3d(self, context, event, loc, w_locations, w_normals, woc, ):
        a = np.array(w_locations, dtype=float, )
        
        c = Vector((event.mouse_region_x, event.mouse_region_y, ))
        n = c + Vector((self._theme._fixed_radius, 0, ))
        n = view3d_utils.region_2d_to_location_3d(context.region, context.region_data, n, loc)
        l = Vector(n - loc).length
        b = a + (np.array(w_normals, dtype=float, ) * l)
        
        vs = np.concatenate([a, b, ])
        vs = vs.astype(np.float32)
        i = np.arange(len(a))
        es = np.c_[i, i + len(a)]
        es = es.astype(np.int32)
        
        woc = self._theme._outline_color_helper_hint
        ls = (
            {
                'function': 'multiple_thick_lines_3d',
                'arguments': {
                    'vertices': vs,
                    'indices': es,
                    'matrix': Matrix(),
                    'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                    'thickness': self._theme._outline_thickness_helper,
                },
            },
        )
        return ls
    
    def _widgets_fabricate_radius_with_falloff_and_dot_2d(self, coord, radius, falloff, woc, wfc, ):
        ls = (
            # circle
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius,
                    'steps': self._theme._circle_steps,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
            {
                'function': 'circle_fill_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius,
                    'steps': self._theme._circle_steps,
                    'color': wfc,
                }
            },
            # falloff circle
            {
                'function': 'circle_thick_outline_dashed_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius * falloff,
                    'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                    'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            # center dot
            {
                # 'function': 'dot_shader_2d',
                'function': 'dot_shader_2_2d',
                'arguments': {
                    'center': coord,
                    'diameter': self._theme._fixed_center_dot_radius * 2,
                    'color': woc,
                },
            },
        )
        return ls
    
    def _widgets_fabricate_fixed_size_cross_cursor_and_dot_2d(self, coord, woc, wfc, ):
        c = coord
        r = self._theme._fixed_radius
        h = r / 2
        ls = (
            # cursor inner circle
            {
                'function': 'circle_thick_outline_2d',
                'arguments': {
                    'center': c,
                    'radius': h,
                    'steps': self._theme._circle_steps,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
            {
                'function': 'circle_fill_2d',
                'arguments': {
                    'center': c,
                    'radius': h,
                    'steps': self._theme._circle_steps,
                    'color': wfc,
                }
            },
            # cursor outer cross
            {
                'function': 'thick_line_2d',
                'arguments': {
                    'a': (-r + c[0], c[1], ),
                    'b': (-h + c[0], c[1], ),
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_2d',
                'arguments': {
                    'a': (c[0], -r + c[1], ),
                    'b': (c[0], -h + c[1], ),
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_2d',
                'arguments': {
                    'a': (h + c[0], c[1], ),
                    'b': (r + c[0], c[1], ),
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_2d',
                'arguments': {
                    'a': (c[0], h + c[1], ),
                    'b': (c[0], r + c[1], ),
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            # center dot
            {
                'function': 'dot_shader_2_2d',
                'arguments': {
                    'center': coord,
                    'diameter': self._theme._fixed_center_dot_radius * 2,
                    'color': woc,
                },
            },
        )
        return ls
    
    def _widgets_fabricate_direction_triangle_2d(self, coord, radius, woc, ):
        d = self._mouse_2d_direction
        if(self._get_prop_value('use_direction_interpolation')):
            d = self._mouse_2d_direction_interpolated
        
        ls = (
            # direction triangle
            {
                'function': 'triangle_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius / 10,
                    'direction': d,
                    'y_offset': radius + ((radius / 10) / 2),
                    'color': woc,
                }
            },
            {
                'function': 'triangle_outline_2d',
                'arguments': {
                    'center': coord,
                    'radius': radius / 10,
                    'direction': d,
                    'y_offset': radius + ((radius / 10) / 2),
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_fixed_size_hints_loc_nor_lines_2d(self, context, event, w_locations, w_normals, woc, ):
        a = np.array(self._w_locations, dtype=float, )
        
        region = context.region
        rv3d = context.region_data
        
        loc = Vector(self._w_locations[0])
        c = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
        
        n = c + Vector((self._theme._fixed_radius, 0, ))
        n = view3d_utils.region_2d_to_location_3d(region, rv3d, n, loc)
        l = Vector(n - loc).length
        
        b = a + (np.array(self._w_normals, dtype=float, ) * l)
        
        vs = np.concatenate([a, b, ])
        vs = vs.astype(np.float32)
        i = np.arange(len(a))
        es = np.c_[i, i + len(a)]
        es = es.astype(np.int32)
        
        ls = (
            {
                'function': 'multiple_thick_lines_3d',
                'arguments': {
                    'vertices': vs,
                    'indices': es,
                    'matrix': Matrix(),
                    'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                    'thickness': self._theme._outline_thickness_helper,
                },
            },
        )
        return ls
    
    def _widgets_fabricate_hints_origin_destination_lines(self, w_origins, w_destinations, matrix, woc, ):
        a = np.array(w_origins, dtype=float, )
        b = np.array(w_destinations, dtype=float, )
        
        vs = np.concatenate([a, b, ])
        vs = vs.astype(np.float32)
        i = np.arange(len(a))
        es = np.c_[i, i + len(a)]
        es = es.astype(np.int32)
        
        ls = (
            {
                'function': 'multiple_thick_lines_3d',
                'arguments': {
                    'vertices': vs,
                    'indices': es,
                    'matrix': matrix,
                    'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                    'thickness': self._theme._outline_thickness_helper,
                },
            },
        )
        return ls
    
    def _widgets_fabricate_tooltip(self, coords, message, ):
        ui_scale = bpy.context.preferences.system.ui_scale
        coords = (coords[0] + (8 * ui_scale), coords[1] + self._theme._text_size + ((8 * ui_scale) * 2), )
        ls = (
            {
                'function': 'fancy_tooltip_2d',
                'arguments': {
                    'coords': coords,
                    'text': message,
                    'offset': (0, 0),
                    'align': None,
                    'size': self._theme._text_size,
                    'color': self._theme._text_color,
                    'shadow': True,
                    'padding': 8 * self._theme._ui_scale,
                    'steps': self._theme._circle_steps,
                    'radius': 4 * self._theme._ui_scale,
                    'bgfill': self._theme._text_tooltip_background_color,
                    'bgoutline': self._theme._text_tooltip_outline_color,
                    'thickness': self._theme._text_tooltip_outline_thickness,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_fixed_size_crosshair_cursor_3d(self, mt, mr, ms, woc, ):
        m = mt @ mr @ ms
        ls = (
            # cursor outer cross
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (-1.0, 0.0, 0.0, ),
                    'b': (-0.5, 0.0, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (0.0, -1.0, 0.0, ),
                    'b': (0.0, -0.5, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (0.5, 0.0, 0.0, ),
                    'b': (1.0, 0.0, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': (0.0, 0.5, 0.0, ),
                    'b': (0.0, 1.0, 0.0, ),
                    'matrix': m,
                    'color': woc,
                    'thickness': self._theme._outline_thickness_helper,
                }
            },
        )
        return ls
    
    # ------------------------------------------------------------------ widgets utilities <<<
    # ------------------------------------------------------------------ custom ui >>>
    
    @verbose
    def _integration_on_invoke(self, context, event, ):
        if(ToolSession.active):
            return
        ToolSession.active = True
        t = context.workspace.tools.from_space_view3d_mode(context.mode).idname
        if(t in get_all_tool_ids()):
            # NOTE: there was error in previous tool, it did not set any of built in tools.. reset to default
            t = 'builtin.select_box'
        ToolSession.user_tool = t
        ToolSession.user_select = [o.name for o in bpy.context.selected_objects]
        ToolSession.user_active = None
        if(bpy.context.view_layer.objects.active is not None):
            ToolSession.user_active = bpy.context.view_layer.objects.active.name
        
        # NOTE: do i need that?
        if(self._emitter.hide_viewport):
            self._emitter.hide_viewport = False
        
        for o in self._surfaces:
            if(o.hide_viewport):
                o.hide_viewport = False
        if(self._target.hide_viewport):
            self._target.hide_viewport = False
        
        from ..ui import ui_manual
        ui_manual.modal_hijacking(context)
        
        bpy.ops.ed.undo_push(message="Manual Mode: Initialize", )
        
        # set active tool to our newly hijacked registered interface
        bpy.ops.wm.tool_set_by_id(name=self.tool_id)
            
        # deselect all
        for i in bpy.context.scene.objects:
            i.select_set(False)
        # make target active/unselected object
        self._target.select_set(True)
        bpy.context.view_layer.objects.active = self._target
        self._target.select_set(False)
    
    @verbose
    def _integration_on_finish(self, context, event, ):
        if(not ToolSession.active):
            return
        ToolSession.active = False
        
        from ..ui import ui_manual
        ui_manual.modal_hijack_restore(context)
        
        bpy.ops.ed.undo_push(message="Manual Mode: Deinitialize", )
        
        ToolSessionCache.free()
        
        # statusbar text
        bpy.context.workspace.status_text_set(text=None, )
        
        for n in ToolSession.user_select:
            o = bpy.data.objects.get(n)
            if(o is not None):
                o.select_set(True)
        if(ToolSession.user_active):
            o = bpy.data.objects.get(ToolSession.user_active)
            bpy.context.view_layer.objects.active = o
        bpy.ops.wm.tool_set_by_id(name=ToolSession.user_tool)
        
        ToolSession.reset()
    
    # ------------------------------------------------------------------ custom ui <<<


# DONE: check if fully numpyfied storing opration is faster than loop even with low amount of inserted points, and if so, rewrite all storing operations. something like `_store_one_np` and `_store_many_np` with possibility of callback at the end for various deviations from standard storing operation, like mouse direction aligned tools etc.. -->> non-numpyfied is faster for single verts (4x @25k points)
# NOTTODO: creation brushes to draw points on just created brushes? until next stroke? or tool change? or timed (timed maybe not, having a lot of timers in background is not a good idea)? --> too messy
# NOTTODO: mark new created point with dot? drawn as long as lmb is down? --> it will get really messy, too much on screen. created models are more important than fancy drawings..
# DONE: numpyfied store: dot, pose, path, chain, spatter -->> non-numpyfied is faster for single verts (4x @25k points)
# DONE: numpyfied store: spray, spray aligned, lasso -->> numpyfied is faster for batchs of verts
# DONE: add `_store_vertex(loc, nor)` as non-numpyfied variant at one place with similar before/after mechanism so i don;t need special and separate `_store` at almost each tool
class SCATTER5_OT_create_mixin():
    # ------------------------------------------------------------------ generate >>>
    
    # TODO: i am getting local coords here, got to put it back to global so whole calculation works. not ideal.. opportunity for optimization, or would it work if i swap to local after generation?
    def _gen_rotation(self, n, vs, ns, uids, ):
        vs, ns = self._surfaces_to_world_space(vs, ns, uids, )
        # bsb = self._brush
        
        l = len(vs)
        if(self._get_prop_value('rotation_align') == 'GLOBAL_Z_AXIS'):
            nors = [Vector((0.0, 0.0, 1.0, )) for i in range(l)]
        elif(self._get_prop_value('rotation_align') == 'LOCAL_Z_AXIS'):
            _vs = np.zeros((l, 3), dtype=float, )
            _ns = np.full((l, 3), (0.0, 0.0, 1.0, ), dtype=float, )
            _, _ns = self._surfaces_to_world_space(_vs, _ns, uids, )
            nors = [Vector(n) for i, n in enumerate(_ns)]
        elif(self._get_prop_value('rotation_align') == 'SURFACE_NORMAL'):
            nors = [Vector(e) for e in ns]
        
        def direction_to_rotation_with_m3x3(direction, up=Vector((0.0, 1.0, 0.0, )), ):
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
        
        if(self._get_prop_value('rotation_up') == 'LOCAL_Y_AXIS'):
            _vs = np.zeros((l, 3), dtype=float, )
            _ns = np.full((l, 3), (0.0, 1.0, 0.0, ), dtype=float, )
            _, _ns = self._surfaces_to_world_space(_vs, _ns, uids, )
            ups = [Vector(n) for i, n in enumerate(_ns)]
            
            qs = []
            for i in range(l):
                q = direction_to_rotation_with_m3x3(nors[i], ups[i], )
                qs.append(q)
                # # DEBUG
                # debug.points(self._target, [vs[i], vs[i], vs[i], ], [ns[i], nors[i], ups[i], ])
                # # DEBUG
        elif(self._get_prop_value('rotation_up') == 'GLOBAL_Y_AXIS'):
            qs = []
            for i in range(l):
                q = direction_to_rotation_with_m3x3(nors[i], )
                qs.append(q)
        
        rng = np.random.default_rng()
        _random_numbers = rng.random((l, 3, ), )
        
        eb = self._get_prop_value('rotation_base')
        er = self._get_prop_value('rotation_random')
        err = []
        for i in range(l):
            err.append(Euler((er.x * _random_numbers[i][0], er.y * _random_numbers[i][1], er.z * _random_numbers[i][2], ), ))
        
        if(type(uids) == int):
            uids = [uids, ]
        
        fq = []
        for i in range(l):
            uid = uids[i]
            mwi = bpy.data.objects.get(self._surfaces_db[uid]).matrix_world.inverted()
            _, cr, _ = mwi.decompose()
            
            q = Quaternion()
            q.rotate(eb)
            q.rotate(err[i])
            q.rotate(qs[i])
            q.rotate(cr)
            fq.append(q)
        
        _private_r_align = np.zeros(l, dtype=int, )
        if(self._get_prop_value('rotation_align') == 'GLOBAL_Z_AXIS'):
            _private_r_align = _private_r_align + 2
        elif(self._get_prop_value('rotation_align') == 'LOCAL_Z_AXIS'):
            _private_r_align = _private_r_align + 1
        elif(self._get_prop_value('rotation_align') == 'SURFACE_NORMAL'):
            pass
        
        _private_r_up = np.zeros(l, dtype=int, )
        if(self._get_prop_value('rotation_up') == 'LOCAL_Y_AXIS'):
            _private_r_up = _private_r_up + 1
        elif(self._get_prop_value('rotation_up') == 'GLOBAL_Y_AXIS'):
            pass
        
        _private_r_base = np.full((l, 3), self._get_prop_value('rotation_base'), dtype=float, )
        _private_r_random = np.full((l, 3), self._get_prop_value('rotation_random'), dtype=float, )
        
        self._private_r_align = _private_r_align
        self._private_r_up = _private_r_up
        self._private_r_base = _private_r_base
        self._private_r_random = _private_r_random
        self._private_r_random_random = _random_numbers
        
        return fq
    
    def _regenerate_rotation_from_attributes(self, indices, ):
        # this will load all attributes for rotation (set by create brushes), calculate again and set back final rotations for indices
        # if some attribute has bee changed before running, it will change resulting rotation, and brush doing it can just change attribute and call function.. in theory..
        
        # get attributes for ALL points
        me = self._target.data
        l = len(me.vertices)
        
        _vs = self._get_target_attribute_masked(me.vertices, 'co', )
        _ns = self._get_target_attribute_masked(me.attributes, 'normal', )
        _rotation = self._get_target_attribute_masked(me.attributes, 'rotation', )
        _private_r_align = self._get_target_attribute_masked(me.attributes, 'private_r_align', )
        _private_r_align_vector = self._get_target_attribute_masked(me.attributes, 'private_r_align_vector', )
        _private_r_up = self._get_target_attribute_masked(me.attributes, 'private_r_up', )
        _private_r_up_vector = self._get_target_attribute_masked(me.attributes, 'private_r_up_vector', )
        _private_r_base = self._get_target_attribute_masked(me.attributes, 'private_r_base', )
        _private_r_random = self._get_target_attribute_masked(me.attributes, 'private_r_random', )
        _private_r_random_random = self._get_target_attribute_masked(me.attributes, 'private_r_random_random', )
        _align_z = self._get_target_attribute_masked(me.attributes, 'align_z', )
        _align_y = self._get_target_attribute_masked(me.attributes, 'align_y', )
        _surface_uuid = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        # select points to modify by indices
        vs = _vs[indices]
        ns = _ns[indices]
        rotation = _rotation[indices]
        private_r_align = _private_r_align[indices]
        private_r_align_vector = _private_r_align_vector[indices]
        private_r_up = _private_r_up[indices]
        private_r_up_vector = _private_r_up_vector[indices]
        private_r_base = _private_r_base[indices]
        private_r_random = _private_r_random[indices]
        private_r_random_random = _private_r_random_random[indices]
        align_z = _align_z[indices]
        align_y = _align_y[indices]
        surface_uuid = _surface_uuid[indices]
        
        # calculate it..
        l = len(indices)
        vs, ns = self._surfaces_to_world_space(vs, ns, surface_uuid, )
        
        nors = []
        for i, a in enumerate(private_r_align):
            if(a == 0):
                # normal
                nors.append(Vector(ns[i]))
            elif(a == 1):
                # local
                _, nor_1 = self._surfaces_to_world_space(Vector(), Vector((0.0, 0.0, 1.0, )), int(surface_uuid[i]), )
                nors.append(Vector(nor_1))
            elif(a == 2):
                # global
                nors.append(Vector((0.0, 0.0, 1.0, )))
            elif(a == 3):
                # custom
                nors.append(Vector(private_r_align_vector[i]))
        
        ups = []
        for i, u in enumerate(private_r_up):
            if(u == 0):
                # global
                ups.append(Vector((0.0, 1.0, 0.0, )))
            elif(u == 1):
                # local
                _, locy_1 = self._surfaces_to_world_space(Vector(), Vector((0.0, 1.0, 0.0, )), int(surface_uuid[i]), )
                ups.append(locy_1)
            elif(u == 2):
                # custom
                ups.append(Vector(private_r_up_vector[i]))
        
        # # DEBUG
        # print(private_r_align)
        # _vs = tuple(vs) + tuple(vs)
        # _ns = tuple(nors) + tuple(ups)
        # debug.points(self._target, _vs, _ns)
        # # DEBUG
        
        def direction_to_rotation_with_m3x3(direction, up=Vector((0.0, 1.0, 0.0, )), ):
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
        
        qs = []
        for i in range(l):
            q = direction_to_rotation_with_m3x3(nors[i], ups[i], )
            qs.append(q)
        
        # # DEBUG
        # # debug.points(self._target, vs, ns)
        # v = vs[0]
        # m = bpy.data.objects.get(self._surfaces_db[int(surface_uuid[i])]).matrix_world.inverted()
        # z = Vector((0.0, 0.0, 1.0)) @ m
        # z.normalize()
        # y = Vector((0.0, 1.0, 0.0)) @ m
        # y.normalize()
        # debug.points(self._target, [v, v, v, v, v, ], [ns[0], y, z, nors[0], ups[0]])
        # # DEBUG
        
        err = []
        for i in range(l):
            err.append(Euler(private_r_random[i] * private_r_random_random[i]))
        
        fq = []
        for i in range(l):
            uid = int(surface_uuid[i])
            mwi = bpy.data.objects.get(self._surfaces_db[uid]).matrix_world.inverted()
            _, cr, _ = mwi.decompose()
            
            q = Quaternion()
            q.rotate(Euler(private_r_base[i]))
            q.rotate(err[i])
            q.rotate(qs[i])
            q.rotate(cr)
            
            fq.append(q)
        
        for i, q in enumerate(fq):
            e = q.to_euler('XYZ')
            rotation[i] = (e.x, e.y, e.z, )
        
        # and set back to attribute..
        _rotation[indices] = rotation
        self._set_target_attribute_masked(me.attributes, 'rotation', _rotation, )
        
        for i in range(len(indices)):
            v = Vector((0.0, 0.0, 1.0))
            v.rotate(Euler(rotation[i]))
            align_z[i] = v.to_tuple()
            
            v = Vector((0.0, 1.0, 0.0))
            v.rotate(Euler(rotation[i]))
            align_y[i] = v.to_tuple()
        
        # write those as well, so i don't have to store them specially after regeneration..
        _align_z[indices] = align_z
        _align_y[indices] = align_y
        self._set_target_attribute_masked(me.attributes, 'align_z', _align_z, )
        self._set_target_attribute_masked(me.attributes, 'align_y', _align_y, )
    
    def _gen_scale(self, n, ):
        d = np.array(self._get_prop_value('scale_default'), dtype=float, )
        r = np.array(self._get_prop_value('scale_random_factor'), dtype=float, )
        t = 0
        rr = np.random.rand(n, 3)
        if self._get_prop_value('scale_default_use_pressure'):
            d = d * self._pressure
        if(self._get_prop_value('scale_random_type') == 'UNIFORM'):
            f = rr[:, 0]
            f.shape = (-1, 1)
            fn = 1.0 - f
            dr = d * r
            s = (d * fn) + (dr * f)
        elif(self._get_prop_value('scale_random_type') == 'VECTORIAL'):
            t = 1
            f = r + (1.0 - r) * rr
            s = d * f
        # else:
        #     s = np.ones((n, 3, ), dtype=float, )
        
        self._private_s_base = np.full((n, 3), d, dtype=float, )
        self._private_s_random = np.full((n, 3), r, dtype=float, )
        self._private_s_random_random = rr
        self._private_s_random_type = np.full(n, t, dtype=int, )
        self._private_s_change = np.zeros((n, 3), dtype=float, )
        
        self._private_s_change_random = np.random.rand(n, 3)
        
        s.shape = (-1, 3, )
        
        return s
    
    def _regenerate_scale_from_attributes(self, indices, ):
        me = self._target.data
        l = len(me.vertices)
        
        _scale = self._get_target_attribute_masked(me.attributes, 'scale', )
        _private_s_base = self._get_target_attribute_masked(me.attributes, 'private_s_base', )
        _private_s_random = self._get_target_attribute_masked(me.attributes, 'private_s_random', )
        _private_s_random_random = self._get_target_attribute_masked(me.attributes, 'private_s_random_random', )
        _private_s_random_type = self._get_target_attribute_masked(me.attributes, 'private_s_random_type', )
        _private_s_change = self._get_target_attribute_masked(me.attributes, 'private_s_change', )
        
        # slice by indices..
        scale = _scale[indices]
        private_s_base = _private_s_base[indices]
        private_s_random = _private_s_random[indices]
        private_s_random_random = _private_s_random_random[indices]
        private_s_random_type = _private_s_random_type[indices]
        private_s_change = _private_s_change[indices]
        
        # calculate..
        l = len(indices)
        for i in range(l):
            d = private_s_base[i]
            r = private_s_random[i]
            rr = private_s_random_random[i]
            
            if(private_s_random_type[i] == 0):
                # 'UNIFORM'
                f = rr[0]
                fn = 1.0 - f
                dr = d * r
                s = (d * fn) + (dr * f)
            elif(private_s_random_type[i] == 1):
                # 'VECTORIAL'
                f = r + (1.0 - r) * rr
                s = d * f
            
            s = s + private_s_change[i]
            
            scale[i] = s
        
        # and set back to attribute..
        _scale[indices] = scale
        self._set_target_attribute_masked(me.attributes, 'scale', _scale, )
    
    def _gen_id(self, n, ):
        if(not hasattr(self, '_max_id')):
            # NOTE: do this only when create brush is run for the first time..
            me = self._target.data
            l = len(me.vertices)
            if(l == 0):
                self._max_id = 0
            else:
                # NOTE: exception, in this case i want raw values..
                ids = self._get_target_attribute_raw(me.attributes, 'id', )
                v = np.max(ids) + 1
                self._max_id = v
        
        a = np.arange(n)
        r = a + self._max_id
        self._max_id += n
        return r
    
    # ------------------------------------------------------------------ generate <<<
    # ------------------------------------------------------------------ store >>>
    
    # NOTE: `_store_vertices_np` does not make any transforms, so use `_global_to_surface_space` before
    # @stopwatch
    @verbose
    def _store_vertices_np(self, vs, ns, uids, ):
        self._ensure_attributes()
        
        if(uids is None):
            # use active, not sure what to do it is None. in theory it should not happen because creation requires mouse over surface, once is, uuid is determinable.
            if(self._mouse_active_surface_uuid):
                uids = np.full(len(vs), self._mouse_active_surface_uuid, dtype=int, )
        
        if(uids is None):
            raise Exception("_store_vertex: uid is None")
        
        '''
        # NOTE: should i do that? maybe better to run into error, do checks in tool before storing..
        if(not len(vs)):
            return False
        if(not len(ns)):
            return False
        '''
        
        # ------------------------------------------------------------------ before >>>
        
        ok = self._store_vertices_np_before(vs, ns, uids, )
        if(not ok):
            return
        
        # surface local
        vs, ns = self._world_to_surfaces_space(vs, ns, uids, )
        
        # ------------------------------------------------------------------ before <<<
        # ------------------------------------------------------------------ validation >>>
        
        # NOTE: should i do that? maybe better to run into error, set proper shape in tool itself before storing.. but i leave it here for now..
        if(type(vs) is not np.ndarray):
            vs = np.array(vs, dtype=float, ).reshape((-1, 3))
        else:
            if(len(vs.shape) == 1):
                vs.shape = (-1, 3)
        if(type(ns) is not np.ndarray):
            ns = np.array(ns, dtype=float, ).reshape((-1, 3))
        else:
            if(len(ns.shape) == 1):
                ns.shape = (-1, 3)
        
        # ------------------------------------------------------------------ validation <<<
        
        me = self._target.data
        
        # ------------------------------------------------------------------ generate components >>>
        
        s = self._gen_scale(len(vs), )
        r = self._gen_rotation(len(vs), vs, ns, uids, )
        ids = self._gen_id(len(vs), )
        
        # ------------------------------------------------------------------ generate components <<<
        
        _l = len(me.vertices)
        l = len(vs)
        
        # ------------------------------------------------------------------ sanitize indices >>>
        mask = self._get_target_active_mask()
        _l = np.sum(mask)
        # ------------------------------------------------------------------ sanitize indices >>>
        
        me.vertices.add(l)
        ll = len(me.vertices)
        
        # ------------------------------------------------------------------ get/set data >>>
        
        mask = self._get_target_active_mask()
        
        locations = self._get_target_attribute_masked(me.vertices, 'co', mask=mask, )
        locations[_l:] = vs
        self._set_target_attribute_masked(me.vertices, 'co', locations, mask=mask, )
        
        n = 'index'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._get_prop_value('instance_index')
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'normal'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = ns
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        ee = [i.to_euler('XYZ') for i in r]
        
        n = 'rotation'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = ee
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        az = np.zeros((l, 3, ), dtype=float, )
        az[:, 2] = 1.0
        for i in np.arange(l):
            v = Vector(az[i])
            v.rotate(ee[i])
            az[i] = v.to_tuple()
        
        n = 'align_z'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = az
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        ay = np.zeros((l, 3, ), dtype=float, )
        ay[:, 1] = 1.0
        for i in np.arange(l):
            v = Vector(ay[i])
            v.rotate(ee[i])
            ay[i] = v.to_tuple()
        
        n = 'align_y'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = ay
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'scale'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = s
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_s_base'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_s_base
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_s_random'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_s_random
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_s_random_random'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_s_random_random
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_s_random_type'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d.shape = (-1, 1, )
        d[_l:] = self._private_s_random_type.reshape(-1, 1)
        d.shape = (-1, )
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_s_change'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_s_change
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_s_change_random'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_s_change_random
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'id'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d.shape = (-1, 1, )
        d[_l:] = ids.reshape(-1, 1)
        d.shape = (-1, )
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_r_align'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d.shape = (-1, 1, )
        d[_l:] = self._private_r_align.reshape(-1, 1)
        d.shape = (-1, )
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_r_up'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d.shape = (-1, 1, )
        d[_l:] = self._private_r_up.reshape(-1, 1)
        d.shape = (-1, )
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_r_base'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_r_base
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_r_random'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_r_random
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'private_r_random_random'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d[_l:] = self._private_r_random_random
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        n = 'surface_uuid'
        d = self._get_target_attribute_masked(me.attributes, n, mask=mask, )
        d.shape = (-1, 1, )
        d[_l:] = uids.reshape(-1, 1)
        d.shape = (-1, )
        self._set_target_attribute_masked(me.attributes, n, d, mask=mask, )
        
        # ------------------------------------------------------------------ get/set data >>>
        # ------------------------------------------------------------------ after >>>
        
        indices = np.arange(len(vs), dtype=int, ) + _l
        ok = self._store_vertices_np_after(indices, )
        if(ok):
            me.update()
        
        # ------------------------------------------------------------------ after <<<
    
    def _store_vertices_np_before(self, vs, ns, uids, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return False if nothing can be stored because of some condition
        return True
    
    def _store_vertices_np_after(self, indices, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return True if mesh data need to be updated, for example when operation is fully numpyfied, blender will not be triggered to update itself
        return True
    
    # @stopwatch
    @verbose
    def _store_vertex(self, loc, nor, uid=None, ):
        self._ensure_attributes()
        
        if(uid is None):
            # use active, not sure what to do it is None. in theory it should not happen because creation requires mouse over surface, once is, uuid is determinable.
            uid = self._mouse_active_surface_uuid
        
        if(uid is None):
            raise Exception("_store_vertex: uid is None")
        
        # world
        ok = self._store_vertex_before(loc, nor, uid, )
        if(not ok):
            return
        
        # surface local
        loc, nor = self._world_to_active_surface_space(loc, nor, )
        
        me = self._target.data
        me.vertices.add(1)
        i = len(me.vertices) - 1
        
        # NOTE: funny is, this is 2x faster only by writing it to one line, before i had attribute name and attribute reference as variables, writing it at one line went from 0.002s to 0.001s. interesting..
        
        # NOTE: basics
        me.vertices[i].co = loc
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self._get_prop_value('instance_index')
        me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector = nor
        
        # NOTE: rotation
        r = self._gen_rotation(1, np.array(loc, dtype=float, ).reshape(-1, 3), np.array(nor, dtype=float, ).reshape(-1, 3), uid, )[0]
        
        e = r.to_euler('XYZ')
        me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector = e
        
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
        me.attributes['{}align_z'.format(self.attribute_prefix)].data[i].vector = v
        
        v = Vector((0.0, 1.0, 0.0))
        v.rotate(e)
        me.attributes['{}align_y'.format(self.attribute_prefix)].data[i].vector = v
        
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = self._private_r_align[0]
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = self._private_r_up[0]
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector = self._private_r_base[0]
        me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector = self._private_r_random[0]
        me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector = self._private_r_random_random[0]
        
        # NOTE: scale
        s = self._gen_scale(1, )
        me.attributes['{}scale'.format(self.attribute_prefix)].data[i].vector = s[0]
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = self._private_s_base[0]
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data[i].vector = self._private_s_random[0]
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data[i].vector = self._private_s_random_random[0]
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data[i].value = self._private_s_random_type[0]
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector = self._private_s_change[0]
        me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[i].vector = self._private_s_change_random[0]
        
        # NOTE: id
        ids = self._gen_id(1, )
        me.attributes['{}id'.format(self.attribute_prefix)].data[i].value = ids[0]
        # NOTE: surface uuid
        me.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[i].value = uid
        
        self._store_vertex_after(i, )
    
    def _store_vertex_before(self, loc, nor, uid, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return False if nothing can be stored because of some condition
        return True
    
    def _store_vertex_after(self, index, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return True if mesh data need to be updated, for example when operation is fully numpyfied, blender will not be triggered to update itself
        return True
    
    # ------------------------------------------------------------------ store <<<
    # ------------------------------------------------------------------ modal erasers >>>
    
    def _modal_eraser_action_fixed_radius_size(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            return
        
        region = self._context_region
        rv3d = self._context_region_data
        
        loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, loc, )
        loc2_2d = Vector((loc_2d.x, loc_2d.y + self._theme._fixed_radius))
        loc2_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, loc2_2d, loc)
        radius = ((loc.x - loc2_3d.x) ** 2 + (loc.y - loc2_3d.y) ** 2 + (loc.z - loc2_3d.z) ** 2) ** 0.5
        # because of cursor circle..
        radius = radius * 0.5
        
        me = self._target.data
        l = len(me.vertices)
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        if(not len(vs)):
            return
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        # NOTE: convert to world, because in local i would have all mixed up
        vs, _ = self._surfaces_to_world_space(vs, nor=None, uid=uids, )
        
        # # DEBUG
        # debug.points(self._target, vs)
        # # DEBUG
        
        _, _, indices = self._distance_range(vs, loc, radius, )
        if(not len(indices)):
            return
        
        indices = self._get_masked_index_to_target_vertex_index(indices)
        
        mask = np.zeros(l, dtype=bool, )
        mask[indices] = True
        
        bm = bmesh.new()
        bm.from_mesh(me)
        rm = []
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            if(mask[i]):
                rm.append(v)
        for v in rm:
            bm.verts.remove(v)
        bm.to_mesh(me)
        bm.free()
    
    def _modal_eraser_action_real_radius(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            return
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        me = self._target.data
        l = len(me.vertices)
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        if(not len(vs)):
            return
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        # NOTE: convert to world, because in local i would have all mixed up
        vs, _ = self._surfaces_to_world_space(vs, nor=None, uid=uids, )
        
        _, _, indices = self._distance_range(vs, loc, radius, )
        if(not len(indices)):
            return
        
        indices = self._get_masked_index_to_target_vertex_index(indices)
        
        mask = np.zeros(l, dtype=bool, )
        mask[indices] = True
        
        bm = bmesh.new()
        bm.from_mesh(me)
        rm = []
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            if(mask[i]):
                rm.append(v)
        for v in rm:
            bm.verts.remove(v)
        bm.to_mesh(me)
        bm.free()
    
    # ------------------------------------------------------------------ modal erasers <<<


class SCATTER5_OT_fake_context():
    _ls = ['region', 'region_data', ]
    
    def __init__(self, context, ):
        for n in self._ls:
            setattr(self, n, getattr(context, n))


class SCATTER5_OT_fake_event():
    _ls = ['mouse_x', 'mouse_y', 'mouse_region_x', 'mouse_region_y', 'ctrl', 'alt', 'shift', 'oskey', ]
    
    def __init__(self, context, ):
        for n in self._ls:
            setattr(self, n, getattr(context, n))


# DONE: check if fully numpyfied storing opration is faster than loop even with low amount of inserted points, and if so, rewrite all storing operations. something like `_store_one_np` and `_store_many_np` with possibility of callback at the end for various deviations from standard storing operation, like mouse direction aligned tools etc.. -->> checked, and it is not, with batch it is faster, with single vertex is not
# DONE: scale effects with falloff by normalized distances
# DONE: so backport calculations from `_select_2d` and make it into something standard that all tools are using
# DONE: use `_select_weights_?` in brushes that can scale it's effect
# DONE: use `_select_indices_?` in brushes that work on vertices and falloff can only be random selection of them (eraser, dilute, move, free move, drop down, object, and smooth (i think))
# DONE: rename `_select` to something more descriptive
# DONE: add `_select_weights_2d` with same results, only for 2d brushes
# DONE: maybe all selection functions should provide the same result arrays, so they can be swapped if needed, now each functions results in something else
# DONE: use `_selection_` prefix for all selection functions results
# NOTTODO: flip falloff value so that falloff 0.0 = hardest brush, falloff 1.0 = smoothest brush -----> well, i guess it can be like that anyway, see bellow
# NOTTODO: or just rename it? something like falloff border? in sculpt mode shift+f adjust strength, but it is kinda the same result.. allegedly. -->> anyway, i am quite content it being like it is now..
# DONE: prepare `_execute` or `_modify` to be called from outside, now it is some half way there, or just make special function `_execute_for_all` or something like that
# DONE: runtime zero division when falloff = 1.0 and affect = 1.0 in `_select_indices_3d`, possibly in other selection functions as well
# DONE: it is this formula: `nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))` what the hell is this? i am normalizing distance into range (falloff <> radius), soooo, add if range is 0.0, skip that? all at 0.0? or 1.0? some value it should have. there is quite a few places with this is used. it is turned into weights most of time.
# DONE: 1.0 - ((v - 0.0) / ((radius 1.0 - falloff 1.0) - 0.0)) -->> 1.0 - (v / 0.0) -->> so if radius == falloff -->> all ones.. right? is it? i want linear values from falloff to radius and at radius is zero and falloff is one, inside falloff is always one. if i have radius == falloff, there is no falloff, all in radius is selected, so return ones and skip this formula.
# DONE: add `_select_none` so i have intial values at one place
class SCATTER5_OT_modify_mixin():
    # ------------------------------------------------------------------ action support >>>
    def _action_begin_private(self, context, event, ):
        self._action_any_private(context, event, )
        
        # update execute on in case user changed it.
        # TODO: this should be included in base class i guess..
        self._action_execute_on = self._get_prop_value('draw_on')
        if(self._action_execute_on in ('TIMER', 'BOTH', )):
            # update interval value in case user changed it.
            # TODO: this should be included in base class i guess..
            self._action_timer_interval = self._get_prop_value('interval')
            bpy.app.timers.register(self._action_timer_private, first_interval=self._action_timer_interval, )
        
        self._action_begin()
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            self._execute()
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            self._execute()
    
    @verbose
    def _action_finish(self, ):
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._action_timer_interval = self._get_prop_value('interval')
        self._action_execute_on = self._get_prop_value('draw_on')
    
    # ------------------------------------------------------------------ action support <<<
    # ------------------------------------------------------------------ selection >>>
    
    def _select_indices_3d(self, ):
        me = self._target.data
        
        # # NOTE: fabricate default value with nothing selected
        self._select_none()
        
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            # NOTE: i am not above surface
            return
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        if(not len(vs)):
            # NOTE: i have no data
            return
        
        vs_orig = vs.copy()
        
        # NOTE: because of multi surface, i need to do all in global and everything convert to global before
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        # and copy original in world coordinates as well, will be handy later..
        vs_orig_world = vs.copy()
        
        falloff = radius * self._get_prop_value('falloff')
        affect = self._get_prop_value('affect')
        if(self._get_prop_value('affect_pressure')):
            affect = self._pressure
        
        _, distances, indices = self._distance_range(vs, loc, radius, )
        if(not len(indices)):
            # NOTE: all vertices are too far away
            return
        
        mask = np.zeros(l, dtype=bool, )
        
        center = indices[distances <= falloff]
        annulus = indices[(distances > falloff) & (distances <= radius)]
        ad = distances[(distances > falloff) & (distances <= radius)] - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        # choose weighted random from annulus
        s = int(len(annulus) * affect)
        if(s == 0 and len(annulus) > 0):
            s = 1
        if(s > 0):
            ws = nd / np.sum(nd)
            choice = np.random.choice(annulus, size=s, replace=False, p=ws, )
            mask[choice] = True
        
        if(self._get_prop_value('falloff') < 1.0):
            # choose weighted random from border between circle ans annulus so there is no visible circle in result
            b = 0.2
            f2 = falloff * (1.0 - b)
            r2 = falloff * (1.0 + b)
            a = 0.75
            a2 = a + (1.0 - a) * affect
            center2 = indices[distances <= f2]
            transition = indices[(distances > f2) & (distances <= r2)]
            
            s = int(len(transition) * a2)
            if(s == 0 and len(transition) > 0):
                s = 1
            if(s > 0):
                ad = distances[(distances > f2) & (distances <= r2)] - f2
                nd = 1.0 - ((ad - 0.0) / ((r2 - f2) - 0.0))
                ws = nd / np.sum(nd)
                choice = np.random.choice(transition, size=s, replace=False, p=ws, )
                mask[choice] = True
                mask[center2] = True
            else:
                mask[center2] = True
        else:
            mask[center] = True
        
        self._selection_mask = mask
        self._selection_indices = np.arange(l, dtype=int, )[mask]
        
        # # DEBUG
        # _vs, _ = self._surface_to_global_space(vs.copy(), None, )
        # debug.points(self._target, _vs[mask], None, None, )
        # return
        # # DEBUG
        
        ds = np.zeros(l, dtype=float, )
        ds[indices] = distances
        ds = ds[mask]
        self._selection_distances = ds
        self._selection_distances_normalized = (ds - 0.0) / (radius - 0.0)
        
        # # DEBUG
        # vs, _ = self._surface_to_global_space(vs.copy(), None, )
        # vs = vs[self._selection_indices]
        # l = len(vs)
        # ns = np.zeros((l, 3), dtype=float, )
        # z = np.zeros(l, dtype=float, )
        # cs = np.c_[self._selection_distances_normalized, z, z, np.ones(l, dtype=float, )]
        # debug.points(self._target, vs, ns, cs, )
        # # DEBUG
        
        ws = np.zeros(l, dtype=float, )
        ad = self._selection_distances - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        ws[self._selection_indices] = nd
        ws[center] = 1.0
        self._selection_weights = ws[self._selection_mask]
        
        # NOTE: untransformed vertices
        self._selection_vs_original = vs_orig
        # NOTE: untransformed vertices in world coords
        self._selection_vs_original_world = vs_orig_world
        
        # # DEBUG
        # vs, _ = self._surface_to_global_space(vs.copy(), None, )
        # vs = vs[self._selection_indices]
        # l = len(self._selection_weights)
        # ns = np.zeros((l, 3), dtype=float, )
        # z = np.zeros(l, dtype=float, )
        # cs = np.c_[self._selection_weights, z, z, np.ones(l, dtype=float, )]
        # debug.points(self._target, vs, ns, cs, )
        # # DEBUG
    
    def _select_weights_3d(self, ):
        me = self._target.data
        
        # # NOTE: fabricate default value with nothing selected
        self._select_none()
        
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            # NOTE: i am not above surface
            return
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        if(not len(vs)):
            # NOTE: i have no data
            return
        
        vs_orig = vs.copy()
        
        # NOTE: because of multi surface, i need to do all in global and everything convert to global before
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        # and copy original in world coordinates as well, will be handy later..
        vs_orig_world = vs.copy()
        
        falloff = radius * self._get_prop_value('falloff')
        # NOTE: `affect` is redundant now, because with true falloff i use all points, but scale brush effect.. i leave it here, but i have no idea what to use it for..
        
        _, distances, indices = self._distance_range(vs, loc, radius, )
        if(not len(indices)):
            # NOTE: all vertices are too far away
            return
        
        mask = np.zeros(l, dtype=bool, )
        
        center = indices[distances <= falloff]
        annulus = indices[(distances > falloff) & (distances <= radius)]
        ad = distances[(distances > falloff) & (distances <= radius)] - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        mask[indices] = True
        self._selection_mask = mask
        
        self._selection_indices = indices
        self._selection_distances = distances
        self._selection_distances_normalized = (distances - 0.0) / (radius - 0.0)
        
        ws = np.zeros(l, dtype=float, )
        # center circle, always 1.0
        ws[center] = 1.0
        # annulus, linear transition from circle edge (1.0) to radius circle (0.0), normalized distances are it already
        ws[annulus] = nd
        ws = ws[indices]
        self._selection_weights = ws
        
        # NOTE: untransformed vertices
        self._selection_vs_original = vs_orig
        # NOTE: untransformed vertices in world coords
        self._selection_vs_original_world = vs_orig_world
        
        # # DEBUG
        # vs, _ = self._surface_to_global_space(vs.copy(), None, )
        # vs = vs[self._selection_indices]
        # l = len(self._selection_weights)
        # ns = np.zeros((l, 3), dtype=float, )
        # z = np.zeros(l, dtype=float, )
        # cs = np.c_[self._selection_weights, z, z, np.ones(l, dtype=float, )]
        # debug.points(self._target, vs, ns, cs, )
        # # DEBUG
    
    # DONE: not fully updated to multi surface yet
    def _select_indices_2d(self, ):
        me = self._target.data
        
        # # NOTE: fabricate default value with nothing selected
        self._select_none()
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        if(not len(vs)):
            return
        
        vs_orig = vs.copy()
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        
        vs_orig_world = vs.copy()
        
        vs = np.c_[vs[:, 0], vs[:, 1], vs[:, 2], np.ones(len(vs), dtype=vs.dtype, )]
        
        # model = self._surface.matrix_world
        view = self._context_region_data.view_matrix
        projection = self._context_region_data.window_matrix
        
        # vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
        x = vs[:, 0]
        y = vs[:, 1]
        z = vs[:, 1]
        w = vs[:, 3]
        x_ndc = x / w
        y_ndc = y / w
        z_ndc = z / w
        x2d = (x_ndc + 1.0) / 2.0
        y2d = (y_ndc + 1.0) / 2.0
        # # NOTE: do i need some depth? lets go with zeros for now
        # z = np.zeros(len(vs), dtype=float, )
        # vs2d = np.c_[x2d, y2d, z]
        vs2d = np.c_[x2d, y2d]
        
        # # and normalize path from pixels to 0.0-1.0
        # vertices2d = np.zeros((len(vertices), 2), dtype=float, )
        # vertices2d[:, 0] = vertices[:, 0] * (1.0 / self._context_region.width)
        # vertices2d[:, 1] = vertices[:, 1] * (1.0 / self._context_region.height)
        
        # to pixel coordinates
        vs2d[:, 0] = vs2d[:, 0] * self._context_region.width
        vs2d[:, 1] = vs2d[:, 1] * self._context_region.height
        
        vs = np.c_[vs2d[:, 0], vs2d[:, 1], np.zeros(len(vs2d), dtype=vs2d.dtype, )]
        loc = self._mouse_2d_region.copy()
        loc3d = Vector((loc.x, loc.y, 0.0))
        
        _, distances, indices = self._distance_range(vs, loc3d, radius, )
        if(not len(indices)):
            return
        
        ds = np.zeros(l, dtype=float, )
        ds[indices] = distances
        
        falloff = radius * self._get_prop_value('falloff')
        affect = self._get_prop_value('affect')
        if(self._get_prop_value('affect_pressure')):
            affect = self._pressure
        
        mask = np.zeros(l, dtype=bool, )
        
        center = indices[distances <= falloff]
        annulus = indices[(distances > falloff) & (distances <= radius)]
        ad = distances[(distances > falloff) & (distances <= radius)] - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        s = int(len(annulus) * affect)
        if(s == 0 and len(annulus) > 0):
            s = 1
        if(s > 0):
            ws = nd / np.sum(nd)
            choice = np.random.choice(annulus, size=s, replace=False, p=ws, )
            mask[choice] = True
        
        if(self._get_prop_value('falloff') < 1.0):
            b = 0.2
            f2 = falloff * (1.0 - b)
            r2 = falloff * (1.0 + b)
            a = 0.75
            a2 = a + (1.0 - a) * affect
            center2 = indices[distances <= f2]
            transition = indices[(distances > f2) & (distances <= r2)]
            
            s = int(len(transition) * a2)
            if(s == 0 and len(transition) > 0):
                s = 1
            if(s > 0):
                ad = distances[(distances > f2) & (distances <= r2)] - f2
                nd = 1.0 - ((ad - 0.0) / ((r2 - f2) - 0.0))
                ws = nd / np.sum(nd)
                choice = np.random.choice(transition, size=s, replace=False, p=ws, )
                mask[choice] = True
                mask[center2] = True
            else:
                mask[center2] = True
        else:
            mask[center] = True
        
        # # DEBUG
        # _vs, _ = self._surface_to_global_space(vs_orig.copy(), None, )
        # debug.points(self._target, _vs[mask], None, None, )
        # # DEBUG
        
        self._selection_mask = mask
        self._selection_indices = np.arange(l, dtype=int, )[mask]
        
        ds = np.zeros(l, dtype=float, )
        ds[indices] = distances
        ds = ds[mask]
        self._selection_distances = ds
        self._selection_distances_normalized = (ds - 0.0) / (radius - 0.0)
        
        ws = np.zeros(l, dtype=float, )
        ad = self._selection_distances - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        ws[self._selection_indices] = nd
        ws[center] = 1.0
        self._selection_weights = ws[self._selection_mask]
        
        # NOTE: untransformed vertices
        self._selection_vs_original = vs_orig
        # NOTE: vertices in world coords
        self._selection_vs_original_world = vs_orig_world
        # NOTE: in screen space
        self._selection_vs_2d = vs2d
        
        # # DEBUG
        # vs, _ = self._surface_to_global_space(vs_orig.copy(), None, )
        # vs = vs[mask]
        # l = len(vs)
        # ns = np.zeros((l, 3), dtype=float, )
        # z = np.zeros(l, dtype=float, )
        # cs = np.c_[self._selection_weights, z, z, np.ones(l, dtype=float, )]
        # debug.points(self._target, vs, ns, cs, )
        # # DEBUG
    
    # DONE: not fully updated to multi surface yet
    def _select_weights_2d(self, ):
        me = self._target.data
        
        # # NOTE: fabricate default value with nothing selected
        self._select_none()
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        if(not len(vs)):
            return
        
        vs_orig = vs.copy()
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        
        vs_orig_world = vs.copy()
        
        vs = np.c_[vs[:, 0], vs[:, 1], vs[:, 2], np.ones(len(vs), dtype=vs.dtype, )]
        
        # model = self._surface.matrix_world
        view = self._context_region_data.view_matrix
        projection = self._context_region_data.window_matrix
        
        # vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
        x = vs[:, 0]
        y = vs[:, 1]
        z = vs[:, 1]
        w = vs[:, 3]
        x_ndc = x / w
        y_ndc = y / w
        z_ndc = z / w
        x2d = (x_ndc + 1.0) / 2.0
        y2d = (y_ndc + 1.0) / 2.0
        # # NOTE: do i need some depth? lets go with zeros for now
        # z = np.zeros(len(vs), dtype=float, )
        # vs2d = np.c_[x2d, y2d, z]
        vs2d = np.c_[x2d, y2d]
        
        # # and normalize path from pixels to 0.0-1.0
        # vertices2d = np.zeros((len(vertices), 2), dtype=float, )
        # vertices2d[:, 0] = vertices[:, 0] * (1.0 / self._context_region.width)
        # vertices2d[:, 1] = vertices[:, 1] * (1.0 / self._context_region.height)
        
        # to pixel coordinates
        vs2d[:, 0] = vs2d[:, 0] * self._context_region.width
        vs2d[:, 1] = vs2d[:, 1] * self._context_region.height
        
        vs = np.c_[vs2d[:, 0], vs2d[:, 1], np.zeros(len(vs2d), dtype=vs2d.dtype, )]
        loc = self._mouse_2d_region.copy()
        loc3d = Vector((loc.x, loc.y, 0.0))
        
        _, distances, indices = self._distance_range(vs, loc3d, radius, )
        if(not len(indices)):
            return
        
        ds = np.zeros(l, dtype=float, )
        ds[indices] = distances
        
        falloff = radius * self._get_prop_value('falloff')
        
        mask = np.zeros(l, dtype=bool, )
        
        center = indices[distances <= falloff]
        annulus = indices[(distances > falloff) & (distances <= radius)]
        ad = distances[(distances > falloff) & (distances <= radius)] - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        mask[indices] = True
        self._selection_mask = mask
        
        self._selection_indices = indices
        self._selection_distances = distances
        self._selection_distances_normalized = (distances - 0.0) / (radius - 0.0)
        
        ws = np.zeros(l, dtype=float, )
        # center circle, always 1.0
        ws[center] = 1.0
        # annulus, linear transition from circle edge (1.0) to radius circle (0.0), normalized distances are it already
        ws[annulus] = nd
        ws = ws[indices]
        self._selection_weights = ws
        
        # NOTE: untransformed vertices
        self._selection_vs_original = vs_orig
        # NOTE: vertices in world coords
        self._selection_vs_original_world = vs_orig_world
        # NOTE: in screen space
        self._selection_vs_2d = vs2d
        
        # # DEBUG
        # vs, _ = self._surface_to_global_space(vs_orig.copy(), None, )
        # vs = vs[mask]
        # l = len(vs)
        # ns = np.zeros((l, 3), dtype=float, )
        # z = np.zeros(l, dtype=float, )
        # cs = np.c_[self._selection_weights, z, z, np.ones(l, dtype=float, )]
        # debug.points(self._target, vs, ns, cs, )
        # # DEBUG
    
    _selection_types = {'INDICES_3D', 'WEIGHTS_3D', 'INDICES_2D', 'WEIGHTS_2D', }
    _selection_type = 'INDICES_3D'
    
    def _select(self, ):
        if(self._selection_type not in self._selection_types):
            raise TypeError("Unknown selection type")
        
        if(self._selection_type == 'INDICES_3D'):
            self._select_indices_3d()
        elif(self._selection_type == 'WEIGHTS_3D'):
            self._select_weights_3d()
        elif(self._selection_type == 'INDICES_2D'):
            self._select_indices_2d()
        elif(self._selection_type == 'WEIGHTS_2D'):
            self._select_weights_2d()
    
    def _select_all(self, ):
        if(self._selection_type not in self._selection_types):
            raise TypeError("Unknown selection type")
        
        me = self._target.data
        
        self._select_none()
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        if(not len(vs)):
            # NOTE: i have no data
            return
        
        self._selection_mask = np.ones(l, dtype=bool, )
        self._selection_indices = np.arange(l, dtype=int, )
        # WATCH: not sure what will happen, should be zeros or ones?
        self._selection_distances = np.zeros(l, dtype=float, )
        # WATCH: not sure what will happen, should be zeros or ones?
        self._selection_distances_normalized = np.ones(l, dtype=float, )
        self._selection_weights = np.ones(l, dtype=float, )
        self._selection_vs_original = vs.copy()
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        self._selection_vs_original_world = vs.copy()
        
        if(self._selection_type in ('INDICES_3D', 'WEIGHTS_3D', )):
            pass
            
        elif(self._selection_type in ('INDICES_2D', 'WEIGHTS_2D', )):
            self._selection_vs_2d = np.c_[vs[:, 0], vs[:, 1]]
    
    def _select_none(self, ):
        me = self._target.data
        m = self._get_target_active_mask()
        l = np.sum(m)
        
        self._selection_mask = np.zeros(l, dtype=bool, )
        self._selection_indices = np.arange(0, dtype=int, )
        self._selection_distances = np.zeros(0, dtype=float, )
        self._selection_distances_normalized = np.zeros(0, dtype=float, )
        self._selection_weights = np.zeros(0, dtype=float, )
        self._selection_vs_original = np.zeros((0, 3), dtype=float, )
        self._selection_vs_original_world = np.zeros((0, 3), dtype=float, )
        
        if(self._selection_type in ('INDICES_2D', 'WEIGHTS_2D', )):
            self._selection_vs_2d = np.zeros((0, 2), dtype=float, )
    
    # ------------------------------------------------------------------ selection <<<
    # ------------------------------------------------------------------ action >>>
    
    def _modify(self, ):
        # NOTE: override in brush
        pass
    
    def _execute(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            return
        
        self._select()
        
        indices = self._selection_indices
        if(not len(indices)):
            return
        
        self._ensure_attributes()
        
        # NOTE: flip the switch if brush uses foreach_set only, foreach_set does not force blender to update data
        self._force_update = False
        self._modify()
        if(self._force_update):
            self._target.data.update()
    
    # NOTE: to be used by menu operator
    def _execute_all(self, ):
        self._select_all()
        
        indices = self._selection_indices
        if(not len(indices)):
            return
        
        self._ensure_attributes()
        self._modify()
        self._target.data.update()
    
    # ------------------------------------------------------------------ action <<<
    # ------------------------------------------------------------------ utilities >>>
    
    def _get_axis(self, i, uid, ):
        me = self._target.data
        axis = Vector()
        if(self._get_prop_value('effect_axis') == 'SURFACE_NORMAL'):
            v, _ = self._surfaces_to_world_space(me.vertices[i].co, None, uid, )
            _, axis, _, _ = self._bvh.find_nearest(v)
        elif(self._get_prop_value('effect_axis') == 'LOCAL_Z_AXIS'):
            _, axis = self._surfaces_to_world_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), uid, )
        elif(self._get_prop_value('effect_axis') == 'GLOBAL_Z_AXIS'):
            axis = Vector((0.0, 0.0, 1.0, ))
        elif(self._get_prop_value('effect_axis') == 'PARTICLE_Z'):
            axis = Vector((0.0, 0.0, 1.0, ))
            e = Euler(me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector)
            axis.rotate(e)
            # NOTE: only rotate axis, no need for anything else..
            _, r, _ = bpy.data.objects.get(self._surfaces_db[uid]).matrix_world.decompose()
            axis.rotate(r)
        return axis
    
    def _calc_rotation_components_from_attributes(self, i, uid, ):
        me = self._target.data
        
        vec, nor = self._surfaces_to_world_space(me.vertices[i].co, me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector, uid, )
        _, nor_1 = self._surfaces_to_world_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), uid, )
        
        private_r_align = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
        if(private_r_align == 0):
            nor = Vector(nor)
        elif(private_r_align == 1):
            nor = nor_1.copy()
        elif(private_r_align == 2):
            nor = Vector((0.0, 0.0, 1.0, ))
        elif(private_r_align == 3):
            nor = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector)
        
        surface_matrix = bpy.data.objects.get(self._surfaces_db[uid]).matrix_world.copy()
        
        locy_1 = Vector((0.0, 1.0, 0.0, ))
        mwi_1 = surface_matrix
        _, cr_1, _ = mwi_1.decompose()
        locy_1.rotate(cr_1)
        
        private_r_up = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value
        if(private_r_up == 0):
            aq = self._direction_to_rotation(nor, )
        elif(private_r_up == 1):
            aq = self._direction_to_rotation(nor, locy_1, )
        elif(private_r_up == 2):
            aq = self._direction_to_rotation(nor, Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector), )
        
        private_r_random = np.array(me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector, dtype=float, )
        private_r_random_random = np.array(me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector, dtype=float, )
        err = Euler(private_r_random * private_r_random_random)
        
        mwi = surface_matrix.inverted()
        _, cr, _ = mwi.decompose()
        
        eb = Euler(me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector)
        
        return eb, err, aq, cr
    
    # ------------------------------------------------------------------ utilities <<<
    # ------------------------------------------------------------------ widgets on timer >>>
    
    # TODO: basically this is hacking of base class, should i be worried? should i make it part of base class? if more than one brush (as of now) needs that, maybe..
    # TODO: i am not sure if this is even possible, more testing is required i guess, so far it seems it is working
    # NOTE: from events i store just a few numbers, but from context region and region_data, do they free from memory while operator is running? should i retrieve matching reference from api instead?
    # NOTE: enabled by `self._widgets_use_timer_events = True` in `_invoke`
    
    def _widgets_any_event(self, context, event, ):
        if(not hasattr(self, '_widgets_use_timer_events')):
            return
        if(not self._widgets_use_timer_events):
            return
        
        if(event.type != 'TIMER'):
            # # NOTE: memory address is constant, as it seems..
            # print(context.region, context.region_data)
            
            self._store_event_data(context, event, )
    
    def _store_event_data(self, context, event, ):
        self._widgets_last_fake_context = SCATTER5_OT_fake_context(context, )
        self._widgets_last_fake_event = SCATTER5_OT_fake_event(event, )
    
    def _action_timer_private(self, ):
        super()._action_timer_private()
        
        try:
            if(not hasattr(self, '_widgets_use_timer_events')):
                return
            if(not self._widgets_use_timer_events):
                return
            if(not getattr(self, '_widgets_last_fake_context')):
                # nothing has been stored yet, no drawing this time..
                return
        except ReferenceError as e:
            # NOTE: if an error happen in timer brush, timer will run after, but with `ReferenceError: StructRNA of type SCATTER5_OT_manual_brush_tool_scale_random has been removed` when `self` is accessed
            # NOTE: so to prevent mess in error reports, panic instead
            panic('SCATTER5_OT_modify_mixin._action_timer_private')
            return
        
        if(self._lmb):
            self._widgets_mouse_press(self._widgets_last_fake_context, self._widgets_last_fake_event, )
        else:
            self._widgets_mouse_idle(self._widgets_last_fake_context, self._widgets_last_fake_event, )
    
    # ------------------------------------------------------------------ widgets on timer <<<


# ------------------------------------------------------------------ base classes <<<
# ------------------------------------------------------------------ create brushes >>>

# DONE: common widget drawing elements to helper functions, so i don't have that long dict literals and various matrix calculations could be also turn into function
# DONE: set size for no entry sing from `_widget_no_entry_sign_size` and turn whole sign drawing definition to utility function that return drawing list, so it is single function call
# DONE: where to put those helpers? on tool itself via common mixin? on ToolWidgets itself? (i got one function there, maybe it is not a good idea)
# DONE: all fills in cursor widgets at 50% then it is now (with gesture widgets exception, leave them, or maybe even more opaque)
# DONE: all falloff circles more opaque to be more visible
# DONE: get rid of brush center crosses, either replace with dot (but have to be antialliased) or leave empty (try 2d dot outlined circle at integer coords, maybe it will look ok, or numpy array with texture)
# DONE: press and erase colors a bit less aggressive. more pastel
# DONE: dashed multiplier to theme
# DONE: get rid of mouse widget center dot when modal eraser is used, dot is there for nothing, it erases in full radius
# DONE: dot and pose modal eraser messes with states. dot, if during erasing ctrl is released, it changes color and won't start drawing again like other brushes because depends on `_action_begin` to set up things. pose, when you start posing, hit ctrl, switche to erasing (and posing is stooped), that is correct, but when ctrl is released it switches to no entry sign (because last posing is erased), and the same as with dot, start erasing, release ctrl, you get press color but no entry sign.
# DONE: tools using direction (aligned spray, comb, z align), add some direction interpolation so it is smoother. comb got `direction_smoothing_steps` which is used for effect, but not for widget. would be nice to have it on all these three and use it also for widget -->> can use `_mouse_3d_direction_interpolated` and `_mouse_2d_direction_interpolated`
# DONE: aligned spray, comb and z align (and spatter), use `_mouse_3d_direction_interpolated` and `_mouse_2d_direction_interpolated` for direction, leave that open in ui (like it was on comb) -->> global mouse direction interpolation, exposed for these brushes only
# DONE: multi surface support

# DONE: drag from outside to surface, widget have press colors, but nothing will happen
# DONOTWATCH: dot, sometimes helper lines modal scale disappear, it happens at seemingly random.. and it recovers back after some time. no errors whatsoever -->> never happened again..
# DONE: add rotation on mouse wheel and scale on ctls mouse wheel like surface move has
# NOTTODO: modal rotation/scale widget is too big i think. or is my test scene instance too small? not going to calc bounding box for it. or do i?
class SCATTER5_OT_manual_brush_tool_dot(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_dot"
    bl_label = "Dot Brush"
    bl_description = "Dot Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_dot"
    tool_category = 'CREATE'
    tool_label = "Dot Brush"
    # NOTE: dot has no gestures, these above are just for testing.
    tool_gesture_definitions = {}
    # tool_gesture_space = None
    tool_infobox = (
        "• Draw: LMB",
        "• Adjust: LMB+DRAG",
        "• Rotate: LMB+Mouse Wheel",
        "• Scale: LMB+CTRL+Mouse Wheel",
        "• Erase: CTRL+LMB",
    )
    
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    # @verbose
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            if(self._last_index is not None):
                woc = self._theme._outline_color_press
                wfc = self._theme._fill_color_press
            if(self._eraser_mode):
                woc = self._theme._outline_color_eraser
                wfc = self._theme._fill_color_eraser
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            if(not self._eraser_mode):
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
            
            if(not self._eraser_mode and self._last_index is not None):
                r = radius * self._modal_scale_factor_widgets
                ms = Matrix(((r / 2, 0.0, 0.0, 0.0), (0.0, r / 2, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                
                mmsf = mt @ mr @ ms
                q = Quaternion(nor, self._modal_rotate_radians_widgets)
                mrrr = mt @ (q.to_matrix().to_4x4() @ mr) @ ms
                
                if(self._modal_rotate_radians_widgets != 0.0):
                    ls.extend((
                        # rotation line
                        {
                            'function': 'thick_line_3d',
                            'arguments': {
                                'a': (-1.0, 0.0, 0.0, ),
                                'b': (1.0, 0.0, 0.0, ),
                                'matrix': mrrr,
                                'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                                'thickness': self._theme._outline_thickness_helper,
                            }
                        },
                    ))
                if(self._modal_scale_factor_widgets != 1.0):
                    ls.extend((
                        # scale circle
                        {
                            'function': 'circle_outline_3d',
                            'arguments': {
                                'matrix': mmsf,
                                'steps': self._theme._circle_steps,
                                'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                                'thickness': self._theme._outline_thickness_helper,
                            }
                        },
                    ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    # @verbose
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
        else:
            self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: brush
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        # loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._eraser_mode = True
                self._modal_eraser_action_fixed_radius_size()
            else:
                self._store_vertex(loc, nor, None, )
                self._last_index = int(self._get_target_vertex_index_to_masked_index([self._target.data.vertices[-1].index, ], )[0])
                
                # # DEBUG
                # i = self._last_index
                # s = bpy.data.objects.get(self._mouse_active_surface_name)
                # m = s.matrix_world
                # v = m @ self._target.data.vertices[i].co
                # _, r, _ = m.decompose()
                # r = r.to_matrix().to_4x4()
                # n = r @ self._target.data.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector
                # y = r @ self._target.data.attributes['{}align_y'.format(self.attribute_prefix)].data[i].vector
                # z = r @ self._target.data.attributes['{}align_z'.format(self.attribute_prefix)].data[i].vector
                # debug.points(self._target, [v, v, v, ], [n, y, z, ])
                # # DEBUG
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._eraser_mode):
                self._modal_eraser_action_fixed_radius_size()
            else:
                if(self._last_index is None):
                    return
                
                loc, nor = self._world_to_active_surface_space(loc, nor, )
                ii = int(self._get_masked_index_to_target_vertex_index([self._last_index, ])[0])
                self._target.data.vertices[ii].co = loc
                self._target.data.attributes['{}normal'.format(self.attribute_prefix)].data[ii].vector = nor
                
                if(self._mouse_active_surface_uuid != self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[ii].value):
                    self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[ii].value = self._mouse_active_surface_uuid
                
                if(self._modal_rotate_radians != 0.0):
                    # TODO: this is ridiculous, i need that so many lines to rotate y along z according to all rotation related attributes? i think rotation attributes system is bad.. and need to change
                    '''
                    i = self._last_index
                    me = self._target.data
                    
                    vec, nor = self._surface_to_global_space(me.vertices[i].co, me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector, )
                    _, nor_1 = self._surface_to_global_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), )
                    
                    private_r_align = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
                    if(private_r_align == 0):
                        nor = Vector(nor)
                    elif(private_r_align == 1):
                        nor = nor_1.copy()
                    elif(private_r_align == 2):
                        nor = Vector((0.0, 0.0, 1.0, ))
                    elif(private_r_align == 3):
                        nor = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector)
                    
                    locy_1 = Vector((0.0, 1.0, 0.0, ))
                    mwi_1 = self._surface.matrix_world.copy()
                    _, cr_1, _ = mwi_1.decompose()
                    locy_1.rotate(cr_1)
                    
                    private_r_up = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value
                    if(private_r_up == 0):
                        aq = self._direction_to_rotation(nor, )
                    elif(private_r_up == 1):
                        aq = self._direction_to_rotation(nor, locy_1, )
                    elif(private_r_up == 2):
                        aq = self._direction_to_rotation(nor, Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector), )
                    
                    private_r_random = np.array(me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector, dtype=float, )
                    private_r_random_random = np.array(me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector, dtype=float, )
                    err = Euler(private_r_random * private_r_random_random)
                    
                    mwi = self._surface.matrix_world.inverted()
                    _, cr, _ = mwi.decompose()
                    
                    eb = Euler(me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector)
                    
                    q = Quaternion()
                    q.rotate(aq)
                    q.rotate(cr)
                    m = q.to_matrix().to_4x4()
                    e = m
                    e = self._surface.matrix_world @ e
                    
                    axis = nor
                    angle = self._modal_rotate_radians
                    q = Quaternion(axis, angle, ).to_matrix().to_4x4()
                    
                    m = q @ e
                    _, v, _ = m.decompose()
                    v = v.to_euler('XYZ')
                    z = Vector((0.0, 0.0, 1.0, ))
                    z.rotate(v)
                    y = Vector((0.0, 1.0, 0.0, ))
                    y.rotate(v)
                    me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
                    me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = z
                    me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
                    me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = y
                    
                    self._modal_rotate_radians = 0.0
                    '''
                    
                    r = self._target.data.attributes['{}private_r_base'.format(self.attribute_prefix)].data[ii].vector
                    r.z += self._modal_rotate_radians
                    self._target.data.attributes['{}private_r_base'.format(self.attribute_prefix)].data[ii].vector = r
                    self._modal_rotate_radians = 0.0
                
                self._regenerate_rotation_from_attributes(np.array([self._last_index, ], dtype=int, ), )
                
                if(self._modal_scale_factor != 0.0):
                    s = self._target.data.attributes['{}private_s_base'.format(self.attribute_prefix)].data[ii].vector
                    
                    s = s * (1.0 + self._modal_scale_factor)
                    
                    self._target.data.attributes['{}private_s_base'.format(self.attribute_prefix)].data[ii].vector = s
                    self._modal_scale_factor = 0.0
                    self._regenerate_scale_from_attributes(np.array([self._last_index, ], dtype=int, ), )
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._eraser_mode = False
        
        self._last_index = None
        
        self._modal_rotate_increment = 0.1
        self._modal_rotate_radians = 0.0
        self._modal_rotate_radians_widgets = 0.0
        
        self._modal_scale_increment = 0.1
        self._modal_scale_factor = 0.0
        self._modal_scale_factor_widgets = 1.0
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _modal(self, context, event, ):
        # if i need something to be constantly refreshed.. not widgets..
        self._on_any_modal_event(context, event, )
        
        # update..
        self._context_region = context.region
        self._context_region_data = context.region_data
        # update settings..
        self._update_references_and_settings(context, event, )
        
        # ------------------------------------------------------------------------------------------
        # NOTE: inject into `_modal` and repeat all steps until gestures, this should ensure all is set for action
        
        if(event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', }):
            if(self._lmb):
                if(event.ctrl):
                    if(event.type == 'WHEELUPMOUSE'):
                        self._modal_scale_factor += self._modal_scale_increment
                        self._modal_scale_factor_widgets *= 1.0 + self._modal_scale_factor
                    if(event.type == 'WHEELDOWNMOUSE'):
                        self._modal_scale_factor -= self._modal_scale_increment
                        self._modal_scale_factor_widgets *= 1.0 + self._modal_scale_factor
                else:
                    if(event.type == 'WHEELUPMOUSE'):
                        self._modal_rotate_radians -= self._modal_rotate_increment
                        self._modal_rotate_radians_widgets -= self._modal_rotate_increment
                    if(event.type == 'WHEELDOWNMOUSE'):
                        self._modal_rotate_radians += self._modal_rotate_increment
                        self._modal_rotate_radians_widgets += self._modal_rotate_increment
                
                self._widgets_mouse_press(context, event, )
                
                loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
                if(loc is not None):
                    if(self._last_index is not None):
                        self._action_update()
                
                return {'RUNNING_MODAL'}
        
        # ------------------------------------------------------------------------------------------
        
        # NOTE: super!
        return super()._modal(context, event, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_dot'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        # NOTE: brush specific props..
        self._eraser_mode = False
        self._last_index = None
        
        self._modal_rotate_increment = 0.1
        self._modal_rotate_radians = 0.0
        self._modal_rotate_radians_widgets = 0.0
        
        self._modal_scale_increment = 0.1
        self._modal_scale_factor = 0.0
        self._modal_scale_factor_widgets = 1.0


# DONE: connection line disconnects dots when actively posing and mouse wheel is used. i guess best solution to this is to deny any navigation (mouse wheel, ndof, trackpad), add some more flag to base class that disables all navigation.
# DONE: something better than filled cube for widget. outlined cube? and no axis? or something else? don't like current widget. it's chaotic. maybe find out something quite different? it is one of a kind tool type..
# FIXMENOT: NOTTODO: scale gesture widget is unsatisfactory, be it either something representing scale, or just tooltip -->> it is not absolute scale, but multiplier of initial scale
class SCATTER5_OT_manual_brush_tool_pose(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_pose"
    bl_label = "Pose Brush"
    bl_description = "Pose Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_pose"
    tool_category = 'CREATE'
    tool_label = "Pose Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'scale_multiplier',
            'datatype': 'float',
            'change': 1 / 1000,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Scale Multiplier',
            'widget': 'TOOLTIP_3D',
        },
    }
    # tool_gesture_space = None
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Adjust: LMB+DRAG",
        "• Erase: CTRL+LMB",
    )
    
    icon = "W_SCALE_GROW"
    dat_icon = "SCATTER5_POSE"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: overrides
    
    def _update_last(self, ):
        me = self._target.data
        i = self._target.data.vertices[-1].index
        
        # scale
        d = Vector(self._mouse_2d_region - self._origin_2d).length * self._get_prop_value('scale_multiplier')
        v = self._get_prop_value('scale_default')
        x = v.x + (v.x * d)
        y = v.y + (v.y * d)
        z = v.z + (v.z * d)
        s = Vector((x, y, z, ))
        
        me.attributes['{}scale'.format(self.attribute_prefix)].data[i].vector = s
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = s
        
        # rotation
        region = self._context_region
        rv3d = self._context_region_data
        coord = self._mouse_2d_region
        # get mouse location in 3d at origin depth
        loc = view3d_utils.region_2d_to_location_3d(region, rv3d, coord, self._origin, )
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
        
        if(self._get_prop_value('rotation_align') == 'GLOBAL_Z_AXIS'):
            av = Vector((0.0, 0.0, 1.0, ))
        elif(self._get_prop_value('rotation_align') == 'LOCAL_Z_AXIS'):
            _, av = self._surfaces_to_world_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), self._uid, )
        elif(self._get_prop_value('rotation_align') == 'SURFACE_NORMAL'):
            av = self._normal
        me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = av
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
        # use that as before in 3d
        d = self._origin - loc
        q = self._rotation_to(Vector((0.0, 0.0, 1.0, )), d)
        u = Vector((0.0, 0.0, 1.0, ))
        u.rotate(q)
        u.normalize()
        u.negate()
        me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = u
        
        ii = int(self._get_target_vertex_index_to_masked_index([i, ], )[0])
        self._regenerate_rotation_from_attributes(np.array([ii, ], dtype=int, ), )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            bm = mt @ mr @ ms
            sl = 0.5
            ls.extend((
                # box outline
                {
                    'function': 'box_outline_3d',
                    'arguments': {
                        'side_length': sl,
                        'matrix': bm,
                        'offset': (0.0, 0.0, sl / 2, ),
                        'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
            ))
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        if(self._eraser_mode):
            loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
            if(loc is not None):
                woc = self._theme._outline_color_eraser
                wfc = self._theme._fill_color_eraser
                
                radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
                
                ls = []
                
                c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
                ls.extend(c)
                
                ToolWidgets._cache[self.tool_id]['screen_components'] = ls
                ToolWidgets._cache[self.tool_id]['cursor_components'] = []
            else:
                ls = []
                sign = self._widgets_fabricate_no_entry_sign(event, )
                ls.extend(sign)
                
                ToolWidgets._cache[self.tool_id]['screen_components'] = []
                ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        else:
            loc = self._origin
            nor = self._normal
            if(loc is not None):
                woc = self._theme._outline_color_press
                wfc = self._theme._fill_color_press
                
                radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
                
                ms = self._widgets_compute_surface_matrix_scale_component_3d(radius / 2, )
                cm = mt @ mr @ ms
                
                mcr = self._theme._fixed_radius / 4
                
                a = self._origin_2d
                e = Vector((event.mouse_region_x, event.mouse_region_y, ))
                n = a - e
                n.normalize()
                b = e + (n * mcr)
                
                ls = [
                    # cursor circle
                    {
                        'function': 'circle_outline_3d',
                        'arguments': {
                            'matrix': cm,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'circle_fill_3d',
                        'arguments': {
                            'matrix': cm,
                            'steps': self._theme._circle_steps,
                            'color': wfc,
                        }
                    },
                    # connection line
                    {
                        'function': 'thick_line_2d',
                        'arguments': {
                            'a': a,
                            'b': b,
                            'color': woc,
                            'thickness': self._theme._outline_thickness_helper,
                        },
                    },
                    # mouse circle
                    {
                        'function': 'circle_thick_outline_2d',
                        'arguments': {
                            'center': (event.mouse_region_x, event.mouse_region_y, ),
                            'radius': mcr,
                            'steps': self._theme._circle_steps,
                            'color': woc,
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                ]
                
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
                
                ToolWidgets._cache[self.tool_id]['screen_components'] = ls
                ToolWidgets._cache[self.tool_id]['cursor_components'] = []
            else:
                ls = []
                sign = self._widgets_fabricate_no_entry_sign(event, )
                ls.extend(sign)
                
                ToolWidgets._cache[self.tool_id]['screen_components'] = []
                ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
        else:
            self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: brush
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._eraser_mode = True
                self._modal_eraser_action_fixed_radius_size()
                return
            
            self._nav_enabled = False
            
            self._uid = self._mouse_active_surface_uuid
            self._origin = loc.copy()
            self._normal = nor.copy()
            self._origin_2d = self._mouse_2d_region.copy()
            
            self._store_vertex(loc, nor, )
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        if(self._eraser_mode):
            self._modal_eraser_action_fixed_radius_size()
        
        if(self._origin is None):
            return
        
        a = self._origin_2d
        b = self._mouse_2d_region
        c = b - a
        self._distance = c.length
        self._angle = c.angle_signed(Vector((0.0, 1.0, )), 0.0, )
        
        self._update_last()
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._eraser_mode = False
        
        self._uid = None
        self._origin = None
        self._normal = None
        self._origin_2d = None
        self._angle = 0.0
        self._distance = 0.0
        
        self._nav_enabled = True
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_pose'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        # NOTE: brush specific props..
        self._eraser_mode = False
        # inital surface uuid
        self._uid = None
        # this is where instance will be located
        self._origin = None
        # this is instance up (z)
        self._normal = None
        # and store this for 2d calculations
        self._origin_2d = None
        self._angle = 0.0
        self._distance = 0.0


# DONE: multi surface: when i leave one surface, cross gap and enter another surface, it will not restart drawing on new surface, most likely due to large distance. on surface just left it should stop distance measuring, and resume on next surface enter
class SCATTER5_OT_manual_brush_tool_path(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_path"
    bl_label = "Path Brush"
    bl_description = "Path Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_path"
    tool_category = 'CREATE'
    tool_label = "Path Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'distance',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20 * 10,
            'text': '{}: {:.3f}',
            'name': 'Distance',
            'widget': 'LENGTH_3D',
        },
        '__gesture_secondary__': {
            'property': 'divergence',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20 * 10,
            'text': '{}: {:.3f}',
            'name': 'Divergence',
            'widget': 'LENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Erase: CTRL+LMB",
    )
    
    icon = "W_PENCIL"
    dat_icon = "SCATTER5_PENCIL"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: overrides
    
    def _store_vertex_after(self, index, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return True if mesh data need to be updated, for example when operation is fully numpyfied, blender will not be triggered to update itself
        
        # if(self._brush.use_align_y_to_stroke):
        if(self._get_prop_value('use_align_y_to_stroke')):
            d = self._stroke_directions[-1]
            
            me = self._target.data
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[index].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[index].vector = d
            
            # NOTE: sanitize indices
            i = int(self._get_target_vertex_index_to_masked_index([index, ], )[0])
            indices = [i, ]
            
            self._regenerate_rotation_from_attributes(np.array(indices, dtype=int, ), )
            # TODO: until `_regenerate_rotation_from_attributes` is fully numpyfied, return False, after it can return True so it is updated once
            # TODO: hmmm? `_regenerate_rotation_from_attributes` does not trigger? modifying vertex attributes does not trigger update?
            return True
        
        return True
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            # d = self._brush.distance
            d = self._get_prop_value('distance')
            ms = self._widgets_compute_surface_matrix_scale_component_3d(d, )
            cm = mt @ mr @ ms
            
            ls.extend((
                # distance helper circle
                {
                    'function': 'circle_outline_dashed_3d',
                    'arguments': {
                        'matrix': cm,
                        'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                        'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
            ))
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            if(event.ctrl):
                woc = self._theme._outline_color_eraser
                wfc = self._theme._fill_color_eraser
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            if(not event.ctrl):
                d = self._get_prop_value('distance')
                if(self._get_prop_value('distance_pressure')):
                    d = d * self._pressure
                ms = self._widgets_compute_surface_matrix_scale_component_3d(d, )
                cm = mt @ mr @ ms
                
                ls.extend((
                    # distance helper circle
                    {
                        'function': 'circle_outline_dashed_3d',
                        'arguments': {
                            'matrix': cm,
                            'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                            'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                ))
                
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
        else:
            self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: brush
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_fixed_radius_size()
                
                # NOTE: eraser should break stroke
                self._stroke_locations = []
                self._stroke_directions = []
            else:
                self._stroke_locations.append(loc)
                if(self._mouse_3d_direction):
                    self._stroke_directions.append(self._mouse_3d_direction)
                else:
                    self._stroke_directions.append(Vector())
                
                self._store_vertex(loc, nor, )
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_fixed_radius_size()
                
                # NOTE: eraser should break stroke
                self._stroke_locations = []
                self._stroke_directions = []
            else:
                if(not len(self._stroke_locations)):
                    # NOTE: in case i started with eraser first
                    self._stroke_locations.append(loc)
                    if(self._mouse_3d_direction):
                        self._stroke_directions.append(self._mouse_3d_direction)
                    else:
                        self._stroke_directions.append(Vector())
                    
                    self._store_vertex(loc, nor, )
                    return
                
                a = self._stroke_locations[-1]
                b = loc
                d = self._distance_vectors_3d(a, b)
                fd = self._get_prop_value('distance')
                if(self._get_prop_value('distance_pressure')):
                    fd = fd * self._pressure
                
                if(fd <= d):
                    # NOTE: why it is getting slower with more point when i use just last point from path with new one?
                    n = b - a
                    n.normalize()
                    direction = n
                    c = Vector((a.x + fd * n.x, a.y + fd * n.y, a.z + fd * n.z, ))
                    if(self._get_prop_value('divergence') > 0.0):
                        d = self._get_prop_value('divergence')
                        if(self._get_prop_value('divergence_pressure')):
                            d = d * self._pressure
                        
                        v = direction.cross(nor)
                        if(random.random() < 0.5):
                            v.negate()
                        
                        d = d * random.random()
                        c = c + (v.normalized() * d)
                        
                        lp = self._stroke_locations[-1]
                        cc = c - lp
                        cc.normalize()
                        cc.length = fd
                        c = lp + cc
                    
                    # find it again, because target polygon and normal can change while coorecting distance
                    loc, nor, idx, dst = self._bvh.find_nearest(c)
                    nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
                    
                    self._stroke_locations.append(loc)
                    self._stroke_directions.append(direction)
                    self._store_vertex(loc, nor, )
        else:
            # NOTE: mouse left surface, restart?
            self._stroke_locations = []
            self._stroke_directions = []
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._stroke_locations = []
        self._stroke_directions = []
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_path'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        self._action_execute_on = 'BOTH'
        self._action_timer_interval = 0.1
        
        # NOTE: brush specific props..
        self._stroke_locations = []
        self._stroke_directions = []


# DONE: multi surface: when i leave one surface, cross gap and enter another surface, it will not restart drawing on new surface, most likely due to large distance. on surface just left it should stop distance measuring, and resume on next surface enter
class SCATTER5_OT_manual_brush_tool_chain(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_chain"
    bl_label = "Chain Brush"
    bl_description = "Chain Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_chain"
    tool_category = 'CREATE'
    tool_label = "Chain Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'distance',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20 * 10,
            'text': '{}: {:.3f}',
            'name': 'Distance',
            'widget': 'LENGTH_3D',
        },
        '__gesture_secondary__': {
            'property': 'divergence',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20 * 10,
            'text': '{}: {:.3f}',
            'name': 'Divergence',
            'widget': 'LENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Erase: CTRL+LMB",
    )
    
    icon = "W_PENCIL"
    dat_icon = "SCATTER5_PENCIL_CHAIN"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: overrides
    
    def _store_vertex_after(self, index, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return True if mesh data need to be updated, for example when operation is fully numpyfied, blender will not be triggered to update itself
        
        d = self._stroke_directions[-1]
        
        me = self._target.data
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[index].value = 2
        me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[index].vector = d
        
        indices = [index, ]
        
        if(len(self._stroke_locations) >= 2):
            a = self._stroke_locations[-2]
            b = self._stroke_locations[-1]
            n = b - a
            n.normalize()
            
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[index - 1].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[index - 1].vector = n
            indices.append(index - 1)
        
        # NOTE: sanitize indices
        i = int(self._get_target_vertex_index_to_masked_index([index, ], )[0])
        indices = [i, ]
        
        self._regenerate_rotation_from_attributes(np.array(indices, dtype=int, ), )
        
        # TODO: until `_regenerate_rotation_from_attributes` is fully numpyfied, return False, after it can return True so it is updated once
        # TODO: hmmm? `_regenerate_rotation_from_attributes` does not trigger? modifying vertex attributes does not trigger update?
        return True
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            d = self._get_prop_value('distance')
            ms = self._widgets_compute_surface_matrix_scale_component_3d(d, )
            cm = mt @ mr @ ms
            
            ls.extend((
                # distance helper circle
                {
                    'function': 'circle_outline_dashed_3d',
                    'arguments': {
                        'matrix': cm,
                        'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                        'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
            ))
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            if(event.ctrl):
                woc = self._theme._outline_color_eraser
                wfc = self._theme._fill_color_eraser
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            if(not event.ctrl):
                d = self._get_prop_value('distance')
                if(self._get_prop_value('distance_pressure')):
                    d = d * self._pressure
                ms = self._widgets_compute_surface_matrix_scale_component_3d(d, )
                cm = mt @ mr @ ms
                
                ls.extend((
                    # distance helper circle
                    {
                        'function': 'circle_outline_dashed_3d',
                        'arguments': {
                            'matrix': cm,
                            'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                            'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                ))
                
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
                
                # stroke connection lines only when some points already exist
                if(len(self._stroke_locations)):
                    vertices = np.array([v.to_tuple() for v in self._stroke_locations], dtype=np.float32, )
                    # and connect to 3d mouse
                    vertices = np.concatenate([vertices, np.array(self._mouse_3d_loc.to_tuple(), dtype=np.float32, ).reshape(-1, 3)])
                    i = np.arange(len(vertices))
                    indices = np.c_[i, np.roll(i, -1), ]
                    indices = indices[:-1]
                    indices = indices.astype(np.int32)
                    
                    ls.extend((
                        # stroke connection lines
                        {
                            'function': 'multiple_thick_lines_3d',
                            'arguments': {
                                'vertices': vertices,
                                'indices': indices,
                                'matrix': Matrix(),
                                'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                                'thickness': self._theme._outline_thickness_helper,
                            }
                        },
                    ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
        else:
            self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: brush
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_fixed_radius_size()
                
                # NOTE: eraser should break stroke
                self._stroke_locations = []
                self._stroke_directions = []
            else:
                self._stroke_locations.append(loc)
                if(self._mouse_3d_direction):
                    self._stroke_directions.append(self._mouse_3d_direction)
                else:
                    self._stroke_directions.append(Vector())
                
                self._store_vertex(loc, nor, )
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_fixed_radius_size()
                
                # NOTE: eraser should break stroke
                self._stroke_locations = []
                self._stroke_directions = []
            else:
                if(not len(self._stroke_locations)):
                    # NOTE: in case i started with eraser first
                    self._stroke_locations.append(loc)
                    if(self._mouse_3d_direction):
                        self._stroke_directions.append(self._mouse_3d_direction)
                    else:
                        self._stroke_directions.append(Vector())
                    
                    self._store_vertex(loc, nor, )
                    return
                
                a = self._stroke_locations[-1]
                b = loc
                d = self._distance_vectors_3d(a, b)
                fd = self._get_prop_value('distance')
                if(self._get_prop_value('distance_pressure')):
                    fd = fd * self._pressure
                
                if(fd <= d):
                    # NOTE: why it is getting slower with more point when i use just last point from path with new one?
                    n = b - a
                    n.normalize()
                    direction = n
                    c = Vector((a.x + fd * n.x, a.y + fd * n.y, a.z + fd * n.z, ))
                    if(self._get_prop_value('divergence') > 0.0):
                        d = self._get_prop_value('divergence')
                        if(self._get_prop_value('divergence_pressure')):
                            d = d * self._pressure
                        
                        v = direction.cross(nor)
                        if(random.random() < 0.5):
                            v.negate()
                        
                        d = d * random.random()
                        c = c + (v.normalized() * d)
                        
                        lp = self._stroke_locations[-1]
                        cc = c - lp
                        cc.normalize()
                        cc.length = fd
                        c = lp + cc
                    
                    # find it again, because target polygon and normal can change while coorecting distance
                    loc, nor, idx, dst = self._bvh.find_nearest(c)
                    nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
                    
                    self._stroke_locations.append(loc)
                    self._stroke_directions.append(direction)
                    
                    self._store_vertex(loc, nor, )
        else:
            # NOTE: mouse left surface, restart?
            self._stroke_locations = []
            self._stroke_directions = []
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._stroke_locations = []
        self._stroke_directions = []
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_chain'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        self._action_execute_on = 'BOTH'
        self._action_timer_interval = 0.1
        
        # NOTE: brush specific props..
        self._stroke_locations = []
        self._stroke_directions = []


class SCATTER5_OT_manual_brush_tool_spatter(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_spatter"
    bl_label = "Spatter Brush"
    bl_description = "Spatter Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_spatter"
    tool_category = 'CREATE'
    tool_label = "Spatter Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'divergence',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20 * 10,
            'text': '{}: {:.3f}',
            'name': 'Divergence',
            'widget': 'LENGTH_3D',
        },
        '__gesture_secondary__': {
            'property': 'interval',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Interval',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Erase: CTRL+LMB",
    )
    
    icon = "W_PENCIL"
    dat_icon = "SCATTER5_SPATTER"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: overrides
    
    def _store_vertex_before(self, loc, nor, uid, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return False if nothing can be stored because of some condition
        if(self._get_prop_value('use_align_y_to_stroke')):
            # NOTE: if brush is invoked by shortcut and mouse is not moved, following will fail and point will be rejected until mouse is moved
            
            # if align is enabled, but mouse did not moved yet, skip until it moves so i have direction to use.. this is preventing having the first instance oriented in wrong direction..
            if(self._stroke_directions[-1].length == 0.0):
                return False
            
            if(self._mouse_3d_direction is None):
                return False
            if(self._mouse_3d_direction_interpolated is None):
                return False
        
        return True
    
    def _store_vertex_after(self, index, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return True if mesh data need to be updated, for example when operation is fully numpyfied, blender will not be triggered to update itself
        
        if(self._get_prop_value('use_align_y_to_stroke')):
            d = self._stroke_directions[-1]
            if(self._get_prop_value('use_direction_interpolation')):
                d = self._mouse_3d_direction_interpolated
            
            me = self._target.data
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[index].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[index].vector = d
            
            # NOTE: sanitize indices
            i = int(self._get_target_vertex_index_to_masked_index([index, ], )[0])
            indices = [i, ]
            
            self._regenerate_rotation_from_attributes(indices, )
            
            # TODO: until `_regenerate_rotation_from_attributes` is fully numpyfied, return False, after it can return True so it is updated once
            # TODO: hmmm? `_regenerate_rotation_from_attributes` does not trigger? modifying vertex attributes does not trigger update?
            return True
        
        return True
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            d = self._get_prop_value('divergence')
            ms = self._widgets_compute_surface_matrix_scale_component_3d(d, )
            cm = mt @ mr @ ms
            
            ls.extend((
                # distance helper circle
                {
                    'function': 'circle_outline_dashed_3d',
                    'arguments': {
                        'matrix': cm,
                        'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                        'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
            ))
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            if(event.ctrl):
                woc = self._theme._outline_color_eraser
                wfc = self._theme._fill_color_eraser
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            if(not event.ctrl):
                d = self._get_prop_value('divergence')
                if(self._get_prop_value('divergence_pressure')):
                    d = d * self._pressure
                ms = self._widgets_compute_surface_matrix_scale_component_3d(d, )
                cm = mt @ mr @ ms
                
                ls.extend((
                    # distance helper circle
                    {
                        'function': 'circle_outline_dashed_3d',
                        'arguments': {
                            'matrix': cm,
                            'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                            'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                ))
                
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
        else:
            self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: brush
    
    def _action_generate(self, loc, nor, ):
        d = self._get_prop_value('divergence')
        if(d > 0.0):
            if(self._get_prop_value('divergence_pressure')):
                d = d * self._pressure
            r = d * np.random.random()
            a = (2 * np.pi) * np.random.random()
            x = r * np.cos(a)
            y = r * np.sin(a)
            z = 0.0
            v = Vector((x, y, z, ))
            z = Vector((0.0, 0.0, 1.0, ))
            q = self._rotation_to(z, nor, )
            v.rotate(q)
            c = loc + v
            loc, nor, idx, dst = self._bvh.find_nearest(c)
            nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
        return loc, nor
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_fixed_radius_size()
                
                # NOTE: eraser should break stroke
                self._stroke_locations = []
                self._stroke_directions = []
            else:
                self._stroke_locations.append(loc)
                if(self._mouse_3d_direction):
                    self._stroke_directions.append(self._mouse_3d_direction)
                else:
                    self._stroke_directions.append(Vector())
                
                loc, nor = self._action_generate(loc, nor, )
                self._store_vertex(loc, nor, )
    
    # @verbose
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_fixed_radius_size()
                
                # NOTE: eraser should break stroke
                self._stroke_locations = []
                self._stroke_directions = []
            else:
                self._stroke_locations.append(loc)
                if(self._mouse_3d_direction):
                    self._stroke_directions.append(self._mouse_3d_direction)
                else:
                    self._stroke_directions.append(Vector())
                
                loc, nor = self._action_generate(loc, nor, )
                self._store_vertex(loc, nor, )
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._stroke_locations = []
        self._stroke_directions = []
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_spatter'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        # NOTE: brush specific props..
        self._stroke_locations = []
        self._stroke_directions = []


# DONE: i've seen it adding a vertex at 0,0,0. investigate..
# DONE: cursor widget as radius circle + jet cone + reach dashed circle + maybe dot in the middle of radius, get rif of all other elements
# DONE: cone widget seems to be larger then actual result --> was an error in reach calculation
# DONE: there is some falloff happening, expose that to user as setting and draw to widget, so it is similar to modify brushes --> reach circle drawing
# DONE: get rid of spray jet cone -> last attempt, a lot smaller than before, if i ever going to change it again, i will remove it
class SCATTER5_OT_manual_brush_tool_spray(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_spray"
    bl_label = "Spray Brush"
    bl_description = "Spray Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_spray"
    tool_category = 'CREATE'
    tool_label = "Spray Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_wheel': 20,
            'change_pixels': 1,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'num_dots',
            'datatype': 'int',
            'change': 1,
            'change_pixels': 5,
            'change_wheel': 20,
            'text': '{}: {:d}',
            'name': 'Points Per Interval',
            'widget': 'COUNT_3D',
        },
        '__gesture_tertiary__': {
            'property': 'interval',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Interval',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Erase: CTRL+LMB",
    )
    
    icon = "W_SPRAY"
    dat_icon = "SCATTER5_SPRAY"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            m = mt @ mr @ ms
            
            r = self._domain_aware_brush_radius()
            h = self._get_prop_value('jet') * r
            ms = Matrix(((radius, 0.0, 0.0, 0.0), (0.0, radius, 0.0, 0.0), (0.0, 0.0, h, 0.0), (0.0, 0.0, 0.0, 1.0)))
            jm = mt @ mr @ ms
            
            # radius
            b = self._domain_aware_brush_radius()
            # height
            a = self._get_prop_value('jet') * b
            # hypotenuse from height & radius
            c = np.sqrt(a ** 2 + b ** 2)
            # angle opposite of b, between a and c
            beta = np.arctan(b / a)
            # add reach (behind mouse 3d location)
            c += self._get_prop_value('reach')
            # new a
            aa = c * np.cos(beta)
            # new b
            bb = c * np.sin(beta)
            # location of reach circle
            rloc = loc - (nor * (aa - a))
            # matrix
            _mt = Matrix.Translation(rloc)
            ms = self._widgets_compute_surface_matrix_scale_component_xy_3d(bb, )
            rm = _mt @ mr @ ms
            
            ls = [
                # radius circle
                {
                    'function': 'circle_outline_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                {
                    'function': 'circle_fill_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': wfc,
                    }
                },
                # jet cone
                {
                    'function': 'cone_3d',
                    'arguments': {
                        'height': 1.0,
                        'matrix': jm,
                        'steps': self._theme._circle_steps,
                        'color': wfc[:3] + (self._theme._fill_color_helper_alpha, ),
                    }
                },
                # reach circle
                {
                    'function': 'circle_outline_dashed_3d',
                    'arguments': {
                        'matrix': rm,
                        'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                        'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
            ]
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            if(event.ctrl):
                woc = self._theme._outline_color_eraser
                wfc = self._theme._fill_color_eraser
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            m = mt @ mr @ ms
            
            ls = [
                # radius circle
                {
                    'function': 'circle_outline_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                {
                    'function': 'circle_fill_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': wfc,
                    }
                },
            ]
            
            if(not event.ctrl):
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
        else:
            self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: brush
    
    # NOTE: removed some loops, but not all, loops left: normal quaternios, bvh.ray_cast (for all) and bvh.find_nearest (for hits)
    # @stopwatch
    def _spray_generate_np(self, loc, nor, ):
        brush_radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            brush_radius = brush_radius * self._pressure
        
        num_dots = self._get_prop_value('num_dots')
        if(self._get_prop_value('num_dots_pressure')):
            num_dots = int(self._get_prop_value('num_dots') * self._pressure)
            if(num_dots == 0):
                # draw at least one..
                num_dots = 1
        else:
            num_dots = self._get_prop_value('num_dots')
        
        '''
        rnd = random.Random()
        
        # radius in radians from 0.0 to math.pi to be somewhat useable
        def rnd_in_cone(radius, ):
            # http://answers.unity.com/comments/1324674/view.html
            z = rnd.uniform(math.cos(radius), 1)
            t = rnd.uniform(0, math.pi * 2)
            v = Vector((math.sqrt(1 - z * z) * math.cos(t), math.sqrt(1 - z * z) * math.sin(t), z))
            return v
        '''
        
        # height
        d = self._get_prop_value('jet') * brush_radius
        
        # hypotenuse from height & radius
        max_d = np.sqrt(d ** 2 + brush_radius ** 2)
        # add reach (behind mouse 3d location)
        max_d += self._get_prop_value('reach')
        
        # NOTE: epsilon of the same value as bvh epsilon result in around half of points being discarded
        epsilon = 0.001
        epsilon_d = epsilon * 2
        
        origin = loc + (nor * d)
        
        # # DEBUG
        # debug.points(self._target, origin, )
        # # DEBUG
        
        vs = np.zeros((num_dots, 3, ), dtype=float, )
        ns = np.zeros((num_dots, 3, ), dtype=float, )
        uids = np.zeros((num_dots, ), dtype=int, )
        
        # cone slice = right angle triangle so:
        angle = math.atan(brush_radius / d)
        angle = angle * 2
        
        _l = num_dots
        _origin = np.array(origin, dtype=float, )
        _directions = np.zeros((_l, 3, ), dtype=float, )
        _rng = np.random.default_rng()
        _axes = (_rng.random((_l, 3, )) - 0.5) * 2.0
        
        def normalize(v):
            with np.errstate(divide='ignore', invalid='ignore', ):
                r = v / np.linalg.norm(v, axis=1, ).reshape((-1, 1, ))
                return np.nan_to_num(r)
        
        _axes = normalize(_axes)
        _r = _rng.random((_l, 1, ))
        _a = (_r - 0.5) * angle
        # NOTE: get rid of loop somehow?
        for i, _axis in enumerate(_axes):
            _q = Quaternion(_axis, _a[i])
            _d = nor * (-1.0)
            _d.rotate(_q)
            _directions[i] = _d
        
        # # DEBUG
        # debug.points(self._target, np.full((len(_directions), 3), _origin), _directions, )
        # # DEBUG
        
        _locs = np.zeros((_l, 3), dtype=float, )
        _nors = np.zeros((_l, 3), dtype=float, )
        _idxs = np.zeros(_l, dtype=int, )
        _dsts = np.zeros(_l, dtype=float, )
        _status = np.zeros(_l, dtype=bool, )
        for i in np.arange(num_dots):
            _loc, _nor, _idx, _dst = self._bvh.ray_cast(_origin, _directions[i], )
            if(_loc):
                _status[i] = True
                _locs[i] = _loc
                _nors[i] = _nor
                _idxs[i] = _idx
                _dsts[i] = _dst
        
        def distance(a, b, ):
            return ((a[:, 0] - b[:, 0]) ** 2 + (a[:, 1] - b[:, 1]) ** 2 + (a[:, 2] - b[:, 2]) ** 2) ** 0.5
        
        _dd = distance(np.full((_l, 3, ), _origin, dtype=float, ), _locs, )
        _mask = _dd < max_d
        
        _cache_f_surface = ToolSessionCache._cache['arrays']['f_surface']
        _indices = np.arange(_l)
        for i in _indices:
            if(not _mask[i]):
                _status[i] = False
                continue
            
            co, _, _, _ = self._bvh.find_nearest(_locs[i], epsilon_d, )
            if(co is None):
                _status[i] = False
                continue
            
            vs[i] = _locs[i]
            _nor = self._interpolate_smooth_face_normal(_locs[i], _nors[i], _idxs[i], )
            ns[i] = _nor
            uids[i] = _cache_f_surface[_idxs[i]]
        
        vs = vs[_status]
        ns = ns[_status]
        uids = uids[_status]
        
        if(self._get_prop_value('use_minimal_distance')):
            minimal_distance = self._get_prop_value('minimal_distance')
            if(self._get_prop_value('minimal_distance_pressure')):
                minimal_distance = minimal_distance * self._pressure
            
            if(len(vs) > 0):
                # filter new points with each other
                indices = []
                for i, v in enumerate(vs):
                    if(len(indices) > 0):
                        fvs, fds, fii = self._distance_range(vs[indices], v, minimal_distance, )
                        if(len(fii) > 0):
                            continue
                    indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
            
            locations = self._get_target_attribute_masked(self._target.data.vertices, 'co', )
            locations_uids = self._get_target_attribute_masked(self._target.data.attributes, 'surface_uuid', )
            
            locations, _ = self._surfaces_to_world_space(locations, None, locations_uids, )
            
            if(len(vs) > 0 and len(locations) > 0):
                # filter new points with existing points
                indices = []
                for i, v in enumerate(vs):
                    fvs, fds, fii = self._distance_range(locations, v, minimal_distance, )
                    if(len(fii) == 0):
                        indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
        
        return vs, ns, uids
    
    # @stopwatch
    def _spray_generate_uniform_np(self, loc, nor, ):
        brush_radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            brush_radius = brush_radius * self._pressure
        
        num_dots = self._get_prop_value('num_dots')
        if(self._get_prop_value('num_dots_pressure')):
            num_dots = int(self._get_prop_value('num_dots') * self._pressure)
            if(num_dots == 0):
                # draw at least one..
                num_dots = 1
        else:
            num_dots = self._get_prop_value('num_dots')
        
        d = self._get_prop_value('jet') * brush_radius
        max_d = np.sqrt(d ** 2 + brush_radius ** 2)
        max_d += self._get_prop_value('reach')
        
        # NOTE: epsilon of the same value as bvh epsilon result in around half of points being discarded
        epsilon = 0.001
        epsilon_d = epsilon * 2
        
        origin = loc + (nor * d)
        vs = np.zeros((num_dots, 3, ), dtype=float, )
        ns = np.zeros((num_dots, 3, ), dtype=float, )
        uids = np.zeros((num_dots, ), dtype=int, )
        
        rng = np.random.default_rng()
        theta = rng.uniform(0.0, 2.0 * np.pi, num_dots)
        r = brush_radius * (rng.uniform(0.0, 1.0, num_dots) ** 0.5)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = np.zeros(num_dots, dtype=float, )
        cpoints = np.c_[x, y, z]
        
        m = self._direction_to_rotation(nor).to_matrix().to_4x4()
        cpoints, _ = self._apply_matrix(m, cpoints, None)
        
        cpoints += loc
        
        def normalize(v):
            with np.errstate(divide='ignore', invalid='ignore', ):
                r = v / np.linalg.norm(v, axis=1, ).reshape((-1, 1, ))
                return np.nan_to_num(r)
        
        directions = normalize(cpoints - np.array(origin, dtype=float, ))
        
        _l = num_dots
        _origin = np.array(origin, dtype=float, )
        _locs = np.zeros((_l, 3), dtype=float, )
        _nors = np.zeros((_l, 3), dtype=float, )
        _idxs = np.zeros(_l, dtype=int, )
        _dsts = np.zeros(_l, dtype=float, )
        _status = np.zeros(_l, dtype=bool, )
        for i in np.arange(_l):
            _loc, _nor, _idx, _dst = self._bvh.ray_cast(_origin, directions[i], )
            if(_loc):
                _status[i] = True
                _locs[i] = _loc
                _nors[i] = _nor
                _idxs[i] = _idx
                _dsts[i] = _dst
        
        def distance(a, b, ):
            return ((a[:, 0] - b[:, 0]) ** 2 + (a[:, 1] - b[:, 1]) ** 2 + (a[:, 2] - b[:, 2]) ** 2) ** 0.5
        
        _dd = distance(np.full((_l, 3, ), _origin, dtype=float, ), _locs, )
        _mask = _dd < max_d
        
        _cache_f_surface = ToolSessionCache._cache['arrays']['f_surface']
        _indices = np.arange(_l)
        for i in _indices:
            if(not _mask[i]):
                _status[i] = False
                continue
            
            co, _, _, _ = self._bvh.find_nearest(_locs[i], epsilon_d, )
            if(co is None):
                _status[i] = False
                continue
            
            vs[i] = _locs[i]
            _nor = self._interpolate_smooth_face_normal(_locs[i], _nors[i], _idxs[i], )
            ns[i] = _nor
            uids[i] = _cache_f_surface[_idxs[i]]
        
        vs = vs[_status]
        ns = ns[_status]
        uids = uids[_status]
        
        if(self._get_prop_value('use_minimal_distance')):
            minimal_distance = self._get_prop_value('minimal_distance')
            if(self._get_prop_value('minimal_distance_pressure')):
                minimal_distance = minimal_distance * self._pressure
            
            if(len(vs) > 0):
                # filter new points with each other
                indices = []
                for i, v in enumerate(vs):
                    if(len(indices) > 0):
                        fvs, fds, fii = self._distance_range(vs[indices], v, minimal_distance, )
                        if(len(fii) > 0):
                            continue
                    indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
            
            locations = self._get_target_attribute_masked(self._target.data.vertices, 'co', )
            locations_uids = self._get_target_attribute_masked(self._target.data.attributes, 'surface_uuid', )
            
            locations, _ = self._surfaces_to_world_space(locations, None, locations_uids, )
            
            if(len(vs) > 0 and len(locations) > 0):
                # filter new points with existing points
                indices = []
                for i, v in enumerate(vs):
                    fvs, fds, fii = self._distance_range(locations, v, minimal_distance, )
                    if(len(fii) == 0):
                        indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
        
        return vs, ns, uids
    
    def _action_begin_private(self, context, event, ):
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('TIMER', 'BOTH', )):
            # update interval value in case user changed it.
            # TODO: this should be included in base class i guess..
            self._action_timer_interval = self._get_prop_value('interval')
            bpy.app.timers.register(self._action_timer_private, first_interval=self._action_timer_interval, )
        
        self._action_begin()
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_real_radius()
            else:
                if(self._get_prop_value('uniform')):
                    vs, ns, uids = self._spray_generate_uniform_np(loc, nor, )
                else:
                    vs, ns, uids = self._spray_generate_np(loc, nor, )
                if(len(vs)):
                    self._store_vertices_np(vs, ns, uids, )
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_real_radius()
            else:
                if(self._get_prop_value('uniform')):
                    vs, ns, uids = self._spray_generate_uniform_np(loc, nor, )
                else:
                    vs, ns, uids = self._spray_generate_np(loc, nor, )
                if(len(vs)):
                    self._store_vertices_np(vs, ns, uids, )
    
    @verbose
    def _action_finish(self, ):
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._action_timer_interval = self._get_prop_value('interval')
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_spray'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = 'TIMER'
        self._action_timer_interval = self._get_prop_value('interval')
        
        # NOTE: brush specific props..


# DONE: i've seen spray adding a vertex at 0,0,0. aligned spray works alsmot the same. investigate..
# DONE: cursor widget as radius circle + jet cone + reach dashed circle + direction triangle + maybe dot in the middle of radius, get rif of all other elements
# DONE: get rid of spray jet cone -> last attempt, a lot smaller than before, if i ever going to change it again, i will remove it
# DONE: draw alignment as triangle on radius edge instead of middle line
class SCATTER5_OT_manual_brush_tool_spray_aligned(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_spray_aligned"
    bl_label = "Aligned Spray Brush"
    bl_description = "Aligned Spray Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_spray_aligned"
    tool_category = 'CREATE'
    tool_label = "Aligned Spray Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'num_dots',
            'datatype': 'int',
            'change': 1,
            'change_pixels': 5,
            'change_wheel': 20,
            'text': '{}: {:d}',
            'name': 'Points Per Interval',
            'widget': 'COUNT_3D',
        },
        '__gesture_tertiary__': {
            'property': 'interval',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Interval',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Erase: CTRL+LMB",
    )
    
    icon = "W_SPRAY"
    dat_icon = "SCATTER5_SPRAY_ALIGN"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: overrides
    
    def _store_vertices_np_before(self, vs, ns, uids, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return False if nothing can be stored because of some condition
        
        # NOTE: always aligned
        if(self._mouse_3d_direction is None):
            # skip event if user just went out of surface and now it is returning back, to have 3d direction i need to wait to another event to calculate direction..
            return False
        if(self._mouse_3d_direction_interpolated is None):
            # skip event if user just went out of surface and now it is returning back, to have 3d direction i need to wait to another event to calculate direction..
            return False
        
        return True
    
    def _store_vertices_np_after(self, indices, ):
        # NOTE: do some post modifications if needed, like aligning axis, or similar stuff
        # NOTE: return True if mesh data need to be updated, for example when operation is fully numpyfied, blender will not be triggered to update itself
        
        # NOTE: always aligned y to stroke
        
        me = self._target.data
        
        l = len(indices)
        ll = len(me.vertices)
        _l = ll - l
        
        up = np.full((l, 1), 2, dtype=int, )
        d = self._mouse_3d_direction
        if(self._get_prop_value('use_direction_interpolation')):
            d = self._mouse_3d_direction_interpolated
        upvec = np.full((l, 3), d, dtype=float, )
        
        def get_vectors(length, where, what, ):
            a = np.zeros(length * 3, dtype=float, )
            where.foreach_get(what, a)
            a.shape = (-1, 3)
            return a
        
        def get_floats(length, where, what, ):
            a = np.zeros(length, dtype=float, )
            where.foreach_get(what, a)
            a.shape = (-1, 1)
            return a
        
        def get_ints(length, where, what, ):
            a = np.zeros(length, dtype=int, )
            where.foreach_get(what, a)
            a.shape = (-1, 1)
            return a
        
        def set_data(data, where, what, ):
            where.foreach_set(what, data.flatten())
        
        a = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data
        d = get_ints(ll, a, 'value')
        d[_l:] = up
        set_data(d, a, 'value', )
        
        a = me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data
        d = get_vectors(ll, a, 'vector')
        d[_l:] = upvec
        set_data(d, a, 'vector', )
        
        indices = self._get_target_vertex_index_to_masked_index(indices, )
        
        self._regenerate_rotation_from_attributes(indices, )
        # TODO: until `_regenerate_rotation_from_attributes` is fully numpyfied, return False, after it can return True so it is updated once
        # TODO: hmmm? `_regenerate_rotation_from_attributes` does not trigger? modifying vertex attributes does not trigger update?
        
        # # DEBUG
        # vs = []
        # ns = []
        # uids = []
        # for i in indices:
        #     u = me.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[i].value
        #     v = me.vertices[i].co
        #     vs.append(v)
        #     ns.append(me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector)
        #     uids.append(u)
        #     vs.append(v)
        #     ns.append(me.attributes['{}align_y'.format(self.attribute_prefix)].data[i].vector)
        #     uids.append(u)
        #     vs.append(v)
        #     ns.append(me.attributes['{}align_z'.format(self.attribute_prefix)].data[i].vector)
        #     uids.append(u)
        # vs, ns = self._surfaces_to_world_space(np.array(vs, dtype=float, ), np.array(ns, dtype=float, ), np.array(uids, dtype=int, ), )
        # debug.points(self._target, vs, ns)
        # # DEBUG
        
        return True
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            m = mt @ mr @ ms
            
            r = self._domain_aware_brush_radius()
            h = self._get_prop_value('jet') * r
            ms = Matrix(((radius, 0.0, 0.0, 0.0), (0.0, radius, 0.0, 0.0), (0.0, 0.0, h, 0.0), (0.0, 0.0, 0.0, 1.0)))
            jm = mt @ mr @ ms
            
            # radius
            b = self._domain_aware_brush_radius()
            # height
            a = self._get_prop_value('jet') * b
            # hypotenuse from height & radius
            c = np.sqrt(a ** 2 + b ** 2)
            # angle opposite of b, between a and c
            beta = np.arctan(b / a)
            # add reach (behind mouse 3d location)
            c += self._get_prop_value('reach')
            # new a
            aa = c * np.cos(beta)
            # new b
            bb = c * np.sin(beta)
            # location of reach circle
            rloc = loc - (nor * (aa - a))
            # matrix
            _mt = Matrix.Translation(rloc)
            ms = self._widgets_compute_surface_matrix_scale_component_xy_3d(bb, )
            rm = _mt @ mr @ ms
            
            ls = [
                # radius circle
                {
                    'function': 'circle_outline_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                {
                    'function': 'circle_fill_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': wfc,
                    }
                },
                # jet cone
                {
                    'function': 'cone_3d',
                    'arguments': {
                        'height': 1.0,
                        'matrix': jm,
                        'steps': self._theme._circle_steps,
                        'color': wfc[:3] + (self._theme._fill_color_helper_alpha, ),
                    }
                },
                # reach circle
                {
                    'function': 'circle_outline_dashed_3d',
                    'arguments': {
                        'matrix': rm,
                        'steps': self._theme._circle_steps * self._theme._outline_dashed_steps_multiplier,
                        'color': woc[:3] + (self._theme._outline_color_falloff_helper_alpha, ),
                        'thickness': self._theme._outline_thickness_helper,
                    }
                },
            ]
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            if(self._mouse_3d_direction and self._mouse_3d_direction_interpolated):
                tri = self._widgets_fabricate_direction_triangle_3d(loc, nor, radius, woc, )
                ls.extend(tri)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            if(event.ctrl):
                woc = self._theme._outline_color_eraser
                wfc = self._theme._fill_color_eraser
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            m = mt @ mr @ ms
            
            ls = [
                # radius circle
                {
                    'function': 'circle_outline_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                {
                    'function': 'circle_fill_3d',
                    'arguments': {
                        'matrix': m,
                        'steps': self._theme._circle_steps,
                        'color': wfc,
                    }
                },
            ]
            
            if(not event.ctrl):
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
            
            if(not event.ctrl and self._mouse_3d_direction and self._mouse_3d_direction_interpolated):
                tri = self._widgets_fabricate_direction_triangle_3d(loc, nor, radius, woc, )
                ls.extend(tri)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
        else:
            self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: brush
    
    # NOTE: removed some loops, but not all, loops left: normal quaternios, bvh.ray_cast (for all) and bvh.find_nearest (for hits)
    # @stopwatch
    def _spray_generate_np(self, loc, nor, ):
        brush_radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            brush_radius = brush_radius * self._pressure
        
        num_dots = self._get_prop_value('num_dots')
        if(self._get_prop_value('num_dots_pressure')):
            num_dots = int(self._get_prop_value('num_dots') * self._pressure)
            if(num_dots == 0):
                # draw at least one..
                num_dots = 1
        else:
            num_dots = self._get_prop_value('num_dots')
        
        '''
        rnd = random.Random()
        
        # radius in radians from 0.0 to math.pi to be somewhat useable
        def rnd_in_cone(radius, ):
            # http://answers.unity.com/comments/1324674/view.html
            z = rnd.uniform(math.cos(radius), 1)
            t = rnd.uniform(0, math.pi * 2)
            v = Vector((math.sqrt(1 - z * z) * math.cos(t), math.sqrt(1 - z * z) * math.sin(t), z))
            return v
        '''
        
        # height
        d = self._get_prop_value('jet') * brush_radius
        
        # hypotenuse from height & radius
        max_d = np.sqrt(d ** 2 + brush_radius ** 2)
        # add reach (behind mouse 3d location)
        max_d += self._get_prop_value('reach')
        
        # NOTE: epsilon of the same value as bvh epsilon result in around half of points being discarded
        epsilon = 0.001
        epsilon_d = epsilon * 2
        
        origin = loc + (nor * d)
        vs = np.zeros((num_dots, 3, ), dtype=float, )
        ns = np.zeros((num_dots, 3, ), dtype=float, )
        uids = np.zeros((num_dots, ), dtype=int, )
        
        # cone slice = right angle triangle so:
        angle = math.atan(brush_radius / d)
        angle = angle * 2
        
        _l = num_dots
        _origin = np.array(origin, dtype=float, )
        _directions = np.zeros((_l, 3, ), dtype=float, )
        _rng = np.random.default_rng()
        _axes = (_rng.random((_l, 3, )) - 0.5) * 2.0
        
        def normalize(v):
            with np.errstate(divide='ignore', invalid='ignore', ):
                r = v / np.linalg.norm(v, axis=1, ).reshape((-1, 1, ))
                return np.nan_to_num(r)
        
        _axes = normalize(_axes)
        _r = _rng.random((_l, 1, ))
        _a = (_r - 0.5) * angle
        # NOTE: get rid of loop somehow?
        for i, _axis in enumerate(_axes):
            _q = Quaternion(_axis, _a[i])
            _d = nor * (-1.0)
            _d.rotate(_q)
            _directions[i] = _d
        
        _locs = np.zeros((_l, 3), dtype=float, )
        _nors = np.zeros((_l, 3), dtype=float, )
        _idxs = np.zeros(_l, dtype=int, )
        _dsts = np.zeros(_l, dtype=float, )
        _status = np.zeros(_l, dtype=bool, )
        for i in np.arange(num_dots):
            _loc, _nor, _idx, _dst = self._bvh.ray_cast(_origin, _directions[i], )
            if(_loc):
                _status[i] = True
                _locs[i] = _loc
                _nors[i] = _nor
                _idxs[i] = _idx
                _dsts[i] = _dst
        
        def distance(a, b, ):
            return ((a[:, 0] - b[:, 0]) ** 2 + (a[:, 1] - b[:, 1]) ** 2 + (a[:, 2] - b[:, 2]) ** 2) ** 0.5
        
        _dd = distance(np.full((_l, 3, ), _origin, dtype=float, ), _locs, )
        _mask = _dd < max_d
        
        _indices = np.arange(_l)
        _cache_f_surface = ToolSessionCache._cache['arrays']['f_surface']
        for i in _indices:
            if(not _mask[i]):
                _status[i] = False
                continue
            
            co, _, _, _ = self._bvh.find_nearest(_locs[i], epsilon_d, )
            if(co is None):
                _status[i] = False
                continue
            
            vs[i] = _locs[i]
            _nor = self._interpolate_smooth_face_normal(_locs[i], _nors[i], _idxs[i], )
            ns[i] = _nor
            uids[i] = _cache_f_surface[_idxs[i]]
        
        vs = vs[_status]
        ns = ns[_status]
        uids = uids[_status]
        
        if(self._get_prop_value('use_minimal_distance')):
            minimal_distance = self._get_prop_value('minimal_distance')
            if(self._get_prop_value('minimal_distance_pressure')):
                minimal_distance = minimal_distance * self._pressure
            
            if(len(vs) > 0):
                # filter new points with each other
                indices = []
                for i, v in enumerate(vs):
                    if(len(indices) > 0):
                        fvs, fds, fii = self._distance_range(vs[indices], v, minimal_distance, )
                        if(len(fii) > 0):
                            continue
                    indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
            
            locations = self._get_target_attribute_masked(self._target.data.vertices, 'co', )
            locations_uids = self._get_target_attribute_masked(self._target.data.attributes, 'surface_uuid', )
            
            locations, _ = self._surfaces_to_world_space(locations, None, locations_uids, )
            
            if(len(vs) > 0 and len(locations) > 0):
                # filter new points with existing points
                indices = []
                for i, v in enumerate(vs):
                    fvs, fds, fii = self._distance_range(locations, v, minimal_distance, )
                    if(len(fii) == 0):
                        indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
        
        return vs, ns, uids
    
    # @stopwatch
    def _spray_generate_uniform_np(self, loc, nor, ):
        brush_radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            brush_radius = brush_radius * self._pressure
        
        num_dots = self._get_prop_value('num_dots')
        if(self._get_prop_value('num_dots_pressure')):
            num_dots = int(self._get_prop_value('num_dots') * self._pressure)
            if(num_dots == 0):
                # draw at least one..
                num_dots = 1
        else:
            num_dots = self._get_prop_value('num_dots')
        
        d = self._get_prop_value('jet') * brush_radius
        max_d = np.sqrt(d ** 2 + brush_radius ** 2)
        max_d += self._get_prop_value('reach')
        
        # NOTE: epsilon of the same value as bvh epsilon result in around half of points being discarded
        epsilon = 0.001
        epsilon_d = epsilon * 2
        
        origin = loc + (nor * d)
        vs = np.zeros((num_dots, 3, ), dtype=float, )
        ns = np.zeros((num_dots, 3, ), dtype=float, )
        uids = np.zeros((num_dots, ), dtype=int, )
        
        rng = np.random.default_rng()
        theta = rng.uniform(0.0, 2.0 * np.pi, num_dots)
        r = brush_radius * (rng.uniform(0.0, 1.0, num_dots) ** 0.5)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = np.zeros(num_dots, dtype=float, )
        cpoints = np.c_[x, y, z]
        
        m = self._direction_to_rotation(nor).to_matrix().to_4x4()
        cpoints, _ = self._apply_matrix(m, cpoints, None)
        
        cpoints += loc
        
        def normalize(v):
            with np.errstate(divide='ignore', invalid='ignore', ):
                r = v / np.linalg.norm(v, axis=1, ).reshape((-1, 1, ))
                return np.nan_to_num(r)
        
        directions = normalize(cpoints - np.array(origin, dtype=float, ))
        
        _l = num_dots
        _origin = np.array(origin, dtype=float, )
        _locs = np.zeros((_l, 3), dtype=float, )
        _nors = np.zeros((_l, 3), dtype=float, )
        _idxs = np.zeros(_l, dtype=int, )
        _dsts = np.zeros(_l, dtype=float, )
        _status = np.zeros(_l, dtype=bool, )
        for i in np.arange(_l):
            _loc, _nor, _idx, _dst = self._bvh.ray_cast(_origin, directions[i], )
            if(_loc):
                _status[i] = True
                _locs[i] = _loc
                _nors[i] = _nor
                _idxs[i] = _idx
                _dsts[i] = _dst
        
        def distance(a, b, ):
            return ((a[:, 0] - b[:, 0]) ** 2 + (a[:, 1] - b[:, 1]) ** 2 + (a[:, 2] - b[:, 2]) ** 2) ** 0.5
        
        _dd = distance(np.full((_l, 3, ), _origin, dtype=float, ), _locs, )
        _mask = _dd < max_d
        
        _cache_f_surface = ToolSessionCache._cache['arrays']['f_surface']
        _indices = np.arange(_l)
        for i in _indices:
            if(not _mask[i]):
                _status[i] = False
                continue
            
            co, _, _, _ = self._bvh.find_nearest(_locs[i], epsilon_d, )
            if(co is None):
                _status[i] = False
                continue
            
            vs[i] = _locs[i]
            _nor = self._interpolate_smooth_face_normal(_locs[i], _nors[i], _idxs[i], )
            ns[i] = _nor
            uids[i] = _cache_f_surface[_idxs[i]]
        
        vs = vs[_status]
        ns = ns[_status]
        uids = uids[_status]
        
        if(self._get_prop_value('use_minimal_distance')):
            minimal_distance = self._get_prop_value('minimal_distance')
            if(self._get_prop_value('minimal_distance_pressure')):
                minimal_distance = minimal_distance * self._pressure
            
            if(len(vs) > 0):
                # filter new points with each other
                indices = []
                for i, v in enumerate(vs):
                    if(len(indices) > 0):
                        fvs, fds, fii = self._distance_range(vs[indices], v, minimal_distance, )
                        if(len(fii) > 0):
                            continue
                    indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
            
            locations = self._get_target_attribute_masked(self._target.data.vertices, 'co', )
            locations_uids = self._get_target_attribute_masked(self._target.data.attributes, 'surface_uuid', )
            
            locations.shape = (-1, 3)
            locations, _ = self._surfaces_to_world_space(locations, None, locations_uids, )
            
            if(len(vs) > 0 and len(locations) > 0):
                # filter new points with existing points
                indices = []
                for i, v in enumerate(vs):
                    fvs, fds, fii = self._distance_range(locations, v, minimal_distance, )
                    if(len(fii) == 0):
                        indices.append(i)
                vs = vs[indices]
                ns = ns[indices]
                uids = uids[indices]
        
        return vs, ns, uids
    
    def _action_begin_private(self, context, event, ):
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('TIMER', 'BOTH', )):
            # update interval value in case user changed it.
            # TODO: this should be included in base class i guess..
            self._action_timer_interval = self._get_prop_value('interval')
            bpy.app.timers.register(self._action_timer_private, first_interval=self._action_timer_interval, )
        
        self._action_begin()
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_real_radius()
            else:
                if(self._get_prop_value('uniform')):
                    vs, ns, uids = self._spray_generate_uniform_np(loc, nor, )
                else:
                    vs, ns, uids = self._spray_generate_np(loc, nor, )
                if(len(vs)):
                    self._store_vertices_np(vs, ns, uids, )
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl):
                self._modal_eraser_action_real_radius()
            else:
                if(self._get_prop_value('uniform')):
                    vs, ns, uids = self._spray_generate_uniform_np(loc, nor, )
                else:
                    vs, ns, uids = self._spray_generate_np(loc, nor, )
                if(len(vs)):
                    self._store_vertices_np(vs, ns, uids, )
    
    @verbose
    def _action_finish(self, ):
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._action_timer_interval = self._get_prop_value('interval')
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_spray_aligned'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = 'TIMER'
        self._action_timer_interval = self._get_prop_value('interval')
        
        # NOTE: brush specific props..


# DONE: do not create mesh from bmesh, use data from cache
class SCATTER5_OT_manual_brush_tool_lasso_fill(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_lasso_fill"
    bl_label = "Lasso Fill"
    bl_description = "Lasso Fill"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_lasso_fill"
    tool_category = 'CREATE'
    tool_label = "Lasso Fill"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'density',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Density',
            'widget': 'TOOLTIP_2D',
        },
        '__gesture_secondary__': {
            'property': 'omit_backfacing',
            'datatype': 'bool',
            'change': 1,
            'change_pixels': 1,
            'change_wheel': 1,
            'text': '{}: {}',
            'name': 'Omit Backfacing',
            'widget': 'BOOLEAN_2D',
        },
    }
    # tool_gesture_space = '3D'
    tool_gesture_space = '2D'
    tool_infobox = (
        "• Draw: LMB",
        "• Erase: CTRL+LMB",
    )
    
    icon = "SELECT_SET"
    dat_icon = "SCATTER5_LASSO_FILL"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    def _area_fill(self, ):
        c = ToolSessionCache._cache
        
        vs = c['arrays']['v_co'].copy()
        original_vs = vs.copy()
        ones = np.ones(len(vs), dtype=vs.dtype, )
        vs = np.c_[vs[:, 0], vs[:, 1], vs[:, 2], ones]
        
        tris = c['arrays']['f_vertices'].copy()
        smooth = c['arrays']['f_smooth'].copy().ravel()
        areas = c['arrays']['f_area'].copy().ravel()
        tri_indices = np.arange(len(tris), dtype=int, )
        
        # NOTE: NaN to zeros, quick and dirty fix for maformed meshes with NaN polygon area.
        # NOTE: zero areas are excluded from generation by `area_threshold` that should be never zero, but at minimum 0.0001 (property minimum in settings)
        # areas = np.nan_to_num(areas, nan=0.0, )
        # NOTE: exclude also +/- infinity
        areas = np.nan_to_num(areas, copy=True, nan=0.0, posinf=0.0, neginf=0.0, )
        
        # drawn polygon in 2d to arrays
        vertices = np.array(self._lasso_path, dtype=float, )
        indices = np.array(mathutils.geometry.tessellate_polygon((vertices, )), dtype=int, )
        
        # adjust coordinates to be the same for both, i.e. convert to normalized 2d coordinates x 0.0-1.0, y 0.0-1.0
        view = self._context_region_data.view_matrix
        projection = self._context_region_data.window_matrix
        vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
        # NOTE: mark (i can't remove them i guess) vertices behind view? and use that later? lets skip that for now..
        x = vs[:, 0]
        y = vs[:, 1]
        z = vs[:, 1]
        w = vs[:, 3]
        x_ndc = x / w
        y_ndc = y / w
        z_ndc = z / w
        x2d = (x_ndc + 1.0) / 2.0
        y2d = (y_ndc + 1.0) / 2.0
        # # NOTE: do i need some depth? lets go with zeros for now
        # z = np.zeros(len(vs), dtype=float, )
        # vs2d = np.c_[x2d, y2d, z]
        vs2d = np.c_[x2d, y2d]
        
        # and normalize path from pixels to 0.0-1.0
        vertices2d = np.zeros((len(vertices), 2), dtype=float, )
        vertices2d[:, 0] = vertices[:, 0] * (1.0 / self._context_region.width)
        vertices2d[:, 1] = vertices[:, 1] * (1.0 / self._context_region.height)
        
        # slice box border points
        pmin_xy = np.array([np.min(vertices2d[:, 0]), np.min(vertices2d[:, 1]), ], dtype=float, )
        pmax_xy = np.array([np.max(vertices2d[:, 0]), np.max(vertices2d[:, 1]), ], dtype=float, )
        
        vtris = vs2d[tris]
        # slice between min to max in x and y
        a = (vtris[:, :, 0] >= pmin_xy[0]) & (vtris[:, :, 0] <= pmax_xy[0])
        b = (vtris[:, :, 1] >= pmin_xy[1]) & (vtris[:, :, 1] <= pmax_xy[1])
        # include all triangles that have any vertex selected by box
        mask = a.any(axis=1, ) & b.any(axis=1, )
        
        # now the slow part..
        rtris = tris[mask]
        rvs2d = vs2d[rtris]
        
        # bvh from path polygons
        z = np.zeros(len(vertices2d), dtype=float, )
        vertices2d_3d = np.c_[vertices2d[:, 0], vertices2d[:, 1], z, ]
        pbvh = BVHTree.FromPolygons(vertices2d_3d.tolist(), indices.tolist(), all_triangles=True, epsilon=0.0, )
        
        # raycast triangle vertices to path bvh
        rc_mask = np.zeros(len(rvs2d), dtype=bool, )
        direction = Vector((0.0, 0.0, 1.0))
        for i, tri in enumerate(rvs2d):
            for v in tri:
                origin = (v[0], v[1], -1.0, )
                loc, _, _, _ = pbvh.ray_cast(origin, direction, )
                if(loc is not None):
                    rc_mask[i] = True
                    continue
        
        a = tri_indices[mask]
        selected_tris_indices = a[rc_mask]
        
        # when drawn area does not cover any surface vertex i need to raycast area vertices to surface
        if(not len(selected_tris_indices)):
            z = np.zeros(len(vs2d), dtype=float, )
            vs2d_3d = np.c_[vs2d[:, 0], vs2d[:, 1], z, ]
            s_bvh = BVHTree.FromPolygons(vs2d_3d.tolist(), tris.tolist(), all_triangles=True, epsilon=0.0, )
            s_rc_indices = np.zeros(len(vertices2d), dtype=int, )
            # fill it with -1, without it i will always have one false positive face with index 0
            s_rc_indices = s_rc_indices - 1
            direction = Vector((0.0, 0.0, 1.0))
            for i, v in enumerate(vertices2d):
                origin = (v[0], v[1], -1.0, )
                loc, _, idx, _ = s_bvh.ray_cast(origin, direction, )
                if(loc is not None):
                    s_rc_indices[i] = idx
            # found = np.unique(s_rc_indices)
            # remove negative indices. and filter out only unique indices
            found = np.unique(s_rc_indices[s_rc_indices >= 0])
            if(len(found)):
                selected_tris_indices = found
        
        # still nothing selected, euther path is drawn outside of surface or something strange happened
        if(not len(selected_tris_indices)):
            # no face selected..
            return
        
        # select data
        sel_tris = tris[selected_tris_indices]
        sel_areas = areas[selected_tris_indices]
        sel_vertices = original_vs[sel_tris]
        
        area_threshold = self._get_prop_value('area_threshold')
        m = (sel_areas < area_threshold)
        sel_areas = sel_areas.copy()
        sel_areas[m] = area_threshold
        
        total_area = np.sum(sel_areas)
        total_points = int(total_area * self._get_prop_value('density'))
        if(self._get_prop_value('max_points_per_fill') > 0):
            if(total_points > self._get_prop_value('max_points_per_fill')):
                # TODO: maybe take advantage of `ex` and if more that 1, slice somewhat later points down, so i can get better results with low count values
                # TODO: only problem with this is, it will then fail as safety check, so number of points can get crazy before it is used
                # TODO: maybe go with max_points_per_fill * 2 for generating, the slice down on final value after generating
                total_points = self._get_prop_value('max_points_per_fill')
        weights = sel_areas / np.sum(sel_areas)
        
        minn = np.min(total_points * weights)
        ex = 1
        if(minn < 1.0):
            if(minn != 0.0):
                ex = int(1.0 / minn)
            else:
                # if i have zero area triangle somewhere, go with this..
                ex = 10
        
        ex_max = 50
        if(ex >= ex_max):
            # prevent something really crazy.. don't know if this is good enough for all cases
            ex = ex_max
        
        total_points = total_points * ex
        
        nums = total_points * weights
        gen_nums = np.around(nums)
        gen_nums = gen_nums.astype(int)
        gen_nums_max = np.max(gen_nums)
        
        points = np.zeros((np.sum(gen_nums), 3), dtype=float, )
        rng = np.random.default_rng()
        pi = 0
        for ni, n in enumerate(gen_nums):
            a = np.full((n, 3), sel_vertices[ni][0], dtype=float, )
            b = np.full((n, 3), sel_vertices[ni][1], dtype=float, )
            c = np.full((n, 3), sel_vertices[ni][2], dtype=float, )
            r1 = rng.random(n).reshape((-1, 1))
            r2 = rng.random(n).reshape((-1, 1))
            ps = (1 - np.sqrt(r1)) * a + (np.sqrt(r1) * (1 - r2)) * b + (np.sqrt(r1) * r2) * c
            points[pi:pi + len(ps)] = ps
            pi += len(ps)
        
        if(ex != 1):
            rng.shuffle(points)
            points = points[::ex]
        
        pindices = np.arange(len(points), dtype=int, )
        
        # now 3d points to 2d 0.0-1.0 coords
        z = np.ones(len(points), dtype=float, )
        vs = np.c_[points[:, 0], points[:, 1], points[:, 2], z]
        vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
        x = vs[:, 0]
        y = vs[:, 1]
        z = vs[:, 1]
        w = vs[:, 3]
        x_ndc = x / w
        y_ndc = y / w
        z_ndc = z / w
        x2d = (x_ndc + 1.0) / 2.0
        y2d = (y_ndc + 1.0) / 2.0
        points2d = np.c_[x2d, y2d]
        
        # ray cast all points to path bvh so i have exact contour. basically throw away outside poinst and hope for the best
        # TODO: this could be optimized that i store array of indices of partly covered triangles and raycast only those (if i also store to which triangle point belongs in generation phase)
        mask = np.ones(len(points), dtype=bool, )
        direction = Vector((0.0, 0.0, 1.0))
        for i, v in enumerate(points2d):
            origin = (v[0], v[1], -1.0, )
            loc, _, _, _ = pbvh.ray_cast(origin, direction, )
            if(loc is None):
                mask[i] = False
        
        points = points[mask]
        
        # now omit points on backfacing polygons is user says so
        if(self._get_prop_value('omit_backfacing')):
            # # DEBUG
            # vs = []
            # ns = []
            # cs = []
            # # DEBUG
            
            mask = np.ones(len(points), dtype=bool, )
            # NOTE: this might be handy next time.. but not this time..
            # region = context.region
            # rv3d = context.region_data
            # w = region.width
            # h = region.height
            # eye_co = np.array(rv3d.view_matrix.inverted().translation, dtype=np.float32, ).reshape(-1, 3)
            # eye_no = np.array(view3d_utils.region_2d_to_vector_3d(region, rv3d, [w / 2, h / 2]).normalized(), dtype=np.float32, ).reshape(-1, 3)
            rv3d = self._context_region_data
            eye = Vector(rv3d.view_matrix.inverted().translation)
            t = self._get_prop_value('omit_backfacing_tolerance')
            for i, p in enumerate(points):
                p = Vector(p)
                d = p - eye
                d.normalize()
                loc, nor, idx, dst = self._bvh.ray_cast(eye, d, )
                
                if(loc is None):
                    # ray cast can go through sometimes.. lets ignore and throw away point in such case.
                    mask[i] = False
                    continue
                
                dd = ((loc.x - p.x) ** 2 + (loc.y - p.y) ** 2 + (loc.z - p.z) ** 2) ** 0.5
                
                # # DEBUG
                # vs.append(loc)
                # ns.append(nor)
                # if(dd > t):
                #     cs.append([dd, 0, 0, 1.0])
                # else:
                #     cs.append([dd, dd, dd, 1.0])
                # # DEBUG
                
                if(dd > t):
                    mask[i] = False
                    continue
            
            # # DEBUG
            # debug.points(self.target, vs, ns, cs)
            # # DEBUG
            
            points = points[mask]
        
        # now, generate normals from points, i have handy function for that already
        normals = np.zeros(points.shape, dtype=float, )
        # and get uids if i got face index for free here
        uids = np.zeros(len(points), dtype=int, )
        f_surface = ToolSessionCache._cache['arrays']['f_surface']
        for i, p in enumerate(points):
            loc, nor, idx, dst = self._bvh.find_nearest(p)
            n = self._interpolate_smooth_face_normal(loc, nor, idx, )
            normals[i] = n
            uids[i] = f_surface[idx]
        
        if(not len(points)):
            # NOTE: if no points left, or area is too small for any to be generated, prevent storing zero points
            # NOTE: normally it will be ok, but because of eulers list comp i use list, zero length array would be not a problem
            return
        
        self._store_vertices_np(points, normals, uids, )
    
    def _area_erase(self, ):
        # drawn polygon
        vertices = np.array(self._lasso_path, dtype=float, )
        tris = np.array(mathutils.geometry.tessellate_polygon((vertices, )), dtype=int, )
        # and normalize from pixels to 0.0-1.0
        vertices2d = np.zeros((len(vertices), 2), dtype=float, )
        vertices2d[:, 0] = vertices[:, 0] * (1.0 / self._context_region.width)
        vertices2d[:, 1] = vertices[:, 1] * (1.0 / self._context_region.height)
        
        vs = self._get_target_attribute_masked(self._target.data.vertices, 'co', )
        vs_orig = vs.copy()
        uids = self._get_target_attribute_masked(self._target.data.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        
        # to 2d ndc
        z = np.ones(len(vs), dtype=float, )
        vs = np.c_[vs[:, 0], vs[:, 1], vs[:, 2], z]
        # model = self._surface.matrix_world
        view = self._context_region_data.view_matrix
        projection = self._context_region_data.window_matrix
        # vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
        # NOTE: mark (i can't remove them i guess) vertices behind view? and use that later? lets skip that for now..
        x = vs[:, 0]
        y = vs[:, 1]
        z = vs[:, 1]
        w = vs[:, 3]
        x_ndc = x / w
        y_ndc = y / w
        z_ndc = z / w
        x2d = (x_ndc + 1.0) / 2.0
        y2d = (y_ndc + 1.0) / 2.0
        # # NOTE: do i need some depth? lets go with zeros for now
        # z = np.zeros(len(vs), dtype=float, )
        # vs2d = np.c_[x2d, y2d, z]
        vs2d = np.c_[x2d, y2d]
        
        m = np.zeros(len(vs), dtype=bool, )
        epsilon = 0.001
        a = np.c_[vertices2d[:, 0], vertices2d[:, 1], np.zeros(len(vertices2d), dtype=float, )]
        bvh = BVHTree.FromPolygons(a.tolist(), tris.tolist(), all_triangles=True, epsilon=0.0, )
        for i, v2d in enumerate(vs2d):
            v = [v2d[0], v2d[1], 0.0]
            _, _, _, d = bvh.find_nearest(v)
            if(d < epsilon):
                m[i] = True
        
        # now filter out points not visible if user wants to omit backfacing
        if(self._get_prop_value('omit_backfacing')):
            rv3d = self._context_region_data
            eye = Vector(rv3d.view_matrix.inverted().translation)
            t = self._get_prop_value('omit_backfacing_tolerance')
            for i in np.arange(len(m))[m]:
                p = model @ Vector(vs_orig[i])
                d = p - eye
                d.normalize()
                loc, nor, idx, dst = self._bvh.ray_cast(eye, d, )
                if(loc is None):
                    # ray cast can go through sometimes.. lets ignore and throw away point in such case.
                    m[i] = False
                    continue
                dd = ((loc.x - p.x) ** 2 + (loc.y - p.y) ** 2 + (loc.z - p.z) ** 2) ** 0.5
                if(dd > t):
                    m[i] = False
                    continue
        
        indices = np.arange(len(vs), dtype=int, )
        indices = indices[m]
        indices = self._get_masked_index_to_target_vertex_index(indices)
        mask = self._get_target_active_mask()
        m = np.zeros(len(mask), dtype=bool, )
        m[indices] = True
        
        # remove vertices.. finally
        bm = bmesh.new()
        bm.from_mesh(self._target.data)
        rm = []
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            if(m[i]):
                rm.append(v)
        for v in rm:
            bm.verts.remove(v)
        bm.to_mesh(self._target.data)
        bm.free()
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        
        c = (event.mouse_region_x, event.mouse_region_y, )
        
        ls = [
            # dot
            {
                'function': 'dot_shader_2_2d',
                'arguments': {
                    'center': c,
                    'diameter': self._theme._fixed_center_dot_radius * 2,
                    'color': woc,
                },
            },
        ]
        
        # v = 0.7071067690849304
        # v = self._theme._fixed_radius_default / 4 * v
        # vs = ((-v + c[0], -v + c[1], 0.0), (v + c[0], v + c[1], 0.0), (v + c[0], -v + c[1], 0.0), (-v + c[0], v + c[1], 0.0), )
        # es = ((0, 1), (2, 3), )
        # ls.extend((
        #     {
        #         'function': 'multiple_thick_line_2d',
        #         'arguments': {
        #             'vertices': vs,
        #             'indices': es,
        #             'color': woc,
        #             'thickness': self._theme._outline_thickness,
        #         }
        #     },
        # ))
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        if(event.ctrl):
            woc = self._theme._outline_color_eraser
            wfc = self._theme._fill_color_eraser
        
        f = self._lasso_path[0]
        l = self._lasso_path[-1]
        
        ls = [
            # first dot
            {
                'function': 'dot_shader_2_2d',
                'arguments': {
                    'center': f,
                    'diameter': self._theme._fixed_center_dot_radius * 2,
                    'color': woc,
                },
            },
            # last dot
            {
                'function': 'dot_shader_2_2d',
                'arguments': {
                    'center': l,
                    'diameter': self._theme._fixed_center_dot_radius * 2,
                    'color': woc,
                },
            },
            # area
            {
                'function': 'tri_fan_tess_fill_2d',
                'arguments': {
                    'vertices': self._lasso_path,
                    'color': wfc,
                },
            },
            {
                'function': 'tri_fan_tess_thick_outline_2d',
                'arguments': {
                    'vertices': self._lasso_path,
                    'color': woc,
                    'thickness': self._theme._outline_thickness,
                },
            },
        ]
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    def _widgets_modifiers_change(self, context, event, ):
        if(self._lmb):
            self._widgets_mouse_press(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._lasso_path = []
        self._lasso_path.append(self._mouse_2d_region.copy())
    
    def _action_update_inbetween(self, ):
        if(not self._get_prop_value('high_precision')):
            return
        
        self._lasso_path.append(self._mouse_2d_region.copy())
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._lasso_path.append(self._mouse_2d_region.copy())
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        
        self._lasso_path.append(self._mouse_2d_region.copy())
        
        if(self._ctrl):
            self._area_erase()
        else:
            self._area_fill()
        
        # # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._mouse_tracking_inbetween = self._get_prop_value('high_precision')
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_lasso_fill'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # self._cursor_modal_set = 'PAINT_BRUSH'
        # self._cursor_modal_set = 'NONE'
        self._mouse_tracking_inbetween = self._get_prop_value('high_precision')
        
        # NOTE: brush specific props..
        self._lasso_path = []
        self._eraser_modifier_flag = False


# ------------------------------------------------------------------ create brushes <<<
# ------------------------------------------------------------------ quasi create brushes >>>


# NOTTODO: decide if clone tool should rotate and scale at instance level. current behavior is like move tool, which is ok, but should it rotate and scale instances as well? only on instance level? on both levels? what would it look like? -->> current is ok. would be way too complicated..
# DONE: sample points, move mouse, start modal scale on mouse wheel, points will slightly rotate, investigate why. looks like either first transform is not good, or it is not updated on move. after that single initial rotation it seems to be stable. it also does that when it is modal roatted, only that change is not that wisible.. -->> added `_action_idle` to have some update function while lmb is not pressed
# DONE: refactor it.. there is some nasty residue from move brush.. -->> well.. it's a bit better. yes, a bit, a bit..
# NOTTODO: reposition on lmb + mouse move? like dot? or move? will be total spaghetti, but maybe it is worth a try -->> it's too much functionality at once.. confusing. it's meant to be clone stap like tool. don't like it? undo and try again.
# DONE: modal eraser is removing sample, while it is understandable why, would be better if all data from sample is saved and i don't need samplet vertices to clone on next action
# DONE: refactor that i don't rely on `_selection_indices` for everything, change it to `_sample_data`
# NOTTODO: can i use standard `_store_vertices_np` or `_store_vertex`? yeah i know, clone is different, but would halp if i have all in one place.. -->> clone is from arrays stored on tool, will be extra complexity
# NOTTODO: or, maybe better option, make `clone` standard operation in create mixin -->> see above
# DONE: options to scale and rotate at instance level so sample transforms as single unit
# DONE: cache sample until manual mode is exited
# DONE: remove eraser, will be different category
# DONE: some rotation math is not quite right, something between align z to surface, rotate instances and brush normal. find where it is and fix it..
# DONE: i think it is because i flatten sample, and then normals are used from brush. only then after new points are placed i get normals from surface. it that correct?
# WATCH: align z to normal (with or without) + rotate instances (with or without) + various sampled data with various state of alignment and original normal (per surface) + different new surface normal (per surface), all of this is mix that is hard to test. i tested many combinations and it looks fine. but better to watch that thing..
class SCATTER5_OT_manual_brush_tool_clone(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_clone"
    bl_label = "Clone Brush"
    bl_description = "Clone Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_clone"
    tool_category = 'TRANSLATE'
    tool_label = "Clone Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Sample: CTRL+SHIFT+LMB",
        "• Rotate Sample: CTRL+Mouse Wheel",
        "• Scale Sample: CTRL+ALT+Mouse Wheel",
    )
    
    icon = "W_CLICK"
    dat_icon = "SCATTER5_AREA_SAMPLE"
    
    _message_no_selection = "No points sampled"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    def _action_get_sample(self, ):
        me = self._target.data
        l = len(me.vertices)
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        ns = self._get_target_attribute_masked(me.attributes, 'normal', )
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        vs, ns = self._surfaces_to_world_space(vs, ns, uids, )
        
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        
        indices = self._selection_indices
        sel_vs = vs[indices]
        sel_ns = ns[indices]
        sel_uids = uids[indices]
        
        self._brush_prev_location = loc
        self._brush_prev_normal = nor
        self._brush_initial_location = loc.copy()
        self._brush_initial_normal = nor.copy()
        
        brush_radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            brush_radius = brush_radius * self._pressure
        
        # NOTE: pick points just above brush radius, is that good for something?
        # epsilon = 0.001
        epsilon = 0.0
        plane_loc = self._brush_prev_location + (self._brush_prev_normal.normalized() * (brush_radius + epsilon))
        plane_nor = self._brush_prev_normal.normalized()
        
        # move all points at brush plane along brush normal
        picked_vs = sel_vs.copy()
        picked_ns = sel_ns.copy()
        for i, co in enumerate(picked_vs):
            d = mathutils.geometry.distance_point_to_plane(co, plane_loc, plane_nor)
            picked_vs[i] = co + (plane_nor * (-d))
        picked_uids = sel_uids.copy()
        
        self._sample_vs = picked_vs.copy()
        # and move it all to center so i can freely rotate, and add brush location after again
        self._sample_vs = self._sample_vs - np.array(plane_loc)
        self._sample_ns = picked_ns.copy()
        self._sample_uids = picked_uids.copy()
        
        # arrays of all existing coords and attributes
        db = {}
        active_mask = self._get_target_active_mask()
        l = len(me.vertices)
        v = self._get_target_attribute_masked(me.vertices, 'co', mask=active_mask, )
        db['co'] = v[indices]
        for k, (t, d, ) in self.attribute_map.items():
            v = self._get_target_attribute_masked(me.attributes, k, mask=active_mask, )
            db[k] = v[indices]
        self._sample_data = db
        
        # # NOTE: and data for display..
        # # rotate from brush plane to '2d'
        # m = self._rotation_to(nor, Vector((0.0, 0.0, 1.0))).to_matrix().to_4x4()
        # vs = self._vs.copy()
        # vs = np.c_[vs[:, 0], vs[:, 1], vs[:, 2], np.ones(len(vs), dtype=vs.dtype, )]
        # vs = np.dot(m, vs.T)[0:4].T.reshape((-1, 4))
        # vs = vs[:, :3]
        # vs = vs.astype(np.float32)
        # # FIXMENOT: NOTWATCH: NOTTODO: NOTE: if i don't copy here, it will draw just mess, even though values, shape and dtype is the same. what is happening???
        # self._w_points = vs.copy()
        
        self._w_points = self._sample_vs + np.array(self._mouse_3d_loc, dtype=float, )
        ToolWidgets._tag_redraw()
        
        # # # DEBUG
        # debug.points(self._target, self._w_points)
        # # # DEBUG
        
        # # DEBUG
        # me = bpy.data.meshes.new('debug')
        # me.from_pydata(vs.tolist(), [], [])
        # o = bpy.data.objects.new('debug', me)
        # bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
        # # DEBUG
        
        # NOTE: to session tool cache, so i can get it back on next tool run
        self._copy_sample_data_to_cache()
    
    def _action_update_sample(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None or nor is None):
            # is also called from `_modal` and at that stage can be None
            return
        
        if(not self._sample_data):
            return
        
        if(self._brush_prev_location is None or self._brush_prev_normal is None):
            return
        
        # from old brush plane to new
        r = self._rotation_to(self._brush_prev_normal, nor).to_matrix().to_4x4()
        if(self._get_prop_value('use_align_z_to_surface')):
            # if align, also with normals
            self._sample_vs, self._sample_ns = self._apply_matrix(r, self._sample_vs, self._sample_ns, )
        else:
            self._sample_vs, _ = self._apply_matrix(r, self._sample_vs, None, )
        
        # set new brush plane normal
        self._brush_prev_normal = nor
        
        # i have some modal change
        if(self._modal_rotate_radians != 0.0):
            # rotate along brush plane normal as axis
            q = Quaternion(nor, self._modal_rotate_radians).to_matrix().to_4x4()
            if(self._get_prop_value('use_align_z_to_surface')):
                # if align, also with normals
                self._sample_vs, self._sample_ns = self._apply_matrix(q, self._sample_vs, self._sample_ns, )
            else:
                self._sample_vs, _ = self._apply_matrix(q, self._sample_vs, None, )
            
            if(self._get_prop_value('use_rotate_instances')):
                # for i, axis in enumerate(self._sample_ns):
                q = Quaternion(nor, self._modal_rotate_radians).to_matrix().to_4x4()
                for i in np.arange(len(self._sample_vs)):
                    a = self._sample_data['private_r_up'][i]
                    # global
                    y = Vector((0.0, 1.0, 0.0))
                    if(a == 1):
                        _, y = self._surfaces_to_world_space(Vector(), Vector((0.0, 1.0, 0.0, )), self._sample_data['surface_uuid'][i])
                    if(a == 2):
                        # custom
                        y = Vector(self._sample_data['private_r_up_vector'][i])
                    y.rotate(q)
                    y.normalize()
                    self._sample_data['private_r_up'][i] = 2
                    self._sample_data['private_r_up_vector'][i] = y.to_tuple()
            
            # zero out so it is ready for next
            self._modal_rotate_radians = 0.0
        
        # i have some modal scale
        if(self._modal_scale_factor != 0.0):
            self._sample_vs, _ = self._apply_matrix(Matrix.Scale(1.0 + self._modal_scale_factor, 4, ), self._sample_vs, None, )
            
            if(self._get_prop_value('use_scale_instances')):
                self._sample_data['private_s_base'] *= 1.0 + self._modal_scale_factor
            
            # zero out so it is ready for next
            self._modal_scale_factor = 0.0
        
        self._w_points = self._sample_vs + np.array(self._mouse_3d_loc, dtype=float, )
        ToolWidgets._tag_redraw()
        
        # NOTE: to session tool cache, so i can get it back on next tool run
        self._copy_sample_data_to_cache()
        
        # # # DEBUG
        # debug.points(self._target, self._w_points)
        # debug.points(self._target, self._sample_vs, self._sample_ns)
        # # # DEBUG
        
        # # NOTE: and data for display..
        # m = self._rotation_to(nor, Vector((0.0, 0.0, 1.0))).to_matrix().to_4x4()
        # vs = self._sample_vs.copy()
        # vs = np.c_[vs[:, 0], vs[:, 1], vs[:, 2], np.ones(len(vs), dtype=vs.dtype, )]
        # vs = np.dot(m, vs.T)[0:4].T.reshape((-1, 4))
        # vs = vs[:, :3]
        # vs = vs.astype(np.float32)
        # # FIXMENOT: NOTWATCH: NOTTODO: NOTE: if i don't copy here, it will draw just mess, even though values, shape and dtype is the same. what is happening???
        # self._w_points = vs.copy()
        
        # # # DEBUG
        # loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        # vs = self._sample_vs + np.array(loc, dtype=float, )
        # ns = self._sample_ns
        # debug.points(self._target, vs, ns, )
        # # # DEBUG
    
    def _action_clone(self, ):
        self._ensure_attributes()
        
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        me = self._target.data
        
        vs = self._sample_vs + np.array(loc, dtype=float, )
        ns = self._sample_ns
        
        surface_normals = np.zeros((len(ns), 3), dtype=float, )
        bnor = np.array(nor)
        for i, v in enumerate(vs):
            l, n, ii, d = self._bvh.ray_cast(v, bnor)
            l2, n2, ii2, d2 = self._bvh.ray_cast(v, bnor * -1.0)
            if(l is not None and l2 is not None):
                if(d > d2):
                    vv = l2
                    nn = n2
                else:
                    vv = l
                    nn = n
            elif(l is not None and l2 is None):
                vv = l
                nn = n
            elif(l is None and l2 is not None):
                vv = l2
                nn = n2
            else:
                # i did not hit anything.. try to recover from it..
                l3, n3, ii3, d3 = self._bvh.find_nearest(v, )
                vv = l3
                nn = n3
            vs[i] = vv
            surface_normals[i] = nn
        
        # # DEBUG
        # debug.points(self._target, vs, ns)
        # # DEBUG
        
        # arrays of all existing coords and attributes
        db = {}
        l = len(me.vertices)
        v = self._get_target_attribute_raw(me.vertices, 'co', )
        db['co'] = v
        for k, (t, d, ) in self.attribute_map.items():
            v = self._get_target_attribute_raw(me.attributes, k, )
            db[k] = v
        
        sample = self._sample_data
        
        if(self._get_prop_value('update_uuid')):
            f_surface = ToolSessionCache._cache['arrays']['f_surface']
            new_uids = np.zeros(self._sample_uids.shape, dtype=self._sample_uids.dtype, )
            for i, v in enumerate(vs):
                _, _, idx, _ = self._bvh.find_nearest(v, )
                new_uids[i] = f_surface[idx]
            self._sample_uids = new_uids
        
        vs, ns = self._world_to_surfaces_space(vs, ns, self._sample_uids, )
        
        old_normals = sample['normal'].copy()
        
        # clone all and update what is needed
        for k, v in db.items():
            a = sample[k].copy()
            if(k == 'co'):
                # use updated coordinates..
                a = vs
            elif(k == 'normal'):
                a = ns
            elif(k == 'id'):
                # update ids.. they should stay unique.. not that it is used now, but might in future
                a = self._gen_id(len(vs))
                a = a.astype(v.dtype)
            elif(k == 'surface_uuid'):
                a = self._sample_uids
            b = np.concatenate([v, a, ])
            db[k] = b
        
        # # DEBUG
        # debug.points(self._surface, db['co'].copy(), db['{}normal'.format(self.attribute_prefix)].copy())
        # # DEBUG
        
        # # DEBUG
        # # _vs, _ns = self._surfaces_to_world_space(vs, ns, self._sample_uids)
        # _vs = self._sample_vs + np.array(loc, dtype=float, )
        # _ns = self._sample_ns
        # debug.points(self._target, _vs, _ns)
        # # DEBUG
        
        # add vertices
        me.vertices.add(len(vs))
        
        # paste all data back
        self._set_target_attribute_raw(me.vertices, 'co', db['co'], )
        del db['co']
        
        for k, v in db.items():
            self._set_target_attribute_raw(me.attributes, k, v, )
        
        indices = np.arange(len(vs), dtype=int, ) + l
        
        already_regenerated = False
        
        iii = self._get_target_vertex_index_to_masked_index(indices, )
        
        if(self._get_prop_value('use_align_z_to_surface')):
            for i, ii in enumerate(indices):
                new_normal = Vector(surface_normals[i])
                me.attributes['{}normal'.format(self.attribute_prefix)].data[ii].vector = new_normal
                
                if(me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value == 3):
                    old_normal = Vector(old_normals[i])
                    q = self._rotation_to(old_normal, new_normal, )
                    a = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector)
                    a.rotate(q)
                    me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = a
            
            self._regenerate_rotation_from_attributes(iii, )
            already_regenerated = True
        
        if(self._get_prop_value('use_rotate_instances') and not already_regenerated):
            self._regenerate_rotation_from_attributes(iii, )
        
        if(self._get_prop_value('use_scale_instances')):
            self._regenerate_scale_from_attributes(iii, )
        
        me.update()
    
    def _copy_sample_data_to_cache(self, ):
        ToolSession.tool_cache[self.tool_id] = None
        
        d = {}
        for k, v in self._sample_data.items():
            d[k] = v.copy()
        ToolSession.tool_cache[self.tool_id] = {
            # dict, copied key by key
            '_sample_data': d,
            # numpy arrays, can copy
            '_sample_vs': self._sample_vs.copy(),
            '_sample_ns': self._sample_ns.copy(),
            '_w_points': self._w_points.copy(),
            # both should be Vector, can copy
            '_brush_prev_location': self._brush_prev_location.copy(),
            '_brush_prev_normal': self._brush_prev_normal.copy(),
        }
    
    def _load_sample_data_from_cache(self, ):
        if(self.tool_id in ToolSession.tool_cache.keys()):
            # if key exists, it should have all data available..
            tc = ToolSession.tool_cache[self.tool_id]
            self._sample_data = tc['_sample_data']
            self._sample_vs = tc['_sample_vs']
            self._sample_ns = tc['_sample_ns']
            self._w_points = tc['_w_points']
            self._brush_prev_location = tc['_brush_prev_location']
            self._brush_prev_normal = tc['_brush_prev_normal']
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            if(event.ctrl and event.shift):
                # NOTE: sample combo, show radius
                radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
                ls.extend(radoff)
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
                
                if(len(self._w_points)):
                    # NOTE: got old sample, show it as well
                    col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                    ls.extend((
                        {
                            'function': 'round_points_px_3d',
                            'arguments': {
                                'vertices': self._w_points,
                                'matrix': Matrix(),
                                'color': col,
                                'size': self._theme._point_size,
                            }
                        },
                    ))
                else:
                    # NOTE: no sample, tooltip
                    tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_no_selection, )
                    ls.extend(tooltip)
            else:
                if(len(self._w_points)):
                    # NOTE: paste
                    r = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
                    cms = self._widgets_compute_surface_matrix_scale_component_3d(r, )
                    cross = self._widgets_fabricate_fixed_size_crosshair_cursor_3d(mt, mr, cms, woc, )
                    ls.extend(cross)
                    dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                    ls.extend(dot)
                    
                    col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                    ls.extend((
                        {
                            'function': 'round_points_px_3d',
                            'arguments': {
                                'vertices': self._w_points,
                                'matrix': Matrix(),
                                'color': col,
                                'size': self._theme._point_size,
                            }
                        },
                    ))
                else:
                    # NOTE: no sample
                    radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
                    ls.extend(radoff)
                    dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                    ls.extend(dot)
                    tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_no_selection, )
                    ls.extend(tooltip)
            
            # v = 0.7071067690849304 / 10
            # vs = ((-v, -v, 0.0), (v, v, 0.0), (v, -v, 0.0), (-v, v, 0.0), )
            # es = ((0, 1), (2, 3), )
            # m = mt @ mr @ ms
            #
            # ls.extend((
            #     {
            #         'function': 'multiple_thick_lines_3d',
            #         'arguments': {
            #             'vertices': vs,
            #             'indices': es,
            #             'matrix': m,
            #             'color': woc,
            #             'thickness': self._theme._outline_thickness,
            #         }
            #     },
            # ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            if(event.ctrl and event.shift):
                # NOTE: sample combo, show radius
                radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
                ls.extend(radoff)
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
                
                if(len(self._w_points)):
                    # NOTE: got old sample, show it as well
                    col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                    ls.extend((
                        {
                            'function': 'round_points_px_3d',
                            'arguments': {
                                'vertices': self._w_points,
                                'matrix': Matrix(),
                                'color': col,
                                'size': self._theme._point_size,
                            }
                        },
                    ))
                else:
                    # NOTE: no sample, tooltip
                    tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_no_selection, )
                    ls.extend(tooltip)
            else:
                if(len(self._w_points)):
                    # NOTE: paste
                    r = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
                    cms = self._widgets_compute_surface_matrix_scale_component_3d(r, )
                    cross = self._widgets_fabricate_fixed_size_crosshair_cursor_3d(mt, mr, cms, woc, )
                    ls.extend(cross)
                    dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                    ls.extend(dot)
                    
                    col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                    ls.extend((
                        {
                            'function': 'round_points_px_3d',
                            'arguments': {
                                'vertices': self._w_points,
                                'matrix': Matrix(),
                                'color': col,
                                'size': self._theme._point_size,
                            }
                        },
                    ))
                else:
                    # NOTE: no sample
                    radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
                    ls.extend(radoff)
                    dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                    ls.extend(dot)
                    tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_no_selection, )
                    ls.extend(tooltip)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._ctrl and self._shift):
                # reset..
                self._modal_rotate_radians = 0.0
                self._modal_scale_factor = 0.0
                
                self._select()
                if(len(self._selection_indices)):
                    self._action_get_sample()
            else:
                if(self._sample_data):
                    self._action_clone()
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._lmb):
                self._action_update_sample()
            else:
                if(self._sample_data):
                    self._action_update_sample()
    
    def _action_idle(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(self._sample_data):
                self._action_update_sample()
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        if(self._get_prop_value('use_random_scale')):
            # uscale back
            l = self._last_random_scale_factor
            self._modal_scale_factor = (1.0 / (1.0 + l)) - 1.0
            self._action_update_sample()
            # scale with new random
            v = self._get_prop_value('random_scale_range')
            vmin = v[0]
            vmax = v[1]
            f = vmin + (vmax - vmin) * np.random.random()
            self._modal_scale_factor = f
            self._last_random_scale_factor = f
        
        if(self._get_prop_value('use_random_rotation')):
            self._modal_rotate_radians = np.pi * np.random.random()
        
        if(self._get_prop_value('use_random_rotation') or self._get_prop_value('use_random_scale')):
            self._action_update_sample()
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._action_timer_interval = self._get_prop_value('interval')
        self._action_execute_on = self._get_prop_value('draw_on')
    
    def _modal(self, context, event, ):
        # if i need something to be constantly refreshed.. not widgets..
        self._on_any_modal_event(context, event, )
        
        # update..
        self._context_region = context.region
        self._context_region_data = context.region_data
        # update settings..
        self._update_references_and_settings(context, event, )
        
        # ------------------------------------------------------------------------------------------
        # NOTE: inject into `_modal` and repeat all steps until gestures, this should ensure all is set for action
        
        if(event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', } and event.ctrl and not self._lmb):
            if(event.ctrl and event.alt):
                if(event.type == 'WHEELUPMOUSE'):
                    self._modal_scale_factor += self._modal_scale_increment
                if(event.type == 'WHEELDOWNMOUSE'):
                    self._modal_scale_factor -= self._modal_scale_increment
            elif(event.ctrl):
                if(event.type == 'WHEELUPMOUSE'):
                    self._modal_rotate_radians -= self._modal_rotate_increment
                    self._w_rotate_steps -= 1
                if(event.type == 'WHEELDOWNMOUSE'):
                    self._modal_rotate_radians += self._modal_rotate_increment
                    self._w_rotate_steps += 1
            
            self._action_update_sample()
            self._widgets_mouse_idle(context, event, )
            
            return {'RUNNING_MODAL'}
        
        # ------------------------------------------------------------------------------------------
        
        # NOTE: super!
        return super()._modal(context, event, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_clone'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        self._selection_type = 'INDICES_3D'
        
        # NOTE: brush specific props..
        
        self._sample_data = None
        self._sample_vs = None
        self._sample_ns = None
        
        self._modal_rotate_increment = 0.1
        self._modal_rotate_radians = 0.0
        self._modal_scale_increment = 0.1
        self._modal_scale_factor = 0.0
        self._brush_prev_location = None
        self._brush_prev_normal = None
        
        # self._clone_indices = None
        
        self._last_random_scale_factor = 0.0
        
        self._w_points = np.zeros((0, 3), dtype=float, )
        self._w_rotate_steps = 0
        
        # NOTE: get from session tool cache, if available
        self._load_sample_data_from_cache()


# ------------------------------------------------------------------ quasi create brushes <<<
# ------------------------------------------------------------------ destroy brushes >>>

# NOTTODO: erasers instead of dot have `X` in cursor widget? -->> would be mistaken for not-allowed-to-run thingy
# DONE: widgets: constant preview of selection under cursor? red dots? >>> but that would mean that select have to run constantly, not good for performance --> erased vertices draw as point until mouse is released
# FIXMENOT: multiple strokes result in multiple empty undo states, after they are undoed all at once. check dilute as well -->> it must have been something else.. now in new scene, fresh points, does not happen.
# DONE: 2d eraser mode, so we got covered points floating above surface
# DONE: draw erased points even when mouse is outside surface while lmb is pressed down
class SCATTER5_OT_manual_brush_tool_eraser(SCATTER5_OT_common_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_eraser"
    bl_label = "Eraser Brush"
    bl_description = "Eraser Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_eraser"
    tool_category = 'DESTROY'
    tool_label = "Eraser Brush"
    # mode will change this as needed
    tool_domain = '3D'
    # NOTE: tool have 3d and 2d modes, if definitions are changed here, change them also in `_setup_mode` method
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'mode',
            'datatype': 'enum',
            'change': 1,
            'change_pixels': 1,
            'change_wheel': 1,
            'text': '{}: {}',
            'name': 'Mode',
            'widget': 'ENUM_2D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_ERASER"
    dat_icon = "SCATTER5_ERASER"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            ls = []
            
            if(self._get_prop_value('mode') == '2D'):
                coord = (event.mouse_region_x, event.mouse_region_y, )
                
                radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
                ls.extend(radoff)
            else:
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
                
                radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
                ls.extend(radoff)
                
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            if(self._get_prop_value('mode') == '2D'):
                woc = self._theme._outline_color
                wfc = self._theme._fill_color
                
                radius = self._domain_aware_brush_radius()
                falloff = self._get_prop_value('falloff')
                
                coord = (event.mouse_region_x, event.mouse_region_y, )
                
                radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
                ls.extend(radoff)
            else:
                sign = self._widgets_fabricate_no_entry_sign(event, )
                ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            # NOTE: this is eraser, always use eraser color..
            woc = self._theme._outline_color_eraser
            wfc = self._theme._fill_color_eraser
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            ls = []
            
            if(self._get_prop_value('mode') == '2D'):
                coord = (event.mouse_region_x, event.mouse_region_y, )
                
                radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
                ls.extend(radoff)
            else:
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
                
                radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
                ls.extend(radoff)
                
                dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
                ls.extend(dot)
            
            if(len(self._w_points)):
                col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                ls.extend((
                    {
                        'function': 'round_points_px_3d',
                        'arguments': {
                            'vertices': self._w_points,
                            'matrix': Matrix(),
                            'color': col,
                            'size': self._theme._point_size,
                        }
                    },
                ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            woc = self._theme._outline_color_eraser
            wfc = self._theme._fill_color_eraser
            
            ls = []
            
            if(self._get_prop_value('mode') == '2D'):
                radius = self._domain_aware_brush_radius()
                if(self._get_prop_value('radius_pressure')):
                    radius = radius * self._pressure
                falloff = self._get_prop_value('falloff')
                
                coord = (event.mouse_region_x, event.mouse_region_y, )
                
                radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
                ls.extend(radoff)
            else:
                sign = self._widgets_fabricate_no_entry_sign(event, )
                ls.extend(sign)
            
            if(len(self._w_points)):
                col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                ls.extend((
                    {
                        'function': 'round_points_px_3d',
                        'arguments': {
                            'vertices': self._w_points,
                            'matrix': Matrix(),
                            'color': col,
                            'size': self._theme._point_size,
                        }
                    },
                ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _setup_mode(self, ):
        if(self._setup_last_used_mode == self._get_prop_value('mode')):
            return
        
        if(self._get_prop_value('mode') == '2D'):
            # NOTE: have to change it directly on class itself..
            # WATCH: i don't like it much, if this is going to be used more then once, make some better system for it
            from ..properties.manual_settings import SCATTER5_PR_manual_brush_tool_eraser
            SCATTER5_PR_manual_brush_tool_eraser._domain = '2D'
            
            self.tool_domain = '2D'
            self._selection_type = 'INDICES_2D'
            self.tool_gesture_definitions = {
                '__gesture_primary__': {
                    'property': 'radius_2d',
                    'datatype': 'float',
                    'change': 1,
                    'change_pixels': 1,
                    'change_wheel': 20,
                    'text': '{}: {:.0f}',
                    'name': 'Radius',
                    'widget': 'RADIUS_2D',
                },
                '__gesture_secondary__': {
                    'property': 'mode',
                    'datatype': 'enum',
                    'change': 1,
                    'change_pixels': 1,
                    'change_wheel': 1,
                    'text': '{}: {}',
                    'name': 'Mode',
                    'widget': 'ENUM_2D',
                },
                '__gesture_tertiary__': {
                    'property': 'falloff',
                    'datatype': 'float',
                    'change': 1 / 100,
                    'change_pixels': 1,
                    'change_wheel': 20,
                    'text': '{}: {:.3f}',
                    'name': 'Falloff',
                    'widget': 'STRENGTH_2D',
                },
                '__gesture_quaternary__': {
                    'property': 'affect',
                    'datatype': 'float',
                    'change': 1 / 100,
                    'change_pixels': 1,
                    'change_wheel': 20,
                    'text': '{}: {:.3f}',
                    'name': 'Probability',
                    'widget': 'STRENGTH_2D',
                },
            }
            self.tool_gesture_space = '2D'
        else:
            # NOTE: have to change it directly on class itself..
            # WATCH: i don't like it much, if this is going to be used more then once, make some better system for it
            from ..properties.manual_settings import SCATTER5_PR_manual_brush_tool_eraser
            SCATTER5_PR_manual_brush_tool_eraser._domain = '3D'
            
            self.tool_domain = '3D'
            self._selection_type = 'INDICES_3D'
            self.tool_gesture_definitions = {
                '__gesture_primary__': {
                    'property': 'radius',
                    'datatype': 'float',
                    'change': 1 / 100,
                    'change_pixels': 1,
                    'change_wheel': 20,
                    'text': '{}: {:.3f}',
                    'name': 'Radius',
                    'widget': 'RADIUS_3D',
                },
                '__gesture_secondary__': {
                    'property': 'mode',
                    'datatype': 'enum',
                    'change': 1,
                    'change_pixels': 1,
                    'change_wheel': 1,
                    'text': '{}: {}',
                    'name': 'Mode',
                    'widget': 'ENUM_3D',
                },
                '__gesture_tertiary__': {
                    'property': 'falloff',
                    'datatype': 'float',
                    'change': 1 / 100,
                    'change_pixels': 1,
                    'change_wheel': 20,
                    'text': '{}: {:.3f}',
                    'name': 'Falloff',
                    'widget': 'STRENGTH_3D',
                },
                '__gesture_quaternary__': {
                    'property': 'affect',
                    'datatype': 'float',
                    'change': 1 / 100,
                    'change_pixels': 1,
                    'change_wheel': 20,
                    'text': '{}: {:.3f}',
                    'name': 'Probability',
                    'widget': 'STRENGTH_3D',
                },
            }
            self.tool_gesture_space = '3D'
        
        self._configurator = ToolKeyConfigurator(self)
        
        self._setup_last_used_mode = self._get_prop_value('mode')
    
    @verbose
    def _action_begin(self, ):
        if(self._get_prop_value('mode') == '2D'):
            self._execute()
        else:
            loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
            if(loc is not None):
                self._execute()
    
    def _action_update(self, ):
        if(self._get_prop_value('mode') == '2D'):
            self._execute()
        else:
            loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
            if(loc is not None):
                self._execute()
    
    @verbose
    def _action_finish(self, ):
        super()._action_finish()
        
        self._w_points = np.zeros((0, 3), dtype=float, )
    
    def _execute(self, ):
        if(self._get_prop_value('mode') == '2D'):
            pass
        else:
            loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
            if(loc is None):
                return
        
        self._select()
        
        indices = self._selection_indices
        if(not len(indices)):
            return
        
        self._ensure_attributes()
        
        # NOTE: flip the switch if brush uses foreach_set only, foreach_set does not force blender to update data
        self._force_update = False
        self._modify()
        if(self._force_update):
            self._target.data.update()
    
    @verbose
    def _modify(self, ):
        mask = self._selection_mask
        me = self._target.data
        
        self._w_points = np.concatenate([self._w_points, self._selection_vs_original_world[self._selection_mask]])
        
        indices = self._get_masked_index_to_target_vertex_index(self._selection_indices)
        l = len(me.vertices)
        mask = np.zeros(l, dtype=bool, )
        mask[indices] = True
        
        bm = bmesh.new()
        bm.from_mesh(me)
        rm = []
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            if(mask[i]):
                rm.append(v)
        for v in rm:
            bm.verts.remove(v)
        bm.to_mesh(me)
        bm.free()
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._action_timer_interval = self._get_prop_value('interval')
        self._action_execute_on = self._get_prop_value('draw_on')
        
        self._setup_mode()
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_eraser'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._setup_last_used_mode = None
        self._setup_mode()
        
        # NOTE: brush specific props..
        
        self._w_points = np.zeros((0, 3), dtype=float, )


# DONE: try to fix weird bigger gaps between instances that are sometimes happening (i notice it mostly at starting position), no idea what is causing it..
# DONE: widgets: constant preview of selection under cursor? red dots? maybe too cpu intensive, there will a lot of distance comparisons.. --> erased vertices draw as point until mouse is released
class SCATTER5_OT_manual_brush_tool_dilute(SCATTER5_OT_common_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_dilute"
    bl_label = "Dilute Brush"
    bl_description = "Dilute Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_dilute"
    tool_category = 'DESTROY'
    tool_label = "Dilute Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'minimal_distance',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Minimal Distance',
            'widget': 'LENGTH_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "MATFLUID"
    dat_icon = "SCATTER5_DILLUTE"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            mind = self._get_prop_value('minimal_distance')
            ms = self._widgets_compute_surface_matrix_scale_component_3d(mind, )
            mindm = mt @ mr @ ms
            ls.extend((
                # minimal distance circle
                {
                    'function': 'circle_outline_3d',
                    'arguments': {
                        'matrix': mindm,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
            ))
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            # NOTE: this is eraser, always use eraser color..
            woc = self._theme._outline_color_eraser
            wfc = self._theme._fill_color_eraser
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            mind = self._get_prop_value('minimal_distance')
            ms = self._widgets_compute_surface_matrix_scale_component_3d(mind, )
            mindm = mt @ mr @ ms
            ls.extend((
                # minimal distance circle
                {
                    'function': 'circle_outline_3d',
                    'arguments': {
                        'matrix': mindm,
                        'steps': self._theme._circle_steps,
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
            ))
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            if(len(self._w_points)):
                col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                ls.extend((
                    {
                        'function': 'round_points_px_3d',
                        'arguments': {
                            'vertices': self._w_points,
                            'matrix': Matrix(),
                            'color': col,
                            'size': self._theme._point_size,
                        }
                    },
                ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            woc = self._theme._outline_color_eraser
            wfc = self._theme._fill_color_eraser
            
            if(len(self._w_points)):
                col = woc[:3] + (self._theme._outline_color_helper_alpha, )
                ls.extend((
                    {
                        'function': 'round_points_px_3d',
                        'arguments': {
                            'vertices': self._w_points,
                            'matrix': Matrix(),
                            'color': col,
                            'size': self._theme._point_size,
                        }
                    },
                ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    @verbose
    def _action_finish(self, ):
        super()._action_finish()
        
        self._w_points = np.zeros((0, 3), dtype=float, )
    
    def _dilute_action(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        
        me = self._target.data
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        
        if(not len(vs)):
            return
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        selection = self._selection_indices
        if(selection is None):
            return
        if(not len(selection)):
            return
        
        fvs, fds, fii = self._distance_range(vs[selection], loc, radius, )
        asort = np.argsort(fds)
        selection_sorted = selection[asort]
        
        m = np.zeros(l, dtype=bool, )
        m[selection_sorted] = True
        indices = np.arange(l, dtype=int, )
        remove = np.zeros(l, dtype=bool, )
        leave = np.zeros(l, dtype=bool, )
        
        for i, si in enumerate(selection_sorted):
            if(remove[si]):
                continue
            leave[si] = True
            fvs, fds, fii = self._distance_range(vs[m], vs[si], self._get_prop_value('minimal_distance'), )
            ii = indices[m]
            remove[ii[fii]] = True
        
        remove = self._get_masked_index_to_target_vertex_index(remove)
        leave = self._get_masked_index_to_target_vertex_index(leave)
        l = len(me.vertices)
        
        mask = np.zeros(l, dtype=bool, )
        mask[remove] = True
        mask[leave] = False
        
        # ------------------------------------------------------
        
        mm = self._get_target_vertex_index_to_masked_index(np.arange(l, dtype=int, )[mask], )
        self._w_points = np.concatenate([self._w_points, self._selection_vs_original_world[mm]])
        
        bm = bmesh.new()
        bm.from_mesh(me)
        rm = []
        bm.verts.ensure_lookup_table()
        for i, v in enumerate(bm.verts):
            if(mask[i]):
                rm.append(v)
        for v in rm:
            bm.verts.remove(v)
        bm.to_mesh(me)
        bm.free()
    
    def _modify(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            return
        
        self._dilute_action()
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_dilute'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        self._selection_type = 'INDICES_3D'
        
        # NOTE: brush specific props..
        
        self._w_points = np.zeros((0, 3), dtype=float, )


# ------------------------------------------------------------------ destroy brushes <<<
# ------------------------------------------------------------------ modify brushes >>>


# DONE: check what happens with 0, 1, 2 vertices, there is no area, no convex hull. it should fail elegantly, tooltip like message? i don't like `operator.report` much, i often miss it down at status bar..
# WATCH: rarely there is mismatch between vetex lengths in delaunay mesh input and output. i THINK it is this. i am not SURE. it happened ONCE with ONE scene. got the blend saved for debugging. it is repeatable. either try to recover from this, or warn user that delunay mesh can't be constructed and refuse to work.. `delaunay_2d_cdt` is black box and it warns that result may differ. that is why i have `_split_impulse` there. maybe that epsilon distance is not enough? test that first. -->> `convex_hull_2d` in some cases returns one index twice, this lead to edge from and to the same vertex, it is later removed by `delaunay_2d_cdt` and lead to index errors later..
# NOTTODO: check startup performance -->> is ok, it runs just once.. it is slow mainly because of `_split_impulse`, but i really need that, or i run into errors..
# NOTTODO: look if `_split_impulse` can be optimized, every tiny bit counts in this case
# NOTTODO: cursor widget is weird. try world z aligned cylinder or something so it is similar to spray cursor widget -> it is even weirder
# DONE: make special gestures just for 2.5D tools, having simple unrotated cursor and surface rotated gesture widgets is weird
# DONE: change it to use `SCATTER5_OT_modify_mixin._select()` and not only simple distance comparison..
# DONE: still not very happy with widgets, it's just ok, but fact is, it need to show it is 2.5D only somehow
# DONE: update surface normal on new position
# DONE: check what happens with smooth active and with data, then use op to clear points, then try to draw.. will fail i think
class SCATTER5_OT_manual_brush_tool_smooth(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_smooth"
    bl_label = "Relax Brush"
    bl_description = "Relax Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_smooth"
    tool_category = 'TRANSLATE'
    tool_label = "Relax Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_2_5D',
        },
        '__gesture_secondary__': {
            'property': 'strength',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Strength',
            'widget': 'STRENGTH_2_5D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_2_5D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_2_5D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_CLICK"
    dat_icon = "SCATTER5_RELAX"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    _debug_smooth_mesh = False
    _debug_smooth_mesh_keep_on_exit = False
    
    _message_mesh_requirements = "Three or more vertices required"
    _message_delaunay_failed = "Delaunay triangulation failed (see console for error message)"
    _delaunay_failed = False
    
    def _split_impulse(self, vs, epsilon=0.001, ):
        # find groups of points with distance between them less than epsilon, practically groups of points on the same spot
        indices = np.arange(len(vs), dtype=int, )
        groups = []
        for i, v in enumerate(vs):
            # calculate distance from all verts, including the one i am testing, so it have always one match, will sort it out in next lines
            d = ((vs[:, 0] - v[0]) ** 2 + (vs[:, 1] - v[1]) ** 2) ** 0.5
            m = d < epsilon
            if(np.sum(m) > 1):
                # more than one point in epsilon distance, i got a group
                g = indices[m]
                groups.append(g.tolist())
        
        # remove duplicates so i am left with unique groups
        groups.sort()
        import itertools
        groups = list(i for i, _ in itertools.groupby(groups))
        
        for g in groups:
            l = len(g)
            ii = np.array(g, dtype=int, )
            
            # make direction normals from circle split to len(group) pieces
            c = np.zeros((l, 2), dtype=float, )
            angstep = 2 * np.pi / l
            a = np.arange(l, dtype=int, )
            c[:, 0] = 0.0 + (np.sin(a * angstep) * 1.0)
            c[:, 1] = 0.0 + (np.cos(a * angstep) * 1.0)
            
            # shift group verts by epsilon in direction of circular normals
            a = vs[ii]
            a = a + (c * epsilon)
            vs[ii] = a
        
        return vs
    
    def _prepare_smooth_mesh(self, ):
        me = bpy.data.meshes.get(self._smooth_me_name)
        if(me is None):
            me = bpy.data.meshes.new(name=self._smooth_me_name, )
        self._smooth_me = me
        
        me = self._target.data
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        
        vs2d = vs[:, 0:2]
        
        vs2d = self._split_impulse(vs2d, 0.001, )
        
        h = mathutils.geometry.convex_hull_2d(vs2d)
        
        # WATCH: don't know if this is best solution, but that is what i get using black box dunctions from api, functions that are allowed to arbitrarily modify input data
        # NOTE: this will search for identical index returned from `convex_hull_2d` which will later result in edge from and to same vertex, while `delaunay_2d_cdt` will be able to create mesh, i will then have indexing off by 1..
        # HACK: maybe it is..
        h = np.array(h)
        i = np.arange(len(h), dtype=int, )
        es = np.c_[h[i], np.roll(h[i], -1), ]
        emin = np.min(es, axis=1)
        emax = np.max(es, axis=1)
        m = (emin == emax)
        es = es[~m]
        h = es[:, 0]
        # HACK: maybe it isn't..
        
        hvs = vs2d[h]
        bvs = np.c_[hvs[:, 0], hvs[:, 1], np.zeros(len(hvs), dtype=hvs.dtype, )]
        center = np.array([
            np.min(hvs[:, 0]) + ((np.max(hvs[:, 0]) - np.min(hvs[:, 0])) / 2),
            np.min(hvs[:, 1]) + ((np.max(hvs[:, 1]) - np.min(hvs[:, 1])) / 2),
            0.0,
        ], dtype=float, )
        bvs = bvs - center
        
        # TODO: is there some way to have this adjusted to overall dimensions? or average distance between points? or something else?
        border_scale_factor = 1.2
        
        m = np.array(Matrix.Scale(border_scale_factor, 4))
        bvs = np.c_[bvs[:, 0], bvs[:, 1], bvs[:, 2], np.ones(len(bvs), dtype=bvs.dtype, )]
        bvs = np.dot(m, bvs.T)[0:4].T.reshape((-1, 4))
        bvs = bvs[:, :3] + center
        
        mask = np.zeros(len(bvs) + len(vs2d), dtype=bool, )
        mask[np.arange(len(bvs))] = True
        self._smooth_mask = mask
        
        avs2d = np.concatenate([bvs[:, :2], vs2d])
        i = np.arange(len(bvs))
        es = np.c_[i, np.roll(i, -1), ]
        
        # vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(avs2d, es, [], 0, self.smooth_epsilon, True)
        # NOTE: use epsilon 0.0 so my epsilon for split impulse is greater..
        # vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(avs2d, es, [], 0, 0.0, True)
        # NOTE: docs says, epsilon should not be zero, so lets go with 0.00001..
        vert_coords, edges, faces, _, _, _ = mathutils.geometry.delaunay_2d_cdt(avs2d, es, [], 0, 0.00001, True)
        vs = np.array(vert_coords)
        vs = np.c_[vs[:, 0], vs[:, 1], np.zeros(len(vs), dtype=vs.dtype, )]
        
        self._smooth_me.from_pydata(vs.tolist(), [], faces)
        self._smooth_me.validate()
        self._smooth_me.update()
        
        self._smooth_me.vertices.foreach_set('select', np.zeros(len(self._smooth_me.vertices), dtype=bool, ))
        self._smooth_me.edges.foreach_set('select', np.zeros(len(self._smooth_me.edges), dtype=bool, ))
        self._smooth_me.polygons.foreach_set('select', np.zeros(len(self._smooth_me.polygons), dtype=bool, ))
        
        if(self._debug_smooth_mesh):
            o = bpy.data.objects.new(self._smooth_me_name, self._smooth_me, )
            bpy.context.view_layer.active_layer_collection.collection.objects.link(o)
            o.display_type = 'WIRE'
            o.show_all_edges = True
            o.show_in_front = True
        
        return self._smooth_me
    
    def _modify(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            return
        
        if(np.sum(self._get_target_active_mask()) < 3):
            return
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        me = bpy.data.meshes.get(self._smooth_me_name)
        
        # NOTE: i think this is never called because mesh is created at startup. why it is here?
        # NOTE: i will wrap it the same as in in `_invoke`.. and leave here.. we'll see..
        if(not me):
            try:
                me = self._prepare_smooth_mesh()
            except Exception as e:
                self._delaunay_failed = True
                traceback.print_exc()
        
        mask = self._smooth_mask
        
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        
        loc2d = Vector((loc.x, loc.y, 0.0))
        
        l = len(me.vertices)
        vs = np.zeros(l * 3, dtype=float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        
        vs = [bm.verts[i] for i in self._selection_indices if not bm.verts[i].is_boundary]
        for v in vs:
            v.select_set(True)
        
        factor = self._get_prop_value('strength')
        if(self._get_prop_value('strength_pressure')):
            factor = factor * self._pressure
        
        bmesh.ops.smooth_vert(bm, verts=vs, factor=factor, use_axis_x=True, use_axis_y=True, use_axis_z=False, )
        
        bm.to_mesh(me)
        bm.free()
        
        vs = np.zeros(l * 3, dtype=float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        m = np.zeros(len(vs), dtype=bool, )
        m[self._selection_indices] = True
        # WATCH: --------------------------------------------------------- here..
        m[mask] = False
        chvs = vs[m]
        chii = np.arange(len(vs))[m]
        chii = chii - np.sum(mask)
        
        me = self._target.data
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        l = len(vs)
        ns = self._get_target_attribute_masked(me.attributes, 'normal', )
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        vs, ns = self._surfaces_to_world_space(vs, ns, uids, )
        
        vs[chii, 0] = chvs[:, 0]
        vs[chii, 1] = chvs[:, 1]
        
        # # DEBUG
        # debug.points(self._target, vs[chii], )
        # # DEBUG
        
        for i in chii:
            v = Vector(vs[i])
            
            l, n, ii, d = self._bvh.ray_cast(v, Vector((0.0, 0.0, -1.0)))
            if(not l):
                l, n, ii, d = self._bvh.ray_cast(v, Vector((0.0, 0.0, 1.0)))
                if(not l):
                    l, n, ii, d = self._bvh.find_nearest(v)
            
            # NOTE: interpolate normal first, while i have location in world coordinates
            if(self._get_prop_value('use_align_z_to_surface')):
                nn = self._interpolate_smooth_face_normal(l, n, ii, )
                ns[i] = nn.to_tuple()
            
            vs[i] = l.to_tuple()
        
        # # DEBUG
        # debug.points(self._target, vs[chii], )
        # debug.points(self._target, vs, )
        # # DEBUG
        
        # pass all verts
        self._w_selected_vertices = np.c_[vs[:, 0], vs[:, 1], np.full(len(vs), self._mouse_3d_loc.z, dtype=vs.dtype, )]
        # but select only edges of affected vertices
        _w_me = bpy.data.meshes.get(self._smooth_me_name)
        _w_es = np.zeros((len(_w_me.edges) * 2), dtype=int, )
        _w_me.edges.foreach_get('vertices', _w_es)
        _w_es.shape = (-1, 2)
        _offset = np.sum(self._smooth_mask)
        _w_es = _w_es - _offset
        _w_es = _w_es[(_w_es[:, 0] >= 0) & (_w_es[:, 1] >= 0)]
        m = np.all(np.isin(_w_es, chii, assume_unique=False, invert=False, ), axis=1, )
        _w_es = _w_es[m]
        self._w_selected_edges = _w_es.copy()
        
        vs, ns = self._world_to_surfaces_space(vs, ns, uids, )
        
        self._set_target_attribute_masked(me.vertices, 'co', vs, )
        
        if(self._get_prop_value('use_align_z_to_surface')):
            # # DEBUG
            # debug.points(self._surface, vs, ns)
            # # DEBUG
            
            self._set_target_attribute_masked(me.attributes, 'normal', ns, )
            iii = self._get_target_vertex_index_to_masked_index(chii, )
            self._regenerate_rotation_from_attributes(iii, )
        
        # WATCH: do i update mesh twice? once in regenerate and once here?
        self._target.data.update()
    
    # DONE: unless i use `_select` from modify mixin, this will not work.
    def _execute(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            return
        
        if(len(self._target.data.vertices) < 3):
            # self.report({'ERROR'}, self._message_mesh_requirements, )
            # self.report({'WARNING'}, self._message_mesh_requirements, )
            return
        
        self._select()
        
        indices = self._selection_indices
        if(not len(indices)):
            # clear this here, because `_modify` will not run
            self._w_selected_vertices = []
            self._w_selected_edges = []
            return
        
        self._ensure_attributes()
        
        # NOTE: flip the switch if brush uses foreach_set only, foreach_set does not force blender to update data
        self._force_update = False
        self._modify()
        if(self._force_update):
            self._target.data.update()
    
    # NOTE: to be used by menu operator
    def _execute_all(self, ):
        if(len(self._target.data.vertices) < 3):
            self.report({'WARNING'}, self._message_mesh_requirements, )
            return
        
        self._select_all()
        
        indices = self._selection_indices
        if(not len(indices)):
            return
        
        self._ensure_attributes()
        
        # NOTE: trick `_modify` check
        if(self._mouse_3d_loc is None):
            l, n = None, None
        else:
            l, n = self._mouse_3d_loc.copy(), self._mouse_3d_nor.copy()
        self._mouse_3d_loc = Vector()
        self._mouse_3d_nor = Vector((0.0, 0.0, 1.0))
        
        self._modify()
        
        # NOTE: restore
        self._mouse_3d_loc, self._mouse_3d_nor = l, n
        
        self._target.data.update()
    
    # NOTE: override, i use different mesh for vertices and 2d location
    def _select_indices_3d(self, ):
        # me = self._target.data
        me = bpy.data.meshes.get(self._smooth_me_name)
        l = len(me.vertices)
        
        # # NOTE: fabricate default value with nothing selected
        self._select_none()
        
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is None):
            # NOTE: i am not above surface
            return
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        vs = np.zeros(l * 3, dtype=float, )
        me.vertices.foreach_get('co', vs)
        vs.shape = (-1, 3)
        if(not len(vs)):
            # NOTE: i have no data
            return
        
        vs_orig = vs.copy()
        
        # i have all in world coords, so i just send mouse 3d location to ground plane..
        loc = Vector((loc.x, loc.y, 0.0))
        
        vs_orig_world = vs.copy()
        
        falloff = radius * self._get_prop_value('falloff')
        affect = self._get_prop_value('affect')
        if(self._get_prop_value('affect_pressure')):
            affect = self._pressure
        
        _, distances, indices = self._distance_range(vs, loc, radius, )
        if(not len(indices)):
            # NOTE: all vertices are too far away
            return
        
        mask = np.zeros(l, dtype=bool, )
        
        center = indices[distances <= falloff]
        annulus = indices[(distances > falloff) & (distances <= radius)]
        ad = distances[(distances > falloff) & (distances <= radius)] - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        # choose weighted random from annulus
        s = int(len(annulus) * affect)
        if(s == 0 and len(annulus) > 0):
            s = 1
        if(s > 0):
            ws = nd / np.sum(nd)
            choice = np.random.choice(annulus, size=s, replace=False, p=ws, )
            mask[choice] = True
        
        if(self._get_prop_value('falloff') < 1.0):
            # choose weighted random from border between circle ans annulus so there is no visible circle in result
            b = 0.2
            f2 = falloff * (1.0 - b)
            r2 = falloff * (1.0 + b)
            a = 0.75
            a2 = a + (1.0 - a) * affect
            center2 = indices[distances <= f2]
            transition = indices[(distances > f2) & (distances <= r2)]
            
            s = int(len(transition) * a2)
            if(s == 0 and len(transition) > 0):
                s = 1
            if(s > 0):
                ad = distances[(distances > f2) & (distances <= r2)] - f2
                nd = 1.0 - ((ad - 0.0) / ((r2 - f2) - 0.0))
                ws = nd / np.sum(nd)
                choice = np.random.choice(transition, size=s, replace=False, p=ws, )
                mask[choice] = True
                mask[center2] = True
            else:
                mask[center2] = True
        else:
            mask[center] = True
        
        self._selection_mask = mask
        self._selection_indices = np.arange(l, dtype=int, )[mask]
        
        # # DEBUG
        # _vs, _ = self._surface_to_global_space(vs.copy(), None, )
        # debug.points(self._target, _vs[mask], None, None, )
        # return
        # # DEBUG
        
        ds = np.zeros(l, dtype=float, )
        ds[indices] = distances
        ds = ds[mask]
        self._selection_distances = ds
        self._selection_distances_normalized = (ds - 0.0) / (radius - 0.0)
        
        # # DEBUG
        # vs, _ = self._surface_to_global_space(vs.copy(), None, )
        # vs = vs[self._selection_indices]
        # l = len(vs)
        # ns = np.zeros((l, 3), dtype=float, )
        # z = np.zeros(l, dtype=float, )
        # cs = np.c_[self._selection_distances_normalized, z, z, np.ones(l, dtype=float, )]
        # debug.points(self._target, vs, ns, cs, )
        # # DEBUG
        
        ws = np.zeros(l, dtype=float, )
        ad = self._selection_distances - falloff
        
        # DONE: RuntimeWarning: divide by zero encountered in true_divide
        if(radius == falloff):
            nd = np.ones(len(ad), dtype=float, )
        else:
            nd = 1.0 - ((ad - 0.0) / ((radius - falloff) - 0.0))
        
        ws[self._selection_indices] = nd
        ws[center] = 1.0
        self._selection_weights = ws[self._selection_mask]
        
        # NOTE: untransformed vertices
        self._selection_vs_original = vs_orig
        
        # NOTE: untransformed vertices in world coords
        self._selection_vs_original_world = vs_orig_world
        
        # # # DEBUG
        # # # vs, _ = self._surface_to_global_space(vs.copy(), None, )
        # vs = vs[self._selection_indices]
        # l = len(self._selection_weights)
        # ns = np.zeros((l, 3), dtype=float, )
        # z = np.zeros(l, dtype=float, )
        # cs = np.c_[self._selection_weights, z, z, np.ones(l, dtype=float, )]
        # debug.points(self._target, vs, ns, cs, )
        # # # DEBUG
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, _, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            mr = Matrix()
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            if(self._delaunay_failed):
                tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_delaunay_failed, )
                ls.extend(tooltip)
            elif(len(self._target.data.vertices) < 3):
                tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_mesh_requirements, )
                ls.extend(tooltip)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, _, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            mr = Matrix()
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            vs = self._w_selected_vertices
            es = self._w_selected_edges
            if(len(vs) and len(es)):
                woc = self._theme._outline_color_helper_hint
                wfc = self._theme._fill_color_helper_hint
                ls.extend((
                    # connections
                    {
                        'function': 'multiple_thick_lines_3d',
                        'arguments': {
                            'vertices': vs,
                            'indices': es,
                            'matrix': Matrix(),
                            'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                            'thickness': self._theme._outline_thickness_helper,
                        }
                    },
                ))
            
            if(self._delaunay_failed):
                tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_delaunay_failed, )
                ls.extend(tooltip)
            elif(len(self._target.data.vertices) < 3):
                tooltip = self._widgets_fabricate_tooltip((event.mouse_region_x, event.mouse_region_y, ), self._message_mesh_requirements, )
                ls.extend(tooltip)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_smooth'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'INDICES_3D'
        
        self._widgets_use_timer_events = True
        
        # NOTE: brush specific props..
        
        self._smooth_me_name = 'tmp-{}'.format(uuid.uuid1())
        if(len(self._target.data.vertices) >= 3):
            try:
                self._prepare_smooth_mesh()
            except Exception as e:
                self._delaunay_failed = True
                traceback.print_exc()
        
        self._w_selected_vertices = []
        self._w_selected_edges = []
    
    def _cleanup(self, context, event, ):
        if(self._debug_smooth_mesh_keep_on_exit):
            super()._cleanup(context, event, )
            return
        
        if(self._debug_smooth_mesh):
            o = bpy.data.objects.get(self._smooth_me_name)
            if(o is not None):
                try:
                    bpy.data.objects.remove(o, do_unlink=True, )
                except Exception as e:
                    traceback.print_exc()
        
        me = bpy.data.meshes.get(self._smooth_me_name)
        if(me is not None):
            try:
                bpy.data.meshes.remove(me)
            except Exception as e:
                traceback.print_exc()
        
        super()._cleanup(context, event, )


# DONE: proportional mode, should be easy if i port `_select_2d` result `_distances_normalized` to `_select` itself.. well, i hope so..
# NOTTODO: draw rotation as triangle on radius edge instead of middle line? don't like it..
class SCATTER5_OT_manual_brush_tool_move(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_move"
    bl_label = "Move Brush"
    bl_description = "Move Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_move"
    tool_category = 'TRANSLATE'
    tool_label = "Move Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'proportional_mode',
            'datatype': 'bool',
            'change': 1,
            'change_pixels': 1,
            'change_wheel': 1,
            'text': '{}: {}',
            'name': 'Proportional',
            'widget': 'BOOLEAN_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Rotate: LMB+Mouse Wheel",
        "• Scale: LMB+CTRL+Mouse Wheel",
    )
    
    icon = "W_MOVE"
    dat_icon = "SCATTER5_MOVE"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    def _action_pickup(self, ):
        me = self._target.data
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        ns = self._get_target_attribute_masked(me.attributes, 'normal', )
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        l = len(vs)
        
        vs, ns = self._surfaces_to_world_space(vs, ns, uids, )
        
        # # DEBUG
        # debug.points(self._target, vs, ns, )
        # # DEBUG
        
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        
        indices = self._selection_indices
        sel_vs = vs[indices]
        sel_ns = ns[indices]
        
        self._vs_original = vs.copy()[indices]
        
        self._brush_prev_location = loc
        self._brush_prev_normal = nor
        
        self._brush_initial_location = loc.copy()
        self._brush_initial_normal = nor.copy()
        
        brush_radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            brush_radius = brush_radius * self._pressure
        
        # NOTE: pick points just above brush radius, is that good for something?
        epsilon = 0.001
        plane_loc = self._brush_prev_location + (self._brush_prev_normal.normalized() * (brush_radius + epsilon))
        plane_nor = self._brush_prev_normal.normalized()
        
        picked_vs = sel_vs.copy()
        picked_ns = sel_ns.copy()
        for i, co in enumerate(picked_vs):
            d = mathutils.geometry.distance_point_to_plane(co, plane_loc, plane_nor)
            picked_vs[i] = co + (plane_nor * (-d))
        
        self._vs = picked_vs.copy()
        self._vs = self._vs - np.array(plane_loc)
        self._ns = picked_ns.copy()
        
        # # # DEBUG
        # debug.points(self._target, self._vs, self._ns, )
        # # # DEBUG
    
    def _action_move(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        brush_loc = loc
        brush_nor = nor
        
        r = self._rotation_to(self._brush_prev_normal, brush_nor)
        if(self._get_prop_value('use_align_z_to_surface')):
            self._vs, self._ns = self._apply_matrix(r.to_matrix().to_4x4(), self._vs, self._ns, )
        else:
            self._vs, _ = self._apply_matrix(r.to_matrix().to_4x4(), self._vs, None, )
        self._brush_prev_normal = brush_nor
        
        if(self._modal_rotate_radians != 0.0):
            q = Quaternion(brush_nor, self._modal_rotate_radians)
            if(self._get_prop_value('use_align_z_to_surface')):
                self._vs, self._ns = self._apply_matrix(q.to_matrix().to_4x4(), self._vs, self._ns, )
            else:
                self._vs, _ = self._apply_matrix(q.to_matrix().to_4x4(), self._vs, None, )
            self._modal_rotate_radians = 0.0
        
        if(self._modal_scale_factor != 0.0):
            self._vs, _ = self._apply_matrix(Matrix.Scale(1.0 + self._modal_scale_factor, 4, ), self._vs, None, )
            self._modal_scale_factor = 0.0
        
        # # # DEBUG
        # debug.points(self._target, self._vs, self._ns, )
        # # # DEBUG
    
    def _store(self, ):
        self._ensure_attributes()
        
        me = self._target.data
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        
        if(self._get_prop_value('proportional_mode')):
            weights = self._selection_weights
            il = self._brush_initial_location
            d = Vector(il - loc)
            ds = np.full((len(self._vs), 3), d, dtype=float, )
            wds = ds * (1.0 - weights.reshape((-1, 1, )))
            vs = self._vs + wds
            vs += np.array(loc, dtype=float, )
        else:
            vs = self._vs + np.array(loc, dtype=float, )
        
        # # DEBUG
        # debug.points(self._target, vs, )
        # return
        # # DEBUG
        
        bnor = np.array(nor)
        for i, v in enumerate(vs):
            if(self._get_prop_value('proportional_mode')):
                w = self._selection_weights[i]
                ni = self._brush_initial_normal
                nn = ni.lerp(nor, w)
                bnor = np.array(nn)
            
            l, n, ii, d = self._bvh.ray_cast(v, bnor)
            l2, n2, ii2, d2 = self._bvh.ray_cast(v, bnor * -1.0)
            if(l is not None and l2 is not None):
                if(d > d2):
                    vv = l2
                else:
                    vv = l
            elif(l is not None and l2 is None):
                vv = l
            elif(l is None and l2 is not None):
                vv = l2
            else:
                # i did not hit anything.. try to recover from it..
                l3, n3, ii3, d3 = self._bvh.find_nearest(v, )
                vv = l3
            
            if(self._get_prop_value('proportional_mode')):
                w = self._selection_weights[i]
                v = Vector(self._vs_original[i])
                vv = vv.lerp(v, 1.0 - w)
                vs[i] = vv
            else:
                vs[i] = vv
        
        # # DEBUG
        # debug.points(self._target, vs, )
        # return
        # # DEBUG
        
        indices = self._selection_indices
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        for i, ii in enumerate(indices):
            # snap to surface even more...
            # NOTTODO: to much snapping to surface.. shouldn't it be all on one spot? -> i need final surface normal for surface align anyway..
            v = Vector(vs[i])
            loc, nor, idx, dst = self._bvh.find_nearest(v, )
            # iterpolate normal if on smooth surface
            nor = self._interpolate_smooth_face_normal(loc, nor, idx, )
            mii = self._get_masked_index_to_target_vertex_index(ii, )
            
            if(self._get_prop_value('update_uuid')):
                nuid = int(ToolSessionCache._cache['arrays']['f_surface'][idx])
                if(nuid != uids[ii]):
                    me.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[mii].value = nuid
            
            loc, nor = self._world_to_surfaces_space(loc, nor, uids[ii], )
            me.vertices[mii].co = loc
            
            if(self._get_prop_value('use_align_z_to_surface')):
                old_normal = Vector(me.attributes['{}normal'.format(self.attribute_prefix)].data[mii].vector)
                
                me.attributes['{}normal'.format(self.attribute_prefix)].data[mii].vector = nor
                
                q = self._rotation_to(old_normal, nor, )
                if(me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[mii].value == 3):
                    a = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[mii].vector)
                    a.rotate(q)
                    me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[mii].vector = a
                if(me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[mii].value == 2):
                    a = Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[mii].vector)
                    a.rotate(q)
                    me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[mii].vector = a
        
        if(self._get_prop_value('use_align_z_to_surface')):
            indices = self._get_target_vertex_index_to_masked_index(indices, )
            self._regenerate_rotation_from_attributes(indices, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            if(self._modal_rotate_radians_widgets != 0.0 or self._modal_scale_factor_widgets != 1.0):
                r = radius * self._modal_scale_factor_widgets
                ms = Matrix(((r, 0.0, 0.0, 0.0), (0.0, r, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
                mmsf = mt @ mr @ ms
                
                q = Quaternion(nor, self._modal_rotate_radians_widgets)
                mrrr = mt @ (q.to_matrix().to_4x4() @ mr) @ ms
                
                if(self._modal_rotate_radians_widgets != 0.0):
                    ls.extend((
                        # rotation line
                        {
                            'function': 'thick_line_3d',
                            'arguments': {
                                'a': (-1.0, 0.0, 0.0, ),
                                'b': (1.0, 0.0, 0.0, ),
                                'matrix': mrrr,
                                'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                                'thickness': self._theme._outline_thickness_helper,
                            }
                        },
                    ))
                if(self._modal_scale_factor_widgets != 1.0):
                    ls.extend((
                        # scale circle
                        {
                            'function': 'circle_outline_3d',
                            'arguments': {
                                'matrix': mmsf,
                                'steps': self._theme._circle_steps,
                                'color': woc[:3] + (self._theme._outline_color_helper_alpha, ),
                                'thickness': self._theme._outline_thickness_helper,
                            }
                        },
                    ))
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    @verbose
    def _action_begin(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            self._select()
            if(len(self._selection_indices)):
                self._action_pickup()
    
    def _action_update(self, ):
        # NOTE: here is the right spot to do actual brush work
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            if(len(self._selection_indices)):
                self._action_move()
                self._store()
    
    @verbose
    def _action_finish(self, ):
        # NOTE: here is the right spot to do actual brush work
        self._modal_rotate_radians_widgets = 0.0
        self._modal_scale_factor_widgets = 1.0
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
        
        self._action_timer_interval = self._get_prop_value('interval')
        self._action_execute_on = self._get_prop_value('draw_on')
        
        if(self._get_prop_value('proportional_mode')):
            self._selection_type = 'WEIGHTS_3D'
        else:
            self._selection_type = 'INDICES_3D'
    
    def _modal(self, context, event, ):
        # if i need something to be constantly refreshed.. not widgets..
        self._on_any_modal_event(context, event, )
        
        # update..
        self._context_region = context.region
        self._context_region_data = context.region_data
        # update settings..
        self._update_references_and_settings(context, event, )
        
        # ------------------------------------------------------------------------------------------
        # NOTE: inject into `_modal` and repeat all steps until gestures, this should ensure all is set for action
        
        if(event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', }):
            if(self._lmb):
                if(event.ctrl):
                    if(event.type == 'WHEELUPMOUSE'):
                        self._modal_scale_factor += self._modal_scale_increment
                        self._modal_scale_factor_widgets *= 1.0 + self._modal_scale_increment
                    if(event.type == 'WHEELDOWNMOUSE'):
                        self._modal_scale_factor -= self._modal_scale_increment
                        self._modal_scale_factor_widgets /= 1.0 + self._modal_scale_increment
                else:
                    if(event.type == 'WHEELUPMOUSE'):
                        self._modal_rotate_radians -= self._modal_rotate_increment
                        self._modal_rotate_radians_widgets -= self._modal_rotate_increment
                    if(event.type == 'WHEELDOWNMOUSE'):
                        self._modal_rotate_radians += self._modal_rotate_increment
                        self._modal_rotate_radians_widgets += self._modal_rotate_increment
                
                self._widgets_mouse_press(context, event, )
                
                loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
                if(loc is not None):
                    # NOTE: check if i have picked up points..
                    if(self._vs is not None):
                        if(len(self._vs)):
                            self._action_move()
                            self._store()
                
                return {'RUNNING_MODAL'}
        
        # ------------------------------------------------------------------------------------------
        
        # NOTE: super!
        return super()._modal(context, event, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_move'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        if(self._get_prop_value('proportional_mode')):
            self._selection_type = 'WEIGHTS_3D'
        else:
            self._selection_type = 'INDICES_3D'
        
        # NOTE: brush specific props..
        
        self._modal_rotate_increment = 0.1
        self._modal_rotate_radians = 0.0
        self._modal_scale_increment = 0.1
        self._modal_scale_factor = 0.0
        self._brush_prev_location = None
        self._brush_prev_normal = None
        self._vs = None
        self._ns = None
        
        self._modal_rotate_radians_widgets = 0.0
        self._modal_scale_factor_widgets = 1.0


class SCATTER5_OT_manual_brush_tool_rotation_set(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_rotation_set"
    bl_label = "Rotation Settings Brush"
    bl_description = "Rotation Settings Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_rotation_set"
    tool_category = 'ROTATE'
    tool_label = "Rotation Settings Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "PREFERENCES"
    dat_icon = "SCATTER5_ROTATION_SETTINGS"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _modify(self, ):
        indices = self._selection_indices
        me = self._target.data
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            if(self._get_prop_value('use_rotation_align')):
                a = 0
                if(self._get_prop_value('rotation_align') == 'LOCAL_Z_AXIS'):
                    a = 1
                elif(self._get_prop_value('rotation_align') == 'GLOBAL_Z_AXIS'):
                    a = 2
                me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value = a
                u = 0
                if(self._get_prop_value('rotation_up') == 'GLOBAL_Y_AXIS'):
                    u = 1
                me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[ii].value = u
                
                # reset custom vectors as well so brushes using that start from scratch..
                me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = (0.0, 0.0, 0.0, )
                me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector = (0.0, 0.0, 0.0, )
                me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[ii].vector = (0.0, 0.0, 0.0, )
                # and random numbers as well.. they will (read: if i don't forget, they will) be regenerated at first brush run..
                me.attributes['{}private_z_random'.format(self.attribute_prefix)].data[ii].vector = (0.0, 0.0, 0.0, )
            
            if(self._get_prop_value('use_rotation_base')):
                me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[ii].vector = self._get_prop_value('rotation_base')
            
            if(self._get_prop_value('use_rotation_random')):
                me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[ii].vector = self._get_prop_value('rotation_random')
                me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[ii].vector = (random.random(), random.random(), random.random(), )
        
        self._regenerate_rotation_from_attributes(indices, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_rotation_set'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'INDICES_3D'
        
        # NOTE: brush specific props..


# NOTTODO: "Random Rotation" it should modify y alignment as well, not only z. make it optional to spin along instance z? there are many ways of random rotation.. -->> maybe either full control, or nothing at all..
# DONE: some hint lines? --> z axis lines
# DONE: hints are not updated when mouse is out of surface causing them to display outdated on surface re-enter for a single redraw until they are updated
class SCATTER5_OT_manual_brush_tool_random_rotation(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_random_rotation"
    bl_label = "Random Rotation Brush"
    bl_description = "Random Rotation Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_random_rotation"
    tool_category = 'ROTATE'
    tool_label = "Random Rotation Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'speed',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Speed',
            'widget': 'STRENGTH_MINUS_PLUS_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_DICE"
    dat_icon = "SCATTER5_ROTATION_RANDOM"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            if(len(self._w_locations)):
                hints = self._widgets_fabricate_fixed_size_hints_loc_nor_lines_3d(context, event, loc, self._w_locations, self._w_normals, self._theme._outline_color_helper_hint, )
                ls.extend(hints)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _action_begin(self, ):
        self._w_locations = []
        self._w_normals = []
        
        super()._action_begin()
    
    def _action_update(self, ):
        self._w_locations = []
        self._w_normals = []
        
        super()._action_update()
    
    def _modify(self, ):
        me = self._target.data
        
        indices = self._selection_indices
        weights = np.zeros(len(me.vertices), dtype=float, )
        weights[indices] = self._selection_weights
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        for i in indices:
            original = Vector()
            
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            align = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value
            if(align == 0):
                original = me.attributes['{}normal'.format(self.attribute_prefix)].data[ii].vector
                # rotate original normal vector by emitter rotation so there is no sudden jump, global and local z alignments seems to be working fine, but this one need correction..
                m = bpy.data.objects.get(self._surfaces_db[uids[i]]).matrix_world.copy()
                _, mr, _ = m.decompose()
                original.rotate(mr)
            elif(align == 1):
                _, original_1 = self._surfaces_to_world_space(Vector(), Vector((0.0, 0.0, 1.0, )), uids[i], )
                original = original_1.copy()
            elif(align == 2):
                original = Vector((0.0, 0.0, 1.0, ))
            elif(align == 3):
                original = me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[ii].vector
                if(original.length == 0.0):
                    original = me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector
                    me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[ii].vector = original
            
            if(align < 3):
                me.attributes['{}private_z_original'.format(self.attribute_prefix)].data[ii].vector = original
            
            rns = me.attributes['{}private_z_random'.format(self.attribute_prefix)].data[ii].vector
            if(np.sum(rns) == 0.0):
                rns = np.random.rand(3)
                rns[2] = 1.0
            
            pi2 = 2 * np.pi
            start = pi2 * rns[0]
            current = pi2 * rns[1]
            step = self._get_prop_value('speed')
            if(self._get_prop_value('speed_pressure')):
                step = step * self._pressure
            
            # NOTE: apply falloff
            step = step * weights[i]
            
            conform = rns[2]
            conform = conform - step
            if(conform <= 0.0):
                conform = 0.0
            rns[2] = conform
            
            alpha = self._get_prop_value('angle') / 2
            # +
            # |   \
            # a       c
            # |            \
            # +-----1.0-----alpha
            _c = 1.0 / math.cos(alpha)
            _a = (_c ** 2 - 1.0 ** 2) ** 0.5
            A = _a
            B = _a
            
            # Lissajous curve
            # https://en.wikipedia.org/wiki/Lissajous_curve
            # 5 by 4
            
            t = (current + step) % pi2
            # A = 0.5
            a = 5
            f = np.pi / 4
            C = 0
            # B = 0.5
            b = 4
            D = 0
            x = A * np.sin((a * t) + f) + C
            y = B * np.sin(b * t) + D
            
            # TODO: somehow let user to set max variance in degrees? or something like that, or (pi)*0-1? something to control it..
            z = 1.0
            d = Vector((x, y, z, ))
            d.normalize()
            
            q = self._rotation_to(Vector((0.0, 0.0, 1.0, )), original, )
            d.rotate(q)
            
            d = d.lerp(original, conform, )
            
            current = t / pi2
            rns[1] = current
            me.attributes['{}private_z_random'.format(self.attribute_prefix)].data[ii].vector = rns
            
            me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value = 3
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = d
        
        self._regenerate_rotation_from_attributes(indices, )
        
        # NOTE: hint data, just get it finished. faster then filling from loop
        w_locations = self._get_target_attribute_masked(me.vertices, 'co', )
        w_normals = self._get_target_attribute_masked(me.attributes, 'align_z', )
        w_locations, w_normals = self._surfaces_to_world_space(w_locations, w_normals, uids, )
        
        # # DEBUG
        # debug.points(self._target, w_locations, w_normals, )
        # # DEBUG
        
        self._w_locations = w_locations[indices]
        self._w_normals = w_normals[indices]
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_random_rotation'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'WEIGHTS_3D'
        
        # NOTE: brush specific props..
        
        self._widgets_use_timer_events = True
        self._w_locations = []
        self._w_normals = []


# DONE: direction triangle to mouse widget (like on sligned spray)
# DONE: hints are not updated when mouse is out of surface causing them to display outdated on surface re-enter for a single redraw until they are updated
# DONE: masked update
class SCATTER5_OT_manual_brush_tool_comb(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_comb"
    bl_label = "Tangent Alignment Brush"
    bl_description = "Tangent Alignment Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_comb"
    tool_category = 'ROTATE'
    tool_label = "Tangent Alignment Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'strength',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Strength',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_ARROW_TANGENT"
    dat_icon = "SCATTER5_ROTATION_ALIGN"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            if(self._mouse_3d_direction and self._mouse_3d_direction_interpolated):
                tri = self._widgets_fabricate_direction_triangle_3d(loc, nor, radius, woc, )
                ls.extend(tri)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            if(self._mouse_3d_direction and self._mouse_3d_direction_interpolated):
                tri = self._widgets_fabricate_direction_triangle_3d(loc, nor, radius, woc, )
                ls.extend(tri)
            
            if(len(self._w_locations)):
                hints = self._widgets_fabricate_fixed_size_hints_loc_nor_lines_3d(context, event, loc, self._w_locations, self._w_normals, self._theme._outline_color_helper_hint, )
                ls.extend(hints)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _action_begin(self, ):
        self._w_locations = []
        self._w_normals = []
        
        super()._action_begin()
    
    def _action_update(self, ):
        self._w_locations = []
        self._w_normals = []
        
        super()._action_update()
    
    '''
    def _modify(self, ):
        if(not len(self._mouse_3d_path_direction)):
            return
        if(self._mouse_3d_path_direction[-1] is None):
            return
        if(self._mouse_3d_direction is None):
            return
        if(self._mouse_3d_direction_interpolated is None):
            return
        
        me = self._target.data
        
        indices = self._selection_indices
        weights = np.zeros(len(me.vertices), dtype=float, )
        weights[indices] = self._selection_weights
        
        d = self._mouse_3d_direction.copy()
        if(self._get_prop_value('use_direction_interpolation')):
            d = self._mouse_3d_direction_interpolated.copy()
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        # # DEBUG
        # _vs = []
        # _ns = []
        # # DEBUG
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            axis = self._get_axis(ii, uids[i], )
            
            # # DEBUG
            # _co, _ = self._surfaces_to_world_space(me.vertices[i].co, None, uids[i])
            # _vs.append(_co)
            # _ns.append(axis)
            # # DEBUG
            
            py = Vector((0.0, 1.0, 0.0, ))
            e = Euler(me.attributes['{}rotation'.format(self.attribute_prefix)].data[ii].vector)
            py.rotate(e)
            
            def project_on_plane(p, n, q, ):
                return q - Vector(q - p).dot(n) * n
            
            pyp = project_on_plane(Vector((0.0, 0.0, 0.0, )), axis, py, )
            dp = project_on_plane(Vector((0.0, 0.0, 0.0, )), axis, d, )
            
            angle = Vector((dp.x, dp.y, )).angle_signed(Vector((pyp.x, pyp.y, )), 0.0, )
            # NOTE: apply falloff
            angle = angle * (self._get_prop_value('strength') * weights[i])
            
            if(self._get_prop_value('strength_random')):
                r = np.random.rand(1, )
                rr = self._get_prop_value('strength_random_range')
                r = rr[0] + (rr[1] - rr[0]) * r
                angle = angle * r
            
            if(self._get_prop_value('strength_pressure')):
                angle = angle * self._pressure
            
            _eb, _er, _qa, _cr = self._calc_rotation_components_from_attributes(ii, uids[i], )
            _q = Quaternion()
            _q.rotate(_qa)
            _q.rotate(_cr)
            _m = _q.to_matrix().to_4x4()
            e = _m
            e = bpy.data.objects.get(self._surfaces_db[uids[i]]).matrix_world @ e
            
            q = Quaternion(axis, angle, ).to_matrix().to_4x4()
            m = q @ e
            
            _, v, _ = m.decompose()
            v = v.to_euler('XYZ')
            
            z = Vector((0.0, 0.0, 1.0, ))
            z.rotate(v)
            y = Vector((0.0, 1.0, 0.0, ))
            y.rotate(v)
            me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value = 3
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = z
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[ii].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector = y
        
        # # DEBUG
        # debug.points(self._target, _vs, _ns, )
        # # DEBUG
        
        w_locations = self._get_target_attribute_masked(me.vertices, 'co', )[indices]
        w_normals = self._get_target_attribute_masked(me.attributes, 'private_r_up_vector', )[indices]
        
        w_locations, _ = self._surfaces_to_world_space(w_locations, None, uids[indices], )
        
        self._w_locations = w_locations
        self._w_normals = w_normals
        
        self._regenerate_rotation_from_attributes(indices, )
    '''
    
    def _modify(self, ):
        if(not len(self._mouse_3d_path_direction)):
            return
        if(self._mouse_3d_path_direction[-1] is None):
            return
        if(self._mouse_3d_direction is None):
            return
        if(self._mouse_3d_direction_interpolated is None):
            return
        
        me = self._target.data
        
        indices = self._selection_indices
        weights = np.zeros(len(me.vertices), dtype=float, )
        weights[indices] = self._selection_weights
        
        d = self._mouse_3d_direction.copy()
        if(self._get_prop_value('use_direction_interpolation')):
            d = self._mouse_3d_direction_interpolated.copy()
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        # # # DEBUG
        # _vs = []
        # _ns = []
        # # # DEBUG
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            axis = self._get_axis(ii, uids[i], )
            
            # # # DEBUG
            # _co, _ = self._surfaces_to_world_space(me.vertices[i].co, None, uids[i])
            # _vs.append(_co)
            # _ns.append(axis)
            # # # DEBUG
            
            py = Vector((0.0, 1.0, 0.0, ))
            e = Euler(me.attributes['{}rotation'.format(self.attribute_prefix)].data[ii].vector)
            py.rotate(e)
            
            py.rotate(bpy.data.objects.get(self._surfaces_db[uids[i]]).matrix_world)
            
            # # # DEBUG
            # _co, _ = self._surfaces_to_world_space(me.vertices[i].co, None, uids[i])
            # _vs.append(_co)
            # _ns.append(py)
            # # # DEBUG
            
            def project_on_plane(p, n, q, ):
                return q - Vector(q - p).dot(n) * n
            
            pyp = project_on_plane(Vector((0.0, 0.0, 0.0, )), axis, py, )
            dp = project_on_plane(Vector((0.0, 0.0, 0.0, )), axis, d, )
            
            # # # DEBUG
            # _co, _ = self._surfaces_to_world_space(me.vertices[i].co, None, uids[i])
            # _vs.append(_co)
            # _ns.append(pyp)
            # _vs.append(_co)
            # _ns.append(dp)
            # # # DEBUG
            
            cwm = self._rotation_to(axis, Vector((0.0, 0.0, 1.0)))
            pyp = cwm @ pyp
            dp = cwm @ dp
            # print(pyp, dp, )
            
            # # # DEBUG
            # _co, _ = self._surfaces_to_world_space(me.vertices[i].co, None, uids[i])
            # _vs.append(_co)
            # _ns.append(pyp)
            # _vs.append(_co)
            # _ns.append(dp)
            # # # DEBUG
            
            angle = Vector((dp.x, dp.y, )).angle_signed(Vector((pyp.x, pyp.y, )), 0.0, )
            # angle = Vector((pyp.x, pyp.y, )).angle_signed(Vector((dp.x, dp.y, )), 0.0, )
            # NOTE: apply falloff
            angle = angle * (self._get_prop_value('strength') * weights[i])
            
            # print(angle)
            
            if(self._get_prop_value('strength_random')):
                r = np.random.rand(1, )
                rr = self._get_prop_value('strength_random_range')
                r = rr[0] + (rr[1] - rr[0]) * r
                angle = angle * r
            
            if(self._get_prop_value('strength_pressure')):
                angle = angle * self._pressure
            
            _eb, _er, _qa, _cr = self._calc_rotation_components_from_attributes(ii, uids[i], )
            _q = Quaternion()
            _q.rotate(_qa)
            _q.rotate(_cr)
            _m = _q.to_matrix().to_4x4()
            e = _m
            
            e = bpy.data.objects.get(self._surfaces_db[uids[i]]).matrix_world @ e
            
            q = Quaternion(axis, angle, ).to_matrix().to_4x4()
            m = q @ e
            _, v, _ = m.decompose()
            # v = v.to_euler('XYZ')
            # z = Vector((0.0, 0.0, 1.0, ))
            # z.rotate(v)
            # y = Vector((0.0, 1.0, 0.0, ))
            # y.rotate(v)
            z = Vector((0.0, 0.0, 1.0, ))
            z = v @ z
            y = Vector((0.0, 1.0, 0.0, ))
            y = v @ y
            me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value = 3
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = z
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[ii].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector = y
        
        # # # DEBUG
        # debug.points(self._target, _vs, _ns, )
        # # # DEBUG
        
        w_locations = self._get_target_attribute_masked(me.vertices, 'co', )[indices]
        w_normals = self._get_target_attribute_masked(me.attributes, 'private_r_up_vector', )[indices]
        # w_normals = self._get_target_attribute_masked(me.attributes, 'align_y', )[indices]
        
        w_locations, _ = self._surfaces_to_world_space(w_locations, None, uids[indices], )
        
        self._w_locations = w_locations
        self._w_normals = w_normals
        
        self._regenerate_rotation_from_attributes(indices, )
        
        # # DEBUG
        # vs = self._get_target_attribute_masked(me.vertices, 'co', )[indices]
        # ns = self._get_target_attribute_masked(me.attributes, 'align_y', )[indices]
        # vs, ns = self._surfaces_to_world_space(vs, ns, uids[indices])
        # debug.points(self._target, vs, ns, )
        # # DEBUG
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_comb'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'WEIGHTS_3D'
        
        # NOTE: brush specific props..
        
        self._w_locations = []
        self._w_normals = []


# DONE: better y axis then z for hint? or both? --> y axis
# DONE: draw an arrow in spin direction on idle and press?
# NOTTODO: maybe a bit bigger arrows.. -->> eh, no. it is not important, i am even thinking of removing them
# DONE: hints are not updated when mouse is out of surface causing them to display outdated on surface re-enter for a single redraw until they are updated
# DONE: masked update
class SCATTER5_OT_manual_brush_tool_spin(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_spin"
    bl_label = "Spin Brush"
    bl_description = "Spin Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_spin"
    tool_category = 'ROTATE'
    tool_label = "Spin Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'speed',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Speed',
            'widget': 'ANGLE_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Invert Effect: CTRL+LMB",
    )
    
    icon = "FILE_REFRESH"
    dat_icon = "SCATTER5_SPIN"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            # spin direction triangles --------------------------------------
            mt = Matrix.Translation(loc)
            mr = self._rotation_to(Vector((0.0, 0.0, 1.0)), nor).to_matrix().to_4x4()
            s = radius / 10 / 2
            ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
            
            if(self._get_prop_value('speed') == 0.0):
                pass
            else:
                # move arrows a bit in so they fit tessellated circle better
                a = 0.1
                if((event.ctrl and self._get_prop_value('speed') > 0) or not event.ctrl and self._get_prop_value('speed') < 0):
                    # left
                    tm0 = mt @ (mr @ Matrix.Rotation(np.radians(180), 4, 'Y')) @ ms
                    to0 = ((radius / s) - a, 0.0, 0.0, )
                    tm1 = tm0 @ Matrix.Rotation(np.radians(90), 4, 'Z')
                    to1 = to0
                    tm2 = tm0 @ Matrix.Rotation(np.radians(180), 4, 'Z')
                    to2 = to0
                    tm3 = tm0 @ Matrix.Rotation(np.radians(270), 4, 'Z')
                    to3 = to0
                else:
                    # right
                    tm0 = mt @ mr @ ms
                    to0 = ((radius / s) - a, 0.0, 0.0, )
                    tm1 = tm0 @ Matrix.Rotation(np.radians(90), 4, 'Z')
                    to1 = to0
                    tm2 = tm0 @ Matrix.Rotation(np.radians(180), 4, 'Z')
                    to2 = to0
                    tm3 = tm0 @ Matrix.Rotation(np.radians(270), 4, 'Z')
                    to3 = to0
                
                tris = (
                    # spin direction triangle
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to0,
                            'matrix': tm0,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to0,
                            'matrix': tm0,
                            'color': woc,
                        }
                    },
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to1,
                            'matrix': tm1,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to1,
                            'matrix': tm1,
                            'color': woc,
                        }
                    },
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to2,
                            'matrix': tm2,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to2,
                            'matrix': tm2,
                            'color': woc,
                        }
                    },
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to3,
                            'matrix': tm3,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to3,
                            'matrix': tm3,
                            'color': woc,
                        }
                    },
                )
                ls.extend(tris)
            # spin direction triangles --------------------------------------
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            # spin direction triangles --------------------------------------
            mt = Matrix.Translation(loc)
            mr = self._rotation_to(Vector((0.0, 0.0, 1.0)), nor).to_matrix().to_4x4()
            s = radius / 10 / 2
            ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
            
            if(self._get_prop_value('speed') == 0.0):
                pass
            else:
                # move arrows a bit in so they fit tessellated circle better
                a = 0.1
                if((event.ctrl and self._get_prop_value('speed') > 0) or not event.ctrl and self._get_prop_value('speed') < 0):
                    # left
                    tm0 = mt @ (mr @ Matrix.Rotation(np.radians(180), 4, 'Y')) @ ms
                    to0 = ((radius / s) - a, 0.0, 0.0, )
                    tm1 = tm0 @ Matrix.Rotation(np.radians(90), 4, 'Z')
                    to1 = to0
                    tm2 = tm0 @ Matrix.Rotation(np.radians(180), 4, 'Z')
                    to2 = to0
                    tm3 = tm0 @ Matrix.Rotation(np.radians(270), 4, 'Z')
                    to3 = to0
                else:
                    # right
                    tm0 = mt @ mr @ ms
                    to0 = ((radius / s) - a, 0.0, 0.0, )
                    tm1 = tm0 @ Matrix.Rotation(np.radians(90), 4, 'Z')
                    to1 = to0
                    tm2 = tm0 @ Matrix.Rotation(np.radians(180), 4, 'Z')
                    to2 = to0
                    tm3 = tm0 @ Matrix.Rotation(np.radians(270), 4, 'Z')
                    to3 = to0
                
                tris = (
                    # spin direction triangle
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to0,
                            'matrix': tm0,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to0,
                            'matrix': tm0,
                            'color': woc,
                        }
                    },
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to1,
                            'matrix': tm1,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to1,
                            'matrix': tm1,
                            'color': woc,
                        }
                    },
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to2,
                            'matrix': tm2,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to2,
                            'matrix': tm2,
                            'color': woc,
                        }
                    },
                    {
                        'function': 'sharp_triangle_outline_3d',
                        'arguments': {
                            'offset': to3,
                            'matrix': tm3,
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    {
                        'function': 'sharp_triangle_fill_3d',
                        'arguments': {
                            'offset': to3,
                            'matrix': tm3,
                            'color': woc,
                        }
                    },
                )
                ls.extend(tris)
            # spin direction triangles --------------------------------------
            
            if(len(self._w_locations)):
                hints = self._widgets_fabricate_fixed_size_hints_loc_nor_lines_3d(context, event, loc, self._w_locations, self._w_normals, self._theme._outline_color_helper_hint, )
                ls.extend(hints)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _action_begin(self, ):
        self._w_locations = []
        self._w_normals = []
        
        super()._action_begin()
    
    def _action_update(self, ):
        self._w_locations = []
        self._w_normals = []
        
        super()._action_update()
    
    def _modify(self, ):
        me = self._target.data
        
        indices = self._selection_indices
        weights = np.zeros(len(me.vertices), dtype=float, )
        weights[indices] = self._selection_weights
        
        # NOTE: this is not for strictly unique number per particle, but having seed per particles really slow it down.. so this result in stable rotation increment per instance at current state, if some are removed, than it changes, but while in brush it will get the same random number per instance..
        if(self._get_prop_value('speed_random')):
            rng = np.random.default_rng(seed=0, )
            l = np.sum(self._get_target_active_mask())
            rns = rng.random((l, 1))
            rr = self._get_prop_value('speed_random_range')
            rns = rr[0] + (rr[1] - rr[0]) * rns
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            axis = self._get_axis(ii, uids[i], )
            
            # NOTE: apply falloff
            angle = self._get_prop_value('speed') * weights[i]
            
            if(self._get_prop_value('speed_random')):
                u = me.attributes['{}id'.format(self.attribute_prefix)].data[ii].value
                angle = angle * rns[i]
            
            if(self._get_prop_value('speed_pressure')):
                angle = angle * self._pressure
            
            if(self._ctrl):
                angle = angle * -1
            
            _eb, _er, _qa, _cr = self._calc_rotation_components_from_attributes(ii, uids[i], )
            _q = Quaternion()
            _q.rotate(_qa)
            _q.rotate(_cr)
            _m = _q.to_matrix().to_4x4()
            e = _m
            
            e = bpy.data.objects.get(self._surfaces_db[uids[i]]).matrix_world @ e
            
            q = Quaternion(axis, angle, ).to_matrix().to_4x4()
            m = q @ e
            _, v, _ = m.decompose()
            
            z = Vector((0.0, 0.0, 1.0, ))
            z = v @ z
            y = Vector((0.0, 1.0, 0.0, ))
            y = v @ y
            me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[ii].value = 3
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = z
            me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[ii].value = 2
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector = y
        
        w_locations = self._get_target_attribute_masked(me.vertices, 'co', )[indices]
        w_normals = self._get_target_attribute_masked(me.attributes, 'private_r_up_vector', )[indices]
        
        w_locations, _ = self._surfaces_to_world_space(w_locations, None, uids[indices], )
        
        self._w_locations = w_locations
        self._w_normals = w_normals
        
        self._regenerate_rotation_from_attributes(indices, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_spin'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'WEIGHTS_3D'
        
        # NOTE: brush specific props..
        
        self._widgets_use_timer_events = True
        self._w_locations = []
        self._w_normals = []


# DONE: when brush goes from points to none, hint lines are left from last drawing. empty arrays somewhere
# DONE: refactor 2d widget drawing definitions in `_widgets_mouse_idle` and `_widgets_mouse_press`
# DONE: direction triangle to mouse widget (like on sligned spray)
class SCATTER5_OT_manual_brush_tool_z_align(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_z_align"
    bl_label = "Normal Alignment Brush"
    bl_description = "Normal Alignment Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_z_align"
    tool_category = 'ROTATE'
    tool_label = "Normal Alignment Brush"
    tool_domain = '2D'
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius_2d',
            'datatype': 'float',
            'change': 1,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.0f}',
            'name': 'Radius',
            'widget': 'RADIUS_2D',
        },
        '__gesture_secondary__': {
            'property': 'strength',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Strength',
            'widget': 'STRENGTH_2D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_2D',
        },
    }
    tool_gesture_space = '2D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_ARROW_NORMAL"
    dat_icon = "SCATTER5_ROTATION_ALIGN_Z"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        radius = self._domain_aware_brush_radius()
        falloff = self._get_prop_value('falloff')
        
        ls = []
        
        radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
        ls.extend(radoff)
        
        if(self._mouse_2d_direction and self._mouse_2d_direction_interpolated):
            tri = self._widgets_fabricate_direction_triangle_2d(coord, radius, woc, )
            ls.extend(tri)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        falloff = self._get_prop_value('falloff')
        
        ls = []
        
        radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
        ls.extend(radoff)
        
        if(self._mouse_2d_direction and self._mouse_2d_direction_interpolated):
            tri = self._widgets_fabricate_direction_triangle_2d(coord, radius, woc, )
            ls.extend(tri)
        
        if(len(self._w_locations)):
            hints = self._widgets_fabricate_fixed_size_hints_loc_nor_lines_2d(context, event, self._w_locations, self._w_normals, self._theme._outline_color_helper_hint, )
            ls.extend(hints)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _execute(self, ):
        self._ensure_attributes()
        
        self._select()
        indices = self._selection_indices
        if(not len(indices)):
            self._w_locations = []
            self._w_normals = []
            return
        
        weights = self._selection_weights
        
        distances = self._selection_distances
        vs_2d = self._selection_vs_2d
        
        view_direction = self._context_region_data.view_rotation.to_matrix() @ Vector((0.0, 0.0, -1.0, ))
        up_direction = self._context_region_data.view_rotation.to_matrix() @ Vector((0.0, 1.0, 0.0, ))
        view_location = view3d_utils.region_2d_to_origin_3d(self._context_region, self._context_region_data, (self._context_region.width / 2, self._context_region.height / 2), )
        view_target = self._context_region_data.view_location
        
        current = self._mouse_2d_region
        previous = self._mouse_2d_region_prev
        direction = self._mouse_2d_direction
        if(self._get_prop_value('use_direction_interpolation')):
            direction = self._mouse_2d_direction_interpolated
        
        if(direction == Vector()):
            self._w_locations = []
            self._w_normals = []
            return
        
        axis = view_direction
        
        def get_set_axes(i, uid, ):
            me = self._target.data
            a = me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value
            if(a == 0):
                vec, nor = self._surfaces_to_world_space(me.vertices[i].co, me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector, uid, )
                z_axis = Vector(nor)
            elif(a == 1):
                _, nor_1 = self._surfaces_to_world_space(Vector((0.0, 0.0, 0.0, )), Vector((0.0, 0.0, 1.0, )), uid, )
                z_axis = nor_1.copy()
            elif(a == 2):
                z_axis = Vector((0.0, 0.0, 1.0, ))
            elif(a == 3):
                z_axis = Vector(me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector)
            
            if(a < 3):
                # change to custom..
                me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 3
                me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = z_axis
            
            surface_matrix = bpy.data.objects.get(self._surfaces_db[uid]).matrix_world.copy()
            
            locy_1 = Vector((0.0, 1.0, 0.0, ))
            mwi_1 = surface_matrix
            _, cr_1, _ = mwi_1.decompose()
            locy_1.rotate(cr_1)
            
            up = me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value
            if(up == 0):
                y_axis = Vector((0.0, 1.0, 0.0, ))
            elif(up == 1):
                y_axis = Vector((0.0, 1.0, 0.0, ))
                gm = surface_matrix
                _, gr, _ = gm.decompose()
                y_axis.rotate(gr)
            elif(up == 2):
                y_axis = Vector(me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector)
            
            if(up < 2):
                # change to custom..
                me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 2
                me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = y_axis
            
            return z_axis, y_axis
        
        def project_on_plane(p, n, q, ):
            return q - Vector(q - p).dot(n) * n
        
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        
        view_un_rotate = self._rotation_to(view_direction, Vector((0.0, 0.0, 1.0, )), )
        view_rotate = self._rotation_to(Vector((0.0, 0.0, 1.0, )), view_direction, )
        
        flip_axis = axis.copy()
        flip_axis.negate()
        
        coord = current.copy()
        
        vec = view3d_utils.region_2d_to_vector_3d(self._context_region, self._context_region_data, coord, )
        loc = view3d_utils.region_2d_to_location_3d(self._context_region, self._context_region_data, coord, vec, )
        
        coord = current + (direction * radius)
        vec2 = view3d_utils.region_2d_to_vector_3d(self._context_region, self._context_region_data, coord, )
        loc2 = view3d_utils.region_2d_to_location_3d(self._context_region, self._context_region_data, coord, vec, )
        
        direction_3d = loc2 - loc
        direction_3d.normalize()
        
        strength = self._get_prop_value('strength')
        if(self._get_prop_value('strength_pressure')):
            strength = strength * self._pressure
        
        distances_normalized = 1.0 - (distances / radius)
        
        me = self._target.data
        
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        
        for j, i in enumerate(indices):
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            z_axis, y_axis = get_set_axes(ii, uids[i])
            
            s = strength
            # NOTE: apply falloff
            s = s * weights[j]
            
            q = self._rotation_to(z_axis, direction_3d)
            q = Quaternion().slerp(q, s, )
            
            rot_mat = q.to_matrix()
            
            z_axis = rot_mat @ z_axis
            me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[ii].vector = z_axis
            y_axis = rot_mat @ y_axis
            me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[ii].vector = y_axis
        
        w_locations = self._get_target_attribute_masked(me.vertices, 'co', )[indices]
        w_normals = self._get_target_attribute_masked(me.attributes, 'private_r_align_vector', )[indices]
        w_locations, _ = self._surfaces_to_world_space(w_locations, None, uids[indices], )
        
        self._w_locations = w_locations
        self._w_normals = w_normals
        
        self._regenerate_rotation_from_attributes(indices, )
        
        self._target.data.update()
    
    @verbose
    def _action_begin(self, ):
        # NOTE: override - it is true 2d brush, does not depend on mouse projected on surface
        self._execute()
    
    def _action_update(self, ):
        # NOTE: override - it is true 2d brush, does not depend on mouse projected on surface
        self._execute()
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_z_align'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'WEIGHTS_2D'
        
        # NOTE: brush specific props..
        
        self._w_locations = []
        self._w_normals = []


class SCATTER5_OT_manual_brush_tool_scale_set(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_scale_set"
    bl_label = "Scale Settings Brush"
    bl_description = "Scale Settings Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_scale_set"
    tool_category = 'SCALE'
    tool_label = "Scale Settings Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'scale_default',
            'datatype': 'vector',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: ({:.3f}, {:.3f}, {:.3f})',
            'name': 'Default Scale',
            'widget': 'SCALE_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "PREFERENCES"
    dat_icon = "SCATTER5_SCALE_SETTINGS"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _modify(self, ):
        indices = self._selection_indices
        me = self._target.data
        
        r = np.array(self._get_prop_value('scale_random_factor'), dtype=float, )
        if(self._get_prop_value('scale_random_type') == 'UNIFORM'):
            t = 0
        elif(self._get_prop_value('scale_random_type') == 'VECTORIAL'):
            t = 1
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            if(self._get_prop_value('use_scale_default')):
                me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[ii].vector = self._get_prop_value('scale_default')
                me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[ii].vector = (0.0, 0.0, 0.0, )
                
                # regenerate also random numbers..
                me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[ii].vector = np.random.rand(3)
            
            if(self._get_prop_value('use_scale_random_factor')):
                rr = np.random.rand(3)
                me.attributes['{}private_s_random'.format(self.attribute_prefix)].data[ii].vector = r
                me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data[ii].vector = rr
                me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data[ii].value = t
        
        self._regenerate_scale_from_attributes(indices, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_scale_set'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'INDICES_3D'
        
        # NOTE: brush specific props..


class SCATTER5_OT_manual_brush_tool_grow_shrink(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_grow_shrink"
    bl_label = "Grow/Shrink Brush"
    bl_description = "Grow/Shrink Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_grow_shrink"
    tool_category = 'SCALE'
    tool_label = "Grow/Shrink Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'change',
            'datatype': 'vector',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: ({:.3f}, {:.3f}, {:.3f})',
            'name': 'Scale Change',
            'widget': 'SCALE_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
        "• Invert Effect: CTRL+LMB",
    )
    
    icon = "W_SCALE_GROW"
    dat_icon = "SCATTER5_SCALE_GROW"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _modify(self, ):
        me = self._target.data
        
        indices = self._selection_indices
        weights = np.zeros(len(me.vertices), dtype=float, )
        weights[indices] = self._selection_weights
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            change = np.array(self._get_prop_value('change'), dtype=float, )
            
            # NOTE: apply falloff
            change = change * weights[i]
            
            if(self._get_prop_value('change_pressure')):
                change = change * self._pressure
            if(self._get_prop_value('change_mode') == 'SUBTRACT'):
                change = -change
            
            if(self._ctrl):
                # if CTRL is pressed, invert mode
                change = -change
            
            if(self._get_prop_value('use_change_random')):
                rnd = np.array(me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[ii].vector, dtype=float, )
                rr = self._get_prop_value('change_random_range')
                rv = rr[0] + (rr[1] - rr[0]) * rnd[1]
                change = change * rv
            
            if(self._get_prop_value('use_limits')):
                s = np.array(me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[ii].vector, dtype=float, )
                ch = np.array(me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[ii].vector, dtype=float, )
                r = change.copy()
                minv, maxv = self._get_prop_value('limits')
                
                x = s[0] + ch[0] + r[0]
                if(x >= maxv):
                    r[0] = maxv - s[0]
                elif(x <= minv):
                    r[0] = -(s[0] - minv)
                else:
                    r[0] = ch[0] + r[0]
                
                y = s[1] + ch[1] + r[1]
                if(y >= maxv):
                    r[1] = maxv - s[1]
                elif(y <= minv):
                    r[1] = -(s[1] - minv)
                else:
                    r[1] = ch[1] + r[1]
                
                z = s[2] + ch[2] + r[2]
                if(z >= maxv):
                    r[2] = maxv - s[2]
                elif(z <= minv):
                    r[2] = -(s[2] - minv)
                else:
                    r[2] = ch[2] + r[2]
            else:
                ch = np.array(me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[ii].vector, dtype=float, )
                r = ch + change
            
            me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[ii].vector = r
        
        self._regenerate_scale_from_attributes(indices, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_grow_shrink'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'WEIGHTS_3D'
        
        # NOTE: brush specific props..


class SCATTER5_OT_manual_brush_tool_object_set(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_object_set"
    bl_label = "Object Index Brush"
    bl_description = "Object Index Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_object_set"
    tool_category = 'SPECIAL'
    tool_label = "Object Index Brush"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Radius',
            'widget': 'RADIUS_3D',
        },
        '__gesture_secondary__': {
            'property': 'index',
            'datatype': 'int',
            'change': 1,
            'change_pixels': 20,
            'change_wheel': 20,
            'text': '{}: {}',
            'name': 'Object Index',
            'widget': 'TOOLTIP_3D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_3D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_3D',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_INSTANCE"
    dat_icon = "SCATTER5_INSTANCE"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._domain_aware_brush_radius()
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._domain_aware_brush_radius()
            if(self._get_prop_value('radius_pressure')):
                radius = radius * self._pressure
            falloff = self._get_prop_value('falloff')
            
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            radoff = self._widgets_fabricate_radius_with_falloff_3d(mt, mr, ms, radius, falloff, woc, wfc, )
            ls.extend(radoff)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _modify(self, ):
        indices = self._selection_indices
        
        me = self._target.data
        objects = self._get_target_attribute_masked(me.attributes, 'index', )
        objects[indices] = self._get_prop_value('index')
        self._set_target_attribute_masked(me.attributes, 'index', objects, )
        
        self._force_update = True
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_object_set'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'INDICES_3D'
        
        # NOTE: brush specific props..
        
        # # DEBUG
        # l = len(self._target.data.vertices)
        # vs = np.zeros(l * 3, dtype=float, )
        # self._target.data.vertices.foreach_get('co', vs, )
        # vs.shape = (-1, 3)
        # self._w_points = vs
        # # DEBUG


# DONE: refactor 2d widget drawing definitions in `_widgets_mouse_idle` and `_widgets_mouse_press`
# DONE: how to prevent points falling through objects that have volume? ray cast from a tiny bit above?
# DONE: most likely the same problem as with hints in comb and spin it is only not visible because lines are zero length, but should be fixed anyway
class SCATTER5_OT_manual_brush_tool_drop_down(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_drop_down"
    bl_label = "Drop Down Brush"
    bl_description = "Drop Down Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_drop_down"
    tool_category = 'TRANSLATE'
    tool_label = "Drop Down Brush"
    tool_domain = '2D'
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius_2d',
            'datatype': 'float',
            'change': 1,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.0f}',
            'name': 'Radius',
            'widget': 'RADIUS_2D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_2D',
        },
        '__gesture_quaternary__': {
            'property': 'affect',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Probability',
            'widget': 'STRENGTH_2D',
        },
    }
    tool_gesture_space = '2D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "NLA_PUSHDOWN"
    dat_icon = "SCATTER5_DROP_DOWN"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        radius = self._domain_aware_brush_radius()
        falloff = self._get_prop_value('falloff')
        
        ls = []
        
        radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
        ls.extend(radoff)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        falloff = self._get_prop_value('falloff')
        
        ls = []
        
        radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
        ls.extend(radoff)
        
        if(len(self._w_origins)):
            hints = self._widgets_fabricate_hints_origin_destination_lines(self._w_origins, self._w_destinations, Matrix(), self._theme._outline_color_helper_hint, )
            ls.extend(hints)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _execute(self, ):
        self._ensure_attributes()
        
        self._select()
        indices = self._selection_indices
        if(not len(indices)):
            self._w_origins = []
            self._w_destinations = []
            return
        
        me = self._target.data
        
        vs_orig = self._selection_vs_original
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs_orig, None, uids, )
        
        z = Vector()
        direction = Vector((0.0, 0.0, -1.0))
        
        w_origins = []
        w_destinations = []
        
        extra_z = 0.001
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            v = vs[i]
            v[2] += extra_z
            loc, _, idx, dst = self._bvh.ray_cast(v, direction, )
            
            # NOTE: better stick to surface
            epsilon = 0.001 / 2
            if(dst):
                if(dst < epsilon):
                    loc, _, idx, dst = self._bvh.find_nearest(v, )
            
            if(loc):
                # append to widget lists before conversion to surface space
                w_origins.append(vs[i])
                w_destinations.append(loc.to_tuple())
                
                if(self._get_prop_value('update_uuid')):
                    n_uid = int(ToolSessionCache._cache['arrays']['f_surface'][idx])
                    me.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[ii].value = n_uid
                    uids[i] = n_uid
                
                loc, _ = self._world_to_surfaces_space(loc, None, uids[i], )
                
                self._target.data.vertices[ii].co = loc
            else:
                # NOTE: do we need to handle situation when there is no ground under to drop to? or we let user to sort it out in this case?
                pass
                
                if(self._get_prop_value('use_ground_plane')):
                    loc = Vector((v[0], v[1], 0.0))
                    
                    # append to widget lists before conversion to surface space
                    w_origins.append(vs[i])
                    w_destinations.append(loc.to_tuple())
                    
                    if(self._get_prop_value('update_uuid')):
                        _, _, idx, _ = self._bvh.find_nearest(v, )
                        n_uid = int(ToolSessionCache._cache['arrays']['f_surface'][idx])
                        me.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[ii].value = n_uid
                        uids[i] = n_uid
                    
                    loc, _ = self._world_to_surfaces_space(loc, None, uids[i], )
                    self._target.data.vertices[ii].co = loc
        
        self._w_origins = w_origins
        self._w_destinations = w_destinations
    
    def _execute_all(self, ):
        self._ensure_attributes()
        
        self._select_all()
        
        indices = self._selection_indices
        if(not len(indices)):
            return
        
        me = self._target.data
        
        vs_orig = self._selection_vs_original
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs_orig, None, uids, )
        
        z = Vector()
        direction = Vector((0.0, 0.0, -1.0))
        
        extra_z = 0.001
        
        for i in indices:
            ii = self._get_masked_index_to_target_vertex_index(i, )
            
            v = vs[i]
            v[2] += extra_z
            loc, _, _, dst = self._bvh.ray_cast(v, direction, )
            
            # NOTE: better stick to surface
            epsilon = 0.001 / 2
            if(dst):
                if(dst < epsilon):
                    loc, _, _, dst = self._bvh.find_nearest(v, )
            
            if(loc):
                loc, _ = self._world_to_surfaces_space(loc, None, uids[i], )
                
                self._target.data.vertices[ii].co = loc
            else:
                # NOTE: do we need to handle situation when there is no ground under to drop to? or we let user to sort it out in this case?
                pass
                
                if(self._get_prop_value('use_ground_plane')):
                    loc = Vector((v[0], v[1], 0.0))
                    loc, _ = self._world_to_surfaces_space(loc, None, uids[i], )
                    self._target.data.vertices[ii].co = loc
        
        self._w_origins = []
        self._w_destinations = []
    
    @verbose
    def _action_begin(self, ):
        self._w_locations = []
        self._w_normals = []
        
        # NOTE: override - it is true 2d brush, does not depend on mouse projected on surface
        self._execute()
    
    def _action_update(self, ):
        self._w_locations = []
        self._w_normals = []
        
        # NOTE: override - it is true 2d brush, does not depend on mouse projected on surface
        self._execute()
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_drop_down'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'INDICES_2D'
        
        # NOTE: brush specific props..
        
        self._widgets_use_timer_events = True
        self._w_origins = []
        self._w_destinations = []


# DONE: refactor 2d widget drawing definitions in `_widgets_mouse_idle` and `_widgets_mouse_press`
# DONE: proportional mode, should be easy now with `_select_2d` result `_distances_normalized`
# TODO: with extremely spaced points and in perspective view, some points are moved beyond cursor. does not happen in ortho. it is not tecnically a bug, it is just perspective, but is there some way to count projection in so it looks 'correctly'? even though points in distance will actually move further then close points?
class SCATTER5_OT_manual_brush_tool_free_move(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_free_move"
    bl_label = "Free Move Brush"
    bl_description = "Free Move Brush"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_free_move"
    tool_category = 'TRANSLATE'
    tool_label = "Free Move Brush"
    tool_domain = '2D'
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'property': 'radius_2d',
            'datatype': 'float',
            'change': 1,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.0f}',
            'name': 'Radius',
            'widget': 'RADIUS_2D',
        },
        '__gesture_tertiary__': {
            'property': 'falloff',
            'datatype': 'float',
            'change': 1 / 100,
            'change_pixels': 1,
            'change_wheel': 20,
            'text': '{}: {:.3f}',
            'name': 'Falloff',
            'widget': 'STRENGTH_2D',
        },
    }
    tool_gesture_space = '2D'
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_MOVE"
    dat_icon = "SCATTER5_FREE_MOVE"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_mouse_idle(self, context, event, ):
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        radius = self._domain_aware_brush_radius()
        falloff = self._get_prop_value('falloff')
        
        ls = []
        
        radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
        ls.extend(radoff)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        radius = self._domain_aware_brush_radius()
        if(self._get_prop_value('radius_pressure')):
            radius = radius * self._pressure
        falloff = self._get_prop_value('falloff')
        
        ls = []
        
        radoff = self._widgets_fabricate_radius_with_falloff_and_dot_2d(coord, radius, falloff, woc, wfc, )
        ls.extend(radoff)
        
        if(len(self._w_origins)):
            hints = self._widgets_fabricate_hints_origin_destination_lines(self._w_origins, self._w_destinations, Matrix(), self._theme._outline_color_helper_hint, )
            ls.extend(hints)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    @verbose
    def _action_pickup(self, ):
        me = self._target.data
        
        vs = self._get_target_attribute_masked(me.vertices, 'co', )
        self._vertices = vs.copy()
        uids = self._get_target_attribute_masked(me.attributes, 'surface_uuid', )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        self._locations = vs
        self._uids = uids
        
        indices = self._selection_indices
        weights = self._selection_weights
        
        vs = self._locations[indices]
        x = (np.min(vs[:, 0]), np.max(vs[:, 0]))
        y = (np.min(vs[:, 1]), np.max(vs[:, 1]))
        z = (np.min(vs[:, 2]), np.max(vs[:, 2]))
        cx = x[0] + ((x[1] - x[0]) / 2)
        cy = y[0] + ((y[1] - y[0]) / 2)
        cz = z[0] + ((z[1] - z[0]) / 2)
        c = np.array([cx, cy, cz, ], dtype=float, )
        self._center = c
        
        self._start_2d = self._mouse_2d_region.copy()
        self._end_2d = self._mouse_2d_region.copy()
        self._start_3d = view3d_utils.region_2d_to_location_3d(self._context_region, self._context_region_data, self._start_2d, self._center, )
        self._end_3d = view3d_utils.region_2d_to_location_3d(self._context_region, self._context_region_data, self._end_2d, self._center, )
        
        self._w_origins = self._locations[indices].copy()
        self._w_destinations = self._w_origins.copy()
    
    @verbose
    def _action_move(self, ):
        self._end_2d = self._mouse_2d_region.copy()
        self._end_3d = view3d_utils.region_2d_to_location_3d(self._context_region, self._context_region_data, self._end_2d, self._center, )
        diff = self._end_3d - self._start_3d
        
        indices = self._selection_indices
        weights = self._selection_weights
        
        # NOTE: apply falloff
        diff = np.array(diff, dtype=float, )
        diff = np.full((len(indices), 3), diff, dtype=float, )
        diff = diff * weights.reshape(-1, 1)
        
        me = self._target.data
        vs = self._locations[indices]
        vs = vs + diff
        vs, _ = self._world_to_surfaces_space(vs, None, self._uids[indices])
        coords = self._vertices.copy()
        coords[indices] = vs
        self._set_target_attribute_masked(me.vertices, 'co', coords, )
        self._target.data.update()
        
        self._w_origins = self._locations[indices].copy()
        self._w_destinations = self._w_origins + np.array(diff, dtype=float, )
    
    @verbose
    def _action_drop(self, ):
        # NOTE: add some snapping options? but that is job of surface move tool..
        pass
    
    # @verbose
    def _action_begin(self, ):
        # NOTE: true 2d brush, no checks
        self._select()
        if(len(self._selection_indices)):
            self._action_pickup()
    
    def _action_update(self, ):
        # NOTE: true 2d brush, no checks
        if(len(self._selection_indices)):
            self._action_move()
    
    def _action_finish(self, ):
        # NOTE: true 2d brush, no checks
        if(len(self._selection_indices)):
            self._action_drop()
        
        self._w_origins = []
        self._w_destinations = []
        
        # push to history..
        bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_free_move'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        # NOTE: overrides..
        self._action_execute_on = self._get_prop_value('draw_on')
        self._action_timer_interval = self._get_prop_value('interval')
        
        self._selection_type = 'WEIGHTS_2D'
        
        # NOTE: brush specific props..
        
        self._w_origins = []
        self._w_destinations = []


# ------------------------------------------------------------------ modify brushes <<<
# ------------------------------------------------------------------ special brushes >>>


# DONE: make it select point on release and draw selected point on press and move
# DONE: weird things are happening because of split personality this tool have. got to rethink basic interaction. i would like following: idle is normal, once ctrl is pressed, there is preview which closest point will be selected, when lmb down, same preview, you are allowed to move mouse to select different next to it, on lmb release point is selected and gizmo shown. operate as you wish, but when you press ctrl you get into point selection mode again (hide gizmo at this point back again?)
# DONE: and i am not sure about ctrl, holding ctrl makes gizmo to move by steps (like shift lowes sensitivity or what is this called). so select point at shift+ctrl?
# DONE: or switch selection / manipulation with SPACE? that might be best option. clear modes, one to select point, second to manipulate point. i think this is it
# DONE: manipulator is getting stuck in navigating
# DONE: make it use 2d selection so i can pick up point that has been moved out of surface
# DONE: error on select with no points
# DONE: it is getting stuck in navigating while gizmos are active.. again
# DONE: update ./manual/gizmos.py module to work with new getting emitter/surfaces/target, multiple surfaces and new place for tool props
# TODO: multi selection with shift? gizmo at center of selection?
# DONE: update invoke get emitter/surface(s)/target and in gizmos module
# DONE: masked update
class SCATTER5_OT_manual_brush_tool_manipulator(SCATTER5_OT_common_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_manipulator"
    bl_label = "Manipulator"
    bl_description = "Manipulator"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_manipulator"
    tool_category = 'SPECIAL'
    tool_label = "Manipulator"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'name': 'Swap Gizmo',
            'function': '_swap_mode',
            'arguments': {},
            'widget': 'FUNCTION_CALL',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Select: LMB",
        # "• Select Add: SHIFT+LMB",
        # "• Select Sub: CTRL+SHIFT+LMB",
        "• Mode: SPACE",
    )
    
    """
    tool_workspace_idname = "scatter5.manual_brush_tool_manipulator_workspace_tool"
    """
    tool_widget = "OBJECT_GGT_sc5_manipulator"
    
    icon = "EMPTY_ARROWS"
    dat_icon = "SCATTER5_MANIPULATOR"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    def _widgets_fabricate_selected_point(self, region, rv3d, pos, woc, ):
        coord = view3d_utils.location_3d_to_region_2d(region, rv3d, pos, )
        ls = tuple()
        if(coord is not None):
            # NOTE: coord is None when outside of view.. so be careful
            ls = (
                # circle
                {
                    'function': 'circle_thick_outline_dashed_2d',
                    'arguments': {
                        'center': coord,
                        'radius': int(self._theme._fixed_radius / 2),
                        'steps': int(self._theme._circle_steps / 2),
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                # dot
                {
                    # 'function': 'dot_shader_2d',
                    'function': 'dot_shader_2_2d',
                    'arguments': {
                        'center': coord,
                        'diameter': self._theme._fixed_center_dot_radius * 2,
                        'color': woc,
                    },
                },
            )
        return ls
    
    def _widgets_mouse_idle(self, context, event, ):
        from .gizmos import SC5GizmoManager
        if(SC5GizmoManager.index != -1):
            self._widgets_clear(context, event, )
            return
        
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        
        ls = []
        
        c = self._widgets_fabricate_fixed_size_cross_cursor_and_dot_2d(coord, woc, wfc, )
        ls.extend(c)
        
        if(self._w_position is not None):
            '''
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            coord = view3d_utils.location_3d_to_region_2d(context.region, context.region_data, self._w_position, )
            if(coord is not None):
                # NOTE: coord is None when outside of view.. so be careful
                select = (
                    # circle
                    {
                        'function': 'circle_thick_outline_dashed_2d',
                        'arguments': {
                            'center': coord,
                            'radius': int(self._theme._fixed_radius / 2),
                            'steps': int(self._theme._circle_steps / 2),
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # dot
                    {
                        # 'function': 'dot_shader_2d',
                        'function': 'dot_shader_2_2d',
                        'arguments': {
                            'center': coord,
                            'diameter': self._theme._fixed_center_dot_radius * 2,
                            'color': woc,
                        },
                    },
                )
                ls.extend(select)
            '''
            sel = self._widgets_fabricate_selected_point(context.region, context.region_data, self._w_position, self._theme._outline_color_press, )
            ls.extend(sel)
        
        '''
        for pos in self._w_dots:
            sel = self._widgets_fabricate_selected_point(context.region, context.region_data, pos, self._theme._outline_color_press, )
            ls.extend(sel)
        '''
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        from .gizmos import SC5GizmoManager
        if(SC5GizmoManager.index != -1):
            self._widgets_clear(context, event, )
            return
        
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        
        ls = []
        
        c = self._widgets_fabricate_fixed_size_cross_cursor_and_dot_2d(coord, woc, wfc, )
        ls.extend(c)
        
        if(self._w_position is not None):
            '''
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            coord = view3d_utils.location_3d_to_region_2d(context.region, context.region_data, self._w_position, )
            if(coord is not None):
                # NOTE: coord is None when outside of view.. so be careful
                select = (
                    # circle
                    {
                        'function': 'circle_thick_outline_dashed_2d',
                        'arguments': {
                            'center': coord,
                            'radius': int(self._theme._fixed_radius / 2),
                            'steps': int(self._theme._circle_steps / 2),
                            'color': woc,
                            'thickness': self._theme._outline_thickness,
                        }
                    },
                    # dot
                    {
                        # 'function': 'dot_shader_2d',
                        'function': 'dot_shader_2_2d',
                        'arguments': {
                            'center': coord,
                            'diameter': self._theme._fixed_center_dot_radius * 2,
                            'color': woc,
                        },
                    },
                )
                ls.extend(select)
            '''
            sel = self._widgets_fabricate_selected_point(context.region, context.region_data, self._w_position, self._theme._outline_color_press, )
            ls.extend(sel)
        
        '''
        for pos in self._w_dots:
            sel = self._widgets_fabricate_selected_point(context.region, context.region_data, pos, self._theme._outline_color_press, )
            ls.extend(sel)
        '''
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _modal_shortcuts(self, context, event, ):
        # NOTE: so i can still add some dubug stuff in base class i will then hace everywhere. currently on manipulator defines own `_modal_shortcuts`..
        super()._modal_shortcuts(context, event, )
        
        # NOTE: is called from `_modal`, after all else is handled (apart from exit), any custom keys can be put here..
        if(event.type == 'SPACE' and event.value == 'RELEASE'):
            from .gizmos import SC5GizmoManager
            
            if(self._gizmo_mode):
                self._gizmo_mode = False
                # gizmo is shown, hide
                SC5GizmoManager.index = -1
                
                co = self._target.data.vertices[self._index].co.copy()
                # co, _ = self._apply_matrix(self._surface.matrix_world, co, )
                uid = self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[self._index].value
                co, _ = self._surfaces_to_world_space(co, None, uid, )
                self._w_position = co
                self._widgets_mouse_idle(context, event, )
            else:
                # gizmo is not shown,
                if(self._index < 0):
                    # nothing selected.. cannot run
                    self._gizmo_mode = False
                    SC5GizmoManager.index = -1
                    
                    self._widgets_mouse_idle(context, event, )
                    return
                else:
                    # something selected, show gizmo
                    self._gizmo_mode = True
                    
                    '''
                    if(SC5GizmoManager.index != self._index):
                        # push to history..
                        bpy.ops.ed.undo_push(message=self.bl_label, )
                        
                        SC5GizmoManager.index = self._index
                        self._flatten(self._index, )
                        
                        # NOTE: in some rare cases (and seems to be connected with higher number of vertices), hidden gizmos were not updated by newly selected vertex, lets call it again here.. it is called on index change anyway.. seems to be fixed, but test it properly, with gizmos you never know..
                        # TODO: check if `group.refresh()` should not be called as well. this time i guess with `SC5GizmoManager.group.refresh(bpy.context, )` to have some effect, like with internal `setup()` call..
                        if(SC5GizmoManager.group is not None):
                            SC5GizmoManager.group.rebuild()
                    '''
                    
                    # push to history..
                    bpy.ops.ed.undo_push(message=self.bl_label, )
                    
                    SC5GizmoManager.surface = self._surfaces_db[int(self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[self._index].value)]
                    
                    SC5GizmoManager.index = self._index
                    self._flatten(self._index, )
                    
                    # # DEBUG
                    # v = bpy.data.objects.get(SC5GizmoManager.surface).matrix_world @ self._target.data.vertices[SC5GizmoManager.index].co
                    # e = Euler(self._target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
                    # n = e @ Vector((0.0, 0.0, 1.0))
                    # debug.points(self._target, v, n, )
                    # # DEBUG
                    
                    # NOTE: in some rare cases (and seems to be connected with higher number of vertices), hidden gizmos were not updated by newly selected vertex, lets call it again here.. it is called on index change anyway.. seems to be fixed, but test it properly, with gizmos you never know..
                    # TODO: check if `group.refresh()` should not be called as well. this time i guess with `SC5GizmoManager.group.refresh(bpy.context, )` to have some effect, like with internal `setup()` call..
                    if(SC5GizmoManager.group is not None):
                        SC5GizmoManager.group.rebuild()
                        # SC5GizmoManager.group.refresh(context, )
                    
                    self._widgets_clear(context, event, )
    
    def _lock(self, ):
        # NOTE: called on invoke, lock selectability on all objects in scene, store their status in SC5GizmoManager and restore on brush cleanup
        d = {}
        for o in bpy.data.objects:
            d[o.name] = o.hide_select
            o.hide_select = True
        
        from .gizmos import SC5GizmoManager
        SC5GizmoManager.restore = d
    
    def _unlock(self, ):
        # NOTE: have to be called on brush cleanup, use this for manipulator only and use event blocking like in other brushes
        from .gizmos import SC5GizmoManager
        d = SC5GizmoManager.restore
        for k, v in d.items():
            o = bpy.data.objects.get(k)
            if(o is not None):
                o.hide_select = v
        
        SC5GizmoManager.restore = {}
    
    def _swap_mode(self, ):
        if(not self._gizmo_mode):
            return
        
        # if(self._brush.translation):
        if(self._get_prop_value('translation')):
            # self._brush.translation = False
            # self._brush.rotation = True
            # self._brush.scale = True
            self._set_prop_value('translation', False)
            self._set_prop_value('rotation', True)
            self._set_prop_value('scale', True)
        else:
            self._set_prop_value('translation', True)
            self._set_prop_value('rotation', False)
            self._set_prop_value('scale', False)
    
    """
    def _find_closest(self, vs, point, ):
        d = ((vs[:, 0] - point[0]) ** 2 + (vs[:, 1] - point[1]) ** 2 + (vs[:, 2] - point[2]) ** 2) ** 0.5
        return np.argmin(d, )
    """
    
    def _flatten(self, i, ):
        # DONE: flatten transformation attributes into base rotation and scale, gizmos will work only with these, so flatten all random and extra components into base attribute
        target = self._target
        me = target.data
        
        # rotation
        r = me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector[:]
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector = r
        me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 2
        me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 1.0]
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 0
        me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = [0.0, 1.0, 0.0]
        
        # scale
        s = me.attributes['{}scale'.format(self.attribute_prefix)].data[i].vector[:]
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = s
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data[i].value = 0
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        
        self._regenerate_scale_from_attributes(np.array([i, ], dtype=int, ), )
        self._regenerate_rotation_from_attributes(np.array([i, ], dtype=int, ), )
    
    def _regenerate_rotation_from_attributes(self, indices, ):
        target = self._target
        me = target.data
        # surface = self._surface
        
        l = len(me.vertices)
        
        _rotation = np.zeros(l * 3, dtype=float, )
        me.attributes['{}rotation'.format(self.attribute_prefix)].data.foreach_get('vector', _rotation, )
        _rotation.shape = (-1, 3)
        
        _private_r_base = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_base, )
        _private_r_base.shape = (-1, 3)
        
        _align_z = np.zeros((l * 3), dtype=float, )
        me.attributes['{}align_z'.format(self.attribute_prefix)].data.foreach_get('vector', _align_z, )
        _align_z.shape = (-1, 3)
        _align_y = np.zeros((l * 3), dtype=float, )
        me.attributes['{}align_y'.format(self.attribute_prefix)].data.foreach_get('vector', _align_y, )
        _align_y.shape = (-1, 3)
        
        # select points to modify by indices
        rotation = _rotation[indices]
        private_r_base = _private_r_base[indices]
        align_z = _align_z[indices]
        align_y = _align_y[indices]
        
        # ---------------------------------------------------------------------
        
        rotation = np.zeros((len(indices), 3), dtype=float, )
        align_z = np.zeros((len(indices), 3), dtype=float, )
        align_y = np.zeros((len(indices), 3), dtype=float, )
        for i in range(len(indices)):
            v = Vector((0.0, 0.0, 1.0))
            v.rotate(Euler(private_r_base[i]))
            align_z[i] = v.to_tuple()
            
            v = Vector((0.0, 1.0, 0.0))
            v.rotate(Euler(private_r_base[i]))
            align_y[i] = v.to_tuple()
            
            rotation[i] = private_r_base[i]
        
        _rotation[indices] = rotation
        me.attributes['{}rotation'.format(self.attribute_prefix)].data.foreach_set('vector', _rotation.flatten(), )
        _align_z[indices] = align_z
        me.attributes['{}align_z'.format(self.attribute_prefix)].data.foreach_set('vector', _align_z.flatten(), )
        _align_y[indices] = align_y
        me.attributes['{}align_y'.format(self.attribute_prefix)].data.foreach_set('vector', _align_y.flatten(), )
    
    def _regenerate_scale_from_attributes(self, indices, ):
        target = self._target
        me = target.data
        # surface = self._surface
        
        l = len(me.vertices)
        
        # get all..
        _scale = np.zeros(l * 3, dtype=float, )
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_get('vector', _scale, )
        _scale.shape = (-1, 3)
        
        _private_s_base = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_base, )
        _private_s_base.shape = (-1, 3)
        
        _private_s_random = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_random, )
        _private_s_random.shape = (-1, 3)
        
        _private_s_random_random = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_random_random, )
        _private_s_random_random.shape = (-1, 3)
        
        _private_s_random_type = np.zeros(l, dtype=int, )
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data.foreach_get('value', _private_s_random_type, )
        
        _private_s_change = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_change, )
        _private_s_change.shape = (-1, 3)
        
        # slice by indices..
        scale = _scale[indices]
        private_s_base = _private_s_base[indices]
        private_s_random = _private_s_random[indices]
        private_s_random_random = _private_s_random_random[indices]
        private_s_random_type = _private_s_random_type[indices]
        private_s_change = _private_s_change[indices]
        
        # calculate..
        l = len(indices)
        for i in range(l):
            d = private_s_base[i]
            r = private_s_random[i]
            rr = private_s_random_random[i]
            
            if(private_s_random_type[i] == 0):
                # 'UNIFORM'
                f = rr[0]
                fn = 1.0 - f
                dr = d * r
                s = (d * fn) + (dr * f)
            elif(private_s_random_type[i] == 1):
                # 'VECTORIAL'
                f = r + (1.0 - r) * rr
                s = d * f
            
            s = s + private_s_change[i]
            
            scale[i] = s
        
        # and set back to attribute..
        _scale[indices] = scale
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_set('vector', _scale.flatten(), )
    
    # @verbose
    def _regenerate(self, ):
        from .gizmos import SC5GizmoManager
        self._regenerate_scale_from_attributes(np.array([SC5GizmoManager.index, ], dtype=int, ), )
        self._regenerate_rotation_from_attributes(np.array([SC5GizmoManager.index, ], dtype=int, ), )
    
    # TODO: there will be a bit better performance if i cache 2d points until view is moved (not easy to know if it is or not). or at least cache vertices from mesh until mode is swapped (after that i can expect modifications..)
    @verbose
    def _choose(self, add=False, sub=False, ):
        if(not len(self._target.data.vertices)):
            return
        
        allowed_mask = self._get_target_active_mask()
        
        # get target vertices
        vs = np.zeros(len(self._target.data.vertices) * 3, dtype=float, )
        self._target.data.vertices.foreach_get('co', vs, )
        vs.shape = (-1, 3, )
        vs = vs[allowed_mask]
        
        # transform to screen space
        # model = np.array(self._surface.matrix_world, dtype=float, )
        uids = np.zeros(len(self._target.data.vertices), dtype=int, )
        self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data.foreach_get('value', uids, )
        uids = uids[allowed_mask]
        
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        world_points = vs.copy()
        
        view = np.array(self._context_region_data.view_matrix, dtype=float, )
        projection = np.array(self._context_region_data.window_matrix, dtype=float, )
        
        vs = np.c_[vs, np.ones(len(vs), dtype=vs.dtype, )]
        # vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
        
        x = vs[:, 0]
        y = vs[:, 1]
        z = vs[:, 1]
        w = vs[:, 3]
        x_ndc = x / w
        y_ndc = y / w
        z_ndc = z / w
        
        x2d = (x_ndc + 1.0) / 2.0
        y2d = (y_ndc + 1.0) / 2.0
        # z2d = (z_ndc + 1.0) / 2.0
        
        # # NOTE: do i need some depth? lets go with zeros for now
        # z = np.zeros(len(vs), dtype=float, )
        # vs2d = np.c_[x2d, y2d, z]
        # vs2d = np.c_[x2d, y2d, z2d]
        vs2d = np.c_[x2d, y2d, ]
        # # and normalize path from pixels to 0.0-1.0
        # vertices2d = np.zeros((len(vertices), 2), dtype=float, )
        # vertices2d[:, 0] = vertices[:, 0] * (1.0 / self._context_region.width)
        # vertices2d[:, 1] = vertices[:, 1] * (1.0 / self._context_region.height)
        # to pixel coordinates
        vs2d[:, 0] = vs2d[:, 0] * self._context_region.width
        vs2d[:, 1] = vs2d[:, 1] * self._context_region.height
        
        # x, y are in pixels, z is normalized 0-1, so put mouse at z 1.0 to select by depth as well
        # point = Vector((self._mouse_2d_region.x, self._mouse_2d_region.y, 1.0, ))
        point = self._mouse_2d_region
        
        # # 3d
        # ds = ((vs2d[:, 0] - point[0]) ** 2 + (vs2d[:, 1] - point[1]) ** 2 + (vs2d[:, 2] - point[2]) ** 2) ** 0.5
        # 2d
        ds = ((vs2d[:, 0] - point[0]) ** 2 + (vs2d[:, 1] - point[1]) ** 2) ** 0.5
        
        closest = np.argmin(ds, )
        ii = self._get_masked_index_to_target_vertex_index(closest, )
        
        # self._index = closest
        self._index = ii
        # self._w_position = self._surface.matrix_world @ self._target.data.vertices[closest].co
        # m = bpy.data.objects.get(self._surfaces_db[uids[closest]]).matrix_world
        m = bpy.data.objects.get(self._surfaces_db[uids[closest]]).matrix_world
        # self._w_position = m @ self._target.data.vertices[closest].co
        self._w_position = m @ self._target.data.vertices[ii].co
        
        if(add):
            # self._selection_toggle_mask[closest] = True
            self._selection_toggle_mask[ii] = True
        elif(sub):
            # self._selection_toggle_mask[closest] = False
            self._selection_toggle_mask[ii] = False
        else:
            self._selection_toggle_mask[:] = False
            # self._selection_toggle_mask[closest] = True
            self._selection_toggle_mask[ii] = True
        
        # self._w_dots = world_points[self._selection_toggle_mask]
        # NOTE: i broke unused feature, hehe..
        self._w_dots = [self._w_position, ]
        
        # # # DEBUG
        # vs = vs2d.copy()
        # # vs = np.c_[vs[:, 0], vs[:, 1], np.zeros(len(vs), dtype=float, )]
        # # vs = vs.astype(np.float32)
        # # vs[:, 0] = vs[:, 0] / self._context_region.width
        # # vs[:, 1] = vs[:, 1] / self._context_region.height
        # cs = np.ones((len(vs), 4), dtype=np.float32, )
        # cs[:, 0] = 1.0 - (ds / 300)
        # cs[:, 1] = 1.0 - (ds / 300)
        # cs[:, 2] = 1.0 - (ds / 300)
        # cs[closest] = (1, 0, 0, 1)
        # cs = np.clip(cs, 0.0, 1.0, )
        # # debug.points(self._target, vs, None, cs)
        # debug.points_2d(self._context_region, self._context_region_data, self._target, vs, cs, )
        # # # DEBUG
    
    # ------------------------------------------------------------------ action methods >>>
    
    # @verbose
    def _action_begin_private(self, context, event, ):
        if(self._gizmo_mode):
            self._lmb = False
            return
        
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('TIMER', 'BOTH', )):
            bpy.app.timers.register(self._action_timer_private, first_interval=self._action_timer_interval, )
        
        self._action_begin()
    
    # @verbose
    def _action_update_private(self, context, event, ):
        if(self._gizmo_mode):
            self._lmb = False
            return
        
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('MOUSEMOVE', 'BOTH', )):
            self._action_update()
    
    # @verbose
    def _action_finish_private(self, context, event, ):
        if(self._gizmo_mode):
            self._lmb = False
            return
        
        self._action_any_private(context, event, )
        
        self._action_finish()
    
    # ------------------------------------------------------------------ action methods <<<
    
    # @verbose
    def _action_begin(self, ):
        # # NOTE: here is the right spot to do actual brush work
        # loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        # if(loc is not None):
        #     # if(self._ctrl):
        #     #     self._select()
        #     #
        #     #     from .gizmos import SC5GizmoManager
        #     #     if(SC5GizmoManager.group is not None):
        #     #         SC5GizmoManager.group.rebuild()
        #     self._choose()
        
        # if(self._shift):
        #     if(self._shift and self._ctrl):
        #         self._choose(sub=True)
        #     else:
        #         self._choose(add=True)
        # else:
        #     self._choose()
        self._choose()
    
    def _action_update(self, ):
        # # NOTE: here is the right spot to do actual brush work
        # pass
        # # loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        # # if(loc is not None):
        # #     pass
        # loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        # if(loc is not None):
        #     self._choose()
        
        # if(self._shift):
        #     if(self._shift and self._ctrl):
        #         self._choose(sub=True)
        #     else:
        #         self._choose(add=True)
        # else:
        #     self._choose()
        self._choose()
    
    # @verbose
    def _action_finish(self, ):
        # # NOTE: here is the right spot to do actual brush work
        # pass
        # # # push to history..
        # # bpy.ops.ed.undo_push(message=self.bl_label, )
        pass
    
    def _modal(self, context, event, ):
        r = super()._modal(context, event, )
        # return r
        
        # # WATCH: why this was here? it was blocking trackpad. it is from before `_gizmo_mode`, it is redundant now with flag for gizmos enabled/disabled?
        # NOTE: why? to not get stuck in navigating while gizmos are active.. that's why. now check on trackpad+ndof again
        if(self._nav):
            return {'RUNNING_MODAL'}
        
        # # WATCH: and now, why this was here?
        # if(r != {'RUNNING_MODAL'}):
        #     return r
        
        if(not self._gizmo_mode):
            return r
        
        if(event.type != 'TIMER'):
            # NOTE: there is running timer in background. so if event is timer, don't refresh, refresh only on user events
            from .gizmos import SC5GizmoManager
            if(SC5GizmoManager.index > -1):
                self._regenerate()
        
        allow = (
            # 'NONE',
            # manipulating with gizmos.. and navigation
            'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'BUTTON4MOUSE', 'BUTTON5MOUSE', 'BUTTON6MOUSE', 'BUTTON7MOUSE', 'PEN', 'ERASER', 'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE',
            'TRACKPADPAN', 'TRACKPADZOOM', 'MOUSEROTATE', 'MOUSESMARTZOOM', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'WHEELINMOUSE', 'WHEELOUTMOUSE',
            # 'EVT_TWEAK_L','EVT_TWEAK_M','EVT_TWEAK_R','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y',
            # undo..
            'Z',
            # 'ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE',
            # modifiers for gizmos
            'LEFT_CTRL', 'LEFT_ALT', 'LEFT_SHIFT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY',
            # ?
            # 'APP',
            # 'GRLESS',
            # kill all key
            'ESC',
            # 'TAB','RET','SPACE','LINE_FEED','BACK_SPACE','DEL','SEMI_COLON','PERIOD','COMMA','QUOTE','ACCENT_GRAVE',
            # 'MINUS','PLUS',
            # 'SLASH','BACK_SLASH','EQUAL','LEFT_BRACKET','RIGHT_BRACKET','LEFT_ARROW','DOWN_ARROW','RIGHT_ARROW','UP_ARROW',
            # navigation viewport
            'NUMPAD_2', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_8', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_5', 'NUMPAD_7', 'NUMPAD_9', 'NUMPAD_0',
            # 'NUMPAD_PERIOD','NUMPAD_SLASH','NUMPAD_ASTERIX',
            'NUMPAD_MINUS',
            # 'NUMPAD_ENTER',
            'NUMPAD_PLUS',
            # 'F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12','F13','F14','F15','F16','F17','F18','F19','F20','F21','F22','F23','F24',
            # 'PAUSE','INSERT','HOME','PAGE_UP','PAGE_DOWN','END','MEDIA_PLAY','MEDIA_STOP','MEDIA_FIRST','MEDIA_LAST','TEXTINPUT','WINDOW_DEACTIVATE',
            # 'TIMER','TIMER0','TIMER1','TIMER2','TIMER_JOBS','TIMER_AUTOSAVE','TIMER_REPORT','TIMERREGION',
            # ndof device
            'NDOF_MOTION', 'NDOF_BUTTON_MENU', 'NDOF_BUTTON_FIT', 'NDOF_BUTTON_TOP', 'NDOF_BUTTON_BOTTOM', 'NDOF_BUTTON_LEFT', 'NDOF_BUTTON_RIGHT', 'NDOF_BUTTON_FRONT',
            'NDOF_BUTTON_BACK', 'NDOF_BUTTON_ISO1', 'NDOF_BUTTON_ISO2', 'NDOF_BUTTON_ROLL_CW', 'NDOF_BUTTON_ROLL_CCW', 'NDOF_BUTTON_SPIN_CW', 'NDOF_BUTTON_SPIN_CCW',
            'NDOF_BUTTON_TILT_CW', 'NDOF_BUTTON_TILT_CCW', 'NDOF_BUTTON_ROTATE', 'NDOF_BUTTON_PANZOOM', 'NDOF_BUTTON_DOMINANT', 'NDOF_BUTTON_PLUS', 'NDOF_BUTTON_MINUS',
            'NDOF_BUTTON_ESC', 'NDOF_BUTTON_ALT', 'NDOF_BUTTON_SHIFT', 'NDOF_BUTTON_CTRL', 'NDOF_BUTTON_1', 'NDOF_BUTTON_2', 'NDOF_BUTTON_3', 'NDOF_BUTTON_4', 'NDOF_BUTTON_5',
            'NDOF_BUTTON_6', 'NDOF_BUTTON_7', 'NDOF_BUTTON_8', 'NDOF_BUTTON_9', 'NDOF_BUTTON_10', 'NDOF_BUTTON_A', 'NDOF_BUTTON_B', 'NDOF_BUTTON_C',
            # 'ACTIONZONE_AREA','ACTIONZONE_REGION','ACTIONZONE_FULLSCREEN','XR_ACTION',
        )
        
        if(event.type not in allow):
            return {'RUNNING_MODAL'}
        
        # pass through allowed events..
        return {'PASS_THROUGH'}
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_manipulator'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        # NOTE: brush specific props..
        self._lock()
        
        from .gizmos import SC5GizmoManager
        # SC5GizmoManager.surface = s.name
        SC5GizmoManager.surface = None
        SC5GizmoManager.target = self._target.name
        
        # if(len(t.data.vertices) == 0):
        if(len(self._target.data.vertices) == 0):
            SC5GizmoManager.index = -1
        
        self._index = -1
        self._w_position = None
        self._gizmo_mode = False
        
        self._selection_toggle_mask = np.zeros(len(self._target.data.vertices), dtype=bool, )
        self._selection_toggle_ignore = np.zeros(len(self._target.data.vertices), dtype=bool, )
        self._w_dots = []
    
    def _cleanup(self, context, event, ):
        from .gizmos import SC5GizmoManager
        
        try:
            # NOTE: rebuild heere seems redundant and most of the time raises error. on the other hand i added it later dor some reason i don't remember. maybe because it should be prepared (reset) for next use? i think so..
            # NOTE: `print(SC5GizmoManager.group)` returns `<bpy_struct, SC5ManipulatorWidgetGroup invalid>` is there any way to get GizmoGroup valid/invalid status? i don't see any in docs..
            if(SC5GizmoManager.group is not None):
                SC5GizmoManager.group.rebuild()
        except Exception as e:
            pass
        
        SC5GizmoManager.index = -1
        SC5GizmoManager.group = None
        SC5GizmoManager.surface = None
        SC5GizmoManager.target = None
        
        self._unlock()
        
        super()._cleanup(context, event, )
        
        """
        # NOTE: DEBUG >>>
        bpy.ops.wm.tool_set_by_id(name='builtin.select_box')
        # NOTE: DEBUG <<<
        """


# ------------------------------------------------------------------ special brushes <<<


"""
class SCATTER5_OT_manual_brush_tool_manipulator(SCATTER5_OT_common_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_manipulator"
    bl_label = "Manipulator"
    bl_description = "Manipulator"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_manipulator"
    tool_category = 'SPECIAL'
    tool_label = "Manipulator"
    tool_gesture_definitions = {
        '__gesture_primary__': {
            'name': 'Swap Gizmo',
            'function': '_swap_mode',
            'arguments': {},
            'widget': 'FUNCTION_CALL',
        },
    }
    tool_gesture_space = '3D'
    tool_infobox = (
        "• Select: LMB",
        "• Select Add: SHIFT+LMB",
        "• Select Sub: CTRL+SHIFT+LMB",
        "• Mode: SPACE",
    )
    
    tool_widget = "OBJECT_GGT_sc5_manipulator"
    
    icon = "EMPTY_ARROWS"
    dat_icon = "SCATTER5_MANIPULATOR"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    '''
    def _widgets_fabricate_selected_point(self, region, rv3d, pos, woc, ):
        coord = view3d_utils.location_3d_to_region_2d(region, rv3d, pos, )
        ls = tuple()
        if(coord is not None):
            # NOTE: coord is None when outside of view.. so be careful
            ls = (
                # circle
                {
                    'function': 'circle_thick_outline_dashed_2d',
                    'arguments': {
                        'center': coord,
                        'radius': int(self._theme._fixed_radius / 2),
                        'steps': int(self._theme._circle_steps / 2),
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                # dot
                {
                    # 'function': 'dot_shader_2d',
                    'function': 'dot_shader_2_2d',
                    'arguments': {
                        'center': coord,
                        'diameter': self._theme._fixed_center_dot_radius * 2,
                        'color': woc,
                    },
                },
            )
        return ls
    '''
    
    def _widgets_fabricate_multiple_selected_points(self, region, rv3d, vertices, woc, ):
        vs = []
        for pos in vertices:
            coord = view3d_utils.location_3d_to_region_2d(region, rv3d, pos, )
            vs.append(coord)
        
        ls = (
            {
                'function': 'vertices_selection_circles_2d',
                'arguments': {
                    'vertices': vs,
                    # 'c_radius': int(self._theme._fixed_radius / 2),
                    'c_radius': int(self._theme._fixed_radius / 4),
                    'c_steps': int(self._theme._circle_steps / 2),
                    'c_color': woc,
                    'c_thickness': self._theme._outline_thickness,
                    'd_diameter': self._theme._fixed_center_dot_radius * 2,
                    'd_color': woc,
                }
            },
        )
        return ls
    
    def _widgets_fabricate_center(self, region, rv3d, pos, woc, ):
        coord = view3d_utils.location_3d_to_region_2d(region, rv3d, pos, )
        ls = tuple()
        if(coord is not None):
            # NOTE: coord is None when outside of view.. so be careful
            ls = (
                # circle
                {
                    'function': 'circle_thick_outline_dashed_2d',
                    'arguments': {
                        'center': coord,
                        'radius': int(self._theme._fixed_radius / 2),
                        'steps': int(self._theme._circle_steps / 2),
                        'color': woc,
                        'thickness': self._theme._outline_thickness,
                    }
                },
                # dot
                {
                    'function': 'dot_shader_2_2d',
                    'arguments': {
                        'center': coord,
                        'diameter': self._theme._fixed_center_dot_radius * 2,
                        'color': woc,
                    },
                },
            )
        return ls
    
    def _widgets_mouse_idle(self, context, event, ):
        from .gizmos import SC5GizmoManager
        # if(SC5GizmoManager.index != -1):
        if(len(SC5GizmoManager.indices)):
            self._widgets_clear(context, event, )
            return
        
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        
        ls = []
        
        c = self._widgets_fabricate_fixed_size_cross_cursor_and_dot_2d(coord, woc, wfc, )
        ls.extend(c)
        
        # for pos in self._w_dots:
        #     sel = self._widgets_fabricate_selected_point(context.region, context.region_data, pos, self._theme._outline_color_press, )
        #     ls.extend(sel)
        
        sel = self._widgets_fabricate_multiple_selected_points(context.region, context.region_data, self._w_dots, self._theme._outline_color_press, )
        ls.extend(sel)
        
        if(self._w_center is not None):
            sel = self._widgets_fabricate_center(context.region, context.region_data, self._w_center, self._theme._outline_color_press, )
            ls.extend(sel)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_press(self, context, event, ):
        from .gizmos import SC5GizmoManager
        # if(SC5GizmoManager.index != -1):
        if(len(SC5GizmoManager.indices)):
            self._widgets_clear(context, event, )
            return
        
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        
        ls = []
        
        c = self._widgets_fabricate_fixed_size_cross_cursor_and_dot_2d(coord, woc, wfc, )
        ls.extend(c)
        
        # for pos in self._w_dots:
        #     sel = self._widgets_fabricate_selected_point(context.region, context.region_data, pos, self._theme._outline_color_press, )
        #     ls.extend(sel)
        
        sel = self._widgets_fabricate_multiple_selected_points(context.region, context.region_data, self._w_dots, self._theme._outline_color_press, )
        ls.extend(sel)
        
        if(self._w_center is not None):
            sel = self._widgets_fabricate_center(context.region, context.region_data, self._w_center, self._theme._outline_color_press, )
            ls.extend(sel)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    def _modal_shortcuts(self, context, event, ):
        # NOTE: so i can still add some dubug stuff in base class i will then hace everywhere. currently on manipulator defines own `_modal_shortcuts`..
        super()._modal_shortcuts(context, event, )
        
        # NOTE: is called from `_modal`, after all else is handled (apart from exit), any custom keys can be put here..
        if(event.type == 'SPACE' and event.value == 'RELEASE'):
            from .gizmos import SC5GizmoManager
            
            if(self._gizmo_mode):
                self._gizmo_mode = False
                # gizmo is shown, hide
                # SC5GizmoManager.index = -1
                SC5GizmoManager.indices = []
                
                # co = self._target.data.vertices[self._index].co.copy()
                # # co, _ = self._apply_matrix(self._surface.matrix_world, co, )
                # uid = self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[self._index].value
                # co, _ = self._surfaces_to_world_space(co, None, uid, )
                # self._w_position = co
                
                vs = np.zeros(len(self._target.data.vertices) * 3, dtype=float, )
                self._target.data.vertices.foreach_get('co', vs, )
                vs.shape = (-1, 3, )
                local_points = vs.copy()
                uids = np.zeros(len(self._target.data.vertices), dtype=int, )
                self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data.foreach_get('value', uids, )
                vs, _ = self._surfaces_to_world_space(vs, None, uids, )
                world_points = vs.copy()
                
                # self._g_vertices = local_points[self._g_mask]
                self._g_vertices = world_points[self._g_mask]
                self._g_indices = np.arange(len(self._target.data.vertices), dtype=int, )[self._g_mask]
                self._g_uids = uids[self._g_mask]
                self._g_center = world_points[self._g_mask].mean(axis=0, )
                self._w_dots = world_points[self._g_mask]
                self._w_center = self._g_center.copy()
                
                self._widgets_mouse_idle(context, event, )
            else:
                # gizmo is not shown,
                # if(self._index < 0):
                # if(len(self._g_vertices) == 0):
                if(len(self._g_indices) == 0):
                    # nothing selected.. cannot run
                    self._gizmo_mode = False
                    # SC5GizmoManager.index = -1
                    SC5GizmoManager.indices = []
                    
                    self._widgets_mouse_idle(context, event, )
                    return
                else:
                    # something selected, show gizmo
                    self._gizmo_mode = True
                    
                    '''
                    if(SC5GizmoManager.index != self._index):
                        # push to history..
                        bpy.ops.ed.undo_push(message=self.bl_label, )
                        
                        SC5GizmoManager.index = self._index
                        self._flatten(self._index, )
                        
                        # NOTE: in some rare cases (and seems to be connected with higher number of vertices), hidden gizmos were not updated by newly selected vertex, lets call it again here.. it is called on index change anyway.. seems to be fixed, but test it properly, with gizmos you never know..
                        # TODO: check if `group.refresh()` should not be called as well. this time i guess with `SC5GizmoManager.group.refresh(bpy.context, )` to have some effect, like with internal `setup()` call..
                        if(SC5GizmoManager.group is not None):
                            SC5GizmoManager.group.rebuild()
                    '''
                    
                    # push to history..
                    bpy.ops.ed.undo_push(message=self.bl_label, )
                    
                    # SC5GizmoManager.surface = self._surfaces_db[int(self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data[self._index].value)]
                    SC5GizmoManager.surfaces = self._surfaces_db
                    # SC5GizmoManager.index = self._index
                    SC5GizmoManager.indices = self._g_indices
                    # self._flatten(self._index, )
                    
                    for i in self._g_indices:
                        self._flatten(i)
                    
                    # # DEBUG
                    # v = bpy.data.objects.get(SC5GizmoManager.surface).matrix_world @ self._target.data.vertices[SC5GizmoManager.index].co
                    # e = Euler(self._target.data.attributes['manual_private_r_base'].data[SC5GizmoManager.index].vector).to_matrix().to_4x4()
                    # n = e @ Vector((0.0, 0.0, 1.0))
                    # debug.points(self._target, v, n, )
                    # # DEBUG
                    
                    # NOTE: in some rare cases (and seems to be connected with higher number of vertices), hidden gizmos were not updated by newly selected vertex, lets call it again here.. it is called on index change anyway.. seems to be fixed, but test it properly, with gizmos you never know..
                    # TODO: check if `group.refresh()` should not be called as well. this time i guess with `SC5GizmoManager.group.refresh(bpy.context, )` to have some effect, like with internal `setup()` call..
                    if(SC5GizmoManager.group is not None):
                        SC5GizmoManager.group.rebuild()
                        # SC5GizmoManager.group.refresh(context, )
                    
                    self._widgets_clear(context, event, )
    
    def _lock(self, ):
        # NOTE: called on invoke, lock selectability on all objects in scene, store their status in SC5GizmoManager and restore on brush cleanup
        d = {}
        for o in bpy.data.objects:
            d[o.name] = o.hide_select
            o.hide_select = True
        
        from .gizmos import SC5GizmoManager
        SC5GizmoManager.restore = d
    
    def _unlock(self, ):
        # NOTE: have to be called on brush cleanup, use this for manipulator only and use event blocking like in other brushes
        from .gizmos import SC5GizmoManager
        d = SC5GizmoManager.restore
        for k, v in d.items():
            o = bpy.data.objects.get(k)
            if(o is not None):
                o.hide_select = v
        
        SC5GizmoManager.restore = {}
    
    def _swap_mode(self, ):
        if(not self._gizmo_mode):
            return
        
        if(self._get_prop_value('translation')):
            self._set_prop_value('translation', False)
            self._set_prop_value('rotation', True)
            self._set_prop_value('scale', True)
        else:
            self._set_prop_value('translation', True)
            self._set_prop_value('rotation', False)
            self._set_prop_value('scale', False)
    
    def _flatten(self, i, ):
        # DONE: flatten transformation attributes into base rotation and scale, gizmos will work only with these, so flatten all random and extra components into base attribute
        target = self._target
        me = target.data
        
        # rotation
        r = me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector[:]
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector = r
        me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 2
        me.attributes['{}private_r_align_vector'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 1.0]
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 0
        me.attributes['{}private_r_up_vector'.format(self.attribute_prefix)].data[i].vector = [0.0, 1.0, 0.0]
        
        # scale
        s = me.attributes['{}scale'.format(self.attribute_prefix)].data[i].vector[:]
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = s
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data[i].value = 0
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[i].vector = [0.0, 0.0, 0.0]
        
        self._regenerate_scale_from_attributes(np.array([i, ], dtype=int, ), )
        self._regenerate_rotation_from_attributes(np.array([i, ], dtype=int, ), )
    
    def _regenerate_rotation_from_attributes(self, indices, ):
        target = self._target
        me = target.data
        # surface = self._surface
        
        l = len(me.vertices)
        
        _rotation = np.zeros(l * 3, dtype=float, )
        me.attributes['{}rotation'.format(self.attribute_prefix)].data.foreach_get('vector', _rotation, )
        _rotation.shape = (-1, 3)
        
        _private_r_base = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data.foreach_get('vector', _private_r_base, )
        _private_r_base.shape = (-1, 3)
        
        _align_z = np.zeros((l * 3), dtype=float, )
        me.attributes['{}align_z'.format(self.attribute_prefix)].data.foreach_get('vector', _align_z, )
        _align_z.shape = (-1, 3)
        _align_y = np.zeros((l * 3), dtype=float, )
        me.attributes['{}align_y'.format(self.attribute_prefix)].data.foreach_get('vector', _align_y, )
        _align_y.shape = (-1, 3)
        
        # select points to modify by indices
        rotation = _rotation[indices]
        private_r_base = _private_r_base[indices]
        align_z = _align_z[indices]
        align_y = _align_y[indices]
        
        # ---------------------------------------------------------------------
        
        rotation = np.zeros((len(indices), 3), dtype=float, )
        align_z = np.zeros((len(indices), 3), dtype=float, )
        align_y = np.zeros((len(indices), 3), dtype=float, )
        for i in range(len(indices)):
            v = Vector((0.0, 0.0, 1.0))
            v.rotate(Euler(private_r_base[i]))
            align_z[i] = v.to_tuple()
            
            v = Vector((0.0, 1.0, 0.0))
            v.rotate(Euler(private_r_base[i]))
            align_y[i] = v.to_tuple()
            
            rotation[i] = private_r_base[i]
        
        _rotation[indices] = rotation
        me.attributes['{}rotation'.format(self.attribute_prefix)].data.foreach_set('vector', _rotation.flatten(), )
        _align_z[indices] = align_z
        me.attributes['{}align_z'.format(self.attribute_prefix)].data.foreach_set('vector', _align_z.flatten(), )
        _align_y[indices] = align_y
        me.attributes['{}align_y'.format(self.attribute_prefix)].data.foreach_set('vector', _align_y.flatten(), )
    
    def _regenerate_scale_from_attributes(self, indices, ):
        target = self._target
        me = target.data
        # surface = self._surface
        
        l = len(me.vertices)
        
        # get all..
        _scale = np.zeros(l * 3, dtype=float, )
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_get('vector', _scale, )
        _scale.shape = (-1, 3)
        
        _private_s_base = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_base, )
        _private_s_base.shape = (-1, 3)
        
        _private_s_random = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_random, )
        _private_s_random.shape = (-1, 3)
        
        _private_s_random_random = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_random_random, )
        _private_s_random_random.shape = (-1, 3)
        
        _private_s_random_type = np.zeros(l, dtype=int, )
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data.foreach_get('value', _private_s_random_type, )
        
        _private_s_change = np.zeros(l * 3, dtype=float, )
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data.foreach_get('vector', _private_s_change, )
        _private_s_change.shape = (-1, 3)
        
        # slice by indices..
        scale = _scale[indices]
        private_s_base = _private_s_base[indices]
        private_s_random = _private_s_random[indices]
        private_s_random_random = _private_s_random_random[indices]
        private_s_random_type = _private_s_random_type[indices]
        private_s_change = _private_s_change[indices]
        
        # calculate..
        l = len(indices)
        for i in range(l):
            d = private_s_base[i]
            r = private_s_random[i]
            rr = private_s_random_random[i]
            
            if(private_s_random_type[i] == 0):
                # 'UNIFORM'
                f = rr[0]
                fn = 1.0 - f
                dr = d * r
                s = (d * fn) + (dr * f)
            elif(private_s_random_type[i] == 1):
                # 'VECTORIAL'
                f = r + (1.0 - r) * rr
                s = d * f
            
            s = s + private_s_change[i]
            
            scale[i] = s
        
        # and set back to attribute..
        _scale[indices] = scale
        me.attributes['{}scale'.format(self.attribute_prefix)].data.foreach_set('vector', _scale.flatten(), )
    
    # @verbose
    def _regenerate(self, ):
        from .gizmos import SC5GizmoManager
        # self._regenerate_scale_from_attributes(np.array([SC5GizmoManager.index, ], dtype=int, ), )
        self._regenerate_scale_from_attributes(np.array(SC5GizmoManager.indices, dtype=int, ), )
        # self._regenerate_rotation_from_attributes(np.array([SC5GizmoManager.index, ], dtype=int, ), )
        self._regenerate_rotation_from_attributes(np.array(SC5GizmoManager.indices, dtype=int, ), )
    
    # TODO: there will be a bit better performance if i cache 2d points until view is moved (not easy to know if it is or not). or at least cache vertices from mesh until mode is swapped (after that i can expect modifications..)
    @verbose
    def _choose(self, add=False, sub=False, ):
        if(not len(self._target.data.vertices)):
            return
        
        # get target vertices
        vs = np.zeros(len(self._target.data.vertices) * 3, dtype=float, )
        self._target.data.vertices.foreach_get('co', vs, )
        vs.shape = (-1, 3, )
        local_points = vs.copy()
        
        # transform to screen space
        # model = np.array(self._surface.matrix_world, dtype=float, )
        uids = np.zeros(len(self._target.data.vertices), dtype=int, )
        self._target.data.attributes['{}surface_uuid'.format(self.attribute_prefix)].data.foreach_get('value', uids, )
        vs, _ = self._surfaces_to_world_space(vs, None, uids, )
        world_points = vs.copy()
        
        view = np.array(self._context_region_data.view_matrix, dtype=float, )
        projection = np.array(self._context_region_data.window_matrix, dtype=float, )
        
        vs = np.c_[vs, np.ones(len(vs), dtype=vs.dtype, )]
        # vs = np.dot(model, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(view, vs.T)[0:4].T.reshape((-1, 4))
        vs = np.dot(projection, vs.T)[0:4].T.reshape((-1, 4))
        
        x = vs[:, 0]
        y = vs[:, 1]
        z = vs[:, 1]
        w = vs[:, 3]
        x_ndc = x / w
        y_ndc = y / w
        z_ndc = z / w
        
        x2d = (x_ndc + 1.0) / 2.0
        y2d = (y_ndc + 1.0) / 2.0
        # z2d = (z_ndc + 1.0) / 2.0
        
        # # NOTE: do i need some depth? lets go with zeros for now
        # z = np.zeros(len(vs), dtype=float, )
        # vs2d = np.c_[x2d, y2d, z]
        # vs2d = np.c_[x2d, y2d, z2d]
        vs2d = np.c_[x2d, y2d, ]
        # # and normalize path from pixels to 0.0-1.0
        # vertices2d = np.zeros((len(vertices), 2), dtype=float, )
        # vertices2d[:, 0] = vertices[:, 0] * (1.0 / self._context_region.width)
        # vertices2d[:, 1] = vertices[:, 1] * (1.0 / self._context_region.height)
        # to pixel coordinates
        vs2d[:, 0] = vs2d[:, 0] * self._context_region.width
        vs2d[:, 1] = vs2d[:, 1] * self._context_region.height
        
        # x, y are in pixels, z is normalized 0-1, so put mouse at z 1.0 to select by depth as well
        # point = Vector((self._mouse_2d_region.x, self._mouse_2d_region.y, 1.0, ))
        point = self._mouse_2d_region
        
        # # 3d
        # ds = ((vs2d[:, 0] - point[0]) ** 2 + (vs2d[:, 1] - point[1]) ** 2 + (vs2d[:, 2] - point[2]) ** 2) ** 0.5
        # 2d
        ds = ((vs2d[:, 0] - point[0]) ** 2 + (vs2d[:, 1] - point[1]) ** 2) ** 0.5
        
        closest = np.argmin(ds, )
        # self._index = closest
        
        # # self._w_position = self._surface.matrix_world @ self._target.data.vertices[closest].co
        # m = bpy.data.objects.get(self._surfaces_db[uids[closest]]).matrix_world
        # self._w_position = m @ self._target.data.vertices[closest].co
        
        if(add):
            self._g_mask[closest] = True
        elif(sub):
            self._g_mask[closest] = False
        else:
            self._g_mask[:] = False
            self._g_mask[closest] = True
        
        # self._g_vertices = local_points[self._g_mask]
        self._g_vertices = world_points[self._g_mask]
        self._g_indices = np.arange(len(self._target.data.vertices), dtype=int, )[self._g_mask]
        self._g_uids = uids[self._g_mask]
        self._g_center = world_points[self._g_mask].mean(axis=0, )
        
        self._w_dots = world_points[self._g_mask]
        self._w_center = self._g_center.copy()
        
        # # # DEBUG
        # vs = vs2d.copy()
        # # vs = np.c_[vs[:, 0], vs[:, 1], np.zeros(len(vs), dtype=float, )]
        # # vs = vs.astype(np.float32)
        # # vs[:, 0] = vs[:, 0] / self._context_region.width
        # # vs[:, 1] = vs[:, 1] / self._context_region.height
        # cs = np.ones((len(vs), 4), dtype=np.float32, )
        # cs[:, 0] = 1.0 - (ds / 300)
        # cs[:, 1] = 1.0 - (ds / 300)
        # cs[:, 2] = 1.0 - (ds / 300)
        # cs[closest] = (1, 0, 0, 1)
        # cs = np.clip(cs, 0.0, 1.0, )
        # # debug.points(self._target, vs, None, cs)
        # debug.points_2d(self._context_region, self._context_region_data, self._target, vs, cs, )
        # # # DEBUG
    
    # ------------------------------------------------------------------ action methods >>>
    
    # @verbose
    def _action_begin_private(self, context, event, ):
        if(self._gizmo_mode):
            self._lmb = False
            return
        
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('TIMER', 'BOTH', )):
            bpy.app.timers.register(self._action_timer_private, first_interval=self._action_timer_interval, )
        
        self._action_begin()
    
    # @verbose
    def _action_update_private(self, context, event, ):
        if(self._gizmo_mode):
            self._lmb = False
            return
        
        self._action_any_private(context, event, )
        
        if(self._action_execute_on in ('MOUSEMOVE', 'BOTH', )):
            self._action_update()
    
    # @verbose
    def _action_finish_private(self, context, event, ):
        if(self._gizmo_mode):
            self._lmb = False
            return
        
        self._action_any_private(context, event, )
        
        self._action_finish()
    
    # ------------------------------------------------------------------ action methods <<<
    
    # @verbose
    def _action_begin(self, ):
        if(self._shift):
            if(self._shift and self._ctrl):
                self._choose(sub=True)
            else:
                self._choose(add=True)
        else:
            self._choose()
    
    def _action_update(self, ):
        if(self._shift):
            if(self._shift and self._ctrl):
                self._choose(sub=True)
            else:
                self._choose(add=True)
        else:
            self._choose()
    
    # @verbose
    def _action_finish(self, ):
        # # NOTE: here is the right spot to do actual brush work
        # pass
        # # # push to history..
        # # bpy.ops.ed.undo_push(message=self.bl_label, )
        pass
    
    def _modal(self, context, event, ):
        r = super()._modal(context, event, )
        # return r
        
        # # WATCH: why this was here? it was blocking trackpad. it is from before `_gizmo_mode`, it is redundant now with flag for gizmos enabled/disabled?
        # NOTE: why? to not get stuck in navigating while gizmos are active.. that's why. now check on trackpad+ndof again
        if(self._nav):
            return {'RUNNING_MODAL'}
        
        # # WATCH: and now, why this was here?
        # if(r != {'RUNNING_MODAL'}):
        #     return r
        
        if(not self._gizmo_mode):
            return r
        
        if(event.type != 'TIMER'):
            # NOTE: there is running timer in background. so if event is timer, don't refresh, refresh only on user events
            from .gizmos import SC5GizmoManager
            # if(SC5GizmoManager.index > -1):
            if(len(SC5GizmoManager.indices)):
                self._regenerate()
        
        allow = (
            # 'NONE',
            # manipulating with gizmos.. and navigation
            'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'BUTTON4MOUSE', 'BUTTON5MOUSE', 'BUTTON6MOUSE', 'BUTTON7MOUSE', 'PEN', 'ERASER', 'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE',
            'TRACKPADPAN', 'TRACKPADZOOM', 'MOUSEROTATE', 'MOUSESMARTZOOM', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'WHEELINMOUSE', 'WHEELOUTMOUSE',
            # 'EVT_TWEAK_L','EVT_TWEAK_M','EVT_TWEAK_R','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y',
            # undo..
            'Z',
            # 'ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE',
            # modifiers for gizmos
            'LEFT_CTRL', 'LEFT_ALT', 'LEFT_SHIFT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY',
            # ?
            # 'APP',
            # 'GRLESS',
            # kill all key
            'ESC',
            # 'TAB','RET','SPACE','LINE_FEED','BACK_SPACE','DEL','SEMI_COLON','PERIOD','COMMA','QUOTE','ACCENT_GRAVE',
            # 'MINUS','PLUS',
            # 'SLASH','BACK_SLASH','EQUAL','LEFT_BRACKET','RIGHT_BRACKET','LEFT_ARROW','DOWN_ARROW','RIGHT_ARROW','UP_ARROW',
            # navigation viewport
            'NUMPAD_2', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_8', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_5', 'NUMPAD_7', 'NUMPAD_9', 'NUMPAD_0',
            # 'NUMPAD_PERIOD','NUMPAD_SLASH','NUMPAD_ASTERIX',
            'NUMPAD_MINUS',
            # 'NUMPAD_ENTER',
            'NUMPAD_PLUS',
            # 'F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12','F13','F14','F15','F16','F17','F18','F19','F20','F21','F22','F23','F24',
            # 'PAUSE','INSERT','HOME','PAGE_UP','PAGE_DOWN','END','MEDIA_PLAY','MEDIA_STOP','MEDIA_FIRST','MEDIA_LAST','TEXTINPUT','WINDOW_DEACTIVATE',
            # 'TIMER','TIMER0','TIMER1','TIMER2','TIMER_JOBS','TIMER_AUTOSAVE','TIMER_REPORT','TIMERREGION',
            # ndof device
            'NDOF_MOTION', 'NDOF_BUTTON_MENU', 'NDOF_BUTTON_FIT', 'NDOF_BUTTON_TOP', 'NDOF_BUTTON_BOTTOM', 'NDOF_BUTTON_LEFT', 'NDOF_BUTTON_RIGHT', 'NDOF_BUTTON_FRONT',
            'NDOF_BUTTON_BACK', 'NDOF_BUTTON_ISO1', 'NDOF_BUTTON_ISO2', 'NDOF_BUTTON_ROLL_CW', 'NDOF_BUTTON_ROLL_CCW', 'NDOF_BUTTON_SPIN_CW', 'NDOF_BUTTON_SPIN_CCW',
            'NDOF_BUTTON_TILT_CW', 'NDOF_BUTTON_TILT_CCW', 'NDOF_BUTTON_ROTATE', 'NDOF_BUTTON_PANZOOM', 'NDOF_BUTTON_DOMINANT', 'NDOF_BUTTON_PLUS', 'NDOF_BUTTON_MINUS',
            'NDOF_BUTTON_ESC', 'NDOF_BUTTON_ALT', 'NDOF_BUTTON_SHIFT', 'NDOF_BUTTON_CTRL', 'NDOF_BUTTON_1', 'NDOF_BUTTON_2', 'NDOF_BUTTON_3', 'NDOF_BUTTON_4', 'NDOF_BUTTON_5',
            'NDOF_BUTTON_6', 'NDOF_BUTTON_7', 'NDOF_BUTTON_8', 'NDOF_BUTTON_9', 'NDOF_BUTTON_10', 'NDOF_BUTTON_A', 'NDOF_BUTTON_B', 'NDOF_BUTTON_C',
            # 'ACTIONZONE_AREA','ACTIONZONE_REGION','ACTIONZONE_FULLSCREEN','XR_ACTION',
        )
        
        if(event.type not in allow):
            return {'RUNNING_MODAL'}
        
        # pass through allowed events..
        return {'PASS_THROUGH'}
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_manipulator'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        # NOTE: brush specific props..
        self._lock()
        
        from .gizmos import SC5GizmoManager
        # SC5GizmoManager.surface = s.name
        # SC5GizmoManager.surface = None
        SC5GizmoManager.surfaces = self._surfaces_db
        SC5GizmoManager.target = self._target.name
        
        # if(len(t.data.vertices) == 0):
        if(len(self._target.data.vertices) == 0):
            # SC5GizmoManager.index = -1
            SC5GizmoManager.indices = []
        
        # self._index = -1
        
        # self._w_position = None
        self._gizmo_mode = False
        
        self._g_mask = np.zeros(len(self._target.data.vertices), dtype=bool, )
        self._g_vertices = []
        self._g_indices = []
        self._g_uids = []
        self._g_center = None
        
        self._w_dots = []
        self._w_center = None
    
    def _cleanup(self, context, event, ):
        from .gizmos import SC5GizmoManager
        
        try:
            # NOTE: rebuild heere seems redundant and most of the time raises error. on the other hand i added it later dor some reason i don't remember. maybe because it should be prepared (reset) for next use? i think so..
            # NOTE: `print(SC5GizmoManager.group)` returns `<bpy_struct, SC5ManipulatorWidgetGroup invalid>` is there any way to get GizmoGroup valid/invalid status? i don't see any in docs..
            if(SC5GizmoManager.group is not None):
                SC5GizmoManager.group.rebuild()
        except Exception as e:
            pass
        
        # SC5GizmoManager.index = -1
        # SC5GizmoManager.group = None
        # SC5GizmoManager.surface = None
        # SC5GizmoManager.target = None
        SC5GizmoManager.clear()
        
        self._unlock()
        
        super()._cleanup(context, event, )
"""


# ------------------------------------------------------------------ debug brushes >>>


class SCATTER5_OT_manual_brush_tool_debug_3d(SCATTER5_OT_common_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_debug_3d"
    bl_label = "debug 3d"
    bl_description = "debug 3d"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_debug_3d"
    tool_category = 'SPECIAL'
    tool_label = "debug 3d"
    
    tool_gesture_definitions = {}
    tool_gesture_space = None
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: legacy brush code
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    '''
    # @verbose
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            # DEBUG
            coord = (event.mouse_region_x, event.mouse_region_y, )
            
            # f = self._theme._fixed_radius
            # w = f * 2
            # h = f
            # r = f / 2
            #
            # txls = [
            #     "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed",
            #     "do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            #     "Ut enim ad minim veniam, quis nostrud exercitation ullamco",
            #     "laboris nisi ut aliquip ex ea commodo consequat. Duis aute",
            #     "irure dolor in reprehenderit in voluptate velit esse cillum",
            #     "dolore eu fugiat nulla pariatur. Excepteur sint occaecat",
            #     "cupidatat non proident, sunt in culpa qui officia deserunt",
            #     "mollit anim id est laborum.",
            # ]
            
            
            s = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_center_dot_radius, )
            # NOTE: it needs diameter
            s = s * 2
            ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
            mt = Matrix.Translation(loc + Vector((0.0, 0.0, 0.5)))
            m = mt @ mr @ ms
            
            mt = Matrix.Translation(loc + Vector((0.0, 0.0, 1.0)))
            m2 = mt @ mr @ ms
            
            mt = Matrix.Translation(loc + Vector((0.0, 0.0, 1.5)))
            m3 = mt @ mr @ ms
            
            test = (
                {
                    'function': 'dot_shader_3d',
                    'arguments': {
                        'matrix': m,
                        'color': woc,
                        'bias': 0.1,
                    }
                },
                {
                    'function': 'dot_shader_3d',
                    'arguments': {
                        'matrix': m2,
                        'color': woc,
                        'bias': 0.01,
                    }
                },
                {
                    'function': 'dot_shader_3d',
                    'arguments': {
                        'matrix': m3,
                        'color': woc,
                        'bias': 0.001,
                    }
                },
                
                # {
                #     'function': 'label_2d',
                #     'arguments': {
                #         'coords': coord,
                #         'text': 'Lorem ipsum dolor sit amet.',
                #         'offset': (11 * self._theme._ui_scale, 11 * self._theme._ui_scale, ),
                #         'size': self._theme._text_size,
                #         'color': self._theme._text_color,
                #         'shadow': True,
                #     }
                # },
                # {
                #     'function': 'tooltip_2d',
                #     'arguments': {
                #         'coords': coord,
                #         'text': 'Lorem ipsum dolor sit amet.',
                #         'offset': (11 * self._theme._ui_scale, 11 * self._theme._ui_scale, ),
                #         'size': self._theme._text_size,
                #         'color': self._theme._text_color,
                #         'shadow': True,
                #         'padding': 5 * self._theme._ui_scale,
                #         'bgfill': self._theme._text_tooltip_background_color,
                #         'bgoutline': self._theme._text_tooltip_outline_color,
                #         'thickness': self._theme._text_tooltip_outline_thickness,
                #     }
                # },
                # {
                #     'function': 'fancy_switch_2d',
                #     'arguments': {
                #         'coords': coord,
                #         'state': True,
                #         'dimensions': (w, h),
                #         # 'offset': self._theme._text_tooltip_offset,
                #         # 'offset': (0, h / 2),
                #         'offset': (0, 0, ),
                #         'align': 'CENTER',
                #         'steps': self._theme._circle_steps,
                #         'radius': r,
                #         'bgfill': self._theme._text_tooltip_background_color,
                #         'bgoutline': self._theme._text_tooltip_outline_color,
                #         'thickness': self._theme._text_tooltip_outline_thickness,
                #     }
                # },
                # {
                #     'function': 'fancy_tooltip_2d',
                #     'arguments': {
                #         'coords': coord,
                #         'text': 'Lorem ipsum dolor sit amet.',
                #         # 'offset': self._theme._text_tooltip_offset,
                #         'offset': (0, (f / 2) + 8 * self._theme._ui_scale + 4 * self._theme._ui_scale + 1 * self._theme._ui_scale, ),
                #         'align': 'CENTER',
                #         'size': self._theme._text_size,
                #         'color': self._theme._text_color,
                #         'shadow': True,
                #         'padding': 8 * self._theme._ui_scale,
                #         'steps': self._theme._circle_steps,
                #         'radius': 4 * self._theme._ui_scale,
                #         'bgfill': self._theme._text_tooltip_background_color,
                #         'bgoutline': self._theme._text_tooltip_outline_color,
                #         'thickness': self._theme._text_tooltip_outline_thickness,
                #     }
                # },
                # {
                #     'function': 'label_multiline_left_flag_2d',
                #     'arguments': {
                #         'coords': coord,
                #         'lines': txls,
                #         'offset': (0, 0),
                #         'size': self._theme._text_size,
                #         'color': self._theme._text_color,
                #         'shadow': True,
                #         'padding': 5 * self._theme._ui_scale,
                #     }
                # },
            )
            ls.extend(test)
            # DEBUG
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    '''
    
    # @verbose
    def _widgets_mouse_idle(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color
            wfc = self._theme._fill_color
            
            '''
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            t = []
            t.append('circle: ')
            t.append('r: {}'.format(self._theme._fixed_radius))
            t.append('loc: {}'.format(repr(loc)))
            t.append('s: {}'.format(radius))
            a = repr(ms)
            als = a.split('\n')
            for i in als:
                t.append("ms: {}".format(i))
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            # dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            # ls.extend(dot)
            
            t.append('dot: ')
            t.append("r: {}".format(self._theme._fixed_center_dot_radius))
            t.append("loc: {}".format(repr(loc)))
            
            s = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_center_dot_radius, )
            t.append("s: {}".format(s))
            # NOTE: it needs diameter
            s = s * 2
            t.append("d: {}".format(s))
            ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
            m = mt @ mr @ ms
            
            a = repr(ms)
            als = a.split('\n')
            for i in als:
                t.append("ms: {}".format(i))
            
            info = (
                # cursor dot
                {
                    'function': 'dot_shader_3d',
                    'arguments': {
                        'matrix': m,
                        'color': woc,
                    }
                },
                {
                    'function': 'label_multiline_left_flag_2d',
                    'arguments': {
                        'coords': (event.mouse_region_x, event.mouse_region_y, ),
                        'lines': t,
                        'offset': (50, 0),
                        'size': self._theme._text_size,
                        'color': self._theme._text_color,
                        'shadow': True,
                        'padding': 5 * self._theme._ui_scale,
                    }
                },
            )
            ls.extend(info)
            
            # -------------------------------------
            
            r = self._theme._fixed_center_dot_radius * 2
            s = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, r, )
            ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
            d = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, 50, )
            o = Vector((0.0, 0.0, d))
            mt = Matrix.Translation(loc + o)
            m = mt @ mr @ ms
            
            t = [
                "dot_shader_2_3d:",
                "r: {}".format(self._theme._fixed_center_dot_radius),
                "r*2: {}".format(r),
                "s: {}".format(s),
            ]
            dot2 = (
                # cursor dot
                {
                    'function': 'dot_shader_2_3d',
                    'arguments': {
                        'matrix': m,
                        'scale_factor': s,
                        'color': woc,
                    }
                },
                # {
                #     'function': 'label_2d',
                #     'arguments': {
                #         'coords': (event.mouse_region_x, event.mouse_region_y, ),
                #         'text': "dot_shader_2_3d",
                #         'offset': (50, 50),
                #         'size': self._theme._text_size,
                #         'color': self._theme._text_color,
                #         'shadow': True,
                #     }
                # },
                {
                    'function': 'label_multiline_left_flag_2d',
                    'arguments': {
                        'coords': (event.mouse_region_x, event.mouse_region_y, ),
                        'lines': t,
                        'offset': (50, 100),
                        'size': self._theme._text_size,
                        'color': self._theme._text_color,
                        'shadow': True,
                        'padding': 5 * self._theme._ui_scale,
                    }
                },
            )
            ls.extend(dot2)
            '''
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            # dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            # ls.extend(dot)
            
            r = self._theme._fixed_center_dot_radius * 2
            s = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, r, )
            mr = self._widgets_compute_billboard_rotation_matrix(context.region, context.region_data, )
            ms = self._widgets_compute_surface_matrix_scale_component_3d(s, )
            m = mt @ mr @ ms
            
            w = context.region.width
            h = context.region.height
            c = Vector((w / 2, h / 2, ))
            a = c - Vector((r / 2, 0.0))
            b = c + Vector((r / 2, 0.0))
            a3 = view3d_utils.region_2d_to_location_3d(context.region, context.region_data, a, loc)
            b3 = view3d_utils.region_2d_to_location_3d(context.region, context.region_data, b, loc)
            d = ((a3.x - b3.x) ** 2 + (a3.y - b3.y) ** 2 + (a3.z - b3.z) ** 2) ** 0.5
            
            dot2 = (
                {
                    'function': 'dot_shader_2_3d',
                    'arguments': {
                        'matrix': m,
                        'scale_factor': s,
                        'color': woc,
                    }
                },
                {
                    'function': 'label_multiline_left_flag_2d',
                    'arguments': {
                        'coords': (event.mouse_region_x + 50, event.mouse_region_y, ),
                        'lines': [
                            "dot_shader_2_3d + billboard matrix",
                            "r: {}".format(r),
                            "s: {}".format(s),
                            "-" * 50,
                            "loc: {}".format(loc),
                            "w: {}, h: {}".format(w, h),
                            "c: {}".format(c),
                            "a: {}".format(a),
                            "b: {}".format(b),
                            "a3: {}".format(a3),
                            "b3: {}".format(b3),
                            "d: {}".format(d),
                        ],
                        'offset': (0, 0),
                        'size': self._theme._text_size,
                        'color': self._theme._text_color,
                        'shadow': True,
                        'padding': 5 * self._theme._ui_scale,
                    }
                },
            )
            ls.extend(dot2)
            
            # r = self._theme._fixed_center_dot_radius * 2
            # dot2d = (
            #     {
            #         'function': 'dot_shader_2_2d',
            #         'arguments': {
            #             'center': (event.mouse_region_x, event.mouse_region_y + 50, ),
            #             'diameter': r,
            #             'color': woc,
            #         },
            #     },
            # )
            # ls.extend(dot2d)
            
            # DEBUG: mouse direction interpolation
            ls.extend([
                {
                    'function': 'thick_line_2d',
                    'arguments': {
                        'a': Vector((event.mouse_region_x, event.mouse_region_y)),
                        'b': Vector((event.mouse_region_x, event.mouse_region_y)) + (self._mouse_2d_direction_interpolated * 100),
                        'color': (1.0, 0.0, 0.0, 1.0),
                        'thickness': 3.0,
                    }
                },
                {
                    'function': 'thick_line_2d',
                    'arguments': {
                        'a': Vector((event.mouse_region_x, event.mouse_region_y)),
                        'b': Vector((event.mouse_region_x, event.mouse_region_y)) + (self._mouse_2d_direction * 100),
                        'color': (1.0, 0.0, 0.0, 0.5),
                        'thickness': 1.0,
                    }
                },
            ])
            if(self._mouse_3d_direction_interpolated is not None and self._mouse_3d_direction is not None):
                radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, 100, )
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
                # m = mt @ mr @ ms
                # NOTE: so i see real vector
                m = mt @ ms
                ls.extend([
                    {
                        'function': 'thick_line_3d',
                        'arguments': {
                            'a': Vector((0.0, 0.0, 0.0, )),
                            'b': Vector((0.0, 0.0, 0.0, )) + (self._mouse_3d_direction_interpolated * 1.0),
                            'matrix': m,
                            'color': (0.0, 1.0, 0.0, 1.0),
                            'thickness': 3.0,
                        }
                    },
                    {
                        'function': 'thick_line_3d',
                        'arguments': {
                            'a': Vector((0.0, 0.0, 0.0, )),
                            'b': Vector((0.0, 0.0, 0.0, )) + (self._mouse_3d_direction * 1.0),
                            'matrix': m,
                            'color': (0.0, 1.0, 0.0, 0.5),
                            'thickness': 1.0,
                        }
                    },
                ])
            # DEBUG: mouse direction interpolation
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            # DEBUG: mouse direction interpolation
            ls.extend([
                {
                    'function': 'thick_line_2d',
                    'arguments': {
                        'a': Vector((event.mouse_region_x, event.mouse_region_y)),
                        'b': Vector((event.mouse_region_x, event.mouse_region_y)) + (self._mouse_2d_direction_interpolated * 100),
                        'color': (1.0, 0.0, 0.0, 1.0),
                        'thickness': 3.0,
                    }
                },
                {
                    'function': 'thick_line_2d',
                    'arguments': {
                        'a': Vector((event.mouse_region_x, event.mouse_region_y)),
                        'b': Vector((event.mouse_region_x, event.mouse_region_y)) + (self._mouse_2d_direction * 100),
                        'color': (1.0, 0.0, 0.0, 0.5),
                        'thickness': 1.0,
                    }
                },
            ])
            '''
            if(self._mouse_3d_direction_interpolated is not None and self._mouse_3d_direction is not None):
                radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, 100, )
                mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
                # m = mt @ mr @ ms
                # NOTE: so i see real vector
                m = mt @ ms
                ls.extend([
                    {
                        'function': 'thick_line_3d',
                        'arguments': {
                            'a': Vector((0.0, 0.0, 0.0, )),
                            'b': Vector((0.0, 0.0, 0.0, )) + (self._mouse_3d_direction_interpolated * 1.0),
                            'matrix': m,
                            'color': (0.0, 1.0, 0.0, 1.0),
                            'thickness': 3.0,
                        }
                    },
                    {
                        'function': 'thick_line_3d',
                        'arguments': {
                            'a': Vector((0.0, 0.0, 0.0, )),
                            'b': Vector((0.0, 0.0, 0.0, )) + (self._mouse_3d_direction * 1.0),
                            'matrix': m,
                            'color': (0.0, 1.0, 0.0, 0.5),
                            'thickness': 1.0,
                        }
                    },
                ])
            '''
            # DEBUG: mouse direction interpolation
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_press(self, context, event, ):
        loc, nor, idx, dst = self._project_mouse_to_surface(context, event, )
        if(loc is not None):
            woc = self._theme._outline_color_press
            wfc = self._theme._fill_color_press
            
            radius = self._widgets_compute_fixed_scale_3d(context.region, context.region_data, loc, self._theme._fixed_radius, )
            mt, mr, ms = self._widgets_compute_surface_matrix_components_3d(loc, nor, radius, )
            
            ls = []
            
            c = self._widgets_fabricate_fixed_size_cross_cursor_3d(mt, mr, ms, radius, woc, wfc, )
            ls.extend(c)
            
            dot = self._widgets_fabricate_center_dot_3d(context.region, context.region_data, loc, mt, mr, woc, )
            ls.extend(dot)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = ls
            ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        else:
            ls = []
            sign = self._widgets_fabricate_no_entry_sign(event, )
            ls.extend(sign)
            
            ToolWidgets._cache[self.tool_id]['screen_components'] = []
            ToolWidgets._cache[self.tool_id]['cursor_components'] = ls
        
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    # @verbose
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        pass
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    @verbose
    def _action_begin(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            pass
    
    def _action_update(self, ):
        loc, nor = self._mouse_3d_loc, self._mouse_3d_nor
        if(loc is not None):
            pass
    
    @verbose
    def _action_finish(self, ):
        pass
    
    def _invoke(self, context, event, ):
        # NOTE: set brush props name before `super()._invoke` so it can get correct reference
        # NOTE: with name identification i can handle getting reference after undo/redo automatically, no need for special fuction in subclasses.. which is good!
        self._brush_props_name = 'tool_default'
        # NOTE: super!
        super()._invoke(context, event, )
        
        # NOTE: overrides..
        # self._cursor_modal_set = 'DOT'
        
        # NOTE: brush specific props..


class SCATTER5_OT_manual_brush_tool_debug_errors(SCATTER5_OT_common_mixin, SCATTER5_OT_create_mixin, SCATTER5_OT_modify_mixin, SCATTER5_OT_manual_brush_tool_base, ):
    bl_idname = "scatter5.manual_brush_tool_debug_errors"
    bl_label = "debug errors"
    bl_description = "debug errors"
    bl_options = {'INTERNAL', }
    
    tool_id = "scatter5.manual_brush_tool_debug_errors"
    tool_category = 'SPECIAL'
    tool_label = "debug errors"
    
    tool_gesture_definitions = {}
    tool_gesture_space = None
    tool_infobox = (
        "• Draw: LMB",
    )
    
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: widgets
    
    # @verbose
    def _widgets_mouse_idle(self, context, event, ):
        woc = self._theme._outline_color
        wfc = self._theme._fill_color
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        ls = [
            {
                'function': 'dot_shader_2_2d',
                'arguments': {
                    'center': coord,
                    'diameter': self._theme._fixed_center_dot_radius * 2,
                    'color': woc,
                },
            },
        ]
        tooltip = self._widgets_fabricate_tooltip(coord, "uncomment exception raising where needed", )
        ls.extend(tooltip)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_press(self, context, event, ):
        woc = self._theme._outline_color_press
        wfc = self._theme._fill_color_press
        
        coord = (event.mouse_region_x, event.mouse_region_y, )
        ls = [
            {
                'function': 'dot_shader_2_2d',
                'arguments': {
                    'center': coord,
                    'diameter': self._theme._fixed_center_dot_radius * 2,
                    'color': woc,
                },
            },
        ]
        tooltip = self._widgets_fabricate_tooltip(coord, "uncomment exception raising where needed", )
        ls.extend(tooltip)
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._cache[self.tool_id]['cursor_components'] = []
        
        ToolWidgets._tag_redraw()
    
    # @verbose
    def _widgets_mouse_move(self, context, event, ):
        self._widgets_mouse_press(context, event, )
    
    # @verbose
    def _widgets_mouse_release(self, context, event, ):
        self._widgets_mouse_idle(context, event, )
    
    # @verbose
    def _widgets_modifiers_change(self, context, event, ):
        # NOTE: tool with modifier key function change, i need to redraw on modifiers change
        pass
    
    # ---------------------------------------------------------------------------------------------------
    # NOTE: actual brush code.. without integration bit (ui rebuild) for now..
    
    '''
    def _action_begin_private(self, context, event, ):
        super()._action_begin_private(context, event, )
    
    def _update_references_and_settings(self, context, event, ):
        super()._update_references_and_settings(context, event, )
    
    def _modify(self, ):
        pass
    
    def _execute(self, ):
        self._modify()
        
        if(not hasattr(self, '_counter')):
            self._counter = 0
        else:
            self._counter += 1
        if(self._counter >= 10):
            self._counter = 0
            raise Exception("!")
        else:
            print(".")
        
        super()._execute()
    '''
    
    @verbose
    def _action_begin(self, ):
        # NOTE: ok, reset
        # raise Exception("!")
        
        # NOTE: ok, report, do not panic or blender will crash
        # self._execute()
        
        pass
    
    def _action_update(self, ):
        # NOTE: ok, reset
        # raise Exception("!")
        
        # NOTE: ok, report, do not panic or blender will crash
        # self._execute()
        
        pass
    
    @verbose
    def _action_finish(self, ):
        # NOTE: ok, reset
        # raise Exception("!")
        pass
    
    def _modal(self, context, event, ):
        # NOTE: ok, reset
        # raise Exception("!")
        
        r = super()._modal(context, event, )
        
        # NOTE: ok, reset
        # raise Exception("!")
        
        return r
    
    def modal(self, context, event, ):
        # NOTE: error, cannot reset, expected
        # NOTE: solution: no code in `invoke` and `modal` apart of try...except wrapped function call
        '''
        Traceback (most recent call last):
          File "/Users/carbon/Library/Application Support/Blender/3.3/scripts/addons/Scatter5/manual/brushes.py", line 15956, in modal
            raise Exception("!")
        Exception: !
        Error: Python: Traceback (most recent call last):
          File "/Users/carbon/Library/Application Support/Blender/3.3/scripts/addons/Scatter5/manual/brushes.py", line 15956, in modal
            raise Exception("!")
        Exception: !

        Traceback (most recent call last):
          File "/Users/carbon/Library/Application Support/Blender/3.3/scripts/addons/Scatter5/widgets/grid.py", line 99, in _draw
            if(self._invoke_area == context.area):
          File "/Applications/Blender/blender-3.3.0.app/Contents/Resources/3.3/scripts/modules/bpy_types.py", line 813, in __getattribute__
            properties = StructRNA.path_resolve(self, "properties")
        ReferenceError: StructRNA of type SCATTER5_OT_manual_brush_tool_debug_errors has been removed
        '''
        # raise Exception("!")
        
        r = super().modal(context, event, )
        
        # NOTE: error, cannot reset, expected, same as above..
        # NOTE: solution: no code in `invoke` and `modal` apart of try...except wrapped function call
        '''
        ------------ || ------------
        '''
        # raise Exception("!")
        
        return r
    
    def _invoke(self, context, event, ):
        self._brush_props_name = 'tool_default'
        
        # NOTE: ok, all seems reset
        # raise Exception("!")
        
        r = super()._invoke(context, event, )
        
        # NOTE: ok, all seems reset
        # raise Exception("!")
        
        '''
        self._brush.interval = 0.1
        self._brush.draw_on = 'TIMER'
        
        self._action_execute_on = self._brush.draw_on
        self._action_timer_interval = self._brush.interval
        '''
        
        return r
    
    def _invoke_private(self, context, event, ):
        # NOTE: ok, all seems reset
        # raise Exception("!")
        
        r = super()._invoke_private(context, event, )
        
        # NOTE: insta crash at: /Applications/Blender/blender-3.3.0.app/Contents/Resources/3.3/scripts/startup/bl_ui/space_statusbar.py @12
        # raise Exception("!")
        
        return r
    
    def invoke(self, context, event, ):
        # NOTE: does nothing.. expected
        # NOTE: solution: no code in `invoke` and `modal` apart of try...except wrapped function call
        # raise Exception("!")
        
        r = super().invoke(context, event, )
        
        # NOTE: insta crash at: /Applications/Blender/blender-3.3.0.app/Contents/Resources/3.3/scripts/startup/bl_ui/space_statusbar.py @12
        # NOTE: problems expected, cannot wrap such error
        # NOTE: solution: no code in `invoke` and `modal` apart of try...except wrapped function call
        # raise Exception("!")
        
        return r


# ------------------------------------------------------------------ debug brushes <<<


# DONE: add debug tool that can produce artificial errors in different stages to test that errors are always reported and ui can be restored afterwards
# DONE: everything related to cleanup: addon deactivation, loading new files etc..


def panic(where="", ):
    m = "{: <{namew}} >>> {}".format(where, "panic! > {}".format(ToolBox.tool), namew=36, )
    # log(m, prefix='>>>', color='ERROR', )
    log(m, prefix='>>>', )
    
    # print error, if any, to console
    import sys
    import traceback
    e = sys.exc_info()
    if(e != (None, None, None, )):
        traceback.print_exc()
    
    # log panic..
    m = "{: <{namew}} >>> {}".format(where, "shutdown everything!", namew=36, )
    log(m, prefix='>>>', )
    
    # reset toolbox
    ToolBox.tool = None
    if(ToolBox.reference is not None):
        # call abort on tool if it didn't by itself
        ToolBox.reference._abort(bpy.context, None, )
    ToolBox.reference = None
    
    # stop all screen drawing
    ToolWidgets.deinit()
    SC5InfoBox.deinit()
    # SC5GridOverlay.deinit()
    GridOverlay.deinit()
    
    # restore pointer and status
    bpy.context.window.cursor_modal_restore()
    bpy.context.workspace.status_text_set(text=None, )
    
    # restore custom workspace
    from ..ui import ui_manual
    ui_manual.modal_hijack_restore(bpy.context)
    
    # add history state
    bpy.ops.ed.undo_push(message="Deinitialize", )
    
    # clear runtime mesh, bmesh and bvh data
    ToolSessionCache.free()
    # reset runtime props
    ToolSession.reset()
    # select builtin tool
    bpy.ops.wm.tool_set_by_id(name="builtin.select")
    # and reset last used tool so next time it does not load the one that had problem.. unless problem is in spray.. maybe add dot instead? but dot is more complex then before as well...
    bpy.context.scene.scatter5.manual.active_tool = "scatter5.manual_brush_tool_spray"


def init():
    pass


def deinit():
    ToolBox.tool = None
    # if(ToolBox.reference is not None):
    #     ToolBox.reference._abort(bpy.context, None, )
    # ToolBox.reference = None
    
    if(ToolBox.reference is not None):
        try:
            ToolBox.reference._abort(bpy.context, None, )
        except Exception as e:
            # NOTE: panic!
            panic(deinit.__qualname__)
    ToolBox.reference = None
    
    ToolWidgets.deinit()
    SC5InfoBox.deinit()
    # SC5GridOverlay.deinit()
    GridOverlay.deinit()
    
    # WATCH: i am not so sure with this..
    if(ToolSession.active):
        from ..ui import ui_manual
        ui_manual.modal_hijack_restore(bpy.context)
    
    ToolSession.reset()
    
    ToolSessionCache.free()
    
    if(bpy.context.window is not None):
        bpy.context.window.cursor_modal_restore()
    if(bpy.context.workspace is not None):
        bpy.context.workspace.status_text_set(text=None, )
    
    # WATCH: i am not so sure with this..
    if(bpy.context.window is not None and bpy.context.workspace is not None):
        try:
            n = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode).idname
        except Exception as e:
            n = None
        if(n in get_all_tool_ids()):
            bpy.ops.wm.tool_set_by_id(name="builtin.select")


def add_unique_handler(ls, fn, ):
    n = fn.__name__
    m = fn.__module__
    for i in range(len(ls) - 1, -1, -1):
        if(ls[i].__name__ == n and ls[i].__module__ == m):
            del ls[i]
    ls.append(fn)


from bpy.app.handlers import persistent


@persistent
def watcher(undefined):
    deinit()


add_unique_handler(bpy.app.handlers.load_pre, watcher, )


# ------------------------------------------------------------------ DEBUG >>>

@persistent
def update_watcher(scene, depsgraph, ):
    dus = depsgraph.updates
    for u in dus:
        m = "id.name: {}: geometry: {}, shading: {}, transform: {}".format(u.id.name, u.is_updated_geometry, u.is_updated_shading, u.is_updated_transform)
        log(m, indent=0, prefix='DEPSGRAPH_UPDATE:', )


WATCH_DEPSGRAPH_UPDATES = False
if(WATCH_DEPSGRAPH_UPDATES):
    add_unique_handler(bpy.app.handlers.depsgraph_update_post, update_watcher, )


# ------------------------------------------------------------------ DEBUG <<<


# -----------------------------------------------------------------------------------------------------------------------------

"""
class SCATTER5_OT_manual_physics_brush(SCATTER5_OT_manual_base_brush, ):
    bl_idname = "scatter5.manual_physics_brush"
    bl_label = translate("Physics Brush")
    bl_description = translate("Physics Brush")
    
    brush_type = "physics_brush"
    icon = "W_CLICK"
    dat_icon = "SCATTER5_CLICK"
    
    modal_adjust_map = []
    
    tool_id = "scatter5.manual_physics_brush"
    
    DUMMY_INSTANCE_INITIAL_GLOBAL_LOCATION = Vector((0.0, 0.0, -1000.0, ))
    
    @classmethod
    def poll(cls, context, ):
        # NOTE: disable physics brush for 5.1
        return False
    
    def activate(self, ob, ):
        # activation of object for use with builtinn operators
        if(type(ob) == str):
            o = bpy.data.objects[ob]
        else:
            o = ob
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        return o
    
    def invoke(self, context, event, ):
        # set brush props here so subclass can inject its own collection..
        self.brush = context.scene.scatter5.manual.physics_brush
        
        self._theme = ToolTheme(self, )
        ToolWidgets.init(self, context, )
        ToolWidgets._cache[self.tool_id] = {
            'screen_components': [],
            'cursor_components': [],
        }
        
        r = super().invoke(context, event, )
        
        self._max_reached = False
        self._alive = {}
        self.scene = context.scene
        
        # self._unique_location_counter = 0
        self._ignore_existing_pids_from = -1
        if(len(self.target.data.vertices)):
            me = self.target.data
            pids = np.zeros(len(me.vertices), dtype=int, )
            me.attributes['{}id'.format(self.attribute_prefix)].data.foreach_get('value', pids, )
            self._ignore_existing_pids_from = np.max(pids)
        
        # store initial state
        self._initial_fps = self.scene.render.fps
        self._initial_frame_start = self.scene.frame_start
        self._initial_frame_end = self.scene.frame_end
        self._initial_frame_step = self.scene.frame_step
        self._initial_frame_map_old = self.scene.render.frame_map_old
        self._initial_frame_map_new = self.scene.render.frame_map_new
        # set something suitable
        self.scene.render.fps = self.brush.scene_render_fps
        self.scene.frame_start = self.brush.scene_frame_start
        self.scene.frame_end = self.brush.scene_frame_end
        self.scene.frame_step = self.brush.scene_frame_step
        self.scene.render.frame_map_old = self.brush.scene_render_frame_map_old
        self.scene.render.frame_map_new = self.brush.scene_render_frame_map_new
        
        # remove existing rigid body world so we can start with default one
        if(self.scene.rigidbody_world is not None):
            bpy.ops.rigidbody.world_remove()
        
        # setup collection to store all simulation obejcts
        self.col = bpy.data.collections.get(self.brush.simulation_collection_name)
        if(not self.col):
            self.col = bpy.data.collections.new(self.brush.simulation_collection_name)
            self.scene.collection.children.link(self.col)
        
        # set passive for surface and by this rigid world will be created
        self.activate(self.surface)
        bpy.ops.rigidbody.objects_add(type='PASSIVE')
        self.surface.rigid_body.collision_shape = 'MESH'
        self.surface.rigid_body.friction = 0.75
        
        # # use existing.. set them as passive to act as obstacle. like tool never stopped
        # bpy.ops.object.select_all(action='DESELECT')
        # if(len(self.col.objects)):
        #     for o in self.col.objects:
        #         o.select_set(True)
        #     bpy.context.view_layer.objects.active = o
        #     bpy.ops.rigidbody.objects_add(type='PASSIVE')
        #     bpy.ops.object.select_all(action='DESELECT')
        
        # set some props to rigid body world
        self.scene.rigidbody_world.use_split_impulse = True
        self.scene.rigidbody_world.point_cache.frame_start = self.brush.scene_frame_start
        self.scene.rigidbody_world.point_cache.frame_end = self.brush.scene_frame_end
        self.scene.rigidbody_world.point_cache.frame_step = self.brush.scene_frame_step
        
        # add frame change handlers
        bpy.app.handlers.frame_change_pre.append(self.on_frame_change_pre)
        bpy.app.handlers.frame_change_post.append(self.on_frame_change_post)
        
        # play timeline
        bpy.ops.screen.animation_play()
        
        return r
    
    '''
    def _get_unique_location_counter(self, ):
        self._unique_location_counter += 1
        return self._unique_location_counter
    '''
    
    def _add_blank(self, ):
        self._ensure_attributes()
        
        me = self.target.data
        me.vertices.add(1)
        i = len(me.vertices) - 1
        
        pid = self._gen_id(1, )[0]
        
        # move it somewhere away..
        loc = self.DUMMY_INSTANCE_INITIAL_GLOBAL_LOCATION.copy()
        # loc.z -= self._get_unique_location_counter()
        loc.z -= pid
        nor = Vector((0.0, 0.0, 1.0))
        loc, nor = self._global_to_surface_space(loc, nor, )
        
        me.vertices[i].co = loc
        
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self.brush.instance_index
        me.attributes['{}id'.format(self.attribute_prefix)].data[i].value = pid
        
        me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector = nor
        me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        me.attributes['{}align_z'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 1.0)
        me.attributes['{}align_y'.format(self.attribute_prefix)].data[i].vector = (0.0, 1.0, 0.0)
        
        # and scale to zero so it is not visible
        scale = (0.0, 0.0, 0.0)
        me.attributes['{}scale'.format(self.attribute_prefix)].data[i].vector = scale
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = scale
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data[i].value = 0
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = 0
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = 0
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector = (0.0, 0.0, 0.0)
        
        return i
    
    def get_new_instance_object(self, ):
        # # TODO: use instance list.. somehow..
        # return bpy.data.objects['Cube']
        
        # col = self.surface.scatter5.get_psy_active().s_instances_coll_ptr
        # return col.objects[0]
        
        i = self._add_blank()
        self.target.data.update()
        
        z_max = 0
        o_name = None
        
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for o in depsgraph.object_instances:
            if(o.is_instance):
                if(o.parent.original == self.target):
                    z = int(abs(round(o.matrix_world[2][3])))
                    if(z > z_max and z > 1000):
                        # NOTE: what if something goes wrong? and i don't find correct instance?
                        z_max = z
                        o_name = o.object.original.name
        
        col = self.surface.scatter5.get_psy_active().s_instances_coll_ptr
        return col.objects[o_name]
    
    def get_recycled_instance_object(self, pi, ):
        for i, v in enumerate(self.target.data.vertices):
            pid = self.target.data.attributes['{}id'.format(self.attribute_prefix)].data[i].value
            if(pid == pi):
                break
        
        zz = self.DUMMY_INSTANCE_INITIAL_GLOBAL_LOCATION.z - ((int(pi) - 1) + 1)
        zz = int(abs(round(zz)))
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for o in depsgraph.object_instances:
            if(o.is_instance):
                if(o.parent.original == self.target):
                    z = int(abs(round(o.matrix_world[2][3])))
                    if(zz == z):
                        o_name = o.object.original.name
                        break
        
        col = self.surface.scatter5.get_psy_active().s_instances_coll_ptr
        return col.objects[o_name], pi, v.index
    
    def on_frame_change_pre(self, scene, depsgraph, ):
        if(self._max_reached is True):
            return
        # if mouse is down
        if(self.lmb):
            loc, nor, idx, dst = self._project(None, None)
            if(loc is None):
                return
            # and i have some space in alive instances count
            if(len(self._alive.keys()) < self.brush.max_active):
                if(self._loc is None):
                    # and i project something before
                    return
                
                reuse = []
                for i, v in enumerate(self.target.data.vertices):
                    pid = self.target.data.attributes['{}id'.format(self.attribute_prefix)].data[i].value
                    if(pid <= self._ignore_existing_pids_from):
                        continue
                    
                    f = False
                    for o in self.col.objects:
                        props = o.scatter5.manual_physics_brush_object_properties
                        if(props.point_id == pid):
                            f = True
                    if(not f):
                        reuse.append(pid)
                
                if(len(reuse)):
                    oo, pi, vi = self.get_recycled_instance_object(np.min(reuse))
                    o = self.clone(oo, True)
                    props = o.scatter5.manual_physics_brush_object_properties
                    props.point_id = pi
                    props.vertex_index = vi
                    props.object_name = oo.name
                    props.active = True
                    props.frozen = False
                else:
                    # clone
                    oo = self.get_new_instance_object()
                    o = self.clone(oo, True)
                    props = o.scatter5.manual_physics_brush_object_properties
                    props.point_id = self.target.data.attributes['{}id'.format(self.attribute_prefix)].data[len(self.target.data.vertices) - 1].value
                    props.vertex_index = len(self.target.data.vertices) - 1
                    props.object_name = oo.name
                    props.active = True
                    props.frozen = False
                
                # and store in alive dict
                self._alive[o.name] = {
                    'start_frame': self.scene.frame_current,
                    'matrix_world': np.array(o.matrix_world),
                }
                
                if(len(self._alive.keys()) >= self.brush.max_active):
                    self._max_reached = True
    
    def on_frame_change_post(self, scene, depsgraph, ):
        # find dead instances by comparing current matrix and matrix from previous frame
        # if values are within _atol, consider it stable
        dead = {}
        for k, v in self._alive.items():
            o = bpy.data.objects[k]
            a = np.array(o.matrix_world)
            if(np.allclose(v['matrix_world'], a, atol=self.brush.np_allclose_atol, ) and v['start_frame'] != self.scene.frame_current):
                # bpy.ops.screen.animation_cancel(restore_frame=False, )
                dead[k] = True
            else:
                self._alive[k]['matrix_world'] = a
        
        # freeze dead and remove from alive dict
        for k, v in dead.items():
            self.freeze(k)
            
            o = bpy.data.objects.get(k)
            props = o.scatter5.manual_physics_brush_object_properties
            props.active = False
            props.frozen = True
            
            del self._alive[k]
        
        if(not len(self._alive.keys())):
            self._max_reached = False
        
        # i use many builtin operators (sadly) so deselect all to look ok
        bpy.ops.object.select_all(action='DESELECT')
        
        # if i am out of timeout
        if(self.scene.frame_current >= self.brush.timeout):
            # and some are still alive
            if(len(self._alive.keys())):
                log('timeout: removing {} object(s)'.format(len(self._alive.keys())))
                # kill them all..
                self.kill()
                self._max_reached = False
        
        # # DEBUG
        # vs = []
        # ns = []
        # for o in self.col.objects:
        #     l, r, s = o.matrix_world.decompose()
        #     vs.append(l.to_tuple())
        #     ns.append(Vector(r.to_matrix().to_4x4() @ Vector((0.0, 0.0, 1.0))).to_tuple())
        # debug.points(self.target, vs, ns, None, )
        # # DEBUG
        
        # # DEBUG
        # vs = []
        # cs = []
        # for o in self.col.objects:
        #     l, r, s = o.matrix_world.decompose()
        #     vs.append(l.to_tuple())
        #     props = o.scatter5.manual_physics_brush_object_properties
        #     if(props.frozen):
        #         cs.append((1.0, 1.0, 0.0, 1.0))
        #     else:
        #         cs.append((1.0, 1.0, 1.0, 1.0))
        # debug.points(self.target, vs, None, cs, )
        # # DEBUG
    
    def kill(self, ):
        # on abort or timeout, kill all alive instances so they don't mess simulation on first frame
        for k, v in self._alive.items():
            o = bpy.data.objects[k]
            me = o.data
            self.col.objects.unlink(o)
            bpy.data.objects.remove(o)
            bpy.data.meshes.remove(me)
        
        self._alive = {}
    
    def freeze(self, k, ):
        # set instance to passive and add its already simulated matrix
        o = self.activate(k)
        m = o.matrix_world.copy()
        bpy.ops.rigidbody.objects_add(type='PASSIVE')
        o.matrix_world = m
    
    def clone(self, ob, active=True, ):
        # duplicate instance object and set active
        # object data is copied as well, i want matrix aplied and in the end instance will be converted to manual system vertex with attributes..
        if(type(ob) == str):
            o = bpy.data.objects[ob]
        else:
            o = ob
        
        o = o.copy()
        o.name = 'tmp-instance-{}'.format(uuid.uuid1())
        o.data = o.data.copy()
        o.data.name = o.name
        # o.data.transform(o.matrix_world)
        self.col.objects.link(o)
        # o.select_set(True)
        # bpy.context.view_layer.objects.active = o
        xy = [-self.brush.radius, self.brush.radius]
        a = np.random.uniform(xy[0], xy[1], [2, ])
        '''
        mt = Matrix.Translation((self._loc.x + a[0], self._loc.y + a[1], self._loc.z + self.brush.height)).to_4x4()
        # TODO: use rotation and scale from panels, following is just basic randomization so something is there..
        mr = Matrix.Rotation(np.random.uniform(0.0, np.pi, ), 4, 'Z', )
        # d = 0.2
        # ms = Matrix.Scale(np.random.uniform(1.0 - d, 1.0 + d, ), 4, )
        
        gl, gr, gs = self.surface.matrix_world.decompose()
        gms = Matrix(((gs[0], 0.0, 0.0, 0.0), (0.0, gs[1], 0.0, 0.0), (0.0, 0.0, gs[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        ms = Matrix()
        # ms = gms.inverted() @ ms
        ms = gms @ ms
        
        m = mt @ mr @ ms
        # o.matrix_world = Matrix.Translation((self._loc.x + a[0], self._loc.y + a[1], self._loc.z + self.height))
        o.matrix_world = m
        # self.cinstance = o
        '''
        mt = Matrix.Translation((self._loc.x + a[0], self._loc.y + a[1], self._loc.z + self.brush.height)).to_4x4()
        r = self._gen_rotation(1, np.array(self._loc, dtype=float, ).reshape(-1, 3), np.array(self._nor, dtype=float, ).reshape(-1, 3), )[0]
        s = self._gen_scale(1, )[0]
        gl, gr, gs = self.surface.matrix_world.decompose()
        mr = r.to_matrix().to_4x4()
        gmr = gr.to_matrix().to_4x4()
        mr = gmr @ mr
        ms = Matrix(((s[0], 0.0, 0.0, 0.0), (0.0, s[1], 0.0, 0.0), (0.0, 0.0, s[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        gms = Matrix(((gs[0], 0.0, 0.0, 0.0), (0.0, gs[1], 0.0, 0.0), (0.0, 0.0, gs[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        ms = gms @ ms
        m = mt @ mr @ ms
        # m = m @ self.surface.matrix_world
        o.matrix_world = m
        
        if(active):
            self.activate(o)
            bpy.ops.rigidbody.objects_add(type='ACTIVE')
            # is there any way to get these presets? without rewriting them?
            # list is in: source/blender/editors/physics/rigidbody_object.c
            bpy.ops.rigidbody.mass_calculate(material='Stone', density=2515, )
            
            o.rigid_body.friction = 0.75
            o.rigid_body.linear_damping = 0.1
            o.rigid_body.angular_damping = 0.2
        
        return o
    
    def _self_brush_modal_update(self, context, ):
        self.brush = context.scene.scatter5.manual.physics_brush
    
    def _on_mouse_hover(self, context, event, ):
        self._drawing(context, event, )
        loc = self._loc
        nor = self._nor
        
        l = loc.copy()
        h = self.brush.height
        # l = l + (nor * h)
        l.z += h
        mt = Matrix.Translation(l, )
        # mr = self._rotation_to(Vector((0.0, 0.0, 1.0, )), nor, ).to_matrix().to_4x4()
        mr = Matrix()
        radius = self.brush.radius
        ms = Matrix(((radius, 0.0, 0.0, 0.0), (0.0, radius, 0.0, 0.0), (0.0, 0.0, radius, 0.0), (0.0, 0.0, 0.0, 1.0)))
        m = mt @ mr @ ms
        
        wcf = self._theme._fill_color
        wco = self._theme._outline_color
        if(len(self._alive.keys()) and self.lmb and len(self._alive.keys()) < self.brush.max_active and not self._max_reached):
            # wcf = (1.0, 0.0, 0.0, 0.1, )
            wcf = (1.0, 1.0, 0.0, 0.5, )
            wco = (1.0, 1.0, 0.0, 1.0, )
        elif(len(self._alive.keys())):
            # wcf = (1.0, 1.0, 0.0, 0.1, )
            wcf = (1.0, 1.0, 0.0, 0.5, )
            wco = (1.0, 1.0, 0.0, 1.0, )
        
        lpx = 20
        region = context.region
        rv3d = context.region_data
        loc_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, self._loc, )
        loc2_2d = Vector((loc_2d.x, loc_2d.y + lpx))
        loc2_3d = view3d_utils.region_2d_to_location_3d(region, rv3d, loc2_2d, self._loc)
        al = ((self._loc.x - loc2_3d.x) ** 2 + (self._loc.y - loc2_3d.y) ** 2 + (self._loc.z - loc2_3d.z) ** 2) ** 0.5
        
        ll = loc.copy()
        ll.z += al
        mt = Matrix.Translation(ll, )
        mr = Matrix.Rotation(np.radians(180.0), 3, 'X').to_4x4()
        marr = mt @ mr
        
        alen = self.brush.height
        
        ls = []
        ls.extend([
            {
                'function': 'circle_outline_3d',
                'arguments': {
                    'matrix': m,
                    'color': wco,
                },
            },
            {
                'function': 'thick_line_3d',
                'arguments': {
                    'a': loc,
                    'b': l,
                    'matrix': Matrix(),
                    'color': wco,
                }
            },
            {
                'function': 'arrow_3d',
                'arguments': {
                    'point': self._loc,
                    # 'length': self.brush.height,
                    # 'length': 1 / 5 * 4,
                    'length': al,
                    'matrix': marr,
                    'color': wco,
                    # # 'outer_radius': 1 / 20,
                    # # 'inner_radius': 1 / 60,
                    # # 'shoulder_offset': 1 / 5,
                    # # 'steps': 16,
                    # 'outer_radius': 1 / 5,
                    # 'inner_radius': 1 / 15,
                    # 'shoulder_offset': 1 / 5 * 4,
                    'outer_radius': alen / 20,
                    'inner_radius': alen / 60,
                    'shoulder_offset': alen / 5,
                }
            },
        ])
        
        if(self.lmb):
            # ls.extend([
            #     {
            #         'function': 'circle_fill_3d',
            #         'arguments': {
            #             'matrix': m,
            #             'color': wcf,
            #         },
            #     },
            # ])
            ls.insert(0, {
                'function': 'circle_fill_3d',
                'arguments': {
                    'matrix': m,
                    'color': wcf,
                },
            })
        
        l = len(self._alive.keys())
        if(l):
            x = event.mouse_region_x
            y = event.mouse_region_y
            ls.extend([
                {
                    'function': 'label_2d',
                    'arguments': {
                        'coords': (x, y, ),
                        'offset': (10, -10 * 2, ),
                        'text': "Active: {}".format(l),
                        # 'color': self._theme._text_color,
                        'color': wco,
                        'size': self._theme._text_size,
                    },
                },
            ])
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._tag_redraw()
    
    def _on_mouse_out(self, context, event, ):
        ls = []
        
        wcf = self._theme._fill_color
        wco = self._theme._outline_color
        l = len(self._alive.keys())
        if(l):
            wcf = self._theme._fill_color
            wco = self._theme._outline_color
            if(len(self._alive.keys()) and self.lmb and len(self._alive.keys()) < self.brush.max_active and not self._max_reached):
                # wcf = (1.0, 0.0, 0.0, 0.1, )
                wcf = (1.0, 0.5, 0.0, 0.5, )
                wco = (1.0, 0.5, 0.0, 1.0, )
            elif(len(self._alive.keys())):
                # wcf = (1.0, 1.0, 0.0, 0.1, )
                wcf = (1.0, 1.0, 0.0, 0.5, )
                wco = (1.0, 1.0, 0.0, 1.0, )
            
            x = event.mouse_region_x
            y = event.mouse_region_y
            ls.extend([
                {
                    'function': 'label_2d',
                    'arguments': {
                        'coords': (x, y, ),
                        'offset': (10, -10 * 2, ),
                        'text': "Active: {}".format(l),
                        # 'color': self._theme._text_color,
                        'color': wco,
                        'size': self._theme._text_size,
                    },
                },
            ])
        
        ToolWidgets._cache[self.tool_id]['screen_components'] = ls
        ToolWidgets._tag_redraw()
    
    def _drawing(self, context, event, ):
        loc, nor, idx, dst = self._project(context, event, )
        if(loc is not None):
            # for each draw event, those two should be the same for all generated points, so i can keep this on class.. might get easier in future to access that
            self._loc = loc.copy()
            self._nor = nor.copy()
            
            # r = self._generate(loc, nor, idx, dst, )
            # if(r is not None):
            #     loc, nor = r
            #     self._store(loc, nor, )
            #
            # self.target.data.update()
    
    def _on_lmb_press(self, context, event, ):
        # NOTE: very important, if there was some drawing done, then undo without dropping tool, this is pointing somewhere invalid, each brush MUST set this again on each use AND before super()
        self.brush = context.scene.scatter5.manual.physics_brush
        super()._on_lmb_press(context, event, )
        
        self._drawing(context, event, )
        
        # kill alive
        self.kill()
        # restart timeline
        self.scene.frame_set(1)
    
    def _on_lmb_move(self, context, event, ):
        super()._on_lmb_move(context, event, )
        
        self._drawing(context, event, )
    
    def _on_lmb_release(self, context, event, ):
        super()._on_lmb_release(context, event, )
        
        self._drawing(context, event, )
        
        # # # push to history..
        # bpy.ops.ed.undo_push(message=self.bl_label, )
    
    def _cleanup(self, ):
        ToolWidgets.deinit()
        
        # handlers
        bpy.app.handlers.frame_change_pre.remove(self.on_frame_change_pre)
        bpy.app.handlers.frame_change_post.remove(self.on_frame_change_post)
        # timeline
        bpy.ops.screen.animation_cancel(restore_frame=True, )
        # remove rigidbody flag
        self.activate(self.surface)
        bpy.ops.rigidbody.objects_remove()
        # kill alive instances
        self.kill()
        # remove rigidbody flag from instances in collection
        if(len(self.col.objects)):
            bpy.ops.object.select_all(action='DESELECT')
            for o in self.col.objects:
                o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.rigidbody.objects_remove()
        bpy.ops.object.select_all(action='DESELECT')
        
        # restore initial state
        self.scene.render.fps = self._initial_fps
        self.scene.frame_start = self._initial_frame_start
        self.scene.frame_end = self._initial_frame_end
        self.scene.frame_step = self._initial_frame_step
        self.scene.render.frame_map_old = self._initial_frame_map_old
        self.scene.render.frame_map_new = self._initial_frame_map_new
        
        # remove rigidbody world
        if(self.scene.rigidbody_world is not None):
            bpy.ops.rigidbody.world_remove()
        
        # # TODO: at this stage, objects in collection should be converted to manual system vertices and removed together with collection from scene..
        # if(len(self.col.objects)):
        #     for o in self.col.objects:
        #         self._store_instance(o, )
        
        # frozen object to instances
        not_void = []
        if(len(self.col.objects)):
            for o in self.col.objects:
                props = o.scatter5.manual_physics_brush_object_properties
                i = props.vertex_index
                not_void.append(i)
                self._store_instance2(o, )
        # NOTE: points that don't have corresponding frozen objects leave in void, scaled to zero in center. what to do with them? if i remove them it will change order..
        l = len(self.target.data.vertices)
        void = []
        if(len(not_void) < l):
            for i in range(l):
                if(i not in not_void):
                    # ignore existing, instances that been there before brush started
                    pid = self.target.data.attributes['{}id'.format(self.attribute_prefix)].data[i].value
                    if(pid <= self._ignore_existing_pids_from):
                        continue
                    
                    self.target.data.vertices[i].co = Vector()
                    void.append(i)
        # NOTE: the only thing i can do is look if they are all at the end of list, then i can safely remove them, any in the middle need to stay.
        if(len(void)):
            a = np.zeros(l, dtype=bool, )
            a[not_void] = True
            b = a[:len(not_void)]
            safe = np.all(b)
            if(safe):
                bm = bmesh.new()
                bm.from_mesh(self.target.data)
                bm.verts.ensure_lookup_table()
                for v in bm.verts:
                    if(v.index in void):
                        bm.verts.remove(v)
                bm.to_mesh(self.target.data)
                bm.free()
        
        # now just remove all generated stuff..
        if(len(self.col.objects)):
            for o in self.col.objects:
                me = o.data
                self.col.objects.unlink(o)
                bpy.data.objects.remove(o)
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(self.col)
        
        # # DEBUG
        # vs = []
        # ns = []
        # cs = []
        # me = self.target.data
        # m = self.surface.matrix_world
        # _, r, _ = m.decompose()
        # r = r.to_matrix()
        # for i, v in enumerate(me.vertices):
        #     vs.append(Vector(m @ v.co).to_tuple())
        #     n = Vector(r @ me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector)
        #     n.normalize()
        #     ns.append(n.to_tuple())
        #     cs.append((1.0, 1.0, 0.0, 1.0))
        # debug.points(self.target, vs, ns, cs, )
        # # DEBUG
        
        super()._cleanup()
    
    def _store_instance(self, o, ):
        self._ensure_attributes()
        
        location, rotation, scale = o.matrix_world.decompose()
        
        gl, gr, gs = self.surface.matrix_world.decompose()
        # mr = rotation.to_matrix().to_4x4()
        # gmr = gr.to_matrix().to_4x4()
        # mr = gmr.inverted() @ mr
        # _, rotation, _ = mr.decompose()
        ms = Matrix(((scale[0], 0.0, 0.0, 0.0), (0.0, scale[1], 0.0, 0.0), (0.0, 0.0, scale[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        gms = Matrix(((gs[0], 0.0, 0.0, 0.0), (0.0, gs[1], 0.0, 0.0), (0.0, 0.0, gs[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        ms = gms.inverted() @ ms
        _, _, scale = ms.decompose()
        
        nor = rotation.to_matrix().to_4x4() @ Vector((0.0, 0.0, 1.0))
        up = rotation.to_matrix().to_4x4() @ Vector((0.0, 1.0, 0.0))
        
        loc, nor = self._global_to_surface_space(location, nor, )
        
        me = self.target.data
        me.vertices.add(1)
        i = len(me.vertices) - 1
        me.vertices[i].co = loc
        
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self.brush.instance_index
        
        nm = '{}normal'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = nor
        
        # r = self._gen_rotation(1, np.array(loc, dtype=float, ).reshape(-1, 3), np.array(nor, dtype=float, ).reshape(-1, 3), )[0]
        r = self._direction_to_rotation_with_m3x3(nor, up, )
        
        e = r.to_euler('XYZ')
        nm = '{}rotation'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = e
        
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
        nm = '{}align_z'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        
        v = Vector((0.0, 1.0, 0.0))
        v.rotate(e)
        nm = '{}align_y'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = v
        
        # s = self._gen_scale(1, )
        s = scale
        
        nm = '{}scale'.format(self.attribute_prefix)
        me.attributes[nm].data[i].vector = s
        
        anm = '{}private_s_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_base[0]
        
        anm = '{}private_s_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random[0]
        
        anm = '{}private_s_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_random_random[0]
        
        anm = '{}private_s_random_type'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_s_random_type[0]
        
        anm = '{}private_s_change'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change[0]
        
        anm = '{}private_s_change_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_s_change_random[0]
        
        # id
        ids = self._gen_id(1, )
        nm = '{}id'.format(self.attribute_prefix)
        me.attributes[nm].data[i].value = ids[0]
        
        # rotation intermediates v2 ---------------------------------------------------
        anm = '{}private_r_align'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_align[0]
        
        anm = '{}private_r_up'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].value = self._private_r_up[0]
        
        anm = '{}private_r_base'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_base[0]
        
        anm = '{}private_r_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random[0]
        
        anm = '{}private_r_random_random'.format(self.attribute_prefix)
        att = me.attributes[anm].data
        att[i].vector = self._private_r_random_random[0]
    
    def _store_instance2(self, o, ):
        self._ensure_attributes()
        
        location, rotation, scale = o.matrix_world.decompose()
        
        gl, gr, gs = self.surface.matrix_world.decompose()
        ms = Matrix(((scale[0], 0.0, 0.0, 0.0), (0.0, scale[1], 0.0, 0.0), (0.0, 0.0, scale[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        gms = Matrix(((gs[0], 0.0, 0.0, 0.0), (0.0, gs[1], 0.0, 0.0), (0.0, 0.0, gs[2], 0.0), (0.0, 0.0, 0.0, 1.0)))
        ms = gms.inverted() @ ms
        _, _, scale = ms.decompose()
        
        nor = rotation.to_matrix().to_4x4() @ Vector((0.0, 0.0, 1.0))
        up = rotation.to_matrix().to_4x4() @ Vector((0.0, 1.0, 0.0))
        
        loc, nor = self._global_to_surface_space(location, nor, )
        
        props = o.scatter5.manual_physics_brush_object_properties
        pid = props.point_id
        i = props.vertex_index
        
        me = self.target.data
        
        me.vertices[i].co = loc
        
        me.attributes['{}index'.format(self.attribute_prefix)].data[i].value = self.brush.instance_index
        
        me.attributes['{}normal'.format(self.attribute_prefix)].data[i].vector = nor
        
        r = self._direction_to_rotation_with_m3x3(nor, up, )
        e = r.to_euler('XYZ')
        me.attributes['{}rotation'.format(self.attribute_prefix)].data[i].vector = e
        
        v = Vector((0.0, 0.0, 1.0))
        v.rotate(e)
        me.attributes['{}align_z'.format(self.attribute_prefix)].data[i].vector = v
        
        v = Vector((0.0, 1.0, 0.0))
        v.rotate(e)
        me.attributes['{}align_y'.format(self.attribute_prefix)].data[i].vector = v
        
        s = scale
        me.attributes['{}scale'.format(self.attribute_prefix)].data[i].vector = s
        me.attributes['{}private_s_base'.format(self.attribute_prefix)].data[i].vector = self._private_s_base[0]
        me.attributes['{}private_s_random'.format(self.attribute_prefix)].data[i].vector = self._private_s_random[0]
        me.attributes['{}private_s_random_random'.format(self.attribute_prefix)].data[i].vector = self._private_s_random_random[0]
        me.attributes['{}private_s_random_type'.format(self.attribute_prefix)].data[i].value = self._private_s_random_type[0]
        me.attributes['{}private_s_change'.format(self.attribute_prefix)].data[i].vector = self._private_s_change[0]
        me.attributes['{}private_s_change_random'.format(self.attribute_prefix)].data[i].vector = self._private_s_change_random[0]
        
        # ids = self._gen_id(1, )
        # me.attributes['{}id'.format(self.attribute_prefix)].data[i].value = ids[0]
        me.attributes['{}id'.format(self.attribute_prefix)].data[i].value = pid
        
        me.attributes['{}private_r_align'.format(self.attribute_prefix)].data[i].value = self._private_r_align[0]
        me.attributes['{}private_r_up'.format(self.attribute_prefix)].data[i].value = self._private_r_up[0]
        me.attributes['{}private_r_base'.format(self.attribute_prefix)].data[i].vector = self._private_r_base[0]
        me.attributes['{}private_r_random'.format(self.attribute_prefix)].data[i].vector = self._private_r_random[0]
        me.attributes['{}private_r_random_random'.format(self.attribute_prefix)].data[i].vector = self._private_r_random_random[0]
"""

# -----------------------------------------------------------------------------------------------------------------------------


classes = (
    SCATTER5_OT_manual_brush_tool_dot,
    SCATTER5_OT_manual_brush_tool_pose,
    SCATTER5_OT_manual_brush_tool_path,
    SCATTER5_OT_manual_brush_tool_chain,
    SCATTER5_OT_manual_brush_tool_spatter,
    SCATTER5_OT_manual_brush_tool_spray,
    SCATTER5_OT_manual_brush_tool_spray_aligned,
    SCATTER5_OT_manual_brush_tool_lasso_fill,
    SCATTER5_OT_manual_brush_tool_clone,
    SCATTER5_OT_manual_brush_tool_eraser,
    SCATTER5_OT_manual_brush_tool_dilute,
    SCATTER5_OT_manual_brush_tool_smooth,
    SCATTER5_OT_manual_brush_tool_move,
    SCATTER5_OT_manual_brush_tool_free_move,
    SCATTER5_OT_manual_brush_tool_manipulator,
    SCATTER5_OT_manual_brush_tool_drop_down,
    SCATTER5_OT_manual_brush_tool_rotation_set,
    SCATTER5_OT_manual_brush_tool_random_rotation,
    SCATTER5_OT_manual_brush_tool_comb,
    SCATTER5_OT_manual_brush_tool_spin,
    SCATTER5_OT_manual_brush_tool_z_align,
    SCATTER5_OT_manual_brush_tool_scale_set,
    SCATTER5_OT_manual_brush_tool_grow_shrink,
    SCATTER5_OT_manual_brush_tool_object_set,
    
    # # DEBUG -------------------------------------------
    # SCATTER5_OT_manual_brush_tool_debug_3d,
    # SCATTER5_OT_manual_brush_tool_debug_errors,
)


def get_all_tool_classes():
    r = []
    for c in classes:
        if(hasattr(c, 'tool_id')):
            if(c.tool_id != "scatter5.manual_brush_tool_base"):
                r.append(c)
    return r


def get_all_tool_ids():
    r = []
    for c in get_all_tool_classes():
        r.append(c.tool_id)
    return r


def get_tool_class(tool_id):
    for c in get_all_tool_classes():
        if(c.tool_id == tool_id):
            return c
    return None
