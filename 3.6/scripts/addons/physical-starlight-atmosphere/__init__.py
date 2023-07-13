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

bl_info = {
	"name": "Physical Starlight and Atmosphere",
	"author": "Martins Upitis, Karlis Upitis",
	"version": (1, 5, 2),
	"blender": (3, 0, 0),
	"description": "Physical Starlight and Atmosphere",
	"location": "World > Atmosphere",
	"wiki_url": "https://www.physicaladdons.com/psa/",
	"support": "COMMUNITY",
	"category": "Lighting",
	"tracker_url": "https://github.com/PhysicalAddons/physical-starlight-and-atmosphere/issues"
	}

import bpy
from bpy.props import *
from bpy.app.handlers import persistent
from threading import Timer

from . properties import *
from . preferences import RIG_OT_OpenDocumentation, RIG_MT_addon_preferences, update_toolbar_label
from . sunlight import *
from . ui import *
from . clouds import RIG_PT_PhysicalCloudsTB, RIG_PT_PhysicalCloudsWT, clouds_update_handler
from . handlers import validate_version, create_sun

if locals().get('loaded'):
	loaded = False
	from importlib import reload
	from sys import modules

	modules[__name__] = reload(modules[__name__])
	for name, module in modules.items():
		if name.startswith(f"{__package__}."):
			globals()[name] = reload(module)
	del reload, modules


def tuple_to_str(n):
	""" Concat tuple and nested tuple in string """
	if type(n).__name__ == 'bpy_prop_array':
		return "".join(map(str, n))
	else:
		return str(n)


# check if sun is being transformed
previous_world = None
@persistent
def sun_handler(scene, depsgraph):  # allow rotating the sun and seeing changes in the real time
	if not hasattr(scene.world, 'psa_general_settings'):
		return
	gsettings = scene.world.psa_general_settings
	asettings = scene.world.psa_atmosphere_settings
	prefs = bpy.context.preferences.addons['physical-starlight-atmosphere'].preferences

	if gsettings.enabled:
		# check if sun exists when switching worlds. If not - add one.
		create_sun()

		# draw world when applying world asset
		for update in depsgraph.updates:
			global previous_world
			if update.id.bl_rna.name == 'World' and previous_world != scene.world.name:
				update_blend_version(bpy.context, gsettings)
				previous_world = scene.world.name
				node_tree = node_tree = scene.world.node_tree
				# set correct physical values intensity multiplier
				gsettings.intensity_multiplier = 1
				if prefs.use_physical_values:
					gsettings.intensity_multiplier = 64
				# make sure to use ACES if selected in addon preferences
				world_output_name = scene.world.psa_exposed.output_node_name
				world_output_node = node_tree.nodes.get(world_output_name)
				if prefs.use_aces == 1 and get_previous_node(world_output_node).name != ACES_CONVERTER_NODE_NAME:
					converter = node_tree.nodes[ACES_CONVERTER_NODE_NAME]
					atmosphere = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME]
					node_tree.links.new(converter.outputs[0], world_output_node.inputs[0])
					node_tree.links.new(atmosphere.outputs[0], converter.inputs[0])
				
				sun = scene.world.psa_exposed.sun_object
				if hasattr(asettings, 'azimuth') and hasattr(asettings, 'elevation'):
					sun.rotation_euler[2] = asettings.azimuth
					sun.rotation_euler[0] = asettings.elevation
				sun_calculation(bpy.context, depsgraph, 'realtime')
			
		# draw world if not in rendering and addon is enabled
		if gsettings.is_rendering == False:
			sun = scene.world.psa_exposed.sun_object
			if sun is None:
				return
			for update in depsgraph.updates:
				if update.id.original == sun and update.is_updated_transform:
					sun_calculation(bpy.context, depsgraph, 'realtime')


@persistent
def fog_handler(scene, depsgraph):
	if not hasattr(bpy.context.scene.world, 'psa_atmosphere_settings'):
		return
	gsettings = scene.world.psa_general_settings
	asettings = scene.world.psa_atmosphere_settings
	if len(bpy.data.materials) > gsettings.material_count and asettings.fog_state == 'auto':
		gsettings.material_count = len(bpy.data.materials)
		toggle_fog(1)


# Render engine handler
previous_scene = None
@persistent
def frame_change_handler(scene, depsgraph):
	""" redraw atmosphere when scene has change """
	sun = bpy.context.scene.world.psa_exposed.sun_object
	if not scene.world or sun is None:
		return

	g = scene.world.psa_general_settings
	a = scene.world.psa_atmosphere_settings

	global previous_scene
	if g.enabled and previous_scene != bpy.context.scene:
		# redraw atmosphere
		sun_calculation(bpy.context, depsgraph, 'rendering')
		previous_scene = bpy.context.scene


	# redraw atmosphere if between frames any of atmosphere UI parameters has changed
	a = scene.world.psa_atmosphere_settings
	g = scene.world.psa_general_settings
	sun = sun.evaluated_get(depsgraph) # update sun position to see if it has changed
	atmosphere_props = (
		a.sun_diameter, a.sun_temperature, a.sun_intensity, a.sun_intensity,
		a.atmosphere_density, a.atmosphere_height, a.atmosphere_intensity, a.night_intensity, a.atmosphere_color,
		a.atmosphere_inscattering, a.atmosphere_extinction, a.atmosphere_mie, a.atmosphere_mie_dir, a.stars_intensity,
		a.stars_gamma, a.ground_albedo, a.ground_offset, a.atmosphere_distance, a.atmosphere_falloff,
		a.sun_radiance_gamma, sun.rotation_euler[0], sun.rotation_euler[2],
		a.clouds_scale, a.clouds_min, a.clouds_max, a.clouds_thickness, a.clouds_scattering, a.clouds_amount,
        a.clouds_power, a.clouds_lighting_intensity, a.clouds_location[0], a.clouds_location[1], a.clouds_rotation[0], a.clouds_rotation[1], a.clouds_rotation[2]
	)

	atmosphere_prop_strings = map(tuple_to_str, atmosphere_props)
	checksum = "".join(atmosphere_prop_strings)

	if g.enabled and (g.all_props_checksum != checksum or scene.frame_current == 1):  # redraw atmosphere only when a property has changed or it is 1st frame
		sun_calculation(bpy.context, depsgraph, 'rendering')
		clouds_update_handler(scene, bpy.context)
		g.all_props_checksum = checksum


# To prevent triggering sun_handler on rendering we implement `is_rendering` flag
@persistent
def render_init_handler(scene, depsgraph):
	g = bpy.context.scene.world.psa_general_settings
	g.is_rendering = True

@persistent
def render_complete_handler(scene, depsgraph):
	g = bpy.context.scene.world.psa_general_settings
	g.is_rendering = False

@persistent
def render_cancel_handler(scene, depsgraph):
	g = bpy.context.scene.world.psa_general_settings
	g.is_rendering = False


@persistent
def blend_load_handler(scene, depsgraph):
	# When loading a .blend file we need to check if there's an older version of PSA present and convert
	validate_version(bpy.context, bpy.context.scene.world.psa_general_settings)


def get_classes():
	return (
		GeneralSettings,
		AtmosphereSettings,
		PA_Exposed,

		RIG_PT_StarlightAtmosphereWT,
		RIG_PT_StarlightAtmosphereTB,
		RIG_PT_SunWT,
		RIG_PT_SunTB,
		RIG_PT_BinarySunWT,
		RIG_PT_BinarySunTB,
		RIG_PT_AtmosphereWT,
		RIG_PT_AtmosphereTB,
		RIG_PT_StarsWT,
		RIG_PT_StarsTB,
		RIG_PT_PhysicalCloudsWT,
		RIG_PT_PhysicalCloudsTB,
		RIG_PT_ObjectFogWT,
		RIG_PT_ObjectFogTB,
		RIG_PT_GroundWT,
		RIG_PT_GroundTB,
		RIG_PT_ArtisticControlsWT,
		RIG_PT_ArtisticControlsTB,
		RIG_PT_FooterWT,
		RIG_PT_FooterTB,
	
		RIG_OT_RemoveObjectFog,
		RIG_OT_ApplyObjectFog,
		RIG_OT_OpenDocumentation,
		RIG_MT_addon_preferences
	)


def register():
	classes = get_classes()
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.World.psa_exposed = PointerProperty(type=PA_Exposed)
	bpy.types.World.psa_general_settings = PointerProperty(type=GeneralSettings)
	bpy.types.World.psa_atmosphere_settings = PointerProperty(type=AtmosphereSettings)

	# Depsgraph change handler
	bpy.app.handlers.depsgraph_update_post.append(sun_handler)
	bpy.app.handlers.depsgraph_update_post.append(fog_handler)
	# Frame change handler
	bpy.app.handlers.frame_change_post.append(frame_change_handler)
	# Render start/stop handlers
	bpy.app.handlers.render_init.append(render_init_handler)
	bpy.app.handlers.render_complete.append(render_complete_handler)
	bpy.app.handlers.render_cancel.append(render_cancel_handler)
	# Blend file load handler
	bpy.app.handlers.load_post.append(blend_load_handler)


	prefs = bpy.context.preferences.addons['physical-starlight-atmosphere'].preferences
	update_toolbar_label(prefs, bpy.context)


def unregister():
	classes = get_classes()
	for cls in classes:
		bpy.utils.unregister_class(cls)
	del bpy.types.World.psa_atmosphere_settings
	del bpy.types.World.psa_general_settings
	del bpy.types.World.psa_exposed

	# Render start/stop handlers
	bpy.app.handlers.render_cancel.remove(render_cancel_handler)
	bpy.app.handlers.render_complete.remove(render_complete_handler)
	bpy.app.handlers.render_init.remove(render_init_handler)
	# Frame change handler
	bpy.app.handlers.frame_change_post.remove(frame_change_handler)
	# Depsgraph change handler
	bpy.app.handlers.depsgraph_update_post.remove(fog_handler)
	bpy.app.handlers.depsgraph_update_post.remove(sun_handler)
	# Blend file load handler
	bpy.app.handlers.load_post.remove(blend_load_handler)


if __name__ == "__main__":
	register()


loaded = True