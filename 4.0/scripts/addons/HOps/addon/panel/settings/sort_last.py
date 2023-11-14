import bpy

from bpy.types import Panel

from ... utility import addon, modifier


class HOPS_PT_sort_last(Panel):
    bl_label = 'Sort Last'
    bl_space_type = 'TOPBAR'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        preference = addon.preference()
        layout = self.layout

        row = layout.row(align=True)

        for type in modifier.sort_types:
            icon = F'MOD_{type}'
            if icon == 'MOD_WEIGHTED_NORMAL':
                icon = 'MOD_NORMALEDIT'
            elif icon == 'MOD_SIMPLE_DEFORM':
                icon = 'MOD_SIMPLEDEFORM'
            elif icon == 'MOD_DECIMATE':
                icon = 'MOD_DECIM'
            elif icon == 'MOD_WELD':
                icon = 'AUTOMERGE_OFF'
            elif icon == 'MOD_UV_PROJECT':
                icon = 'MOD_UVPROJECT'
            sub = row.row(align=True)
            sub.enabled = getattr(preference.property, F'sort_{type.lower()}')
            sub.prop(preference.property, F'sort_{type.lower()}_last', text='', icon=icon)

        if preference.property.sort_bevel:
            label_row(preference.property, 'sort_bevel_ignore_weight', layout.row(), label='Ignore Bevels using Weights')
            label_row(preference.property, 'sort_bevel_ignore_vgroup', layout.row(), label='Ignore Bevels with VGroups')
            label_row(preference.property, 'sort_bevel_ignore_only_verts', layout.row(), label='Ignore Bevels using Only Verts')

        layout.separator()

        label_row(preference.property, 'sort_depth', layout.row(), label='Sort Depth')
        label_row(preference.property, 'sort_ignore_char', layout.row(), label='Ignore Flag', scale_x_prop=0.35)
        label_row(preference.property, 'sort_stop_char', layout.row(), label='Stop Flag', scale_x_prop=0.35)


def label_row(path, prop, row, label='', scale_x_prop=1.0):
    row.label(text=label)
    sub = row.row()
    sub.scale_x = scale_x_prop
    sub.prop(path, prop, text='')

