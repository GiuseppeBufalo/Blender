import bpy
from ..operators import world as wd
from bpy.types import PropertyGroup
from bpy.props import (BoolProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       )

class LightMixerWorldSettings(PropertyGroup):
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
