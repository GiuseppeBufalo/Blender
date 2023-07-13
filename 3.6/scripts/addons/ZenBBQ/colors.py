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

import json
from dataclasses import dataclass
import os

from mathutils import Vector

from . import ico

jsonNamedColors = os.path.dirname(__file__) + os.sep + 'namedColors.json'

# Reading named colors from json

fileNamedColorsJSON = open(jsonNamedColors)
namedColors = json.load(fileNamedColorsJSON)
fileNamedColorsJSON.close()


@dataclass
class ZBBQ_Color:
    iconName: str = None
    color: Vector = (1, 1, 1)

    def iconId(self):
        return ico.ZBBQ_Icons[self.iconName].id()


def gammaCorrection(color, gamma):

    invGamma = 1.0 / gamma

    return ((color[0]/255.0) ** invGamma, (color[1]/255.0) ** invGamma, (color[2]/255.0) ** invGamma)


ZBBQ_Colors = {}


for color in namedColors:
    ZBBQ_Colors[color] = ZBBQ_Color(color+"Position3", gammaCorrection(namedColors[color], 0.454))
