import bpy



def add_shrinkwrap(obj, target, vgroup):
    shrinkwrap = obj.modifiers.new(name="Shrinkwrap", type="SHRINKWRAP")

    shrinkwrap.target = target
    shrinkwrap.wrap_method = 'NEAREST_VERTEX'
    shrinkwrap.vertex_group = vgroup
    shrinkwrap.show_expanded = False
    shrinkwrap.show_on_cage = True


def add_boolean(obj, operator, method='DIFFERENCE', solver='FAST'):
    boolean = obj.modifiers.new(name=method.title(), type="BOOLEAN")

    boolean.object = operator
    boolean.operation = 'DIFFERENCE' if method == 'SPLIT' else method
    boolean.show_in_editmode = True

    if method == 'SPLIT':
        boolean.show_viewport = False

    boolean.solver = solver

    return boolean


def add_displace(obj, name="Displace", mid_level=0, strength=0):
    displace = obj.modifiers.new(name=name, type="DISPLACE")
    displace.mid_level = mid_level
    displace.strength = strength

    displace.show_expanded = False

    return displace



def apply_mod(modname):
    bpy.ops.object.modifier_apply(modifier=modname)



def get_mod_obj(mod):
    if mod.type in ['BOOLEAN', 'HOOK', 'LATTICE', 'DATA_TRANSFER']:
        return mod.object
    elif mod.type == 'MIRROR':
        return mod.mirror_object
    elif mod.type == 'ARRAY':
        return mod.offset_object


def get_mod_objects(obj, mod_objects, mod_types=['BOOLEAN', 'MIRROR', 'ARRAY', 'HOOK', 'LATTICE', 'DATA_TRANSFER'], recursive=True, depth=0, debug=False):
    depthstr = " " * depth

    if debug:
        print(f"\n{depthstr}{obj.name}")

    for mod in obj.modifiers:
        if mod.type in mod_types:
            mod_obj = get_mod_obj(mod)

            print(f" {depthstr}mod: {mod.name} | obj: {mod_obj.name if mod_obj else mod_obj}")

            if mod_obj:
                if mod_obj not in mod_objects:
                    mod_objects.append(mod_obj)

                if recursive:
                    get_mod_objects(mod_obj, mod_objects, mod_types=mod_types, recursive=True, depth=depth + 1, debug=debug)
