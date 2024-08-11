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
import math

from . fog import toggle_fog
from . variables import VERSION_FORMAT_NUMBER


def purge_node_groups_version_0():
    """ Delete all Node Groups from the blenderfile """
    #  list of shader node groups in addon
    nodeTreeGroupArray = [
        "StarlightAtmosphere",
        ". calculate_fog_object",
        ". calculate_fog_world",
        ". calculate_scattering",
        ". calculcate_scattering_object",
        ". smoothstep()",
        ". camera_position",
        ". camera_position_world",
        ". clamp()",
        ". earth_shadow_hack",
        ". exp()",
        ". flat_world",
        ". intersect_plane",
        ". length()",
        ". mie_scattering",
        ". ray_plane_intersection",
        ". sun_ground_radiance",
        ". sun_limb_darkening_radiance",
        ". binary_star_position",
        ". B",
        ". C",
        ". calculate_fog_noground",
        ". calculate_fog_ob",
        ". clamp",
        ". clouds_lighting",
        ". cubify",
        ". d",
        ". D",
        ". get_planet",
        ". near_far",
        ". NumericMie",
        ". phase_rayleigh",
        ". PhysicalClouds",
        ". PhysicalCoordinates",
        ". PhysicalInputs",
        ". PhysicalStars",
        ". planet_intersect",
        ". PlanetData",
        ". smoothstep",
        ". exp2()",
        ". sphere_penumbra",
        ". fbm",
        ". xyz_to_cube_coords",
        ". sRGBtoAP1",
    ]
    for x in nodeTreeGroupArray:
        for g in bpy.data.node_groups:
            if x in g.name:
                bpy.data.node_groups.remove(g)


def update_blend_version_1(context, settings):
    # Migration from azimuth/elevation to the sun horizonal and vertical rotation
    asettings = context.scene.world.psa_atmosphere_settings
    asettings.azimuth = math.pi - asettings.azimuth
    asettings.elevation = math.pi/2 - asettings.elevation
    # Starting 1.5.2 we are storing sun obj in a variable
    sun = None
    for obj in context.scene.objects:
        if obj.name.startswith("Starlight Sun"):
            sun = obj
    bpy.context.scene.world.psa_exposed.sun_object = sun
    settings.version_format = 2
    

def update_blend_version_0(context, settings):
    # Update .blend file from version format 0 (1.4.x and older) to
    # version format 1 (1.5.x and newer)
    scene = context.scene
    old_gsettings = scene.get("general_settings")
    old_asettings = scene.get("atmosphere_settings")
    asettings = scene.world.psa_atmosphere_settings

    # Version 0 format used hardcoded world name
    if not scene.world.name.startswith("Atmosphere"):
        settings.version_format = 1
        return

    if old_gsettings.get("material_count") is not None:
        #settings.enabled = old_gsettings.get("enabled", False)
        settings.material_count = old_gsettings.get("material_count", 0)
        settings.material_with_fog_count = old_gsettings.get("material_with_fog_count", 0)
        settings.intensity_multiplier = old_gsettings.get("intensity_multiplier", 0.0)
        settings.sun_pos_checksum = old_gsettings.get("sun_pos_checksum", "")
        settings.all_props_checksum = old_gsettings.get("all_props_checksum", "")
        settings.fog_enabled = old_gsettings.get("fog_enabled", False)
        settings.silent_update = old_gsettings.get("silent_update", False)
        settings.is_rendering = False # scene["general_settings"].is_rendering

        asettings.sun_disk = old_asettings.get("sun_disk", True)
        asettings.sun_lamp = old_asettings.get("sun_lamp", True)
        asettings.azimuth = old_asettings.get("azimuth", 2.449570)
        asettings.elevation = old_asettings.get("elevation", 3.089843)
        asettings.sun_diameter = old_asettings.get("sun_diameter", 0.009180)
        asettings.atmosphere_color = old_asettings.get("atmosphere_color", (0.75, 0.8, 1.0, 1.0))
        asettings.atmosphere_inscattering = old_asettings.get("atmosphere_inscattering", (0.0573, 0.1001, 0.1971, 1.000000))
        asettings.atmosphere_extinction = old_asettings.get("atmosphere_extinction", (1.0-0.0573, 1.0-0.1001, 1.0-0.1971, 1.000000))
        asettings.atmosphere_density = old_asettings.get("atmosphere_density", 1.2)
        asettings.atmosphere_height = old_asettings.get("atmosphere_height", 8000.0)
        asettings.atmosphere_intensity = old_asettings.get("atmosphere_intensity", 2.0)
        asettings.night_intensity = old_asettings.get("night_intensity", 0.02)
        asettings.atmosphere_falloff = old_asettings.get("atmosphere_falloff", 1.0)
        asettings.atmosphere_mie = old_asettings.get("atmosphere_mie", 2.0)
        asettings.atmosphere_mie_dir = old_asettings.get("atmosphere_mie_dir", 0.7)
        asettings.atmosphere_distance = old_asettings.get("atmosphere_distance", 1.0)
        asettings.ground_visible = old_asettings.get("ground_visible", True)
        asettings.ground_albedo = old_asettings.get("ground_albedo", (0.25, 0.25, 0.25, 1.0))
        asettings.ground_offset = old_asettings.get("ground_offset", -100.0)
        asettings.horizon_offset = old_asettings.get("horizon_offset", 0.0)
        asettings.sun_temperature = old_asettings.get("sun_temperature", 5700)
        asettings.sun_intensity = old_asettings.get("sun_intensity", 200000)
        asettings.enable_binary_sun = old_asettings.get("enable_binary_sun", False)
        asettings.binary_distance = old_asettings.get("binary_distance", 0.16)
        asettings.binary_phase = old_asettings.get("binary_phase", 2.0)
        asettings.binary_diameter = old_asettings.get("binary_diameter", 0.017453)
        asettings.binary_temperature = old_asettings.get("binary_temperature", 1800)
        asettings.binary_intensity = old_asettings.get("binary_intensity", 50000)
        asettings.sun_radiance_gamma = old_asettings.get("sun_radiance_gamma", 1.0)
        asettings.stars_path = old_asettings.get("stars_path", "")
        asettings.stars_intensity = old_asettings.get("stars_intensity", 0.02)
        asettings.stars_gamma = old_asettings.get("stars_gamma", 0.5)
        asettings.clouds_scale = old_asettings.get("clouds_scale", 2.0)
        asettings.clouds_min = old_asettings.get("clouds_min", -1.0)
        asettings.clouds_max = old_asettings.get("clouds_max", 1.0)
        asettings.clouds_thickness = old_asettings.get("clouds_thickness", 15.0)
        asettings.clouds_scattering = old_asettings.get("clouds_scattering", (0.4, 0.45, 0.8, 1.0))
        asettings.clouds_amount = old_asettings.get("clouds_amount", 5.0)
        asettings.clouds_power = old_asettings.get("clouds_power", 5.0)
        asettings.clouds_lighting_intensity = old_asettings.get("clouds_lighting_intensity", 1.0)
        asettings.clouds_location = old_asettings.get("clouds_location", (0, 0, 0))
        asettings.clouds_rotation = old_asettings.get("clouds_rotation", (0, 0, 0))
        #asettings.fog_state = old_asettings.get("fog_state", 0)
        #asettings.stars_type = old_asettings.get("stars_type", 0)
        #asettings.clouds_type = old_asettings.get("clouds_type", 0)

        del scene["general_settings"]
        del scene["atmosphere_settings"]

        toggle_fog(0)

        for n in scene.world.node_tree.nodes:
            # Version 0 overwrites worlds and forces atmosphere so this is acceptable
            if n.name in (
                'StarlightAtmosphere',
                'PhysicalInputs',
                'PhysicalCoordinates',
                'PhysicalPlanetData',
                'PhysicalClouds',
                'PhysicalStars',
                'StarlightAtmosphereMaterial',
                'sRGBtoAP1'):
                scene.world.node_tree.nodes.remove(n)

        purge_node_groups_version_0()

    else:
        # File hasn't been opened with older version
        pass

    settings.version_format = 1


def update_blend_version(context, settings):
    while settings.version_format < VERSION_FORMAT_NUMBER:
        if settings.version_format == 0:
            update_blend_version_0(context, settings)
        elif settings.version_format == 1:
            update_blend_version_1(context, settings)
        else:
            # Version should be right or newer
            break
