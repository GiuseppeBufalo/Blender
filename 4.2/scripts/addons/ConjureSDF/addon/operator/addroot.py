import bpy

from bpy.types import Operator



# add object W_Plane
class CSDF_OT_ADD_ROOT(Operator):
    """Add CSDF Root object. Holds all scene info for CSDF primitives"""
    bl_idname = "mesh.csdf_addroot"
    bl_label = "CSDF"

    @classmethod
    def poll(cls, context):
        if context.scene.objects.get("CSDF Root"):
            return False
        return True

    def execute(self, context):

        SDF_Coll = bpy.data.collections.get("CSDF Primitives")
        if not SDF_Coll:
            SDF_Coll = bpy.data.collections.new("CSDF Primitives")
            SDF_Coll.color_tag = 'COLOR_04'
            bpy.context.scene.collection.children.link(SDF_Coll)

        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

        root = bpy.context.active_object
        root['CSDF_Root'] = True
        root.name = "CSDF Root"

        for col in root.users_collection:
            col.objects.unlink(root)
        SDF_Coll.objects.link(root)

        csdfData = root.csdfData
        csdfData.is_root = True

        root.hide_select = True # just don't touch the root
        root.lock_location = [True, True, True] # no really, just don't
        root.lock_rotation = [True, True, True] # I'm no longer asking
        root.lock_scale = [True, True, True] # Stop
        root.lock_rotation_w = True # Bad blender user

        setup_CSDF_Scene_Nodes(root)
        setup_CSDF_OutlinerUI_Tree()

        return {'FINISHED'}


def setup_CSDF_Scene_Nodes(root):
    csdf_scene_nodes = bpy.context.scene.CSDF_SceneNodes
    csdf_scene_nodes.clear()

    # never moves or changes
    node = csdf_scene_nodes.add()
    node.set_obj(root)
    node.selfIndex = 0

def setup_CSDF_OutlinerUI_Tree():
    treeList = bpy.context.scene.CSDF_OutlinerTree
    treeList.clear()    
