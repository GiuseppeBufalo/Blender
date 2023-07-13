bl_info = {
    "name": "Photographer",
    "description": "Adds Physical Camera and Physical Light controls, LightMixer and Render Queue",
    "author": "Fabien 'chafouin' Christin, @fabienchristin",
    "version": (5, 0, 7),
    "blender": (3, 0, 0),
    "location": "View3D > Side Panel > Photographer",
    "support": "COMMUNITY",
    "category": "Camera"}

import bpy
from bpy.props import PointerProperty

from . import (
    prefs,
    camera,
    camera_presets,
    presets_install,
    view_layer,
    light_presets,
    handler,
    render_queue,
    driver_functions,
)
from .ui import (
    camera_panel,
    post_effects_panel,
    lens_panel,
    light_panel,
    physical_light_add,
    physical_camera_add,
    library,
    focus_plane,
    pie_camera,
    composition_guides_menu,
    scene_panel,
)
from .ui import bokeh as bokeh_ui
from .ui.panel_classes import photographer_panel_classes, lightmixer_panel_classes
from .properties import light, scene, material, node, object, post_effects
from .properties import world as world_props
from .operators import (
    auto_exposure,
    autofocus,
    bokeh,
    camera_ops,
    lens,
    light_material,
    sampling_threshold,
    select,
    target,
    stop_adj,
    expand_ui,
    emissive,
    updater,
    exposure,
    ui,
    resolution,
    white_balance,
    world,
)
from .operators import lightmixer as lightmixer_op

from .rigs import build_rigs

classes = (
    # Preferences
    prefs.AddonPreferences,
    prefs.PHOTOGRAPHER_OT_Hotkey_Add_Pie_Camera,

    # Properties
    camera.PhotographerCameraSettings,
    post_effects.LensEffectsSettings,
    light.PhotographerLightSettings,

    # LightMixer Object
    object.LightMixerObjectSettings,

    # LightMixer Material
    material.LightMixerMaterialSettings,
    node.LightMixerNodeSettings,

    # Scene Properties
    scene.SceneSettings,
    scene.LightMixerSceneSettings,

    # World Properties
    world_props.LightMixerWorldSettings,

    # Operators
    lens.PHOTOGRAPHER_OT_DollyZoom,
    lens.PHOTOGRAPHER_OT_DollyZoom_Set_Key,
    lens.PHOTOGRAPHER_OT_LensEffects_Add,

    light_material.PHOTOGRAPHER_OT_Light_Textures_Add,
    light_material.PHOTOGRAPHER_OT_Reset_Intensity,

    select.PHOTOGRAPHER_OT_Select,
    select.PHOTOGRAPHER_OT_SelectCollection,
    select.PHOTOGRAPHER_OT_SelectEmissive,

    # stop_adj.PHOTOGRAPHER_OT_LightStop_Adj,
    stop_adj.PHOTOGRAPHER_OT_LightMixerStop_Adj,
    stop_adj.PHOTOGRAPHER_OT_EmissiveStop_Adj,

    target.PHOTOGRAPHER_OT_TargetAdd,
    target.PHOTOGRAPHER_OT_TargetDelete,

    expand_ui.PHOTOGRAPHER_OT_CollectionExpand,
    expand_ui.LIGHTMIXER_OT_ShowMore,

    ui.PHOTOGRAPHER_OT_ButtonStringClear,
    ui.PHOTOGRAPHER_OT_ButtonEnumClear,

    # Camera Operators
    camera.PHOTOGRAPHER_OT_MakeCamActive,
    camera.PHOTOGRAPHER_OT_ApplyPhotographerSettings,
    camera.PHOTOGRAPHER_OT_SelectActiveCam,
    camera.PHOTOGRAPHER_OT_SetShutterAngle,
    camera.PHOTOGRAPHER_OT_SetShutterSpeed,
    camera.PHOTOGRAPHER_OT_RenderMotionBlur,
    lens.PHOTOGRAPHER_OT_AutoLensShift,
    white_balance.PHOTOGRAPHER_OT_WBReset,
    white_balance.PHOTOGRAPHER_OT_WBPicker,
    autofocus.PHOTOGRAPHER_OT_FocusSingle,
    autofocus.PHOTOGRAPHER_OT_FocusTracking,
    autofocus.PHOTOGRAPHER_OT_FocusTracking_Cancel,
    autofocus.PHOTOGRAPHER_OT_CreateFocusPlane,
    autofocus.PHOTOGRAPHER_OT_DeleteFocusPlane,
    camera_ops.PHOTOGRAPHER_OT_LookThrough,
    camera_ops.PHOTOGRAPHER_OT_SwitchCamera,
    camera_ops.PHOTOGRAPHER_OT_CycleCamera,
    camera_ops.PHOTOGRAPHER_OT_AddDroneCamera,
    camera_ops.PHOTOGRAPHER_OT_AddCamera,
    camera_ops.PHOTOGRAPHER_OT_DeleteCamera,
    camera_ops.PHOTOGRAPHER_OT_DuplicateCamera,
    camera_ops.PHOTOGRAPHER_OT_SetDroneCameraKey,

    # Bokeh
    bokeh.PHOTOGRAPHER_OT_Bokeh_Add,
    bokeh.PHOTOGRAPHER_OT_Bokeh_Delete,
    bokeh.PHOTOGRAPHER_OT_OptVignetting_Add,
    bokeh.PHOTOGRAPHER_OT_OptVignetting_Delete,
    bokeh.PHOTOGRAPHER_OT_FixDisplayType,

    # Photographer Presets
    camera_presets.PHOTOGRAPHER_MT_CameraPresets,
    camera_presets.PHOTOGRAPHER_OT_AddCameraPreset,
    camera_presets.PHOTOGRAPHER_PT_CameraPresets,
    camera_presets.PHOTOGRAPHER_MT_LensPresets,
    camera_presets.PHOTOGRAPHER_OT_AddLensPreset,
    camera_presets.PHOTOGRAPHER_PT_LensPresets,
    camera_presets.PHOTOGRAPHER_MT_LensEffectsPresets,
    camera_presets.PHOTOGRAPHER_OT_AddLensEffectsPreset,
    camera_presets.PHOTOGRAPHER_PT_LensEffectsPresets,
    camera_presets.PHOTOGRAPHER_MT_ExposurePresets,
    camera_presets.PHOTOGRAPHER_OT_AddExposurePreset,
    camera_presets.PHOTOGRAPHER_PT_ExposurePresets,
    camera_presets.PHOTOGRAPHER_MT_ResolutionPresets,
    camera_presets.PHOTOGRAPHER_OT_AddResolutionPreset,
    camera_presets.PHOTOGRAPHER_PT_ResolutionPresets,

    # Camera UI
    camera_panel.PHOTOGRAPHER_PT_Panel,
    camera_panel.PHOTOGRAPHER_PT_Panel_Exposure,
    camera_panel.PHOTOGRAPHER_PT_Panel_WhiteBalance,
    camera_panel.PHOTOGRAPHER_PT_Panel_Resolution,
    camera_panel.PHOTOGRAPHER_PT_Panel_Autofocus,
    post_effects_panel.PHOTOGRAPHER_PT_Panel_LensEffects,
    camera_panel.PHOTOGRAPHER_OT_ChangeLuxCoreDevice,
    camera_panel.PHOTOGRAPHER_OT_EEVEE_DisableSoftShadows,

    # Camera PIE
    pie_camera.PHOTOGRAPHER_MT_Pie_Camera,

    # Image and Node Editor panels
    camera_panel.PHOTOGRAPHER_PT_ImageEditor_Exposure,
    camera_panel.PHOTOGRAPHER_PT_NodeEditor_Exposure,
    camera_panel.PHOTOGRAPHER_PT_ImageEditor_WhiteBalance,
    camera_panel.PHOTOGRAPHER_PT_NodeEditor_WhiteBalance,
    camera_panel.PHOTOGRAPHER_PT_ImageEditor_Resolution,
    camera_panel.PHOTOGRAPHER_PT_NodeEditor_Resolution,
    post_effects_panel.PHOTOGRAPHER_PT_ImageEditor_LensEffects,
    post_effects_panel.PHOTOGRAPHER_PT_NodeEditor_LensEffects,

    # Light Presets
    light_presets.PHOTOGRAPHER_PT_PhysicalLightPointPresets,
    light_presets.PHOTOGRAPHER_PT_PhysicalLightSunPresets,
    light_presets.PHOTOGRAPHER_PT_PhysicalLightSpotPresets,
    light_presets.PHOTOGRAPHER_PT_PhysicalLightAreaPresets,
    light_presets.PHOTOGRAPHER_OT_AddPointPreset,
    light_presets.PHOTOGRAPHER_OT_AddSunPreset,
    light_presets.PHOTOGRAPHER_OT_AddSpotPreset,
    light_presets.PHOTOGRAPHER_OT_AddAreaPreset,
    light_presets.PHOTOGRAPHER_MT_PhysicalLightPointPresets,
    light_presets.PHOTOGRAPHER_MT_PhysicalLightSunPresets,
    light_presets.PHOTOGRAPHER_MT_PhysicalLightSpotPresets,
    light_presets.PHOTOGRAPHER_MT_PhysicalLightAreaPresets,

    # Light UI
    light_panel.PHOTOGRAPHER_PT_Panel_Light,
    light_panel.PHOTOGRAPHER_PT_EEVEE_light_distance,
    light_panel.PHOTOGRAPHER_PT_spot,
    light_panel.PHOTOGRAPHER_PT_beam_shape,
    light_panel.PHOTOGRAPHER_OT_CalculateLightSize,
    light_panel.PHOTOGRAPHER_OT_CopySpotSize,
    light_panel.PHOTOGRAPHER_OT_SwitchColorMode,
    light_panel.PHOTOGRAPHER_OT_ApplyLightSettings,

    # Exposure
    exposure.PHOTOGRAPHER_OT_AddExposureNode,
    exposure.PHOTOGRAPHER_OT_DisableExposureNode,
    exposure.PHOTOGRAPHER_OT_EVPicker,

    # Resolution
    resolution.PHOTOGRAPHER_OT_FlipImage,

    # Light Mixer
    lightmixer_op.LIGHTMIXER_OT_LightModal,
    lightmixer_op.LIGHTMIXER_OT_Add,
    lightmixer_op.LIGHTMIXER_OT_Target_Add,
    lightmixer_op.LIGHTMIXER_OT_Delete,
    lightmixer_op.LIGHTMIXER_OT_Enable,
    lightmixer_op.LIGHTMIXER_OT_RefreshHDRIPreview,

    # Emissive Mixer
    emissive.LIGHTMIXER_OT_ScanEmissive,
    emissive.LIGHTMIXER_OT_CreateEmissive,
    emissive.LIGHTMIXER_OT_AddEmissiveControls,
    emissive.LIGHTMIXER_OT_EmissiveEnable,
    emissive.LIGHTMIXER_OT_MaterialEnable,
    emissive.LIGHTMIXER_OT_AddBackfaceCullingNodes,
    emissive.LIGHTMIXER_OT_AssignEmissive,

    # Render UI
    sampling_threshold.PHOTOGRAPHER_OT_UpdateLightThreshold,

    # World
    world.LIGHTMIXER_OT_World_HDRI_Add,
    world.LIGHTMIXER_OT_Sky_Texture_Add,
    world.LIGHTMIXER_OT_WorldEnable,
    world.LIGHTMIXER_OT_World_AddControls,
    world.LIGHTMIXER_OT_Refresh_HDR_Categories,
    world.LIGHTMIXER_OT_Cycle_World,

    # Updater
    updater.PHOTOGRAPHER_OT_CheckForUpdate,
)

# 3D Header Autofocus buttons
af_header_buttons = (
    autofocus.focus_single_button,
    autofocus.focus_continuous_button,
    autofocus.focus_animate_button,
    autofocus.focus_tracking_button,
    autofocus.focus_distance_header,
)
cam_header_buttons = (
    camera.lock_camera_button,
)

def eevee_light_panel_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.light) and (context.engine in {'BLENDER_EEVEE'})

def eevee_light_distance_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.light and context.light.type != 'SUN')  and (context.engine in {'BLENDER_EEVEE'})

def spot_panel_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.light and context.light.type == 'SPOT')  and (context.engine in {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'})

def area_panel_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.light and context.light.type == 'AREA')  and (context.engine in {'BLENDER_RENDER', 'BLENDER_WORKBENCH'})

def light_panel_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.engine in {'BLENDER_RENDER', 'BLENDER_WORKBENCH'})

def cycles_light_panel_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.light) and (context.engine in {'CYCLES'})

def cycles_spot_panel_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.light and context.light.type == 'SPOT') and (context.engine in {'CYCLES'})

def cycles_beam_shape_panel_poll(cls,context):
    pref = bpy.context.preferences.addons[__package__].preferences
    return (pref.show_default_light_panels or not pref.use_physical_lights) and (context.light and context.light.type in {'SPOT', 'AREA'}) and (context.engine in {'CYCLES'})

def cycles_check(load=False):
    import addon_utils
    is_enabled,is_loaded = addon_utils.check('cycles')
    if not is_loaded:
        if load:
            print ('Photographer requires Cycles to operate, automatically enabling it...')
            success = addon_utils.enable('cycles', default_set=True)
            if success:
                print ('Cycles is now enabled.')
                return True
        else:
            return False
    else:
        return True

def luxcore_check():
    import addon_utils
    is_enabled,is_loaded = addon_utils.check('BlendLuxCore')
    if is_loaded:
        return True

def register():
    # Load Cycles if not enabled
    if cycles_check(True):
        from bpy.utils import register_class, unregister_class
        from bpy.types import (
            DATA_PT_EEVEE_light,
            DATA_PT_EEVEE_light_distance,
            DATA_PT_spot,
            DATA_PT_light,
            DATA_PT_EEVEE_shadow,
            DATA_PT_EEVEE_shadow_cascaded_shadow_map,
            DATA_PT_EEVEE_shadow_contact,
            DATA_PT_custom_props_light,
            CYCLES_LIGHT_PT_light,
            CYCLES_LIGHT_PT_nodes,
        )
        if bpy.app.version < (3,5,0):
            from bpy.types import DATA_PT_area

        # Unregistering light panels to place Physical Light panel
        light_classes=[
            DATA_PT_EEVEE_shadow,
            DATA_PT_EEVEE_shadow_cascaded_shadow_map,
            DATA_PT_EEVEE_shadow_contact,
            DATA_PT_custom_props_light,
            CYCLES_LIGHT_PT_nodes,
        ]
        if bpy.app.version >= (2,93,0):
            from bpy.types import CYCLES_LIGHT_PT_beam_shape
            light_classes.append(CYCLES_LIGHT_PT_beam_shape)
        else:
            from bpy.types import CYCLES_LIGHT_PT_spot
            light_classes.append(CYCLES_LIGHT_PT_spot)

        for cls in light_classes:
            unregister_class(cls)

        # Registering classes
        for cls in (classes + photographer_panel_classes + lightmixer_panel_classes):
            register_class(cls)

        handler.register()
        prefs.register()
        scene_panel.register()
        auto_exposure.register()
        presets_install.register()
        render_queue.register()
        driver_functions.register()
        physical_light_add.register()
        physical_camera_add.register()
        library.register()
        composition_guides_menu.register()
        build_rigs.register()
        view_layer.register()

        # Reset Updater
        bpy.context.preferences.addons[__package__].preferences.needs_update = ""
        # Pass current add-on version to Updater
        updater.addon_version = bl_info['version']

        # Registering Panel classes - Preferences sets bl_category
        context = bpy.context
        preferences = context.preferences.addons[__name__].preferences
        prefs.update_photographer_category(preferences,context)
        prefs.update_lightmixer_category(preferences,context)

        # Change polls to hide or show default light panels
        DATA_PT_EEVEE_light.poll = classmethod(eevee_light_panel_poll)
        DATA_PT_EEVEE_light_distance.poll = classmethod(eevee_light_distance_poll)
        DATA_PT_spot.poll = classmethod(spot_panel_poll)
        if bpy.app.version < (3,5,0):
            DATA_PT_area.poll = classmethod(area_panel_poll)
        DATA_PT_light.poll = classmethod(light_panel_poll)
        CYCLES_LIGHT_PT_light.poll = classmethod(cycles_light_panel_poll)
        if bpy.app.version >= (2,93,0):
            CYCLES_LIGHT_PT_beam_shape.poll = classmethod(cycles_beam_shape_panel_poll)
        else:
            CYCLES_LIGHT_PT_spot.poll = classmethod(cycles_spot_panel_poll)

        # Addin Photographer property groups
        bpy.types.Camera.photographer = PointerProperty(type=camera.PhotographerCameraSettings)
        bpy.types.Camera.post_effects = PointerProperty(type=post_effects.LensEffectsSettings)
        bpy.types.Light.photographer = PointerProperty(type=light.PhotographerLightSettings)
        bpy.types.Scene.lightmixer = PointerProperty(type=scene.LightMixerSceneSettings)
        bpy.types.World.lightmixer = PointerProperty(type=world_props.LightMixerWorldSettings)
        bpy.types.Scene.photographer = PointerProperty(type=scene.SceneSettings)
        bpy.types.Object.lightmixer = PointerProperty(type=object.LightMixerObjectSettings)
        bpy.types.Material.lightmixer = PointerProperty(type=material.LightMixerMaterialSettings)
        bpy.types.ShaderNodeBsdfPrincipled.lightmixer = PointerProperty(type=node.LightMixerNodeSettings)
        bpy.types.ShaderNodeEmission.lightmixer = PointerProperty(type=node.LightMixerNodeSettings)

        # Adding Photographer panels to Blender UI
        bpy.types.RENDER_PT_eevee_shadows.append(sampling_threshold.light_threshold_button)
        bpy.types.DATA_PT_camera_dof.append(focus_plane.focus_plane_ui)
        bpy.types.DATA_PT_camera_dof_aperture.append(bokeh_ui.bokeh_ui)
        bpy.types.DATA_PT_lens.append(lens_panel.lens_shift_ui)
        bpy.types.CYCLES_RENDER_PT_sampling_advanced.append(sampling_threshold.light_threshold_button)
        bpy.types.CYCLES_CAMERA_PT_dof.append(focus_plane.focus_plane_ui)
        bpy.types.CYCLES_CAMERA_PT_dof_aperture.append(bokeh_ui.bokeh_ui)

        # Adding 3D view header buttons
        for button in af_header_buttons:
            bpy.types.VIEW3D_HT_header.append(button)

        for button in cam_header_buttons:
            bpy.types.VIEW3D_HT_header.append(button)

        # Registrering light panels again
        for cls in light_classes:
            register_class(cls)

    # Adding Photographer panels to LuxCore UI if enabled
    if luxcore_check():
        bpy.types.LUXCORE_CAMERA_PT_depth_of_field.append(bokeh_ui.bokeh_ui)


def revert_eevee_light_panel_poll(cls,context):
    return (context.engine in {'BLENDER_EEVEE'})

def revert_eevee_light_distance_poll(cls,context):
    return (context.light and context.light.type != 'SUN')  and (context.engine in {'BLENDER_EEVEE'})

def revert_spot_panel_poll(cls,context):
    return (context.light and context.light.type == 'SPOT')  and (context.engine in {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'})

def revert_area_panel_poll(cls,context):
    return (context.light and context.light.type == 'AREA')  and (context.engine in {'BLENDER_RENDER', 'BLENDER_WORKBENCH'})

def revert_light_panel_poll(cls,context):
    return (context.engine in {'BLENDER_RENDER', 'BLENDER_WORKBENCH'})

def revert_cycles_light_panel_poll(cls,context):
    return (context.light) and (context.engine in {'CYCLES'})

def revert_cycles_spot_panel_poll(cls,context):
    return (context.light and context.light.type == 'SPOT') and (context.engine in {'CYCLES'})

def revert_cycles_beam_shape_panel_poll(cls,context):
    return (context.light and context.light.type in {'SPOT', 'AREA'}) and (context.engine in {'CYCLES'})

####

def unregister():
    from bpy.utils import unregister_class, register_class
    from bpy.types import (
        DATA_PT_EEVEE_light,
        DATA_PT_EEVEE_light_distance,
        DATA_PT_spot,
        DATA_PT_light,
    )
    if bpy.app.version < (3,5,0):
        from bpy.types import DATA_PT_area

    # Add back Blender Light panels
    DATA_PT_EEVEE_light.poll = classmethod(revert_eevee_light_panel_poll)
    DATA_PT_EEVEE_light_distance.poll = classmethod(revert_eevee_light_distance_poll)
    DATA_PT_spot.poll = classmethod(revert_spot_panel_poll)
    if bpy.app.version < (3,5,0):
        DATA_PT_area.poll = classmethod(revert_area_panel_poll)
    DATA_PT_light.poll = classmethod(revert_light_panel_poll)

    # Remove 3D view header buttons
    for button in af_header_buttons:
        bpy.types.VIEW3D_HT_header.remove(button)

    for button in cam_header_buttons:
        bpy.types.VIEW3D_HT_header.remove(button)

    # Remove Photographer panels from Blender UI
    bpy.types.RENDER_PT_eevee_shadows.remove(sampling_threshold.light_threshold_button)
    bpy.types.DATA_PT_camera_dof.remove(focus_plane.focus_plane_ui)
    bpy.types.DATA_PT_camera_dof_aperture.remove(bokeh_ui.bokeh_ui)
    bpy.types.DATA_PT_lens.remove(lens_panel.lens_shift_ui)

    # Try to unregister Photographer Cycles UI if Cycles is enabled
    if cycles_check():
        if bpy.app.version >= (2,93,0):
            from bpy.types import CYCLES_LIGHT_PT_beam_shape
            CYCLES_LIGHT_PT_beam_shape.poll = classmethod(revert_cycles_beam_shape_panel_poll)
        else:
            from bpy.types import CYCLES_LIGHT_PT_spot
            CYCLES_LIGHT_PT_spot.poll = classmethod(revert_cycles_spot_panel_poll)

        from bpy.types import CYCLES_LIGHT_PT_light
        CYCLES_LIGHT_PT_light.poll = classmethod(revert_cycles_light_panel_poll)

        bpy.types.CYCLES_RENDER_PT_sampling_advanced.remove(sampling_threshold.light_threshold_button)
        bpy.types.CYCLES_CAMERA_PT_dof.remove(focus_plane.focus_plane_ui)
        bpy.types.CYCLES_CAMERA_PT_dof_aperture.remove(bokeh_ui.bokeh_ui)

    # Try to unregister Photographer LuxCore UI if LuxCore is enabled
    if luxcore_check():
        try:
            bpy.types.LUXCORE_CAMERA_PT_depth_of_field.remove(bokeh_ui.bokeh_ui)
        except:
            pass

    # Unregister Photographer Classes
    handler.unregister()
    prefs.unregister()
    scene_panel.unregister()
    auto_exposure.unregister()
    render_queue.unregister()
    driver_functions.unregister()
    physical_camera_add.unregister()
    physical_light_add.unregister()
    library.unregister()
    composition_guides_menu.unregister()
    build_rigs.unregister()
    view_layer.unregister()

    for cls in (classes + photographer_panel_classes + lightmixer_panel_classes):
        unregister_class(cls)

    # Unregister Photographer Properties
    del bpy.types.Camera.photographer
    del bpy.types.Light.photographer
    del bpy.types.Scene.lightmixer
    del bpy.types.World.lightmixer
    del bpy.types.Scene.photographer
    del bpy.types.Object.lightmixer
    del bpy.types.Material.lightmixer
    del bpy.types.ShaderNodeBsdfPrincipled.lightmixer
    del bpy.types.ShaderNodeEmission.lightmixer

if __name__ == "__main__":
    register()
