import bpy
import bmesh
from mathutils import Vector
import os
from . registration import get_prefs, get_templates_path, get_version_as_float
from . append import append_material
from . system import abspath, log, splitpath
from . mesh import get_most_common_material_index


def get_active_material(obj):
    activemat = obj.active_material
    if activemat:
        if not activemat.use_nodes:
            activemat.use_nodes = True
        return activemat



def get_decalmat(obj):
    mat = obj.active_material
    if mat and mat.DM.isdecalmat:
        return mat


def get_decalmats(obj):
    return [mat for mat in obj.data.materials if mat.DM.isdecalmat]


def get_unique_by_uuid_decalmats_from_decals(decals):

    materials = {}

    for decal in decals:
        for mat in decal.data.materials:
            if mat and mat.DM.isdecalmat and mat.DM.version and get_version_as_float(mat.DM.version) >= 2:
                if mat.DM.uuid not in materials:
                    materials[mat.DM.uuid] = mat

    return materials



def get_panel_material(context, uuid):
    panelmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.uuid == uuid and not mat.DM.ismatched]

    if panelmats:
        mat = panelmats[0]

        return mat, False, None, None

    else:
        decaluuids = context.window_manager.decaluuids

        for duuid, decals in decaluuids.items():
            if duuid == uuid:
                name, library, libtype = decals[0]

                mat = append_material(os.path.join(get_prefs().assetspath, libtype, library, name, "decal.blend"), "LIBRARY_DECAL")

                if mat:
                    mat = deduplicate_decal_material(context, mat)

                    mat.DM.parallaxdefault = get_parallax_amount(mat)

                    return mat, True, library, name

    return None, None, None, None



def remove_decalmat(decalmat, remove_textures=False, legacy=False, debug=False):
    if debug:
        print("\n%s, users: %d" % (decalmat.name, decalmat.users))

    dg = get_decalgroup_from_decalmat(decalmat)
    pg = get_parallaxgroup_from_decalmat(decalmat)

    if dg:
        if debug:
            print("decalgroup users:", dg.node_tree.users)

        if dg.node_tree.users == 1:
            if debug:
                print("Removing decalgroup '%s'." % (dg.name))

            bpy.data.node_groups.remove(dg.node_tree, do_unlink=True)

    if pg:
        if debug:
            print("parallaxgroup users:", pg.node_tree.users)

        hg = get_heightgroup_from_parallaxgroup(pg)

        if pg.node_tree.users == 1:
            if debug:
                print("Removing heightgroup '%s'." % (hg.name))

            bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

            if debug:
                print("Removing parallaxgroup '%s'." % (pg.name))

            bpy.data.node_groups.remove(pg.node_tree, do_unlink=True)

    if remove_textures:
        textures = get_legacy_decal_textures(decalmat) if legacy else get_decal_textures(decalmat)

        for img in textures.values():
            if debug:
                print("Removing image '%s'." % (img.name))

            bpy.data.images.remove(img, do_unlink=True)

    if debug:
        print("Removing material '%s'" % (decalmat.name))

    bpy.data.materials.remove(decalmat, do_unlink=True)


def remove_trimsheetmat(trimsheetmat, remove_textures=False, debug=False):
    if debug:
        print("\n%s, users: %d" % (trimsheetmat.name, trimsheetmat.users))

    tsg = get_trimsheetgroup_from_trimsheetmat(trimsheetmat)
    pg = get_parallaxgroup_from_any_mat(trimsheetmat)
    pg_removed = False

    textures = get_trimsheet_textures(trimsheetmat)

    if tsg:
        if debug:
            print("trimsheet group users:", tsg.node_tree.users)

        if tsg.node_tree.users <= 1:
            if debug:
                print("Removing trimsheet group '%s'." % (tsg.name))

            bpy.data.node_groups.remove(tsg.node_tree, do_unlink=True)

    if pg:
        if debug:
            print("parallax group users:", pg.node_tree.users)

        hg = get_heightgroup_from_parallaxgroup(pg)


        if pg.node_tree.users <= 1:
            if debug:
                print("Removing height group '%s'." % (hg.name))

            bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

            if debug:
                print("Removing parallax group '%s'." % (pg.name))

            bpy.data.node_groups.remove(pg.node_tree, do_unlink=True)

            pg_removed = True

    if remove_textures:
        for maptype, img in textures.items():

            if maptype == 'HEIGHT':
                if pg_removed:
                    if debug:
                        print("Removing image '%s'." % (img.name))

                    bpy.data.images.remove(img, do_unlink=True)

            elif img.users <= 1:
                if debug:
                    print("Removing image '%s'." % (img.name))

                bpy.data.images.remove(img, do_unlink=True)

    if debug:
        print("Removing material '%s'" % (trimsheetmat.name))

    bpy.data.materials.remove(trimsheetmat, do_unlink=True)


def remove_atlasmat(atlasmat, remove_textures=False, debug=False):
    if debug:
        print("\n%s, users: %d" % (atlasmat.name, atlasmat.users))

    ag = get_atlasgroup_from_atlasmat(atlasmat)
    pg = get_parallaxgroup_from_any_mat(atlasmat)

    textures = get_atlas_textures(atlasmat)

    if ag:
        if debug:
            print("atlas group users:", ag.node_tree.users)

        if ag.node_tree.users <= 1:
            if debug:
                print("Removing atlas group '%s'." % (ag.name))

            bpy.data.node_groups.remove(ag.node_tree, do_unlink=True)

    if pg:
        if debug:
            print("parallax group users:", pg.node_tree.users)

        hg = get_heightgroup_from_parallaxgroup(pg)


        if pg.node_tree.users <= 1:
            if debug:
                print("Removing height group '%s'." % (hg.name))

            bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

            if debug:
                print("Removing parallax group '%s'." % (pg.name))

            bpy.data.node_groups.remove(pg.node_tree, do_unlink=True)


    if remove_textures:
        for maptype, img in textures.items():
            if img.users <= 1:
                if debug:
                    print("Removing image '%s'." % (img.name))

                bpy.data.images.remove(img, do_unlink=True)

    if debug:
        print("Removing material '%s'" % (atlasmat.name))

    bpy.data.materials.remove(atlasmat, do_unlink=True)



def get_decalgroup_from_decalmat(decalmat):
    output = get_material_output(decalmat)

    if output:
        links = output.inputs[0].links
        if links:
            nodegroup = links[0].from_node

            return nodegroup


def get_decalgroup_from_decalobj(decalobj):
    decalmat = get_decalmat(decalobj)

    if decalmat:
        return get_decalgroup_from_decalmat(decalmat)



def get_parallaxgroup_from_decalmat(decalmat):
    if decalmat.DM.parallaxnodename:
        nodegroup = decalmat.node_tree.nodes.get(decalmat.DM.parallaxnodename)

        if nodegroup:
            return nodegroup

    for node in decalmat.node_tree.nodes:
        if node.type == "GROUP" and node.node_tree and node.node_tree.name.startswith("parallax"):
            return node


def get_parallaxgroup_from_any_mat(mat):
    for node in mat.node_tree.nodes:
        if node.type == "GROUP" and node.node_tree and node.label == "Parallax Group":
            return node


def get_parallaxgroup_from_decalobj(decalobj):
    decalmat = get_decalmat(decalobj)

    if decalmat:
        return get_parallaxgroup_from_decalmat(decalmat)


def get_parallax_amount(decalmat):
    parallax = 0.1

    if decalmat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL']:
        pg = get_parallaxgroup_from_decalmat(decalmat)

        if pg:
            parallax = round(pg.inputs[0].default_value, 6)

    return parallax



def get_heightgroup_from_parallaxgroup(parallaxgroup, getall=False):
    tree = parallaxgroup.node_tree

    heightgroups = []

    for node in tree.nodes:
        if node.type == "GROUP":
                heightgroups.append(node)

    heightgroups.sort(key=lambda x: x.name)

    return heightgroups if getall else heightgroups[0] if heightgroups else None


def get_heightgroup_from_decalmat(decalmat, getall=False):
    parallaxgroup = get_parallaxgroup_from_decalmat(decalmat)

    if parallaxgroup:
        return get_heightgroup_from_parallaxgroup(parallaxgroup, getall)


def get_heightgroup_from_decalobj(decalobj, getall=False):
    decalmat = get_decalmat(decalobj)

    if decalmat:
        return get_heightgroup_from_decalmat(decalmat)



def get_legacy_decal_textures(decalmat):

    textures = {}

    for node in decalmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                if node.image.filepath.endswith("ao_curv_height.png"):
                    textures["AO_CURV_HEIGHT"] = node.image

                elif node.image.filepath.endswith("nrm_alpha.png"):
                    textures["NRM_ALPHA"] = node.image

                elif node.image.filepath.endswith("masks.png") or (node.image.filepath.endswith("subset.png") or node.image.filepath.endswith("mat2_alpha.png")):
                    textures["MASKS"] = node.image

                else:
                    textures["COLOR_ALPHA"] = node.image

    return textures


def get_legacy_decal_texture_nodes(decalmat, height=False):

    nodes = {}

    for node in decalmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                if node.image.filepath.endswith("ao_curv_height.png"):
                    nodes["AO_CURV_HEIGHT"] = node

                elif node.image.filepath.endswith("nrm_alpha.png"):
                    nodes["NRM_ALPHA"] = node

                elif node.image.filepath.endswith("masks.png") or (node.image.filepath.endswith("subset.png") or node.image.filepath.endswith("mat2_alpha.png")):
                    nodes["MASKS"] = node

                else:
                    nodes["COLOR_ALPHA"] = node

    if height:
        heightgroup = get_heightgroup_from_decalmat(decalmat)

        if heightgroup:
            for node in heightgroup.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    nodes["HEIGHT"] = node
                    break
    return nodes



def get_decal_textures(decalmat):
    textures = {}

    for node in decalmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                textype = node.image.DM.decaltextype

                if textype != 'NONE':
                    textures[textype] = node.image

    return textures


def get_decal_texture_nodes(decalmat, height=False):
    nodes = {}

    for node in decalmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                textype = node.image.DM.decaltextype

                if textype != 'NONE':
                    nodes[textype] = node

    if height:
        heightgroup = get_heightgroup_from_decalmat(decalmat)

        if heightgroup:
            for node in heightgroup.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    nodes["HEIGHT"] = node
                    break
    return nodes


def set_decal_textures(decalmat, textures, height=False):
    for node in decalmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                decaltextype = node.image.DM.decaltextype

                if decaltextype != 'NONE':
                    bpy.data.images.remove(node.image, do_unlink=True)
                    node.image = textures[decaltextype]

    if height:
        heightgroup = get_heightgroup_from_decalmat(decalmat)

        if heightgroup:
            for node in heightgroup.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    node.image = textures["AO_CURV_HEIGHT"]
                    break


def set_decal_texture_paths(decalmat, texturepaths):
    for node in decalmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                node.image.filepath = texturepaths[node.image.DM.decaltextype]



def is_trimsheetmat_matchable(mat=None, textures=None, node=None):

    if mat:
        nodes = mat.node_tree.nodes

    elif textures:
        if any(textype in textures.keys() for textype in ['COLOR', 'ROUGHNESS', 'METALLIC']):
            return False

    elif node:
        nodes = node.id_data.nodes

    else:
        return False

    for node in nodes:
        if node.type == "TEX_IMAGE" and node.image:
            textype = node.image.DM.trimsheettextype

            if textype in ['COLOR', 'ROUGHNESS', 'METALLIC']:
                return False

    return True


def append_and_setup_trimsheet_material(sheetdata, skip_deduplication=False):
    assetspath = get_prefs().assetspath
    templatepath = get_templates_path()

    sheetmat = append_material(templatepath, "TEMPLATE_TRIMSHEET")

    sheetmat.DM.trimsheetuuid = sheetdata['uuid']
    sheetmat.DM.trimsheetname = sheetdata['name']

    deduplicated = False if skip_deduplication else deduplicate_trimsheet_material(sheetmat, name=sheetdata['name'])

    nodes = sheetmat.node_tree.nodes

    if not deduplicated:

        if 'HEIGHT' not in sheetdata['maps']:
            pg = get_parallaxgroup_from_any_mat(sheetmat)

            if pg:
                hg = get_heightgroup_from_parallaxgroup(pg)

                reroute = None

                if pg.node_tree.users <= 1:
                    links = pg.outputs[0].links

                    if links:
                        reroute = links[0].to_node

                    bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)
                    bpy.data.node_groups.remove(pg.node_tree, do_unlink=True)

            if reroute:
                nodes.remove(reroute)

            nodes.remove(pg)

        setup_trimsheet_textures(assetspath, sheetdata, sheetmat)

    empty = [node for node in sheetmat.node_tree.nodes if node.type == 'TEX_IMAGE' and node.mute]

    for e in empty:
        nodes.remove(e)

    set_node_names_of_trimsheet_material(sheetmat, sheetdata['name'])

    return sheetmat


def get_trimsheet_material_from_faces(active, faces, sheetdata, force_new_material=False, debug=False):

    sheetuuid = sheetdata.get('uuid')

    log(debug=debug)

    if active.data.materials:
        log("object has materials", debug=debug)

        slot_idx, unique = get_most_common_material_index(faces)

        currentmat = active.data.materials[slot_idx]

        if currentmat:
            log(" there is a material in the active slot", debug=debug)

            if currentmat.DM.istrimsheetmat:
                log("  it's a trim sheet material", debug=debug)

                if force_new_material:
                    log("   FORCE ADD NEW sheet material", debug=debug)
                    sheetmat = append_and_setup_trimsheet_material(sheetdata)

                    log("    add new sheet mat to the end of the stack", debug=debug)
                    return {'sheetmat': sheetmat, 'appended': True, 'matchedmat': None, 'index': len(active.data.materials)}

                else:
                    log("   ATTEMPT TO REUSE exsiting sheet material", debug=debug)

                    if currentmat.DM.trimsheetuuid == sheetuuid:
                        log("    Current sheet material fits already", debug=debug)
                        return {'sheetmat': None, 'appended': False, 'matchedmat': None, 'index': slot_idx}

                    else:
                        for idx, slot in enumerate(active.material_slots):
                            if slot.material and slot.material.DM.trimsheetuuid == sheetuuid:
                                log("    Current sheet material belongs to different sheet, but found fitting sheet mat in the stack", debug=debug)
                                return {'sheetmat': None, 'appended': False, 'matchedmat': None, 'index': idx}

                        sheetmat = append_and_setup_trimsheet_material(sheetdata)

                        if is_trimsheetmat_matchable(mat=sheetmat) and is_trimsheetmat_matchable(mat=currentmat) and get_trimsheetgroup_from_trimsheetmat(currentmat):
                            matchedmat, matchtype = match_trimsheet_material(sheetmat, currentmat)

                            if matchtype == 'EXISTING':
                                remove_trimsheetmat(sheetmat, debug=False)
                                log("    Found existing matching sheetmat in the scene, adding it to the end of the stack", debug=debug)
                                return {'sheetmat': matchedmat, 'appended': False, 'matchedmat': None, 'index': len(active.data.materials)}

                            elif matchtype == 'MATCHED':
                                log("    Appended and matched new sheet mat to existing one and added it to the end of the stack", debug=debug)
                                return {'sheetmat': matchedmat, 'appended': True, 'matchedmat': None, 'index': len(active.data.materials)}

                        else:
                            log("    Can't match new trim sheet mat to exising one, adding new sheet at the end of the stack", debug=debug)
                            return {'sheetmat': sheetmat, 'appended': True, 'matchedmat': None, 'index': len(active.data.materials)}

            else:
                log("  it's not a trim sheet material", debug=debug)

                sheetmat = append_and_setup_trimsheet_material(sheetdata)

                if is_trimsheetmat_matchable(mat=sheetmat) and get_pbrnode_from_mat(currentmat):
                    log("   it's a PBR material and sheet can be matched to it", debug=debug)
                    matchedmat, matchtype = match_trimsheet_material(sheetmat, currentmat)

                    if matchtype == 'EXISTING':
                        remove_trimsheetmat(sheetmat, debug=False)

                        if matchedmat.name in active.data.materials:
                            for idx, slot in enumerate(active.material_slots):
                                if slot.material and slot.material == matchedmat:
                                    log("    Found existing matching sheetmat in the stack", debug=debug)
                                    return {'sheetmat': None, 'appended': False, 'matchedmat': None, 'index': idx}

                        else:
                            log("    Found existing matching sheetmat in the scene, adding to the current slot replacing the existing pbr material completely", debug=debug)
                            return {'sheetmat': matchedmat, 'appended': False, 'matchedmat': currentmat, 'index': slot_idx}

                    elif matchtype == 'MATCHED':
                        matchedmat.name = "%s.%s" % (currentmat.name, sheetdata['name'])

                        log("    Appended and matched new sheet mat to existing PBR material, replacing it completely", debug=debug)
                        return {'sheetmat': matchedmat, 'appended': True, 'matchedmat': currentmat, 'index': slot_idx}

                elif get_pbrnode_from_mat(currentmat):
                    log("   it's a PBR material, but sheet CAN NOT be matched to it", debug=debug)

                    for idx, slot in enumerate(active.material_slots):
                        if slot.material and slot.material.DM.istrimsheetmat and slot.material.DM.trimsheetuuid == sheetuuid:
                            remove_trimsheetmat(sheetmat, debug=False)

                            log("    found fitting material in the stack", debug=debug)
                            return {'sheetmat': None, 'appended': False, 'matchedmat': None, 'index': idx}

                log("    appending fresh sheetmat to end of stack", debug=debug)
                return {'sheetmat': sheetmat, 'appended': True, 'matchedmat': None, 'index': len(active.data.materials)}

        else:
            log(" the current slot is empty", debug=debug)

            if not force_new_material:

                for idx, slot in enumerate(active.material_slots):
                    if slot.material and slot.material.DM.istrimsheetmat and slot.material.DM.trimsheetuuid == sheetuuid:
                        log("  found existing fitting material in the stack", debug=debug)
                        return {'sheetmat': None, 'appended': False, 'matchedmat': None, 'index': idx}

            sheetmat = append_and_setup_trimsheet_material(sheetdata)

            log("  appending new sheet mat and added it to the current slot", debug=debug)
            return {'sheetmat': sheetmat, 'appended': True, 'matchedmat': None, 'index': slot_idx}


    else:
        log("object doesn't have any materials", debug=debug)

        unmatchedmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat.DM.trimsheetuuid == sheetuuid and not mat.DM.ismatched]

        if unmatchedmats:
            log(" using existing unmatched material for this sheet found in the scene as the first and only material in the stack", debug=debug)
            return {'sheetmat': unmatchedmats[0], 'appended': False, 'matchedmat': None, 'index': 0}

        else:
            sheetmat = append_and_setup_trimsheet_material(sheetdata)

            log(" appended new sheet mat and added it as the first and only material in the stack", debug=debug)
            return {'sheetmat': sheetmat, 'appended': True, 'matchedmat': None, 'index': 0}


def assign_trimsheet_material(obj, faces, mat_dict=None, sheetmat=None, index=0, add_material=False):

    if mat_dict:
        sheetmat = mat_dict['sheetmat']
        index = mat_dict['index']

    for f in faces:
        f.material_index = index

    if add_material and sheetmat:

        if index == len(obj.data.materials) or not obj.data.materials:
            obj.data.materials.append(sheetmat)

        elif obj.data.materials:
            obj.data.materials[index] = sheetmat


def get_most_used_sheetmat_from_selection(obj):

    sheetmats = {idx: slot.material for idx, slot in enumerate(obj.material_slots) if slot.material and slot.material.DM.istrimsheetmat}

    bm = bmesh.from_edit_mesh(obj.data)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    faces = [f for f in bm.faces if f.select]

    slot_idx, unique = get_most_common_material_index(faces)

    if slot_idx in sheetmats:
        return sheetmats[slot_idx], slot_idx, unique

    return None, None, None



def get_trimsheetgroup_from_trimsheetmat(trimsheetmat):

    def get_trimsheetgroup_from_links(links):
        node = links[0].from_node

        if node.type == 'GROUP' and node.label == 'Trim Sheet Group':
            return True, node
        return False, node

    output = get_material_output(trimsheetmat)

    if output:
        links = output.inputs[0].links
        if links:
            is_tsg, node = get_trimsheetgroup_from_links(links)

            if is_tsg:
                return node

            elif node.type == 'MIX_SHADER':
                links = node.inputs[1].links

                if links:
                    is_tsg, node = get_trimsheetgroup_from_links(links)

                    if is_tsg:
                        return node

                    elif node.type == 'REROUTE':
                        links = node.inputs[0].links

                        if links:
                            is_tsg, node = get_trimsheetgroup_from_links(links)

                            if is_tsg:
                                return node

            elif node.type == 'REROUTE':
                links = node.inputs[0].links

                if links:
                    is_tsg, node = get_trimsheetgroup_from_links(links)

                    if is_tsg:
                        return node

        tsgs = sorted([node for node in trimsheetmat.node_tree.nodes if node.type == 'GROUP' and node.label == 'Trim Sheet Group'], key=lambda x: x.name)

        if tsgs:
            return tsgs[0]


def get_trimsheet_nodes(trimsheetmat, skip_parallax=False):
    nodes = {}

    for node in trimsheetmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.label == 'NORMAL':
                nodes["NORMAL"] = node

            elif node.label == 'AO':
                nodes["AO"] = node

            elif node.label == 'CURVATURE':
                nodes["CURVATURE"] = node

            elif node.label == 'COLOR':
                nodes["COLOR"] = node

            elif node.label == 'METALLIC':
                nodes["METALLIC"] = node

            elif node.label == 'ROUGHNESS':
                nodes["ROUGHNESS"] = node

            elif node.label == 'EMISSION':
                nodes["EMISSION"] = node

            elif node.label == 'ALPHA':
                nodes["ALPHA"] = node

            elif node.label == 'SUBSET':
                nodes["SUBSET"] = node

            elif node.label == 'MATERIAL2':
                nodes["MATERIAL2"] = node

        elif node.type == "GROUP":
            if node.node_tree and node.label == "Parallax Group" and not skip_parallax:
                nodes["PARALLAXGROUP"] = node

                tree = node.node_tree

                heightgroups = []

                for node in tree.nodes:
                    if node.type == "GROUP":
                        heightgroups.append(node)

                if heightgroups:
                    heightgroups.sort(key=lambda x: x.name)

                    nodes["HEIGHTGROUP"] = heightgroups

                    for node in heightgroups[0].node_tree.nodes:
                        if node.type == "TEX_IMAGE":
                            nodes["HEIGHT"] = node

    return nodes


def get_trimsheet_textures(trimsheetmat, ignore_groups=False):
    textures = {}

    for node in trimsheetmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                textype = node.image.DM.trimsheettextype

                if textype != 'NONE':
                    textures[textype] = node.image

        elif node.type == "GROUP":
            if node.node_tree and node.label == "Parallax Group":
                tree = node.node_tree

                heightgroups = []

                for node in tree.nodes:
                    if node.type == "GROUP":
                        heightgroups.append(node)
                        break

                if heightgroups:
                    for node in heightgroups[0].node_tree.nodes:
                        if node.type == "TEX_IMAGE" and node.image:
                            textures['HEIGHT'] = node.image
    return textures


def setup_trimsheet_textures(assetspath, sheetdata, sheetmat):
    sheetmaps = sheetdata.get('maps')
    nodes = get_trimsheet_nodes(sheetmat)

    tree = sheetmat.node_tree
    tsg = get_trimsheetgroup_from_trimsheetmat(sheetmat)

    if tree and tsg:
        existingimages = {img.DM.trimsheettextype: img for img in bpy.data.images if img.DM.istrimsheettex and img.DM.trimsheetuuid == sheetmat.DM.trimsheetuuid}

        for maptype in sheetmaps:
            node = nodes.get(maptype)

            if node:

                if maptype in existingimages:
                    node.image = existingimages[maptype]

                else:
                    path = os.path.join(assetspath, 'Trims', sheetdata['name'], "%s.png" % maptype.lower())

                    if os.path.exists(path):
                        img = bpy.data.images.load(path)
                        img.DM.istrimsheettex = True
                        img.DM.trimsheettextype = maptype
                        img.DM.trimsheetuuid = sheetdata.get('uuid')
                        img.DM.trimsheetname = sheetdata.get('name')
                        img.colorspace_settings.name = 'sRGB' if maptype in ['COLOR', 'EMISSION'] else 'Non-Color'

                        node.image = img

                node.mute = False

                if maptype == 'HEIGHT':
                    pg = nodes.get('PARALLAXGROUP')

                    if pg:
                        pg.mute = False

                    pg.inputs[0].default_value = sheetmaps[maptype]['parallax_amount']


                elif maptype not in ['ALPHA', 'SUBSET', 'MATERIAL2']:
                    i = '%s Map' % maptype.title() if maptype in ['NORMAL', 'CURVATURE'] else 'AO Map' if maptype == 'AO' else 'Base Color' if maptype == 'COLOR' else maptype.title()
                    tree.links.new(node.outputs[0], tsg.inputs[i])


def set_node_names_of_trimsheet_material(trimsheetmat, name, reset_heightnode_names=False):
    tsg = get_trimsheetgroup_from_trimsheetmat(trimsheetmat)

    tsg.name = "trimsheet.%s" % (name)

    nodes = get_trimsheet_nodes(trimsheetmat)

    for nodetype, node in nodes.items():
        if nodetype == 'PARALLAXGROUP':
            node.name = "parallax.%s" % name
            node.node_tree.name = node.name

        elif nodetype == 'HEIGHTGROUP':
            heightnodes = node

            if reset_heightnode_names:
                for node in heightnodes:
                    node.name = ''

            for idx, node in enumerate(heightnodes):
                node.name = "height.%s" % name

                if idx == 0:
                    node.node_tree.name = node.name

        else:
            node.name = "%s.%s" % (nodetype.lower(), name)

            if node.type == 'TEX_IMAGE' and node.image:
                node.image.name = "%s.%s" % (nodetype.lower(), name)



def get_atlasmat(obj):
    mat = obj.active_material
    if mat and mat.DM.isatlasmatmat:
        return mat


def get_atlasmats(obj):
    return [mat for mat in obj.data.materials if mat.DM.isatlasmat]


def append_and_setup_atlas_material(atlasdata, istrimsheet=False):
    assetspath = get_prefs().assetspath
    templatepath = get_templates_path()

    atlasmat = append_material(templatepath, "TEMPLATE_ATLAS")
    atlasmat.name = atlasdata['name']

    atlasmat.DM.atlasuuid = atlasdata['uuid']
    atlasmat.DM.atlasname = atlasdata['name']

    nodes = atlasmat.node_tree.nodes

    if 'HEIGHT' not in atlasdata['maps']:
        pg = get_parallaxgroup_from_any_mat(atlasmat)

        if pg:
            hg = get_heightgroup_from_parallaxgroup(pg)

            reroute = None

            if pg.node_tree.users <= 1:
                links = pg.outputs[0].links

                if links:
                    reroute = links[0].to_node

                bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)
                bpy.data.node_groups.remove(pg.node_tree, do_unlink=True)

        if reroute:
            nodes.remove(reroute)

        nodes.remove(pg)

    setup_atlas_textures(assetspath, atlasdata, atlasmat, istrimsheet=istrimsheet)

    empty = [node for node in atlasmat.node_tree.nodes if node.type == 'TEX_IMAGE' and node.mute]

    for e in empty:
        nodes.remove(e)

    set_node_names_of_atlas_material(atlasmat, atlasdata['name'])

    return atlasmat



def get_atlasgroup_from_atlasmat(atlasmat):
    output = get_material_output(atlasmat)

    if output:
        links = output.inputs[0].links
        if links:
            nodegroup = links[0].from_node

            return nodegroup


def get_atlas_nodes(atlasmat, skip_parallax=False, skip_height=False):
    nodes = {}

    for node in atlasmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.label == 'NORMAL':
                nodes["NORMAL"] = node

            elif node.label == 'AO':
                nodes["AO"] = node

            elif node.label == 'CURVATURE':
                nodes["CURVATURE"] = node

            elif node.label == 'COLOR':
                nodes["COLOR"] = node

            elif node.label == 'EMISSION':
                nodes["EMISSION"] = node

            elif node.label == 'ALPHA':
                nodes["ALPHA"] = node

            elif node.label == 'SUBSET':
                nodes["SUBSET"] = node

            elif node.label == 'MATERIAL2':
                nodes["MATERIAL2"] = node

            elif node.label == 'METALLIC':
                nodes["METALLIC"] = node

            elif node.label == 'ROUGHNESS':
                nodes["ROUGHNESS"] = node

        elif node.type == "GROUP":
            if node.node_tree and node.label == "Parallax Group" and not skip_parallax:
                nodes["PARALLAXGROUP"] = node

                if not skip_height:
                    tree = node.node_tree

                    heightgroups = []

                    for node in tree.nodes:
                        if node.type == "GROUP":
                            heightgroups.append(node)

                    if heightgroups:
                        heightgroups.sort(key=lambda x: x.name)

                        nodes["HEIGHTGROUP"] = heightgroups

                        for node in heightgroups[0].node_tree.nodes:
                            if node.type == "TEX_IMAGE":
                                nodes["HEIGHT"] = node

    return nodes


def get_atlas_textures(atlasmat):
    textures = {}

    for node in atlasmat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                textype = node.image.DM.atlastextype

                if textype != 'NONE':
                    textures[textype] = node.image

        elif node.type == "GROUP":
            if node.node_tree and node.label == "Parallax Group":
                tree = node.node_tree

                heightgroups = []

                for node in tree.nodes:
                    if node.type == "GROUP":
                        heightgroups.append(node)
                        break

                if heightgroups:
                    for node in heightgroups[0].node_tree.nodes:
                        if node.type == "TEX_IMAGE" and node.image:
                            textures['HEIGHT'] = node.image

    return textures


def set_atlasdummy_texture_paths(atlasdummymat, texturepaths):
    for node in atlasdummymat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            if node.image:
                if texturepaths.get(node.image.DM.atlastextype):
                    node.image.filepath = texturepaths[node.image.DM.atlastextype]

                else:
                    bpy.data.images.remove(node.image, do_unlink=True)
                    atlasdummymat.node_tree.nodes.remove(node)

        elif node.type == 'GROUP':
            if node.node_tree and node.label == 'Parallax Group':
                pg = node
                reroute = pg.outputs[0].links[0].to_node

                heightgroups = []

                for node in pg.node_tree.nodes:
                    if node.type == "GROUP":
                        heightgroups.append(node)
                        break

                if heightgroups:
                    for node in heightgroups[0].node_tree.nodes:

                        if node.type == "TEX_IMAGE" and node.image:

                            if 'HEIGHT' in texturepaths:
                                node.image.filepath = texturepaths[node.image.DM.atlastextype]

                            else:
                                bpy.data.images.remove(node.image, do_unlink=True)

                                bpy.data.node_groups.remove(heightgroups[0].node_tree, do_unlink=True)
                                bpy.data.node_groups.remove(pg.node_tree, do_unlink=True)

                                atlasdummymat.node_tree.nodes.remove(pg)
                                atlasdummymat.node_tree.nodes.remove(reroute)


def setup_atlas_textures(assetspath, atlasdata, atlasmat, istrimsheet=False):
    atlasmaps = atlasdata.get('maps')
    nodes = get_atlas_nodes(atlasmat)

    tree = atlasmat.node_tree
    ag = get_atlasgroup_from_atlasmat(atlasmat)

    if tree and ag:
        existingimages = {img.DM.atlastextype: img for img in bpy.data.images if img.DM.isatlastex and img.DM.atlasuuid == atlasmat.DM.atlasuuid}

        for maptype in atlasmaps:
            node = nodes.get(maptype)

            if node:

                if maptype in existingimages:
                    node.image = existingimages[maptype]

                else:
                    path = os.path.join(assetspath, 'Trims' if istrimsheet else 'Atlases', atlasdata['name'], "%s.png" % maptype.lower())

                    if os.path.exists(path):
                        img = bpy.data.images.load(path)
                        img.DM.isatlastex = True
                        img.DM.atlastextype = maptype
                        img.DM.atlasuuid = atlasdata.get('uuid')
                        img.DM.atlasname = atlasdata.get('name')
                        img.colorspace_settings.name = 'sRGB' if maptype in ['COLOR', 'EMISSION'] else 'Non-Color'

                        node.image = img

                node.mute = False

                if maptype == 'HEIGHT':
                    pg = nodes.get('PARALLAXGROUP')

                    if pg:
                        pg.mute = False

                    pg.inputs[0].default_value = atlasmaps[maptype]['parallax_amount']


                elif maptype not in ['SUBSET', 'MATERIAL2']:
                    i = '%s Map' % maptype.title() if maptype in ['NORMAL', 'CURVATURE'] else 'AO Map' if maptype == 'AO' else 'Base Color' if maptype == 'COLOR' else maptype.title()
                    tree.links.new(node.outputs[0], ag.inputs[i])

                    if maptype == 'ALPHA':
                        atlasmat.blend_method = 'BLEND'


def set_node_names_of_atlas_material(atlasmat, name, dummy=False):
    ag = get_atlasgroup_from_atlasmat(atlasmat)

    ag.name = "%s.%s" % ('atlasdummy' if dummy else 'atlas', name)
    ag.node_tree.name = ag.name

    nodes = get_atlas_nodes(atlasmat)

    for nodetype, node in nodes.items():
        if nodetype == 'PARALLAXGROUP':
            node.name = "parallax.%s" % name
            node.node_tree.name = node.name

        elif nodetype == 'HEIGHTGROUP':
            heightnodes = node

            for idx, node in enumerate(heightnodes):
                node.name = "height.%s" % name

                if idx == 0:
                    node.node_tree.name = node.name
        else:
            node.name = "%s.%s" % (nodetype.lower(), name)

            if node.type == 'TEX_IMAGE' and node.image:
                if node.image:
                    node.image.name = "%s.%s" % (nodetype.lower(), name)



def get_material_output(mat):
    if not mat.use_nodes:
        mat.use_nodes = True

    output = mat.node_tree.nodes.get('Material Output')

    if not output:
        for node in mat.node_tree.nodes:
            if node.type == 'OUTPUT_MATERIAL':
                return node
    return output


def get_pbrnode_from_mat(mat):
    output = get_material_output(mat)

    if output:
        links = output.inputs[0].links

        if links:
            lastnode = links[0].from_node


            if lastnode.type == "BSDF_PRINCIPLED":
                return lastnode

            elif lastnode.type == "GROUP":
                return get_pbrnode_from_group(lastnode)


def get_pbrnode_from_group(group):
    output = group.node_tree.nodes.get('Group Output')

    if output:
        bsdf = output.inputs.get('BSDF')

        if bsdf and bsdf.links:
            lastnode = bsdf.links[0].from_node

            if lastnode.type == "BSDF_PRINCIPLED":
                return lastnode



def deduplicate_decal_material(context, decalmat, name='', library='', instant=False, trim=False):

    typemats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat != decalmat and mat.DM.decaltype == decalmat.DM.decaltype]

    existingmats = [mat for mat in typemats if mat.DM.isdecalmat and mat != decalmat and mat.DM.uuid == decalmat.DM.uuid]

    if typemats:
        newdecalgroup = get_decalgroup_from_decalmat(decalmat)
        olddecalgroup = get_decalgroup_from_decalmat(typemats[0])

        if newdecalgroup and olddecalgroup:
            bpy.data.node_groups.remove(newdecalgroup.node_tree, do_unlink=True)
            newdecalgroup.node_tree = olddecalgroup.node_tree

    if existingmats:
        unmatched = [mat for mat in existingmats if not mat.DM.ismatched]
        matched = [mat for mat in existingmats if mat.DM.ismatched]

        if unmatched:
            existingmat = sorted(unmatched, key=lambda x: x.name)[0]

            for img in get_decal_textures(decalmat).values():
                bpy.data.images.remove(img, do_unlink=True)

            if decalmat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL']:
                heightgroup = get_heightgroup_from_decalmat(decalmat)

                if heightgroup:
                    bpy.data.node_groups.remove(heightgroup.node_tree, do_unlink=True)

                parallaxgroup = get_parallaxgroup_from_decalmat(decalmat)
                if parallaxgroup:
                    bpy.data.node_groups.remove(parallaxgroup.node_tree, do_unlink=True)

            bpy.data.materials.remove(decalmat, do_unlink=True)

            return existingmat

        elif matched:
            existingmat = sorted(matched, key=lambda x: x.name)[0]

            textures = get_decal_textures(existingmat)

            if textures:
                set_decal_textures(decalmat, textures, height=False)

            if decalmat.DM.decaltype in ['SIMPLE', 'SUBSET', 'PANEL']:
                heightgroup = get_heightgroup_from_decalmat(decalmat)
                if heightgroup:
                    bpy.data.node_groups.remove(heightgroup.node_tree, do_unlink=True)

                existingparallaxgroup = get_parallaxgroup_from_decalmat(existingmat)
                newparallaxgroup = get_parallaxgroup_from_decalmat(decalmat)

                if existingparallaxgroup and newparallaxgroup:
                    parallax_tree = newparallaxgroup.node_tree
                    newparallaxgroup.node_tree = existingparallaxgroup.node_tree
                    bpy.data.node_groups.remove(parallax_tree, do_unlink=True)

    else:
        dm = context.scene.DM

        for textype, img in get_decal_textures(decalmat).items():

            if name and library:
                assetspath = get_prefs().assetspath
                split = splitpath(img.filepath)

                filename = split[-1]

                if instant:
                    imgpath = os.path.join(assetspath, 'Create', 'decalinstant', name, filename)
                elif trim:
                    imgpath = os.path.join(assetspath, 'Trims', library, name, filename)
                else:
                    imgpath = os.path.join(assetspath, 'Decals', library, name, filename)

                if img.filepath != imgpath:
                    img.filepath = imgpath

            else:
                img.filepath = abspath(img.filepath)

            if dm.pack_images == 'PACKED':
                img.pack()

    return decalmat


def deduplicate_trimsheet_material(trimsheetmat, name=None):

    sheetmats = [mat for mat in bpy.data.materials if mat.DM.istrimsheetmat and mat != trimsheetmat]

    existingmats = [mat for mat in sheetmats if mat != trimsheetmat and mat.DM.istrimsheetmat and mat.DM.trimsheetuuid == trimsheetmat.DM.trimsheetuuid]

    if sheetmats:
        newtsg = get_trimsheetgroup_from_trimsheetmat(trimsheetmat)
        oldtsg = get_trimsheetgroup_from_trimsheetmat(sheetmats[0])

        if newtsg and oldtsg:
            bpy.data.node_groups.remove(newtsg.node_tree, do_unlink=True)
            newtsg.node_tree = oldtsg.node_tree

    if existingmats:
        existingmat = existingmats[0]

        existing_nodes = get_trimsheet_nodes(existingmat)
        new_nodes = get_trimsheet_nodes(trimsheetmat)

        existingpg = existing_nodes.get('PARALLAXGROUP')
        newpg = new_nodes.get('PARALLAXGROUP')

        if existingpg and newpg:
            hg = get_heightgroup_from_parallaxgroup(newpg)

            if hg:
                bpy.data.node_groups.remove(hg.node_tree, do_unlink=True)

            parallax_tree = newpg.node_tree

            newpg.node_tree = existingpg.node_tree
            bpy.data.node_groups.remove(parallax_tree, do_unlink=True)

            newpg.mute = existingpg.mute
            newpg.inputs[0].default_value = existingpg.inputs[0].default_value


        tree = trimsheetmat.node_tree

        for nodetype, node in existing_nodes.items():
            if nodetype in ['NORMAL', 'AO', 'CURVATURE', 'COLOR', 'METALLIC', 'ROUGHNESS', 'EMISSION', 'ALPHA', 'SUBSET', 'MATERIAL2']:
                if node.image:
                    new_node = new_nodes.get(nodetype)

                    if new_node:
                        new_node.image = node.image
                        new_node.mute = False

                        if newtsg and nodetype not in ['ALPHA', 'SUBSET', 'MATERIAL2']:
                            i = '%s Map' % nodetype.title() if nodetype in ['NORMAL', 'CURVATURE'] else 'AO Map' if nodetype == 'AO' else 'Base Color' if nodetype == 'COLOR' else nodetype.title()

                            tree.links.new(new_node.outputs[0], newtsg.inputs[i])

        if name:
            names = [mat.name for mat in existingmats]

            basename = name
            counter = 0

            while name in names:
                counter += 1
                name = "%s.%s" % (basename, str(counter).zfill(3))

            trimsheetmat.name = name

    elif name:
        trimsheetmat.name = name

    return True if existingmats else False



def get_pbrnode_as_dict(node):
    d = {}

    for i in node.inputs:
        if i.name in ['Alpha', 'Weight']:
            continue

        if i.type == "VECTOR" and "Subsurface" not in i.name:
            continue

        if i.type in ["RGBA", "VECTOR"]:
            value = [round(v, 3) for v in i.default_value]

        else:
            value = round(i.default_value, 3)

        d[i.name] = value

    return d


def get_defaultwhite_as_dict():
    d = {}

    d["Base Color"] = [0.8, 0.8, 0.8, 1]
    d["Subsurface"] = 0
    d["Subsurface Radius"] = [1, 0.2, 0.1]
    d["Subsurface Color"] = [0.8, 0.8, 0.8, 1]

    if bpy.app.version >= (3, 0, 0):
        d["Subsurface IOR"] = 1.4
        d["Subsurface Anisotropy"] = 0

    d["Metallic"] = 0
    d["Specular"] = 0.5
    d["Specular Tint"] = 0
    d["Roughness"] = 0.5
    d["Anisotropic"] = 0
    d["Anisotropic Rotation"] = 0
    d["Sheen"] = 0
    d["Sheen Tint"] = 0.5
    d["Clearcoat"] = 0
    d["Clearcoat Roughness"] = 0.03
    d["IOR"] = 1.45
    d["Transmission"] = 0
    d["Transmission Roughness"] = 0
    d["Emission"] = [0, 0, 0, 1]
    d["Emission Strength"] = 1

    return d


def get_defaultmetal_as_dict():
    d = {}

    d["Base Color"] = [0.222, 0.222, 0.222, 1]
    d["Subsurface"] = 0
    d["Subsurface Radius"] = [1, 1, 1]
    d["Subsurface Color"] = [0.7, 0.1, 0.1, 1]

    if bpy.app.version >= (3, 0, 0):
        d["Subsurface IOR"] = 1.4
        d["Subsurface Anisotropy"] = 0

    d["Metallic"] = 1
    d["Specular"] = 0.5
    d["Specular Tint"] = 0
    d["Roughness"] = 0.25
    d["Anisotropic"] = 0
    d["Anisotropic Rotation"] = 0
    d["Sheen"] = 0
    d["Sheen Tint"] = 0.5
    d["Clearcoat"] = 0
    d["Clearcoat Roughness"] = 0.03
    d["IOR"] = 1.45
    d["Transmission"] = 0
    d["Transmission Roughness"] = 0
    d["Emission"] = [0, 0, 0, 1]
    d["Emission Strength"] = 1

    return d


def get_decalgroup_as_dict(node):
    material = {}
    material2 = {}
    subset = {}


    for i in node.inputs:
        if i.name in ['Material Normal', 'Material 2 Normal', 'Subset Normal']:
            continue

        if any([i.name.startswith(string) for string in ["Material ", "Subset "]]):
            if i.type in ["RGBA", "VECTOR"]:
                value = [round(v, 3) for v in i.default_value]

            else:
                value = round(i.default_value, 3)

            if i.name.startswith("Material 2 "):
                material2[i.name.replace("Material 2 ", "")] = value

            elif i.name.startswith("Material "):
                material[i.name.replace("Material ", "")] = value

            elif i.name.startswith("Subset "):
                subset[i.name.replace("Subset ", "")] = value

    return material, material2, subset


def get_trimsheetgroup_as_dict(node):
    if not is_trimsheetmat_matchable(node=node):
        return {}

    d = {}

    for i in node.inputs:
        if any([i.name.endswith(string) for string in ['Alpha', 'Normal', ' Map', ' Multiplier']]):
            continue

        else:
            if i.links and i.links[0].from_node.type in ['MIX', 'MIX_RGB']:

                mixnode = i.links[0].from_node
                mixinA = get_mix_node_input(mixnode, inpt='A')

                if not mixinA.links:
                    color = mixinA.default_value

                    if i.type == 'RGBA':
                        i.default_value = color

                    elif i.type == 'VALUE':
                        i.default_value = color[0]

            if i.type in ["RGBA", "VECTOR"]:
                value = [round(v, 3) for v in i.default_value]

            else:
                value = round(i.default_value, 3)

            d[i.name] = value

    return d


def get_dict_from_matname(matname):
    if matname is None:
        return {}, None

    elif matname == "None":
        return get_defaultwhite_as_dict(), None

    elif matname == "Default":
        return get_defaultmetal_as_dict(), None

    else:
        mat = bpy.data.materials.get(matname)

        if mat:
            pbrnode = get_pbrnode_from_mat(mat)

            if pbrnode:
                return get_pbrnode_as_dict(pbrnode), mat

            elif mat.DM.istrimsheetmat:
                tsg = get_trimsheetgroup_from_trimsheetmat(mat)

                if tsg:
                    return get_trimsheetgroup_as_dict(tsg), mat

        return {}, None


def get_dict_from_faceidx(matchobj, face_idx, debug=False):
    matchmat, matchpbrnode = get_material_from_faceidx(matchobj, face_idx)

    if matchmat == "None":
        if debug:
            print("Matching to Default White Material")

        return get_defaultwhite_as_dict(), None

    elif matchmat:
        if debug:
            print("Matching to %s" % (matchmat.name))

        return get_pbrnode_as_dict(matchpbrnode), matchmat

    else:
        return None, None



def get_material_from_faceidx(matchobj, face_idx):
    idx = matchobj.data.polygons[face_idx].material_index

    mats = [mat for mat in matchobj.data.materials]

    if mats:
        matchmat = mats[idx] if idx < len(mats) else None

        if matchmat:
            return matchmat

    return "None"


def set_decalgroup_from_dict(nodegroup, material=None, material2=None, subset=None):
    if material:
        for i in material:
            nodegroup.inputs["Material %s" % i].default_value = material[i]

    if material2:
        for i in material2:
            nodegroup.inputs["Material 2 %s" % i].default_value = material2[i]

    if subset:
        for i in subset:
            nodegroup.inputs["Subset %s" % i].default_value = subset[i]


def auto_match_material(decalobj, decalmat, matchobj=None, face_idx=None, face_idx2=None, matchmatname=None, debug=False):
    if matchmatname:
        if debug:
            print("Auto-matching material to selected material '%s' from matchmaterial enum." % (matchmatname))

    elif matchobj and face_idx is not None:
        if debug:
            print("Auto-matching material based on obj and face index.")

        matchmat = get_material_from_faceidx(matchobj, face_idx)
        matchmatname = matchmat.name if isinstance(matchmat, bpy.types.Material) else matchmat if matchmat else None

    else:
        if debug:
            print("Exiting auto match material, insufficient arguments.")
        return

    if matchmatname:
        if face_idx2 is not None:
            if debug:
                print("Matching material2 as well.")

            matchmat2 = get_material_from_faceidx(matchobj, face_idx2)
            matchmat2name = matchmat2.name if isinstance(matchmat2, bpy.types.Material) else matchmat2 if matchmat2 else None

        else:
            matchmat2name = matchmatname if decalmat.DM.decaltype == "PANEL" else None

        matchsubname = None

        match_material(decalobj, decalmat, matchmatname=matchmatname, matchmat2name=matchmat2name, matchsubname=matchsubname, debug=debug)


def match_material(decalobj, decalmat, matchmatname=None, matchmat2name=None, matchsubname=None, debug=False):
    log("matching", decalmat.name, "to", matchmatname, matchmat2name, matchsubname, debug=debug)

    materialdict, material = get_dict_from_matname(matchmatname)
    material2dict, material2 = get_dict_from_matname(matchmat2name)
    subsetdict, subset = get_dict_from_matname(matchsubname)

    if not any([materialdict, material2dict, subsetdict]):
        log("Aborting, all material dictionaries are empty!", debug=debug)
        return None, None

    dg = get_decalgroup_from_decalmat(decalmat)
    decal_materialdict, decal_material2dict, decal_subsetdict = get_decalgroup_as_dict(dg)

    match_materialdict = materialdict if materialdict else decal_materialdict
    match_material2dict = material2dict if material2dict else decal_material2dict
    match_subsetdict = subsetdict if subsetdict else decal_subsetdict

    match_tuple = (match_materialdict, match_material2dict, match_subsetdict)


    existingmatchedmats = [mat for mat in bpy.data.materials if mat.DM.isdecalmat and mat.DM.uuid == decalmat.DM.uuid and mat.DM.ismatched]

    for candidate in existingmatchedmats:
        candidate_dg = get_decalgroup_from_decalmat(candidate)
        candidate_tuple = get_decalgroup_as_dict(candidate_dg)

        if match_tuple == candidate_tuple:
            log("Found existing matching material %s" % (candidate.name), debug=debug)

            decalobj.active_material = candidate
            return candidate, "EXISTING"

    log("Creating new matched decal material", debug=debug)

    decalmatmatched = decalmat.copy()
    decalmatmatched.DM.ismatched = True
    decalobj.active_material = decalmatmatched

    decalnodegroup = get_decalgroup_from_decalmat(decalmatmatched)
    set_decalgroup_from_dict(decalnodegroup, material=materialdict, material2=material2dict, subset=subsetdict)

    decaldict = get_decalgroup_as_dict(decalnodegroup)

    transmission = max([value for d in decaldict for key, value in d.items() if key.endswith('Transmission')])
    decalmatmatched.use_screen_refraction = transmission > 0

    if materialdict:
        decalmatmatched.DM.matchedmaterialto = material

    if material2dict:
        decalmatmatched.DM.matchedmaterial2to = material2

    if subsetdict:
        decalmatmatched.DM.matchedsubsetto = subset

    return decalmatmatched, "MATCHED"


def set_subset_component_from_matname(decalmat, subsetmatname):

    print("INFO: Setting Subset Material to:", subsetmatname)

    subsetdict, _ = get_dict_from_matname(subsetmatname)

    decalnodegroup = get_decalgroup_from_decalmat(decalmat)
    set_decalgroup_from_dict(decalnodegroup, material=None, material2=None, subset=subsetdict)

    decalmat.use_screen_refraction = subsetdict['Transmission'] > 0


def set_subset_component_from_decalgroup(decalmat, subsetdecalgroup):

    print("INFO: Setting Subset Material from:", subsetdecalgroup.name)

    decalnodegroup = get_decalgroup_from_decalmat(decalmat)

    _, _, subset = get_decalgroup_as_dict(subsetdecalgroup)
    set_decalgroup_from_dict(decalnodegroup, subset=subset)


def set_match_material_enum(debug=False):

    wm = bpy.context.window_manager
    default = wm.matchmaterial

    mats = [mat for mat in bpy.data.materials if not mat.DM.isdecalmat and mat.use_nodes and get_pbrnode_from_mat(mat)]

    matchable = []

    if mats:
        if debug:
            print("Matchable materials:", [mat.name for mat in mats])

        for mat in sorted(mats, key=lambda x: x.name, reverse=True):

            icon_id = mat.preview_ensure().icon_id if bpy.app.version >= (3, 0, 0) else mat.preview.icon_id
            matchable.append((mat.name, mat.name, "", icon_id, icon_id))

            if not getattr(mat.preview, 'icon_id', False):
                print(f"WARNING: Failed to retrieve 'icon_id' of material '{mat.name}'")


    matchable.append(("None", "None", "", 0, 0))
    matchable.append(("Default", "Default", "", 0, 1))

    if default not in [item[0] for item in matchable]:
        default=matchable[0][0]

    bpy.types.WindowManager.matchmaterial = bpy.props.EnumProperty(name="Materials, that can be matched", items=matchable)

    bpy.context.window_manager.matchmaterial = default

    return sorted(mats, key=lambda x: x.name)



def set_trimsheetgroup_from_dict(nodegroup, pbrdict):
    for i in pbrdict:
        nodegroup.inputs[i].default_value = pbrdict[i]


def match_trimsheet_material(trimsheetmat, matchmat):

    pbr = get_pbrnode_from_mat(matchmat)

    if pbr:
        matchedmats = [mat for mat in bpy.data.materials if mat != trimsheetmat and mat.DM.istrimsheetmat and mat.DM.trimsheetuuid == trimsheetmat.DM.trimsheetuuid and mat.DM.ismatched and mat.DM.matchedtrimsheetto == matchmat]

        if matchedmats:
            return matchedmats[0], 'EXISTING'

        else:
            tsg = get_trimsheetgroup_from_trimsheetmat(trimsheetmat)

            if tsg:
                pbrdict = get_pbrnode_as_dict(pbr)
                set_trimsheetgroup_from_dict(tsg, pbrdict)

                trimsheetmat.use_screen_refraction = pbrdict.get('Transmission') > 0

                trimsheetmat.DM.ismatched = True
                trimsheetmat.DM.matchedtrimsheetto = matchmat

                trimsheetmat.diffuse_color = matchmat.diffuse_color

                return trimsheetmat, 'MATCHED'

    matchtsg = get_trimsheetgroup_from_trimsheetmat(matchmat)

    if matchtsg:
        matchedmats = [mat for mat in bpy.data.materials if mat != trimsheetmat and mat.DM.istrimsheetmat and mat.DM.trimsheetuuid == trimsheetmat.DM.trimsheetuuid and mat.DM.ismatched and mat.DM.matchedtrimsheetto == matchmat]

        if matchedmats:
            return matchedmats[0], 'EXISTING'

        else:
            tsg = get_trimsheetgroup_from_trimsheetmat(trimsheetmat)

            matchtsgdict = get_trimsheetgroup_as_dict(matchtsg)
            set_trimsheetgroup_from_dict(tsg, matchtsgdict)

            trimsheetmat.use_screen_refraction = matchtsgdict.get('Transmission') > 0

            trimsheetmat.DM.ismatched = True
            trimsheetmat.DM.matchedtrimsheetto = matchmat


            trimsheetmat.diffuse_color = matchmat.diffuse_color

            return trimsheetmat, 'MATCHED'

    return None, None



def link_to_socket(mat, fromnode, tonode, outputidx, socketname, atlas=False):
    if atlas:
        inpt = tonode.inputs.get(socketname)

        if inpt:
            mat.node_tree.links.new(fromnode.outputs[outputidx], inpt)

    else:
        inpt = tonode.inputs.get(f"Material {socketname}")

        if inpt:
            mat.node_tree.links.new(fromnode.outputs[outputidx], inpt)

        if mat.DM.decaltype == 'PANEL':
            inpt = tonode.inputs.get(f"Material 2 {socketname}")

            if inpt:
                mat.node_tree.links.new(fromnode.outputs[outputidx], inpt)


def restore_detail_normal_links(tree, dg):

    normal_inputs = [i for i in dg.inputs if i.name.endswith('Normal')]
    detail_normal = tree.nodes.get('Detail Normal')

    if detail_normal:
        for i in normal_inputs:
            if not i.links:
                print(f"INFO: Restoring Detail Normal Link to {i.name}")
                tree.links.new(detail_normal.outputs[0], i)


def transfer_parent_textures(parent, mat, tree, transferuvs, use_normals=False, atlas=False):

    parentmat = get_active_material(parent)

    newnodes = []

    if parentmat:
        pbrnode = get_pbrnode_from_mat(parentmat)
        group = get_atlasgroup_from_atlasmat(mat) if atlas else get_decalgroup_from_decalmat(mat)

        imgnodes = sorted([node for node in parentmat.node_tree.nodes if node.type == 'TEX_IMAGE'], key=lambda n: n.location.y)

        node_space = 35

        for i, node in enumerate(imgnodes):
            imgnode = tree.nodes.new('ShaderNodeTexImage')
            imgnode.image = node.image
            imgnode.hide = True
            imgnode.name = imgnode.name + '[UVTRANSFER]'

            imgnode.interpolation = node.interpolation
            imgnode.projection = node.projection
            imgnode.extension = node.extension

            imgnode.location = Vector((-850, 475 - (((len(imgnodes) - 1) * node_space) / 2) + (i * node_space)))

            link = tree.links.new(transferuvs.outputs[0], imgnode.inputs[0])

            if pbrnode:
                for idx, output in enumerate(node.outputs):
                    for link in output.links:

                        if link.to_node == pbrnode:
                            link_to_socket(mat, imgnode, group, idx, link.to_socket.name, atlas=atlas)

                        elif not atlas and use_normals and link.to_node.type == 'NORMAL_MAP':
                            nrm = link.to_node

                            if nrm.outputs[0].links and nrm.outputs[0].links[0].to_node == pbrnode:
                                nrmnode = tree.nodes.new('ShaderNodeNormalMap')
                                nrmnode.name = nrmnode.name + '[UVTRANSFER]'
                                nrmnode.label = 'TransferNormal'
                                nrmnode.hide = True

                                nrmnode.location.x = imgnode.location.x + 280
                                nrmnode.location.y = imgnode.location.y

                                tree.links.new(imgnode.outputs[0], nrmnode.inputs[1])
                                link_to_socket(mat, nrmnode, group, 0, 'Normal')

            newnodes.append(imgnode)

        if not atlas and not use_normals:
            restore_detail_normal_links(tree, group)

    return newnodes


def transfer_parallax(mat, tree, transferuvs, imgnodes, atlas=False):

    pg = get_parallaxgroup_from_any_mat(mat)

    if pg:
        transferuvs.location.x = -1310

        baseuvs = tree.nodes.new('ShaderNodeUVMap')
        baseuvs.name = baseuvs.name + '[UVTRANSFER]'
        baseuvs.location = Vector((-1700, 300))
        baseuvs.hide = True

        subtract = tree.nodes.new('ShaderNodeVectorMath')
        subtract.name = subtract.name + '[UVTRANSFER]'
        subtract.location = Vector((-1500, 300))
        subtract.operation = 'SUBTRACT'
        subtract.hide = True

        multiply = tree.nodes.new('ShaderNodeVectorMath')
        multiply.name = multiply.name + '[UVTRANSFER]'
        multiply.location = Vector((-1300, 300))
        multiply.operation = 'MULTIPLY'
        multiply.hide = True

        value = tree.nodes.new('ShaderNodeValue')
        value.name = value.name + '[UVTRANSFER]'
        value.label = 'Parallax Amount'
        value.location = Vector((-1500, 250))
        value.outputs[0].default_value = 1 if atlas else 0.1

        add = tree.nodes.new('ShaderNodeVectorMath')
        add.name = add.name + '[UVTRANSFER]'
        add.location = Vector((-1100, 400))
        add.hide = True

        tree.links.new(pg.outputs[0], subtract.inputs[0])
        tree.links.new(baseuvs.outputs[0], subtract.inputs[1])
        tree.links.new(subtract.outputs[0], multiply.inputs[0])
        tree.links.new(value.outputs[0], multiply.inputs[1])

        tree.links.new(transferuvs.outputs[0], add.inputs[0])
        tree.links.new(multiply.outputs[0], add.inputs[1])

        for imgnode in imgnodes:
            tree.links.new(add.outputs[0], imgnode.inputs[0])



def get_mix_node_input(node, inpt='Factor', debug=False):


    if debug:
        print()
        print(node, inpt)

    if bpy.app.version >= (3, 4, 0):
        if debug:
            print("Blender 3.4.0")
            print("mix data_type:", node.data_type)

        if inpt == 'Factor':
            i = node.inputs[0]

        if node.data_type == 'FLOAT':
            if inpt == 'Color1':
                i = node.inputs[2]
            elif inpt == 'Color2':
                i = node.inputs[3]

        elif node.data_type == 'VECTOR':
            if inpt == 'Color1':
                i = node.inputs[4]
            elif inpt == 'Color2':
                i = node.inputs[5]

        elif node.data_type == 'RGBA':
            if inpt == 'A':
                i = node.inputs[6]
            elif inpt == 'B':
                i = node.inputs[7]

    else:
        if debug:
            print("Blender 3.3.0")

        if inpt == 'Factor':
            i = node.inputs[0]

        elif inpt == 'A':
            i = node.inputs[1]

        elif inpt == 'B':
            i = node.inputs[2]

    if debug:
        print("input:", i, i.name, i.type)

    return i


def get_mix_node_output(node):
    if bpy.app.version >= (3, 4, 0):
        if node.data_type == 'FLOAT':
            return node.outputs[0]

        elif node.data_type == 'VECTOR':
            return node.outputs[1]

        elif node.data_type == 'RGBA':
            return node.outputs[2]
    else:
        return node.outputs[0]
