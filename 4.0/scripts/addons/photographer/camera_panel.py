import bpy
from .functions import (
    calc_exposure_value,
    update_exposure_guide,
    shutter_speed_to_angle,
    shutter_angle_to_speed,
    lc_exposure_check,
)
from .autofocus import dof_hyperfocal
from . import camera_presets
from .ui import bokeh
from .constants import panel_value_size

class PHOTOGRAPHER_PT_Panel(bpy.types.Panel):
    # bl_idname = "CAMERA_PT_Photographer"
    bl_label = "Photographer"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        return context.camera

    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True
        settings = context.camera.photographer
        scene = bpy.context.scene

        # UI if camera isn't active
        if scene.camera != bpy.context.active_object:
            layout.label(text="This is not the Active Camera")

            row = layout.row()
            row.operator("photographer.makecamactive", text="Make Active Camera")
            row.operator("photographer.selectactivecam", text="Select Active Camera")

        col = layout.column()
        # Enable UI if Camera is Active
        if scene.camera != bpy.context.active_object:
            col.enabled = False

        col.operator("photographer.applyphotographersettings",
            text="Apply all Settings",
            icon='FILE_REFRESH')
        col.prop(settings,'renderable')

        # World Override
        row = col.row(align=True)
        split = row.split(factor=0.33)
        split.prop(settings, "override_world", text="World Override")
        sub = split.row(align=True)
        sub.active = settings.override_world
        sub.prop(settings, "cam_world", text="")

        # Frame range Override
        row = col.row(align=True)
        row.prop(settings, "override_frames")
        sub = row.row(align=True)
        sub.active = settings.override_frames
        sub.prop(settings, "cam_frame_start", text="Start")
        sub.prop(settings, "cam_frame_end", text="End")

        # Flip canvas
        row = col.row(align=True)
        # row.alignment = 'RIGHT'
        # split = row.split(factor=0.41, align=True)
        # sub = split.row()
        # sub.alignment='RIGHT'
        row.label(text='Flip Camera ')
        flip_x = row.operator("photographer.flip_image", text='X')
        flip_x.x = True
        flip_x.y = False
        flip_x.use_scene_camera = False
        flip_y = row.operator("photographer.flip_image", text= 'Y')
        flip_y.x = False
        flip_y.y = True
        flip_y.use_scene_camera = False

#### CAMERA SETTINGS PANEL ####
class PHOTOGRAPHER_PT_ViewPanel_Camera(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'Camera'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'

    def draw_header_preset(self, context):
        layout = self.layout
        if context.scene.camera == bpy.data.objects.get('MasterCamera'):
            layout.enabled = False
        if context.preferences.addons[__package__].preferences.show_compact_ui:
            row = layout.row(align=False)
            row.alignment = 'RIGHT'

            cam = context.scene.camera.data
            settings = cam.photographer
            row.scale_x = 0.9
            row.prop(settings,'sensor_type', text="")

        camera_presets.PHOTOGRAPHER_PT_CameraPresets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        cam = context.scene.camera.data
        settings = cam.photographer

        master_col = layout.column(align=True)
        if context.scene.camera == bpy.data.objects.get('MasterCamera'):
            master_col.enabled = False

        col = master_col.column(align=True)
        if not context.preferences.addons[__package__].preferences.show_compact_ui:
            col.prop(settings,'sensor_type')
        if settings.sensor_type == 'Custom':
            if cam.sensor_fit == 'VERTICAL':
                col.prop(cam,'sensor_height')
            else:
                col.prop(cam,'sensor_width')

        col = layout.column(align=True)
        col.prop(cam, "type")
        if context.scene.render.engine == 'CYCLES' and settings.fisheye:
            col.enabled = False

        # Clip values
        col = layout.column(align=True)
        col.prop(cam, "clip_start")
        col.prop(cam, "clip_end")

        # Passepartout
        if bpy.app.version >= (2, 90, 1):
            col = layout.column(align=False, heading='Passepartout')
        else:
            col = layout.column(align=False)
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(cam, "show_passepartout", text="")
        else:
            sub.prop(cam, "show_passepartout", text="Passepartout")
        sub = sub.row(align=True)
        sub.active = cam.show_passepartout
        sub.prop(cam, "passepartout_alpha", text="")

        # Flip canvas
        row = col.row(align=True)
        row.alignment = 'RIGHT'
        split = row.split(factor=0.41, align=True)
        sub = split.row()
        sub.alignment='RIGHT'
        sub.label(text='Flip Camera ')
        flip_x = split.operator("photographer.flip_image", text='X')
        flip_x.x = True
        flip_x.y = False
        flip_x.use_scene_camera = True
        flip_y = split.operator("photographer.flip_image", text= 'Y')
        flip_y.x = False
        flip_y.y = True
        flip_y.use_scene_camera = True


        # Composition guides
        row = col.row(align=True)
        split = row.split(factor=0.41, align=True)
        split.label(text='')
        split.popover(
            panel="ADD_CAMERA_RIGS_PT_composition_guides",
            text="Composition Guides",)


        # World Override per camera
        if bpy.app.version >= (2, 90, 1):
            col = layout.column(align=False, heading='World Override')
        else:
            col = layout.column(align=False)
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(settings, "override_world", text="")
        else:
            sub.prop(settings, "override_world")
        sub = sub.row(align=True)
        sub.active = settings.override_world
        sub.prop(settings, "cam_world", text="")

        # Frames Override per camera
        if bpy.app.version >= (2, 90, 1):
            col = layout.column(align=False, heading='Frames Override')
        else:
            col = layout.column(align=False)
        col.use_property_decorate = False
        row = col.row(align=True)
        sub = row.row(align=True)
        if bpy.app.version >= (2, 90, 1):
            sub.prop(settings, "override_frames", text="")
        else:
            sub.prop(settings, "override_frames")
        sub = sub.row(align=True)
        sub.active = settings.override_frames
        sub.prop(settings, "cam_frame_start", text="")
        sub.prop(settings, "cam_frame_end", text="")


#### CAMERA SETTINGS PANEL ####
class PHOTOGRAPHER_PT_ViewPanel_Lens(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'Lens'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'

    def draw_header_preset(self, context):
        layout = self.layout
        if context.scene.camera == bpy.data.objects.get('MasterCamera'):
            layout.enabled = False
        if context.preferences.addons[__package__].preferences.show_compact_ui:
            row = layout.row(align=False)
            row.alignment = 'RIGHT'
            row.scale_x = panel_value_size

            cam = context.scene.camera.data
            settings = cam.photographer

            if cam.type == 'ORTHO':
                row.prop(cam, 'ortho_scale',text="")
            else:
                if context.scene.render.engine == 'CYCLES' and settings.fisheye:
                    row.prop(settings,'fisheye_focal', text="")
                else:
                    row.prop(settings, 'focal',text="")
        camera_presets.PHOTOGRAPHER_PT_LensPresets.draw_panel_header(layout)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        cam = context.scene.camera.data
        cam_name = context.scene.camera.name
        settings = cam.photographer

        master_col = layout.column(align=True)
        if context.scene.camera == bpy.data.objects.get('MasterCamera'):
            master_col.enabled = False

        # Focal Length and Fisheye
        col = master_col.column(align=True)
        if not context.preferences.addons[__package__].preferences.show_compact_ui:
            if cam.type == 'ORTHO':
                col.prop(cam, 'ortho_scale')
            else:
                if context.scene.render.engine == 'CYCLES' and settings.fisheye:
                    col.prop(settings,'fisheye_focal', text='Focal Length')
                else:
                    col.prop(settings, 'focal')

        if context.scene.render.engine == 'CYCLES':
            col.prop(settings, 'fisheye')
        if context.scene.render.engine == 'CYCLES' and settings.fisheye:
            col.prop(cam.cycles,'fisheye_fov')
            col.separator()

        # col.prop(settings, 'breathing')
        col = master_col.column(align=True)
        col.use_property_split = True

        row = col.row(align=True)
        row.prop(settings,'lens_shift', slider=True)
        row.operator('photographer.auto_lens_shift', text='', icon='EVENT_A').camera=cam_name
        row = col.row(align=True)
        row.prop(settings,'lens_shift_x', slider=True)
        col.prop(settings,'lens_shift_compensated')

        if context.scene.render.engine == 'CYCLES':
            col.enabled = not settings.fisheye

        # Dolly Zoom
        col.separator()
        col.operator('photographer.dollyzoom', icon='VIEW_ZOOM')
        col.operator('photographer.dollyzoom_set_key', icon='KEY_HLT')

# Function to add Lens Shift to Camera Properties UI
def lens_shift_ui(self, context):
    layout = self.layout
    settings = context.camera.photographer
    cam_name = context.view_layer.objects.active.name

    col = layout.column(align=True)
    row = col.row(align=True)

    row.prop(settings,'lens_shift', slider=True)
    row.operator('photographer.auto_lens_shift', text='', icon='EVENT_A').camera=cam_name
    row = col.row(align=True)
    row.prop(settings,'lens_shift_x', slider=True)
    col.prop(settings,'lens_shift_compensated')

#### DEPTH OF FIELD PANEL ####
class PHOTOGRAPHER_PT_ViewPanel_DOF_Char(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'Depth of Field Characteristics'
    bl_parent_id = "PHOTOGRAPHER_PT_ViewPanel_Lens"

    @classmethod
    def poll(cls, context):
        return context.scene.camera and context.scene.camera.type == 'CAMERA'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        cam_name = context.scene.camera.name
        cam = context.scene.camera.data
        settings = cam.photographer

        if context.scene.render.engine == 'LUXCORE':
            bokeh = cam.luxcore.bokeh
            col = layout.column(align=True)
            col.prop(bokeh,'non_uniform')

            col = layout.column(align=True)
            col.enabled = bokeh.non_uniform
            col.prop(bokeh, "blades")
            col.prop(bokeh, "anisotropy")
            col.prop(bokeh, "distribution")
            if bokeh.distribution in {"EXPONENTIAL", "INVERSEEXPONENTIAL"}:
                col.prop(bokeh, "power")
            elif bokeh.distribution == "CUSTOM":
                col.template_ID(bokeh, "image", open="image.open")
                bokeh.image_user.draw(col, context.scene)

        else:
            col = layout.column(align=True)
            col.prop(settings,'lock_vertical_fov')
            col.prop(cam.dof,'aperture_ratio', text="Anamorphic Ratio")
            col.prop(cam.dof,'aperture_blades')
            col.prop(cam.dof,'aperture_rotation')

class PHOTOGRAPHER_PT_ViewPanel_DOF(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Depth of Field"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'

    def draw_header(self, context):
        cam = context.scene.camera.data
        settings = cam.photographer
        self.layout.prop(settings, "use_dof", text="")

    def draw_header_preset(self, context):
        if context.preferences.addons[__package__].preferences.show_compact_ui:
            layout = self.layout
            if context.scene.camera == bpy.data.objects.get('MasterCamera'):
                layout.enabled = False
            row = layout.row(align=False)
            row.alignment = 'RIGHT'
            row.scale_x = panel_value_size

            cam = context.scene.camera
            cam_name = cam.name
            settings = cam.data.photographer
            if not settings.aperture_slider_enable:
                sub = row.row(align=False)
                sub.scale_x = 1.09
                sub.prop(settings, 'aperture_preset', text="")
            else:
                row.prop(settings, 'aperture', slider=True, text="")
            sub = layout.row(align=False)
            sub.scale_x = 1.26
            sub.prop(settings,'aperture_slider_enable', icon='SETTINGS',
                text='',emboss=False)

            layout.enabled = settings.use_dof
            #or (settings.exposure_mode == 'MANUAL' and settings.exposure_enabled)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        cam = context.scene.camera.data
        settings = cam.photographer
        layout.enabled = settings.use_dof

        if not context.preferences.addons[__package__].preferences.show_compact_ui:
            row = layout.row(align=True)
            if not settings.aperture_slider_enable:
                row.prop(settings, 'aperture_preset', text='Aperture')
            else:
                row.prop(settings, 'aperture', slider=True, text='Aperture F-stop')
            row.prop(settings,'aperture_slider_enable', icon='SETTINGS', text='')

        bokeh.bokeh_ui(self, context,True)

#### EXPOSURE PANELS ####

def exposure_header_preset(self, context, settings, guide):
        layout = self.layout
        if context.scene.camera == bpy.data.objects.get('MasterCamera'):
            layout.enabled = False
        row = layout.row(align=False)
        row.alignment = 'RIGHT'
        row.scale_x = panel_value_size
        row.enabled = settings.exposure_enabled

        ev = calc_exposure_value(self, context, settings)
        ev_guide = update_exposure_guide(self, context, ev)

        if settings.exposure_mode == 'EV':
            if guide == True:
                row.label(text = ev_guide)
            if context.preferences.addons[__package__].preferences.show_compact_ui:
                row.prop(settings,'ev',text='')
        elif settings.exposure_mode == 'MANUAL':
            if guide == True:
                row.label(text = ev_guide + " - Manual  " + str("%.2f" % ev) + " EV")
            else:
                row.label(text = "M - " + str("%.2f" % ev) + " EV")
        elif settings.exposure_mode == 'AUTO':
            if guide == True:
                row.label(text = ev_guide + " - Auto  " + str("%.2f" % ev) + " EV")
            else:
                row.label(text = "A - " + str("%.2f" % ev) + " EV")

def exposure_header(self, context, settings):
    layout = self.layout
    if context.scene.camera == bpy.data.objects.get('MasterCamera'):
        layout.enabled = False
    layout.prop(settings, "exposure_enabled", text="")

def exposure_settings(self,context,settings,parent_ui,guide,image_editor):
    # Settings in Manual
    layout = parent_ui.column()
    layout.enabled = settings.exposure_enabled
    if settings.exposure_mode == 'MANUAL':
        # Shutter Speed parameter
        row = layout.row(align = True)
        if settings.shutter_mode == 'SPEED':
            if not settings.shutter_speed_slider_enable:
                row.prop(settings, 'shutter_speed_preset', text='Shutter Speed')
            else:
                row.prop(settings, 'shutter_speed', slider=True)
            row.operator("photographer.setshutterangle",icon="DRIVER_ROTATIONAL_DIFFERENCE", text="")
            row.prop(settings,'shutter_speed_slider_enable', icon='SETTINGS', text='')

        if settings.shutter_mode == 'ANGLE':
            if not settings.shutter_speed_slider_enable:
                row.prop(settings, 'shutter_angle_preset', text='Shutter Angle')
            else:
                row.prop(settings, 'shutter_angle', slider=True)
            row.operator("photographer.setshutterspeed",icon="PREVIEW_RANGE", text="")
            row.prop(settings,'shutter_speed_slider_enable', icon='SETTINGS', text='')

        # Aperture parameter
        row = layout.row(align = True)
        if not settings.aperture_slider_enable:
            row.prop(settings, 'aperture_preset', text='Aperture')
        else:
            row.prop(settings, 'aperture', slider=True, text='Aperture F-stop')
        row.prop(settings,'aperture_slider_enable', icon='SETTINGS', text='')

        # ISO parameter
        row = layout.row(align = True)
        if not settings.iso_slider_enable:
            row.prop(settings, 'iso_preset', text='ISO')
        else:
            row.prop(settings, 'iso', slider=True)
        row.prop(settings,'iso_slider_enable', icon='SETTINGS', text='')

        # Exposure Compensation
        layout.prop(settings, 'exposure_compensation', text='Exp. Compensation')

    # Settings in EV Mode
    else:
        col = layout.column(align=True)
        col.use_property_split = False
        if settings.exposure_mode == 'EV':
            col.prop(settings, 'ev', slider=True)
            # col.separator()
            col.prop(settings, 'exposure_compensation', text='Exposure Compensation', slider=True)

        auto_col = layout.column(align=True)
        auto_col.use_property_split = False

        if settings.exposure_mode == 'AUTO':
            # No Auto Exposure if using LuxCore and CPU
            engine = context.scene.render.engine
            if engine == 'LUXCORE':
                lc_device = context.scene.luxcore.config.device
                if lc_device == 'CPU':
                    col.operator("photographer.changelcdevice",icon="INFO", text="Requires GPU device")
                    auto_col.enabled = False
            if engine == 'BLENDER_EEVEE':
                if context.scene.eevee.use_soft_shadows:
                    col.operator("photographer.disablesoftshadows",icon="INFO",
                        text="Soft shadows might cause issues")
            auto_col.prop(settings, 'center_weight', slider=True)
            auto_col.prop(settings, 'ae_speed', text='Speed', slider=True)
            # auto_col.separator()
            auto_col.prop(settings, 'exposure_compensation', text='Exposure Compensation', slider=True)

            # Show AE Set Key if 3D view and Auto Exposure mode
            if guide:
                auto_col.separator()
                auto_col.operator("photographer.ae_set_key", icon="KEY_HLT")

            if image_editor:
                auto_col.enabled = False

def exposure_panel(self, context, settings, prop_panel, guide, image_editor):
        layout = self.layout
        scene = bpy.context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.enabled = settings.exposure_enabled

        if context.scene.camera == bpy.data.objects.get('MasterCamera'):
            layout.enabled = False

        if lc_exposure_check(self,context):
            layout.label(text="Settings need to be reapplied", icon='INFO')
            layout.operator("photographer.applyphotographersettings",
                text="Apply Photographer Settings",
                icon='FILE_REFRESH')

        col = layout.column(align=True)
        col.use_property_split = False
        row = col.row(align=True)
        row.alignment = "CENTER"
        row.scale_y = 1.5
        if not prop_panel:
        #     row.operator('exposure.picker', text = '', icon = 'EYEDROPPER').use_scene_camera = False
        # else:
            row.operator('exposure.picker', text='', icon = 'EYEDROPPER').use_scene_camera = True
        row.prop(settings, 'exposure_mode', expand=True)

        exposure_settings(self,context,settings,layout,guide,image_editor)

        if settings.exposure_mode != 'MANUAL':
            # Shutter Speed parameter
            row = layout.row(align = True)
            row.enabled = settings.motionblur_enabled
            if settings.shutter_mode == 'SPEED':
                if not settings.shutter_speed_slider_enable:
                    row.prop(settings, 'shutter_speed_preset', text='Shutter Speed')
                else:
                    row.prop(settings, 'shutter_speed', slider=True)
                row.operator("photographer.setshutterangle",icon="DRIVER_ROTATIONAL_DIFFERENCE", text="")
                row.prop(settings,'shutter_speed_slider_enable', icon='SETTINGS', text='')

            if settings.shutter_mode == 'ANGLE':
                if not settings.shutter_speed_slider_enable:
                    row.prop(settings, 'shutter_angle_preset', text='Shutter Angle')
                else:
                    row.prop(settings, 'shutter_angle', slider=True)
                row.operator("photographer.setshutterspeed",icon="PREVIEW_RANGE", text="")
                row.prop(settings,'shutter_speed_slider_enable', icon='SETTINGS', text='')

            # Aperture parameter
            row = layout.row(align = True)
            use_dof = settings.use_dof

            row.enabled = use_dof
            if prop_panel:
                if not settings.aperture_slider_enable:
                    row.prop(settings, 'aperture_preset', text='Aperture')
                else:
                    row.prop(settings, 'aperture', slider=True, text='Aperture F-stop / DOF only')
                row.prop(settings,'aperture_slider_enable', icon='SETTINGS', text='')

        col = layout.column(align=False)
        col.prop(settings, 'motionblur_enabled', text='Affect Motion Blur')

        # Check if the Motion Blur is enabled in the Render Settings
        if settings.motionblur_enabled and not scene.render.use_motion_blur:
            row = layout.row(align = True)
            row.label(icon= 'ERROR', text="")
            row.operator("photographer.rendermotionblur", text="Enable Motion Blur")

        # Hide Affect Depth of Field in 3D View Panel
        if prop_panel:
            col.prop(settings, "use_dof", text='Affect Depth of Field')

        col.prop(settings, 'falsecolor_enabled')
        col.prop(scene.photographer, 'comp_exposure')
        if scene.photographer.comp_exposure:
            col.label(text="Exposure won't be visible in Viewport", icon='INFO')

        # if image_editor:
        #     if scene.photographer.comp_exposure:
        #         col.operator("photographer.disable_exposure_node")
        #     else:
        #         col.operator("photographer.add_exposure_node")

        # EV Guide for ViewPanel
        if guide:
            row = layout.row()
            row.alignment = 'RIGHT'
            ev = calc_exposure_value(self, context, settings)
            ev_guide = update_exposure_guide(self, context, ev)
            row.label(text = "EV Guide: " + ev_guide )

        # FPS / Shutter Angle info
        row = layout.row()
        row.alignment = 'RIGHT'
        fps = scene.render.fps/scene.render.fps_base
        framerate_guide = "FPS : " + str(round(fps,2))
        if settings.shutter_mode == 'ANGLE':
            shutter_speed_guide = " - " + "Shutter Speed : 1/" + str(int(shutter_angle_to_speed(self,context,settings))) + "s"
            framerate_guide += shutter_speed_guide
        if settings.shutter_mode == 'SPEED':
            shutter_angle_guide = " - " + "Shutter Angle : " + str(round(shutter_speed_to_angle(self,context,settings),1))
            framerate_guide += shutter_angle_guide
        row.label(text = framerate_guide)

        # Light Sampling Threshold warning
        col = layout.column(align=True)
        row = col.row()
        row.alignment = 'RIGHT'
        if context.scene.render.engine in {'CYCLES','BLENDER_EEVEE'}:
            alt = bpy.context.preferences.addons[__package__].preferences.auto_light_threshold
            hltw = bpy.context.preferences.addons[__package__].preferences.hide_light_threshold_warning
            if not alt and settings.exposure_mode != 'AUTO':
                if settings.light_threshold_warning and not hltw:
                    row.label(text="Potential Sampling issue", icon='INFO')
                    col.operator("photographer.updatelightthreshold", text='Update Light Threshold')


class PHOTOGRAPHER_PT_Panel_Exposure(bpy.types.Panel):
    bl_label = 'Exposure'
    bl_parent_id = 'PHOTOGRAPHER_PT_Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw_header_preset(self, context):
        settings = context.camera.photographer
        exposure_header_preset(self,context,settings, True)
        camera_presets.PHOTOGRAPHER_PT_ExposurePresets.draw_panel_header(self.layout)

    def draw_header(self, context):
        settings = context.camera.photographer
        exposure_header(self,context,settings)

    def draw(self, context):
        settings = context.camera.photographer
        prop_panel = True
        guide = False
        image_editor = False
        exposure_panel(self,context,settings,prop_panel,guide, image_editor)


class PHOTOGRAPHER_PT_ViewPanel_Exposure(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'Exposure'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 6

    @classmethod
    def poll(cls, context):
        return context.scene.camera and context.scene.camera.type == 'CAMERA'

    def draw_header_preset(self, context):
        settings = context.scene.camera.data.photographer
        exposure_header_preset(self,context,settings, False)
        camera_presets.PHOTOGRAPHER_PT_ExposurePresets.draw_panel_header(self.layout)

    def draw_header(self, context):
        settings = context.scene.camera.data.photographer
        exposure_header(self,context,settings)

    def draw(self, context):
        settings = context.scene.camera.data.photographer
        prop_panel = False
        guide = True
        image_editor = False
        exposure_panel(self,context,settings,prop_panel, guide, image_editor)

class PHOTOGRAPHER_PT_ImageEditor_Exposure(PHOTOGRAPHER_PT_ViewPanel_Exposure):
    bl_space_type = 'IMAGE_EDITOR'

    @classmethod
    def poll(cls, context):
        show_image_panels =  bpy.context.preferences.addons[__package__].preferences.show_image_panels
        return context.scene.camera and context.scene.camera.type == 'CAMERA' and show_image_panels

    def draw(self, context):
        settings = context.scene.camera.data.photographer
        prop_panel = False
        guide = True
        image_editor = True
        exposure_panel(self,context,settings,prop_panel, guide, image_editor)

class PHOTOGRAPHER_PT_NodeEditor_Exposure(PHOTOGRAPHER_PT_ViewPanel_Exposure):
    bl_space_type = 'NODE_EDITOR'

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        show_image_panels =  bpy.context.preferences.addons[__package__].preferences.show_image_panels
        return context.scene.camera and context.scene.camera.type == 'CAMERA' and show_image_panels and snode.tree_type == 'CompositorNodeTree'

    def draw(self, context):
        settings = context.scene.camera.data.photographer
        prop_panel = False
        guide = True
        image_editor = True
        exposure_panel(self,context,settings,prop_panel, guide, image_editor)

#### WHITE BALANCE PANELS ####

def whitebalance_header_preset(self, context,use_scene_camera,image_editor):
    layout = self.layout
    if context.scene.camera == bpy.data.objects.get('MasterCamera'):
        layout.enabled = False
    row = layout.row(align=True)
    row.alignment = 'RIGHT'
    row.scale_x = panel_value_size

    if use_scene_camera:
        settings = context.scene.camera.data.photographer
    else:
        settings = context.camera.photographer

    if not settings.wb_enabled :
        row.enabled = False

    if context.preferences.addons[__package__].preferences.show_compact_ui:
        row.prop(settings,'color_temperature', text="", slider=True)

    sub = layout.row(align=False)
    sub.scale_x = 1.27
    if image_editor:
        sub.scale_x = 0.45
        sub.prop(settings, "wb_color", text='')
    elif use_scene_camera:
        sub.operator("white_balance.picker", text='', icon='EYEDROPPER', emboss=False).use_scene_camera=use_scene_camera
    else:
        sub.operator("white_balance.reset", text='', icon='LOOP_BACK', emboss=False).use_scene_camera=use_scene_camera

def whitebalance_header(self, context):
    layout = self.layout
    if context.scene.camera == bpy.data.objects.get('MasterCamera'):
        layout.enabled = False
    layout.prop(context.scene.camera.data.photographer, "wb_enabled", text="")

def whitebalance_panel(self, context, settings):
    layout = self.layout
    scene = bpy.context.scene
    if context.scene.camera == bpy.data.objects.get('MasterCamera'):
        layout.enabled = False
    else:
        layout.enabled = context.scene.view_settings.use_curve_mapping
    layout.use_property_split = True
    layout.use_property_decorate = False  # No animation.

    row = layout.row(align=True)
    row.prop(settings, "color_temperature", slider=True, text='Temperature')
    row.prop(settings, "preview_color_temp", text='')

    row = layout.row(align=True)
    row.prop(settings, "tint", slider=True)
    row.prop(settings, "preview_color_tint", text='')


class PHOTOGRAPHER_PT_Panel_WhiteBalance(bpy.types.Panel):
    bl_label = "White Balance"
    bl_parent_id = "PHOTOGRAPHER_PT_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw_header_preset(self, context):
        whitebalance_header_preset(self,context,False,False)

    def draw_header(self, context):
        whitebalance_header(self,context)

    def draw(self, context):
        settings = context.camera.photographer
        whitebalance_panel(self,context,settings)

class PHOTOGRAPHER_PT_ViewPanel_WhiteBalance(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'White Balance'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 7

    @classmethod
    def poll(cls, context):
        return context.scene.camera and context.scene.camera.type == 'CAMERA'

    def draw_header_preset(self, context):
        whitebalance_header_preset(self,context,True,False)

    def draw_header(self, context):
        whitebalance_header(self,context)

    def draw(self, context):
        settings = context.scene.camera.data.photographer
        whitebalance_panel(self,context,settings)

class PHOTOGRAPHER_PT_ImageEditor_WhiteBalance(PHOTOGRAPHER_PT_ViewPanel_WhiteBalance):
    bl_space_type = 'IMAGE_EDITOR'

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        show_image_panels = bpy.context.preferences.addons[__package__].preferences.show_image_panels
        return context.scene.camera and context.scene.camera.type == 'CAMERA' and show_image_panels

    def draw_header_preset(self, context):
        whitebalance_header_preset(self,context,True,True)

class PHOTOGRAPHER_PT_NodeEditor_WhiteBalance(PHOTOGRAPHER_PT_ViewPanel_WhiteBalance):
    bl_space_type = 'NODE_EDITOR'

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        snode = context.space_data
        show_image_panels = bpy.context.preferences.addons[__package__].preferences.show_image_panels
        return context.scene.camera and context.scene.camera.type == 'CAMERA' and show_image_panels and snode.tree_type == 'CompositorNodeTree'

    def draw_header_preset(self, context):
        whitebalance_header_preset(self,context,True,True)

#### RESOLUTION PANELS ####

def resolution_header_preset(self, context, settings):
    layout = self.layout
    # layout.enabled = settings.resolution_enabled
    row = layout.row(align=True)
    row.alignment = 'RIGHT'
    # Resolution
    resolution_x = str(int(context.scene.render.resolution_x * context.scene.render.resolution_percentage/100))
    resolution_y = str(int(context.scene.render.resolution_y * context.scene.render.resolution_percentage/100))
    row.label(text = resolution_x + "x" + resolution_y)

def resolution_header(self, context, settings):
    self.layout.prop(settings, "resolution_enabled", text="")

def resolution_panel(self, context, settings, use_scene_camera):
    layout = self.layout

    layout.use_property_split = True
    layout.use_property_decorate = False  # No animation.
    layout.enabled = settings.resolution_enabled

    col = layout.column()
    col.alignment = 'RIGHT'

    col.prop(settings, 'resolution_mode')

    sub = col.column(align=True)

    if settings.resolution_mode == 'CUSTOM_RES':
        sub.prop(settings, "resolution_x", text='Resolution X')
        sub.prop(settings, "resolution_y", text='Y')
        sub.prop(context.scene.render, "resolution_percentage", text='%')
        col.row().prop(settings, 'resolution_rotation',expand=True)

    elif settings.resolution_mode == 'CUSTOM_RATIO':
        sub.prop(settings, "ratio_x", text='Ratio X')
        sub.prop(settings, "ratio_y", text='Y')
        sub.separator()
        sub.prop(settings, "resolution_x", text='Resolution X')
        sub.prop(context.scene.render, "resolution_percentage", text='%')
        col.row().prop(settings, 'resolution_rotation',expand=True)

    else:
        sub.prop(settings, "longedge")
        sub.prop(context.scene.render, "resolution_percentage", text='%')
        if not settings.resolution_mode == '11':
            col.row().prop(settings, 'resolution_rotation',expand=True)

class PHOTOGRAPHER_PT_Panel_Resolution(bpy.types.Panel):
    bl_label = "Resolution"
    bl_parent_id = "PHOTOGRAPHER_PT_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw_header_preset(self, context):
        settings = context.camera.photographer
        resolution_header_preset(self,context,settings)
        camera_presets.PHOTOGRAPHER_PT_ResolutionPresets.draw_panel_header(self.layout)

    def draw_header(self, context):
        settings = context.camera.photographer
        resolution_header(self,context,settings)

    def draw(self, context):
        settings = context.camera.photographer
        resolution_panel(self,context,settings,False)

class PHOTOGRAPHER_PT_ViewPanel_Resolution(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = 'Resolution'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 8

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'

    def draw_header_preset(self, context):
        settings = context.scene.camera.data.photographer
        if context.preferences.addons[__package__].preferences.show_compact_ui:
            resolution_header_preset(self,context,settings)
        camera_presets.PHOTOGRAPHER_PT_ResolutionPresets.draw_panel_header(self.layout)

    def draw_header(self, context):
        settings = context.scene.camera.data.photographer
        resolution_header(self,context,settings)

    def draw(self, context):
        settings = context.scene.camera.data.photographer
        resolution_panel(self,context,settings,True)

class PHOTOGRAPHER_PT_ImageEditor_Resolution(PHOTOGRAPHER_PT_ViewPanel_Resolution):
    bl_space_type = 'IMAGE_EDITOR'
    bl_parent_id = ""

    @classmethod
    def poll(cls, context):
        # Add Panel properties to cameras
        show_image_panels = bpy.context.preferences.addons[__package__].preferences.show_image_panels
        return context.scene.camera and context.scene.camera.type == 'CAMERA' and show_image_panels

class PHOTOGRAPHER_PT_NodeEditor_Resolution(PHOTOGRAPHER_PT_ViewPanel_Resolution):
    bl_space_type = 'NODE_EDITOR'
    bl_parent_id = ""

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        show_image_panels = bpy.context.preferences.addons[__package__].preferences.show_image_panels
        return context.scene.camera and context.scene.camera.type == 'CAMERA' and show_image_panels and snode.tree_type == 'CompositorNodeTree'


class PHOTOGRAPHER_PT_ViewPanel_Focus(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Focus"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 5

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'

    def draw_header_preset(self, context):
        cam = context.scene.camera.data
        prefs = context.preferences.addons[__package__].preferences
        layout = self.layout
        if context.scene.camera == bpy.data.objects.get('MasterCamera'):
            layout.enabled = False
        row = layout.row(align=False)
        row.alignment = 'RIGHT'

        if prefs.show_compact_ui:
            if prefs.focus_eyedropper_func != 'BL_PICKER':
                row.scale_x = panel_value_size
                if cam.dof.focus_object is None:
                    row.prop(cam.dof, 'focus_distance',text="")
                else:
                    row.scale_x = 1
                    row.label(text="Tracking")

        sub = layout.row(align=False)
        sub.scale_x = 1.26
        if prefs.focus_eyedropper_func == 'AFS':
            sub.operator("photographer.focus_single", text="", icon='EYEDROPPER',emboss=False)
        elif prefs.focus_eyedropper_func == 'AFT':
            sub.operator("photographer.focus_tracking", text="", icon='EYEDROPPER',emboss=False)
        elif prefs.focus_eyedropper_func == 'BL_PICKER':
            row.scale_x = panel_value_size + 0.1
            row.prop(cam.dof, 'focus_object', text="")

    def draw(self, context):
        cam = context.scene.camera.data
        prefs = context.preferences.addons[__package__].preferences
        settings = cam.photographer
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        if not prefs.show_compact_ui:
            layout.prop(cam.dof, 'focus_distance')

        if prefs.focus_eyedropper_func == 'BL_PICKER':
            row = layout.row()
            row.prop(cam.dof, 'focus_distance')
            if cam.dof.focus_object is not None:
                row.enabled = False

        # Focus Plane
        cam_name = context.scene.camera.name
        col = layout.column(align=True)
        col.use_property_decorate = False
        if settings.show_focus_plane:
            col.operator("photographer.delete_focus_plane", text="Hide Focus Plane", icon='CANCEL').camera=cam_name
        else:
            col.operator("photographer.create_focus_plane", text="Show Focus Plane", icon='NORMALS_FACE').camera=cam_name
        col_fp = col.column(align=True)
        col_fp.prop(settings, "focus_plane_color")
        col_fp.prop(settings,"dof_limits")
        col_fp.enabled = settings.show_focus_plane

        col = layout.column()
        col.alignment = 'RIGHT'
        col.label(text='Hyperfocal Distance: '+ str(dof_hyperfocal(cam)))


class PHOTOGRAPHER_PT_ViewPanel_Autofocus(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Autofocus"
    bl_parent_id = "PHOTOGRAPHER_PT_ViewPanel_Focus"

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA'

    def draw(self, context):
        cam = context.scene.camera.data
        settings = cam.photographer
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column(align=True)
        # col.enabled = False

        if context.scene.camera:
            if context.scene.camera.type == 'CAMERA':
                if cam.dof.focus_object is None:
                    icon_afs = 'EYEDROPPER'
                    if settings.af_animate:
                        icon_afs = 'KEYTYPE_KEYFRAME_VEC'
                    col.operator("photographer.focus_single", text="AF-S", icon=icon_afs)
                    col.operator("photographer.focus_tracking", text="AF-Track", icon='OBJECT_DATA')

                    col_afc = layout.column(align=True)
                    col_afc.enabled = False
                    icon_afc = 'HOLDOUT_ON'
                    if settings.af_animate:
                        icon_afc = 'KEYTYPE_KEYFRAME_VEC'
                    col_afc.prop(settings, "af_continuous_enabled", text="Enable AF-C", icon=icon_afc)
                    col_afc_int = col_afc.column(align=True)
                    col_afc_int.enabled = settings.af_continuous_enabled
                    col_afc_int.prop(settings, "af_continuous_interval", slider=True)

                    col = layout.column(align=True)
                    col.prop(settings, "af_animate", text="Animate AF", icon="KEY_HLT" )

                    # Disable AF-C button if not looking through scene camera
                    for area in bpy.context.screen.areas:
                        if area.type == 'VIEW_3D':
                            if area.spaces[0].region_3d.view_perspective == 'CAMERA' :
                                if context.scene.camera:
                                    if context.scene.camera.type == 'CAMERA':
                                        col_afc.enabled = True
                else:
                    col2 = layout.column(align=True)
                    col2.operator("photographer.focus_tracking_cancel", text="Cancel AF Tracking", icon='OBJECT_DATA')

#### AUTOFOCUS PANELS ####
class PHOTOGRAPHER_PT_Panel_Autofocus(bpy.types.Panel):
    # bl_idname = "CAMERA_PT_Photographer_Autofocus"
    bl_label = "Continuous Autofocus"
    bl_parent_id = "PHOTOGRAPHER_PT_Panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        settings = context.camera.photographer
        self.layout.prop(settings, "af_continuous_enabled", text="")

    def draw(self, context):
        settings = context.camera.photographer
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column(align=True)
        col.prop(settings, "af_continuous_interval", slider=True)

class PHOTOGRAPHER_OT_ChangeLuxCoreDevice(bpy.types.Operator):
    bl_idname = "photographer.changelcdevice"
    bl_label = "Set LuxCore device to GPU"
    bl_description = "Auto Exposure requires using GPU device"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        engine = context.scene.render.engine
        if engine == 'LUXCORE':
            lc_device = context.scene.luxcore.config.device
            if lc_device == 'CPU':
                context.scene.luxcore.config.device = 'OCL'
            return{'FINISHED'}


class PHOTOGRAPHER_OT_EEVEE_DisableSoftShadows(bpy.types.Operator):
    bl_idname = "photographer.disablesoftshadows"
    bl_label = "Disable Soft Shadows"
    bl_description = "Click to disable EEVEE Soft Shadows that may lock Auto Exposure into an infinite update loop"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        engine = context.scene.render.engine
        if engine == 'BLENDER_EEVEE':
            usf = context.scene.eevee.use_soft_shadows
            if usf:
                context.scene.eevee.use_soft_shadows = False
        return{'FINISHED'}
