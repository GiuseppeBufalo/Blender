import bpy
camera = bpy.context.scene.camera.data
photographer = bpy.context.scene.camera.data.photographer

photographer.sensor_type = 'Micro 4/3'
camera.sensor_width = 17.3
camera.sensor_height = 13
camera.show_passepartout = True
camera.passepartout_alpha = 1.0
