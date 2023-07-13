import bpy

from math import radians, degrees
from mathutils import Matrix

from .. utils import addon
from .. utils import objects
from .. utils import transforms


def alt_press_events(self, context, event):
    # ALT press activates an alternate transformation mode.
    # Any per-mode initialization is done here.

    if self.press_alt:  # Exit if ALT is already pressed.
        return
    
    if self.scaling:
        self.randomize_scale = True
        self.transform_name = 'Rand Scale'

        for i, curve in enumerate(self.selection):
            key = curve.name
            ob = objects.retrieve(context, curve.get('geo'))

            index = curve['index']
            mode  = curve['mode']
            
            if mode == 1 and index == -1:
                self.start_rand_scale[i] = curve.data.bevel_depth
            
            elif mode == 2:
                self.start_rand_scale[i] = ob.data.uniform_scale
            
            elif mode in {1, 3}:
                self.start_rand_scale[i] = ob.uniform_scale

        
        # self.start_mouse_x = event.mouse_x

    elif self.rotating:
        self.randomize_rotation = True
        self.transform_name = 'Rand Rotate'

        for i, curve in enumerate(self.selection):
            index = curve['index']
            mode  = curve['mode']
            
            if mode == 1 and index == -1:
                continue
            
            ob = objects.retrieve(context, curve.get('geo'))
            if not ob:
                continue

            elif mode == 1:
                self.start_rand_rotation[i] = degrees(ob.profile_rot)
            else:
                self.start_rand_rotation[i] = degrees(ob.rotation_euler.z)

    elif self.twisting:
        update_twist(self, context, event, reverse=True)

    self.press_alt = True

    if addon.debug():
        print('ALT mode Enabled')


def alt_release_events(self, context, event):
    # Disables any active ALT transformation mode.

    if not self.press_alt:
        return
    
    if self.scaling:

        self.randomize_scale = False
        self.randomize_seed = False
        self.transform_name = 'Scale'

        for i, curve in enumerate(self.selection):
            key = curve.name
            ob = objects.retrieve(context, curve.get('geo'))

            index = curve['index']
            mode  = curve['mode']

            delta = event.mouse_x - self.start_mouse_x

            if mode == 1 and index == -1:
                self.end_rand_scale[i] = curve.data.bevel_depth - self.start_scale[i] - delta * self.scale_speed
            
            elif mode == 2:
                self.end_rand_scale[i] =  ob.data.uniform_scale - self.start_scale[i] - delta * self.scale_speed
            
            elif mode in {1, 3}:
                self.end_rand_scale[i] = ob.uniform_scale - self.start_scale[i] - delta * self.scale_speed
        
    elif self.rotating:

        self.randomize_rotation = False
        self.randomize_seed = False
        self.transform_name = 'Rotate'

        for i, curve in enumerate(self.selection):
            index = curve['index']
            mode  = curve['mode']

            delta = event.mouse_x - self.start_mouse_x

            if mode == 1 and index == -1:
                continue
            
            ob = objects.retrieve(context, curve.get('geo'))
            if not ob:
                continue

            elif mode == 1:
                self.end_rand_rotation[i] = degrees(ob.profile_rot) -  self.start_rotation[i] - delta * self.rotate_speed
            else:
                self.end_rand_rotation[i] = degrees(ob.rotation_euler.z) -  self.start_rotation[i] - delta * self.rotate_speed

    elif self.twisting:
        update_twist(self, context, event)

    self.press_alt = False

    if addon.debug():
        print('ALT mode Disabled')


def shift_press_events(self, context, event):
    # SHIFT press activates an alternate transformation mode.
    # Any per-mode initialization is done here.
    
    if self.press_shift:
        return

    if self.scaling:
    
        if self.randomize_scale:
            self.randomize_seed = True
            self.transform_name = 'Ultra Rand'

    elif self.rotating:

        if self.randomize_rotation:
            self.randomize_seed = True
            self.transform_name = 'Ultra Rand'

    self.press_shift = True


    if addon.debug():
        print('SHIFT mode Enabled')


def shift_release_events(self, context, event):
    # Disables any active SHIFT transformation mode.
    
    if not self.press_shift:
        return

    if self.scaling:
    
        if self.randomize_scale:
            self.randomize_seed = False
            self.transform_name = 'Rand Scale'

        else:
            self.transform_name = 'Scale'
    
    elif self.rotating:

        if self.randomize_rotation:
            self.randomize_seed = False
            self.transform_name = 'Rand Rotate'

        else:
            self.transform_name = 'Rotate'

    self.press_shift = False

    if addon.debug():
        print('SHIFT mode Disabled')
    
    
def update_twist(self, context, event, reverse=False):
    # Reversing the twist operation on ALT press requires some setup.

    self.start_mouse_x = event.mouse_x

    if reverse:

        for i, curve in enumerate(self.selection):
            self.twist_offset[i] = self.curve_points[i][-1].tilt
            self.start_twist[i] = (self.curve_points[i][-1].tilt - self.curve_points[i][0].tilt) * -1

    else:

        for i, curve in enumerate(self.selection):
            self.twist_offset[i] = self.curve_points[i][0].tilt
            self.start_twist[i] = self.curve_points[i][-1].tilt - self.curve_points[i][0].tilt


def set_curve_resolution(self, context, curve, increment=2):
    curve.data.resolution_u += increment
    self.curve_divisions = curve.data.resolution_u


def set_curve_sides(self, context, curve, increment=1):
    # 2 Sides are added for every increment (recommend keeping at 1).
    curve.data.bevel_resolution += increment
    self.curve_sides = curve.data.bevel_resolution


def set_array_count(self, context, curve, i, increment=1):
    ob = objects.retrieve(context, curve.get('geo'))
    if not ob:
        return

    array = ob.modifiers.get('CB Array')

    if not array:
        return

    if array.fit_type == 'FIT_CURVE':
        array.count = ob.array_fit_count

        # transforms.center_along_curve(context, curve)
        # transforms.update_start_values(self, context, curve, i)

    array.fit_type = 'FIXED_COUNT'
    array.count += increment

    # if curve.name == self.master_curve.name:
    #     self.array_type = array.fit_type
    #     self.array_count = array.count



    # context.view_layer.update()