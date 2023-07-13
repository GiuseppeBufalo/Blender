import bpy

# Add Operators to Blender Add > Light Menu
def physical_camera_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("photographer.add_cam", text='Photographer Camera', icon="OUTLINER_OB_CAMERA")

def register():
    bpy.types.VIEW3D_MT_add.append(physical_camera_draw)
    
def unregister():
    bpy.types.VIEW3D_MT_add.remove(physical_camera_draw)