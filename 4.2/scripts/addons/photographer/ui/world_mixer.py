import bpy
from ..operators import world as wd
from ..constants import addon_name

hdri_scale_y = 11

def world_mixer_draw_header_preset(self,context):
    layout = self.layout
    row = layout.row(align=True)

    if context.preferences.addons[addon_name].preferences.show_compact_ui:
        if context.scene.world:
            world_name = context.scene.world.name
            label = (world_name[:12] + '...') if len(world_name) > 14 else world_name
            row.label(text=label)
    # sub = row.row(align=True)
    row.operator('lightmixer.cycle_world', text='', icon='TRIA_LEFT').previous=True
    row.operator('lightmixer.cycle_world', text='', icon='TRIA_RIGHT').previous=False

def world_mixer_draw(self,context):
    layout = self.layout
    layout.use_property_split = False

    world_box = layout.box()
    # Column to align buttons together
    world_col = world_box.column(align=True)
    row = world_col.row(align=True)

    scene = context.scene
    world =scene.world
    lightmixer = scene.lightmixer

    if world:
        if world.get('solo',False):
            icn = 'EVENT_S'
        elif world.get('enabled',True):
            icn = 'OUTLINER_OB_LIGHT'
        else:
            icn = 'LIGHT'
        row.operator("lightmixer.world_enable", text="", icon=icn, emboss=False)

    name_row = row.row(align=True)
    if scene:
        name_row.template_ID(scene, "world", new="world.new")
    elif world:
        name_row.template_ID(space, "pin_id")

    intensity_row = world_col.row(align=True)

    if world and not world.get('enabled',True):
        if not world.get('solo',False):
            name_row.enabled = False
            intensity_row.enabled = False

    if world:
        wd_lightmixer = world.lightmixer
        if context.scene.render.engine == "LUXCORE" and not world.luxcore.use_cycles_settings:
            intensity_row.prop(lightmixer, 'world_show_more', text="",
                            icon='TRIA_DOWN' if lightmixer.world_show_more else 'TRIA_RIGHT',
                            emboss=False, icon_only=True)

            sub = intensity_row.row(align=True)
            if world.luxcore.light != 'none':
                # Turn red if Solo
                if world.get('solo',False):
                    name_row.alert = True
                    sub.alert = True

                if world.get('enabled',True):
                    if world.luxcore.light != 'none':
                        if world.luxcore.light == 'sky2':
                            sub.prop(world.luxcore,'sun_sky_gain')
                        else:
                            sub.prop(world.luxcore,'gain')
                else:
                    sub.enabled = False
                    sub.prop(world,'strength', text='Gain')
                sub.prop(world.luxcore,'exposure', text='')

                minus = sub.operator("lightmixer.emissive_stop", text='', icon='REMOVE')
                minus.factor = -0.5
                minus.world = True
                plus = sub.operator("lightmixer.emissive_stop", text='', icon='ADD')
                plus.factor = 0.5
                plus.world = True
            else:
                sub.label(text="Sky is set to None")
                sub.alignment='CENTER'

            if lightmixer.world_show_more:
                more_col = world_box.column(align=False)
                more_col.enabled = world.enabled
                row = more_col.row(align=True)
                row.prop(world.luxcore, "light", expand=True)
                if world.luxcore.light != 'none':
                    row = more_col.row(align=True)
                    if world.luxcore.color_mode == 'temperature':
                        row.prop(world.luxcore, "temperature", text='')
                    else:
                        row.prop(world.luxcore, "rgb_gain", text='')
                    icn = 'EVENT_K' if world.luxcore.color_mode == 'temperature' else 'EVENT_C'
                    row.prop(world.luxcore, "color_mode", icon=icn, icon_only=True)
                    if world.luxcore.light == 'sky2':
                        row = more_col.row(align=True)
                        row.prop(world.luxcore, "sun")
                    if world.luxcore.light == 'infinite':
                        row = more_col.row(align=True)
                        row.template_ID(world.luxcore, "image", open="image.open")

                    row = more_col.row(align=True)
                    row.prop(world.luxcore, "visibility_indirect_diffuse", toggle=True)
                    row.prop(world.luxcore, "visibility_indirect_glossy", toggle=True)
                    row.prop(world.luxcore, "visibility_indirect_specular", toggle=True)

        else:
            backgrounds = wd.get_background(context)

            if not backgrounds:
                intensity_row.label(text='No Background nodes in World shader')
            else:
                intensity_row.prop(lightmixer, 'world_show_more', text="",
                                icon='TRIA_DOWN' if lightmixer.world_show_more else 'TRIA_RIGHT',
                                emboss=False, icon_only=True)

                sub = intensity_row.row(align=True)
                # Turn red if Solo
                if world:
                    if world.get('solo',False):
                        sub.alert = True

                # if intensity_row.enabled:
                sub.prop(backgrounds[0].inputs[1],'default_value', text=backgrounds[0].name+' Strength')
                # else:
                #     sub.label(text='Strength: '+ str(round(backgrounds[0].get('strength'),3)))
                minus = sub.operator("lightmixer.emissive_stop", text='', icon='REMOVE')
                minus.factor = -0.5
                minus.world = True
                minus.background_name = backgrounds[0].name
                plus = sub.operator("lightmixer.emissive_stop", text='', icon='ADD')
                plus.factor = 0.5
                plus.world = True
                plus.background_name = backgrounds[0].name

                if len(backgrounds)>=2:
                    for bg in backgrounds[1:]:
                        bg_row = world_col.row(align=True)
                        bg_row.enabled = intensity_row.enabled
                        if world.get('solo',False):
                            bg_row.alert = True
                        bg_empty = bg_row.row()
                        bg_empty.ui_units_x = 1
                        bg_empty.separator()
                        # if bg_row.enabled:
                        bg_row.prop(bg.inputs[1],'default_value', text=bg.name+' Strength')
                        # else:
                        #     bg_row.label(text='Strength: '+ str(round(bg.get('strength'),3)))
                        minus = bg_row.operator("lightmixer.emissive_stop", text='', icon='REMOVE')
                        minus.factor = -0.5
                        minus.world = True
                        minus.background_name = bg.name
                        plus = bg_row.operator("lightmixer.emissive_stop", text='', icon='ADD')
                        plus.factor = 0.5
                        plus.world = True
                        plus.background_name = bg.name


            if lightmixer.world_show_more:
                more_col = world_box.column(align=False)
                more_col.enabled = world.enabled
                col = more_col.column(align=True)
                col.use_property_split = False

                if world.get('is_world_hdri',False):
                    prefs = context.preferences.addons[addon_name].preferences
                    if not prefs.hdri_lib_path:
                        col.label(text='Please set your HDRI library path:')
                        col.prop(prefs, 'hdri_lib_path', text = '')
                        col.separator()
                    else:
                        row = col.row(align=True)
                        row.prop(lightmixer, 'hdri_category', text='')
                        row.operator('lightmixer.generate_hdri_thumbs',icon='RENDERLAYERS', text='')
                        row.operator('lightmixer.refresh_hdr_categories', icon='FILE_REFRESH', text='')

                        hdri_tex = scene.world.get('hdri_tex','')

                        if hdri_tex and scene.lightmixer.hdri_tex != hdri_tex:
                            row = col.row(align=True)
                            row.scale_y = hdri_scale_y
                            row.operator('lightmixer.refresh_hdri_preview', icon='FILE_REFRESH')
                        else:
                            col.template_icon_view(lightmixer, "hdri_tex",
                                                   show_labels=True, scale=hdri_scale_y)
                        col.prop(wd_lightmixer, 'hdri_rotation', slider=True, )

                elif world.get('is_sky',False):
                    if world.use_nodes:
                        # nodes = world.node_tree.nodes
                        sky = wd.get_sky_tex(context)
                        if sky:
                            col.prop(sky[0], 'sky_type')
                            col.separator()
                            if sky[0].sky_type == "NISHITA":
                                col.prop(sky[0], 'sun_size')
                                col.prop(sky[0], 'sun_intensity')
                                col.separator()
                                col.prop(sky[0], 'sun_elevation')
                                col.prop(sky[0], 'sun_rotation')
                                col.prop(sky[0], 'altitude')
                                col.separator()
                                col.prop(sky[0], 'air_density')
                                col.prop(sky[0], 'dust_density')
                                col.prop(sky[0], 'ozone_density')
                            elif sky[0].sky_type in {"PREETHAM","HOSEK_WILKIE"}:
                                col.prop(sky[0], 'sun_direction', text='')
                                col.prop(sky[0], 'turbidity')
                                if sky[0].sky_type == "HOSEK_WILKIE":
                                    col.prop(sky[0], 'ground_albedo')
                else:
                    col.separator()
                    col_large = col.column(align=True)
                    col_large.scale_y = 2
                    col_large.operator('lightmixer.hdri_add')
                    col_large.operator('lightmixer.sky_add')

                # White Balance controls
                if world.get('is_world_hdri', False) or world.get('is_sky', False):
                    wb = wd.get_wb_groups(context)
                    if wb:
                        icn = 'EVENT_K' if wd_lightmixer.hdri_use_temperature else 'EVENT_C'
                        col.separator()
                        row = col.row(align=True)
                        if wd_lightmixer.hdri_use_temperature:
                            row.prop(wd_lightmixer, 'hdri_temperature', slider=True)

                            col.prop(wd_lightmixer, 'hdri_tint', slider=True)
                        else:
                            row.prop(wd_lightmixer, 'hdri_color', text='')
                        row.prop(wd_lightmixer, "hdri_use_temperature", icon=icn, icon_only=True, toggle=True)

                        # Blur slider if HDRI
                        blur = wd.get_blur_groups(context)
                        if world.get('is_world_hdri', False) and blur:
                            col.prop(wd_lightmixer, 'hdri_blur', slider=True)
                    else:
                        col.separator()
                        col.operator('lightmixer.world_add_controls', icon='ERROR')

                if context.scene.render.engine == "CYCLES":
                    col.separator()
                    row = col.row(align=True)
                    row.prop(world.cycles_visibility, "diffuse", toggle=True)
                    row.prop(world.cycles_visibility, "glossy", toggle=True)
                    row.prop(world.cycles_visibility, "camera", toggle=True)

                more_col.enabled = intensity_row.enabled

class LIGHTMIXER_PT_WorldViewPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "World Mixer"
    bl_order = 11

    def draw_header_preset(self, context):
        world_mixer_draw_header_preset(self,context)

    def draw(self, context):
        world_mixer_draw(self,context)

class LIGHTMIXER_PT_WorldProperties(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_label = "World Mixer"

    def draw_header_preset(self, context):
        world_mixer_draw_header_preset(self,context)

    def draw(self, context):
        world_mixer_draw(self,context)
