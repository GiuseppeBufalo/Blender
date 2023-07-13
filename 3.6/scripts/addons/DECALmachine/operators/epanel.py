import bpy
import bmesh
from .. utils.selection import get_selected_vert_sequences, get_vert_sequences
from .. utils.decal import create_float_slice_geometry, get_panel_width, create_panel_uvs, finish_panel_decal, clear_decalobj_props
from .. utils.raycast import find_nearest_normals, shrinkwrap, get_closest
from .. utils.collection import sort_into_collections
from .. utils.addon import gp_add_to_edit_mode_group
from .. utils.object import update_local_view, unparent, unlock


class EPanel(bpy.types.Operator):
    bl_idname = "machin3.epanel"
    bl_label = "MACHIN3: Edge Panel"
    bl_description = "Create Panel Decals from edges in EDIT mode or from and edge-only object in OBJECT mode\nSHIFT: In EDIT mode, mark edges as MESHCUTS\nCTRL: in EDIT mode, remove edges immediately.\nALT: In EDIT mode, create edge-only object"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        column = layout.column()

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            active = context.active_object
            bm = bmesh.from_edit_mesh(active.data)
            return bm.faces and [e for e in bm.edges if e.select] and len([f for f in bm.faces if f.select]) <= 1

        elif context.mode == 'OBJECT':
            sel = context.selected_objects
            active = context.active_object

            if active and active.type == 'MESH':
                if len(sel) == 1 and active in sel and not active.data.polygons and active.data.edges:
                    return True

                elif len(sel) == 2:
                    sel_objs = [obj for obj in sel if obj != active and obj.type == 'MESH']
                    return sel_objs[0] if sel_objs and not sel_objs[0].data.polygons and sel_objs[0].data.edges else None

    def invoke(self, context, event):
        dg = context.evaluated_depsgraph_get()
        col = context.collection
        active = context.active_object

        if context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')

            if event.alt:
                name = "EPanel Object"
                edgeonly = active.copy()
                edgeonly.name = "EPanel Object"
                edgeonly.modifiers.clear()

                unparent(edgeonly)
                unlock(edgeonly)

                clear_decalobj_props(edgeonly)

                mesh = bpy.data.meshes.new(name=name)
                edgeonly.data = mesh

                col.objects.link(edgeonly)

            else:
                panel = bpy.data.objects.new("Panel Decal", object_data=bpy.data.meshes.new("Panel Decal"))
                panel.matrix_world = active.matrix_world
                col.objects.link(panel)


            bm = bmesh.new()
            bm.from_mesh(active.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            if event.shift:
                s = bm.edges.layers.string.verify()

            verts = [v for v in bm.verts if v.select]
            edges = [e for e in bm.edges if e.select]

            if event.alt:
                self.create_edge_only_object(context, dg, event, bm, active, edgeonly, verts, edges, s if event.shift else None)
                return {'FINISHED'}

            else:
                self.create_panel_decal_from_edges(context, dg, event, bm, active, panel, verts, edges, s if event.shift else None)

            target = active.parent if active.DM.isdecal and active.parent else active

            backup = None

        elif context.mode == 'OBJECT':
            panel, target, backup = self.create_panel_decal_from_object(context, dg, active)

            panel.name = "Panel Decal"
            panel.data.name = "Panel Decal"

        finish_panel_decal(dg, context, panel, target, backup)

        sort_into_collections(context, panel)

        context.view_layer.objects.active = panel
        bpy.ops.object.select_all(action='DESELECT')
        panel.select_set(True)

        gp_add_to_edit_mode_group(context, panel)

        update_local_view(context.space_data, [(panel, True)])

        if panel.data.has_custom_normals:
            bpy.ops.mesh.customdata_custom_splitnormals_clear({'object': panel})

        return {'FINISHED'}

    def create_panel_decal_from_object(self, context, depsgraph, active):
        sel = context.selected_objects

        if active.type == 'MESH':
            if len(sel) == 1 and active in sel and not active.data.polygons and active.data.edges:
                if active.parent:
                    target = active.parent

                else:
                    origin = active.matrix_world @ active.data.vertices[1].co
                    targets = [obj for obj in context.visible_objects if not obj.DM.isdecal and obj.type == 'MESH']

                    target, _, _, _, _, _ = get_closest(depsgraph, targets, origin, debug=False)

                panel = active

            elif len(sel) == 2:
                target = active
                panel = [obj for obj in sel if obj != active][0]

        if panel and target:
            panel.data.materials.clear()
            panel.modifiers.clear()

            backup = panel.copy()
            backup.data = panel.data.copy()

            if panel.matrix_world != target.matrix_world:
                panel.data.transform(target.matrix_world.inverted_safe() @ panel.matrix_world)
                panel.matrix_world = target.matrix_world

            width = get_panel_width(panel, context.scene)

            bm = bmesh.new()
            bm.from_mesh(panel.data)
            bm.verts.ensure_lookup_table()

            verts = [v for v in bm.verts]
            verts_init = verts.copy()

            sequences = get_vert_sequences(verts, ensure_seq_len=True, debug=False)

            normals, bmt = find_nearest_normals(bm, target.evaluated_get(depsgraph).to_mesh(), debug=False)

            geo = create_float_slice_geometry(bm, panel.matrix_world, sequences, normals, width=width)

            bmesh.ops.delete(bm, geom=verts_init, context='VERTS')

            shrinkwrap(bm, bmt)

            create_panel_uvs(bm, geo, panel, width=width)

            bm.free()
            bmt.free()

            depsgraph.update()

            return panel, target, backup

        else:
            return {'CANCELLED'}

    def create_panel_decal_from_edges(self, context, depsgraph, event, bm, active, panel, verts, edges, layer):
        sequences = get_selected_vert_sequences(verts, ensure_seq_len=True, debug=False)

        normals = {}

        for seq, cyclic in sequences:
            for v in seq:
                normals[v] = v.normal

        width = get_panel_width(panel, context.scene)

        bmp = bmesh.new()

        geo = create_float_slice_geometry(bmp, panel.matrix_world, sequences, normals, width, debug=False)

        create_panel_uvs(bmp, geo, panel, width=width)

        if event.shift:
            for e in edges:
                e[layer] = 'MESHCUT'.encode()
                e.seam = True

        elif event.ctrl:
            bmesh.ops.dissolve_edges(bm, edges=edges, use_verts=True)

        if event.shift or event.ctrl:
            bm.to_mesh(active.data)

            depsgraph.update()

        panel.data.update()

        bmp.free()
        bm.free()

    def create_edge_only_object(self, context, depsgraph, event, bm, active, edgeonly, verts, edges, layer):
        bmeo = bmesh.new()
        bmeo.from_mesh(edgeonly.data)

        vdict = {}
        for v in verts:
            veo = bmeo.verts.new()
            veo.co = v.co
            vdict[v] = veo

        for e in edges:
            v1, v2 = e.verts
            bmeo.edges.new([vdict[v1], vdict[v2]])

        bmeo.to_mesh(edgeonly.data)
        bmeo.free()

        del vdict

        if event.shift:
            for e in edges:
                e[layer] = 'MESHCUT'.encode()
                e.seam = True

        elif event.ctrl:
            bmesh.ops.dissolve_edges(bm, edges=edges, use_verts=True)

        if event.shift or event.ctrl:
            bm.to_mesh(active.data)
            bm.free()

        depsgraph.update()

        update_local_view(context.space_data, [(edgeonly, True)])

        context.view_layer.objects.active = edgeonly
        active.select_set(False)
        edgeonly.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
