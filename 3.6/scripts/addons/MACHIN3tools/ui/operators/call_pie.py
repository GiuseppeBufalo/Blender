import bpy
from bpy.props import StringProperty


class CallMACHIN3toolsPie(bpy.types.Operator):
    bl_idname = "machin3.call_machin3tools_pie"
    bl_label = "MACHIN3: Call MACHIN3tools Pie"
    bl_options = {'REGISTER', 'UNDO'}

    idname: StringProperty()

    def invoke(self, context, event):
        view = context.space_data

        if view.type == 'VIEW_3D':
            scene = context.scene
            m3 = scene.M3


            if self.idname == 'shading_pie':
                engine = scene.render.engine
                device = scene.cycles.device
                shading = view.shading

                if engine != m3.render_engine and engine in ['BLENDER_EEVEE', 'CYCLES']:
                    m3.avoid_update = True
                    m3.render_engine = engine

                if engine == 'CYCLES' and device != m3.cycles_device:
                    m3.avoid_update = True
                    m3.cycles_device = device

                if shading.light != m3.shading_light:
                    m3.avoid_update = True
                    m3.shading_light = shading.light

                    m3.avoid_update = True
                    m3.use_flat_shadows = shading.show_shadows

                if bpy.app.version >= (3, 5, 0) and shading.type in ['MATERIAL', 'RENDERED']:
                    m3.avoid_update = True
                    m3.use_compositor = shading.use_compositor

                bpy.ops.wm.call_menu_pie(name='MACHIN3_MT_%s' % (self.idname))


            elif self.idname == 'tools_pie':
                if context.mode in ['OBJECT', 'EDIT_MESH']:
                    bpy.ops.wm.call_menu_pie(name='MACHIN3_MT_%s' % (self.idname))

                else:
                    return {'PASS_THROUGH'}

        return {'FINISHED'}
