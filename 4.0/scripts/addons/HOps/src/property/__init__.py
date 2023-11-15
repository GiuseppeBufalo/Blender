import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup, Object, Collection
from bpy.props import *

from . import preference, data, last, object, dots, helper



class option(PropertyGroup):
    running: BoolProperty()
    dots: PointerProperty(type=dots.option)
    helper: PointerProperty(type=helper.option)


classes = [
    dots.Points,
    dots.option,
    helper.option,
    option]


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.hardflow = PointerProperty(type=option)

    preference.register()


def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.WindowManager.hardflow

    preference.unregister()
