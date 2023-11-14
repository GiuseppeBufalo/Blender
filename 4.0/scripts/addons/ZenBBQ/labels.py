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

class ZBBQ_Labels:

    # ============ OPERATORS

    ZBBQ_OT_ActiveObjectGetReady_Label = "Get Active Ready for Zen BBQ"
    ZBBQ_OT_ActiveObjectGetReady_Desc = "Add all required properties to this Object to make it ready for add-on usage"
    ZBBQ_OT_ActiveObjectGetReady_Report = "Getting active Object ready for Zen BBQ!"

    ZBBQ_OT_ShaderNodeNormalAdd_Label = "Add Bevel Normal Node"
    ZBBQ_OT_ShaderNodeNormalAdd_Desc = "Add Bevel Normal Node to Object Materials"

    ZBBQ_OT_ShaderNodeNormalRemove_Label = "Remove Bevel Normal Node"
    ZBBQ_OT_ShaderNodeNormalRemove_Desc = "Remove Bevel Normal Node from Object Materials"

    ZBBQ_OT_ShaderNodeNormalToggle_Label = "Material Bevel Normal Node"
    ZBBQ_OT_ShaderNodeNormalToggle_Desc = "Toggle Add/Remove Bevel Normal Node to/from Object Materials"

    ZBBQ_OT_SetBevelRadiusToSelection_Label = "Set Radius to Selection"
    ZBBQ_OT_SetBevelRadiusToSelection_Desc = "Set Bevel Radius to Selection"
    ZBBQ_OT_SetBevelRadiusToSelection_Prop_Radius_Name = "Bevel Radius"
    ZBBQ_OT_SetBevelRadiusToSelection_Prop_Radius_Desc = "Bevel Radius"
    ZBBQ_OT_SetBevelRadiusToSelection_Prop_Units_Name = "Units"
    ZBBQ_OT_SetBevelRadiusToSelection_Prop_Units_Desc = "Measurement Unit"

    ZBBQ_OT_SetZeroBevelRadiusToSelection_Label = "Set Zero Radius to Selection"
    ZBBQ_OT_SetZeroBevelRadiusToSelection_Desc = "Set Zero Bevel Radius to selected Geometry"

    ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Label = "Smart Select"
    ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Desc = "Select Vertices that have same Bevel Value with selected Geometry, with given threshold"
    ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Prop_ThresholdPrecentage_Name = "% Threshold"
    ZBBQ_OT_SmartSelectByRadiusOfSelectedVerts_Prop_ThresholdPrecentage_Desc = "Selection Accuracy"

    ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Label = "Select by Selected Preset"
    ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Desc = "Select Vertices that have same Bevel Value with selected Preset"
    ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_ThresholdPrecentage_Name = "% Threshold"
    ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_ThresholdPrecentage_Desc = "Selection Accuracy"
    ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_AddToSelection_Name = "Add to Selection"
    ZBBQ_OT_SmartSelectByRadiusFromActivePreset_Prop_AddToSelection_Desc = "Add Selection to currently selected Geometry"

    ZBBQ_OT_PreviewShaderNodeToggle_Label = "Preview Mat Override"
    ZBBQ_OT_PreviewShaderNodeToggle_Desc = "Toggle On/Off Shader Node for Bevel Preview on active Material"

    ZBBQ_OT_SwitchToCycles_Label = "Activate Cycles"
    ZBBQ_OT_SwitchToCycles_Desc = "Set Render Engine to Cycles (required to use this addon)"

    ZBBQ_OT_FixSceneUnitSystem_Label = "Fix Scene Unit System"
    ZBBQ_OT_FixSceneUnitSystem_Desc = "Change Scene Unit System to Unit System of selected Bevel Preset"
    ZBBQ_OT_FixSceneUnitSystem_Confirm = "Will switch Scene Unit System to "

    ZBBQ_OT_RenderPreviewToggle_Label = "Render Preview"
    ZBBQ_OT_RenderPreviewToggle_Desc = "Switch Viewport render type between Solid or Rendered"
    ZBBQ_OT_RenderPreviewToggle_Report_Cycles = "Render Engine was set to Cycles!"
    ZBBQ_OT_RenderPreviewToggle_Confirm_Cycles = "It's required to switch Render Engine to Cycles, "

    ZBBQ_OT_BakeNormalForSelection_Label = "Bake Normal"
    ZBBQ_OT_BakeNormalForSelection_Desc = "Bake Normal for selected Objects"

    ZBBQ_OT_PieMenuGeometryOptionsTop_Label = "Smart Select | Reset Selection"
    ZBBQ_OT_PieMenuGeometryOptionsTop_Desc = "Default: Smart Select\nCTRL: Set Zero Bevel Radius to selected Vertices"

    ZBBQ_OT_PieMenuGeometryOptionsBottom_Label = "Render Preview | Highlight Bevels"
    ZBBQ_OT_PieMenuGeometryOptionsBottom_Desc = "Default: Switch Solid/Rendered\nCTRL: (Edit Mode only) Switch Colored Edges On/Off"
    ZBBQ_OT_PieMenuGeometryOptionsBottom_Report_MeshEditOnly = "Sorry, Bevel Highlight is available only in Edit Mode!"

    ZBBQ_OT_MaterialRepair_Label = "Repair Materials"
    ZBBQ_OT_MaterialRepair_Desc = "Remove all Zen BBQ Nodes for all Materials in Scene and re-add Zen BBQ Bevel Shader Node (if it was present in that Material before)"

    ZBBQ_OT_ObjectAddonCleanup_Label = "Reset Selected Objects"
    ZBBQ_OT_ObjectAddonCleanup_Desc = "Remove all traces of Zen BBQ add-on usage from selected Objects"

    ZBBQ_OT_GlobalAddonCleanup_Label = "Global Cleanup"
    ZBBQ_OT_GlobalAddonCleanup_Desc = "Global Cleanup of Zen BBQ in the entire Scene"
    ZBBQ_OT_GlobalAddonCleanup_Report_Success = "Zen BBQ in scene has been successfully cleaned up!"
    ZBBQ_OT_GlobalAddonCleanup_Confirm = "Global Cleanup of Zen BBQ in the entire Scene, "

    ZBBQ_OT_Keymaps_Label = "Keymap"
    ZBBQ_OT_Keymaps_Desc = "Set Shortcuts for Zen BBQ functions"

    ZBBQ_OT_PresetsPresetGroupAdd_Label = "New Preset Group"
    ZBBQ_OT_PresetsPresetGroupAdd_Desc = "Add new Preset Group"

    ZBBQ_OT_PresetsPresetGroupRemove_Label = "Remove Preset Group"
    ZBBQ_OT_PresetsPresetGroupRemove_Desc = "Remove selected Preset Group"
    ZBBQ_OT_PresetsPresetGroupAdd_Prop_Title_Name = "Title"
    ZBBQ_OT_PresetsPresetGroupAdd_Prop_Title_Desc = "Title for this Preset"
    ZBBQ_OT_PresetsPresetGroupAdd_Prop_Units_Name = "Units"
    ZBBQ_OT_PresetsPresetGroupAdd_Prop_Units_Desc = "Measurement units"

    ZBBQ_OT_PresetsPresetGroupImportFromScene_Label = "Import Preset Group"
    ZBBQ_OT_PresetsPresetGroupImportFromScene_Desc = "Import Preset group from Scene to Preferences"

    ZBBQ_OT_PresetsPresetGroupOrderChange_Label = "Change Preset Group order"
    ZBBQ_OT_PresetsPresetGroupOrderChange_Desc = "Move the selected Preset Group in order"

    ZBBQ_OT_PresetsPresetOrderChange_Label = "Change Preset order"
    ZBBQ_OT_PresetsPresetOrderChange_Desc = "Move selected Preset in order"

    ZBBQ_OT_ResetPreferences_Label = "Reset Preferences"
    ZBBQ_OT_ResetPreferences_Desc = "Reset all Zen BBQ Preferences (including Presets) to Default state"
    ZBBQ_OT_ResetPreferences_Report_Success = "All Zen BBQ Preferences and Presets were reset to defaults!"
    ZBBQ_OT_ResetPreferences_Confirm = "Reset all Preferences and Presets to Default state, "

    ZBBQ_OT_DrawHighlight_Label = "Highlight Bevels Toggle"
    ZBBQ_OT_DrawHighlight_Desc = "Toggle On/Off Highlight Bevels on Objects in Edit Mode"

    # ============ OPERATORS FROM UI

    ZBBQ_OT_CallPie_GeometryOptions_Label = 'Zen BBQ - Pie Menu'
    ZBBQ_OT_CallPie_GeometryOptions_Desc = 'Call the main Zen BBQ Pie Menu'

    # ============ PREFERENCES

    ZBBQ_Pref_BevelPreset_Prop_Radius_Name = "Radius"
    ZBBQ_Pref_BevelPreset_Prop_Radius_Desc = "Radius Value"
    ZBBQ_Pref_BevelPreset_Prop_UnitSystem_Name = "Unit System"
    ZBBQ_Pref_BevelPreset_Prop_UnitSystem_Desc = "Unit System"
    ZBBQ_Pref_BevelPreset_Prop_Units_Name = "Units"
    ZBBQ_Pref_BevelPreset_Prop_Units_Desc = "Measurement Units"
    ZBBQ_Pref_BevelPreset_Prop_ColorId_Name = "Color ID"
    ZBBQ_Pref_BevelPreset_Prop_ColorId_Desc = "Color ID for this Preset"
    ZBBQ_Pref_BevelPreset_Prop_Color_Name = "Color"
    ZBBQ_Pref_BevelPreset_Prop_Color_Desc = "Color for this Preset"

    ZBBQ_Pref_BevelPresetGroup_Prop_Title_Name = "Title"
    ZBBQ_Pref_BevelPresetGroup_Prop_Title_Desc = "Title for this Preset Group"
    ZBBQ_Pref_BevelPresetGroup_Prop_UnitSystem_Name = "Unit System"
    ZBBQ_Pref_BevelPresetGroup_Prop_UnitSystem_Desc = "Unit System"
    ZBBQ_Pref_BevelPresetGroup_Prop_BevelPresetsIndex_Title = "Selected Bevel Preset Index"
    ZBBQ_Pref_BevelPresetGroup_Prop_BevelPresetsIndex_Desc = "Currently selected Bevel Presets Index in UL list"

    ZBBQ_Prefs_Prop_BevelPresetGroupsDropdown_Name = "Bevel Preset Groups"
    ZBBQ_Prefs_Prop_BevelPresetGroupsDropdown_Desc = "Bevel Preset Groups"
    ZBBQ_Prefs_Prop_SmartSelectRadiusThreshold_Name = "Smart Select Accuracy"
    ZBBQ_Prefs_Prop_SmartSelectRadiusThreshold_Desc = "Smart Select Radius Threshold in %"
    ZBBQ_Prefs_Prop_CyclesActivatingConfirmation_Name = "Always confirm before switching to Cycles"
    ZBBQ_Prefs_Prop_CyclesActivatingConfirmation_NameShort = "Ask for switching to Cycles"
    ZBBQ_Prefs_Prop_CyclesActivatingConfirmation_Desc = "Ask before switching to Cycles while assigning Bevel Preset"
    ZBBQ_Prefs_Prop_PolygonBoundaryLoopOnly_Name = "Face Boundary Mode"
    ZBBQ_Prefs_Prop_PolygonBoundaryLoopOnly_Desc = "Assign Values only to Boundary Edges of selected Faces"

    # ============ SETTINGS

    PANEL_HELP_LABEL = "Help"
    PANEL_HELP_DOC_LABEL = "Documentation"
    PANEL_HELP_DOC_LINK = "https://zen-masters.github.io/Zen-BBQ/"
    PANEL_HELP_DISCORD_LABEL = "Discord"
    PANEL_HELP_DISCORD_LINK = "https://discordapp.com/invite/wGpFeME"
    PANEL_HELP_DISCORD_ICO = "Discord-Logo-White_32"

    PREF_ZEN_SETS_URL_DESC = "Zen Sets: Create and manage Groups of Mesh Elements and Collections"
    PREF_ZEN_SETS_URL_LINK = 'https://gumroad.com/l/ZenSets'

    PREF_ZEN_UV_URL_DESC = "Zen UV: Optimize UV mapping workflow"
    PREF_ZEN_UV_URL_LINK = 'https://gumroad.com/l/ZenUV'

    PREF_ZEN_UV_CHECKER_URL_DESC = "Checker: Check the state of UV’s (FREE)"
    PREF_ZEN_UV_CHECKER_URL_LINK = 'https://gumroad.com/l/zenuv_checker'

    PREF_ZEN_UV_TOPMOST_URL_DESC = "Console Top Most: Make the System Console to the TOPMOST window"
    PREF_ZEN_UV_TOPMOST_URL_LINK = 'https://gumroad.com/l/ZenConsoleTopMost'
