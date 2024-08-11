import bpy

import os.path

from ..util.data.nodegroups import append_object

class CSDF_OT_ADDBOUNDS(bpy.types.Operator):
    """Adds Bounds visualization object"""
    bl_idname = 'csdf.addbounds'
    bl_label = 'Add Bounds'  

    @classmethod
    def poll(cls, context):
        if not context.scene.objects.get("CSDF_Meshing_Bounds"):
            return True
        return False
    
    def execute(self, context):

        corner01_name = "CSDF_Meshing_Corner01"
        corner02_name = "CSDF_Meshing_Corner02"
        bounds_name = "CSDF_Meshing_Bounds"


        # based on https://blender.stackexchange.com/questions/220072/check-using-name-if-a-collection-exists-in-blend-is-linked-to-scene
        bounds_Coll = bpy.data.collections.get("CSDF Bounds")
        if not bounds_Coll:
            bounds_Coll = bpy.data.collections.new("CSDF Bounds")
            bounds_Coll.color_tag = 'COLOR_05'
            bpy.context.scene.collection.children.link(bounds_Coll)


        # check if geonodes tree already exists, and delete it
        # then check if corners already exist, and delete them
        geo_tree_name = "CSDF_Meshing_Bounds"
        if geo_tree_name in bpy.data.node_groups:
            geo_tree = bpy.data.node_groups[geo_tree_name]
            bpy.data.node_groups.remove(geo_tree)
        
        if corner01_name in bpy.data.objects:
            obj = bpy.data.objects[corner01_name]
            bpy.data.objects.remove(obj)
        if corner02_name in bpy.data.objects:
            obj = bpy.data.objects[corner02_name]
            bpy.data.objects.remove(obj)

        bounds_obj_path = os.path.join('resources', 'blend', 'CSDF_Meshing.blend')
        objects = append_object(bounds_obj_path, "CSDF_Meshing_", bounds_Coll)
        if objects:

            Corner01 = [obj for obj in objects if obj.name == corner01_name][0]
            Corner02 = [obj for obj in objects if obj.name == corner02_name][0]
            Bounds = [obj for obj in objects if obj.name == bounds_name][0]

            Corner01.parent = Bounds
            Corner02.parent = Bounds

            Bounds.lock_location = [True, True, True] # no really, just don't
            Bounds.lock_rotation = [True, True, True] # I'm no longer asking
            Bounds.lock_scale = [True, True, True] # Stop
            Bounds.lock_rotation_w = True # Bad blender user

            Bounds.show_in_front = True

        return {'FINISHED'}



class CSDF_OT_CLEANMESH(bpy.types.Operator):
    """Merges meshed chunks, and remeshes them to get rid of artifacts"""
    bl_idname = 'csdf.cleanmesh'
    bl_label = 'Clean up Mesh Chunks'  

    
    def execute(self, context):

        scene = context.scene
        CSDF_meshingprops = scene.csdf_meshingprops

        bpy.ops.object.select_all(action='DESELECT')

        Mesh_Coll = bpy.data.collections.get("CSDF Mesh")

        if not Mesh_Coll:
            self.report({'ERROR'}, "Couldn't find CSDF Mesh collection that contains chunks. \nDid you rename it?")
            return {'CANCELLED'}
        
        if len(Mesh_Coll.all_objects) == 0:
            self.report({'ERROR'}, "No chunks to cleanup and merge in CSDF Mesh collection. \nDid you move them?")
            return {'CANCELLED'}        



        chunk_base = Mesh_Coll.all_objects[0]

        with context.temp_override(active_object=chunk_base, selected_editable_objects=Mesh_Coll.all_objects):
            bpy.ops.object.join()
        
        remesh_mod = chunk_base.modifiers.new("Voxel Remesh", 'REMESH')
        remesh_mod.voxel_size = 1/CSDF_meshingprops.triangle_density
        remesh_mod.use_smooth_shade = True

        smooth_mod = chunk_base.modifiers.new("Smooth", 'SMOOTH')
        smooth_mod.factor = 1
        smooth_mod.iterations = 20

        decimate_mod = chunk_base.modifiers.new("Decimate", 'DECIMATE')
        decimate_mod.ratio = 0.2



        context.view_layer.objects.active = chunk_base
        chunk_base.select_set(True)

        self.report({'INFO'}, "Meshing result cleaned up. Remesh Density and Smoothing can be adjusted in the modifiers panel")

        return {'FINISHED'}
