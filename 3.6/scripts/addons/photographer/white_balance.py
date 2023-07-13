import bpy, bgl, math, gpu
from bpy.app.handlers import persistent
from .functions import srgb_to_linear,linear_to_srgb, InterpolatedArray, rgb_to_luminance, read_pixel_color
from .autofocus import list_focus_planes

# Default variables
default_color_temperature = 6500
default_tint = 0

# Creating Color Temperature to sRGB look up tables (CIE 1964 10 degree CMFs)
# from http://www.vendian.org/mncharity/dir3/blackbody/UnstableURLs/bbr_color.html
# Using 6500 as default white: purposefully changed 255,249,251 to 255,255,255
color_temperature_red = ((1000,255),(1200,255),(1400,255),(1600,255),(1800,255),
                        (2000, 255),(2200,255),(2400,255),(2700,255),(3000,255),
                        (3300,255),(3600,255),(3900,255),(4300,255),
                        (5000,255),(6000,255),(6500, 255),(7000,245),(8000,227),
                        (9000,214),(10000,204),(11000,196),(12000,191),(13000,120),
                        (14000, 30))
color_temperature_green = ((1000,56),(1200,83),(1400,101),(1600,115),(1800,126),
                        (2000,137),(2200,147),(2400,157),(2700,169),(3000,180),
                        (3300,190),(3600,199),(3900,206),(4300,219),(5000,228),
                        (6000,243),(6500, 255),(7000,243),(8000,233),(9000,225),
                        (10000,219),(11000,215),(12000,211),(13000,200),(14000, 100))
color_temperature_blue = ((1000,1),(1200,1),(1400,1),(1600,1),(1800,1),(2000,18),
                        (2200,44),(2400,63),(2700,87),(3000,107),(3300,126),
                        (3600,143),(3900,159),(4300,175),(5000,206),(6000,239),
                        (6500, 255),(7000,255),(8000,255),(9000,255),(10000,255),
                        (11000,255),(12000,255),(13000,255),(14000,255))


#White Balance functions #############################################################


# Not used, but keeping it as an alternative to convert K to RGB
def convert_K_to_RGB(color_temperature):

    """
    Converts from K to RGB, algorithm courtesy of 
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    """
    #range check
    if color_temperature < 1000: 
        color_temperature = 1000
    elif color_temperature > 40000:
        color_temperature = 40000
    
    tmp_internal = color_temperature / 100.0
    
    # red 
    if tmp_internal <= 66:
        red = 255
    else:
        tmp_red = 329.698727446 * math.pow(tmp_internal - 60, -0.1332047592)
        if tmp_red < 0:
            red = 0
        elif tmp_red > 255:
            red = 255
        else:
            red = tmp_red
    
    # green
    if tmp_internal <=66:
        tmp_green = 99.4708025861 * math.log(tmp_internal) - 161.1195681661
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    else:
        tmp_green = 288.1221695283 * math.pow(tmp_internal - 60, -0.0755148492)
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    
    # blue
    if tmp_internal >=66:
        blue = 255
    elif tmp_internal <= 19:
        blue = 0
    else:
        tmp_blue = 138.5177312231 * math.log(tmp_internal - 10) - 305.0447927307
        if tmp_blue < 0:
            blue = 0
        elif tmp_blue > 255:
            blue = 255
        else:
            blue = tmp_blue

    red = srgb_to_linear(red)
    green = srgb_to_linear(green)
    blue = srgb_to_linear(blue)
    
    return (red / 255, green / 255, blue / 255)

# Not used, but keeping it as an alternative to convert RGB to CCT Correlated Color Temperature
# Only holds true within a certain distance of the Planckian locus
def convert_RGB_to_CCT(rgb):
    R,G,B = rgb

    # Math below is assuming sRGB encoded values
    R = linear_to_srgb(R)
    G = linear_to_srgb(G)
    B = linear_to_srgb(B)

    # Convert RGB to XYZ
    X = 0.4124*R + 0.3576*G + 0.1805*B
    Y = 0.2126*R + 0.7152*G + 0.0722*B
    Z = 0.0193*R + 0.1192*G + 0.9505*B

    # Normalize to CIE 1931 xy
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)

    # CCT -- https://dsp.stackexchange.com/questions/8949/how-to-calculate-the-color-temperature-tint-of-the-colors-in-an-image
    n = (x-0.3320)/(0.1858-y)
    CCT = 449 * math.pow(n,3) + 3525 * math.pow(n,2) + 6823.3 * n + 5520.33

    # CCT -- Another formula, McCamy's approx? https://www.waveformlighting.com/tech/calculate-color-temperature-cct-from-cie-1931-xy-coordinates
    # CCT = 437 * math.pow(n,3) + 3601 * math.pow(n,2) + 6861 * n + 5517

    return CCT


def temp_ratio_table(red_temp, blue_temp):
    return (float(red_temp[1]) / blue_temp[1], red_temp[0])

def convert_temperature_to_RGB_table(color_temperature):

    # Interpolate Tables
    table_red = InterpolatedArray(color_temperature_red)
    table_green = InterpolatedArray(color_temperature_green)
    table_blue = InterpolatedArray(color_temperature_blue)

    # Convert Temperature to RGB using the look up tables
    red = table_red[color_temperature]
    green = table_green[color_temperature]
    blue = table_blue[color_temperature]

    return (red / 255, green / 255, blue / 255)

def convert_RGB_to_temperature_table(rgb):
    # Convert Color Temp from sRGB to linear
    color_temp_red = []
    color_temp_blue = []
    for x in color_temperature_red:
        y = [x[0], srgb_to_linear(float(x[1])/255.0)]
        color_temp_red.append(y)
    for x in color_temperature_blue:
        y = [x[0], srgb_to_linear(float(x[1])/255.0)]
        color_temp_blue.append(y)

    # Convert Table to Red/Blue ratio    
    temperature_ratio = list(map(temp_ratio_table, color_temp_red, color_temp_blue))
    table_ratio = InterpolatedArray(temperature_ratio)

    # Min and Max ratios from the table
    maxratio = temperature_ratio[0][0]
    minratio = temperature_ratio[-1][0]

    # rgb = [linear_to_srgb(x) for x in rgb]
    R,G,B = rgb

    # Make sure to not divide by 0
    if B == 0:
        ratio = minratio
    else: 
        ratio = R / B

    #Clamping ratio to avoid looking outside of the table
    ratio = maxratio if ratio > maxratio else minratio if ratio < minratio else ratio

    color_temperature = table_ratio[ratio]

    return (color_temperature)

def convert_RBG_to_whitebalance(picked_color,use_scene_camera):
    if use_scene_camera:
        settings = bpy.context.scene.camera.data.photographer
    else:
        settings = bpy.context.camera.photographer

    # glReadPixels returns raw linear pixel values
    red, green, blue = picked_color

    average = rgb_to_luminance(picked_color)

    if average != 0:

        # Calculating Curves white level values
        curve_mult = [x / average for x in picked_color]

        # Accurate multiplier to test accuracy of color temperature conversion
        bpy.context.scene.view_settings.curve_mapping.white_level = curve_mult

        # Convert Curve value to Temperature
        settings.color_temperature = int(convert_RGB_to_temperature_table(curve_mult))

        # Make sure that Green is the same as Red after conversion to Color Temperature
        target = red / bpy.context.scene.view_settings.curve_mapping.white_level[0]
        green_mult = green / target

        # Convert Curve value to Tint
        if green_mult < 1 :
            settings.tint = int((green_mult - 1) * 200) # Reverse Tint Math
        else:
            settings.tint = int((green_mult - 1) * 50) # Reverse Tint Math



class PHOTOGRAPHER_OT_WBReset(bpy.types.Operator):
    bl_idname = "white_balance.reset"
    bl_label = "Reset White Balance"
    bl_description = "Reset White Balance"
    bl_options = {'UNDO'}

    use_scene_camera: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        if self.use_scene_camera:
            settings = context.scene.camera.data.photographer
        else:
            settings = context.camera.photographer

        settings.color_temperature = default_color_temperature
        settings.tint = default_tint
        settings.wb_color = (0.5,0.5,0.5)

        return{'FINISHED'}

def white_balance_picker(self,context):
    x,y = self.mouse_region_x, self.mouse_region_y

    area = context.area
    if area.type=='VIEW_3D':

        red = 0
        green = 0
        blue = 0

        if bpy.app.version >= (3,2,2):
            # get currently bound framebuffer
            buffer = gpu.state.active_framebuffer_get()
        else:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
            buffer = bgl.Buffer(bgl.GL_FLOAT, 3)

        for i in range(x-4, x+5):
            for j in range(y-4, y+5):
                value = read_pixel_color(i,j,buffer)
                red += value[0]
                green += value[1]
                blue += value[2]

        average_r = red / 81
        average_g = green / 81
        average_b = blue / 81

        picked_average = [average_r,average_g,average_b]

        # Clear Buffer
        del buffer

        if picked_average != [0.0,0.0,0.0]:
            convert_RBG_to_whitebalance(picked_average,self.use_scene_camera)

class PHOTOGRAPHER_OT_WBPicker(bpy.types.Operator):
    bl_idname = "white_balance.picker"
    bl_label = "Pick White Balance"
    bl_description = "Pick a grey area in the 3D view to adjust the White Balance.\nShift + Click to reset"
    bl_options = {'REGISTER', 'UNDO'}

    use_scene_camera: bpy.props.BoolProperty(default=False)
    mouse_region_x: bpy.props.IntProperty(default=0)
    mouse_region_y: bpy.props.IntProperty(default=0)

    def modal(self, context, event):
        if self.use_scene_camera:
            settings = context.scene.camera.data.photographer
        else:
            settings = context.camera.photographer

        context.area.tag_redraw()

        self.mouse_region_x = event.mouse_region_x
        self.mouse_region_y = event.mouse_region_y

        # Allow navigation for Blender and Maya shortcuts
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} or event.alt and event.type == 'LEFTMOUSE' or event.alt and event.type == 'RIGHTMOUSE':
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if context.area.type=='VIEW_3D':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            # Restore Mouse Cursor from EYEDROPPER Icon
            if self.cursor_set:
                context.window.cursor_modal_restore()

            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if context.area.type=='VIEW_3D':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            # Restore previous state
            context.scene.view_settings.use_curve_mapping = self.stored_use_curve_mapping
            settings.color_temperature = self.stored_color_temperature
            settings.tint = self.stored_tint

            # Restore Focus Planes visibility
            for o in self.fp:
                o.hide_viewport = False

            # Restore Mouse Cursor from EYEDROPPER Icon
            if self.cursor_set:
                context.window.cursor_modal_restore()

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        if event.shift == True:
            bpy.ops.white_balance.reset(use_scene_camera=True)
            return {'FINISHED'}

        else:
            if context.area.type=='VIEW_3D':
                if self.use_scene_camera:
                    settings = context.scene.camera.data.photographer
                else:
                    settings = context.camera.photographer

                # Store state
                self.stored_use_curve_mapping = context.scene.view_settings.use_curve_mapping
                self.stored_color_temperature = settings.color_temperature
                self.stored_tint = settings.tint

                self.fp = list_focus_planes()

                if not context.scene.view_settings.use_curve_mapping:
                    context.scene.view_settings.use_curve_mapping = True

                args = (self, context)
                self._handle = bpy.types.SpaceView3D.draw_handler_add(white_balance_picker, args, 'WINDOW', 'PRE_VIEW')

                # Set Cursor to EYEDROPPER icon
                self.cursor_set = True
                context.window.cursor_modal_set('EYEDROPPER')

                context.window_manager.modal_handler_add(self)

                return {'RUNNING_MODAL'}
            else:
                self.report({'WARNING'}, "No 3D view found")
                return {'CANCELLED'}
