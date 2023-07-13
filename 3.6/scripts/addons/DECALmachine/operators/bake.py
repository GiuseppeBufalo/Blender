import bpy
import os
from datetime import datetime
from .. utils.registration import get_prefs, get_templates_path
from .. utils.append import append_scene
from .. utils.ui import popup_message, init_prefs
from .. utils.system import open_folder
from .. utils.pil import create_decals_mask, apply_decals_mask, create_empty_map, combine, split_ao_curv_height_channels, combine_emission_maps
from .. utils.bake import create_bakebasepath, prepare_active, prepare_decals, bake_target_mask, bake_decals_margin_mask, bake, preview, apply_substance_naming, resample
from .. utils.decal import remove_decal_orphans
from .. utils.object import update_local_view




class Bake(bpy.types.Operator):
    bl_idname = "machin3.bake_decals"
    bl_label = "MACHIN3: Bake Decals"
    bl_description = "Bake Decal Textures to Parent Object's UV space"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if get_prefs().pil and context.mode == 'OBJECT':
            dm = context.scene.DM
            if any([dm.export_bake_color, dm.export_bake_normal, dm.export_bake_emission, dm.export_bake_aocurvheight, dm.export_bake_masks]):
                return [obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.DM.isdecal and obj.data.uv_layers and not obj.DM.prebakepreviewmats and not obj.name == 'Combined']

    def execute(self, context):
        targets = [obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.DM.isdecal and obj.data.uv_layers and [child for child in obj.children if child.DM.isdecal] and not obj.DM.prebakepreviewmats and not obj.name == 'Combined']

        if targets:
            start = datetime.now()

            templatepath = get_templates_path()
            assetspath = get_prefs().assetspath
            exportpath = os.path.join(assetspath, "Export")
            bakespath = os.path.join(exportpath, "bakes")
            blendname = os.path.basename(bpy.data.filepath)[:-6] if bpy.data.filepath else ''
            bakebasepath = create_bakebasepath(bakespath, blendname)

            device = context.scene.cycles.device

            scene = context.scene
            dm = scene.DM

            width = dm.export_bake_x
            height = dm.export_bake_y
            supersample = int(dm.export_bake_supersample)
            samples = dm.export_bake_samples

            init_prefs(context)

            print("\nInfo: Starting to bake decals to %s, at %s with %s samples and %dx Anti Aliasing using the %s --------------------" % (", ".join([target.name for target in targets]), "x".join([str(width), str(height)]), samples, supersample, device))

            if supersample:
                width *= supersample
                height *= supersample

            margin = dm.export_bake_margin
            ray_distance = dm.export_bake_distance
            triangulate = dm.export_bake_triangulate

            combine_bakes = dm.export_bake_combine_bakes and len(targets) > 1
            preview_bakes = dm.export_bake_preview
            open_bake_folder = dm.export_bake_open_folder
            substance_naming = dm.export_bake_substance_naming

            bake_color = dm.export_bake_color
            bake_normal = dm.export_bake_normal
            bake_emission = dm.export_bake_emission
            bake_aocurvheight = dm.export_bake_aocurvheight
            bake_masks = dm.export_bake_masks


            remove_decal_orphans(debug=True)

            view_layer = context.view_layer

            bakescene = append_scene(templatepath, "Bake")

            context.window.scene = bakescene

            bakescene.cycles.device = device

            bakescene.cycles.samples = samples


            baketypes = []

            if bake_color:
                baketypes.append('COLOR')

            if bake_normal:
                baketypes.append('NORMAL')

            if bake_emission:
                baketypes.extend(['EMISSION_NORMAL', 'EMISSION_COLOR'])  # emission is baked two times

            if bake_aocurvheight:
                baketypes.append('AO_CURV_HEIGHT')

            if bake_masks:
                baketypes.append('SUBSET')

            bakes = {}

            for target in targets:
                bakes[target] = {}

            if baketypes:
                support_bakes = []

                for target in targets:
                    bpy.ops.object.select_all(action='DESELECT')

                    active, bakeimg, bakemat = prepare_active(context, bakescene, target, width, height, triangulate)

                    target_mask = bake_target_mask(bakescene, bakebasepath, target.name, 'mask', bakeimg, bakemat, margin=0, ray_distance=ray_distance)
                    if bake_masks:
                        bakes[target]['MASKS'] = [target_mask]
                    else:
                        support_bakes.append(target_mask)

                    if combine_bakes:
                        combine_mask = bake_target_mask(bakescene, bakebasepath, target.name, 'combine', bakeimg, bakemat, margin=margin, ray_distance=ray_distance)

                        bakes[target]['COMBINE'] = combine_mask
                        support_bakes.append(combine_mask)

                    normal_decals_mask = None
                    color_decals_mask = None

                    for baketype in baketypes:

                        decals = prepare_decals(context, view_layer, bakescene, target, baketype, debug=False)

                        if decals:
                            if baketype in ['NORMAL', 'AO_CURV_HEIGHT', 'SUBSET', 'EMISSION_NORMAL']:
                                if not normal_decals_mask:
                                    normal_margin_0_mask = bake_decals_margin_mask(bakescene, bakebasepath, target.name, 'normal', bakeimg, decals, margin=0, ray_distance=ray_distance)
                                    normal_margin_3_mask = bake_decals_margin_mask(bakescene, bakebasepath, target.name, 'normal', bakeimg, decals, margin=margin, ray_distance=ray_distance)
                                    support_bakes.extend([normal_margin_0_mask, normal_margin_3_mask])

                                    normal_decals_mask = create_decals_mask(bakebasepath, target.name, 'normal', target_mask, normal_margin_0_mask, normal_margin_3_mask)
                                    if bake_masks:
                                        bakes[target]['MASKS'].append(normal_decals_mask)
                                    else:
                                        support_bakes.append(normal_decals_mask)

                            if baketype in ['COLOR', 'EMISSION_COLOR']:
                                if not color_decals_mask:
                                    color_margin_0_mask = bake_decals_margin_mask(bakescene, bakebasepath, target.name, 'color', bakeimg, decals, margin=0, ray_distance=ray_distance)
                                    color_margin_3_mask = bake_decals_margin_mask(bakescene, bakebasepath, target.name, 'color', bakeimg, decals, margin=margin, ray_distance=ray_distance)
                                    support_bakes.extend([color_margin_0_mask, color_margin_3_mask])

                                    color_decals_mask = create_decals_mask(bakebasepath, target.name, 'color', target_mask, color_margin_0_mask, color_margin_3_mask)
                                    if bake_masks:
                                        bakes[target]['MASKS'].append(color_decals_mask)
                                    else:
                                        support_bakes.append(color_decals_mask)

                            bake_map = bake(bakescene, bakebasepath, decals, target.name, baketype, bakeimg, margin=margin, ray_distance=ray_distance)

                            bakes[target][baketype] = bake_map

                            if baketype in ['NORMAL', 'AO_CURV_HEIGHT', 'SUBSET', 'EMISSION_NORMAL']:
                                apply_decals_mask(normal_decals_mask, bake_map, baketype, target.name)

                                if baketype in ['AO_CURV_HEIGHT', 'EMISSION_NORMAL']:
                                    support_bakes.append(bake_map)

                            elif baketype in ['COLOR', 'EMISSION_COLOR']:
                                apply_decals_mask(color_decals_mask, bake_map, baketype, target.name)

                                if baketype == 'EMISSION_COLOR':
                                    support_bakes.append(bake_map)

                            self.unlink_decals(bakescene, decals)

                        else:

                            if combine_bakes or baketype in ['AO_CURV_HEIGHT', 'EMISSION_NORMAL', 'EMISSION_COLOR']:
                                empty_map = create_empty_map(bakebasepath, baketype, target.name, (width, height))
                                bakes[target][baketype] = empty_map

                                if baketype in ['AO_CURV_HEIGHT', 'EMISSION_NORMAL', 'EMISSION_COLOR']:
                                    support_bakes.append(empty_map)


                    self.remove_active(active, bakemat, bakeimg)

                bpy.data.worlds.remove(bakescene.world, do_unlink=True)
                bpy.data.scenes.remove(bakescene, do_unlink=True)

                context.window.scene = scene

                end = datetime.now()
                print("Info: Baking Decals complete, duration: %s ----------------------------------------\n" % (str(end - start)))

                if combine_bakes:
                    combine(bakebasepath, bakes, support_bakes)

                if supersample:
                    resample(bakes, 1 / supersample)

                if bake_aocurvheight:
                    split_ao_curv_height_channels(bakebasepath, bakes)

                if bake_emission:
                    combine_emission_maps(bakebasepath, bakes)

                for path in support_bakes:
                    print("Info: Removing support bake: %s" % (path))
                    os.unlink(path)

                if substance_naming:
                    apply_substance_naming(bakes)

                if preview_bakes:
                    preview(templatepath, bakes, combine_bakes)

                if open_bake_folder:
                    open_folder(bakebasepath)

        else:
            popup_message('Select at least one object, that has decal children!', title='Illegal Selection')

        return {'FINISHED'}

    def remove_active(self, active, mat, img):
        bpy.data.meshes.remove(active.data, do_unlink=True)
        bpy.data.materials.remove(mat, do_unlink=True)
        bpy.data.images.remove(img, do_unlink=True)

    def unlink_decals(self, bakescene, decals):
        for decal, decalmats in decals:
            bakescene.collection.objects.unlink(decal)

            for mat, pg in decalmats:
                if pg:
                    pg.mute = False


class RestorePreBakePreviewMaterials(bpy.types.Operator):
    bl_idname = "machin3.restore_pre_bakepreview_materials"
    bl_label = "MACHIN3: Restore Pre-BakePreview Materials"
    bl_description = "Restore Pre-BakePreview Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and [obj for obj in context.selected_objects if not obj.DM.isdecal and obj.DM.prebakepreviewmats]

    def execute(self, context):
        remove_images = set()

        for target in [obj for obj in context.selected_objects if not obj.DM.isdecal and obj.DM.prebakepreviewmats]:

            if target.DM.prebakepreviewmats[0].name == 'NO_SLOTS':
                target.data.materials.clear()

            else:
                for col, slot in zip(target.DM.prebakepreviewmats, target.material_slots):
                    preview_material = slot.material
                    slot.material = col.material

                    for node in preview_material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE':
                            if node.image:
                                remove_images.add(node.image)

                    bpy.data.materials.remove(preview_material, do_unlink=True)

            target.DM.prebakepreviewmats.clear()

            decals = [obj for obj in target.children if obj.DM.isdecal and not obj.DM.isbackup]

            for decal in decals:
                decal.hide_set(False)

            update_local_view(context.space_data, [(decal, True) for decal in decals])

        for img in remove_images:
            bpy.data.images.remove(img, do_unlink=True)

        return {'FINISHED'}
