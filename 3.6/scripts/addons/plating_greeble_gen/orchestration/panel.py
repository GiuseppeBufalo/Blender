###########################
# UI for Orchestration
###########################

import bpy
from bpy.types import Panel, UIList, Menu
from bpy.utils import register_class, unregister_class
from .operators import PLATINGGEN_OT_SelectFromObject, PLATINGGEN_OT_UpdatePlatingSelection
from ..plating_gen import plating_ui
from ..greeble_gen import greeble_ui
from ..plating_gen.plating_generator import MESH_OT_PlateGeneratorCreateNewOperator, MESH_OT_PlateGeneratorOperator, MESH_OT_PlateGeneratorPanelLineOperator
from ..greeble_gen.greeble_generator import MESH_OT_GreebleGeneratorOperator
from .operators import preset_dir, PLATINGGEN_OT_OpenFile, PLATINGGEN_OT_OpenFilebrowser, PLATINGGEN_OT_ExecutePlatingGenPreset, PLATINGGEN_OT_AddPlatingGenPreset, PLATINGGEN_OT_SaveFilebrowser
from bl_ui.utils import PresetPanel
from .. import preferences
import re

class PLATINGGEN_MT_PlatingGenPresets(Menu): 
    bl_label = 'Presets' 
    preset_subdir = preset_dir
    preset_operator = 'script.platinggen_execute_preset'
    draw = Menu.draw_preset


class PLATINGGEN_PT_presets(PresetPanel, Panel):
    bl_label = 'Presets'
    preset_subdir = preset_dir
    preset_operator = 'script.platinggen_execute_preset'
    preset_add_operator = 'mesh.add_platinggen_preset'


class PLATINGGEN_ENTRY_UL_List(UIList): 
    """These are for rendering all level entries.""" 
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): 
        row = layout.row(align=True)

        level_icon = 'RIGHTARROW_THIN' if index == active_data.level_index else 'BLANK1'
           
        row.label(text="", icon = level_icon, icon_value=1)

        row.label(text='', icon='VIEW_PERSPECTIVE' if item.type == 'PlatingGeneratorDecorator' else 'PARTICLE_POINT')
        row.prop(item, 'level_color', text="", icon='BLANK1')
        row.prop(item, 'level_name', text="")

        if item.type == 'PlatingGeneratorDecorator':
            props = item.plating_props
            if props.pattern_type == '0':
                row.prop(props, "random_seed", text='')
            elif props.pattern_type == '2':
                row.prop(props, "random_seed", text='')
            elif props.pattern_type == '3':
                row.prop(props, "rectangle_random_seed", text='')
            elif props.pattern_type == '4':
                row.prop(props, "rectangle_random_seed", text='')
            elif props.pattern_type == '6':
                row.prop(props, "ruby_dragon_random_seed", text='')
        elif item.type == 'GreebleDecorator':
            props = item.greeble_props
            row.prop(props, "greeble_random_seed", text='')
        
        row.prop(item, 'visible', text='', icon='HIDE_OFF' if item.visible else 'HIDE_ON')

        enabled_row = row.row(align=True)
        enabled_row.alert = not item.is_enabled
        enabled_row.prop(item, 'is_enabled', text="", icon="CHECKBOX_HLT" if item.is_enabled else "CHECKBOX_DEHLT")

        props = row.operator('platinggen.delete_level', icon='X', text='')
        props.item_index_to_delete = index



def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]



def draw_presets(self, context, add_new=False):
    """Draw List of Presets"""
    layout = self.layout
    global my_bundled_presets
    if os.path.isdir(my_bundled_presets):
        files = [file for file in os.listdir(my_bundled_presets) if file.endswith('.json')]
        if files:
            files.sort(key=natural_keys)
            layout.label(text='Bundled Presets')
            for file in files:
                props = layout.operator(PLATINGGEN_OT_OpenFile.bl_idname, text=os.path.splitext(file)[0])
                props.file_path = os.path.join(my_bundled_presets, file)
                props.add_new = add_new
            
    preference = preferences.preference()
    # custom_filepath = preference.presets_folder_path
    presets_folders = preference.presets_folders

    for preset_folder_entry in presets_folders:
        custom_filepath = preset_folder_entry.presets_folder_path
        if os.path.isdir(custom_filepath):
            files = [file for file in os.listdir(custom_filepath) if file.endswith('.json')]
            if files:
                files.sort(key=natural_keys)
                layout.separator()
                
                layout.label(text=preset_folder_entry.presets_category_name)

                for file in files:
                    props = layout.operator(PLATINGGEN_OT_OpenFile.bl_idname, text=os.path.splitext(file)[0])
                    props.file_path = os.path.join(custom_filepath, file)
                    props.add_new = add_new

    global panel_presets
    if os.path.isdir(panel_presets):
        files = [file for file in os.listdir(panel_presets) if file.endswith('.py') and file != 'Defaults.py']
        if files:
            files.sort(key=natural_keys)
            layout.separator()
            layout.label(text='Other Presets')
            for file in files:
                props = layout.operator(PLATINGGEN_OT_ExecutePlatingGenPreset.bl_idname, text=os.path.splitext(file)[0])
                props.add_new = add_new
                props.filepath = os.path.join(panel_presets, file)
                props = layout.operator(PLATINGGEN_OT_AddPlatingGenPreset.bl_idname, text="    - Remove " + os.path.splitext(file)[0])
                props.name = os.path.splitext(file)[0]
                props.remove_name = True

class OBJECT_MT_plating_generator_presets_menu(Menu):
    bl_idname = 'OBJECT_MT_plating_generator_presets_menu'
    bl_label = 'Presets Menu'

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj and context.active_object.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout

        layout.operator(PLATINGGEN_OT_OpenFilebrowser.bl_idname, icon='PRESET', text="Load Preset...")
        layout.operator(PLATINGGEN_OT_SaveFilebrowser.bl_idname, icon='PRESET_NEW', text="Save Preset...")
        layout.separator()
        draw_presets(self, context, add_new=False)



class PLATINGGEN_PT_GeneralPanel(bpy.types.Panel):
    """Plating Generator Main Panel"""
    bl_idname = "PLATINGGEN_PT_GeneralPanel"
    bl_label = "Plating Generator"
    bl_category = "Plating Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw_header_preset(self, context):
        layout = self.layout
        row = layout.row()
        row.separator()
        
        if context.active_object and context.active_object.plating_generator.is_plating_obj and context.active_object.mode == 'OBJECT':
            row.menu(OBJECT_MT_plating_generator_presets_menu.bl_idname, icon='PRESET', text='')

        row.operator("platinggen.open_url", icon='QUESTION', text="").url = "https://plating-generator-docs.readthedocs.io/"
        row.separator()

    def draw(self, context):

        layout = self.layout
        col = layout.column()

        if context.active_object and context.active_object.plating_generator.is_plating_obj:
            if  context.active_object.mode == 'OBJECT' :
                obj = context.active_object
                plating_generator = obj.plating_generator
                row = col.row(align=True)
                row.prop(plating_generator, 'master_seed')
                row.operator('platinggen.rand_master_seed', text='', icon = 'FILE_REFRESH' )
                row = col.row(align=True)
                row.operator('platinggen.update', text='Update')
                row.prop(obj.plating_generator, 'auto_update', text="", icon= 'PROP_ON' if obj.plating_generator.auto_update else 'PROP_OFF' )
            else:
                col.label(text='Cannot change parameters in EDIT mode.')
        else:
            col.label(text='Please select a Plating Object.')


class PLATINGGEN_PT_StackPanel(bpy.types.Panel):
    """Plating Generator Panel"""
    bl_idname = "PLATINGGEN_PT_StackPanel"
    bl_label = "Levels"
    bl_category = "Plating Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = 'PLATINGGEN_PT_GeneralPanel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj and context.active_object.mode == 'OBJECT'

    def draw(self, context):

        if context.active_object and context.active_object.plating_generator.is_plating_obj:

            obj = context.active_object
            plating_generator = obj.plating_generator
            layout = self.layout
            col = layout.column()
            col.template_list("PLATINGGEN_ENTRY_UL_List", "The_List", plating_generator, "levels", plating_generator, "level_index", type='DEFAULT')
            row = col.row(align=True)
            row.operator("platinggen.add_level", text="Add")
            row.operator("platinggen.duplicate_entry", text="Copy")
            row.operator("platinggen.move_entry", icon="TRIA_UP", text='').direction = 'UP' 
            row.operator("platinggen.move_entry", icon="TRIA_DOWN", text='').direction = 'DOWN'



class PLATINGGEN_PT_PropertiesPanel(bpy.types.Panel):
    """Plating Generator Panel"""
    bl_idname = "PLATINGGEN_PT_PropertiesPanel"
    bl_label = "Properties"
    bl_category = "Plating Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = 'PLATINGGEN_PT_GeneralPanel'

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj and context.active_object.mode == 'OBJECT'

    def draw(self, context):

        if context.active_object and context.active_object.plating_generator.is_plating_obj:
            obj = context.active_object
            plating_generator = obj.plating_generator

            layout = self.layout
            col = layout.column()

            if plating_generator.level_index >= len(plating_generator.levels):
                return

            level = plating_generator.levels[plating_generator.level_index]

            row = col.row(align=True)
            row.label(text='', icon='VIEW_PERSPECTIVE' if level.type == 'PlatingGeneratorDecorator' else 'PARTICLE_POINT')
            row.separator()
            split = row.split(align=True, factor=0.1)
            split.prop(level, 'level_color', text='')
            split.prop(level, 'level_name', text='')
            enabled_row = row.row(align=True)
            enabled_row.alert = not level.is_enabled
            enabled_row.prop(level, 'is_enabled', text="", icon="CHECKBOX_HLT" if level.is_enabled else "CHECKBOX_DEHLT")
        
            col.separator()
            col.row(align=True).prop(level, 'type', expand=True)

            if plating_generator.levels.find(level.name) != 0:
                col.separator()
                col.prop(level, 'selection_level')
                col.row().prop(level, 'selection_type')
            col.separator() 

            # if plating_generator.level_index != 0:
            if level.type == 'PlatingGeneratorDecorator':
                selection_amount_row = col.row(align=True)
                selection_amount_row.prop(level, 'selection_amount', text="Selection Amount")
                selection_amount_row.prop(level, 'select_remaining', text="", icon="SELECT_SUBTRACT")
                selection_amount_row.operator('platinggen.rand_sel_seed', text="", icon = "FILE_REFRESH").level_index = plating_generator.level_index

            col.prop(level, 'min_selection_area', text="Minimum Face Area")

            


            col.separator() 

            if level.type == 'PlatingGeneratorDecorator':
                plating_ui.draw(level.plating_props, context, col)
            elif level.type == 'GreebleDecorator':
                greeble_ui.draw(level.greeble_props, context, col)
            col.prop(obj.plating_generator, 'generate_uvs', text="Generate UV Map")
            col_uv_limit = col.column()
            col_uv_limit.enabled = obj.plating_generator.generate_uvs
            col_uv_limit.prop(obj.plating_generator, 'uv_projection_limit', text="UV Projection Limit")
            col.prop(obj.data, "use_auto_smooth")
            col_smooth_angle = col.column()
            col_smooth_angle.enabled =  obj.data.use_auto_smooth
            col_smooth_angle.prop(obj.data, "auto_smooth_angle")



class PLATINGGEN_PT_UI_PT_IteratorPanel(Panel):
    """Properties panel for iterator controls."""
    bl_idname = "PLATINGGEN_PT_Panel_Iterator"
    bl_label = "Iterator"
    bl_category = "Plating Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = 'PLATINGGEN_PT_GeneralPanel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj and context.active_object.mode == 'OBJECT'

    def draw(self, context):
        """Draw all options for the user to input to."""
        layout = self.layout

        config = context.scene.plating_generator_iterator

        col = layout.column()
        col.label(text='Seed Range')
        row = col.row(align=True)
        row.prop(config, 'start_seed', text="")
        row.prop(config, 'end_seed', text="")

        col.label(text='File Path')
        col.prop(config, 'file_path', text="")

        col.label(text='Render Engine')
        col.prop(config, 'render_engine', text="")

        col.separator()
        col.operator('mesh.plating_generator_iterator', text='Start')

        if not bpy.data.filepath:
            col_warn = col.column()
            col_warn.alert = True
            col_warn.label(text="Save .blend file before proceeding")


class PLATINGGEN_UI_PT_LoadSavePanel(bpy.types.Panel):
    """Properties panel for add-on operators."""
    bl_idname = "PLATINGGEN_PT_Panel_LoadSave"
    bl_label = "Presets"
    bl_category = "Plating Generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = 'PLATINGGEN_PT_GeneralPanel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj and context.active_object.mode == 'OBJECT'

    def draw(self, context):
        """Draw all options for the user to input to."""
        layout = self.layout
        scene = context.scene
        # preference = get_current_layer(context)
        # if preference == None:
        #     layout.label(text="No Layer Selected")
        #     return
        # option = addon.option()


            
        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        row.operator('mesh.plating_generator_open_filebrowser', text='Load Preset')

        box = layout.box()
        col = box.column(align=True)
        col.alignment='CENTER'
        row = col.row(align=True)

        col.operator('mesh.plating_generator_save_filebrowser', text='Save Preset')

##################################################
# Menu Classes for right-click options
##################################################

class OBJECT_MT_plating_generator_objs_selection_copy(Menu):
    bl_idname = 'OBJECT_MT_plating_generator_objs_selection_copy'
    bl_label = 'Copy Plating From: '

    def draw(self, context):
        layout = self.layout
        plating_objects = [obj for obj in bpy.data.objects if obj.plating_generator.is_plating_obj and obj.plating_generator.parent_obj == context.active_object]
        for plating_object in plating_objects:
            props = layout.operator(PLATINGGEN_OT_UpdatePlatingSelection.bl_idname, text=plating_object.name)
            props.obj_ref = plating_object.name
            props.copy_obj = True


class OBJECT_MT_plating_generator_objs_selection(Menu):
    bl_idname = 'OBJECT_MT_plating_generator_objs_selection'
    bl_label = 'Update Plating Selection For: '

    def draw(self, context):
        layout = self.layout
        plating_objects = [obj for obj in bpy.data.objects if obj.plating_generator.is_plating_obj and obj.plating_generator.parent_obj == context.active_object]
        for plating_object in plating_objects:
            props = layout.operator(PLATINGGEN_OT_UpdatePlatingSelection.bl_idname, text=plating_object.name)
            props.obj_ref = plating_object.name
            props.copy_obj = False

class OBJECT_MT_plating_generator_objs(Menu):
    bl_idname = 'OBJECT_MT_plating_generator_objs'
    bl_label = 'Select Faces For: '

    def draw(self, context):
        layout = self.layout
        plating_objects = [obj for obj in bpy.data.objects if obj.plating_generator.is_plating_obj and obj.plating_generator.parent_obj == context.active_object]
        for plating_object in plating_objects:
            layout.operator(PLATINGGEN_OT_SelectFromObject.bl_idname, text=plating_object.name).obj_ref = plating_object.name

import os
my_bundled_presets = ''
panel_presets = ''
class OBJECT_MT_plating_generator_presets(Menu):
    bl_idname = 'OBJECT_MT_plating_generator_presets'
    bl_label = 'Add Preset: '

    def draw(self, context):
        draw_presets(self, context, add_new=True)

        
class OBJECT_MT_plating_generator(Menu):
    bl_idname = 'OBJECT_MT_plating_generator'
    bl_label = 'Plating Generator'

    def draw(self, context):
        layout = self.layout
        if context.active_object and context.active_object.mode == 'EDIT':
            layout.label(text="Non-Destructive: ")
        layout.operator(MESH_OT_PlateGeneratorCreateNewOperator.bl_idname, icon='VIEW_PERSPECTIVE', text="Add Plates").level_type="PlatingGeneratorDecorator"
        layout.operator(MESH_OT_PlateGeneratorCreateNewOperator.bl_idname, icon='PARTICLE_POINT', text="Add Greebles").level_type="GreebleDecorator"
        layout.menu(OBJECT_MT_plating_generator_presets.bl_idname, icon='PRESET')
        
        if context.active_object and context.active_object.mode == 'EDIT':
            layout.separator()
            layout.label(text="Destructive: ")
            layout.operator(MESH_OT_PlateGeneratorOperator.bl_idname, icon='VIEW_PERSPECTIVE', text="Add Plates to Mesh")
            layout.operator(MESH_OT_GreebleGeneratorOperator.bl_idname, icon='PARTICLE_POINT', text="Add Greebles to Mesh")
            props = layout.operator(MESH_OT_PlateGeneratorPanelLineOperator.bl_idname, icon='MESH_GRID', text="Add Panel Lines to Mesh")
            props.pattern_type = '1'
            props.select_plates = False
            props.select_grooves = True
            plating_objects = [obj for obj in bpy.data.objects if obj.plating_generator.is_plating_obj and obj.plating_generator.parent_obj == context.active_object]
            if plating_objects:
                layout.separator()
                layout.menu(OBJECT_MT_plating_generator_objs_selection.bl_idname, icon='SELECT_EXTEND')
                layout.menu(OBJECT_MT_plating_generator_objs_selection_copy.bl_idname, icon='COPYDOWN')
                layout.menu(OBJECT_MT_plating_generator_objs.bl_idname, icon='RESTRICT_SELECT_OFF')


classes = [
    PLATINGGEN_ENTRY_UL_List,
    PLATINGGEN_PT_GeneralPanel,
    PLATINGGEN_PT_StackPanel,
    PLATINGGEN_PT_PropertiesPanel,
    PLATINGGEN_PT_UI_PT_IteratorPanel,
    OBJECT_MT_plating_generator_objs_selection_copy,
    OBJECT_MT_plating_generator_objs_selection,
    OBJECT_MT_plating_generator_objs,
    OBJECT_MT_plating_generator,
    PLATINGGEN_MT_PlatingGenPresets,
    OBJECT_MT_plating_generator_presets,
    OBJECT_MT_plating_generator_presets_menu
    ]

def menu_func(self, context):
    self.layout.menu(OBJECT_MT_plating_generator.bl_idname)

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_func)   
    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)   


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func)   
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)   
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)


    for cls in classes:
        unregister_class(cls)