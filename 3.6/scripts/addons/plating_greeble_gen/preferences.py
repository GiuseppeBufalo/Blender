import os
import bpy
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import CollectionProperty, StringProperty, BoolProperty, PointerProperty, IntProperty
from .greeble_gen import greeble_factory

def addon_name():
    return os.path.basename(os.path.dirname(os.path.realpath(__file__)))

def preference():
    preference = bpy.context.preferences.addons[addon_name()].preferences
    return preference

class GreebleMetadata(bpy.types.PropertyGroup):
    greeble_name : StringProperty()
    icon_id : IntProperty()
    file_path: StringProperty(
        name = 'Path',
        description = 'Greeble Object Path',
        subtype = 'DIR_PATH',
        default = '')

class GreebleCategory(bpy.types.PropertyGroup):
    category_name: StringProperty()
    greebles : CollectionProperty(type=GreebleMetadata)

    folder_path: StringProperty(
        name = 'Path',
        description = 'Greeble library Path',
        subtype = 'DIR_PATH',
        default = 'Choose Folder')

class GreebleCatalogue(bpy.types.PropertyGroup):
    categories : CollectionProperty(type=GreebleCategory)
    default_category : StringProperty()

class PresetsFolder(bpy.types.PropertyGroup):

    presets_category_name : StringProperty(name="Name for presets")

    def update_category_name(self, context):
        self.presets_category_name = os.path.basename(os.path.dirname(self.presets_folder_path))

    presets_folder_path: StringProperty(
        name = 'Presets Path',
        description = 'Presets Path',
        subtype = 'DIR_PATH',
        default = 'Choose Folder',
        update=update_category_name)

class plating_greeble_preferences(AddonPreferences):
    bl_idname = addon_name()

    catalogue : PointerProperty(type=GreebleCatalogue)
    
    presets_folders : CollectionProperty(type=PresetsFolder)

    def draw(self, context):
        layout = self.layout

        col = layout.column()

        box = layout.box()

        box.label(text="Preset Folders")

        col = box.column()

            
        if not self.presets_folders:
            center_col = col.row()
            center_col.alignment="CENTER"
            center_col.label(text="No Presets Folders Set")
            col.separator()

        if self.presets_folders:
            i = 0
            folders_row = col.row()
            folder_col = folders_row.column()
            for presets_folders_entry in self.presets_folders:
                row  = folder_col.row()
                split = row.split(factor=0.7)
                
                split.prop(presets_folders_entry, 'presets_folder_path', text="")
                split.prop(presets_folders_entry, 'presets_category_name', text="")

                row.operator('platinggen.delete_preset_folder', text='', icon="CANCEL").item_index_to_delete = i
                move_row = row.row(align=True)
                up_col = move_row.column(align=True)
                up_col.enabled = i != 0
                props = up_col.operator("platinggen.move_preset_folder", icon="TRIA_UP", text='')
                props.direction = 'UP' 
                props.item_index = i
                down_col = move_row.column(align=True)
                down_col.enabled = i != len(self.presets_folders) - 1
                props = down_col.operator("platinggen.move_preset_folder", icon="TRIA_DOWN", text='')
                props.direction = 'DOWN' 
                props.item_index = i
                i+=1
            col.separator()

        col.operator('platinggen.add_preset_folder', text="Add Folder Containing Presets")
        
        box = layout.box()

        box.label(text="Greeble Libraries")

        if len(self.catalogue.categories) == 0:
            box.label(text="No Greeble Libraries loaded.")

        for index, category in enumerate(self.catalogue.categories):
            row = box.row()
            split = row.split(factor=0.2)
            split.prop(category, 'category_name', text='', emboss=False)

            split.prop(category, 'folder_path', text='')

            op = row.operator('mesh.copy_greebles_path', text='', emboss=False, icon='PASTEDOWN')
            op.index = index

            op = row.operator('mesh.remove_greebles_path', text='', emboss=False, icon='CANCEL')
            op.index = index

        col = box.column()
        col.operator('mesh.add_greebles_path', text='Add Folder Containing Greebles', icon='FILE_NEW')


        col = box.column()
        col.operator('mesh.refresh_greebles_path', text='Refresh Libraries')