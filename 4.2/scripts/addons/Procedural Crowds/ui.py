from dataclasses import dataclass
import bpy
from bpy.types import Panel, UILayout, NodesModifier, NodeSocketInterfaceStandard

@dataclass
class Pointer_Prop:
    type_:str
    search_id:str
    icon:str

def draw_gn_mod_props(layout:UILayout,mod:NodesModifier,input:NodeSocketInterfaceStandard):
    data, prop, use_attr, prop_attr = mod, f'["{input.identifier}"]', f'["{input.identifier}_use_attribute"]', f'["{input.identifier}_attribute_name"]'
    pointer_data:dict = {
        'OBJECT' : Pointer_Prop('OBJECT','objects','OBJECT_DATA'),
        'COLLECTION' : Pointer_Prop('COLLECTION','collections','OUTLINER_COLLECTION'),
        'MATERIAL' : Pointer_Prop('MATERIAL','materials','MATERIAL'),
        'TEXTURE' : Pointer_Prop('TEXTURE','textures','TEXTURE'),
        'IMAGE' : Pointer_Prop('IMAGE','images','IMAGE')
    }
    row = layout.split(align=True, factor=0.4)
    row.alignment='RIGHT'
    
    row.label(text=input.name)
    
    subrow = row.row(align=True)
    subrow.use_property_split=True
    subrow.use_property_decorate=True

    if 'DIAMOND' in mod.node_group.nodes['Group Input'].outputs[input.name].display_shape: # Possible shape : Diamond, Diamond_dot
        op_props = subrow.operator('object.geometry_nodes_input_attribute_toggle',text='', icon='SPREADSHEET')
        op_props.prop_path = use_attr
        op_props.modifier_name = mod.name

    if input.type in pointer_data.keys():
        subrow.prop_search(mod,prop,bpy.data,pointer_data[input.type].search_id,text='',icon=pointer_data[input.type].icon)
    else:
        final_prop = prop_attr if getattr(mod,use_attr,0)!=0 else prop
        subrow.prop(data,final_prop, text='',)
        
class Procedural_Crowds_PT_Browser(Panel):

    bl_idname = "PROCEDURAL_CROWDS_PT_Browser"
    bl_label = "Procedural Crowds"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Procedural Crowds'

    def draw(self, context):
        layout = self.layout
        props = context.scene.procedural_crowds
        scale_y = 1.4
        icon_scale = 5
        scale_popup = 6

        crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
        if not crowd_sys_dir:
            box=layout.box()
            box.label(text="Select Asset Folder in Preferences", icon='ERROR')
            return
        
        box = layout.box()
        row = box.row()
        row.template_icon_view(props,"crowd_system", show_labels=True)
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=props.crowd_system.capitalize())

        row = box.row()
        row.prop(props,"crowd_models", text="Models")

        row = box.row()
        row.operator('procedural_crowds.append')

def get_gn_mod(obj: bpy.types.Object):
    mod = None
    for m in obj.modifiers:
        if m.type == "NODES":
            mod = m
            break
    return mod

class Procedural_Crowds_PT_GeoNode(Panel):

    bl_idname = "MOD_PT_GeometryNodes"
    bl_label = "Crowd Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Procedural Crowds'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_boid_settings(self, context, layout:UILayout):
        ps = context.active_object.particle_systems[0]
        ps_settings = ps.settings
        layout.use_property_split = True
        layout.use_property_decorate = True
        box = layout.box()
        box.prop(ps_settings,'count',text='People Count')
        box = layout.box()
        box.prop(ps,'seed',text='People Seed')
        box = layout.box()
        box.prop(ps_settings.boids,'land_speed_max',text='Speed')
        box = layout.box()
        box.prop(ps_settings.boids,'land_personal_space',text='Personal Space')
        # box = layout.box()
        # box.prop(ps_settings,'collision_collection')
        box = layout.box()
        op = box.operator('procedural_crowds.assign_collision', text = 'Set Floor')
        op.collision_collection_name = ps_settings.collision_collection.name if ps_settings.collision_collection else ''
        box = layout.box()
        op = box.operator('procedural_crowds.assign_force_field', text = 'Set Collision')
        box = layout.box()
        box.prop(ps_settings.boids.active_boid_state.rules["Goal"],'object',text='Goal')

    def draw(self, context):
        layout = self.layout
        if not context.active_object:
            box = layout.box()
            box.label(text="No Active Object", icon='INFO')
            return
        
        if len(context.active_object.particle_systems)>0:
            col = layout.column(align=True)
            self.draw_boid_settings(context, col)
            return
        
        mod = get_gn_mod(context.active_object)
        
        if not mod:
            box = layout.box()
            box.label(text="No Crowd System Found.", icon='INFO')
            return

        col = layout.column(align=True)
        for input in mod.node_group.inputs:
            if input.identifier == "Input_0":
                continue
            box = col.box()
            box.use_property_split = True
            box.use_property_decorate = True
            draw_gn_mod_props(box,mod,input)
            

            

class Procedural_Crowds_PT_Individual(Panel):

    bl_idname = "PROCEDURAL_CROWDS_PT_Individual_Models"
    bl_label = "Individual Humans"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Procedural Crowds'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.procedural_crowds
        scale_y = 1.4
        icon_scale = 5
        scale_popup = 6

        crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
        if not crowd_sys_dir:
            box=layout.box()
            box.label(text="Select Asset Folder in Preferences", icon='ERROR')
            return
        
        wrapper = layout.column(align=True)
        box = wrapper.box()
        row = box.split(factor=1)
        row.prop(props,"individual_model_categories",)
        # row.prop(props,"link_individual_models", toggle=True, text='Link Assets')
        row = box.row()
        row.template_icon_view(props,"individual_models", show_labels=True)
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=props.individual_models.capitalize())

        row = box.row()
        row.operator('procedural_crowds.append_individual', icon='ADD', text='Add Human')

        box = wrapper.box()

        row = box.row()
        row.label(text='Animations:')
        row = box.row()
        row.prop(props,"individual_animations", text="")
        row = box.row()
        row.operator("procedural_crowds.open_gif", icon='PLAY', text="Preview Animation")
        row = box.row()
        row.operator("procedural_crowds.add_animation", icon='ADD', text='Add Animation to selected')
        row.operator("procedural_crowds.apply_action_to_selected")

        if context.active_object and context.active_object.animation_data is not None:
            row = box.row()
            row.prop(context.active_object.animation_data,"action")
classes = [Procedural_Crowds_PT_Browser, Procedural_Crowds_PT_GeoNode, Procedural_Crowds_PT_Individual]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)