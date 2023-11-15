import bpy
from ... utility import addon


def draw(column, context):

    preference = addon.preference().property
    #self.layout.row().prop(preference, 'boolean_solver', expand=True)
    row = column.row(align=True)
    row.label(text = "Behavior")

    box = column.box()
    row = box.row(align=True)
    row.prop(preference, 'bool_bstep', text='Bevel Step')
    row.prop(preference, 'parent_boolshapes', text='Parent Boolshapes')

    row = column.row(align=True)
    row.label(text = "Auto Cutter Removal")

    box = column.box()
    row = box.row(align=True)
    row.prop(preference, 'Hops_sharp_remove_cutters', text='Csharp')
    row.prop(preference, 'Hops_smartapply_remove_cutters', text='Smart Apply')
    
    row = column.row(align=True)
    row.label(text='Cut In:')
    
    box = column.box()
    row = box.row(align=True)
    row.prop(preference, 'keep_cutin_bevel', expand=True, text='Keep Bevel')
    #label_row(preference.property, 'Hops_sharp_remove_cutters', layout.row(), label='Hops_sharp_remove_cutters')
