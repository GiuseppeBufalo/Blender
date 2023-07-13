from .. import render_queue, view_layer
from . import camera_list, emissive_mixer, post_effects_panel, lightmixer_panel, world_mixer, camera_panel, lens_panel

photographer_panel_classes = (
    camera_list.PHOTOGRAPHER_PT_ViewPanel_CameraList,
    # camera_list.PHOTOGRAPHER_PT_ImageEditor_CameraList,
    # camera_list.PHOTOGRAPHER_PT_NodeEditor_CameraList,
    camera_list.PHOTOGRAPHER_UL_ViewPanel_CameraList,
    camera_list.PHOTOGRAPHER_UL_ViewPanel_CameraCollectionsList,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Camera,
    lens_panel.PHOTOGRAPHER_PT_ViewPanel_Lens,
    post_effects_panel.PHOTOGRAPHER_PT_ViewPanel_LensEffects,
    # camera_panel.PHOTOGRAPHER_PT_ViewPanel_DOF_Char,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Exposure,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_DOF,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Focus,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Autofocus,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_WhiteBalance,
    camera_panel.PHOTOGRAPHER_PT_ViewPanel_Resolution,
    render_queue.PHOTOGRAPHER_PT_ViewPanel_RenderQueue,
    view_layer.PHOTOGRAPHER_PT_ViewPanel_ViewLayer,
)

lightmixer_panel_classes = (
    lightmixer_panel.LIGHTMIXER_PT_ViewPanel,
    lightmixer_panel.LIGHTMIXER_PT_PropertiesSubPanel,
    emissive_mixer.LIGHTMIXER_PT_EmissiveViewPanel,
    world_mixer.LIGHTMIXER_PT_WorldViewPanel,
    world_mixer.LIGHTMIXER_PT_WorldProperties,
    lightmixer_panel.PHOTOGRAPHER_UL_ViewPanel_LightList,
    lightmixer_panel.PHOTOGRAPHER_UL_ViewPanel_LightCollectionsList,
)

# image_panel_classes = (
#     camera_panel.PHOTOGRAPHER_PT_ImageEditor_Exposure,
#     camera_panel.PHOTOGRAPHER_PT_NodeEditor_Exposure,
#     camera_panel.PHOTOGRAPHER_PT_ImageEditor_WhiteBalance,
#     camera_panel.PHOTOGRAPHER_PT_NodeEditor_WhiteBalance,
#     render_queue.PHOTOGRAPHER_PT_ImageEditor_RenderQueue,
#     render_queue.PHOTOGRAPHER_PT_NodeEditor_RenderQueue,
# )
