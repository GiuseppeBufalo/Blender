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
import mathutils
from . helpers import *
from . variables import *


def get_object(name):
    """ Get object from scene context (even if prefixed with e.g. 002) """
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(name):
            return obj
    return None

def necessary_nodes_available(node_tree):
    if node_tree.nodes.get(STARLIGHT_ATMOSPHERE_NODE_NAME) is None:
        return False
    if node_tree.nodes.get(PHYSICAL_INPUTS_NODE_NAME) is None:
        return False
    if node_tree.nodes.get(PHYSICAL_COORDINATES_NODE_NAME) is None:
        return False
    return True


def sun_calculation(context, depsgraph, mode):
    gsettings = context.scene.world.psa_general_settings
    asettings = context.scene.world.psa_atmosphere_settings
    node_tree = context.scene.world.node_tree

    atmosphere_height = asettings.atmosphere_height
    atmosphere_density = asettings.atmosphere_density

    infinity = 1000000  # not an infinity at all, but a value that makes look "flat" earth to be round
    intensity = asettings.sun_intensity * gsettings.intensity_multiplier
    sun = context.scene.world.psa_exposed.sun_object 
        
    # If there is no sun or atmosphere do nothing
    if sun is None or not necessary_nodes_available(node_tree):
        return

    if gsettings.is_rendering or mode == 'rendering':  # is_rendering occurs while in rendering mode, mode rendering passed by frame_change
       sun = sun.evaluated_get(depsgraph)  # whenever sun is modified using object handle

    inputs = bpy.context.scene.world.node_tree.nodes[PHYSICAL_INPUTS_NODE_NAME].node_tree

    # Calculating the sun intensity and color
    ray = mathutils.Vector((0, 0, -1))
    ray.rotate(sun.rotation_euler)
    ray.normalized()
    p = ray*infinity

    eye = mathutils.Vector((0, 0, 0.5))  # ground level. to do -> make viewer level
    eye2 = mathutils.Vector((0, 0, atmosphere_height))  # ground level. to do -> make viewer level

    a = 1.0-math.exp(p[2]/atmosphere_height)
    b = math.exp((eye[2]-asettings.ground_offset)*-1.0/atmosphere_height) * (atmosphere_density)
    b2 = math.exp((eye2[2]-asettings.ground_offset)*-1.0/atmosphere_height) * (atmosphere_density)
    fog = ((a*b)/ray[2])
    fog = fog*-1  # fog here is negative, we need to pow() it so we make it positive
    fog = min(fog, 1e+22)  # shader has it to fix something, forgot what.
    fog = math.pow(fog, asettings.atmosphere_falloff)
    fog = fog*asettings.atmosphere_distance*-1  # make it negative again

    fog2 = ((a*b2)/ray[2])
    fog2 = fog2*-1  # fog here is negative, we need to pow() it so we make it positive
    fog2 = min(fog2, 1e+22)  # shader has it to fix something, forgot what.
    fog2 = math.pow(fog2, asettings.atmosphere_falloff)
    fog2 = fog2*asettings.atmosphere_distance*-1  # make it negative again

    steridianLamp = 2*math.pi*(1.0-math.cos(0.00918/2))#0.00918 = sun diameter default
    steridianDisk = 1.0/(2*math.pi*(1.0-math.cos(asettings.sun_diameter/2)))
    binary_steridianDisk = 1.0/(2*math.pi*(1.0-math.cos(asettings.binary_diameter/2)))

    scatter = asettings.atmosphere_inscattering
    absorption = asettings.atmosphere_extinction

    sun_color = Helpers.convert_K_to_RGB(asettings.sun_temperature)
    inputs.nodes['sun_color'].outputs[0].default_value = (sun_color[0], sun_color[1], sun_color[2], 1)

    binary_sun_color = Helpers.convert_K_to_RGB(asettings.binary_temperature)
    inputs.nodes['binary_sun_color'].outputs[0].default_value = (binary_sun_color[0], binary_sun_color[1], binary_sun_color[2], 1)

    scatR = (1.0 - math.exp(scatter[0]*fog)) * asettings.atmosphere_color[0]
    scatG = (1.0 - math.exp(scatter[1]*fog)) * asettings.atmosphere_color[1]
    scatB = (1.0 - math.exp(scatter[2]*fog)) * asettings.atmosphere_color[2]

    absorptR = math.exp((1.0-absorption[0])*fog) * sun_color[0] * intensity
    absorptG = math.exp((1.0-absorption[1])*fog) * sun_color[1] * intensity
    absorptB = math.exp((1.0-absorption[2])*fog) * sun_color[2] * intensity

    scatR2 = (1.0 - math.exp(scatter[0]*fog2)) * asettings.atmosphere_color[0]
    scatG2 = (1.0 - math.exp(scatter[1]*fog2)) * asettings.atmosphere_color[1]
    scatB2 = (1.0 - math.exp(scatter[2]*fog2)) * asettings.atmosphere_color[2]

    absorptR2 = math.exp((1.0-absorption[0])*fog2) * sun_color[0] * intensity
    absorptG2 = math.exp((1.0-absorption[1])*fog2) * sun_color[1] * intensity
    absorptB2 = math.exp((1.0-absorption[2])*fog2) * sun_color[2] * intensity

    # Sun Ground Radiance
    #vert = ray.dot(mathutils.Vector((0, 0, -1)))
    #sun_ground_radiance = Helpers.smoothstep(vert, -asettings.sun_diameter*0.5, asettings.sun_diameter*0.5)

    # Sun Strength
    if asettings.sun_lamp:
        sun.data.energy = 1.0
    else:
        sun.data.energy = 0.0

    # Calculate basic attenuation based on sun diameter
    #denom = 2.0/settings.sun_diameter + 1.0
    #lamp_intensity = (1.0 / (denom*denom))

    #Sun Color
    sunColor = [
        Helpers.gamma_correction((scatR+absorptR)*steridianLamp, asettings.sun_radiance_gamma),
        Helpers.gamma_correction((scatG+absorptG)*steridianLamp, asettings.sun_radiance_gamma),
        Helpers.gamma_correction((scatB+absorptB)*steridianLamp, asettings.sun_radiance_gamma)
    ]

    sunColorUpper = [
        Helpers.gamma_correction((scatR2+absorptR2)*steridianLamp, asettings.sun_radiance_gamma),
        Helpers.gamma_correction((scatG2+absorptG2)*steridianLamp, asettings.sun_radiance_gamma),
        Helpers.gamma_correction((scatB2+absorptB2)*steridianLamp, asettings.sun_radiance_gamma)
    ]

    # Apply color an angle to lamp and sky
    sun.data.color = [sunColor[0], sunColor[1], sunColor[2]]

    # Workaround of a workaround
    inv_intensity_mult =  1.0/gsettings.intensity_multiplier

    inputs.nodes['sun_light'].outputs[0].default_value = (sunColor[0]*inv_intensity_mult, sunColor[1]*inv_intensity_mult, sunColor[2]*inv_intensity_mult, 1)
    inputs.nodes['sun_light_upper'].outputs[0].default_value = (sunColorUpper[0]*inv_intensity_mult, sunColorUpper[1]*inv_intensity_mult, sunColorUpper[2]*inv_intensity_mult, 1)
    inputs.nodes['steridian'].outputs[0].default_value = steridianLamp*steridianDisk
    inputs.nodes['binary_steridian'].outputs[0].default_value = steridianLamp*binary_steridianDisk
    sun.data.angle = asettings.sun_diameter

    # Atmosphere
    asettings.azimuth = sun.rotation_euler[2]
    asettings.elevation = sun.rotation_euler[0]
    atmosphere_calculation(asettings, gsettings,  sun)


# Atmosphere
def atmosphere_calculation(asettings, gsettings, sun):


    atmosphere_height = asettings.atmosphere_height
    atmosphere_density = asettings.atmosphere_density

    atmosphere_color = asettings.atmosphere_color
    atmosphere_inscattering = asettings.atmosphere_inscattering
    atmosphere_extinction = asettings.atmosphere_extinction

    atmosphere_mie = asettings.atmosphere_mie
    atmosphere_mie_dir = asettings.atmosphere_mie_dir

    atmosphere_distance = asettings.atmosphere_distance
    atmosphere_falloff = asettings.atmosphere_falloff

    ground_visible = asettings.ground_visible
    ground_albedo = asettings.ground_albedo
    ground_offset = asettings.ground_offset
    horizon_offset = asettings.horizon_offset

    node_tree = bpy.context.scene.world.node_tree
    coordinates = node_tree.nodes[PHYSICAL_COORDINATES_NODE_NAME].node_tree
    inputs = node_tree.nodes[PHYSICAL_INPUTS_NODE_NAME].node_tree


    # Atmosphere rotation
    vec = mathutils.Vector((0, 0, 1))
    vec.rotate(sun.rotation_euler)
    # Planet's shadow hack thing
    vec1 = mathutils.Vector((0, 1, 0))
    vec1.rotate(sun.rotation_euler)

    vec2 = mathutils.Vector((1, 0, 0))
    vec2.rotate(sun.rotation_euler)

    coordinates.nodes['sun_rot'].outputs[0].default_value = mathutils.Vector((
        math.degrees(sun.rotation_euler[0]),
        math.degrees(sun.rotation_euler[1]),
        math.degrees(sun.rotation_euler[2])
    ))

    coordinates.nodes['sun_dir'].outputs[0].default_value = vec
    coordinates.nodes['sun_up'].outputs[0].default_value = vec1
    coordinates.nodes['sun_right'].outputs[0].default_value = vec2

    inputs.nodes['sun_diameter'].outputs[0].default_value = asettings.sun_diameter
    inputs.nodes['binary_sun_diameter'].outputs[0].default_value = asettings.binary_diameter

    inputs.nodes['binary_phase'].outputs[0].default_value = asettings.binary_phase
    inputs.nodes['binary_distance'].outputs[0].default_value = asettings.binary_distance


    if asettings.sun_disk == False:
        inputs.nodes['sun_intensity'].outputs[0].default_value = 0.0
        inputs.nodes['binary_sun_intensity'].outputs[0].default_value = 0.0
    else:
        inputs.nodes['sun_intensity'].outputs[0].default_value = asettings.sun_intensity
        inputs.nodes['binary_sun_intensity'].outputs[0].default_value = asettings.binary_intensity

    if asettings.sun_disk and asettings.sun_lamp:
        inputs.nodes['sun_intensity'].outputs[0].default_value = asettings.sun_intensity * 0.05
        inputs.nodes['binary_sun_intensity'].outputs[0].default_value = asettings.binary_intensity * 0.05

    if asettings.enable_binary_sun == False:
        inputs.nodes['binary_sun_intensity'].outputs[0].default_value = 0.0

    inputs.nodes['night_radiance'].outputs[0].default_value = asettings.night_intensity

    inputs.nodes['atmosphere_height'].outputs[0].default_value = atmosphere_height
    inputs.nodes['atmosphere_density'].outputs[0].default_value = atmosphere_density

    inputs.nodes['atmosphere_intensity'].outputs[0].default_value = asettings.atmosphere_intensity

    inputs.nodes['atmosphere_color'].outputs[0].default_value = atmosphere_color
    inputs.nodes['atmosphere_inscattering'].outputs[0].default_value = atmosphere_inscattering
    inputs.nodes['atmosphere_extinction'].outputs[0].default_value = atmosphere_extinction

    inputs.nodes['atmosphere_mie'].outputs[0].default_value = atmosphere_mie
    inputs.nodes['atmosphere_mie_dir'].outputs[0].default_value = atmosphere_mie_dir

    inputs.nodes['atmosphere_distance'].outputs[0].default_value = atmosphere_distance
    inputs.nodes['atmosphere_falloff'].outputs[0].default_value = atmosphere_falloff
    # ground
    inputs.nodes['ground_visible'].outputs[0].default_value = ground_visible
    inputs.nodes['ground_albedo'].outputs[0].default_value = ground_albedo
    inputs.nodes['ground_offset'].outputs[0].default_value = ground_offset
    inputs.nodes['horizon_offset'].outputs[0].default_value = horizon_offset
    # stars
    inputs.nodes['stars_radiance_intensity'].outputs[0].default_value = asettings.stars_intensity
    inputs.nodes['stars_radiance_gamma'].outputs[0].default_value = asettings.stars_gamma
    #general
    inputs.nodes['intensity_multiplier'].outputs[0].default_value = gsettings.intensity_multiplier
