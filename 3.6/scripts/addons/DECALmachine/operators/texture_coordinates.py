import bpy
from bpy.props import BoolProperty
import bmesh
from mathutils import Vector
from .. utils.uv import get_uv_transfer_layer, get_active_uv_layer
from .. utils.ui import popup_message
from .. utils.material import get_decalmats, get_decalgroup_from_decalmat, get_atlasmats, get_atlasgroup_from_atlasmat
from .. utils.material import transfer_parent_textures, transfer_parallax, restore_detail_normal_links
from .. utils.modifier import get_nrmtransfer


class InitGeneratedCoordinates(bpy.types.Operator):
    bl_idname = "machin3.init_generated_coordinates"
    bl_label = "MACHIN3: Initialize Generated Coordinates"
    bl_description = "Prepare projected and sliced decals for generated texture coordinates by creating lone verts in the bounding box corners of the decal parent"
    bl_options = {'REGISTER', 'UNDO'}

    evaluated: BoolProperty(name="Use evaluated Geometry", default=False)

    def draw(self, context):
        layout = self.layout

        column = layout.column()
        column.prop(self, "evaluated", toggle=True)

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.DM.isdecal and (obj.DM.isprojected or obj.DM.issliced)]

    def execute(self, context):
        candidates = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.DM.isdecal and (obj.DM.isprojected or obj.DM.issliced)]

        if candidates:

            init = {}

            for obj in candidates:
                if obj.DM.isprojected:
                    target = obj.DM.projectedon if obj.DM.projectedon else obj.parent if obj.parent else None

                elif obj.DM.issliced:
                    target = obj.DM.slicedon if obj.DM.slicedon else obj.parent if obj.parent else None

                if target:
                    if target in init:
                        init[target].append(obj)

                    else:
                        init[target] = [obj]

            for target, decals in init.items():
                mirrors = []

                if not self.evaluated:
                    mirrors = [mod for mod in target.modifiers if mod.type == 'MIRROR' and mod.show_viewport]

                    for mod in mirrors:
                        mod.show_viewport = False

                context.view_layer.update()

                coords = [Vector(co) for co in target.bound_box]

                for mod in mirrors:
                    mod.show_viewport = True

                for decal in decals:
                    bm = bmesh.new()
                    bm.from_mesh(decal.data)
                    bm.normal_update()
                    bm.verts.ensure_lookup_table()

                    loose_verts = [v for v in bm.verts if not v.link_edges]
                    bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")

                    for co in coords:
                        bm.verts.new(co)

                    bm.to_mesh(decal.data)
                    bm.clear()

                    decal.data.update()

        return {'FINISHED'}






class UVTransfer(bpy.types.Operator):
    bl_idname = "machin3.uv_transfer"
    bl_label = "MACHIN3: UV Transfer"
    bl_description = "Transfer UVs and and all Image Textures from Decal Parent Material over to the Decal\nALT: Remove UVTransfer"
    bl_options = {'REGISTER', 'UNDO'}

    remove: BoolProperty(name="Remove a previously created UV Transfer")

    use_normals: BoolProperty(name="Use Normal Map")
    use_parallax: BoolProperty(name="Use Parallax for Transferred Maps")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.DM.isdecal and (get_decalmats(obj) or get_atlasmats(obj))]

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        if not self.remove:
            box = column.box()

            col = box.column(align=True)
            col.label(text="The following will only work if Decal and Parent", icon='INFO')
            col.label(text="UV spaces are oriented the same way!", icon='BLANK1')
            col.label(text="Usually this will not be the case.", icon='BLANK1')

            row = column.row(align=True)
            row.prop(self, 'use_normals', toggle=True)
            row.prop(self, 'use_parallax', text="Use Parallax", toggle=True)

    def invoke(self, context, event):
        self.remove = event.alt
        return self.execute(context)

    def execute(self, context):
        decals = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.DM.isdecal and obj.parent and (get_decalmats(obj) or get_atlasmats(obj))]
        missing_parents = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.DM.isdecal and not obj.parent]

        seen = []

        for decal in decals:

            if self.remove:
                transfer_uvs = get_uv_transfer_layer(decal, create=False)

                if transfer_uvs:
                    decal.data.uv_layers.remove(transfer_uvs)

                mod = get_nrmtransfer(decal, create=False)

                if mod and 'UVTransfer' in mod.name:
                    mod.name = 'NormalTransfer'
                    mod.data_types_loops = {'CUSTOM_NORMAL'}
                    mod.use_poly_data = False
                    mod.layers_uv_select_src = 'ALL'
                    mod.layers_uv_select_dst = 'NAME'

            else:
                mod = self.setup_transfer_mod(decal)
                source_uvs, transfer_uvs = self.setup_uv_transfer(context, decal, mod)


            materials = get_decalmats(decal) + get_atlasmats(decal)

            for mat in materials:

                if mat in seen:
                    continue

                else:
                    seen.append(mat)
                    tree = mat.node_tree
                    atlas = mat.DM.isatlasmat

                    if self.remove:
                        remove = [node for node in tree.nodes if node.name == 'UVTRANSFER' or '[UVTRANSFER]' in node.name]

                        for node in remove:
                            tree.nodes.remove(node)

                        group = get_atlasgroup_from_atlasmat(mat) if atlas else get_decalgroup_from_decalmat(mat)

                        if not atlas:
                            restore_detail_normal_links(tree, group)

                        for idx, slot in enumerate(decal.material_slots):
                            if slot.material == mat:
                                decal.active_material_index = idx

                        decal.active_material = decal.active_material

                    else:

                        for node in tree.nodes:
                            node.select = False

                        transferuvs = tree.nodes.get('UVTRANSFER')

                        if transferuvs:
                            transferuvs.select = True

                            for node in tree.nodes:
                                if '[UVTRANSFER]' in node.name:
                                    tree.nodes.remove(node)

                        else:
                            transferuvs = tree.nodes.new('ShaderNodeUVMap')
                            transferuvs.location = Vector((-1200, 500))
                            transferuvs.label = 'UVTransfer'
                            transferuvs.name = 'UVTRANSFER'

                        transferuvs.uv_map = transfer_uvs.name

                        imgnodes = transfer_parent_textures(decal.parent, mat, tree, transferuvs, use_normals=self.use_normals, atlas=atlas)

                        if self.use_parallax:
                            transfer_parallax(mat, tree, transferuvs, imgnodes, atlas=atlas)

        if missing_parents and not self.remove:
            msg = [f'''The following (now unselected) {"Decals don't have parent objects" if len(missing_parents) > 1 else "Decal doesn't have a parent object"}, so UV's couldn't be transfered''']

            for obj in missing_parents:
                obj.select_set(False)

                msg.append(f" • {obj.name}")

            msg.append("Use the Re-Apply tool to fix this.")
            popup_message(msg, title="Missing Decal Parents")


        return {'FINISHED'}

    def setup_transfer_mod(self, decal):
        mod = get_nrmtransfer(decal)

        if not mod.object or mod.object != decal.parent:
            mod.object = decal.parent

        if mod.name == 'NormalTransfer' and mod.object:
            mod.name = 'NormalUVTransfer'

        mod.data_types_loops = {'CUSTOM_NORMAL', 'UV'}
        return mod

    def setup_uv_transfer(self, context, decal, mod):

        context.view_layer.objects.active = decal

        transfer_uvs = get_uv_transfer_layer(decal, create=True)

        source_uvs = get_active_uv_layer(decal.parent)

        mod.layers_uv_select_src = source_uvs.name
        mod.layers_uv_select_dst = transfer_uvs.name

        return source_uvs, transfer_uvs
