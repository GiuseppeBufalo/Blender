import bpy

from .modifier_stack.main import CSDF_OT_MODSTACK_MOVE_ITEM, CSDF_OT_SELECT_NESTED_PRIMITIVES, CSDF_OT_UNNEST_PRIMITIVE

from .addroot import CSDF_OT_ADD_ROOT
from .addprim import csdfData, CSDF_OT_ADD_PRIM

from bpy.props import PointerProperty


classes = (
    CSDF_OT_MODSTACK_MOVE_ITEM, CSDF_OT_SELECT_NESTED_PRIMITIVES, CSDF_OT_UNNEST_PRIMITIVE,

    CSDF_OT_ADD_ROOT,
    CSDF_OT_ADD_PRIM, csdfData
)


def register_operators():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.csdfData = PointerProperty(type=csdfData)


def unregister_operators():

    del bpy.types.Object.csdfData

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
