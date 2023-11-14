import bpy
import os
from .. functions import save_load_asset_list

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class ASSET_SKETCHER_OT_ImportAssetLib(Operator, ImportHelper):
    bl_idname = "asset_sketcher.import_asset_lib"
    bl_label = "Import Asset Lib"
    bl_description = ""
    bl_options = {"REGISTER"}
    
    filename_ext = ".blend"
    link: BoolProperty(name="Link Assets",description="Link Assets to other Scene, otherwise they will be appended.", default=True)
    relative_path: BoolProperty(name="Relative Path",description="Path to linked Assets will be set relative.", default=True)
    append_assets: BoolProperty(name="Append Asset List",description="If checked, the Asset List will be appended to existing. If not checked, it will override existing Asset List.", default=True)
    filter_glob: StringProperty(default="*.blend",options={'HIDDEN'},maxlen=255)
    
    @classmethod
    def poll(cls, context):
        return True

    def string_in_array(self, text, array):
        for item in array:
            if text in item:
                return True
        return False

    def execute(self, context):
        wm = context.window_manager
        asset_sketcher = wm.asset_sketcher
        
        current_blend_name = os.path.basename(context.blend_data.filepath)
        if current_blend_name != '' and current_blend_name in self.filepath:
            self.report({'WARNING'}, "You cannot import Asset Lib from opened Blendfile.")
            return {'FINISHED'}
        

        scenes_in_blendfile = []
        with bpy.data.libraries.load(self.filepath,link=self.link,relative=self.relative_path) as (data_from,data_to):
            data_to.scenes = data_from.scenes
            scenes_in_blendfile = data_from.scenes[:]
        scene = None
        for i, sc in enumerate(bpy.data.scenes):
            if i > 0:
                if len(sc.asset_sketcher.asset_list) > 0:
                    scene = sc

        if scene == None:
            self.report({'WARNING'}, "No Assets found.")
            return{"FINISHED"}
        clean_collection_props = not self.append_assets            
        save_load_asset_list(context,mode="IMPORT",src_custom=scene.asset_sketcher,dst_custom=bpy.context.window_manager.asset_sketcher,clean_collection_props=clean_collection_props)
        bpy.data.scenes.remove(scene)
        
        if "AssetSketcher_lib" not in bpy.data.scenes:
            lib_scene = bpy.data.scenes.new("AssetSketcher_lib")
        else:
            lib_scene = bpy.data.scenes["AssetSketcher_lib"]
                
        for asset_item in asset_sketcher.asset_list:
            if asset_item.type == "OBJECT":
                if asset_item.name in bpy.data.objects and asset_item.name not in lib_scene.objects:
                    lib_scene.collection.objects.link(bpy.data.objects[asset_item.name])
            elif asset_item.type == "GROUP":
                for obj in asset_item.group_objects:
                    if obj.name in bpy.data.objects and obj.name not in lib_scene.objects:
                       lib_scene.collection.objects.link(bpy.data.objects[obj.name])
            elif asset_item.type == "EMPTY":
                if asset_item.name in bpy.data.objects and asset_item.name not in lib_scene.objects:
                    lib_scene.collection.objects.link(bpy.data.objects[asset_item.name])
                    for obj in bpy.data.objects[asset_item.name].instance_collection.objects:
                        if obj.name not in lib_scene.objects:
                            lib_scene.collection.objects.link(obj)

        # cleanup linked scenes
        for scene in bpy.data.scenes:
            if scene.library != None and self.string_in_array(scene.name, scenes_in_blendfile):
                bpy.data.scenes.remove(scene, do_unlink=True)
        return {'FINISHED'}
