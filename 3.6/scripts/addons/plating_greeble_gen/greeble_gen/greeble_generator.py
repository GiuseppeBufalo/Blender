import bpy
import bmesh
from .greeble_props import GreebleProps, handle_greeble_entries
from . import greeble_ui
from . import greeble_functions
from . import greeble_factory
from .. import preferences
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        FloatVectorProperty,
        EnumProperty
        )
import uuid
import os

def init_greebles(self):
    pref = preferences.preference()
    catalogue = pref.catalogue
    if self.load_greebles:
        default_greeble_metas = greeble_factory.get_greebles_metadata_from_category(catalogue, catalogue.default_category)
        for default_greeble_meta in default_greeble_metas:
            default_greeble = self.library_greebles.add()
            default_greeble.name = str(uuid.uuid4())
            default_greeble.thumbnail = default_greeble_meta.greeble_name
            default_greeble.file_path = default_greeble_meta.file_path
        self.load_greebles = False


#
# Class that contains plate creation logic.
#
class GreebleGenerator(GreebleProps):
    """Generate Greeble Objects"""

    def invoke(self, context, event):
        self.scene_objects.clear()
        for object in context.scene.objects:
            if object.type == "MESH":
                item = self.scene_objects.add()
                item.name = object.name

        # Get any selected objects that aren't the active one and add to custom settings.
        custom_names = []
        for custom_greeble in self.custom_greebles:
            name = getattr(custom_greeble, "name")
            custom_names.append(name)

        for selected_object in context.selected_objects:
            if selected_object.type == "MESH" and  selected_object != context.view_layer.objects.active:
                if selected_object.name not in custom_names:
                    custom_greeble = None
                    for i in range(0, len(self.custom_greebles)):
                        potential_custom_greeble = self.custom_greebles[i]
                        if potential_custom_greeble.name == "":
                            custom_greeble = potential_custom_greeble
                            break
                    if custom_greeble is None:
                        custom_greeble = self.custom_greebles.add()
                    custom_greeble.name = selected_object.name
                    custom_greeble.scene_ref = selected_object.name
                    custom_greeble.coverage = 100
                    custom_greeble.material_index = -1
                    custom_greeble.height_override = 0
                    custom_greeble.keep_aspect_ratio= False

        return self.execute(context)

    # draw out a custom interface as there are a lot of properties.
    def draw(self, context):
        greeble_ui.draw(self, context, self.layout)

    @classmethod
    def poll(cls, context):
        return context.active_object and \
            ((context.active_object.type == 'MESH' and \
            context.active_object.mode == 'OBJECT') or \
            (context.active_object.type == 'MESH' and \
            context.active_object.mode == 'EDIT' and \
            context.scene.tool_settings.mesh_select_mode[2]) or \
            (context.active_object.type == 'MESH' and \
            context.active_object.mode == 'EDIT' and \
            context.scene.tool_settings.mesh_select_mode[1]))

    def execute(self, context):
        if self.update_draw_only:
            self.update_draw_only = False
            return {'PASS_THROUGH'}
        if bpy.ops.object.mode_set.poll():
            
            set_up_create_new(self, context)

            init_greebles(self)
            handle_greeble_entries(self)

            pref = preferences.preference()

            #capture previous edit mode
            previous_mode = bpy.context.active_object.mode
            previous_edit_mode = list(bpy.context.tool_settings.mesh_select_mode)

            # Switching to EDIT edge mode
            bpy.ops.object.mode_set(mode = 'EDIT')

            # read mesh data
            obj = context.edit_object
            me = obj.data
            bm = bmesh.from_edit_mesh(me)

            greeble_functions.greeble_gen_exec(self, obj, bm, context)

            # update the bmmesh
            bmesh.update_edit_mesh(obj.data)
            # NOTE: bm does not need to be freed, see https://developer.blender.org/T39121

            #reset to previous mode
            context.tool_settings.mesh_select_mode = previous_edit_mode

            bpy.ops.object.mode_set(mode = previous_mode)

            finish_complete_new(self, context)

            return {'FINISHED'}
        return {'CANCELLED'}


def set_up_create_new(self, context):
    if self.create_new:
        # mark faces for deletion and copy over after object is created.
        bpy.ops.object.mode_set(mode = 'OBJECT')
        new_obj = context.active_object.copy()
        new_obj.data = context.active_object.data.copy()
        new_obj.name = context.active_object.name + ' greebles'
        users_collection = context.active_object.users_collection
        if len(users_collection) > 0:
            collection = users_collection[0]
            collection.objects.link(new_obj)

        for selected_object in context.selected_objects:
            selected_object.select_set(False)
        context.view_layer.objects.active = new_obj
        context.active_object.select_set(True)

        bm = bmesh.new()
        bm.from_mesh(context.active_object.data)
        try:

            face_was_not_selected_prop = bm.faces.layers.int.new('face_was_not_selected_prop')
            for f in bm.faces:
                f[face_was_not_selected_prop] = 1

            bm.to_mesh(context.active_object.data)

        finally:
            bm.free()

def finish_complete_new(self, context):
    if self.create_new:
        bm = bmesh.new()
        bm.from_mesh(context.active_object.data)
        try:
            face_was_not_selected_prop = bm.faces.layers.int.get('face_was_not_selected_prop')
            unselected_faces = [f for f in bm.faces if f[face_was_not_selected_prop] == 1]            
            
            bmesh.ops.delete(bm, geom=unselected_faces, context='FACES')
            bm.faces.layers.int.remove(face_was_not_selected_prop)
            bm.to_mesh(context.active_object.data)

        finally:
            bm.free()



class MESH_OT_GreebleGeneratorOperator(bpy.types.Operator, GreebleGenerator):
    bl_idname = "mesh.greebles_generate"
    bl_label = "Generate Greebles"
    bl_description ='Create Greebles objects on the selection'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

def refresh_greeble_libraries():
    # Initialise Greeble Library Objects

    # register custom paths.
    pref = preferences.preference()
    catalogue = pref.catalogue
    if len (catalogue.categories) == 0:
        # create default location.
        script_file = os.path.realpath(__file__)
        current_directory = os.path.dirname(script_file)
        directory_path = os.path.join(current_directory, '../Defaults')
        catalogue_entry = catalogue.categories.add()
        catalogue_entry.folder_path = directory_path

    greeble_factory.refresh_greebles(catalogue)

def remove_greeble_libraries():
    # Remove Greeble Library Objects
    greeble_factory.remove()


class MESH_OT_refresh_greebles_path(bpy.types.Operator):
    bl_idname = 'mesh.refresh_greebles_path'
    bl_label = 'Refresh paths'
    bl_description ='Refresh the Greebles libraries'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        refresh_greeble_libraries()
        
        return {'FINISHED'}

class MESH_OT_add_greebles_path(bpy.types.Operator):
    bl_idname = 'mesh.add_greebles_path'
    bl_label = 'Add path'
    bl_description = 'Add a path to a the Greebles libraries'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        preference = preferences.preference()

        folder = preference.catalogue.categories.add()
        folder['location'] = 'Choose Path'
        return {'FINISHED'}

class MESH_OT_remove_greebles_path(bpy.types.Operator):
    bl_idname = 'mesh.remove_greebles_path'
    bl_label = 'Remove path'
    bl_description = 'Remove path'
    bl_options = {'INTERNAL'}

    index: IntProperty()

    def execute(self, context):
        preference = preferences.preference()

        preference.catalogue.categories.remove(self.index)
        return {'FINISHED'}

class MESH_OT_copy_greebles_path(bpy.types.Operator):
    bl_idname = 'mesh.copy_greebles_path'
    bl_label = 'Copy greeble library path'
    bl_description = 'Copy greeble library path'
    bl_options = {'INTERNAL'}

    index: IntProperty()

    def execute(self, context):
        preference = preferences.preference()
        i = 0
        for category in preference.catalogue.categories:
            if i == self.index:
                new_category = preference.catalogue.categories.add()
                new_category.folder_path = category.folder_path
                preference.catalogue.categories.move(len(preference.catalogue.categories) - 1, i)
                break
            i += 1
        return {'FINISHED'}