import bpy

from bpy.props import IntProperty, IntVectorProperty, FloatProperty, BoolProperty, StringProperty
from math import degrees, radians
from mathutils import Matrix

from .. utils import addon
from .. utils import colors
from .. utils import collections
from .. utils import cursor
from .. utils import hud
from .. utils import key_handler
from .. utils import modifiers
from .. utils import mouse_transforms
from .. utils import objects
from .. utils import selection
from .. utils import transforms
from .. utils import visibility


def load_global_transforms(self, context, curve, i):
    ob = objects.retrieve(context, curve.get('geo'))
    if addon.debug():
        print(f'scaling geo {ob}')
    if ob is not None:
        cap1 = objects.find(ob.get('cap1'))
        cap2 = objects.find(ob.get('cap2'))
    
    mode  = curve['mode']
    index = curve['index']

    min_scale = 0.001   # Safety Scale

    if mode == 1 and index == -1:
        curve.data.bevel_depth = self.start_scale[i]
    
    elif mode == 1:
        if self.start_scale[i] < min_scale:
            self.start_scale[i] = min_scale
        
        ob.uniform_scale = self.start_scale[i]
        ob.profile_rot = radians(self.start_rotation[i])

    elif mode == 2:
        if self.start_scale[i] < min_scale:
            self.start_scale[i] = min_scale

        ob.data.uniform_scale = self.start_scale[i]
        ob.rotation_euler.z = radians(self.start_rotation[i])
        ob.array_center = self.start_slide[i]

        if cap1 is not None and cap2 is not None:
            cap1.data.uniform_scale = self.start_scale[i]
            cap2.data.uniform_scale = self.start_scale[i]

    elif mode == 3:
        if self.start_scale[i] < min_scale:
            self.start_scale[i] = min_scale

        ob.uniform_scale = self.start_scale[i]
        ob.rotation_euler.z = radians(self.start_rotation[i])
        ob.location.z = self.start_slide[i]


def kitbash_instance_creator(self, context, mode, index, curve, i):
    
    if mode == 1 and index == -1:
        if bpy.app.version >= (2, 91, 0): 
            curve.data.bevel_mode = 'ROUND' 

        # if curve == self.master_curve: 
        #     self.profile_name = 'Simple Pipe'
    
    else:
        if bpy.app.version >= (2, 91, 0): 
            curve.data.bevel_mode = 'OBJECT'
        
        source_obj = self.source_objects[index]
   
        self.cap1 = None
        self.cap2 = None

        if source_obj.type == 'COLLECTION':
            if addon.debug():
                print(f'source is coll {source_obj.name}')

            # Do this first because we have to change the val of source_obj.
            if source_obj.children:
                if addon.debug():
                    print(f'source coll children {source_obj.children[:]}')
                if len(source_obj.children[0].objects) > 1:
                    self.cap1 = source_obj.children[0].objects[0]
                    self.cap2 = source_obj.children[0].objects[1]
                else:
                    if addon.debug():
                        print('Caps Collection is Empty')

            # Change source_obj to the real thing.
            if source_obj.objects:
                if addon.debug():
                    print(f'real source object {source_obj.objects[0].name}')
                source_obj = source_obj.objects[0]
            else:
                self.report({'ERROR'}, 'Collection has no object to array')
                return {'CANCELLED'}
                # source_obj = None
                # if addon.debug():
                #     print('Collection has no Object to Array')
        if addon.debug():
            print(f'Source Cap 1 {self.cap1}')
            print(f'Source Cap 2 {self.cap2}')

        self.instance_obj = objects.duplicate_object(context, source_obj, suffix=str(index), coll=self.default_collection)
        self.instance_obj.color = colors.DEMO_COLOR

        if self.cap1 is not None and self.cap2 is not None:
            # Always add a suffix to prevent names from matching source files.
            self.cap1 = objects.duplicate_object(context, self.cap1, suffix='_in', coll=self.caps_collection, select=False)
            self.cap2 = objects.duplicate_object(context, self.cap2, suffix='_in', coll=self.caps_collection, select=False)

            # if self.cap1.name == source_obj.children[0].objects[0].name:
            #     self.report({'ERROR'}, 'Cap1 name matches source name')
            # if self.cap2.name == source_obj.children[0].objects[1].name:
            #     self.report({'ERROR'}, 'Cap2 name matches source name')

            self.instance_obj['cap1'] = self.cap1.name
            self.instance_obj['cap2'] = self.cap2.name

            if addon.debug():
                print(f'Cap duplicates are {self.cap1}, {self.cap2}')
            self.cap1.select_set(True)

        modifiers.apply_modifiers(self, context, self.instance_obj, curve)

        self.instance_obj['curve'] = curve.name
        curve['geo'] = self.instance_obj.name
        if addon.debug():
            print(f'setting geo ID to {self.instance_obj.name}')
    
    self.index_list[mode-1] = index

    if curve == self.master_curve:
        try:
            self.profile_name = source_obj.name
        except UnboundLocalError:
            self.profile_name = 'Simple Pipe'
        
    # set_array_strings(self, context, self.master_curve)  # Does nothing if not mode 2.
    load_global_transforms(self, context, curve, i)


def get_mode_source_objects(self, mode):
    mode_names = [      # This should be changed so the master curve determines the mode name.
        'PROFILE',
        'ARRAY',
        'KITBASH',
        ]
    
    self.mode_name = mode_names[mode-1]
    source_mode_objects = self.all_source_objects[mode-1]

    return source_mode_objects


def shading_switch(current_shading):
    switch = {
        'ANGLE': 'FLAT',
        'FLAT': 'SMOOTH',
        'SMOOTH': 'ANGLE',
    }

    return switch[current_shading]


def set_array_strings(self, context, curve):
    '''Use Master curve as Input'''

    mode = curve.get('mode')
    if mode != 2:
        return
    
    ob = objects.retrieve(context, curve.get('geo'))
    if ob is None:
        return

    array = ob.modifiers.get('CB Array')
    if array is None:
        return

    self.array_type = array.fit_type
    self.array_count = array.count


class ARMORED_OT_Curve_Basher(bpy.types.Operator):
    '''Run the Modal Kitbasher (scroll through presets and scale, twist, etc).

(www.armoredColony.com)'''

    bl_idname  = 'curvebash.kitbasher_modal'
    bl_label   = 'Modal Kitbasher'
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR_X', 'BLOCKING'}

    index_list   : IntVectorProperty(default=(-1, 0, 0), name='Start Index')
    
    last_mode : IntProperty(default=1, name='Start Type')
    # last_index : IntProperty (default=-1)

    last_scale : FloatProperty (name='Start Scale', default=0.1,
            description='Starting Scale', options={'HIDDEN'})

    last_rotation : FloatProperty (name='Start Rotation', default=0,
            description='Starting Rotation', options={'HIDDEN'})

    last_twist : FloatProperty (name='Start Twist', default=0,
            description='Starting Twist', options={'HIDDEN'})

    last_twist_offset : FloatProperty (name='Start Twist Offset', default=0,
            description='Starting Twist Offset', options={'HIDDEN'})

        
    array_count       : IntProperty    (default=1, name='Array Count')
    array_type        : StringProperty (default='FIT_CURVE', name='Array Type')
    # array_count_str   : StringProperty (default='Auto')
    
    scale_speed  : FloatProperty (default=0.0005, precision=4, name='Scale Speed')
    rotate_speed : FloatProperty (default=0.5000, precision=4, name='Rotate Speed')
    twist_speed  : FloatProperty (default=0.0100, precision=4, name='Twist Speed')
    slide_speed  : FloatProperty (default=0.0050, precision=4, name='Slide Speed')

    def modal(self, context, event):

        context.area.tag_redraw()

        # 'ALT, SHIFT' PRESS AND RELEASE
        # Some operations must be performed instantly on modifier key Press. -----------------------------
        if event.alt:
            key_handler.alt_press_events(self, context, event)
        else:
            key_handler.alt_release_events(self, context, event)
        
        if event.shift:
            key_handler.shift_press_events(self, context, event)
        else:
            key_handler.shift_release_events(self, context, event)
        
        
        # SWITCH BETWEEN TRANSFORM MODES ------------------------------------------------------------------
        
        if event.type in {'S', 'R', 'T', 'G'} and event.value == 'PRESS':

            # Re-setting transforms also requires a random_offset reset
            if event.alt:
                key_handler.alt_release_events(self, context, event)

            if not self.press_transform_key:
                self.press_transform_key = True

                if event.type == 'S':
                    
                    if event.alt:
                        transforms.reset_radius(self, context)

                    else:
                        if not self.scaling:
                            self.scaling, self.rotating, self.twisting, self.sliding  = True, False, False, False
                            self.transform_name = 'Scale'

                elif event.type == 'R':

                    if event.alt:
                        transforms.reset_rotation(self, context)
                        
                    else:
                        if not self.rotating:
                            self.scaling, self.rotating, self.twisting, self.sliding  = False, True, False, False
                            self.transform_name = 'Rotate'

                elif event.type == 'T':

                    if event.alt:
                        transforms.reset_twist(self, context)

                    else:
                        if not self.twisting:
                            self.scaling, self.rotating, self.twisting, self.sliding  = False, False, True, False
                            self.transform_name = 'Twist'

                elif event.type == 'G':

                    if event.alt:
                        transforms.reset_slide(self, context)

                    else:
                        if not self.sliding:
                            self.scaling, self.rotating, self.twisting, self.sliding  = False, False, False, True
                            self.transform_name = 'Slide'

                            visibility.set_stretch(self, False) # Disable Confine so we can slide.

                self.start_mouse_x = event.mouse_region_x
                for i, curve in enumerate(self.selection):
                    transforms.update_start_values(self, context, curve, i)

        # Prevents repeated activations when holding down the keys.
        elif event.type in {'S', 'R', 'T', 'G'} and event.value == 'RELEASE':
            self.press_transform_key = False
        

        # TRANSFORM OPERATIONS USING MOUSE MOVEMENT -------------------------------------------------------
        if event.type == 'MOUSEMOVE':	

            cursor.wrap_cursor(self, context, event)

            self.mouse_x = event.mouse_region_x - self.cursor_wrap_offset_x
            self.mouse_y = event.mouse_region_y

            delta = event.mouse_region_x - self.start_mouse_x

            if self.scaling:
                mouse_transforms.modal_scale(self, context, delta)

                #Canging the array count also changes it's dimensions. Reposition...
                # self.start_mouse_x = event.mouse_region_x
                # for i, curve in enumerate(self.selection):
                #     transforms.update_start_values(self, context, curve, i)
                #     load_global_transforms(self, context, curve, i)

            elif self.rotating:
                mouse_transforms.modal_rotate(self, context, delta)

            elif self.twisting:
                mouse_transforms.modal_twist_curve(self, context, delta, reverse=event.alt)
            
            elif self.sliding:
                for curve in self.selection:
                    mode = curve['mode']
                    if mode in {2, 3}:
                        mouse_transforms.slide_along_curve(self, context, curve, delta)
        

        # SWITCHING PROFILES/KITBASH PRESETS WITH MOUSE SCROLL --------------------------------------------
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'UP_ARROW', 'DOWN_ARROW'} and event.value == 'PRESS':

            if not event.shift and not event.ctrl:
                if addon.debug():
                    print('not shift and not ctrl')

                for i, curve in enumerate(self.selection):
                    mode  = curve['mode']
                    index = curve['index']
                    
                    transforms.update_start_values(self, context, curve, i)

                    objects.clear_objects(self, context, curve, i)
                    
                    self.source_objects = get_mode_source_objects(self, mode)
                    
                    floor = -1 if mode == 1 else 0      # Special index case for mode 1 only
                    ceil = len(self.source_objects)-1

                    if event.type in {'WHEELUPMOUSE', 'UP_ARROW'}:
                        index = index + 1 if index < ceil else floor
                    else:
                        index = index - 1 if index > floor else ceil
                    
                    curve['index'] = index
                    kitbash_instance_creator(self, context, mode, index, curve, i)
                    # transforms.update_start_values(self, context, curve, i)

                set_array_strings(self, context, self.master_curve)
                self.start_mouse_x = event.mouse_region_x

            if event.shift:
                
                for i, curve in enumerate(self.selection):
                    mode  = curve['mode']
                    index = curve['index']

                    if mode == 1:
                        if event.type in {'WHEELUPMOUSE', 'UP_ARROW'}:
                            key_handler.set_curve_resolution(self, context, curve, increment=2)
                        else:
                            key_handler.set_curve_resolution(self, context, curve, increment=-2)
                    
                    elif mode == 2:
                        if event.type in {'WHEELUPMOUSE', 'UP_ARROW'}:
                            key_handler.set_array_count(self, context, curve, i, increment=1)
                        else:
                            key_handler.set_array_count(self, context, curve, i, increment=-1)

                set_array_strings(self, context, self.master_curve)  # Does nothing if not mode 2.

            if event.ctrl:
                
                for i, curve in enumerate(self.selection):
                    mode  = curve['mode']
                    index = curve['index']

                    if event.type in {'WHEELUPMOUSE', 'UP_ARROW'}:
                        key_handler.set_curve_sides(self, context, curve, increment=1)
                    else:
                        key_handler.set_curve_sides(self, context, curve, increment=-1)
            
            context.view_layer.objects.active = objects.get_master_kitbash(context, self.master_curve)
            
            visibility.load_preferences(self, context)


        # SWITCH KITBASY TYPE -----------------------------------------------------------------------------
        elif event.type in {'ONE', 'TWO', 'THREE', 'LEFT_ARROW', 'RIGHT_ARROW', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3'} and event.value == 'PRESS':

            if event.type in {'ONE', 'NUMPAD_1'}:
                mode = 1

            elif event.type in {'TWO', 'NUMPAD_2'}:
                mode = 2
                
            elif event.type in {'THREE', 'NUMPAD_3'}:
                mode = 3

            elif event.type == 'LEFT_ARROW':
                mode = self.master_curve.get('mode', 1)
                mode = mode - 1 if mode > 1 else 3

            elif event.type == 'RIGHT_ARROW':
                mode = self.master_curve.get('mode', 1)
                mode = mode + 1 if mode < 3 else 1

            self.source_objects = get_mode_source_objects(self, mode)
            index = self.index_list[mode-1]

            for i, curve in enumerate(self.selection):
                transforms.update_start_values(self, context, curve, i)

                # Safe to do this here bacause the ID properties haven't been updated yet.
                objects.clear_objects(self, context, curve, i)

                curve['mode']  = mode
                curve['index'] = index

                kitbash_instance_creator(self, context, mode, index, curve, i)

            set_array_strings(self, context, self.master_curve)
            self.start_mouse_x = event.mouse_region_x

            context.view_layer.objects.active = objects.get_master_kitbash(context, self.master_curve)

            visibility.load_preferences(self, context)
            
        # ENTER CURVE EDIT MODE ---------------------------------------------------------------------------
        elif event.type == 'TAB' and event.value == 'PRESS':
            visibility.reset(self, context)  # Selection based (run before modifying selections)

            # Only have curves Selected.
            bpy.ops.object.select_all(action='DESELECT')
            for i, curve in enumerate(self.selection):
                curve.select_set(True)
            
            # Set any curve as the active object so mode toggling takes us into EDIT_CURVE.
            context.view_layer.objects.active = self.master_curve

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.select_all(action='SELECT')

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}


        # RESET ALL TRANSFORMATIONS -----------------------------------------------------------------------
        elif event.type in {'ZERO', 'NUMPAD_0'} and event.value == 'PRESS':

            # if event.alt:
                # transforms.reset_transforms(self, context, relative=True)

            # else:
                # transforms.reset_transforms(self, context, relative=False)
            transforms.reset_transforms(self, context, relative=event.alt)

            self.start_mouse_x = event.mouse_x
            for i, curve in enumerate(self.selection):
                transforms.update_start_values(self, context, curve, i)


        # EVENT FOR TESTING STUFF -------------------------------------------------------------------------
        elif event.type == 'SPACE' and event.value == 'PRESS':
            pass

            # if self.mode == 1:
            #     bpy.ops.object.convert(target='MESH', keep_original=True)
            #     for i, curve in enumerate(self.selection):
            #         curve.select_set(False)
            #         curve.hide_set(True)

            # bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            # return {'FINISHED'}
                
            # elif self.mode == 2 or self.mode == 3:
            #     modifiers.apply_subsurf_modifiers(self, context, self.instance_obj, levels = 2)
            #     bpy.data.objects[self.instance_obj.name].data.use_auto_smooth = False


        # MINOR EVENTS ------------------------------------------------------------------------------------
        elif event.type == 'A' and event.value == 'PRESS':
            addon.get_prefs().smoothing = shading_switch(addon.get_prefs().smoothing)
            # addon.get_prefs().smoothing = not addon.get_prefs().smoothing
            visibility.set_smoothing(self, context, addon.get_prefs().smoothing)

        elif event.type == 'C' and event.value == 'PRESS':
            addon.get_prefs().array_caps = not addon.get_prefs().array_caps
            modifiers.set_array_caps(self, context, addon.get_prefs().array_caps)


        elif event.type == 'F' and event.value == 'PRESS':
            self.array_type = modifiers.toggle_array_fit_type(current=self.array_type)
            modifiers.set_array_fit_type(self, context, self.array_type)

            if self.array_type == 'FIT_CURVE':
                # if addon.get_prefs().autofit_exits_slide and self.sliding:
                #     self.scaling, self.rotating, self.twisting, self.sliding  = True, False, False, False
                #     self.transform_name = 'Scale'
                if addon.get_prefs().autofit_enables_stretch and not self.sliding:
                    visibility.set_stretch(self, True)
                    # addon.get_prefs().stretch = True
                    # visibility.set_stretch(self, addon.get_prefs().stretch)

            self.start_mouse_x = event.mouse_region_x
            for i, curve in enumerate(self.selection):
                transforms.update_start_values(self, context, curve, i)
                load_global_transforms(self, context, curve, i)


        elif event.type == 'X' and event.value == 'PRESS':
            if self.sliding:
                self.report({'WARNING'}, 'Cannot Confine while Sliding')
            else:
                visibility.toggle_stretch(self)
                # addon.get_prefs().stretch = not addon.get_prefs().stretch
                # visibility.set_stretch(self, addon.get_prefs().stretch)


        elif event.type == 'W' and event.value == 'PRESS':
            addon.get_prefs().wireframe = not addon.get_prefs().wireframe
            visibility.set_wireframe(self, addon.get_prefs().wireframe)


        elif event.type in {'Z', 'O'} and event.value == 'PRESS':
            addon.get_prefs().outline = not addon.get_prefs().outline
            context.space_data.overlay.show_outline_selected = addon.get_prefs().outline


        elif event.type in {'F1', 'H'} and event.value == 'PRESS':
            addon.get_prefs().expanded_hud = not addon.get_prefs().expanded_hud
            # self.expanded_HUD = not self.expanded_HUD


        # APPLY AND EXIT THE OPERATOR ---------------------------------------------------------------------
        elif event.type in {'LEFTMOUSE', 'NUMPAD_ENTER'}:

            if event.ctrl and event.alt and event.shift and event.type == 'NUMPAD_ENTER':
                self.report({'ERROR'}, 'DEVELOPER EXIT\n The addon will not work until blender restarts.')
                return {'CANCELLED'}

            for i, curve in enumerate(self.selection):
                mode  = curve['mode']
                index = curve['index']

                transforms.update_start_values(self, context, curve, i)
                self.last_curve = curve

            transforms.set_defaults_for_new_curves(self, context, base_curve=self.master_curve)
                
            visibility.reset(self, context)
            collections.cleanup(self, context)
            bpy.ops.wm.save_userpref()

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            return {'FINISHED'}


        # CANCEL THE OPERATOR -----------------------------------------------------------------------------
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            
            if event.ctrl and event.alt and event.shift and event.type == 'NUMPAD_ENTER':
                self.report({'ERROR'}, 'DEVELOPER EXIT\n The addon will not work until reload/restart.')
                return {'CANCELLED'}
            
            transforms.reset_transforms(self, context, relative=True)
            visibility.reset(self, context)
            collections.cleanup(self, context)

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            return {'CANCELLED'}
        

        # PASS THROUGH EVENTS -----------------------------------------------------------------------------
        # MIDDLE MOUSE EVENT DOES NOT WORK WHEN GRAB_CURSOR IS ENABLED
        # elif event.type in {'MIDDLEMOUSE'}:

        #     self.mouse_x = event.mouse_x
        #     self.mouse_y = event.mouse_y

        #     return {'PASS_THROUGH'}
        # for i, curve in enumerate(self.selection):
            # print(f'MESH SCALE: { curve["mesh_scale"] }')
        

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        # CHECK: CURRENT MODE >>
        if context.mode == 'OBJECT':
            pass

        elif context.mode == 'EDIT_CURVE':
            bpy.ops.object.mode_set(mode='OBJECT')

        elif context.mode == 'EDIT_MESH':
            if not selection.edge_to_curve(self, context):
                self.report({'ERROR'}, 'Curve Basher\n Select at least 1 Edge')
                return {'CANCELLED'}
    
        else:
            self.report({'ERROR'}, 'Curve Basher\n Unsupported Mode. Expected OBJECT or EDIT mode')
            return {'CANCELLED'}

        # CHECK: NOTHING IS SELECTED >>
        mixed_selection = set(context.selected_objects)

        if not mixed_selection:
            self.report({'ERROR'}, 'Curve Basher\n Select at least 1 Curve')
            return {'CANCELLED'}

        # Make sure the Active Object is part of our selection. Seems dumb but it's needed.
        if context.object not in mixed_selection:
            context.view_layer.objects.active = next(iter(mixed_selection))

        # Create a list of Curves (incompatible objects are deselected and discarded).
        self.selection = selection.filter_incompatible_types(self, context, selection=mixed_selection)

        if self.selection is None:
            return {'CANCELLED'}

        if context.object is None:
            context.view_layer.objects.active = self.selection[0]
            # context.view_layer.objects.active = next(iter(self.selection))

        # Set the main curve to be used as a template.
        self.master_curve = objects.set_master_curve(context, ob=context.object)
        
        # Change the active object from a curve to its kitbash if it has any.
        context.view_layer.objects.active = objects.get_master_kitbash(context, self.master_curve)

        # self.selection = list(self.selection)   # Don't need sets from this point forward.

        # THIS IS NOW DONE BY THE SELECTION FILTERING SUBROUTINE
        # for curve in self.selection:
        #     ob = curve.get('geo')
        #     if ob is None:                              # No object reference Exists.
        #         continue

        #     ob = context.scene.objects.get(ob)
        #     if ob is None:                              # Referenced object is not in scene.
        #         print('Missing object, clearing IDs')
        #         self.self.report({'ERROR'}, 'Message')
        #         del curve['mode']
        #         del curve['index']
        #         del curve['geo']

        # This check is better done in it's own loop so we can still abort without cleanup.
        self.curve_points = []
        for i, curve in enumerate(self.selection):
            spline = curve.data.splines[0]
            curve_type = spline.type
                
            if curve_type == 'BEZIER':
                self.curve_points.append(spline.bezier_points)

            elif curve_type == 'POLY':
                self.curve_points.append(spline.points)

            else:
                self.report({'ERROR'}, f'Curve Basher\n {curve_type} curves are not supported.')
                return {'CANCELLED'}
            
        self.mode_name = 'BASIC'
        self.transform_name = 'Scale'
        self.profile_name = 'Default'

        # Init helper flags.
        self.randomize_scale     = False
        self.randomize_rotation  = False
        self.randomize_seed      = False
        
        self.press_alt           = False
        self.press_shift         = False
        self.press_transform_key = False

        # Define all the necessary transform lists.
        # Useful for resetting transforms or reloading them after a preset swap.
        sel_count = len(self.selection)

        # self.original_scale = [None] * sel_count
 
        self.start_scale      = [.1] * sel_count
        self.start_rand_scale = [ 0] * sel_count
        self.end_rand_scale   = [ 0] * sel_count

        self.start_rotation      = [0] * sel_count
        self.start_rand_rotation = [0] * sel_count
        self.end_rand_rotation   = [0] * sel_count

        self.twist_offset = [0] * sel_count
        self.start_twist  = [0] * sel_count
        # self.start_rand_twist    = [0] * sel_count    # Not implemented yet.
        # self.end_rand_twist      = [0] * sel_count    # Not implemented yet.

        # self.start_slide = [0] * sel_count
        self.start_slide = [curve.data.splines[0].calc_length()/2 for curve in self.selection]

        for curve in self.selection:
            if addon.get_prefs().mk_override_apply_locations_rotation:
                transforms.apply_location_rotation(curve)
            else:
                transforms.apply_transforms(curve)  # Need this so kitbash can correctly.

                if addon.get_prefs().mk_inverse_scale_points:
                    if addon.debug():
                        print('Inverse Scale Curve Points\n')
                    spline = curve.data.splines[0]
                    points = spline.bezier_points
                    for p in points:
                        if p.radius != 0:
                            p.radius /= p.radius

            curve.color = colors.DEMO_COLOR

        # LINK THE NECESSARY 3D ASSETS.
        self.all_source_objects = collections.link_all_collections()
        self.default_collection = collections.create_collection(context, name='CB Kitbash')
        self.caps_collection    = collections.create_collection(context, name='CB Caps', parent=self.default_collection)

        # View Layer Hide
        # context.view_layer.layer_collection.children[self.default_collection.name].children[self.caps_collection.name].hide_viewport = addon.get_prefs().hide_source_caps

        # Similar to above but global for all view layers.
        self.caps_collection.hide_viewport = addon.get_prefs().hide_source_caps
        self.caps_collection.hide_render = True     # This is being ignored and auto-applied for some reason.
            
        self.start_mouse_x = event.mouse_region_x
        self.mouse_x = event.mouse_region_x
        self.mouse_y = event.mouse_region_y

        self.cursor_wrap_offset_x = 0
        self.region_border_x = context.region.width
        self.region_border_y = context.region.height
        
        # The first var set to True will become the active transform mode.
        self.scaling, self.rotating, self.twisting, self.sliding = True, False, False, False
        self.transform_name = 'Scale'   # Make sure this name is related to the transform mode set above.
        
        for i, curve in enumerate(self.selection):
            mode  = curve.get('mode')
            index = curve.get('index')
            # mode  = curve.get('mode',  self.last_mode)
            # index = curve.get('index', self.index_list[mode-1])

            # if curve.name != curve.get('name'):     # It's a virgin curve?
            #     if addon.debug():
            #         print(f'[Virgin Curve] {curve.name}\n')
            #     if addon.get_prefs().stretch_fit_new:
            #         curve.data.use_stretch = True
            #         curve.data.use_deform_bounds = True

            # if mode in {None, 1} or index in {None, -1} or curve.get('virgin') == True:
            if mode in {None} or index in {None} or curve.get('virgin') == True:
                mode = self.last_mode
                index = self.index_list[mode-1]

                if curve.get('virgin'):
                    del curve['virgin']

                if addon.get_prefs().stretch_fit_new:
                    curve.data.use_stretch = True
                    curve.data.use_deform_bounds = True

                if addon.debug():
                    print(f'[Virgin Curve] {curve.name}\n')

            curve['mode']  = mode   # Re-init just in case.
            curve['index'] = index  

            self.source_objects = get_mode_source_objects(self, mode)

            if mode == 1 and index == -1:
                # if curve == self.master_curve: 
                #     self.profile_name = 'Simple Pipe'
                if bpy.app.version >= (2, 91, 0):
                    curve.data.bevel_mode = 'ROUND'
                if curve.data.bevel_depth == 0:
                    transforms.set_transforms(self, context, curve, i, use_last_radius=True, use_last_rotation=True, use_last_twist=True)
                pass
            else:
                if bpy.app.version >= (2, 91, 0):
                    curve.data.bevel_mode = 'OBJECT'
                self.instance_obj = objects.retrieve(context, curve.get('geo'))
            
                if self.instance_obj is None:
                    if addon.debug():
                        print(f'Instance not found >> creating')
                    kitbash_instance_creator(self, context, mode, index, curve, i)
                    transforms.set_transforms(self, context, curve, i, use_last_radius=True, use_last_rotation=True, use_last_twist=True)
                
            if curve == self.master_curve:
                try:
                    self.profile_name = self.source_objects[index].name
                except UnboundLocalError:
                    self.profile_name = 'Simple Pipe'
            
            self.index_list[mode-1] = index
            
            transforms.update_start_values(self, context, curve, i)

        set_array_strings(self, context, self.master_curve)
        context.view_layer.objects.active = objects.get_master_kitbash(context, self.master_curve)
        transforms.store_original_transforms(self, context)
        visibility.load_preferences(self, context)
        
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(hud.draw_kitbasher_hud, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}


classes = (
    ARMORED_OT_Curve_Basher,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)