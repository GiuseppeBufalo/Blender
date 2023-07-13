import bpy
import os
import rna_keymap_ui

from bpy.props import (BoolProperty,
                       FloatProperty,
                       EnumProperty,
                       FloatVectorProperty,
                       StringProperty,
                       )
from . import camera_sensors
from .constants import addon_name, photographer_presets_folder
from .ui import panel_classes
from .operators.sampling_threshold import update_light_threshold
from .properties.light import(INTENSITY_DESCRIPTION,
                    EXPOSURE_DESCRIPTION,
                    POWER_DESCRIPTION,
                    EFFICACY_DESCRIPTION,
                    LUMEN_DESCRIPTION,
                    CANDELA_DESCRIPTION,
                    NORMALIZEBYCOLOR_DESCRIPTION,
                    PER_SQUARE_METER_DESCRIPTION,
                    )
from .ui.library import hdri_lib_path_update
from .operators.updater import changelog,latest_msg

SHOW_DEFAULT_LIGHT_PANELS_DESC = ( "In case a Blender updates adds new Light features and Photographer is not updated,"
            "these features might not be visible in the Physical Light panel.\n"
            "This option allows you to show both panels at the same time"
)

SUN_SKY_GAIN_DESC = (
    "Brightness multiplier. Set to 1 for physically correct sun/sky brightness, "
    "if you also use physically based tonemapper and light settings"
)

addon_keymaps = []

def get_hotkey_entry_item(km, kmi_name, kmi_value):
    '''
    returns hotkey of specific type, with specific properties.name (keymap is not a dict, so referencing by keys is not enough
    if there are multiple hotkeys!)
    '''
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if km.keymap_items[i].properties.name == kmi_value:
                return km_item
    return None

def add_hotkey(keymap,space,region,identifier,property,event_type,value,ctrl=False,shift=False,alt=False):
    addon_prefs = bpy.context.preferences.addons[addon_name].preferences

    if bpy.context.window_manager:
        wm = bpy.context.window_manager
        if wm.keyconfigs.addon:
            kc = wm.keyconfigs.addon
            km = kc.keymaps.new(name=keymap, space_type=space, region_type=region)
            kmi = km.keymap_items.new(identifier,event_type,value, shift=shift, ctrl=ctrl, alt=alt)
            kmi.properties.name = property
            kmi.active = True
            addon_keymaps.append((km, kmi))


class PHOTOGRAPHER_OT_Hotkey_Add_Pie_Camera(bpy.types.Operator):
    '''Add hotkey to Photographer's Camera Pie menu'''
    bl_idname = "photographer.hotkey_add_pie_camera"
    bl_label = "Camera Pie hotkey"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        add_hotkey("3D View",'VIEW_3D','WINDOW',
            "wm.call_menu_pie","PHOTOGRAPHER_MT_Pie_Camera",
            'C', 'PRESS', shift=True, ctrl=True)

        self.report({'INFO'}, "Hotkey added in User Preferences -> Keymap -> 3D View -> 3D View (Global)")
        return {'FINISHED'}


def remove_hotkey(keymap):
    ''' clears all addon level keymap hotkeys stored in addon_keymaps '''

    if bpy.context.window_manager:
        wm = bpy.context.window_manager
        if wm.keyconfigs.addon:
            kc = wm.keyconfigs.addon
            if kc.keymaps.get(keymap, False):
                km = kc.keymaps[keymap]

                for km, kmi in addon_keymaps:
                    km.keymap_items.remove(kmi)
                    wm.keyconfigs.addon.keymaps.remove(km)
                addon_keymaps.clear()


def update_photographer_category(self,context):
    for cls in panel_classes.photographer_panel_classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
        cls.bl_category = self.category
        bpy.utils.register_class(cls)

def update_lightmixer_category(self,context):
    for cls in panel_classes.lightmixer_panel_classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
        cls.bl_category = self.lightmixer_category
        bpy.utils.register_class(cls)

def update_exposure(self,context):
    photographer = context.scene.camera.data.photographer
    from . import camera
    if photographer.exposure_enabled:
        camera.update_ev(photographer,context)

def update_all_lights_energy(self,context):
    from .properties import light
    if self.use_physical_lights:
        lights = [o for o in bpy.data.objects if o.type == 'LIGHT']
        for l in lights:
            photographer = l.data.photographer
            light.update_energy(photographer)

# def update_cam_list_sorting(self,context):
#     context.scene.photographer.cam_list_sorting = self.default_cam_list_sorting

# def update_default_rq_incremental(self,context):
#     print (bpy.data.scenes)
#     for scene in bpy.data.scenes:
#         scene.renderqueue.incremental = self.default_rq_incremental


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_name

    category : StringProperty(
        description=("Choose a name for the category of the Photographer panel. \n"
        "You can write the name of an existing panel"),
        default="Photographer",
        update=update_photographer_category
    )

    lightmixer_category : StringProperty(
        description=("Choose a name for the category of the Lightmixer panel. \n"
        "You can write the name of an existing panel"),
        default="Photographer",
        update=update_lightmixer_category
    )

    # use_short_labels : BoolProperty(
    #     name = "Use Short names for Panels",
    #     description = "You can opt for shorter names if you want to keep your Add-on panel small",
    #     default = False
    # )
    show_compact_ui : BoolProperty(
        name = "Show Compact UI",
        description = "Adds most important settings into Panel names to keep the UI compact",
        default = True
    )

    needs_update : StringProperty()

    changelog_expanded : BoolProperty(
        default= False,
    )

    ui_tab : EnumProperty(
        name = "Preferences Tab",
        items = [('UI','UI', ''),
                ('LIBRARY','Library',''),
                ('CAMERA','Camera',''),
                ('EXPOSURE','Exposure',''),
                ('LIGHT','Light',''),
                ('RENDER','Render',''),
                ],
        default = 'UI',
    )
    exposure_mode_pref : EnumProperty(
        name = "Default Exposure Mode",
        description = "Choose the default Exposure Mode",
        items = [('EV','EV', ''),('AUTO','Auto',''),('MANUAL','Manual','')],
        default = 'EV',
    )

    shutter_speed_slider_pref : BoolProperty(
        name = "Shutter Speed / Angle",
        description = "Use Slider for Shutter Speed / Angle",
        default = False
    )

    aperture_slider_pref : BoolProperty(
        name = "Aperture",
        description = "Use Slider for Aperture",
        default = False
    )

    iso_slider_pref : BoolProperty(
        name = "ISO",
        description = "Use Slider for ISO setting",
        default = False
    )

    show_af_buttons_pref : BoolProperty(
        name = "Show Autofocus buttons in 3D View header",
        description = "AF buttons will still be available in the Add-on panel",
        default = True
    )

    show_cam_buttons_pref : BoolProperty(
        name = "Show 'Lock Camera to View' button in 3D View header",
        description = "'Lock Camera to View' will still be available in the Add-on panel",
        default = True
    )

    show_image_panels : BoolProperty(
        name = "Show Photographer panel in Image and Node editors",
        description = "Photographer will still be accessible in the 3D View panel",
        default = True
    )

    show_drone_camera : BoolProperty(
        name = "Show Drone Camera feature",
        description = "Uncheck if you don't plan to use the Drone Camera feature, for a cleaner UI",
        default = True
    )

    use_physical_lights : BoolProperty(
        name = "Use Physical lights",
        description = ("Replace Light properties with advanced Physical Light properties. \n"
        "It is recommend to disable this feature when using LuxCore, unless you plan to do comparisons with Cycles"),
        default = True,
    )

    follow_unit_scale : BoolProperty(
        name = "Follow Scene Unit Scale",
        description = "Multiplies lighting power according to the scene Unit Scale",
        default = True,
        update = update_all_lights_energy,
    )

    show_default_light_panels : BoolProperty(
        name = "Keep showing Blender Light panels",
        description = SHOW_DEFAULT_LIGHT_PANELS_DESC,
        default = False
    )

    aces_ue_match : BoolProperty(
        name = "Match Blender ACES to Unreal ACES",
        description = ("Unreal ACES tonemapper uses a 1.45 multiplier. "
        "Check this box to fix this discrepancy. \n"
        "This setting is only effective when using ACES in Blender"),
        default = True,
        update = update_exposure,
    )

    lens_attenuation : FloatProperty(
        name = "Lens Attenuation factor",
        description = ("Default value of 0.78 will cancel lens attenuation calculations"
        "and will match Unreal 4.25 camera exposure. \n"
        "ISO standard recommends a lens transmittance of 0.65, which is sometimes"
        " used by other render engines to match real cameras"),
        default = 0.78,
        min = 0.01,
        max = 1,
        precision = 3,
        update = update_exposure,
    )

    default_light_threshold : FloatProperty(
        name = "Default Light Threshold",
        description = "Defines the Light Sampling Threshold that will be multiplied by the Exposure Value",
        default = 0.01,
        min = 0,
        max = 1,
        precision = 5,
        update = update_light_threshold,
    )

    auto_light_threshold : BoolProperty(
        name = "Automatic Light Threshold",
        description = ("Exposure changes will update the Light Sampling threshold automatically. \n"
        "Note: Viewport render will refresh when changing the exposure when Auto is ON"),
        default = False,
    )

    hide_light_threshold_warning: BoolProperty(
        name = "Hide warning",
        description = ("Hides the warning that will appear in the Exposure Panel "
        "if the current Light Sampling threshold is too far from its optimal value"),
        default = False,
    )
    fit_inside_sensor : BoolProperty(
        name = "Fit inside Sensor",
        description = "Automatically adjusts the Camera Sensor fit in order to make the Resolution fit inside the sensor. \n"
        "This is a smarter Auto Fit than the one provided by Blender.\n"
        "FOV calculation will be more accurate when trying to match a photo.\n"
        "This setting defines the default value that will be used when creating a new camera",
        default = True,

    )
    default_sensor_type : EnumProperty(
        name = "Default Sensor Type", description = "Camera Sensor Size used when creating a new camera",
        items = camera_sensors.sensor_type_items,
        default = 8,
    )
    default_show_passepartout: BoolProperty(
        name = "Show Passepartout",
        description = "Show Passepartout value for newly created cameras",
        default = True,
    )
    default_passepartout_alpha: FloatProperty(
        name = "Passepartout Alpha",
        description = "Passepartout opacity for newly created cameras",
        default = 1.0, # Necessary for Viewport compositing
        min = 0,
        max = 1,
    )
    default_focus_plane_color : FloatVectorProperty(
        name="Default Focus Plane Color", description="Set Color and Alpha opacity of the Focus Plane debug",
        subtype='COLOR', min=0.0, max=1.0, size=4, default=(1,0,0,0.4),
        options = {'HIDDEN'},
    )
    frame_full_viewport: BoolProperty(
        name = "Full Viewport Framing",
        description = "Frame the full Viewport when adding a new Camera, instead of keeping the viewport overscan",
        default = True,
    )
    focus_eyedropper_func : EnumProperty(
        name = "Focus Eyedropper function",
        description = "Defines the function of the Focus Eyedropper in the Compact UI",
        items = [('AFS','AF-Single', ''),('AFT','AF-Track','photographer.focus_tracking'),('BL_PICKER','Blender Focus Picker','')],
        default = 'AFS',
    )
    # Composition Guides Default values
    show_composition_thirds: BoolProperty(
        name = "Show Thirds Composition Guide",
        description = "Displays Thirds composition guide for newly created cameras",
        default = False,
    )
    show_composition_center: BoolProperty(
        name = "Show Center Composition Guide",
        description = "Displays Center composition guide for newly created cameras",
        default = False,
    )
    show_composition_center_diagonal: BoolProperty(
        name = "Show Diagonal Composition Guide",
        description = "Displays Diagonal composition guide for newly created cameras",
        default = False,
    )
    show_composition_golden: BoolProperty(
        name = "Show Golden Ratio Composition Guide",
        description = "Displays Golden Ratio composition guide for newly created cameras",
        default = False,
    )
    show_composition_golden_tria_a: BoolProperty(
        name = "Show Golden Ratio Triangle A Composition Guide",
        description = "Displays Golden Ratio Triangle A composition guide for newly created cameras",
        default = False,
    )
    show_composition_golden_tria_b: BoolProperty(
        name = "Show Golden Ratio Triangle B Composition Guide",
        description = "Displays Golden Ratio Triangle B composition guide for newly created cameras",
        default = False,
    )
    show_composition_harmony_tri_a: BoolProperty(
        name = "Show Harmony Ratio Triangle A Composition Guide",
        description = "Displays Harmony Ratio Triangle A composition guide for newly created cameras",
        default = False,
    )
    show_composition_harmony_tri_b: BoolProperty(
        name = "Show Harmony Ratio Triangle B Composition Guide",
        description = "Displays Harmony Ratio Triangle B composition guide for newly created cameras",
        default = False,
    )
    # default_rq_incremental: bpy.props.BoolProperty(
    #     name = "Default Incremental",
    #     description = "Incremental default value for the Render Queue"
    #                 "Adds number suffix and increments for each re-render",
    #     default = True,
    #     update = update_default_rq_incremental,
    # )

    sunlight_units = [
        ("artistic", "Artistic", "Artist friendly unit using Gain and Exposure",0),
        ("irradiance", "Irradiance (W/m2)", "Irradiance in Watt per square meter",1),
        ("illuminance", "Illuminance (Lux)", "Illuminance in Lux",2),
    ]

    default_sunlight_unit: EnumProperty(
        name="Default Sunlight Unit",
        items=sunlight_units,
        default='irradiance',
    )

    default_irradiance: FloatProperty(
        name="Irradiance W/m2", #description=light.IRRADIANCE_DESCRIPTION,
        default=1, min=0, precision=3,
    )

    default_illuminance: FloatProperty(
        name="Lux", #description=light.ILLUMINANCE_DESCRIPTION,
        default=110000, min=0, precision=2,
    )

    light_units = [
        ("artistic", "Artistic", "Artist friendly unit using Gain and Exposure",0),
        ("power", "Power", "Radiant flux in Watt",1),
        ("lumen", "Lumen", "Luminous flux in Lumen",2),
        ("candela", "Candela", "Luminous intensity in Candela",3),
        ("advanced_power", "Power (Advanced)", "Radiant flux in Watt",4),
    ]

    default_light_unit: EnumProperty(
        name="Default Light Unit",
        items=light_units,
        default='power',
    )

    default_intensity: FloatProperty(
        name="Intensity", description=INTENSITY_DESCRIPTION,
        default=10, soft_min=0,
    )

    default_light_exposure: FloatProperty(
        name="Exposure", description=EXPOSURE_DESCRIPTION,
        default=0, soft_min=-10, soft_max=10, precision=2,
    )

    default_power: FloatProperty(
        name="Power", description=POWER_DESCRIPTION,
        default=10, soft_min=0, precision=5, unit='POWER',
    )

    default_advanced_power: FloatProperty(
        name="Power (Advanced)", description=POWER_DESCRIPTION,
        default=10, soft_min=0, precision=4, unit='POWER',
    )

    default_efficacy: FloatProperty(
        name="Efficacy (lm/W)", description=EFFICACY_DESCRIPTION,
        default=683, min=0,
    )

    default_lumen: FloatProperty(
        name="Lumen", description=LUMEN_DESCRIPTION,
        default=683, soft_min=0, precision=2,
    )

    default_candela: FloatProperty(
        name="Candela", description=CANDELA_DESCRIPTION,
        default=543.514, soft_min=0, precision=3,
    )

    default_normalizebycolor: BoolProperty(
        name="Normalize by Color Luminance",
        description=NORMALIZEBYCOLOR_DESCRIPTION,
        default=True,
    )
    default_per_square_meter: BoolProperty(
        name="Per square meter",
        description=PER_SQUARE_METER_DESCRIPTION,
        default=False,
    )

    # EEVEE Light settings
    default_use_custom_distance: BoolProperty(
        name="Custom Distance",
        default=True,
    )
    default_cutoff_distance: FloatProperty(
        name="Distance",
        default=40,
        unit='LENGTH',
    )
    default_shadow_buffer_bias: FloatProperty(
        name="Shadow Bias",
        default=0.01,
    )
    default_use_contact_shadow: BoolProperty(
        name="Contact Shadows",
        default=False,
    )
    default_contact_shadow_distance: FloatProperty(
        name="Distance",
        default=0.2,
        unit='LENGTH',
    )
    default_contact_shadow_bias: FloatProperty(
        name="Contact Shadows Bias",
        default=0.03,
    )
    default_contact_shadow_thickness: FloatProperty(
        name="Contact Shadows Thickness",
        default=0.2,
    )
    lc_light_types = [
        ("sun", "Sun", "Physically correct sun that emits parallel light rays and changes color with elevation", 0),
        ("distant", "Distant", "Distant star without atmosphere simulation (emits parallel light)", 1),
        ("hemi", "Hemi", "180 degree constant light source", 2),
    ]
    default_lc_light_type: EnumProperty(
    name="Sun Type",
    items=lc_light_types,
    default="sun"
    )
    lc_light_units = [
        ("artistic", "Artistic", "Artist friendly unit using Gain and Exposure",0),
        ("power", "Power", "Radiant flux in Watt",1),
        ("lumen", "Lumen", "Luminous flux in Lumen",2),
        ("candela", "Candela", "Luminous intensity in Candela",3),
    ]

    default_lc_light_unit: EnumProperty(
        name="Default Light Unit",
        items=lc_light_units,
        default='power',
    )

    default_sun_sky_gain: FloatProperty(
        name="Sun Gain",
        default=0.00002,
        description=SUN_SKY_GAIN_DESC,
    )
    default_gain: FloatProperty(
        name="Gain",
        default=1,
    )
    opt_vignetting_lib_path: StringProperty(
        name="Optical Vignetting Library Path",
        default= os.path.join(os.path.join(photographer_presets_folder,'optical_vignetting'),''),
        description=("Folder where you store your Optical Vignetting textures for Depth of Field. \n"
                    "Default will use Scripts/Presets/photographer/optical_vignetting"),
        subtype="DIR_PATH",
    )
    bokeh_lib_path: StringProperty(
        name="Bokeh Library Path",
        default= os.path.join(os.path.join(photographer_presets_folder,'bokeh'),''),
        description=("Folder where you store your Bokeh textures for Depth of Field. \n"
                    "Default will use Scripts/Presets/photographer/bokeh"),
        subtype="DIR_PATH",
    )
    gobo_lib_path: StringProperty(
        name="Light Gobo Library Path",
        default= os.path.join(os.path.join(photographer_presets_folder,'light_gobos'),''),
        description=("Folder where you store your Light Gobo textures. \n"
                    "Default will use Scripts/Presets/photographer/light_gobos"),
        subtype="DIR_PATH",
    )
    ies_lib_path: StringProperty(
        name="Light Gobo Library Path",
        default= os.path.join(os.path.join(photographer_presets_folder,'ies_profiles'),''),
        description=("Folder where you store your IES Profiles. \n"
                    "Default will use Scripts/Presets/photographer/ies_profiles"),
        subtype="DIR_PATH",
    )
    stmap_lib_path: StringProperty(
        name="Distortion STMap Library Path",
        default= os.path.join(os.path.join(photographer_presets_folder,'stmaps'),''),
        description=("Folder where you store your STMap textures for camera distortion. \n"
                    "Default will use Scripts/Presets/photographer/stmaps"),
        subtype="DIR_PATH",
    )
    film_grain_lib_path: StringProperty(
        name="Film Grain textures Library Path",
        default= os.path.join(os.path.join(photographer_presets_folder,'film_grain'),''),
        description=("Folder where you store your Film Grain textures. \n"
                    "Default will use Scripts/Presets/photographer/film_grain"),
        subtype="DIR_PATH",
    )
    hdri_lib_path: StringProperty(
        name="HDRI Library Path",
        default= '',
        description="Folder where you store your HDRI images for the World Environment",
        subtype="DIR_PATH",
        update=hdri_lib_path_update,
    )
    hdri_auto_world_rename: BoolProperty(
        name="Automatically rename World with HDRI texture name",
        description="Automatically rename the World data with the name of the HDRI it is using",
        default=True,
    )
    # Does not work as expected
    # lightmixer_min_rows: IntProperty(
    #     name="Lightmixer Minimum amount of Rows",
    #     description="Minimum number of rows to display in the Lightmixer Light list",
    #     default=2,
    #     min=3, max=40,
    # )
    # lightmixer_coll_min_rows: IntProperty(
    #     name="Lightmixer Minimum amount of Rows",
    #     description="Minimum number of rows to display in the Lightmixer Light list",
    #     default=15,
    #     min=3, max=40,
    # )
    
    # Widget prefix
    widget_prefix: StringProperty(
        name="Camera Widget prefix",
        description="Prefix for the widget objects",
        default="WGT-",
    )

    # Collection name
    camera_widget_collection_name: StringProperty(
        name="Bone Widget collection name",
        description="Name for the collection the widgets will appear",
        default="Widgets",
    )


    def draw(self, context):
            layout = self.layout
            wm = bpy.context.window_manager

            box = layout.box()
            split = box.split(factor = 0.45)
            row = split.row()
            row.operator("photographer.check_for_update")
            row = split.row(align=True)
            row.operator("wm.url_open", text="Gumroad").url = "https://gumroad.com/library"
            # row.operator("wm.url_open", text="Blender Market").url = "https://blendermarket.com/account/orders"

            # Update Check
            if self.needs_update and self.needs_update != latest_msg:
                row = box.row()
                row.alert = True
                row.label(text=self.needs_update)

                row = box.row()
                row.prop(self, "changelog_expanded",
                    icon="TRIA_DOWN" if self.changelog_expanded else "TRIA_RIGHT",
                    icon_only=True, emboss=False
                )
                row.label(text='Changelog')
                if self.changelog_expanded:
                    for v in changelog:
                        version_box = box.box()
                        row = version_box.row()
                        row.scale_y = 0.6
                        row.label(text=v[0]+":")

                        split_str = v[1].splitlines()
                        for str in split_str:
                            row = version_box.row()
                            row.scale_y = 0.5
                            row.label(text=str)
            elif self.needs_update == latest_msg:
                row = box.row()
                row.label(text=latest_msg)
            else:
                row = box.row()
                row.label(text="Press 'Check for Updates' to verify if you are "
                        "running the latest version of the add-on.")

            percentage_columns = 0.35
            row = layout.row(align=True)
            row.prop(self, "ui_tab", expand=True)

            box = layout.box()
            if self.ui_tab == 'UI':
                # UI options
                row = box.row(align=True)
                row.label(text="Panel Category:")
                row.prop(self, "category", text="")
                row = box.row(align=True)
                row.label(text="Light Mixer Panel Category:")
                row.prop(self, "lightmixer_category", text="")
                box.prop(self, 'show_compact_ui')
                box.prop(self, 'show_image_panels')
                box.prop(self, 'show_af_buttons_pref')
                box.prop(self, 'show_cam_buttons_pref')
                box.prop(self, 'show_drone_camera')
                # Pie menu Hotkey
                box = layout.box()
                box.label(text="Hotkeys:")
                wm = bpy.context.window_manager
                kc = wm.keyconfigs.user
                km = kc.keymaps['3D View']
                kmi = get_hotkey_entry_item(km, 'wm.call_menu_pie', 'PHOTOGRAPHER_MT_Pie_Camera')
                if kmi:
                    box.context_pointer_set("keymap", km)
                    rna_keymap_ui.draw_kmi([], kc, km, kmi, box, 0)
                else:
                    box.operator('photographer.hotkey_add_pie_camera', text = "Add Camera Pie hotkey")

            elif self.ui_tab == 'LIBRARY':
                # Library Paths
                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "World HDRI folder:")
                split.prop(self, 'hdri_lib_path', text = '')

                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "Optical Vignetting folder:")
                split.prop(self, 'opt_vignetting_lib_path', text = '')

                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "Bokeh folder :")
                split.prop(self, 'bokeh_lib_path', text = '')
               
                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "Light Gobo folder :")
                split.prop(self, 'gobo_lib_path', text = '')

                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "IES Profiles folder :")
                split.prop(self, 'ies_lib_path', text = '')

                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "STMaps folder:")
                split.prop(self, 'stmap_lib_path', text = '')

                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "Film Grain folder:")
                split.prop(self, 'film_grain_lib_path', text = '')

            elif self.ui_tab == 'CAMERA':
                # # Camera List Sorting
                # row = box.row(align=True)
                # split = row.split(factor=percentage_columns)
                # split.label(text="Default Camera List Sorting :")
                # row = split.row(align=True)
                # row.prop(self, 'default_cam_list_sorting', expand=True)

                # Camera Viewport Display options
                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Focus Eyedropper :")
                split.prop(self, 'focus_eyedropper_func', text = '')

                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Full Viewport Framing :")
                split.prop(self, 'frame_full_viewport', text = '')

                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Fit inside Sensor :")
                split.prop(self, 'fit_inside_sensor', text = '')

                box = layout.box()
                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Default Sensor Type :")
                split.prop(self, 'default_sensor_type', text = '')

                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Default Passepartout :")
                row = split.row(align=True)
                row.prop(self, 'default_show_passepartout')
                row.prop(self, 'default_passepartout_alpha', text = '')

                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Default Focus Plane Color :")
                split.prop(self, 'default_focus_plane_color', text = '')

                col = box.column(align=True)
                col.label(text= "Default Composition Guides :")
                row = col.row(align=True)
                split = row.split(factor = 1/4 )
                split.label(text="Thirds / Center :")
                split.prop(self, "show_composition_thirds", text="Thirds")
                split.prop(self, "show_composition_center", text="Center")
                split.prop(self, "show_composition_center_diagonal", text="Diagonal")

                row = col.row(align=True)
                split = row.split(factor = 1/4 )
                split.label(text="Golden :")
                split.prop(self, "show_composition_golden", text="Ratio")
                split.prop(self, "show_composition_golden_tria_a", text="Triangle A")
                split.prop(self, "show_composition_golden_tria_b", text="Triangle B")

                row = col.row(align=True)
                split = row.split(factor = 1/4 )
                split.label(text="Harmony :")
                split.prop(self, "show_composition_harmony_tri_a", text="Triangle A")
                split.prop(self, "show_composition_harmony_tri_b", text="Triangle B")
                split.separator()

                box = layout.box()
                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Camera Rig Widget Prefix :")
                split.prop(self, 'widget_prefix', text = '')

                row = box.row(align=True)
                split = row.split(factor=percentage_columns)
                split.label(text="Camera Rig Collection name :")
                split.prop(self, 'camera_widget_collection_name', text = '')

            elif self.ui_tab == 'EXPOSURE':
                # Default Exposure mode
                split = box.split(factor=percentage_columns)
                split.label(text = "Default Exposure Mode :" )
                row = split.row(align=True)
                row.prop(self, 'exposure_mode_pref', expand=True)

                # Use camera values presets or sliders
                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "Use Sliders instead of Presets:")
                col2 = split.column()
                row = col2.row()
                row.prop(self, 'shutter_speed_slider_pref')
                row.prop(self, 'aperture_slider_pref')
                row.prop(self, 'iso_slider_pref')

                box.prop(self,'lens_attenuation')
                box.prop(self, 'aces_ue_match')

            elif self.ui_tab == 'LIGHT':
            # Physical lights options
                row = box.row(align=True)
                box.prop(self, 'use_physical_lights',
                text='Use Physical Lights (supported by Cycles, EEVEE, Workbench and LuxCore)')
                col = box.column(align=True)
                if self.use_physical_lights:
                    col.enabled = True
                else:
                    col.enabled = False
                col.prop(self, 'follow_unit_scale')
                col.prop(self, 'show_default_light_panels')
                col.separator()
                box.prop(self, 'hdri_auto_world_rename')
                # Doesn't work as expected
                # box.prop(self, 'lightmixer_min_rows')
                # box.prop(self, 'lightmixer_coll_min_rows')

                box = layout.box()
                col = box.column(align=True)

                # Sunlight settings
                if self.use_physical_lights:
                    split = col.split(factor=0.35)
                    split.label(text='Default Sunlight Unit:')
                    split.prop(self,"default_sunlight_unit", text='')
                    split = col.split(factor=0.35)
                    split.label(text='')
                    if self.default_sunlight_unit == 'irradiance':
                        split.prop(self,"default_irradiance")
                    elif self.default_sunlight_unit == 'illuminance':
                        split.prop(self,"default_illuminance")
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self, "default_normalizebycolor")
                    elif self.default_sunlight_unit == 'artistic':
                        split.prop(self,"default_intensity")
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self,"default_light_exposure")

                elif context.scene.render.engine == 'LUXCORE' and not self.use_physical_lights:
                    split = col.split(factor=0.35)
                    split.label(text='Default Sunlight Type:')
                    split.prop(self,"default_lc_light_type", text='')
                    split = col.split(factor=0.35)
                    split.label(text='')
                    if self.default_lc_light_type == 'sun':
                        split.prop(self,"default_sun_sky_gain")
                    else:
                        split.prop(self,"default_gain")
                    split.prop(self,"default_light_exposure")
                else:
                    split = col.split(factor=0.35)
                    split.label(text='Default Sunlight Intensity:')
                    split.prop(self,"default_irradiance", text = 'Strength')

                col.separator()

                # Other light types settings
                if self.use_physical_lights:
                    split = col.split(factor=0.35)
                    split.label(text='Default Light Unit:')
                    split.prop(self, "default_light_unit", text='')
                    split = col.split(factor=0.35)
                    split.label(text='')
                    if self.default_light_unit == 'artistic':
                        split.prop(self,"default_intensity")
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self,"default_light_exposure")

                    elif self.default_light_unit == 'power':
                        split.prop(self,"default_power")

                    elif self.default_light_unit == 'advanced_power':
                        split.prop(self,"default_advanced_power")
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self,"default_efficacy")

                    elif self.default_light_unit == 'lumen':
                        split.prop(self,"default_lumen")

                    elif self.default_light_unit == 'candela':
                        split.prop(self,"default_candela")

                    if self.default_light_unit in {'lumen','candela'}:
                        split.prop(self,"default_per_square_meter")
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self, "default_normalizebycolor")

                elif context.scene.render.engine == 'LUXCORE' and not self.use_physical_lights:
                    split = col.split(factor=0.35)
                    split.label(text='Default Light Unit:')
                    split.prop(self, "default_lc_light_unit", text='')
                    split = col.split(factor=0.35)
                    split.label(text='')
                    if self.default_lc_light_unit == 'artistic':
                        split.prop(self,"default_gain")
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self,"default_light_exposure")

                    elif self.default_lc_light_unit == 'power':
                        split.prop(self,"default_power")
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self,"default_efficacy")

                    elif self.default_lc_light_unit == 'lumen':
                        split.prop(self,"default_lumen")

                    elif self.default_lc_light_unit == 'candela':
                        split.prop(self,"default_candela")
                        split.prop(self,"default_per_square_meter")

                    if self.default_lc_light_unit in {'lumen','candela'}:
                        split = col.split(factor=0.35)
                        split.label(text='')
                        split.prop(self, "default_normalizebycolor")
                else:
                    split = col.split(factor=0.35)
                    split.label(text='Default Light Intensity:')
                    split.prop(self,"default_power")

                col.separator()
                col.separator()

                split = col.split(factor=0.35)
                split.label(text='Default EEVEE Light settings:')
                row = split.row(align=True)
                row.prop(self,"default_use_custom_distance")
                row.prop(self,"default_cutoff_distance")
                split = col.split(factor=0.35)
                split.label(text='')
                split.prop(self,"default_shadow_buffer_bias")

                col.separator()
                col.separator()

                split = col.split(factor=0.35)
                split.label(text='')
                row = split.row(align=True)
                row.prop(self,"default_use_contact_shadow")
                sub = row.row(align=True)
                sub.enabled = self.default_use_contact_shadow
                sub.prop(self,"default_contact_shadow_distance")
                split = col.split(factor=0.35)
                split.label(text='')
                split.enabled = self.default_use_contact_shadow
                split.prop(self,"default_contact_shadow_bias")
                split = col.split(factor=0.35)
                split.label(text='')
                split.enabled = self.default_use_contact_shadow
                split.prop(self,"default_contact_shadow_thickness")

            elif self.ui_tab == 'RENDER':
                # Render options
                row = box.row(align=True)
                split = row.split(factor = percentage_columns)
                split.label(text = "Light Sampling Threshold :")
                split.prop(self, 'default_light_threshold', text = '')
                split.prop(self, 'auto_light_threshold', text = 'Auto update')
                split.prop(self, 'hide_light_threshold_warning')

                # row = box.row(align=True)
                # split = row.split(factor = percentage_columns)
                # split.label(text = "Render Queue Incremental :")
                # split.prop(self, 'default_rq_incremental', text = '')

            # Useful links
            box = layout.box()
            row = box.row(align=True)
            row.label(text='Useful links : ')
            row.operator("wm.url_open", text="Documentation").url = "https://sites.google.com/view/photographer-5-documentation"
            row.operator("wm.url_open", text="Video Tutorials").url = "https://www.youtube.com/playlist?list=PLDS3IanhbCIXERthzS7cWG1lnGQwQq5vB"
            row.operator("wm.url_open", text="Blender Artists Forum").url = "https://blenderartists.org/t/addon-photographer-camera-exposure-white-balance-and-autofocus/1101721"
            row = box.row(align=True)
            row.label(text='Free Libraries : ')
            row.operator("wm.url_open", text="PolyHaven HDRIs").url = "https://polyhaven.com/hdris"
            row.operator("wm.url_open", text="IES Library").url = "https://ieslibrary.com"
            row.operator("wm.url_open", text="Gobo Textures [Flora]").url = "https://mschumacher.gumroad.com/l/DkHCV"


def register():
    add_hotkey("3D View",'VIEW_3D','WINDOW',
        "wm.call_menu_pie","PHOTOGRAPHER_MT_Pie_Camera",
        'C', 'PRESS', shift=True, ctrl=True)

def unregister():
    remove_hotkey("3D View")
