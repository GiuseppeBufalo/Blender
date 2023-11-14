import bpy
import bmesh
from mathutils import Vector, Matrix
import numpy as np
from .. utils.trim import get_sheetdata_from_uuid, get_trim_from_uuid
from .. utils.uv import set_trim_uv_channel, get_selection_uv_bbox, get_trim_uv_bbox
from .. utils.selection import get_boundary_edges
from .. utils.material import get_trimsheet_material_from_faces, assign_trimsheet_material
from .. utils.object import unshrinkwrap
from .. utils.mesh import unhide_deselect
from .. utils.raycast import cast_obj_ray_from_object


class TrimCut(bpy.types.Operator):
    bl_idname = "machin3.trim_cut"
    bl_label = "MACHIN3: Trim Cut"
    bl_description = "Cut Trim Decal into the its Parent Object's Mesh\nALT: keep Decals, but hide them"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if obj.DM.istrimdecal and obj.DM.decaltype != 'PANEL']

    def invoke(self, context, event):
        sel = context.selected_objects
        trim_decals = [obj for obj in context.selected_objects if obj.DM.istrimdecal and obj.DM.decaltype != 'PANEL']

        space_data = context.space_data
        r3d = space_data.region_3d

        init_persp = r3d.view_perspective
        init_viewmx = r3d.view_matrix.copy()

        r3d.view_perspective = 'ORTHO'

        bpy.ops.object.select_all(action='DESELECT')

        for decal in trim_decals:
            dg = context.evaluated_depsgraph_get()

            target = decal.DM.projectedon if decal.DM.projectedon else decal.parent if decal.parent else cast_obj_ray_from_object(dg, decal, (0, 0, -1), backtrack=0.01)[0]

            if target:
                if bpy.app.version < (2, 93, 4):
                    decal.select_set(True)

                else:
                    decal.select_set(False)

                target.select_set(True)
                context.view_layer.objects.active = target

                unshrinkwrap(decal)

                mirrors = [mod for mod in decal.modifiers if mod.type == 'MIRROR' and mod.show_viewport]

                for mod in mirrors:
                    mod.show_viewport = False

                sheetdata = get_sheetdata_from_uuid(decal.DM.trimsheetuuid)
                trim = get_trim_from_uuid(sheetdata, decal.DM.uuid)

                sheetresolution = Vector(sheetdata.get('resolution'))
                trimlocation = Vector(trim.get('location'))
                trimscale = Vector(trim.get('scale'))

                unhide_deselect(decal.data)
                unhide_deselect(target.data)

                set_trim_uv_channel(target)

                bpy.ops.object.mode_set(mode='EDIT')

                if bpy.app.version >= (2, 93, 4):
                    decal.select_set(True)

                if decal.DM.isprojected and decal.DM.decalbackup and decal.DM.projectedon == target:
                    viewmx = (target.matrix_world @ decal.DM.decalbackup.DM.backupmx).inverted_safe()
                else:
                    viewmx = decal.matrix_world.inverted_safe()

                r3d.view_matrix = viewmx

                bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)

                bpy.ops.mesh.knife_project()

                target.update_from_editmode()
                face_count = len(target.data.polygons)
                selected = np.empty((face_count, 1), np.bool)
                target.data.polygons.foreach_get('select', selected)

                if not np.any(selected):
                    bpy.ops.object.mode_set(mode='OBJECT')
                    decal.select_set(False)
                    target.select_set(False)

                    for mod in mirrors:
                        mod.show_viewport = True
                    continue

                bpy.ops.object.face_map_add()
                bpy.ops.object.face_map_assign()
                target.face_maps[target.face_maps.active_index].name = 'trim_cut_%s' % (decal.name)

                bpy.ops.uv.project_from_view(camera_bounds=True, correct_aspect=False)

                bm = bmesh.from_edit_mesh(target.data)
                bm.normal_update()
                bm.verts.ensure_lookup_table()

                faces = [f for f in bm.faces if f.select]

                uvs = bm.loops.layers.uv.active
                loops = [loop for face in faces for loop in face.loops]

                selbbox, selmid, selscale = get_selection_uv_bbox(uvs, loops)

                trimbbox, trimmid = get_trim_uv_bbox(sheetresolution, trimlocation, trimscale)

                smx = Matrix(((trimscale.x / selscale.x, 0), (0, trimscale.y / selscale.y)))

                for loop in loops:
                    loop[uvs].uv = trimmid + smx @ (loop[uvs].uv - selmid)

                boundary = get_boundary_edges(faces)

                for e in boundary:
                    e.seam = True

                mat_dict = get_trimsheet_material_from_faces(target, faces, sheetdata)

                assign_trimsheet_material(target, faces, mat_dict=mat_dict, add_material=True)

                bmesh.update_edit_mesh(target.data)

                bpy.ops.object.mode_set(mode='OBJECT')

                sel.remove(decal)

                decal.select_set(False)
                target.select_set(False)

                if event.alt:
                    decal.hide_set(True)

                    for mod in mirrors:
                        mod.show_viewport =True

                else:
                    bpy.data.meshes.remove(decal.data, do_unlink=True)

        r3d.view_perspective = init_persp
        r3d.view_matrix = init_viewmx

        for obj in sel:
            obj.select_set(True)

        context.view_layer.objects.active = sel[0] if sel else None

        return {'FINISHED'}
