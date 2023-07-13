import bpy, math, bgl, gpu
from bpy.app.handlers import persistent
from . import camera, functions
# from .constants import base_ev

# Global
handle = ()
old_engine = ""

def view3d_find():
    # returns first 3d view, normally we get from context
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return region, rv3d
    return None, None

def view3d_camera_border(scene):
    obj = scene.camera
    cam = obj.data

    frame = cam.view_frame(scene=scene)

    # move from object-space into world-space
    frame = [obj.matrix_world @ v for v in frame]

    # move into pixelspace
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    region, rv3d = view3d_find()
    frame_px = [location_3d_to_region_2d(region, rv3d, v) for v in frame]
    return frame_px

# def read_color(x,y,buffer):
#     if bpy.app.version >= (3,2,2):
#         pixel = buffer.read_color(x, y, 1, 1, 3, 0, 'FLOAT')
#         pixel.dimensions = 1 * 1 * 3
#         value = [float(item) for item in pixel]
#     else:
#         bgl.glReadPixels(x, y, 1, 1, bgl.GL_RGB, bgl.GL_FLOAT, buffer)
#         value = buffer
#     return value


# Auto Exposure algorithms
def ae_calc():
    context = bpy.context
    engine = context.scene.render.engine
    shading = context.area.spaces.active.shading.type
    if shading == "RENDERED":
        if context.scene.camera and hasattr(context.scene.camera.data,"photographer"):
            settings = context.scene.camera.data.photographer
            if settings.exposure_mode == 'AUTO':
                if not (engine == 'LUXCORE' and context.scene.luxcore.config.device == 'CPU'):
                    offset_x = 0
                    offset_y = 0

                    if bpy.app.version >= (3,2,2):
                        # get information on current viewport 
                        viewport_info = gpu.state.viewport_get()
                        width = viewport_info[2]
                        height = viewport_info[3]

                        buffer = gpu.state.active_framebuffer_get()

                    else:
                        # width and height of the full viewport
                        viewport = bgl.Buffer(bgl.GL_INT, 4)
                        bgl.glGetIntegerv(bgl.GL_VIEWPORT, viewport)
                        width = viewport[2]
                        height = viewport[3]

                        bgl.glDisable(bgl.GL_DEPTH_TEST)
                        buffer = bgl.Buffer(bgl.GL_FLOAT, 3)

                    # If looking through scene camera, use camera border
                    for area in context.screen.areas:
                        if area.type == 'VIEW_3D':
                            if area.spaces[0].region_3d.view_perspective == 'CAMERA' :
                                if context.scene.camera:
                                    if context.scene.camera.type == 'CAMERA':
                                        frame_px = view3d_camera_border(bpy.context.scene)
                                        border_width = int(frame_px[0][0] - frame_px[2][0])
                                        border_height = int(frame_px[0][1] - frame_px[2][1])
                                        offset_x = int(frame_px[2][0])
                                        offset_y = int(frame_px[2][1])

                                        # Use viewport size as maximum
                                        if border_width < width:
                                            width = border_width
                                        if border_height < height:
                                            height = border_height
                    
                    # Split viewport in a 16*16 grid
                    grid = 10
                    center_min = int(grid/2 - 1)
                    center_max = int(grid/2 + 1)
                    values = center = count = center_count = 0

                    # print (width, height, offset_x, offset_y)

                    # Next pixel position
                    step = 1/(grid+1)

                    # Sample each pixel of the grid
                    for i in range (grid):
                        for j in range (grid):
                            x = int(step*(j+1)*width+offset_x)
                            y = int(step*(i+1)*height+offset_y)
                            value = functions.read_pixel_color(x,y,buffer)
                            lum = functions.rgb_to_luminance(value)
                            if lum != 0:
                                values += lum
                                count += 1
                            # Store the 4 center pixels separately for weighing
                            if i in range (center_min,center_max) and j in range (center_min,center_max):
                                if lum != 0:
                                    center += lum
                                    center_count += 1

                            # Higher coefficient for the center point
                            if i == grid/2 and j == grid/2:
                                if lum != 0:
                                    center += lum
                                    center_count += 1

                    # Average luminance
                    if count != 0 and center_count != 0:
                        full_avg = values/count
                        center_avg = center/center_count
                        # Center Weighing lerping between the two averages
                        avg = functions.lerp(full_avg,center_avg,settings.center_weight/100)

                        # Exposure target
                        mid_grey = 0.18
                        diff_lum = avg / mid_grey
                        if diff_lum > 0:
                            target = -math.log2(diff_lum)
                            current = settings.ae

                            # Optimization to not run indefinitely
                            threshold = abs(target - current)
                            if threshold > 0.02:
                                settings.ae = functions.interpolate_float(current, target, settings.ae_speed)[0]
                                # print ('Full ' + str(full_avg) + ', Center ' + str(center_avg) + ', AVG '+ str(avg))


## BAKE DOESN'T WORK BECAUSE OF PLAYBACK ISSUES WITH DRAW_HANDLER
# def ae_bake():
#     context = bpy.context
#     settings = context.scene.camera.data.photographer
#     current_frame = context.scene.frame_current
#
#     timer = 0.25
#     settings.ae_speed = 1
#     # Passing AE value to EV
#     settings.ev = base_ev - settings.ae
#     # Setting key on EV
#     settings.keyframe_insert(data_path='ev', frame=(current_frame))
#
#     return timer

# SET EV KEY BUTTON
class PHOTOGRAPHER_OT_AE_Set_Key(bpy.types.Operator):
    """Auto Exposure: Set EV key"""
    bl_idname = "photographer.ae_set_key"
    bl_label = "Set Exposure Key"

    def execute(self, context):
        settings = context.scene.camera.data.photographer
        current_frame = context.scene.frame_current
        settings.keyframe_insert(data_path='ev', frame=(current_frame))

        return{'FINISHED'}


@persistent
def auto_exposure_handler(*args):
    bpy.types.SpaceView3D.draw_handler_add(ae_calc, (), 'WINDOW', 'PRE_VIEW')
    # bpy.types.SpaceView3D.draw_handler_add(ae_calc, (), 'WINDOW', 'POST_PIXEL')

# Register
def register():
    from bpy.utils import register_class
    register_class(PHOTOGRAPHER_OT_AE_Set_Key)
    bpy.app.handlers.load_post.append(auto_exposure_handler)

# Unregister
def unregister():
    from bpy.utils import unregister_class
    unregister_class(PHOTOGRAPHER_OT_AE_Set_Key)
    bpy.app.handlers.load_post.remove(auto_exposure_handler)
