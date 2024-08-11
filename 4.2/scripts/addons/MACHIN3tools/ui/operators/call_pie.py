import bpy
from bpy.props import StringProperty
from ... utils.modifier import replace_invalid_auto_smooth_mods
from ... utils.render import get_render_engine, get_device, is_eevee_view, is_volume, is_cycles
from ... utils.scene import is_bloom
from ... utils.view import get_shading_type

class CallMACHIN3toolsPie(bpy.types.Operator):
    bl_idname = "machin3.call_machin3tools_pie"
    bl_label = "MACHIN3: Call MACHIN3tools Pie"
    bl_options = {'REGISTER'}

    idname: StringProperty()

    def invoke(self, context, event):
        view = context.space_data

        if view.type == 'VIEW_3D':
            scene = context.scene
            m3 = scene.M3

            if self.idname =='shading_pie':
                eevee = context.scene.eevee
                shading = view.shading
                shading_type = get_shading_type(context)
                active = context.active_object

                if (engine := get_render_engine(context)) != m3.render_engine and engine in ['BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'CYCLES']:
                    m3.avoid_update = True
                    m3.render_engine = engine

                if is_cycles(context) and (device := get_device(context)) != m3.cycles_device:
                    m3.avoid_update = True
                    m3.cycles_device = device

                if bpy.app.version >= (4, 2, 0) and shading_type in ['MATERIAL', 'RENDERED']:

                    if is_eevee_view(context):
                        m3.avoid_update = True
                        m3.eevee_next_resolution = eevee.fast_gi_resolution

                        m3.avoid_update = True
                        m3.eevee_next_thickness = eevee.fast_gi_thickness_near

                        m3.avoid_update = True
                        m3.eevee_next_quality = eevee.fast_gi_quality

                    if (use_volumes := is_volume(context, simple=True, debug=False)) != m3.use_volumes:
                        m3.avoid_update = True
                        m3.use_volumes = use_volumes

                    if (use_bloom := is_bloom(context, simple=True)) != m3.use_bloom:
                        m3.avoid_update = True
                        m3.use_bloom = use_bloom
                    
                if shading.light != m3.shading_light:
                    m3.avoid_update = True
                    m3.shading_light = shading.light

                    m3.avoid_update = True
                    m3.use_flat_shadows = shading.show_shadows

                if active and not active.display_type:
                    active.display_type = 'WIRE' if active.hide_render or not active.visible_camera else 'TEXTURED'

                if active:
                    replace_invalid_auto_smooth_mods([active])

                bpy.ops.wm.call_menu_pie(name=f"MACHIN3_MT_{self.idname}")

            elif self.idname == 'tools_pie':
                if context.mode in ['OBJECT', 'EDIT_MESH']:
                    bpy.ops.wm.call_menu_pie(name=f"MACHIN3_MT_{self.idname}")

                else:
                    return {'PASS_THROUGH'}

        return {'FINISHED'}
