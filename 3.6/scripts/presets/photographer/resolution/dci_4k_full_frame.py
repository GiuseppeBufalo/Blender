import bpy
render = bpy.context.scene.render
photographer = bpy.context.scene.camera.data.photographer

photographer.resolution_mode = 'CUSTOM_RATIO'
photographer.resolution_x = 4096
photographer.resolution_y = 1080
photographer.ratio_x = 1.899999976158142
photographer.ratio_y = 1.0019999742507935
photographer.resolution_rotation = 'LANDSCAPE'
photographer.longedge = 4096
photographer.fit_inside_sensor = True
render.resolution_percentage = 100
