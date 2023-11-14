import bpy

from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ... import utility


class BC_OT_error_log(Operator):
    bl_idname = 'bc.error_log'
    bl_label = 'Error Encountered'
    bl_description = '\n  Click to view error log'


    def execute(self, context):
        utility.handled_error = False

        element_default = {
            'expand': False,
            'count': 1,
            'header': '',
            'body': '',
        }

        utility.error_elem = {}

        for error in utility.error_log:
            if error not in utility.error_elem:
                utility.error_elem[error] = element_default.copy()
                utility.error_elem[error]['header'] = error.split('\n')[-1]
                utility.error_elem[error]['body'] = error
            else:
                utility.error_elem[error]['count'] += 1

        bpy.ops.wm.call_panel(name='BC_PT_error_log', keep_open=True)
        return {'FINISHED'}
