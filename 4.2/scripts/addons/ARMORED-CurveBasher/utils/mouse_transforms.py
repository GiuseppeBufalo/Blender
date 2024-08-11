import bpy

from math import radians, degrees
from mathutils import Matrix
from random import random, uniform, seed

from .. utils import addon
from .. utils import objects
from .. utils import transforms


def modal_scale(self, context, delta):

    for i, curve in enumerate(self.selection):
        ob = objects.retrieve(context, curve.get('geo'))

        if ob is not None:
            cap1 = objects.find(ob.get('cap1'))
            cap2 = objects.find(ob.get('cap2'))

        mode  = curve['mode']
        index = curve['index']

        scale = self.start_scale[i] + self.end_rand_scale[i] + delta * self.scale_speed
        scale = abs(scale)  # Positive scale works better with some modifiers.

        if self.randomize_scale:
            if not self.randomize_seed:
                seed(i)
            
            min = self.start_rand_scale[i]
            max = scale
            scale = uniform(min, max)
        
        if mode == 1 and index == -1:
            curve.data.bevel_depth = scale

        elif mode == 2:
            if scale == 0:      # SAFETY CHECK
                scale = .001
                
            if ob is None: 
                continue

            ob.data.uniform_scale = scale
            if cap1 and cap2:
                cap1.data.uniform_scale = scale
                cap2.data.uniform_scale = scale
            
        elif mode in {1, 3}:
            if ob is None: 
                continue

            ob.uniform_scale = scale


def modal_rotate(self, context, delta):

    for i, curve in enumerate(self.selection):
        index = curve['index']
        mode  = curve['mode']

        if mode == 1 and index == -1:
            continue

        rotation = self.start_rotation[i] + self.end_rand_rotation[i] + delta * self.rotate_speed

        if self.randomize_rotation:
            if not self.randomize_seed:
                seed(i)

            min = self.start_rand_rotation[i]
            max = rotation
            rotation = uniform(min, max)

        ob = objects.retrieve(context, curve.get('geo'))
        if not ob:
            continue
        
        elif mode == 1:
            ob.profile_rot = radians(rotation)
        else:
            ob.rotation_euler.z = radians(rotation)
        

def modal_twist_curve(self, context, delta, reverse=False):

    for i, curve in enumerate(self.selection):
        # mode  = curve['mode']
        index = curve['index']

        def twist_points():
            val = self.start_twist[i] + delta * self.twist_speed
            point.tilt = index * (val / ( len( self.curve_points[i] ) -1 )) + self.twist_offset[i]
        
        if reverse:
            for index, point in enumerate(reversed(self.curve_points[i])):
                twist_points()
            
        else:
            for index, point in enumerate(self.curve_points[i]):
                twist_points()


def slide_along_curve(self, context, curve, delta):

    for i, curve in enumerate(self.selection):
        ob = objects.retrieve(context, curve.get('geo'))
        mode  = curve['mode']
        index = curve['index']

        # curve_len = curve.data.splines[0].calc_length()

        slide = self.start_slide[i] + delta * self.slide_speed

        if mode == 1 and index == -1:
            continue

        elif mode == 1:
            continue

        elif mode == 2:
            ob.array_center = slide

        elif mode == 3:
            ob.location.z = slide