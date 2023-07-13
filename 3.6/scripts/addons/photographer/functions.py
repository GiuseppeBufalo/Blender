import bpy, math, bgl

from bpy_extras import view3d_utils
from mathutils import Matrix,Vector
from mathutils.geometry import distance_point_to_plane
from .constants import base_ev

class InterpolatedArray(object):
  # An array-like object that provides interpolated values between set points.

    def __init__(self, points):
        self.points = sorted(points)

    def __getitem__(self, x):
        if x < self.points[0][0] or x > self.points[-1][0]:
            raise ValueError
        lower_point, upper_point = self._GetBoundingPoints(x)
        return self._Interpolate(x, lower_point, upper_point)

    def _GetBoundingPoints(self, x):
    #Get the lower/upper points that bound x.
        lower_point = None
        upper_point = self.points[0]
        for point  in self.points[1:]:
            lower_point = upper_point
            upper_point = point
            if x <= upper_point[0]:
                break
        return lower_point, upper_point

    def _Interpolate(self, x, lower_point, upper_point):
    #Interpolate a Y value for x given lower & upper bounding points.
        slope = (float(upper_point[1] - lower_point[1]) / (upper_point[0] - lower_point[0]))
        return lower_point[1] + (slope * (x - lower_point[0]))

ev_lookup =  ["Starlight","Aurora Borealis","Half Moon","Full Moon","Full Moon in Snowscape",
            "Dim artifical light","Dim artifical light","Distant view of lit buildings",
            "Distant view of lit buildings","Fireworks","Candle","Campfire","Home interior",
            "Night Street","Office Lighting","Neon Signs","Skyline after Sunset","Sunset",
            "Heavy Overcast","Bright Cloudy","Hazy Sun","Sunny","Bright Sun"]

# sRGB to linear function
def srgb_to_linear(x):
    a = 0.055
    if x <= 0.04045 :
        y = x / 12.92
    else:
        y = pow( (x + a) * (1.0 / (1 + a)), 2.4)
    return y

def linear_to_srgb(x):
    if (x > 0.0031308):
        y = 1.055 * (pow(x, (1.0 / 2.4))) - 0.055
    else:
        y = 12.92 * x
    return y

def rgb_to_luminance(color):
    luminance = 0.2126729*color[0] + 0.7151522*color[1] + 0.072175*color[2]
    return luminance

def lerp(a, b, percent):
    return (a + percent*(b - a))

def interpolate_float(float1, float2, speed):
    float = float1 + (float2 - float1) * speed
    return float, abs(float-float2)

def interpolate_int(int1, int2, speed):
    if (int2 - int1) != 0:
        delta = (int2 - int1) * speed
        if 0 < delta < 1:
            delta = 1
        elif -1 < delta < 0:
            delta = -1
    else:
        delta = 0
    val = int(int1 + delta)
    return val, abs(val-int2)

def update_exposure_guide(self,context,ev):
    if ev <= 16 and ev >= -6:
        ev = int(ev+6)
        ev_guide = ev_lookup[ev]
    else:
        ev_guide = "Out of realistic range"
    return ev_guide

def calc_exposure_value(self,context):
    if self.exposure_mode == 'EV':
        EV = self.ev - self.exposure_compensation

    elif self.exposure_mode == 'AUTO':
        EV = base_ev - self.ae - self.exposure_compensation

    else:
        if not self.aperture_slider_enable:
            aperture = float(self.aperture_preset)
        else:
            aperture = self.aperture
        A = aperture

        if self.shutter_mode == 'SPEED':
            if not self.shutter_speed_slider_enable:
                shutter_speed = float(self.shutter_speed_preset)
            else:
                shutter_speed = self.shutter_speed

        if self.shutter_mode == 'ANGLE':
            shutter_speed = shutter_angle_to_speed(self,context)

        S = 1 / shutter_speed

        if not self.iso_slider_enable:
            iso = float(self.iso_preset)
        else:
            iso = self.iso
        I = iso

        EV = math.log((100*(A*A)/(I*S)), 2)
        EV = round(EV, 2) - self.exposure_compensation
    return EV

def shutter_angle_to_speed(self,context,):
    if not self.shutter_speed_slider_enable:
        shutter_angle = float(self.shutter_angle_preset)
    else:
        shutter_angle = self.shutter_angle
    fps = context.scene.render.fps / context.scene.render.fps_base
    shutter_speed = 1 / (shutter_angle / 360) * fps
    return shutter_speed

def shutter_speed_to_angle(self,context):
    fps = context.scene.render.fps / context.scene.render.fps_base
    if not self.shutter_speed_slider_enable:
        shutter_angle = (fps * 360) / float(self.shutter_speed_preset)
    else:
        shutter_angle = (fps * 360) / self.shutter_speed
    return shutter_angle

def lc_exposure_check(self,context):
    if context.scene.camera:
        settings = context.scene.camera.data.photographer
        if bpy.context.scene.render.engine == 'LUXCORE' and settings.exposure_enabled:
            tonemapper = context.scene.camera.data.luxcore.imagepipeline.tonemapper
            if not tonemapper.enabled:
                return True
            else:
                if (tonemapper.type != 'TONEMAP_LINEAR' or tonemapper.use_autolinear or round(tonemapper.linear_scale,6) != 0.001464 ):
                    return True
                else:
                    return False
        else:
            return False

# Focus picker
def raycast(context, event, focus, continuous, cam_obj, coord=None):
    scene = bpy.context.scene

    if continuous:
        # Shoot ray from Scene camera
        # Offset origin to avoid hitting Bokeh objects
        org = cam_obj.matrix_world @ Vector((0.0, 0.0, 0.0))
        dir = cam_obj.matrix_world @ Vector((0.0, 0.0, -100)) - org

    else:
        # Shoot ray from mouse pointer
        region = context.region
        rv3d = context.region_data
        if not coord:
            coord = event.mouse_region_x, event.mouse_region_y

        org = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        dir = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)

    # Offset origin to avoid hitting DoF objects
    offset = 0.02
    for c in cam_obj.children:
        if c.get("is_opt_vignetting", False):
            offset -= c.location.z * context.scene.unit_settings.scale_length
            break
    offset /= context.scene.unit_settings.scale_length
    dir.normalize()
    org += (offset * dir)

    if bpy.app.version >= (2, 91, 0):
        vl = bpy.context.view_layer.depsgraph
    else:
        vl = bpy.context.view_layer

    result, location, normal, index, object, matrix = scene.ray_cast(vl, org, dir)

    if result:
        if focus:
            cam_dir = cam_obj.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
            dist = abs(distance_point_to_plane(cam_obj.location, location, cam_dir))
            # print ('dist = ' + str(dist))
            cam_obj.data.dof.focus_distance = dist
        return result, location, object, normal

    else:
        return result, None, None, None

def traverse_tree(t):
    yield t
    for child in t.children:
        yield from traverse_tree(child)

def copy_collections(object, target):
    colls = object.users_collection

    # Remove collections from object if it is in another collection than the default Scene / Master Collection
    if not (len(colls) == 1 and colls == (bpy.data.scenes[bpy.context.scene.name].collection,)):
        bpy.context.view_layer.objects.active = target
        bpy.ops.collection.objects_remove_all()
        # Assign Object collections to Target
        for coll in colls:
            bpy.data.collections[coll.name].objects.link(target)

def list_collections(context):
    scene_colls = context.scene.collection

    # Get names of collections and sort them
    collections = [c for c in traverse_tree(scene_colls)]
    collection_names = [c.name for c in traverse_tree(scene_colls)]
    collection_names = sorted(collection_names)

    # Get Collections from Collection names, but still sorted.
    collections=[]
    for c in collection_names:
        # Ignore 'Master Collection' or 'Scene Collection' (Blender 3.0), adding it as scene.collection)
        if c not in {'Master Collection', 'Scene Collection'}:
            collections.append(bpy.data.collections[c])
        else:
            collections.append(context.scene.collection)
    return collections

def show_message(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def has_keyframe(ob, attr):
    anim = ob.animation_data
    if anim is not None and anim.action is not None:
        for fcu in anim.action.fcurves:
            if fcu.data_path == attr:
                return len(fcu.keyframe_points) > 0
    return False

def list_cameras(context):
    drone_cam = None
    cam_collections = []
    cam_list = []

    cameras = [cam for cam in context.scene.collection.all_objects if cam.type=='CAMERA']
    cam_list = [cam.name for cam in cameras]
    cam_list.sort()
    if 'DroneCamera' in cam_list:
        drone_cam = 'DroneCamera'
        cam_list.remove('DroneCamera')

    collections = list_collections(context)
    for coll in collections:
        coll_cams = [obj.name for obj in coll.objects if obj.type=='CAMERA']
        if coll_cams:
            cam_collections.append(coll)

    return cam_list,cam_collections,drone_cam

def list_lights(context):
    light_collections = []
    light_list = []
    active_light = None

    light_list = [obj.name for obj in context.scene.collection.all_objects if obj.type=='LIGHT']
    
    if bpy.context.object and bpy.context.object.type =='LIGHT':
        active_light = bpy.context.object

    light_list.sort()

    collections = list_collections(context)
    for coll in collections:
        coll_lights = [obj.name for obj in coll.objects if obj.type=='LIGHT']
        if coll_lights:
            light_collections.append(coll)

    return light_list,light_collections,active_light

def read_pixel_color(x,y,buffer):
    if bpy.app.version >= (3,2,2):
        pixel = buffer.read_color(x, y, 1, 1, 3, 0, 'FLOAT')
        pixel.dimensions = 1 * 1 * 3
        value = [float(item) for item in pixel]
    else:
        bgl.glReadPixels(x, y, 1, 1, bgl.GL_RGB, bgl.GL_FLOAT, buffer)
        value = buffer
    return value
    
def duplicate_object(obj, data=True, actions=True, collection=None):
    obj_copy = obj.copy()
    if data:
        obj_copy.data = obj_copy.data.copy()
    if actions and obj_copy.animation_data:
        if obj_copy.animation_data.action:
            obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
    collection.objects.link(obj_copy)
    return obj_copy

def rot_around_pivot(obj, pivot, angle, axis='Z',apply=True):
    # get the rotation matrix (deg is negated - bpy goes clockwise, mathutils counter-clockwise
    rot_matrix = Matrix.Rotation(math.radians(angle), 4, axis)

    # decompose the world matrix
    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
    orig_rot_matrix =   orig_rot.to_matrix().to_4x4()
    orig_scale_matrix = Matrix.Scale(orig_scale[0],4,(1,0,0)) @ Matrix.Scale(orig_scale[1],4,(0,1,0)) @ Matrix.Scale(orig_scale[2],4,(0,0,1))

    # this does the job
    #                       1. translate to center
    #         2. rotate     |
    #         |             |                  3. translate back
    #         |             |                  |
    new_loc = rot_matrix @ (orig_loc - pivot.location) + pivot.location

    # make a matrix out of the new location 
    new_loc_matrix = Matrix.Translation(new_loc)

    # all together now
    if apply:
        obj.matrix_world = new_loc_matrix @ rot_matrix @ orig_rot_matrix @ orig_scale_matrix
        
    return new_loc

def same_sign(x,y):
    if abs(x) + abs(y) == abs(x + y):
        return True

def should_update(self,context,prop_enabled,post_effects=False):
    if post_effects:
        settings = context.scene.camera.data.post_effects
    else:
        settings = context.scene.camera.data.photographer
    update = False
    pg_main_cam_settings = None
    pg_main_cam = bpy.data.objects.get(context.scene.photographer.main_camera,None)

    if pg_main_cam:
        if post_effects:
            pg_main_cam_settings = pg_main_cam.data.post_effects
        else:
            pg_main_cam_settings = pg_main_cam.data.photographer
    
    # If the current camera (self) is the scene camera, update
    if self == settings:
        update = True

    # If not, but there is a Main Camera and the camera does not override  
    elif pg_main_cam_settings:
        if self == pg_main_cam_settings and not settings.get(prop_enabled,False):
            update = True
    
    return update

def set_node_param(parent_data,node_name,param,value):
    nodes = parent_data.node_tree.nodes
    node = nodes.get(node_name)
    node.inputs[param].default_value = value

def keyframe_node_param(parent_data,node_name,param):
    nodes = parent_data.node_tree.nodes
    node = nodes.get(node_name)
    node.inputs[param].keyframe_insert(data_path='default_value') 