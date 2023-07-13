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


class ToolNavigator():
    # inspired from: https://developer.blender.org/diffusion/BA/browse/master/mesh_snap_utilities_line/common_classes.py
    
    @staticmethod
    def to_flag(shift, ctrl, alt, cmd, ):
        return (shift << 0) | (ctrl << 1) | (alt << 2) | (cmd << 3)
    
    def __init__(self, context, ):
        self._move = set()
        self._rotate = set()
        self._zoom = set()
        self._view = set()
        
        # TODO: add `dolly` and look for some others i am forgetting on
        # DONE: test trackpad, should work i think, but test it..
        
        # self._use_ndof = context.preferences.inputs.use_ndof
        # self._ndof = set()
        
        from collections import namedtuple
        view_ops = {
            'view3d.view_camera',
            'view3d.view_axis',
            'view3d.view_orbit',
            'view3d.view_persportho',
            'view3d.view_pan',
            'view3d.view_roll',
            'view3d.view_all',
            'view3d.view_selected',
        }
        # ndof_ops = {
        #     'view3d.ndof_all',
        #     'view3d.ndof_orbit',
        #     'view3d.ndof_orbit_zoom',
        #     'view3d.ndof_pan',
        # }
        
        for key in context.window_manager.keyconfigs.user.keymaps['3D View'].keymap_items:
            if(key.idname == 'view3d.move'):
                self._move.add((self.to_flag(key.shift, key.ctrl, key.alt, key.oskey, ), key.type, key.value, ))
            elif(key.idname == 'view3d.rotate'):
                self._rotate.add((self.to_flag(key.shift, key.ctrl, key.alt, key.oskey, ), key.type, key.value, ))
            elif(key.idname == 'view3d.zoom'):
                if(key.type == 'WHEELINMOUSE'):
                    self._zoom.add((self.to_flag(key.shift, key.ctrl, key.alt, key.oskey, ), 'WHEELUPMOUSE', key.value, key.properties.delta, ))
                elif(key.type == 'WHEELOUTMOUSE'):
                    self._zoom.add((self.to_flag(key.shift, key.ctrl, key.alt, key.oskey, ), 'WHEELDOWNMOUSE', key.value, key.properties.delta, ))
                else:
                    self._zoom.add((self.to_flag(key.shift, key.ctrl, key.alt, key.oskey, ), key.type, key.value, key.properties.delta, ))
            # elif(key.idname in view_ops and not key.type.startswith('NDOF_')):
            elif(key.idname in view_ops):
                if(key.type.startswith('NDOF_')):
                    # NOTE: no way to test it for me, so ignore it..
                    continue
                
                skip = {'__doc__', '__module__', '__slots__', 'bl_rna', 'rna_type', }
                a = set(dir(key.properties))
                ls = list(a - skip)
                Args = namedtuple('Args', ls)
                d = {}
                for v in ls:
                    d[v] = getattr(key.properties, v)
                args = Args(**d)
                self._view.add((key.idname, self.to_flag(key.shift, key.ctrl, key.alt, key.oskey, ), key.type, key.value, args, ))
            # elif(self._use_ndof and key.type.startswith('NDOF_')):
            #     skip = {'__doc__', '__module__', '__slots__', 'bl_rna', 'rna_type', }
            #     a = set(dir(key.properties))
            #     ls = list(a - skip)
            #     Args = namedtuple('Args', ls)
            #     d = {}
            #     for v in ls:
            #         d[v] = getattr(key.properties, v)
            #     args = Args(**d)
            #     self._ndof.add((key.idname, self.to_flag(key.shift, key.ctrl, key.alt, key.oskey, ), key.type, key.value, args, ))
    
    def run(self, context, event, location, ):
        evkey = (self.to_flag(event.shift, event.ctrl, event.alt, event.oskey, ), event.type, event.value, )
        
        # print(evkey)
        #
        # # FIXME: trackpad pan and zoom does not work.. any ideas why?
        # # mainly because in key config there is `ANY` value, but at runtime it is `NOTHING`
        #
        # if(event.type in {'TRACKPADZOOM', 'TRACKPADPAN', }):
        #     evkey = (self.to_flag(event.shift, event.ctrl, event.alt, event.oskey, ), event.type, 'ANY', )
        
        if(evkey in self._move):
            bpy.ops.view3d.move('INVOKE_DEFAULT')
            return True
        
        if(evkey in self._rotate):
            if(location):
                bpy.ops.view3d.rotate_custom_pivot('INVOKE_DEFAULT', pivot=location)
            else:
                bpy.ops.view3d.rotate('INVOKE_DEFAULT', use_cursor_init=True)
            return True
        
        for key in self._zoom:
            if(evkey == key[0:3]):
                if(key[3]):
                    if(location):
                        bpy.ops.view3d.zoom_custom_target('INVOKE_DEFAULT', delta=key[3], target=location)
                    else:
                        bpy.ops.view3d.zoom('INVOKE_DEFAULT', delta=key[3])
                else:
                    bpy.ops.view3d.zoom('INVOKE_DEFAULT')
                return True
        
        for key in self._view:
            if(evkey == key[1:4]):
                opname = key[0].split(".")
                op = getattr(getattr(bpy.ops, opname[0]), opname[1])
                args = key[4]._asdict()
                
                if(key[2] in {'NUMPAD_2', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_8', }):
                    if('angle' in args.keys()):
                        if(args['angle'] == 0.0):
                            args['angle'] = context.preferences.view.rotation_angle * np.pi / 180.0
                
                if(op.poll()):
                    op('INVOKE_DEFAULT', **args)
                    return True
        
        # for key in self._ndof:
        #     if(evkey[:2] == key[1:3]):
        #         opname = key[0].split(".")
        #         op = getattr(getattr(bpy.ops, opname[0]), opname[1])
        #         args = key[4]._asdict()
        #         if(op.poll()):
        #
        #             print(op, args)
        #
        #             r = op('INVOKE_DEFAULT', **args)
        #
        #             print(r)
        #
        #             return True
        
        return False


classes = ()
