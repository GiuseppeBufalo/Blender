import bpy

def PHOTOGRAPHER_MT_SceneSettings(self, context):
    settings = context.scene.photographer
    layout = self.layout

    row = layout.row(align=True)
    row.prop(settings, "main_camera")
    if settings.main_camera:
        row.operator("photographer.button_enum_clear", text='',icon='PANEL_CLOSE',emboss=False).prop='main_camera'

def register():
    bpy.types.SCENE_PT_scene.append(PHOTOGRAPHER_MT_SceneSettings)

def unregister():
    bpy.types.SCENE_PT_scene.remove(PHOTOGRAPHER_MT_SceneSettings)