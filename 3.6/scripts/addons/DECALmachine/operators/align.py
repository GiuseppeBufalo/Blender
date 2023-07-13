import bpy
import bmesh
from mathutils import Vector, Matrix, geometry
from .. utils.math import get_center_between_verts, create_rotation_difference_matrix_from_quat
from .. utils.draw import draw_vector, draw_point


class AlignDecalToEdge(bpy.types.Operator):
    bl_idname = "machin3.align_decal_to_edge"
    bl_label = "MACHIN3: Align Decal to Edge"
    bl_description = "Align Decal(s) to edge of the active object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            sel = [obj for obj in context.selected_objects if obj != active and obj.DM.isdecal]

            if active and sel:
                for obj in [active] + sel:
                    bm = bmesh.from_edit_mesh(obj.data)

                    if len([e for e in bm.edges if e.select]) != 1:
                        return False
                return True

    def execute(self, context):
        target = context.active_object
        decals = [obj for obj in context.selected_objects if obj != target]
        debug = context.scene.DM.debug

        for decal in decals:

            v_decal, v_target, mid, coords = self.get_vectors_from_alignment_edges(decal, target)

            if v_decal and v_target:
                loc, _, _ = decal.matrix_world.decompose()

                if debug:
                    draw_vector(v_decal, loc, color=(1, 0, 0), modal=False)
                    draw_vector(v_target, loc, color=(0, 0, 1), modal=False)


                rmx = create_rotation_difference_matrix_from_quat(v_decal, v_target)

                decal.matrix_world = Matrix.Translation(loc) @ rmx @ Matrix.Translation(-loc) @ decal.matrix_world

                mid = decal.matrix_world @ mid

                if debug:
                    draw_point(mid, color=(1, 1, 0), modal=False)
                    draw_point(coords[0], color=(1, 1, 0), modal=False)
                    draw_point(coords[1], color=(1, 1, 0), modal=False)

                co, _ = geometry.intersect_point_line(mid, *coords)

                if debug:
                    draw_point(co, color=(1, 1, 1), modal=False)

                if co:
                    decal.matrix_world = Matrix.Translation(co - mid) @ decal.matrix_world

        bpy.ops.object.mode_set(mode='OBJECT')

        if debug:
            context.area.tag_redraw()

        return {'FINISHED'}

    def get_vectors_from_alignment_edges(self, decal, target):

        bm = bmesh.from_edit_mesh(decal.data)
        edges = [e for e in bm.edges if e.select]

        v_decal = (decal.matrix_world.to_3x3() @ Vector(edges[0].verts[0].co - edges[0].verts[1].co)).normalized() if len(edges) == 1 else None
        mid = get_center_between_verts(*edges[0].verts) if edges else None

        bm = bmesh.from_edit_mesh(target.data)
        edges = [e for e in bm.edges if e.select]

        v_target = (target.matrix_world.to_3x3() @ Vector(edges[0].verts[0].co - edges[0].verts[1].co)).normalized() if len(edges) == 1 else None
        coords = [target.matrix_world @ v.co for v in edges[0].verts] if edges else None

        if v_decal and v_target:

            dot = v_decal.dot(v_target)

            if dot < 0:
                v_decal.negate()

            return v_decal, v_target, mid, coords
        return None, None, None, None
