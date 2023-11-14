import bpy
import bmesh
from .. utils.material import get_most_used_sheetmat_from_selection
from .. utils.trim import get_sheetdata_from_uuid, get_trim_from_selection
from .. utils.uv import set_trim_uv_channel, mirror_trim_uvs
from .. utils.selection import get_selection_islands
from .. utils.ui import popup_message


class MirrorTrim(bpy.types.Operator):
    bl_idname = "machin3.mirror_trim"
    bl_label = "MACHIN3: Mirror Trim"
    bl_description = "Mirror Trim\nALT: Batch Mirror Trims based on Selection Islands\nCTRL: V Mirror"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            bm = bmesh.from_edit_mesh(active.data)
            if bm.loops.layers.uv.active:
                sheetmats = [mat for mat in active.data.materials if mat and mat.DM.istrimsheetmat]
                return sheetmats and [f for f in bm.faces if f.select]

    def invoke(self, context, event):
        active = context.active_object

        mat, _, _ = get_most_used_sheetmat_from_selection(active)

        set_trim_uv_channel(active)

        sheetdata = get_sheetdata_from_uuid(mat.DM.trimsheetuuid)

        if sheetdata:
            bm = bmesh.from_edit_mesh(active.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            uvs = bm.loops.layers.uv.active
            faces = [f for f in bm.faces if f.select]

            if not event.alt:
                trim = get_trim_from_selection(active, sheetdata)

                if trim:
                    loops = [loop for face in faces for loop in face.loops]
                    mirror_trim_uvs(uvs, loops, trim, u=not event.ctrl)

                    bmesh.update_edit_mesh(active.data)

            else:
                islands = get_selection_islands(faces, debug=False)

                for _, _, faces in islands:
                    loops = [loop for face in faces for loop in face.loops]

                    meshdata = {'faces': faces,
                                'loops': loops,
                                'uvs': uvs}

                    trim = get_trim_from_selection(active, sheetdata, meshdata=meshdata)

                    if trim:
                        mirror_trim_uvs(uvs, loops, trim, u=not event.ctrl)

                        bmesh.update_edit_mesh(active.data)

        else:
            popup_message("The Trim Sheet the current Trim Sheet Material is created from is not registered!", title="Trim Sheet not found!")
        return {'FINISHED'}
