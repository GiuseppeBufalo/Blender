# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# (c) 2022 Jakub Uhlik

import numpy as np
import bpy
from bpy.props import PointerProperty, BoolProperty, StringProperty, FloatProperty, IntProperty, FloatVectorProperty, EnumProperty, CollectionProperty, IntVectorProperty
from bpy.types import PropertyGroup
from .. resources.translate import translate


# TODO: all prop groups to: `SCATTER5_PR_...` naming scheme


class SCATTER5_PR_manual_brush_tool_common(PropertyGroup, ):
    # ------------------------------------------------------------------ ui >>>
    _tool = None
    _location = None
    _rotation = None
    _scale = None
    _settings = None
    # NOTE: override in 2d tools to '2D' so proper radius prop (radius_2d) is drawn, it is not used for anything else yet. Eraser with both modes is exception, handled differently. manipulator is 2d, but does not use any radius, so don't bother with it..
    _domain = '3D'
    # ------------------------------------------------------------------ ui <<<
    # ------------------------------------------------------------------ sync >>>
    _sync = None
    # ------------------------------------------------------------------ sync <<<
    
    # ------------------------------------------------------------------ stroke >>>
    # radius in world coordinates. fixed widget tools have always 1.0
    radius: FloatProperty(name=translate("Radius"), default=1.0, min=0.001, soft_max=3.0, precision=3, subtype='FACTOR', description=translate("Tool active radius"), )
    radius_px: FloatProperty(name=translate("Radius"), default=50.0, min=1.0, soft_max=300.0, precision=0, subtype='PIXEL', description=translate("Tool active radius"), )
    radius_units: EnumProperty(name=translate("Units"), default='SCENE', items=[
        ('SCENE', translate("Scene"), "Radius relative to scene", ),
        ('VIEW', translate("View"), "Radius relative to view", ),
    ], description=translate("Radius units"), )
    # NOTE: tool logic got to select right one, and sadly, ui logic as well..
    radius_2d: FloatProperty(name=translate("Radius"), default=50.0, min=1.0, soft_max=300.0, precision=0, subtype='PIXEL', description=translate("Tool active radius"), )
    # radius controlled by stylus pressure, do not draw in ui if not available
    radius_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    # timer interval for timer brushes
    interval: FloatProperty(name=translate("Interval"), default=0.1, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate("Tool action interval in seconds"), )
    # some brushes can draw on timer or on mouse move or both. if brush is not timer based it will not care what is set here
    draw_on: EnumProperty(name=translate("Draw On"), default='BOTH', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    
    # TODO: falloff also controlled by pressure? could be.. but it would be total mess with radius + pressure + fallof + pressure. not sure how to deal with it in some calculations
    
    # at 0, effect is scaled from brush center, at 1, effect is the same on whole area
    falloff: FloatProperty(name=translate("Falloff"), default=0.5, min=0.0, max=1.0, precision=3, subtype='FACTOR', description=translate("Linear gradation of tool effect in Falloff to Radius area"), )
    # controls probability of selected point outside of falloff if uses boolean selection mask, if weighted mask is used it have no effect
    affect: FloatProperty(name=translate("Probability"), default=0.25, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate("Probability of tool effect in Falloff to Radius area when tool cannot be applied gradually"), )
    affect_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    # use normal interpolation by averaging neighbouring faces normals within radius * normal_interpolation_radius_factor
    use_normal_interpolation: BoolProperty(name=translate("Normal Interpolation"), default=False, description=translate("Interpolate surface normals under tool Radius"), )
    # portion of radius used for interpolation
    normal_interpolation_radius_factor: FloatProperty(name=translate("Radius"), default=0.5, min=0.0, max=1.0, precision=3, subtype='FACTOR', description=translate("Portion of tool Radius used to interpolate normals. Tools without Radius use 1.0 in world units"), )
    # interpolate mouse movement direction both 3d and 2d
    use_direction_interpolation: BoolProperty(name=translate("Direction Interpolation"), default=False, description=translate("Interpolate mouse pointer movement direction"), )
    # use n steps to history, 0 is no interpolation, current is taken
    direction_interpolation_steps: IntProperty(name=translate("Steps"), default=10, min=0, max=50, description=translate("Number od steps in history movement used to interpolate direction vector"), subtype='FACTOR', )
    # ------------------------------------------------------------------ stroke <<<
    
    # ------------------------------------------------------------------ instance >>>
    instance_index: IntProperty(name=translate("Instance Index"), default=0, min=0, max=99, description=translate("Tweak > Instancing > Manual index"), )
    
    rotation_align: EnumProperty(name=translate("Align Z"), default='SURFACE_NORMAL', items=[
        ('SURFACE_NORMAL', translate("Toward Mesh Normals"), "", "NORMALS_FACE", 1),
        ('LOCAL_Z_AXIS', translate("Toward Local Z"), "", "ORIENTATION_LOCAL", 32),
        ('GLOBAL_Z_AXIS', translate("Toward Global Z"), "", "WORLD", 3),
    ], description=translate("Instance Z axis direction"), )
    use_rotation_align_tilt_override: BoolProperty(name=translate("Use Stylus Tilt"), default=False, description=translate("Use stylus tilt to override Align Z property. Z axis is tilted in screen space accoring to stylus tilt, then transformed back to world space. Will not work if no tablet is present or tablet does not support stylus tilt info"), )
    rotation_up: EnumProperty(name=translate("Align Y"), default='GLOBAL_Y_AXIS', items=[
        ('GLOBAL_Y_AXIS', translate("Toward Global Y"), "", "WORLD", 2),
        ('LOCAL_Y_AXIS', translate("Toward Local Y"), "", "ORIENTATION_LOCAL", 1),
    ], description=translate("Instance Y axis direction"), )
    rotation_base: FloatVectorProperty(name=translate("Rotation Values"), default=(0.0, 0.0, 0.0, ), precision=3, subtype='EULER', size=3, description=translate("Base instance rotation"), )
    rotation_random: FloatVectorProperty(name=translate("Random Addition"), default=(0.0, 0.0, 0.0, ), precision=3, subtype='EULER', size=3, description=translate("Randomized instance rotation added on top of base rotation"), )
    
    scale_default: FloatVectorProperty(name=translate("Default Scale"), default=(1.0, 1.0, 1.0, ), precision=3, subtype='XYZ', size=3, description=translate("Default instance scale"), )
    scale_default_use_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    scale_random_factor: FloatVectorProperty(name=translate("Random Factor"), default=(1.0, 1.0, 1.0, ), precision=3, subtype='XYZ', size=3, description=translate("Random instance scale on top of default scale"), )
    scale_random_type: EnumProperty(name=translate("Randomization Type"), default='UNIFORM', items=[
        ('UNIFORM', translate("Uniform"), "", ),
        ('VECTORIAL', translate("Vectorial"), "", ),
    ], description=translate("Scale randomization type"), )
    # ------------------------------------------------------------------ instance <<<
    
    # ------------------------------------------------------------------ common >>>
    
    # NOTE: put the most used tool specific ("unique") props here..
    # DONE: axis (is in modify mixin, even used by two tools only, but might be handy in future)
    # DONE: align (a few tools uses something similar)
    # DONE: some sort of length/distance? + its pressure flag, quite a few of tools use that, with different names
    # DONE: some sort of strength 0-1 float + its pressure flag
    # DONE: use_minimal_distance, minimal_distance, minimal_distance_pressure
    
    effect_axis: EnumProperty(name=translate("Axis"), default='SURFACE_NORMAL', items=[
        ('SURFACE_NORMAL', translate("Mesh Normal"), "", "NORMALS_FACE", 1, ),
        ('LOCAL_Z_AXIS', translate("Surface Local Z"), "", "ORIENTATION_LOCAL", 2, ),
        ('GLOBAL_Z_AXIS', translate("Global Z"), "", "WORLD", 3, ),
        ('PARTICLE_Z', translate("Instance Z"), "", "SNAP_NORMAL", 4, ),
    ], description=translate("Tool effect axis"), )
    use_align_y_to_stroke: BoolProperty(name=translate("Align Y to Stroke Direction"), default=False, description=translate("Align instance Y axis to mouse movement direction"), )
    use_align_z_to_surface: BoolProperty(name=translate("Align Z To Surface Normal"), default=True, description=translate("Align instance Z axis to closest surface normal"), )
    
    strength: FloatProperty(name=translate("Strength"), default=1.0, min=0.0, max=1.0, precision=3, subtype='FACTOR', description=translate("Effect strength"), )
    strength_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    
    use_minimal_distance: BoolProperty(name=translate("Use Minimal Distance"), default=False, description=translate("Use minimal distance"), )
    minimal_distance: FloatProperty(name=translate("Points Minimal Distance"), default=0.25, min=0.0, precision=3, subtype='DISTANCE', description=translate("Minimal distance to other points"), )
    minimal_distance_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    
    distance: FloatProperty(name=translate("Distance"), default=1.0, min=0.00001, max=100.0, precision=5, subtype='DISTANCE', description=translate("Distance from previous point"), )
    distance_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    divergence: FloatProperty(name=translate("Divergence Distance"), default=0.0, min=0.0, max=100.0, precision=5, subtype='DISTANCE', description=translate("Randomize point location"), )
    divergence_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    
    # ------------------------------------------------------------------ common <<<


# DONE: radius + radius_pressure always first, on all tools. or even better, two columns, one is brush "shape" and second is strength and other stuff. so i got "header" always the same?
# DONE: use `_tool`, `_rotation`, `_scale` and `_effect` lists as ui drawing order? not it is for better memory what is used and what is not. but it could be also for auto drawing? if i group prop and prop_pressure into tuples, it could mark it as prop and bool pressure row. then each other have it own row and leave the rest as default. it have some exceptions. but it is worth to try.
# DONE: add `_location` or `_translation` category?
# DONE: move direction interpolation and normal interpolation to rotation menu


class SCATTER5_PR_manual_brush_tool_default(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    # NOTE: overrides:
    # NOTE: unique:
    pass


class SCATTER5_PR_manual_brush_tool_dot(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _rotation = [{'OVERRIDE': ('rotation_align', 'use_rotation_align_tilt_override', ), }, 'rotation_up', 'rotation_base', 'rotation_random',
                 ('use_normal_interpolation', 'normal_interpolation_radius_factor', ), ]
    _scale = ['scale_default', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('rotation_align', 'use_rotation_align_tilt_override', 'rotation_up', 'rotation_base', 'rotation_random',
             'use_normal_interpolation', 'normal_interpolation_radius_factor',
             'scale_default', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_spatter(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = ['interval', 'draw_on', ]
    _location = [('divergence', 'divergence_pressure', ), ]
    _rotation = [{'OVERRIDE': ('rotation_align', 'use_rotation_align_tilt_override', ), }, 'rotation_up', 'use_align_y_to_stroke', 'rotation_base', 'rotation_random',
                 ('use_normal_interpolation', 'normal_interpolation_radius_factor', ),
                 ('use_direction_interpolation', 'direction_interpolation_steps', ), ]
    _scale = ['scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('divergence', 'divergence_pressure',
             'rotation_align', 'use_rotation_align_tilt_override', 'rotation_up', 'use_align_y_to_stroke', 'rotation_base', 'rotation_random',
             'use_normal_interpolation', 'normal_interpolation_radius_factor',
             'use_direction_interpolation', 'direction_interpolation_steps',
             'scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    divergence: FloatProperty(name=translate("Divergence Distance"), default=0.333, min=0.0, max=100.0, precision=5, subtype='DISTANCE', description=translate("Randomize point location"), )
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_pose(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _rotation = ['rotation_align', ('use_normal_interpolation', 'normal_interpolation_radius_factor', ), ]
    _scale = ['scale_default', 'scale_multiplier', ]
    # NOTE: sync:
    _sync = ('rotation_align',
             'use_normal_interpolation', 'normal_interpolation_radius_factor', )
    # NOTE: overrides:
    scale_default: FloatVectorProperty(name=translate("Initial Scale"), default=(0.3, 0.3, 0.3, ), precision=3, subtype='XYZ', size=3, description=translate("Initial instance scale"), )
    # NOTE: unique:
    scale_multiplier: FloatProperty(name=translate("Scale Multiplier"), default=0.1, min=0.001, soft_max=1.0, precision=3, subtype='FACTOR', description=translate("Factor of scale added with mouse distance from origin"), )


class SCATTER5_PR_manual_brush_tool_path(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _location = [('distance', 'distance_pressure', ), ('divergence', 'divergence_pressure', ), ]
    _rotation = [{'OVERRIDE': ('rotation_align', 'use_rotation_align_tilt_override', ), }, 'rotation_up', 'use_align_y_to_stroke', 'rotation_base', 'rotation_random',
                 ('use_normal_interpolation', 'normal_interpolation_radius_factor', ),
                 ('use_direction_interpolation', 'direction_interpolation_steps', ), ]
    _scale = ['scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('distance', 'distance_pressure', 'divergence', 'divergence_pressure',
             'rotation_align', 'use_rotation_align_tilt_override', 'rotation_up', 'use_align_y_to_stroke', 'rotation_base', 'rotation_random',
             'use_normal_interpolation', 'normal_interpolation_radius_factor',
             'use_direction_interpolation', 'direction_interpolation_steps',
             'scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_chain(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _location = [('distance', 'distance_pressure', ), ('divergence', 'divergence_pressure', ), ]
    _rotation = [{'OVERRIDE': ('rotation_align', 'use_rotation_align_tilt_override', ), }, 'rotation_up', 'rotation_base', 'rotation_random',
                 ('use_normal_interpolation', 'normal_interpolation_radius_factor', ),
                 ('use_direction_interpolation', 'direction_interpolation_steps', ), ]
    _scale = ['scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('distance', 'distance_pressure', 'divergence', 'divergence_pressure',
             'rotation_align', 'use_rotation_align_tilt_override', 'rotation_up', 'rotation_base', 'rotation_random',
             'use_normal_interpolation', 'normal_interpolation_radius_factor',
             'use_direction_interpolation', 'direction_interpolation_steps',
             'scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_spray(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', ('num_dots', 'num_dots_pressure', ), 'uniform', 'jet', 'reach', ]
    _location = [('use_minimal_distance', 'minimal_distance', 'minimal_distance_pressure', ), ]
    _rotation = [{'OVERRIDE': ('rotation_align', 'use_rotation_align_tilt_override', ), }, 'rotation_up', 'rotation_base', 'rotation_random',
                 ('use_normal_interpolation', 'normal_interpolation_radius_factor', ), ]
    _scale = ['scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval',
             'use_minimal_distance', 'minimal_distance', 'minimal_distance_pressure',
             'rotation_align', 'use_rotation_align_tilt_override', 'rotation_up', 'rotation_base', 'rotation_random',
             'use_normal_interpolation', 'normal_interpolation_radius_factor',
             'scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    # spray is always on timer, but to remind me and to make sure some other parts of inherited code works properly, override it here
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    num_dots: IntProperty(name=translate("Points Per Interval"), default=50, min=1, soft_max=250, max=5000, description=translate("Number of point created per tool action"), )
    num_dots_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    jet: FloatProperty(name=translate("Jet Factor"), default=1.0, min=0.001, soft_max=3.0, precision=3, subtype='NONE', description=translate("Spray jet distance from surface as factor * radius"), )
    reach: FloatProperty(name=translate("Reach"), default=1.0, min=0.001, precision=3, soft_max=4, subtype='DISTANCE', description=translate("How far spray can reach past surface at center"), )
    uniform: BoolProperty(name=translate("Uniform Sampling"), default=False, description=translate("Distribute points uniformly in radius circle"), )


class SCATTER5_PR_manual_brush_tool_spray_aligned(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', ('num_dots', 'num_dots_pressure', ), 'uniform', 'jet', 'reach', ]
    _location = [('use_minimal_distance', 'minimal_distance', 'minimal_distance_pressure', ), ]
    _rotation = [{'OVERRIDE': ('rotation_align', 'use_rotation_align_tilt_override', ), }, 'rotation_base', 'rotation_random',
                 ('use_normal_interpolation', 'normal_interpolation_radius_factor', ),
                 ('use_direction_interpolation', 'direction_interpolation_steps', ), ]
    _scale = ['scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval',
             'use_minimal_distance', 'minimal_distance', 'minimal_distance_pressure',
             'rotation_align', 'use_rotation_align_tilt_override', 'rotation_base', 'rotation_random',
             'use_normal_interpolation', 'normal_interpolation_radius_factor',
             'use_direction_interpolation', 'direction_interpolation_steps',
             'scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    # spray is always on timer, but to remind me and to make sure some other parts of inherited code works properly, override it here
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    num_dots: IntProperty(name=translate("Points Per Interval"), default=50, min=1, soft_max=250, max=5000, description=translate("Number of point created per tool action"), )
    num_dots_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    jet: FloatProperty(name=translate("Jet Factor"), default=1.0, min=0.001, soft_max=3.0, precision=3, subtype='NONE', description=translate("Spray jet distance from surface as factor * radius"), )
    reach: FloatProperty(name=translate("Reach"), default=1.0, min=0.001, precision=3, soft_max=4, subtype='DISTANCE', description=translate("How far spray can reach past surface at center"), )
    uniform: BoolProperty(name=translate("Uniform Sampling"), default=False, description=translate("Distribute points uniformly in radius circle"), )


class SCATTER5_PR_manual_brush_tool_lasso_fill(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = ['omit_backfacing', 'high_precision', ]
    _location = ['density', ]
    _rotation = ['rotation_align', 'rotation_up', 'rotation_base', 'rotation_random',
                 ('use_normal_interpolation', 'normal_interpolation_radius_factor', ), ]
    _scale = ['scale_default', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('rotation_align', 'rotation_up', 'rotation_base', 'rotation_random',
             'use_normal_interpolation', 'normal_interpolation_radius_factor',
             'scale_default', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    # NOTE: unique:
    density: FloatProperty(name=translate("Instance/m²"), default=5.0, min=0.001, precision=3, description=translate("Points density in world units"), )
    area_threshold: FloatProperty(name=translate("Triangle Area Threshold"), default=0.01, min=0.0001, precision=3, description=translate(""), )
    max_points_per_fill: IntProperty(name=translate("Approx. Max. Points Per Fill"), default=-1, min=-1, soft_max=5000, max=10000, description=translate(""), )
    omit_backfacing: BoolProperty(name=translate("Omit Backfacing"), default=False, description=translate("Ignore surface facing out from view"), )
    omit_backfacing_tolerance: FloatProperty(default=0.01, )
    high_precision: BoolProperty(name=translate("High Precision"), default=False, description=translate("Precise fill area borders drawing"), )


class SCATTER5_PR_manual_brush_tool_clone(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), None, 'radius_units', ), }, 'falloff', ('affect', 'affect_pressure', ), ]
    _location = ['update_uuid', ]
    _rotation = ['use_align_z_to_surface', 'use_random_rotation', 'use_rotate_instances', ]
    _scale = [('use_random_scale', 'random_scale_range', ), 'use_scale_instances', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_units', 'falloff', 'affect', 'affect_pressure', 'use_align_z_to_surface', )
    # NOTE: overrides:
    # NOTE: unique:
    use_random_rotation: BoolProperty(name=translate("Random Sample Rotation"), default=False, description=translate("Rotate sample randomly after each use"), )
    use_random_scale: BoolProperty(name=translate("Random Sample Scale"), default=False, description=translate("Scale sample randomly after each use"), )
    random_scale_range: FloatVectorProperty(name=translate("Range"), default=(-0.25, 0.25, ), precision=3, size=2, description=translate("Random sample scale range"), )
    use_rotate_instances: BoolProperty(name=translate("Rotate Instances"), default=False, description=translate("Rotate instances individually when sample is rotated"), )
    use_scale_instances: BoolProperty(name=translate("Scale Instances"), default=False, description=translate("Scale instances individually when sample is scaled"), )
    update_uuid: BoolProperty(name=translate("Reassign Surface By Proximity"), default=True, description=translate("Assign new surface to cloned points"), )


class SCATTER5_PR_manual_brush_tool_eraser(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = ['mode', {'RADIUS': (('radius', 'radius_px', 'radius_2d', ), 'radius_pressure', 'radius_units', ), }, 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_2d', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on', )
    # NOTE: overrides:
    # NOTE: unique:
    mode: EnumProperty(name=translate("Mode"), default='3D', items=[
        ('3D', translate("Surface"), "Erase on surface", ),
        ('2D', translate("Screen"), "Erase under cursor", ),
    ], description=translate("Eraser action mode"), )


class SCATTER5_PR_manual_brush_tool_dilute(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    _location = ['minimal_distance', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on', 'minimal_distance', )
    # NOTE: overrides:
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_smooth(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, ('strength', 'strength_pressure', ), 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    _rotation = ['use_align_z_to_surface', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on',
             'use_align_z_to_surface', 'strength', 'strength_pressure', )
    # NOTE: overrides:
    strength: FloatProperty(name=translate("Strength"), default=0.1, min=0.0, max=1.0, precision=3, subtype='FACTOR', description=translate(""), )
    # FIXMENOT: default is True, no need for override -->> but i want different name
    use_align_z_to_surface: BoolProperty(name=translate("Update Surface Normal"), default=True, description=translate("Align instance Z axis to closest surface normal"), )
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_move(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), None, 'radius_units', ), }, {'BUTTON': 'proportional_mode', }, 'falloff', ('affect', 'affect_pressure', ), ]
    _location = ['update_uuid', ]
    _rotation = ['use_align_z_to_surface', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_units', 'falloff', 'affect', 'affect_pressure', 'use_align_z_to_surface', )
    # NOTE: overrides:
    # NOTE: unique:
    proportional_mode: BoolProperty(name=translate("Proportional"), default=False, description=translate("Use proportional mode"), )
    update_uuid: BoolProperty(name=translate("Reassign Surface By Proximity"), default=True, description=translate("Reassign surface to points"), )


class SCATTER5_PR_manual_brush_tool_rotation_set(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    _rotation = [{'SECTION': ('use_rotation_align', 'rotation_align', 'rotation_up', ), }, {'SECTION': ('use_rotation_base', 'rotation_base', ), }, {'SECTION': ('use_rotation_random', 'rotation_random', ), }, ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on', )
    # NOTE: overrides:
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    use_rotation_align: BoolProperty(name=translate("Enabled"), default=True, description=translate("Use align settings"), )
    use_rotation_base: BoolProperty(name=translate("Enabled"), default=True, description=translate("Use base rotation settings"), )
    use_rotation_random: BoolProperty(name=translate("Enabled"), default=True, description=translate("Use random rotation settings"), )


class SCATTER5_PR_manual_brush_tool_random_rotation(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    _rotation = ['angle', ('speed', 'speed_pressure', ), ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on', )
    # NOTE: overrides:
    interval: FloatProperty(name=translate("Interval"), default=0.1 / 2, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate("Tool action interval in seconds"), )
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    speed: FloatProperty(name=translate("Speed"), default=0.015, min=-1.0, max=1.0, precision=3, subtype='NONE', description=translate("Angle change per action step"), )
    speed_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    angle: FloatProperty(name=translate("Max Angle"), default=np.radians(30), min=np.radians(1), max=np.radians(179), precision=3, subtype='ANGLE', description=translate("Maximum divergence angle"), )


class SCATTER5_PR_manual_brush_tool_comb(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'falloff', ]
    _rotation = ['effect_axis', ('strength', 'strength_pressure', ), 'strength_random', ('use_direction_interpolation', 'direction_interpolation_steps', ), ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'falloff',
             'use_direction_interpolation', 'direction_interpolation_steps',
             'effect_axis', 'strength', 'strength_pressure', )
    # NOTE: overrides:
    # only mouse move, it does not work with timers..
    draw_on: EnumProperty(name=translate("Draw On"), default='MOUSEMOVE', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    strength: FloatProperty(name=translate("Strength"), default=1.0, min=0.0, max=1.0, precision=3, subtype='FACTOR', description=translate("Effect strength"), )
    # NOTE: unique:
    strength_random: BoolProperty(name=translate("Random Strength"), default=False, description=translate("Random strength"), )
    strength_random_range: FloatVectorProperty(name=translate("Random Strength Range"), default=(0.0, 1.0, ), precision=3, subtype='NONE', size=2, soft_min=-1.0, soft_max=1.0, description=translate("Random strength range"), )


class SCATTER5_PR_manual_brush_tool_spin(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'falloff', ]
    _rotation = ['effect_axis', ('speed', 'speed_pressure', ), 'speed_random', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'falloff',
             'effect_axis', )
    # NOTE: overrides:
    # always timer..
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    speed: FloatProperty(name=translate("Angle"), default=np.radians(5), min=-np.pi, max=np.pi, precision=3, subtype='ANGLE', description=translate("Angular rotation speed"), )
    speed_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    speed_random: BoolProperty(name=translate("Random Angle"), default=False, description=translate("Use random angle"), )
    speed_random_range: FloatVectorProperty(name=translate("Random Angle Range"), default=(-1.0, 1.0, ), precision=3, subtype='NONE', size=2, soft_min=-1.0, soft_max=1.0, description=translate("Random angle range"), )


class SCATTER5_PR_manual_brush_tool_z_align(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius_2d', ), 'radius_pressure', ), }, 'falloff', ]
    _rotation = [('strength', 'strength_pressure', ), ('use_direction_interpolation', 'direction_interpolation_steps', ), ]
    _domain = '2D'
    # NOTE: sync:
    _sync = ('radius_2d', 'radius_pressure', 'falloff',
             'use_direction_interpolation', 'direction_interpolation_steps',
             'strength', 'strength_pressure', )
    # NOTE: overrides:
    '''
    # 2d tool, override world radius to screen radius
    radius: FloatProperty(name=translate("Radius"), default=50.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate("Tool active radius"), )
    '''
    # only mouse move, it does not work with timers..
    draw_on: EnumProperty(name=translate("Draw On"), default='MOUSEMOVE', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    strength: FloatProperty(name=translate("Strength"), default=0.2, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate("Effect strength"), )
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_scale_set(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    _scale = [{'SECTION': ('use_scale_default', 'scale_default', ), }, {'SECTION': ('use_scale_random_factor', 'scale_random_factor', 'scale_random_type', ), }, ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on', )
    # NOTE: overrides:
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    use_scale_default: BoolProperty(name=translate("Enabled"), default=True, description=translate("Use default scale settings"), )
    use_scale_random_factor: BoolProperty(name=translate("Enabled"), default=True, description=translate("Use random scale settings"), )


class SCATTER5_PR_manual_brush_tool_grow_shrink(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    _scale = ['change_mode', 'change', 'change_pressure', 'use_change_random', ('use_limits', 'limits', ), ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on', )
    # NOTE: overrides:
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    change_mode: EnumProperty(name=translate("Mode"), default='ADD', items=[('ADD', translate("Add"), "", ), ('SUBTRACT', translate("Subtract"), "", ), ], description=translate("Tool mode"), )
    change: FloatVectorProperty(name=translate("Value"), default=(0.1, 0.1, 0.1, ), precision=3, subtype='XYZ', size=3, description=translate("Scale change per action"), )
    change_pressure: BoolProperty(name=translate("Use Pressure"), default=False, description=translate("Use stylus pressure"), )
    use_limits: BoolProperty(name=translate("Use Limits"), default=False, description=translate("Use min and max scale"), )
    limits: FloatVectorProperty(name=translate("Limits"), default=(0.0, 1.0, ), precision=3, size=2, description=translate("Min and max scale"), )
    use_change_random: BoolProperty(name=translate("Random"), default=False, description=translate("Random scale change per action"), )
    # hidden.. just to use factors bigger than 0.5, so scaling is not too slow, will be still random, but not that much..
    change_random_range: FloatVectorProperty(name=translate("Random Range"), default=(0.5, 1.0, ), precision=3, subtype='NONE', size=2, soft_min=0.0, soft_max=1.0, description=translate(""), )


class SCATTER5_PR_manual_brush_tool_object_set(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius', 'radius_px', ), 'radius_pressure', 'radius_units', ), }, 'interval', 'falloff', ('affect', 'affect_pressure', ), 'draw_on', ]
    _settings = ['index', ]
    # NOTE: sync:
    _sync = ('radius', 'radius_px', 'radius_pressure', 'radius_units', 'interval', 'falloff', 'affect', 'affect_pressure', 'draw_on', )
    # NOTE: overrides:
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    index: IntProperty(name=translate("Instance Index"), default=0, min=0, max=99, description=translate("Instance index"), )


class SCATTER5_PR_manual_brush_tool_drop_down(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _location = ['use_ground_plane', 'update_uuid', ]
    _tool = [{'RADIUS': (('radius_2d', ), ), }, 'falloff', ('affect', 'affect_pressure', ), ]
    _domain = '2D'
    # NOTE: sync:
    _sync = ('radius_2d', 'falloff', 'affect', 'affect_pressure', )
    # NOTE: overrides:
    '''
    # 2d tool, override world radius to screen radius
    radius: FloatProperty(name=translate("Radius"), default=50.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate("Tool active radius"), )
    '''
    # NOTE: unique:
    use_ground_plane: BoolProperty(name=translate("Use Ground Plane"), default=False, description=translate("If there is no surface under point, drop point to ground plane"), )
    update_uuid: BoolProperty(name=translate("Reassign Surface By Proximity"), default=False, description=translate("Reassign surface to points"), )


class SCATTER5_PR_manual_brush_tool_free_move(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = [{'RADIUS': (('radius_2d', ), ), }, 'falloff', ]
    _domain = '2D'
    # NOTE: sync:
    _sync = ('radius_2d', 'falloff', )
    # NOTE: overrides:
    '''
    # 2d tool, override world radius to screen radius
    radius: FloatProperty(name=translate("Radius"), default=50.0, min=1.0, soft_max=300.0, precision=0, subtype='FACTOR', description=translate("Tool active radius"), )
    '''
    # always mousemove
    draw_on: EnumProperty(name=translate("Draw On"), default='MOUSEMOVE', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:


class SCATTER5_PR_manual_brush_tool_manipulator(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = ['translation', 'rotation', 'scale', ]
    # NOTE: sync:
    _sync = tuple()
    # NOTE: overrides:
    # NOTE: unique:
    translation: bpy.props.BoolProperty(name=translate("Translation"), default=True, description=translate("Show translation gizmo"), )
    rotation: bpy.props.BoolProperty(name=translate("Rotation"), default=False, description=translate("Show rotation gizmo"), )
    scale: bpy.props.BoolProperty(name=translate("Scale"), default=False, description=translate("Show scale gizmo"), )


class SCATTER5_PR_manual_brush_tool_heaper(SCATTER5_PR_manual_brush_tool_common, ):
    # NOTE: ui:
    _tool = ['interval', 'draw_on', 'drop_height', 'max_alive', 'frames_alive', ]
    _location = []
    _rotation = ['rotation_base', 'rotation_random', ]
    _scale = ['scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', ]
    # NOTE: sync:
    _sync = ('rotation_base', 'rotation_random',
             'scale_default', 'scale_default_use_pressure', 'scale_random_factor', 'scale_random_type', )
    # NOTE: overrides:
    interval: FloatProperty(name=translate("Interval"), default=0.2, min=0.001, max=1.0, precision=3, subtype='FACTOR', description=translate("Tool action interval in seconds"), )
    draw_on: EnumProperty(name=translate("Draw On"), default='TIMER', items=[
        ('TIMER', translate("Timer"), "Action on time interval", ),
        ('MOUSEMOVE', translate("Move"), "Action on mouse pointer movement", ),
        ('BOTH', translate("Both"), "Action on both time interval or mouse pointer movement", ),
    ], description=translate("Tool action method"), )
    # NOTE: unique:
    # private ---------------------------------------------- >>>
    # matrices of simulation objects with values within this limit are considered stable
    # np_allclose_atol: FloatProperty(default=1e-04, precision=6, )
    np_allclose_atol: FloatProperty(default=1e-03, precision=6, )
    # simulation scene setup
    scene_render_fps: IntProperty(default=30, )
    scene_frame_start: IntProperty(default=1, )
    scene_frame_end: IntProperty(default=1048574, )
    scene_frame_step: IntProperty(default=1, )
    scene_render_frame_map_old: IntProperty(default=100, )
    scene_render_frame_map_new: IntProperty(default=100, )
    
    # include_existing: BoolProperty(name=translate("Include Existing"), default=True, description=translate("Include existing instances as obstacles"), )
    drop_height: FloatProperty(name=translate("Drop Height"), default=5.0, min=0.0, subtype='DISTANCE', description=translate("Height above surface from where objects will be dropped down"), )
    frames_alive: IntProperty(name=translate("Frames Alive"), default=200, min=1, description=translate("Maximal simulation object life in frames, if object is not stable after its lifespan, will be removed without effect"), )
    max_alive: IntProperty(name=translate("Max Alive"), default=10, min=1, max=100, description=translate("Maximum of alive simulation objects at the same time"), )
    # other private bits..
    batch_multiplier: FloatProperty(default=10.0, )
    simulation_collection_name: StringProperty(default="simulation-collection", )
    # private ---------------------------------------------- <<<


class SCATTER5_PR_scene_manual(PropertyGroup, ):
    tool_default: PointerProperty(type=SCATTER5_PR_manual_brush_tool_default, )
    
    tool_dot: PointerProperty(type=SCATTER5_PR_manual_brush_tool_dot, )
    tool_spatter: PointerProperty(type=SCATTER5_PR_manual_brush_tool_spatter, )
    tool_pose: PointerProperty(type=SCATTER5_PR_manual_brush_tool_pose, )
    tool_path: PointerProperty(type=SCATTER5_PR_manual_brush_tool_path, )
    tool_chain: PointerProperty(type=SCATTER5_PR_manual_brush_tool_chain, )
    tool_spray: PointerProperty(type=SCATTER5_PR_manual_brush_tool_spray, )
    tool_spray_aligned: PointerProperty(type=SCATTER5_PR_manual_brush_tool_spray_aligned, )
    tool_lasso_fill: PointerProperty(type=SCATTER5_PR_manual_brush_tool_lasso_fill, )
    tool_clone: PointerProperty(type=SCATTER5_PR_manual_brush_tool_clone, )
    tool_eraser: PointerProperty(type=SCATTER5_PR_manual_brush_tool_eraser, )
    tool_dilute: PointerProperty(type=SCATTER5_PR_manual_brush_tool_dilute, )
    tool_smooth: PointerProperty(type=SCATTER5_PR_manual_brush_tool_smooth, )
    tool_move: PointerProperty(type=SCATTER5_PR_manual_brush_tool_move, )
    tool_rotation_set: PointerProperty(type=SCATTER5_PR_manual_brush_tool_rotation_set, )
    tool_random_rotation: PointerProperty(type=SCATTER5_PR_manual_brush_tool_random_rotation, )
    tool_comb: PointerProperty(type=SCATTER5_PR_manual_brush_tool_comb, )
    tool_spin: PointerProperty(type=SCATTER5_PR_manual_brush_tool_spin, )
    tool_z_align: PointerProperty(type=SCATTER5_PR_manual_brush_tool_z_align, )
    tool_scale_set: PointerProperty(type=SCATTER5_PR_manual_brush_tool_scale_set, )
    tool_grow_shrink: PointerProperty(type=SCATTER5_PR_manual_brush_tool_grow_shrink, )
    tool_object_set: PointerProperty(type=SCATTER5_PR_manual_brush_tool_object_set, )
    tool_drop_down: PointerProperty(type=SCATTER5_PR_manual_brush_tool_drop_down, )
    tool_free_move: PointerProperty(type=SCATTER5_PR_manual_brush_tool_free_move, )
    tool_manipulator: PointerProperty(type=SCATTER5_PR_manual_brush_tool_manipulator, )
    tool_heaper: PointerProperty(type=SCATTER5_PR_manual_brush_tool_heaper, )
    
    # `tool_id`
    active_tool: StringProperty(default="scatter5.manual_brush_tool_spray", )
    # synchronization
    use_sync: BoolProperty(name=translate("Unified Tool Settings"), default=False, description=translate("Keep select general tool properties in sync"), )
    # exp scale
    use_radius_exp_scale: BoolProperty(name=translate("Radius Gesture Exponential Scale"), default=False, description=translate("Use exponential scale for 3D radius gestures"), )
