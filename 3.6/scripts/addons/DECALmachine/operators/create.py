import bpy
from bpy.props import BoolProperty
import os
import re
from uuid import uuid4
import shutil
from mathutils import Vector
from .. utils.registration import get_templates_path, get_prefs, reload_infotextures, reload_infofonts, reload_instant_decals, set_new_decal_index, reload_decal_libraries, reload_trim_libraries, get_version_from_blender, get_version_filename_from_blender, get_version_as_float, is_library_corrupted
from .. utils.append import append_scene, append_material, append_object
from .. utils.math import get_bbox_dimensions
from .. utils.system import makedir, get_new_directory_index, abspath
from .. utils.material import get_decal_textures, get_decalgroup_from_decalmat, get_parallaxgroup_from_decalmat, set_decal_textures, get_heightgroup_from_parallaxgroup, get_decal_texture_nodes, append_and_setup_trimsheet_material
from .. utils.material import get_decalmat, deduplicate_decal_material, remove_decalmat, set_decal_texture_paths, get_decalgroup_as_dict, set_decalgroup_from_dict, get_trimsheetgroup_from_trimsheetmat, get_trimsheetgroup_as_dict, set_trimsheetgroup_from_dict, get_parallaxgroup_from_any_mat, remove_trimsheetmat
from .. utils.material import get_pbrnode_from_mat, set_subset_component_from_decalgroup
from .. utils.collection import get_decaltype_collection
from .. utils.scene import setup_surface_snapping
from .. utils.decal import align_decal, set_defaults, apply_decal, set_decalobj_name, set_props_and_node_names_of_decal, remove_decal_from_blend
from .. utils.trim import get_sheetdata_from_uuid
from .. utils.create import create_decal_blend, create_info_decal_textures, create_decal_textures, create_decal_geometry, get_decal_source_objects, save_blend, save_uuid, render_thumbnail
from .. utils.pil import pack_textures, text2img, split_alpha, create_new_masks_texture, create_dummy_texture
from .. utils.ui import init_prefs, popup_message
from .. utils.object import update_local_view
from .. utils.library import get_legacy_libs, reset_legacy_libs_check
from .. import bl_info


class Create(bpy.types.Operator):
    bl_idname = "machin3.create_decal"
    bl_label = "MACHIN3: Create Decal"
    bl_description = "Create your own Decals - from Geometry, Images or Text"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if get_prefs().pil and context.mode == 'OBJECT':
            active = context.active_object
            sel = context.selected_objects

            if context.scene.DM.create_decaltype == "INFO":
                if context.scene.DM.create_infotype == "IMAGE":
                    return bpy.types.WindowManager.infotextures.keywords['items']

                elif context.scene.DM.create_infotype == "FONT":
                    return bpy.types.WindowManager.infofonts.keywords['items'] and context.scene.DM.create_infotext

                elif context.scene.DM.create_infotype == "GEOMETRY":
                    return active in sel and not active.DM.isdecal

            else:
                return active in sel and not active.DM.isdecal

    def execute(self, context):
        scene = context.scene
        dm = scene.DM
        wm = context.window_manager

        templatepath = get_templates_path()
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        instantpath = os.path.join(createpath, "decalinstant")
        infopath = os.path.join(createpath, 'infotextures')
        fontspath = os.path.join(createpath, 'infofonts')

        active = context.active_object
        force_uuid = dm.create_force_uuid

        if not (dm.create_decaltype == 'INFO' and dm.create_infotype in ['IMAGE', 'FONT']) and active and force_uuid and active.DM.forced_uuid:
            uuid = active.DM.forced_uuid

            remove_decal_from_blend(uuid)

        else:
            uuid = str(uuid4())

            if active and force_uuid:
                active.DM.forced_uuid = uuid

        index = get_new_directory_index(instantpath)
        decalpath = makedir(os.path.join(instantpath, "%s_%s" % (index, uuid)))

        dg = context.evaluated_depsgraph_get()

        init_prefs(context)

        device = scene.cycles.device

        if dm.create_decaltype in ['SIMPLESUBSET', 'PANEL'] or (dm.create_decaltype == 'INFO' and dm.create_infotype == 'GEOMETRY'):
            decaltype = dm.create_decaltype.title() if dm.create_decaltype in ['INFO', 'PANEL'] else 'Simple' if len(context.selected_objects) == 1 else 'Subset'
            print(f"\nINFO: Starting {decaltype} Decal Creation {'from Geometry ' if dm.create_decaltype == 'INFO' else ''}using {device}")

        else:
            print(f"\nINFO: Starting Info Decal Creation from {dm.create_infotype.title()}")

        if 'LIBRARY_DECAL' in bpy.data.objects:
            print("WARNING: Removing leftover LIBRARY_DECAL")
            bpy.data.meshes.remove(bpy.data.objects['LIBRARY_DECAL'].data, do_unlink=True)

        if dm.create_decaltype == 'INFO':
            location = (0, 0, 0)
            width = 0

            if dm.create_infotype == "IMAGE":
                texturespath = makedir(os.path.join(decalpath, 'textures'))
                texturename = wm.infotextures

                basename, ext = os.path.splitext(texturename)
                decalnamefromfile = basename.strip().replace(' ', '_')

                crop = dm.create_infoimg_crop
                padding = dm.create_infoimg_padding

                srcpath = os.path.join(infopath, texturename)
                destpath = os.path.join(texturespath, f"color{ext}")
                shutil.copy(srcpath, destpath)

                packed, decaltype = pack_textures(dm, decalpath, [destpath], crop=crop, padding=padding)

                decal, decalmat, size = create_decal_blend(context, templatepath, decalpath, packed, decaltype, uuid=uuid, decalnamefromfile=decalnamefromfile)

                render_thumbnail(context, decalpath, decal, decalmat, size=size)

            elif dm.create_infotype == "FONT":
                texturespath = makedir(os.path.join(decalpath, 'textures'))
                fontname = wm.infofonts

                font = os.path.join(fontspath, fontname)
                text = dm.create_infotext.replace("\\n", "\n")

                textcolor = dm.create_infotext_color
                bgcolor = dm.create_infotext_bgcolor

                size = dm.create_infotext_size
                padding = dm.create_infotext_padding
                offset = dm.create_infotext_offset

                align = dm.create_infotext_align

                texturename = "%d_%s_%s" % (size, fontname[:-4], text.replace("\n", "") + ".png")
                text2imgpath = os.path.join(texturespath, texturename)

                text2img(text2imgpath, text, font, size, padding=padding, offset=offset, align=align, color=textcolor, bgcolor=bgcolor)

                packed, decaltype = pack_textures(dm, decalpath, [text2imgpath])

                decal, decalmat, size = create_decal_blend(context, templatepath, decalpath, packed, decaltype, uuid=uuid)

                render_thumbnail(context, decalpath, decal, decalmat, size=size)

            elif dm.create_infotype == "GEOMETRY":
                bakepath = makedir(os.path.join(decalpath, "bakes"))
                padding = dm.create_infotext_padding
                emissive = dm.create_bake_emissive

                sel = [obj for obj in context.selected_objects]

                bakescene = append_scene(templatepath, "Bake")

                context.window.scene = bakescene

                bakescene.cycles.device = device

                source_objs, bbox_coords, _ = get_decal_source_objects(context, dg, bakescene, sel, clear_mats=False)

                width, depth, height = get_bbox_dimensions(bbox_coords)

                decal, location = create_decal_geometry(context, bakescene, bbox_coords, min((d for d in [width, depth, height] if d != 0)))

                if force_uuid:
                    decal.DM.is_forced_uuid = True

                textures, size = create_info_decal_textures(context, dm, templatepath, bakepath, bakescene, decal, source_objs, bbox_coords, width, depth, padding)

                packed, decaltype = pack_textures(dm, decalpath, textures, size)

                decal, decalmat, size = create_decal_blend(context, templatepath, decalpath, packed, decaltype, decal, size, uuid=uuid, set_emission=emissive)

                render_thumbnail(context, decalpath, decal, decalmat, size=size)

        else:
            bakepath = makedir(os.path.join(decalpath, "bakes"))
            emissive = dm.create_bake_emissive

            sel = [obj for obj in context.selected_objects if obj.type == "MESH"]
            active = context.active_object

            issubset = len(sel) > 1
            store_subset = dm.create_bake_store_subset
            subsetmatname = False

            if issubset and store_subset:
                mat = bpy.data.materials.get(wm.matchmaterial)
                subsetmatname = wm.matchmaterial if wm.matchmaterial in ['None'] else mat.name if (mat and get_pbrnode_from_mat(mat)) else False

            bakescene = append_scene(templatepath, "Bake")

            context.window.scene = bakescene

            bakescene.cycles.device = device

            source_objs, bbox_coords, active = get_decal_source_objects(context, dg, bakescene, sel, active, clear_mats=False if emissive else True, debug=False)

            width, depth, height = get_bbox_dimensions(bbox_coords)

            decal, location = create_decal_geometry(context, bakescene, bbox_coords, height)

            if force_uuid:
                decal.DM.is_forced_uuid = True

            textures, size = create_decal_textures(context, dm, templatepath, bakepath, bakescene, decal, active, source_objs, bbox_coords, width, depth)

            packed, decaltype = pack_textures(dm, decalpath, textures, size)

            decal, decalmat, size = create_decal_blend(context, templatepath, decalpath, packed, decaltype, decal, size, uuid=uuid, set_emission=emissive, set_subset=subsetmatname)

            render_thumbnail(context, decalpath, decal, decalmat, size=size)

        reload_instant_decals(default=os.path.basename(decalpath))

        context.window.scene = scene
        self.insert_decal(context, decalpath, decaltype, location, width)

        dm.quickinsertdecal = os.path.basename(decalpath)
        dm.quickinsertlibrary = "INSTANT"
        dm.quickinsertisinstant = True

        setup_surface_snapping(scene)

        return {'FINISHED'}

    def insert_decal(self, context, decalpath, decaltype, location, width):
        baked = False if decaltype == "INFO" and context.scene.DM.create_infotype in ['IMAGE', 'FONT'] else True

        decalobj = append_object(os.path.join(decalpath, "decal.blend"), "LIBRARY_DECAL")

        dtcol = get_decaltype_collection(context, decalobj.DM.decaltype)

        dtcol.objects.link(decalobj)

        if baked:
            decalobj.location = location
            factor = decalobj.dimensions[0] / width
            decalobj.scale /= factor

        else:
            dg = context.evaluated_depsgraph_get()
            align_decal(decalobj, context.scene, dg, force_cursor_align=True)

        bpy.ops.object.select_all(action='DESELECT')
        decalobj.select_set(True)
        context.view_layer.objects.active = decalobj

        mat = get_decalmat(decalobj)

        if mat:
            decalmat = deduplicate_decal_material(context, mat)
            decalobj.active_material = decalmat

        else:
            decalmat = None

        if decalmat:
            set_props_and_node_names_of_decal("INSTANT", os.path.basename(decalpath), decalobj=decalobj, decalmat=decalmat)

            set_defaults(decalobj=decalobj, decalmat=decalmat)

            if not baked:
                apply_decal(dg, decalobj, raycast=True)

            set_decalobj_name(decalobj)


class BatchCreate(bpy.types.Operator):
    bl_idname = "machin3.batch_create_decals"
    bl_label = "MACHIN3: Batch Create Decals"
    bl_description = "Batch create your own Info Decals from multiple Images"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if get_prefs().pil and context.mode == 'OBJECT':
            if context.scene.DM.create_decaltype == "INFO":
                if context.scene.DM.create_infotype == "IMAGE":
                    return len(bpy.types.WindowManager.infotextures.keywords['items']) > 1

    def execute(self, context):
        templatepath = get_templates_path()
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        instantpath = os.path.join(createpath, "decalinstant")
        infopath = os.path.join(createpath, 'infotextures')

        index = get_new_directory_index(instantpath)

        dm = context.scene.DM

        crop = dm.create_infoimg_crop
        padding = dm.create_infoimg_padding

        init_prefs(context)

        infotextures = [f for f in sorted(os.listdir(infopath)) if f.endswith('.jpg') or f.endswith('.png')]

        batch = []

        for idx, texturename in enumerate(infotextures):
            print("\nCreating decal from image %s" % (texturename))

            uuid = str(uuid4())

            decalpath = makedir(os.path.join(instantpath, "%s_%s" % (str(int(index) + idx).zfill(3), uuid)))
            texturespath = makedir(os.path.join(decalpath, 'textures'))

            basename, ext = os.path.splitext(texturename)
            decalnamefromfile = basename.strip().replace(' ', '_')

            srcpath = os.path.join(infopath, texturename)
            destpath = os.path.join(texturespath, "color%s" % (ext))
            shutil.copy(srcpath, destpath)

            packed, decaltype = pack_textures(dm, decalpath, [destpath], crop=crop, padding=padding)

            decal, decalmat, size = create_decal_blend(context, templatepath, decalpath, packed, decaltype, uuid=uuid, decalnamefromfile=decalnamefromfile)

            render_thumbnail(context, decalpath, decal, decalmat, size=size)

            batch.append((decalpath, size))

        reload_instant_decals(default=os.path.basename(decalpath))

        self.batch_insert_decals(context, batch, decaltype)

        dm.quickinsertdecal = os.path.basename(decalpath)
        dm.quickinsertlibrary = "INSTANT"
        dm.quickinsertisinstant = True

        setup_surface_snapping(context.scene)

        return {'FINISHED'}

    def batch_insert_decals(self, context, batch, decaltype):
        bpy.ops.object.select_all(action='DESELECT')

        xoffset = 0
        prev_size = 0

        dg = context.evaluated_depsgraph_get()

        for idx, (decalpath, size) in enumerate(batch):
            if idx > 0:
                xoffset += (prev_size[0] / 2 + size[0] / 2 + 100) / 1000

            decalobj = append_object(os.path.join(decalpath, "decal.blend"), "LIBRARY_DECAL")

            dtcol = get_decaltype_collection(context, decalobj.DM.decaltype)

            dtcol.objects.link(decalobj)

            dg.update()

            if xoffset:
                decalobj.matrix_world.translation = Vector((xoffset, 0, 0))

            prev_size = size

            decalobj.select_set(True)
            context.view_layer.objects.active = decalobj

            mat = get_decalmat(decalobj)

            if mat:
                decalmat = deduplicate_decal_material(context, mat)
                decalobj.active_material = decalmat

            else:
                decalmat = None

            if decalmat:
                set_props_and_node_names_of_decal("INSTANT", os.path.basename(decalpath), decalobj=decalobj, decalmat=decalmat)

                set_defaults(decalobj=decalobj, decalmat=decalmat)

                set_decalobj_name(decalobj)

                update_local_view(context.space_data, [(decalobj, True)])


class AddDecalToLibrary(bpy.types.Operator):
    bl_idname = "machin3.add_decal_to_library"
    bl_label = "MACHIN3: Add Decal to Library"
    bl_description = "Add Selected Decal(s) to Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(obj for obj in context.selected_objects if obj.DM.isdecal and not obj.DM.isprojected and not obj.DM.issliced) and context.scene.userdecallibs

    def draw(self, context):
        layout = self.layout
        column = layout.column()

    def execute(self, context):
        set_new_decal_index(self, context)

        dm = context.scene.DM

        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        index = context.window_manager.newdecalidx
        library = context.scene.userdecallibs
        name = dm.addlibrary_decalname.strip().replace(' ', '_')

        librarypath = os.path.join(assetspath, 'Decals', library)
        existingpaths = [os.path.join(librarypath, f) for f in os.listdir(librarypath) if os.path.isdir(os.path.join(librarypath, f))]

        use_filename = dm.addlibrary_use_filename
        skip_index = dm.addlibrary_skip_index
        store_subset = dm.create_bake_store_subset

        init_prefs(context)

        decals = sorted([obj for obj in context.selected_objects if obj.DM.isdecal and not obj.DM.isprojected and not obj.DM.issliced], key=lambda x: x.name)

        decalpaths = []
        skipped = []

        for idx, source_decal in enumerate(decals):
            basename = source_decal.active_material.DM.decalnamefromfile if (source_decal.active_material.DM.decalnamefromfile and use_filename) else name
            decalidx = None if skip_index else str(int(index) + idx).zfill(3)
            decalname = f"{decalidx + '_' if decalidx else ''}{basename}" if basename else decalidx

            if not decalname:
                decalname = str(int(index) + idx).zfill(3)

            decalpath = os.path.join(assetspath, 'Decals', library, decalname)

            if decalpath in existingpaths:
                print(f"WARNING: Skipped adding decal '{source_decal.name}' using the name '{decalname}' to library '{library}', because a folder of that name exists already: {decalpath}")
                skipped.append((source_decal, decalname, decalpath, 'Existing Folder'))
                continue

            elif decalpath in decalpaths:
                print(f"WARNING: Skipped adding decal '{source_decal.name}' using the name '{decalname}' to library '{library}', because a decal of that name was added already")
                skipped.append((source_decal, decalname, decalpath, 'Duplicate Name'))
                continue

            print(f"\nINFO: Adding decal '{decalname}' to library '{library}' at path: {decalpath}")

            decalpaths.append(decalpath)
            makedir(decalpath)

            decal = source_decal.copy()
            decal.data = source_decal.data.copy()

            oldmat = source_decal.active_material

            decalmat = append_material(templatepath, f"TEMPLATE_{oldmat.DM.decaltype}", relative=False)
            decal.active_material = decalmat

            if oldmat.DM.decaltype == 'INFO':
                olddg = get_decalgroup_from_decalmat(oldmat)
                dg = get_decalgroup_from_decalmat(decalmat)

                if olddg and dg:
                    for oldi, i in zip(olddg.inputs, dg.inputs):
                        i.default_value = oldi.default_value

            else:
                oldpg = get_parallaxgroup_from_decalmat(oldmat)
                pg = get_parallaxgroup_from_decalmat(decalmat)

                if oldpg and pg:
                    pg.inputs[0].default_value = oldpg.inputs[0].default_value

                olddg = get_decalgroup_from_decalmat(oldmat)
                dg = get_decalgroup_from_decalmat(decalmat)

                if olddg and dg:
                    oldemission = olddg.inputs['Emission Multiplier'].default_value
                    dg.inputs['Emission Multiplier'].default_value = oldemission

                if store_subset and decalmat.DM.decaltype == 'SUBSET':
                    set_subset_component_from_decalgroup(decalmat, olddg)

            if source_decal.DM.is_forced_uuid:
                uuid = source_decal.DM.uuid

            else:
                uuid = str(uuid4())

            creator = oldmat.DM.creator
            version = oldmat.DM.version

            set_props_and_node_names_of_decal("LIBRARY", "DECAL", decalobj=decal, uuid=uuid, version=version, creator=creator)

            decal.name = "LIBRARY_DECAL"
            decal.data.name = decal.name

            oldtextures = get_decal_textures(oldmat)
            textures = get_decal_textures(decalmat)

            for textype, img in oldtextures.items():
                srcpath = abspath(img.filepath)
                destpath = os.path.join(decalpath, os.path.basename(srcpath))

                shutil.copy(srcpath, destpath)

                textures[textype].filepath = destpath

            bpy.ops.scene.new(type='NEW')
            decalscene = context.scene
            decalscene.name = "Decal Asset"

            decalscene.collection.objects.link(decal)

            save_uuid(decalpath, uuid)

            save_blend(decal, decalpath, decalscene)

            render_thumbnail(context, decalpath, decal, decalmat, removeall=True)

            source_decal.select_set(False)

        if decalpaths:
            reload_decal_libraries(library=library, default=os.path.basename(decalpath))

            set_new_decal_index(self, context)

        if skipped:
            title = f"{len(skipped)}/{len(decals)} decals could not be added to the '{library}' library!"
            msg = []

            for idx, (decal, name, path, reason) in enumerate(skipped):
                explanation = 'folder of that name exists already' if reason == 'Existing Folder' else 'decal of that name was added already'
                msg.append(f"{idx + 1}.{reason}: Skipped decal '{decal.name}' using the name '{name}', because a {explanation}")

            if skip_index:
                msg.append('')
                msg.append(f"Disable the option to skip {'indices' if len(decals) > 1 else 'the index'} to prevent decal path conflicts like these.")

            popup_message(msg, title=title)

        if decalpaths:
            return {'FINISHED'}
        return {'CANCELLED'}


class Update18DecalLibrary(bpy.types.Operator):
    bl_idname = "machin3.update_18_decal_library"
    bl_label = "MACHIN3: Update 1.8 Decal Library"
    bl_description = "Update 1.8 - 1.9.4 Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT' and get_prefs().pil:
            dm = context.scene.DM
            if context.scene.userdecallibs or dm.updatelibraryinplace:
                return dm.update18librarypath and dm.update18librarypath != "CHOOSE A 1.8 - 1.9.4 DECAL LIBRARY!" and os.path.exists(dm.update18librarypath)

    def execute(self, context):
        set_new_decal_index(self, context)

        scene = context.scene
        dm = scene.DM

        inplace = dm.updatelibraryinplace
        keepthumbnails = dm.update_keep_old_thumbnails

        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        sourcepath = dm.update18librarypath

        if os.path.exists(os.path.join(sourcepath, get_version_filename_from_blender())):
            dm.avoid_update = True
            dm.update18librarypath = ''

        else:

            if is_library_corrupted(sourcepath):
                popup_message(message=["The library appears to be corrupted, it contains non-Decal folders!", "Remove them and try again!"], title="Corrupted Library!")
                return {'CANCELLED'}

            librarypath = os.path.join(assetspath, 'Decals', scene.userdecallibs)
            inplacepath = makedir(os.path.join(assetspath, 'Decals', '__IN_PLACE__')) if inplace else ''
            startidx = '001' if inplace else context.window_manager.newdecalidx

            legacydecals, metafiles = self.get_18_decals(sourcepath)

            if legacydecals:

                for metafile in metafiles:
                    shutil.copy(metafile, os.path.join(inplacepath if inplace else librarypath, os.path.basename(metafile)))

                if inplace:
                    with open(os.path.join(inplacepath, get_version_filename_from_blender()), "w") as f:
                        f.write("")

                for idx, (name, decalpath, blendpath, iconpath, texturepaths) in enumerate(legacydecals):
                    index = str(int(startidx) + idx).zfill(3)

                    decalname = self.create_new_decal(context, templatepath, inplacepath if inplace else librarypath, index, name, decalpath, blendpath, iconpath, texturepaths, keepthumbnails)

                if inplace:
                    print("INFO: Replacing original decal library folder")
                    shutil.rmtree(sourcepath)
                    shutil.move(inplacepath, sourcepath)

                    dm.avoid_update = True
                    dm.update18librarypath = ''

                    reload_decal_libraries()

                else:
                    reload_decal_libraries(library=scene.userdecallibs, default=decalname)

        reset_legacy_libs_check()

        return {'FINISHED'}

    def create_new_decal(self, context, templatepath, librarypath, index, name, decalpath, blendpath, iconpath, texturepaths, keepthumbnails):
        decalscene = bpy.data.scenes.new(name="Decal Asset")
        context.window.scene = decalscene
        mcol = decalscene.collection

        decalobj = append_object(blendpath, 'LIBRARY_DECAL')
        decalmat = decalobj.active_material if decalobj.active_material.DM.isdecalmat else None
        version = get_version_from_blender()

        if decalobj and decalmat:
            mcol.objects.link(decalobj)

            decalname = "%s_%s" % (index, name) if name else index
            newdecalpath = makedir(os.path.join(librarypath, decalname))

            decaltype = decalmat.DM.decaltype

            newmat = append_material(templatepath, "TEMPLATE_%s" % decaltype, relative=False)
            decalobj.active_material = newmat

            newtexturepaths = self.update_decal_textures(newdecalpath, texturepaths, decaltype)

            decalobj.name = "LIBRARY_DECAL"
            decalobj.data.name = decalobj.name

            set_decal_texture_paths(newmat, newtexturepaths)

            newtextures = get_decal_textures(newmat)

            set_props_and_node_names_of_decal("LIBRARY", "DECAL", decalobj, newmat, list(newtextures.values()), decaltype, decalobj.DM.uuid, version, decalobj.DM.creator)

            if decaltype == 'INFO':
                nodes = get_decal_texture_nodes(newmat)

                color = nodes.get('COLOR')
                masks = nodes.get('MASKS')

                if color:
                    color.interpolation = 'Closest'

                if masks:
                    masks.interpolation = 'Closest'

            pg = get_parallaxgroup_from_decalmat(decalmat)

            if pg:
                newpg = get_parallaxgroup_from_decalmat(newmat)

                if newpg:
                    newpg.inputs[0].default_value = pg.inputs[0].default_value

            save_uuid(newdecalpath, decalobj.DM.uuid)

            save_blend(decalobj, newdecalpath, decalscene)

            if keepthumbnails:
                shutil.copy(iconpath, os.path.join(newdecalpath, "decal.png"))

                bpy.data.meshes.remove(decalobj.data, do_unlink=True)
                remove_decalmat(newmat, remove_textures=True)

            else:
                render_thumbnail(context, newdecalpath, decalobj, newmat, removeall=True)

            remove_decalmat(decalmat, remove_textures=True, legacy=True)

            print("INFO: Updated decal %s to %s" % (decalname, newdecalpath))

            return decalname

    def update_decal_textures(self, decalpath, texturepaths, decaltype):
        nrm_alpha_path = texturepaths.get('NRM_ALPHA')
        color_alpha_path = texturepaths.get('COLOR_ALPHA')
        ao_curv_height_path = texturepaths.get('AO_CURV_HEIGHT')
        masks_path = texturepaths.get('MASKS')

        newtextures = {}

        if nrm_alpha_path:
            alpha, path = split_alpha(decalpath, abspath(nrm_alpha_path), 'NRM_ALPHA')
            newtextures['NORMAL'] = path

        elif color_alpha_path:
            alpha, path = split_alpha(decalpath, abspath(color_alpha_path), 'COLOR_ALPHA')
            newtextures['COLOR'] = path

        newtextures['MASKS'] = create_new_masks_texture(decalpath, alpha, maskspath=abspath(masks_path) if masks_path else None, decaltype=decaltype)

        newtextures['EMISSION'] = create_dummy_texture(decalpath, 'emission.png')

        if ao_curv_height_path:
            path = os.path.join(decalpath, 'ao_curv_height.png')
            shutil.copy(abspath(ao_curv_height_path), path)
            newtextures['AO_CURV_HEIGHT'] = path

        return newtextures

    def get_18_decals(self, librarypath):
        legacydecals = []
        metafiles = []

        for f in sorted(os.listdir(librarypath)):
            decalpath = os.path.join(librarypath, f)

            if os.path.isdir(decalpath):

                decalnameRegex = re.compile(r'[\d]{3}_?(.*)')
                mo = decalnameRegex.match(f)

                decalname = mo.group(1) if mo else f

                files = [name for name in os.listdir(decalpath)]

                blendpath = os.path.join(decalpath, 'decal.blend') if 'decal.blend' in files else None
                iconpath = os.path.join(decalpath, 'decal.png') if 'decal.png' in files else None

                texturepaths = {}

                if 'ao_curv_height.png' in files:
                    texturepaths['AO_CURV_HEIGHT'] = os.path.join(decalpath, 'ao_curv_height.png')

                if 'nrm_alpha.png' in files:
                    texturepaths['NRM_ALPHA'] = os.path.join(decalpath, 'nrm_alpha.png')

                if 'masks.png' in files:
                    texturepaths['MASKS'] = os.path.join(decalpath, 'masks.png')

                if 'color_alpha.png' in files:
                    texturepaths['COLOR_ALPHA'] = os.path.join(decalpath, 'color_alpha.png')

                legacydecals.append((decalname, decalpath, blendpath, iconpath, texturepaths))

                print("INFO: Found decal %s: %s" % (decalname, decalpath))


            elif f.startswith('.') and f != '.is280':
                metafiles.append(os.path.join(librarypath, f))

        return legacydecals, metafiles


class Update20DecalLibrary(bpy.types.Operator):
    bl_idname = "machin3.update_20_decal_library"
    bl_label = "MACHIN3: Update 2.0 Decal Library"
    bl_description = "Update 2.0 Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT' and get_prefs().pil:
            dm = context.scene.DM
            if context.scene.userdecallibs or dm.updatelibraryinplace or dm.updatelibraryistrimsheet:
                if dm.updatelibraryistrimsheet:
                    sheetname = os.path.basename(context.scene.DM.update20librarypath)
                    sheetlib = get_prefs().decallibsCOL.get(sheetname)
                    if sheetlib and not dm.updatelibraryinplace:
                        return False
                return dm.update20librarypath and dm.update20librarypath != "CHOOSE A 2.0 - 2.0.1 DECAL LIBRARY!" and os.path.exists(dm.update20librarypath)

    def execute(self, context):
        set_new_decal_index(self, context)

        scene = context.scene
        dm = scene.DM

        inplace = dm.updatelibraryinplace
        istrimsheet = dm.updatelibraryistrimsheet
        keepthumbnails = dm.update_keep_old_thumbnails

        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        sourcepath = dm.update20librarypath

        if os.path.exists(os.path.join(sourcepath, get_version_filename_from_blender())):
            dm.avoid_update = True
            dm.update20librarypath = ''

        else:

            if is_library_corrupted(sourcepath):
                popup_message(message=["The library appears to be corrupted, it contains non-Decal folders!", "Remove them and try again!"], title="Corrupted Library!")
                return {'CANCELLED'}

            legacydecals, metafiles = self.get_20_decals(sourcepath, istrimsheet=istrimsheet)

            if legacydecals:

                if istrimsheet:
                    librarypath = os.path.join(assetspath, 'Trims', os.path.basename(sourcepath))

                    if not inplace:
                        makedir(librarypath)

                    inplacepath = makedir(os.path.join(assetspath, 'Trims', '__IN_PLACE__')) if inplace else ''
                    startidx = '001'

                    with open(os.path.join(inplacepath if inplace else librarypath, get_version_filename_from_blender()), "w") as f:
                        f.write("")

                    self.copy_trimsheet_textures(sourcepath, inplacepath if inplace else librarypath)

                else:
                    librarypath = os.path.join(assetspath, 'Decals', scene.userdecallibs)
                    inplacepath = makedir(os.path.join(assetspath, 'Decals', '__IN_PLACE__')) if inplace else ''
                    startidx = '001' if inplace else context.window_manager.newdecalidx

                    if inplace:
                        with open(os.path.join(inplacepath, get_version_filename_from_blender()), "w") as f:
                            f.write("")

                for metafile in metafiles:
                    shutil.copy(metafile, os.path.join(inplacepath if inplace else librarypath, os.path.basename(metafile)))

                for idx, (name, decalpath, blendpath, iconpath, texturepaths) in enumerate(legacydecals):
                    index = str(int(startidx) + idx).zfill(3)

                    decalname = self.create_new_decal(context, templatepath, inplacepath if inplace else librarypath, index, name, decalpath, blendpath, iconpath, texturepaths, keepthumbnails)

                if inplace:
                    print("INFO: Replacing original %s library folder" % ('trim decal' if istrimsheet else 'decal'))
                    shutil.rmtree(sourcepath)
                    shutil.move(inplacepath, sourcepath)

                    dm.avoid_update = True
                    dm.update20librarypath = ''

                    reload_trim_libraries() if istrimsheet else reload_decal_libraries()

                else:
                    if istrimsheet:
                        reload_trim_libraries()

                        dm.avoid_update = True
                        dm.update20librarypath = ''

                    else:
                        reload_decal_libraries(library=scene.userdecallibs, default=decalname)

        reset_legacy_libs_check()

        return {'FINISHED'}

    def copy_trimsheet_textures(self, sourcepath, librarypath):
        sheettextures = [(f, os.path.join(sourcepath, f)) for f in os.listdir(sourcepath) if f.endswith('.png')]

        for f, path in sheettextures:
            newpath = os.path.join(librarypath, f)
            shutil.copy(path, newpath)

            print(f"INFO: Copying trim sheet texture from {path} to to {newpath}")

    def create_new_decal(self, context, templatepath, librarypath, index, name, decalpath, blendpath, iconpath, texturepaths, keepthumbnails):
        decalscene = bpy.data.scenes.new(name="Decal Asset")
        context.window.scene = decalscene
        mcol = decalscene.collection

        decalobj = append_object(blendpath, 'LIBRARY_DECAL')
        decalmat = decalobj.active_material if decalobj.active_material.DM.isdecalmat else None
        version = get_version_from_blender()

        if decalobj and decalmat:
            mcol.objects.link(decalobj)

            decalname = "%s_%s" % (index, name) if name else index
            newdecalpath = makedir(os.path.join(librarypath, decalname))

            decaltype = decalmat.DM.decaltype

            newmat = append_material(templatepath, "TEMPLATE_%s" % decaltype, relative=False)
            decalobj.active_material = newmat

            newtexturepaths = self.copy_decal_textures(newdecalpath, texturepaths, decaltype)

            if decalobj.DM.trimsheetuuid and os.path.exists(os.path.join(decalpath, '.ispanel')):
                shutil.copy(os.path.join(decalpath, '.ispanel'), newdecalpath)

            decalobj.name = "LIBRARY_DECAL"
            decalobj.data.name = decalobj.name

            set_decal_texture_paths(newmat, newtexturepaths)

            newtextures = get_decal_textures(newmat)

            if decalobj.DM.istrimdecal:
                newmat.DM.istrimdecalmat = True

                for img in newtextures.values():
                    img.DM.istrimdecaltex = True

            set_props_and_node_names_of_decal("LIBRARY", "DECAL", decalobj, newmat, list(newtextures.values()), decaltype, decalobj.DM.uuid, version, decalobj.DM.creator, decalobj.DM.trimsheetuuid)

            dg = get_decalgroup_from_decalmat(decalmat)
            newdg = get_decalgroup_from_decalmat(newmat)

            for i in dg.inputs:
                if i.name.endswith('Emission') or i.name == 'Emission Multiplier':
                    newdg.inputs[i.name].default_value = i.default_value

            if decaltype == 'INFO':
                nodes = get_decal_texture_nodes(newmat)

                color = nodes.get('COLOR')
                masks = nodes.get('MASKS')

                if color:
                    color.interpolation = 'Closest'

                if masks:
                    masks.interpolation = 'Closest'

            pg = get_parallaxgroup_from_decalmat(decalmat)

            if pg:
                newpg = get_parallaxgroup_from_decalmat(newmat)

                if newpg:
                    newpg.inputs[0].default_value = pg.inputs[0].default_value

            save_uuid(newdecalpath, decalobj.DM.uuid)

            save_blend(decalobj, newdecalpath, decalscene)

            if keepthumbnails:
                shutil.copy(iconpath, os.path.join(newdecalpath, "decal.png"))

                bpy.data.meshes.remove(decalobj.data, do_unlink=True)
                remove_decalmat(newmat, remove_textures=True)

            else:
                render_thumbnail(context, newdecalpath, decalobj, newmat, removeall=True)

            remove_decalmat(decalmat, remove_textures=True, legacy=False)

            print("INFO: Updated decal %s to %s" % (decalname, newdecalpath))

            return decalname

    def copy_decal_textures(self, decalpath, texturepaths, decaltype):
        newpaths = {}

        for decaltype, path in texturepaths.items():
            newpath = os.path.join(decalpath, '%s.png' % (decaltype.lower()))
            shutil.copy(path, newpath)
            newpaths[decaltype] = newpath

        return newpaths

    def get_20_decals(self, librarypath, istrimsheet=False):
        legacydecals = []
        metafiles = []

        for f in sorted(os.listdir(librarypath)):
            decalpath = os.path.join(librarypath, f)

            if os.path.isdir(decalpath):

                decalnameRegex = re.compile(r'[\d]{3}_?(.*)')
                mo = decalnameRegex.match(f)

                decalname = mo.group(1) if mo else f

                files = [name for name in os.listdir(decalpath)]

                blendpath = os.path.join(decalpath, 'decal.blend') if 'decal.blend' in files else None
                iconpath = os.path.join(decalpath, f, 'decal.png') if 'decal.png' in files else None

                texturepaths = {}

                if 'ao_curv_height.png' in files:
                    texturepaths['AO_CURV_HEIGHT'] = os.path.join(decalpath, 'ao_curv_height.png')

                if 'normal.png' in files:
                    texturepaths['NORMAL'] = os.path.join(decalpath, 'normal.png')

                if 'masks.png' in files:
                    texturepaths['MASKS'] = os.path.join(decalpath, 'masks.png')

                if 'emission.png' in files:
                    texturepaths['EMISSION'] = os.path.join(decalpath, 'emission.png')

                if 'color.png' in files:
                    texturepaths['COLOR'] = os.path.join(decalpath, 'color.png')

                legacydecals.append((decalname, decalpath, blendpath, iconpath, texturepaths))

                print("INFO: Found decal %s: %s" % (decalname, decalpath))

            elif (f.startswith('.') and f != '.is20') or (istrimsheet and f == 'data.json'):
                metafiles.append(os.path.join(librarypath, f))

        return legacydecals, metafiles


class Update21DecalLibrary(bpy.types.Operator):
    bl_idname = "machin3.update_21_decal_library"
    bl_label = "MACHIN3: Update 2.1 Decal Library"
    bl_description = "Update 2.1 Decal Library"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT' and get_prefs().pil and bpy.app.version >= (3, 0, 0):
            dm = context.scene.DM
            if context.scene.userdecallibs or dm.updatelibraryinplace or dm.updatelibraryistrimsheet:
                if dm.updatelibraryistrimsheet:
                    sheetname = os.path.basename(context.scene.DM.update21librarypath)
                    sheetlib = get_prefs().decallibsCOL.get(sheetname)
                    if sheetlib and not dm.updatelibraryinplace:
                        return False
                return dm.update21librarypath and dm.update21librarypath != "CHOOSE A 2.1 - 2.4.1 DECAL LIBRARY!" and os.path.exists(dm.update21librarypath)

    def execute(self, context):
        set_new_decal_index(self, context)

        scene = context.scene
        dm = scene.DM

        inplace = dm.updatelibraryinplace
        istrimsheet = dm.updatelibraryistrimsheet
        keepthumbnails = dm.update_keep_old_thumbnails

        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        sourcepath = dm.update21librarypath

        if os.path.exists(os.path.join(sourcepath, get_version_filename_from_blender())):
            dm.avoid_update = True
            dm.update21librarypath = ''

        else:

            if is_library_corrupted(sourcepath):
                popup_message(message=["The library appears to be corrupted, it contains non-Decal folders!", "Remove them and try again!"], title="Corrupted Library!")
                return {'CANCELLED'}

            legacydecals, metafiles = self.get_21_decals(sourcepath, istrimsheet=istrimsheet)

            if legacydecals:

                if istrimsheet:
                    librarypath = os.path.join(assetspath, 'Trims', os.path.basename(sourcepath))

                    if not inplace:
                        makedir(librarypath)

                    inplacepath = makedir(os.path.join(assetspath, 'Trims', '__IN_PLACE__')) if inplace else ''
                    startidx = '001'

                    with open(os.path.join(inplacepath if inplace else librarypath, get_version_filename_from_blender()), "w") as f:
                        f.write("")

                    self.copy_trimsheet_textures(sourcepath, inplacepath if inplace else librarypath)

                else:
                    librarypath = os.path.join(assetspath, 'Decals', scene.userdecallibs)
                    inplacepath = makedir(os.path.join(assetspath, 'Decals', '__IN_PLACE__')) if inplace else ''
                    startidx = '001' if inplace else context.window_manager.newdecalidx

                    if inplace:
                        with open(os.path.join(inplacepath, get_version_filename_from_blender()), "w") as f:
                            f.write("")

                for metafile in metafiles:
                    shutil.copy(metafile, os.path.join(inplacepath if inplace else librarypath, os.path.basename(metafile)))

                for idx, (name, decalpath, blendpath, iconpath, texturepaths) in enumerate(legacydecals):
                    index = str(int(startidx) + idx).zfill(3)

                    decalname = self.create_new_decal(context, templatepath, inplacepath if inplace else librarypath, index, name, decalpath, blendpath, iconpath, texturepaths, keepthumbnails)

                if inplace:
                    print("INFO: Replacing original %s library folder" % ('trim decal' if istrimsheet else 'decal'))
                    shutil.rmtree(sourcepath)
                    shutil.move(inplacepath, sourcepath)

                    dm.avoid_update = True
                    dm.update21librarypath = ''

                    reload_trim_libraries() if istrimsheet else reload_decal_libraries()

                else:
                    if istrimsheet:
                        reload_trim_libraries()

                        dm.avoid_update = True
                        dm.update21librarypath = ''

                    else:
                        reload_decal_libraries(library=scene.userdecallibs, default=decalname)

        reset_legacy_libs_check()

        return {'FINISHED'}

    def copy_trimsheet_textures(self, sourcepath, librarypath):
        sheettextures = [(f, os.path.join(sourcepath, f)) for f in os.listdir(sourcepath) if f.endswith('.png')]

        for f, path in sheettextures:
            newpath = os.path.join(librarypath, f)
            shutil.copy(path, newpath)

            print(f"INFO: Copying trim sheet texture from {path} to to {newpath}")

    def create_new_decal(self, context, templatepath, librarypath, index, name, decalpath, blendpath, iconpath, texturepaths, keepthumbnails):
        decalscene = bpy.data.scenes.new(name="Decal Asset")
        context.window.scene = decalscene
        mcol = decalscene.collection

        decalobj = append_object(blendpath, 'LIBRARY_DECAL')
        decalmat = decalobj.active_material if decalobj.active_material.DM.isdecalmat else None
        version = get_version_from_blender()

        if decalobj and decalmat:
            mcol.objects.link(decalobj)

            decalname = "%s_%s" % (index, name) if name else index
            newdecalpath = makedir(os.path.join(librarypath, decalname))

            decaltype = decalmat.DM.decaltype

            newmat = append_material(templatepath, "TEMPLATE_%s" % decaltype, relative=False)
            decalobj.active_material = newmat

            newtexturepaths = self.copy_decal_textures(newdecalpath, texturepaths, decaltype)

            if decalobj.DM.trimsheetuuid and os.path.exists(os.path.join(decalpath, '.ispanel')):
                shutil.copy(os.path.join(decalpath, '.ispanel'), newdecalpath)

            decalobj.name = "LIBRARY_DECAL"
            decalobj.data.name = decalobj.name

            set_decal_texture_paths(newmat, newtexturepaths)

            newtextures = get_decal_textures(newmat)

            if decalobj.DM.istrimdecal:
                newmat.DM.istrimdecalmat = True

                for img in newtextures.values():
                    img.DM.istrimdecaltex = True

            set_props_and_node_names_of_decal("LIBRARY", "DECAL", decalobj, newmat, list(newtextures.values()), decaltype, decalobj.DM.uuid, version, decalobj.DM.creator, decalobj.DM.trimsheetuuid)

            dg = get_decalgroup_from_decalmat(decalmat)
            newdg = get_decalgroup_from_decalmat(newmat)

            for i in dg.inputs:
                if i.name.endswith('Emission') or i.name == 'Emission Multiplier':
                    newdg.inputs[i.name].default_value = i.default_value

            if decaltype == 'INFO':
                nodes = get_decal_texture_nodes(newmat)

                color = nodes.get('COLOR')
                masks = nodes.get('MASKS')

                if color:
                    color.interpolation = 'Closest'

                if masks:
                    masks.interpolation = 'Closest'

            pg = get_parallaxgroup_from_decalmat(decalmat)

            if pg:
                newpg = get_parallaxgroup_from_decalmat(newmat)

                if newpg:
                    newpg.inputs[0].default_value = pg.inputs[0].default_value

            save_uuid(newdecalpath, decalobj.DM.uuid)

            save_blend(decalobj, newdecalpath, decalscene)

            if keepthumbnails:
                shutil.copy(iconpath, os.path.join(newdecalpath, "decal.png"))

                bpy.data.meshes.remove(decalobj.data, do_unlink=True)
                remove_decalmat(newmat, remove_textures=True)

            else:
                render_thumbnail(context, newdecalpath, decalobj, newmat, removeall=True)

            remove_decalmat(decalmat, remove_textures=True, legacy=False)

            print("INFO: Updated decal %s to %s" % (decalname, newdecalpath))

            return decalname

    def copy_decal_textures(self, decalpath, texturepaths, decaltype):
        newpaths = {}

        for decaltype, path in texturepaths.items():
            newpath = os.path.join(decalpath, '%s.png' % (decaltype.lower()))
            shutil.copy(path, newpath)
            newpaths[decaltype] = newpath

        return newpaths

    def get_21_decals(self, librarypath, istrimsheet=False):
        legacydecals = []
        metafiles = []

        for f in sorted(os.listdir(librarypath)):
            decalpath = os.path.join(librarypath, f)

            if os.path.isdir(decalpath):

                decalnameRegex = re.compile(r'[\d]{3}_?(.*)')
                mo = decalnameRegex.match(f)

                decalname = mo.group(1) if mo else f

                files = [name for name in os.listdir(decalpath)]

                blendpath = os.path.join(decalpath, 'decal.blend') if 'decal.blend' in files else None
                iconpath = os.path.join(decalpath, f, 'decal.png') if 'decal.png' in files else None

                texturepaths = {}

                if 'ao_curv_height.png' in files:
                    texturepaths['AO_CURV_HEIGHT'] = os.path.join(decalpath, 'ao_curv_height.png')

                if 'normal.png' in files:
                    texturepaths['NORMAL'] = os.path.join(decalpath, 'normal.png')

                if 'masks.png' in files:
                    texturepaths['MASKS'] = os.path.join(decalpath, 'masks.png')

                if 'emission.png' in files:
                    texturepaths['EMISSION'] = os.path.join(decalpath, 'emission.png')

                if 'color.png' in files:
                    texturepaths['COLOR'] = os.path.join(decalpath, 'color.png')

                legacydecals.append((decalname, decalpath, blendpath, iconpath, texturepaths))

                print("INFO: Found decal %s: %s" % (decalname, decalpath))

            elif (f.startswith('.') and f != '.is21') or (istrimsheet and f == 'data.json'):
                metafiles.append(os.path.join(librarypath, f))

        return legacydecals, metafiles


class BatchUpdate(bpy.types.Operator):
    bl_idname = "machin3.batch_update_decal_libraries"
    bl_label = "MACHIN3: Batch Update Legacy Decal and Trim Sheet libraries"
    bl_description = "Batch Update Legacy Decal and Trim Sheet libraries found in the Assets Path"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode =='OBJECT' and any([*get_legacy_libs()]):
            return get_prefs().pil

    def execute(self, context):
        dm = context.scene.DM

        decal_libs_18, decal_libs_20, decal_libs_21, trimsheet_libs_20, trimsheet_libs_21 = get_legacy_libs()



        if decal_libs_18:
            print("INFO: Updating 1.8 - 1.9.4 Legacy Decal Libraries")

            for lib in decal_libs_18:
                dm.avoid_update = True
                dm.update18librarypath = lib

                dm.avoid_update = True
                dm.updatelibraryinplace = True

                bpy.ops.machin3.update_18_decal_library()


        if decal_libs_20:
            print("INFO: Updating 2.0.x Legacy Decal Libraries")

            for lib in decal_libs_20:
                dm.avoid_update = True
                dm.update20librarypath = lib

                dm.avoid_update = True
                dm.updatelibraryinplace = True

                dm.updatelibraryistrimsheet = False

                bpy.ops.machin3.update_20_decal_library()

        if decal_libs_21:
            print("INFO: Updating 2.1 - 2.4.1 Legacy Decal Libraries")

            for lib in decal_libs_21:
                dm.avoid_update = True
                dm.update21librarypath = lib

                dm.avoid_update = True
                dm.updatelibraryinplace = True

                dm.updatelibraryistrimsheet = False

                bpy.ops.machin3.update_21_decal_library()


        if trimsheet_libs_20:
            print("INFO: Updating 2.0.x Legacy Trim Sheet Libraries")

            for lib in trimsheet_libs_20:
                dm.avoid_update = True
                dm.update20librarypath = lib

                dm.avoid_update = True
                dm.updatelibraryinplace = True

                dm.updatelibraryistrimsheet = True

                bpy.ops.machin3.update_20_decal_library()


        if trimsheet_libs_21:
            print("INFO: Updating 2.1 - 2.4.1 Legacy Trim Sheet Libraries")

            for lib in trimsheet_libs_21:
                dm.avoid_update = True
                dm.update21librarypath = lib

                dm.avoid_update = True
                dm.updatelibraryinplace = True

                dm.updatelibraryistrimsheet = True

                bpy.ops.machin3.update_21_decal_library()

        dm.avoid_update = True
        dm.updatelibraryinplace = False

        return {'FINISHED'}


class Update18BlendFile(bpy.types.Operator):
    bl_idname = "machin3.update_18_blend_file"
    bl_label = "MACHIN3: Update 1.8 Blend File"
    bl_description = "Update the current Blend file containing 1.8 - 1.9.4 Decals\nALT: Use fallback method utilizing simple path-based approach"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        legacydecalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat if mat.use_nodes and any([node.label.endswith('_ALPHA') for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE'])]
        return legacydecalmats

    def invoke(self, context, event):
        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        version = get_version_from_blender()

        legacydecalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat if mat.use_nodes and any([node.label.endswith('_ALPHA') for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE'])]

        if legacydecalmats:
            updated_decals = []

            materials, orphanmats = self.get_legacy_materials(legacydecalmats, debug=False)

            for idx, (mat, objs_and_slot_indices) in enumerate(materials):
                matching_uuid = context.window_manager.decaluuids.get(mat.DM.uuid)

                if matching_uuid:
                    name, library, _ = matching_uuid[0]

                    decalpath = os.path.join(assetspath, 'Decals', library, name)
                    newmat = append_material(templatepath, "TEMPLATE_%s" % mat.DM.decaltype, relative=False)

                    self.update_legacy_material(context, library, name, version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices)

                    if newmat not in updated_decals:
                        updated_decals.append(newmat)

                else:
                    print("WARNING: Decal %s %s could not be found among the registered decals!" % (mat.DM.decalname, mat.DM.uuid))

                    if event.alt:
                        print("INFO: Trying path based method to find it")

                        library = mat.DM.decallibrary
                        name = mat.DM.decalname.replace(library + '_', '')

                        decalpath = os.path.join(assetspath, 'Decals', library, name)

                        if os.path.exists(decalpath):
                            decaltype = mat.DM.decaltype

                            masks_path = os.path.join(decalpath, 'masks.png')
                            ao_curv_height_path = os.path.join(decalpath, 'ao_curv_height.png')
                            normal_path = os.path.join(decalpath, 'normal.png')
                            color_path = os.path.join(decalpath, 'color.png')

                            if decaltype in ["SIMPLE", "SUBSET", "PANEL"] and all(os.path.exists(path) for path in [masks_path, ao_curv_height_path, normal_path]) or decaltype == "INFO" and all(os.path.exists(path) for path in [masks_path, color_path]):
                                newmat = append_material(templatepath, "TEMPLATE_%s" % mat.DM.decaltype, relative=False)

                                self.update_legacy_material(context, mat.DM.decallibrary, mat.DM.decalname.replace(mat.DM.decallibrary + '_', ''), version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices)
                        else:
                            print("WARNING: decal path doesn't exist:", decalpath)

            self.deduplicate_decalmats(updated_decals)

            for mat in orphanmats:
                print("Removing orphan mat:", mat.name)
                bpy.data.materials.remove(mat, do_unlink=True)

        return {'FINISHED'}

    def deduplicate_decalmats(self, updated_decals):

        unique_textures = {}
        unique_parallaxgroups = {}

        unique_decalgroups = {'SIMPLE': None, 'SUBSET': None, 'PANEL': None, 'INFO': None}

        for mat in sorted(updated_decals, key=lambda x: x.name):
            decaltype = mat.DM.decaltype

            textures = get_decal_textures(mat)

            if mat.DM.uuid not in unique_textures:
                unique_textures[mat.DM.uuid] = textures

            elif unique_textures[mat.DM.uuid] != textures:
                set_decal_textures(mat, unique_textures[mat.DM.uuid])

            dg = get_decalgroup_from_decalmat(mat)

            if unique_decalgroups[decaltype]:
                bpy.data.node_groups.remove(dg.node_tree, do_unlink=True)
                dg.node_tree = unique_decalgroups[decaltype]

            else:
                unique_decalgroups[decaltype] = dg.node_tree

                indexRegex = re.compile(r"(.+\.decal_group)\.[\d]+")
                mo = indexRegex.match(dg.node_tree.name)

                if mo:
                    dg.node_tree.name = mo.group(1)

            pg = get_parallaxgroup_from_decalmat(mat)

            if pg:
                if mat.DM.uuid not in unique_parallaxgroups:
                    unique_parallaxgroups[mat.DM.uuid] = pg.node_tree

                elif unique_parallaxgroups[mat.DM.uuid] != pg.node_tree:
                    dup_tree = pg.node_tree
                    hg = get_heightgroup_from_parallaxgroup(pg)

                    if hg:
                        bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

                    pg.node_tree = unique_parallaxgroups[mat.DM.uuid]
                    bpy.data.node_groups.remove(dup_tree, do_unlink=True)

    def update_legacy_material(self, context, library, name, version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices):
        print("INFO: Updating legacy decal material", mat.name)

        for obj, slot_idx in objs_and_slot_indices:
            obj.material_slots[slot_idx].material = newmat

            obj.DM.version = version

        textures = get_decal_textures(newmat)

        for textype, img in textures.items():
            img.filepath = os.path.join(decalpath, "%s.png" % (textype.lower()))


        if mat.DM.ismatched:
            newmat.DM.ismatched = True
            newmat.DM.matchedmaterialto = mat.DM.matchedmaterialto
            newmat.DM.matchedmaterial2to = mat.DM.matchedmaterial2to
            newmat.DM.matchedsubsetto = mat.DM.matchedsubsetto

        dg = get_decalgroup_from_decalmat(mat)
        newdg = get_decalgroup_from_decalmat(newmat)

        if dg and newdg:
            material, material2, subset = get_decalgroup_as_dict(dg)

            set_decalgroup_from_dict(newdg, material, material2, subset)

            if newmat.DM.decaltype == 'INFO':
                newdg.inputs['Invert'].default_value = dg.inputs['Invert'].default_value

            elif newmat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL']:
                newdg.inputs['AO Multiplier'].default_value = dg.inputs['AO Strength'].default_value
                newdg.inputs['Curvature Multiplier'].default_value = dg.inputs['Edge Highlights'].default_value


        set_props_and_node_names_of_decal(library, name, None, newmat, list(textures.values()), mat.DM.decaltype, mat.DM.uuid, version, mat.DM.creator)

        newmat.blend_method = mat.blend_method

        set_defaults(decalmat=newmat, ignore_material_blend_method=True)

        pg = get_parallaxgroup_from_decalmat(mat)

        if pg:
            newpg = get_parallaxgroup_from_decalmat(newmat)

            if newpg:
                newpg.inputs[0].default_value = pg.inputs[0].default_value

        print("INFO: Success! library: %s, name: %s" % (library, name))

        remove_decalmat(mat, remove_textures=True, legacy=True, debug=False)

    def get_legacy_materials(self, legacydecalmats, debug=False):
        orphans = []
        mats = []

        for mat in legacydecalmats:
            if mat.users == 0:
                orphans.append(mat)
                continue

            objects = [obj for obj in bpy.data.objects if obj.type == 'MESH' and mat.name in obj.data.materials]

            objs_and_slot_indices = []

            for obj in objects:
                for idx, slot in enumerate(obj.material_slots):
                    if slot.material == mat:
                        objs_and_slot_indices.append((obj, idx))
                        break

            mats.append((mat, objs_and_slot_indices))

        if debug:
            for mat, objindices in mats:
                print(mat.name, [(obj.name, idx) for obj, idx in objindices])

        return mats, orphans


class Update20BlendFile(bpy.types.Operator):
    bl_idname = "machin3.update_20_blend_file"
    bl_label = "MACHIN3: Update 2.0 Blend File"
    bl_description = "Update the current Blend file containing 2.0 - 2.0.1 Decals, Trim Decals and Trim Sheets\nALT: Use fallback method utilizing simple path-based approach"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        legacydecalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.version and 2.0 <= get_version_as_float(mat.DM.version) < 2.1]
        legacytrimsheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat.DM.version and 2.0 <= get_version_as_float(mat.DM.version) < 2.1]
        return legacydecalmats or legacytrimsheetmats

    def invoke(self, context, event):
        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        version = get_version_from_blender()

        legacydecalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.version and 2.0 <= get_version_as_float(mat.DM.version) < 2.1]
        legacytrimsheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat.DM.version and 2.0 <= get_version_as_float(mat.DM.version) < 2.1]

        if legacydecalmats:
            updated_decals = []

            materials, orphanmats = self.get_legacy_materials(legacydecalmats, debug=False)

            for idx, (mat, objs_and_slot_indices) in enumerate(materials):
                matching_uuid = context.window_manager.decaluuids.get(mat.DM.uuid)

                if matching_uuid:
                    name, library, _ = matching_uuid[0]

                    decalpath = os.path.join(assetspath, 'Trims' if mat.DM.istrimdecalmat else 'Decals', library, name)
                    newmat = append_material(templatepath, "TEMPLATE_%s" % mat.DM.decaltype, relative=False)

                    self.update_legacy_decal_material(context, library, name, version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices)

                    if newmat not in updated_decals:
                        updated_decals.append(newmat)

                else:
                    print("WARNING: Decal %s %s could not be found among the registered decals!" % (mat.DM.decalname, mat.DM.uuid))

                    if event.alt:
                        print("INFO: Trying path based method to find it")

                        library = mat.DM.decallibrary
                        name = mat.DM.decalname.replace(library + '_', '')

                        decalpath = os.path.join(assetspath, 'Decals', library, name)

                        if os.path.exists(decalpath):
                            decaltype = mat.DM.decaltype

                            masks_path = os.path.join(decalpath, 'masks.png')
                            ao_curv_height_path = os.path.join(decalpath, 'ao_curv_height.png')
                            normal_path = os.path.join(decalpath, 'normal.png')
                            color_path = os.path.join(decalpath, 'color.png')
                            emission_path = os.path.join(decalpath, 'emission.png')

                            if decaltype in ["SIMPLE", "SUBSET", "PANEL"] and all(os.path.exists(path) for path in [masks_path, ao_curv_height_path, normal_path, emission_path]) or decaltype == "INFO" and all(os.path.exists(path) for path in [masks_path, color_path, emission_path]):
                                newmat = append_material(templatepath, "TEMPLATE_%s" % mat.DM.decaltype, relative=False)

                                self.update_legacy_material(context, mat.DM.decallibrary, mat.DM.decalname.replace(mat.DM.decallibrary + '_', ''), version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices)

                                if newmat not in updated_decals:
                                    updated_decals.append(newmat)
                        else:
                            print("WARNING: decal path doesn't exist:", decalpath)

            self.deduplicate_decalmats(updated_decals)

            for mat in orphanmats:
                print("Removing orphan mat:", mat.name)
                bpy.data.materials.remove(mat, do_unlink=True)

        if legacytrimsheetmats:
            updated_trimsheets = []

            materials, orphanmats = self.get_legacy_materials(legacytrimsheetmats, debug=False)

            for idx, (mat, objs_and_slot_indices) in enumerate(materials):
                data = get_sheetdata_from_uuid(mat.DM.trimsheetuuid)

                if data:
                    sheetpath = os.path.join(assetspath, 'Trims', data['name'])
                    newmat = append_and_setup_trimsheet_material(data, skip_deduplication=True)


                    self.update_legacy_trimsheet_material(context, data, version, assetspath, templatepath, sheetpath, mat, newmat, objs_and_slot_indices)

                    if newmat not in updated_trimsheets:
                        updated_trimsheets.append(newmat)

                    self.deduplicate_trimsheetmats(updated_trimsheets)

                else:
                    print("WARNING: Trim Sheet '%s' %s could not be found among the registered Trim Sheet!" % (mat.DM.trimsheetname, mat.DM.trimsheetuuid))

        return {'FINISHED'}

    def deduplicate_trimsheetmats(self, updated_trimsheets):

        unique_trimsheetgroup = None
        unique_parallaxgroups = {}

        for mat in sorted(updated_trimsheets, key=lambda x: x.name):

            tsg = get_trimsheetgroup_from_trimsheetmat(mat)

            if not unique_trimsheetgroup:
                unique_trimsheetgroup = tsg.node_tree

                indexRegex = re.compile(r"(.+\.decal_group)\.[\d]+")
                mo = indexRegex.match(tsg.node_tree.name)

                if mo:
                    tsg.node_tree.name = mo.group(1)

            else:
                bpy.data.node_groups.remove(tsg.node_tree, do_unlink=True)
                tsg.node_tree = unique_trimsheetgroup

            pg = get_parallaxgroup_from_any_mat(mat)

            if pg:
                if mat.DM.trimsheetuuid not in unique_parallaxgroups:
                    unique_parallaxgroups[mat.DM.trimsheetuuid] = pg.node_tree

                elif unique_parallaxgroups[mat.DM.trimsheetuuid] != pg.node_tree:
                    dup_tree = pg.node_tree
                    hg = get_heightgroup_from_parallaxgroup(pg)

                    if hg:
                        bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

                    pg.node_tree = unique_parallaxgroups[mat.DM.trimsheetuuid]
                    bpy.data.node_groups.remove(dup_tree, do_unlink=True)

    def deduplicate_decalmats(self, updated_decals):

        unique_textures = {}
        unique_parallaxgroups = {}

        unique_decalgroups = {'SIMPLE': None, 'SUBSET': None, 'PANEL': None, 'INFO': None}

        for mat in sorted(updated_decals, key=lambda x: x.name):
            decaltype = mat.DM.decaltype

            textures = get_decal_textures(mat)

            if mat.DM.uuid not in unique_textures:
                unique_textures[mat.DM.uuid] = textures

            elif unique_textures[mat.DM.uuid] != textures:
                set_decal_textures(mat, unique_textures[mat.DM.uuid])

            dg = get_decalgroup_from_decalmat(mat)

            if unique_decalgroups[decaltype]:
                bpy.data.node_groups.remove(dg.node_tree, do_unlink=True)
                dg.node_tree = unique_decalgroups[decaltype]

            else:
                unique_decalgroups[decaltype] = dg.node_tree

                indexRegex = re.compile(r"(.+\.decal_group)\.[\d]+")
                mo = indexRegex.match(dg.node_tree.name)

                if mo:
                    dg.node_tree.name = mo.group(1)

            pg = get_parallaxgroup_from_decalmat(mat)

            if pg:
                if mat.DM.uuid not in unique_parallaxgroups:
                    unique_parallaxgroups[mat.DM.uuid] = pg.node_tree

                elif unique_parallaxgroups[mat.DM.uuid] != pg.node_tree:
                    dup_tree = pg.node_tree
                    hg = get_heightgroup_from_parallaxgroup(pg)

                    if hg:
                        bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

                    pg.node_tree = unique_parallaxgroups[mat.DM.uuid]
                    bpy.data.node_groups.remove(dup_tree, do_unlink=True)

    def update_legacy_trimsheet_material(self, context, sheetdata, version, assetspath, templatepath, sheetpath, mat, newmat, objs_and_slot_indices):
        print("INFO: Updating legacy trim sheet material", mat.name)

        newmat.name = mat.name

        for obj, slot_idx in objs_and_slot_indices:
            obj.material_slots[slot_idx].material = newmat

            obj.DM.version = version

        if mat.DM.ismatched:
            newmat.DM.ismatched = True
            newmat.DM.matchedtrimsheetto = mat.DM.matchedtrimsheetto

        tsg = get_trimsheetgroup_from_trimsheetmat(mat)
        newtsg = get_trimsheetgroup_from_trimsheetmat(newmat)

        if tsg and newtsg:
            matchtsgdict = get_trimsheetgroup_as_dict(tsg)

            set_trimsheetgroup_from_dict(newtsg, matchtsgdict)

            inputs = ['AO Multiplier', 'Curvature Multiplier']

            for i in inputs:
                newtsg.inputs[i].default_value = tsg.inputs[i].default_value

        newmat.blend_method = mat.blend_method

        pg = get_parallaxgroup_from_any_mat(mat)

        if pg:
            newpg = get_parallaxgroup_from_any_mat(newmat)

            if newpg:
                newpg.inputs[0].default_value = pg.inputs[0].default_value

        print("INFO: Success! Material: %s, Trim sheet: %s" % (newmat.name, sheetdata['name']))

        remove_trimsheetmat(mat, remove_textures=False, debug=False)

    def update_legacy_decal_material(self, context, library, name, version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices):
        print("INFO: Updating legacy decal material", mat.name)

        for obj, slot_idx in objs_and_slot_indices:
            obj.material_slots[slot_idx].material = newmat

            obj.DM.version = version

        textures = get_decal_textures(newmat)

        for textype, img in textures.items():
            img.filepath = os.path.join(decalpath, "%s.png" % (textype.lower()))

            img.DM.istrimdecaltex = mat.DM.istrimdecalmat

        if mat.DM.ismatched:
            newmat.DM.ismatched = True
            newmat.DM.matchedmaterialto = mat.DM.matchedmaterialto
            newmat.DM.matchedmaterial2to = mat.DM.matchedmaterial2to
            newmat.DM.matchedsubsetto = mat.DM.matchedsubsetto

        dg = get_decalgroup_from_decalmat(mat)
        newdg = get_decalgroup_from_decalmat(newmat)

        if dg and newdg:
            material, material2, subset = get_decalgroup_as_dict(dg)

            set_decalgroup_from_dict(newdg, material, material2, subset)

            inputs = ['Emission Multiplier']

            if newmat.DM.decaltype == 'INFO':
                inputs.extend(['Alpha', 'Invert'])
            else:
                inputs.extend(['AO Multiplier', 'Curvature Multiplier'])

            for i in inputs:
                newdg.inputs[i].default_value = dg.inputs[i].default_value


        newmat.DM.istrimdecalmat = mat.DM.istrimdecalmat

        set_props_and_node_names_of_decal(library, name, None, newmat, list(textures.values()), mat.DM.decaltype, mat.DM.uuid, version, mat.DM.creator, trimsheetuuid=mat.DM.trimsheetuuid if mat.DM.istrimdecalmat else None)

        newmat.blend_method = mat.blend_method

        set_defaults(decalmat=newmat, ignore_material_blend_method=True)

        pg = get_parallaxgroup_from_decalmat(mat)

        if pg:
            newpg = get_parallaxgroup_from_decalmat(newmat)

            if newpg:
                newpg.inputs[0].default_value = pg.inputs[0].default_value

        print("INFO: Success! library: %s, name: %s" % (library, name))

        remove_decalmat(mat, remove_textures=True, legacy=False, debug=False)

    def get_legacy_materials(self, legacydecalmats, debug=False):
        orphans = []
        mats = []

        for mat in legacydecalmats:
            if mat.users == 0:
                orphans.append(mat)
                continue

            objects = [obj for obj in bpy.data.objects if obj.type == 'MESH' and mat.name in obj.data.materials]

            objs_and_slot_indices = []

            for obj in objects:
                for idx, slot in enumerate(obj.material_slots):
                    if slot.material == mat:
                        objs_and_slot_indices.append((obj, idx))
                        break

            mats.append((mat, objs_and_slot_indices))

        if debug:
            for mat, objindices in mats:
                print(mat.name, [(obj.name, idx) for obj, idx in objindices])

        return mats, orphans


class Update21BlendFile(bpy.types.Operator):
    bl_idname = "machin3.update_21_blend_file"
    bl_label = "MACHIN3: Update 2.1 Blend File"
    bl_description = "Update the current Blend file containing 2.1 - 2.4.1 Decals, Trim Decals and Trim Sheets\nALT: Use fallback method utilizing simple path-based approach"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0):
            legacydecalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.version and 2.1 <= get_version_as_float(mat.DM.version) < 2.5]
            legacytrimsheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat.DM.version and 2.1 <= get_version_as_float(mat.DM.version) < 2.5]
            return legacydecalmats or legacytrimsheetmats

    def invoke(self, context, event):
        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        version = get_version_from_blender()

        legacydecalmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.version and 2.1 <= get_version_as_float(mat.DM.version) < 2.5]
        legacytrimsheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat.DM.version and 2.1 <= get_version_as_float(mat.DM.version) < 2.5]

        if legacydecalmats:
            updated_decals = []

            materials, orphanmats = self.get_legacy_materials(legacydecalmats, debug=False)

            for idx, (mat, objs_and_slot_indices) in enumerate(materials):
                matching_uuid = context.window_manager.decaluuids.get(mat.DM.uuid)

                if matching_uuid:
                    name, library, _ = matching_uuid[0]

                    decalpath = os.path.join(assetspath, 'Trims' if mat.DM.istrimdecalmat else 'Decals', library, name)
                    newmat = append_material(templatepath, "TEMPLATE_%s" % mat.DM.decaltype, relative=False)

                    self.update_legacy_decal_material(context, library, name, version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices)

                    if newmat not in updated_decals:
                        updated_decals.append(newmat)

                else:
                    print("WARNING: Decal %s %s could not be found among the registered decals!" % (mat.DM.decalname, mat.DM.uuid))

                    if event.alt:
                        print("INFO: Trying path based method to find it")

                        library = mat.DM.decallibrary
                        name = mat.DM.decalname.replace(library + '_', '')

                        decalpath = os.path.join(assetspath, 'Decals', library, name)

                        if os.path.exists(decalpath):
                            decaltype = mat.DM.decaltype

                            masks_path = os.path.join(decalpath, 'masks.png')
                            ao_curv_height_path = os.path.join(decalpath, 'ao_curv_height.png')
                            normal_path = os.path.join(decalpath, 'normal.png')
                            color_path = os.path.join(decalpath, 'color.png')
                            emission_path = os.path.join(decalpath, 'emission.png')

                            if decaltype in ["SIMPLE", "SUBSET", "PANEL"] and all(os.path.exists(path) for path in [masks_path, ao_curv_height_path, normal_path, emission_path]) or decaltype == "INFO" and all(os.path.exists(path) for path in [masks_path, color_path, emission_path]):
                                newmat = append_material(templatepath, "TEMPLATE_%s" % mat.DM.decaltype, relative=False)

                                self.update_legacy_material(context, mat.DM.decallibrary, mat.DM.decalname.replace(mat.DM.decallibrary + '_', ''), version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices)

                                if newmat not in updated_decals:
                                    updated_decals.append(newmat)
                        else:
                            print("WARNING: decal path doesn't exist:", decalpath)

            self.deduplicate_decalmats(updated_decals)

            for mat in orphanmats:
                print("Removing orphan mat:", mat.name)
                bpy.data.materials.remove(mat, do_unlink=True)

        if legacytrimsheetmats:
            updated_trimsheets = []

            materials, orphanmats = self.get_legacy_materials(legacytrimsheetmats, debug=False)

            for idx, (mat, objs_and_slot_indices) in enumerate(materials):
                data = get_sheetdata_from_uuid(mat.DM.trimsheetuuid)

                if data:
                    sheetpath = os.path.join(assetspath, 'Trims', data['name'])
                    newmat = append_and_setup_trimsheet_material(data, skip_deduplication=True)

                    self.update_legacy_trimsheet_material(context, data, version, assetspath, templatepath, sheetpath, mat, newmat, objs_and_slot_indices)

                    if newmat not in updated_trimsheets:
                        updated_trimsheets.append(newmat)

                    self.deduplicate_trimsheetmats(updated_trimsheets)

                else:
                    print("WARNING: Trim Sheet '%s' %s could not be found among the registered Trim Sheet!" % (mat.DM.trimsheetname, mat.DM.trimsheetuuid))

        return {'FINISHED'}

    def deduplicate_trimsheetmats(self, updated_trimsheets):

        unique_trimsheetgroup = None
        unique_parallaxgroups = {}

        for mat in sorted(updated_trimsheets, key=lambda x: x.name):

            tsg = get_trimsheetgroup_from_trimsheetmat(mat)

            if not unique_trimsheetgroup:
                unique_trimsheetgroup = tsg.node_tree

                indexRegex = re.compile(r"(.+\.decal_group)\.[\d]+")
                mo = indexRegex.match(tsg.node_tree.name)

                if mo:
                    tsg.node_tree.name = mo.group(1)

            else:
                bpy.data.node_groups.remove(tsg.node_tree, do_unlink=True)
                tsg.node_tree = unique_trimsheetgroup

            pg = get_parallaxgroup_from_any_mat(mat)

            if pg:
                if mat.DM.trimsheetuuid not in unique_parallaxgroups:
                    unique_parallaxgroups[mat.DM.trimsheetuuid] = pg.node_tree

                elif unique_parallaxgroups[mat.DM.trimsheetuuid] != pg.node_tree:
                    dup_tree = pg.node_tree
                    hg = get_heightgroup_from_parallaxgroup(pg)

                    if hg:
                        bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

                    pg.node_tree = unique_parallaxgroups[mat.DM.trimsheetuuid]
                    bpy.data.node_groups.remove(dup_tree, do_unlink=True)

    def deduplicate_decalmats(self, updated_decals):

        unique_textures = {}
        unique_parallaxgroups = {}

        unique_decalgroups = {'SIMPLE': None, 'SUBSET': None, 'PANEL': None, 'INFO': None}

        for mat in sorted(updated_decals, key=lambda x: x.name):
            decaltype = mat.DM.decaltype

            textures = get_decal_textures(mat)

            if mat.DM.uuid not in unique_textures:
                unique_textures[mat.DM.uuid] = textures

            elif unique_textures[mat.DM.uuid] != textures:
                set_decal_textures(mat, unique_textures[mat.DM.uuid])

            dg = get_decalgroup_from_decalmat(mat)

            if unique_decalgroups[decaltype]:
                bpy.data.node_groups.remove(dg.node_tree, do_unlink=True)
                dg.node_tree = unique_decalgroups[decaltype]

            else:
                unique_decalgroups[decaltype] = dg.node_tree

                indexRegex = re.compile(r"(.+\.decal_group)\.[\d]+")
                mo = indexRegex.match(dg.node_tree.name)

                if mo:
                    dg.node_tree.name = mo.group(1)

            pg = get_parallaxgroup_from_decalmat(mat)

            if pg:
                if mat.DM.uuid not in unique_parallaxgroups:
                    unique_parallaxgroups[mat.DM.uuid] = pg.node_tree

                elif unique_parallaxgroups[mat.DM.uuid] != pg.node_tree:
                    dup_tree = pg.node_tree
                    hg = get_heightgroup_from_parallaxgroup(pg)

                    if hg:
                        bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

                    pg.node_tree = unique_parallaxgroups[mat.DM.uuid]
                    bpy.data.node_groups.remove(dup_tree, do_unlink=True)

    def update_legacy_trimsheet_material(self, context, sheetdata, version, assetspath, templatepath, sheetpath, mat, newmat, objs_and_slot_indices):
        print("INFO: Updating legacy trim sheet material", mat.name)

        newmat.name = mat.name

        for obj, slot_idx in objs_and_slot_indices:
            obj.material_slots[slot_idx].material = newmat

            obj.DM.version = version

        if mat.DM.ismatched:
            newmat.DM.ismatched = True
            newmat.DM.matchedtrimsheetto = mat.DM.matchedtrimsheetto

        tsg = get_trimsheetgroup_from_trimsheetmat(mat)
        newtsg = get_trimsheetgroup_from_trimsheetmat(newmat)

        if tsg and newtsg:
            matchtsgdict = get_trimsheetgroup_as_dict(tsg)

            set_trimsheetgroup_from_dict(newtsg, matchtsgdict)

            inputs = ['AO Multiplier', 'Curvature Multiplier']

            for i in inputs:
                newtsg.inputs[i].default_value = tsg.inputs[i].default_value

        newmat.blend_method = mat.blend_method

        pg = get_parallaxgroup_from_any_mat(mat)

        if pg:
            newpg = get_parallaxgroup_from_any_mat(newmat)

            if newpg:
                newpg.inputs[0].default_value = pg.inputs[0].default_value

        print("INFO: Success! Material: %s, Trim sheet: %s" % (newmat.name, sheetdata['name']))

        remove_trimsheetmat(mat, remove_textures=False, debug=False)

    def update_legacy_decal_material(self, context, library, name, version, assetspath, templatepath, decalpath, mat, newmat, objs_and_slot_indices):
        print("INFO: Updating legacy decal material", mat.name)

        for obj, slot_idx in objs_and_slot_indices:
            obj.material_slots[slot_idx].material = newmat

            obj.DM.version = version

        textures = get_decal_textures(newmat)

        for textype, img in textures.items():
            img.filepath = os.path.join(decalpath, "%s.png" % (textype.lower()))

            img.DM.istrimdecaltex = mat.DM.istrimdecalmat

        if mat.DM.ismatched:
            newmat.DM.ismatched = True
            newmat.DM.matchedmaterialto = mat.DM.matchedmaterialto
            newmat.DM.matchedmaterial2to = mat.DM.matchedmaterial2to
            newmat.DM.matchedsubsetto = mat.DM.matchedsubsetto

        dg = get_decalgroup_from_decalmat(mat)
        newdg = get_decalgroup_from_decalmat(newmat)

        if dg and newdg:
            material, material2, subset = get_decalgroup_as_dict(dg)

            set_decalgroup_from_dict(newdg, material, material2, subset)

            inputs = ['Emission Multiplier']

            if newmat.DM.decaltype == 'INFO':
                inputs.extend(['Alpha', 'Invert'])
            else:
                inputs.extend(['AO Multiplier', 'Curvature Multiplier'])

            for i in inputs:
                newdg.inputs[i].default_value = dg.inputs[i].default_value


        newmat.DM.istrimdecalmat = mat.DM.istrimdecalmat

        set_props_and_node_names_of_decal(library, name, None, newmat, list(textures.values()), mat.DM.decaltype, mat.DM.uuid, version, mat.DM.creator, trimsheetuuid=mat.DM.trimsheetuuid if mat.DM.istrimdecalmat else None)

        newmat.blend_method = mat.blend_method

        set_defaults(decalmat=newmat, ignore_material_blend_method=True)

        pg = get_parallaxgroup_from_decalmat(mat)

        if pg:
            newpg = get_parallaxgroup_from_decalmat(newmat)

            if newpg:
                newpg.inputs[0].default_value = pg.inputs[0].default_value

        print("INFO: Success! library: %s, name: %s" % (library, name))

        remove_decalmat(mat, remove_textures=True, legacy=False, debug=False)

    def get_legacy_materials(self, legacydecalmats, debug=False):
        orphans = []
        mats = []

        for mat in legacydecalmats:
            if mat.users == 0:
                orphans.append(mat)
                continue

            objects = [obj for obj in bpy.data.objects if obj.type == 'MESH' and mat.name in obj.data.materials]

            objs_and_slot_indices = []

            for obj in objects:
                for idx, slot in enumerate(obj.material_slots):
                    if slot.material == mat:
                        objs_and_slot_indices.append((obj, idx))
                        break

            mats.append((mat, objs_and_slot_indices))

        if debug:
            for mat, objindices in mats:
                print(mat.name, [(obj.name, idx) for obj, idx in objindices])

        return mats, orphans


class LoadImages(bpy.types.Operator):
    bl_idname = "machin3.load_images"
    bl_label = "MACHIN3: Load Images"
    bl_description = "Load PNG Images to Create Info Decals from"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        wm.collectinfotextures = True

        for img in bpy.data.images:
            i = wm.excludeimages.add()
            i.name = img.name

        bpy.ops.image.open('INVOKE_DEFAULT', display_type='THUMBNAIL', use_sequence_detection=False)


        return {'FINISHED'}


class ClearImages(bpy.types.Operator):
    bl_idname = "machin3.clear_images"
    bl_label = "MACHIN3: Clear Images"
    bl_description = "Clear Pool of Images to be used for Info Decal Creation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        infotexturespath = os.path.join(createpath, "infotextures")

        images = [os.path.join(infotexturespath, f) for f in os.listdir(infotexturespath) if f != ".gitignore"]

        for img in images:
            os.unlink(img)

        reload_infotextures()

        context.scene.DM.create_infoimg_batch = False

        return {'FINISHED'}


class LoadFonts(bpy.types.Operator):
    bl_idname = "machin3.load_fonts"
    bl_label = "MACHIN3: Load Fonts"
    bl_description = "Load Fonts to be used for Info Decal Creation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        wm.collectinfofonts = True

        for font in bpy.data.fonts:
            f = wm.excludefonts.add()
            f.name = font.name

        bpy.ops.font.open('INVOKE_DEFAULT', display_type='THUMBNAIL')


        return {'FINISHED'}


class ClearFonts(bpy.types.Operator):
    bl_idname = "machin3.clear_fonts"
    bl_label = "MACHIN3: Clear Fonts"
    bl_description = "Clear Pool of Fonts to be used for Info Decal Creation"
    bl_options = {'REGISTER', 'UNDO'}

    keepubuntu: BoolProperty(name="Keep Ubuntu Font", default=True)

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        column.prop(self, "keepubuntu")

    def execute(self, context):
        assetspath = get_prefs().assetspath
        createpath = os.path.join(assetspath, "Create")
        infofontspath = os.path.join(createpath, "infofonts")

        fonts = [os.path.join(infofontspath, f) for f in os.listdir(infofontspath) if f != ".gitignore"]

        for font in fonts:
            if self.keepubuntu and os.path.basename(font) == "ubuntu.ttf":
                continue
            os.unlink(font)

        reload_infofonts()

        return {'FINISHED'}
