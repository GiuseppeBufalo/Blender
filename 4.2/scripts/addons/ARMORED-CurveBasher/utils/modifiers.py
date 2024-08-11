import bpy

from .. utils import addon
from .. utils import objects


def array(ob, curve=None):
    mod = ob.modifiers.get('CB Array')
    if mod is None:
        mod = ob.modifiers.new('CB Array', type='ARRAY')

    mod.relative_offset_displace[0] = 0
    mod.relative_offset_displace[1] = 0
    mod.relative_offset_displace[2] = 1

    mod.constant_offset_displace[0] = 0
    mod.constant_offset_displace[1] = 0
    mod.constant_offset_displace[2] = 1

    mod.merge_threshold = 0.001
    if curve:
        mod.curve = curve
    mod.use_merge_vertices = True
    mod.fit_type = 'FIT_CURVE'
    mod.show_in_editmode = False
    mod.show_on_cage = True
    # modArray.fit_type = 'FIXED_COUNT'
    # modArray.count = 10

    return mod


def curve(ob, curve=None):
    mod = ob.modifiers.get('CB Curve')
    if mod is None:
        mod = ob.modifiers.new('CB Curve', type='CURVE')

    if curve is not None:
        mod.object = curve
    mod.deform_axis = 'POS_Z'
    mod.show_in_editmode = False
    mod.show_on_cage = True

    return mod


def apply_subsurf_modifiers(self, context, obj, levels = 2, render_levels = 3):
    mod = obj.modifiers.new("CB Subdivision", type = "SUBSURF")

    mod.render_levels = render_levels
    mod.levels = levels
    mod.show_only_control_edges = True


def apply_infinite_modifiers(self, context, obj, curve):
    modArray = obj.modifiers.new("CB Array", type = "ARRAY")

    modArray.relative_offset_displace[0] = 0
    modArray.relative_offset_displace[1] = 0
    modArray.relative_offset_displace[2] = 1
    modArray.merge_threshold = 0.0001
    modArray.curve = curve
    modArray.use_merge_vertices = True

    # modArray.fit_type = 'FIT_CURVE'
    modArray.fit_type = self.array_type
    modArray.count = self.array_count

    modCurve = obj.modifiers.new("CB Curve", type = "CURVE")

    modCurve.object = curve
    modCurve.deform_axis = 'POS_Z'
    modCurve.show_in_editmode = True

    # self.cap1 = bpy.data.objects.get(str(curve.get('cap1')))
    # self.cap2 = bpy.data.objects.get(str(curve.get('cap2')))

    if addon.get_prefs().array_caps:
        modArray.start_cap = self.cap1
        modArray.end_cap = self.cap2
    else:
        modArray.start_cap = None
        modArray.end_cap = None
    # from .. utils import transforms
    # transforms.scale_mesh(cap, .1)


def apply_kitbash_modifiers(self, context, obj, curve):
    modCurve = obj.modifiers.new("CB Curve", type = "CURVE")

    modCurve.object = curve
    modCurve.deform_axis = 'POS_Z'


def apply_modifiers(self, context, obj, curve):
    mode = curve['mode']

    if mode == 1:
        curve.data.bevel_object = obj

    if mode == 2:
        apply_infinite_modifiers(self, context, obj, curve)

    if mode == 3:
        apply_kitbash_modifiers(self, context, obj, curve)


def toggle_array_fit_type(current):
    if current == 'FIT_CURVE':
        return 'FIXED_COUNT'

    if current == 'FIXED_COUNT':
        return 'FIT_CURVE'
    
    return 'FIT_CURVE'


def set_array_fit_type(self, context, state='FIT_CURVE'):
    for curve in self.selection:
        ob = objects.retrieve(context, curve.get('geo'))
        if ob is None:
            continue

        array = ob.modifiers.get('CB Array')
        if not array:
            continue

        array.fit_type = state


def set_array_caps(self, context, bool_state):
    for curve in self.selection:
        ob = objects.retrieve(context, curve.get('geo'))
        if ob is None:
            continue
        
        cap1 = objects.find(ob.get('cap1'))
        cap2 = objects.find(ob.get('cap2'))
        
        array = ob.modifiers.get('CB Array')
        if not array:
            continue

        if bool_state:
            array.start_cap = cap1
            array.end_cap = cap2
        else:
            array.start_cap = None
            array.end_cap = None