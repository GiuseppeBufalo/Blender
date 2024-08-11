"""
    User driven preferences.
"""
import bpy
from bpy.types import AddonPreferences
from bpy.props import FloatVectorProperty, IntProperty, BoolProperty
import os
from bpy.utils import register_class, unregister_class
import numpy as np


def addon_name():
    return os.path.basename(os.path.dirname(os.path.realpath(__file__)))

class ConformObjectPreferences(AddonPreferences):
    """Custom preferences and associated UI for add on properties."""
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = addon_name()

    disable_bg_checks : BoolProperty(
        name = "Disable Background Checks",
        description="Disable the add-on's background checks which can slow down busy scenes",
        default=False)



    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'disable_bg_checks')



    
classes = [
    ConformObjectPreferences]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)