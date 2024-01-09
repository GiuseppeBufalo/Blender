import bpy
import numpy as np
import math

from mathutils import Matrix, Vector, Quaternion

from .. utils import addon
from .. utils import objects


def find(ob):
    if not ob:
        return None

    ob = bpy.data.objects.get(ob) 
    if not ob:
        return None
    
    return ob

def retrieve(context, ob):
    if not ob:
        return None

    ob = context.scene.objects.get(ob) 
    if not ob:
        return None
    
    return ob


def clear_objects(self, context, curve, i):
    # This function is used as a cleanup utility to remove any previous mesh/profile 
    # before a new one is added to the curve. Different cleanups are required for different modes.

    # We can still use mode and index because 
    # their new values have NOT been assigned yet.
    mode = curve['mode']
    index = curve['index']

    if mode == 1 and index == -1:
        curve.data.bevel_depth = 0
        curve.data.bevel_object = None

    else:
        ob = objects.retrieve(context, curve.get('geo'))
        if ob is not None:
            cap1 = ob.get('cap1')
            cap2 = ob.get('cap2')

        if cap1:
            del ob['cap1']
            cap1 = objects.find(cap1)
            if cap1:
                if cap1.name == 'CapStart':
                    if addon.debug():
                        print('\n')
                        print('YOU\'RE DELETING THE SOURCE STUPID\n\n')
                    self.report({'ERROR'}, 'Message')
                if addon.debug():
                    print(f'DELETING {cap1.name}')
                hard_delete(cap1)

        if cap2:
            del ob['cap2']
            cap2 = objects.find(cap2)
            if cap2:
                if addon.debug():
                    print(f'DELETING {cap2.name}')
                hard_delete(cap2)

        hard_delete(ob)     # Safe to perform even if the object is None
        # hard_delete(cap1)
        # hard_delete(cap2)

        if curve.get('geo'):
            del curve['geo']


def duplicate_object(context, obj, suffix='', linked=False, coll=None, select=True, hidden=False):
    new_obj = obj.copy()

    if suffix:
        new_obj.name = obj.name + suffix

    if not linked:
        new_obj.data = obj.data.copy()
        if suffix:
            new_obj.data.name = obj.data.name + suffix

    if coll is None:
        if not hidden:
            context.collection.objects.link(new_obj)    # Links to current collection.
    elif type(coll) == str:
        bpy.data.collections[coll].objects.link(new_obj)
    else:
        coll.objects.link(new_obj)

    make_materials_local(target_obj=new_obj)

    if new_obj.type == 'CURVE':
        new_obj['type'] = 'profile'

    if select:
        if not hidden:
            new_obj.select_set(True)

    if addon.debug():
        print(f'Source OBJ: {obj.name}')
        print(f'Instance OBJ: {new_obj.name} \n')

    return new_obj


def make_materials_local(target_obj):
    if target_obj is None:
        return

    target_materials = target_obj.data.materials
    # target_materials = [mat for mat in target_obj.data.materials if mat is not None]  # Alt method

    if not target_materials:
        return

    for i, mat in enumerate(target_materials):
        if mat is None: # an Empty material slot
            continue
        
        if mat.library is None:
            continue
        
        local_mat = bpy.data.materials.get((mat.name, None), None)

        if local_mat is None:
            mat.make_local()
            continue
        
        target_obj.data.materials[i] = local_mat


def duplicate_mesh(mesh, dup_name=None, suffix=''):
    new_mesh = mesh.copy()

    if dup_name is None:
        new_mesh.name = mesh.name + suffix
    else:
        new_mesh.name = dup_name + suffix

    return new_mesh


def delete_object(obj=None, name=None):
    # bpy.data.meshes.remove(obj.data)
    # bpy.data.curves.remove(data)

    if obj: 
        bpy.data.objects.remove(obj, do_unlink=True)

    elif name:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    
    if addon.debug(): print('No Object was deleted')

    return


def hard_delete(ob):
    '''Deleting the object data from the blend file will also remove the data and object from the scene'''

    if ob is None:
        # print('Nothing to delete')
        return

    if ob.type == 'CURVE':
        # print(f'deleting {ob.name}')
        bpy.data.curves.remove(ob.data)

    elif ob.type == 'MESH':
        # print(f'deleting {ob.name}')
        bpy.data.meshes.remove(ob.data)


def delete_object_data(obj=None, name=None):
    # bpy.data.meshes.remove(obj.data)
    # bpy.data.curves.remove(data)
    if obj: 
        if obj.type == 'CURVE':
            bpy.data.curves.remove(obj.data)

    elif name:
        # bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        if obj.type == 'CURVE':
            bpy.data.curves.remove(bpy.data.objects[name].data,)
    
    if addon.debug(): print('No Data was deleted')
    
    return


def set_master_curve(context, ob=None):
    # Defines the Master Curve, even if kitbash is selected instead of a curve.

    # active = curve if curve else context.object

    if ob.type == 'CURVE':
        if ob.get('type') == 'profile':
           master_curve = bpy.data.objects[ob['curve']]
        else:
           master_curve = ob

    elif ob.type == 'MESH':
       master_curve = bpy.data.objects[ob['curve']]
    
    if addon.debug():
        print(f'Set Master Curve: {master_curve}')
    
    return master_curve


def get_master_kitbash(context, master_curve):
    '''Returns the Master Curve's kitbash if possible, otherwise returns the master Curve.
    References to non-existant objects should have been cleared by this point.'''

    ob = objects.retrieve(context, master_curve.get('geo'))
    active = master_curve if ob is None else ob

    if addon.debug():
        print(f'Get Adaptive Master: {active} \n')
    
    return active


def purge_orphan_data(self):
    for mode_objects in self.all_source_objects:
        for ob in mode_objects:
            hard_delete(ob)
#     # Optional Alternative:
#     # bpy.ops.outliner.orphans_purge()

#     objects = self.imported_objects
#     object_data = list()

#     # Store a reference to the data before we remove the object.
#     for ob in self.imported_objects:
#         object_data.append(ob.data)
#         bpy.data.objects.remove(ob)
    
#     for data in object_data:
#         try:
#             bpy.data.meshes.remove(data)
#         except TypeError:
#             bpy.data.curves.remove(data)

