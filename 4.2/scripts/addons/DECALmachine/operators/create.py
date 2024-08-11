import bpy
from bpy.props import BoolProperty, StringProperty
import os
import re
from uuid import uuid4
import shutil
from mathutils import Vector
from .. utils.registration import get_templates_path, get_prefs, get_version_files, get_version_from_filename, reload_infotextures, reload_infofonts, reload_instant_decals, set_new_decal_index, reload_decal_libraries, reload_trim_libraries, get_version_from_blender, get_version_filename_from_blender, get_version_as_float, is_library_corrupted, is_library_trimsheet, shape_version, get_path, get_version_filename_from_version, is_decal_registered, is_trimsheet_registered
from .. utils.append import append_scene, append_material, append_object
from .. utils.math import get_bbox_dimensions
from .. utils.system import makedir, get_new_directory_index, abspath, get_safe_filename, printd, get_file_size
from .. utils.material import get_decal_textures, get_decalgroup_from_decalmat, get_parallaxgroup_from_decalmat, set_decal_textures, get_heightgroup_from_parallaxgroup, get_decal_texture_nodes, append_and_setup_trimsheet_material
from .. utils.material import get_decalmat, deduplicate_decal_material, remove_decalmat, set_decal_texture_paths, get_decalgroup_as_dict, set_decalgroup_from_dict, get_trimsheetgroup_from_trimsheetmat, get_trimsheetgroup_as_dict, set_trimsheetgroup_from_dict, get_parallaxgroup_from_any_mat, remove_trimsheetmat
from .. utils.material import get_pbrnode_from_mat, set_subset_component_from_decalgroup, get_legacy_materials
from .. utils.modifier import get_auto_smooth, remove_mod
from .. utils.collection import get_decaltype_collection
from .. utils.scene import setup_surface_snapping
from .. utils.decal import align_decal, set_defaults, apply_decal, set_decalobj_name, set_props_and_node_names_of_decal, remove_decal_from_blend
from .. utils.create import bl_info, create_decal_blend, create_info_decal_textures, create_decal_textures, create_decal_geometry, get_decal_source_objects, save_blend, save_uuid, render_thumbnail
from .. utils.pil import pack_textures, text2img, split_alpha, create_new_masks_texture, create_dummy_texture
from .. utils.ui import init_prefs, popup_message
from .. utils.object import update_local_view, remove_obj
from .. utils.assets import get_ambiguous_libs, get_invalid_libs, get_corrupt_libs, get_skipped_update_path, declutter_assetspath, get_assets_dict, reload_all_assets
from .. utils.library import get_short_library_path
from .. utils.property import get_indexed_suffix_name, set_name
from .. utils.time import get_time_code

from . trimsheet import SetupSubsets

batch_update_info = []

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
                text2imgpath = os.path.join(texturespath, get_safe_filename(texturename))

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
        name = get_safe_filename(dm.addlibrary_decalname.strip().replace(' ', '_'))

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

class UpdateDecalLibrary(bpy.types.Operator):
    bl_idname = "machin3.update_decal_library"
    bl_label = "MACHIN3: Update Decal Library"
    bl_description = "Update Decal Library"
    bl_options = {'REGISTER', 'UNDO'}

    path: StringProperty(name="Library Update Path", subtype='DIR_PATH', default='')
    batch: BoolProperty(name="Called from Batch Updated", default=False)
    keep_thumbnails: BoolProperty(name="Keep Original Thumbnails (passed in from Batch Updater)", default=True)
    auto_fix: BoolProperty(name="Auto-Fix Run", default=False)
    @classmethod
    def poll(cls, context):
        return get_prefs().pil

    def execute(self, context):
        debug = False

        global batch_update_info

        scene = context.scene
        dm = scene.DM

        shortpath = get_short_library_path(self.path)

        if self.path:
            if os.path.exists(self.path):
                sourcepath = self.path

            else:
                msg = f"Library path '{self.path}' does not exist!"

                if self.batch:
                    print("WARNING:", msg)
                    batch_update_info.append(f"❌ Ignored {shortpath}. Does not exist!")  # NOTE: should be impossible to get here unless the folder is removed while the update is running
                else:
                    popup_message(msg, title="Illegal Library Path")
                return {'CANCELLED'}

        else:
            return {'CANCELLED'}

        if is_library_corrupted(sourcepath):
            msg = ["The library appears to be corrupted, it contains non-Decal folders!",
                   "It could also be a pre-1.8 Decal Library."]

            if self.batch:
                print("WARNING:", msg[0])
                print("INFO:", msg[1])
                batch_update_info.append(f"❌ Ignored {shortpath}. Library is corrupt and contains non-Decal folders!")  # NOTE: should be impossible to get here as the batch updater excludes corrupted libs 
            else:
                popup_message(msg, title="Corrupted or Unsupported Library")
            return {'CANCELLED'}

        versions = get_version_files(sourcepath)

        if len(versions) == 1:
            if versions[0] == get_version_filename_from_blender():
                msg = [f"The chosen library at '{self.path}'",
                        "is already up to date, and not a Legacy Library, that can be updated!"]

                if self.batch:
                    print("WARNING:", msg[0] + msg[1])
                    batch_update_info.append(f"{'✔' if self.auto_fix else '❌'} Ignored {shortpath}. Library is already up to date{' now, after a previous auto-fixing of the library version' if self.auto_fix else ''}!")
                else:
                    popup_message(msg, title="Already up to date!")
                return {'CANCELLED'}

            elif get_version_as_float(get_version_from_filename(versions[0])) > get_version_as_float(get_version_from_blender()):
                msg = [f"The chosen library at '{self.path}'",
                       f"is newer {'now ' if self.auto_fix else ''}than what DECALmachine in Blender {bpy.app.version_string} can use{', after a previous auto-fixing of the library version' if self.auto_fix else ''}!"]

                if self.batch:
                    print("WARNING:", msg[0] + msg[1])
                    batch_update_info.append(f"❌ Ignored {shortpath}. Library is newer {'now ' if self.auto_fix else ''}than what DECAlmachine in Blender {bpy.app.version_string} can use{', after a previous auto-fixing of the library version' if self.auto_fix else ''}!")
                else:
                    popup_message(msg, title="Next-Gen Library Version!")
                return {'CANCELLED'}

        else:
            if len(versions) > 0:
                print(f"\nINFO: Ambiguous library at '{self.path}'. Force-resetting library version to 1.8 (.is280)! Library version will be determined from each decal independently.")

                for version_filename in versions:
                    os.unlink(os.path.join(self.path, version_filename))

                with open(os.path.join(self.path, '.is280'), 'w') as f:
                    f.write('')

                versions = ['.is280']

            else:
                msg = f"'No version indicator file present in Library at '{self.path}'!"

                if self.batch:
                    print("WARNING:", msg)
                    batch_update_info.append(f"❌ Ignored {shortpath}. Library is invalid as it contains no version indicaor file!")  # NOTE: should be impossible to get here as the batch updater excluses invalid libs
                else:
                    popup_message(msg, title="Invalid Library")

                return {'CANCELLED'}

        is_trimsheet = is_library_trimsheet(sourcepath)

        is_inplace = True if self.batch else dm.update_library_inplace
        
        if not self.batch:

            if is_trimsheet:
                sheetname = os.path.basename(context.scene.DM.updatelibrarypath)
                sheetlib = get_prefs().decallibsCOL.get(sheetname)

                if sheetlib and not dm.update_library_inplace:
                    msg = f"You can't update the selected trimsheet library into the assets path, because a sheet using the name '{sheetname}' is already registered."

                    popup_message(msg, title="Warning")
                    return {'CANCELLED'}

            else:
                if not is_inplace:
                    if not scene.userdecallibs:
                        msg = ["To Update this Library, you need to have a Library in your assets location, where decals can be added to!",
                               "Create a new empty Library in the DECALmachine addon preferences for instance."]

                        popup_message(msg, title="Warning")
                        return {'CANCELLED'}

        version_filename = versions[0]
        version = get_version_as_float(get_version_from_filename(version_filename))

        if self.auto_fix:
            print(f"\nINFO: Re-Starting Update of now version {version} Asset Library at '{self.path}' after fixing library version in previous attempt.")
        else:
            print(f"\nINFO: Starting Update of version {version} Asset Library at '{self.path}'")

        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        keep_thumbnails = self.keep_thumbnails if self.batch else dm.update_keep_old_thumbnails

        if debug:
            print(" version:", version)
            print(" version file:", version_filename)
            print(" trimsheet:", is_trimsheet)
            print(" in-place:", is_inplace)
            print(" keep thumbnails:", keep_thumbnails)

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if not is_inplace:
            set_new_decal_index(self, context)

        if is_trimsheet:
            startidx = '001'

            librarypath = os.path.join(assetspath, 'Trims', os.path.basename(sourcepath))
            inplacepath = self.get_in_place_path(assetspath, is_inplace, libtype='Trims')

            if not is_inplace:
                makedir(librarypath)

            with open(os.path.join(inplacepath if is_inplace else librarypath, get_version_filename_from_blender()), "w") as f:
                f.write('')

            self.copy_trimsheet_textures(sourcepath, inplacepath if is_inplace else librarypath)

        else:
            startidx = '001' if is_inplace else context.window_manager.newdecalidx

            librarypath = os.path.join(assetspath, 'Decals', scene.userdecallibs)
            inplacepath = self.get_in_place_path(assetspath, is_inplace, libtype='Decals')

            if is_inplace:
                with open(os.path.join(inplacepath, get_version_filename_from_blender()), "w") as f:
                    f.write('')

        legacy_decals, meta_files = self.get_legacy_decals(sourcepath, version, version_filename, is_trimsheet=is_trimsheet, debug=debug)

        for metafile in meta_files:
            shutil.copy(metafile, os.path.join(inplacepath if is_inplace else librarypath, os.path.basename(metafile)))

        if legacy_decals:

            names = []
            skipped = []

            for idx, (orig_name, base_name, decalpath, blendpath, iconpath, texturepaths) in enumerate(legacy_decals):
                index = str(int(startidx) + idx).zfill(3)
                index_name = f"{index}_{base_name}" if base_name else index

                size_ret = self.decal_file_size_check(blendpath, iconpath, texturepaths)

                if type(size_ret) == bool:
                    print()
                    print(f"INFO: Updating decal '{base_name} at '{decalpath}'")

                    create_decal_ret = self.create_new_decal(context, version, templatepath, inplacepath if is_inplace else librarypath, index, base_name, decalpath, blendpath, iconpath, texturepaths, keep_thumbnails)

                    if type(create_decal_ret) == tuple:
                        print(f"WARNING: Skipping decal '{base_name}' at '{decalpath}, due to {create_decal_ret[0]}")
                        skipped.append((decalpath, orig_name, index_name, create_decal_ret[0], create_decal_ret[1]))
                        continue

                else:
                    print(f"WARNING: Skipping decal '{base_name}' at '{decalpath}' due to corrupt {size_ret}")
                    skipped.append((decalpath, orig_name, index_name, f"Corrupt {size_ret}", None))
                    continue

                names.append(index_name)

            is_all_skipped = len(skipped) == len(legacy_decals)

            if not self.auto_fix and is_all_skipped:
                if len(set(s[4] for s in skipped)) == 1 and skipped[0][4] is not None:
                    auto_fix = False

                    if all('Decal and Library version mismatch!' in reason for _, _, _, reason, _ in skipped):
                        auto_fix = True

                    elif all('Is this actually a 1.8 (.is280) legacy decal and library?' in reason for _, _, _, reason, _ in skipped):
                        auto_fix = True

                    elif all('Is this actually a 2.0 (or higher) legacy decal and library?' in reason for _, _, _, reason, _ in skipped):
                        auto_fix = True

                    if auto_fix:

                        reason, decal_version = skipped[0][3:5]

                        print(f"\nINFO: All decals of this library, were skipped for the same reason: {reason} Attempting automatic fix by adjusting the library version to {decal_version}")

                        src = os.path.join(sourcepath, version_filename)
                        dst = os.path.join(sourcepath, get_version_filename_from_version(decal_version))

                        os.rename(src, dst)

                        if is_inplace:
                            shutil.rmtree(inplacepath)

                        bpy.ops.machin3.update_decal_library(path=self.path, batch=self.batch, keep_thumbnails=self.keep_thumbnails, auto_fix=True)

                        return {'FINISHED'}

            logrootpath = self.process_skipped_decals(sourcepath, skipped, is_all_skipped, is_trimsheet, is_inplace)

            if is_inplace:

                if is_all_skipped:
                    print(f"\nWARNING: None of the decals could be updated, and all of them have been moved to '{logrootpath}'. See the log.txt file for details")

                    shutil.rmtree(sourcepath)
                    shutil.rmtree(inplacepath)

                    if self.batch:
                        batch_update_info.append(f"❌ Ignored {shortpath}. All Decals were skipped. Check the log.txt file in the {'Trims' if is_trimsheet else 'Decals'}_Skipped folder for details!")

                else:
                    print(f"\nINFO: Replacing original {'trim decal' if is_trimsheet else 'decal'} library folder, with updated library.")

                    if skipped:
                        print(f"WARNING: {len(skipped)}/{len(legacy_decals)} Decals couldn't be updated and have been moved to '{logrootpath}'. See the log.txt file for details.")

                        if self.batch:
                            batch_update_info.append(f"☑  Only some Decals could be updated in {shortpath}. {len(skipped)}/{len(legacy_decals)} Decals were skipped. Check the log.txt file in the {'Trims' if is_trimsheet else 'Decals'}_Skipped folder for details!")

                    else:
                        if self.batch:
                            batch_update_info.append(f"✔ All Decals in {shortpath} were updated successfully{' on second attempt after fixing the library version indicator' if self.auto_fix else ''}!")

                    shutil.rmtree(sourcepath)
                    shutil.move(inplacepath, sourcepath)

                if not self.batch:
                    get_assets_dict(force=True)
                    reload_trim_libraries() if is_trimsheet else reload_decal_libraries()

            else:
                if is_all_skipped:
                    print(f"\nWARNING: None of the decals could be updated! See the log.txt file in '{logrootpath}' for details.")

                    if self.batch:
                        batch_update_info.append(f"❌ Ignored {shortpath}. All Decals were skipped. Check the log.txt file in the {'Trims' if is_trimsheet else 'Decals'}_Skipped folder for details!")

                elif skipped:
                    print(f"\nWARNING: {len(skipped)}/{len(legacy_decals)} Decals couldn't be updated. See the log.txt file in '{logrootpath}' for details.")

                    if self.batch:
                        batch_update_info.append(f"☑  Only some Decals could be updated from {shortpath}. {len(skipped)}/{len(legacy_decals)} Decals were skipped. Check the log.txt file in the {'Trims' if is_trimsheet else 'Decals'}_Skipped folder for details!")

                else:
                    if self.batch:
                        batch_update_info.append(f"✔ All Decals from {shortpath} were updated successfully{' on second attempt after fixing the library version indicator' if self.auto_fix else ''}!")

                if names and not self.batch:
                    get_assets_dict(force=True)

                    reload_trim_libraries() if is_trimsheet else reload_decal_libraries(library=scene.userdecallibs, default=names[-1])
            if not self.batch:

                dm.avoid_update = True
                dm.updatelibrarypath = ''

                if is_all_skipped:
                    popup_message(["None of the Decals could be updated! ALL of them were skipped. See the log.txt file at", f"'{logrootpath}' for details."], title="Skipped Decals")

                elif skipped:
                    popup_message([f"{len(skipped)}/{len(legacy_decals)} Decals couldn't be updated. See the log.txt file at", f"'{logrootpath}' for details."], title="Skipped Decals")

        else:
            print(f"INFO: Library at {sourcepath} is Empty!")

            if is_inplace:
                print(f"INFO: Replacing original {'trim decal' if is_trimsheet else 'decal'} library folder, with updated library.")

                shutil.rmtree(sourcepath)
                shutil.move(inplacepath, sourcepath)

                if not self.batch:
                    get_assets_dict(force=True)

                    reload_trim_libraries() if is_trimsheet else reload_decal_libraries()

                    dm.avoid_update = True
                    dm.updatelibrarypath = ''

                    popup_message(["Library is Empty, therefore no decals were updated.", "The library itself was updated though."], title="Empty Library")

                if self.batch:
                    batch_update_info.append(f"✔ Empty Library in {sourcepath} was updated successfully!")

            else:
                print("INFO: Therefore, there is nothing to do.")

                if not self.batch:
                    popup_message("Library is Empty, therefore no decals were updated!", title="Empty Library")

                if self.batch:
                    batch_update_info.append(f"❌ Ignored Empty Library in {sourcepath}. There is nothing to update!")

        print(f"\nINFO: DECALmachine Library Update concluded{' on second attempt after fixing the library version indicator' if self.auto_fix else ''}!")

        return {'FINISHED'}

    def get_in_place_path(self, assetspath, is_inplace, libtype='Decals'):
        if is_inplace:
            inplace_path = os.path.join(assetspath, libtype, '__IN_PLACE__')

            if os.path.exists(inplace_path):
                print(f"WARNING: A previous __IN_PLACE__ path exists already at {inplace_path}, removing!")
                shutil.rmtree(inplace_path)

            makedir(inplace_path)
            return inplace_path

    def update_18_decal_textures(self, decalpath, texturepaths, decaltype):
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

    def copy_trimsheet_textures(self, sourcepath, librarypath):
        sheettextures = [(f, os.path.join(sourcepath, f)) for f in os.listdir(sourcepath) if f.endswith('.png')]

        for f, path in sheettextures:
            newpath = os.path.join(librarypath, f)
            shutil.copy(path, newpath)

            print(f"INFO: Copying trim sheet texture from {path} to to {newpath}")

    def copy_decal_textures(self, decalpath, texturepaths, decaltype):
        newpaths = {}

        for decaltype, path in texturepaths.items():
            newpath = os.path.join(decalpath, '%s.png' % (decaltype.lower()))
            shutil.copy(path, newpath)
            newpaths[decaltype] = newpath

        return newpaths

    def get_legacy_decals(self, librarypath, version, version_filename, is_trimsheet=False, debug=False):
        if debug:
            print("\n looking for legacy decals of version", version)

        legacy_decals = []
        meta_files = []

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

                if 'masks.png' in files:
                    texturepaths['MASKS'] = os.path.join(decalpath, 'masks.png')
                
                if version >= 2.0:
                    if 'emission.png' in files:
                        texturepaths['EMISSION'] = os.path.join(decalpath, 'emission.png')

                    if 'normal.png' in files:
                        texturepaths['NORMAL'] = os.path.join(decalpath, 'normal.png')

                    if 'color.png' in files:
                        texturepaths['COLOR'] = os.path.join(decalpath, 'color.png')

                else:
                    if 'nrm_alpha.png' in files:
                        texturepaths['NRM_ALPHA'] = os.path.join(decalpath, 'nrm_alpha.png')

                    if 'color_alpha.png' in files:
                        texturepaths['COLOR_ALPHA'] = os.path.join(decalpath, 'color_alpha.png')

                legacy_decals.append((f, decalname, decalpath, blendpath, iconpath, texturepaths))

                print(f"INFO: Found legacy decal '{decalname}' at '{decalpath}'")

            elif (f.startswith('.') and f != version_filename) or (is_trimsheet and f == 'data.json'):
                meta_files.append(os.path.join(librarypath, f))

        if debug:
            print("legacy decals:")

            for folder, base_name, decalpath, blendpath, iconpath, texturepaths in legacy_decals:
                print()
                print("folder:", folder)
                print("base name:", base_name)
                print("decal path:", decalpath)
                print("blend path:", blendpath)
                print("icon path:", iconpath)
                printd(texturepaths)

            print("meta files:", meta_files)

        return legacy_decals, meta_files

    def decal_file_size_check(self, blendpath, iconpath, texturepaths):
        for path in [blendpath, iconpath] + list(texturepaths.values()):
            size = get_file_size(path)

            if not size:
                filename = os.path.basename(path)

                return f"blend file: {filename}" if path == blendpath else f"thumbnail: {filename}" if path == iconpath else f"texture: {filename}"

        return True

    def create_new_decal(self, context, library_version, templatepath, librarypath, index, name, decalpath, blendpath, iconpath, texturepaths, keepthumbnails):
        def verify_decal_versions():
            if library_version < 2.0:

                if decalobj.DM.version or decalmat.DM.version:
                    msg = "Invalid version property! Is this actually a 2.0 (or higher) legacy decal and library?"

                    decal_version = decalmat.DM.version

                    remove_decalmat(decalmat)
                    remove_obj(decalobj)
                    return msg, decal_version

            else:

                if decalobj.DM.version and decalmat.DM.version and decalobj.DM.version != decalmat.DM.version:
                    msg = f"Decal object and material version mismatch! Decal object version is {decalobj.DM.version}, but Decal material version is {decalmat.DM.version}!"

                    remove_decalmat(decalmat)
                    remove_obj(decalobj)
                    return msg, None

                if not decalobj.DM.version and not decalmat.DM.version:
                    msg = "Unset Decal version! Decal version property is not set on both - the Decal object and material! Is this actually a 1.8 (.is280) legacy decal and library?"

                    remove_decalmat(decalmat)
                    remove_obj(decalobj)
                    return msg, 1.8

                if not decalobj.DM.version:
                    msg = "Unset Decal version! Decal version property is not set on Decal object!"

                    remove_decalmat(decalmat)
                    remove_obj(decalobj)
                    return msg, None

                if not decalmat.DM.version:
                    msg = "Unset Decal version! Decal version property is not set on Decal material!"

                    remove_decalmat(decalmat)
                    remove_obj(decalobj)
                    return msg, None

                decal_version = get_version_as_float(decalmat.DM.version)

                if not (shape_version(decal_version) == shape_version(library_version)):
                    msg = f"Decal and Library version mismatch! Decal version is {decal_version}, but Library indicates it's version {library_version}!"

                    remove_decalmat(decalmat)
                    remove_obj(decalobj)
                    return msg, decal_version

            if library_version < 2.0:
                required_map_types = {'COLOR_ALPHA'} if decaltype == 'INFO' else {'AO_CURV_HEIGHT', 'NRM_ALPHA'} if decaltype == 'SIMPLE' else {'AO_CURV_HEIGHT', 'NRM_ALPHA', 'MASKS'}

            else:
                required_map_types = {'COLOR', 'EMISSION', 'MASKS'} if decaltype == 'INFO' else {'AO_CURV_HEIGHT', 'NORMAL', 'EMISSION', 'MASKS'}

            if (map_types := set(texturepaths.keys())) != required_map_types:
                msg = f"Missing decal textures! Required: {', '.join(required_map_types)} - Missing: {', '.join(required_map_types - map_types)}"

                remove_decalmat(decalmat)
                remove_obj(decalobj)
                return msg, None

        decalobj = append_object(blendpath, 'LIBRARY_DECAL')

        if not decalobj:
            msg = "Missing Decal object"
            return msg, None

        decalmat = decalobj.active_material if decalobj.active_material and decalobj.active_material.DM.isdecalmat else None

        if not decalmat:
            msg = "Missing Decal material on Decal object!"

            remove_obj(decalobj)
            return msg, None

        decaltype = decalmat.DM.decaltype

        if ret := verify_decal_versions():
            return ret

        create_version = get_version_from_blender()

        decalscene = bpy.data.scenes.new(name="Decal Asset")
        context.window.scene = decalscene
        mcol = decalscene.collection

        mcol.objects.link(decalobj)

        decalname = f"{index}_{name}" if name else index
        newdecalpath = makedir(os.path.join(librarypath, decalname))

        newmat = append_material(templatepath, f"TEMPLATE_{decaltype}", relative=False)
        decalobj.active_material = newmat

        if library_version < 2.0:
            newtexturepaths = self.update_18_decal_textures(newdecalpath, texturepaths, decaltype)

        else:
            newtexturepaths = self.copy_decal_textures(newdecalpath, texturepaths, decaltype)

        if decalobj.DM.trimsheetuuid and os.path.exists(os.path.join(decalpath, '.ispanel')):
            shutil.copy(os.path.join(decalpath, '.ispanel'), newdecalpath)

        set_name(decalobj, 'LIBRARY_DECAL', force=True)
        set_name(decalobj.data, 'LIBRARY_DECAL', force=True)

        set_decal_texture_paths(newmat, newtexturepaths)

        newtextures = get_decal_textures(newmat)

        if decalobj.DM.istrimdecal:
            newmat.DM.istrimdecalmat = True

            for img in newtextures.values():
                img.DM.istrimdecaltex = True

        set_props_and_node_names_of_decal("LIBRARY", "DECAL", decalobj, newmat, list(newtextures.values()), decaltype, decalobj.DM.uuid, create_version, decalobj.DM.creator, decalobj.DM.trimsheetuuid)

        context.view_layer.objects.active = decalobj

        dg = get_decalgroup_from_decalmat(decalmat)
        newdg = get_decalgroup_from_decalmat(newmat)

        for i in dg.inputs:
            if i.name.endswith('Emission'):
               if bpy.app.version < (4, 0, 0):
                   newdg.inputs[i.name].default_value = i.default_value
               else:
                   newdg.inputs[i.name + ' Color'].default_value = i.default_value
            elif i.name == 'Emission Multiplier':
                newdg.inputs[i.name].default_value = i.default_value

        if decaltype == 'INFO':
            nodes = get_decal_texture_nodes(newmat)

            color = nodes.get('COLOR')
            masks = nodes.get('MASKS')

            if color:
                color.interpolation = 'Closest'

            if masks:
                masks.interpolation = 'Closest'

        elif decaltype in ['SUBSET', 'PANEL']:
            subsetdict = get_decalgroup_as_dict(dg)[2]
            set_decalgroup_from_dict(newdg, subset=subsetdict)

        pg = get_parallaxgroup_from_decalmat(decalmat)

        if pg:
            newpg = get_parallaxgroup_from_decalmat(newmat)

            if newpg:
                newpg.inputs[0].default_value = pg.inputs[0].default_value

        if bpy.app.version >= (4, 1, 0) and (mod := get_auto_smooth(decalobj)):
            remove_mod(mod)

        save_uuid(newdecalpath, decalobj.DM.uuid)

        save_blend(decalobj, newdecalpath, decalscene)

        if keepthumbnails:
            shutil.copy(iconpath, os.path.join(newdecalpath, "decal.png"))

            bpy.data.meshes.remove(decalobj.data, do_unlink=True)
            remove_decalmat(newmat, remove_textures=True)

        else:
            render_thumbnail(context, newdecalpath, decalobj, newmat, removeall=True)

        remove_decalmat(decalmat, remove_textures=True, legacy=False)

        print(" Sucess! Updated decal:", decalname, "to:", newdecalpath)
        return True

    def process_skipped_decals(self, sourcepath, skipped, is_all_skipped, is_trimsheet, is_inplace):
        if skipped:

            for idx, (decal_path, orig_name, index_name, skip_reason, _) in enumerate(skipped):

                if is_inplace:

                    skippedpath = get_skipped_update_path('Trims' if is_trimsheet else 'Decals', os.path.basename(sourcepath), index_name)

                    shutil.move(decal_path, skippedpath)

                    log_path = os.path.join(os.path.dirname(skippedpath), "log.txt")

                else:
                    log_path = os.path.join(sourcepath, "log.txt")

                time_code = get_time_code().split(' ')

                name = index_name if is_inplace else orig_name

                if os.path.exists(log_path):
                    with open(log_path, 'a') as f:

                        if idx == 0:
                            f.write(f"This part of the log file was added by DECALmachine on {time_code[0]} at {time_code[1]} when {'ALL' if is_all_skipped else 'SOME'} Decals of the Library '{os.path.basename(sourcepath)}' could not be updated. \n\n")

                        f.write(f"📁 {name} - {skip_reason}\n")

                        if idx == len(skipped) - 1:
                            f.write("\n")

                else:
                    with open(log_path, 'w') as f:
                        f.write(f"This file was generated by DECALmachine on {time_code[0]} at {time_code[1]} when {'ALL' if is_all_skipped else 'SOME'} Decals of the Library '{os.path.basename(sourcepath)}' could not be updated. \n\n")
                        f.write(f"📁 {name} - {skip_reason}\n")

                if is_inplace:
                    version_path = os.path.join(os.path.dirname(skippedpath), '.is25')

                    if not os.path.exists(version_path):
                        with open(version_path, "w") as f:
                            f.write('')

            return os.path.dirname(log_path)

class BatchUpdate(bpy.types.Operator):
    bl_idname = "machin3.batch_update_decal_libraries"
    bl_label = "MACHIN3: Batch Update Legacy Decal and Trim Sheet libraries"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        assets_dict = get_assets_dict()

        if assets_dict['LEGACY'] or assets_dict['AMBIGUOUS']:
            return get_prefs().pil

    @classmethod
    def description(cls, context, properties):
        desc = "Batch Update Legacy Decal and Trim Sheet libraries found in the Assets Path"
        desc += "\nALT: Force Thumbnail Re-Render"
        return desc

    def invoke(self, context, event):
        debug = False

        global batch_update_info 
        batch_update_info = []

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        print("\nINFO: Starting DECALmachine Batch Asset Update")

        decluttered = declutter_assetspath()

        if decluttered:
            for old_path, new_path in decluttered:
                shortpath = get_short_library_path(old_path)
                is_dir = os.path.isdir(new_path)

                batch_update_info.append(f"🗑️ Decluttered {shortpath}{'/' if is_dir else ''}. This {'Folder' if is_dir else 'File'} should not be there!")

            batch_update_info.append('')

        assets_dict = get_assets_dict(force=True)

        legacy = assets_dict['LEGACY']
        ambiguous = get_ambiguous_libs()

        for path in legacy + ambiguous:
            bpy.ops.machin3.update_decal_library(path=path, batch=True, keep_thumbnails=not event.alt, auto_fix=False)

        reload_all_assets()

        print("\nINFO: DECALmachine Batch Asset Update concluded\n")

        assets_dict = get_assets_dict(force=True)

        obsolete = assets_dict['OBSOLETE']
        invalid = get_invalid_libs()
        corrupt = get_corrupt_libs()

        for idx, path in enumerate(obsolete + invalid + corrupt):

            if idx == 0:
                batch_update_info.append('')

            shortpath = get_short_library_path(path)

            if path in obsolete:
                batch_update_info.append(f"❌ Ignored {shortpath}. Library is obsolete. It predates DECALmachine 1.8/Blender 2.80 and can't be user-updated anymore!")

            elif path in invalid:
                batch_update_info.append(f"❌ Ignored {shortpath}. Library is invalid. It contains no version indicator file!")

            elif path in corrupt:
                batch_update_info.append(f"❌ Ignored {shortpath}. Library is corrupt. There are non-Decal folders in it!")

        if batch_update_info:

            logspath = makedir(os.path.join(get_path(), 'logs'))
            name = get_indexed_suffix_name(os.listdir(logspath), 'batch_updated', end='.log')

            time_code = get_time_code().split(' ')
            log_path = os.path.join(os.path.join(logspath, name))

            with open(log_path, 'w') as f:
               f.write(f"This file was generated by DECALmachine on {time_code[0]} at {time_code[1]} when Batch Updating your assets location\nat {get_prefs().assetspath} in Blender {bpy.app.version_string} with DECALmachine {'.'.join([str(v) for v in bl_info['version']])}\n\n")

               for line in batch_update_info:
                   f.write(f"{line}\n")

               if any(msg.startswith('❌') or msg.startswith('☑') for msg in batch_update_info):
                   f.writelines(['\n', 'ℹ  If you require assistance with the failed updates above, you can get in touch with decal@machin3.io!\n', '   Make sure to use the Get Support tool, if you do so!\n'])

            if any(msg.startswith('❌') or msg.startswith('☑') for msg in batch_update_info):
                batch_update_info.append('')
                batch_update_info.append('ℹ  If you require assistance with the failed updates, you can get in touch with decal@machin3.io!')
                batch_update_info.append('      Make sure to use the Get Support tool, if you do so!')

            popup_message(batch_update_info, title="Batch Asset Update")

        return {'FINISHED'}

class UpdateBlendFile(bpy.types.Operator):
    bl_idname = "machin3.update_blend_file"
    bl_label = "MACHIN3: Update Blend File with Legacy Decals"
    bl_description = "Update the current Blend file Legacy Decals, Trim Decals and Trim Sheets"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        legacy_dict = get_legacy_materials(force=False, debug=False)
        return legacy_dict['DECAL'] or legacy_dict['TRIM']

    def invoke(self, context, event):
        assetspath = get_prefs().assetspath
        templatepath = get_templates_path()

        expected_version = get_version_from_blender()

        legacy_dict = get_legacy_materials(force=True, debug=False)

        legacy_decalmats = legacy_dict['DECAL']
        legacy_sheetmats = legacy_dict['TRIM']

        ghost_decals = []
        ghost_sheets = []

        if legacy_decalmats:
            updated_decals = []
            orphan_decals = []

            for version, decals in sorted(legacy_decalmats.items()):
                print(f"\nINFO: Updating Version {version} Legacy Decal Materials in this .blend file!")

                registered, ghosts, orphans = self.sort_materials_into_registered_ghosts_orphans(decals['materials'], debug=False)
                
                ghost_decals.extend(ghosts)
                orphan_decals.extend(orphans)

                for mat, objs_and_slot_indices, library, decalname, libtype in registered:
                    decalpath = os.path.join(assetspath, libtype, library, decalname)

                    newmat = append_material(templatepath, f"TEMPLATE_{mat.DM.decaltype}", relative=False)

                    self.update_legacy_decal_material(library, decalname, expected_version, decalpath, mat, newmat, objs_and_slot_indices)

                    if newmat not in updated_decals:
                        updated_decals.append(newmat)

            self.deduplicate_decalmats(updated_decals)

            for mat in orphan_decals:
                print(f"INFO: Removing unused orphan decal material '{mat.name}'")
                bpy.data.materials.remove(mat, do_unlink=True)

        if legacy_sheetmats:
            updated_sheets = []
            orphan_sheets = []

            for version, sheets in sorted(legacy_sheetmats.items()):
                print(f"\nINFO: Updating Version {version} Legacy Trimsheet Materials in this .blend file!")

                registered, ghosts, orphans = self.sort_materials_into_registered_ghosts_orphans(sheets['materials'], trim=True, debug=False)

                ghost_sheets.extend(ghosts)
                orphan_sheets.extend(orphans)

                for mat, objs_and_slot_indices, sheetdata in registered:
                    newmat = append_and_setup_trimsheet_material(sheetdata, skip_deduplication=True)

                    self.update_legacy_trimsheet_material(sheetdata, expected_version, mat, newmat, objs_and_slot_indices)

                    if newmat not in updated_sheets:
                        updated_sheets.append(newmat)

            self.deduplicate_trimsheetmats(updated_sheets)

            for mat in orphan_sheets:
                print(f"INFO: Removing unused orphan trimsheet material '{mat.name}'")
                bpy.data.materials.remove(mat, do_unlink=True)

        get_legacy_materials(force=True, debug=False)

        if ghost_decals or ghost_sheets:
            msg = ["Some Ghost Assets have been found in this .blend file, that couldn't be updated.",
                   "Ghosts are decals or trimsheets that aren't currently registered in DECALmachine.",
                   "It may be necessary to import or update these decals, libraries, or trim sheets.",
                   ""]

            if ghost_decals:
                msg.append("These decal materials could not be updated:")

                for mat in ghost_decals:
                    msg.append(f"  • {mat.name}")

            if ghost_sheets:
                msg.append("These trimsheet materials could not be updated:")

                for mat in ghost_sheets:
                    msg.append(f"  • {mat.name}")

            popup_message(msg, title="Ghost Assets in .blend File")

        return {'FINISHED'}

    def sort_materials_into_registered_ghosts_orphans(self, sheetmats, trim=False, debug=False):
        registered = []
        ghosts = []
        orphans = []

        for mat in sheetmats:

            if mat.users == 0:
                orphans.append(mat)
                continue

            is_reg = is_trimsheet_registered(mat.DM.trimsheetuuid) if trim else is_decal_registered(mat.DM.uuid)

            if is_reg:
                if trim:
                    sheetdata = is_reg
                else:
                    decalname, library, libtype = is_reg[0]

                objects = [obj for obj in bpy.data.objects if obj.type == 'MESH' and mat.name in obj.data.materials]

                objs_and_slot_indices = []

                for obj in objects:
                    for idx, slot in enumerate(obj.material_slots):
                        if slot.material == mat:
                            objs_and_slot_indices.append((obj, idx))
                            break

                if trim:
                    registered.append((mat, objs_and_slot_indices, sheetdata))
                else:
                    registered.append((mat, objs_and_slot_indices, library, decalname, libtype))

            else:
                ghosts.append(mat)

        if debug:
            print("  registered:")

            if trim:
                for mat, objindices, _ in registered:
                    print("  ", mat.name, [(obj.name, idx) for obj, idx in objindices])

            else:
                for mat, objindices, _, _, _ in registered:
                    print("  ", mat.name, [(obj.name, idx) for obj, idx in objindices])

            print("  ghosts:")
            for mat in ghosts:
                print("  ", mat.name)

            print("  orphans:")
            for mat in orphans:
                print("  ", mat.name)

        return registered, ghosts, orphans

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

                indexRegex = re.compile(r".+\.decal_group\.[\d]+")
                mo = indexRegex.match(dg.node_tree.name)

                if mo:
                    dg.node_tree.name = f"{decaltype.lower()}.decal_group"

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

    def deduplicate_trimsheetmats(self, updated_trimsheets):
        unique_trimsheetgroups = {}
        unique_parallaxgroups = {}

        for mat in sorted(updated_trimsheets, key=lambda x: x.name):

            tsg = get_trimsheetgroup_from_trimsheetmat(mat)

            if mat.DM.trimsheetuuid not in unique_trimsheetgroups:
                unique_trimsheetgroups[mat.DM.trimsheetuuid] = tsg.node_tree
                tsg.node_tree.name = f"trimsheet.{mat.DM.trimsheetname}"

            else:
                dup_tree = tsg.node_tree
                tsg.node_tree = unique_trimsheetgroups[mat.DM.trimsheetuuid]
                bpy.data.node_groups.remove(dup_tree, do_unlink=True)

            pg = get_parallaxgroup_from_any_mat(mat)

            if pg:
                if mat.DM.trimsheetuuid not in unique_parallaxgroups:
                    unique_parallaxgroups[mat.DM.trimsheetuuid] = pg.node_tree
                    pg.node_tree.name = f"parallax.{mat.DM.trimsheetname}"

                elif unique_parallaxgroups[mat.DM.trimsheetuuid] != pg.node_tree:
                    dup_tree = pg.node_tree
                    hg = get_heightgroup_from_parallaxgroup(pg)

                    if hg:
                        bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

                    pg.node_tree = unique_parallaxgroups[mat.DM.trimsheetuuid]
                    bpy.data.node_groups.remove(dup_tree, do_unlink=True)

    def update_legacy_decal_material(self, library, name, version, decalpath, mat, newmat, objs_and_slot_indices):
        print(f" Updating legacy decal material '{mat.name}'")

        is_pre_20_decal = get_version_as_float(mat.DM.version) < 2

        for obj, slot_idx in objs_and_slot_indices:
            obj.material_slots[slot_idx].material = newmat

            obj.DM.version = version

        textures = get_decal_textures(newmat)

        for textype, img in textures.items():
            img.filepath = os.path.join(decalpath, f"{textype.lower()}.png")

            if not is_pre_20_decal:
                img.DM.istrimdecaltex = mat.DM.istrimdecalmat

        newmat.DM.istrimdecalmat = mat.DM.istrimdecalmat
        
        newmat.blend_method = mat.blend_method

        if mat.DM.ismatched:
            newmat.DM.ismatched = True
            newmat.DM.matchedmaterialto = mat.DM.matchedmaterialto
            newmat.DM.matchedmaterial2to = mat.DM.matchedmaterial2to
            newmat.DM.matchedsubsetto = mat.DM.matchedsubsetto

        set_defaults(decalmat=newmat, ignore_material_blend_method=True)

        dg = get_decalgroup_from_decalmat(mat)
        newdg = get_decalgroup_from_decalmat(newmat)

        if dg and newdg:
            material, material2, subset = get_decalgroup_as_dict(dg)

            set_decalgroup_from_dict(newdg, material, material2, subset)

            inputs = []

            if not is_pre_20_decal:
                inputs.append('Emission Multiplier')

            if newmat.DM.decaltype == 'INFO':
                inputs.append('Invert')

                if not is_pre_20_decal:
                    inputs.append('Alpha')

            else:
                inputs.extend(['AO Multiplier', 'Curvature Multiplier'])

            for i in inputs:
                if is_pre_20_decal:
                    if i == 'AO Multiplier':
                        newdg.inputs[i].default_value = dg.inputs['AO Strength'].default_value
                    elif i == 'Curvature Multiplier':
                        newdg.inputs[i].default_value = dg.inputs['Edge Highlights'].default_value
                    else:
                        newdg.inputs[i].default_value = dg.inputs[i].default_value
                else:
                    newdg.inputs[i].default_value = dg.inputs[i].default_value

        pg = get_parallaxgroup_from_decalmat(mat)

        if pg:
            newpg = get_parallaxgroup_from_decalmat(newmat)

            if newpg:
                newpg.inputs[0].default_value = pg.inputs[0].default_value

        print(f"  ✔ Success! library: '{library}' decal '{name}' has been updated!")

        set_props_and_node_names_of_decal(library, name, None, newmat, list(textures.values()), mat.DM.decaltype, mat.DM.uuid, version, mat.DM.creator, trimsheetuuid=mat.DM.trimsheetuuid if mat.DM.istrimdecalmat else None)

        remove_decalmat(mat, remove_textures=True, legacy=is_pre_20_decal, debug=False)

    def update_legacy_trimsheet_material(self, sheetdata, version, mat, newmat, objs_and_slot_indices):
        print(f" Updating legacy trimsheet material '{mat.name}'")

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
        is_subset = SetupSubsets.is_subset_trimsheet(None, mat)

        if is_subset and is_subset == 'COLOR_MIX':
            SetupSubsets.deselect_all_nodes(None, newmat)

            newtsg, newsubset = SetupSubsets.get_tsg_and_subset_node(None, newmat)

            if is_subset == 'COLOR_MIX':
                SetupSubsets.add_color_mix_nodes(None, newmat, newtsg, newsubset)

        print(f"  ✔ Success! Trimsheet: '{sheetdata['name']}' has been updated!")

        remove_trimsheetmat(mat, remove_textures=False, debug=False)

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
