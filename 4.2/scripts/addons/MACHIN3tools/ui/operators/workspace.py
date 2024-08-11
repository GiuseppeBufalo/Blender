import bpy
from bpy.props import StringProperty
from ... utils.registration import get_addon, enable_addon

class SwitchWorkspace(bpy.types.Operator):
    bl_idname = "machin3.switch_workspace"
    bl_label = "Switch Workspace"
    bl_options = {'REGISTER'}

    name: StringProperty()

    @classmethod
    def description(cls, context, properties):
        return "Switch to Workplace '%s' and sync Viewport\nALT: Also sync Shading and Overlays" % (properties.name)

    def invoke(self, context, event):
        ws = bpy.data.workspaces.get(self.name)

        view = self.get_view(context, ws)
        shading = self.get_shading(context, ws)
        overlay = self.get_overlay(context, ws)

        if ws and context.window.workspace == ws:
            ws = bpy.data.workspaces.get(f"{self.name}.alt")

            if ws:
                bpy.context.window.workspace = ws

                if shading:
                    self.set_shading_and_overlay(ws, shading, overlay)

        elif ws and f"{ws.name}.alt" == context.workspace.name:
            bpy.context.window.workspace = ws

            if shading:
                self.set_shading_and_overlay(ws, shading, overlay)

        elif ws:
            bpy.context.window.workspace = ws

            if shading and event.alt:
                self.set_shading_and_overlay(ws, shading, overlay)

        if ws and view:
            self.set_view(ws, view)

        return {'FINISHED'}

    def get_shading(self, context, workspace):
        if context.space_data.type == 'VIEW_3D':
            shading = context.space_data.shading

            s = {'shading_type': shading.type,
                 'shading_color_type': shading.color_type,
                 'shading_light': shading.light,
                 'studio_light': shading.studio_light,
                 'rotate_z': shading.studiolight_rotate_z,
                 'background_alpha': shading.studiolight_background_alpha,
                 'background_blur': shading.studiolight_background_blur,
                 'studiolight_intensity': shading.studiolight_intensity,
              
                 'use_scene_lights': shading.use_scene_lights,
                 'use_scene_world': shading.use_scene_world,
                 'use_scene_lights_render': shading.use_scene_lights_render,
                 'use_scene_world_render': shading.use_scene_world_render,
              
                 'show_cavity': shading.show_cavity,
                 'show_shadows': shading.show_shadows,
                 'cavity_type': shading.cavity_type,
                 'cavity_ridge_factor': shading.cavity_ridge_factor,
                 'cavity_valley_factor': shading.cavity_valley_factor,
                 'curvature_ridge_factor': shading.curvature_ridge_factor,
                 'curvature_valley_factor': shading.curvature_valley_factor,
                 'show_object_outline': shading.show_object_outline,
              
                 'show_xray': shading.show_xray,
                 'xray_alpha': shading.xray_alpha,
              
                 'show_backface_culling': shading.show_backface_culling,

                 'use_compositor': shading.use_compositor,
                 'render_pass': shading.render_pass}

            return s

    def get_overlay(self, context, workspace):
        if context.space_data.type == 'VIEW_3D':
            overlay = context.space_data.overlay

            o = {'show_overlays': overlay.show_overlays,

                 'show_wireframes': overlay.show_wireframes,
                 'wireframe_threshold': overlay.wireframe_threshold,
                 
                 'show_face_orientation': overlay.show_face_orientation,
                 
                 'show_floor': overlay.show_floor,
                 'show_ortho_grid': overlay.show_ortho_grid,
                 'show_axis_x': overlay.show_axis_x,
                 'show_axis_y': overlay.show_axis_y,
                 'show_axis_z': overlay.show_axis_z,
                 
                 'show_relationship_lines': overlay.show_relationship_lines,
                 
                 'show_cursor': overlay.show_cursor,
                 'show_object_origins': overlay.show_object_origins,
                 'show_object_origins_all': overlay.show_object_origins_all}

            return o

    def set_shading_and_overlay(self, workspace, shading, overlay):
        for screen in workspace.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':

                            space.shading.type = shading['shading_type']
                            space.shading.color_type = shading['shading_color_type']
                            space.shading.light = shading['shading_light']
                            space.shading.studio_light = shading['studio_light']
                            space.shading.studiolight_rotate_z = shading['rotate_z']
                            space.shading.studiolight_background_alpha = shading['background_alpha']
                            space.shading.studiolight_background_blur = shading['background_blur']
                            space.shading.studiolight_intensity = shading['studiolight_intensity']

                            space.shading.use_scene_lights = shading['use_scene_lights']
                            space.shading.use_scene_world = shading['use_scene_world']
                            space.shading.use_scene_lights_render = shading['use_scene_lights_render']
                            space.shading.use_scene_world_render = shading['use_scene_world_render']

                            space.shading.show_cavity = shading['show_cavity']
                            space.shading.show_shadows = shading['show_shadows']
                            space.shading.cavity_type = shading['cavity_type']
                            space.shading.cavity_ridge_factor = shading['cavity_ridge_factor']
                            space.shading.cavity_valley_factor = shading['cavity_valley_factor']
                            space.shading.curvature_ridge_factor = shading['curvature_ridge_factor']
                            space.shading.curvature_valley_factor = shading['curvature_valley_factor']
                            space.shading.show_object_outline = shading['show_object_outline']

                            space.shading.show_xray = shading['show_xray']
                            space.shading.xray_alpha = shading['xray_alpha']

                            space.shading.show_backface_culling = shading['show_backface_culling']

                            space.shading.use_compositor = shading['use_compositor']
                            space.shading.render_pass = shading['render_pass']

                            space.overlay.show_overlays = overlay['show_overlays']

                            space.overlay.show_wireframes = overlay['show_wireframes']
                            space.overlay.wireframe_threshold = overlay['wireframe_threshold']

                            space.overlay.show_face_orientation = overlay['show_face_orientation']

                            space.overlay.show_floor = overlay['show_floor']
                            space.overlay.show_ortho_grid = overlay['show_ortho_grid']
                            space.overlay.show_axis_x = overlay['show_axis_x']
                            space.overlay.show_axis_y = overlay['show_axis_y']
                            space.overlay.show_axis_z = overlay['show_axis_z']

                            space.overlay.show_relationship_lines = overlay['show_relationship_lines']

                            space.overlay.show_cursor = overlay['show_cursor']
                            space.overlay.show_object_origins = overlay['show_object_origins']
                            space.overlay.show_object_origins_all = overlay['show_object_origins_all']

                            return

    def get_view(self, context, workspace):
        view = context.space_data

        if view.type == 'VIEW_3D':
            r3d = context.space_data.region_3d

            if r3d.view_perspective == 'PERSP':

                view = {'view_location': r3d.view_location,
                        'view_rotation': r3d.view_rotation,
                        'view_distance': r3d.view_distance,
                       
                        'view_perspective': r3d.view_perspective,
                       
                        'is_perspective': r3d.is_perspective,
                        'is_side_view': r3d.is_orthographic_side_view}

                return view

    def set_view(self, workspace, view):
        for screen in workspace.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            r3d = space.region_3d

                            if r3d.view_perspective != 'CAMERA':

                                r3d.view_location = view['view_location']
                                r3d.view_rotation = view['view_rotation']
                                r3d.view_distance = view['view_distance']

                                r3d.view_perspective = view['view_perspective']

                                r3d.is_perspective = view['is_perspective']
                                r3d.is_orthographic_side_view = view['is_side_view']

                            return

class GetIconNameHelp(bpy.types.Operator):
    bl_idname = "machin3.get_icon_name_help"
    bl_label = "MACHIN3: Get Icon Name Help"
    bl_description = ""
    bl_options = {'INTERNAL'}

    def execute(self, context):
        enabled, _, _, _ = get_addon('Icon Viewer')

        if not enabled:
            enabled, _ = enable_addon(context, 'Icon Viewer')

        if enabled:
            bpy.ops.iv.icons_show('INVOKE_DEFAULT', filter_auto_focus="", filter="", selected_icon="")

        return {'FINISHED'}
