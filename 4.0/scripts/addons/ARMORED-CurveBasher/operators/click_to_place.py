import bpy, bmesh
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty

from .. utils import addon
from .. utils import curve_utils
from .. utils import raycast
from .. utils import objects


class ARMORED_OT_click_place(bpy.types.Operator):
    '''Create a curve with endpoints that are oriented to the surface you click on.

(www.armoredColony.com)'''

    bl_idname = 'curvebash.raycast_curve'
    bl_label  = 'Cable Raycast'
    bl_options = {'REGISTER', 'UNDO'}

    def update_curve_sag(self, context):
        if self.sag_strength == 0:
            self.sag_strength = 0.5

    def set_handle_offset(self, context):
        if self.outer_handle_type == 'FIXED':
            self.handle_offset = 1
        elif self.outer_handle_type == 'ADAPTIVE':
            self.handle_offset = 0
            self.adaptive_strength = 0.4

    def reset_handles(self, context):
        self.property_unset('adaptive_strength')
        self.property_unset('handle_offset')
        self.property_unset('sag_strength')
        self.property_unset('reset_handles')

    def reset_all(self, context):
        self.property_unset('radius')
        self.property_unset('outer_handle_type')
        self.property_unset('adaptive_strength')
        self.property_unset('handle_offset')
        self.property_unset('resolution_u')
        self.property_unset('bevel_resolution')
        self.property_unset('curve_sag')
        self.property_unset('sag_strength')
        self.property_unset('mid_handle_type')
        self.property_unset('reset_all')
        self.property_unset('enter_edit')

    list_description = [
        'Reset all properties that affect handle positions:',
        '\u2022 Adaptive Strengths',
        '\u2022 Handle Offsets',
    ]
    packed_description =( '\n'.join(line for line in list_description) )

    # RESETS
    reset_handles : BoolProperty(name='Handles', default=False,
            description=packed_description,
            update=reset_handles)
    
    reset_all : BoolProperty(name='All', default=False,
            description='Reset everything to default values',
            update=reset_all)
    

    # CURVE SETTINGS
    radius : FloatProperty(name='Radius', default=0.1,
            description='Cable Radius',
            precision=3, min=0, step=0.2)
    
    resolution_u : IntProperty(name='Curve Segments', default=24, 
            min=1)

    bevel_resolution : IntProperty(name='Bevel Resolution', default=4, 
            min=0)


    # HANDLE SETTINGS
    outer_handle_type : EnumProperty(name='Handle Algorithm', default='ADAPTIVE',
            items=[ ('ADAPTIVE', 'Adaptive', 'Desc'),
                    ('FIXED', 'Fixed', 'Desc'), ])

    adaptive_strength : FloatProperty(name='Adaptive Strength', default=0.5,
            description='Handle size grows the farther the curve\'s endpoints are from each other', 
            precision=2, step=1)

    handle_offset : FloatProperty(name='Handle Size', default=1, 
            description='Handle Size Multiplier',
            precision=3, step=0.1)

    mid_handle_type : EnumProperty(name='Mid Handle Type', default='ALIGNED',
            items=[ ('AUTO', 'Auto', 'Handle resizes automatically the farther it is from the adjacent points'),
                    ('ALIGNED', 'Aligned', 'Fixed middle handle'), ])
    

    # GRAVITY
    curve_sag : BoolProperty(name='Gravity', default=False,
            description='Simulate gravity',
            update=update_curve_sag)

    sag_strength : FloatProperty(name='Strength', default=0.5, 
            description='Gravity Strength',
            precision=3, step=0.1)

    
    # POST OPTIONS
    keep_prev_sel : BoolProperty(name='Keep Previous Selection', default=True,
            description='Maintain the previous selection')

    enter_edit : BoolProperty(name='Enter Edit Mode', default=False,
            description='Enter Edit-mode after creating a cable',)


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row(heading='RESET')
        row.prop(self, 'reset_handles', toggle=True); row.prop(self, 'reset_all', toggle=True)
        layout.separator()
        layout.prop(self, 'radius')
        layout.separator()

        row = layout.row()
        row.prop(self, 'outer_handle_type', expand=True)
        sub1 = layout.row()
        sub1.enabled = True if self.outer_handle_type == 'ADAPTIVE' else False
        sub1.prop(self, 'adaptive_strength')

        layout.prop(self, 'handle_offset')
        # layout.prop(self, 'resolution_u')
        # layout.prop(self, 'bevel_resolution')
        layout.separator()

        layout.prop(self, 'curve_sag', toggle=True)
        sub2 = layout.column()
        sub2.enabled = True if self.curve_sag else False
        sub2.prop(self, 'sag_strength')
        row = layout.row()
        row.prop(self, 'mid_handle_type', expand=True)
        layout.separator()
        
        layout.prop(self, 'keep_prev_sel')
        layout.separator()

        layout.prop(self, 'enter_edit', toggle=True)

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object is not None

    def invoke(self, context, event):
        # if context.mode != 'OBJECT':
            # bpy.ops.object.mode_set(mode='OBJECT')
        if addon.get_prefs().rc_undo_push:
            bpy.ops.ed.undo_push()
        
        
        self.key_type = event.type
        self.key_value = event.value
        self.counter = 0
        self.locations = list()
        self.rotations = list()
        self.normals = list()
        self.marker = None

        # self.curve = curve_utils.new_bezier(self, context, handle_type='FREE')

        context.window.cursor_modal_set('PAINT_CROSS')  # modal_set to work better

        context.window_manager.modal_handler_add(self)
        # bpy.ops.ed.undo_push()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and not event.alt:

            loc, normal = raycast.cursorcast(context, rot_as_vector=True)

            self.locations.append(loc)
            self.normals.append(normal)
            
            self.counter += 1
            
            if self.counter == 1:
                self.marker = curve_utils.circle_marker(self, context, 
                    name='P1', radius=self.radius, location=loc, normal=normal)
                
            elif self.counter >= 2:
                objects.delete_object_data(self.marker)
                context.window.cursor_modal_restore()

                # EXECUTE >>
                return self.execute(context)

        # YES I SACRIFICED EFFICIENCY FOR THESE CONDITIONS:

        # Blender or Maya Navigation.
        elif (  event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE' } or 
                (event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'MOUSEMOVE'} and event.alt) or 
                event.type in {'F', 'NUMPAD_PERIOD'}):
            return {'PASS_THROUGH'}

        # Cancel or Operator's Shortcut Key pressed again.
        elif (event.type in {'RIGHTMOUSE', 'ESC'} or
            event.type == self.key_type and event.value == self.key_value):

            objects.delete_object_data(self.marker)
            context.window.cursor_modal_restore()

            self.report({'OPERATOR'}, 'CANCELLED')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        curve = curve_utils.new_normal_handle_bezier(self, context, self.locations, self.normals)
        
        curve.select_set(True)
        context.view_layer.objects.active = curve

        if self.enter_edit:
            prev_sel = context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')

            bpy.ops.object.mode_set(mode='EDIT')

            for ob in prev_sel:
                ob.select_set(True)

        return {'FINISHED'}


classes = (
    ARMORED_OT_click_place,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
