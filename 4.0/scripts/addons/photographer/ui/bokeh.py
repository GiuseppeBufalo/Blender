import bpy

# Function to add Bokeh and Optical Vignetting to Camera Properties UI
def bokeh_ui(self, context, add_on_panel=False):
    layout = self.layout
    if add_on_panel:
        settings = context.scene.camera.data.photographer
        cam_obj = context.scene.camera
    else:
        settings = context.camera.photographer
        cam_obj = context.object

    no_textures = "No texture found in folder."
    no_textures2 = "Set Path in Add-on Preferences."

    engine = context.scene.render.engine
    if engine in {'CYCLES','LUXCORE'} or (engine=='BLENDER_EEVEE' and bpy.app.version >= (2, 93, 0)):
        box = layout.box()
        top_row = box.row(align=True)
        top_row.prop(settings,'opt_vignetting')
        for c in cam_obj.children:
            if c.get("is_opt_vignetting", False):
                top_row.prop(c, "hide_viewport", text='', icon_only=True, emboss=False)
                top_row.prop(c, "hide_render", text='', icon_only=True, emboss=False)
                        
        if settings.opt_vignetting:
            for c in cam_obj.children:
                if c.get("is_opt_vignetting", False):
                    if c.display_type != 'TEXTURED':
                        box.operator('photographer.fix_display_type', icon='ERROR').obj=c.name
            col = box.column(align=True)
            col.prop(settings,'ov_scale', text='Scale', slider=True)
            if not engine == 'LUXCORE':
                col.prop(settings,'ov_rotation', slider=True)
            col.template_icon_view(settings, "opt_vignetting_tex",
                                   show_labels=True, scale=5)
                                   
            if engine=='BLENDER_EEVEE':
                col = box.column(align=True)
                col.label(text='Requires Jitter and high Sample count', icon='ERROR')
                col.prop(context.scene.eevee,'use_bokeh_jittered')
                col.prop(context.scene.eevee,'bokeh_overblur')
                col.separator()
                col.prop(context.scene.eevee,'taa_render_samples')
                col.prop(context.scene.eevee,'taa_samples')
        
        if engine in {'CYCLES','LUXCORE'}:    
            box = layout.box()
            top_row = box.row(align=True)
            top_row.prop(settings,'bokeh')
            if not engine == 'LUXCORE':
                for c in cam_obj.children:
                    if c.get("is_bokeh_plane", False):
                        top_row.prop(c, "hide_viewport", text='', icon_only=True, emboss=False)
                        top_row.prop(c, "hide_render", text='', icon_only=True, emboss=False)
            if settings.bokeh:
                col = box.column(align=True)
                if not engine == 'LUXCORE':
                    col.prop(settings,'bokeh_brightness', slider=True)
                    col.prop(settings,'bokeh_rotation', slider=True)
                col.template_icon_view(settings, "bokeh_tex",
                                       show_labels=True, scale=5)
                                              
    else:
        layout.label(text="Check Lens Panel for settings")
                        