# ///////////////////////////////////////////////////////////////
#
# Blender Dome Light
# by: WANDERSON M. PIMENTA
# version: 3.0.0
#
# ///////////////////////////////////////////////////////////////

import bpy
import os
from bpy.types import Panel, AddonPreferences
from bpy.props import StringProperty, EnumProperty

# Add-on info
bl_info = {
    "name": "Dome Light v3",
    "author": "Wanderson M Pimenta",
    "version": (3, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Properties > Dome Light",
    "description": "Create a Dome Light", 
    "wiki_url": "",
    "tracker_url": "https://blender-addons.gumroad.com/l/dome_light_for_blender",      
    "category": "3D View"
}

# Import Shared Data
from .core.shared import (
    preview_collections,
    version,
    addon_keymaps,
    icons_info
)

# Import functions
from .core.functions import (
    generate_previews,
    update_light,
    generate_previews_2,
    update_light_2,
    check_environment_nodes,
    update_second_light, 
    load_favorites,
    load_icons
)

# Load Icons
load_icons(preview_collections, icons_info)

# Import Panels
from .core.panels import *

# Import operators
from .core.operators import *

# Import Menus
from .core.menus import (
    DOMELIGHT_MT_menu
)

# Preferences
class DOMELIGHT_preferences(AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        
        # Add shortcut field with a reset button
        row = layout.row(align=False)
        img_col = row.column(align=True)
        # Display the icon using template_icon
        icon = preview_collections['icons']['logo_icon']
        img_col.template_icon(icon_value=icon.icon_id, scale=8.0)

        inf_col = row.column(align=True)
        inf_box = inf_col.box()
        inf_title = inf_box.box()
        inf_title.label(text = f'Dome Light - Version: {version}', icon = 'WORLD')
        inf_box.label(text='Shortcut:', icon='INFO')
        inf_box.label(text='Default shortcut for menu in 3D view:')
        inf_box.label(text='Ctrl + Shift + Right Click')
        inf_box.separator()
        inf_box.label(text='To change, search in "Keymap" for "Dome Light Menu"')
        inf_box.label(text='and change it to whatever you want')

    
# Main Panel - Dome Light
class DOMELIGHT_PT_dome_light(Panel):
    bl_idname = 'DOMELIGHT_PT_dome_light'
    bl_label = 'Dome Light'
    bl_category = 'Dome Light'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_description = 'Dome Light panel'

    SUPPORTED_ENGINES = {
        'CYCLES',
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT'
    }

    @classmethod
    def poll(cls, context):
        return (context.engine in cls.SUPPORTED_ENGINES)
    
    def draw_header(self, context):
        self.layout.label(text="", icon='WORLD')

    def draw(self, context):
        # Layout
        layout = self.layout

        # Display the icon using template_icon
        icon = preview_collections['icons']['logo_icon']
        if check_environment_nodes() != 'OK':
            layout.template_icon(icon_value=icon.icon_id, scale=6.0)

        # // Box environment
        box = layout.box()
        box.label(text='Environments:', icon='WORLD')

        # Get the list of all worlds
        worlds = bpy.data.worlds

        # Add each world to the list in the panel
        item = box.column(align=True)
        for world in worlds:
            row = item.row(align=True)
            row.operator('domelight.rename_world', text=world.name, icon='WORLD_DATA').world_index = world.name
            row.operator('domelight.set_active_world', text='', icon='RESTRICT_VIEW_OFF' if bpy.context.scene.world == world else 'RESTRICT_VIEW_ON').world_index = world.name
            row.operator('domelight.remove_world', text='', icon='X').world_index = world.name

        # Button to create a new layer
        button_box = item.column(align=True)
        button_box.scale_y = 1.5 
        button_box.operator('domelight.create_new_environment_modal', text='New Environment', icon='ADD')

        # // Create/Fix environment
        if worlds:
            if check_environment_nodes() == 'Create':
                col = layout.column()
                box = col.box()
                col = box.column()
                col.label(text = 'Create light:', icon = 'OUTLINER_OB_LIGHT')
                col = box.column()
                col.scale_y = 1.5 
                col.operator('domelight.create_environment_light', text = 'Create Light', icon='WORLD_DATA')
            elif check_environment_nodes() == 'Fix':
                col = layout.column()
                box = col.box()
                col = box.column()
                col.label(text = 'Fix light:', icon = 'OUTLINER_OB_LIGHT')
                col.separator()
                box_info = col.box()
                col_info = box_info.column()
                col_info.label(text = 'WARNING:')
                col_info.label(text = 'Some nodes are missing,')
                col_info.label(text = 'click Fix Light to recreate them')
                col = box.column()
                col.scale_y = 1.5 
                col.operator('domelight.create_environment_light', text = 'Fix Light', icon='WORLD_DATA')
            else:
                pass

        # Display the icon using template_icon
        icon = preview_collections['icons']['logo_icon']
        if check_environment_nodes() != 'OK':
            box = layout.box()
            box.label(text=f'Version: {version}', icon='FUND')

# Light Settings
class DOMELIGHT_PT_light_settings(Panel):
    # Panel properties
    bl_idname = 'DOMELIGHT_PT_light_settings'
    bl_label = 'Light Settings'
    bl_parent_id = 'DOMELIGHT_PT_dome_light'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    # Draw header
    def draw_header(self, context):
        self.layout.label(text="", icon='LIGHT')

    # Poll function
    @classmethod
    def poll(cls, context):
        return check_environment_nodes() == 'OK'

    # Draw function
    def draw(self, context):
        layout = self.layout

        # Scene Objects
        scn = context.scene
        cycles_scn = scn.cycles
        engine = scn.render.engine
        active_world = scn.world
        view_settings = scn.view_settings

        # Node Properties
        nodes = scn.world.node_tree.nodes

        # Enable Mix HDR
        enable_second_light = active_world.enable_second_light

        col = layout.column(align=True)
        box = col.box()
        box.label(text=f"Choose an HDR:", icon='IMAGE_DATA')
        hdr = box.column(align=True)
        
        hdr_box = hdr.box()
        row = hdr_box.row(align=True)
        row.scale_y = 1.5
        row.operator('domelight.choose_folder_my_previews_dir', icon='FILEBROWSER')
        row.operator('domelight.reload_previews', text='', icon='FILE_REFRESH')
        
        if active_world.my_previews_dir and os.path.exists(active_world.my_previews_dir):
            hdr_box.label(text=active_world.my_previews_dir)

        # Get the name of the selected image
        if active_world.my_previews_dir and os.path.exists(active_world.my_previews_dir):
            hdr.separator()
            if any(filename.lower().endswith(('.exr', '.hdr')) for filename in os.listdir(active_world.my_previews_dir)):
                box = hdr.box()
                box.template_icon_view(active_world, "my_previews", show_labels=True, scale = 6, scale_popup=4)            

                # Display the name of the file or the message "Select an image above" with the icon of an upward arrow
                if active_world.actual_hdr == active_world.my_previews:
                    if not active_world.actual_hdr == "" and active_world.my_previews == "":
                        box.label(text="Empty folders, choose another", icon='ERROR')
                    else:
                        # Display the name of the file with the 'IMAGE_DATA' icon
                        box.label(text=active_world.my_previews, icon='IMAGE_DATA')
                else:
                    # Display the message "Select an image above" with the icon of an upward arrow
                    box.label(text="Select an image above", icon='FILE_PARENT')
                hdr.separator()
            else:
                box = hdr.box()
                box.label(text="Empty folders, choose another", icon='ERROR')
                hdr.separator()

        # Button to add current directory to favorites
        col = hdr.column(align=True)
        if active_world.my_previews_dir:
            col.label(text=f"Favorites:", icon='SOLO_ON')
            col.separator()
        button = col.column(align=True)
        normalized_active_dir = os.path.normpath(active_world.my_previews_dir)
        if active_world.my_previews_dir:
            if not any(fav["path"] == normalized_active_dir for fav in load_favorites(favorites_file)):
                button.operator('domelight.add_to_favorites', text='Add To Favorites', icon='SOLO_ON')

        # List of favorites
        favorites = load_favorites(favorites_file)
        for favorite in favorites:
            # Normalize paths before comparing them
            normalized_active_dir = os.path.normpath(active_world.my_previews_dir)
            normalized_favorite_path = os.path.normpath(favorite["path"])

            # Check if normalized paths are equal
            if normalized_active_dir == normalized_favorite_path:
                # If they are equal, set the icon to 'RESTRICT_VIEW_OFF'
                icon = 'RESTRICT_VIEW_OFF' 
            else:
                # If they are not equal, set the icon to 'RESTRICT_VIEW_ON'
                icon = 'RESTRICT_VIEW_ON'     

            row = col.row(align=True) 
            row.operator('domelight.rename_favorite', text=favorite["name"], icon='SOLO_OFF').favorite_index = favorites.index(favorite)
            row.operator('domelight.set_favorite', text='', icon=icon).favorite_index = favorites.index(favorite)
            row.operator('domelight.delete_favorite', text='', icon='X').favorite_index = favorites.index(favorite)

        # Enable Mix HDR if my_previews_dir exists
        if active_world.my_previews_dir and os.path.exists(active_world.my_previews_dir):
            # Box for HDR 2
            hdr.separator()
            box_hdr_2 = hdr.box()
            col_hdr_2 = box_hdr_2.column(align=True)

            if not enable_second_light:
                col_hdr_2.prop(active_world, 'enable_second_light', text='Enable Mix HDR', icon='UV_SYNC_SELECT')
            else:
                col_hdr_2.prop(active_world, 'enable_second_light', text='Disable Mix HDR', icon='RENDERLAYERS')

            if enable_second_light:                
                # Choose HDR for 'DOMELIGHT_environment_2'
                col_hdr_2.separator()
                col_hdr_2.label(text="Choose an HDR for Mix:", icon='IMAGE_DATA')
                col_hdr_2.separator()

                hdr_box_2 = col_hdr_2.box()
                row = hdr_box_2.row(align=True)
                row.scale_y = 1.5
                row.operator('domelight.choose_folder_my_previews_dir_2', icon='FILEBROWSER')
                row.operator('domelight.reload_previews_2', text='', icon='FILE_REFRESH')
                
                if active_world.my_previews_dir_2 and os.path.exists(active_world.my_previews_dir_2):
                    hdr_box_2.label(text=active_world.my_previews_dir_2)

                if active_world.my_previews_dir_2 and os.path.exists(active_world.my_previews_dir_2):
                    col_hdr_2.separator()
                    if any(filename.lower().endswith(('.exr', '.hdr')) for filename in os.listdir(active_world.my_previews_dir_2)):
                        col_hdr_2.template_icon_view(active_world, "my_previews_2", show_labels=True, scale=6, scale_popup=4)            

                        # Display the name of the file or the message "Select an image above" with the icon of an upward arrow
                        col_hdr_2.separator()
                        if active_world.actual_hdr_2 == active_world.my_previews_2:
                            # Display the name of the file with the 'IMAGE_DATA' icon
                            col_hdr_2.label(text=active_world.my_previews_2, icon='IMAGE_DATA')
                        else:
                            # Display the message "Select an image above" with the icon of an upward arrow
                            col_hdr_2.label(text="Select an image above", icon='FILE_PARENT')
                        col_hdr_2.separator()
                    else:
                        box = col_hdr_2.box()
                        box.label(text="Empty folders, choose another", icon='ERROR')
                        col_hdr_2.separator()

                # Button to add current directory to favorites
                if active_world.my_previews_dir_2:
                    col_hdr_2.separator()
                    col_hdr_2.label(text=f"Favorites:", icon='SOLO_ON')
                    col_hdr_2.separator()

                button_hdr_2 = col_hdr_2.column(align=True)
                normalized_active_dir_2 = os.path.normpath(active_world.my_previews_dir_2)
                if active_world.my_previews_dir_2:
                    if not any(fav["path"] == normalized_active_dir_2 for fav in load_favorites(favorites_file)):
                        button_hdr_2.operator('domelight.add_to_favorites_2', text='Add To Favorites', icon='SOLO_ON')

                # List of favorites
                favorites = load_favorites(favorites_file)
                for favorite in favorites:
                    # Normalize paths before comparing them
                    normalized_active_dir = os.path.normpath(active_world.my_previews_dir_2)
                    normalized_favorite_path = os.path.normpath(favorite["path"])

                    # Check if normalized paths are equal
                    if normalized_active_dir == normalized_favorite_path:
                        # If they are equal, set the icon to 'RESTRICT_VIEW_OFF'
                        icon = 'RESTRICT_VIEW_OFF' 
                    else:
                        # If they are not equal, set the icon to 'RESTRICT_VIEW_ON'
                        icon = 'RESTRICT_VIEW_ON'     

                    row = col_hdr_2.row(align=True) 
                    row.operator('domelight.rename_favorite', text=favorite["name"], icon='SOLO_OFF').favorite_index = favorites.index(favorite)
                    row.operator('domelight.set_favorite_2', text='', icon=icon).favorite_index = favorites.index(favorite)
                    row.operator('domelight.delete_favorite', text='', icon='X').favorite_index = favorites.index(favorite)

                if active_world.my_previews_dir_2:
                    col_hdr_2.separator()
                    col_hdr_2.prop(nodes['DOMELIGHT_mix_BG_RGB'], "blend_type", text = '', icon='NONE')
                    col_hdr_2.prop(nodes['DOMELIGHT_mix_BG_RGB'].inputs[0], "default_value", text = 'Mix', icon='NONE')
                    col_hdr_2.separator()
                    col_hdr_2.label(text = "Rotation:", icon = 'FILE_REFRESH')
                    col_hdr_2.separator()
                    col_hdr_2.prop(nodes["DOMELIGHT_mapping_2"].inputs[2], "default_value", text = "")

        # Show extra options if my_previews_dir exists 
        if active_world.my_previews_dir and os.path.exists(active_world.my_previews_dir):
            col_light = layout.column(align=True)
            box_light = col_light.box()
            col_settings = box_light.column(align=True)
            col_settings.label(text = 'Settings:', icon = 'LIGHT')
            col_settings.separator()
            if 'DOMELIGHT_environment' in nodes:
                col_settings.prop(nodes['DOMELIGHT_environment'], "projection", text = '')
                col_settings.separator()
            if 'DOMELIGHT_math_add' in nodes:
                col_settings.prop(nodes['DOMELIGHT_math_add'].inputs[1], "default_value", text = 'Intensity')
            if 'DOMELIGHT_math_multiply' in nodes:
                col_settings.prop(nodes['DOMELIGHT_math_multiply'].inputs[1], "default_value", text = 'Sun Intensity')
            if 'DOMELIGHT_gamma' in nodes:
                col_settings.prop(nodes['DOMELIGHT_gamma'].inputs[1], "default_value", text = "Gamma")
            if 'DOMELIGHT_saturation' in nodes:
                col_settings.prop(nodes['DOMELIGHT_saturation'].inputs[1], "default_value", text = "Saturation")

            box = col_light.box()
            col = box.column(align=True)
            col.label(text = "Rotation:", icon = 'FILE_REFRESH')
            col.separator()
            col.prop(nodes["DOMELIGHT_mapping"].inputs[2], "default_value", text = "")

            box = col_light.box()
            col = box.column(align=True)
            if 'DOMELIGHT_color' in nodes:            
                col.label(text = 'Color overlay:', icon = 'EYEDROPPER')
                col.separator()
                col.prop(nodes['DOMELIGHT_color'].inputs[2], "default_value", text = "")     
                col.prop(nodes['DOMELIGHT_color'], "blend_type", text="")     
                col.prop(nodes['DOMELIGHT_color'].inputs[0], "default_value", text = "Intensity")
                
            box = col_light.box()
            col = box.column(align=True)
            col.label(text = "Exposure:", icon = 'SCENE')
            col.separator()
            if engine == 'CYCLES':
                col.prop(cycles_scn, "film_exposure", text = "Cycles Exposure")
            col.prop(view_settings, "exposure", text = "Color Exposure")

        col = layout.column()
        col.label(text = f'Version: {version}', icon = 'FUND')

    
classes = [
    DOMELIGHT_preferences,
    DOMELIGHT_PT_dome_light,
    DOMELIGHT_PT_preview_settings,
    DOMELIGHT_PT_light_settings,
    DOMELIGHT_OT_create_new_environment,
    DOMELIGHT_OT_create_new_environment_modal,
    DOMELIGHT_OT_create_environment_light,
    DOMELIGHT_OT_rename_world,
    DOMELIGHT_OT_set_active_world,
    DOMELIGHT_OT_remove_world,
    DOMELIGHT_OT_choose_hdr_folder,
    DOMELIGHT_OT_choose_hdr_2_folder,
    DOMELIGHT_OT_reload_previews,
    DOMELIGHT_OT_reload_previews_2,
    DOMELIGHT_OT_add_to_favorites,
    DOMELIGHT_OT_add_to_favorites_2,
    DOMELIGHT_OT_rename_favorite,
    DOMELIGHT_OT_rename_favorite_popup,
    DOMELIGHT_OT_set_favorite,
    DOMELIGHT_OT_set_favorite_2,
    DOMELIGHT_OT_delete_favorite,
    DOMELIGHT_OT_open_menu,
    DOMELIGHT_MT_menu,
]

def register():
    from bpy.utils import register_class

    # Register classes
    for cls in classes:
        register_class(cls)

    # HDR 1 
    # Enable access to our preview collection outside of this function
    bpy.types.World.my_previews_dir = StringProperty(
        name="Folder Path",
        subtype='DIR_PATH'
    )

    bpy.types.World.my_previews = EnumProperty(
        items=generate_previews,
        update=update_light
    )
    
    pcoll = bpy.utils.previews.new()
    pcoll.my_previews_dir = ""
    pcoll.my_previews = ()

    preview_collections["hdr_thumbnails"] = pcoll

    # HDR 2
    bpy.types.World.my_previews_dir_2 = StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
    )

    bpy.types.World.my_previews_2 = EnumProperty(
        items=generate_previews_2,
        update=update_light_2
    )

    pcoll_2 = bpy.utils.previews.new()
    pcoll_2.my_previews_dir = ""
    pcoll_2.my_previews = ()
    preview_collections["hdr_thumbnails_2"] = pcoll_2

    # Actual HDR
    bpy.types.World.actual_hdr = bpy.props.StringProperty(
        name="Actual HDRI",
        default="",
    )

    # Actual HDR
    bpy.types.World.actual_hdr_2 = bpy.props.StringProperty(
        name="Actual HDRI",
        default="",
    )

    # HDR Mix
    bpy.types.World.enable_second_light = bpy.props.BoolProperty(
        name = 'Enable Mix Light',
        default = False,
        options={'HIDDEN'},
        update = update_second_light
    )

    # Add the key shortcut to the Keymap class
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        keymap_item = km.keymap_items.new("domelight.open_menu", type='RIGHTMOUSE', value='PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, keymap_item))

def unregister():
    from bpy.utils import unregister_class

    # Unregister classes
    for cls in reversed(classes):
        unregister_class(cls)

    # Enable access to our preview collection outside of this function
    del bpy.types.World.my_previews_dir

    # Remove HDR preview collection
    del bpy.types.World.my_previews

    # Enable access to our preview collection outside of this function
    del bpy.types.World.my_previews_dir_2

    # Remove HDR preview collection
    del bpy.types.World.my_previews_2

    # Actual HDR
    del bpy.types.World.actual_hdr

    # Actual HDR
    del bpy.types.World.actual_hdr_2

    # Remove the preview collection
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    # HDR Mix
    del bpy.types.World.enable_second_light

    # Remove the key shortcut from the Keymap class
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
