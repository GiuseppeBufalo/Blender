import bpy
import bmesh
from mathutils import Vector, Matrix
from .. utils.decal import apply_decal, set_defaults, get_target
from .. utils.modifier import add_displace, add_nrmtransfer, get_displace, add_subd, add_shrinkwrap, get_subd, get_shrinkwrap, get_mods_as_dict, add_mods_from_dict, get_uvtransfer
from .. utils.raycast import get_origin_from_object_boundingbox
from .. utils.mesh import hide, unhide, blast, smooth, init_uvs, reset_material_indices
from .. utils.object import intersect, flatten, parent, update_local_view, lock, unshrinkwrap
from .. utils.math import remap, create_bbox, flatten_matrix
from .. utils.raycast import get_bvh_ray_distance_from_verts
from .. utils.ui import popup_message, init_cursor, init_status, finish_status
from .. utils.uv import get_uv_transfer_layer, get_active_uv_layer
from .. utils.collection import unlink_object
from .. utils.addon import gp_add_to_edit_mode_group
from .. utils.property import set_cycles_visibility
from .. utils.draw import draw_lines, draw_tris


class Project(bpy.types.Operator):
    bl_idname = "machin3.project_decal"
    bl_label = "MACHIN3: Project Decal"
    bl_description = "Project Selected Decals on Surface\nALT: Manually Adjust Projection Depth\nCTRL: Use UV Project instead of UV Transfer\nSHIFT: Shrinkwrap"
    bl_options = {'REGISTER', 'UNDO'}

    passthrough = False

    @classmethod
    def poll(cls, context):
        return any(obj.DM.isdecal and not obj.DM.isprojected and not obj.DM.issliced and not obj.DM.preatlasmats and not obj.DM.prejoindecals for obj in context.selected_objects)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

    def draw_VIEW3D(self, args):
        for decal, target, projected, (front, back), bbox in self.projections:
            coords, edge_indices, tri_indices = bbox

            mxcoords = []
            for idx, co in enumerate(coords):
                if idx > 3:
                    mxt = Matrix.Translation((0, 0, (back + abs(self.offset)) / decal.scale.z))
                    mxco = decal.matrix_world @ mxt @ Vector(co)
                else:
                    mxt = Matrix.Translation((0, 0, (-front - abs(self.offset)) / decal.scale.z))
                    mxco = decal.matrix_world @ mxt @ Vector(co)

                mxcoords.append(mxco)

            draw_lines(mxcoords, indices=edge_indices[:8], width=2, alpha=0.3, xray=False)

            draw_lines(mxcoords, indices=edge_indices[8:], width=1, alpha=0.2, xray=False)

            draw_tris(mxcoords, indices=tri_indices[:4], alpha=0.1, xray=False)

    def modal(self, context, event):
        context.area.tag_redraw()

        events = ['MOUSEMOVE']

        if event.type in events:

            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                elif not event.alt:
                    divisor = 1000 if event.shift else 10 if event.ctrl else 100

                    delta_x = event.mouse_x - self.last_mouse_x
                    delta_offset = delta_x / divisor

                    self.offset += delta_offset


        elif event.type in {'MIDDLEMOUSE'} or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}):
            self.passthrough = True
            return {'PASS_THROUGH'}


        elif event.type in {'LEFTMOUSE', 'SPACE'}:
            self.finish()

            for decal, target, projected, (front, back), bbox in self.projections:
                projected = self.project(context, event, decal, target, projected=projected, depth=(front + abs(self.offset), back + abs(self.offset)))

                if not projected:
                    self.failed.append(decal)

            if self.failed:
                self.report_errors(self.failed)

            return {'FINISHED'}


        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal()
            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x

        return {'RUNNING_MODAL'}

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

        finish_status(self)

    def cancel_modal(self):
        self.finish()

        for decal, target, projected, (front, back), bbox in self.projections:
            bpy.data.meshes.remove(projected.data, do_unlink=True)

    def invoke(self, context, event):
        self.dg = context.evaluated_depsgraph_get()

        self.active = context.active_object
        self.sel = context.selected_objects.copy()

        decals = [obj for obj in self.sel if obj.DM.isdecal and not obj.DM.isprojected and not obj.DM.issliced and not obj.DM.preatlasmats and not obj.DM.prejoindecals]

        for obj in self.sel:
            if obj not in decals:
                obj.select_set(False)

        if event.alt:
            if self.invoke_modal(context, event, decals):
                return {'RUNNING_MODAL'}

            elif self.failed:
                self.report_errors(self.failed)

        else:
            self.invoke_simple(context, event, decals)

        return {'FINISHED'}

    def invoke_modal(self, context, event, decals):
        self.projections = []
        self.failed = []

        for decal in decals:
            target = get_target(self.dg, self.active, self.sel, decal)

            if target:
                if target != decal.parent:
                    apply_decal(self.dg, decal, target=target)

                projected = target.copy()
                projected.data = bpy.data.meshes.new_from_object(target.evaluated_get(self.dg))
                projected.modifiers.clear()
                projected.name = decal.name + "_projected"

                front, back = get_bvh_ray_distance_from_verts(projected, decal, (0, 0, -1), 0.1)

                if front + back < 0.001 * decal.scale.z:
                    front = back = 0.001 * decal.scale.z

                bbox = create_bbox(decal)

                self.projections.append((decal, target, projected, (front, back), bbox))

            else:
                self.failed.append(decal)


        if self.projections:

            self.offset = 0

            init_cursor(self, event)

            init_status(self, context, 'Project')

            args = (context, event)
            self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (args, ), 'WINDOW', 'POST_VIEW')

            context.window_manager.modal_handler_add(self)
            return True

    def invoke_simple(self, context, event, decals):
        failed = []

        for decal in decals:
            target = get_target(self.dg, self.active, self.sel, decal)

            if target:

                if target != decal.parent:
                    apply_decal(self.dg, decal, target=target)

                if event.shift:
                    self.shrinkwrap(context, decal, target)

                else:
                    projected = self.project(context, event, decal, target)

                    if not projected:
                        failed.append(decal)

            else:
                failed.append(decal)

        if failed:
            self.report_errors(failed)

    def report_errors(self, failed):
        msg = ["Projecting the following decals failed:"]

        for obj in failed:
            msg.append(" • " + obj.name)

        msg.append("Try Re-Applying the decal first!")
        msg.append("You can also force-project on a non-decal object by selecting it last.")

        popup_message(msg)

    def project(self, context, event, decal, target, projected=None, depth=None):
        mirrors = [mod for mod in decal.modifiers if mod.type == "MIRROR" and mod.show_render and mod.show_viewport]

        for mod in mirrors:
            mod.show_viewport = False

        unshrinkwrap(decal)

        if event.ctrl:
            uvempty = bpy.data.objects.new("uvempty", None)
            context.collection.objects.link(uvempty)

            self.align_uvempty(uvempty, decal)

        if not projected:
            projected = target.copy()
            projected.data = bpy.data.meshes.new_from_object(target.evaluated_get(self.dg))
            projected.modifiers.clear()
            projected.modifiers.clear()
            projected.name = decal.name + "_projected"

        for col in decal.users_collection:
            col.objects.link(projected)

        unhide(projected.data)
        hide(decal.data)

        if not depth:
            front, back = get_bvh_ray_distance_from_verts(projected, decal, (0, 0, -1), 0.1)

            if front + back < 0.001 * decal.scale.z:
                front = back = 0.001 * decal.scale.z

            factor = 1.2

        else:
            front, back = depth

            factor = 1.01


        thickness = (front + back) / decal.scale.z

        solidify = decal.modifiers.new(name="Solidify", type="SOLIDIFY")
        solidify.thickness = thickness * factor
        solidify.offset = remap(0, -back, front, -1 / factor, 1 / factor)

        displace = get_displace(decal)
        if displace:
            displace.show_viewport = False

        intersect(projected, decal)
        flatten(projected)

        blast(projected.data, "hidden", "FACES")

        parent(projected, target)

        projected.DM.isdecal = True
        projected.DM.isprojected = True
        projected.DM.projectedon = target
        projected.DM.decalbackup = decal
        projected.DM.uuid = decal.DM.uuid
        projected.DM.version = decal.DM.version
        projected.DM.decaltype = decal.DM.decaltype
        projected.DM.decallibrary = decal.DM.decallibrary
        projected.DM.decalname = decal.DM.decalname
        projected.DM.decalmatname = decal.DM.decalmatname
        projected.DM.creator = decal.DM.creator

        projected.DM.istrimdecal = decal.DM.istrimdecal

        if projected.DM.istrimdecal:
            projected.DM.trimsheetuuid = decal.DM.trimsheetuuid

        set_cycles_visibility(projected, 'shadow', False)
        set_cycles_visibility(projected, 'diffuse', False)


        decal.modifiers.remove(solidify)
        unhide(decal.data)

        if displace:
            displace.show_viewport=True

        if not self.validate_projected(projected, decal):
            bpy.data.meshes.remove(projected.data, do_unlink=True)
            for mod in mirrors:
                mod.show_viewport = True

            return False

        init_uvs(projected.data)


        reset_material_indices(projected.data)

        if event.ctrl:
            uvproject = projected.modifiers.new(name="UVProject", type="UV_PROJECT")
            uvproject.projectors[0].object = uvempty
            flatten(projected)
            bpy.data.objects.remove(uvempty, do_unlink=True)

        else:
            uvtransfer = projected.modifiers.new(name="UVTransfer", type="DATA_TRANSFER")
            uvtransfer.object = decal
            uvtransfer.use_loop_data = True
            uvtransfer.loop_mapping = 'POLYINTERP_NEAREST'
            uvtransfer.data_types_loops = {'UV'}
            uvtransfer.layers_uv_select_dst = 'INDEX'
            flatten(projected)

        projected.data.materials.clear()  # actually no longer necessary, materials are cleared and obj is flattened
        if decal.active_material:
            projected.data.materials.append(decal.active_material)

        add_displace(projected)

        for mod in mirrors:
            mirror = projected.modifiers.new(name=mod.name, type="MIRROR")
            mirror.use_axis = mod.use_axis
            mirror.use_mirror_u = mod.use_mirror_u
            mirror.use_mirror_v = mod.use_mirror_v
            mirror.mirror_object = mod.mirror_object

        nrmtransfer = add_nrmtransfer(projected, target)

        set_defaults(decalobj=projected)

        lock(projected)

        projected.select_set(True)

        if context.active_object == decal:
            context.view_layer.objects.active = projected

        decal.use_fake_user = True
        decal.DM.isbackup = True

        unlink_object(decal)

        decal.DM.backupmx = flatten_matrix(target.matrix_world.inverted_safe() @ decal.matrix_world)

        gp_add_to_edit_mode_group(context, projected)

        update_local_view(context.space_data, [(projected, True)])

        if projected.data.has_custom_normals:
            bpy.ops.mesh.customdata_custom_splitnormals_clear({'object': projected})

        if get_uv_transfer_layer(decal, create=False) and get_uvtransfer(decal):
            self.setup_uv_transfer(context, decal, projected, nrmtransfer)

        return True



    def align_uvempty(self, uvempty, decal):
        loc = get_origin_from_object_boundingbox(self.dg, decal)

        _, rot, _ = decal.matrix_world.decompose()

        sca = Matrix()
        sca[0][0] = decal.dimensions.x / 2
        sca[1][1] = decal.dimensions.y / 2
        sca[2][2] = 1

        uvempty.matrix_world = Matrix.Translation(loc) @ rot.to_matrix().to_4x4() @ sca

    def validate_projected(self, projected, decal):

        if not projected.data.polygons:
            return False

        dmxw = decal.matrix_world
        origin, _, _ = dmxw.decompose()
        direction = dmxw @ Vector((0, 0, -1)) - origin

        pmxw = projected.matrix_world
        pmxi = pmxw.inverted_safe()
        direction_local = pmxi.to_3x3() @ direction

        bm = bmesh.new()
        bm.from_mesh(projected.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        backfaces = [f for f in bm.faces if f.normal.dot(direction_local) > 0]

        bmesh.ops.delete(bm, geom=backfaces, context="FACES")

        if bm.faces:
            bm.to_mesh(projected.data)
            bm.clear()
            return True

        else:
            return False

    def shrinkwrap(self, context, decal, target):
        smooth(decal.data)

        mirrors = get_mods_as_dict(decal, types=['MIRROR'])

        displace = get_displace(decal)
        midlevel = displace.mid_level if displace else None

        isuvtransfer = get_uv_transfer_layer(decal, create=False) and get_uvtransfer(decal)

        decal.modifiers.clear()

        add_subd(decal)
        add_shrinkwrap(decal, target)

        displace = add_displace(decal)
        if midlevel:
            displace.mid_level = midlevel

        add_mods_from_dict(decal, mirrors)

        nrmtransfer = add_nrmtransfer(decal, target)

        set_defaults(decalobj=decal)

        if isuvtransfer:
            self.setup_uv_transfer(context, decal, decal, nrmtransfer)


    def setup_uv_transfer(self, context, decal, projected, mod):

        context.view_layer.objects.active = projected

        transfer_uvs = get_uv_transfer_layer(projected, create=True)
        source_uvs = get_active_uv_layer(decal.parent)

        mod.name = 'NormalUVTransfer'
        mod.data_types_loops = {'CUSTOM_NORMAL', 'UV'}

        mod.layers_uv_select_src = source_uvs.name
        mod.layers_uv_select_dst = transfer_uvs.name


class UnShrinkwrap(bpy.types.Operator):
    bl_idname = "machin3.unshrinkwrap_decal"
    bl_label = "MACHIN3: Unshrinkwrap"
    bl_description = "Un-Shrinkwrap, turn shrinkwrapped decal back into flat one."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        decals = [obj for obj in context.selected_objects if obj.DM.isdecal]
        return decals and any(get_shrinkwrap(obj) or get_subd(obj) for obj in decals)

    def execute(self, context):
        decals = [obj for obj in context.selected_objects if obj.DM.isdecal]

        for obj in decals:
            unshrinkwrap(obj)

            smooth(obj.data, smooth=False)

        return {'FINISHED'}
