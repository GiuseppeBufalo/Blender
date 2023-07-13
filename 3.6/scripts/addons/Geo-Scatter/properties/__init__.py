

#####################################################################################################
#
# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
################################# o888o ##############################################################

"""

>>>DEPENDENCIES Precised below

>>>NOTE that in this module you'll find all properties registration of addon_prefs/window_manager/object/scene
   Some are stored in this module, some are not. See below, if `import from ..` 

>>>THERE ARE MORE PROPERTIES TOO! :

   -bpy.types.WindowManager.scatter5_bitmap_library ->Dynamic Enum
   -bpy.types.WindowManager.scatter5_preset_gallery ->Dynamic Enum
   -bpy.types.Texture.scatter5 

""" 

import bpy 

from . import main_settings
from . import addon_settings
from . import gui_settings
from . import manual_settings
from . import mask_settings
from . import ops_settings
from . import particle_settings


# ooooooooo.
# `888   `Y88.
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88(  "8
#  888          888     888   888  888   888 `"Y88b.
#  888          888     888   888  888   888 o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                  888
#                                 o888o

######### PER ADDON

#bpy.context.preferences.addons["Geo-Scatter"].preferences
from . addon_settings import SCATTER5_AddonPref
#bpy.context.preferences.addons["Geo-Scatter"].preferences.blend_environment_paths
from . addon_settings import SCATTER5_PR_blend_environment_paths

######### PER OBJECT

#bpy.context.object.scatter5
from . main_settings import SCATTER5_PR_Object
#bpy.context.object.scatter5.particle_systems
from . particle_settings import SCATTER5_PR_particle_systems
#bpy.context.object.scatter5.mask_systems
from . mask_settings import SCATTER5_PR_procedural_vg

######### PER SCENE 

#bpy.context.scene.scatter5
from . main_settings import SCATTER5_PR_Scene

#bpy.context.scene.scatter5.operators
from . ops_settings import SCATTER5_PR_operators
#bpy.context.scene.scatter5.operators.save_operator_preset
from . ops_settings import SCATTER5_PR_save_operator_preset
#bpy.context.scene.scatter5.operators.save_biome_to_disk_dialog
from . ops_settings import SCATTER5_PR_save_biome_to_disk_dialog
#bpy.context.scene.scatter5.operators.generate_thumbnail
from . ops_settings import SCATTER5_PR_generate_thumbnail
#bpy.context.scene.scatter5.operators.create_operators
from . ops_settings import SCATTER5_PR_creation_operators
#bpy.context.scene.scatter5.operators.xxx.instances/surfaces
from . ops_settings import SCATTER5_PR_objects
#bpy.context.scene.scatter5.operators.add_psy_preset
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_preset
#bpy.context.scene.scatter5.operators.add_psy_density
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_density
#bpy.context.scene.scatter5.operators.add_psy_manual
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_manual
#bpy.context.scene.scatter5.operators.add_psy_modal
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_modal
#bpy.context.scene.scatter5.operators.load_biome
from . ops_settings import SCATTER5_PR_creation_operator_load_biome

#bpy.context.scene.scatter5.uuids
from . main_settings import SCATTER5_PR_uuids

#bpy.context.scene.scatter5.manual
# from . manual_settings import SCATTER5_PR_scene_manual
#bpy.context.scene.scatter5.manual.lambda_brushes
# from . manual_settings import (
#     SCATTER5_manual_default_brush,
#     SCATTER5_manual_default_brush_2d,
#     SCATTER5_manual_dot_brush,
#     SCATTER5_manual_spatter_brush,
#     SCATTER5_manual_pose_brush,
#     SCATTER5_manual_path_brush,
#     SCATTER5_manual_chain_brush,
#     SCATTER5_manual_spray_brush,
#     SCATTER5_manual_spray_aligned_brush,
#     SCATTER5_manual_move_brush,
#     SCATTER5_manual_smooth_brush,
#     SCATTER5_manual_eraser_brush,
#     SCATTER5_manual_dilute_brush,
#     # SCATTER5_manual_rotation_align_brush,
#     # SCATTER5_manual_rotation_set_brush,
#     # SCATTER5_manual_rotation_random_brush,
#     SCATTER5_manual_rotation_brush,
#     # SCATTER5_manual_scale_set_brush,
#     # SCATTER5_manual_scale_random_brush,
#     SCATTER5_manual_scale_brush,
#     # SCATTER5_manual_scale_grow_brush,
#     # SCATTER5_manual_scale_shrink_brush,
#     SCATTER5_manual_scale_grow_shrink_brush,
#     SCATTER5_manual_comb_brush,
#     SCATTER5_manual_spin_brush,
#     SCATTER5_manual_object_brush,
#     SCATTER5_manual_random_rotation_brush,
#     SCATTER5_manual_z_align_brush,
#     SCATTER5_manual_drop_down_brush,
#     SCATTER5_manual_manipulator,
#     SCATTER5_manual_free_move_brush,
#     SCATTER5_manual_lasso_fill,
#     SCATTER5_manual_physics_brush,
#     SCATTER5_manual_physics_brush_object_properties,
#     # SCATTER5_manual_debug_brush_2d,
#     )
# ------------------------------------------------------------------ manual 2.0 >>>
from .manual_settings import (
    SCATTER5_PR_manual_brush_tool_default,
    SCATTER5_PR_manual_brush_tool_dot,
    SCATTER5_PR_manual_brush_tool_spatter,
    SCATTER5_PR_manual_brush_tool_pose,
    SCATTER5_PR_manual_brush_tool_path,
    SCATTER5_PR_manual_brush_tool_chain,
    SCATTER5_PR_manual_brush_tool_spray,
    SCATTER5_PR_manual_brush_tool_spray_aligned,
    SCATTER5_PR_manual_brush_tool_lasso_fill,
    SCATTER5_PR_manual_brush_tool_clone,
    SCATTER5_PR_manual_brush_tool_eraser,
    SCATTER5_PR_manual_brush_tool_dilute,
    SCATTER5_PR_manual_brush_tool_smooth,
    SCATTER5_PR_manual_brush_tool_move,
    SCATTER5_PR_manual_brush_tool_rotation_set,
    SCATTER5_PR_manual_brush_tool_random_rotation,
    SCATTER5_PR_manual_brush_tool_comb,
    SCATTER5_PR_manual_brush_tool_spin,
    SCATTER5_PR_manual_brush_tool_z_align,
    SCATTER5_PR_manual_brush_tool_scale_set,
    SCATTER5_PR_manual_brush_tool_grow_shrink,
    SCATTER5_PR_manual_brush_tool_object_set,
    SCATTER5_PR_manual_brush_tool_drop_down,
    SCATTER5_PR_manual_brush_tool_free_move,
    SCATTER5_PR_manual_brush_tool_manipulator,
    SCATTER5_PR_scene_manual,
)
# ------------------------------------------------------------------ manual 2.0 <<<
#bpy.context.scene.scatter5.sync_channels
from .. scattering.synchronize import SCATTER5_PR_sync_channels
#bpy.context.scene.scatter5.sync_channels[].members
from .. scattering.synchronize import SCATTER5_PR_channel_members

######### PER WINDOW_MANAGER

#bpy.context.window_manager.scatter5
from . main_settings import SCATTER5_PR_Window
#bpy.context.window_manager.scatter5.library
from .. ui.biome_library import SCATTER5_PR_library
#bpy.context.window_manager.scatter5.folder_navigation
from .. ui.biome_library import SCATTER5_PR_folder_navigation
#bpy.context.window_manager.scatter5.ui
from . gui_settings import SCATTER5_PR_ui
#bpy.context.window_manager.scatter5.ui.popovers_args
from . gui_settings import SCATTER5_PR_popovers_arg
from . gui_settings import SCATTER5_PR_popovers_dummy_class

######### PER NODEGROUP

#bpy.context.node_tree.scatter5
from . main_settings import SCATTER5_PR_node_group
#bpy.context.node_tree.scatter5.texture
from ..scattering.texture_datablock import SCATTER5_PR_node_texture


# ooooooooo.                        
# `888   `Y88.                      
#  888   .d88'  .ooooo.   .oooooooo 
#  888ooo88P'  d88' `88b 888' `88b  
#  888`88b.    888ooo888 888   888  
#  888  `88b.  888    .o `88bod8P'  
# o888o  o888o `Y8bod8P' `8oooooo.  
#                        d"     YD
#                        "Y88888P'


#Children types children aways first! 
classes = (
            
    SCATTER5_PR_blend_environment_paths,
    SCATTER5_AddonPref,

    SCATTER5_PR_folder_navigation, 
    SCATTER5_PR_library, 
    SCATTER5_PR_popovers_dummy_class,
    SCATTER5_PR_popovers_arg,
    SCATTER5_PR_ui,
    SCATTER5_PR_Window,

    SCATTER5_PR_node_texture,
    SCATTER5_PR_node_group,

    # SCATTER5_manual_default_brush,
    # SCATTER5_manual_default_brush_2d,
    # SCATTER5_manual_dot_brush,
    # SCATTER5_manual_spatter_brush,
    # SCATTER5_manual_pose_brush,
    # SCATTER5_manual_path_brush,
    # SCATTER5_manual_chain_brush,
    # SCATTER5_manual_spray_brush,
    # SCATTER5_manual_spray_aligned_brush,
    # SCATTER5_manual_move_brush,
    # SCATTER5_manual_smooth_brush,
    # SCATTER5_manual_eraser_brush,
    # SCATTER5_manual_dilute_brush,
    # # SCATTER5_manual_rotation_align_brush,
    # # SCATTER5_manual_rotation_set_brush,
    # # SCATTER5_manual_rotation_random_brush,
    # SCATTER5_manual_rotation_brush,
    # # SCATTER5_manual_scale_set_brush,
    # # SCATTER5_manual_scale_random_brush,
    # SCATTER5_manual_scale_brush,
    # # SCATTER5_manual_scale_grow_brush,
    # # SCATTER5_manual_scale_shrink_brush,
    # SCATTER5_manual_scale_grow_shrink_brush,
    # SCATTER5_manual_comb_brush,
    # SCATTER5_manual_spin_brush,
    # SCATTER5_manual_object_brush,
    # SCATTER5_manual_random_rotation_brush,
    # SCATTER5_manual_z_align_brush,
    # SCATTER5_manual_drop_down_brush,
    # SCATTER5_manual_manipulator,
    # SCATTER5_manual_free_move_brush,
    # # SCATTER5_manual_debug_brush_2d,
    # SCATTER5_manual_lasso_fill,
    # SCATTER5_manual_physics_brush,
    # SCATTER5_manual_physics_brush_object_properties,
    #
    # SCATTER5_PR_scene_manual,
    
    # ------------------------------------------------------------------ manual 2.0 >>>
    SCATTER5_PR_manual_brush_tool_default,
    SCATTER5_PR_manual_brush_tool_dot,
    SCATTER5_PR_manual_brush_tool_spatter,
    SCATTER5_PR_manual_brush_tool_pose,
    SCATTER5_PR_manual_brush_tool_path,
    SCATTER5_PR_manual_brush_tool_chain,
    SCATTER5_PR_manual_brush_tool_spray,
    SCATTER5_PR_manual_brush_tool_spray_aligned,
    SCATTER5_PR_manual_brush_tool_lasso_fill,
    SCATTER5_PR_manual_brush_tool_clone,
    SCATTER5_PR_manual_brush_tool_eraser,
    SCATTER5_PR_manual_brush_tool_dilute,
    SCATTER5_PR_manual_brush_tool_smooth,
    SCATTER5_PR_manual_brush_tool_move,
    SCATTER5_PR_manual_brush_tool_rotation_set,
    SCATTER5_PR_manual_brush_tool_random_rotation,
    SCATTER5_PR_manual_brush_tool_comb,
    SCATTER5_PR_manual_brush_tool_spin,
    SCATTER5_PR_manual_brush_tool_z_align,
    SCATTER5_PR_manual_brush_tool_scale_set,
    SCATTER5_PR_manual_brush_tool_grow_shrink,
    SCATTER5_PR_manual_brush_tool_object_set,
    SCATTER5_PR_manual_brush_tool_drop_down,
    SCATTER5_PR_manual_brush_tool_free_move,
    SCATTER5_PR_manual_brush_tool_manipulator,
    SCATTER5_PR_scene_manual,
    # ------------------------------------------------------------------ manual 2.0 <<<
    
    SCATTER5_PR_save_operator_preset,
    SCATTER5_PR_save_biome_to_disk_dialog,
    SCATTER5_PR_generate_thumbnail,
    SCATTER5_PR_objects,
    SCATTER5_PR_creation_operators,
    SCATTER5_PR_creation_operator_add_psy_preset,
    SCATTER5_PR_creation_operator_add_psy_density,
    SCATTER5_PR_creation_operator_add_psy_manual,
    SCATTER5_PR_creation_operator_add_psy_modal,
    SCATTER5_PR_creation_operator_load_biome,

    SCATTER5_PR_operators,

    SCATTER5_PR_channel_members,
    SCATTER5_PR_sync_channels,
    SCATTER5_PR_uuids,

    SCATTER5_PR_Scene,

    SCATTER5_PR_procedural_vg,
    SCATTER5_PR_particle_systems,

    SCATTER5_PR_Object,

    )


def all_classes():
    """find all classes loaded in our plugin"""

    import sys, inspect

    ret = set()
    for mod_path,mod in sys.modules.copy().items(): #for all modules in sys.modules
        if (mod_path.split('.')[0]=="Geo-Scatter"): #filer module that isn't ours
            for o in mod.__dict__.values(): #for each objects found in module find & return class
                if (inspect.isclass(o)):
                    if (o not in ret): #guarantee unique values
                        ret.add(o)
                        yield o

def all_classes_with_enums():
    """find all classes who detain blender enum properties in their annotation space"""

    for cls in all_classes():
        if (hasattr(cls,"__annotations__")):
            if ("<built-in function EnumProperty>" in [repr(a.function) for a in cls.__annotations__.values() if hasattr(a,"function") ]):
                yield cls

def patch_custom_enum_icons(cls, patchsignal="INIT_ICON:"):
    """because properties are defined in __annotation__ space, we cannot get custom icon value as icons are not registered yet
    thus we need to re-sample the icons right before registering the PropertyGroup, this function will patch EnumProperty when needed"""

    #ignore operators, we can't patch them it seems????? 
    #might be very problematic if we want operators with custom icons, problem to be resolve me later if needed
    if ("_OT_" in cls.__name__): #relying on names, my naming system is consistent, is yours too? it should
        #print("ignored due to being an operator : ",cls)
        return None

    #ignore classes already registered
    if ( (hasattr(cls, "is_registered")) and (cls.is_registered) ):
        #print("ignored due to already being registered : ",cls)
        return None

    from .. resources.icons import cust_icon

    def patch_needed(itm):
        """check if this item need to be patched, if the icon element of the item has a patchsignal"""
        return (type(itm[3]) is str) and itm[3].startswith(patchsignal)

    def patch_item(itm):
        """patch icon element of an item if needed"""
        if (patch_needed(itm)):
            return tuple(cust_icon(e.replace(patchsignal,"")) if (type(e) is str and e.startswith(patchsignal)) else e for e in itm)
        return itm

    #for all EnumProperties initialized in cls.annotation space, 
    #that have more than 3 element per items 
    #& have at least one icon str value with the patch signal

    for propname,prop in [(propname,prop) for propname,prop in cls.__annotations__.items() 
               if (repr(prop.function)=="<built-in function EnumProperty>")
               and (len(prop.keywords["items"][0])>3)
               and len([itm for itm in prop.keywords["items"] if patch_needed(itm)])
               ]:

        #if found monkey-patch new items tuple w correct icon values
        prop.keywords["items"] = tuple(patch_item(itm) for itm in prop.keywords["items"])
        continue

    return None 

def register():

    #monkey patch all classes with enums & custom icons

    for cls in all_classes_with_enums():
        patch_custom_enum_icons(cls)

    #register classes

    for cls in classes:
        bpy.utils.register_class(cls)

    #register main props 

    bpy.types.Scene.scatter5          = bpy.props.PointerProperty(type=SCATTER5_PR_Scene)
    bpy.types.Object.scatter5         = bpy.props.PointerProperty(type=SCATTER5_PR_Object)
    bpy.types.WindowManager.scatter5  = bpy.props.PointerProperty(type=SCATTER5_PR_Window)
    bpy.types.NodeTree.scatter5       = bpy.props.PointerProperty(type=SCATTER5_PR_node_group) #TODO: tell me why again we aren't we unregistering nodetrees props?

    #update directories globals with new addon_prefs.library_path
    
    from .. resources.directories import update_lib
    update_lib()

    return 

def unregister():

    #remove props 

    del bpy.types.Scene.scatter5
    del bpy.types.Object.scatter5
    del bpy.types.WindowManager.scatter5

    #unregister classes 

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    return 

#if __name__ == "__main__":
#    register()