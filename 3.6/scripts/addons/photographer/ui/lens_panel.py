import bpy, math
from bpy.types import Panel
from .. import camera_presets
from ..constants import panel_value_size, addon_name

def crop_factor(camera):
    fullframe_diagonal = 43.27
    if camera.photographer.fit_inside_sensor:
        camera_diagonal = math.sqrt(math.pow(camera.sensor_height,2)+math.pow(camera.sensor_width,2))
    else:
        if camera.sensor_height > camera.sensor_width:
            ratio = 2/3
        else:
            ratio = 3/2       
        camera_diagonal = math.sqrt(math.pow(camera.sensor_width,2)+math.pow(camera.sensor_width/ratio,2))
    crop_factor = round(fullframe_diagonal/(camera_diagonal),2)
    equivalent = round(camera.lens * crop_factor)
    return "Crop Factor: " + str(crop_factor) + ", " + str(equivalent) + " mm equivalent."

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
    row = col.row()
    row.alignment = 'RIGHT'
    row.label(text=crop_factor(context.camera))

#### CAMERA SETTINGS PANEL ####
class PHOTOGRAPHER_PT_ViewPanel_Lens(Panel):
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
        if context.scene.camera == bpy.data.objects.get('DroneCamera'):
            layout.enabled = False
        if context.preferences.addons[addon_name].preferences.show_compact_ui:
            row = layout.row(align=False)
            row.alignment = 'RIGHT'
            row.scale_x = panel_value_size

            cam = context.scene.camera.data
            settings = cam.photographer

            if cam.type == 'ORTHO':
                row.prop(cam, 'ortho_scale',text="")
            else:
                if context.scene.render.engine == 'CYCLES':
                    if settings.fisheye or (cam.type == 'PANO' and cam.cycles.panorama_type == 'FISHEYE_EQUISOLID'):
                        row.prop(settings,'fisheye_focal', text="")
                    else:
                        row.prop(settings, 'focal',text="")
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

        main_col = layout.column(align=True)
        if context.scene.camera == bpy.data.objects.get('DroneCamera'):
            main_col.enabled = False

        # Focal Length and Fisheye
        col = main_col.column(align=True)
        if not context.preferences.addons[addon_name].preferences.show_compact_ui:
            if cam.type == 'ORTHO':
                col.prop(cam, 'ortho_scale')
            else:
                if context.scene.render.engine == 'CYCLES' and settings.fisheye:
                    col.prop(settings,'fisheye_focal', text='Focal Length')
                else:
                    col.prop(settings, 'focal')

        row=col.row()
        row.prop(cam, "type")
        if context.scene.render.engine == 'CYCLES' and settings.fisheye:
            row.enabled = False
        if context.scene.render.engine == 'CYCLES':
            col.prop(settings, 'fisheye')
        if context.scene.render.engine == 'CYCLES' and settings.fisheye:
            col.prop(cam.cycles,'fisheye_fov')
            col.separator()

        # col.prop(settings, 'breathing')
        col = main_col.column(align=True)
        col.use_property_split = True

        row = col.row(align=True)
        row.prop(settings,'lens_shift', slider=True)
        row.operator('photographer.auto_lens_shift', text='', icon='EVENT_A').camera=cam_name
        row = col.row(align=True)
        row.prop(settings,'lens_shift_x', slider=True)
        col.prop(settings,'lens_shift_compensated')
        row = col.row()
        row.alignment = 'RIGHT'
        row.label(text=crop_factor(cam))

        if context.scene.render.engine == 'CYCLES':
            col.enabled = not settings.fisheye

        # Dolly Zoom
        col.separator()
        col.operator('photographer.dollyzoom', icon='VIEW_ZOOM')
        col.operator('photographer.dollyzoom_set_key', icon='KEY_HLT')

