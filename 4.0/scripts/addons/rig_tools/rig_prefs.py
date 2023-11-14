import bpy

def update_all_tab_names(self, context):
    try:
        from . import rig_functions      
        rig_functions.update_arp_tab()
    except:
        pass

class RT_MT_arp_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__   
    arp_tools_tab_name : bpy.props.StringProperty(name="Tools Interface Tab", description="Name of the tab to display the tools (Ik-FK snap...) interface in", default="Tool", update=update_all_tab_names)
    rig_layers_path: bpy.props.StringProperty(name="Rig Layers Path", subtype='FILE_PATH', default="/Rig Layers/", description='Path to store rig layers presets')
    
    def draw(self, context):        
        col = self.layout.column(align=True)       
        col.prop(self, "arp_tools_tab_name", text="Tools Interface Tab")   
        col.prop(self, "rig_layers_path")
        
def register():
    from bpy.utils import register_class

    #for cls in classes:
    register_class(RT_MT_arp_addon_preferences)
    prefs = bpy.context.preferences.addons[__package__].preferences
  
def unregister():
    from bpy.utils import unregister_class
    
    #for cls in reversed(classes):
    unregister_class(RT_MT_arp_addon_preferences)  
