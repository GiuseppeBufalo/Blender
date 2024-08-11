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

"""
    Zen UV Text Blocks
"""


class ZuvLabels:
    """ Zen UV Labels and text blocks """
    # ADDON
    ADDON_NAME_LABEL = "Zen UV"
    ADDON_NAME = "ZenUV"
    ADDON_ICO = "zen-uv_32"

    ZEN_MODIFIER_KEY_LABEL = "Zen Modifier Key"
    ZEN_MODIFIER_KEY_DESC = "The key is a modifier that is used in combination with a mouse."

    UPDATE_MESSAGE_FULL = """To avoid errors, before upgrading the add-on, Zen UV Core library must be unregistered.
Use the button (Unregister Zen UV Core Library) in Modules Tab first.
Or use the (Update Zen UV) button below.
    """
    UPDATE_MESSAGE_SHORT = "To avoid errors when updating Zen UV, use the button below."
    UPDATE_MESSAGE_SHORT_P02 = "Tip: Select *.zip file containing Zen UV addon."
    UPDATE_WARNING_MAIN_01 = 'During the update of the Add-on, in order to avoid errors,'
    UPDATE_WARNING_MAIN_02 = 'use "Update Zen UV" button below and select *.zip file containing Zen UV Add-on.'
    UPDATE_WARNING_UNREGISTER = "Unregister Zen UV Core if you want to update the Add-on manually."

    # HOPS Section
    HOPS_UV_ACTIVATE_LABEL = "HOps UV Display"
    HOPS_UV_ACTIVATE_DESC = "Display UV's in 3D View using Hard Ops addon"
    HOPS_UV_CONTEXT_LABEL = "Context sensitive"
    HOPS_UV_CONTEXT_DESC = "Enable HOps UV Display if UV Editor is open"
    # PREFERENCES

    PREF_AUTO_PIN_QUADRIFIED_LABEL = "Pin Quadrified"
    PREF_AUTO_PIN_QUADRIFIED_DESC = "Pin Islands after Quadrify Islands operation"

    PREF_ORIENT_TO_WORLD_QUADRIFY_LABEL = "Orient to World Quadrified"
    PREF_ORIENT_TO_WORLD_QUADRIFY_DESC = "Orient Quadrified Islands to the World coordinate system"

    PREF_QUADRIFY_BY_SELECTED_EDGES_LABEL = "By selected Edges"
    PREF_QUADRIFY_BY_SELECTED_EDGES_DESC = """Selected Edges will be used
as Seams during Quadrify Islands operation.
Works only in edge selection mode"""

    PREF_PACK_ENGINE_LABEL = "Pack Engine"
    PREF_PACK_ENGINE_DESC = "Select Pack Engine for Pack Islands operation"
    PREF_PACK_ENGINE_BLDR_LABEL = "Blender Pack"
    PREF_PACK_ENGINE_BLDR_DESC = "Blender Pack Engine"
    PREF_PACK_ENGINE_UVP_LABEL = "UVPackmaster"
    PREF_PACK_ENGINE_UVP_DESC = "UVPackmaster Pack Engine"
    PREF_PACK_ENGINE_UVPACKER_LABEL = "UV-Packer"
    PREF_PACK_ENGINE_UVPACKER_DESC = "UV-Packer Pack Engine"
    PREF_PACK_CUSTOM_LABEL = "Custom"
    PREF_PACK_CUSTOM_DESC = "Any command for execution"

    PREF_PACK_MARGIN_UVPACKER_DESC = "Margin in conventional units. Not percentages or pixels"

    PREF_AVERAGE_BEFORE_PACK_LABEL = "Average Islands Scale"
    PREF_AVERAGE_BEFORE_PACK_DESC = "Average Islands scale before Pack Islands operation"

    PREF_ROTATE_ON_PACK_LABEL = "Rotate Islands"
    PREF_ROTATE_ON_PACK_DESC = "Allow the packer to rotate Islands"

    PREF_FIXED_SCALE_LABEL = "Fixed Scale"
    PREF_FIXED_SCALE_DESC = """Do not scale islands during packing
Packer will return an error if UV islands can't fit into the packing box
Use this if you have already set the texel density"""

    OT_SYNC_TO_UVP_LABEL = "Transfer settings to UVPackmaster"
    OT_SYNC_TO_UVP_DESC = "Transfer Pack settings from Zen UV to UVPackmaster"

    PREF_AUTO_FIT_UV_LABEL = "Auto Fit UV View"
    PREF_AUTO_FIT_UV_DESC = "Automatically Fit and Zoom UV Editor viewport"

    PREF_KEEP_STACKED_LABEL = "Keep Stacked"
    PREF_KEEP_STACKED_DESC = "Keeps stacked islands as they are"

    LOCK_OVERLAPPING_MODE_NAME = 'Lock Overlapping'
    LOCK_OVERLAPPING_MODE_DESC = 'Treat overlapping islands as a single island'

    LOCK_OVERLAPPING_ENABLE_NAME = 'Lock Overlapping Enable'
    LOCK_OVERLAPPING_ENABLE_DESC = 'Treat overlapping islands as a single island'

    LOCK_OVERLAPPING_MODE_DISABLED_DESC = "Overlapping islands won't be locked"
    LOCK_OVERLAPPING_MODE_ANY_PART_DESC = "Two islands will be locked together if only they overlap by any part"
    LOCK_OVERLAPPING_MODE_EXACT_DESC = "Two islands will be locked together only if they have the same bounding boxes in the UV space and have identical area"

    PREF_ZEN_SORT_ISLANDS_LABEL = "Auto Sort Islands"
    PREF_ZEN_SORT_ISLANDS_DESC = "Automatically Sort Islands by Tags. Finished Islands move to the right side from Main UV Tile, Unfinished - to the left"

    PREF_PACK_SORT_ISLANDS_LABEL = "Auto Sort by Finished"
    PREF_PACK_SORT_ISLANDS_DESC = "Pack Only. Automatically Sort Islands by tags Finished/Unfinished"

    PREF_AUTO_PINNED_AS_FINISHED_LABEL = "Auto Mark Finished"
    PREF_AUTO_PINNED_AS_FINISHED_DESC = "Automatically Mark Pinned Islands as Finished"

    PREF_AUTO_FINISHED_TO_PINNED_LABEL = "Pin Finished"
    PREF_AUTO_FINISHED_TO_PINNED_DESC = "Pin Islands after Tag Finished operation"

    PREF_MARGIN_LABEL = "Margin pct"
    PREF_MARGIN_DESC = "Set space between Islands in percentage for Pack Islands operation"
    PREF_MARGIN_PX_LABEL = "Margin px"
    PREF_MARGIN_PX_DESC = "Set space between Islands in pixels for Pack Islands operation"
    PREF_MARGIN_SHOW_PX_LABEL = "Margin in px"
    PREF_MARGIN_SHOW_PX_DESC = "Display margin in pixels for Pack Islands operation"

    PREF_PACK_AF_QUADRIFY_LABEL = "Pack Quadrified"
    PREF_PACK_AF_QUADRIFY_DESC = "Pack Islands after Quadrify Islands operation"

    PREF_QUADRIFY_TAG_FINISHED_LABEL = "Tag as Finished"
    PREF_QUADRIFY_TAG_FINISHED_DESC = "Tag Quadrified island as finished"

    PREF_UPD_SEAMS_AF_QUADRIFY_LABEL = "Mark Borders"
    PREF_UPD_SEAMS_AF_QUADRIFY_DESC = """Mark Island boundaries
after Quadrify Islands operation"""

    # BLENDER PREFERENCES RENAMING
    B_PREF_SHOW_EDGE_SEAMS_LABEL = "Show Seams"
    B_PREF_SHOW_EDGE_SHARP_LABEL = "Show Sharp Edges"
    B_PREF_SHOW_BEVEL_WEIGHTS_LABEL = "Show Bevel Weights"
    B_PREF_SHOW_EDGE_CREASE_LABEL = "Show Crease Edges"

    # OPERATORS

    # Global
    PT_GLOBAL_LABEL = "Zen UV"

    # Uwrap section ================================================
    ZEN_UNWRAP_LABEL = "Zen Unwrap"
    ZEN_UNWRAP_DESC = """Unwrap by Marked edges. If you have selected edges or faces they will be Marked as Seams and/or Sharp edges and Unwrapped after.
Objects without Seams and Edge borders will receive Isometric Projection"""
    ZEN_UNWRAP_ICO = "zen-unwrap_32"

    PREF_UNWRAP_SWITCH_MODE_LABEL = "Switch Seams"
    PREF_UNWRAP_SWITCH_MODE_DESC = "Unmark if selected edges or polygons border have Seams"

    PREF_AUTO_SEAMS_WITH_UNWRAP_LABEL = "Mark Unwrapped"
    PREF_AUTO_SEAMS_WITH_UNWRAP_DESC = "Mark edges or face borders as Seams and/or Sharp edges after Zen Unwrap operation. Not available in the Seam Switch mode"

    PREF_WORK_ON_SELECTED_LABEL = "Unwrap Selected Only"
    PREF_WORK_ON_SELECTED_DESC = "Separate workflow where only Selected Faces\
 will be Unwrapped. It includes warnings and Unwrapping options if nothing is\
 selected"

    PREF_AUTO_TAG_FINISHED_LABEL = "Tag Unwrapped"
    PREF_AUTO_TAG_FINISHED_DESC = "Tag Unwrapped Islands as Finished after Zen Unwrap operation"

    PREF_ZEN_UNWRAP_SORT_ISLANDS_LABEL = "Sort Unwrapped"
    PREF_ZEN_UNWRAP_SORT_ISLANDS_DESC = "Sort Islands by Tags after Zen Unwrap operation. Finished Islands move to the right side from Main UV Tile, Unfinished - to the left"

    PREF_ZEN_UNWRAP_AVG_TD_LABEL = "Averaged Texel Density"
    PREF_ZEN_UNWRAP_AVG_TD_DESC = "Set averaged Texel Density. Not available in the Seam Switch mode or if Pack Unwrapped is On"

    PREF_AUTO_ACTIVATE_UV_SYNC_LABEL = "Auto UV Sync"
    PREF_AUTO_ACTIVATE_UV_SYNC_DESC = "Automatically Activate UV Sync Selection Mode in UV Editor for Zen Unwrap operation"

    PANEL_UNWRAP_METHOD_LABEL = "Unwrap Method:"
    PREF_UNWRAP_METHOD_ANGLE_LABEL = "Angle Based"
    PREF_UNWRAP_METHOD_ANGLE_DESC = "Angle Based Method"
    PREF_UNWRAP_METHOD_CONFORMAL_LABEL = "Conformal"
    PREF_UNWRAP_METHOD_CONFORMAL_DESC = "Conformal Method"

    PREF_PACK_AF_UNWRAP_LABEL = "Pack Unwrapped"
    PREF_PACK_AF_UNWRAP_DESC = "Execute Pack after Zen Unwrap operation. Not available in the Selected Only mode"

    ZEN_UNWRAP_AUTO_MODE_LABEL = "Mark by Angle & Unwrap"
    ZEN_UNWRAP_AUTO_MODE_DESC = "Mark edges as Seams and/or Sharp edges by Angle and Unwrap after "
    ZEN_UNWRAP_NO_SELECT_WARN = "Nothing is selected. The whole object(s) will \
be unwrapped."
    ZEN_UNWRAP_POPUP_MARK_LABEL = "Mark Selected"

    ZEN_UNWRAP_POPUP_LABEL = "Some objects doesn`t have Marked edges or Selection. You can use the following functions:"

    # PREF_UNWRAP_CONFIRM_LABEL = "Unwrap Confirm"
    # PREF_UNWRAP_CONFIRM_DESC = "Confirm Unwrap for the whole object"

    PREF_ZEN_UNWRAP_FILL_HOLES_LABEL = "Fill Holes"
    PREF_ZEN_UNWRAP_FILL_HOLES_DESC = "Virtual fill holes in mesh before unwrapping, to better avoid overlaps and preserve symmetry"

    PREF_ZEN_UNWRAP_CORR_ASPECT_LABEL = "Correct Aspect"
    PREF_ZEN_UNWRAP_CORR_ASPECT_DESC = "Map UVs taking image aspect ratio into account"

    # Mark Section ================================================
    AUTO_MARK_LABEL = "Mark by Angle"
    AUTO_MARK_DESC = "Mark edges as Seams and/or Sharp edges by Angle"

    AUTO_MARK_ANGLE_NAME = "Angle"
    AUTO_MARK_ANGLE_DESC = "Set angle"

    PREF_USE_GLOBAL_MARK_LABEL = "Use Global Mark Settings"
    PREF_USE_GLOBAL_MARK_DESC = "Use Global Mark settings instead of personal per operator"

    PREF_MARK_SHARP_EDGES_LABEL = "Mark Sharp Edges"
    PREF_MARK_SHARP_EDGES_DESC = "Automatically assign Sharp edges"

    PREF_MARK_SEAM_EDGES_LABEL = "Mark Seams"
    PREF_MARK_SEAM_EDGES_DESC = "Automatically assign Seams"

    PREF_MARK_PINNED_LABEL = "Clear Pinned"
    PREF_MARK_PINNED_DESC = "Clear Pinned vertices"

    OT_MARK_LABEL = "Mark"
    OT_MARK_DESC = "Mark selected edges or face borders as Seams and/or \
Sharp edges"
    OT_MARK_ICO = "mark-seams_32"

    OT_UNMARK_LABEL = "Unmark"
    OT_UNMARK_DESC = "Unmark selected edges or face borders as Seams and/or \
Sharp edges"
    OT_UNMARK_ICO = "unmark-seams_32"

    PIE_MARK_SEAMS_TEXT_ADD = " Seams"
    PIE_MARK_SHARP_TEXT_ADD = " Sharp Edges"

    UNMARK_ALL_LABEL = "Unmark All"
    UNMARK_ALL_DESC = "Remove all the Seams and/or Sharp edges from the mesh"

    UNIFIED_MARK_LABEL = "Mark By"
    UNIFIED_MARK_DESC = "Mark and Convert Seams and Sharp"

    MARK_BY_BORDER_LABEL = "Seams by UV Borders"
    MARK_BY_BORDER_DESC = "Mark Seams by existing UV Borders"

    MARK_SHARP_BY_BORDER_LABEL = "Sharp by UV Borders"
    MARK_SHARP_BY_BORDER_DESC = "Mark Sharp by existing UV Borders"

    SELECT_UV_BORDER_LABEL = "Select UV Borders"
    SELECT_UV_BORDER_DESC = "Select existing UV Borders"

    SEAM_BY_OPEN_EDGES_LABEL = "Seams by Open Edges"
    SEAM_BY_OPEN_EDGES_DESC = "Mark Seams by Open Edges. The way that looks in the viewport"

    SEAM_BY_SHARP_LABEL = "Seams by Sharp Edges"
    SEAM_BY_SHARP_DESC = "Mark Seams by existing Sharp edges"

    SHARP_BY_SEAM_LABEL = "Sharp Edges by Seams"
    SHARP_BY_SEAM_DESC = "Mark Sharp edges by existing Seams"

    PREF_MARK_WARN_MES = "Both options (Mark Sharp Edges and Mark Seams) \
are Disabled. Some operators will not produce anything."
    PREF_MARK_WARN_TITLE = "Zen Warning!"

    # Finished Section ====================================================
    SORTING_LABEL = "Sort Islands by Tags"
    SORTING_DESC = "Sort Islands by Tags. Finished Islands move to the right side from Main UV Tile, Unfinished - to the left"
    OT_TAG_FINISHED_LABEL = "Tag Finished"
    OT_TAG_FINISHED_DESC = "Tag Islands as Finished"
    OT_UNTAG_FINISHED_LABEL = "Tag Unfinished"
    OT_UNTAG_FINISHED_DESC = "Tag Islands as Unfinished"
    TAG_FINISHED_COLOR_NAME = "Finished Color"
    TAG_FINISHED_COLOR_DESC = "Finished Islands viewport display color"
    TAG_FINISHED_COLOR_NAME = "Excluded Color"
    TAG_FINISHED_COLOR_DESC = "Excluded Islands viewport display color"
    TAG_UNFINISHED_COLOR_NAME = "Unfinished Color"
    TAG_UNFINISHED_COLOR_DESC = "Unfinished Islands viewport display color"

    OT_FINISHED_SELECT_LABEL = "Select Finished"
    OT_FINISHED_SELECT_DESC = "Select Islands tagged as Finished"
    OT_FINISHED_DISPLAY_LABEL = "Display Finished"
    OT_FINISHED_DISPLAY_DESC = "Display Finished/Unfinished Islands in the viewport"
    OT_EXCL_DISPLAY_LABEL = "Display Excluded"
    OT_EXCL_DISPLAY_DESC = "Display Islands tagged as Excluded from Pack in the viewport"

    OT_STRETCH_DISPLAY_LABEL = "Display Stretch Map"
    OT_STRETCH_DISPLAY_DESC = "Display an angle-based stretching map"

    # Select section ================================================
    SELECT_OVERLAP_LABEL = "Select Overlapped Islands"
    SELECT_OVERLAP_DESC = "Select Overlapped Islands"

    AUTOSMOOTH_LABEL = "Smooth by Sharp (Toggle)"
    AUTOSMOOTH_DESC = "Toggle between Auto Smooth 180° (with sharp edges) and \
regular smooth modes"

    PIN_UV_ISLAND_LABEL = "Pin Islands"
    PIN_UV_ISLAND_DESC = "Select at least one edge/face of the Island(s)"
    PIN_UV_ISLAND_PIN_ACTION_NAME = "Pin Current Island"
    PIN_UV_ISLAND_PIN_ACTION_DESC = "Set Current Island Pinned or Not."
    PIN_UV_ISLAND_ISLAND_COLOR_NAME = "Pin Color"
    PIN_UV_ISLAND_ISLAND_COLOR_DESC = "Color of pinned Island."
    PIN_UV_ISLAND_RAND_COLOR_NAME = "Randomize Color"
    PIN_UV_ISLAND_RAND_COLOR_DESC = "Adds some variations to the current \
color."
    PANEL_PIN_LABEL = "Pin Islands"
    PANEL_UNPIN_LABEL = "Unpin Islands"

    ISOLATE_ISLAND_LABEL = "Isolate Islands (Toggle)"
    ISOLATE_ISLAND_DESC = "Isolate Islands (Toggle) by selected edge/face of the Islands"
    ISOLATE_ISLAND_MES = "Nothing is made. Try to select something."

    # Select Section
    SELECT_ISLAND_LABEL = "Select Islands"
    SELECT_ISLAND_DESC = "Select Islands by selected edge/face of the Islands"

    OT_SELECT_EDGES_SHARP_LABEL = "Select Sharp Edges"
    OT_SELECT_EDGES_SHARP_DESC = "Select Edges Marked as Sharp"

    OT_SELECT_EDGES_SEAM_LABEL = "Select Seams Edges"
    OT_SELECT_EDGES_SEAM_DESC = "Select Edges Marked as Seams"

    OT_SELECT_FLIPPED_ISLANDS_LABEL = "Select Flipped Islands"
    OT_SELECT_FLIPPED_ISLANDS_DESC = "Select Flipped Islands"

    OT_SELECT_SIMILAR_ISLANDS_LABEL = "Select Similar Islands"
    OT_SELECT_SIMILAR_ISLANDS_DESC = "Select Islands similar to selected"

    PREF_OT_SEL_SIMILAR_SELECT_MASTER_LABEL = "Select Primary"
    PREF_OT_SEL_SIMILAR_SELECT_MASTER_DESC = "Select Primary Island"

    PREF_OT_SEL_SIMILAR_SELECT_STACK_LABEL = "Select Similar"
    PREF_OT_SEL_SIMILAR_SELECT_STACK_DESC = "Select Similar"

    OT_SELECT_STACK_PARTS_LABEL = "Select Stack Parts"
    OT_SELECT_STACK_PARTS_DESC = "Select Stack Parts"
    OT_SELECT_STACK_PRIMARY_LABEL = "Select Primary"
    OT_SELECT_STACK_PRIMARY_DESC = """Clear selection and Select Primaries
* (Zen Modifier Key) - Append to existing Selection"""
    OT_SELECT_STACK_REPLICAS_LABEL = "Select Replicas"
    OT_SELECT_STACK_REPLICAS_DESC = """Clear selection and Select Replicas
* (Zen Modifier Key) - Append to existing Selection"""
    OT_SELECT_STACK_SINGLES_LABEL = "Select Singles"
    OT_SELECT_STACK_SINGLES_DESC = """Clear selection and Select Singles
* (Zen Modifier Key) - Append to existing Selection"""

    OT_SEL_BY_DIRECTION_LABEL = "Select Edges By Direction"
    OT_SEL_BY_DIRECTION_DESC = "Select edges by direction"

    # Operator "Select by UV Area" START Block
    OT_SEL_BY_UV_AREA_LABEL = "Select by UV Area"
    OT_SEL_BY_UV_AREA_DESC = "Select faces by their UV area"

    PROP_SEL_BY_UV_AREA_CONDITION_LABEL = "Condition"
    PROP_SEL_BY_UV_AREA_CONDITION_DESC = "Select condition"
    PROP_SEL_BY_UV_AREA_TRESHOLD_LABEL = "With Treshold"
    PROP_SEL_BY_UV_AREA_TRESHOLD_DESC = "Treshold"
    PROP_SEL_BY_UV_AREA_FROM_LABEL = "From Area"
    PROP_SEL_BY_UV_AREA_FROM_DESC = "The initial value of the range"
    PROP_SEL_BY_UV_AREA_TO_LABEL = "To Area"
    PROP_SEL_BY_UV_AREA_TO_DESC = "The final value of the range"
    LABEL_SEL_BY_UV_AREA_DRAW = "Select Faces if their Area is:"

    OT_GET_UV_AREA_LABEL = "Get Selected Area"
    OT_GET_UV_AREA_DESC = "Get the area of the selected. This value is used in the 'Select by UV Area' operator"

    PROP_GET_UV_REAL_LABEL = "Real Area"
    PROP_GET_UV_REAL_DESC = "Real area of the selected faces"

    PROP_GET_UV_MULT_LABEL = "Multiplied Area"
    PROP_GET_UV_MULT_DESC = "Real area of the selected faces multiplied for best convenient usage"

    # Operator "Select by UV Area" END Block

    PANEL_CHECKER_LABEL = "Checker Map"
    ZEN_CHECKER_ICO = "checker_32"
    OT_CHECKER_TOGGLE_LABEL = "Checker Texture (Toggle)"
    OT_CHECKER_TOGGLE_DESC = "Add Checker Texture to the mesh (Toggle)"
    OT_CHECKER_RESET_LABEL = "Reset Checker"
    OT_CHECKER_RESET_DESC = "Reset Zen UV Checker to Default state "
    OT_CHECKER_REMOVE_LABEL = "Remove Checker Nodes"
    OT_CHECKER_REMOVE_DESC = "Remove Checker from the scene materials"

    OT_CHECKER_OPEN_EDITOR_LABEL = "Open Shader Editor"
    OT_CHECKER_OPEN_EDITOR_DESC = "Open Shader Editor with Zen Checker Node"

    CHECKER_PANEL_LABEL = "Checker Texture"
    CHECKER_PRESETS_LABEL = "Zen UV Checker Presets"
    CHECKER_PRESETS_DESC = "Presets of Zen UV Default Checker"

    CHECKER_SHOW_IN_UV_LABEL = "Show Image In UV Editor"
    CHECKER_SHOW_IN_UV_DESC = "Show Image In UV Editor Toggle"

    ZEN_CHECKER_POPUP_LABEL_PART_1 = "Checker Texture is missing in nodes."
    ZEN_CHECKER_POPUP_LABEL_PART_2 = "Best way - Reset Checker to Default state."
    ZEN_CHECKER_POPUP_LABEL_PART_3 = "If you know what Nodes are, you can Open Shader Editor and do it manually."

    TOGGLE_OBJECT_COLOR_LABEL = "Show Pinned Islands (Toggle)"
    TOGGLE_OBJECT_COLOR_DESC = "Show Pinned Islands (Toggle)"

    QUADRIFY_LABEL = "Quadrify Island"
    QUADRIFY_DESC = "Straighten rectangular shaped Island"
    ZEN_QUADRIFY_ICO = "quadrify_32"

    SELECT_EDGE_LOOP_LABEL = "Select Interseams Loop"
    SELECT_EDGE_LOOP_DESC = "Select Edge Loop with Seams respect"

    PANEL_PACK_LABEL = "Pack"
    PACK_LABEL = "Pack Islands"
    PACK_DESC = "Pack all Islands"

    PACK_CONSOLE_OUTPUT_UVP = "Zen UV: Packing UV by UVPackmaster 2..."
    PACK_CONSOLE_OUTPUT_BLDR = "Zen UV: Packing UV by Blender Pack..."
    PACK_CONSOLE_OUTPUT_CUSTOM = "Zen UV: Packing UV by Custom Operator..."
    PACK_CONSOLE_OUTPUT_UVPACKER = "Zen UV: Packing UV by UV-Packer..."

    PANEL_TEXEL_DENSITY_LABEL = "Texel Density"
    TEXEL_DENSITY_LABEL = "Texel Density"
    PROP_TD_DYNAMIC_UPDATE_LABEL = "Auto Sync TD"
    PROP_TD_DYNAMIC_UPDATE_DESC = "Automatically update displayed Texel Density color"
    OT_GET_TEXEL_DENSITY_LABEL = "Get TD"
    OT_GET_TEXEL_DENSITY_DESC = "Get Texel Density from selected Islands"
    OT_SET_TEXEL_DENSITY_LABEL = "Set TD"
    OT_SET_TEXEL_DENSITY_DESC = "Set Texel Density to selected Islands"
    OT_SET_TEXEL_DENSITY_OBJ_DESC = "Set Texel Density to selected Objects"
    OT_GET_UV_COVERAGE_LABEL = "Refresh"
    OT_GET_UV_COVERAGE_DESC = "Recalculate UV Coverage"
    PREF_UNITS_LABEL = "Units"
    PREF_UNITS_DESC = "Texel density calculation units"
    OT_DISPLAY_TD_LABEL = "Show TD"
    OT_DISPLAY_TD_DESC = "Display Balanced Texel Density in Viewport by chosen TD Checker value and colors"
    OT_REFRESH_TD_LABEL = "Refresh TD"
    OT_HIDE_TD_LABEL = "Hide TD"
    OT_HIDE_TD_DESC = "Disable displaying Texel Density in Viewport by chosen TD Checker value and colors"

    OT_SET_CUR_TO_CH_TD_LABEL = "Set to Checker"
    OT_SET_CUR_TO_CH_TD_DESC = "Set Current TD value to Checker TD value"

    PROP_TD_COLOR_TRESHOLD_LABEL = "Threshold"
    PROP_TD_COLOR_TRESHOLD_DESC = "Threshold in percents for TD Checker colors"

    TD_COLOR_EQUAL_LABEL = "Equal"
    TD_COLOR_EQUAL_DESC = "Viewport display color to represent Texel Density equal to TD Checker value"
    TD_COLOR_LESS_LABEL = "Less"
    TD_COLOR_LESS_DESC = "Viewport display color to represent Texel Density less than TD Checker value"
    TD_COLOR_OVER_LABEL = "Over"
    TD_COLOR_OVER_DESC = "Viewport display color to represent Texel Density over than TD Checker value"

    PREF_TEXEL_DENSITY_LABEL = ""
    PREF_TEXEL_DENSITY_DESC = "Texel Density value"
    PREF_TD_CHECKER_LABEL = "TD Checker"
    PREF_TD_CHECKER_DESC = "Texel Density value used for Show TD operation"
    PREF_UV_COVERAGE_LABEL = "UV Coverage:"
    PREF_UV_DENSITY_DESC = "UV Coverage in percents(%)"

    OT_GET_IMAGE_SIZE_ACTIVE_LABEL = "From Active Image"
    OT_GET_IMAGE_SIZE_ACTIVE_DESC = "Get image size from the image displayed in UV Editor"

    PREF_TD_SET_MODE_LABEL = "Set TD Mode"
    PREF_TD_SET_MODE_DESC = "Mode for setting Texel Density"
    PREF_SET_PER_ISLAND_LABEL = "Island Mode"
    PREF_SET_OVERALL_LABEL = "Overall Mode"
    PREF_SET_ASONE_LABEL = "As One"
    PREF_SET_ASONE_DESC = "Sets TD for the entire object as for one island. Preferred method if object has a modifiers"
    PREF_SET_PER_ISLAND_DESC = "Set Texel Density individually for every selected Island"
    PREF_SET_OVERALL_DESC = "Set Texel Density for all selected Islands together"

    PREF_TD_TEXTURE_SIZE_LABEL = "Texture Size"
    PREF_TD_TEXTURE_SIZE_DESC = "Image Size for Texel Density computation"

    PREF_GLOBAL_TEXTURE_SIZE = "Global Texture Size"

    PREF_IMAGE_SIZE_PRESETS_LABEL = "Image Size Presets:"
    PREF_IMAGE_SIZE_PRESETS_DESC = "Image Size Preset"

    # Texel Density Presets TDPR
    PANEL_TDPR_LABEL = "Presets"
    OT_TDPR_SET_LABEL = "Set From Preset"
    OT_TDPR_SET_DESC = "Set TD from active preset to selected Islands"
    OT_TDPR_GET_LABEL = "Get"
    OT_TDPR_GET_DESC = "Get TD from selected Islands to active preset"
    OT_TDPR_GENERATE_LABEL = "Generate"
    OT_TDPR_GENERATE_DESC = "Generate Presets"
    OT_TDPR_CLEAR_LABEL = "Clear"
    OT_TDPR_CLEAR_DESC = "Clear List"
    OT_TDPR_SEL_BY_TD_LABEL = "Select by TD"
    OT_TDPR_SEL_BY_TD_DESC = "Select Islands By Texel Density"

    OT_TDPR_SEL_BY_TD_CLEAR_SEL_LABEL = "Clear selection"
    OT_TDPR_SEL_BY_TD_CLEAR_SEL_DESC = "Clear previous selection"
    OT_TDPR_SEL_BY_TD_SEL_UNDER_LABEL = "Select Underrated"
    OT_TDPR_SEL_BY_TD_SEL_OVER_LABEL = "Select Overrated"
    OT_TDPR_SEL_BY_TD_SEL_VALUE_LABEL = "By Texel Density"

    OT_TDPR_DISPLAY_TD_PRESETS_LABEL = "Show Presets"
    OT_TDPR_DISPLAY_TD_PRESETS_DESC = "Display Presets"
    OT_TDPR_DISPLAY_TD_PRESETS_ONLY_LABEL = "Presets Only"

    PROP_TD_SELECT_TYPE_UNDER_LABEL = "Under Rated"
    PROP_TD_SELECT_TYPE_OVER_LABEL = "Over Rated"
    PROP_TD_SELECT_TYPE_VALUE_LABEL = "By Value"

    # Advanced UV Maps ==================================================
    PT_ADV_UV_MAPS_LABEL = "Advanced UV Maps"
    OT_ADD_UV_MAPS_LABEL = ""
    OT_ADD_UV_MAPS_DESC = """\
- Duplicate active UV Map.
- Hold * (Zen Modifier Key) to apply on all selected objects"""
    OT_REMOVE_UV_MAPS_LABEL = ""
    OT_REMOVE_UV_MAPS_DESC = """\
- Remove active UV Map.
- Hold * (Zen Modifier Key) to apply on all selected objects"""
    OT_SHOW_UV_MAP_LABEL = "Show"
    OT_SHOW_UV_MAP_DESC = "Display selected UV Map"
    OT_CLEAN_REMOVE_UV_MAPS_LABEL = "Clean UV Maps"
    OT_CLEAN_REMOVE_UV_MAPS_DESC = """\
- Remove all inactive UV Maps.
- Hold * (Zen Modifier Key) to apply on all selected objects"""
    OT_RENAME_UV_MAPS_LABEL = "Rename UV Maps"
    OT_RENAME_UV_MAPS_DESC = """\
- Rename all UV Maps using UVChannel_* pattern.
- Hold * (Zen Modifier Key) to apply on all selected objects"""
    OT_SYNC_UV_MAPS_LABEL = "Sync UV Maps IDs"
    OT_SYNC_UV_MAPS_DESC = """\
- Set the same active UV Map index for all selected objects.
- Hold * (Zen Modifier Key) to enable/disable automatic synchronization.
- Blue background - UV Maps are synchronized.
- Red background - UV Maps are desynchronized"""
    OT_AUTO_SYNC_UV_MAPS_LABEL = "Auto Sync UV Maps IDs"
    OT_AUTO_SYNC_UV_MAPS_DESC = """\
Automatically set the same active UV Map
index for all selected objects"""

    OT_COPY_UV_LABEL = "Copy UV"
    OT_COPY_UV_DESC = "Copy the UV coordinates of the selection"

    OT_PASTE_UV_LABEL = "Paste UV"
    OT_PASTE_UV_DESC = "Paste the UV coordinates"

    # Mirror Seam Operator ==========================
    OT_MIRROR_SEAMS_LABEL = "Mirror Seams"
    OT_MIRROR_SEAMS_DESC = "Mirror Seams by axes"

    # Seam Groups =======================================================
    PT_SEAMS_GROUP_LABEL = "Seam Groups"
    OT_SGL_NEW_ITEM_LABEL = "Add a new item"
    OT_SGL_NEW_ITEM_DESC = "Add a new item to the list"
    OT_SGL_DEL_ITEM_LABEL = "Deletes an item"
    OT_SGL_DEL_ITEM_DESC = "Delete the selected item from the list"
    OT_SGL_MOVE_ITEM_LABEL = "Move"
    OT_SGL_MOVE_ITEM_DESC = "Move an item in the list"
    OT_SGL_ASSIGN_ITEM_LABEL = "Assign"
    OT_SGL_ASSIGN_ITEM_DESC = "Assign Seams to selected Seam Group"
    OT_SGL_ACTIVATE_ITEM_LABEL = "Activate"
    OT_SGL_ACTIVATE_ITEM_DESC = "Set Seams from selected Seam Group"
    OT_SGL_ACTIVATE_ITEM_MSG = "Select one of Seams group"

    # STACK =========================================================
    # -- Copy / Paste
    OT_COPY_PARAM_LABEL = "Copy"
    OT_COPY_PARAM_DESC = "Copy parameters of selected Islands/Faces and save them"

    OT_PASTE_PARAM_LABEL = "Paste"
    OT_PASTE_PARAM_DESC = "Paste the parameters saved earlier to selected Islands/Faces"

    PREF_OT_COPY_MODE_LABEL = "Mode"
    PREF_OT_COPY_MODE_DESC = "Copy and save parameters from"
    PREF_OT_COPY_MODE_ISLAND_LABEL = "Island"
    PREF_OT_COPY_MODE_ISLAND_DESC = "Copy and save parameters from the selected Islands"
    PREF_OT_COPY_MODE_FACES_LABEL = "Faces"
    PREF_OT_COPY_MODE_FACES_DESC = "Copy and save parameters from the selected Faces"

    PREF_OT_PASTE_MATCH_LABEL = "Match"
    PREF_OT_PASTE_MATCH_DESC = "Match horizontal or vertical"
    PREF_OT_AREA_MATCH_LABEL = "Area Matching"
    PREF_OT_AREA_MATCH_DESC = "Set strict requirements to Islands Area Matching when Stacking. Disable this option if the Islands have a slightly different Area"

    PREF_OT_PASTE_MATCH_HOR_LABEL = "Horizontally"
    PREF_OT_PASTE_MATCH_HOR_DESC = "Fit Islands horizontally"
    PREF_OT_PASTE_MATCH_VERT_LABEL = "Vertically"
    PREF_OT_PASTE_MATCH_VERT_DESC = "Fit Islands vertically"

    PREF_OT_FIT_REGION_FULL_LABEL = "Full"
    PREF_OT_FIT_REGION_FULL_DESC = "Fit Islands into region by longest side"

    PREF_OT_PASTE_TYPE_LABEL = "Type"
    PREF_OT_PASTE_TYPE_DESC = ""

    PREF_OT_PASTE_TYPE_ISLAND_LABEL = "Islands"
    PREF_OT_PASTE_TYPE_ISLAND_DESC = "Paste parameters to selected Islands"

    PREF_OT_PASTE_TYPE_FACES_LABEL = "Faces"
    PREF_OT_PASTE_TYPE_FACES_DESC = "Paste parameters to selected Faces"

    PREF_OT_PASTE_MATCH_LABEL = "Parameters"
    PREF_OT_PASTE_MATCH_DESC = "Paste individual parameters"

    PREF_OT_PASTE_MATCH_TD_LABEL = "Texel Density"
    PREF_OT_PASTE_MATCH_TD_DESC = "Paste Texel Density parameter to selected Islands"
    PREF_OT_PASTE_MATCH_FIT_LABEL = "Size (Fit Islands)"
    PREF_OT_PASTE_MATCH_FIT_DESC = "Paste Size parameter. Fit selected Islands horizontally or vertically"
    PREF_OT_PASTE_MATCH_NOTHING_LABEL = "Nothing"
    PREF_OT_PASTE_MATCH_NOTHING_DESC = "Do not perform"

    PREF_OT_PASTE_TRANS_MODE_LABEL = "Mode"
    PREF_OT_PASTE_TRANS_MODE_DESC = ""
    PREF_OT_PASTE_TRANS_MODE_STACK_LABEL = "Stack"
    PREF_OT_PASTE_TRANS_MODE_STACK_DESC = "Stack Islands if possible"
    PREF_OT_PASTE_TRANS_MODE_TRANS_LABEL = "Transfer"
    PREF_OT_PASTE_TRANS_MODE_TRANS_DESC = "Transfer individual parameters"

    PREF_OT_PASTE_MOVE_LABEL = "Position"
    PREF_OT_PASTE_MOVE_DESC = "Paste Position paramater if Islands have different geometry"

    # -- Copy / Paste END

    PANEL_STACK_LABEL = "Stack"
    ZEN_STACK_ICO = "stack_32"
    PREF_STACK_MOVE_ONLY_LABEL = "Stack Move Only"
    PREF_STACK_MOVE_ONLY_DESC = "Don't fit Islands. Just move to the same position"
    PREF_STACK_PASTE_ANYWAY_LABEL = "Paste Anyway"
    PREF_STACK_PASTE_ANYWAY_DESC = "Paste Position paramater if Islands have different geometry"
    PT_STACK_GROUP_LABEL = "Manual Stacks"

    PREF_ST_STACK_MODE_ALL_LABEL = "Global Mode"
    PREF_ST_STACK_MODE_ALL_DESC = "Collect all Similar Islands on Stacks"

    PREF_ST_STACKED_COLOR_LABEL = "Stacked Color"
    PREF_ST_STACKED_COLOR_DESC = "Color for displaying already Stacked Islands"

    PREF_ST_STACK_MODE_LABEL = "Stack Mode"
    PREF_ST_STACK_MODE_DESC = "Stacks collect mode"

    PREF_ST_STACK_MODE_SEL_LABEL = "Selected Mode"
    PREF_ST_STACK_MODE_SEL_DESC = "Collect selected Similar Islands on Stacks"

    PREF_ST_STACK_MODE_SIMPLE_LABEL = "Simple Mode"
    PREF_ST_STACK_MODE_SIMPLE_DESC = "Places selected islands in the stack, with no respect for their topology"

    PROP_STACK_DISPLAY_SOLVER_LABEL = "Display Stacks"
    PROP_STACK_DISPLAY_SOLVER_DESC = "Display Stacks"

    PREF_STACK_DISPLAY_MODE_LABEL = "Stack Display Mode"
    PREF_STACK_DISPLAY_MODE_DESC = "Islands type"

    PROP_ENUM_STACK_DISPLAY_SIMILAR_LABEL = "Similar (Static)"
    PROP_ENUM_STACK_DISPLAY_SIMILAR_DESC = "Display all Similar Islands"

    PROP_ENUM_STACK_DISPLAY_SELECTED_LABEL = "Selected"
    PROP_ENUM_STACK_DISPLAY_SELECTED_DESC = "Display Similar Islands by Selected"

    PROP_ENUM_STACK_DISPLAY_STACKED_LABEL = "Stacked"
    PROP_ENUM_STACK_DISPLAY_STACKED_DESC = "Display Stacked Islands"

    PROP_ENUM_STACK_DISPLAY_MASTERS_LABEL = "Primaries"
    PROP_ENUM_STACK_DISPLAY_MASTERS_DESC = "Primary Islands. Without Replicated Islands"

    PROP_ENUM_STACK_DISPLAY_STACKS_LABEL = "Replicas"
    PROP_ENUM_STACK_DISPLAY_STACKS_DESC = "Islands that can be Stacked. Without Primary Islands"

    PROP_ENUM_STACK_DISPLAY_SINGLES_LABEL = "Singles"
    PROP_ENUM_STACK_DISPLAY_SINGLES_DESC = "Islands that don't have Similar Islands"

    OT_ZMS_SELECT_STACK_LABEL = "Select Islands"
    OT_ZMS_SELECT_STACK_DESC = "Select Islands in the Stack"

    OT_ZMS_STACK_LABEL = "Stack"
    OT_ZMS_STACK_DESC = "Collect Similar Islands on Stacks"

    OT_ZMS_UNSTACK_LABEL = "Unstack"
    OT_ZMS_UNSTACK_DESC = "Shift Islands from Stacks in the given direction"

    PREF_UNSTACK_RELATIVE_LABEL = "Iterative Unstack"
    PREF_UNSTACK_RELATIVE_DESC = "Unstack Islands iteratively with moving in given direction"

    PREF_UNSTACK_ENUM_MODE_LABEL = "Mode"
    PREF_UNSTACK_ENUM_MODE_DESC = "Mode to Unstack Islands"

    PREF_UNSTACK_ENUM_MODE_GLOBAL_LABEL = "Global"
    PREF_UNSTACK_ENUM_MODE_GLOBAL_DESC = "Unstack all Similar Islands"
    PREF_UNSTACK_ENUM_MODE_STACKED_LABEL = "Stacked"
    PREF_UNSTACK_ENUM_MODE_STACKED_DESC = "Unstack Stacked Islands"
    PREF_UNSTACK_ENUM_MODE_OVERLAP_LABEL = "Overlapped"
    PREF_UNSTACK_ENUM_MODE_OVERLAP_DESC = "Unstack Overlapped Islands"

    PREF_UNSTACK_BREAK_LABEL = "Break Stacks"
    PREF_UNSTACK_BREAK_DESC = "Shift Islands from Stacks by given increment until all of them will be individually placed"

    PREF_UNSTACK_INCREMENT_LABEL = "Unstack Increment"
    PREF_UNSTACK_INCREMENT_DESC = "Unstack Increment"

    OT_ZMS_ANALYZE_STACK_LABEL = "Analyze Stack"
    OT_ZMS_ANALYZE_STACK_DESC = "Analyze Islands Similarities in the Stack. You can find details in the Zen UV Manual Stack Analyze document in the Text Editor"

    OT_ZMS_ASSIGN_TO_STACK_LABEL = "Add Islands"
    OT_ZMS_ASSIGN_TO_STACK_DESC = "Append selected Islands to the active Stack"
    OT_ZMS_NEW_ITEM_LABEL = "Add"
    OT_ZMS_NEW_ITEM_DESC = "Add new Stack"
    OT_ZMS_DEL_ITEM_LABEL = "Delete"
    OT_ZMS_DEL_ITEM_DESC = "Delete selected Stack"

    OT_ZMS_CLEAR_LIST_LABEL = "Remove All"
    OT_ZMS_CLEAR_LIST_DESC = "Remove all Manual Stacks from selected Objects"

    # ZMS_OT_CollectManualStacks
    OT_ZMS_COLLECT_STACK_LABEL = "Stack"
    OT_ZMS_COLLECT_STACK_DESC = "Collect Islands on Manual Stacks"

    OT_ZMS_COLLECT_STACK_MSG = "Select one of Stacks"
    OT_ZMS_COLLECT_ALL_STACKS_LABEL = "Collect All Stacks"
    OT_ZMS_COLLECT_ALL_STACKS_DESC = "Collect All Stacks"

    # ZMS_OT_Unstack_Manual_Stack
    OT_ZMS_MANUAL_UNSTACK_LABEL = "Unstack"
    OT_ZMS_MANUAL_UNSTACK_DESC = "Shift Islands from Manual Stacks in the given direction"

    PREF_OT_M_UNSTACK_BREAK_LABEL = "Break Stack"
    PREF_OT_M_UNSTACK_BREAK_DESC = "Shift Islands from the Stack by given increment without overlaps"
    PREF_OT_M_UNSTACK_INCREMENT_LABEL = "Unstack Increment"
    PREF_OT_M_UNSTACK_INCREMENT_DESC = "Unstack Increment"
    PREF_OT_M_UNSTACK_SELECTED_LABEL = "Selected Only"
    PREF_OT_M_UNSTACK_SELECTED_DESC = "Selected Only"

    PROP_M_STACK_UI_LIST_SIM_INDEX_LABEL = "Similarity Data"
    PROP_M_STACK_UI_LIST_SIM_INDEX_DESC = "Similarity Data"
    PROP_M_STACK_UI_LIST_MOVE_ONLY_LABEL = "Move Only"
    PROP_M_STACK_UI_LIST_MOVE_ONLY_DESC = "Don't fit Islands. Just move to the same position"

    # ZUV_OT_Select_Stacked
    OT_SELECT_STACKED_LABEL = ""
    OT_SELECT_STACKED_DESC = """Clear Selection and Select Stacked Islands
* (Zen Modifier Key) - Append to existing Selection"""

    # Display System: Scene Properties
    PROP_TAGGED_LABEL = "Display Tagged"
    PROP_TAGGED_DESC = "Display Edges Tagged by Edge.tag"

    PROP_STACKED_LABEL = "Similar (Static)"
    PROP_STACKED_DESC = "Display all Similar Islands"

    PROP_M_STACKED_LABEL = "Display Manual Stacks"
    PROP_M_STACKED_DESC = "Display Manual Stacks (Static)"

    PROP_S_STACKED_LABEL = "Selected"
    PROP_S_STACKED_DESC = "Display Similar Islands by Selected"

    PROP_AST_STACKED_LABEL = "Stacked"
    PROP_AST_STACKED_DESC = "Display Stacked Islands"

    PROP_ST_UV_AREA_ONLY_LABEL = "Only UV Area"
    PROP_ST_UV_AREA_ONLY_DESC = "Display Stacks only in UV area"

    # TRANSFORM =========================================================
    TRANSFORM_LABELS = {
        "MOVE": {
            "tl": {"desc": "Move Islands Up Left", "enable": True, "icon": "tr_control_tl"},
            "tc": {"desc": "Move Islands Up", "enable": True, "icon": "tr_control_tc"},
            "tr": {"desc": "Move Islands Up Right", "enable": True, "icon": "tr_control_tr"},
            "lc": {"desc": "Move Islands Left", "enable": True, "icon": "tr_control_lc"},
            "cen": {"desc": "Disabled", "enable": False, "icon": "tr_control_cen"},
            "rc": {"desc": "Move Islands Right", "enable": True, "icon": "tr_control_rc"},
            "bl": {"desc": "Move Islands Down Left", "enable": True, "icon": "tr_control_bl"},
            "bc": {"desc": "Move Islands Down", "enable": True, "icon": "tr_control_bc"},
            "br": {"desc": "Move Islands Down Right", "enable": True, "icon": "tr_control_br"}
        },
        "SCALE": {
            "tl": {"desc": "Scale Islands from Up Left", "enable": True, "icon": "tr_control_tl"},
            "tc": {"desc": "Scale Islands from Up", "enable": True, "icon": "tr_control_tc"},
            "tr": {"desc": "Scale Islands from Up Right", "enable": True, "icon": "tr_control_tr"},
            "lc": {"desc": "Scale Islands from Left", "enable": True, "icon": "tr_control_lc"},
            "cen": {"desc": "Scale from Center", "enable": True, "icon": "tr_control_cen"},
            "rc": {"desc": "Scale Islands from Right", "enable": True, "icon": "tr_control_rc"},
            "bl": {"desc": "Scale Islands from Down Left", "enable": True, "icon": "tr_control_bl"},
            "bc": {"desc": "Scale Islands from Down", "enable": True, "icon": "tr_control_bc"},
            "br": {"desc": "Scale Islands from Down Right", "enable": True, "icon": "tr_control_br"}
        },
        "ROTATE": {
            "tl": {"desc": "Rotate Islands counterclockwise", "enable": True, "icon": "tr_rotate_tl"},
            "tc": {"desc": "Orient Islands vertically", "enable": True, "icon": "tr_rotate_tc"},
            "tr": {"desc": "Rotate Islands clockwise", "enable": True, "icon": "tr_rotate_tr"},
            "lc": {"desc": "Orient Islands horizontally", "enable": True, "icon": "tr_rotate_lc"},
            "cen": {"desc": "Orient Islands automatically", "enable": True, "icon": "tr_rotate_cen"},
            "rc": {"desc": "Orient Islands horizontally", "enable": True, "icon": "tr_rotate_rc"},
            "bl": {"desc": "Rotate Islands counterclockwise", "enable": True, "icon": "tr_rotate_bl"},
            "bc": {"desc": "Orient Islands vertically", "enable": True, "icon": "tr_rotate_bc"},
            "br": {"desc": "Rotate Islands clockwise", "enable": True, "icon": "tr_rotate_br"}
        },
        "FLIP": {
            "tl": {"desc": "Flip Islands Up Left in X and Y", "enable": True, "icon": "tr_control_tl"},
            "tc": {"desc": "Flip Islands Up in Y", "enable": True, "icon": "tr_control_tc"},
            "tr": {"desc": "Flip Islands Up Right in X and Y", "enable": True, "icon": "tr_control_tr"},
            "lc": {"desc": "Flip Islands Left in X", "enable": True, "icon": "tr_control_lc"},
            "cen": {"desc": "Disabled", "enable": False, "icon": "tr_control_cen"},
            "rc": {"desc": "Flip Islands Right in X", "enable": True, "icon": "tr_control_rc"},
            "bl": {"desc": "Flip Islands Down Left in X and Y", "enable": True, "icon": "tr_control_bl"},
            "bc": {"desc": "Flip Islands Down in Y", "enable": True, "icon": "tr_control_bc"},
            "br": {"desc": "Flip Islands Down Right in X and Y", "enable": True, "icon": "tr_control_br"}
        },
        "FIT": {
            "tl": {"desc": "Fit Islands from Up Left", "enable": True, "icon": "tr_control_tl"},
            "tc": {"desc": "Fit Islands from Up with width X. The length will change proportionally", "enable": True, "icon": "tr_control_tc"},
            "tr": {"desc": "Fit Islands from Up Right", "enable": True, "icon": "tr_control_tr"},
            "lc": {"desc": "Fit Islands from Left with width Y. The length will change proportionally", "enable": True, "icon": "tr_control_lc"},
            "cen": {"desc": "Fit Islands from Center", "enable": True, "icon": "tr_control_cen"},
            "rc": {"desc": "Fit Islands from Right with width Y. The length will change proportionally", "enable": True, "icon": "tr_control_rc"},
            "bl": {"desc": "Fit Islands from Down Left", "enable": True, "icon": "tr_control_bl"},
            "bc": {"desc": "Fit Islands from Down with width X. The length will change proportionally", "enable": True, "icon": "tr_control_bc"},
            "br": {"desc": "Fit Islands from Down Right", "enable": True, "icon": "tr_control_br"}
        },
        "ALIGN": {
            "tl": {"desc": "Align Islands from Up Left in X and Y", "enable": True, "icon": "tr_control_tl"},
            "tc": {"desc": "Align Islands from Up in Y only", "enable": True, "icon": "tr_control_tc"},
            "tr": {"desc": "Align Islands from Up Right in X and Y", "enable": True, "icon": "tr_control_tr"},
            "lc": {"desc": "Align Islands from Left in X only", "enable": True, "icon": "tr_control_lc"},
            "cen": {"desc": "Align Islands to Center in X and Y", "enable": True, "icon": "tr_control_cen"},
            "rc": {"desc": "Align Islands from Right in X only", "enable": True, "icon": "tr_control_rc"},
            "bl": {"desc": "Align Islands from Down Left in X and Y", "enable": True, "icon": "tr_control_bl"},
            "bc": {"desc": "Align Islands from Down in Y only", "enable": True, "icon": "tr_control_bc"},
            "br": {"desc": "Align Islands from Down Right in X and Y", "enable": True, "icon": "tr_control_br"}
        },
        "2DCURSOR": {
            "tl": {"desc": "Set 2D Cursor Up Left", "enable": True, "icon": "tr_control_tl"},
            "tc": {"desc": "Set 2D Cursor Up", "enable": True, "icon": "tr_control_tc"},
            "tr": {"desc": "Set 2D Cursor Up Right", "enable": True, "icon": "tr_control_tr"},
            "lc": {"desc": "Set 2D Cursor Left", "enable": True, "icon": "tr_control_lc"},
            "cen": {"desc": "Set 2D Cursor to Center", "enable": True, "icon": "tr_control_cen"},
            "rc": {"desc": "Set 2D Cursor Right", "enable": True, "icon": "tr_control_rc"},
            "bl": {"desc": "Set 2D Cursor Down Left", "enable": True, "icon": "tr_control_bl"},
            "bc": {"desc": "Set 2D Cursor Down", "enable": True, "icon": "tr_control_bc"},
            "br": {"desc": "Set 2D Cursor Down Right", "enable": True, "icon": "tr_control_br"}
        }
    }
    TR_FILL_NO_PROPORTION_LABEL = "Fill Islands"
    TR_FILL_NO_PROPORTION_DESC = "Fit Islands from Center without keeping proportions"

    PANEL_TRANSFORM_LABEL = "Transform"
    PROP_ENUM_TRANSFORM_DESC = "Transform Type"
    PROP_TRANSFORM_SPACE_LABEL = "Transform space"
    PROP_TRANSFORM_SPACE_DESC = """Switch between Island and Texture-based transforms in 3D View
Texture-based transforms work for Move and Rotation tools only."""
    PROP_TRANSFORM_TYPE_LABEL = "Mode"
    PROP_TRANSFORM_TYPE_DESC = "Transform Mode. Affect Islands or Elements (vertices, edges, polygons)"
    OT_ROTATE_ISLANDS_LABEL = "Transform Islands"
    OT_ROTATE_ISLANDS_DESC = "Performs Rotation of UV islands"
    ROTATE_ISLANDS_CV_ENUM_LABEL = "Rotate CV"
    ROTATE_ISLANDS_CV_ENUM_DESC = "Rotate Islands clockwise"
    ROTATE_ISLANDS_CCV_ENUM_LABEL = "Rotate CCV"
    ROTATE_ISLANDS_CCV_ENUM_DESC = "Rotate Islands counterclockwise"
    PROP_ROTATE_INCREMENT_LABEL = " Rotate Increment"
    PROP_ROTATE_INCREMENT_DESC = "Island rotation angle"

    # Relax
    ZEN_RELAX_ICO = "relax-1_32"
    PROP_RELAX_METHOD_LABEL = "Method"
    PROP_RELAX_METHOD_DESC = "Unwrapping method"

    # Props Distribute Islands
    PROP_FROM_WHERE_LABEL = "Start Point Offset"
    PROP_FROM_WHERE_DESC = "Islands location start point"
    PROP_SORT_TO_LABEL = "Sort by"
    PROP_SORT_TO_DESC = "Sort by"
    PROP_REV_SORT_LABEL = "Reverse"
    PROP_REV_SORT_DESC = "Swap the beginning and end of the line"
    PROP_SORT_MARGIN_LABEL = "Margin"
    PROP_SORT_MARGIN_DESC = "Distance between distributed Islands"
    PROP_SORT_ALIGN_TO_LABEL = "Align to"
    PROP_SORT_ALIGN_TO_DESC = "Alignment options"

    # Props Randomize Transform
    OT_RANDOMIZE_TRANSFORM_LABEL = "Randomize"
    OT_RANDOMIZE_TRANSFORM_DESC = "Randomize Transformation"
    PROP_RAND_TRANS_MODE_LABEL = "Transform Mode"
    PROP_RAND_TRANS_MODE_DESC = "Set transform mode"
    PROP_RAND_POS_LABEL = "Position"
    PROP_RAND_POS_DESC = "Location range"
    PROP_RAND_ROT_LABEL = "Rotation"
    PROP_RAND_ROT_DESC = "Rotation angle range"
    PROP_RAND_SCALE_LABEL = "Scale"
    PROP_RAND_SCALE_DESC = "Scale range"
    PROP_RAND_LOCK_LABEL = "Lock Axes"
    PROP_RAND_LOCK_DESC = "Lock values for uniform transformation over the axes"
    PROP_RAND_SHAKE_LABEL = "Seed"
    PROP_RAND_SHAKE_DESC = "Change transformation in the set ranges by random value"

    OT_ORIENT_TO_EDGE_LABEL = "Orient To Selection"
    OT_ORIENT_TO_EDGE_DESC = "Align Islands in the direction of selection"

    OT_SCALE_LABEL = "Scale"
    OT_SCALE_DESC = "Scale Islands"

    OT_MOVE_LABEL = "Move"
    OT_MOVE_DESC = "Move Islands"

    PROP_MOVE_INCREMENT_LABEL = "Increment"

    OT_FIT_LABEL = "Fit UV"
    OT_FIT_DESC = "Scale Islands to Fit UV space"

    # Props Arrange Islands

    OT_ARRANGE_LABEL = "Arrange"
    OT_ARRANGE_DESC = "Arrange selected islands"

    PROP_ARRANGE_QUANT_U_LABEL = "Quant U"
    PROP_ARRANGE_QUANT_U_DESC = "Divider for UV Area in U direction"
    PROP_ARRANGE_QUANT_V_LABEL = "Quant V"
    PROP_ARRANGE_QUANT_V_DESC = "Divider for UV Area in v direction"

    PROP_ARRANGE_COUNT_U_LABEL = "Count U"
    PROP_ARRANGE_COUNT_U_DESC = "The number of islands in the UV Area range"
    PROP_ARRANGE_COUNT_V_LABEL = "Count V"
    PROP_ARRANGE_COUNT_V_DESC = "The number of islands in the UV Area range"

    PROP_ARRANGE_POSITION_LABEL = "Position"
    PROP_ARRANGE_POSITION_DESC = "Offset for current Position"
    PROP_ARRANGE_LIMIT_LABEL = "Limit"
    PROP_ARRANGE_LIMIT_DESC = "Distribution Limit"

    PROP_ARRANGE_INP_MODE_LABEL = "Mode"
    PROP_ARRANGE_INP_MODE_DESC = "Input mode"

    PROP_ARRANGE_INP_MODE_SIMPL_LABEL = "Simplified"
    PROP_ARRANGE_INP_MODE_ADV_LABEL = "Advanced"

    PROP_ARRANGE_START_FROM_LABEL = "Start from"
    PROP_ARRANGE_START_FROM_DESC = "The position from which the distribution begins"

    PROP_ARRANGE_RANDOMIZE_LABEL = "Randomize"
    PROP_ARRANGE_RANDOMIZE_DESC = "Change transformation in the set ranges by random value"

    PROP_ARRANGE_SEED_LABEL = "Seed"
    PROP_ARRANGE_SEED_DESC = "Change transformation in the set ranges by random value"

    PROP_ARRANGE_SCALE_LABEL = "Scale"
    PROP_ARRANGE_SCALE_DESC = "Changes the scale of each island separately"

    # World Orient operator
    OT_WORLD_ORIENT_LABEL = "World Orient"
    OT_WORLD_ORIENT_DESC = """Rotate Islands the way they are oriented on the Models.
Each method (Organic/Hard Surface) uses a heuristic approach
and correctly orients most of the Islands in its area"""
    PROP_WO_METHOD_LABEL = "Method"
    PROP_WO_METHOD_DESC = "Orientation method"
    PROP_WO_FURTHER_LABEL = "Further orient"
    PROP_WO_FURTHER_DESC = "Further rotation for horizontal or vertical alignment"

    # Sticky UV Editor ==================================================
    STK_UV_ED_OPERATOR_DESC = """ Show/Hide UV Editor on the side of the 3D Viewport.
Hold * (Zen Modifier Key) to open UV Editor in a separate window.
Hold Ctrl + Shift to open Sticky UV Editor Preferences"""

    # Reset Zen UV Preferences ==========================================
    RESET_LABEL = "Reset Preferences"
    RESET_DESC = "Reset preferences to the Default state"
    RESET_MES = "Confirm: Reset Zen UV preferences to Default state?"

    # PIE Menu ==========================================================
    PIE_LABEL = "Zen UV"

    # Main Panel ========================================================
    PANEL_CONTROLS_LABEL = "Controls"

    PANEL_HELP_LABEL = "Help"
    PANEL_OBJECT_MODE_LABEL = "To use Zen UV enter Edit mode."
    PANEL_HELP_DOC_LABEL = "Documentation"
    PANEL_HELP_DOC_LINK = "https://zen-masters.github.io/Zen-UV/"
    PANEL_HELP_DISCORD_LABEL = "Discord"
    PANEL_HELP_DISCORD_LINK = "https://discordapp.com/invite/wGpFeME"
    PANEL_HELP_DISCORD_ICO = "Discord-Logo-White_32"

    PANEL_SELECT_LABEL = "Select"
    PANEL_UNWRAP_LABEL = "Unwrap"
    PANEL_PREFERENCES_LABEL = "Preferences"

    # CLIB
    CLIB_NAME = "Zen UV Core Library"
    PANEL_CLIB_LABEL = "Zen UV Core Library Properties"

    # PIE CALLERS

    PROP_DISPLAY_PIE_ASSIST_LABEL = "Display Pie Assist"
    PROP_DISPLAY_PIE_ASSIST_DESC = "Display Pie Help Assist Panel"

    PROP_PIE_ASSIST_FONT_SIZE_LABEL = "Pie Assist Font Size"
    PROP_PIE_ASSIST_FONT_SIZE_DESC = "Pie Assist Font Size"

    CAL_SEC9_LABEL = "Zen UV Caller Sector 9"
    CAL_SEC9_DESC = """Setup Auto Seams.
ALT - Setup Seams by UV borders"""

    CAL_SEC4_LABEL = "Zen UV Caller Sector 4"
    CAL_SEC4_DESC = """Unmark selected edges or face borders as Seams and/or Sharp edges.
CTRL — Tag selected Islands as Unfinished.
ALT — Remove all the Seams and/or Sharp edges from the mesh"""

    CAL_SEC7_LABEL = "Zen UV Caller Sector 7"
    CAL_SEC7_DESC = """Select Islands by selected edge/face of the Islands.
ALT — Select Overlapped Islands.
CTRL — Select Flipped Islands"""

    CAL_SEC3_LABEL = "Zen UV Caller Sector 3"
    CAL_SEC3_DESC = """Add Checker Texture to the mesh (Toggle).
CTRL — Display Finished Islands (Toggle)"""

    CAL_SEC6_LABEL = "Zen UV Caller Sector 6"
    CAL_SEC6_DESC = """Mark selected edges or face borders as Seams and/or Sharp edges.
CTRL — Tag selected Islands as Finished"""

    CAL_SEC8_LABEL = "Zen UV Caller Sector 8"
    CAL_SEC8_DESC = """Isolate Islands (Toggle) by selected edge/face of the Islands"""

    CAL_SEC2_LABEL = "Zen UV Caller Sector 2"
    CAL_SEC2_DESC = """Unwrap by Marked edges. If you have selected edges or faces they will be Marked as Seams and/or Sharp edges and Unwrapped after..
ALT — Pack all Islands"""

    CAL_SEC1_LABEL = "Zen UV Caller Sector 1"
    CAL_SEC1_DESC = "User Defined Operators"

    PREF_ZEN_SETS_URL_DESC = "Zen Sets: Create and manage Groups of mesh Elements (Verts, Edges, Faces)"
    PREF_ZEN_SETS_URL_LINK = 'https://gumroad.com/l/ZenSets'

    PREF_ZEN_UV_URL_DESC = "Zen UV: Optimize UV mapping workflow"
    PREF_ZEN_UV_URL_LINK = 'https://gumroad.com/l/ZenUV'

    PREF_ZEN_UV_BBQ_URL_DESC = "Zen BBQ: Build Bevels Quickly!"
    PREF_ZEN_UV_BBQ_URL_LINK = 'https://gumroad.com/l/ZenBBQ'

    PREF_ZEN_UV_CHECKER_URL_DESC = "Checker: Check the state of UVs (FREE)"
    PREF_ZEN_UV_CHECKER_URL_LINK = 'https://gumroad.com/l/zenuv_checker'

    PREF_ZEN_UV_TOPMOST_URL_DESC = "Console Top Most: Make the System Console to the TOPMOST window"
    PREF_ZEN_UV_TOPMOST_URL_LINK = 'https://gumroad.com/l/ZenConsoleTopMost'

    AddonZenBBQ = "zen-bbq"
    AddonZenChecker = "checker_32"
    AddonZenSets = "zen-sets"

    PREF_ZEN_CORE_URL_DESC = "Download Zen UV Core Library"
    PREF_ZEN_CORE_URL_LINK = "https://gumroad.com/l/ZenUVCore"


if __name__ == '__main__':
    pass
