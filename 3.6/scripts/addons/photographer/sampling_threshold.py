import bpy

from . import prefs
from .operators.exposure import get_exposure_node

def calc_light_threshold(self, context):
    light_thres = bpy.context.preferences.addons[__package__].preferences.default_light_threshold
    exposure = context.scene.view_settings.exposure

    # Replace Scene Exposure value with Node exposure value if doing compositing exposure
    if context.scene.photographer.comp_exposure:
        exp_node = get_exposure_node(self,context)
        if exp_node:
            exposure = exp_node.inputs['Exposure'].default_value

    optimal_threshold = light_thres / pow(2,exposure)

    return optimal_threshold

def update_light_threshold(self,context):
    if context.scene.render.engine == 'CYCLES':
        context.scene.cycles.light_sampling_threshold = calc_light_threshold(self,context)
        #trick to update render
        bpy.context.scene.view_settings.exposure = bpy.context.scene.view_settings.exposure

    if context.scene.render.engine == 'BLENDER_EEVEE':
        context.scene.eevee.light_threshold = calc_light_threshold(self,context)

    settings = context.scene.camera.data.photographer
    settings.light_threshold_warning = False

def check_light_threshold(self,context):
    if context.scene.render.engine in {'CYCLES','BLENDER_EEVEE'}:
        optimal_threshold = calc_light_threshold(self,context)
        if context.scene.render.engine == 'CYCLES':
            light_threshold = context.scene.cycles.light_sampling_threshold
        elif context.scene.render.engine == 'BLENDER_EEVEE':
            light_threshold = context.scene.eevee.light_threshold

        settings = context.scene.camera.data.photographer

        if light_threshold >= optimal_threshold:
            if light_threshold - optimal_threshold >= optimal_threshold:
                settings.light_threshold_warning = True
                return "Potential Noise issue"
            else:
                settings.light_threshold_warning = False

        elif light_threshold <= optimal_threshold:
            if optimal_threshold - light_threshold >= light_threshold:
                settings.light_threshold_warning = True
                return "Ineffective Light Threshold"
            else:
                settings.light_threshold_warning = False


class PHOTOGRAPHER_OT_UpdateLightThreshold(bpy.types.Operator):
    bl_idname = "photographer.updatelightthreshold"
    bl_label = "Calculate Light Threshold from Exposure"
    bl_description = "Calculate Light Threshold according to Exposure to avoid grain in low exposure scenes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs.update_light_threshold(self,context)
        return{'FINISHED'}

def light_threshold_button(self, context):
    layout = self.layout
    if bpy.context.preferences.addons[__package__].preferences.auto_light_threshold:
        layout.label(text='Auto Light Threshold (see Photographer add-on preferences)', icon='INFO')
    else:
        layout.operator("photographer.updatelightthreshold")
