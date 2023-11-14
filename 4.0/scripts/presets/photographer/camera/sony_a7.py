import bpy
camera = bpy.context.scene.camera.data
photographer = bpy.context.scene.camera.data.photographer

photographer.sensor_type = 'Fullframe'
camera.sensor_width = 36
camera.sensor_height = 24
camera.show_passepartout = True
camera.passepartout_alpha = 1.0
