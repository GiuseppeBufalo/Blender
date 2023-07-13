import bpy

# Function to add Focus Plane to Camera Properties UI
def focus_plane_ui(self, context):
    layout = self.layout
    settings = context.camera.photographer

    split = layout.split(factor=0.37, align=False)
    split.separator()
    col = split.column(align=True)
    col.use_property_decorate = False
    
    cam_obj = [o for o in bpy.data.objects if o.data is context.camera][0]
    if settings.show_focus_plane:
        col.operator("photographer.delete_focus_plane", text="Hide Focus Plane", icon='CANCEL').camera=cam_obj.name
    else:
        col.operator("photographer.create_focus_plane", text="Show Focus Plane", icon='NORMALS_FACE').camera=cam_obj.name
    col.prop(settings, "focus_plane_color", text="")