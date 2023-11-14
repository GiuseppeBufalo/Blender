import bpy
import bmesh
from . import plating_ui
from . import plating_functions
from .plating_props import PlatingGeneratorProps
from .plating_util import plating_poll
from ..orchestration.operators import add_level
from ..orchestration import decorators
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty
        )

import uuid



class PlateGenerator(PlatingGeneratorProps):
    """Generate Plating Pattern"""

    # draw out a custom interface as there are a lot of properties.
    def draw(self, context):
        plating_ui.draw(self, context, self.layout)

    @classmethod
    def poll(cls, context):
        return plating_poll(cls, context)

    def execute(self, context):
        return plating_functions.plating_gen_execute(self, context)

    def check(self, context):
        return True

class PlateGeneratorCreateNew(PlateGenerator):
    """Generate Plating Pattern on a new object"""

    groove_depth : FloatProperty(
        name="Groove Depth",
        description="Depth of grooves",
        default=0,
        precision=3,
        step=1
        )

    plate_min_height : FloatProperty(
            name="Min Plate Height",
            description="Minimum Plate Height",
            default=0.01,
            precision=3,
            step=1
            )

    plate_max_height : FloatProperty(
            name="Max Plate Height",
            description="Maximum Plate Height",
            default=0.01,
            precision=3,
            step=1
            )


    remove_inner_grooves : BoolProperty(
            name="Remove Inner Grooves",
            description="Remove the inner grooves, not the bevels, to just leave the plates",
            default=True
            )

    level_type : StringProperty(default="PlatingGeneratorDecorator")


    def execute(self, context):
        if self.update_draw_only:
            self.update_draw_only = False
            return {'PASS_THROUGH'}
        
        # mark faces for deletion and copy over after object is created.
        bpy.ops.object.mode_set(mode = 'OBJECT')
        new_obj = context.active_object.copy()
        new_obj.data = context.active_object.data.copy()
        no_objects = [obj for obj in bpy.data.objects if obj.plating_generator.parent_obj == context.active_object]
        suffix = ''
        if len(no_objects):
            suffix = ' ' + str(len(no_objects))
        new_obj.name = context.active_object.name + ' plating' + suffix


        old_active_auto_update = context.active_object.plating_generator.auto_update
        context.active_object.plating_generator.auto_update = False

        # NEW ORCHESTRATION
        #set an initial level to plating.

        new_obj.plating_generator.levels.clear()
        new_obj.plating_generator.face_ids.clear()
        new_obj.plating_generator.edge_ids.clear()
        new_obj.plating_generator.parent_obj = context.active_object
        new_obj.plating_generator.auto_update = False
        bm = bmesh.new()
        bm.from_mesh(context.active_object.data)
        for f in bm.faces:
            if f.select:
                new_obj.plating_generator.face_ids.add().face_id = f.index
        for e in bm.edges:
            if e.select:
                new_obj.plating_generator.edge_ids.add().edge_id = e.index
        bm.free()


        level = add_level(new_obj)
        level.level_name = "Base Level"
        level.type = self.level_type


        # copy to incoming properties onto the collection so we can reference them to change the shape in the future.
        plating_materials_to_copy = []
        for pointer in dir(level.plating_props):
            if '__' in pointer or pointer in {'bl_rna', 'rna_type', 'type', 'face_count', 'falloff_curve', 'vertex_indices', 'vertex_indices_set', 'is_property_group', 'auto_update'}:
                continue

            self_attr = getattr(self, pointer, None)
            
            if self_attr != None:
                try:
                    if pointer in {'plating_materials'}:
                        plating_materials = getattr(self, pointer, None)
                        for plating_material in plating_materials:
                            plating_materials_to_copy.append(plating_material)
                    else:
                        setattr(level.plating_props, pointer, self_attr)
                except AttributeError:
                    print('Trouble copying: ', pointer)
        i = 0
        for plating_material_to_copy in plating_materials_to_copy:
            level.plating_props.plating_materials[i].name = plating_material_to_copy.name
            i+=1

        for attr, value in self.__dict__.items():
            print(attr, value)
            if hasattr(level, attr):
                setattr(level, value)

        users_collection = context.active_object.users_collection
        if len(users_collection) > 0:
            collection = users_collection[0]
            collection.objects.link(new_obj)

        for selected_object in context.selected_objects:
            selected_object.select_set(False)

        context.active_object.plating_generator.auto_update = old_active_auto_update
        context.view_layer.objects.active = new_obj
        context.active_object.select_set(True)

        new_obj.plating_generator.auto_update = True
        new_obj.plating_generator.is_plating_obj = True
        decorators.decorate(context.active_object, context)

        return {'FINISHED'}



class MESH_OT_PlateGeneratorOperator(bpy.types.Operator, PlateGenerator):
    bl_idname = "mesh.plates_generate"
    bl_label = "Generate Plates"
    bl_description ='Create a plating pattern on the selection'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

class MESH_OT_PlateGeneratorPanelLineOperator(bpy.types.Operator, PlateGenerator):
    bl_idname = "mesh.plates_generate_panel_lines"
    bl_label = "Generate Plates"
    bl_description ='Add panel lines using selected edges'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

class MESH_OT_PlateGeneratorCreateNewOperator(bpy.types.Operator, PlateGeneratorCreateNew):
    bl_idname = "mesh.plates_generate_new"
    bl_label = "Generate Plates (Create New Object)"
    bl_description ='Creates a new object with a plating pattern from the selection'
    bl_options = {'INTERNAL', 'UNDO', 'PRESET'}

class MESH_OT_PlateGeneratorAddPlatingMaterial_OT_Operator(bpy.types.Operator):
    """Add a selected source object to the scene properties"""
    bl_idname = "mesh.plating_generator_add_plating_material"
    bl_label = "Plating Generator - add plating material"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        if context.scene.plating_gen_plating_material_to_add is None:
            self.report({'ERROR'}, 'No material to add.')
            return {'CANCELLED'}
            
        new_prop = context.scene.plating_gen_plating_materials.add()
        new_prop.name = context.scene.plating_gen_plating_material_to_add.name
        context.scene.plating_gen_plating_material_to_add = None
        # props.exec_interactive(self, context)
        return {'FINISHED'}

class MESH_OT_PlateGeneratorRemovePlatingMaterial_OT_Operator(bpy.types.Operator):
    """Remove a plating material"""
    bl_idname = "mesh.plating_generator_remove_plating_material"
    bl_label = "Plating Generator - remove plating material"
    bl_options = {"INTERNAL"}

    id_to_remove : bpy.props.IntProperty()

    def execute(self, context):
        for plating_gen_plating_material in context.scene.plating_gen_plating_materials:
            print(plating_gen_plating_material)
            
        context.scene.plating_gen_plating_materials.remove(self.id_to_remove)

        for plating_gen_plating_material in context.scene.plating_gen_plating_materials:
            print(plating_gen_plating_material)

        context.view_layer.update() 
        return {'FINISHED'}
