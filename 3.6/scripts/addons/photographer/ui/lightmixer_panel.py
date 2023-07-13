import bpy
from ..functions import traverse_tree, list_lights, list_collections
from ..constants import addon_name
from ..properties.light import energy_check
from ..operators.target import get_target

def light_textures_ui(parent_col, context, settings,light_name):

    engine = context.scene.render.engine
    if engine == 'CYCLES':
        box = parent_col.box()
        top_row = box.row(align=True)
        top_row.prop(settings,'gobo')
        if settings.gobo:
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(settings,'gobo_scale')
            row.prop(settings,'gobo_scale_y')
            row = col.row(align=True)
            row.prop(settings,'gobo_offset_x')
            row.prop(settings,'gobo_offset_y')
            col.prop(settings,'gobo_opacity', slider=True)
            row=col.row(align=True)
            row.prop(settings,'gobo_tex_repeat', text='Repeat')
            if settings.light_type == 'SPOT':
                row.prop(settings,'gobo_link_spot_size')
            col.template_icon_view(settings, "gobo_tex", show_labels=True, scale=5)
        box.enabled = settings.light_type != 'SUN'      
        
        box = parent_col.box()
        top_row = box.row(align=True)
        top_row.prop(settings,'ies')
        top_row.operator('lightmixer.generate_ies_thumbs',icon='RENDERLAYERS', text='')
        if settings.ies:
            col = box.column(align=True)
            col.operator("lightmixer.reset_intensity").light=light_name
            col.separator()
            col.prop(settings,'ies_opacity', slider=True)
            col.template_icon_view(settings, "ies_tex", show_labels=True, scale=5)
        box.enabled = settings.light_type not in {'SUN','AREA'}            

def light_row(context,light_obj,layout):
    scene = context.scene
    solo_active = scene.lightmixer.solo_active
    preferences = context.preferences.addons[addon_name].preferences

    light = light_obj.data
    lightmixer = light_obj.lightmixer
    settings = light.photographer
    scene_lm = scene.lightmixer

    luxcore = False
    if context.scene.render.engine == "LUXCORE" and not light.luxcore.use_cycles_settings:
        luxcore = True

    row = layout.row(align=True)
    row.scale_y = 1.25
    row.scale_x = 0.9
    main_col = row.column(align=True)

    if solo_active and lightmixer.solo:
        icn = 'EVENT_S'
        row.alert=True
    elif not solo_active and lightmixer.enabled:
        icn = 'OUTLINER_OB_LIGHT'
    else:
        icn = 'LIGHT'

    main_col.operator("lightmixer.enable", text="",
                        icon=icn, emboss=False).light=light_obj.name

    col = row.column(align=True)
    row = col.row(align=True)

    select_row = row.row(align=True)
    name_row = row.row(align=True)
    # if not lightmixer.enabled:
    #     # Get Outliner selection of disabled lights
    #     selected = False
    #     areaOverride=bpy.context.area
    #     if bpy.context.area:    
    #         if bpy.context.area.type!='OUTLINER':
    #             for area in bpy.context.screen.areas:
    #                 if area.type == 'OUTLINER':
    #                     areaOverride=area

    #     with bpy.context.temp_override(area=areaOverride):
    #         if light_obj in bpy.context.selected_ids:
    #             selected = True

    #     if bpy.context.object == light_obj or selected:
    #         icn = 'RESTRICT_SELECT_OFF'
    #     else:
    #         icn = 'RESTRICT_SELECT_ON'

    #     select_row.operator("photographer.select", text='', icon=icn).obj_name=light_obj.name
    # else:
    select_row.operator("photographer.select", text='',
                icon="%s" % 'RESTRICT_SELECT_OFF'if light_obj.select_get()
                else 'RESTRICT_SELECT_ON').obj_name=light_obj.name

    name_row.prop(light_obj, "name", text='')
    name_row.ui_units_x = scene_lm.light_name_width
    row_sep = name_row.row(align=True)
    row_sep.ui_units_x = .3
    row_sep.prop(scene_lm,"light_name_width")
    row_sep.separator()

    split = row.split(align=True,factor=0.4)
    # subrow.ui_units_x = 4
    color_row = split.row(align=True)
    color_row.scale_x = 0.9
    if preferences.use_physical_lights:
        if settings.use_light_temperature:
            color_row.prop(settings, "light_temperature", text='')
            # c_row=subrow.row(align=True)
            # c_row.ui_units_x = 1
            # c_row.prop(settings, "preview_color_temp", text='')
        else:
            # color_row.ui_units_x = 1
            color_row.prop(settings, "color", text='')
        # icn = 'EVENT_K' if settings.use_light_temperature else 'EVENT_C'
        # subrow.operator("photographer.switchcolormode",
        #                 icon=icn, text='').light=light.name
    else:
        color_row.prop(light, "color", text='')

    intensity_row = split.row(align=True)


    if light.type == 'SUN':
        if preferences.use_physical_lights:
            if settings.sunlight_unit == 'irradiance':
                intensity_row.prop(settings,"irradiance", text='')
            elif settings.sunlight_unit == 'illuminance':
                intensity_row.prop(settings,"illuminance", text='')
            elif settings.sunlight_unit == 'artistic':
                sub = intensity_row.split(factor=0.5,align=True)
                sub.prop(settings,"intensity", text='Intensity')
                sub.prop(settings,"light_exposure", text='')
        else:
            intensity_row.prop(light,"energy")

    else:
        if preferences.use_physical_lights:
            if settings.light_unit == 'artistic':
                # sub = intensity_row.split(factor=0.5,align=True)
                intensity_row.prop(settings,"intensity", text='')
                # sub.prop(settings,"light_exposure", text='')

            elif settings.light_unit == 'power':
                intensity_row.prop(settings,"power", text='')

            elif settings.light_unit == 'advanced_power':
                # sub = intensity_row.split(factor=0.5,align=True)
                intensity_row.prop(settings,"advanced_power", text='')
                # sub.prop(settings,"efficacy", text='Efficacy')

            elif settings.light_unit == 'lumen':
                intensity_row.prop(settings,"lumen", text='')

            elif settings.light_unit == 'candela':
                intensity_row.prop(settings,"candela", text='')

            # if light.type == 'AREA' and  settings.light_unit in {'lumen', 'candela'}:
            #     sub = intensity_row.row(align=True)
            #     sub.ui_units_x = 2
            #     label = "/m\u00B2"
            #     sub.prop(settings, "per_square_meter", text=label, toggle=True)

        else:
            intensity_row.prop(light,"energy")

    exp_col = intensity_row.column(align=True)
    exp_col.scale_y = 0.52
    plus = exp_col.operator("lightmixer.light_stop", text='', icon='TRIA_UP')
    plus.light = light.name
    plus.factor = 0.5
    minus = exp_col.operator("lightmixer.light_stop", text='', icon='TRIA_DOWN')
    minus.light = light.name
    minus.factor = -0.5

    delete_row = row.row(align=True)
    delete_row.operator("lightmixer.delete", text="",
        icon='PANEL_CLOSE', emboss=False).light=light_obj.name


def light_collection_row(context,coll,layout):
    settings = context.scene.lightmixer
    coll_lights = [obj.name for obj in coll.objects if obj.type=='LIGHT']
    if coll_lights:
        coll_lights= sorted(coll_lights)
        
        coll_box = layout.box()
        coll_row = coll_box.row(align=True)
        exp = coll_row.operator("photographer.collection_expand", text="",
                        icon='TRIA_DOWN' if coll.get('cl_expand', True) else 'TRIA_RIGHT',
                        emboss=False)
        exp.collection=coll.name
        exp.cam_list=True

        if bpy.app.version >= (2, 91, 0):
            color_tag = 'OUTLINER_COLLECTION'if coll.color_tag == 'NONE' else 'COLLECTION_'+ coll.color_tag
        else:
            color_tag = 'GROUP'
        sel = coll_row.operator('photographer.select_collection', text='', icon=color_tag)
        sel.coll_name = coll.name
        sel.coll_type = 'CAMERA'
        coll_row.prop(coll, "name", text='')
        exp_col = coll_row.column(align=True)
        exp_col.scale_y = 0.52
        plus = exp_col.operator("lightmixer.light_stop", text='', icon='TRIA_UP')
        plus.collection = coll.name
        plus.factor = 0.5
        minus = exp_col.operator("lightmixer.light_stop", text='', icon='TRIA_DOWN')
        minus.collection = coll.name
        minus.factor = -0.5


        # Find Layer Collection inside the tree
        lc = [c for c in traverse_tree(context.view_layer.layer_collection) if c.name == coll.name][0]
        coll_row.prop(lc, "exclude", text='', icon_only=True, emboss=False)
        # coll_row.prop(coll, "hide_viewport", text='', icon_only=True, emboss=False)
        coll_row.prop(coll, "hide_render", text='', icon_only=True, emboss=False)
        exclude = lc.exclude

    # Add cameras into Collection box
    if coll.get('cl_expand', True) and not exclude:
        parent_col = coll_box.column(align=True)
        for light in coll_lights:
            # Disable light boxes if Collection is hidden in Viewport
            # if coll.hide_viewport:
            #     parent_col.enabled = False
            if settings.list_filter:
                if settings.use_filter_invert:
                    if settings.list_filter.lower() not in light.lower():
                        light_row(context,bpy.data.objects[light],parent_col)
                elif settings.list_filter.lower() in light.lower():
                    light_row(context,bpy.data.objects[light],parent_col)
            else:
                light_row(context,bpy.data.objects[light],parent_col)

def light_panel(context,parent_ui):
    layout = parent_ui
    scene = context.scene
    settings = scene.lightmixer

    light_list,light_collections,active_light = list_lights(context)

    # Light list UI
    box = layout.box()
    panel_row = box.row(align=False)
    panel_col = panel_row.column()

    if not light_list:
        row = panel_col.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="No Light in the Scene", icon='INFO')

    if scene.lightmixer.light_list_sorting == 'COLLECTION':
        for coll in light_collections:
            coll_lights = [obj.name for obj in coll.objects if obj.type=='LIGHT']
            if coll_lights:
                coll_lights= sorted(coll_lights)

                if coll.name in {'Master Collection', 'Scene Collection'}:
                    # sc = 'Scene collection'
                    # if  scene.lightmixer.list_filter in sc.lower():
                    coll_box = panel_col.box()
                    row = coll_box.row(align=True)
                    row.prop(scene.lightmixer, "scene_collection_expand", text="",
                                    icon='TRIA_DOWN' if scene.lightmixer.get('scene_collection_expand', True)
                                    else 'TRIA_RIGHT', emboss=False)
                    row.label(text='Scene Collection', icon='OUTLINER_COLLECTION')
                    col = coll_box.column(align=True)
                    # exclude = False
                    if scene.lightmixer.scene_collection_expand:
                        for light in coll_lights:
                            if settings.list_filter:
                                if settings.use_filter_invert:
                                    if settings.list_filter.lower() not in light.lower():
                                        light_row(context,bpy.data.objects[light],col) 
                                elif settings.list_filter.lower() in light.lower():
                                    light_row(context,bpy.data.objects[light],col)    
                            else:
                                light_row(context,bpy.data.objects[light],col)

        light_list,light_collections,active_light = list_lights(bpy.context)
        filtered_items = [c for c in light_collections]
        rows_count = len(filtered_items)
        panel_col.template_list("PHOTOGRAPHER_UL_ViewPanel_LightCollectionsList", "Light List", bpy.data,
                "collections", scene.lightmixer, "active_light_collection_index", maxrows=rows_count)
    else:
        filtered_items = [o for o in bpy.context.view_layer.objects if o.type=='LIGHT']
        rows_count = len(filtered_items)
        panel_col.template_list("PHOTOGRAPHER_UL_ViewPanel_LightList", "Light List", bpy.data,
                "objects", scene.lightmixer, "active_light_index",maxrows=rows_count)

class PHOTOGRAPHER_UL_ViewPanel_LightList(bpy.types.UIList):
    """Light List for Lightmixer panel"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index):
        col = layout.column(align=True)
        light_row(context,item,col)

    def draw_filter(self, context, layout):
        settings = context.scene.lightmixer
        layout.separator()
        col_main = layout.column(align=True)

        row = col_main.row(align=True)
        row.prop(settings, 'list_filter', text='', icon='VIEWZOOM')
        if settings.list_filter:
            clear = row.operator("photographer.button_string_clear", text='',
                    icon='PANEL_CLOSE',emboss=False)
            clear.prop='list_filter'
            clear.type = 'light'
        row.prop(settings, 'use_filter_invert', text='', icon='ARROW_LEFTRIGHT')
        row.separator()
        row.prop(settings, 'list_filter_reverse', text='', icon='SORT_DESC'
                if settings.list_filter_reverse else "SORT_ASC")
        row.separator()
        row.prop(settings,'light_list_sorting', icon_only=True, expand=True)

    def filter_items(self,context,data,propname):
        settings = context.scene.lightmixer
        filtered = []
        ordered = []
        items = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        filtered = [self.bitflag_filter_item] * len(items)
        self.use_filter_sort_reverse = settings.list_filter_reverse

        ordered = helper_funcs.sort_items_by_name(items, "name")

        filtered_items = self.get_props_filtered_items()

        for i, item in enumerate(items):
            if not item in filtered_items:
                filtered[i] &= ~self.bitflag_filter_item

        return filtered,ordered

    def get_props_filtered_items(self):
        settings = bpy.context.scene.lightmixer

        filtered_items = [o for o in bpy.context.scene.objects if o.type=='LIGHT']
        if settings.list_filter:
            if settings.use_filter_invert:
                filtered_items = [o for o in filtered_items if o.name.lower().find(settings.list_filter.lower()) == -1]
            else:
                filtered_items = [o for o in filtered_items if not o.name.lower().find(settings.list_filter.lower()) == -1]

        return filtered_items

class PHOTOGRAPHER_UL_ViewPanel_LightCollectionsList(bpy.types.UIList):
    """Light List for Lightmixer panel"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_property, index):
        col = layout.column(align=True)
        light_collection_row(context,item,col)


    def draw_filter(self, context, layout):
        settings = context.scene.lightmixer
        layout.separator()
        col_main = layout.column(align=True)

        row = col_main.row(align=True)
        row.prop(settings, 'list_filter', text='', icon='VIEWZOOM')
        if settings.list_filter:
            clear = row.operator("photographer.button_string_clear", text='',icon='PANEL_CLOSE',
                    emboss=False)
            clear.prop='list_filter'
            clear.type = 'light'
        row.prop(settings, 'use_filter_invert', text='', icon='ARROW_LEFTRIGHT')
        row.separator()
        row.prop(settings, 'list_filter_reverse', text='', icon='SORT_DESC'
                if settings.list_filter_reverse else "SORT_ASC")
        row.separator()
        row.prop(settings,'light_list_sorting', icon_only=True, expand=True)

    def filter_items(self,context,data,propname):
        settings = context.scene.lightmixer
        filtered = []
        ordered = []
        items = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        filtered = [self.bitflag_filter_item] * len(items)
        self.use_filter_sort_reverse = settings.list_filter_reverse

        ordered = helper_funcs.sort_items_by_name(items, "name")

        filtered_items = self.get_props_filtered_items()

        for i, item in enumerate(items):
            if not item in filtered_items:
                filtered[i] &= ~self.bitflag_filter_item

        return filtered,ordered

    def get_props_filtered_items(self):
        settings = bpy.context.scene.lightmixer

        light_list,light_collections,active_light = list_lights(bpy.context)
        filtered_items = [c for c in light_collections]
        # if settings.list_filter:
        #     filtered_items = [o for o in filtered_items if not o.name.lower().find(settings.list_filter.lower()) == -1]
        return filtered_items

class LIGHTMIXER_PT_ViewPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Light Mixer"
    bl_order = 12


    def draw_header_preset(self, context):
        if context.preferences.addons[addon_name].preferences.show_compact_ui:
            layout = self.layout
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.scale_x = 1.25
            row.operator("lightmixer.add", text="", icon='LIGHT_POINT').type='POINT'
            row.operator("lightmixer.add", text="", icon='LIGHT_SPOT').type='SPOT'
            row.operator("lightmixer.add", text="", icon='LIGHT_AREA').type='AREA'
            row.operator("lightmixer.add", text="", icon='LIGHT_SUN').type='SUN'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        col=layout.column(align=True)
        if not context.preferences.addons[addon_name].preferences.show_compact_ui:
            row = col.row(align=True)
            row.scale_y = 1.2
            row.operator("lightmixer.add", text='Add Point', icon="LIGHT_POINT").type='POINT'
            row.operator("lightmixer.add", text='Add Spot', icon="LIGHT_SPOT").type='SPOT'
            row = col.row(align=True)
            row.scale_y = 1.2
            row.operator("lightmixer.add", text='Add Area', icon="LIGHT_AREA").type='AREA'
            row.operator("lightmixer.add", text='Add Sun', icon="LIGHT_SUN").type='SUN'

        else:
            light_panel(context,col)

class LIGHTMIXER_PT_PropertiesSubPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Light Properties"
    bl_parent_id = "LIGHTMIXER_PT_ViewPanel"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        solo_active = context.scene.lightmixer.solo_active
        preferences = context.preferences.addons[addon_name].preferences
        luxcore = False
        if context.scene.render.engine == "LUXCORE" and not light.luxcore.use_cycles_settings:
            luxcore = True

        light_obj = None
        if context.object:
            if context.object and context.object.type =='LIGHT':
                light_obj = bpy.context.object
            elif context.object.get('is_target',False):
                for obj in bpy.context.scene.objects:
                    if obj.type =='LIGHT' and obj.constraints.get("Aim Target") is not None:
                        if obj.constraints["Aim Target"].target == context.object:
                            light_obj = obj
                            break         

        if light_obj:
            light = light_obj.data
            lightmixer = light_obj.lightmixer
            settings = light.photographer

            main_col = layout.column(align=False)
            if preferences.use_physical_lights:
                color_row = main_col.row(align=True)
                if settings.use_light_temperature:
                    color_row.prop(settings, "light_temperature", slider=True)
                    row2 = color_row.row(align=True)
                    row2.ui_units_x = 2
                    row2.prop(settings, "preview_color_temp", text='')
                    color_row.operator("photographer.switchcolormode",
                                icon="EVENT_K", text='').light=light.name
                else:
                    color_row.prop(settings, "color", text='')
                    color_row.operator("photographer.switchcolormode",
                                icon="EVENT_C", text='').light=light.name

                intensity_row = main_col.row(align=True)
                if light.type == 'SUN':
                    if settings.sunlight_unit == 'irradiance':
                        intensity_row.prop(settings,"irradiance", text='Irradiance')
                    elif settings.sunlight_unit == 'illuminance':
                        intensity_row.prop(settings,"illuminance", text='Lux')
                    elif settings.sunlight_unit == 'artistic':
                        sub = intensity_row.split(factor=0.5,align=True)
                        sub.prop(settings,"intensity", text='Intensity')
                        sub.prop(settings,"light_exposure", text='')
                else:
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
                color_row = main_col.row(align=True)
                color_row.prop(light, "color", text='')
                intensity_row = main_col.row(align=True)
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
                if light.type == 'SUN':
                    row.prop(settings, "sunlight_unit", icon_only=True)
                else:
                    row.prop(settings, "light_unit", icon_only=True)
            else:
                row.separator()

            shape_row = main_col.row(align=True)
            # Keep Photographer Light Type to rename automatically
            shape_row.prop(settings, "light_type", text='', icon='LIGHT_%s' % light.type, icon_only=True)
            if light.type == 'SUN':
                if luxcore:
                    shape_row.prop(light.luxcore, "relsize")
                else:
                    shape_row.prop(light, "angle", text='Disk Angle')
            elif light.type == 'POINT':
                shape_row.prop(light, "shadow_soft_size", text='Source Radius')
            elif light.type == 'SPOT':
                shape_row.prop(light, "shadow_soft_size", text='Size')
                sub =  main_col.row(align=True)
                if preferences.use_physical_lights:
                    sub.prop(settings, "spot_size", text='Cone')
                else:
                    sub.prop(light, "spot_size", text='Cone')
                sub.prop(light, "spot_blend", text='Blend')
            elif light.type == 'AREA':
                if energy_check(settings):
                    check_col = main_col.column(align=False)
                    check_col.label(text="Light Size changed", icon='INFO')
                    check_col.operator("photographer.applyphotographersettings",
                                        text="Recalculate Intensity")
                if context.scene.render.engine == "CYCLES" and bpy.app.version >= (2,93,0):
                    sub =  main_col.row(align=True)
                    sub.prop(light, "spread", text='Spread')

                if preferences.use_physical_lights:
                    # Use Photographer settings
                    data = settings
                else:
                    #Use Blender settings
                    data = light
                shape_row.prop(data, "shape", text='')
                if settings.shape in {'SQUARE','DISK'}:
                    shape_row.prop(data, "size", text='')
                else:
                    shape_row.prop(data, "size", text='')
                    shape_row.prop(data, "size_y", text='')

            # Target
            row = shape_row.row(align=True)
            if settings.target_enabled:
                target_obj = get_target(light_obj.name)
                if target_obj:
                    row.operator("photographer.select", text="",
                    icon="%s" % 'RESTRICT_SELECT_OFF'if target_obj.select_get()
                            else 'RESTRICT_SELECT_ON').obj_name=target_obj.name
                row.operator("photographer.target_delete", text="", icon='CANCEL').obj_name=light_obj.name
            else:
                row.operator("object.light_target_add", text="", icon='TRACKER')

            row.operator("object.light_modal",text="", icon='ORIENTATION_GIMBAL')
            # modal.light = light_obj.name
            # if settings.target_enabled and target_obj:
            #     modal.target = target_obj.name
            # else:
            #     modal.target = ''

            if light.type == 'SUN':
                row = main_col.row(align=True)
                if settings.target_enabled:
                    row.enabled = False
                row.prop(settings, "use_elevation", text='')
                sub = row.row(align=True)
                sub.enabled = settings.use_elevation
                sub.prop(settings, "azimuth", slider=True)
                sub.prop(settings, "elevation", slider=True)

                if context.scene.render.engine == "LUXCORE":
                    row = main_col.row(align=True)
                    row.prop(light.luxcore, "sun_type", expand=True)
                    col = main_col.column(align=True)

            light_textures_ui(main_col, context, settings, light.name)

            if context.scene.render.engine == "BLENDER_EEVEE":
                col = main_col.column(align=True)
                row = col.row(align=True)
                row.prop(light, "diffuse_factor", slider=True, text='Diffuse')
                row.prop(light, "specular_factor", slider=True, text='Specular')
                row.prop(light, "volume_factor", slider=True, text='Volume')
            elif context.scene.render.engine == "CYCLES":
                col = main_col.column(align=True)
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
                col = main_col.column(align=True)
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
                row = col.row(align=True)
                row.prop(settings, "light_falloff", text='')
                row.prop(settings,"light_falloff_smooth")
                row.enabled = light.type != 'SUN'
        else:
            box = layout.box()
            row = box.row()
            row.alignment = 'CENTER'
            row.label(text="No Light selected and active")
            col = box.column()
            col.separator()