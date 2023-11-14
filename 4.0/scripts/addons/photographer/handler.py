import bpy
from bpy.app.handlers import persistent
from .camera import update_settings
from .properties.post_effects import update_post_effects
from . import camera

LAST_CAMERA = None
LAST_SENSOR_WIDTH = 1
LAST_SENSOR_HEIGHT = 1

@persistent
def update_render_camera(scene,depsgraph):
    if scene.camera:
        camera_ob = scene.camera
        camera_ob_eval = camera_ob.evaluated_get(depsgraph)
        # Dictionary of Photographer Camera properties
        for key in camera.PhotographerCameraSettings.__annotations__.keys() and camera_ob.data.photographer.keys():
            if key not in {'light_threshold_warning', 'preview_color_tint', 'preview_color_temp', 'ev'}:
                key_eval = camera_ob_eval.data.photographer[key]
                camera_ob.data.photographer[key] = key_eval

        # EV needs to be evaluated after manual settings
        camera_ob.data.photographer.ev = camera_ob_eval.data.photographer.ev

@persistent
def update_scene_camera(scene, depsgraph):
    global LAST_CAMERA
    global LAST_SENSOR_WIDTH
    global LAST_SENSOR_HEIGHT
    if scene.camera:
        if scene.camera != LAST_CAMERA:
            LAST_CAMERA = scene.camera
            # print("Photographer: Scene Camera changed, updating all settings.")
            update_settings(scene.camera.data.photographer,bpy.context)
            update_post_effects(scene.camera.data.post_effects,bpy.context)
        if scene.camera.data.sensor_width != LAST_SENSOR_WIDTH or scene.camera.data.sensor_height != LAST_SENSOR_HEIGHT:
            update_settings(scene.camera.data.photographer,bpy.context)

def register():
    bpy.app.handlers.frame_change_post.append(update_render_camera)
    bpy.app.handlers.depsgraph_update_pre.append(update_scene_camera)

def unregister():
    bpy.app.handlers.frame_change_post.remove(update_render_camera)
    bpy.app.handlers.depsgraph_update_pre.remove(update_scene_camera)
