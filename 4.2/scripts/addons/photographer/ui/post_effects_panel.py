import bpy
from bpy.types import Panel
from .. import camera_presets
from ..constants import  addon_name

def post_effects_header(self,context,use_scene_camera=False):
    layout = self.layout
    if use_scene_camera:
        cam = context.scene.camera
        settings = cam.data.post_effects
    else:
        cam = context.camera
        settings = cam.post_effects
    main_cam = context.scene.photographer.main_camera
    layout.prop(settings, "post_effects_enabled", text="")
    if main_cam != 'NONE':
        if main_cam != cam.name:
            if not settings.post_effects_enabled:
                layout.label(text='', icon='EVENT_M')

class PHOTOGRAPHER_PT_ViewPanel_LensEffects(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'Camera Post FX'
    bl_order = 5
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'    
    
    def draw_header_preset(self, context):
        camera_presets.PHOTOGRAPHER_PT_LensEffectsPresets.draw_panel_header(self.layout)
    
    def draw_header(self,context):
        post_effects_header(self,context,True)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        cam = context.scene.camera.data
        post_effects = cam.post_effects
        layout.enabled = post_effects.post_effects_enabled

        view = context.space_data
        if bpy.app.version >= (3,5,0):
            if view.type == 'VIEW_3D':
                shading = view.shading
                layout.prop(shading, "use_compositor", text="Viewport Render", expand=True)
                if shading.use_compositor != 'DISABLED':
                    if cam.passepartout_alpha != 1.0:
                        layout.label(text='Passepartout should be set to 1',icon='ERROR')

        # Distortion
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading='Distortion')
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "lens_distortion", text="")
        else:
            sub.prop(post_effects, "lens_distortion", text="Distortion")
        sub = sub.row(align=True)
        sub.active = post_effects.lens_distortion
        sub.prop(post_effects, "lens_distortion_amount", text="", slider=True)
        if post_effects.lens_distortion:
            col = box.column(align=True)
            col.prop(post_effects, "lens_distortion_type", text="Type")
            if post_effects.lens_distortion_type == 'STMAP':
                col.prop(post_effects, "lens_distortion_scale_comp", text="Upscale %")
                col.label(text='Reatime Comp not supported yet.',icon='ERROR')
                col.template_icon_view(post_effects, "stmap_tex", show_labels=True, scale=5)     
            # col.active = settings.lens_distortion

        # Chromatic Aberration
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading='Lateral CA')
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "lateral_ca", text="")
        else:
            sub.prop(post_effects, "lateral_ca", text="Lateral CA")
        sub = sub.row(align=True)
        sub.active = post_effects.lateral_ca
        sub.prop(post_effects, "lateral_ca_amount", text="", slider=True)
        if post_effects.lateral_ca:
            col = box.column(align=True)
            col.prop(post_effects, "lateral_ca_type", text="Type")
            # col.active = settings.lateral_ca

        # Lens Softness
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading="Lens Softness")
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "lens_softness", text="")
        else:
            sub.prop(post_effects, "lens_softness", text="Lens Softness")
        sub = sub.row(align=True)
        sub.active = post_effects.lens_softness
        sub.prop(post_effects, "lens_softness_amount", text="", slider=True)
        if post_effects.lens_softness:
            col = box.column(align=True)
            col.prop(post_effects, "corner_softness_amount")
            col.prop(post_effects, "center_softness_amount", slider=True)
            col.separator()
            col.prop(post_effects, "corner_softness_falloff", slider=True)
            row = col.row(align=True)
            row.prop(post_effects, "corner_mask_width", text="Scale X")
            row.prop(post_effects, "corner_mask_height", text="Y")
            # col.active = settings.lens_softness

        # Fringing
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading='Fringing')
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "fringing", text="")
        else:
            sub.prop(post_effects, "fringing", text="Fringing")
        sub = sub.row(align=True)
        sub.active = post_effects.fringing
        sub.prop(post_effects, "fringing_amount", text="", slider=True)
        if post_effects.fringing:
            col = box.column(align=True)
            col.prop(post_effects, "fringing_size", text="Size")
            col.prop(post_effects, "fringing_threshold", text="Threshold")
            col.prop(post_effects, "fringing_color", text="Color")

        # Streaks
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading='Streaks')
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "streaks", text="")
        else:
            sub.prop(post_effects, "streaks", text="Streaks")
        sub = sub.row(align=True)
        sub.active = post_effects.streaks
        sub.prop(post_effects, "streaks_amount", text="", slider=True)
        if post_effects.streaks:
            col = box.column(align=True)
            col.prop(post_effects, "streaks_number", text="Number")
            col.prop(post_effects, "streaks_angle_offset", text="Angle", slider=True)
            col.prop(post_effects, "streaks_fade", text="Fade", slider=True)
            col.prop(post_effects, "streaks_threshold", text="Threshold")

        # Lens Vignetting
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading='Vignetting')
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "lens_vignetting", text="")
        else:
            sub.prop(post_effects, "lens_vignetting", text="Vignetting")
        sub = sub.row(align=True)
        sub.active = post_effects.lens_vignetting
        sub.prop(post_effects, "lens_vignetting_amount", text="", slider=True)
        if post_effects.lens_vignetting:
            col = box.column(align=True)
            col.prop(post_effects, "lens_vignetting_falloff", text="Falloff")
            row = col.row(align=True)
            row.prop(post_effects, "lens_vignetting_width", text="Scale X")
            row.prop(post_effects, "lens_vignetting_height", text="Y")
            # col.active = settings.lens_vignetting

        # Sharpen
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading="Sharpen")
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "sharpen", text="")
        else:
            sub.prop(post_effects, "sharpen", text="Sharpen")
        sub = sub.row(align=True)
        sub.active = post_effects.sharpen
        sub.prop(post_effects, "sharpen_amount", text="", slider=True)
        if post_effects.sharpen:
            col = box.column(align=True)
            col.prop(post_effects, "sharpen_radius", text="Radius")

        # Fil Grain
        box = layout.box()
        if bpy.app.version >= (2, 90, 1):
            col = box.column(heading="Film Grain")
        else:
            col = box.column()
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(post_effects, "film_grain", text="")
        else:
            sub.prop(post_effects, "film_grain", text="Film Grain")
        sub = sub.row(align=True)
        sub.active = post_effects.film_grain
        sub.prop(post_effects, "film_grain_amount", text="", slider=True)
        if post_effects.film_grain:
            col = box.column(align=True)
            col.prop(post_effects, "film_grain_size", text="Size")
            if bpy.app.version >= (3,5,0):
                if view.type == 'VIEW_3D':
                    if shading.use_compositor != 'DISABLED':
                        col.label(text='Size cannot be trusted in Viewport',icon='ERROR')
            col.template_icon_view(post_effects, "film_grain_tex", show_labels=True, scale=8)     

class PHOTOGRAPHER_PT_Panel_LensEffects(PHOTOGRAPHER_PT_ViewPanel_LensEffects):
    bl_parent_id = "PHOTOGRAPHER_PT_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw_header(self,context):
        post_effects_header(self,context,False)

class PHOTOGRAPHER_PT_NodeEditor_LensEffects(PHOTOGRAPHER_PT_ViewPanel_LensEffects):
    bl_space_type = 'NODE_EDITOR'
    bl_parent_id = ''

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        show_image_panels =  bpy.context.preferences.addons[addon_name].preferences.show_image_panels
        return context.scene.camera and context.scene.camera.type == 'CAMERA' and show_image_panels and snode.tree_type == 'CompositorNodeTree'

class PHOTOGRAPHER_PT_ImageEditor_LensEffects(PHOTOGRAPHER_PT_ViewPanel_LensEffects):
    bl_space_type = 'IMAGE_EDITOR'
    bl_parent_id = ''

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        return bpy.context.preferences.addons[addon_name].preferences.show_image_panels