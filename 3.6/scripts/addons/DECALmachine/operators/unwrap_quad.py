import bpy
import bmesh
from mathutils import Vector, Matrix
from math import degrees, radians
import numpy as np
from .. utils.selection import get_selection_islands, get_boundary_edges, get_selected_vert_sequences, get_edges_vert_sequences
from .. utils.property import rotate_list
from .. utils.draw import draw_vector, draw_point, draw_line
from .. utils.ui import popup_message
from .. utils.material import get_most_used_sheetmat_from_selection
from .. utils.trim import get_sheetdata_from_uuid, get_trim_from_selection
from .. utils.uv import get_selection_uv_bbox, get_trim_uv_bbox, set_trim_uv_channel, quad_unwrap
from .. utils.math import trilaterate





class QuadUnwrap(bpy.types.Operator):
    bl_idname = "machin3.quad_unwrap"
    bl_label = "MACHIN3: Quad Unwrap"
    bl_description = "Quad Unwrap selected faces, even with triangles and n-gons among the selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            bm = bmesh.from_edit_mesh(active.data)
            return [f for f in bm.faces if f.select]

    def execute(self, context):
        active = context.active_object

        set_trim_uv_channel(active)

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        uvs = bm.loops.layers.uv.verify()

        faces = [f for f in bm.faces if f.select]

        islands = get_selection_islands(faces, debug=False)

        if len(islands) > 1:
            for _, _, faces in islands[1:]:
                for f in faces:
                    f.select_set(False)

        verts = islands[0][0]
        edges = islands[0][1]
        faces = islands[0][2]

        trim = None

        mat, _, _ = get_most_used_sheetmat_from_selection(active)

        if mat:
            sheetdata = get_sheetdata_from_uuid(mat.DM.trimsheetuuid)

            if sheetdata:
                trim = get_trim_from_selection(active, sheetdata)

        quads = [f for f in faces if len(f.verts) == 4]
        isallquads = len(faces) == len(quads)

        if isallquads:
            quad_unwrap(bm, uvs, faces, bm.faces.active)

        else:
            isshallow = self.check_selection_depth(faces)

            boundary_edges = get_boundary_edges(faces)
            boundary_verts = list({v for e in boundary_edges for v in e.verts})

            sequences = get_edges_vert_sequences(boundary_verts, boundary_edges, debug=False)

            if isshallow:
                r, errtitle, errmsg = self.shallow_unwrap(active, bm, uvs, faces, sequences)
            else:
                r, errtitle, errmsg = self.deep_unwrap(active, bm, uvs, verts, edges, faces, sequences)

            if r:
                popup_message(errmsg, title=errtitle)
                return r

        if trim and not trim['isempty']:
            self.align_to_trim(uvs, faces, sheetdata, trim)

        bmesh.update_edit_mesh(active.data)

        return {'FINISHED'}

    def align_to_trim(self, uvs, faces, sheetdata, trim):

        sheetresolution = Vector(sheetdata.get('resolution'))
        trimlocation = Vector(trim.get('location'))
        trimscale = Vector(trim.get('scale'))
        trimratio = trimscale.x / trimscale.y

        loops = [loop for face in faces for loop in face.loops]

        trimbbox, trimmid = get_trim_uv_bbox(sheetresolution, trimlocation, trimscale)

        if trim['ispanel']:

            selbbox, selmid, selscale = get_selection_uv_bbox(uvs, loops)

            selratio = selscale.x / selscale.y

            if not ((selratio >= 1 and trimratio >= 1) or (selratio <= 1 and trimratio <= 1)):
                rmx = Matrix.Rotation(radians(-90), 2)

                for loop in loops:
                    loop[uvs].uv = rmx @ loop[uvs].uv

        selbbox, selmid, selscale = get_selection_uv_bbox(uvs, loops)

        selratio = selscale.x / selscale.y

        if trim['ispanel'] and selratio > trimratio:
            smx = Matrix.Scale(trimscale.y / selscale.y, 2)

        elif trim['ispanel'] and selratio < trimratio:
            smx = Matrix.Scale(trimscale.y / selscale.y, 2)

        else:
            smx = Matrix(((trimscale.x / selscale.x, 0), (0, trimscale.y / selscale.y)))

        for loop in loops:
            loop[uvs].uv = trimmid + smx @ (loop[uvs].uv - selmid)

    def deep_unwrap(self, active, bm, uvs, verts, edges, faces, sequences, debug=False):

        def duplicate(bm, verts, edges, faces):
            verts_map = {}

            dup_verts = []
            dup_edges = []
            dup_faces = []

            active_dup_face = None

            for v in verts:
                dup = bm.verts.new(v.co)
                verts_map[v] = dup
                dup_verts.append(dup)

            for e in edges:
                dup = bm.edges.new([verts_map[v] for v in e.verts])
                dup.seam = e.seam
                dup_edges.append(dup)

            for f in faces:
                dup = bm.faces.new([verts_map[v] for v in f.verts])
                dup_faces.append(dup)

                if f == bm.faces.active:
                    active_dup_face = dup

            return verts_map, dup_verts, dup_edges, dup_faces, active_dup_face

        def quadrify(bm, faces, dup_verts, dup_edges):

            seams = [e for e in dup_edges if e.seam]
            bmesh.ops.dissolve_edges(bm, edges=seams, use_verts=False, use_face_split=False)

            two_edged = [v for v in dup_verts if v.is_valid and len([e for e in v.link_edges if e in dup_edges]) == 2]
            straight_two_edged = []

            for v in two_edged:
                e1, e2 = [e for e in v.link_edges]

                vector1 = e1.other_vert(v).co - v.co
                vector2 = e2.other_vert(v).co - v.co

                angle = degrees(vector1.angle(vector2))

                if 178 <= angle < 181:
                    straight_two_edged.append(v)

            bmesh.ops.dissolve_verts(bm, verts=straight_two_edged, use_face_split=False, use_boundary_tear=False)

            for f in faces:
                f.select_set(False)

            for v in dup_verts:
                if v.is_valid:
                    v.select_set(True)

            bm.select_flush(True)

            dup_faces = [f for f in bm.faces if f.select]

            quads = [f for f in dup_faces if len(f.verts) == 4]

            return len(dup_faces) == len(quads), dup_faces

        if len(sequences) == 1:

            verts_map, dup_verts, dup_edges, dup_faces, active_dup_face = duplicate(bm, verts, edges, faces)

            if debug:
                bmesh.ops.translate(bm, verts=dup_verts, vec=(0.0, 0.0, 0.3))

            all_quad, dup_faces = quadrify(bm, faces, dup_verts, dup_edges)

            if all_quad:
                quad_unwrap(bm, uvs, dup_faces, active_face=active_dup_face)

                regular = []

                for v in verts:

                    if verts_map[v].is_valid:
                        regular.append(v)

                        loops = [l for l in v.link_loops if l.face in faces]

                        dup = verts_map[v]

                        dup_loops = [l for l in dup.link_loops if l.face in dup_faces]
                        dup_co = dup_loops[0][uvs].uv

                        for l in loops:
                            l[uvs].uv = dup_co

                        if debug:
                            for l in loops:
                                l[uvs].uv += Vector((2, 0))


                for v_original in verts:
                    if not verts_map[v_original].is_valid:

                        connected_regular = list({v for e in v_original.link_edges if not e.seam for v in e.verts if v in regular and v != v_original})


                        if len(connected_regular) == 2:
                            c1 = connected_regular[0]
                            c2 = connected_regular[1]

                            c1_v_dir = v_original.co - c1.co
                            c1_c2_dir = c2.co - c1.co

                            ratio = c1_v_dir.length / c1_c2_dir.length

                            l1 = [l for l in verts_map[c1].link_loops][0]
                            l2 = [l for l in verts_map[c2].link_loops][0]

                            loops = [l for l in v_original.link_loops if l.face in faces]

                            for l in loops:
                                l[uvs].uv = l1[uvs].uv + (l2[uvs].uv - l1[uvs].uv) * ratio

                            if debug:
                                for l in loops:
                                    l[uvs].uv += Vector((2, 0))


                        else:
                            v_original.select_set(True)


                            regular_face_verts = list({v for f in v_original.link_faces if f in faces for v in f.verts if v in regular})

                            if connected_regular and connected_regular[0] not in regular_face_verts:
                                closest_regular = connected_regular + regular_face_verts
                            else:
                                closest_regular = regular_face_verts

                            if len(closest_regular) < 4:
                                distances = sorted([((v.co - v_original.co).length, v) for v in regular if v not in closest_regular], key=lambda x: x[0])
                                closest_regular += [v for _, v in distances[:4 - len(closest_regular)]]


                            elif len(closest_regular) > 4:
                                closest_regular = closest_regular[:4]

                            regular_loops = [verts_map[v].link_loops[0] for v in closest_regular]

                            d_world = (closest_regular[1].co - closest_regular[0].co).length
                            d_uv = (regular_loops[1][uvs].uv - regular_loops[0][uvs].uv).length

                            ratio = d_uv / d_world

                            distances = [(v.co - v_original.co).length * ratio for v in closest_regular]

                            coords = [np.array([*l[uvs].uv, 0]) for l in regular_loops]

                            p = trilaterate(coords, distances)

                            loops = [l for l in v_original.link_loops if l.face in faces]

                            for l in loops:
                                l[uvs].uv = p[:2]

                            if debug:
                                for l in loops:
                                    l[uvs].uv += Vector((2, 0))

                bmesh.ops.delete(bm, geom=dup_faces, context='FACES')

                for f in faces:
                    f.select_set(True)

                return False, "", ""


            else:

                bmesh.ops.delete(bm, geom=dup_faces, context='FACES')

                for f in faces:
                    f.select_set(True)

                errtitle = "Illegal Selection"
                errmsg = "Verify that all irregular edges have been marked as seams!"

                return {'FINISHED'}, errtitle, errmsg


        elif len(sequences) == 2:
            errtitle = "Illegal Selection"
            errmsg = "Cyclic selections are not supported when selection is multiple faces deep and contains triangles or n-gnos!"

            return {'CANCELLED'}, errtitle, errmsg

        else:
            errtitle = "Illegal Selection"
            errmsg = "Your selection is invalid!"

            return {'CANCELLED'}, errtitle, errmsg

    def shallow_unwrap(self, active, bm, uvs, faces, sequences):

        def align_vert_sequences(bm, vertsA, vertsB, mx=None, debug=False):
            vA_start = None
            vB_start = None

            for v in vertsA:
                linked_verts = [(e.other_vert(v), (e.other_vert(v).co - v.co).length) for e in v.link_edges if e.other_vert(v) in vertsB]

                if linked_verts:
                    vA_start = v
                    vB_start = min(linked_verts, key=lambda x: x[1])[0]
                    break

            rotate_list(vertsA, vertsA.index(vA_start))
            rotate_list(vertsB, vertsB.index(vB_start))

            vA, vA_next = vertsA[0:2]
            vA_dir = vA_next.co - vA.co

            vB, vB_next = vertsB[0:2]
            vB_dir = vB_next.co - vB.co

            dot = vA_dir.dot(vB_dir)

            if dot < 0:
                if debug:
                    print("reversing side B")

                vertsB.reverse()
                rotate_list(vertsB, -1)

                vB_next = vertsB[1]

                if debug:
                    print([v.index for v in vertsB])

            edge = bm.edges.get((vA, vB))
            loop = [l for l in edge.link_loops if l.vert == vA][0]

            if not (loop.link_loop_prev.vert == vA_next or loop.link_loop_next.link_loop_next.vert == vB_next):
                if debug:
                    print("switching side A and B")

                vertsA, vertsB = vertsB, vertsA

                vA, vA_next = vertsA[0:2]
                vB, vB_next = vertsB[0:2]


            if debug:
                print("aligned vert sequences:")
                print([v.index for v in vertsA])
                print([v.index for v in vertsB])

                draw_point(vA.co, mx=mx, color=(1, 0, 0), modal=False)
                draw_point(vA_next.co, mx=mx, color=(1, 1, 1), modal=False)

                draw_point(vB.co, mx=mx, color=(0, 1, 0), modal=False)
                draw_point(vB_next.co, mx=mx, color=(1, 1, 1), modal=False)

            return vertsA, vertsB

        def get_seam_edge(bm, vertsA, vertsB, debug=False):
            active_edge = bm.select_history[-1] if bm.select_history and isinstance(bm.select_history[-1], bmesh.types.BMEdge) else None

            edge = bm.edges.get((vertsA[0], vertsB[0]))

            if active_edge and active_edge != edge:
                if debug:
                    print("found active edge:", active_edge)

                if all([f.select for f in active_edge.link_faces]):
                    if debug:
                        print("active edge is sweep edge, rotating vert lists!")
                        print("pre-rotation verts:")
                        print([v.index for v in vertsA])
                        print([v.index for v in vertsB])

                    vA = [v for v in active_edge.verts if v in vertsA]
                    vB = [v for v in active_edge.verts if v in vertsB]

                    if vA and vB:
                        rotate_list(vertsA, vertsA.index(vA[0]))
                        rotate_list(vertsB, vertsB.index(vB[0]))

                        if debug:
                            print("post-rotation verts")
                            print([v.index for v in vertsA])
                            print([v.index for v in vertsB])

                        return active_edge
            return edge

        def get_cap_edges(bm, verts, mx=None, debug=False):

            lasttwo = list(bm.select_history)[-2:] if len(bm.select_history) >= 2 else None

            if lasttwo and all([isinstance(e, bmesh.types.BMEdge) for e in lasttwo]):
                if debug:
                    print("found two 'active' edges")
                    for e in lasttwo:
                        print(e)

                cap_edges = [e for e in lasttwo if all([v in verts for v in e.verts]) and len([f for f in e.link_faces if f.select]) == 1]

                if debug:
                    for e in cap_edges:
                        draw_line([v.co for v in e.verts], mx=mx, color=(0, 1, 0), modal=False)

                if len(cap_edges) == 2:
                    return cap_edges

            corner_candidates = []

            for idx, v in enumerate(verts):
                if idx == 0:
                    v_prev = verts[-1]
                    v_next = verts[1]

                elif idx == len(verts) - 1:
                    v_prev = verts[-2]
                    v_next = verts[0]

                else:
                    v_prev = verts[idx - 1]
                    v_next = verts[idx + 1]

                angle = (v_prev.co - v.co).angle(v_next.co - v.co)

                if 80 < degrees(angle) < 110:
                    corner_candidates.append(v)

            if debug:
                for v in corner_candidates:
                    print(v)
                    draw_point(v.co, mx=mx, modal=False)

            cap_edges = {e for v in corner_candidates for e in v.link_edges if e.other_vert(v) in corner_candidates and len([f for f in e.link_faces if f.select]) == 1}

            if debug:
                for e in cap_edges:
                    draw_line([v.co for v in e.verts], mx=mx, color=(0, 1, 0), modal=False)

            return list(cap_edges) if len(cap_edges) == 2 else None

        def create_each_vert_sequence(cap_edges, verts, mx=None, debug=False):

            start_verts = cap_edges[0].verts
            end_verts = cap_edges[1].verts

            vA, vB = (start_verts[0], start_verts[1]) if (verts + [verts[0]])[verts.index(start_verts[0]) + 1] != start_verts[1] else (start_verts[1], start_verts[0])

            if debug:
                print("vertA", vA.index)
                print("vertB", vB.index)

            rotate_list(verts, verts.index(vA))

            if debug:
                print("rotated")
                print([v.index for v in verts])

            for idx, v in enumerate(verts):
                if v in end_verts:
                    break

            vertsA = verts[:idx + 1]
            vertsB = verts[idx + 1:]
            vertsB.reverse()

            if debug:
                print("split vertsA and vertsB")
                print([v.index for v in vertsA])
                print([v.index for v in vertsB])

                draw_point(vertsA[0].co, mx=mx, color=(1, 0, 0), modal=False)
                draw_point(vertsA[-1].co, mx=mx, color=(1, 0, 0), modal=False)

                draw_point(vertsB[0].co, mx=mx, color=(0, 1, 0), modal=False)
                draw_point(vertsB[-1].co, mx=mx, color=(0, 1, 0), modal=False)


            vA, vA_next = vertsA[0:2]
            vB, vB_next = vertsB[0:2]

            edge = cap_edges[0]
            loop = [l for l in edge.link_loops if l.face.select][0]

            if loop.vert == vB:
                if debug:
                    print("switching side A and B")

                vertsA, vertsB = vertsB, vertsA

                vA, vA_next = vertsA[0:2]
                vB, vB_next = vertsB[0:2]

            if debug:
                print("aligned vert sequences:")
                print([v.index for v in vertsA])
                print([v.index for v in vertsB])

                draw_point(vA.co, mx=mx, color=(1, 0, 0), modal=False)
                draw_point(vA_next.co, mx=mx, color=(1, 1, 1), modal=False)

                draw_point(vB.co, mx=mx, color=(0, 1, 0), modal=False)
                draw_point(vB_next.co, mx=mx, color=(1, 1, 1), modal=False)

            return vertsA, vertsB

        def create_uv_coords(dictionary, verts, u=0, cyclic=False, debug=False):
            distance = 0

            for idx, v in enumerate(verts):
                dictionary[v] = (u, distance)

                if idx < len(verts) - 1:
                    v_next = verts[idx + 1]
                    distance += (v_next.co - v.co).length

                elif cyclic and idx == len(verts) - 1:
                    distance += (verts[0].co - v.co).length
                    dictionary[verts[0]] = (u, distance)


            if debug:
                print([(v.index, coords) for v, coords in dictionary.items()])

            return distance

        def align_uv_coords(uv_coords, verts, ratio):
            for v, coords in uv_coords.items():
                if v in verts:
                    uv_coords[v] = (coords[0], coords[1] * ratio)

        def unwrap(uvs, faces, edge, vertsA, vertsB, uv_coords, cyclic=False, debug=False):

            loop = [l for l in edge.link_loops if l.vert == vertsA[0]][0]
            start_loop = loop

            loop[uvs].uv = (0, 0)

            vert = vertsA[0]

            next_loop = None
            next_vert = None

            face_count = 1

            while True:
                if debug:
                    print()
                    print(loop.vert.index, loop)

                radial_loop = loop.link_loop_radial_next if loop.link_loop_radial_next != loop else None

                if radial_loop and radial_loop.face.select and radial_loop.vert in vertsA:
                    if debug:
                        print("found possible next face, loop and vert!")
                        print(radial_loop.face.index, radial_loop.vert.index, radial_loop)

                    next_loop = radial_loop
                    next_vert = radial_loop.vert

                loop = loop.link_loop_next

                if loop.vert == vert:
                    if debug:
                        print("returned to initial vert, jumping to the next face/loop/vert")

                    if next_loop == start_loop:
                        if debug:
                            print(" come full circle, finished unwrap")
                        break

                    elif next_loop is None:
                        if debug:
                            print(" reached end, finished unwrap")
                        break

                    loop = next_loop
                    vert = next_vert

                    next_loop = None
                    next_vert = None

                    face_count += 1

                elif face_count > len(faces) * 10:
                    if debug:
                        print("aborting unwrap early, this shoulfn't happen, but reached face_count higher than amount of selected faces!")
                    break


                if loop.vert in [vertsA[0], vertsB[0]] and cyclic and face_count < len(faces) / 2:
                    loop[uvs].uv = (0, 0) if loop.vert == vertsA[0] else (edge.calc_length(), 0)
                    continue

                else:
                    loop[uvs].uv = uv_coords[loop.vert]

        if len(sequences) == 2:
            cyclic = True

            vertsA = sequences[0][0]
            vertsB = sequences[1][0]

            vertsA, vertsB = align_vert_sequences(bm, vertsA, vertsB, mx=active.matrix_world, debug=False)

            edge = get_seam_edge(bm, vertsA, vertsB, debug=False)

        elif len(sequences) == 1:
            cyclic = False

            verts = sequences[0][0]

            cap_edges = get_cap_edges(bm, verts, mx=active.matrix_world, debug=False)

            if cap_edges:

                vertsA, vertsB = create_each_vert_sequence(cap_edges, verts, mx=active.matrix_world, debug=False)

                edge = cap_edges[0]

            else:
                errtitle = "Ambiguous Selection"
                errmsg = ["Cap edges could not be determined.", "Select them manually!"]

                return {'CANCELLED'}, errtitle, errmsg

        else:
            errtitle = "Illegal Selection"
            errmsg = "Make sure your selection is a polygon strip 1 face deep, cyclic or not, but without any holes!"

            return {'CANCELLED'}, errtitle, errmsg

        uv_coords = {}
        distanceA = create_uv_coords(uv_coords, vertsA, u=0, cyclic=cyclic, debug=False)
        distanceB = create_uv_coords(uv_coords, vertsB, u=edge.calc_length(), cyclic=cyclic, debug=False)

        align_uv_coords(uv_coords, vertsB, distanceA / distanceB)

        unwrap(uvs, faces, edge, vertsA, vertsB, uv_coords, cyclic=cyclic, debug=False)

        return False, "", ""

    def check_selection_depth(self, faces):
        for face in faces:
            selected_neighbors = [e for e in face.edges for f in e.link_faces if f != face and f.select]

            if len(selected_neighbors) > 2:
                return False
        return True
