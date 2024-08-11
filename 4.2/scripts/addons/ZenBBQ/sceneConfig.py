# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2022, Dmitry Aleksandrovich Maslov (ABTOMAT)

import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty, PointerProperty, EnumProperty
from .labels import ZBBQ_Labels
from .consts import ZBBQ_Consts
from .units import ZBBQ_Units, ZBBQ_UnitsForEnumPropertySceneUnitSystem, ZBBQ_UnitsForEnumPropertyConsideringUnitSystem

from . import globals as ZBBQ_Globals
from .vlog import Log

from .colors import ZBBQ_Colors
from .commonFunc import ZBBQ_CommonFunc, ZBBQ_MaterialFunc
from .preferences import ZBBQ_Pref_BevelPresetGroup
from .blender_zen_utils import ZenStrUtils

from dataclasses import dataclass

import math


@dataclass
class ZBBQ_PreviewRenderConfigPreset:
    id: str = None
    title: str = None

    device: str = "GPU"

    noiseTresholdUse: bool = True
    noiseTresholdVal: float = 0.1

    samples: int = 1024
    samplesMin: int = 0  # only used if noiseTresholdUse is True

    denoiseUse: bool = False
    denoiser: str = "AUTO"
    denoiserPrefilter: str = "FAST"
    denoiserPasses: str = "RGB_ALBEDO"
    denoiserStartSample: int = 1

    useSceneLights: bool = False
    useSceneWorld: bool = False

    studioLightRotation: float = 0
    studioLightIntensity: float = 2
    studioWorldOpacity: float = 1

    bevelNodeSamples: int = 16

    def IsSet(self):

        cycles = bpy.context.scene.cycles
        spaceView3D = bpy.context.area.spaces.active

        # print(f"Current {ZBBQ_CommonFunc.NodeTreeNormalGetSamples()} vs Self: {self.bevelNodeSamples}")

        return (cycles.device == self.device and

                cycles.use_preview_adaptive_sampling == self.noiseTresholdUse and
                math.isclose(cycles.preview_adaptive_threshold, self.noiseTresholdVal, rel_tol=0.0000001) and

                cycles.preview_samples == self.samples and
                cycles.preview_adaptive_min_samples == self.samplesMin and

                cycles.use_preview_denoising == self.denoiseUse and
                cycles.preview_denoiser == self.denoiser and
                cycles.preview_denoising_prefilter == self.denoiserPrefilter and
                cycles.preview_denoising_input_passes == self.denoiserPasses and
                cycles.preview_denoising_start_sample == self.denoiserStartSample and

                spaceView3D.shading.use_scene_lights_render == self.useSceneLights and
                spaceView3D.shading.use_scene_world_render == self.useSceneWorld and

                spaceView3D.shading.studiolight_rotate_z == self.studioLightRotation and
                spaceView3D.shading.studiolight_intensity == self.studioLightIntensity and
                spaceView3D.shading.studiolight_background_alpha == self.studioWorldOpacity and

                ZBBQ_MaterialFunc.NodeTreeNormalGetSamples() == self.bevelNodeSamples
                )

    def CompareWithCurrent(self):  # Debug purposes only

        cycles = bpy.context.scene.cycles
        spaceView3D = bpy.context.area.spaces.active

        print("ZBBQ_PreviewRenderConfigPreset: Current vs Self")

        print("=== cycles ==")
        print(f"device: {cycles.device} vs {self.device}")
        print(f"use_preview_adaptive_sampling: {cycles.use_preview_adaptive_sampling} vs {self.noiseTresholdUse}")
        print(f"preview_adaptive_threshold: {cycles.preview_adaptive_threshold} vs {self.noiseTresholdVal}")
        print(f"preview_samples: {cycles.preview_samples} vs {self.samples}")
        print(f"preview_adaptive_min_samples: {cycles.preview_adaptive_min_samples} vs {self.samplesMin}")
        print(f"use_preview_denoising: {cycles.use_preview_denoising} vs {self.denoiseUse}")
        print(f"preview_denoiser: {cycles.preview_denoiser} vs {self.denoiser}")
        print(f"preview_denoising_prefilter: {cycles.preview_denoising_prefilter} vs {self.denoiserPrefilter}")
        print(f"preview_denoising_input_passes: {cycles.preview_denoising_input_passes} vs {self.denoiserPasses}")
        print(f"preview_denoising_start_sample: {cycles.preview_denoising_start_sample} vs {self.denoiserStartSample}")

        print("=== spaceView3D.shading ==")
        print(f"use_scene_lights_render: {spaceView3D.shading.use_scene_lights_render} vs {self.useSceneLights}")
        print(f"use_scene_world_render: {spaceView3D.shading.use_scene_world_render} vs {self.useSceneWorld}")
        print(f"studiolight_rotate_z: {spaceView3D.shading.studiolight_rotate_z} vs {self.studioLightRotation}")
        print(f"studiolight_intensity: {spaceView3D.shading.studiolight_intensity} vs {self.studioLightIntensity}")
        print(f"studiolight_background_alpha: {spaceView3D.shading.studiolight_background_alpha} vs {self.studioWorldOpacity}")

        print("=== Bevel Node ==")
        print(f"NodeTreeNormalGetSamples: {ZBBQ_MaterialFunc.NodeTreeNormalGetSamples()} vs {self.bevelNodeSamples}")

    def Set(self):

        if ZBBQ_PreviewRenderPresetsGetCurrentIdx(None) == 0:
            ZBBQ_PreviewRenderPresetsSaveCurrent()

        cycles = bpy.context.scene.cycles
        spaceView3D = bpy.context.area.spaces.active

        cycles.device = self.device

        cycles.use_preview_adaptive_sampling = self.noiseTresholdUse
        cycles.preview_adaptive_threshold = self.noiseTresholdVal

        cycles.preview_samples = self.samples
        cycles.preview_adaptive_min_samples = self.samplesMin

        cycles.use_preview_denoising = self.denoiseUse
        cycles.preview_denoiser = self.denoiser
        cycles.preview_denoising_prefilter = self.denoiserPrefilter
        cycles.preview_denoising_input_passes = self.denoiserPasses
        cycles.preview_denoising_start_sample = self.denoiserStartSample

        spaceView3D.shading.use_scene_lights_render = self.useSceneLights
        spaceView3D.shading.use_scene_world_render = self.useSceneWorld

        spaceView3D.shading.studiolight_rotate_z = self.studioLightRotation
        spaceView3D.shading.studiolight_intensity = self.studioLightIntensity
        spaceView3D.shading.studiolight_background_alpha = self.studioWorldOpacity

        ZBBQ_MaterialFunc.NodeTreeNormalSetSamples(self.bevelNodeSamples)

        ZBBQ_BuggedPinkShaderReset3DSpace(spaceView3D)


class ZBBQ_PreviewRenderConfigForSaving(PropertyGroup):  # Same as the previous class, but we need this once more as props for being saved

    isSet: BoolProperty(
            name="Is set",
            description="Was it written at least once?",
            default=False)

    device: StringProperty(
           name="Device",
           description="What device shall we use?",
           default="GPU"
    )

    noiseTresholdUse: BoolProperty(
            name="Noise Threshold Usage",
            description="Use Noise Threshold or not?",
            default=True)

    noiseTresholdVal: FloatProperty(
            name="Noise Threshold Value",
            description="Noise Threshold Value",
            default=0.1,
            min=0,
    )

    samples: IntProperty(
            name="Samples",
            description="Samples",
            default=1024,
            min=0,
    )

    samplesMin: IntProperty(  # only used if noiseTresholdUse is True
            name="Samples Min",
            description="Samples Min",
            default=0,
            min=0,
    )

    denoiseUse: BoolProperty(
            name="Denoise Usage",
            description="Use Denoise or not?",
            default=False)

    denoiser: StringProperty(
           name="Denoiser",
           description="What denoiser shall we use?",
           default="AUTO"
    )

    denoiserPrefilter: StringProperty(  # Only used in OpenImageDenoiser
           name="Denoiser Prefilter",
           description="Denoiser Prefilter (only for OpenImageDenoiser)",
           default="FAST"
    )

    denoiserPasses: StringProperty(
           name="Denoiser Passes",
           description="Denoiser Passes",
           default="RGB_ALBEDO"
    )

    denoiserStartSample: IntProperty(
            name="Denoiser Start Sample",
            description="Denoiser Start Sample",
            default=1,
            min=0,
    )

    useSceneLights: BoolProperty(
            name="Scene Lights Usage",
            description="Use Scene Lights or not?",
            default=False)

    useSceneWorld: BoolProperty(
            name="Scene World Usage",
            description="Use Scene World or not?",
            default=False)

    studioLightRotation: FloatProperty(
            name="Studio Light Rotation",
            description="Studio Light Rotation Z value",
            default=0
    )

    studioLightIntensity: FloatProperty(
        name="Studio Light Intensity",
        description="Studio Light Intensity value",
        default=2
    )

    studioWorldOpacity: FloatProperty(
        name="Studio World Opacity",
        description="Studio World Opacity value",
        default=1
    )

    bevelNodeSamples: IntProperty(
            name="Bevel Node Samples",
            description="Bevel Node Samples",
            default=16,
            min=2,
    )


ZBBQ_PreviewRenderPresets = [
    ZBBQ_PreviewRenderConfigPreset("LOW", "Low", "GPU", True, 0.1, 1, 1, False, "AUTO", "FAST", "RGB_ALBEDO", 2, False, False, 0, 1, 0, 2),
    ZBBQ_PreviewRenderConfigPreset("MEDIUM", "Med", "GPU", True, 0.1, 8, 1, True, "AUTO", "FAST", "RGB_ALBEDO", 8, False, False, 0, 1, 0, 16),
    ZBBQ_PreviewRenderConfigPreset("HIGH", "High", "GPU", False, 0.1, 32, 1, True, "AUTO", "ACCURATE", "RGB_ALBEDO", 32, False, False, 0, 1, 0, 128),
]

ZBBQ_PreviewRenderConfigStandard = ZBBQ_PreviewRenderConfigPreset("STD", "Standard", "CPU", True, 0.1, 1024, 0, False, "AUTO", "FAST", "RGB_ALBEDO", 1, True, True, 0, 1, 0, 16)


def ZBBQ_PreviewRenderConfigIsStandard():
    return ZBBQ_PreviewRenderConfigStandard.IsSet()


def ZBBQ_PreviewRenderConfigIsNotTouched():
    userConfig = bpy.context.scene.ZBBQ_PreviewRenderUserConfig
    return not userConfig.isSet  # and ZBBQ_PreviewRenderConfigIsStandard()
    # We don't check for standard settings any longer


def ZBBQ_PreviewRenderPresetsSaveCurrent():

    userConfig = bpy.context.scene.ZBBQ_PreviewRenderUserConfig
    cycles = bpy.context.scene.cycles
    spaceView3D = bpy.context.area.spaces.active

    userConfig.isSet = True

    userConfig.device = cycles.device

    userConfig.noiseTresholdUse = cycles.use_preview_adaptive_sampling
    userConfig.noiseTresholdVal = cycles.preview_adaptive_threshold

    userConfig.samples = cycles.preview_samples
    userConfig.samplesMin = cycles.preview_adaptive_min_samples

    userConfig.denoiseUse = cycles.use_preview_denoising
    userConfig.denoiser = cycles.preview_denoiser
    userConfig.denoiserPrefilter = cycles.preview_denoising_prefilter
    userConfig.denoiserPasses = cycles.preview_denoising_input_passes
    userConfig.denoiserStartSample = cycles.preview_denoising_start_sample

    userConfig.useSceneLights = spaceView3D.shading.use_scene_lights_render
    userConfig.useSceneWorld = spaceView3D.shading.use_scene_world_render

    userConfig.studioLightRotation = spaceView3D.shading.studiolight_rotate_z
    userConfig.studioLightIntensity = spaceView3D.shading.studiolight_intensity
    userConfig.studioWorldOpacity = spaceView3D.shading.studiolight_background_alpha

    userConfig.bevelNodeSamples = ZBBQ_MaterialFunc.NodeTreeNormalGetSamples()

    # print(f"Saved user's preview render settings, Samples: {bpy.context.scene.ZBBQ_PreviewRenderUserConfig.samples}")


def ZBBQ_BuggedPinkShaderReset3DSpace(spaceView3D):

    if bpy.context.scene.render.engine != 'CYCLES':
        return
    if(type(spaceView3D) is not bpy.types.SpaceView3D):
        print("[Zen BBQ] ZBBQ_BuggedPinkShaderReset3DSpace func only works in SpaceView3D!")
        return

    bpy.context.view_layer.use = bpy.context.view_layer.use  # Applies the changed settings (probably a bug of Blender)

    if spaceView3D.shading.studio_light != 'Default':
        spaceView3D.shading.studio_light = spaceView3D.shading.studio_light  # Resolves bug with pink object and environment (probably a bug of Blender)
    else:
        # We will need to reset this once user changes mode to rendered, so we memorize it
        ZBBQ_Globals.buggedPinkShaderReset3DSpaceDeferred = True
        # print("ZBBQ_Globals.buggedPinkShaderReset3DSpaceDeferred will be deferred!")


def ZBBQ_PreviewRenderPresetsRestoreSaved():

    userConfig = bpy.context.scene.ZBBQ_PreviewRenderUserConfig
    cycles = bpy.context.scene.cycles
    spaceView3D = bpy.context.area.spaces.active

    cycles.device = userConfig.device

    cycles.use_preview_adaptive_sampling = userConfig.noiseTresholdUse
    cycles.preview_adaptive_threshold = userConfig.noiseTresholdVal

    cycles.preview_samples = userConfig.samples
    cycles.preview_adaptive_min_samples = userConfig.samplesMin

    cycles.use_preview_denoising = userConfig.denoiseUse
    cycles.preview_denoiser = userConfig.denoiser
    cycles.preview_denoising_prefilter = userConfig.denoiserPrefilter
    cycles.preview_denoising_input_passes = userConfig.denoiserPasses
    cycles.preview_denoising_start_sample = userConfig.denoiserStartSample

    spaceView3D.shading.use_scene_lights_render = userConfig.useSceneLights
    spaceView3D.shading.use_scene_world_render = userConfig.useSceneWorld

    spaceView3D.shading.studiolight_rotate_z = userConfig.studioLightRotation
    spaceView3D.shading.studiolight_intensity = userConfig.studioLightIntensity
    spaceView3D.shading.studiolight_background_alpha = userConfig.studioWorldOpacity

    ZBBQ_MaterialFunc.NodeTreeNormalSetSamples(userConfig.bevelNodeSamples)

    ZBBQ_BuggedPinkShaderReset3DSpace(spaceView3D)
    # print("Restored user's preview render settings")


def ZBBQ_PreviewRenderPresetsMatchesSaved():

    userConfig = bpy.context.scene.ZBBQ_PreviewRenderUserConfig
    cycles = bpy.context.scene.cycles
    spaceView3D = bpy.context.area.spaces.active

    return (userConfig.isSet and

            cycles.device == userConfig.device and

            cycles.use_preview_adaptive_sampling == userConfig.noiseTresholdUse and
            math.isclose(cycles.preview_adaptive_threshold, userConfig.noiseTresholdVal, rel_tol=0.0000001) and

            cycles.preview_samples == userConfig.samples and
            cycles.preview_adaptive_min_samples == userConfig.samplesMin and

            cycles.use_preview_denoising == userConfig.denoiseUse and
            cycles.preview_denoiser == userConfig.denoiser and
            cycles.preview_denoising_prefilter == userConfig.denoiserPrefilter and
            cycles.preview_denoising_input_passes == userConfig.denoiserPasses and
            cycles.preview_denoising_start_sample == userConfig.denoiserStartSample and

            spaceView3D.shading.use_scene_lights_render == userConfig.useSceneLights and
            spaceView3D.shading.use_scene_world_render == userConfig.useSceneWorld and

            spaceView3D.shading.studiolight_rotate_z == userConfig.studioLightRotation and
            spaceView3D.shading.studiolight_intensity == userConfig.studioLightIntensity and
            spaceView3D.shading.studiolight_background_alpha == userConfig.studioWorldOpacity
            )


def ZBBQ_PreviewRenderPresetsGetCurrentIdx(self):

    for idx, preset in enumerate(ZBBQ_PreviewRenderPresets):
        if preset.IsSet():
            return idx+1

    return 0  # Zero is always the "Custom" option


def ZBBQ_PreviewRenderPresetsSet(self, value):

    if value == -1:  # -1 is for "Revert"
        ZBBQ_PreviewRenderPresetsRestoreSaved()
    else:
        ZBBQ_PreviewRenderPresets[value-1].Set()
    return None


def ZBBQ_PreviewRenderPresetsSetDefault(self):
    ZBBQ_PreviewRenderConfigStandard.Set()


def ZBBQ_PreviewRenderPresetsForEnumPropertyDynamic():
    # Can't use this propertly, hoping to do so in Bright Future
    # See: https://blender.stackexchange.com/questions/215781/enum-items-is-empty-on-a-dynamic-enumproperty
    # Also: https://developer.blender.org/T86803

    result = []

    if ZBBQ_PreviewRenderPresetsGetCurrentIdx(None) == 0:
        result.append(('CUSTOM', 'Custom', 'Custom preview render settings', 0))
    else:
        # result.append(('CUSTOM', 'Revert', "Revert to user's", 'LOOP_BACK', 0))  # With icon
        result.append(('CUSTOM', 'Revert', "Revert to user's", 0))

    result.extend([(preset.id, preset.title, preset.title, idx+1) for idx, preset in enumerate(ZBBQ_PreviewRenderPresets)])

    return result


def ZBBQ_PreviewRenderPresetsForEnumPropertyStatic():

    result = [('CUSTOM', 'Custom', 'Custom preview render settings', 0), ('REVERT', 'Revert', "Revert to user's", -1)]

    result.extend([(preset.id, preset.title, preset.title, idx+1) for idx, preset in enumerate(ZBBQ_PreviewRenderPresets)])

    return result


class ZBBQ_SceneConfigFunc:

    @classmethod
    def CbOnBBQOverlayOn(cls):

        bpy.context.scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce = True

        cls.OverlayShow(True)
        cls.OverlayConfigOverride()

    @classmethod
    def CbOnBBQOverlayOff(cls):
        bpy.context.scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce = True

        cls.OverlayShow(bpy.context.scene.ZBBQ_OverlayShow)
        cls.OverlayConfigRestore()

    def OverlayConfigIsOverridden():

        if bpy.context.area is not None:

            overlayConfig = bpy.context.area.spaces.active.overlay

            return (not overlayConfig.show_edge_crease and
                    not overlayConfig.show_edge_sharp and
                    not overlayConfig.show_edge_bevel_weight and
                    not overlayConfig.show_edge_seams)

    def OverlayShow(val):  # Set Blender's Overlays On or Off

        if bpy.context.area is not None:
            bpy.context.scene.ZBBQ_OverlayShow = bpy.context.area.spaces.active.overlay.show_overlays

            if bpy.context.area.spaces.active.overlay.show_overlays != val:  # Take action only if we really need to change it

                # Need to disable subscription, otherwise we'll get settings re-set
                from . import eventHandling
                eventHandling.ZBBQ_RnaUnsubscribeSpaceView3DOverlay()
                bpy.context.area.spaces.active.overlay.show_overlays = val
                eventHandling.ZBBQ_RnaSubscribeSpaceView3DOverlay()

    @classmethod
    def OverlayConfigOverride(cls):
        if not cls.OverlayConfigIsOverridden():
            cls.OverlayConfigStore()

        # Need to disable subscription, otherwise we'll get settings re-set
        from . import eventHandling
        eventHandling.ZBBQ_RnaUnsubscribeSpaceView3DOverlayEdgeDisplay()

        if bpy.context.area is not None:

            overlayConfig = bpy.context.area.spaces.active.overlay

            overlayConfig.show_edge_crease = False
            overlayConfig.show_edge_sharp = False
            overlayConfig.show_edge_bevel_weight = False
            overlayConfig.show_edge_seams = False

        eventHandling.ZBBQ_RnaSubscribeSpaceView3DOverlayEdgeDisplay()

    def OverlayConfigStore():

        if bpy.context.area is not None:

            overlayConfig = bpy.context.area.spaces.active.overlay

            bpy.context.scene.ZBBQ_OverlayConfigCreases = overlayConfig.show_edge_crease
            bpy.context.scene.ZBBQ_OverlayConfigSharp = overlayConfig.show_edge_sharp
            bpy.context.scene.ZBBQ_OverlayConfigBevel = overlayConfig.show_edge_bevel_weight
            bpy.context.scene.ZBBQ_OverlayConfigSeams = overlayConfig.show_edge_seams

            bpy.context.scene.ZBBQ_OverlayConfigIsStored = True

    def OverlayConfigRestore():
        if not bpy.context.scene.ZBBQ_OverlayConfigIsStored:
            return

        # Need to disable subscription, otherwise we'll get settings re-set
        from . import eventHandling
        eventHandling.ZBBQ_RnaUnsubscribeSpaceView3DOverlayEdgeDisplay()

        overlayConfig = None

        if bpy.context.area is not None:  # To-Do: Make function for this!
            overlayConfig = bpy.context.area.spaces.active.overlay
        else:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    overlayConfig = area.spaces.active.overlay

        if overlayConfig is not None:
            overlayConfig.show_edge_crease = bpy.context.scene.ZBBQ_OverlayConfigCreases
            overlayConfig.show_edge_sharp = bpy.context.scene.ZBBQ_OverlayConfigSharp
            overlayConfig.show_edge_bevel_weight = bpy.context.scene.ZBBQ_OverlayConfigBevel
            overlayConfig.show_edge_seams = bpy.context.scene.ZBBQ_OverlayConfigSeams

        eventHandling.ZBBQ_RnaSubscribeSpaceView3DOverlayEdgeDisplay()

    def PresetGroupSaveActive():

        # Copies bevel preset group and presets in it from prefs to scene data

        bpgActive = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()
        bpgStored = bpy.context.scene.ZBBQ_PresetsIncluded

        bpy.context.scene.ZBBQ_HasPresetsIncluded = True

        bpgStored.title = bpgActive.title
        bpgStored.unitSystem = bpgActive.unitSystem
        bpgStored.bevelPresetsIndex = bpgActive.bevelPresetsIndex

        for i in range(len(bpgStored.bevelPresets)-1, -1, -1):
            bpgStored.bevelPresets.remove(i)

        for bpActive in bpgActive.bevelPresets:
            bpStored = bpgStored.bevelPresets.add()

            bpStored.unitSystem = bpActive.unitSystem
            bpStored.radius = bpActive.radius
            bpStored.units = bpActive.units
            bpStored.colorId = bpActive.colorId
            bpStored.color = bpActive.color

    def PresetGroupGetIdxCorresponding():

        bpgStored = bpy.context.scene.ZBBQ_PresetsIncluded
        prefs = ZBBQ_CommonFunc.GetPrefs()

        for idxBpg in range(len(prefs.bevelPresetGroups)):

            bpg = prefs.bevelPresetGroups[idxBpg]

            if not (bpgStored.title == bpg.title
                    and bpgStored.unitSystem == bpg.unitSystem
                    and len(bpgStored.bevelPresets) == len(bpg.bevelPresets)):

                continue

            for idxBp in range(len(bpg.bevelPresets)):
                bp = bpg.bevelPresets[idxBp]
                bpStored = bpgStored.bevelPresets[idxBp]

                if not (bpStored.unitSystem == bp.unitSystem
                        and bpStored.radius == bp.radius
                        and bpStored.units == bp.units
                        and bpStored.colorId == bp.colorId
                        and bpStored.color == bp.color):
                    break
            else:
                # All checks passed: this is it!
                return idxBpg
            continue

        return -1  # Not Found

    @classmethod
    def CbOnInit(cls):

        # On scene loaded or add-on activated
        # print("ZBBQ_SceneConfigFunc.CbOnInit")

        prefs = ZBBQ_CommonFunc.GetPrefs()

        if bpy.context.scene.ZBBQ_HasPresetsIncluded:
            for i, bp in enumerate(bpy.context.scene.ZBBQ_PresetsIncluded.bevelPresets):
                colorKeys = list(ZBBQ_Colors.keys())
                if bp.colorId not in colorKeys:  # From old version
                    bp.colorId = colorKeys[i]
                    bp.color = ZBBQ_Colors[bp.colorId].color

            idxCorresponding = cls.PresetGroupGetIdxCorresponding()
            if(idxCorresponding != -1):
                ZBBQ_Globals.displaySceneIncludedBevelPresets = False
                prefs.bevelPresetGroupsDropdown = f"{idxCorresponding}"
            else:
                ZBBQ_Globals.displaySceneIncludedBevelPresets = True
                prefs.bevelPresetGroupsDropdown = str(len(prefs.bevelPresetGroups))
        else:
            ZBBQ_Globals.displaySceneIncludedBevelPresets = False

            if(prefs.bevelPresetGroupsDropdown == ''):
                prefs.bevelPresetGroupsDropdown = '1'  # str(len(prefs.bevelPresetGroups) - 1)

        # If before saving BBQ Highlight was On, we should corerect all saved settings

        if bpy.context.scene.ZBBQ_ZenBBQOverlayShow:

            Log.debug(f"On Init: Was BBQ Highlight enabled? {bpy.context.scene.ZBBQ_ZenBBQOverlayShow}")
            cls.CbOnBBQOverlayOff()

    @classmethod
    def CbOnSceneSaved(cls):

        # On scene saved
        # print("ZBBQ_SceneConfigFunc.CbOnSceneSaved")

        cls.PresetGroupSaveActive()


classes = (

    ZBBQ_PreviewRenderConfigForSaving,

)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce = BoolProperty(
            name="User knows where Display Colored Edges button is",
            description="User has used it at least once, so we will not switch it for them any longer",
            default=False)

    bpy.types.Scene.ZBBQ_PreviewRenderUserConfig = PointerProperty(type=ZBBQ_PreviewRenderConfigForSaving)

    bpy.types.Screen.ZBBQ_PreviewRenderConfigSwitch = EnumProperty(

        # items=lambda self, context: ZBBQ_PreviewRenderPresetsForEnumPropertyDynamic(),
        items=ZBBQ_PreviewRenderPresetsForEnumPropertyStatic(),

        set=ZBBQ_PreviewRenderPresetsSet,
        get=ZBBQ_PreviewRenderPresetsGetCurrentIdx,

        options={'HIDDEN', 'SKIP_SAVE'}
    )

    bpy.types.Scene.ZBBQ_AutoPreviewShaderNodeToggle = BoolProperty(
            name="Auto Preview Material Override",
            description="Automatically Toggle Preview Material Override shader node while switching Render preview",
            default=True)

    # Zen BBQ Overlay On/Off

    bpy.types.Scene.ZBBQ_ZenBBQOverlayShow = BoolProperty(
            name="Zen BBQ Overlay Display On/Off",
            description="Stored value for Zen BBQ Overlay Display On/Off",
            default=False)

    # Overlay On/Off

    bpy.types.Scene.ZBBQ_OverlayShow = BoolProperty(
            name="Blender Overlay Display On/Off",
            description="Stored user's value for Blender Overlay Display On/Off",
            default=False)

    # Overlay Config

    bpy.types.Scene.ZBBQ_OverlayConfigIsStored = BoolProperty(
            name="Is user's Overlay Config stored?",
            description="Is user's Overlay Config stored?",
            default=False)

    bpy.types.Scene.ZBBQ_OverlayConfigCreases = BoolProperty(
            name="Overlay Config Creases",
            description="Stored user's value for overlay creases edges",
            default=False)

    bpy.types.Scene.ZBBQ_OverlayConfigSharp = BoolProperty(
            name="Overlay Config Sharp",
            description="Stored user's value for overlay sharp edges",
            default=False)

    bpy.types.Scene.ZBBQ_OverlayConfigBevel = BoolProperty(
            name="Overlay Config Bevel",
            description="Stored user's value for overlay bevel edges",
            default=False)

    bpy.types.Scene.ZBBQ_OverlayConfigSeams = BoolProperty(
            name="Overlay Config Seams",
            description="Stored user's value for overlay seam edges",
            default=False)

    # In-scene saved presets

    bpy.types.Scene.ZBBQ_HasPresetsIncluded = BoolProperty(
            name="Has presets included?",
            description="Has bevel preset group included?",
            default=False)

    bpy.types.Scene.ZBBQ_PresetsIncluded = PointerProperty(type=ZBBQ_Pref_BevelPresetGroup)

    # Object units display

    def ZBBQ_IntactBevelDisplayUnitsUpdate(self,value):
        # Log.debug("Чего такую рожу скорчил? Сказано же, поддержка Blender 4.0 ближе к выходным будет.")
        Log.debug(self.ZBBQ_IntactBevelDisplayRadius * ZBBQ_Units[self.ZBBQ_IntactBevelDisplayUnits].unitAndSceneScaleMultiplier())

    bpy.types.Object.ZBBQ_IntactBevelDisplayUnits = bpy.props.EnumProperty(
        items=lambda self, context: ZBBQ_UnitsForEnumPropertyConsideringUnitSystem(ZBBQ_CommonFunc.GetActiveBevelPresetGroup().unitSystem),
        # items=lambda self, context: ZBBQ_UnitsForEnumPropertySceneUnitSystem(),
        name=ZBBQ_Labels.ZBBQ_PROP_IntactBevelDisplayUnits_Label,
        description=ZBBQ_Labels.ZBBQ_PROP_IntactBevelDisplayUnits_Desc,
        update=ZBBQ_IntactBevelDisplayUnitsUpdate
    )

    def ZBBQ_IntactBevelDisplayRadiusSet(self,value):
        self[ZBBQ_Consts.customPropertyIntactBevelRadiusName] = value*ZBBQ_Units[self.ZBBQ_IntactBevelDisplayUnits].unitAndSceneScaleMultiplier()

    def ZBBQ_IntactBevelDisplayRadiusGet(self):
        return self[ZBBQ_Consts.customPropertyIntactBevelRadiusName]/ZBBQ_Units[self.ZBBQ_IntactBevelDisplayUnits].unitAndSceneScaleMultiplier()

    bpy.types.Object.ZBBQ_IntactBevelDisplayRadius = bpy.props.FloatProperty(
        name=ZBBQ_Labels.ZBBQ_PROP_IntactBevelDisplayRadius_Label,
        description=ZBBQ_Labels.ZBBQ_PROP_IntactBevelDisplayRadius_Desc,
        set=ZBBQ_IntactBevelDisplayRadiusSet,
        get=ZBBQ_IntactBevelDisplayRadiusGet,
    )

    # Save to folder

    def get_bake_folder_expand(self):
        import os
        s_path = bpy.path.abspath(self.ZBBQ_BakeSaveToFolder)
        s_path = ZenStrUtils.ireplace(s_path, '//', bpy.path.abspath('//'))
        s_path = ZenStrUtils.ireplace(s_path, '%RENDER_OUTPUT%', bpy.path.abspath(bpy.context.preferences.filepaths.render_output_directory))
        s_path = ZenStrUtils.ireplace(s_path, '%TEXTURES%', bpy.path.abspath(bpy.context.preferences.filepaths.texture_directory))
        s_path = ZenStrUtils.ireplace(s_path, '%SCENE_NAME%', self.name)

        s_path = os.path.abspath(s_path)

        return s_path

    def set_bake_folder_expand(self, value):
        if value:
            value = bpy.path.abspath(value)
            value = ZenStrUtils.ireplace(value, bpy.path.abspath('//'), '//')
            value = ZenStrUtils.ireplace(value, bpy.path.abspath(bpy.context.preferences.filepaths.render_output_directory), '%RENDER_OUTPUT%')
            value = ZenStrUtils.ireplace(value, bpy.path.abspath(bpy.context.preferences.filepaths.texture_directory), '%TEXTURES%')
            value = ZenStrUtils.ireplace(value, self.name, '%SCENE_NAME%')

        self.ZBBQ_BakeSaveToFolder = value

    bpy.types.Scene.ZBBQ_BakeSaveToFolderExpand = StringProperty(
            name="Save baked images to",
            description="Directory where the baked images are saved to",
            get=get_bake_folder_expand,
            set=set_bake_folder_expand,
            options={'HIDDEN', 'SKIP_SAVE'},
            subtype='DIR_PATH')

    def get_bake_folder(self):
        s_path = self.get('ZBBQ_BakeSaveToFolder', '')
        return s_path if s_path else '//'

    def set_bake_folder(self, value):
        self['ZBBQ_BakeSaveToFolder'] = value

    bpy.types.Scene.ZBBQ_BakeSaveToFolder = StringProperty(
        name="Save baked images to",
        description="Directory where the baked images are saved to",
        get=get_bake_folder,
        set=set_bake_folder)

    def get_bake_image_name(self):
        s_path = self.get('ZBBQ_BakeImageName', '')
        return s_path if s_path else r'%MAT_NAME% - %IMAGE_NAME%.png'

    def set_bake_image_name(self, value):
        self['ZBBQ_BakeImageName'] = value

    bpy.types.Scene.ZBBQ_BakeImageName = StringProperty(
        name="Image Name",
        description="Name of the baked image, available constants: %MAT_NAME%, %IMAGE_NAME%, %SCENE_NAME%, %ID%",
        get=get_bake_image_name,
        set=set_bake_image_name)

    bpy.types.Scene.ZBBQ_BakeImageWidth = IntProperty(
            name="Baked image width",
            description="Baked image width",
            default=1024,
            min=128,
            max=8096)

    bpy.types.Scene.ZBBQ_BakeImageHeight = IntProperty(
            name="Baked image height",
            description="Baked image height",
            default=1024,
            min=128,
            max=8096)


def unregister():

    del bpy.types.Scene.ZBBQ_UserHasDisabledColoredEdgesAtLeastOnce

    del bpy.types.Scene.ZBBQ_PreviewRenderUserConfig

    del bpy.types.Screen.ZBBQ_PreviewRenderConfigSwitch

    del bpy.types.Scene.ZBBQ_AutoPreviewShaderNodeToggle

    # Zen BBQ Overlay On/Off

    del bpy.types.Scene.ZBBQ_ZenBBQOverlayShow

    # Overlay On/Off

    del bpy.types.Scene.ZBBQ_OverlayShow

    # Overlay Config

    del bpy.types.Scene.ZBBQ_OverlayConfigIsStored

    del bpy.types.Scene.ZBBQ_OverlayConfigCreases
    del bpy.types.Scene.ZBBQ_OverlayConfigSharp
    del bpy.types.Scene.ZBBQ_OverlayConfigBevel
    del bpy.types.Scene.ZBBQ_OverlayConfigSeams

    # In-scene saved presets

    del bpy.types.Scene.ZBBQ_HasPresetsIncluded
    del bpy.types.Scene.ZBBQ_PresetsIncluded

    del bpy.types.Object.ZBBQ_IntactBevelDisplayUnits
    del bpy.types.Object.ZBBQ_IntactBevelDisplayRadius

    for cls in classes:
        bpy.utils.unregister_class(cls)
