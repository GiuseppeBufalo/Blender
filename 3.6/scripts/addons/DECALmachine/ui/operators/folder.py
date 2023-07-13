import bpy
from bpy.props import StringProperty
import os
from ... utils.registration import get_prefs
from ... utils.system import open_folder


class OpenInstantLocation(bpy.types.Operator):
    bl_idname = "machin3.open_instant_location"
    bl_label = "MACHIN3: Open Instant Decal Location"
    bl_options = {'REGISTER', 'UNDO'}

    type: StringProperty(name="Instant Type", default='ATLAS')

    @classmethod
    def description(cls, context, properties):
        if properties.type == 'ATLAS':
            return "Open Instant Atlas Location"
        elif properties.type == 'TRIMSHEET':
            return "Open Instant Trim Sheet Location"
        elif properties.type == 'TRIMTEXTURES':
            return "Open Instant Trim Textures Location"
        elif properties.type == 'INFOTEXTURES':
            return "Open Instant Info Decal Source Textures Location"
        elif properties.type == 'INFOFONTS':
            return "Open Instant Info Decal Font Location"
        elif properties.type == 'DECAL':
            return "Open Instant Decal Location"

    def execute(self, context):
        folder = 'atlasinstant' if self.type == 'ATLAS' else 'triminstant' if self.type == 'TRIMSHEET' else 'trimtextures' if self.type == 'TRIMTEXTURES' else 'infotextures' if self.type == 'INFOTEXTURES' else 'infofonts' if self.type == 'INFOFONTS' else 'decalinstant'

        if folder:
            instantpath = os.path.join(get_prefs().assetspath, 'Create', folder)

            if os.path.exists(instantpath):
                open_folder(instantpath)

        return {'FINISHED'}


class OpenUserDecalLib(bpy.types.Operator):
    bl_idname = "machin3.open_user_decal_lib"
    bl_label = "MACHIN3: open_user_decal_lib"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.userdecallibs

    def execute(self, context):
        userdecallib = context.scene.userdecallibs
        assetspath = get_prefs().assetspath
        librarypath = os.path.join(assetspath, 'Decals', userdecallib)

        if os.path.exists(librarypath):
            open_folder(librarypath)

        return {'FINISHED'}
