import bpy
camera = bpy.context.scene.camera.data
photographer = bpy.context.scene.camera.data.photographer

photographer.sensor_type = 'Alexa 65'
camera.sensor_width = 54.12
camera.sensor_height = 25.58
camera.show_passepartout = True
camera.passepartout_alpha = 1.0
