import bpy
from bpy.props import StringProperty, BoolProperty
import os
from .. utils.system import abspath, open_folder
from .. utils.property import step_list


class Open(bpy.types.Operator):
    bl_idname = "machin3.filebrowser_open"
    bl_label = "MACHIN3: Open in System's filebrowser"
    bl_description = "Open the current location in the System's own filebrowser\nALT: Open .blend file"

    path: StringProperty(name="Path")
    blend_file: BoolProperty(name="Open .blend file")

    @classmethod
    def poll(cls, context):
        return context.area.type == 'FILE_BROWSER'

    def execute(self, context):
        params = context.space_data.params
        directory = abspath(params.directory.decode())

        if self.blend_file:
            active_file = context.active_file

            if active_file.asset_data:
                bpy.ops.asset.open_containing_blend_file()

            else:
                path = os.path.join(directory, active_file.relative_path)
                bpy.ops.machin3.open_library_blend(blendpath=path)

        else:
            open_folder(directory)

        return {'FINISHED'}


class Toggle(bpy.types.Operator):
    bl_idname = "machin3.filebrowser_toggle"
    bl_label = "MACHIN3: Toggle Filebrowser"
    bl_description = ""

    type: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.area.type == 'FILE_BROWSER'

    def execute(self, context):
        params = context.space_data.params

        if self.type == 'SORT':

            if context.area.ui_type == 'FILES':
                if params.sort_method == 'FILE_SORT_ALPHA':
                    params.sort_method = 'FILE_SORT_TIME'

                else:
                    params.sort_method = 'FILE_SORT_ALPHA'

            elif context.area.ui_type == 'ASSETS':
                base_libs = ['LOCAL']

                if bpy.app.version >= (3, 5, 0):
                    base_libs.insert(0, 'ALL')
                    base_libs.append('ESSENTIALS')

                asset_libraries = base_libs + [lib.name for lib in context.preferences.filepaths.asset_libraries]
                current = params.asset_library_ref

                params.asset_library_ref = step_list(current, asset_libraries, 1)

        elif self.type == 'DISPLAY_TYPE':

            if context.area.ui_type == 'FILES':
                if params.display_type == 'LIST_VERTICAL':
                    params.display_type = 'THUMBNAIL'

                else:
                    params.display_type = 'LIST_VERTICAL'

            elif context.area.ui_type == 'ASSETS':

                if params.asset_library_ref != 'LOCAL':
                    import_types = ['LINK', 'APPEND', 'APPEND_REUSE']

                    if bpy.app.version >= (3, 5, 0):
                        import_types.insert(0, 'FOLLOW_PREFS')

                    current = params.import_type
                    params.import_type = step_list(current, import_types, 1)

        elif self.type == 'HIDDEN':
            if context.area.ui_type == 'FILES':
                params.show_hidden = not params.show_hidden
                params.use_filter_backup = params.show_hidden

        return {'FINISHED'}


class CycleThumbs(bpy.types.Operator):
    bl_idname = "machin3.filebrowser_cycle_thumbnail_size"
    bl_label = "MACHIN3: Cycle Thumbnail Size"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    reverse: BoolProperty(name="Reverse Cycle Diretion")

    @classmethod
    def poll(cls, context):
        return context.area.type == 'FILE_BROWSER' and context.space_data.params.display_type == 'THUMBNAIL'

    def execute(self, context):
        params = context.space_data.params
        sizes = ['TINY', 'SMALL', 'NORMAL', 'LARGE']
        params.display_size = step_list(params.display_size, sizes, -1 if self.reverse else 1, loop=True)
        return {'FINISHED'}
