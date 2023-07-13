import bpy

from bpy.utils import register_class, unregister_class

from ..... utility import addon
from .... utility import adjust_shapez_to_solver
from .... import toolbar
from .... operator.property import operation
from .... operator.shape.utility.modal.mode import change

sort_options = (
    'sort_modifiers',
    'sort_bevel',
    'sort_array',
    'sort_mirror',
    'sort_solidify',
    'sort_weighted_normal',
    'sort_simple_deform',
    'sort_triangulate',
    'sort_decimate',
    'sort_remesh',
    'sort_subsurf',
    'sort_bevel_last',
    'sort_array_last',
    'sort_mirror_last',
    'sort_solidify_last',
    'sort_weighted_normal_last',
    'sort_simple_deform_last',
    'sort_triangulate_last',
    'sort_decimate_last',
    'sort_remesh_last',
    'sort_subsurf_last')


def sync_sort(behavior, context):
    for option in sort_options:
        if addon.hops() and hasattr(addon.hops().property, option):
            addon.hops().property[option] = getattr(behavior, option)
        else:
            print(F'Unable to sync sorting options with Hard Ops; Box Cutter {option}\nUpdate Hard Ops!')

        if addon.kitops() and hasattr(addon.kitops(), option):
            addon.kitops()[option] = getattr(behavior, option)
        else:
            print(F'Unable to sync sorting options with KIT OPS; Box Cutter {option}\nUpdate KIT OPS!')


def sort_ignore_char(behavior, context):
    if not behavior.sort_ignore_char:
        behavior.sort_ignore_char = ' '

    sync_sort(behavior, context)


def sort_stop_char(behavior, context):
    if not behavior.sort_stop_char:
        behavior.sort_stop_char = '_'

    sync_sort(behavior, context)


def simple_topbar(display, context):
    toggle = not display.simple_topbar
    display.topbar_pad = toggle
    display.pad_menus = toggle


def release_lock(keymap, context):
    bpy.ops.bc.release_lock('INVOKE_DEFAULT')


def tab(display, context):
    from .... panel import classes as panels

    for panel in panels:
        if hasattr(panel, 'bl_category') and panel.bl_category and panel.bl_category != 'Tool':
            unregister_class(panel)
            panel.bl_category = display.tab
            register_class(panel)


def shape_type(behavior, context):
    op = toolbar.option()

    # if op.shape_type != 'BOX' and behavior.draw_line:
    #     op.shape_type = 'BOX'


def shift_operation_preset(shift_operation, context):
    preference = addon.preference()
    preference.keymap['shift_operation_preset'] = shift_operation.name


def shift_operation_presets(keymap, context):
    preset = keymap.shift_operation_preset

    if preset:
        keymap.shift_operation_presets[preset].operation = keymap.shift_operation


def shift_in_operation(_, context):
    preference = addon.preference()

    if not preference.keymap.shift_operation_preset:
        return

    preset = preference.keymap.shift_operation_presets[preference.keymap.shift_operation_preset]

    for shift_operation in operation.shift_operations:
        preset[shift_operation.lower()] = getattr(preference.keymap.shift_in_operations, shift_operation.lower())


def shift_operation(keymap, context):
    preset_name = keymap.shift_operation_preset

    preset = None

    if preset_name:
        preset = keymap.shift_operation_presets[preset_name]

        if keymap.shift_operation != preset.operation:
            keymap.shift_operation = preset.operation

        for shift_operation in operation.shift_operations:
            keymap.shift_in_operations[shift_operation.lower()] = getattr(preset, shift_operation.lower())


def rebool(_, context):
    bc = context.scene.bc

    if not bc.running:
        return

    operator = bc.operator

    event = type('fake_event', (), {'ctrl' : False, 'shift' : False, 'alt' : False})
    change(operator, context, event, to=operator.mode, force=True)


def boolean_solver(behavior, context):
    bc = context.scene.bc

    if not bc.running or not bpy.app.version[:2] >= (2, 91):
        return

    operator = bc.operator

    if operator.mode == 'INSET':
        for target, inset in zip(operator.datablock['targets'], operator.datablock['insets']):
            for mod in reversed(target.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is inset:
                    mod.solver = behavior.boolean_solver
                    break

            for mod in reversed(inset.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is bc.shape:
                    mod.solver = behavior.boolean_solver
                    break

        for slice, inset in zip(operator.datablock['slices'], operator.datablock['insets']):
            for mod in reversed(slice.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is inset:
                    mod.solver = behavior.boolean_solver
                    break

        #<< elif operator.mode == 'JOIN':
        #<<     for obj in operator.datablock['targets'] + operator.datablock['slices']:
        #<<         for mod in reversed(obj.modifiers):
        #<<             if mod.type == 'BOOLEAN' and mod.object is bc.shape:
        #<<                 # mod.solver = 'EXACT' if addon.preference().behavior.join_exact else behavior.boolean_solver
        #<<                 mod.solver = behavior.boolean_solver
        #<<                 break

    else:
        for obj in operator.datablock['targets'] + operator.datablock['slices']:
            for mod in reversed(obj.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is bc.shape:
                    mod.solver = behavior.boolean_solver
                    break


    bc = context.scene.bc
    op = bc.operator

    adjust_shapez_to_solver(behavior, bc, op)

