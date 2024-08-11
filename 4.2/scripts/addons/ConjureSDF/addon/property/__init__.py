import bpy

from .primitives.main import CSDF_primitives
from .addon import CSDF_Props

# register CSDF_Props last!
classes = (
    CSDF_primitives,
    CSDF_Props,
)


def register_properties():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister_properties():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)