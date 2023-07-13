import bpy

from .. utils import addon
from .. utils import objects


def set_cap_smoothing(self, context, bool_state):
    for curve in self.selection:
        ob = objects.retrieve(context, curve.get('geo'))

        if ob is None:
            continue

        cap1 = objects.find(ob.get('cap1'))
        cap2 = objects.find(ob.get('cap2'))

        if cap1 is not None:
            for f in cap1.data.polygons:
                f.use_smooth = bool_state

        if cap2 is not None:
            for f in cap2.data.polygons:
                f.use_smooth = bool_state


def set_wireframe(self, bool_state):
    for curve in self.selection:
        curve.show_wire = bool_state
        if curve.get('geo'):
            bpy.data.objects[curve['geo']].show_wire = bool_state


def set_autosmooth(self, bool_state):
     for curve in self.selection:
        if curve.get('mode') in {2, 3}:
            bpy.data.objects[curve['geo']].data.use_auto_smooth = bool_state


def set_smoothing(self, context, state):
    if state == 'ANGLE':
        bpy.ops.object.shade_smooth()
        set_autosmooth(self, True)
        set_cap_smoothing(self, context, True)

    elif state == 'SMOOTH':
        bpy.ops.object.shade_smooth()
        set_autosmooth(self, False)
        set_cap_smoothing(self, context, True)

    elif state == 'FLAT':
        bpy.ops.object.shade_flat()
        set_autosmooth(self, False)
        set_cap_smoothing(self, context, False)


# def set_smoothing(self, bool_state):
#     if bool_state:
#         bpy.ops.object.shade_smooth()
#     else:
#         bpy.ops.object.shade_flat()

#     for i, curve in enumerate(self.selection):
#         if curve['mode'] in {2, 3}:
#             # bpy.data.objects[curve['geo']].data.use_auto_smooth = bool_state
#             bpy.data.objects[curve['geo']].data.use_auto_smooth = False


def toggle_stretch(self):
    # Use global master curve as reference before toggling:
    bool_state = self.master_curve.data.use_stretch

    for curve in self.selection:
        curve.data.use_stretch = not bool_state
        curve.data.use_deform_bounds = not bool_state   # These props should always have the same val


def set_stretch(self, bool_state):
    addon.get_prefs().stretch = bool_state
    for curve in self.selection:
        curve.data.use_stretch = bool_state
        curve.data.use_deform_bounds = bool_state


def reset(self, context):
    '''Some display modes should be reset when the modal ends'''
    set_wireframe(self, False)
    context.space_data.overlay.show_outline_selected = True


def load_preferences(self, context):
    set_wireframe(self, addon.get_prefs().wireframe)
    set_smoothing(self, context, addon.get_prefs().smoothing)
    # set_stretch(self, addon.get_prefs().stretch)
    
    context.space_data.overlay.show_outline_selected = addon.get_prefs().outline
    



    