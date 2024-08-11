import bpy, blf, math
from mathutils import Matrix,Vector
from ..constants import addon_name
from .world import get_environment_tex
from ..operators.target import create_target, get_target
from ..functions import raycast, rot_around_pivot,same_sign
from .autofocus import list_focus_planes, list_dof_objects

MODAL_MODES = ('POSITION','ELEVATION','ORBIT','DISTANCE', 'INTENSITY', 'TEMPERATURE', 'SIZE', 'CONE')

def get_light_unit(context, light):
    preferences = context.preferences.addons[addon_name].preferences
    settings = light.photographer

    if light.type == 'SUN':
        if preferences.use_physical_lights:
            if settings.sunlight_unit == 'artistic':
                light_unit = 'intensity'
            else:
                light_unit = settings.sunlight_unit
        else:
            light_unit = 'energy'

    else:
        if preferences.use_physical_lights:
            if settings.light_unit == 'artistic':
                light_unit = 'intensity'
            else:
                light_unit = settings.light_unit
        else:
            light_unit = 'energy'
    
    return light_unit


def create_light(context,type):
    
    # Switch to object mode to create light
    if bpy.context.scene.collection.all_objects:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.light_add(type=type)
    # Select Light
    light_obj = context.view_layer.objects.active

    light = light_obj.data
    settings = light.photographer
    prefs = bpy.context.preferences.addons[addon_name].preferences

    # Apply Sun default settings
    if light.type == 'SUN':
        if prefs.use_physical_lights:
            settings.sunlight_unit = prefs.default_sunlight_unit
            if settings.sunlight_unit == 'irradiance':
                settings.irradiance = prefs.default_irradiance
            elif settings.sunlight_unit == 'illuminance':
                settings.illuminance = prefs.default_illuminance
            elif settings.sunlight_unit == 'artistic':
                settings.intensity = prefs.default_intensity
                settings.light_exposure = prefs.default_light_exposure
        elif context.scene.render.engine == 'LUXCORE' and not prefs.use_physical_lights:
            light.luxcore.light_type = prefs.default_lc_light_type
            if light.luxcore.light_type == 'sun':
                light.luxcore.sun_sky_gain = prefs.default_sun_sky_gain
            else:
                light.luxcore.gain = prefs.default_gain
            light.luxcore.exposure = prefs.default_light_exposure
        else:
            light.energy = prefs.default_irradiance
    else:
        # Apply other lights default settions
        unit = ''
        if prefs.use_physical_lights:
            data = settings
            unit = prefs.default_light_unit
            data.light_unit = unit
        elif context.scene.render.engine == 'LUXCORE' and not prefs.use_physical_lights:
            data = light.luxcore
            unit = prefs.default_lc_light_unit
            data.light_unit = unit
        if unit:
            if unit == 'artistic':
                if context.scene.render.engine == 'LUXCORE' and not prefs.use_physical_lights:
                    data.gain = prefs.default_gain
                    data.exposure = prefs.default_light_exposure
                else:
                    data.intensity = prefs.default_intensity
                    data.light_exposure = prefs.default_light_exposure
            if unit == 'power':
                data.power = prefs.default_power
            if unit == 'advanced_power':
                data.advanced_power = prefs.default_advanced_power
                data.efficacy = prefs.default_efficacy
            if unit == 'lumen':
                data.lumen = prefs.default_lumen
            if unit == 'candela':
                data.candela = prefs.default_candela
            if unit in {'lumen','candela'}:
                data.normalizebycolor = prefs.default_normalizebycolor
                data.per_square_meter = prefs.default_per_square_meter
        else:
            light.energy = prefs.default_power

    unit_scale = context.scene.unit_settings.scale_length

    light.use_custom_distance = prefs.default_use_custom_distance
    light.cutoff_distance = prefs.default_cutoff_distance / unit_scale
    light.shadow_buffer_bias = prefs.default_shadow_buffer_bias
    light.use_contact_shadow = prefs.default_use_contact_shadow
    light.contact_shadow_distance = prefs.default_contact_shadow_distance / unit_scale
    light.contact_shadow_bias = prefs.default_contact_shadow_bias
    light.contact_shadow_thickness = prefs.default_contact_shadow_thickness

    if context.scene.render.engine == 'LUXCORE':
        settings.enable_lc_physical = prefs.use_physical_lights
        light_obj.data.luxcore.use_cycles_settings = prefs.use_physical_lights

    return light_obj

def create_light_target(context, light_obj,parent=False, offset_location=False):
    #Create Target object at the selected object center
    if offset_location:
        offset_loc = Vector((0.0,1.0,2.0))
        light_obj.location += offset_loc
    target_obj = create_target(context,(0,0,0),light_obj)
    if parent:
        #Parent the target object to the object under the mask
        target_obj.parent = object

    #Set the Tracking to enable
    light_obj.data.photographer.target_enabled = True

    return target_obj

def store_light_params(self,context):
    light = self.light_obj.data
    settings = light.photographer
    preferences = context.preferences.addons[addon_name].preferences

    self.stored_lgt_location = self.light_obj.location
    self.stored_lgt_rotation = self.light_obj.rotation_euler
    self.prev_lgt_loc = self.stored_lgt_location
    self.prev_lgt_rot = self.stored_lgt_rotation

    if self.target_obj:
        self.stored_tgt_location = self.target_obj.location
        self.stored_tgt_rotation = self.target_obj.rotation_euler
        self.prev_tgt_loc = self.stored_tgt_location
        self.prev_tgt_rot = self.stored_tgt_rotation

        self.distance = (self.light_obj.location - self.target_obj.location).length

    light_unit = get_light_unit(context,light)
    self.stored_intensity = settings[light_unit]
    self.stored_temperature = settings.light_temperature

    if light.type == 'SUN':
        self.stored_size = light.angle
    elif light.type == 'AREA':
        if preferences.use_physical_lights:
            self.stored_size = settings.size
        else:
            self.stored_size = light.size
    else:
        self.stored_size = light.shadow_soft_size

    # Store Cone
    if light.type == 'SPOT':
        if preferences.use_physical_lights:
            self.stored_cone = settings.spot_size
        else:
            self.stored_cone = light.spot_size
    elif light.type == 'AREA':
        self.stored_cone = light.spread


def draw_string(self, color1, color2, left, bottom, text, max_option, divide = 1):
    """ Draw the text like 'option : key' or just 'option' """

    font_id = 0

    blf.enable(font_id,blf.SHADOW)
    blf.shadow(font_id, 0, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(font_id,2,-2)
    line_height = (blf.dimensions(font_id, "gM")[1] * 1.45)
    y_offset = 5

    # Test if the text is a list formatted like : ('option', 'key')
    if isinstance(text,list):
        spacer_text = " : "
        spacer_width = blf.dimensions(font_id, spacer_text)[0]
        for string in text:
            if string[0].lower() == self.mode.lower():
                color = color1
            else:
                color = color2
            blf.position(font_id, (left), (bottom + y_offset), 0)
            blf.color(font_id, *color)
            blf.draw(font_id, string[0])
            blf.position(font_id, (left + max_option), (bottom + y_offset), 0)
            blf.draw(font_id, spacer_text)
            blf.color(font_id, *color2)
            blf.position(font_id, (left + max_option + spacer_width), (bottom + y_offset), 0)
            blf.draw(font_id, string[1])
            y_offset += line_height
    else:
        # The text is formatted like : ('option')
        blf.position(font_id, left, (bottom + y_offset), 0)
        blf.color(font_id, *color1)
        blf.draw(font_id, text)
        y_offset += line_height

    blf.disable(font_id,blf.SHADOW)

def get_text_info(self, context, help_txt):
    """ Return the dimensions of each part of the text """

    #Extract the longest first option in sublist
    max_option = max(list(blf.dimensions(0, row[0])[0] for row in help_txt))

    #Extract the longest key in sublist
    max_key = max(list(blf.dimensions(0, row[1])[0] for row in help_txt))

    #Space between option and key  with a comma separator (" : ")
    comma = blf.dimensions(0, "_:_")[0]

    #Get a default height for all the letters
    line_height = (blf.dimensions(0, "gM")[1] * 1.45)

    #Get the total height of the text
    bloc_height = 0
    for row in help_txt:
        bloc_height += line_height

    return(help_txt, bloc_height, max_option, max_key, comma)

def draw_callback_px(self,context):
    font_id = 0
    region = context.region
    region_width = int(region.width / 2.0)
    ui_scale = bpy.context.preferences.system.ui_scale

    overlap = context.preferences.system.use_region_overlap

    t_panel_width = 0
    if overlap:
        for region in context.area.regions:
            if region.type == 'TOOLS':
                t_panel_width = region.width

    # Draw the center command from bottom to top

    # Get the size of the text
    text_size = 18 if region.width >= 850 else 12
    ui_scale = bpy.context.preferences.system.ui_scale
    blf.size(0, round(text_size * ui_scale), 72)

    x_offset = 35
    light = context.object.data
    settings = light.photographer
    key_color = (1.0,0.7,0.02,1.0)
    text_color = (1.0,1.0,1.0,1.0)
    active_mode_color = (1.0,0.7,0.02,1.0)

    xHelp = 30 + t_panel_width
    yHelp = 100

    help_txt =[
            ["Cancel", "Esc"],\
            ["Validate", "Enter, Right Mouse"],\
            ["Pause", "Space, Left Mouse"],\
            ["Size", "S"],\
            ["Intensity", "I"],\
            ["Color Temp", "K"],\
            ["Position", "G, W"],\
            ["Target", "T"],\
            ["Elevation", "E"],\
            ["Orbit", "R"],\
            ["Distance", "D"],\
            ]
    if light.type == 'SPOT':
        help_txt.insert(4,["Cone", "C"])
    elif light.type == 'AREA':
        help_txt.insert(4,["Spread", "C"])
            
    help_txt, bloc_height, max_option, max_key, comma = get_text_info(self, context, help_txt)
    draw_string(self, key_color, text_color, xHelp, yHelp, help_txt, max_option)   

    text =  self.mode        
    if self.mode == 'DISTANCE':
        text += " : " + str(round(self.target_distance,3))
    elif self.mode == 'INTENSITY':
        light_unit = get_light_unit(context, light)
        text = light_unit.capitalize() + " : " + str(round(settings.get(light_unit,None),3))
    elif self.mode == 'TEMPERATURE':
        text += " : " + str(settings.light_temperature) + " K"
    elif self.mode == 'CONE':
        if light.type == 'SPOT':
            text += " : " + str(round(math.degrees(light.spot_size),2)) + "°"
        elif light.type == 'AREA':
            text = "SPREAD : " + str(round(math.degrees(light.spread),2)) + "°"

    # find text dimensions
    dim = blf.dimensions(font_id,text)
    # Center Text
    x_offset = (region.width - dim[0]) / 2
    y_offset = 35
    blf.position(font_id, x_offset, y_offset ,0)
    blf.size(font_id, 28, 72)
    blf.color(font_id, 1.0,0.7,0.02,1.0)
    blf.draw(font_id,text)

def light_modal(self, context, event, parent_target=False):
    context.area.tag_redraw()
    preferences = context.preferences.addons[addon_name].preferences
    light = self.light_obj.data
    settings = light.photographer
    light_unit = get_light_unit(context,self.light_obj.data)

    # Allow navigation for Blender and Maya shortcuts
    if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.alt or event.alt and event.type == 'LEFTMOUSE' or event.alt and event.type == 'RIGHTMOUSE':
        return {'PASS_THROUGH'}

    self.mouse_region_x = event.mouse_region_x
    self.mouse_region_y = event.mouse_region_y

    object = None

    if self.target_obj:
        self.transform_offset = self.light_obj.location - self.target_obj.location

        if context.space_data.type == 'VIEW_3D':            
            if self.mode == 'POSITION':
                if event.type == 'MOUSEMOVE':
                    #Raycast and store the hit location
                    result, location, object, normal = raycast(context, event, False, False, self.light_obj, coord=(self.mouse_region_x, self.mouse_region_y))
                
                    if result:
                        if object is not None:
                            self.target_obj.location = location
                            
                            self.light_obj.location = location + self.transform_offset
                            self.transform_offset = self.light_obj.location - self.target_obj.location
            
            elif self.mode == 'TARGET':
                if event.type == 'MOUSEMOVE':
                    #Raycast and store the hit location
                    result, location, object, normal = raycast(context, event, False, False, self.light_obj, coord=(self.mouse_region_x, self.mouse_region_y))
                
                    if result:
                        if object is not None:
                            self.target_obj.location = location
                            self.transform_offset = self.light_obj.location - self.target_obj.location
                
            elif self.mode == 'ELEVATION':
                if event.type == 'MOUSEMOVE':
                    angle = (event.mouse_x - self.initial_x)/3
                    vec = Vector((1.0, 0.0, 0.0))
                    vec.rotate(self.light_obj.rotation_euler)

                    # Avoid going to the other side and bouncing
                    old_loc = self.light_obj.location
                    new_loc =  rot_around_pivot(self.light_obj, self.target_obj, angle, vec, False)
                    if same_sign((new_loc-self.target_obj.location).x, (old_loc-self.target_obj.location).x):
                        rot_around_pivot(self.light_obj, self.target_obj, angle, vec)
                    self.initial_x = event.mouse_x

            elif self.mode == 'ORBIT':
                if event.type == 'MOUSEMOVE':
                    angle = (event.mouse_x - self.initial_x)/3
                    rot_around_pivot(self.light_obj, self.target_obj, angle, 'Z')
                    self.initial_x = event.mouse_x

            elif self.mode == 'DISTANCE':
                distance_offset = 0.0
                if event.type == 'MOUSEMOVE':
                    distance_offset = (event.mouse_x - self.initial_x)/30
                    # if event.type == 'WHEELUPMOUSE':
                    #     distance_offset += 0.2
                    # elif event.type == 'WHEELDOWNMOUSE':
                    #     distance_offset -= 0.2  
                    movement_vector = self.light_obj.matrix_world.to_3x3() @ Vector((0, 0, distance_offset))
                    old_loc = self.light_obj.location
                    new_loc =  self.light_obj.location + movement_vector
                    if same_sign((new_loc-self.target_obj.location).x, (old_loc-self.target_obj.location).x):
                        self.light_obj.location += movement_vector
                    self.initial_x = event.mouse_x
                    self.target_distance = (self.light_obj.location - self.target_obj.location).length
            
            elif self.mode == 'INTENSITY':
                if event.type == 'MOUSEMOVE':
                    exposure_offset = (event.mouse_x - self.initial_x)/40
                    # Support for regular Blender Light
                    if light_unit == 'energy':             
                        new_intensity = self.light_obj.data[light_unit] * math.pow(2,exposure_offset)
                        setattr(self.light_obj.data , light_unit, new_intensity)
                    else:
                        new_intensity = settings[light_unit] * math.pow(2,exposure_offset)
                        setattr(settings, light_unit, new_intensity)                        
                    self.initial_x = event.mouse_x

            elif self.mode == 'TEMPERATURE':
                if event.type == 'MOUSEMOVE':
                    if preferences.use_physical_lights:
                        if not settings.use_light_temperature:
                            settings.use_light_temperature = True
                    
                    temp_offset = (event.mouse_x - self.initial_x)*10
                    if settings.light_temperature + int(temp_offset) > 13000:
                        settings.light_temperature = 13000
                    elif settings.light_temperature + int(temp_offset) < 1000:
                        settings.light_temperature = 1000
                    else:
                        settings.light_temperature += int(temp_offset)
                    self.initial_x = event.mouse_x

            elif self.mode == 'SIZE':
                if event.type == 'MOUSEMOVE':
                    size_offset = (event.mouse_x - self.initial_x)/200
                    if light.type == 'SUN':
                        light.angle += size_offset
                    elif light.type == 'AREA':
                        if settings.size > 0:
                            ratio = settings.size_y / settings.size
                        else:
                            ratio = 0.0
                        settings.size += size_offset
                        settings.size_y += size_offset * ratio
                    else:
                        light.shadow_soft_size += size_offset
                    self.initial_x = event.mouse_x
            
            elif self.mode == 'CONE' and light.type in {'SPOT','AREA'}:
                if event.type == 'MOUSEMOVE':
                    cone_offset = (event.mouse_x - self.initial_x)/200
                    if light.type == 'SPOT':
                        if preferences.use_physical_lights:
                            settings.spot_size += cone_offset
                        else:
                            light.spot_size += cone_offset
                    elif light.type == 'AREA':
                        light.spread += cone_offset
                    self.initial_x = event.mouse_x
                

        if event.type in {'G','W'} and event.value == 'PRESS':
            self.prev_lgt_loc = self.light_obj.location
            self.prev_tgt_loc = self.target_obj.location
            self.prev_lgt_rot = self.light_obj.rotation_euler
            self.prev_tgt_rot = self.target_obj.rotation_euler
            self.initial_x = event.mouse_x
            if self.mode != 'POSITION':
                self.mode = 'POSITION'

        if event.type == 'E' and event.value == 'PRESS':
            self.prev_lgt_loc = self.light_obj.location
            self.prev_lgt_rot = self.light_obj.rotation_euler
            self.initial_x = event.mouse_x
            if self.mode != 'ELEVATION':
                self.mode = 'ELEVATION'
        
        if event.type == 'R' and event.value == 'PRESS':
            self.prev_lgt_loc = self.light_obj.location
            self.prev_lgt_rot = self.light_obj.rotation_euler  
            self.initial_x = event.mouse_x
            if self.mode != 'ORBIT':
                self.mode = 'ORBIT'

        if event.type == 'D' and event.value == 'PRESS':
            self.prev_lgt_loc = self.light_obj.location
            self.prev_lgt_rot = self.light_obj.rotation_euler
            self.initial_x = event.mouse_x
            if self.mode != 'DISTANCE':
                self.mode = 'DISTANCE'

        if event.type == 'T' and event.value == 'PRESS':
            self.prev_tgt_loc = self.target_obj.location
            self.prev_tgt_rot = self.target_obj.rotation_euler
            self.initial_x = event.mouse_x
            if self.mode != 'TARGET':
                self.mode = 'TARGET'

        if event.type == 'I' and event.value == 'PRESS':
            if light_unit == 'energy':  
                self.prev_intensity = self.light_obj.data[light_unit]          
            else:
                self.prev_intensity = settings[light_unit]
            self.initial_x = event.mouse_x
            if self.mode != 'INTENSITY':
                self.mode = 'INTENSITY'
        
        if event.type == 'K' and event.value == 'PRESS':
            self.prev_temperature = settings.light_temperature
            self.initial_x = event.mouse_x
            if self.mode != 'TEMPERATURE':
                self.mode = 'TEMPERATURE'

        if light.type in  {'SPOT','AREA'}:
            if event.type == 'C' and event.value == 'PRESS':
                if light.type == 'SPOT':
                    self.prev_cone = light.spot_size
                elif light.type == 'AREA':
                    self.prev_cone = light.spread
                self.initial_x = event.mouse_x
                if self.mode != 'CONE':
                    self.mode = 'CONE'

        if event.type == 'S' and event.value == 'PRESS':
            if light.type == 'SUN':
                self.prev_size = light.angle
            elif light.type == 'AREA':
                self.prev_size = light.size
                self.prev_size_y = light.size_y
            else:
                self.prev_size = light.shadow_soft_size    
            self.initial_x = event.mouse_x
            if self.mode != 'SIZE':
                self.mode = 'SIZE'

        if event.type in {'SPACE', 'LEFTMOUSE'} and event.value == 'PRESS':
            self.initial_x = event.mouse_x
            if self.mode != 'PAUSE':
                self.mode = 'PAUSE'

        if event.type in {'RET', 'NUMPAD_ENTER', 'RIGHTMOUSE'}:
            if event.value == 'RELEASE':
                # Restore Mouse Cursor from EYEDROPPER Icon
                if self.cursor_set:
                    context.window.cursor_modal_restore()
                # Restore Focus Planes visibility
                for o in self.fp:
                    o.hide_viewport = False

                if object is not None and parent_target:
                    self.target_obj.parent = object
                
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'FINISHED'}

        # Cancel Modal with RightClick and ESC
        elif event.type in {'ESC', 'BACKSPACE'} and event.value == 'PRESS':
            if self.mode != 'PAUSE':
                # Restore Light Position only
                if self.mode in {'ELEVATION','DISTANCE','ORBIT'}:
                    self.light_obj.location = self.prev_lgt_loc
                    self.light_obj.rotation_euler = self.prev_lgt_rot
                    if self.prev_tgt_loc:
                        self.target_obj.location = self.prev_tgt_loc
                    if self.prev_tgt_rot:
                        self.target_obj.rotation_euler = self.prev_tgt_rot
                
                # Restore Light and Target Position
                elif self.mode == 'POSITION': 
                    self.light_obj.location = self.prev_lgt_loc
                    self.light_obj.rotation_euler = self.prev_lgt_rot
                    if self.prev_tgt_loc:
                        self.target_obj.location = self.prev_tgt_loc
                    if self.prev_tgt_rot:
                        self.target_obj.rotation_euler = self.prev_tgt_rot

                # Restore Target Position only
                elif self.mode == 'TARGET': 
                    if self.prev_tgt_loc:
                        self.target_obj.location = self.prev_tgt_loc
                    if self.prev_tgt_rot:
                        self.target_obj.rotation_euler = self.prev_tgt_rot

                # Restore Intensity
                elif self.mode == 'INTENSITY':    
                    if light_unit == 'energy':
                        setattr(self.light_obj.data, light_unit, self.prev_intensity)
                    else:
                        setattr(settings, light_unit, self.prev_intensity)
                
                # Restore Temperature
                elif self.mode == 'TEMPERATURE':
                    settings.light_temperature = self.prev_temperature
                    
                # Restore Size
                elif self.mode == 'SIZE':
                    if light.type == 'SUN':
                        light.angle = self.prev_size
                    elif light.type == 'AREA':
                        if preferences.use_physical_lights:
                            settings.size = self.prev_size
                            settings.size_y = self.prev_size_y
                        else:
                            light.size = self.prev_size
                            light.size_y = self.prev_size_y
                    else:
                        light.shadow_soft_size = self.prev_size         
                
                # Restore Cone 
                elif self.mode == 'CONE':
                    if light.type == 'SPOT':
                        if preferences.use_physical_lights:
                            settings.spot_size = self.prev_cone
                        else:
                            light.spot_size = self.prev_cone
                    elif light.type == 'AREA':
                        light.spread = self.prev_cone
                
                self.mode = 'PAUSE'

            else:
                if self.cursor_set:
                    context.window.cursor_modal_restore()
                # Restore Focus Planes visibility
                for o in self.fp:
                    o.hide_viewport = False
                for o in self.dof_objects:
                    o.hide_viewport = False

                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                
                # Restore location and rotations
                self.light_obj.location = self.stored_lgt_location
                self.target_obj.location = self.stored_tgt_location
                self.light_obj.rotation_euler = self.stored_lgt_rotation
                self.target_obj.rotation_euler = self.stored_tgt_rotation

                # Restore Intensity
                if light_unit == 'energy':
                    setattr(self.light_obj.data, light_unit, self.stored_intensity)
                else:
                    setattr(settings, light_unit, self.stored_intensity)

                # Restore Temperature
                settings.light_temperature = self.stored_temperature
                
                # Restore Size
                if light.type == 'SUN':
                    light.angle = self.stored_size
                elif light.type == 'AREA':
                    if preferences.use_physical_lights:
                        settings.size = self.stored_size
                        settings.size_y = self.stored_size_y
                    else:
                        light.size = self.stored_size
                        light.size_y = self.stored_size_y
                else:
                    light.shadow_soft_size = self.stored_size         

                # Restore Cone
                if light.type == 'SPOT':
                    if preferences.use_physical_lights:
                        settings.spot_size = self.stored_cone
                    else:
                        light.spot_size = self.stored_cone
                elif light.type == 'AREA':
                    light.spread = self.stored_cone

                self.light = ''
                return {'CANCELLED'}

    return {'RUNNING_MODAL'}

def light_modal_simple(self, context, event):

    # Allow navigation for Blender and Maya shortcuts
    if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.alt or event.alt and event.type == 'LEFTMOUSE' or event.alt and event.type == 'RIGHTMOUSE':
        return {'PASS_THROUGH'}

    self.mouse_region_x = event.mouse_region_x
    self.mouse_region_y = event.mouse_region_y

    if self.invert_direction:
        direction = '-Z'
    else:
        direction = 'Z'

    if event.type == 'WHEELUPMOUSE':
        self.distance += 0.2
    elif event.type == 'WHEELDOWNMOUSE':
        self.distance -= 0.2  

    elif event.type == 'I' and event.value == 'RELEASE':
        self.invert_direction = not self.invert_direction

    elif event.type == 'N' and event.value == 'RELEASE':
        self.follow_normals = not self.follow_normals

    result, location, object, normal = raycast(context, event, False, False, self.light_obj, coord=(self.mouse_region_x, self.mouse_region_y))
    
    if result:
        if object is not None:
            mw = object.matrix_world
            # Can't use face_index because it fails with Subdivision modifier
            # f = object.data.polygons[face_index]
            M = mw.normalized() @ normal.to_track_quat(direction, 'Y').to_matrix().to_4x4()
            self.light_obj.matrix_world = M
            self.light_obj.location = location + Vector(normal) * self.distance
            if not self.follow_normals:
                self.light_obj.rotation_euler = (0,0,0) 

    if event.type in {'LEFTMOUSE', 'ESC', 'BACKSPACE', 'RIGHTMOUSE'}:
        if event.value == 'RELEASE':
            # Restore Mouse Cursor from EYEDROPPER Icon
            if self.cursor_set:
                context.window.cursor_modal_restore()
            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False
            for o in self.dof_objects:
                 o.hide_viewport = False
            self.light = ''
            return {'FINISHED'}
    return {'RUNNING_MODAL'}

class LIGHTMIXER_OT_Add(bpy.types.Operator):
    bl_idname = "lightmixer.add"
    bl_label = "Add Light"
    bl_description = ("Create a light under your mouse cursor, Left-click to validate. \n"
                    "Hold Ctrl to create light on the Cursor. \n"
                    "Hold Alt key to create a light with a target and enter modal placement. \n"
                    "Hold Alt + Shift will parent the created target to the selected object"
                    )
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(
            name = "Light Type",
            items = [('POINT','Point',''),('AREA','Area',''),
                    ('SPOT','Spot',''), ('SUN','Sun','')],
    )

    light: bpy.props.StringProperty(default='')

    stored_lgt_location : bpy.props.FloatVectorProperty()
    stored_tgt_location : bpy.props.FloatVectorProperty()
    stored_lgt_rotation : bpy.props.FloatVectorProperty()
    stored_tgt_rotation : bpy.props.FloatVectorProperty()
    stored_intensity : bpy.props.FloatProperty()
    stored_temperature : bpy.props.IntProperty(default=6500)    
    stored_size : bpy.props.FloatProperty()
    stored_size_y : bpy.props.FloatProperty()
    stored_cone : bpy.props.FloatProperty()

    # Previous transform before entering Mode
    prev_lgt_loc : bpy.props.FloatVectorProperty()
    prev_tgt_loc : bpy.props.FloatVectorProperty()
    prev_lgt_rot : bpy.props.FloatVectorProperty()
    prev_tgt_rot : bpy.props.FloatVectorProperty()
    prev_intensity : bpy.props.FloatProperty()
    prev_temperature : bpy.props.IntProperty(default=6500)
    prev_size : bpy.props.FloatProperty()
    prev_size_y : bpy.props.FloatProperty()
    prev_cone : bpy.props.FloatProperty()

    add_target = False
    target_obj = None
    light_obj = None

    parent_target = False

    fp = []
    dof_objects = []

    mouse_region_x = None
    mouse_region_y = None

    initial_x = 0
    offset_x = 0

    transform_offset = None
    distance = 1.0
    target_distance = 0
    invert_direction = False
    follow_normals = True

    mode = MODAL_MODES

    def modal(self, context, event):
        if self.add_target:
            return light_modal(self,context,event,self.parent_target)
        else:
            return light_modal_simple(self,context,event)

    def invoke(self, context, event):

        self.add_target = event.alt
        self.parent_target = event.shift

        self.light_obj = create_light(context,self.type)
        if self.add_target:
            self.target_obj = create_light_target(context,self.light_obj,self.parent_target,True)

        # Enter Light Modal if adding a target
        if self.add_target:    
            self.mode = 'POSITION' 
            # Hide all Focus Planes
            self.fp = list_focus_planes()
            self.dof_objects = list_dof_objects()

            store_light_params(self,context)

            # Switch to object mode to create light
            if bpy.context.scene.collection.all_objects:
                if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')

            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            # Set Cursor to EYEDROPPER icon
            self.cursor_set = True
            context.window.cursor_modal_set('EYEDROPPER')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        elif not event.ctrl:
            # Hide all Focus Planes
            self.fp = list_focus_planes()
            self.dof_objects = list_dof_objects()

            # Set Cursor to EYEDROPPER icon
            self.cursor_set = True
            context.window.cursor_modal_set('EYEDROPPER')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            return {'FINISHED'}
        
class LIGHTMIXER_OT_Target_Add(bpy.types.Operator):
    bl_idname = "object.light_target_add"
    bl_label = "Add Light Target"
    bl_description = ("Enters Light Modal to create a target under your mouse cursor. \n"
                    "Right-Click to validate. \n"
                    )
    bl_options = {'REGISTER', 'UNDO'}

    # Storing transforms before entering the Modal Operator
    stored_lgt_location : bpy.props.FloatVectorProperty()
    stored_tgt_location : bpy.props.FloatVectorProperty()
    stored_lgt_rotation : bpy.props.FloatVectorProperty()
    stored_tgt_rotation : bpy.props.FloatVectorProperty()
    stored_intensity : bpy.props.FloatProperty()
    stored_temperature : bpy.props.IntProperty(default=6500)    
    stored_size : bpy.props.FloatProperty()
    stored_size_y : bpy.props.FloatProperty()
    stored_cone : bpy.props.FloatProperty()

    # Previous transform before entering Mode
    prev_lgt_loc : bpy.props.FloatVectorProperty()
    prev_tgt_loc : bpy.props.FloatVectorProperty()
    prev_lgt_rot : bpy.props.FloatVectorProperty()
    prev_tgt_rot : bpy.props.FloatVectorProperty()
    prev_intensity : bpy.props.FloatProperty()
    prev_temperature : bpy.props.IntProperty(default=6500)
    prev_size : bpy.props.FloatProperty()
    prev_size_y : bpy.props.FloatProperty()
    prev_cone : bpy.props.FloatProperty()

    target_obj = None
    light_obj = None

    parent_target = False

    fp = []
    dof_objects = []

    mouse_region_x = None
    mouse_region_y = None

    initial_x = 0
    offset_x = 0

    transform_offset = None
    distance = 0.0
    target_distance = 0

    mode = MODAL_MODES

    def modal(self, context, event):
        return light_modal(self,context,event,self.parent_target)

    def invoke(self, context, event):

        self.parent_target = event.shift
        
        if context.object.type == 'LIGHT':
            self.light_obj = context.object
        else:
            self.report({"ERROR"}, "Light not found, make sure to select a light first.")
            return {'CANCELLED'}
        
        self.target_obj = create_light_target(context,self.light_obj,self.parent_target)

        self.mode = 'TARGET' 
        # Hide all Focus Planes
        self.fp = list_focus_planes()
        self.dof_objects = list_dof_objects()

        store_light_params(self,context)

        # Switch to object mode to create light
        if bpy.context.scene.collection.all_objects:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        # Set Cursor to EYEDROPPER icon
        self.cursor_set = True
        context.window.cursor_modal_set('EYEDROPPER')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
class LIGHTMIXER_OT_LightModal(bpy.types.Operator):
    bl_idname = "object.light_modal"
    bl_label = "Light Modal"
    bl_description = " Enter modal that helps you positionning your light around its target"
    bl_options = {'REGISTER', 'UNDO'}

    # Storing transforms before entering the Modal Operator
    stored_lgt_location : bpy.props.FloatVectorProperty()
    stored_tgt_location : bpy.props.FloatVectorProperty()
    stored_lgt_rotation : bpy.props.FloatVectorProperty()
    stored_tgt_rotation : bpy.props.FloatVectorProperty()
    stored_intensity : bpy.props.FloatProperty()
    stored_temperature : bpy.props.IntProperty(default=6500)    
    stored_size : bpy.props.FloatProperty()
    stored_size_y : bpy.props.FloatProperty()
    stored_cone : bpy.props.FloatProperty()

    # Previous transform before entering Mode
    prev_lgt_loc : bpy.props.FloatVectorProperty()
    prev_tgt_loc : bpy.props.FloatVectorProperty()
    prev_lgt_rot : bpy.props.FloatVectorProperty()
    prev_tgt_rot : bpy.props.FloatVectorProperty()
    prev_intensity : bpy.props.FloatProperty()
    prev_temperature : bpy.props.IntProperty(default=6500)
    prev_size : bpy.props.FloatProperty()
    prev_size_y : bpy.props.FloatProperty()
    prev_cone : bpy.props.FloatProperty()

    target_obj = None
    light_obj = None

    fp = []
    dof_objects = []

    mouse_region_x = None
    mouse_region_y = None

    initial_x = 0
    offset_x = 0

    transform_offset = None
    distance = 1.0
    target_distance = 0
    invert_direction = False
    follow_normals = True

    mode = MODAL_MODES

    def modal(self, context, event):

        if self.target_obj:
            return light_modal(self,context,event)
        else:
            return light_modal_simple(self,context,event)

    def invoke(self, context, event):

        if context.object.type == 'LIGHT':
            self.light_obj = context.object
        else:
            self.report({"ERROR"}, "Light not found, make sure to select a light first.")
            return {'CANCELLED'}

        self.target_obj = get_target(self.light_obj.name)
        store_light_params(self,context)

        if self.target_obj:
            self.mode = 'PAUSE'
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        # Hide all Focus Planes
        self.fp = list_focus_planes()
        self.dof_objects = list_dof_objects()

        # Switch to object mode to create light
        if bpy.context.scene.collection.all_objects:
            if bpy.context.object and bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

        # Set Cursor to EYEDROPPER icon
        self.cursor_set = True
        context.window.cursor_modal_set('EYEDROPPER')

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}
   
class LIGHTMIXER_OT_Delete(bpy.types.Operator):
    bl_idname = "lightmixer.delete"
    bl_label = "Delete Light"
    bl_options = {'REGISTER', 'UNDO'}

    light: bpy.props.StringProperty()
    use_global: bpy.props.BoolProperty(
                default=False,
                name="Delete Global",
                description="Delete from all Scenes")
    @classmethod
    def description(self, context, event):
        return f'Shift-Click to delete "{event.light}" globally'

    def execute(self, context):
        scene = context.scene
        bpy.ops.photographer.target_delete(obj_name=self.light)

        light_obj = scene.objects.get(self.light)
        if light_obj:
            return bpy.ops.object.delete(
                {
                     "object" : None,
                     "selected_objects" : [light_obj]
                 },
                 use_global = self.use_global,
            )
        return {'CANCELLED'}

    def invoke(self, context, event):
        self.use_global = event.shift
        wm = context.window_manager
        if self.use_global:
            return wm.invoke_confirm(self, event)
        else:
            return self.execute(context)

class LIGHTMIXER_OT_Enable(bpy.types.Operator):
    bl_idname = "lightmixer.enable"
    bl_label = "Enable Light"
    bl_description = ("Shift-Click to Solo this light. \n"
                    "Ctrl-Click to enable/disable all linked lights")
    bl_options = {'UNDO'}

    light: bpy.props.StringProperty()
    linked: bpy.props.BoolProperty()
    shift: bpy.props.BoolProperty()
    alt: bpy.props.BoolProperty()

    def execute(self, context):
        light_objs = []
        light_obj = bpy.data.objects[self.light]

        if self.linked:
            for o in context.scene.collection.all_objects:
                if o.type == 'LIGHT' and o.data == light_obj.data:
                    light_objs.append(o)
        elif self.alt:
            # Find selected lights in Outliner
            areaOverride=bpy.context.area    
            if bpy.context.area.type!='OUTLINER':
                for area in bpy.context.screen.areas:
                    if area.type == 'OUTLINER':
                        areaOverride=area

            with bpy.context.temp_override(area=areaOverride):
                light_objs = [o for o in bpy.context.selected_ids if bpy.data.objects.get(o.name) and o.type=='LIGHT']
                if bpy.context.active_object.type == 'LIGHT' and bpy.context.active_object not in light_objs:
                    light_objs.append(bpy.context.active_object)

            if light_obj not in light_objs:
                light_objs = [light_obj]

        else:
            light_objs.append(light_obj)

        if self.shift:
            if context.scene.lightmixer.solo_active:
                solo_light=[o for o in context.scene.collection.all_objects if o.type=='LIGHT' and o.lightmixer.solo]
                emissive_mats=[mat for mat in bpy.data.materials if mat.get('is_emissive', False)]
                em_nodes = []
                for mat in emissive_mats:
                    nodes = mat.node_tree.nodes
                    for n in mat['em_nodes']:
                        em_nodes.append(nodes.get(n))

                solo_node = [n for n in em_nodes if n.lightmixer.solo]

                if solo_light:
                    if solo_light[0] == light_obj:
                        light_obj.lightmixer.solo = False
                    else:
                        solo_light[0].lightmixer.solo = False
                        light_obj.lightmixer.solo = True
                elif context.scene.world.solo:
                    context.scene.world.solo = False
                    light_obj.lightmixer.solo = True
                elif solo_node:
                    solo_node[0].lightmixer.solo = False
                    light_obj.lightmixer.solo = True
            else:
                light_obj.lightmixer.solo = not light_obj.lightmixer.solo

        else:
            for l in light_objs:
                if not context.scene.lightmixer.solo_active:
                    l.lightmixer.enabled = not l.lightmixer.enabled



        for l in light_objs:
            if l.lightmixer.enabled and not l.select_get():
                # Check for given object names
                bpy.data.objects[l.name].select_set(True)

        return{'FINISHED'}

    def invoke(self, context, event):
        self.linked = event.ctrl
        self.shift = event.shift
        self.alt = event.alt
        return self.execute(context)

class LIGHTMIXER_OT_RefreshHDRIPreview(bpy.types.Operator):
    bl_idname = "lightmixer.refresh_hdri_preview"
    bl_label = "World changed! Refresh Preview"
    bl_description = "HDRI preview is outdated as the World changed"

    def execute(self,context):
        # Update HDRI thumbnail
        if context.scene.world.get('hdri_category',''):
            hdri_category = context.scene.world['hdri_category']

        if context.scene.world.get('hdri_tex',''):
            hdri_tex = context.scene.world['hdri_tex']
        else:
            if get_environment_tex(context):
                hdri_tex = get_environment_tex(context)[0].image.filepath

        try:
            context.scene.lightmixer.hdri_category = hdri_category
            context.scene.lightmixer.hdri_tex = hdri_tex
            return {'FINISHED'}
        except:
            print ("Did not update HDRI preview as it was not found")
            return {'CANCELLED'}
