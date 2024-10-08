import bpy

from ... icons import get_icon_id


def draw(column, context):
    asmooth = bpy.context.object.data
    obj = bpy.context.object
    swire = bpy.context.object
    ob = bpy.context.object

    row = column.row(align=True)

    column.separator()
    row = column.row(align=True)
    row.prop(obj, "name", text="")
    row.prop(ob, "parent", text="")

    column.separator()
    row = column.row(align=True)
    row.operator("object.shade_smooth", text="Smooth")
    row.operator("object.shade_flat", text="Flat")

    row = column.row(align=True)
    asmooth = bpy.context.object.data

    if context.active_object and context.active_object.type == 'MESH':
        if ob.data.has_custom_normals:
            row.prop(asmooth, "use_auto_smooth", text="Auto Smooth", toggle=True)
            row.operator("mesh.customdata_custom_splitnormals_clear", text = "Remove Normal", icon='X')
        else:
            row.prop(asmooth, "use_auto_smooth", text="Auto Smooth", toggle=True)
            row.operator("mesh.customdata_custom_splitnormals_add", text = "Add Normal", icon='ADD')


    column.separator()
    row = column.row(align=True)

    column.separator()
    row = column.row(align=True)
    row.prop(swire, "show_wire", text="Show Wire")
    row.prop(swire, "show_all_edges", text="Show All Wires")

    if context.active_object and context.active_object.type == 'MESH':
        column.separator()
        row = column.row(align=True)
        row.prop(context.active_object.data, 'remesh_voxel_size', text='Voxel Size')
        row.operator("view3d.voxelizer", text=F"Voxelize Object", icon_value=get_icon_id("Voxelize"))
    column.separator()
