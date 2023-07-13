import bpy

# Add Operators to Blender Add > Light Menu
def physical_lights_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("lightmixer.add", text='Physical Point', icon="LIGHT_POINT").type='POINT'
    layout.operator("lightmixer.add", text='Physical Sun', icon="LIGHT_SUN").type='SUN'
    layout.operator("lightmixer.add", text='Physical Spot', icon="LIGHT_SPOT").type='SPOT'
    layout.operator("lightmixer.add", text='Physical Area', icon="LIGHT_AREA").type='AREA'    

def register():
    bpy.types.VIEW3D_MT_light_add.append(physical_lights_draw)
    
def unregister():
    bpy.types.VIEW3D_MT_light_add.remove(physical_lights_draw)