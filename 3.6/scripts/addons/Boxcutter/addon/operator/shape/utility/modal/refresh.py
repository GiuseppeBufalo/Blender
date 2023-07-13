import bpy
from mathutils import Vector, geometry

from . import array, axis, behavior, bevel, displace, display, draw, extrude, mode, move, offset, operation, origin, ray, refresh, mirror, solidify, rotate, scale, taper, grid

# from ... import shape
from ...... utility import addon, view3d, math
# from ... import shape as _shape
from .. import modifier, mesh


def shape(op, context, event, dot=False):
    preference = addon.preference()
    wm = context.window_manager
    bc = context.scene.bc

    bound_object(op, context)

    if not bc.running or not op.bounds:
        return

    mouse = op.mouse['location'] + op.mouse['offset']
    front = (1, 2, 5, 6)
    back = (0, 3, 4, 7)

    matrix = bc.plane.matrix_world
    inverse = matrix.inverted()

    alignment = matrix.copy()
    side = front

    if preference.shape.auto_depth:
        side = back if op.inverted_extrude else front

    alignment.translation = bc.shape.matrix_world @ op.input_plane
    orig = view3d.location2d_to_origin3d(*mouse)
    ray = view3d.location2d_to_vector3d(*mouse)

    v1 = alignment @ Vector((0,1,0))
    v2 = alignment @ Vector((1,-1,0))
    v3 = alignment @ Vector((-1,-1,0))

    intersect = geometry.intersect_ray_tri(v1, v2, v3, ray, orig, False)

    if not intersect:
        intersect = geometry.intersect_ray_tri(v1, v2, v3, -ray, orig, False)

    if intersect:
        intersect = (inverse @ intersect) - op.last['draw_delta']

    elif op.operation == 'DRAW' and op.shape_type != 'NGON':
        location = bc.lattice.matrix_world @ Vector(bc.lattice.bound_box[op.draw_dot_index])
        intersect = inverse @ view3d.location2d_to_location3d(*mouse, location)

    else:
        intersect = op.mouse['intersect']

    op.mouse['intersect'] = intersect
    op.view3d['origin'] = 0.125 * sum((op.bounds[point] for point in (0, 1, 2, 3, 4, 5, 6, 7)), Vector())

    side = back if (op.operation == 'EXTRUDE') != op.inverted_extrude  else front
    coord = matrix @ (0.25 * sum((op.bounds[point] for point in side), Vector()))

    thin = bc.lattice.dimensions[2] < preference.shape.offset

    location = inverse @ view3d.location2d_to_location3d(mouse.x, mouse.y, coord)
    offset = op.start['offset'] if op.operation == 'OFFSET' else op.start['extrude']
    op.view3d['location'] = Vector((op.mouse['intersect'].x, op.mouse['intersect'].y, location.z - op.start['intersect'].z + offset))

    if dot:
        if op.operation == 'DRAW' and op.shape_type == 'NGON':
            index = -1
            for dot in op.widget.dots:
                if dot.type == 'DRAW' and dot.highlight:
                    index = dot.index

                    break

            # if index != -1:
                # break

            if index != -1:
                draw.shape(op, context, event, index=index)

        else:
            globals()[op.operation.lower()].shape(op, context, event)

    elif op.operation != 'NONE':
        globals()[op.operation.lower()].shape(op, context, event)

    if context.active_object:
        if modifier.shape_bool(context.active_object):
            display.shape.boolean(op)

    if op.operation not in {'NONE', 'BEVEL', 'ARRAY'} and not bc.shape.bc.copy:
        for mod in bc.shape.modifiers:
            if mod.type != 'SOLIDIFY':
                continue

            mod.show_viewport = bc.lattice.dimensions[2] > preference.shape.offset or (op.shape_type == 'NGON' or op.ngon_fit)

    if (op.operation != 'DRAW' or (preference.keymap.release_lock and preference.keymap.release_lock_lazorcut and preference.keymap.quick_execute) or op.original_mode == 'EDIT_MESH') and op.live:
        if op.mode in {'CUT', 'SLICE', 'INTERSECT', 'INSET', 'JOIN', 'EXTRACT'}:
            if hasattr(wm, 'Hard_Ops_material_options'):
                bc.shape.hops.status = 'BOOLSHAPE'

            if bc.shape.display_type != 'WIRE':
                bc.shape.display_type = 'WIRE'
                bc.shape.hide_set(False)

            if not modifier.shape_bool(context.active_object):
                modifier.create(op)

                if op.live:
                    for obj in op.datablock['targets'] + op.datablock['slices'] + op.datablock['insets']:
                        for mod in reversed(obj.modifiers):
                            if mod.type == 'BOOLEAN':
                                mod.show_viewport = True

                                break

            if op.original_mode == 'EDIT_MESH':

                for target in op.datablock['targets']:
                    for mod in target.modifiers:
                        if mod != modifier.shape_bool(target):
                            # mod.show_viewport = False

                            if op.mode == 'INSET' and mod.type == 'BOOLEAN' and mod.object in op.datablock['insets'] and not thin:
                                mod.show_viewport = True

                if bpy.app.version[:2] < (2, 91):
                    modifier.update(op, context)

        elif op.mode == 'MAKE':
            if hasattr(wm, 'Hard_Ops_material_options'):
                bc.shape.hops.status = 'UNDEFINED'

            if bc.shape.display_type != 'TEXTURED':
                bc.shape.display_type = 'TEXTURED'
                bc.shape.hide_set(True)

            if op.datablock['targets']:
                if modifier.shape_bool(context.active_object):
                    modifier.clean(op)

        elif op.mode == 'KNIFE':
            if hasattr(wm, 'Hard_Ops_material_options'):
                bc.shape.hops.status = 'UNDEFINED'

            if bc.shape.display_type != 'WIRE':
                bc.shape.display_type = 'WIRE'
                bc.shape.hide_set(False)

            if modifier.shape_bool(context.active_object):
                modifier.clean(op)

            mesh.knife(op, context, event)

    if op.shape_type == 'NGON' or op.ngon_fit:
        screw = None
        for mod in bc.shape.modifiers:
            if mod.type == 'SCREW' and mod.angle == 0:
                screw = mod

                break

        if not screw and not preference.shape.cyclic and not op.extruded:
            mod = bc.shape.modifiers.new(name='Screw', type='SCREW')
            mod.screw_offset = -0.001
            mod.angle = 0
            mod.steps = 1
            mod.render_steps = 1
            mod.use_normal_calculate = True

            for mod in bc.shape.modifiers:
                if mod.type == 'WELD':
                    mod.show_viewport = False

        elif screw and (preference.shape.cyclic or op.extruded):
            bc.shape.modifiers.remove(screw)

        solidify = None
        for mod in bc.shape.modifiers:
            if mod.type == 'SOLIDIFY':
                solidify = mod

                break

        if not solidify and not preference.shape.cyclic:
            mod = bc.shape.modifiers.new(name='Solidify', type='SOLIDIFY')
            mod.offset = 0
            mod.use_even_offset = True
            mod.use_quality_normals = True
            mod.thickness = op.last['modifier']['thickness']

        elif solidify and preference.shape.cyclic and not op.extruded:
            bc.shape.modifiers.remove(solidify)

    clamp(op, bc)
    weld_size(op, bc)


def clamp(op, bc):
    _clamp = bevel.clamp(op)
    ngon = op.shape_type == 'NGON' or op.ngon_fit
    boxgon = op.shape_type == 'BOX' and not op.ngon_fit and (op.ngon_point_index != -1 or op.ngon_point_bevel)
    for mod in bc.shape.modifiers:
        if mod.type != 'BEVEL':
            continue

        width_type = 'bevel_width' if mod.name.startswith('Bevel') else F'{mod.name.split(" ")[0].lower()}_bevel_width'

        if op.shape_type != 'NGON' and not op.ngon_fit:
            mod.width = op.last['modifier'][width_type] if not ngon and not boxgon else _clamp
        else:
            mod.width = _clamp

        if 'Quad' not in mod.name:
            continue

        # _clamp = bevel.clamp(op, q=True)

        if op.shape_type == 'NGON' or op.ngon_fit:
            vindices = op.geo['indices']['offset'] if not op.inverted_extrude else op.geo['indices']['extrusion']

            weight = 0.0
            for i, v in enumerate(vindices):
                vert = bc.shape.data.vertices[i]

                if vert.bevel_weight < weight:
                    continue

                weight = vert.bevel_weight

            _clamp *= weight

        else:
            _clamp = bevel.clamp(op, q=True)

        if mod.width > _clamp:
            mod.width = _clamp


def weld_size(op, bc):
    width = op.last['modifier']['bevel_width']
    for key, value in op.last['modifier'].items():
        if 'bevel' in key:
            if value < width:
                width = value

    weld_threshold = (width / op.last['modifier']['segments']) * 0.25
    limit = max(bc.shape.dimensions) * 0.001
    if weld_threshold > limit:
        weld_threshold = limit

    for mod in bc.shape.modifiers:
        if mod.type == 'WELD':
            mod.merge_threshold = weld_threshold if weld_threshold > 0.00001 else 0.00001


def bound_object(op, context):
    bc = context.scene.bc
    preference = addon.preference()

    if not bc.running:
        return

    existing_by_name = [m.name for m in bc.shape.modifiers]
    for mod in bc.bound_object.modifiers:
        if mod.name not in existing_by_name and mod.type != 'LATTICE':
            bc.bound_object.modifiers.remove(mod)

    existing_by_name = [m.name for m in bc.bound_object.modifiers]
    for mod in bc.shape.modifiers:
        if mod.name not in existing_by_name and mod.type not in {'ARRAY', 'MIRROR', 'SCREW', 'DECIMATE', 'BEVEL', 'WELD', 'LATTICE', 'VERTEX_WEIGHT_EDIT'}:
            if (op.shape_type == 'NGON' or op.ngon_fit) and not preference.shape.cyclic:
                continue
            modifier.new(bc.bound_object, mod=mod)

        elif mod.type == 'DISPLACE':
            bound_mod = bc.bound_object.modifiers[mod.name]
            bound_mod.direction = mod.direction
            bound_mod.strength = mod.strength
            bound_mod.mid_level = 0

        elif mod.type == 'SOLIDIFY':
            bound_mod = bc.bound_object.modifiers[mod.name]
            bound_mod.thickness = mod.thickness
            bound_mod.offset = mod.offset

    op.bounds = [Vector(c) for c in bc.bound_object.bound_box]
    bc.bound_object.matrix_world = bc.shape.matrix_world
