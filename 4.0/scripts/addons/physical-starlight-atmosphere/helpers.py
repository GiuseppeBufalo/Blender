# ##### BEGIN GPL LICENSE BLOCK #####
# Physical Starlight and Atmosphere is is a completely volumetric procedural
# sky, sunlight, and atmosphere simulator addon for Blender
# Copyright (C) 2022  Physical Addons

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ##### END GPL LICENSE BLOCK #####


import math
import addon_utils

class Helpers:
    #  function to clamp rgb values
    @staticmethod
    def clamp(val, valMin, valMax):
        return max(min(val, valMax), valMin)

    #  smooth interpolation by AMD
    @staticmethod
    def smoothstep(val, edge0, edge1):
        #  Scale, bias and saturate x to 0..1 range
        x = Helpers.clamp((val - edge0) / (edge1 - edge0), 0.0, 1.0)
        #  Evaluate polynomial
        return x * x * x * (x * (x * 6 - 15) + 10)  # smootherstep by Ken Perlin

    @staticmethod
    def gamma_correction(val, gamma):
        return float(math.pow(val, 1.0/gamma))

    @staticmethod
    def convert_K_to_RGB(colour_temperature):
        """
        Converts from K to RGB, algorithm courtesy of
        http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
        """
        # range check
        if colour_temperature < 1000:
            colour_temperature = 1000
        elif colour_temperature > 40000:
            colour_temperature = 40000

        tmp_internal = colour_temperature / 100.0

        # red
        if tmp_internal <= 66:
            red = 255
        else:
            tmp_red = 329.698727446 * math.pow(tmp_internal - 60, -0.1332047592)
            if tmp_red < 0:
                red = 0
            elif tmp_red > 255:
                red = 255
            else:
                red = tmp_red

        # green
        if tmp_internal <=66:
            tmp_green = 99.4708025861 * math.log(tmp_internal) - 161.1195681661
            if tmp_green < 0:
                green = 0
            elif tmp_green > 255:
                green = 255
            else:
                green = tmp_green
        else:
            tmp_green = 288.1221695283 * math.pow(tmp_internal - 60, -0.0755148492)
            if tmp_green < 0:
                green = 0
            elif tmp_green > 255:
                green = 255
            else:
                green = tmp_green

        # blue
        if tmp_internal >= 66:
            blue = 255
        elif tmp_internal <= 19:
            blue = 0
        else:
            tmp_blue = 138.5177312231 * math.log(tmp_internal - 10) - 305.0447927307
            if tmp_blue < 0:
                blue = 0
            elif tmp_blue > 255:
                blue = 255
            else:
                blue = tmp_blue

        return red/255, green/255, blue/255


def current_addon_version():
    # This can definitely be done better
    av = (-1, -1, -1)
    addon_versions = [addon.bl_info.get('version', (-1,-1,-1)) for addon in addon_utils.modules() if addon.bl_info['name'] == 'Physical Starlight and Atmosphere']
    if len(addon_versions) > 0:
        av = addon_versions[0]
    return av
