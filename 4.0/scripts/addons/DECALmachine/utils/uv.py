import bpy
import bmesh
from mathutils import Vector, Matrix
from . registration import get_prefs
from . modifier import get_uvtransfer


def get_active_uv_layer(obj):
    if obj.data.uv_layers:
        return obj.data.uv_layers[obj.data.uv_layers.active_index]
    return obj.data.uv_layers.new()



def get_uv_transfer_layer(obj, create=True):
    if obj.data.uv_layers.get('UVTransfer'):
        return obj.data.uv_layers.get('UVTransfer')
    if create:
        return obj.data.uv_layers.new(name="UVTransfer")


def ensure_uv_transfer_is_last(obj):

    uvtransfer = get_uv_transfer_layer(obj, create=False)

    if uvtransfer and len(obj.data.uv_layers) > 1 and obj.data.uv_layers[-1] != uvtransfer:
        obj.data.uv_layers.remove(uvtransfer)
        uvtransfer = obj.data.uv_layers.new(name="UVTransfer")

    return uvtransfer


def verify_uv_transfer(context, obj):

    uvtransfer = ensure_uv_transfer_is_last(obj)

    if uvtransfer:
        mod = get_uvtransfer(obj)

        if mod:
            context.view_layer.objects.active = obj
            mod.layers_uv_select_dst = uvtransfer.name



def set_trim_uv_channel(obj):

    trim_uv_layer = get_prefs().trim_uv_layer

    while len(obj.data.uv_layers) <= trim_uv_layer:
        obj.data.uv_layers.new()

    obj.data.uv_layers.active_index = trim_uv_layer
    obj.data.uv_layers[trim_uv_layer].active_render = True


def set_second_uv_channel(obj):

    second_uv_layer = get_prefs().second_uv_layer

    while len(obj.data.uv_layers) <= second_uv_layer:
        obj.data.uv_layers.new()

    obj.data.uv_layers.active_index = second_uv_layer


def get_selection_uv_bbox(uvs, loops):

    coords = [loop[uvs].uv for loop in loops]

    minu = min([co.x for co in coords])
    minv = min([co.y for co in coords])
    maxu = max([co.x for co in coords])
    maxv = max([co.y for co in coords])

    bottom_left = Vector((minu, minv))
    top_right = Vector((maxu, maxv))

    bbox = (bottom_left, top_right)
    mid = (bottom_left + top_right) / 2
    scale = Vector((maxu - minu, maxv - minv))

    if scale != Vector((0, 0)):
        return bbox, mid, scale
    return None, None, None


def get_trim_uv_bbox(resolution, location, scale):

    bottom_left = Vector((0.5, 0.5)) + Vector((location.x / (resolution.x / 1000), location.y / (resolution.y / 1000))) + Vector((-scale.x / 2, -scale.y / 2))
    top_right = Vector((0.5, 0.5)) + Vector((location.x / (resolution.x / 1000), location.y / (resolution.y / 1000))) + Vector((scale.x / 2, scale.y / 2))

    return (bottom_left, top_right), (bottom_left + top_right) / 2



def unwrap_to_empty_trim(active, sheetresolution, trimlocation, trimscale, remove_seams=False, select_seams=False, unwrap=False):

    set_trim_uv_channel(active)

    if unwrap:
        bpy.ops.uv.unwrap()
    else:
        bpy.ops.uv.reset()

    bm = bmesh.from_edit_mesh(active.data)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    if remove_seams:
        edges = [e for e in bm.edges if e.select]

        for e in edges:
            if e.seam:
                e.seam = False
            elif select_seams:
                e.select_set(False)

    faces = [f for f in bm.faces if f.select]

    uvs = bm.loops.layers.uv.active
    loops = [loop for face in faces for loop in face.loops]

    trimbbox, trimmid = get_trim_uv_bbox(sheetresolution, trimlocation, trimscale)

    smx = Matrix(((trimscale.x, 0), (0, trimscale.y)))

    for loop in loops:
        loop[uvs].uv = trimmid + smx @ (loop[uvs].uv - Vector((0.5, 0.5)))

    bmesh.update_edit_mesh(active.data)


def rectangulate(uvs, face):

    loops = [l for l in face.loops]

    bbox, _, _ = get_selection_uv_bbox(uvs, loops)
    corners = [bbox[0], Vector((bbox[1].x, bbox[0].y)), bbox[1], Vector((bbox[0].x, bbox[1].y))]


    for corner in corners:
        distances = [((corner - l[uvs].uv).length, l) for l in loops]
        closest = min(distances, key=lambda x: x[0])[1]
        closest[uvs].uv = corner

        loops.remove(closest)


def quad_unwrap(bm, uvs, faces, active_face=None):

    if not active_face or (active_face not in faces) or (active_face and not active_face.is_valid):
        active_face = faces[0]

    bm.faces.active = active_face

    for f in faces:
        f.select_set(False)

    active_face.select_set(True)
    bpy.ops.uv.unwrap(margin=0)

    rectangulate(uvs, active_face)

    for f in faces:
        f.select_set(True)

    bpy.ops.uv.follow_active_quads()



def mirror_trim_uvs(uvs, loops, trim, u=True):

    mid = Vector((0.5, 0.5)) if trim['ispanel'] else get_selection_uv_bbox(uvs, loops)[1]

    if mid:
        mmx = Matrix(((-1, 0), (0, 1))) if u else Matrix(((1, 0), (0, -1)))

        for loop in loops:
            loop[uvs].uv = mid + mmx @ (loop[uvs].uv - mid)
