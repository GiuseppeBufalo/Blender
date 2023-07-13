import bpy
from bpy.app.handlers import persistent
from mathutils import Vector
from . utils.curve import get_curve_as_dict, get_curve_selection
from . utils.system import printd


selection_history = []
previous_selection = set()

@persistent
def curve_selection_history(scene):
    global selection_history, previous_selection

    C = bpy.context
    active = getattr(C, 'active_object', None)


    if active and active.type == 'CURVE' and C.mode == 'EDIT_CURVE':
        data = get_curve_as_dict(active.data)
        selection = get_curve_selection(data, debug=False)

        symdiff = selection.symmetric_difference(previous_selection)

        if symdiff:
            if len(symdiff) == 1:
                change = symdiff.pop()

                if change in selection:
                    selection_history.append(change)
                else:
                    if change in selection_history:
                        selection_history.remove(change)
                    else:
                        selection_history = []
            else:
                selection_history = []

        if not selection_history and len(selection) == 1:
            selection_history = list(selection)

        previous_selection = selection
