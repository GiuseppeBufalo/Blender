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

from array import array
import bpy

from dataclasses import dataclass, field


@dataclass
class ZBBQ_Unit:
    title: str = None
    shortTitle: str = None
    multiplier: float = 1
    unitSystem: str = 'METRIC'
    defaultValues: array = field(default_factory=lambda: [])
    useSceneUnitScale: bool = True

    @staticmethod
    def unitAndSceneScaleMultiplierByUnitsName(unitName):
        return ZBBQ_Units[unitName].unitAndSceneScaleMultiplier()

    def unitAndSceneScaleMultiplier(self):
        result = self.multiplier
        if self.useSceneUnitScale:
            result /= bpy.context.scene.unit_settings.scale_length
        return result


ZBBQ_Units = {

    # Generic Units

    'UNITS':  ZBBQ_Unit('Units', 'units', 1, 'NONE', [1, 2, 3, 5, 7, 10], False),

    # Metric

    'MILLIMETERS': ZBBQ_Unit('Millimeters', 'mm', 0.001,    'METRIC', [1, 2, 3, 5, 7, 10], True),
    'CENTIMETERS': ZBBQ_Unit('Cenitmeters', 'cm', 0.01,     'METRIC', [1, 2, 3, 5, 7, 10], True),
    'METERS':      ZBBQ_Unit('Meters',      'm',  1,        'METRIC', [1, 2, 3, 5, 7, 10], True),
    'KILOMETERS':  ZBBQ_Unit('Kilometers',  'km', 1000,     'METRIC', [1, 2, 3, 5, 7, 10], True),
    'MICROMETERS': ZBBQ_Unit('Micrometers', 'um', 0.000001, 'METRIC', [1, 2, 3, 5, 7, 10], True),

    # Imperial

    'INCHES': ZBBQ_Unit('Inches',                  'in',   0.0254,    'IMPERIAL', [1, 2, 3, 5, 7, 10],  True),
    'FEET':   ZBBQ_Unit('Feet',                    'ft',   0.3048,    'IMPERIAL', [1, 2, 3, 5, 7, 10],  True),
    'MILES':  ZBBQ_Unit('Miles',                   'mi',   1609.344,  'IMPERIAL', [1, 2, 3, 5, 7, 10], True),
    'THOU':   ZBBQ_Unit('Thousandths of an inch',  'thou', 0.0000254, 'IMPERIAL', [1, 2, 3, 5, 7, 10], True),

}

ZBBQ_UnitSystems = {

    'NONE': 'None',
    'METRIC': 'Metric',
    'IMPERIAL': 'Imperial'

}

ZBBQ_UnitsForEnumProperty = [(unitKey, unit.shortTitle, unit.title) for unitKey, unit in ZBBQ_Units.items()]
ZBBQ_UnitSystemsForEnumProperty = [(unitSystemKey, unitSystemName, unitSystemName) for unitSystemKey, unitSystemName in ZBBQ_UnitSystems.items()]


def ZBBQ_UnitsForEnumPropertySceneUnitSystem():
    return [(unitKey, unit.title, "") for unitKey, unit in ZBBQ_Units.items() if unit.unitSystem == bpy.context.scene.unit_settings.system]


def ZBBQ_UnitsForEnumPropertyConsideringUnitSystem(unitSystem):
    return [(unitKey, unit.shortTitle, unit.title) for unitKey, unit in ZBBQ_Units.items() if unit.unitSystem == unitSystem]


def ZBBQ_UnitsForEnumPropertyUnitSystemForCurrentPresetGroup():
    from .commonFunc import ZBBQ_CommonFunc

    return [(unitKey, unit.shortTitle, unit.title) for unitKey, unit in ZBBQ_Units.items() if unit.unitSystem == ZBBQ_CommonFunc.GetActiveBevelPresetGroup().unitSystem]
