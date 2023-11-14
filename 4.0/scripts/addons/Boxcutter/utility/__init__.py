import time
import traceback

import bpy

name = __name__.partition('.')[0]
handled_error = False
error_log = []


def new_type(name='object', default=None, inherent=(), attribute={}, **keyed_argument):
    space = type(name, inherent, attribute)
    space.__new__ = default if default else lambda self: self

    for key, argument in keyed_argument.items():
        setattr(space, key, argument)

    return space


def context_copy(**kargs):
    return new_type(name='context', attribute=bpy.context.copy(), **kargs)


def debug_print(name, identifier, header=''):
    out = ''

    if header:
        global handled_error
        handled_error = True
        out = header + '\n'

    out += F'{name} {identifier} Method Failed:\n'

    for elem in traceback.format_exc().split('\n'):
        if not elem:
            continue
        out += elem + '\n'

    error_log.append(out[:-1])

    if bpy.context.preferences.addons[name].preferences.debug: # TODO: store traceback for recall on enable
        print(out)
    else:
        print(F'{name} Method Failure: Enable {name} debug preference to view error')


def method_handler(method, arguments=(), identifier='', exit_method=None, exit_arguments=(), return_result=True, return_value={'CANCELLED'}):
    try:
        if return_result:
            return method(*arguments)

        else:
            method(*arguments)

    except Exception:
        debug_print(name, identifier, header=F'\n##### METHOD HANDLER FAILURE #####')

        if exit_method:
            try:
                if return_result:
                    return exit_method(*exit_arguments)

                else:
                    exit_method(*exit_arguments)

            except Exception:
                debug_print(name, identifier, header=F'\n##### EXIT METHOD HANDLER FAILURE #####')

        if return_result:
            try:
                return return_value

            except Exception:
                debug_print(name, identifier, header=F'\n##### RETURN METHOD HANDLER FAILURE #####')


def timed_print(*args):
    if bpy.context.preferences.addons[name].preferences.debug:
        print(F'{time.perf_counter()}:', *args)
