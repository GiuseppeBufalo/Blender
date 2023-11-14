import bpy
from .. items import mirror_props



def add_displace(obj, height=None):
    displace = obj.modifiers.new(name="Displace", type="DISPLACE")

    displace.mid_level = bpy.context.scene.DM.height if height is None else height
    displace.show_in_editmode = True
    displace.show_on_cage = True
    displace.show_expanded = False

    return displace


def add_nrmtransfer(obj, target=None):
    nrmtransfer = obj.modifiers.new("NormalTransfer", "DATA_TRANSFER")

    nrmtransfer.object = target
    nrmtransfer.use_loop_data = True
    nrmtransfer.data_types_loops = {'CUSTOM_NORMAL'}
    nrmtransfer.loop_mapping = 'POLYINTERP_LNORPROJ'
    nrmtransfer.show_expanded = False

    obj.data.use_auto_smooth = True

    return nrmtransfer


def add_subd(obj):
    subd = obj.modifiers.new(name="Subdivision", type="SUBSURF")

    subd.subdivision_type = 'SIMPLE'
    subd.levels = 3
    subd.render_levels = 3
    subd.quality = 1
    subd.show_expanded = False


def add_shrinkwrap(obj, target):
    shrinkwrap = obj.modifiers.new(name="Shrinkwrap", type="SHRINKWRAP")

    shrinkwrap.target = target
    shrinkwrap.wrap_method = 'PROJECT'
    shrinkwrap.use_negative_direction = True
    shrinkwrap.show_expanded = False


def add_boolean(obj, target, method='UNION', solver='FAST'):
    boolean = obj.modifiers.new(name=method.title(), type="BOOLEAN")

    boolean.object = target
    boolean.operation = method
    boolean.solver = solver

    return boolean


def add_solidify(obj, thickness=0.01):
    solidify = obj.modifiers.new(name="Solidify", type="SOLIDIFY")

    solidify.thickness = thickness

    return solidify


def add_triangulate(obj, keep_normals=True):
    triangulate = obj.modifiers.new(name="Triangulate", type="TRIANGULATE")
    triangulate.keep_custom_normals = keep_normals
    return triangulate


def add_mods_from_dict(obj, modsdict):
    for name, props in modsdict.items():
        mod = obj.modifiers.new(name=name, type=props['type'])

        for pname, pvalue in props.items():
            if pname != 'type':
                setattr(mod, pname, pvalue)



def get_displace(obj):
    displacemods = [mod for mod in obj.modifiers if mod.type == "DISPLACE"]

    if displacemods:
        return displacemods[0]


def get_nrmtransfer(obj, create=True):
    nrmtransfermods = [mod for mod in obj.modifiers if mod.type == "DATA_TRANSFER" and any([mod.name == name for name in ["NormalTransfer", "NormalUVTransfer"]])]

    if nrmtransfermods:
        return nrmtransfermods[0]
    if create:
        return add_nrmtransfer(obj, target=obj.parent)


def get_uvtransfer(obj):
    uvtransfermods = [mod for mod in obj.modifiers if mod.type == "DATA_TRANSFER" and mod.name == "NormalUVTransfer"]

    if uvtransfermods:
        return uvtransfermods[0]


def get_subd(obj):
    subdmods = [mod for mod in obj.modifiers if mod.type == "SUBSURF"]

    if subdmods:
        return subdmods[0]


def get_shrinkwrap(obj):
    shrinkwrapmods = [mod for mod in obj.modifiers if mod.type == "SHRINKWRAP"]

    if shrinkwrapmods:
        return shrinkwrapmods[0]


def get_mod_as_dict(mod):
    d = {}

    if mod.type == 'MIRROR':
        for prop in mirror_props:
            if prop in ['use_axis', 'use_bisect_axis', 'use_bisect_flip_axis']:
                d[prop] = tuple(getattr(mod, prop))
            else:
                d[prop] = getattr(mod, prop)

    return d


def get_mods_as_dict(obj, types=[]):
    mods = []

    for mod in obj.modifiers:
        if types:
            if mod.type in types:
                mods.append(mod)

        else:
            mods.append(mod)

    modsdict = {}

    for mod in mods:
        modsdict[mod.name] = get_mod_as_dict(mod)

    return modsdict
