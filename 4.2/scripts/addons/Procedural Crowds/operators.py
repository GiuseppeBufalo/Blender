from pathlib import Path
import json
import bpy
from bpy.types import Context, Event, Operator
from bpy.props import StringProperty, BoolProperty

from .properties import Procedural_Crowds_Properties


def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def get_gn_mod(obj: bpy.types.Object):
    mod = None
    for m in obj.modifiers:
        if m.type == "NODES" and m.name == 'Procedural_Crowd_GN__ADDON':
            mod = m
            break
    return mod

def handle_geometry_node(obj: bpy.types.Object):
    mod = None
    for m in obj.modifiers:
        if m.type == "NODES":
            mod = m
            break
    if not mod:
        # print("no GN modifiers... returning : ", obj.name)
        return
    
    mod.name = 'Procedural_Crowd_GN__ADDON'
    gn_tree = mod.node_group
    name = gn_tree.name
    # print(name)

    if '.' in name:
        #get original name without .000 
        og_name,suffix = name.rsplit('.',1) #node_group.004 -> node_group
        # print(og_name)

        #check if node_group with og_name exist
        # og_node_group = next(ng for ng in bpy.data.node_groups if ng.name == og_name)
        og_node_group = None
        if og_name in bpy.data.node_groups:
            og_node_group = bpy.data.node_groups[og_name]

        #If og_node_group exist then remove
        if og_node_group:
            # group_node.node_tree.user_clear()
            bpy.data.node_groups.remove(mod.node_group)
            mod.node_group = og_node_group
            mod.node_group.user_remap(og_node_group)

        return gn_tree

def get_collection(collection_name:str, parent_collection:bpy.types.Collection):
    coll = bpy.data.collections.get(collection_name)
    if not coll:
        coll = bpy.data.collections.new(collection_name)
        parent_collection.children.link(coll)
    return coll

def exclude_collection(context, collection_name, exclude = True,):
    def traverse_tree(t):
        yield t
        for child in t.children:
            yield from traverse_tree(child)

    coll = context.view_layer.layer_collection

    for c in traverse_tree(coll):
        if c.name == collection_name:
            c.exclude = exclude 

def redraw_area(area_type:str, context):
    for area in context.screen.areas:
        if area.type == area_type:
            area.tag_redraw()

class Procedural_Crowds_OT_append(Operator):
    
    bl_idname = 'procedural_crowds.append'
    bl_label = "Add Crowd"
    bl_description = "Add Procedural Crowd system with select type of Models"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context) -> bool:
        enabled_modes = ['OBJECT']
        return context.mode in enabled_modes

    def append_required_collections(self, context, metadata):
        # check which animation is needed and append that collection and set it up
        for animation in metadata['animations']:
            model_blend_path = next(self.crowd_model_path.glob(f"{animation}.blend"))

            object_col_name = f'PEOPLE_{animation}'.lower()
            armature_col_name = f'Armatures_{animation}'.lower()

            object_col,armature_col = bpy.data.collections.get(f'PEOPLE_{animation.upper()}_{self.crowd_model.capitalize()}'),bpy.data.collections.get(f'Armatures_{animation.capitalize()}_{self.crowd_model.capitalize()}')

            if object_col is not None:
                object_col_name = ''
            if armature_col is not None:
                armature_col_name = ''

            with bpy.data.libraries.load(str(model_blend_path), link=False) as (data_from, data_to):
                data_to.collections = [col for col in data_from.collections if col.lower() in [object_col_name,armature_col_name]]
            
            collection = get_collection(self.crowd_model,context.scene.collection)
            for col in data_to.collections:
                col.name = f'{col.name}_{self.crowd_model.capitalize()}'
                collection.children.link(col)
                exclude_collection(context,col.name,True)

    def execute(self, context):
        props = context.scene.procedural_crowds
        crowd_system:str = props.crowd_system
        self.crowd_model:str = props.crowd_models

        packs_dir = context.preferences.addons[__package__].preferences.filepath
        crowd_sys_path = Path(packs_dir) / 'Crowd-Systems' / crowd_system
        self.crowd_model_path = Path(packs_dir) / 'Crowd-Models' / self.crowd_model
        sys_blend_path = next(crowd_sys_path.glob("*.blend"))

        with bpy.data.libraries.load(str(sys_blend_path), link=False) as (data_from, data_to):
                data_to.texts = [text for text in data_from.texts if text.lower() == 'metadata.json']
        # read metadata and remove appended text block
        metadata = None
        for text in data_to.texts:
            metadata = json.loads(text.as_string())
            bpy.data.texts.remove(text)

        if 'random walk' in crowd_system.lower():
            with bpy.data.libraries.load(str(sys_blend_path), link=False) as (data_from, data_to):
                data_to.collections = [col for col in data_from.collections if 'random_walk' in col.lower()]
            # duplicate appended collections list 
            collections = data_to.collections[:]

            self.append_required_collections(context,metadata)

            for col in collections:
                context.scene.collection.children.link(col)
                obj = next(obj for obj in col.objects if 'emitter' in obj.name)
                animation = metadata['animations'][0].upper()
                obj.particle_systems[0].settings.instance_collection = bpy.data.collections.get(f'PEOPLE_{animation}_{self.crowd_model.capitalize()}')
                obj.select_set(True)
                context.view_layer.objects.active = obj
        else:
            with_object = metadata["with_object"]
            if with_object:
                # load crowd_system object with gn modifier and load metadata file
                with bpy.data.libraries.load(str(sys_blend_path), link=False) as (data_from, data_to):
                    data_to.objects = [obj for obj in data_from.objects if obj == 'Crowd_System']
                objects = data_to.objects[:]
                for obj in data_to.objects:
                    obj.name = f'{crowd_system}_GN'
                    handle_geometry_node(obj)
                    context.scene.collection.objects.link(obj)
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
            else:
                if context.active_object is None:
                    ShowMessageBox('No Active Object!!!')
                    return {'FINISHED'}
                if not context.active_object.type in metadata['supported_types']:
                    ShowMessageBox(f'{crowd_system} only supports {", ".join(metadata["supported_types"])} type objects' )
                    return {'FINISHED'}
                # check if node-group exist 
                node_group_name = "".join([word.capitalize() for word in crowd_system.split()])+'Crowd'
                node_group = bpy.data.node_groups.get(node_group_name)
                if not node_group: # if not exist
                # load crowd_system object with gn modifier and load metadata file
                    with bpy.data.libraries.load(str(sys_blend_path), link=False) as (data_from, data_to):
                        data_to.node_groups = [ng for ng in data_from.node_groups if ng == node_group_name]

                node_group = bpy.data.node_groups.get(node_group_name)
                # check if active object already has crowd system
                if not 'Procedural_Crowd_GN__ADDON' in context.active_object.modifiers:
                    mod = context.active_object.modifiers.new('Procedural_Crowd_GN__ADDON', type='NODES')
                    mod.node_group = node_group
                else: # Popup Info Message box
                    ShowMessageBox('Object already has crowd system modifier assigned')
                    return {'FINISHED'}
                objects = [context.active_object]
            
            self.append_required_collections(context, metadata)

            for obj in objects:
                gn_mod = get_gn_mod(obj)
                inputs = [inp for inp in gn_mod.node_group.inputs if inp.type == 'COLLECTION']
                # print(inputs, metadata['animations'])
                for input, animation in zip(inputs,metadata['animations']):
                    animation = animation.upper()
                    col = bpy.data.collections.get(f'PEOPLE_{animation}_{self.crowd_model.capitalize()}')
                    gn_mod[input.identifier] = bpy.data.collections.get(f'PEOPLE_{animation}_{self.crowd_model.capitalize()}')

        context.scene.update_tag()
        return {'FINISHED'}

class Procedural_Crowds_OT_property_selector(Operator):
    
    bl_idname = 'procedural_crowds.property_selector'
    bl_label = "Select"
    bl_description = "Select property"
    bl_options = {'REGISTER','UNDO'}

    input_types = [('OBJECT','object','object'),('COLLECTION','collection','collection'),('MATERIAL','material','material'),('IMAGE','image','image'),('TEXTURE','texture','texture')]
    input_type: bpy.props.EnumProperty(items=input_types)
    input_identifier: bpy.props.StringProperty()

    def execute(self, context):
        mod = get_gn_mod(context.active_object)
        props = context.scene.procedural_crowds_gn_workaround
        prop = getattr(props,self.input_type.lower())
        mod[self.input_identifier] = prop
        # setattr(context.scene.procedural_crowds_gn_workaround,self.input_type.lower(),None)
        context.area.tag_redraw()
        redraw_area('PROPERTIES', context)
        context.active_object.update_tag()
        return {'FINISHED'}

    def invoke(self, context, event):
        # mod = get_gn_mod(context.active_object)
        # props = context.scene.procedural_crowds_gn_workaround
        # setattr(props,self.input_type.lower(),mod[self.input_identifier])
        return context.window_manager.invoke_props_popup(self,event)

    def draw(self, context):
        layout = self.layout
        props = context.scene.procedural_crowds_gn_workaround
        layout.box().prop(props,self.input_type.lower())

class Procedural_Crowds_OT_assign_collision(Operator):
    
    bl_idname = 'procedural_crowds.assign_collision'
    bl_label = "Set Floor"
    bl_description = "Add collision property to selected objects(except active) and move them to collision collection"
    bl_options = {'REGISTER','UNDO'}
    
    collision_collection_name: bpy.props.StringProperty()
    def execute(self, context):
        collision_collection = bpy.data.collections.get(self.collision_collection_name)
        for obj in context.selected_objects:
            if obj is not context.active_object:
                mod = obj.modifiers.new('Collision',type='COLLISION')
                if not mod:
                    continue
                mod.settings.damping_factor = 1.0
                mod.settings.friction_factor = 1.0
                mod.settings.stickiness = 1.0

                if collision_collection and collision_collection not in obj.users_collection:
                    collision_collection.objects.link(obj)
        return {'FINISHED'}

class Procedural_Crowds_OT_assign_force_field(Operator):
    
    bl_idname = 'procedural_crowds.assign_force_field'
    bl_label = "Set Floor"
    bl_description = "Add force_field property to selected objects(except active)"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self, context):
        exclude_obj = context.active_object.name
        for obj in context.selected_objects:
            if obj.name != exclude_obj:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                if obj.field is None or obj.field.type == 'NONE':
                    bpy.ops.object.forcefield_toggle()
                    obj.field.shape = 'SURFACE'
                    obj.field.strength = 15.0
                    obj.field.use_max_distance = True
                    obj.field.distance_max = 1
        obj = bpy.data.objects.get(exclude_obj)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}

class Procedural_Crowds_OT_append_individual(Operator):
    bl_idname = 'procedural_crowds.append_individual'
    bl_label = "Crowd Add Human"
    bl_description = "Add High Quality Individual Human Model"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context) -> bool:
        enabled_modes = ['OBJECT']
        return context.mode in enabled_modes
    
    def execute(self, context: Context):
        props:Procedural_Crowds_Properties = context.scene.procedural_crowds
        model:str = props.individual_models
        model_category:str = props.individual_model_categories

        packs_dir = context.preferences.addons[__package__].preferences.filepath
        model_path = Path(packs_dir) / 'Individuals' / 'Models' / model_category / model
        model_blend_path = next(model_path.glob("*.blend"))

        model_name = model.replace(" ","_")
        obj_names = [f'IND_{model_name}', f'IND_{model_name}_Armature']
        # print(model_blend_path)

        if props.link_individual_models is False:
            with bpy.data.libraries.load(str(model_blend_path), link=False) as (data_from, data_to):
                data_to.objects = [obj for obj in data_from.objects if obj in obj_names]
            
            collection = get_collection(f'IND_{model_name}',context.scene.collection)
            armature_collection = get_collection(f'IND_Armatures',context.scene.collection)
            for obj in data_to.objects:
                if 'Armature' in obj.name: # is armature
                    armature_collection.objects.link(obj)
                else: # is model
                    collection.objects.link(obj)
        else:
            with bpy.data.libraries.load(str(model_blend_path), link=True) as (data_from, data_to):
                data_to.collections = [col for col in data_from.collections if col == f'IND_{model_name}']

            for coll in data_to.collections:
                empty = bpy.data.objects.new(coll.name, None)
                empty.instance_type = 'COLLECTION'
                empty.instance_collection = coll
                context.scene.collection.objects.link(empty)
        return {'FINISHED'}

class Procedural_Crowds_OT_add_animation(Operator):
    bl_idname = 'procedural_crowds.add_animation'
    bl_label = "Add Animation to selected"
    bl_description = "Append armature with animation and assign it to selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    use_existing: BoolProperty(default=False, options={'SKIP_SAVE',})
    @classmethod
    def poll(cls, context) -> bool:
        enabled_modes = ['OBJECT']
        return context.mode in enabled_modes
    
    def execute(self, context: Context):
        props:Procedural_Crowds_Properties = context.scene.procedural_crowds
        animation:str = props.individual_animations

        packs_dir = context.preferences.addons[__package__].preferences.filepath
        animation_path = Path(packs_dir) / 'Individuals' / 'Animations' / props.individual_animations
        animation_blend_path = next(animation_path.glob("*.blend"))

        animation_name = animation.replace(" ","_")
        armature_name = f'IND_{animation_name}_Armature'

        armature = bpy.data.objects.get(armature_name,None)
        if armature is None or not self.use_existing :
            with bpy.data.libraries.load(str(animation_blend_path), link=False) as (data_from, data_to):
                data_to.objects = [obj for obj in data_from.objects if obj == armature_name]
            
            armature_collection = get_collection(f'Animation_Armatures',context.scene.collection)
            for obj in data_to.objects:
                armature_collection.objects.link(obj)
                armature = obj
            exclude_collection(context, armature_collection.name, True)

        for obj in context.selected_objects:
            mod = next((mod for mod in obj.modifiers if mod.type == 'ARMATURE'), None)
            if mod is None:
                continue
            print(mod, mod.object)
            print(armature, armature)
            mod.object.animation_data.action = armature.animation_data.action
        return {'FINISHED'}
    
    def invoke(self, context: Context, event: Event):
        props:Procedural_Crowds_Properties = context.scene.procedural_crowds
        animation:str = props.individual_animations
        animation_name = animation.replace(" ","_")
        armature_name = f'IND_{animation_name}_Armature'

        armature = bpy.data.objects.get(armature_name,None)
        if armature:
            return context.window_manager.invoke_props_dialog(self)
        
        return self.execute(context)
    def draw(self, context):
        props:Procedural_Crowds_Properties = context.scene.procedural_crowds
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text='Armature already exist in blend file')
        row = box.row()
        row.prop(self, 'use_existing', text='Use Existing', toggle=True)
        row.prop(self, 'use_existing', text='Append Duplicate', toggle=True, invert_checkbox=True)

class Procedural_Crowds_OT_open_gif(Operator):
    '''Open Preview GIF/Movie in any image viewer application'''
    bl_idname = "procedural_crowds.open_gif"
    bl_label = "Open in ImageViewer"
    bl_description = "Open Preview GIF in any image viewer application"
    bl_options = {'REGISTER'}

    cam_move : StringProperty(name="cam_move",options={'HIDDEN','SKIP_SAVE'})
    #https://stackoverflow.com/a/35305473/10358314
    def openImage(self,context,path):
        import sys
        import subprocess

        imageViewerFromCommandLine = context.preferences.addons[__package__].preferences.ext_img_editor
        if(not imageViewerFromCommandLine):
            imageViewerFromCommandLine = {'linux':['xdg-open'],
                                    'win32':['explorer'],
                                    'darwin':['qlmanage', '-p']}[sys.platform]
        subprocess.run([*imageViewerFromCommandLine,path])

    @classmethod
    def poll(cls, context):
        return context.scene.procedural_crowds.individual_animations
        # return True

    def execute(self, context):
        props:Procedural_Crowds_Properties = context.scene.procedural_crowds
        crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
        if not crowd_sys_dir:
            return {'CANCELLED'}

        path = Path(crowd_sys_dir) / 'Individuals' / 'Animations' / props.individual_animations
        preview_path = next(path.glob("preview.*"), None)
        if preview_path is None:
            self.report({'ERROR'},"Preview Not Found!!!")
            return {'CANCELLED'}
        self.openImage(context,preview_path)
        return {'FINISHED'}

class Procedural_Crowds_OT_apply_action_to_selected(Operator):
    bl_idname = 'procedural_crowds.apply_action_to_selected'
    bl_label = "Apply action to selected"
    bl_description = "Apply action of active armature to selected armatures"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context) -> bool:
        enabled_modes = ['OBJECT']
        return context.mode in enabled_modes and context.active_object and context.active_object.type == 'ARMATURE'
    
    def execute(self, context: Context):
        active_armature = context.active_object
        for obj in context.selected_objects:
            if obj.type != 'ARMATURE':
                continue
            if obj is active_armature:
                continue
            obj.animation_data.action = active_armature.animation_data.action
        return {'FINISHED'}
    
classes = [Procedural_Crowds_OT_append, Procedural_Crowds_OT_property_selector, Procedural_Crowds_OT_assign_collision, Procedural_Crowds_OT_assign_force_field,\
           Procedural_Crowds_OT_append_individual, Procedural_Crowds_OT_add_animation, Procedural_Crowds_OT_open_gif, Procedural_Crowds_OT_apply_action_to_selected]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
