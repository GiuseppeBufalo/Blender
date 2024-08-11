# ///////////////////////////////////////////////////////////////
#
# Blender Dome Light
# by: WANDERSON M. PIMENTA
# version: 3.0.0
#
# ///////////////////////////////////////////////////////////////

import bpy
import os
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

# Import Shared Data
from .shared import (
    preview_collections,
    favorites_file
)

# Import functions
from .functions import (
    generate_previews,
    create_world_nodes,
    save_favorites,
    load_favorites
)

# Import Menus
from .menus import (
    DOMELIGHT_MT_menu
)

# This class allows the user to choose a folder for the HDR previews in the DomeLight addon.
class DOMELIGHT_OT_choose_hdr_folder(Operator, ImportHelper):
    bl_idname = 'domelight.choose_folder_my_previews_dir'
    bl_label = 'Choose HDR Folder'
    bl_description = 'Choose a folder that contains HDR and EXR'
    bl_options = {'REGISTER'}
    
    filepath: bpy.props.StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
    ) # type: ignore

    filter_folder: bpy.props.BoolProperty( 
        default=True,
        options={"HIDDEN"}
    ) # type: ignore

    def invoke(self, context, event):
        self.filepath = ""  # Set to empty the default file name
        return super().invoke(context, event)

    # Updates the scene with the newly chosen path
    def execute(self, context):
        path = os.path.dirname(self.filepath)
        context.scene.world.my_previews_dir = path
        print("Selected path:", path)
        return {'FINISHED'}
    
# This class allows the user to choose a folder for the HDR 2 previews in the DomeLight addon.
class DOMELIGHT_OT_choose_hdr_2_folder(Operator, ImportHelper):
    bl_idname = 'domelight.choose_folder_my_previews_dir_2'
    bl_label = 'Choose HDR 2 Folder'
    bl_description = 'Choose a folder that contains HDR and EXR'
    bl_options = {'REGISTER'}
    
    filepath: bpy.props.StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
    ) # type: ignore

    filter_folder: bpy.props.BoolProperty( 
        default=True,
        options={"HIDDEN"}
    ) # type: ignore

    def invoke(self, context, event):
        self.filepath = ""  # Set to empty the default file name
        return super().invoke(context, event)

    # Updates the scene with the newly chosen path
    def execute(self, context):
        path = os.path.dirname(self.filepath)
        context.scene.world.my_previews_dir_2 = path
        print("Selected path:", path)
        return {'FINISHED'}

# Create new layer
class DOMELIGHT_OT_create_new_environment(Operator):
    bl_idname = 'domelight.create_environment_layer'
    bl_label = 'Create Environment'
    bl_description = 'Create a new environment in the world'

    new_layer_name: bpy.props.StringProperty(name="Name", default="Dome Light")

    def execute(self, context):
        # Create a new world
        new_world = bpy.data.worlds.new(name=self.new_layer_name)

        # Enable use_nodes
        new_world.use_nodes = True

        # Set the newly created world as the active world
        bpy.context.scene.world = new_world

        # Redraw the UI to reflect the changes
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        return {'FINISHED'}
    
class DOMELIGHT_OT_create_new_environment_modal(Operator):
    bl_idname = 'domelight.create_new_environment_modal'
    bl_label = 'New Environment'
    bl_description = 'Create a new environment in the world'

    new_layer_name: bpy.props.StringProperty(name='Name', default='Dome Light')

    def execute(self, context):
        # Check if the new layer name is provided
        if self.new_layer_name.strip():  # Check if the string is not empty after removing leading and trailing spaces
            # Create a new world
            new_world = bpy.data.worlds.new(name=self.new_layer_name)

            # Enable use_nodes
            new_world.use_nodes = True

            # Set the newly created world as the active world
            bpy.context.scene.world = new_world

            # Redraw the UI to reflect the changes
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
# Create environment           
class DOMELIGHT_OT_create_environment_light(Operator):
    bl_idname = 'domelight.create_environment_light'
    bl_label = 'Create Environment'
    bl_description = 'Create Dome Light'
    
    def execute(self, context):
        try:
            create_world_nodes()
            bpy.context.space_data.shading.use_scene_lights_render = True
            bpy.context.space_data.shading.use_scene_world_render = True
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = True
            bpy.context.space_data.shading.type = 'MATERIAL'

            self.report({'INFO'}, 'Light nodes successfully created for the current environment! Now choose an HDR.')
        except Exception as e:
            print("An error occurred:", e)  # Print the error to the console
            self.report({'ERROR'}, 'An error was found! Check the console for more information')

        # Update the actual HDR
        try:
            active_world = context.scene.world
            active_world.actual_hdr = ""
            active_world.actual_hdr_2 = ""
        except:
            pass

        return {'FINISHED'}
    
# Rename world layers
class DOMELIGHT_OT_rename_world(Operator):
    bl_idname = 'domelight.rename_world'
    bl_label = 'Rename World'
    world_index: bpy.props.StringProperty()
    world_name: bpy.props.StringProperty()
    bl_description = 'Rename environment'

    def execute(self, context):
        bpy.data.worlds[self.world_index].name = self.world_name
        return {'FINISHED'}

    def invoke(self, context, event):
        # Set the initial value of world_name as the current name of the world layer
        self.world_name = bpy.data.worlds[self.world_index].name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'world_name', text='New name')

# Set world as active
class DOMELIGHT_OT_set_active_world(Operator):
    bl_idname = 'domelight.set_active_world'
    bl_label = 'Set active environment'
    bl_description = 'Use this option to switch between worlds/environments in Blender'
    world_index: bpy.props.StringProperty()

    def execute(self, context):
        bpy.context.scene.world = bpy.data.worlds.get(self.world_index)
        return {'FINISHED'}

# Remove layer
class DOMELIGHT_OT_remove_world(Operator):
    bl_idname = 'domelight.remove_world'
    bl_label = 'Remove environment'
    bl_description = 'This option will remove the current project environment'
    world_index: bpy.props.StringProperty()

    def execute(self, context):
        bpy.data.worlds.remove(bpy.data.worlds.get(self.world_index))
        return {'FINISHED'}
    
class DOMELIGHT_OT_reload_previews(Operator):
    # Operator properties
    bl_idname = "domelight.reload_previews"
    bl_label = "Reload previews"
    bl_options = {'UNDO'}
    bl_description = "Reload images from selected folder"

    # Execute function
    def execute(self, context):
        active_world = context.scene.world
        temp_path = active_world.my_previews_dir

        # Clear preview data
        if preview_collections.get("hdr_thumbnails"):
            pcoll = preview_collections["hdr_thumbnails"]
            pcoll.clear()
            pcoll.my_previews_dir = ""
            pcoll.my_previews = ()
            preview_collections["hdr_thumbnails"] = pcoll

        # Update previews again
        generate_previews(self, context)

        # Restore temporary directory
        active_world.my_previews_dir = temp_path

        return {'FINISHED'}

class DOMELIGHT_OT_reload_previews_2(Operator):
    # Operator properties
    bl_idname = "domelight.reload_previews_2"
    bl_label = "Reload previews"
    bl_options = {'UNDO'}
    bl_description = "Reload images from selected folder"

    # Execute function
    def execute(self, context):
        active_world = context.scene.world
        temp_path = active_world.my_previews_dir

        # Clear preview data
        if preview_collections.get("hdr_thumbnails_2"):
            pcoll = preview_collections["hdr_thumbnails_2"]
            pcoll.clear()
            pcoll.my_previews_dir = ""
            pcoll.my_previews = ()
            preview_collections["hdr_thumbnails_2"] = pcoll

        # Update previews again
        generate_previews(self, context)

        # Restore temporary directory
        active_world.my_previews_dir = temp_path

        return {'FINISHED'}
    
class DOMELIGHT_OT_add_to_favorites(Operator):
    # Operator properties
    bl_idname = "domelight.add_to_favorites"
    bl_label = "Add to Favorites"
    bl_description = "Add current directory to favorites"

    # Execute function
    def execute(self, context):
        active_world = context.scene.world
        favorites = load_favorites(favorites_file)

        # Normalize path before getting the name of the last valid folder
        path = os.path.normpath(active_world.my_previews_dir.rstrip("\\"))
        name = os.path.basename(path)

        # Check if the folder name already exists in the favorites list
        if not any(fav["name"] == name for fav in favorites):
            favorites.append({"name": name, "path": path})
            save_favorites(favorites, favorites_file)
            self.report({'INFO'}, f"Directory '{path}' added to favorites.")
        else:
            self.report({'WARNING'}, f"Directory '{name}' is already in favorites.")

        # Force UI update
        context.area.tag_redraw()
        return {'FINISHED'}
    
class DOMELIGHT_OT_add_to_favorites_2(Operator):
    # Operator properties
    bl_idname = "domelight.add_to_favorites_2"
    bl_label = "Add to Favorites"
    bl_description = "Add current directory to favorites"

    # Execute function
    def execute(self, context):
        active_world = context.scene.world
        favorites = load_favorites(favorites_file)

        # Normalize path before getting the name of the last valid folder
        path = os.path.normpath(active_world.my_previews_dir_2.rstrip("\\"))
        name = os.path.basename(path)

        # Check if the folder name already exists in the favorites list
        if not any(fav["name"] == name for fav in favorites):
            favorites.append({"name": name, "path": path})
            save_favorites(favorites, favorites_file)
            self.report({'INFO'}, f"Directory '{path}' added to favorites.")
        else:
            self.report({'WARNING'}, f"Directory '{name}' is already in favorites.")

        # Force UI update
        context.area.tag_redraw()
        return {'FINISHED'}


class DOMELIGHT_OT_rename_favorite(Operator):
    # Operator properties
    bl_idname = "domelight.rename_favorite"
    bl_label = "Rename Favorite"
    bl_description = "Rename selected favorite"

    favorite_index: bpy.props.IntProperty()

    # Execute function
    def execute(self, context):
        # Open popup to rename the favorite
        bpy.ops.domelight.rename_favorite_popup('INVOKE_DEFAULT', favorite_index=self.favorite_index)
        return {'FINISHED'}

class DOMELIGHT_OT_rename_favorite_popup(Operator):
    # Operator properties
    bl_idname = "domelight.rename_favorite_popup"
    bl_label = "Rename Favorite"
    bl_description = "Rename this favorite"

    favorite_index: bpy.props.IntProperty()
    new_name: bpy.props.StringProperty(name="New Name")

    # Execute function
    def execute(self, context):
        favorites = load_favorites(favorites_file)
        favorites[self.favorite_index]["name"] = self.new_name
        save_favorites(favorites, favorites_file)
        context.area.tag_redraw()
        return {'FINISHED'}

    # Invoke function
    def invoke(self, context, event):
        fav_index = self.favorite_index
        fav_name = load_favorites(favorites_file)[fav_index]["name"]
        self.new_name = fav_name  # Set the current name as the initial value of the text field
        return context.window_manager.invoke_props_dialog(self)

    # Draw function
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name", text='New name')  # Text field for the new favorite name
        layout.label(text="Path: " + load_favorites(favorites_file)[self.favorite_index]["path"])  # Label for the favorite path


class DOMELIGHT_OT_set_favorite(Operator):
    # Operator properties
    bl_idname = "domelight.set_favorite"
    bl_label = "Set Favorite"
    bl_description = "Set selected favorite as current directory"

    favorite_index: bpy.props.IntProperty()

    # Execute function
    def execute(self, context):
        favorites = load_favorites(favorites_file)
        favorite = favorites[self.favorite_index]
        active_world = context.scene.world
        active_world.my_previews_dir = favorite["path"]
        generate_previews(self, context)
        self.report({'INFO'}, f"Directory set to '{favorite['path']}'")
        return {'FINISHED'}
    
class DOMELIGHT_OT_set_favorite_2(Operator):
    # Operator properties
    bl_idname = "domelight.set_favorite_2"
    bl_label = "Set Favorite"
    bl_description = "Set selected favorite as current directory"

    favorite_index: bpy.props.IntProperty()

    # Execute function
    def execute(self, context):
        favorites = load_favorites(favorites_file)
        favorite = favorites[self.favorite_index]
        active_world = context.scene.world
        active_world.my_previews_dir_2 = favorite["path"]
        generate_previews(self, context)
        self.report({'INFO'}, f"Directory set to '{favorite['path']}'")
        return {'FINISHED'}

class DOMELIGHT_OT_delete_favorite(Operator):
    # Operator properties
    bl_idname = "domelight.delete_favorite"
    bl_label = "Delete Favorite"
    bl_description = "Delete selected favorite"

    favorite_index: bpy.props.IntProperty()

    # Execute function
    def execute(self, context):
        favorites = load_favorites(favorites_file)
        favorite = favorites.pop(self.favorite_index)
        save_favorites(favorites, favorites_file)
        self.report({'INFO'}, f"Favorite '{favorite['name']}' deleted.")
        context.area.tag_redraw()
        return {'FINISHED'}
    
# Operator class to open the menu
class DOMELIGHT_OT_open_menu(Operator):
    bl_idname = "domelight.open_menu"
    bl_label = "Dome Light Menu"

    def execute(self, context):
        # Activate the menu panel
        bpy.context.window_manager.popup_menu(DOMELIGHT_MT_menu.draw, title=DOMELIGHT_MT_menu.bl_label)
        return {'FINISHED'}