
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

import bpy
from bpy.utils import register_class, unregister_class
# from ZenUV.prop.zuv_preferences import get_prefs
from shutil import copy
import os
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from ZenUV.utils.clib.lib_init import register_library, unregister_library, get_zenlib_name, is_zenlib_present
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.constants import zenuv_update_filename, zenuv_update_filter


class ZUVLibrary_OT_InstallFile(Operator, ImportHelper):
    bl_idname = "view3d.zenuv_install_library"
    bl_label = "Install " + ZuvLabels.CLIB_NAME
    bl_description = "Install and Register Zen UV Dynamic Library"

    def extention():
        filename, file_extension = os.path.splitext(get_zenlib_name())
        return file_extension

    filter_glob: StringProperty(
        default="*{}".format(extention()),
        options={'HIDDEN'}
    )
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    filename: StringProperty(maxlen=1024)
    directory: StringProperty(maxlen=1024)

    def check(self, context):
        self.filename = get_zenlib_name()

    def execute(self, context):
        # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences

        path = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + get_zenlib_name()

        ### Only if we didn't change path
        if is_zenlib_present() and (self.filepath.lower() == path.lower()):
            # addon_prefs.zen_lib = True
            self.report({"INFO"}, ZuvLabels.CLIB_NAME + " is already installed. Trying to activate...")
            register_library()
        else:
            # Copy Library to
            copy(self.filepath, path)
            print("Zen UV: File ", self.filepath)
            print("          Copied to: ", path)
            if is_zenlib_present():
                # addon_prefs.zen_lib = True
                register_library()
                self.report({"INFO"}, ZuvLabels.CLIB_NAME + " was installed!")
            else:
                self.report({"ERROR"}, "For some reason, the library cannot be installed. Try to do it manually")
        return {'FINISHED'}


class ZUVLibrary_OT_Check(Operator):
    bl_idname = "view3d.zenuv_check_library"
    bl_label = "Check Library"
    bl_description = "Check Zen UV Dynamic Library"

    def execute(self, context):
        # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        if is_zenlib_present():
            # addon_prefs.zen_lib = True
            self.report({"INFO"}, "The library is already installed.  Trying to activate...")
            register_library()
        else:
            self.report({"WARNING"}, "The library is not found. First, install in the Zen UV settings.")
        return {'FINISHED'}


class ZUV_OT_Update(Operator, ImportHelper):
    bl_idname = "uv.zenuv_update_addon"
    bl_label = "Update Zen UV"
    bl_description = "Update Zen UV add-on"

    filename_ext = ".zip"
    use_filter = True
    filter_glob: StringProperty(
        default=zenuv_update_filter,
        options={'HIDDEN'}
    )
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    filename: StringProperty(maxlen=1024)
    directory: StringProperty(maxlen=1024)

    def check(self, context):
        self.filename = zenuv_update_filename

    def execute(self, context):
        message = "Zen UV: Select only one *.zip file containing an addon."
        message_02 = "Zen UV: The file should be the type of ZenUV_x_x.zip."
        if not self.files or len(self.files) > 1:
            self.report({"WARNING"}, message)
            return {'CANCELLED'}
        filename, extension = os.path.splitext(self.filepath)
        if extension != '.zip':
            self.report({"WARNING"}, message)
            return {'CANCELLED'}
        file = self.files[0]
        if not file.name.startswith("ZenUV"):
            self.report({"WARNING"}, message_02)
            return {'CANCELLED'}

        fullname = os.path.join(self.directory, file.name)
        print("Zen UV: Updating by ", fullname)

        unregister_library()
        bpy.ops.preferences.addon_install(
            overwrite=True,
            target='DEFAULT',
            filepath=fullname,
            filter_folder=True,
            filter_python=True,
            filter_glob="*.zip"
        )

        return {'FINISHED'}


class ZUVLibrary_OT_Unregister(Operator):
    bl_idname = "uv.zenuv_unregister_library"
    bl_label = "Unregister Zen UV Core Library"
    bl_description = "Unregister Zen UV Core Library"

    def execute(self, context):
        unregister_library()

        return {'FINISHED'}


classes = (
    ZUVLibrary_OT_InstallFile,
    ZUVLibrary_OT_Check,
    ZUVLibrary_OT_Unregister,
    ZUV_OT_Update
)


def register():
    for cl in classes:
        register_class(cl)

    register_library()


def unregister():

    for cl in classes:
        unregister_class(cl)

    unregister_library()


if __name__ == "__main__":
    pass
