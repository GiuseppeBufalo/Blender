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
import numpy as np

# DONE: link infobox anf grid to theme
# DONE: unify infobox colors with theme (especially infobox outline)

# NOTE: `ToolTheme` field value has to be the same as default `.config.SCATTER5_PR_preferences_theme` property value to work properly


class ToolTheme():
    # NOTE: if False, color is always default
    USE_TOOL_CATEGORY_FOR_COLORS = False
    # NOTE: of category colors are True, if True, press color is brighter and bit more saturated
    USE_ADJUST_COLOR_PRESS_STATE = False
    
    _circle_steps = 32
    # _circle_dot_2d_steps = 16
    # _circle_dot_2d_radius = 3
    
    # NOTE: this block depends on `ui_scale`, in `__init__`, `_default` should be multiplied by `ui_scale`
    _fixed_radius_default = 48
    _fixed_center_dot_radius_default = 3
    _no_entry_sign_size_default = 16
    # this block will be modified in `__init__` and is to be used in widget code
    _fixed_radius = _fixed_radius_default * 1.0
    _fixed_center_dot_radius = _fixed_center_dot_radius_default * 1.0
    _no_entry_sign_size = _no_entry_sign_size_default * 1.0
    
    _no_entry_sign_color = (1.0, 1.0, 1.0, 0.5, )
    
    # NOTE: this block depends on `ui_line_width`, in `__init__`, `_default` should be multiplied by `ui_line_width`
    _no_entry_sign_thickness_default = 2
    # this block will be modified in `__init__` and is to be used in widget code
    _no_entry_sign_thickness = _no_entry_sign_thickness_default * 1
    
    # NOTE: main colors for types
    # NOTE: blender color picker values are in linear, but i need srgb for display, so do approximate correction..
    # green
    _base_color_create = tuple((np.array((0.215861, 0.679543, 0.386429, ), dtype=float, ) ** (1 / 2.2)).tolist())
    # red
    _base_color_destroy = tuple((np.array((0.64448, 0.187821, 0.147027, ), dtype=float, ) ** (1 / 2.2)).tolist())
    # grey
    # _base_color_translate = tuple((np.array((0.40724, 0.40724, 0.40724, ), dtype=float, ) ** (1 / 2.2)).tolist())
    _base_color_translate = tuple((np.array((0.6, 0.6, 0.6, ), dtype=float, ) ** (1 / 2.2)).tolist())
    # blue
    _base_color_rotate = tuple((np.array((0.274677, 0.48515, 0.679543, ), dtype=float, ) ** (1 / 2.2)).tolist())
    # yellow
    _base_color_scale = tuple((np.array((0.679543, 0.564712, 0.168269, ), dtype=float, ) ** (1 / 2.2)).tolist())
    # violet
    _base_color_special = tuple((np.array((0.533277, 0.391573, 0.64448, ), dtype=float, ) ** (1 / 2.2)).tolist())
    
    a = 1.0
    # NOTE: default colors, replaced by getter
    _default_outline_color = (1.0, 1.0, 1.0, a, )
    _default_outline_color_press = (1.0, 1.0, 0.5, a, )
    _outline_color_eraser = (1.0, 0.5, 0.4, a, )
    _outline_color_helper_hint = (0.4, 1.0, 1.0, a / 8, )
    
    _outline_color_disabled_alpha = a / 2
    _outline_color_helper_alpha = a / 4
    _outline_color_gesture_helper_alpha = a / 2
    _outline_color_falloff_helper_alpha = a / 2
    del a
    
    # NOTE: this block depends on `ui_line_width`, in `__init__`, `_default` should be multiplied by `ui_line_width`
    _outline_thickness_default = 2
    _outline_thickness_helper_default = 1
    # this block will be modified in `__init__` and is to be used in widget code
    _outline_thickness = _outline_thickness_default * 1
    _outline_thickness_helper = _outline_thickness_helper_default * 1
    
    _outline_dashed_steps_multiplier = 2
    
    a = 0.05
    # NOTE: default colors, replaced by getter
    _default_fill_color = (1.0, 1.0, 1.0, a, )
    _default_fill_color_press = (1.0, 1.0, 0.5, a, )
    _fill_color_eraser = (1.0, 0.5, 0.4, a, )
    _fill_color_helper_hint = (0.4, 1.0, 1.0, a / 16, )
    
    _fill_color_disabled_alpha = a / 2
    _fill_color_helper_alpha = a / 4
    _fill_color_gesture_helper_alpha = a * 2
    del a
    
    # NOTE: this block depends on `ui_scale`, in `__init__`, `_default` should be multiplied by `ui_scale`
    _text_size_default = 11
    # this block will be modified in `__init__` and is to be used in widget code
    _text_size = _text_size_default * 1
    
    _text_color = (1.0, 1.0, 1.0, 1.0, )
    # _text_tooltip_outline_color = (1.0, 1.0, 1.0, 1.0, )
    _text_tooltip_outline_color = (0.12, 0.12, 0.12, 0.95, )
    # _text_tooltip_background_color = (0.0, 0.0, 0.0, 0.9, )
    _text_tooltip_background_color = (0.12, 0.12, 0.12, 0.95, )
    
    # NOTE: this block depends on `ui_scale`, in `__init__`, `_default` should be multiplied by `ui_scale`
    _text_tooltip_offset_default = (0, 32, )
    _text_tooltip_outline_thickness_default = 2
    # this block will be modified in `__init__` and is to be used in widget code
    _text_tooltip_offset = (_text_tooltip_offset_default[0] * 1, _text_tooltip_offset_default[1] * 1, )
    _text_tooltip_outline_thickness = _text_tooltip_outline_thickness_default * 1
    
    # for point shader
    # NOTE: this block depends on `ui_scale`, in `__init__`, `_default` should be multiplied by `ui_scale`
    _point_size_default = 4
    # this block will be modified in `__init__` and is to be used in widget code
    _point_size = _point_size_default * 1
    
    # grid overlay
    _grid_overlay_size_default = 1
    _grid_overlay_size = _grid_overlay_size_default * 1
    _grid_overlay_color_a = (0.0, 0.0, 0.0, 1.0, )
    _grid_overlay_color_b = (0.0, 0.0, 0.0, 0.25, )
    
    # infobox
    _info_box_scale = 1.0
    _info_box_shadow_color = (0.0, 0.0, 0.0, 0.5, )
    _info_box_fill_color = (0.12, 0.12, 0.12, 0.95, )
    # _info_box_outline_color = (1.0, 1.0, 1.0, 1.0, )
    _info_box_outline_color = (0.12, 0.12, 0.12, 0.95, )
    _info_box_outline_thickness_default = 2.0
    _info_box_outline_thickness = _info_box_outline_thickness_default * 1
    _info_box_logo_color = (1.0, 1.0, 1.0, 1.0, )
    _info_box_text_header_color = (1.0, 1.0, 1.0, 1.0, )
    _info_box_text_body_color = (0.8, 0.8, 0.8, 1.0, )
    
    @classmethod
    def update_from_preferences(cls, ):
        prefs = bpy.context.preferences.addons["Geo-Scatter"].preferences.manual_theme
        # NOTE: like that i should just get list of modified props.. so default values left as they are.. as long as props and class fields and values match..
        for k in prefs.keys():
            # NOTE: no need for it, class has no `_show_ui` field
            # if(k == 'show_ui'):
            #     # this is just for ui drawing..
            #     continue
            
            # NOTE: prop names are without undescores, otherwise match class fields
            a = '_{}'.format(k)
            if(hasattr(cls, a)):
                setattr(cls, a, prefs[k])
    
    def __init__(self, tool=None, ):
        self.update_from_preferences()
        
        if(tool is None):
            self._tool_id = 'UNDEFINED'
            self._tool_category = 'UNDEFINED'
        else:
            if(hasattr(tool, 'tool_id')):
                self._tool_id = tool.tool_id
            else:
                self._tool_id = 'UNDEFINED'
            if(hasattr(tool, 'tool_category')):
                self._tool_category = tool.tool_category
            else:
                self._tool_category = 'UNDEFINED'
        
        self._ui_scale = bpy.context.preferences.system.ui_scale
        
        self._fixed_radius = self._fixed_radius_default * self._ui_scale
        self._fixed_center_dot_radius = self._fixed_center_dot_radius_default * self._ui_scale
        self._no_entry_sign_size = self._no_entry_sign_size_default * self._ui_scale
        
        self._text_size = self._text_size_default * self._ui_scale
        self._text_tooltip_offset = (self._text_tooltip_offset_default[0] * self._ui_scale, self._text_tooltip_offset_default[1] * self._ui_scale, )
        self._text_tooltip_outline_thickness = self._text_tooltip_outline_thickness_default * self._ui_scale
        
        self._point_size = self._point_size_default * self._ui_scale
        
        self._ui_line_width = bpy.context.preferences.system.ui_line_width
        
        self._outline_thickness = self._outline_thickness_default * self._ui_line_width
        self._outline_thickness_helper = self._outline_thickness_helper_default * self._ui_line_width
        
        self._no_entry_sign_thickness = self._no_entry_sign_thickness_default * self._ui_line_width
        
        self._grid_overlay_size = self._grid_overlay_size_default * self._ui_scale
        
        self._info_box_outline_thickness = self._info_box_outline_thickness_default * self._ui_line_width
    
    # getter private bits :)
    __color_press_contrast = 1.2
    __color_press_brightness = 0.1
    
    @property
    def _outline_color(self, ):
        c = self._tool_category
        d = self._default_outline_color
        if(not self.USE_TOOL_CATEGORY_FOR_COLORS):
            return d
        a = d[3]
        
        if(c == 'CREATE'):
            return self._base_color_create + (a, )
        elif(c == 'DESTROY'):
            return self._base_color_destroy + (a, )
        elif(c == 'TRANSLATE'):
            return self._base_color_translate + (a, )
        elif(c == 'ROTATE'):
            return self._base_color_rotate + (a, )
        elif(c == 'SCALE'):
            return self._base_color_scale + (a, )
        elif(c == 'SPECIAL'):
            return self._base_color_special + (a, )
        else:
            # 'UNDEFINED'
            return d
    
    @property
    def _fill_color(self, ):
        c = self._tool_category
        d = self._default_fill_color
        if(not self.USE_TOOL_CATEGORY_FOR_COLORS):
            return d
        a = d[3]
        
        if(c == 'CREATE'):
            return self._base_color_create + (a, )
        elif(c == 'DESTROY'):
            return self._base_color_destroy + (a, )
        elif(c == 'TRANSLATE'):
            return self._base_color_translate + (a, )
        elif(c == 'ROTATE'):
            return self._base_color_rotate + (a, )
        elif(c == 'SCALE'):
            return self._base_color_scale + (a, )
        elif(c == 'SPECIAL'):
            return self._base_color_special + (a, )
        else:
            # 'UNDEFINED'
            return d
    
    def __adjust(self, rgb, ):
        if(not self.USE_ADJUST_COLOR_PRESS_STATE):
            return rgb
        
        a = np.array(rgb, dtype=float, )
        a = (a - 0.5) * self.__color_press_contrast + 0.5 + self.__color_press_brightness
        a = np.clip(a, 0.0, 1.0, )
        a = tuple(a.tolist())
        return a
    
    @property
    def _outline_color_press(self, ):
        c = self._tool_category
        d = self._default_outline_color_press
        if(not self.USE_TOOL_CATEGORY_FOR_COLORS):
            return d
        a = d[3]
        
        if(c == 'CREATE'):
            return self.__adjust(self._base_color_create) + (a, )
        elif(c == 'DESTROY'):
            return self.__adjust(self._base_color_destroy) + (a, )
        elif(c == 'TRANSLATE'):
            return self.__adjust(self._base_color_translate) + (a, )
        elif(c == 'ROTATE'):
            return self.__adjust(self._base_color_rotate) + (a, )
        elif(c == 'SCALE'):
            return self.__adjust(self._base_color_scale) + (a, )
        elif(c == 'SPECIAL'):
            return self.__adjust(self._base_color_special) + (a, )
        else:
            # 'UNDEFINED'
            return d
    
    @property
    def _fill_color_press(self, ):
        c = self._tool_category
        d = self._default_fill_color_press
        if(not self.USE_TOOL_CATEGORY_FOR_COLORS):
            return d
        a = d[3]
        
        rgb = np.array(d[:3], dtype=float, )
        rgb = (rgb - 0.5) * self.__color_press_contrast + 0.5 + self.__color_press_brightness
        rgb = np.clip(rgb, 0.0, 1.0, )
        d = tuple(rgb.tolist())
        
        if(c == 'CREATE'):
            return self.__adjust(self._base_color_create) + (a, )
        elif(c == 'DESTROY'):
            return self.__adjust(self._base_color_destroy) + (a, )
        elif(c == 'TRANSLATE'):
            return self.__adjust(self._base_color_translate) + (a, )
        elif(c == 'ROTATE'):
            return self.__adjust(self._base_color_rotate) + (a, )
        elif(c == 'SCALE'):
            return self.__adjust(self._base_color_scale) + (a, )
        elif(c == 'SPECIAL'):
            return self.__adjust(self._base_color_special) + (a, )
        else:
            # 'UNDEFINED'
            return d


classes = ()
