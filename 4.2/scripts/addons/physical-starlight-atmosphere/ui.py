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

from bpy.types import Panel, Operator, AddonPreferences, Menu
from . handlers import sun_calculation_handler, toggle_fog
from . helpers import current_addon_version

############################################################################
# BASE CLASES
############################################################################
# Base for World tab and not sure how to call it.
class RIG_WT:
    bl_parent_id = "RIG_PT_StarlightAtmosphereWT"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"
    bl_context = "world"
class RIG_TB:
    bl_parent_id = "RIG_PT_StarlightAtmosphereTB"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"

# Base class
class DrawablePanel:
    @classmethod
    def poll(self, context):
        settings_available = context.scene and hasattr(context.scene.world, 'psa_atmosphere_settings')
        if not settings_available:
            return False
        # toolbar preferences are stored under preferences Class.
        prefs = context.preferences.addons['physical-starlight-atmosphere'].preferences
        if self.bl_context == "objectmode" and not prefs.toolbar_enabled:  # if drawing toolbar but it's not enabled
            return False
        return True

    def draw_header(self, context):
        self.layout.label(text='', icon=self.icon_name)

    # indented column with a padding from left
    def indentedColumn(self, squished=True):
        row = self.layout.row()
        row.separator()
        return row.column(align=squished)



############################################################################
# StarlightAtmosphere
############################################################################

class StarlightAtmosphere(DrawablePanel):
    bl_label = "Physical Atmosphere"
    @classmethod
    def poll(self, context):
        # Overriding poll method as this UI part should be present even without a world.
        prefs = context.preferences.addons['physical-starlight-atmosphere'].preferences
        if self.bl_context == "objectmode" and not prefs.toolbar_enabled:
            return False
        return True

    def draw_header(self, context):
        if context.scene.world:
            psa_gsettings = context.scene.world.psa_general_settings
            layout = self.layout
            layout.prop(psa_gsettings, 'enabled', text='')

    def draw(self, context):
        if context.scene:
            layout = self.layout
            layout.template_ID(context.scene, "world", new="world.new")
            if context.scene.world is None:
                layout.label(text="A world is required.", icon='ERROR')


class RIG_PT_StarlightAtmosphereWT(Panel, StarlightAtmosphere):
    bl_idname = "RIG_PT_StarlightAtmosphereWT"
    bl_region_type = "WINDOW"            # location of the panel
    bl_space_type = "PROPERTIES"
    bl_context = "world"


class RIG_PT_StarlightAtmosphereTB(Panel, StarlightAtmosphere):
    bl_idname = "RIG_PT_StarlightAtmosphereTB"
    bl_region_type = "UI"          # location of the panel
    bl_space_type = "VIEW_3D"      # Region not found in space type if PROPERTIES used
    bl_context = "objectmode"      # without objectmode it is not appearing as a tab
    bl_category = "Atmosphere"      # Tab label

############################################################################
# Sun
############################################################################
class Sun(DrawablePanel):
    bl_label = "Sun"
    icon_name = "LIGHT_SUN"

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            psa_gsettings = context.scene.world.psa_general_settings
            asettings = context.scene.world.psa_atmosphere_settings
            sun = context.scene.world.psa_exposed.sun_object
            layout = self.layout
            layout.enabled = psa_gsettings.enabled
            col = self.indentedColumn()
            if sun:
                col.label(text='Rotation:')
                col.prop(sun, 'rotation_euler', index=2, text="Horizontal")
                col.prop(sun, 'rotation_euler', index=0, text="Vertical")
            col.prop(asettings, 'sun_disk')
            col.prop(asettings, 'sun_lamp')
            col.prop(asettings, 'sun_diameter')
            col.prop(asettings, 'sun_temperature')
            col.prop(asettings, 'sun_intensity')
            # if prefs.use_experimental_features:
            col.prop(asettings, 'enable_binary_sun')


class RIG_PT_SunWT(RIG_WT, Panel, Sun):
    pass

class RIG_PT_SunTB(RIG_TB, Panel, Sun):
    pass


############################################################################
# Binary Sun
############################################################################
class BinarySun(DrawablePanel):
    bl_label = "Binary Sun"
    icon_name = "LIGHT_SUN"

    @classmethod
    def poll(self, context):
        settings_available = context.scene and hasattr(context.scene.world, 'psa_atmosphere_settings')
        if not settings_available:
            return False
        prefs = context.preferences.addons['physical-starlight-atmosphere'].preferences
        asettings = context.scene.world.psa_atmosphere_settings
        if asettings.enable_binary_sun:
            if self.bl_context == "objectmode" and not prefs.toolbar_enabled:
                return False
            return True
        else:
            return False


    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            psa_gsettings = context.scene.world.psa_general_settings
            asettings = context.scene.world.psa_atmosphere_settings
            layout = self.layout
            layout.enabled = psa_gsettings.enabled
            col = self.indentedColumn()
            col.prop(asettings, 'binary_distance')
            col.prop(asettings, 'binary_phase')
            col.prop(asettings, 'binary_diameter')
            col.prop(asettings, 'binary_temperature')
            col.prop(asettings, 'binary_intensity')


class RIG_PT_BinarySunWT(RIG_WT, Panel, BinarySun):
    pass

class RIG_PT_BinarySunTB(RIG_TB, Panel, BinarySun):
    pass


############################################################################
# Atmosphere
############################################################################
class Atmosphere(DrawablePanel):
    bl_label = "Atmosphere"
    icon_name= "WORLD_DATA"

    def draw(self, context):
        psa_gsettings = context.scene.world.psa_general_settings
        asettings = context.scene.world.psa_atmosphere_settings
        layout = self.layout
        layout.enabled = psa_gsettings.enabled

        col = self.indentedColumn()
        col.prop(asettings, 'atmosphere_density')
        col.prop(asettings, 'atmosphere_height')
        col.prop(asettings, 'atmosphere_intensity')
        col = self.indentedColumn()
        col.prop(asettings, 'night_intensity')

        # inline color fields
        col = self.indentedColumn()
        row = col.row(align=True)
        row.label(text='Color:')
        row.prop(asettings, 'atmosphere_color')
        row = col.row(align=True)
        row.label(text='Inscattering:')
        row.prop(asettings, 'atmosphere_inscattering')
        row = col.row(align=True)
        row.label(text='Absorption:')
        row.prop(asettings, 'atmosphere_extinction')

        col.label(text='Mie Scattering:')
        col.prop(asettings, 'atmosphere_mie')
        col.prop(asettings, 'atmosphere_mie_dir')

class RIG_PT_AtmosphereWT(RIG_WT, Panel, Atmosphere):
    pass

class RIG_PT_AtmosphereTB(RIG_TB, Panel, Atmosphere):
    pass


############################################################################
# Stars
############################################################################
class Stars(DrawablePanel):
    bl_label = "Stars"
    icon_name = 'STICKY_UVS_DISABLE'

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            psa_gsettings = context.scene.world.psa_general_settings
            asettings = context.scene.world.psa_atmosphere_settings
            stars_type = asettings.stars_type
            layout = self.layout
            layout.enabled = psa_gsettings.enabled

            row = layout.row(align=True)
            row.prop(asettings, 'stars_type', expand=True)

            if stars_type in {'procedural', 'texture'}:
                col = self.indentedColumn()
            if stars_type == 'texture':

                col.prop(asettings, 'stars_path', text="")
            if stars_type in {'procedural', 'texture'}:
                col.prop(asettings, 'stars_intensity')
                col.prop(asettings, 'stars_gamma')


class RIG_PT_StarsWT(RIG_WT, Panel, Stars):
    pass


class RIG_PT_StarsTB(RIG_TB, Panel, Stars):
    pass


############################################################################
# Ground
############################################################################
class ObjectFog(DrawablePanel):
    bl_label = "Object Fog" 
    icon_name = "MATERIAL"
    properties_type = "objectfog"

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            psa_gsettings = context.scene.world.psa_general_settings
            asettings = context.scene.world.psa_atmosphere_settings
            fog_state = asettings.fog_state
            layout = self.layout
            layout.enabled = psa_gsettings.enabled

            row = layout.row(align=True)
            row.prop(asettings, 'fog_state', expand=True)
            col = self.indentedColumn()
            col.label(text='Fog applied to ' + str(psa_gsettings.material_with_fog_count) + '/' + str(len(bpy.data.materials)) + ' materials')
            if fog_state == 'manual':
                row = col.row(align=True)
                row.operator(RIG_OT_ApplyObjectFog.bl_idname, icon='FILE_REFRESH')
                row.operator(RIG_OT_RemoveObjectFog.bl_idname)


class RIG_PT_ObjectFogWT(RIG_WT, Panel, ObjectFog):
    pass


class RIG_PT_ObjectFogTB(RIG_TB, Panel, ObjectFog):
    pass


############################################################################
# Ground
############################################################################
class Ground(DrawablePanel):
    bl_label = "Ground"
    icon_name = "VIEW_PERSPECTIVE"

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            psa_gsettings = context.scene.world.psa_general_settings
            asettings = context.scene.world.psa_atmosphere_settings
            layout = self.layout
            layout.enabled = psa_gsettings.enabled

            col = self.indentedColumn(False)
            row = col.row(align=True)
            col.prop(asettings, 'ground_visible')
            row.label(text='Color:')
            row.prop(asettings, 'ground_albedo')
            col.prop(asettings, 'ground_offset')
            col.prop(asettings, 'horizon_offset')


class RIG_PT_GroundWT(RIG_WT, Panel, Ground):
    pass


class RIG_PT_GroundTB(RIG_TB, Panel, Ground):
    pass


############################################################################
# ArtisticControls
############################################################################
class ArtisticControls(DrawablePanel):
    bl_label = "Artistic Controls"
    icon_name = "SHADERFX"

    def draw(self, context):
        psa_gsettings = context.scene.world.psa_general_settings
        asettings = context.scene.world.psa_atmosphere_settings
        layout = self.layout
        layout.enabled = psa_gsettings.enabled

        col = self.indentedColumn()
        col.prop(asettings, 'atmosphere_distance')
        col.prop(asettings, 'atmosphere_falloff')
        col.prop(asettings, 'sun_radiance_gamma')


class RIG_PT_ArtisticControlsWT(RIG_WT, Panel, ArtisticControls):
    pass


class RIG_PT_ArtisticControlsTB(RIG_TB, Panel, ArtisticControls):
    pass


############################################################################
# Footer
############################################################################
class Footer(DrawablePanel):
    bl_label = "Addon Settings"
    icon_name = "INFO"
    properties_type = "addonsettings"

    def draw(self, context):
        psa_gsettings = context.scene.world.psa_general_settings
        layout = self.layout
        layout.enabled = True

        col = self.indentedColumn()

        av = current_addon_version()
        av_text = "Addon version: " + str(av[0]) + "." + str(av[1]) + "." + str(av[2])
        col.label(text=av_text)
        vf_text = "API version format: " + str(psa_gsettings.version_format)
        col.label(text=vf_text)


class RIG_PT_FooterWT(RIG_WT, Panel, Footer):
    pass


class RIG_PT_FooterTB(RIG_TB, Panel, Footer):
    pass

class RIG_OT_ApplyObjectFog(Operator):
    bl_idname = "rig.apply_fog"
    bl_label = "apply"
    bl_description = "Apply fog to all object materials"
    # properties_type: bpy.props.StringProperty()

    def execute(self, context):
        toggle_fog(1)
        return {'FINISHED'}

class RIG_OT_RemoveObjectFog(Operator):
    bl_idname = "rig.remove_fog"
    bl_label = "clear"
    bl_description = "Remove fog from all object materials"
    # properties_type: bpy.props.StringProperty()

    def execute(self, context):
        toggle_fog(0)
        return {'FINISHED'}