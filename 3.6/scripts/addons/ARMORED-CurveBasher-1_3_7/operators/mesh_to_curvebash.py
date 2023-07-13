import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty, FloatVectorProperty

import numpy as np
from math import pi, radians, degrees
from mathutils import Matrix, Vector, Quaternion

from .. utils import addon
from .. utils import modifiers
from .. utils import objects
from .. utils import transforms


def add_modifiers(self, context, ob, curve, fit_type, count):
    # Array Modifier. >>
    array = modifiers.array(ob)

    array.fit_type = fit_type
    array.count = count if fit_type == 'FIXED_COUNT' else 1
    array.curve = curve
    array.use_merge_vertices = self.merge

    if array.start_cap != self.start_cap:
        array.start_cap = self.start_cap

    if array.end_cap != self.end_cap:
        array.end_cap = self.end_cap
    
    if self.start_cap is None or self.end_cap is None:
        ob.curvebash.start_cap = ''
        ob.curvebash.end_cap   = ''
        cap1_id = ob.get('cap1')
        cap2_id = ob.get('cap2')

        if cap1_id: del ob['cap1']
        if cap2_id: del ob['cap2']

    else:
        ob.curvebash.start_cap = self.start_cap.name
        ob.curvebash.end_cap   = self.end_cap.name
        ob['cap1'] = self.start_cap.name
        ob['cap2'] = self.end_cap.name

    # if fit_type == 'FIT_CURVE':
    #     curve.data.use_stretch =    True
    #     curve.data.use_deform_bounds =  True
    # elif fit_type == 'FIXED_COUNT':
    #     curve.data.use_stretch = False
    #     curve.data.use_deform_bounds = False

    # array.array.relative_offset_displace[0] = 0

    if self.offset_type == 'RELATIVE':
        array.use_constant_offset = False
        # if self.offset_relative == 0:
        #     self.report({'WARNING'}, 'Your offset is set to 0')
        array.relative_offset_displace[2] = self.offset_relative
        self.prev_offset_relative         = self.offset_relative

    elif self.offset_type == 'CONSTANT':
        array.use_constant_offset = True
        array.constant_offset_displace[2] = self.offset_constant
    
    # Curve Modifier >>
    deform = modifiers.curve(ob, curve=curve)

    context.view_layer.update()

    ob.curvebash.offset_type = self.offset_type
    ob.curvebash.offset_relative = self.offset_relative
    ob.curvebash.offset_constant = self.offset_constant

    return array, deform


def get_caps(self, context, ob, meshes):
    active = context.object

    start_cap = objects.find(active.curvebash.get('start_cap'))
    end_cap = objects.find(active.curvebash.get('end_cap'))

    return start_cap, end_cap


def create_caps(self, context, ob, meshes):
    self.start_cap = None
    self.end_cap = None
    
    # Didn't find any reference to cap objects. Try to create them.
    # if not self.start_cap and not self.end_cap:
    if len(meshes) > 1:
        if ob.curvebash.get('strain') != 'FAST_FOOD':
            self.start_cap = objects.duplicate_object(context,  meshes[1], suffix='_in', linked=False, hidden=False)
            meshes[1].select_set(False)
            if addon.debug():
                print('cap 1 from mesh 1')

        if len(meshes) > 2:
            if ob.curvebash.get('strain') != 'FAST_FOOD':
                self.end_cap = objects.duplicate_object(context,  meshes[2], suffix='_in', linked=False, hidden=False)
                meshes[2].select_set(False)
                if addon.debug():
                    print('cap 2 from mesh 2')

        else:
            if self.start_cap:
                self.end_cap = objects.duplicate_object(context, self.start_cap, suffix='_in', linked=False, hidden=False)
                # self.end_cap.name = self.start_cap.name + '_rev'
                transforms.rotate_and_apply(self.end_cap, angle=180)
                if addon.debug():
                    print('cap 2 from dup cap 1')

    else:
        if addon.debug():
            print('not enough selected objects to create caps, try getting them from self caps')
        
        if self.start_cap is not None and self.end_cap is not None:
            self.start_cap = objects.duplicate_object(context, self.start_cap, suffix='_in', linked=False, hidden=False)
            self.end_cap   = objects.duplicate_object(context, self.end_cap,   suffix='_in', linked=False, hidden=False)

            # self.start_cap.select_set(False)
            # self.end_cap.select_set(False)

            if addon.debug():
                print('active has caps, duplicate from that')
        else:
            if addon.debug():
                print('and active caps are set to None so do nothing I guess')
            pass
    
    # context.view_layer.update()
    # if self.start_cap is not None:
    #     transforms.center_origin(self.start_cap)
    #     print('centered start cap')
    # if self.end_cap is not None:
    #     transforms.center_origin(self.end_cap)
    #     print('centered end cap')


def reposition(self, context, ob, curve, place='CENTER', slide=0, flip=False):
    curve_mod = ob.modifiers.get('CB Curve') 
    if curve_mod: 
        curve_mod.show_viewport = False
    else:
        if addon.debug():
            print('this thing has no curve modifier')
            self.report({'WARNING'}, 'Expected curve modifier not found')

    context.view_layer.update()

    array_len = ob.dimensions.copy().z
    mesh_len  = ob.data.dimensions.z * ob.scale.z       # Mesh data dims are local, hence the mult.
    curve_len = curve.data.splines[0].calc_length()

    if curve_mod: 
        curve_mod.show_viewport = True
    
    start_cap_len = 0
    if self.start_cap is not None:
        start_cap_len = self.start_cap.data.dimensions.z

    end_cap_len = 0
    if self.end_cap is not None:
        end_cap_len = self.end_cap.data.dimensions.z

    if place == 'START':
        pos = mesh_len/2 + start_cap_len

    elif place == 'CENTER':
        pos = mesh_len/2 + start_cap_len + curve_len/2 - array_len/2

    elif place == 'END':
        pos = mesh_len/2 + curve_len - array_len + end_cap_len

    if flip:
        ob.rotation_euler.x = pi
        pos += array_len - mesh_len - start_cap_len - end_cap_len
        ob.curvebash.flip = True

    else:
        ob.rotation_euler.x = 0

    offset = 0
    if self.start_cap is not None:
        if self.offset_type == 'RELATIVE':
            offset = mesh_len * (self.offset_relative-1)
        elif self.offset_type == 'CONSTANT':
            offset = self.offset_constant

    ob.location = (0, 0, pos + slide + offset)

    ob.curvebash.place = place
    ob.curvebash.slide = slide
    ob.curvebash.flip  = flip


class CurvebashSettings(bpy.types.PropertyGroup):
    strain : StringProperty()
    curve  : StringProperty()

    place  : StringProperty()
    slide  : FloatProperty()
    flip   : BoolProperty()

    scale  : FloatProperty()
    rotation  : FloatProperty()
    
    # mesh_scale : FloatProperty()

    start_cap : StringProperty()
    end_cap   : StringProperty()

    offset_type : StringProperty()
    offset_relative : FloatProperty()
    offset_constant : FloatProperty()


class CURVEBASH_OT_mesh_to_curvebash(bpy.types.Operator):
    '''Apply a mesh to a curve plus array options.\nSHIFT + LMB - Mesh to Curve Endpoints instead.

(www.armoredColony.com)'''
    bl_idname = 'curvebash.mesh_to_curvebash'
    bl_label  = 'Mesh to Curve'
    bl_options = {'REGISTER', 'UNDO'}
# 

    def reset_placement(self, context):
        if self.placement == {'START'}:
            self.place = 'START'

        elif self.placement == {'CENTER'}:
            self.place = 'CENTER'
        
        elif self.placement == {'END'}:
            self.place = 'END'
        
        self.slide=0
        self.property_unset('placement')
        return None


    def update_offset_type(self, context):
        if self.offset_type == 'RELATIVE':
            self.prev_offset_constant = self.offset_constant 

            if self.offset_relative != self.prev_offset_relative:
                self.offset_relative = self.prev_offset_relative
            
            self.using_constant = False
                
        elif self.offset_type == 'CONSTANT':
            self.offset_relative = 1

        return None


    mode : StringProperty()

    fit_type : EnumProperty(
        name='Array Type',
        default='FIXED_COUNT',
        items=[ ('FIXED_COUNT', 'Fixed Count', 'Control the array count manually'),
                ('FIT_CURVE', 'Fit to Curve', 'Match the array count to the curve length (aproximation, combine with "Stretch Fit" for a perfect fit)'),
            ]
        )

    count : IntProperty(
        name='Count',
        description='Array element count',
        default=1,
        min=1,
        soft_max=50,
        )

    place : StringProperty(name='Place', default='CENTER')
    placement : EnumProperty(
        name='Move to',
        update=reset_placement,
        default=set(),
        options={'ENUM_FLAG'},
        items=[ ('START', 'Start', 'Move mesh to curve start',),
                ('CENTER', 'Center', 'Move mesh to curve center'),
                ('END', 'End', 'Move mesh to curve End'), 
            ]
        )

    offset_type : EnumProperty(
        name='Offset Type',
        # update=update_offset_type,
        default='RELATIVE',
        items=[ ('RELATIVE', 'Relative', 'Based on mesh dimensions'),
                ('CONSTANT', 'Constant', 'Based on an absolute value'),
            ]
        )

    offset_relative : FloatProperty(name='Offset', default=1,
            description='Relative separation between array elements',)

    offset_constant : FloatProperty(name='Offset', default=0,
            description='Constant separation between array elements')

    using_constant :  BoolProperty(default=False)
    prev_offset_relative : FloatProperty(default=1)
    prev_offset_constant : FloatProperty(default=0)

    merge : BoolProperty(name='Merge Vertices', default=True,
            description='Merge vertices in adjacent duplicates')

    scale : FloatProperty(name='Scale', default=1.0,
            description='Mesh Scale',
            precision=2, step=0.1, min=0.1, soft_min=0.01)

    rotation : FloatProperty(name='Rotation', default=0,
            description='Rotation in degrees',
            precision=0, step=10)

    slide : FloatProperty(name='Slide', default=0,
            description='Slide along curve',
            precision=2, step=0.5)

    flip : BoolProperty(name='Reverse', default=False,
            description='Reverse direction of the Mesh/Array (only noticeable with asymmetrical meshes)')

    stretch_to_fit : BoolProperty(name='Stretch-fit (disables Slide)', default=False,
            description='Stretch the Array to fit perfectly withink the bounds of the curve (cannot slide while this is enabled)')
    # rot  : FloatProperty(name='Rot', default=0)


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row()
        row.prop(self, 'fit_type', expand=True)

        col = layout.column()
        col.enabled = True if self.fit_type == 'FIXED_COUNT' else False
        col.prop(self, 'count')
        layout.separator()

        layout.prop(self, 'scale')
        layout.prop(self, 'rotation')
        layout.separator()

        layout.prop(self, 'slide'); #row.prop(self, 'center', text='', icon='FAKE_USER_OFF')
        row = layout.row(align=True)
        row.prop(self, 'placement', expand=True)
        layout.separator()

        layout.prop(self, 'flip', toggle=True, expand=True)
        layout.separator()

        row = layout.row()
        row.prop(self, 'offset_type', expand=True)

        if self.offset_type == 'RELATIVE':
            layout.prop(self, 'offset_relative')
            if self.offset_relative == 0:
                layout.label(text='(Relative offset of 0 can create overlapping geo)')

        elif self.offset_type == 'CONSTANT':
            layout.prop(self, 'offset_constant')
        
        elif self.offset_type == 'BOTH':
            layout.prop(self, 'offset_relative')
            layout.prop(self, 'offset_constant')

        layout.separator()

        layout.prop(self, 'merge')
        layout.separator()

        col = layout.column(heading='Curve Settings', align=True)
        col.prop(self, 'stretch_to_fit')
        # col.prop(self, 'stretch')
        # col.prop(self, 'bounds_clamp')

#

    def invoke(self, context, event):
        print(f'addon debug {addon.debug()}')
        # print('INVOKED')

        # Get the starting values from the active object
            
        meshes = [ob for ob in context.selected_objects if ob.type == 'MESH']

        if not meshes:
            self.report({'ERROR'}, 'Select a single Mesh')
            return {'FINISHED'}
        
        # for mesh in meshes:
        #     transforms.center_origin(mesh)
            # center = mesh.bounds_center.copy()
        #     transforms.apply_transforms(mesh)
            # transforms.move_origin(mesh, center)

        active = meshes[0]
        if context.object in meshes:
            active = context.object

        array = active.modifiers.get('CB Array')

        # Get everything we need from the array instead of the properties.
        if array is not None:
            self.fit_type = array.fit_type
            self.count = array.count

            self.offset_relative = array.relative_offset_displace[2]
            self.offset_constant = array.constant_offset_displace[2]

        # self.scale = 1

        # self.start_cap = context.scene.objects.get(str(active.curvebash.get('start_cap')))
        # self.end_cap   = context.scene.objects.get(str(active.curvebash.get('end_cap')))
        self.start_cap = objects.retrieve(context, active.curvebash.get('start_cap'))
        self.end_cap   = objects.retrieve(context, active.curvebash.get('end_cap'))
        if addon.debug():
            print(f'active\'s caps {self.start_cap}, {self.end_cap}')

        self.place = active.curvebash.get('place', self.place)
        self.slide = active.curvebash.get('slide', self.slide)
        self.flip  = active.curvebash.get('flip',  self.flip)
        
        self.scale = active.curvebash.get('scale', self.scale)
        self.rotation = active.curvebash.get('rotation', self.rotation)
        
        # self.scale = active.data.get('uniform_scale', self.scale)
        # self.scale = active.rotation.z

        self.offset_type = active.curvebash.get('offset_type', self.offset_type)


        # MODE OVERRIDES
        if event.shift:
            self.mode = 'ENDPOINTS'
            self.count = 1
            self.fit_type = 'FIXED_COUNT'
            self.slide = 0
            self.start_cap = None
            self.end_cap = None

        if self.mode in {'ADD', 'ENDPOINTS'}:
            curves = [ob for ob in context.selected_objects if ob.type == 'CURVE']

            if not curves:
                self.report({'ERROR'}, 'Select at least 1 curve')
                return {'FINISHED'}

        bpy.ops.ed.undo_push()
        return self.execute(context)


    def execute(self, context):
        meshes = [ob for ob in context.selected_objects if ob.type == 'MESH']

        active = meshes[0]
        if context.object in meshes:
            active = context.object
        
        # Extra stuff for specific modes.
        if self.mode in {'ADD', 'ENDPOINTS'}:
            curves = [c for c in context.selected_objects if c.type == 'CURVE' and c.get('type') != 'profile']  # Ignore curve profiles

            for curve in curves:
                curve.data.transform(curve.matrix_world)
                curve.matrix_world = Matrix()

            # EXTRA
            # -------------------------------------------------------------------
            for curve in curves:
                curve.data.use_stretch = self.stretch_to_fit
                curve.data.use_deform_bounds = self.stretch_to_fit

        # -------------------------------------------------------------------

        if self.mode == 'ADD':

            if active == context.object:
                active.select_set(False)
            
            # Will leave this enabled for now and worry about ramifications later >_>
            # for mesh in meshes:
                # transforms.center_origin(mesh)

            for curve in curves:
                ob = objects.duplicate_object(context, active, linked=False)   
                ob.curvebash.curve = curve.name
                # transforms.center_origin(ob)

                create_caps(self, context, ob, meshes)    # Does nothing if no reference to cap objects are found.

                # transforms.scale_mesh(ob, self.scale)
                ob.data.uniform_scale = self.scale
                ob.curvebash.scale = self.scale
                if self.start_cap and self.end_cap:
                    self.start_cap.data.uniform_scale = self.scale
                    self.end_cap.data.uniform_scale = self.scale
                    # transforms.scale_mesh(self.start_cap, self.scale)
                    # transforms.scale_mesh(self.end_cap, self.scale)
                
                ob.rotation_euler.z = radians(self.rotation)
                ob.curvebash.rotation = self.rotation
                
                array, _ = add_modifiers(self, context, ob, curve, fit_type=self.fit_type, count=self.count)
                # ob.location = (0, 0, 0)
                # if array.fit_type == 'FIXED_COUNT':
                reposition(self, context, ob, curve, place=self.place, slide=self.slide, flip=self.flip)

                # curve.data.bevel_depth = 0
                ob['curve'] = curve.name
                # curve['mesh_scale'] = self.scale
                # if not curve.get('geo'):
                # curve['mode'] = 2
                # curve['index'] = -1
                # curve['geo'] = ob.name
                ob.curvebash.strain = 'FAST_FOOD'
                context.view_layer.objects.active = ob     
                curve.select_set(False)
            
            # TESTING SHIT
            context.view_layer.update()
        
        elif self.mode == 'ENDPOINTS':
            
            for curve in curves:
                ob1 = objects.duplicate_object(context, active, linked=False)   
                ob2 = objects.duplicate_object(context, active, linked=False)

                # I believe this doesn't work because the bounding box changes when applied toa curve,
                # So the centering based on bounding boxes fails.
                # transforms.center_origin(ob1)
                # transforms.center_origin(ob2)

                transforms.scale_mesh(ob1, self.scale)  
                transforms.scale_mesh(ob2, self.scale)  
                ob1.rotation_euler.z = radians(self.rotation)
                ob2.rotation_euler.z = radians(self.rotation)

                ob1.curvebash.curve = curve.name
                ob2.curvebash.curve = curve.name
                
                # Fit is FIXED and count is 1 (check Invoke).
                add_modifiers(self, context, ob1, curve, fit_type=self.fit_type, count=self.count)
                add_modifiers(self, context, ob2, curve, fit_type=self.fit_type, count=self.count)

                reposition(self, context, ob1, curve, place='START', slide= self.slide, flip=False)
                reposition(self, context, ob2, curve, place='END',   slide=-self.slide, flip=True)

                ob1.curvebash.strain = 'FAST_FOOD'
                ob2.curvebash.strain = 'FAST_FOOD'
                context.view_layer.objects.active = ob1  
                curve.select_set(False)

        elif self.mode == 'EDIT':
            editable_meshes = [ob for ob in meshes if ob.curvebash.strain == 'FAST_FOOD']

            if not editable_meshes:
                self.report({'ERROR'}, 'No Editable Curvebash was found')
                return {'FINISHED'}

            for ob in editable_meshes:
                curve_name = ob.curvebash.get('curve')
                curve = context.scene.objects.get(curve_name)

                if curve is None:
                    del ob['curvebash']
                    self.report({'ERROR'}, 'Failed to Edit Curvebash [missing original curve]')
                    return {'FINISHED'}

                curve.data.use_stretch = self.stretch_to_fit
                curve.data.use_deform_bounds = self.stretch_to_fit

                self.start_cap, self.end_cap = get_caps(self, context, ob, meshes)

                # NOT SURE IF THIS SHOULD CREATE CAPS
                # USEFUL FOR ADDING CAPS TO A PRE-EXISTING ARRAY?
                # DOES NOT EVEN WORK XD!!!
                # if not self.start_cap or not self.end_cap:
                #     if addon.debug():
                #         print('get caps is None, try to create')
                #     create_caps(self, context, ob, editable_meshes)    # Sets caps to None if no geo is available to use.
                # else:
                #     if addon.debug():
                #         print('skip cap creation')
                
                ob.data.uniform_scale = self.scale
                ob.curvebash.scale = self.scale
                if self.start_cap and self.end_cap:
                    self.start_cap.data.uniform_scale = self.scale
                    self.end_cap.data.uniform_scale = self.scale
                
                ob.rotation_euler.z = radians(self.rotation)
                ob.curvebash.rotation = self.rotation

                add_modifiers(self, context, ob, curve, fit_type=self.fit_type, count=self.count)
                reposition(self, context, ob, curve, place=self.place, slide=self.slide, flip=self.flip)

                ob.curvebash.strain = 'FAST_FOOD'
                curve.select_set(False)

        return {'FINISHED'}


def draw_menu(self, context):
    ob = context.object
    strain = ob.curvebash.get('strain') if ob is not None else ''

    layout = self.layout
    layout.separator()
    layout.operator_context = 'INVOKE_DEFAULT'

    layout.operator(CURVEBASH_OT_mesh_to_curvebash.bl_idname, text='Mesh to Curvebash').mode = 'ADD'

    if strain == 'FAST_FOOD':
        layout.operator(CURVEBASH_OT_mesh_to_curvebash.bl_idname, text='Edit Curvebash').mode = 'EDIT'


classes = (
    CURVEBASH_OT_mesh_to_curvebash,
    CurvebashSettings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_menu)
    bpy.types.Object.curvebash = bpy.props.PointerProperty(type=CurvebashSettings)
    

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_menu)
    del bpy.types.Object.curvebash
