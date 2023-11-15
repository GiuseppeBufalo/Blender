import traceback
import bpy

from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as view3d_tools

name = __name__.partition('.')[0]


def active_tool():
    return view3d_tools.tool_active_from_context(bpy.context)


def operator_override(context, op, override, *args, **kwargs):
    if not hasattr(context, 'temp_override'):
        return op({**override}, *args, **kwargs)

    with context.temp_override(**override):
        return op(*args, **kwargs)


def method_handler(method,
    arguments = tuple(),
    identifier = str(),
    exit_method = None,
    exit_arguments= tuple(),
    return_result = False,
    return_value = {'CANCELLED'}):
    '''
    method: method to call
    arguments: method arguments
    identifier: optional identifer for printout
    exit_method: optional exit method to call on exception
    exit_arguments: exit method arguments
    return_result: allows return of the method and values
    return_value: return value on exception
    '''
    identifier = identifier + ' ' if identifier else ''
    try:
        if return_result:
            return method(*arguments)
        else:
            method(*arguments)
    except Exception:
        print(F'\n{name} {identifier}Method Failed:\n')
        traceback.print_exc()

        if exit_method:
            try:
                if return_result:
                    return exit_method(*exit_arguments)
                else:
                    exit_method(*exit_arguments)
            except Exception:
                print(F'\n{name} {identifier}Exit Method Failed:\n')
                traceback.print_exc()

        if return_result:
            try: return return_value
            except Exception:
                print(F'\n{name} {identifier}Exit Return Value Failed:\n')
                traceback.print_exc()
