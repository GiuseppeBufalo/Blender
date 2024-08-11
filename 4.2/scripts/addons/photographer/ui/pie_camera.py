import bpy
from bpy.types import Menu
from .camera_list import camera_list_panel
from ..constants import addon_name
from .camera_panel import exposure_settings

class PHOTOGRAPHER_MT_Pie_Camera(Menu):
    bl_label = "Photographer Camera Pie"

    def draw(self, context):
        scene = context.scene
        prefs = context.preferences.addons[addon_name].preferences
        layout = self.layout
        pie = layout.menu_pie()

        if scene.camera:
            settings = scene.camera.data.photographer

            #4 - LEFT
            # Exposure column
            if scene.camera and scene.camera!= bpy.data.objects.get('DroneCamera'):
                left_col = pie.column()
                row = left_col.row(align=True)
                row.prop(settings, "exposure_enabled", text="")
                sub = row.row(align=True)
                sub.enabled = settings.exposure_enabled
                sub.scale_x = 1.09
                sub.prop(settings, 'exposure_mode', expand=True)
                sub = row.row(align=False)
                sub.scale_x = 1.26
                sub.operator('exposure.picker', text='', icon = 'EYEDROPPER',emboss=False).use_scene_camera = True
                exposure_settings(self,context,settings,left_col,False,False)
                row = left_col.row(align=True)
                row.prop(settings, 'falsecolor_enabled')
                row.enabled = settings.exposure_enabled

                # White Balance column
                left_col.separator()
                col = left_col.column(align=True)

                row = col.row(align=True)
                row.prop(settings, "wb_enabled", text="")
                sub = row.row(align=True)
                sub.scale_x = 0.6
                split = sub.split(factor=0.8,align=True)
                split.prop(settings, 'color_temperature',text="Temperature")
                split.prop(settings, 'preview_color_temp',text='')
                sub.enabled = settings.wb_enabled
                picker_row = row.row(align=False)
                picker_row.scale_x = 1.26
                picker_row.operator('white_balance.picker',text='',icon='EYEDROPPER',emboss=False).use_scene_camera=True

                row = col.row(align=True)
                sub = row.row(align=True)
                sub.scale_x = 0.6
                split = sub.split(factor=0.825,align=True)
                split.prop(settings, 'tint')
                split.prop(settings, 'preview_color_tint', text='')
                sub.enabled = settings.wb_enabled
                picker_row = row.row(align=False)
                picker_row.scale_x = 1.26
                picker_row.label(text='')

            else:
                pie.separator()

            #6 - RIGHT
            col = pie.column(align=True)
            from ..render_queue import render_buttons
            render_buttons(self,context,col)

        else:
            pie.separator()
            pie.separator()

        #2 - BOTTOM
        bottom = pie.column()
        camera_list_panel(context,bottom)

        #8 - TOP
        if scene.camera and scene.camera!= bpy.data.objects.get('DroneCamera'):
            cam_obj = scene.camera
            cam = cam_obj.data
            col = pie.column()
            
            
            row = col.row(align=True)
            if cam.type == 'ORTHO':
                row.prop(cam, 'ortho_scale')
                 # Aligning to the buttons
                row.label(text='       ')
            elif context.scene.render.engine == 'CYCLES' and settings.fisheye:
                row.prop(settings,'fisheye_focal', text='Focal Length')
                col.prop(cam.cycles,'fisheye_fov')
            else:
                row.prop(settings, "focal")
            if cam.type != 'ORTHO':
                sub = row.row(align=False)
                sub.scale_x = 1.26
                sub.operator("photographer.dollyzoom", text="", icon='VIEW_ZOOM',emboss=False)

            row = col.row(align=True)
            if settings.show_focus_plane:
                row.operator("photographer.delete_focus_plane", text="", icon='CANCEL').camera=cam_obj.name
            else:
                row.operator("photographer.create_focus_plane", text="", icon='NORMALS_FACE').camera=cam_obj.name

            if prefs.focus_eyedropper_func == 'AFS':
                row.prop(scene.camera.data.dof, "focus_distance")
                sub = row.row(align=False)
                sub.scale_x = 1.26
                sub.operator("photographer.focus_single", text="", icon='EYEDROPPER',emboss=False)
            elif prefs.focus_eyedropper_func == 'AFT':
                if scene.camera.data.dof.focus_object is not None:
                    split = row.split(factor=0.86)
                    split.operator("photographer.focus_tracking_cancel", text="Cancel AF Tracking", icon='OBJECT_DATA')
                    split.label(text='')
                else:
                    row.prop(scene.camera.data.dof, "focus_distance")
                    sub = row.row(align=False)
                    sub.scale_x = 1.26
                    sub.operator("photographer.focus_tracking", text="", icon='EYEDROPPER',emboss=False)
            elif prefs.focus_eyedropper_func == 'BL_PICKER':
                split = row.split(factor=0.88)
                split.prop(scene.camera.data.dof, "focus_distance")
                split.label(text='')
                if scene.camera.data.dof.focus_object is not None:
                    split.enabled = False
                row = col.row(align=True)
                row.label(text='Focus Object')
                split = row.split(factor=0.83)
                split.prop(scene.camera.data.dof, 'focus_object', text="")
                split.label(text='')

            row = col.row(align=True)
            row.prop(settings, "use_dof", text="")
            if not settings.aperture_slider_enable:
                sub = row.row(align=False)
                sub.scale_x = 1.09
                sub.prop(settings, 'aperture_preset', text="")
            else:
                row.prop(settings, 'aperture', slider=True)

            sub = row.row(align=False)
            sub.scale_x = 1.26
            sub.prop(settings,'aperture_slider_enable', icon='SETTINGS', text='',emboss=False)

            row = col.row(align=True)
            row.prop(settings, "lens_shift")
            sub = row.row(align=False)
            sub.scale_x = 1.26
            sub.operator("photographer.auto_lens_shift", text="", icon='EVENT_A',emboss=False).camera=cam_obj.name

            row = col.row(align=True)
            sub_row = row.row(align=True)
            sub_row.prop(cam,'type',text='')
            if context.scene.render.engine == 'CYCLES':
                row.prop(settings, 'fisheye')

            if context.scene.render.engine == 'CYCLES' and settings.fisheye:
                sub_row.enabled = False
            # Aligning to the buttons
            row.label(text='       ')

        else:
            pie.separator()


        #7 - TOP - LEFT
        # pie.operator("view3d.cycle_camera", text='Previous', icon="TRIA_LEFT").previous=True
        pie.separator()
        #9 - TOP - RIGHT
        pie.separator()
        #1 - BOTTOM - LEFT
        pie.separator()
        #3 - BOTTOM - RIGHT
        pie.separator()
