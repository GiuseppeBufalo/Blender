import bpy
import bmesh



def hide(mesh):
    mesh.polygons.foreach_set('hide', [True] * len(mesh.polygons))
    mesh.edges.foreach_set('hide', [True] * len(mesh.edges))
    mesh.vertices.foreach_set('hide', [True] * len(mesh.vertices))

    mesh.update()


def unhide(mesh):
    mesh.polygons.foreach_set('hide', [False] * len(mesh.polygons))
    mesh.edges.foreach_set('hide', [False] * len(mesh.edges))
    mesh.vertices.foreach_set('hide', [False] * len(mesh.vertices))

    mesh.update()


def unhide_select(mesh):
    polygons = len(mesh.polygons)
    edges = len(mesh.edges)
    vertices = len(mesh.vertices)

    mesh.polygons.foreach_set('hide', [False] * polygons)
    mesh.edges.foreach_set('hide', [False] * edges)
    mesh.vertices.foreach_set('hide', [False] * vertices)

    mesh.polygons.foreach_set('select', [True] * polygons)
    mesh.edges.foreach_set('select', [True] * edges)
    mesh.vertices.foreach_set('select', [True] * vertices)

    mesh.update()


def unhide_deselect(mesh):
    polygons = len(mesh.polygons)
    edges = len(mesh.edges)
    vertices = len(mesh.vertices)

    mesh.polygons.foreach_set('hide', [False] * polygons)
    mesh.edges.foreach_set('hide', [False] * edges)
    mesh.vertices.foreach_set('hide', [False] * vertices)

    mesh.polygons.foreach_set('select', [False] * polygons)
    mesh.edges.foreach_set('select', [False] * edges)
    mesh.vertices.foreach_set('select', [False] * vertices)

    mesh.update()


def select(mesh):
    mesh.polygons.foreach_set('select', [True] * len(mesh.polygons))
    mesh.edges.foreach_set('select', [True] * len(mesh.edges))
    mesh.vertices.foreach_set('select', [True] * len(mesh.vertices))

    mesh.update()


def deselect(mesh):
    mesh.polygons.foreach_set('select', [False] * len(mesh.polygons))
    mesh.edges.foreach_set('select', [False] * len(mesh.edges))
    mesh.vertices.foreach_set('select', [False] * len(mesh.vertices))

    mesh.update()


def clear_uvs(mesh):
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])


def init_uvs(mesh):
    clear_uvs(mesh)
    uvs = mesh.uv_layers.new()

    return uvs


def reset_material_indices(mesh):
    mesh.polygons.foreach_set('material_index', [0] * len(mesh.polygons))
    mesh.update()


def smooth(mesh, smooth=True):
    mesh.polygons.foreach_set('use_smooth', [smooth] * len(mesh.polygons))
    mesh.update()



def blast(mesh, prop, type):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    if prop == "hidden":
        faces = [f for f in bm.faces if f.hide]

    elif prop == "visible":
        faces = [f for f in bm.faces if not f.hide]

    elif prop == "selected":
        faces = [f for f in bm.faces if f.select]

    bmesh.ops.delete(bm, geom=faces, context=type)

    bm.to_mesh(mesh)
    bm.clear()


def loop_index_update(bm, debug=False):

    lidx = 0

    for f in bm.faces:
        if debug:
            print(f)
        for l in f.loops:
            l.index = lidx
            lidx += 1
            if debug:
                print(" •", l)


def join(target, objects, select=[]):
    mxi = target.matrix_world.inverted_safe()

    bm = bmesh.new()
    bm.from_mesh(target.data)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    i = bm.faces.layers.int.verify()

    if any([obj.data.use_auto_smooth for obj in objects]):
        target.data.use_auto_smooth = True

    for idx, obj in enumerate(objects):
        mesh = obj.data
        mx = obj.matrix_world
        mesh.transform(mxi @ mx)

        bmm = bmesh.new()
        bmm.from_mesh(mesh)
        bmm.normal_update()
        bmm.verts.ensure_lookup_table()

        im = bmm.faces.layers.int.verify()

        for f in bmm.faces:
            f[im] = idx + 1

        bmm.to_mesh(mesh)
        bmm.clear()

        bm.from_mesh(mesh)

        bpy.data.meshes.remove(mesh, do_unlink=True)

    if select:
        for f in bm.faces:
            if f[i] in select:
                f.select_set(True)

    bm.to_mesh(target.data)
    bm.clear()


def get_most_common_material_index(faces):

    slots = [f.material_index for f in faces]
    unique_slots = set(slots)

    if len(unique_slots) == 1:
        slot_idx = unique_slots.pop()

        return slot_idx, True

    else:
        slot_idx = max(unique_slots, key=slots.count)
        return slot_idx, False
