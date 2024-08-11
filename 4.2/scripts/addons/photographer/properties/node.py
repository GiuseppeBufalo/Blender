import bpy

from ..constants import addon_name, color_temp_desc
from .light import(
                    get_light_temperature_color,
                    set_light_temperature_color,
                    temp_to_rgb_linear,
                    )
from bpy.props import (BoolProperty,
                       FloatProperty,
                       IntProperty,
                       FloatVectorProperty,
                       )

def wire_up(node_tree):
    nodes = (n for n in node_tree.nodes if n.get('em_color',False))
    for n in nodes:
        n.lightmixer.name = n.name

def get_em_strength(mat,node):
    nodes = mat.node_tree.nodes
    em_node = nodes[node]
    em_strength = em_node.get('em_strength','')
    if em_strength:
        return em_node,em_strength[0],em_strength[1]
    else:
        return None,None,None

# Light Mixer Properties functions
def get_enabled(self):
    return self.get('enabled', True)

def set_enabled(self,value):
    self['enabled'] = value
    wire_up(self.id_data)
    nodes = self.id_data.nodes
    node = nodes.get(self.name)
    em_strength = node.get('em_strength','')
    if em_strength:
        em_node = em_strength[0]
        em_input = em_strength[1]
        if self.enabled:
            nodes[em_node].inputs[em_input].default_value = self.strength
        else:
            self.strength = nodes[em_node].inputs[em_input].default_value
            nodes[em_node].inputs[em_input].default_value = 0
    return None

def update_solo(self,context):
    if self.solo:
        context.scene.lightmixer.solo_active = True
    else:
        context.scene.lightmixer.solo_active = False

    # Solo behavior for Lights
    light_objs = [o for o in bpy.data.objects if o.type == 'LIGHT']
    for light_obj in light_objs:
        if self.solo:
            light_obj.hide_viewport = True
            light_obj.hide_render = True
        else:
            light_obj.hide_viewport = not light_obj.lightmixer.enabled
            light_obj.hide_render = not light_obj.lightmixer.enabled

    # Solo behavior for Materials
    emissive_mats = [mat for mat in bpy.data.materials if mat.get('is_emissive', False)]
    wire_up(self.id_data)
    self_node =  self.id_data.nodes.get(self.name)

    for mat in emissive_mats:
        nodes = mat.node_tree.nodes
        for node in mat.get('em_nodes', ''):
            em_node,ctrl_node,ctrl_input = get_em_strength(mat,node)
            if em_node and ctrl_node and ctrl_input:
                if self.solo:
                    if em_node == self_node:
                        if self.enabled and nodes[ctrl_node].inputs[ctrl_input].default_value != 0:
                            self.strength = nodes[ctrl_node].inputs[ctrl_input].default_value
                        nodes[ctrl_node].inputs[ctrl_input].default_value = self.strength
                    elif em_node.lightmixer.enabled:
                        em_node.lightmixer.strength = nodes[ctrl_node].inputs[ctrl_input].default_value
                        nodes[ctrl_node].inputs[ctrl_input].default_value = 0
                else:
                    if em_node.lightmixer.enabled:
                        nodes[ctrl_node].inputs[ctrl_input].default_value = em_node.lightmixer.strength
                    else:
                        nodes[ctrl_node].inputs[ctrl_input].default_value = 0

# def get_color(self):
#     # wire_up(self.id_data)
#     # node = self.id_data.nodes.get(self.name)
#     # if node:
#     #     em_color = node.get('em_color','')
#     #     if em_color:
#     #         return node.inputs[em_color[1]].default_value
#     # else:
#     return self.get('color',(1.0,1.0,1.0,1.0))

# def set_color(self, value):
#     self['color'] = value
#     if not self.use_light_temperature:
#         wire_up(self.id_data)
#         nodes = self.id_data.nodes
#         node = nodes.get(self.name)
#         em_color = node.get('em_color','')
#         if em_color:
#             nodes[em_color[0]].inputs[em_color[1]].default_value = value
#     return None

def get_light_temperature(self):
    return self.get('light_temperature', 6500)

def set_light_temperature(self, value):
    self['light_temperature'] = value
    color = temp_to_rgb_linear(value)
    color.append(1.0)
    if self.use_light_temperature:
        wire_up(self.id_data)
        nodes = self.id_data.nodes
        node = nodes.get(self.name)
        em_color = node.get('em_color','')
        if em_color:
            nodes[em_color[0]].inputs[em_color[1]].default_value = color
            self.color = color
    return None

def get_use_light_temperature(self):
    return self.get('use_light_temperature', False)

def set_use_light_temperature(self, value):
    self['use_light_temperature'] = value
    set_light_temperature(self,self.light_temperature)
    return None

class LightMixerNodeSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enable Emissive",
        default=True,
        get=get_enabled,
        set=set_enabled,
    )
    solo: BoolProperty(
        name="Solo",
        default=False,
        update=update_solo,
    )
    strength: FloatProperty(
        name='Strength',
        precision=3,
    )
    # color: FloatVectorProperty(
    #     name="Color", description="Emissive Color",
    #     subtype='COLOR',
    #     min=0.0, max=1.0, size=4,
    #     default=(1.0,1.0,1.0,1.0),
    #     get=get_color,
    #     set=set_color,
    # )
    light_temperature : IntProperty(
        name="Color Temperature", description=color_temp_desc,
        min=1000, max=13000, default=6500,
        get=get_light_temperature,
        set=set_light_temperature,
    )

    use_light_temperature: BoolProperty(
        name="Use Emissive Color Temperature",
        default=False,
        options = {'HIDDEN'},
        get=get_use_light_temperature,
        set=set_use_light_temperature,
    )

    preview_color_temp : FloatVectorProperty(
        name="Preview Color", description="Color Temperature preview color",
        subtype='COLOR', min=0.0, max=1.0, size=3,
        options = {'HIDDEN'},
        get=get_light_temperature_color,
        set=set_light_temperature_color,
    )
