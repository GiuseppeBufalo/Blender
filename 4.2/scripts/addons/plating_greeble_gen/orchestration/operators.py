##################################################################
#### Class defining all operators related to orchestration.
##################################################################

import bpy
import bmesh
from bpy.types import Operator, Menu
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty
        )

from bpy.utils import register_class, unregister_class

import uuid
from . import decorators
from ..plating_gen.plating_util import plating_poll
from ..greeble_gen.greeble_generator import init_greebles
from .. import preferences
import numpy as np
import colorsys
import os
import time
import json

from bpy_extras.io_utils import ExportHelper, ImportHelper

from .. encoding.encoding import PresetEncoder, decode_preset

# location of presets diretory for orchestration.
preset_dir = 'operator/mesh.plating_generator'

def add_level(obj):
    """Core Method for adding new levels"""

    # intitially set auto update on the level to false to prevent updates.
    old_auto_update = obj.plating_generator.auto_update
    obj.plating_generator.auto_update = False
    levels = obj.plating_generator.levels

    # add the level.
    level = levels.add()
    level.name = str(uuid.uuid4())
    level.type = "PlatingGeneratorDecorator"

    # assign a random color.
    rgb = colorsys.hsv_to_rgb(np.random.uniform(), 1, 1)
    level.level_color[0] = rgb[0]
    level.level_color[1] = rgb[1]
    level.level_color[2] = rgb[2]

    # as we are in "Non Destructive" mode, set some custom properties; groove depth should be zero but other plate heights should be set slightly higher.
    level.plating_props.groove_depth = 0
    level.plating_props.remove_inner_grooves = True
    level.plating_props.plate_min_height = 0.01
    level.plating_props.plate_max_height = 0.01


    # intialise some greeble references in case we need them later.
    init_greebles(level.greeble_props)

    # intitially, the selection level will be set to zero (the default level, e.g. original object.)
    level.selection_level = str(0)

    # if there is only one level, ensure it is set to enabled. Otherwise, disable the level and let the user decide.
    if len(levels) == 1:
        level.is_enabled=True

    # set the appropriate reference index.
    obj.plating_generator.level_index = len(levels) - 1
    obj.plating_generator.auto_update = old_auto_update
    return level

def validate_levels(levels):
    """Check that all levels are consitent, e.g. selection levels reference a valid level."""
    changed = False
    i = 0
    for level in levels:
        if not level.selection_level or int(level.selection_level) >= len(levels):
            level.selection_level = str(i) # This will set it to the level below.
            if level.is_enabled:
                changed = True
        i+=1
    return changed

class PLATINGGEN_OT_AddEntry(Operator): 
    """Add a Level""" 
    bl_idname = "platinggen.add_level" 
    bl_label = "Adds an Entry" 
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj

    def execute(self, context): 
        obj = context.active_object
        add_level(obj)        
        return{'FINISHED'}

class PLATINGGEN_OT_DeleteEntry(Operator): 
    """Delete the selected level entry""" 
    bl_idname = "platinggen.delete_level" 
    bl_label = "Deletes a level entry" 
    bl_options = {'INTERNAL', 'UNDO'}

    item_index_to_delete : IntProperty(default=-1)

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj

    def execute(self, context): 
        config = context.active_object.plating_generator
        levels = config.levels
        index = self.item_index_to_delete
        was_enabled = levels[index].is_enabled
        levels.remove(index) 

        # make sure there is always one entry though...
        if not len(levels):
            bpy.ops.platinggen.add_level('INVOKE_DEFAULT')
        else:
            config.level_index = min(max(0, index - 1), len(levels) - 1)
        
        changed = validate_levels(levels)

        if changed or was_enabled:
            decorators.decorate(context.active_object, context)
        
        return{'FINISHED'}

class PLATINGGEN_OT_RandomizeSelectionSeed(Operator): 
    """Randomise Seed""" 
    bl_idname = "platinggen.rand_sel_seed" 
    bl_label = "Randomise selection seed on level" 
    bl_options = {'INTERNAL', 'UNDO'}

    level_index : IntProperty(min=0)

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj

    def execute(self, context): 
        level = context.active_object.plating_generator.levels[self.level_index]
        level.selection_amount_seed = np.random.randint(99999)
        return{'FINISHED'}

class PLATINGGEN_OT_RandomizeMasterSeed(Operator): 
    """Randomise Seed""" 
    bl_idname = "platinggen.rand_master_seed" 
    bl_label = "Randomise master seed" 
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj

    def execute(self, context): 
        props = context.active_object.plating_generator
        props.master_seed = np.random.randint(99999)
        return{'FINISHED'}

class PLATINGGEN_OT_MoveEntry(Operator): 
    """Move the level up or down""" 
    bl_idname = "platinggen.move_entry" 
    bl_label = "Move level" 
    direction : bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),)) 
    bl_options = {'INTERNAL', 'UNDO'}
    
    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj

    def move_index(self, context): 
        """ Move index of an item render queue while clamping it. """ 
        config =  context.active_object.plating_generator
        index = config.level_index
        list_length = len(config.levels) - 1 # (index starts at 0) 
        new_index = index + (-1 if self.direction == 'UP' else 1) 
        
        config.level_index = max(0, min(new_index, list_length)) 
        
    def execute(self, context): 
        my_list = context.active_object.plating_generator.levels
        index = context.active_object.plating_generator.level_index
        neighbor = index + (-1 if self.direction == 'UP' else 1) 
        
        my_list.move(neighbor, index) 
        self.move_index(context) 

        
        changed = validate_levels(my_list)

        if changed or my_list[index].is_enabled:
            decorators.decorate(context.active_object, context)

        return{'FINISHED'}

class PLATINGGEN_OT_DuplicateEntry(Operator): 
    """Duplicate the selected Level entry""" 
    bl_idname = "platinggen.duplicate_entry" 
    bl_label = "Duplicate an Entry" 
    bl_options = {'INTERNAL', 'UNDO'}


    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj


    def execute(self, context): 


        config = context.active_object.plating_generator
        entries = config.levels
        index = config.level_index

        if index >= 0 and index < len(entries):
            entry_to_copy = entries[index]

            new_entry = entries.add()
            

            for k, v in entry_to_copy.items():
                if k != 'is_enabled':
                    new_entry[k] = v

            new_entry.name = str(uuid.uuid4())

            new_entry.level_name += ' Copy'


            config.entry_index = len(entries) - 1
            
        else:
            return {'CANCELLED'}
        
        return{'FINISHED'}


class PLATINGGEN_OT_SelectFromObject(Operator): 
    """Select Faces associated with a Plating Object""" 
    bl_idname = "platinggen.select_from_object" 
    bl_label = "Select From Object" 
    bl_options = {'INTERNAL', 'UNDO'}

    obj_ref : StringProperty(default='')

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.mode == 'EDIT'

    def execute(self, context): 
        if self.obj_ref not in bpy.data.objects:
            return{'CANCELLED'}
        
        plating_obj = bpy.data.objects[self.obj_ref]
        if not plating_obj.plating_generator.is_plating_obj:
            return{'CANCELLED'}

        face_ids = [face_ref.face_id for face_ref in plating_obj.plating_generator.face_ids]
        edge_ids = [edge_ref.edge_id for edge_ref in plating_obj.plating_generator.edge_ids]

        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        for f in bm.faces:
            f.select_set(False)
        for face_id in face_ids:
            try:
                bm.faces[face_id].select_set(True)
            except IndexError:
                pass
        for edge_id in edge_ids:
            try:
                bm.edges[edge_id].select_set(True)
            except IndexError:
                pass

        bmesh.update_edit_mesh(obj.data)
        return{'FINISHED'}


class PLATINGGEN_OT_UpdatePlatingSelection(Operator): 
    """Plating Object""" 
    bl_idname = "platinggen.update_plating_selection" 
    bl_label = "Update Plating Selection" 
    bl_options = {'INTERNAL', 'UNDO'}

    obj_ref : StringProperty(default='')

    copy_obj : BoolProperty(default=False)

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.mode == 'EDIT'

    def execute(self, context): 
        if self.obj_ref not in bpy.data.objects:
            return{'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')
        old_active = context.active_object
        context.view_layer.objects.active = bpy.data.objects[self.obj_ref]
        plating_obj = bpy.data.objects[self.obj_ref]
        if not plating_obj.plating_generator.is_plating_obj:
            return{'CANCELLED'}

        if self.copy_obj:
            old_auto_update = plating_obj.plating_generator.auto_update
            old_plating_obj = plating_obj
            plating_obj.plating_generator.auto_update = False
            new_data = plating_obj.data.copy()
            plating_obj = plating_obj.copy()
            plating_obj.data = new_data
            plating_obj.animation_data_clear()
            context.collection.objects.link(plating_obj)
            plating_obj.plating_generator.auto_update = old_auto_update
            old_plating_obj.plating_generator.auto_update = old_auto_update

        plating_obj.plating_generator.face_ids.clear()
        plating_obj.plating_generator.edge_ids.clear()
        obj = old_active


        bm = bmesh.new()
        bm.from_mesh(obj.data)
        for f in bm.faces:
            if f.select:
                plating_obj.plating_generator.face_ids.add().face_id = f.index
        for e in bm.edges:
            if e.select:
                plating_obj.plating_generator.edge_ids.add().edge_id = e.index
        bm.free()
        decorators.decorate(plating_obj, context)
        context.view_layer.objects.active = old_active
        bpy.ops.object.mode_set(mode='EDIT')
        return{'FINISHED'}


class PLATINGGEN_OT_Update(Operator): 
    """Update the Plating Object""" 
    bl_idname = "platinggen.update" 
    bl_label = "Update Object" 
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj

    def execute(self, context): 
        decorators.decorate(context.active_object, context)
        return{'FINISHED'}



def get_config(context):
    return context.active_object.plating_generator
class PLATINGGEN_OT_Iterator(bpy.types.Operator):
    """Start Plating Generator Iterator"""
    bl_idname = "mesh.plating_generator_iterator"
    bl_label = "Plating Generator Iterator Run"
    bl_options = {"INTERNAL", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.plating_generator.is_plating_obj and bpy.data.filepath

    def execute(self, context):
        file_path = context.scene.plating_generator_iterator.file_path
        start_seed = context.scene.plating_generator_iterator.start_seed
        end_seed = context.scene.plating_generator_iterator.end_seed

        config = get_config(context)

        auto_update_was_false = not config.auto_update
        if auto_update_was_false:
            config.auto_update = True

        old_master_seed = config.master_seed
        old_file_path = context.scene.render.filepath
        old_render_engine = context.scene.render.engine

        wm = bpy.context.window_manager
        wm.progress_begin(0, abs(end_seed - start_seed) + 1)

        try:

            if context.scene.plating_generator_iterator.render_engine != 'SAME':
                # temporarily set the render engine.
                context.scene.render.engine = context.scene.plating_generator_iterator.render_engine 

        
            if not os.path.exists(file_path):
                os.makedirs(file_path)

            ack_path = os.path.join(file_path, 'running.ack')
            open(ack_path, 'a').close()

            i = 0
            for seed in range(start_seed, end_seed + 1):
                start = time.time()

                # first check if we should abort because the .ack file is no longer there.
                try:
                    f = open (ack_path)
                except IOError:
                    # abort the run if there is an error opening the file.
                    report_message = 'ITERATE run aborted.'
                    self.report({'INFO'}, report_message)
                    break
                finally:
                    f.close()

                print('Commence Iterator with SEED: ', seed)

                # perform the next iteraton.
                config.master_seed = seed
                context.scene.render.filepath = os.path.join(file_path, 'plating_generator_' + str(seed))
                try:
                    bpy.ops.render.render(write_still = True)
                except RuntimeError as re:
                    self.report({'ERROR'}, "An error occured: " + str(re) + ' Is the image open in another program?')
                    return {'CANCELLED'}

                end = time.time()

                print('Plating Generator Time Taken: ', str(end-start))

                i += 1
                wm.progress_update(i)

        finally:
            config.master_seed = old_master_seed
            if auto_update_was_false:
                config.auto_update = False
            context.scene.render.filepath = old_file_path
            context.scene.render.engine = old_render_engine
            wm.progress_end()

        return {'FINISHED'}


################
# PRESETS
################
class PLATINGGEN_OT_ExecutePlatingGenPreset(bpy.types.Operator):
    """Execute a preset"""
    bl_idname = "script.platinggen_execute_preset"
    bl_label = "Execute a Python Preset"
    bl_options = {'INTERNAL', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )
    menu_idname: StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE'},
        default='PLATINGGEN_PT_presets'
    )
    add_new : BoolProperty(default=False)

    @classmethod
    def poll(self, context):
        return plating_poll(self, context)

    def execute(self, context):
        if self.add_new:
            bpy.ops.mesh.plates_generate_new()

        from os.path import basename, splitext
        filepath = self.filepath

        # change the menu title to the most recently chosen option
        preset_class = getattr(bpy.types, self.menu_idname)
        preset_class.bl_label = bpy.path.display_name(basename(filepath), title_case=False)

        ext = splitext(filepath)[1].lower()

        if ext not in {".py", ".xml"}:
            self.report({'ERROR'}, "Unknown file type: %r" % ext)
            return {'CANCELLED'}

        if hasattr(preset_class, "reset_cb"):
            preset_class.reset_cb(context)

        if ext == ".py":
            context.active_object.plating_generator.auto_update = False
            try:

                count = 0
                with open(filepath) as fp:
                    Lines = fp.readlines()
                    for line in Lines:
                        try:
                            exec(line)
                        except KeyError:
                            pass


            except Exception as ex:
                self.report({'ERROR'}, "Failed to execute the preset: " + repr(ex))
            finally:
                context.active_object.plating_generator.auto_update = True
            decorators.decorate(context.active_object, context)

        elif ext == ".xml":
            import rna_xml
            rna_xml.xml_file_run(context,
                                 filepath,
                                 preset_class.preset_xml_map)

        if hasattr(preset_class, "post_cb"):
            preset_class.post_cb(context)

        return {'FINISHED'}

from bl_operators.presets import AddPresetBase

class PLATINGGEN_OT_AddPlatingGenPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'mesh.add_platinggen_preset'
    bl_label = 'Manage Preset'
    bl_description = "Remove old preset"
    preset_menu = 'PLATINGGEN_MT_PlatingGenPresets'

    bl_options = {'INTERNAL', 'UNDO'}

    # Common variable used for all preset values
    preset_defines = [
                        'op = bpy.context.active_object.plating_generator'
                     ]

    # Properties to store in the preset
    preset_values = [
                    'op.master_seed',
                    'op.levels'
                    ]

    # Directory to store the presets
    preset_subdir = preset_dir


######################################################
# RECIPE PRESETS
######################################################

def load_file(context, filepath):

    with open(filepath) as json_file:
        old_update_state = context.active_object.plating_generator.auto_update
        context.active_object.plating_generator.auto_update = False
        try:
            recipeJSON = json.load(json_file)
            decode_preset(recipeJSON, context)
            
            decorators.decorate(context.active_object, context)

            context.area.tag_redraw()
        finally:
            context.active_object.plating_generator.auto_update = old_update_state


class PLATINGGEN_OT_OpenFile(Operator): 
    bl_idname = "mesh.plating_generator_open" 
    bl_label = "LOAD" 
    bl_description = 'Open Preset'
    bl_options = {'INTERNAL', 'UNDO'}

    file_path : StringProperty()

    add_new : BoolProperty(default=False)

    @classmethod
    def poll(self, context):
        return plating_poll(self, context)

    def execute(self, context): 

        if self.add_new:
            bpy.ops.mesh.plates_generate_new()

        load_file(context, self.file_path)

        return {'FINISHED'}

class PLATINGGEN_OT_OpenFilebrowser(Operator, ImportHelper): 
    bl_idname = "mesh.plating_generator_open_filebrowser" 
    bl_label = "LOAD" 
    bl_description = 'Open Preset'
    bl_options = {'INTERNAL', 'UNDO'}

    filter_glob: StringProperty( 
        default='*.json', 
        options={'HIDDEN'} ) 
        
    def execute(self, context): 
        """Do something with the selected file(s)""" 
        filename, extension = os.path.splitext(self.filepath) 
            
        load_file(context, self.filepath)
                
        return {'FINISHED'}

class PLATINGGEN_OT_SaveFilebrowser(bpy.types.Operator, ExportHelper):
    bl_idname = "mesh.plating_generator_save_filebrowser" 
    bl_label = "SAVE"
    bl_description = 'Save Preset'
    bl_options = {'INTERNAL', 'UNDO'}
    
    filename_ext = ".json"  # ExportHelper mixin class uses this    

    def execute(self, context):
        filepath = self.filepath

        # encode dict as JSON 
        data = json.dumps(context.active_object.plating_generator, indent=4, cls=PresetEncoder)

        # write JSON file
        with open(filepath, 'w') as outfile:
            outfile.write(data + '\n')

        return{'FINISHED'}




class PLATINGGEN_OT_OpenHelpURL(Operator):
    bl_idname = "mesh.plating_generator_open_help_url" 
    bl_label = "Help"
    bl_description = 'Open Plating Generator documentation'
    bl_options = {'INTERNAL', 'UNDO'}
    
    url : StringProperty()

    def execute(self, context):
        bpy.ops.wm.url_open(url = self.url)
        return {'FINISHED'}

class PLATINGGEN_OT_OpenURL(Operator):
    bl_idname = "platinggen.open_url" 
    bl_label = "openurl"
    bl_description = 'Open URL'
    bl_options = {'INTERNAL', 'UNDO'}
    
    url : StringProperty()

    def execute(self, context):
        bpy.ops.wm.url_open(url = self.url)
        return {'FINISHED'}


class PLATINGGEN_OT_AddPresetFolder(Operator): 
    """Add a Preset Folder""" 
    bl_idname = "platinggen.add_preset_folder" 
    bl_label = "Adds a preset folder entry" 
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context): 
        
        pref = preferences.preference()

        pref.presets_folders.add()

        return{'FINISHED'}

class PLATINGGEN_OT_DeletePresetFolder(Operator): 
    """Delete the selected level entry""" 
    bl_idname = "platinggen.delete_preset_folder" 
    bl_label = "Deletes a preset folder entry" 
    bl_options = {'INTERNAL', 'UNDO'}

    item_index_to_delete : IntProperty(default=-1)

    def execute(self, context): 
        index = self.item_index_to_delete
        pref = preferences.preference()
        presets_folders = pref.presets_folders
        
        presets_folders.remove(index) 
        
        return{'FINISHED'}

class PLATINGGEN_OT_MovePresetFolder(Operator): 
    """Move the level up or down""" 
    bl_idname = "platinggen.move_preset_folder" 
    bl_label = "Move Preset Folder" 
    direction : bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),)) 
    bl_options = {'INTERNAL', 'UNDO'}

    item_index : IntProperty(default=-1)

    # def move_index(self, context): 
    #     """ Move index of an item render queue while clamping it. """ 
    #     pref = preferences.preference()
    #     index = self.item_index
    #     presets_folders = pref.presets_folders

    #     list_length = len(presets_folders) - 1 # (index starts at 0) 
    #     new_index = index + (-1 if self.direction == 'UP' else 1) 
        
    #     config.level_index = max(0, min(new_index, list_length)) 

        
    def execute(self, context): 

        
        pref = preferences.preference()
        my_list = pref.presets_folders
        index = self.item_index

        neighbor = index + (-1 if self.direction == 'UP' else 1) 
        
        my_list.move(neighbor, index)

        return{'FINISHED'}


        

classes = [
    PLATINGGEN_OT_AddEntry,
    PLATINGGEN_OT_DeleteEntry,
    PLATINGGEN_OT_RandomizeSelectionSeed,
    PLATINGGEN_OT_RandomizeMasterSeed,
    PLATINGGEN_OT_MoveEntry,
    PLATINGGEN_OT_DuplicateEntry,
    PLATINGGEN_OT_SelectFromObject,
    PLATINGGEN_OT_UpdatePlatingSelection,
    PLATINGGEN_OT_ExecutePlatingGenPreset,
    PLATINGGEN_OT_AddPlatingGenPreset,
    PLATINGGEN_OT_Update,
    PLATINGGEN_OT_Iterator,
    PLATINGGEN_OT_OpenFilebrowser,
    PLATINGGEN_OT_SaveFilebrowser,
    PLATINGGEN_OT_OpenHelpURL,
    PLATINGGEN_OT_OpenFile,
    PLATINGGEN_OT_OpenURL,
    PLATINGGEN_OT_AddPresetFolder,
    PLATINGGEN_OT_DeletePresetFolder,
    PLATINGGEN_OT_MovePresetFolder
    ]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)