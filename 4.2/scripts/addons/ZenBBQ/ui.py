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

import os
import bpy
from bpy.types import UIList, Operator, Panel, Menu

from . import globals as ZBBQ_Globals
from .colors import ZBBQ_Colors
from .ico import ZBBQ_Icons
from .units import ZBBQ_UnitSystems
from .consts import ZBBQ_Consts
from .bake import ZBBQ_Bake
from .commonFunc import ZBBQ_CommonFunc, ZBBQ_MaterialFunc
from .sceneConfig import ZBBQ_PreviewRenderPresetsGetCurrentIdx, ZBBQ_PreviewRenderPresetsMatchesSaved
from .operators import ZBBQ_OT_ActiveObjectGetReady, ZBBQ_OT_BakeNormalForSelection, ZBBQ_OT_BakeOpenFolder, ZBBQ_OT_FixSceneUnitSystem, ZBBQ_OT_BakeStart, ZBBQ_OT_MaterialsRepair, ZBBQ_OT_PieMenuGeometryOptionsTop, ZBBQ_OT_PresetsPresetGroupImportFromScene, ZBBQ_OT_SetZeroBevelRadiusToSelection, ZBBQ_OT_ShaderNodeNormalAdd, ZBBQ_OT_DrawHighlight, ZBBQ_OT_GlobalAddonCleanup, ZBBQ_OT_Keymaps, ZBBQ_OT_ObjectAddonCleanup, ZBBQ_OT_PieMenuGeometryOptionsBottom, ZBBQ_OT_PresetsPresetGroupAdd, ZBBQ_OT_PresetsPresetGroupRemove, ZBBQ_OT_PreviewShaderNodeToggle, ZBBQ_OT_ShaderNodeNormalRemove, ZBBQ_OT_RenderPreviewToggle, ZBBQ_OT_ResetPreferences, ZBBQ_OT_SetBevelRadiusToSelection, ZBBQ_OT_ShaderNodeNormalToggle, ZBBQ_OT_SmartSelectByRadiusFromActivePreset, ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts, ZBBQ_OT_TestOpA, ZBBQ_OT_TestOpB  # , ZBBQ_OT_bake_modal
from .labels import ZBBQ_Labels
from .blender_zen_utils import ZsUiConstants

from .draw_sets import is_draw_handler_enabled, ZBBQ_EdgeLayerManager


class ZBBQ_PT_Main(Panel):

    bl_idname = "ZBBQ_PT_Main"
    bl_label = "Zen BBQ"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zen BBQ'

    @classmethod
    def poll(cls, context):
        if context.mode in {'EDIT_MESH', 'OBJECT'}:
            return True
        return False

    # def draw_header(self, context):

    #     bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()
    #     # bpg and self.layout.label(text=bpg.title+(" ("+bpg.getUnitInfo().shortTitle+")" if bpg.getUnitInfo().shortTitle != '' else ''))
    #     bpg and self.layout.label(text=bpg.title)

    def draw(self, context):
        # with cProfile.Profile() as pr:
        layout = self.layout

        prefs = ZBBQ_CommonFunc.GetPrefs()
        bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()

        # Presets Dropdown, Add and Remove

        rowRight = layout.row(align=True)
        rowRight.prop(prefs, "bevelPresetGroupsDropdown", text='')

        panelWidth = 0

        for reg in bpy.context.area.regions:
            if reg.type == "UI":
                panelWidth = reg.width
        if panelWidth < ZBBQ_Consts.refPanelWidth:
            rowRight.scale_x = ZBBQ_Consts.refPanelWidth*0.15/panelWidth
        else:
            rowRight.scale_x = 0.1

        if ZBBQ_Globals.displaySceneIncludedBevelPresets and ZBBQ_CommonFunc.GetActiveBevelPresetGroup() == bpy.context.scene.ZBBQ_PresetsIncluded:
            rowRight.operator(ZBBQ_OT_PresetsPresetGroupImportFromScene.bl_idname, text=" ", icon="IMPORT")
        rowRight.operator(ZBBQ_OT_PresetsPresetGroupAdd.bl_idname, text="+")
        rowRight.operator(ZBBQ_OT_PresetsPresetGroupRemove.bl_idname, text="-")

        # Wrong unit system warning

        if bpg and bpy.context.scene.unit_settings.system != 'NONE' and bpg.unitSystem != 'NONE' and bpy.context.scene.unit_settings.system != bpg.unitSystem:

            rowWrongUnitSystem = layout.row(align=False)
            rowLeft = rowWrongUnitSystem.row(align=False)
            rowRight = rowWrongUnitSystem.row(align=True)
            rowRight.alignment = 'RIGHT'

            rowLeft.label(text=f"Scene unit system is {ZBBQ_UnitSystems[bpy.context.scene.unit_settings.system]}", icon='ERROR')
            rowRight.operator(ZBBQ_OT_FixSceneUnitSystem.bl_idname, text="Fix")

        if bpg is None:
            layout.label(text="Please create a new preset group")

        else:

            rowToolbar = layout.row(align=False)
            rowLeft = rowToolbar.row(align=False)
            rowRight = rowToolbar.row(align=True)
            rowRight.alignment = 'RIGHT'

            b_is_highlight_enabled = is_draw_handler_enabled(ZBBQ_EdgeLayerManager)
            rowLeft.operator(ZBBQ_OT_DrawHighlight.bl_idname,  depress=b_is_highlight_enabled, text='', icon='OVERLAY')

            rowRight.operator(ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts.bl_idname, text='', icon='RESTRICT_SELECT_OFF')

            rowRight.operator(ZBBQ_OT_SmartSelectByRadiusFromActivePreset.bl_idname, text='', icon='ANCHOR_RIGHT')

            rowRight.separator()

            previewShaderNodeToggleModeAndObjects = []
            if context.mode == 'EDIT_MESH':
                previewShaderNodeToggleModeAndObjects = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(context.objects_in_mode, ZBBQ_Consts.shaderNodeTreeNormalName)
            elif context.mode == 'OBJECT':
                previewShaderNodeToggleModeAndObjects = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(context.selected_objects, ZBBQ_Consts.shaderNodeTreeNormalName)

            previewShaderNodeToggleDepress = previewShaderNodeToggleModeAndObjects['toggleMode'] == 'OFF' and len(previewShaderNodeToggleModeAndObjects['objectsToToggle']) > 0

            rowRight.operator(ZBBQ_OT_ShaderNodeNormalToggle.bl_idname, depress=previewShaderNodeToggleDepress, text='', icon="NODETREE")

            # rowRight.operator(ZBBQ_OT_ObjectAddonCleanup.bl_idname, text='', icon="LOOP_BACK")
            # rowRight.operator(ZBBQ_OT_SetZeroBevelRadiusToSelection.bl_idname, text='', icon="LAYER_USED")

            if context.mode == 'EDIT_MESH':
                rowRight.operator(ZBBQ_OT_SetZeroBevelRadiusToSelection.bl_idname, text='', icon="LOOP_BACK")
            elif context.mode == 'OBJECT':
                rowRight.operator(ZBBQ_OT_ObjectAddonCleanup.bl_idname, text='', icon="LOOP_BACK")

            # row.operator(ZBBQ_OT_PresetsPresetOrderChange.bl_idname, text="", icon='TRIA_UP').direction = 'UP'
            # row.operator(ZBBQ_OT_PresetsPresetOrderChange.bl_idname, text="", icon='TRIA_DOWN').direction = 'DOWN'

            rowRight = layout.row()
            rowRight.template_list("ZBBQ_UL_Presets", "zbv_ul_presets_main", bpg, "bevelPresets", bpg, "bevelPresetsIndex", rows=6, sort_lock=True)

            # row.operator(ZBBQ_OT_SmartSelectByRadiusFromActivePreset.bl_idname)

            # if panelWidth < ZBBQ_Consts.refPanelWidth:
            #     row.scale_x = ZBBQ_Consts.refPanelWidth*0.2/panelWidth
            # else:
            #     row.scale_x = 0.2

            # row.operator(ZBBQ_OT_UI_ShowPreferences.bl_idname, text="  ", icon="PREFERENCES")

            rowRight = layout.row()
            rowRight.scale_y = 2

            rowRight.operator(ZBBQ_OT_RenderPreviewToggle.bl_idname, depress=ZBBQ_CommonFunc.IsRenderPreviewActive(), icon='HIDE_OFF')

            rowRight = layout.row()

            col = rowRight.column()

            toggleNodeTreeName = ZBBQ_Consts.shaderNodeTreePreviewMetallicName  # To-Do: Normal to color mode

            previewShaderNodeToggleModeAndObjects = []
            if context.mode == 'EDIT_MESH':
                previewShaderNodeToggleModeAndObjects = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(context.objects_in_mode, toggleNodeTreeName, 'OVERRIDE')
            elif context.mode == 'OBJECT':
                previewShaderNodeToggleModeAndObjects = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(context.selected_objects, toggleNodeTreeName, 'OVERRIDE')

            previewShaderNodeToggleDepress = previewShaderNodeToggleModeAndObjects['toggleMode'] == 'OFF' and len(previewShaderNodeToggleModeAndObjects['objectsToToggle']) > 0

            col.operator(ZBBQ_OT_PreviewShaderNodeToggle.bl_idname, depress=previewShaderNodeToggleDepress)

            col = rowRight.column()
            col.scale_x = 0.65
            col.prop(context.scene, "ZBBQ_AutoPreviewShaderNodeToggle", text="Auto")

            # layout.operator(ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts.bl_idname)

            # To-Do: Make separate panel for debug
            # self.DrawDebugInfo(context)

        # stats = pstats.Stats(pr)
        # stats.sort_stats(pstats.SortKey.TIME)
        # print('PT Main Draw Stats')
        # stats.print_stats()

    def DrawDebugInfo(self, context):

        layout = self.layout

        layout.operator(ZBBQ_OT_ShaderNodeNormalAdd.bl_idname)
        layout.operator(ZBBQ_OT_ShaderNodeNormalRemove.bl_idname)

        # Readiness for work

        obj = context.active_object

        if ZBBQ_CommonFunc.ObjectIsReadyForBevel(obj):
            layout.label(text="Ready for Zen BBQ!")
        else:
            if not ZBBQ_CommonFunc.ObjectIsConvenient(obj):
                layout.label(text="This object CAN NOT be used for Zen BBQ!")
            else:
                layout.label(text="This object can be used for Zen BBQ!")

                hasDataLayer = ZBBQ_CommonFunc.ObjectHasDataLayerRadius(obj)
                layout.label(text=f'Has Data Layer: {"YES" if hasDataLayer else "NO"}')

                hasMaterial = ZBBQ_MaterialFunc.ObjectHasMaterialsFilled(obj)
                layout.label(text=f'Has Material: {"YES" if hasMaterial else "NO"}')

                if hasMaterial:
                    hasShaderNode = ZBBQ_MaterialFunc.ObjectHasShaderNodeNormal(obj)
                    layout.label(text=f'Has Sahder Node: {"YES" if hasShaderNode else "NO"}')

        layout.label(text=f"Current scene unit system: {bpy.context.scene.unit_settings.system}")
        layout.label(text=f"Current scene unit scale: {bpy.context.scene.unit_settings.scale_length}")

        layout.operator(ZBBQ_OT_ActiveObjectGetReady.bl_idname)

        layout.prop(ZBBQ_CommonFunc.GetPrefs(), "smartSelectRadiusThreshold")


class ZBBQ_PT_Main_Sub_Quality(Panel):
    bl_idname = "ZBBQ_PT_Main_Sub_Quality"
    bl_parent_id = "ZBBQ_PT_Main"
    bl_label = "Preview Render Quality"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zen BBQ'
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        DrawPreviewRenderPresetsSwitch(layout)


class ZBBQ_PT_Main_Sub_Advanced(Panel):
    bl_idname = "ZBBQ_PT_Main_Sub_Advanced"
    bl_parent_id = "ZBBQ_PT_Main"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zen BBQ'
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        layout = self.layout
        layout.label(text=ZBBQ_Labels.ZBBQ_PROP_IntactBevelDisplayRadius_Label)

        # bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()

        # TODO: ERROR: rna_uiItemR: property not found: Object.["ZenBBQ_IntactBevelRadius"]
        if(len(bpy.context.selected_objects) == 0):
            layout.label(text="(Please select an object)")
        else:
            objectsSelectedAndReadyForBevel = [obj for obj in bpy.context.selected_objects if ZBBQ_CommonFunc.ObjectIsReadyForBevel(obj)]
            if(len(objectsSelectedAndReadyForBevel) == 1):
                # layout.label(text=f"for: {len(objectsSelectedAndreadyForBevel)} selected objects:")
                # layout.prop(objectsSelectedAndReadyForBevel[0], f'["{ZBBQ_Consts.customPropertyIntactBevelRadiusName}"]', text="")

                row = layout.row()

                col = row.column()
                col.prop(objectsSelectedAndReadyForBevel[0], "ZBBQ_IntactBevelDisplayRadius", text="")

                col = row.column()
                col.scale_x = 0.65
                col.prop(objectsSelectedAndReadyForBevel[0], "ZBBQ_IntactBevelDisplayUnits", text="")
            else:
                if(len(objectsSelectedAndReadyForBevel) == 0):
                    layout.label(text="(No ZenBBQ in selection)")
                else:
                    layout.label(text="(Please select one object)")


# class ZBBQ_PT_Main_Sub_Advanced(Panel):
#     bl_idname = "ZBBQ_PT_Main_Sub_Advanced"
#     bl_parent_id = "ZBBQ_PT_Main"
#     bl_label = "Advanced"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = 'Zen BBQ'
#     bl_options = {"DEFAULT_CLOSED"}

#     def draw(self, context):
#         layout = self.layout

#         previewShaderNodeToggleModeAndObjects = []
#         if context.mode == 'EDIT_MESH':
#             previewShaderNodeToggleModeAndObjects = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(context.objects_in_mode, ZBBQ_Consts.shaderNodeTreeNormalName)
#         elif context.mode == 'OBJECT':
#             previewShaderNodeToggleModeAndObjects = ZBBQ_MaterialFunc.ShaderNodeToggleModeAndObjects(context.selected_objects, ZBBQ_Consts.shaderNodeTreeNormalName)

#         previewShaderNodeToggleDepress = previewShaderNodeToggleModeAndObjects['toggleMode'] == 'OFF' and len(previewShaderNodeToggleModeAndObjects['objectsToToggle']) > 0

#         layout.operator(ZBBQ_OT_ShaderNodeNormalToggle.bl_idname, depress=previewShaderNodeToggleDepress)

class ZBBQ_PT_Bake(Panel):

    bl_idname = "ZBBQ_PT_Bake"
    bl_label = "Bake"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zen BBQ'

    @classmethod
    def poll(cls, context):
        if context.mode in {'EDIT_MESH', 'OBJECT'}:
            return True
        return False

    def draw(self, context: bpy.types.Context):

        layout = self.layout

        p_scene = context.scene

        layout.prop(p_scene, "ZBBQ_BakeImageWidth")
        layout.prop(p_scene, "ZBBQ_BakeImageHeight")

        layout.label(text="Save baked files to:")

        b_is_bake_dir_valid = ZBBQ_Bake.BakeFolderIsValid()

        r = layout.row(align=False)
        r.alert = not b_is_bake_dir_valid
        r1 = r.row(align=True)
        r1.prop(p_scene, "ZBBQ_BakeSaveToFolder", text='')
        r2 = r.row(align=True)
        r2.alignment = 'RIGHT'
        r2.prop(p_scene, "ZBBQ_BakeSaveToFolderExpand", text="", icon_only=True)

        if p_scene.ZBBQ_BakeSaveToFolderExpand != p_scene.ZBBQ_BakeSaveToFolder:
            layout.label(text=p_scene.ZBBQ_BakeSaveToFolderExpand)

        if not ZBBQ_Bake.BakeFolderIsValid():
            layout.label(text="Please choose a valid path!")

        layout.prop(p_scene, 'ZBBQ_BakeImageName')

        layout.operator(ZBBQ_OT_BakeOpenFolder.bl_idname)
        layout.operator(ZBBQ_OT_BakeStart.bl_idname)




class ZBBQ_PT_Preferences(Panel):

    bl_idname = "ZBBQ_PT_Preferences"
    bl_label = "Preferences"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zen BBQ'

    @classmethod
    def poll(cls, context):
        if context.mode in {'EDIT_MESH', 'OBJECT'}:
            return True
        return False

    def draw(self, context):

        layout = self.layout

        layout.operator(ZBBQ_OT_Keymaps.bl_idname, icon_value=ZBBQ_Icons['Addon-Logo'].id())
        layout.operator(ZBBQ_OT_ResetPreferences.bl_idname)
        layout.operator(ZBBQ_OT_MaterialsRepair.bl_idname)
        layout.operator(ZBBQ_OT_GlobalAddonCleanup.bl_idname)
        # layout.label(text="Other Settings:")
        # layout.prop(ZBBQ_CommonFunc.GetPrefs(), "cyclesActivatingConfirmation", text="Ask before switching to Cycles")


class ZBBQ_PT_Preferences_Sub_Common(Panel):
    bl_idname = "ZBBQ_PT_Preferences_Sub_Common"
    bl_parent_id = "ZBBQ_PT_Preferences"
    bl_label = "Common"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zen BBQ'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        prefs = ZBBQ_CommonFunc.GetPrefs()

        layout = self.layout
        layout.prop(prefs, "smartSelectRadiusThreshold")
        layout.prop(prefs, 'polygonBoundaryLoopOnly')
        layout.prop(prefs, 'cyclesActivatingConfirmation', text=ZBBQ_Labels.ZBBQ_Prefs_Prop_CyclesActivatingConfirmation_NameShort)


class ZBBQ_PT_Help(bpy.types.Panel):
    bl_space_type = ZsUiConstants.ZSTS_SPACE_TYPE
    bl_idname = "ZBBQ_PT_Help"
    bl_label = "Help"
    bl_region_type = ZsUiConstants.ZSTS_REGION_TYPE
    bl_category = ZsUiConstants.ZSTS_PANEL_CATEGORY

    @classmethod
    def poll(cls, context):
        if context.mode not in {'EDIT_MESH', 'OBJECT'}:
            return False

        return True

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=False)

        row = col.row(align=True)
        row.operator(
            "wm.url_open",
            text=ZBBQ_Labels.PANEL_HELP_DOC_LABEL,
            icon="HELP"
        ).url = ZBBQ_Labels.PANEL_HELP_DOC_LINK
        row = col.row(align=True)
        row.operator(
            "wm.url_open",
            text=ZBBQ_Labels.PANEL_HELP_DISCORD_LABEL,
            icon_value=ZBBQ_Icons['Discord-Logo-White_32'].id()
        ).url = ZBBQ_Labels.PANEL_HELP_DISCORD_LINK
        
        try:
            row = layout.row(align=True)
            row.label(text='Version: ' + ZBBQ_CommonFunc.GetAddonVersion())
        except Exception:
            print('Zen BBQ: No version found. There may be several versions installed. Try uninstalling everything and installing the latest version.')

        addon_prefs = ZBBQ_CommonFunc.GetPrefs()
        box = layout.box()
        addon_prefs.demo.draw(box, context)

        


class ZBBQ_PT_Debug(bpy.types.Panel):
    bl_space_type = ZsUiConstants.ZSTS_SPACE_TYPE
    bl_idname = "ZBBQ_PT_Debug"
    bl_label = "Debug"
    bl_region_type = ZsUiConstants.ZSTS_REGION_TYPE
    bl_category = ZsUiConstants.ZSTS_PANEL_CATEGORY

    @classmethod
    def poll(cls, context):
        if context.mode not in {'EDIT_MESH', 'OBJECT'}:
            return False

        return True

    def draw(self, context):
        layout = self.layout

        # DBG Quick Action for testing purposes
        layout.label(text="Debug purposes only:")
        layout.operator(ZBBQ_OT_BakeNormalForSelection.bl_idname)
        layout.operator(ZBBQ_OT_MaterialsRepair.bl_idname)
        layout.operator(ZBBQ_OT_TestOpA.bl_idname)
        layout.operator(ZBBQ_OT_TestOpB.bl_idname)

        # layout.label(text=f"Is user config set? {bpy.context.scene.ZBBQ_PreviewRenderUserConfig.isSet}")
        # layout.label(text=f"ZBBQ_PreviewRenderConfigIsStandard? {ZBBQ_PreviewRenderConfigStandard.CompareWithCurrent()}")

        layout.prop(bpy.context.scene, "ZBBQ_HasPresetsIncluded")
        layout.label(text=f"displaySceneIncludedBevelPresets {ZBBQ_Globals.displaySceneIncludedBevelPresets}")

        bpgi = bpy.context.scene.ZBBQ_PresetsIncluded
        layout.prop(bpgi, "title")

        for i in range(len(bpgi.bevelPresets)):
            bp = bpgi.bevelPresets[i]
            layout.label(text=f"{'[] ' if bpgi.bevelPresetsIndex == i else ''}{bp.colorId} {bp.radius} {bp.units}")

        layout.prop(bpy.context.scene, "ZBBQ_ZenBBQOverlayShow")

        layout.prop(bpy.context.scene, "ZBBQ_OverlayConfigIsStored")
        layout.prop(bpy.context.scene, "ZBBQ_OverlayConfigCreases")
        layout.prop(bpy.context.scene, "ZBBQ_OverlayConfigSharp")
        layout.prop(bpy.context.scene, "ZBBQ_OverlayConfigBevel")
        layout.prop(bpy.context.scene, "ZBBQ_OverlayConfigSeams")

        layout.label(text=f"This is custom icon test. Id: {ZBBQ_Icons['ColorBPosition7'].id()}", icon_value=ZBBQ_Icons['ColorBPosition7'].id())
        layout.label(text=f"Another way to get icon id: {ZBBQ_Colors['ColorA'].iconId()}", icon_value=ZBBQ_Colors['ColorA'].iconId())


def DrawPreviewRenderPresetsSwitch(container):

    # layout.prop(context.window.screen, "ZBBQ_PreviewRenderConfigSwitch", expand=True)

    items = bpy.context.window.screen.bl_rna.properties["ZBBQ_PreviewRenderConfigSwitch"].enum_items_static

    if bpy.context.scene.render.engine == 'CYCLES':

        currentPreviewRenderPresetIdx = ZBBQ_PreviewRenderPresetsGetCurrentIdx(None)
        hasSavedConfig = bpy.context.scene.ZBBQ_PreviewRenderUserConfig.isSet
        matchesSaved = ZBBQ_PreviewRenderPresetsMatchesSaved()

        # print(f"Matches saved? {matchesSaved} Idx? {currentPreviewRenderPresetIdx}")

        row = container.row(align=True)
        for item in items:

            identifier = item.identifier

            if(identifier == "REVERT"):
                if(matchesSaved or currentPreviewRenderPresetIdx == 0):
                    continue

            if(identifier == "CUSTOM"):
                if(not matchesSaved and currentPreviewRenderPresetIdx > 0):
                    continue

            item_layout = row.row(align=True)
            item_layout.prop_enum(bpy.context.window.screen, "ZBBQ_PreviewRenderConfigSwitch", identifier)
            # item_layout.enabled = is_enum_item_available(context, identifier)

            if(identifier == "REVERT"):
                item_layout.enabled = hasSavedConfig

            if(identifier == "CUSTOM" and currentPreviewRenderPresetIdx > 0):
                item_layout.enabled = False

    else:
        row = container.row(align=True)  # Just draw it all grey

        for item in items:

            identifier = item.identifier
            if identifier == "REVERT":
                continue

            item_layout = row.row(align=True)
            item_layout.prop_enum(bpy.context.window.screen, "ZBBQ_PreviewRenderConfigSwitch", identifier)
            item_layout.enabled = False


# === Pie Menus

class ZBBQ_MT_GeometryOptions(Menu):
    bl_idname = "ZBBQ_MT_GeometryOptions"
    bl_label = "Zen BBQ"
    bl_context = "mesh_edit"
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        pie = self.layout.menu_pie()
        # pie.operator(ZBBQ_OT_SwitchShadingMode.bl_idname)
        # pie.operator(ZBBQ_OT_SmartSelectByRadius.bl_idname, text=f"Smart Select (accuracy {ZBBQ_CommonFunc.GetPrefs().smartSelectRadiusThreshold})%").threshold = ZBBQ_CommonFunc.GetPrefs().smartSelectRadiusThreshold

        bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()

        if bpg is None:
            pie.label(text="Please have at least one Preset Group")
        else:

            # Works only with 6 PGs

            # bevelPresetsReSorted = [  # Old order
            #     bpg.bevelPresets[1],
            #     bpg.bevelPresets[4],
            #     bpg.bevelPresets[0],
            #     bpg.bevelPresets[3],
            #     bpg.bevelPresets[2],
            #     bpg.bevelPresets[5],
            # ]

            bevelPresetsReSorted = [
                bpg.bevelPresets[4],
                bpg.bevelPresets[1],
                bpg.bevelPresets[5],
                bpg.bevelPresets[0],
                bpg.bevelPresets[3],
                bpg.bevelPresets[2],
            ]

            idxPresets = 0
            for i in range(len(bpg.bevelPresets)+2):
                if i == 2:
                    if context.mode == 'EDIT_MESH':
                        pie.operator(ZBBQ_OT_PieMenuGeometryOptionsBottom.bl_idname, depress=ZBBQ_CommonFunc.IsRenderPreviewActive(), icon='HIDE_OFF')
                    elif context.mode == 'OBJECT':
                        pie.operator(ZBBQ_OT_RenderPreviewToggle.bl_idname, depress=ZBBQ_CommonFunc.IsRenderPreviewActive(), icon="HIDE_OFF")

                elif i == 3:

                    if context.mode == 'EDIT_MESH':
                        pie.operator(ZBBQ_OT_PieMenuGeometryOptionsTop.bl_idname, icon='RESTRICT_SELECT_OFF')
                    elif context.mode == 'OBJECT':
                        pie.operator(ZBBQ_OT_ObjectAddonCleanup.bl_idname, icon="LOOP_BACK")

                else:

                    bp = bevelPresetsReSorted[idxPresets]
                    unitTitle = bp.getUnitInfo().shortTitle
                    # unitAndSceneScaleMultiplier = bp.unitAndSceneScaleMultiplier()

                    OpSetRadius = pie.operator(ZBBQ_OT_SetBevelRadiusToSelection.bl_idname, text=f"{bp.radius:2g} {unitTitle}", icon_value=ZBBQ_CommonFunc.PieMenuIndexAndColorToPieMenuIconId(i, bp.colorId))
                    OpSetRadius.radius = bp.radius  # *unitAndSceneScaleMultiplier
                    OpSetRadius.units = bp.units

                    idxPresets += 1


class ZBBQ_OT_CallPie_GeometryOptions(Operator):
    bl_idname = "object.zen_bbq_callpie_geometry_options"
    bl_label = ZBBQ_Labels.ZBBQ_OT_CallPie_GeometryOptions_Label
    bl_description = ZBBQ_Labels.ZBBQ_OT_CallPie_GeometryOptions_Desc

    def execute(self, context):

        # if bpy.context.scene.render.engine != 'CYCLES':
        #     bpy.ops.wm.call_menu_pie(name="ZBBQ_MT_SwitchToCycles")
        # else:
        #     bpy.ops.wm.call_menu_pie(name="ZBBQ_MT_GeometryOptions")

        bpy.ops.wm.call_menu_pie(name="ZBBQ_MT_GeometryOptions")

        return {'FINISHED'}


class ZBBQ_UL_Presets(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        panelWidth = 0
        # spaces = 0

        for reg in bpy.context.area.regions:
            if reg.type == "UI":
                panelWidth = reg.width

        propWidth = ZBBQ_Consts.refPanelWidth*0.5/panelWidth
        # spaces = int(0.057*panelWidth)
        # spaces = int(0.035*panelWidth)  # With 1 button
        # spaces = int(0.025*panelWidth)  # With 2 buttons

        if propWidth < 0.25:
            propWidth = 0.25

        if propWidth > 0.5:
            propWidth = 0.5

        rowMain = layout.row(align=True)
        rowMain.label(text="", icon_value=ZBBQ_CommonFunc.ULIndexAndColorToPieMenuIconId(index, item.colorId))
        # rowMain.operator(ZBBQ_OT_DrawHighlight.bl_idname,  text='', icon_value=ZBBQ_CommonFunc.ULIndexAndColorToPieMenuIconId(index, item.colorId))

        rowLeft = rowMain.row(align=True)
        rowRight = rowMain.row(align=True)
        rowRight.alignment = 'RIGHT'

        rowLeftL = rowLeft.row(align=True)
        rowLeftR = rowLeft.row(align=True)

        rowLeftL.scale_x = propWidth
        rowLeftR.scale_x = propWidth

        bpg = ZBBQ_CommonFunc.GetActiveBevelPresetGroup()

        rowLeftL.prop(item, 'radius', text="", emboss=False)  # text=f'{item.radius:2g}
        rowLeftR.prop(item, 'units', text="", emboss=False)  # text=f'{item.radius:2g}

        rowLeftL.enabled = index == bpg.bevelPresetsIndex
        rowLeftR.enabled = index == bpg.bevelPresetsIndex

        rowRight.split(factor=0.5)

        rowRight.separator()

        opAssign = rowRight.operator(ZBBQ_OT_SetBevelRadiusToSelection.bl_idname, text="", icon='LAYER_ACTIVE')
        opAssign.radius = item.radius  # *unitAndSceneScaleMultiplier
        opAssign.units = item.units

        # if index == bpg.bevelPresetsIndex:

        #     rowLeftL.prop(item, 'radius', text="", emboss=False)  # text=f'{item.radius:2g}
        #     rowLeftR.prop(item, 'units', text="", emboss=False)  # text=f'{item.radius:2g}

        #     rowRight.split(factor=0.5)

        #     rowRight.separator()

        #     opAssign = rowRight.operator(ZBBQ_OT_SetBevelRadiusToSelection.bl_idname, text="", icon='LAYER_ACTIVE')
        #     opAssign.radius = item.radius  # *unitAndSceneScaleMultiplier
        #     opAssign.units = item.units

        # else:

        #     # rowLeftL.label(text=spaces*" "+f"{item.radius:2g}")
        #     rowLeftL.label(text=spaces*" "+f"{item.radius:.2f}")
        #     rowLeftR.label(text=f"  {item.getUnitInfo().shortTitle}")

        #     rowRight.split(factor=0.5)

        #     rowRight.separator()

        #     opAssign = rowRight.operator(ZBBQ_OT_SetBevelRadiusToSelection.bl_idname, text="", icon='LAYER_ACTIVE')
        #     opAssign.radius = item.radius  # *unitAndSceneScaleMultiplier
        #     opAssign.units = item.units


classes = [

    ZBBQ_PT_Main,
    ZBBQ_PT_Main_Sub_Quality,
    ZBBQ_PT_Main_Sub_Advanced,
    # ZBBQ_PT_Main_Sub_Advanced,

    # ZBBQ_PT_Bake,

    ZBBQ_PT_Preferences,
    ZBBQ_PT_Preferences_Sub_Common,

    ZBBQ_MT_GeometryOptions,
    ZBBQ_OT_CallPie_GeometryOptions,

    ZBBQ_UL_Presets,
    ZBBQ_PT_Help

]

# classes.append(ZBBQ_PT_Debug)

# === Registration

addonKeymaps = []


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # if bpy.context.window_manager.keyconfigs.addon:

    #     keyMap = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')

    #     keymapItem = keyMap.keymap_items.new(ZBBQ_OT_CallPie_GeometryOptions.bl_idname, 'Z', 'PRESS', ctrl=True, shift=True)
    #     addonKeymaps.append((keyMap, keymapItem))

    # UL for presets

    # print(bpy.context.preferences.addons.keys())
    # print(bpy.context.preferences.addons["ZenBBQ"].preferences)

    # bpy.context.preferences.addons["ZenBBQ"].preferences.zbv_ul_presets = CollectionProperty(type=ZBBQ_LI_Preset)
    # bpy.context.preferences.addons["ZenBBQ"].preferences.zbv_ul_presets_index = IntProperty(name="Index for zbv_ul_presets", default=0)

    # print(bpy.context.preferences.addons["ZenBBQ"].preferences.zbv_ul_presets_index)

    # bpy.types.Scene.zbv_ul_presets = CollectionProperty(type=ZBBQ_LI_Preset)
    # bpy.types.Scene.zbv_ul_presets_index = IntProperty(name="Index for zbv_ul_presets", default=0)

    # bpy.types.Preferences.zbv_ul_presets = CollectionProperty(type=ZBBQ_LI_Preset)
    # bpy.types.Preferences.zbv_ul_presets_index = IntProperty(name="Index for zbv_ul_presets", default=0)


def unregister():

    # for keyMap, keymapItem in addonKeymaps:
    #     keyMap.keymap_items.remove(keymapItem)
    # addonKeymaps.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)
