'''
Copyright (C) 2022 vfxguide
realvfxguide@gmail.com

Created by VFXGuide

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


bl_info = {
    "name": "OCD",
    "author": "VFXGuide",
    "version": (1, 5, 0),
    "blender": (2, 92, 0),
    "location": "View3D",
    "description": "One click Object Damage",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}


import bpy
from bpy import context
from bpy.types import Operator, Panel, AddonPreferences, PropertyGroup
from bpy.props import FloatProperty, PointerProperty, BoolProperty
from bpy.utils import register_class, unregister_class


def update_func(self, context):
    obj = bpy.context.object
    name = context.object.name + "_temp"
    props = context.scene.dmgamnt
    damage_amount = props.damage_amount
    minM = 0.1
    maxM = 0.94
    xM = (maxM - minM) / 100
    
    minS = 0.95
    maxS = 1.35
    xS = (maxS - minS) / 100
    y = damage_amount
    
    bpy.data.objects[name].modifiers["OCD_Displace"].mid_level = (xM * y) + minM
    bpy.data.objects[name].modifiers["OCD_Displace"].strength = (xS * y + minS) / 10
    
def damage_on(context):
    props = context.scene.dmgamnt
    damage_amount = props.damage_amount
    scale_amount = props.scale_amount
    minM = 0.1
    maxM = 0.94
    xM = (maxM - minM) / 100
    minS = 0.95
    maxS = 1.35
    xS = (maxS - minS) / 100
    y = damage_amount
    
    damaged_col = "OCD_temp"
         
    if damaged_col not in bpy.data.collections:      
        damaged_collection = bpy.context.blend_data.collections.new(name=damaged_col)
        bpy.context.collection.children.link(damaged_collection)
    else:
        damaged_collection = bpy.data.collections[damaged_col]      
    damaged_collection.hide_viewport = True
    damaged_collection.hide_render = True
    
    sourceName = bpy.context.object.name
    sourceMeshName = bpy.data.objects[sourceName].data.name
    bpy.context.object.name = sourceMeshName
    
    sourceName = bpy.context.object.name
    sourceObj = bpy.data.objects[sourceName]
    
    bpy.context.object.name = sourceName
    
    bpy.data.objects[sourceName].data.name = sourceName 
    sourceMeshName = bpy.data.objects[sourceName].data.name
    bpy.ops.object.transform_apply(location = False, rotation = False, scale = True)
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
    bpy.context.object.name = sourceName + "_dmg"
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.edges_select_sharp(sharpness=0.436332)
    bpy.ops.mesh.mark_sharp()
    bpy.ops.object.editmode_toggle()
    damageName = bpy.context.object.name
    damageObj = bpy.data.objects[damageName]
    
    bpy.context.object.name = damageName
    bpy.data.objects[damageName].data.name = damageName
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[sourceName].select_set(True)
    bpy.context.view_layer.objects.active = sourceObj
    bpy.ops.object.delete(use_global=False)

    bpy.data.objects[damageName].select_set(True)
    bpy.context.view_layer.objects.active = damageObj

    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
    bpy.context.object.name = damageName + "_temp"

    targetName = bpy.context.object.name
    targetObj = bpy.data.objects[targetName]
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.object.editmode_toggle()

    for ob in bpy.context.object.users_collection:
        ob.objects.unlink(targetObj)
        
    bpy.data.collections[damaged_col].objects.link(targetObj)

    bpy.context.view_layer.objects.active = targetObj
    
    bpy.context.object.modifiers.new("OCD_bevel", type='BEVEL')
    bpy.context.object.modifiers["OCD_bevel"].width = 0.065
    bpy.context.object.modifiers["OCD_bevel"].use_clamp_overlap = False
    
    bpy.context.object.modifiers.new("OCD_remesh", type='REMESH')
    bpy.context.object.modifiers["OCD_remesh"].voxel_size = 0.035
    bpy.context.object.modifiers["OCD_remesh"].use_smooth_shade = True
    
    bpy.context.object.modifiers.new("OCD_Displace", type='DISPLACE')
    bpy.context.object.modifiers["OCD_Displace"].strength = (xS * y + minS) / 10
    bpy.context.object.modifiers["OCD_Displace"].mid_level = (xM * y) + minM
    
    if "OCD_texture" not in bpy.data.textures:
        OCD_texture = bpy.data.textures.new(name = "OCD_texture", type = 'MUSGRAVE')
        bpy.data.textures["OCD_texture"].noise_basis = 'VORONOI_CRACKLE'
        bpy.data.textures["OCD_texture"].musgrave_type = 'HYBRID_MULTIFRACTAL'
        bpy.data.textures["OCD_texture"].noise_scale = 0.5
    else:     
        OCD_texture = bpy.data.textures["OCD_texture"]
        
    bpy.context.object.modifiers.new("OCD_remesh_02", type='REMESH')
    bpy.context.object.modifiers["OCD_remesh_02"].voxel_size = 0.035
    bpy.context.object.modifiers["OCD_remesh_02"].use_smooth_shade = True
    
    bpy.context.object.modifiers["OCD_Displace"].texture = bpy.data.textures['OCD_texture']
    bpy.context.object.modifiers["OCD_Displace"].texture_coords = 'GLOBAL'
    
    bpy.context.view_layer.objects.active = damageObj
    bpy.context.active_object.select_set(state=True)
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
   
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
    bpy.context.object.modifiers["OCD_Boolean"].solver = 'FAST'
    bpy.context.object.modifiers["OCD_Boolean"].object = targetObj
    bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
    bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

    bpy.context.object.data.use_auto_smooth = True
    bpy.context.object.data.auto_smooth_angle = 1.0472
    
    obj = context.active_object
    if (len(obj.modifiers)):
        vs = 0
        for mod in obj.modifiers:
            if (mod.show_expanded):
                vs += 1
            else:
                vs -= 1
        is_close = False
        if (0 < vs):
            is_close = True
        for mod in obj.modifiers:
            mod.show_expanded = not is_close
    else:
        self.report({'WARNING'}, "Not a single modifier to Expand/Collapse")
        return {'CANCELLED'}

    return {'FINISHED'}
 
def ctrl_damage(context):
    props = context.scene.dmgamnt
    damage_amount = props.damage_amount
    scale_amount = props.scale_amount
    minM = 0.1
    maxM = 0.94
    xM = (maxM - minM) / 100

    minS = 0.95
    maxS = 1.35
    xS = (maxS - minS) / 100
    y = damage_amount
    
    damaged_col = "OCD_temp"
         
    if damaged_col not in bpy.data.collections:      
        damaged_collection = bpy.context.blend_data.collections.new(name=damaged_col)
        bpy.context.collection.children.link(damaged_collection)
    else:
        damaged_collection = bpy.data.collections[damaged_col]      

    damaged_collection.hide_viewport = True
    damaged_collection.hide_render = True
    
    renameName = bpy.context.object.name
    
    sourceName = bpy.context.object.name
    sourceMeshName = bpy.data.objects[sourceName].data.name
    bpy.context.object.name = sourceMeshName
    
    sourceName = bpy.context.object.name
    sourceObj = bpy.data.objects[sourceName]
    
    bpy.context.object.name = sourceName
    
    bpy.data.objects[sourceName].data.name = sourceName 
    
    sourceMeshName = bpy.data.objects[sourceName].data.name
    
    bpy.ops.object.transform_apply(location = False, rotation = False, scale = True)
    
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
    bpy.context.object.name = sourceName + "_dmg"
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.edges_select_sharp(sharpness=0.436332)
    bpy.ops.mesh.mark_sharp()
    bpy.ops.object.editmode_toggle()

    damageName = bpy.context.object.name
    damageObj = bpy.data.objects[damageName]
    
    bpy.context.object.name = damageName
    bpy.data.objects[damageName].data.name = damageName
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[sourceName].select_set(True)
    bpy.context.view_layer.objects.active = sourceObj
    bpy.ops.object.delete(use_global=False)

    bpy.data.objects[damageName].select_set(True)
    bpy.context.view_layer.objects.active = damageObj

    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
    bpy.context.object.name = damageName + "_temp"

    targetName = bpy.context.object.name
    targetObj = bpy.data.objects[targetName]
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.mesh.normals_make_consistent(inside=False)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.object.editmode_toggle()

    for ob in bpy.context.object.users_collection:
        ob.objects.unlink(targetObj)
    
    bpy.data.collections[damaged_col].objects.link(targetObj)

    bpy.context.view_layer.objects.active = targetObj
    
    bpy.context.object.modifiers.new("OCD_bevel", type='BEVEL')
    bpy.context.object.modifiers["OCD_bevel"].width = 0.065
    bpy.context.object.modifiers["OCD_bevel"].use_clamp_overlap = False
    
    bpy.context.object.modifiers.new("OCD_remesh", type='REMESH')
    bpy.context.object.modifiers["OCD_remesh"].voxel_size = 0.035
    bpy.context.object.modifiers["OCD_remesh"].use_smooth_shade = True
    
    bpy.context.object.modifiers.new("OCD_Displace", type='DISPLACE')
    bpy.context.object.modifiers["OCD_Displace"].strength = (xS * y + minS) / 10
    bpy.context.object.modifiers["OCD_Displace"].mid_level = (xM * y) + minM
    
    if "OCD_texture" not in bpy.data.textures:
        OCD_texture = bpy.data.textures.new(name = "OCD_texture", type = 'MUSGRAVE')
        bpy.data.textures["OCD_texture"].noise_basis = 'VORONOI_CRACKLE'
        bpy.data.textures["OCD_texture"].musgrave_type = 'HYBRID_MULTIFRACTAL'
        bpy.data.textures["OCD_texture"].noise_scale = 0.5
    else:     
        OCD_texture = bpy.data.textures["OCD_texture"]

    bpy.context.object.modifiers.new("OCD_remesh_02", type='REMESH')
    bpy.context.object.modifiers["OCD_remesh_02"].voxel_size = 0.035
    bpy.context.object.modifiers["OCD_remesh_02"].use_smooth_shade = True
   
    bpy.context.object.modifiers["OCD_Displace"].texture = bpy.data.textures['OCD_texture']
    bpy.context.object.modifiers["OCD_Displace"].texture_coords = 'GLOBAL'
    
    bpy.context.view_layer.objects.active = damageObj
    bpy.context.active_object.select_set(state=True)
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
    bpy.context.object.modifiers["OCD_Boolean"].solver = 'FAST'
    bpy.context.object.modifiers["OCD_Boolean"].object = targetObj
    bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
    bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

    bpy.context.object.data.use_auto_smooth = True
    bpy.context.object.data.auto_smooth_angle = 1.0472
    
    obj = context.active_object
    if (len(obj.modifiers)):
        vs = 0
        for mod in obj.modifiers:
            if (mod.show_expanded):
                vs += 1
            else:
                vs -= 1
        is_close = False
        if (0 < vs):
            is_close = True
        for mod in obj.modifiers:
            mod.show_expanded = not is_close
    else:
        self.report({'WARNING'}, "Not a single modifier to Expand/Collapse")
        return {'CANCELLED'}
    
    active_obj = context.view_layer.objects.active
    bpy.context.object.modifiers["OCD_Boolean"].solver = 'EXACT'
    
    for mod in active_obj.modifiers:
        if mod.name == "OCD_Boolean":
            bpy.ops.object.modifier_apply(modifier=mod.name)
        if mod.type == "EDGE_SPLIT":
            bpy.ops.object.modifier_remove(modifier=mod.name)
     
    
    bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
    bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
    
    active_obj = bpy.context.view_layer.objects.active
    if  bpy.context.object.active_material is None:
        mat_1 = bpy.data.materials.get("OUTSIDE")
        mat_2 = bpy.data.materials.get("INSIDE")
        if mat_1 is None:
            mat_1 = bpy.data.materials.new(name="OUTSIDE")
            bpy.data.materials["OUTSIDE"].use_nodes = True
        else:
            pass
        if mat_2 is None:
            mat_2 = bpy.data.materials.new(name="INSIDE")
            bpy.data.materials["INSIDE"].use_nodes = True
        else:
            pass
        if active_obj.data.materials:
            active_obj.data.materials[0] = mat_1
            active_obj.data.materials[1] = mat_2
        else:
            active_obj.data.materials.append(mat_1)
            active_obj.data.materials.append(mat_2)
         
        bpy.ops.object.editmode_toggle()

        bpy.context.object.active_material_index = 0
        bpy.ops.object.material_slot_assign()

        bpy.ops.mesh.select_all(action='INVERT')
        
        bpy.context.object.active_material_index = 1
        bpy.ops.object.material_slot_assign()
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.editmode_toggle()
    else:
        mat_2 = bpy.data.materials.get("INSIDE")
        if mat_2 is None:
            mat_2 = bpy.data.materials.new(name="INSIDE")
            bpy.data.materials["INSIDE"].use_nodes = True
        
        bpy.ops.object.material_slot_add()

        obj = bpy.context.object
        idx = obj.active_material_index

        obj.material_slots[idx].material = mat_2
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.object.material_slot_assign()
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.editmode_toggle()
    
    damageName = bpy.context.object.name
    sourceName = damageName[:-4]
    
    bpy.data.meshes[sourceName].use_fake_user = True
    
    collection_name = "OCD_temp"
    collection = bpy.data.collections[collection_name]

    meshes = set()
    for obj in [o for o in collection.objects if o.type == 'MESH']:
        meshes.add( obj.data )
        bpy.data.objects.remove( obj )
    for mesh in [m for m in meshes if m.users == 0]:
        bpy.data.meshes.remove( mesh )
    collection = bpy.data.collections.get(collection_name)
    bpy.data.collections.remove(collection)
    return {'FINISHED'}   

def multobj_damage(context):
    props = context.scene.dmgamnt
    damage_amount = props.damage_amount
    scale_amount = props.scale_amount
    minM = 0.1
    maxM = 0.94
    xM = (maxM - minM) / 100

    minS = 0.95
    maxS = 1.35
    xS = (maxS - minS) / 100
    y = damage_amount
    
    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        damaged_col = "OCD_temp"
             
        if damaged_col not in bpy.data.collections:      
            damaged_collection = bpy.context.blend_data.collections.new(name=damaged_col)
            bpy.context.collection.children.link(damaged_collection)
        else:
            damaged_collection = bpy.data.collections[damaged_col]    
        damaged_collection.hide_viewport = True
        damaged_collection.hide_render = True
        sourceName = bpy.context.object.name
        sourceMeshName = bpy.data.objects[sourceName].data.name
        
        bpy.context.object.name = sourceMeshName
        sourceName = bpy.context.object.name
        sourceObj = bpy.data.objects[sourceName]
        
        bpy.data.objects[sourceName].data.name = sourceName 
        bpy.ops.object.select_all(action='DESELECT')
        
        bpy.data.objects[sourceName].select_set(True)
        bpy.context.view_layer.objects.active = sourceObj
        
        bpy.ops.object.transform_apply(location = False, rotation = False, scale = True)
        
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        
        bpy.context.object.name = sourceName + "_dmg"
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.edges_select_sharp(sharpness=0.436332)
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.editmode_toggle()

        damageName = bpy.context.object.name
        damageObj = bpy.data.objects[damageName]
        
        bpy.context.object.name = damageName
        bpy.data.objects[damageName].data.name = damageName
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[sourceName].select_set(True)
        bpy.context.view_layer.objects.active = sourceObj
        bpy.ops.object.delete(use_global=False)
        
        bpy.data.objects[damageName].select_set(True)
        bpy.context.view_layer.objects.active = damageObj

        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        bpy.context.object.name = damageName + "_temp"
        
        targetName = bpy.context.object.name
        targetObj = bpy.data.objects[targetName]
        
        for ob in bpy.context.object.users_collection:
            ob.objects.unlink(targetObj)
        bpy.data.collections[damaged_col].objects.link(targetObj)
        bpy.context.view_layer.objects.active = targetObj
        
        bpy.context.object.modifiers.new("OCD_bevel", type='BEVEL')
        bpy.context.object.modifiers["OCD_bevel"].width = 0.065
        bpy.context.object.modifiers["OCD_bevel"].use_clamp_overlap = False
        
        bpy.context.object.modifiers.new("OCD_remesh", type='REMESH')
        bpy.context.object.modifiers["OCD_remesh"].voxel_size = 0.035
        bpy.context.object.modifiers["OCD_remesh"].use_smooth_shade = True
        
        bpy.context.object.modifiers.new("OCD_Displace", type='DISPLACE')
        bpy.context.object.modifiers["OCD_Displace"].strength = (xS * y + minS) / 10
        bpy.context.object.modifiers["OCD_Displace"].mid_level = (xM * y) + minM
       
        if "OCD_texture" not in bpy.data.textures:
            OCD_texture = bpy.data.textures.new(name = "OCD_texture", type = 'MUSGRAVE')
            bpy.data.textures["OCD_texture"].noise_basis = 'VORONOI_CRACKLE'
            bpy.data.textures["OCD_texture"].musgrave_type = 'HYBRID_MULTIFRACTAL'
            bpy.data.textures["OCD_texture"].noise_scale = 0.5
        else:     
            OCD_texture = bpy.data.textures["OCD_texture"]
        bpy.context.object.modifiers.new("OCD_remesh_02", type='REMESH')
        bpy.context.object.modifiers["OCD_remesh_02"].voxel_size = 0.035
        bpy.context.object.modifiers["OCD_remesh_02"].use_smooth_shade = True
        bpy.context.object.modifiers["OCD_Displace"].texture = bpy.data.textures['OCD_texture']
        bpy.context.object.modifiers["OCD_Displace"].texture_coords = 'GLOBAL'
        
        bpy.context.view_layer.objects.active = damageObj
        bpy.context.active_object.select_set(state=True)

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.editmode_toggle()
        
        bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
        bpy.context.object.modifiers["OCD_Boolean"].solver = 'EXACT'
        bpy.context.object.modifiers["OCD_Boolean"].object = targetObj
        bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
        bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
        bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

        bpy.context.object.data.use_auto_smooth = True
        bpy.context.object.data.auto_smooth_angle = 1.0472
        
        bpy.ops.object.select_all(action='DESELECT')
        
        bpy.data.objects[damageName].select_set(True)
        bpy.context.view_layer.objects.active = damageObj 
        
        active_obj = bpy.context.view_layer.objects.active
        
        for mod in active_obj.modifiers:
            if mod.name == "OCD_Boolean":
                bpy.ops.object.modifier_apply(modifier=mod.name)
            if mod.type == "EDGE_SPLIT":
                bpy.ops.object.modifier_remove(modifier=mod.name)
       
        bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
        
        active_obj = bpy.context.view_layer.objects.active
        if  bpy.context.object.active_material is None:
            mat_1 = bpy.data.materials.get("OUTSIDE")
            mat_2 = bpy.data.materials.get("INSIDE")
            if mat_1 is None:
                mat_1 = bpy.data.materials.new(name="OUTSIDE")
                bpy.data.materials["OUTSIDE"].use_nodes = True
            else:
                pass
            if mat_2 is None:
                mat_2 = bpy.data.materials.new(name="INSIDE")
                bpy.data.materials["INSIDE"].use_nodes = True
            else:
                pass
            if active_obj.data.materials:
                active_obj.data.materials[0] = mat_1
                active_obj.data.materials[1] = mat_2
            else:
                active_obj.data.materials.append(mat_1)
                active_obj.data.materials.append(mat_2)
            
            bpy.ops.object.editmode_toggle()

            bpy.context.object.active_material_index = 0
            bpy.ops.object.material_slot_assign()

            bpy.ops.mesh.select_all(action='INVERT')
            
            bpy.context.object.active_material_index = 1
            bpy.ops.object.material_slot_assign()
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_sharp()
            bpy.ops.object.editmode_toggle()
        else:
            mat_2 = bpy.data.materials.get("INSIDE")
            if mat_2 is None:
                mat_2 = bpy.data.materials.new(name="INSIDE")
                bpy.data.materials["INSIDE"].use_nodes = True
            
            bpy.ops.object.material_slot_add()

            obj = bpy.context.object
            idx = obj.active_material_index

            obj.material_slots[idx].material = mat_2
            
            bpy.ops.object.editmode_toggle()
            
            bpy.ops.mesh.select_all(action='INVERT')
            
            bpy.ops.object.material_slot_assign()
           
            bpy.ops.mesh.region_to_loop()
                
            bpy.ops.mesh.mark_sharp()
            
            bpy.ops.object.editmode_toggle()
            
       
        damageName = bpy.context.object.name
        sourceName = damageName[:-4]
        
        bpy.data.meshes[sourceName].use_fake_user = True
        
        collection_name = "OCD_temp"
        collection = bpy.data.collections[collection_name]
        
        meshes = set()
        for obj in [o for o in collection.objects if o.type == 'MESH']:
            meshes.add( obj.data )
            bpy.data.objects.remove( obj )

        for mesh in [m for m in meshes if m.users == 0]:
            bpy.data.meshes.remove( mesh )
        
        collection = bpy.data.collections.get(collection_name)
        bpy.data.collections.remove(collection)     
         
def damage_off(context):
    obj = context.active_object
    
    damageName = bpy.context.object.name
    sourceName = damageName[:-4]
    
    bpy.context.object.name = sourceName
    
    if sourceName in bpy.data.meshes:
            mesh = bpy.data.meshes[sourceName]
            bpy.data.meshes.remove(mesh)
            
            bpy.data.objects[sourceName].data.name = sourceName
    
    for mod in obj.modifiers:
        if mod.type == "BOOLEAN":
            bpy.ops.object.modifier_remove(modifier=mod.name)
        if mod.type == "EDGE_SPLIT":
            bpy.ops.object.modifier_remove(modifier=mod.name)
    
        collection_name = "OCD_temp"
        
        if collection_name not in bpy.data.collections:
            pass
        else:
            collection = bpy.data.collections[collection_name]
            meshes = set()
            for obj in [o for o in collection.objects if o.type == 'MESH']:
                meshes.add( obj.data )
                bpy.data.objects.remove( obj )
            for mesh in [m for m in meshes if m.users == 0]:
                bpy.data.meshes.remove( mesh )
        if collection_name not in bpy.data.collections:      
            pass
        else:
            collection = bpy.data.collections.get(collection_name)
            bpy.data.collections.remove(collection)
        
    return {'FINISHED'}

def simple_apply(context):
        
        active_obj = context.view_layer.objects.active
        bpy.context.object.modifiers["OCD_Boolean"].solver = 'EXACT'
        
        for mod in active_obj.modifiers:
            if mod.name == "OCD_Boolean":
                bpy.ops.object.modifier_apply(modifier=mod.name)
            if mod.type == "EDGE_SPLIT":
                bpy.ops.object.modifier_remove(modifier=mod.name)
         
        
        bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
        
        active_obj = bpy.context.view_layer.objects.active
        if  bpy.context.object.active_material is None:
            mat_1 = bpy.data.materials.get("OUTSIDE")
            mat_2 = bpy.data.materials.get("INSIDE")
            if mat_1 is None:
                mat_1 = bpy.data.materials.new(name="OUTSIDE")
                bpy.data.materials["OUTSIDE"].use_nodes = True
            else:
                pass
            
            if mat_2 is None:
                mat_2 = bpy.data.materials.new(name="INSIDE")
                bpy.data.materials["INSIDE"].use_nodes = True
            else:
                pass
            if active_obj.data.materials:
                active_obj.data.materials[0] = mat_1
                active_obj.data.materials[1] = mat_2
            else:
                active_obj.data.materials.append(mat_1)
                active_obj.data.materials.append(mat_2)
                
            bpy.ops.object.editmode_toggle()
            bpy.context.object.active_material_index = 0
            bpy.ops.object.material_slot_assign()

            bpy.ops.mesh.select_all(action='INVERT')
            bpy.context.object.active_material_index = 1
            bpy.ops.object.material_slot_assign()
                
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_sharp()
            bpy.ops.object.editmode_toggle()
        else:
            mat_2 = bpy.data.materials.get("INSIDE")
            if mat_2 is None:
                mat_2 = bpy.data.materials.new(name="INSIDE")
                bpy.data.materials["INSIDE"].use_nodes = True
            
            bpy.ops.object.material_slot_add()

            obj = bpy.context.object
            idx = obj.active_material_index

            obj.material_slots[idx].material = mat_2
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.object.material_slot_assign()
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_sharp()
            bpy.ops.object.editmode_toggle()
            
        damageName = bpy.context.object.name
        sourceName = damageName[:-4]
        
        bpy.data.meshes[sourceName].use_fake_user = True
        
        collection_name = "OCD_temp"

        collection = bpy.data.collections[collection_name]
        meshes = set()
        for obj in [o for o in collection.objects if o.type == 'MESH']:
            meshes.add( obj.data )
            bpy.data.objects.remove( obj )
        for mesh in [m for m in meshes if m.users == 0]:
            bpy.data.meshes.remove( mesh )
        collection = bpy.data.collections.get(collection_name)
        bpy.data.collections.remove(collection)
        return {'FINISHED'}

def ctrl_apply(context):
    
        obj = bpy.context.object
        name = context.object.name + "_temp"
        bpy.data.objects[name].modifiers.new("OCD_Subd", type='SUBSURF')
        
        if "OCD_texture_02" not in bpy.data.textures:
            OCD_texture_02 = bpy.data.textures.new(name = "OCD_texture_02", type = 'CLOUDS')
            bpy.data.textures["OCD_texture_02"].noise_basis = 'BLENDER_ORIGINAL'
            bpy.data.textures["OCD_texture_02"].noise_scale = 0.025
        else:     
            OCD_texture_02 = bpy.data.textures["OCD_texture_02"]
        
        bpy.data.objects[name].modifiers.new("OCD_Displace_02", type='DISPLACE')
        bpy.data.objects[name].modifiers["OCD_Displace_02"].strength = 0.02
        bpy.data.objects[name].modifiers["OCD_Displace_02"].texture = bpy.data.textures['OCD_texture_02']
        bpy.data.objects[name].modifiers["OCD_Displace_02"].texture_coords = 'GLOBAL'
        active_obj = context.view_layer.objects.active
        bpy.context.object.modifiers["OCD_Boolean"].solver = 'EXACT'
        
        for mod in active_obj.modifiers:
            if mod.name == "OCD_Boolean":
                bpy.ops.object.modifier_apply(modifier=mod.name)
            if mod.type == "EDGE_SPLIT":
                bpy.ops.object.modifier_remove(modifier=mod.name)
        
        bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
        
        active_obj = bpy.context.view_layer.objects.active
        if  bpy.context.object.active_material is None:
            mat_1 = bpy.data.materials.get("OUTSIDE")
            mat_2 = bpy.data.materials.get("INSIDE")
            if mat_1 is None:
                mat_1 = bpy.data.materials.new(name="OUTSIDE")
                bpy.data.materials["OUTSIDE"].use_nodes = True
            else:
                pass
            
            if mat_2 is None:
                mat_2 = bpy.data.materials.new(name="INSIDE")
                bpy.data.materials["INSIDE"].use_nodes = True
            else:
                pass
            
            if active_obj.data.materials:
                active_obj.data.materials[0] = mat_1
                active_obj.data.materials[1] = mat_2
            else:
                active_obj.data.materials.append(mat_1)
                active_obj.data.materials.append(mat_2)
                
            bpy.ops.object.editmode_toggle()
            bpy.context.object.active_material_index = 0
            bpy.ops.object.material_slot_assign()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.context.object.active_material_index = 1
            bpy.ops.object.material_slot_assign()
                
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_sharp()
            bpy.ops.object.editmode_toggle()
        else:
            mat_2 = bpy.data.materials.get("INSIDE")
            if mat_2 is None:
                mat_2 = bpy.data.materials.new(name="INSIDE")
                bpy.data.materials["INSIDE"].use_nodes = True
            
            bpy.ops.object.material_slot_add()
            obj = bpy.context.object
            idx = obj.active_material_index
            obj.material_slots[idx].material = mat_2
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.object.material_slot_assign()
                
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_sharp()
            bpy.ops.object.editmode_toggle()
        
        damageName = bpy.context.object.name
        sourceName = damageName[:-4]
        
        bpy.data.meshes[sourceName].use_fake_user = True
        
        collection_name = "OCD_temp"
        collection = bpy.data.collections[collection_name]
        meshes = set()
        for obj in [o for o in collection.objects if o.type == 'MESH']:
            meshes.add( obj.data )
            bpy.data.objects.remove( obj )
        for mesh in [m for m in meshes if m.users == 0]:
            bpy.data.meshes.remove( mesh )
        collection = bpy.data.collections.get(collection_name)
        bpy.data.collections.remove(collection)
        return {'FINISHED'}    

class DamageProps(PropertyGroup):
    damage_amount : FloatProperty(
        name = "Amount",
        default = 50,
        min = 0,
        max = 100,
        subtype = "PERCENTAGE",
        update=update_func,
    )
    
    scale_amount : FloatProperty(
        name = "Scale",
        default = 0.5,
        min = 0.0,
        soft_max = 2,
        subtype = "FACTOR",
    
    )

class OBJECT_OT_damageON(Operator):
    bl_label = "OCD"
    bl_idname = "object.ocd_on"
    bl_description = "hold ctrl for instant damage"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return bpy.context.object.select_get() and bpy.context.object.type == 'MESH' and bpy.context.object.mode == 'OBJECT'
    
    def invoke(self, context, event):
        if event.ctrl or event.oskey:
            ctrl_damage(context)
        else:
            piece = len(bpy.context.selected_objects)
            if piece > 1:
                multobj_damage(context)
            else:
                damage_on(context)
        return {'FINISHED'}
    
class OBJECT_OT_damageOFF(Operator):
    bl_label = "OCD"
    bl_idname = "object.ocd_off"
    bl_description = "cancel the damage"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return bpy.context.object.select_get() and bpy.context.object.type == 'MESH' and bpy.context.object.mode == 'OBJECT'
    my_bool: bpy.props.BoolProperty(name="Toggle Option", default=False)
    
    def execute(self, context):
        damage_off(context)
        return {'FINISHED'}   
        
class OBJECT_OT_apply(Operator):
    bl_label = "Apply all"
    bl_idname = "object.apply_all_mods"
    bl_description = "hold ctrl for more detail"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        objs = context.selected_objects
        return bpy.context.object.mode == 'OBJECT'

        for modifier in obj.modifiers:
            if modifier.type == "BOOLEAN": 
                return True
            else:
                pass
        return False
    
    def invoke(self, context, event):
        if event.ctrl or event.oskey:
            ctrl_apply(context)
        else:
            simple_apply(context)
        
        return {'FINISHED'}
    
class OBJECT_OT_recall(Operator):
    bl_label = "Recall Original"
    bl_idname = "object.recall_original"
    bl_description = "hold ctrl for Recall the original object"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    
    def invoke(self, context, event):
        
        if event.ctrl or event.oskey:
            damageName = bpy.context.object.name
            objlocation = bpy.data.objects[damageName].location
            objrotation = bpy.data.objects[damageName].rotation_euler
            objscale = bpy.data.objects[damageName].scale
            
            bpy.ops.mesh.primitive_plane_add(size=0.1, enter_editmode=False, align='WORLD', location=objlocation, scale=(1, 1, 1))
            ob = bpy.context.object
            me = ob.data
            ob.name = 'donor'
            me.name = 'donor'   
            bpy.context.object.rotation_euler = objrotation
            
            donorName = bpy.context.object.name
            donorObj = bpy.data.objects[donorName]
            
            area = bpy.context.area
            area.type = 'OUTLINER'
                            
            sourceName = damageName[:-4] 
            
            bpy.context.view_layer.objects.active = donorObj
            
            bpy.ops.outliner.id_remap(id_type='MESH', old_id='donor', new_id=sourceName)
            
            area.type = 'VIEW_3D'
            
            for mesh in bpy.data.meshes:
                if mesh.name == 'donor':
                    bpy.data.meshes.remove( mesh )
                    
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
            bpy.context.object.name = sourceName + ".001"
            bpy.context.object.scale = objscale
            
            ob = bpy.data.objects.get("donor") 
            bpy.data.objects.remove(ob)
            return {'FINISHED'}
        else:
            damageName = bpy.context.object.name
            
            bpy.context.object.name = damageName
            bpy.data.objects[damageName].data.name = damageName
            area = bpy.context.area
            area.type = 'OUTLINER'
                    
            sourceName = damageName[:-4] 
            if sourceName not in bpy.data.meshes:
                print ('No mesh to recall')
                pass
            else:
                bpy.ops.outliner.id_remap(id_type='MESH', old_id=damageName, new_id=sourceName)
            
            area.type = 'VIEW_3D'
            bpy.context.object.name = damageName[:-4]
            
            sourceName = damageName[:-4]
            bpy.data.objects[sourceName].data.name = sourceName
            
            if damageName in bpy.data.meshes:
                mesh = bpy.data.meshes[damageName]
                bpy.data.meshes.remove(mesh)
            damageName = sourceName
            obj = context.active_object
            for mod in obj.modifiers:
                if mod.name == "OCD_WNormal":
                    bpy.ops.object.modifier_remove(modifier=mod.name)
            return {'FINISHED'}
        
class OBJECT_PT_OCD_panel(Panel):
    bl_label = 'One Click Damage v1.5'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OCD'
    
    try:
        objName = bpy.context.object.name
    except: 
        pass
    
    def draw(self, context):
        layout = self.layout
        
        obj = bpy.context.object
        props = context.scene.dmgamnt
        damage_amount = props.damage_amount
        
        if context.active_object is None:
            print ('None')
        else:
            targetNameProp = obj.name + '_temp'
        
            row = self.layout.column()
            row.scale_y = 2.0
            
            if ('_dmg' not in obj.name) :
                row.operator("object.ocd_on", text = 'Make Damage', depress = True)
            else:
                pass
            
            for modifier in obj.modifiers:
                if modifier.name == 'OCD_Boolean':
                    row.operator("object.ocd_off", text = 'Cancel', depress = False)
            
            for modifier in obj.modifiers:
                if modifier.name == 'OCD_Boolean':
                    col = self.layout.column()
                    col.prop(bpy.data.textures['OCD_texture'], 'noise_scale', text = 'Scale')
                    col.prop(props, "damage_amount")
                    col.label(text=" Noise type") 
                    col.prop(bpy.data.textures["OCD_texture"], 'type', text = '')
                    col = self.layout.column()
                    col.operator("object.apply_all_mods", text = "Apply")
                else:
                    pass
                
            for modifier in obj.modifiers: 
                if modifier.name == 'OCD_WNormal':
                    row.enabled = ('_dmg.' not in obj.name)
                    row.operator("object.recall_original", text = "Recall")

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

#---Classes register list
classes = [
    DamageProps,
    OBJECT_OT_damageON,
    OBJECT_OT_damageOFF,
    OBJECT_OT_apply,
    OBJECT_OT_recall,
    OBJECT_PT_OCD_panel,
]

def register():
    for cl in classes:
       register_class(cl)
    bpy.types.Scene.dmgamnt = PointerProperty(type = DamageProps)   
       
def unregister():
    for cl in reversed(classes):
        unregister_class(cl)



if __name__ == "__main__":
    register()