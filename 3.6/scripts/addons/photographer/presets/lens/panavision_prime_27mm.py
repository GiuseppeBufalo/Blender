import bpy
camera = bpy.context.scene.camera.data
photographer = bpy.context.scene.camera.data.photographer

photographer.focal = 27.0
photographer.fisheye = False
photographer.lens_shift = 0
photographer.use_dof = True
photographer.aperture = 1.9
photographer.aperture_preset = '2.8'
photographer.aperture_slider_enable = True
camera.dof.focus_distance = 10.0
camera.dof.aperture_ratio = 1.0
camera.dof.aperture_blades = 13
camera.dof.aperture_rotation = 0.0
