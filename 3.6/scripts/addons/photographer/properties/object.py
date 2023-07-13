import bpy
from .node import get_em_strength

# Light Mixer Properties functions
def get_enabled(self):
    return self.get('enabled', True)

def set_enabled(self,value):
    self['enabled'] = value
    self.id_data.hide_viewport = not value
    self.id_data.hide_render = not value
    return None
    
def update_solo(self,context):
    # Solo behavior for Materials
    emissive_mats = [mat for mat in bpy.data.materials if mat.get('is_emissive', False)]       
    for mat in emissive_mats:
        nodes = mat.node_tree.nodes
        for node in mat.get('em_nodes', ''):
            em_node,ctrl_node, ctrl_input = get_em_strength(mat,node)
            if em_node and ctrl_node and ctrl_input:
                if self.solo:
                    em_node.lightmixer.strength = nodes[ctrl_node].inputs[ctrl_input].default_value
                    nodes[ctrl_node].inputs[ctrl_input].default_value = 0
                else:
                    nodes[ctrl_node].inputs[ctrl_input].default_value = em_node.lightmixer.strength
                
    light_objs = [o for o in bpy.data.objects if o.type == 'LIGHT']
    for light_obj in light_objs:
        if self.solo:
            context.scene.lightmixer.solo_active = True
            if light_obj == self.id_data:
                light_obj.hide_viewport = False
                light_obj.hide_render = False
            else:
                light_obj.hide_viewport = True
                light_obj.hide_render = True
        else:
            context.scene.lightmixer.solo_active = False
            light_obj.hide_viewport = not light_obj.lightmixer.enabled
            light_obj.hide_render = not light_obj.lightmixer.enabled
            
                
class LightMixerObjectSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enable Light",
        default=True,
        get=get_enabled,
        set=set_enabled,
    )    
    solo: bpy.props.BoolProperty(
        name="Solo",
        default=False,
        options = {'HIDDEN'},
        update = update_solo
    )    
    show_more: bpy.props.BoolProperty(
        name="Show More",
        default=False,
        options = {'HIDDEN'},
    )     