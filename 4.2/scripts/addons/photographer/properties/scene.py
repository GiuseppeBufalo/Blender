import bpy
from ..camera import update_settings
from ..operators import world as wd
from ..constants import addon_name
from ..ui import library
from bpy.types import PropertyGroup
from bpy.props import (BoolProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       IntProperty,
                       StringProperty,
                       )

CAMERAS = []
main_cameraS = [('NONE','','')]

def update_comp_exposure(self,context):
    if self.comp_exposure:
        bpy.ops.photographer.add_exposure_node()
    else:
        bpy.ops.photographer.disable_exposure_node()

def update_active_camera_index(self, context):
	context.scene.photographer.active_camera_index = -1

def update_active_light_index(self, context):
	context.scene.photographer.active_light_index = -1

def camera_items(self,context):
    global CAMERAS
    CAMERAS = []
    camera_objs = [o for o in bpy.context.scene.objects if o.type=='CAMERA']
    for cam in camera_objs:
        CAMERAS.append((cam.name,cam.name,''))
    return CAMERAS

def main_camera_items(self,context):
    global main_cameraS
    main_cameraS = [('NONE','','')]
    camera_objs = [o for o in bpy.context.scene.objects if o.type=='CAMERA']
    for cam in camera_objs:
        main_cameraS.append((cam.name,cam.name,''))
    # print(main_cameraS[0])
    return main_cameraS

# def get_active_scene_camera(self):
#     for i, item in enumerate(CAMERAS):
#         if item[0] == self.id_data.camera.name:
#             index = str(i)
#             break
#     return self.get(index, 0)
# index doesn't work, expects string but doesn't work with camera name either.

# def set_active_scene_camera(self,value):
#     self['active_scene_camera'] = value
#     print(value)
#     if value is not None:
#         bpy.ops.photographer.look_through(camera = CAMERAS[value][0])

# def update_active_scene_camera(self,context):
#     if self.active_scene_camera:
#         bpy.ops.photographer.look_through(camera = self.active_scene_camera)

def update_main_camera(self,context):
    cam = context.scene.camera
    if cam:
        settings = cam.data.photographer
        update_settings(settings,context)

class SceneSettings(PropertyGroup):
    comp_exposure : BoolProperty(
        name = "Apply at Compositing",
        description = ("Apply Exposure during Compositing. \nExposure won't be "
                        "visible in viewport, but will be applied to EXR files"),
        default = False,
        options = {'HIDDEN'},
        update = update_comp_exposure,
    )
    main_camera : EnumProperty(
        name="Photographer Main Camera",
        items = main_camera_items,
        options = {'HIDDEN'},
        update = update_main_camera,
    )
    active_view_layer_index: IntProperty(
        default=-1,
    )
    cam_list_sorting : EnumProperty(
        name = "Sort by Camera or Collection",
        items = [('ALPHA','Sort Alphabetically','','CAMERA_DATA',0),
                ('COLLECTION','Group by Collection','','OUTLINER_OB_GROUP_INSTANCE',1)],
        options = {'HIDDEN'},
        # default = bpy.context.preferences.addons[addon_name].preferences.default_cam_list_sorting,
    )
    active_camera_index: IntProperty(
        default=-1,
        # update=update_active_camera_index,
    )
    active_camera_collection_index: IntProperty(default=-1,
        # update=update_active_light_index,
    )
    # active_scene_camera: EnumProperty(
    #     name="Scene Camera",
    #     items = camera_items,
    #     options = {'HIDDEN'},
    #     get = get_active_scene_camera,
    #     set = set_active_scene_camera,
    #     # update = update_active_scene_camera,
    # )
    list_filter : StringProperty(
        name="Filter",
        description="Filter by name",
    )
    list_filter_reverse : BoolProperty(
        name="Reverse Order",
        description="Reverse Sorting order",
        default = False,
    )
    use_filter_invert : BoolProperty(
        name="Invert",
        description="Invert filtering (show hidden items, and vice versa)",
        default = False,
    )   
    scene_collection_expand : BoolProperty(default = True)

class LightMixerSceneSettings(PropertyGroup):
    solo_active: BoolProperty(
        name="Solo",
        default=False,
        options = {'HIDDEN'},
    )
    world_show_more: BoolProperty(
        name="Expand World settings",
        default=True,
        options = {'HIDDEN'},
    )
    show_active_light : BoolProperty(
        name="Active Light properties",
        default=True,
    )

    hdri_tex: EnumProperty(
        name="HDRI Texture",
        items=wd.enum_previews_hdri_tex,
        update=wd.update_hdri_tex,
    )
    hdri_category: EnumProperty(
        name="HDRI Category",
        items=library.subfolders_return,
        description="HDRI Subfolder category",
        update=wd.update_hdri_tex,
    )
    hdri_rotation: FloatProperty(
        name="Rotation",
        default=0, soft_min=-3.141593, soft_max=3.141593, unit='ROTATION',
        get=wd.get_hdri_rotation,
        set=wd.set_hdri_rotation,
    )
    hdri_use_temperature: BoolProperty(
        name="Use Color Temperature",
        default=True,
        options = {'HIDDEN'},
        update = wd.update_hdri_use_temperature,
    )
    hdri_temperature: FloatProperty(
        name="Temperature",
        default=6500, min=0, soft_min=1100, soft_max=13000,
        get=wd.get_hdri_temperature,
        set=wd.set_hdri_temperature,
    )
    hdri_tint: FloatProperty(
        name="Tint",
        default=0, min=-100, max=100,
        get=wd.get_hdri_tint,
        set=wd.set_hdri_tint,
    )
    hdri_color: FloatVectorProperty(
        name="Color Multiplier",
        subtype='COLOR',
        min=0.0, max=1.0, size=4,
        default=(1.0,1.0,1.0,1.0),
        get=wd.get_hdri_color,
        set=wd.set_hdri_color,
    )
    hdri_blur: FloatProperty(
        name="Blur",
        default=0, min=0, soft_max=1,
        get=wd.get_hdri_blur,
        set=wd.set_hdri_blur,
    )
    light_list_sorting : EnumProperty(
        name = "Sort by Light or Collection",
        items = [('ALPHA','Sort Alphabetically','','LIGHT_DATA',0),
                ('COLLECTION','Group by Collection','','OUTLINER_OB_GROUP_INSTANCE',1)],
        options = {'HIDDEN'},
    )
    active_light_index: IntProperty(
        default=-1,
        # update=update_active_light_index,
    )
    active_light_collection_index: IntProperty(default=-1,
        # update=update_active_light_index,
    )
    list_filter : StringProperty(
        name="Filter",
        description="Filter by name",
    )
    list_filter_reverse : BoolProperty(
        name="Reverse Order",
        description="Reverse Sorting order",
        default = False,
    )
    use_filter_invert : BoolProperty(
        name="Invert",
        description="Invert filtering (show hidden items, and vice versa)",
        default = False,
    )   
    scene_collection_expand : BoolProperty(default = True)
    light_name_width : FloatProperty(name = "Width", default = 9 ,min = 0.5)    
