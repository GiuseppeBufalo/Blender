import bpy
from bpy.props import StringProperty, BoolProperty
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as view3d_tools


class CallDecalOperator(bpy.types.Operator):
    bl_idname = "machin3.call_decal_operator"
    bl_label = "MACHIN3: Call DECALmachine Operator"
    bl_options = {'INTERNAL', 'UNDO'}

    idname: StringProperty()
    isinvoke: BoolProperty()

    def invoke(self, context, event):
        active_tool = view3d_tools.tool_active_from_context(context)

        if active_tool.idname == 'BoxCutter':
            return {'PASS_THROUGH'}

        else:
            op = getattr(bpy.ops.machin3, self.idname, None)

            if op:
                if self.isinvoke:
                    op('INVOKE_DEFAULT')

                else:
                    op()

        return {'FINISHED'}
