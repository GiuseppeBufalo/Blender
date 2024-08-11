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

# (c) 2022 Jakub Uhlik

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, FloatVectorProperty
from bpy.types import PropertyGroup
from ..resources.translate import translate


# NOTE: upon ToolTheme instatiation, this is read from its `__init__` and ONLY modified values written into instance.
# NOTE: values NOT user modified are left as they are defined in ToolTheme fields
# NOTE: because only modified are read, default values much MATCH exactly with defaults in ToolTheme fields
# NOTE: ToolTheme fields begin with underscore, props can't begin with underscore, so prop names are the same only without underscore
# NOTE: for fields that depends on `ui_scale` or `ui_line_width`, `*_default` values has to be linked here
# NOTE: prop `name` that does not match any `_name` in ToolTheme are ignored
class SCATTER5_PR_preferences_theme(PropertyGroup, ):
    show_ui: BoolProperty(name="Show", default=False, )
    
    circle_steps: IntProperty(name="Circle Steps", default=32, min=6, description="", )
    
    fixed_radius_default: IntProperty(name="Fixed Radius", default=48, min=24, description="", )
    fixed_center_dot_radius_default: IntProperty(name="Fixed Dot Radius", default=3, min=3, description="", )
    
    no_entry_sign_size_default: IntProperty(name="No Entry Sign Size", default=16, min=16, description="", )
    no_entry_sign_color: FloatVectorProperty(name="No Entry Sign Color", default=(1.0, 1.0, 1.0, 0.5, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    no_entry_sign_thickness_default: IntProperty(name="No Entry Sign Thickness", default=2, min=1, description="", )
    
    default_outline_color: FloatVectorProperty(name="Outline Color", default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    default_outline_color_press: FloatVectorProperty(name="Outline Color Press", default=(1.0, 1.0, 0.5, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    outline_color_eraser: FloatVectorProperty(name="Outline Color Eraser", default=(1.0, 0.5, 0.4, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    outline_color_hint: FloatVectorProperty(name="Outline Color Hint", default=(0.4, 1.0, 1.0, 1.0 / 8, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    outline_color_disabled_alpha: FloatProperty(name="Outline Disabled Alpha", default=1.0 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    outline_color_helper_alpha: FloatProperty(name="Outline Helper Alpha", default=1.0 / 4, min=0.0, max=1.0, subtype='FACTOR', description="", )
    outline_color_gesture_helper_alpha: FloatProperty(name="Outline Gesture Helper Alpha", default=1.0 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    outline_color_falloff_helper_alpha: FloatProperty(name="Outline Falloff Helper Alpha", default=1.0 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    
    outline_thickness_default: IntProperty(name="Outline Thickness", default=2, min=1, description="", )
    outline_thickness_helper_default: IntProperty(name="Outline Helper Thickness", default=1, min=1, description="", )
    outline_dashed_steps_multiplier: IntProperty(name="Outline Dashed Steps Multiplier", default=2, min=1, description="", )
    
    default_fill_color: FloatVectorProperty(name="Fill Color", default=(1.0, 1.0, 1.0, 0.05, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    default_fill_color_press: FloatVectorProperty(name="Fill Color Press", default=(1.0, 1.0, 0.5, 0.05, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    fill_color_press_eraser: FloatVectorProperty(name="Fill Color Eraser", default=(1.0, 0.5, 0.4, 0.05, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    fill_color_helper_hint: FloatVectorProperty(name="Fill Color Hint", default=(0.4, 1.0, 1.0, 0.05 / 16, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    fill_color_disabled_alpha: FloatProperty(name="Fill Disabled Alpha", default=0.05 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    fill_color_helper_alpha: FloatProperty(name="Fill Helper Alpha", default=0.05 / 4, min=0.0, max=1.0, subtype='FACTOR', description="", )
    fill_color_gesture_helper_alpha: FloatProperty(name="Fill Gesture Helper Alpha", default=0.05 * 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    
    text_size_default: IntProperty(name="Text Size", default=11, min=11, description="", )
    text_color: FloatVectorProperty(name="Text Color", default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    text_tooltip_outline_color: FloatVectorProperty(name="Tooltip Outline Color", default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    text_tooltip_background_color: FloatVectorProperty(name="Tooltip Background Color", default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    text_tooltip_outline_thickness: IntProperty(name="Tooltip Outline Thickness", default=2, min=1, description="", )
    
    point_size_default: IntProperty(name="Point Size", default=4, min=1, description="", )
    
    grid_overlay_size: IntProperty(name="Overlay Grid Size", default=1, min=1, description="", )
    grid_overlay_color_a: FloatVectorProperty(name="Overlay Grid Color A", default=(0.0, 0.0, 0.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    grid_overlay_color_b: FloatVectorProperty(name="Overlay Grid Color B", default=(0.0, 0.0, 0.0, 0.25, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    info_box_scale: FloatProperty(name="Infobox Scale", default=1.0, min=1.0, description="", )
    info_box_shadow_color: FloatVectorProperty(name="Infobox Shadow Color", default=(0.0, 0.0, 0.0, 0.5, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_fill_color: FloatVectorProperty(name="Infobox Fill Color", default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_outline_color: FloatVectorProperty(name="Infobox Outline Color", default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_outline_thickness_default: IntProperty(name="Infobox Outline Thickness", default=2, min=1, description="", )
    info_box_logo_color: FloatVectorProperty(name="Infobox Logo Color", default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_text_header_color: FloatVectorProperty(name="Infobox Text Header Color", default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_text_body_color: FloatVectorProperty(name="Infobox Text Body Color", default=(0.8, 0.8, 0.8, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )


classes = (
    SCATTER5_PR_preferences_theme,
)
