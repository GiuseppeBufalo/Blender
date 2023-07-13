import bpy
from bpy.props import BoolProperty, FloatProperty
import os
import bmesh
from mathutils import Vector, Matrix, geometry
from .. utils.material import remove_decalmat, get_decalmat, get_decalgroup_from_decalmat, get_pbrnode_from_mat, get_decal_texture_nodes
from .. utils.registration import get_prefs, get_templates_path
from .. utils.decal import set_decalobj_props_from_material, set_decalobj_name
from .. utils.create import render_thumbnail, save_blend
from .. utils.modifier import add_displace
from .. utils.append import append_nodetree, append_object
from .. utils.ui import get_icon
from .. utils.math import flatten_matrix, create_rotation_difference_matrix_from_quat, get_center_between_verts
from .. utils.object import flatten
from .. utils.trim import get_trim, get_sheetdata_from_uuid
from .. utils.math import trimmx_to_box_coords, trimmx_to_img_coords, img_coords_to_trimmx, get_loc_matrix, get_rot_matrix, get_sca_matrix
from .. utils.uv import get_trim_uv_bbox


class DebugWhatever(bpy.types.Operator):
    bl_idname = "machin3.debug_whatever"
    bl_label = "MACHIN3: Debug Whatever"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):

        return {'FINISHED'}


class TrimMatrixConversion(bpy.types.Operator):
    bl_idname = "machin3.trim_matrix_conversion"
    bl_label = "MACHIN3: Trim Matrix Conversion"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object if context.active_object and context.active_object.DM.istrimsheet else None

    def execute(self, context):
        sheet = context.active_object

        idx, trims, active = get_trim(sheet)

        trimmx = active.mx
        print(trimmx)

        top_left, bottom_right = trimmx_to_box_coords(trimmx, sheet.dimensions)
        print("trimmx to box coords:", top_left.xy, bottom_right.xy)

        resolution = Vector(sheet.DM.trimsheetresolution)
        location = Vector(trimmx.col[3][:2])
        scale = Vector((trimmx[0][0], trimmx[1][1]))

        (bottom_left, top_right), _ = get_trim_uv_bbox(resolution, location, scale)
        print("     trim to uv bbox:", bottom_left, top_right)

        resolution = Vector(int(d * 1000) for d in sheet.dimensions[:2])

        coords, dimensions = trimmx_to_img_coords(trimmx, resolution)
        print("trimmx to img coords:", coords, dimensions)

        trimmx = img_coords_to_trimmx(coords, dimensions, list(resolution))
        print(trimmx)

        print(20 * "=")

        decal_res = (100, 100)
        atlas_res = (1000, 1000)

        top_left = (0, 0)


        top_lefts = [(0, 0), (2, 0), (123000, 3000309), (372172112, 0), (2200000000, 0)]

        for top_left in top_lefts:
            print()

            print("decal coords:", top_left)
            print("decal resolution:", decal_res)

            trimmx = img_coords_to_trimmx(top_left, decal_res, atlas_res)

            top_left, dimensions = trimmx_to_img_coords(trimmx, atlas_res)

            print("decal coords:", top_left)
            print("decal resolution:", dimensions)

        return {'FINISHED'}


class DebugToggle(bpy.types.Operator):
    bl_idname = "machin3.decalmachine_debug"
    bl_label = "MACHIN3: Debug DECALmachine"
    bl_description = "Toggle DECALmachine Developer Tools"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        dm = context.scene.DM
        dm.debug = not dm.debug
        return {'FINISHED'}


class ReRenderThumbnails(bpy.types.Operator):
    bl_idname = "machin3.rerender_decal_thumbnails"
    bl_label = "MACHIN3: Re-Render Decal Thumbnails"
    bl_description = "Re-Render Decal Thumbnails of the Selected User Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        assetspath = get_prefs().assetspath
        librarypath = os.path.join(assetspath, 'Decals', scene.userdecallibs)

        folders = sorted([f for f in os.listdir(librarypath) if os.path.isdir(os.path.join(librarypath, f))])

        for folder in folders:
            decalpath = os.path.join(librarypath, folder)
            blendpath = os.path.join(decalpath, "decal.blend")

            if os.path.exists(blendpath):
                decal = append_object(blendpath, "LIBRARY_DECAL")

                if decal:
                    decalmat = get_decalmat(decal)

                    if decalmat:
                        render_thumbnail(context, decalpath, decal, decalmat, removeall=True)


        return {'FINISHED'}


class UpdateNodeTree(bpy.types.Operator):
    bl_idname = "machin3.update_decal_node_tree"
    bl_label = "MACHIN3: update_decal_node_tree"
    bl_description = "Updatees Decal Node Tree in selected User Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        assetspath = get_prefs().assetspath
        librarypath = os.path.join(assetspath, 'Decals', scene.userdecallibs)

        templatepath = get_templates_path()

        folders = sorted([f for f in os.listdir(librarypath) if os.path.isdir(os.path.join(librarypath, f))])

        for folder in folders:
            decalpath = os.path.join(librarypath, folder)
            blendpath = os.path.join(decalpath, "decal.blend")

            treetypes = ['subset', 'panel']

            while treetypes:
                treetype = treetypes.pop(0)
                nt = append_nodetree(blendpath, "%s.LIBRARY_DECAL" % (treetype))

                if nt:
                    print("found a %s decal: %s" % (treetype, blendpath))
                    bpy.data.node_groups.remove(nt, do_unlink=True)

                    decal = append_object(blendpath, "LIBRARY_DECAL")
                    newnt = append_nodetree(templatepath, "%s.TEMPLATE_%s" % (treetype, treetype.upper()))

                    decalscene = bpy.data.scenes.new(name="Decal Asset")
                    decalscene.collection.objects.link(decal)

                    decalmat = get_decalmat(decal)
                    dg = get_decalgroup_from_decalmat(decalmat)

                    from_node = dg.inputs['Masks'].links[0].from_node

                    oldnt = dg.node_tree
                    dg.node_tree = newnt
                    newnt.name = oldnt.name

                    bpy.data.node_groups.remove(oldnt, do_unlink=True)

                    decalmat.node_tree.links.new(from_node.outputs[0], dg.inputs['Masks'])

                    save_blend(decal, decalpath, decalscene)

                    remove_decalmat(decalmat, remove_textures=True)

                    bpy.data.meshes.remove(decal.data, do_unlink=True)

                    break


        return {'FINISHED'}


class UpdateInterpolation(bpy.types.Operator):
    bl_idname = "machin3.update_interpolation"
    bl_label = "MACHIN3: Update Masks Interpolation"
    bl_description = "Updates Decal Masks Interpolation selected User Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        assetspath = get_prefs().assetspath
        librarypath = os.path.join(assetspath, 'Decals', scene.userdecallibs)

        folders = sorted([f for f in os.listdir(librarypath) if os.path.isdir(os.path.join(librarypath, f))])

        for folder in folders:
            decalpath = os.path.join(librarypath, folder)
            blendpath = os.path.join(decalpath, "decal.blend")

            print()
            print(blendpath)

            decal = append_object(blendpath, "LIBRARY_DECAL")

            decalscene = bpy.data.scenes.new(name="Decal Asset")
            decalscene.collection.objects.link(decal)

            mat = get_decalmat(decal)

            nodes = get_decal_texture_nodes(mat)

            updated = False

            if 'MASKS' in nodes:
                masks = nodes['MASKS']

                if masks.interpolation == 'Closest':
                    masks.interpolation = 'Linear'
                    print(" changed masks interpolation to Linear")
                    updated = True

            if 'EMISSION' in nodes:
                emission = nodes['EMISSION']

                if emission.interpolation == 'Closest':
                    emission.interpolation = 'Linear'
                    print(" changed emission interpolation to Linear")
                    updated = True

            if updated:
                save_blend(decal, decalpath, decalscene)
                print(" saved changed!")

            else:
                print(" no changes required")

            remove_decalmat(mat, remove_textures=True)

            bpy.data.meshes.remove(decal.data, do_unlink=True)

        return {'FINISHED'}


class UpdateModifierCollapse(bpy.types.Operator):
    bl_idname = "machin3.update_modifier_collapse"
    bl_label = "MACHIN3: Update Modifier Collapse"
    bl_description = "Update Modifier Collapse"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        assetspath = get_prefs().assetspath

        libs = [lib for lib in get_prefs().decallibsCOL if not lib.istrimsheet]


        for lib in libs:
            print()
            print(lib.name)

            libpath = os.path.join(assetspath, 'Decals', lib.name)

            folders = sorted([f for f in os.listdir(libpath) if os.path.isdir(os.path.join(libpath, f))])

            for folder in folders:

                print("", folder)

                decalpath = os.path.join(libpath, folder)
                blendpath = os.path.join(decalpath, "decal.blend")

                decal = append_object(blendpath, "LIBRARY_DECAL")

                decalscene = bpy.data.scenes.new(name="Decal Asset")
                decalscene.collection.objects.link(decal)

                mods = [mod for mod in decal.modifiers if mod.show_expanded]

                if mods:
                    for mod in mods:
                        print(" collapsing", mod.name)
                        mod.show_expanded = False

                    save_blend(decal, decalpath, decalscene)
                    print(" changes saved!")


                else:
                    print(" no changes required")

                mat = get_decalmat(decal)

                remove_decalmat(mat, remove_textures=True)
                bpy.data.meshes.remove(decal.data, do_unlink=True)

        return {'FINISHED'}


class UpdateAddNodesClamping(bpy.types.Operator):
    bl_idname = "machin3.update_add_nodes_clamping"
    bl_label = "MACHIN3: Update Add Nodes Clamping"
    bl_description = "Updates Add Node Clamping in Decal Node Trees in selected User Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        assetspath = get_prefs().assetspath

        templatepath = get_templates_path()

        libs = get_prefs().decallibsCOL


        for lib in libs:

            print()
            libpath = os.path.join(assetspath, 'Trims' if lib.istrimsheet else 'Decals', lib.name)
            print("Library:", lib.name)

            folders = sorted([f for f in os.listdir(libpath) if os.path.isdir(os.path.join(libpath, f))])

            for folder in folders:
                decalpath = os.path.join(libpath, folder)
                blendpath = os.path.join(decalpath, 'decal.blend')
                print("Decal:", folder)

                treenames = ['simple.decal_group', 'subset.decal_group', 'panel.decal_group']

                if bpy.app.version < (3, 0, 0):
                    treenames = ['simple.LIBRARY_DECAL', 'subset.LIBRARY_DECAL', 'panel.LIBRARY_DECAL'] + treenames

                for treename in treenames:
                    nt = append_nodetree(blendpath, treename)

                    if nt:

                        bpy.data.node_groups.remove(nt, do_unlink=True)

                        self.remove_linked_library(os.path.basename(blendpath), debug=False)

                        decal = append_object(blendpath, "LIBRARY_DECAL")

                        decalmat = decal.active_material
                        dg = get_decalgroup_from_decalmat(decalmat)

                        if decalmat:
                            add_nodes = [node for node in dg.node_tree.nodes if node.type == 'MIX_RGB' and node.blend_type == 'ADD']

                            if any(node.use_clamp for node in add_nodes):
                                print(" INFO: Skipping, as ADD nodes are already clamped!")

                                self.remove_decal(decal)

                                self.remove_linked_library(os.path.basename(blendpath), debug=False)

                                break

                        treetype = treename.split('.')[0]
                        newnt = append_nodetree(templatepath, f"{treetype}.decal_group")

                        decalscene = bpy.data.scenes.new(name="Decal Asset")
                        decalscene.collection.objects.link(decal)

                        bpy.data.node_groups.remove(dg.node_tree, do_unlink=True)

                        dg.node_tree = newnt
                        newnt.name = f"{treetype}.decal_group"

                        save_blend(decal, decalpath, decalscene)

                        self.remove_decal(decal)

                        self.remove_linked_library(os.path.basename(blendpath), debug=False)
                        self.remove_linked_library(os.path.basename(templatepath), debug=False)

                        print(" INFO: Updated ADD nodes!")

                        break

                    self.remove_linked_library(os.path.basename(blendpath), debug=False)






        context.window.scene = scene

        return {'FINISHED'}

    def remove_linked_library(self, name, debug=False):

        linked_library = bpy.data.libraries.get(name)

        if linked_library:
            if debug:
                print(f" INFO: removing linked_library '{name}'")
            bpy.data.libraries.remove(linked_library)

    def remove_decal(self, obj):
        if obj.active_material:
            remove_decalmat(obj.active_material, remove_textures=True)

        bpy.data.meshes.remove(obj.data, do_unlink=True)


class ReplaceMaterial(bpy.types.Operator):
    bl_idname = "machin3.replace_material"
    bl_label = "MACHIN3: Replace Material"
    bl_description = "Replace Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object in context.selected_objects

    def execute(self, context):
        active = context.active_object
        sel = [obj for obj in context.selected_objects if obj != active]

        activemat = active.active_material

        if sel and activemat:
            for obj in sel:
                obj.data.materials.clear()
                obj.data.materials.append(activemat)

        return {'FINISHED'}


class SetPropsAndNameFromMaterial(bpy.types.Operator):
    bl_idname = "machin3.set_props_and_name_from_material"
    bl_label = "MACHIN3: Set Props and Name from Material"
    bl_description = "Set decal props and name from material"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        for obj in context.selected_objects:
            context.view_layer.objects.active = obj

            decalmat = get_decalmat(obj)

            if decalmat:
                obj.DM.isdecal = True
                obj.DM.decaltype = decalmat.DM.decaltype

                set_decalobj_props_from_material(obj, decalmat)

                set_decalobj_name(obj)

                obj.hide_viewport = True

                displace = False
                nrmtransfer = False

                for mod in obj.modifiers:
                    if mod.type == "DISPLACE":
                        displace = mod
                        mod.name = "Displace"

                    elif mod.type == "DATA_TRANSFER":
                        nrmtransfer = mod
                        mod.object = obj.parent
                        mod.name = "NormalTransfer"

                if not displace:
                    displace = add_displace(obj)

                while obj.modifiers[0] != displace:
                    bpy.ops.object.modifier_move_up(modifier=displace.name)


                obj.data.use_auto_smooth = True


        return {'FINISHED'}


class UpdateDecalBackup(bpy.types.Operator):
    bl_idname = "machin3.update_decal_backup"
    bl_label = "MACHIN3: Update Decal Backup"
    bl_description = "Update Decal Backup (Matrix)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        return active and (active.DM.isbackup or active.DM.decalbackup)

    def invoke(self, context, event):
        if event.alt:
            backup = context.active_object
            target = backup.parent

            backup.DM.backupmx = flatten_matrix(target.matrix_world.inverted_safe() @ backup.matrix_world)

            context.scene.collection.objects.unlink(backup)

        else:
            backup = context.active_object.DM.decalbackup
            context.scene.collection.objects.link(backup)

            bpy.ops.object.select_all(action='DESELECT')

            backup.select_set(True)
            context.view_layer.objects.active = backup


        return {'FINISHED'}
