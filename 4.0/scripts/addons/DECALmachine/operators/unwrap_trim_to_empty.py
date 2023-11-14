import bpy
import bmesh
from mathutils import Vector
from .. utils.trim import get_sheetdata_from_uuid, get_empty_trim_from_sheetmat, get_empty_trim_from_sheetdata
from .. utils.uv import set_trim_uv_channel, unwrap_to_empty_trim
from .. utils.mesh import get_most_common_material_index


class TrimUnwrapToEmpty(bpy.types.Operator):
    bl_idname = "machin3.trim_unwrap_to_empty"
    bl_label = "MACHIN3: Trim Unwrap to Empty"
    bl_description = "Unwrap selected faces to Empty Trim\nALT: Remove and Select Seams\nCTRL: use UV Unwrap instead of UV Reset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object

            bm = bmesh.from_edit_mesh(active.data)
            sheetmats = [mat for mat in active.data.materials if mat and mat.DM.istrimsheetmat and get_empty_trim_from_sheetmat(mat)]

            return sheetmats and [f for f in bm.faces if f.select]

    def invoke(self, context, event):
        active = context.active_object

        set_trim_uv_channel(active)

        mat, slot_idx, unique = get_most_used_sheetmat_with_empty_trim_from_selection(active)

        if not mat:
            mat, slot_idx = get_most_used_sheetmat_with_empty_trim_in_stack(active)

            unique = False

        if not unique:
            active.active_material_index = slot_idx
            bpy.ops.object.material_slot_assign()

        sheetdata = get_sheetdata_from_uuid(mat.DM.trimsheetuuid)
        empty = get_empty_trim_from_sheetdata(sheetdata)

        sheetresolution = Vector(sheetdata.get('resolution'))
        emptylocation = Vector(empty.get('location'))
        emptyscale = Vector(empty.get('scale'))

        unwrap_to_empty_trim(active, sheetresolution, emptylocation, emptyscale, remove_seams=event.alt, select_seams=event.alt, unwrap=event.ctrl)

        if event.alt:
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

        return {'FINISHED'}



def get_most_used_sheetmat_with_empty_trim_from_selection(obj):

    sheetmats = {idx: slot.material for idx, slot in enumerate(obj.material_slots) if slot.material and slot.material.DM.istrimsheetmat and get_empty_trim_from_sheetmat(slot.material)}

    bm = bmesh.from_edit_mesh(obj.data)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    faces = [f for f in bm.faces if f.select]

    slot_idx, unique = get_most_common_material_index(faces)

    if slot_idx in sheetmats:
        return sheetmats[slot_idx], slot_idx, unique

    return None, None, None


def get_most_used_sheetmat_with_empty_trim_in_stack(obj):

    sheetmats = {idx: slot.material for idx, slot in enumerate(obj.material_slots) if slot.material and slot.material.DM.istrimsheetmat and get_empty_trim_from_sheetmat(slot.material)}

    if len(sheetmats) > 1:
        bm = bmesh.from_edit_mesh(obj.data)
        indices = [f.material_index for f in bm.faces]

        slot_idx = max(sheetmats, key=indices.count)

    else:
        slot_idx = list(sheetmats.keys())[0]

    return sheetmats[slot_idx], slot_idx
