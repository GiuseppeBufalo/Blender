import bpy
from .light import energy_check, update_energy
from . import light_presets

class PHOTOGRAPHER_OT_CalculateLightSize(bpy.types.Operator):
    bl_idname = "photographer.calc_light_size"
    bl_label = "Calculate Light surface area"
    bl_description = "Apply Object size and calculate light surface area"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.view_layer.objects.active.type == "LIGHT":
            settings = context.light.photographer
            light = context.light

            size = light.size
            size_y = light.size_y

            if settings.shape in {'SQUARE','DISK'}:
                size_y = light.size

            if context.object.scale[0] != context.object.scale[1] and settings.shape not in {'RECTANGLE', 'ELLIPSE'}:
                if settings.shape == 'SQUARE':
                    settings.shape = 'RECTANGLE'
                if settings.shape == 'DISK':
                     settings.shape = 'ELLIPSE'

            size *= abs(context.object.scale[0])
            size_y *= abs(context.object.scale[1])

            context.object.scale[0] = 1
            context.object.scale[1] = 1

            settings.size = size
            settings.size_y = size_y

            if settings.size_y == settings.size:
                if settings.shape == 'RECTANGLE':
                    settings.shape = 'SQUARE'
                if settings.shape == 'ELLIPSE':
                     settings.shape = 'DISK'

        return{'FINISHED'}

class PHOTOGRAPHER_OT_CopySpotSize(bpy.types.Operator):
    bl_idname = "photographer.copy_spot_size"
    bl_label = "Calculate Light brightness"
    bl_description = "Calculate Light brightness with new Spot sizea"
    bl_options = {'UNDO'}

    def execute(self, context):
        if context.view_layer.objects.active.type == "LIGHT":
            settings = context.light.photographer
            light = context.light

            settings.spot_size = light.spot_size
            settings.spot_size_old = light.spot_size

        return{'FINISHED'}


class PHOTOGRAPHER_OT_SwitchColorMode(bpy.types.Operator):
    bl_idname = "photographer.switchcolormode"
    bl_label = "Switch Color Mode"
    bl_description = "Choose between Temperature in Kelvin and Color RGB"

    light: bpy.props.StringProperty()

    def execute(self, context):
        light = bpy.data.lights[self.light]
        if context.scene.render.engine == 'LUXCORE' and not light.photographer.enable_lc_physical:
            if light.luxcore.color_mode == 'rgb':
                light.luxcore.color_mode = 'temperature'
            else:
                light.luxcore.color_mode = 'rgb'
            # Refresh viewport Trick
            bpy.ops.object.add(type='EMPTY')
            bpy.ops.object.delete()
        else:
            settings = light.photographer
            settings.use_light_temperature = not settings.use_light_temperature

        # Clear attributes
        self.light = ''
        return{'FINISHED'}

class PHOTOGRAPHER_OT_ApplyLightSettings(bpy.types.Operator):
    bl_idname = "photographer.applylightsettings"
    bl_label = "Apply Light Settings"
    bl_description = "If you changed Render engines and settings outside of the Photographer addon, reapply the settings to make sure they are up to date"
    bl_options = {'UNDO'}

    def execute(self, context):
        lights = [l for l in bpy.data.lights]
        for l in lights:
            l.photographer.color = l.photographer.color
            l.photographer.light_temperature = l.photographer.light_temperature
            # Update energy already part of Color and Temperature set functions
            # update_energy(photographer)

        return{'FINISHED'}

class PHOTOGRAPHER_PT_Panel_Light(bpy.types.Panel):
    bl_label = "Physical Light"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES', 'LUXCORE'}

    @classmethod
    def poll(cls, context):
        # Add Panel properties to lights when using CYCLES or EEVEE
        engine = context.engine
        return (context.light) and (engine in cls.COMPAT_ENGINES)  and (bpy.context.preferences.addons[__package__].preferences.use_physical_lights)

    def draw_header(self,context):
        if context.scene.render.engine == 'LUXCORE':
            self.layout.prop(context.light.photographer, "enable_lc_physical", text="")

    def draw_header_preset(self, context):
        if context.light.type == 'POINT':
            light_presets.PHOTOGRAPHER_PT_PhysicalLightPointPresets.draw_panel_header(self.layout)
        elif context.light.type == 'SUN':
            light_presets.PHOTOGRAPHER_PT_PhysicalLightSunPresets.draw_panel_header(self.layout)
        elif context.light.type == 'SPOT':
            light_presets.PHOTOGRAPHER_PT_PhysicalLightSpotPresets.draw_panel_header(self.layout)
        elif context.light.type == 'AREA':
            light_presets.PHOTOGRAPHER_PT_PhysicalLightAreaPresets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        settings = context.light.photographer
        light = context.light
        light_name = context.light.id_data.name

        layout.use_property_decorate = True
        if energy_check(settings):
            layout.label(text="Properties changed outside of Photographer", icon='INFO')
            layout.operator("photographer.applyphotographersettings",
                            text="Recalculate Light Intensity")

        # Compact layout for node editor.
        if self.bl_space_type == 'PROPERTIES':
            layout.row().prop(settings, "light_type", expand=True)
            layout.use_property_split = True
        else:
            layout.use_property_split = True
            layout.row().prop(light, "type")

        row = layout.row(align=True)
        # if settings.use_light_temperature:
        #     row.prop(settings, "light_temperature", slider=True)
        #     row2 = row.row(align=True)
        #     row2.use_property_decorate = False
        #     row2.prop(settings, "preview_color_temp", text='')
        # else:
        #     row.prop(settings, "color")
        # row.prop(settings, "use_light_temperature",
        # icon="EVENT_K" if settings.use_light_temperature else 'EVENT_C',
        # icon_only=True)
        if settings.use_light_temperature:

            row.prop(settings, "light_temperature", slider=True)
            row2 = row.row(align=True)
            row2.use_property_decorate = False
            row2.ui_units_x = 2
            row2.prop(settings, "preview_color_temp", text='')
            row.operator("photographer.switchcolormode",
                        icon="EVENT_K", text='').light=light.name
        else:
            row.prop(settings, "color")
            row.operator("photographer.switchcolormode",
                        icon="EVENT_C", text='').light=light.name

        col = layout.column(align=True)
        if light.type == 'SUN':
            col.prop(settings,"sunlight_unit")
            if settings.sunlight_unit == 'irradiance':
                col.prop(settings,"irradiance")
            elif settings.sunlight_unit == 'illuminance':
                col.prop(settings,"illuminance")
            elif settings.sunlight_unit == 'artistic':
                col.prop(settings,"intensity")
                col.prop(settings,"light_exposure")
        else:
            col.prop(settings, "light_unit")
            if settings.light_unit == 'artistic':
                col.prop(settings,"intensity")
                col.prop(settings,"light_exposure")

            elif settings.light_unit == 'power':
                col.prop(settings,"power")

            elif settings.light_unit == 'advanced_power':
                col.prop(settings,"advanced_power")
                col.prop(settings,"efficacy")

            elif settings.light_unit == 'lumen':
                col.prop(settings,"lumen")

            elif settings.light_unit == 'candela':
                col.prop(settings,"candela")

        split = col.split(factor=0.38, align=True)
        col_stop=split.column(align=False)
        col_stop.alignment = 'RIGHT'
        col_stop.label(text="Stop Adjusment")
        row = split.row(align=True)
        minus_one = row.operator("photographer.light_stop", text="-1")
        minus_one.light = light.name
        minus_one.factor = -1
        minus_half = row.operator("photographer.light_stop", text="-0.5")
        minus_half.light = light.name
        minus_half.factor= -0.5
        plus_half = row.operator("photographer.light_stop", text="+0.5")
        plus_half.light = light.name
        plus_half.factor = 0.5
        plus_one = row.operator("photographer.light_stop", text="+1")
        plus_one.light = light.name
        plus_one.factor = 1

        # Normalize by Color and Per Square meter
        if light.type == 'SUN':
            if settings.sunlight_unit == 'illuminance':
                col.prop(settings, "normalizebycolor")

        else:
            if settings.light_unit in {'lumen','candela'}:
                if settings.light_type == 'AREA':
                    col.prop(settings,"per_square_meter")
                col.prop(settings, "normalizebycolor")

        # EEVEE Specific Specular setting
        if context.engine == 'BLENDER_EEVEE':
            col.separator()
            if bpy.app.version >= (2,93,0):
                col.prop(light, "diffuse_factor", text="Diffuse")
            col.prop(light, "specular_factor", text="Specular")
            if bpy.app.version >= (2,93,0):
                col.prop(light, "volume_factor", text="Volume")

        col.separator()

        if settings.light_type in {'POINT', 'SPOT'}:
            col.prop(light, "shadow_soft_size", text="Size")
        elif settings.light_type == 'SUN':
            col.prop(light, "angle")
            col.prop(settings, "use_elevation", text="Use Horizontal Coordinate")
            subcol = col.column(align=True)
            subcol.enabled = settings.use_elevation
            subcol.prop(settings, "azimuth", slider=True)
            subcol.prop(settings, "elevation", slider=True)
        elif settings.light_type == 'AREA':
            col.prop(settings, "shape")
            sub = col.column(align=True)
            if settings.shape in {'SQUARE', 'DISK'}:
                sub.prop(settings, "size")
            elif settings.shape in {'RECTANGLE', 'ELLIPSE'}:
                sub.prop(settings, "size", text="Size X")
                sub.prop(settings, "size_y", text="Y")

            if settings.light_unit == 'candela' and settings.per_square_meter:
                if settings.size_old != light.size or settings.size_y_old != light.size_y or context.object.scale[0] != 1 or context.object.scale[1] != 1:
                    sub.label(icon="INFO", text="Light size has changed and needs to be recalculated.")
                    sub.operator("photographer.calc_light_size")

        col.separator()
        if context.engine == 'CYCLES':
            col.prop(light.cycles, "max_bounces")
            col.prop(light.cycles, "cast_shadow")
            col.prop(light.cycles, "use_multiple_importance_sampling")
            if bpy.app.version >= (3,2,0):
                col.prop(light.cycles, "is_caustics_light")
            if light.type == 'AREA':
                col.prop(light.cycles, "is_portal", text="Portal")

        if context.scene.render.engine == 'LUXCORE' and not settings.enable_lc_physical:
            layout.enabled = False
        else:
            layout.enabled = True

class PHOTOGRAPHER_PT_EEVEE_light_distance(bpy.types.Panel):
    bl_label = "Custom Distance"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "PHOTOGRAPHER_PT_Panel_Light"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_EEVEE'}

    @classmethod
    def poll(cls, context):
        light = context.light
        engine = context.engine

        return (light and light.type != 'SUN') and (engine in cls.COMPAT_ENGINES) and (bpy.context.preferences.addons[__package__].preferences.use_physical_lights)

    def draw_header(self, context):
        light = context.light

        layout = self.layout
        layout.active = light.use_custom_distance
        layout.prop(light, "use_custom_distance", text="")

    def draw(self, context):
        layout = self.layout
        light = context.light
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()

        col.prop(light, "cutoff_distance", text="Distance")

class PHOTOGRAPHER_PT_spot(bpy.types.Panel):
    bl_label = "Spot Shape"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "PHOTOGRAPHER_PT_Panel_Light"
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'}

    @classmethod
    def poll(cls, context):
        light = context.light
        engine = context.engine
        preferences = bpy.context.preferences.addons[__package__].preferences
        use_physical_lights = preferences.use_physical_lights
        if bpy.app.version < (2,93,0):
            return (light and light.type == 'SPOT') and (engine in cls.COMPAT_ENGINES) and (use_physical_lights)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        light = context.light
        settings = context.light.photographer

        col = layout.column()
        if settings.light_unit in {'advanced_power','lumen'} and settings.spot_size_old != light.spot_size:
            col.label(text='Cone Angle has changed and brightness needs to be recalculated', icon='INFO')
            col.operator("photographer.copy_spot_size")
        col.prop(settings, "spot_size", text="Size")
        col.prop(light, "spot_blend", text="Blend", slider=True)

        col.prop(light, "show_cone")


class PHOTOGRAPHER_PT_beam_shape(bpy.types.Panel):
    bl_label = "Beam Shape"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "PHOTOGRAPHER_PT_Panel_Light"
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'}

    @classmethod
    def poll(cls, context):
        light = context.light
        engine = context.engine
        preferences = bpy.context.preferences.addons[__package__].preferences
        use_physical_lights = preferences.use_physical_lights
        if bpy.app.version >= (2,93,0):
            return (light and light.type in {'SPOT','AREA'}) and (engine in cls.COMPAT_ENGINES) and (use_physical_lights)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        light = context.light
        settings = context.light.photographer

        col = layout.column()
        if light.type == 'SPOT':
            if settings.light_unit in {'advanced_power','lumen'} and settings.spot_size_old != light.spot_size:
                col.label(text='Cone Angle has changed and brightness needs to be recalculated', icon='INFO')
                col.operator("photographer.copy_spot_size")
            col.prop(settings, "spot_size", text="Size")
            col.prop(light, "spot_blend", text="Blend", slider=True)

            col.prop(light, "show_cone")
        elif light.type == 'AREA':
            col.prop(light, "spread")
