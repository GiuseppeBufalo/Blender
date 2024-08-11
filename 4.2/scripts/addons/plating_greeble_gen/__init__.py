bl_info = {
    "name": "Generate Plates with Greebles",
    "author": "Mark Kingsnorth",
    "version": (2, 0, 11),
    "blender": (2, 80, 0),
    "description": "Plating and Greebles Generator",
    "warning": "",
    "wiki_url": "https://plating-generator-docs.readthedocs.io/",
    "category": "Mesh",
    }
# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
    import imp
    imp.reload(preferences)
    imp.reload(plating_props)
    imp.reload(plating_functions)
    imp.reload(plating_generator)
    imp.reload(plating_ui)
    imp.reload(standard_greeble_objects)
    imp.reload(greeble_props)
    imp.reload(greeble_functions)
    imp.reload(greeble_generator)
    imp.reload(greeble_ui)
    imp.reload(greeble_factory)

    imp.reload(properties)
    imp.reload(operators)
    imp.reload(panel)

    print("Reloaded greeble files")
else:
    import os
    import shutil
    from bpy.utils import previews
    from . import preferences
    from .plating_gen import plating_props
    from .plating_gen import plating_functions
    from .plating_gen import plating_generator
    from .plating_gen import plating_ui   
    from .greeble_gen import greeble_props
    from .greeble_gen import standard_greeble_objects
    from .greeble_gen import greeble_functions
    from .greeble_gen import greeble_generator
    from .greeble_gen import greeble_ui
    from .greeble_gen import greeble_factory
    
    from .orchestration import properties, panel, operators

    print("Imported greeble and plating files")

import bpy


classes = [ 
            greeble_props.SceneGreebleObject,
            greeble_props.SceneGreebleSetting,
            greeble_props.SceneGreebleSettingPropertyGroup,
            plating_props.PlatingGeneratorMaterial,
            plating_props.PlatingGeneratorMaterialPropertyGroup,
            plating_props.PlatingGeneratorPropsPropertyGroup,
            greeble_props.GreeblePropsPropertyGroup,
            plating_generator.MESH_OT_PlateGeneratorAddPlatingMaterial_OT_Operator,
            plating_generator.MESH_OT_PlateGeneratorRemovePlatingMaterial_OT_Operator,
            plating_generator.MESH_OT_PlateGeneratorOperator,
            plating_generator.MESH_OT_PlateGeneratorPanelLineOperator,
            plating_generator.MESH_OT_PlateGeneratorCreateNewOperator,
            greeble_generator.MESH_OT_GreebleGeneratorOperator,
            greeble_generator.MESH_OT_refresh_greebles_path,
            greeble_generator.MESH_OT_add_greebles_path,
            greeble_generator.MESH_OT_remove_greebles_path,
            greeble_generator.MESH_OT_copy_greebles_path,
            # OBJECT_MT_ButtonsSub,
            preferences.PresetsFolder,
            preferences.GreebleMetadata,
            preferences.GreebleCategory,
            preferences.GreebleCatalogue,
            preferences.plating_greeble_preferences,

]

def load_presets(presets_folder_name, presets_folder_suffix):
    """Load preset files if they have not been already"""
    presets_folder = bpy.utils.user_resource('SCRIPTS', path="presets")
    my_presets = os.path.join(presets_folder, 'operator', presets_folder_name)
    if not os.path.isdir(my_presets) or len(os.listdir(my_presets) ) == 0:
        my_bundled_presets = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'presets'), presets_folder_suffix)

        # makedirs() will also create all the parent folders (like "object")
        try:
            os.makedirs(my_presets)
        except FileExistsError:
            pass

        # Get a list of all the files in your bundled presets folder
        files = os.listdir(my_bundled_presets)

        # Copy them
        [shutil.copy2(os.path.join(my_bundled_presets, f), my_presets) for f in files]

# def menu_func(self, context):
#     self.layout.menu(OBJECT_MT_ButtonsSub.bl_idname)

custom_icons = None
name = __name__.partition('.')[0]
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # bpy.types.VIEW3D_MT_object.append(menu_func)
    # bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)

    # # Initialise Greeble Library Objects
    greeble_generator.refresh_greeble_libraries()

    # load any presets.
    load_presets('mesh.plates_generate', 'plates')
    # load_presets('mesh.plates_greebles_generate', 'plates')
    # load_presets('mesh.plating_generator', 'panel')

    operators.register()
    properties.register()
    panel.register()

    panel.my_bundled_presets = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'presets'), 'panel')
    presets_folder = bpy.utils.user_resource('SCRIPTS', path="presets")
    panel_presets = os.path.join(presets_folder, 'operator', 'mesh.plating_generator')
    panel.panel_presets = panel_presets


    


def unregister():

    panel.unregister()
    properties.unregister()
    operators.unregister()

    # bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func)
    # bpy.types.VIEW3D_MT_object.remove(menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    greeble_generator.remove_greeble_libraries()

    

if __name__ == "__main__":
    register()
