import bpy
import bmesh
from mathutils import Vector, Matrix
import os
import re
from shutil import rmtree
from . append import append_object
from . material import get_decalmat, deduplicate_decal_material, get_parallax_amount
from . collection import sort_into_collections, unlink_object
from . scene import setup_surface_snapping
from . material import get_decal_textures, get_decalgroup_from_decalmat, get_parallaxgroup_from_decalmat, get_heightgroup_from_parallaxgroup, get_decal_texture_nodes, auto_match_material, remove_decalmat, get_panel_material
from . raycast import get_origin_from_object, get_closest, get_origin_from_face, get_origin_from_object_boundingbox, get_grid_intersection, cast_obj_ray_from_mouse, cast_obj_ray_from_object, get_two_origins_from_face
from . object import remove_obj, update_local_view, parent, lock
from . modifier import get_nrmtransfer, get_displace, add_nrmtransfer, add_displace, get_shrinkwrap, get_auto_smooth, remove_mod
from . registration import get_prefs, get_version_from_blender, reload_decal_libraries, reload_instant_decals, set_new_decal_index, reload_trim_libraries, shape_version
from . math import create_rotation_matrix_from_normal, flatten_matrix, get_sca_matrix, get_edge_normal
from . draw import draw_vector, draw_points, draw_vectors
from . property import get_cycles_visibility, set_cycles_visibility, set_name
from . developer import Benchmark
from . ui import popup_message
from .. colors import normal

def get_decals(context):
    sel = context.selected_objects
    source = sel if sel else context.visible_objects
    return sorted([obj for obj in source if obj.DM.isdecal], key=lambda d: d.name)

def get_target(depsgraph, active, sel, decal):
    target = active if active and active in sel and not active.DM.isdecal else None

    if target:
        return target

    else:
        target, _, _, _, _, _ = cast_obj_ray_from_object(depsgraph, decal, (0, 0, -1), backtrack=0.01)

        return target if target else decal.parent if decal.parent else None

def insert_single_decal(context, libraryname, decalname, instant=False, trim=False, force_cursor_align=False, push_undo=False):
    assetspath = get_prefs().assetspath

    T = Benchmark(context.scene.DM.debug)

    if instant:
        blendpath = os.path.join(assetspath, 'Create', 'decalinstant', decalname, 'decal.blend')
    elif trim:
        blendpath = os.path.join(assetspath, 'Trims', libraryname, decalname, 'decal.blend')
    else:
        blendpath = os.path.join(assetspath, 'Decals', libraryname, decalname, 'decal.blend')

    decalobj = append_object(blendpath, "LIBRARY_DECAL")

    T.measure("append decal")

    if decalobj:
        expected_version = get_version_from_blender(use_float=True)
        decal_version = shape_version(decalobj.DM.version)

        if decal_version == expected_version:
            scene = context.scene

            bpy.ops.object.select_all(action='DESELECT')

            T.measure("deselection")

            scene.collection.objects.link(decalobj)

            if bpy.app.version >= (4, 1, 0) and (mod := get_auto_smooth(decalobj)):
                remove_mod(mod)

            dg = context.evaluated_depsgraph_get()

            align_decal(decalobj, scene, dg, force_cursor_align=force_cursor_align)

            dg.update()

            T.measure("align")

            mat = get_decalmat(decalobj)

            if mat:
                decalmat = deduplicate_decal_material(context, mat, name=decalname, library=libraryname, instant=instant, trim=trim)
                decalobj.active_material = decalmat

                T.measure("de-duplicate material")

                decalmat.DM.parallaxdefault = get_parallax_amount(decalmat)
                set_props_and_node_names_of_decal(libraryname, decalname, decalobj=decalobj, decalmat=decalmat)

                T.measure("set properties")

                set_defaults(decalobj=decalobj, decalmat=decalmat)
                T.measure("set defaults")
                apply_decal(dg, decalobj, raycast=True)

                T.measure("apply decal")

                set_decalobj_name(decalobj)

                T.measure("set decal obj name")

                setup_surface_snapping(scene)

                T.measure("set surface snapping")

            sort_into_collections(context, decalobj)

            T.measure("collections")

            decalobj.select_set(True)
            context.view_layer.objects.active = decalobj

            T.measure("decal selection")

            update_local_view(context.space_data, [(decalobj, True)])

            T.measure("add to local view")

            scene.DM.quickinsertlibrary = libraryname
            scene.DM.quickinsertdecal = decalname
            scene.DM.quickinsertisinstant = instant
            scene.DM.quickinsertistrim = trim

            T.measure("set quick insert props")

            T.total()

            if push_undo:
                bpy.ops.ed.undo_push(message=f"Insert Decal {decalobj.DM.decalname}")

            return

        else:
            mat = get_decalmat(decalobj)

            if mat:
                remove_decalmat(mat, remove_textures=True, legacy=decal_version < 2, debug=False)

            remove_obj(decalobj, debug=False)

            if decal_version < expected_version:
                reason = 'LEGACY', "the decal version differs from what its library indicates. It's a legacy decal, not a current one."
            else:
                reason = 'NEXT-GEN', "the decal version differs from what its library indicates. It's a next-gen decal, not a current one."

    else:
        reason = 'MISSING', "the decal object in the asset .blend file is missing."
    
    msg = [f"Decal '{decalname}' of library '{libraryname}' couldn't be brought into the scene, because",
           f"{reason[1]}"]

    popup_message(msg, title=f"Failed to bring {reason[0].title()} Decal into the Scene")

def batch_insert_decals(context, libraryname, decalname, trim=False):
    def get_batch(context, folder, debug=False):
        batch = []

        for uuid, decals in context.window_manager.decaluuids.items():
            for name, library, libtype in decals:
                if library == libraryname and libtype == folder:
                    batch.append((folder, library, name))

        if debug:
            for folder, library, name in batch:
                print(folder, library, name)

        return batch

    assetspath = get_prefs().assetspath

    folder = 'Trims' if trim else 'Decals'
    batch = get_batch(context, folder, debug=False)

    missing = []
    legacy = []
    future = []

    if batch:
        assetspath = get_prefs().assetspath
        expected_version = get_version_from_blender(use_float=True)

        xoffset, cursory, cursorz = context.scene.cursor.location
        prev_size = 0

        for idx, (folder, library, name) in enumerate(batch):
            decalpath = os.path.join(assetspath, folder, library, name)

            decalobj = append_object(os.path.join(decalpath, "decal.blend"), "LIBRARY_DECAL")

            if decalobj:
                decal_version = shape_version(decalobj.DM.version)

                if decal_version == expected_version:
                    size = decalobj.dimensions[0]
                    xoffset += prev_size / 2 + size / 2 + 0.05

                    decalobj.matrix_world.translation = Vector((xoffset, cursory, cursorz))

                    sort_into_collections(context, decalobj)

                    if bpy.app.version >= (4, 1, 0) and (mod := get_auto_smooth(decalobj)):
                        remove_mod(mod)

                    decalobj.select_set(False)

                    prev_size = size

                    mat = get_decalmat(decalobj)

                    if mat:
                        decalmat = deduplicate_decal_material(context, mat, name=name, library=library, trim=folder=='Trims')
                        decalobj.active_material = decalmat

                        decalmat.DM.parallaxdefault = get_parallax_amount(decalmat)
                        set_props_and_node_names_of_decal(library, name, decalobj=decalobj, decalmat=decalmat)

                        set_defaults(decalobj=decalobj, decalmat=decalmat)
                        set_decalobj_name(decalobj)

                        update_local_view(context.space_data, [(decalobj, True)])

                else:
                    mat = get_decalmat(decalobj)

                    if mat:
                        remove_decalmat(mat, remove_textures=True, legacy=decal_version < 2, debug=False)

                    remove_obj(decalobj, debug=False)

                    if decal_version < expected_version:
                        legacy.append(name)
                    else:
                        future.append(name)

            else:
                missing.append(name)

        if not any(legacy or future or missing):
            return

    if batch:
        total_count = len(batch)
        failed_count = len(legacy) + len(future) + len(missing)
        failed_types = []

        msg = [f"{failed_count}/{total_count} Decals of library '{libraryname}' couldn't be brought into the scene, because"]

        if legacy:
            is_all = len(legacy) == total_count
            msg.append(f"{'All' if is_all else len(legacy)} Decals are legacy decals, not current ones.")

            if not is_all:
                for name in legacy:
                    msg.append(f" • {name}")

            failed_types.append('Legacy')

        if future:
            is_all = len(future) == total_count
            msg.append(f"{'All' if is_all else len(future)} Decals are next-gen decals, not current ones.")
            
            if not is_all:
                for name in future:
                    msg.append(f" • {name}")

            failed_types.append('Next-Gen')

        if missing:
            is_all = len(missing) == total_count
            msg.append(f"{'All' if is_all else len(missing)} Decals are invalid due to a missing decal object.")

            if not is_all:
                for name in missing:
                    msg.append(f" • {name}")

            failed_types.append('Next-Gen')
        
        popup_message(msg, title=f"Failed to bring {failed_count} Decals into the Scene")

    else:
        popup_message("You can't batch insert Decals from an Empty Library, duh", title=f"Empty Library")

def remove_decal_from_blend(uuid):
    if uuid:
        for obj in bpy.data.objects:
            if obj.DM.isdecal and obj.DM.uuid == uuid:
                bpy.data.meshes.remove(obj.data, do_unlink=True)

        for mat in bpy.data.materials:
            if mat.DM.isdecalmat and mat.DM.uuid == uuid:
                remove_decalmat(mat, debug=False)

        for img in bpy.data.images:
            if img.DM.isdecaltex and img.DM.uuid == uuid:
                bpy.data.images.remove(img, do_unlink=True)

def remove_single_decal(context, libraryname, decalname, instant=False, trim=False):
    debug = False

    if debug:
        print()
        print("library:", libraryname)
        print("decal", decalname)
        print("instant:", instant)
        print("trim:", trim)

    assetspath = get_prefs().assetspath

    if debug:
        print("assetspath:", assetspath, os.path.exists(assetspath))

    if instant:
        librarypath = os.path.join(assetspath, 'Create', 'decalinstant')
    elif trim:
        librarypath = os.path.join(assetspath, 'Trims', libraryname)
    else:
        librarypath = os.path.join(assetspath, 'Decals', libraryname)

    if debug:
        print("librarypath:", librarypath, os.path.exists(librarypath))

        if os.path.exists(librarypath):
            for f in os.listdir(librarypath):
                print("", f)

    decalpath = os.path.join(librarypath, decalname)
    uuidpath = os.path.join(decalpath, "uuid")

    if debug:
        print("uuidpath:", uuidpath, os.path.exists(uuidpath))
        print("decalpath:", decalpath, os.path.exists(decalpath))

        if os.path.exists(decalpath):
            for f in os.listdir(decalpath):
                print("", f)

    if os.path.exists(uuidpath):
        with open(uuidpath, "r") as f:
            uuid = f.read()

        if debug:
            print()
            print("removing decal with uuid:", uuid)

        remove_decal_from_blend(uuid)

        if debug:
            print(" removed!")

    if debug:
        print()
        print("removing decalpath", decalpath)

    rmtree(decalpath)

    if debug:
        print(" removed!")

    folders = [f for f in sorted(os.listdir(librarypath)) if os.path.isdir(os.path.join(librarypath, f))]

    decals = []
    nondecals = []

    for folder in folders:
        files = os.listdir(os.path.join(librarypath, folder))

        if all([f in files for f in ["decal.blend", "decal.png", "uuid"]]):
            decals.append(folder)
        else:
            nondecals.append(folder)

    for nondecal in nondecals:
        path = os.path.join(librarypath, nondecal)

        print("Found broken instant decal, also removing %s!" % (path))
        rmtree(path)

    default = decals[-1] if decals else None
    if instant:
        reload_instant_decals(default=default)
    elif trim:
        reload_trim_libraries(library=libraryname, default=default)
    else:
        reload_decal_libraries(library=libraryname, default=default)
        set_new_decal_index(None, context)

def set_props_and_node_names_of_decal(library, name, decalobj=None, decalmat=None, decaltextures=None, decaltype=None, uuid=None, version=None, creator=None, trimsheetuuid=None):
    if any([decalobj, decalmat, decaltextures]):
        decalname = f"{library}_{name}"

        force = decalname == 'LIBRARY_DECAL'

        if decalobj:
            if not decalmat:
                decalmat = decalobj.active_material

        if decalmat:
            set_name(decalmat, decalname, force=force)

            if not decaltextures:
                textures = get_decal_textures(decalmat)

                if textures:
                    decaltextures = list(textures.values())

        complist = [comp for comp in [decalobj, decalmat] + decaltextures if comp]

        for component in complist:
            component.DM.decallibrary = library
            component.DM.decalname = decalname
            component.DM.decalmatname = decalname

            if decaltype:
                component.DM.decaltype = decaltype

            if uuid:
                component.DM.uuid = uuid

            if version:
                component.DM.version = version

            if creator:
                component.DM.creator = creator

            if trimsheetuuid:
                component.DM.trimsheetuuid = trimsheetuuid

        if decalobj and decalmat:
            decalobj.DM.uuid = decalmat.DM.uuid
            decalobj.DM.creator = decalmat.DM.creator
            decalobj.DM.version = decalmat.DM.version

        if decalmat:
            decalgroup = get_decalgroup_from_decalmat(decalmat)
            decalgroup.name = f"{decalmat.DM.decaltype.lower()}.{decalname}"
            set_name(decalgroup.node_tree, f"{decalmat.DM.decaltype.lower()}.decal_group", force=force)

            parallaxgroup = get_parallaxgroup_from_decalmat(decalmat)

            if parallaxgroup:
                parallaxgroup.name = f"parallax.{decalname}"

                set_name(parallaxgroup.node_tree, parallaxgroup.name, force=force)

                decalmat.DM.parallaxnodename = parallaxgroup.name

                heightgroups = get_heightgroup_from_parallaxgroup(parallaxgroup, getall=True)

                if heightgroups:
                    for idx, hg in enumerate(heightgroups):
                        hg.name = f"height.{decalname}"

                        if idx == 0:
                            set_name(hg.node_tree, hg.name, force=force)

            else:
                decalmat.DM.parallaxnodename = ""

            imgnodes = get_decal_texture_nodes(decalmat, height=True)

            for textype, node in imgnodes.items():
                node.name = f"{textype.lower()}.{decalname}"

                if textype != "HEIGHT":
                    set_name(node.image, node.name, force=force)

def set_decalobj_props_from_material(obj, decalmat):
    obj.DM.decallibrary = decalmat.DM.decallibrary
    obj.DM.decalname = decalmat.DM.decalname
    obj.DM.decalmatname = decalmat.DM.decalmatname
    obj.DM.uuid = decalmat.DM.uuid
    obj.DM.version = decalmat.DM.version
    obj.DM.creator = decalmat.DM.creator

def set_decalobj_name(decalobj, decalname=None, uuid=None):
    decalname = decalname if decalname else decalobj.DM.decalname
    uuid = uuid if uuid else decalobj.DM.uuid

    if uuid:
        decals = [obj for obj in bpy.data.objects if obj != decalobj and obj.DM.uuid == uuid]

        if decals:
            counters = []
            countRegex = re.compile(r".+\.([\d]{3,})")

            for obj in decals:
                mo = countRegex.match(obj.name)

                if mo:
                    count = mo.group(1)
                    counters.append(int(count))

            if counters:
                decalobj.name = "%s.%s" % (decalname, str(max(counters) + 1).zfill(3))

            else:
                decalobj.name = decalname + ".001"

        else:
            decalobj.name = decalname

        decalobj.data.name = decalobj.name

def clear_decalobj_props(obj):
    obj.DM.uuid = ''
    obj.DM.version = ''
    obj.DM.decaltype = 'NONE'
    obj.DM.decallibrary = ''
    obj.DM.decalname = ''
    obj.DM.decalmatname = ''

    obj.DM.isdecal = False
    obj.DM.isbackup = False
    obj.DM.isprojected = False
    obj.DM.issliced = False

    obj.DM.decalbackup = None
    obj.DM.projectedon = None
    obj.DM.slicedon = None

    obj.DM.creator = ''

    obj.DM.backupmx = flatten_matrix(Matrix())

    obj.DM.istrimsheet = False
    obj.DM.trimsheetname = ''
    obj.DM.trimsheetindex = ''
    obj.DM.trimsheetuuid = ''

    obj.DM.istrimdecal = False

def ensure_decalobj_versions(decals, debug=False):
    expected_version = get_version_from_blender(use_float=True)

    if debug:
        print("\nexpected version:", expected_version)

    current_decals = []
    legacy_decals = []
    future_decals = []

    for obj in decals:
        if debug:
            print(obj.name, obj.DM.version)

        decal_version = shape_version(obj.DM.version)

        if decal_version == expected_version:
            current_decals.append(obj)

            if debug:
                print(" valid current decal")

        elif decal_version < expected_version:
            legacy_decals.append(obj)

            if debug:
                print(" invalid legacy decals")

        else:
            future_decals.append(obj)

            if debug:
                print(" invalid future decals")

    return current_decals, legacy_decals, future_decals

def align_decal(decalobj, scene, depsgraph, force_cursor_align=False):
    dm = scene.DM
    wm = bpy.context.window_manager
    view = bpy.context.space_data

    if decalobj.DM.uuid in dm.individualscales:
        decalobj.scale = dm.individualscales[decalobj.DM.uuid].scale

    elif dm.globalscale != 1:
        decalobj.scale *= scene.DM.globalscale

    depsgraph.update()

    displace = get_displace(decalobj)

    if displace:
        displace.mid_level = scene.DM.height

    if dm.align_mode == "CURSOR" or force_cursor_align or (view.region_3d.view_perspective == 'CAMERA' and scene.camera.data.type == 'ORTHO'):
        decalobj.location = bpy.context.scene.cursor.location
        bpy.context.scene.cursor.rotation_mode = "QUATERNION"
        decalobj.rotation_mode = "QUATERNION"
        decalobj.rotation_quaternion = bpy.context.scene.cursor.rotation_quaternion

    elif dm.align_mode == "RAYCAST":
        mousepos = wm.decal_mousepos

        hitobj, loc, normal, _, _ = cast_obj_ray_from_mouse(mousepos, exclude_decals=False, exclude_objects=[decalobj], debug=False)

        _, _, sca = decalobj.matrix_world.decompose()

        if hitobj:
            rotmx = create_rotation_matrix_from_normal(hitobj.matrix_world, normal, loc, debug=False)
            decalobj.matrix_world = Matrix.LocRotScale(loc, rotmx.to_3x3(), sca)

        else:
            loc, rotmx = get_grid_intersection(mousepos)
            decalobj.matrix_world = Matrix.LocRotScale(loc, rotmx.to_3x3(), sca)

def apply_decal(depsgraph, decalobj, target=None, raycast=False, force_automatch=False):
    displace = get_displace(decalobj)

    if not displace:
        displace = add_displace(decalobj)

    nrmtransfer = get_nrmtransfer(decalobj)

    if decalobj.DM.decaltype == 'PANEL' and nrmtransfer.loop_mapping != 'NEAREST_POLYNOR':
        nrmtransfer.loop_mapping = 'NEAREST_POLYNOR'

    dm = bpy.context.scene.DM

    faceidx2 = None

    if decalobj.DM.isprojected:
        origin = get_origin_from_object_boundingbox(depsgraph, decalobj, ignore_mirrors=True)

        if target:
            targets = [target]

        else:
            targets = [decalobj.DM.projectedon] if decalobj.DM.projectedon else [decalobj.parent] if decalobj.parent else [obj for obj in bpy.context.visible_objects if obj.type == "MESH" and not obj.DM.isdecal]

        target, target_eval, _, _, faceidx, _ = get_closest(depsgraph, targets, origin)

    elif decalobj.DM.issliced:
        origin, origin2, direction = get_two_origins_from_face(decalobj)

        if target:
            targets = [target]

        else:
            targets = [decalobj.DM.slicedon] if decalobj.DM.slicedon else [decalobj.parent] if decalobj.parent else [obj for obj in bpy.context.visible_objects if obj.type == "MESH" and not obj.DM.isdecal]

        target, target_eval, _, _, faceidx, _ = get_closest(depsgraph, targets, origin)

        _, _, _, _, faceidx2, _ = get_closest(depsgraph, targets, origin2)

    else:
        if raycast:

            target, target_eval, _, _, faceidx, _ = cast_obj_ray_from_object(depsgraph, decalobj, (0, 0, -1), backtrack=0.01, debug=False)

        else:
            origin, _ = get_origin_from_object(decalobj)

            if target:
                targets = [target]

            else:
                targets = [obj for obj in bpy.context.visible_objects if obj.type == "MESH" and not obj.DM.isdecal]

            target, target_eval, _, _, faceidx, _ = get_closest(depsgraph, targets, origin)

    if target and faceidx is not None:

        if nrmtransfer.object != target:
            nrmtransfer.object = target

        shrinkwrap = get_shrinkwrap(decalobj)
        if shrinkwrap:
            if shrinkwrap.target != target:
                shrinkwrap.target = target

        if decalobj.parent != target:
            parent(decalobj, target)

        if decalobj.DM.isprojected:
            if decalobj.DM.projectedon != target:
                decalobj.DM.projectedon = target

        if decalobj.DM.issliced:
            if decalobj.DM.slicedon != target:
                decalobj.DM.slicedon = target

        if (dm.auto_match == "AUTO" or force_automatch) and decalobj.active_material and decalobj.DM.decaltype in ["SIMPLE", "SUBSET", "PANEL"]:
            auto_match_material(decalobj, decalobj.active_material, matchobj=target_eval, face_idx=faceidx, face_idx2=faceidx2)

        elif dm.auto_match == "MATERIAL" and decalobj.DM.decaltype in ["SIMPLE", "SUBSET", "PANEL"]:
            auto_match_material(decalobj, decalobj.active_material, matchmatname=bpy.context.window_manager.matchmaterial)

        return True

    elif dm.auto_match == "MATERIAL" and decalobj.DM.decaltype in ["SIMPLE", "SUBSET", "PANEL"]:
        auto_match_material(decalobj, decalobj.active_material, matchmatname=bpy.context.window_manager.matchmaterial)

    return True

def set_defaults(decalobj=None, decalmat=None, ignore_material_blend_method=False, ignore_normal_transfer_visibility=False):
    dm = bpy.context.scene.DM

    if decalobj:

        set_cycles_visibility(decalobj, 'shadow', False)
        set_cycles_visibility(decalobj, 'diffuse', False)

        if get_cycles_visibility(decalobj, 'glossy') != dm.glossyrays:
            set_cycles_visibility(decalobj, 'glossy', dm.glossyrays)

        if not ignore_normal_transfer_visibility:
            mod = get_nrmtransfer(decalobj)

            if mod:
                render = dm.normaltransfer_render
                viewport = dm.normaltransfer_viewport

                if mod.show_render != render:
                    mod.show_render = render

                if mod.show_viewport != viewport:
                    mod.show_viewport = viewport

    if decalmat:
        decalgroup = get_decalgroup_from_decalmat(decalmat)
        nodetrees = [decalgroup.node_tree] if decalgroup else []

        textures = get_decal_textures(decalmat)

        if decalmat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL']:
            parallaxgroup = get_parallaxgroup_from_decalmat(decalmat)
            heightgroup = get_heightgroup_from_parallaxgroup(parallaxgroup) if parallaxgroup else None

            if parallaxgroup:
                nodetrees.append(parallaxgroup.node_tree)

            if heightgroup:
                nodetrees.append(heightgroup.node_tree)

            parallax = dm.parallax

            if parallaxgroup and parallaxgroup.mute == parallax:
                parallaxgroup.mute = not parallax

            if decalgroup:

                ao = dm.ao_strength
                i = decalgroup.inputs.get("AO Strength")

                if i and i.default_value != ao:
                    i.default_value = ao

                highlights = float(dm.edge_highlights)
                i = decalgroup.inputs.get("Edge Highlights")

                if i and i.default_value != highlights:
                    i.default_value = highlights

        if decalmat.DM.decaltype == 'INFO':

            colornode = get_decal_texture_nodes(decalmat).get("COLOR")
            masksnode = get_decal_texture_nodes(decalmat).get("MASKS")
            interpolation = dm.color_interpolation

            if colornode and colornode.interpolation != interpolation:
                colornode.interpolation = interpolation

            if masksnode and masksnode.interpolation != interpolation:
                masksnode.interpolation = interpolation

            invert = dm.invert_infodecals

            if decalgroup:
                i = decalgroup.inputs.get("Invert")

                if i and i.default_value != invert:
                    i.default_value = invert

        decalmat.use_backface_culling = True

        if not ignore_material_blend_method:
            blendmode = dm.alpha_blendmode

            if decalmat.blend_method != blendmode:
                decalmat.blend_method = blendmode

        hide = dm.hide_materials

        if hide:
            if not decalmat.name.startswith("."):
                decalmat.name = ".%s" % decalmat.name

        else:
            if decalmat.name.startswith("."):
                decalmat.name = decalmat.name[1:]

        hide = dm.hide_materials

        if hide:
            if not decalmat.name.startswith("."):
                decalmat.name = ".%s" % decalmat.name

        else:
            if decalmat.name.startswith("."):
                decalmat.name = decalmat.name[1:]

        if textures:
            hide = dm.hide_textures

            for img in textures.values():
                if hide:
                    if not img.name.startswith("."):
                        img.name = ".%s" % img.name

                else:
                    if img.name.startswith("."):
                        img.name = img.name[1:]

        hide = dm.hide_nodetrees

        for tree in nodetrees:
            if hide:
                if not tree.name.startswith("."):
                    tree.name = ".%s" % tree.name

            else:
                if tree.name.startswith("."):
                    tree.name = tree.name[1:]

def get_decal_library_and_name_from_uuid(context, uuid):
    uuids = context.window_manager.decaluuids

    for duuid, decals in uuids.items():

        if duuid == uuid:
            name, library, libtype = decals[0]
            return name, library, libtype
    return None, None, None

def get_panel_width(obj, scene):
    dm = scene.DM

    mxi = obj.matrix_world.inverted_safe()

    return (Vector((0, 0, dm.panelwidth * dm.globalscale)) @ mxi).length

def get_panel_width_from_edge(obj, edge):
    mx = obj.matrix_world
    return (mx.to_3x3() @ (edge.verts[1].co - edge.verts[0].co)).length * bpy.context.scene.DM.globalscale

def sort_panel_geometry(bm, debug=False):
    geo_sequences = []

    faces = [f for f in bm.faces]
    boundary_edges = [e for e in bm.edges if not e.is_manifold]

    if len(boundary_edges) == 4 * len(faces):

        ends = []

        for f in faces:
            edge_lengths = sorted([(e, e.calc_length()) for e in f.edges], key=lambda x: x[1])
            for e, _ in edge_lengths[0:2]:
                ends.append(e)

        rail_edges = ends

    else:
        ends = [e for e in boundary_edges if all(len(v.link_edges) == 2 for v in e.verts)]
        rail_edges = [e for e in bm.edges if e not in boundary_edges] + ends

    edge = ends[0] if ends else rail_edges[0]
    loop = edge.link_loops[0]
    face = loop.face

    geo = [(face, edge)]

    while faces:
        if debug:
            print("face:", face.index, "edge:", edge.index, "loop:", loop)

        face.smooth = True

        faces.remove(face)
        rail_edges.remove(edge)
        if edge in ends:
            ends.remove(edge)

        while True:
            loop = loop.link_loop_next

            if loop.edge in ends or loop.edge == geo[0][1]:

                if loop.edge in ends:
                    cyclic = False
                    ends.remove(loop.edge)

                elif loop.edge == geo[0][1]:
                    cyclic = True

                if debug:
                    print("cyclic:", cyclic)

                geo_sequences.append((geo, cyclic))

                if faces:
                    edge = ends[0] if ends else rail_edges[0]
                    loop = edge.link_loops[0]
                    face = loop.face

                    geo = [(face, edge)]

                break

            elif loop.edge.is_manifold:

                loop = loop.link_loop_radial_next
                face = loop.face
                edge = loop.edge

                geo.append((face, edge))

                break

    return geo_sequences

def create_panel_uvs(bm, geo_sequences, panel, width=None):
    uvs = bm.loops.layers.uv.verify()

    for geo, cyclic in geo_sequences:
        u_start = 0
        u_end = 0

        if not width:
            width_edge = geo[1][1] if len(geo) > 1 else geo[0][1]
            width = get_panel_width_from_edge(panel, width_edge)

        for gidx, (face, edge) in enumerate(geo):
            if cyclic:
                edge_next = geo[0][1] if gidx == len(geo) - 1 else geo[gidx + 1][1]

            else:
                if len(geo) == 1:
                    edge_next = [e for e in face.edges if not any(v in edge.verts for v in e.verts)][0]

                elif gidx == len(geo) - 1:
                    edge_next = [e for e in face.edges if all(len(v.link_edges) == 2 for v in e.verts)][0]

                else:
                    edge_next = geo[0][1] if gidx == len(geo) - 1 else geo[gidx + 1][1]

            midpoint = (edge.verts[0].co + edge.verts[1].co) / 2
            midpoint_next = (edge_next.verts[0].co + edge_next.verts[1].co) / 2

            distance_local = (midpoint - midpoint_next).length * 1 / width

            distance_world = (panel.matrix_world.to_3x3() @ Vector((distance_local, 0, 0))).length

            u_end += distance_world

            loop = [l for l in edge.link_loops if l.face == face][0]

            maxvstart = maxvend = 1
            minvstart = minvend = 0

            if not cyclic:
                if gidx == 0:
                    ratio = edge.calc_length() / edge_next.calc_length()
                    if ratio < 1 / 3:
                        maxvstart = 0.5 + ratio / 2
                        minvstart = 0.5 - ratio / 2

                elif gidx == len(geo) - 1:
                    ratio = edge_next.calc_length() / edge.calc_length()
                    if ratio < 1 / 3:
                        maxvend = 0.5 + ratio / 2
                        minvend = 0.5 - ratio / 2

            for i in range(4):
                if i == 0:
                    loop[uvs].uv = (u_start, maxvstart)
                elif i == 1:
                    loop[uvs].uv = (u_start, minvstart)
                elif i == 2:
                    loop[uvs].uv = (u_end, minvend)
                elif i == 3:
                    loop[uvs].uv = (u_end, maxvend)

                loop = loop.link_loop_next

            u_start = u_end

    bm.to_mesh(panel.data)
    bm.clear()

def change_panel_width(bm, amount, panel=None, scene=None, set_prop=False):
    boundary_edges = [e for e in bm.edges if not e.is_manifold]

    if len(boundary_edges) == 4 * len(bm.faces):
        ends = []

        for f in bm.faces:
            edge_lengths = sorted([(e, e.calc_length()) for e in f.edges], key=lambda x: x[1])
            for e, _ in edge_lengths[0:2]:
                ends.append(e)

    else:
        ends = [e for e in boundary_edges if all(len(v.link_edges) == 2 for v in e.verts)]

    rail_edges = [e for e in bm.edges if e.is_manifold] + ends

    for idx, e in enumerate(rail_edges):
        avg = (e.verts[0].co + e.verts[1].co) / 2

        for v in e.verts:
            v.co = avg + (v.co - avg) * amount

        if idx == 0 and panel and scene and set_prop:
            scene.DM.panelwidth = get_panel_width_from_edge(panel, e)

def create_float_slice_geometry(bm, mx, sequences, normals, width, debug=False):
    geo_sequences = []

    for seq, cyclic in sequences:
        geo = []

        for idx, v in enumerate(seq):
            prevv = seq[-1] if idx == 0 else seq[idx -1]
            nextv = seq[0] if idx == len(seq) - 1 else seq[idx + 1]

            normal = normals[v].normalized()

            if cyclic or idx not in [0, len(seq) - 1]:
                vec_next = (v.co - nextv.co).normalized()
                vec_prev = (prevv.co - v.co).normalized()

                direction = vec_prev + vec_next

            else:
                if idx == 0:
                    direction = (v.co - nextv.co).normalized()

                elif idx == len(seq) - 1:
                    direction = (prevv.co - v.co).normalized()

            cross = direction.cross(normal).normalized()

            if debug:
                draw_vector(normal * 0.1, origin=v.co.copy(), mx=mx, color=(1, 0, 0), modal=False)
                draw_vector(direction * 0.05, origin=v.co.copy(), mx=mx, color=(0, 0, 1), modal=False)
                draw_vector(cross * 0.05, origin=v.co.copy(), mx=mx, color=(0, 1, 0), modal=False)

            v1 = bm.verts.new()
            v1.co = v.co + cross * width / 2

            v2 = bm.verts.new()
            v2.co = v.co - cross * width / 2

            if idx == 0:
                prevv1 = firstv1 = v1
                prevv2 = firstv2 = v2
                continue

            f = bm.faces.new((v1, prevv1, prevv2, v2))
            f.smooth = True

            geo.append((f, bm.edges.get((prevv1, prevv2))))

            if cyclic and idx == len(seq) - 1:
                f = bm.faces.new((firstv1, v1, v2, firstv2))
                f.smooth = True

                geo.append((f, bm.edges.get((v1, v2))))

            else:
                prevv1 = v1
                prevv2 = v2

        geo_sequences.append((geo, cyclic))

    return geo_sequences

def get_available_panel_decals(cycle_libs=None):
    if not cycle_libs:
        cycle_libs = [lib.name for lib in get_prefs().decallibsCOL if (lib.ispanel or lib.istrimsheet) and lib.ispanelcycle]

    seen = []
    availablepanels = []

    for panel in bpy.types.WindowManager.paneldecals.keywords['items']:
        uuid, name, library = panel

        if uuid not in seen:
            seen.append(uuid)

            if library in cycle_libs:
                availablepanels.append(panel)

    return availablepanels

def finish_panel_decal(depsgraph, context, panel, target, cutter):
    dm = context.scene.DM

    parent(panel, target)

    panel.DM.isdecal = True
    panel.DM.issliced = True
    panel.DM.slicedon = target
    panel.DM.decalbackup = cutter
    panel.DM.decaltype = "PANEL"

    set_cycles_visibility(panel, 'shadow', False)
    set_cycles_visibility(panel, 'diffuse', False)

    uuid = context.window_manager.paneldecals

    if uuid:

        availablepanels = get_available_panel_decals()

        if availablepanels:

            if uuid not in [uuid for uuid, _, _ in availablepanels]:
                uuid, name, library = availablepanels[0]

                print(f'INFO: Updating current panel decal to {library + "_" + name}')
                context.window_manager.paneldecals = uuid

            mat, appended, library, name = get_panel_material(context, uuid)

            if mat:
                if appended:
                    set_props_and_node_names_of_decal(library, name, decalobj=panel, decalmat=mat)

                    set_defaults(decalmat=mat)
                else:
                    set_decalobj_props_from_material(panel, mat)

                panel.data.materials.append(mat)

                set_decalobj_name(panel, decalname=mat.DM.decalname, uuid=mat.DM.uuid)

                if mat.DM.decaltype != 'INFO':
                    automatch = dm.auto_match

                    if automatch == "AUTO":
                        origin, direction = get_origin_from_face(panel)

                        _, target_eval, _, _, faceidx, _ = get_closest(depsgraph, [target], origin)

                        if target_eval and faceidx is not None:
                            auto_match_material(panel, mat, matchobj=target_eval, face_idx=faceidx)

                    elif automatch == "MATERIAL":
                        auto_match_material(panel, mat, matchmatname=context.window_manager.matchmaterial)

            else:
                print("WARNING: Current Panel decal material could not be fetched. Panel decal material will not be applied.")

        else:
            print("WARNING: Found no Panel Decals to cycle through. Panel decal material will not be applied.")

    else:
        print("WARNING: No current panel decal UUID found. Panel decal material will not be applied.")

    add_displace(panel)

    add_nrmtransfer(panel, target)

    set_defaults(decalobj=panel)
    lock(panel)

    if cutter:
        cutter.use_fake_user = True
        cutter.DM.isbackup = True

        unlink_object(cutter)

        cutter.DM.backupmx = flatten_matrix(target.matrix_world.inverted_safe() @ cutter.matrix_world)

def get_rail_centers(sequences, mx=None, debug=False):
    rail_center_sequences = []

    for seq, cyclic in sequences:
        rseq = []

        for idx, (face, edge) in enumerate(seq):
            co = (edge.verts[0].co + edge.verts[1].co) / 2
            no = get_edge_normal(edge)
            rseq.append((co, no))

            if not cyclic and idx == len(seq) - 1:
                loop = [loop for loop in edge.link_loops if loop.face == face][0]
                edge = loop.link_loop_next.link_loop_next.edge

                co = (edge.verts[0].co + edge.verts[1].co) / 2
                no = get_edge_normal(edge)
                rseq.append((co, no))

        rail_center_sequences.append((rseq, cyclic))

        if debug and mx:
            draw_points([co for co, _ in rseq], mx=mx, alpha=0.5, modal=False)
            draw_vectors([no * 0.2 for _, no in rseq], [co for co, _ in rseq], mx=mx, color=normal, modal=False)

    return rail_center_sequences

def create_cutter(col, panel, rail_center_sequences, depth):
    cutter_name = "Cutter_%s" % panel.name
    cutter = bpy.data.objects.new(cutter_name, bpy.data.meshes.new(cutter_name))
    cutter.matrix_world = panel.matrix_world

    col.objects.link(cutter)

    bm = bmesh.new()
    bm.from_mesh(cutter.data)

    for rseq, cyclic in rail_center_sequences:
        for idx, (co, no) in enumerate(rseq):
            v1 = bm.verts.new()
            v1.co = co + no * depth

            v2 = bm.verts.new()
            v2.co = co - no * depth

            if idx == 0:
                v1_prev = v1
                v2_prev = v2

                if cyclic:
                    v1_start = v1
                    v2_start = v2

                continue

            bm.faces.new((v1_prev, v2_prev, v2, v1))

            v1_prev = v1
            v2_prev = v2

            if cyclic and idx == len(rseq) - 1:
                bm.faces.new((v1_prev, v2_prev, v2_start, v1_start))

    bm.to_mesh(cutter.data)
    bm.clear()

    return cutter

def remove_decal_orphans(debug=False):
    orphan_backups = [obj for obj in bpy.data.objects if obj.DM.isbackup and obj.use_fake_user and obj.users <= 1]
    orphan_joined = [obj for obj in bpy.data.objects if obj.DM.wasjoined and obj.use_fake_user and obj.users <= 1]
    orphan_decals = [obj for obj in bpy.data.objects if obj.DM.isdecal and not obj.use_fake_user and obj.users <= 1 and not obj.users_collection and not obj.users_scene and obj]

    backup_count = len(orphan_backups)
    joined_count = len(orphan_joined)
    decal_count = len(orphan_decals)

    for obj in orphan_backups + orphan_joined + orphan_decals:
        bpy.data.meshes.remove(obj.data, do_unlink=True)

    if debug:
        print("Info: Removed Orphans! Backups: %d, Joined: %d, Decals: %d" % (backup_count, joined_count, decal_count))

    return backup_count, joined_count, decal_count

def remove_trim_decals(sheet, trim, debug=False):
    col = sheet.DM.trimcollection

    if col:
        if col:
            trim_decals = [obj for obj in col.objects if obj.DM.istrimdecal and obj.DM.trimsheetuuid == sheet.DM.trimsheetuuid and obj.DM.uuid == trim.uuid]

            for decal in trim_decals:
                mat = decal.active_material
                if mat:
                    remove_decalmat(mat, remove_textures=True, debug=debug)

                bpy.data.meshes.remove(decal.data, do_unlink=True)
