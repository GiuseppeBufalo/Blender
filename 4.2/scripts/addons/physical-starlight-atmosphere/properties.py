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

import bpy
from bpy.types import PropertyGroup, Object
from bpy.props import (
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
    PointerProperty,
)
from . handlers import *
from . clouds import toggle_clouds, clouds_update_handler


class PA_Exposed(PropertyGroup):
    ############################################################################
    # Exposed pointers and parameters
    ############################################################################

    output_node_name: StringProperty(
        description="Name of the output node",
    )

    atmosphere_node_name: StringProperty(
        description="Name of the Starlight Atmosphere node",
    )

    stars_node_name: StringProperty(
        description="Name of the Physical Stars node",
    )

    sun_object: PointerProperty(
        type=Object,
        description="Sun object used by addon"
    )

class GeneralSettings(PropertyGroup):
    ############################################################################
    # General Properties
    ############################################################################

    enabled: BoolProperty(
        name="Enable starlight atmosphere",
        default=False,
        update=enable_atmosphere
    )

    version_format: IntProperty(
        name="Version format",
        default=0, # Default to 0 to detect pre-version system .blend files
    )

    material_count: IntProperty(
        name="Material Count",
        default=0,
    )

    material_with_fog_count: IntProperty(
        name="Material with applied fog count",
        default=0,
    )

    intensity_multiplier: IntProperty(
        name="Default property intensity multiplier",
        default=1,
    )

    sun_pos_checksum: FloatProperty(
        name="Sun Position checksum",
        default=0,
    )

    all_props_checksum: StringProperty(
        description="Contains last frame all property string concatenation",
    )

    fog_enabled: BoolProperty(
        default=False
    )

    is_rendering: BoolProperty(
        default=False
        # description="Update azimuth or elevation without triggering update function"
    )



class AtmosphereSettings(PropertyGroup):
    ############################################################################
    # Physical Atmosphere panel properties
    ############################################################################

    sun_disk : BoolProperty(
        name = "Sun Disk",
        description = "Toggles Sun disk in the atmosphere",
        default = True,
        update = sun_calculation_handler
    )

    sun_lamp : BoolProperty(
        name = "Sun Lamp",
        description = "Use Sun lamp as light source instead of Sun disk in world background",
        default = True,
        update = sun_calculation_handler
    )

    azimuth : FloatProperty(
        name = "Azimuth",
        description = "Horizontal direction: at 0° the Sun is in the Y+ axis",
        soft_min = -999,
        soft_max = 999,
        step = 5,
        precision = 3,
        default = 2.449570,
        unit = "ROTATION",
        #update = azimuth_handler
    )

    elevation : FloatProperty(
        name = "Elevation",
        description = "Vertical direction: at 90° the Sun is in the zenith",
        soft_min = -999,
        soft_max = 999,
        step = 5,
        precision = 3,
        default = 3.089843,
        unit = "ROTATION",
        #update = elevation_handler
    )

    sun_diameter : FloatProperty(
        name = "Angular Diameter",
        description = "Angular diameter of the Sun disk in degrees",
        min = 0.001,
        max = math.pi*0.5,
        step = 1,
        precision = 3,
        default = 0.009180,
        unit = "ROTATION",
        update = sun_calculation_handler
    )

    atmosphere_color : FloatVectorProperty(
        name = "",
        description = "Atmosphere color",
        subtype="COLOR_GAMMA",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.75, 0.8, 1.0, 1.0),
        update = sun_calculation_handler
    )

    atmosphere_inscattering : FloatVectorProperty(
        name = "",
        description = "Rayleigh scattering",
        subtype="COLOR_GAMMA",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0573, 0.1001, 0.1971, 1.000000),
        update = sun_calculation_handler
    )

    atmosphere_extinction : FloatVectorProperty(
        name = "",
        description = "Atmosphere absorption / color wavelength extinction value",
        subtype="COLOR_GAMMA",
        size=4,
        min=0.0,
        max=1.0,
        default=(1.0-0.0573, 1.0-0.1001, 1.0-0.1971, 1.000000),
        update = sun_calculation_handler
    )

    atmosphere_density : FloatProperty(
        name = "Density",
        description = "Atmosphere density in kg/m3",
        min = 0,
        soft_max = 100,
        step = 100,
        precision = 2,
        default = 1.2,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    atmosphere_height : FloatProperty(
        name = "Scale Height",
        description = "Atmosphere height",
        min = 2,
        soft_max = 10000,
        step = 100,
        precision = 2,
        default = 8000,
        unit = "LENGTH",
        subtype = "DISTANCE",
        update = sun_calculation_handler
    )

    atmosphere_intensity : FloatProperty(
        name = "Intensity",
        description = "Atmosphere Radiance Intensity in W/m2",
        min = 0,
        soft_max = 500,
        step = 100,
        precision = 2,
        default = 2,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    night_intensity : FloatProperty(
        name = "Night Intensity",
        description = "Night Sky Radiance Intensity in W/m2",
        min = 0.000001,
        soft_max = 0.04,
        step = 100,
        precision = 2,
        default = 0.02,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    atmosphere_falloff : FloatProperty(
        name = "Falloff",
        description = "Artistic atmosphere falloff curve",
        min = 0,
        max = 3.0,
        step = 10,
        precision = 2,
        default = 1.0,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    atmosphere_mie : FloatProperty(
        name = "Intensity",
        description = "Mie scattering Intensity in W/m2",
        min = 0,
        soft_max = 500.0,
        step = 10,
        precision = 2,
        default = 2.0,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    atmosphere_mie_dir : FloatProperty(
        name = "Anisotropy",
        description = "Mie directional anisotropy",
        min = 0,
        max = 1.0,
        step = 10,
        precision = 2,
        default = 0.7,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    atmosphere_distance : FloatProperty(
        name = "Distance Scalar",
        description = "Artistic atmosphere distance scalar",
        min = 0.0,
        soft_max = 500,
        step = 10,
        precision = 2,
        default = 1,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    ground_visible: BoolProperty(
        name="Ground",
        description="Parametric ground visibility",
        default=True,
        update=sun_calculation_handler
    )

    ground_albedo : FloatVectorProperty(
        name = "",
        description = "Ground color",
        subtype ="COLOR_GAMMA",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (0.25, 0.25, 0.25, 1.0),
        update = sun_calculation_handler
    )

    ground_offset : FloatProperty(
        name = "Ground Offset",
        description = "Parametric ground plane offset distance in meters",
        unit = "LENGTH",
        subtype = "DISTANCE",
        soft_min = -500000.0,
        soft_max = 0.0,
        default = -100.0,
        update = sun_calculation_handler
    )

    horizon_offset : FloatProperty(
        name = "Horizon Offset",
        description = "Move horizon line up or down",
        unit = "NONE",
        subtype = "FACTOR",
        min = -1.0,
        max = 1.0,
        default = 0,
        update = sun_calculation_handler
    )

    sun_temperature : FloatProperty(
        name = "Temperature K",
        description = "Sun's blackbody temperature in Kelvins",
        min = 1000,
        soft_max = 10000,
        step = 100,
        precision = 2,
        default = 5700,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    sun_intensity : FloatProperty(
        name = "Intensity",
        description = "Sun Radiance Intensity in W/m2. Influences only sun disk and ground",
        soft_min = 100,
        soft_max = 200000,
        step = 100,
        precision = 2,
        default = 200000,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    enable_binary_sun: BoolProperty(
        name="Binary Sun",
        description="Use Binary Sun",
        default=False,
        update=sun_calculation_handler
    )

    binary_distance: FloatProperty(
        name="Distance",
        description="Distance from the Sun",
        min=0.0,
        soft_max=1,
        step=0.001,
        precision=3,
        default=0.16,
        unit="NONE",
        subtype="FACTOR",
        update=sun_calculation_handler
    )

    binary_phase: FloatProperty(
        name="Phase",
        description="Phase in context of Sun",
        soft_min=-360,
        soft_max=360,
        step=5,
        precision=3,
        default=2.0,
        unit="ROTATION",
        update=sun_calculation_handler
    )

    binary_diameter: FloatProperty(
        name="Angular Diameter",
        description="Angular diameter of the Binary Sun disk in degrees",
        min=0.001,
        max=math.pi*0.5,
        step=1,
        precision=3,
        default=0.017453,
        unit="ROTATION",
        update=sun_calculation_handler
    )

    binary_temperature: FloatProperty(
        name="Temperature K",
        description="Binary Sun's blackbody temperature in Kelvins",
        min=1000,
        soft_max=10000,
        step=100,
        precision=2,
        default=1800,
        unit="NONE",
        subtype="FACTOR",
        update=sun_calculation_handler
    )

    binary_intensity: FloatProperty(
        name="Intensity",
        description="Binary Sun Radiance Intensity in W/m2. Influences only sun disk and ground",
        soft_min=100,
        soft_max=200000,
        step=100,
        precision=2,
        default=50000,
        unit="NONE",
        subtype="FACTOR",
        update=sun_calculation_handler
    )

    sun_radiance_gamma : FloatProperty(
        name = "Sun Radiance Gamma",
        description = "Artistic Sun Radiance Gamma",
        min = 0.01,
        max = 3.0,
        step = 10,
        precision = 2,
        default = 1.0,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    stars_type: EnumProperty(
        items=[('procedural', 'Procedural', 'Enable procedurally generated stars (textures loading instantly)'),
               ('texture', 'Texture', 'Enable texture for the starmap (textures loading slowly)'),
               ('none', 'None', 'disable stars')],
        default='procedural',
        update=stars_handler
    )

    stars_path : StringProperty(
        name = "Starmap File",
        description="Choose a Starmap Image File",
        subtype='FILE_PATH',
        update = stars_texture_handler,
    )

    stars_intensity : FloatProperty(
        name = "Radiance Intensity",
        description = "Stars Radiance Intensity",
        min = 0,
        soft_max = 15.0,
        step = 10,
        precision = 2,
        default = 0.02,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    stars_gamma : FloatProperty(
        name = "Radiance Gamma",
        description = "Stars Radiance Gamma",
        min = 0,
        soft_max = 3.0,
        step = 10,
        precision = 2,
        default = 0.5,
        unit = "NONE",
        subtype = "FACTOR",
        update = sun_calculation_handler
    )

    # All cloud related properties
    clouds_type: EnumProperty(
        items=[('procedural', 'Procedural', 'Enable procedurally generated clouds'),
               ('none', 'None', 'Disable clouds')],
        default='procedural',
        update=toggle_clouds
    )

    clouds_scale : FloatProperty(
        name = "Scale",
        description = "Clouds scale",
        min = 0,
        soft_max = 15,
        step = 0.1,
        precision = 2,
        default = 2,
        unit = "NONE",
        subtype = "FACTOR",
        update = clouds_update_handler,
    )

    clouds_min : FloatProperty(
        name = "Min",
        description = "Clouds min",
        min = -1,
        soft_max = 1,
        step = 0.1,
        precision = 2,
        default = -1.0,
        unit = "NONE",
        subtype = "FACTOR",
        update = clouds_update_handler,
    )

    clouds_max : FloatProperty(
        name = "Max",
        description = "Clouds max",
        min = -1,
        soft_max = 1,
        step = 0.1,
        precision = 2,
        default = 1.0,
        unit = "NONE",
        subtype = "FACTOR",
        update = clouds_update_handler,
    )

    clouds_thickness : FloatProperty(
        name = "Thickness",
        description = "Clouds thickness",
        min = 0,
        soft_max = 10,
        step = 0.1,
        precision = 2,
        default = 15,
        unit = "NONE",
        subtype = "FACTOR",
        update = clouds_update_handler,
    )

    clouds_scattering : FloatVectorProperty(
        name = "",
        description = "Clouds Inscattering",
        subtype="COLOR_GAMMA",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.4, 0.45, 0.8, 1.0),
        update = clouds_update_handler
    )

    clouds_amount : FloatProperty(
        name = "Self Shadowing",
        description = "Self Shadowing",
        min = 0,
        soft_max = 100,
        step = 0.1,
        precision = 2,
        default = 5,
        unit = "NONE",
        subtype = "FACTOR",
        update = clouds_update_handler,
    )

    clouds_power : FloatProperty(
        name = "Directional Power",
        description = "Clouds power",
        min = 0,
        soft_max = 100,
        step = 0.1,
        precision = 2,
        default = 5,
        unit = "NONE",
        subtype = "FACTOR",
        update = clouds_update_handler,
    )

    clouds_lighting_intensity : FloatProperty(
        name = "Lighting Intensity",
        description = "Lighting Intensity",
        min = 0,
        soft_max = 10,
        step = 1,
        precision = 2,
        default = 1,
        unit = "NONE",
        subtype = "FACTOR",
        update = clouds_update_handler,
    )

    clouds_location : FloatVectorProperty(
        name = "Location",
        description = "Clouds Location",
        subtype="XYZ",
        size=3,
        default=(0, 0, 0),
        update = clouds_update_handler
    )

    clouds_rotation : FloatVectorProperty(
        name = "Rotation",
        description = "Clouds Rotation",
        subtype="EULER",
        size=3,
        default=(0, 0, 0),
        update = clouds_update_handler
    )


    fog_state: EnumProperty(
        items=[('manual', 'Manual', 'Enable fog for existing objects in the scene manually'),
               ('auto', 'Auto', 'Fog is automatically added whenever new material is added to an object')],
        default='manual',
        update=toggle_fog_handler
    )
