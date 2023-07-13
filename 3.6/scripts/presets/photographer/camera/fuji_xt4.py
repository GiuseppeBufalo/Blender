import bpy
camera = bpy.context.scene.camera.data
photographer = bpy.context.scene.camera.data.photographer

photographer.sensor_type = 'APS-C'
camera.sensor_width = 23.6
camera.sensor_height = 15.6
camera.show_passepartout = True
camera.passepartout_alpha = 1.0
