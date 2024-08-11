import bpy

from ..constants import addon_name
from bpy.props import BoolProperty

# Light Mixer Properties functions
def get_enabled(self):
    return self.get('enabled', True)

def set_enabled(self,value):
    self['enabled'] = value
    mat = self.id_data
    nodes = mat.node_tree.nodes
    em_nodes = mat.get('em_nodes','')    
    for em_node in em_nodes:
        em_node = nodes[em_node]
        em_node.lightmixer.enabled = self.enabled
    return None
    
def update_backface_culling(self,context):    
    self.id_data.use_backface_culling = self.backface_culling
    bpy.ops.lightmixer.add_backface_culling_nodes(mat_name=self.id_data.name)
        
    
class LightMixerMaterialSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enable Emissive",
        default=True,
        get=get_enabled,
        set=set_enabled,
    )    
    show_more: BoolProperty(
        name="Expand Material Emissive settings",
        default=False,
    )
    backface_culling: BoolProperty(
        name="Backface Culling",
        default=False,
        update=update_backface_culling,
    )   