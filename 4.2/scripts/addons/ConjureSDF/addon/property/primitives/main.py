import bpy

from bpy.props import BoolProperty


class CSDF_primitives(bpy.types.PropertyGroup):

    keep_scale : BoolProperty(
        name = "Keep Primitive Scale", description = "Scale of primitive does not revert to default when primitive type is changed",
        default=False
    )


def draw_primitives(prefs, layout):

    column = layout.column()
    column.label(text="Primitives", icon='MESH_CUBE')

    box = column.box()

    row = box.row()
    row.prop(prefs.prims, "keep_scale")
