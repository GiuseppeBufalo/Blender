import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
import os
from mathutils import Vector
from .. utils.asset import get_asset_library_reference, get_most_used_local_catalog_id, get_registered_library_references, set_asset_library_reference, get_asset_import_method, set_asset_import_method, get_asset_details_from_space, get_asset_ids
from .. utils.draw import draw_fading_label, draw_init, draw_label
from .. utils.property import step_list
from .. utils.registration import get_prefs
from .. utils.system import abspath, open_folder
from .. utils.ui import get_mouse_pos, get_scale, ignore_events, wrap_mouse
from .. utils.workspace import get_window_region_from_area, get_3dview_area
from .. colors import red, white

class Open(bpy.types.Operator):
    bl_idname = "machin3.filebrowser_open"
    bl_label = "MACHIN3: Open in System's filebrowser"
    bl_description = "Open the current location in the System's own filebrowser\nALT: Open .blend file"

    path: StringProperty(name="Path")
    blend_file: BoolProperty(name="Open .blend file")

    @classmethod
    def poll(cls, context):
        if context.area:
            return context.area.type == 'FILE_BROWSER'

    def execute(self, context):
        space = context.space_data
        params = space.params

        directory = abspath(params.directory.decode())
        active_file = context.active_file

        if active_file:
            if self.blend_file:

                if active_file.asset_data:
                    _, _, local_id = get_asset_ids(context)

                    if not local_id:
                        bpy.ops.asset.open_containing_blend_file()

                    else:
                        area = get_3dview_area(context)

                        if area:
                            region, region_data = get_window_region_from_area(area)

                            with context.temp_override(area=area, region=region, region_data=region_data):
                                draw_fading_label(context, text="The blend file containing this asset is already open.", color=red)

                else:
                    path = os.path.join(directory, active_file.relative_path)
                    bpy.ops.machin3.open_library_blend(blendpath=path)

            else:

                if active_file.asset_data:
                    _, libpath, _, _ = get_asset_details_from_space(context, space, debug=False)

                    if libpath:
                        open_folder(libpath)

                else:
                    open_folder(directory)

            return {'FINISHED'}
        return {'CANCELLED'}

class Toggle(bpy.types.Operator):
    bl_idname = "machin3.filebrowser_toggle"
    bl_label = "MACHIN3: Toggle Filebrowser"
    bl_description = ""

    type: StringProperty()

    @classmethod
    def poll(cls, context):
        if context.area:
            return context.area.type == 'FILE_BROWSER'

    @classmethod
    def description(cls, context, properties):
        if context.area.ui_type == 'ASSETS' and properties.type == 'DISPLAY_TYPE':
            return f"Cycle Display Type: {context.space_data.params.display_type}"
        return "Toggle/Cycle SORT, DISPLAY_TYPE, HIDDEN"

    def execute(self, context):
        params = context.space_data.params

        if self.type == 'SORT':

            if context.area.ui_type == 'FILES':
                if params.sort_method == 'FILE_SORT_ALPHA':
                    params.sort_method = 'FILE_SORT_TIME'

                else:
                    params.sort_method = 'FILE_SORT_ALPHA'

            elif context.area.ui_type == 'ASSETS':
                asset_libraries = get_registered_library_references(context)

                current = get_asset_library_reference(params)
                next = step_list(current, asset_libraries, 1)

                set_asset_library_reference(params, next)

                if next == 'LOCAL':
                    if catalog_id := get_most_used_local_catalog_id():
                        params.catalog_id = catalog_id

        elif self.type == 'DISPLAY_TYPE':

            if context.area.ui_type == 'FILES':
                if params.display_type == 'LIST_VERTICAL':
                    params.display_type = 'THUMBNAIL'

                else:
                    params.display_type = 'LIST_VERTICAL'

            elif context.area.ui_type == 'ASSETS':
                if params.display_type == 'THUMBNAIL':
                    params.display_type = 'LIST_VERTICAL'

                elif params.display_type == 'LIST_VERTICAL':
                    params.display_type = 'LIST_HORIZONTAL'

                else:
                    params.display_type = 'THUMBNAIL'

        elif self.type == 'HIDDEN':
            if context.area.ui_type == 'FILES':
                params.show_hidden = not params.show_hidden
                params.use_filter_backup = params.show_hidden

            elif context.area.ui_type == 'ASSETS':

                current = get_asset_library_reference(params)

                if current != 'LOCAL':
                    import_methods = ['LINK', 'APPEND', 'APPEND_REUSE']

                    if bpy.app.version >= (3, 5, 0):
                        import_methods.insert(0, 'FOLLOW_PREFS')

                    current = get_asset_import_method(params)
                    next = step_list(current, import_methods, 1)
                    set_asset_import_method(params, next)

        return {'FINISHED'}

class AdjustThumbnailSize(bpy.types.Operator):
    bl_idname = "machin3.filebrowser_adjust_thumbnail_size"
    bl_label = "MACHIN3: Adjust Thumbnail Size"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    size: FloatProperty(name="Thumbnail Size", min=24, max=256)

    reverse: BoolProperty(name="Reverse Cycle Diretion")

    @classmethod
    def poll(cls, context):
        if context.area:
            return context.area.type == 'FILE_BROWSER' and context.space_data.params.display_type == 'THUMBNAIL'

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self, None)

            scale_compensate = context.preferences.system.ui_scale * get_prefs().modal_hud_scale

            text_size = int(self.window_size.y * 0.75 / scale_compensate) 
            title = f"{int(self.size)}"

            x = (self.window_size.x / 2)
            y = (self.window_size.y / 2) - ((text_size * scale_compensate) / 3)  # not sure why 3, but 2 does not center it properly

            draw_label(context, title=title, coords=Vector((x, y)), center=True, size=text_size, color=white, alpha=0.5)

            if self.size == 24:

                draw_label(context, title="very smol", coords=Vector((x, y)), offset=text_size / 4, center=True, size=12 / scale_compensate, color=white, alpha=0.25)
            elif self.size == 256:
                draw_label(context, title="very big", coords=Vector((x, y)), offset=text_size / 4, center=True, size=12 / scale_compensate, color=white, alpha=0.25)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)
            wrap_mouse(self, context, x=True, y=False)

            deltax = self.mouse_pos.x - self.last_mouse.x
            sensitivity = 0.1 * self.scale

            self.size += deltax * sensitivity
            context.space_data.params.display_size = int(self.size)

        if event.value == 'RELEASE' or event.type in ['LEFTMOUSE', 'SPACE']:
            self.finish(context)#
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)

            context.space_data.params.display_size = self.init_size
            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos
        return {'RUNNING_MODAL'}

    def finish(self, context):
        bpy.types.SpaceFileBrowser.draw_handler_remove(self.HUD, 'WINDOW')#
        context.window.cursor_set('DEFAULT')

    def invoke(self, context, event):
        if bpy.app.version >= (4, 0, 0) and get_prefs().filebrowser_modal_thumbnail:
            params = context.space_data.params
            
            self.size = params.display_size
            self.init_size = self.size

            get_mouse_pos(self, context, event)
            context.window.cursor_set('SCROLL_X')
            self.last_mouse = self.mouse_pos

            self.scale = get_scale(context)

            for region in context.area.regions:
                if region.type == 'WINDOW':
                    self.window_size = Vector((region.width, region.height))
                    break

            self.area = context.area
            self.HUD = bpy.types.SpaceFileBrowser.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        else:
            return self.execute(context)

    def execute(self, context):
        params = context.space_data.params

        if bpy.app.version >= (4, 0, 0):
            if params.display_size == 256 and not self.reverse:
                params.display_size = 16

            elif params.display_size == 16 and self.reverse:
                params.display_size = 256

            else:
                params.display_size += -20 if self.reverse else 20

        else:
            sizes = ['TINY', 'SMALL', 'NORMAL', 'LARGE']
            params.display_size = step_list(params.display_size, sizes, -1 if self.reverse else 1, loop=True)

        return {'FINISHED'}
