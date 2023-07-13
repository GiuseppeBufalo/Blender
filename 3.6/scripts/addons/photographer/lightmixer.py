import bpy
from .functions import traverse_tree,list_collections
from .properties.light import energy_check
from .operators.target import get_target
from .constants import addon_name


def light_panel(context,parent_box,light_name):
    scene = context.scene
    solo_active = scene.lightmixer.solo_active
    preferences = context.preferences.addons[addon_name].preferences

    light_obj = bpy.data.objects.get(light_name)
    light = light_obj.data
    lightmixer = light_obj.lightmixer
    settings = light.photographer

    luxcore = False
    if scene.render.engine == "LUXCORE" and not light.luxcore.use_cycles_settings:
        luxcore = True

    box = parent_box.box()
    row = box.row(align=True)
    main_col = row.column(align=True)

    if solo_active and lightmixer.solo:
        icn = 'EVENT_S'
        row.alert=True
    elif not solo_active and lightmixer.enabled:
        icn = 'OUTLINER_OB_LIGHT'
    else:
        icn = 'LIGHT'

    main_col.operator("lightmixer.enable", text="",
                        icon=icn, emboss=False).light=light_name

    col = row.column(align=True)
    row = col.row(align=True)

    select_row = row.row(align=True)
    name_row = row.row(align=True)
    if not lightmixer.enabled:
        # Get Outliner selection of disabled lights
        selected = False
        areaOverride=bpy.context.area    
        if bpy.context.area.type!='OUTLINER':
            for area in bpy.context.screen.areas:
                if area.type == 'OUTLINER':
                    areaOverride=area

        with bpy.context.temp_override(area=areaOverride):
            if light_obj in bpy.context.selected_ids:
                selected = True

        if bpy.context.object == light_obj or selected:
            icn = 'RESTRICT_SELECT_OFF'
        else:
            icn = 'RESTRICT_SELECT_ON'

        select_row.operator("photographer.select", text='', icon=icn).obj_name=light_name
    else:
        select_row.operator("photographer.select", text='',
                    icon="%s" % 'RESTRICT_SELECT_OFF'if light_obj.select_get()
                    else 'RESTRICT_SELECT_ON').obj_name=light_name
    name_row.prop(bpy.data.objects[light_name], "name", text='')
    subrow = name_row.row(align=True)
    if preferences.use_physical_lights:
        if settings.use_light_temperature:
            subrow.prop(settings, "light_temperature", text='')
            c_row=subrow.row(align=True)
            c_row.ui_units_x = 1
            c_row.prop(settings, "preview_color_temp", text='')
        else:
            subrow.ui_units_x = 6
            subrow.prop(settings, "color", text='')
        icn = 'EVENT_K' if settings.use_light_temperature else 'EVENT_C'
        subrow.operator("photographer.switchcolormode",
                        icon=icn, text='').light=light.name
    else:
        subrow.ui_units_x = 3
        subrow.prop(light, "color", text='')
    row.operator("lightmixer.delete", text="",
                    icon='PANEL_CLOSE', emboss=False).light=light_name

    intensity_row = col.row(align=True)
    sub = intensity_row.row(align=True)

    if light.type == 'SUN':
        if preferences.use_physical_lights:
            if settings.sunlight_unit == 'irradiance':
                intensity_row.prop(settings,"irradiance", text='Irradiance')
            elif settings.sunlight_unit == 'illuminance':
                intensity_row.prop(settings,"illuminance", text='Lux')
            elif settings.sunlight_unit == 'artistic':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(settings,"intensity", text='Intensity')
                sub.prop(settings,"light_exposure", text='')
        else:
            intensity_row.prop(light,"energy")
        intensity_row.ui_units_x = 2
        minus = intensity_row.operator("lightmixer.light_stop", text='', icon='REMOVE')
        minus.light = light.name
        minus.factor = -0.5
        plus = intensity_row.operator("lightmixer.light_stop", text='', icon='ADD')
        plus.light = light.name
        plus.factor = 0.5

        row = intensity_row.row(align=True)
        row.ui_units_x = 1
        if preferences.use_physical_lights:
            row.prop(settings,"sunlight_unit", icon_only=True)
        else:
            row.separator()
    else:
        if preferences.use_physical_lights:
            if settings.light_unit == 'artistic':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(settings,"intensity", text='Intensity')
                sub.prop(settings,"light_exposure", text='')

            elif settings.light_unit == 'power':
                intensity_row.prop(settings,"power", text='Power')

            elif settings.light_unit == 'advanced_power':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(settings,"advanced_power", text='Watts')
                sub.prop(settings,"efficacy", text='Efficacy')

            elif settings.light_unit == 'lumen':
                intensity_row.prop(settings,"lumen", text='Lumen')

            elif settings.light_unit == 'candela':
                intensity_row.prop(settings,"candela", text='Candela')

            if light.type == 'AREA' and  settings.light_unit in {'lumen', 'candela'}:
                sub = intensity_row.row(align=True)
                sub.ui_units_x = 2
                label = "/m\u00B2"
                sub.prop(settings, "per_square_meter", text=label, toggle=True)

        else:
            intensity_row.prop(light,"energy")

        # sub = row.row(align=True)
        intensity_row.ui_units_x = 2
        minus = intensity_row.operator("lightmixer.light_stop", text='', icon='REMOVE')
        minus.light = light.name
        minus.factor = -0.5
        plus = intensity_row.operator("lightmixer.light_stop", text='', icon='ADD')
        plus.light = light.name
        plus.factor = 0.5

        row = intensity_row.row(align=True)
        row.ui_units_x = 1
        if preferences.use_physical_lights:
            row.prop(settings, "light_unit", icon_only=True)
        else:
            row.separator()

    main_col.operator("lightmixer.show_more", text="",
                    icon='TRIA_DOWN' if lightmixer.show_more else 'TRIA_RIGHT',
                    emboss=False).light=light_name

    if lightmixer.show_more:
        more_col = box.column(align=False)
        row = more_col.row(align=True)
        # Keep Photographer Light Type to rename automatically
        row.prop(settings, "light_type", text='', icon='LIGHT_%s' % light.type, icon_only=True)
        if light.type == 'SUN':
            if luxcore:
                row.prop(light.luxcore, "relsize")
            else:
                row.prop(light, "angle", text='Disk Angle')
        elif light.type == 'POINT':
            row.prop(light, "shadow_soft_size", text='Source Radius')
        elif light.type == 'SPOT':
            row.prop(light, "shadow_soft_size", text='Size')
            sub =  more_col.row(align=True)
            if preferences.use_physical_lights:
                sub.prop(settings, "spot_size", text='Cone')
            else:
                sub.prop(light, "spot_size", text='Cone')
            sub.prop(light, "spot_blend", text='Blend')
        elif light.type == 'AREA':
            if energy_check(settings):
                check_col = more_col.column(align=False)
                check_col.label(text="Light Size changed", icon='INFO')
                check_col.operator("photographer.applyphotographersettings",
                                    text="Recalculate Intensity")

            if preferences.use_physical_lights:
                # Use Photographer settings
                data = settings
            else:
                #Use Blender settings
                data = light
            row.prop(data, "shape", text='')
            if settings.shape in {'SQUARE','DISK'}:
                row.prop(data, "size", text='')
            else:
                row.prop(data, "size", text='')
                row.prop(data, "size_y", text='')
            if scene.render.engine == "CYCLES" and bpy.app.version >= (2,93,0):
                sub =  more_col.row(align=True)
                sub.prop(light, "spread", text='Spread')

        # Target
        # if light.type in {'SUN','SPOT','AREA'}:
        if settings.target_enabled:
            target = get_target(light_name)
            if target:
                row.operator("photographer.select", text="",
                icon="%s" % 'RESTRICT_SELECT_OFF'if target.select_get()
                        else 'RESTRICT_SELECT_ON').obj_name=target.name
            row.operator("photographer.target_delete", text="", icon='CANCEL').obj_name=light_name
        else:
            row.operator("photographer.target_add", text="", icon='TRACKER').obj_name=light_name

        if light.type == 'SUN':
            row = more_col.row(align=True)
            if settings.target_enabled:
                row.enabled = False
            row.prop(settings, "use_elevation", text='')
            sub = row.row(align=True)
            sub.enabled = settings.use_elevation
            sub.prop(settings, "azimuth", slider=True)
            sub.prop(settings, "elevation", slider=True)

            if context.scene.render.engine == "LUXCORE":
                row = more_col.row(align=True)
                row.prop(light.luxcore, "sun_type", expand=True)
                col = more_col.column(align=True)

        if context.scene.render.engine == "BLENDER_EEVEE":
            col = more_col.column(align=True)
            row = col.row(align=True)
            row.prop(light, "diffuse_factor", slider=True, text='Diffuse')
            row.prop(light, "specular_factor", slider=True, text='Specular')
            row.prop(light, "volume_factor", slider=True, text='Volume')
        elif context.scene.render.engine == "CYCLES":
            col = more_col.column(align=True)
            row = col.row(align=True)
            if bpy.app.version >= (3,0,0):
                row.prop(light_obj, "visible_camera", toggle=True, text='Camera')
                row.prop(light_obj, "visible_diffuse", toggle=True, text='Diffuse')
                row.prop(light_obj, "visible_glossy", toggle=True, text='Glossy')
            else:
                # row.prop(light_obj.cycles_visibility, "camera", toggle=True)
                row.prop(light_obj.cycles_visibility, "diffuse", toggle=True)
                row.prop(light_obj.cycles_visibility, "glossy", toggle=True)
        elif context.scene.render.engine == "LUXCORE":
            col = more_col.column(align=True)
            row = col.row(align=True)
            row.prop(light_obj.luxcore, "visible_to_camera", text="Camera", toggle=True)
            if light.type == 'SUN' and not light.luxcore.use_cycles_settings:
                row.prop(light.luxcore, "visibility_indirect_diffuse", toggle=True)
                row = col.row(align=True)
                row.prop(light.luxcore, "visibility_indirect_glossy", toggle=True)
                row.prop(light.luxcore, "visibility_indirect_specular", toggle=True)

        if context.scene.render.engine == "BLENDER_EEVEE":
            row = col.row(align=True)
            row.prop(light, "use_shadow", text='Shadows', toggle=True)
            row.prop(light, "use_contact_shadow", text='Contact Shadows', toggle=True)
        elif context.scene.render.engine == "CYCLES":
            row = col.row(align=True)
            row.prop(light.cycles, "cast_shadow", text='Shadows', toggle=True)
            if bpy.app.version >= (3,2,0):
             row.prop(light.cycles, "is_caustics_light", text='Caustics', toggle=True)

    if solo_active or not light_obj.lightmixer.enabled:
        if not light_obj.lightmixer.solo:
            name_row.enabled = False
            intensity_row.enabled = False
            if lightmixer.show_more:
                more_col.enabled = False

def light_panel_luxcore(context,parent_box,light_name):
    scene = context.scene
    solo_active = context.scene.lightmixer.solo_active
    preferences = context.preferences.addons[addon_name].preferences

    light_obj = bpy.data.objects.get(light_name)
    lightmixer = light_obj.lightmixer
    light = light_obj.data
    settings = light.photographer

    luxcore_settings = not light.luxcore.use_cycles_settings
    cycles_settings = light.luxcore.use_cycles_settings
    photographer_settings = False
    if cycles_settings and settings.enable_lc_physical and preferences.use_physical_lights:
        photographer_settings = True

    box = parent_box.box()
    row = box.row(align=True)
    main_col = row.column(align=True)

    if solo_active and light_obj.lightmixer.solo:
        icn = 'EVENT_S'
        row.alert=True
    elif not solo_active and light_obj.lightmixer.enabled:
        icn = 'OUTLINER_OB_LIGHT'
    else:
        icn = 'LIGHT'

    main_col.operator("lightmixer.enable", text="",
                        icon=icn, emboss=False).light=light_name
    col = row.column(align=True)
    row = col.row(align=True)
    name_row = row.row(align=True)
    name_row.operator("photographer.select", text='',
                    icon="%s" % 'RESTRICT_SELECT_OFF'if light_obj.select_get()
                    else 'RESTRICT_SELECT_ON').obj_name=light_name
    name_row.prop(bpy.data.objects[light_name], "name", text='')
    subrow = name_row.row(align=True)
    if photographer_settings:
        if settings.use_light_temperature:
            subrow.prop(settings, "light_temperature", text='')
            c_row=subrow.row(align=True)
            c_row.ui_units_x = 1
            c_row.prop(settings, "preview_color_temp", text='')
            subrow.operator("photographer.switchcolormode",
                            icon="EVENT_K", text='').light=light.name
        else:
            subrow.ui_units_x = 6
            subrow.prop(settings, "color", text='')
            subrow.operator("photographer.switchcolormode",
                            icon="EVENT_C", text='').light=light.name
    elif cycles_settings:
        subrow.ui_units_x = 3
        subrow.prop(light, "color", text='')
    elif luxcore_settings:
        if not (light.type == 'SUN' and light.luxcore.light_type == 'sun'):
            if light.luxcore.color_mode == 'temperature':
                subrow.prop(light.luxcore, "temperature", text='')
                c_row=subrow.row(align=True)
                c_row.ui_units_x = 1
                c_row.prop(settings, "preview_color_temp", text='')
            else:
                subrow.ui_units_x = 6
                subrow.prop(light.luxcore, "rgb_gain", text='')
            icn = 'EVENT_K' if light.luxcore.color_mode == 'temperature' else 'EVENT_C'
            subrow.operator("photographer.switchcolormode",
                            icon=icn, text='').light=light.name

    row.operator("lightmixer.delete", text="",
                    icon='PANEL_CLOSE', emboss=False).light=light_name

    intensity_row = col.row(align=True)
    sub = intensity_row.row(align=True)

    if light.type == 'SUN':
        if photographer_settings:
            if settings.sunlight_unit == 'irradiance':
                intensity_row.prop(settings,"irradiance", text='Irradiance')
            elif settings.sunlight_unit == 'illuminance':
                intensity_row.prop(settings,"illuminance", text='Lux')
            elif settings.sunlight_unit == 'artistic':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(settings,"intensity", text='Intensity')
                sub.prop(settings,"light_exposure", text='')
        elif cycles_settings:
            intensity_row.prop(light,"energy")
        else: # luxcore_settings
            if light.luxcore.light_type =='sun':
                intensity_row.prop(light.luxcore,"sun_sky_gain", text='Gain')
            else:
                intensity_row.prop(light.luxcore,"gain", text='Gain')
            intensity_row.prop(light.luxcore,"exposure", text='')

        intensity_row.ui_units_x = 2
        minus = intensity_row.operator("lightmixer.light_stop", text='', icon='REMOVE')
        minus.light = light.name
        minus.factor = -0.5
        plus = intensity_row.operator("lightmixer.light_stop", text='', icon='ADD')
        plus.light = light.name
        plus.factor = 0.5

        row = intensity_row.row(align=True)
        row.ui_units_x = 1
        if photographer_settings:
            row.prop(settings,"sunlight_unit", icon_only=True)
        else:
            row.separator()
    else:
        if photographer_settings:
            if settings.light_unit == 'artistic':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(settings,"intensity", text='Intensity')
                sub.prop(settings,"light_exposure", text='')

            elif settings.light_unit == 'power':
                intensity_row.prop(settings,"power", text='Power')

            elif settings.light_unit == 'advanced_power':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(settings,"advanced_power", text='Watts')
                sub.prop(settings,"efficacy", text='Efficacy')

            elif settings.light_unit == 'lumen':
                intensity_row.prop(settings,"lumen", text='Lumen')

            elif settings.light_unit == 'candela':
                intensity_row.prop(settings,"candela", text='Candela')

            if light.type == 'AREA' and  settings.light_unit in {'lumen', 'candela'}:
                sub = intensity_row.row(align=True)
                sub.ui_units_x = 2
                label = "/m\u00B2"
                sub.prop(settings, "per_square_meter", text=label, toggle=True)

        elif cycles_settings:
            intensity_row.prop(light,"energy")
        else: #luxcore settings
            if light.luxcore.light_unit == 'artistic':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(light.luxcore,"gain", text='Intensity')
                sub.prop(light.luxcore,"exposure", text='')

            elif light.luxcore.light_unit == 'power':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(light.luxcore,"power", text='Watts')
                sub.prop(light.luxcore,"efficacy", text='Efficacy')

            elif light.luxcore.light_unit == 'lumen':
                intensity_row.prop(light.luxcore,"lumen", text='Lumen')

            elif light.luxcore.light_unit == 'candela':
                intensity_row.prop(light.luxcore,"candela", text='Candela')

            if light.type == 'AREA' and  light.luxcore.light_unit == 'candela':
                sub = intensity_row.row(align=True)
                sub.ui_units_x = 2
                label = "/m\u00B2"
                sub.prop(light.luxcore, "per_square_meter", text=label, toggle=True)

        # sub = row.row(align=True)
        intensity_row.ui_units_x = 2
        minus = intensity_row.operator("lightmixer.light_stop", text='', icon='REMOVE')
        minus.light = light.name
        minus.factor = -0.5
        plus = intensity_row.operator("lightmixer.light_stop", text='', icon='ADD')
        plus.light = light.name
        plus.factor = 0.5

        row = intensity_row.row(align=True)
        row.ui_units_x = 1
        if photographer_settings:
            row.prop(settings, "light_unit", icon_only=True)
        elif cycles_settings:
            row.separator()
        else: #luxcoresettings
            row.prop(light.luxcore, "light_unit", icon_only=True)

    main_col.operator("lightmixer.show_more", text="",
                    icon='TRIA_DOWN' if lightmixer.show_more else 'TRIA_RIGHT',
                    emboss=False).light=light_name

    if lightmixer.show_more:
        more_col = box.column(align=False)
        row = more_col.row(align=True)
        # Keep Photographer Light Type to rename automatically
        row.prop(settings, "light_type", text='', icon='LIGHT_%s' % light.type, icon_only=True)
        if light.type == 'SUN':

            sub = more_col.row(align=True)
            if luxcore_settings:
                row.prop(light.luxcore, "light_type", expand=True)
                if light.luxcore.light_type =='sun':
                    sub.prop(light.luxcore, "relsize")
                elif light.luxcore.light_type =='distant':
                    sub.prop(light.luxcore, "theta")
                else:
                    sub.template_ID(light.luxcore, "image", open="image.open")
            else:
                row.prop(light, "angle", text='Disk Angle')

        elif light.type == 'POINT':
            row.prop(light, "shadow_soft_size", text='Source Radius')
        elif light.type == 'SPOT':
            row.prop(light, "shadow_soft_size", text='Size')
            sub = more_col.row(align=True)
            if photographer_settings:
                sub.prop(settings, "spot_size", text='Cone')
            else:
                sub.prop(light, "spot_size", text='Cone')
            sub.prop(light, "spot_blend", text='Blend')
        elif light.type == 'AREA':
            if preferences.use_physical_lights:
                # Use Photographer settings
                data = settings
            else:
                #Use Blender settings
                data = light
            row.prop(data, "shape", text='')
            if settings.shape in {'SQUARE','DISK'}:
                row.prop(data, "size", text='')
            else:
                row.prop(data, "size", text='')
                row.prop(data, "size_y", text='')
            # if cycles_settings:
            #     row = more_col.row(align=True)
            #     row.prop(data, "spread", text='Spread')
            if luxcore_settings:
                row = more_col.row(align=True)
                row.prop(light.luxcore, "spread_angle")

        # Target
        if light.type in {'SUN','SPOT','AREA'}:
            if settings.target_enabled:
                row.operator("photographer.target_delete", text="", icon='CANCEL').obj_name=light_name
            else:
                row.operator("photographer.target_add", text="", icon='TRACKER').obj_name=light_name

        # Azimuth / Elevation
        if light.type == 'SUN':
            row = more_col.row(align=True)
            if settings.target_enabled:
                row.enabled = False
            row.prop(settings, "use_elevation", text='')
            sub = row.row(align=True)
            sub.enabled = settings.use_elevation
            sub.prop(settings, "azimuth", slider=True)
            sub.prop(settings, "elevation", slider=True)

        if preferences.use_physical_lights:
            col = more_col.column(align=True)
            col.prop(settings, "enable_lc_physical", toggle=True)

        if luxcore_settings:
            col = more_col.column(align=True)
            row = col.row(align=True)
            row.prop(light_obj.luxcore, "visible_to_camera", text="Camera", toggle=True)

        # LuxCore ray visibility settings
        if light.type == 'SUN' and not light.luxcore.use_cycles_settings:
            row.prop(light.luxcore, "visibility_indirect_diffuse", toggle=True)
            row = col.row(align=True)
            row.prop(light.luxcore, "visibility_indirect_glossy", toggle=True)
            row.prop(light.luxcore, "visibility_indirect_specular", toggle=True)

    if solo_active or not light_obj.lightmixer.enabled:
        if not light_obj.lightmixer.solo:
            name_row.enabled = False
            intensity_row.enabled = False
            if lightmixer.show_more:
                more_col.enabled = False


class LIGHTMIXER_PT_ViewPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Light Mixer"
    bl_order = 12

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        lightmixer = context.scene.lightmixer

        row = layout.row()
        row.alignment='LEFT'
        row.prop(lightmixer,"show_active_light", icon='TRIA_DOWN' if lightmixer.show_active_light else 'TRIA_RIGHT',
                    emboss=False)
        if lightmixer.show_active_light:
            col=layout.column(align=True)
            if bpy.context.object:
                if bpy.context.object.type=='LIGHT':
                    active_light = bpy.context.object
                    if context.scene.render.engine == 'LUXCORE':
                        light_panel_luxcore(context,col,active_light.name)
                    else:
                        light_panel(context,col,active_light.name)
                else:
                    box = layout.box()
                    row = box.row()
                    row.alignment = 'CENTER'
                    row.label(text="No Light selected and active")
                    col = box.column()
                    col.separator()

                # col = box.column()

        col=layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("lightmixer.add", text='Add Point', icon="LIGHT_POINT").type='POINT'
        row.operator("lightmixer.add", text='Add Sun', icon="LIGHT_SUN").type='SUN'
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("lightmixer.add", text='Add Spot', icon="LIGHT_SPOT").type='SPOT'
        row.operator("lightmixer.add", text='Add Area', icon="LIGHT_AREA").type='AREA'

        lights=[obj.name for obj in context.scene.collection.all_objects if obj.type=='LIGHT']
        if not lights:
            row = layout.row(align=True)
            row.alignment = 'CENTER'
            row.label(text="No Light in the Scene", icon='INFO')

        collections = list_collections(context)

        for coll in collections:
            coll_lights = [obj.name for obj in coll.objects if obj.type=='LIGHT']
            if coll_lights:
                # If not in a Collection, add light to the base layout
                if coll.name in {'Master Collection', 'Scene Collection'}:
                    parent_box = layout
                    exclude = False
                else:
                    parent_box = layout.box()
                    coll_row = parent_box.row(align=True)
                    exp = coll_row.operator("photographer.collection_expand", text="",
                                    icon='TRIA_DOWN' if coll.get('expand', True) else 'TRIA_RIGHT',
                                    emboss=False)
                    exp.collection=coll.name

                    if bpy.app.version >= (2, 91, 0):
                        color_tag = 'OUTLINER_COLLECTION'if coll.color_tag == 'NONE' else 'COLLECTION_'+ coll.color_tag
                    else:
                        color_tag = 'GROUP'
                    sel = coll_row.operator('photographer.select_collection', text='', icon=color_tag)
                    sel.coll_name = coll.name
                    sel.coll_type = 'LIGHT'

                    coll_row.prop(coll, "name", text='')

                    minus = coll_row.operator("lightmixer.light_stop", text='', icon='REMOVE')
                    minus.collection = coll.name
                    minus.factor = -0.5
                    plus = coll_row.operator("lightmixer.light_stop", text='', icon='ADD')
                    plus.collection = coll.name
                    plus.factor = 0.5

                    # Find Layer Collection inside the tree
                    lc = [c for c in traverse_tree(context.view_layer.layer_collection) if c.name == coll.name][0]
                    coll_row.prop(lc, "exclude", text='', icon_only=True, emboss=False)
                    coll_row.prop(coll, "hide_viewport", text='', icon_only=True, emboss=False)
                    coll_row.prop(coll, "hide_render", text='', icon_only=True, emboss=False)
                    exclude = lc.exclude

                # Sorting alphabetically
                coll_lights= sorted(coll_lights)

                # Add lights into Collection box
                if coll.get('expand', True) and not exclude:
                    for light in coll_lights:
                        # Disable light boxes if Collection is hidden in Viewport
                        col = parent_box.column()
                        if coll.hide_viewport:
                            col.enabled = False

                        if context.scene.render.engine == 'LUXCORE':
                            light_panel_luxcore(context,col,light)
                        else:
                            light_panel(context,col,light)
