import bpy
from bpy.props import (BoolProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       FloatVectorProperty,
                       )

import math
# import bl_math
from . import functions
from .white_balance import convert_temperature_to_RGB_table
from .constants import color_temp_desc

default_sunlight_unit = 'irradiance'
default_light_unit = 'power'
default_power = 10
default_advanced_power = 10
default_efficacy = 683
default_lumen = 683
default_candela = 543.514
default_irradiance = 1
default_illuminance = 10
default_intensity = 10
default_light_exposure = 0
default_normalizebycolor = True
default_per_square_meter = False


INTENSITY_DESCRIPTION = (
    "Brightness multiplier"
)

EXPOSURE_DESCRIPTION = (
    "Power-of-2 step multiplier. "
    "An EV step of 1 will double the brightness of the light"
)

POWER_DESCRIPTION = (
    "Power in watt; Radiometric unit used by default in Cycles"
)

ADVANCED_POWER_DESCRIPTION = (
    "Power in watt with tweakable luminous efficacy value and energy conserving option"
)

EFFICACY_DESCRIPTION = (
    "Luminous efficacy in lumens per watt"
)

LUMEN_DESCRIPTION = (
    "Luminous flux in lumens, assuming a maximum possible luminous efficacy of 683 lm/W.\n"
    "Photometric unit, it should be normalized by Color Luminance.\n"
    "Best for Point lights, using Lightbulb packages as reference"
)

CANDELA_DESCRIPTION = (
    "Luminous intensity in candela (luminous power per unit solid angle).\n"
    "Photometric unit, it should be normalized by Color Luminance.\n"
    "Best for Spot lights to maintain brighness when changing Angle"
)

IRRADIANCE_DESCRIPTION = (
    "Radiant flux per unit area in Watts per square meter."
)

ILLUMINANCE_DESCRIPTION = (
    "Luminous flux per unit area in Lumens per square meter, called Lux. \n"
    "Photometric unit, it should be normalized by Color Luminance."
)

PER_SQUARE_METER_DESCRIPTION = (
    "Per Square Meter allows to maintain brightness when changing Size.\n"
    "Candela per square meter (also called Nit) is the unit of Luminance. \n"
    "Lumen per square meter is often use for LED strip lights, and corresponds to \n"
    "the emission intensity of the Area Light surface (not to be mistaken for Illuminance in Lux)"
)

LUX_DESCRIPTION = (
    "Illuminance in Lux (luminous flux incident on a surface in lumen per square meter).\n"
    "Photometric unit, it should be normalized by Color Luminance"
)

NORMALIZEBYCOLOR_DESCRIPTION = (
    "Normalize intensity by the Color Luminance.\n"
    "Recommended for Photometric units (Lumen, Candela, Lux) to simulate \n"
    "the luminous efficiency function"
)

SPOT_SIZE_DESCRIPTION = (
    "Angle of the spotlight beam"
)

SPREAD_DESCRIPTION = (
    "How widely the emitted light fans out, as in the case of a gridded box"
)

SIZE_DESCRIPTION = (
    "Size of the area of the area light, X direction size for rectangle shapes"
)

SIZE_Y_DESCRIPTION = (
    "Size of the area of the area light, Y direction size for rectangle shapes"
)

# UNIT CONVERSIONS
def normalizebycolor_fac(self):
    if self.normalizebycolor:
        x = functions.rgb_to_luminance(self.color)
        if x != 0:
            return x
        else:
            return 1
    else:
        return 1

def unit_scale_conversion(x):
    if bpy.context.preferences.addons[__package__].preferences.follow_unit_scale:
        x /= math.pow(bpy.context.scene.unit_settings.scale_length,2)
    return x

def artistic_factor(self):
    x = pow(2, self.light_exposure)

    return unit_scale_conversion(x)

def power_factor(self):
    if bpy.context.scene.render.engine == 'LUXCORE':
        x = 683
    else:
        x = 1

    return x

def advanced_power_factor(self):
    if self.light_type == 'SPOT':
        x = self.efficacy / (683 * (1 - math.cos(self.spot_size/2)))* 2
        # Cycles Spotlight doesn't conserve energy by default and needs to be compensated.
    elif self.light_type == 'AREA':
        x = self.efficacy / (683 * 2)

    else:
        x = self.efficacy / 683

    if bpy.context.scene.render.engine == 'LUXCORE':
        x *= 683

    return x

def lumen_factor(self):
    if self.light_type == 'SPOT':
        x = 1 / (683 * (1 - math.cos(self.spot_size/2))) * 2
        # Cycles Spotlight doesn't conserve energy by default and needs to be compensated.
    elif self.light_type == 'AREA':
        # Using 155 degrees angle for area lights to match brightness with spotlight
        x = 1 / (683 * 2 * (1 - math.cos(math.radians(155)/2)))
        if self.per_square_meter:
            light = self.id_data
            obj = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data is light]
            if obj:
                obj_surface = obj[0].scale[0] * obj[0].scale[1]
                if self.shape in {'SQUARE', 'DISK'}:
                    x *= (self.size * self.size * obj_surface)
                elif self.shape in {'RECTANGLE', 'ELLIPSE'}:
                    x *= (self.size * self.size_y * obj_surface)

    else:
        x = 1/ 683

    if x == 0:
        # Avoid division by 0
        x = 0.001

    if bpy.context.scene.render.engine == 'LUXCORE':
        x *= 683

    return unit_scale_conversion(x) / normalizebycolor_fac(self)

def candela_factor(self):
    x = 1 / 683 * 4 * math.pi

    if self.light_type == 'AREA':
        # if bpy.app.version == (2,93,0):
            # From Cycles code, but doesn't work
            # min_spread_angle = math.pi / 180.0
            # spread_angle = 0.5 * (math.pi - max(self.spread, min_spread_angle))
            # tan_spread = math.tan(spread_angle);
            # normalize_spread = 2.0 / (2.0 + (2.0 * spread_angle - math.pi)) * tan_spread;
            # x /= normalize_spread

            # Normalizes brightness fine, but will give wrong value conversion
            # if self.spread >= (math.pi/2):
            #     x *= (1 - math.cos(self.spread)) / 2
            # else:
            #     x *= (1 - math.cos(math.pi/2)) / 2
            #     x /= bl_math.lerp(1,math.pi, math.cos(self.spread))

        x /= math.pi
        if self.per_square_meter:
            light = self.id_data
            obj = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data is light]
            if obj:
                obj_surface = obj[0].scale[0] * obj[0].scale[1]
                if self.shape in {'SQUARE', 'DISK'}:
                    x *= (self.size * self.size * obj_surface)
                elif self.shape in {'RECTANGLE', 'ELLIPSE'}:
                    x *= (self.size * self.size_y * obj_surface)

    if x == 0:
        # Avoid division by 0
        x = 0.001

    if bpy.context.scene.render.engine == 'LUXCORE':
        x *= 683

    return unit_scale_conversion(x) / normalizebycolor_fac(self)

def irradiance_factor(self):
    if bpy.context.scene.render.engine == 'LUXCORE':
        x = 683
    else:
        x = 1
    return x

def illuminance_factor(self):
    if bpy.context.scene.render.engine == 'LUXCORE':
        x = 1
    else:
        x = 1 / 683

    return x / normalizebycolor_fac(self)

# APPLY VALUE CHANGE TO ALL UNITS TO SUPPORT LIGHT UNIT CHANGE
def store_units(self):
    self['power'] = self.id_data.energy / power_factor(self)
    self['advanced_power'] = self.id_data.energy / advanced_power_factor(self)
    self['lumen'] = self.id_data.energy / lumen_factor(self)
    self['candela'] = self.id_data.energy /  candela_factor(self)
    self['intensity'] = self.id_data.energy / artistic_factor(self)

# APPLY VALUE CHANGE TO ALL UNITS TO SUPPORT LIGHT UNIT CHANGE
def store_sun_units(self):
    self['irradiance'] = self.id_data.energy / irradiance_factor(self)
    self['illuminance'] = self.id_data.energy / illuminance_factor(self)
    self['artistic'] = self.id_data.energy / artistic_factor(self)

# ENERGY CALCULATION
def calc_energy(self):
    light = self.id_data

    if self.light_type == 'SUN':
        if self.sunlight_unit == 'irradiance':
            energy = self.irradiance * irradiance_factor(self)

        elif self.sunlight_unit == 'illuminance':
            energy = self.illuminance * illuminance_factor(self)

        elif self.sunlight_unit == 'artistic':
            energy = self.intensity * artistic_factor(self)

    else:

        if self.light_unit == 'artistic':
            energy = self.intensity * artistic_factor(self)

        elif self.light_unit == 'power':
            energy = self.power * power_factor(self)

        elif self.light_unit == 'advanced_power':
            energy = self.advanced_power * advanced_power_factor(self)

        elif self.light_unit == 'lumen':
            energy = self.lumen * lumen_factor(self)

        elif self.light_unit == 'candela':
            energy = self.candela * candela_factor(self)

    return energy

def update_energy(self):
    light = self.id_data

    if self.light_type == 'AREA':
        light.size = self.size
        light.size_y = self.size_y

    light.energy = calc_energy(self)

    # Updating stored previous size values to check if brightness needs to be re-calculated
    self.spot_size_old = self.spot_size
    self.size_old = self.size
    self.size_y_old = self.size_y

    store_units(self)
    store_sun_units(self)

def energy_check(self):
    light = self.id_data
    if light.energy != 0:
        delta_percentage = abs(light.energy - calc_energy(self))*100 / light.energy
        if delta_percentage >= 0.01:
            return True
        else:
            return False
    else:
        return False

# LIGHT UNIT FUNCTIONS
def get_light_unit(self):
    return self.get('light_unit', 1)

def set_light_unit(self,value):
    self['light_unit'] = value
    return None

# SUNLIGHT UNIT FUNCTIONS
def get_sunlight_unit(self):
    return self.get('sunlight_unit', 1)

def set_sunlight_unit(self,value):
    self['sunlight_unit'] = value
    return None

# LIGHT TYPE
def get_type(self):
    if self.id_data.type == 'POINT':
        return 0
    if self.id_data.type == 'SUN':
        return 1
    if self.id_data.type == 'SPOT':
        return 2
    if self.id_data.type == 'AREA':
        return 3

def set_type(self, light_type):
    if light_type == 0:
        self.id_data.type = 'POINT'
    if light_type == 1:
        self.id_data.type = 'SUN'
    if light_type == 2:
        self.id_data.type = 'SPOT'
    if light_type == 3:
        self.id_data.type = 'AREA'

    update_energy(self)

    # Rename if default name
    data_name = self.id_data.name
    obj = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data == self.id_data]
    obj_name = obj[0].name
    type = str(self.id_data.type).lower()
    list = ['point','sun','spot','area']
    for t in list:
        import re
        if t in obj_name.lower():
            new_obj_name = re.sub(t, type.capitalize(), obj_name, flags=re.IGNORECASE)
            obj[0].name = new_obj_name
            break
    for t in list:
        if t in data_name.lower():
            new_data_name = re.sub(t, type.capitalize(), data_name, flags=re.IGNORECASE)
            self.id_data.name = new_data_name
            break
    return None

# SUN ENERGY
def get_irradiance(self):
    if bpy.context.scene.render.engine == 'LUXCORE':
        return self.get('irradiance', default_irradiance)
    else:
        store_sun_units(self)
        return self.id_data.energy

def set_irradiance(self, value):
    if bpy.context.scene.render.engine == 'LUXCORE':
        self['irradiance'] = value
        update_energy(self)
    else:
        self.id_data.energy = value
    return None

def get_illuminance(self):
    return self.get('illuminance', default_illuminance)

def set_illuminance(self, value):
    self['illuminance'] = value
    update_energy(self)
    return None

# ARTISTIC
def get_intensity(self):
    if self.id_data.type == 'SUN':
        default = 1
    else:
        default = 10
    return self.get('intensity', default)

def set_intensity(self, value):
    self['intensity'] = value
    update_energy(self)
    return None

def get_light_exposure(self):
    return self.get('light_exposure', default_light_exposure)

def set_light_exposure(self, value):
    self['light_exposure'] = value
    update_energy(self)
    return None

def get_power(self):
    if bpy.context.scene.render.engine == 'LUXCORE':
        return self.get('power', default_power)
    else:
        store_units(self)
        return self.id_data.energy

def set_power(self, value):
    if bpy.context.scene.render.engine == 'LUXCORE':
        self['power'] = value
        update_energy(self)
    else:
        self.id_data.energy = value

    update_energy(self)
    return None

def get_advanced_power(self):
    return self.get('advanced_power', default_advanced_power)

def set_advanced_power(self,value):
    self['advanced_power'] = value
    update_energy(self)
    return None

def get_efficacy(self):
    return self.get('efficacy', default_efficacy)

def set_efficacy(self,value):
    self['efficacy'] = value
    update_energy(self)
    return None

def get_lumen(self):
    return self.get('lumen', default_lumen)

def set_lumen(self,value):
    self['lumen'] = value
    update_energy(self)
    return None

def get_candela(self):
    return self.get('candela', default_candela)

def set_candela(self,value):
    self['candela'] = value
    update_energy(self)
    return None

def get_per_square_meter(self):
    return self.get('per_square_meter', default_per_square_meter)

def set_per_square_meter(self,value):
    self['per_square_meter'] = value
    update_energy(self)
    return None

# NORMALIZE BY COLOR
def get_normalizebycolor(self):
    return self.get('normalizebycolor', default_normalizebycolor)

def set_normalizebycolor(self,value):
    self['normalizebycolor'] = value
    update_energy(self)
    return None

# SHAPE
def get_shape(self):
    if self.light_type == 'AREA':
        if self.id_data.shape == 'SQUARE':
            return 0
        if self.id_data.shape == 'RECTANGLE':
            return 1
        if self.id_data.shape == 'DISK':
            return 2
        if self.id_data.shape == 'ELLIPSE':
            return 3
    else:
        return 0

def set_shape(self, shape):
    if self.light_type == 'AREA':
        if shape == 0:
            self.id_data.shape = 'SQUARE'
        if shape == 1:
            self.id_data.shape = 'RECTANGLE'
        if shape == 2:
            self.id_data.shape = 'DISK'
        if shape == 3:
            self.id_data.shape = 'ELLIPSE'
        update_energy(self)
    return None

# LIGHT SIZE
def get_size(self):
    if self.id_data.type == 'AREA':
        return self.id_data.size
    else:
        return 1

def set_size(self, size):
    if self.id_data.type == 'AREA':
        self.id_data.size = size
        update_energy(self)
    return None

def get_size_y(self):
    if self.id_data.type == 'AREA':
        return self.id_data.size_y
    else:
        return 1

def set_size_y(self, size_y):
    if self.id_data.type == 'AREA':
        self.id_data.size_y = size_y
        update_energy(self)
    return None

def get_spot_size(self):
    if self.id_data.type == 'SPOT':
        return self.id_data.spot_size
    else:
        return 1

def set_spot_size(self, spot_size):
    if self.id_data.type == 'SPOT':
        self.id_data.spot_size = spot_size
        update_energy(self)
    return None

def get_spread(self):
    if self.id_data.type == 'AREA':
        return self.id_data.spread
    else:
        return 1

def set_spread(self, spread):
    if self.id_data.type == 'AREA':
        self.id_data.spread = spread
        update_energy(self)
    return None

# COLOR
def temp_to_rgb_linear(temperature):
    color = convert_temperature_to_RGB_table(temperature)
    color = [functions.srgb_to_linear(color[0]), functions.srgb_to_linear(color[1]), functions.srgb_to_linear(color[2])]
    return color

def get_color(self):
    return self.id_data.color

def set_color(self, value):
    self['color'] = value
    if not self.use_light_temperature:
        self.id_data.color = value
    update_energy(self)
    return None

# LIGHT TEMPERATURE
def get_light_temperature_color(self):
    if self.get('enable_lc_physical', False):
        if bpy.context.scene.render.engine == 'LUXCORE' and not self.enable_lc_physical:
            temp = self.id_data.luxcore.temperature
        else:
            temp = self.light_temperature
    else:
        temp = self.light_temperature
    color = temp_to_rgb_linear(temp)
    return color

def set_light_temperature_color(self, value):
    return None

def get_light_temperature(self):
    return self.get('light_temperature', 6500)

def set_light_temperature(self, value):
    self['light_temperature'] = value
    color = temp_to_rgb_linear(value)
    if self.use_light_temperature:
        self.id_data.color = color
        self['color'] = value
    update_energy(self)
    return None

def get_use_light_temperature(self):
    return self.get('use_light_temperature', False)

def set_use_light_temperature(self, value):
    self['use_light_temperature'] = value
    color = temp_to_rgb_linear(self.light_temperature)
    if value:
        self.id_data.color = color
        self['color'] = value
    update_energy(self)
    return None

def update_enable_lc_physical(self,context):
    if context.scene.render.engine == 'LUXCORE':
        luxcore = self.id_data.luxcore
        luxcore.use_cycles_settings = self.enable_lc_physical
        update_energy(self)

# def get_use_custom_distance(self):
#     return self.get('use_custom_distance', default_use_custom_distance)
#
# def set_use_custom_distance(self, value):
#     self['use_custom_distance'] = value
#     self.id_data.use_custom_distance = value
#     return None
#
# def get_cutoff_distance(self):
#     return self.get('use_cutoff_distance', default_cutoff_distance)
#
# def set_cutoff_distance(self, value):
#     self['cutoff_distance'] = value
#     self.id_data.cutoff_distance = value
#     return None

def update_use_elevation(self,context):
    if self.use_elevation:
        self.azimuth = self.azimuth
        self.elevation = self.elevation

def get_azimuth(self):
    return self.get('azimuth', 0)

def set_azimuth(self, value):
    self['azimuth'] = value
    if self.use_elevation:
        obj = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data is self.id_data]
        obj[0].rotation_euler[2] = math.pi - self.azimuth

        world = bpy.context.scene.world
        if world:
            if world.use_nodes:
                nodes = world.node_tree.nodes
                for node in nodes:
                    if type(node) is bpy.types.ShaderNodeTexSky:
                        if node.sky_type == 'NISHITA':
                            node.sun_rotation = value
    return None

def get_elevation(self):
    return self.get('elevation', 0.2617)

def set_elevation(self, value):
    self['elevation'] = value
    if self.use_elevation:
        obj = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data is self.id_data]
        obj[0].rotation_euler[0] = math.pi/2 - self.elevation

        world = bpy.context.scene.world
        if world:
            if world.use_nodes:
                nodes = world.node_tree.nodes
                for node in nodes:
                    if type(node) is bpy.types.ShaderNodeTexSky:
                        if node.sky_type == 'NISHITA':
                            node.sun_elevation = value
    return None

# PROPERTIES
class PhotographerLightSettings(bpy.types.PropertyGroup):

    enable_lc_physical: BoolProperty(
        name="Use Physical Light",
        description=("Use Photographer Physical Light properties instead of LuxCore properties.\n"
                    "Useful for switching between Cycles, EEVEE and LuxCore"
                    "but it will remove some LuxCore specific settings"),
        default=False,
        options = {'HIDDEN'},
        update = update_enable_lc_physical
    )

    light_types = [
        ("POINT", "Point", "Omnidirectional point light source", 'LIGHT_POINT',0),
        ("SUN", "Sun", "Constant direction parallel ray light source",'LIGHT_SUN',1),
        ("SPOT", "Spot", "Directional cone light source",'LIGHT_SPOT',2),
        ("AREA", "Area", "Directional area light source",'LIGHT_AREA',3),
    ]

    light_type: EnumProperty(
        name="Light Type",
         items=light_types,
        get=get_type,
        set=set_type,
    )

    color: FloatVectorProperty(
        name="Color", description="Light Color",
        subtype='COLOR',
        min=0.0, size=3,
        default=(1.0,1.0,1.0),
        get=get_color,
        set=set_color,
    )

    light_temperature : IntProperty(
        name="Color Temperature", description=color_temp_desc,
        min=1000, max=13000, default=6500,
        get=get_light_temperature,
        set=set_light_temperature,
    )

    use_light_temperature: BoolProperty(
        name="Use Light Color Temperature",
        default=False,
        options = {'HIDDEN'},
        get=get_use_light_temperature,
        set=set_use_light_temperature,
    )

    preview_color_temp : FloatVectorProperty(
        name="Preview Color", description="Color Temperature preview color",
        subtype='COLOR', min=0.0, max=1.0, size=3,
        options = {'HIDDEN'},
        get=get_light_temperature_color,
        set=set_light_temperature_color,
    )

    sunlight_units = [
        ("artistic", "Artistic", "Artist friendly unit using Gain and Exposure",0),
        ("irradiance", "Irradiance (W/m2)", "Irradiance in Watt per square meter",1),
        ("illuminance", "Illuminance (Lux)", "Illuminance in Lux",2),
    ]

    sunlight_unit: EnumProperty(
        name="Light Unit",
        items=sunlight_units,
        default=default_sunlight_unit,
        get=get_sunlight_unit,
        set=set_sunlight_unit,
        options = {'HIDDEN'},
    )

    irradiance: FloatProperty(
        name="Irradiance W/m2", description=IRRADIANCE_DESCRIPTION,
        default=default_irradiance,
        min=0, precision=3,
        get=get_irradiance,
        set=set_irradiance,
    )

    illuminance: FloatProperty(
        name="Lux", description=ILLUMINANCE_DESCRIPTION,
        default=default_illuminance, min=0, precision=2,
        get=get_illuminance,
        set=set_illuminance,
    )

    light_units = [
        ("artistic", "Artistic", "Artist friendly unit using Gain and Exposure",0),
        ("power", "Power", "Radiant flux in Watt",1),
        ("lumen", "Lumen", "Luminous flux in Lumen",2),
        ("candela", "Candela", "Luminous intensity in Candela",3),
        ("advanced_power", "Power (Advanced)", "Radiant flux in Watt",4),
    ]

    light_unit: EnumProperty(
        name="Light Unit",
        items=light_units,
        default=default_light_unit,
        get=get_light_unit,
        set=set_light_unit,
        options = {'HIDDEN'},
    )

    intensity: FloatProperty(
        name="Intensity", description=INTENSITY_DESCRIPTION,
        default=default_intensity, soft_min=0,
        get=get_intensity,
        set=set_intensity,
    )

    light_exposure: FloatProperty(
        name="Exposure", description=EXPOSURE_DESCRIPTION,
        default=default_light_exposure,
        soft_min=-10, soft_max=10, precision=2,
        get=get_light_exposure,
        set=set_light_exposure,
    )

    power: FloatProperty(
        name="Power", description=POWER_DESCRIPTION,
        default=default_power,
        soft_min=0, precision=5, unit='POWER',
        get=get_power,
        set=set_power,
    )

    advanced_power: FloatProperty(
        name="Power (Advanced)", description=POWER_DESCRIPTION,
        default=default_advanced_power,
        soft_min=0, precision=4, unit='POWER',
        get=get_advanced_power,
        set=set_advanced_power,
    )

    efficacy: FloatProperty(
        name="Efficacy (lm/W)", description=EFFICACY_DESCRIPTION,
        default=default_efficacy,
        min=0, precision=1,
        get=get_efficacy,
        set=set_efficacy,
    )

    lumen: FloatProperty(
        name="Lumen", description=LUMEN_DESCRIPTION,
        default=default_lumen,
        soft_min=0, precision=1,
        get=get_lumen,
        set=set_lumen,
    )

    candela: FloatProperty(
        name="Candela", description=CANDELA_DESCRIPTION,
        default=default_candela,
        soft_min=0, precision=1,
        get=get_candela,
        set=set_candela,
    )

    normalizebycolor: BoolProperty(
        name="Normalize by Color Luminance", description=NORMALIZEBYCOLOR_DESCRIPTION,
        default=default_normalizebycolor,
        get=get_normalizebycolor,
        set=set_normalizebycolor,
    )

    per_square_meter: BoolProperty(
        name="Per square meter (/m\u00B2)", description=PER_SQUARE_METER_DESCRIPTION,
        default=default_per_square_meter,
        get=get_per_square_meter,
        set=set_per_square_meter,
    )

    spot_size: FloatProperty(
        name="Cone Angle (Size)", description=SPOT_SIZE_DESCRIPTION,
        default=0.785398, min=0.0174533, max=3.14159, precision=3, unit='ROTATION',
        get=get_spot_size,
        set=set_spot_size,
    )

    spot_size_old: FloatProperty()

    # spread: FloatProperty(
    #     name="Spread", description=SPREAD_DESCRIPTION,
    #     default=0.785398, min=0.0174533, max=3.14159, precision=3, unit='ROTATION',
    #     get=get_spread,
    #     set=set_spread,
    # )

    light_shapes = [
        ("SQUARE", "Square", ""),
        ("RECTANGLE", "Rectangle", ""),
        ("DISK", "Disk", ""),
        ("ELLIPSE", "Ellipse", ""),
    ]

    shape: EnumProperty(
        name="Shape",
        items=light_shapes,
        default='SQUARE',
        get=get_shape,
        set=set_shape,
    )

    size: FloatProperty(
        name='Size', description=SIZE_DESCRIPTION,
        default=0.25, min=0.001, precision=3, unit='LENGTH',
        get=get_size,
        set=set_size,
    )

    size_old: FloatProperty(
        name='Size', description=SIZE_DESCRIPTION,
        default=0.25, min=0, precision=3, unit='LENGTH',
    )

    size_y: FloatProperty(
        name='Size Y', description=SIZE_Y_DESCRIPTION,
        default=0.25, min=0.001, precision=3, unit='LENGTH',
        get=get_size_y,
        set=set_size_y,
    )

    size_y_old: FloatProperty(
        name='Size Y', description=SIZE_Y_DESCRIPTION,
        default=0.25, min=0, precision=3, unit='LENGTH',
    )

    use_elevation: BoolProperty(
        name='Use Horizontal Coordinate System',
        description='Rotates the Sun using Azimuth and Elevation',
        default=False,
        update = update_use_elevation,
    )

    azimuth: FloatProperty(
        name='Azimuth', description='Horizontal rotation of the Sun',
        default=0, soft_min=0, soft_max=6.283, unit='ROTATION',
        get = get_azimuth,
        set = set_azimuth,
    )

    elevation: FloatProperty(
        name='Elevation', description='Vertical rotation of the Sun',
        default=0.2617, soft_min=-0.2617, soft_max=1.571, unit='ROTATION',
        get = get_elevation,
        set = set_elevation,
    )

    target_enabled : bpy.props.BoolProperty(
        name = "Light Target", description = "Light Target Tracking on an object",
        options = {'HIDDEN'},
        default = False,
    )
    # use_custom_distance: BoolProperty(
    #     name="Custom Distance",
    #     default=default_use_custom_distance,
    #     get=get_use_custom_distance,
    #     set=set_use_custom_distance,
    # )
    #
    # cutoff_distance: FloatProperty(
    #     name="Distance",
    #     default=default_cutoff_distance,
    #     unit='LENGTH',
    #     get=get_cutoff_distance,
    #     set=set_cutoff_distance,
    # )
